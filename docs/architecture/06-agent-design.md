# AI Agent Design

> Phase 6 (single agent), Phase 9 (multi-agent). See [step-07](../plan/step-07-multi-agent.md) and [step-16](../plan/step-16-agent-workflows.md).

## Core design principles

1. **Tools, not hallucinations.** Every fact comes from a tool call. The LLM synthesizes; it doesn't invent prices.
2. **Citations always.** Every claim links to a source.
3. **Bounded autonomy.** Hard limits enforced in code, not prompts.
4. **Observability first.** Every reasoning step logged.
5. **Graceful failure.** A failed sub-agent does not crash the supervisor.
6. **Cost discipline.** Cache, batch, use small models for routing, big models for synthesis.

## Phase 6: single agent

```
                  user query
                      │
                      ▼
              ┌──────────────────┐
              │  research_agent  │  (LangGraph state machine)
              └────────┬─────────┘
                       │
           ┌───────────┼───────────┐
           ▼           ▼           ▼
      market_tool  news_tool   rag_tool   portfolio_tool
           │           │           │           │
           └───────────┴────┬──────┴───────────┘
                            ▼
                       synthesizer
                            │
                            ▼
                  streaming response + citations
```

### State machine

```python
class ResearchState(TypedDict):
    query: str
    plan: list[str]
    tool_results: dict[str, Any]
    citations: list[Citation]
    response: str

graph = StateGraph(ResearchState)
graph.add_node("plan", plan_node)
graph.add_node("tools", tool_node)         # parallel tool calls
graph.add_node("synthesize", synth_node)
graph.add_edge(START, "plan")
graph.add_edge("plan", "tools")
graph.add_edge("tools", "synthesize")
graph.add_edge("synthesize", END)
```

### Tools

| Tool | Operations |
|------|-----------|
| `market_tool` | `get_price(symbol)`, `get_candles(symbol, tf, range)` |
| `news_tool` | `search(query, since)`, `get_for_symbol(symbol)` |
| `rag_tool` | `query_filings(question, symbol)`, `query_research(question)` |
| `portfolio_tool` | `get_holdings(user_id)`, `get_metrics(user_id, range)` |
| `signals_tool` | `get_signals(symbol, since)` |

Each tool returns structured Pydantic objects. The LLM consumes them via JSON schema.

### Prompt template (system)

```
You are a financial research assistant for the quant-os platform.

Rules:
- You provide ANALYSIS, never investment advice.
- Refuse "should I buy" questions; offer factual analysis instead.
- ALL factual claims MUST come from tool calls. Never invent prices, dates, or numbers.
- ALWAYS cite sources for facts.
- If you don't have a tool for something, say so.
- If a tool returns an error, surface it to the user.

Tools available: ...
```

## Phase 9: multi-agent

```
                    supervisor (CIO)
                          │
              plan + delegate
                          │
        ┌─────────┬───────┼───────┬─────────┐
        ▼         ▼       ▼       ▼         ▼
    research   sentiment  risk  portfolio  macro
                                            │
                                       (Phase 7 optimization)
                          │
                  consensus engine
                          │
                          ▼
                  recommendation + reasoning
                          │
                  human approval gate
                          │
                          ▼
                  paper execution + log
```

### Communication

**Phase 9 MVP:** in-process function calls between agents (LangGraph nodes).
**Phase 11+:** event-based via Kafka topics (`agent.tasks`, `agent.responses`).

### Memory architecture

| Type | Storage | Use |
|------|---------|-----|
| Short-term | Redis | current workflow state |
| Conversation | Postgres | message history per user |
| Long-term semantic | pgvector | research reports, filings |
| Episodic | Postgres | past decisions + outcomes |

### Consensus engine

Weighted scoring:
```python
final_score = sum(w[a] * scores[a] for a in agents)
decision = (
    "BUY"  if final_score > buy_threshold and risk_ok else
    "SELL" if final_score < sell_threshold and risk_ok else
    "HOLD"
)
```

Weights tuned empirically; expose them in admin UI for tuning.

### Adversarial reasoning (advanced)

Bull agent + Bear agent + Risk agent argue → Supervisor decides. Reduces single-agent overconfidence. Use only when you have measurable improvement vs single-agent baseline.

## Cost management

| Action | Mitigation |
|--------|-----------|
| Embedding re-generation | Cache by content hash |
| LLM tool routing | Use cheap model (gpt-4o-mini, claude-haiku) |
| Synthesis | Use smart model (gpt-4o, claude-sonnet) only for final output |
| Repeated queries | Redis cache with TTL on common questions |
| Long contexts | Truncate aggressively; summarize old turns |

Track cost per user and per conversation. Alert on outliers.

## Observability

Use LangSmith or Phoenix:
- Every LangGraph run produces a trace
- Each tool call logged with input/output/latency
- Token counts and costs tracked per node
- Errors and retries visible

Without this you cannot debug agent regressions.

## Hallucination defense

1. Tool grounding (most important)
2. Citation requirements (system prompt + post-processing check)
3. Self-consistency (run twice with temperature 0.2, compare)
4. Refusal training (system prompt: refuse rather than invent)

## Safety

Hardcoded refusals (in middleware, not prompts):
- "Should I buy/sell X" → response template: "I don't give investment advice. Here's the analysis..."
- Specific tickers on regulatory watch lists → flag
- Personal info requests → refuse

Rate limits:
- 30 messages / minute / user
- 200 tool calls / hour / user
- $5 LLM cost / day / user (initial limit; raise as you confirm value)

## Anti-patterns

- ❌ Letting agents write to portfolios autonomously
- ❌ Multiple agents that share most context (just be one agent)
- ❌ Skipping memory entirely (no continuity = poor UX)
- ❌ Putting risk limits in prompts ("don't exceed 25%") — enforce in code
- ❌ Storing prompts in DB and editing live (version-control them)
