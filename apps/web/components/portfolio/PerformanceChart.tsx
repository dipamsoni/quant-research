"use client";

import { useMemo, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { usePortfolioMetrics } from "@/hooks/usePortfolio";
import { useNiftyBenchmark } from "@/hooks/usePortfolio";
import type { CandleResponse } from "@/services/marketData";
import type { MetricsSnapshot } from "@/services/portfolio";

type Range = "1W" | "1M" | "3M" | "6M" | "1Y" | "All";

const RANGES: Range[] = ["1W", "1M", "3M", "6M", "1Y", "All"];

function rangeToFrom(range: Range): string | undefined {
  if (range === "All") return undefined;
  const d = new Date();
  const offsets: Record<Range, () => void> = {
    "1W": () => d.setDate(d.getDate() - 7),
    "1M": () => d.setMonth(d.getMonth() - 1),
    "3M": () => d.setMonth(d.getMonth() - 3),
    "6M": () => d.setMonth(d.getMonth() - 6),
    "1Y": () => d.setFullYear(d.getFullYear() - 1),
    All: () => {},
  };
  offsets[range]();
  return d.toISOString().slice(0, 10);
}

function toDateStr(isoOrDate: string): string {
  return isoOrDate.slice(0, 10);
}

interface ChartPoint {
  date: string;
  portfolioNorm: number;
  niftyNorm: number | null;
  portfolioValue: number;
  niftyClose: number | null;
}

function buildChartData(
  metrics: MetricsSnapshot[],
  niftyCandles: CandleResponse[]
): ChartPoint[] {
  const sorted = [...metrics].sort(
    (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
  );
  if (sorted.length === 0) return [];

  const niftyMap = new Map(
    niftyCandles.map((c) => [toDateStr(c.time), c.close])
  );

  // Find first portfolio value for normalization
  const basePortfolio = parseFloat(sorted[0].total_value);

  // Find Nifty base: earliest date that matches a portfolio date
  let baseNifty: number | null = null;
  for (const m of sorted) {
    const close = niftyMap.get(m.date);
    if (close != null) {
      baseNifty = close;
      break;
    }
  }

  return sorted.map((m) => {
    const portfolioValue = parseFloat(m.total_value);
    const niftyClose = niftyMap.get(m.date) ?? null;
    return {
      date: m.date,
      portfolioValue,
      niftyClose,
      portfolioNorm:
        basePortfolio > 0
          ? parseFloat(((portfolioValue / basePortfolio) * 100).toFixed(2))
          : 100,
      niftyNorm:
        niftyClose != null && baseNifty != null && baseNifty > 0
          ? parseFloat(((niftyClose / baseNifty) * 100).toFixed(2))
          : null,
    };
  });
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("en-IN", { day: "numeric", month: "short" });
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function PerformanceTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;

  const portfolio = payload.find((p: { dataKey: string }) => p.dataKey === "portfolioNorm");
  const nifty = payload.find((p: { dataKey: string }) => p.dataKey === "niftyNorm");

  const pVal: number = portfolio?.value ?? 100;
  const nVal: number | null = nifty?.value ?? null;
  const outperformance = nVal != null ? (pVal - nVal).toFixed(2) : null;

  const portfolioRaw: number = portfolio?.payload?.portfolioValue ?? 0;
  const sign = outperformance != null && parseFloat(outperformance) >= 0 ? "+" : "";

  return (
    <div
      style={{
        background: "hsl(var(--popover))",
        border: "1px solid hsl(var(--border))",
        borderRadius: "0.5rem",
        padding: "10px 14px",
        fontSize: "0.75rem",
        lineHeight: "1.6",
      }}
    >
      <p className="mb-1 font-semibold">{formatDate(label as string)}</p>
      <p style={{ color: "#6366f1" }}>
        Portfolio: {pVal.toFixed(1)}{" "}
        <span className="text-muted-foreground">
          (₹{portfolioRaw.toLocaleString("en-IN", { maximumFractionDigits: 0 })})
        </span>
      </p>
      {nVal != null && (
        <p style={{ color: "#10b981" }}>Nifty 50: {nVal.toFixed(1)}</p>
      )}
      {outperformance != null && (
        <p
          className={parseFloat(outperformance) >= 0 ? "text-emerald-400" : "text-rose-400"}
        >
          Outperformance: {sign}{outperformance} pts
        </p>
      )}
    </div>
  );
}

interface PerformanceChartProps {
  portfolioId: string;
}

export function PerformanceChart({ portfolioId }: PerformanceChartProps) {
  const [range, setRange] = useState<Range>("1M");
  const from = rangeToFrom(range);

  const { data: metrics = [], isLoading: metricsLoading } = usePortfolioMetrics(
    portfolioId,
    from,
    undefined
  );
  const { data: niftyCandles = [], isLoading: niftyLoading } = useNiftyBenchmark(from, undefined);

  const isLoading = metricsLoading || niftyLoading;

  const chartData = useMemo(
    () => buildChartData(metrics, niftyCandles),
    [metrics, niftyCandles]
  );

  const hasNifty = chartData.some((p) => p.niftyNorm != null);

  if (isLoading) {
    return <div className="bg-muted h-[280px] animate-pulse rounded-xl" />;
  }

  if (metrics.length === 0) {
    return (
      <div className="bg-card border-border flex h-[280px] items-center justify-center rounded-xl border border-dashed">
        <p className="text-muted-foreground text-sm">No performance data yet</p>
      </div>
    );
  }

  return (
    <div className="bg-card border-border rounded-xl border p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold">Performance</h3>
        <div className="flex gap-0.5 rounded-md border text-xs overflow-hidden">
          {RANGES.map((r) => (
            <button
              key={r}
              onClick={() => setRange(r)}
              className={
                range === r
                  ? "bg-primary text-primary-foreground px-2.5 py-1"
                  : "text-muted-foreground hover:bg-muted px-2.5 py-1"
              }
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={230}>
        <LineChart data={chartData} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis
            dataKey="date"
            tickFormatter={formatDate}
            tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
            tickLine={false}
            axisLine={false}
            minTickGap={40}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v: number) => `${v.toFixed(0)}`}
            domain={["auto", "auto"]}
          />
          <Tooltip content={<PerformanceTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: "0.75rem", paddingTop: "8px" }}
            iconType="plainline"
          />
          <Line
            type="monotone"
            dataKey="portfolioNorm"
            name="Portfolio"
            stroke="#6366f1"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
            connectNulls
          />
          {hasNifty && (
            <Line
              type="monotone"
              dataKey="niftyNorm"
              name="Nifty 50"
              stroke="#10b981"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
              connectNulls={false}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
