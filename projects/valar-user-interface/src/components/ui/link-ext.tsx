import { cn } from "@/lib/shadcn-utils";
import { ReactNode } from "react";

const LinkExt: React.FC<{
  href: string;
  children: ReactNode;
  className?: string;
}> = ({ href, children, className }) => {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className={cn("text-secondary", className)}
    >
      {children}
    </a>
  );
};
export default LinkExt;
