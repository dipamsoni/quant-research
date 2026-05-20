"use client";

import { useQuery } from "@tanstack/react-query";
import { marketService } from "@/services/market";

export function useAssetSearch(query: string) {
  return useQuery({
    queryKey: ["assets", "search", query],
    queryFn: () => marketService.searchAssets(query),
    enabled: query.trim().length >= 1,
    staleTime: 30 * 1000,
  });
}
