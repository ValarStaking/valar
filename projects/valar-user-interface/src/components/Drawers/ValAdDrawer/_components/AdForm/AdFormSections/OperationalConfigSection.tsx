import { FormInput, FormSwitch } from "@/components/FormFields/FormFields";
import ITooltip from "@/components/Tooltip/ITooltip";
import { ToolTips } from "@/constants/tooltips";
import { UseFormReturn } from "react-hook-form";

import { AdFormGroup, AdFormInput, AdFormLabel, AdFormSection } from "../AdFormBuilder";

const OperationalConfigSection = ({ form, disabled = false }: { form: UseFormReturn<any>; disabled?: boolean }) => {
  return (
    <AdFormSection>
      <h1 className="text-sm">Operational Configuration</h1>
      <AdFormGroup>
        <AdFormLabel className="w-[200px]">
          Manager Address <ITooltip value={ToolTips.ManagerAddress} />
        </AdFormLabel>
        <AdFormInput className="w-auto flex-1">
          <FormInput form={form} name="managerAddress" disabled={disabled} />
        </AdFormInput>
      </AdFormGroup>
      <div className="flex flex-wrap gap-4">
        <AdFormGroup>
          <AdFormLabel className="w-[200px]">
            Maximum no. of users <ITooltip value={ToolTips.MaxNoOfUsers} />
          </AdFormLabel>
          <AdFormInput className="w-auto flex-1">
            <FormInput form={form} name="maxUser" disabled={disabled} />
          </AdFormInput>
        </AdFormGroup>
        <AdFormGroup className="flex items-center justify-start">
          <AdFormLabel className="w-full text-nowrap">
            Accepting new users <ITooltip value={ToolTips.AcceptingNewUsers} />
          </AdFormLabel>
          <div className="flex items-center gap-2">
            <FormSwitch form={form} name="acceptingNewUser" disabled={disabled} />
            <AdFormLabel>Yes</AdFormLabel>
          </div>
        </AdFormGroup>
      </div>
    </AdFormSection>
  );
};

export default OperationalConfigSection;
