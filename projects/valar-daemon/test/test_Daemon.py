"""Testing of validator ad and delegator contract handling.

Notes
-----
The tests hare heavily based on the implementations in `Daemon`, such as the usage of `PartkeyManager`.
These tests are akin to integration tests.

Warning
-------
At the time of writing, setting a delco with different delegator manager and beneficiary to LIVE state does not work.
"""
# import sys
import time
import pytest
import logging
from pathlib import Path
from typing import Tuple, Callable

from algosdk import mnemonic
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.account_manager import AddressAndSigner
from algosdk.transaction import AssetFreezeTxn
from algosdk.atomic_transaction_composer import AtomicTransactionComposer, TransactionWithSigner

from valar_daemon.DaemonConfig import DaemonConfig
from valar_daemon.utils import DelegatorContractGlobalState
from valar_daemon.Daemon import Daemon
from valar_daemon.PartkeyManager import PartkeyManager
from valar_daemon.AppWrapper import (
    ValadAppWrapper,
    DelcoAppWrapper
)
from valar_daemon.constants import (
    VALAD_NOT_READY_STATUS_CHANGE_OK,
    VALAD_NOT_READY_STATUS_ATTRIBUTE_ERROR,
    VALAD_NOT_READY_STATUS_NO_CHANGE,
    DELCO_READY_STATUS_NOT_SUBMITTED,
    DELCO_READY_STATUS_BREACH_PAY,
    DELCO_READY_STATUS_REQUESTED,
    DELCO_READY_STATUS_PENDING,
    DELCO_READY_STATUS_SUBMITTED,
    DELCO_READY_STATUS_URL_ERROR,
    VALAD_STATE_READY,
    VALAD_STATE_NOT_READY,
    VALAD_STATE_NOT_LIVE,
    DELCO_STATE_READY,
    DELCO_STATE_SUBMITTED,
    DELCO_STATE_LIVE,
    DELCO_STATE_ENDED_NOT_SUBMITTED,
    DELCO_STATE_ENDED_NOT_CONFIRMED,
    DELCO_STATE_ENDED_LIMITS,
    DELCO_STATE_ENDED_EXPIRED,
    DELCO_STATE_ENDED_CANNOT_PAY,
    ALGO_ASA_ID
)
from test.utils import (
    # translate_valad_state_to_noticeboard_util_class_action,
    translate_delco_state_to_noticeboard_util_class_action,
    wait_for_rounds,
    send_payment,
    get_asset_amount_from_account_info,
    get_min_asa_limit_from_gating_asa_list,
    send_asa,
    generate_partkey,
    calc_sleep_time_for_partkey_generation,
    wait_for_rounds_until_not_submitted
)

# import sys
# sys.path.insert(0, str(Path(*Path(__file__).parent.parts[:-2], 'valar-smart-contracts')))
from tests.noticeboard.utils import Noticeboard # type: ignore
from tests.noticeboard.config import ActionInputs # type: ignore


### Helpers ############################################################################################################

def wait_for_partkey_generation(
    partkey_manager: PartkeyManager,
    address: str, 
    vote_first_valid: int, 
    vote_last_valid: int,
    timeout_s=10
):       
    """Wait for the generation of participation keys.

    Parameters
    ----------
    partkey_manager : PartkeyManager
        Participation key manager.
    address : str
        Address which will participant in consensus.
    vote_first_valid : int
        First round when keys are valid.
    vote_last_valid : int
        Last round when keys are valid.
    timeout_s : int, optional
        Time to wait for the partkeys to get generated, default is 10 s.

    Raises
    ------
    RuntimeError
    """
    # Add generation request
    partkey_manager.add_partkey_generation_request(
        address, 
        vote_first_valid, 
        vote_last_valid
    )
    partkey_manager.refresh() # Request generation at node
    start_time = time.time()
    while time.time() - start_time < timeout_s:
        time.sleep(0.1)
        is_generated = partkey_manager.is_partkey_generated(
            address, 
            vote_first_valid, 
            vote_last_valid
        )
        partkey_manager.refresh() # Refresh buffers
        if is_generated:
            return
    raise RuntimeError(f'Did not generate partkey in {timeout_s} seconds.')


def freeze_asset_for_address(
    algorand_client: AlgorandClient,
    issuer: AddressAndSigner,
    asset_id: int,
    target_address: str
):
    """Freeze an asset for the address.

    Parameters
    ----------
    algorand_client : AlgorandClient
        Algorand client.
    issuer : AddressAndSigner
        The issuer of the asset.
    asset_id : int
        The ID of the issued / to-be-frozen asset.
    target_address : str
        Address for which the asset will be frozen.
    """
    sp = algorand_client.client.algod.suggested_params()
    # Create the freeze transaction
    freeze_txn = AssetFreezeTxn(
        sender=issuer.address,
        sp=sp,
        index=asset_id,
        target=target_address,
        new_freeze_state=True
    )
    # Wrap the transaction with the signer
    txn_with_signer = TransactionWithSigner(
        txn=freeze_txn, 
        signer=issuer.signer
    )
    # Add the transaction to the composer
    composer = AtomicTransactionComposer()
    composer.add_transaction(txn_with_signer)
    # Submit transaction
    result = composer.execute(algorand_client.client.algod, 2)
    assert(result)


### Fixtures ###########################################################################################################

# @pytest.fixture
# def valad_app_wrapper_and_valman(
#     algorand_client: AlgorandClient,
#     noticeboard: Noticeboard,
#     action_inputs: ActionInputs,
#     valad_state: bytes  # Param
# ) -> Tuple[ValadAppWrapper, AddressAndSigner]:
#     """Make a validator ad in the desired state.

#     Parameters
#     ----------
#     algorand_client : AlgorandClient
#         [fixture] Algorand client.
#     noticeboard : Noticeboard
#         [fixture] Noticeboard utility from smart contract tests.
#     action_inputs : ActionInputs
#         [fixture] Action inputs utility from smart contract tests.
#     valad_state : bytes
#         [param] Targeted validator ad state.

#     Returns
#     -------
#     Tuple[ValadAppWrapper, AddressAndSigner]
#         Validator ad app wrapper and validator manager.
#     """
#     valad_action = translate_valad_state_to_noticeboard_util_class_action(valad_state)
#     valad_id = noticeboard.initialize_validator_ad_state(
#         action_inputs=action_inputs, 
#         target_state=valad_action
#     )
#     return (
#         ValadAppWrapper(
#             algorand_client,
#             valad_id
#         ),
#         noticeboard.val_managers[0]
#     )


