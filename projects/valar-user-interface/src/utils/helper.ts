import { ALGORAND_REWARDS } from "@/constants/smart-contracts";
import { BLOCKS_PER_YEAR } from "@/constants/timing";

export function estimateRateForRounds(currentRound: bigint, stakeOnline: bigint, rounds: bigint): number {
  const getRewardAtRound = (round: bigint) => {
    return (
      ALGORAND_REWARDS.startReward *
      (1 -
        (Math.floor(Number(round - ALGORAND_REWARDS.startRound) / ALGORAND_REWARDS.decayRounds) *
          ALGORAND_REWARDS.decayRate) /
          100)
    );
  };

  const currentReward = getRewardAtRound(currentRound);
  const endReward = getRewardAtRound(currentRound + rounds);
  const averageReward = (currentReward + endReward) / 2;

  const returnRate = ((Number(rounds) * averageReward) / Number(stakeOnline)) * 100;

  return returnRate;
}

export function estimateAPY(currentRound: bigint, stakeOnline: bigint): number {
  return estimateRateForRounds(currentRound, stakeOnline, BigInt(Math.floor(BLOCKS_PER_YEAR)));
}
