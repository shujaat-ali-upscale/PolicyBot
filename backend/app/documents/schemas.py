from datetime import datetime
from pydantic import BaseModel


class UploadResponse(BaseModel):
    success: bool
    message: str
    chunks_created: int


class DocumentStatus(BaseModel):
    has_document: bool
    filename: str | None = None
    chunk_count: int | None = None
    uploaded_at: datetime | None = None
