"use client";

import { useMemo } from "react";
import { TrendingUpIcon, TrendingDownIcon } from "lucide-react";
import type { PortfolioDetail } from "@/services/portfolio";
import { cn } from "@/lib/utils";
import { usePrices } from "@/hooks/usePrices";
import { usePricesStore } from "@/store/prices";

interface SummaryCardsProps {
  portfolio: PortfolioDetail;
}

function fmtInr(n: number | null | undefined): string {
  if (n == null || isNaN(n)) return "—";
  return `₹${n.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function fmtStr(
  n: string | null | undefined,
  prefix = "",
  suffix = "",
  decimals = 2
): string {
  if (n == null) return "—";
  const v = parseFloat(n);
  if (isNaN(v)) return "—";
  return `${prefix}${v.toLocaleString("en-IN", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })}${suffix}`;
}

function fmtPct(n: string | null | undefined) {
  return fmtStr(n, "", "%");
}

interface CardProps {
  label: string;
  value: string;
  sub?: string;
  trend?: "up" | "down" | "neutral";
  showArrow?: boolean;
}

function MetricCard({ label, value, sub, trend, showArrow }: CardProps) {
  return (
    <div className="bg-card border-border rounded-xl border p-4">
      <p className="text-muted-foreground mb-1 text-xs font-medium uppercase tracking-wider">
        {label}
      </p>
      <p
        className={cn(
          "flex items-center gap-1 font-mono text-xl font-semibold",
          trend === "up" && "text-emerald-500",
          trend === "down" && "text-red-500"
        )}
      >
        {showArrow && trend === "up" && (
          <TrendingUpIcon className="size-4 shrink-0" aria-hidden />
        )}
        {showArrow && trend === "down" && (
          <TrendingDownIcon className="size-4 shrink-0" aria-hidden />
        )}
        {value}
      </p>
      {sub && <p className="text-muted-foreground mt-0.5 text-xs">{sub}</p>}
    </div>
  );
}

export function SummaryCards({ portfolio }: SummaryCardsProps) {
  const m = portfolio.latest_metrics;

  // Subscribe to live WebSocket prices for all held symbols
  const symbols = useMemo(
    () => portfolio.holdings.map((h) => h.symbol),
    // stable key so effect only re-runs when the symbol set changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [portfolio.holdings.map((h) => h.symbol).join(",")]
  );
  usePrices(symbols);
  const allPrices = usePricesStore((s) => s.prices);

  const { liveTotal, unrealizedPnL } = useMemo(() => {
    let holdingsValue = 0;
    let costBasis = 0;
    for (const h of portfolio.holdings) {
      const qty = parseFloat(h.quantity);
      const avg = parseFloat(h.avg_price);
      if (!isNaN(qty) && !isNaN(avg)) costBasis += qty * avg;

      const livePrice = allPrices[h.symbol]?.price;
      if (livePrice != null && !isNaN(qty)) {
        holdingsValue += qty * livePrice;
      } else if (h.market_value) {
        holdingsValue += parseFloat(h.market_value) || 0;
      }
    }
    const cash = parseFloat(portfolio.cash_balance) || 0;
    return {
      liveTotal: holdingsValue + cash,
      unrealizedPnL: holdingsValue - costBasis,
    };
  }, [portfolio, allPrices]);

  const dailyReturn = m?.daily_return ? parseFloat(m.daily_return) : null;
  const hasHoldings = portfolio.holdings.length > 0;

  const totalValueDisplay = hasHoldings
    ? fmtInr(liveTotal)
    : fmtStr(m?.total_value, "₹");

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
      <MetricCard
        label="Total Value"
        value={totalValueDisplay}
        sub={portfolio.base_currency}
      />
      <MetricCard
        label="Daily Return"
        value={fmtPct(m?.daily_return)}
        trend={dailyReturn == null ? "neutral" : dailyReturn >= 0 ? "up" : "down"}
        showArrow
        sub={m?.date ?? undefined}
      />
      <MetricCard
        label="Unrealized P&L"
        value={hasHoldings ? fmtInr(unrealizedPnL) : "—"}
        trend={
          !hasHoldings ? "neutral" : unrealizedPnL >= 0 ? "up" : "down"
        }
      />
      <MetricCard
        label="Realized P&L"
        value={fmtStr(m?.realized_pnl, "₹")}
        trend={
          m?.realized_pnl == null
            ? "neutral"
            : parseFloat(m.realized_pnl) >= 0
            ? "up"
            : "down"
        }
        sub="cumulative"
      />
      <MetricCard
        label="Sharpe Ratio"
        value={fmtStr(m?.sharpe_ratio, "", "", 3)}
        sub="annualised"
      />
      <MetricCard
        label="Max Drawdown"
        value={fmtPct(m?.max_drawdown)}
        trend={m?.max_drawdown ? "down" : "neutral"}
      />
      <MetricCard
        label="Cash"
        value={fmtStr(portfolio.cash_balance, "₹")}
        sub="available"
      />
    </div>
  );
}
