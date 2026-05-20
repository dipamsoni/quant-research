"use client";

import { useChartStore } from "@/store/chart";
import { useCandles } from "@/hooks/useCandles";
import { Watchlist } from "@/components/trading/Watchlist";
import { CandlestickChart } from "@/components/charts/CandlestickChart";
import { TimeframeSelector } from "@/components/charts/TimeframeSelector";
import { IndicatorPanel } from "@/components/charts/IndicatorPanel";
import { NewsPanel } from "@/components/market/NewsPanel";

export default function MarketsPage() {
  const selectedSymbol = useChartStore((s) => s.selectedSymbol);
  const timeframe = useChartStore((s) => s.timeframe);
  const activeIndicators = useChartStore((s) => s.activeIndicators);
  const setSelectedSymbol = useChartStore((s) => s.setSelectedSymbol);
  const setTimeframe = useChartStore((s) => s.setTimeframe);
  const toggleIndicator = useChartStore((s) => s.toggleIndicator);

  const { data: candles = [], isLoading, isError } = useCandles(
    selectedSymbol,
    timeframe,
    [...activeIndicators],
  );

  return (
    <div className="-m-6 flex h-[calc(100vh-3.5rem)] overflow-hidden">
      <aside className="border-border w-72 shrink-0 border-r">
        <Watchlist
          selectedSymbol={selectedSymbol}
          onSelectSymbol={setSelectedSymbol}
        />
      </aside>

      <main className="flex flex-1 flex-col overflow-hidden">
        {selectedSymbol ? (
          <>
            <div className="border-border flex flex-wrap items-center gap-3 border-b px-4 py-2">
              <span className="font-mono text-sm font-semibold">
                {selectedSymbol}
              </span>
              <TimeframeSelector value={timeframe} onChange={setTimeframe} />
              <IndicatorPanel active={activeIndicators} onToggle={toggleIndicator} />
            </div>

            <div className="min-h-0 flex-1 overflow-y-auto p-4">
              <CandlestickChart
                candles={candles}
                activeIndicators={activeIndicators}
                isLoading={isLoading}
                isError={isError}
              />
            </div>

            <NewsPanel symbol={selectedSymbol} />
          </>
        ) : (
          <div className="flex flex-1 items-center justify-center">
            <p className="text-muted-foreground text-sm">
              Select a symbol from the watchlist to view the chart
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
