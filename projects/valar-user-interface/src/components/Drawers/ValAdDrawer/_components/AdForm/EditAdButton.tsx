import { ValidatorAdApiCall } from "@/api/contract/ValidatorAdCall";
import { notify } from "@/components/Notification/notification";
import TermsAndConditions from "@/components/TermsAndConditions/TermsAndConditions";
import { Button, LoadingButton } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { TC_LATEST } from "@/constants/terms-and-conditions";
import { useAppGlobalState } from "@/contexts/AppGlobalStateContext";
import { useValAdDrawer } from "@/contexts/ValAdDrawerContext";
import useTxnLoader from "@/store/txnLoaderStore";
import useUserStore from "@/store/userStore";
import { formToTermsAndConfig, hexToBytes } from "@/utils/convert";
import { useWallet } from "@txnlab/use-wallet-react";
import { useState } from "react";

const EditAdButton = () => {
  const { gsValAd, isEditing, setIsEditing, form, setOpenDrawer } = useValAdDrawer();
  const { activeAddress, transactionSigner } = useWallet();
  const { user } = useUserStore();
  const { algorandClient, noticeboardApp } = useAppGlobalState();

  const [termsChecked, setTermsChecked] = useState<boolean>(false);
  const { txnLoading, setTxnLoading } = useTxnLoader();

  const handleConfigure = async () => {
    console.log("Editing ad...");
    setTxnLoading(true);

    try {
      const { terms, config } = await formToTermsAndConfig(form.getValues(), noticeboardApp!.globalState!);
      const tcSha256 = hexToBytes(TC_LATEST);

      const res = await ValidatorAdApiCall.adTermsAndConfig({
        algorandClient: algorandClient,
        noticeBoardClient: noticeboardApp.client,
        gsValAd: gsValAd,
        userAddress: activeAddress!,
        userInfo: user?.userInfo!,
        valAppId: gsValAd!.appId,
        terms: terms,
        tcSha256: tcSha256,
        config: config,
        signer: transactionSigner,
      });

      console.log(res.transactions[0].txID());
      notify({ title: "Ad edited successfully", variant: "success", onMountDismiss: ["txnLoading"] });
      // If successful ad configuration, close drawer
      setOpenDrawer(false);
    } catch (error) {
      console.error("Error in submit:", error);
      notify({ title: "Ad edit failed", variant: "error", onMountDismiss: ["txnLoading"] });
    }

    setTxnLoading(false);
  };

  return (
    <div>
      {!isEditing ? (
        <Button type="button" variant={"v_secondary"} className="w-full lg:w-auto" onClick={() => setIsEditing(true)}>
          Edit Configuration
        </Button>
      ) : (
        <div>
          <div>
            <Checkbox onCheckedChange={(v) => setTermsChecked(v === "indeterminate" ? false : v)} />{" "}
            <label className="ml-2 text-sm">
              I have read, understand, and agree with <TermsAndConditions terms={TC_LATEST} />.
            </label>
          </div>
          <div className="mt-4 flex gap-10">
            <LoadingButton
              variant={"v_secondary"}
              loading={txnLoading}
              disabled={!termsChecked || (!form.formState.isValid && form.formState.isDirty)}
              onClick={handleConfigure}
            >
              Save Configuration
            </LoadingButton>
            <Button
              type="button"
              variant={"v_link"}
              onClick={() => {
                setIsEditing(false);
                setTermsChecked(false);
                setOpenDrawer(false);
              }}
            >
              Cancel
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default EditAdButton;
