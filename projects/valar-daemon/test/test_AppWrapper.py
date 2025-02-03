"""Test the app wrappers and app wrapper lists for valads and delcos.

Notes
-----
The inherited `...AppWrapper` methods are tested through `ValadAppWrapperList` and are skipped for delcos.
The wrappers should be independent of app state (just the client is connected), so tests don't have to be exhaustive.
"""
# import sys
import pytest
import logging
# from pathlib import Path
from typing import Callable

from algokit_utils.beta.algorand_client import AlgorandClient
from algosdk.error import AlgodHTTPError 

from valar_daemon.ValidatorAdClient import ValidatorAdClient
from valar_daemon.DelegatorContractClient import DelegatorContractClient
from valar_daemon.NoticeboardClient import NoticeboardClient
from valar_daemon.AppWrapper import (
    AppWrapper,
    ValadAppWrapper,
    DelcoAppWrapper,
    ValadAppWrapperList,
    DelcoAppWrapperList
)
from valar_daemon.constants import (
    VALAD_STATE_NOT_READY, 
    VALAD_STATE_READY,
    DELCO_STATE_READY,
    DELCO_STATE_ENDED_EXPIRED,
    VALAD_STATE_DELETED_MASK
)
from test.utils import (
    translate_valad_state_to_noticeboard_util_class_action,
    translate_delco_state_to_noticeboard_util_class_action
)

# sys.path.insert(0, str(Path(*Path(__file__).parent.parts[:-2], 'valar-smart-contracts')))
from tests.noticeboard.utils import Noticeboard
from tests.noticeboard.config import ActionInputs


@pytest.fixture
def valad_id(
    noticeboard: object,
    action_inputs: object,
    valad_state: str
):
    """Generate valad and get its ID.

    Parameters
    ----------
    noticeboard : object
        Noticeboard handler from smart contract testers.
    action_inputs : object
        Action inputs for noticeboard handler.
    state : str, optional
        Desired valad state. By default 'READY'

    Returns
    -------
    int
    """
    valad_action = translate_valad_state_to_noticeboard_util_class_action(valad_state)
    return noticeboard.initialize_validator_ad_state(
        action_inputs=action_inputs,
        target_state=valad_action
    )


@pytest.fixture
def valad_id_generator(
        valad_id: Callable[[object, object, str], int]
    ) -> Callable[[], int]:
    """Generate valad on demand.

    Parameters
    ----------
    valad_id : int

    Returns
    -------
    Callable[[], int]
    """
    def _valad_id():
        return valad_id
    return _valad_id
    

@pytest.fixture
def delco_id(
    noticeboard: object,
    action_inputs: object,
    valad_id: int,
    delco_state: str
) -> int:
    """Generate delco nad get its ID.

    Parameters
    ----------
    noticeboard : object
        Noticeboard handler from smart contract testers.
    action_inputs : object
        Action inputs for noticeboard handler.
    valad_id : int
        Valad ID.
    state : str, optional
        Desired delco state. By default 'READY'

    Returns
    -------
    int
    """
    delco_action = translate_delco_state_to_noticeboard_util_class_action(delco_state)
    return noticeboard.initialize_delegator_contract_state(
        action_inputs=action_inputs, 
        val_app_id=valad_id,
        target_state=delco_action
    )


def test_app_wrapper_initialization():
    """Test initializing app wrapper.
    """
    assert AppWrapper()


@pytest.mark.parametrize(
    "algo_fee_asset, valad_state, delben_equal_delman", 
    [
        (True, VALAD_STATE_READY, False),
        # (VALAD_STATE_READY, True),
        # (VALAD_STATE_NOT_READY, False),
        # (VALAD_STATE_NOT_READY, True),
    ]
)
def test_valad_app_wrapper_initialization(
        algorand_client: AlgorandClient, 
        valad_id: int,
    ):
    """Test initializing valad app wrapper.

    Parameters
    ----------
    algorand_client : AlgorandClient
    valad_id : int
    """
    wrapper = ValadAppWrapper(algorand_client, valad_id)
    assert wrapper.app_id == valad_id
    assert isinstance(wrapper.valad_client, ValidatorAdClient)
    assert isinstance(wrapper.notbd_client, NoticeboardClient)


