import base64
import copy
import math
import os
from typing import Literal

from algokit_utils import ABITransactionResponse, TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import AssetFreezeParams, OnlineKeyRegParams, PayParams
from algosdk.abi import AddressType, TupleType, UintType
from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer,
    AtomicTransactionResponse,
    TransactionWithSigner,
)
from algosdk.constants import ZERO_ADDRESS
from algosdk.logic import get_application_address

import tests.noticeboard.validator_ad_interface as va
import tests.validator_ad.delegator_contract_interface as dc
from smart_contracts.artifacts.noticeboard.client import (
    KeyRegTxnInfo,
    NoticeboardAssetInfo,
    NoticeboardClient,
    PartnerCommissions,
)
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    BOX_ASA_KEY_PREFIX,
    BOX_ASSET_KEY_PREFIX,
    BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY,
    BOX_PARTNERS_PREFIX,
    BOX_SIZE_PER_REF,
    BOX_VALIDATOR_AD_TEMPLATE_KEY,
    INCENTIVES_ELIGIBLE_FEE,
    MAXIMUM_NUMBER_OF_DELEGATORS_PER_NODE,
    MBR_ACCOUNT,
    MBR_ASA,
    MBR_NOTICEBOARD_ASSET_BOX,
    MBR_NOTICEBOARD_VALIDATOR_AD_CONTRACT_INCREASE,
    MBR_PARTNER_BOX,
    MBR_USER_BOX,
    MBR_VALIDATOR_AD_ASA_BOX,
    MBR_VALIDATOR_AD_DELEGATOR_CONTRACT_INCREASE,
)
from smart_contracts.noticeboard.constants import (
    ROLE_DEL,
    ROLE_VAL,
    STATE_DEPLOYED,
    STATE_RETIRED,
    STATE_SET,
    STATE_SUSPENDED,
)
from tests.conftest import TestConsts
from tests.utils import (
    KeyRegTxnInfoPlain,
    available_balance,
    balance,
    calc_box_mbr,
    calc_fee_round,
    calc_fees_partner,
    calc_operational_fee,
    create_and_fund_account,
    create_pay_fee_txn,
    get_account_key_reg_info,
    get_box,
    is_online,
    is_opted_in,
    wait_for_rounds,
    wait_for_suspension,
)

from .client_helper import NoticeboardGlobalState, UserInfo, decode_noticeboard_asset_box
from .config import (
    DEFAULT_VALIDATOR_SELF_DISCLOSURE,
    ActionInputs,
)

POSSIBLE_STATES = Literal[
    "START",
    "DEPLOYED",
    "SET",
    "SUSPENDED",
    "RETIRED",
]

POSSIBLE_ACTIONS = Literal[
    "noticeboard_deploy",
    "noticeboard_suspend",
    "noticeboard_migrate",
    "noticeboard_set",
    "noticeboard_key_reg",
    "noticeboard_optin_asa",
    "noticeboard_config_asset",
    "noticeboard_income",
    "template_load_init",
    "template_load_data",
    "partner_config",

    "user_create",
    "user_delete",

    "ad_create",
    "ad_config",
    "ad_delete",
    "ad_ready",
    "ad_self_disclose",
    "ad_terms",
    "ad_income",
    "ad_asa_close",

    "breach_limits",
    "breach_pay",
    "breach_suspended",
    "contract_claim",
    "contract_create",
    "contract_delete",
    "contract_expired",
    "contract_report_expiry_soon",
    "contract_withdraw",
    "keys_confirm",
    "keys_not_confirmed",
    "keys_not_submitted",
    "keys_submit",

    "get_noticeboard_asset",
    "get_noticeboard_user",
]

REL_PATH_TO_DELEGATOR_CONTRACT_BIN = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__), \
        "../../smart_contracts/artifacts/delegator_contract/"
    )
)

REL_PATH_TO_VALIDATOR_AD_BIN = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__), \
        "../../smart_contracts/artifacts/validator_ad/"
    )
)

ACCOUNT_ROLE_LIST = Literal[
    "creator",
    "pla_manager",
    "del_manager",
    "del_beneficiary",
    "val_manager",
    "val_owner",
    "dispenser",
    "unspecified",
    "partner",
]

