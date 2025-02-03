import { DelegatorContractGlobalState } from "@/interfaces/contracts/DelegatorContract";
import { DelCoStatus } from "@/lib/types";
import { CURRENCIES } from "@/constants/platform";
import { algoBigIntToDisplay, assetAmountToFeeDisplay, decodeDelCoStateToString, roundsToDate, roundsToDuration } from "@/utils/convert";
import { AssetParams, TimeParams } from "@/constants/units";

export type ValDelCoListItem = {
  adId: bigint;
  stakingAddress: string;
  contractId: bigint;
  status: DelCoStatus;
  validUntil: string;
  maxStake: string;
  duration: string;
  currency: string;
  setupFee: string;
  opFee: string;
  warnings: string;
  latestWarning: string;
  setupTime: string;
  confirmationTime: string;
  gated: string;
};

export async function getValDelCoList(
  delCoMap: Map<bigint, DelegatorContractGlobalState>,
): Promise<ValDelCoListItem[]> {

  const valDelCoList =  Promise.all([...delCoMap.values()]
  .map(async (gsDelCo) => {
    const adId = gsDelCo.validatorAdAppId;
    const { status } = decodeDelCoStateToString(gsDelCo.stateCur);

    const assetId = gsDelCo.delegationTermsGeneral.feeAssetId;
    const gated = gsDelCo.delegationTermsBalance.gatingAsaList[0][0] !== 0n || gsDelCo.delegationTermsBalance.gatingAsaList[1][0] !== 0n ? "Yes" : "No";

    const validUntil = await roundsToDate(gsDelCo.roundEnd);

    return ({
      adId: adId,
      stakingAddress: gsDelCo.delBeneficiary,
      contractId: gsDelCo.appId,
      status: status,
      validUntil: validUntil.toISOString().split("T")[0],
      maxStake: algoBigIntToDisplay(gsDelCo.delegationTermsBalance.stakeMax,"ceil", true),
      duration: roundsToDuration(gsDelCo.roundEnd-gsDelCo.roundStart, TimeParams.stake, true),
      currency: CURRENCIES.get(assetId)?.ticker,
      setupFee: assetAmountToFeeDisplay(gsDelCo.delegationTermsGeneral.feeSetup, assetId, AssetParams.setup),
      opFee: assetAmountToFeeDisplay(gsDelCo.feeOperational, assetId, AssetParams.opDuration),
      warnings: gsDelCo.cntBreachDel + " / " + gsDelCo.delegationTermsBalance.cntBreachDelMax,
      latestWarning: gsDelCo.roundBreachLast.toString(),
      setupTime: roundsToDuration(gsDelCo.delegationTermsGeneral.roundsSetup, TimeParams.setup, true),
      confirmationTime: roundsToDuration(gsDelCo.delegationTermsGeneral.roundsConfirm, TimeParams.confirmation, true),
      gated: gated,
    }) as ValDelCoListItem;
  }));

  return valDelCoList;

}
