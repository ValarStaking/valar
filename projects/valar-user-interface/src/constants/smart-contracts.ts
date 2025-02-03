/**
 * Constants related to smart contracts and AVM.
 */
import { AlgorandRewards } from "@/lib/types";
import { getPlatformConfig } from "@/utils/config/getPlatformConfig";
import { strToBytes } from "@/utils/convert"

// Get platform configuration
const config = getPlatformConfig();

// About minimum balance requirement (MBR) - based on algod parameters (v4.0.0)
export const MBR_ACCOUNT = 100_000;
export const MBR_ASA = 100_000;
export const MBR_USER_BOX = 2_500 + 400 * ((32) + (4 + 8 + 2*32 + 8*110 + 8));
export const MBR_NOTICEBOARD_VALIDATOR_AD_CONTRACT_INCREASE = 921_000;
export const MBR_VALIDATOR_AD_ASA_BOX = 2_500 + 400 * (4 + 8 + 2 * 8);
export const MBR_DELEGATOR_CONTRACT = MBR_ACCOUNT + MBR_ASA;
export const MBR_VALIDATOR_AD_DELEGATOR_CONTRACT_INCREASE = MBR_DELEGATOR_CONTRACT + 992_000;

// About boxes
export const BOX_SIZE_PER_REF = 1024;  // [bytes]
export const BOX_VALIDATOR_AD_TEMPLATE_KEY = strToBytes('v');
export const BOX_DELEGATOR_CONTRACT_TEMPLATE_KEY = strToBytes('d');
export const BOX_ASSET_KEY_PREFIX = strToBytes('asset_');
export const BOX_ASA_KEY_PREFIX = strToBytes('asa_');
export const BOX_PARTNERS_PREFIX = strToBytes('partner_');

// About roles on Noticeboard
export const ROLE_VAL_STR = 'val_';
export const ROLE_DEL_STR = 'del_';
export const ROLE_VAL = strToBytes(ROLE_VAL_STR);
export const ROLE_DEL = strToBytes(ROLE_DEL_STR);

// ID of ALGO as asset
export const ASA_ID_ALGO = 0n;

// Fee for consensus performance tracking mechanism opt in, a.k.a. rewards eligibility
export const FEE_OPT_IN_PERFORMANCE_TRACKING = 2_000_000; // [microAlgo]

// Algorand zero address
export const ZERO_ADDRESS: string = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ";

// Algorand staking rewards info
export const ALGORAND_REWARDS: AlgorandRewards = {
  startRound: BigInt(config.algoRewards.startRound),   // first block
  startReward: config.algoRewards.startReward,         // starting rewards rate [microALGO]
  decayRounds: config.algoRewards.decayRounds,         // decay window [number of rounds]
  decayRate: config.algoRewards.decayRate,             // decay rate [%]
}

// Algorand minimum staking amount for rewards
export const MIN_ALGO_STAKE_FOR_REWARDS = 30_000_000_000;  // [microALGO]

// Maximum transaction validity window
export const MAX_TXN_VALIDITY: number = 1_000;  // [rounds]