# !PENDING! Enable changing from not ready to ready state (`noticeboard.validator_action`).
@pytest.mark.parametrize(
    "algo_fee_asset, valad_state, delben_equal_delman, delete_app, break_algod, propagate_deleted_error, expected_valad_state", 
    [
        (True, VALAD_STATE_READY,     False, True,  False, False, VALAD_STATE_DELETED_MASK),
        (True, VALAD_STATE_READY,     False, True,  False, True,  VALAD_STATE_DELETED_MASK),
        (True, VALAD_STATE_READY,     False, True,  True,  False, VALAD_STATE_DELETED_MASK),
        (True, VALAD_STATE_READY,     False, True,  True,  True,  VALAD_STATE_DELETED_MASK),
        # (True, VALAD_STATE_NOT_READY, False, False, False, False, VALAD_STATE_READY), # Pending
        # (True, VALAD_STATE_NOT_READY, False, True,  False, False, VALAD_STATE_READY), # Pending
        (True, VALAD_STATE_READY, False, False, False, False, VALAD_STATE_READY), # Useless placeholder
        (True, VALAD_STATE_READY, False, True,  False, False, VALAD_STATE_READY)  # Useless placeholder
    ]
)
def test_valad_app_wrapper_update_dynamic(
        algorand_client: AlgorandClient, 
        valad_id: int,
        noticeboard: Noticeboard,
        action_inputs: ActionInputs,
        delete_app:bool,
        propagate_deleted_error: bool,
        break_algod: bool,
        expected_valad_state: bytes
    ):
    """Test fetching and deleted valad's state and updating the app wrapper's attributes.

    Parameters
    ----------
    algorand_client : AlgorandClient
        Algorand client.
    valad_id : int
        Validator ad ID.
    noticeboard : Noticeboard
        Noticeboard utility object.
    action_inputs : ActionInputs
        Action inputs utility object.
    delete_app : bool
        Flag if valad should be deleted after init, as part of the test.
    propagate_deleted_error : bool
        Flag if the deleted app error should propagate or be handled (update ad state to deleted).
    break_algod : bool
        Flag if algod connection should be broken.
    expected_valad_state : bytes
        Expected validator ad state.
    """
    wrapper = ValadAppWrapper(algorand_client, valad_id)
    if break_algod:     # URLError, disconnected or wrong URL for algod
        algorand_client.client.algod.algod_address = "https://some.cloud" # Wrong URL
        with pytest.raises(Exception):
            wrapper.update_dynamic(propagate_deleted_error=propagate_deleted_error)
    else:
        if delete_app:
            noticeboard.validator_action(
                app_id=valad_id,
                action_name="ad_delete",
                action_inputs=action_inputs
            )
            if propagate_deleted_error:
                with pytest.raises(AlgodHTTPError):
                    wrapper.update_dynamic(propagate_deleted_error=propagate_deleted_error)
            else:
                wrapper.update_dynamic(propagate_deleted_error=propagate_deleted_error)
                assert wrapper.state == VALAD_STATE_DELETED_MASK
        else:
            # noticeboard.validator_action(
            #     app_id=valad_id,
            #     action_name="ad_ready",
            #     action_inputs=action_inputs
            # )
            wrapper.update_dynamic(propagate_deleted_error=propagate_deleted_error)
            assert wrapper.state == expected_valad_state


def test_valad_app_wrapper_list_initialization(
        algorand_client: AlgorandClient,
        logger_mockup: logging.Logger
    ):
    """Test initializing valad app wrapper list.

    Parameters
    ----------
    algorand_client : AlgorandClient
    logger_mockup : logging.Logger
    """
    valad_app_wrapper_list = ValadAppWrapperList(
        algorand_client=algorand_client, 
        logger=logger_mockup
    )
    assert len(valad_app_wrapper_list.get_app_list()) == 0


@pytest.mark.parametrize(
    "algo_fee_asset, valad_state, delben_equal_delman, break_algod, wrong_app_id", 
    [
        (True, VALAD_STATE_NOT_READY, True, False, False),
        (True, VALAD_STATE_NOT_READY, True, False, True),
        (True, VALAD_STATE_NOT_READY, True, True,  False),
        (True, VALAD_STATE_READY, True, False, False),
        (True, VALAD_STATE_READY, True, False, True),
        (True, VALAD_STATE_READY, True, True,  False),
    ]
)
def test_valad_app_wrapper_list_add_single_app(
        algorand_client: AlgorandClient,
        logger_mockup : logging.Logger,
        valad_id: int,
        break_algod: bool,
        wrong_app_id: bool
    ):
    """Test adding single valad app wrapper.

    Parameters
    ----------
    algorand_client : AlgorandClient
    logger_mockup : logging.Logger
    valad_id : int
    break_algod: bool
    wrong_app_id: bool
    """
    valad_app_wrapper_list = ValadAppWrapperList(
        algorand_client=algorand_client, 
        logger=logger_mockup
    )
    if break_algod:     # URLError, disconnected or wrong URL for algod
        algorand_client.client.algod.algod_address = "https://some.cloud" # Wrong URL
        expected_num_of_apps = 0
        expected_id_list = []
    elif wrong_app_id:  # Algo internal error, wrong ID
        valad_id += 1 # Wrong ID
        expected_num_of_apps = 0
        expected_id_list = []
    else:
        expected_num_of_apps = 1
        expected_id_list = [valad_id]
    res = valad_app_wrapper_list.add_single_app(valad_id+int(wrong_app_id))
    assert res == expected_num_of_apps
    assert len(valad_app_wrapper_list.get_app_list()) == expected_num_of_apps
    assert valad_app_wrapper_list.get_id_list() == expected_id_list