@pytest.fixture
def valad_and_delco_app_wrapper_and_valman(
    algorand_client: AlgorandClient,
    dispenser: AddressAndSigner,
    noticeboard: Noticeboard,
    action_inputs: ActionInputs,
    valad_app_wrapper_and_valman: Callable[
        [AlgorandClient, Noticeboard, ActionInputs, bytes], 
        Tuple[ValadAppWrapper, AddressAndSigner]
    ],
    asset_issuer: AddressAndSigner,
    fee_asset_id: int,
    gating_asset_id: int,
    delben_equal_delman: bool,  # Param
    delco_state: bytes,         # Param
    breach_pay: bool,           # Param
    breach_stake: bool,         # Param
    breach_gating: bool,        # Param
) -> Tuple[ValadAppWrapper, DelcoAppWrapper, AddressAndSigner]:
    """Make a validator ad and delegator contract in the desired state.

    Parameters
    ----------
    algorand_client : AlgorandClient
        [fixture] Algorand client.
    algorand_client : AddressAndSigner
        [fixture] Dispenser account (well-funded account, i.e., on-chain money sack).
    noticeboard : Noticeboard
        [fixture] Noticeboard utility from smart contract tests.
    action_inputs : ActionInputs
        [fixture] Action inputs utility from smart contract tests.
    valad_app_wrapper_and_valman : Callable[ ..., Tuple[ValadAppWrapper, AddressAndSigner] ]
        [fixture] Callable for making the validator ad.
    asset_issuer : AddressAndSigner
        [fixture] Account that issued the fee asset (payment ASA).
    fee_asset_id : int,
        [fixture] The ID of the fee asset (payment ASA).
    delben_equal_delman : bool
        [param] Flag whether to use the same address for the delegator beneficiary and the delegator manager.
    delco_state : bytes
        [param] Targeted delegator contract state.
    breach_pay : bool
        [param] Flag whether to freeze delegator contract fee asset.
    breach_stake : bool
        [param] Flag whether to push delegator beneficiary's stake over max limit.
    breach_gating : bool
        [param] Flag whether to push gating ASA below minimal limit.

    Returns
    -------
    Tuple[ValadAppWrapper, DelcoAppWrapper, AddressAndSigner]
        Validator ad app wrapper, delegator contract app wrapper, and validator manager.
    """

    # Initialize valad
    valad_app_wrapper, valman = valad_app_wrapper_and_valman

    # Initialize delco
    delco_action = translate_delco_state_to_noticeboard_util_class_action(delco_state)
    if delben_equal_delman:
        action_inputs.del_beneficiary = noticeboard.del_managers[0].address
    else: # Throes error for live state
        action_inputs.del_beneficiary = noticeboard.del_beneficiaries[0].address
    delco_id = noticeboard.initialize_delegator_contract_state(
        action_inputs=action_inputs, 
        val_app_id=valad_app_wrapper.app_id,
        target_state=delco_action
    )
    delco_app_wrapper = DelcoAppWrapper(
        algorand_client,
        delco_id
    )

    # Freeze delegator contract payment funds
    if breach_pay:
        if fee_asset_id == ALGO_ASA_ID:
            raise RuntimeError('Tried freezing ALGO ASA')
        freeze_asset_for_address(
            algorand_client,
            asset_issuer,
            fee_asset_id,
            delco_app_wrapper.delco_client.app_address
        )

    # Increase / decrease delegator beneficiary's stake amount
    # Get max stake from terms
    stake_max = DelegatorContractGlobalState.from_global_state( 
        delco_app_wrapper.delco_client.get_global_state() 
    ).delegation_terms_balance.stake_max
    # Get delegator beneficiary's stake amount
    delben_balance_algo = algorand_client.client.algod.account_info(
        delco_app_wrapper.delben_address
    )['amount']
    txn_fee = 1_000 # 1 milli ALGO
    if breach_stake: # Increase stake amount above limit
        if delben_balance_algo < stake_max:
            send_payment( # End up with stake max limit
                algorand_client=algorand_client, 
                sender=dispenser,  # Top up using dispenser account
                receiver_address=delco_app_wrapper.delben_address, 
                amount=int(stake_max - delben_balance_algo + txn_fee)
            )
    else: # Decrease stake below limit
        if delben_balance_algo >= stake_max:
            send_payment( # End up with one ALGO less than stake max limit
                algorand_client=algorand_client, 
                sender=noticeboard.del_managers[0] if delben_equal_delman else noticeboard.del_beneficiaries[0], 
                receiver_address=dispenser.address, # Send surplus funds to dispenser account
                amount=int(delben_balance_algo - stake_max - 10**6 + txn_fee)
            )

    # Send gating ASAs to / from the delegator beneficiary
    # Get gating ASA minimum limit
    gating_asa_list = DelegatorContractGlobalState.from_global_state(
        delco_app_wrapper.delco_client.get_global_state()
    ).delegation_terms_balance.gating_asa_list
    gating_min = get_min_asa_limit_from_gating_asa_list(
        gating_asa_list=gating_asa_list,
        asset_id=gating_asset_id
    )
    # Get the delegator beneficiary's balance for the gating ASA
    delben_balance_gating = get_asset_amount_from_account_info(
        algorand_client.client.algod.account_info(delco_app_wrapper.delben_address)['assets'],
        gating_asset_id
    )
    if breach_gating: # Send ASA away
        if delben_balance_gating >= gating_min:
            send_asa( # End up with one less than limit
                algorand_client, 
                sender=noticeboard.del_managers[0] if delben_equal_delman else noticeboard.del_beneficiaries[0],
                receiver_address=dispenser.address, 
                amount=delben_balance_gating+1-gating_min, 
                asset_id=gating_asset_id,
            )
    else: # Top up ASA
        if delben_balance_gating < gating_min:
            send_asa( # End up with limit amount
                algorand_client, 
                sender=dispenser,
                receiver_address=delco_app_wrapper.delman_address, 
                amount=gating_min-delben_balance_gating, 
                asset_id=gating_asset_id,
            )

    return (
        valad_app_wrapper,
        delco_app_wrapper,
        valman
    )


# @pytest.fixture
# def logger_mockup(tmp_path: Path) -> logging.Logger:
#     """Create an in-memory logger with no handlers to avoid clutter.

#     Returns
#     -------
#     logging.Logger
#     """
#     logger = Logger(
#         log_dirpath=tmp_path,
#         log_max_size_bytes=1024,
#         log_file_count=1
#     )
#     # logger = logging.getLogger('test_logger')
#     # logger.setLevel(logging.DEBUG)  # Or desired level
#     return logger


@pytest.fixture
def partkey_manager(
    algorand_client: AlgorandClient,
    logger_mockup: logging.Logger
) -> PartkeyManager:
    """Initialize partkey manager.

    Parameters
    ----------
    algorand_client : AlgorandClient
        [fixture] Algorand client.
    logger_mockup : logging.Logger
        [fixture] Logger.

    Returns
    -------
    PartkeyManager
    """
    return PartkeyManager(
        logger_mockup,
        algorand_client
    )


