import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  MIN_ALGO_STAKE_FOR_REWARDS,
  ROLE_DEL_STR,
} from "@/constants/smart-contracts";
import useUserStore from "@/store/userStore";
import { bytesToStr } from "@/utils/convert";
import { useWallet } from "@txnlab/use-wallet-react";
import { useEffect, useState } from "react";

const MinAlgoRequiredStakePopup = () => {
  const { user } = useUserStore();
  const { activeWallet } = useWallet();
  const [open, setOpen] = useState<boolean>(false);
  const retiURL = import.meta.env.VITE_RETI_URL;

  useEffect(() => {
    if (
      user && // If user has connected their wallet
      (user?.userInfo === undefined || // If user has not registered at the platform
        (user?.userInfo && bytesToStr(user.userInfo.role) === ROLE_DEL_STR)) && // If user has registered at the platform as delegator
      Number(user.beneficiary.algo) < MIN_ALGO_STAKE_FOR_REWARDS //Minimum Algo is required
    ) {
      setOpen(true);
    }
  }, [user]);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Notice about Staking Rewards</DialogTitle>
          <DialogDescription />
        </DialogHeader>
        <div className="text-text-tertiary">
          <div className="text-sm">
            Your balance is below 30,000 ALGO - the minimum defined by the
            Algorand network to be eligible for staking rewards. You will be
            able to earn Algorand staking rewards with peer-to-peer staking only
            if your balance is above the minimum. You acknowledge this by
            continuing to use the platform.
          </div>
          {retiURL && retiURL !== "null" && (
            <div className="mt-6 text-sm">
              You can earn staking rewards with your current balance using
              Valar's Reti staking pool.
            </div>
          )}
          <div className="mt-4 flex gap-2">
            <DialogClose asChild>
              <Button
                variant={"v_outline"}
                onClick={() => activeWallet?.disconnect()}
              >
                Cancel
              </Button>
            </DialogClose>
            <DialogClose asChild>
              <Button variant={"v_primary"} className="flex-grow">
                Continue
              </Button>
            </DialogClose>
            {retiURL && retiURL !== "null" && (
              <Button
                variant={"v_tertiary"}
                className="flex-grow"
                onClick={() =>
                  window.open(retiURL, "_blank", "noopener,noreferrer")
                }
              >
                To Staking Pool
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default MinAlgoRequiredStakePopup;
