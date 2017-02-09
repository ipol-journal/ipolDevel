#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public Licence (GPL)
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place, Suite 330, Boston, MA  02111-1307  USA
#

import optparse
import re


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    ENDC = '\033[0m'


def start_scann(module):
    # Open and read file
    with open(module) as f:
        lines = f.readlines()

    for line_index in range(len(lines)):
        if "@cherrypy.expose" in lines[line_index]:

            line_index += 1
            while not "def" in lines[line_index]:
                line_index += 1

            # Name of the method
            print bcolors.OKBLUE + lines[line_index].strip()[:3] + bcolors.ENDC + lines[line_index].strip()[3:]
            while not "):" in lines[line_index]:
                line_index += 1
                print lines[line_index][:-1]

            line_index += 1
            # Check for comments or empty lines before docstring
            while lines[line_index].strip().startswith("#") or re.match(r'^\s*$', lines[line_index]):
                line_index += 1

            # Check if the method have any docstring
            if not ("\"\"\"" in lines[line_index] or "\'\'\'" in lines[line_index]):
                print "    " + bcolors.ERROR + "Warning: This method does not have any docstring" + bcolors.ENDC
            else:
                line_index += 1
                # Print the docstring
                while not ("\"\"\"" in lines[line_index] or "\'\'\'" in lines[line_index]):
                    print "    " + bcolors.OKGREEN + lines[line_index].strip() + bcolors.ENDC
                    line_index += 1
            print "\n"


# Parse program arguments
parser = optparse.OptionParser()
(opts, args) = parser.parse_args()

if len(args) != 1:
    print "Wrong number of arguments (given {}, expected 1)".format(len(args))
    exit(0)

module = args[0].lower()
acepted_modules = ["core", "dispatcher", "demorunner", "demoinfo", "blobs", "archive"]

if module in acepted_modules:
    module_file = "../../ipol_demo/modules/{}/{}.py".format(module, module)
    start_scann(module_file)
elif module == "all":
    for module in acepted_modules:
        print bcolors.HEADER + "\n ---------- {} ---------- \n".format(module.capitalize()) + bcolors.ENDC
        module_file = "../../ipol_demo/modules/{}/{}.py".format(module, module)
        start_scann(module_file)
else:
    print "Unknown module '{}'".format(module)
    exit(-1)
