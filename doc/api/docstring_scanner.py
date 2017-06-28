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
import time

def start_scann(module):
    # Open and read file
    method_list = []

    with open("../../ipol_demo/modules/{}/{}.py".format(module, module)) as f:
        lines = f.readlines()

    for line_index in range(len(lines)):

        method = ""
        if "@cherrypy.expose" in lines[line_index]:

            line_index += 1
            while not "def" in lines[line_index]:
                line_index += 1

            # Name of the method
            method += lines[line_index].strip() +"\n"
            while not "):" in lines[line_index]:
                line_index += 1
                method += lines[line_index][:-1] + "\n"

            line_index += 1
            # Check for comments or empty lines before docstring
            while lines[line_index].strip().startswith("#") or re.match(r'^\s*$', lines[line_index]):
                line_index += 1

            # Check if the method have any docstring
            if not ("\"\"\"" in lines[line_index] or "\'\'\'" in lines[line_index]):
                method += "    \\error{this method does not have any docstring}\n"
            else:
                line_index += 1
                # Docstring
                while not ("\"\"\"" in lines[line_index] or "\'\'\'" in lines[line_index]):
                    method += "    " + lines[line_index].strip() + "\n"
                    line_index += 1
            method += "\n"
            method_list.append(method)

    return {module:method_list}


def print_latex(content):
    result =""
    for module in content:
        result += "\\subsection{"+module.capitalize()+"} \n"
        result += "\\begin{itemize} \n"
        for method in content[module]:
            result += "\item {}".format(method.replace("_","\\_")
                                        .replace("\n","\n\\\\")
                                        .replace("<", "\textless")
                                        .replace(">", "\textgreater")
                                        .replace("{", "\{")
                                        .replace("}", "\}"))
        result += "\\end{itemize} \n"
    print result.replace("\\\\\\","\\")


# Parse program arguments
parser = optparse.OptionParser()
(opts, args) = parser.parse_args()

if len(args) > 1:
    print "Wrong number of arguments"
    exit(0)

module = args[0].lower() if len(args) == 1 else None
acepted_modules = ["core", "dispatcher", "demorunner", "demoinfo", "blobs", "archive", "conversion"]
date = time.strftime("%d/%m/%Y")
modules = []

if module in acepted_modules:
    modules.append(module)
elif module is None:
    modules = acepted_modules
else:
    print "Unknown module '{}'".format(module)
    exit(-1)

content = {}
for module in modules:
    content.update(start_scann(module))
print_latex(content)