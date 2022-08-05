#!/usr/bin/env python3
# -*- coding:utf-8 -*-

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

"""
IPOL modules control terminal.
A tool for sysadmins.
"""

import json
import os
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

# Prompt
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

import sys

ROOT = Path(__file__).parent.parent.parent.absolute()

class Terminal(object):
    """
    IPOL Control Terminal Tool
    """

    def get_modules_xml_filename(self):
        '''
        Gets the full path of the modules.xml configuration file
        '''
        return os.path.join(ROOT, 'ipol_demo/modules/config_common/modules.xml')

    def get_demorunners_xml_filename(self):
        '''
        Gets the full path of the demorunners.xml configuration file
        '''
        return os.path.join(ROOT, 'ipol_demo/modules/config_common/demorunners.xml')

    def get_ipol_environment(self):
        '''
        Returns the IPOL environment being currently used
        '''
        link = self.get_modules_xml_filename()
        if not os.path.islink(link):
            print("ERROR: file is not a link! - {}".format(link))
            sys.exit(0)
        filename = os.path.normpath(os.path.realpath(link))
        
        # The environment is on the right of directory 'env':
        dirs = filename.split(os.sep)
        idx = dirs.index("envs")
        return dirs[idx+1]

    def set_ipol_environment(self, env):
        '''
        Sets the IPOL environment
        '''
        # Get targets
        target_modules = os.path.join(ROOT, 'ipol_demo/modules/config_common/envs/{}/modules.xml'.format(env))
        if not os.path.isfile(target_modules):
            print("ERROR. File not found: {}".format(target_modules))
            return

        target_demorunners = os.path.join(ROOT, 'ipol_demo/modules/config_common/envs/{}/demorunners.xml'.format(env))
        if not os.path.isfile(target_demorunners):
            print("ERROR. File not found: {}".format(target_modules))
            return

        # Remove links
        link_modules = self.get_modules_xml_filename()
        if os.path.islink(link_modules):
            os.remove(link_modules)
        
        link_demorunners = self.get_demorunners_xml_filename()
        if os.path.islink(link_demorunners):
            os.remove(link_demorunners)
        
        # Create the new links
        os.symlink(target_modules, link_modules)
        os.symlink(target_demorunners, link_demorunners)
        
        # Reload new configuration
        self.reload_config()
        
    def env_command(self, args_array):
        # Remove empty arguments
        args = [arg for arg in args_array if arg.strip() != ""]

        if len(args) == 0:
            # Show environment
            print("\033[96m{}\033[0m".format(self.get_ipol_environment()))
        elif len(args) == 1:
            # Set environment
            environment = args[0]
            self.set_ipol_environment(environment)
        else:
            print("ERROR: wrong number or arguments")

    def add_modules(self):
        """
        Return a dictionary of the differents IPOL modules as keys, and
        another dictionary as value, containing several keys: a url,
        the server where the module is, the directory of the module on the
        server, and a list of strings representing the commands available
        to the module.
        """        
        dict_modules = {}
        tree = ET.parse(self.get_modules_xml_filename())
        root = tree.getroot()

        for module in root.findall('module'):
            dict_tmp = {}
            list_tmp = []

            for command in module.findall('command'):
                list_tmp.append(command.text)

            list_tmp.append("info")
            dict_tmp["server"] = module.find('server').text
            dict_tmp["module"] = module.find('module').text
            dict_tmp["serverSSH"] = module.find('serverSSH').text
            dict_tmp["path"] = module.find('path').text
            dict_tmp["commands"] = list_tmp
            self.dict_modules[module.get('name')] = dict_tmp

        return dict_modules

    def add_demorunners(self):
        """
        Read demorunners xml
        """
        dict_demorunners = {}
        tree = ET.parse(self.get_demorunners_xml_filename())
        root = tree.getroot()

        list_tmp = []
        for commands in root.findall('commands'):
            for command in commands.findall('command'):
                list_tmp.append(command.text)
        list_tmp.append("info")
        for demorunner in root.findall('demorunner'):
            dict_tmp = {}
            dict_tmp["name"] = demorunner.attrib['name']
            dict_tmp["server"] = demorunner.find('server').text
            dict_tmp["module"] = demorunner.find('module').text
            dict_tmp["serverSSH"] = demorunner.find('serverSSH').text
            dict_tmp["path"] = demorunner.find('path').text
            dict_tmp["commands"] = list_tmp

            self.dict_modules[demorunner.get('name')] = dict_tmp

        return dict_demorunners

    @staticmethod
    def do_nothing(dummy=None):
        """
        Do nothing
        """
        pass
        
    def reload_config(self):
        '''
        Reloads the configuration files
        '''
        # Read module's info
        self.dict_modules = {}

        # Add to dict_modules the information in modules.xml and demorunners.xml
        self.add_modules()
        self.add_demorunners()

        # Get pull servers
        self.pull_servers = set()
        for module in list(self.dict_modules.keys()):
            self.pull_servers.add(self.dict_modules[module]["serverSSH"])


    def __init__(self):
        '''
        Constructor
        '''
        # Create the links to integration by default if absent
        filename_modules = self.get_modules_xml_filename()
        filename_demorunners = self.get_demorunners_xml_filename()

        if not (os.path.exists(filename_modules) and os.path.exists(filename_demorunners)):
            self.set_ipol_environment("integration")

        # Reload the configuration
        self.reload_config()

    def get_active_modules(self):
        """
        Print a list of the active modules.
        """
        modules_up = False
        print("Welcome to the IPOL Control Terminal")
        print("Cursor up to repeat a line")
        print("Cursor right to autocomplete from the history")
        environment = self.get_ipol_environment()
        print("Environment: \033[96m{}\033[0m".format(environment))
        print()

        for key, value in list(self.dict_modules.items()):
            list_tmp = [key, ]
            if self.ping_module(list_tmp):
                modules_up = True
        print("\n")
        if not modules_up:
            print("\033[93mNo modules running. Check if NGINX is running\033[0m")

    def check_module_input(self, command, args_array):
        """
        This function checks, for commands taking a module as a parameter,
        that the given module exists and the command is valid for it.
        """
        status = True
        if len(args_array) == 0:
            print("Missing module parameter")
            status = False
        elif args_array[0] not in list(self.dict_modules.keys()):
            print("Given module doesn't exist.")
            status = False
        elif command not in self.dict_modules[args_array[0]]["commands"]:
            status = False
            print(("command " + command + " unavailable for module"
                   + args_array[0]))
        return status

    def ping_module(self, args_array):
        """
        Ping specified module.
        """
        if not self.check_module_input("ping", args_array):
            return False
        name = args_array[0]
        try:
            server = self.dict_modules[name]["server"]
            module = self.dict_modules[name]["module"]
            if module in ('demorunner', 'demorunner-docker'):
                json_response = urllib.request.urlopen(f"{server}api/demorunner/{name}/ping",
                    timeout=3).read()
            else:
                json_response = urllib.request.urlopen("http://{}/api/{}/ping".format(
                    server, module), timeout=3).read()

            response = json.loads(json_response.decode())
            status = response['status']

            if status == "OK":
                print("{} ({}): \033[92mOK\033[0m".format(name, self.dict_modules[name]["server"]))
                return True
            else:
                print("{} ({}): \033[31;1m*** KO ***\033[0m".format(name, self.dict_modules[name]["server"]))
                return False
        except Exception as ex:
            # No JSON object could be decoded exception
            print("{} ({}): \033[31;1mUnresponsive\033[0m".format(name, self.dict_modules[name]["server"]))
            return False

    def ping_all(self, dummy=None):
        """
        ping all modules
        """
        for module in list(self.dict_modules.keys()):
            list_tmp = [module, ]
            self.ping_module(list_tmp)

    def stop_module(self, args_array):
        """
        Stop specified module.
        """
        if not self.check_module_input("stop", args_array):
            return

        name = args_array[0]
        try:
            if self.dict_modules[name]["module"] == 'demorunner':
                server = self.dict_modules[name]["server"]
                module = self.dict_modules[name]["module"]
                json_response = urllib.request.urlopen(f"{server}api/{module}/{name}/shutdown", timeout=3).read()
            else:
                json_response = urllib.request.urlopen("http://{}/api/{}/shutdown".format(
                    self.dict_modules[name]["server"],
                    self.dict_modules[name]["module"]
                )).read()
            response = json.loads(json_response.decode())
            status = response['status']

            if status == "OK":
                print("{} ({}): \033[93mStopped\033[0m".format(name, self.dict_modules[name]["server"]))
            else:
                print("{} ({}): \033[31;1m*** KO ***\033[0m".format(name, self.dict_modules[name]["server"]))
                print(name + "  (" + self.dict_modules[name]["server"] 
                        + "): JSON response is KO when shutting down the module")
        except Exception:
            # No JSON object could be decoded exception
            print("{} ({}): \033[31;1m*** KO (exception) ***\033[0m".format(name, self.dict_modules[name]["server"]))

    def start_module(self, args_array):
        """
        Start specified module.
        """
        if not self.check_module_input("start", args_array):
            return

        module = args_array[0]
        try:
            cmd = (" \"" + self.dict_modules[module]["path"] + "start.sh\" &")
            os.system("ssh " + self.dict_modules[module]["serverSSH"] + cmd)
        except Exception as ex:
            print(ex)

    def start_all(self, dummy=None):
        """
        Start all the modules.
        """
        for module in list(self.dict_modules.keys()):
            print("Starting {} ({})".format(module, self.dict_modules[module]["server"]))
            self.start_module([module, ])

    def stop_all(self, dummy=None):
        """
        Shutdown all the modules.
        """
        for module in list(self.dict_modules.keys()):
            self.stop_module([module, ])

    def restart_module(self, args_array):
        """
        restart specified module.
        """
        self.stop_module(args_array)
        self.start_module(args_array)

    def info_module(self, args_array):
        """
        Print the list of available commands for a given module.
        """
        if not self.check_module_input("info", args_array):
            return

        module = args_array[0]
        print("List of avalaible commands for " + module + " module :")
        for command in self.dict_modules[module]["commands"]:
            if command != "info":
                print("    " + command)
        print("")

    def display_modules(self, dummy=None):
        """
        Print the modules.
        """
        print("list of modules :")
        for module in list(self.dict_modules.keys()):
            print(module)

    def display_help(self, dummy=None):
        """
        Help of the terminal
        """
        print("""List of available commands:
    startall          : Start all IPOL modules
    start <module>    : Start selected module
    stopall           : Stop all IPOL modules
    stop <module>     : Stop selected module
    restart <module>  : Restart selected module
    pingall           : Ping all IPOL modules
    ping <module>     : Ping selected module
    info <module>     : List of the available commands for selected module
    modules           : List all IPOL modules
    pull              : Git pull in all servers
    env               : get or set the current IPOL environment
    help              : List available commands
    exit              : Exit the terminal
    """)
        print("For more detailed information please read the documentation.")

    def pull(self, dummy=None):
        """
        Ssh into servers and pull.
        """
        for server in self.pull_servers:
            print("\t * Pulling from {}".format(server))
            os.system('ssh {} "cd ipolDevel/ci_tests && bash pull.sh"'.format(server))
            print()

    def exec_loop(self):
        """
        Execution loop of the terminal.
        """
        user_input = ""
        entry_buffer = {
            "startall": self.start_all,
            "start": self.start_module,
            "stop": self.stop_module,
            "stopall": self.stop_all,
            "restart": self.restart_module,
            "ping": self.ping_module,
            "pingall": self.ping_all,
            "info": self.info_module,
            "modules": self.display_modules,
            "pull": self.pull,
            "env": self.env_command,
            "help": self.display_help,
            "exit": self.do_nothing,
            "": self.do_nothing
        }

        self.get_active_modules()

        try:
            while user_input != 'exit':

                user_input = prompt('IPOL> ',
                        history=FileHistory('history.txt'),
                        auto_suggest=AutoSuggestFromHistory()
                        )
                user_input = user_input.strip()

                tab_input = user_input.split(" ", -1)

                if tab_input[0] in list(entry_buffer.keys()):
                    entry_buffer[tab_input[0]](tab_input[1:])
                else:
                    print(f"\033[0;31mInvalid command: {tab_input[0]}\033[0m")
                
                print()
        except (EOFError, KeyboardInterrupt):
            print("\nexit")


def main():
    """
    Main function of the program.
    """
    terminal = Terminal()
    terminal.exec_loop()


if __name__ == "__main__":
    main()
