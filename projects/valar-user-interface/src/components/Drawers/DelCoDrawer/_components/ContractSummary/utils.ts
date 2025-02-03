import { DelegatorContractGlobalState } from "@/interfaces/contracts/DelegatorContract";
import { DelCoStatus } from "@/lib/types";
import { DateToFormDisplay } from "@/lib/utils";
import { algoBigIntToDisplay, bytesToHex, decodeDelCoStateToString, roundsToDate } from "@/utils/convert";

export type DelCoSummary = {
  delBeneficiary: string;
  contractId: string;
  status: DelCoStatus;
  contractStart: string;
  contractEnd: string;
  currentStake: string;
  maxStake: string;
  warned: boolean;
  warnings: string;
  lastWarning: string;
  tc: string;
};

/**
 * =====================================
 *      DelCo GS to Contract Summary
 * =====================================
 */

export async function getDelCoSummary(
  gsDelCo: DelegatorContractGlobalState,
  currentStake: bigint,
): Promise<DelCoSummary> {
  const { status } = decodeDelCoStateToString(gsDelCo.stateCur);

  const delBeneficiary = gsDelCo.delBeneficiary;
  const contractStart = DateToFormDisplay(await roundsToDate(gsDelCo.roundStart));
  const contractEnd = DateToFormDisplay(await roundsToDate(gsDelCo.roundEnd));
  const _currentStake = algoBigIntToDisplay(currentStake, "floor", true);
  const maxStake = algoBigIntToDisplay(gsDelCo.delegationTermsBalance.stakeMax, "floor", true);
  const warnings = gsDelCo.cntBreachDel;
  const maxWarnings = gsDelCo.delegationTermsBalance.cntBreachDelMax;
  const lastWarning = gsDelCo.roundBreachLast.toString();

  let warned = false;
  if (warnings > 0n) {
    warned = true;
  }

  return {
    delBeneficiary: delBeneficiary,
    contractId: gsDelCo.appId.toString(),
    status: status,
    contractStart: contractStart,
    contractEnd: contractEnd,
    currentStake: _currentStake,
    maxStake: maxStake,
    warned: warned,
    warnings: warnings.toString() + "/" + maxWarnings.toString(),
    lastWarning: lastWarning,
    tc: bytesToHex(gsDelCo.tcSha256),
  } as DelCoSummary;
}