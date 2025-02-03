import { AppRouter } from "@/pages/AppRouter";
import { walletManager } from "@/utils/wallet";
import { WalletProvider } from "@txnlab/use-wallet-react";
import { AppGlobalStateProvider } from "./contexts/AppGlobalStateContext";

function App() {
  return (
    <WalletProvider manager={walletManager}>
      <AppGlobalStateProvider>
        <AppRouter />
      </AppGlobalStateProvider>
    </WalletProvider>
  );
}

export default App;
