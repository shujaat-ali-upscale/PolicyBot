import json
from typing import AsyncGenerator, TypedDict

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser

from app.agent.guardrails import is_blocked, REFUSAL_MESSAGE
from app.rag.chain import STRICT_PROMPT, format_docs, get_llm
from app.rag.hybrid_search import hybrid_search
from app.rag.reranker import rerank

NO_INFO_RESPONSE = "I don't have information about that in the policy document."


class AgentState(TypedDict):
    question: str
    docs: list[Document]
    answer: str
    blocked: bool
    block_reason: str


def guard_node(state: AgentState) -> AgentState:
    blocked, reason = is_blocked(state["question"])
    return {**state, "blocked": blocked, "block_reason": reason}


def retrieve_node(state: AgentState) -> AgentState:
    candidates: list[Document] = hybrid_search(state["question"], top_k=6)
    docs = rerank(state["question"], candidates, top_k=3) if candidates else []
    return {**state, "docs": docs}


def _build_sources(docs: list[Document]) -> list[dict]:
    return [
        {
            "text": doc.page_content[:300],
            "chunk_index": doc.metadata.get("chunk_index", 0),
            "filename": doc.metadata.get("filename", "Unknown"),
            "page_number": doc.metadata.get("page_number"),
        }
        for doc in docs
    ]


async def run_agent_stream(question: str) -> AsyncGenerator[str, None]:
    state = AgentState(
        question=question,
        docs=[],
        answer="",
        blocked=False,
        block_reason="",
    )

    state = guard_node(state)
    if state["blocked"]:
        yield f"data: {json.dumps({'token': state['block_reason']})}\n\n"
        yield f"data: {json.dumps({'done': True, 'sources': []})}\n\n"
        return

    try:
        state = retrieve_node(state)
    except Exception:
        yield f"data: {json.dumps({'token': 'Sorry, something went wrong while searching. Please try again.'})}\n\n"
        yield f"data: {json.dumps({'done': True, 'sources': []})}\n\n"
        return

    if not state["docs"]:
        yield f"data: {json.dumps({'token': NO_INFO_RESPONSE})}\n\n"
        yield f"data: {json.dumps({'done': True, 'sources': []})}\n\n"
        return

    sources = _build_sources(state["docs"])
    chain = STRICT_PROMPT | get_llm() | StrOutputParser()
    async for token in chain.astream({"context": format_docs(state["docs"]), "question": question}):
        yield f"data: {json.dumps({'token': token})}\n\n"

    yield f"data: {json.dumps({'done': True, 'sources': sources})}\n\n"
