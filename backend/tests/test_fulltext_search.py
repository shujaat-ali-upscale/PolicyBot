from unittest.mock import MagicMock, patch
from langchain_core.documents import Document


def test_fulltext_search_returns_ranked_tuples():
    mock_row = MagicMock()
    mock_row.document = "policy content about PTO"
    mock_row.cmetadata = {"filename": "hr.pdf", "chunk_index": 0}

    with patch("app.rag.fulltext_search.create_engine") as mock_engine_cls:
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_engine.connect.return_value = mock_conn
        mock_conn.execute.return_value.fetchall.return_value = [mock_row]
        mock_engine_cls.return_value = mock_engine

        from app.rag.fulltext_search import fulltext_search
        results = fulltext_search("PTO policy", k=5)

    assert len(results) == 1
    doc, rank = results[0]
    assert isinstance(doc, Document)
    assert rank == 1
    assert doc.page_content == "policy content about PTO"
    assert doc.metadata["filename"] == "hr.pdf"


def test_fulltext_search_returns_empty_on_no_match():
    with patch("app.rag.fulltext_search.create_engine") as mock_engine_cls:
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_engine.connect.return_value = mock_conn
        mock_conn.execute.return_value.fetchall.return_value = []
        mock_engine_cls.return_value = mock_engine

        from app.rag.fulltext_search import fulltext_search
        results = fulltext_search("xyzabc123", k=5)

    assert results == []
