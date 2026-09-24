"""Tests for core demo management views in ControlPanel/view.py."""
import json
import os

import pytest
import responses

# ==============================================================================
# Status & DDL Doc Views
# ==============================================================================


@pytest.mark.django_db
class TestStatusViews:
    def test_status_requires_login(self, client):
        """Unauthenticated status request redirects to login."""
        response = client.get("/cp2/status")
        assert response.status_code == 302
        assert "login" in response.url

    def test_status_authenticated_renders(self, auth_client):
        """Authenticated status request renders status.html with 200 OK."""
        response = auth_client.get("/cp2/status")
        assert response.status_code == 200
        assert "status.html" in [t.name for t in response.templates]


# ==============================================================================
# Demo Editors Management Views
# ==============================================================================


@pytest.mark.django_db
class TestDemoEditorsViews:
    def test_demo_editors_requires_login(self, client):
        """Unauthenticated demo_editors request redirects to login."""
        response = client.get("/cp2/demo_editors?demo_id=100")
        assert response.status_code == 302
        assert "login" in response.url

    def test_demo_editors_renders_and_sorts_available(
        self, auth_client, mocked_responses
    ):
        """demo_editors renders with current editors and sorts available_editors by name."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.GET,
            f"{host}/api/demoinfo/demos/100/editors",
            json=[{"id": 1, "mail": "assigned@example.com"}],
            status=200,
        )
        mocked_responses.add(
            responses.GET,
            f"{host}/api/demoinfo/available_editors/100",
            json=[
                {"id": 3, "name": "Charlie", "mail": "c@example.com"},
                {"id": 2, "name": "Alice", "mail": "a@example.com"},
                {"id": 4, "name": "Bob", "mail": "b@example.com"},
            ],
            status=200,
        )

        response = auth_client.get("/cp2/demo_editors?demo_id=100")
        assert response.status_code == 200
        assert "demoEditors.html" in [t.name for t in response.templates]
        assert response.context["demo_id"] == "100"
        # Verify available_editors were sorted alphabetically by name
        names = [e["name"] for e in response.context["available_editors"]]
        assert names == ["Alice", "Bob", "Charlie"]

    def test_add_demo_editor_success(self, auth_client, staff_user, mocked_responses):
        """Staff user adding an editor calls API and redirects to HTTP_REFERER."""
        auth_client.force_login(staff_user)
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.POST,
            f"{host}/api/demoinfo/demos/100/editor/5",
            json={},
            status=201,
        )

        response = auth_client.post(
            "/cp2/add_demo_editor",
            {"demo_id": "100", "editor_id": "5"},
            HTTP_REFERER="/cp2/demo_editors?demo_id=100",
        )
        assert response.status_code == 302
        assert response.url == "/cp2/demo_editors?demo_id=100"

    def test_add_demo_editor_api_failure_returns_ko(
        self, auth_client, staff_user, mocked_responses
    ):
        """When API rejects adding an editor, returns JSON KO response."""
        auth_client.force_login(staff_user)
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.POST,
            f"{host}/api/demoinfo/demos/100/editor/5",
            json={"error": "Editor already assigned"},
            status=400,
        )

        response = auth_client.post(
            "/cp2/add_demo_editor",
            {"demo_id": "100", "editor_id": "5"},
            HTTP_REFERER="/cp2/demo_editors?demo_id=100",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "KO"
        assert data["message"] == "Editor already assigned"

    def test_remove_demo_editor_success(
        self, auth_client, staff_user, mocked_responses
    ):
        """Staff user removing an editor calls API DELETE and returns JSON OK."""
        auth_client.force_login(staff_user)
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.DELETE,
            f"{host}/api/demoinfo/demos/100/editor/5",
            status=204,
        )

        response = auth_client.post(
            "/cp2/remove_demo_editor",
            {"demo_id": "100", "editor_id": "5"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "OK"

    def test_remove_demo_editor_failure_triggers_response_defect(
        self, auth_client, staff_user, mocked_responses
    ):
        """
        Implementation defect assertion:
        In view.py line 152, remove_demo_editor calls demoinfo_response.get('error').
        However, api_post(..., method='delete') returns a raw requests.Response object
        rather than a dict, causing AttributeError: 'Response' object has no attribute 'get'.
        """
        auth_client.force_login(staff_user)
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.DELETE,
            f"{host}/api/demoinfo/demos/100/editor/5",
            json={"error": "Cannot remove sole editor"},
            status=400,
        )

        with pytest.raises(
            AttributeError, match="'Response' object has no attribute 'get'"
        ):
            auth_client.post(
                "/cp2/remove_demo_editor",
                {"demo_id": "100", "editor_id": "5"},
            )


# ==============================================================================
# Demo Creation & Deletion Views
# ==============================================================================


@pytest.mark.django_db
class TestDemoCreationDeletion:
    def test_ajax_add_demo_non_integer_id_returns_400(self, auth_client):
        """Submitting non-numeric demo_id returns HTTP 400 error."""
        response = auth_client.post(
            "/cp2/addDemo/ajax",
            {
                "state": "work_in_progress",
                "title": "Test Demo",
                "demo_id": "not-an-int",
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "KO"
        assert "integer" in data["message"]

    def test_ajax_add_demo_success(self, auth_client, test_user, mocked_responses):
        """Successfully adding a demo creates demo record, links creator, and redirects to showDemo."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.POST,
            f"{host}/api/demoinfo/demo",
            json={"id": 555},
            status=201,
        )
        mocked_responses.add(
            responses.GET,
            f"{host}/api/demoinfo/editor",
            json={"editor": {"id": 42, "mail": test_user.email}},
            status=200,
        )
        mocked_responses.add(
            responses.POST,
            f"{host}/api/demoinfo/demos/555/editor/42",
            json={},
            status=201,
        )

        response = auth_client.post(
            "/cp2/addDemo/ajax",
            {"state": "work_in_progress", "title": "Brand New Demo", "demo_id": "555"},
        )
        assert response.status_code == 302
        assert response.url == "/cp2/showDemo?demo_id=555"

    def test_ajax_delete_demo_success(self, auth_client, staff_user, mocked_responses):
        """Authorized user deleting demo calls core API and returns JSON OK."""
        auth_client.force_login(staff_user)
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.DELETE,
            f"{host}/api/core/demo/100",
            status=204,
        )

        response = auth_client.post(
            "/cp2/removeDemo/ajax",
            {"demo_id": "100"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "OK"


# ==============================================================================
# Show Demo, DDL & Metadata Views
# ==============================================================================


@pytest.mark.django_db
class TestShowDemoAndDDL:
    def test_show_demo_renders_all_components(self, auth_client, mocked_responses):
        """showDemo loads DDL, SSH keys, editors, metadata and renders showDemo.html."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.GET,
            f"{host}/api/demoinfo/ddl/100",
            json={"build": {"files": []}},
            status=200,
        )
        mocked_responses.add(
            responses.GET,
            f"{host}/api/demoinfo/ssh_keys/100",
            json={"pubkey": "ssh-rsa AAAA..."},
            status=200,
        )
        mocked_responses.add(
            responses.GET,
            f"{host}/api/demoinfo/demos/100/editors",
            json=[{"mail": "editor@example.com"}],
            status=200,
        )
        mocked_responses.add(
            responses.GET,
            f"{host}/api/demoinfo/available_editors/100",
            json=[],
            status=200,
        )
        mocked_responses.add(
            responses.GET,
            f"{host}/api/demoinfo/demo_metainfo/100",
            json={"title": "Interactive Demo"},
            status=200,
        )

        response = auth_client.get("/cp2/showDemo?demo_id=100")
        assert response.status_code == 200
        assert "showDemo.html" in [t.name for t in response.templates]
        assert response.context["demo_id"] == "100"
        assert response.context["title"] == "Interactive Demo"
        assert response.context["ssh_pubkey"] == "ssh-rsa AAAA..."

    def test_show_demo_graceful_fallbacks(self, auth_client, mocked_responses):
        """When DDL or SSH keys return 502/non-200, showDemo provides fallback values gracefully."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.GET,
            f"{host}/api/demoinfo/ddl/100",
            status=502,
        )
        mocked_responses.add(
            responses.GET,
            f"{host}/api/demoinfo/ssh_keys/100",
            status=502,
        )
        mocked_responses.add(
            responses.GET,
            f"{host}/api/demoinfo/demos/100/editors",
            json=[],
            status=200,
        )
        mocked_responses.add(
            responses.GET,
            f"{host}/api/demoinfo/available_editors/100",
            json=[],
            status=200,
        )
        mocked_responses.add(
            responses.GET,
            f"{host}/api/demoinfo/demo_metainfo/100",
            json={},
            status=200,
        )

        response = auth_client.get("/cp2/showDemo?demo_id=100")
        assert response.status_code == 200
        assert response.context["ddl"] == "{}"
        assert response.context["ssh_pubkey"] == "(error fetching the ssh public key)"

    def test_ajax_show_ddl(self, auth_client, mocked_responses):
        """ajax_show_DDL returns DDL JSON from demoinfo."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.GET,
            f"{host}/api/demoinfo/ddl/100",
            json={"schema": "1.0", "inputs": []},
            status=200,
        )

        response = auth_client.post(
            "/cp2/showDemo/ajax_showDDL",
            {"demo_id": "100"},
        )
        assert response.status_code == 200
        assert response.json() == {"schema": "1.0", "inputs": []}

    def test_ajax_save_ddl_authorized(self, auth_client, staff_user, mocked_responses):
        """Authorized user saves DDL, returning JSON OK with status 200."""
        auth_client.force_login(staff_user)
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.POST,
            f"{host}/api/demoinfo/ddl/100",
            status=200,
        )

        response = auth_client.post(
            "/cp2/showDemo/ajax_save_DDL",
            {"demo_id": "100", "ddl": json.dumps({"schema": "1.0"})},
        )
        assert response.status_code == 200
        assert response.json() == {"status": "OK"}

    def test_ajax_save_ddl_unauthorized(self, auth_client, mocked_responses):
        """Unauthorized user attempting to save DDL returns 401."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.GET,
            f"{host}/api/demoinfo/demos/100/editors",
            json=[],  # Not an editor
            status=200,
        )

        response = auth_client.post(
            "/cp2/showDemo/ajax_save_DDL",
            {"demo_id": "100", "ddl": "{}"},
        )
        assert response.status_code == 401
        data = response.json()
        assert data["message"] == "Unauthorized"

    def test_ajax_user_can_edit_demo(self, auth_client, staff_user):
        """ajax_user_can_edit_demo returns JSON boolean for edit capability."""
        auth_client.force_login(staff_user)
        response = auth_client.post(
            "/cp2/showDemo/ajax_user_can_edit_demo",
            {"demoID": "100"},
        )
        assert response.status_code == 200
        assert response.json() == {"can_edit": True}

    def test_edit_demo_success(self, auth_client, mocked_responses):
        """edit_demo coordinates demoinfo, blobs, and archive updates, then redirects."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.PATCH,
            f"{host}/api/demoinfo/demo/100",
            status=201,
        )
        mocked_responses.add(
            responses.PUT,
            f"{host}/api/blobs/demos/100",
            status=201,
        )
        mocked_responses.add(
            responses.PUT,
            f"{host}/api/archive/demo/100",
            status=204,
        )

        response = auth_client.post(
            "/cp2/showDemo/ajax_edit_demo",
            {
                "demo_id": "100",
                "new_demo_id": "100",
                "demoTitle": "Updated Title",
                "state": "published",
            },
        )
        assert response.status_code == 302
        assert response.url == "/cp2/showDemo?demo_id=100"

    def test_ddl_history_renders(self, auth_client, mocked_responses):
        """ddl_history retrieves revision list from demoinfo and renders ddl_history.html."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.GET,
            f"{host}/api/demoinfo/ddl_history/100",
            json=[{"revision": 1, "date": "2026-09-01"}],
            status=200,
        )

        response = auth_client.get("/cp2/showDemo/ddl_history?demo_id=100&title=Test")
        assert response.status_code == 200
        assert "ddl_history.html" in [t.name for t in response.templates]
        assert len(response.context["ddl_history"]) == 1

    def test_reset_ssh_key_success(self, auth_client, staff_user, mocked_responses):
        """reset_ssh_key calls demoinfo endpoint and redirects to referer."""
        auth_client.force_login(staff_user)
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.GET,
            f"{host}/api/demoinfo/reset_ssh_keys/100",
            status=200,
        )

        response = auth_client.post(
            "/cp2/showDemo/reset_ssh_key",
            {"demo_id": "100"},
            HTTP_REFERER="/cp2/showDemo?demo_id=100",
        )
        assert response.status_code == 302
        assert response.url == "/cp2/showDemo?demo_id=100"
