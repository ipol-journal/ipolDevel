"""Tests for template and blob management views in ControlPanel/view.py."""
import json
import os

import pytest
import responses
from django.core.files.uploadedfile import SimpleUploadedFile


# ==============================================================================
# Template Views Tests
# ==============================================================================

@pytest.mark.django_db
class TestTemplateViews:
    def test_templates_requires_login(self, client):
        """Unauthenticated templates request redirects to login."""
        response = client.get("/cp2/templates")
        assert response.status_code == 302
        assert "login" in response.url

    def test_templates_renders_list(self, auth_client, mocked_responses):
        """templates view loads templates from API and renders Templates.html."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.GET,
            f"{host}/api/blobs/templates",
            json=[{"id": 1, "name": "Standard Images"}],
            status=200,
        )

        response = auth_client.get("/cp2/templates")
        assert response.status_code == 200
        assert "Templates.html" in [t.name for t in response.templates]
        assert len(response.context["templates"]) == 1
        assert response.context["templates"][0]["name"] == "Standard Images"

    def test_ajax_add_template_success(self, auth_client, mocked_responses):
        """ajax_add_template successfully creates template and returns JSON with template_id."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.POST,
            f"{host}/api/blobs/templates",
            json={"template_id": 15},
            status=201,
        )

        response = auth_client.post(
            "/cp2/templates/ajax",
            {"templateName": "New Test Template"},
        )
        assert response.status_code == 200
        assert response.json() == {"template_id": 15}

    def test_ajax_add_template_unauthorized(self, auth_client, mocked_responses):
        """When API rejects template creation, returns 401 Unauthorized."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.POST,
            f"{host}/api/blobs/templates",
            status=403,
        )

        response = auth_client.post(
            "/cp2/templates/ajax",
            {"templateName": "Forbidden Template"},
        )
        assert response.status_code == 401
        assert response.json() == {"message": "Unauthorized"}

    def test_show_template_renders_details(self, auth_client, mocked_responses):
        """showTemplate loads sets and associated demos, checking can_edit superuser flag."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.GET,
            f"{host}/api/blobs/templates/1",
            json=[{"name": "input_images", "blobs": {}}],
            status=200,
        )
        mocked_responses.add(
            responses.GET,
            f"{host}/api/blobs/demos_using_template/1",
            json=[{"id": 100, "title": "Demo 100"}],
            status=200,
        )

        response = auth_client.get("/cp2/showTemplate?template_id=1&template_name=Standard")
        assert response.status_code == 200
        assert "showTemplate.html" in [t.name for t in response.templates]
        assert response.context["template_name"] == "Standard"
        assert response.context["can_edit"] is False  # standard test user is not superuser

    def test_ajax_delete_template_success(self, auth_client, mocked_responses):
        """ajax_delete_template calls API DELETE and returns JSON status OK."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.DELETE,
            f"{host}/api/blobs/templates/1",
            status=204,
        )

        response = auth_client.post(
            "/cp2/showTemplates/ajax_delete_template",
            {"template_id": "1"},
        )
        assert response.status_code == 200
        assert response.json() == {"status": "OK"}

    def test_ajax_delete_template_failure(self, auth_client, mocked_responses):
        """When delete template API returns error, returns JSON status KO."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.DELETE,
            f"{host}/api/blobs/templates/1",
            status=400,
        )

        response = auth_client.post(
            "/cp2/showTemplates/ajax_delete_template",
            {"template_id": "1"},
        )
        assert response.status_code == 200
        assert response.json() == {"status": "KO"}


# ==============================================================================
# Blob Creation & Upload Tests
# ==============================================================================

