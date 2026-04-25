import hashlib
from langchain_core.documents import Document
from app.rag.hybrid_search import reciprocal_rank_fusion, hybrid_search


def _doc(content: str) -> Document:
    return Document(page_content=content, metadata={})


def _key(doc: Document) -> str:
    return hashlib.md5(doc.page_content.encode()).hexdigest()


def test_rrf_boosts_docs_appearing_in_both_lists():
    shared = _doc("shared content")
    only_vector = _doc("only in vector")
    only_fulltext = _doc("only in fulltext")

    vector_results = [(shared, 1), (only_vector, 2)]
    fulltext_results = [(shared, 1), (only_fulltext, 2)]

    merged = reciprocal_rank_fusion(vector_results, fulltext_results, top_k=3)

    assert merged[0].page_content == "shared content"


def test_rrf_respects_top_k():
    docs = [(_doc(f"doc{i}"), i + 1) for i in range(8)]
    merged = reciprocal_rank_fusion(docs, [], top_k=4)
    assert len(merged) == 4


def test_rrf_empty_inputs_returns_empty():
    result = reciprocal_rank_fusion([], [], top_k=6)
    assert result == []


def test_rrf_single_list():
    docs = [(_doc("a"), 1), (_doc("b"), 2), (_doc("c"), 3)]
    merged = reciprocal_rank_fusion(docs, [], top_k=6)
    assert len(merged) == 3
    assert merged[0].page_content == "a"


def test_hybrid_search_calls_both_retrievers(monkeypatch):
    from unittest.mock import MagicMock, patch

    vec_doc = _doc("vector result")
    ft_doc = _doc("fulltext result")

    with patch("app.rag.hybrid_search.similarity_search_ranked", return_value=[(vec_doc, 1)]) as mock_vec, \
         patch("app.rag.hybrid_search.fulltext_search", return_value=[(ft_doc, 1)]) as mock_ft:

        results = hybrid_search("test query", top_k=6)

    mock_vec.assert_called_once_with("test query", k=10)
    mock_ft.assert_called_once_with("test query", k=10)
    assert len(results) <= 6
