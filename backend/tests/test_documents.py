from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def _get_admin_token(client: AsyncClient) -> str:
    res = await client.post("/auth/login", json={
        "email": "admin@example.com",
        "password": "adminpass123",
    })
    return res.json()["access_token"]


async def _get_employee_token(client: AsyncClient) -> str:
    res = await client.post("/auth/login", json={
        "email": "employee@example.com",
        "password": "emppass123",
    })
    return res.json()["access_token"]


async def test_upload_requires_admin(client: AsyncClient, employee_user):
    token = await _get_employee_token(client)
    res = await client.post(
        "/documents/upload",
        files={"file": ("policy.pdf", b"fake", "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


async def test_upload_rejects_non_pdf(client: AsyncClient, admin_user):
    token = await _get_admin_token(client)
    res = await client.post(
        "/documents/upload",
        files={"file": ("policy.txt", b"some text", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 400
    assert "PDF" in res.json()["detail"]


async def test_status_no_document(client: AsyncClient, admin_user):
    token = await _get_admin_token(client)
    res = await client.get(
        "/documents/status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["has_document"] is False


async def test_upload_success(client: AsyncClient, admin_user):
    with patch("app.documents.service.upsert_chunks", return_value=5), \
         patch("app.documents.service.PdfReader") as mock_reader:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Employee leave policy. Employees get 20 days annual leave."
        mock_reader.return_value.pages = [mock_page]

        token = await _get_admin_token(client)
        fake_pdf = BytesIO(b"%PDF-1.4 fake content")
        res = await client.post(
            "/documents/upload",
            files={"file": ("policy.pdf", fake_pdf, "application/pdf")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        assert res.json()["success"] is True
        assert res.json()["chunks_created"] == 5
