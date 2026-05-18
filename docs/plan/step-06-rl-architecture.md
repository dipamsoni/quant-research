# Step 6 — RL Trading Architecture

> Phase 8+ only. Reading this before completing Phases 1–7 is procrastination.

## Honest preface

RL for trading is an active research area where well-funded teams struggle to beat simple baselines after costs. The plan below is correct, but expectations must match reality:

- A working backtested PPO agent: weeks of effort, realistic
- A profitable paper-trading agent: months of careful work
- A profitable live agent: years and significant capital
- "Beats the market consistently": research-grade, no guarantees

## RL system layers

```
Data Layer
Environment Layer
Agent Layer
Training Layer
Evaluation Layer
Inference Layer
Execution Layer
Monitoring Layer
```

## Core concepts

| Concept | Meaning |
|---------|---------|
| State | What the agent observes |
| Action | What the agent can do |
| Reward | Learning signal |
| Policy | Decision function (a neural network) |
| Environment | Market simulator |

## Environment design (most important part)

A `TradingEnvironment` (Gymnasium-style) must simulate:

- Prices and price moves
- Position state (long/short/flat)
- PnL accounting
- **Transaction costs** (non-negotiable)
- **Slippage** (non-negotiable)
- Risk constraints
- Liquidity limits
- Market hours
- Partial fills

```python
class TradingEnvironment(gym.Env):
    def reset(self) -> tuple[State, dict]: ...
    def step(self, action) -> tuple[State, float, bool, bool, dict]: ...
    def calculate_reward(self) -> float: ...
```

## State space

| Level | Includes |
|-------|----------|
| Beginner | OHLCV, RSI, MACD, balance, position, cash |
| Intermediate | Above + sentiment, regime, correlation, exposure |
| Advanced | Above + order book, tick data, macro, factor exposures, agent memory, news embeddings |

## Action space

| Type | Shape | Use case |
|------|-------|----------|
| Discrete | `{HOLD, BUY, SELL}` | Beginner |
| Continuous | `[-1.0, 1.0]` | Position sizing |
| Portfolio | `[w1, w2, ..., wn]` | Multi-asset allocation |

## Reward engineering

**Never use raw daily PnL alone.** That trains reckless agents.

Risk-adjusted reward:

```
reward = pnl
       - transaction_costs
       - drawdown_penalty
       - volatility_penalty
       - turnover_penalty
```

Optimize for: Sharpe, Sortino, Calmar, max drawdown.

## Algorithm progression

1. **DQN** — discrete actions, simplest entry
2. **PPO** — best general starter (stable, scalable)
3. **SAC / TD3** — continuous actions, portfolio sizing
4. **Multi-Agent PPO** — hedge fund simulation
5. **Hierarchical RL** — research-grade

## Stack

| Purpose | Tool |
|---------|------|
| RL algorithms | Stable-Baselines3 |
| Distributed | Ray RLlib |
| Environments | Gymnasium |
| Trading-specific | FinRL |
| Tracking | Weights & Biases |

## Training pipeline

```
Historical Data → Feature Engineering → Trading Env →
RL Agent Training → Policy Evaluation → Backtest →
Paper Trading → (eventually) Small Live Capital
```

## Risk-aware RL

Don't let RL execute unconstrained:

```
RL Action → Risk Engine → Validated Action → Execution
```

If RL wants 100% TSLA, risk engine reduces to 25%.

## Offline RL (advanced)

Train on historical data without exploration. Algorithms: CQL, BCQ, IQL.
Live exploration with real money is dangerous; offline RL avoids that.

## Multi-agent RL (Phase 9)

Agents:
- Momentum agent
- Mean reversion agent
- Macro agent
- Risk agent
- Execution agent
- Portfolio manager (supervisor)

Coordination via consensus engine.

## Paper trading workflow

```
Backtest → Paper Trade → Shadow Trade → Small Capital → (maybe) Production
```

Skip steps at your own risk.

## Database tables (Phase 8)

- `rl_experiments`
- `rl_training_runs`
- `rl_actions`
- `rl_evaluations`
- model checkpoints in object storage

## Mistakes to avoid

- ❌ Ignoring slippage and fees
- ❌ Using future-leaked features
- ❌ Training on tiny datasets
- ❌ Deploying directly live
- ❌ Optimizing only cumulative return
- ❌ Assuming RL will beat classical systems

## See also

- [Phase 8 tasks](../phases/phase-8.md)
