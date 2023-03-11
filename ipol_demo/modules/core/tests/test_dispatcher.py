from dataclasses import dataclass
from typing import Optional

from dispatcher.demorunnerinfo import DemoRunnerInfo
from dispatcher.dispatcher import (
    Dispatcher,
    NoDemorunnerAvailableError,
    NoSuitableDemorunnerForRequirementsError,
    PingProvider,
    UnresponsiveDemorunnerError,
    WorkloadProvider,
)
from dispatcher.policy import RandomPolicy
from result import Err, Ok, Result


@dataclass
class TestWorkloadProvider(WorkloadProvider):
    __test__ = False

    workloads: Optional[dict[str, Result[float, str]]] = None

    def get_workload(self, demorunner: DemoRunnerInfo) -> Result[float, str]:
        if self.workloads:
            return self.workloads[demorunner.name]
        return Ok(1)


@dataclass
class TestPingProvider(PingProvider):
    __test__ = False

    response: Result[None, str] = Ok()

    def ping(self, demorunner: DemoRunnerInfo) -> Result[None, str]:
        return self.response


def test_find_suitable_demorunner_empty_requirements():
    """
    Dispatcher should find a demorunner when requirements are empty and there is one demorunner without capabilities.
    """
    workload_provider = TestWorkloadProvider()
    ping_provider = TestPingProvider()
    demorunners = [
        DemoRunnerInfo(name="dr1", capabilities=[]),
        DemoRunnerInfo(name="dr2", capabilities=["c1!"]),
    ]
    dispatcher = Dispatcher(workload_provider, ping_provider, demorunners)

    r = dispatcher.get_suitable_demorunner(requirements="")
    dr = r.unwrap()
    assert dr == "dr1"


def test_find_suitable_demorunner_matches_capabilities():
    """
    Dispatcher should matches capabilities and requirements.
    Demorunners failing to return their workload should be ignored.
    """
    workload_provider = TestWorkloadProvider(
        workloads={
            "dr1": Ok(1),
            "dr2": Ok(1),
            "dr3": Ok(1),
            "dr4": Ok(1),
            "broken": Err("a"),
        }
    )
    ping_provider = TestPingProvider()
    demorunners = [
        DemoRunnerInfo(name="dr1", capabilities=[]),
        DemoRunnerInfo(name="dr2", capabilities=["c1!"]),
        DemoRunnerInfo(name="dr3", capabilities=["c1!", "c2!"]),
        DemoRunnerInfo(name="dr4", capabilities=["c1", "c2"]),
        DemoRunnerInfo(name="broken", capabilities=["c1", "c2"]),
    ]
    dispatcher = Dispatcher(
        workload_provider, ping_provider, demorunners, policy=RandomPolicy()
    )

    matches = set()
    for _ in range(1000):
        matches.add(dispatcher.get_suitable_demorunner(requirements="").unwrap())
    assert matches == {"dr1", "dr4"}

    matches = set()
    for _ in range(1000):
        matches.add(dispatcher.get_suitable_demorunner(requirements="c1").unwrap())
    assert matches == {"dr2", "dr4"}

    matches = set()
    for _ in range(1000):
        matches.add(dispatcher.get_suitable_demorunner(requirements="c2").unwrap())
    assert matches == {"dr4"}

    matches = set()
    for _ in range(1000):
        matches.add(dispatcher.get_suitable_demorunner(requirements="c1,c2").unwrap())
    assert matches == {"dr3", "dr4"}


def test_find_suitable_demorunner_empty_requirements_nodr():
    """
    Dispatcher should return a NoDemorunnerAvailableError error if there are no 'default' demorunner.
    """
    workload_provider = TestWorkloadProvider()
    ping_provider = TestPingProvider()
    demorunners = [
        DemoRunnerInfo(name="dr2", capabilities=["c1!"]),
    ]
    dispatcher = Dispatcher(workload_provider, ping_provider, demorunners)

    r = dispatcher.get_suitable_demorunner(requirements="")
    err = r.unwrap_err()
    assert isinstance(err, NoDemorunnerAvailableError)


def test_find_suitable_demorunner_invalid_requirements():
    """
    Dispatcher should return a NoSuitableDemorunnerForRequirementsError if there are not demorunner that can satisfy some requirements.
    """
    workload_provider = TestWorkloadProvider()
    ping_provider = TestPingProvider()
    demorunners = [
        DemoRunnerInfo(name="dr1", capabilities=[]),
    ]
    dispatcher = Dispatcher(workload_provider, ping_provider, demorunners)

    r = dispatcher.get_suitable_demorunner(requirements="c2")
    err = r.unwrap_err()
    assert isinstance(err, NoSuitableDemorunnerForRequirementsError)


def test_find_suitable_demorunner_unresponsive():
    """
    Dispatcher should return a UnresponsiveDemorunnerError if the DR is unreachable by a ping.
    """
    workload_provider = TestWorkloadProvider()
    ping_provider = TestPingProvider(response=Err("a"))
    demorunners = [
        DemoRunnerInfo(name="dr1", capabilities=[]),
    ]
    dispatcher = Dispatcher(workload_provider, ping_provider, demorunners)

    r = dispatcher.get_suitable_demorunner(requirements="")
    err = r.unwrap_err()
    assert isinstance(err, UnresponsiveDemorunnerError)


def test_get_demorunners_stats():
    """
    Dispatcher should return the stats of each demorunners.
    """
    workload_provider = TestWorkloadProvider(
        workloads={"dr1": Ok(2), "dr2": Ok(4), "dr3": Err("a")}
    )
    ping_provider = TestPingProvider(response=Err("a"))
    demorunners = [
        DemoRunnerInfo(name="dr1", capabilities=[]),
        DemoRunnerInfo(name="dr2", capabilities=[]),
        DemoRunnerInfo(name="dr3", capabilities=[]),
    ]
    dispatcher = Dispatcher(workload_provider, ping_provider, demorunners)

    stats = dispatcher.get_demorunners_stats()
    assert len(stats) == 3
    assert {"name": "dr1", "status": "OK", "workload": 2} in stats
    assert {"name": "dr2", "status": "OK", "workload": 4} in stats
    assert {"name": "dr3", "status": "KO", "message": "a"} in stats


def test_demorunners_workload():
    """
    Dispatcher should return the workload of each demorunners, except failing ones.
    """
    workload_provider = TestWorkloadProvider(
        workloads={"dr1": Ok(2), "dr2": Ok(4), "dr3": Err("a")}
    )
    ping_provider = TestPingProvider(response=Err("a"))
    demorunners = [
        DemoRunnerInfo(name="dr1", capabilities=[]),
        DemoRunnerInfo(name="dr2", capabilities=[]),
        DemoRunnerInfo(name="dr3", capabilities=[]),
    ]
    dispatcher = Dispatcher(workload_provider, ping_provider, demorunners)

    workloads = dispatcher.demorunners_workload()
    assert workloads == {"dr1": 2, "dr2": 4}
