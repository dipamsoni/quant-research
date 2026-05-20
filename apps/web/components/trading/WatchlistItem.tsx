"use client";

import { memo } from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { usePricesStore } from "@/store/prices";
import { useRemoveFromWatchlist } from "@/hooks/useWatchlist";
import type { WatchlistItem as WatchlistItemType } from "@/services/market";

interface WatchlistItemProps {
  item: WatchlistItemType;
  selected?: boolean;
  onSelect?: (symbol: string) => void;
}

const TYPE_DOT: Record<string, string> = {
  stock: "bg-blue-400",
  crypto: "bg-amber-400",
  etf: "bg-emerald-400",
  forex: "bg-violet-400",
};

export const WatchlistItem = memo(function WatchlistItem({ item, selected, onSelect }: WatchlistItemProps) {
  const entry = usePricesStore((s) => s.prices[item.symbol]);
  const remove = useRemoveFromWatchlist();

  const isPositive = entry?.change24h != null && entry.change24h >= 0;
  const isNegative = entry?.change24h != null && entry.change24h < 0;

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onSelect?.(item.symbol)}
      onKeyDown={(e) => e.key === "Enter" && onSelect?.(item.symbol)}
      className={cn(
        "group flex cursor-pointer items-center justify-between gap-2 rounded-md px-2 py-1.5 hover:bg-muted/50",
        selected && "bg-muted",
      )}
    >
      <div className="flex min-w-0 items-center gap-2">
        <span
          className={cn(
            "size-1.5 shrink-0 rounded-full",
            TYPE_DOT[item.asset_type] ?? "bg-muted-foreground"
          )}
        />
        <div className="min-w-0">
          <span className="font-mono text-sm font-semibold leading-none">{item.symbol}</span>
          <p className="text-muted-foreground truncate text-xs leading-none mt-0.5">{item.name}</p>
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-1">
        {entry ? (
          <div className="text-right">
            <p className="font-mono text-sm tabular-nums leading-none">
              ${entry.price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
            {entry.change24h != null && (
              <p
                className={cn(
                  "text-xs leading-none mt-0.5 tabular-nums",
                  isPositive && "text-green-400",
                  isNegative && "text-red-400"
                )}
              >
                {isPositive ? "+" : ""}
                {entry.change24h.toFixed(2)}%
              </p>
            )}
          </div>
        ) : (
          <span className="text-muted-foreground font-mono text-sm">—</span>
        )}
        <Button
          variant="ghost"
          size="icon-xs"
          className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive shrink-0"
          onClick={() => remove.mutate(item.symbol)}
          disabled={remove.isPending}
          aria-label={`Remove ${item.symbol}`}
        >
          <X />
        </Button>
      </div>
    </div>
  );
});
