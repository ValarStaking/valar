import {
  // FormDate,
  FormInputUnit,
} from "@/components/FormFields/FormFields";
import ITooltip from "@/components/Tooltip/ITooltip";
import { ToolTips } from "@/constants/tooltips";
import { UseFormReturn } from "react-hook-form";

import { AdFormGroup, AdFormInput, AdFormLabel, AdFormSection } from "../AdFormBuilder";

const TimingsSection = ({ form, disabled = false }: { form: UseFormReturn<any>; disabled?: boolean }) => {
  return (
    <AdFormSection>
      <h1 className="text-sm">Timings</h1>
      <AdFormGroup>
        <AdFormLabel>Valid until</AdFormLabel>
        <AdFormInput>
          <FormInputUnit form={form} name="validUntil" unit="" disabled={disabled} />
        </AdFormInput>
      </AdFormGroup>
      <AdFormGroup>
        <AdFormLabel>Min contract duration</AdFormLabel>
        <AdFormInput>
          <FormInputUnit form={form} name="minDuration" unit="days" disabled={disabled} />
        </AdFormInput>
      </AdFormGroup>
      <AdFormGroup>
        <AdFormLabel>Max contract duration</AdFormLabel>
        <AdFormInput>
          <FormInputUnit form={form} name="maxDuration" unit="days" disabled={disabled} />
        </AdFormInput>
      </AdFormGroup>
      <AdFormGroup>
        <AdFormLabel>
          Setup time <ITooltip value={ToolTips.SetupTimeAdCreation} />
        </AdFormLabel>
        <AdFormInput>
          <FormInputUnit form={form} name="setupTime" unit="min" disabled={disabled} />
        </AdFormInput>
      </AdFormGroup>
      <AdFormGroup>
        <AdFormLabel>
          Confirmation time <ITooltip value={ToolTips.ConfirmationTimeAdCreation} />
        </AdFormLabel>
        <AdFormInput>
          <FormInputUnit form={form} name="confirmationTime" unit="hours" disabled={disabled} />
        </AdFormInput>
      </AdFormGroup>
    </AdFormSection>
  );
};

export default TimingsSection;
