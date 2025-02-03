import { ASA_ID_ALGO, BOX_ASA_KEY_PREFIX, ROLE_DEL } from "@/constants/smart-contracts";
import { DC_STATE_ENDED_EXPIRED, DC_STATE_ENDED_NOT_CONFIRMED, DC_STATE_ENDED_NOT_SUBMITTED } from "@/constants/states";
import { NoticeboardClient } from "@/contracts/Noticeboard";
import { DelegatorContractGlobalState } from "@/interfaces/contracts/DelegatorContract";
import { NoticeboardGlobalState } from "@/interfaces/contracts/Noticeboard";
import { PartnerInfo } from "@/interfaces/contracts/Partners";
import { UserInfo } from "@/interfaces/contracts/User";
import { ValidatorAdGlobalState } from "@/interfaces/contracts/ValidatorAd";
import { KeyRegParams } from "@/lib/types";
import { AccountInfo, User } from "@/store/userStore";
import { DelegatorApiBuilder } from "@/utils/api-builder/DelegatorApiBuilder";
import { bytesToHex, bytesToStr, strToBytes } from "@/utils/convert";
import { TxnParams } from "@/utils/txn-params";
import { AlgorandClient, microAlgos } from "@algorandfoundation/algokit-utils";
import { BoxReference } from "@algorandfoundation/algokit-utils/types/app";
import { bigIntToBytes, TransactionSigner } from "algosdk";

export class DelegatorApiCall {
  /**
   * ================================
   *          Contract Create
   * ================================
   */

  static async contractCreate({
    algorandClient,
    noticeBoardClient,
    gsNoticeBoard,
    gsValidatorAd,
    userAddress,
    maxStake,
    duration,
    delBeneficiary,
    partner,
    delUserInfo,
    signer,
  }: {
    algorandClient: AlgorandClient;
    noticeBoardClient: NoticeboardClient;
    gsNoticeBoard: NoticeboardGlobalState;
    gsValidatorAd: ValidatorAdGlobalState;
    userAddress: string;
    maxStake: bigint;
    duration: bigint;
    delBeneficiary: string;
    partner?: PartnerInfo;
    delUserInfo: UserInfo;
    signer: TransactionSigner;
  }) {
    const {
      tcSha256,
      foreignApps,
      foreignAssets,
      foreignAccounts,
      valAppId,
      valAppIdx,
      delAppIdx,
      valOwner,
      partnerAddress,
      boxesDel_ValAd,
      boxesContractCreate,
      txnParams,
      mbrTxn,
      feeTxn,
    } = await DelegatorApiBuilder.contractCreate({
      algorandClient,
      gsNoticeBoard,
      gsValidatorAd,
      userAddress,
      partner,
      delUserInfo,
      stakeMax: maxStake,
      roundsDuration: duration,
      delBeneficiary,
      signer,
    });

    const res = await noticeBoardClient
      .compose()
      .gas(
        {},
        {
          sender: {
            addr: userAddress,
            signer,
          },
          boxes: boxesDel_ValAd,
          assets: foreignAssets,
          apps: foreignApps,
        },
      )
      .contractCreate(
        {
          delBeneficiary: delBeneficiary,
          roundsDuration: duration,
          stakeMax: maxStake,
          valOwner,
          valApp: valAppId,
          valAppIdx,
          delAppIdx,
          tcSha256,
          partnerAddress,
          mbrTxn,
          txn: feeTxn,
        },
        {
          sender: {
            addr: userAddress,
            signer,
          },
          boxes: boxesContractCreate,
          assets: foreignAssets,
          accounts: foreignAccounts,
          sendParams: { fee: microAlgos(txnParams.fee) },
        },
      )
      .execute();

    return res;
  }

  // // Validator Claimg Any Pending Earning from a Delegator Contract
  // export async function contractClaim({
  //   algorandClient,
  //   noticeBoardClient,
  //   userAddress,
  //   valAppId,
  //   delAppId,
  //   signer,
  // }: {
  //   algorandClient: AlgorandClient
  //   noticeBoardClient: NoticeboardClient
  //   userAddress: string
  //   valAppId: bigint
  //   delAppId: bigint
  //   signer: TransactionSigner
  // }) {
  //   //Fetching ValAd and Noticeboard Global-state
  //   const gsDel = await getDelegatorContractGlobalState(algorandClient.client.algod, delAppId)
  //   const gsVal = await getValidatorAdGlobalState(algorandClient.client.algod, valAppId)

