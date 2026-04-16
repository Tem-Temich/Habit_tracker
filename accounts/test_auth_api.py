from rest_framework.test import APIClient


def test_register_and_token_obtain(db):
    client = APIClient()

    payload = {
        "email": "new_user@example.com",
        "telegram_chat_id": 111,
        "telegram_username": "new_user_tg",
        "username": "new_user",
        "password": "strong-pass-123",
    }

    resp = client.post("/api/register/", data=payload, format="json")
    assert resp.status_code == 201

    token_resp = client.post(
        "/api/token/",
        data={"email": payload["email"], "password": payload["password"]},
        format="json",
    )
    assert token_resp.status_code == 200
    assert "access" in token_resp.data
    assert "refresh" in token_resp.data

