# Phase 8 — RL Trading Systems

**Duration:** ~4 weeks (likely longer in practice)
**Goal:** PPO-based trading agent with realistic environment, paper-trading only.

> Read [step-06 (RL architecture)](../plan/step-06-rl-architecture.md) carefully. Read the honest preface twice.

## Reality check

RL in finance is genuinely hard. Realistic outcomes for this phase:
- ✅ A trained PPO agent that runs in a Gymnasium environment
- ✅ Backtested results showing the agent learns *something*
- ⚠️ Paper-trading performance that *might* beat buy-and-hold on training-distribution markets
- ❌ A profitable live strategy (not realistic for one phase of work)

If the agent doesn't beat a simple momentum strategy out-of-sample, that's normal. Don't fudge the metrics.

## Acceptance criteria
- [ ] `services/rl-service/` running, with proper layout
- [ ] At least one Gymnasium env with realistic costs/slippage
- [ ] Trained PPO agent stored as MLflow / W&B artifact
- [ ] Honest evaluation report: in-sample vs out-of-sample, vs baselines
- [ ] Paper trading runner that consumes live prices and logs decisions
- [ ] RL Lab UI: training curves, action heatmap, episode replay

## Task list

### Week 1: Environment
- [ ] Install gymnasium, stable-baselines3, FinRL (for reference), wandb
- [ ] `app/environments/single_asset_env.py` with:
  - State: OHLCV + indicators + position + cash
  - Action: discrete {hold, buy, sell} or continuous [-1, 1]
  - Reward: PnL − transaction_cost − drawdown_penalty
  - Realistic execution: slippage, fees, partial fills
- [ ] Unit tests on env

### Week 2: Training
- [ ] `app/trainers/ppo_trainer.py`
- [ ] Walk-forward train/test split
- [ ] Track via W&B
- [ ] Baselines: buy-hold, random, momentum, ML-signal
- [ ] Report: agent vs each baseline, in-sample and out-of-sample

### Week 3: Inference + paper trading
- [ ] `app/inference/policy_runner.py` — load checkpoint, decide actions on live data
- [ ] Paper trading service: subscribes to market WS, simulates execution, logs PnL
- [ ] Risk overrides: hard position limits enforced outside the policy

### Week 4: UI
- [ ] `/rl-lab` page
- [ ] Reward curve over training
- [ ] Episode replay (action heatmap on candlestick)
- [ ] Paper trading dashboard (live PnL, current position, trade log)

## Out of scope
- ❌ Live trading with real money
- ❌ Multi-agent RL (Phase 9)
- ❌ Custom RL algorithms (use SB3 implementations)
- ❌ GPU clusters (a single GPU or even CPU is fine for this scale)

## Pitfalls
- **Reward hacking.** If you reward only PnL, agent learns to gamble. Always include drawdown penalty.
- **Overfitting to training period.** Walk-forward CV. Don't tune hyperparameters on the test set.
- **Future leakage.** Make sure the env's `step()` only exposes data the agent could have known at that moment.
- **Tiny dataset.** If you train on 6 months of one stock, results mean nothing. Use multiple symbols and multiple years.
- **No baseline comparison.** A "+15% Sharpe-1.2" agent that loses to buy-and-hold is a failed agent.
- **Live deployment without paper trading.** Don't.
