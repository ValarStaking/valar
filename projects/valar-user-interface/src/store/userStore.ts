import { UserInfo } from '@/interfaces/contracts/User';
import { KeyRegParams } from '@/lib/types';
import { create } from 'zustand';

export interface AccountInfo {
  address: string;
  algo: bigint;
  assets: Map<bigint, bigint>;
  keyRegParams: KeyRegParams | undefined;
  trackedPerformance: boolean;
}

export interface User extends AccountInfo {
  userInfo: UserInfo | undefined;
  beneficiary: AccountInfo;
  galgo: AccountInfo | null;
}

export interface UserStore {
  user: User | null;
  setUser: (user: UserStore['user']) => void;
}

const useUserStore = create<UserStore>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
}));

export default useUserStore;
