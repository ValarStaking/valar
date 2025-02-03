# pyright: reportMissingModuleSource=false

from algopy import (
    Account,
    Application,
    ARC4Contract,
    Asset,
    BoxMap,
    BoxRef,
    Bytes,
    Global,
    GlobalState,
    TransactionType,
    Txn,
    UInt64,
    arc4,
    compile_contract,
    gtxn,
    itxn,
    op,
    subroutine,
    urange,
)

from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    BOX_ASSET_KEY_PREFIX,
    BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY,
    BOX_PARTNERS_PREFIX,
    BOX_VALIDATOR_AD_TEMPLATE_KEY,
    COMMISSION_MAX,
    DLL_DEL,
    DLL_VAL,
    ERROR_AD_CREATION_INCORRECT_PAY_AMOUNT,
    ERROR_AD_FEE_ROUND_MIN_TOO_SMALL,
    ERROR_AD_FEE_ROUND_VAR_TOO_SMALL,
    ERROR_AD_FEE_SETUP_TOO_SMALL,
    ERROR_AD_MAX_DURATION_TOO_LONG,
    ERROR_AD_MIN_DURATION_TOO_SHORT,
    ERROR_AD_STAKE_MAX_TOO_LARGE,
    ERROR_AD_STAKE_MAX_TOO_SMALL,
    ERROR_AMOUNT_ASA_OPTIN_MBR,
    ERROR_APP_NOT_WITH_USER,
    ERROR_ASSET_NOT_ALLOWED,
    ERROR_CALLED_BY_NOT_PLA_MANAGER,
    ERROR_CALLED_BY_NOT_PLA_MANAGER_OR_ASSET_CONFIG_MANAGER,
    ERROR_CALLED_BY_NOT_PLA_MANAGER_OR_CREATOR,
    ERROR_CALLED_FROM_STATE_RETIRED,
    ERROR_COMMISSION_MAX,
    ERROR_COMMISSION_MIN,
    ERROR_MBR_INCREASE_NOT_PAID,
    ERROR_NO_MEMORY_FOR_MORE_DELEGATORS,
    ERROR_NOT_PAYMENT_OR_XFER,
    ERROR_NOT_STATE_DEPLOYED,
    ERROR_NOT_STATE_SET,
    ERROR_NOT_STATE_SUSPENDED,
    ERROR_PARTNER_CREATION_FEE_NOT_PAID,
    ERROR_PARTNER_NOT_DELETED,
    ERROR_PLATFORM_NOT_OPTED_IN_ASA,
    ERROR_RECEIVER,
    ERROR_TERMS_AND_CONDITIONS_DONT_MATCH,
    ERROR_THERE_CAN_BE_AT_LEAST_ONE_DELEGATOR,
    ERROR_UNEXPECTED_TEMPLATE_NAME,
    ERROR_UNKNOWN_USER_ROLE,
    ERROR_UNSAFE_NUMBER_OF_DELEGATORS,
    ERROR_USER_ALREADY_EXISTS,
    ERROR_USER_APP_CANNOT_REMOVE_FROM_LIST,
    ERROR_USER_APP_LIST_INDEX_TAKEN,
    ERROR_USER_BOX_NOT_DELETED,
    ERROR_USER_HAS_ACTIVE_CONTRACTS,
    ERROR_USER_NOT_DELEGATOR,
    ERROR_USER_NOT_VALIDATOR,
    ERROR_USER_REGISTRATION_FEE_NOT_PAID,
    ERROR_USER_UNEXPECTED_ROLE,
    ERROR_VALIDATOR_AD_DOES_NOT_COMPLY_WITH_TC,
    ERROR_VALIDATOR_AD_DOES_NOT_HAVE_STATE,
    MAXIMUM_NUMBER_OF_DELEGATOR_CONTRACTS_PER_VALIDATOR_AD,
)
from smart_contracts.noticeboard.constants import (
    ROLE_DEL,
    ROLE_VAL,
    STATE_DEPLOYED,
    STATE_NONE,
    STATE_RETIRED,
    STATE_SET,
    STATE_SUSPENDED,
)
from smart_contracts.validator_ad.constants import STATE_CREATED as VALIDATOR_AD_STATE_CREATED
from smart_contracts.validator_ad.contract import ValidatorAd

from ..helpers.common import (
    ContractDeleteReturn,
    DllName,
    EarningsDistribution,
    KeyRegTxnInfo,
    NoticeboardAppList,
    NoticeboardAssetInfo,
    NoticeboardFees,
    NoticeboardTermsNodeLimits,
    NoticeboardTermsTiming,
    PartnerCommissions,
    Sha256,
    UserInfo,
    UserRole,
    UsersDoubleLinkedList,
    ValidatorSelfDisclosure,
    ValidatorTermsGating,
    ValidatorTermsPricing,
    ValidatorTermsStakeLimits,
    ValidatorTermsTiming,
    ValidatorTermsWarnings,
    try_send_note,
)


