import { UserQuery } from "@/api/queries/user";
import { InfoItem, InfoLabel, InfoValue } from "@/components/Info/InfoUtilsCompo";
import ContractStatus from "@/components/Status/ContractStatus";
import TermsAndConditions from "@/components/TermsAndConditions/TermsAndConditions";
import ITooltip from "@/components/Tooltip/ITooltip";
import LinkExt from "@/components/ui/link-ext";
import { Separator } from "@/components/ui/separator";
import { DC_STATE_ENDED_MASK, DC_STATE_LIVE, DC_STATE_READY, DC_STATE_SUBMITTED } from "@/constants/states";
import { ASSUMED_BLOCK_TIME } from "@/constants/timing";
import { ToolTips } from "@/constants/tooltips";
import { FROM_BASE_TO_MILLI_MULTIPLIER } from "@/constants/units";
import { useAppGlobalState } from "@/contexts/AppGlobalStateContext";
import { useDelCoDrawer } from "@/contexts/DelCoDrawerContext";
import { cn } from "@/lib/shadcn-utils";
import { getExplorerConfigFromViteEnvironment } from "@/utils/config/getExplorerConfig";
import { bytesToStr, decodeDelCoStateToString, ellipseAddress, timeFormatter } from "@/utils/convert";
import { ParamsCache } from "@/utils/paramsCache";
import { useWallet } from "@txnlab/use-wallet-react";
import { useEffect, useState } from "react";

import ArchiveContractButton from "./ContractActions/ArchiveContractButton";
import ConfirmSetupButton from "./ContractActions/ConfirmSetupButton";
import ExtendContractButton from "./ContractActions/ExtendContractButton";
import WithdrawContractButton from "./ContractActions/WithdrawContractButton";
import { DelCoSummary, getDelCoSummary } from "./utils";

