import os
import tempfile

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from pypdf import PdfReader
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PolicyDocument
from app.rag.vector_store import delete_all_chunks, upsert_chunks

TEXT_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
    separators=["\n\n", "\n", ". ", " ", ""],
)


async def process_pdf(file_bytes: bytes, filename: str, db: AsyncSession) -> int:
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        reader = PdfReader(tmp_path)
        full_text = "\n\n".join(
            page.extract_text() or "" for page in reader.pages
        ).strip()
    finally:
        os.unlink(tmp_path)

    if not full_text:
        raise ValueError("PDF appears to be empty or unreadable")

    raw_doc = Document(page_content=full_text, metadata={"source": filename})
    chunks = TEXT_SPLITTER.split_documents([raw_doc])
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i

    chunk_count = upsert_chunks(chunks)

    await db.execute(delete(PolicyDocument))
    db.add(PolicyDocument(filename=filename, chunk_count=chunk_count))
    await db.commit()

    return chunk_count


async def get_document_status(db: AsyncSession) -> dict:
    result = await db.execute(
        select(PolicyDocument).order_by(PolicyDocument.uploaded_at.desc()).limit(1)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        return {"has_document": False}
    return {
        "has_document": True,
        "filename": doc.filename,
        "chunk_count": doc.chunk_count,
        "uploaded_at": doc.uploaded_at,
    }


async def delete_document(db: AsyncSession) -> None:
    delete_all_chunks()
    await db.execute(delete(PolicyDocument))
    await db.commit()
