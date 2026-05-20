"use client";

import { useEffect, useRef } from "react";
import { useAuthStore } from "@/store/auth";
import { usePricesStore, type RawTick } from "@/store/prices";

const WS_BASE =
  process.env.NEXT_PUBLIC_MARKET_DATA_WS_URL ?? "ws://localhost:8001";
const MAX_BACKOFF_MS = 30_000;

export function usePrices(symbols: string[]) {
  const token = useAuthStore((s) => s.accessToken);
  const applyTicks = usePricesStore((s) => s.applyTicks);
  const lastSeq = usePricesStore((s) => s.lastSeq);

  const symbolsKey = symbols.join(",");
  const tokenRef = useRef(token);
  const lastSeqRef = useRef(lastSeq);
  const applyTicksRef = useRef(applyTicks);

  tokenRef.current = token;
  lastSeqRef.current = lastSeq;
  applyTicksRef.current = applyTicks;

  useEffect(() => {
    if (!token || symbols.length === 0) return;

    let ws: WebSocket | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;
    let flushTimer: ReturnType<typeof setTimeout> | null = null;
    let backoff = 1_000;
    let stopped = false;
    const buffer: RawTick[] = [];

    function flush() {
      flushTimer = null;
      if (buffer.length > 0) {
        applyTicksRef.current(buffer.splice(0));
      }
    }

    function connect() {
      if (stopped) return;
      const url = `${WS_BASE}/ws/prices?symbols=${symbolsKey}&token=${tokenRef.current}&seq=${lastSeqRef.current}`;
      ws = new WebSocket(url);

      ws.onopen = () => {
        backoff = 1_000;
      };

      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data as string) as RawTick;
          if (msg.type === "ping") {
            ws?.send(JSON.stringify({ type: "pong" }));
            return;
          }
          buffer.push(msg);
          if (flushTimer == null) {
            flushTimer = setTimeout(flush, 100);
          }
        } catch {
          // malformed frame — ignore
        }
      };

      // onerror always fires before onclose on network failures.
      // Only schedule reconnect in onclose so we don't fire twice.
      ws.onerror = () => {
        // intentionally empty — onclose will follow and handle reconnect
      };

      ws.onclose = () => {
        ws = null;
        if (stopped) return;
        const jitter = Math.random() * 1_000 - 500; // ±500 ms
        retryTimer = setTimeout(() => {
          backoff = Math.min(backoff * 2, MAX_BACKOFF_MS);
          connect();
        }, Math.max(0, backoff + jitter));
      };
    }

    connect();

    return () => {
      stopped = true;
      ws?.close();
      ws = null;
      if (retryTimer != null) clearTimeout(retryTimer);
      if (flushTimer != null) clearTimeout(flushTimer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, symbolsKey]);
}
