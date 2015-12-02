#!/usr/bin/python
# -*- coding:utf-8 -*-

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# Written by Alexis Mongin. Contact : alexis.mongin #~AT~# outlook.com

"""
This script implements a terminal for controlling the IPOL system modules.
"""

import os
import subprocess
import urllib
import xml.etree.ElementTree as ET

class Terminal(object):
    """
    This is the terminal.
    """


    @staticmethod
    def get_dict_modules():
        """
        Return a dictionary of the differents IPOL modules as keys, and
        another dictionary as value, containing several keys: a url,
        the server where the module is, the directory of the module on the
        server, and a list of strings representing the commands available
        to the module.
        """
        dict_modules = {}
        tree = ET.parse('config_common/modules.xml')
        root = tree.getroot()

        for module in root.findall('module'):
            dict_tmp = {}
            list_tmp = []

            for command in module.findall('command'):
                list_tmp.append(command.text)

            list_tmp.append("info")
            dict_tmp["url"] = module.find('url').text
            dict_tmp["server"] = module.find('server').text
            dict_tmp["path"] = module.find('path').text
            dict_tmp["commands"] = list_tmp
            dict_modules[module.get('name')] = dict_tmp

        return dict_modules


    @staticmethod
    def do_nothing(_dummy):
        """
        Do nothing :)
        """
        return


    def __init__(self):
        self.dict_modules = self.get_dict_modules()


    def get_active_modules(self):
        """
        Print a list of the active modules.
        """
        modules_up = False
        print "Welcome to IPOL control terminal !"
        for key, value in self.dict_modules.items():
            try:
                urllib.urlopen(value["url"] + "ping")
                print key + " module running."
                modules_up = True
            except IOError:
                pass

        if not modules_up:
            print "No modules running."


    def check_module_input(self, command, args_array):
        """
        This function checks, for commands taking a module as a parameter,
        that the given module exists and the command is valid for it.
        """
        status = True
        if len(args_array) == 0:
            print "Missing module parameter"
            status = False
        elif args_array[0] not in self.dict_modules.keys():
            print "Given module doesn't exist."
            status  = False
        elif command not in self.dict_modules[args_array[0]]["commands"]:
            status = False
            print ("command " + command + " unavailable for module"
                   + args_array[0])
        return status


    def ping_module(self, args_array):
        """
        Ping specified module.
        """
        if not self.check_module_input("ping", args_array):
            return

        module = args_array[0]
        try:
            urllib.urlopen(self.dict_modules[module]["url"]
                           + "ping")
            print module + " : Module active, it says pong!"
        except IOError:
            print module + " : Module unresponsive."


    def ping_all(self, _dummy):
        """
        ping all modules
        """
        for module in self.dict_modules.keys():
            list_tmp = [module,]
            self.ping_module(list_tmp)


    def stop_module(self, args_array):
        """
        Stop specified module.
        """
        if not self.check_module_input("stop", args_array):
            return

        module = args_array[0]
        try:
            urllib.urlopen(self.dict_modules[module]["url"]
                           + "shutdown")
            print module + " shut down."
        except IOError:
            print module + " : stop : service unreachable."


    def start_module(self, args_array):
        """
        Start specified module.
        """
        if not self.check_module_input("start", args_array):
            return

        module = args_array[0]
        try:
            cmd = (" \"" + self.dict_modules[module]["path"] + "start.sh\" ")
            os.system("ssh " + self.dict_modules[module]["server"] + cmd + "&")
            print module + " started, try to ping it."
        except Exception as ex:
            print ex


    def start_all(self, _dummy):
        """
        Start all the modules.
        """
        for module in self.dict_modules.keys():
            list_tmp = [module,]
            self.start_module(list_tmp)

    def stop_all(self, _dummy):
        """
        Shutdown all the modules.
        """
        for module in self.dict_modules.keys():
            list_tmp = [module,]
            self.stop_module(list_tmp)


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
        print "List of avalaible commands for " + module + " module :"
        for command in self.dict_modules[module]["commands"]:
            if command != "info":
                print "    " + command
        print ""


    def display_modules(self, _dummy):
        """
        Print the modules.
        """
        print "list of modules :"
        for module in self.dict_modules.keys():
            print module


    def display_help(self, _dummy):
        """
        Help of the terminal
        """
        print "Please read the documentation."


    def pull(self, _dummy):
        """
        Ssh into ipol2 and pull.
        """
        os.system("ssh ipol2 \"cd ipolDevel && git pull\"")

    def exec_loop(self):
        """
        Execution loop of the terminal.
        """
        str_input = str()
        entry_buffer = {
            "startall" : self.start_all,
            "start" : self.start_module,
            "stop" : self.stop_module,
            "stopall" : self.stop_all,
            "restart" : self.restart_module,
            "ping" : self.ping_module,
            "pingall" : self.ping_all,
            "info" : self.info_module,
            "modules": self.display_modules,
            "pull" : self.pull,
            "help" : self.display_help,
            "exit" : self.do_nothing,
            "" : self.do_nothing
        }

        self.get_active_modules()

        try:
            while str_input != "exit":
                str_input = raw_input("admin@IPOL:~>")
                tab_input = str_input.split(" ", -1)

                if tab_input[0] in entry_buffer.keys():
                    entry_buffer[tab_input[0]](tab_input[1:])
                else:
                    print "Invalid command."

        except EOFError:
            str_input = "exit"
            print


def main():
    """
    Main function of the program.
    """
    terminal = Terminal()
    terminal.exec_loop()

if __name__ == "__main__":
    main()
