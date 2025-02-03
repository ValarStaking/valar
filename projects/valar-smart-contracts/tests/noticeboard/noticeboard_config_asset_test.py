
import pytest
from algokit_utils.logic_error import LogicError

from smart_contracts.artifacts.noticeboard.client import NoticeboardAssetInfo
from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_CALLED_BY_NOT_PLA_MANAGER_OR_ASSET_CONFIG_MANAGER,
    ERROR_CALLED_FROM_STATE_RETIRED,
    ERROR_MBR_INCREASE_NOT_PAID,
    ERROR_RECEIVER,
)
from tests.constants import (
    ERROR_GLOBAL_STATE_MISMATCH,
    ERROR_MBR_INCORRECTLY_SPENT,
    SKIP_SAME_AS_FOR_ALGO,
)
from tests.noticeboard.utils import POSSIBLE_STATES, Noticeboard
from tests.utils import is_expected_logic_error

from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "DEPLOYED"
TEST_ACTION_NAME = "noticeboard_config_asset"

# ------- Tests -------
def test_action(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    # Ensure contract is opted-in the asset that will be added
    noticeboard.noticeboard_action(action_name="noticeboard_optin_asa", action_inputs=action_inputs)
    action_inputs.asset_info = NoticeboardAssetInfo(
        accepted=True,
        fee_round_min_min=10,
        fee_round_var_min=23,
        fee_setup_min=412_002,
    )

    gs_start = noticeboard.get_global_state()
    start_available_bal = noticeboard.app_available_balance(ALGO_ASA_ID)

    # Action
    res = noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    assert res.confirmed_round

    # Check contract state
    gs_exp = gs_start
    gs_end = noticeboard.get_global_state()
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check available balance
    end_available_bal = noticeboard.app_available_balance(ALGO_ASA_ID)
    assert end_available_bal == start_available_bal, ERROR_MBR_INCORRECTLY_SPENT

    # Check box
    asset_info = noticeboard.app_get_asset_info(asset)
    assert asset_info == action_inputs.asset_info, "Asset is incorrectly configured."

    return

def test_action_w_asset_config_manager(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    # Setup
    action_inputs = ActionInputs(asset=asset, asset_config_manager=noticeboard.asset_config_manager.address)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    # Set noticeboard, including the asset_config_manager
    noticeboard.noticeboard_action(action_name="noticeboard_set", action_inputs=action_inputs)
    # Ensure contract is opted-in the asset that will be added
    noticeboard.noticeboard_action(action_name="noticeboard_optin_asa", action_inputs=action_inputs)
    action_inputs.asset_info = NoticeboardAssetInfo(
        accepted=True,
        fee_round_min_min=10,
        fee_round_var_min=23,
        fee_setup_min=412_002,
    )

    gs_start = noticeboard.get_global_state()
    start_available_bal = noticeboard.app_available_balance(ALGO_ASA_ID)

    # Action - done with asset config manager
    res = noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs, action_account=noticeboard.asset_config_manager)  # noqa: E501

    # Check return
    assert res.confirmed_round

    # Check the txn was sent by asset config manager
    assert res.tx_info["txn"]["txn"]["snd"] == action_inputs.asset_config_manager

    # Check contract state
    gs_exp = gs_start
    gs_end = noticeboard.get_global_state()
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check available balance
    end_available_bal = noticeboard.app_available_balance(ALGO_ASA_ID)
    assert end_available_bal == start_available_bal, ERROR_MBR_INCORRECTLY_SPENT

    # Check box
    asset_info = noticeboard.app_get_asset_info(asset)
    assert asset_info == action_inputs.asset_info, "Asset is incorrectly configured."

    return

def test_add_remove(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    # Ensure contract is opted-in the asset that will be added
    noticeboard.noticeboard_action(action_name="noticeboard_optin_asa", action_inputs=action_inputs)
    # Add it
    action_inputs.asset_info = NoticeboardAssetInfo(
        accepted=True,
        fee_round_min_min=10,
        fee_round_var_min=23,
        fee_setup_min=412_002,
    )
    noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
    # Remove it
    action_inputs.asset_info.accepted = False
    # To remove it a 2nd time, there is no fee because the box was already created
    action_inputs.amount = 0

    gs_start = noticeboard.get_global_state()
    start_available_bal = noticeboard.app_available_balance(ALGO_ASA_ID)

    # Action
    res = noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    # Check return
    assert res.confirmed_round

    # Check contract state
    gs_exp = gs_start
    gs_end = noticeboard.get_global_state()
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # Check available balance
    end_available_bal = noticeboard.app_available_balance(ALGO_ASA_ID)
    assert end_available_bal == start_available_bal, ERROR_MBR_INCORRECTLY_SPENT

    # Check box
    asset_info = noticeboard.app_get_asset_info(asset)
    assert asset_info == action_inputs.asset_info, "Asset is not disabled."

    return

def test_wrong_receiver(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.receiver = noticeboard.dispenser.address
        noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_RECEIVER, e)

    return

def test_mbr_increase_not_paid(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.amount = 0
        noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_MBR_INCREASE_NOT_PAID, e)

    return

def test_wrong_account(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Action fail
    with pytest.raises(LogicError) as e:
        # Switch sender not to be the platform manager or asset config manager
        noticeboard.noticeboard_action(
            action_name=TEST_ACTION_NAME,
            action_inputs=action_inputs,
            action_account=noticeboard.dispenser,
        )

    assert is_expected_logic_error(ERROR_CALLED_BY_NOT_PLA_MANAGER_OR_ASSET_CONFIG_MANAGER, e)

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
        gs_start = noticeboard.get_global_state()

        # Action success
        res = noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
        assert res.confirmed_round

        # Check new state - should not change
        exp_state = gs_start.state
        gs_end = noticeboard.get_global_state()
        assert gs_end.state == exp_state
    else:
        # Action fail
        with pytest.raises(LogicError) as e:
            noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)
        assert is_expected_logic_error(ERROR_CALLED_FROM_STATE_RETIRED, e)

    return
