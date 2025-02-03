import { ValidatorAdApiCall } from "@/api/contract/ValidatorAdCall";
import { notify } from "@/components/Notification/notification";
import { LoadingButton } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { TC_LATEST } from "@/constants/terms-and-conditions";
import { useAppGlobalState } from "@/contexts/AppGlobalStateContext";
import { useValAdDrawer } from "@/contexts/ValAdDrawerContext";
import useTxnLoader from "@/store/txnLoaderStore";
import useUserStore from "@/store/userStore";
import { formToTermsAndConfig, hexToBytes } from "@/utils/convert";
import { useWallet } from "@txnlab/use-wallet-react";
import { Dispatch, SetStateAction } from "react";

const ConfigureAdDialog = ({
  createdAppId,
  openDialog,
  setOpenDialog,
}: {
  createdAppId: bigint;
  openDialog: boolean;
  setOpenDialog: Dispatch<SetStateAction<boolean>>;
}) => {
  const { activeAddress, transactionSigner } = useWallet();
  const { user } = useUserStore();
  const { algorandClient, noticeboardApp } = useAppGlobalState();
  const { form, setOpenDrawer } = useValAdDrawer();

  const { txnLoading, setTxnLoading } = useTxnLoader();

  const handleConfigure = async () => {
    setTxnLoading(true);

    try {
      const { terms, config } = await formToTermsAndConfig(form.getValues(), noticeboardApp!.globalState!);
      const tcSha256 = hexToBytes(TC_LATEST);

      const res = await ValidatorAdApiCall.adTermsAndConfig({
        algorandClient: algorandClient,
        noticeBoardClient: noticeboardApp.client,
        gsValAd: undefined,
        userAddress: activeAddress!,
        userInfo: user?.userInfo!,
        valAppId: createdAppId,
        terms: terms,
        tcSha256: tcSha256,
        config: config,
        signer: transactionSigner,
      });

      console.log(res.transactions[0].txID());

      notify({ title: "Ad configured successfully", variant: "success", onMountDismiss: ["txnLoading"] });
    } catch (error) {
      console.error("Error in submit:", error);
      notify({ title: "Ad configuration failed", variant: "error", onMountDismiss: ["txnLoading"] });
    }

    setTxnLoading(false);
    setOpenDialog(false); // Close popup
    setOpenDrawer(false); // Close drawer
  };

  return (
    <Dialog open={openDialog} onOpenChange={setOpenDialog} modal={true}>
      <DialogContent className="w-[390px]" onInteractOutside={(e) => e.preventDefault()}>
        <DialogHeader>
          <DialogTitle className="text-base font-semibold text-text">Your Ad is being prepared.</DialogTitle>
          <DialogDescription className="text-sm text-text-tertiary">
            Your ad is almost ready. Please complete the configuration and it will get automatically published!
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="w-full">
          <LoadingButton variant={"v_primary"} loading={txnLoading} className="flex-grow" onClick={handleConfigure}>
            Configure
          </LoadingButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default ConfigureAdDialog;
