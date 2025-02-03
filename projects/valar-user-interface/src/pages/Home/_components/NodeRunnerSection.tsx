import { Button } from "@/components/ui/button";
import {
  ChartColumnIncreasing,
  ClipboardPen,
  Handshake,
  Settings,
  Sun,
  UserCheck,
} from "lucide-react";

import FeaturesCard from "./FeaturesCard";
import { useNavigate } from "react-router-dom";
import { ROLE_VAL_STR } from "@/constants/smart-contracts";

const NodeRunnerSection = () => {
  const stakingFeatures: { icon: JSX.Element; head: string; desc: string }[] = [
    {
      icon: <UserCheck className="h-8 w-8 text-tertiary" />,
      head: "Reduce Risks",
      desc: "You never take custody of any users' assets. Staking rewards go directly to your users.",
    },
    {
      icon: (
        <ChartColumnIncreasing className="h-8 w-8 text-tertiary" />
      ),
      head: "Predictable",
      desc: "Charge in ALGO or stablecoins. Customize your price per stake and duration.",
    },
    {
      icon: <Handshake className="h-8 w-8 text-tertiary" />,
      head: "Support the Network",
      desc: "Let ALGO holders stake directly via your node, supporting the network.",
    },
    {
      icon: <Sun className="h-8 w-8 text-tertiary" />,
      head: "Resource Efficiency",
      desc: "Let others fully utilize your nodes by staking on them while paying for the service.",
    },
    {
      icon: <Settings className="h-8 w-8 text-tertiary" />,
      head: "Automatic Management",
      desc: "Valar daemon enables automatic servicing of new staking requests.",
    },
    {
      icon: <ClipboardPen className="h-8 w-8 text-tertiary" />,
      head: "Exclusive Access",
      desc: "Define who can use your node: NFT holders, community token holders, KYC users, etc. ",
    },
  ];

  const navigate = useNavigate()

  return (
    <div className="grid grid-cols-1 gap-y-6 lg:grid-cols-3 lg:gap-12">
      <div className="col-span-1">
        <div className="flex flex-col gap-3">
          <p className="text-xs lg:text-sm  font-semibol text-tertiary">
            NODE RUNNER
          </p>
          <h1 className="text-xl font-semibold lg:text-3xl">
            Do you run an Algorand node or want to?
          </h1>
          <p className="text-sm leading-5 lg:text-base lg:leading-7">
            Maximize its utilization and your revenue by letting others stake
            with you, contributing to network's decentralization.
          </p>
        </div>
        <Button className="mt-6 w-full bg-tertiary-dark" variant={'v_tertiary'} onClick={() => navigate("/dashboard",  { state: { role: ROLE_VAL_STR }})}>
          Run a Node
        </Button>
      </div>
      <div className="col-span-2">
        <div className="grid grid-cols-2 gap-x-6 gap-y-12 lg:grid-cols-3">
          {stakingFeatures.map((f, index) => (
            <FeaturesCard key={index} {...f} />
          ))}
        </div>
      </div>
    </div>
  );
};

export default NodeRunnerSection;
