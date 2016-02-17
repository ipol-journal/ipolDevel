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
import urllib
import requests
from lib.misc import app_expose, ctime

from mako.exceptions import RichTraceback
from . import http
from . import config
from . import archive
from .empty_app import empty_app
from .image import thumbnail, image
from .misc import prod
from shutil import rmtree

import json
# json schema validation
from jsonschema import validate
from jsonschema import Draft4Validator
from jsonschema import ValidationError
import urllib2

import build_demo_base

import  run_demo_base
from    run_demo_base import RunDemoBase
from    run_demo_base import TimeoutError
from    timeit import default_timer as timer
import  glob
from PIL import Image,ImageDraw

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
            self2 = base_app(self.base_dir, self.demo_description)
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

    #---------------------------------------------------------------------------
    def __init__(self, base_dir, ddl_dict):
        """
        app setup
        base_dir is supposed to be received from a subclass
        """
        # setup the parent class
        empty_app.__init__(self, base_dir)
        
        self.proxy_server = cherrypy.config['demo.proxy_server']
        
        self.demo_description  = ddl_dict
        #self.read_demo_description()
        self.init_parameters()
        
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
        
        # expose methods
        app_expose(base_app.index)
        app_expose(base_app.input_upload)
        # params() is modified from the template
        app_expose(base_app.params)
        

    #---------------------------------------------------------------------------
    def CheckDemoDescription(self,desc):
        """
            Check the demo description based on the json schema
        """
        CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
        ddl_schema = json.load(open(CURRENT_DIR+"/../modules/config_common/ddl_schema.json"))
        #print "****"
        #print ddl_schema
        #print "****"
        try:
            validate(desc,ddl_schema)
        except ValidationError as e:
            print e.message
            return False
        return True

    #---------------------------------------------------------------------------
    def reload_demo_description(self):
        # we need:
        # demo_id
        # internalid for demo
        # json package
        # CheckDemoDescription method
        
        print "---- Reload json schema for demo {0:10}".format(self.id)
        
        
        #
        try:
            # find internal id: demo with the same title
            # using demoinfo module to create demo_dict ...
            # use proxy
            proxy_server = cherrypy.config['demo.proxy_server']
            get_demolist_url = proxy_server+'/?module=demoinfo&service=demo_list'
            res = urllib2.urlopen(get_demolist_url)
            resjson = json.loads(res.read())
            internalid=-1
            if resjson['status']=="OK":
                for d in resjson['demo_list']:
                    id_str = str(d['editorsdemoid'])
                    if id_str==str(self.id):
                        internalid=d['id']
            if internalid==-1:
                raise cherrypy.HTTPError(400, "Failed to find a demo with the same id")
            else:
                # read demo descriptions
                res1 = urllib2.urlopen(proxy_server +\
                        "/?module=demoinfo&service=read_last_demodescription_from_demo&demo_id="+\
                        str(internalid)+"&returnjsons=True" )
                res1json = json.loads(res1.read())
                if res1json['status'] == 'OK':
                    ddl_info = res1json['last_demodescription']
                    if ddl_info:
                        ddl = ddl_info['json']
                        demo_description = json.loads(ddl)
                        demo_description = json.loads(demo_description)
                        if self.CheckDemoDescription(demo_description):
                            print " --> OK "
                            self.demo_description = demo_description
        except ValueError as e:
            print "EXCEPTION: ", e
            cherrypy.log("failed to reload JSON demo description")


    #---------------------------------------------------------------------------
    def init_parameters(self):
        """
        Initialization of general demo parameters
        """
        
        # default class attributes
        # to be modified in subclasses
        self.title = "base demo"
        self.timeout = 60 # subprocess execution timeout
        self.is_test = True
        self.show_results_on_error = False
        
        #-----
        general_params = self.demo_description["general"]
        self.title            = general_params["demo_title"]
        # switch to False for deployment
        self.is_test          = general_params["is_test"]
        self.xlink_article    = general_params["xlink_article"]
        if 'show_results_on_error' in general_params:
          self.show_results_on_error = general_params['show_results_on_error']
        self.nb_inputs        = len(self.demo_description['inputs'])

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

    #---------------------------------------------------------------------------
    def valid_paths(self, fname):
        '''
        Checks if the given list of paths is safe
        '''
        for filename in fname:
            idx_dd = filename.find("..")
            if idx_dd != -1:
                return False
        return True
    

    #---------------------------------------------------------------------------
    @cherrypy.expose
    def index(self):
        """
        demo presentation and input menu
        """
        
        #if no input go directly to parameters
        if self.nb_inputs==0:
            # jump to the params page
            return self.params()
        
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

    #---------------------------------------------------------------------------
    def save_image(self, im, fullpath):
        '''
        Save image object given full path
        '''
        im.save(fullpath)

    #---------------------------------------------------------------------------
    def convert_and_resize(self, im, input_info):
        '''
        Convert and resize an image object
        '''
        im.convert(input_info['dtype'])
        # check max size
        max_pixels = eval(str(input_info['max_pixels']))
        resize = prod(im.size) > max_pixels
        if resize:
            self.log("input resize")
            im.resize(max_pixels)

    #---------------------------------------------------------------------------
    def process_inputs(self):
        """
        pre-process the input data
        we suppose that config has been initialized, and save the dimensions
        of each converted image in self.cfg['meta']['input$i_size_{x,y}']
        """
        print "process_inputs()"
        start = timer()
        msg = None
        self.max_width = 0
        self.max_height = 0
        inputs_desc = self.demo_description['inputs']
        
        for i in range(self.nb_inputs):
          # check the input type
          input_desc = inputs_desc[i]
          # find files starting with input_%i
          input_files = glob.glob(self.work_dir + 'input_%i' % i+'.*')
          
          if input_desc['type']=='image':
            # we deal with an image, go on ...
            print "Processing input ",i
            if len(input_files)!=1:
              # problem here
              raise cherrypy.HTTPError(400, "Wrong number of inputs for an image")
            else:
              # open the file as an image
              try:
                  im = image(input_files[0])
              except IOError:
                print "failed to read image " + input_files[0]
                raise cherrypy.HTTPError(400, # Bad Request
                                         "Bad input file")

            
            # why use threads here? is it really better ???
            threads = []

            #-----------------------------
            # Save the original file as PNG
            # todo: why save original image as PNG??
            #
            # Do a check before security attempting copy.
            # If the check fails, do a save instead
            if  im.im.format != "PNG" or \
                im.size[0] > 20000 or im.size[1] > 20000 or \
                len(im.im.getbands()) > 4:
              # Save as PNG (slow)
              threads.append(threading.Thread(target=self.save_image,
                              args = (im, self.work_dir + 'input_%i.orig.png' % i)))
              # delete the original
              os.remove(input_files[0])
            else:
              # Copy file (fast)
              shutil.move(input_files[0],
                          self.work_dir + 'input_%i.orig.png' % i)

            
            #-----------------------------
            # convert to the expected input format: TODO: do it if needed ...
            im_converted = im.clone()
            print "input description: ", input_desc
            threads.append(threading.Thread(target=self.convert_and_resize, 
                                            args = (im_converted,input_desc) ))


            # Execute threads and wait for them
            for t in threads:
                t.start()
            for t in threads:
                t.join()


            ext = input_desc['ext']
            # why saving a copy of the converted image in non-png format ?
            ## save a working copy:
            #if ext != ".png":
                ## Problem with PIL or our image class: this call seems to be
                ## problematic when saving PGM files. Not reentrant?? In any
                ## case, avoid calling it from a thread.
                ##threads.append(threading.Thread(target=self.save_image,
                ##               args = (im_converted, self.work_dir + 'input_%i' % i + ext))
                #self.save_image(im_converted, self.work_dir + 'input_%i' % i + ext)

            # save a web viewable copy
            self.save_image(im_converted, self.work_dir + 'input_%i.png' % i)

            if im.size != im_converted.size:
                msg = "The image has been resized for a reduced computation time."
                print msg,": ", im.size, "-->", im_converted.size
            self.max_width  = max(self.max_width,im_converted.size[0])
            self.max_height = max(self.max_height,im_converted.size[1])
            self.cfg['meta']['input%i_size_x'%i] = im_converted.size[0]
            self.cfg['meta']['input%i_size_y'%i] = im_converted.size[1]
          # end if type is image
          else:
            # check if we have a representing image to display
            if len(input_files)>1:
              # the number of input files should be 2...
              # for the moment, only check for png file
              png_file = self.work_dir + 'input_%i.png' % i
              if png_file in input_files:
                # save in configuration the information to allow its display
                self.cfg['meta']['input%i_has_image'%i] = True
        # end for i in range(nb_inputs)
        end=timer()
        print "process_inputs() took: ", (end-start), " seconds"
        
        return msg


    #---------------------------------------------------------------------------
    def clone_input(self):
        """
        clone the input for a re-run of the algo
        """
        self.log("cloning input from %s" % self.key)
        # get a new key
        old_work_dir   = self.work_dir
        old_cfg_meta   = self.cfg['meta']
        old_cfg_params = self.cfg['param']
        self.new_key()
        self.init_cfg()
        # copy the input files
        fnames = ['input_%i' % i + self.demo_description['inputs'][i]['ext']
                  for i in range(self.nb_inputs)]
        fnames += ['input_%i.png' % i
                   for i in range(self.nb_inputs)]
        fnames += ['input_%i.orig.png' %i
                   for i in range(self.nb_inputs)]
        for fname in fnames:
          try:
            shutil.copy(old_work_dir + fname,
                        self.work_dir + fname)
          except:
            print "clone_input, file not found:", fname
        # copy cfg
        self.cfg['meta'] .update(old_cfg_meta)
        self.cfg['param'].update(old_cfg_params)
        self.cfg.save()
        return

    #
    # INPUT STEP
    #

    #---------------------------------------------------------------------------
    def input_select_callback(self, fnames):
        '''
        Callback for the users to give the opportunity
        to process non-standard input
        '''
        pass # May be redefined by the subclass

    #---------------------------------------------------------------------------
    @cherrypy.expose
    def input_select_angular(self, **kwargs):
        """
        use the selected available input images
        """
        
        # reload demo description
        self.reload_demo_description()

        # When we arrive here, self.key should be empty.
        # If not, it means that the execution belongs to another thread
        # and therefore we need to reuse the app object
        key_is_empty = (self.key == "")
        if key_is_empty:
            # New execution: create new app object
            self2 = base_app(self.base_dir, self.demo_description)
            self2.__class__ = self.__class__
            self2.__dict__.update(self.__dict__)
        else:
            # Already known execution
            self2 = self

        self2.new_key()
        self2.init_cfg()

        # Add app to object pool
        if key_is_empty:
            pool = AppPool.get_instance() # Singleton pattern
            pool.add_app(self2.key, self2)

        print "kwargs", kwargs
        blob_url = kwargs.pop('url',None)
        print "blob_url", blob_url
        print "kwargs",kwargs
        
        print "input_select_angular :", kwargs.keys()
        # copy to work_dir
        blobfile = urllib.URLopener()
        for inputinfo in kwargs.keys():
          # 1. retreive index
          posstart=inputinfo.index(':')
          idx = int(inputinfo[:posstart])
          print self.demo_description['inputs'][idx]
          inputinfo = inputinfo[posstart+1:]
          if ',' in inputinfo:
            # what should we do ? we should have two files here...
            inputfiles = inputinfo.split(',')
          else:
            inputfiles = [ inputinfo ]
          # extract input files to work dir as input_%i.ext
          print "inputfiles:",inputfiles
          for inputfile in inputfiles:
            print "inputfile:",inputfile
            basename  = inputfile[:inputfile.index('.')]
            ext       = inputfile[inputfile.index('.'):]
            blob_link =  blob_url +'/'+ basename + ext
            print "blob_link = ", blob_link
            blobfile.retrieve(blob_link, 
                              self2.work_dir + 'input_{0}{1}'.format(idx,ext))
        
        msg = self2.process_inputs()
        #self2.log("input selected : %s" % kwargs.keys()[0])
        self2.cfg['meta']['original'] = False
        self2.cfg['meta']['max_width']  = self2.max_width;
        self2.cfg['meta']['max_height'] = self2.max_height;
        self2.cfg.save()

        # Let users copy non-standard input into the work dir
        # don't have fnames here
        #self2.input_select_callback(fnames)

        # jump to the params page
        return self2.params(msg=msg, key=self2.key)

    #---------------------------------------------------------------------------
    def input_upload(self, **kwargs):
        """
        use the uploaded input files
        """
        self.new_key()
        self.init_cfg()
        inputs_desc = self.demo_description['inputs']
        
        for i in range(self.nb_inputs):
          file_up = kwargs['file_%i' % i]
          
          if file_up.filename == '':
            if  not('required' in inputs_desc[i].keys()) or \
                inputs_desc[i]['required']:
              # missing file
              raise cherrypy.HTTPError(400, # Bad Request
                                        "Missing input file number {0}".format(i))
            else:
                # skip this input
                continue

          # suppose than the file is in the correct format for its extension
          ext = inputs_desc[i]['ext']
          file_save = file(self.work_dir + 'input_%i' % i + ext, 'wb')

          size = 0
          while True:
            # TODO larger data size
            data = file_up.file.read(128)
            if not data:
                break
            size += len(data)
            if 'max_weight' in inputs_desc[i] and size > eval(str(inputs_desc[i]['max_weight'])):
                # file too heavy
                raise cherrypy.HTTPError(400, # Bad Request
                                          "File too large, " +
                                          "resize or use better compression")
            file_save.write(data)
          file_save.close()
        msg = self.process_inputs()
        self.log("input uploaded")
        self.cfg['meta']['original'] = True
        self.cfg['meta']['max_width']  = self.max_width;
        self.cfg['meta']['max_height'] = self.max_height;
        self.cfg.save()
        # jump to the params page
        return self.params(msg=msg, key=self.key)

    #---------------------------------------------------------------------------
    #
    # ERROR HANDLING
    #
    def error(self, errcode=None, errmsg=''):
        """
        signal an error
        """
        msgd = {'badparams'  : 'Error: bad parameters. ',
                'timeout'    : 'Error: execution timeout. ' +
                               'The algorithm took more than %i seconds ' % self.timeout +
                               'and had to be interrupted. ',
                'returncode' : 'Error: execution failed. ',
                'runtime'    : 'RuntimeError. ' }
        if errcode in msgd.keys():
          msg = msgd[errcode] + errmsg
        else:
          msg = errmsg
        if msg=='':
          msg = 'Error: an unknown error occured. '

        # Extract stack calls to print them in the error template
        # In case of a timeout, don't print the traceback
        tb = traceback.extract_stack() if errcode != "timeout" else None
        return self.tmpl_out("error.html", msg=msg, traceback=tb)

    #===========================================================================
    # Inpainting related methods
    #
    
    #---------------------------------------------------------------------------
    def inpainting_init(self):
        self.inpainting_default_param = {
                'pensize': 5,
                'pencolor':'yellow'}
        self.inpainting_pencolors = {'yellow'   : [255, 255, 0], 
                'blue'          : [0, 0, 255], 
                'black'         : [0, 0, 0]}
        # Generate a new timestamp
        self.inpainting_timestamp = int(100*time.time())

    #---------------------------------------------------------------------------
    def inpainting_readcommandlist(self):
        """
        Read the drawing commandlist from maskcomands.txt
        """
                
        try:
            ifile = file(self.work_dir + 'maskcommands.txt', 'r')
            commandlist = [tuple([int(t) for t in line.split(' ')]) \
                for line in ifile.readlines()]
            ifile.close()
        except IOError:
            commandlist = []
        
        return commandlist
    
    
    #---------------------------------------------------------------------------
    def print_palette(self,palette):
        """
        print palette information to standard output
        """
        import array
        print "mode", palette.mode
        palarray = array.array('B',palette.palette)
        size = len(palette.mode)
        val = range(size)
        for i in range(256):
            for j in range(i*size, (i+1)*size):
                try:
                    val[j-i*size] =  palarray[j]
                except IndexError:
                    val[j-i*size] = 0
            if (i==0) or (i==255):
                print "%d" %i,  val
            else:
                if val!=prev_val:
                    print "%d" %i,  val
            prev_val = val[:]
        
    #---------------------------------------------------------------------------
    def inpainting_rendermask(self):
        """
        Render the drawing commandlist into the mask 
        """        
        
        commandlist = self.inpainting_readcommandlist()
        size = image(self.work_dir + 'input_0.png').size
        self.cfg['param']['viewbox_width'] = size[0]
        self.cfg['param']['viewbox_height'] = size[1]
        
        mask = Image.new('P', size, 0)   # Create a grayscale image
        draw = ImageDraw.Draw(mask)
    
        for (t, x, y) in commandlist:
            draw.ellipse((x - t, y - t, x + t + 1, y + t + 1), fill=255)
        
        mask.putpalette([128, 128, 128] + [0, 0, 0] * 254
            + self.inpainting_pencolors[self.cfg['param']['pencolor']])
        self.print_palette(mask.palette)
        
        mask.save(self.work_dir + 'mask.png', transparency=0)
        
    
    #---------------------------------------------------------------------------
    @cherrypy.expose
    @init_app
    def inpainting_editmask(self, **kwargs):
        """
        Edit the inpainting mask
        avoid using gif since the palette is then compressed,
        use png format for the mask
        """
        self.inpainting_init()
        
        generate_options = {
            'random text' : 'rl',
            'random walk' : 'rw',
            'random Bernoulli' : 'bernoulli'
            }
        commandlist = self.inpainting_readcommandlist()
        
        pencolors = set(['pencolor_yellow','pencolor_blue','pencolor_black'])
        pencolor_arg = pencolors.intersection(kwargs)
        
        if 'action' in kwargs:
            if kwargs['action'] == 'undo':
                if commandlist:
                    commandlist.pop()
            elif kwargs['action'] == 'clear':
                commandlist = []
            elif kwargs['action'] in generate_options.keys():
                self.wait_proc(self.run_proc(['random_mask', 
                    generate_options[kwargs['action']],
                    self.work_dir + 'input_0.png', 'mask.png'],
                    stdout=None, stderr=None), None)
                
                if os.path.isfile(self.work_dir + 'maskcommands.txt'):
                    os.remove(self.work_dir + 'maskcommands.txt')
                
                mask = Image.open(self.work_dir + 'mask.png')
                mask = mask.convert('L')
                mask = mask.convert('P')
                mask.putpalette([128, 128, 128] + [0, 0, 0] * 254 
                    + self.inpainting_pencolors[self.cfg['param']['pencolor']])
                mask.save(self.work_dir + 'mask.png', transparency=0)
                                
                return self.tmpl_out('params_angular.html')
        elif len(pencolor_arg)>0:
            color = pencolor_arg.pop()[9:]
            self.cfg['param']['pencolor'] = color
            mask = Image.open(self.work_dir + 'mask.png')
            mask.putpalette([128, 128, 128] + [0, 0, 0] * 254 
                            + self.inpainting_pencolors[color])
            mask.save(self.work_dir + 'mask.png', transparency=0)
            return self.tmpl_out('params_angular.html')
        else:
            commandlist.append( (int(kwargs['pensize']), \
                                int(kwargs['x']), int(kwargs['y'])))
        
        f = file(self.work_dir + 'maskcommands.txt', 'w')
        #f.write('This is a test\n')
        f.writelines('%i %i %i\n' % (t, x, y)  \
                    for (t, x, y) in commandlist )
        f.close()
        
        # Generate a new timestamp
        self.inpainting_timestamp = int(100*time.time())
                
        self.cfg['param']['pensize'] = int(kwargs['pensize'])
        # Set undefined parameters to default values
        self.cfg['param'] = dict(self.inpainting_default_param, **self.cfg['param'])
        
        self.inpainting_rendermask()
        return self.tmpl_out('params_angular.html')
    
    
    #
    #
    #===========================================================================

    #
    # PARAMETER HANDLING
    #

    @cherrypy.expose
    @init_app
    def params(self, newrun=False, msg=None, **kwargs):
        """
        configure the algo execution
        """

        # First check if input is OK
        if 'input_condition' in self.demo_description['general'].keys():
          condition = self.demo_description['general']['input_condition']
          # Get all image sizes
          for i in range(self.nb_inputs):
            if self.demo_description['inputs'][i]['type']=='image':
              exec("input{0}_size_x = self.cfg['meta']['input{0}_size_x']".format(i) )
              exec("input{0}_size_y = self.cfg['meta']['input{0}_size_y']".format(i) )
          try:
            inputs_ok = eval(condition[0])
            if not(inputs_ok):
              return self.error(condition[1],condition[2])
          except:
            print "Failed to evaluate input condition"
        else:
          print "no input condition"
        
        # check for inpainting option
        self.inpainting = \
            (   'inpainting' in self.demo_description['general'].keys() and \
                self.demo_description['general']['inpainting'])
        
        print "inpainting = ", self.inpainting
        
        if newrun:
            old_work_dir = self.work_dir
            self.clone_input()
            if self.inpainting:
                # Also need to clone maskcommands.txt to keep the mask
                if os.path.isfile(old_work_dir + 'maskcommands.txt'):
                    shutil.copy(old_work_dir  + 'maskcommands.txt',
                                self.work_dir + 'maskcommands.txt')
                
        if self.inpainting:
            self.inpainting_init()
            # Set undefined parameters to default values
            self.cfg['param'] = dict(self.inpainting_default_param, **self.cfg['param'])
            print "self.cfg['param']=",self.cfg['param']
            
            # Generate a new timestamp
            self.inpainting_timestamp = int(100*time.time())
            self.inpainting_rendermask()

        return self.tmpl_out("params_angular.html", msg=msg)

    #
    # EXECUTION AND RESULTS
    #

    @cherrypy.expose
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
                                    for i in range(self.nb_inputs)])

    #---------------------------------------------------------------------------
    def check_build(self):
        """
            rebuild demo from source code if required
        """
        
        # reload demo description
        self.reload_demo_description()
        demo_id   = self.id
        demo_path = self.base_dir
        print "---- check_build demo: {0:10}".format(demo_id),
        # we should have a dict or a list of dict
        if isinstance(self.demo_description['build'],dict):
            builds = [ self.demo_description['build'] ]
        else:
            builds = self.demo_description['build']
        first_build = True
        for build_params in builds:
            bd = build_demo_base.BuildDemoBase( demo_path)
            bd.set_params(build_params)
            cherrypy.log("building", context='SETUP/%s' % demo_id,
                        traceback=False)
            try:
                bd.make(first_build)
                first_build=False
            except Exception as e:
                print "Build failed with exception ",e
                cherrypy.log("build failed (see the build log)",
                                context='SETUP/%s' % demo_id,
                                traceback=False)
        print ""

    #---------------------------------------------------------------------------
    @cherrypy.expose
    @init_app
    def run(self, **kwargs):
      """
      algo execution and redirection to result
      """
      
      self.check_build()
      
      # run the algorithm
      try:
        run_time = time.time()
        self.cfg.save()
        self.run_algo()
        self.cfg.Reload()
        # re-read the config in case it changed during the execution
        self.cfg['info']['run_time'] = time.time() - run_time
        self.cfg['info']['status']   = 'success'
        self.cfg.save()
      except TimeoutError:
        return self.error(errcode='timeout') 
      except RuntimeError as e:
        print "self.show_results_on_error =", self.show_results_on_error
        if not(self.show_results_on_error):
          return self.error(errcode='runtime',errmsg=str(e))
        else:
          self.cfg['info']['run_time'] = time.time() - run_time
          self.cfg['info']['status']   = 'failure'
          self.cfg['info']['error']    = str(e)
          self.cfg.save()
          pass

      http.redir_303(self.base_url + 'result?key=%s' % self.key)

      # check if new config fields
      if 'config' in self.demo_description.keys():
        desc = self.demo_description['config']
        info_changed = False
        if 'info_from_file' in desc.keys():
          print desc['info_from_file']
          for info in desc['info_from_file']:
            print "*** ",info
            filename = desc['info_from_file'][info]
            try:
              f = open( os.path.join(self.work_dir,filename))
              file_lines = f.read().splitlines()
              # remove empty lines and replace new lines with ' | '
              new_string = " | ".join([ll.rstrip() for ll in file_lines if ll.strip()])
              self.cfg['info'][info] = new_string
              print "Added info ", info, " with value ", self.cfg['info'][info]
              info_changed = True
              f.close()
            except:
              print "failed to get info ",  info, " from file ", filename
        if info_changed:
          self.cfg.save()

      # archive (OLD CODE)
      #if self.nb_inputs==0:
      #    self.cfg['meta']['original'] = True
      #    self.cfg.save()
      #    
      #if (self.nb_inputs==0) or (self.cfg['meta']['original']):
      #  desc = self.demo_description['archive']
      #  ar = self.make_archive()
      #  if 'files' in desc.keys():
      #    for filename in desc['files']:
      #      ar.add_file(filename, info=desc['files'][filename])
      #  if 'compressed_files' in desc.keys():
      #    for filename in desc['compressed_files']:
      #      ar.add_file(filename, info=desc['compressed_files'][filename], 
      #                  compress=True)
      #    
      #  # let's add all the parameters
      #  if 'params' in desc.keys():
      #    for p in desc['params']:
      #      if p in self.cfg['param']:
      #        ar.add_info({ p: self.cfg['param'][p]})
      #    
      #  if 'info' in desc.keys():
      #    # save info
      #    for i in desc['info']:
      #      if i in self.cfg['info']:
      #        ar.add_info({ desc['info'][i] : self.cfg['info'][i]})
      #  ar.save()
      #return self.tmpl_out("run.html")
      # End archive (OLD CODE)
      
       #Files must be stored by the archive module
      if (self.nb_inputs==0) or (self.cfg['meta']['original']):
        
        desc = self.demo_description['archive']
        
        blobs = {}
        if 'files' in desc.keys():
          for filename in desc['files']:
            file_complete_route = os.path.join(self.work_dir, filename)
            if os.path.exists(file_complete_route):
               blobs[file_complete_route] = desc['files'][filename]
        
        if 'compressed_files' in desc.keys(): 
          for filename in desc['compressed_files']:
            file_complete_route = os.path.join(self.work_dir, filename)
            file_complete_route_compressed = file_complete_route + '.gz'
            if os.path.exists(file_complete_route):
               f_src = open(file_complete_route, 'rb')
               f_dst = gzip.open(file_complete_route_compressed, 'wb')
               f_dst.writelines(f_src)
               f_dst.close()
               f_src.close()
               blobs[file_complete_route_compressed] = desc['compressed_files'][filename]  
            
        # let's add all the parameters
        parameters = {}
        if 'params' in desc.keys():
          for p in desc['params']:
            if p in self.cfg['param']:
               parameters[p] = self.cfg['param'][p]

        # save info
        if 'info' in desc.keys():
          for i in desc['info']:
            if i in self.cfg['info']:
               parameters[desc['info'][i]] = self.cfg['info'][i]
        
        try:
            request = '?module=archive&service=add_experiment&demo_id=' + self.id
            call_service = urllib.urlopen(self.proxy_server + request + "&blobs=" + json.dumps(blobs) + "&parameters=" + json.dumps(parameters)).read()
        except Exception as ex:
            return self.error(errcode='modulefailure',
                             errmsg="The archive module has failed: " + str(ex))


      return self.tmpl_out("run.html")
    

    #---------------------------------------------------------------------------
    # Core algorithm runner
    #---------------------------------------------------------------------------
    def run_algo(self):
      """
      the core algo runner
      """
      
      # refresh demo description ??
      
      rd = run_demo_base.RunDemoBase(self.base_dir, self.work_dir)
      rd.set_logger(cherrypy.log)
      if 'demo.extra_path' in cherrypy.config:
        rd.set_extra_path(cherrypy.config['demo.extra_path'])
      rd.set_algo_params(self.cfg['param'])
      rd.set_algo_info  (self.cfg['info'])
      rd.set_algo_meta  (self.cfg['meta'])
      rd.set_MATLAB_path(self.get_MATLAB_path())
      rd.set_demo_id(self.id)
      rd.set_commands(self.demo_description['run'])
      rd.run_algo()
      # take into account possible changes in parameters
      self.cfg['param'] = rd.get_algo_params()
      self.cfg['info']  = rd.get_algo_info()
      self.cfg['meta']  = rd.get_algo_meta()
      print "self.cgf['param']=",self.cfg['param']
      return


    #---------------------------------------------------------------------------
    @cherrypy.expose
    @init_app
    def result(self):
        """
        display the algo results
        """
        return self.tmpl_out("result.html")

    #---------------------------------------------------------------------------
    def select_subimage(self, x0, y0, x1, y1):
        """
        cut subimage from original image
        """
        # draw selected rectangle on the image
        imgS        = image(self.work_dir + 'input_0.png')
        max_pixels  = eval(str(self.demo_description['inputs'][0]['max_pixels']))
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
            im0.crop((int(x0*z+0.5), int(y0*z+0.5), int(x1*z+0.5), int(y1*z+0.5)))
            # resize if cropped image is too big
            if max_pixels and prod(im0.size) > max_pixels:
                im0.resize(max_pixels, method="antialias")
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
        print "**kwargs = ", kwargs
        # if a key appears several times, join the strings ?
        # first empty dictionnary
        self.cfg['param'].clear()
        for key in kwargs:
            self.cfg['param'][key] = kwargs[key]

        if (self.nb_inputs>0)and(x != None):
          #save parameters
          try:
            # already done ...
            #for key in kwargs:
                #self.cfg['param'][key] = kwargs[key]
            self.cfg['param']['x0'] = x0
            self.cfg['param']['y0'] = y0
            self.cfg['param']['x1'] = x
            self.cfg['param']['y1'] = y
            self.cfg.save()
            # Create subimage
            self.select_subimage(int(x0), int(y0), int(x), int(y))
          except ValueError:
            return self.error(errcode='badparams',
                              errmsg="Incorrect parameters.")
        else:
          self.cfg.save()

        if self.nb_inputs>0:
            # use the whole image if no subimage is available
            try:
                img = image(self.work_dir + 'input_0.sel.png')
            except IOError:
                img = image(self.work_dir + 'input_0.png')
                img.save(self.work_dir + 'input_0.sel.png')

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
