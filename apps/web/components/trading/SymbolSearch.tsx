"use client";

import { useEffect, useRef, useState } from "react";
import { Search } from "lucide-react";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import { useAssetSearch } from "@/hooks/useAssetSearch";
import type { AssetResult } from "@/services/market";

interface SymbolSearchProps {
  onSelect: (asset: AssetResult) => void;
  placeholder?: string;
  className?: string;
}

const TYPE_BADGE: Record<string, string> = {
  stock: "bg-blue-500/15 text-blue-400",
  crypto: "bg-amber-500/15 text-amber-400",
  etf: "bg-emerald-500/15 text-emerald-400",
  forex: "bg-violet-500/15 text-violet-400",
};

export function SymbolSearch({
  onSelect,
  placeholder = "Add symbol…",
  className,
}: SymbolSearchProps) {
  const [query, setQuery] = useState("");
  const [debounced, setDebounced] = useState("");
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const t = setTimeout(() => setDebounced(query), 250);
    return () => clearTimeout(t);
  }, [query]);

  const { data: results = [], isFetching } = useAssetSearch(debounced);

  useEffect(() => {
    setOpen(debounced.trim().length >= 1);
  }, [debounced]);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  function handleSelect(asset: AssetResult) {
    onSelect(asset);
    setQuery("");
    setDebounced("");
    setOpen(false);
  }

  return (
    <div ref={containerRef} className={cn("relative", className)}>
      <div className="relative">
        <Search className="text-muted-foreground absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2" />
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder}
          className="pl-8"
          onFocus={() => debounced.trim().length >= 1 && setOpen(true)}
        />
      </div>
      {open && (
        <ul className="bg-popover border-border absolute left-0 right-0 top-full z-50 mt-1 max-h-64 overflow-y-auto rounded-lg border shadow-lg">
          {isFetching && results.length === 0 && (
            <li className="text-muted-foreground px-3 py-2 text-sm">Searching…</li>
          )}
          {!isFetching && results.length === 0 && debounced.trim().length >= 1 && (
            <li className="text-muted-foreground px-3 py-2 text-sm">No results</li>
          )}
          {results.map((asset) => (
            <li key={asset.id}>
              <button
                type="button"
                className="hover:bg-accent flex w-full items-center gap-2 px-3 py-2 text-left text-sm"
                onMouseDown={(e) => {
                  e.preventDefault();
                  handleSelect(asset);
                }}
              >
                <span className="font-mono font-semibold">{asset.symbol}</span>
                <span className="text-muted-foreground min-w-0 flex-1 truncate">{asset.name}</span>
                <span
                  className={cn(
                    "rounded px-1.5 py-0.5 text-xs font-medium",
                    TYPE_BADGE[asset.asset_type] ?? "bg-muted text-muted-foreground"
                  )}
                >
                  {asset.asset_type}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
