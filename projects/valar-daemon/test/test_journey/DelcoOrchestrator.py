from valar_daemon.AppWrapper import DelcoAppWrapper
from valar_daemon.constants import DELCO_STATE_SUBMITTED


class DelcoOrchestrator():

    def __init__(
        self, 
        actions,
        checker,
        algorand_client,
        valad_id,
        noticeboard,
        action_inputs
    ) -> list:
        self.actions = actions
        self.checker = checker
        self.algorand_client = algorand_client
        self.valad_id = valad_id
        self.action_inputs = action_inputs
        self.dispenser = noticeboard.dispenser
        self.noticeboard = noticeboard
        self.allow_key_confirming = None
        self.delco_app = None

    def refresh(self, last_round:int) -> int:
        if self.delco_app is not None:
            gs = self.delco_app.delco_client.get_global_state()
            self.checker.update_state_history(gs.state.as_bytes)
            if self.allow_key_confirming and gs.state.as_bytes == DELCO_STATE_SUBMITTED:
                print(f'Signing keys for delegator contract with ID {self.delco_app.delco_client.app_id}.')
                self.try_to_confirm_keys()
        if len(self.actions) > 0: # Actions pending
            next_action = self.actions[0]
            if next_action[0] <= last_round: # Should take action now
                # Create / delete contract
                if next_action[1] & 1 << 7:
                    if self.delco_app is None: # Create if non-existent
                        self.create_contract()
                else: 
                    self.delete_contract()
                # # Withdraw from contract
                if next_action[1] & 1 << 5:
                    self.withdraw_contract()
                else:
                    pass
                # # Add / remove gating asset
                # if next_action[1] & 1 << 3:
                #     self.fund_gating()
                # else:
                #     self.remove_gating()
                # # Add / remove gating asset
                # if next_action[1] & 1 << 3:
                #     self.fund_gating()
                # else:
                #     self.remove_gating()
                # # Add / remove stake funds
                # if next_action[1] & 1 << 2:
                #     self.fund_stake()
                # else:
                #     self.remove_stake()
                # # Unfreeze / freeze fee asset
                # if next_action[1] & 1 << 1:
                #     pass
                # else:
                #     self.freeze_fee_asset()
                # # Allow the confirming of keys
                if next_action[1] & 1 << 0:
                    self.allow_key_confirming = True
                else:
                    self.allow_key_confirming = False
                self.actions.pop(0)
            return 1
        return 0
    
    def try_to_confirm_keys(self):
        self.noticeboard.delegator_action(
            app_id=self.delco_app.app_id,
            action_name='keys_confirm',
            action_inputs=self.action_inputs,
            val_app=self.delco_app.valad_id,
            # action_account=self.noticeboard.del_managers[0]
        )
    
    def create_contract(self) -> None:
        """Create delegator contract in READY state.
        """
        delco_id = self.noticeboard.initialize_delegator_contract_state(
            action_inputs=self.action_inputs, 
            val_app_id=self.valad_id,
            target_state="READY"
        )
        self.delco_app = DelcoAppWrapper(
            self.algorand_client,
            delco_id
        )
        print(f'Created delegator contract with ID {delco_id}.')
    
    def delete_contract(self):
        pass
    
    def withdraw_contract(self) -> None:
        """Withdraw from delegator contract.
        """
        self.noticeboard.delegator_action(
            app_id=self.delco_app.app_id,
            action_name='contract_withdraw',
            action_inputs=self.action_inputs,
            val_app=self.delco_app.valad_id,
        )
    
    def fund_gating(self):
        pass
    
    def remove_gating(self):
        pass
    
    def fund_stake(self):
        pass
    
    def remove_stake(self):
        pass
    
    def freeze_fee_asset(self):
        pass
    
