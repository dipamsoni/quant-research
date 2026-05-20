"use client";

import { cn } from "@/lib/utils";
import type { IndicatorKey } from "@/services/market";

interface IndicatorMeta {
  key: IndicatorKey;
  label: string;
  color: string;
}

const INDICATORS: IndicatorMeta[] = [
  { key: "sma_20", label: "SMA 20", color: "#f59e0b" },
  { key: "ema_50", label: "EMA 50", color: "#60a5fa" },
  { key: "bbands_20_2", label: "BB 20,2", color: "#a78bfa" },
  { key: "rsi_14", label: "RSI 14", color: "#a78bfa" },
  { key: "macd_12_26_9", label: "MACD", color: "#60a5fa" },
];

interface Props {
  active: Set<IndicatorKey>;
  onToggle: (key: IndicatorKey) => void;
}

export function IndicatorPanel({ active, onToggle }: Props) {
  return (
    <div className="flex items-center gap-1 flex-wrap">
      {INDICATORS.map(({ key, label, color }) => {
        const on = active.has(key);
        return (
          <button
            key={key}
            onClick={() => onToggle(key)}
            className={cn(
              "flex items-center gap-1 rounded border px-1.5 py-0.5 text-xs transition-colors",
              on
                ? "border-transparent bg-muted text-foreground"
                : "border-border text-muted-foreground hover:text-foreground",
            )}
          >
            <span
              className="size-1.5 shrink-0 rounded-full"
              style={{ backgroundColor: on ? color : "currentColor" }}
            />
            {label}
          </button>
        );
      })}
    </div>
  );
}
