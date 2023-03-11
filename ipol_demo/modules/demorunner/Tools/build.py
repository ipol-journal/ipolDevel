"""
build tools
"""
import base64
import datetime
import os
import os.path
import shutil
import tarfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from subprocess import Popen

from .error import VirtualEnvError

TIME_FMT = "%a, %d %b %Y %H:%M:%S %Z"

class IPOLInvalidPath(Exception):
    """
    IPOLInvalidPath
    """
    pass

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
        url_handle = urllib.request.urlopen(url)
    else:
        request = urllib.request.Request(url)
        base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string)
        url_handle = urllib.request.urlopen(request)
    if not os.path.isfile(fname):
        # no local copy : retrieve
        urllib.request.urlretrieve(url, fname)
        return True
    else:
        # only retrieve if a newer version is available
        url_info = url_handle.info()

        if 'last-modified' not in url_info:
            raise IPOLHTTPMissingHeader("Missing 'last-modified' HTTP header")

        last_modified = url_info['last-modified']
        url_ctime = datetime.datetime.strptime(last_modified, TIME_FMT)

        url_size = int(url_info['content-length'])
        file_utc_ctime = datetime.datetime.utcfromtimestamp(os.path.getmtime(fname))
        file_size = os.path.getsize(fname)

        need_download = url_size != file_size or url_ctime > file_utc_ctime
        if need_download:
            # download
            file_handle = open(fname, 'wb')
            file_handle.write(url_handle.read())
            file_handle.close()
            print("Retrieved")

        return need_download


def extract(fname, target):
    """
    extract tar, tgz, tbz and zip archives

    @param fname: archive file name
    @param target: target extraction directory

    @return: the archive content
    """
    extension = os.path.splitext(fname)[1]
    if extension == '.zip':
        ar = zipfile.ZipFile(fname)
        content = ar.namelist()

        # Report bad path in case of starting with "/" or containing ".."
        if any([os.path.isabs(f) or ".." in f for f in content]):
            raise IPOLInvalidPath
    else:
        # tar files
        ar = tarfile.open(fname)
        content = ar.getnames()

    # cleanup/create the target dir
    if os.path.isdir(target):
        for entry in os.listdir(target):
            file_path = os.path.join(target, entry)
            if os.path.isfile(file_path):
                os.unlink(file_path)
            else:
                shutil.rmtree(file_path)
    else:
        os.mkdir(target)

    # extract into the target dir
    try:
        ar.extractall(target)
    except IOError:
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


def run(command, stdout, cwd=None):
    """
    run a build execution

    @param command: shell-like command string
    @param stdout: standard output storage

    @return: the exit code
    """
    if "VIRTUAL_ENV" not in os.environ.copy():
        raise VirtualEnvError('Running without a virtualenv')
    # open the log file and write the command
    with open(stdout, 'w') as logfile:
        logfile.write("%s : %s\n" % (time.strftime(TIME_FMT),
                                     command))
    with open(stdout, 'a') as logfile:
        process = Popen(command, shell=True, stdout=logfile, stderr=logfile,
                        cwd=cwd)
    process.wait()
    if 0 != process.returncode:
        raise IPOLCompilationError
    return process.returncode
