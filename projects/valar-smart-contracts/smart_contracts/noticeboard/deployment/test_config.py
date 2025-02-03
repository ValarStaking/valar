
from smart_contracts.artifacts.noticeboard.client import (
    ValidatorTermsGating,
    ValidatorTermsPricing,
    ValidatorTermsStakeLimits,
    ValidatorTermsTiming,
    ValidatorTermsWarnings,
)
from smart_contracts.noticeboard.deployment.helpers import DelCo, ValAd
from smart_contracts.noticeboard.deployment.platform_params import BLOCKS_PER_DAY, NOTICEBOARD_FEES
from tests.utils import calc_fee_round, calc_operational_fee

# ----------------------------------------------------------------------------
# ------------------- Define scenario for test deployment  -------------------
# ----------------------------------------------------------------------------

# Array of ValAd objects, which define validator ads created, including delegator contracts under them.
TEST_SCENARIO : list[ValAd] = [
    ValAd(dels=[DelCo(state="LIVE")]),
    ValAd(dels=[DelCo(state="LIVE"), DelCo(state="READY")]),
    ValAd(dels=[DelCo(state="SUBMITTED"), DelCo(state="ENDED_WITHDREW")]),
    ValAd(state="READY"),
    ValAd(dels=[DelCo(state="LIVE")]),
    ValAd(dels=[DelCo(state="LIVE"), DelCo(state="READY"), DelCo(state="LIVE")]),
    ValAd(dels=[DelCo(state="SUBMITTED"), DelCo(state="ENDED_WITHDREW")]),
    ValAd(dels=[DelCo(state="LIVE"), DelCo(state="SUBMITTED")]),
    ValAd(dels=[DelCo(state="READY")]),
    ValAd(dels=[DelCo(state="READY"), DelCo(state="LIVE"), DelCo(state="LIVE")]),
    ValAd(state="READY"),
    ValAd(state="READY"),
    ValAd(dels=[DelCo(state="LIVE"), DelCo(state="LIVE")]),
    ValAd(dels=[DelCo(state="LIVE")]),
    ValAd(dels=[DelCo(state="LIVE"), DelCo(state="LIVE")]),
    ValAd(dels=[DelCo(state="LIVE"), DelCo(state="LIVE")]),
    ValAd(dels=[DelCo(state="LIVE"), DelCo(state="LIVE")]),
    ValAd(state="CREATED"),
    ValAd(acc_idx=-1, state="SET"),
    ValAd(acc_idx=-1, state="NOT_LIVE"),
    ValAd(acc_idx=-1, state="NOT_READY"),
    ValAd(acc_idx=-1, dels=[DelCo(state="LIVE"), DelCo(acc_idx=-1, state="READY")]),
    ValAd(acc_idx=-1, dels=[DelCo(acc_idx=-1, state="LIVE"), DelCo(acc_idx=-1, state="SUBMITTED"), ]),# DelCo(acc_idx=-1, state="ENDED_EXPIRED")]),  # noqa: E501
    ValAd(acc_idx=-1, dels=[DelCo(acc_idx=-1, state="ENDED_WITHDREW"), ]),# DelCo(acc_idx=-1, state="ENDED_NOT_CONFIRMED"), DelCo(acc_idx=-1, state="ENDED_NOT_SUBMITTED"), DelCo(acc_idx=-1, state="LIVE")]),  # noqa: E501
    ValAd(acc_idx=-1, state="READY"),
]

# -------------------------------------
# -------  Test validator terms -------
# -------------------------------------
VALIDATOR_TERMS_TIME = ValidatorTermsTiming(
    rounds_setup = round(BLOCKS_PER_DAY / 24 / 24),       # Maximum time to prepare the setup: ~2.5 min [in rounds]
    rounds_confirm = round(BLOCKS_PER_DAY/24/12),         # Waiting time for setup confirmation: ~5 min [in rounds]
    rounds_duration_min = round(BLOCKS_PER_DAY/24/6),    # Minimum staking duration:  10 min [in rounds]; must be larger than NOTICEBOARD_TERMS_TIMING.rounds_duration_min_min to succeed  # noqa: E501
    rounds_duration_max = round(90 * BLOCKS_PER_DAY),     # Maximum staking duration:  ~90 days [in rounds]; must be smaller than NOTICEBOARD_TERMS_TIMING.rounds_duration_max_max to succeed  # noqa: E501
    round_max_end = 999_999_999_999,                      # End date of node validity [round number]
)

VALIDATOR_TERMS_PRICE = ValidatorTermsPricing(
    commission = NOTICEBOARD_FEES.commission_min,  # Use minimum commission
    fee_round_min = round(10*10**6 / (30 * BLOCKS_PER_DAY) * 10**3),            # ~10 USDC/month [in nanoUSDC/round = (milli baseUSDC)/round]; must be larger than USDC_INFO.fee_round_min_min to succeed  # noqa: E501
    fee_round_var = round(10*10**6 / (30 * BLOCKS_PER_DAY * 10**5) * 10**9),    # ~10 USDC/(month * 100k ALGO) [in femtoUSDC/(round * ALGO) = (nano baseUSDC)/(round * ALGO)]; must be larger than USDC_INFO.fee_round_var_min to succeed  # noqa: E501
    fee_setup = 1*10**6,                                                        # 1 USDC [in microUSDC = baseUSDC]; must be larger than USDC_INFO.fee_setup_min to succeed  # noqa: E501
    fee_asset_id = 0,                                       # Must be set to the asset used
)

VALIDATOR_TERMS_STAKE = ValidatorTermsStakeLimits(
    stake_max = 2*10**(5+6),  # Maximum stake accepted per account [in microALGO]; must be smaller than NOTICEBOARD_TERMS_NODE.stake_max_max to succeed  # noqa: E501
    stake_gratis = 10**5,     # Gratis on the maximum stake [in ppm]
)

VALIDATOR_TERMS_REQS = ValidatorTermsGating(
    gating_asa_list = [(0, 0), (0, 0)],         # No ASA gating
)

VALIDATOR_TERMS_WARN = ValidatorTermsWarnings(
    cnt_warning_max = 3,                                    # Number of allowed warnings
    rounds_warning = round(1 * BLOCKS_PER_DAY / 3),         # Period between warnings: ~8 hours [in rounds]
)

# -------------------------------------
# -------  Test delegator terms -------
# -------------------------------------
STAKE_MAX = 5*10**(4+6)   # Must be smaller than VALIDATOR_TERMS_STAKE.stake_max to succeed
ROUNDS_DURATION = VALIDATOR_TERMS_TIME.rounds_duration_min
FEE_ROUND = calc_fee_round(
    STAKE_MAX,
    VALIDATOR_TERMS_PRICE.fee_round_min,
    VALIDATOR_TERMS_PRICE.fee_round_var,
)
FEE_OPERATIONAL = calc_operational_fee(FEE_ROUND, ROUNDS_DURATION, 0)
