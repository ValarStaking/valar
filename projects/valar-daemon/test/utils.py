"""Different helper / abstraction functions.
"""
import time
import threading
from typing import List, Tuple

from algokit_utils.beta.composer import PayParams
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils import is_localnet
from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer, 
    TransactionWithSigner
)
from algokit_utils.beta.composer import (
    AssetCreateParams,
    AssetTransferParams
)

from valar_daemon.constants import (
    VALAD_STATE_READY,
    VALAD_STATE_NOT_READY,
    VALAD_STATE_NOT_LIVE,
    DELCO_STATE_READY,
    DELCO_STATE_SUBMITTED,
    DELCO_STATE_LIVE,
    DELCO_STATE_ENDED_EXPIRED
)
from valar_daemon.AppWrapper import ValadAppWrapper, DelcoAppWrapper
from valar_daemon.utils import decode_validator_terms_time, DelegatorContractGlobalState


def send_payment(
    algorand_client: AlgorandClient, 
    sender: AddressAndSigner, 
    receiver_address: str, 
    amount: int
) -> None:
    """Send / issue a payment. 

    Args:
        sender (str): Sender address.
        receiver (str): Receiver address.
        amount (int): Amount.
    """
    atc = AtomicTransactionComposer()
    txn = TransactionWithSigner(
        algorand_client.transactions.payment(
            PayParams(
                sender=sender.address,
                receiver=receiver_address,
                amount=amount,
                extra_fee=0,
            )
        ),
        signer=sender.signer,
    )
    atc.add_transaction(txn)
    res = atc.execute(algorand_client.client.algod, 0)
    assert res, 'Transfer failed'


def send_payment_simple(
    algorand_client: AlgorandClient, 
    sender_address: str, 
    receiver_address: str, 
    amount: int
) -> None:
    """Send a payment using only addresses, without signer. 

    Args:
        sender (str): Sender address.
        receiver (str): Receiver address.
        amount (int): Amount.
    """
    algorand_client.send.payment(
        PayParams(
            sender=sender_address,
            receiver=receiver_address,
            amount=amount,
        )
    )


def send_asa(
    algorand_client: AlgorandClient, 
    sender: AddressAndSigner, 
    receiver_address: str, 
    amount: int, 
    asset_id: int
):
    """Send ASA.

    Parameters
    ----------
    algorand_client : AlgorandClient
        Algorand client.
    sender : AddressAndSigner
        The sender.
    receiver_address : str
        Address of the receiver.
    amount : int
        Amount of ASA sent.
    asset_id : int
        ID of the ASA to send.
    """
    # Create an instance of AtomicTransactionComposer
    atc = AtomicTransactionComposer()
    # Get suggested transaction parameters
    sp = algorand_client.client.algod.suggested_params()
    from algosdk.transaction import AssetTransferTxn
    # Create the asset transfer transaction
    txn = TransactionWithSigner(
        txn=AssetTransferTxn(
            sender=sender.address,
            sp=sp,
            receiver=receiver_address,
            amt=amount,
            index=asset_id
        ),
        signer=sender.signer
    )
    # Add the transaction to the composer
    atc.add_transaction(txn)
    # Execute the transaction
    res = atc.execute(algorand_client.client.algod, 0)
    assert res, 'ASA transfer failed'


def send_asa_simple(
    algorand_client: AlgorandClient, 
    sender_address: str, 
    receiver_address: str, 
    amount: int, 
    asset_id: int
):
    """Send ASA using only addresses, without signer.

    Parameters
    ----------
    algorand_client : AlgorandClient
        Algorand client.
    sender_address : str
        Address of the sender.
    receiver_address : str
        Address of the receiver.
    amount : int
        Amount of ASA sent.
    asset_id : int
        ID of the ASA to send.
    """
    algorand_client.send.asset_transfer(
        AssetTransferParams(
            sender=sender_address,
            receiver=receiver_address,
            amount=amount,
            asset_id=asset_id,
        )
    )