@pytest.fixture
def prepare_daemon_config(
    tmp_path: Path,
    noticeboard: Noticeboard
):
    """Prepare / generate a config file for the daemon.

    Parameters
    ----------
    tmp_path : Path
        [fixture] Path to temporary directory, per test.
    noticeboard : Noticeboard
        [fixture] Noticeboard utility from smart contract tests.
    """
    def _prep_daemon_config(
        valad_id: list
    ) -> Tuple[Path, str]:
        # config_path = Path(Path(__file__).parent, 'tmp')
        config_path = tmp_path
        config_name = 'daemon.config'
        daemon_config = DaemonConfig(
            config_path,
            config_name
        )
        valad_manager = noticeboard.val_managers[0]
        mne = mnemonic.from_private_key(valad_manager.signer.private_key)
        daemon_config.update_config(
            validator_ad_id_list=valad_id,
            validator_manager_mnemonic=mne
        )
        daemon_config.write_config()
        return (config_path, config_name)
    return _prep_daemon_config


### Tests ##############################################################################################################

class TestValadHandler:
    """General simple validator ad handler.
    """

    @staticmethod
    @pytest.mark.parametrize(
        "algo_fee_asset, valad_state, delben_equal_delman, "
        "break_algod, expected_valad_state, expected_valad_status", 
        [   # `delben_equal_delman` has no effect and is only used for `noticeboard` init
            (False, VALAD_STATE_NOT_LIVE,  False, False, VALAD_STATE_NOT_LIVE,  VALAD_NOT_READY_STATUS_NO_CHANGE),
            (False, VALAD_STATE_NOT_READY, False, False, VALAD_STATE_READY,     VALAD_NOT_READY_STATUS_CHANGE_OK),
            (False, VALAD_STATE_READY,     False, False, VALAD_STATE_READY,     VALAD_NOT_READY_STATUS_NO_CHANGE), 
            (True,  VALAD_STATE_NOT_LIVE,  False, False, VALAD_STATE_NOT_LIVE,  VALAD_NOT_READY_STATUS_NO_CHANGE),
            (True,  VALAD_STATE_NOT_READY, False, False, VALAD_STATE_READY,     VALAD_NOT_READY_STATUS_CHANGE_OK),
            (True,  VALAD_STATE_READY,     False, False, VALAD_STATE_READY,     VALAD_NOT_READY_STATUS_NO_CHANGE), 
            (False, VALAD_STATE_NOT_LIVE,  False, True,  VALAD_STATE_NOT_LIVE,  VALAD_NOT_READY_STATUS_NO_CHANGE),
            (False, VALAD_STATE_NOT_READY, False, True,  VALAD_STATE_NOT_READY, VALAD_NOT_READY_STATUS_ATTRIBUTE_ERROR),
            (False, VALAD_STATE_READY,     False, True,  VALAD_STATE_READY,     VALAD_NOT_READY_STATUS_NO_CHANGE), 
            (True,  VALAD_STATE_NOT_LIVE,  False, True,  VALAD_STATE_NOT_LIVE,  VALAD_NOT_READY_STATUS_NO_CHANGE),
            (True,  VALAD_STATE_NOT_READY, False, True,  VALAD_STATE_NOT_READY, VALAD_NOT_READY_STATUS_ATTRIBUTE_ERROR),
            (True,  VALAD_STATE_READY,     False, True,  VALAD_STATE_READY,     VALAD_NOT_READY_STATUS_NO_CHANGE), 
        ]
    )
    def test_maintain_single_valad(
        algorand_client: AlgorandClient,
        valad_app_wrapper_and_valman: Callable[
            [AlgorandClient, Noticeboard, ActionInputs, bytes], 
            Tuple[ValadAppWrapper, AddressAndSigner]
        ],
        logger_mockup: logging.Logger,
        break_algod: bool,
        expected_valad_state: bytes,
        expected_valad_status: int
    ):
        """Try maintaining a single validator ad.

        Notes
        -----
        There is only one validator ad handler, which tries changing the state from `NOT_READY` to `READY`.

        Parameters
        ----------
        algorand_client : AlgorandClient
            [fixture] Algorand client.
        valad_app_wrapper_and_valman : Callable[ ..., Tuple[ValadAppWrapper, AddressAndSigner] ]
            [fixture] Callable for making the validator ad.
        logger_mockup : logging.Logger
            [fixture] Logger.
        break_algod: bool
            [param] Flag indicating whether to break the algod connection/service.
        expected_valad_state: bytes
            [param] The expected state of the validator ad.
        expected_valad_status: int
            [param] The expected status returned by the handler.
        """
        valad_app_wrapper, valman = valad_app_wrapper_and_valman
        valad_state = lambda: valad_app_wrapper.valad_client.get_global_state().state.as_bytes
        algod_address = algorand_client.client.algod.algod_address # Save for later
        if break_algod: 
            algorand_client.client.algod.algod_address = "https://some.cloud"
        res = Daemon.maintain_single_valad(
            algorand_client,
            valman,
            valad_app_wrapper,
            logger_mockup
        )
        assert(res == expected_valad_status)
        algorand_client.client.algod.algod_address = algod_address # Fix in order to get state
        assert(valad_state() == expected_valad_state)


