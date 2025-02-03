import { InfoHeading, InfoItem, InfoLabel, InfoSection, InfoValue } from "@/components/Info/InfoUtilsCompo";
import ITooltip from "@/components/Tooltip/ITooltip";
import LinkExt from "@/components/ui/link-ext";
import { ToolTips } from "@/constants/tooltips";
import { getExplorerConfigFromViteEnvironment } from "@/utils/config/getExplorerConfig";

export type EligibilitySectionType = {
  asa1Amount: bigint;
  asa1Id: bigint;
  asa2Amount: bigint;
  asa2Id: bigint;
};

const EligibilitySection = ({ data }: { data: EligibilitySectionType }) => {
  const { assetUrl } = getExplorerConfigFromViteEnvironment();
  // Leave out the section if there is no eligibility requirement
  if (data.asa1Id === 0n && data.asa2Id === 0n) return;

  // Different section section if there is just one eligibility requirement
  if ( (data.asa1Id !== 0n && data.asa2Id === 0n) || (data.asa1Id === 0n && data.asa2Id !== 0n) ) {
    let asa = data.asa1Id !== 0n ? data.asa1Id : data.asa2Id;
    let amount = data.asa1Id !== 0n ? data.asa1Amount : data.asa2Amount;
    
    return (
      <InfoSection>
        <InfoHeading>Eligibility requirements</InfoHeading>
        <InfoItem>
          <InfoLabel>
            Amount of ASA <ITooltip value={ToolTips.EligibilityASASingle} />:
          </InfoLabel>
          <InfoValue>{amount.toString()}</InfoValue>
          <InfoValue>
            (ID:
            <LinkExt href={assetUrl + asa.toString()}>{asa.toString()}</LinkExt>)
          </InfoValue>
        </InfoItem>
      </InfoSection>
    );
  } else {
    return (
      <InfoSection>
        <InfoHeading>Eligibility requirements</InfoHeading>
        <InfoItem>
          <InfoLabel>
            Amount of ASA1 <ITooltip value={ToolTips.EligibilityASA} />:
          </InfoLabel>
          <InfoValue>{data.asa1Amount.toString()}</InfoValue>
          <InfoValue>
            (ID:
            <LinkExt href={assetUrl + data.asa1Id.toString()}>{data.asa1Id.toString()}</LinkExt>)
          </InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel>
            Amount of ASA2 <ITooltip value={ToolTips.EligibilityASA} />:
          </InfoLabel>
          <InfoValue>{data.asa2Amount.toString()}</InfoValue>
          <InfoValue>
            (ID:
            <LinkExt href={assetUrl + data.asa2Id.toString()}>{data.asa2Id.toString()}</LinkExt>)
          </InfoValue>
        </InfoItem>
      </InfoSection>
    );
  }
};

export default EligibilitySection;
