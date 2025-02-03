import { FormLabel } from "@/components/ui/form";
import { cn } from "@/lib/shadcn-utils";
import { ReactNode } from "react";

export const AdFormSection = ({ className, children }: { children: ReactNode; className?: string }) => {
  return <div className={cn("space-y-2", className)}>{children}</div>;
};

export const AdFormGroup = ({ className, children }: { children: ReactNode; className?: string }) => {
  return <div className={cn("flex items-center justify-between gap-3", className)}>{children}</div>;
};

export const AdFormLabel = ({ className, children }: { children: ReactNode; className?: string }) => {
  return (
    <FormLabel className={cn("w-1/2 items-center gap-1 text-xs text-text-tertiary", className)}>{children}</FormLabel>
  );
};

export const AdFormInput = ({ className, children }: { children: ReactNode; className?: string }) => {
  return <div className={cn("w-1/2", className)}>{children}</div>;
};
