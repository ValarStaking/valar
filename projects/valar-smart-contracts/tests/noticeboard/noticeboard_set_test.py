
import copy

import pytest
from algokit_utils.logic_error import LogicError

from smart_contracts.artifacts.noticeboard.client import (
    NoticeboardFees,
    NoticeboardTermsNodeLimits,
    NoticeboardTermsTiming,
)
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY,
    BOX_VALIDATOR_AD_TEMPLATE_KEY,
    ERROR_CALLED_BY_NOT_PLA_MANAGER_OR_CREATOR,
    ERROR_CALLED_FROM_STATE_RETIRED,
    ERROR_NO_MEMORY_FOR_MORE_DELEGATORS,
    ERROR_THERE_CAN_BE_AT_LEAST_ONE_DELEGATOR,
    MAXIMUM_NUMBER_OF_DELEGATOR_CONTRACTS_PER_VALIDATOR_AD,
    MAXIMUM_NUMBER_OF_DELEGATORS_PER_NODE,
)
from smart_contracts.noticeboard.constants import (
    STATE_SET,
)
from tests.constants import ERROR_GLOBAL_STATE_MISMATCH, SKIP_SAME_AS_FOR_ALGO
from tests.noticeboard.utils import POSSIBLE_STATES, Noticeboard, get_template_del_bin, get_template_val_bin
from tests.utils import is_expected_logic_error

from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "DEPLOYED"
TEST_ACTION_NAME = "noticeboard_set"

