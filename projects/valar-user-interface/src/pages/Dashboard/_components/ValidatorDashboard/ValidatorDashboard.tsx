import { Container } from "@/components/Container/Container";

import CreateAdCard from "./_components/CreateAd/CreateAdCard";
import LearnMoreCard from "./_components/Learn/LearnMoreCard";
import ValAdListCard from "./_components/ValAdList/ValAdListCard";
import ValDelCoListCard from "./_components/ValDelCoList/ValDelCoListCard";
import ShareAdCard from "./_components/ShareAd/ShareAdCard";

const ValidatorDashboard = () => {

  return (
    <Container>
      <div className="grid grid-cols-1 gap-2 lg:grid-cols-11">
        <div className="flex flex-col gap-2 lg:col-span-3 lg:gap-4">
          <CreateAdCard />
          <LearnMoreCard />
          <ShareAdCard />
        </div>
        <div className="space-y-4 lg:col-span-8">
          <ValAdListCard />
          <ValDelCoListCard />
        </div>
      </div>
    </Container>
  );
};

export default ValidatorDashboard;
