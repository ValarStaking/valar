"""App wrapper definitions for caching the state of contracts and keeping reference to the corresponding clients.
"""
import logging
from typing import List, Tuple
from urllib.error import URLError

from algosdk.encoding import encode_address
from algokit_utils.beta.algorand_client import AlgorandClient
from algosdk.error import AlgodHTTPError

from valar_daemon.Logger import Logger
from valar_daemon.ValidatorAdClient import (
    ValidatorAdClient,
    GlobalState as ValidatorAdGlobalState
)
from valar_daemon.DelegatorContractClient import (
    DelegatorContractClient,
    GlobalState as DelegatorContractGlobalState
)
from valar_daemon.NoticeboardClient import NoticeboardClient
from valar_daemon.utils import (
    get_delco_fee_and_gating_asa_id,
    decode_delegation_terms_general,
    decode_uint64_list
)
from valar_daemon.constants import (
    VALAD_STATE_DELETED_MASK,
    DELCO_STATE_DELETED_MASK
)


class AppWrapper(object):
    """Smart contract (app) wrapper."""

    def __init__(self):
        pass


class ValadAppWrapper(AppWrapper):
    """Validator Ad wrapper.

    Attributes
    ----------
    algorand_client: AlgorandClient
        Algorand client.
    app_id: int
        Validator Ad application ID.
    valad_client: ValidatorAdClient
        Validator ad client.
    notbd_client: NoticeboardClient
        Noticeboard client.
    valown_address: str
        Address of the validator owner.
    delco_id_list: list
        [dynamic] List of the IDs of connected delegator contracts.
    state: bytes
        [dynamic] State of the validator ad.
    """
    def __init__(
        self,
        algorand_client: AlgorandClient,
        app_id: int
    ):
        """Validator Ad wrapper, used for storing the client and relevant parameters for the daemon's operation.

        Parameters
        ----------
        algorand_client : AlgorandClient
            Algorand client.
        app_id : int
            Validator Ad ID.
        """
        self.app_id = app_id
        self.valad_client = ValidatorAdClient(
            algorand_client.client.algod,
            app_id=app_id
        )
        # Fetch global state and populate corresponding attributes
        valad_global_state = self.update_dynamic(propagate_deleted_error=True)
        self.notbd_client = NoticeboardClient(
            algorand_client.client.algod,
            app_id=valad_global_state.noticeboard_app_id
        )
        self.notbd_client.get_global_state() # Try to see if it can be connected to (error caught in upper layers)
        self.valown_address = encode_address(valad_global_state.val_owner.as_bytes)

    def update_dynamic(
            self,
            propagate_deleted_error: bool=True
        ) -> object:
        """Update the dynamic parts of the valad app.

        Notes
        -----
        Can handle non-existent error and set the state accordingly.

        Parameters
        ----------
        propagate_deleted_error : bool, optional
            If true, does not handle any errors that are raised, by default True

        Returns
        -------
        object
            The app's global state.

        Raises
        ------
        e
            Given error type.
        """
        try:
            valad_global_state = self.valad_client.get_global_state()
        except AlgodHTTPError as e:
            # Update to show the thing was deleted
            if not propagate_deleted_error and e.code == 404 and e.args[0] == 'application does not exist':
                self.state = VALAD_STATE_DELETED_MASK
                return None
            else:
                raise e
        except Exception as e: # Must be last to capture AlgodHTTPError first and execute corresponding logic
            raise e
        self.delco_id_list = ValadAppWrapper.get_delco_id_list(valad_global_state)
        self.state = valad_global_state.state.as_bytes
        return valad_global_state

    @staticmethod
    def get_delco_id_list(
        valad_global_state: ValidatorAdGlobalState
    ):
        """Get list of IDs of delcos that are associated with the valad (between, including, ready and live state).

        Parameters
        ----------
        valad_global_state : ValidatorAdGlobalState
            Get the global state of the valad.

        Returns
        -------
        List
            IDs of the associated delcos.
        """
        delco_id_list = decode_uint64_list(
            # valad_app.valad_client.get_global_state().del_app_list.as_bytes
            valad_global_state.del_app_list.as_bytes
        )
        return [i for i in delco_id_list if i != 0]


