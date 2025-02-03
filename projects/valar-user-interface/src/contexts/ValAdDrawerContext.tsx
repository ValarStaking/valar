import { ValidatorQuery } from "@/api/queries/validator-ads";
import { AD_FORM_DEFAULTS } from "@/constants/platform";
import { ValidatorAdGlobalState } from "@/interfaces/contracts/ValidatorAd";
import { adFormSchema } from "@/lib/form-schema";
import { AdFormValuesDisplay } from "@/lib/types";
import { ValAdToForm } from "@/utils/convert";
import { zodResolver } from "@hookform/resolvers/zod";
import { createContext, useContext, useEffect, useState } from "react";
import { useForm, UseFormReturn } from "react-hook-form";
import { z } from "zod";

import { useAppGlobalState } from "./AppGlobalStateContext";

type ValAdDrawerContextType = {
  openDrawer: boolean;
  setOpenDrawer: React.Dispatch<React.SetStateAction<boolean>>;
  valAppId: bigint | undefined;

  isEditing: boolean;
  setIsEditing: React.Dispatch<React.SetStateAction<boolean>>;

  form: UseFormReturn<z.infer<typeof adFormSchema>>;
  gsValAd: ValidatorAdGlobalState | undefined;

  formDefaults: AdFormValuesDisplay;
  setFormDefaults: React.Dispatch<React.SetStateAction<AdFormValuesDisplay>>;
};

const ValAdDrawerContext = createContext<ValAdDrawerContextType | undefined>(undefined);

// Create a provider component
export const ValAdDrawerProvider: React.FC<{
  children: React.ReactNode;
  openDrawer: boolean;
  setOpenDrawer: React.Dispatch<React.SetStateAction<boolean>>;
  valAppId: bigint | undefined;
  onClose?: () => void;
}> = ({ children, openDrawer, setOpenDrawer, valAppId, onClose }) => {
  const { algorandClient } = useAppGlobalState();
  const [isEditing, setIsEditing] = useState(!valAppId);
  const [gsValAd, setGsValAd] = useState<ValidatorAdGlobalState | undefined>(undefined);
  const [mount, setMount] = useState<boolean>(true);

  /**
   * Mount is when the component is being rendering for the First Time.
   * We are setting it to False, after the First Render. And it remains false for Update Renders.
   */
  useEffect(() => setMount(false), []);

  /**
   * =============================
   *     Validator Ad Form
   * =============================
   */

  const adFormDefaults = {
    ...AD_FORM_DEFAULTS,
    paymentCurrency: AD_FORM_DEFAULTS.paymentCurrency.toString(),
  };
  const [formDefaults, setFormDefaults] = useState<AdFormValuesDisplay>(adFormDefaults);

  const form = useForm<z.infer<typeof adFormSchema>>({
    resolver: zodResolver(adFormSchema),
    defaultValues: formDefaults,
    mode: "all",
  });

  // Fetching Validator Ad
  useEffect(() => {
    const fetch = async () => {
      if (valAppId) {
        console.log(`Fetching validator ad with ID: ${valAppId}.`);

        try {
          const res = await ValidatorQuery.fetchValidatorAds(algorandClient.client.algod, [valAppId]);

          if (res) {
            const gsValAd = res.get(valAppId)!;
            console.log("Validator Ad ::", gsValAd);
            setGsValAd(gsValAd);

            const formValues = await ValAdToForm(gsValAd);
            const formDefaults = {
              ...formValues,
              paymentCurrency: formValues.paymentCurrency.toString(),
            };

            setFormDefaults(formDefaults);
            form.reset(formDefaults);

            return;
          }
        } catch (e) {}
      }

      setGsValAd(undefined);
      setFormDefaults(adFormDefaults);
    };

    fetch();
  }, [valAppId]);

  // onClose Integration
  useEffect(() => {
    if (!mount && !openDrawer && onClose) {
      onClose();
    }
  }, [openDrawer]);

  return (
    <ValAdDrawerContext.Provider
      value={{
        openDrawer,
        setOpenDrawer,
        valAppId,
        isEditing,
        setIsEditing: setIsEditing,
        form,
        gsValAd,
        formDefaults,
        setFormDefaults,
      }}
    >
      {children}
    </ValAdDrawerContext.Provider>
  );
};

// Custom hook to use the context
export const useValAdDrawer = (): ValAdDrawerContextType => {
  const context = useContext(ValAdDrawerContext);
  if (!context) {
    throw new Error("useValAdDrawerContext must be used within a ValAdDrawerProvider");
  }
  return context;
};