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
import socket
import sys

import cherrypy

import requests


def authenticate(func):
    """
    Wrapper to authenticate before using an exposed function
    """

    def authenticate_and_call(*args, **kwargs):
        """
        Invokes the wrapped function if authenticated
        """
        if not is_authorized_ip(cherrypy.request.remote.ip) and not (
                "X-Real-IP" in cherrypy.request.headers and is_authorized_ip(cherrypy.request.headers["X-Real-IP"])):
            error = {"status": "KO", "error": "Authentication Failed"}
            return json.dumps(error).encode()
        return func(*args, **kwargs)

    def is_authorized_ip(ip):
        """
        Validates the given IP
        """
        dispatcher = Dispatcher.get_instance()
        patterns = []
        # Creates the patterns  with regular expressions
        for authorized_pattern in dispatcher.authorized_patterns:
            patterns.append(re.compile(authorized_pattern.replace(".", r"\.").replace("*", "[0-9]*")))
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
        self.demorunners = None
        self.config_common_dir = cherrypy.config.get("config_common_dir")

        # Default policy: lowest_workload
        self.policy = Policy.factory('lowest_workload')

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
        authorized_patterns_path = os.path.join(self.config_common_dir, "authorized_patterns.conf")
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

    def refresh_demorunners(self):
        """
        Refresh the value of the demorunners
        """
        url = 'http://{}/api/core/get_demorunners'.format(socket.getfqdn())
        resp = requests.post(url)

        self.demorunners = []
        dict_demorunners = json.loads(resp.json()['demorunners'].replace('\'', '\"'))

        for demorunner_name in list(dict_demorunners.keys()):
            self.demorunners.append(DemoRunnerInfo(
                dict_demorunners[demorunner_name]["server"],
                demorunner_name,
                dict_demorunners[demorunner_name]["capability"]
            ))

    @cherrypy.expose
    def set_demorunners(self, demorunners):
        """
        Set the list of demoRunners in the system.
        """
        data = {"status": "KO"}
        try:
            json_demorunners = json.loads(demorunners)
            self.demorunners = []
            for demorunner in json_demorunners:
                self.demorunners.append(DemoRunnerInfo(
                    json_demorunners[demorunner]["server"],
                    demorunner,
                    json_demorunners[demorunner]["capability"]
                ))
            data["status"] = "OK"
        except Exception as ex:
            data["message"] = "Can not refresh the demorunners"
            self.logger.exception("Can not refresh the demorunners")
            print("Can not refresh the demorunners", ex)
        return json.dumps(data).encode()

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
    def get_demorunner(self, demorunners_workload, requirements=None):
        """
        Choose a demoRunner meeting the specified requirements according to the current execution policy
        """

        data = {"status": "KO"}
        try:
            if self.demorunners is None:
                self.refresh_demorunners()

            dr_winner = self.policy.execute(self.demorunners, demorunners_workload, requirements)

            if dr_winner is None:
                return json.dumps(data).encode()

            data["name"] = dr_winner.name
            data["status"] = "OK"

        except Exception as ex:
            self.logger.exception("No demorunner for the requirements and {} policy".format(self.policy))
            print("No demorunner for the requirements and {} policy - {}".format(self.policy, ex))

        return json.dumps(data).encode()


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

            # Adds the workload of each demorunner to a dict
            dict_dr_wl = json.loads(demorunners_workload.replace('\'', '\"'))

            min_workload = float("inf")
            lowest_workload_dr = None
            #
            for dr in suitable_drs:
                if dr.name in dict_dr_wl and float(dict_dr_wl[dr.name]) < min_workload:
                    min_workload = dict_dr_wl[dr.name]
                    lowest_workload_dr = dr

            return lowest_workload_dr

        except Exception as ex:
            print("Error in execute policy Lowest Workload", ex)
            raise


class DemoRunnerInfo():
    """
    Demorunner information object
    """

    def __init__(self, server, name, capabilities=None):
        self.capabilities = [] if capabilities is None else capabilities
        self.server = server
        self.name = name
