import { ValTermsGating, ValTermsPricing, ValTermsStakeLimits, ValTermsTiming, ValTermsWarnings, ValidatorAdGlobalState } from "@/interfaces/contracts/ValidatorAd"
import { AdFormValues, AssetAmountUnit, AssetDisplay, DelCoStatus, TimeDisplay, TimeUnit, ValAdStatus } from "@/lib/types"
import { CURRENCIES } from "../constants/platform"
import { adFormSchema } from "@/lib/form-schema"
import { z } from "zod"
import { NoticeboardGlobalState } from "@/interfaces/contracts/Noticeboard"
import { DC_STATE_ENDED_CANNOT_PAY, DC_STATE_ENDED_EXPIRED, DC_STATE_ENDED_LIMITS, DC_STATE_ENDED_NOT_CONFIRMED, DC_STATE_ENDED_NOT_SUBMITTED, DC_STATE_ENDED_SUSPENDED, DC_STATE_ENDED_WITHDREW, DC_STATE_LIVE, DC_STATE_READY, DC_STATE_SUBMITTED, VA_STATE_CREATED, VA_STATE_NOT_LIVE, VA_STATE_NOT_READY, VA_STATE_READY } from "@/constants/states"
import { AssetParams, DAYS_IN_MONTH, FROM_BASE_TO_MILLI_MULTIPLIER, FROM_MILLI_TO_NANO_MULTIPLIER, HOURS_IN_DAY, MINUTES_IN_HOUR, ONE_IN_PPM, SECONDS_IN_MINUTE, TimeParams } from "@/constants/units"
import { ASSUMED_BLOCK_TIME, BLOCKS_PER_MONTH} from "@/constants/timing"
import { ParamsCache } from "./paramsCache"
import { DateToFormDisplay } from "@/lib/utils"

export function strToBytesLength(str: string, length: number): Uint8Array {
  const encoded = new TextEncoder().encode(str)
  if (encoded.length > length) {
    // Truncate the array
    return encoded.slice(0, length)
  } else if (encoded.length < length) {
    // Pad the array
    const paddedArray = new Uint8Array(length)
    paddedArray.set(encoded)
    return paddedArray
  } else {
    // If the length is exactly the same
    return encoded
  }
}

export function bytesToStr(data: Uint8Array) {
  return new TextDecoder().decode(new Uint8Array(data));
}

export function strToBytes(str: string): Uint8Array {
  return new TextEncoder().encode(str);
}

type ByteOrder = 'big' | 'little'
export function bigIntToBytes(value: bigint, byteLength: number, byteOrder: ByteOrder = 'big'): Uint8Array {
  const BytesArray = new Uint8Array(byteLength)

  //Filling the ByteArray
  for (let i = byteLength - 1; i >= 0; i--) {
    const index = byteOrder == 'little' ? byteLength - 1 - i : i
    BytesArray[index] = Number(value & 255n)
    value = value >> 8n
    if (value === 0n) break
  }

  return BytesArray
}

export function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes)
      .map(byte => byte.toString(16).padStart(2, "0"))
      .join("");
}

export function hexToBytes(hex: string): Uint8Array {
  const byteArray = new Uint8Array(hex.length / 2);

  for (let i = 0; i < hex.length; i += 2) {
    byteArray[i / 2] = parseInt(hex.substring(i, i + 2), 16);
  }

  return byteArray;
}

export function decodeDelCoStateToString(state: Uint8Array): {status: DelCoStatus, extStatusText?: string} {
  // Decode delegator contract status
  let status: DelCoStatus = "LIVE";
  let extStatusText = undefined;
  if(bytesToStr(state) === bytesToStr(DC_STATE_READY)){
    status = "AWAITING_SETUP"
  }
  else if(bytesToStr(state) === bytesToStr(DC_STATE_SUBMITTED)){
    status = "CONFIRM_SETUP"
  }
  else if(bytesToStr(state) === bytesToStr(DC_STATE_LIVE)){
    status = "LIVE"
  }
  else{
    status = "ENDED";
    if(bytesToStr(state) === bytesToStr(DC_STATE_ENDED_NOT_SUBMITTED)){
      extStatusText = " - node not prepared in time.";
    } else if(bytesToStr(state) === bytesToStr(DC_STATE_ENDED_NOT_CONFIRMED)){
      extStatusText = " - setup not confirmed in time.";
    } else if(bytesToStr(state) === bytesToStr(DC_STATE_ENDED_LIMITS)){
      extStatusText = " - limits breached too many times.";
    } else if(bytesToStr(state) === bytesToStr(DC_STATE_ENDED_WITHDREW)){
      extStatusText = " - contract was withdrawn.";
    } else if(bytesToStr(state) === bytesToStr(DC_STATE_ENDED_EXPIRED)){
      extStatusText = " - the contract expired.";
    } else if(bytesToStr(state) === bytesToStr(DC_STATE_ENDED_SUSPENDED)){
      extStatusText = " - account suspended by the network.";
    } else if(bytesToStr(state) === bytesToStr(DC_STATE_ENDED_CANNOT_PAY)){
      extStatusText = " - payment was rejected.";
    } else {
      console.error("Unexpected state.");
    }
  }

  return {status, extStatusText};
}

