"""Smoke tests verifying test runner configuration, database isolation, and basic routing."""
import pytest
import responses
from django.conf import settings


def test_settings_and_db_isolation():
    """Verify that test settings are loaded and database is strictly in-memory."""
    assert "memory" in settings.DATABASES["default"]["NAME"]
    assert settings.DEBUG is False
    assert (
        settings.PASSWORD_HASHERS[0] == "django.contrib.auth.hashers.MD5PasswordHasher"
    )


@pytest.mark.django_db
def test_user_factory_creation(user_factory):
    """Verify user_factory creates a user safely without signal crashes."""
    user = user_factory(username="smoke_user", email="smoke@example.com")
    assert user.id is not None
    assert user.username == "smoke_user"
    assert user.check_password("password123")


def test_unauthenticated_homepage_redirects(client):
    """Verify that unauthenticated access to /cp2/ redirects to login."""
    response = client.get("/cp2/")
    assert response.status_code == 302
    assert "login" in response.url


def test_login_page_renders(client):
    """Verify that the login page renders with HTTP 200."""
    response = client.get("/cp2/login")
    assert response.status_code == 200
    assert "form" in response.context


@pytest.mark.django_db
def test_authenticated_homepage_renders(auth_client, mocked_responses):
    """Verify that authenticated user can access homepage when external API is mocked."""
    ipol_url = settings.IPOL_URL.rstrip("/")

    # Mock pagination endpoint called by homepage view
    mocked_responses.add(
        responses.GET,
        f"{ipol_url}/api/demoinfo/demo_list_pagination_and_filter",
        json={"demo_list": [], "next_page_number": None, "previous_page_number": None},
        status=200,
    )
    # Mock editor info called by homepage view for page 1
    mocked_responses.add(
        responses.GET,
        f"{ipol_url}/api/demoinfo/editor",
        json={
            "editor": {"id": 10, "name": "Smoke User", "mail": "testuser@example.com"}
        },
        status=200,
    )
    # Mock own demos endpoint
    mocked_responses.add(
        responses.GET,
        f"{ipol_url}/api/demoinfo/demo_list_by_editorid/10",
        json=[],
        status=200,
    )

    response = auth_client.get("/cp2/")
    assert response.status_code == 200
    assert "demos" in response.context
