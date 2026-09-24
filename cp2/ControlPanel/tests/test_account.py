"""Tests for account management flows in ControlPanel/account.py."""
from smtplib import SMTPException
from unittest.mock import patch

import pytest
import responses
from django.conf import settings
from django.contrib.messages import get_messages
from django.core import mail
from django.core.mail import BadHeaderError

# ==============================================================================
# Login Page Tests
# ==============================================================================


@pytest.mark.django_db
class TestLoginPage:
    def test_login_page_get_renders_form(self, client):
        """GET /cp2/login renders login form."""
        response = client.get("/cp2/login")
        assert response.status_code == 200
        assert "form" in response.context
        assert set(response.context["form"].fields.keys()) == {"username", "password"}

    def test_login_success_redirects_and_creates_session(self, client, user_factory):
        """Valid credentials log in the user and redirect to /cp2/."""
        user = user_factory(username="validuser", password="securepassword123")
        response = client.post(
            "/cp2/login",
            {"username": "validuser", "password": "securepassword123"},
        )
        assert response.status_code == 302
        assert response.url == "/cp2/"
        assert client.session["_auth_user_id"] == str(user.id)

    def test_login_remember_me_disabled_sets_browser_session(
        self, client, user_factory
    ):
        """Without 'remember', session expiry is set to 0 (expires when browser closes)."""
        user_factory(username="validuser", password="securepassword123")
        response = client.post(
            "/cp2/login",
            {"username": "validuser", "password": "securepassword123"},
        )
        assert response.status_code == 302
        assert client.session.get_expire_at_browser_close() is True

    def test_login_remember_me_enabled_retains_expiry(self, client, user_factory):
        """With 'remember', session uses standard long-lived expiry."""
        user_factory(username="validuser", password="securepassword123")
        response = client.post(
            "/cp2/login",
            {
                "username": "validuser",
                "password": "securepassword123",
                "remember": "on",
            },
        )
        assert response.status_code == 302
        assert client.session.get_expire_at_browser_close() is False

    def test_login_invalid_credentials_shows_error(self, client, user_factory):
        """Invalid credentials redisplay login form with error message."""
        user_factory(username="validuser", password="securepassword123")
        response = client.post(
            "/cp2/login",
            {"username": "validuser", "password": "wrongpassword"},
        )
        assert response.status_code == 200
        msg_list = list(get_messages(response.wsgi_request))
        assert any("Invalid username or password" in m.message for m in msg_list)

    def test_login_empty_post_shows_no_credentials_error(self, client):
        """Empty POST does not trigger 'Invalid username or password' flash."""
        response = client.post("/cp2/login", {})
        assert response.status_code == 200
        msg_list = list(get_messages(response.wsgi_request))
        assert not any("Invalid username or password" in m.message for m in msg_list)


# ==============================================================================
# Signout & Logout Tests
# ==============================================================================


@pytest.mark.django_db
class TestSignoutAndLogout:
    def test_signout_requires_login(self, client):
        """Unauthenticated signout request redirects to login."""
        response = client.get("/cp2/signout")
        assert response.status_code == 302
        assert "login" in response.url

    def test_signout_renders_for_authenticated_user(self, auth_client):
        """Authenticated signout request renders signout.html."""
        response = auth_client.get("/cp2/signout")
        assert response.status_code == 200
        assert "signout.html" in [t.name for t in response.templates]

    def test_logout_requires_login(self, client):
        """Unauthenticated logout request redirects to login."""
        response = client.get("/cp2/logout")
        assert response.status_code == 302
        assert "login" in response.url

    def test_logout_clears_session_and_redirects(self, auth_client):
        """Authenticated logout clears session and redirects to login."""
        response = auth_client.get("/cp2/logout")
        assert response.status_code == 302
        assert response.url == "/cp2/login"
        assert "_auth_user_id" not in auth_client.session


# ==============================================================================
# Password Reset Tests
# ==============================================================================


