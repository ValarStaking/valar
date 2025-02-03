import time
import copy
import string
import random
import pytest
from typing import Callable
from dataclasses import dataclass

from algosdk.error import AlgodHTTPError
from algokit_utils.beta.algorand_client import AlgorandClient

from test.utils import (
    wait_for_rounds, 
    create_and_fund_account,
    does_partkey_exist,
    get_partkey_id,
    generate_partkey,
    try_to_delete_partkey,
    delete_existing_partkeys,
    calc_sleep_time_for_partkey_generation,
    get_existing_partkey_parameters
)

from valar_daemon.PartkeyManager import (
    PartkeyManager, 
    PartkeyBuffer,
    PARTKEY_GENERATION_REQUEST_OK_ADDED,
    PARTKEY_GENERATION_REQUEST_FAIL_IN_PENDING,
    PARTKEY_GENERATION_REQUEST_FAIL_IN_GENERATED,
    PARTKEY_GENERATION_REQUEST_FAIL_PENDING_FULL,
    PARTKEY_GENERATION_REQUEST_FAIL_GENERATED_FULL,
    PARTKEY_GENERATION_REQUEST_FAIL_ALGOD_ERROR,
    PARTKEY_GENERATION_REQUEST_FAIL_IN_THE_PAST
)



### Setup ######################################################################

def generate_random_address(length=58):
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=length))

@pytest.fixture(scope="function")
def partkey_buffer():
    return PartkeyBuffer()

@pytest.fixture(scope="function")
def partkey_manager(algorand_client, logger_mockup):
    return PartkeyManager(
        # logging.Logger('test'),
        logger_mockup,
        algorand_client
    )

@dataclass(kw_only=True)
class PartkeyInfo:
    """Partkey information, included in the tests - for generating, checking, deleting, etc.
    """
    address: str
    vote_first_valid: int
    vote_last_valid: int
    selection_participation_key: None | str = None
    state_proof_key: None | str = None
    vote_participation_key: None | str = None
    vote_key_dilution: None | int = None
    scheduled_deletion: None | str = None
    def to_dict(self):
        return {
            'address': self.address,
            'vote-first-valid': self.vote_first_valid,
            'vote-last-valid': self.vote_last_valid
        }

@pytest.fixture(scope="function")
def dummy_partkey_factory(algorand_client) -> Callable:
    """
    Generate a factory function to create unique participation key information for a random address for 1000 rounds.

    Parameters
    ----------
    algorand_client : AlgorandClient
        Algorand client connected to localnet.

    Returns
    -------
    Callable
        Factory function that returns a new PartkeyInfo instance.
    """
    def _create():
        last_round = algorand_client.client.algod.status()['last-round']
        return PartkeyInfo(
            address=algorand_client.account.random().address,
            vote_first_valid=last_round,
            vote_last_valid=last_round + 1_000,
            vote_key_dilution=32,
            scheduled_deletion=None,
        )
    return _create

@pytest.fixture(scope="function")
def dummy_partkey(
    dummy_partkey_factory: Callable
) -> PartkeyInfo:
    """Generate participation key information for a random address with a 1000-round duration.

    Parameters
    ----------
    dummy_partkey_factory : Callable
        Factory function that returns a new PartkeyInfo instance.

    Returns
    -------
    object
        Participation key information.
    """
    return dummy_partkey_factory()
    # last_round = algorand_client.client.algod.status()['last-round']
    # return PartkeyInfo(
    #     address = algorand_client.account.random().address,
    #     vote_first_valid = last_round,
    #     vote_last_valid = last_round + 1_000,
    #     vote_key_dilution = 32,
    #     scheduled_deletion = None
    # )


### Tests ######################################################################

