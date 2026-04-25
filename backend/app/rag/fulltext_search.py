from sqlalchemy import create_engine, text
from langchain_core.documents import Document

from app.config import settings
from app.rag.vector_store import COLLECTION_NAME

_FTS_SQL = text("""
    SELECT e.document, e.cmetadata,
           ts_rank(
               to_tsvector('english', e.document),
               plainto_tsquery('english', :query)
           ) AS rank
    FROM langchain_pg_embedding e
    JOIN langchain_pg_collection c ON e.collection_id = c.uuid
    WHERE c.name = :collection
      AND to_tsvector('english', e.document) @@ plainto_tsquery('english', :query)
    ORDER BY rank DESC
    LIMIT :k
""")


def fulltext_search(query: str, k: int = 10) -> list[tuple[Document, int]]:
    engine = create_engine(settings.sync_database_url)
    with engine.connect() as conn:
        rows = conn.execute(
            _FTS_SQL,
            {"query": query, "collection": COLLECTION_NAME, "k": k},
        ).fetchall()

    results = []
    for rank, row in enumerate(rows):
        doc = Document(
            page_content=row.document,
            metadata=row.cmetadata or {},
        )
        results.append((doc, rank + 1))
    return results