class TestDelcoReadyStateHandler():

    @staticmethod
    @pytest.mark.parametrize(
        "algo_fee_asset, breach_pay, breach_stake, breach_gating, "
        "valad_state, delben_equal_delman, delco_state, "
        "break_algod, expected_delco_state, expected_response", 
        [
            ( # Unique delegator manager and beneficiary
                False, False, False, False, 
                VALAD_STATE_READY, False, DELCO_STATE_READY, 
                False, DELCO_STATE_READY, DELCO_READY_STATUS_REQUESTED
            ),
            ( # Same delegator manager and beneficiary
                False, False, False, False, 
                VALAD_STATE_READY, True, DELCO_STATE_READY, 
                False, DELCO_STATE_READY, DELCO_READY_STATUS_REQUESTED
            ),
            ( # URL error on submission, unique delegator manager and beneficiary
                False, False, False, False, 
                VALAD_STATE_READY, True, DELCO_STATE_READY, 
                True, DELCO_STATE_READY, DELCO_READY_STATUS_URL_ERROR
            ),
            ( # URL error on submission, same delegator manager and beneficiary
                False, False, False, False, 
                VALAD_STATE_READY, False, DELCO_STATE_READY, 
                True, DELCO_STATE_READY, DELCO_READY_STATUS_URL_ERROR
            )
        ]
    )
    def test_add_partkey_generation_request(
        algorand_client: AlgorandClient,
        valad_and_delco_app_wrapper_and_valman: Callable[
            [AlgorandClient, Noticeboard, ActionInputs, bytes], 
            Tuple[ValadAppWrapper, DelcoAppWrapper, AddressAndSigner]
        ],
        partkey_manager: PartkeyManager,
        logger_mockup: logging.Logger,
        break_algod: bool,
        expected_delco_state: bytes,
        expected_response: int
    ):
        """Check that partkey generation request is added.

        Parameters
        ----------
        algorand_client : AlgorandClient
            [fixture] Algorand client.
        valad_and_delco_app_wrapper_and_valman : Callable[ ..., Tuple[...] ]
            [fixture] Function to make a validator ad and delegator contract in the desired state.
        partkey_manager : PartkeyManager
            [fixture] Participation key manager.
        logger_mockup : logging.Logger
            [fixture] Logger.
        break_algod: bool
            [param] Flag indicating whether to break the algod connection/service.
        expected_delco_state : bytes
            [param] The expected state of the delegator contract.
        expected_response : int
            [param] The expected response from the Daemon's handler.
        """
        _, delco_app_wrapper, valad_manager = valad_and_delco_app_wrapper_and_valman
        delco_state = lambda: delco_app_wrapper.delco_client.get_global_state().state.as_bytes
        assert(delco_state() == DELCO_STATE_READY)
        # Inject error by breaking the algod address
        algod_address = algorand_client.client.algod.algod_address # Save for later
        if break_algod: 
            algorand_client.client.algod.algod_address = "https://some.cloud"
        res = Daemon.delco_ready_state_handler(
            algorand_client,
            valad_manager,
            delco_app_wrapper,
            partkey_manager,
            logger_mockup
        )
        assert(res == expected_response)
        algorand_client.client.algod.algod_address = algod_address # Fix in order to get state
        assert(delco_state() == expected_delco_state)

    
    @staticmethod
    @pytest.mark.parametrize(
        "algo_fee_asset, breach_pay, breach_stake, breach_gating, "
        "valad_state, delben_equal_delman, delco_state, "
        "break_algod, expected_delco_state, expected_response", 
        [
            ( # Unique delegator manager and beneficiary
                False, False, False, False, 
                VALAD_STATE_READY, False, DELCO_STATE_READY, 
                False, DELCO_STATE_READY, DELCO_READY_STATUS_PENDING
            ),
            ( # Same delegator manager and beneficiary
                False, False, False, False, 
                VALAD_STATE_READY, True, DELCO_STATE_READY, 
                False, DELCO_STATE_READY, DELCO_READY_STATUS_PENDING
            ),
            ( # URL error on submission, unique delegator manager and beneficiary
                False, False, False, False, 
                VALAD_STATE_READY, True, DELCO_STATE_READY, 
                True, DELCO_STATE_READY, DELCO_READY_STATUS_URL_ERROR
            ),
            ( # URL error on submission, same delegator manager and beneficiary
                False, False, False, False, 
                VALAD_STATE_READY, False, DELCO_STATE_READY, 
                True, DELCO_STATE_READY, DELCO_READY_STATUS_URL_ERROR
            )
        ]
    )
    def test_backoff_for_pending_key_generation(
        algorand_client: AlgorandClient,
        valad_and_delco_app_wrapper_and_valman: Callable[
            [AlgorandClient, Noticeboard, ActionInputs, bytes], 
            Tuple[ValadAppWrapper, DelcoAppWrapper, AddressAndSigner]
        ],
        partkey_manager: PartkeyManager,
        logger_mockup: logging.Logger,
        break_algod: bool,
        expected_delco_state: bytes,
        expected_response: int
    ):
        """Check that nothing happens when calling the handler while key generation is pending.

        Parameters
        ----------
        algorand_client : AlgorandClient
            [fixture] Algorand client.
        valad_and_delco_app_wrapper_and_valman : Callable[ ..., Tuple[...] ]
            [fixture] Function to make a validator ad and delegator contract in the desired state.
        partkey_manager : PartkeyManager
            [fixture] Participation key manager.
        logger_mockup : logging.Logger
            [fixture] Logger.
        break_algod: bool
            [param] Flag indicating whether to break the algod connection/service.
        expected_delco_state : bytes
            [param] The expected state of the delegator contract.
        expected_response : int
            [param] The expected response from the Daemon's handler.
        """
        _, delco_app, valad_manager = valad_and_delco_app_wrapper_and_valman
        # Add keys to buffer -> will say that the keys are pending
        partkey_manager.add_partkey_generation_request(
            delco_app.delben_address, 
            delco_app.round_start, 
            delco_app.round_end,
        )
        delco_state = lambda: delco_app.delco_client.get_global_state().state.as_bytes
        assert(delco_state() == DELCO_STATE_READY)
        # Inject error by breaking the algod address
        algod_address = algorand_client.client.algod.algod_address # Save for later
        if break_algod: 
            algorand_client.client.algod.algod_address = "https://some.cloud"
        res = Daemon.delco_ready_state_handler(
            algorand_client,
            valad_manager,
            delco_app,
            partkey_manager,
            logger_mockup
        )
        assert(res == expected_response)
        algorand_client.client.algod.algod_address = algod_address # Fix in order to get state
        assert(delco_state() == expected_delco_state)

    
    @staticmethod
    @pytest.mark.parametrize(
        "algo_fee_asset, breach_pay, breach_stake, breach_gating, "
        "valad_state, delben_equal_delman, delco_state, "
        "not_submitted, break_algod, expected_delco_state, expected_response", 
        [
            ( # Frozen payment ASA, unique delegator manager and beneficiary
                False, True, False, False, 
                VALAD_STATE_READY, False, DELCO_STATE_READY, 
                False, False, DELCO_STATE_ENDED_CANNOT_PAY, DELCO_READY_STATUS_BREACH_PAY
            ),
            ( # Frozen payment ASA, same delegator manager and beneficiary
                False, True, False, False, 
                VALAD_STATE_READY, True, DELCO_STATE_READY, 
                False, False, DELCO_STATE_ENDED_CANNOT_PAY, DELCO_READY_STATUS_BREACH_PAY
            ),
            # ( # Stake limits breached, unique delegator manager and beneficiary
            #     False, False, True, False, 
            #     VALAD_STATE_READY, False, DELCO_STATE_READY, 
            #     DELCO_STATE_ENDED_CANNOT_PAY, DELCO_READY_STATUS_BREACH_PAY
            # ),
            # ( # Stake limits breached, same delegator manager and beneficiary
            #     False, False, True, False, 
            #     VALAD_STATE_READY, True, DELCO_STATE_READY, 
            #     DELCO_STATE_ENDED_CANNOT_PAY, DELCO_READY_STATUS_BREACH_PAY
            # ),
            # ( # Gating ASA limits breached, unique delegator manager and beneficiary
            #     False, False, False, True, 
            #     VALAD_STATE_READY, False, DELCO_STATE_READY, 
            #     DELCO_STATE_ENDED_CANNOT_PAY, DELCO_READY_STATUS_BREACH_PAY
            # ),
            # ( # Gating ASA limits breached, same delegator manager and beneficiary
            #     False, False, False, True, 
            #     VALAD_STATE_READY, True, DELCO_STATE_READY, 
            #     DELCO_STATE_ENDED_CANNOT_PAY, DELCO_READY_STATUS_BREACH_PAY
            # ),
            ( # URL error on submission, unique delegator manager and beneficiary
                False, False, False, False, 
                VALAD_STATE_READY, True, DELCO_STATE_READY, 
                False, True, DELCO_STATE_READY, DELCO_READY_STATUS_URL_ERROR
            ),
            ( # URL error on submission, same delegator manager and beneficiary
                False, False, False, False, 
                VALAD_STATE_READY, False, DELCO_STATE_READY, 
                False, True, DELCO_STATE_READY, DELCO_READY_STATUS_URL_ERROR
            ),
            ( # Did not submit on time, unique delegator manager and beneficiary
                False, False, False, False, 
                VALAD_STATE_READY, False, DELCO_STATE_READY, 
                True, False, DELCO_STATE_ENDED_NOT_SUBMITTED, DELCO_READY_STATUS_NOT_SUBMITTED
            ),
            ( # Did not submit on time, same delegator manager and beneficiary
                False, False, False, False, 
                VALAD_STATE_READY, True, DELCO_STATE_READY, 
                True, False, DELCO_STATE_ENDED_NOT_SUBMITTED, DELCO_READY_STATUS_NOT_SUBMITTED
            ),
            ( # Submission without problem, unique delegator manager and beneficiary
                False, False, False, False, 
                VALAD_STATE_READY, False, DELCO_STATE_READY, 
                False, False, DELCO_STATE_SUBMITTED, DELCO_READY_STATUS_SUBMITTED
            ),
            ( # Submission without problem, same delegator manager and beneficiary
                False, False, False, False, 
                VALAD_STATE_READY, True, DELCO_STATE_READY, 
                False, False, DELCO_STATE_SUBMITTED, DELCO_READY_STATUS_SUBMITTED
            ),
            ( # Submission without problem, same delegator manager and beneficiary - ALGO ASA (make sure testing stuff runs OK)
                True, False, False, False, 
                VALAD_STATE_READY, True, DELCO_STATE_READY, 
                False, False, DELCO_STATE_SUBMITTED, DELCO_READY_STATUS_SUBMITTED
            )
        ]
    )
    def test_submit_generated_keys(
        algorand_client: AlgorandClient,
        valad_and_delco_app_wrapper_and_valman: Callable[
            [AlgorandClient, Noticeboard, ActionInputs, bytes], 
            Tuple[ValadAppWrapper, DelcoAppWrapper, AddressAndSigner]
        ],
        partkey_manager: PartkeyManager,
        logger_mockup: logging.Logger,
        not_submitted: bool,
        break_algod: bool,
        expected_delco_state: bytes,
        expected_response: int
    ):
        """Test submitting generated keys.

        Parameters
        ----------
        algorand_client : AlgorandClient
            [fixture] Algorand client.
        valad_and_delco_app_wrapper_and_valman : Callable[ ..., Tuple[...] ]
            [fixture] Function to make a validator ad and delegator contract in the desired state.
        partkey_manager : PartkeyManager
            [fixture] Participation key manager.
        logger_mockup : logging.Logger
            [fixture] Logger.
        break_algod: bool
            [param] Flag indicating whether to break the algod connection/service.
        expected_delco_state : bytes
            [param] The expected state of the delegator contract.
        expected_response : int
            [param] The expected response from the Daemon's handler.
        """
        valad_app, delco_app, valad_manager = valad_and_delco_app_wrapper_and_valman
        wait_for_partkey_generation(
            partkey_manager,
            delco_app.delben_address, 
            delco_app.round_start, 
            delco_app.round_end,
        )
        delco_state = lambda: delco_app.delco_client.get_global_state().state.as_bytes
        assert(delco_state() == DELCO_STATE_READY)
        # Inject error by breaking the algod address
        algod_address = algorand_client.client.algod.algod_address # Save for later
        if break_algod: 
            algorand_client.client.algod.algod_address = "https://some.cloud"
        if not_submitted:
            wait_for_rounds_until_not_submitted(algorand_client, valad_app, delco_app)
        res = Daemon.delco_ready_state_handler(
            algorand_client,
            valad_manager,
            delco_app,
            partkey_manager,
            logger_mockup
        )
        assert(res == expected_response)
        algorand_client.client.algod.algod_address = algod_address # Fix in order to get state
        assert(delco_state() == expected_delco_state)


