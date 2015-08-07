"""
base IPOL demo web app
includes interaction and rendering
"""

# TODO add steps (cf amazon cart)

import shutil
from mako.lookup import TemplateLookup
import traceback
import cherrypy
import os.path
import math
import copy
import threading
import time

from mako.exceptions import RichTraceback
from . import http
from . import config
from . import archive
from .empty_app import empty_app
from .image import thumbnail, image
from .misc import prod
from shutil import rmtree

class AppPool(object):
    """
    App object pool used by the init_func decorator to
    obtain instances of the app object
    Used to fix a bug
    https://tools.ipol.im/mailman/archive/discuss/2012-December/000969.html
    """

    pool_lock = threading.Lock()

    class __AppPool(object):
        """
        App Pool singleton pattern implementation
        """
        pool = {}

        def pool_tidyup(self):
            """
            Removes old app objects from the pool, to save memory
            """
            keys_to_remove = []
            # Get keys of the objects to remove
            for key in self.pool.keys():
                entry = self.pool[key]
                timestamp = entry['timestamp']
                if time.time() - timestamp > 7200: # two hours
                    keys_to_remove.append(key)
            # Remove old objects
            for key in keys_to_remove:
                del self.pool[key]
            

        def get_app(self, exec_id):
            """
            Obtains the app object associated to the exec_id ID
            """
            if exec_id in self.pool:
                return self.pool[exec_id]['app_object']
            else:
                return None

        def add_app(self, exec_id, app_object):
            """
            Adds an app object and to the pool.
            The creation time is also stored
            """
            # Remove stored old app objects
            self.pool_tidyup()
            # Add app_object and timestamp
            entry = {'app_object': app_object,
                     'timestamp': time.time()}
            self.pool[exec_id] = entry

    # Singleton object instance
    instance = None

    @staticmethod
    def get_instance():
        """
        Get an app pool singleton instance
        """

        try:
            # Acquire lock
            AppPool.pool_lock.acquire()

            # Set singleton object instance
            if AppPool.instance is None:
                AppPool.instance = AppPool.__AppPool()
        finally:
            # Release lock
            AppPool.pool_lock.release()

        return AppPool.instance


#
# ACTION DECORATOR TO HANDLE GENERIC SETTINGS
#

def init_app(func):
    """
    decorator to reinitialize the app with the current request key
    """
    def init_func(self, *args, **kwargs):
        """
        original function, modified
        """            
        # key check
        key = kwargs.pop('key', None)
        # It might happen that here we receive a list with several copies of
        # the key, if the demo passes it more than once in the URL.
        #
        # In that case, just use the first entry of the list.
        if isinstance(key, list):
            if len(key) > 0:
                key = key[0]

        # Obtain a copy of the object and use it instead of self
        # Bug fix
        pool = AppPool.get_instance() # Singleton pattern
        #
        self2 = pool.get_app(key)
        if self2 is None:
            self2 = base_app(self.base_dir)
            self2.__class__ = self.__class__
            self2.__dict__.update(self.__dict__)
            pool.add_app(key, self2)

        if isinstance(key, list):
            key = key[0]
        self2.init_key(key)
        self2.init_cfg()

        # public_archive cookie setup
        # default value
        if not cherrypy.request.cookie.get('public_archive', '1') == '0':
            cherrypy.response.cookie['public_archive'] = '1'
            self2.cfg['meta']['public'] = True
        else:
            self2.cfg['meta']['public'] \
                = (cherrypy.request.cookie['public_archive'] != '0')

        # user setting
        if kwargs.has_key('set_public_archive'):
            if kwargs.pop('set_public_archive') != '0':
                cherrypy.response.cookie['public_archive'] = '1'
                self2.cfg['meta']['public'] = True
            else:
                cherrypy.response.cookie['public_archive'] = '0'
                self2.cfg['meta']['public'] = False
            # TODO: dirty hack, fixme
            ar_path = self2.archive_dir + archive.key2path(self2.key)
            if os.path.isdir(ar_path):
                ar = archive.bucket(path=self2.archive_dir,
                                    cwd=self2.work_dir,
                                    key=self2.key)
                ar.cfg['meta']['public'] = self2.cfg['meta']['public']
                ar.cfg.save()
                archive.index_add(self2.archive_index,
                                  buc=ar,
                                  path=self2.archive_dir)
        x = func(self2, *args, **kwargs)
        self2.cfg.save()
        return x
    return init_func


