import pytest

from smart_contracts.helpers.constants import ALGO_ASA_ID
from smart_contracts.noticeboard.constants import (
    STATE_DEPLOYED,
)
from tests.constants import ERROR_GLOBAL_STATE_MISMATCH, SKIP_SAME_AS_FOR_ALGO
from tests.noticeboard.client_helper import (
    DEFAULT_DLL,
    DEFAULT_NOTICEBOARD_FEES,
    DEFAULT_SETUP_NOTICEBOARD_TERMS_STAKE,
    DEFAULT_SETUP_NOTICEBOARD_TERMS_TIMING,
    NoticeboardGlobalState,
)
from tests.noticeboard.utils import Noticeboard

from .config import ActionInputs

# ------- Test constants -------
TEST_INITIAL_STATE = "START"
TEST_ACTION_NAME = "noticeboard_deploy"


# ------- Tests -------
def test_action(
    noticeboard: Noticeboard,
    asset: int,
) -> None:

    pytest.skip(SKIP_SAME_AS_FOR_ALGO) if asset != ALGO_ASA_ID else None

    # Setup
    action_inputs = ActionInputs()
    action_inputs.app_id_old = 333_333

    action_account = noticeboard.creator # Explicitly define that the call is executed by creator account.

    # Action
    res = noticeboard.noticeboard_action(
        action_name=TEST_ACTION_NAME,
        action_inputs=action_inputs,
        action_account=action_account
    )

    # Check return
    assert res.return_value != 0, "App was not created."

    # Check contract state
    gs_exp = NoticeboardGlobalState(
        pla_manager=action_account.address,
        asset_config_manager=action_account.address,
        tc_sha256=bytes([0x00] * 32),
        noticeboard_fees=DEFAULT_NOTICEBOARD_FEES,
        noticeboard_terms_timing=DEFAULT_SETUP_NOTICEBOARD_TERMS_TIMING,
        noticeboard_terms_node=DEFAULT_SETUP_NOTICEBOARD_TERMS_STAKE,
        state=STATE_DEPLOYED,
        app_id_new=0,
        app_id_old=action_inputs.app_id_old,
        dll_del=DEFAULT_DLL,
        dll_val=DEFAULT_DLL,
    )
    gs_end = noticeboard.get_global_state()
    assert gs_end == gs_exp, ERROR_GLOBAL_STATE_MISMATCH

    return
