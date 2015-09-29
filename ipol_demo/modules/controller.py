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
This script implement a terminal for controlling the IPOL system.
"""

import os
import subprocess
import urllib
import xml.etree.ElementTree as ET

class Controller(object):
    """
    This is the terminal.
    """

    @staticmethod
    def get_dict_modules():
        """
        Return a dictionary of the differents IPOL modules as keys, and
        another dictionary as value, containing two keys : a url (string), and
        a list of strings representing the commands availables to the module.
        """
        dict_modules = {}
        tree = ET.parse('modules.xml')
        root = tree.getroot()

        for module in root.findall('module'):
            dict_tmp = {}
            list_tmp = []

            for command in module.findall('command'):
                list_tmp.append(command.text)

            list_tmp.append("info")
            dict_tmp["url"] = module.find('url').text
            dict_tmp["commands"] = list_tmp
            dict_modules[module.get('name')] = dict_tmp

        return dict_modules

    @staticmethod
    def do_nothing():
        """
        Do nothing :)
        """
        return

    def get_actives_modules(self):
        """
        Return a list of the actives modules of IPOL.
        """
        active_modules = []

        for key, value in self.dict_modules.items():
            try:
                netobjct = urllib.urlopen(value["url"] + "ping")
                active_modules.append(key)
            except IOError:
                pass

        return active_modules

    def __init__(self):
        self.dict_modules = self.get_dict_modules()
        self.active_modules = self.get_actives_modules()

    def ping_module(self, module):
        """
        Ping specified module.
        """
        if module not in self.active_modules:
            print "Module not active."
            try:
                netobjct = urllib.urlopen(self.dict_modules[module]["url"]
                                          + "ping")
                print "But he's responsing ! Something went really wrong."
                self.actives_modules.append(module)
            except IOError:
                pass
        else:
            try:
                netobjct = urllib.urlopen(self.dict_modules[module]["url"]
                                          + "ping")
                print "Module active, he say pong !"
            except IOError:
                print ("Module active, unresponsive. " +
                       "(check your connection)")

    def shutdown_module(self, module):
        """
        Shutdown specified module.
        """
        try:
            netobjct = urllib.urlopen(self.dict_modules[module]["url"]
                                      + "shutdown")
            self.active_modules.remove(module)
            print module + " shut down."
        except IOError:
            pass
            print "Service unreachable."
            
    def start_module(self, module):
        """
        Start specified module.
        """
        try:
            if module not in self.active_modules:
                os.chdir(module)
                subprocess.Popen(["python", "main.py", module + "conf"],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
                os.chdir("..")
                self.active_modules.append(module)
                print module + " started !"
            else:
                print "Module already running."
        except Exception as ex:
            print ex

    def restart_module(self, module):
        """
        restart specified module.
        """
        self.shutdown_module(module)
        self.start_module(module)

    def info_module(self, module):
        """
        Give user info on specified module.
        """
        if module in self.active_modules:
            status = "active."
        else:
            status = "unactive."

        print "Status of " + module + " module : " + status
        print "List of avalaible commands for " + module + " module :"
        for command in self.dict_modules[module]["commands"]:
            if command != "info":
                print "    " + command
        print ""

    def process_command(self, tab_input, entry_buffer):
        """
        Check if the input is valid by verifying if the given module
        exist, and if the command given is authorized for the given module.
        """
        if tab_input[1] in self.dict_modules.keys():

            if tab_input[0] in self.dict_modules[tab_input[1]]["commands"]:
                entry_buffer[tab_input[0]](tab_input[1])
            else:
                print ("Requested command isn't available for module " +
                       tab_input[1])

        else:
            print "Module " + tab_input[1] + " don't exist."

    def display_modules(self):
        """
        Display the modules.
        """
        for module in self.dict_modules.keys():
            if module in self.active_modules:
                print module + " : active"
            else:
                print module + " : unactive"

    def display_help(self):
        """
        Help of the terminal
        """
        print "Read the freaking manual" # temporary

    def exec_loop(self):
        """
        Execution loop of the terminal.
        """
        str_input = str()
        entry_buffer_modules = {
            "start" : self.start_module,
            "shutdown" : self.shutdown_module,
            "restart" : self.restart_module,
            "ping" : self.ping_module,
            "info" : self.info_module
        }
        entry_buffer_terminal = {
            "exit" : self.do_nothing,
            "" : self.do_nothing,
            "modules": self.display_modules,
            "module": self.display_modules,
            "help" : self.display_help
        }

        print "Welcome to the Ipol control terminal."
        if len(self.active_modules) != 0:
            print "There is a list of actives modules :"
            for module in self.active_modules:
                print module
        else:
            print "There is no active modules."

        try:
            while str_input != "exit":
                str_input = raw_input("admin@IPOL:~>")
                tab_input = str_input.split(" ", -1)

                if tab_input[0] in entry_buffer_terminal.keys():
                    entry_buffer_terminal[tab_input[0]]()
                elif tab_input[0] in entry_buffer_modules.keys():
                    if len(tab_input) < 2:
                        print "Invalid command."
                    else:
                        self.process_command(tab_input, entry_buffer_modules)
                else:
                    print "Invalid command."

        except EOFError:
            str_input = "exit"
            print
            pass

def main():
    """
    Main function of the program.
    """
    terminal = Controller()
    terminal.exec_loop()

if __name__ == "__main__":
    main()
