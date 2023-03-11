"""
various help tools for the IPOL demo environment
"""

import gzip as _gzip
import os
import time
from datetime import datetime
from functools import reduce

#
# TINY STUFF
#

def prod(lst):
    return reduce(lambda a, b: a * b, lst, 1)

#
# BASE_APP REUSE
#

def app_expose(function):
    """
    shortcut to expose app actions from the base class
    """
    function.__func__.exposed = True

#
# TIME
#

def _timeformat(t, fmt="struct"):
    """
    provide alternative time type formatting:
    * default: struct time
    * s : seconds since Epoch
    * iso : iso string
    """
    if "struct" == fmt:
        return time.gmtime(t)
    elif "s" == fmt:
        return  t
    elif "iso" == fmt:
        return datetime.fromtimestamp(t).isoformat('-')
    else:
        raise AttributeError

def ctime(path, fmt="struct"):
    """
    get the (unix) change time of a file/dir
    """
    return _timeformat(os.path.getctime(path), fmt)

def mtime(path, fmt="struct"):
    """
    get the (unix) modification time of a file/dir
    """
    return _timeformat(os.path.getmtime(path), fmt)

#
# GZIP
#

def gzip(fname_in, fname_out=None, delete=True):
    """
    compress a file with gzip, like the command-line utility
    """
    if not fname_out:
        fname_out = fname_in + ".gz"
    assert fname_out != fname_in
    # compress fname_in into fname_out
    f_in = open(fname_in, 'rb')
    f_out = _gzip.open(fname_out, 'wb')
    f_out.writelines(f_in)
    f_out.close()
    f_in.close()
    # delete fname_in
    if delete:
        os.unlink(fname_in)
    return

def gunzip(fname_in, fname_out=None, delete=True):
    """
    uncompress a file with gzip, like the command-line utility
    """
    if not fname_out:
        assert fname_in.endswith(".gz")
        fname_out = fname_in[:-3]
    assert fname_out != fname_in
    # decompress fname_in into fname_out
    f_in = _gzip.open(fname_in, 'rb')
    f_out = open(fname_out, 'wb')
    f_out.writelines(f_in)
    f_out.close()
    f_in.close()
    # delete fname_in
    if delete:
        os.unlink(fname_in)
    return
