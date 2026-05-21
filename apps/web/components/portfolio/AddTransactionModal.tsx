"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { SymbolSearch } from "@/components/trading/SymbolSearch";
import { useAddTransaction } from "@/hooks/usePortfolio";
import type { AssetResult } from "@/services/market";
import type { Holding } from "@/services/portfolio";
import { PlusIcon, XIcon } from "lucide-react";
import { useState } from "react";

const schema = z.object({
  asset_id: z.string().uuid("Select a valid symbol"),
  symbol: z.string().min(1, "Required"),
  transaction_type: z.enum(["buy", "sell"]),
  quantity: z.string().regex(/^\d+(\.\d+)?$/, "Must be a positive number"),
  price: z.string().regex(/^\d+(\.\d+)?$/, "Must be a positive number"),
  fees: z.string().regex(/^\d*(\.\d+)?$/, "Must be a non-negative number").optional(),
  executed_at: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

interface AddTransactionModalProps {
  portfolioId: string;
  holdings: Holding[];
}

export function AddTransactionModal({ portfolioId, holdings }: AddTransactionModalProps) {
  const [open, setOpen] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState<AssetResult | null>(null);
  const addTx = useAddTransaction(portfolioId);

  const today = new Date().toISOString().split("T")[0];

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { transaction_type: "buy", fees: "0", executed_at: today },
  });

  const txType = watch("transaction_type");

  function handleAssetSelect(asset: AssetResult) {
    setSelectedAsset(asset);
    setValue("asset_id", asset.id, { shouldValidate: true });
    setValue("symbol", asset.symbol, { shouldValidate: true });
  }

  function handleClose() {
    reset({ transaction_type: "buy", fees: "0", executed_at: today });
    setSelectedAsset(null);
    setOpen(false);
  }

  async function onSubmit(values: FormValues) {
    if (values.transaction_type === "sell") {
      const holding = holdings.find((h) => h.symbol === values.symbol);
      const maxQty = holding ? parseFloat(holding.quantity) : 0;
      if (parseFloat(values.quantity) > maxQty) {
        setError("quantity", {
          message: `Max sellable: ${maxQty} shares`,
        });
        return;
      }
    }

    await addTx.mutateAsync({
      asset_id: values.asset_id,
      symbol: values.symbol,
      transaction_type: values.transaction_type,
      quantity: values.quantity,
      price: values.price,
      fees: values.fees ?? "0",
      executed_at: values.executed_at
        ? new Date(values.executed_at).toISOString()
        : undefined,
    });
    handleClose();
  }

  return (
    <>
      <Button onClick={() => setOpen(true)}>
        <PlusIcon className="mr-1.5 size-4" />
        Add Transaction
      </Button>

      <Dialog open={open} onOpenChange={(o) => { if (!o) handleClose(); else setOpen(true); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Transaction</DialogTitle>
          </DialogHeader>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* hidden fields for RHF validation */}
            <input type="hidden" {...register("asset_id")} />
            <input type="hidden" {...register("symbol")} />

            <div className="grid grid-cols-2 gap-3">
              {/* Symbol search */}
              <div className="col-span-2 space-y-1">
                <Label>Symbol</Label>
                {selectedAsset ? (
                  <div className="border-border flex items-center gap-2 rounded-md border px-3 py-2">
                    <span className="font-mono text-sm font-semibold">{selectedAsset.symbol}</span>
                    <span className="text-muted-foreground min-w-0 flex-1 truncate text-sm">
                      {selectedAsset.name}
                    </span>
                    <button
                      type="button"
                      className="text-muted-foreground hover:text-foreground ml-auto shrink-0"
                      onClick={() => {
                        setSelectedAsset(null);
                        setValue("asset_id", "");
                        setValue("symbol", "");
                      }}
                      aria-label="Clear symbol"
                    >
                      <XIcon className="size-3.5" />
                    </button>
                  </div>
                ) : (
                  <SymbolSearch
                    onSelect={handleAssetSelect}
                    placeholder="Search symbol…"
                  />
                )}
                {errors.asset_id && (
                  <p className="text-destructive text-xs">{errors.asset_id.message}</p>
                )}
              </div>

              {/* Buy / Sell */}
              <div className="col-span-2 space-y-1">
                <Label>Type</Label>
                <div className="flex gap-4">
                  {(["buy", "sell"] as const).map((t) => (
                    <label key={t} className="flex cursor-pointer items-center gap-1.5 text-sm">
                      <input
                        type="radio"
                        value={t}
                        {...register("transaction_type")}
                        className="accent-primary"
                      />
                      <span className="capitalize">{t}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Quantity */}
              <div className="space-y-1">
                <Label htmlFor="quantity">Quantity</Label>
                <Input
                  id="quantity"
                  placeholder="10"
                  {...register("quantity")}
                  aria-invalid={!!errors.quantity}
                />
                {errors.quantity && (
                  <p className="text-destructive text-xs">{errors.quantity.message}</p>
                )}
                {txType === "sell" && selectedAsset && (() => {
                  const h = holdings.find((h) => h.symbol === selectedAsset.symbol);
                  return h ? (
                    <p className="text-muted-foreground text-xs">
                      Holding: {parseFloat(h.quantity).toLocaleString("en-IN")} shares
                    </p>
                  ) : (
                    <p className="text-amber-500 text-xs">No holding for this symbol</p>
                  );
                })()}
              </div>

              {/* Price */}
              <div className="space-y-1">
                <Label htmlFor="price">Price (₹)</Label>
                <Input
                  id="price"
                  placeholder="1500.00"
                  {...register("price")}
                  aria-invalid={!!errors.price}
                />
                {errors.price && (
                  <p className="text-destructive text-xs">{errors.price.message}</p>
                )}
              </div>

              {/* Fees */}
              <div className="space-y-1">
                <Label htmlFor="fees">Fees (₹)</Label>
                <Input
                  id="fees"
                  placeholder="0"
                  {...register("fees")}
                  aria-invalid={!!errors.fees}
                />
                {errors.fees && (
                  <p className="text-destructive text-xs">{errors.fees.message}</p>
                )}
              </div>

              {/* Date */}
              <div className="space-y-1">
                <Label htmlFor="executed_at">Date</Label>
                <Input
                  id="executed_at"
                  type="date"
                  {...register("executed_at")}
                  aria-invalid={!!errors.executed_at}
                />
                {errors.executed_at && (
                  <p className="text-destructive text-xs">{errors.executed_at.message}</p>
                )}
              </div>
            </div>

            {addTx.isError && (
              <p className="text-destructive text-sm">
                {addTx.error instanceof Error ? addTx.error.message : "Transaction failed"}
              </p>
            )}

            <DialogFooter>
              <Button type="button" variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting || addTx.isPending}>
                {addTx.isPending ? "Adding…" : "Add Transaction"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
}
