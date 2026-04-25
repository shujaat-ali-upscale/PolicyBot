from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from langchain_core.documents import Document

pytestmark = pytest.mark.asyncio


async def _token(client: AsyncClient, email: str, password: str) -> str:
    res = await client.post("/auth/login", json={"email": email, "password": password})
    return res.json()["access_token"]


async def test_chat_requires_auth(client: AsyncClient):
    res = await client.post("/chat/", json={"question": "What is the leave policy?"})
    assert res.status_code == 403


async def test_chat_returns_answer(client: AsyncClient, employee_user):
    mock_docs = [
        Document(
            page_content="Employees receive 20 days of annual leave.",
            metadata={"chunk_index": 0},
        )
    ]
    with patch("app.chat.service.similarity_search", return_value=mock_docs), \
         patch("app.chat.service.generate_answer", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = "Employees receive 20 days of annual leave per year."

        token = await _token(client, "employee@example.com", "emppass123")
        res = await client.post(
            "/chat/",
            json={"question": "How many leave days do employees get?"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "answer" in data
        assert "sources" in data
        assert len(data["sources"]) == 1
        assert data["sources"][0]["chunk_index"] == 0


async def test_chat_no_docs_returns_fallback(client: AsyncClient, employee_user):
    with patch("app.chat.service.similarity_search", return_value=[]):
        token = await _token(client, "employee@example.com", "emppass123")
        res = await client.post(
            "/chat/",
            json={"question": "What is the overtime policy?"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        assert "don't have information" in res.json()["answer"]
