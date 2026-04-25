from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.database import get_db
from app.documents.schemas import DocumentStatus, UploadResponse
from app.documents.service import delete_document_by_id, get_document_status, process_pdf
from app.models import User

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    file_bytes = await file.read()
    result = await process_pdf(file_bytes, file.filename, db)
    return UploadResponse(
        success=True,
        message="Document processed successfully",
        chunks_created=result["chunk_count"],
        document_id=result["document_id"],
    )


@router.get("/status", response_model=DocumentStatus)
async def document_status(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    status = await get_document_status(db)
    return DocumentStatus(**status)


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    await delete_document_by_id(document_id, db)
    return {"success": True, "message": "Document deleted successfully"}
