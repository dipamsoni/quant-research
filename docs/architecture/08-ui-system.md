# UI System

> See [step-08](../plan/step-08-ui-wireframes.md) for module-level wireframes.

## Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | Next.js 15 App Router | RSC, streaming, mature ecosystem |
| Language | TypeScript strict | Type safety across FE/BE via shared `packages/types` |
| Styling | Tailwind CSS | Utility-first, dark-mode trivial, fast |
| Components | shadcn/ui | Owned components, customizable, accessible |
| Icons | Lucide | Tree-shakeable, large set |
| Charts (financial) | TradingView Lightweight Charts | Industry-standard candlesticks |
| Charts (analytics) | ECharts | Heatmaps, complex charts |
| Charts (KPI cards) | Tremor | Pre-built dashboard pieces |
| State | Zustand | Lightweight, no boilerplate |
| Server state | TanStack Query | Caching, refetch, mutations |
| Forms | React Hook Form + Zod | Validated forms with TS inference |
| Tables | TanStack Table + Virtual | Performant for >1k rows |
| Animation | Framer Motion | Sparingly |
| Command palette | cmdk | shadcn-compatible |

## Folder structure

```
apps/web/
├── app/
│   ├── (auth)/
│   ├── (dashboard)/
│   │   ├── layout.tsx
│   │   ├── dashboard/
│   │   ├── market/
│   │   ├── portfolio/
│   │   ├── backtesting/
│   │   ├── research/
│   │   ├── analytics/
│   │   ├── rl-lab/
│   │   ├── agents/
│   │   └── settings/
│   ├── layout.tsx
│   └── globals.css
├── components/
│   ├── charts/
│   ├── layouts/
│   ├── tables/
│   └── ui/                     # local-only shadcn variants
├── hooks/
├── lib/                         # formatters, fetchers, utilities
├── services/                    # typed API clients
├── store/                       # Zustand stores
└── providers/
```

When a component is reusable across apps → move to `packages/ui/`.

## Component organization

```
components/
├── charts/
│   ├── CandlestickChart.tsx
│   ├── EquityCurve.tsx
│   ├── DrawdownChart.tsx
│   ├── AllocationPie.tsx
│   ├── CorrelationHeatmap.tsx
│   └── FactorExposureBar.tsx
├── tables/
│   ├── HoldingsTable.tsx
│   ├── TradesTable.tsx
│   └── SignalsTable.tsx
├── trading/
│   ├── Watchlist.tsx
│   ├── OrderForm.tsx
│   ├── PriceTicker.tsx
│   └── SymbolSearch.tsx
├── ai/
│   ├── ChatPanel.tsx
│   ├── CitationBadge.tsx
│   └── ToolTrace.tsx
└── layouts/
    ├── DashboardShell.tsx
    ├── Sidebar.tsx
    └── TopNav.tsx
```

## State management

Two layers:

**Server state** (TanStack Query)
- All API data
- Caching, refetch on focus, optimistic updates
- One query key per resource

**Client state** (Zustand)
- Auth tokens
- Watchlist (local cache, synced to server)
- WebSocket-streamed prices
- UI preferences (theme, sidebar collapsed)

NEVER store API data in Zustand. NEVER store UI-only state in TanStack Query.

## Real-time streaming

```
WebSocket → store/prices.ts (Zustand) → useStockPrice(symbol) hook → component
```

Coalesce updates per 100ms (`requestAnimationFrame` batch) so React doesn't re-render every tick.

## SDK pattern

```typescript
// packages/sdk/market/client.ts
export const marketClient = {
  getCandles: (params: GetCandlesParams) =>
    fetch(`/api/v1/market/candles?${qs(params)}`).then(handleResponse<Candle[]>),
  // ...
};

// hooks/useCandles.ts
export function useCandles(symbol: string, timeframe: Timeframe) {
  return useQuery({
    queryKey: ["candles", symbol, timeframe],
    queryFn: () => marketClient.getCandles({ symbol, timeframe }),
  });
}
```

## Theming

Dark theme first. Light mode optional. Token-based:
- `--background`, `--foreground`, `--muted`, `--accent`
- `--positive` (green), `--negative` (red), `--warning` (amber)

shadcn/ui uses these out of the box.

Typography: Geist or Inter. Tabular numerals for prices (`font-feature-settings: 'tnum'`).

## Performance

| Concern | Solution |
|---------|----------|
| Large tables | TanStack Virtual; render only visible rows |
| Heavy charts | Dynamic import (`next/dynamic`); load on view |
| API waterfalls | Parallel queries; use `useQueries` |
| WebSocket spam | 100ms throttle in store reducer |
| Bundle size | Analyze with `@next/bundle-analyzer` periodically |
| Images | `next/image` everywhere |

## Accessibility

- Keyboard-navigable everywhere (especially CMD+K)
- ARIA labels on icon-only buttons
- Color contrast: WCAG AA minimum
- Don't communicate state with color alone (use icons + text too)
- Focus visible

## Testing

| Layer | Tool | When |
|-------|------|------|
| Components | Vitest + Testing Library | Critical UI logic |
| E2E | Playwright | Auth flows, key user journeys |
| Visual | Percy or Chromatic | Optional, Phase 11+ |

Don't aim for 100% coverage. Test what would hurt to break.

## Dev workflow

```bash
pnpm --filter web dev          # Next.js dev server
pnpm --filter web typecheck    # tsc
pnpm --filter web lint         # eslint
pnpm --filter web test         # vitest
pnpm --filter web build        # production build
```

## Anti-patterns

- ❌ Inline styles (use Tailwind)
- ❌ Component re-implementations of shadcn primitives
- ❌ Fetching in `useEffect` (use TanStack Query)
- ❌ Prop drilling beyond 2 levels (use Zustand or context)
- ❌ Global Redux store (overkill for this app)
- ❌ Computing derived data in components on every render (use `useMemo` or move to query select)
