import pytest
# from pathlib import Path

# import sys
# sys.path.insert(0, str(Path(*Path(__file__).parent.parts[:-3], 'valar-smart-contracts')))
from tests.noticeboard.config import ActionInputs


@pytest.fixture(scope='function')
def action_inputs():
    # return ActionInputs(
    #     asset=0,
    #     live=True,
    #     cnt_del_max=2,
    # )
    action_inputs = ActionInputs(
        asset=0,
        live=True,
        cnt_del_max=2,
        stake_max=100_000_000_000,
        # rounds_duration=40
        # delegation_terms_balance = DelegationTermsBalance(
        #     stake_min=0,
        #     stake_max=100_000_000_000,
        #     cnt_breach_del_max=3,
        #     rounds_breach=10,
        #     gating_asa_list=[(0,0), (0,0), (0,0), (0,0)],
        # )
    )
    # action_inputs.terms_time.rounds_setup = 5
    # action_inputs.terms_time.rounds_confirm = 5
    # action_inputs.terms_time.rounds_duration_min = 0
    print() # To avoid writing on the same line as initial pytest info statement
    print('Rounds duration ', action_inputs.rounds_duration)
    print('Rounds setup', action_inputs.terms_time.rounds_setup)
    print('Rounds confirm', action_inputs.terms_time.rounds_confirm)
    print('Rounds duration min', action_inputs.terms_time.rounds_duration_min)
    print('Rounds duration max', action_inputs.terms_time.rounds_duration_max)
    return action_inputs



# @pytest.fixture(scope='function')
# def daemon_config():
#     config_path = Path(Path(__file__).parent, 'tmp')
#     config_name = 'daemon.config'
#     daemon_config = DaemonConfig(
#         config_path,
#         config_name
#     )
#     return daemon_config


# @pytest.fixture(scope='function')
# def algorand_client():
#     algorand_client = AlgorandClient.default_local_net()
#     algorand_client.set_suggested_params_timeout(0)
#     return algorand_client


# @pytest.fixture(scope='function')
# def noticeboard(algorand_client, action_inputs):

#     dispenser = algorand_client.account.dispenser()

#     # Create localnet accounts
#     creator = create_and_fund_account(algorand_client, dispenser, [0])
#     pla_manager = create_and_fund_account(algorand_client, dispenser, [0])
#     del_manager = create_and_fund_account(algorand_client, dispenser, [0])
#     del_beneficiary = create_and_fund_account(algorand_client, dispenser, [0])
#     valad_manager = create_and_fund_account(algorand_client, dispenser, [0])
#     valad_owner = create_and_fund_account(algorand_client, dispenser, [0])
#     partner = create_and_fund_account(algorand_client, dispenser, [0])

#     # Initialize noticeboard client
#     noticeboard_client = NoticeboardClient(
#         algorand_client.client.algod,
#         creator=creator.address,
#         signer=creator.signer,
#         indexer_client=algorand_client.client.indexer,
#     )

#     # Make class for settin states
#     noticeboard = Noticeboard(
#         noticeboard_client=noticeboard_client,
#         algorand_client=algorand_client,
#         assets=[0],
#         creator=creator,
#         dispenser=dispenser,
#         pla_manager=pla_manager,
#         del_managers=[del_manager],
#         del_beneficiaries=[del_beneficiary],
#         val_managers=[valad_manager],
#         val_owners=[valad_owner],
#         partners=[partner]
#     )

#     # # 
#     # action_inputs = ActionInputs(
#     #     asset=0,
#     #     live=True,
#     # )

#     noticeboard.initialize_state(
#         target_state="SET", 
#         action_inputs=action_inputs
#     )

#     return noticeboard
