"use client";

import { useEffect, useRef } from "react";
import { authService } from "@/services/auth";
import { useAuthStore } from "@/store/auth";

export function AuthInitializer() {
  const { refreshToken, setAuth, clearAuth } = useAuthStore();
  const attempted = useRef(false);

  useEffect(() => {
    if (attempted.current || !refreshToken) return;
    attempted.current = true;

    authService
      .refresh(refreshToken)
      .then(setAuth)
      .catch(() => clearAuth());
  }, [refreshToken, setAuth, clearAuth]);

  return null;
}
