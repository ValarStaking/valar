import { Container } from "@/components/Container/Container";
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
import { Separator } from "@/components/ui/separator";
import { ValAdDrawerProvider } from "@/contexts/ValAdDrawerContext";
import { X } from "lucide-react";
import { useState } from "react";
import { DialogProps } from "vaul";

import ValAdDrawerContents from "./ValAdDrawerContents";

const ValAdDrawer: React.FC<{ valAppId?: bigint } & DialogProps> = ({ valAppId, ...props }) => {
  const [openDrawer, setOpenDrawer] = useState<boolean>(false);

  return (
    <ValAdDrawerProvider
      openDrawer={openDrawer}
      setOpenDrawer={setOpenDrawer}
      valAppId={valAppId}
      onClose={props.onClose}
    >
      <Drawer open={openDrawer} onOpenChange={setOpenDrawer} {...props}>
        <DrawerTrigger asChild>
          {!valAppId ? (
            <Button variant={"v_primary"} className="mt-3 w-full">
              Create Ad
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
        <DrawerContent className="h-[90%] rounded-t-3xl border-t border-border bg-background pb-10 pt-9 md:h-[calc(100vh-48px)] lg:h-[calc(100vh-72px)] lg:pt-6">
          <ScrollArea>
            <Container className="lg:px-4">
              <div className="space-y-1">
                <DrawerTitle className="font-bold">{!valAppId ? "Creating Ad" : "Ad Details"}</DrawerTitle>
                <DrawerDescription className="text-sm text-text">
                  {!valAppId
                    ? "Create an ad for your node by defining below your service terms and then publishing the ad."
                    : "Inspect or edit your ad details and monitor its performance."}
                </DrawerDescription>
              </div>
              <Separator className="mb-4 mt-2 bg-opacity-40" />
              <ValAdDrawerContents />
            </Container>
          </ScrollArea>
          <DrawerClose className="absolute right-4 top-3 lg:top-4">
            <X />
          </DrawerClose>
        </DrawerContent>
      </Drawer>
    </ValAdDrawerProvider>
  );
};

export default ValAdDrawer;
