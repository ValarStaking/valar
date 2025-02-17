import { CURRENCIES } from "@/constants/platform";
import { ROLE_DEL_STR, ROLE_VAL_STR } from "@/constants/smart-contracts";
import { DC_STATE_ENDED_MASK, DC_STATE_LIVE, VA_STATE_READY } from "@/constants/states";
import { TC_LATEST } from "@/constants/terms-and-conditions";
import { TimeParams } from "@/constants/units";
import { DelegatorContractGlobalState } from "@/interfaces/contracts/DelegatorContract";
import { ValidatorAdGlobalState } from "@/interfaces/contracts/ValidatorAd";
import { StakeReqs } from "@/lib/types";
import { User } from "@/store/userStore";

import { calculateNodeRunnerFee } from "./contract/helpers";
import { algoBigIntToDisplay, bytesToHex, bytesToStr, roundsToDate, roundsToDuration } from "./convert";
import { ParamsCache } from "./paramsCache";

export type NodeRelation =
  | "your-ad"
  | "staking-you"
  | "staking-others"
  | "awaiting-you"
  | "awaiting-others"
  | "used"
  | undefined;

export type Stakable = {
  possible: boolean;
  reasons: string[];
  relation: NodeRelation;
};

export class StakingUtils {
  /**
   * ======================
   *    Checks canStake
   * =======================
   */

  static async canStake(
    gsValAd: ValidatorAdGlobalState,
    user: User | null,
    stakeReqs: StakeReqs,
    renewDelCo: DelegatorContractGlobalState | undefined,
  ): Promise<Stakable> {
    const reasons: string[] = [];
    let relation: NodeRelation = undefined;

    // If user is null, show it as possible, although it isn't
    // until they connect wallet, when the possibility is re-resolved.
    if (user === null) {
      return { possible: true, reasons, relation };
    }

    // Check relationship
    if (user.userApps && user.userInfo) {
      if (bytesToStr(user.userInfo.role) === ROLE_DEL_STR) {
        //User is a Delegator

        //Checking if Using
        const gsDelCoUsing = Array.from((user.userApps as Map<bigint, DelegatorContractGlobalState>).values()).find(
          (gsDelCo) =>
            gsValAd.appId === gsDelCo.validatorAdAppId &&
            bytesToStr(gsDelCo.stateCur) < bytesToStr(DC_STATE_ENDED_MASK),
        );

        if (gsDelCoUsing) {
          //Found Using
          relation = ((bytesToStr(gsDelCoUsing.stateCur) === bytesToStr(DC_STATE_LIVE) ? "staking-" : "awaiting-") +
            (gsDelCoUsing.delBeneficiary === user.beneficiary.address ? "you" : "others")) as NodeRelation;
          console.log(relation);
        } else {
          //Not Using

          //Checking if Used
          const gsDelCoUsed = Array.from((user.userApps as Map<bigint, DelegatorContractGlobalState>).values()).find(
            (gsDelCo) =>
              gsValAd.appId === gsDelCo.validatorAdAppId &&
              bytesToStr(gsDelCo.stateCur) >= bytesToStr(DC_STATE_ENDED_MASK),
          );

          relation = gsDelCoUsed ? "used" : relation;
        }
      } else if (bytesToStr(user.userInfo.role) === ROLE_VAL_STR) {
        //User Validator

        relation = gsValAd.valOwner === user.address ? "your-ad" : relation;
      }
    } else {
      console.log("Unknown role.");
    }

    // Check if beneficiary is passing gating requirement
    const gatingPassed = gsValAd.termsReqs.gatingAsaList.every(([assetId, requiredAmount]) => {
      if (assetId !== 0n) {
        return (user.beneficiary.assets.get(assetId) || 0n) > requiredAmount;
      } else {
        return true;
      }
    });
    if (!gatingPassed) {
      reasons.push("You do not meet this node runner's eligibility requirements.");
    }

    const roundCurrent = await ParamsCache.getRound();

    const valAssetId = gsValAd.termsPrice.feeAssetId;
    const delAssetId = stakeReqs.currency;
    const valMaxStake = gsValAd.termsStake.stakeMax;
    const delMaxStake = stakeReqs.maxStake;
    const duration = stakeReqs.duration;
    const minDuration = gsValAd.termsTime.roundsDurationMin;
    const maxDuration = gsValAd.termsTime.roundsDurationMax;
    const endRound = duration + roundCurrent;
    const roundMaxEnd = gsValAd.termsTime.roundMaxEnd;
    const endDate = await roundsToDate(roundMaxEnd);

    // If validator ad is full, it isn't an issue if contract is being renewed and the selected ad is the one with the current DelCo
    const occupied =
      renewDelCo && gsValAd.appId === renewDelCo.validatorAdAppId ? false : gsValAd.cntDel >= gsValAd.cntDelMax;

    // Condition checks
    if (user.userInfo && bytesToStr(user.userInfo.role) !== ROLE_DEL_STR) {
      reasons.push("You cannot stake with this account because you have already registered as a node runner.");
    }
    if (valAssetId !== delAssetId) {
      reasons.push(
        `This node runner does not accept payments in the currency you selected (${CURRENCIES.get(delAssetId)!.ticker}) but only in ${CURRENCIES.get(valAssetId)!.ticker}.`,
      );
    }
    if (minDuration > duration) {
      reasons.push(
        `Your selected staking duration (${roundsToDuration(duration, TimeParams.stake, true)}) is shorter than the minimum supported by this node runner (${roundsToDuration(minDuration, TimeParams.stake, true)}).`,
      );
    }
    if (maxDuration < duration) {
      reasons.push(
        `Your selected staking duration (${roundsToDuration(duration, TimeParams.stake, true)}) is longer than the maximum supported by this node runner (${roundsToDuration(maxDuration, TimeParams.stake, true)}).`,
      );
    }
    if (roundMaxEnd < endRound) {
      reasons.push(
        `Your selected staking duration would end beyond the end date supported by this node runner (${endDate.toISOString().split("T")[0]}).`,
      );
    }
    if (valMaxStake < delMaxStake) {
      reasons.push(
        `Your selected maximum stake amount (${algoBigIntToDisplay(delMaxStake, "floor", true)}) exceeds the maximum supported by this node runner (${algoBigIntToDisplay(valMaxStake, "floor", true)}).`,
      );
    }
    if (delMaxStake < user.beneficiary.algo) {
      reasons.push(
        `The account, with which you want to stake ${user.beneficiary.address} has ALGO balance that exceeds the requested maximum stake amount (${algoBigIntToDisplay(delMaxStake, "floor", true)}).`,
      );
    }
    if (!user || (user.assets.get(valAssetId) || 0n) <= calculateNodeRunnerFee(stakeReqs, gsValAd)) {
      reasons.push(`You do not have enough ${CURRENCIES.get(valAssetId)!.ticker} to pay for the node runner fees.`);
    }
    if (occupied) {
      reasons.push("This node runner is currently fully occupied and will not be able to serve you.");
    }
    if (bytesToStr(gsValAd.state) !== bytesToStr(VA_STATE_READY)) {
      reasons.push("This node runner is currently not accepting new users.");
    }
    if (bytesToHex(gsValAd.tcSha256) !== TC_LATEST) {
      reasons.push("This node runner has not agreed to the platform's terms and conditions.");
    }
    const possible = reasons.length === 0;

    return { possible, reasons, relation };
  }
}
