import { decodeAddress, LogicSigAccount } from "algosdk";

export class FolksFinance {
  /**
   * ================================
   *       Folks Finance gALGO
   * ================================
   */

  static appId = Number(import.meta.env.VITE_GALGO_APP);

  public static getEscrow(userAddr: string): string {
    const prefix = Uint8Array.from([
      7, 32, 1, 1, 128, 36, 70, 79, 76, 75, 83, 95, 70, 73, 78, 65, 78, 67, 69,
      95, 65, 76, 71, 79, 95, 76, 73, 81, 85, 73, 68, 95, 71, 79, 86, 69, 82,
      78, 65, 78, 67, 69, 72, 49, 22, 34, 9, 56, 16, 34, 18, 68, 49, 22, 34, 9,
      56, 0, 128, 32,
    ]);
    const suffix = Uint8Array.from([
      18, 68, 49, 22, 34, 9, 56, 8, 20, 68, 49, 22, 34, 9, 56, 32, 50, 3, 18,
      68, 49, 22, 34, 9, 56, 9, 50, 3, 18, 68, 49, 22, 34, 9, 56, 21, 50, 3, 18,
      68, 34, 67,
    ]);
    return new LogicSigAccount(
      new Uint8Array([
        ...prefix,
        ...decodeAddress(userAddr).publicKey,
        ...suffix,
      ]),
    ).address();
  }
}