  //   const delManager = gsDel!.delManager
  //   const valOwner = gsVal!.valOwner

  //   //Creating Manager Box
  //   const managerVal = new User(ROLE_VAL, delManager)
  //   const managerDel = new User(ROLE_DEL, delManager)
  //   const boxesDelManager: BoxReference[] = [
  //     { appId: 0, name: managerVal.toBoxName() },
  //     { appId: 0, name: managerDel.toBoxName() },
  //   ]

  //   const ownerVal = new User(ROLE_VAL, valOwner)
  //   const ownerDel = new User(ROLE_DEL, valOwner)
  //   const boxesValOwner: BoxReference[] = [
  //     { appId: 0, name: ownerVal.toBoxName() },
  //     { appId: 0, name: ownerDel.toBoxName() },
  //   ]

  //   const boxesUser = [...boxesDelManager, ...boxesValOwner]

  //   //Get index in validator's list at which the validator ad is stored
  //   const valUserInfo = await getUserInfo(algorandClient.client.algod, BigInt(noticeboardAppID), ownerVal)
  //   const valAppIdx = valUserInfo!.getAppIndex(valAppId)

  //   const delUserInfo = await getUserInfo(algorandClient.client.algod, BigInt(noticeboardAppID), managerDel)
  //   const delAppIdx = delUserInfo!.getAppIndex(delAppId)

  //   const feeAssetId = gsDel!.delegationTermsGeneral.feeAssetId
  //   let boxesAsset: BoxReference[] = []
  //   if (feeAssetId != ASA_ID_ALGO) {
  //     boxesAsset = [{ appId: valAppId, name: new Uint8Array([...BOX_ASA_KEY_PREFIX, ...bigIntToBytes(feeAssetId, 8)]) }]
  //   }

  //   //Txn Params
  //   const txnParams = await TxnParams.getSuggestedTxnParams(algorandClient.client.algod)
  //   txnParams.fee = 5 * txnParams.minFee
  //   txnParams.flatFee = true

  //   const res = await noticeBoardClient.contractClaim(
  //     {
  //       delApp: delAppId,
  //       valApp: valAppId,
  //       valOwner,
  //       delManager,
  //       valAppIdx,
  //       delAppIdx,
  //     },
  //     {
  //       sender: {
  //         addr: userAddress,
  //         signer,
  //       },
  //       boxes: [...boxesUser, ...boxesAsset],
  //       assets: [Number(feeAssetId)],
  //       accounts: [delManager],
  //       sendParams: { fee: microAlgos(txnParams.fee) },
  //     },
  //   )

  //   console.log(res)

  //   return res
  // }

  /**
   * ================================
   *         Contract Delete
   * ================================
   */

