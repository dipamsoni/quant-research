"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import {
  createChart,
  ColorType,
  CrosshairMode,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
  type LogicalRange,
} from "lightweight-charts";
import type { Candle, IndicatorKey } from "@/services/market";

interface TooltipData {
  x: number;
  y: number;
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface Props {
  candles: Candle[];
  activeIndicators: Set<IndicatorKey>;
}

const CHART_THEME = {
  background: "#0c0e14",
  text: "#9ca3af",
  grid: "#1a1d27",
  border: "#2d3148",
  up: "#22c55e",
  down: "#ef4444",
  upDim: "#22c55e33",
  downDim: "#ef444433",
};

function toTs(isoTime: string): UTCTimestamp {
  return Math.floor(new Date(isoTime).getTime() / 1000) as UTCTimestamp;
}

function fmtPrice(v: number) {
  return v.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function fmtVol(v: number) {
  if (v >= 1_000_000_000) return (v / 1_000_000_000).toFixed(2) + "B";
  if (v >= 1_000_000) return (v / 1_000_000).toFixed(2) + "M";
  if (v >= 1_000) return (v / 1_000).toFixed(1) + "K";
  return v.toFixed(0);
}

const CHART_OPTS = (width: number) =>
  ({
    width,
    height: 400,
    layout: {
      background: { type: ColorType.Solid, color: CHART_THEME.background },
      textColor: CHART_THEME.text,
      fontFamily: "'Inter', 'Geist', monospace",
    },
    grid: {
      vertLines: { color: CHART_THEME.grid },
      horzLines: { color: CHART_THEME.grid },
    },
    crosshair: { mode: CrosshairMode.Normal },
    rightPriceScale: { borderColor: CHART_THEME.border },
    timeScale: {
      borderColor: CHART_THEME.border,
      timeVisible: true,
      secondsVisible: false,
    },
  }) as const;

const SUB_CHART_OPTS = (width: number, height: number) =>
  ({
    width,
    height,
    layout: {
      background: { type: ColorType.Solid, color: CHART_THEME.background },
      textColor: CHART_THEME.text,
      fontFamily: "'Inter', 'Geist', monospace",
    },
    grid: {
      vertLines: { color: CHART_THEME.grid },
      horzLines: { color: CHART_THEME.grid },
    },
    crosshair: { mode: CrosshairMode.Normal },
    rightPriceScale: { borderColor: CHART_THEME.border },
    timeScale: {
      borderColor: CHART_THEME.border,
      timeVisible: true,
      secondsVisible: false,
    },
  }) as const;

export default function CandlestickChartImpl({ candles, activeIndicators }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const rsiContainerRef = useRef<HTMLDivElement>(null);
  const macdContainerRef = useRef<HTMLDivElement>(null);

  const mainChartRef = useRef<IChartApi | null>(null);
  const rsiChartRef = useRef<IChartApi | null>(null);
  const macdChartRef = useRef<IChartApi | null>(null);

  // Main pane series
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const smaSeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const emaSeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const bbUpperRef = useRef<ISeriesApi<"Line"> | null>(null);
  const bbMidRef = useRef<ISeriesApi<"Line"> | null>(null);
  const bbLowerRef = useRef<ISeriesApi<"Line"> | null>(null);

  // Sub-pane series
  const rsiSeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const macdLineRef = useRef<ISeriesApi<"Line"> | null>(null);
  const macdSignalRef = useRef<ISeriesApi<"Line"> | null>(null);
  const macdHistRef = useRef<ISeriesApi<"Histogram"> | null>(null);

  const [tooltip, setTooltip] = useState<TooltipData | null>(null);

  const showRsi = activeIndicators.has("rsi_14");
  const showMacd = activeIndicators.has("macd_12_26_9");

  // Sync logical range from main → sub charts
  const syncRange = useCallback((range: LogicalRange | null) => {
    if (!range) return;
    rsiChartRef.current?.timeScale().setVisibleLogicalRange(range);
    macdChartRef.current?.timeScale().setVisibleLogicalRange(range);
  }, []);

  // ── Initialize main chart ──────────────────────────────────────────────
  useEffect(() => {
    if (!containerRef.current) return;
    const el = containerRef.current;

    const chart = createChart(el, CHART_OPTS(el.clientWidth));
    mainChartRef.current = chart;

    const candleSeries = chart.addCandlestickSeries({
      upColor: CHART_THEME.up,
      downColor: CHART_THEME.down,
      borderUpColor: CHART_THEME.up,
      borderDownColor: CHART_THEME.down,
      wickUpColor: CHART_THEME.up,
      wickDownColor: CHART_THEME.down,
    });
    candleSeriesRef.current = candleSeries;

    volumeSeriesRef.current = chart.addHistogramSeries({
      priceFormat: { type: "volume" },
      priceScaleId: "",
      color: "#26a69a",
    });
    (volumeSeriesRef.current as ISeriesApi<"Histogram">).priceScale().applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });

    smaSeriesRef.current = chart.addLineSeries({
      color: "#f59e0b",
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    });

    emaSeriesRef.current = chart.addLineSeries({
      color: "#60a5fa",
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    });

    const bbLineOpts = {
      lineWidth: 1 as const,
      priceLineVisible: false,
      lastValueVisible: false,
    };
    bbUpperRef.current = chart.addLineSeries({ ...bbLineOpts, color: "#a78bfa" });
    bbMidRef.current = chart.addLineSeries({ ...bbLineOpts, color: "#a78bfa88" });
    bbLowerRef.current = chart.addLineSeries({ ...bbLineOpts, color: "#a78bfa" });

    // Crosshair tooltip
    chart.subscribeCrosshairMove((param) => {
      if (!param.point || !param.time || !param.seriesData) {
        setTooltip(null);
        return;
      }
      const bar = param.seriesData.get(candleSeries) as
        | { open: number; high: number; low: number; close: number }
        | undefined;
      const vol = param.seriesData.get(volumeSeriesRef.current!) as
        | { value: number }
        | undefined;
      if (!bar) {
        setTooltip(null);
        return;
      }
      setTooltip({
        x: param.point.x,
        y: param.point.y,
        time: typeof param.time === "number"
          ? new Date(param.time * 1000).toISOString()
          : String(param.time),
        open: bar.open,
        high: bar.high,
        low: bar.low,
        close: bar.close,
        volume: vol?.value ?? 0,
      });
    });

    // Sync sub-charts
    chart.timeScale().subscribeVisibleLogicalRangeChange(syncRange);

    // Resize observer
    const ro = new ResizeObserver(() => {
      if (el.clientWidth > 0) {
        chart.applyOptions({ width: el.clientWidth });
      }
    });
    ro.observe(el);

    return () => {
      ro.disconnect();
      chart.timeScale().unsubscribeVisibleLogicalRangeChange(syncRange);
      chart.remove();
      mainChartRef.current = null;
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── RSI chart ─────────────────────────────────────────────────────────
  useEffect(() => {
    if (!showRsi || !rsiContainerRef.current) return;
    const el = rsiContainerRef.current;
    const chart = createChart(el, SUB_CHART_OPTS(el.clientWidth, 100));
    rsiChartRef.current = chart;

    const series = chart.addLineSeries({
      color: "#a78bfa",
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: true,
    });
    rsiSeriesRef.current = series;

    // Overbought/oversold reference lines via price lines
    series.createPriceLine({ price: 70, color: "#ef444466", lineWidth: 1, lineStyle: 2, axisLabelVisible: false });
    series.createPriceLine({ price: 30, color: "#22c55e66", lineWidth: 1, lineStyle: 2, axisLabelVisible: false });

    const ro = new ResizeObserver(() => {
      if (el.clientWidth > 0) chart.applyOptions({ width: el.clientWidth });
    });
    ro.observe(el);

    // Sync range from main chart
    const currentRange = mainChartRef.current?.timeScale().getVisibleLogicalRange();
    if (currentRange) chart.timeScale().setVisibleLogicalRange(currentRange);
    chart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
      if (range) mainChartRef.current?.timeScale().setVisibleLogicalRange(range);
    });

    return () => {
      ro.disconnect();
      chart.remove();
      rsiChartRef.current = null;
      rsiSeriesRef.current = null;
    };
  }, [showRsi]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── MACD chart ────────────────────────────────────────────────────────
  useEffect(() => {
    if (!showMacd || !macdContainerRef.current) return;
    const el = macdContainerRef.current;
    const chart = createChart(el, SUB_CHART_OPTS(el.clientWidth, 110));
    macdChartRef.current = chart;

    macdLineRef.current = chart.addLineSeries({
      color: "#60a5fa",
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    macdSignalRef.current = chart.addLineSeries({
      color: "#f97316",
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    macdHistRef.current = chart.addHistogramSeries({
      priceScaleId: "right",
      color: "#22c55e66",
    });

    const ro = new ResizeObserver(() => {
      if (el.clientWidth > 0) chart.applyOptions({ width: el.clientWidth });
    });
    ro.observe(el);

    const currentRange = mainChartRef.current?.timeScale().getVisibleLogicalRange();
    if (currentRange) chart.timeScale().setVisibleLogicalRange(currentRange);
    chart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
      if (range) mainChartRef.current?.timeScale().setVisibleLogicalRange(range);
    });

    return () => {
      ro.disconnect();
      chart.remove();
      macdChartRef.current = null;
      macdLineRef.current = null;
      macdSignalRef.current = null;
      macdHistRef.current = null;
    };
  }, [showMacd]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Push candle + volume data ──────────────────────────────────────────
  useEffect(() => {
    if (!candles.length || !candleSeriesRef.current || !volumeSeriesRef.current) return;

    candleSeriesRef.current.setData(
      candles.map((c) => ({
        time: toTs(c.time),
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      })),
    );

    volumeSeriesRef.current.setData(
      candles.map((c) => ({
        time: toTs(c.time),
        value: c.volume,
        color: c.close >= c.open ? CHART_THEME.upDim : CHART_THEME.downDim,
      })),
    );

    mainChartRef.current?.timeScale().fitContent();
  }, [candles]);

  // ── Push overlay indicator data ────────────────────────────────────────
  useEffect(() => {
    if (!candles.length) return;

    const withTs = <T,>(fn: (c: Candle) => T | null) =>
      candles
        .map((c) => {
          const v = fn(c);
          return v != null ? { time: toTs(c.time), ...v } : null;
        })
        .filter((x): x is NonNullable<typeof x> => x !== null);

    // SMA
    smaSeriesRef.current?.setData(
      activeIndicators.has("sma_20")
        ? withTs((c) =>
            c.indicators?.sma_20 != null ? { value: c.indicators.sma_20 } : null,
          )
        : [],
    );

    // EMA
    emaSeriesRef.current?.setData(
      activeIndicators.has("ema_50")
        ? withTs((c) =>
            c.indicators?.ema_50 != null ? { value: c.indicators.ema_50 } : null,
          )
        : [],
    );

    // BBands
    const showBB = activeIndicators.has("bbands_20_2");
    bbUpperRef.current?.setData(
      showBB
        ? withTs((c) =>
            c.indicators?.bb_upper != null ? { value: c.indicators.bb_upper } : null,
          )
        : [],
    );
    bbMidRef.current?.setData(
      showBB
        ? withTs((c) =>
            c.indicators?.bb_middle != null ? { value: c.indicators.bb_middle } : null,
          )
        : [],
    );
    bbLowerRef.current?.setData(
      showBB
        ? withTs((c) =>
            c.indicators?.bb_lower != null ? { value: c.indicators.bb_lower } : null,
          )
        : [],
    );
  }, [candles, activeIndicators]);

  // ── Push RSI data ──────────────────────────────────────────────────────
  useEffect(() => {
    if (!showRsi || !rsiSeriesRef.current || !candles.length) return;
    rsiSeriesRef.current.setData(
      candles
        .filter((c) => c.indicators?.rsi_14 != null)
        .map((c) => ({ time: toTs(c.time), value: c.indicators!.rsi_14! })),
    );
  }, [showRsi, candles]);

  // ── Push MACD data ─────────────────────────────────────────────────────
  useEffect(() => {
    if (!showMacd || !macdLineRef.current || !candles.length) return;

    macdLineRef.current.setData(
      candles
        .filter((c) => c.indicators?.macd_macd != null)
        .map((c) => ({ time: toTs(c.time), value: c.indicators!.macd_macd! })),
    );
    macdSignalRef.current?.setData(
      candles
        .filter((c) => c.indicators?.macd_signal != null)
        .map((c) => ({ time: toTs(c.time), value: c.indicators!.macd_signal! })),
    );
    macdHistRef.current?.setData(
      candles
        .filter((c) => c.indicators?.macd_histogram != null)
        .map((c) => ({
          time: toTs(c.time),
          value: c.indicators!.macd_histogram!,
          color:
            (c.indicators!.macd_histogram ?? 0) >= 0
              ? CHART_THEME.upDim
              : CHART_THEME.downDim,
        })),
    );
  }, [showMacd, candles]);

  // ── Tooltip display ────────────────────────────────────────────────────
  const isUp = tooltip ? tooltip.close >= tooltip.open : true;

  return (
    <div className="relative flex flex-col gap-px">
      {/* Crosshair tooltip */}
      {tooltip && (
        <div
          className="pointer-events-none absolute z-10 rounded border border-border bg-background/90 px-2 py-1 text-xs font-mono shadow backdrop-blur-sm"
          style={{ left: tooltip.x + 12, top: 8 }}
        >
          <span className="text-muted-foreground mr-2">
            {new Date(tooltip.time).toLocaleDateString()}
          </span>
          <span className={isUp ? "text-green-400" : "text-red-400"}>
            O {fmtPrice(tooltip.open)} H {fmtPrice(tooltip.high)} L{" "}
            {fmtPrice(tooltip.low)} C {fmtPrice(tooltip.close)}
          </span>
          <span className="text-muted-foreground ml-2">
            Vol {fmtVol(tooltip.volume)}
          </span>
        </div>
      )}

      {/* Main chart */}
      <div ref={containerRef} className="w-full" />

      {/* RSI pane */}
      {showRsi && (
        <div className="relative w-full">
          <span className="absolute left-2 top-1 z-10 text-xs text-muted-foreground">
            RSI(14)
          </span>
          <div ref={rsiContainerRef} className="w-full" />
        </div>
      )}

      {/* MACD pane */}
      {showMacd && (
        <div className="relative w-full">
          <span className="absolute left-2 top-1 z-10 text-xs text-muted-foreground">
            MACD(12,26,9)
          </span>
          <div ref={macdContainerRef} className="w-full" />
        </div>
      )}
    </div>
  );
}
