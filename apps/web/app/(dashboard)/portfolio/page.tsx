"use client";

import { usePortfolioStore } from "@/store/portfolio";
import { usePortfolio, usePortfolioAllocation } from "@/hooks/usePortfolio";
import { PortfolioSelector } from "@/components/portfolio/PortfolioSelector";
import { SummaryCards } from "@/components/portfolio/SummaryCards";
import { AllocationChart } from "@/components/portfolio/AllocationChart";
import { PerformanceChart } from "@/components/portfolio/PerformanceChart";
import { HoldingsTable } from "@/components/portfolio/HoldingsTable";
import { AddTransactionModal } from "@/components/portfolio/AddTransactionModal";

export default function PortfolioPage() {
  const selectedId = usePortfolioStore((s) => s.selectedPortfolioId);
  const { data: portfolio, isLoading, isError } = usePortfolio(selectedId);
  const { data: allocation, isLoading: allocationLoading } = usePortfolioAllocation(
    selectedId ?? null
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Portfolio</h1>
          <p className="text-muted-foreground mt-0.5 text-sm">
            Track holdings, performance, and allocation
          </p>
        </div>
        <div className="flex items-center gap-2">
          <PortfolioSelector />
          {selectedId && <AddTransactionModal portfolioId={selectedId} holdings={portfolio?.holdings ?? []} />}
        </div>
      </div>

      {!selectedId && (
        <div className="text-muted-foreground flex h-64 items-center justify-center rounded-xl border border-dashed text-sm">
          Select or create a portfolio to get started
        </div>
      )}

      {selectedId && isLoading && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="bg-muted h-24 animate-pulse rounded-xl" />
          ))}
        </div>
      )}

      {selectedId && isError && (
        <div className="text-destructive flex h-32 items-center justify-center rounded-xl border text-sm">
          Failed to load portfolio data
        </div>
      )}

      {portfolio && (
        <>
          <SummaryCards portfolio={portfolio} />

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <PerformanceChart portfolioId={portfolio.id} />
            <AllocationChart
              allocation={allocation}
              holdings={portfolio.holdings}
              isLoading={allocationLoading}
            />
          </div>

          <HoldingsTable holdings={portfolio.holdings} portfolioName={portfolio.name} />
        </>
      )}
    </div>
  );
}
