import copy
import dataclasses

from algosdk.constants import ZERO_ADDRESS

from smart_contracts.artifacts.delegator_contract.client import DelegationTermsBalance, DelegationTermsGeneral
from smart_contracts.artifacts.noticeboard.client import (
    NoticeboardAssetInfo,
    NoticeboardFees,
    NoticeboardTermsNodeLimits,
    NoticeboardTermsTiming,
    PartnerCommissions,
    ValidatorSelfDisclosure,
    ValidatorTermsGating,
    ValidatorTermsPricing,
    ValidatorTermsStakeLimits,
    ValidatorTermsTiming,
    ValidatorTermsWarnings,
)
from smart_contracts.helpers.constants import MAXIMUM_NUMBER_OF_DELEGATORS_PER_NODE
from smart_contracts.noticeboard.constants import (
    STATE_NONE,
)
from tests.utils import KeyRegTxnInfoPlain, calc_fee_round, calc_stake_max

DEFAULT_STAKE_MAX = 100_000_000_000
DEFAULT_COMMISSION = 420_000
DEFAULT_PARTNER_COMMISSIONS = PartnerCommissions(
    commission_setup = 73_100,
    commission_operational = 31_321,
)
DEFAULT_TC_SHA256 = bytes([0xFF] * 32)

# -------  Default noticeboard terms -------
DEFAULT_SETUP_NOTICEBOARD_FEES = NoticeboardFees(
    commission_min = DEFAULT_COMMISSION,
    val_user_reg=1,
    del_user_reg=2,
    val_ad_creation=3,
    del_contract_creation=4,
)

DEFAULT_SETUP_NOTICEBOARD_TERMS_TIMING = NoticeboardTermsTiming(
    rounds_duration_min_min = 3,
    rounds_duration_max_max = 4_000_000,
    before_expiry = 102,
    report_period = 5,
)
DEFAULT_ASSET_INFO = NoticeboardAssetInfo(
    accepted = True,
    fee_round_min_min = 1,
    fee_round_var_min = 2,
    fee_setup_min = 3,
)
DEFAULT_SETUP_NOTICEBOARD_TERMS_NODE = NoticeboardTermsNodeLimits(
    stake_max_max = 10**(10+6),
    stake_max_min = 11,
    cnt_del_max_max = MAXIMUM_NUMBER_OF_DELEGATORS_PER_NODE,
)

# -------  Default key params -------
DEFAULT_SETUP_KEY_REG = KeyRegTxnInfoPlain(
    vote_first = None,
    vote_last = None,
    vote_key_dilution = None,
    selection_pk = "TyPKJHa8IcFFwJ0xvx4/uUeGgVk4pp8r90S5J/xya4M=",
    vote_pk = "CrPTVLdfR0z5U5Vx2MbcY8pMM8MDq7uSmKL8YJgGwuw=",
    state_proof_pk = "wcT8pSuOGU84gHJr67NiasgsMpr5pFir6wnzYCmEddnsp5Ys7mh9zWZ6jJJY7VK8jM3FsBoEnHFboYci8VbNpQ==",
    sender = None,
)

# -------  Default validator terms -------
DEFAULT_VALIDATOR_TERMS_TIME = ValidatorTermsTiming(
    rounds_setup = 11,
    rounds_confirm = 22,
    rounds_duration_min = 43,
    rounds_duration_max = 64,
    round_max_end = 999_999_999,
)

DEFAULT_VALIDATOR_TERMS_PRICE = ValidatorTermsPricing(
    commission = DEFAULT_COMMISSION,
    fee_round_min = 2,
    fee_round_var = 11,
    fee_setup = 115,
    fee_asset_id = 0,
)

DEFAULT_VALIDATOR_TERMS_STAKE = ValidatorTermsStakeLimits(
    stake_max = 11_111_111_111_000,
    stake_gratis = 85_000,
)

DEFAULT_VALIDATOR_TERMS_REQS = ValidatorTermsGating(
    gating_asa_list = [(0, 0), (0, 0)],
)

DEFAULT_VALIDATOR_TERMS_WARN = ValidatorTermsWarnings(
    cnt_warning_max = 3,
    rounds_warning = 10,
)

DEFAULT_VALIDATOR_SELF_DISCLOSURE = ValidatorSelfDisclosure(
    name = b"Silvio M".ljust(30, b" "),
    https = b"google.com".ljust(60, b" "),
    country_code = b"CH",
    hw_cat = 999_999_999,
    node_version = b"3.25.0-future".ljust(20, b" "),
)

