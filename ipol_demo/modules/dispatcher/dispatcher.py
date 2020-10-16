#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
Dispatcher: choose the best demorunner according to a policy

All exposed WS return JSON with a status OK/KO, along with an error
description if that's the case.
"""

import configparser
import json
import logging
import os
import random
import re
import sys
import xml.etree.ElementTree as ET
import requests
import cherrypy


def authenticate(func):
    """
    Wrapper to authenticate before using an exposed function
    """

    def authenticate_and_call(*args, **kwargs):
        """
        Invokes the wrapped function if authenticated
        """
        if "X-Real-IP" in cherrypy.request.headers \
                and is_authorized_ip(cherrypy.request.headers["X-Real-IP"]):
            return func(*args, **kwargs)
        error = {"status": "KO", "error": "Authentication Failed"}
        return json.dumps(error).encode()

    def is_authorized_ip(ip):
        """
        Validates the given IP
        """
        dispatcher = Dispatcher.get_instance()
        patterns = []
        # Creates the patterns  with regular expressions
        for authorized_pattern in dispatcher.authorized_patterns:
            patterns.append(re.compile(authorized_pattern.replace(
                ".", "\\.").replace("*", "[0-9a-zA-Z]+")))
        # Compare the IP with the patterns
        for pattern in patterns:
            if pattern.match(ip) is not None:
                return True
        return False

    return authenticate_and_call


class Dispatcher():
    """
    The Dispatcher chooses the best DR according to a policy
    """

    instance = None

    @staticmethod
    def get_instance():
        """
        Singleton pattern
        """
        if Dispatcher.instance is None:
            Dispatcher.instance = Dispatcher()
        return Dispatcher.instance

    def __init__(self):
        """
        Initialize Dispatcher class
        """
        self.base_directory = os.getcwd()
        self.logs_dir = cherrypy.config.get("logs_dir")
        self.authorized_patterns_file = cherrypy.config.get("authorized_patterns_file")

        # Default policy: lowest_workload
        self.policy = Policy.factory('lowest_workload')

        self.demorunners = []
        self.demorunners_file = cherrypy.config.get("demorunners_file")
        self.refresh_demorunners()

        # Logs
        try:
            if not os.path.exists(self.logs_dir):
                os.makedirs(self.logs_dir)
            self.logger = self.init_logging()
        except Exception as e:
            self.logger.exception("Failed to create log dir (using file dir) : {}".format(e))

        # Security: authorized IPs
        self.authorized_patterns = self.read_authorized_patterns()

    def read_authorized_patterns(self):
        """
        Read from the IPs conf file
        """
        # Check if the config file exists
        authorized_patterns_path = os.path.join(self.authorized_patterns_file)
        if not os.path.isfile(authorized_patterns_path):
            self.error_log("read_authorized_patterns",
                           "Can't open {}".format(authorized_patterns_path))
            return []

        # Read config file
        try:
            cfg = configparser.ConfigParser()
            cfg.read([authorized_patterns_path])
            patterns = []
            for item in cfg.items('Patterns'):
                patterns.append(item[1])
            return patterns
        except configparser.Error:
            self.logger.exception("Bad format in {}".format(authorized_patterns_path))
            return []

    @cherrypy.expose
    def refresh_demorunners(self):
        """
        Update dispatcher's DRs information
        """
        data = {"status": "KO"}
        self.demorunners = []
        demorunners = ET.parse(self.demorunners_file).getroot()

        try:
            for demorunner in demorunners.findall('demorunner'):
                capabilities = []
                for capability in demorunner.findall('capability'):
                    capabilities.append(capability.text)

                self.demorunners.append(DemoRunnerInfo(
                    demorunner.find('server').text,
                    demorunner.get('name'),
                    demorunner.find('serverSSH').text,
                    capabilities
                ))
        except Exception as ex:
            print(ex)
            self.logger.exception("refresh_demorunners")

        data["status"] = "OK"
        return json.dumps(data).encode()

    @cherrypy.expose
    def get_demorunners_stats(self):
        """
        Get statistic information of all DRs.
        This is mainly used by external monitoring tools.
        """
        demorunners = []
        for dr in self.demorunners:
            try:
                response = requests.get(
                    'http://{}/api/demorunner/get_workload'.format(dr.server), timeout=3)
                if not response:
                    demorunners.append({'status': 'KO', 'name': dr.name})
                    continue

                json_response = response.json()
                if json_response.get('status') == 'OK':
                    workload = float('%.2f' % (json_response.get('workload')))
                    demorunners.append({'status': 'OK',
                                        'name': dr.name,
                                        'workload': workload})
                else:
                    demorunners.append({'name': dr.name, 'status': 'KO'})

            except requests.ConnectionError:
                self.logger.exception("Couldn't reach DR={}".format(dr.name))
                demorunners.append({'status': 'KO', 'name': dr.name})
                continue
            except Exception as ex:
                message = "Couldn't get the DRs workload. Error = {}".format(ex)
                print(message)
                self.logger.exception(message)
                return json.dumps({'status': 'KO', 'message': message}).encode()

        return json.dumps({'status': 'OK', 'demorunners': demorunners}).encode()

    # ---------------------------------------------------------------------------
    def init_logging(self):
        """
        Initialize the error logs of the module.
        """
        logger = logging.getLogger("dispatcher_log")

        logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(os.path.join(self.logs_dir, 'error.log'))
        formatter = logging.Formatter(
            '%(asctime)s; [%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        return logger

    def error_log(self, function_name, error):
        """
        Write an error log in the logs_dir defined in archive.conf
        """
        error_string = function_name + ": " + error
        self.logger.error(error_string)

    # ---------------------------------------------------------------------------
    @staticmethod
    @cherrypy.expose
    def index():
        """
        index of the module.
        """
        return "Dispatcher module"

    @staticmethod
    @cherrypy.expose
    def default(attr):
        """
        Default method invoked when asked for non-existing service.
        """
        data = {"status": "KO", "message": "Unknown service '{}'".format(attr)}
        return json.dumps(data).encode()

    @staticmethod
    @cherrypy.expose
    def ping():
        """
        Ping service: answer with a PONG.
        """
        data = {"status": "OK", "ping": "pong"}
        return json.dumps(data).encode()

    @cherrypy.expose
    @authenticate
    def shutdown(self):
        """
        Shutdown the module.
        """
        data = {"status": "KO"}
        try:
            cherrypy.engine.exit()
            data["status"] = "OK"
        except Exception as ex:
            self.logger.error("Failed to shutdown : {}".format(ex))
            sys.exit(1)
        return json.dumps(data).encode()

    @cherrypy.expose
    @authenticate
    def set_policy(self, policy):
        """
        Change the current execution policy. If the given name is not a known policy, it will remain unchanged.
        """
        data = {"status": "OK"}

        orig_policy = self.policy

        self.policy = Policy.factory(policy)

        if self.policy is None:
            data["status"] = "KO"
            data["message"] = "Policy {} is not a known policy".format(policy)
            self.error_log("set_policy", "Policy {} is not a known policy".format(policy))
            self.policy = orig_policy

        return json.dumps(data).encode()

    @cherrypy.expose
    def get_suitable_demorunner(self, requirements=None):
        """
        Return an active DR which meets the requirements
        """
        data = {"status": "KO"}
        if self.demorunners is None:
            self.refresh_demorunners()

        # Get a demorunner for the requirements
        dr_workloads = self.demorunners_workload()
        chosen_dr = self.policy.execute(self.demorunners, dr_workloads, requirements)
        if not chosen_dr:
            if requirements is None:
                self.error_log("get_suitable_demorunner",
                            f'No DR available with requirement {requirements}')
            else:
                self.error_log("get_suitable_demorunner",
                            f'No DR available')
            return json.dumps(data).encode()

        dr_name = chosen_dr.name
        dr_server = chosen_dr.server

        # Check if the DR is up.
        dr_response = requests.get('http://{}/api/demorunner/ping'.format(dr_server), timeout=3)
        if not dr_response:
            self.error_log("get_suitable_demorunner",
                           "Module {} unresponsive".format(dr_name))
            print("Module {} unresponsive".format(dr_name))
            data['unresponsive_dr'] = dr_name
            return json.dumps(data).encode()

        data['dr_name'] = dr_name
        data['dr_server'] = dr_server
        data['status'] = "OK"
        return json.dumps(data).encode()

    def demorunners_workload(self):
        """
        Get the workload of each DR
        """
        dr_workload = {}
        for dr_info in self.demorunners:
            try:
                dr_server = dr_info.server
                url = 'http://{}/api/demorunner/get_workload'.format(dr_server)
                resp = requests.get(url, timeout=3)
                if not resp:
                    error_message = "No response from DR='{}'".format(dr_info.name)
                    self.error_log("demorunners_workload", error_message)
                    continue

                response = resp.json()
                if response.get('status', '') == 'OK':
                    dr_workload[dr_info.name] = response.get('workload')
                else:
                    error_message = "get_workload KO response for DR='{}'".format(
                        dr_info.name)
                    self.error_log("demorunners_workload", error_message)
            except requests.ConnectionError:
                error_message = "get_workload ConnectionError for DR='{}'".format(
                    dr_info.name)
                self.error_log("demorunners_workload", error_message)
                continue
            except Exception:
                error_message = "Error when obtaining the workload of '{}'".format(
                    dr_info)
                self.logger.exception(error_message)
                continue

        return dr_workload


class Policy():
    """
    This class represents the policy used to pick a demoRunner at each
    execution.
    """

    @staticmethod
    def factory(policy):
        """
        Factory Method
        """
        if policy == "random":
            return RandomPolicy()
        if policy == "sequential":
            return SequentialPolicy()
        if policy == "lowest_workload":
            return LowestWorkloadPolicy()

        return None

    @staticmethod
    def get_suitable_demorunners(requirements, demorunners):
        """
        Return all the suitable demorunners
        """
        if requirements is None:
            return demorunners

        suitable_demorunners = []
        requirements = requirements.lower().split(',')

        for dr in demorunners:
            dr_capabilities = [cap.lower().strip() for cap in dr.capabilities]

            if all([req.strip() in dr_capabilities for req in requirements]):
                suitable_demorunners.append(dr)

        return suitable_demorunners

    # Abstract methods

    def execute(self, demorunners, demorunners_workload, requirements=None):
        """
        Abstract method to choose a DemoRunner that matches the requirements
        """

class RandomPolicy(Policy):
    """
    RandomPolicy
    """
    def execute(self, demorunners, demorunners_workload, requirements=None):
        """
        Chooses a random DemoRunner that matches the requirements
        """
        try:

            suitable_dr = Policy().get_suitable_demorunners(requirements, demorunners)
            if suitable_dr:
                return suitable_dr[random.randrange(0, len(suitable_dr), 1)]
            print("RandomPolicy could not find any DR available")
            return None

        except Exception as ex:
            print("Error in execute policy Random", ex)
            raise


class SequentialPolicy(Policy):
    """
    SequentialPolicy
    """
    def __init__(self):
        self.iterator = 0

    def execute(self, demorunners, demorunners_workload, requirements=None):
        """
        Chooses a random DemoRunner that matches the requirements
        """

        try:
            suitable_dr = Policy().get_suitable_demorunners(requirements, demorunners)
            if suitable_dr:
                dr_winner = suitable_dr[self.iterator % len(suitable_dr)]
                self.iterator = (self.iterator + 1) % len(demorunners)
                return dr_winner
            print("SequentialPolicy could not find any DR available")
            return None

        except Exception as ex:
            print("Error in execute policy Sequential", ex)
            raise


class LowestWorkloadPolicy(Policy):
    """
    LowestWorkloadPolicy
    """
    def execute(self, demorunners, demorunners_workload, requirements=None):
        """
        Chooses the DemoRunner with the lowest workload which
        satisfies the requirements.
        """
        try:
            suitable_drs = Policy().get_suitable_demorunners(requirements, demorunners)
            if not suitable_drs:
                print("LowestWorkloadPolicy could not find any DR available")
                return None

            min_workload = float("inf")
            lowest_workload_dr = None

            for dr in suitable_drs:
                if dr.name in demorunners_workload and float(demorunners_workload[dr.name]) < min_workload:
                    min_workload = demorunners_workload[dr.name]
                    lowest_workload_dr = dr

            return lowest_workload_dr

        except Exception as ex:
            print("Error in execute policy Lowest Workload", ex)
            raise


class DemoRunnerInfo():
    """
    Demorunner information object
    """

    def __init__(self, server, name, serverSSH, capabilities=None):
        self.capabilities = [] if capabilities is None else capabilities
        self.server = server
        self.name = name
        self.serverSSH = serverSSH
