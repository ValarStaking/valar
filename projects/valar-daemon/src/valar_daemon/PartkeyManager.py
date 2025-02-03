"""Participation key manager definition.

Potential danger points:
- If the output format of partkey gets changed, `get_existing_partkey_parameters` would need adapting.
- General algod API changes (paths, parameters, behavior).
"""
import time
from typing import Tuple, List, Dict

from algokit_utils.beta.algorand_client import AlgorandClient
from algosdk.error import AlgodHTTPError

from valar_daemon.Logger import Logger


"""Return values when requesting partkey generation/
PARTKEY_GENERATION_REQUEST_OK_ADDED              - Request successfully added
PARTKEY_GENERATION_REQUEST_FAIL_IN_PENDING       - Already in pending buffer
PARTKEY_GENERATION_REQUEST_FAIL_IN_GENERATED     - Already generated 
PARTKEY_GENERATION_REQUEST_FAIL_PENDING_FULL     - Pending buffer full
PARTKEY_GENERATION_REQUEST_FAIL_GENERATED_FULL   - Generated buffer full
PARTKEY_GENERATION_REQUEST_FAIL_ALGOD_ERROR      - Encountered Algod error
PARTKEY_GENERATION_REQUEST_FAIL_IN_THE_PAST      - Key validity in the past
"""
PARTKEY_GENERATION_REQUEST_OK_ADDED              =  0
PARTKEY_GENERATION_REQUEST_FAIL_IN_PENDING       = -1
PARTKEY_GENERATION_REQUEST_FAIL_IN_GENERATED     = -2
PARTKEY_GENERATION_REQUEST_FAIL_PENDING_FULL     = -3
PARTKEY_GENERATION_REQUEST_FAIL_GENERATED_FULL   = -4
PARTKEY_GENERATION_REQUEST_FAIL_ALGOD_ERROR      = -5
PARTKEY_GENERATION_REQUEST_FAIL_IN_THE_PAST      = -6


def create_partkey_dict(
    address: str,
    vote_first_valid: int,
    vote_last_valid: int,
    selection_participation_key: str = None,
    state_proof_key: str = None,
    vote_participation_key: str = None,
    vote_key_dilution: str = None,
    id: str=None,
    scheduled_deletion: int=None
) -> dict:
    """Structure partkey information into dictionary.

    Notes
    -----
    Only the address and first/last round is mandatory to facilitate future keys.

    Parameters
    ----------
    address : str
        Account to which partkey belongs.
    vote_first_valid : int
        Starting round.
    vote_last_valid : int
        End round.
    selection_participation_key : str, optional
        Selection key parameter, by default None
    state_proof_key : str, optional
        State proof key parameter, by default None
    vote_participation_key : str, optional
        Participation key parameter, by default None
    vote_key_dilution : str, optional
        Dilution key parameter, by default None
    id : str, optional
        The key's ID, by default None
    scheduled_deletion : int, optional
        Round at which key will be deleted, by default None

    Returns
    -------
    dict
        Structured key information.
    """
    return {
        'address': address,
        'id': id,
        'scheduled-deletion': scheduled_deletion,
        'selection-participation-key': selection_participation_key,
        'state-proof-key': state_proof_key,
        'vote-first-valid': vote_first_valid,
        'vote-key-dilution': vote_key_dilution,
        'vote-last-valid': vote_last_valid,
        'vote-participation-key': vote_participation_key,
    }


