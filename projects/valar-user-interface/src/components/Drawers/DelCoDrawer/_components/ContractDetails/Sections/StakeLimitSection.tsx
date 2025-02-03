import { InfoHeading, InfoItem, InfoLabel, InfoSection, InfoValue } from "@/components/Info/InfoUtilsCompo";
import ITooltip from "@/components/Tooltip/ITooltip";
import { ToolTips } from "@/constants/tooltips";
import { ValTermsStakeLimitsInterface } from "@/interfaces/contracts/ValidatorAd";
import { algoBigIntToDisplay, gratisBigIntToNumber } from "@/utils/convert";

const StakeLimitsSection = ({ data }: { data: undefined | ValTermsStakeLimitsInterface }) => {
  // Leave out section if there is no eligibility data should not be displayed
  if (!data) return;

  return (
    <InfoSection>
      <InfoHeading className="text-sm font-semibold">Stake limits</InfoHeading>
      <InfoItem>
        <InfoLabel className="text-sm font-medium">
          Max stake <ITooltip value={ToolTips.MaxStake} />:
        </InfoLabel>
        <InfoValue>{algoBigIntToDisplay(data.stakeMax, "floor", true)}</InfoValue>
      </InfoItem>
      <InfoItem>
        <InfoLabel className="text-sm font-semibold">
          Gratis stake <ITooltip value={ToolTips.GratisStake} />
        </InfoLabel>
        <InfoValue>{gratisBigIntToNumber(data.stakeGratis) + " %"}</InfoValue>
      </InfoItem>
    </InfoSection>
  );
};

export default StakeLimitsSection;
