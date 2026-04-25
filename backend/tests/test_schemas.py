from app.chat.schemas import Source, ChatResponse
from app.documents.schemas import DocumentInfo, DocumentStatus, UploadResponse


def test_source_has_filename_and_page():
    s = Source(text="hello", chunk_index=0, filename="test.pdf", page_number=1)
    assert s.filename == "test.pdf"
    assert s.page_number == 1


def test_source_filename_defaults():
    s = Source(text="hello", chunk_index=0)
    assert s.filename == "Unknown"
    assert s.page_number is None


def test_document_status_empty():
    status = DocumentStatus(has_documents=False)
    assert status.documents == []


def test_upload_response_has_document_id():
    resp = UploadResponse(
        success=True, message="ok", chunks_created=5, document_id="abc-123"
    )
    assert resp.document_id == "abc-123"
