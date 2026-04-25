from langchain_core.documents import Document
from sentence_transformers import CrossEncoder

_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
_model: CrossEncoder | None = None


def _get_model() -> CrossEncoder:
    global _model
    if _model is None:
        _model = CrossEncoder(_MODEL_NAME)
    return _model


def load_reranker() -> None:
    model = _get_model()
    # Force full initialization (tokenizer + ONNX/torch runtime warmup)
    # so the first real request doesn't pay this cost
    model.predict([["warmup query", "warmup passage"]])


def rerank(query: str, chunks: list[Document], top_k: int = 3) -> list[Document]:
    if not chunks:
        return []

    model = _get_model()
    pairs = [[query, chunk.page_content] for chunk in chunks]
    scores_result = model.predict(pairs)
    # Handle both numpy arrays and lists
    scores: list[float] = scores_result.tolist() if hasattr(scores_result, "tolist") else scores_result
    ranked = sorted(zip(scores, chunks), key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in ranked[:top_k]]
