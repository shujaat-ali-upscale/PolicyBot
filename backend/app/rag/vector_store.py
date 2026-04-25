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


def upsert_chunks(chunks: list[Document]) -> int:
    store = get_vector_store()
    store.delete_collection()
    store.create_collection()
    store.add_documents(chunks)
    return len(chunks)


def similarity_search(query: str, k: int = 4) -> list[Document]:
    store = get_vector_store()
    return store.similarity_search(query, k=k)


def delete_all_chunks() -> None:
    store = get_vector_store()
    store.delete_collection()
