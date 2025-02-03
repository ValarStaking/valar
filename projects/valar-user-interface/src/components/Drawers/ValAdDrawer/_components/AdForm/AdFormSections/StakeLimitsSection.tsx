import { FormInputUnit } from "@/components/FormFields/FormFields";
import ITooltip from "@/components/Tooltip/ITooltip";
import { ToolTips } from "@/constants/tooltips";
import { UseFormReturn } from "react-hook-form";

import { AdFormGroup, AdFormInput, AdFormLabel, AdFormSection } from "../AdFormBuilder";

const StakeLimitSection = ({ form, disabled = false }: { form: UseFormReturn<any>; disabled?: boolean }) => {
  return (
    <AdFormSection>
      <h1 className="text-sm">Stake Limits</h1>
      <AdFormGroup>
        <AdFormLabel>
          Max stake <ITooltip value={ToolTips.MaxStake} />
        </AdFormLabel>
        <AdFormInput>
          <FormInputUnit form={form} name="maxStake" unit="ALGO" disabled={disabled} />
        </AdFormInput>
      </AdFormGroup>
      <AdFormGroup>
        <AdFormLabel>
          Gratis stake <ITooltip value={ToolTips.GratisStake} />
        </AdFormLabel>
        <AdFormInput>
          <FormInputUnit form={form} name="gratisStake" unit="%" disabled={disabled} />
        </AdFormInput>
      </AdFormGroup>
    </AdFormSection>
  );
};

export default StakeLimitSection;
