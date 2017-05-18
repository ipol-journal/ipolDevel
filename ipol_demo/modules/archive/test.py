#!/usr/bin/python
# -*- coding: utf-8 -*-

# Unit tests for the Blobs module
import os
import socket
import unittest
import requests
import sys
import json


class ArchiveTests(unittest.TestCase):
    HOST = socket.gethostbyname(socket.gethostname())
    module = 'archive'

    # Blob info
    blob_path = ''
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
        status = None
        try:
            response = self.post(self.module, 'ping')
            json_response = response.json()
            status = json_response.get('status')
        finally:
            self.assertEqual(status, 'OK')

    def test_add_and_delete_experiment(self):
        """
        Test add and delete experiment
        """
        add_status = None
        id_experiment = None
        del_status = None
        try:
            abs_path = os.path.abspath(self.blob_path)
            parameters = {'test_param': 0}
            response = self.add_experiment(self.demo_id, [abs_path], parameters)
            add_status = response.get('status')
            id_experiment = response.get('id_experiment')

            response = self.delete_experiment(id_experiment)
            del_status = response.get('status')
        finally:
            self.assertEqual(add_status, 'OK')
            self.assertTrue(isinstance(id_experiment, int))
            self.assertEqual(del_status, 'OK')

    def test_delete_non_existent_experiment(self):
        """
        Test delete non existent experiment
        """
        status = None
        try:
            response = self.delete_experiment(0)
            status = response.get('status')
        finally:
            self.assertEqual(status, 'KO')

    def test_get_experiment(self):
        """
        Test get experiment
        """
        status = None
        abs_path = None
        parameters = None
        experiment = None
        response_params = None
        url = None
        name = None
        try:
            abs_path = os.path.abspath(self.blob_path)
            parameters = {'test_param': 0}
            response = self.add_experiment(self.demo_id, [abs_path], parameters)
            id_experiment = response.get('id_experiment')

            response = self.get_experiment(id_experiment)
            status = response.get('status')
            experiment = response.get('experiment')
            try:
                response_params = experiment.get('parameters')
                files = experiment.get('files')
                url = files[0].get('url')
                name = files[0].get('name')
            except Exception:
                pass

            self.delete_experiment(id_experiment)
        finally:
            self.assertEqual(status, 'OK')
            self.assertTrue(isinstance(experiment, dict))
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
            response = self.add_experiment(self.demo_id, [abs_path], parameters)
            id_experiment = response.get('id_experiment')

            response = self.get_page(self.demo_id)
            status = response.get('status')
            experiments = response.get('experiments')
            exp_meta = response.get('meta')
            try:
                n_experiments = exp_meta.get('number_of_experiments')
            except Exception:
                pass

            self.delete_experiment(id_experiment)
        finally:
            self.assertEqual(status, 'OK')
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
            parameters = {'test_param': 0}
            self.add_experiment(self.demo_id, [abs_path], parameters)

            response = self.delete_demo(self.demo_id)
            status = response.get('status')

            response = self.get_page(self.demo_id)
            experiments = response.get('experiments')
            exp_meta = response.get('meta')
            try:
                n_experiments = exp_meta.get('number_of_experiments')
            except Exception:
                pass

        finally:
            self.assertEqual(status, 'OK')
            self.assertTrue(len(experiments) == 0)
            self.assertTrue(n_experiments == 0)

    def test_delete_non_existent_demo(self):
        """
        Test delete non existent demo
        """
        status = None
        try:
            response = self.delete_demo(self.demo_id)
            status = response.get('status')

        finally:
            self.assertEqual(status, 'KO')

    def test_demo_list(self):
        """
        Test demo list
        """
        status = None
        try:
            abs_path = os.path.abspath(self.blob_path)
            parameters = {'test_param': 0}
            response = self.add_experiment(self.demo_id, [abs_path], parameters)
            id_experiment = response.get('id_experiment')

            response = self.demo_list()
            status = response.get('status')
            demo_list = response.get('demo_list')

            self.delete_experiment(id_experiment)
        finally:
            self.assertEqual(status, 'OK')
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
            parameters = {'test_param': 0}
            response = self.add_experiment(self.demo_id, [abs_path], parameters)
            id_experiment = response.get('id_experiment')

            response = self.update_demo_id(self.demo_id, new_demo_id)
            status = response.get('status')

            response = self.get_page(new_demo_id)
            experiments = response.get('experiments')
            try:
                id_experiment_from_new_demo = experiments[0].get('id')
                parameter_from_new_demo = experiments[0].get('parameters')
            except Exception:
                pass

            self.delete_demo(new_demo_id)
        finally:
            self.assertEqual(status, 'OK')
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
            status = response.get('status')
            nb_blobs = response.get('nb_blobs')
            nb_experiments = response.get('nb_experiments')

        finally:
            self.assertEqual(status, 'OK')
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
            parameters = {'test_param': 0}
            # Add blob experiment to one demo
            self.add_experiment(self.demo_id, [abs_path], parameters)
            # Add same blob experiment to other demo
            self.add_experiment(other_demo_id, [abs_path], parameters)

            response = self.get_page(self.demo_id)
            blob_id = response.get('experiments')[0].get('files')[0].get('id')

            response = self.delete_blob_w_deps(blob_id)
            status = response.get('status')

            response = self.get_page(self.demo_id)
            first_experiments = response.get('experiments')

            response = self.get_page(other_demo_id)
            second_experiments = response.get('experiments')

            self.delete_demo(self.demo_id)
            self.delete_demo(other_demo_id)
        finally:
            self.assertEqual(status, 'OK')
            self.assertTrue(len(first_experiments) == 0)
            self.assertTrue(len(second_experiments) == 0)

    #####################
    #       TOOLS       #
    #####################

    def post(self, module, service, params=None, data=None, files=None, servicejson=None):
        """
        post
        """
        url = 'http://{}/api/{}/{}'.format(self.HOST, module, service)
        return requests.post(url, params=params, data=data, files=files, json=servicejson)

    def add_experiment(self, demo_id, blobs_path, parameters):
        """
        add experiment
        """
        blobs = []
        for path in blobs_path:
            blobs.append({os.path.basename(path): path})
        params = {'demo_id': demo_id, 'blobs': json.dumps(blobs), 'parameters': json.dumps(parameters)}
        response = self.post(self.module, 'add_experiment', params=params)
        return response.json()

    def get_experiment(self, experiment_id):
        """
        get experiment
        """
        params = {'experiment_id': experiment_id}
        response = self.post(self.module, 'get_experiment', params=params)
        return response.json()

    def delete_experiment(self, experiment_id):
        """
        delete experiment
        """
        params = {'experiment_id': experiment_id}
        response = self.post(self.module, 'delete_experiment', params=params)
        return response.json()

    def get_page(self, demo_id, page=None):
        """
        get page
        """
        params = {'demo_id': demo_id}
        if page is not None:
            params['page'] = page

        response = self.post(self.module, 'get_page', params=params)
        return response.json()

    def delete_blob_w_deps(self, id_blob):
        """
        delete blob w deps
        """
        params = {'id_blob': id_blob}
        response = self.post(self.module, 'delete_blob_w_deps', params=params)
        return response.json()

    def delete_demo(self, demo_id):
        """
        delete demo
        """
        params = {'demo_id': demo_id}
        response = self.post(self.module, 'delete_demo', params=params)
        return response.json()

    def demo_list(self):
        """
        demo list
        """
        response = self.post(self.module, 'demo_list')
        return response.json()

    def update_demo_id(self, old_demo_id, new_demo_id):
        """
        update demo id
        """
        params = {'old_demo_id': old_demo_id, 'new_demo_id': new_demo_id}
        response = self.post(self.module, 'update_demo_id', params=params)
        return response.json()

    def stats(self):
        """
        stats
        """
        response = self.post(self.module, 'stats')
        return response.json()


if __name__ == '__main__':
    shared_folder = sys.argv.pop()
    demorunners = sys.argv.pop()
    resources_path = sys.argv.pop()
    ArchiveTests.blob_path = os.path.join(resources_path, 'test_image.png')
    unittest.main()
