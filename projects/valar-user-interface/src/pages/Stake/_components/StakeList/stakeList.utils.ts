import { CURRENCIES } from "@/constants/platform";
import { AssetParams, TimeParams } from "@/constants/units";
import { ValidatorAdGlobalState } from "@/interfaces/contracts/ValidatorAd";
import { Nfd } from "@/interfaces/nfd";
import { StakeReqs, ValAdStatus } from "@/lib/types";
import { User } from "@/store/userStore";
import { adjustedMaxStakeForGratis, calculateFeeRound, calculateOperationalFee } from "@/utils/contract/helpers";
import {
  algoBigIntToDisplay,
  assetAmountToFeeDisplay,
  decodeValAdStateToString,
  roundsToDate,
  roundsToDuration,
} from "@/utils/convert";
import { StakingUtils } from "@/utils/staking-utils";

export type StakeListItem = {
  name: string;
  nfd: Nfd;
  adId: bigint;
  totalPrice: string;
  occupation: string;
  status: ValAdStatus;
  currency: string;
  setupFee: string;
  opFee: string;
  opFeeMin: string;
  opFeeVar: string;
  setupTime: string;
  confirmationTime: string;
  minDuration: string;
  maxDuration: string;
  validUntil: string;
  maxStake: string;
  maxWarnings: number;
  gated: string;
  canStake: boolean;
};

/**
 * =================================
 *        ValAdsMap to StakeList
 * =================================
 */

export async function getStakeList(
  valAdsMap: Map<bigint, ValidatorAdGlobalState>,
  stakeReqs: StakeReqs,
  user: User | null,
  valNfdsMap?: Map<string, Nfd | null>,
  partner?: string,
): Promise<StakeListItem[]> {
  const stakeListItems = Promise.all(
    [...valAdsMap.values()].map(async (gsValAd) => {
      const res = await StakingUtils.canStake(gsValAd, user, stakeReqs);

      const valOwner = gsValAd.valOwner;
      const nfd = valNfdsMap?.get(valOwner) || null;

      const maxStakeAdjusted = adjustedMaxStakeForGratis(stakeReqs, gsValAd);
      const feeRound = calculateFeeRound(
        maxStakeAdjusted,
        gsValAd.termsPrice.feeRoundMin,
        gsValAd.termsPrice.feeRoundVar,
      );
      const feeSetup = gsValAd.termsPrice.feeSetup;
      const feeOperational = calculateOperationalFee(feeRound, stakeReqs.duration, 0n);
      const feeNodeRunner = feeSetup + feeOperational;
      const feePartner = partner ? 0n : 0n;
      const feeTotal = feeNodeRunner + feePartner;

      const status = decodeValAdStateToString(gsValAd.state);

      const gated =
        gsValAd.termsReqs.gatingAsaList[0][0] !== 0n || gsValAd.termsReqs.gatingAsaList[1][0] !== 0n ? "Yes" : "No";

      const validUntil = await roundsToDate(gsValAd.termsTime.roundMaxEnd);

      return {
        name: valOwner,
        nfd: nfd,
        adId: gsValAd.appId,
        totalPrice: assetAmountToFeeDisplay(feeTotal, stakeReqs.currency, AssetParams.total),
        currency: CURRENCIES.get(gsValAd.termsPrice.feeAssetId)?.ticker,
        occupation: gsValAd.cntDel + " / " + gsValAd.cntDelMax,
        status: status,
        setupFee: assetAmountToFeeDisplay(feeSetup, stakeReqs.currency, AssetParams.setup),
        opFee: assetAmountToFeeDisplay(feeOperational, stakeReqs.currency, AssetParams.opDuration),
        opFeeMin: assetAmountToFeeDisplay(gsValAd.termsPrice.feeRoundMin, stakeReqs.currency, AssetParams.opMin),
        opFeeVar: assetAmountToFeeDisplay(gsValAd.termsPrice.feeRoundVar, stakeReqs.currency, AssetParams.opVar),
        partnerFee: assetAmountToFeeDisplay(feePartner, stakeReqs.currency, AssetParams.total),
        setupTime: roundsToDuration(gsValAd.termsTime.roundsSetup, TimeParams.setup, true),
        confirmationTime: roundsToDuration(gsValAd.termsTime.roundsConfirm, TimeParams.confirmation, true),
        minDuration: roundsToDuration(gsValAd.termsTime.roundsDurationMin, TimeParams.stake, true),
        maxDuration: roundsToDuration(gsValAd.termsTime.roundsDurationMax, TimeParams.stake, true),
        validUntil: validUntil.toISOString().split("T")[0],
        maxStake: algoBigIntToDisplay(gsValAd.termsStake.stakeMax, "floor", true),
        maxWarnings: Number(gsValAd.termsWarn.cntWarningMax),
        gated: gated,
        canStake: res.possible,
      } as StakeListItem;
    }),
  );

  return stakeListItems;
}
