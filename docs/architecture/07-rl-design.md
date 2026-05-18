# RL System Design

> Phase 8+. See [step-06](../plan/step-06-rl-architecture.md) for the full plan and honest reality-check.

## Architectural pillars

```
Data → Environment → Agent → Trainer → Evaluator → Inference → Risk Gate → (paper) Execution
                                                                       ↑
                                                                  Monitoring
```

Each layer is replaceable. Don't fuse them.

## Stack

| Component | Tool |
|-----------|------|
| Algorithms | Stable-Baselines3 (PPO, DQN, SAC) |
| Distributed | Ray RLlib (Phase 9 multi-agent) |
| Environments | Gymnasium |
| Trading-specific reference | FinRL |
| Tracking | Weights & Biases |
| Storage | MLflow for checkpoints; Postgres for run metadata |

Don't reimplement PPO. Use SB3.

## Environment contract

Every env implements:

```python
class TradingEnvironment(gym.Env):
    observation_space: gym.Space
    action_space: gym.Space

    def reset(self, *, seed=None, options=None) -> tuple[obs, info]: ...
    def step(self, action) -> tuple[obs, reward, terminated, truncated, info]: ...
    def render(self): ...
    def close(self): ...
```

`info` includes everything you need for offline analysis: position, cash, fees paid, slippage, current price, drawdown.

## State space (observation)

| Tier | Components |
|------|-----------|
| MVP | OHLCV (last N bars), 5 indicators (RSI, MACD, BB, ATR, momentum), position (long/short/flat), cash ratio |
| Intermediate | + sentiment score, regime label, sector return, correlation to SPY |
| Advanced | + order book features, factor exposures, news embeddings, agent memory state |

Normalize all features (z-score or min-max). Unnormalized inputs destroy training.

## Action space

| Type | Shape | When |
|------|-------|------|
| Discrete | `Discrete(3)` (hold, buy, sell) | Single asset, beginner |
| Continuous | `Box(-1, 1, (1,))` | Position sizing |
| Portfolio | `Box(0, 1, (N,))` with sum-to-1 | Multi-asset allocation |

Start discrete. Move to continuous only when discrete is mastered.

## Reward design

**Never use raw daily PnL.** That trains gambling behavior.

```python
def reward(self):
    pnl = self.current_value - self.previous_value
    fees = self.last_trade_fees
    drawdown_pen = max(0, self.current_drawdown - DRAWDOWN_THRESHOLD) * DD_WEIGHT
    turnover_pen = self.last_turnover * TURNOVER_WEIGHT

    return pnl - fees - drawdown_pen - turnover_pen
```

Optimize for risk-adjusted metrics: Sharpe, Sortino, Calmar.

## Realistic execution

Every env must simulate:
- Transaction fees (bps based on asset class)
- Slippage (bps; higher for large orders, low liquidity)
- Partial fills for large orders
- Market hours / closed periods
- No-trade buffer between fills (avoid 100x trades per minute)

If your env doesn't simulate these, your agent will look profitable in training and lose money everywhere else.

## Training pipeline

```
historical OHLCV → feature engineering → env wrap → PPO train → checkpoint → eval on holdout → log to W&B
```

Walk-forward CV:
```
[train 2020-2023] [test Q1 2024]
[train 2020-Q1 2024] [test Q2 2024]
[train 2020-Q2 2024] [test Q3 2024]
...
```

Don't tune hyperparameters on the final test set.

## Evaluation

Compare ALWAYS against baselines:
- Buy-and-hold SPY
- Buy-and-hold the asset
- Random actions
- Simple momentum (12-1)
- Phase 4 ML signal strategy

If RL beats all baselines on out-of-sample data after costs, you have something interesting. If not, that's the typical result; iterate or simplify.

## Inference

Inference path:
```
new candle → feature engineering → policy.predict(obs) → action → risk gate → paper execution
```

Risk gate (in code, not in policy):
- Position size cap
- Sector exposure cap
- Max drawdown stop (force flat if exceeded)
- Volatility filter (no trading during extreme vol)
- Trading hours
- Holiday calendar

Policy proposes; risk gate disposes.

## Storage

| Item | Where |
|------|-------|
| Trained policy weights | MLflow artifact store (S3-compatible) |
| Training metrics | W&B |
| Run metadata | Postgres `rl_experiments`, `rl_training_runs` |
| Live actions | Postgres `rl_actions` (every action, every state, for audit) |

## Multi-agent (Phase 9 with RL)

Phase 9's "multi-agent" is mostly LLM-based, not RL multi-agent. True multi-agent RL (MARL) is research-grade. If you go there:
- Use RLlib (built for MARL)
- Centralized training, decentralized execution (CTDE)
- Specialized agents per regime/factor

Most teams won't get value from MARL. Single-agent RL with multiple policies (one per regime) often outperforms.

## Live deployment policy

Never go from backtest to live with real money in one step. The order:

```
backtest → paper trade → shadow trade → small capital ($100s) → scale carefully
```

Each step should run for weeks. Skipping = losing money.

## Failure modes

- **Reward hacking.** Agent finds exploit (e.g., infinite tiny trades that arb the simulator). Test reward function with random/dumb agents first.
- **Overfitting to one regime.** Agent learns "always buy" because training period was bull market. Mitigation: train on multiple regimes (2008, 2020 COVID, 2022 bear, etc.).
- **Look-ahead leak.** Feature pipeline sees future data. Audit every feature for time alignment.
- **Distribution shift.** Live market differs from training. Continuous monitoring + retraining cadence.
- **Policy collapse.** Continuous training degrades performance. Always keep a stable baseline.
