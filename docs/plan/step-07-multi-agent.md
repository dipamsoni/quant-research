# Step 7 — Multi-Agent Hedge Fund Architecture

> Phase 9. Honest framing first, then design.

## Honest framing

The "AI hedge fund" framing is mostly aesthetic. In practice:

- A single well-prompted LLM with good tools often outperforms a chain of 5 specialized agents
- Each agent introduces error, latency, and token cost
- Multi-agent systems shine when tasks are genuinely parallelizable and have clear separation
- Use this when you've validated a single-agent baseline isn't enough

That said — building this is still valuable for:
- Learning agent orchestration
- Producing structured, auditable reasoning
- Adversarial reasoning (bull vs bear) for nuanced decisions

## Agent hierarchy

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

| Agent | Responsibility | Tools |
|-------|----------------|-------|
| Supervisor | Orchestrate, delegate, decide | All sub-agents |
| Research | Equity research, trends | SEC filings, news, market data, RAG |
| Sentiment | News & social analysis | News APIs, FinBERT/LLM |
| Risk | Drawdown, exposure, VaR | Portfolio data, stress test tools |
| Portfolio | Allocation, rebalance | PyPortfolioOpt, optimization |
| Execution | Order placement (paper) | Broker mock |
| Macro | Rates, inflation, sector rotation | FRED data, news |

## Communication: events, not function calls

Use Kafka topics (or Redis Streams during MVP-of-this-phase):

```
agent.tasks
agent.responses
agent.memory
agent.consensus
agent.alerts
```

Agents subscribe to topics and emit events. This decouples them.

## Orchestration framework

**Primary: LangGraph.** Stateful workflows, branching, memory, retries.

**Secondary: CrewAI** for rapid prototyping.

**Avoid:** AutoGen for production until you've evaluated whether its conversation-based model fits your debate use case.

## Memory architecture

| Type | Purpose | Storage |
|------|---------|---------|
| Short-term | Current workflow state | Redis |
| Long-term | Persistent knowledge | pgvector |
| Episodic | Past decisions/outcomes | Postgres + pgvector |
| Semantic | Financial knowledge base | pgvector + RAG |

## RAG pipeline

```
SEC Filings / News / Reports
    ↓
Chunking (LlamaIndex)
    ↓
Embeddings (OpenAI or BGE)
    ↓
pgvector
    ↓
Retrieval + Reranking
    ↓
LLM Context Injection
    ↓
Agent Response
```

## Tool-calling architecture

Agents must use tools, not hallucinate. Build via MCP servers or LangGraph tool nodes:

- `market_tool.get_price(symbol)`
- `portfolio_tool.get_metrics(portfolio_id)`
- `news_tool.search(query)`
- `analytics_tool.factor_exposure(portfolio_id)`
- `backtest_tool.run(strategy)`

## Consensus engine

Combines outputs:

```python
final_score = (
    0.30 * research_score +
    0.20 * sentiment_score +
    0.20 * risk_score +
    0.30 * rl_signal
)
```

Output: `{ decision: BUY, confidence: 0.79, allocation: 0.12 }`

## AI debate system (advanced)

Bull agent vs Bear agent vs Risk agent → Supervisor decides. Reduces single-agent overconfidence.

## Safety

- **Never autonomous execution.** Human-in-the-loop for any real trades.
- Position limits enforced outside the agent (in code, not in prompts)
- All agent decisions logged for audit
- Risk engine validates every recommendation

## Observability

Track per agent:
- Latency
- Tool call count
- Token usage
- Hallucination rate (sample-checked)
- Decision quality (vs paper-trading outcome)

Use LangSmith or Phoenix for trace inspection.

## See also

- [Phase 9 tasks](../phases/phase-9.md)
- [Agent design](../architecture/06-agent-design.md)
