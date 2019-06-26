#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dispatcher test
"""
import json
# Unit tests for the Blobs module
import socket
import sys
import unittest
import xml.etree.ElementTree as ET

import requests


def load_demorunners(demorunners_file):
    """
    Read demorunners xml
    """
    dict_demorunners = {}
    tree = ET.parse(demorunners_file)
    root = tree.getroot()

    for demorunner in root.findall('demorunner'):
        dict_tmp = {}
        capabilities = []

        for capability in demorunner.findall('capability'):
            capabilities.append(capability.text)

        dict_tmp["server"] = demorunner.find('server').text
        dict_tmp["serverSSH"] = demorunner.find('serverSSH').text
        dict_tmp["capabilities"] = ''.join(capabilities)

        dict_demorunners[demorunner.get('name')] = dict_tmp

    return dict_demorunners

class DispatcherTests(unittest.TestCase):
    """
    Dispatcher tests
    """
    HOST = socket.getfqdn()
    module = 'dispatcher'

    demorunners = []

    #####################
    #       Tests       #
    #####################
    def test_ping(self):
        """
        Test ping
        """
        status = None
        try:
            ping = 'http://{}/api/dispatcher/ping'.format(self.HOST)
            response = requests.get(ping).json()
            status = response.get('status')
        finally:
            self.assertEqual(status, 'OK')

    def test_find_suitable_demorunner(self):
        """
        Test get suitable demorunner
        """
        try:
            suitable_dr = 'http://{}/api/dispatcher/get_suitable_demorunner'.format(
                self.HOST)
            response = requests.get(suitable_dr).json()
            status = response.get('status')
        finally:
            self.assertEqual(status, 'OK')

    def test_find_demorunner_with_requirement(self):
        """
        Test get suitable demorunner with requirements according to
        local demorunners.xml
        """
        status = 'OK'
        try:
            suitable_dr = 'http://{}/api/dispatcher/get_suitable_demorunner'.format(
                self.HOST)
            for demorunner in self.demorunners:
                payload = {'requirements': self.demorunners[demorunner]['capabilities']}
                response = requests.get(suitable_dr, params=payload).json()
                if response.get('status') != 'OK':
                    status = response.get('status')
        finally:
            self.assertEqual(status, 'OK')

    def test_get_demorunner_stats(self):
        """
        Test get demorunner stats
        """
        status = 'KO'
        try:
            dr_stats = 'http://{}/api/dispatcher/get_demorunners_stats'.format(self.HOST)
            response = requests.get(dr_stats).json()
            for dr in response.get('demorunners'):
                if dr['status'] == 'OK' and 'workload' in dr:
                    status = 'OK'
        finally:
            self.assertEqual(status, 'OK')

    #####################
    #       TOOLS       #
    #####################

    def get_demorunner(self, demorunners_workload, requirements=None):
        """
        get demorunner
        """
        params = {'demorunners_workload': demorunners_workload}
        if requirements is not None:
            params['requirements'] = requirements
        response = self.post(self.module, 'get_suitable_demorunner')
        return response.json()

if __name__ == '__main__':
    shared_folder = sys.argv.pop()
    demorunners = sys.argv.pop()
    resources_path = sys.argv.pop()
    DispatcherTests.demorunners = load_demorunners(demorunners)
    unittest.main()