@pytest.mark.parametrize(
    "algo_fee_asset, valad_state, delben_equal_delman", 
    [
        (True, VALAD_STATE_READY, False),
        # (VALAD_STATE_READY, True),
        # (VALAD_STATE_NOT_READY, False),
        # (VALAD_STATE_NOT_READY, True),
    ]
)
def test_valad_app_wrapper_list_remove_single_app(
        algorand_client: AlgorandClient,
        logger_mockup : logging.Logger,
        valad_id: int
    ):
    """Test removing single valad app wrapper.

    Parameters
    ----------
    algorand_client : AlgorandClient
    valad_id : int
    """
    valad_app_wrapper_list = ValadAppWrapperList(
        algorand_client=algorand_client, 
        logger=logger_mockup
    )
    valad_app_wrapper_list.add_single_app(valad_id)
    # Remove existing
    assert valad_app_wrapper_list.remove_single_app(valad_id)
    assert len(valad_app_wrapper_list.get_app_list()) == 0
    # Can't remove non-existent
    assert not valad_app_wrapper_list.remove_single_app(valad_id)


@pytest.mark.parametrize(
    "algo_fee_asset, valad_state, delben_equal_delman, break_algod, wrong_app_id", 
    [
        (True, VALAD_STATE_NOT_READY, True, False, False),
        (True, VALAD_STATE_NOT_READY, True, False, True),
        (True, VALAD_STATE_NOT_READY, True, True,  False),
        (True, VALAD_STATE_READY, True, False, False),
        (True, VALAD_STATE_READY, True, False, True),
        (True, VALAD_STATE_READY, True, True,  False),
    ]
)
def test_valad_app_wrapper_list_add_multiple_apps(
        algorand_client: AlgorandClient,
        logger_mockup : logging.Logger,
        valad_id_generator: Callable[[], int],
        break_algod: bool,
        wrong_app_id: bool
    ):
    """Test adding multiple valad app wrapper.

    Parameters
    ----------
    algorand_client : AlgorandClient
    logger_mockup : logging.Logger
    valad_id_generator : Callable[[], int]
    break_algod : bool
    wrong_app_id : bool
    """
    valad_id_list = [valad_id_generator() for i in range(3)]
    valad_app_wrapper_list = ValadAppWrapperList(
        algorand_client=algorand_client, 
        logger=logger_mockup
    )
    if break_algod:     # URLError, disconnected or wrong URL for algod
        algorand_client.client.algod.algod_address = "https://some.cloud" # Wrong URL
        expected_num_of_apps = 0
        expected_id_list = []
    elif wrong_app_id:  # Algo internal error, wrong ID
        valad_id_list[-1] += 1 # Wrong ID
        expected_num_of_apps = len(valad_id_list) - 1
        expected_id_list = valad_id_list[:-1]
    else:
        expected_num_of_apps = len(valad_id_list)
        expected_id_list = valad_id_list
    res = valad_app_wrapper_list.add_multiple_apps(valad_id_list)
    assert res == expected_num_of_apps
    assert len(valad_app_wrapper_list.get_app_list()) == expected_num_of_apps
    assert valad_app_wrapper_list.get_id_list() == expected_id_list


