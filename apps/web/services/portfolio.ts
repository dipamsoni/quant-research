import { useAuthStore } from "@/store/auth";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface Portfolio {
  id: string;
  user_id: string;
  name: string;
  base_currency: string;
  risk_profile: string | null;
  cash_balance: string;
  created_at: string;
}

export interface Holding {
  id: string;
  portfolio_id: string;
  asset_id: string;
  symbol: string;
  quantity: string;
  avg_price: string;
  market_value: string | null;
}

export interface MetricsSnapshot {
  id: string;
  portfolio_id: string;
  date: string;
  total_value: string;
  daily_return: string | null;
  sharpe_ratio: string | null;
  max_drawdown: string | null;
  volatility: string | null;
  beta: string | null;
  alpha: string | null;
  cost_basis: string | null;
  unrealized_pnl: string | null;
  realized_pnl: string | null;
}

export interface PortfolioDetail extends Portfolio {
  holdings: Holding[];
  latest_metrics: MetricsSnapshot | null;
}

export interface AllocationItem {
  asset_id: string;
  symbol?: string;
  value: string;
  pct: string;
}

export interface Allocation {
  total_value: string;
  allocations: AllocationItem[];
}

export interface TransactionCreate {
  asset_id: string;
  symbol: string;
  transaction_type: "buy" | "sell";
  quantity: string;
  price: string;
  fees?: string;
  executed_at?: string;
}

export interface PortfolioCreate {
  name: string;
  base_currency?: string;
  risk_profile?: string;
}

function authHeaders(): HeadersInit {
  const token = useAuthStore.getState().accessToken;
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
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

export const portfolioService = {
  list: () => apiFetch<Portfolio[]>("/api/v1/portfolio"),

  create: (data: PortfolioCreate) =>
    apiFetch<Portfolio>("/api/v1/portfolio", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  get: (id: string) => apiFetch<PortfolioDetail>(`/api/v1/portfolio/${id}`),

  addTransaction: (id: string, data: TransactionCreate) =>
    apiFetch<{ id: string }>(`/api/v1/portfolio/${id}/transactions`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getMetrics: (id: string, from?: string, to?: string) => {
    const params = new URLSearchParams();
    if (from) params.set("from", from);
    if (to) params.set("to", to);
    const qs = params.toString();
    return apiFetch<MetricsSnapshot[]>(
      `/api/v1/portfolio/${id}/metrics${qs ? `?${qs}` : ""}`
    );
  },

  getAllocation: (id: string) =>
    apiFetch<Allocation>(`/api/v1/portfolio/${id}/allocation`),
};
