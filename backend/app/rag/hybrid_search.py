import hashlib

from langchain_core.documents import Document

from app.rag.fulltext_search import fulltext_search
from app.rag.vector_store import similarity_search_ranked

_RRF_K = 60


def reciprocal_rank_fusion(
    vector_results: list[tuple[Document, int]],
    fulltext_results: list[tuple[Document, int]],
    top_k: int = 6,
) -> list[Document]:
    scores: dict[str, float] = {}
    docs: dict[str, Document] = {}

    for doc, rank in vector_results + fulltext_results:
        key = hashlib.md5(doc.page_content.encode()).hexdigest()
        scores[key] = scores.get(key, 0.0) + 1.0 / (rank + _RRF_K)
        docs[key] = doc

    sorted_keys = sorted(scores, key=lambda k: scores[k], reverse=True)
    return [docs[k] for k in sorted_keys[:top_k]]


def hybrid_search(query: str, top_k: int = 6) -> list[Document]:
    vector_results = similarity_search_ranked(query, k=10)
    fulltext_results = fulltext_search(query, k=10)
    return reciprocal_rank_fusion(vector_results, fulltext_results, top_k=top_k)
