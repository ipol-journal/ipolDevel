"""
Dispatcher: choose the best demorunner according to a policy
"""

import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass

import requests
from dispatcher.demorunnerinfo import DemoRunnerInfo
from dispatcher.policy import (
    LowestWorkloadPolicy,
    Policy,
    RandomPolicy,
    SequentialPolicy,
)
from result import Err, Ok, Result


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


class WorkloadProvider:

    def get_workload(self, demorunner: DemoRunnerInfo) -> Result[float, str]:
        raise NotImplementedError


@dataclass
class APIWorkloadProvider(WorkloadProvider):
    base_url: str
    timeout: float = 3.0

    def get_workload(self, demorunner: DemoRunnerInfo) -> Result[float, str]:
        name = demorunner.name
        url = f'{self.base_url}/api/demorunner/{name}/get_workload'

        try:
            resp = requests.get(url, timeout=self.timeout)
            resp.raise_for_status()
        except requests.RequestException as e:
            return Err(repr(e))

        try:
            response = resp.json()
        except requests.JSONDecodeError as e:
            return Err(repr(e))

        if response['status'] != 'OK':
            return Err("KO response")

        workload = response['workload']
        return Ok(workload)


class PingProvider:

    def ping(self, demorunner: DemoRunnerInfo) -> Result[None, str]:
        raise NotImplementedError


@dataclass
class APIPingProvider(PingProvider):
    base_url: str
    timeout: float = 3.0

    def ping(self, demorunner: DemoRunnerInfo) -> Result[None, str]:
        name = demorunner.name
        url = f'{self.base_url}/api/demorunner/{name}/ping'

        try:
            resp = requests.get(url, timeout=self.timeout)
            resp.raise_for_status()
        except requests.RequestException as e:
            return Err(repr(e))

        try:
            response = resp.json()
        except requests.JSONDecodeError as e:
            return Err(repr(e))

        if response['status'] != 'OK':
            return Err("KO response")

        return Ok()


def make_policy(name: str) -> Policy:
    """
    Factory Method
    """
    if name == "random":
        return RandomPolicy()
    if name == "sequential":
        return SequentialPolicy()
    if name == "lowest_workload":
        return LowestWorkloadPolicy()

    assert False


class Dispatcher:
    """
    The Dispatcher chooses the best DR according to a policy
    """

    def __init__(self,
                 workload_provider: WorkloadProvider,
                 ping_provider: PingProvider,
                 demorunners: list[DemoRunnerInfo],
                 policy: Policy = LowestWorkloadPolicy(),
                 ):
        self.workload_provider = workload_provider
        self.ping_provider = ping_provider
        self.demorunners = demorunners
        self.policy = policy
        self.logger = init_logging()

    def get_demorunners_stats(self) -> list[dict]:
        """
        Get statistic information of all DRs.
        This is mainly used by external monitoring tools.
        """
        stats = []
        for dr in self.demorunners:
            result = self.workload_provider.get_workload(dr)

            if isinstance(result, Ok):
                workload = round(result.value, 2)
                stats.append({
                    'status': 'OK',
                    'name': dr.name,
                    'workload': workload,
                })
            else:
                stats.append({
                    'status': 'KO',
                    'name': dr.name,
                    'message': result.value,
                })

        return stats

    def get_suitable_demorunner(self, requirements: str) -> Result[str, DispatcherError]:
        """
        Return an active DR which meets the requirements, or a DispatcherError.
        """
        dr_workloads = self.demorunners_workload()
        valid_drs = [dr for dr in self.demorunners if dr.name in dr_workloads]
        chosen_dr = self.policy.execute(valid_drs, dr_workloads, requirements)

        if chosen_dr is None:
            if requirements:
                err = NoSuitableDemorunnerForRequirementsError(requirements)
            else:
                err = NoDemorunnerAvailableError()
            self.logger.warning(err.error())
            return Err(err)

        ping_result = self.ping_provider.ping(chosen_dr)

        dr_name = chosen_dr.name
        if ping_result.is_err():
            self.logger.warning(f"Couldn't reach {dr_name}: {ping_result.value}")
            return Err(UnresponsiveDemorunnerError(dr_name))

        return Ok(dr_name)

    def demorunners_workload(self) -> dict[str, float]:
        """
        Get the workload of each DR
        """
        dr_workload = {}
        for dr_info in self.demorunners:
            name = dr_info.name

            result = self.workload_provider.get_workload(dr_info)

            if isinstance(result, Ok):
                dr_workload[name] = result.value
            else:
                self.logger.warning(f"Cannot get workload of {name}: {result.value}")

        return dr_workload


def init_logging():
    """
    Initialize the error logs of the module.
    """
    logger = logging.getLogger("dispatcher")

    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s; [%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger

def parse_demorunners(demorunners_path) -> list[DemoRunnerInfo]:
    """
    Parse a demorunners.xml file.
    """
    root = ET.parse(demorunners_path).getroot()

    demorunners = []
    for element in root.findall('demorunner'):
        capabilities = []
        for capability in element.findall('capability'):
            capabilities.append(capability.text)

        demorunners.append(DemoRunnerInfo(
            name=element.get('name'),
            capabilities=capabilities,
        ))

    return demorunners
