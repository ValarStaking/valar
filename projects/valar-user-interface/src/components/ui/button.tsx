import { cn } from "@/lib/shadcn-utils";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";

import LoadingSpinner from "../Loader/loading-spinner";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-neutral-950 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0 dark:focus-visible:ring-neutral-300",
  {
    variants: {
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-10 rounded-md px-8",
        icon: "h-9 w-9",
      },
      variant: {
        default:
          "bg-neutral-900 text-neutral-50 shadow hover:bg-neutral-900/90 dark:bg-neutral-50 dark:text-neutral-900 dark:hover:bg-neutral-50/90",
        destructive:
          "bg-red-500 text-neutral-50 shadow-sm hover:bg-red-500/90 dark:bg-red-900 dark:text-neutral-50 dark:hover:bg-red-900/90",
        outline:
          "border border-neutral-200 bg-white shadow-sm hover:bg-neutral-100 hover:text-neutral-900 dark:border-neutral-800 dark:bg-neutral-950 dark:hover:bg-neutral-800 dark:hover:text-neutral-50",
        secondary:
          "bg-neutral-100 text-neutral-900 shadow-sm hover:bg-neutral-100/80 dark:bg-neutral-800 dark:text-neutral-50 dark:hover:bg-neutral-800/80",
        ghost: "hover:bg-neutral-100 hover:text-neutral-900 dark:hover:bg-neutral-800 dark:hover:text-neutral-50",
        link: "text-neutral-900 underline-offset-4 hover:underline dark:text-neutral-50",
        wallet:
          "text-white bg-secondary-dark bg-gradient-to-r from-gradient-light to-gradient-dark hover:bg-gradient-to-l",
        v_outline:
          "bg-transparent text-base font-semibold leading-7 text-white border border-neutral-200 shadow-sm hover:bg-white hover:bg-opacity-10",
        v_primary: "bg-primary text-text text-base font-semibold leading-7 hover:bg-primary-light",
        v_secondary: "bg-secondary text-black text-base font-semibold leading-7 hover:bg-secondary-dark",
        v_tertiary: "bg-tertiary text-black text-base font-semibold leading-7 hover:bg-tertiary-light",
        icon: "bg-transparent hover:bg-white hover:bg-opacity-10 p-0",
        v_ghost: "hover:bg-white hover:bg-opacity-10",
        v_link: "text-secondary-dark hover:text-secondary-light px-0",
      },
    },
    defaultVariants: {
      size: "default",
      variant: "default",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return <Comp className={cn(buttonVariants({ size, variant, className }))} ref={ref} {...props} />;
  },
);
Button.displayName = "Button";

const IconButton: React.FC<React.ComponentProps<"div">> = ({ children, ...props }) => {
  return (
    <div {...props} className="cursor-pointer">
      {children}
    </div>
  );
};

const LoadingButton: React.FC<ButtonProps & { loading: boolean }> = ({
  loading,
  className,
  variant,
  size,
  asChild = false,
  ...props
}) => {
  return (
    <>
      <Button className={cn("", className)} size={size} variant={variant} asChild={asChild} {...props} disabled={props.disabled || loading} >
        {loading && <LoadingSpinner visible={loading} />} {props.children}
      </Button>
    </>
  );
};

export { Button, buttonVariants, IconButton, LoadingButton };
