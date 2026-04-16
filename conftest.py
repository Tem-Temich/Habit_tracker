import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_user(db):
    user = User(
        email="user@example.com",
        username="user",
        telegram_chat_id=123456,
        telegram_username="user_tg",
    )
    user.set_password("strong-pass")
    user.save()
    return user


@pytest.fixture
def auth_client(api_client, auth_user):
    refresh = RefreshToken.for_user(auth_user)
    access_token = str(refresh.access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    return api_client

