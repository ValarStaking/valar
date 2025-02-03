"""Valar Daemon.

Some terms are shortened to preserve space:
- valad: Validator Ad
- delco: Delegator Contract
- valman: Validator Manager.
"""
import copy
import time
from pathlib import Path
from typing import Tuple, List
from dataclasses import dataclass
from urllib.error import URLError, HTTPError

from algosdk import mnemonic, account
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.account_manager import AddressAndSigner
from algosdk.atomic_transaction_composer import AccountTransactionSigner      
from algokit_utils.logic_error import LogicError
from algosdk.error import AlgodHTTPError

from valar_daemon.AppWrapper import ValadAppWrapperList, DelcoAppWrapperList, ValadAppWrapper, DelcoAppWrapper
from valar_daemon.DaemonConfig import DaemonConfig
from valar_daemon.PartkeyManager import PartkeyManager, PARTKEY_GENERATION_REQUEST_OK_ADDED
from valar_daemon.Logger import Logger
from valar_daemon.utils import (
    get_algorand_client,
    set_valad_ready, 
    submit_partkeys,
    report_delco_breach_pay,
    report_partkeys_not_submitted,
    report_unconfirmed_partkeys,
    report_contract_expired,
    report_delben_breach_limits,
)
from valar_daemon.constants import (
    VALAD_NOT_READY_STATUS_CHANGE_OK,
    VALAD_NOT_READY_STATUS_ATTRIBUTE_ERROR,
    VALAD_NOT_READY_STATUS_NO_CHANGE,
    DELCO_READY_STATUS_REQUEST_DENIED,
    DELCO_READY_STATUS_BREACH_PAY,
    DELCO_READY_STATUS_NOT_SUBMITTED,
    DELCO_READY_STATUS_URL_ERROR,
    DELCO_READY_STATUS_REQUESTED,
    DELCO_READY_STATUS_PENDING,
    DELCO_READY_STATUS_SUBMITTED,
    VALAD_STATE_NOT_READY,
    DELCO_STATE_READY,
    DELCO_STATE_SUBMITTED,
    DELCO_STATE_LIVE,
    DELCO_STATE_ENDED_WITHDREW
) 


@dataclass(kw_only=True)
class AlgodStatus:
    """Algod status abstraction class.

    Parameters
    ----------
    is_ok : bool
        Flag indicating whether algod is running OK.
    message : str
        Corresponding (error) message, obtained when checking the status.
    """
    is_ok: bool
    message: str


