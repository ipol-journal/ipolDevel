"""
Dispatcher policy model classes.
"""

import random
from typing import Optional

from .demorunnerinfo import DemoRunnerInfo


def get_suitable_demorunners(
    requirements: str, demorunners: list[DemoRunnerInfo]
) -> list[DemoRunnerInfo]:
    """
    Return all the suitable demorunners
    """
    suitable_demorunners = []
    reqs = {req.strip() for req in requirements.lower().split(",") if req.strip()}

    def capability_is_respected(capability, requirements):
        if capability.endswith("!"):
            capability = capability.rstrip("!")
            return capability in requirements
        return True

    def requirement_is_respected(requirement, capabilities):
        plain_capabilities = {c.rstrip("!") for c in capabilities}
        return requirement in plain_capabilities

    for dr in demorunners:
        dr_capabilities = {cap.lower().strip() for cap in dr.capabilities}

        if all(
            requirement_is_respected(requirement, dr_capabilities)
            for requirement in reqs
        ) and all(
            capability_is_respected(capability, reqs) for capability in dr_capabilities
        ):
            suitable_demorunners.append(dr)

    return suitable_demorunners


class Policy:
    """
    This class represents the policy used to pick a demoRunner at each
    execution.
    """

    def execute(
        self,
        demorunners: list[DemoRunnerInfo],
        workloads: dict[str, float],
        requirements: str,
    ) -> Optional[DemoRunnerInfo]:
        """
        Choose a DemoRunner that matches the requirements
        """
        suitable_drs = get_suitable_demorunners(requirements, demorunners)

        if not suitable_drs:
            return None

        workloads = {dr.name: workloads[dr.name] for dr in suitable_drs}
        assert all(dr.name in workloads for dr in suitable_drs)

        return self._choose(suitable_drs, workloads)

    def _choose(
        self, demorunners: list[DemoRunnerInfo], demorunners_workload: dict[str, float]
    ) -> Optional[DemoRunnerInfo]:
        raise NotImplementedError()


class RandomPolicy(Policy):
    def _choose(
        self, demorunners: list[DemoRunnerInfo], workload: dict[str, float]
    ) -> Optional[DemoRunnerInfo]:
        """
        Chooses a random DemoRunner that matches the requirements
        """
        return random.choice(demorunners)


class SequentialPolicy(Policy):
    def __init__(self):
        self.iterator = 0

    def _choose(
        self, demorunners: list[DemoRunnerInfo], workload: dict[str, float]
    ) -> Optional[DemoRunnerInfo]:
        """
        Chooses a random DemoRunner that matches the requirements
        """
        dr = demorunners[self.iterator % len(demorunners)]
        self.iterator = (self.iterator + 1) % len(demorunners)
        return dr


class LowestWorkloadPolicy(Policy):
    def _choose(
        self, demorunners: list[DemoRunnerInfo], workload: dict[str, float]
    ) -> Optional[DemoRunnerInfo]:
        """
        Chooses the DemoRunner with the lowest workload which
        satisfies the requirements.
        """
        return min(demorunners, key=lambda dr: workload[dr.name])