def create_account(
    algorand_client: AlgorandClient, 
) -> AddressAndSigner:
    """Make a new random account and fund it.

    Args:
        algorand_client (AlgorandClient): Algorand client.

    Returns:
        AddressAndSigner: New account.
    """
    account = algorand_client.account.random()
    return account


def create_and_fund_account(
    algorand_client: AlgorandClient, 
    amount: int=40_000_000
) -> AddressAndSigner:
    """Make a new random account and fund it.

    Args:
        algorand_client (AlgorandClient): Algorand client.

    Returns:
        AddressAndSigner: New funded account.
    """
    account = create_account(algorand_client)
    send_payment_simple(
        algorand_client=algorand_client,
        sender_address=algorand_client.account.dispenser().address,
        receiver_address=account.address,
        amount=amount,
    )
    return account


def create_funded_account_list(
    algorand_client: AlgorandClient,
    num_of_accounts: list
) -> List[AddressAndSigner]:
    """Create a number of funded accounts.

    Args:
        algorand_client (AlgorandClient): Algorand client.
        num_of_accounts (list): Number of accounts to create.

    Returns:
        List[AddressAndSigner]: Funded accounts.
    """
    acc_list = []
    for i in range(num_of_accounts):
        acc = create_and_fund_account(algorand_client)
        acc_list.append(acc)
    return acc_list


def wait_for_rounds(
    algorand_client: AlgorandClient,
    num_rounds: int,
    # acc: AddressAndSigner | None = None,
) -> None:
    """
    Wait for rounds to progress or progress them manually.

    Notes
    -----
    If on localnet, this is done by sending individual zero payment transactions.
    If on other networks, wait for more rounds to pass.

    Parameters
    ----------
    algorand_client: AlgorandClient
        Algorand client for the network connection.
    num_rounds : int
        Number of rounds to progress.
    """
    if is_localnet(algorand_client.client.algod):
        dispenser = algorand_client.account.dispenser()
        for _ in range(num_rounds):
            # Send the transaction
            txn = TransactionWithSigner(
                algorand_client.transactions.payment(
                    PayParams(
                        sender=dispenser.address,
                        receiver=dispenser.address,
                        amount=0,
                        extra_fee=0,
                    )
                ),
                signer=dispenser.signer,
            )
            atc = AtomicTransactionComposer()
            atc.add_transaction(txn)
            res = atc.execute(algorand_client.client.algod, 0)  # noqa: F841
            assert res, 'Round progression failed'
            # print(f"Transaction sent with txID: {res.tx_ids}")
    else:
        status = algorand_client.client.algod.status()
        current_round = status["last-round"]
        while (
            current_round + num_rounds
            > algorand_client.client.algod.status()["last-round"]
        ):
            time.sleep(3)
    return


class LocalnetRoundProgressor(object):

    def __init__(
        self,
        algorand_client,
        round_period_s,
    ):
        if not is_localnet(algorand_client.client.algod):
            raise RuntimeError('Only works on localnet.')
        self.run_flag = True
        self.algorand_client = algorand_client
        self.round_period_s = round_period_s
        self.acc = create_and_fund_account(algorand_client)

    def _trigger_round(self):
        wait_for_rounds(
            self.algorand_client,
            1,
            # self.acc
        )

    def stop(self):
        self.run_flag = False
        self.thread.join()

    def _run(self):
        while self.run_flag:
            self._trigger_round()
            time.sleep(self.round_period_s)

    def run(self):
        self.thread = threading.Thread(
            target=self._run
        )
        self.thread.start()


if __name__ == '__main__':

    algorand_client = AlgorandClient.default_local_net()
    algorand_client.set_suggested_params_timeout(0)

    lrp = LocalnetRoundProgressor(
        algorand_client,
        1
    )
    lrp.run()
    time.sleep(10)
    lrp.stop()


    # account = create_and_fund_account(algorand_client)
    # print(account)
    # from algosdk import mnemonic
    # print(mnemonic.from_private_key(account.signer.private_key))

    # send_simple_payment(
    #     algorand_client=algorand_client,
    #     sender_address=algorand_client.account.dispenser().address,
    #     receiver_address='WPONCVMVICV4DQHTE53O2BNQTWM5L57K55H3ZYRQSLHRIUOEJXNV2LW3ZQ',
    #     amount=100_000_000_000,
    # )


