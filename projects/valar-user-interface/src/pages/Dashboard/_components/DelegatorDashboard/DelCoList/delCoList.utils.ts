import { DelegatorContractGlobalState } from "@/interfaces/contracts/DelegatorContract";
import { ValidatorAdGlobalState } from "@/interfaces/contracts/ValidatorAd";
import { DelCoStatus } from "@/lib/types";
import { assetAmountToFeeDisplay, decodeDelCoStateToString, roundsToDate, roundsToDuration } from "@/utils/convert";
import { AssetParams, TimeParams } from "@/constants/units";

export type DelCoListItem = {
  stakingAddress: string;
  contractId: bigint;
  status: DelCoStatus;
  valName: string;
  adId: bigint;
  expiry: string;
  start: string;
  duration: string;
  warnings: string;
  latestWarning: string;
  totalPrice: string;
  gated: string;
};

export async function getDelCoListItems(
  delCoMap: Map<bigint, DelegatorContractGlobalState>,
  valAdMap: Map<bigint, ValidatorAdGlobalState>,
): Promise<DelCoListItem[]> {

  const delCoList = Promise.all([...delCoMap.values()]
  .map(async (gsDelCo) => {
      const adId = gsDelCo.validatorAdAppId;
      const { status } = decodeDelCoStateToString(gsDelCo.stateCur);

      const feeTotal = (
        gsDelCo.feeOperational +
        gsDelCo.feeOperationalPartner +
        gsDelCo.delegationTermsGeneral.feeSetup +
        gsDelCo.delegationTermsGeneral.feeSetupPartner
      )

      const assetId = gsDelCo.delegationTermsGeneral.feeAssetId;

      const gated = gsDelCo.delegationTermsBalance.gatingAsaList[0][0] !== 0n || gsDelCo.delegationTermsBalance.gatingAsaList[1][0] !== 0n ? "Yes" : "No";

      const expiryDate = await roundsToDate(gsDelCo.roundEnd);
      const startDate = await roundsToDate(gsDelCo.roundStart);
      const expiry = expiryDate.toISOString().split("T")[0];
      const start = startDate.toISOString().split("T")[0];

      return ({
        stakingAddress: gsDelCo.delBeneficiary,
        contractId: gsDelCo.appId,
        status: status,
        valName: valAdMap.get(adId)!.valOwner,
        adId: adId,
        expiry: expiry,
        start: start,
        duration: roundsToDuration(gsDelCo.roundEnd-gsDelCo.roundStart, TimeParams.stake, true),
        warnings: gsDelCo.cntBreachDel + " / " + gsDelCo.delegationTermsBalance.cntBreachDelMax,
        latestWarning: gsDelCo.roundBreachLast.toString(),
        totalPrice: assetAmountToFeeDisplay(feeTotal, assetId, AssetParams.total, true),
        gated: gated,
      }) as DelCoListItem;
    }));

  return delCoList;
}