class TestPartkeyBuffer:

    @staticmethod
    @pytest.mark.parametrize(
        "max_num_of_keys, num_of_keys, expected_is_full_result", 
        [
            (50, 10, False),
            (50, 49, False),
            (50, 50, True),
            (50, 51, True),
        ]
    )
    def test_is_full(
        partkey_buffer: PartkeyBuffer,
        max_num_of_keys: int,
        num_of_keys: int,
        expected_is_full_result: bool
    ):
        partkey_buffer.max_num_of_keys = max_num_of_keys
        partkey_buffer.partkeys = [i for i in range(num_of_keys)]
        assert partkey_buffer.is_full() == expected_is_full_result

    @staticmethod
    @pytest.mark.parametrize(
        "test_buffer_full", 
        [
            (False),
            (True),
        ]
    )
    def test_add_partkey_to_buffer(
        dummy_partkey: dict,
        partkey_buffer: object,
        test_buffer_full: bool
    ):
        if test_buffer_full:
            partkey_buffer.max_num_of_keys = 50
            partkey_buffer.partkeys = [i for i in range(partkey_buffer.max_num_of_keys)]
            with pytest.raises(RuntimeError):
                partkey_buffer.add_partkey_to_buffer(
                    dummy_partkey.address,
                    dummy_partkey.vote_first_valid,
                    dummy_partkey.vote_last_valid
                )
        else:
            partkey_buffer.add_partkey_to_buffer(
                dummy_partkey.address,
                dummy_partkey.vote_first_valid,
                dummy_partkey.vote_last_valid
            )
            for entry in partkey_buffer.return_partkeys():
                if entry['address'] == dummy_partkey.address:
                    assert True
                    return
            assert False

    @staticmethod
    def test_get_next(
        dummy_partkey,
        partkey_buffer
    ):
        partkey_buffer.add_partkey_to_buffer(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        res = partkey_buffer.get_next()
        assert all([
            res['address'] == dummy_partkey.address,
            res['vote-first-valid'] == dummy_partkey.vote_first_valid,
            res['vote-last-valid'] == dummy_partkey.vote_last_valid
        ])

    @staticmethod
    def test_get_next_empty(
        partkey_buffer
    ):
        assert partkey_buffer.get_next() == None

    @staticmethod
    def test_is_empty_true(
        partkey_buffer
    ):
        assert partkey_buffer.is_empty()

    @staticmethod
    def test_is_empty_false(
        dummy_partkey,
        partkey_buffer
    ):
        for i in range(3):
            partkey_buffer.add_partkey_to_buffer(
                dummy_partkey.address,
                dummy_partkey.vote_first_valid,
                dummy_partkey.vote_last_valid
            )
        assert not partkey_buffer.is_empty()

    @staticmethod
    def test_pop_partkey_from_buffer(
        dummy_partkey,
        partkey_buffer
    ):
        for i in range(3):
            partkey_buffer.add_partkey_to_buffer(
                dummy_partkey.address,
                dummy_partkey.vote_first_valid,
                dummy_partkey.vote_last_valid
            )
        assert len(partkey_buffer.partkeys) == 3
        partkey_buffer.pop_partkey_from_buffer()
        assert len(partkey_buffer.partkeys) == 2

    @staticmethod
    def test_is_partkey_in_buffer(
        dummy_partkey,
        partkey_buffer
    ):
        res = partkey_buffer.is_partkey_in_buffer(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert res == False
        partkey_buffer.add_partkey_to_buffer(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        res = partkey_buffer.is_partkey_in_buffer(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert res == True

    @staticmethod
    def test_return_partkeys(
        dummy_partkey,
        partkey_buffer
    ):
        partkey_buffer.add_partkey_to_buffer(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert partkey_buffer.return_partkeys() == partkey_buffer.partkeys



class TestPartkeyManager:

    @staticmethod
    @pytest.mark.parametrize(
        "return_target", 
        [
            (PARTKEY_GENERATION_REQUEST_OK_ADDED),
            (PARTKEY_GENERATION_REQUEST_FAIL_IN_PENDING),
            (PARTKEY_GENERATION_REQUEST_FAIL_IN_GENERATED),
            (PARTKEY_GENERATION_REQUEST_FAIL_PENDING_FULL),
            (PARTKEY_GENERATION_REQUEST_FAIL_GENERATED_FULL),
            (PARTKEY_GENERATION_REQUEST_FAIL_ALGOD_ERROR),
            (PARTKEY_GENERATION_REQUEST_FAIL_IN_THE_PAST)
        ]
    )
    def test_add_partkey_generation_request(
        algorand_client,
        partkey_manager,
        dummy_partkey,
        return_target
    ):
        
        if return_target == PARTKEY_GENERATION_REQUEST_FAIL_ALGOD_ERROR:
            partkey_manager.algorand_client.client.algod.algod_address = "https://some.cloud"
        elif return_target == PARTKEY_GENERATION_REQUEST_FAIL_IN_THE_PAST:
            last_round = algorand_client.client.algod.status()['last-round']
            delta = dummy_partkey.vote_last_valid - last_round
            dummy_partkey.vote_first_valid -= delta
            dummy_partkey.vote_last_valid -= delta
        elif return_target == PARTKEY_GENERATION_REQUEST_FAIL_IN_PENDING:
            partkey_manager.buffer_pending.add_partkey_to_buffer(
                address=dummy_partkey.address,
                vote_first_valid=dummy_partkey.vote_first_valid,
                vote_last_valid=dummy_partkey.vote_last_valid,
                vote_key_dilution=dummy_partkey.vote_key_dilution,
                scheduled_deletion=dummy_partkey.scheduled_deletion
            )
        elif return_target == PARTKEY_GENERATION_REQUEST_FAIL_IN_GENERATED:
            partkey_manager.buffer_generated.add_partkey_to_buffer(
                address=dummy_partkey.address,
                vote_first_valid=dummy_partkey.vote_first_valid,
                vote_last_valid=dummy_partkey.vote_last_valid,
                vote_key_dilution=dummy_partkey.vote_key_dilution,
                scheduled_deletion=dummy_partkey.scheduled_deletion
            )
        elif return_target == PARTKEY_GENERATION_REQUEST_FAIL_PENDING_FULL:
            partkey_manager.buffer_pending.max_num_of_keys = 50
            partkey_manager.buffer_pending.partkeys = [i for i in range(50)]
        elif return_target == PARTKEY_GENERATION_REQUEST_FAIL_GENERATED_FULL:
            partkey_manager.buffer_generated.max_num_of_keys = 50
            partkey_manager.buffer_generated.partkeys = [i for i in range(50)]
        res = partkey_manager.add_partkey_generation_request(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert res == return_target
        # for entry in partkey_manager.buffer_pending.return_partkeys():
        #     if entry['address'] == dummy_partkey.address:
        #         assert True
        #         return
        # assert False

    # @staticmethod
    # def test_add_partkey_generation_request_fail_in_pending(
    #     partkey_manager,
    #     dummy_partkey
    # ):
    #     partkey_manager.buffer_pending.add_partkey_to_buffer(
    #         dummy_partkey.address,
    #         dummy_partkey.vote_first_valid,
    #         dummy_partkey.vote_last_valid
    #     )
    #     with pytest.raises(RuntimeError):
    #         partkey_manager.add_partkey_generation_request(
    #             dummy_partkey.address,
    #             dummy_partkey.vote_first_valid,
    #             dummy_partkey.vote_last_valid
    #         )

    # @staticmethod
    # def test_add_partkey_generation_request_fail_in_generated(
    #     partkey_manager,
    #     dummy_partkey
    # ):
    #     partkey_manager.buffer_generated.add_partkey_to_buffer(
    #         dummy_partkey.address,
    #         dummy_partkey.vote_first_valid,
    #         dummy_partkey.vote_last_valid
    #     )
    #     with pytest.raises(RuntimeError):
    #         partkey_manager.add_partkey_generation_request(
    #             dummy_partkey.address,
    #             dummy_partkey.vote_first_valid,
    #             dummy_partkey.vote_last_valid
    #         )

    @staticmethod
    @pytest.mark.parametrize(
        "num_of_new_partkeys, num_of_loaded_partkeys", 
        [
            (0, 1), # One already in buffer, no need to add extra
            (1, 0), # Add one to buffer
            (0, 4), # Four already in buffer, no need to add extra
            (4, 0), # Add four to buffer
            (2, 2), # Two already in buffer, add two more
        ]
    )
    def test_try_adding_generated_keys_to_buffer(
        algorand_client: AlgorandClient,
        partkey_manager: PartkeyManager,
        dummy_partkey_factory: Callable,
        num_of_new_partkeys: int,
        num_of_loaded_partkeys: int
    ):
        """Verify that already-generated partkeys get added on request to the partkey buffer.

        Parameters
        ----------
        algorand_client : AlgorandClient
            Algorand client.
        partkey_manager : PartkeyManager
            The participation key manager of the Daemon.
        dummy_partkey_factory : Callable
            Generator of dummy participation key parameters for testing purpose.
        num_of_new_partkeys : int
            Number of participation keys that will need adding to buffer.
        num_of_loaded_partkeys : int
            Number of participation keys that will need already be in the to buffer.
        """
        # Set up partkeys
        new_partkeys = [dummy_partkey_factory() for i in range(num_of_new_partkeys)]
        loaded_partkeys = [dummy_partkey_factory() for i in range(num_of_loaded_partkeys)]
        for partkey in new_partkeys + loaded_partkeys:
            # Cleanup
            try_to_delete_partkey( # Initial cleanup if partkey exists
                algorand_client,
                partkey.address,
                partkey.vote_first_valid,
                partkey.vote_last_valid
            )
            # Generate key manually (without partkey manager)
            generate_partkey(
                algorand_client,
                partkey.address,
                partkey.vote_first_valid,
                partkey.vote_last_valid
            )
            time.sleep(
                calc_sleep_time_for_partkey_generation(partkey.vote_last_valid - partkey.vote_first_valid)
            )
            exists = does_partkey_exist(
                algorand_client,
                partkey.address,
                partkey.vote_first_valid,
                partkey.vote_last_valid
            )
            assert exists == True
        # Add some partkeys to buffer (these are 'already loaded')
        for partkey in loaded_partkeys:
            partkey_manager.buffer_generated.add_partkey_to_buffer(
                partkey.address,
                partkey.vote_first_valid,
                partkey.vote_last_valid
            )
        # Check that the partkey manager includes only the 'already loaded' partkeys
        assert len(partkey_manager.buffer_generated.partkeys) == num_of_loaded_partkeys
        # Add to partkey manager (the Daemon would call this based on info from Delegator Contract)
        res = partkey_manager.try_adding_generated_keys_to_buffer([pk_info.to_dict() for pk_info in new_partkeys])
        assert res == num_of_new_partkeys
        # Check that buffer includes both 'already loaded' and 'new' partkeys
        assert len(partkey_manager.buffer_generated.partkeys) == num_of_loaded_partkeys + num_of_new_partkeys
        # Final check that the partkey parameters are in order
        for partkey_inf, partkey_buf in zip(loaded_partkeys + new_partkeys, partkey_manager.buffer_generated.partkeys):
            entry = get_existing_partkey_parameters( # Fetch partkey parameters from node
                algorand_client,
                partkey_inf.address,
                partkey_inf.vote_first_valid,
                partkey_inf.vote_last_valid
            )
            assert partkey_buf['address'] == entry['address']
            assert partkey_buf['vote-first-valid'] == entry['key']['vote-first-valid']
            assert partkey_buf['vote-last-valid'] == entry['key']['vote-last-valid']
        # Cleanup
        for partkey in loaded_partkeys + new_partkeys:
            try_to_delete_partkey(
                algorand_client,
                partkey.address,
                partkey.vote_first_valid,
                partkey.vote_last_valid
            )


    @staticmethod
    def test_generate_partkey(
        algorand_client,
        partkey_manager,
        dummy_partkey
    ):
        # Cleanup
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        # Check that keys don't already exist
        if does_partkey_exist(
            algorand_client, 
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        ):
            raise RuntimeError('Found existing keys associated with the address.')
        res = partkey_manager.generate_partkey(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid,
            dummy_partkey.vote_key_dilution
        )
        assert res == 0
        # Wait for processing
        time.sleep(
            calc_sleep_time_for_partkey_generation(dummy_partkey.vote_last_valid - dummy_partkey.vote_first_valid)
        )
        assert does_partkey_exist(
            algorand_client, 
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        # Cleanup
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )

    @staticmethod
    def test_generate_partkey_busy(
        algorand_client,
        partkey_manager,
        dummy_partkey
    ):
        # Cleanup
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        res_first = partkey_manager.generate_partkey(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid + 100_000
        )
        assert res_first == 0
        res_second = partkey_manager.generate_partkey(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert res_second == 1
        # Wait for processing
        # sleep_time = calc_sleep_time_for_partkey_generation(
        #     dummy_partkey.vote_last_valid + 100_000 - dummy_partkey.vote_first_valid
        # )
        # time.sleep(sleep_time)
        time.sleep(10)
        assert does_partkey_exist(
            algorand_client, 
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid + 100_000
        )
        # Cleanup
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid + 100_000
        )

    @staticmethod
    def test_generate_partkey_error(
        partkey_manager,
        dummy_partkey
    ):
        with pytest.raises(AlgodHTTPError):
            partkey_manager.generate_partkey(
                dummy_partkey.address,
                dummy_partkey.vote_first_valid,
                -1
            )

    @staticmethod
    def test_get_existing_partkey_parameters(
        algorand_client,
        partkey_manager,
        dummy_partkey
    ):
        # Cleanup
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        res_first = partkey_manager.generate_partkey(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        # assert res_first == 0
        time.sleep(
            calc_sleep_time_for_partkey_generation(dummy_partkey.vote_last_valid - dummy_partkey.vote_first_valid)
        )
        res = partkey_manager.get_existing_partkey_parameters(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert all([
            res['address'] == dummy_partkey.address,
            res['vote-first-valid'] == dummy_partkey.vote_first_valid,
            res['vote-last-valid'] == dummy_partkey.vote_last_valid
        ])
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )

    @staticmethod
    def test_get_existing_partkey_parameters_error(
        algorand_client,
        partkey_manager,
        dummy_partkey
    ):
        # Cleanup
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        res = partkey_manager.get_existing_partkey_parameters(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert res is None
        # with pytest.raises(RuntimeError):
        #     partkey_manager.get_existing_partkey_parameters(
        #         dummy_partkey.address,
        #         dummy_partkey.vote_first_valid,
        #         dummy_partkey.vote_last_valid
        #     )


    # @staticmethod
    # def test_generate_next_partkey(
    #     algorand_client,
    #     partkey_manager,
    #     dummy_partkey
    # ):
    #     # Cleanup
    #     try_to_delete_partkey(
    #         algorand_client,
    #         dummy_partkey.address,
    #         dummy_partkey.vote_first_valid,
    #         dummy_partkey.vote_last_valid
    #     )
    #     partkey_manager.add_partkey_generation_request(
    #         dummy_partkey.address,
    #         dummy_partkey.vote_first_valid,
    #         dummy_partkey.vote_last_valid
    #     )
    #     partkey_manager.generate_next_partkey()
    #     time.sleep(
    #         calc_sleep_time_for_partkey_generation(dummy_partkey.vote_last_valid - dummy_partkey.vote_first_valid)
    #     )
    #     assert does_partkey_exist(
    #         algorand_client, 
    #         dummy_partkey.address,
    #         dummy_partkey.vote_first_valid,
    #         dummy_partkey.vote_last_valid
    #     )
    #     # Cleanup
    #     try_to_delete_partkey(
    #         algorand_client,
    #         dummy_partkey.address,
    #         dummy_partkey.vote_first_valid,
    #         dummy_partkey.vote_last_valid
    #     )


    @staticmethod
    def test_move_next_partkey_to_generated_buffer(
        algorand_client,
        partkey_manager,
        dummy_partkey
    ):
        # Cleanup
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        partkey_manager.buffer_pending.add_partkey_to_buffer(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert len(partkey_manager.buffer_pending.partkeys) == 1
        assert len(partkey_manager.buffer_generated.partkeys) == 0
        res = partkey_manager.generate_partkey(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid,
        )
        assert res == 0
        # Wait for processing
        time.sleep(
            calc_sleep_time_for_partkey_generation(dummy_partkey.vote_last_valid - dummy_partkey.vote_first_valid)
        )
        assert does_partkey_exist(
            algorand_client, 
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        partkey_manager.move_next_partkey_to_generated_buffer()
        assert len(partkey_manager.buffer_pending.partkeys) == 0
        assert len(partkey_manager.buffer_generated.partkeys) == 1
        # Cleanup
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )


    @staticmethod
    def test_remove_old_entries_in_buffer_generated(
        algorand_client,
        partkey_manager,
        dummy_account,
        dummy_partkey
    ):
        delta_rounds = 3
        assert partkey_manager.buffer_generated.is_empty()
        partkey_manager.buffer_generated.add_partkey_to_buffer(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_first_valid + delta_rounds
        )
        generate_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_first_valid + delta_rounds
        )
        time.sleep(1)
        partkey_manager.remove_old_entries_in_buffer_generated()
        assert not partkey_manager.buffer_generated.is_empty()
        wait_for_rounds(
            algorand_client, 
            delta_rounds + 1
        )
        assert not partkey_manager.buffer_generated.is_empty()
        partkey_manager.remove_old_entries_in_buffer_generated()
        assert partkey_manager.buffer_generated.is_empty()


    # @staticmethod
    # def test_fetch_and_add_existing_partkeys_to_buffer_generated(
    #     algorand_client,
    #     partkey_manager,
    #     dummy_partkey
    # ):
    #     delete_existing_partkeys(algorand_client)
    #     account_list = [create_and_fund_account(algorand_client) for i in range(5)]
    #     for i, account in enumerate(account_list):
    #         generate_partkey(
    #             algorand_client,
    #             account.address,
    #             dummy_partkey.vote_first_valid,
    #             dummy_partkey.vote_last_valid
    #         )
    #         time.sleep(
    #             calc_sleep_time_for_partkey_generation(dummy_partkey.vote_last_valid - dummy_partkey.vote_first_valid)
    #         )
    #         if i < 2:
    #             partkey_manager.buffer_generated.add_partkey_to_buffer(
    #                 address=account.address,
    #                 vote_first_valid=dummy_partkey.vote_first_valid,
    #                 vote_last_valid=dummy_partkey.vote_last_valid
    #             )
    #     assert len(partkey_manager.buffer_generated.return_partkeys()) == 2
    #     partkey_manager.fetch_and_add_existing_partkeys_to_buffer_generated()
    #     res = algorand_client.client.algod.algod_request(
    #         'GET', 
    #         '/participation'
    #     )
    #     assert len(partkey_manager.buffer_generated.return_partkeys()) == 5
    #     delete_existing_partkeys(algorand_client)


    # @staticmethod
    # def test_fetch_and_add_existing_partkeys_to_buffer_generated_nothing_new(
    #     algorand_client,
    #     partkey_manager,
    #     dummy_partkey
    # ):
    #     delete_existing_partkeys(algorand_client)
    #     account_list = [create_and_fund_account(algorand_client) for i in range(5)]
    #     for i, account in enumerate(account_list):
    #         generate_partkey(
    #             algorand_client,
    #             account.address,
    #             dummy_partkey.vote_first_valid,
    #             dummy_partkey.vote_last_valid
    #         )
    #         time.sleep(
    #             calc_sleep_time_for_partkey_generation(dummy_partkey.vote_last_valid - dummy_partkey.vote_first_valid)
    #         )
    #         partkey_manager.buffer_generated.add_partkey_to_buffer(
    #             address=account.address,
    #             vote_first_valid=dummy_partkey.vote_first_valid,
    #             vote_last_valid=dummy_partkey.vote_last_valid
    #         )
    #     assert len(partkey_manager.buffer_generated.return_partkeys()) == 5
    #     partkey_manager.fetch_and_add_existing_partkeys_to_buffer_generated()
    #     res = algorand_client.client.algod.algod_request(
    #         'GET', 
    #         '/participation'
    #     )
    #     assert len(partkey_manager.buffer_generated.return_partkeys()) == 5
    #     delete_existing_partkeys(algorand_client)


    # @staticmethod
    # def test_fetch_and_add_existing_partkeys_to_buffer_generated_no_partkeys(
    #     algorand_client,
    #     partkey_manager,
    #     dummy_partkey
    # ):
    #     delete_existing_partkeys(algorand_client)
    #     assert len(partkey_manager.buffer_generated.return_partkeys()) == 0
    #     partkey_manager.fetch_and_add_existing_partkeys_to_buffer_generated()
    #     res = algorand_client.client.algod.algod_request(
    #         'GET', 
    #         '/participation'
    #     )
    #     assert len(partkey_manager.buffer_generated.return_partkeys()) == 0
    #     delete_existing_partkeys(algorand_client)


    @staticmethod
    def test_is_partkey_generated(
        algorand_client,
        partkey_manager,
        dummy_partkey
    ):
        # Cleanup
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        res = partkey_manager.is_partkey_generated(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert res == False
        res_first = partkey_manager.generate_partkey(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert res_first == 0
        time.sleep(
            calc_sleep_time_for_partkey_generation(dummy_partkey.vote_last_valid - dummy_partkey.vote_first_valid)
        )
        res = partkey_manager.is_partkey_generated(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert res == True
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )


    @staticmethod
    def test_get_partkey_id(
        algorand_client,
        partkey_manager,
        dummy_partkey
    ):
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        generate_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        time.sleep(
            calc_sleep_time_for_partkey_generation(dummy_partkey.vote_last_valid - dummy_partkey.vote_first_valid)
        )
        exists = does_partkey_exist(
            algorand_client, 
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert exists == True
        generated_partkey_id = get_partkey_id(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        fetched_partkey_id = partkey_manager.get_partkey_id(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert generated_partkey_id == fetched_partkey_id


    @staticmethod
    def test_delete_partkey_using_id(
        algorand_client,
        partkey_manager,
        dummy_partkey
    ):
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        generate_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        time.sleep(
            calc_sleep_time_for_partkey_generation(dummy_partkey.vote_last_valid - dummy_partkey.vote_first_valid)
        )
        exists = does_partkey_exist(
            algorand_client, 
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert exists == True
        generated_partkey_id = get_partkey_id(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        partkey_manager.delete_partkey_using_id(
            generated_partkey_id
        )
        exists = does_partkey_exist(
            algorand_client, 
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert exists == False


    @staticmethod
    def test_delete_partkey(
        algorand_client,
        partkey_manager,
        dummy_partkey
    ):
        partkey_manager.buffer_generated.add_partkey_to_buffer(
            address = dummy_partkey.address,
            vote_first_valid = dummy_partkey.vote_first_valid,
            vote_last_valid = dummy_partkey.vote_last_valid
        )
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        generate_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        time.sleep(
            calc_sleep_time_for_partkey_generation(dummy_partkey.vote_last_valid - dummy_partkey.vote_first_valid)
        )
        exists = does_partkey_exist(
            algorand_client, 
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert exists == True
        partkey_manager.delete_partkey(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        exists = does_partkey_exist(
            algorand_client, 
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert exists == False


    @staticmethod
    def test_delete_one_of_multiple_partkeys_for_single_address(
        algorand_client: AlgorandClient,
        partkey_manager: PartkeyManager,
        dummy_partkey: PartkeyInfo
    ):
        """Verify that only one partkey gets deleted even if multiple are present on the node for a single address.

        Parameters
        ----------
        algorand_client : AlgorandClient
            Algorand client.
        partkey_manager : PartkeyManager
            The participation key manager of the Daemon.
        dummy_partkey : object
            Dummy participation key parameters for testing purpose.
        """
        # Set params for additional key (same address, different validity)
        another_partkey = copy.deepcopy(dummy_partkey)
        another_partkey.vote_first_valid += 100
        another_partkey.vote_last_valid += 100
        assert another_partkey.address == dummy_partkey.address
        assert another_partkey.vote_first_valid == dummy_partkey.vote_first_valid + 100
        assert another_partkey.vote_last_valid == dummy_partkey.vote_last_valid + 100
        # Create both keys
        for partkey in [dummy_partkey, another_partkey]:
            partkey_manager.buffer_generated.add_partkey_to_buffer(
                address = partkey.address,
                vote_first_valid = partkey.vote_first_valid,
                vote_last_valid = partkey.vote_last_valid
            )
            try_to_delete_partkey(
                algorand_client,
                partkey.address,
                partkey.vote_first_valid,
                partkey.vote_last_valid
            )
            generate_partkey(
                algorand_client,
                partkey.address,
                partkey.vote_first_valid,
                partkey.vote_last_valid
            )
            time.sleep(
                calc_sleep_time_for_partkey_generation(partkey.vote_last_valid - partkey.vote_first_valid)
            )
            exists = does_partkey_exist(
                algorand_client, 
                partkey.address,
                partkey.vote_first_valid,
                partkey.vote_last_valid
            )
            assert exists == True
        # Delete the first key
        partkey_manager.delete_partkey(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        exists = does_partkey_exist(
            algorand_client, 
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert exists == False
        # Check that additional partkey exists
        exists = does_partkey_exist(
            algorand_client, 
            another_partkey.address,
            another_partkey.vote_first_valid,
            another_partkey.vote_last_valid
        )
        assert exists == True
        # Clean up additional partkey
        partkey_manager.delete_partkey(
            another_partkey.address,
            another_partkey.vote_first_valid,
            another_partkey.vote_last_valid
        )
        exists = does_partkey_exist(
            algorand_client, 
            another_partkey.address,
            another_partkey.vote_first_valid,
            another_partkey.vote_last_valid
        )
        assert exists == False


    @staticmethod
    def test_delete_partkey_no_touch_partkeys_on_node(
        algorand_client: AlgorandClient,
        partkey_manager: PartkeyManager,
        dummy_partkey: object
    ):
        """Check that deleting the Daemon's participation key leaves other partkeys on the node alone.

        Parameters
        ----------
        algorand_client : AlgorandClient
            Algorand client.
        partkey_manager : PartkeyManager
            The participation key manager of the Daemon.
        dummy_partkey : object
            Dummy participation key parameters for testing purpose.
        """
        # Determine another address for the second partkey on the node
        system_partkey = copy.deepcopy(dummy_partkey)
        system_partkey.address = algorand_client.account.random().address
        # Cleanup possible existing partkey entries
        for partkey in [dummy_partkey, system_partkey]:
            try_to_delete_partkey( # Initial cleanup if partkey exists
                algorand_client,
                partkey.address,
                partkey.vote_first_valid,
                partkey.vote_last_valid
            )
        # Add to PartkeyManager (deletion won't work without this)
        partkey_manager.buffer_generated.add_partkey_to_buffer(
            address = dummy_partkey.address,
            vote_first_valid = dummy_partkey.vote_first_valid,
            vote_last_valid = dummy_partkey.vote_last_valid
        )
        # Generate both keys manually
        for partkey in [dummy_partkey, system_partkey]:
            generate_partkey(
                algorand_client,
                partkey.address,
                partkey.vote_first_valid,
                partkey.vote_last_valid
            )
            time.sleep(
                calc_sleep_time_for_partkey_generation(partkey.vote_last_valid - partkey.vote_first_valid)
            )
            exists = does_partkey_exist(
                algorand_client, 
                partkey.address,
                partkey.vote_first_valid,
                partkey.vote_last_valid
            )
            assert exists == True
        # Delete 'the Valar key' using the PartkeyManager
        partkey_manager.delete_partkey(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        # Check if the 'the Valar key' has been deleted
        exists = does_partkey_exist(
            algorand_client, 
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert exists == False
        # Check if 'the external key' was left alone
        exists = does_partkey_exist(
            algorand_client, 
            system_partkey.address,
            system_partkey.vote_first_valid,
            system_partkey.vote_last_valid
        )
        assert exists == True
        # Final cleanup of 'the external key'
        try_to_delete_partkey(
            algorand_client, 
            system_partkey.address,
            system_partkey.vote_first_valid,
            system_partkey.vote_last_valid
        )
        exists = does_partkey_exist(
            algorand_client, 
            system_partkey.address,
            system_partkey.vote_first_valid,
            system_partkey.vote_last_valid
        )
        assert exists == False


    @staticmethod
    def test_delete_partkey_no_touch_not_in_buf(
        algorand_client: AlgorandClient,
        partkey_manager: PartkeyManager,
        dummy_partkey: object
    ):
        """Check that the daemon cannot delete a partkey which is not in its buffer (not generated by the daemon).

        Parameters
        ----------
        algorand_client : AlgorandClient
            Algorand client.
        partkey_manager : PartkeyManager
            The participation key manager of the Daemon.
        dummy_partkey : object
            Dummy participation key parameters for testing purpose.
        """
        system_partkey = dummy_partkey # Rename for consistency with other tests regarding external partkey
        # Cleanup possible existing partkey entries
        try_to_delete_partkey( # Initial cleanup if partkey exists
            algorand_client,
            system_partkey.address,
            system_partkey.vote_first_valid,
            system_partkey.vote_last_valid
        )
        # Do not add anything to buffer (the generated partkey is an external one on the node)
        # Generate the key manually
        generate_partkey(
            algorand_client,
            system_partkey.address,
            system_partkey.vote_first_valid,
            system_partkey.vote_last_valid
        )
        time.sleep(
            calc_sleep_time_for_partkey_generation(system_partkey.vote_last_valid - system_partkey.vote_first_valid)
        )
        exists = does_partkey_exist(
            algorand_client, 
            system_partkey.address,
            system_partkey.vote_first_valid,
            system_partkey.vote_last_valid
        )
        assert exists == True
        # Try to delete 'the external key' using the PartkeyManager (should not succeed)
        try: # Error raising evaluated in another test
            partkey_manager.delete_partkey(
                system_partkey.address,
                system_partkey.vote_first_valid,
                system_partkey.vote_last_valid
            )
        except: 
            pass # Should fail - another test evaluates if the exception is raised
        # 'The external key' should be left alone
        exists = does_partkey_exist(
            algorand_client, 
            system_partkey.address,
            system_partkey.vote_first_valid,
            system_partkey.vote_last_valid
        )
        assert exists == True
        # Final cleanup of 'the external key'
        try_to_delete_partkey(
            algorand_client, 
            system_partkey.address,
            system_partkey.vote_first_valid,
            system_partkey.vote_last_valid
        )
        exists = does_partkey_exist(
            algorand_client, 
            system_partkey.address,
            system_partkey.vote_first_valid,
            system_partkey.vote_last_valid
        )
        assert exists == False


    @staticmethod
    def test_delete_partkey_raise_not_in_buf(
        partkey_manager,
        dummy_partkey
    ):
        with pytest.raises(RuntimeError):
            partkey_manager.delete_partkey(
                dummy_partkey.address,
                dummy_partkey.vote_first_valid,
                dummy_partkey.vote_last_valid
            )        


    @staticmethod
    def test_delete_partkey_raise_not_generated(
        partkey_manager,
        dummy_partkey
    ):
        partkey_manager.buffer_generated.add_partkey_to_buffer(
            address = dummy_partkey.address,
            vote_first_valid = dummy_partkey.vote_first_valid,
            vote_last_valid = dummy_partkey.vote_last_valid
        )
        with pytest.raises(RuntimeError):
            partkey_manager.delete_partkey(
                dummy_partkey.address,
                dummy_partkey.vote_first_valid,
                dummy_partkey.vote_last_valid
            )     

        
    @staticmethod
    def test_refresh_generate(
        algorand_client,
        partkey_manager,
        dummy_partkey
    ):
        partkey_manager.buffer_pending.add_partkey_to_buffer(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        partkey_manager.refresh()
        time.sleep(
            calc_sleep_time_for_partkey_generation(dummy_partkey.vote_last_valid - dummy_partkey.vote_first_valid)
        )
        exists = does_partkey_exist(
            algorand_client, 
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert exists
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )

        
    @staticmethod
    def test_refresh_change_buffers(
        algorand_client,
        partkey_manager,
        dummy_partkey
    ):
        partkey_manager.buffer_pending.add_partkey_to_buffer(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        generate_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        time.sleep(
            calc_sleep_time_for_partkey_generation(dummy_partkey.vote_last_valid - dummy_partkey.vote_first_valid)
        )
        exists = does_partkey_exist(
            algorand_client, 
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert exists == True
        partkey_manager.busy_generating_partkey = True
        assert not partkey_manager.buffer_pending.is_empty()
        assert partkey_manager.buffer_generated.is_empty()
        partkey_manager.refresh()
        assert partkey_manager.buffer_pending.is_empty()
        assert not partkey_manager.buffer_generated.is_empty()
        try_to_delete_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )

        
    @staticmethod
    def test_refresh_remove_old(
        algorand_client,
        partkey_manager,
        dummy_account,
        dummy_partkey
    ):
        delta_rounds = 3
        assert partkey_manager.buffer_generated.is_empty()
        partkey_manager.buffer_generated.add_partkey_to_buffer(
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_first_valid + delta_rounds
        )
        generate_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_first_valid + delta_rounds
        )
        time.sleep(1)
        partkey_manager.refresh()
        assert not partkey_manager.buffer_generated.is_empty()
        wait_for_rounds(
            algorand_client, 
            delta_rounds + 1
        )
        assert not partkey_manager.buffer_generated.is_empty()
        partkey_manager.refresh()
        assert partkey_manager.buffer_generated.is_empty()


    @staticmethod
    def test_delete_scheduled_partkey(
        algorand_client,
        partkey_manager,
        dummy_partkey
    ):
        delta_rounds = 3
        partkey_manager.buffer_generated.add_partkey_to_buffer(
            address = dummy_partkey.address,
            vote_first_valid = dummy_partkey.vote_first_valid,
            vote_last_valid = dummy_partkey.vote_last_valid,
            scheduled_deletion = dummy_partkey.vote_first_valid + delta_rounds
        )
        generate_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        time.sleep(
            calc_sleep_time_for_partkey_generation(dummy_partkey.vote_last_valid - dummy_partkey.vote_first_valid)
        )
        wait_for_rounds(
            algorand_client, 
            delta_rounds + 1
        )
        exists = does_partkey_exist(
            algorand_client, 
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert exists == True
        partkey_manager.delete_scheduled_partkeys()
        exists = does_partkey_exist(
            algorand_client, 
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert exists == False


    @staticmethod
    def test_refresh_delete_scheduled_partkey(
        algorand_client,
        partkey_manager,
        dummy_partkey
    ):
        delta_rounds = 3
        partkey_manager.buffer_generated.add_partkey_to_buffer(
            address = dummy_partkey.address,
            vote_first_valid = dummy_partkey.vote_first_valid,
            vote_last_valid = dummy_partkey.vote_last_valid,
            scheduled_deletion = dummy_partkey.vote_first_valid + delta_rounds
        )
        generate_partkey(
            algorand_client,
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        time.sleep(
            calc_sleep_time_for_partkey_generation(dummy_partkey.vote_last_valid - dummy_partkey.vote_first_valid)
        )
        partkey_manager.refresh()
        exists = does_partkey_exist(
            algorand_client, 
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert exists == True
        wait_for_rounds(
            algorand_client, 
            delta_rounds + 1
        )
        partkey_manager.refresh()
        exists = does_partkey_exist(
            algorand_client, 
            dummy_partkey.address,
            dummy_partkey.vote_first_valid,
            dummy_partkey.vote_last_valid
        )
        assert exists == False