def translate_valad_state_to_noticeboard_util_class_action(
    valad_state: bytes
) -> str:
    """Get the `Noticeboard` action name for moving a validator ad to a certain state.

    Parameters
    ----------
    valad_state : bytes

    Returns
    -------
    str

    Raises
    ------
    ValueError
        Unknown state.
    """
    if valad_state == VALAD_STATE_READY:
        return "READY"
    elif valad_state == VALAD_STATE_NOT_READY:
        return "NOT_READY"
    elif valad_state == VALAD_STATE_NOT_LIVE:
        return "NOT_LIVE"
    else:
        raise ValueError(f'Unknown valad state {valad_state}')


def translate_delco_state_to_noticeboard_util_class_action(
    delco_state: bytes
) -> str:
    """Get the `Noticeboard` action name for moving a delegator contract to a certain state.

    Parameters
    ----------
    delco_state : bytes

    Returns
    -------
    str

    Raises
    ------
    ValueError
        Unknown state.
    """
    if delco_state == DELCO_STATE_READY:
        return "READY"
    elif delco_state == DELCO_STATE_SUBMITTED:
        return "SUBMITTED"
    elif delco_state == DELCO_STATE_LIVE:
        return "LIVE"
    elif delco_state == DELCO_STATE_ENDED_EXPIRED:
        return "ENDED_EXPIRED"
    else:
        raise ValueError(f'Unknown valad state {delco_state}')


def create_asset(
    algorand_client: AlgorandClient,
    asset_issuer: AddressAndSigner,
    asset_name: str,
    unit_name: str,
    total_amount: int=42_000_000_000_000_000
):
    """Generate an Algorand Standard Asset (ASA).

    Parameters
    ----------
    algorand_client : AlgorandClient
        Algorand client.
    asset_issuer : AddressAndSigner
        Account that issues the token.
    asset_name : str
        Name of the token itself.
    unit_name : str
        Unit name of the token.
    total_amount : int, optional
        Number of generated tokens, by default 42_000_000_000_000_000

    Returns
    -------
    int
        The ID of the created asset.
    """
    res = algorand_client.send.asset_create(
        AssetCreateParams(
            sender=asset_issuer.address,
            total = total_amount,
            decimals = 6,
            default_frozen = False,
            manager = asset_issuer.address,
            reserve = asset_issuer.address,
            freeze = asset_issuer.address,
            clawback = asset_issuer.address,
            unit_name = unit_name,
            asset_name = asset_name,
        )
    )
    return res["confirmation"]["asset-index"]


def get_asset_amount_from_account_info(
    asset_list: List[dict], 
    asset_id: int
) -> int:
    """Get the amount of an asset in the accounts possession.

    Parameters
    ----------
    asset_list : List[dict]
        A list of assets from `algorand_client.client.algod.account_info(address)['assets']`
    asset_id : int
        The target asset's ID.

    Returns
    -------
    int
        Amount of the targeted asset.

    Raises
    ------
    ValueError
        Could not find asset with the ID.
    """
    for asset in asset_list:
        if asset['asset-id'] == asset_id:
            return asset['amount']
    raise ValueError(f'Could not find asset with ID {asset_id}.')


def get_min_asa_limit_from_gating_asa_list(
    gating_asa_list: List[Tuple[int, int]], 
    asset_id: int
) -> int:
    """Get the minimal limit for a gating asa.

    Parameters
    ----------
    gating_asa_list : list
        A list of assets from `DelegatorContractGlobalState.delegation_terms_balance.gating_asa_list`
    asset_id : int
        The target asset's ID.

    Returns
    -------
    int
        Minimal limit of the targeted asset.

    Raises
    ------
    ValueError
        Could not find asset with the ID.
    """
    for asset in gating_asa_list:
        if asset[0] == asset_id:
            return asset[1]
    raise ValueError(f'Could not find asset with ID {asset_id}.')


### Partkey management ################################################################################################

