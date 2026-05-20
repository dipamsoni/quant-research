"use client";

import { useCallback, useMemo, useRef } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { ListX } from "lucide-react";
import { useWatchlist, useAddToWatchlist } from "@/hooks/useWatchlist";
import { usePrices } from "@/hooks/usePrices";
import { SymbolSearch } from "./SymbolSearch";
import { WatchlistItem } from "./WatchlistItem";
import type { AssetResult } from "@/services/market";

interface WatchlistProps {
  selectedSymbol?: string | null;
  onSelectSymbol?: (symbol: string) => void;
}

export function Watchlist({ selectedSymbol, onSelectSymbol }: WatchlistProps) {
  const { data: items = [], isLoading } = useWatchlist();
  const addMutation = useAddToWatchlist();
  const scrollRef = useRef<HTMLDivElement>(null);

  const symbols = useMemo(() => items.map((i) => i.symbol), [items]);
  usePrices(symbols);

  const handleSelect = useCallback(
    (asset: AssetResult) => {
      addMutation.mutate(asset.symbol);
    },
    [addMutation],
  );

  const handleSelectSymbol = useCallback(
    (symbol: string) => {
      onSelectSymbol?.(symbol);
    },
    [onSelectSymbol],
  );

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => 48,
    overscan: 5,
  });

  return (
    <div className="flex h-full flex-col">
      <div className="border-border border-b px-3 py-3">
        <h2 className="text-sm font-semibold tracking-tight mb-2">Watchlist</h2>
        <SymbolSearch onSelect={handleSelect} />
        {addMutation.isError && (
          <p className="text-destructive mt-1 text-xs">
            {addMutation.error instanceof Error
              ? addMutation.error.message
              : "Failed to add symbol"}
          </p>
        )}
      </div>
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-1 py-1">
        {isLoading && (
          <div className="text-muted-foreground px-2 py-8 text-center text-sm">
            Loading…
          </div>
        )}
        {!isLoading && items.length === 0 && (
          <div className="text-muted-foreground flex flex-col items-center gap-2 px-2 py-8 text-center">
            <ListX className="size-8 opacity-40" />
            <p className="text-sm">No symbols yet</p>
            <p className="text-xs opacity-60">Search above to add</p>
          </div>
        )}
        {!isLoading && items.length > 0 && (
          <div
            style={{ height: `${virtualizer.getTotalSize()}px`, position: "relative" }}
          >
            {virtualizer.getVirtualItems().map((virtualRow) => {
              const item = items[virtualRow.index];
              return (
                <div
                  key={item.id}
                  style={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    right: 0,
                    transform: `translateY(${virtualRow.start}px)`,
                  }}
                  data-index={virtualRow.index}
                  ref={virtualizer.measureElement}
                >
                  <WatchlistItem
                    item={item}
                    selected={selectedSymbol === item.symbol}
                    onSelect={handleSelectSymbol}
                  />
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
