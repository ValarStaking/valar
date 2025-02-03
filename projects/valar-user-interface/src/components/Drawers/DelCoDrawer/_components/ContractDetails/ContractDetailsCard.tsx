import { NFDApi } from "@/api/nfd";
import Avatar from "@/components/Avatar/Avatar";
import { InfoItem, InfoLabel, InfoSection, InfoValue } from "@/components/Info/InfoUtilsCompo";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import LinkExt from "@/components/ui/link-ext";
import { Separator } from "@/components/ui/separator";
import { useDelCoDrawer } from "@/contexts/DelCoDrawerContext";
import {
  ValTermsPricingInterface,
  ValTermsStakeLimitsInterface,
  ValTermsTimingInterface,
  ValTermsWarningsInterface,
} from "@/interfaces/contracts/ValidatorAd";
import { Nfd } from "@/interfaces/nfd";
import { cn } from "@/lib/shadcn-utils";
import { getExplorerConfigFromViteEnvironment } from "@/utils/config/getExplorerConfig";
import { calculateFeeRound } from "@/utils/contract/helpers";
import { ellipseAddress } from "@/utils/convert";
import { getNfdProfileUrl } from "@/utils/nfd";
import { ChevronDown, ChevronUp } from "lucide-react";
import { useEffect, useState } from "react";

import EligibilitySection, { EligibilitySectionType } from "./Sections/EligibilitySection";
import PricingSection, { PricingSectionTypeContract } from "./Sections/PricingSection";
import StakeLimitsSection from "./Sections/StakeLimitSection";
import TimingSection, { TimingSectionTypeContract } from "./Sections/TimingSection";
import WarningsSection from "./Sections/WarningsSection";

export type ContractDetailsDataType = {
  pricing: PricingSectionTypeContract | ValTermsPricingInterface;
  stakeLimits: undefined | ValTermsStakeLimitsInterface;
  warnings: ValTermsWarningsInterface;
  timings: TimingSectionTypeContract | ValTermsTimingInterface;
  eligibility: EligibilitySectionType;
};

