/**
 * Constants related to the Platform configuration.
 */

import { AdConfigValues, AdFormValues, AdTermsReqs, AdTermsStake, AdTermsTime, AdTermsWarn, CurrencyDetails } from '@/lib/types'
import { DateToFormDisplay } from '@/lib/utils';
import { getPlatformConfig } from '@/utils/config/getPlatformConfig';
import { FROM_BASE_TO_MILLI_MULTIPLIER, HOURS_IN_DAY, MINUTES_IN_HOUR, SECONDS_IN_MINUTE } from './units';

// Get platform configuration
const config = getPlatformConfig();

/**
 * -----------------------------------
 * -----------------------------------
 *       Noticeboard App ID
 * -----------------------------------
 * -----------------------------------
 */
const envAppId = Number(import.meta.env.VITE_NOTICEBOARD_APP_ID);
export const noticeboardAppID = (!envAppId || envAppId === 0) ? config.noticeboardAppID : envAppId;

/**
 * -----------------------------------
 * -----------------------------------
 *    Supported payment currencies
 * -----------------------------------
 * -----------------------------------
 */
export const CURRENCIES = new Map(
  Object.entries(config.currencies).map(([key, value]: [string, any]) => [
    BigInt(key),
    value as CurrencyDetails,
  ])
);

export const CURRENCIES_OPTIONS = Array.from(CURRENCIES.entries())
  .filter(([_, details]) => details.allowed)
  .map(([key, details]) => ({ value: key.toString(), display: details.ticker }))

/**
 * -----------------------------------
 * -----------------------------------
 *        Noticeboard limits
 * -----------------------------------
 * -----------------------------------
 */
export const LIMITS_DURATION = config.limits.duration;
export const LIMITS_MAX_STAKE = config.limits.maxStake;
export const LIMIT_MAX_USERS = config.limits.maxUsers;

/**
 * -----------------------------------
 * -----------------------------------
 *        Suggestions for DelCo
 * -----------------------------------
 * -----------------------------------
 */
export const SUGGESTED_DURATION = config.suggestions.delCo.duration; // [days] Default suggest duration
export const PAYMENT_ASA: bigint = BigInt(config.suggestions.delCo.paymentAsa); // Default suggest currency
export const SUGGESTED_MAX_STAKE_BUFFER = config.suggestions.delCo.maxStakeBuffer; // [%] Suggest user a max stake this much % above current stake
export const DEFAULT_MAX_STAKE: bigint = BigInt(config.suggestions.delCo.maxStake); // [uALGO] - in case no wallet is connected

/**
 * -----------------------------------
 * -----------------------------------
 *        Suggestions for ValAd
 * -----------------------------------
 * -----------------------------------
 */
const AD_VALID_FOR = config.suggestions.valAd.time.validFor * HOURS_IN_DAY * MINUTES_IN_HOUR * SECONDS_IN_MINUTE * FROM_BASE_TO_MILLI_MULTIPLIER;
export const AD_TERMS_TIME: AdTermsTime = {
  validUntil: DateToFormDisplay(new Date(Date.now() + AD_VALID_FOR)),
  minDuration: config.suggestions.valAd.time.minDuration,
  maxDuration: config.suggestions.valAd.time.maxDuration,
  setupTime: config.suggestions.valAd.time.setupTime,
  confirmationTime: config.suggestions.valAd.time.confirmationTime,
};

export const AD_TERMS_STAKE: AdTermsStake = config.suggestions.valAd.stake;

export const AD_TERMS_REQS: AdTermsReqs = config.suggestions.valAd.reqs;

export const AD_TERMS_WARN: AdTermsWarn = config.suggestions.valAd.warn;

export const AD_CONFIG: AdConfigValues = config.suggestions.valAd.config;

export const AD_FORM_DEFAULTS: AdFormValues = {
  ...AD_CONFIG,
  ...AD_TERMS_TIME,
  ...CURRENCIES.get(PAYMENT_ASA)!.adTermsFees,
  ...AD_TERMS_STAKE,
  ...AD_TERMS_REQS,
  ...AD_TERMS_WARN,
}
