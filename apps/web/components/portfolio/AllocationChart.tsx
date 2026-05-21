"use client";

import { useState } from "react";
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from "recharts";
import type { Allocation, Holding } from "@/services/portfolio";
import { sectorOf } from "@/lib/nse-sectors";

const COLORS = [
  "#6366f1", "#22d3ee", "#f59e0b", "#10b981", "#f43f5e",
  "#8b5cf6", "#14b8a6", "#fb923c", "#a3e635", "#e879f9",
];

type View = "asset" | "sector";

interface AllocationChartProps {
  allocation?: Allocation;
  holdings?: Holding[];
  isLoading?: boolean;
}

interface ChartEntry {
  name: string;
  value: number;
  pct: number;
}

function buildAssetData(allocation: Allocation, holdings: Holding[]): ChartEntry[] {
  const symbolMap = new Map(holdings.map((h) => [h.asset_id, h.symbol]));
  return allocation.allocations.map((a) => ({
    name: a.symbol ?? symbolMap.get(a.asset_id) ?? a.asset_id.slice(0, 8),
    value: parseFloat(a.value),
    pct: parseFloat(a.pct),
  }));
}

function buildSectorData(allocation: Allocation, holdings: Holding[]): ChartEntry[] {
  const symbolMap = new Map(holdings.map((h) => [h.asset_id, h.symbol]));
  const sectorTotals = new Map<string, number>();

  for (const a of allocation.allocations) {
    const symbol = a.symbol ?? symbolMap.get(a.asset_id) ?? "";
    const sector = sectorOf(symbol);
    sectorTotals.set(sector, (sectorTotals.get(sector) ?? 0) + parseFloat(a.value));
  }

  const total = parseFloat(allocation.total_value);
  return Array.from(sectorTotals.entries())
    .sort((a, b) => b[1] - a[1])
    .map(([name, value]) => ({
      name,
      value,
      pct: total > 0 ? parseFloat(((value / total) * 100).toFixed(4)) : 0,
    }));
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function AllocationTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const { name, value, pct } = payload[0].payload as ChartEntry;
  return (
    <div
      style={{
        background: "hsl(var(--popover))",
        border: "1px solid hsl(var(--border))",
        borderRadius: "0.5rem",
        padding: "8px 12px",
        fontSize: "0.75rem",
      }}
    >
      <p className="font-semibold">{name}</p>
      <p>₹{value.toLocaleString("en-IN", { maximumFractionDigits: 0 })}</p>
      <p className="text-muted-foreground">{pct.toFixed(1)}%</p>
    </div>
  );
}

export function AllocationChart({ allocation, holdings = [], isLoading }: AllocationChartProps) {
  const [view, setView] = useState<View>("asset");

  if (isLoading) {
    return <div className="bg-muted h-64 animate-pulse rounded-xl" />;
  }

  if (!allocation || allocation.allocations.length === 0) {
    return (
      <div className="bg-card border-border flex h-64 items-center justify-center rounded-xl border border-dashed">
        <p className="text-muted-foreground text-sm">No holdings yet</p>
      </div>
    );
  }

  const data =
    view === "asset"
      ? buildAssetData(allocation, holdings)
      : buildSectorData(allocation, holdings);

  return (
    <div className="bg-card border-border rounded-xl border p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold">Allocation</h3>
        <div className="flex rounded-md border text-xs overflow-hidden">
          {(["asset", "sector"] as View[]).map((v) => (
            <button
              key={v}
              onClick={() => setView(v)}
              className={
                view === v
                  ? "bg-primary text-primary-foreground px-3 py-1 capitalize"
                  : "text-muted-foreground hover:bg-muted px-3 py-1 capitalize"
              }
            >
              {v}
            </button>
          ))}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={220}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={55}
            outerRadius={85}
            paddingAngle={2}
            dataKey="value"
          >
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip content={<AllocationTooltip />} />
          <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: "0.75rem" }} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
