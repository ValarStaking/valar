import { DelegatorApiCall } from "@/api/contract/DelegatorCall";
import { notify } from "@/components/Notification/notification";
import { LoadingButton } from "@/components/ui/button";
import { useAppGlobalState } from "@/contexts/AppGlobalStateContext";
import { useDelCoDrawer } from "@/contexts/DelCoDrawerContext";
import useTxnLoader from "@/store/txnLoaderStore";
import useUserStore from "@/store/userStore";
import { useWallet } from "@txnlab/use-wallet-react";

const ArchiveContractButton = () => {
  const { algorandClient, noticeboardApp } = useAppGlobalState();
  const { activeAddress, transactionSigner } = useWallet();
  const { user } = useUserStore();
  const { gsDelCo, gsValAd, setOpenDrawer, setRefetch } = useDelCoDrawer();

  const { txnLoading, setTxnLoading } = useTxnLoader();

  const handleArchive = async () => {
    console.log("Submitting txn to archive contract...");

    if (!gsDelCo || !gsValAd) return;

    setTxnLoading(true);
    try {
      const res = await DelegatorApiCall.contractDelete({
        algorandClient: algorandClient,
        noticeBoardClient: noticeboardApp.client,
        gsValAd,
        gsDelCo,
        userAddress: activeAddress!,
        delUserInfo: user!.userInfo!,
        signer: transactionSigner,
      });

      if (res.transactions[0]) {
        console.log(`Archived service contract ID ${gsDelCo.appId}.`);
        console.log(res.transactions[0].txID());
        notify({ title: "Contract archived successfully", variant: "success", onMountDismiss: ["txnLoading"] });

        setRefetch(true);
        setOpenDrawer(false);
      }
    } catch (error) {
      console.error("Error in submit:", error);
      notify({ title: "Contract archive failed", variant: "error", onMountDismiss: ["txnLoading"] });
    }
    setTxnLoading(false);
  };
  return (
    <LoadingButton loading={txnLoading} variant={"v_primary"} className="w-full text-sm" onClick={handleArchive}>
      Archive Contract
    </LoadingButton>
  );
};

export default ArchiveContractButton;
