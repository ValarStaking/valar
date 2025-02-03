import { FormInput } from "@/components/FormFields/FormFields";
import ITooltip from "@/components/Tooltip/ITooltip";
import { ToolTips } from "@/constants/tooltips";
import { UseFormReturn } from "react-hook-form";

import { AdFormGroup, AdFormInput, AdFormLabel, AdFormSection } from "../AdFormBuilder";

const EligibilitySection = ({ form, disabled = false }: { form: UseFormReturn<any>; disabled?: boolean }) => {
  return (
    <AdFormSection>
      <h1 className="text-sm">Eligibility Requirements</h1>
      <div className="flex gap-8">
        <AdFormGroup>
          <AdFormLabel>
            ASA1 <ITooltip value={ToolTips.EligibilityASAAdCreation} />
          </AdFormLabel>
          <AdFormInput className="w-full">
            <FormInput form={form} name="idASA1" disabled={disabled} />
          </AdFormInput>
        </AdFormGroup>
        <AdFormGroup>
          <AdFormLabel>Amount</AdFormLabel>
          <AdFormInput className="w-full">
            <FormInput form={form} name="amountASA1" disabled={disabled} />
          </AdFormInput>
        </AdFormGroup>
      </div>
      <div className="flex gap-8">
        <AdFormGroup>
          <AdFormLabel>
            ASA2 <ITooltip value={ToolTips.EligibilityASAAdCreation} />
          </AdFormLabel>
          <AdFormInput className="w-full">
            <FormInput form={form} name="idASA2" disabled={disabled} />
          </AdFormInput>
        </AdFormGroup>
        <AdFormGroup>
          <AdFormLabel>Amount</AdFormLabel>
          <AdFormInput className="w-full">
            <FormInput form={form} name="amountASA2" disabled={disabled} />
          </AdFormInput>
        </AdFormGroup>
      </div>
    </AdFormSection>
  );
};

export default EligibilitySection;
