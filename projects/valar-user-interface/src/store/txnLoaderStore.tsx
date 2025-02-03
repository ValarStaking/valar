import LoadingSpinner from "@/components/Loader/loading-spinner";
import { cn } from "@/lib/shadcn-utils";
import { toast } from "sonner";
import { create } from "zustand";

interface TxnState {
  txnLoading: boolean;
  setTxnLoading: (loading: boolean) => void;
}

const useTxnLoader = create<TxnState>((set) => ({
  txnLoading: false,
  setTxnLoading: (loading) => {set({ txnLoading: loading })
  if (loading) {
    toast.custom(
      () => (
        <div className={cn("w-[22rem] rounded-lg bg-gray-800 p-4 text-white")}>
          <div className="grid grid-cols-[1rem_auto] gap-x-2">
            <LoadingSpinner className="col-start-1 w-full place-self-center" />
            <h3 className="font-semibold">Transaction Processing</h3>
            <h6 className="col-start-2 text-sm font-normal text-opacity-20">Please check your wallet to confirm.</h6>
          </div>
        </div>
      ),
      { id: "txnLoading", duration: Infinity },
    );
  } else {
    toast.dismiss("txnLoading");
  }
},
}));

export default useTxnLoader;