  static async contractDelete({
    algorandClient,
    noticeBoardClient,
    gsValAd,
    gsDelCo,
    userAddress,
    delUserInfo,
    signer,
  }: {
    algorandClient: AlgorandClient;
    noticeBoardClient: NoticeboardClient;
    gsValAd: ValidatorAdGlobalState;
    gsDelCo: DelegatorContractGlobalState;
    userAddress: string;
    delUserInfo: UserInfo;
    signer: TransactionSigner;
  }) {
    const { delAppId, valAppId, delAppIdx, valAppIdx, valOwner, foreignAssets, boxesContractDelete, txnParams } =
      await DelegatorApiBuilder.contractDelete({
        algorandClient,
        gsValAd,
        gsDelCo,
        userAddress,
        delUserInfo,
      });

    const atc = noticeBoardClient.compose();

    const stateCur = bytesToStr(gsDelCo.stateCur);
    const state = bytesToStr(gsDelCo.state);
    if (stateCur !== state) {
      const delManager = gsDelCo.delManager;
      const partnerAddress = gsDelCo.delegationTermsGeneral.partnerAddress;
      const foreignAccounts = [delManager, partnerAddress];
      let boxesAsset: BoxReference[] = [];
      const assetId = gsDelCo.delegationTermsGeneral.feeAssetId;
      if (assetId != ASA_ID_ALGO) {
        boxesAsset = [
          {
            appId: Number(valAppId),
            name: new Uint8Array([...BOX_ASA_KEY_PREFIX, ...bigIntToBytes(assetId, 8)]),
          },
        ];
      }
      const boxes = [...boxesContractDelete, ...boxesAsset];
      // Correct state has not yet been reported, thus another txn is needed.
      if (stateCur === bytesToStr(DC_STATE_ENDED_NOT_SUBMITTED)) {
        atc.keysNotSubmitted(
          {
            delManager: delManager,
            delApp: delAppId,
            valApp: valAppId,
            valOwner,
            delAppIdx,
            valAppIdx,
          },
          {
            sender: {
              addr: userAddress,
              signer,
            },
            boxes: boxes,
            assets: foreignAssets,
            accounts: foreignAccounts,
            sendParams: { fee: microAlgos((await TxnParams.setTxnFees(6, true)).fee) },
          },
        );
      } else if (stateCur === bytesToStr(DC_STATE_ENDED_NOT_CONFIRMED)) {
        atc.keysNotConfirmed(
          {
            delManager: delManager,
            delApp: delAppId,
            valApp: valAppId,
            valOwner,
            delAppIdx,
            valAppIdx,
          },
          {
            sender: {
              addr: userAddress,
              signer,
            },
            boxes: boxes,
            assets: foreignAssets,
            accounts: foreignAccounts,
            sendParams: { fee: microAlgos((await TxnParams.setTxnFees(6, true)).fee) },
          },
        );
      } else if (stateCur === bytesToStr(DC_STATE_ENDED_EXPIRED)) {
        atc.contractExpired(
          {
            delManager: delManager,
            delApp: delAppId,
            valApp: valAppId,
            valOwner,
            delAppIdx,
            valAppIdx,
          },
          {
            sender: {
              addr: userAddress,
              signer,
            },
            boxes: boxes,
            assets: foreignAssets,
            accounts: foreignAccounts,
            sendParams: { fee: microAlgos((await TxnParams.setTxnFees(7, true)).fee) },
          },
        );
      } else {
        // Should not be possible
        console.error(
          "Unexpected difference in states (state, stateCur): ",
          bytesToHex(strToBytes(state)),
          bytesToHex(strToBytes(stateCur)),
        );
      }
    }

    atc.contractDelete(
      {
        delApp: delAppId,
        valApp: valAppId,
        valOwner,
        delAppIdx,
        valAppIdx,
      },
      {
        sender: {
          addr: userAddress,
          signer,
        },
        boxes: boxesContractDelete,
        assets: foreignAssets,
        sendParams: { fee: microAlgos(txnParams.fee) },
      },
    );

    const res = atc.execute();

    return res;
  }

  /**
   * ================================
   *         Contract Withdraw
   * ================================
   */
  static async contractWithdraw({
    algorandClient,
    noticeBoardClient,
    gsValAd,
    gsDelCo,
    user,
    signer,
  }: {
    algorandClient: AlgorandClient;
    noticeBoardClient: NoticeboardClient;
    gsValAd: ValidatorAdGlobalState;
    gsDelCo: DelegatorContractGlobalState;
    user: User;
    signer: TransactionSigner;
  }) {
    const {
      delAppId,
      valAppId,
      delAppIdx,
      valAppIdx,
      valOwner,
      foreignAssets,
      foreignAccounts,
      txns,
      boxesContractWithdraw,
      txnParams,
    } = await DelegatorApiBuilder.contractWithdraw({
      algorandClient,
      gsValAd,
      gsDelCo,
      user,
      signer,
    });

    const ntc = noticeBoardClient.compose();

    txns.forEach((txn) => {
      ntc.addTransaction({
        txn,
        signer,
      });
    });

    ntc.contractWithdraw(
      {
        delApp: delAppId,
        delAppIdx,
        valOwner,
        valApp: valAppId,
        valAppIdx,
      },
      {
        sender: {
          addr: user.address,
          signer,
        },
        boxes: boxesContractWithdraw,
        assets: foreignAssets,
        accounts: foreignAccounts,
        sendParams: { fee: microAlgos(txnParams.fee) },
      },
    );

    const res = ntc.execute();

    return res;
  }

