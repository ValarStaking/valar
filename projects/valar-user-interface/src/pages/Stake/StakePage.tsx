import { Container } from "@/components/Container/Container";
import { DEFAULT_MAX_STAKE, PAYMENT_ASA, SUGGESTED_DURATION } from "@/constants/platform";
import { TimeParams } from "@/constants/units";
import { StakeReqs } from "@/lib/types";
import { durationToRounds } from "@/utils/convert";
import { useState } from "react";

import StakeListCard from "./_components/StakeList/StakeListCard";
import StakePotentialCard from "./_components/StakePotential/StakePotentialCard";
import StakeRequirementCard from "./_components/StakeRequirement/StakeRequirementCard";
import StakeSidebarCard from "./_components/StakeSidebar/StakeSidebarCard";
import MinAlgoRequiredStakePopup from "@/components/Popup/MinAlgoRequiredStakePopup";

const StakePage: React.FC = () => {
  const [stakeReqs, setStakeReqs] = useState<StakeReqs>({
    duration: durationToRounds(SUGGESTED_DURATION, TimeParams.stake.unit),
    maxStake: DEFAULT_MAX_STAKE,
    currency: PAYMENT_ASA,
  });

  return (
    <Container>
      <div className="grid gap-2 lg:grid-cols-12">
        <div className="col-span-9 flex flex-col gap-2">
          <div className="flex flex-wrap gap-2 lg:flex-nowrap">
            <StakeRequirementCard setStakeReqs={setStakeReqs} className="w-full" />
            <StakePotentialCard stakeReqs={stakeReqs} className="lg:min-w-[260px] lg:flex-1" />
          </div>
          <StakeListCard stakeReqs={stakeReqs} />
        </div>
        <div className="col-span-3 hidden lg:block">
          <StakeSidebarCard />
        </div>
      </div>
      <MinAlgoRequiredStakePopup/>
    </Container>
  );
};

export default StakePage;