# ------- Tests -------
def test_action(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    # Note: Platform manager is the creator
    # Load validator ad
    action_inputs.template_name = BOX_VALIDATOR_AD_TEMPLATE_KEY
    action_inputs.template = get_template_val_bin()
    action_inputs.template_size = len(action_inputs.template)
    noticeboard.noticeboard_action(action_name="template_load_init", action_inputs=action_inputs)
    noticeboard.noticeboard_action(action_name="template_load_data", action_inputs=action_inputs)
    assert noticeboard.app_box(BOX_VALIDATOR_AD_TEMPLATE_KEY) == [action_inputs.template, True,]
    # Load delegator ad
    action_inputs.template_name = BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY
    action_inputs.template = get_template_del_bin()
    action_inputs.template_size = len(action_inputs.template)
    noticeboard.noticeboard_action(action_name="template_load_init", action_inputs=action_inputs)
    noticeboard.noticeboard_action(action_name="template_load_data", action_inputs=action_inputs)
    assert noticeboard.app_box(BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY) == [action_inputs.template, True,]

    # Prepare settings for the noticeboard
    action_inputs.pla_manager = noticeboard.pla_manager.address
    action_inputs.asset_config_manager = noticeboard.asset_config_manager.address
    action_inputs.tc_sha256 = bytes([0xDD] * 32)
    action_inputs.noticeboard_fees = NoticeboardFees(
        commission_min = 661_087,
        val_user_reg=51_021,
        del_user_reg=54_321,
        val_ad_creation=199_999_999,
        del_contract_creation=1_111_111,
    )
    action_inputs.noticeboard_terms_timing = NoticeboardTermsTiming(
        rounds_duration_min_min = 3,
        rounds_duration_max_max = 4_000_000,
        before_expiry = 403_200,
        report_period = 28_800,
    )
    action_inputs.noticeboard_terms_node = NoticeboardTermsNodeLimits(
        stake_max_max = 10**(7+6),
        stake_max_min = 3*10**(3+6),
        cnt_del_max_max = MAXIMUM_NUMBER_OF_DELEGATORS_PER_NODE,
    )

    gs_start = noticeboard.get_global_state()

    # Action
    res = noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    assert res.confirmed_round

    # Check contract state
    gs_exp = gs_start
    gs_exp.state = STATE_SET
    gs_exp.pla_manager = action_inputs.pla_manager
    gs_exp.asset_config_manager = action_inputs.asset_config_manager
    gs_exp.tc_sha256 = action_inputs.tc_sha256
    gs_exp.noticeboard_fees = action_inputs.noticeboard_fees
    gs_exp.noticeboard_terms_timing = action_inputs.noticeboard_terms_timing
    gs_exp.noticeboard_terms_node = action_inputs.noticeboard_terms_node
    gs_end = noticeboard.get_global_state()
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    return

def test_pla_change_twice(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    # Note: The creator is the platform manager
    # Load validator ad
    action_inputs.template_name = BOX_VALIDATOR_AD_TEMPLATE_KEY
    action_inputs.template = get_template_val_bin()
    action_inputs.template_size = len(action_inputs.template)
    noticeboard.noticeboard_action(action_name="template_load_init", action_inputs=action_inputs)
    noticeboard.noticeboard_action(action_name="template_load_data", action_inputs=action_inputs)
    assert noticeboard.app_box(BOX_VALIDATOR_AD_TEMPLATE_KEY) == [action_inputs.template, True,]
    # Load delegator ad
    action_inputs.template_name = BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY
    action_inputs.template = get_template_del_bin()
    action_inputs.template_size = len(action_inputs.template)
    noticeboard.noticeboard_action(action_name="template_load_init", action_inputs=action_inputs)
    noticeboard.noticeboard_action(action_name="template_load_data", action_inputs=action_inputs)
    assert noticeboard.app_box(BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY) == [action_inputs.template, True,]

    # Change platform manager - issued by the creator
    action_inputs.pla_manager = noticeboard.pla_manager.address
    noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    gs_start = noticeboard.get_global_state()

    # Action
    res = noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    assert res.confirmed_round

    # Check contract state
    gs_exp = gs_start
    gs_exp.pla_manager = action_inputs.pla_manager
    gs_end = noticeboard.get_global_state()
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    return

def test_wrong_cnt_del_max_max(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    # Note: Platform manager is the creator
    # Load validator ad
    action_inputs.template_name = BOX_VALIDATOR_AD_TEMPLATE_KEY
    action_inputs.template = get_template_val_bin()
    action_inputs.template_size = len(action_inputs.template)
    noticeboard.noticeboard_action(action_name="template_load_init", action_inputs=action_inputs)
    noticeboard.noticeboard_action(action_name="template_load_data", action_inputs=action_inputs)
    assert noticeboard.app_box(BOX_VALIDATOR_AD_TEMPLATE_KEY) == [action_inputs.template, True,]
    # Load delegator ad
    action_inputs.template_name = BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY
    action_inputs.template = get_template_del_bin()
    action_inputs.template_size = len(action_inputs.template)
    noticeboard.noticeboard_action(action_name="template_load_init", action_inputs=action_inputs)
    noticeboard.noticeboard_action(action_name="template_load_data", action_inputs=action_inputs)
    assert noticeboard.app_box(BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY) == [action_inputs.template, True,]

    # Action fail
    with pytest.raises(LogicError) as e:
        # Increase limit above maximum allowed due to memory constraints
        ai_tmp = copy.deepcopy(action_inputs)
        ai_tmp.noticeboard_terms_node.cnt_del_max_max = MAXIMUM_NUMBER_OF_DELEGATOR_CONTRACTS_PER_VALIDATOR_AD + 1
        noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=ai_tmp)

    assert is_expected_logic_error(ERROR_NO_MEMORY_FOR_MORE_DELEGATORS, e)

    # Action fail
    with pytest.raises(LogicError) as e:
        # Set limit to 0
        ai_tmp = copy.deepcopy(action_inputs)
        ai_tmp.noticeboard_terms_node.cnt_del_max_max = 0
        noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=ai_tmp)

    assert is_expected_logic_error(ERROR_THERE_CAN_BE_AT_LEAST_ONE_DELEGATOR, e)

    return

def test_wrong_pla_manager(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    # Note: Platform manager is the creator
    # Load validator ad
    action_inputs.template_name = BOX_VALIDATOR_AD_TEMPLATE_KEY
    action_inputs.template = get_template_val_bin()
    action_inputs.template_size = len(action_inputs.template)
    noticeboard.noticeboard_action(action_name="template_load_init", action_inputs=action_inputs)
    noticeboard.noticeboard_action(action_name="template_load_data", action_inputs=action_inputs)
    assert noticeboard.app_box(BOX_VALIDATOR_AD_TEMPLATE_KEY) == [action_inputs.template, True,]
    # Load delegator ad
    action_inputs.template_name = BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY
    action_inputs.template = get_template_del_bin()
    action_inputs.template_size = len(action_inputs.template)
    noticeboard.noticeboard_action(action_name="template_load_init", action_inputs=action_inputs)
    noticeboard.noticeboard_action(action_name="template_load_data", action_inputs=action_inputs)
    assert noticeboard.app_box(BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY) == [action_inputs.template, True,]

    # Action fail
    with pytest.raises(LogicError) as e:
        # Switch sender not to be the platform manager
        noticeboard.noticeboard_action(
            action_name=TEST_ACTION_NAME,
            action_inputs=action_inputs,
            action_account=noticeboard.dispenser,
        )

    assert is_expected_logic_error(ERROR_CALLED_BY_NOT_PLA_MANAGER_OR_CREATOR, e)

    return

def test_unsuspend(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state="SUSPENDED", action_inputs=action_inputs)

    gs_start = noticeboard.get_global_state()

    # Action
    res = noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    assert res.confirmed_round

    # Check contract state
    gs_exp = gs_start
    gs_exp.state = STATE_SET
    gs_end = noticeboard.get_global_state()
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    return

@pytest.mark.parametrize("init_state", [
    "DEPLOYED",
    "SET",
    "SUSPENDED",
    "RETIRED",
])
def test_state(
    noticeboard: Noticeboard,
    asset : int,
    init_state : POSSIBLE_STATES,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=init_state, action_inputs=action_inputs)

    if init_state != "RETIRED":
        # Action success
        res = noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
        assert res.confirmed_round

        # Check new state
        exp_state = STATE_SET
        gs_end = noticeboard.get_global_state()
        assert gs_end.state == exp_state
    else:
        # Action fail
        with pytest.raises(LogicError) as e:
            noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
        assert is_expected_logic_error(ERROR_CALLED_FROM_STATE_RETIRED, e)

    return
