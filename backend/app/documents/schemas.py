from datetime import datetime
from pydantic import BaseModel


class UploadResponse(BaseModel):
    success: bool
    message: str
    chunks_created: int
    document_id: str


class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    chunk_count: int
    file_size: int
    uploaded_at: datetime


class DocumentStatus(BaseModel):
    has_documents: bool
    documents: list[DocumentInfo] = []
