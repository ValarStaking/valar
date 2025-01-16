import copy
import dataclasses

from algosdk.abi import AddressType, ArrayStaticType, ByteType, TupleType, UintType
from algosdk.constants import ZERO_ADDRESS

from smart_contracts.artifacts.noticeboard.client import (
    GlobalState,
    NoticeboardAssetInfo,
    NoticeboardFees,
    NoticeboardTermsNodeLimits,
    NoticeboardTermsTiming,
)

DEFAULT_NOTICEBOARD_FEES = NoticeboardFees(
    commission_min = 0,
    val_user_reg=0,
    del_user_reg=0,
    val_ad_creation=0,
    del_contract_creation=0,
)

DEFAULT_SETUP_NOTICEBOARD_TERMS_TIMING = NoticeboardTermsTiming(
    rounds_duration_min_min = 0,
    rounds_duration_max_max = 0,
    before_expiry = 0,
    report_period = 0,
)
DEFAULT_SETUP_NOTICEBOARD_TERMS_STAKE = NoticeboardTermsNodeLimits(
    stake_max_max = 0,
    stake_max_min = 0,
    cnt_del_max_max = 0,
)

# ----- Were not generated by Puya -----
@dataclasses.dataclass(kw_only=True)
class UsersDoubleLinkedList:
    cnt_users: int
    user_first: str
    user_last: str

DEFAULT_DLL = UsersDoubleLinkedList(
    cnt_users=0,
    user_first=ZERO_ADDRESS,
    user_last=ZERO_ADDRESS,
)

# ----- Expanded box data wrappers -----
@dataclasses.dataclass()
class UserInfo:
    """
    UserInfo(): Creates a new object with user info with all values initialized to zero by default.
    """
    role: bytes = b""
    dll_name: bytes = b""

    prev_user: str = ZERO_ADDRESS
    next_user: str = ZERO_ADDRESS

    app_ids: list[int] = dataclasses.field(default_factory=lambda: [0] * 110)
    cnt_app_ids: int = 0

    @classmethod
    def from_bytes(cls, data: bytes) -> "UserInfo":
        data_type = TupleType(
            [
                ArrayStaticType(ByteType(), 4),    # role
                ArrayStaticType(ByteType(), 8),    # dll_name
                AddressType(),   # prev_user
                AddressType(),   # next_user
                ArrayStaticType(UintType(64), 110),   # app_ids
                UintType(64),   # cnt_app_ids
            ]
        )
        decoded_tuple = data_type.decode(data)

        return UserInfo(
            role=bytes(decoded_tuple[0]),
            dll_name=bytes(decoded_tuple[1]),
            prev_user=decoded_tuple[2],
            next_user=decoded_tuple[3],
            app_ids= decoded_tuple[4],
            cnt_app_ids=decoded_tuple[5],
        )

    def get_free_app_idx(self) -> int | None:
        return self.get_app_idx(0)

    def get_app_idx(self, app_id: int) -> int | None:
        try:
            val_app_idx = self.app_ids.index(app_id)
        except ValueError:
            val_app_idx = None
        return val_app_idx

#---------------------------------------------

@dataclasses.dataclass(kw_only=True)
class NoticeboardGlobalState:
    pla_manager: str = ZERO_ADDRESS

    tc_sha256: bytes = bytes(32)

    noticeboard_fees: NoticeboardFees = dataclasses.field(default_factory=lambda: copy.deepcopy(DEFAULT_NOTICEBOARD_FEES))  # noqa: E501
    noticeboard_terms_timing: NoticeboardTermsTiming = dataclasses.field(default_factory=lambda: copy.deepcopy(DEFAULT_SETUP_NOTICEBOARD_TERMS_TIMING))  # noqa: E501
    noticeboard_terms_node: NoticeboardTermsNodeLimits = dataclasses.field(default_factory=lambda: copy.deepcopy(DEFAULT_SETUP_NOTICEBOARD_TERMS_STAKE))  # noqa: E501

    state: bytes = b"\x00"

    app_id_new: int = 0
    app_id_old: int = 0

    dll_del: UsersDoubleLinkedList = dataclasses.field(default_factory=lambda: DEFAULT_DLL)
    dll_val: UsersDoubleLinkedList = dataclasses.field(default_factory=lambda: DEFAULT_DLL)

    @classmethod
    def from_global_state(cls, gs: GlobalState) -> "NoticeboardGlobalState":
        return cls(
            pla_manager=decode_abi_address(gs.pla_manager.as_bytes),
            tc_sha256=gs.tc_sha256.as_bytes,
            noticeboard_fees=decode_noticeboard_fees(gs.noticeboard_fees.as_bytes),
            noticeboard_terms_timing=decode_noticeboard_terms_timing(gs.noticeboard_terms_timing.as_bytes),
            noticeboard_terms_node=decode_noticeboard_terms_node(gs.noticeboard_terms_node.as_bytes),
            state=gs.state.as_bytes,
            app_id_new=gs.app_id_new,
            app_id_old=gs.app_id_old,
            dll_del= decode_user_double_linked_list(gs.dll_del.as_bytes),
            dll_val= decode_user_double_linked_list(gs.dll_val.as_bytes),
        )

    @classmethod
    def with_defaults(cls) -> "NoticeboardGlobalState":
        return cls()