class Daemon(object):


    def __init__(
        self,
        log_path: str,
        config_path: str
    ):
        """Valar Daemon master class.

        Parameters
        ----------
        log_path : str
            Path to where the log will be generated.
        config_path : str
            Path to the input config file.
        daemon_config : DaemonConfig
            Daemon configuration.
        logger : Logger
            Daemon log abstraction.
        algorand_client : AlgorandClient
            Algorand client.
        partkey_manager : PartkeyManager
            Participation key management class.
        valman : AddressAndSigner
            Validator Manager.
        stop_flag : bool
            Indicator to stop the Daemon.
        loop_period_s : float
            Period at which contracts are checked.
        valad_app_list : ValadAppWrapperList
            List of Validator Ads and relevant info.
        delco_app_list : DelcoAppWrapperList
            List of Delegator Contract and relevant info.
        """
        ### Read config ################################################################################################
        config_filename = Path(config_path).name
        self.daemon_config = DaemonConfig(
            Path(config_path).parent,
            config_filename
        )
        self.daemon_config.read_config() # Read and load up config values.
        self.daemon_config.create_swap() # In case of intermediate config reading, allow the user to edit the original.

        ### Initialize logger ##########################################################################################
        self.logger = Logger(
            log_dirpath=log_path,
            log_max_size_bytes=self.daemon_config.max_log_file_size_B,
            log_file_count=self.daemon_config.num_of_log_files_per_level
        )

        ### Configure client ###########################################################################################
        self.algorand_client = get_algorand_client(
            algod_config_server = self.daemon_config.algod_config_server,
            algod_config_token = self.daemon_config.algod_config_token,
        )

        ### Set up partkey manager #####################################################################################
        self.partkey_manager = PartkeyManager(
            self.logger,
            self.algorand_client
        )

        ### Set up validator manager ###################################################################################
        manager_private_key = mnemonic.to_private_key(self.daemon_config.validator_manager_mnemonic)
        manager_address = account.address_from_private_key(manager_private_key)
        self.valman = AddressAndSigner(
            address=manager_address,
            signer=AccountTransactionSigner(manager_private_key)
        )

        ### Set up loop ################################################################################################
        self.stop_flag = False
        self.loop_period_s = self.daemon_config.loop_period_s

        ### Initialize up valad and delco lists ########################################################################
        self.valad_app_list = ValadAppWrapperList(
            self.algorand_client,
            self.logger
        )
        self.delco_app_list = DelcoAppWrapperList(
            self.algorand_client,
            self.logger
        )

        ### Initialize app wrappers ####################################################################################
        self.populate_valad_wrapper_list() # Initialize valad wrappers using config
        self.populate_delco_wrapper_list() # Initialize delco wrappers using the valads

        ### Fetch existing partkeys (e.g. after reboot) ################################################################
        self.partkey_manager.try_adding_generated_keys_to_buffer(
            self.delco_app_list.get_partkey_params_list()
        )
        

    @staticmethod
    def check_algod_status(
        algorand_client: AlgorandClient
    ) -> AlgodStatus:
        """Check the status of algod and report error if not OK.

        Notes
        -----
        URLError 111: Algod service is offline
        URLError -2: Can not reach service (internet offline or initialization URL/token is not correct)

        Parameters
        ----------
        algorand_client : AlgorandClient
            Algorand client.

        Returns
        -------
        AlgodStatus
        """
        try:
            algorand_client.client.algod.status()
            return AlgodStatus(
                is_ok=True, 
                message="Algod is OK."
            )
        except URLError as e:
            return AlgodStatus(
                is_ok = False,
                message = f'URLError {e.args[0].errno}: {e.args[0].strerror}'
            )
        except AlgodHTTPError as e:
            return AlgodStatus(
                is_ok = False,
                message = f'AlgodHTTPError {e.code}: {e.args[0]}'
            )
        except Exception as e:
            return AlgodStatus(
                is_ok = False,
                message = f'Unknown error: {e}'
            )


    def maintain_valads(
        self
    ):
        """Maintain validator ads (try to change state from `NOT READY` to `READY` where applicable).
        """
        self.logger.log_maintaining_valads(num_of_valads=len(self.valad_app_list.get_app_list()))
        for valad_app in self.valad_app_list.get_app_list():
            self.maintain_single_valad(
                self.algorand_client,
                self.valman,
                copy.copy(valad_app),
                self.logger
            )


    @staticmethod
    def maintain_single_valad(
        algorand_client: AlgorandClient,
        valman: AddressAndSigner,
        valad_app: ValadAppWrapper,
        logger: Logger,
    ) -> int:
        """Maintain validator ads (try to change state from `NOT READY` to `READY` where applicable).

        Parameters
        ----------
        algorand_client : AlgorandClient
            Algorand client.
        valman : AddressAndSigner
            Validator manager.
        valad_app : ValadAppWrapper
            Client and relevant parameters of the validator ad.
        logger : logging.Logger
            Message logger.

        Returns
        -------
        int
            Status message.
        """
        logger.log_state_of_valad_with_id(app_id=valad_app.app_id, state=valad_app.state)
        if valad_app.state == VALAD_STATE_NOT_READY:
            try:
                set_valad_ready(
                    algorand_client=algorand_client,
                    valown_address=valad_app.valown_address,
                    valad_id=valad_app.app_id,
                    valman=valman,
                    noticeboard_client=valad_app.notbd_client
                )
                return VALAD_NOT_READY_STATUS_CHANGE_OK
            except AttributeError as e:
                logger.log_set_valad_ready_attribute_error(app_id=valad_app.app_id)
                return VALAD_NOT_READY_STATUS_ATTRIBUTE_ERROR
        return VALAD_NOT_READY_STATUS_NO_CHANGE


    def maintain_delcos(
        self
    ):
        """Maintain delegator contracts.
        """
        self.logger.log_maintaining_delcos(num_of_delcos=len(self.delco_app_list.get_app_list()))
        for delco_app in self.delco_app_list.get_app_list():
            self.maintain_single_delco(
                self.algorand_client,
                self.valman,
                copy.copy(delco_app),
                self.partkey_manager,
                self.logger,
            )
            if delco_app.state[0] >> 4 or delco_app.state[0] >> 5:
                self.delco_app_list.remove_single_app(delco_app.app_id)
                self.logger.log_removed_ended_or_deleted_delco(app_id=delco_app.app_id)

        
    @staticmethod
    def maintain_single_delco(
        algorand_client: AlgorandClient,
        valman: AddressAndSigner,
        delco_app: DelcoAppWrapper,
        partkey_manager: PartkeyManager,
        logger: Logger,
    ):
        """Maintain a single delegator contract.

        Parameters
        ----------
        delco_app : DelcoAppWrapper
            Delegator contract app wrapper.
        """
        try:
            delco_state = delco_app.state
            logger.log_state_of_delco_with_id(app_id=delco_app.app_id, state=delco_state)
            if delco_state == DELCO_STATE_READY: # Generate and submit keys (add internal state)
                Daemon.delco_ready_state_handler(
                    algorand_client,
                    valman,
                    delco_app,
                    partkey_manager,
                    logger,
                )
            elif delco_state == DELCO_STATE_SUBMITTED:
                Daemon.delco_submitted_state_handler(
                    algorand_client,
                    valman,
                    delco_app,
                    logger
                )
            elif delco_state == DELCO_STATE_LIVE:
                Daemon.delco_live_state_handler(
                    algorand_client,
                    valman,
                    delco_app,
                    logger
                )
            # Ended contracts no longer visible from validator ad's list -> no need for handler
            elif delco_state[0] >> 4: # Ended contract
                Daemon.delco_ended_state_handler(
                    algorand_client,
                    partkey_manager,
                    delco_app,
                    logger
                )
            elif delco_state[0] >> 5: # Deleted contract
                Daemon.delco_deleted_state_handler(
                    algorand_client,
                    partkey_manager,
                    logger
                )
            else:
                logger.log_unknown_delco_state(state=delco_state)
        except Exception as e:
            logger.error(f'Error while handling delco with ID {delco_app.app_id}: {e}.')


    @staticmethod
    def delco_ready_state_handler(
        algorand_client: AlgorandClient,
        valman: AddressAndSigner,
        delco_app: DelcoAppWrapper,
        partkey_manager: PartkeyManager,
        logger: Logger,
    ):
        """Handle a ready delegator contract (generate and submit keys).

        Parameters
        ----------
        delco_app : DelcoAppWrapper

        Returns
        -------
        int
            Internal state indicator.
        """
        logger.log_delco_in_ready_handler(app_id=delco_app.app_id)
        try: # Check if can pay (funds not frozen)
            report_delco_breach_pay( # Error if can pay, success if can not
                algorand_client=algorand_client,
                valown_address=delco_app.valown_address,
                delman_address=delco_app.delman_address,
                valad_id=delco_app.valad_id,
                delco_id=delco_app.app_id,
                fee_asset_id=delco_app.fee_asa_id,
                valman=valman,
                noticeboard_client=delco_app.notbd_client
            )
            logger.log_delco_cannot_pay(app_id=delco_app.app_id)
            return DELCO_READY_STATUS_BREACH_PAY
        except AttributeError:
            logger.log_attributeerror_cannot_pay(app_id=delco_app.app_id)
        except LogicError: # Failed transaction on LocalNet
            logger.log_logicerror_cannot_pay(app_id=delco_app.app_id)
        except HTTPError: # Failed transaction on public network
            logger.log_httperror_cannot_pay(app_id=delco_app.app_id)
        except AlgodHTTPError: # Failed transaction on public network
            logger.log_httperror_cannot_pay(app_id=delco_app.app_id)
            # Proceed to possible self-reporting
        try: # Check if can pay (funds not frozen)
            report_partkeys_not_submitted( # Error if still time
                algorand_client=algorand_client,
                valown_address=delco_app.valown_address,
                delman_address=delco_app.delman_address,
                valad_id=delco_app.valad_id,
                delco_id=delco_app.app_id,
                fee_asset_id=delco_app.fee_asa_id,
                valman=valman,
                noticeboard_client=delco_app.notbd_client
            )
            logger.log_partkeys_not_submitted(app_id=delco_app.app_id)
            return DELCO_READY_STATUS_NOT_SUBMITTED
        except AttributeError:
            logger.log_attributeerror_partkeys_not_submitted(app_id=delco_app.app_id)
        except LogicError: # Failed transaction on LocalNet
            logger.log_logicerror_partkeys_not_submitted(app_id=delco_app.app_id)
        except HTTPError: # Failed transaction on public network
            logger.log_httperror_partkeys_not_submitted(app_id=delco_app.app_id)
        except AlgodHTTPError: # Failed transaction on public network
            logger.log_httperror_cannot_pay(app_id=delco_app.app_id)
        # Check if partkeys already generated / exist
        try:
            is_generated = partkey_manager.is_partkey_generated(
                address=delco_app.delben_address,
                vote_first_valid=delco_app.round_start,
                vote_last_valid=delco_app.round_end
            )
        except URLError:
            logger.log_urlerror_checking_partkey_generated(app_id=delco_app.app_id)
            return DELCO_READY_STATUS_URL_ERROR
        if is_generated:    # Partkeys generated, submit and move to next state
            logger.log_partkeys_generated_for_delco(app_id=delco_app.app_id)
            # Get key parameters
            partkey_params = partkey_manager.get_existing_partkey_parameters(
                address=delco_app.delben_address,
                vote_first_valid=delco_app.round_start,
                vote_last_valid=delco_app.round_end
            )
            try: # Submit partkeys
                submit_partkeys(
                    algorand_client=algorand_client,
                    valown_address=delco_app.valown_address,
                    delman_address=delco_app.delman_address,
                    delben_address=delco_app.delben_address,
                    partner_address=delco_app.partner_address,
                    valad_id=delco_app.valad_id,
                    delco_id=delco_app.app_id,
                    fee_asset_id=delco_app.fee_asa_id,
                    valman=valman,
                    noticeboard_client=delco_app.notbd_client,
                    vote_first=partkey_params['vote-first-valid'],
                    vote_last=partkey_params['vote-last-valid'],
                    vote_key_dilution=partkey_params['vote-key-dilution'],
                    vote_pk=partkey_params['vote-participation-key'],
                    selection_pk=partkey_params['selection-participation-key'],
                    state_proof_pk=partkey_params['state-proof-key']
                )
                logger.log_partkey_params_submitted(app_id=delco_app.app_id)
                return DELCO_READY_STATUS_SUBMITTED
            except AttributeError:
                logger.log_attributeerror_partkey_submit(app_id=delco_app.app_id)
                return DELCO_READY_STATUS_URL_ERROR
        # Partkey was not generated, so check if it is still pending or if it needs to be generated
        try:
            is_pending = partkey_manager.is_partkey_generation_pending(
                address=delco_app.delben_address,
                vote_first_valid=delco_app.round_start,
                vote_last_valid=delco_app.round_end
            )
        except URLError:
            logger.log_urlerror_checking_partkey_pending(app_id=delco_app.app_id)
            return DELCO_READY_STATUS_URL_ERROR
        if is_pending:      # Generating, wait it out
            logger.log_partkey_generation_pending(app_id=delco_app.app_id)
            return DELCO_READY_STATUS_PENDING
        else:               # Request partkey generation
            res = partkey_manager.add_partkey_generation_request( # No on-chain operation
                address=delco_app.delben_address,
                vote_first_valid=delco_app.round_start,
                vote_last_valid=delco_app.round_end
            )
            if res == PARTKEY_GENERATION_REQUEST_OK_ADDED:
                logger.log_requested_partkey_generation(delco_app.app_id)
                return DELCO_READY_STATUS_REQUESTED
            else:
                logger.log_partkey_generation_denied(delco_app.app_id)
                return DELCO_READY_STATUS_REQUEST_DENIED


    @staticmethod
    def delco_submitted_state_handler(
        algorand_client: AlgorandClient,
        valman: AddressAndSigner,
        delco_app: DelcoAppWrapper,
        logger: Logger,
    ):
        """Handle a delegator contract with submitted keys (report unconfirmed keys).

        Parameters
        ----------
        delco_app : DelcoAppWrapper
        """
        logger.debug(f'In submitted state handler for delco with ID {delco_app.app_id}.')
        try:
            report_unconfirmed_partkeys(
                algorand_client=algorand_client,
                valown_address=delco_app.valown_address,
                delman_address=delco_app.delman_address,
                partner_address=delco_app.partner_address,
                valad_id=delco_app.valad_id,
                delco_id=delco_app.app_id,
                fee_asset_id=delco_app.fee_asa_id,
                valman=valman,
                noticeboard_client=delco_app.notbd_client,
            )
            logger.log_partkeys_not_confirmed(delco_app.app_id)
        except AttributeError:
            logger.log_attributeerror_partkeys_not_confirmed(delco_app.app_id)
        except LogicError:
            logger.log_logicerror_partkeys_not_confirmed(delco_app.app_id)
        except HTTPError: # Failed transaction on public network
            logger.log_httperror_partkeys_not_confirmed(app_id=delco_app.app_id)
        except AlgodHTTPError: # Failed transaction on public network
            logger.log_httperror_cannot_pay(app_id=delco_app.app_id)


    @staticmethod
    def delco_live_state_handler(
        algorand_client: AlgorandClient,
        valman: AddressAndSigner,
        delco_app: DelcoAppWrapper,
        logger: Logger,
    ):
        """Handle a live delegator contract (check different limit breaches and expiry).

        Parameters
        ----------
        delco_app : DelcoAppWrapper
        """
        logger.log_delco_in_live_handler(app_id=delco_app.app_id)
        # Call the corresponding checkup functions, which could result in a state change
        # Check if expired
        try:
            report_contract_expired(
                algorand_client=algorand_client,
                valown_address=delco_app.valown_address,
                delman_address=delco_app.delman_address,
                partner_address=delco_app.partner_address,
                valad_id=delco_app.valad_id,
                delco_id=delco_app.app_id,
                fee_asset_id=delco_app.fee_asa_id,
                valman=valman,
                noticeboard_client=delco_app.notbd_client
            )
            logger.log_contract_expired(delco_app.app_id)
            return
        except AttributeError:
            logger.log_expired_attribute_error(app_id=delco_app.app_id)
        except LogicError:
            logger.log_tried_contract_expired(app_id=delco_app.app_id)
        except HTTPError: # Failed transaction on public network
            logger.log_httperror_contract_expired(app_id=delco_app.app_id)
        except AlgodHTTPError: # Failed transaction on public network
            logger.log_httperror_contract_expired(app_id=delco_app.app_id)
        # Check if ALGO (max) or gating ASA (min) limits breached
        try:
            report_delben_breach_limits(
                algorand_client=algorand_client,
                valown_address=delco_app.valown_address,
                delman_address=delco_app.delman_address,
                delben_address=delco_app.delben_address,
                partner_address=delco_app.partner_address,
                valad_id=delco_app.valad_id,
                delco_id=delco_app.app_id,
                fee_asset_id=delco_app.fee_asa_id,
                gating_asa_id_list=delco_app.gating_asa_id_list,
                valman=valman,
                noticeboard_client=delco_app.notbd_client
            )
            logger.log_gating_or_stake_limit_breached(app_id=delco_app.app_id)
            return
        except AttributeError:
            logger.log_gating_or_stake_limit_breached_attribute_error(app_id=delco_app.app_id)
        except LogicError:
            logger.log_logicerror_gating_or_stake_limit_breached(app_id=delco_app.app_id)
        except HTTPError: # Failed transaction on public network
            logger.log_httperror_gating_or_stake_limit_breached(app_id=delco_app.app_id)
        except AlgodHTTPError: # Failed transaction on public network
            logger.log_httperror_gating_or_stake_limit_breached(app_id=delco_app.app_id)
        try: # Check if can pay
            report_delco_breach_pay( # Error if can pay, success if can not
                algorand_client=algorand_client,
                valown_address=delco_app.valown_address,
                delman_address=delco_app.delman_address,
                valad_id=delco_app.valad_id,
                delco_id=delco_app.app_id,
                fee_asset_id=delco_app.fee_asa_id,
                valman=valman,
                noticeboard_client=delco_app.notbd_client
            )
            logger.log_delco_cannot_pay(app_id=delco_app.app_id)
            return
        except AttributeError:
            logger.log_attributeerror_cannot_pay(app_id=delco_app.app_id)
        except LogicError:
            logger.log_logicerror_cannot_pay(app_id=delco_app.app_id)
        except HTTPError: # Failed transaction on public network
            logger.log_httperror_cannot_pay(app_id=delco_app.app_id)
        except AlgodHTTPError: # Failed transaction on public network
            logger.log_httperror_cannot_pay(app_id=delco_app.app_id)


    @staticmethod
    def delco_ended_state_handler(
        algorand_client: AlgorandClient,
        partkey_manager: PartkeyManager,
        delco_app: DelcoAppWrapper,
        logger: Logger,
    ):
        """Handle an ended delegator contract (delete partkeys).

        Parameters
        ----------
        algorand_client : AlgorandClient
        partkey_manager : PartkeyManager
        delco_app : DelcoAppWrapper
        """
        # logger.debug(f'In ended state handler for delco with ID {delco_app.app_id}.')
        logger.log_delco_in_ended_handler(app_id=delco_app.app_id)
        # Check if the partkey still exists (could be deleted at contract expiry or manually)
        try:
            is_generated = partkey_manager.is_partkey_generated(
                address=delco_app.delben_address,
                vote_first_valid=delco_app.round_start,
                vote_last_valid=delco_app.round_end
            )
        except URLError:
            logger.log_urlerror_checking_partkey_generated(app_id=delco_app.app_id)
        # Scheduled deletion of partkey, which will no longer be used
        if is_generated:
            current_round = algorand_client.client.algod.status()['last-round']
            # Extend duration for the 320 rounds (15 min)
            # To prevent the delayed staking on extension
            # Extension falls under withdrawal
            # Classic withdrawal grants these rounds for free 
            if delco_app.state == DELCO_STATE_ENDED_WITHDREW:
                target_scheduled_deletion = current_round + 320
            else:
                target_scheduled_deletion = current_round
            # Update accordingly
            partkey_manager.update_generated_partkey_scheduled_deletion(
                address=delco_app.delben_address,
                vote_first_valid=delco_app.round_start,
                vote_last_valid=delco_app.round_end,
                scheduled_deletion=target_scheduled_deletion 
            )
            logger.log_scheduled_partkey_deletion_for_ended_or_deleted(
                app_id=delco_app.app_id,
                scheduled_deletion=target_scheduled_deletion,
                round_end=delco_app.round_end
            )
        else:
            logger.log_no_partkeys_found_for_ended_or_deleted(app_id=delco_app.app_id)


    @staticmethod
    def delco_deleted_state_handler(
        algorand_client: AlgorandClient,
        partkey_manager: PartkeyManager,
        delco_app: DelcoAppWrapper,
        logger: Logger,
    ):
        """Handle an ended delegator contract (delete partkeys).

        Parameters
        ----------
        partkey_manager : PartkeyManager
        delco_app : DelcoAppWrapper
        """
        logger.log_delco_in_deleted_handler(app_id=delco_app.app_id)
        # Check if the partkey still exists (could be deleted at contract expiry or manually)
        try:
            is_generated = partkey_manager.is_partkey_generated(
                address=delco_app.delben_address,
                vote_first_valid=delco_app.round_start,
                vote_last_valid=delco_app.round_end
            )
        except URLError:
            logger.debug(f'URL error while checking if partkey already generated for delco with ID {delco_app.app_id}.')
            logger.log_urlerror_checking_partkey_generated(app_id=delco_app.app_id)
        # Scheduled deletion of partkey, which will no longer be used
        if is_generated:
            current_round = algorand_client.client.algod.status()['last-round']
            target_scheduled_deletion = current_round
            partkey_manager.update_generated_partkey_scheduled_deletion(
                address=delco_app.delben_address,
                vote_first_valid=delco_app.round_start,
                vote_last_valid=delco_app.round_end,
                scheduled_deletion=target_scheduled_deletion
            )
            logger.log_scheduled_partkey_deletion_for_ended_or_deleted(
                app_id=delco_app.app_id,
                scheduled_deletion=target_scheduled_deletion,
                round_end=delco_app.round_end
            )
        else:
            logger.log_no_partkeys_found_for_ended_or_deleted(app_id=delco_app.app_id)


    def populate_valad_wrapper_list(self) -> Tuple[int, List]:
        """Populate the list of validator ad apps wrappers.

        Returns
        -------
        Tuple[int, int]
            Number of validator ads connected and the list of validator ad IDs from the config file.
        """
        # Read in latest valad app IDs
        self.daemon_config.read_swap()
        # Fetch valads based on the info provided in the config
        valad_id_list = copy.copy(self.daemon_config.validator_ad_id_list)
        self.logger.log_num_of_valad_ids_found(num_of_valads=len(valad_id_list))
        # Add new valads (if any after the first call)
        num_of_added_valads = self.valad_app_list.add_multiple_apps(valad_id_list)
        self.logger.log_num_of_valad_clients_connected(num_of_valads=num_of_added_valads)
        # Update the dynamic information of apps
        num_of_valads, num_of_updated_valads = self.valad_app_list.update_apps()
        self.logger.log_num_of_updated_valads(
            num_of_updated_valads=num_of_updated_valads, 
            num_of_valads=num_of_valads
        )
        return num_of_valads, valad_id_list


    def populate_delco_wrapper_list(self) -> None:
        """Populate the list of delegator contract apps wrappers.
        """
        # Fetch IDs of delcos associated with the valads
        delco_id_list = [d_id for valad_app in self.valad_app_list.get_app_list() for d_id in valad_app.delco_id_list]
        self.logger.log_num_of_connected_delcos(num_of_delcos=len(delco_id_list))
        # Add new delcos (if any after the first call)
        num_of_added_delcos = self.delco_app_list.add_multiple_apps(delco_id_list)
        self.logger.log_num_of_delco_clients_connected(num_of_delcos=num_of_added_delcos)
        # Update the dynamic information of apps
        num_of_delcos, num_of_updated_delcos = self.delco_app_list.update_apps()
        self.logger.log_num_of_updated_delcos(
            num_of_updated_delcos=num_of_updated_delcos, 
            num_of_delcos=num_of_delcos
        )


    def maintain_contracts(
        self
    ) -> None:
        """Maintain (service) the validator ads and delegator contracts.
        """
        ### Valad part #################################################################################################
        num_of_valads, valad_id_list = self.populate_valad_wrapper_list()
        # Stop if there will be nothing to service
        if num_of_valads == 0:
            self.logger.log_zero_valad_clients(valad_id_list=valad_id_list)
            return
        # Set to valad ready where applicable
        self.maintain_valads()
        ### Delco part #################################################################################################
        self.populate_delco_wrapper_list()
        # Handle each delco based on its state
        self.maintain_delcos()


    def run(
        self
    ) -> None:
        """Run the daemon, periodically calling the smart contract record function.
        """
        while not self.stop_flag:
            # Measure time
            start_time_s = time.time()
            # Check algod
            algod_status = Daemon.check_algod_status(self.algorand_client)
            # If good, run daemon logic
            if algod_status.is_ok:
                self.logger.log_algod_ok_continuing()
                self.logger.log_current_round(current_round=self.algorand_client.client.algod.status()["last-round"])
                try:
                    self.maintain_contracts()        # Service valads and delcos
                except Exception as e:
                    self.logger.log_generic_contract_servicing_error(e)
                try:
                    self.partkey_manager.refresh()  # Manage partkeys
                except Exception as e:
                    self.logger.log_generic_partkey_manager_error(e)
            # If not, report critical
            else:
                self.logger.log_algod_error(algod_status.message)
            # Sleep for the remaining time
            try:
                self.logger.log_single_loop_execution_time(round(time.time() - start_time_s, 2))
                self.logger.log_targeted_sleep_duration(round(start_time_s + self.loop_period_s - time.time(), 2))
                time.sleep(start_time_s + self.loop_period_s - time.time())
            except Exception as e:
                self.logger.log_could_not_sleep(duration_s=self.loop_period_s, e=e)


    def stop(
        self
    ) -> None:
        """Stop the daemon by altering the stop flag.
        """
        self.stop_flag = True
        self.logger.info('Stopping daemon.')
