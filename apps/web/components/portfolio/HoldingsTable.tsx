"use client";

import { useMemo, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type SortingState,
} from "@tanstack/react-table";
import { useVirtualizer } from "@tanstack/react-virtual";
import { useState } from "react";
import { DownloadIcon, ArrowUpIcon, ArrowDownIcon, ArrowUpDownIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Holding } from "@/services/portfolio";
import { usePricesStore } from "@/store/prices";
import { useChartStore } from "@/store/chart";

interface HoldingRow extends Holding {
  current_price: number;
  day_change: number | null;
  unrealized_pnl: number;
  market_value_live: number;
}

interface HoldingsTableProps {
  holdings: Holding[];
  portfolioName: string;
}

function fmt(n: number | null | undefined, prefix = ""): string {
  if (n == null || isNaN(n)) return "—";
  return `${prefix}${n.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function SortIcon({ sorted }: { sorted: false | "asc" | "desc" }) {
  if (sorted === "asc") return <ArrowUpIcon className="size-3" />;
  if (sorted === "desc") return <ArrowDownIcon className="size-3" />;
  return <ArrowUpDownIcon className="size-3 opacity-40" />;
}

const col = createColumnHelper<HoldingRow>();

const columns = [
  col.accessor("symbol", {
    header: "Symbol",
    enableSorting: true,
    cell: (info) => (
      <span className="font-mono text-xs font-semibold">{info.getValue()}</span>
    ),
  }),
  col.accessor((row) => parseFloat(row.quantity), {
    id: "quantity",
    header: "Qty",
    enableSorting: true,
    cell: (info) => fmt(info.getValue()),
  }),
  col.accessor((row) => parseFloat(row.avg_price), {
    id: "avg_price",
    header: "Avg Price (₹)",
    enableSorting: true,
    cell: (info) => fmt(info.getValue(), "₹"),
  }),
  col.accessor("current_price", {
    header: "Current Price (₹)",
    enableSorting: true,
    cell: (info) => fmt(info.getValue(), "₹"),
  }),
  col.accessor("market_value_live", {
    header: "Market Value (₹)",
    enableSorting: true,
    cell: (info) => fmt(info.getValue(), "₹"),
  }),
  col.accessor("unrealized_pnl", {
    header: "Unrealized P&L",
    enableSorting: true,
    cell: ({ getValue, row }) => {
      const pnl = getValue();
      const avg = parseFloat(row.original.avg_price);
      const qty = parseFloat(row.original.quantity);
      const costBasis = avg * qty;
      const pct = costBasis > 0 ? (pnl / costBasis) * 100 : 0;
      const color = pnl >= 0 ? "text-emerald-500" : "text-red-500";
      return (
        <span className={color}>
          {pnl >= 0 ? "+" : "−"}₹{Math.abs(pnl).toLocaleString("en-IN", { maximumFractionDigits: 0 })}{" "}
          ({pct >= 0 ? "+" : ""}{pct.toFixed(2)}%)
        </span>
      );
    },
  }),
  col.accessor("day_change", {
    header: "Day Change %",
    enableSorting: true,
    sortingFn: (a, b) => {
      const va = a.original.day_change ?? -Infinity;
      const vb = b.original.day_change ?? -Infinity;
      return va - vb;
    },
    cell: (info) => {
      const v = info.getValue();
      if (v == null) return <span className="text-muted-foreground">—</span>;
      const color = v >= 0 ? "text-emerald-500" : "text-red-500";
      return (
        <span className={color}>
          {v >= 0 ? "+" : ""}{v.toFixed(2)}%
        </span>
      );
    },
  }),
];

export function HoldingsTable({ holdings, portfolioName }: HoldingsTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const tableContainerRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const prices = usePricesStore((s) => s.prices);
  const setSelectedSymbol = useChartStore((s) => s.setSelectedSymbol);

  const data = useMemo<HoldingRow[]>(() =>
    holdings.map((h) => {
      const p = prices[h.symbol];
      const currentPrice = p?.price ?? parseFloat(h.avg_price);
      const qty = parseFloat(h.quantity);
      const avg = parseFloat(h.avg_price);
      const mv = currentPrice * qty;
      const pnl = mv - avg * qty;
      return {
        ...h,
        current_price: currentPrice,
        day_change: p?.change24h ?? null,
        unrealized_pnl: pnl,
        market_value_live: mv,
      };
    }),
    [holdings, prices]
  );

  const handleRowClick = useCallback((symbol: string) => {
    setSelectedSymbol(symbol);
    router.push("/markets");
  }, [setSelectedSymbol, router]);

  function exportCsv() {
    const date = new Date().toISOString().split("T")[0];
    const header = [
      "Symbol", "Quantity", "Avg Price", "Current Price",
      "Market Value", "Unrealized PnL", "Unrealized PnL %",
    ];
    const rows = data.map((h) => {
      const costBasis = parseFloat(h.avg_price) * parseFloat(h.quantity);
      const pct = costBasis > 0 ? (h.unrealized_pnl / costBasis) * 100 : 0;
      return [
        h.symbol,
        h.quantity,
        parseFloat(h.avg_price).toFixed(2),
        h.current_price.toFixed(2),
        h.market_value_live.toFixed(2),
        h.unrealized_pnl.toFixed(2),
        pct.toFixed(2),
      ].join(",");
    });
    const csv = [header.join(","), ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `portfolio-${portfolioName}-${date}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const table = useReactTable({
    data,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  const { rows } = table.getRowModel();

  const virtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => tableContainerRef.current,
    estimateSize: () => 40,
    overscan: 10,
  });

  const virtualItems = virtualizer.getVirtualItems();
  const totalSize = virtualizer.getTotalSize();

  return (
    <div className="bg-card border-border rounded-xl border">
      <div className="flex items-center justify-between px-4 py-3">
        <h3 className="text-sm font-semibold">Holdings</h3>
        <Button
          variant="ghost"
          size="sm"
          onClick={exportCsv}
          disabled={holdings.length === 0}
        >
          <DownloadIcon className="mr-1.5 size-3.5" />
          Export CSV
        </Button>
      </div>

      {holdings.length === 0 ? (
        <div className="flex h-32 items-center justify-center">
          <p className="text-muted-foreground text-sm">
            No holdings. Add a transaction to get started.
          </p>
        </div>
      ) : (
        <div
          ref={tableContainerRef}
          className="overflow-auto"
          style={{ maxHeight: 400 }}
        >
          <table className="w-full text-sm">
            <thead className="bg-muted/50 sticky top-0 z-10">
              {table.getHeaderGroups().map((hg) => (
                <tr key={hg.id}>
                  {hg.headers.map((header) => (
                    <th
                      key={header.id}
                      className="text-muted-foreground select-none px-4 py-2 text-left text-xs font-medium"
                      onClick={header.column.getToggleSortingHandler()}
                      style={{ cursor: header.column.getCanSort() ? "pointer" : "default" }}
                    >
                      <span className="flex items-center gap-1">
                        {flexRender(header.column.columnDef.header, header.getContext())}
                        {header.column.getCanSort() && (
                          <SortIcon sorted={header.column.getIsSorted()} />
                        )}
                      </span>
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody>
              <tr style={{ height: virtualItems[0]?.start ?? 0 }} />
              {virtualItems.map((vi) => {
                const row = rows[vi.index];
                return (
                  <tr
                    key={row.id}
                    data-index={vi.index}
                    className="border-border hover:bg-muted/30 cursor-pointer border-t"
                    onClick={() => handleRowClick(row.original.symbol)}
                  >
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id} className="px-4 py-2 font-mono text-xs">
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </tr>
                );
              })}
              <tr style={{ height: totalSize - (virtualItems.at(-1)?.end ?? 0) }} />
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
