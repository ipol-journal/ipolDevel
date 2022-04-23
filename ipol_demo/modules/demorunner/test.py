#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demorunner test
"""
import json
import os
import shutil
import sys
import tarfile
# Unit tests for the Blobs module
import unittest
import xml.etree.ElementTree as ET

import requests
from PIL import Image


def load_demorunners(demorunners_file):
    """
    Read demorunners xml
    """
    dict_demorunners = {}
    tree = ET.parse(demorunners_file)
    root = tree.getroot()

    for demorunner in root.findall('demorunner'):
        dict_tmp = {}
        list_tmp = []

        for capability in demorunner.findall('capability'):
            list_tmp.append(capability.text)

        dict_tmp["server"] = demorunner.find('server').text
        dict_tmp["serverSSH"] = demorunner.find('serverSSH').text
        dict_tmp["capability"] = list_tmp

        if any(c.endswith("!") for c in dict_tmp["capability"]):
            # don't run tests on non-standard demorunners
            continue

        dict_demorunners[demorunner.get('name')] = dict_tmp

    return dict_demorunners


class DemorunnerTests(unittest.TestCase):
    """
    Demorunner Tests
    """
    module = 'demorunner'

    # Demo
    demo_id = -1
    execution_folder = '48AF3CB426BA877EA46E7B24A98ADA9B'

    # Shared folder
    shared_folder = None

    # Resources
    ddl_file = None
    blob_path = None
    test_demo_extras_file = None

    # Demo Runners
    demorunners = []

    #####################
    #       Tests       #
    #####################
    def setUp(self):
        """
        Clean the DB from the tests
        """
        try:
            self.delete_extras_folder()
            self.delete_workdir()
        except Exception:
            pass

    def test_ping(self):
        """
        Test ping
        """
        status_list = []
        try:

            for demorunner in self.demorunners:
                response = self.post(self.demorunners[demorunner].get('server'), self.module, 'ping')
                json_response = response.json()
                status_list.append(json_response.get('status'))
        finally:
            for status in status_list:
                self.assertEqual(status, 'OK')

    def test_workload(self):
        """
        Test workload
        """
        status_list = []
        workload_list = []
        try:

            for demorunner in self.demorunners:
                response = self.get_workload(self.demorunners[demorunner].get('server'))
                status_list.append(response.get('status'))
                workload_list.append(response.get('workload'))
        finally:
            for status in status_list:
                self.assertEqual(status, 'OK')
            for workload in workload_list:
                self.assertTrue(isinstance(workload, float))

    def test_ensure_compilation(self):
        """
        Test ensure compilation
        """
        status_list = []
        try:

            for demorunner in self.demorunners:
                self.create_extras_folder()

                with open(self.ddl_file, 'r') as f:
                    ddl = f.read()
                ddl_json = json.loads(ddl)
                build = json.dumps(ddl_json['build'])
                host = self.demorunners[demorunner].get('server')

                self.post(host, self.module, 'delete_compilation', data={'demo_id': self.demo_id})
                response = self.ensure_compilation(host, self.demo_id, build)
                status_list.append(response.get('status'))

                self.delete_extras_folder()
        finally:
            for status in status_list:
                self.assertEqual(status, 'OK')

    def test_ensure_compilation_without_demo_extras_folder(self):
        """
        Test ensure compilation without demo extras folder
        """
        status_list = []
        try:
            for demorunner in self.demorunners:

                with open(self.ddl_file, 'r') as f:
                    ddl = f.read()
                ddl_json = json.loads(ddl)
                build = json.dumps(ddl_json['build'])
                host = self.demorunners[demorunner].get('server')

                self.post(host, self.module, 'delete_compilation', data={'demo_id': self.demo_id})
                response = self.ensure_compilation(host, self.demo_id, build)
                status_list.append(response.get('status'))

        finally:
            for status in status_list:
                self.assertEqual(status, 'OK')

    def test_exec_and_wait(self):
        """
        Test exec and wait
        """
        status_list = []
        try:

            blob_image = Image.open(self.blob_path)
            width, height = blob_image.size
            for demorunner in self.demorunners:
                self.create_extras_folder()
                self.create_work_dir()

                with open(self.ddl_file, 'r') as f:
                    ddl = f.read()
                ddl_json = json.loads(ddl)
                run = json.dumps(ddl_json['run'])
                build = json.dumps(ddl_json['build'])
                host = self.demorunners[demorunner].get('server')

                self.post(host, self.module, 'delete_compilation', data={'demo_id': self.demo_id})
                self.ensure_compilation(host, self.demo_id, build)

                params = json.dumps({'x0': 0, 'x1': width, 'y0': 0, 'y1': height})
                response = self.exec_and_wait(host, self.demo_id, self.execution_folder, params, run)
                status_list.append(response.get('status'))

                self.delete_workdir()
                self.delete_extras_folder()
        finally:
            for status in status_list:
                self.assertEqual(status, 'OK')

    def test_exec_and_wait_without_execution_folder(self):
        """
        Test exec and wait without execution folder
        """
        status_list = []
        try:

            blob_image = Image.open(self.blob_path)
            width, height = blob_image.size
            for demorunner in self.demorunners:
                self.create_extras_folder()

                with open(self.ddl_file, 'r') as f:
                    ddl = f.read()
                ddl_json = json.loads(ddl)
                run = json.dumps(ddl_json['run'])
                build = json.dumps(ddl_json['build'])
                host = self.demorunners[demorunner].get('server')

                self.post(host, self.module, 'delete_compilation', data={'demo_id': self.demo_id})
                self.ensure_compilation(host, self.demo_id, build)

                params = json.dumps({'x0': 0, 'x1': width, 'y0': 0, 'y1': height})
                response = self.exec_and_wait(host, self.demo_id, self.execution_folder, params, run)
                status_list.append(response.get('status'))

                self.delete_extras_folder()
        finally:
            for status in status_list:
                self.assertEqual(status, 'KO')


    #####################
    #       TOOLS       #
    #####################

    @staticmethod
    def post(host, module, service, params=None, data=None, files=None, servicejson=None):
        """
        post
        """
        url = 'http://{}/api/{}/{}'.format(host, module, service)
        return requests.post(url, params=params, data=data, files=files, json=servicejson)

    def create_work_dir(self):
        """
        create work dir
        """
        run_folder = os.path.join(self.shared_folder, 'run', str(self.demo_id))
        os.makedirs(os.path.join(run_folder, self.execution_folder))
        with open(os.path.join(run_folder, self.execution_folder, 'input_0.png'), 'wb') as f, open(self.blob_path, 'rb') as blob:
            f.write(blob.read())

        blob.close()

    def delete_workdir(self):
        """
        delete workdir
        """
        run_folder = os.path.join(self.shared_folder, 'run', str(self.demo_id))
        shutil.rmtree(os.path.join(run_folder))

    def create_extras_folder(self):
        """
        create extras folder
        """
        dl_extras_folder = os.path.join(self.shared_folder, 'dl_extras', str(self.demo_id))
        demo_extras_folder = os.path.join(self.shared_folder, 'demoExtras', str(self.demo_id))

        demo_extras = open(self.test_demo_extras_file, 'rb')
        os.makedirs(dl_extras_folder)
        os.makedirs(demo_extras_folder)
        with open(os.path.join(dl_extras_folder, 'DemoExtras.tar.gz'), 'wb') as f:
            f.write(demo_extras.read())

        ar = tarfile.open(self.test_demo_extras_file)
        ar.extractall(demo_extras_folder)
        demo_extras.close()

    def delete_extras_folder(self):
        """
        delete extras folder
        """
        dl_extras_folder = os.path.join(self.shared_folder, 'dl_extras', str(self.demo_id))
        demo_extras_folder = os.path.join(self.shared_folder, 'demoExtras', str(self.demo_id))
        shutil.rmtree(dl_extras_folder)
        shutil.rmtree(demo_extras_folder)

    def get_workload(self, host):
        """
        get workload
        """
        response = self.post(host, self.module, 'get_workload')
        return response.json()

    def exec_and_wait(self, host, demo_id, key, params, ddl_run):
        """
        exec and wait
        """
        data = {'demo_id': str(demo_id), 'key': key, 'params': params, 'ddl_run': ddl_run}
        response = self.post(host, self.module, 'exec_and_wait', data=data)
        return response.json()

    def ensure_compilation(self, host, demo_id, ddl_build):
        """
        ensure compilation
        """
        data = {'demo_id': demo_id, 'ddl_build': ddl_build}
        response = self.post(host, self.module, 'ensure_compilation', data=data)
        return response.json()


if __name__ == '__main__':
    shared_folder = sys.argv.pop()
    demorunners = sys.argv.pop()
    resources_path = sys.argv.pop()

    DemorunnerTests.shared_folder = shared_folder
    DemorunnerTests.demorunners = load_demorunners(demorunners)
    DemorunnerTests.ddl_file = os.path.join(resources_path, 'test_ddl.txt')
    DemorunnerTests.blob_path = os.path.join(resources_path, 'test_image.png')
    DemorunnerTests.test_demo_extras_file = os.path.join(resources_path, 'test_demo_extras.tar.gz')
    unittest.main()
