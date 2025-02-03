import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { InputUnit } from "@/components/ui/input";
import useUserStore from "@/store/userStore";
import { DEFAULT_MAX_STAKE, LIMITS_MAX_STAKE } from "@/constants/platform";
import { getSuggestedMaxStake } from "@/utils/contract/helpers";
import { algoBigIntToDisplay, algoDisplayToBigInt } from "@/utils/convert";
import { Settings } from "lucide-react";
import { useEffect, useState } from "react";

const MaxSettingsPopup = ({
  setMaxStake,
}:{
  setMaxStake: React.Dispatch<React.SetStateAction<bigint>>;
}) => {
  const { user } = useUserStore();

  const [selectedMaxStake, setSelectedMaxStake] = useState<number>(Number(algoBigIntToDisplay(DEFAULT_MAX_STAKE,"ceil")));

  useEffect(() => {
    if(user){
      setSelectedMaxStake(Number(algoBigIntToDisplay(getSuggestedMaxStake(user.beneficiary.algo), "floor")));
    } else {
      setSelectedMaxStake(Number(algoBigIntToDisplay(DEFAULT_MAX_STAKE,"ceil")));
    }
  }, [user]);

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Settings className="h-4 w-4 cursor-pointer" />
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Max Stake Settings</DialogTitle>
          <DialogDescription className="text-text-tertiary">
            You will stop staking if your account has more ALGO than the maximum agreed with the node runner.
          </DialogDescription>
        </DialogHeader>
        <div>
          <div className="mt-6 flex gap-4">
            <InputUnit
              unit="ALGO"
              type={"number"}
              value={selectedMaxStake}
              onChange={ (e: React.ChangeEvent<HTMLInputElement>) => {
                let selected = Number(e.target.value);
                if(user && selected < Number(algoBigIntToDisplay(user!.beneficiary.algo, "ceil"))) selected = Number(algoBigIntToDisplay(user!.beneficiary.algo, "ceil"));
                const isInteger = Math.abs(selected % 1) === 0;
                if(!isInteger) selected = Math.ceil(selected);
                if(selected > LIMITS_MAX_STAKE.max) selected = Math.floor(LIMITS_MAX_STAKE.max);
                if(selected < 0) selected = 0;
                setSelectedMaxStake(selected);
              }}
            />
            <Button
              variant={"v_link"}
              className="text-text-tertiary hover:text-text"
              onClick={ () => {
                if(user){
                  setSelectedMaxStake(Number(algoBigIntToDisplay(getSuggestedMaxStake(user.beneficiary.algo),"floor")));
                } else {
                  setSelectedMaxStake(Number(algoBigIntToDisplay(DEFAULT_MAX_STAKE,"ceil")));
                }
              }}
            >
              Set to Default
            </Button>
          </div>
          {user && (
            <div className="mt-2 flex gap-1 text-xs">
              <div>Your stake:</div>
              <div>{algoBigIntToDisplay(user.beneficiary.algo,"floor") + " ALGO"}</div>
            </div>
          )}
          <DialogClose className="mt-6 flex w-full gap-2">
            <Button variant={"v_outline"} className="w-full">
              Cancel
            </Button>
            <Button
              variant={"v_primary"}
              className="w-full"
              onClick={ () => {setMaxStake(algoDisplayToBigInt(selectedMaxStake))} }
            >
              Confirm
            </Button>
          </DialogClose>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default MaxSettingsPopup;
