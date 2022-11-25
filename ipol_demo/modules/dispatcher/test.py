#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dispatcher test
"""
# Unit tests for the Blobs module
import os
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

        dict_tmp["serverSSH"] = demorunner.find('serverSSH').text
        dict_tmp["capabilities"] = ','.join(capabilities)

        dict_demorunners[demorunner.get('name')] = dict_tmp

    return dict_demorunners

class DispatcherTests(unittest.TestCase):
    """
    Dispatcher tests
    """
    BASE_URL = os.environ.get('IPOL_URL', 'http://' + socket.getfqdn())
    module = 'dispatcher'

    demorunners = []

    #####################
    #       Tests       #
    #####################
    def test_find_suitable_demorunner(self):
        """
        Test get suitable demorunner
        """
        if True:
            # test broken since the endpoint get_suitable_demorunner was removed
            return
        try:
            suitable_dr = '{}/api/dispatcher/get_suitable_demorunner'.format(self.BASE_URL)
            response = requests.get(suitable_dr).json()
            status = response.get('status')
        finally:
            self.assertEqual(status, 'OK')

    def test_find_demorunner_with_requirement(self):
        """
        Test get suitable demorunner with requirements according to
        local demorunners.xml
        """
        if True:
            # test broken since the endpoint get_suitable_demorunner was removed
            return
        status = 'OK'
        try:
            suitable_dr = '{}/api/dispatcher/get_suitable_demorunner'.format(self.BASE_URL)
            for demorunner in self.demorunners:
                capabilities = self.demorunners[demorunner]['capabilities'].split(',')
                capabilities_as_requirements = [cap.rstrip('!') for cap in capabilities]
                payload = {'requirements': ','.join(capabilities_as_requirements)}
                response = requests.get(suitable_dr, params=payload).json()
                if response.get('status') != 'OK':
                    status = response.get('status')
        finally:
            self.assertEqual(status, 'OK')

    def test_get_demorunner_stats(self):
        """
        Test get demorunner stats
        """
        if True:
            # test broken since the endpoint get_demorunners_stats was removed
            return
        status = 'KO'
        try:
            dr_stats = '{}/api/dispatcher/get_demorunners_stats'.format(self.BASE_URL)
            response = requests.get(dr_stats).json()
            for dr in response.get('demorunners'):
                if dr['status'] == 'OK' and 'workload' in dr:
                    status = 'OK'
        finally:
            self.assertEqual(status, 'OK')

if __name__ == '__main__':
    shared_folder = sys.argv.pop()
    demorunners = sys.argv.pop()
    resources_path = sys.argv.pop()
    DispatcherTests.demorunners = load_demorunners(demorunners)
    unittest.main()
