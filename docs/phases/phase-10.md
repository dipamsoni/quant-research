# Phase 10 — Institutional Analytics

**Duration:** ~4 weeks
**Goal:** Bloomberg-style analytics: heatmaps, correlation matrices, factor exposure, risk decomposition.

## Acceptance criteria
- [ ] Sector/industry heatmap of holdings
- [ ] Correlation matrix between portfolio assets
- [ ] Factor exposure (Fama-French style)
- [ ] Risk decomposition: variance contribution per asset
- [ ] Performance attribution (asset selection vs allocation)
- [ ] Multi-panel analytics dashboard

## Task list

### Week 1-2: Backend
- [ ] Factor models: Fama-French 3 and 5 factor regressions
- [ ] Rolling correlations
- [ ] Risk decomposition engine
- [ ] Performance attribution

### Week 3-4: UI
- [ ] Heatmap component (D3 or ECharts)
- [ ] Correlation matrix
- [ ] Factor exposure bar charts
- [ ] Customizable analytics workspace (drag/drop panels)

## Open-source
- **statsmodels** — regressions
- **pandas / numpy** — data ops
- **ECharts / D3** — visuals
- **Qlib** — for inspiration on factor model structure

## Pitfalls
- **Showing too much.** Bloomberg-style isn't "every metric on screen"; it's the right metric at the right time.
- **Stale data.** Update analytics in background, not on every page load.
