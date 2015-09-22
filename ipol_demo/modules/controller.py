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

class Controller(object):
    """
    This is the terminal.
    """

    @staticmethod
    def get_dict_modules():
        """
        Return a dictionary of the differents IPOL modules as keys, and
        their respectives URL at which the services can be accessed as values.
        """
        dict_modules = {}
        os.system("ls -d */ > .ctrl_tmp")

        with open(".ctrl_tmp") as f:
            list_modules = f.readlines()

        list_modules = [i.strip('/\n') for i in list_modules]

        for module in list_modules:
            with open(module + "/module_url") as f:
                dict_modules[module] = f.readline()

        return dict_modules

    def get_actives_modules(self):
        """
        Return a list of the actives modules of IPOL.
        """
        active_modules = []

        for key, value in self.dict_modules.items():
            try:
                netobjct = urllib.urlopen(value + "ping")
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

        if module in self.dict_modules.keys():

            if module not in self.active_modules:
                print "Module not active."
                try:
                    netobjct = urllib.urlopen(self.dict_modules[module]
                                              + "ping")
                    print "But he's responsing ! Something went really wrong."
                    self.actives_modules.append(module)
                except IOError:
                    pass
            else:
                try:
                    netobjct = urllib.urlopen(self.dict_modules[module]
                                              + "ping")
                    print "Module active, he say pong !"
                except IOError:
                    print "Module active, unresponsive."

        else:
            print "module " + module + " don't exist."

    def shutdown_module(self, module):
        """
        Shutdown specified module.
        """
        if module in self.dict_modules.keys():
            try:
                netobjct = urllib.urlopen(self.dict_modules[module]
                                          + "shutdown")
                self.active_modules.remove(module)
                print module + " shut down."
            except IOError:
                pass
                print "Service unreachable."
        else:
            print "module " + module + " don't exist."

    def start_module(self, module):
        """
        Start specified module.
        """
        try :
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

    def exec_loop(self):
        """
        Execution loop of the terminal.
        """
        str_input = str()
        entry_buffer = {
            "start" : self.start_module,
            "shutdown" : self.shutdown_module,
            "restart" : self.restart_module,
            "ping" : self.ping_module
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

                if tab_input[0] != "exit" and tab_input[0] != "":

                    if len(tab_input) < 2 :
                        print "Invalid command."
                    elif tab_input[0] in entry_buffer.keys():
                        entry_buffer[tab_input[0]](tab_input[1])
                    else:
                        print tab_input[0] + " is not a command."
  
        except EOFError:
            str_input = "exit"
            print
            pass

def main():
    terminal = Controller()
    terminal.exec_loop()

if __name__ == "__main__":
    main()
