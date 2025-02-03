import { NoticeboardClient } from "@/contracts/Noticeboard";
import { NoticeboardGlobalState } from "@/interfaces/contracts/Noticeboard";
import { UserInfo } from "@/interfaces/contracts/User";
import { UserApiBuilder } from "@/utils/api-builder/UserApiBuilder";
import { strToBytes } from "@/utils/convert";
import { AlgorandClient, microAlgos } from "@algorandfoundation/algokit-utils";
import { TransactionSigner } from "algosdk";

export class UserApiCall {
  /**
   * ================================
   *         User Create
   * ================================
   */

  static async userCreate({
    algorandClient,
    noticeBoardClient,
    gsNoticeBoard,
    userAddress,
    userRole,
    signer,
  }: {
    algorandClient: AlgorandClient;
    noticeBoardClient: NoticeboardClient;
    gsNoticeBoard: NoticeboardGlobalState;
    userAddress: string;
    userRole: string;
    signer: TransactionSigner;
  }) {
    const { feeTxn, txnParams, boxesUser } = await UserApiBuilder.userCreate({
      algorandClient,
      gsNoticeBoard,
      userAddress,
      userRole,
      signer,
    });

    const res = await noticeBoardClient.userCreate(
      {
        userRole: strToBytes(userRole),
        txn: feeTxn,
      },
      {
        sendParams: { fee: microAlgos(txnParams.fee) },
        boxes: boxesUser,
      },
    );

    console.log(res);
  }

  /**
   * ================================
   *         User Delete
   * ================================
   */

  static async userDelete({
    algorandClient,
    noticeBoardClient,
    userAddress,
    userInfo,
  }: {
    algorandClient: AlgorandClient;
    noticeBoardClient: NoticeboardClient;
    userAddress: string;
    userRole: Uint8Array;
    userInfo: UserInfo;
    signer: TransactionSigner;
  }) {
    const { txnParams, boxesUser } = await UserApiBuilder.userDelete({ userAddress, userInfo });

    const res = await noticeBoardClient.userDelete(
      {},
      { sendParams: { fee: microAlgos(txnParams.fee) }, boxes: boxesUser },
    );
    console.log("User Deleted :", res);
  }

  /**
   * =======================================
   *  Deprecated Calls
   * =======================================
   */

  // export async function depositIncrease({
  //   algorandClient,
  //   noticeBoardClient,
  //   userAddress,
  //   deposit,
  //   signer,
  // }: {
  //   algorandClient: AlgorandClient
  //   noticeBoardClient: NoticeboardClient
  //   userAddress: string
  //   deposit: number
  //   signer: TransactionSigner
  // }) {
  //   const { txnParams, feeTxn, boxesUser } = await UserApiBuilder.depositIncrease({
  //     algorandClient,
  //     userAddress,
  //     deposit,
  //     signer,
  //   })

  //   const res = await noticeBoardClient.depositIncrease(
  //     { txn: feeTxn },
  //     {
  //       sendParams: { fee: microAlgos(txnParams.fee) },
  //       boxes: boxesUser,
  //     },
  //   )

  //   console.log('Dep Incr::', res)
  // }

  // export async function depositReduce({
  //   algorandClient,
  //   noticeBoardClient,
  //   userAddress,
  //   amount,
  // }: {
  //   algorandClient: AlgorandClient
  //   noticeBoardClient: NoticeboardClient
  //   userAddress: string
  //   amount: number
  // }) {
  //   const { txnParams, boxesUser } = await UserApiBuilder.depositDecrease({ algorandClient, userAddress })

  //   const res = await noticeBoardClient.depositReduce(
  //     {
  //       amt: amount,
  //     },
  //     {
  //       boxes: boxesUser,
  //       sendParams: { fee: microAlgos(txnParams.fee) },
  //     },
  //   )
  //   console.log('Dep Decr ::', res)
  // }
}