class PartkeyBuffer(object):
    """Buffer housing participation key information.
    """

    def __init__(self, max_num_of_keys: int=50):
        """Initialize a partkey buffer.

        Parameters
        ----------
        max_num_of_keys : int, optional
            Maximum number of keys stored in the buffer, by default 50.
        """
        self.max_num_of_keys = max_num_of_keys
        self.partkeys = []

    def is_full(self) -> bool:
        """Check if partkey buffer is full.

        Returns
        -------
        bool
            True if full.
        """
        return len(self.partkeys) >= self.max_num_of_keys
        
    def add_partkey_to_buffer(            
        self,
        address: str,
        vote_first_valid: int,
        vote_last_valid: int,
        selection_participation_key: str=None,
        state_proof_key: str=None,
        vote_participation_key: str=None,
        vote_key_dilution: str=None,
        id=None,
        scheduled_deletion=None
    ):
        """Add a participation key to the buffer.

        Parameters
        ----------
        address : str
            Account to which partkey belongs.
        vote_first_valid : int
            Starting round.
        vote_last_valid : int
            End round.
        selection_participation_key : str, optional
            Selection key parameter, by default None
        state_proof_key : str, optional
            State proof key parameter, by default None
        vote_participation_key : str, optional
            Participation key parameter, by default None
        vote_key_dilution : str, optional
            Dilution key parameter, by default None
        id : str, optional
            The key's ID, by default None
        scheduled_deletion : int, optional
            Round at which key will be deleted, by default None
        """
        if self.is_full():
            raise RuntimeError(f'Partkey buffer is full ({len(self.partkeys)} partkeys present).')
        partkey = create_partkey_dict(
            address=address,
            vote_first_valid=vote_first_valid,
            vote_last_valid=vote_last_valid,
            selection_participation_key=selection_participation_key,
            state_proof_key=state_proof_key,
            vote_participation_key=vote_participation_key,
            vote_key_dilution=vote_key_dilution,
            id=id,
            scheduled_deletion=scheduled_deletion
        )
        self.partkeys.append(partkey)
    
    def pop_partkey_from_buffer(
        self,
        idx: int=0
    ) -> dict:
        """Pop oldest entry.

        Parameters
        ----------
        idx : int, optional
            _description_, by default 0

        Returns
        -------
        dict
            _description_
        """
        return self.partkeys.pop(idx)

    def get_next(
        self
    ) -> dict:
        """Get the next partkey entry.

        Returns
        -------
        dict
            Partkey info.
        """
        if self.is_empty():
            return None
        else:
            return self.partkeys[0]

    def is_empty(
        self
    ) -> bool:
        """Check if buffer is empty.

        Returns
        -------
        bool
            Flag on emptiness of buffer.
        """
        if len(self.partkeys) == 0:
            return True
        else: 
            return False

    def is_partkey_in_buffer(
        self,
        address: str,
        vote_first_valid: int,
        vote_last_valid: int
    ) -> bool:
        """Check if the partkey is already in the given buffer.

        Parameters
        ----------
        address : str
            Address of participating entity.
        vote_first_valid : int
            First round when the partkeys are valid.
        vote_last_valid : int
            Last round when the partkeys are valid.
        checked_buffer : List[dict]
            The buffer that is checked.

        Returns
        -------
        bool
        """
        if len(self.partkeys) > 0:
            for entry in self.partkeys:
                if all([
                    entry['address'] == address,
                    entry['vote-first-valid'] == vote_first_valid,
                    entry['vote-last-valid'] == vote_last_valid
                ]):
                    return True
        return False
                    
    def return_partkeys(
            self
    ) -> list:
        """Return a list of the participation keys.

        Returns
        -------
        list
            Participation keys.
        """
        return self.partkeys
    
    def get_index_of_partkey_in_buffer(
        self,
        address: str,
        vote_first_valid: int,
        vote_last_valid: int,
    ) -> int:
        """Get the index of a partkey in the buffer.

        Parameters
        ----------
        address : str
            Address of participating entity.
        vote_first_valid : int
            First round when the partkeys are valid.
        vote_last_valid : int
            Last round when the partkeys are valid.

        Returns
        -------
        int
            The index.

        Raises
        ------
        RuntimeError
            Cannot find partkey with ID
        """
        for idx, entry in enumerate(self.partkeys):
            if all([
                entry['address'] == address,
                entry['vote-first-valid'] == vote_first_valid,
                entry['vote-last-valid'] == vote_last_valid
            ]):
                return idx
        raise RuntimeError(
            f'Cannot find partkey with ' + \
            f'first round {entry["vote-first-valid"]} and last round {entry["vote-last-valid"]} ' + \
            f'for address {address} in buffer.'
        )
    
    def update_partkey_scheduled_deletion(
        self,
        address: str,
        vote_first_valid: int,
        vote_last_valid: int,
        scheduled_deletion: int
    ) -> Tuple[str, int]:
        """Update the scheduled deletion time.

        Parameters
        ----------
        address : str
            Address of participating entity.
        vote_first_valid : int
            First round when the partkeys are valid.
        vote_last_valid : int
            Last round when the partkeys are valid.
        scheduled_deletion : int
            Round at which the partkey should be deleted

        Returns
        -------
        Tuple(str, int)
            Confirmation of the ID and scheduled deletion round.
        """
        idx = self.get_index_of_partkey_in_buffer(
            address=address,
            vote_first_valid=vote_first_valid,
            vote_last_valid=vote_last_valid,
        )
        self.partkeys[idx]['scheduled-deletion'] = scheduled_deletion
        return (self.partkeys[idx]['id'], self.partkeys[idx]['scheduled-deletion'])


