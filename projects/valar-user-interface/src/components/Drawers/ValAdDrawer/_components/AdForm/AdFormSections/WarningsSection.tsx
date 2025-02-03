import { FormInput, FormInputUnit } from "@/components/FormFields/FormFields";
import ITooltip from "@/components/Tooltip/ITooltip";
import { ToolTips } from "@/constants/tooltips";
import { UseFormReturn } from "react-hook-form";

import { AdFormGroup, AdFormInput, AdFormLabel, AdFormSection } from "../AdFormBuilder";

const WarningsSection = ({ form, disabled = false }: { form: UseFormReturn<any>; disabled?: boolean }) => {
  return (
    <AdFormSection>
      <h1 className="text-sm">Warnings</h1>
      <AdFormGroup>
        <AdFormLabel>
          Max warnings <ITooltip value={ToolTips.MaxWarnings} />
        </AdFormLabel>
        <AdFormInput>
          <FormInput form={form} name="maxWarnings" disabled={disabled} />
        </AdFormInput>
      </AdFormGroup>
      <AdFormGroup>
        <AdFormLabel>
          Warning time <ITooltip value={ToolTips.WarningTime} />
        </AdFormLabel>
        <AdFormInput>
          <FormInputUnit form={form} name="warnTime" unit="hours" disabled={disabled} />
        </AdFormInput>
      </AdFormGroup>
    </AdFormSection>
  );
};

export default WarningsSection;