const ContractActiveCard: React.FC<{ className?: string }> = ({ className }) => {
  const { accountUrl, appUrl } = getExplorerConfigFromViteEnvironment();
  const { activeAddress } = useWallet();
  const { algorandClient } = useAppGlobalState();
  const [contract, setContract] = useState<DelCoSummary | undefined>(undefined);
  const [timeLeft, setTimeLeft] = useState<number | undefined>(undefined);
  const [extStatusText, setExtStatusText] = useState<string | undefined>(undefined);
  const { gsDelCo, setRefetch } = useDelCoDrawer();

  useEffect(() => {
    const fetch = async () => {
      if (!gsDelCo) return;

      // Convert data to be displayed
      const delBeneficiaryAccount = await UserQuery.getAccountInfo(algorandClient.client.algod, gsDelCo.delBeneficiary);
      const currentStake = delBeneficiaryAccount.algo;
      const data = await getDelCoSummary(gsDelCo, currentStake);

      // Set countdown timer based on state and current round
      if (
        bytesToStr(gsDelCo.stateCur) === bytesToStr(DC_STATE_READY) ||
        bytesToStr(gsDelCo.stateCur) === bytesToStr(DC_STATE_SUBMITTED)
      ) {
        const roundCur = await ParamsCache.getRound();
        let roundEnd = gsDelCo.roundStart + gsDelCo.delegationTermsGeneral.roundsSetup;
        if (bytesToStr(gsDelCo.stateCur) === bytesToStr(DC_STATE_SUBMITTED)) {
          roundEnd =
            gsDelCo.roundStart +
            gsDelCo.delegationTermsGeneral.roundsSetup +
            gsDelCo.delegationTermsGeneral.roundsConfirm;
        }
        const timer = Number(roundEnd - roundCur) * ASSUMED_BLOCK_TIME * FROM_BASE_TO_MILLI_MULTIPLIER;
        setTimeLeft(timer); // Initialize timer to estimated time
      } else {
        setTimeLeft(undefined);
        const { extStatusText } = decodeDelCoStateToString(gsDelCo.stateCur);
        setExtStatusText(extStatusText);
      }
      setContract(data);
    };

    fetch();
  }, [gsDelCo]);

  // Update timer
  const timerInterval = 1 * FROM_BASE_TO_MILLI_MULTIPLIER; // [ms]
  useEffect(() => {
    if (timeLeft) {
      if (timeLeft <= 0) {
        setExtStatusText(undefined);
        setRefetch(true);
        return;
      }

      const intervalId = setInterval(() => {
        setTimeLeft((prev) => {
          setExtStatusText(" (" + timeFormatter(Math.floor(prev! / FROM_BASE_TO_MILLI_MULTIPLIER)) + ")");
          return prev! - timerInterval;
        });
      }, timerInterval);

      return () => clearInterval(intervalId); // Clear on component unmount
    }
  }, [timeLeft]);

  if (!contract) return;

  return (
    <div className={cn("h-min rounded-lg bg-gradient-to-br from-gradient-light to-gradient-dark p-3", className)}>
      <h1 className="my-1 text-base font-bold">Contract Summary</h1>
      <Separator />
      <div className="my-3 space-y-1">
        <InfoItem>
          <InfoLabel>Contract for address:</InfoLabel>
          <LinkExt href={accountUrl + contract.delBeneficiary}>{ellipseAddress(contract.delBeneficiary)}</LinkExt>
        </InfoItem>
        <InfoItem>
          <InfoLabel>Contract ID:</InfoLabel>
          <InfoValue>
            {" "}
            <LinkExt href={appUrl + contract.contractId}>{contract.contractId}</LinkExt>
          </InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel>Status:</InfoLabel>
          <InfoValue>
            <ContractStatus status={contract.status} extStatusText={extStatusText} />
          </InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel className="flex items-center gap-1">
            Monitor performance <ITooltip value={ToolTips.MonitorPerformance} /> :
          </InfoLabel>
          <InfoValue>
            <a target="_blank" rel="noopener noreferrer" className="text-secondary" href="https://alerts.allo.info/">
              https://alerts.allo.info/
            </a>
          </InfoValue>
        </InfoItem>
      </div>
      <Separator />
      <div className="my-3 space-y-1">
        <InfoItem>
          <InfoLabel>Contract start:</InfoLabel>
          <InfoValue>{contract.contractStart}</InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel>Contract expiry:</InfoLabel>
          <InfoValue>{contract.contractEnd}</InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel>{activeAddress === gsDelCo!.delManager ? "Your current stake:" : "Current stake:"}</InfoLabel>
          <InfoValue>{contract.currentStake}</InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel>Max stake:</InfoLabel>
          <InfoValue>{contract.maxStake}</InfoValue>
        </InfoItem>
        {contract.warned && (
          <div>
            <InfoItem>
              <InfoLabel>Number of warnings:</InfoLabel>
              <InfoValue>{contract.warnings}</InfoValue>
            </InfoItem>
            <InfoItem>
              <InfoLabel>Latest warning:</InfoLabel>
              <InfoValue>{contract.lastWarning}</InfoValue>
            </InfoItem>
          </div>
        )}
      </div>
      <div className="mt-4 text-sm text-text-tertiary">
        Accepted <TermsAndConditions terms={contract.tc} />
      </div>
      {activeAddress === gsDelCo!.delManager && (
        <div className="mt-10 flex gap-2">
          {bytesToStr(gsDelCo!.stateCur) === bytesToStr(DC_STATE_LIVE) && (
            <>
              <WithdrawContractButton delAppId={gsDelCo!.appId} />
              {/* <ExtendContractButton /> */}
            </>
          )}
          {(bytesToStr(gsDelCo!.stateCur) === bytesToStr(DC_STATE_READY) ||
            bytesToStr(gsDelCo!.stateCur) === bytesToStr(DC_STATE_SUBMITTED)) && <ConfirmSetupButton />}
          {bytesToStr(gsDelCo!.stateCur) >= bytesToStr(DC_STATE_ENDED_MASK) && <ArchiveContractButton />}
        </div>
      )}
    </div>
  );
};

export default ContractActiveCard;
