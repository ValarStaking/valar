import pytest
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.config import config

from smart_contracts.artifacts.noticeboard.client import (
    NoticeboardClient,
)
from smart_contracts.helpers.constants import ALGO_ASA_ID
from tests.conftest import TestConsts
from tests.noticeboard.utils import Noticeboard, create_and_fund_account


@pytest.fixture(scope="package", params=[ALGO_ASA_ID, "asa"])
def asset(request: pytest.FixtureRequest, asa: int) -> int:
    if request.param == "asa":
        return asa
    else:
        return request.param


@pytest.fixture(scope="package")
def creator(
    algorand_client: AlgorandClient,
    dispenser: AddressAndSigner,
    asset: int,
) -> AddressAndSigner:
    return create_and_fund_account(algorand_client, dispenser, [asset], algo_amount=TestConsts.acc_dispenser_amt, asa_amount=TestConsts.acc_dispenser_asa_amt)  # noqa: E501

@pytest.fixture(scope="module")
def pla_manager(
    algorand_client: AlgorandClient,
    dispenser: AddressAndSigner,
    asset: int,
) -> AddressAndSigner:
    return create_and_fund_account(algorand_client, dispenser, [asset], algo_amount=TestConsts.acc_dispenser_amt, asa_amount=TestConsts.acc_dispenser_asa_amt)  # noqa: E501

@pytest.fixture(scope="module")
def asset_config_manager(
    algorand_client: AlgorandClient,
    dispenser: AddressAndSigner,
    asset: int,
) -> AddressAndSigner:
    return create_and_fund_account(algorand_client, dispenser, [asset], algo_amount=TestConsts.acc_dispenser_amt, asa_amount=TestConsts.acc_dispenser_asa_amt)  # noqa: E501

@pytest.fixture(scope="function")
def del_manager(
    algorand_client: AlgorandClient,
    dispenser: AddressAndSigner,
    asset: int,
) -> AddressAndSigner:
    return create_and_fund_account(algorand_client, dispenser, [asset], algo_amount=TestConsts.acc_dispenser_amt, asa_amount=TestConsts.acc_dispenser_asa_amt)  # noqa: E501

@pytest.fixture(scope="function")
def del_beneficiary(
    algorand_client: AlgorandClient,
    dispenser: AddressAndSigner,
) -> AddressAndSigner:
    return create_and_fund_account(algorand_client, dispenser, algo_amount=TestConsts.acc_dispenser_amt, asa_amount=TestConsts.acc_dispenser_asa_amt)  # noqa: E501

@pytest.fixture(scope="module")
def val_manager(
    algorand_client: AlgorandClient,
    dispenser: AddressAndSigner,
) -> AddressAndSigner:
    return create_and_fund_account(algorand_client, dispenser, algo_amount=TestConsts.acc_dispenser_amt, asa_amount=TestConsts.acc_dispenser_asa_amt)  # noqa: E501

@pytest.fixture(scope="module")
def val_owner(
    algorand_client: AlgorandClient,
    dispenser: AddressAndSigner,
    asset: int,
) -> AddressAndSigner:
    return create_and_fund_account(algorand_client, dispenser, [asset], algo_amount=TestConsts.acc_dispenser_amt, asa_amount=TestConsts.acc_dispenser_asa_amt)  # noqa: E501

@pytest.fixture(scope="module")
def partner(
    algorand_client: AlgorandClient,
    dispenser: AddressAndSigner,
    asset: int,
) -> AddressAndSigner:
    return create_and_fund_account(algorand_client, dispenser, [asset], algo_amount=TestConsts.acc_dispenser_amt, asa_amount=TestConsts.acc_dispenser_asa_amt)  # noqa: E501

@pytest.fixture(scope="function")
def noticeboard_client(
    algorand_client: AlgorandClient,
    creator: AddressAndSigner,
) -> NoticeboardClient:
    """
    Create a new Noticeboard client.

    Parameters
    ----------
    algorand_client : AlgorandClient

    creator : AddressAndSigner

    Returns
    -------
    noticeboard_client : NoticeboardClient
        Noticeboard app client.
    """

    config.configure(
        debug=True,
        # trace_all=True,
    )

    noticeboard_client = NoticeboardClient(
        algorand_client.client.algod,
        creator=creator.address,
        signer=creator.signer,
        indexer_client=algorand_client.client.indexer,
    )

    return noticeboard_client


@pytest.fixture(scope="function")
def noticeboard(
    noticeboard_client: NoticeboardClient,
    algorand_client: AlgorandClient,
    asset: int,
    creator: AddressAndSigner,
    dispenser: AddressAndSigner,
    pla_manager: AddressAndSigner,
    asset_config_manager: AddressAndSigner,
    del_manager: AddressAndSigner,
    del_beneficiary: AddressAndSigner,
    val_manager: AddressAndSigner,
    val_owner: AddressAndSigner,
    partner: AddressAndSigner,
) -> Noticeboard:

    # Return wrapped noticeboard client
    return Noticeboard(
        noticeboard_client=noticeboard_client,
        algorand_client=algorand_client,
        assets=[asset],
        creator=creator,
        dispenser=dispenser,
        pla_manager=pla_manager,
        asset_config_manager=asset_config_manager,
        del_managers=[del_manager],
        del_beneficiaries=[del_beneficiary],
        val_managers=[val_manager],
        val_owners=[val_owner],
        partners=[partner],
    )