@pytest.mark.parametrize(
    "algo_fee_asset, valad_state, delben_equal_delman, break_algod", 
    [
        (True, VALAD_STATE_READY, True, False),
        (True, VALAD_STATE_READY, True, True),
    ]
)
def test_valad_app_wrapper_list_update_apps(
        algorand_client: AlgorandClient,
        logger_mockup : logging.Logger,
        valad_id_generator: Callable[[], int],
        break_algod: bool
    ):
    """Test updating multiple valad app wrappers.

    Parameters
    ----------
    algorand_client : AlgorandClient
    logger_mockup : logging.Logger
    valad_id_generator : Callable[[], int]
    break_algod : bool
    """
    valad_id_list = [valad_id_generator() for i in range(3)]
    valad_app_wrapper_list = ValadAppWrapperList(
        algorand_client=algorand_client, 
        logger=logger_mockup
    )
    valad_app_wrapper_list.add_multiple_apps(valad_id_list)
    if break_algod:     # URLError, disconnected or wrong URL for algod
        algorand_client.client.algod.algod_address = "https://some.cloud" # Wrong URL
        expected_num_of_updated = 0
    else:
        expected_num_of_updated = len(valad_app_wrapper_list.get_app_list())
    num_of_apps, num_of_updated = valad_app_wrapper_list.update_apps()
    assert num_of_apps == len(valad_id_list)
    assert num_of_updated == expected_num_of_updated


@pytest.mark.parametrize(
    "algo_fee_asset, valad_state, delben_equal_delman", 
    [
        (True, VALAD_STATE_READY, False),
        # (VALAD_STATE_READY, True),
        # (VALAD_STATE_NOT_READY, False),
        # (VALAD_STATE_NOT_READY, True),
    ]
)
def test_valad_app_wrapper_list_remove_multiple_apps(
        algorand_client: AlgorandClient,
        logger_mockup : logging.Logger,
        valad_id_generator: Callable[[], int]
    ):
    """Test removing multiple valad apps wrapper.

    Parameters
    ----------
    algorand_client : AlgorandClient
    logger_mockup : logging.Logger
    valad_id_generator : Callable[[], int]
    """
    # Fill up and check
    num_of_valads = 5
    valad_id_list = [valad_id_generator() for i in range(num_of_valads)]
    valad_app_wrapper_list = ValadAppWrapperList(
        algorand_client=algorand_client, 
        logger=logger_mockup
    )
    valad_app_wrapper_list.add_multiple_apps(valad_id_list)
    assert len(valad_app_wrapper_list.get_app_list()) == len(valad_id_list)
    assert valad_app_wrapper_list.get_id_list() == valad_id_list
    # Remove first two
    valad_app_wrapper_list.remove_multiple_apps(valad_id_list[:2])
    valad_id_list = valad_id_list[2:]
    assert len(valad_app_wrapper_list.get_app_list()) == len(valad_id_list)
    assert valad_app_wrapper_list.get_id_list() == valad_id_list
    # Remove remaining
    valad_app_wrapper_list.remove_multiple_apps(valad_id_list)
    assert len(valad_app_wrapper_list.get_app_list()) == 0


@pytest.mark.parametrize(
    "algo_fee_asset, valad_state, delco_state, delben_equal_delman", 
    [
        (True, VALAD_STATE_READY, DELCO_STATE_READY, True),
        # (VALAD_STATE_READY, DELCO_STATE_READY, True),
        # (VALAD_STATE_READY, DELCO_STATE_SUBMITTED, False),
        # (VALAD_STATE_READY, DELCO_STATE_SUBMITTED, True),
        # (VALAD_STATE_READY, DELCO_STATE_LIVE, False),
        # (VALAD_STATE_READY, DELCO_STATE_LIVE, True),
    ]
)
def test_delco_app_wrapper_initialization(
        algorand_client: AlgorandClient, 
        delco_id: int,
    ):
    """Test initializing delco app wrapper.

    Parameters
    ----------
    algorand_client : AlgorandClient
    delco_id : int
    """
    wrapper = DelcoAppWrapper(algorand_client, delco_id)
    assert wrapper.app_id == delco_id
    assert isinstance(wrapper.delco_client, DelegatorContractClient)
    assert isinstance(wrapper.notbd_client, NoticeboardClient)


