"""Default conftest for the Valar Daemon.
"""
import os
# import sys
import time
import pytest
import pytest
import logging
from pathlib import Path
from typing import Tuple
from _pytest.config import Config

from algokit_utils import is_localnet
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.account_manager import AddressAndSigner

from valar_daemon.Logger import Logger
from valar_daemon.constants import ALGO_ASA_ID, VALAD_STATE_NOT_READY
from valar_daemon.AppWrapper import ValadAppWrapper
from valar_daemon.NoticeboardClient import NoticeboardClient

# Applied renaming so that the local definition is called (not from smart contract folder)
from .utils import (
    create_and_fund_account as cfa,
    create_asset,
    translate_valad_state_to_noticeboard_util_class_action
)

# sys.path.insert(0, str(Path(*Path(__file__).parent.parts[:-2], 'valar-smart-contracts')))
from tests.utils import create_and_fund_account
from tests.noticeboard.utils import Noticeboard
from tests.noticeboard.config import ActionInputs


def pytest_configure(config: Config): # Do not rename - `pytest_configure` is a hook
    """Create and point the `basetemp` (`tmp_path`) to a unique subdirectory within the indicated `basetemp` path.

    Parameters
    ----------
    config : Config
    """
    basetemp = config.getoption("--basetemp")
    if basetemp:
        timestamp = time.strftime("pytest-dump_%Y-%m-%dT%H-%M-%S")
        unique_path = os.path.join(basetemp, timestamp)
        os.makedirs(unique_path, exist_ok=True)
        config.option.basetemp = unique_path


@pytest.fixture(scope='function')
def algorand_client(
) -> AlgorandClient:
    """Initialize and expose the AlgorandClient.

    Returns
    -------
    AlgorandClient
    """ 
    algorand_client = AlgorandClient.default_local_net()
    algorand_client.set_suggested_params_timeout(0)
    return algorand_client


@pytest.fixture(scope='function')
def dispenser(
    algorand_client
) -> AddressAndSigner:
    """Get the dispenser account.

    Parameters
    ----------
    algorand_client : AlgorandClient
        [fixture] Algorand client.
    
    Returns
    -------
    AddressAndSigner
    """
    if is_localnet(algorand_client.client.algod):
        return algorand_client.account.dispenser()
    else:
        raise RuntimeError('No dispenser defined for non-localnet.')


@pytest.fixture(scope='function')
def dummy_account(
    algorand_client
) -> AddressAndSigner:
    """Generate a throwaway account.

    Parameters
    ----------
    algorand_client : AlgorandClient
        [fixture] Algorand client.

    Returns
    -------
    AddressAndSigner
    """
    return cfa(algorand_client) # Rename so that the local definition is called (not from smart contract folder)


@pytest.fixture(scope='function')
def asset_issuer(
    algorand_client: AlgorandClient, 
) -> AddressAndSigner:
    """Designate an account as the issuer of an asset (the dispenser by default).

    Parameters
    ----------
    algorand_client : AlgorandClient
        [fixture] Algorand client.

    Returns
    -------
    AddressAndSigner
        Account that issued the asset.
    """
    return algorand_client.account.dispenser()


@pytest.fixture(scope='function')
def fee_asset_id(
    algorand_client: AlgorandClient,
    asset_issuer: AddressAndSigner,
    algo_fee_asset: bool
) -> int:
    """Create fee asset, which is not ALGO.

    Parameters
    ----------
    algorand_client : AlgorandClient
        [fixture] Algorand client.
    asset_issuer : AddressAndSigner
        [fixture] Issuer of fee asset (used if `algo_fee_asset` not ALGO).
    algo_fee_asset: bool
        [param] Flag whether to use ALGO as the fee asset.

    Returns
    -------
    int
        Created asset ID.
    """
    if algo_fee_asset:
        return 0
    else:
        return create_asset(
            algorand_client=algorand_client,
            asset_issuer=asset_issuer,
            asset_name="TEST_TOKEN_0",
            unit_name="T0",
            total_amount=42_000_000_000_000_000
        )
        # res = algorand_client.send.asset_create(
        #     AssetCreateParams(
        #         sender=asset_issuer.address,
        #         total = 42_000_000_000_000_000,
        #         decimals = 6,
        #         default_frozen = False,
        #         manager = asset_issuer.address,
        #         reserve = asset_issuer.address,
        #         freeze = asset_issuer.address,
        #         clawback = asset_issuer.address,
        #         unit_name = "T0",
        #         asset_name = "TEST_TOKEN_0",
        #     )
        # )
        # return res["confirmation"]["asset-index"]
    

@pytest.fixture(scope='function')
def gating_asset_id(
    algorand_client: AlgorandClient,
    asset_issuer: AddressAndSigner
) -> int:
    """Create gating asset.

    Parameters
    ----------
    algorand_client : AlgorandClient
        [fixture] Algorand client.
    asset_issuer : AddressAndSigner
        [fixture] Issuer of fee asset (used if `algo_fee_asset` not ALGO).

    Returns
    -------
    int
        Created asset ID.
    """
    return create_asset(
        algorand_client=algorand_client,
        asset_issuer=asset_issuer,
        asset_name="TEST_TOKEN_1",
        unit_name="T1",
        total_amount=42_000_000_000_000_000
    )


