import { ValidatorQuery } from "@/api/queries/validator-ads";
import { CURRENCIES } from "@/constants/platform";
import { AssetParams, TimeParams } from "@/constants/units";
import { ValidatorAdGlobalState } from "@/interfaces/contracts/ValidatorAd";
import { ValAdStatus } from "@/lib/types";
import {
  algoBigIntToDisplay,
  assetAmountToFeeDisplay,
  decodeValAdStateToString,
  gratisBigIntToNumber,
  roundsToDate,
  roundsToDuration,
} from "@/utils/convert";
import AlgodClient from "algosdk/dist/types/client/v2/algod/algod";

export type ValAdListItem = {
  adId: bigint;
  status: ValAdStatus;
  validUntil: string;
  occupation: string;
  earnTotal: string;
  earnClaim: string;
  currency: string;
  setupFee: string;
  opFeeMin: string;
  opFeeVar: string;
  maxStake: string;
  gratisStake: string;
  minDuration: string;
  maxDuration: string;
  setupTime: string;
  confirmationTime: string;
  maxWarnings: number;
  warningTime: string;
  gated: string;
};

export async function getValAdList(
  algodClient: AlgodClient,
  valAdMap: Map<bigint, ValidatorAdGlobalState>,
): Promise<ValAdListItem[]> {
  const valAdList = await Promise.all(
    [...valAdMap.values()].map(async (gsValAd) => {
      const adId = gsValAd.appId;
      const status = decodeValAdStateToString(gsValAd.state);

      const assetId = gsValAd.termsPrice.feeAssetId;
      const currency = CURRENCIES.get(assetId)?.ticker;

      console.log("Fetching currencies and earnings of ad.");
      const earnings = await ValidatorQuery.fetchValEarnings(
        algodClient,
        gsValAd,
      );
      const earning = earnings.find((earning) => earning.id === assetId);
      const earnTotal = earning?.total || 0n;
      const earnClaim = earning?.unclaimed || 0n;

      const gated =
        gsValAd.termsReqs.gatingAsaList[0][0] !== 0n ||
        gsValAd.termsReqs.gatingAsaList[1][0] !== 0n
          ? "Yes"
          : "No";

      const validUntil = await roundsToDate(gsValAd.termsTime.roundMaxEnd);

      return {
        adId: adId,
        status: status,
        validUntil: validUntil.toISOString().split("T")[0],
        occupation: gsValAd.cntDel + " / " + gsValAd.cntDelMax,
        earnTotal: assetAmountToFeeDisplay(
          earnTotal,
          assetId,
          AssetParams.total,
        ),
        earnClaim: assetAmountToFeeDisplay(
          earnClaim,
          assetId,
          AssetParams.total,
        ),
        currency: currency,
        setupFee: assetAmountToFeeDisplay(
          gsValAd.termsPrice.feeSetup,
          assetId,
          AssetParams.setup,
        ),
        opFeeMin: assetAmountToFeeDisplay(
          gsValAd.termsPrice.feeRoundMin,
          assetId,
          AssetParams.opMin,
        ),
        opFeeVar: assetAmountToFeeDisplay(
          gsValAd.termsPrice.feeRoundVar,
          assetId,
          AssetParams.opVar,
        ),
        maxStake: algoBigIntToDisplay(
          gsValAd.termsStake.stakeMax,
          "floor",
          true,
        ),
        gratisStake: gratisBigIntToNumber(gsValAd.termsStake.stakeGratis) + "%",
        minDuration: roundsToDuration(
          gsValAd.termsTime.roundsDurationMin,
          TimeParams.stake,
          true,
        ),
        maxDuration: roundsToDuration(
          gsValAd.termsTime.roundsDurationMax,
          TimeParams.stake,
          true,
        ),
        setupTime: roundsToDuration(
          gsValAd.termsTime.roundsSetup,
          TimeParams.setup,
          true,
        ),
        confirmationTime: roundsToDuration(
          gsValAd.termsTime.roundsConfirm,
          TimeParams.confirmation,
          true,
        ),
        maxWarnings: Number(gsValAd.termsWarn.cntWarningMax),
        warningTime: roundsToDuration(
          gsValAd.termsWarn.roundsWarning,
          TimeParams.warn,
          true,
        ),
        gated: gated,
      } as ValAdListItem;
    }),
  );

  return valAdList;
}