@pytest.mark.parametrize(
    "algo_fee_asset, valad_state, delben_equal_delman, delco_state, propagate_deleted_error", 
    [
        (True, VALAD_STATE_READY, True, DELCO_STATE_ENDED_EXPIRED, False),
        (True, VALAD_STATE_READY, True, DELCO_STATE_ENDED_EXPIRED, True),
    ]
)
def test_delco_app_deleted_state(
        algorand_client: AlgorandClient, 
        delco_id: int,
        noticeboard: Noticeboard,
        action_inputs: ActionInputs,
        propagate_deleted_error: bool
    ):
    """Test fetching and deleted valad's state and updating the app wrapper's attributes.

    Parameters
    ----------
    algorand_client : AlgorandClient
    valad_id : int
    noticeboard : Noticeboard
    action_inputs : ActionInputs
    propagate_deleted_error : bool
    """
    wrapper = DelcoAppWrapper(algorand_client, delco_id)
    noticeboard.delegator_action(
        app_id=delco_id,
        action_name="contract_delete",
        action_inputs=action_inputs
    )
    if propagate_deleted_error:
        with pytest.raises(AlgodHTTPError):
            wrapper.update_dynamic(propagate_deleted_error=propagate_deleted_error)
    else:
        wrapper.update_dynamic(propagate_deleted_error=propagate_deleted_error)
        assert wrapper.state == VALAD_STATE_DELETED_MASK


def test_delco_app_wrapper_list_initialization(
        algorand_client: AlgorandClient,
        logger_mockup: logging.Logger
    ):
    """Test initializing delco app wrapper list.

    Parameters
    ----------
    algorand_client : AlgorandClient
    logger_mockup : logging.Logger
    """
    delco_app_wrapper_list = DelcoAppWrapperList(
        algorand_client=algorand_client, 
        logger=logger_mockup
    )
    assert len(delco_app_wrapper_list.get_app_list()) == 0


@pytest.mark.parametrize(
    "algo_fee_asset, valad_state, delco_state, delben_equal_delman", 
    [
        (True, VALAD_STATE_READY, DELCO_STATE_READY, True),
        # (VALAD_STATE_READY, DELCO_STATE_READY, True),
        # (VALAD_STATE_READY, DELCO_STATE_SUBMITTED, False),
        # (VALAD_STATE_READY, DELCO_STATE_SUBMITTED, True),
        # (VALAD_STATE_READY, DELCO_STATE_LIVE, False),
        # (VALAD_STATE_READY, DELCO_STATE_LIVE, True),
    ]
    )
def test_delco_app_wrapper_list_add_single_app(
        algorand_client: AlgorandClient,
        logger_mockup: logging.Logger,
        delco_id: int
    ):
    """Test adding single delco app wrapper.

    Parameters
    ----------
    algorand_client : AlgorandClient
    logger_mockup : logging.Logger
    delco_id : int
    """
    delco_app_wrapper_list = DelcoAppWrapperList(
        algorand_client=algorand_client, 
        logger=logger_mockup
    )
    delco_app_wrapper_list.add_single_app(delco_id)
    assert len(delco_app_wrapper_list.get_app_list()) == 1
    assert delco_app_wrapper_list.get_id_list() == [delco_id]


@pytest.mark.parametrize(
    "algo_fee_asset, valad_state, delco_state, delben_equal_delman", 
    [
        (True, VALAD_STATE_READY, DELCO_STATE_READY, True)
    ]
    )
def test_delco_app_wrapper_get_partkey_params(
        algorand_client: AlgorandClient,
        delco_id: int
    ):
    """Test fetching partkey parameters from delco wrapper.

    Parameters
    ----------
    algorand_client : AlgorandClient
    delco_id : int
    """
    app_wrapper = DelcoAppWrapper(algorand_client, delco_id)
    params = app_wrapper.get_partkey_params()
    assert app_wrapper.delben_address == params['address']
    assert app_wrapper.round_start == params['vote-first-valid']
    assert app_wrapper.round_end == params['vote-last-valid']


@pytest.mark.parametrize(
    "algo_fee_asset, valad_state, delco_state, delben_equal_delman", 
    [
        (True, VALAD_STATE_READY, DELCO_STATE_READY, True)
    ]
    )
def test_delco_app_wrapper_list_get_partkey_params(
        algorand_client: AlgorandClient,
        logger_mockup: logging.Logger,
        delco_id: int
    ):
    """Test fetching partkey parameters from delco wrapper list.

    Parameters
    ----------
    algorand_client : AlgorandClient
    logger_mockup : logging.Logger
    delco_id : int
    """
    # Populate list
    delco_app_wrapper_list = DelcoAppWrapperList(
        algorand_client=algorand_client, 
        logger=logger_mockup
    )
    # Get app and params from app list (see if it exposes the params)
    delco_app_wrapper_list.add_single_app(delco_id)
    app_wrapper = delco_app_wrapper_list.get_app_list()[0]
    params = delco_app_wrapper_list.get_partkey_params_list()[0]
    # Evaluate correctness
    assert app_wrapper.delben_address == params['address']
    assert app_wrapper.round_start == params['vote-first-valid']
    assert app_wrapper.round_end == params['vote-last-valid']
