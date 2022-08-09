#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
Dispatcher policy model classes.
"""

import random


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
        suitable_demorunners = []
        if requirements:
            requirements = {req.strip() for req in requirements.lower().split(',')}
        else:
            requirements = {}

        def capability_is_respected(capability, requirements):
            if capability.endswith('!'):
                capability = capability.rstrip('!')
                return capability in requirements
            return True
        def requirement_is_respected(requirement, capabilities):
            plain_capabilities = {c.rstrip('!') for c in capabilities}
            return requirement in plain_capabilities

        for dr in demorunners:
            dr_capabilities = {cap.lower().strip() for cap in dr.capabilities}

            if all(requirement_is_respected(requirement, dr_capabilities) for requirement in requirements) \
            and all(capability_is_respected(capability, requirements) for capability in dr_capabilities):
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
