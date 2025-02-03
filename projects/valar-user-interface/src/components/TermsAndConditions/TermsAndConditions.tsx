import { emailLink } from "@/constants/socials";
import { TERMS_AND_CONDITIONS } from "@/constants/terms-and-conditions";
import { cn } from "@/lib/shadcn-utils";

import LinkExt from "../ui/link-ext";

const NULL_TC = "0000000000000000000000000000000000000000000000000000000000000000";

const TermsAndConditions: React.FC<{
  terms: string;
  className?: string;
}> = ({ terms, className }) => {
  if (terms === NULL_TC) {
    return <>Terms & Conditions are not available because the ad has not yet been configured.</>;
  }

  let href = TERMS_AND_CONDITIONS.get(terms);
  let text = "Terms & Conditions";

  if (!href) {
    href = emailLink;
    text = "Unknown Terms & Conditions - notify developers";
  }

  return <LinkExt href={href} children={text} className={cn("text-secondary", className)} />;
};
export default TermsAndConditions;
