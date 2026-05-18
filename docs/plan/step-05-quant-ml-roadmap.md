# Step 5 — Quant ML Roadmap

> The intelligence layer. Learn order matters more than model complexity.

## Critical rule

**Don't start with deep learning or RL.** The institutional path is:

```
Phase 1 → Market Data Intelligence (cleaning, indicators)
Phase 2 → Feature Engineering
Phase 3 → Classical ML (XGBoost, LightGBM)
Phase 4 → Signal Generation
Phase 5 → Portfolio Optimization
Phase 6 → Deep Learning (only if classical isn't enough)
Phase 7 → RL Trading
Phase 8 → Multi-Agent Quant
```

Most failed quant projects skip the first four steps.

## Phase A: Market data intelligence (Phase 2 in roadmap)

Build technical indicators using `pandas-ta` or `TA-Lib`:
- RSI, MACD, Bollinger Bands, ATR, VWAP, EMA/SMA, momentum, volume indicators

Store engineered features in a `feature_store` table. This is non-optional.

## Phase B: Feature engineering (Phase 4 in roadmap)

Categories:
- **Price-based:** returns, rolling mean/std, volatility, z-score, momentum
- **Technical:** RSI, MACD, ADX, VWAP, stochastic
- **Time:** day of week, market session, earnings season
- **Statistical:** Hurst exponent, autocorrelation, cointegration, beta, alpha
- **Sentiment:** news, social, earnings calls, SEC filings (FinBERT or LLM-based)

Pipeline: `Raw → Cleaning → Normalization → Generation → Validation → Feature Store`.

## Phase C: Classical ML first (Phase 4)

**Best first model:** XGBoost.
- Strong on tabular financial data
- Fast, interpretable

Targets to predict:
- `next_day_return`
- `5_day_return`
- `volatility`
- `trend_direction` (classification: BUY/SELL/HOLD)

**Don't optimize for accuracy.** Optimize for Sharpe ratio after backtesting.

## Phase D: Signal generation (Phase 4)

Prediction ≠ trading signal. Convert with rules:

```python
if prediction_return > 0.02 and confidence > 0.7:
    signal = BUY
elif prediction_return < -0.02 and confidence > 0.7:
    signal = SELL
else:
    signal = HOLD
```

Filter signals by:
- prediction confidence
- market regime
- portfolio risk constraints

## Phase E: Backtest validation (Phase 5)

Real metrics — NOT accuracy:
- Sharpe ratio
- Sortino ratio
- Max drawdown
- CAGR
- Win rate
- Profit factor

Always include transaction costs and slippage. A "winning" model that ignores costs is worthless.

## Phase F: Time-series forecasting (Phase 6, optional)

Order to try:
1. Prophet (baseline)
2. LSTM (sequence memory)
3. TFT / Temporal Fusion Transformer
4. Plain Transformers

**Reality check:** Deep learning often performs WORSE than gradient boosting in finance. Don't assume more complexity = better alpha.

## Phase G: Regime detection (Phase 7+)

Models: KMeans, HMM, Gaussian Mixture
Why: different strategies work in different regimes (bull/bear/high-vol).

## Phase H: Sentiment pipeline (Phase 6)

Sources: news, X/Twitter, Reddit, SEC filings, earnings calls
Models:
- Beginner: VADER, TextBlob
- Production: FinBERT, LLMs, sentence-transformers

## Phase I: Factor modeling (Phase 7+)

Common factors: momentum, value, size, quality, low volatility, profitability
Models: Fama-French style, Barra-style, custom factor engines

## Phase J: Portfolio optimization (Phase 7)

- Mean-variance (PyPortfolioOpt)
- Risk parity
- Black-Litterman
- ML-based return forecasts

## Phase K: RL preparation (Phase 8+ only)

Don't touch this until you have:
- Working backtester
- Working signal system
- Working portfolio optimization
- Working risk engine

See [step-06-rl-architecture.md](step-06-rl-architecture.md).

## MLOps essentials

| Concern | Tool |
|---------|------|
| Experiment tracking | MLflow or Weights & Biases |
| Model registry | MLflow |
| Feature store | Postgres tables (no need for Feast in MVP) |
| Versioning | Git tags + MLflow |

## Mistakes to avoid

- ❌ Predicting exact prices only
- ❌ Optimizing only for accuracy
- ❌ Ignoring transaction costs
- ❌ Ignoring slippage
- ❌ Ignoring market regimes
- ❌ Starting with RL
- ❌ Using random Kaggle finance datasets without understanding survivorship bias

## See also

- [Phase 4 tasks](../phases/phase-4.md)
- [Phase 5 tasks](../phases/phase-5.md)
