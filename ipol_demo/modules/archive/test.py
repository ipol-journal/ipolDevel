#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ArchiveTests
"""
import json

# Unit tests for the Blobs module
import os
import socket
import sys
import unittest

import requests


class ArchiveTests(unittest.TestCase):
    """
    ArchiveTests
    """

    BASE_URL = os.environ.get("IPOL_URL", "http://" + socket.getfqdn())
    module = "archive"

    # Blob info
    blob_path = ""
    # Demo
    demo_id = -1

    #####################
    #       Tests       #
    #####################

    def setUp(self):
        """
        Clean the DB from the tests
        """
        # Delete demo test
        self.delete_demo(self.demo_id)

    def test_ping(self):
        """
        Test ping
        """
        try:
            response = self.post(self.module, 'get', 'ping')
        finally:
            self.assertEqual(response.status_code, 200)

    def test_add_and_delete_experiment(self):
        """
        Test add and delete experiment
        """
        add_status = None
        id_experiment = None
        del_status = None
        try:
            abs_path = os.path.abspath(self.blob_path)
            parameters = {"test_param": 0}
            response = self.add_experiment(self.demo_id, [abs_path], parameters, {})
            add_status = response.status_code
            id_experiment = response.json().get('experiment_id')

            response = self.delete_experiment(id_experiment)
            del_status = response.status_code
        finally:
            self.assertEqual(add_status, 201)
            self.assertTrue(isinstance(id_experiment, int))
            self.assertEqual(del_status, 204)

    def test_delete_non_existent_experiment(self):
        """
        Test delete non existent experiment
        """
        try:
            response = self.delete_experiment(0)
        finally:
            self.assertEqual(response.status_code, 204)

    def test_get_experiment(self):
        """
        Test get experiment
        """
        abs_path = None
        parameters = None
        experiment = None
        response_params = None
        url = None
        name = None
        try:
            abs_path = os.path.abspath(self.blob_path)
            parameters = {"test_param": 0}
            response = self.add_experiment(self.demo_id, [abs_path], parameters, {})
            experiment_id = response.json().get('experiment_id')

            response = self.get_experiment(experiment_id)
            experiment = response.json()
            try:
                response_params = experiment.get("parameters")
                files = experiment.get("files")
                url = files[0].get("url")
                name = files[0].get("name")
            except Exception:
                pass

            self.delete_experiment(experiment_id)
        finally:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response_params, parameters)
            self.assertEqual(name, os.path.basename(abs_path))
            self.assertTrue(url is not None)

    def test_get_page(self):
        """
        Test get page
        """
        status = None
        experiments = None
        n_experiments = None
        try:
            abs_path = os.path.abspath(self.blob_path)
            parameters = {'test_param': 0}
            response = self.add_experiment(self.demo_id, [abs_path], parameters, {}).json()
            id_experiment = response.get('experiment_id')

            response = self.get_page(self.demo_id)
            status = response.status_code
            experiments = response.json().get('experiments')
            exp_meta = response.json().get('meta')
            try:
                n_experiments = exp_meta.get("number_of_experiments")
            except Exception:
                pass

            self.delete_experiment(id_experiment)
        finally:
            self.assertEqual(status, 200)
            self.assertTrue(isinstance(experiments, list))
            self.assertTrue(len(experiments) == 1)
            self.assertTrue(n_experiments == 1)

    def test_delete_demo(self):
        """
        Test delete demo
        """
        status = None
        experiments = None
        n_experiments = None
        try:
            abs_path = os.path.abspath(self.blob_path)
            parameters = {"test_param": 0}
            self.add_experiment(self.demo_id, [abs_path], parameters, {})

            response = self.delete_demo(self.demo_id)
            status = response.status_code

            response = self.get_page(self.demo_id)
            experiments = response.json().get('experiments')
            exp_meta = response.json().get('meta_info')
            try:
                n_experiments = exp_meta.get("number_of_experiments")
            except Exception:
                pass

        finally:
            self.assertEqual(status, 204)
            self.assertTrue(len(experiments) == 0)
            self.assertTrue(n_experiments == 0)

    def test_delete_non_existent_demo(self):
        """
        Test delete non existent demo
        """
        status = None
        try:
            response = self.delete_demo(self.demo_id)
            status = response.status_code

        finally:
            self.assertEqual(status, 204)

    def test_demo_list(self):
        """
        Test demo list
        """
        status = None
        try:
            abs_path = os.path.abspath(self.blob_path)
            parameters = {"test_param": 0}
            response = self.add_experiment(self.demo_id, [abs_path], parameters, {})
            id_experiment = response.json().get('id_experiment')

            response = self.demo_list()
            status = response.status_code
            demo_list = response.json().get('demo_list')

            self.delete_experiment(id_experiment)
        finally:
            self.assertEqual(status, 200)
        self.assertTrue(isinstance(demo_list, list))
        self.assertTrue(len(demo_list) > 0)

    def test_update_demo_id(self):
        """
        Test update demo id
        """
        new_demo_id = -2
        status = None
        id_experiment = None
        id_experiment_from_new_demo = None
        parameters = None
        parameter_from_new_demo = None
        try:
            abs_path = os.path.abspath(self.blob_path)
            parameters = {"test_param": 0}
            response = self.add_experiment(self.demo_id, [abs_path], parameters, {})
            id_experiment = response.json().get('experiment_id')

            response = self.update_demo_id(self.demo_id, new_demo_id)
            status = response.status_code

            response = self.get_page(new_demo_id)
            experiments = response.json().get('experiments')
            try:
                id_experiment_from_new_demo = experiments[0].get("id")
                parameter_from_new_demo = experiments[0].get("parameters")
            except Exception:
                pass

            self.delete_demo(new_demo_id)
        finally:
            self.assertEqual(status, 204)
            self.assertEqual(id_experiment_from_new_demo, id_experiment)
            self.assertEqual(parameter_from_new_demo, parameters)

    def test_stats(self):
        """
        Test stats
        """
        status = None
        nb_blobs = None
        nb_experiments = None
        try:
            response = self.stats()
            status = response.status_code
            nb_blobs = response.json().get('nb_blobs')
            nb_experiments = response.json().get('nb_experiments')

        finally:
            self.assertEqual(status, 200)
            self.assertTrue(isinstance(nb_blobs, int))
            self.assertTrue(isinstance(nb_experiments, int))

    def test_delete_blob_w_deps(self):
        """
        Test delete blob w deps
        """
        other_demo_id = -2
        status = None
        first_experiments = None
        second_experiments = None
        try:
            abs_path = os.path.abspath(self.blob_path)
            parameters = {"test_param": 0}
            # Add blob experiment to one demo
            self.add_experiment(self.demo_id, [abs_path], parameters, {})
            # Add same blob experiment to other demo
            self.add_experiment(other_demo_id, [abs_path], parameters, {})

            response = self.get_page(self.demo_id)
            blob_id = response.json().get('experiments')[0].get('files')[0].get('id')

            response = self.delete_blob_w_deps(blob_id)
            status = response.status_code

            response = self.get_page(self.demo_id)
            first_experiments = response.json().get('experiments')

            response = self.get_page(other_demo_id)
            second_experiments = response.json().get('experiments')

            self.delete_demo(self.demo_id)
            self.delete_demo(other_demo_id)
        finally:
            self.assertEqual(status, 204)
            self.assertTrue(len(first_experiments) == 0)
            self.assertTrue(len(second_experiments) == 0)

    #####################
    #       TOOLS       #
    #####################

    def post(self, module, method, service, params=None, data=None):
        """
        post
        """
        url = f'{self.BASE_URL}/api/{module}/{service}'
        headers = {'Content-Type':'application/json; charset=UTF-8'}
        if method == 'get':
            return requests.get(url)
        elif method == 'put':
            return requests.put(url, data=json.dumps(data), headers=headers)
        elif method == 'post':
            return requests.post(url, data=json.dumps(params), headers=headers)
        elif method == 'delete':
            return requests.delete(url, headers=headers)

    def add_experiment(self, demo_id, blobs_path, parameters, execution):
        """
        add experiment
        """
        blobs = []
        for path in blobs_path:
            blobs.append({os.path.basename(path): path})
        params = {'demo_id': demo_id, 'blobs': json.dumps(blobs), 'parameters': json.dumps(parameters), 'execution': json.dumps(execution)}
        response = self.post(self.module, 'post', 'experiment', params=params)
        return response

    def get_experiment(self, experiment_id):
        """
        get experiment
        """
        response = self.post(self.module, 'get', f'experiment/{experiment_id}')
        return response

    def delete_experiment(self, experiment_id):
        """
        delete experiment
        """
        response = self.post(self.module, 'delete', f'experiment/{experiment_id}')
        return response

    def get_page(self, demo_id, page=None):
        """
        get page
        """
        if page is not None:
            service = f'page/{page}'
        else:
            service = 'page/1'
        response = self.post(self.module, 'get', service + f'?demo_id={demo_id}')
        return response

    def delete_blob_w_deps(self, id_blob):
        """
        delete blob w deps
        """
        response = self.post(self.module, 'delete', f'blob/{id_blob}')
        return response

    def delete_demo(self, demo_id):
        """
        delete demo
        """
        response = self.post(self.module, 'delete', f'demo/{demo_id}')
        return response

    def demo_list(self):
        """
        demo list
        """
        response = self.post(self.module, 'get', 'demo_list')
        return response

    def update_demo_id(self, old_demo_id, new_demo_id):
        """
        update demo id
        """
        response = self.post(self.module, 'put', f'demo/{old_demo_id}?new_demo_id={new_demo_id}')
        return response

    def stats(self):
        """
        stats
        """
        response = self.post(self.module, 'get', 'stats')
        return response

if __name__ == "__main__":
    shared_folder = sys.argv.pop()
    demorunners = sys.argv.pop()
    resources_path = sys.argv.pop()
    ArchiveTests.blob_path = os.path.join(resources_path, "test_image.png")
    unittest.main()
