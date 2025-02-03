export class ToolTips {
  static StakeShowAll = `Show ads of all node runners, even of those you can't stake with because
  they are fully occupied, not active, or you don't meet their requirements.`
  static AlgorandRewards = `Estimated yearly Algorand staking rewards rate based on estimated Algorand Foundation rewards for the period and current online stake.`;

  static PossibleRewards = `Estimated amount of ALGO the network could reward you with during the
  selected staking duration based on estimated Algorand staking rewards rate and your current stake.`;

  static MaxStake = `Maximum amount of ALGO you promise to have in your account during the
  selected staking duration. If you get more ALGO than the agreed max stake,
  your contract can get terminated.`;

  static Rating = `Rating of node runner performance based on the number of produced blocks
  vs. expected number of produced blocks.`;

  static SetupFee = `Fee charged by the node runner to prepare the node for a new user.`;

  static OperationalFee = `Fee charged by the node runner for operation of the node.
  It is proportionate to the agreed duration of staking and the maximum stake.`;

  static MinOperationalFee = `Minimum fee charged by the node runner per time unit of operation.`;

  static VarOperationalFee = `Variable fee charged by the node runner per time unit of operation
  based on user's reserved maximum stake amount.`;

  static GratisStake = `Relative increase to the user's requested maximum stake, for which the user is not charged for.
  This acts as a free buffer given to users to reduce the chance of them unintentionally breaching the agreed contract
  terms. Sum of requested maximum stake and buffer is capped at the defined maximum allowed stake at the node.`;

  static MaxWarnings = `Maximum number of warnings given for breaching the agreed stake or gating token
  balance before the contract is terminated.`;

  static WarningTime = `Maximum amount of time to correct a mistake in stake or gating token balance before
  another warning is given for the same mistake.`;

  static SetupTime = `Maximum amount of time a new user must wait for the node runner to prepare the node for them.`;

  static SetupTimeAdCreation = `Maximum amount of time a new user must wait for you to prepare the node for them.`;

  static ConfirmationTime = `Maximum amount of time a new user has in order to confirm the setup that the node runner prepared for them.`;

  static ConfirmationTimeAdCreation = `Maximum amount of time a new user has in order to confirm the setup that you prepare for them.`;

  static EligibilityASA = `Node runner allows access to their service only if the user's account has at least the stated amounts of the stated
  ASA1 and ASA2 at all times, otherwise the contract can get terminated.
  Amounts are displayed in ASA's smallest unit.`;

  static EligibilityASASingle = `Node runner allows access to their service only if the user's account has at least the stated amounts of the stated
  ASA at all times, otherwise the contract can get terminated.
  Amounts are displayed in ASA's smallest unit.`;

  static EligibilityASAAdCreation = `Allow access to your service only if the user's account has at least the defined amounts
  of the ASA1 and ASA2 at all times, otherwise the contract can get terminated.
  Leave empty if there should be no restrictions.
  Amounts are entered in ASA's smallest unit.`;

  static NodeRunnerFee = `Total fee paid to the node runner for the service, consisting of setup and operational fees.`;

  static ConvenienceFee = `Convenience fee charged by the platform's partner to simplify user staking.`;

  static AlgorandDepositDel = `Deposit charged by the Algorand network to store your service contract.
  The deposit gets returned when you stop using the platform.`;

  static AlgorandDepositVal = `Deposit charged by the Algorand network to store your node runner ad.
  The deposit is partially charged on ad creation and when configuring the ad for the first time.
  The deposit gets returned when you stop using the platform.`;

  static AlgorandDepositUserAndDel = `Deposit charged by the Algorand network to store your address information and your service contract.
  The deposit gets returned when you stop using the platform.`;

  static AlgorandDepositUserAndVal = `Deposit charged by the Algorand network to store your address information and your node runner ad.
  The deposit is partially charged on ad creation and when configuring the ad for the first time.
  The deposit gets returned when you stop using the platform.`;

  static MonitorPerformance = `Check or register for off-chain monitoring of your account to be notified
  of any under-performance sooner than identified by the network.`;

  static RewardsEarned = `Rewards earned due to the staking service contract.`;

  static ManagerAddress = `Address of the account that is submitting key registration transaction parameters
  generated for your users. If you are using Valar daemon, this is the address of the daemon account.`;

  static MaxNoOfUsers = `Maximum number of users that can simultaneously stake via this ad.`;

  static AcceptingNewUsers = `Set to enable accepting new users to stake via your ad.`;

  static AlgorandRegistrationFee = `Algorand network charges a fee to opt an account into the network's monitoring mechanism.
  Without it, you cannot stake via Valar.
  Paying this fee is a condition by the network to be eligible for staking rewards.
  It is paid when you confirm the setup that the node runner prepares for you.`;
}
