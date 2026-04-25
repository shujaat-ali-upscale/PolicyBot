import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.documents import Document
from app.chat.service import get_rag_response, generate_stream


def _doc(content: str, filename: str = "policy.pdf", page: int = 1) -> Document:
    return Document(
        page_content=content,
        metadata={"filename": filename, "page_number": page, "chunk_index": 0},
    )


@pytest.mark.asyncio
async def test_get_rag_response_returns_answer_and_sources():
    docs = [_doc("vacation policy content")]

    with patch("app.chat.service.hybrid_search", return_value=docs), \
         patch("app.chat.service.rerank", return_value=docs), \
         patch("app.chat.service.generate_answer", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = "You get 15 days of vacation."
        result = await get_rag_response("How many vacation days?")

    assert result["answer"] == "You get 15 days of vacation."
    assert len(result["sources"]) == 1
    assert result["sources"][0]["filename"] == "policy.pdf"


@pytest.mark.asyncio
async def test_get_rag_response_no_docs_returns_fallback():
    with patch("app.chat.service.hybrid_search", return_value=[]), \
         patch("app.chat.service.rerank", return_value=[]):
        result = await get_rag_response("unknown question")

    assert "don't have information" in result["answer"].lower()
    assert result["sources"] == []


@pytest.mark.asyncio
async def test_generate_stream_yields_tokens_then_done():
    docs = [_doc("some policy content")]
    collected = []

    async def fake_astream(*args, **kwargs):
        for token in ["Hello", " world"]:
            yield token

    with patch("app.chat.service.hybrid_search", return_value=docs), \
         patch("app.chat.service.rerank", return_value=docs), \
         patch("app.chat.service.STRICT_PROMPT") as mock_prompt, \
         patch("app.chat.service.get_llm") as mock_llm_fn, \
         patch("app.chat.service.StrOutputParser") as mock_parser:

        mock_chain = MagicMock()
        mock_chain.astream = fake_astream
        mock_prompt.__or__ = MagicMock(return_value=mock_chain)
        mock_chain.__or__ = MagicMock(return_value=mock_chain)

        async for chunk in generate_stream("test question"):
            collected.append(chunk)

    token_events = [c for c in collected if '"token"' in c]
    done_events = [c for c in collected if '"done": true' in c]
    assert len(token_events) >= 1
    assert len(done_events) == 1


@pytest.mark.asyncio
async def test_generate_stream_no_docs_yields_fallback_then_done():
    collected = []

    with patch("app.chat.service.hybrid_search", return_value=[]), \
         patch("app.chat.service.rerank", return_value=[]):
        async for chunk in generate_stream("unknown"):
            collected.append(chunk)

    assert any('"token"' in c for c in collected)
    assert any('"done": true' in c for c in collected)
