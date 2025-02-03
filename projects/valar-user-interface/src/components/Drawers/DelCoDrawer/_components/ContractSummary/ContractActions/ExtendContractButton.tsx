import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";

const ExtendContractButton = () => {
  const handleExtend = async () => {
  };
  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <Button variant={"v_primary"} className="w-1/2 text-sm">
          Extend Contract
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="text-base font-semibold text-text">
            Define your new staking requirements.
          </AlertDialogTitle>
          <AlertDialogDescription className="text-sm text-text-tertiary">
            To extend the staking with the same node runner, please define your new requirements.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter className="w-full">
          <AlertDialogCancel className="flex-grow">Cancel</AlertDialogCancel>
          <AlertDialogAction className="flex-grow" onClick={handleExtend}>
            Extend
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
};

export default ExtendContractButton;