class TestDelcoSubmittedStateHandler():

    @staticmethod
    @pytest.mark.parametrize(
        "algo_fee_asset, breach_pay, breach_stake, breach_gating, "
        "valad_state, delben_equal_delman, delco_state, "
        "expected_delco_state", 
        [
            ( # Still time to confirm, unique delegator manager and beneficiary
                False, False, False, False, 
                VALAD_STATE_READY, False, DELCO_STATE_SUBMITTED, 
                DELCO_STATE_SUBMITTED
            ),
            # ( # Still time to confirm, Same delegator manager and beneficiary
            #     False, False, False, False, 
            #     VALAD_STATE_READY, True, DELCO_STATE_SUBMITTED, 
            #     DELCO_STATE_SUBMITTED
            # )
            ( # Confirmation time elapsed, unique delegator manager and beneficiary
                False, False, False, False, 
                VALAD_STATE_READY, False, DELCO_STATE_SUBMITTED, 
                DELCO_STATE_ENDED_NOT_CONFIRMED
            ),
            # ( # Confirmation time elapsed, same delegator manager and beneficiary
            #     False, False, False, False, 
            #     VALAD_STATE_READY, True, DELCO_STATE_SUBMITTED, 
            #     DELCO_STATE_ENDED_NOT_CONFIRMED
            # )
        ]
    )
    def test_add_partkey_generation_request(
        algorand_client: AlgorandClient,
        valad_and_delco_app_wrapper_and_valman: Callable[
            [AlgorandClient, Noticeboard, ActionInputs, bytes], 
            Tuple[ValadAppWrapper, DelcoAppWrapper, AddressAndSigner]
        ],
        logger_mockup: logging.Logger,
        expected_delco_state: bytes
    ):
        """Test reporting un-submitted keys.

        Parameters
        ----------
        algorand_client : AlgorandClient
            [fixture] Algorand client.
        valad_and_delco_app_wrapper_and_valman : Callable[ ..., Tuple[...] ]
            [fixture] Function to make a validator ad and delegator contract in the desired state.
        logger_mockup : logging.Logger
            [fixture] Logger.
        expected_delco_state : bytes
            [param] The expected state of the delegator contract.
        """
        _, delco_app, valad_manager = valad_and_delco_app_wrapper_and_valman
        # Wait for the confirmation time to elapse
        if expected_delco_state == DELCO_STATE_ENDED_NOT_CONFIRMED:
            global_state = DelegatorContractGlobalState.from_global_state(
                delco_app.delco_client.get_global_state()
            )
            current_round = algorand_client.client.algod.status()["last-round"]
            num_rounds = \
                global_state.round_start + \
                global_state.delegation_terms_general.rounds_setup + \
                global_state.delegation_terms_general.rounds_confirm \
                - current_round
            wait_for_rounds(
                algorand_client,
                num_rounds
            )
        Daemon.delco_submitted_state_handler(
            algorand_client,
            valad_manager,
            delco_app,
            logger_mockup
        )
        delco_state = delco_app.delco_client.get_global_state().state.as_bytes
        assert(delco_state == expected_delco_state)



