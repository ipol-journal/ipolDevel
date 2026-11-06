"""Tests for extras, template-demo linking, archive, and experiment views in ControlPanel/view.py."""
import os
from datetime import datetime

import pytest
import responses
from django.core.files.uploadedfile import SimpleUploadedFile

# ==============================================================================
# Demo Extras Views Tests
# ==============================================================================


@pytest.mark.django_db
class TestDemoExtrasViews:
    def test_demo_extras_requires_login(self, client):
        """Unauthenticated demoExtras request redirects to login."""
        response = client.get("/cp2/demoExtras?demo_id=100")
        assert response.status_code == 302
        assert "login" in response.url

    def test_demo_extras_renders_metadata(
        self, auth_client, staff_user, mocked_responses
    ):
        """demoExtras parses size, URL basename, and timestamp into datetime, rendering demoExtras.html."""
        auth_client.force_login(staff_user)
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.GET,
            f"{host}/api/demoinfo/demoextras/100",
            json={
                "size": 4096,
                "url": "https://ipol.im/extras/sample%20archive.tar.gz",
                "date": 1600000000,
            },
            status=200,
        )

        response = auth_client.get("/cp2/demoExtras?demo_id=100")
        assert response.status_code == 200
        assert "demoExtras.html" in [t.name for t in response.templates]
        assert response.context["size"] == 4096
        assert response.context["extras_name"] == "sample archive.tar.gz"
        assert response.context["date"] == datetime.fromtimestamp(1600000000)
        assert response.context["can_edit"] is True

    def test_ajax_add_demo_extras_success(
        self, auth_client, staff_user, mocked_responses
    ):
        """Staff user uploads demoextras archive; view coordinates upload and refreshes metadata."""
        auth_client.force_login(staff_user)
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.POST,
            f"{host}/api/demoinfo/demoextras/100",
            json={},
            status=201,
        )
        mocked_responses.add(
            responses.GET,
            f"{host}/api/demoinfo/demoextras/100",
            json={"size": 1024, "url": "https://ipol.im/extras/new.tar.gz"},
            status=200,
        )

        dummy_tar = SimpleUploadedFile(
            "new.tar.gz", b"archive contents", content_type="application/gzip"
        )

        response = auth_client.post(
            "/cp2/demoExtras/ajax_add_demo_extras",
            {"demo_id": "100", "demoextras": dummy_tar},
        )
        assert response.status_code == 200
        assert "demoExtras.html" in [t.name for t in response.templates]
        assert response.context["extras_name"] == "new.tar.gz"

    def test_ajax_add_demo_extras_failure_renders_500(
        self, auth_client, staff_user, mocked_responses
    ):
        """When API rejects demoextras upload, view renders demoExtras.html with status 500."""
        auth_client.force_login(staff_user)
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.POST,
            f"{host}/api/demoinfo/demoextras/100",
            json={"detail": "Corrupt tarfile"},
            status=400,
        )

        dummy_tar = SimpleUploadedFile(
            "bad.tar.gz", b"corrupt", content_type="application/gzip"
        )

        response = auth_client.post(
            "/cp2/demoExtras/ajax_add_demo_extras",
            {"demo_id": "100", "demoextras": dummy_tar},
        )
        assert response.status_code == 500
        assert "demoExtras.html" in [t.name for t in response.templates]
        assert response.context["error"] == "Corrupt tarfile"

    def test_ajax_delete_demo_extras_success(
        self, auth_client, staff_user, mocked_responses
    ):
        """Staff user successfully removes demo extras; redirects to demoExtras view."""
        auth_client.force_login(staff_user)
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.DELETE,
            f"{host}/api/demoinfo/demoextras/100",
            status=204,
        )

        response = auth_client.get(
            "/cp2/demoExtras/ajax_delete_demo_extras?demo_id=100"
        )
        assert response.status_code == 302
        assert response.url == "/cp2/demoExtras?demo_id=100"

    def test_ajax_delete_demo_extras_failure(
        self, auth_client, staff_user, mocked_responses
    ):
        """When delete demo extras returns non-204, view renders error.html."""
        auth_client.force_login(staff_user)
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.DELETE,
            f"{host}/api/demoinfo/demoextras/100",
            status=404,
        )

        response = auth_client.get(
            "/cp2/demoExtras/ajax_delete_demo_extras?demo_id=100"
        )
        assert response.status_code == 200
        assert "error.html" in [t.name for t in response.templates]
        assert response.context["error_code"] == 404
        assert "Error while removing demoextras" in response.context["message"]


# ==============================================================================
# Template Linking & Demo Blob Editing Tests
# ==============================================================================