const ContractDetailsCard: React.FC<{ className?: string }> = ({ className }) => {
  const { accountUrl, appUrl } = getExplorerConfigFromViteEnvironment();
  const [openTerms, setOpenTerms] = useState<boolean>(true);
  const { gsValAd, gsDelCo, stakeReqs } = useDelCoDrawer();
  const [nfd, setNfd] = useState<Nfd | null>(null);

  let contractDetails: ContractDetailsDataType | undefined = undefined;

  if (gsDelCo) {
    // If Delegator Contract info is defined, it will be displayed.
    contractDetails = {
      pricing: {
        currency: gsDelCo.delegationTermsGeneral.feeAssetId,
        setupFee: gsDelCo.delegationTermsGeneral.feeSetup,
        operationalFee: gsDelCo.delegationTermsGeneral.feeRound,
      },
      stakeLimits: undefined,
      warnings: {
        cntWarningMax: gsDelCo.delegationTermsBalance.cntBreachDelMax,
        roundsWarning: gsDelCo.delegationTermsBalance.roundsBreach,
      },
      timings: {
        roundsSetup: gsDelCo.delegationTermsGeneral.roundsSetup,
        roundsConfirm: gsDelCo.delegationTermsGeneral.roundsConfirm,
      },
      eligibility: {
        asa1Id: gsDelCo.delegationTermsBalance.gatingAsaList[0][0],
        asa1Amount: gsDelCo.delegationTermsBalance.gatingAsaList[0][1],
        asa2Id: gsDelCo.delegationTermsBalance.gatingAsaList[1][0],
        asa2Amount: gsDelCo.delegationTermsBalance.gatingAsaList[1][1],
      },
    };
  } else {
    // If no Delegator Contract info is defined, data based on Validator Ad will be displayed.
    if (stakeReqs) {
      // If staking requirements are known, tailored data
      contractDetails = {
        pricing: {
          currency: gsValAd!.termsPrice.feeAssetId,
          setupFee: gsValAd!.termsPrice.feeSetup,
          operationalFee: calculateFeeRound(
            stakeReqs.maxStake,
            gsValAd!.termsPrice.feeRoundMin,
            gsValAd!.termsPrice.feeRoundVar,
          ),
        },
        stakeLimits: undefined,
        warnings: gsValAd!.termsWarn,
        timings: {
          roundsSetup: gsValAd!.termsTime.roundsSetup,
          roundsConfirm: gsValAd!.termsTime.roundsConfirm,
        },
        eligibility: {
          asa1Id: gsValAd!.termsReqs.gatingAsaList[0][0],
          asa1Amount: gsValAd!.termsReqs.gatingAsaList[0][1],
          asa2Id: gsValAd!.termsReqs.gatingAsaList[1][0],
          asa2Amount: gsValAd!.termsReqs.gatingAsaList[1][1],
        },
      };
    } else {
      contractDetails = {
        pricing: gsValAd!.termsPrice,
        stakeLimits: gsValAd!.termsStake,
        warnings: gsValAd!.termsWarn,
        timings: gsValAd!.termsTime,
        eligibility: {
          asa1Id: gsValAd!.termsReqs.gatingAsaList[0][0],
          asa1Amount: gsValAd!.termsReqs.gatingAsaList[0][1],
          asa2Id: gsValAd!.termsReqs.gatingAsaList[1][0],
          asa2Amount: gsValAd!.termsReqs.gatingAsaList[1][1],
        },
      };
    }
  }

  /**
   * =========================================
   *          UseEffect and Functions
   * =========================================
   */

  useEffect(() => {
    const fetch = async () => {
      if (gsValAd) {
        try {
          const address = gsValAd.valOwner;
          const nfd = await NFDApi.fetchNfdReverseLookup(address, { view: "thumbnail" });
          setNfd(nfd);
        } catch (e) {
          return;
        }
      }
    };
    fetch();
  }, [gsValAd]);

  return (
    <div className={cn("", className)}>
      <h1 className="my-1 text-base font-bold">Node Runner Details</h1>
      <Separator />
      <div className="flex justify-between py-3">
        <div className="">
          <InfoSection>
            <InfoItem>
              <InfoLabel>Node runner:</InfoLabel>
              <InfoValue>
                <LinkExt href={accountUrl + gsValAd!.valOwner}>{ellipseAddress(gsValAd!.valOwner)}</LinkExt>
              </InfoValue>
            </InfoItem>
            {nfd && (
              <InfoItem>
                <InfoLabel>More info:</InfoLabel>
                <InfoValue>
                  <LinkExt href={getNfdProfileUrl(nfd.name)} children={nfd.name} className={"text-sm text-secondary"} />
                </InfoValue>
              </InfoItem>
            )}
            <InfoItem>
              <InfoLabel>Ad ID:</InfoLabel>
              <InfoValue>
                <LinkExt href={appUrl + gsValAd!.appId.toString()}>{gsValAd!.appId.toString()}</LinkExt>
              </InfoValue>
            </InfoItem>
            <InfoItem>
              <InfoLabel>Occupation:</InfoLabel>
              <InfoValue>{gsValAd!.cntDel + "/" + gsValAd!.cntDelMax}</InfoValue>
            </InfoItem>
          </InfoSection>
        </div>
        <div className="flex-shrink-0">
          <Avatar address={gsValAd!.valOwner} nfd={nfd} className="h-10 w-10" />
        </div>
      </div>
      <Collapsible open={openTerms} onOpenChange={setOpenTerms}>
        <div className="flex justify-between">
          <h4 className="text-sm font-bold">Node runner terms</h4>
          <CollapsibleTrigger>
            {openTerms ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            <span className="sr-only">Toggle</span>
          </CollapsibleTrigger>
        </div>
        <CollapsibleContent className="mt-3 grid grid-cols-1 gap-4 lg:grid-cols-2">
          <div className="flex flex-col justify-between gap-6">
            <PricingSection data={contractDetails.pricing} />
            <StakeLimitsSection data={contractDetails.stakeLimits} />
            <WarningsSection data={contractDetails.warnings} />
          </div>
          <div className="flex flex-col gap-6">
            <TimingSection data={contractDetails.timings} />
            <EligibilitySection data={contractDetails.eligibility} />
          </div>
        </CollapsibleContent>
      </Collapsible>
    </div>
  );
};

export default ContractDetailsCard;
