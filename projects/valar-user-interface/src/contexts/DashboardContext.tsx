import { createContext, useContext, useState } from "react";

type DashboardContextType = {
  valAdRefetch: boolean;
  setValAdRefetch: React.Dispatch<React.SetStateAction<boolean>>;

  delCoRefetch: boolean;
  setDelCoRefetch: React.Dispatch<React.SetStateAction<boolean>>;
};

const DashboardContext = createContext<DashboardContextType | undefined>(undefined);

export const DashboardContextProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [valAdRefetch, setValAdRefetch] = useState<boolean>(true);
  const [delCoRefetch, setDelCoRefetch] = useState<boolean>(true);

  return (
    <DashboardContext.Provider
      value={{ valAdRefetch, setValAdRefetch, delCoRefetch, setDelCoRefetch }}
    >
      {children}
    </DashboardContext.Provider>
  );
};

export const useDashboardContext = () => {
  const context = useContext(DashboardContext);
  if (!context) {
    throw new Error("useDashboardPageContext must be used within a DashboardPageProvider");
  }
  return context;
};
