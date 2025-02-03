import { ValidatorAdApiCall } from "@/api/contract/ValidatorAdCall";
import { notify } from "@/components/Notification/notification";
import TermsAndConditions from "@/components/TermsAndConditions/TermsAndConditions";
import ITooltip from "@/components/Tooltip/ITooltip";
import { LoadingButton } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Wallet } from "@/components/Wallet/Wallet";
import {
  ASA_ID_ALGO,
  BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY,
  MBR_ACCOUNT,
  MBR_ASA,
  MBR_NOTICEBOARD_VALIDATOR_AD_CONTRACT_INCREASE,
  MBR_USER_BOX,
  MBR_VALIDATOR_AD_ASA_BOX,
  ROLE_DEL_STR,
} from "@/constants/smart-contracts";
import { TC_LATEST } from "@/constants/terms-and-conditions";
import { ToolTips } from "@/constants/tooltips";
import { ALGORAND_DEPOSIT_DECIMALS } from "@/constants/units";
import { useAppGlobalState } from "@/contexts/AppGlobalStateContext";
import { useValAdDrawer } from "@/contexts/ValAdDrawerContext";
import { UserInfo } from "@/interfaces/contracts/User";
import useTxnLoader from "@/store/txnLoaderStore";
import useUserStore from "@/store/userStore";
import { BoxUtils } from "@/utils/contract/box-utils";
import { algoBigIntToDisplay } from "@/utils/convert";
import { useWallet } from "@txnlab/use-wallet-react";
import { useEffect, useState } from "react";

import ConfigureAdDialog from "./ConfigureAdDialog";

