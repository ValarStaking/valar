import { cn } from "@/lib/shadcn-utils";
import { cva } from "class-variance-authority";
import { Check, Info, X } from "lucide-react";
import { toast } from "sonner";

const notificationVariants = cva("w-[22rem] rounded-lg p-4", {
  variants: {
    variant: {
      success: "bg-success-background text-success-dark",
      error: "bg-error-background text-error",
      info: "bg-secondary-light text-primary",
    },
  },
});

const icons: Record<"success" | "error" | "info", React.ComponentType<any>> = {
  success: Check,
  error: X,
  info: Info,
};

export function notify({
  title,
  description,
  variant = "success",
}: {
  title: string;
  description?: string;
  variant?: "success" | "error" | "info";
}) {
  const Icon = icons[variant];

  toast.custom((t) => (
    <div className={cn(notificationVariants({ variant }))}>
      <div className="flex gap-2">
        {Icon && <Icon className="w-5" />}
        <div className="flex-1">
          <h3 className="font-semibold">{title}</h3>
          <h6 className="text-sm font-normal text-opacity-20">{description}</h6>
        </div>
      </div>
    </div>
  ));
}
