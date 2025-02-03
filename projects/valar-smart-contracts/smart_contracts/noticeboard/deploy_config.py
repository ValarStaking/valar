import logging
import os

import algokit_utils
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.client_manager import AlgoSdkClients
from algokit_utils.beta.composer import AssetCreateParams
from algokit_utils.network_clients import (
    get_algod_client,
    get_default_localnet_config,
    get_indexer_client,
    get_kmd_client,
)
from algosdk.constants import ZERO_ADDRESS
from algosdk.transaction import PaymentTxn
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from smart_contracts.noticeboard.deployment.platform_params import (
    ACCEPTED_ASSET_ID,
    ACCEPTED_ASSET_ID_2,
    ACCEPTED_ASSET_INFO,
    ACCEPTED_ASSET_INFO_2,
    NB_STATE,
    NOTICEBOARD_FEES,
    NOTICEBOARD_TERMS_NODE,
    NOTICEBOARD_TERMS_TIMING,
    TC_SHA256,
)
from smart_contracts.noticeboard.deployment.test_config import (
    FEE_OPERATIONAL,
    ROUNDS_DURATION,
    STAKE_MAX,
    TEST_SCENARIO,
    VALIDATOR_TERMS_PRICE,
    VALIDATOR_TERMS_REQS,
    VALIDATOR_TERMS_STAKE,
    VALIDATOR_TERMS_TIME,
    VALIDATOR_TERMS_WARN,
)
from tests.conftest import TestConsts
from tests.noticeboard.config import ActionInputs
from tests.noticeboard.utils import Noticeboard, create_and_fund_account

logger = logging.getLogger(__name__)


