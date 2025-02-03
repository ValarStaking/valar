import {
  Nfd,
  NfdGetLookup200,
  NfdGetLookupParams,
  NfdGetNFDParams,
  NfdSearchV2Params,
  NfdV2SearchRecords,
} from "@/interfaces/nfd";
import axios from "@/lib/axios";
import { AxiosError } from "axios";
import { CacheRequestConfig } from "axios-cache-interceptor";

export class NFDApi {
  static async fetchNfd(
    nameOrID: string | bigint | number,
    params?: NfdGetNFDParams,
    options?: CacheRequestConfig,
  ): Promise<Nfd> {
    const { data: nfd } = await axios.get<Nfd>(`/nfd/${nameOrID}`, {
      ...options,
      params: { ...params, ...options?.params },
    });
    if (!nfd || !nfd.name) {
      throw new Error("NFD not found");
    }
    return nfd;
  }
  static async fetchNfdSearch(params: NfdSearchV2Params, options?: CacheRequestConfig): Promise<NfdV2SearchRecords> {
    const { data: result } = await axios.get<NfdV2SearchRecords>(`/nfd/v2/search`, {
      ...options,
      params: { ...params, ...options?.params },
    });
    return result;
  }

  static async fetchNfdReverseLookup(
    address: string,
    params?: Omit<NfdGetLookupParams, "address">,
    options?: CacheRequestConfig,
  ): Promise<Nfd | null> {
    try {
      if (import.meta.env.VITE_ALGOD_NETWORK === "localnet") {
        // For testing on localnet with emulated mainnet address for different picture sources
        const nonce = Math.random();
        if (nonce < 0.25) {
          address = "DC7K77UQNHNLULBGRNTWJSSFSHUHRWJG3B52B5WKGLFMJ3PBI3DGESEK3Q";
        } else if (nonce < 0.5) {
          address = "Z4H5IYQ2WBS3L7BJLUORQT4M5BAJCMIBG5VQWBP7VSIVFC7OPNLVEYIRKA";
        } else if (nonce < 0.75) {
          address = "FLA2ANGWV6YP724P3SNONMCECNHF7EPRZPM62AGTXS4KEDTDZOLUYBPTQM";
        }
      }

      const { data } = await axios.get<NfdGetLookup200>(`/nfd/lookup`, {
        ...options,
        params: { address: [address], ...params, ...options?.params },
      });
      const nfd = data[address];
      return nfd || null;
    } catch (error) {
      if (error instanceof AxiosError && error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  }

  static async fetchNfdReverseLookups(
    params: NfdGetLookupParams,
    options?: CacheRequestConfig,
  ): Promise<NfdGetLookup200> {
    const { data } = await axios.get<NfdGetLookup200>(`/nfd/lookup`, {
      ...options,
      params: { ...params, ...options?.params },
    });
    return data;
  }
}
