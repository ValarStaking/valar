import { DelegatorQuery } from "@/api/queries/delegator-contracts";
import { ValidatorQuery } from "@/api/queries/validator-ads";
import { Container } from "@/components/Container/Container";
import { FETCH_INTERVAL } from "@/constants/timing";
import { useAppGlobalState } from "@/contexts/AppGlobalStateContext";
import { useDelCoDrawer } from "@/contexts/DelCoDrawerContext";
import useUserStore from "@/store/userStore";
import { Stakable, StakingUtils } from "@/utils/staking-utils";
import { useWallet } from "@txnlab/use-wallet-react";
import { useEffect, useState } from "react";

import ContractDetailsCard from "./_components/ContractDetails/ContractDetailsCard";
import CannotStakeCard from "./_components/ContractSummary/CannotStakeCard";
import ConnectWalletCard from "./_components/ContractSummary/ConnectWalletCard";
import ContractActiveCard from "./_components/ContractSummary/ContractActiveCard";
import ContractCreateCard from "./_components/ContractSummary/ContractCreateCard";

const DelCoDrawerContents = () => {
  const { algorandClient } = useAppGlobalState();
  const { activeAddress } = useWallet();
  const { user } = useUserStore();
  const { openDrawer, delAppId, valAppId, gsDelCo, setGsDelCo, gsValAd, setGsValAd, refetch, setRefetch, stakeReqs } =
    useDelCoDrawer();

  const [loading, setLoading] = useState(true);
  const [stakable, setStakable] = useState<Stakable | undefined>(undefined);

  useEffect(() => {
    const fetch = async () => {
      if (gsValAd && stakeReqs) {
        const res = await StakingUtils.canStake(gsValAd, user, stakeReqs);
        setStakable(res);
      }
    };
    fetch();
  }, [gsValAd, user, stakeReqs]);

  // -----------------------------------
  // Periodically fetch data or when delAppId or open status change
  useEffect(() => {
    // Fetch data
    const fetch = async () => {
      console.log("Trying to fetch data...");
      if (openDrawer && refetch) {
        console.log("Fetching data...");

        if (delAppId) {
          // Fetch delegator contract and its validator ad
          try {
            const resDelCo = await DelegatorQuery.fetchDelegatorContracts(algorandClient.client.algod, [delAppId]);
            const gsDelCo = resDelCo!.get(delAppId);

            console.log("Delegator Contract ::", delAppId, gsDelCo);
            setGsDelCo(gsDelCo);

            const valAppId = gsDelCo!.validatorAdAppId;
            const resValAd = await ValidatorQuery.fetchValidatorAds(algorandClient.client.algod, [valAppId]);
            const gsValAd = resValAd!.get(valAppId);

            console.log("Validator Ad ::", valAppId, gsValAd);
            setGsValAd(gsValAd);
          } catch {
            setGsDelCo(undefined);
          }
        } else if (valAppId) {
          // Fetch validator ad
          try {
            const resValAd = await ValidatorQuery.fetchValidatorAds(algorandClient.client.algod, [valAppId]);
            const gsValAd = resValAd!.get(valAppId);
            console.log("Validator Ad ::", valAppId, gsValAd);
            setGsValAd(gsValAd);
          } catch {
            setGsValAd(undefined);
          }
        }
        setRefetch(false);
      }
      setLoading(false);
    };
    fetch(); // Fetch immediately when component mounts or parameter changes

    const interval = setInterval(() => {
      setRefetch(true);
      fetch();
    }, FETCH_INTERVAL); // Fetch at a regular interval

    return () => clearInterval(interval); // Clear interval on unmount or parameter change
  }, [delAppId, refetch, openDrawer]);

  /**
   * ==============================
   *         Component Render
   * ==============================
   */

  if (loading) {
    return (
      <Container>
        <p>Loading...</p>
      </Container>
    );
  }

  if (!gsValAd) {
    return (
      <Container>
        <p>Unable to Fetch Validator Ad Details.</p>
      </Container>
    );
  }

  if (delAppId && !gsDelCo) {
    return (
      <Container>
        <p>Unable to Fetch Delegator Contract details.</p>
      </Container>
    );
  }

  return (
    <Container>
      <div className="grid gap-3 lg:grid-cols-5">
        <div className="h-min rounded-lg border border-border bg-background-light p-3 lg:col-span-3">
          <ContractDetailsCard />
        </div>
        <div className="lg:col-span-2">
          {!activeAddress ? (
            <ConnectWalletCard />
          ) : delAppId && gsDelCo ? (
            <ContractActiveCard />
          ) : stakable?.possible ? (
            <ContractCreateCard />
          ) : (
            <CannotStakeCard stakable={stakable} />
          )}
        </div>
      </div>
    </Container>
  );
};

export default DelCoDrawerContents;
