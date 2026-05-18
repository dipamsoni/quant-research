# Phase 6 — AI Research Assistant ← **MVP COMPLETE**

**Duration:** ~4 weeks
**Goal:** LangGraph-based research agent with RAG over financial documents. End of MVP.

> Read [step-07](../plan/step-07-multi-agent.md) and [step-16](../plan/step-16-agent-workflows.md). For Phase 6, build **one** good agent — multi-agent comes in Phase 9.

## Acceptance criteria

- [ ] User can chat with an AI assistant about any tracked asset
- [ ] Assistant has access to: market data, portfolio data, news, SEC filings (RAG)
- [ ] Responses include citations to specific documents/data points
- [ ] Streaming responses (token-by-token)
- [ ] Conversation history persisted; user can resume
- [ ] Assistant refuses to give investment advice; sticks to analysis
- [ ] Chat works on the dashboard via CMD+K palette and a dedicated `/research` route

## Task list

### Week 1: Foundations
- [ ] `services/agent-service/` scaffold (or as a module if still semi-monolithic)
- [ ] Tables: `agent_conversations`, `agent_messages`, `research_reports`, `news_embeddings` (pgvector)
- [ ] Install: langgraph, langchain, llama-index, pgvector, openai (or anthropic)
- [ ] Add `pgvector` extension to Postgres
- [ ] Embeddings model: `text-embedding-3-small` (OpenAI) or `BAAI/bge-small-en-v1.5` (local, free)

### Week 2: RAG ingestion
- [ ] `app/retrieval/ingestion.py` — chunk + embed news articles, store in pgvector
- [ ] SEC filings ingestion: pull 10-K, 10-Q, 8-K from SEC EDGAR for tracked tickers
- [ ] Background job: re-embed new articles every hour
- [ ] `app/retrieval/search.py` — semantic search by similarity, filter by date/symbol
- [ ] Reranker (optional): BGE reranker for top-k → top-n refinement

### Week 3: Agent + tools
- [ ] `app/tools/market_tool.py` — `get_price`, `get_candles`
- [ ] `app/tools/portfolio_tool.py` — `get_holdings`, `get_metrics`
- [ ] `app/tools/news_tool.py` — `search_news`
- [ ] `app/tools/rag_tool.py` — `query_filings(question, symbol)`
- [ ] `app/tools/signals_tool.py` — `get_signals`
- [ ] `app/agents/research_agent.py` — LangGraph state machine: plan → tool calls (parallel) → synthesize → cite
- [ ] System prompt explicitly says: "You provide analysis, not investment advice. Always cite sources."

### Week 4: API + UI
- [ ] `POST /api/v1/agents/chat` — streaming endpoint (SSE)
- [ ] `GET /api/v1/agents/conversations` — list user's conversations
- [ ] `GET /api/v1/agents/conversations/{id}` — full history
- [ ] Frontend: `/research` route with chat UI, shadcn-style
- [ ] CMD+K integration: ask AI from anywhere
- [ ] Citations rendered as clickable badges → open source
- [ ] Streaming token display
- [ ] Acceptance check; tag; **MVP complete**

## Out of scope

- ❌ Multi-agent supervisor (Phase 9)
- ❌ Autonomous workflows (Phase 9)
- ❌ Fine-tuned finance LLMs (Phase 10+)
- ❌ Voice interface

## Open-source

- **LangGraph** — orchestration
- **LlamaIndex** — RAG (chunking, retrievers)
- **pgvector** — vector store
- **OpenAI / Anthropic** — LLM
- **BGE** — embeddings if you want free/local

## Pitfalls

- **Hallucinations.** Without good tool grounding the assistant will invent stock prices. Always tool-call for facts.
- **Citation laziness.** Force citations in the system prompt and in your post-processing.
- **Context window blowout.** Don't dump 50 SEC filings into context. Use RAG with top-5 chunks.
- **Investment advice liability.** Make the disclaimer explicit; refuse "should I buy" questions.
- **Cost runaway.** Cache embeddings. Use cheap models (gpt-4o-mini, claude-haiku) for tool routing; reserve big models for synthesis.
- **PII / data leakage.** Don't send portfolio data to the LLM if you can avoid it; or at least let the user opt in.

## MVP COMPLETE

At this point you have:
- ✅ Live market dashboard
- ✅ Portfolio analytics
- ✅ ML-driven trading signals
- ✅ Backtesting platform
- ✅ AI research assistant

This is a complete, demo-able, useful product. **Stop and get users.** Phases 7–12 are upside, not requirements.