@pytest.mark.django_db
class TestBlobCreationUpload:
    def test_create_blob_demo_mode(self, auth_client, staff_user):
        """CreateBlob in demo mode verifies permissions and prepares context."""
        auth_client.force_login(staff_user)
        response = auth_client.get("/cp2/createBlob?demo_id=100")
        assert response.status_code == 200
        assert "createBlob.html" in [t.name for t in response.templates]
        assert response.context["demo_id"] == "100"
        assert response.context["can_edit"] is True

    def test_create_blob_template_mode(self, auth_client):
        """CreateBlob in template mode sets template attributes in context."""
        response = auth_client.get("/cp2/createBlob?template_id=2&template_name=Custom")
        assert response.status_code == 200
        assert "createBlob.html" in [t.name for t in response.templates]
        assert response.context["template_id"] == "2"
        assert response.context["template_name"] == "Custom"

    def test_ajax_add_blob_demo_authorized(self, auth_client, staff_user, mocked_responses):
        """Authorized user uploading a blob forwards file and parameters to blobs API."""
        auth_client.force_login(staff_user)
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.POST,
            f"{host}/api/blobs/demo_blobs/100",
            json={"status": "OK"},
            status=200,
        )

        test_file = SimpleUploadedFile("sample.png", b"fake_png_data", content_type="image/png")

        response = auth_client.post(
            "/cp2/createBlob/demo",
            {
                "SET": "input_images",
                "PositionSet": "1",
                "Title": "Sample Image",
                "Credit": "Public Domain",
                "demo_id": "100",
                "Blobs": test_file,
            },
        )
        assert response.status_code == 200
        assert len(mocked_responses.calls) == 1

    def test_ajax_add_blob_demo_unauthorized(self, auth_client, mocked_responses):
        """Unauthorized user attempting to upload blob renders homepage without calling API."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.GET,
            f"{host}/api/demoinfo/demos/100/editors",
            json=[],  # No editor permission
            status=200,
        )

        test_file = SimpleUploadedFile("sample.png", b"data", content_type="image/png")

        response = auth_client.post(
            "/cp2/createBlob/demo",
            {
                "SET": "input_images",
                "PositionSet": "0",
                "Title": "Title",
                "Credit": "Credit",
                "demo_id": "100",
                "Blobs": test_file,
            },
        )
        assert response.status_code == 200
        assert "homepage.html" in [t.name for t in response.templates]


# ==============================================================================
# Blob Details & Editing Tests
# ==============================================================================

@pytest.mark.django_db
class TestBlobDetailsEditing:
    def test_details_blob_demo_mode(self, auth_client, staff_user, mocked_responses):
        """detailsBlob in demo mode parses matching blob from demo sets."""
        auth_client.force_login(staff_user)
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.GET,
            f"{host}/api/blobs/demo_blobs/100",
            json=[
                {
                    "name": "input",
                    "blobs": {
                        "0": {
                            "id": 42,
                            "title": "Lenna",
                            "blob": "lenna.png",
                            "format": "png",
                            "credit": "USC SIPI",
                        }
                    },
                }
            ],
            status=200,
        )

        response = auth_client.get("/cp2/detailsBlob?demo_id=100&set=input&pos=0")
        assert response.status_code == 200
        assert "detailsBlob.html" in [t.name for t in response.templates]
        assert response.context["blob_id"] == 42
        assert response.context["title"] == "Lenna"
        assert response.context["credit"] == "USC SIPI"

    def test_details_blob_template_mode(self, auth_client, mocked_responses):
        """detailsBlob in template mode parses matching blob from template sets."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.GET,
            f"{host}/api/blobs/templates/1",
            json=[
                {
                    "name": "defaults",
                    "blobs": {
                        "0": {
                            "id": 99,
                            "title": "Default Image",
                            "blob": "default.png",
                            "format": "png",
                            "credit": "IPOL",
                        }
                    },
                }
            ],
            status=200,
        )

        response = auth_client.get(
            "/cp2/detailsBlob?template_id=1&template_name=Standard&set=defaults&pos=0"
        )
        assert response.status_code == 200
        assert response.context["blob_id"] == 99
        assert response.context["title"] == "Default Image"

    def test_details_blob_template_not_found_returns_404(self, auth_client, mocked_responses):
        """When requested blob position does not exist in template sets, returns 404."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.GET,
            f"{host}/api/blobs/templates/1",
            json=[{"name": "defaults", "blobs": {}}],
            status=200,
        )

        response = auth_client.get(
            "/cp2/detailsBlob?template_id=1&template_name=Standard&set=defaults&pos=99"
        )
        assert response.status_code == 404
        assert response.json() == {"status": "OK", "message": "Blob not found"}

    def test_ajax_edit_blob_template_success(self, auth_client, mocked_responses):
        """ajax_edit_blob_template calls PUT and returns JSON OK on 204."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.PUT,
            f"{host}/api/blobs/template_blobs/1",
            status=204,
        )

        response = auth_client.post(
            "/cp2/detailsBlob/ajax_template",
            {
                "SET": "new_set",
                "old_set": "old_set",
                "PositionSet": "1",
                "old_pos": "0",
                "Title": "Updated Title",
                "Credit": "Updated Credit",
                "template_id": "1",
            },
        )
        assert response.status_code == 200
        assert response.json() == {"status": "OK"}


