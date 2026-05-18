# Phase 9 — Multi-Agent Hedge Fund

**Duration:** ~4 weeks
**Goal:** LangGraph-based supervisor + specialized agents with consensus engine.

> Read [step-07](../plan/step-07-multi-agent.md) and [step-16](../plan/step-16-agent-workflows.md). Honest framing matters here.

## Reality check
Multi-agent systems are harder to get right than they look. A single well-prompted agent often outperforms a chain. Build this for:
- Auditability (clear separation of concerns)
- Adversarial reasoning (bull vs bear)
- Specialized memory and tooling

If you find that adding more agents makes outputs worse, simplify. That's normal.

## Acceptance criteria
- [ ] Supervisor agent that delegates to specialized sub-agents
- [ ] At least 3 sub-agents: Research, Risk, Portfolio
- [ ] Consensus engine combining outputs
- [ ] All decisions go through human approval (no autonomous execution)
- [ ] Workflow execution traces visible in UI (LangSmith-style)
- [ ] Agent memory: short-term in Redis, long-term in pgvector

## Task list

### Week 1: Sub-agents
- [ ] Refactor `services/agent-service/` for multiple agents
- [ ] Research agent (extends Phase 6 single agent)
- [ ] Risk agent (validates against limits, computes VaR)
- [ ] Portfolio agent (uses Phase 7 optimization)

### Week 2: Supervisor
- [ ] `app/agents/supervisor_agent.py` with LangGraph state machine
- [ ] Task planner → parallel sub-agent calls → consensus → output
- [ ] Conflict resolution: when agents disagree, escalate to user

### Week 3: Memory + observability
- [ ] Long-term memory: research reports indexed in pgvector
- [ ] Episodic memory: agent decisions + outcomes for learning
- [ ] LangSmith integration (or Phoenix) for trace visualization

### Week 4: UI + safety
- [ ] `/agents` workflow visualization
- [ ] Trace inspector: see each agent's reasoning, tool calls, time, tokens
- [ ] Approval flow: every recommendation requires human click before paper execution
- [ ] Hard limits enforced in code (not prompts): position size, sector cap, drawdown stop

## Out of scope
- ❌ Autonomous execution (never)
- ❌ Custom agent frameworks (use LangGraph)
- ❌ Fine-tuned agents (Phase 10+ if ever)

## Pitfalls
- **Cascading errors.** Agent N consumes agent N-1's output, errors compound. Design for graceful failure.
- **Token cost explosion.** A 5-agent workflow can be 10x the cost of a single agent. Cache aggressively, use small models for routing.
- **Latency.** Sequential agents = slow UX. Parallelize when possible.
- **"Agent" theater.** Don't add agents that don't do meaningfully different work. If two "agents" share most context and tools, they should be one.
