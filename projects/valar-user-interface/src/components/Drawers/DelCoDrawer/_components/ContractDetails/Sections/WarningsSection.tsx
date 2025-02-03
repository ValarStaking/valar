import { InfoHeading, InfoItem, InfoLabel, InfoSection, InfoValue } from "@/components/Info/InfoUtilsCompo";
import ITooltip from "@/components/Tooltip/ITooltip";
import { ToolTips } from "@/constants/tooltips";
import { TimeParams } from "@/constants/units";
import { ValTermsWarningsInterface } from "@/interfaces/contracts/ValidatorAd";
import { roundsToDuration } from "@/utils/convert";

const WarningsSection = ({ data }: { data: ValTermsWarningsInterface }) => {
  return (
    <InfoSection>
      <InfoHeading className="text-sm font-semibold">Warnings</InfoHeading>
      <InfoItem>
        <InfoLabel className="text-sm font-medium">
          Max warnings <ITooltip value={ToolTips.MaxWarnings} />:
        </InfoLabel>
        <InfoValue>{Number(data.cntWarningMax)}</InfoValue>
      </InfoItem>
      <InfoItem>
        <InfoLabel className="text-sm font-medium">
          Warning time <ITooltip value={ToolTips.WarningTime} />:
        </InfoLabel>
        <InfoValue>{roundsToDuration(data.roundsWarning, TimeParams.warn, true)}</InfoValue>
      </InfoItem>
    </InfoSection>
  );
};

export default WarningsSection;
