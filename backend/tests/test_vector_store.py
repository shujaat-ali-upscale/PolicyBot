from unittest.mock import MagicMock, patch
from langchain_core.documents import Document
from app.rag.vector_store import upsert_chunks, delete_document_chunks, similarity_search_ranked


def _make_doc(content: str, doc_id: str = "abc") -> Document:
    return Document(page_content=content, metadata={"document_id": doc_id})


def test_upsert_chunks_deletes_existing_and_adds_new():
    chunks = [_make_doc("chunk1"), _make_doc("chunk2")]

    with patch("app.rag.vector_store.get_vector_store") as mock_get_store, \
         patch("app.rag.vector_store._delete_by_document_id") as mock_delete:
        mock_store = MagicMock()
        mock_get_store.return_value = mock_store

        count = upsert_chunks(chunks, document_id="abc")

    mock_delete.assert_called_once_with("abc")
    mock_store.add_documents.assert_called_once_with(chunks)
    assert count == 2


def test_similarity_search_ranked_returns_tuples():
    mock_doc = Document(page_content="test", metadata={})

    with patch("app.rag.vector_store.get_vector_store") as mock_get_store:
        mock_store = MagicMock()
        mock_store.similarity_search.return_value = [mock_doc]
        mock_get_store.return_value = mock_store

        results = similarity_search_ranked("query", k=10)

    assert results == [(mock_doc, 1)]


def test_similarity_search_ranked_assigns_sequential_ranks():
    docs = [Document(page_content=f"doc{i}", metadata={}) for i in range(3)]

    with patch("app.rag.vector_store.get_vector_store") as mock_get_store:
        mock_store = MagicMock()
        mock_store.similarity_search.return_value = docs
        mock_get_store.return_value = mock_store

        results = similarity_search_ranked("query", k=10)

    ranks = [r for _, r in results]
    assert ranks == [1, 2, 3]