# -------  Default delegator terms -------
DEFAULT_CREATED_DELEGATION_TERMS_BALANCE = DelegationTermsBalance(
    stake_max = calc_stake_max(
        DEFAULT_STAKE_MAX,
        DEFAULT_VALIDATOR_TERMS_STAKE.stake_max,
        DEFAULT_VALIDATOR_TERMS_STAKE.stake_gratis,
    ),
    cnt_breach_del_max = DEFAULT_VALIDATOR_TERMS_WARN.cnt_warning_max,
    rounds_breach = DEFAULT_VALIDATOR_TERMS_WARN.rounds_warning,
    gating_asa_list = DEFAULT_VALIDATOR_TERMS_REQS.gating_asa_list,
)
DEFAULT_FEE_ROUND = calc_fee_round(
    DEFAULT_STAKE_MAX,
    DEFAULT_VALIDATOR_TERMS_PRICE.fee_round_min,
    DEFAULT_VALIDATOR_TERMS_PRICE.fee_round_var,
)
DEFAULT_CREATED_DELEGATION_TERMS_GENERAL = DelegationTermsGeneral(
    commission = DEFAULT_COMMISSION,
    fee_round = DEFAULT_FEE_ROUND,
    fee_setup = DEFAULT_VALIDATOR_TERMS_PRICE.fee_setup,
    fee_asset_id = DEFAULT_VALIDATOR_TERMS_PRICE.fee_asset_id,
    partner_address = ZERO_ADDRESS,
    fee_round_partner = 0,
    fee_setup_partner = 0,
    rounds_setup = DEFAULT_VALIDATOR_TERMS_TIME.rounds_setup,
    rounds_confirm = DEFAULT_VALIDATOR_TERMS_TIME.rounds_confirm,
)

# ------- Data classes -------
@dataclasses.dataclass(kw_only=True)
class ActionInputs:

    # Noticeboard
    pla_manager: str | None = None
    asset_config_manager: str | None = None

    tc_sha256: bytes = DEFAULT_TC_SHA256

    noticeboard_fees: NoticeboardFees | None = dataclasses.field(default_factory=lambda: copy.deepcopy(DEFAULT_SETUP_NOTICEBOARD_FEES))  # noqa: E501
    noticeboard_terms_timing: NoticeboardTermsTiming | None = dataclasses.field(default_factory=lambda: copy.deepcopy(DEFAULT_SETUP_NOTICEBOARD_TERMS_TIMING))  # noqa: E501
    noticeboard_terms_node: NoticeboardTermsNodeLimits | None = dataclasses.field(default_factory=lambda: copy.deepcopy(DEFAULT_SETUP_NOTICEBOARD_TERMS_NODE))  # noqa: E501

    state: bytes = STATE_NONE

    app_id_new: int = 0
    app_id_old: int = 0

    template: bytes | None = None
    template_size: int | None = None
    template_name: bytes | None = None
    template_test_offset: int | None = None

    user_role: bytes | None = None

    partner_address: str | None = ZERO_ADDRESS
    partner_commissions: PartnerCommissions | None = dataclasses.field(default_factory=lambda: copy.deepcopy(DEFAULT_PARTNER_COMMISSIONS))  # noqa: E501
    partner_delete: bool = False

    asset_info: NoticeboardAssetInfo | None = dataclasses.field(default_factory=lambda: copy.deepcopy(DEFAULT_ASSET_INFO))  # noqa: E501

    user_to_get: str | None = None

    # ValidatorAd
    val_info: ValidatorSelfDisclosure | None = None

    ad_sha256: bytes | None = None
    ad_commission: int | None = None

    terms_time: ValidatorTermsTiming = dataclasses.field(default_factory=lambda: copy.deepcopy(DEFAULT_VALIDATOR_TERMS_TIME))  # noqa: E501
    terms_price: ValidatorTermsPricing = dataclasses.field(default_factory=lambda: copy.deepcopy(DEFAULT_VALIDATOR_TERMS_PRICE))  # noqa: E501
    terms_stake: ValidatorTermsStakeLimits = dataclasses.field(default_factory=lambda: copy.deepcopy(DEFAULT_VALIDATOR_TERMS_STAKE))  # noqa: E501
    terms_reqs: ValidatorTermsGating = dataclasses.field(default_factory=lambda: copy.deepcopy(DEFAULT_VALIDATOR_TERMS_REQS))  # noqa: E501
    terms_warn: ValidatorTermsWarnings = dataclasses.field(default_factory=lambda: copy.deepcopy(DEFAULT_VALIDATOR_TERMS_WARN))  # noqa: E501

    val_manager: str | None = None
    live: bool | None = None
    cnt_del_max: int | None = None

    mbr_delegator_template_box: int | None = None

    val_app_id: int | None = None
    val_app_idx: int | None = None

    val_owner: str | None = None
    ready: bool | None = None

    # DelegatorContract

    del_beneficiary: str | None = None
    rounds_duration: int | None = None
    stake_max: int = DEFAULT_STAKE_MAX

    fee_amount: int | None = None

    del_sha256: bytes | None = None

    del_manager: str | None = None

    del_app_id: int | None = None
    del_app_idx: int | None = None

    fee_operational: int | None = None

    wait_until_keys_not_submitted : bool = True
    wait_until_keys_not_confirmed : bool = True
    wait_until_expired : bool = True
    freeze_delegator_contract : bool = True

    wait_until_limit_breach : bool = True

    wait_expiry_report : bool = True

    key_reg_before_confirm: bool = True
    key_reg_fee: int | None = None
    key_reg_atomically: bool = False

    wait_until_suspended: bool = False

    # Joint (for simplicity)
    key_reg: KeyRegTxnInfoPlain | None = dataclasses.field(default_factory=lambda: copy.deepcopy(DEFAULT_SETUP_KEY_REG))

    receiver: str | None = None
    amount: int | None = None

    asset: int | None = None


