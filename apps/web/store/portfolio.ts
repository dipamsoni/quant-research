import { create } from "zustand";
import { persist } from "zustand/middleware";

interface PortfolioState {
  selectedPortfolioId: string | null;
  setSelectedPortfolioId: (id: string | null) => void;
}

export const usePortfolioStore = create<PortfolioState>()(
  persist(
    (set) => ({
      selectedPortfolioId: null,
      setSelectedPortfolioId: (id) => set({ selectedPortfolioId: id }),
    }),
    { name: "quant-os-portfolio" }
  )
);