export function decodeValAdStateToString(state: Uint8Array): ValAdStatus{
  // Decode validator ad status
  let status: ValAdStatus = "CREATED"
  if(bytesToStr(state) === bytesToStr(VA_STATE_CREATED)){
    status = "CREATED"
  }
  else if(bytesToStr(state) === bytesToStr(VA_STATE_READY)){
    status = "READY"
  }
  else if(bytesToStr(state) === bytesToStr(VA_STATE_NOT_LIVE)){
    status = "NOT_LIVE"
  }
  else if(bytesToStr(state) === bytesToStr(VA_STATE_NOT_READY)){
    status = "NOT_READY"
  }
  else{
    // If not using UI, Ad can also get in state "SET", which is similar to NOT_LIVE
    status = "NOT_LIVE"
  }

  return status
}

export async function formToTermsAndConfig(
  formValues: z.infer<typeof adFormSchema>,
  gsNoticeBoard: NoticeboardGlobalState,
): Promise<{
  terms: {
    termsTime: ValTermsTiming,
    termsPrice: ValTermsPricing,
    termsStake: ValTermsStakeLimits,
    termsReqs: ValTermsGating,
    termsWarn: ValTermsWarnings,
  },
  config: {
    valManagerAddr: string,
    live: boolean,
    cntDelMax: bigint,
  },
}> {

  const assetId = BigInt(formValues.paymentCurrency);
  const roundMaxEnd = await dateToRounds(formValues.validUntil);

  return ({
    terms:{
      termsTime: {
        roundsSetup: durationToRounds(formValues.setupTime, TimeParams.setup.unit),
        roundsConfirm: durationToRounds(formValues.confirmationTime, TimeParams.confirmation.unit),
        roundsDurationMin: durationToRounds(formValues.minDuration, TimeParams.stake.unit),
        roundsDurationMax: durationToRounds(formValues.maxDuration, TimeParams.stake.unit),
        roundMaxEnd: roundMaxEnd,
      },
      termsPrice: {
        commission: gsNoticeBoard.noticeboardFees.commissionMin,
        feeAssetId: assetId,
        feeRoundMin: feeDisplayToBigInt(formValues.minOperationalFee, "per month", assetId),
        feeRoundVar: feeDisplayToBigInt(formValues.varOperationalFee, "per month & per 100k ALGO", assetId),
        feeSetup: feeDisplayToBigInt(formValues.setupFee, "", assetId),
      },
      termsStake: {
        stakeMax: algoDisplayToBigInt(formValues.maxStake),
        stakeGratis: gratisToBigInt(formValues.gratisStake),
      },
      termsReqs: {
        gatingAsaList: [
          [BigInt(formValues.idASA1), BigInt(formValues.amountASA1)],
          [BigInt(formValues.idASA2), BigInt(formValues.amountASA2)],
        ]
      },
      termsWarn: {
        cntWarningMax: BigInt(formValues.maxWarnings),
        roundsWarning: durationToRounds(formValues.warnTime, TimeParams.warn.unit),
      },
    },
    config: {
      valManagerAddr: formValues.managerAddress,
      live: formValues.acceptingNewUser,
      cntDelMax: BigInt(formValues.maxUser),
    },
  });
}

export function isValidDateTime(input: string): boolean {
  const regex = /^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}$/;
  if (!regex.test(input)) return false;

  const [datePart, timePart] = input.trim().split(/\s+/);  // Splits by any spaces
  const [year, month, day] = datePart.split('-').map(Number);
  const [hour, minute] = timePart.split(':').map(Number);

  const date = new Date(year, month - 1, day, hour, minute);
  return (
      date.getFullYear() === year &&
      date.getMonth() === month - 1 &&
      date.getDate() === day &&
      date.getHours() === hour &&
      date.getMinutes() === minute
  );
}