# ==============================================================================
# Blob Removal & VR Management Tests
# ==============================================================================

@pytest.mark.django_db
class TestBlobRemovalAndVR:
    def test_ajax_remove_blob_from_template_success(self, auth_client, mocked_responses):
        """ajax_remove_blob_from_template calls DELETE and returns JSON status OK on 201."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.DELETE,
            f"{host}/api/blobs/template_blobs/1",
            status=201,
        )

        response = auth_client.post(
            "/cp2/removeBlob/ajax_remove_blob_from_template",
            {"template_id": "1", "blob_set": "input", "pos_set": "0"},
        )
        assert response.status_code == 200
        assert response.json() == {"status": "OK"}

    def test_ajax_remove_blob_from_demo_unauthorized(self, auth_client, mocked_responses):
        """Non-staff user without permissions cannot remove demo blob and receives KO."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.GET,
            f"{host}/api/demoinfo/demos/100/editors",
            json=[],  # Unauthorized
            status=200,
        )

        response = auth_client.post(
            "/cp2/removeBlob/ajax_remove_blob_from_demo",
            {"demo_id": "100", "blob_set": "input", "pos_set": "0"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "KO"
        assert data["message"] == "User not allowed"

    def test_ajax_remove_blob_from_demo_authorized(self, auth_client, staff_user, mocked_responses):
        """Staff user successfully removes demo blob when API returns 204."""
        auth_client.force_login(staff_user)
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.DELETE,
            f"{host}/api/blobs/demo_blobs/100",
            status=204,
        )

        response = auth_client.post(
            "/cp2/removeBlob/ajax_remove_blob_from_demo",
            {"demo_id": "100", "blob_set": "input", "pos_set": "0"},
        )
        assert response.status_code == 200
        assert response.json() == {"status": "OK"}

    def test_show_blobs_demo_renders(self, auth_client, staff_user, mocked_responses):
        """showBlobsDemo loads owned blobs, demo templates, and template list, rendering showBlobsDemo.html."""
        auth_client.force_login(staff_user)
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.GET,
            f"{host}/api/blobs/demo_owned_blobs/100",
            json=[{"name": "input", "blobs": {}}],
            status=200,
        )
        mocked_responses.add(
            responses.GET,
            f"{host}/api/blobs/demo_templates/100",
            json=[{"id": 1, "name": "Default Template"}],
            status=200,
        )
        mocked_responses.add(
            responses.GET,
            f"{host}/api/blobs/templates",
            json=[{"id": 1, "name": "Default Template"}, {"id": 2, "name": "Other"}],
            status=200,
        )

        response = auth_client.get("/cp2/showBlobsDemo?demo_id=100")
        assert response.status_code == 200
        assert "showBlobsDemo.html" in [t.name for t in response.templates]
        assert len(response.context["blob_sets"]) == 1
        assert len(response.context["template_list"]) == 2

    def test_ajax_remove_vr_success(self, auth_client, mocked_responses):
        """ajax_remove_vr returns status 200 OK when API deletion returns 204."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.DELETE,
            f"{host}/api/blobs/visual_representations/1",
            status=204,
        )

        response = auth_client.post(
            "/cp2/detailsBlob/ajax_remove_vr",
            {"blob_id": "1"},
        )
        assert response.status_code == 200
        assert response.json() == {"status": "OK"}

    def test_ajax_remove_vr_failure(self, auth_client, mocked_responses):
        """ajax_remove_vr returns status 404 when deletion fails."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.DELETE,
            f"{host}/api/blobs/visual_representations/1",
            status=404,
        )

        response = auth_client.post(
            "/cp2/detailsBlob/ajax_remove_vr",
            {"blob_id": "1"},
        )
        assert response.status_code == 404
        assert response.json() == {"message": "Could not remove VR"}
