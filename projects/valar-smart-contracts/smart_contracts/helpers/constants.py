# pyright: reportMissingModuleSource=false

# ------- Definition of constants -------

ALGO_ASA_ID = 0
"""
ALGO_ASA_ID : int
    ALGO asset ID.
"""

COMMISSION_MAX = 1_000_000
"""
COMMISSION_MAX : int
    Maximum commission possible at the platform.
"""

ONE_IN_PPM = 1_000_000
"""
ONE_IN_PPM : int
    1 = 1_000_000 parts per million.
"""

STAKE_GRATIS_MAX = 1_000_000
"""
STAKE_GRATIS_MAX : int
    Maximum percentage for increasing the maximum stake requested by the delegator.
"""

FROM_BASE_TO_MILLI_MULTIPLIER = 1_000
"""
FROM_BASE_TO_MILLI_MULTIPLIER : int
    Multiplier to convert a value in base units to milli units.
"""

FROM_BASE_TO_MICRO_MULTIPLIER = 1_000_000
"""
FROM_BASE_TO_MICRO_MULTIPLIER : int
    Multiplier to convert a value in base units to micro units.
"""

FROM_MILLI_TO_NANO_MULTIPLIER = 1_000_000
"""
FROM_MILLI_TO_FEMTO_MULTIPLIER : int
    Multiplier to convert a value in milli units to nano units.
"""

INCENTIVES_ELIGIBLE_FEE = 2_000_000
"""
INCENTIVES_ELIGIBLE_FEE : int
    Fee amount required by Algorand network during key registration transaction for
    account to be eligible for incentives, i.e. tracked by the suspension mechanism.
"""

MBR_ACCOUNT = 100_000
"""
MBR_ACCOUNT : int
    Minimum balance requirement for a valid account.
    In microAlgo.
"""

MBR_ASA = 100_000
"""
MBR_ASA : int
    Minimum balance requirement increase when opting into an ASA.
    In microAlgo.
"""

MBR_VALIDATOR_AD_ASA_BOX = 2_500 + 400 * (4 + 8 + 2*8)
"""
MBR_VALIDATOR_AD_ASA_BOX : int
    Minimum balance requirement increase due to box for an ASA at ValidatorAd.
    In microAlgo.
    The box consists of 4 bytes for key prefix, 8 bytes for the name, and 2*8 bytes for the contents of ValidatorASA.
"""

MBR_NOTICEBOARD_ASSET_BOX = 2_500 + 400 * (6 + 8 + 25)
"""
MBR_VALIDATOR_ASSET_BOX : int
    Minimum balance requirement increase due to box for an asset at Noticeboard.
    In microAlgo.
    The box consists of 6 bytes for key prefix (BOX_ASSET_KEY_PREFIX), 8 bytes for the name (asset_id), and
    (1+3*8) byte for the contents of NoticeboardAsset.
"""

MBR_USER_BOX = 2_500 + 400 * ((32) + (4 + 8 + 2*32 + 8*110 + 8))
r"""
MBR_USER_BOX : int
    Minimum balance requirement increase due to box for an user at Noticeboard.
    In microAlgo.
    The box consists of 32 bytes for the name (i.e. address), and
    (4 + 8 + 2\*32 + 8\*110 + 8) = 980 bytes for the contents of UserInfo.
"""

MBR_PARTNER_BOX = 2_500 + 400 * ((8 + 32) + (2*8))
r"""
MBR_PARTNER_BOX : int
    Minimum balance requirement increase due to box for a partner at Noticeboard.
    In microAlgo.
    The box consists of 8 bytes for key (i.e. "partner_") and 32 bytes for the name (i.e. address),
    and (2*8) = 16 bytes for the contents of PartnerCommissions.
"""

MBR_AD_TERMS = MBR_ASA + MBR_VALIDATOR_AD_ASA_BOX
"""
MBR_AD_TERMS : int
    Minimum balance requirement increase when adding a new ASA to ValidatorAd terms.
    In microAlgo.
"""

MAXIMUM_NUMBER_OF_DELEGATORS_PER_NODE: int = 4
"""
MAXIMUM_NUMBER_OF_DELEGATORS_PER_NODE : int
    Maximum number of delegator contracts allowed per node, i.e. validator ad.
    This is due to performance degradation of a node with more accounts.
"""

