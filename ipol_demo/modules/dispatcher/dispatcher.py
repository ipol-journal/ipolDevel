#!/usr/bin/python
# -*- coding:utf-8 -*-
"""
Dispatcher: choose the best demorunner acording to a policy

All exposed WS return JSON with a status OK/KO, along with an error
description if that's the case.
"""

import logging
import cherrypy
import os
import json
import random
import sys
import requests


class Dispatcher(object):
    def __init__(self, option, conf_file):
        """
        Initialize Dispatcher class
        """
        self.base_directory = os.getcwd()
        self.logs_dir = cherrypy.config.get("logs_dir")
        self.host_name = cherrypy.config.get("server.socket_host")
        self.demorunners = None

        # Default policy: sequential
        self.policy=Policy.factory('sequential')

        try:
            if not os.path.exists(self.logs_dir):
                os.makedirs(self.logs_dir)

            self.logger = self.init_logging()
        except Exception as e:
            self.logger.exception("Failed to create log dir (using file dir) : %s".format(e))

    @cherrypy.expose
    def refresh_demorunners(self):
        '''
        Refresh the value of the demorunners
        '''
        data = {}
        data["status"] = "OK"
        try:

            url='http://{}/api/{}/{}'.format(
                self.host_name,
                'core',
                'get_demorunners'
            )
            resp = requests.post(url)

            self.demorunners = []
            dict_demorunners = json.loads(resp.json()['demorunners'].replace('\'', '\"'))

            for demorunner_name in list(dict_demorunners.keys()):
                self.demorunners.append(DemoRunnerInfo(
                    dict_demorunners[demorunner_name]["server"],
                    demorunner_name,
                    dict_demorunners[demorunner_name]["capability"]
                ))

        except Exception as ex:
            data["status"] = "KO"
            data["message"] = "Can not refresh the demorunners"
            self.logger.exception("Can not refresh the demorunners")
            print "Can not refresh the demorunners",ex

        return json.dumps(data)


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
        data = {}
        cherrypy.response.headers['Content-Type'] = "application/json"
        data["status"] = "KO"
        data["message"] = "Unknown service '{}'".format(attr)
        return json.dumps(data)

    @staticmethod
    @cherrypy.expose
    def ping():
        """
        Ping pong.
        """
        data = {}
        cherrypy.response.headers['Content-Type'] = "application/json"

        data["status"] = "OK"
        data["ping"] = "pong"
        return json.dumps(data)

    @cherrypy.expose
    def shutdown(self):
        """
        Shutdown the module.
        """
        data = {}
        cherrypy.response.headers['Content-Type'] = "application/json"

        data["status"] = "KO"
        try:
            cherrypy.engine.exit()
            data["status"] = "OK"
        except Exception as ex:
            self.logger.error("Failed to shutdown : " + ex)
            sys.exit(1)
        return json.dumps(data)

    @cherrypy.expose
    def set_policy(self, policy):
        '''
        Change the policy used. If the given name is not a known policy the original policy is not changed
        '''
        data = {}
        data["status"] = "OK"

        orig_policy = self.policy

        self.policy=Policy.factory(policy)

        if self.policy is None:
            data["status"] = "KO"
            data["message"] = "Policy {} is not a known policy".format(policy)
            self.error_log("set_policy","Policy {} is not a known policy".format(policy))
            self.policy = orig_policy

        return json.dumps(data)


    @cherrypy.expose
    def get_demorunner(self, demorunners_workload, requirements=None):
        '''
        Select a demorunner acording to policy and requirements
        :param policy_name: policy name
        :param requirements: list of requirements
        :return: json
        '''

        data = {}
        data["status"] = "KO"
        try:
            if self.demorunners is None:
                self.refresh_demorunners()

            dr_winner = self.policy.execute(self.demorunners, demorunners_workload, requirements)
            data["name"] = dr_winner.name
            data["status"] = "OK"

        except Exception as ex:
            data["message"] = "No demorunner for the requirements"
            self.logger.exception("No demorunner for the requirements and {} policy".format(self.policy))
            print "No demorunner for the requirements and {} policy - {}".format(self.policy, ex)

        return json.dumps(data)


        # ---------------------------------------------------------------------------


class Policy(object):
    '''
    This class represents the policy used to pick a demoRunner at each
    execution.
    '''

    @staticmethod
    def factory(type):
        '''
        Factory Method
        '''
        if type == "random":
            return RandomPolicy()
        elif type == "sequential":
            return SequentialPolicy()
        elif type == "lowest_workload":
            return LowestWorkloadPolicy()
        else:
            return None

    @staticmethod
    def get_suitable_demorunners(requirements, demorunners):
        '''
        Return all the suitable demorunners
        '''
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
        '''
        Abstract method to choose a DemoRunner that matches the requirements
        '''
        pass


class RandomPolicy(Policy):

    def execute(self, demorunners, demorunners_workload, requirements=None):
        '''
        Chooses a random DemoRunner that matches the requirements
        '''
        try:

            suitable_dr = Policy().get_suitable_demorunners(requirements,demorunners)
            if len(suitable_dr) > 0:
                return suitable_dr[random.randrange(0, len(suitable_dr), 1)]
            else:
                print "RandomPolicy could not find any DR available"
                return None

        except Exception as ex:
            print "Error in execute policy Random", ex

class SequentialPolicy(Policy):

    def __init__(self):
        self.iterator = 0


    def execute(self, demorunners, demorunners_workload, requirements=None):
        '''
        Chooses a random DemoRunner that matches the requirements
        '''

        try:
            suitable_dr = Policy().get_suitable_demorunners(requirements, demorunners)
            if len(suitable_dr) > 0:
                dr_winner = suitable_dr[self.iterator % len(suitable_dr)]
                self.iterator = (self.iterator + 1) % len(demorunners)
                return dr_winner
            else:
                print "SequentialPolicy could not find any DR available"
                return None

        except Exception as ex:
            print "Error in execute policy Sequential", ex


class LowestWorkloadPolicy(Policy):

    def execute(self, demorunners, demorunners_workload, requirements=None):
        """
        Chooses the DemoRunner with the lowest workload that matches the requirements
        """

        try:
            suitable_dr = Policy().get_suitable_demorunners(requirements, demorunners)
            if len(suitable_dr) == 0:
                print "LowestWorkloadPolicy could not find any DR available"
                return None

            # Adds the workload of each demorunner to a dict
            dict_dr_wl = json.loads(demorunners_workload.replace('\'', '\"'))

            # This number must be the highest workload possible
            workload = 100.0

            lowest_workload_dr = None
            for dr in suitable_dr:

                if workload > float(dict_dr_wl[dr.name]):
                    workload = dict_dr_wl[dr.name]
                    lowest_workload_dr = dr

            return lowest_workload_dr

        except Exception as ex:
            print "Error in execute policy Lowest Workload", ex

                        # ---------------------------------------------------------------------------

class DemoRunnerInfo(object):
    '''
    Demorunner information object
    '''

    def __init__(self, server, name, capabilities=[]):
        self.capabilities = capabilities
        self.server = server
        self.name = name