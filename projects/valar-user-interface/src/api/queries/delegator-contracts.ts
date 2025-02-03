import {
  DC_STATE_ENDED_EXPIRED,
  DC_STATE_ENDED_MASK,
  DC_STATE_ENDED_NOT_CONFIRMED,
  DC_STATE_ENDED_NOT_SUBMITTED,
  DC_STATE_LIVE,
  DC_STATE_READY,
  DC_STATE_SUBMITTED,
} from "@/constants/states";
import { DelegatorContractGlobalState } from "@/interfaces/contracts/DelegatorContract";
import { UserInfo } from "@/interfaces/contracts/User";
import { bytesToStr } from "@/utils/convert";
import { ParamsCache } from "@/utils/paramsCache";
import AlgodClient from "algosdk/dist/types/client/v2/algod/algod";

export class DelegatorQuery {
  
  static async fetchDelegatorContracts(
    algodClient: AlgodClient,
    delAppIds: bigint[],
  ): Promise<Map<bigint, DelegatorContractGlobalState> | undefined> {
    const delCoMap: Map<bigint, DelegatorContractGlobalState> = new Map();
    for (let id of delAppIds) {
      const gsDelCo = await DelegatorContractGlobalState.getGlobalState(
        algodClient,
        id,
      );
      if (gsDelCo) {
        const round = await ParamsCache.getRound();
        // Modify DelCo current state depending on current round.
        if (bytesToStr(gsDelCo.state) === bytesToStr(DC_STATE_READY)) {
          if (
            round >=
            gsDelCo.roundStart + gsDelCo.delegationTermsGeneral.roundsSetup
          ) {
            // Contract has not been setup in time, which was not yet reported.
            gsDelCo.stateCur = DC_STATE_ENDED_NOT_SUBMITTED;
          }
        } else if (
          bytesToStr(gsDelCo.state) === bytesToStr(DC_STATE_SUBMITTED)
        ) {
          if (
            round >=
            gsDelCo.roundStart +
              gsDelCo.delegationTermsGeneral.roundsSetup +
              gsDelCo.delegationTermsGeneral.roundsConfirm
          ) {
            // Contract has not been confirmed in time, which was not yet reported.
            gsDelCo.stateCur = DC_STATE_ENDED_NOT_CONFIRMED;
          }
        } else if (bytesToStr(gsDelCo.state) === bytesToStr(DC_STATE_LIVE)) {
          if (round >= gsDelCo.roundEnd) {
            // Contract has already expired, it just was not reported yet.
            gsDelCo.stateCur = DC_STATE_ENDED_EXPIRED;
          }
        } else if (
          bytesToStr(gsDelCo.state) >= bytesToStr(DC_STATE_ENDED_MASK)
        ) {
          // Contract is already ended, thus no change needed.
          gsDelCo.stateCur = gsDelCo.state;
        } else {
          // Should not happen.
        }

        // Set contract
        delCoMap.set(gsDelCo.appId, gsDelCo);
      }
    }

    return delCoMap;
  }

  static async fetchDelManagerContracts(
    algodClient: AlgodClient,
    delegatorManager: string,
  ): Promise<Map<bigint, DelegatorContractGlobalState> | undefined> {
    const info = await UserInfo.getUserInfo(algodClient, delegatorManager);

    if (info) {
      const delAppIds: bigint[] = [...info.appIds.filter((id) => id != 0n)];
      const delCoMap = DelegatorQuery.fetchDelegatorContracts(
        algodClient,
        delAppIds,
      );
      return delCoMap;
    } else {
      return undefined;
    }
  }
}
