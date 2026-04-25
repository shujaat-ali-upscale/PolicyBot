from sqlalchemy import create_engine, text
from langchain_core.documents import Document
from langchain_postgres import PGVector

from app.config import settings
from app.rag.embeddings import get_embeddings

COLLECTION_NAME = "policy_chunks"


def get_vector_store() -> PGVector:
    return PGVector(
        embeddings=get_embeddings(),
        collection_name=COLLECTION_NAME,
        connection=settings.sync_database_url,
        use_jsonb=True,
    )


def _delete_by_document_id(document_id: str) -> None:
    engine = create_engine(settings.sync_database_url)
    with engine.begin() as conn:
        conn.execute(
            text("""
                DELETE FROM langchain_pg_embedding e
                USING langchain_pg_collection c
                WHERE e.collection_id = c.uuid
                  AND c.name = :collection
                  AND e.cmetadata->>'document_id' = :doc_id
            """),
            {"collection": COLLECTION_NAME, "doc_id": document_id},
        )


def upsert_chunks(chunks: list[Document], document_id: str) -> int:
    _delete_by_document_id(document_id)
    store = get_vector_store()
    store.add_documents(chunks)
    return len(chunks)


def similarity_search_ranked(query: str, k: int = 10) -> list[tuple[Document, int]]:
    store = get_vector_store()
    docs = store.similarity_search(query, k=k)
    return [(doc, rank + 1) for rank, doc in enumerate(docs)]


def delete_document_chunks(document_id: str) -> None:
    _delete_by_document_id(document_id)