MAXIMUM_NUMBER_OF_DELEGATOR_CONTRACTS_PER_VALIDATOR_AD: int = 14
"""
MAXIMUM_NUMBER_OF_DELEGATOR_CONTRACTS_PER_VALIDATOR_AD : int
    Maximum number of delegator contracts allowed per node, i.e. validator ad.
    This is due to limited (global) memory storage.
"""

MBR_DELEGATOR_CONTRACT = MBR_ACCOUNT + MBR_ASA
"""
MBR_DELEGATOR_CONTRACT : int
    Minimum balance requirement for the Delegator Contract.
    In microAlgo.
"""

MBR_VALIDATOR_AD_DELEGATOR_CONTRACT_INCREASE = MBR_DELEGATOR_CONTRACT + 992_000
"""
MBR_VALIDATOR_AD_DELEGATOR_CONTRACT_INCREASE : int
    Minimum balance requirement increase for the Validator Ad at creation of a delegator contract.
    In microAlgo.
"""

MBR_NOTICEBOARD_VALIDATOR_AD_CONTRACT_INCREASE = 921_000
"""
MBR_NOTICEBOARD_VALIDATOR_AD_CONTRACT_INCREASE : int
    Minimum balance requirement increase for the Noticeboard at creation of a validator ad.
    In microAlgo.
"""

BOX_ASA_KEY_PREFIX = b"asa_"
"""
BOX_ASA_KEY_PREFIX : bytes
    Prefix for the boxes of ASA at ValidatorAd.
"""

BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY = b"d"
"""
BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY : bytes of length 1
    Key for the box of delegator contract template at ValidatorAd and Noticeboard.
"""

BOX_VALIDATOR_AD_TEMPLATE_KEY = b"v"
"""
BOX_VALIDATOR_AD_TEMPLATE_KEY : bytes of length 1
    Key for the box of validator ad template at Noticeboard.
"""

BOX_SIZE_PER_REF = 1024
"""
BOX_SIZE_PER_REF : int
    Number of bytes of access per box reference.
"""

BOX_ASSET_KEY_PREFIX = b"asset_"
"""
BOX_ASSET_KEY_PREFIX : bytes
    Prefix for the boxes of asset at Noticeboard.
"""

BOX_PARTNERS_PREFIX = b"partner_"
"""
BOX_PARTNERS_PREFIX : bytes
    Prefix for the boxes of partners at Noticeboard.
"""

DLL_PREFIX = b"dll_"
"""
DLL_PREFIX : bytes
    Prefix for the double linked list in global storage at Noticeboard.
"""

DLL_VAL = DLL_PREFIX + b"_val"
"""
DLL_VAL : bytes
    Name for the double linked list for validators in global storage at Noticeboard.
"""

DLL_DEL = DLL_PREFIX + b"_del"
"""
DLL_DEL : bytes
    Name for the double linked list for delegators in global storage at Noticeboard.
"""

# ------- Notification messages -------
MSG_CORE = b"Message from Valar: "
MSG_CORE_KEYS_SUBMIT        = MSG_CORE + b"Node has been prepared for you to stake.                                        "  # noqa: E501
MSG_CORE_KEYS_NOT_SUBMITTED = MSG_CORE + b"Node runner has unfortunately not prepared a node for you.                      "  # noqa: E501
MSG_CORE_KEYS_NOT_CONFIRMED = MSG_CORE + b"You have not confirmed the node that was prepared for you.                      "  # noqa: E501
MSG_CORE_CONTRACT_EXPIRED   = MSG_CORE + b"Your contract to stake with a node runner has ended.                            "  # noqa: E501
MSG_CORE_BREACH_LIMITS_ERROR= MSG_CORE + b"Your balance is outside the limits agreed with the node runner. Correct it!     "  # noqa: E501
MSG_CORE_BREACH_LIMITS_END  = MSG_CORE + b"Your contract has ended because you breached the terms too many times.          "  # noqa: E501
MSG_CORE_BREACH_SUSPENDED   = MSG_CORE + b"The network has suspended your account from staking. You don't stake anymore.   "  # noqa: E501
MSG_CORE_BREACH_PAY         = MSG_CORE + b"There is an issue with your payment to the node runner. You don't stake anymore."  # noqa: E501
MSG_CORE_WILL_EXPIRE        = MSG_CORE + b"Your contract to stake with a node runner is expiring. Consider extending it!   "  # noqa: E501

