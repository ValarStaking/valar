import configLocalnet from '../../constants/timing.localnet.json'
import configFnet from '../../constants/timing.fnet.json'
import configMainnet from '../../constants/timing.mainnet.json'

export function getTimingConfig() {
  if (!import.meta.env.VITE_ALGOD_NETWORK) {
    throw new Error(
      'Attempt to get algod config without specifying VITE_ALGOD_NETWORK in the environment variables',
    )
  }

  let config;
  switch (import.meta.env.VITE_ALGOD_NETWORK) {
    case "localnet":
      config = configLocalnet;
      break;
    case "fnet":
        config = configFnet;
        break;
    case "mainnet":
      config = configMainnet;
      break;
    default:
      throw("Unexpected network.");
      break;
  }

  return config;
}
