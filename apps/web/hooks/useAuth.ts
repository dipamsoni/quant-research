"use client";

import { useRouter } from "next/navigation";
import { authService } from "@/services/auth";
import { useAuthStore } from "@/store/auth";

export function useAuth() {
  const router = useRouter();
  const { user, accessToken, setAuth, clearAuth } = useAuthStore();

  async function login(email: string, password: string) {
    const data = await authService.login(email, password);
    setAuth(data);
    router.push("/");
  }

  async function register(payload: {
    email: string;
    username: string;
    password: string;
    full_name?: string;
  }) {
    const data = await authService.register(payload);
    setAuth(data);
    router.push("/");
  }

  async function logout() {
    if (accessToken) {
      await authService.logout(accessToken).catch(() => {});
    }
    clearAuth();
    router.push("/login");
  }

  async function refreshSession(): Promise<boolean> {
    const { refreshToken } = useAuthStore.getState();
    if (!refreshToken) return false;
    try {
      const data = await authService.refresh(refreshToken);
      setAuth(data);
      return true;
    } catch {
      clearAuth();
      return false;
    }
  }

  return {
    user,
    accessToken,
    isAuthenticated: !!accessToken,
    login,
    register,
    logout,
    refreshSession,
  };
}
