from unittest.mock import MagicMock, patch
from langchain_core.documents import Document
from app.rag.reranker import rerank, load_reranker


def _doc(content: str) -> Document:
    return Document(page_content=content, metadata={})


def test_rerank_returns_top_k():
    chunks = [_doc(f"chunk {i}") for i in range(6)]

    with patch("app.rag.reranker._get_model") as mock_model_fn:
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.9, 0.1, 0.8, 0.2, 0.7, 0.3]
        mock_model_fn.return_value = mock_model

        result = rerank("query", chunks, top_k=3)

    assert len(result) == 3


def test_rerank_sorts_by_score_descending():
    chunks = [_doc("low relevance"), _doc("high relevance"), _doc("medium relevance")]
    scores = [0.1, 0.9, 0.5]

    with patch("app.rag.reranker._get_model") as mock_model_fn:
        mock_model = MagicMock()
        mock_model.predict.return_value = scores
        mock_model_fn.return_value = mock_model

        result = rerank("query", chunks, top_k=3)

    assert result[0].page_content == "high relevance"
    assert result[1].page_content == "medium relevance"
    assert result[2].page_content == "low relevance"


def test_rerank_passes_correct_pairs_to_model():
    chunks = [_doc("content A"), _doc("content B")]

    with patch("app.rag.reranker._get_model") as mock_model_fn:
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.5, 0.8]
        mock_model_fn.return_value = mock_model

        rerank("my question", chunks, top_k=2)

    call_args = mock_model.predict.call_args[0][0]
    assert call_args == [["my question", "content A"], ["my question", "content B"]]


def test_rerank_empty_chunks_returns_empty():
    result = rerank("query", [], top_k=3)
    assert result == []