# ------- Smart contract -------
class Noticeboard(ARC4Contract, avm_version=11):
    """
    Platform for peer-to-peer consensus delegation.
    Validators, i.e. node runners/operators, can post ads to offer their services to users.
    Delegators, i.e. users/ALGO holders, can open requests for the service and conclude a contract with a validator.

    Global state
    ------------

    pla_manager : Account
        Platform manager account.
    asset_config_manager : Account
        Manager account that can configure assets supported by the noticeboard.

    tc_sha256 : Sha256
        Hash (i.e. SHA 256) of the Terms and Conditions.

    noticeboard_fees : NoticeboardFees
        Fees charged by the noticeboard.
    noticeboard_terms_timing : NoticeboardTermsTiming
        Noticeboard limits on timing terms for validator ads.
    noticeboard_terms_node : NoticeboardTermsNodeLimits
        Noticeboard limits on node and related stake limit terms for validator ads.

    state : Bytes
        State of the contract. Can be one of the following:
            DEPLOYED - noticeboard contract has been deployed.
            SET - noticeboard has been set.
            RETIRED - noticeboard has been retired. Operations no new ads or contracts can be opened.

    app_id_old : UInt64
        The app ID of previous version of the platform.
    app_id_new : UInt64
        The app ID of next version of the platform.

    dll_val :  UsersDoubleLinkedList
        Information about the double linked list of validator users.
    dll_del :  UsersDoubleLinkedList
        Information about the double linked list of delegator users.

    Box storage
    -----------
    assets : asset_[asset_id] = NoticeboardAssetInfo
        Box map for storing assets that are or were supported by the noticeboard at any point of time as a means of
        payment between validators and delegators.
        Each entry is a NoticeboardAssetInfo, which is struct with fields:
            - a boolean marking whether the asset is currently accepted as payment (True) or not (False).
            - minimum pricing parameters for this asset.
        Keys correspond to "asset_" followed by byte representation of ASA ID or 0 for ALGO.
        Once an entry is created, it cannot be deleted.

    user : [arc4.Address] = UserInfo
        Box map for storing data about validator owner or delegator manager user.
        Each entry is a UserInfo, with fields for user role, list of app IDs and its counter, as well as
        the previous and next user of the same role in the linked list.
        Keys correspond to user address (32 Byte).

    template_del : BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY = Byte
        Box for storing the delegator contract template.

    template_val : BOX_VALIDATOR_AD_TEMPLATE_KEY = Byte
        Box for storing the validator ad template.

    partner : partner_[arc4.Address] = PartnerCommissions
        Box map for storing commissions of a partner of the platform.
        Each entry is a PartnerCommissions, which includes two UInt64 with the partners commission in ppm
        charged on top of setup and operational fees.
        Keys correspond to "partner_" followed by partners address.

    Methods
    -------
    noticeboard_deploy(
        app_id_old: UInt64,
    ) -> arc4.UInt64:
        Creates a new Noticeboard.

    noticeboard_suspend(
    ) -> None:
        Suspends the platform, temporarily preventing creation of new validator ads and modification of existing ones,
        as well as creation of new delegation contracts and registration of new users.

    noticeboard_migrate(
        app_id_new: UInt64,
    ) -> None:
        Retires the current platform, preventing creation of new validator ads and modification of existing ones,
        as well as creation of new delegation contracts and updating of existing ones.
        Since retired platform cannot create new validator ads or modify existing ones, adding or removing
        an ASA is not needed anymore.

    noticeboard_set(
        pla_manager: Account,
        asset_config_manager: Account,
        tc_sha256 : Sha256,
        noticeboard_fees : NoticeboardFees,
        noticeboard_terms_timing : NoticeboardTermsTiming,
        noticeboard_terms_node : NoticeboardTermsNodeLimits,
    ) -> None:
        Set (anew) all of the platform's operating parameters.

    noticeboard_key_reg(
        key_reg_info : KeyRegTxnInfo,
        txn : gtxn.PaymentTransaction,
    ) -> None:
        Issues a key (de)registration transaction by the platform.

    noticeboard_optin_asa(
        asa : Asset,
        txn : gtxn.PaymentTransaction,
    ) -> None:
        Opts the platform address in to an ASA.

    noticeboard_config_asset(
        asset_id : UInt64,
        asset_info : NoticeboardAssetInfo,
        txn : gtxn.PaymentTransaction,
    ) -> None:
        Adds or modifies an asset from the accepted payment methods.

    noticeboard_income(
        asset_id : UInt64,
    ) -> None:
        Sends all platform earnings of asset to platform manager account.

    template_load_init(
        name: arc4.Byte,
        template_size: UInt64,
    ) -> None:
        Starts the process of uploading a contract template.

    template_load_data(
        name: arc4.Byte,
        offset: UInt64,
        data: Bytes,
    ) -> None:
        Uploads a data chunk to a contract template.

    partner_config(
        partner_address: arc4.Address,
        partner_commissions: UInt64,
        partner_delete: arc4.Bool,
        txn : gtxn.PaymentTransaction,
    ) -> None:
        Creates or modifies a platform's partner.

    gas(
    ) -> None:
        To fit more resources in app reference arrays.

    user_create(
        user_role : UInt64,
        txn : gtxn.PaymentTransaction,
    ) -> None:
        Creates a new user data structure for the sender depending on the requested user role.

    user_delete(
    ) -> None:
        Clears the user's existing role on noticeboard.

    contract_create(
        del_beneficiary: arc4.Address,
        rounds_duration: UInt64,
        stake_max: UInt64,
        val_owner: arc4.Address,
        val_app: Application,
        val_app_idx: UInt64,
        del_app_idx: UInt64,
        tc_sha256: Sha256,
        partner_address: arc4.Address,
        mbr_txn: gtxn.PaymentTransaction,
        txn: gtxn.Transaction,
    ) -> arc4.UInt64:

    keys_confirm(
        del_app: Application,
        del_app_idx : UInt64,
        val_owner: arc4.Address,
        val_app: Application,
        val_app_idx: UInt64,
    ) -> None:
        Delegator manager confirms that the keys have been confirmed by the delegator beneficiary.

    keys_not_confirmed(
        del_manager: arc4.Address,
        del_app: Application,
        del_app_idx : UInt64,
        val_owner: arc4.Address,
        val_app: Application,
        val_app_idx: UInt64,
    ) -> None:
        Anyone confirms that delegator manager has not confirmed the confirmation of
        the keys by the delegator beneficiary and failed to pay the operational fee
        in the agreed time.

    keys_not_submitted(
        del_manager: arc4.Address,
        del_app: Application,
        del_app_idx : UInt64,
        val_owner: arc4.Address,
        val_app: Application,
        val_app_idx: UInt64,
    ) -> None:
        Anyone confirms that validator manager has not submitted the keys in the agreed time.

    keys_submit(
        del_manager: arc4.Address,
        del_app: Application,
        del_app_idx : UInt64,
        val_owner: arc4.Address,
        val_app: Application,
        val_app_idx: UInt64,
        key_reg_txn_info : KeyRegTxnInfo,
    ) -> None:
        Validator manager submits the keys generated for the delegator beneficiary.

    breach_limits(
        del_manager: arc4.Address,
        del_app: Application,
        del_app_idx : UInt64,
        val_owner: arc4.Address,
        val_app: Application,
        val_app_idx: UInt64,
    ) -> None:
        Reports that a limit breach event occurred on a delegator contract of a validator ad.

    breach_pay(
        del_manager: arc4.Address,
        del_app: Application,
        del_app_idx : UInt64,
        val_owner: arc4.Address,
        val_app: Application,
        val_app_idx: UInt64,
    ) -> None:
        Reports that a payment cannot be made because the payment asset on a delegator contract
        have been either frozen or clawed back.

    breach_suspended(
        del_manager: arc4.Address,
        del_app: Application,
        del_app_idx : UInt64,
        val_owner: arc4.Address,
        val_app: Application,
        val_app_idx: UInt64,
    ) -> None:
        Reports that the delegator beneficiary was suspended by consensus.

    contract_claim(
        del_manager: arc4.Address,
        del_app: Application,
        del_app_idx : UInt64,
        val_owner: arc4.Address,
        val_app: Application,
        val_app_idx: UInt64,
    ) -> EarningsDistribution:
        Claims the operational fee up to this round from a delegator contract and
        transfers it to the validator ad as well as the commission to the platform.

    contract_expired(
        del_manager: arc4.Address,
        del_app: Application,
        del_app_idx : UInt64,
        val_owner: arc4.Address,
        val_app: Application,
        val_app_idx: UInt64,
    ) -> None:
        Reports that a delegator contract has expired.

    contract_withdraw(
        del_app: Application,
        del_app_idx : UInt64,
        val_owner: arc4.Address,
        val_app: Application,
        val_app_idx: UInt64,
    ) -> None:
        Delegator manager gracefully withdraws from the delegator contract prematurely.

    contract_delete(
        del_app: Application,
        del_app_idx : UInt64,
    ) -> ContractDeleteReturn:
        Deletes a delegator contract.

    contract_report_expiry_soon(
        del_manager: arc4.Address,
        del_app: Application,
        del_app_idx : UInt64,
    ) -> None:
        Reports that the contract will expire soon.

    ad_create(
        val_app_idx: UInt64,
        txn: gtxn.PaymentTransaction,
    ) -> arc4.UInt64:
        Creates a new validator ad for the sender (i.e. validator owner).

    ad_config(
        val_owner: arc4.Address,
        val_app: Application,
        val_app_idx: UInt64,
        val_manager: arc4.Address,
        live : arc4.Bool,
        cnt_del_max : UInt64,
    ) -> None:
        Sets all operation configuration parameters for the validator ad

    ad_delete(
        val_owner: arc4.Address,
        val_app: Application,
        val_app_idx: UInt64,
    ) -> None:
        Validator owner deletes a validator ad.

    ad_ready(
        val_owner: arc4.Address,
        val_app: Application,
        val_app_idx: UInt64,
        ready: arc4.Bool,
    ) -> None:
        Ad manager sets its readiness for operation.

    ad_self_disclose(
        val_owner: arc4.Address,
        val_app: Application,
        val_app_idx: UInt64,
        val_info: ValidatorSelfDisclosure,
    ) -> None:
        Ad owner sets its self-disclosure information.

    ad_terms(
        val_owner: arc4.Address,
        val_app: Application,
        val_app_idx: UInt64,
        tc_sha256: Sha256,
        terms_time: ValidatorTermsTiming,
        terms_price: ValidatorTermsPricing,
        terms_stake: ValidatorTermsStakeLimits,
        terms_reqs: ValidatorTermsGating,
        terms_warn: ValidatorTermsWarnings,
        mbr_delegator_template_box: UInt64,
        txn: gtxn.PaymentTransaction,
    ) -> None:
        Sets all the terms for creating a delegation contract.

    ad_income(
        val_app: Application,
        val_app_idx: UInt64,
        asset_id: UInt64,
    ) -> arc4.UInt64:
        Validator owner withdraws all available balance from the validator ad for the given asset.

    ad_asa_close(
        val_app: Application,
        val_app_idx: UInt64,
        asset_id: UInt64,
    ) -> None:
        Removes the asset's storage on the validator ad.

    get_noticeboard_asset(
        asset_id : UInt64,
    ) -> NoticeboardAssetInfo:
        Returns information about the payment asset that is or was accepted on the platform.

    get_noticeboard_user(
        user : arc4.Address,
    ) -> UserInfo:
        Returns information about the user on the platform.

    """

    def __init__(self) -> None:
        """
        Define smart contract's global storage and boxes.
        """

        self.pla_manager = Global.zero_address
        self.asset_config_manager = Global.zero_address

        self.tc_sha256 = Sha256.from_bytes(op.bzero(32))

        self.noticeboard_fees = NoticeboardFees.from_bytes(op.bzero(40))
        self.noticeboard_terms_timing = NoticeboardTermsTiming.from_bytes(op.bzero(32))
        self.noticeboard_terms_node = NoticeboardTermsNodeLimits.from_bytes(op.bzero(24))

        self.state = Bytes(STATE_NONE)

        self.app_id_old = UInt64(0)
        self.app_id_new = UInt64(0)

        self.dll_val = GlobalState(
            UsersDoubleLinkedList.from_bytes(op.bzero(72)),
            key=DLL_VAL
        )
        self.dll_del = GlobalState(
            UsersDoubleLinkedList.from_bytes(op.bzero(72)),
            key=DLL_DEL
        )

        self.users = BoxMap(arc4.Address, UserInfo, key_prefix="")

        self.assets = BoxMap(UInt64, NoticeboardAssetInfo, key_prefix=BOX_ASSET_KEY_PREFIX)

        self.template_del = BoxRef(key=BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY)
        self.template_val = BoxRef(key=BOX_VALIDATOR_AD_TEMPLATE_KEY)

        self.partners = BoxMap(arc4.Address, PartnerCommissions, key_prefix=BOX_PARTNERS_PREFIX)

    @arc4.abimethod(create="require")
    def noticeboard_deploy(
        self,
        app_id_old: UInt64,
    ) -> arc4.UInt64:
        """
        Creates a new Noticeboard.

        Parameters
        ----------
        app_id_old : UInt64
            The app ID of previous version of the platform.

        Returns
        -------
        noticeboard_app_id : Application
            App ID of the created noticeboard application.
        """

        # Set global variables
        self.app_id_old = app_id_old

        self.pla_manager = Global.creator_address
        self.asset_config_manager = Global.creator_address

        # Change state to DEPLOYED
        self.state = Bytes(STATE_DEPLOYED)

        return arc4.UInt64(Global.current_application_id.id)

    @arc4.abimethod()
    def noticeboard_suspend(
        self,
    ) -> None:
        """
        Suspends the platform, temporarily preventing creation of new validator ads and modification of existing ones,
        as well as creation of new delegation contracts and registration of new users.
        """

        assert self.state == Bytes(STATE_SET), ERROR_NOT_STATE_SET
        assert (
            Txn.sender == self.pla_manager or
            Txn.sender == Global.creator_address
        ), ERROR_CALLED_BY_NOT_PLA_MANAGER_OR_CREATOR

        # Change state to SUSPENDED
        self.state = Bytes(STATE_SUSPENDED)

        return

    @arc4.abimethod()
    def noticeboard_migrate(
        self,
        app_id_new: UInt64,
    ) -> None:
        """
        Retires the current platform, permanently preventing creation of new validator ads and modification of existing
        ones, as well as creation of new delegation contracts and registration of new users.
        Since retired platform cannot create new validator ads or modify existing ones, configuring payment assets
        and partners is not needed anymore.

        Parameters
        ----------
        app_id_new : UInt64
            The app ID of next version of the platform.
        """

        assert self.state == Bytes(STATE_SUSPENDED), ERROR_NOT_STATE_SUSPENDED
        assert (
            Txn.sender == self.pla_manager or
            Txn.sender == Global.creator_address
        ), ERROR_CALLED_BY_NOT_PLA_MANAGER_OR_CREATOR

        self.app_id_new = app_id_new

        # Change state to RETIRED
        self.state = Bytes(STATE_RETIRED)

        return

    @arc4.abimethod()
    def noticeboard_set(
        self,
        pla_manager: Account,
        asset_config_manager: Account,
        tc_sha256 : Sha256,
        noticeboard_fees : NoticeboardFees,
        noticeboard_terms_timing : NoticeboardTermsTiming,
        noticeboard_terms_node : NoticeboardTermsNodeLimits,
    ) -> None:
        """
        Set (anew) all of the platform's operating parameters.

        Parameters
        ----------
        pla_manager : Account
            Platform manager account.
        asset_config_manager : Account
            Manager account that can configure assets supported by the noticeboard.
        tc_sha256 : Sha256
            Hash (i.e. SHA 256) of the Terms and Conditions.
        noticeboard_fees : NoticeboardFees
            Fees charged by the noticeboard.
        noticeboard_terms_timing : NoticeboardTermsTiming
            Noticeboard limits on timing terms for validator ads.
        noticeboard_terms_node : NoticeboardTermsNodeLimits
            Noticeboard limits on node and related stake limit terms for validator ads.
        """

        assert self.state != Bytes(STATE_RETIRED), ERROR_CALLED_FROM_STATE_RETIRED
        assert (
            Txn.sender == self.pla_manager or
            Txn.sender == Global.creator_address
        ), ERROR_CALLED_BY_NOT_PLA_MANAGER_OR_CREATOR

        self.pla_manager = pla_manager
        self.asset_config_manager = asset_config_manager
        self.tc_sha256 = tc_sha256.copy()

        # Sanity check on commission to prevent calculation errors
        assert noticeboard_fees.commission_min <= COMMISSION_MAX, ERROR_COMMISSION_MAX

        self.noticeboard_fees = noticeboard_fees.copy()
        self.noticeboard_terms_timing = noticeboard_terms_timing.copy()
        # Check the maximum number of allowed delegators is below memory limit
        assert noticeboard_terms_node.cnt_del_max_max <= UInt64(MAXIMUM_NUMBER_OF_DELEGATOR_CONTRACTS_PER_VALIDATOR_AD), ERROR_NO_MEMORY_FOR_MORE_DELEGATORS  # noqa: E501
        # Check the maximum number of allowed delegators is at least one
        assert noticeboard_terms_node.cnt_del_max_max >= UInt64(1), ERROR_THERE_CAN_BE_AT_LEAST_ONE_DELEGATOR
        self.noticeboard_terms_node = noticeboard_terms_node.copy()

        # Change state to SET
        self.state = Bytes(STATE_SET)

        return

    @arc4.abimethod()
    def noticeboard_key_reg(
        self,
        key_reg_info : KeyRegTxnInfo,
        txn : gtxn.PaymentTransaction,
    ) -> None:
        """
        Issues a key (de)registration transaction by the platform.

        Parameters
        ----------
        key_reg_info : KeyRegTxnInfo
            Key registration information to send.
        txn : gtxn.PaymentTransaction
            Payment transaction to cover costs for the key (de)registration fee.
        """

        assert Txn.sender == self.pla_manager, ERROR_CALLED_BY_NOT_PLA_MANAGER

        # Check if payment for covering the fee was made to this contract
        assert txn.receiver == Global.current_application_address, ERROR_RECEIVER
        key_reg_txn_fee = txn.amount

        # Issue the key registration transaction
        itxn.KeyRegistration(
            vote_key = key_reg_info.vote_pk.bytes,
            selection_key = key_reg_info.selection_pk.bytes,
            vote_first = key_reg_info.vote_first.native,
            vote_last = key_reg_info.vote_last.native,
            vote_key_dilution = key_reg_info.vote_key_dilution.native,
            state_proof_key = key_reg_info.state_proof_pk.bytes,
            fee = key_reg_txn_fee,
        ).submit()

        return

    @arc4.abimethod()
    def noticeboard_optin_asa(
        self,
        asa : Asset,
        txn : gtxn.PaymentTransaction,
    ) -> None:
        """
        Opts the platform address in to an ASA.

        Parameters
        ----------
        asa : Asset
            Asset to opt into.
        txn : gtxn.PaymentTransaction
            Payment transaction to cover MBR increase.
        """

        assert (
            Txn.sender == self.pla_manager or
            Txn.sender == self.asset_config_manager
        ), ERROR_CALLED_BY_NOT_PLA_MANAGER_OR_ASSET_CONFIG_MANAGER

        # Check if payment for covering the MBR increase was made to this contract
        assert txn.receiver == Global.current_application_address, ERROR_RECEIVER
        assert txn.amount == Global.asset_opt_in_min_balance, ERROR_AMOUNT_ASA_OPTIN_MBR

        # Opt in to the asset
        itxn.AssetTransfer(
            xfer_asset=asa,
            asset_receiver=Global.current_application_address,
            asset_amount=0,
        ).submit()

        return

    @arc4.abimethod()
    def noticeboard_config_asset(
        self,
        asset_id : UInt64,
        asset_info : NoticeboardAssetInfo,
        txn : gtxn.PaymentTransaction,
    ) -> None:
        """
        Adds or modifies an asset from the accepted payment methods.

        Parameters
        ----------
        asset_id : UInt64
            ID of asset to add or modify as an accepted payment method, i.e. ASA ID or 0 for ALGO.
        asset_info : NoticeboardAssetInfo
            Information about the payment asset, i.e. if it is accepted as a payment at the platform (True) or not
            (False), and its minimum pricing limits.
        txn : gtxn.PaymentTransaction
            Payment transaction to cover (potential) MBR increase.
        """

        assert (
            Txn.sender == self.pla_manager or
            Txn.sender == self.asset_config_manager
        ), ERROR_CALLED_BY_NOT_PLA_MANAGER_OR_ASSET_CONFIG_MANAGER
        assert self.state != Bytes(STATE_RETIRED), ERROR_CALLED_FROM_STATE_RETIRED

        mbr_cur = Global.current_application_address.min_balance

        if asset_id != ALGO_ASA_ID:
            asset = Asset(asset_id)
            assert Global.current_application_address.is_opted_in(asset), ERROR_PLATFORM_NOT_OPTED_IN_ASA

        self.assets[asset_id] = asset_info.copy()

        mbr_new = Global.current_application_address.min_balance

        # Check if payment for covering the potential MBR was made to this contract
        assert txn.receiver == Global.current_application_address, ERROR_RECEIVER
        mbr_pay_amount = mbr_new - mbr_cur
        assert txn.amount == mbr_pay_amount, ERROR_MBR_INCREASE_NOT_PAID

        return

    @arc4.abimethod()
    def noticeboard_income(
        self,
        asset_id : UInt64,
    ) -> None:
        """
        Sends all platform earnings of asset to platform manager account.

        Parameters
        ----------
        asset_id : UInt64
            ID of asset to withdraw all earnings.
        """

        assert Txn.sender == self.pla_manager, ERROR_CALLED_BY_NOT_PLA_MANAGER

        if asset_id != ALGO_ASA_ID:
            asset = Asset(asset_id)
            bal = asset.balance(Global.current_application_address)
            itxn.AssetTransfer(
                xfer_asset=asset,
                asset_receiver=self.pla_manager,
                asset_amount=bal,
            ).submit()
        else:
            bal = Global.current_application_address.balance - Global.current_application_address.min_balance
            itxn.Payment(
                receiver=self.pla_manager,
                amount=bal,
            ).submit()

        return

    @arc4.abimethod()
    def template_load_init(
        self,
        name: arc4.Byte,
        template_size: UInt64,
    ) -> None:
        """
        Starts the process of uploading a contract template.

        Parameters
        ----------
        name : arc4.Byte
            Name of the box with the contract template.
        template_size : UInt64
            Size of the delegator contract template in bytes.
        """

        assert Txn.sender == self.pla_manager, ERROR_CALLED_BY_NOT_PLA_MANAGER

        assert self.state == Bytes(STATE_DEPLOYED), ERROR_NOT_STATE_DEPLOYED

        if name.bytes == BOX_VALIDATOR_AD_TEMPLATE_KEY:
            assert self.template_val.create(size=template_size)
        elif name.bytes == BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY:
            assert self.template_del.create(size=template_size)
        else:
            assert False, ERROR_UNEXPECTED_TEMPLATE_NAME  # noqa: B011

        return

    @arc4.abimethod()
    def template_load_data(
        self,
        name: arc4.Byte,
        offset: UInt64,
        data: Bytes,
    ) -> None:
        """
        Uploads a data chunk to a contract template.

        Parameters
        ----------
        name : arc4.Byte
            Name of the box with the contract template.
        offset : UInt64
            Offset in the box at which to replace the data.
        data : Bytes
            Data to replace in the box at the defined position.
        """

        assert Txn.sender == self.pla_manager, ERROR_CALLED_BY_NOT_PLA_MANAGER

        assert self.state == Bytes(STATE_DEPLOYED), ERROR_NOT_STATE_DEPLOYED

        if name.bytes == BOX_VALIDATOR_AD_TEMPLATE_KEY:
            self.template_val.replace(offset, data)
        elif name.bytes == BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY:
            self.template_del.replace(offset, data)
        else:
            assert False, ERROR_UNEXPECTED_TEMPLATE_NAME  # noqa: B011

        return

    @arc4.abimethod()
    def partner_config(
        self,
        partner_address: arc4.Address,
        partner_commissions: PartnerCommissions,
        partner_delete: arc4.Bool,
        txn : gtxn.PaymentTransaction,
    ) -> None:
        """
        Creates or modifies a platform's partner.

        Parameters
        ----------
        partner_address : arc4.Address
            Address of the partner to register on the platform.
        partner_commissions : PartnerCommissions
            Information about platform's partner commissions.
        partner_delete : arc4.Bool
            Boolean set to true to delete the partner from the platform, otherwise create or modify it.
        txn : gtxn.PaymentTransaction
            Payment transaction to cover (potential) MBR increase.
        """

        assert Txn.sender == self.pla_manager, ERROR_CALLED_BY_NOT_PLA_MANAGER

        assert self.state != Bytes(STATE_RETIRED), ERROR_CALLED_FROM_STATE_RETIRED

        if not partner_delete.native:
            mbr_cur = Global.current_application_address.min_balance

            # Create or modify a partner
            self.partners[partner_address] = partner_commissions.copy()

            mbr_new = Global.current_application_address.min_balance

            # Check if payment for covering the (potential) MBR increase was made to this contract
            assert txn.receiver == Global.current_application_address, ERROR_RECEIVER
            mbr_pay_amount = (mbr_new - mbr_cur)
            assert txn.amount == mbr_pay_amount, ERROR_PARTNER_CREATION_FEE_NOT_PAID
        else:
            assert op.Box.delete(Bytes(BOX_PARTNERS_PREFIX) + partner_address.bytes), ERROR_PARTNER_NOT_DELETED

        return

    @arc4.abimethod()
    def gas(
        self,
    ) -> None:
        """
        To fit more resources in app reference arrays.
        """
        return

    # # ----- ----- ----- ----------------------------- ----- ----- -----
    # # ----- ----- -----        User Management       ----- ----- -----
    # # ----- ----- ----- ----------------------------- ----- ----- -----


    @arc4.abimethod()
    def user_create(
        self,
        user_role : UserRole,
        txn : gtxn.PaymentTransaction,
    ) -> None:
        """
        Creates a new user data structure for the sender depending on the requested user role.

        Parameters
        ----------
        user_role : UserRole
            Role to requested by the user.
            Possible options:
                ROLE_VAL - user is a validator.
                ROLE_DEL - user is a delegator.
        txn : gtxn.PaymentTransaction
            Payment transaction to cover MBR increase and user creation fee.
        """

        assert self.state == Bytes(STATE_SET), ERROR_NOT_STATE_SET

        mbr_cur = Global.current_application_address.min_balance

        # Cannot create a user if it already exists on the platform
        user = arc4.Address(Txn.sender)
        assert user not in self.users, ERROR_USER_ALREADY_EXISTS

        # Define the user
        if user_role.bytes == Bytes(ROLE_VAL):
            user_fee = self.noticeboard_fees.val_user_reg.native
            dll_name = DllName.from_bytes(DLL_VAL)
            dll = GlobalState(UsersDoubleLinkedList, key=dll_name.bytes)
        elif user_role.bytes == Bytes(ROLE_DEL):
            user_fee = self.noticeboard_fees.del_user_reg.native
            dll_name = DllName.from_bytes(DLL_DEL)
            dll = GlobalState(UsersDoubleLinkedList, key=dll_name.bytes)
        else:
            assert False, ERROR_UNKNOWN_USER_ROLE  # noqa: B011

        # Add the user to the appropriate double linked list according to the role
        if dll.value.user_first == arc4.Address(Global.zero_address):
            prev_user = arc4.Address(Global.zero_address)
            next_user = arc4.Address(Global.zero_address)
            dll.value.user_first = user
            dll.value.user_last = user
        else:
            prev_user = dll.value.user_last
            next_user = arc4.Address(Global.zero_address)
            dll.value.user_last = user

            self.users[prev_user].next_user = user

        dll.value.cnt_users = arc4.UInt64(
            dll.value.cnt_users.native + UInt64(1)
        )

        # Create the user
        self.users[user] = UserInfo(
            role=user_role.copy(),
            dll_name=dll_name.copy(),
            prev_user=prev_user,
            next_user=next_user,
            app_ids=NoticeboardAppList.from_bytes(op.bzero(8*110)),
            cnt_app_ids=arc4.UInt64(0),
        )

        mbr_new = Global.current_application_address.min_balance

        # Check if payment for covering the potential MBR was made to this contract
        assert txn.receiver == Global.current_application_address, ERROR_RECEIVER
        mbr_pay_amount = (mbr_new - mbr_cur) + user_fee
        assert txn.amount == mbr_pay_amount, ERROR_USER_REGISTRATION_FEE_NOT_PAID

        return

    @arc4.abimethod()
    def user_delete(
        self,
    ) -> None:
        """
        Clears the user's existing role on noticeboard.
        """

        mbr_cur = Global.current_application_address.min_balance

        user = arc4.Address(Txn.sender)

        prev_user = self.users[user].prev_user
        next_user = self.users[user].next_user

        assert self.users[user].cnt_app_ids.native == UInt64(0), ERROR_USER_HAS_ACTIVE_CONTRACTS

        # Remove the user from the double linked list it belongs to according to its role
        dll = GlobalState(UsersDoubleLinkedList, key=self.users[user].dll_name.bytes)
        if prev_user == arc4.Address(Global.zero_address) and next_user == arc4.Address(Global.zero_address):
            # There is just one account in the list
            dll.value.user_first = arc4.Address(Global.zero_address)
            dll.value.user_last = arc4.Address(Global.zero_address)
        elif prev_user == arc4.Address(Global.zero_address):
            # Deleting the first account in the list
            dll.value.user_first = next_user
            self.users[next_user].prev_user = arc4.Address(Global.zero_address)
        elif next_user == arc4.Address(Global.zero_address):
            # Deleting the last account in the list
            dll.value.user_last = prev_user
            self.users[prev_user].next_user = arc4.Address(Global.zero_address)
        else:
            # Deleting other accounts in the list
            self.users[prev_user].next_user = next_user
            self.users[next_user].prev_user = prev_user
        dll.value.cnt_users = arc4.UInt64(
            dll.value.cnt_users.native - UInt64(1)
        )

        assert op.Box.delete(user.bytes), ERROR_USER_BOX_NOT_DELETED

        mbr_new = Global.current_application_address.min_balance

        # Send the freed MBR to the user
        mbr_freed_amount = mbr_cur - mbr_new
        itxn.Payment(
            receiver=user.native,
            amount=mbr_freed_amount,
        ).submit()

        return

    # # # ----- ----- ----- ----------------------------- ----- ----- -----
    # # # ----- ----- -----    Validator Ad Management    ----- ----- -----
    # # # ----- ----- ----- ----------------------------- ----- ----- -----

    @arc4.abimethod()
    def ad_create(
        self,
        val_app_idx: UInt64,
        txn: gtxn.PaymentTransaction,
    ) -> arc4.UInt64:
        """
        Creates a new validator ad for the sender (i.e. validator owner).

        Parameters
        ----------
        val_app_idx : UInt64
            Index in the validator owner app list at which to place the newly created validator ad.
            This is to save on opcode cost instead of looping through the whole list.
        txn : gtxn.Transaction
            Transaction for the payment of the validator ad creation fee and
            all the MBR increases at Noticeboard and the newly created ValidatorAd.

        Returns
        -------
        val_app_id : UInt64
            App ID of the created validator ad application.
        """

        assert self.state == Bytes(STATE_SET), ERROR_NOT_STATE_SET

        val_owner = arc4.Address(Txn.sender)
        assert self.users[val_owner].role.bytes == Bytes(ROLE_VAL), ERROR_USER_NOT_VALIDATOR

        mbr_cur = Global.current_application_address.min_balance

        # Create a new validator ad
        compiled = compile_contract(ValidatorAd)
        if self.template_val.length > UInt64(4096):
            approval_program = (
                self.template_val.extract(UInt64(0), UInt64(4096)),
                self.template_val.extract(UInt64(4096), self.template_val.length - UInt64(4096)),
            )
        else:
            approval_program = (
                self.template_val.extract(UInt64(0), self.template_val.length),
                Bytes(),
            )

        val_app_id, txn_create = arc4.abi_call(
            ValidatorAd.ad_create,
            val_owner,
            approval_program=approval_program,
            clear_state_program=compiled.clear_state_program,
            global_num_uint=compiled.global_uints,
            global_num_bytes=compiled.global_bytes,
            local_num_uint=compiled.local_uints,
            local_num_bytes=compiled.local_bytes,
            extra_program_pages=compiled.extra_program_pages,
        )
        val_app = Application(val_app_id.native)

        self._store_user_app(val_owner, val_app_id, val_app_idx)

        # Fund the created ad with MBR
        contract_fund_pay = Global.min_balance
        itxn.Payment(
            receiver=val_app.address,
            amount=contract_fund_pay,
        ).submit()

        # Check if ALGO payment is enough to cover validator setup fee and
        # MBR increase on Noticeboard due to ad creation and
        # for MBR funding of the new validator ad.
        assert txn.receiver == Global.current_application_address, ERROR_RECEIVER
        mbr_new = Global.current_application_address.min_balance
        pay_amount = (
            self.noticeboard_fees.val_ad_creation.native +
            (mbr_new - mbr_cur) +
            contract_fund_pay
        )
        assert txn.amount == pay_amount, ERROR_AD_CREATION_INCORRECT_PAY_AMOUNT

        return val_app_id

    @arc4.abimethod()
    def ad_config(
        self,
        val_app: Application,
        val_app_idx: UInt64,
        val_manager: arc4.Address,
        live : arc4.Bool,
        cnt_del_max : UInt64,
    ) -> None:
        """
        Sets all operation configuration parameters for the validator ad, i.e.
        the validator manager account, the status whether the ad is live to accept new delegators (`live=True`)
        or not (`live=False`), and the maximum number of delegators the validator ad can accept.

        Parameters
        ----------
        val_app : Application
            App ID of the validator ad.
        val_app_idx : UInt64
            Index of the requested validator ad in validator owner app list.
            This is to save on opcode cost instead of looping through the whole list.
        val_manager : arc4.Address
            Manager address for the validator ad.
        live : arc4.Bool
            Set to True if the newly created validator ad should be accepting new delegators right away,
            otherwise set to False.
        cnt_del_max : UInt64
            Maximum number of delegators the validator is willing to manage simultaneously.
        """

        val_owner = arc4.Address(Txn.sender)
        self._assert_user_and_app(val_owner, val_app, val_app_idx, Bytes(ROLE_VAL))

        # Check if requested maximum is below the allowed limit for node performance safety
        assert cnt_del_max <= self.noticeboard_terms_node.cnt_del_max_max, ERROR_UNSAFE_NUMBER_OF_DELEGATORS

        # Configure ad
        app_txn = arc4.abi_call(  # noqa: F841
            ValidatorAd.ad_config,
            val_owner,
            val_manager,
            live,
            cnt_del_max,
            app_id=val_app.id,
        )

        return

    @arc4.abimethod()
    def ad_delete(
        self,
        val_app: Application,
        val_app_idx: UInt64,
    ) -> None:
        """
        Validator owner deletes a validator ad.
        Possible only if there are no active delegators and all balances have been claimed.

        Parameters
        ----------
        val_app : Application
            App ID of the validator ad.
        val_app_idx : UInt64
            Index of the requested validator ad in validator owner app list.
            This is to save on opcode cost instead of looping through the whole list.
        """

        val_owner = arc4.Address(Txn.sender)
        self._assert_user_and_app(val_owner, val_app, val_app_idx, Bytes(ROLE_VAL))

        mbr_cur = Global.current_application_address.min_balance

        # Delete ad
        app_txn = arc4.abi_call(  # noqa: F841
            ValidatorAd.ad_delete,
            val_owner,
            app_id=val_app.id,
        )

        self._remove_user_app(val_owner, arc4.UInt64(val_app.id), val_app_idx)

        mbr_new = Global.current_application_address.min_balance

        itxn.Payment(
            receiver=val_owner.native,
            amount=mbr_cur-mbr_new,
        ).submit()

        return

    @arc4.abimethod()
    def ad_ready(
        self,
        val_owner: arc4.Address,
        val_app: Application,
        val_app_idx: UInt64,
        ready: arc4.Bool,
    ) -> None:
        """
        Ad manager sets its readiness for operation.

        Parameters
        ----------
        val_owner : arc4.Address
            Owner address for the validator ad.
        val_app : Application
            App ID of the validator ad.
        val_app_idx : UInt64
            Index of the requested validator ad in validator owner app list.
            This is to save on opcode cost instead of looping through the whole list.
        ready : arc4.Bool
            Set to True if validator manager is ready for accepting new delegators, otherwise set to False.
        """

        self._assert_user_and_app(val_owner, val_app, val_app_idx, Bytes(ROLE_VAL))

        # Set manager readiness
        val_manager = arc4.Address(Txn.sender)
        app_txn = arc4.abi_call(  # noqa: F841
            ValidatorAd.ad_ready,
            val_manager,
            ready,
            app_id=val_app.id,
        )

        return

    @arc4.abimethod()
    def ad_self_disclose(
        self,
        val_app: Application,
        val_app_idx: UInt64,
        val_info: ValidatorSelfDisclosure,
    ) -> None:
        """
        Ad owner sets its self-disclosure information.

        Parameters
        ----------
        val_app : Application
            App ID of the validator ad.
        val_app_idx : UInt64
            Index of the requested validator ad in validator owner app list.
            This is to save on opcode cost instead of looping through the whole list.
        val_info : ValidatorSelfDisclosure
            Self-disclosed information about the validator.
        """

        assert self.state == Bytes(STATE_SET), ERROR_NOT_STATE_SET

        val_owner = arc4.Address(Txn.sender)
        self._assert_user_and_app(val_owner, val_app, val_app_idx, Bytes(ROLE_VAL))

        # Set self-disclose info
        app_txn = arc4.abi_call(  # noqa: F841
            ValidatorAd.ad_self_disclose,
            val_owner,
            val_info,
            app_id=val_app.id,
        )

        return

    @arc4.abimethod()
    def ad_terms(
        self,
        val_app: Application,
        val_app_idx: UInt64,
        tc_sha256: Sha256,
        terms_time: ValidatorTermsTiming,
        terms_price: ValidatorTermsPricing,
        terms_stake: ValidatorTermsStakeLimits,
        terms_reqs: ValidatorTermsGating,
        terms_warn: ValidatorTermsWarnings,
        mbr_delegator_template_box: UInt64,
        txn: gtxn.PaymentTransaction,
    ) -> None:
        """
        Sets all the terms for creating a delegation contract.
        With this action, the validator agrees with the (new) terms.

        Parameters
        ----------
        val_app : Application
            App ID of the validator ad.
        val_app_idx : UInt64
            Index of the requested validator ad in validator owner app list.
            This is to save on opcode cost instead of looping through the whole list.
        tc_sha256 : Sha256
            Hash (i.e. SHA 256) of the Terms and Conditions agreed by the validator.
        terms_time: ValidatorTermsTiming
            Validator's terms about timing.
        terms_price: ValidatorTermsPricing
            Validator's terms about pricing.
        terms_stake: ValidatorTermsStakeLimits
            Validator's terms about stake limits.
        terms_reqs: ValidatorTermsGating
            Validator's terms about gating requirements.
        terms_warn: ValidatorTermsWarnings
            Validator's terms about warnings.
        mbr_delegator_template_box : UInt64
            Amount needed to pay to the validator ad for creating box for delegator template.
        txn : gtxn.PaymentTransaction
            Transaction for the payment of potential MBR increase of ValidatorAd in case
            of ASA opt-in and payment of box for delegator contract template box in case
            the ValidatorAd is in STATE_CREATED.
        """

        assert self.state == Bytes(STATE_SET), ERROR_NOT_STATE_SET

        val_owner = arc4.Address(Txn.sender)
        self._assert_user_and_app(val_owner, val_app, val_app_idx, Bytes(ROLE_VAL))

        # Check compliance of requested validator ad terms
        assert tc_sha256.bytes == self.tc_sha256.bytes, ERROR_TERMS_AND_CONDITIONS_DONT_MATCH
        self._assert_terms_time(terms_time)
        self._assert_terms_price(terms_price)
        self._assert_terms_stake(terms_stake)

        # If validator ad is in created state, first also load ad template to its box storage
        ad_state = op.AppGlobal.get_ex_bytes(val_app, b"state")
        assert ad_state[1], ERROR_VALIDATOR_AD_DOES_NOT_HAVE_STATE # Error should not be possible
        if ad_state[0] == VALIDATOR_AD_STATE_CREATED:
            # Load delegator contract template
            mbr_template_txn = itxn.Payment(
                receiver=val_app.address,
                amount=mbr_delegator_template_box,
            )
            txn_load_init = arc4.abi_call(  # noqa: F841
                ValidatorAd.template_load_init,
                val_owner,
                self.template_del.length,
                mbr_template_txn,
                app_id=val_app.id,
            )

            chunks = op.shr(self.template_del.length, 10) + UInt64(1)
            for idx in urange(chunks):
                offset = idx * UInt64(1024)
                if idx == chunks - UInt64(1):
                    chunk_size = self.template_del.length - idx * UInt64(1024)
                else:
                    chunk_size = UInt64(1024)
                data = self.template_del.extract(offset, chunk_size)
                template_load_data = arc4.abi_call(  # noqa: F841
                    ValidatorAd.template_load_data,
                    val_owner,
                    offset,
                    data,
                    app_id=val_app.id,
                )

            template_load_end = arc4.abi_call(  # noqa: F841
                ValidatorAd.template_load_end,
                val_owner,
                app_id=val_app.id,
            )

        # Check if payment for increase of MBR of ValidatorAd was made to this contract
        assert txn.receiver == Global.current_application_address, ERROR_RECEIVER
        asa_optin_txn = itxn.Payment(
            receiver=val_app.address,
            amount=txn.amount - mbr_delegator_template_box,
        )
        # Set ad terms
        txn_set = arc4.abi_call(  # noqa: F841
            ValidatorAd.ad_terms,
            val_owner,
            tc_sha256.copy(),
            terms_time.copy(),
            terms_price.copy(),
            terms_stake.copy(),
            terms_reqs.copy(),
            terms_warn.copy(),
            asa_optin_txn,
            app_id=val_app.id,
        )

        return

    @arc4.abimethod()
    def ad_income(
        self,
        val_app: Application,
        val_app_idx: UInt64,
        asset_id: UInt64,
    ) -> arc4.UInt64:
        """
        Validator owner withdraws all available balance from the validator ad for the given asset.

        Parameters
        ----------
        val_app : Application
            App ID of the validator ad.
        val_app_idx : UInt64
            Index of the requested validator ad in validator owner app list.
            This is to save on opcode cost instead of looping through the whole list.
        asset_id : UInt64
            ID of the asset (i.e. ASA ID or 0 for ALGO) for which the owner would like to withdraw all earnings from
            the validator ad.

        Returns
        -------
        income : arc4.UInt64
            Withdrawn income from the validator ad for the input asset.
        """

        val_owner = arc4.Address(Txn.sender)
        self._assert_user_and_app(val_owner, val_app, val_app_idx, Bytes(ROLE_VAL))

        # Withdraw income
        income, app_txn = arc4.abi_call(
            ValidatorAd.ad_income,
            val_owner,
            asset_id,
            app_id=val_app.id,
        )

        return income

    @arc4.abimethod()
    def ad_asa_close(
        self,
        val_app: Application,
        val_app_idx: UInt64,
        asset_id: UInt64,
    ) -> None:
        """
        Removes the asset's storage on the validator ad.

        Parameters
        ----------
        val_app : Application
            App ID of the validator ad.
        val_app_idx : UInt64
            Index of the requested validator ad in validator owner app list.
            This is to save on opcode cost instead of looping through the whole list.
        asset_id : UInt64
            ID of the asset (i.e. ASA ID or 0 for ALGO) for which the owner would like to withdraw all earnings from
            the validator ad.
        """

        val_owner = arc4.Address(Txn.sender)
        self._assert_user_and_app(val_owner, val_app, val_app_idx, Bytes(ROLE_VAL))

        # Remove ASA
        app_txn = arc4.abi_call(  # noqa: F841
            ValidatorAd.ad_asa_close,
            val_owner,
            asset_id,
            app_id=val_app.id,
        )

        return


    # # # ----- ----- ----- ----------------------------- ----- ----- -----
    # # # ----- ----- ----- Delegator Contract Management ----- ----- -----
    # # # ----- ----- ----- ----------------------------- ----- ----- -----

    @arc4.abimethod()
    def contract_create(
        self,
        del_beneficiary: arc4.Address,
        rounds_duration: UInt64,
        stake_max: UInt64,
        val_owner: arc4.Address,
        val_app: Application,
        val_app_idx: UInt64,
        del_app_idx: UInt64,
        tc_sha256: Sha256,
        partner_address: arc4.Address,
        mbr_txn: gtxn.PaymentTransaction,
        txn: gtxn.Transaction,
    ) -> arc4.UInt64:
        """
        Creates a new delegator contract for a delegator beneficiary with the given validator owner under the terms
        defined in the given ad for the input defined contract duration.

        Parameters
        ----------
        del_beneficiary : arc4.Address
            Beneficiary address for the new delegation contract.
        rounds_duration : UInt64
            Contract duration in number of rounds.
        stake_max : UInt64
            The maximum amount of ALGO that the delegator beneficiary address intends to have at any point in time
            during the contract duration.
        val_owner : arc4.Address
            Owner address for the validator ad.
        val_app : Application
            App ID of the validator ad.
        val_app_idx : UInt64
            Index of the requested validator ad in validator owner app list.
            This is to save on opcode cost instead of looping through the whole list.
        del_app_idx : UInt64
            Index of the delegator manager app list at which to store the new delegator contract.
            This is to save on opcode cost instead of looping through the whole list.
        tc_sha256 : Sha256
            Hash (i.e. SHA 256) of the Terms and Conditions agreed by the delegator.
        partner_address : arc4.Address
            Address of the partner that facilitated the contract creation.
            If there is no partner, set to Global.zero_address.
        mbr_txn : gtxn.PaymentTransaction
            Payment transaction for the payment of the increase of validator ad MBR due to creation of a new contract
            and payment of delegator contract creation fee.
        txn : gtxn.Transaction
            Transaction for the payment of the setup and operational fee.

        Returns
        -------
        delegator_app_id : UInt64
            App ID of the created delegator contract application.
        """

        assert self.state == Bytes(STATE_SET), ERROR_NOT_STATE_SET

        del_manager = arc4.Address(Txn.sender)
        assert self.users[del_manager].role.bytes == Bytes(ROLE_DEL), ERROR_USER_NOT_DELEGATOR

        self._assert_user_and_app(val_owner, val_app, val_app_idx, Bytes(ROLE_VAL))

        assert tc_sha256.bytes == self.tc_sha256.bytes, ERROR_TERMS_AND_CONDITIONS_DONT_MATCH

        val_tc = op.AppGlobal.get_ex_bytes(val_app, b"tc_sha256")
        assert val_tc[0] == self.tc_sha256.bytes, ERROR_VALIDATOR_AD_DOES_NOT_COMPLY_WITH_TC

        # Check MBR payment and forward it to the validator ad contract
        assert mbr_txn.receiver == Global.current_application_address, ERROR_RECEIVER
        mbr_txn_forward = itxn.InnerTransaction(
            type=TransactionType.Payment,
            receiver=val_app.address,
            amount=mbr_txn.amount-self.noticeboard_fees.del_contract_creation.native,
        )

        # Check payment and forward it to the validator ad contract
        if txn.type == TransactionType.Payment:
            assert txn.receiver == Global.current_application_address, ERROR_RECEIVER
            txn_forward = itxn.InnerTransaction(
                type=TransactionType.Payment,
                receiver=val_app.address,
                amount=txn.amount,
            )
        elif txn.type == TransactionType.AssetTransfer:
            assert txn.asset_receiver == Global.current_application_address, ERROR_RECEIVER
            txn_forward = itxn.InnerTransaction(
                type=TransactionType.AssetTransfer,
                xfer_asset=txn.xfer_asset,
                asset_receiver=val_app.address,
                asset_amount=txn.asset_amount,
            )
        else:
            assert False, ERROR_NOT_PAYMENT_OR_XFER  # noqa: B011

        # Check if there is commission for the partner
        if partner_address in self.partners:
            partner = partner_address
            partner_commissions = self.partners[partner_address].copy()
        else:
            partner = arc4.Address(Global.zero_address)
            partner_commissions = PartnerCommissions(
                commission_setup = arc4.UInt64(0),
                commission_operational = arc4.UInt64(0),
            )

        # Create delegator contract
        del_app_id, app_txn = arc4.abi_call(
            ValidatorAd.contract_create,
            del_manager,
            del_beneficiary,
            rounds_duration,
            stake_max,
            partner,
            partner_commissions,
            mbr_txn_forward,
            txn_forward,
            app_id=val_app.id,
        )

        self._store_user_app(del_manager, del_app_id, del_app_idx)

        return del_app_id

    @arc4.abimethod()
    def keys_confirm(
        self,
        del_app: Application,
        del_app_idx : UInt64,
        val_owner: arc4.Address,
        val_app: Application,
        val_app_idx: UInt64,
    ) -> None:
        """
        Delegator manager confirms that the keys have been confirmed by the delegator beneficiary.

        Parameters
        ----------
        del_app : Application
            App ID of the delegator contract.
        del_app_idx : UInt64
            Index of the delegator manager app list at which the delegator contract is stored.
            This is to save on opcode cost instead of looping through the whole list.
        val_owner : arc4.Address
            Owner address for the validator ad.
        val_app : Application
            App ID of the validator ad.
        val_app_idx : UInt64
            Index of the requested validator ad in validator owner app list.
            This is to save on opcode cost instead of looping through the whole list.
        """

        del_manager = arc4.Address(Txn.sender)
        self._assert_user_and_app(del_manager, del_app, del_app_idx, Bytes(ROLE_DEL))

        self._assert_user_and_app(val_owner, val_app, val_app_idx, Bytes(ROLE_VAL))

        # Confirms the keys and pays the operational fee to the validator ad
        app_txn = arc4.abi_call(  # noqa: F841
        # arc4.abi_call(
            ValidatorAd.keys_confirm,
            del_manager,
            del_app,
            app_id=val_app.id,
        )

        return

    @arc4.abimethod()
    def keys_not_confirmed(
        self,
        del_manager: arc4.Address,
        del_app: Application,
        del_app_idx : UInt64,
        val_owner: arc4.Address,
        val_app: Application,
        val_app_idx: UInt64,
    ) -> None:
        """
        Anyone confirms that delegator manager has not confirmed the confirmation of
        the keys by the delegator beneficiary and failed to pay the operational fee
        in the agreed time.

        Parameters
        ----------
        del_manager : arc4.Address
            Manager address for the delegation contract.
        del_app : Application
            App ID of the delegator contract.
        del_app_idx : UInt64
            Index of the delegator manager app list at which the delegator contract is stored.
            This is to save on opcode cost instead of looping through the whole list.
        val_owner : arc4.Address
            Owner address for the validator ad.
        val_app : Application
            App ID of the validator ad.
        val_app_idx : UInt64
            Index of the requested validator ad in validator owner app list.
            This is to save on opcode cost instead of looping through the whole list.
        """

        self._assert_user_and_app(del_manager, del_app, del_app_idx, Bytes(ROLE_DEL))

        self._assert_user_and_app(val_owner, val_app, val_app_idx, Bytes(ROLE_VAL))

        # Reports the keys have not been confirmed
        res, app_txn = arc4.abi_call(
            ValidatorAd.keys_not_confirmed,
            del_app,
            app_id=val_app.id,
        )

        try_send_note(res.del_manager.native, res.msg.bytes)

        return

    @arc4.abimethod()
    def keys_not_submitted(
        self,
        del_manager: arc4.Address,
        del_app: Application,
        del_app_idx : UInt64,
        val_owner: arc4.Address,
        val_app: Application,
        val_app_idx: UInt64,
    ) -> None:
        """
        Anyone confirms that validator manager has not submitted the keys in the agreed time.
        Internally, the setup fee is returned to the delegator manager if possible.

        Parameters
        ----------
        del_manager : arc4.Address
            Manager address for the delegation contract.
        del_app : Application
            App ID of the delegator contract.
        del_app_idx : UInt64
            Index of the delegator manager app list at which the delegator contract is stored.
            This is to save on opcode cost instead of looping through the whole list.
        val_owner : arc4.Address
            Owner address for the validator ad.
        val_app : Application
            App ID of the validator ad.
        val_app_idx : UInt64
            Index of the requested validator ad in validator owner app list.
            This is to save on opcode cost instead of looping through the whole list.
        """

        self._assert_user_and_app(del_manager, del_app, del_app_idx, Bytes(ROLE_DEL))

        self._assert_user_and_app(val_owner, val_app, val_app_idx, Bytes(ROLE_VAL))


        # Reports the keys have not been submitted
        res, app_txn = arc4.abi_call(
            ValidatorAd.keys_not_submitted,
            del_app,
            app_id=val_app.id,
        )

        try_send_note(res.del_manager.native, res.msg.bytes)

        return

    @arc4.abimethod()
    def keys_submit(
        self,
        del_manager: arc4.Address,
        del_app: Application,
        del_app_idx : UInt64,
        val_owner: arc4.Address,
        val_app: Application,
        val_app_idx: UInt64,
        key_reg_txn_info : KeyRegTxnInfo,
    ) -> None:
        """
        Validator manager submits the keys generated for the delegator beneficiary.
        Internally, the setup fee is assigned to the validator.

        Parameters
        ----------
        del_manager : arc4.Address
            Manager address for the delegation contract.
        del_app : Application
            App ID of the delegator contract.
        del_app_idx : UInt64
            Index of the delegator manager app list at which the delegator contract is stored.
            This is to save on opcode cost instead of looping through the whole list.
        val_owner : arc4.Address
            Owner address for the validator ad.
        val_app : Application
            App ID of the validator ad.
        val_app_idx : UInt64
            Index of the requested validator ad in validator owner app list.
            This is to save on opcode cost instead of looping through the whole list.
        key_reg_txn_info : KeyRegTxnInfo
            Information about the generated participation keys.
        """

        self._assert_user_and_app(del_manager, del_app, del_app_idx, Bytes(ROLE_DEL))

        self._assert_user_and_app(val_owner, val_app, val_app_idx, Bytes(ROLE_VAL))

        # Submits the keys
        res, app_txn = arc4.abi_call(
            ValidatorAd.keys_submit,
            arc4.Address(Txn.sender),
            del_app,
            key_reg_txn_info.copy(),
            app_id=val_app.id,
        )

        try_send_note(res.del_manager.native, res.msg.bytes)

        return

    @arc4.abimethod()
    def breach_limits(
        self,
        del_manager: arc4.Address,
        del_app: Application,
        del_app_idx : UInt64,
        val_owner: arc4.Address,
        val_app: Application,
        val_app_idx: UInt64,
    ) -> None:
        """
        Reports that a limit breach event occurred on a delegator contract of a validator ad.

        Parameters
        ----------
        del_manager : arc4.Address
            Manager address for the delegation contract.
        del_app : Application
            App ID of the delegator contract.
        del_app_idx : UInt64
            Index of the delegator manager app list at which the delegator contract is stored.
            This is to save on opcode cost instead of looping through the whole list.
        val_owner : arc4.Address
            Owner address for the validator ad.
        val_app : Application
            App ID of the validator ad.
        val_app_idx : UInt64
            Index of the requested validator ad in validator owner app list.
            This is to save on opcode cost instead of looping through the whole list.
        """

        self._assert_user_and_app(del_manager, del_app, del_app_idx, Bytes(ROLE_DEL))

        self._assert_user_and_app(val_owner, val_app, val_app_idx, Bytes(ROLE_VAL))


        # Reports a breach in limits
        res, app_txn = arc4.abi_call(
            ValidatorAd.breach_limits,
            del_app,
            app_id=val_app.id,
        )

        try_send_note(res.del_manager.native, res.msg.bytes)

        return

    @arc4.abimethod()
    def breach_pay(
        self,
        del_manager: arc4.Address,
        del_app: Application,
        del_app_idx : UInt64,
        val_owner: arc4.Address,
        val_app: Application,
        val_app_idx: UInt64,
    ) -> None:
        """
        Reports that a payment cannot be made because the payment asset on a delegator contract
        have been either frozen or clawed back.

        Parameters
        ----------
        del_manager : arc4.Address
            Manager address for the delegation contract.
        del_app : Application
            App ID of the delegator contract.
        del_app_idx : UInt64
            Index of the delegator manager app list at which the delegator contract is stored.
            This is to save on opcode cost instead of looping through the whole list.
        val_owner : arc4.Address
            Owner address for the validator ad.
        val_app : Application
            App ID of the validator ad.
        val_app_idx : UInt64
            Index of the requested validator ad in validator owner app list.
            This is to save on opcode cost instead of looping through the whole list.
        """

        self._assert_user_and_app(del_manager, del_app, del_app_idx, Bytes(ROLE_DEL))

        self._assert_user_and_app(val_owner, val_app, val_app_idx, Bytes(ROLE_VAL))

        # Reports a breach in payment method
        res, app_txn = arc4.abi_call(
            ValidatorAd.breach_pay,
            del_app,
            app_id=val_app.id,
        )

        try_send_note(res.del_manager.native, res.msg.bytes)

        return

    @arc4.abimethod()
    def breach_suspended(
        self,
        del_manager: arc4.Address,
        del_app: Application,
        del_app_idx : UInt64,
        val_owner: arc4.Address,
        val_app: Application,
        val_app_idx: UInt64,
    ) -> None:
        """
        Reports that the delegator beneficiary was suspended by consensus.

        Parameters
        ----------
        del_manager : arc4.Address
            Manager address for the delegation contract.
        del_app : Application
            App ID of the delegator contract.
        del_app_idx : UInt64
            Index of the delegator manager app list at which the delegator contract is stored.
            This is to save on opcode cost instead of looping through the whole list.
        val_owner : arc4.Address
            Owner address for the validator ad.
        val_app : Application
            App ID of the validator ad.
        val_app_idx : UInt64
            Index of the requested validator ad in validator owner app list.
            This is to save on opcode cost instead of looping through the whole list.
        """

        self._assert_user_and_app(del_manager, del_app, del_app_idx, Bytes(ROLE_DEL))

        self._assert_user_and_app(val_owner, val_app, val_app_idx, Bytes(ROLE_VAL))

        # Reports a breach in suspended
        res, app_txn = arc4.abi_call(
            ValidatorAd.breach_suspended,
            del_app,
            app_id=val_app.id,
        )

        try_send_note(res.del_manager.native, res.msg.bytes)

        return

    @arc4.abimethod()
    def contract_claim(
        self,
        del_manager: arc4.Address,
        del_app: Application,
        del_app_idx : UInt64,
        val_owner: arc4.Address,
        val_app: Application,
        val_app_idx: UInt64,
    ) -> EarningsDistribution:
        """
        Claims the operational fee up to this round from a delegator contract and
        transfers it to the validator ad as well as the commission to the platform.

        Parameters
        ----------
        del_manager : arc4.Address
            Manager address for the delegation contract.
        del_app : Application
            App ID of the delegator contract.
        del_app_idx : UInt64
            Index of the delegator manager app list at which the delegator contract is stored.
            This is to save on opcode cost instead of looping through the whole list.
        val_owner : arc4.Address
            Owner address for the validator ad.
        val_app : Application
            App ID of the validator ad.
        val_app_idx : UInt64
            Index of the requested validator ad in validator owner app list.
            This is to save on opcode cost instead of looping through the whole list.
        """

        self._assert_user_and_app(del_manager, del_app, del_app_idx, Bytes(ROLE_DEL))

        self._assert_user_and_app(val_owner, val_app, val_app_idx, Bytes(ROLE_VAL))

        # Claims operational fee
        res, app_txn = arc4.abi_call(
            ValidatorAd.contract_claim,
            del_app,
            app_id=val_app.id,
        )

        return res.copy()

    @arc4.abimethod()
    def contract_expired(
        self,
        del_manager: arc4.Address,
        del_app: Application,
        del_app_idx : UInt64,
        val_owner: arc4.Address,
        val_app: Application,
        val_app_idx: UInt64,
    ) -> None:
        """
        Reports that a delegator contract has expired.

        Parameters
        ----------
        del_manager : arc4.Address
            Manager address for the delegation contract.
        del_app : Application
            App ID of the delegator contract.
        del_app_idx : UInt64
            Index of the delegator manager app list at which the delegator contract is stored.
            This is to save on opcode cost instead of looping through the whole list.
        val_owner : arc4.Address
            Owner address for the validator ad.
        val_app : Application
            App ID of the validator ad.
        val_app_idx : UInt64
            Index of the requested validator ad in validator owner app list.
            This is to save on opcode cost instead of looping through the whole list.
        """

        self._assert_user_and_app(del_manager, del_app, del_app_idx, Bytes(ROLE_DEL))

        self._assert_user_and_app(val_owner, val_app, val_app_idx, Bytes(ROLE_VAL))

        # Reports contract has expired
        res, app_txn = arc4.abi_call(
            ValidatorAd.contract_expired,
            del_app,
            app_id=val_app.id,
        )

        try_send_note(res.del_manager.native, res.msg.bytes)

        return

    @arc4.abimethod()
    def contract_withdraw(
        self,
        del_app: Application,
        del_app_idx : UInt64,
        val_owner: arc4.Address,
        val_app: Application,
        val_app_idx: UInt64,
    ) -> None:
        """
        Delegator manager gracefully withdraws from the delegator contract prematurely.

        Parameters
        ----------
        del_app : Application
            App ID of the delegator contract.
        del_app_idx : UInt64
            Index of the delegator manager app list at which the delegator contract is stored.
            This is to save on opcode cost instead of looping through the whole list.
        val_owner : arc4.Address
            Owner address for the validator ad.
        val_app : Application
            App ID of the validator ad.
        val_app_idx : UInt64
            Index of the requested validator ad in validator owner app list.
            This is to save on opcode cost instead of looping through the whole list.
        """

        del_manager = arc4.Address(Txn.sender)
        self._assert_user_and_app(del_manager, del_app, del_app_idx, Bytes(ROLE_DEL))

        self._assert_user_and_app(val_owner, val_app, val_app_idx, Bytes(ROLE_VAL))

        # Gracefully withdraw from contract prematurely
        app_txn = arc4.abi_call(  # noqa: F841
            ValidatorAd.contract_withdraw,
            del_manager,
            del_app,
            app_id=val_app.id,
        )

        return

    @arc4.abimethod()
    def contract_delete(
        self,
        del_app: Application,
        del_app_idx : UInt64,
        val_owner: arc4.Address,
        val_app: Application,
        val_app_idx: UInt64,
    ) -> ContractDeleteReturn:
        """
        Deletes a delegator contract.

        Parameters
        ----------
        del_app : Application
            App ID of the delegator contract.
        del_app_idx : UInt64
            Index of the delegator manager app list at which the delegator contract is stored.
            This is to save on opcode cost instead of looping through the whole list.
        val_owner : arc4.Address
            Owner address for the validator ad.
        val_app : Application
            App ID of the validator ad.
        val_app_idx : UInt64
            Index of the requested validator ad in validator owner app list.
            This is to save on opcode cost instead of looping through the whole list.

        Returns
        -------
        remaining_balance : UInt64
            Balance of the fee asset that remained in the delegator contract.
        asset_id : UInt64
            Asset ID of the remaining balance.
        """

        del_manager = arc4.Address(Txn.sender)
        self._assert_user_and_app(del_manager, del_app, del_app_idx, Bytes(ROLE_DEL))

        self._assert_user_and_app(val_owner, val_app, val_app_idx, Bytes(ROLE_VAL))

        # Deletes the delegator contract
        remaining_balance, app_txn = arc4.abi_call(
            ValidatorAd.contract_delete,
            del_manager,
            del_app,
            app_id=val_app.id,
        )

        self._remove_user_app(del_manager, arc4.UInt64(del_app.id), del_app_idx)

        return remaining_balance

    @arc4.abimethod()
    def contract_report_expiry_soon(
        self,
        del_manager: arc4.Address,
        del_app: Application,
        del_app_idx : UInt64,
        val_owner: arc4.Address,
        val_app: Application,
        val_app_idx: UInt64,
    ) -> None:
        """
        Reports that the contract will expire soon.

        Parameters
        ----------
        del_manager : arc4.Address
            Manager address for the delegation contract.
        del_app : Application
            App ID of the delegator contract.
        del_app_idx : UInt64
            Index of the delegator manager app list at which the delegator contract is stored.
            This is to save on opcode cost instead of looping through the whole list.
        val_owner : arc4.Address
            Owner address for the validator ad.
        val_app : Application
            App ID of the validator ad.
        val_app_idx : UInt64
            Index of the requested validator ad in validator owner app list.
            This is to save on opcode cost instead of looping through the whole list.
        """

        self._assert_user_and_app(del_manager, del_app, del_app_idx, Bytes(ROLE_DEL))

        self._assert_user_and_app(val_owner, val_app, val_app_idx, Bytes(ROLE_VAL))

        # Reports contract will soon expire
        res, app_txn = arc4.abi_call(
            ValidatorAd.contract_report_expiry_soon,
            self.noticeboard_terms_timing.before_expiry.native,
            self.noticeboard_terms_timing.report_period.native,
            del_app,
            app_id=val_app.id,
        )

        try_send_note(res.del_manager.native, res.msg.bytes)

        return

    # ----- ----- ----- ------------------ ----- ----- -----
    # ----- ----- ----- Read-only functions ----- ----- ----
    # ----- ----- ----- ------------------ ----- ----- -----
    @arc4.abimethod(readonly=True)
    def get_noticeboard_asset(
        self,
        asset_id : UInt64,
    ) -> NoticeboardAssetInfo:
        """
        Returns information about the payment asset that is or was accepted on the platform.

        Returns
        -------
        asset_info : NoticeboardAssetInfo
            Information about the payment asset that is or was accepted on the platform.
        """
        return self.assets[asset_id]

    @arc4.abimethod(readonly=True)
    def get_noticeboard_user(
        self,
        user : arc4.Address,
    ) -> UserInfo:
        """
        Returns information about the user on the platform.

        Returns
        -------
        user_info : UserInfo
            Information about the user on the platform.
        """
        return self.users[user]

    # ----- ----- ----- ------------------ ----- ----- -----
    # ----- ----- ----- Internal functions ----- ----- -----
    # ----- ----- ----- ------------------ ----- ----- -----
    @subroutine
    def _assert_user_and_app(
        self,
        user: arc4.Address,
        app: Application,
        app_idx: UInt64,
        role: Bytes,
    ) -> None:
        """
        Asserts that the input user has the given role.
        Asserts that the input user has the input app in its list of apps (at app_idx),
        i.e. that the app is part of this platform.
        """
        assert self.users[user].role.bytes == role, ERROR_USER_UNEXPECTED_ROLE
        assert self.users[user].app_ids[app_idx] == app.id, ERROR_APP_NOT_WITH_USER

        return

    @subroutine
    def _store_user_app(
        self,
        user: arc4.Address,
        app_id: arc4.UInt64,
        app_idx: UInt64,
    ) -> None:
        """
        Stores the app ID to user's list of apps at given index.
        If index is already occupied, the call fails.
        """

        # Check if delegator has place to store the new contract and store it
        assert self.users[user].app_ids[app_idx].native == UInt64(0), ERROR_USER_APP_LIST_INDEX_TAKEN
        self.users[user].app_ids[app_idx] = app_id
        self.users[user].cnt_app_ids = arc4.UInt64(
            self.users[user].cnt_app_ids.native + UInt64(1)
        )

        return

    @subroutine
    def _remove_user_app(
        self,
        user: arc4.Address,
        app_id: arc4.UInt64,
        app_idx: UInt64,
    ) -> None:
        """
        Removes the app ID from user's list of apps at given index.
        """

        assert self.users[user].app_ids[app_idx].native == app_id, ERROR_USER_APP_CANNOT_REMOVE_FROM_LIST
        self.users[user].app_ids[app_idx] = arc4.UInt64(UInt64(0))
        self.users[user].cnt_app_ids = arc4.UInt64(
            self.users[user].cnt_app_ids.native - UInt64(1)
        )

        return

    @subroutine
    def _assert_terms_time(
        self,
        terms_time: ValidatorTermsTiming,
    ) -> None:

        assert terms_time.rounds_duration_min >= self.noticeboard_terms_timing.rounds_duration_min_min, ERROR_AD_MIN_DURATION_TOO_SHORT  # noqa: E501
        assert terms_time.rounds_duration_max <= self.noticeboard_terms_timing.rounds_duration_max_max, ERROR_AD_MAX_DURATION_TOO_LONG  # noqa: E501

        return

    @subroutine
    def _assert_terms_price(
        self,
        terms_price: ValidatorTermsPricing,
    ) -> None:

        # Confirm minimum commission
        assert terms_price.commission.native <= COMMISSION_MAX, ERROR_COMMISSION_MAX
        assert terms_price.commission.native >= self.noticeboard_fees.commission_min, ERROR_COMMISSION_MIN

        # Confirm that the payment asset is accepted at the platform
        asset_info = self.assets[terms_price.fee_asset_id.native].copy()  # Will fail if asset does not exist on the platform  # noqa: E501
        assert asset_info.accepted.native, ERROR_ASSET_NOT_ALLOWED

        # Confirm minimum pricing for this asset
        assert terms_price.fee_round_min >= asset_info.fee_round_min_min, ERROR_AD_FEE_ROUND_MIN_TOO_SMALL
        assert terms_price.fee_round_var >= asset_info.fee_round_var_min, ERROR_AD_FEE_ROUND_VAR_TOO_SMALL
        assert terms_price.fee_setup >= asset_info.fee_setup_min, ERROR_AD_FEE_SETUP_TOO_SMALL

        return

    @subroutine
    def _assert_terms_stake(
        self,
        terms_stake: ValidatorTermsStakeLimits,
    ) -> None:

        assert terms_stake.stake_max <= self.noticeboard_terms_node.stake_max_max, ERROR_AD_STAKE_MAX_TOO_LARGE
        assert terms_stake.stake_max >= self.noticeboard_terms_node.stake_max_min, ERROR_AD_STAKE_MAX_TOO_SMALL

        return
