#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import socket
import sys
import unittest

import requests
from PIL import Image


class IntegrationTests(unittest.TestCase):
    """
    Integration Tests
    """

    # General
    BASE_URL = os.environ.get("IPOL_URL", "http://" + socket.getfqdn())

    # These variables are initialized in the __main__
    test_ddl_file = None
    test_demo_extras_file = None
    test_image_file = None

    blob_set_name = "set"
    blob_pos_in_set = 0
    blobset_id = 0

    # Demo info
    demo_id = -1
    demo_title = "Demo test"
    demo_state = "test"

    #####################
    #       Tests       #
    #####################
    def setUp(self):
        """
        Clean the DB from the tests
        """
        # Delete demo test
        self.delete_demo(self.demo_id)

    def test_execution_with_blobset(self):
        """
        Test the normal flow of IPOL. Creates a demo, add DDL, DemoExtras and blob
        and execute it with the blob in the blobset
        """
        create_demo_status = None
        add_ddl_status = None
        demo_extras_status = None
        add_blob_status = None
        blob_id = None
        run_status = None
        delete_demo_status = None
        try:
            # Create Demo
            response, _ = self.create_demo(
                self.demo_id, self.demo_title, self.demo_state
            )
            create_demo_status = response.get("status")

            # Add DDL to demo
            with open(self.test_ddl_file, "r") as f:
                ddl = f.read()
            response, _ = self.add_ddl(self.demo_id, ddl)
            add_ddl_status = response.get("status")

            # Add DemoExtras.gz
            with open(self.test_demo_extras_file, "rb") as demo_extras:
                demo_extras_name = os.path.basename(demo_extras.name)
                response, _ = self.add_demo_extras(
                    self.demo_id, demo_extras, demo_extras_name
                )
            demo_extras_status = response.get("status")

            # Add the test blob to the demo in the Blobs module
            with open(self.test_image_file, "rb") as blob:
                response, add_blob_status = self.add_blob(
                    self.demo_id,
                    blob,
                    self.demo_title,
                    self.blob_set_name,
                    self.blob_pos_in_set,
                )

                # Get the blob id
                blob_id = self.get_blob_id(self.demo_id, self.blob_pos_in_set)
                # Run the demo with the uploaded image
                blob_image = Image.open(blob.name)
            response = self.run_demo_with_blobset(
                self.demo_id, blob_image, blob_id, self.blobset_id
            )
            run_status = response.get("status")

            # Delete demo in Demoinfo and Blobs
            response, _ = self.delete_demo(self.demo_id)
            delete_demo_status = response.get("status")

        finally:
            self.assertEqual(create_demo_status, "OK")
            self.assertEqual(add_ddl_status, "OK")
            self.assertEqual(demo_extras_status, "OK")
            self.assertEqual(add_blob_status, 201)
            self.assertTrue(isinstance(blob_id, int))
            self.assertEqual(run_status, "OK")
            self.assertEqual(delete_demo_status, "OK")

    def test_execution_with_upload(self):
        """
        Test the normal flow of IPOL. Creates a demo, add DDL, DemoExtras
        and execute it with an uploaded blob
        """
        create_demo_status = None
        add_ddl_status = None
        demo_extras_status = None
        run_status = None
        experiments = None
        n_experiments = None
        archive_status = None
        delete_demo_status = None
        try:
            # Create Demo
            response, _ = self.create_demo(
                self.demo_id, self.demo_title, self.demo_state
            )
            create_demo_status = response.get("status")

            # Add DDL to demo
            with open(self.test_ddl_file, "r") as f:
                ddl = f.read()
            response, _ = self.add_ddl(self.demo_id, ddl)
            add_ddl_status = response.get("status")

            # Add DemoExtras.gz
            with open(self.test_demo_extras_file, "rb") as demo_extras:
                demo_extras_name = os.path.basename(demo_extras.name)
                response, _ = self.add_demo_extras(
                    self.demo_id, demo_extras, demo_extras_name
                )
            demo_extras_status = response.get("status")

            # Run the demo with the uploaded image
            with open(self.test_image_file, "rb") as blob:
                with Image.open(self.test_image_file) as blob_image:
                    width, height = blob_image.size
                response = self.run_demo_with_uploaded_blob(
                    self.demo_id, blob, width, height
                )
            run_status = response.get("status")

            response, status_code = self.get_archive_experiments_by_page(
                self.BASE_URL, self.demo_id
            )
            archive_status = status_code
            experiments = response.get("experiments")
            exp_meta = response.get("meta_info")
            try:
                n_experiments = exp_meta.get("number_of_experiments")
            except Exception:
                pass

            # Delete demo
            response, _ = self.delete_demo(self.demo_id)
            delete_demo_status = response.get("status")

        finally:
            self.assertEqual(create_demo_status, "OK")
            self.assertEqual(add_ddl_status, "OK")
            self.assertEqual(demo_extras_status, "OK")
            self.assertEqual(run_status, "OK")
            self.assertEqual(archive_status, 200)
            self.assertTrue(isinstance(experiments, list))
            self.assertTrue(n_experiments > 0)
            self.assertEqual(delete_demo_status, "OK")

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

    def check_status(self, response, error_msg):
        """
        If the response is not OK it will log the error
        """
        if "status" not in response or response["status"] == "KO":
            print("{}. Response from the module: {}".format(error_msg, response))

    def create_demo(self, demo_id, title, state):
        """
        Creates a demo
        """
        params = {"demo_id": demo_id, "title": title, "state": state}
        response = self.post(
            "demoinfo",
            "post",
            "add_demo",
            params=params,
        )
        return response.json(), response.status_code

    def add_ddl(self, demo_id, ddl):
        """
        Add the ddl to the demo
        """
        params = {"demoid": demo_id}
        response = self.post(
            "demoinfo", "post", "save_ddl", params=params, json=json.loads(ddl)
        )
        return response.json(), response.status_code

    def add_demo_extras(self, demo_id, demo_extras, demo_extras_name):
        """
        Add DemoExtras to the demo
        """
        files = {"demoextras": demo_extras}
        params = {"demo_id": demo_id, "demoextras_name": demo_extras_name}
        response = self.post(
            "demoinfo", "post", "add_demoextras", params=params, files=files
        )
        return response.json(), response.status_code

    def add_blob(self, demo_id, blob, demo_title, set_name, pos_in_set):
        """
        Add a blob to the demo
        """
        files = {"blob": blob}
        params = {
            "title": demo_title,
            "blob_set": set_name,
            "pos_set": pos_in_set,
        }
        response = self.post(
            "blobs", "post", f"demo_blobs/{demo_id}", params=params, files=files
        )
        return response.json(), response.status_code

    def get_blob_id(self, demo_id, pos_in_set):
        """
        Return the blob id
        """
        response = self.post("blobs", "get", f"demo_blobs/{demo_id}")
        json_response = response.json()
        if response.status_code == 200:
            return json_response[0]["blobs"][str(pos_in_set)]["id"]

    def run_demo_with_blobset(self, demo_id, blob, blob_id, blobset_id):
        """
        Runs the demo with the blob given
        """
        width, height = blob.size
        params = {
            "demo_id": demo_id,
            "origin": "blobSet",
            "params": {},
            "crop_info": {
                "x": 20,
                "y": 9.199999999999996,
                "width": width,
                "height": height,
                "rotate": 0,
                "scaleX": 1,
                "scaleY": 1,
            },
            "blobs": {"id_blobs": [blob_id]},
            "setId": blobset_id,
        }
        response = self.post(
            "core", "post", "run", data={"clientData": json.dumps(params)}
        )
        return response.json()

    def run_demo_with_uploaded_blob(self, demo_id, blob, width, height):
        params = {
            "demo_id": demo_id,
            "origin": "upload",
            "params": {},
        }
        files = {"file_0": blob}
        response = self.post(
            "core", "post", "run", data={"clientData": json.dumps(params)}, files=files
        )
        return response.json()

    def delete_demo(self, demo_id):
        """
        Delete demo from demoinfo
        """
        params = {"demo_id": demo_id}
        response = self.post("core", "post", "delete_demo", params=params)
        return response.json(), response.status_code

    def get_archive_experiments_by_page(self, url, demo_id, page=None):
        if page is None:
            page = 0
        response = requests.get(f"{url}/api/archive/page/{page}?demo_id={demo_id}")
        return response.json(), response.status_code


if __name__ == "__main__":
    shared_folder = sys.argv.pop()
    demorunners = sys.argv.pop()
    resources_path = sys.argv.pop()
    IntegrationTests.test_ddl_file = os.path.join(resources_path, "test_ddl.txt")
    IntegrationTests.test_demo_extras_file = os.path.join(
        resources_path, "test_demo_extras.tar.gz"
    )
    IntegrationTests.test_image_file = os.path.join(resources_path, "test_image.png")
    unittest.main()
