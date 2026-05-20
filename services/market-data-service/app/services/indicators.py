from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.ohlcv import OHLCVCandle

from app.schemas.market import IndicatorValues

VALID_INDICATORS: frozenset[str] = frozenset(
    {"sma_20", "ema_50", "rsi_14", "macd_12_26_9", "bbands_20_2"}
)


def validate_indicators(indicators: list[str]) -> list[str]:
    invalid = [i for i in indicators if i not in VALID_INDICATORS]
    if invalid:
        raise ValueError(
            f"Unknown indicators: {invalid}. Valid: {sorted(VALID_INDICATORS)}"
        )
    return indicators


def _safe(v: object) -> float | None:
    if v is None:
        return None
    try:
        f = float(v)  # type: ignore[arg-type]
        return None if math.isnan(f) or math.isinf(f) else f
    except (TypeError, ValueError):
        return None


def compute_indicators(
    candles: list[OHLCVCandle],
    requested: list[str],
) -> list[IndicatorValues | None]:
    """Compute technical indicators server-side using the `ta` library.

    Returns a list aligned 1-to-1 with `candles`. Early candles that lack
    sufficient history for a given indicator will have None for that field.
    """
    if not candles or not requested:
        return [None] * len(candles)

    try:
        import pandas as pd
        import ta.momentum as tam
        import ta.trend as tat
        import ta.volatility as tav
    except ImportError:
        return [None] * len(candles)

    close = pd.Series([float(c.close) for c in candles])

    results: list[dict[str, float | None]] = [{} for _ in candles]

    if "sma_20" in requested:
        sma = tat.sma_indicator(close, window=20, fillna=False)
        for i, v in enumerate(sma):
            results[i]["sma_20"] = _safe(v)

    if "ema_50" in requested:
        ema = tat.ema_indicator(close, window=50, fillna=False)
        for i, v in enumerate(ema):
            results[i]["ema_50"] = _safe(v)

    if "rsi_14" in requested:
        rsi = tam.rsi(close, window=14, fillna=False)
        for i, v in enumerate(rsi):
            results[i]["rsi_14"] = _safe(v)

    if "macd_12_26_9" in requested:
        macd_obj = tat.MACD(close, window_slow=26, window_fast=12, window_sign=9, fillna=False)
        macd_line = macd_obj.macd()
        signal_line = macd_obj.macd_signal()
        hist = macd_obj.macd_diff()
        for i in range(len(candles)):
            results[i]["macd_macd"] = _safe(macd_line.iloc[i])
            results[i]["macd_signal"] = _safe(signal_line.iloc[i])
            results[i]["macd_histogram"] = _safe(hist.iloc[i])

    if "bbands_20_2" in requested:
        bb_obj = tav.BollingerBands(close, window=20, window_dev=2, fillna=False)
        upper = bb_obj.bollinger_hband()
        mid = bb_obj.bollinger_mavg()
        lower = bb_obj.bollinger_lband()
        for i in range(len(candles)):
            results[i]["bb_upper"] = _safe(upper.iloc[i])
            results[i]["bb_middle"] = _safe(mid.iloc[i])
            results[i]["bb_lower"] = _safe(lower.iloc[i])

    return [IndicatorValues(**r) if r else None for r in results]
