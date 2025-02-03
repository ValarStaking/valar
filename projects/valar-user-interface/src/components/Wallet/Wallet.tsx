import { FolksFinance } from "@/api/contract/galgo/helpers";
import { UserQuery } from "@/api/queries/user";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { MBR_ACCOUNT, MIN_ALGO_STAKE_FOR_REWARDS } from "@/constants/smart-contracts";
import { useAppGlobalState } from "@/contexts/AppGlobalStateContext";
import { UserInfo } from "@/interfaces/contracts/User";
import { cn } from "@/lib/shadcn-utils";
import useUserStore, { AccountInfo } from "@/store/userStore";
import { ellipseAddress } from "@/utils/convert";
import { useWallet } from "@txnlab/use-wallet-react";
import { LogOut } from "lucide-react";
import { useEffect, useState } from "react";

import { notify } from "../Notification/notification";

export const Wallet = ({
  className,
  onClick,
  variant = "wallet",
  text = "Connect Wallet",
}: {
  className?: string;
  onClick?: () => void;
  variant?: "wallet" | "v_outline";
  text?: string;
}) => {
  const { activeAddress, wallets, activeWallet, activeAccount, activeWalletAccounts } = useWallet();
  const { user, setUser } = useUserStore();
  const { algorandClient } = useAppGlobalState();
  const algodClient = algorandClient.client.algod;
  const [open, onOpenChange] = useState<boolean | undefined>(undefined);

  useEffect(() => {
    const fetch = async () => {
      console.log(`Fetching user info for ${activeAddress}.`);
      //Fetching user role and algo amount
      if (activeAddress) {
        try {
          const userInfo = await UserInfo.getUserInfo(algodClient, activeAddress);

          const account = await UserQuery.getAccountInfo(algodClient, activeAddress);

          // Check if account has minted gALGO - if FolksFinance.appId is different than zero
          console.log("FolksFinance appId: ", FolksFinance.appId);
          let galgoAccount: AccountInfo | null = null;
          if (FolksFinance.appId !== 0) {
            const galgoEscrow = FolksFinance.getEscrow(activeAddress);
            console.log("Account's gALGO escrow on FolksFinance: ", galgoEscrow);

            galgoAccount = await UserQuery.getAccountInfo(algodClient, galgoEscrow);
            if (galgoAccount.algo < MBR_ACCOUNT) galgoAccount = null;
          }

          let beneficiary = account; // by default set connected user as beneficiary
          // Unless the account has less then min ALGO for staking but the gALGO escrow account does have more
          if (
            beneficiary.algo < MIN_ALGO_STAKE_FOR_REWARDS &&
            galgoAccount !== null &&
            galgoAccount.algo >= MIN_ALGO_STAKE_FOR_REWARDS
          ) {
            beneficiary = galgoAccount;
          }

          setUser({
            ...account,
            userInfo: userInfo,
            beneficiary: beneficiary,
            galgo: galgoAccount,
          });
        } catch (error) {
          console.error("Error in fetching user:", error);
        }
      } else {
        if (user) {
          // Clear user
          setUser(null);
        }
      }
    };

    fetch();
  }, [activeAddress]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>
        <Button variant={variant} className={cn("", className)}>
          {ellipseAddress(activeAddress as string) ?? text}
        </Button>
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          {!activeWallet ? (
            <DialogTitle> Connect Your Wallet </DialogTitle>
          ) : (
            <DialogTitle> Modify Your Wallet </DialogTitle>
          )}
          <DialogDescription>Select your wallet to access your account.</DialogDescription>
        </DialogHeader>
        {!activeWallet ? (
          <div className="flex flex-col gap-4">
            {wallets.map((wallet) => (
              <div
                className="flex w-full cursor-pointer items-center gap-4 rounded-lg p-2 hover:bg-background"
                key={wallet.id}
                onClick={async () => {
                  onOpenChange(false);
                  try {
                    const connectedWalletAccount = await wallet.connect();
                    if (connectedWalletAccount.length > 0) {
                      if (onClick) onClick();
                    } else {
                      console.log("No wallet account connected.");
                    }
                  } catch {
                    notify({ title: "Wallet connection failed.", variant: "error" });
                    console.log("Wallet was not connected.");
                  }
                }}
              >
                <img src={wallet.metadata.icon} className="h-9 w-9 rounded-lg" />
                <div className="w-auto">{wallet.metadata.name}</div>
              </div>
            ))}
          </div>
        ) : (
          <div>
            <div className="flex w-full items-center gap-4 rounded-lg bg-background p-2">
              <img src={activeWallet.metadata.icon} className="h-9 w-9 rounded-lg" />
              <div className="flex w-auto flex-grow items-center justify-between">
                <div className="">
                  <h1>{activeWallet.metadata.name} </h1>
                  <h6 className="max-w-lg text-xs">{ellipseAddress(activeAccount!.address as string)}</h6>
                </div>
                <div>
                  <LogOut className="mr-2 h-5 w-5 cursor-pointer" onClick={() => activeWallet.disconnect()} />
                </div>
              </div>
            </div>
            <Select
              defaultValue={activeAddress as string}
              onValueChange={(value) => activeWallet.setActiveAccount(value)}
            >
              <SelectTrigger className="mt-4 w-[180px] border-opacity-50">
                <SelectValue defaultValue={activeAccount?.name} placeholder="Choose a Address" />
              </SelectTrigger>
              <SelectContent>
                {activeWalletAccounts?.map((acc, index) => (
                  <SelectItem key={index} value={acc.address}>
                    {ellipseAddress(acc.address)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};
