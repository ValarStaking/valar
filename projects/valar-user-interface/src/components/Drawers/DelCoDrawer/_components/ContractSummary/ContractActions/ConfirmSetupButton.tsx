import { DelegatorApiCall } from "@/api/contract/DelegatorCall";
import { notify } from "@/components/Notification/notification";
import { LoadingButton } from "@/components/ui/button";
import { DC_STATE_SUBMITTED } from "@/constants/states";
import { useAppGlobalState } from "@/contexts/AppGlobalStateContext";
import { useDelCoDrawer } from "@/contexts/DelCoDrawerContext";
import { UserInfo } from "@/interfaces/contracts/User";
import useTxnLoader from "@/store/txnLoaderStore";
import useUserStore from "@/store/userStore";
import { bytesToStr } from "@/utils/convert";
import { useWallet } from "@txnlab/use-wallet-react";

const ConfirmSetupButton = () => {
  const { algorandClient, noticeboardApp } = useAppGlobalState();
  const { activeAddress, transactionSigner } = useWallet();
  const { user } = useUserStore();

  const { gsDelCo, gsValAd, setRefetch } = useDelCoDrawer();

  const { txnLoading, setTxnLoading } = useTxnLoader();

  const handleConfirmSetup = async () => {
    console.log("Submitting txn to confirm setup...");

    if (!gsDelCo || !gsValAd) return;

    setTxnLoading(true);
    try {
      const userInfo = await UserInfo.getUserInfo(algorandClient.client.algod, activeAddress!);

      const res = await DelegatorApiCall.keysConfirm({
        algorandClient: algorandClient,
        noticeBoardClient: noticeboardApp.client,
        gsValAd,
        gsDelCo,
        user: { ...user!, userInfo: userInfo },
        signer: transactionSigner,
      });

      if (res.transactions[0]) {
        console.log(`Confirmed keys for account ${gsDelCo.delBeneficiary} under service contract ID ${gsDelCo.appId}.`);
        console.log(res.transactions[0].txID());

        setRefetch(true);
        notify({ title: "Setup confirmed successfully", variant: "success", onMountDismiss: ["txnLoading"] });
      }
    } catch (error) {
      console.error("Error in submit:", error);
      notify({ title: "Setup confirmation failed", variant: "error", onMountDismiss: ["txnLoading"] });
    }

    setTxnLoading(false);
  };

  return (
    <LoadingButton
      loading={txnLoading}
      variant={"v_primary"}
      className="w-full text-sm"
      disabled={bytesToStr(gsDelCo!.stateCur) !== bytesToStr(DC_STATE_SUBMITTED)}
      onClick={handleConfirmSetup}
    >
      Confirm Setup
    </LoadingButton>
  );
};

export default ConfirmSetupButton;
