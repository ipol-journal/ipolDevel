"""
empty IPOL demo web app
this class handles all the backend : paths, archives, indexes, ...
"""

#
# EMPTY APP
#

import hashlib
from datetime import datetime
from random import random

import os
import time
from subprocess import Popen

from cherrypy import TimeoutError
import cherrypy

from . import archive
from . import config

class empty_app(object):
    """
    This app only contains configuration and tools, no actions.
    """

    def __init__(self, base_dir):
        """
        app setup

        @param base_dir: the base directory for this demo, used to
        look for special subfolders (input, tmp, ...)
        """
        # the demo ID is the folder name
        self.base_dir = os.path.abspath(base_dir) + os.path.sep
        self.id = os.path.basename(base_dir)

        # TODO: better key initialization
        self.key = ''
        self.cfg = dict()

        # static subfolders
        for static_dir in [self.input_dir, self.tmp_dir, \
                           self.archive_dir, self.static_dir]:
            # Create static subfolder
            if not os.path.isdir(static_dir):
                os.mkdir(static_dir)

        # TODO : merge with getattr
        self.archive_index = os.path.join(self.archive_dir, "index.db")

        # static folders
        # mime types, override python mimetypes modules because it
        # says .gz files are text/plain, which is right (gzip is an
        # encoding, not a mime type) but a problem (we use http gzip
        # compression on text/plain files)
        mime_types = {'gz' : 'application/x-gzip-compressed'}
        # use cherrypy.tools.staticdir as a decorator,
        self.input = \
            cherrypy.tools.staticdir(dir=self.input_dir,
                                     content_types=mime_types)\
                                     (lambda x: None)
        self.tmp = \
            cherrypy.tools.staticdir(dir=self.tmp_dir,
                                     content_types=mime_types)\
                                     (lambda x: None)
        self.arc = \
            cherrypy.tools.staticdir(dir=self.archive_dir,
                                     content_types=mime_types)\
                                     (lambda x: None)
        self.static = \
            cherrypy.tools.staticdir(dir=self.static_dir,
                                     content_types=mime_types)\
                                     (lambda x: None)


    def __getattr__(self, attr):
        """
        direct access to some class attributes
        """

        # subfolder patterns
        # TODO: "path" is the correct syntax
        dir_pattern = {'input_dir' : 'input',
                       'dl_dir' : 'dl',
                       'src_dir' : 'src',
                       'bin_dir' : 'bin',
                       'tmp_dir' : 'tmp',
                       'work_dir' : os.path.join('tmp', self.key),
                       'archive_dir' : 'archive',
                       'static_dir' : 'template/static'}
        url_pattern = {'base_url' : '/',
                       'input_url' : '/input/',
                       'tmp_url' : '/tmp/',
                       'work_url' : '/tmp/%s/' % self.key,
                       'archive_url' : '/arc/',
                       'static_url' : '/static/'}

        # subfolders
        if attr in dir_pattern:
            value = os.path.join(self.base_dir,
                                 dir_pattern[attr])
            value = os.path.abspath(value) + os.path.sep
        # url
        elif attr in url_pattern:
            value = cherrypy.url(path=url_pattern[attr])
        # real attribute
        else:
            value = object.__getattribute__(self, attr)
        return value

    def init_key(self, key):
        """
        reinitialize the key between 2 page calls
        """
        # delete key
        self.key = ''
        # regenerate key-related attributes
        self.new_key(key)

    def init_cfg(self):
        """
        reinitialize the config dictionary between 2 page calls
        """
        # read the config dict
        self.cfg = config.cfg_open(self.work_dir)
        # default three sections
        self.cfg.setdefault('param', {})
        self.cfg.setdefault('info', {})
        self.cfg.setdefault('meta', {})

    #
    # UPDATE
    #

    def build(self):
        """
        virtual function, to be overriden by subclasses
        """
        cherrypy.log("warning: no build method",
                     context='SETUP/%s' % self.id, traceback=False)

    #
    # KEY MANAGEMENT
    #

    def new_key(self, key=None):
        """
        create a key if needed, and the key-related attributes
        """
        if key is None:
            keygen = hashlib.md5()
            seeds = [cherrypy.request.remote.ip,
                     # use port to improve discrimination
                     # for proxied or NAT clients
                     cherrypy.request.remote.port,
                     datetime.now(),
                     random()]
            for seed in seeds:
                keygen.update(str(seed))
            key = keygen.hexdigest().upper()

        self.key = key

        # check key
        if not (self.key
                and self.key.isalnum()
                and (self.tmp_dir ==
                     os.path.commonprefix([self.work_dir, self.tmp_dir]))):
            # HTTP Bad Request
            raise cherrypy.HTTPError(400, "The key is invalid")

        if not os.path.isdir(self.work_dir):
            os.mkdir(self.work_dir)

        return

    #
    # LOGS
    #

    def log(self, msg):
        """
        simplified log handler

        @param msg: the log message string
        """
        cherrypy.log(msg, context="DEMO/%s/%s" % (self.id, self.key),
                     traceback=False)
        return

    #
    # SUBPROCESS
    #

    def run_proc(self, args, stdin=None, stdout=None, stderr=None, env=None):
        """
        execute a sub-process from the 'tmp' folder
        """

        if env is None:
            env = {}
        # update the environment
        newenv = os.environ.copy()
        # add local environment settings
        newenv.update(env)
        # TODO clear the PATH, hard-rewrite the exec arg0
        # TODO use shell-string execution
        newenv.update({'PATH' : self.bin_dir})
        # run
        return Popen(args, stdin=stdin, stdout=stdout, stderr=stderr,
                     env=newenv, cwd=self.work_dir)

    @staticmethod
    def wait_proc(process, timeout=False):
        """
        wait for the end of a process execution with an optional timeout
        timeout: False (no timeout) or a numeric value (seconds)
        process: a process or a process list, tuple, ...
        """

        # If production and timeout is not set, assign a security value
        if cherrypy.config['server.environment'] == 'production' and \
           not timeout:
            timeout = 60*15 # Avoid misconfigured demos running forever.

        if isinstance(process, Popen):
            # require a list
            process_list = [process]
        else:
            # duck typing, suppose we have an iterable
            process_list = process

        if not timeout:
            # timeout is False, None or 0
            # wait until everything is finished
            for p in process_list:
                p.wait()
        else:
            # http://stackoverflow.com/questions/1191374/
            # wainting for better : http://bugs.python.org/issue5673
            start_time = time.time()
            run_time = 0
            while True:
                if all([p.poll() is not None for p in process_list]):
                    # all processes have terminated
                    break
                run_time = time.time() - start_time
                if run_time > timeout:
                    for p in process_list:
                        try:
                            p.terminate()
                        except OSError:
                            # could not stop the process
                            # probably self-terminated
                            pass
                    raise TimeoutError
                time.sleep(0.1)
        if any([0 != p.returncode for p in process_list]):
            raise RuntimeError
        return

    #
    # ARCHIVE
    #

    def make_archive(self):
        """
        create an archive bucket
        """

        ar = archive.bucket(path=self.archive_dir,
                            cwd=self.work_dir,
                            key=self.key)
        ar.cfg['meta']['public'] = self.cfg['meta']['public']

        def hook_index():
            """
            hook index
            """

            return archive.index_add(self.archive_index,
                                     buc=ar,
                                     path=self.archive_dir)
        ar.hook['post-save'] = hook_index
        return ar

