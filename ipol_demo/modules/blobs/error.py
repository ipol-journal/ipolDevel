#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
This file describes exception error class and printing color exception
"""

import sys
import sqlite3
import traceback

class   DatabaseError(sqlite3.Error):
    """
    Implements exception class
    """
    pass

class   DatabaseInsertError(DatabaseError):
    """
    Exception used when insert instruction failed in database
    """
    pass

class   DatabaseSelectError(DatabaseError):
    """
    Exception used when insert instruction failed in database
    """
    pass

class   DatabaseDeleteError(DatabaseError):
    """
    Exception used when delete instruction failed in database
    """
    pass

class DatabaseUpdateError(DatabaseError):
    """
    Exception used when update instruction failed in database
    """
    pass

class PrintColors(object):
    """
    Defined ANSI printing codes
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_usage_function(executable):
    """
    This function prints usage message with color

    :param executable: name of binary
    :type executable: string
    """
    mess = PrintColors.WARNING
    mess += "[Usage]: " + executable + " file.conf"

    print >> sys.stderr, mess

