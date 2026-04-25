from langchain_core.documents import Document

from app.chat.schemas import Source
from app.rag.chain import generate_answer
from app.rag.vector_store import similarity_search

NO_INFO_RESPONSE = "I don't have information about that in the policy document."


async def get_rag_response(question: str) -> dict:
    docs: list[Document] = similarity_search(question, k=4)

    if not docs:
        return {"answer": NO_INFO_RESPONSE, "sources": []}

    answer = await generate_answer(question, docs)
    sources = [
        Source(
            text=doc.page_content[:300],
            chunk_index=doc.metadata.get("chunk_index", 0),
        )
        for doc in docs
    ]
    return {"answer": answer, "sources": sources}
