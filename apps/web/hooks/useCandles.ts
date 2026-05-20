"use client";

import { useQuery } from "@tanstack/react-query";
import { marketService } from "@/services/market";
import type { IndicatorKey, Timeframe } from "@/services/market";

export function useCandles(
  symbol: string | null,
  timeframe: Timeframe,
  indicators: IndicatorKey[],
) {
  const sortedIndicators = [...indicators].sort();
  return useQuery({
    queryKey: ["candles", symbol, timeframe, sortedIndicators],
    queryFn: () => marketService.getCandles(symbol!, timeframe, indicators),
    enabled: !!symbol,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}
