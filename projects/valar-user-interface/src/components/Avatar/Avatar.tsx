import { cn } from "@/lib/shadcn-utils";
import IdenticonAvatar from "../Identicon/Identicon";
import { Nfd } from "@/interfaces/nfd";
import { getNfdAvatarUrl } from "@/utils/nfd";


const Avatar = ({
  address,
  nfd,
  className,
}: {
  address: string;
  nfd: Nfd | null;
  className?: string;
}) => {


  if (nfd) {
    const src = getNfdAvatarUrl(nfd);
    if (src) {
      return <img src={src} alt="NFD Avatar" className={cn("rounded-full w-7 h-7", className)} />
    }
  }

  return <IdenticonAvatar value={address} className={cn("", className)} />
};

export default Avatar;
