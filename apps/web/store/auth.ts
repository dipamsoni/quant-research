import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { AuthData, User } from "@/services/auth";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  setAuth: (data: AuthData) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      setAuth: (data) =>
        set({
          user: data.user,
          accessToken: data.access_token,
          refreshToken: data.refresh_token,
        }),
      clearAuth: () => set({ user: null, accessToken: null, refreshToken: null }),
    }),
    { name: "quant-os-auth" }
  )
);
