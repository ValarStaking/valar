import { ValidatorAdApiCall } from "@/api/contract/ValidatorAdCall";
import { ValidatorQuery } from "@/api/queries/validator-ads";
import { InfoItem, InfoLabel, InfoValue } from "@/components/Info/InfoUtilsCompo";
import { notify } from "@/components/Notification/notification";
import { LoadingButton } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { CURRENCIES } from "@/constants/platform";
import { AssetParams } from "@/constants/units";
import { useAppGlobalState } from "@/contexts/AppGlobalStateContext";
import { ValidatorAdGlobalState } from "@/interfaces/contracts/ValidatorAd";
import { Earning } from "@/lib/types";
import useTxnLoader from "@/store/txnLoaderStore";
import useUserStore from "@/store/userStore";
import { assetAmountToFeeDisplay } from "@/utils/convert";
import { useWallet } from "@txnlab/use-wallet-react";
import { useEffect, useState } from "react";

const EarningsCard = ({ gsValAd }: { gsValAd: ValidatorAdGlobalState }) => {
  const [earnings, setEarnings] = useState<Earning[]>([]);
  const [gettingIncome, setGettingIncome] = useState<boolean>(false);
  const [selectedCurrency, setSelectedCurrency] = useState<string | undefined>(undefined);
  const { activeAddress, transactionSigner } = useWallet();
  const { user } = useUserStore();
  const { algorandClient, noticeboardApp } = useAppGlobalState();
  const algodClient = algorandClient.client.algod;

  const { txnLoading, setTxnLoading } = useTxnLoader();

  // Fetching all earnings at Validator Ad
  useEffect(() => {
    const fetch = async () => {
      if (!gettingIncome) {
        console.log("Fetching currencies and earnings of ad.");
        try {
          const earnings = await ValidatorQuery.fetchValEarnings(algodClient, gsValAd);
          setEarnings(earnings);
          setSelectedCurrency(gsValAd.termsPrice.feeAssetId.toString()); // By default, display earnings of current asset
        } catch {
          setEarnings([]);
        }
      }
    };

    fetch();
  }, [gsValAd, gettingIncome]);

  const selectedEarningData = earnings.find((earning) => earning.id.toString() === selectedCurrency);

  const handleIncome = async () => {
    setTxnLoading(true);
    console.log("Withdrawing earnings...");
    setGettingIncome(true);
    const assetId = gsValAd.termsPrice.feeAssetId;

    try {
      const res = await ValidatorAdApiCall.adIncome({
        noticeBoardClient: noticeboardApp.client,
        userAddress: activeAddress!,
        userInfo: user?.userInfo!,
        valAppId: gsValAd.appId,
        valAssetId: assetId,
        signer: transactionSigner,
      });

      if (res.confirmation) {
        console.log(`Withdrew earnings for asset ID ${assetId} in amount ${res.return}.`);
        console.log(res.transactions[0].txID());
        notify({ title: "Withdrew successfully", variant: "success", onMountDismiss: ["txnLoading"] });
      }
    } catch (error) {
      console.error("Error in submit:", error);
      notify({ title: "Withdraw failed", variant: "error", onMountDismiss: ["txnLoading"] });
    }

    setTxnLoading(false);
    setGettingIncome(false);
  };

  return (
    <div className="rounded-lg border border-border bg-background-light p-3">
      <div className="flex items-center gap-1 text-sm">
        <div>Your earnings for</div>
        <Select value={selectedCurrency} onValueChange={(value) => setSelectedCurrency(value)}>
          <SelectTrigger className="w-auto border-0 p-0 focus:ring-0 active:ring-0">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {earnings.map((item, index) => (
              <SelectItem key={index} value={item.id.toString()}>
                {CURRENCIES.get(item.id)!.ticker || "Unknown"}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="my-2 space-y-2">
        <InfoItem className="flex gap-1">
          <InfoLabel>Total earnings:</InfoLabel>
          <InfoValue>
            {selectedEarningData
              ? assetAmountToFeeDisplay(selectedEarningData.total, selectedEarningData.id, AssetParams.total, true)
              : "N/A"}
          </InfoValue>
        </InfoItem>
        <InfoLabel className="flex gap-1">
          <InfoLabel>Unclaimed earnings:</InfoLabel>
          <InfoValue>
            {selectedEarningData
              ? assetAmountToFeeDisplay(selectedEarningData.unclaimed, selectedEarningData.id, AssetParams.total, true)
              : "N/A"}
          </InfoValue>
        </InfoLabel>
      </div>
      <LoadingButton loading={txnLoading} className="w-full" variant={"v_primary"} onClick={handleIncome}>
        Get Earnings
      </LoadingButton>
    </div>
  );
};

export default EarningsCard;