class TestDelcoLiveStateHandler():

    @staticmethod
    @pytest.mark.parametrize(
        "algo_fee_asset, breach_pay, breach_stake, breach_gating, "
        "valad_state, delben_equal_delman, delco_state, "
        "expected_delco_state", 
        [
            ( # No breach, same delegator manager and beneficiary
                False, False, False, False, 
                VALAD_STATE_READY, True, DELCO_STATE_LIVE, 
                DELCO_STATE_LIVE
            ),
            ( # Max stake limit breach, same delegator manager and beneficiary
                False, False, True, False, 
                VALAD_STATE_READY, True, DELCO_STATE_LIVE, 
                DELCO_STATE_ENDED_LIMITS
            ),
            ( # Insufficient gating ASA, same delegator manager and beneficiary
                False, False, False, True, 
                VALAD_STATE_READY, True, DELCO_STATE_LIVE, 
                DELCO_STATE_ENDED_LIMITS
            )
        ]
    )
    def test_limit_breach(
        algorand_client: AlgorandClient,
        action_inputs: ActionInputs,
        valad_and_delco_app_wrapper_and_valman: Callable[
            [AlgorandClient, Noticeboard, ActionInputs, bytes], 
            Tuple[ValadAppWrapper, DelcoAppWrapper, AddressAndSigner]
        ],
        logger_mockup: logging.Logger,
        expected_delco_state: bytes
    ):
        """Test reporting breached stake (max) or gating (min) limits.

        Parameters
        ----------
        algorand_client : AlgorandClient
            [fixture] Algorand client.
        action_inputs : ActionInputs
            [fixture] Action inputs.
        valad_and_delco_app_wrapper_and_valman : Callable[ ..., Tuple[...] ]
            [fixture] Function to make a validator ad and delegator contract in the desired state.
        logger_mockup : logging.Logger
            [fixture] Logger.
        expected_delco_state : bytes
            [param] The expected state of the delegator contract.
        """
        _, delco_app, valad_manager = valad_and_delco_app_wrapper_and_valman
        # Get rounds to breach
        rounds_between_warning = action_inputs.terms_warn.rounds_warning
        num_of_warning = action_inputs.terms_warn.cnt_warning_max
        for i in range(num_of_warning):
            wait_for_rounds(
                algorand_client,
                rounds_between_warning
            )
            Daemon.delco_live_state_handler(
                algorand_client,
                valad_manager,
                delco_app,
                logger_mockup
            )
        delco_state = delco_app.delco_client.get_global_state().state.as_bytes
        assert(delco_state == expected_delco_state)


    @staticmethod
    @pytest.mark.parametrize(
        "algo_fee_asset, breach_pay, breach_stake, breach_gating, "
        "valad_state, delben_equal_delman, delco_state, "
        "expected_delco_state", 
        [
            ( # No breach, same delegator manager and beneficiary
                False, False, False, False, 
                VALAD_STATE_READY, True, DELCO_STATE_LIVE, 
                DELCO_STATE_LIVE
            ),
            ( # Payment frozen (breached), same delegator manager and beneficiary
                False, True, False, False, 
                VALAD_STATE_READY, True, DELCO_STATE_LIVE, 
                DELCO_STATE_ENDED_CANNOT_PAY
            )
        ]
    )
    def test_pay_breach(
        algorand_client: AlgorandClient,
        valad_and_delco_app_wrapper_and_valman: Callable[
            [AlgorandClient, Noticeboard, ActionInputs, bytes], 
            Tuple[ValadAppWrapper, DelcoAppWrapper, AddressAndSigner]
        ],
        logger_mockup: logging.Logger,
        expected_delco_state: bytes
    ):
        """Test payment frozen.

        Parameters
        ----------
        algorand_client : AlgorandClient
            [fixture] Algorand client.
        valad_and_delco_app_wrapper_and_valman : Callable[ ..., Tuple[...] ]
            [fixture] Function to make a validator ad and delegator contract in the desired state.
        logger_mockup : logging.Logger
            [fixture] Logger.
        expected_delco_state : bytes
            [param] The expected state of the delegator contract.
        """
        _, delco_app, valad_manager = valad_and_delco_app_wrapper_and_valman
        Daemon.delco_live_state_handler(
            algorand_client,
            valad_manager,
            delco_app,
            logger_mockup
        )
        delco_state = delco_app.delco_client.get_global_state().state.as_bytes
        assert(delco_state == expected_delco_state)


    @staticmethod
    @pytest.mark.parametrize(
        "algo_fee_asset, breach_pay, breach_stake, breach_gating, "
        "valad_state, delben_equal_delman, delco_state, "
        "expected_delco_state", 
        [
            ( # Active, same delegator manager and beneficiary
                False, False, False, False, 
                VALAD_STATE_READY, True, DELCO_STATE_LIVE, 
                DELCO_STATE_LIVE
            ),
            ( # Duration elapsed, same delegator manager and beneficiary
                False, False, False, False, 
                VALAD_STATE_READY, True, DELCO_STATE_LIVE, 
                DELCO_STATE_ENDED_EXPIRED
            )
        ]
    )
    def test_expired(
        algorand_client: AlgorandClient,
        valad_and_delco_app_wrapper_and_valman: Callable[
            [AlgorandClient, Noticeboard, ActionInputs, bytes], 
            Tuple[ValadAppWrapper, DelcoAppWrapper, AddressAndSigner]
        ],
        logger_mockup: logging.Logger,
        expected_delco_state: bytes
    ):
        """Test contract expired (successfully ended).

        Parameters
        ----------
        algorand_client : AlgorandClient
            [fixture] Algorand client.
        valad_and_delco_app_wrapper_and_valman : Callable[ ..., Tuple[...] ]
            [fixture] Function to make a validator ad and delegator contract in the desired state.
        logger_mockup : logging.Logger
            [fixture] Logger.
        expected_delco_state : bytes
            [param] The expected state of the delegator contract.
        """
        _, delco_app, valad_manager = valad_and_delco_app_wrapper_and_valman
        # Wait / progress rounds until delco expires
        if expected_delco_state == DELCO_STATE_ENDED_EXPIRED:
            global_state = DelegatorContractGlobalState.from_global_state(
                delco_app.delco_client.get_global_state()
            )
            status = algorand_client.client.algod.status()
            current_round = status["last-round"]
            num_rounds = (global_state.round_end-1) - current_round
            wait_for_rounds(
                algorand_client,
                num_rounds
            )
        Daemon.delco_live_state_handler(
            algorand_client,
            valad_manager,
            delco_app,
            logger_mockup
        )
        delco_state = delco_app.delco_client.get_global_state().state.as_bytes
        assert(delco_state == expected_delco_state)


