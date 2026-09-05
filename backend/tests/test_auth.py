import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _unique_email() -> str:
    return f"test-{uuid.uuid4().hex[:12]}@example.com"


def test_register_login_me_and_refresh():
    email = _unique_email()
    password = "securepass123"

    register_response = client.post(
        "/auth/register",
        json={
            "full_name": "Test User",
            "email": email,
            "password": password,
        },
    )
    assert register_response.status_code == 201
    user = register_response.json()
    assert user["email"] == email
    assert user["is_active"] is True

    login_response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200
    tokens = login_response.json()
    assert tokens["token_type"] == "bearer"
    assert tokens["access_token"]
    assert tokens["refresh_token"]

    me_response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == email

    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh_response.status_code == 200
    new_tokens = refresh_response.json()
    assert new_tokens["access_token"]
    assert new_tokens["refresh_token"]

    me_with_new_access = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {new_tokens['access_token']}"},
    )
    assert me_with_new_access.status_code == 200


def test_refresh_token_rejected_on_me():
    email = _unique_email()
    password = "securepass123"

    client.post(
        "/auth/register",
        json={
            "full_name": "Test User",
            "email": email,
            "password": password,
        },
    )
    login_response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    refresh_token = login_response.json()["refresh_token"]

    me_response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert me_response.status_code == 401