class DelcoAppWrapper(AppWrapper):
    """Delegator Contract wrapper.

    Attributes
    ----------
    app_id: int
        Delegator Contract application ID.
    delco_client: DelegatorContractClient
        Delegator contract client.
    notbd_client: NoticeboardClient
        Noticeboard client.
    valad_id: int
        Validator Ad app ID.
    delman_address: str
        Delegator manager address.
    delben_address: str
        Delegator beneficiary address.
    fee_asa_id: int
        Asset ID for issuing payment.
    gating_asa_id_list: List[Tuple(int, int)]
        Gating asset IDs and their minimal values.
    round_start: int
        Staking start (partkey validity).
    round_end: int
        Staking end (partkey validity).
    valown_address: int
        Validator owner address.
    partner_address: int
        Address of the partner that forwarded the delegator.
    round_ended: int
        [dynamic] Round at which the contract ended.
    state: bytes
        [dynamic] State of the validator ad.
    """
    def __init__(
        self,
        algorand_client,
        app_id: int
    ):
        """Delegator Contract wrapper, used for storing the client and relevant parameters for the daemon's operation.

        Parameters
        ----------
        algorand_client : AlgorandClient
            Algorand client.
        app_id : int
            Delegator Contract ID.
        """
        self.app_id = app_id
        self.delco_client = DelegatorContractClient(
            algorand_client.client.algod,
            app_id=app_id
        )
        delco_global_state = self.update_dynamic(propagate_deleted_error=True)
        self.notbd_client = NoticeboardClient(
            algorand_client.client.algod,
            app_id=delco_global_state.noticeboard_app_id
        )
        self.notbd_client.get_global_state() # Try to see if it can be connected to (error caught in upper layers)
        self.valad_id = delco_global_state.validator_ad_app_id
        self.delman_address = encode_address(delco_global_state.del_manager.as_bytes)
        self.delben_address = encode_address(delco_global_state.del_beneficiary.as_bytes)
        self.fee_asa_id, self.gating_asa_id_list = get_delco_fee_and_gating_asa_id(delco_global_state)
        self.round_start = delco_global_state.round_start
        self.round_end = delco_global_state.round_end
        # self.round_end = delco_global_state.round_end + 320 # Account for initial 320 round delay
        # self.round_key_delete = self.round_end # Default value - contract end and key deletion can be earlier
        valad_client = ValidatorAdClient(
                algorand_client.client.algod,
                app_id=delco_global_state.validator_ad_app_id
            )
        valad_global_state = valad_client.get_global_state()
        self.valown_address = encode_address(valad_global_state.val_owner.as_bytes)
        self.partner_address = decode_delegation_terms_general(
            delco_global_state.delegation_terms_general.as_bytes
        ).partner_address

    def get_partkey_params(self) -> dict:
        """Get the basic participation key parameters for identifying a specific key.

        Returns
        -------
        dict
            Address, first round, and last round.
        """
        return {
            'address': self.delben_address,
            'vote-first-valid': self.round_start,
            'vote-last-valid': self.round_end
        }

    def update_dynamic(
            self,
            propagate_deleted_error: bool=True
        ) -> DelegatorContractGlobalState:
        """Update the dynamic parts of the delco app.

        Notes
        -----
        Can handle non-existent error and set the state accordingly.

        Parameters
        ----------
        propagate_deleted_error : bool, optional
            If true, does not handle any errors that are raised, by default True

        Returns
        -------
        DelegatorContractGlobalState
            The app's global state.

        Raises
        ------
        e
            Given error type.
        """
        try:
            delco_global_state = self.delco_client.get_global_state()
        except AlgodHTTPError as e:
            # Update to show the thing was deleted
            if not propagate_deleted_error and e.code == 404 and e.args[0] == 'application does not exist':
                self.state = DELCO_STATE_DELETED_MASK
                return None
            else:
                raise e
        except Exception as e:
            raise e
        self.state = delco_global_state.state.as_bytes
        self.round_ended = delco_global_state.round_ended
        return delco_global_state


