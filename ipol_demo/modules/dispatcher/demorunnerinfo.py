#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
Demorunner information type class.
"""

class DemoRunnerInfo():
    """
    Demorunner information object
    """

    def __init__(self, server, name, serverSSH, capabilities=None):
        self.capabilities = [] if capabilities is None else capabilities
        self.server = server
        self.name = name
        self.serverSSH = serverSSH