# ------- Error messages -------
# From DelegatorContract
ERROR_RECEIVER = "Transaction must be to this contract."
ERROR_ASSET_ID = "Sent asset doesn't match the agreed one."
ERROR_AMOUNT = "Sent amount doesn't match the agreed one."
ERROR_NOT_PAYMENT_OR_XFER = "Transaction type must be either Payment or AssetTransfer."
ERROR_NOT_STATE_SET = "Cannot be called from other state than SET."
ERROR_NOT_STATE_CREATED = "Cannot be called from other state than CREATED."
ERROR_NOT_STATE_READY = "Cannot be called from other state than READY."
ERROR_NOT_STATE_SUBMITTED = "Cannot be called from other state than SUBMITTED."
ERROR_NOT_STATE_LIVE = "Cannot be called from other state than LIVE."
ERROR_NOT_STATE_LIVE_OR_SUBMITTED_OR_READY = "Cannot be called from other state than LIVE or SUBMITTED or READY."
ERROR_DELEGATION_PERIOD_TOO_SHORT = "Too short delegation period."
ERROR_DELEGATION_PERIOD_TOO_LONG = "Too long delegation period."
ERROR_DELEGATION_ENDS_TOO_LATE = "Delegation would end at a later time than allowed by validator."
ERROR_REQUESTED_MAX_STAKE_TOO_HIGH = "Delegator requested a stake above the maximum allowed by the validator."
ERROR_TERM_GRATIS_MAX = "Validator ad gratis stake amount must be at smaller or equal to the maximum possible."
ERROR_AD_END_IS_IN_PAST = "Validator ad end time defined is in the past."
ERROR_CALLED_BY_NOT_CREATOR = "Can only be called by smart contract creator."
ERROR_KEY_SUBMIT_TOO_LATE = "Key submission was done too late."
ERROR_KEY_BENEFICIARY_MISMATCH = "Key beneficiary does not match."
ERROR_VOTE_FIRST_ROUND_MISMATCH = "Vote first round does not match contract start."
ERROR_VOTE_LAST_ROUND_MISMATCH = "Vote last round does not match contract end."
ERROR_NOT_MANAGER = "Can only be approved by delegator manager."

ERROR_KEY_CONFIRM_TOO_LATE = "Key confirmation was done too late."
ERROR_REPORT_NOT_SUBMITTED_TOO_EARLY = "Report keys as not submitted can be done only after enough rounds have passed."
ERROR_REPORT_NOT_CONFIRMED_TOO_EARLY = "Report keys as not confirmed can be done only after enough rounds have passed."
ERROR_INSUFFICIENT_BALANCE = "Earnings cannot be paid because DelegatorContract has insufficient amount."
ERROR_BALANCE_FROZEN = "Earnings cannot be paid because DelegatorContract has the asset frozen."
ERROR_INSUFFICIENT_ALGO = "Earnings cannot be paid because DelegatorContract has insufficient ALGO."
ERROR_OPERATION_FEE_ALREADY_CLAIMED_AT_ROUND = "Operational fee has already been claimed up to this round."
ERROR_NOT_YET_EXPIRED = "Cannot be called when the contract has not yet expired."
ERROR_ALREADY_EXPIRED = "Cannot be called when the contract has already expired."
ERROR_NOT_ENDED_STATE = "Cannot be called from other state than ENDED_xyz."
ERROR_ALGO_IS_PERMISSIONLESS = "ALGO cannot be frozen or clawed back."
ERROR_ENOUGH_FUNDS_FOR_SETUP_AND_OPERATIONAL_FEE = "Contract has sufficient funds to pay the setup and operational fee."
ERROR_ENOUGH_FUNDS_FOR_OPERATIONAL_FEE = "Contract has sufficient funds to pay the full operational fee."
ERROR_ENOUGH_FUNDS_FOR_EARNED_OPERATIONAL_FEE = "Contract has sufficient funds to pay the earned operational fee."
ERROR_LIMIT_BREACH_TOO_EARLY = "Not enough rounds have passed since last limit breach event."
ERROR_IS_STILL_ELIGIBLE = "Delegator beneficiary is still eligible according to the agreed limits."
ERROR_NOT_ELIGIBLE = "Delegator beneficiary is not eligible according to the agreed limits."
ERROR_ACCOUNT_HAS_NOT_BEEN_SUSPENDED = "Account is still participating in consensus."
ERROR_ACCOUNT_HAS_NOT_REGISTERED_FOR_SUSPENSION_TRACKING = "Must opt-in to consensus suspension tracking."
# From ValidatorAd
ERROR_CALLED_FROM_STATE_CREATED_TEMPLATE_LOAD_OR_TEMPLATE_LOADED = \
    "Cannot be called from state CREATED, TEMPLATE_LOAD or TEMPLATE_LOADED."
