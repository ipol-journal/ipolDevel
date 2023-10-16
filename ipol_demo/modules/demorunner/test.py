#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demorunner test
"""
import io
import json
import os
import shutil
import socket
import sys
import tarfile

# Unit tests for the Blobs module
import unittest
import xml.etree.ElementTree as ET
import zipfile

import requests
from PIL import Image


def load_demorunners(demorunners_file):
    """
    Read demorunners xml
    """
    dict_demorunners = {}
    tree = ET.parse(demorunners_file)
    root = tree.getroot()

    for demorunner in root.findall("demorunner"):
        dict_tmp = {}
        list_tmp = []

        for capability in demorunner.findall("capability"):
            list_tmp.append(capability.text)

        dict_tmp["serverSSH"] = demorunner.find("serverSSH").text
        dict_tmp["capability"] = list_tmp
        dict_tmp["name"] = demorunner.get("name")

        if any(c.endswith("!") for c in dict_tmp["capability"]):
            # don't run tests on non-standard demorunners
            continue

        dict_demorunners[demorunner.get("name")] = dict_tmp

    return dict_demorunners


class DemorunnerTests(unittest.TestCase):
    """
    Demorunner Tests
    """

    module = "demorunner"

    # Demo
    demo_id = -1
    key = "48AF3CB426BA877EA46E7B24A98ADA9B"

    # Shared folder
    shared_folder = None

    # Resources
    ddl_file = None
    blob_path = None
    test_demo_extras_file = None

    # Demo Runners
    demorunners = {}
    base_url = os.environ.get("IPOL_URL", "http://" + socket.getfqdn())

    #####################
    #       Tests       #
    #####################
    def setUp(self):
        """
        Clean the DB from the tests
        """
        try:
            self.delete_extras_folder()
        except Exception:
            pass

    def test_ping(self):
        """
        Test ping
        """
        status_list = []
        try:
            for dr in self.demorunners.values():
                _, status = self.post_to_dr(dr, "ping", method="get")
        finally:
            for status in status_list:
                self.assertEqual(status, 200)

    def test_workload(self):
        """
        Test workload
        """
        status_list = []
        workload_list = []
        try:
            for dr in self.demorunners.values():
                response, status = self.get_workload(dr)
                status_list.append(status)
                workload_list.append(response)
        finally:
            for status in status_list:
                self.assertEqual(status, 200)
            for workload in workload_list:
                self.assertTrue(isinstance(workload, float))

    def test_ensure_compilation(self):
        """
        Test ensure compilation
        """
        status_list = []
        try:
            for dr in self.demorunners.values():
                self.create_extras_folder()

                with open(self.ddl_file, "r") as f:
                    ddl = f.read()
                ddl_json = json.loads(ddl)

                self.post_to_dr(dr, f"compilations/{self.demo_id}", method="delete")
                status = self.ensure_compilation(dr, self.demo_id, ddl_json["build"])
                status_list.append(status)

                self.delete_extras_folder()
        finally:
            for status in status_list:
                self.assertEqual(status, 201)

    def test_ensure_compilation_without_demo_extras_folder(self):
        """
        Test ensure compilation without demo extras folder
        """
        status_list = []
        try:
            for dr in self.demorunners.values():
                with open(self.ddl_file, "r") as f:
                    ddl = f.read()
                ddl_json = json.loads(ddl)

                self.post_to_dr(dr, f"compilations/{self.demo_id}", method="delete")
                status = self.ensure_compilation(dr, self.demo_id, ddl_json["build"])
                status_list.append(status)

        finally:
            for status in status_list:
                self.assertEqual(status, 201)

    def test_exec_and_wait(self):
        """
        Test exec and wait
        """
        status_list = []
        try:
            blob_image = Image.open(self.blob_path)
            width, height = blob_image.size
            for dr in self.demorunners.values():
                files = self.get_input_files()
                self.create_extras_folder()

                with open(self.ddl_file, "r") as f:
                    ddl = f.read()
                ddl_json = json.loads(ddl)
                run = ddl_json["run"]

                self.post_to_dr(dr, f"compilations/{self.demo_id}", method="delete")
                self.ensure_compilation(dr, self.demo_id, ddl_json["build"])

                params = json.dumps({"x0": 0, "x1": width, "y0": 0, "y1": height})
                _, status = self.exec_and_wait(
                    dr, self.demo_id, self.key, params, run, files
                )
                status_list.append(status)

                self.delete_extras_folder()
        finally:
            for status in status_list:
                self.assertEqual(status, 200)

    #####################
    #       TOOLS       #
    #####################

    def post_to_dr(self, demorunner, service, method="post", **kwargs):
        """
        post
        """
        url = "{}/api/demorunner/{}/{}".format(
            self.base_url, demorunner["name"], service
        )
        if method == "get":
            response = requests.get(url)
            return response, response.status_code
        elif method == "put":
            response = requests.put(url, **kwargs)
            return response, response.status_code
        elif method == "post":
            response = requests.post(url, **kwargs)
            return response, response.status_code
        elif method == "delete":
            response = requests.delete(url, **kwargs)
            return response, response.status_code
        else:
            assert False

    def get_input_files(self):
        """
        create input files
        """
        inputs = {
            "files": (
                "./input_0.png",
                open(self.blob_path, "rb"),
                "application/octet-stream",
            ),
        }
        return inputs

    def create_extras_folder(self):
        """
        create extras folder
        """
        dl_extras_folder = os.path.join(
            self.shared_folder, "dl_extras", str(self.demo_id)
        )
        demo_extras_folder = os.path.join(
            self.shared_folder, "demoExtras", str(self.demo_id)
        )

        demo_extras = open(self.test_demo_extras_file, "rb")
        os.makedirs(dl_extras_folder)
        os.makedirs(demo_extras_folder)
        with open(os.path.join(dl_extras_folder, "DemoExtras.tar.gz"), "wb") as f:
            f.write(demo_extras.read())

        ar = tarfile.open(self.test_demo_extras_file)
        ar.extractall(demo_extras_folder)
        demo_extras.close()

    def delete_extras_folder(self):
        """
        delete extras folder
        """
        dl_extras_folder = os.path.join(
            self.shared_folder, "dl_extras", str(self.demo_id)
        )
        demo_extras_folder = os.path.join(
            self.shared_folder, "demoExtras", str(self.demo_id)
        )
        shutil.rmtree(dl_extras_folder)
        shutil.rmtree(demo_extras_folder)

    def get_workload(self, dr):
        """
        get workload
        """
        response, response_code = self.post_to_dr(dr, "workload", "get")
        return response.json(), response_code

    def exec_and_wait(self, dr, demo_id, key, params, ddl_run, files):
        """
        exec and wait
        """
        data = {"key": key, "ddl_run": ddl_run, "parameters": params}
        dr_response, status_code = self.post_to_dr(
            dr,
            f"exec_and_wait/{demo_id}",
            params=data,
            files=files,
        )
        if status_code == 200:
            zipcontent = io.BytesIO(dr_response.content)
            zip = zipfile.ZipFile(zipcontent)
            exec_info = zip.read("exec_info.json")
            response = json.loads(exec_info)
            return response, status_code
        else:
            return dr_response, status_code

    def ensure_compilation(self, dr, demo_id, ddl_build):
        """
        ensure compilation
        """
        data = json.dumps({"ddl_build": ddl_build})
        _, status_code = self.post_to_dr(dr, f"compilations/{demo_id}", data=data)
        return status_code


if __name__ == "__main__":
    shared_folder = sys.argv.pop()
    demorunners = sys.argv.pop()
    resources_path = sys.argv.pop()

    DemorunnerTests.shared_folder = shared_folder
    DemorunnerTests.demorunners = load_demorunners(demorunners)
    DemorunnerTests.ddl_file = os.path.join(resources_path, "test_ddl.txt")
    DemorunnerTests.blob_path = os.path.join(resources_path, "test_image.png")
    DemorunnerTests.test_demo_extras_file = os.path.join(
        resources_path, "test_demo_extras.tar.gz"
    )
    unittest.main()
