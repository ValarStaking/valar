import { DelegatorApiCall } from "@/api/contract/DelegatorCall";
import { notify } from "@/components/Notification/notification";
import { Button, LoadingButton } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useAppGlobalState } from "@/contexts/AppGlobalStateContext";
import { useDelCoDrawer } from "@/contexts/DelCoDrawerContext";
import useTxnLoader from "@/store/txnLoaderStore";
import useUserStore from "@/store/userStore";
import { DialogClose } from "@radix-ui/react-dialog";
import { useWallet } from "@txnlab/use-wallet-react";

const WithdrawContractButton = ({ delAppId }: { delAppId: bigint }) => {
  const { algorandClient, noticeboardApp } = useAppGlobalState();
  const { transactionSigner } = useWallet();
  const { user } = useUserStore();

  const { gsDelCo, gsValAd, setRefetch } = useDelCoDrawer();

  const { txnLoading, setTxnLoading } = useTxnLoader();

  const handleWithdraw = async () => {
    console.log("Submitting txn to withdraw from contract...");

    if (!gsValAd || !gsDelCo || !user) return;

    setTxnLoading(true);
    try {
      const res = await DelegatorApiCall.contractWithdraw({
        algorandClient: algorandClient,
        noticeBoardClient: noticeboardApp.client,
        gsValAd,
        gsDelCo,
        user: { ...user },
        signer: transactionSigner,
      });

      if (res.transactions[0]) {
        console.log(`Withdrew from service contract ID ${gsDelCo.appId}.`);
        console.log(res.transactions[0].txID());
        notify({ title: "Contract withdrew successfully", variant: "success", onMountDismiss: ["txnLoading"] });

        setRefetch(true);
      }
    } catch (error) {
      console.error("Error in submit:", error);
      notify({ title: "Contract withdraw failed", variant: "error", onMountDismiss: ["txnLoading"] });
    }
    setTxnLoading(false);
  };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant={"v_outline"} className="w-full text-sm">
          Withdraw from Contract
        </Button>
      </DialogTrigger>
      <DialogContent onInteractOutside={(e) => e.preventDefault()}>
        <DialogHeader>
          <DialogTitle className="text-base font-semibold text-text">
            Are you sure want to withdraw from the contract?
          </DialogTitle>
          <DialogDescription className="text-sm text-text-tertiary">
            You are withdrawing from contract with ID: {delAppId.toString()}.
            <br />
            You will stop staking.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="w-full">
          <DialogClose className="flex-grow" asChild>
            <Button variant={"v_outline"}>Cancel</Button>
          </DialogClose>
          <LoadingButton loading={txnLoading} className="flex-grow bg-error hover:bg-error" onClick={handleWithdraw}>
            Withdraw
          </LoadingButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default WithdrawContractButton;
