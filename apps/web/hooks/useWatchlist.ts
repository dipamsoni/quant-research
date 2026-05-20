"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { marketService } from "@/services/market";

export function useWatchlist() {
  return useQuery({
    queryKey: ["watchlist"],
    queryFn: marketService.getWatchlist,
    staleTime: 5 * 60 * 1000,
  });
}

export function useAddToWatchlist() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (symbol: string) => marketService.addToWatchlist(symbol),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["watchlist"] }),
  });
}

export function useRemoveFromWatchlist() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (symbol: string) => marketService.removeFromWatchlist(symbol),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["watchlist"] }),
  });
}