@pytest.mark.django_db
class TestTemplateLinkingAndBlobDemo:
    def test_ajax_add_template_to_demo_authorized(
        self, auth_client, staff_user, mocked_responses
    ):
        """Staff user links template to demo, receiving JSON status OK."""
        auth_client.force_login(staff_user)
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.POST,
            f"{host}/api/blobs/add_template_to_demo/100",
            status=201,
        )

        response = auth_client.post(
            "/cp2/showBlobsDemo/ajax_add_template_to_demo",
            {"demo_id": "100", "template_id": "5"},
        )
        assert response.status_code == 200
        assert response.json() == {"status": "OK"}

    def test_ajax_add_template_to_demo_unauthorized(
        self, auth_client, mocked_responses
    ):
        """Unauthorized user attempting template linking renders homepage.html."""
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.GET,
            f"{host}/api/demoinfo/demos/100/editors",
            json=[],  # Unauthorized
            status=200,
        )

        response = auth_client.post(
            "/cp2/showBlobsDemo/ajax_add_template_to_demo",
            {"demo_id": "100", "template_id": "5"},
        )
        assert response.status_code == 200
        assert "homepage.html" in [t.name for t in response.templates]

    def test_ajax_remove_template_to_demo_authorized(
        self, auth_client, staff_user, mocked_responses
    ):
        """Staff user unlinks template from demo, receiving 204 JsonResponse."""
        auth_client.force_login(staff_user)
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.DELETE,
            f"{host}/api/blobs/demo_templates/100",
            status=204,
        )

        response = auth_client.post(
            "/cp2/showBlobsDemo/ajax_remove_template_to_demo",
            {"demo_id": "100", "template_id": "5"},
        )
        assert response.status_code == 204

    def test_ajax_edit_blob_demo_success(
        self, auth_client, staff_user, mocked_responses
    ):
        """Staff user updates demo blob metadata via PUT and receives JSON OK."""
        auth_client.force_login(staff_user)
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.PUT,
            f"{host}/api/blobs/demo_blobs/100",
            status=204,
        )

        response = auth_client.post(
            "/cp2/detailsBlob/ajax_demo",
            {
                "demo_id": "100",
                "old_set": "input",
                "SET": "input",
                "old_pos": "0",
                "PositionSet": "1",
                "Title": "Updated Title",
                "Credit": "Updated Credit",
            },
        )
        assert response.status_code == 200
        assert response.json() == {"status": "OK"}


# ==============================================================================
# Archive & Experiment Views Tests
# ==============================================================================


@pytest.mark.django_db
class TestArchiveExperimentViews:
    def test_show_archive_requires_login(self, client):
        """Unauthenticated show_archive request redirects to login."""
        response = client.get("/cp2/showArchive?demo_id=100")
        assert response.status_code == 302
        assert "login" in response.url

    def test_show_archive_renders_experiments_and_pagination(
        self, auth_client, staff_user, mocked_responses
    ):
        """showArchive loads paginated experiments and renders archive.html."""
        auth_client.force_login(staff_user)
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.GET,
            f"{host}/api/archive/page/1",
            json={
                "experiments": [{"id": "exp_123", "date": "2026-09-01"}],
                "meta_info": {"total_pages": 3, "total_elements": 25},
            },
            status=200,
        )

        response = auth_client.get(
            "/cp2/showArchive?demo_id=100&page=1&title=Demo%20Archive"
        )
        assert response.status_code == 200
        assert "archive.html" in [t.name for t in response.templates]
        assert len(response.context["experiments"]) == 1
        assert response.context["page"] == 1
        assert response.context["can_edit"] is True

    def test_show_experiment_success(self, auth_client, staff_user, mocked_responses):
        """show_experiment loads details for specified experiment_id and renders showExperiment.html."""
        auth_client.force_login(staff_user)
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.GET,
            f"{host}/api/archive/experiment/exp_123",
            json={
                "id": "exp_123",
                "stdout": "Finished execution",
                "status": "completed",
            },
            status=200,
        )

        response = auth_client.get(
            "/cp2/showExperiment?demo_id=100&experiment_id=exp_123"
        )
        assert response.status_code == 200
        assert "showExperiment.html" in [t.name for t in response.templates]
        assert response.context["experiment"]["stdout"] == "Finished execution"

    def test_show_experiment_not_found(self, auth_client, staff_user, mocked_responses):
        """When experiment is not found in archive API, renders error.html with 404."""
        auth_client.force_login(staff_user)
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.GET,
            f"{host}/api/archive/experiment/exp_999",
            status=404,
        )

        response = auth_client.get(
            "/cp2/showExperiment?demo_id=100&experiment_id=exp_999"
        )
        assert response.status_code == 200
        assert "error.html" in [t.name for t in response.templates]
        assert response.context["error_code"] == 404
        assert "Experiment not found" in response.context["message"]

    def test_ajax_delete_experiment_success(
        self, auth_client, staff_user, mocked_responses
    ):
        """Staff user deleting experiment calls archive DELETE and returns JSON OK on 204."""
        auth_client.force_login(staff_user)
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.DELETE,
            f"{host}/api/archive/experiment/exp_123",
            status=204,
        )

        response = auth_client.post(
            "/cp2/ajax_delete_experiment",
            {"demo_id": "100", "experiment_id": "exp_123"},
        )
        assert response.status_code == 200
        assert response.json() == {"status": "OK"}

    def test_ajax_delete_experiment_failure(
        self, auth_client, staff_user, mocked_responses
    ):
        """When archive DELETE returns non-204, returns JSON KO."""
        auth_client.force_login(staff_user)
        host = os.environ.get("IPOL_URL", "http://localhost:8000")
        mocked_responses.add(
            responses.DELETE,
            f"{host}/api/archive/experiment/exp_123",
            status=400,
        )

        response = auth_client.post(
            "/cp2/ajax_delete_experiment",
            {"demo_id": "100", "experiment_id": "exp_123"},
        )
        assert response.status_code == 200
        assert response.json() == {"status": "KO"}