@pytest.mark.django_db
class TestPasswordReset:
    def test_password_reset_get_renders_form(self, client):
        """GET password_reset renders the reset request form."""
        response = client.get("/cp2/password_reset/")
        assert response.status_code == 200
        assert "password_reset_form" in response.context

    def test_password_reset_existing_user_sends_email(self, client, user_factory):
        """Submitting email of existing user sends reset email with token."""
        user_factory(username="resetuser", email="reset@example.com")
        mail.outbox.clear()

        response = client.post(
            "/cp2/password_reset/",
            {"email": "reset@example.com"},
        )
        assert response.status_code == 302
        assert response.url == "/cp2/password_reset/done/"

        # Assert email was dispatched to outbox
        assert len(mail.outbox) == 1
        sent_email = mail.outbox[0]
        assert "Password Reset Requested" in sent_email.subject
        assert sent_email.to == ["reset@example.com"]
        assert "reset/" in sent_email.body  # Token link present

    def test_password_reset_nonexistent_email_implementation_defect(self, client):
        """
        Implementation defect assertion:
        In account.py:password_reset, if associated_users does not exist,
        execution falls through to line 99 which overwrites the form and re-renders
        password_reset.html with 200 OK, instead of redirecting to password_reset_done.
        """
        mail.outbox.clear()
        response = client.post(
            "/cp2/password_reset/",
            {"email": "unknown@example.com"},
        )
        assert response.status_code == 200
        assert "password/password_reset.html" in [t.name for t in response.templates]
        assert len(mail.outbox) == 0

    def test_password_reset_invalid_email_format_obliterates_form_errors(self, client):
        """
        Implementation defect assertion:
        When form validation fails, line 99 unconditionally overwrites password_reset_form
        with an unbound PasswordResetForm(), clearing user input and error messages.
        """
        response = client.post(
            "/cp2/password_reset/",
            {"email": "not-a-valid-email"},
        )
        assert response.status_code == 200
        assert "password_reset_form" in response.context
        assert response.context["password_reset_form"].is_bound is False

    def test_password_reset_bad_header_error_handled(self, client, user_factory):
        """BadHeaderError during send_mail returns specific error response."""
        user_factory(username="headeruser", email="header@example.com")
        with patch(
            "ControlPanel.account.send_mail",
            side_effect=BadHeaderError("Header injection"),
        ):
            response = client.post(
                "/cp2/password_reset/",
                {"email": "header@example.com"},
            )
            assert response.status_code == 200
            assert response.content == b"Invalid header found."

    def test_password_reset_smtp_exception_triggers_logging_defect(
        self, client, user_factory
    ):
        """
        Implementation defect assertion:
        In account.py line 94, `logger.warning('SMTP exception, error sending email: ', e)`
        lacks a %s format specifier, which causes Python logging to raise a TypeError
        when an SMTPException occurs during send_mail.
        """
        user_factory(username="smtpuser", email="smtp@example.com")
        with patch(
            "ControlPanel.account.send_mail",
            side_effect=SMTPException("Connection refused"),
        ):
            with pytest.raises(
                TypeError, match="not all arguments converted during string formatting"
            ):
                client.post(
                    "/cp2/password_reset/",
                    {"email": "smtp@example.com"},
                )


# ==============================================================================
# Profile View Tests
# ==============================================================================


@pytest.mark.django_db
class TestProfileView:
    def test_profile_requires_login(self, client):
        """Unauthenticated profile request redirects to login."""
        response = client.get("/cp2/profile")
        assert response.status_code == 302
        assert "login" in response.url

    def test_profile_authenticated_renders_user_data(self, auth_client, test_user):
        """Authenticated profile request renders user attributes in context."""
        response = auth_client.get("/cp2/profile")
        assert response.status_code == 200
        assert response.context["username"] == test_user.username
        assert response.context["email"] == test_user.email
        assert response.context["firstName"] == test_user.first_name
        assert response.context["lastName"] == test_user.last_name


# ==============================================================================
# Save Profile Tests
# ==============================================================================


