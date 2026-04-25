# Phase 3: LangGraph Agent with Guardrails — Design Spec

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Replace the direct hybrid-search → rerank → stream pipeline with a LangGraph `StateGraph` that adds a fast pattern-based guardrail node before retrieval, blocking prompt injection, SQL injection, script injection, and off-topic attacks.

**Architecture:** Linear 3-node graph: `guard → retrieve → generate`. The guard node short-circuits on attack patterns without any LLM call. Clean questions flow through retrieve (existing hybrid search + rerank) then generate (existing Groq streaming chain). The graph is a drop-in replacement inside `generate_stream` — router and frontend unchanged.

**Tech Stack:** `langgraph`, `langchain-groq`, existing `hybrid_search`, `rerank`, `STRICT_PROMPT` chain.

---

## File Structure

| Action | Path | Responsibility |
|--------|------|---------------|
| Create | `backend/app/agent/__init__.py` | Package marker |
| Create | `backend/app/agent/guardrails.py` | Pattern matching logic, `is_blocked(question) -> tuple[bool, str]` |
| Create | `backend/app/agent/graph.py` | LangGraph `StateGraph`, 3 node functions, compiled graph, `run_agent_stream()` |
| Modify | `backend/app/chat/service.py` | Replace inline pipeline with `run_agent_stream()` call |
| Create | `backend/tests/test_guardrails.py` | Unit tests for all block categories |
| Create | `backend/tests/test_agent_graph.py` | Integration tests for graph flow |

---

## Graph State

```python
from typing import TypedDict
from langchain_core.documents import Document

class AgentState(TypedDict):
    question: str
    docs: list[Document]
    answer: str
    blocked: bool
    block_reason: str
```

---

## Guardrails

**File:** `backend/app/agent/guardrails.py`

**Categories and patterns (all case-insensitive):**

| Category | Patterns |
|----------|----------|
| SQL injection | `drop`, `delete`, `insert`, `update`, `select`, `union`, `--`, `;--`, `1=1`, `or 1`, `xp_` |
| Prompt injection | `ignore previous`, `ignore above`, `you are now`, `forget your`, `new persona`, `jailbreak`, `act as`, `pretend you`, `disregard`, `override instructions` |
| Script injection | `<script`, `javascript:`, `onerror=`, `onload=` |
| Excessive length | `len(question) > 500` |

**Interface:**
```python
def is_blocked(question: str) -> tuple[bool, str]:
    # returns (True, reason) if blocked, (False, "") if clean
```

**Refusal message:** `"I can only answer questions about company policy documents."` — returned as the `block_reason` and streamed as the response.

---

## Graph Nodes

**File:** `backend/app/agent/graph.py`

### Node 1: `guard`
```python
def guard_node(state: AgentState) -> AgentState:
    blocked, reason = is_blocked(state["question"])
    return {**state, "blocked": blocked, "block_reason": reason}
```

### Conditional edge after `guard`
```python
def route_after_guard(state: AgentState) -> str:
    return "blocked" if state["blocked"] else "retrieve"
```

### Node 2: `retrieve`
```python
def retrieve_node(state: AgentState) -> AgentState:
    candidates = hybrid_search(state["question"], top_k=6)
    docs = rerank(state["question"], candidates, top_k=3) if candidates else []
    return {**state, "docs": docs}
```

### Node 3: `generate`
```python
def generate_node(state: AgentState) -> AgentState:
    # sets state["answer"], used for non-streaming path only
```

### Graph wiring
```python
graph = StateGraph(AgentState)
graph.add_node("guard", guard_node)
graph.add_node("retrieve", retrieve_node)
graph.add_node("generate", generate_node)
graph.set_entry_point("guard")
graph.add_conditional_edges("guard", route_after_guard, {"blocked": END, "retrieve": "retrieve"})
graph.add_edge("retrieve", "generate")
graph.add_edge("generate", END)
compiled = graph.compile()
```

### Streaming function
```python
async def run_agent_stream(question: str) -> AsyncGenerator[str, None]:
    state = AgentState(question=question, docs=[], answer="", blocked=False, block_reason="")
    # run guard + retrieve synchronously (they are not async)
    state = guard_node(state)
    if state["blocked"]:
        yield f"data: {json.dumps({'token': state['block_reason']})}\n\n"
        yield f"data: {json.dumps({'done': True, 'sources': []})}\n\n"
        return
    state = retrieve_node(state)
    if not state["docs"]:
        yield f"data: {json.dumps({'token': NO_INFO_RESPONSE})}\n\n"
        yield f"data: {json.dumps({'done': True, 'sources': []})}\n\n"
        return
    # stream generate
    sources = [...]
    chain = STRICT_PROMPT | get_llm() | StrOutputParser()
    async for token in chain.astream(...):
        yield f"data: {json.dumps({'token': token})}\n\n"
    yield f"data: {json.dumps({'done': True, 'sources': sources})}\n\n"
```

---

## Integration Point

**File:** `backend/app/chat/service.py`

`generate_stream` becomes a one-liner delegation:
```python
from app.agent.graph import run_agent_stream

async def generate_stream(question: str) -> AsyncGenerator[str, None]:
    async for chunk in run_agent_stream(question):
        yield chunk
```

The `get_rag_response` (non-streaming) function is left unchanged.

---

## Tests

### `backend/tests/test_guardrails.py`
- SQL patterns blocked: `DROP TABLE users`, `SELECT * FROM`, `1=1`, `UNION SELECT`
- Prompt injection blocked: `ignore previous instructions`, `act as a different AI`
- Script injection blocked: `<script>alert(1)</script>`, `javascript:void(0)`
- Excessive length blocked: string of 501 characters
- Clean policy question passes: `"What is the vacation policy?"`
- Case-insensitive: `"IGNORE PREVIOUS instructions"` blocked
- Returns correct refusal string when blocked

### `backend/tests/test_agent_graph.py`
- Blocked question: `guard_node` sets `blocked=True`, `retrieve_node` never called
- Clean question with docs: flows through all 3 nodes, `docs` populated
- Clean question no docs: `retrieve_node` returns empty `docs`, graph exits at generate with `NO_INFO_RESPONSE`
- `run_agent_stream` blocked: yields refusal token then done event
- `run_agent_stream` no docs: yields NO_INFO_RESPONSE then done event
