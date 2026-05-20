import { create } from "zustand";

export interface RawTick {
  type?: string;
  symbol?: string;
  price?: number;
  change24h?: number;
  seq?: number;
  ts?: string;
}

export interface PriceEntry {
  price: number;
  change24h: number | null;
  seq: number;
  ts: string;
}

interface PricesState {
  prices: Record<string, PriceEntry>;
  lastSeq: number;
  applyTicks: (ticks: RawTick[]) => void;
}

export const usePricesStore = create<PricesState>((set, get) => ({
  prices: {},
  lastSeq: 0,
  applyTicks: (ticks) => {
    const updates: Record<string, PriceEntry> = {};
    let maxSeq = get().lastSeq;
    for (const tick of ticks) {
      if (tick.type !== "price" || !tick.symbol || tick.price == null) continue;
      updates[tick.symbol] = {
        price: tick.price,
        change24h: tick.change24h ?? null,
        seq: tick.seq ?? 0,
        ts: tick.ts ?? new Date().toISOString(),
      };
      if ((tick.seq ?? 0) > maxSeq) maxSeq = tick.seq ?? 0;
    }
    if (Object.keys(updates).length === 0) return;
    set((s) => ({ prices: { ...s.prices, ...updates }, lastSeq: maxSeq }));
  },
}));