def does_partkey_exist(
        algorand_client, 
        address,
        vote_first_valid,
        vote_last_valid
    ):
    res = get_partkey_id(
        algorand_client, 
        address,
        vote_first_valid,
        vote_last_valid
    )
    if res is None:
        return False
    else: 
        return True


def get_partkey_id(
        algorand_client, 
        address,
        vote_first_valid,
        vote_last_valid
    ):
    partkeys = algorand_client.client.algod.algod_request(
        'GET', 
        '/participation'
    )
    if partkeys is not None:
        for pk in partkeys:
            if (
                pk['address'] == address and 
                pk['key']['vote-first-valid'] == vote_first_valid and 
                pk['key']['vote-last-valid'] == vote_last_valid
            ):
                return pk['id']
    return None
    

def generate_partkey(
    algorand_client,
    address,
    vote_first_valid,
    vote_last_valid
):
    algorand_client.client.algod.algod_request(
        'POST', 
        f'/participation/generate/{address}',
        params=dict(
            first=vote_first_valid,
            last=vote_last_valid
        )
    )


def calc_sleep_time_for_partkey_generation(
    duration: int,
    sleep_factor: float=0.002
) -> float:
    """Calculate the requires sleep time to generate partkeys with given duration.

    Parameters
    ----------
    duration : int
        Duration in rounds.
    sleep_factor : float, optional
        Sleep time for each duration round, by default 0.002

    Returns
    -------
    float
        Sleep time in seconds.
    """
    return sleep_factor * duration

def try_to_delete_partkey(
    algorand_client,
    address,
    vote_first_valid,
    vote_last_valid
):
    pk_id = get_partkey_id(
        algorand_client, 
        address,
        vote_first_valid,
        vote_last_valid
    )
    try: # Fails in case non-existent
        algorand_client.client.algod.algod_request(
            'DELETE', 
            f'/participation/{pk_id}'
        )
    except:
        pass


def delete_existing_partkeys(
    algorand_client
):
    res = algorand_client.client.algod.algod_request(
        'GET', 
        '/participation'
    )
    if res is not None:
        for entry in res:
            try_to_delete_partkey(
                algorand_client,
                entry['address'],
                entry['key']['vote-first-valid'],
                entry['key']['vote-last-valid']
            )

def wait_for_rounds_until_not_submitted(
    algorand_client: AlgorandClient,
    valad_app: ValadAppWrapper,
    delco_app: DelcoAppWrapper
):
    """Wait for until it is no longer possible to submit participation keys.

    Parameters
    ----------
    algorand_client : AlgorandClient
    valad_app : ValadAppWrapper
    delco_app : DelcoAppWrapper
    """
    delco_state = delco_app.delco_client.get_global_state().state.as_bytes
    if delco_state != DELCO_STATE_READY:
        raise RuntimeError(f'Delco with ID {delco_app.app_id} is not in READY state ({delco_state})')
    delco_gs = DelegatorContractGlobalState.from_global_state(delco_app.delco_client.get_global_state())
    terms_time = decode_validator_terms_time(valad_app.valad_client.get_global_state().terms_time.as_bytes)
    confirm_by_round = delco_gs.round_start + terms_time.rounds_setup
    current_round = algorand_client.client.algod.status()["last-round"]
    num_rounds = confirm_by_round - current_round
    if num_rounds < 0:
        raise RuntimeError(f'Negative number of rounds to progress for delco with ID {delco_app.app_id}')
    wait_for_rounds(
        algorand_client=algorand_client,
        num_rounds=num_rounds
    )

def get_existing_partkey_parameters(
    algorand_client: AlgorandClient,
    address: str,
    vote_first_valid: int,
    vote_last_valid: int
) -> dict:
    """Obtain the relevant parameters of an already generated partkey.

    Parameters
    ----------
    algorand_client : AlgorandClient
        Algorand client.
    address : str
        Address of participating entity.
    vote_first_valid : int
        First round when the partkeys are valid.
    vote_last_valid : int
        Last round when the partkeys are valid.

    Returns
    -------
    dict
        Partkey address and first/last valid parameters. None if did not find the partkey for <address>.
    """
    res = algorand_client.client.algod.algod_request(
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
                return entry
    return None
