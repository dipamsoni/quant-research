import { useAuthStore } from "@/store/auth";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface CandleResponse {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  indicators: Record<string, number | null>;
}

function authHeaders(): HeadersInit {
  const token = useAuthStore.getState().accessToken;
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { headers: authHeaders() });
  if (res.status === 404) return [] as unknown as T;
  const body = await res.json();
  if (!res.ok) {
    const err = body?.error ?? body?.detail ?? {};
    throw new Error(err.message ?? "Request failed");
  }
  return body.data as T;
}

export const marketDataService = {
  getNiftyCandles: (from?: string, to?: string): Promise<CandleResponse[]> => {
    const params = new URLSearchParams({
      symbol: "NIFTY50",
      timeframe: "1d",
      limit: "500",
    });
    if (from) params.set("start", from);
    if (to) params.set("end", to);
    return apiFetch<CandleResponse[]>(`/api/v1/market/candles?${params}`);
  },
};
