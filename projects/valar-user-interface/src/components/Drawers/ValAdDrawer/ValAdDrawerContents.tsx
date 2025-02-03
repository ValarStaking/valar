import { Button } from "@/components/ui/button";
import { Form } from "@/components/ui/form";
import { Separator } from "@/components/ui/separator";
import { AD_FORM_DEFAULTS } from "@/constants/platform";
import { useValAdDrawer } from "@/contexts/ValAdDrawerContext";
import { adFormSchema } from "@/lib/form-schema";
import { z } from "zod";

import EligibilitySection from "./_components/AdForm/AdFormSections/EligibilitySection";
import GraphWidget from "./_components/AdForm/AdFormSections/GraphWidget";
import OperationalConfigSection from "./_components/AdForm/AdFormSections/OperationalConfigSection";
import PricingSection from "./_components/AdForm/AdFormSections/PricingSection";
import StakeLimitSection from "./_components/AdForm/AdFormSections/StakeLimitsSection";
import TimingsSection from "./_components/AdForm/AdFormSections/TimingsSection";
import WarningsSection from "./_components/AdForm/AdFormSections/WarningsSection";
import EditAdButton from "./_components/AdForm/EditAdButton";
import EarningsCard from "./_components/EarningsCard";
import InfoCard from "./_components/InfoCard";
import PublishAndPayCard from "./_components/PublishAndPayCard";

const ValAdDrawerContents = () => {
  const { gsValAd, isEditing, form, formDefaults } = useValAdDrawer();

  //Submit Handler
  function onSubmit(values: z.infer<typeof adFormSchema>) {
    console.log(values);
  }

  return (
    <div className="flex flex-wrap-reverse gap-4 lg:flex-nowrap">
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
          <div className={`${!gsValAd ? "flex flex-wrap gap-6 lg:flex-nowrap" : "flex-1"}`}>
            <div>
              <div className={`${!gsValAd ? "grid grid-cols-1 gap-6 lg:grid-cols-2" : "grid gap-6 lg:grid-cols-2"}`}>
                <div className="space-y-8">
                  <PricingSection form={form} disabled={!isEditing} />
                  <StakeLimitSection form={form} disabled={!isEditing} />
                  <TimingsSection form={form} disabled={!isEditing} />
                </div>
                <div className="flex flex-col justify-between gap-8">
                  <GraphWidget form={form} />
                  <div className="w-full space-y-8">
                    <WarningsSection form={form} disabled={!isEditing} />
                    <EligibilitySection form={form} disabled={!isEditing} />
                  </div>
                </div>
              </div>
              {(!gsValAd || isEditing) && (
                <div className="flex w-full justify-end">
                  <Button
                    type="button"
                    variant={"v_link"}
                    className="text-text underline"
                    onClick={() =>
                      form.reset({
                        ...AD_FORM_DEFAULTS,
                        paymentCurrency: AD_FORM_DEFAULTS.paymentCurrency.toString(),
                        managerAddress: formDefaults.managerAddress,
                      })
                    }
                  >
                    Set to Default
                  </Button>
                </div>
              )}
              <Separator className="my-4" />
              <div>
                <OperationalConfigSection form={form} disabled={!isEditing} />
              </div>
            </div>
            {gsValAd && <EditAdButton />}
          </div>
        </form>
      </Form>
      <div className="flex flex-col gap-2 lg:min-w-[250px]">
        <div className="flex gap-2 lg:flex-col">
          {!gsValAd ? (
            <PublishAndPayCard />
          ) : (
            <>
              <InfoCard gsValAd={gsValAd} />
              <EarningsCard gsValAd={gsValAd} />
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ValAdDrawerContents;
