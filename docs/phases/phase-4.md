# Phase 4 — ML Prediction Systems

**Duration:** ~4 weeks
**Goal:** XGBoost-based price/return predictions exposed as signals.

> Read [step-05](../plan/step-05-quant-ml-roadmap.md) carefully — the order matters.

## Acceptance criteria

- [ ] Feature store table populated daily for all watched assets
- [ ] At least one trained XGBoost model in MLflow registry
- [ ] `/api/v1/ml/predict-price` returns predictions with confidence scores
- [ ] Model evaluation on held-out test set: documented Sharpe, hit rate, info ratio
- [ ] Signals generated from predictions and persisted (`trading_signals` table)
- [ ] UI shows signals overlaid on candlestick chart
- [ ] Honest disclaimer: predictions are not investment advice

## Task list

### Week 1: Feature engineering
- [ ] `services/prediction-service/` scaffold
- [ ] Table: `feature_store(asset_id, feature_name, feature_value, feature_time)` indexed `(asset_id, feature_name, feature_time DESC)`
- [ ] `app/feature_engineering/technical_indicators.py` — RSI, MACD, BB, ATR, etc.
- [ ] `app/feature_engineering/market_features.py` — returns, rolling stats, volatility
- [ ] `app/feature_engineering/time_features.py` — day of week, month, earnings season flag
- [ ] Daily cron: regenerate features for all tracked assets

### Week 2: Model training
- [ ] Install MLflow, configure tracking URI (local file backend OK for MVP)
- [ ] `app/training/xgboost_trainer.py`:
  - Pull features from feature store
  - Target: next-day return
  - Train/test split: walk-forward, NOT random
  - Hyperparameter search: Optuna or simple grid
  - Log run to MLflow with metrics
- [ ] Evaluation: Sharpe of predicted-direction signals on test set, not just R²
- [ ] Register best model to MLflow registry as `next_day_return_xgb_v1`

### Week 3: Inference + signals
- [ ] `app/inference/predictor.py` — load latest model, generate predictions
- [ ] `POST /api/v1/ml/predict-price` — accepts symbol, returns prediction
- [ ] `app/services/signal_engine.py` — convert predictions to BUY/SELL/HOLD with confidence threshold
- [ ] Persist signals in `trading_signals` table
- [ ] `GET /api/v1/signals?symbol=&since=` — list signals
- [ ] Cron: generate signals for watchlist assets each market close

### Week 4: UI + honesty
- [ ] Signal overlay on candlestick chart (arrows up/down with confidence)
- [ ] Signal history panel
- [ ] **Required disclaimer** on every prediction: "Not investment advice. Past performance is not indicative of future results."
- [ ] Model card in UI: training data range, test Sharpe, last retrained
- [ ] Acceptance check; tag; advance phase

## Out of scope

- ❌ Deep learning (Phase 6 if at all)
- ❌ RL (Phase 8)
- ❌ Live trading
- ❌ Sentiment features (Phase 6)
- ❌ Multi-horizon predictions (next-day only for MVP)

## Open-source

- **XGBoost** — primary model
- **LightGBM** — alternative to compare
- **MLflow** — registry and tracking
- **pandas-ta** — already used in Phase 2
- **Optuna** — hyperparameter search

## Critical pitfalls

- **Look-ahead bias.** Features at time t must only use data available at t. Walk-forward CV.
- **Survivorship bias.** Don't train only on currently-listed stocks; that biases performance up.
- **Optimizing R² instead of Sharpe.** A model that predicts direction with 51% accuracy beats one with high R² that predicts wrong direction.
- **Ignoring transaction costs.** Always evaluate net of plausible costs (5–10 bps for liquid US stocks).
- **No baseline comparison.** Always compare to "buy and hold SPY" and "always predict yesterday's return".
