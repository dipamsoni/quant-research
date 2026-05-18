# Step 16 — AI Agent Workflow Diagrams

> Phase 6 (basic) and Phase 9 (advanced multi-agent).

## Honest framing

The "AI hedge fund" framing is mostly aesthetic. In practice:
- A single well-prompted LLM with good tools often outperforms a chain of 5 agents
- Each agent adds latency, cost, and error
- Multi-agent systems shine when tasks are genuinely parallelizable

That said, multi-agent design is worth building for:
- Auditability (clear separation of concerns)
- Adversarial reasoning (bull vs bear)
- Specialized memory and tooling

## Phase 6: single research assistant

Start with **one good agent** before going multi-agent.

### Architecture
```
User Query
   ↓
Research Agent (LangGraph)
   ├── tool: market_data
   ├── tool: news_search
   ├── tool: rag (SEC filings, reports)
   └── tool: portfolio_lookup
   ↓
Streaming Response with Citations
```

### Tools
- `market_tool.get_price(symbol)`
- `market_tool.get_candles(symbol, timeframe, range)`
- `news_tool.search(query, since)`
- `rag_tool.query(question)`
- `portfolio_tool.get_holdings(user_id)`
- `portfolio_tool.get_metrics(user_id)`

### LangGraph state machine
```
START → Plan → Tool Calls (parallel) → Synthesize → END
                ↓ (with retries)
              Error
```

### Memory
- Short-term: conversation history (Redis)
- Long-term: research reports (Postgres + pgvector)

## Phase 9: multi-agent supervisor pattern

```
        Supervisor Agent (CIO)
                │
   ┌────────────┼────────────┐
   ▼            ▼            ▼
Research    Risk        Portfolio
Agent       Agent       Agent
   │            │            │
   ▼            ▼            ▼
Sentiment   Macro        Execution
Agent       Agent        Agent
```

## Agent roles

### Supervisor (Phase 9)
- Receives task, plans, delegates
- Aggregates outputs
- Resolves conflicts via consensus engine
- Final decision

### Research agent
- Equity research, trend analysis
- Tools: SEC filings, market data, news, RAG
- Output: `{ symbol, sentiment, confidence, risk_level, summary }`

### Sentiment agent
- News, social, earnings calls
- Models: FinBERT, LLM-based
- Output: per-symbol sentiment scores

### Risk agent
- Validates trades against limits
- Stress testing, VaR
- Output: `{ approved, risk_score, warnings }`

### Portfolio agent
- Rebalance, optimize, allocate
- Methods: mean-variance, risk parity, Black-Litterman
- Output: weight vector

### Macro agent
- Rates, inflation, sector rotation
- Inputs: FRED data, economic news
- Output: macro outlook by sector

### Execution agent
- Paper trading simulation
- Slippage, timing, liquidity
- Output: simulated fill prices

## Communication

Agents communicate via events (Kafka topics in Phase 9):
- `agent.tasks` — supervisor delegates
- `agent.responses` — agent output
- `agent.memory` — shared context updates
- `agent.consensus` — consensus engine input

NEVER call agents synchronously from each other. That creates tight coupling and breaks observability.

## Memory architecture

| Type | Purpose | Store |
|------|---------|-------|
| Short-term | Current workflow | Redis |
| Long-term | Knowledge base | pgvector |
| Episodic | Past decisions | Postgres + pgvector |
| Semantic | Financial concepts | pgvector + RAG |

## RAG pipeline

```
Documents (SEC filings, news, reports)
    ↓ chunking (LlamaIndex)
    ↓ embeddings (OpenAI text-embedding-3-small or BGE)
    ↓ storage (pgvector)
    ↓ retrieval (top-k by cosine similarity)
    ↓ reranking (optional, BGE reranker)
    ↓ context injection
    ↓ LLM response
```

## Consensus engine

Combines multiple agent outputs into one decision:

```python
final_score = (
    weights["research"] * scores["research"] +
    weights["sentiment"] * scores["sentiment"] +
    weights["risk"] * scores["risk"] +
    weights["macro"] * scores["macro"] +
    weights["rl"] * scores["rl"]
)

if final_score > buy_threshold and risk_score < max_risk:
    decision = "BUY"
```

## AI debate system (advanced)

Bull agent + Bear agent + Risk agent → Supervisor.
Reduces single-agent overconfidence by forcing adversarial reasoning.

```
Question
   ↓
Bull thesis + Bear thesis (parallel)
   ↓
Risk agent reviews both
   ↓
Supervisor weights and decides
```

## Tool-calling architecture

Always use tools, never let agents hallucinate data.

```
Agent → Tool Router → External API → Structured Result → LLM Reasoning
```

Build via:
- LangGraph tool nodes (Phase 6+)
- MCP servers (Phase 9+, when you want tools cross-process)

## Safety / human-in-the-loop

**Never autonomous execution.** Even if you build full multi-agent automation:

```
AI Recommendation → Human Approval → Paper Execution → Logging
```

Hard limits enforced **outside** the agent (in code, not prompts):
- Position size cap
- Sector exposure cap
- Drawdown cap
- Turnover cap

## Observability

For each agent, track:
- Latency (per call)
- Tool call count
- Token usage (cost)
- Hallucination rate (sample-checked)
- Decision quality (vs paper-trading outcome over time)

Tools: LangSmith, Phoenix, or just structured logs to Logtail.

## Mistakes to avoid

- ❌ One giant agent that does everything
- ❌ Letting agents trade unrestricted
- ❌ Skipping memory systems
- ❌ Skipping tool grounding (causing hallucinations)
- ❌ Skipping risk validation
- ❌ Adding agents because it sounds cool, not because tasks are parallelizable

## Most important advice

**Don't start multi-agent.** Build:

```
AI Assistant (Phase 6, single agent + tools)
    ↓
AI Copilot (Phase 6, with deeper context)
    ↓
Workflow Automation (Phase 8, scheduled agent tasks)
    ↓
Multi-Agent Collaboration (Phase 9)
    ↓
Semi-Autonomous Intelligence (Phase 10+)
```

## See also

- [Phase 6 tasks](../phases/phase-6.md)
- [Phase 9 tasks](../phases/phase-9.md)
- [Agent architecture](../architecture/06-agent-design.md)
