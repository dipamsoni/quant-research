const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string | null;
  role: string;
}

export interface AuthData {
  user: User;
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

export class APIError extends Error {
  constructor(
    public code: string,
    message: string
  ) {
    super(message);
    this.name = "APIError";
  }
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  const body = await res.json();
  if (!res.ok) {
    const err = body?.error ?? {};
    throw new APIError(err.code ?? "ERROR", err.message ?? "Request failed");
  }
  return body.data as T;
}

export const authService = {
  register: (payload: { email: string; username: string; password: string; full_name?: string }) =>
    apiFetch<AuthData>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  login: (email: string, password: string) =>
    apiFetch<AuthData>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  refresh: (refresh_token: string) =>
    apiFetch<AuthData>("/api/v1/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token }),
    }),

  logout: (access_token: string) =>
    apiFetch<{ message: string }>("/api/v1/auth/logout", {
      method: "POST",
      headers: { Authorization: `Bearer ${access_token}` },
    }),

  me: (access_token: string) =>
    apiFetch<User>("/api/v1/auth/me", {
      headers: { Authorization: `Bearer ${access_token}` },
    }),
};
