#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
This file describes exception error class and printing color exception
"""

import sys

class   DatabaseError(Exception):
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

def print_exception_function(the_class, result):
    """
    This function prints exception message with color
    during access to the database

    :param the_class: exception class
    :type the_class: DatabaseError
    :param result: result of exception on web service function
    :type result: string
    """
    type_error = type(the_class).__name__
    name_function = str(the_class)

    mess = PrintColors.FAIL
    mess += "[Exception message]:\n\t[Type]: " + type_error
    mess += "\n\t[Location]: " + name_function
    mess += "\n\t[Result]: " + result + PrintColors.ENDC

    print >> sys.stderr, mess

def print_usage_function(executable):
    """
    This function prints usage message with color

    :param executable: name of binary
    :type executable: string
    """
    mess = PrintColors.WARNING
    mess += "[Usage]: " + executable + " file.conf"

    print >> sys.stderr, mess

def print_exception_thumbnail(result, name_function):
    """
    This function prints exception message for the creation of thumbnails

    :param name_function: name of the current function
    :type name_function: string
    """
    mess = PrintColors.FAIL
    mess += "[Exception message]:\n\t[Type]: IOError"
    mess += "\n\t[Location]: " + name_function
    mess += "\n\t[Result]: " + result + PrintColors.ENDC

    print >> sys.stderr, mess

def print_exception_zip(name_function, name_zip):
    """
    This function prints exception message for the decompress zip file

    :param name_function: name of the current function
    :type name_function: string
    :param name_zip: name of the zip file
    :type name_zip: string
    """
    mess = PrintColors.FAIL
    mess += "[Exception message]:\n\t[Type]: ZipError"
    mess += "\n\t[Location]: " + name_function
    mess += "\n\t[Result]: index.cfg missing in " + name_zip
    mess += ": Cannot add item in database" + PrintColors.ENDC

    print >> sys.stderr, mess

