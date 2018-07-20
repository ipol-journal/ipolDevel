"""
build tools
"""
import base64
import os, shutil
import urllib
import urllib2
import time
import tarfile
import zipfile
import shlex
from subprocess import Popen
import cherrypy

from time import gmtime, strftime
import datetime

import os.path

TIME_FMT = "%a, %d %b %Y %H:%M:%S %Z"


class IPOLHTTPMissingHeader(Exception):
    """
    IPOLHTTPMissingHeader
    """
    pass

class IPOLCompilationError(Exception):
    """
    IPOLCompilationError
    """
    pass

def download(url, fname, username=None, password=None):
    """
    download a file from the network if it is newer than the local
    file

    @param url: source url
    @param fname: destination file name

    @return: the file name
    """

    # create the folder if needed
    if not os.path.isdir(os.path.dirname(fname)):
        os.makedirs(os.path.dirname(fname))

    # Open the url. Add authorization header if needed
    if username is None:
        url_handle = urllib2.urlopen(url)
    else:
        request = urllib2.Request(url)
        base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string)
        url_handle = urllib2.urlopen(request)

    if not os.path.isfile(fname):
        # no local copy : retrieve
        file_handle = open(fname, 'w')
        file_handle.write(url_handle.read())
        file_handle.close()
        return True
    else:
        # only retrieve if a newer version is available
        url_info = url_handle.info()

        if 'last-modified' not in url_info:
            raise IPOLHTTPMissingHeader("Missing 'last-modified' HTTP header")

        last_modified = url_info['last-modified']
        url_ctime = datetime.datetime.strptime(last_modified, TIME_FMT)

        url_size = int(url_info['content-length'])
        file_ctime = datetime.datetime.fromtimestamp(os.path.getctime(fname))
        file_size = os.path.getsize(fname)

        need_download = url_size != file_size or url_ctime > file_ctime
        if need_download:
            # download
            file_handle = open(fname, 'w')
            file_handle.write(url_handle.read())
            file_handle.close()
            print "Retrieved"

        return need_download


def extract(fname, target):
    """
    extract tar, tgz, tbz and zip archives

    @param fname: archive file name
    @param target: target extraction directory

    @return: the archive content
    """
    try:
        # start with tar
        ar = tarfile.open(fname)
        content = ar.getnames()
    except tarfile.ReadError:
        # retry with zip
        ar = zipfile.ZipFile(fname)
        content = ar.namelist()

    # no absolute file name
    assert not any([os.path.isabs(f) for f in content])
    # no .. in file name
    assert not any([(".." in f) for f in content])

    # cleanup/create the target dir
    if os.path.isdir(target):
        shutil.rmtree(target)
    os.mkdir(target)

    # extract into the target dir
    try:
        ar.extractall(target)
    except IOError, AttributeError:
        # DUE TO SOME ODD BEHAVIOR OF extractall IN Pthon 2.6.1 (OSX 10.6.8)
        # BEFORE TGZ EXTRACT FAILS INSIDE THE TARGET DIRECTORY A FILE
        # IS CREATED, ONE WITH THE NAME OF THE PACKAGE
        # SO WE HAVE TO CLEAN IT BEFORE STARTING OVER WITH ZIP
        # cleanup/create the target dir
        if os.path.isdir(target):
            shutil.rmtree(target)
        os.mkdir(target)

        # zipfile module < 2.6
        for member in content:
            if member.endswith(os.path.sep):
                os.mkdir(os.path.join(target, member))
            else:
                f = open(os.path.join(target, member), 'wb')
                f.write(ar.read(member))
                f.close()

    return content


def run(command, stdout, cwd=None, env=None):
    """
    run a build execution

    @param command: shell-like command string
    @param stdout: standard output storage

    @return: the exit code
    """
    # merge env with the current environment
    if env != None:
        environ = os.environ
        environ.update(env)
        env = environ

    # open the log file and write the command
    logfile = open(stdout, 'w')
    logfile.write("%s : %s\n" % (time.strftime(TIME_FMT),
                                 command))
    # TODO : fix'n'clean
    logfile.close()
    logfile = open(stdout, 'a')
    process = Popen(shlex.split(command), stdout=logfile, stderr=logfile,
                    cwd=cwd, env=env)
    process.wait()
    logfile.close()
    if 0 != process.returncode:
        raise IPOLCompilationError
    return process.returncode
