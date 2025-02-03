"""Test full journeys, to check if the daemon correctly services delcos from start to finish.

Notes
-----
- Tests fail when run in a bundle, but success when run independently.
"""
import copy
import yaml
import time
import pytest
from pathlib import Path
from typing import List, Tuple

from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.account_manager import AddressAndSigner

from test.test_journey.DelcoChecker import DelcoChecker
from test.test_journey.DelcoOrchestrator import DelcoOrchestrator
from test.test_journey.NodeOrchestrator import NodeOrchestrator
from test.utils import LocalnetRoundProgressor
from tests.noticeboard.utils import Noticeboard
from tests.noticeboard.config import ActionInputs

from valar_daemon.constants import (
    DELCO_STATE_READY,
    DELCO_STATE_SUBMITTED,
    DELCO_STATE_LIVE,
    DELCO_STATE_ENDED_NOT_CONFIRMED,
    DELCO_STATE_ENDED_EXPIRED,
    DELCO_STATE_ENDED_NOT_SUBMITTED,
    DELCO_STATE_ENDED_WITHDREW
)
from valar_daemon.AppWrapper import ValadAppWrapper


### Helpers ############################################################################################################

def load_test_configs(
    journey_templates_path: Path=None,
    parameters_path: Path=None, 
) -> List[List]:
    """Load test configs / parameters and resolve data references.

    Parameters
    ----------
    journey_templates_file : Path, optional
        Path to the journey templates, by default None
    parameters_file : Path, optional
        Path to the test parameters / config, by default None

    Returns
    -------
    List[List]
        Multiple test configs for: Delco actions, delco states, and node actions.
    """

    # Load the journey templates
    if journey_templates_path is None:
        journey_templates_path = Path(Path(__file__).parent, "journey_templates.yaml")
    with journey_templates_path.open("r") as f:
        journey_templates =  yaml.safe_load(f)

    # Load the test configurations / parameters
    if parameters_path is None:
        parameters_path = Path(Path(__file__).parent, "parameters.yaml")
    with parameters_path.open("r") as f:
        parameters = yaml.safe_load(f)

    # Resolve references to centralized data
    resolved_config_list = []
    for config in parameters:
        # Populate delco actions from templates
        delco_actions = [
            journey_templates["delco_actions"][actions_template] for actions_template in config["delco_actions"]
        ]
        # Populate delco states from templates - convert state names to their corresponding masks
        delco_states = []
        for states_template in config["delco_states"]:
            resolved_state_list = list()
            for state in journey_templates["delco_states"][states_template]:
                state_mask = eval(state) # COnvert
                resolved_state_list.append(state_mask)
            delco_states.append(resolved_state_list)
        # Populate node actions from templates
        actions_template = config["node_actions"]
        node_actions = journey_templates["node_actions"][actions_template]
        # Populate other parameters
        resolved_config_list.append([
            copy.deepcopy(delco_actions), # To avoid popping items for later tests
            copy.deepcopy(delco_states),
            copy.deepcopy(node_actions),
            config["valad_state"],
            config["timeout_s"],
            config["round_period_s"],
            config["delben_equal_delman"],
            config["algo_fee_asset"],
            # config["gating_asset_id"],
            # config["fee_asset_id"]
        ])

    return resolved_config_list


### Component definitions ##############################################################################################



### Test definitions ###################################################################################################

@pytest.mark.parametrize(
    "delco_actions, delco_states, node_actions, "
    "valad_state, timeout_s, round_period_s, delben_equal_delman, algo_fee_asset",
    load_test_configs()
)
def test_journey(
    algorand_client: AlgorandClient,
    delco_actions: List[List], 
    delco_states: List, 
    node_actions: List[List],
    valad_app_wrapper_and_valman: Tuple[ValadAppWrapper, AddressAndSigner],
    tmp_path: Path,
    noticeboard: Noticeboard,
    action_inputs: ActionInputs,
    timeout_s: int,
    round_period_s: int | float,
    algo_fee_asset: bool
):
    """Test an entire delegator journey, from non-existent contract to final state.

    Parameters
    ----------
    algorand_client : AlgorandClient
        [param] Algorand client.
    delco_actions : List[List]
        [param] Actions taken by the Delegator (new contract, withdraw,  etc.).
    delco_states : List
        [param] States traversed by Delegator Contract.
    node_actions : List[List]
        [param] Actions applied to the node (power on/off, internet on/off).
    valad_app_wrapper_and_valman : Callable
        [fixture] Validator ad app wrapper and validator manager.
    tmp_path : Path
        [fixture] Path to temporary test file storage.
    noticeboard : Noticeboard
        [fixture] Noticeboard utility instance.
    action_inputs : ActionInputs
        [fixture] Test inputs.
    timeout_s : int
        [param] Test timeout in seconds (maximal allowed duration).
    round_period_s : int | float
        [param] Period / duration of a single round in seconds.
    algo_fee_asset : bool
        [param] Flag whether to use ALGO as the fee asset. Not used here, but required - propagated to conftest.
    """
    
    get_round = lambda: algorand_client.client.algod.status()['last-round']
    
    valad_app, valman = valad_app_wrapper_and_valman
    print(f'Created validator ad with ID {valad_app.app_id} and state {valad_app.state}.')

    # Initialize delegator (contract) orchestrators with checkers
    delco_orc_list = []
    for actions, states in zip(delco_actions, delco_states):
        delco_orc_list.append(
            DelcoOrchestrator(
                actions=actions, 
                checker=DelcoChecker(states=states), 
                algorand_client=algorand_client,
                valad_id=valad_app.app_id,
                noticeboard=noticeboard,
                action_inputs=action_inputs
            )
        )

    # Initialize servicer
    node_orc = NodeOrchestrator(
        actions=node_actions,
        valman=valman,
        valad_id=valad_app.app_id,
        daemon_loop_period_s=3,
        config_path=tmp_path
    )

    lrp = LocalnetRoundProgressor(
        algorand_client=algorand_client,
        round_period_s=round_period_s
    )
    lrp.run()

    start_round = get_round()

    start_time = time.time() 
    while True:
        last_relative_round = get_round() - start_round
        # Refresh node orchestrators
        node_orc.refresh(last_relative_round)
        # Refresh delegator (contract) orchestrators
        [delco_orc.refresh(last_relative_round) for delco_orc in delco_orc_list]
        # Check for test completion (all foreseen delegator contract states reached)
        check_completion = [delco_orc.checker.check_completion() for delco_orc in delco_orc_list]
        if -1 in check_completion:
            print(
                [delco_orc.checker.targeted_states for delco_orc in delco_orc_list]
            )
            print(
                [delco_orc.checker.visited_states for delco_orc in delco_orc_list]
            )
            result = False
            break
        elif all(check == 0 for check in check_completion):
            result = True
            print(f'Successful on round {get_round()}, give daemon chance to recognize and log final state (e.g. ended).')
            print(f'Went through states {delco_states}')
            time.sleep(node_orc.daemon.loop_period_s+1)
            break
        if time.time() - start_time > timeout_s:
            print(f'Timeout on round {get_round()}')
            result = False
            break
        else: 
            time.sleep(0.1)

    node_orc.stop_daemon_thread()
    lrp.stop()
    assert result
