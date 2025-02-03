import { AlgorandClient, microAlgos } from '@algorandfoundation/algokit-utils'
import { getApplicationAddress, TransactionSigner } from 'algosdk'
import { BoxUtils } from '../contract/box-utils'
import { noticeboardAppID } from '@/constants/platform'
import { BoxReference } from '@algorandfoundation/algokit-utils/types/app'
import { TxnParams } from '../txn-params'
import { NoticeboardGlobalState } from '@/interfaces/contracts/Noticeboard'
import { UserInfo } from '@/interfaces/contracts/User'
import { ValidatorAdGlobalState } from '@/interfaces/contracts/ValidatorAd'
import { bigIntToBytes, bytesToStr } from '../convert'
import { ASA_ID_ALGO, MAX_TXN_VALIDITY, MBR_ACCOUNT, MBR_ASA, MBR_NOTICEBOARD_VALIDATOR_AD_CONTRACT_INCREASE, MBR_USER_BOX, MBR_VALIDATOR_AD_ASA_BOX } from '@/constants/smart-contracts'
import { BOX_ASA_KEY_PREFIX, BOX_ASSET_KEY_PREFIX, BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY, BOX_SIZE_PER_REF, BOX_VALIDATOR_AD_TEMPLATE_KEY } from '@/constants/smart-contracts'
import { VA_STATE_CREATED, VA_STATE_NOT_READY, VA_STATE_READY } from '@/constants/states'

export class ValidatorApiBuilder {

  /**
   * ================================
   *          Ad Create
   * ================================
   */

  static async adCreate({
    algorandClient,
    gsNoticeBoard,
    userAddress,
    userInfo,
    signer,
  }: {
    algorandClient: AlgorandClient
    gsNoticeBoard: NoticeboardGlobalState
    userAddress: string
    userInfo: UserInfo
    signer: TransactionSigner
  }) {
    const amount = Number(gsNoticeBoard.noticeboardFees.valAdCreation) + MBR_NOTICEBOARD_VALIDATOR_AD_CONTRACT_INCREASE + MBR_ACCOUNT
    const noticeboardAddress = getApplicationAddress(noticeboardAppID)

    const feeTxn = await algorandClient.transactions.payment({
      sender: userAddress,
      receiver: noticeboardAddress,
      amount: microAlgos(amount),
      validityWindow: MAX_TXN_VALIDITY,
      signer,
    })

    const boxesUser = BoxUtils.createBoxes(0, [userAddress])

    //Add boxes for validator template (to load on creation)
    const boxVal = (await BoxUtils.getNoticeboardBox(algorandClient.client.algod, BOX_VALIDATOR_AD_TEMPLATE_KEY)).value
    const boxValSize = boxVal.length
    const numLoadVal = Math.ceil(boxValSize / BOX_SIZE_PER_REF)
    const boxesVal: BoxReference[] = new Array(numLoadVal).fill({ appId: 0, name: BOX_VALIDATOR_AD_TEMPLATE_KEY })

    const valAppIdx = userInfo.getFreeAppIndex()

    const txnParams = await TxnParams.setTxnFees(3, true)

    return {
      valAppIdx,
      feeTxn,
      txnParams,
      boxesAdCreate: [...boxesUser, ...boxesVal],
    }
  }


  /**
   * ================================
   *          Ad Terms
   * ================================
   */

