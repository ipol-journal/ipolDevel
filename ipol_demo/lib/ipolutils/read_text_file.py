#!/usr/bin/env python3
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
"""
IPOL text file wrapper for reading
"""
import re
import sys


def read_commented_text_file(input_file):
    """
    Return the generated trimmed list after reading a commented text file
    """
    trimmed_list = []
    try:
        with open(input_file, 'r') as file_obj:
            lines = file_obj.readlines()
    except Exception as err:
        print(f"Failed to read input file '{input_file}' - {err}")
        sys.exit(-1)
    for line in lines:
        line_obj = re.match(r'([^#]*)#.*', line)
        if line_obj:
            line = line_obj.group(1)
        line = line.strip()
        if line:
            trimmed_list.append(line)
    return trimmed_list