#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
Dispatcher: choose the best demorunner according to a policy
"""

import json
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
import requests
from result import Ok, Err, Result

from .policy import Policy
from .demorunnerinfo import DemoRunnerInfo


def init_logging():
    """
    Initialize the error logs of the module.
    """
    logger = logging.getLogger("dispatcher_log")

    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s; [%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger


class DispatcherError:
    def error(self) -> str:
        raise NotImplementedError


@dataclass
class UnresponsiveDemorunnerError(DispatcherError):
    dr_name: str

    def error(self) -> str:
        return f"Demorunner '{self.dr_name}' is unresponsive."


class NoDemorunnerAvailableError(DispatcherError):

    def error(self) -> str:
        return 'No DR available.'


@dataclass
class NoSuitableDemorunnerForRequirementsError(DispatcherError):

    requirements: str

    def error(self) -> str:
        return f'No DR satisfies the requirements: {self.requirements}.'


def parse_demorunners(demorunners_file) -> list[DemoRunnerInfo]:
    """
    Update dispatcher's DRs information
    """
    root = ET.parse(demorunners_file).getroot()

    demorunners = []
    for element in root.findall('demorunner'):
        capabilities = []
        for capability in element.findall('capability'):
            capabilities.append(capability.text)

        demorunners.append(DemoRunnerInfo(
            element.get('name'),
            element.find('serverSSH').text,
            capabilities
        ))

    return demorunners


class Dispatcher():
    """
    The Dispatcher chooses the best DR according to a policy
    """

    def __init__(self,
                 base_url: str,
                 demorunners_file: str,
                 policy: str = "lowest_workload",
                 ):
        self.base_url = base_url
        self.logger = init_logging()
        self.policy = Policy.factory(policy)
        self.demorunners = parse_demorunners(demorunners_file)

    def get_demorunners_stats(self):
        """
        Get statistic information of all DRs.
        This is mainly used by external monitoring tools.
        """
        demorunners = []
        for dr in self.demorunners:
            try:
                url = f'{self.base_url}/api/demorunner/{dr.name}/get_workload'
                response = requests.get(url, timeout=3)
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

    def get_suitable_demorunner(self, requirements: str) -> Result[str, DispatcherError]:
        """
        Return an active DR which meets the requirements, or a DispatcherError.
        """
        # Get a demorunner for the requirements
        dr_workloads = self.demorunners_workload()
        chosen_dr = self.policy.execute(self.demorunners, dr_workloads, requirements)

        if not chosen_dr:
            if requirements:
                err = NoSuitableDemorunnerForRequirementsError(requirements)
            else:
                err = NoDemorunnerAvailableError()
            self.logger.error(err.error())
            return Err(err)

        dr_name = chosen_dr.name

        # Check if the DR is up.
        url = f'{self.base_url}/api/demorunner/{dr_name}/ping'
        dr_response = requests.get(url, timeout=3)
        if not dr_response:
            self.error_log("get_suitable_demorunner",
                           "Module {} unresponsive".format(dr_name))
            print("Module {} unresponsive".format(dr_name))
            return Err(UnresponsiveDemorunnerError(dr_name))

        return Ok(dr_name)

    def demorunners_workload(self):
        """
        Get the workload of each DR
        """
        dr_workload = {}
        for dr_info in self.demorunners:
            name = dr_info.name
            try:
                url = f'{self.base_url}/api/demorunner/{name}/get_workload'
                resp = requests.get(url, timeout=3)
                if not resp:
                    self.logger.error(f"No response from DR={name}")
                    continue

                response = resp.json()
                if response.get('status', '') == 'OK':
                    dr_workload[dr_info.name] = response.get('workload')
                else:
                    self.logger.error(f"get_workload KO response for DR={name}")
            except requests.ConnectionError:
                self.logger.error(f"get_workload ConnectionError for DR={name}")
                continue
            except Exception:
                self.logger.exception(f"Error when obtaining the workload of {name}")
                continue

        return dr_workload
