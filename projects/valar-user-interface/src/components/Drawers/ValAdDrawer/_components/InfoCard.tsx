import {
  InfoItem,
  InfoLabel,
  InfoValue,
} from "@/components/Info/InfoUtilsCompo";
import AdStatus from "@/components/Status/AdStatus";
import TermsAndConditions from "@/components/TermsAndConditions/TermsAndConditions";
import LinkExt from "@/components/ui/link-ext";
import { ValidatorAdGlobalState } from "@/interfaces/contracts/ValidatorAd";
import { ValAdStatus } from "@/lib/types";
import { getExplorerConfigFromViteEnvironment } from "@/utils/config/getExplorerConfig";
import { bytesToHex, decodeValAdStateToString, ellipseAddress } from "@/utils/convert";
import { useEffect, useState } from "react";

type ValAdInfo = {
  appId: string;
  nodeRunner: string;
  status: ValAdStatus;
  tc: string;
};

function getValAdInfo(gsValAd: ValidatorAdGlobalState): ValAdInfo {
  const status = decodeValAdStateToString(gsValAd.state);
  const nodeRunner = gsValAd.valOwner;

  return {
    appId: gsValAd.appId.toString(),
    nodeRunner: nodeRunner,
    status: status,
    tc: bytesToHex(gsValAd.tcSha256),
  } as ValAdInfo;
}

const InfoCard = ({ gsValAd }: { gsValAd: ValidatorAdGlobalState }) => {
  const [data, setData] = useState<ValAdInfo | undefined>(undefined);
  const { appUrl, accountUrl } = getExplorerConfigFromViteEnvironment();

  useEffect(() => {
    const data = getValAdInfo(gsValAd);
    setData(data);
  }, [gsValAd]);

  if (!data) return;

  return (
    <div className="space-y-1 rounded-lg border border-border bg-background-light p-3">
      <h1 className="text-sm font-semibold">Main Information</h1>
      <InfoItem className="flex gap-1 text-sm">
        <InfoLabel>Ad ID:</InfoLabel>
        <InfoValue className="text-secondary">
          <LinkExt href={appUrl + data.appId}>{data.appId}</LinkExt>
        </InfoValue>
      </InfoItem>
      <InfoItem className="flex gap-1 text-sm">
        <InfoLabel>Node runner:</InfoLabel>
        <InfoValue className="text-secondary">
          <LinkExt href={accountUrl + data.nodeRunner}>
            {ellipseAddress(data.nodeRunner)}
          </LinkExt>
        </InfoValue>
      </InfoItem>
      <InfoItem className="flex gap-1 text-sm">
        <InfoLabel>Status:</InfoLabel>
        <InfoValue>
          <AdStatus status={data.status} />
        </InfoValue>
      </InfoItem>
      <div>
        <div className="mt-6 text-sm text-text-tertiary">
          Accepted <TermsAndConditions terms={data.tc} />
        </div>
      </div>
    </div>
  );
};

export default InfoCard;
