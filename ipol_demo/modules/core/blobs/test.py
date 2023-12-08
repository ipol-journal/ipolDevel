#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blobs tests
"""
import os

# Unit tests for the Blobs module
import sys
import unittest

import requests


class BlobsTests(unittest.TestCase):
    """
    BlobsTests
    """

    BASE_URL = os.environ.get("IPOL_URL")
    module = "blobs"

    # Blob info
    blob_path = ""
    blob_set = "TestSet"
    pos_in_set = 0
    title = "Test Image"
    credit = "Credit Test"

    # Demo
    demo_id = -1

    # Template
    template_name = "Test Template"
    template_id = -1

    #####################
    #       Tests       #
    #####################
    def setUp(self):
        """
        Clean the DB from the tests
        """
        self.delete_demo(self.demo_id)
        self.delete_test_template()

    def test_ping(self):
        """
        Test ping
        """
        try:
            response = self.post(self.module, "get", "ping")
            status = response.status_code
        finally:
            self.assertEqual(status, 200)

    def test_add_blob_to_demo_without_visual_representation(self):
        """
        Test add blob to demo without visual representation
        """
        add_blob_status = None
        get_blob_status = None
        blob_title = None
        blob_url = None
        blob_vr = None
        delete_demo_status = None
        try:
            with open(self.blob_path, "rb") as blob:
                json_response, add_blob_status = self.add_blob_to_demo(
                    blob=blob,
                    demo_id=self.demo_id,
                    blob_set=self.blob_set,
                    pos_set=self.pos_in_set,
                    title=self.title,
                )

            json_response, get_blob_status = self.get_blobs(self.demo_id)
            try:
                blob_list = json_response[0].get("blobs").get(str(self.pos_in_set))
                blob_title = blob_list.get("title")
                blob_url = blob_list.get("blob")
                blob_vr = blob_list.get("vr")
            except Exception:
                pass

            _, delete_demo_status = self.delete_demo(self.demo_id)

        finally:
            self.assertEqual(add_blob_status, 201)
            self.assertEqual(get_blob_status, 200)
            self.assertEqual(blob_title, self.title)
            self.assertTrue(blob_url is not None)
            self.assertTrue(blob_vr is None)
            self.assertEqual(delete_demo_status, 204)

    def test_add_blob_to_demo_with_visual_representation(self):
        """
        Test add blob to demo with visual representation
        """
        add_blob_status = None
        get_blob_status = None
        blob_title = None
        blob_url = None
        blob_vr = None
        delete_demo_status = None
        try:
            with open(self.blob_path, "rb") as blob, open(self.blob_path, "rb") as vr:
                json_response, add_blob_status = self.add_blob_to_demo(
                    blob=blob,
                    demo_id=self.demo_id,
                    blob_set=self.blob_set,
                    pos_set=self.pos_in_set,
                    title=self.title,
                    blob_vr=vr,
                )

            json_response, get_blob_status = self.get_blobs(self.demo_id)
            try:
                blob_list = json_response[0].get("blobs").get(str(self.pos_in_set))
                blob_title = blob_list.get("title")
                blob_url = blob_list.get("blob")
                blob_vr = blob_list.get("vr")
            except Exception:
                pass

            _, delete_demo_status = self.delete_demo(self.demo_id)
        finally:
            self.assertEqual(add_blob_status, 201)
            self.assertEqual(get_blob_status, 200)
            self.assertEqual(blob_title, self.title)
            self.assertTrue(blob_url is not None)
            self.assertTrue(blob_vr is not None)
            self.assertEqual(delete_demo_status, 204)

    def test_create_template(self):
        """
        Test create template
        """
        create_status = None
        delete_status = None
        try:
            template_id, create_status = self.create_template(self.template_name)

            _, delete_status = self.delete_template(template_id)

        finally:
            self.assertEqual(create_status, 201)
            self.assertEqual(delete_status, 204)

    def test_add_blob_to_template_without_visual_representation(self):
        """
        Test add blob to template without visual representation
        """
        add_blob_status = None
        get_blob_status = None
        blob_title = None
        blob_url = None
        blob_vr = None
        delete_template_status = None
        try:
            template_id, _ = self.create_template(self.template_name)

            with open(self.blob_path, "rb") as blob:
                json_response, add_blob_status = self.add_blob_to_template(
                    blob=blob,
                    template_id=template_id,
                    blob_set=self.blob_set,
                    pos_set=self.pos_in_set,
                    title=self.title,
                )

            json_response, get_blob_status = self.get_template_blobs(template_id)
            try:
                blob_list = json_response[0].get("blobs").get(str(self.pos_in_set))
                blob_title = blob_list.get("title")
                blob_url = blob_list.get("blob")
                blob_vr = blob_list.get("vr")
            except Exception:
                pass

            _, delete_template_status = self.delete_template(template_id)

        finally:
            self.assertEqual(add_blob_status, 201)
            self.assertEqual(get_blob_status, 200)
            self.assertEqual(blob_title, self.title)
            self.assertTrue(blob_url is not None)
            self.assertTrue(blob_vr is None)
            self.assertEqual(delete_template_status, 204)

    def test_add_blob_to_template_with_visual_representation(self):
        """
        Test add blob to template with visual representation
        """
        add_blob_status = None
        get_blob_status = None
        blob_title = None
        blob_url = None
        blob_vr = None
        delete_template_status = None
        try:
            template_id, _ = self.create_template(self.template_name)

            with open(self.blob_path, "rb") as blob, open(self.blob_path, "rb") as vr:
                json_response, add_blob_status = self.add_blob_to_template(
                    blob=blob,
                    template_id=template_id,
                    blob_set=self.blob_set,
                    pos_set=self.pos_in_set,
                    title=self.title,
                    blob_vr=vr,
                )

            json_response, get_blob_status = self.get_template_blobs(template_id)
            try:
                blob_list = json_response[0].get("blobs").get(str(self.pos_in_set))
                blob_title = blob_list.get("title")
                blob_url = blob_list.get("blob")
                blob_vr = blob_list.get("vr")
            except Exception:
                pass

            _, delete_template_status = self.delete_template(template_id)

        finally:
            self.assertEqual(add_blob_status, 201)
            self.assertEqual(get_blob_status, 200)
            self.assertEqual(blob_title, self.title)
            self.assertTrue(blob_url is not None)
            self.assertTrue(blob_vr is not None)
            self.assertEqual(delete_template_status, 204)

    def test_add_blob_to_non_existent_template(self):
        """
        Test add blob to non existent template
        """
        status = None
        try:
            with open(self.blob_path, "rb") as blob:
                _, status = self.add_blob_to_template(
                    blob=blob,
                    template_id=self.template_id,
                    blob_set=self.blob_set,
                    pos_set=self.pos_in_set,
                    title=self.title,
                )

        finally:
            self.assertEqual(status, 404)

    def test_remove_blob_from_demo(self):
        """
        Test remove blob from demo
        """
        status = None
        try:
            with open(self.blob_path, "rb") as blob:
                self.add_blob_to_demo(
                    blob=blob,
                    demo_id=self.demo_id,
                    blob_set=self.blob_set,
                    pos_set=self.pos_in_set,
                    title=self.title,
                )

            response, status = self.remove_blob_from_demo(
                self.demo_id, self.blob_set, self.pos_in_set
            )

            response, _ = self.get_blobs(self.demo_id)
            self.delete_demo(self.demo_id)

        finally:
            self.assertEqual(status, 204)
            self.assertEqual(len(response), 0)

    def test_remove_blob_from_template(self):
        """
        Test remove blob from template
        """
        status = None
        set_list = None
        try:
            template_id, _ = self.create_template(self.template_name)

            with open(self.blob_path, "rb") as blob:
                self.add_blob_to_template(
                    blob=blob,
                    template_id=template_id,
                    blob_set=self.blob_set,
                    pos_set=self.pos_in_set,
                    title=self.title,
                )

            _, status = self.remove_blob_from_template(
                template_id, self.blob_set, self.pos_in_set
            )

            set_list, _ = self.get_template_blobs(template_id)

            self.delete_template(template_id)

        finally:
            self.assertEqual(status, 204)
            self.assertEqual(len(set_list), 0)

    def test_remove_non_existent_blob_from_demo(self):
        """
        Test remove non existent blob from demo
        """
        status = None
        try:
            _, status = self.remove_blob_from_demo(
                self.demo_id, self.blob_set, self.pos_in_set
            )

        finally:
            self.assertEqual(status, 204)

    def test_remove_non_existent_blob_from_template(self):
        """
        Test remove non existent blob from template
        """
        status = None
        try:
            _, status = self.remove_blob_from_template(
                self.template_id, self.blob_set, self.pos_in_set
            )

        finally:
            self.assertEqual(status, 204)

    def test_get_blob_from_non_existent_demo(self):
        """
        Test get blob from non existent demo
        """
        status = None
        try:
            _, status = self.get_blobs(self.demo_id)

        finally:
            # This should be OK because the demo can exist in the demoinfo DB
            self.assertEqual(status, 200)

    def test_get_blob_from_non_existent_template(self):
        """
        Test get blob from non existent template
        """
        status = None
        try:
            _, status = self.get_template_blobs(self.template_id)

        finally:
            self.assertEqual(status, 404)

    def test_add_template_to_demo(self):
        """
        Test add template to demo
        """
        status = None
        try:
            with open(self.blob_path, "rb") as blob:
                self.add_blob_to_demo(
                    blob=blob,
                    demo_id=self.demo_id,
                    blob_set=self.blob_set,
                    pos_set=self.pos_in_set,
                    title=self.title,
                )

            template_id, _ = self.create_template(self.template_name)
            self.add_template_to_demo(self.demo_id, template_id)

            templates, status = self.get_demo_templates(self.demo_id)
            template_name = templates[0]["name"]

            self.delete_demo(self.demo_id)
            self.delete_template(template_id)

        finally:
            self.assertEqual(status, 200)
            self.assertTrue(isinstance(templates, list))
            self.assertEqual(len(templates), 1)
            self.assertEqual(template_name, self.template_name)

    def test_add_non_existent_template_to_demo(self):
        """
        Test add non existent template to demo
        """
        status = None
        try:
            with open(self.blob_path, "rb") as blob:
                self.add_blob_to_demo(
                    blob=blob,
                    demo_id=self.demo_id,
                    blob_set=self.blob_set,
                    pos_set=self.pos_in_set,
                    title=self.title,
                )

            _, status = self.add_template_to_demo(self.demo_id, self.template_id)

            self.delete_demo(self.demo_id)

        finally:
            self.assertEqual(status, 404)

    def test_add_template_to_non_existent_demo(self):
        """
        Test add template to non existent demo
        """
        status = None
        try:
            template_id, _ = self.create_template(self.template_name)

            _, status = self.add_template_to_demo(self.demo_id, template_id)

            self.delete_template(template_id)

        finally:
            # This should be OK because the demo can exist in the demoinfo DB
            self.assertEqual(status, 201)

    def test_remove_template_from_demo(self):
        """
        Test remove template from demo
        """
        status = None
        template_list = None
        try:
            with open(self.blob_path, "rb") as blob:
                self.add_blob_to_demo(
                    blob=blob,
                    demo_id=self.demo_id,
                    blob_set=self.blob_set,
                    pos_set=self.pos_in_set,
                    title=self.title,
                )

            template_id, _ = self.create_template(self.template_name)
            self.add_template_to_demo(self.demo_id, template_id)

            _, status = self.remove_template_from_demo(self.demo_id, template_id)

            template_list, _ = self.get_demo_templates(self.demo_id)

            self.delete_template(template_id)
            self.delete_demo(self.demo_id)

        finally:
            self.assertEqual(status, 204)
            self.assertTrue(isinstance(template_list, list))
            self.assertEqual(len(template_list), 0)

    def test_remove_non_existent_template_from_demo(self):
        """
        Test remove non existent template from demo
        """
        status = None
        try:
            with open(self.blob_path, "rb") as blob:
                self.add_blob_to_demo(
                    blob=blob,
                    demo_id=self.demo_id,
                    blob_set=self.blob_set,
                    pos_set=self.pos_in_set,
                    title=self.title,
                )

            _, status = self.remove_template_from_demo(self.demo_id, self.template_id)

            self.delete_demo(self.demo_id)

        finally:
            self.assertEqual(status, 204)

    def test_remove_template_from_non_existent_demo(self):
        """
        Test remove template from non existent demo
        """
        status = None
        try:
            template_id, _ = self.create_template(self.template_name)
            self.add_template_to_demo(self.demo_id, template_id)

            _, status = self.remove_template_from_demo(self.demo_id, template_id)

            self.delete_template(template_id)

        finally:
            self.assertEqual(status, 204)

    def test_edit_blob_from_demo(self):
        """
        Test edit blob from demo
        """
        status = None
        new_title = self.title + "_new"
        title = None
        new_set = self.blob_set + "_new"
        the_set = None
        new_pos_in_set = self.pos_in_set + 1
        try:
            with open(self.blob_path, "rb") as blob:
                self.add_blob_to_demo(
                    blob=blob,
                    demo_id=self.demo_id,
                    blob_set=self.blob_set,
                    pos_set=self.pos_in_set,
                    title=self.title,
                )

            _, status = self.edit_blob_from_demo(
                demo_id=self.demo_id,
                blob_set=self.blob_set,
                new_blob_set=new_set,
                pos_set=self.pos_in_set,
                new_pos_set=new_pos_in_set,
                title=new_title,
            )

            json_response, _ = self.get_blobs(self.demo_id)
            try:
                blob_list = json_response[0].get("blobs").get(str(new_pos_in_set))
                the_set = json_response[0].get("name")
                title = blob_list.get("title")
            except Exception:
                pass

            self.delete_demo(self.demo_id)

        finally:
            self.assertEqual(status, 204)
            self.assertEqual(new_title, title)
            self.assertEqual(new_set, the_set)

    def test_edit_non_existent_blob_from_demo(self):
        """
        Test edit non existent blob from demo
        """
        status = None
        new_title = self.title + "_new"
        new_set = self.blob_set + "_new"
        new_pos_in_set = self.pos_in_set + 1
        try:
            _, status = self.edit_blob_from_demo(
                demo_id=self.demo_id,
                blob_set=self.blob_set,
                new_blob_set=new_set,
                pos_set=self.pos_in_set,
                new_pos_set=new_pos_in_set,
                title=new_title,
            )

        finally:
            self.assertEqual(status, 404)

    def test_edit_blob_from_template(self):
        """
        Test edit blob from template
        """
        status = None
        new_title = self.title + "_new"
        title = None
        new_set = self.blob_set + "_new"
        the_set = None
        new_pos_in_set = self.pos_in_set + 1
        try:
            template_id, _ = self.create_template(self.template_name)

            with open(self.blob_path, "rb") as blob:
                self.add_blob_to_template(
                    blob=blob,
                    template_id=template_id,
                    blob_set=self.blob_set,
                    pos_set=self.pos_in_set,
                    title=self.title,
                )

            _, status = self.edit_blob_from_template(
                template_id=template_id,
                title=new_title,
                blob_set=self.blob_set,
                new_blob_set=new_set,
                pos_set=self.pos_in_set,
                new_pos_set=new_pos_in_set,
            )

            json_response, _ = self.get_template_blobs(template_id)
            try:
                blob_list = json_response[0].get("blobs").get(str(new_pos_in_set))
                the_set = json_response[0].get("name")
                title = blob_list.get("title")
            except Exception:
                pass

            self.delete_template(template_id)

        finally:
            self.assertEqual(status, 204)
            self.assertEqual(new_title, title)
            self.assertEqual(new_set, the_set)

    def test_edit_non_existent_blob_from_template(self):
        """
        Test edit non existent blob from template
        """
        status = None
        new_title = self.title + "_new"
        new_set = self.blob_set + "_new"
        new_pos_in_set = self.pos_in_set + 1
        try:
            _, status = self.edit_blob_from_template(
                template_id=self.template_id,
                title=new_title,
                blob_set=self.blob_set,
                new_blob_set=new_set,
                pos_set=self.pos_in_set,
                new_pos_set=new_pos_in_set,
            )

        finally:
            self.assertEqual(status, 404)

    def test_get_all_templates(self):
        """
        Test get all templates
        """
        status = None
        templates = None
        try:
            template_id, _ = self.create_template(self.template_name)

            templates, status = self.get_all_templates()

            self.delete_template(template_id)
        finally:
            self.assertEqual(status, 200)
            self.assertTrue(isinstance(templates, list))
            self.assertTrue(len(templates) > 0)

    def test_remove_visual_representation_from_blob(self):
        """
        Test remove visual representation from blob
        """
        status = None
        blob_vr = None
        try:
            with open(self.blob_path, "rb") as blob, open(self.blob_path, "rb") as vr:
                self.add_blob_to_demo(
                    blob=blob,
                    demo_id=self.demo_id,
                    blob_vr=vr,
                    blob_set=self.blob_set,
                    pos_set=self.pos_in_set,
                    title=self.title,
                )
            json_response, _ = self.get_blobs(self.demo_id)
            blob_id = None
            try:
                blob_list = json_response[0].get("blobs").get(str(self.pos_in_set))
                blob_id = blob_list.get("id")
            except Exception:
                pass

            _, status = self.delete_vr_from_blob(blob_id)

            json_response, _ = self.get_blobs(self.demo_id)
            try:
                blob_list = json_response[0].get("blobs").get(str(self.pos_in_set))
                blob_vr = blob_list.get("vr")
            except Exception:
                pass

            self.delete_demo(self.demo_id)

        finally:
            self.assertEqual(status, 204)
            self.assertTrue(blob_vr is None)

    def test_remove_visual_representation_from_non_existent_blob(self):
        """
        Test remove visual representation from non existent blob
        """
        status = None
        try:
            _, status = self.delete_vr_from_blob(0)
        finally:
            self.assertEqual(status, 204)

    #####################
    #       TOOLS       #
    #####################

    def post(self, module, method, service, **kwargs):
        """
        post
        """
        url = f"{self.BASE_URL}/api/{module}/{service}"
        if method == "get":
            return requests.get(url)
        elif method == "put":
            return requests.put(url, **kwargs)
        elif method == "post":
            return requests.post(url, **kwargs)
        elif method == "delete":
            return requests.delete(url, **kwargs)
        else:
            assert False

    def add_blob_to_demo(
        self,
        blob=None,
        demo_id=None,
        blob_set=None,
        pos_set=None,
        title=None,
        credit=None,
        blob_vr=None,
    ):
        """
        add blob to demo
        """
        params = {}
        if demo_id is not None:
            params["demo_id"] = demo_id
        if blob_set is not None:
            params["blob_set"] = blob_set
        if pos_set is not None:
            params["pos_set"] = pos_set
        if title is not None:
            params["title"] = title
        if credit is not None:
            params["credit"] = credit
        files = {}
        if blob is not None:
            files["blob"] = blob
        if blob_vr is not None:
            files["blob_vr"] = blob_vr
        response = self.post(
            self.module, "post", f"/demo_blobs/{demo_id}", params=params, files=files
        )
        return response.json(), response.status_code

    def add_blob_to_template(
        self,
        blob=None,
        template_id=None,
        blob_set=None,
        pos_set=None,
        title=None,
        credit=None,
        blob_vr=None,
    ):
        """
        add blob to template
        """
        params = {}
        if template_id is not None:
            params["template_id"] = template_id
        if blob_set is not None:
            params["blob_set"] = blob_set
        if pos_set is not None:
            params["pos_set"] = pos_set
        if title is not None:
            params["title"] = title
        if credit is not None:
            params["credit"] = credit
        files = {}
        if blob is not None:
            files["blob"] = blob
        if blob_vr is not None:
            files["blob_vr"] = blob_vr
        response = self.post(
            self.module,
            "post",
            f"/template_blobs/{template_id}",
            params=params,
            files=files,
        )
        return response.json(), response.status_code

    def delete_demo(self, demo_id):
        """
        delete demo
        """
        response = self.post(self.module, "delete", f"demos/{demo_id}")
        return response, response.status_code

    def get_blobs(self, demo_id):
        """
        get blobs
        """
        response = self.post(self.module, "get", f"demo_blobs/{demo_id}")
        return response.json(), response.status_code

    def get_template_blobs(self, template_id):
        """
        get template blobs
        """
        response = self.post(self.module, "get", f"templates/{template_id}")
        return response.json(), response.status_code

    def remove_blob_from_demo(self, demo_id, blob_set, pos_set):
        """
        remove blob from demo
        """
        params = {"demo_id": demo_id, "blob_set": blob_set, "pos_set": pos_set}
        response = self.post(
            self.module, "delete", f"demo_blobs/{demo_id}", params=params
        )
        return response, response.status_code

    def create_template(self, template_name):
        """
        create template
        """
        params = {"template_name": template_name}
        response = self.post(self.module, "post", "templates", params=params)

        template_id = response.json().get("template_id")
        return template_id, response.status_code

    def delete_template(self, template_id):
        """
        delete template
        """
        response = self.post(self.module, "delete", f"templates/{template_id}")
        return response, response.status_code

    def delete_test_template(self):
        """
        delete test template
        """
        templates = self.post(self.module, "get", "templates").json()
        for template in templates:
            if self.template_name == template["name"]:
                return self.post(self.module, "delete", f"templates/{template['id']}")

    def remove_blob_from_template(self, template_id, blob_set, pos_set):
        """
        remove blob from template
        """
        params = {"template_id": template_id, "blob_set": blob_set, "pos_set": pos_set}
        response = self.post(
            self.module, "delete", f"template_blobs/{template_id}", params=params
        )
        return response, response.status_code

    def add_template_to_demo(self, demo_id, template_ids):
        """
        add templates to demo
        """
        params = {"template_id": template_ids}
        response = self.post(
            self.module, "post", f"add_template_to_demo/{demo_id}", params=params
        )
        return response, response.status_code

    def get_demo_templates(self, demo_id):
        """
        get demo templates
        """
        response = self.post(self.module, "get", f"demo_templates/{demo_id}")
        return response.json(), response.status_code

    def remove_template_from_demo(self, demo_id, template_id):
        """
        remove template from demo
        """
        params = {"template_id": template_id}
        response = self.post(
            self.module, "delete", f"demo_templates/{demo_id}", params=params
        )
        return response, response.status_code

    def edit_blob_from_demo(
        self,
        demo_id=None,
        blob_set=None,
        new_blob_set=None,
        pos_set=None,
        new_pos_set=None,
        title=None,
        credit=None,
        vr=None,
    ):
        """
        edit blob from demo
        """
        params = {}
        if demo_id is not None:
            params["demo_id"] = demo_id
        if blob_set is not None:
            params["blob_set"] = blob_set
        if new_blob_set is not None:
            params["new_blob_set"] = new_blob_set
        if pos_set is not None:
            params["pos_set"] = pos_set
        if new_pos_set is not None:
            params["new_pos_set"] = new_pos_set
        if title is not None:
            params["title"] = title
        if credit is not None:
            params["credit"] = credit
        files = {}
        if vr is not None:
            files["blob_vr"] = vr
        response = self.post(
            self.module, "put", f"demo_blobs/{demo_id}", params=params, files=files
        )
        return response, response.status_code

    def edit_blob_from_template(
        self,
        template_id=None,
        blob_set=None,
        new_blob_set=None,
        pos_set=None,
        new_pos_set=None,
        title=None,
        credit=None,
        vr=None,
    ):
        """
        edit blob from template
        """
        params = {}
        if template_id is not None:
            params["template_id"] = template_id
        if blob_set is not None:
            params["blob_set"] = blob_set
        if new_blob_set is not None:
            params["new_blob_set"] = new_blob_set
        if pos_set is not None:
            params["pos_set"] = pos_set
        if new_pos_set is not None:
            params["new_pos_set"] = new_pos_set
        if title is not None:
            params["title"] = title
        if credit is not None:
            params["credit"] = credit
        files = {}
        if vr is not None:
            files["blob_vr"] = vr
        response = self.post(
            self.module,
            "put",
            f"template_blobs/{template_id}",
            params=params,
            files=files,
        )
        return response, response.status_code

    def get_all_templates(self):
        """
        get all templates
        """
        response = self.post(self.module, "get", "/templates")
        return response.json(), response.status_code

    def delete_vr_from_blob(self, blob_id):
        """
        delete vr from blob
        """
        response = self.post(self.module, "delete", f"visual_representations/{blob_id}")
        return response, response.status_code


if __name__ == "__main__":
    shared_folder = sys.argv.pop()
    demorunners = sys.argv.pop()
    resources_path = sys.argv.pop()
    BlobsTests.blob_path = os.path.join(resources_path, "test_image.png")
    unittest.main()
