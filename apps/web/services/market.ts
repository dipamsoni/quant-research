import { useAuthStore } from "@/store/auth";

const MARKET_BASE =
  process.env.NEXT_PUBLIC_MARKET_DATA_URL ?? "http://localhost:8001";

export type Timeframe = "1m" | "5m" | "1h" | "1d" | "1w";
export type IndicatorKey =
  | "sma_20"
  | "ema_50"
  | "rsi_14"
  | "macd_12_26_9"
  | "bbands_20_2";

export interface IndicatorValues {
  sma_20?: number | null;
  ema_50?: number | null;
  rsi_14?: number | null;
  macd_macd?: number | null;
  macd_signal?: number | null;
  macd_histogram?: number | null;
  bb_upper?: number | null;
  bb_middle?: number | null;
  bb_lower?: number | null;
}

export interface Candle {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  indicators?: IndicatorValues | null;
}

export interface AssetResult {
  id: string;
  symbol: string;
  name: string;
  asset_type: string;
  exchange: string;
  currency: string;
  sector: string | null;
  industry: string | null;
}

export interface WatchlistItem {
  id: string;
  symbol: string;
  name: string;
  asset_type: string;
  exchange: string;
  added_at: string;
}

function authHeaders(): HeadersInit {
  const token = useAuthStore.getState().accessToken;
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${MARKET_BASE}${path}`, {
    ...init,
    headers: { ...authHeaders(), ...init?.headers },
  });
  const body = await res.json();
  if (!res.ok) {
    const err = body?.error ?? {};
    throw new Error(err.message ?? "Request failed");
  }
  return body.data as T;
}

export interface NewsArticle {
  id: string;
  headline: string;
  source: string;
  url: string;
  published_at: string;
  summary: string | null;
}

export const marketService = {
  searchAssets: (query: string) =>
    apiFetch<AssetResult[]>(
      `/api/v1/market/assets?search=${encodeURIComponent(query)}&limit=20`
    ),

  getWatchlist: () => apiFetch<WatchlistItem[]>("/api/v1/market/watchlist"),

  addToWatchlist: (symbol: string) =>
    apiFetch<WatchlistItem>("/api/v1/market/watchlist", {
      method: "POST",
      body: JSON.stringify({ symbol }),
    }),

  removeFromWatchlist: (symbol: string) =>
    apiFetch<null>(`/api/v1/market/watchlist/${encodeURIComponent(symbol)}`, {
      method: "DELETE",
    }),

  getNews: (symbol: string) =>
    apiFetch<NewsArticle[]>(
      `/api/v1/market/news?symbol=${encodeURIComponent(symbol)}`
    ),

  getCandles: (
    symbol: string,
    timeframe: Timeframe,
    indicators: IndicatorKey[] = [],
    limit = 300,
  ) => {
    const params = new URLSearchParams({
      symbol,
      timeframe,
      limit: String(limit),
    });
    if (indicators.length > 0) {
      params.set("indicators", indicators.join(","));
    }
    return apiFetch<Candle[]>(`/api/v1/market/candles?${params.toString()}`);
  },
};
