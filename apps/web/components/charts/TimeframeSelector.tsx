"use client";

import { cn } from "@/lib/utils";
import type { Timeframe } from "@/services/market";

const TIMEFRAMES: Timeframe[] = ["1m", "5m", "1h", "1d", "1w"];

interface Props {
  value: Timeframe;
  onChange: (tf: Timeframe) => void;
}

export function TimeframeSelector({ value, onChange }: Props) {
  return (
    <div className="flex items-center gap-0.5 rounded-md border border-border bg-muted/30 p-0.5">
      {TIMEFRAMES.map((tf) => (
        <button
          key={tf}
          onClick={() => onChange(tf)}
          className={cn(
            "rounded px-2 py-0.5 font-mono text-xs transition-colors",
            value === tf
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground",
          )}
        >
          {tf}
        </button>
      ))}
    </div>
  );
}