class TestDelcoEndedStateHandler():

    @staticmethod
    @pytest.mark.parametrize(
        "algo_fee_asset, breach_pay, breach_stake, breach_gating, "
        "valad_state, delben_equal_delman, delco_state, withdraw_contract",
        [
            ( 
                False, False, False, False, 
                VALAD_STATE_READY, True, DELCO_STATE_LIVE, True
            ),
            ( 
                False, False, False, False, 
                VALAD_STATE_READY, True, DELCO_STATE_LIVE, False
            )
        ]
    )
    def test_ended(
        algorand_client: AlgorandClient,
        noticeboard: Noticeboard,
        action_inputs: ActionInputs,
        valad_and_delco_app_wrapper_and_valman: Callable[
            [AlgorandClient, Noticeboard, ActionInputs, bytes], 
            Tuple[ValadAppWrapper, DelcoAppWrapper, AddressAndSigner]
        ],
        partkey_manager: PartkeyManager,
        logger_mockup: logging.Logger,
        withdraw_contract: bool
    ):
        """Test contract ended and the corresponding scheduling of partkey deletion.

        Notes
        -----
        The app can be in any state to schedule deletion (state checking is done one level higher in the daemon).

        Parameters
        ----------
        algorand_client : AlgorandClient
            [fixture] Algorand client.
        noticeboard : Noticeboard
            [fixture] NOticeboard utility class.
        action_inputs : ActionInputs
            [fixture] Action inputs.
        valad_and_delco_app_wrapper_and_valman : Callable[ ..., Tuple[...] ]
            [fixture] Function to make a validator ad and delegator contract in the desired state.
        partkey_manager: PartkeyManager,
            [fixture] Participation key manager.
        logger_mockup : logging.Logger
            [fixture] Logger
        withdraw_contract : bool
            [param] Flag whether to withdraw from contract (change state to withdrawn).
        """
        _, delco_app, _ = valad_and_delco_app_wrapper_and_valman
        # Generate keys
        generate_partkey(
            algorand_client=algorand_client,
            address=delco_app.delben_address,
            vote_first_valid=delco_app.round_start,
            vote_last_valid=delco_app.round_end
        )
        time.sleep(
            calc_sleep_time_for_partkey_generation(delco_app.round_end - delco_app.round_start)
        )
        # Add keys to manager
        partkey_manager.buffer_generated.add_partkey_to_buffer(
            address=delco_app.delben_address,
            vote_first_valid=delco_app.round_start,
            vote_last_valid=delco_app.round_end
        )
        # Determine scheduled deletion round and change state to withdrawn if requested
        if withdraw_contract:
            noticeboard.delegator_action(
                app_id=delco_app.app_id,
                action_name="contract_withdraw",
                action_inputs=action_inputs
            )
            expected_partkey_scheduled_deletion = algorand_client.client.algod.status()['last-round'] + 320
        else:
            # expected_partkey_scheduled_deletion = algorand_client.client.algod.status()['last-round'] - 1
            expected_partkey_scheduled_deletion = algorand_client.client.algod.status()['last-round']
        # Update teh app wrapper's internal state (used by the daemon)
        delco_app.update_dynamic()
        # Execute logic
        Daemon.delco_ended_state_handler(
            algorand_client,
            partkey_manager,
            delco_app,
            logger_mockup
        )
        # Check if partkey deletion correctly scheduled (actual deletion tested as a part of `partkeyManager` tests)
        partkey_scheduled_deletion = partkey_manager.buffer_generated.get_next()['scheduled-deletion']
        assert partkey_scheduled_deletion == expected_partkey_scheduled_deletion


    @staticmethod
    @pytest.mark.parametrize(
        "algo_fee_asset, breach_pay, breach_stake, breach_gating, "
        "valad_state, delben_equal_delman, delco_state",
        [
            ( 
                False, False, False, False, 
                VALAD_STATE_READY, True, DELCO_STATE_LIVE
            )
        ]
    )
    def test_deleted(
        algorand_client: AlgorandClient,
        valad_and_delco_app_wrapper_and_valman: Callable[
            [AlgorandClient, Noticeboard, ActionInputs, bytes], 
            Tuple[ValadAppWrapper, DelcoAppWrapper, AddressAndSigner]
        ],
        partkey_manager: PartkeyManager,
        logger_mockup: logging.Logger,
    ):
        """Test contract deleted and the corresponding scheduling of partkey deletion.

        Notes
        -----
        The app can be in any state to schedule deletion (state checking is done one level higher in the daemon).

        Parameters
        ----------
        algorand_client : AlgorandClient
            [fixture] Algorand client.
        valad_and_delco_app_wrapper_and_valman : Callable[ ..., Tuple[...] ]
            [fixture] Function to make a validator ad and delegator contract in the desired state.
        partkey_manager: PartkeyManager,
            [fixture] Participation key manager.
        logger_mockup : logging.Logger
            [fixture] Logger
        """
        _, delco_app, _ = valad_and_delco_app_wrapper_and_valman
        # Generate keys
        generate_partkey(
            algorand_client=algorand_client,
            address=delco_app.delben_address,
            vote_first_valid=delco_app.round_start,
            vote_last_valid=delco_app.round_end
        )
        time.sleep(
            calc_sleep_time_for_partkey_generation(delco_app.round_end - delco_app.round_start)
        )
        # Add keys to manager
        partkey_manager.buffer_generated.add_partkey_to_buffer(
            address=delco_app.delben_address,
            vote_first_valid=delco_app.round_start,
            vote_last_valid=delco_app.round_end
        )
        # Update teh app wrapper's internal state (used by the daemon)
        delco_app.update_dynamic()
        # Determine scheduled deletion round
        # expected_partkey_scheduled_deletion = algorand_client.client.algod.status()['last-round'] - 1
        expected_partkey_scheduled_deletion = algorand_client.client.algod.status()['last-round']
        # Execute logic
        Daemon.delco_deleted_state_handler(
            algorand_client,
            partkey_manager,
            delco_app,
            logger_mockup
        )
        # Check if partkey deletion correctly scheduled (actual deletion tested as a part of `partkeyManager` tests)
        partkey_scheduled_deletion = partkey_manager.buffer_generated.get_next()['scheduled-deletion']
        assert partkey_scheduled_deletion == expected_partkey_scheduled_deletion


class TestDaemonDelcoHandler:
    """Check if handling of a delco in a specific state is correct.
    """
    pass


