import os
from functools import lru_cache

from langchain_community.embeddings import FastEmbedEmbeddings


@lru_cache(maxsize=1)
def get_embeddings() -> FastEmbedEmbeddings:
    cache_dir = os.environ.get("FASTEMBED_CACHE_PATH", None)
    return FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5", cache_dir=cache_dir)