@pytest.fixture(scope='function')
def action_inputs(
    fee_asset_id: int,
    gating_asset_id: int
) -> ActionInputs:
    """Get/initialize the action inputs.

    Parameters
    ----------
    fee_asset_id : int
        [fixture] ID of the fee (payment) asset.
    asset_issuer : int
        [fixture] ID of the gating asset.

    Returns
    -------
    ActionInputs
    """
    asa_limit = 10
    ai = ActionInputs(
        asset=fee_asset_id,
        live=True,
        cnt_del_max=2,
        stake_max=100_000_000_000,
        rounds_duration=50
        # delegation_terms_balance = DelegationTermsBalance(
        #     stake_max=100_000_000_000,
        #     cnt_breach_del_max=3,
        #     rounds_breach=10,
        #     gating_asa_list=[(0,0), (0,0), (0,0), (0,0)],
        # )
    )
    ai.terms_reqs.gating_asa_list = [
        (0, 0), 
        (gating_asset_id, asa_limit) # Work with only one ASA
    ]
    return ai
    

@pytest.fixture(scope='function')
def noticeboard(
    algorand_client: AlgorandClient, 
    action_inputs: ActionInputs,
    delben_equal_delman: bool,
    gating_asset_id: int
) -> Noticeboard:
    """Initialize the noticeboard with all of the key users (one per user role/type).

    Parameters
    ----------
    algorand_client : AlgorandClient
        [fixture] Algorand client.
    action_inputs : ActionInputs
        [fixture] Pre-defined actions.
    delben_equal_delman : bool
        [param] Flag whether to use the same address for the delegator beneficiary and the delegator manager.
    gating_asset_id : bool
        [fixture] ID of the gating asset.

    Returns
    -------
    Noticeboard
    """
    dispenser = algorand_client.account.dispenser()
    # Create localnet accounts
    creator = create_and_fund_account(algorand_client, dispenser, [0])
    plaman = create_and_fund_account(algorand_client, dispenser, [0])
    if action_inputs.asset == ALGO_ASA_ID:
        delman_asset_ids = [0]
    else:
        delman_asset_ids = [0, action_inputs.asset]
    if delben_equal_delman:
        delman_asset_ids.append(gating_asset_id)
    delman = create_and_fund_account(
            algorand_client=algorand_client, 
            dispenser=dispenser, 
            asset_ids=delman_asset_ids,
            optin_to_assets=[True]*len(delman_asset_ids),
            fund_w_assets=[True]*len(delman_asset_ids)
        )
    if delben_equal_delman:
        delben = delman
    else:
        delben = create_and_fund_account(
            algorand_client=algorand_client, 
            dispenser=dispenser, 
            asset_ids=[0, gating_asset_id],
            optin_to_assets=[True, True],
            fund_w_assets=[True, True]
        )
    valman = create_and_fund_account(algorand_client, dispenser, [0])
    valown = create_and_fund_account(algorand_client, dispenser, [0])
    partner = create_and_fund_account(algorand_client, dispenser, [0])
    asset_config_manager = create_and_fund_account(algorand_client, dispenser, [0])
    # Initialize noticeboard client
    noticeboard_client = NoticeboardClient(
        algorand_client.client.algod,
        creator=creator.address,
        signer=creator.signer,
        indexer_client=algorand_client.client.indexer,
    )
    # Make class for setting states
    noticeboard = Noticeboard(
        noticeboard_client=noticeboard_client,
        algorand_client=algorand_client,
        assets=[0],
        creator=creator,
        dispenser=dispenser,
        pla_manager=plaman,
        del_managers=[delman],
        del_beneficiaries=[delben],
        val_managers=[valman],
        val_owners=[valown],
        partners=[partner],
        asset_config_manager=asset_config_manager
    )
    noticeboard.initialize_state(
        target_state="SET", 
        action_inputs=action_inputs
    )
    return noticeboard


# @pytest.fixture
# def logger_mockup() -> logging.Logger:
#     """Create an in-memory logger with no handlers to avoid clutter.

#     Returns
#     -------
#     logging.Logger
#     """
#     logger = logging.getLogger('test_logger')
#     logger.setLevel(logging.DEBUG)  # Or desired level
#     return logger


@pytest.fixture(scope='function')
def logger_mockup(tmp_path: Path) -> logging.Logger:
    """Create an in-memory logger with no handlers to avoid clutter.

    Parameters
    ----------
    tmp_path: Path
        [fixture] Path to the where the log is store (determined through Pytest).

    Returns
    -------
    logging.Logger
    """
    logger = Logger(
        log_dirpath=tmp_path,
        log_max_size_bytes=1024,
        log_file_count=1
    )
    # logger = logging.getLogger('test_logger')
    # logger.setLevel(logging.DEBUG)  # Or desired level
    return logger


@pytest.fixture(scope='function')
def valad_app_wrapper_and_valman(
    algorand_client: AlgorandClient,
    noticeboard: Noticeboard,
    action_inputs: ActionInputs,
    # valad_state: bytes=VALAD_STATE_NOT_READY  # Param
    valad_state: bytes  # Param
) -> Tuple[ValadAppWrapper, AddressAndSigner]:
    """Make a validator ad in the desired state.

    Parameters
    ----------
    algorand_client : AlgorandClient
        [fixture] Algorand client.
    noticeboard : Noticeboard
        [fixture] Noticeboard utility from smart contract tests.
    action_inputs : ActionInputs
        [fixture] Action inputs utility from smart contract tests.
    valad_state : bytes
        [param] Targeted validator ad state.

    Returns
    -------
    Tuple[ValadAppWrapper, AddressAndSigner]
        Validator ad app wrapper and validator manager.
    """
    if type(valad_state) != type(''):
        valad_action = translate_valad_state_to_noticeboard_util_class_action(valad_state)
    else:
        valad_action = valad_state
    valad_id = noticeboard.initialize_validator_ad_state(
        action_inputs=action_inputs, 
        target_state=valad_action
    )
    return (
        ValadAppWrapper(
            algorand_client,
            valad_id
        ),
        noticeboard.val_managers[0]
    )
