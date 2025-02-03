import { SupportedWallet, WalletId, WalletManager } from "@txnlab/use-wallet-react";
import {
  getAlgodConfigFromViteEnvironment,
  getAlgodNetwork,
  getKmdConfigFromViteEnvironment,
} from '@/utils/config/getAlgoClientConfigs'

let wallets: SupportedWallet[]
const siteName = 'Valar'
if (import.meta.env.VITE_ALGOD_NETWORK === 'localnet') {
  const kmdConfig = getKmdConfigFromViteEnvironment()
  wallets = [
    {
      id: WalletId.KMD,
      options: {
        wallet: kmdConfig.wallet,
        baseServer: kmdConfig.server,
        token: String(kmdConfig.token),
        port: String(kmdConfig.port),
      },
    },
    { id: WalletId.LUTE, options: { siteName } },
  ]
} else if (import.meta.env.VITE_ALGOD_NETWORK === 'fnet') {
  wallets = [
    { id: WalletId.LUTE, options: { siteName } },
  ]
} else {
  wallets = [
    WalletId.DEFLY,
    WalletId.PERA,
    WalletId.KIBISIS,
    WalletId.EXODUS,
    { id: WalletId.LUTE, options: { siteName } },
  ]
}

const algodConfig = getAlgodConfigFromViteEnvironment()
const network = getAlgodNetwork()

export const walletManager = new WalletManager({
  wallets,
  network,
  algod: {
    baseServer: algodConfig.server,
    port: algodConfig.port,
    token: algodConfig.token as string,
  },
  options: {
    resetNetwork: true,
  },
})
