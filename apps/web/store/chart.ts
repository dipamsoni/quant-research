import { create } from "zustand";
import type { IndicatorKey, Timeframe } from "@/services/market";

interface ChartState {
  selectedSymbol: string | null;
  timeframe: Timeframe;
  activeIndicators: Set<IndicatorKey>;
  setSelectedSymbol: (symbol: string | null) => void;
  setTimeframe: (tf: Timeframe) => void;
  toggleIndicator: (key: IndicatorKey) => void;
}

export const useChartStore = create<ChartState>((set) => ({
  selectedSymbol: null,
  timeframe: "1d",
  activeIndicators: new Set<IndicatorKey>(),
  setSelectedSymbol: (symbol) => set({ selectedSymbol: symbol }),
  setTimeframe: (timeframe) => set({ timeframe }),
  toggleIndicator: (key) =>
    set((s) => {
      const next = new Set(s.activeIndicators);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return { activeIndicators: next };
    }),
}));
