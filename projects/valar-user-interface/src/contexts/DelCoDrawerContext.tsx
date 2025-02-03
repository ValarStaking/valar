import { DelegatorContractGlobalState } from "@/interfaces/contracts/DelegatorContract";
import { ValidatorAdGlobalState } from "@/interfaces/contracts/ValidatorAd";
import { StakeReqs } from "@/lib/types";
import React, { createContext, ReactNode, useContext, useEffect, useState } from "react";

type DelCoDrawerContextType = {
  openDrawer: boolean;
  setOpenDrawer: React.Dispatch<React.SetStateAction<boolean>>;
  gsDelCo: DelegatorContractGlobalState | undefined;
  setGsDelCo: React.Dispatch<React.SetStateAction<DelegatorContractGlobalState | undefined>>;
  gsValAd: ValidatorAdGlobalState | undefined;
  setGsValAd: React.Dispatch<React.SetStateAction<ValidatorAdGlobalState | undefined>>;
  delAppId: bigint | undefined;
  setDelAppId: React.Dispatch<React.SetStateAction<bigint | undefined>>;
  valAppId: bigint | undefined;
  setValAppId: React.Dispatch<React.SetStateAction<bigint | undefined>>;
  refetch: boolean;
  setRefetch: React.Dispatch<React.SetStateAction<boolean>>;
  stakeReqs: StakeReqs | undefined;
};

const DelCoDrawerContext = createContext<DelCoDrawerContextType | undefined>(undefined);

export const DelCoDrawerProvider: React.FC<{
  children: ReactNode;
  _valAppId: bigint | undefined;
  _delAppId: bigint | undefined;
  stakeReqs: StakeReqs | undefined;
  openDrawer: boolean;
  setOpenDrawer: React.Dispatch<React.SetStateAction<boolean>>;
  onClose?: () => void;
}> = ({ children, _valAppId, _delAppId, openDrawer, setOpenDrawer, stakeReqs, onClose }) => {
  const [gsDelCo, setGsDelCo] = useState<DelegatorContractGlobalState | undefined>(undefined);
  const [gsValAd, setGsValAd] = useState<ValidatorAdGlobalState | undefined>(undefined);
  const [delAppId, setDelAppId] = useState<bigint | undefined>(_delAppId);
  const [valAppId, setValAppId] = useState<bigint | undefined>(_valAppId);
  const [refetch, setRefetch] = useState<boolean>(true);
  const [mount, setMount] = useState<boolean>(true);

  /**
   * Mount is when the component is being rendering for the First Time.
   * We are setting it to False, after the First Render. And it remains false for Update Renders.
   */
  useEffect(() => setMount(false), []);

  // onClose Integration
  useEffect(() => {
    if (!mount && !openDrawer && onClose) {
      onClose();
    }
  }, [openDrawer]);

  return (
    <DelCoDrawerContext.Provider
      value={{
        openDrawer,
        setOpenDrawer,

        gsDelCo,
        setGsDelCo,

        gsValAd,
        setGsValAd,

        delAppId,
        setDelAppId,

        valAppId,
        setValAppId,

        refetch,
        setRefetch,

        stakeReqs,
      }}
    >
      {children}
    </DelCoDrawerContext.Provider>
  );
};

export function useDelCoDrawer() {
  const context = useContext(DelCoDrawerContext);
  if (context === undefined) {
    throw new Error("useDelCoDrawer must be within DelCoDrawerContextProvider");
  }
  return context;
}