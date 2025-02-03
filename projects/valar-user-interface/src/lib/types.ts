export type DelCoStatus = "LIVE" | "AWAITING_SETUP" | "CONFIRM_SETUP" | "ENDED"
export type ValAdStatus = "CREATED" | "NOT_LIVE" | "NOT_READY" | "READY"

export type Earning = {
  id: bigint;
  total: bigint;
  unclaimed: bigint;
}

export type AlgorandRewards = {
  startRound: bigint,    // first block
  startReward: number,   // starting rewards rate [microALGO]
  decayRounds: number,   // decay window [number of rounds]
  decayRate: number,     // decay rate [%]
}

export type StakingData = {
  nodesTotal: number,
  accountsOnlineAll: number,
  accountsOnline30k: number,
  stakeOnline: bigint,
  apy: number,
}

export type AssetAmountUnit = "" | "per month" | "per month & per 100k ALGO" | "raw";
export type AssetDisplay = {
  unit: AssetAmountUnit,
  decimals: number,
};

export type TimeUnit = "min" | "h" | "day" | "days" | "month" | "rounds" | "ms";
export type TimeDisplay = {
  unit: TimeUnit,
  decimals: number,
};

export type AdTermsTime = {
  validUntil: string;
  minDuration: number;
  maxDuration: number;
  setupTime: number;
  confirmationTime: number;
}

export type AdTermsFees = {
  paymentCurrency: bigint;
  setupFee: number;
  minOperationalFee: number;
  varOperationalFee: number;
}

export type AdTermsStake = {
  maxStake: number;
  gratisStake: number;
}

export type AdTermsReqs = {
  idASA1: number;
  amountASA1: number;
  idASA2: number;
  amountASA2: number;
}

export type AdTermsWarn = {
  maxWarnings: number;
  warnTime: number;
}

export type AdConfigValues = {
  managerAddress: string;
  maxUser: number;
  acceptingNewUser: boolean;
}

export type AdFormValues =
  AdConfigValues &
  AdTermsTime &
  AdTermsFees &
  AdTermsStake &
  AdTermsReqs &
  AdTermsWarn

export type AdFormValuesDisplay =
  AdConfigValues &
  AdTermsTime &
  {
      paymentCurrency: string;
      setupFee: number;
      minOperationalFee: number;
      varOperationalFee: number;
  } &
  AdTermsStake &
  AdTermsReqs &
  AdTermsWarn

export type AdTermsFeesMin = {
  setupFee: number;
  minOperationalFee: number;
  varOperationalFee: number;
}

export type CurrencyDetails = {
  allowed: boolean;
  ticker: string;
  decimals: number;
  displayDecimals: number;
  adTermsFees: AdTermsFees;
  adTermsFeesMin: AdTermsFeesMin;
}

export type StakeReqs = {
  duration: bigint;
  maxStake: bigint;
  currency: bigint;
}

export type KeyRegParams = {
  voteKey: Uint8Array;
  selectionKey: Uint8Array;
  voteFirst: bigint;
  voteLast: bigint;
  voteKeyDilution: bigint;
  stateProofKey: Uint8Array;
}

