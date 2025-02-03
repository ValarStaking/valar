import { Button } from "@/components/ui/button";
import {
  Drawer,
  DrawerClose,
  DrawerContent,
  DrawerDescription,
  DrawerTitle,
  DrawerTrigger,
} from "@/components/ui/drawer";
import { ScrollArea } from "@/components/ui/scroll-area";
import { DelCoDrawerProvider } from "@/contexts/DelCoDrawerContext";
import { StakeReqs } from "@/lib/types";
import { X } from "lucide-react";
import { useState } from "react";
import { DialogProps } from "vaul";

import DelCoDrawerContents from "./DelCoDrawerContents";

const DelCoDrawer: React.FC<
  {
    delAppId?: bigint;
    valAppId?: bigint;
    stakeReqs?: StakeReqs;
    canStake?: boolean;
  } & DialogProps
> = ({ delAppId, valAppId, stakeReqs, canStake, ...props }) => {
  const [openDrawer, setOpenDrawer] = useState<boolean>(false);

  return (
    <DelCoDrawerProvider
      stakeReqs={stakeReqs}
      openDrawer={openDrawer}
      setOpenDrawer={setOpenDrawer}
      _valAppId={valAppId}
      _delAppId={delAppId}
      onClose={props.onClose}
    >
      <Drawer open={openDrawer} onOpenChange={setOpenDrawer} {...props}>
        <DrawerTrigger asChild>
          {!delAppId ? (
            <Button variant={canStake ? "v_primary" : "v_outline"} className="w-full">
              {canStake ? "Stake" : "View"}
            </Button>
          ) : (
            <div>
              <Button className="hidden lg:block" variant={"v_link"}>
                Details
              </Button>
              <Button className="text-xs lg:hidden" variant={"v_outline"}>
                Details
              </Button>
            </div>
          )}
        </DrawerTrigger>
        <DrawerContent className="h-[90%] rounded-t-3xl border-t border-border bg-background pb-3 pt-12 md:h-[calc(100vh-48px)] lg:h-[calc(100vh-72px)] lg:pt-9">
          <DrawerTitle />
          <DrawerDescription />
          <ScrollArea>
            <DelCoDrawerContents />
          </ScrollArea>
          <DrawerClose className="absolute right-4 top-3 lg:top-4">
            <X />
          </DrawerClose>
        </DrawerContent>
      </Drawer>
    </DelCoDrawerProvider>
  );
};

export default DelCoDrawer;