  static async adTerms({
    algorandClient,
    gsValAd,
    userAddress,
    valAppId,
    valAssetId,
    userInfo,
    signer,
  }: {
    algorandClient: AlgorandClient
    gsValAd: ValidatorAdGlobalState | undefined
    userAddress: string
    valAppId: bigint
    valAssetId: bigint
    userInfo: UserInfo
    signer: TransactionSigner
  }) {
    const foreignApps = [Number(valAppId)]
    const valAppIdx = userInfo.getAppIndex(valAppId)

    const boxesUser = BoxUtils.createBoxes(0, [userAddress])

    let numTxn: number = 0
    let mbrDelegatorTemplateBox = 0
    let boxesDel_NoticeBoard: BoxReference[] = [] //DelApps Boxes in Noticeboard
    let boxesDel_ValidatorAd: BoxReference[] = [] //DelApps Boxes in ValidatorAd

    if (!gsValAd || bytesToStr(gsValAd.state) === bytesToStr(VA_STATE_CREATED)) {
      const boxDel = (await BoxUtils.getNoticeboardBox(algorandClient.client.algod, BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY)).value
      const boxDelSize = boxDel.length
      mbrDelegatorTemplateBox = BoxUtils.calculateBoxMBR(boxDelSize, BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY)

      const numLoadDel = Math.ceil(boxDelSize / BOX_SIZE_PER_REF)

      boxesDel_NoticeBoard = new Array(numLoadDel).fill({ appId: 0, name: BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY })
      boxesDel_ValidatorAd = new Array(numLoadDel).fill({ appId: Number(valAppId), name: BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY })
      numTxn = numTxn + 1 + numLoadDel + 1
    }

    //Foreign Assets
    let foreignAssets: number[] = []
    let validatorAdNewAssetFee = 0
    let boxAsa_ValidatorAd: BoxReference[] = [] //Add box for accessing ASA on ValidatorAd
    const boxAsa_NoticeBoard: BoxReference[] = [
      { appId: 0, name: new Uint8Array([...BOX_ASSET_KEY_PREFIX, ...bigIntToBytes(valAssetId, 8)]) },
    ]

    if (valAssetId != ASA_ID_ALGO) {
      foreignAssets = [Number(valAssetId)]
      if (!gsValAd || valAssetId != gsValAd.termsPrice.feeAssetId){
        // If it is a new payment asset, another fee must be paid
        validatorAdNewAssetFee = MBR_ASA + MBR_VALIDATOR_AD_ASA_BOX
      }
      boxAsa_ValidatorAd = [{ appId: Number(valAppId), name: new Uint8Array([...BOX_ASA_KEY_PREFIX, ...bigIntToBytes(valAssetId, 8)]) }]
      numTxn += 1
    }

    const amount = validatorAdNewAssetFee + mbrDelegatorTemplateBox

    const noticeboardAddress = getApplicationAddress(noticeboardAppID)
    const feeTxn = await algorandClient.transactions.payment({
      sender: userAddress,
      receiver: noticeboardAddress,
      amount: microAlgos(amount),
      validityWindow: MAX_TXN_VALIDITY,
      signer,
    })

    const txnParams = await TxnParams.setTxnFees(5 + numTxn, true)

    return {
      valAppIdx,
      foreignApps,
      foreignAssets,
      boxesDel_ValidatorAd,
      boxesDel_NoticeBoard,
      mbrDelegatorTemplateBox,
      feeTxn,
      boxesAdTerms: [...boxesUser, ...boxAsa_NoticeBoard, ...boxAsa_ValidatorAd],
      txnParams,
    }
  }


  /**
   * ================================
   *          Ad Config
   * ================================
   */

  static async adConfig({
    gsValidatorAd,
    userAddress,
    userInfo,
    valAppId,
  }: {
    gsValidatorAd: ValidatorAdGlobalState
    userAddress: string
    userInfo: UserInfo
    valAppId: bigint
  }) {
    const live = bytesToStr(gsValidatorAd.state) === bytesToStr(VA_STATE_NOT_READY) || bytesToStr(gsValidatorAd.state) === bytesToStr(VA_STATE_READY);
    const boxesUser = BoxUtils.createBoxes(0, [userAddress]);
    const valAppIdx = userInfo.getAppIndex(valAppId);
    const txnParams = await TxnParams.setTxnFees(2, true);

    return {
      live,
      valAppIdx,
      boxesAdConfig: boxesUser,
      txnParams,
    }
  }

  /**
   * ================================
   *          Ad Delete
   * ================================
   */

  static async adDelete({
    algorandClient,
    userAddress,
    userInfo,
    valAppId,
  }: {
    algorandClient: AlgorandClient
    userAddress: string
    userInfo: UserInfo
    valAppId: bigint
  }) {
    const foreignApps = [Number(valAppId)]
    const boxesUser = BoxUtils.createBoxes(0, [userAddress])
    const valAppIdx = userInfo.getAppIndex(valAppId)

    const boxDel = (await BoxUtils.getNoticeboardBox(algorandClient.client.algod, BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY)).value
    const boxDelSize = boxDel.length
    const numLoadDel = Math.ceil(boxDelSize / BOX_SIZE_PER_REF)
    const boxesDel_ValidatorAd = new Array(numLoadDel).fill({ appId: Number(valAppId), name: BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY })
    const txnParams = await TxnParams.setTxnFees(5, true)

    return {
      valAppIdx,
      foreignApps,
      boxesAdDelete: boxesUser,
      boxesDelVal: boxesDel_ValidatorAd,
      txnParams,
    }
  }


