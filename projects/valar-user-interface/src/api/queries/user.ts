import { ASA_ID_ALGO } from "@/constants/smart-contracts";
import { DelegatorContractGlobalState } from "@/interfaces/contracts/DelegatorContract";
import { NoticeboardGlobalState } from "@/interfaces/contracts/Noticeboard";
import { UserInfo } from "@/interfaces/contracts/User";
import { KeyRegParams } from "@/lib/types";
import { AccountInfo } from "@/store/userStore";
import { bytesToHex } from "@/utils/convert";
import AlgodClient from "algosdk/dist/types/client/v2/algod/algod";
import { Buffer } from "buffer";

export class UserQuery {
  static async fetchAllValidatorUserInfo(
    algodClient: AlgodClient,
    NoticeboardGlobalState: NoticeboardGlobalState,
  ): Promise<Map<string, UserInfo> | undefined> {

    //Map to store list of Validators' User Info
    const validators: Map<string, UserInfo> = new Map();

    let currUser = NoticeboardGlobalState.dllVal.userFirst;
    for (let i = 1; i <= NoticeboardGlobalState.dllVal.cntUsers; i++) {
      const info = await UserInfo.getUserInfo(algodClient, currUser);
      if (info != undefined) {
        validators.set(currUser, info);
      }
      currUser = info!.nextUser;
    }

    return validators;
  }

  static async getAccountInfo(
    algodClient: AlgodClient,
    address: string,
  ): Promise<AccountInfo> {
    const res = await algodClient.accountInformation(address).do();
    const algo: bigint = res["amount"];
    const assets = new Map<bigint, bigint>();
    assets.set(ASA_ID_ALGO, algo);
    res["assets"].forEach(
      (asset: { amount: bigint; "asset-id": bigint; "is-frozen": boolean }) => {
        assets.set(BigInt(asset["asset-id"]), BigInt(asset["amount"]));
      },
    );
    console.log("Assets :: ");
    console.log(assets);
    let keyRegParams = undefined;
    if (res["participation"]) {
      keyRegParams = {
        voteKey: new Uint8Array(
          Buffer.from(res["participation"]["vote-participation-key"], "base64"),
        ),
        selectionKey: new Uint8Array(
          Buffer.from(
            res["participation"]["selection-participation-key"],
            "base64",
          ),
        ),
        voteFirst: BigInt(res["participation"]["vote-first-valid"]),
        voteLast: BigInt(res["participation"]["vote-last-valid"]),
        voteKeyDilution: BigInt(res["participation"]["vote-key-dilution"]),
        stateProofKey: new Uint8Array(
          Buffer.from(res["participation"]["state-proof-key"], "base64"),
        ),
      } as KeyRegParams;
    }
    console.log("Key reg parameters of user: ", keyRegParams);
    const trackedPerformance = res["incentive-eligible"] as boolean;
    const accountInfo: AccountInfo = {
      address,
      algo,
      assets,
      keyRegParams,
      trackedPerformance,
    };
    return accountInfo;
  }
  static keysDelCoSigned(account: AccountInfo, gsDelCo: DelegatorContractGlobalState): boolean {
    return (
      account.keyRegParams !== undefined &&
      bytesToHex(account.keyRegParams.voteKey) === bytesToHex(gsDelCo.voteKey) &&
      bytesToHex(account.keyRegParams.selectionKey) === bytesToHex(gsDelCo.selKey) &&
      account.keyRegParams.voteFirst === gsDelCo.roundStart &&
      account.keyRegParams.voteLast === gsDelCo.roundEnd &&
      account.keyRegParams.voteKeyDilution === gsDelCo.voteKeyDilution &&
      bytesToHex(account.keyRegParams.stateProofKey) === bytesToHex(gsDelCo.stateProofKey)
    );
  }


  static keysDelCoSignedAndTracked(account: AccountInfo, gsDelCo: DelegatorContractGlobalState): boolean {
    return (
      account.trackedPerformance &&
      UserQuery.keysDelCoSigned(account, gsDelCo)
    );
  }
}
