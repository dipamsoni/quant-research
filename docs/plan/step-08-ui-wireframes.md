# Step 8 — Institutional Dashboard UI

> Reference for UI architecture. Implementation references: [architecture/08-ui-system.md](../architecture/08-ui-system.md).

## Inspiration

- **Bloomberg Terminal** — dense financial workflows
- **TradingView** — charting
- **Koyfin** — analytics
- **OpenBB** — quant research workflows
- **Linear** / **Notion** — modern UX polish

## High-level layout

```
┌──────────────────────────────────────────────┐
│              TOP NAVBAR                      │
├──────────┬───────────────────────────────────┤
│          │                                   │
│ SIDEBAR  │      MAIN WORKSPACE               │
│          │                                   │
├──────────┴───────────────────────────────────┤
│             BOTTOM STATUS BAR                │
└──────────────────────────────────────────────┘
```

## Module pages

Built across phases:

| Module | Phase |
|--------|-------|
| Dashboard | 1 (shell), 3 (data) |
| Markets | 2 |
| Portfolio | 3 |
| Trading | 5 (paper trading later) |
| Backtesting | 5 |
| Research AI | 6 |
| Analytics | 7+ |
| RL Lab | 8+ |
| Agents | 9+ |
| Admin | 1 (basic) |
| Settings | 1 |

## Stack

| Purpose | Tool |
|---------|------|
| Styling | TailwindCSS |
| Components | shadcn/ui |
| Icons | Lucide |
| Charts (financial) | TradingView Lightweight Charts |
| Charts (analytics) | ECharts |
| Animation | Framer Motion (sparingly) |
| State | Zustand |
| Data | TanStack Query |

## Sidebar nav (build as you go)

Phase 1: Dashboard, Markets (placeholder), Portfolio (placeholder), Settings
Phase 2: Markets becomes real
Phase 3: Portfolio becomes real
Phase 5: Backtesting added
Phase 6: Research AI added
Phase 7+: Analytics, Agents, RL Lab, Admin

## Top navbar

- Global search (CMD+K)
- AI command bar (Phase 6+)
- Notifications
- Market status indicator
- Profile menu

## Core component patterns

### Market terminal (Phase 2)
```
┌─────────────────────────────────────┐
│ Search | Status | AI Assist        │
├─────────────────────────────────────┤
│ Watchlist  │  Candlestick Chart    │
├────────────┴────────────────────────┤
│ Order Book | Trades | News         │
└─────────────────────────────────────┘
```

### Portfolio dashboard (Phase 3)
```
┌──────────────────────────────────────┐
│ Summary Cards                        │
├──────────────────────────────────────┤
│ Allocation Chart | Performance Chart │
├──────────────────────────────────────┤
│ Holdings Table | Risk Analytics      │
└──────────────────────────────────────┘
```

### Backtesting lab (Phase 5)
```
┌──────────────────────────────────────┐
│ Strategy Builder                     │
├──────────────────────────────────────┤
│ Parameter Controls                   │
├──────────────────────────────────────┤
│ Equity Curve | Drawdown | Metrics    │
├──────────────────────────────────────┤
│ Trade History Table                  │
└──────────────────────────────────────┘
```

### AI research workspace (Phase 6)
```
┌─────────────────────────────────────┐
│ AI Query Bar                        │
├─────────────────────────────────────┤
│ Chat Panel    │ Research Results    │
├───────────────┴─────────────────────┤
│ Sources | Citations | Agent Logs    │
└─────────────────────────────────────┘
```

## Charting

For candlesticks: **TradingView Lightweight Charts**, not Chart.js or D3.
For analytics (heatmaps, correlation matrices, factor exposure): **ECharts**.
For very custom visualizations: **D3**.

Inline AI signals overlay on charts (Phase 6+):
```
BUY signal at $223
confidence: 89%
RL signal: bullish
sentiment: positive
```

## Theme

**Dark theme first.** Institutional apps live in dark mode.
- High information density
- Strong contrast
- Professional typography (use a clean sans like Inter, Geist, or Söhne)

## Performance

- Virtualized tables for >100 rows (use TanStack Virtual)
- Lazy-load chart libraries (`dynamic` import in Next.js)
- Memoize chart data transformations
- WebSocket batching: coalesce price updates per 100ms instead of per tick

## Real-time UI patterns

```
WebSocket → Zustand store → component subscribes
```

Don't trigger React Query refetches on every tick; that's what stores are for.

## Command palette (CMD+K)

Add in Phase 3+. Searchable actions:
- Search stocks
- Run backtest
- Open portfolio
- Ask AI
- Train RL model (later)

Use [`cmdk`](https://cmdk.paco.me/) library.

## See also

- [UI system architecture](../architecture/08-ui-system.md)
- [Phase 1: dashboard shell](../phases/phase-1.md)
