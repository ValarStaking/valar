import { NoticeboardGlobalState } from "@/interfaces/contracts/Noticeboard";
import { UserInfo } from "@/interfaces/contracts/User";
import { noticeboardAppID } from "@/constants/platform";
import { AlgorandClient, microAlgos } from "@algorandfoundation/algokit-utils";
import { BoxReference } from "@algorandfoundation/algokit-utils/types/app";
import { getApplicationAddress, TransactionSigner } from "algosdk";
import { BoxUtils } from "../contract/box-utils";
import { TxnParams } from "../txn-params";
import { MAX_TXN_VALIDITY, MBR_USER_BOX, ROLE_VAL_STR } from "@/constants/smart-contracts";

export class UserApiBuilder {
  /**
   * ================================
   *          User Create
   * ================================
   */

  static async userCreate({
    algorandClient,
    gsNoticeBoard,
    userAddress,
    userRole,
    signer,
  }: {
    algorandClient: AlgorandClient;
    gsNoticeBoard: NoticeboardGlobalState;
    userAddress: string;
    userRole: string;
    signer: TransactionSigner;
  }) {
    const userRegFees =
      userRole === ROLE_VAL_STR
        ? Number(gsNoticeBoard!.noticeboardFees.valUserReg)
        : Number(gsNoticeBoard!.noticeboardFees.delUserReg);

    const amount: number = MBR_USER_BOX + userRegFees;
    const noticeboardAddress = getApplicationAddress(noticeboardAppID);

    //MBR Increase
    const feeTxn = await algorandClient.transactions.payment({
      sender: userAddress,
      receiver: noticeboardAddress,
      amount: microAlgos(amount),
      validityWindow: MAX_TXN_VALIDITY,
      signer,
    });

    //Getting Last User
    const userLast =
      userRole === ROLE_VAL_STR
        ? gsNoticeBoard.dllVal.userLast
        : gsNoticeBoard.dllDel.userLast;

    const boxesUser: BoxReference[] = BoxUtils.createBoxes(0, [
      userAddress,
      userLast,
    ]);

    const txnParams = await TxnParams.setTxnFees(1, true);

    return { feeTxn, txnParams, boxesUser };
  }

  /**
   * ================================
   *          User Delete
   * ================================
   */

  static async userDelete({
    userAddress,
    userInfo,
  }: {
    userAddress: string;
    userInfo: UserInfo;
  }) {
    const boxesUser = BoxUtils.createBoxes(0, [
      userAddress,
      userInfo.prevUser,
      userInfo.nextUser,
    ]);

    const txnParams = await TxnParams.setTxnFees(2, true);

    return { txnParams, boxesUser };
  }

}
