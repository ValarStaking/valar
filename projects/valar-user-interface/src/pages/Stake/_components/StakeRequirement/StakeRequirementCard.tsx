import { InfoItem, InfoValue } from "@/components/Info/InfoUtilsCompo";
import MaxSettingsPopup from "@/components/Popup/MaxSettingsPopup";
import ITooltip from "@/components/Tooltip/ITooltip";
import { InputUnit } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import LinkExt from "@/components/ui/link-ext";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { CURRENCIES_OPTIONS, DEFAULT_MAX_STAKE, PAYMENT_ASA, SUGGESTED_DURATION } from "@/constants/platform";
import { ToolTips } from "@/constants/tooltips";
import { TimeParams } from "@/constants/units";
import { cn } from "@/lib/shadcn-utils";
import { StakeReqs } from "@/lib/types";
import useUserStore from "@/store/userStore";
import { getSuggestedMaxStake } from "@/utils/contract/helpers";
import { algoBigIntToDisplay, durationToRounds } from "@/utils/convert";
import { useEffect, useState } from "react";

const StakeRequirementCard = ({
  setStakeReqs,
  className,
}: {
  setStakeReqs: React.Dispatch<React.SetStateAction<StakeReqs>>;
  className?: string;
}) => {
  const { user, setUser } = useUserStore();
  const [duration, setDuration] = useState<number>(SUGGESTED_DURATION);
  const [maxStake, setMaxStake] = useState<bigint>(DEFAULT_MAX_STAKE);
  const [currency, setCurrency] = useState<bigint>(PAYMENT_ASA);

  const [useEscrow, setUseEscrow] = useState<boolean>(user?.beneficiary.address === user?.galgo?.address);

  useEffect(() => {
    if (user) {
      setMaxStake(getSuggestedMaxStake(user.beneficiary.algo));
    } else {
      setMaxStake(DEFAULT_MAX_STAKE);
    }
  }, [user]);

  useEffect(() => {
    if (user) {
      console.log("Switching user to...");
      if (useEscrow && user.galgo !== null) {
        setUser({ ...user, beneficiary: user.galgo });
        console.log("... gALGO escrow");
      } else {
        setUser({
          ...user,
          beneficiary: {
            address: user.address,
            algo: user.algo,
            assets: user.assets,
            keyRegParams: user.keyRegParams,
            trackedPerformance: user.trackedPerformance,
          },
        });
        console.log("... delegator manager");
      }
    }
  }, [useEscrow, user?.address]);

  useEffect(() => {
    const durationRounds = durationToRounds(duration, TimeParams.stake.unit);
    setStakeReqs({ duration: durationRounds, maxStake, currency });
    console.log("Selected staking requirements:");
    console.log({ durationRounds, maxStake, currency });
  }, [maxStake, duration, currency]);

  return (
    <div className={cn("rounded-lg bg-transparent lg:bg-background-light lg:px-2 lg:py-3", className)}>
      <h1 className="px-2 text-base font-bold">Define Your Staking Requirement</h1>
      <Separator className="mt-2 hidden bg-border lg:block" />
      <div className="px-2 py-2">
        <p className="text-xs text-text-tertiary">
          Please define your staking requirement and see your best matched node runners in the table below.
        </p>
        <div className="mt-3 flex items-end gap-2 rounded-lg bg-background-light p-2 lg:gap-6 lg:bg-transparent lg:p-0">
          <div className="flex w-auto flex-wrap items-center gap-4 lg:gap-2">
            <div className="flex gap-4">
              <div className="flex items-center gap-2 space-y-1">
                <Label className="text-sm">Duration</Label>
                <InputUnit
                  unit="days"
                  type={"number"}
                  value={duration}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                    return setDuration(Number(e.target.value));
                  }}
                  className="max-w-24 bg-background"
                />
              </div>
              <div className="flex items-center gap-2">
                <Label className="text-sm">Payment</Label>
                <Select
                  defaultValue={PAYMENT_ASA.toString()}
                  onValueChange={(value) => {
                    setCurrency(BigInt(value));
                  }}
                >
                  <SelectTrigger className="mr-2 bg-background">
                    <SelectValue defaultValue={PAYMENT_ASA.toString()} />
                  </SelectTrigger>
                  <SelectContent>
                    {CURRENCIES_OPTIONS.map((item, index) => (
                      <SelectItem key={index} value={item.value}>
                        {item.display}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="mr-4">
              <InfoItem className="gap-1">
                <Label className="text-sm">
                  Max stake <ITooltip value={<span>{ToolTips.MaxStake}</span>} /> :
                </Label>
                <InfoValue>{algoBigIntToDisplay(maxStake, "floor", true)}</InfoValue>
                <MaxSettingsPopup setMaxStake={setMaxStake} />
              </InfoItem>
            </div>
          </div>
        </div>
        {user && user.galgo !== null && <div className="mt-3 flex items-end gap-2 rounded-lg bg-background-light p-2  lg:gap-6 lg:bg-transparent lg:p-0">
          <div className="flex w-auto flex-wrap items-center gap-4 lg:gap-3">
            <div className="flex gap-4">
              <p className="text-sm">
                Stake with ALGO you used to mint gALGO on {" "}
                <LinkExt href={"https://app.folks.finance/algo-liquid-governance"} children={"Folks Finance"} className={"text-secondary"}/>?
              </p>
            </div>
            <div className="flex w-auto gap-2">
              <Switch
                className={""}
                checked={useEscrow}
                onCheckedChange={() => {setUseEscrow(!useEscrow)}}
                defaultChecked={useEscrow}
              />
              <p className="text-sm">Yes</p>
            </div>
          </div>
        </div>}
      </div>
    </div>
  );
};

export default StakeRequirementCard;
