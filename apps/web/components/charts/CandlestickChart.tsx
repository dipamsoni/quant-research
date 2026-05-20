"use client";

import dynamic from "next/dynamic";
import type { Candle, IndicatorKey } from "@/services/market";

export interface CandlestickChartProps {
  candles: Candle[];
  activeIndicators: Set<IndicatorKey>;
  isLoading?: boolean;
  isError?: boolean;
}

const CandlestickChartImpl = dynamic(() => import("./CandlestickChartImpl"), {
  ssr: false,
  loading: () => (
    <div className="flex h-[400px] w-full items-center justify-center">
      <span className="text-muted-foreground text-sm animate-pulse">
        Loading chart…
      </span>
    </div>
  ),
});

export function CandlestickChart({
  candles,
  activeIndicators,
  isLoading,
  isError,
}: CandlestickChartProps) {
  if (isLoading) {
    return (
      <div className="flex h-[400px] w-full items-center justify-center">
        <span className="text-muted-foreground text-sm animate-pulse">
          Fetching candles…
        </span>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex h-[400px] w-full items-center justify-center">
        <span className="text-destructive text-sm">
          Failed to load chart data.
        </span>
      </div>
    );
  }

  if (!candles.length) {
    return (
      <div className="flex h-[400px] w-full items-center justify-center">
        <span className="text-muted-foreground text-sm">No candle data.</span>
      </div>
    );
  }

  return (
    <CandlestickChartImpl candles={candles} activeIndicators={activeIndicators} />
  );
}