const PublishAndPayCard = () => {
  const { form } = useValAdDrawer();
  const { activeAddress, transactionSigner } = useWallet();
  const { user, setUser } = useUserStore();
  const { algorandClient, noticeboardApp } = useAppGlobalState();

  const [termsChecked, setTermsChecked] = useState<boolean>(false);
  const [role, setRole] = useState<string>("");
  const [algoDeposit, setAlgoDeposit] = useState<number>(MBR_NOTICEBOARD_VALIDATOR_AD_CONTRACT_INCREASE + MBR_USER_BOX);

  const [preparingAd, setPreparingAd] = useState<boolean>(false);
  const [createdAppId, setCreatedAppId] = useState<bigint>(0n);
  const { txnLoading, setTxnLoading } = useTxnLoader();

  const valRegFee = noticeboardApp.globalState!.noticeboardFees.valUserReg;
  const valCreateFee = noticeboardApp.globalState!.noticeboardFees.valAdCreation;

  useEffect(() => {
    const fetch = async () => {
      // Get box MBR
      const boxDel = (
        await BoxUtils.getNoticeboardBox(algorandClient.client.algod, BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY)
      ).value;
      const boxDelSize = boxDel.length;
      const mbrDelegatorTemplateBox = BoxUtils.calculateBoxMBR(boxDelSize, BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY);

      // Get MBR for asset
      let validatorAdNewAssetFee = 0;
      const currentValues = form.getValues();
      if (BigInt(currentValues.paymentCurrency) !== ASA_ID_ALGO) {
        validatorAdNewAssetFee = MBR_ASA + MBR_VALIDATOR_AD_ASA_BOX;
      }

      // Total MBR
      let totalDeposit =
        MBR_NOTICEBOARD_VALIDATOR_AD_CONTRACT_INCREASE + MBR_ACCOUNT + mbrDelegatorTemplateBox + validatorAdNewAssetFee;

      // Get user role
      if (user) {
        if (user.userInfo) {
          const role = new TextDecoder().decode(new Uint8Array(user.userInfo.role));
          setRole(role);
        } else {
          setRole("");
          totalDeposit += MBR_USER_BOX;
        }
      } else {
        setRole("");
        totalDeposit += MBR_USER_BOX;
      }

      setAlgoDeposit(totalDeposit);
    };

    fetch();
  }, [activeAddress, form]);

  const handleCreate = async () => {
    console.log("Submit txn");
    setTxnLoading(true);

    if (role === "") {
      try {
        const res = await ValidatorAdApiCall.userCreateAndAdCreate({
          algorandClient: algorandClient,
          noticeBoardClient: noticeboardApp.client,
          gsNoticeBoard: noticeboardApp!.globalState!,
          userAddress: activeAddress!,
          signer: transactionSigner,
        });

        console.log("Created ad with ID: " + res.returns[1]);
        console.log(res.transactions[0].txID());

        if (res.returns[1]) {
          // User and ad creation was successful
          const userInfo = await UserInfo.getUserInfo(algorandClient.client.algod, activeAddress!);
          setUser({ ...user!, userInfo: userInfo });
          // Continue with configuration through popup
          setPreparingAd(true);
          setCreatedAppId(res.returns[1]);
          notify({ title: "Ad created successfully", variant: "success", onMountDismiss: ["txnLoading"] });
        }
      } catch (error) {
        console.error("Error in submit:", error);
        notify({ title: "Ad creation failed", variant: "error", onMountDismiss: ["txnLoading"] });
      }
    } else {
      try {
        const res = await ValidatorAdApiCall.adCreate({
          algorandClient: algorandClient,
          noticeBoardClient: noticeboardApp.client,
          gsNoticeBoard: noticeboardApp!.globalState!,
          userAddress: activeAddress!,
          userInfo: user?.userInfo!,
          signer: transactionSigner,
        });

        console.log("Created ad with ID: " + res.return);
        console.log(res.transactions[0].txID());
        notify({ title: "Ad created successfully", variant: "success", onMountDismiss: ["txnLoading"] });

        if (res.return) {
          // Ad creation was successful
          // Update userInfo without need for refetch
          const updatedAppIds = [...user!.userInfo!.appIds];
          const idx = user!.userInfo!.getFreeAppIndex(); // Know where it is stored
          updatedAppIds[idx] = res.return;
          setUser({ ...user!, userInfo: new UserInfo({ ...user!.userInfo!, appIds: updatedAppIds }) });
          // Continue with configuration through popup
          setPreparingAd(true);
          setCreatedAppId(res.return);
        }
      } catch (error) {
        console.error("Error in submit:", error);
        notify({ title: "Ad creation failed", variant: "error", onMountDismiss: ["txnLoading"] });
      }
    }

    setTxnLoading(false);
    console.log("Submitted txn");
  };

  if (role === ROLE_DEL_STR) {
    return (
      <div className="rounded-lg border border-border bg-background-light p-3">
        <div className="space-y-1">
          <div className="flex gap-1 text-sm">
            Your address is already registered as Algorand user for staking. <br />
            Please use a different address to become a node runner.
          </div>
          <Wallet className="mt-4 w-full" />
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-border bg-background-light p-3">
      <div className="space-y-1">
        {role === "" && (
          <div className="flex gap-1 text-sm">
            <div>First-time registration fee:</div>
            <div>{algoBigIntToDisplay(valRegFee, "none", true, ALGORAND_DEPOSIT_DECIMALS)}</div>
          </div>
        )}
        <div className="flex gap-1 text-sm">
          <div>Ad creation fee:</div>
          <div>{algoBigIntToDisplay(valCreateFee, "none", true, ALGORAND_DEPOSIT_DECIMALS)}</div>
        </div>
        <div className="flex gap-1 text-sm">
          <div className="flex items-center gap-1">
            Algorand deposit{" "}
            <ITooltip value={role === "" ? ToolTips.AlgorandDepositUserAndVal : ToolTips.AlgorandDepositVal} /> :
          </div>
          <div>{algoBigIntToDisplay(BigInt(algoDeposit), "none", true, ALGORAND_DEPOSIT_DECIMALS)}</div>
        </div>
      </div>
      <div className="mt-6 flex space-x-2">
        <Checkbox onCheckedChange={(v) => setTermsChecked(v === "indeterminate" ? false : v)} />
        <Label className="text-sm font-normal">
          I have read, understand, and agree with <TermsAndConditions terms={TC_LATEST} />.
        </Label>
      </div>
      {activeAddress ? (
        <LoadingButton
          type="submit"
          variant={"v_primary"}
          loading={txnLoading}
          className="mt-4 w-full"
          disabled={!termsChecked || (!form.formState.isValid && form.formState.isDirty)}
          onClick={handleCreate}
        >
          Publish & Pay
        </LoadingButton>
      ) : (
        <Wallet className="mt-4 w-full" text={"Connect Wallet to Continue"} />
      )}
      <ConfigureAdDialog openDialog={preparingAd} setOpenDialog={setPreparingAd} createdAppId={createdAppId} />
    </div>
  );
};

export default PublishAndPayCard;