  /**
   * ==================================
   *       Contract Keys Confirm
   * ==================================
   */

  static async keysConfirm({
    algorandClient,
    noticeBoardClient,
    gsValAd,
    gsDelCo,
    user,
    signer,
  }: {
    algorandClient: AlgorandClient;
    noticeBoardClient: NoticeboardClient;
    gsValAd: ValidatorAdGlobalState;
    gsDelCo: DelegatorContractGlobalState;
    user: User;
    signer: TransactionSigner;
  }) {
    const { delAppId, valAppId, delAppIdx, valAppIdx, valOwner, txns, boxesKeysConfirm, txnParams } =
      await DelegatorApiBuilder.keysConfirm({
        algorandClient,
        gsValAd,
        gsDelCo,
        user,
        signer,
      });

    const ntc = noticeBoardClient.compose();

    txns.forEach((txn) => {
      ntc.addTransaction({
        txn,
        signer,
      });
    });

    ntc.keysConfirm(
      {
        delApp: delAppId,
        valApp: valAppId,
        valOwner,
        delAppIdx,
        valAppIdx,
      },
      {
        sender: {
          addr: user.address,
          signer,
        },
        boxes: boxesKeysConfirm,
        sendParams: { fee: microAlgos(txnParams.fee) },
      },
    );

    const res = await ntc.execute();

    return res;
  }

  /**
   * =====================================
   *     User Create & Contract Create
   * =====================================
   */

  static async userCreateAndContractCreate({
    algorandClient,
    noticeBoardClient,
    gsNoticeBoard,
    gsValidatorAd,
    userAddress,
    maxStake,
    duration,
    delBeneficiary,
    partner,
    signer,
  }: {
    algorandClient: AlgorandClient;
    noticeBoardClient: NoticeboardClient;
    gsNoticeBoard: NoticeboardGlobalState;
    gsValidatorAd: ValidatorAdGlobalState;
    userAddress: string;
    maxStake: bigint;
    duration: bigint;
    delBeneficiary: string;
    partner?: PartnerInfo;
    signer: TransactionSigner;
  }) {
    const {
      tcSha256,
      foreignApps,
      foreignAssets,
      foreignAccounts,
      valAppId,
      valAppIdx,
      delAppIdx,
      valOwner,
      partnerAddress,
      feeTxnUserCreate,
      boxesUserCreate,
      boxesDel_ValAd,
      boxesContractCreate,
      txnParams,
      mbrTxn,
      feeTxn,
    } = await DelegatorApiBuilder.userCreateAndContractCreate({
      algorandClient,
      gsNoticeBoard,
      gsValidatorAd,
      userAddress,
      partner,
      stakeMax: maxStake,
      roundsDuration: duration,
      delBeneficiary,
      signer,
    });

    const res = await noticeBoardClient
      .compose()
      .userCreate(
        {
          userRole: ROLE_DEL,
          txn: feeTxnUserCreate,
        },
        {
          sender: {
            addr: userAddress,
            signer,
          },
          boxes: boxesUserCreate,
        },
      )
      .gas(
        {},
        {
          sender: {
            addr: userAddress,
            signer,
          },
          boxes: boxesDel_ValAd,
          assets: foreignAssets,
          apps: foreignApps,
        },
      )
      .contractCreate(
        {
          delBeneficiary: delBeneficiary,
          roundsDuration: duration,
          stakeMax: maxStake,
          valOwner,
          valApp: valAppId,
          valAppIdx,
          delAppIdx,
          tcSha256,
          partnerAddress,
          mbrTxn,
          txn: feeTxn,
        },
        {
          sender: {
            addr: userAddress,
            signer,
          },
          boxes: boxesContractCreate,
          assets: foreignAssets,
          accounts: foreignAccounts,
          sendParams: { fee: microAlgos(txnParams.fee) },
        },
      )
      .execute();

    return res;
  }
}