export async function ValAdToForm(
  gsValAd: ValidatorAdGlobalState,
): Promise<AdFormValues> {

  const state = bytesToStr(gsValAd.state);
  const acceptingNewUser = (state === bytesToStr(VA_STATE_READY)) || (state === bytesToStr(VA_STATE_NOT_READY));
  const assetId = gsValAd.termsPrice.feeAssetId;

  const validUntil = await roundsToDate(gsValAd.termsTime.roundMaxEnd);

  return ({
    // Config
    managerAddress: gsValAd.valManager,
    maxUser: Number(gsValAd.cntDelMax),
    acceptingNewUser: acceptingNewUser,
    // Timing
    validUntil: DateToFormDisplay(validUntil),
    minDuration: Number(roundsToDuration(gsValAd.termsTime.roundsDurationMin, TimeParams.stake, false)),
    maxDuration: Number(roundsToDuration(gsValAd.termsTime.roundsDurationMax, TimeParams.stake, false)),
    setupTime: Number(roundsToDuration(gsValAd.termsTime.roundsSetup, TimeParams.setup, false)),
    confirmationTime: Number(roundsToDuration(gsValAd.termsTime.roundsConfirm, TimeParams.confirmation, false)),
    // Pricing
    paymentCurrency: assetId,
    setupFee: Number(assetAmountToFeeDisplay(gsValAd.termsPrice.feeSetup, assetId, AssetParams.setup)),
    minOperationalFee: Number(assetAmountToFeeDisplay(gsValAd.termsPrice.feeRoundMin, assetId, AssetParams.opMin)),
    varOperationalFee: Number(assetAmountToFeeDisplay(gsValAd.termsPrice.feeRoundVar, assetId, AssetParams.opVar)),
    // Stake
    maxStake: Number(algoBigIntToDisplay(gsValAd.termsStake.stakeMax, "floor")),
    gratisStake: gratisBigIntToNumber(gsValAd.termsStake.stakeGratis),
    // Eligibility Requirements
    idASA1: Number(gsValAd.termsReqs.gatingAsaList[0][0]),
    amountASA1: Number(gsValAd.termsReqs.gatingAsaList[0][1]),
    idASA2: Number(gsValAd.termsReqs.gatingAsaList[1][0]),
    amountASA2: Number(gsValAd.termsReqs.gatingAsaList[1][1]),
    // Warnings
    maxWarnings: Number(gsValAd.termsWarn.cntWarningMax),
    warnTime: Number(roundsToDuration(gsValAd.termsWarn.roundsWarning, TimeParams.warn, false)),
  });
}

export function durationToRounds(
  time: number,
  unit: TimeUnit,
): bigint {

  let factor = 1 / ASSUMED_BLOCK_TIME;
  if(unit === "min"){
    factor *= SECONDS_IN_MINUTE;
  } else if (unit === "h"){
    factor *= SECONDS_IN_MINUTE * MINUTES_IN_HOUR;
  } else if (unit === "day" || unit === "days"){
    factor *= SECONDS_IN_MINUTE * MINUTES_IN_HOUR * HOURS_IN_DAY;
  } else if (unit === "month"){
    factor *= SECONDS_IN_MINUTE * MINUTES_IN_HOUR * HOURS_IN_DAY * DAYS_IN_MONTH;
  } else if (unit === "rounds"){
    factor = 1;
  } else if (unit === "ms"){
    factor /= FROM_BASE_TO_MILLI_MULTIPLIER;
  }
  const rounds = time * factor;

  return BigInt(Math.floor(rounds));
}

export function roundsToDuration(
  rounds: bigint | number,
  timeDisplay: TimeDisplay,
  wUnit?: boolean,
): string {

  const unit = timeDisplay.unit;

  let factor = 1 / ASSUMED_BLOCK_TIME;
  if(unit === "min"){
    factor *= SECONDS_IN_MINUTE;
  } else if (unit === "h"){
    factor *= SECONDS_IN_MINUTE * MINUTES_IN_HOUR;
  } else if (unit === "day" || unit === "days"){
    factor *= SECONDS_IN_MINUTE * MINUTES_IN_HOUR * HOURS_IN_DAY;
  } else if (unit === "month"){
    factor *= SECONDS_IN_MINUTE * MINUTES_IN_HOUR * HOURS_IN_DAY * DAYS_IN_MONTH;
  } else if (unit === "rounds"){
    factor = 1;
  } else if (unit === "ms"){
    factor /= FROM_BASE_TO_MILLI_MULTIPLIER;
  }
  const duration = Number(rounds) / factor;

  const display = duration.toFixed(timeDisplay.decimals) + (wUnit ? " " + unit : "");

  return display;
}