class TestDaemonMisc:
    """Test miscellaneous Daemon methods that are not for handling delcos or the run method.
    """
    
    @staticmethod
    @pytest.mark.parametrize(
        "break_algod, expected_is_ok_flag", 
        [   
            (False, True),
            (True, False)
        ]
    )
    def test_check_algod_status(
        algorand_client: AlgorandClient,
        break_algod: bool,
        expected_is_ok_flag: bool
    ):
        """Test whether the check algod status function reports an algod problem.

        Notes
        -----
        Test break algod configuration by changing the algod URL to a dead end (URLError -2).
        A broken internet connection is not included in this automated test (URLError 111).

        Parameters
        ----------
        algorand_client : AlgorandClient
            [fixture] Algorand client.
        break_algod : bool
            [param] Flag whether to break the algod configuration (through URL).
        expected_is_ok_flag : bool
            [param] Expected `is_ok` flag status.
        """
        if break_algod:
            algorand_client.client.algod.algod_address = "https://some.cloud"
        res = Daemon.check_algod_status(algorand_client)
        assert(res.is_ok == expected_is_ok_flag)


class TestDaemonConnectivityReliability:
    """Interrupt Daemon's connectivity to check corresponding error handling.
    """
    
    @staticmethod
    @pytest.mark.parametrize(
        "algo_fee_asset, delben_equal_delman, break_algod, valad_state, first_expected_valad_state, second_expected_valad_state", 
        [   
            (True, True, False, VALAD_STATE_NOT_READY, VALAD_STATE_READY, VALAD_STATE_READY),
            (True, True, True, VALAD_STATE_NOT_READY, VALAD_STATE_NOT_READY, VALAD_STATE_READY)
        ]
    )
    @staticmethod
    def test_algod_error(
        valad_app_wrapper_and_valman: Callable[
            [AlgorandClient, Noticeboard, ActionInputs, bytes], 
            Tuple[ValadAppWrapper, AddressAndSigner]
        ],
        prepare_daemon_config : Callable[
            [Path, Noticeboard], 
            Callable[..., Tuple[Path, str]]
        ],
        break_algod: bool,
        valad_state: bytes,
        first_expected_valad_state: bytes,
        second_expected_valad_state: bytes
    ):
        """Check the daemon can handle an algod connectivity error.

        Parameters
        ----------
        valad_app_wrapper_and_valman : Callable
            [fixture] Callable for making the validator ad.
        prepare_daemon_config : Callable
            [fixture] Prepare configuration for the daemon.
        break_algod : bool
            [param] Flag whether to break the algod configuration (through URL).
        valad_state : bytes
            [param] Targeted validator ad state.
        first_expected_valad_state : bytes
            [param] Expected valad state after breaking algod.
        second_expected_valad_state : bytes
            [param] Expected valad state after fixing algod.
        """
        # Make valad
        valad_app_wrapper, _ = valad_app_wrapper_and_valman
        # Make config file for daemon
        config_path, config_name = prepare_daemon_config(
            valad_id=[valad_app_wrapper.app_id]
        )
        # Initialize daemon
        daemon = Daemon(
            str(Path(config_path, 'daemon.log')),
            str(Path(config_path, config_name))
        )
        # Provoke error
        if break_algod:
            algod_address = daemon.algorand_client.client.algod.algod_address
            daemon.algorand_client.client.algod.algod_address = "https://some.cloud"
        # Run part that should update valad state
        daemon.maintain_contracts()
        # Evaluate
        valad_state = valad_app_wrapper.valad_client.get_global_state().state.as_bytes
        assert(valad_state == first_expected_valad_state)
        # Fix error
        if break_algod:
            daemon.algorand_client.client.algod.algod_address = algod_address
        # Run part that should update valad state
        daemon.maintain_contracts()
        # Evaluate
        valad_state = valad_app_wrapper.valad_client.get_global_state().state.as_bytes
        assert(valad_state == second_expected_valad_state)

        
class TestDaemonRebootReliability:
    """Interrupt Daemon's power (turn Daemon off) to check corresponding error handling.
    """
        
    @staticmethod
    @pytest.mark.parametrize(
        "algo_fee_asset, delben_equal_delman, valad_state", 
        [   
            (True, True, VALAD_STATE_READY)
        ]
    )
    def test_partkey_import_after_reboot(
        valad_app_wrapper_and_valman: Callable[
            [AlgorandClient, Noticeboard, ActionInputs, bytes], 
            Tuple[ValadAppWrapper, AddressAndSigner]
        ],
        prepare_daemon_config : Callable[
            [Path, Noticeboard], 
            Callable[..., Tuple[Path, str]]
        ],
        noticeboard: Noticeboard,
        action_inputs: ActionInputs
    ):
        """Check that the daemon can import already-generated partkeys after a reboot.

        Parameters
        ----------
        valad_app_wrapper_and_valman : Callable
            [fixture] Callable for making the validator ad.
        prepare_daemon_config : Callable
            [fixture] Prepare configuration for the daemon.
        noticeboard: Noticeboard
            [fixture] Noticeboard utility class.
        action_inputs: ActionInputs
            [fixture] Settings for the test.
        """
        # Make valad
        valad_app_wrapper, _ = valad_app_wrapper_and_valman
        # Make config file for daemon
        config_path, config_name = prepare_daemon_config(
            valad_id=[valad_app_wrapper.app_id]
        )
        # Initialize daemon
        daemon = Daemon(
            str(Path(config_path, 'daemon.log')),
            str(Path(config_path, config_name))
        )
        # Create delegator contract for the validator ad that the daemon is servicing
        delco_id = noticeboard.initialize_delegator_contract_state(
            action_inputs=action_inputs, 
            val_app_id=valad_app_wrapper.app_id,
            target_state='READY'
        )
        # Check that the generated partkey buffer is empty
        assert len(daemon.partkey_manager.buffer_generated.partkeys) == 0
        # Run the daemon to service delco and generate the partkey
        daemon.maintain_contracts() # Get contract info and request partkey generation
        daemon.partkey_manager.refresh() # Ask the node to generate the partkey
        # Wait for partkey generation before taking further action
        time.sleep(calc_sleep_time_for_partkey_generation(
            daemon.delco_app_list.get_app_list()[0].round_end - daemon.delco_app_list.get_app_list()[0].round_start
        ))
        # Call once more to detect successful generation and move to generated buffer
        daemon.partkey_manager.refresh()
        # Check that the partkey is in the generated buffer
        assert len(daemon.partkey_manager.buffer_generated.partkeys) == 1
        # Mimic Daemon shutdown by deleting it
        del daemon
        # Mimic Daemon start by initializing it again
        daemon = Daemon(
            str(Path(config_path, 'daemon.log')),
            str(Path(config_path, config_name))
        )
        # Check that the import was successful
        assert len(daemon.partkey_manager.buffer_generated.partkeys) == 1
