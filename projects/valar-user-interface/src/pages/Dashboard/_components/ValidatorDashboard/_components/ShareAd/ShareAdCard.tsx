import { Button } from "@/components/ui/button";
import { ROLE_VAL_STR } from "@/constants/smart-contracts";
import useUserStore from "@/store/userStore";
import { bytesToStr } from "@/utils/convert";
import { Check, Link } from "lucide-react";
import { useState } from "react";

const ShareAdCard = () => {
  const { user } = useUserStore();
  const [copied, setCopied] = useState(false);

  if (!user || !user.userInfo || bytesToStr(user.userInfo.role) !== ROLE_VAL_STR) return;

  const handleCopy = () => {
    const textToCopy = window.location.origin + "/stake" + "?node_runner=" + user.address;
    navigator.clipboard
      .writeText(textToCopy)
      .then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 1200); // Reset message after 1.2 seconds
      })
      .catch((err) => {
        console.error("Failed to copy node runner link: ", err);
      });
  };

  return (
    <div className="flex items-center justify-between gap-2 rounded-lg bg-background-light p-3">
      <h3 className="text-sm">Share your ads.</h3>
      <div className="relative flex flex-col items-center">
        <Button variant={"v_outline"} className="border-0 px-2" onClick={handleCopy}>
          <Link /> Copy Link
        </Button>
        {copied && (
          <div className="absolute top-full mt-2 flex items-center gap-2 rounded-md bg-border px-1.5 py-1">
            <Check size={16} />
            <span className="text-sm font-normal text-text">Link Copied</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default ShareAdCard;
