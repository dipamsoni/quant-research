"use client";

import { usePortfolios, useCreatePortfolio } from "@/hooks/usePortfolio";
import { usePortfolioStore } from "@/store/portfolio";
import { Button } from "@/components/ui/button";
import { ChevronDownIcon, PlusIcon } from "lucide-react";
import { useState, useRef, useEffect } from "react";

export function PortfolioSelector() {
  const { data: portfolios = [], isLoading } = usePortfolios();
  const selectedId = usePortfolioStore((s) => s.selectedPortfolioId);
  const setSelectedId = usePortfolioStore((s) => s.setSelectedPortfolioId);
  const createPortfolio = useCreatePortfolio();
  const [open, setOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const dropdownRef = useRef<HTMLDivElement>(null);

  const selected = portfolios.find((p) => p.id === selectedId);

  useEffect(() => {
    if (!selectedId && portfolios.length > 0) {
      setSelectedId(portfolios[0].id);
    }
  }, [portfolios, selectedId, setSelectedId]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  async function handleCreate() {
    if (!newName.trim()) return;
    const portfolio = await createPortfolio.mutateAsync({ name: newName.trim() });
    setSelectedId(portfolio.id);
    setNewName("");
    setCreating(false);
    setOpen(false);
  }

  if (isLoading) {
    return <div className="bg-muted h-8 w-48 animate-pulse rounded-lg" />;
  }

  return (
    <div ref={dropdownRef} className="relative">
      <Button
        variant="outline"
        className="min-w-48 justify-between gap-2"
        onClick={() => setOpen((o) => !o)}
      >
        <span className="truncate">{selected?.name ?? "Select portfolio"}</span>
        <ChevronDownIcon className="size-4 shrink-0 opacity-60" />
      </Button>

      {open && (
        <div className="bg-popover border-border absolute left-0 top-full z-50 mt-1 w-64 rounded-xl border shadow-lg">
          <div className="max-h-56 overflow-y-auto p-1">
            {portfolios.length === 0 && (
              <p className="text-muted-foreground px-3 py-2 text-sm">No portfolios yet</p>
            )}
            {portfolios.map((p) => (
              <button
                key={p.id}
                className="hover:bg-muted w-full rounded-lg px-3 py-2 text-left text-sm"
                onClick={() => {
                  setSelectedId(p.id);
                  setOpen(false);
                }}
              >
                <span className="font-medium">{p.name}</span>
                <span className="text-muted-foreground ml-2 text-xs">{p.base_currency}</span>
              </button>
            ))}
          </div>

          <div className="border-border border-t p-2">
            {creating ? (
              <div className="flex gap-1">
                <input
                  autoFocus
                  className="border-input bg-background h-7 flex-1 rounded-md border px-2 text-sm"
                  placeholder="Portfolio name"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleCreate();
                    if (e.key === "Escape") setCreating(false);
                  }}
                />
                <Button size="sm" onClick={handleCreate} disabled={createPortfolio.isPending}>
                  Add
                </Button>
              </div>
            ) : (
              <button
                className="text-muted-foreground hover:text-foreground flex w-full items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm"
                onClick={() => setCreating(true)}
              >
                <PlusIcon className="size-4" />
                New portfolio
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
