/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_NOTICEBOARD_APP_ID: string

  readonly VITE_ENVIRONMENT: string

  readonly VITE_ALGOD_TOKEN: string
  readonly VITE_ALGOD_SERVER: string
  readonly VITE_ALGOD_PORT: string
  readonly VITE_ALGOD_NETWORK: string

  readonly VITE_INDEXER_TOKEN: string
  readonly VITE_INDEXER_SERVER: string
  readonly VITE_INDEXER_PORT: string

  readonly VITE_KMD_TOKEN: string
  readonly VITE_KMD_SERVER: string
  readonly VITE_KMD_PORT: string
  readonly VITE_KMD_PASSWORD: string
  readonly VITE_KMD_WALLET: string

  readonly VITE_ALGORAND_STATS: string

  readonly VITE_GALGO_APP: string

  readonly VITE_EXPLORER_ACCOUNT_URL: string
  readonly VITE_EXPLORER_TRANSACTION_URL: string
  readonly VITE_EXPLORER_ASSET_URL: string
  readonly VITE_EXPLORER_APPLICATION_URL: string

  readonly VITE_RETI_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}