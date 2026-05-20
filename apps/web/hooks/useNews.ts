"use client";

import { useQuery } from "@tanstack/react-query";
import { marketService } from "@/services/market";

export function useNews(symbol: string | null) {
  return useQuery({
    queryKey: ["news", symbol],
    queryFn: () => marketService.getNews(symbol!),
    enabled: !!symbol,
    staleTime: 60_000,
    refetchInterval: 600_000,
    refetchOnWindowFocus: false,
  });
}