@pytest.mark.django_db
class TestSaveProfile:
    def test_save_profile_requires_login(self, client):
        """Unauthenticated save_profile request redirects to login."""
        response = client.post("/cp2/save_profile", {})
        assert response.status_code == 302
        assert "login" in response.url

    def test_save_profile_empty_email_shows_warning(self, auth_client):
        """Empty email submission sets warning and redirects."""
        response = auth_client.post(
            "/cp2/save_profile",
            {"username": "any", "firstName": "A", "lastName": "B", "email": ""},
        )
        assert response.status_code == 302
        assert response.url == "/cp2/profile"
        msg_list = list(get_messages(response.wsgi_request))
        assert any("The email cannot be empty." in m.message for m in msg_list)

    def test_save_profile_external_api_error(self, auth_client, mocked_responses):
        """When demoinfo GET returns 502, warning is shown and redirects."""
        ipol_url = settings.IPOL_URL.rstrip("/")
        mocked_responses.add(
            responses.GET,
            f"{ipol_url}/api/demoinfo/editor",
            status=502,
        )

        response = auth_client.post(
            "/cp2/save_profile",
            {
                "username": "updated_user",
                "firstName": "John",
                "lastName": "Doe",
                "email": "new_email@example.com",
            },
        )
        assert response.status_code == 302
        assert response.url == "/cp2/profile"
        msg_list = list(get_messages(response.wsgi_request))
        assert any("Internal error: 502" in m.message for m in msg_list)

    def test_save_profile_new_email_already_in_use(self, auth_client, mocked_responses):
        """When new email belongs to another editor in demoinfo, warning is shown."""
        ipol_url = settings.IPOL_URL.rstrip("/")
        mocked_responses.add(
            responses.GET,
            f"{ipol_url}/api/demoinfo/editor",
            json={
                "editor": {"id": 99, "name": "Existing", "mail": "taken@example.com"}
            },
            status=200,
        )

        response = auth_client.post(
            "/cp2/save_profile",
            {
                "username": "updated_user",
                "firstName": "John",
                "lastName": "Doe",
                "email": "taken@example.com",
            },
        )
        assert response.status_code == 302
        assert response.url == "/cp2/profile"
        msg_list = list(get_messages(response.wsgi_request))
        assert any("New email is already in use." in m.message for m in msg_list)

    def test_save_profile_success_without_email_change(
        self, auth_client, test_user, mocked_responses
    ):
        """Updating name without changing email succeeds and updates user record."""
        ipol_url = settings.IPOL_URL.rstrip("/")
        mocked_responses.add(
            responses.GET,
            f"{ipol_url}/api/demoinfo/editor",
            json={"editor": {"id": 1, "name": "User", "mail": test_user.email}},
            status=200,
        )

        response = auth_client.post(
            "/cp2/save_profile",
            {
                "username": test_user.username,
                "firstName": "NewFirst",
                "lastName": "NewLast",
                "email": test_user.email,
            },
        )
        assert response.status_code == 302
        assert response.url == "/cp2/profile"
        msg_list = list(get_messages(response.wsgi_request))
        assert any(
            "Your profile has been changed successfully." in m.message for m in msg_list
        )

        test_user.refresh_from_db()
        assert test_user.first_name == "NewFirst"
        assert test_user.last_name == "NewLast"

    def test_save_profile_missing_post_keys_raises_key_error(
        self, auth_client, mocked_responses
    ):
        """
        Omitting required POST keys (username, firstName, lastName) raises KeyError in production code.
        Demoinfo returns an error without the 'editor' key so it proceeds to profile field unpacking.
        """
        ipol_url = settings.IPOL_URL.rstrip("/")
        mocked_responses.add(
            responses.GET,
            f"{ipol_url}/api/demoinfo/editor",
            json={"error": "Editor not found"},
            status=200,
        )

        # Missing 'username', 'firstName', 'lastName'
        with pytest.raises(KeyError):
            auth_client.post(
                "/cp2/save_profile",
                {"email": "new@example.com"},
            )
