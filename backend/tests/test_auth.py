"""Phase 1 authentication API tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _register(
    client: AsyncClient,
    *,
    email: str = "priya@company.com",
    password: str = "secret123",
    full_name: str = "Priya Sharma",
):
    return await client.post(
        "/api/auth/register",
        json={
            "full_name": full_name,
            "email": email,
            "password": password,
            "role": "Project manager",
        },
    )


@pytest.mark.asyncio
async def test_register_login_and_me(app_client: AsyncClient):
    register = await _register(app_client)
    assert register.status_code == 201
    body = register.json()
    assert body["success"] is True
    assert body["data"]["access_token"]
    assert body["data"]["user"]["email"] == "priya@company.com"
    assert body["data"]["user"]["initials"] == "PS"

    login = await app_client.post(
        "/api/auth/login",
        json={"email": "priya@company.com", "password": "secret123"},
    )
    assert login.status_code == 200
    token = login.json()["data"]["access_token"]

    me = await app_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me.status_code == 200
    assert me.json()["data"]["full_name"] == "Priya Sharma"


@pytest.mark.asyncio
async def test_register_duplicate_email(app_client: AsyncClient):
    first = await _register(app_client)
    second = await _register(app_client)
    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "email_taken"


@pytest.mark.asyncio
async def test_login_invalid_credentials(app_client: AsyncClient):
    await _register(app_client)
    response = await app_client.post(
        "/api/auth/login",
        json={"email": "priya@company.com", "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"


@pytest.mark.asyncio
async def test_me_requires_auth(app_client: AsyncClient):
    response = await app_client.get("/api/auth/me")
    assert response.status_code == 401