class base_app(empty_app):
    """ base demo app class with a typical flow """
    # default class attributes
    # to be modified in subclasses
    title = "base demo"

    input_nb = 1 # number of input files
    input_max_pixels = 1024 * 1024 # max size of an input image
    input_max_weight = 5 * 1024 * 1024 # max size (in bytes) of an input file
    input_dtype = '1x8i' # input image expected data type
    input_ext = '.tiff' # input image expected extention (ie. file format)
    timeout = 60 # subprocess execution timeout
    is_test = True

    def __init__(self, base_dir):
        """
        app setup
        base_dir is supposed to be received from a subclass
        """
        # setup the parent class
        empty_app.__init__(self, base_dir)
        cherrypy.log("base_dir: %s" % self.base_dir,
                     context='SETUP/%s' % self.id, traceback=False)
        # local base_app templates folder
        tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'template')
        # first search in the subclass template dir
        self.tmpl_lookup = TemplateLookup( \
            directories=[self.base_dir + 'template', tmpl_dir],
            input_encoding='utf-8',
            output_encoding='utf-8', encoding_errors='replace')

    #
    # TEMPLATES HANDLER
    #

    def tmpl_out(self, tmpl_fname, **kwargs):
        """
        templating shortcut, populated with the default app attributes
        """
        # pass the app object
        kwargs['app'] = self
        # production flag
        kwargs['prod'] = (cherrypy.config['server.environment']
                          == 'production')

        tmpl = self.tmpl_lookup.get_template(tmpl_fname)

        # Render the template
        # If an exception occurs, render an error page showing the traceback
        try:
            return tmpl.render(**kwargs)
        except:
            traceback_string = "<h1>IPOL template rendering error</h1>"
            traceback_string += "<h2>Template: %s</h2>" % tmpl_fname
            traceback_string += "<h2>kwargs: %s</h2>" % kwargs
            traceback = RichTraceback()
            for (filename, lineno, function, line) in traceback.traceback:
                traceback_string += \
                    "File <b>%s</b>, line <b>%d</b>, in <b>%s</b><br>" % \
                    (filename, lineno, function)
                traceback_string += line + "<br><br>"
            traceback_string += "%s: %s" % \
                (str(traceback.error.__class__.__name__), \
                traceback.error) + "<br>"
            return traceback_string


    #
    # INDEX
    #

    def valid_paths(self, fname):
        '''
        Checks if the given list of paths is safe
        '''
        for filename in fname:
            idx_dd = filename.find("..")
            if idx_dd != -1:
                return False
        return True
    

    def index(self):
        """
        demo presentation and input menu
        """
        # read the input index as a dict
        inputd = config.file_dict(self.input_dir)
        tn_size = int(cherrypy.config.get('input.thumbnail.size', '192'))
        # TODO: build via list-comprehension
        for (input_id, input_info) in inputd.items():
            # convert the files to a list of file names
            # by splitting at blank characters
            # and generate thumbnails and thumbnail urls
            fname = input_info['files'].split()

            if not self.valid_paths(fname):
                self.log("Invalid path in demo %s: %s" % ((self.title, str(fname))))
                inputd[input_id]['tn_url'] = []
                inputd[input_id]['url'] = []
                continue

             # this generates thumbnails even if the files are in a
             # subdirectory of input
            inputd[input_id]['tn_url'] = [os.path.join(self.input_url, \
                                          os.path.dirname(f), \
                                          os.path.basename(thumbnail(\
                                            self.input_dir + f, (tn_size, \
                                                                 tn_size)))) \
                                           for f in fname]

            inputd[input_id]['url'] = [os.path.join(self.input_url, \
                                       os.path.dirname(f), \
                                       os.path.basename(f)) \
                                           for f in fname]

        return self.tmpl_out("input.html",
                              inputd=inputd)

    #
    # INPUT HANDLING TOOLS
    #

    def save_image(self, im, fullpath):
        '''
        Save image object given full path
        '''
        im.save(fullpath)


    def convert_and_resize(self, im):
        '''
        Convert and resize an image object
        '''
        im.convert(self.input_dtype)

        # check max size
        resize = self.input_max_pixels and prod(im.size) > self.input_max_pixels
        
        if resize:
            self.log("input resize")
            im.resize(self.input_max_pixels)




    def process_input(self):
        """
        pre-process the input data
        """
        msg = None
        for i in range(self.input_nb):
            # open the file as an image
            try:
                im = image(self.work_dir + 'input_%i' % i)
            except IOError:
                raise cherrypy.HTTPError(400, # Bad Request
                                         "Bad input file")


            threads = []

            # convert to the expected input format
            im_converted = im.clone()
            threads.append(threading.Thread(target=self.convert_and_resize, args = (im_converted, )))

            # Save the original file as PNG
            #
            # Do a check before security attempting copy.
            # If the check fails, do a save instead
            if im.im.format != "PNG" or \
                  im.size[0] > 20000 or \
                  im.size[1] > 20000 or \
                  len(im.im.getbands()) > 4:
                # Save as PNG (slow)
                threads.append(threading.Thread(target=self.save_image,
                               args = (im, self.work_dir + 'input_%i.orig.png' % i)))
            else:
                # Copy file (fast)
                shutil.copy(self.work_dir + 'input_%i' % i,
                            self.work_dir + 'input_%i.orig.png' % i)
                
         

            # Execute threads and wait for them
            for t in threads:
                t.start()
            for t in threads:
                t.join()


            threads = []
            # save a working copy:
            if self.input_ext != ".png":
                # Problem with PIL or our image class: this call seems to be
                # problematic when saving PGM files. Not reentrant?? In any
                # case, avoid calling it from a thread.
                #threads.append(threading.Thread(target=self.save_image,
                #               args = (im_converted, self.work_dir + 'input_%i' % i + self.input_ext)))
                self.save_image(im_converted, self.work_dir + 'input_%i' % i + self.input_ext)

            # save a web viewable copy
            threads.append(threading.Thread(target=self.save_image,
                           args = (im_converted, self.work_dir + 'input_%i.png' % i)))

            # Execute threads and wait for them
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # delete the original
            os.unlink(self.work_dir + 'input_%i' % i)

            if im.size != im_converted.size:
                msg = "The image has been resized for a reduced computation time."
        return msg


    def clone_input(self):
        """
        clone the input for a re-run of the algo
        """
        self.log("cloning input from %s" % self.key)
        # get a new key
        old_work_dir = self.work_dir
        old_cfg_meta = self.cfg['meta']
        self.new_key()
        self.init_cfg()
        # copy the input files
        fnames = ['input_%i' % i + self.input_ext
                  for i in range(self.input_nb)]
        fnames += ['input_%i.png' % i
                   for i in range(self.input_nb)]
        fnames += ['input_%i.orig.png' %i
                   for i in range(self.input_nb)]
        for fname in fnames:
            shutil.copy(old_work_dir + fname,
                        self.work_dir + fname)
        # copy cfg
        self.cfg['meta'].update(old_cfg_meta)
        self.cfg.save()
        return

    #
    # INPUT STEP
    #

    def input_select_callback(self, fnames):
        '''
        Callback for the users to give the opportunity
        to process non-standard input
        '''
        pass # May be redefined by the subclass


    def input_select(self, **kwargs):
        """
        use the selected available input images
        """

        # When we arrive here, self.key should be empty.
        # If not, it means that another execution is concurrent.
        # In that case, we need to clone the app object
        key_is_empty = (self.key == "")
        if key_is_empty:
            self2 = base_app(self.base_dir)
            self2.__class__ = self.__class__
            self2.__dict__.update(self.__dict__)
        else:
            self2 = self

        self2.new_key()
        self2.init_cfg()

        # Add to app object pool
        if key_is_empty:
            pool = AppPool.get_instance() # Singleton pattern
            pool.add_app(self2.key, self2)

        # kwargs contains input_id.x and input_id.y
        input_id = kwargs.keys()[0].split('.')[0]
        assert input_id == kwargs.keys()[1].split('.')[0]
        # get the images
        input_dict = config.file_dict(self2.input_dir)
        fnames = input_dict[input_id]['files'].split()
        for i in range(len(fnames)):
            shutil.copy(self2.input_dir + fnames[i],
                        self2.work_dir + 'input_%i' % i)
        msg = self2.process_input()
        self2.log("input selected : %s" % input_id)
        self2.cfg['meta']['original'] = False
        self2.cfg.save()

        # Let users copy non-standard input into the work dir
        self2.input_select_callback(fnames)

        # jump to the params page
        return self2.params(msg=msg, key=self2.key)


    def input_upload(self, **kwargs):
        """
        use the uploaded input images
        """
        self.new_key()
        self.init_cfg()
        for i in range(self.input_nb):
            file_up = kwargs['file_%i' % i]
            file_save = file(self.work_dir + 'input_%i' % i, 'wb')
            if '' == file_up.filename:
                # missing file
                raise cherrypy.HTTPError(400, # Bad Request
                                         "Missing input file")
            size = 0
            while True:
                # TODO larger data size
                data = file_up.file.read(128)
                if not data:
                    break
                size += len(data)
                if size > self.input_max_weight:
                    # file too heavy
                    raise cherrypy.HTTPError(400, # Bad Request
                                             "File too large, " +
                                             "resize or use better compression")
                file_save.write(data)
            file_save.close()
        msg = self.process_input()
        self.log("input uploaded")
        self.cfg['meta']['original'] = True
        self.cfg.save()
        # jump to the params page
        return self.params(msg=msg, key=self.key)

    #
    # ERROR HANDLING
    #

    def error(self, errcode=None, errmsg=''):
        """
        signal an error
        """
        msgd = {'badparams' : 'Error: bad parameters. ',
                'timeout' : 'Error: execution timeout. '
                + 'The algorithm took more than %i seconds ' % self.timeout
                + 'and had to be interrupted. ',
                'returncode' : 'Error: execution failed. '}
        msg = msgd.get(errcode, 'Error: an unknown error occured. ') + errmsg

        # Extract stack calls to print them in the error template
        # In case of a timeout, don't print the traceback
        tb = traceback.extract_stack() if errcode != "timeout" else None
        return self.tmpl_out("error.html", msg=msg, traceback=tb)

    #
    # PARAMETER HANDLING
    #

    @init_app
    def params(self, newrun=False, msg=None):
        """
        configure the algo execution
        """
        if newrun:
            self.clone_input()
        return self.tmpl_out("params.html", msg=msg,
                             input=['input_%i.png' % i
                                      for i in range(self.input_nb)])

    #
    # EXECUTION AND RESULTS
    #

    @init_app
    def wait(self, **kwargs):
        """
        params handling and run redirection
        SHOULD be defined in the derived classes, to check the parameters
        """
        # pylint compliance (kwargs *is* used in derived classes)
        kwargs = kwargs
        # TODO check_params as a hook
        # use http meta refresh (display the page content meanwhile)
        http.refresh(self.base_url + 'run?key=%s' % self.key)
        return self.tmpl_out("wait.html",
                             input=['input_%i.png' % i
                                    for i in range(self.input_nb)])

    @init_app
    def run(self, **kwargs):
        """
        algo execution and redirection to result
        SHOULD be defined in the derived classes, to check the parameters
        """
        # pylint compliance (kwargs *is* used in derived classes)
        kwargs = kwargs
        # run the algo
        # TODO ensure only running once
        self.run_algo({})
        # redirect to the result page
        # use http 303 for transparent non-permanent redirection
        http.redir_303(self.base_url + 'result?key=%s' % self.key)
        return self.tmpl_out("run.html")

    def run_algo(self, params):
        """
        the core algo runner
        * could also be called by a batch processor
        * MUST be defined by the derived classes
        """
        pass

    @init_app
    def result(self):
        """
        display the algo results
        SHOULD be defined in the derived classes, to check the parameters
        """
        return self.tmpl_out("result.html",
                             input=['input_%i.png' % i
                                    for i in range(self.input_nb)],
                             output=['output.png'])

    def select_subimage(self, x0, y0, x1, y1):
        """
        cut subimage from original image
        """
        # draw selected rectangle on the image
        imgS = image(self.work_dir + 'input_0.png')
        imgS.draw_line([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)],
                       color="red")
        imgS.draw_line([(x0+1, y0+1), (x1-1, y0+1), (x1-1, y1-1),
                        (x0+1, y1-1), (x0+1, y0+1)], color="white")
        imgS.save(self.work_dir + 'input_0s.png')
        # crop the image
        # try cropping from the original input image
        # (if different from input_1)
        im0 = image(self.work_dir + 'input_0.orig.png')
        dx0 = im0.size[0]
        img = image(self.work_dir + 'input_0.png')
        dx = img.size[0]
        if dx != dx0:
            z = float(dx0)/float(dx)
            im0.crop((int(x0*z), int(y0*z), int(x1*z), int(y1*z)))
            # resize if cropped image is too big
            if (self.input_max_pixels
                and prod(im0.size) > self.input_max_pixels):
                im0.resize(self.input_max_pixels, method="antialias")
            img = im0
        else:
            img.crop((x0, y0, x1, y1))
        # save result
        img.save(self.work_dir + 'input_0.sel.png')
        return


    @cherrypy.expose
    @init_app
    def rectangle(self, action=None, x=None, y=None, x0=None, y0=None, \
                  *args, **kwargs):
        """
        params handling
        """
        if action == 'run':
            for key in kwargs:
                self.cfg['param'][key] = kwargs[key]
            self.cfg.save()
 
            if x != None:
                 #save parameters
                 try:
                     for key in kwargs:
                         self.cfg['param'][key] = kwargs[key]
                     self.cfg['param']['x0'] = x0
                     self.cfg['param']['y0'] = y0
                     self.cfg['param']['x1'] = x
                     self.cfg['param']['y1'] = y
                     self.cfg.save()
                 except ValueError:
                     return self.error(errcode='badparams',
                                       errmsg="Incorrect parameters.")

            # use the whole image if no subimage is available
            try:
                img = image(self.work_dir + 'input_0.sel.png')
            except IOError:
                img = image(self.work_dir + 'input_0.png')
                img.save(self.work_dir + 'input_0.sel.png')

            # go to the wait page, with the key
            http.redir_303(self.base_url + "wait?key=%s" % ((self.key)))
            return
        else:
            # use a part of the image
            if x0 == None:
                # first corner selection
                x = int(x)
                y = int(y)
                # draw a cross at the first corner
                img = image(self.work_dir + 'input_0.png')
                img.draw_cross((x, y), size=4, color="white")
                img.draw_cross((x, y), size=2, color="red")
                img.save(self.work_dir + 'input.png')
                return self.tmpl_out("params.html", x0=x, y0=y, **kwargs)
            else:
                # second corner selection
                x0 = int(x0)
                y0 = int(y0)
                x1 = int(x)
                y1 = int(y)
                # reorder the corners
                (x0, x1) = (min(x0, x1), max(x0, x1))
                (y0, y1) = (min(y0, y1), max(y0, y1))
                assert (x1 - x0) > 0
                assert (y1 - y0) > 0
                #save parameters
                try:
                    for key in kwargs:
                        self.cfg['param'][key] = kwargs[key]
                    self.cfg['param']['x0'] = x0
                    self.cfg['param']['y0'] = y0
                    self.cfg['param']['x1'] = x
                    self.cfg['param']['y1'] = y
                    self.cfg.save()
                except ValueError:
                    return self.error(errcode='badparams',
                                      errmsg="Incorrect parameters.")
                #select subimage
                self.select_subimage(x0, y0, x1, y1)
                # go to the wait page, with the key
                http.redir_303(self.base_url + "wait?key=%s" % ((self.key)))
            return

    @cherrypy.expose
    @init_app
    def wait(self):
        """
        run redirection
        """
        http.refresh(self.base_url + 'run?key=%s' % self.key)
        return self.tmpl_out("wait.html")


    #
    # ARCHIVE
    #

    def remove_from_archive(self, deleteThisKey=None):
        '''
        Removes a key from the archive
        '''
        # ATTEND TO DELETE COMMAND
        # make sure the other key is not set
        key = None

        # make sure that the target directory is inside the archive
        # just to avoid any .. path to be erased
        entrydir = os.path.abspath(os.path.join(self.archive_dir, \
                                   archive.key2url(deleteThisKey)))
        # these two strings must be the same
        ard1 = os.path.abspath(self.archive_dir)
        ard2 = os.path.commonprefix((ard1, entrydir))

        # proceed to delete the entry then continue as always
        # the bucket directory must exist and must be a subdir of archive
        if ard1 == ard2 and ard1 != entrydir and os.path.isdir(entrydir):
            print "REMOVING ARCHIVE ENTRY: " + entrydir
            # REMOVE THE DIRECTORY
            rmtree(entrydir)

            # REMOVE THE ENTRY FROM THE DATABASE BACKEND
            archive.index_delete(self.archive_index, deleteThisKey)
        else:
            print "IGNORING BOGUS ENTRY REMOVAL: " + entrydir

        # ATTEND TO REBUILD-INDEX COMMAND
        archive.index_rebuild(self.archive_index, self.archive_dir)


    @cherrypy.expose
    def archive(self, page=-1, key=None, deleteThisKey=None, adminmode=False):
        """
        lists the archive content
        """
        if deleteThisKey and deleteThisKey != '':
            self.remove_from_archive(deleteThisKey)

        if key:
            # select one archive
            buckets = [{'url' : self.archive_url + archive.key2url(key),
                        'files' : files, 'meta' : meta, 'info' : info}
                       for (key, (files, meta, info))
                       in archive.index_read(self.archive_index,
                                             key=key,
                                             path=self.archive_dir)]

            # Check if the key is deletable for this user
            ukm = archive.UserKeysManager()
            deletable = ukm.key_belongs_to_user(key)

            return self.tmpl_out("archive_details.html",
                                 bucket=buckets[0],
                                 deletable=deletable,
                                 adminmode=adminmode)
        else:
            # select a page from the archive index
            nbtotal = archive.index_count(self.archive_index,
                                           path=self.archive_dir,
                                           public=True)
            if nbtotal:
                firstdate = archive.index_first_date(self.archive_index,
                                                     path=self.archive_dir)
            else:
                firstdate = 'never'
            limit = 20
            nbpage = int(math.ceil(nbtotal / float(limit)))
            page = int(page)
            if page == -1:
                page = nbpage - 1
            offset = limit * page

            buckets = [{'url' : self.archive_url + archive.key2url(key),
                        'files' : files, 'meta' : meta, 'info' : info}
                       for (key, (files, meta, info))
                       in archive.index_read(self.archive_index,
                                             limit=limit, offset=offset,
                                             public=True,
                                             path=self.archive_dir)]
            return self.tmpl_out("archive_index.html",
                                 bucket_list=buckets,
                                 page=page, nbpage=nbpage,
                                 nbtotal=nbtotal,
                                 firstdate=firstdate,
                                 adminmode=adminmode)

    #
    # ARCHIVE ADMIN
    #

    @cherrypy.expose
    def archive_admin(self, page=-1, key=None, deleteThisKey=None, \
                      rebuildIndexNow=None):
        """
        lists the archive content
        """
        if deleteThisKey and deleteThisKey != '':
            self.remove_from_archive(deleteThisKey)

        # USUAL ARCHIVE BEHAVIOR
        return self.archive(page=page, key=key, adminmode=True)