ERROR_NOT_STATE_TEMPLATE_LOAD = "Cannot be called from other state than TEMPLATE_LOAD."
ERROR_CALLED_BY_NOT_VAL_OWNER = "Can only be called by validator owner."
ERROR_CALLED_BY_NOT_VAL_MANAGER = "Can only be called by validator manager."
ERROR_NOT_STATE_READY_OR_NOT_READY = "Cannot be called from other state than READY or NOT_READY."
ERROR_DELETE_ACTIVE_DELEGATORS = "Cannot delete validator ad if there are active delegators."
ERROR_DELETE_ASA_REMAIN = "Cannot delete validator if there are ASAs that remain."
ERROR_DELETE_TEMPLATE_BOX = "Cannot delete box with smart contract template."
ERROR_ALGO_AVAILABLE_BALANCE_NOT_ZERO = "Algorand balance is not zero."
ERROR_TERMS_MIN_DURATION_SETUP_CONFIRM = "Minimum delegation duration must be longer the sum of setup and confirmation rounds."  # noqa: E501
ERROR_TERM_DURATION_MIN_LARGER_THAN_MAX = "Minimum delegation duration cannot be larger than maximum duration."
ERROR_AD_TERMS_MBR = "Insufficient payment for MBR increase of validator ad due to new terms."
ERROR_ASA_NOT_STORED_AT_VALIDATOR_AD = "ASA is not stored at validator ad."
ERROR_ASA_BOX_NOT_DELETED = "Failed to delete ASA box."
ERROR_CANNOT_REMOVE_ASA_WITH_ACTIVE_DELEGATORS = "Cannot remove ASA while there are active delegators because one could be still using it."  # noqa: E501
ERROR_DELEGATOR_LIST_FULL = "Could not add delegator contract to delegator contract list."
ERROR_VALIDATOR_FULL = "Validator ad has reach the limit of maximum number of active delegators accepted."
ERROR_DELEGATOR_DOES_NOT_EXIST_AT_VALIDATOR_AD = "Delegator contract does not exist in the list of active delegators of the validator ad."  # noqa: E501
ERROR_FAIL_TO_REMOVE_DELEGATOR_CONTRACT_FROM_LIST = "Failed to remove delegator contract from the list of active delegators of the validator ad."  # noqa: E501
ERROR_NO_MEMORY_FOR_MORE_DELEGATORS = "Validator ad does not have enough memory to store that many active delegators."
# From Noticeboard
ERROR_CALLED_BY_NOT_PLA_MANAGER_OR_CREATOR = "Can only be called by platform manager or creator."
ERROR_CALLED_BY_NOT_PLA_MANAGER_OR_ASSET_CONFIG_MANAGER = "Can only be called by platform manager or asset config manager."  # noqa: E501
ERROR_CALLED_FROM_STATE_RETIRED = "Cannot be called from state RETIRED."
ERROR_NOT_STATE_DEPLOYED = "Cannot be called from other state than DEPLOYED."
ERROR_NOT_STATE_SUSPENDED = "Cannot be called from other state than SUSPENDED."
ERROR_CALLED_BY_NOT_PLA_MANAGER = "Can only be called by platform manager."
ERROR_AMOUNT_ASA_OPTIN_MBR = "Sent amount doesn't match the MBR increase for opting into an ASA."
ERROR_PLATFORM_NOT_OPTED_IN_ASA = "Platform is not opted into the ASA."
ERROR_MBR_INCREASE_NOT_PAID = "Increase for the MBR was not paid."
ERROR_USER_ALREADY_EXISTS = "User already exists on the platform."
ERROR_UNKNOWN_USER_ROLE = "Requested user role does not exist."
ERROR_USER_REGISTRATION_FEE_NOT_PAID = "User did not pay for the increase in MBR and user registration fee."
ERROR_USER_DOES_NOT_EXIST = "check self.users entry exists"
ERROR_USER_BOX_NOT_DELETED = "Failed to delete user box."
ERROR_USER_HAS_ACTIVE_CONTRACTS = "User has one or more active smart contracts."
ERROR_USER_NOT_DELEGATOR = "User is not a registered delegator on the platform."
ERROR_USER_NOT_VALIDATOR = "User is not registered as validator on the platform."
ERROR_USER_UNEXPECTED_ROLE = "User does not have the expected role on the platform."
ERROR_APP_NOT_WITH_USER = "Requested app is not under the given user."
ERROR_USER_APP_LIST_INDEX_TAKEN = "Cannot store app on the index because it is taken."
ERROR_USER_APP_CANNOT_REMOVE_FROM_LIST = "Cannot remove app from the index because it does not match."
ERROR_UNEXPECTED_TEMPLATE_NAME = "Unexpected name for box for a contract template."
ERROR_AD_CREATION_INCORRECT_PAY_AMOUNT = "During ad creation, incorrect amount of ALGO was paid."
ERROR_TERMS_AND_CONDITIONS_DONT_MATCH = "Terms and conditions do not match the ones defined by the platform."
ERROR_COMMISSION_MIN = "Validator ad commission must be at least the amount defined at the platform."
ERROR_COMMISSION_MAX = "Validator ad commission must be smaller or equal to the maximum possible platform commission."
ERROR_ASSET_NOT_ALLOWED = "Validator ad payment asset must be allowed by the platform."
ERROR_AD_MIN_DURATION_TOO_SHORT = "Ad minimum accepted duration must be larger than the minimum on the platform."
ERROR_AD_MAX_DURATION_TOO_LONG = "Ad maximum accepted duration must be smaller than the maximum on the platform."
ERROR_AD_FEE_ROUND_MIN_TOO_SMALL = "Ad fee_round_min must be larger than the minimum on the platform."
ERROR_AD_FEE_ROUND_VAR_TOO_SMALL = "Ad fee_round_var duration must be larger than the minimum on the platform."
ERROR_AD_FEE_SETUP_TOO_SMALL = "Ad fee_setup must be larger than the minimum on the platform."
ERROR_AD_STAKE_MAX_TOO_LARGE = "Ad stake_max must be smaller than the maximum on the platform."
ERROR_AD_STAKE_MAX_TOO_SMALL = "Ad stake_max must be larger than the minimum on the platform."
ERROR_VALIDATOR_AD_DOES_NOT_HAVE_STATE = "App does not have state."
ERROR_VALIDATOR_AD_DOES_NOT_COMPLY_WITH_TC = "Validator ad does not comply with platform's terms and conditions."
ERROR_PARTNER_NOT_DELETED = "Error while deleting partner box."
ERROR_PARTNER_CREATION_FEE_NOT_PAID = "Fee for MBR increase for creating partner on platform was not paid."
ERROR_TOO_SOON_TO_REPORT_EXPIRY_SOON = "It is too soon to report the contract is about to expire."
ERROR_TOO_SOON_TO_REPORT_EXPIRY_SOON_AGAIN = "It is too soon to report again that the contract is about to expire."
ERROR_UNSAFE_NUMBER_OF_DELEGATORS = "Requested number of maximum delegator is unsafe for node performance."
ERROR_THERE_CAN_BE_AT_LEAST_ONE_DELEGATOR = "There can be at least one delegator."
