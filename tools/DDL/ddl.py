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
import sys

def do_read(args):
    '''
    Read a DDL
    '''
    print "read"
    print args

def do_write(args):
    '''
    Write a DDL
    '''
    print "write"
    print args
    
def do_read_all():
    '''
    Write a DDL
    '''
    print "do_read_all"

# Parse program arguments
parser = optparse.OptionParser()
(opts, args) = parser.parse_args()

if len(args) < 1:
    print "Error: no command specified!\n"
    parser.print_help()
    sys.exit(-1)

command = args[0].lower()
print command

if command == 'readall' or command == 'getall':
    do_read_all()
elif command == 'read' or command == 'get':
    do_read(args[1:])
elif command == 'write' or command == 'put':
    do_write(args[1:])
else:
    print "Unknown command '{}'".format(command)

