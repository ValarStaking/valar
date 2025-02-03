import { Nfd } from "@/interfaces/nfd"
import { getNfdAppFromViteEnvironment } from "./config/getNfdConfig"

/**
 * Generates the NFD profile URL for the provided name.
 * @param {string} name - The NFD name to generate the URL for
 * @returns {string} The NFD profile URL
 * @example
 * getNfdProfileUrl('example.algo') // 'https://app.nf.domains/name/example.algo'
 */
export function getNfdProfileUrl(name: string): string {
  const baseUrl = getNfdAppFromViteEnvironment()
  return `${baseUrl}/name/${name}`
}

/**
 * Generates the NFD avatar URL for the provided NFD.
 * The base URL must be set as VITE_NFD_APP_URL in the Vite environment.
 * @param {Nfd} nfd - The NFD to generate the URL for
 * @returns {string} The NFD avatar URL
 * @example
 * getNfdAvatarUrl(nfd) // 'https://app.nf.domains/img/nfd-image-placeholder.jpg'
 */
export const getNfdAvatarUrl = (nfd: Nfd): string | undefined => {
  const res = nfd?.properties?.userDefined?.avatar || nfd?.properties?.verified?.avatar

  let url = undefined;
  if (res?.startsWith("ipfs://")) {
    url = "https://images.nf.domains/" + res.replace("://", "/");
  } else {
    url = res;
  }

  return url
}