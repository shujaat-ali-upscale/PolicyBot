import os
import tempfile
import uuid

from langchain_core.documents import Document
from pypdf import PdfReader
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PolicyDocument
from app.documents.chunker import chunk_document
from app.rag.vector_store import delete_document_chunks, upsert_chunks


async def process_pdf(file_bytes: bytes, filename: str, db: AsyncSession) -> dict:
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        reader = PdfReader(tmp_path)
        pages = [
            (page.extract_text() or "", page_num + 1)
            for page_num, page in enumerate(reader.pages)
        ]
    finally:
        os.unlink(tmp_path)

    all_text = "".join(text for text, _ in pages).strip()
    if not all_text:
        raise ValueError("PDF appears to be empty or unreadable")

    doc_id = str(uuid.uuid4())
    chunks = chunk_document(pages)

    for chunk in chunks:
        chunk.metadata["document_id"] = doc_id
        chunk.metadata["filename"] = filename

    chunk_count = upsert_chunks(chunks, document_id=doc_id)

    existing = await db.execute(
        select(PolicyDocument).where(PolicyDocument.filename == filename)
    )
    existing_doc = existing.scalar_one_or_none()

    if existing_doc:
        existing_doc.document_id = doc_id
        existing_doc.chunk_count = chunk_count
        existing_doc.file_size = len(file_bytes)
    else:
        db.add(PolicyDocument(
            document_id=doc_id,
            filename=filename,
            chunk_count=chunk_count,
            file_size=len(file_bytes),
        ))

    await db.commit()
    return {"chunk_count": chunk_count, "document_id": doc_id}


async def get_document_status(db: AsyncSession) -> dict:
    result = await db.execute(
        select(PolicyDocument).order_by(PolicyDocument.uploaded_at.desc())
    )
    docs = result.scalars().all()

    if not docs:
        return {"has_documents": False, "documents": []}

    return {
        "has_documents": True,
        "documents": [
            {
                "document_id": doc.document_id,
                "filename": doc.filename,
                "chunk_count": doc.chunk_count,
                "file_size": doc.file_size,
                "uploaded_at": doc.uploaded_at,
            }
            for doc in docs
        ],
    }


async def delete_document_by_id(document_id: str, db: AsyncSession) -> None:
    delete_document_chunks(document_id)
    await db.execute(
        delete(PolicyDocument).where(PolicyDocument.document_id == document_id)
    )
    await db.commit()
