import { CURRENCIES, LIMIT_MAX_USERS, LIMITS_DURATION, LIMITS_MAX_STAKE } from "@/constants/platform";
import { HOURS_IN_DAY, MINUTES_IN_HOUR, SECONDS_IN_MINUTE } from "@/constants/units";
import { isValidDateTime } from "@/utils/convert";
import { isValidAddress } from "algosdk";
import { z } from "zod";

export const adFormSchema = z
  .object({
    paymentCurrency: z.string(),
    setupFee: z.coerce.number(),
    minOperationalFee: z.coerce.number(),
    varOperationalFee: z.coerce.number(),
    maxStake: z.coerce.number().min(LIMITS_MAX_STAKE.min).max(LIMITS_MAX_STAKE.max),
    gratisStake: z.coerce.number().min(0).max(100),
    validUntil: z.coerce.string(),
    minDuration: z.coerce.number().min(LIMITS_DURATION.min),
    maxDuration: z.coerce.number().max(LIMITS_DURATION.max),
    setupTime: z.coerce.number().min(0),
    confirmationTime: z.coerce.number().min(0),
    maxWarnings: z.coerce.number().min(0).int({ message: "Enter an integer." }),
    warnTime: z.coerce.number().min(0),
    idASA1: z.coerce.number().min(0).int(),
    amountASA1: z.coerce.number().min(0).int({ message: "Please enter amount in ASA's smallest unit as an integer." }),
    idASA2: z.coerce.number().min(0).int(),
    amountASA2: z.coerce.number().min(0).int({ message: "Please enter amount in ASA's smallest unit as an integer." }),
    managerAddress: z.coerce.string(),
    maxUser: z.coerce.number().min(0).max(LIMIT_MAX_USERS).int({ message: "Enter an integer." }),
    acceptingNewUser: z.boolean(),
  })
  .superRefine((data, ctx) => {
    // Validate maxDuration >= minDuration
    if (data.maxDuration < data.minDuration) {
      ctx.addIssue({
        code: "custom",
        path: ["maxDuration"],
        message: "Max duration must be larger or equal to min duration.",
      });
    }
    if (data.minDuration > data.maxDuration) {
      ctx.addIssue({
        code: "custom",
        path: ["minDuration"],
        message: "Min duration must be smaller or equal to max duration.",
      });
    }

    // Validate minDuration > setupTime + confirmationTime
    const minDurationInSeconds = data.minDuration * HOURS_IN_DAY * MINUTES_IN_HOUR * SECONDS_IN_MINUTE;
    const setupAndConfirmationTimeInSeconds =
      data.setupTime * SECONDS_IN_MINUTE + data.confirmationTime * MINUTES_IN_HOUR * SECONDS_IN_MINUTE;

    if (minDurationInSeconds <= setupAndConfirmationTimeInSeconds) {
      ctx.addIssue({
        code: "custom",
        path: ["minDuration"],
        message: "Min duration must be larger than the sum of setup time and confirmation time.",
      });
    }

    // Validate fees against the minimums for the specified currency
    const currency = CURRENCIES.get(BigInt(data.paymentCurrency))!;
    if (data.setupFee < currency.adTermsFeesMin.setupFee) {
      ctx.addIssue({
        code: "custom",
        path: ["setupFee"],
        message: `Minimum setup fee is ${currency.adTermsFeesMin.setupFee}.`,
      });
    }

    if (data.minOperationalFee < currency.adTermsFeesMin.minOperationalFee) {
      ctx.addIssue({
        code: "custom",
        path: ["minOperationalFee"],
        message: `Minimum min operational fee is ${currency.adTermsFeesMin.minOperationalFee}.`,
      });
    }

    if (data.varOperationalFee < currency.adTermsFeesMin.varOperationalFee) {
      ctx.addIssue({
        code: "custom",
        path: ["varOperationalFee"],
        message: `Minimum var operational fee is ${currency.adTermsFeesMin.varOperationalFee}.`,
      });
    }

    // Check if valid Algorand address has been entered
    if (!isValidAddress(data.managerAddress)) {
      ctx.addIssue({
        code: "custom",
        path: ["managerAddress"],
        message: `Manager address must be a valid Algorand address.`,
      });
    }

    // Check if validUntil has been entered as YYYY-MM-DD HH:mm
    if (!isValidDateTime(data.validUntil)) {
      ctx.addIssue({
        code: "custom",
        path: ["validUntil"],
        message: `Enter date as: YYYY-MM-DD HH:mm`,
      });
    }
  });
