import { InfoHeading, InfoItem, InfoLabel, InfoSection, InfoValue } from "@/components/Info/InfoUtilsCompo";
import ITooltip from "@/components/Tooltip/ITooltip";
import { ToolTips } from "@/constants/tooltips";
import { TimeParams } from "@/constants/units";
import { ValTermsTimingInterface } from "@/interfaces/contracts/ValidatorAd";
import { roundsToDate, roundsToDuration } from "@/utils/convert";
import { useEffect, useState } from "react";

export type TimingSectionTypeContract = {
  roundsSetup: bigint;
  roundsConfirm: bigint;
};

const TimingSection = ({ data }: { data: TimingSectionTypeContract | ValTermsTimingInterface }) => {
  const [validUntil, setValidUntil] = useState<string>("N/A");

  useEffect(() => {
    const fetch = async () => {
      if ("roundsDurationMin" in data) {
        const validUntil = await roundsToDate(data.roundMaxEnd);
        setValidUntil(validUntil.toISOString().split("T")[0]);
      }
    };
    fetch();
  }, [data]);

  if ("roundsDurationMin" in data) {
    return (
      <InfoSection>
        <InfoHeading>Timings</InfoHeading>
        <InfoItem>
          <InfoLabel>Valid until:</InfoLabel>
          <InfoValue>{validUntil}</InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel>
            Setup time <ITooltip value={ToolTips.SetupTime} /> :
          </InfoLabel>
          <InfoValue>{roundsToDuration(data.roundsSetup, TimeParams.setup, true)}</InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel>
            Confirmation time <ITooltip value={ToolTips.ConfirmationTime} /> :
          </InfoLabel>
          <InfoValue>{roundsToDuration(data.roundsConfirm, TimeParams.confirmation, true)}</InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel>Min contract duration:</InfoLabel>
          <InfoValue>{roundsToDuration(data.roundsDurationMin, TimeParams.stake, true)}</InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel>Max contract duration:</InfoLabel>
          <InfoValue>{roundsToDuration(data.roundsDurationMax, TimeParams.stake, true)}</InfoValue>
        </InfoItem>
      </InfoSection>
    );
  } else {
    return (
      <InfoSection>
        <InfoHeading className="text-sm font-semibold">Timings</InfoHeading>
        <InfoItem>
          <InfoLabel className="text-sm font-medium">
            Setup time <ITooltip value={ToolTips.SetupTime} /> :
          </InfoLabel>
          <InfoValue>{roundsToDuration(data.roundsSetup, TimeParams.setup, true)}</InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel className="text-sm font-medium">
            Confirmation time <ITooltip value={ToolTips.ConfirmationTime} /> :
          </InfoLabel>
          <InfoValue>{roundsToDuration(data.roundsConfirm, TimeParams.confirmation, true)}</InfoValue>
        </InfoItem>
      </InfoSection>
    );
  }
};

export default TimingSection;