class Noticeboard:
    noticeboard_client: NoticeboardClient
    algorand_client: AlgorandClient

    assets: list[int]

    creator: AddressAndSigner
    dispenser: AddressAndSigner
    pla_manager: AddressAndSigner
    asset_config_manager: AddressAndSigner
    del_managers: list[AddressAndSigner]
    del_beneficiaries: list[AddressAndSigner]
    val_managers: list[AddressAndSigner]
    val_owners: list[AddressAndSigner]
    partners: list[AddressAndSigner]

    account_active: AddressAndSigner | None = None

    template = bytes(1)
    template_name = bytes(1)

    def __init__(
        self,
        noticeboard_client: NoticeboardClient,
        algorand_client: AlgorandClient,
        assets: list[int],
        creator: AddressAndSigner,
        dispenser: AddressAndSigner,
        pla_manager: AddressAndSigner,
        asset_config_manager: AddressAndSigner,
        del_managers: list[AddressAndSigner],
        del_beneficiaries: list[AddressAndSigner],
        val_managers: list[AddressAndSigner],
        val_owners: list[AddressAndSigner],
        partners: list[AddressAndSigner],
    ):
        self.noticeboard_client = noticeboard_client
        self.algorand_client = algorand_client

        self.assets = assets

        self.creator = creator
        self.dispenser = dispenser
        self.pla_manager = pla_manager
        self.asset_config_manager = asset_config_manager
        self.del_managers = del_managers
        self.del_beneficiaries = del_beneficiaries
        self.val_managers = val_managers
        self.val_owners = val_owners
        self.partners = partners

        self.template = bytes(1)
        self.template_name = bytes(1)

    # ----- ----- ----- ------------------ ----- ----- -----
    # ----- ----- -----  Noticeboard utils ----- ----- -----
    # ----- ----- ----- ------------------ ----- ----- -----

    def noticeboard_action(
        self,
        action_name: POSSIBLE_ACTIONS,
        action_inputs: ActionInputs,
        action_account: AddressAndSigner | None = None,
    ) -> ABITransactionResponse:
        """
        Executes a particular action on the Noticeboard instance (on its current state).
        By default, the action gets executed by the self.creator.
        """

        # By default, set active account to Noticeboard creator
        if action_account is None:
            account = self.creator
        else:
            account = action_account

        if action_name == "noticeboard_deploy":
            res = self.noticeboard_client.create_noticeboard_deploy(
                app_id_old=action_inputs.app_id_old,
                transaction_parameters=TransactionParameters(
                    sender=account.address,
                    signer=account.signer,
                ),
            )

            # Fund the application with MBR
            self.algorand_client.send.payment(
                PayParams(
                    sender=account.address,
                    signer=account.signer,
                    receiver=self.noticeboard_client.app_address,
                    amount=MBR_ACCOUNT,
                )
            )

        elif action_name == "noticeboard_suspend":
            res = self.noticeboard_client.noticeboard_suspend(
                transaction_parameters=TransactionParameters(
                    sender=account.address,
                    signer=account.signer,
                ),
            )

        elif action_name == "noticeboard_migrate":
            res = self.noticeboard_client.noticeboard_migrate(
                app_id_new=action_inputs.app_id_new,
                transaction_parameters=TransactionParameters(
                    sender=account.address,
                    signer=account.signer,
                ),
            )

        elif action_name == "noticeboard_key_reg":
            amount = action_inputs.amount \
                if action_inputs.amount is not None \
                else INCENTIVES_ELIGIBLE_FEE

            receiver = action_inputs.receiver \
                if action_inputs.receiver is not None \
                else self.noticeboard_client.app_address

            # Transfer amount for key reg fee
            pay_fee_txn = create_pay_fee_txn(
                algorand_client=self.algorand_client,
                asset_id=ALGO_ASA_ID,
                amount=amount,
                sender=account.address,
                signer=account.signer,
                receiver=receiver,
            )

            # Increase fee for inner key reg txn
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 2 * sp.min_fee
            sp.flat_fee = True

            res = self.noticeboard_client.noticeboard_key_reg(
                key_reg_info=action_inputs.key_reg.to_key_reg_txn_info(),
                txn=pay_fee_txn,
                transaction_parameters=TransactionParameters(
                    sender=account.address,
                    signer=account.signer,
                    suggested_params=sp,
                ),
            )

        elif action_name == "noticeboard_set":
            gs = self.get_global_state()
            pla_manager = action_inputs.pla_manager \
                if action_inputs.pla_manager is not None \
                else gs.pla_manager
            asset_config_manager = action_inputs.asset_config_manager \
                if action_inputs.asset_config_manager is not None \
                else gs.asset_config_manager
            tc_sha256 = action_inputs.tc_sha256
            noticeboard_fees = action_inputs.noticeboard_fees
            noticeboard_terms_timing = action_inputs.noticeboard_terms_timing
            noticeboard_terms_node = action_inputs.noticeboard_terms_node

            res = self.noticeboard_client.noticeboard_set(
                pla_manager=pla_manager,
                asset_config_manager=asset_config_manager,
                tc_sha256=tc_sha256,
                noticeboard_fees=noticeboard_fees,
                noticeboard_terms_timing=noticeboard_terms_timing,
                noticeboard_terms_node=noticeboard_terms_node,
                transaction_parameters=TransactionParameters(
                    sender=account.address,
                    signer=account.signer,
                ),
            )

        elif action_name == "noticeboard_optin_asa":
            if action_inputs.asset == ALGO_ASA_ID:
                res = None
                pass
            else:
                amount = action_inputs.amount \
                    if action_inputs.amount is not None \
                    else MBR_ASA

                receiver = action_inputs.receiver \
                    if action_inputs.receiver is not None \
                    else self.noticeboard_client.app_address

                # Transfer amount for MBR opt-in for ASA
                pay_fee_txn = create_pay_fee_txn(
                    algorand_client=self.algorand_client,
                    asset_id=ALGO_ASA_ID,
                    amount=amount,
                    sender=account.address,
                    signer=account.signer,
                    receiver=receiver,
                )

                # Increase fee for inner asa opt-in txn
                sp = self.algorand_client.client.algod.suggested_params()
                sp.fee = 2 * sp.min_fee
                sp.flat_fee = True

                res = self.noticeboard_client.noticeboard_optin_asa(
                    asa=action_inputs.asset,
                    txn=pay_fee_txn,
                    transaction_parameters=TransactionParameters(
                        sender=account.address,
                        signer=account.signer,
                        suggested_params=sp,
                    ),
                )

        elif action_name == "noticeboard_config_asset":
            asset = action_inputs.asset
            asset_info = self.app_get_asset_info(asset)
            new_asset_info = action_inputs.asset_info \
                if action_inputs.asset_info is not None \
                else asset_info

            amount = action_inputs.amount \
                if action_inputs.amount is not None \
                else (MBR_NOTICEBOARD_ASSET_BOX if asset_info is None else 0)

            receiver = action_inputs.receiver \
                if action_inputs.receiver is not None \
                else self.noticeboard_client.app_address

            # Transfer amount for MBR increase for asset box creation
            pay_fee_txn = create_pay_fee_txn(
                algorand_client=self.algorand_client,
                asset_id=ALGO_ASA_ID,
                amount=amount,
                sender=account.address,
                signer=account.signer,
                receiver=receiver,
            )

            boxes = [(0, BOX_ASSET_KEY_PREFIX + asset.to_bytes(8, byteorder="big"))]
            foreign_assets = [] if asset == ALGO_ASA_ID else [asset]

            # No inner txn
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 1 * sp.min_fee
            sp.flat_fee = True

            res = self.noticeboard_client.noticeboard_config_asset(
                asset_id=asset,
                asset_info=new_asset_info,
                txn=pay_fee_txn,
                transaction_parameters=TransactionParameters(
                    sender=account.address,
                    signer=account.signer,
                    suggested_params=sp,
                    boxes=boxes,
                    foreign_assets=foreign_assets,
                ),
            )

        elif action_name == "noticeboard_income":
            # Increase fee for inner withdrawal txn
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 2 * sp.min_fee
            sp.flat_fee = True

            asset_id = action_inputs.asset
            foreign_assets = [] if asset_id == ALGO_ASA_ID else [asset_id]

            res = self.noticeboard_client.noticeboard_income(
                asset_id=asset_id,
                transaction_parameters=TransactionParameters(
                    sender=account.address,
                    signer=account.signer,
                    suggested_params=sp,
                    foreign_assets=foreign_assets,
                ),
            )

        elif action_name == "template_load_init":
            template_size = action_inputs.template_size \
                if action_inputs.template_size is not None \
                else len(self.template)
            template_name = action_inputs.template_name \
                if action_inputs.template_name is not None \
                else self.template_name

            # Fund the application with MBR to cover the box creation
            amount = calc_box_mbr(template_size, template_name)
            self.algorand_client.send.payment(
                PayParams(
                    sender=account.address,
                    signer=account.signer,
                    receiver=self.noticeboard_client.app_address,
                    amount=amount,
                )
            )

            box_ref_num = math.ceil(template_size / BOX_SIZE_PER_REF)
            boxes = [(0, template_name) for _ in range(box_ref_num)]

            # Prepare txn parameters
            sp = self.algorand_client.client.algod.suggested_params()
            sp.flat_fee = True
            sp.fee = 1 * sp.min_fee

            res = self.noticeboard_client.template_load_init(
                name=int.from_bytes(template_name, byteorder="big"),
                template_size=template_size,
                transaction_parameters = TransactionParameters(
                    sender = account.address,
                    signer = account.signer,
                    suggested_params = sp,
                    boxes=boxes,
                ),
            )

        elif action_name == "template_load_data":
            template_name = action_inputs.template_name \
                if action_inputs.template_name is not None \
                else self.template_name
            template_data = action_inputs.template \
                if action_inputs.template is not None \
                else self.template
            template_data_offset = action_inputs.template_test_offset \
                if action_inputs.template_test_offset is not None \
                else 0

            data_chunk_num = math.ceil( len(template_data) / BOX_SIZE_PER_REF)
            # TO DO : Figure out why so many box references are needed
            #         even though the data is supplied only in 1024 chunks
            boxes = [(0, template_name) for _ in range(5)]

            for i in range(data_chunk_num):
                offset = i*BOX_SIZE_PER_REF + template_data_offset
                if i == data_chunk_num:
                    idx_end = len(template_data) % BOX_SIZE_PER_REF
                else:
                    idx_end = (i+1)*BOX_SIZE_PER_REF
                data = template_data[i*BOX_SIZE_PER_REF:idx_end]

                res = self.noticeboard_client.template_load_data(
                    name=int.from_bytes(template_name, byteorder="big"),
                    offset=offset,
                    data=data,
                    transaction_parameters = TransactionParameters(
                        sender = account.address,
                        signer = account.signer,
                        boxes=boxes,
                    ),
                )

        elif action_name == "partner_config":
            if action_inputs.partner_address is None:
                partner_address = self.partners[0].address
            else:
                partner_address = action_inputs.partner_address

            if partner_address != ZERO_ADDRESS:
                partner_commissions = action_inputs.partner_commissions
                partner_delete = action_inputs.partner_delete

                if partner_delete:
                    partner_config_amt = 0
                else:
                    if self.app_partner_box(partner_address)[1]:
                        partner_config_amt = 0
                    else:
                        partner_config_amt = MBR_PARTNER_BOX

                amount = action_inputs.amount \
                    if action_inputs.amount is not None \
                    else partner_config_amt

                receiver = action_inputs.receiver \
                    if action_inputs.receiver is not None \
                    else self.noticeboard_client.app_address

                # Transfer amount for MBR increase for asset box creation
                pay_fee_txn = create_pay_fee_txn(
                    algorand_client=self.algorand_client,
                    asset_id=ALGO_ASA_ID,
                    amount=amount,
                    sender=account.address,
                    signer=account.signer,
                    receiver=receiver,
                )

                boxes = [(0, BOX_PARTNERS_PREFIX + AddressType().encode(partner_address))]


                # No inner txn
                sp = self.algorand_client.client.algod.suggested_params()
                sp.fee = 1 * sp.min_fee
                sp.flat_fee = True

                res = self.noticeboard_client.partner_config(
                    partner_address=partner_address,
                    partner_commissions=partner_commissions,
                    partner_delete=partner_delete,
                    txn=pay_fee_txn,
                    transaction_parameters=TransactionParameters(
                        sender=account.address,
                        signer=account.signer,
                        suggested_params=sp,
                        boxes=boxes,
                    ),
                )
            else:
                res = None
                pass

        elif action_name == "user_create":
            gs = self.get_global_state()

            user_role = action_inputs.user_role
            if action_inputs.amount is None:
                if user_role == ROLE_VAL:
                    amount = MBR_USER_BOX + gs.noticeboard_fees.val_user_reg
                elif user_role == ROLE_DEL:
                    amount = MBR_USER_BOX + gs.noticeboard_fees.del_user_reg
                else:
                    amount = 0 # This call will fail because role is unexpected, thus amount doesn't matter.
            else:
                amount = action_inputs.amount

            receiver = action_inputs.receiver \
                if action_inputs.receiver is not None \
                else self.noticeboard_client.app_address

            # Transfer amount for MBR increase for user box creation
            pay_fee_txn = create_pay_fee_txn(
                algorand_client=self.algorand_client,
                asset_id=ALGO_ASA_ID,
                amount=amount,
                sender=account.address,
                signer=account.signer,
                receiver=receiver,
            )

            user_last = gs.dll_val.user_last if user_role==ROLE_VAL else gs.dll_del.user_last

            boxes = [
                (0,  AddressType().encode(account.address)),
                (0,  AddressType().encode(user_last)),
            ]

            # No inner txn
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 1 * sp.min_fee
            sp.flat_fee = True

            res = self.noticeboard_client.user_create(
                user_role=user_role,
                txn=pay_fee_txn,
                transaction_parameters=TransactionParameters(
                    sender=account.address,
                    signer=account.signer,
                    suggested_params=sp,
                    boxes=boxes,
                ),
            )

        elif action_name == "user_delete":
            gs = self.get_global_state()

            user_info = self.app_get_user_info(account.address)
            if user_info is not None:
                boxes = [
                    (0,  AddressType().encode(account.address)),
                    (0,  AddressType().encode(user_info.prev_user)),
                    (0,  AddressType().encode(user_info.next_user)),
                ]
            else:
                boxes = [
                    (0,  AddressType().encode(account.address)),
                ]

            # Increase fee for inner txn that returns the MBR
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 2 * sp.min_fee
            sp.flat_fee = True

            res = self.noticeboard_client.user_delete(
                transaction_parameters=TransactionParameters(
                    sender=account.address,
                    signer=account.signer,
                    suggested_params=sp,
                    boxes=boxes,
                ),
            )

        elif action_name == "get_noticeboard_asset":
            gs = self.get_global_state()

            asset_id = action_inputs.asset
            boxes = [(0, BOX_ASSET_KEY_PREFIX + asset_id.to_bytes(8, byteorder="big"))]

            res = self.noticeboard_client.get_noticeboard_asset(
                asset_id = asset_id,
                transaction_parameters=TransactionParameters(
                    sender=account.address,
                    signer=account.signer,
                    boxes=boxes,
                ),
            )

        elif action_name == "get_noticeboard_user":
            gs = self.get_global_state()

            user = action_inputs.user_to_get
            boxes = [(0,  AddressType().encode(user))]

            res = self.noticeboard_client.get_noticeboard_user(
                user = user,
                transaction_parameters=TransactionParameters(
                    sender=account.address,
                    signer=account.signer,
                    boxes=boxes,
                ),
            )

        else:
            raise ValueError(f"Invalid action name {action_name}")

        return res

    def get_global_state(self) -> NoticeboardGlobalState:
        if self.noticeboard_client.app_id == 0:
            return None
        else:
            return NoticeboardGlobalState.from_global_state(
                self.noticeboard_client.get_global_state()
            )

    def get_state(self) -> POSSIBLE_STATES:
        gs = self.get_global_state()
        if gs is None:
            state = "START"

        else:
            state_enc = gs.state

            if state_enc == STATE_DEPLOYED:
                state = "DEPLOYED"
            elif state_enc == STATE_SET:
                state = "SET"
            elif state_enc == STATE_SUSPENDED:
                state = "SUSPENDED"
            elif state_enc == STATE_RETIRED:
                state = "RETIRED"
            else:
                raise ValueError(f"Unknown state: {state_enc}")

        return state

    def initialize_state(
        self,
        target_state: POSSIBLE_STATES,
        action_inputs: ActionInputs,
        current_state: POSSIBLE_STATES | None = None,
        action_account: AddressAndSigner | None = None,
    ):
        """
        Moves a Noticeboard instance from its current state to the target_state,
        while applying action_inputs to the actions that lead to that state.
        """

        # If account is not given, use the creator account
        if action_account is None:
            action_account_passed = self.creator
        else:
            # Use the given account
            action_account_passed = action_account

        if current_state is None:
            _current_state = self.get_state()
        else:
            _current_state = current_state

        if target_state == "START":
            return

        # Transition to the target state step by step
        path_to_state = self.get_path_to_state(
            target_state=target_state,
            current_state=_current_state,
        )

        for action_name in path_to_state:
            if action_name == "template_load_init_val":
                action_inputs_passed = copy.deepcopy(action_inputs)
                self.template = get_template_val_bin()
                self.template_name = BOX_VALIDATOR_AD_TEMPLATE_KEY
                action_name_passed = "template_load_init"
            elif action_name == "template_load_data_val":
                action_inputs_passed = copy.deepcopy(action_inputs)
                self.template = get_template_val_bin()
                self.template_name = BOX_VALIDATOR_AD_TEMPLATE_KEY
                action_name_passed = "template_load_data"
            elif action_name == "template_load_init_del":
                action_inputs_passed = copy.deepcopy(action_inputs)
                self.template = get_template_del_bin()
                self.template_name = BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY
                action_name_passed = "template_load_init"
            elif action_name == "template_load_data_del":
                action_inputs_passed = copy.deepcopy(action_inputs)
                self.template = get_template_del_bin()
                self.template_name = BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY
                action_name_passed = "template_load_data"
            else:
                action_inputs_passed = action_inputs
                action_name_passed = action_name
            self.noticeboard_action(action_name_passed, action_inputs_passed, action_account_passed)

    def get_path_to_state(
        self,
        target_state: POSSIBLE_STATES,
        current_state: POSSIBLE_STATES | None = None,
    ) -> list[str]:
        """
        Returns a list of actions that transition from the start to the target state.
        """
        to_start = []
        to_deployed = [*to_start, "noticeboard_deploy"]
        to_set = [
            *to_deployed,
            "template_load_init_val",
            "template_load_data_val",
            "template_load_init_del",
            "template_load_data_del",
            "noticeboard_optin_asa",
            "noticeboard_config_asset",
            "partner_config",
            "noticeboard_set",
        ]
        to_suspended = [*to_set, "noticeboard_suspend"]
        to_retired = [*to_suspended, "noticeboard_migrate"]

        state_transitions = {
            "START": to_start,
            "DEPLOYED": to_deployed,
            "SET": to_set,
            "SUSPENDED": to_suspended,
            "RETIRED": to_retired,
        }

        if target_state not in state_transitions:
            raise ValueError(f"Unknown target state: {target_state}")

        if current_state is not None:
            path = [
                item
                for item in state_transitions[target_state]
                if item not in state_transitions[current_state]
            ]
        else:
            path = state_transitions[target_state]

        return path


    # ----- ----- ----- ------------------ ----- ----- -----
    # ----- ----- ----- Validator ad utils ----- ----- -----
    # ----- ----- ----- ------------------ ----- ----- -----

    def validator_action(
        self,
        app_id: int,
        action_name: POSSIBLE_ACTIONS,
        action_inputs: ActionInputs,
        action_account: AddressAndSigner | None = None,
    ) -> ABITransactionResponse:
        """
        Executes a particular action on the Noticeboard instance (on its current state)
        for a particular ValidatorAd.

        By default, the action gets executed by the self.val_owners[0], except ad_ready, which
        gets executed by self.val_managers[0].
        """

        # By default, set active account to validator owner (at index 0)
        if action_account is None:
            account = self.val_owners[0]
        else:
            account = action_account

        if action_name == "ad_create":
            gs = self.get_global_state()
            box_val = self.app_box(BOX_VALIDATOR_AD_TEMPLATE_KEY)
            box_val_size = len(box_val[0])

            # Amount to be paid
            amount = action_inputs.amount \
                if action_inputs.amount is not None \
                else (
                    gs.noticeboard_fees.val_ad_creation +
                    MBR_NOTICEBOARD_VALIDATOR_AD_CONTRACT_INCREASE +
                    MBR_ACCOUNT
                )

            receiver = action_inputs.receiver \
                if action_inputs.receiver is not None \
                else self.noticeboard_client.app_address

            # Transfer amount for MBR increase for ad creation, its funding, possible ASA opt-in,
            # ad creation fee payment, and MBR for delegator contract template box
            pay_txn = create_pay_fee_txn(
                algorand_client=self.algorand_client,
                asset_id=ALGO_ASA_ID,
                amount=amount,
                sender=account.address,
                signer=account.signer,
                receiver=receiver,
            )

            boxes_user = [
                (0,  AddressType().encode(account.address)),
            ]

            # Add boxes for validator template (to load on creation)
            num_load_val = math.ceil(box_val_size / BOX_SIZE_PER_REF)
            boxes_val = [(0, BOX_VALIDATOR_AD_TEMPLATE_KEY) for _ in range(num_load_val)]

            # Get first free app index in user's list at which to ad the app
            user_info = self.app_get_user_info(account.address)
            val_app_idx = action_inputs.val_app_idx \
                if action_inputs.val_app_idx is not None \
                else (0 if user_info is None else user_info.get_free_app_idx())

            # Increase fee for inner txns for ad creation (1), its funding (1),
            # and the actual app call (1).
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 3 * sp.min_fee
            sp.flat_fee = True

            res = self.noticeboard_client.ad_create(
                val_app_idx=val_app_idx,
                txn=pay_txn,
                transaction_parameters=TransactionParameters(
                    sender = account.address,
                    signer = account.signer,
                    suggested_params = sp,
                    boxes=boxes_user+boxes_val,
                ),
            )

        elif action_name == "ad_config":
            gs_val = self.get_validator_ad_global_state(app_id)

            val_manager = action_inputs.val_manager \
                if action_inputs.val_manager is not None \
                else (
                    gs_val.val_manager \
                    if gs_val.val_manager != ZERO_ADDRESS \
                    else self.val_managers[-1].address  # Set val_manager by default to the last in list val_managers
                )

            if action_inputs.live is None:
                # If user doesn't specify the liveliness, set it to keep the current liveliness state
                if gs_val.state == va.STATE_NOT_LIVE:
                    live = False
                elif gs_val.state == va.STATE_NOT_READY or gs_val.state == va.STATE_READY:
                    live = True
                else:
                    live = False # The call will anyhow fail
            else:
                live = action_inputs.live

            cnt_del_max = action_inputs.cnt_del_max \
                if action_inputs.cnt_del_max is not None \
                else MAXIMUM_NUMBER_OF_DELEGATORS_PER_NODE

            boxes_user = [
                (0,  AddressType().encode(account.address)),
            ]

            # Get index of app in user's list
            user_info = self.app_get_user_info(account.address)
            val_app_idx = action_inputs.val_app_idx \
                if action_inputs.val_app_idx is not None \
                else (0 if user_info is None else user_info.get_app_idx(app_id))

            val_app = app_id if action_inputs.val_app_id is None else action_inputs.val_app_id

            # Increase fee for inner txns for ad config.
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 2 * sp.min_fee
            sp.flat_fee = True

            res = self.noticeboard_client.ad_config(
                val_app=val_app,
                val_app_idx=val_app_idx,
                val_manager=val_manager,
                live=live,
                cnt_del_max=cnt_del_max,
                transaction_parameters = TransactionParameters(
                    sender = account.address,
                    signer = account.signer,
                    suggested_params=sp,
                    boxes=boxes_user,
                ),
            )

        elif action_name == "ad_delete":

            foreign_apps = [app_id]

            boxes_user = [
                (0,  AddressType().encode(account.address)),
            ]

            # Get index of app in user's list
            user_info = self.app_get_user_info(account.address)
            val_app_idx = action_inputs.val_app_idx \
                if action_inputs.val_app_idx is not None \
                else (0 if user_info is None else user_info.get_app_idx(app_id))

            val_app = app_id if action_inputs.val_app_id is None else action_inputs.val_app_id

            # Add boxes for delegator template on ValidatorAd to delete it
            box_del = self.app_box(BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY)
            box_del_size = len(box_del[0])
            num_load_del = math.ceil(box_del_size / BOX_SIZE_PER_REF)
            boxes_del_val = [(app_id, BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY) for _ in range(num_load_del)]

            # Increase fee for inner txns for ad_delete, its close out txn,
            # return of freed MBR on Noticeboard, and the additional gas txn.
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 5 * sp.min_fee
            sp.flat_fee = True

            res = self.noticeboard_client.compose(
            ).gas(
                transaction_parameters = TransactionParameters(
                    sender = account.address,
                    signer = account.signer,
                    boxes=boxes_del_val,
                    foreign_apps = foreign_apps,
                ),
            ).ad_delete(
                val_app=val_app,
                val_app_idx=val_app_idx,
                transaction_parameters = TransactionParameters(
                    sender = account.address,
                    signer = account.signer,
                    suggested_params=sp,
                    boxes=boxes_user,
                ),
            ).execute()

        elif action_name == "ad_ready":
            gs_val = self.get_validator_ad_global_state(app_id)

            # By default, ad_ready is issued by correct validator manager
            if action_account is None or action_account == self.val_owners[0]:
                account = next(a for a in self.val_managers if a.address == gs_val.val_manager)
            else:
                account = action_account

            val_owner = action_inputs.val_owner \
                if action_inputs.val_owner is not None \
                else gs_val.val_owner

            if action_inputs.ready is None:
                # If user doesn't specify the readiness, set it to keep the current readiness state
                if gs_val.state == va.STATE_NOT_READY:
                    ready = False
                elif gs_val.state == va.STATE_READY:
                    ready = True
                else:
                    ready = False # The call will anyhow fail
            else:
                ready = action_inputs.ready

            boxes_user = [
                (0,  AddressType().encode(val_owner)),
            ]

            # Get index of app in user's list
            user_info = self.app_get_user_info(val_owner)
            val_app_idx = action_inputs.val_app_idx \
                if action_inputs.val_app_idx is not None \
                else (0 if user_info is None else user_info.get_app_idx(app_id))

            val_app = app_id if action_inputs.val_app_id is None else action_inputs.val_app_id


            # Increase fee for inner txns for ad_ready.
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 2 * sp.min_fee
            sp.flat_fee = True

            res = self.noticeboard_client.ad_ready(
                val_owner=val_owner,
                val_app=val_app,
                val_app_idx=val_app_idx,
                ready=ready,
                transaction_parameters = TransactionParameters(
                    sender = account.address,
                    signer = account.signer,
                    suggested_params=sp,
                    boxes=boxes_user,
                ),
            )

        elif action_name == "ad_self_disclose":
            if action_inputs.val_info is None:
                val_info = copy.deepcopy(DEFAULT_VALIDATOR_SELF_DISCLOSURE)
            else:
                val_info = action_inputs.val_info

            boxes_user = [
                (0,  AddressType().encode(account.address)),
            ]

            # Get index of app in user's list
            user_info = self.app_get_user_info(account.address)
            val_app_idx = action_inputs.val_app_idx \
                if action_inputs.val_app_idx is not None \
                else (0 if user_info is None else user_info.get_app_idx(app_id))

            val_app = app_id if action_inputs.val_app_id is None else action_inputs.val_app_id

            # Increase fee for inner txns for ad self disclose call.
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 2 * sp.min_fee
            sp.flat_fee = True

            res = self.noticeboard_client.ad_self_disclose(
                val_app=val_app,
                val_app_idx=val_app_idx,
                val_info=val_info,
                transaction_parameters = TransactionParameters(
                    sender = account.address,
                    signer = account.signer,
                    suggested_params=sp,
                    boxes=boxes_user,
                ),
            )

        elif action_name == "ad_terms":
            gs_val = self.get_validator_ad_global_state(app_id)

            foreign_apps = [app_id]

            num_txn = 0

            if gs_val is not None and gs_val.state == va.STATE_CREATED:
                # It is necessary to load delegator contract template
                box_del = self.app_box(BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY)
                box_del_size = len(box_del[0])

                mbr_delegator_template_box = action_inputs.mbr_delegator_template_box \
                    if action_inputs.mbr_delegator_template_box \
                    else calc_box_mbr(box_del_size, BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY)

                # Add boxes for delegator template on Noticeboard
                num_load_del = math.ceil(box_del_size / BOX_SIZE_PER_REF)
                boxes_del = [(0, BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY) for _ in range(num_load_del)]
                # Add boxes for delegator template on ValidatorAd
                boxes_del_val = [(app_id, BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY) for _ in range(num_load_del)]

                num_txn += 1 + num_load_del + 1
            else:
                mbr_delegator_template_box = 0

                num_txn += 0
                boxes_del = []
                boxes_del_val = []

            asset = action_inputs.asset
            if asset == ALGO_ASA_ID:
                foreign_assets = []
                validator_ad_new_asset_fee = 0

                num_txn += 0
                box_asa = []
            else:
                foreign_assets = [asset]
                validator_ad_new_asset_fee = MBR_ASA + MBR_VALIDATOR_AD_ASA_BOX

                num_txn += 1
                # Add box for accessing ASA on ValidatorAd
                box_asa = [(app_id, BOX_ASA_KEY_PREFIX + asset.to_bytes(8, byteorder="big"))]

            # Add box for accessing asset payment method on Noticeboard
            box_asset = [(0, BOX_ASSET_KEY_PREFIX + asset.to_bytes(8, byteorder="big"))]

            # Amount to be paid
            amount = action_inputs.amount \
                if action_inputs.amount is not None \
                else (
                    validator_ad_new_asset_fee +
                    mbr_delegator_template_box
                )

            receiver = action_inputs.receiver \
                if action_inputs.receiver is not None \
                else self.noticeboard_client.app_address

            # Transfer amount for MBR increase for ad creation, its funding, possible ASA opt-in,
            # ad creation fee payment, and MBR for delegator contract template box
            pay_txn = create_pay_fee_txn(
                algorand_client=self.algorand_client,
                asset_id=ALGO_ASA_ID,
                amount=amount,
                sender=account.address,
                signer=account.signer,
                receiver=receiver,
            )

            gs = self.get_global_state()

            tc_sha256 = action_inputs.ad_sha256 \
                if action_inputs.ad_sha256 is not None \
                else gs.tc_sha256
            terms_time = copy.deepcopy(action_inputs.terms_time)
            terms_price = copy.deepcopy(action_inputs.terms_price)
            terms_price.fee_asset_id = asset
            terms_stake = copy.deepcopy(action_inputs.terms_stake)
            terms_reqs = copy.deepcopy(action_inputs.terms_reqs)
            terms_warn = copy.deepcopy(action_inputs.terms_warn)

            boxes_user = [
                (0,  AddressType().encode(account.address)),
            ]

            # Get index of app in user's list
            user_info = self.app_get_user_info(account.address)
            val_app_idx = action_inputs.val_app_idx \
                if action_inputs.val_app_idx is not None \
                else (0 if user_info is None else user_info.get_app_idx(app_id))

            val_app = app_id if action_inputs.val_app_id is None else action_inputs.val_app_id

            # Increase fee for inner txns for ad terms (1) and forwarding of payment for the
            # potential asa opt-in (1), the potential asa opt-in at ValidatorAd itself (1),
            # potential loading of delegator contract template (1+num_load_del+1)
            # and two additional gas calls (2) and the app call itself (1).
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = (5+num_txn) * sp.min_fee
            sp.flat_fee = True

            res = self.noticeboard_client.compose(
            ).gas(
                transaction_parameters = TransactionParameters(
                    sender = account.address,
                    signer = account.signer,
                    boxes=boxes_del_val,
                    foreign_apps = foreign_apps,
                ),
            ).gas(
                transaction_parameters = TransactionParameters(
                    sender = account.address,
                    signer = account.signer,
                    boxes=boxes_del,
                ),
            ).ad_terms(
                val_app=val_app,
                val_app_idx=val_app_idx,
                tc_sha256 = tc_sha256,
                terms_time = terms_time,
                terms_price = terms_price,
                terms_stake = terms_stake,
                terms_reqs = terms_reqs,
                terms_warn = terms_warn,
                mbr_delegator_template_box = mbr_delegator_template_box,
                txn = pay_txn,
                transaction_parameters = TransactionParameters(
                    sender = account.address,
                    signer = account.signer,
                    suggested_params = sp,
                    foreign_assets = foreign_assets,
                    boxes=boxes_user + box_asa + box_asset,
                ),
            ).execute()

        elif action_name == "ad_income":
            asset = action_inputs.asset
            if asset == ALGO_ASA_ID:
                foreign_assets = []
            else:
                foreign_assets = [asset]

            boxes_user = [
                (0,  AddressType().encode(account.address)),
            ]

            # Get index of app in user's list
            user_info = self.app_get_user_info(account.address)
            val_app_idx = action_inputs.val_app_idx \
                if action_inputs.val_app_idx is not None \
                else (0 if user_info is None else user_info.get_app_idx(app_id))

            val_app = app_id if action_inputs.val_app_id is None else action_inputs.val_app_id

            # Increase fee for inner txns for ad_income call and the withdrawal of asset.
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 3 * sp.min_fee
            sp.flat_fee = True

            res = self.noticeboard_client.ad_income(
                val_app=val_app,
                val_app_idx=val_app_idx,
                asset_id=asset,
                transaction_parameters = TransactionParameters(
                    sender = account.address,
                    signer = account.signer,
                    suggested_params=sp,
                    boxes=boxes_user,
                    foreign_assets=foreign_assets,
                ),
            )

        elif action_name == "ad_asa_close":
            asset = action_inputs.asset
            if asset == ALGO_ASA_ID:
                foreign_assets = []
                box_asa = []
                # Call will anyhow fail
            else:
                foreign_assets = [asset]
                # Add box for accessing ASA on ValidatorAd
                box_asa = [(app_id, BOX_ASA_KEY_PREFIX + asset.to_bytes(8, byteorder="big"))]

            boxes_user = [
                (0,  AddressType().encode(account.address)),
            ]

            # Get index of app in user's list
            user_info = self.app_get_user_info(account.address)
            val_app_idx = action_inputs.val_app_idx \
                if action_inputs.val_app_idx is not None \
                else (0 if user_info is None else user_info.get_app_idx(app_id))

            val_app = app_id if action_inputs.val_app_id is None else action_inputs.val_app_id

            # Increase fee for inner txns for ad_asa_close call and the withdrawal of asset.
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 3 * sp.min_fee
            sp.flat_fee = True

            res = self.noticeboard_client.ad_asa_close(
                val_app=val_app,
                val_app_idx=val_app_idx,
                asset_id=asset,
                transaction_parameters = TransactionParameters(
                    sender = account.address,
                    signer = account.signer,
                    suggested_params=sp,
                    boxes=boxes_user+box_asa,
                    foreign_assets=foreign_assets,
                ),
            )

        else:
            raise ValueError(f"Invalid action name {action_name}")

        return res

    def get_validator_ad_global_state(
        self, app_id: int
    ) -> va.ValidatorAdGlobalState | None:
        if app_id == 0:
            res = None
        else:
            try:
                validator_ad = va.ValidatorAd(
                    validator_ad_client=va.ValidatorAdClient(
                        algod_client=self.algorand_client.client.algod,
                        app_id=app_id,
                    ),
                    algorand_client=self.algorand_client,
                    acc=self.account_active, # can be any account
                    del_beneficiary=self.account_active, # can be any account
                    del_manager=self.account_active,  # can be any account
                )
                res = validator_ad.get_global_state()
            except Exception as e:
                print(str(e))
                res = None
        return res

    def get_validator_ad_state(self, app_id: int) -> va.POSSIBLE_STATES:
        gs = self.get_validator_ad_global_state(app_id)
        if gs is None:
            state = "START"

        else:
            state_enc = gs.state

            if state_enc == va.STATE_CREATED:
                state = "CREATED"
            elif state_enc == va.STATE_SET:
                state = "SET"
            elif state_enc == va.STATE_READY:
                state = "READY"
            elif state_enc == va.STATE_NOT_READY:
                state = "NOT_READY"
            elif state_enc == va.STATE_NOT_LIVE:
                state = "NOT_LIVE"
            else:
                raise ValueError(f"Unknown state: {state_enc}")

        return state

    def initialize_validator_ad_state(
        self,
        action_inputs: ActionInputs,
        app_id: int = 0,
        target_state: va.POSSIBLE_STATES = "READY",
        current_state: va.POSSIBLE_STATES | None = None,
        action_account: AddressAndSigner | None = None,
        create_new_validator: bool = False,  # noqa: FBT001, FBT002
    ) -> int:
        """
        Moves a ValidatorAd instance from its current state to the target_state,
        while applying action_inputs to the actions that lead to that state.

        By default, the actions to get to the state are executed by the self.val_owners[0],
        unless the create_new_validator is set and a new app (app_id==0) is created.
        In this case, the newly created validator is added as the last element to self.val_owners[-1].
        """

        if app_id == 0:
            # To skip any test that are meant to fail later
            action_inputs_passed = copy.deepcopy(action_inputs)
            action_inputs_passed.receiver = None
            action_inputs_passed.amount = None
            action_inputs_passed.user_role = ROLE_VAL

            # If account is not given
            if action_account is None:
                # Create a new validator (owner) if requested
                if create_new_validator:
                    action_account_passed = create_and_fund_account(
                        self.algorand_client,
                        self.dispenser,
                        self.assets,
                        algo_amount=TestConsts.acc_dispenser_amt,
                        asa_amount=TestConsts.acc_dispenser_asa_amt,
                    )
                    self.val_owners.append(action_account_passed)

                    # Create also a new corresponding validator manager
                    val_manager = create_and_fund_account(
                        self.algorand_client,
                        self.dispenser,
                        self.assets,
                        algo_amount=TestConsts.acc_dispenser_amt,
                        asa_amount=TestConsts.acc_dispenser_asa_amt,
                    )
                    self.val_managers.append(val_manager)
                else:
                    # Use the first val_owner account
                    action_account_passed = self.val_owners[0]

                # Ensure the validator account is registered as validator on the Noticeboard
                user_info = self.app_get_user_info(action_account_passed.address)
                if user_info is None:
                    self.noticeboard_action("user_create", action_inputs_passed, action_account_passed)

            else:
                # Use the given account to create a new ad
                action_account_passed = action_account

            # Create a new validator ad (with default settings)
            res_tmp = self.validator_action(app_id, "ad_create", action_inputs_passed, action_account_passed)
            app_id_passed = res_tmp.return_value
        else:
            app_id_passed = app_id
            action_account_passed = action_account


        if current_state is None:
            _current_state = self.get_validator_ad_state(app_id_passed)
        else:
            _current_state = current_state

        if target_state == "START":
            return

        # Transition to the target state step by step
        path_to_state = self.get_validator_ad_path_to_state(
            target_state=target_state,
            current_state=_current_state,
        )

        for action_name in path_to_state:
            _action_account_passed = action_account_passed
            if action_name == "ad_config_live":
                action_inputs_passed = copy.deepcopy(action_inputs)
                action_inputs_passed.live = True
                action_name_passed = "ad_config"
            elif action_name == "ad_config_not_live":
                action_inputs_passed = copy.deepcopy(action_inputs)
                action_inputs_passed.live = False
                action_name_passed = "ad_config"
            elif action_name == "ad_ready_ready":
                action_inputs_passed = copy.deepcopy(action_inputs)
                action_inputs_passed.ready = True
                action_name_passed = "ad_ready"
                _action_account_passed = None  # Use default (i.e. correct) val_manager
            else:
                action_inputs_passed = action_inputs
                action_name_passed = action_name
            self.validator_action(app_id_passed, action_name_passed, action_inputs_passed, _action_account_passed)

        return app_id_passed

    def get_validator_ad_path_to_state(
        self,
        target_state: va.POSSIBLE_STATES,
        current_state: va.POSSIBLE_STATES | None = None,
    ) -> list[str]:
        """
        Returns a list of actions that transition from the start to the target state.
        """
        to_start = []
        to_created = [*to_start, "ad_create"]
        to_set = [*to_created, "ad_terms"]
        to_not_ready = [*to_set, "ad_config_live"]
        to_not_live = [*to_set, "ad_config_not_live"]
        to_ready = [*to_not_ready, "ad_ready_ready"]

        state_transitions = {
            "START": to_start,
            "CREATED": to_created,
            "SET": to_set,
            "READY": to_ready,
            "NOT_READY": to_not_ready,
            "NOT_LIVE": to_not_live,
        }

        if target_state not in state_transitions:
            raise ValueError(f"Unknown target state: {target_state}")

        if current_state is not None:
            path = [item for item in state_transitions[target_state] if item not in state_transitions[current_state]]
        else:
            path = state_transitions[target_state]

        return path


    # ----- ----- ----- ------------------------ ----- ----- -----
    # ----- ----- ----- Delegator contract utils ----- ----- -----
    # ----- ----- ----- ------------------------ ----- ----- -----
    def delegator_action(
        self,
        app_id : int,
        action_name : POSSIBLE_ACTIONS,
        action_inputs : ActionInputs,
        val_app : int | None = None,
        action_account: AddressAndSigner | None = None,
    ) -> ABITransactionResponse:
        """
        Executes a particular action on the ValidatorAd instance (on its current state)
        for a particular DelegatorContract.
        By default, the action gets executed by the self.del_managers[0].
        """

        # By default, set active account to delegator manager (at index 0)
        if action_account is None:
            account = self.del_managers[0]
        else:
            account = action_account

        if val_app is None:
            # Get correct validator app ID if it was not specified
            gs_del = self.get_delegator_global_state(app_id)
            val_app_id = gs_del.validator_ad_app_id
        else:
            val_app_id = val_app

        if action_name == "contract_create":
            gs_val = self.get_validator_ad_global_state(val_app_id)

            gs = self.get_global_state()
            box_del = get_box(
                algorand_client=self.algorand_client,
                box_name=BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY,
                app_id=val_app_id,
            )
            box_del_size = len(box_del[0])

            # Amount to be paid
            amount = action_inputs.amount \
                if action_inputs.amount is not None \
                else (
                    gs.noticeboard_fees.del_contract_creation +
                    MBR_VALIDATOR_AD_DELEGATOR_CONTRACT_INCREASE
                )

            receiver = action_inputs.receiver \
                if action_inputs.receiver is not None \
                else self.noticeboard_client.app_address

            del_beneficiary = action_inputs.del_beneficiary \
                if action_inputs.del_beneficiary is not None \
                else account.address

            val_owner = action_inputs.val_owner \
                if action_inputs.val_owner is not None \
                else gs_val.val_owner

            rounds_duration = action_inputs.rounds_duration \
                if action_inputs.rounds_duration is not None \
                else gs_val.terms_time.rounds_duration_min

            stake_max = action_inputs.stake_max if \
                action_inputs.stake_max is not None else \
                balance(
                    algorand_client=self.algorand_client,
                    address=del_beneficiary,
                    asset_id=ALGO_ASA_ID,
                )
            fee_round = calc_fee_round(stake_max, gs_val.terms_price.fee_round_min, gs_val.terms_price.fee_round_var)
            fee_setup = gs_val.terms_price.fee_setup

            if action_inputs.partner_address is None:
                partner_address = self.partners[0].address
            else:
                partner_address = action_inputs.partner_address
            boxes_partner = [(0, BOX_PARTNERS_PREFIX + AddressType().encode(partner_address))]

            partner_commissions = self.app_get_partner_commissions(partner_address)
            partner_commissions = partner_commissions if partner_commissions is not None else 0

            amount_expected = fee_setup + calc_operational_fee(fee_round, rounds_duration, 0)
            if partner_address != ZERO_ADDRESS:
                fee_setup_partner, fee_round_partner = calc_fees_partner(partner_commissions, fee_setup, fee_round)
                amount_expected += fee_setup_partner + calc_operational_fee(fee_round_partner, rounds_duration, 0)

            tc_sha256 = action_inputs.del_sha256 \
                if action_inputs.del_sha256 is not None \
                else gs.tc_sha256

            fee_amount = action_inputs.fee_amount \
                if action_inputs.fee_amount is not None \
                else amount_expected

            asset = action_inputs.asset
            # Add assets to the foreign asset array
            foreign_assets = [asa_reg[0] for asa_reg in gs_val.terms_reqs.gating_asa_list if asa_reg[0] != ALGO_ASA_ID]
            if asset != ALGO_ASA_ID:
                foreign_assets.append(asset)
            foreign_accounts = [del_beneficiary]

            # Transfer amount for MBR increase for contract creation at the validator ad, the funding of delegator
            # contract, including for one ASA opt-in even if it is not necessary, and fee for delegator contract
            # creation.
            mbr_txn = create_pay_fee_txn(
                algorand_client=self.algorand_client,
                asset_id=ALGO_ASA_ID,
                amount=amount,
                sender=account.address,
                signer=account.signer,
                receiver=receiver,
            )

            # Payment of the setup fee
            pay_txn = create_pay_fee_txn(
                algorand_client=self.algorand_client,
                asset_id=asset,
                amount=fee_amount,
                sender=account.address,
                signer=account.signer,
                receiver=receiver,
            )

            boxes_user = [
                (0,  AddressType().encode(account.address)),
            ]

            boxes_owner = [
               (0,  AddressType().encode(val_owner)),
            ]

            # Add boxes for delegator template (to load on creation)
            num_load_val = math.ceil(box_del_size / BOX_SIZE_PER_REF)
            boxes_del_template = [(val_app_id, BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY) for _ in range(num_load_val)]

            # Get index in validator's list at which the validator ad is stored
            val_user_info = self.app_get_user_info(val_owner)
            val_app_idx = action_inputs.val_app_idx \
                if action_inputs.val_app_idx is not None \
                else (0 if val_user_info is None else val_user_info.get_app_idx(val_app_id))
            # Get first free app index in user's list at which to add the app
            del_user_info = self.app_get_user_info(account.address)
            del_app_idx = action_inputs.del_app_idx \
                if action_inputs.del_app_idx is not None \
                else (0 if del_user_info is None else del_user_info.get_free_app_idx())

            # Increase fee for inner txns for forwarding calls to validator ad (3),
            # contract creation on validator ad (5), the gas call (1),
            # and the actual app call (1).
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 10 * sp.min_fee
            sp.flat_fee = True

            res = self.noticeboard_client.compose(
            ).gas(
                transaction_parameters=TransactionParameters(
                    sender = account.address,
                    signer = account.signer,
                    boxes=boxes_del_template,
                    foreign_apps=[val_app_id],
                ),
            ).contract_create(
                del_beneficiary=del_beneficiary,
                rounds_duration=rounds_duration,
                stake_max=stake_max,
                val_owner=val_owner,
                val_app=val_app_id,
                val_app_idx=val_app_idx,
                del_app_idx=del_app_idx,
                tc_sha256=tc_sha256,
                partner_address=partner_address,
                mbr_txn=mbr_txn,
                txn=pay_txn,
                transaction_parameters=TransactionParameters(
                    sender = account.address,
                    signer = account.signer,
                    suggested_params = sp,
                    boxes=boxes_user+boxes_owner+boxes_partner,
                    foreign_assets=foreign_assets,
                    accounts=foreign_accounts,
                ),
            ).execute()


        elif action_name == "keys_confirm":
            gs_del = self.get_delegator_global_state(app_id)
            gs_val = self.get_validator_ad_global_state(val_app_id)

            val_owner = action_inputs.val_owner \
                if action_inputs.val_owner is not None \
                else gs_val.val_owner

            boxes_del_manager = [
                (0,  AddressType().encode(account.address)),
            ]

            boxes_val_owner = [
                (0,  AddressType().encode(val_owner)),
            ]

            boxes = boxes_del_manager + boxes_val_owner

            # Get index in validator's list at which the validator ad is stored
            val_user_info = self.app_get_user_info(val_owner)
            val_app_idx = action_inputs.val_app_idx \
                if action_inputs.val_app_idx is not None \
                else (0 if val_user_info is None else val_user_info.get_app_idx(val_app_id))
            # Get index in delegator's list at which the delegator contract is stored
            del_user_info = self.app_get_user_info(account.address)
            del_app_idx = action_inputs.del_app_idx \
                if action_inputs.del_app_idx is not None \
                else (0 if del_user_info is None else del_user_info.get_app_idx(app_id))

            # Add a key reg transaction by delegator beneficiary
            if action_inputs.key_reg_before_confirm:
                key_reg_fee = action_inputs.key_reg_fee \
                    if action_inputs.key_reg_fee is not None \
                    else INCENTIVES_ELIGIBLE_FEE

                if action_inputs.key_reg is not None:
                    vote_first = action_inputs.key_reg.vote_first if \
                        action_inputs.key_reg.vote_first is not None else \
                        gs_del.round_start
                    vote_last = action_inputs.key_reg.vote_last if \
                        action_inputs.key_reg.vote_last is not None else \
                        gs_del.round_end
                    vote_key_dilution = action_inputs.key_reg.vote_key_dilution if \
                        action_inputs.key_reg.vote_key_dilution is not None else \
                        gs_del.vote_key_dilution

                    vote_key=action_inputs.key_reg.vote_pk if \
                        action_inputs.key_reg.vote_pk is not None else \
                        base64.b64encode(gs_del.vote_key).decode("utf-8")
                    selection_key=action_inputs.key_reg.selection_pk if \
                        action_inputs.key_reg.selection_pk is not None else \
                        base64.b64encode(gs_del.sel_key).decode("utf-8")
                    state_proof_key=action_inputs.key_reg.state_proof_pk if \
                        action_inputs.key_reg.state_proof_pk is not None else \
                        base64.b64encode(gs_del.state_proof_key).decode("utf-8")

                    key_sender = action_inputs.key_reg.sender if \
                        action_inputs.key_reg.sender is not None else \
                        gs_del.del_beneficiary
                else:
                    vote_first = gs_del.round_start
                    vote_last = gs_del.round_end
                    vote_key_dilution = gs_del.vote_key_dilution
                    vote_key=base64.b64encode(gs_del.vote_key).decode("utf-8")
                    selection_key=base64.b64encode(gs_del.sel_key).decode("utf-8")
                    state_proof_key=base64.b64encode(gs_del.state_proof_key).decode("utf-8")
                    key_sender = gs_del.del_beneficiary

                del_beneficiary_account = next(acc for acc in ([account] + self.del_beneficiaries + self.del_managers) if acc.address == key_sender)  # noqa: E501, RUF005

                if action_inputs.key_reg_atomically:
                    atc = AtomicTransactionComposer()

                    key_reg_txn = self.algorand_client.transactions.online_key_reg(
                        OnlineKeyRegParams(
                            vote_key=vote_key,
                            selection_key=selection_key,
                            vote_first=vote_first,
                            vote_last=vote_last,
                            vote_key_dilution=vote_key_dilution,
                            state_proof_key= state_proof_key,
                            sender = key_sender,
                            static_fee = key_reg_fee,
                        )
                    )

                    key_reg_txn_w_signer = TransactionWithSigner(
                        txn = key_reg_txn,
                        signer = del_beneficiary_account.signer,
                    )

                    atc.add_transaction(key_reg_txn_w_signer)
                else:
                    self.algorand_client.send.online_key_reg(
                        OnlineKeyRegParams(
                            vote_key=vote_key,
                            selection_key=selection_key,
                            vote_first=vote_first,
                            vote_last=vote_last,
                            vote_key_dilution=vote_key_dilution,
                            state_proof_key= state_proof_key,
                            sender = key_sender,
                            static_fee = key_reg_fee,
                            signer = del_beneficiary_account.signer,
                        )
                    )
            else:
                atc = None


            # Increase fee for forwarding of the call to the validator ad (1), and further to
            # the delegator contract (1), besides the app call (1).
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 3 * sp.min_fee
            sp.flat_fee = True

            if action_inputs.key_reg_atomically:
                res = self.noticeboard_client.compose(
                    atc=atc,
                ).keys_confirm(
                    del_app=app_id,
                    del_app_idx=del_app_idx,
                    val_owner=val_owner,
                    val_app=val_app_id,
                    val_app_idx=val_app_idx,
                    transaction_parameters = TransactionParameters(
                        sender = account.address,
                        signer = account.signer,
                        suggested_params=sp,
                        boxes=boxes,
                    ),
                ).execute()
            else:
                res = self.noticeboard_client.keys_confirm(
                    del_app=app_id,
                    del_app_idx=del_app_idx,
                    val_owner=val_owner,
                    val_app=val_app_id,
                    val_app_idx=val_app_idx,
                    transaction_parameters = TransactionParameters(
                        sender = account.address,
                        signer = account.signer,
                        suggested_params=sp,
                        boxes=boxes,
                    ),
                )

        elif action_name == "keys_not_confirmed":
            if action_inputs.wait_until_keys_not_confirmed is True:
                # Wait until keys can be reported as not confirmed
                gs_del = self.get_delegator_global_state(app_id)
                status = self.algorand_client.client.algod.status()
                current_round = status["last-round"]
                num_rounds = \
                    gs_del.round_start + \
                    gs_del.delegation_terms_general.rounds_setup + \
                    gs_del.delegation_terms_general.rounds_confirm \
                    - current_round
                wait_for_rounds(
                    algorand_client=self.algorand_client,
                    num_rounds=num_rounds,
                    acc=self.dispenser,
                )

            gs_del = self.get_delegator_global_state(app_id)
            gs_val = self.get_validator_ad_global_state(val_app_id)

            del_manager = action_inputs.del_manager \
                if action_inputs.del_manager is not None \
                else gs_del.del_manager

            val_owner = action_inputs.val_owner \
                if action_inputs.val_owner is not None \
                else gs_val.val_owner

            boxes_del_manager = [
                (0,  AddressType().encode(del_manager)),
            ]

            boxes_val_owner = [
                (0,  AddressType().encode(val_owner)),
            ]

            boxes = boxes_del_manager + boxes_val_owner

            # Get index in validator's list at which the validator ad is stored
            val_user_info = self.app_get_user_info(val_owner)
            val_app_idx = action_inputs.val_app_idx \
                if action_inputs.val_app_idx is not None \
                else (0 if val_user_info is None else val_user_info.get_app_idx(val_app_id))
            # Get index in delegator's list at which the delegator contract is stored
            del_user_info = self.app_get_user_info(del_manager)
            del_app_idx = action_inputs.del_app_idx \
                if action_inputs.del_app_idx is not None \
                else (0 if del_user_info is None else del_user_info.get_app_idx(app_id))

            # Add asset to the foreign asset array
            asset = action_inputs.asset \
                if action_inputs.asset is not None \
                else gs_del.delegation_terms_general.fee_asset_id
            if asset != ALGO_ASA_ID:
                foreign_assets = [asset]
            else:
                foreign_assets = None

            partner_address = gs_del.delegation_terms_general.partner_address
            foreign_accounts = [partner_address, del_manager]

            # Increase fee for forwarding the call to validator ad (1) and then delegator contract (1),
            # as well as return of the setup and operational fee (1),
            # (potential) payout of partner fee (1), and (potential) notification message (1).
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 6 * sp.min_fee
            sp.flat_fee = True

            res = self.noticeboard_client.keys_not_confirmed(
                del_manager=del_manager,
                del_app=app_id,
                del_app_idx=del_app_idx,
                val_owner=val_owner,
                val_app=val_app_id,
                val_app_idx=val_app_idx,
                transaction_parameters = TransactionParameters(
                    sender = account.address,
                    signer = account.signer,
                    suggested_params=sp,
                    foreign_assets=foreign_assets,
                    accounts=foreign_accounts,
                    boxes=boxes,
                ),
            )

        elif action_name == "keys_not_submitted":
            gs_del = self.get_delegator_global_state(app_id)
            if action_inputs.wait_until_keys_not_submitted is True:
                # Wait until keys can be reported as not submitted
                status = self.algorand_client.client.algod.status()
                current_round = status["last-round"]
                num_rounds = \
                    gs_del.round_start + \
                    gs_del.delegation_terms_general.rounds_setup \
                    - current_round
                wait_for_rounds(
                    algorand_client=self.algorand_client,
                    num_rounds=num_rounds,
                    acc=self.dispenser,
                )

            gs_del = self.get_delegator_global_state(app_id)
            gs_val = self.get_validator_ad_global_state(val_app_id)

            del_manager = action_inputs.del_manager \
                if action_inputs.del_manager is not None \
                else gs_del.del_manager

            val_owner = action_inputs.val_owner \
                if action_inputs.val_owner is not None \
                else gs_val.val_owner

            boxes_del_manager = [
                (0,  AddressType().encode(del_manager)),
            ]

            boxes_val_owner = [
                (0,  AddressType().encode(val_owner)),
            ]

            boxes = boxes_del_manager + boxes_val_owner

            # Get index in validator's list at which the validator ad is stored
            val_user_info = self.app_get_user_info(val_owner)
            val_app_idx = action_inputs.val_app_idx \
                if action_inputs.val_app_idx is not None \
                else (0 if val_user_info is None else val_user_info.get_app_idx(val_app_id))
            # Get index in delegator's list at which the delegator contract is stored
            del_user_info = self.app_get_user_info(del_manager)
            del_app_idx = action_inputs.del_app_idx \
                if action_inputs.del_app_idx is not None \
                else (0 if del_user_info is None else del_user_info.get_app_idx(app_id))

            # Add asset to the foreign asset array
            asset = action_inputs.asset \
                if action_inputs.asset is not None \
                else gs_del.delegation_terms_general.fee_asset_id
            if asset != ALGO_ASA_ID:
                foreign_assets = [asset]
            else:
                foreign_assets = None

            foreign_accounts = [del_manager]

            # Increase fee for forwarding the call to validator ad (1) and then delegator contract (1),
            # as well as return of the setup and operational fee (1), and (potential) notification message (1).
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 5 * sp.min_fee
            sp.flat_fee = True

            res = self.noticeboard_client.keys_not_submitted(
                del_manager=del_manager,
                del_app=app_id,
                del_app_idx=del_app_idx,
                val_owner=val_owner,
                val_app=val_app_id,
                val_app_idx=val_app_idx,
                transaction_parameters = TransactionParameters(
                    sender = account.address,
                    signer = account.signer,
                    suggested_params=sp,
                    foreign_assets=foreign_assets,
                    accounts=foreign_accounts,
                    boxes=boxes,
                ),
            )

        elif action_name == "keys_submit":
            gs_del = self.get_delegator_global_state(app_id)
            gs_val = self.get_validator_ad_global_state(val_app_id)

            # By default, keys_submit is issued by correct validator manager
            if action_account is None or action_account == self.del_managers[0]:
                account = next(a for a in self.val_managers if a.address == gs_val.val_manager)
            else:
                account = action_account

            vote_first = action_inputs.key_reg.vote_first if \
                action_inputs.key_reg.vote_first is not None else \
                gs_del.round_start
            vote_last = action_inputs.key_reg.vote_last if \
                action_inputs.key_reg.vote_last is not None else \
                gs_del.round_end
            vote_key_dilution = action_inputs.key_reg.vote_key_dilution if \
                action_inputs.key_reg.vote_key_dilution is not None else \
                round(math.sqrt(gs_del.round_end-gs_del.round_start))
            key_sender = action_inputs.key_reg.sender if \
                action_inputs.key_reg.sender is not None else \
                gs_del.del_beneficiary

            del_manager = action_inputs.del_manager \
                if action_inputs.del_manager is not None \
                else gs_del.del_manager

            val_owner = action_inputs.val_owner \
                if action_inputs.val_owner is not None \
                else gs_val.val_owner

            boxes_del_manager = [
                (0,  AddressType().encode(del_manager)),
            ]

            boxes_val_owner = [
                (0,  AddressType().encode(val_owner)),
            ]

            boxes = boxes_del_manager + boxes_val_owner

            # Get index in validator's list at which the validator ad is stored
            val_user_info = self.app_get_user_info(val_owner)
            val_app_idx = action_inputs.val_app_idx \
                if action_inputs.val_app_idx is not None \
                else (0 if val_user_info is None else val_user_info.get_app_idx(val_app_id))
            # Get index in delegator's list at which the delegator contract is stored
            del_user_info = self.app_get_user_info(del_manager)
            del_app_idx = action_inputs.del_app_idx \
                if action_inputs.del_app_idx is not None \
                else (0 if del_user_info is None else del_user_info.get_app_idx(app_id))

            # Add asset to the foreign asset array and box array
            asset = action_inputs.asset \
                if action_inputs.asset is not None \
                else gs_del.delegation_terms_general.fee_asset_id
            if asset != ALGO_ASA_ID:
                foreign_assets = [asset]
                boxes_asset = [(val_app_id, BOX_ASA_KEY_PREFIX + asset.to_bytes(8, byteorder="big"))]

                boxes += boxes_asset
            else:
                foreign_assets = None

            partner_address = gs_del.delegation_terms_general.partner_address
            foreign_accounts = [partner_address, del_manager]

            # Increase fee for forwarding the call to validator ad (1) and then delegator contract (1),
            # as well as distribution of earnings to the validator ad (1) and noticeboard (1),
            # (potential) payout of partner fee (1), and (potential) notification message (1).
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 7 * sp.min_fee
            sp.flat_fee = True

            res = self.noticeboard_client.keys_submit(
                del_manager=del_manager,
                del_app=app_id,
                del_app_idx=del_app_idx,
                val_owner=val_owner,
                val_app=val_app_id,
                val_app_idx=val_app_idx,
                key_reg_txn_info = KeyRegTxnInfo(
                    vote_first=vote_first,
                    vote_last=vote_last,
                    vote_key_dilution=vote_key_dilution,
                    vote_pk=base64.b64decode(action_inputs.key_reg.vote_pk),
                    selection_pk=base64.b64decode(action_inputs.key_reg.selection_pk),
                    state_proof_pk=base64.b64decode(action_inputs.key_reg.state_proof_pk),
                    sender=key_sender,
                ),
                transaction_parameters = TransactionParameters(
                    sender = account.address,
                    signer = account.signer,
                    suggested_params=sp,
                    foreign_assets=foreign_assets,
                    accounts=foreign_accounts,
                    boxes=boxes,
                ),
            )

        elif action_name == "breach_limits":
            gs_del = self.get_delegator_global_state(app_id)
            gs_val = self.get_validator_ad_global_state(val_app_id)

            if action_inputs.wait_until_limit_breach is True:
                # Wait until next limit breach
                status = self.algorand_client.client.algod.status()
                current_round = status["last-round"]
                num_rounds = \
                    gs_del.round_breach_last + \
                    gs_del.delegation_terms_balance.rounds_breach \
                    - current_round
                wait_for_rounds(
                    algorand_client=self.algorand_client,
                    num_rounds=num_rounds,
                    acc=self.dispenser,
                )

            del_manager = action_inputs.del_manager \
                if action_inputs.del_manager is not None \
                else gs_del.del_manager

            val_owner = action_inputs.val_owner \
                if action_inputs.val_owner is not None \
                else gs_val.val_owner

            boxes_del_manager = [
                (0,  AddressType().encode(del_manager)),
            ]

            boxes_val_owner = [
                (0,  AddressType().encode(val_owner)),
            ]

            boxes = boxes_del_manager + boxes_val_owner

            # Get index in validator's list at which the validator ad is stored
            val_user_info = self.app_get_user_info(val_owner)
            val_app_idx = action_inputs.val_app_idx \
                if action_inputs.val_app_idx is not None \
                else (0 if val_user_info is None else val_user_info.get_app_idx(val_app_id))
            # Get index in delegator's list at which the delegator contract is stored
            del_user_info = self.app_get_user_info(del_manager)
            del_app_idx = action_inputs.del_app_idx \
                if action_inputs.del_app_idx is not None \
                else (0 if del_user_info is None else del_user_info.get_app_idx(app_id))

            # Add asset to the foreign asset array and box array
            asset = action_inputs.asset \
                if action_inputs.asset is not None \
                else gs_del.delegation_terms_general.fee_asset_id

            foreign_assets = [asa_reg[0] for asa_reg in gs_val.terms_reqs.gating_asa_list if asa_reg[0] != ALGO_ASA_ID]
            if asset != ALGO_ASA_ID:
                foreign_assets.append(asset)

            if asset != ALGO_ASA_ID:
                boxes_asset = [(val_app_id, BOX_ASA_KEY_PREFIX + asset.to_bytes(8, byteorder="big"))]
                boxes += boxes_asset

            # Add delegator manager account and delegator beneficiary account to the foreign account array
            partner_address = gs_del.delegation_terms_general.partner_address
            foreign_accounts = [gs_del.del_beneficiary, gs_del.del_manager, partner_address]

            # Increase fee for forwarding the call to validator ad (1) and then delegator contract (1),
            # as well as for (potential) distribution of earnings (2), (potential) note sending (1), and
            # the gas app call (1), the actual app call (1), (potential) payout of partner fee (1),
            # and (potential) notification message (1).
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 9 * sp.min_fee
            sp.flat_fee = True

            res = self.noticeboard_client.compose(
            ).gas(
                transaction_parameters=TransactionParameters(
                    sender = account.address,
                    signer = account.signer,
                    foreign_assets=foreign_assets,
                    accounts=foreign_accounts,
                    foreign_apps=[val_app_id, app_id]
                ),
            ).breach_limits(
                del_manager=del_manager,
                del_app=app_id,
                del_app_idx=del_app_idx,
                val_owner=val_owner,
                val_app=val_app_id,
                val_app_idx=val_app_idx,
                transaction_parameters = TransactionParameters(
                    sender = account.address,
                    signer = account.signer,
                    suggested_params=sp,
                    boxes=boxes,
                ),
            ).execute()

        elif action_name == "breach_pay":

            gs_del = self.get_delegator_global_state(app_id)
            gs_val = self.get_validator_ad_global_state(val_app_id)

            del_manager = action_inputs.del_manager \
                if action_inputs.del_manager is not None \
                else gs_del.del_manager

            val_owner = action_inputs.val_owner \
                if action_inputs.val_owner is not None \
                else gs_val.val_owner

            boxes_del_manager = [
                (0,  AddressType().encode(del_manager)),
            ]

            boxes_val_owner = [
                (0,  AddressType().encode(val_owner)),
            ]

            boxes = boxes_del_manager + boxes_val_owner

            # Get index in validator's list at which the validator ad is stored
            val_user_info = self.app_get_user_info(val_owner)
            val_app_idx = action_inputs.val_app_idx \
                if action_inputs.val_app_idx is not None \
                else (0 if val_user_info is None else val_user_info.get_app_idx(val_app_id))
            # Get index in delegator's list at which the delegator contract is stored
            del_user_info = self.app_get_user_info(del_manager)
            del_app_idx = action_inputs.del_app_idx \
                if action_inputs.del_app_idx is not None \
                else (0 if del_user_info is None else del_user_info.get_app_idx(app_id))

            # Add asset to the foreign asset array and box array
            asset = action_inputs.asset \
                if action_inputs.asset is not None \
                else gs_del.delegation_terms_general.fee_asset_id
            if asset != ALGO_ASA_ID:
                foreign_assets = [asset]
                boxes_asset = [(val_app_id, BOX_ASA_KEY_PREFIX + asset.to_bytes(8, byteorder="big"))]

                boxes += boxes_asset
            else:
                foreign_assets = None

            # Add delegator manager and partner account to the foreign account array
            partner_address = gs_del.delegation_terms_general.partner_address
            foreign_accounts = [partner_address, del_manager]

            if action_inputs.freeze_delegator_contract is True:
                # Freeze delegator contract account
                self.algorand_client.send.asset_freeze(
                    AssetFreezeParams(
                        sender=self.dispenser.address,
                        asset_id=asset,
                        account=get_application_address(app_id),
                        frozen=True,
                        signer=self.dispenser.signer,
                    )
                )

            # Increase fee for forwarding the call to validator ad (1) and then delegator contract (1),
            # as well as for (potential) distribution of earnings (2), (potential) payout of partner fee (1),
            # and (potential) notification message (1).
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 7 * sp.min_fee
            sp.flat_fee = True

            res = self.noticeboard_client.breach_pay(
                del_manager=del_manager,
                del_app=app_id,
                del_app_idx=del_app_idx,
                val_owner=val_owner,
                val_app=val_app_id,
                val_app_idx=val_app_idx,
                transaction_parameters = TransactionParameters(
                    sender = account.address,
                    signer = account.signer,
                    suggested_params=sp,
                    foreign_assets=foreign_assets,
                    boxes=boxes,
                ),
            )

        elif action_name == "breach_suspended":
            gs_del = self.get_delegator_global_state(app_id)
            gs_val = self.get_validator_ad_global_state(val_app_id)

            if action_inputs.wait_until_suspended:
                wait_for_suspension(self.algorand_client, gs_del.del_beneficiary, self.dispenser)

            del_manager = action_inputs.del_manager \
                if action_inputs.del_manager is not None \
                else gs_del.del_manager

            val_owner = action_inputs.val_owner \
                if action_inputs.val_owner is not None \
                else gs_val.val_owner


            boxes_del_manager = [
                (0,  AddressType().encode(del_manager)),
            ]

            boxes_val_owner = [
                (0,  AddressType().encode(val_owner)),
            ]

            boxes = boxes_del_manager + boxes_val_owner

            # Get index in validator's list at which the validator ad is stored
            val_user_info = self.app_get_user_info(val_owner)
            val_app_idx = action_inputs.val_app_idx \
                if action_inputs.val_app_idx is not None \
                else (0 if val_user_info is None else val_user_info.get_app_idx(val_app_id))
            # Get index in delegator's list at which the delegator contract is stored
            del_user_info = self.app_get_user_info(del_manager)
            del_app_idx = action_inputs.del_app_idx \
                if action_inputs.del_app_idx is not None \
                else (0 if del_user_info is None else del_user_info.get_app_idx(app_id))

            # Add asset to the foreign asset array and box array
            asset = action_inputs.asset \
                if action_inputs.asset is not None \
                else gs_del.delegation_terms_general.fee_asset_id
            if asset != ALGO_ASA_ID:
                foreign_assets = [asset]
                boxes_asset = [(val_app_id, BOX_ASA_KEY_PREFIX + asset.to_bytes(8, byteorder="big"))]

                boxes += boxes_asset
            else:
                foreign_assets = None

            # Add delegator manager account, delegator beneficiary account, and partner account to the foreign accounts
            partner_address = gs_del.delegation_terms_general.partner_address
            foreign_accounts = [del_manager, gs_del.del_beneficiary, partner_address]

            # Increase fee for forwarding the call to validator ad (1) and then delegator contract (1),
            # as well as for (potential) distribution of earnings (2), (potential) payout of partner fee (1),
            # the gas transaction (1), and (potential) notification message (1).
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 8 * sp.min_fee
            sp.flat_fee = True

            res = self.noticeboard_client.compose(
            ).gas(
                transaction_parameters = TransactionParameters(
                    sender = account.address,
                    signer = account.signer,
                    suggested_params=sp,
                    accounts=foreign_accounts,
                    foreign_assets=foreign_assets,   # Must be provided for some reason together with app IDs
                    foreign_apps=[val_app, app_id],  # Needed for some reason because later not enough
                ),
            ).breach_suspended(
                del_manager=del_manager,
                del_app=app_id,
                del_app_idx=del_app_idx,
                val_owner=val_owner,
                val_app=val_app_id,
                val_app_idx=val_app_idx,
                transaction_parameters = TransactionParameters(
                    sender = account.address,
                    signer = account.signer,
                    suggested_params=sp,
                    boxes=boxes,
                ),
            ).execute()

        elif action_name == "contract_claim":
            gs_del = self.get_delegator_global_state(app_id)
            gs_val = self.get_validator_ad_global_state(val_app_id)

            del_manager = action_inputs.del_manager \
                if action_inputs.del_manager is not None \
                else gs_del.del_manager

            val_owner = action_inputs.val_owner \
                if action_inputs.val_owner is not None \
                else gs_val.val_owner

            boxes_del_manager = [
                (0,  AddressType().encode(del_manager)),
            ]

            boxes_val_owner = [
                (0,  AddressType().encode(val_owner)),
            ]

            boxes = boxes_del_manager + boxes_val_owner

            # Get index in validator's list at which the validator ad is stored
            val_user_info = self.app_get_user_info(val_owner)
            val_app_idx = action_inputs.val_app_idx \
                if action_inputs.val_app_idx is not None \
                else (0 if val_user_info is None else val_user_info.get_app_idx(val_app_id))
            # Get index in delegator's list at which the delegator contract is stored
            del_user_info = self.app_get_user_info(del_manager)
            del_app_idx = action_inputs.del_app_idx \
                if action_inputs.del_app_idx is not None \
                else (0 if del_user_info is None else del_user_info.get_app_idx(app_id))

            # Add asset to the foreign asset array and box array
            asset = action_inputs.asset \
                if action_inputs.asset is not None \
                else gs_del.delegation_terms_general.fee_asset_id
            if asset != ALGO_ASA_ID:
                foreign_assets = [asset]
                boxes_asset = [(val_app_id, BOX_ASA_KEY_PREFIX + asset.to_bytes(8, byteorder="big"))]

                boxes += boxes_asset
            else:
                foreign_assets = None

            partner_address = gs_del.delegation_terms_general.partner_address
            foreign_accounts = [partner_address, del_manager]

            # Increase fee for forwarding the call to validator ad (1) and then delegator contract (1),
            # as well as for (potential) distribution of earnings (2),
            # and (potential) payout of partner fee (1).
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 6 * sp.min_fee
            sp.flat_fee = True

            res = self.noticeboard_client.contract_claim(
                del_manager=del_manager,
                del_app=app_id,
                del_app_idx=del_app_idx,
                val_owner=val_owner,
                val_app=val_app_id,
                val_app_idx=val_app_idx,
                transaction_parameters = TransactionParameters(
                    sender = account.address,
                    signer = account.signer,
                    suggested_params=sp,
                    foreign_assets=foreign_assets,
                    accounts=foreign_accounts,
                    boxes=boxes,
                ),
            )

        elif action_name == "contract_expired":
            if action_inputs.wait_until_expired is True:
                # Wait until contract expires
                gs_del = self.get_delegator_global_state(app_id)
                status = self.algorand_client.client.algod.status()
                current_round = status["last-round"]
                num_rounds = (gs_del.round_end-1) - current_round
                wait_for_rounds(
                    algorand_client=self.algorand_client,
                    num_rounds=num_rounds,
                    acc=self.dispenser,
                )

            gs_del = self.get_delegator_global_state(app_id)
            gs_val = self.get_validator_ad_global_state(val_app_id)

            del_manager = action_inputs.del_manager \
                if action_inputs.del_manager is not None \
                else gs_del.del_manager

            val_owner = action_inputs.val_owner \
                if action_inputs.val_owner is not None \
                else gs_val.val_owner

            boxes_del_manager = [
                (0,  AddressType().encode(del_manager)),
            ]

            boxes_val_owner = [
                (0,  AddressType().encode(val_owner)),
            ]

            boxes = boxes_del_manager + boxes_val_owner

            # Get index in validator's list at which the validator ad is stored
            val_user_info = self.app_get_user_info(val_owner)
            val_app_idx = action_inputs.val_app_idx \
                if action_inputs.val_app_idx is not None \
                else (0 if val_user_info is None else val_user_info.get_app_idx(val_app_id))
            # Get index in delegator's list at which the delegator contract is stored
            del_user_info = self.app_get_user_info(del_manager)
            del_app_idx = action_inputs.del_app_idx \
                if action_inputs.del_app_idx is not None \
                else (0 if del_user_info is None else del_user_info.get_app_idx(app_id))

            # Add asset to the foreign asset array and box array
            asset = action_inputs.asset \
                if action_inputs.asset is not None \
                else gs_del.delegation_terms_general.fee_asset_id
            if asset != ALGO_ASA_ID:
                foreign_assets = [asset]
                boxes_asset = [(val_app_id, BOX_ASA_KEY_PREFIX + asset.to_bytes(8, byteorder="big"))]

                boxes += boxes_asset
            else:
                foreign_assets = None

            partner_address = gs_del.delegation_terms_general.partner_address
            foreign_accounts = [partner_address, del_manager]

            # Increase fee for forwarding the call to validator ad (1) and then delegator contract (1),
            # as well as for (potential) distribution of earnings (2), (potential) payout of partner fee (1),
            # and (potential) notification message (1).
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 7 * sp.min_fee
            sp.flat_fee = True

            res = self.noticeboard_client.contract_expired(
                del_manager=del_manager,
                del_app=app_id,
                del_app_idx=del_app_idx,
                val_owner=val_owner,
                val_app=val_app_id,
                val_app_idx=val_app_idx,
                transaction_parameters = TransactionParameters(
                    sender = account.address,
                    signer = account.signer,
                    suggested_params=sp,
                    foreign_assets=foreign_assets,
                    accounts=foreign_accounts,
                    boxes=boxes,
                ),
            )

        elif action_name == "contract_withdraw":

            # By default, contract_withdraw is issued by delegator manager (at index 0)
            if action_account is None:
                account = self.del_managers[0]
            else:
                account = action_account

            gs_del = self.get_delegator_global_state(app_id)
            gs_val = self.get_validator_ad_global_state(val_app_id)

            val_owner = action_inputs.val_owner \
                if action_inputs.val_owner is not None \
                else gs_val.val_owner

            del_manager = account.address
            boxes_del_manager = [
                (0,  AddressType().encode(del_manager)),
            ]

            boxes_val_owner = [
                (0,  AddressType().encode(val_owner)),
            ]

            boxes = boxes_del_manager + boxes_val_owner

            # Get index in validator's list at which the validator ad is stored
            val_user_info = self.app_get_user_info(val_owner)
            val_app_idx = action_inputs.val_app_idx \
                if action_inputs.val_app_idx is not None \
                else (0 if val_user_info is None else val_user_info.get_app_idx(val_app_id))
            # Get index in delegator's list at which the delegator contract is stored
            del_user_info = self.app_get_user_info(del_manager)
            del_app_idx = action_inputs.del_app_idx \
                if action_inputs.del_app_idx is not None \
                else (0 if del_user_info is None else del_user_info.get_app_idx(app_id))

            # Add asset to the foreign asset array and box array
            asset = action_inputs.asset \
                if action_inputs.asset is not None \
                else gs_del.delegation_terms_general.fee_asset_id
            if asset != ALGO_ASA_ID:
                foreign_assets = [asset]
                boxes_asset = [(val_app_id, BOX_ASA_KEY_PREFIX + asset.to_bytes(8, byteorder="big"))]

                boxes += boxes_asset
            else:
                foreign_assets = None

            partner_address = gs_del.delegation_terms_general.partner_address
            foreign_accounts = [del_manager, partner_address]

            # Increase fee for forwarding the call to validator ad (1) and then delegator contract (1),
            # as well as for (potential) distribution of earnings (2).
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 6 * sp.min_fee
            sp.flat_fee = True

            res = self.noticeboard_client.contract_withdraw(
                del_app=app_id,
                del_app_idx=del_app_idx,
                val_owner=val_owner,
                val_app=val_app_id,
                val_app_idx=val_app_idx,
                transaction_parameters = TransactionParameters(
                    sender = account.address,
                    signer = account.signer,
                    suggested_params=sp,
                    foreign_assets=foreign_assets,
                    accounts=foreign_accounts,
                    boxes=boxes,
                ),
            )

        elif action_name == "contract_delete":

            gs_del = self.get_delegator_global_state(app_id)
            gs_val = self.get_validator_ad_global_state(val_app_id)

            # Add asset to the foreign asset array
            asset = action_inputs.asset \
                if action_inputs.asset is not None \
                else gs_del.delegation_terms_general.fee_asset_id
            if asset != ALGO_ASA_ID:
                foreign_assets = [asset]
            else:
                foreign_assets = None

            val_owner = action_inputs.val_owner \
                if action_inputs.val_owner is not None \
                else gs_val.val_owner

            del_manager = account.address
            boxes_del_manager = [
                (0,  AddressType().encode(del_manager)),
            ]

            boxes_val_owner = [
                (0,  AddressType().encode(val_owner)),
            ]

            boxes = boxes_del_manager + boxes_val_owner

            # Get index in validator's list at which the validator ad is stored
            val_user_info = self.app_get_user_info(val_owner)
            val_app_idx = action_inputs.val_app_idx \
                if action_inputs.val_app_idx is not None \
                else (0 if val_user_info is None else val_user_info.get_app_idx(val_app_id))
            # Get index in delegator's list at which the delegator contract is stored
            del_user_info = self.app_get_user_info(del_manager)
            del_app_idx = action_inputs.del_app_idx \
                if action_inputs.del_app_idx is not None \
                else (0 if del_user_info is None else del_user_info.get_app_idx(app_id))

            foreign_accounts = [del_manager]

            # Increase fee for forwarding the call to validator ad (1) and then to
            # delegator contract (1), as well as for (potential) return of remaining balance (2),
            # and the return of MBR (1).
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 6 * sp.min_fee
            sp.flat_fee = True

            res = self.noticeboard_client.contract_delete(
                del_app=app_id,
                del_app_idx=del_app_idx,
                val_owner=val_owner,
                val_app=val_app_id,
                val_app_idx=val_app_idx,
                transaction_parameters = TransactionParameters(
                    sender = account.address,
                    signer = account.signer,
                    suggested_params=sp,
                    foreign_assets=foreign_assets,
                    accounts=foreign_accounts,
                    boxes=boxes,
                ),
            )

        elif action_name == "contract_report_expiry_soon":

            gs_del = self.get_delegator_global_state(app_id)
            gs_val = self.get_validator_ad_global_state(val_app_id)

            if action_inputs.wait_expiry_report is True:
                # Wait until it can be reported that contract will expire soon
                gs = self.get_global_state()
                status = self.algorand_client.client.algod.status()
                current_round = status["last-round"]
                last_report = gs_del.round_expiry_soon_last
                if last_report == 0:
                    num_rounds = gs_del.round_end - current_round - gs.noticeboard_terms_timing.before_expiry
                else:
                    num_rounds = gs.noticeboard_terms_timing.report_period - (current_round - last_report)
                wait_for_rounds(
                    algorand_client=self.algorand_client,
                    num_rounds=num_rounds,
                    acc=self.dispenser,
                )

            val_owner = action_inputs.val_owner \
                if action_inputs.val_owner is not None \
                else gs_val.val_owner

            del_manager = account.address
            boxes_del_manager = [
                (0,  AddressType().encode(del_manager)),
            ]

            boxes_val_owner = [
                (0,  AddressType().encode(val_owner)),
            ]

            boxes = boxes_del_manager + boxes_val_owner

            # Get index in validator's list at which the validator ad is stored
            val_user_info = self.app_get_user_info(val_owner)
            val_app_idx = action_inputs.val_app_idx \
                if action_inputs.val_app_idx is not None \
                else (0 if val_user_info is None else val_user_info.get_app_idx(val_app_id))
            # Get index in delegator's list at which the delegator contract is stored
            del_user_info = self.app_get_user_info(del_manager)
            del_app_idx = action_inputs.del_app_idx \
                if action_inputs.del_app_idx is not None \
                else (0 if del_user_info is None else del_user_info.get_app_idx(app_id))

            foreign_accounts = [del_manager]

            # Increase fee for forwarding the call to validator ad (1), and delegator contract (1),
            # as well as for (potential) notification message (1), and the app call (1).
            sp = self.algorand_client.client.algod.suggested_params()
            sp.fee = 4 * sp.min_fee
            sp.flat_fee = True

            res = self.noticeboard_client.contract_report_expiry_soon(
                del_manager=del_manager,
                del_app=app_id,
                del_app_idx=del_app_idx,
                val_owner=val_owner,
                val_app=val_app_id,
                val_app_idx=val_app_idx,
                transaction_parameters = TransactionParameters(
                    sender = account.address,
                    signer = account.signer,
                    suggested_params=sp,
                    accounts=foreign_accounts,
                    boxes=boxes,
                ),
            )

        else:
            raise ValueError(f"Invalid action name {action_name}")

        return res

    def get_delegator_global_state(self, app_id: int) -> dc.DelegatorContractGlobalState | None:
        if app_id == 0:
            res = None
        else:
            try:
                delegator_contract = dc.DelegatorContract(
                    delegator_contract_client=dc.DelegatorContractClient(
                        algod_client=self.algorand_client.client.algod,
                        app_id=app_id,
                    ),
                    algorand_client=self.algorand_client,
                    acc = self.account_active, # Can be any account
                    del_beneficiary = self.account_active, # Can be any account
                    del_manager = self.account_active, # Can be any account
                )
                res = delegator_contract.get_global_state()
            except Exception as e:  # noqa: F841
                res = None
        return res

    def get_delegator_state(self, app_id: int) -> dc.POSSIBLE_STATES:
        gs = self.get_delegator_global_state(app_id)
        if gs is None:
            state = "START"

        else:
            state_enc = gs.state

            if state_enc == dc.STATE_ENDED_CANNOT_PAY:
                state = "ENDED_CANNOT_PAY"
            elif state_enc == dc.STATE_ENDED_EXPIRED:
                state = "ENDED_EXPIRED"
            elif state_enc == dc.STATE_ENDED_LIMITS:
                state = "ENDED_LIMITS"
            elif state_enc == dc.STATE_ENDED_NOT_CONFIRMED:
                state = "ENDED_NOT_CONFIRMED"
            elif state_enc == dc.STATE_ENDED_NOT_SUBMITTED:
                state = "ENDED_NOT_SUBMITTED"
            elif state_enc == dc.STATE_ENDED_SUSPENDED:
                state = "ENDED_SUSPENDED"
            elif state_enc == dc.STATE_ENDED_WITHDREW:
                state = "ENDED_WITHDREW"
            elif state_enc == dc.STATE_LIVE:
                state = "LIVE"
            elif state_enc == dc.STATE_READY:
                state = "READY"
            elif state_enc == dc.STATE_SUBMITTED:
                state = "SUBMITTED"
            else:
                raise ValueError(f"Unknown state: {state_enc}")

        return state

    def initialize_delegator_contract_state(
        self,
        action_inputs : ActionInputs,
        val_app_id : int,
        del_app_id : int = 0,
        target_state : dc.POSSIBLE_STATES | dc.EXTENDED_POSSIBLE_STATES_WITH_VIA = "READY",
        current_state : dc.POSSIBLE_STATES | None = None,
        action_account: AddressAndSigner | None = None,
        create_new_delegator: bool = False,  # noqa: FBT001, FBT002
    ) -> int:
        """
        Moves a DelegatorContract that is part of ValidatorAd which are both part of the Noticeboard
        from its current state to the target_state, while applying action_inputs to the actions that
        lead to that state.

        By default, the actions to get to the state are executed by the self.del_managers[0],
        unless the create_new_delegator is set and a new app (del_app_id==0) is created.
        In this case, the newly created validator is added as the last element to self.val_owners[-1].
        """

        if del_app_id == 0:

            # To skip any test that are meant to fail later
            action_inputs_passed = copy.deepcopy(action_inputs)
            action_inputs_passed.receiver = None
            action_inputs_passed.amount = None
            action_inputs_passed.user_role = ROLE_DEL

            # If account is not given
            if action_account is None:
                # Create a new delegator (manager) if requested
                if create_new_delegator:
                    action_account_passed = create_and_fund_account(
                        self.algorand_client,
                        self.dispenser,
                        self.assets,
                        algo_amount=TestConsts.acc_dispenser_amt,
                        asa_amount=TestConsts.acc_dispenser_asa_amt,
                    )
                    self.del_managers.append(action_account_passed)
                else:
                    # Use the first del_manager account
                    action_account_passed = self.del_managers[0]

                # Ensure the delegator account is registered as delegator on the Noticeboard
                user_info = self.app_get_user_info(action_account_passed.address)
                if user_info is None:
                    self.noticeboard_action("user_create", action_inputs_passed, action_account_passed)

            else:
                # Use the given account to create a new contract
                action_account_passed = action_account

            # Create a new delegator contract (with default settings)
            res_tmp: AtomicTransactionResponse = self.delegator_action(
                app_id=0,
                action_name="contract_create",
                action_inputs=action_inputs_passed,
                val_app=val_app_id,
                action_account=action_account_passed,
            )
            app_id_passed = res_tmp.abi_results[1].return_value
        else:
            app_id_passed = del_app_id

        if current_state is None:
            _current_state = self.get_delegator_state(app_id_passed)
        else:
            _current_state = current_state

        if target_state == "START":
            return

        # Transition to the target state step by step
        path_to_state = self.get_delegator_path_to_state(
            target_state=target_state,
            current_state=_current_state,
        )

        for action_name in path_to_state:
            action_inputs_passed = action_inputs
            action_name_passed = action_name
            _action_account_passed = action_account_passed
            if action_name == "keys_submit":
                _action_account_passed = None  # To use correct default
            self.delegator_action(app_id_passed, action_name_passed, action_inputs_passed, val_app_id, _action_account_passed)  # noqa: E501

        return app_id_passed

    def get_delegator_path_to_state(
        self,
        target_state : dc.POSSIBLE_STATES | dc.EXTENDED_POSSIBLE_STATES_WITH_VIA,
        current_state : dc.POSSIBLE_STATES | None = None,
    ) -> list[str]:
        """
        Returns a list of actions that transition DelegatorContract from the start to the target state.
        """
        to_start = []
        to_ready = [*to_start, "contract_create"]
        to_submitted = [*to_ready, "keys_submit"]
        to_live = [*to_submitted, "keys_confirm"]
        to_ended_not_submitted = [*to_ready, "keys_not_submitted"]
        to_ended_not_confirmed = [*to_submitted, "keys_not_confirmed"]
        to_ended_limits = [*to_live, "breach_limits"]
        to_ended_withdrew = [*to_live, "contract_withdraw"]
        to_ended_expired = [*to_live, "contract_expired"]
        to_ended_suspended = [*to_live, "breach_suspended"]
        to_ended_cannot_pay_via_ready = [*to_ready, "breach_pay"]
        to_ended_cannot_pay_via_live = [*to_live, "breach_pay"]

        state_transitions = {
            "START": to_start,
            "READY": to_ready,
            "SUBMITTED": to_submitted,
            "LIVE": to_live,
            "ENDED_NOT_SUBMITTED": to_ended_not_submitted,
            "ENDED_NOT_CONFIRMED": to_ended_not_confirmed,
            "ENDED_LIMITS": to_ended_limits,
            "ENDED_WITHDREW": to_ended_withdrew,
            "ENDED_EXPIRED": to_ended_expired,
            "ENDED_SUSPENDED": to_ended_suspended,
            "ENDED_CANNOT_PAY_VIA_READY": to_ended_cannot_pay_via_ready,
            "ENDED_CANNOT_PAY_VIA_LIVE": to_ended_cannot_pay_via_live,
            "DELETED_VIA_ENDED_EXPIRED": [*to_ended_expired, "contract_delete"],
            "DELETED_VIA_ENDED_LIMITS": [*to_ended_limits, "contract_delete"],
            "DELETED_VIA_ENDED_NOT_CONFIRMED": [*to_ended_not_confirmed, "contract_delete"],
            "DELETED_VIA_ENDED_NOT_SUBMITTED": [*to_ended_not_submitted, "contract_delete"],
            "DELETED_VIA_ENDED_SUSPENDED": [*to_ended_suspended, "contract_delete"],
            "DELETED_VIA_ENDED_WITHDREW": [*to_ended_withdrew, "contract_delete"],
            "DELETED_VIA_ENDED_CANNOT_PAY_VIA_READY": [*to_ended_cannot_pay_via_ready, "contract_delete"],
            "DELETED_VIA_ENDED_CANNOT_PAY_VIA_LIVE": [*to_ended_cannot_pay_via_live, "contract_delete"],
        }

        if target_state not in state_transitions:
            raise ValueError(f"Unknown target state: {target_state}")

        if current_state is not None:
            path = [item for item in state_transitions[target_state] if item not in state_transitions[current_state]]
        else:
            path = state_transitions[target_state]

        return path



    # ----- ----- ----- ---------------------- ----- ----- -----
    # ----- ----- -----  General class methods ----- ----- -----
    # ----- ----- ----- ---------------------- ----- ----- -----
    def app_is_opted_in(
        self,
        asset_id: int,
    ) -> bool | None:
        return is_opted_in(
            algorand_client=self.algorand_client,
            address=self.noticeboard_client.app_address,
            asset_id=asset_id,
        )

    def app_balance(
        self,
        asset_id: int,
    ) -> bool | None:
        return balance(
            algorand_client=self.algorand_client,
            address=self.noticeboard_client.app_address,
            asset_id=asset_id,
        )

    def app_available_balance(
        self,
        asset_id: int,
    ) -> int:
        return available_balance(
            algorand_client=self.algorand_client,
            address=self.noticeboard_client.app_address,
            asset_id=asset_id,
        )

    def app_is_online(self) -> bool:
        return is_online(
            algorand_client=self.algorand_client,
            address=self.noticeboard_client.app_address,
        )

    def app_key_params(self) -> KeyRegTxnInfoPlain | None:
        return get_account_key_reg_info(
            algorand_client=self.algorand_client,
            address=self.noticeboard_client.app_address,
        )

    def app_box(
        self,
        box_name: bytes,
    ) -> tuple[bytes, bool]:
        return get_box(
            algorand_client=self.algorand_client,
            box_name=box_name,
            app_id=self.noticeboard_client.app_id,
        )

    def app_asset_box(
        self,
        asset_id: int,
    ) -> tuple[bytes, bool]:
        box_name = BOX_ASSET_KEY_PREFIX + asset_id.to_bytes(8, byteorder="big")
        return self.app_box(box_name=box_name)

    def app_get_asset_info(
        self,
        asset_id: int,
    ) -> NoticeboardAssetInfo | None:
        box_raw = self.app_asset_box(asset_id)
        if box_raw[1]:
            asset_info = decode_noticeboard_asset_box(box_raw[0])
        else:
            asset_info = None
        return asset_info

    def app_user_box(
        self,
        user: str,
    ) -> tuple[bytes, bool]:
        box_name = AddressType().encode(user)
        box_raw = self.app_box(box_name=box_name)
        return box_raw

    def app_get_user_info(
        self,
        user: str,
    ) -> UserInfo | None:
        box_raw = self.app_user_box(user)
        if box_raw[1]:
            user_info = UserInfo.from_bytes(box_raw[0])
        else:
            user_info = None
        return user_info

    def app_partner_box(
        self,
        partner: str,
    ) -> tuple[bytes, bool]:
        box_name = BOX_PARTNERS_PREFIX + AddressType().encode(partner)
        box_raw = self.app_box(box_name=box_name)
        return box_raw

    def app_get_partner_commissions(
        self,
        partner: str,
    ) -> PartnerCommissions | None:
        box_raw = self.app_partner_box(partner)
        if box_raw[1]:
            data_type = TupleType(
                [
                    UintType(64),   # commission_setup
                    UintType(64),   # commission_operational
                ]
            )
            decoded_tuple = data_type.decode(box_raw[0])

            partner_info = PartnerCommissions(
                commission_setup=decoded_tuple[0],
                commission_operational=decoded_tuple[1],
            )
        else:
            partner_info = None
        return partner_info



# ----- ----- ----- ------------------ ----- ----- -----
# ----- ----- -----  General functions ----- ----- -----
# ----- ----- ----- ------------------ ----- ----- -----

def get_template_del_bin() -> bytes | None:
    return get_template_bin(REL_PATH_TO_DELEGATOR_CONTRACT_BIN)

def get_template_val_bin() -> bytes | None:
    return get_template_bin(REL_PATH_TO_VALIDATOR_AD_BIN)

def get_template_bin(
    directory: str,
) -> bytes | None:
    approval_bin_file = next(
        (os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".approval.bin")),
        ""
    )
    template = None
    with open(approval_bin_file, "rb") as f:
        template = f.read()

    return template
