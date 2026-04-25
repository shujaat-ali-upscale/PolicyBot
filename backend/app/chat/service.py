import json
from typing import AsyncGenerator

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser

from app.rag.chain import STRICT_PROMPT, format_docs, generate_answer, get_llm
from app.rag.hybrid_search import hybrid_search
from app.rag.reranker import rerank

NO_INFO_RESPONSE = "I don't have information about that in the policy document."


async def get_rag_response(question: str) -> dict:
    candidates: list[Document] = hybrid_search(question, top_k=6)
    docs = rerank(question, candidates, top_k=3) if candidates else []

    if not docs:
        return {"answer": NO_INFO_RESPONSE, "sources": []}

    answer = await generate_answer(question, docs)
    sources = [
        {
            "text": doc.page_content[:300],
            "chunk_index": doc.metadata.get("chunk_index", 0),
            "filename": doc.metadata.get("filename", "Unknown"),
            "page_number": doc.metadata.get("page_number"),
        }
        for doc in docs
    ]
    return {"answer": answer, "sources": sources}


async def generate_stream(question: str) -> AsyncGenerator[str, None]:
    try:
        candidates: list[Document] = hybrid_search(question, top_k=6)
        docs = rerank(question, candidates, top_k=3) if candidates else []
    except Exception:
        yield f"data: {json.dumps({'token': 'Sorry, something went wrong while searching. Please try again.'})}\n\n"
        yield f"data: {json.dumps({'done': True, 'sources': []})}\n\n"
        return

    if not docs:
        yield f"data: {json.dumps({'token': NO_INFO_RESPONSE})}\n\n"
        yield f"data: {json.dumps({'done': True, 'sources': []})}\n\n"
        return

    sources = [
        {
            "text": doc.page_content[:300],
            "chunk_index": doc.metadata.get("chunk_index", 0),
            "filename": doc.metadata.get("filename", "Unknown"),
            "page_number": doc.metadata.get("page_number"),
        }
        for doc in docs
    ]

    chain = STRICT_PROMPT | get_llm() | StrOutputParser()
    async for token in chain.astream({"context": format_docs(docs), "question": question}):
        yield f"data: {json.dumps({'token': token})}\n\n"

    yield f"data: {json.dumps({'done': True, 'sources': sources})}\n\n"