# -------------------------------------
# --------  Deployment behavior -------
# -------------------------------------
def deploy(
    algod_client: AlgodClient,
    indexer_client: IndexerClient,
    app_spec: algokit_utils.ApplicationSpecification,
    deployer: algokit_utils.Account,
) -> None:
    from smart_contracts.artifacts.noticeboard.client import (
        NoticeboardClient,
    )

    print("----- Setting up deployment... -----\n")

    algorand_client = AlgorandClient.from_clients(
        AlgoSdkClients(
            algod=get_algod_client(),
            kmd=get_kmd_client(get_default_localnet_config("kmd")),
            indexer=get_indexer_client(),
        )
    )
    algorand_client.set_suggested_params_timeout(0)

    deployment_option = os.getenv("DEPLOYMENT")
    if deployment_option == "test":
        # Get dispenser
        dispenser = algorand_client.account.dispenser()

        if ACCEPTED_ASSET_ID is None:
            # Create an ASA with dispenser
            res = algorand_client.send.asset_create(
                AssetCreateParams(
                    sender=dispenser.address,
                    total = 42_000_000_000_000_000,
                    decimals = 6,
                    default_frozen = False,
                    manager = dispenser.address,
                    reserve = dispenser.address,
                    freeze = dispenser.address,
                    clawback = dispenser.address,
                    unit_name = "USDC",
                    asset_name = "TEST_TOKEN_0",
                )
            )
            asset = res["confirmation"]["asset-index"]
        else:
            asset = ACCEPTED_ASSET_ID

        # Create all needed basic accounts
        accounts: list[AddressAndSigner] = []
        for _ in range(8):
            acc = create_and_fund_account(algorand_client, dispenser, [asset], algo_amount=TestConsts.acc_dispenser_amt, asa_amount=TestConsts.acc_dispenser_asa_amt)  # noqa: E501
            accounts.append(acc)

        creator, pla_manager, asset_config_manager, del_manager, del_beneficiary, val_manager, val_owner, partner = accounts  # noqa: E501
        pla_manager_address = None

    elif deployment_option == "production":
        asset = ACCEPTED_ASSET_ID
        if asset is None:
            raise ValueError("Specify a payment asset to use at the platform.")

        pla_manager_address = os.getenv("PLATFORM_MANAGER_ADDRESS")
        if pla_manager_address == ZERO_ADDRESS:
            raise ValueError("Specify a platform manager address.")

        dispenser = deployer
        creator = deployer
        pla_manager = deployer
        asset_config_manager = deployer
        del_manager = deployer
        del_beneficiary = deployer
        val_manager = deployer
        val_owner = deployer
        partner = deployer
    else:
        raise ValueError(f"Unexpected deployment option: {deployment_option}. Expected 'test' or 'production'.")

    # Add asset to ActionInputs
    action_inputs = ActionInputs(
        # Platform terms:
        tc_sha256 = TC_SHA256,
        noticeboard_fees = NOTICEBOARD_FEES,
        noticeboard_terms_timing = NOTICEBOARD_TERMS_TIMING,
        noticeboard_terms_node = NOTICEBOARD_TERMS_NODE,
        asset_info = ACCEPTED_ASSET_INFO,
        pla_manager = pla_manager_address,
        # For testing purposes:
        terms_time = VALIDATOR_TERMS_TIME,
        terms_price = VALIDATOR_TERMS_PRICE,
        terms_stake = VALIDATOR_TERMS_STAKE,
        terms_reqs = VALIDATOR_TERMS_REQS,
        terms_warn = VALIDATOR_TERMS_WARN,
        rounds_duration = ROUNDS_DURATION,
        stake_max = STAKE_MAX,
        fee_operational = FEE_OPERATIONAL,
    )
    action_inputs.asset = asset
    # For testing purposes:
    action_inputs.terms_price.fee_asset_id = asset   # Update the asset to the one used for the test

    # Create Algokit-generated client
    noticeboard_client = NoticeboardClient(
        algod_client=algod_client,
        creator=creator.address,
        signer=creator.signer,
        indexer_client=indexer_client,
    )

    # Create the wrapped Noticeboard client
    noticeboard = Noticeboard(
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


    # Deploy and set noticeboard
    print("----- Deploying and setting noticeboard... -----\n")
    noticeboard.initialize_state(
        target_state=NB_STATE,
        action_inputs=action_inputs,
    )

    nb_app_id = noticeboard.noticeboard_client.app_id
    print(f"Created and set noticeboard with app ID: {nb_app_id}\n")

    if ACCEPTED_ASSET_ID_2 is not None and ACCEPTED_ASSET_INFO_2 is not None :
        print("Adding second payment asset...\n")
        noticeboard.initialize_state(
            target_state=NB_STATE,
            action_inputs=action_inputs,
        )
        action_inputs.asset_info = ACCEPTED_ASSET_INFO_2
        action_inputs.asset = ACCEPTED_ASSET_ID_2
        noticeboard.noticeboard_action(action_name="noticeboard_optin_asa", action_inputs=action_inputs)
        noticeboard.noticeboard_action(action_name="noticeboard_config_asset", action_inputs=action_inputs)

        print(f"Added support for asset with ID: {action_inputs.asset}\n")

    # Rekey creator to platform owner
    owner_address = os.getenv("OWNER_ADDRESS")
    if owner_address != ZERO_ADDRESS:
        print(f"Rekeying creator to: {owner_address} ...\n")
        sp = algod_client.suggested_params()
        unsigned_txn = PaymentTxn(
            sender=creator.address,
            sp=sp,
            receiver=creator.address,
            amt=0,
            rekey_to=owner_address,
        )
        signed_txn = unsigned_txn.sign(creator.signer.private_key)
        algod_client.send_transaction(signed_txn)
        print(f"Rekeyed creator to owner: {owner_address}\n")

    # Setup test validators and delegators
    if os.getenv("DEPLOYMENT") == "test":
        for v_idx, vi in enumerate(TEST_SCENARIO):
            va_state = vi.state

            if vi.acc_idx is None:
                aa = None
                cnv = True
            else:
                aa = noticeboard.val_owners[vi.acc_idx]
                cnv = False

            # Creating validator ad
            print(f"----- Deploying and setting validator ad idx {v_idx}... -----\n")
            val_app_id = noticeboard.initialize_validator_ad_state(
                action_inputs=action_inputs,
                target_state=va_state,
                action_account=aa,
                create_new_validator=cnv,
            )

            print(f"Created and set validator ad with app ID: {val_app_id} in state {va_state}\n")
            print(f"Validator owner: {noticeboard.get_validator_ad_global_state(val_app_id).val_owner}")
            print(f"Validator manager: {noticeboard.get_validator_ad_global_state(val_app_id).val_manager}\n")

            if vi.dels is None:
                continue

            for d_idx, di in enumerate(vi.dels):
                dc_state = di.state

                if di.acc_idx is None:
                    aa = None
                    cnd = True
                else:
                    aa = noticeboard.del_managers[di.acc_idx]
                    cnd = False

                # Creating delegator contract
                print(f"----- Deploying and setting delegator contract idx {v_idx}.{d_idx} in state {dc_state}... -----\n")  # noqa: E501
                del_app_id = noticeboard.initialize_delegator_contract_state(
                    action_inputs=action_inputs,
                    val_app_id=val_app_id,
                    target_state=dc_state,
                    action_account=aa,
                    create_new_delegator=cnd,
                )

                print(f"Created delegator contract with app ID: {del_app_id} in state {dc_state}\n")
                print(f"Delegator manager: {noticeboard.get_delegator_global_state(del_app_id).del_manager}")
                print(f"Delegator beneficiary: {noticeboard.get_delegator_global_state(del_app_id).del_beneficiary}\n")