class AppWrapperList(object):
    """List of app wrappers.

    Attributes
    ----------
    algorand_client : AlgorandClient
        Algorand client.
    logger : logging.Logger
        Logger.
    AppWrapperClass: AppWrapper
        Either `ValadAppWrapper` or `DelcoAppWrapper`.
    """
    def __init__(
        self,
        algorand_client: AlgorandClient,
        logger: Logger,
        AppWrapperClass: AppWrapper
    ):
        """List of app wrappers.

        Parameters
        ----------
        algorand_client : AlgorandClient
            Algorand client.
        AppWrapperClass : AppWrapper
            Either `ValadAppWrapper` or `DelcoAppWrapper`.
        """
        self.algorand_client = algorand_client
        self.logger = logger
        self.AppWrapperClass = AppWrapperClass
        self.app_list = []

    def get_app_list(
        self
    ) -> List[AppWrapper]:
        """Return the app list.

        Returns
        -------
        list
        """
        return self.app_list

    def get_id_list(
        self
    ) -> List[int]:
        """Get the IDs of the apps in the list.

        Returns
        -------
        List[int]
        """
        return [app.app_id for app in self.app_list]

    def add_single_app(
        self,
        app_id: int
    ):
        """Add an app to the list.

        Parameters
        ----------
        app_id : int
            ID of the app to add.

        Returns
        -------
        int
            Number of added apps (0 or 1).
        """
        app_wrapper = None
        # Try to connect the client and get state; log error if not successful
        try:
            app_wrapper = self.AppWrapperClass(self.algorand_client, app_id)
        except URLError as e:
            # self.logger.critical(f'For app ID {app_id}, URLError {e.args[0].errno}: {e.args[0].strerror}.')
            self.logger.log_app_create_urlerror(
                app_id=app_id, errno=e.args[0].errno, strerror=e.args[0].strerror
            )
            return 0
        except AlgodHTTPError as e:
            # self.logger.critical(f'AlgodHTTPError {e.code}: {e.args[0]}.')
            self.logger.log_app_create_algohttperror(
                app_id=app_id, errno=e.code, strerror=e.args[0]
            )
            return 0
        except Exception as e:
            # self.logger.error(e)
            self.logger.log_app_create_genericerror(app_id=app_id, e=e)
            return 0
        # Add app wrapper if successfully initialized
        self.app_list.append(app_wrapper)
        return 1

    def remove_single_app(
        self,
        app_id: int
    ) -> bool:
        """Remove an app from the list.

        Parameters
        ----------
        app_id : int

        Returns
        -------
        bool
            Flag that is `True` if the app was found and deleted.
        """
        for i, app in enumerate(self.app_list):
            if app.app_id == app_id:
                self.app_list.pop(i)
                return True
        return False

    def add_multiple_apps(
        self,
        app_id_list: List[int]
    ) -> int:
        """Add multiple apps to the list.

        Parameters
        ----------
        app_id_list : List[int]
            IDs of apps to add.

        Returns
        -------
        int
            Number of added apps.
        """
        existing_app_ids = self.get_id_list()
        num_of_added_apps = 0
        for app_id in app_id_list:
            if app_id not in existing_app_ids: # Only add new apps
                num_of_added_apps += self.add_single_app(app_id)
        return num_of_added_apps

    def remove_multiple_apps(
        self,
        app_id_list: List[int]
    ):
        """Remove multiple apps from the list.

        Parameters
        ----------
        app_id_list : List[int]
        """
        for app_id in app_id_list:
            self.remove_single_app(app_id)

    def update_apps(
        self
    ) -> Tuple[int, int]:
        """Update the dynamic parts of the connected apps.
        """
        num_of_apps = len(self.app_list)
        num_of_updated = 0
        for app in self.app_list:
            try:
                app.update_dynamic(propagate_deleted_error=False) # Assign 'deleted' state if exists
                num_of_updated += 1
            except Exception as e:
                # self.logger.error(e)
                self.logger.log_app_dynamic_update_genericerror(app_id=app.app_id, e=e)
        return (num_of_apps, num_of_updated)


class ValadAppWrapperList(AppWrapperList):
    """List of Validator Ad app wrappers.

    Attributes
    ----------
    algorand_client: AlgorandClient
        Algorand client.
    """
    def __init__(
        self,
        algorand_client: AlgorandClient,
        logger: logging.Logger
    ):
        """List of Validator Ad app wrappers.

        Parameters
        ----------
        algorand_client : AlgorandClient
            Algorand client.
        logger : logging.Logger
            Logger.
        """
        super().__init__(
            algorand_client=algorand_client,
            logger=logger,
            AppWrapperClass=ValadAppWrapper
        )


class DelcoAppWrapperList(AppWrapperList):
    """List of Delegator Contract app wrappers.

    Attributes
    ----------
    algorand_client : AlgorandClient
        Algorand client.
    logger : logging.Logger
        Logger.
    """
    def __init__(
        self,
        algorand_client: AlgorandClient,
        logger: logging.Logger
    ):
        """List of Delegator Contract app wrappers.

        Parameters
        ----------
        algorand_client : AlgorandClient
            Algorand client.
        """
        super().__init__(
            algorand_client=algorand_client,
            logger=logger,
            AppWrapperClass=DelcoAppWrapper
        )

    def get_partkey_params_list(self) -> List[dict]:
        """Get a list of participation keys.

        Returns
        -------
        List[dict]
            List of address, first round, and last round.
        """
        return [app.get_partkey_params() for app in self.app_list]