  /**
   * ================================
   *          Ad Self Disclose
   * ================================
   */

  static async adSelfDisclose({
    userAddress,
    userInfo,
    valAppId,
  }: {
    userAddress: string
    userInfo: UserInfo
    valAppId: bigint
  }) {
    const boxesUser = BoxUtils.createBoxes(0, [userAddress])
    const valAppIdx = userInfo.getAppIndex(valAppId)
    const txnParams = await TxnParams.setTxnFees(2, true)

    return {
      boxesASD: boxesUser,
      valAppIdx,
      txnParams,
    }
  }

  /**
   * ================================
   *          Ad Config
   * ================================
   */

  static async adIncome({
    userAddress,
    userInfo,
    valAppId,
    valAssetId,
  }: {
    userAddress: string
    userInfo: UserInfo
    valAppId: bigint
    valAssetId: bigint
  }) {
    const foreignAssets = valAssetId === ASA_ID_ALGO ? [] : [Number(valAssetId)]
    const boxesUser = BoxUtils.createBoxes(0, [userAddress])
    const valAppIdx = userInfo.getAppIndex(valAppId)
    const txnParams = await TxnParams.setTxnFees(3, true)

    return {
      foreignAssets,
      valAppIdx,
      boxesAdIncome: boxesUser,
      txnParams,
    }
  }

   /**
   * ================================
   *          Ad ASA Close
   * ================================
   */

  static async adASAClose({
    userAddress,
    userInfo,
    valAppId,
    valAssetId,
  }: {
    userAddress: string
    userInfo: UserInfo
    valAppId: bigint
    valAssetId: bigint
  }) {
    const boxesUser = BoxUtils.createBoxes(0, [userAddress])
    const valAppIdx = userInfo.getAppIndex(valAppId)
    const txnParams = await TxnParams.setTxnFees(3, true)

    let foreignAssets: number[] = []
    let boxAsa_ValidatorAd: BoxReference[] = []
    if (valAssetId != ASA_ID_ALGO) {
      foreignAssets = [Number(valAssetId)]
      boxAsa_ValidatorAd = [{ appId: Number(valAppId), name: new Uint8Array([...BOX_ASA_KEY_PREFIX, ...bigIntToBytes(valAssetId, 8)]) }]
    }

    return {
      valAppIdx,
      foreignAssets,
      boxAdASAClose: [...boxesUser, ...boxAsa_ValidatorAd],
      txnParams,
    }
  }


  /**
   * ================================
   *      Ad Terms and Ad Config
   * ================================
   */

