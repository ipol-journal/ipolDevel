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
    BASE_URL = os.environ.get('IPOL_URL', 'http://' + socket.getfqdn())

    # These variables are initialized in the __main__
    test_ddl_file = None
    test_demo_extras_file = None
    test_image_file = None

    blob_set_name = 'set'
    blob_pos_in_set = 0
    blobset_id = 0

    # Demo info
    demo_id = -1
    demo_title = 'Demo test'
    demo_state = 'test'

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
            response = self.create_demo(self.demo_id, self.demo_title, self.demo_state)
            create_demo_status = response.get('status')

            # Add DDL to demo
            with open(self.test_ddl_file, 'r') as f:
                ddl = f.read()
            response = self.add_ddl(self.demo_id, ddl)
            add_ddl_status = response.get('status')

            # Add DemoExtras.gz
            with open(self.test_demo_extras_file, 'rb') as demo_extras:
                demo_extras_name = os.path.basename(demo_extras.name)
                response = self.add_demo_extras(self.demo_id, demo_extras, demo_extras_name)
            demo_extras_status = response.get('status')

            # Add the test blob to the demo in the Blobs module
            with open(self.test_image_file, 'rb') as blob:
                response = self.add_blob(self.demo_id, blob, self.demo_title, self.blob_set_name,
                                         self.blob_pos_in_set)
                add_blob_status = response.get('status')

                # Get the blob id
                blob_id = self.get_blob_id(self.demo_id, self.blob_pos_in_set)
                # Run the demo with the uploaded image
                blob_image = Image.open(blob.name)
            response = self.run_demo_with_blobset(self.demo_id, blob_image, blob_id, self.blobset_id)
            run_status = response.get('status')

            # Delete demo in Demoinfo and Blobs
            response = self.delete_demo(self.demo_id)
            delete_demo_status = response.get('status')

        finally:
            self.assertEqual(create_demo_status, 'OK')
            self.assertEqual(add_ddl_status, 'OK')
            self.assertEqual(demo_extras_status, 'OK')
            self.assertEqual(add_blob_status, 'OK')
            self.assertTrue(isinstance(blob_id, int))
            self.assertEqual(run_status, 'OK')
            self.assertEqual(delete_demo_status, 'OK')

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
            response = self.create_demo(self.demo_id, self.demo_title, self.demo_state)
            create_demo_status = response.get('status')

            # Add DDL to demo
            with open(self.test_ddl_file, 'r') as f:
                ddl = f.read()
            response = self.add_ddl(self.demo_id, ddl)
            add_ddl_status = response.get('status')

            # Add DemoExtras.gz
            with open(self.test_demo_extras_file, 'rb') as demo_extras:
                demo_extras_name = os.path.basename(demo_extras.name)
                response = self.add_demo_extras(self.demo_id, demo_extras, demo_extras_name)
            demo_extras_status = response.get('status')

            # Run the demo with the uploaded image
            with open(self.test_image_file, 'rb') as blob:
                with Image.open(self.test_image_file) as blob_image:
                    width, height = blob_image.size
                response = self.run_demo_with_uploaded_blob(self.demo_id, blob, width, height)
            run_status = response.get('status')

            response = self.get_archive_experiments_by_page(self.demo_id)
            archive_status = response.get('status')
            experiments = response.get('experiments')
            exp_meta = response.get('meta')
            try:
                n_experiments = exp_meta.get('number_of_experiments')
            except Exception:
                pass

            # Delete demo
            response = self.delete_demo(self.demo_id)
            delete_demo_status = response.get('status')

        finally:
            self.assertEqual(create_demo_status, 'OK')
            self.assertEqual(add_ddl_status, 'OK')
            self.assertEqual(demo_extras_status, 'OK')
            self.assertEqual(run_status, 'OK')
            self.assertEqual(archive_status, 'OK')
            self.assertTrue(isinstance(experiments, list))
            self.assertTrue(n_experiments > 0)
            self.assertEqual(delete_demo_status, 'OK')

    #####################
    #       TOOLS       #
    #####################

    def post(self, module, service, params=None, data=None, files=None, servicejson=None):
        url = '{}/api/{}/{}'.format(self.BASE_URL, module, service)
        return requests.post(url, params=params, data=data, files=files, json=servicejson)

    def check_status(self, response, error_msg):
        """
        If the response is not OK it will log the error
        """
        if 'status' not in response or response['status'] == 'KO':
            print("{}. Response from the module: {}".format(error_msg, response))

    def create_demo(self, demo_id, title, state):
        """
        Creates a demo
        """
        response = self.post('demoinfo', 'add_demo', params={'demo_id': demo_id, 'title': title, 'state': state})
        return response.json()

    def add_ddl(self, demo_id, ddl):
        """
        Add the ddl to the demo
        """
        params = {'demoid': demo_id}
        response = self.post('demoinfo', 'save_ddl', params=params, servicejson=json.loads(ddl))
        return response.json()

    def add_demo_extras(self, demo_id, demo_extras, demo_extras_name):
        """
        Add DemoExtras to the demo
        """
        files = {'demoextras': demo_extras}
        params = {'demo_id': demo_id, 'demoextras_name': demo_extras_name}
        response = self.post('demoinfo', 'add_demoextras', params=params, files=files)
        return response.json()

    def add_blob(self, demo_id, blob, demo_title, set_name, pos_in_set):
        """
        Add a blob to the demo
        """
        files = {'blob': blob}
        params = {'demo_id': demo_id, 'title': demo_title, 'blob_set': set_name, 'pos_set': pos_in_set}
        response = self.post('blobs', 'add_blob_to_demo', params=params, files=files)
        return response.json()

    def get_blob_id(self, demo_id, pos_in_set):
        """
        Return the blob id
        """
        params = {'demo_id': demo_id}
        response = self.post('blobs', 'get_blobs', params=params)
        json_response = response.json()
        if json_response.get('status') == 'OK':
            return json_response['sets'][0]['blobs'][str(pos_in_set)]['id']

    def run_demo_with_blobset(self, demo_id, blob, blob_id, blobset_id):
        """
        Runs the demo with the blob given
        """
        width, height = blob.size
        params = {'demo_id': demo_id,
                    'origin': 'blobSet',
                    'params': {},
                    'crop_info': {'x': 20, 'y': 9.199999999999996,'width': width, 'height': height, 'rotate': 0, 'scaleX': 1, 'scaleY': 1},
                    'blobs': {'id_blobs': [blob_id]},                
                    'setId': blobset_id                  
                }
        response = self.post('core', 'run', data={"clientData": json.dumps(params)})
        return response.json()

    def run_demo_with_uploaded_blob(self, demo_id, blob, width, height):
        params = {'demo_id': demo_id,
                    'origin': 'upload',
                    'params': {},
                  }
        files = {'file_0': blob}
        response = self.post('core', 'run', data={"clientData": json.dumps(params)}, files=files)
        return response.json()

    def delete_demo(self, demo_id):
        """
        Delete demo from demoinfo
        """
        params = {'demo_id': demo_id}
        response = self.post('core', 'delete_demo', params=params)
        return response.json()

    def get_archive_experiments_by_page(self, demo_id, page=None):
        if page is None:
            page = 0
        params = {'demo_id': demo_id, 'page': page}
        response = self.post('archive', 'get_page', params=params)
        return response.json()


if __name__ == '__main__':
    shared_folder = sys.argv.pop()
    demorunners = sys.argv.pop()
    resources_path = sys.argv.pop()
    IntegrationTests.test_ddl_file = os.path.join(resources_path, 'test_ddl.txt')
    IntegrationTests.test_demo_extras_file = os.path.join(resources_path, 'test_demo_extras.tar.gz')
    IntegrationTests.test_image_file = os.path.join(resources_path, 'test_image.png')
    unittest.main()