class PartkeyManager(object):
    """Participation key manager.
    """

    busy_msg = 'participation key generation already in progress'


    def __init__(
        self, 
        logger: Logger,
        algorand_client: AlgorandClient
    ):
        self.logger = logger
        self.algorand_client = algorand_client
        self.buffer_pending = PartkeyBuffer()
        self.buffer_generated = PartkeyBuffer()
        self.busy_generating_partkey = False # Flag


    def add_partkey_generation_request(
        self,
        address: str,
        vote_first_valid: int,
        vote_last_valid: int,
        vote_key_dilution: int=None,
        scheduled_deletion: int=None
    ):
        """Add partkey generation request to buffer. 

        Parameters
        ----------
        address : str
            Address of participating entity.
        vote_first_valid : int
            First round when the partkeys are valid.
        vote_last_valid : int
            Last round when the partkeys are valid.
        vote_key_dilution : str, optional
            Dilution key parameter, by default None
        scheduled_deletion : int, optional
            Round at which key will be deleted, by default None

        Returns
        -------
        int
            Status code.
        """
        # self.logger.debug(f'Requesting partkey generation between rounds {vote_first_valid} and {vote_last_valid} for address {address}.')
        self.logger.log_partkey_generation_request(
            address=address,
            vote_first_valid=vote_first_valid,
            vote_last_valid=vote_last_valid
        )
        try:
            last_round = self.algorand_client.client.algod.status()['last-round']
        except Exception as e:
            self.logger.log_generic_algod_error(e)
            return PARTKEY_GENERATION_REQUEST_FAIL_ALGOD_ERROR
        # First check if the partkey's validity is in the past
        if last_round >= vote_last_valid:
            self.logger.log_requested_partkey_in_past(num_of_keys=len(self.buffer_pending.partkeys))
            return PARTKEY_GENERATION_REQUEST_FAIL_IN_THE_PAST
        # Check for full buffers
        if self.buffer_pending.is_full():
            # self.logger.debug(f'Pending buffer is full ({self.buffer_pending.max_num_of_keys} partkeys).')
            self.logger.log_pending_buffer_is_full(num_of_keys=len(self.buffer_pending.partkeys))
            return PARTKEY_GENERATION_REQUEST_FAIL_PENDING_FULL
        elif self.buffer_generated.is_full():
            # self.logger.debug(f'Generated buffer is full ({self.buffer_generated.max_num_of_keys} partkeys).')
            self.logger.log_generated_buffer_is_full(num_of_keys=len(self.buffer_generated.partkeys))
            return PARTKEY_GENERATION_REQUEST_FAIL_GENERATED_FULL
        else:
            # Then check if already present in the buffers
            in_pending_buffer = self.is_partkey_generation_pending(
                address, 
                vote_first_valid, 
                vote_last_valid
            )
            in_generated_buffer = self.buffer_generated.is_partkey_in_buffer(
                address, 
                vote_first_valid, 
                vote_last_valid,
            )
            if in_pending_buffer:
                # self.logger.debug(f'Requested partkey already in pending buffer.')
                self.logger.log_requested_partkey_in_pending()
                return PARTKEY_GENERATION_REQUEST_FAIL_IN_PENDING
            elif in_generated_buffer:
                # self.logger.debug(f'Requested partkey already in generated buffer.')
                self.logger.log_requested_partkey_in_generated()
                return PARTKEY_GENERATION_REQUEST_FAIL_IN_GENERATED
            else:
                # Finally, update scheduled deletion and make the request
                if scheduled_deletion is None:
                    scheduled_deletion = vote_last_valid # No early deletion by default
                self.buffer_pending.add_partkey_to_buffer(
                    address,
                    vote_first_valid,
                    vote_last_valid,
                    vote_key_dilution=vote_key_dilution,
                    scheduled_deletion=scheduled_deletion
                )
                # self.logger.debug(f'Added to pending buffer.')
                self.logger.log_partkey_generation_request_added()
                return PARTKEY_GENERATION_REQUEST_OK_ADDED
 
                
    def refresh(
        self
    ) -> None:
        """Update buffers and run any pending partkey generation.
        """
        # if not self.busy_generating_partkey:
        # Conduct maintenance - key deletion (and info fetching) can take place even when busy generating
        self.delete_scheduled_partkeys()                # delete scheduled keys from generated buffer
        self.remove_old_entries_in_buffer_generated()   # delete expired keys from generated buffer
        # Keys need to be generated
        if not self.buffer_pending.is_empty(): # Keygen pending or busy
            next_pending = self.buffer_pending.get_next() # Shared between if clauses - should not execute sequentially!
            if self.busy_generating_partkey: # Check if generating finished
                is_generated = self.is_partkey_generated( # Check if the pending task is already done
                    next_pending['address'],
                    next_pending['vote-first-valid'],
                    next_pending['vote-last-valid']
                )
                if is_generated:
                    self.move_next_partkey_to_generated_buffer() # Move to generated buffer
                    self.busy_generating_partkey = False
                    # Warning!
                    # algod remains busy briefly after the key is already generated
                    # This requires a wait period between observing a key and generating a new one
                    time.sleep(0.1)
            else: # If not busy and pending, generate new one
                self.generate_partkey(
                    next_pending['address'],
                    next_pending['vote-first-valid'],
                    next_pending['vote-last-valid'],
                    next_pending['vote-key-dilution']
                )
                self.busy_generating_partkey = True


    def try_adding_generated_keys_to_buffer(
        self,
        partkey_params_list: List[Dict]
    ) -> int:
        """Check if specific partkeys have been generated and add them to the generated buffer if they are on the node.

        Parameters
        ----------
        partkey_params_list : List[Dict]
            Participation key parameters - address, first round, and last round.

        Returns
        -------
        int
            Number of keys added to the buffer.
        """
        # Do not proceed if the partkey manager is busy (first add the new key to the generated buffer)
        if self.busy_generating_partkey == True:
            return -1
        # Initialize - disregard partkeys that are already in the buffer
        for idx in reversed(range(len(partkey_params_list))): # Reverse iteration to avoid pop issues
            partkey_params = partkey_params_list[idx]
            in_buffer = self.buffer_generated.is_partkey_in_buffer(
                partkey_params['address'],
                partkey_params['vote-first-valid'],
                partkey_params['vote-last-valid']
            )
            if in_buffer:
                partkey_params_list.pop(idx)
        # All relevant partkeys are in the buffer, can return
        if len(partkey_params_list) == 0:
            return 0
        # Get all existing partkeys on the node
        res = self.algorand_client.client.algod.algod_request(
            'GET', 
            '/participation'
        )
        # Look for existing partkeys that should be in the buffer and add them if found on the node
        num_of_added_keys = 0
        if res is not None: # If there are partkeys on the node
            for partkey_params in partkey_params_list:  # Iterate provided partkeys
                for entry in res: # Iterate the partkeys that are on the node
                    if all([ # Match against all parameters and add partkey to buffer if it exists on the node
                        entry['address'] == partkey_params['address'],
                        entry['key']['vote-first-valid'] == partkey_params['vote-first-valid'],
                        entry['key']['vote-last-valid'] == partkey_params['vote-last-valid']
                    ]):
                        self.buffer_generated.add_partkey_to_buffer(
                            address=entry['address'],
                            vote_first_valid=entry['key']['vote-first-valid'],
                            vote_last_valid=entry['key']['vote-last-valid'],
                            selection_participation_key=entry['key']['selection-participation-key'],
                            state_proof_key=entry['key']['state-proof-key'],
                            vote_participation_key=entry['key']['vote-participation-key'],
                            vote_key_dilution=entry['key']['vote-key-dilution'],
                            id=entry['id']
                        )
                        num_of_added_keys += 1
        return num_of_added_keys


    def delete_scheduled_partkeys(self):
        """Delete partkeys that have been scheduled for deletion (e.g. on early contract termination).
        """
        current_round = self.algorand_client.client.algod.status()['last-round']
        for entry in self.buffer_generated.return_partkeys():
            if entry['scheduled-deletion'] is not None:
                if current_round > entry['scheduled-deletion']:
                    is_generated = self.is_partkey_generated( # Check if not already deleted in the meantime
                        entry['address'],
                        entry['vote-first-valid'],
                        entry['vote-last-valid']
                    )
                    if is_generated:
                        self.delete_partkey(
                            entry['address'],
                            entry['vote-first-valid'],
                            entry['vote-last-valid']
                        )


    def is_partkey_generation_pending(
        self,
        address: str,
        vote_first_valid: int,
        vote_last_valid: int,
    ) -> bool:
        """Check if partkey generation has been requested.

        Parameters
        ----------
        address : str
            Address of participating entity.
        vote_first_valid : int
            First round when the partkeys are valid.
        vote_last_valid : int
            Last round when the partkeys are valid.

        Returns
        -------
        bool
        """
        return self.buffer_pending.is_partkey_in_buffer(
            address, 
            vote_first_valid, 
            vote_last_valid
        )


    def is_partkey_generated(
        self,
        address: str,
        vote_first_valid: int,
        vote_last_valid: int
    ) -> bool:
        """Check if the partkey has already been generated.

        Parameters
        ----------
        address : str
            Address of participating entity.
        vote_first_valid : int
            First round when the partkeys are valid.
        vote_last_valid : int
            Last round when the partkeys are valid.

        Returns
        -------
        bool
        """
        res = self.get_existing_partkey_parameters(address, vote_first_valid, vote_last_valid)
        if res is not None:
            return True
        else:
            return False


    def move_next_partkey_to_generated_buffer(
        self
    ) -> None:
        """Move oldest partkey (FIFO) from pending to generated buffer.
        """
        entry = self.buffer_pending.pop_partkey_from_buffer() # Pop oldest entry
        entry = self.get_existing_partkey_parameters( # Retrieve partkey from algod
            entry['address'],
            entry['vote-first-valid'],
            entry['vote-last-valid']
        )
        self.buffer_generated.add_partkey_to_buffer(
            address=entry['address'],
            vote_first_valid=entry['vote-first-valid'],
            vote_last_valid=entry['vote-last-valid'],
            selection_participation_key=entry['selection-participation-key'],
            state_proof_key=entry['state-proof-key'],
            vote_participation_key=entry['vote-participation-key'],
            vote_key_dilution=entry['vote-key-dilution'],
            id=entry['id']
        )


    # def generate_next_partkey(
    #     self
    # ) -> None:
    #     """Generate the next pending participation key if not busy and the buffer is not empty.
    #     """
    #     # if not self.buffer_pending.is_empty():
    #     entry = self.buffer_pending.get_next()
    #     self.generate_partkey(
    #         entry["address"],
    #         entry["vote-first-valid"],
    #         entry["vote-last-valid"],
    #         entry["vote-key-dilution"]
    #     )
    #     self.busy_generating = True


    def generate_partkey(
        self,
        address: str,
        vote_first_valid: int,
        vote_last_valid: int,
        vote_key_dilution: int=None
    ) -> int:
        """Try to generate a participation key.

        Notes
        -----
        If `vote_key_dilution` is kept zero, algod makes the dilution sqrt of the duration.

        Parameters
        ----------
        address : str
            Address of participating entity.
        vote_first_valid : int
            First round when the partkeys are valid.
        vote_last_valid : int
            Last round when the partkeys are valid.
        vote_key_dilution : str, optional
            Dilution key parameter, by default None

        Raises
        ------
        AlgodHTTPError

        Returns
        -------
        int
            Partkey generating flag (0=startd, 1=busy).
        """
        params = dict(
            first=vote_first_valid,
            last=vote_last_valid
        )
        if vote_key_dilution is not None:
            params['dilution'] = vote_key_dilution
        try:
            res = self.algorand_client.client.algod.algod_request(
                'POST', 
                f'/participation/generate/{address}',
                params=params
            )
            # self.logger.info(f'Generating partkey for {address} starting at {vote_first_valid} and ending at {vote_last_valid}.')
            self.logger.log_generating_partkeys(
                address=address,
                vote_first_valid=vote_first_valid,
                vote_last_valid=vote_last_valid
            )
            return 0
        except AlgodHTTPError as e:
            # if e.code != 400:
            if self.busy_msg in e.args[0]:
                return 1
            else:
                raise e
        

    def get_existing_partkey_parameters(
        self, 
        address: str,
        vote_first_valid: int,
        vote_last_valid: int
    ) -> dict:
        """Obtain the relevant parameters of an already generated partkey.

        Parameters
        ----------
        address : str
            Address of participating entity.
        vote_first_valid : int
            First round when the partkeys are valid.
        vote_last_valid : int
            Last round when the partkeys are valid.

        Returns
        -------
        dict
            Partkey parameters. None if did not find the partkey for <address>.

        # Raises
        # ------
        # RuntimeError
        #     Did not find the partkey for <address>.
        """
        res = self.algorand_client.client.algod.algod_request(
            'GET', 
            '/participation'
        )
        if res is not None:
            for entry in res:
                if all([
                    entry['address'] == address,
                    entry['key']['vote-first-valid'] == vote_first_valid,
                    entry['key']['vote-last-valid'] == vote_last_valid
                ]):
                    return create_partkey_dict(
                        address=entry['address'],
                        vote_first_valid=entry['key']['vote-first-valid'],
                        vote_last_valid=entry['key']['vote-last-valid'],
                        selection_participation_key=entry['key']['selection-participation-key'],
                        state_proof_key=entry['key']['state-proof-key'],
                        vote_participation_key=entry['key']['vote-participation-key'],
                        vote_key_dilution=entry['key']['vote-key-dilution'],
                        id=entry['id']
                    )
                    # return {key: entry[key] for key in self.relevant_partkey_parameters}
        # raise RuntimeError(f'Did not find the partkey for {address}.')
        return None


    def remove_old_entries_in_buffer_generated(
        self
    ) -> int:
        """Remove partkeys that are no longer in use.

        Returns
        -------
        int
            Number of removed entries.
        """
        num_of_removed = 0 
        last_round = self.algorand_client.client.algod.status()['last-round'] # Get last round
        partkeys = self.buffer_generated.return_partkeys() # Fetch partkeys
        for idx in reversed(range(len(partkeys))): # Reverse iteration to avoid pop issues
            entry = partkeys[idx]
            if entry['vote-last-valid'] < last_round: # Automatically deleted in partkey list
                # self.buffer_generated.pop(idx) # Delete entry
                self.buffer_generated.pop_partkey_from_buffer(idx)
        # for idx, entry in enumerate(self.buffer_generated.return_partkeys()):
        #     is_generated = self.is_partkey_generated(
        #         entry['address'],
        #         entry['vote-first-valid'],
        #         entry['vote-last-valid']
        #     )
        #      # Marked generated, but not in generated buffer => used up or deleted
        #     if not is_generated:
        #         self.buffer_generated.pop_partkey_from_buffer(idx)
        #         num_of_removed += 1
        return num_of_removed


    # def fetch_and_add_existing_partkeys_to_buffer_generated(
    #     self
    # ) -> None:
    #     """Add partkeys that exist on the node to the generated buffer.
    #     """
    #     # Get all partkeys on the node
    #     res = self.algorand_client.client.algod.algod_request(
    #         'GET', 
    #         '/participation'
    #     )
    #     # Do nothing if there are not partkeys on the node
    #     if res is None:
    #         return
    #     # Drop the partkeys that are already in the generated buffer
    #     known_partkey_mask = [False for i in range(len(res))] # Assume all new initially (none known)
    #     for m, fetched_entry in enumerate(res):
    #         for n, buffered_entry in enumerate(self.buffer_generated.return_partkeys()):
    #             if all([
    #                 fetched_entry['address'] == buffered_entry['address'],
    #                 fetched_entry['key']['vote-first-valid'] == buffered_entry['vote-first-valid'],
    #                 fetched_entry['key']['vote-last-valid'] == buffered_entry['vote-last-valid']
    #             ]):
    #                 known_partkey_mask[m] = True # Mark the ones that are in the buffer
    #     if all(known_partkey_mask): # No new keys
    #         return
    #     # Maintain the unknonw (new) entries
    #     res = [res[i] for i in range(len(known_partkey_mask)) if not known_partkey_mask[i]]
    #     # Buffer the partkeys which are on the node, but not in the generated buffer
    #     for m, entry in enumerate(res):
    #         self.buffer_generated.add_partkey_to_buffer(
    #             address=entry['address'],
    #             vote_first_valid=entry['key']['vote-first-valid'],
    #             vote_last_valid=entry['key']['vote-last-valid'],
    #             selection_participation_key=entry['key']['selection-participation-key'],
    #             state_proof_key=entry['key']['state-proof-key'],
    #             vote_participation_key=entry['key']['vote-participation-key'],
    #             vote_key_dilution=entry['key']['vote-key-dilution'],
    #             id=entry['id']
    #         )


    def delete_partkey(
        self,
        address: str,
        vote_first_valid: int,
        vote_last_valid: int
    ) -> None:
        """Delete the participation key.

        Parameters
        ----------
        address : str
            Address of participating entity.
        vote_first_valid : int
            First round when the partkeys are valid.
        vote_last_valid : int
            Last round when the partkeys are valid.

        Raises
        ------
        RuntimeError
            Tried deleting partkey that is not in generated buffer.
        RuntimeError
            Tried deleting non-existent partkey.
        """
        # Check if in buffer
        in_gen_buf = self.buffer_generated.is_partkey_in_buffer(
            address,
            vote_first_valid,
            vote_last_valid
        )
        if not in_gen_buf:
            raise RuntimeError(
                f'Tried deleting partkey with ' + \
                f'first round {vote_first_valid} and last round {vote_last_valid} ' + \
                f'for address {address} that is not in generated buffer.'
            )
        # Check if exists at all
        generated = self.is_partkey_generated(
            address,
            vote_first_valid,
            vote_last_valid
        )
        if not generated:
            raise RuntimeError(
                f'Tried deleting non-existent partkey with ' + \
                f'first round {vote_first_valid} and last round {vote_last_valid} ' + \
                f'for address {address}.'
            )
        partkey_id = self.get_partkey_id(
            address,
            vote_first_valid,
            vote_last_valid
        )
        self.delete_partkey_using_id(partkey_id)


    def delete_partkey_using_id(
        self,
        partkey_id: int
    ) -> None:
        """Delete the participation key.

        Parameters
        ----------
        partkey_id : int
            ID of the participation key.
        """
        self.algorand_client.client.algod.algod_request(
            'DELETE', 
            f'/participation/{partkey_id}'
        )


    def get_partkey_id(
        self,
        address: str,
        vote_first_valid: int,
        vote_last_valid: int
    ) -> int:
        """Get partkey ID.

        Parameters
        ----------
        address : str
            Address of participating entity.
        vote_first_valid : int
            First round when the partkeys are valid.
        vote_last_valid : int
            Last round when the partkeys are valid.

        Returns
        -------
        int
            Partkey ID.
        """
        return self.get_existing_partkey_parameters(
            address,
            vote_first_valid,
            vote_last_valid
        )['id']


    def update_generated_partkey_scheduled_deletion(
        self,
        address: str,
        vote_first_valid: int,
        vote_last_valid: int,
        scheduled_deletion: int
    ) -> Tuple[str, int]:
        """Update the scheduled deletion time for a generated partkey.

        Parameters
        ----------
        address : str
            Address of participating entity.
        vote_first_valid : int
            First round when the partkeys are valid.
        vote_last_valid : int
            Last round when the partkeys are valid.
        scheduled_deletion : int
            Round at which the partkey should be deleted

        Returns
        -------
        Tuple(str, int)
            Confirmation of the ID and scheduled deletion round.
        """
        return self.buffer_generated.update_partkey_scheduled_deletion(
            address=address,
            vote_first_valid=vote_first_valid,
            vote_last_valid=vote_last_valid,
            scheduled_deletion=scheduled_deletion
        )