  static async adTermsAndConfig({
    algorandClient,
    gsValAd,
    userAddress,
    valAppId,
    valAssetId,
    userInfo,
    signer,
  }: {
    algorandClient: AlgorandClient
    gsValAd: ValidatorAdGlobalState | undefined
    userAddress: string
    valAppId: bigint
    valAssetId: bigint
    userInfo: UserInfo
    signer: TransactionSigner
  }) {
    const foreignApps = [Number(valAppId)]
    const valAppIdx = userInfo.getAppIndex(valAppId)

    const boxesUser = BoxUtils.createBoxes(0, [userAddress])

    let numTxn: number = 0
    let mbrDelegatorTemplateBox = 0
    let boxesDel_NoticeBoard: BoxReference[] = [] //DelApps Boxes in Noticeboard
    let boxesDel_ValidatorAd: BoxReference[] = [] //DelApps Boxes in ValidatorAd

    if (!gsValAd || bytesToStr(gsValAd.state) === bytesToStr(VA_STATE_CREATED)) {
      const boxDel = (await BoxUtils.getNoticeboardBox(algorandClient.client.algod, BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY)).value
      const boxDelSize = boxDel.length
      mbrDelegatorTemplateBox = BoxUtils.calculateBoxMBR(boxDelSize, BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY)

      const numLoadDel = Math.ceil(boxDelSize / BOX_SIZE_PER_REF)

      boxesDel_NoticeBoard = new Array(numLoadDel).fill({ appId: 0, name: BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY })
      boxesDel_ValidatorAd = new Array(numLoadDel).fill({ appId: Number(valAppId), name: BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY })
      numTxn = numTxn + 1 + numLoadDel + 1
    }

    //Foreign Assets
    let foreignAssets: number[] = []
    let validatorAdNewAssetFee = 0
    let boxAsa_ValidatorAd: BoxReference[] = [] //Add box for accessing ASA on ValidatorAd
    const boxAsa_NoticeBoard: BoxReference[] = [
      { appId: 0, name: new Uint8Array([...BOX_ASSET_KEY_PREFIX, ...bigIntToBytes(valAssetId, 8)]) },
    ]

    if (valAssetId != ASA_ID_ALGO) {
      foreignAssets = [Number(valAssetId)]
      if (!gsValAd || valAssetId != gsValAd.termsPrice.feeAssetId){
        // If it is a new payment asset, another fee must be paid
        validatorAdNewAssetFee = MBR_ASA + MBR_VALIDATOR_AD_ASA_BOX
      }
      boxAsa_ValidatorAd = [{ appId: Number(valAppId), name: new Uint8Array([...BOX_ASA_KEY_PREFIX, ...bigIntToBytes(valAssetId, 8)]) }]
      numTxn += 1
    }

    const amount = validatorAdNewAssetFee + mbrDelegatorTemplateBox

    const noticeboardAddress = getApplicationAddress(noticeboardAppID)
    const feeTxn = await algorandClient.transactions.payment({
      sender: userAddress,
      receiver: noticeboardAddress,
      amount: microAlgos(amount),
      validityWindow: MAX_TXN_VALIDITY,
      signer,
    })

    const txnParams = await TxnParams.setTxnFees(5 + numTxn + 2, true)

    return {
      valAppIdx,
      foreignApps,
      foreignAssets,
      boxesDel_ValidatorAd,
      boxesDel_NoticeBoard,
      mbrDelegatorTemplateBox,
      feeTxn,
      boxesAdTerms: [...boxesUser, ...boxAsa_NoticeBoard, ...boxAsa_ValidatorAd],
      txnParams,
    }
  }

  /**
   * ================================
   *    User Create and Ad Create
   * ================================
   */

  static async userCreateAndAdCreate({
    algorandClient,
    gsNoticeBoard,
    userAddress,
    signer,
  }: {
    algorandClient: AlgorandClient
    gsNoticeBoard: NoticeboardGlobalState
    userAddress: string
    signer: TransactionSigner
  }) {
    // UserCreate-related:
    const userRegFees = Number(gsNoticeBoard!.noticeboardFees.valUserReg);

    const amountUserCreate: number = MBR_USER_BOX + userRegFees;
    const noticeboardAddress = getApplicationAddress(noticeboardAppID);

    //MBR Increase
    const feeTxnUserCreate = await algorandClient.transactions.payment({
      sender: userAddress,
      receiver: noticeboardAddress,
      amount: microAlgos(amountUserCreate),
      validityWindow: MAX_TXN_VALIDITY,
      signer,
    });

    //Getting Last User
    const userLast = gsNoticeBoard.dllVal.userLast;

    const boxesUserCreate: BoxReference[] = BoxUtils.createBoxes(0, [userAddress, userLast]);

    // AdCreate-related:
    const amountAdCreate = Number(gsNoticeBoard.noticeboardFees.valAdCreation) + MBR_NOTICEBOARD_VALIDATOR_AD_CONTRACT_INCREASE + MBR_ACCOUNT

    const feeTxnAdCreate = await algorandClient.transactions.payment({
      sender: userAddress,
      receiver: noticeboardAddress,
      amount: microAlgos(amountAdCreate),
      validityWindow: MAX_TXN_VALIDITY,
      signer,
    })

    //Add boxes for validator template (to load on creation)
    const boxVal = (await BoxUtils.getNoticeboardBox(algorandClient.client.algod, BOX_VALIDATOR_AD_TEMPLATE_KEY)).value
    const boxValSize = boxVal.length
    const numLoadVal = Math.ceil(boxValSize / BOX_SIZE_PER_REF)
    const boxesAdCreate: BoxReference[] = new Array(numLoadVal).fill({ appId: 0, name: BOX_VALIDATOR_AD_TEMPLATE_KEY })

    const valAppIdx = 0n // Because first app

    const txnParams = await TxnParams.setTxnFees(3, true)

    return {
      valAppIdx,
      feeTxnUserCreate,
      feeTxnAdCreate,
      txnParams,
      boxesUserCreate,
      boxesAdCreate,
    }
  }


}
