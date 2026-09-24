"""Tests for api_post and user_can_edit_demo in ControlPanel/utils.py."""
import os
from unittest.mock import MagicMock

import pytest
import requests
import responses

from ControlPanel.utils import api_post, user_can_edit_demo

# ==============================================================================
# api_post HTTP Verbs & Return Shape Tests
# ==============================================================================


class TestApiPostVerbs:
    def test_api_post_get_success(self, mocked_responses):
        """GET request returns (parsed_json_dict, 200)."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.GET,
            f"{host}/api/test",
            json={"key": "value"},
            status=200,
        )
        data, status = api_post("/api/test", method="get")
        assert status == 200
        assert data == {"key": "value"}

    def test_api_post_post_success(self, mocked_responses):
        """POST request returns (parsed_json_dict, 201)."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.POST,
            f"{host}/api/create",
            json={"created": True},
            status=201,
        )
        data, status = api_post("/api/create", method="post", json={"name": "test"})
        assert status == 201
        assert data == {"created": True}

    def test_api_post_patch_success(self, mocked_responses):
        """PATCH request returns (parsed_json_dict, 200)."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.PATCH,
            f"{host}/api/update",
            json={"updated": True},
            status=200,
        )
        data, status = api_post("/api/update", method="patch", json={"name": "new"})
        assert status == 200
        assert data == {"updated": True}

    def test_api_post_put_returns_raw_response(self, mocked_responses):
        """PUT request returns (raw_requests_Response, status_code) rather than parsed JSON."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.PUT,
            f"{host}/api/put-endpoint",
            body="Raw Response Body",
            status=200,
        )
        resp, status = api_post("/api/put-endpoint", method="put")
        assert status == 200
        assert isinstance(resp, requests.Response)
        assert resp.text == "Raw Response Body"

    def test_api_post_delete_returns_raw_response(self, mocked_responses):
        """DELETE request returns (raw_requests_Response, 204)."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.DELETE,
            f"{host}/api/delete-endpoint",
            status=204,
        )
        resp, status = api_post("/api/delete-endpoint", method="delete")
        assert status == 204
        assert isinstance(resp, requests.Response)

    def test_api_post_forwards_params_and_headers(self, mocked_responses):
        """Query params and custom headers are forwarded to requests."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.GET,
            f"{host}/api/query",
            json={"ok": True},
            status=200,
        )
        api_post(
            "/api/query",
            method="get",
            params={"filter": "active", "limit": 10},
            headers={"X-Custom-Header": "IpolTest"},
        )
        assert len(mocked_responses.calls) == 1
        call = mocked_responses.calls[0]
        assert "filter=active" in call.request.url
        assert "limit=10" in call.request.url
        assert call.request.headers.get("X-Custom-Header") == "IpolTest"


# ==============================================================================
# api_post Resilience & Error Handling Tests
# ==============================================================================


class TestApiPostResilience:
    def test_api_post_malformed_json_returns_empty_dict(self, mocked_responses):
        """When response body is HTML or invalid JSON, returns ({}, status)."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.GET,
            f"{host}/api/bad-json",
            body="<html>502 Bad Gateway</html>",
            content_type="text/html",
            status=502,
        )
        data, status = api_post("/api/bad-json", method="get")
        assert status == 502
        assert data == {}

    def test_api_post_connection_error_returns_502(self, mocked_responses):
        """Network drop or ConnectionError returns ({}, 502)."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.GET,
            f"{host}/api/offline",
            body=requests.exceptions.ConnectionError("Connection refused"),
        )
        data, status = api_post("/api/offline", method="get")
        assert status == 502
        assert data == {}

    def test_api_post_timeout_returns_502(self, mocked_responses):
        """Timeout during request returns ({}, 502)."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.POST,
            f"{host}/api/slow",
            body=requests.exceptions.Timeout("Request timed out"),
        )
        data, status = api_post("/api/slow", method="post")
        assert status == 502
        assert data == {}

    def test_api_post_unsupported_method_absorbed_as_502(self):
        """
        Unsupported method triggers AssertionError('Invalid HTTP(S) method'),
        which is caught by except Exception and returns ({}, 502).
        """
        data, status = api_post("/api/invalid", method="head")
        assert status == 502
        assert data == {}


# ==============================================================================
# user_can_edit_demo Tests
# ==============================================================================


class TestUserCanEditDemo:
    def test_superuser_can_always_edit_without_api_call(self, mocked_responses):
        """Superuser is authorized immediately with zero network requests."""
        user = MagicMock()
        user.is_superuser = True
        user.is_staff = False

        assert user_can_edit_demo(user, "demo123") is True
        assert len(mocked_responses.calls) == 0

    def test_staff_user_can_always_edit_without_api_call(self, mocked_responses):
        """Staff user is authorized immediately with zero network requests."""
        user = MagicMock()
        user.is_superuser = False
        user.is_staff = True

        assert user_can_edit_demo(user, "demo123") is True
        assert len(mocked_responses.calls) == 0

    def test_non_staff_user_with_matching_email_can_edit(self, mocked_responses):
        """Non-staff user whose email matches one of the demo editors returns True."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.GET,
            f"{host}/api/demoinfo/demos/demo123/editors",
            json=[
                {"id": 1, "mail": "other@example.com"},
                {"id": 2, "mail": "editor@example.com"},
            ],
            status=200,
        )
        user = MagicMock()
        user.is_superuser = False
        user.is_staff = False
        user.email = "editor@example.com"

        assert user_can_edit_demo(user, "demo123") is True

    def test_non_staff_user_without_matching_email_cannot_edit(self, mocked_responses):
        """Non-staff user whose email is not in the editors list returns False."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.GET,
            f"{host}/api/demoinfo/demos/demo123/editors",
            json=[{"id": 1, "mail": "someoneelse@example.com"}],
            status=200,
        )
        user = MagicMock()
        user.is_superuser = False
        user.is_staff = False
        user.email = "editor@example.com"

        assert user_can_edit_demo(user, "demo123") is False

    def test_non_staff_empty_editors_list_cannot_edit(self, mocked_responses):
        """Empty editors list returns False."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.GET,
            f"{host}/api/demoinfo/demos/demo123/editors",
            json=[],
            status=200,
        )
        user = MagicMock()
        user.is_superuser = False
        user.is_staff = False
        user.email = "editor@example.com"

        assert user_can_edit_demo(user, "demo123") is False

    def test_non_staff_api_error_returns_false(self, mocked_responses):
        """When editors endpoint returns 502/error status, logs error and returns False."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.GET,
            f"{host}/api/demoinfo/demos/demo123/editors",
            status=502,
        )
        user = MagicMock()
        user.is_superuser = False
        user.is_staff = False
        user.email = "editor@example.com"

        assert user_can_edit_demo(user, "demo123") is False

    def test_non_staff_dict_response_raises_attribute_error(self, mocked_responses):
        """
        Implementation defect assertion:
        When editors endpoint returns a dict instead of a list (e.g. {"error": "Demo not found"}),
        iterating `for editor in editors_list:` iterates dict string keys, causing
        `editor.get('mail')` to raise AttributeError: 'str' object has no attribute 'get'.
        """
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.GET,
            f"{host}/api/demoinfo/demos/demo123/editors",
            json={"error": "Demo not found"},
            status=200,
        )
        user = MagicMock()
        user.is_superuser = False
        user.is_staff = False
        user.email = "editor@example.com"

        with pytest.raises(AttributeError, match="'str' object has no attribute 'get'"):
            user_can_edit_demo(user, "demo123")
