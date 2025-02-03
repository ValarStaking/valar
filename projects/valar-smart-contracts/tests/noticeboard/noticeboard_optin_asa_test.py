
import pytest
from algokit_utils.logic_error import LogicError

from smart_contracts.helpers.constants import (
    ALGO_ASA_ID,
    ERROR_AMOUNT_ASA_OPTIN_MBR,
    ERROR_CALLED_BY_NOT_PLA_MANAGER_OR_ASSET_CONFIG_MANAGER,
    ERROR_RECEIVER,
)
from tests.constants import (
    ERROR_GLOBAL_STATE_MISMATCH,
    ERROR_MBR_INCORRECTLY_SPENT,
    SKIP_NOT_APPLICABLE_TO_ALGO,
)
from tests.noticeboard.utils import Noticeboard
from tests.utils import is_expected_logic_error

from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "DEPLOYED"
TEST_ACTION_NAME = "noticeboard_optin_asa"

# ------- Tests -------
def test_action(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_NOT_APPLICABLE_TO_ALGO) if asset == ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
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

    # If asset ID is not zero (i.e. ALGO), check if contract opted-in to it
    if asset != ALGO_ASA_ID:
        assert noticeboard.app_is_opted_in(asset)

    # Check available balance
    end_available_bal = noticeboard.app_available_balance(ALGO_ASA_ID)
    assert end_available_bal == start_available_bal, ERROR_MBR_INCORRECTLY_SPENT

    return

def test_action_w_asset_config_manager(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_NOT_APPLICABLE_TO_ALGO) if asset == ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset, asset_config_manager=noticeboard.asset_config_manager.address)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)
    # Set noticeboard, including the asset_config_manager
    noticeboard.noticeboard_action(action_name="noticeboard_set", action_inputs=action_inputs)
    gs_start = noticeboard.get_global_state()
    start_available_bal = noticeboard.app_available_balance(ALGO_ASA_ID)

    # Action
    res = noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs, action_account=noticeboard.asset_config_manager)  # noqa: E501

    # Check return
    assert res.confirmed_round

    # Check the txn was sent by asset config manager
    assert res.tx_info["txn"]["txn"]["snd"] == action_inputs.asset_config_manager

    # Check contract state
    gs_exp = gs_start
    gs_end = noticeboard.get_global_state()
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    # If asset ID is not zero (i.e. ALGO), check if contract opted-in to it
    if asset != ALGO_ASA_ID:
        assert noticeboard.app_is_opted_in(asset)

    # Check available balance
    end_available_bal = noticeboard.app_available_balance(ALGO_ASA_ID)
    assert end_available_bal == start_available_bal, ERROR_MBR_INCORRECTLY_SPENT

    return

def test_wrong_receiver(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_NOT_APPLICABLE_TO_ALGO) if asset == ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.receiver = noticeboard.dispenser.address
        noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_RECEIVER, e)

    return

def test_wrong_amount(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_NOT_APPLICABLE_TO_ALGO) if asset == ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Action fail
    with pytest.raises(LogicError) as e:
        action_inputs.amount = 111
        noticeboard.noticeboard_action(action_name=TEST_ACTION_NAME, action_inputs=action_inputs)

    assert is_expected_logic_error(ERROR_AMOUNT_ASA_OPTIN_MBR, e)

    return

def test_wrong_account(
    noticeboard: Noticeboard,
    asset : int,
) -> None:

    pytest.skip(SKIP_NOT_APPLICABLE_TO_ALGO) if asset == ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs(asset=asset)
    noticeboard.initialize_state(target_state=TEST_INITIAL_STATE, action_inputs=action_inputs)

    # Action fail
    with pytest.raises(LogicError) as e:
        # Switch sender not to be the platform manager
        noticeboard.noticeboard_action(
            action_name=TEST_ACTION_NAME,
            action_inputs=action_inputs,
            action_account=noticeboard.dispenser,
        )

    assert is_expected_logic_error(ERROR_CALLED_BY_NOT_PLA_MANAGER_OR_ASSET_CONFIG_MANAGER, e)

    return
