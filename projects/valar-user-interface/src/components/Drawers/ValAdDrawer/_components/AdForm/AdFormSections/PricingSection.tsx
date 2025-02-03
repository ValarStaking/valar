import { FormInput, FormInputUnit, FormSelect } from "@/components/FormFields/FormFields";
import ITooltip from "@/components/Tooltip/ITooltip";
import { CURRENCIES, CURRENCIES_OPTIONS } from "@/constants/platform";
import { ToolTips } from "@/constants/tooltips";
import { UseFormReturn } from "react-hook-form";

import { AdFormGroup, AdFormInput, AdFormLabel, AdFormSection } from "../AdFormBuilder";

const PricingSection = ({ form, disabled = false }: { form: UseFormReturn<any>; disabled?: boolean }) => {
  return (
    <AdFormSection>
      <h1 className="text-sm">Pricing</h1>
      <AdFormGroup>
        <AdFormLabel>Payment currency</AdFormLabel>
        <AdFormInput>
          <FormSelect
            form={form}
            name="paymentCurrency"
            options={CURRENCIES_OPTIONS}
            placeholder="Select currency"
            onValueChangeEffect={(value: string) => {
              const suggestedDefaults = {
                ...form.getValues(),
                ...CURRENCIES.get(BigInt(value))!.adTermsFees,
              };

              form.reset({
                ...suggestedDefaults,
                paymentCurrency: suggestedDefaults.paymentCurrency.toString(),
              });
            }}
            disabled={disabled}
          />
        </AdFormInput>
      </AdFormGroup>
      <AdFormGroup>
        <AdFormLabel>
          Setup fee <ITooltip value={ToolTips.SetupFee} />
        </AdFormLabel>
        <AdFormInput>
          <FormInput form={form} name="setupFee" disabled={disabled} />
        </AdFormInput>
      </AdFormGroup>
      <AdFormGroup>
        <AdFormLabel>
          Min operational fee <ITooltip value={ToolTips.MinOperationalFee} />
        </AdFormLabel>
        <AdFormInput>
          <FormInputUnit form={form} name="minOperationalFee" unit="per month" disabled={disabled} />
        </AdFormInput>
      </AdFormGroup>
      <AdFormGroup>
        <AdFormLabel>
          Var operational fee <ITooltip value={ToolTips.VarOperationalFee} />
        </AdFormLabel>
        <AdFormInput>
          <FormInputUnit
            form={form}
            name="varOperationalFee"
            unit={<span>per month & per 100k ALGO</span>}
            disabled={disabled}
          />
        </AdFormInput>
      </AdFormGroup>
    </AdFormSection>
  );
};

export default PricingSection;
