#!/usr/bin/python
# -*- coding: utf-8 -*-

# Unit tests for the Blobs module
import socket
import unittest
import requests
import json
import sys
import os
import xml.etree.ElementTree as ET


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

        dict_demorunners[demorunner.get('name')] = dict_tmp

    return dict_demorunners

class DispatcherTests(unittest.TestCase):
    """
    Dispatcher tests
    """
    HOST = socket.gethostbyname(socket.gethostname())
    module = 'dispatcher'

    demorunners = None

    #####################
    #       Tests       #
    #####################
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

    def test_refresh_demorunners(self):
        """
        Test refresh demorunners
        """
        status = None
        try:
            json_response = self.refresh_demorunners()
            status = json_response.get('status')
        finally:
            self.assertEqual(status, 'OK')

    def test_get_demorunner(self):
        """
        Test get demorunner
        """
        status = None
        demorunner_name = None
        lowest_demorunner = None
        try:
            demorunner_workload = {}
            i = 0
            for demorunner in self.demorunners:
                if i == 0:
                    lowest_demorunner = demorunner
                demorunner_workload[demorunner] = i
                i += 1

            json_response = self.get_demorunner(json.dumps(demorunner_workload))
            status = json_response.get('status')
            demorunner_name = json_response.get('name')
        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(demorunner_name, lowest_demorunner)

    #####################
    #       TOOLS       #
    #####################

    def post(self, module, service, params=None, data=None, files=None, servicejson=None):
        """
        Do a post
        """
        url = 'http://{}/api/{}/{}'.format(self.HOST, module, service)
        return requests.post(url, params=params, data=data, files=files, json=servicejson)

    def refresh_demorunners(self):
        """
        refresh demorunners
        """
        response = self.post(self.module, 'refresh_demorunners')
        return response.json()

    def get_demorunner(self, demorunners_workload, requirements=None):
        """
        get demorunner
        """
        params = {'demorunners_workload': demorunners_workload}
        if requirements is not None:
            params['requirements'] = requirements

        response = self.post(self.module, 'get_demorunner', params=params)
        return response.json()

if __name__ == '__main__':
    shared_folder = sys.argv.pop()
    demorunners = sys.argv.pop()
    resources_path = sys.argv.pop()
    DispatcherTests.demorunners = load_demorunners(demorunners)
    unittest.main()