export async function roundsToDate(
  round: bigint,
): Promise<Date> {

  const now = Date.now();

  const roundCur = await ParamsCache.getRound();
  const roundDuration = round - roundCur;
  const duration = Number(roundsToDuration(roundDuration, {unit: "ms", decimals: 0}));
  const timeRound = now + duration;
  const date = new Date(timeRound);

  return date;
}

export async function dateToRounds(
  date: string,
): Promise<bigint> {

  const now = Date.now();
  const dateRaw = new Date(date);

  const roundCur = await ParamsCache.getRound();
  const rounds = durationToRounds(dateRaw.getTime() - now, "ms");
  const roundEnd = roundCur + rounds;

  return roundEnd;
}

export function feeDisplayToBigInt(
  fee: number,
  unit: AssetAmountUnit,
  asset: bigint,
): bigint {

  const currencyInfo = CURRENCIES.get(asset)!;

  let value = 0;
  if(unit === ""){
    value = fee * (10 ** currencyInfo.decimals);
  } else if (unit === "per month"){
    value = fee * (((10 ** currencyInfo.decimals) / BLOCKS_PER_MONTH) * FROM_BASE_TO_MILLI_MULTIPLIER);
  } else if (unit === "per month & per 100k ALGO"){
    const ALGO_100k = 10**5;
    value = fee * (((10 ** currencyInfo.decimals) / (BLOCKS_PER_MONTH * ALGO_100k)) * FROM_BASE_TO_MILLI_MULTIPLIER * FROM_MILLI_TO_NANO_MULTIPLIER);
  }

  return BigInt(Math.floor(value));
}

export function assetAmountToFeeDisplay(
  amount: bigint,
  asset: bigint,
  assetDisplay: AssetDisplay,
  wTicker?: boolean,
): string {

  const _amount = Number(amount);
  const currencyInfo = CURRENCIES.get(asset);

  if(!currencyInfo) return "N/A";

  const unit = assetDisplay.unit;
  const ticker = currencyInfo.ticker;

  let value = 0;
  if(unit === ""){
    value = _amount / (10 ** currencyInfo.decimals);
  } else if (unit === "per month"){
    value = _amount / (((10 ** currencyInfo.decimals) / BLOCKS_PER_MONTH) * FROM_BASE_TO_MILLI_MULTIPLIER);
  } else if (unit === "per month & per 100k ALGO"){
    const ALGO_100k = 10**5;
    value = _amount / (((10 ** currencyInfo.decimals) / (BLOCKS_PER_MONTH * ALGO_100k)) * FROM_BASE_TO_MILLI_MULTIPLIER * FROM_MILLI_TO_NANO_MULTIPLIER);
  } else if (unit === "raw") {
    value = _amount;
  }

  const display = value.toFixed(assetDisplay.decimals) + (wTicker ? " " + ticker : "");

  return display; //value.toFixed(currencyInfo.displayDecimals);
}

export function algoDisplayToBigInt(
  amount: number,
): bigint {

  const value = amount * 10**6;

  return BigInt(Math.floor(value));
}

export function algoBigIntToDisplay(
  amount: bigint,
  round: "ceil" | "floor" | "none" | "raw",
  wUnit?: boolean,
  decimals?: number,
): string {

  let value = 0;
  let unit = "N/A";

  if (round === "raw"){
    value = Number(amount);
    unit = "uALGO";
  } else {
    value = Number(amount) / 10**6;
    unit = "ALGO";

    if(round === "ceil"){
      value = Math.ceil(value);
    } else if(round === "floor"){
      value = Math.floor(value);
    }
  }

  let display = "";
  if(decimals && round !== "raw"){
    display = value.toFixed(decimals);
  } else {
    display = value.toString();
  }
  display += (wUnit ? " " + unit : "");

  return display;
}

export function gratisToBigInt(
  amount: number,
): bigint {

  const value = (amount / 100) * ONE_IN_PPM;

  return BigInt(Math.floor(value));
}

export function gratisBigIntToNumber(
  amount: bigint,
): number {

  const value = (Number(amount) / ONE_IN_PPM) * 100;

  return value;
}


export function ellipseAddress(address = ``, width = 6): string {
  return address ? `${address.slice(0, width)}...${address.slice(-width)}` : address
}

export const timeFormatter = (seconds: number) => {
  const hrs = Math.floor(seconds / 3600);
  const min = Math.floor((seconds % 3600) / 60);
  const sec = seconds % 60;

  if (hrs > 0) {
    return `${String(hrs).padStart(2, "0")}:${String(min).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
  }

  return `${String(min).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
};