def decode_abi_address(data: bytes) -> str:
    return AddressType().decode(data)


def decode_noticeboard_fees(data: bytes) -> NoticeboardFees:
    noticeboard_fees_type = TupleType(
        [
            UintType(64),   # commission_min
            UintType(64),   # val_user_reg
            UintType(64),   # del_user_reg
            UintType(64),   # val_ad_creation
            UintType(64),   # del_contract_creation
        ]
    )

    decoded_tuple = noticeboard_fees_type.decode(data)

    noticeboard_fees = NoticeboardFees(
        commission_min=decoded_tuple[0],
        val_user_reg=decoded_tuple[1],
        del_user_reg=decoded_tuple[2],
        val_ad_creation=decoded_tuple[3],
        del_contract_creation=decoded_tuple[4],
    )

    return noticeboard_fees


def decode_noticeboard_terms_timing(data: bytes) -> NoticeboardTermsTiming:
    data_type = TupleType(
        [
            UintType(64),   # rounds_duration_min_min
            UintType(64),   # rounds_duration_max_max
            UintType(64),   # before_expiry
            UintType(64),   # report_period
        ]
    )

    decoded_tuple = data_type.decode(data)

    decoded_data = NoticeboardTermsTiming(
        rounds_duration_min_min=decoded_tuple[0],
        rounds_duration_max_max=decoded_tuple[1],
        before_expiry=decoded_tuple[2],
        report_period=decoded_tuple[3],
    )

    return decoded_data

def decode_noticeboard_terms_node(data: bytes) -> NoticeboardTermsNodeLimits:
    data_type = TupleType(
        [
            UintType(64),   # stake_max_max
            UintType(64),   # stake_max_min
            UintType(64),   # cnt_del_max_max
        ]
    )

    decoded_tuple = data_type.decode(data)

    decoded_data = NoticeboardTermsNodeLimits(
        stake_max_max=decoded_tuple[0],
        stake_max_min=decoded_tuple[1],
        cnt_del_max_max=decoded_tuple[2],
    )

    return decoded_data

def decode_user_double_linked_list(data: bytes) -> UsersDoubleLinkedList:
    user_double_linked_list_type = TupleType(
        [
            UintType(64),   # cnt_users
            AddressType(),  # user_first
            AddressType(),  # user_last
        ]
    )

    decoded_tuple = user_double_linked_list_type.decode(data)

    dll = UsersDoubleLinkedList(
        cnt_users=decoded_tuple[0],
        user_first=decoded_tuple[1],
        user_last=decoded_tuple[2],
    )

    return dll

def decode_noticeboard_asset_box(data: bytes) -> NoticeboardAssetInfo:
    d_type = TupleType(
        [
            ByteType(),     # accepted
            UintType(64),   # fee_round_min_min
            UintType(64),   # fee_round_var_min
            UintType(64),   # fee_setup_min
        ]
    )

    decoded_tuple = d_type.decode(data)

    decoded_data = NoticeboardAssetInfo(
        accepted=decoded_tuple[0] != 0,
        fee_round_min_min=decoded_tuple[1],
        fee_round_var_min=decoded_tuple[2],
        fee_setup_min=decoded_tuple[3],
    )

    return decoded_data
