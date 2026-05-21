"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { portfolioService, type TransactionCreate, type PortfolioCreate } from "@/services/portfolio";
import { marketDataService } from "@/services/marketData";

export function usePortfolios() {
  return useQuery({
    queryKey: ["portfolios"],
    queryFn: () => portfolioService.list(),
    staleTime: 60_000,
  });
}

export function usePortfolio(id: string | null) {
  return useQuery({
    queryKey: ["portfolio", id],
    queryFn: () => portfolioService.get(id!),
    enabled: !!id,
    staleTime: 30_000,
  });
}

export function usePortfolioMetrics(id: string | null, from?: string, to?: string) {
  return useQuery({
    queryKey: ["portfolio-metrics", id, from, to],
    queryFn: () => portfolioService.getMetrics(id!, from, to),
    enabled: !!id,
    staleTime: 60_000,
  });
}

export function usePortfolioAllocation(id: string | null) {
  return useQuery({
    queryKey: ["portfolio-allocation", id],
    queryFn: () => portfolioService.getAllocation(id!),
    enabled: !!id,
    staleTime: 30_000,
  });
}

export function useAddTransaction(portfolioId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: TransactionCreate) =>
      portfolioService.addTransaction(portfolioId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["portfolio", portfolioId] });
      qc.invalidateQueries({ queryKey: ["portfolio-allocation", portfolioId] });
    },
  });
}

export function useCreatePortfolio() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: PortfolioCreate) => portfolioService.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["portfolios"] });
    },
  });
}

export function useNiftyBenchmark(from?: string, to?: string) {
  return useQuery({
    queryKey: ["nifty-benchmark", from, to],
    queryFn: () => marketDataService.getNiftyCandles(from, to),
    staleTime: 5 * 60_000,
  });
}
