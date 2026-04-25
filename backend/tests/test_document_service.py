import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.documents.service import process_pdf, get_document_status, delete_document_by_id


@pytest.mark.asyncio
async def test_process_pdf_returns_chunk_count_and_document_id():
    mock_db = AsyncMock()
    fake_pdf_bytes = b"%PDF-1.4 fake"

    with patch("app.documents.service.PdfReader") as mock_reader_cls, \
         patch("app.documents.service.chunk_document") as mock_chunker, \
         patch("app.documents.service.upsert_chunks") as mock_upsert, \
         patch("app.documents.service.tempfile.NamedTemporaryFile") as mock_tmp, \
         patch("app.documents.service.os.unlink"):

        mock_tmp_file = MagicMock()
        mock_tmp_file.__enter__ = MagicMock(return_value=mock_tmp_file)
        mock_tmp_file.__exit__ = MagicMock(return_value=False)
        mock_tmp_file.name = "/tmp/fake.pdf"
        mock_tmp.return_value = mock_tmp_file

        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "policy content"
        mock_reader.pages = [mock_page]
        mock_reader_cls.return_value = mock_reader

        mock_chunker.return_value = [MagicMock(), MagicMock(), MagicMock()]
        mock_upsert.return_value = 3

        mock_execute_result = MagicMock()
        mock_execute_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_execute_result

        result = await process_pdf(fake_pdf_bytes, "policy.pdf", mock_db)

    assert result["chunk_count"] == 3
    assert "document_id" in result
    assert len(result["document_id"]) == 36  # UUID format


@pytest.mark.asyncio
async def test_process_pdf_raises_on_empty_pdf():
    mock_db = AsyncMock()

    with patch("app.documents.service.PdfReader") as mock_reader_cls, \
         patch("app.documents.service.tempfile.NamedTemporaryFile") as mock_tmp, \
         patch("app.documents.service.os.unlink"):

        mock_tmp_file = MagicMock()
        mock_tmp_file.__enter__ = MagicMock(return_value=mock_tmp_file)
        mock_tmp_file.__exit__ = MagicMock(return_value=False)
        mock_tmp_file.name = "/tmp/fake.pdf"
        mock_tmp.return_value = mock_tmp_file

        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""
        mock_reader.pages = [mock_page]
        mock_reader_cls.return_value = mock_reader

        with pytest.raises(ValueError, match="empty or unreadable"):
            await process_pdf(b"%PDF fake", "empty.pdf", mock_db)


@pytest.mark.asyncio
async def test_get_document_status_returns_list():
    mock_db = AsyncMock()

    mock_doc = MagicMock()
    mock_doc.document_id = "abc-123"
    mock_doc.filename = "policy.pdf"
    mock_doc.chunk_count = 10
    mock_doc.file_size = 2048
    mock_doc.uploaded_at = MagicMock()

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_doc]
    mock_db.execute.return_value = mock_result

    status = await get_document_status(mock_db)

    assert status["has_documents"] is True
    assert len(status["documents"]) == 1
    assert status["documents"][0]["filename"] == "policy.pdf"


@pytest.mark.asyncio
async def test_get_document_status_empty():
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    status = await get_document_status(mock_db)
    assert status["has_documents"] is False
    assert status["documents"] == []


@pytest.mark.asyncio
async def test_delete_document_by_id_removes_chunks_and_db_row():
    mock_db = AsyncMock()

    with patch("app.documents.service.delete_document_chunks") as mock_delete_chunks:
        await delete_document_by_id("abc-123", mock_db)

    mock_delete_chunks.assert_called_once_with("abc-123")
    mock_db.execute.assert_called_once()
    mock_db.commit.assert_called_once()
