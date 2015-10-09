#-------------------------------------------------------------------------------
"""
LSD IPOL demo app
Line Segment Detector
by Rafael Grompone von Gioi, Jeremie Jakubowicz,
   Jean-Michel Morel and Gregory Randall.
March 22, 2012
"""
#-------------------------------------------------------------------------------

from lib import base_app, build, http, image
from lib.misc import app_expose, ctime
from lib.base_app import init_app
import cherrypy
from cherrypy import TimeoutError
import os.path
import shutil
import time

#-------------------------------------------------------------------------------
# LSD IPOL demo main class.
#-------------------------------------------------------------------------------
class app(base_app):
    """LSD IPOL demo main class."""

    # IPOL demo system configuration
    title = "LSD: a Line Segment Detector"
    xlink_article = 'http://www.ipol.im/pub/art/2012/gjmr-lsd/'

    input_nb = 1          # number of input images
    input_max_pixels = 100000000  # max size (in pixels) of an input image
    input_max_weight = 3 * input_max_pixels  # max size (in bytes)
                                             # of an input file
    input_dtype = '1x8i'  # input image expected data type
    input_ext = '.pgm'    # input image expected extension (i.e. file format)
    is_test = False       # switch to False for deployment

    #---------------------------------------------------------------------------
    # Set up application.
    #---------------------------------------------------------------------------
    def __init__(self):
        """Set up application."""

        # setup the parent class
        base_dir = os.path.dirname(os.path.abspath(__file__))
        base_app.__init__(self, base_dir)

        # select the base_app steps to expose
        # index() is generic
        app_expose(base_app.index)
        app_expose(base_app.input_select)
        app_expose(base_app.input_upload)
        # params() is modified from the template
        app_expose(base_app.params)
        # run() and result() must be defined here

    #---------------------------------------------------------------------------
    # Run the algorithm.
    #---------------------------------------------------------------------------
    @cherrypy.expose
    @init_app
    def run(self):
        """Run the algorithm."""

        try:
            run_time = time.time()
            self.run_algo()
            self.cfg['info']['run_time'] = time.time() - run_time
            num_lines = sum(1 for line in open(self.work_dir + 'output.txt'))
            self.cfg['info']['num_detections'] = num_lines
            self.cfg.save()
        except TimeoutError:
            return self.error(errcode='timeout',
                              errmsg="Try again with simpler images.")
        except RuntimeError:
            return self.error(errcode='runtime',
                              errmsg="Something went wrong with the program.")
        http.redir_303(self.base_url + 'result?key=%s' % self.key)

        # archive
        if self.cfg['meta']['original']:
            ar = self.make_archive()
            ar.add_file("input_0.orig.png","uploaded_image.png")
            ar.add_file("input_0.png","uploaded_image_gray.png")
            ar.add_file("input_0.sel.png","lsd_input.png")
            ar.add_file("output.txt")
            ar.add_file("output.eps")
            ar.add_file("output.svg")
            ar.add_file("output.png")
            ar.add_file("output-inv.png")
            try:
                version_file = open(self.work_dir + "version.txt", "w")
                p = self.run_proc(["lsd", "--version"], stdout=version_file)
                self.wait_proc(p)
                version_file.close()
                version_file = open(self.work_dir + "version.txt", "r")
                version_info = version_file.readline()
                version_file.close()
            except Exception:
                version_info = "unknown"
            ar.add_info({"LSD version" : version_info})
            ar.add_info({"run time (s)" : self.cfg['info']['run_time']})
            ar.save()

        return self.tmpl_out("run.html")

    #---------------------------------------------------------------------------
    # Core algorithm runner, it could also be called by a batch processor,
    # this one needs no parameter.
    #---------------------------------------------------------------------------
    def run_algo(self):
        """Core algorithm runner, it could also be called by a batch processor,
           this one needs no parameter.
        """

        # convert input selection to pgm
        img = image(self.work_dir + 'input_0.sel.png')
        img.save(self.work_dir + 'input_0.sel.pgm')

        # run LSD
        p = self.run_proc(['lsd', '-P', 'output.eps', '-S', 'output.svg',
                           'input_0.sel.pgm', 'output.txt'])
        self.wait_proc(p)

        # convert the EPS result into a PNG image
        try:
            p = self.run_proc(['/usr/bin/gs', '-dNOPAUSE', '-dBATCH',
                               '-sDEVICE=pnggray', '-dGraphicsAlphaBits=4',
                               '-r72','-dEPSCrop', '-sOutputFile=output.png',
                               'output.eps'])
            self.wait_proc(p)
            im = image(self.work_dir + "output.png")
            im.convert('1x8i')
            im.invert()
            im.save(self.work_dir + "output-inv.png")
        except Exception:
            self.log("eps->png conversion failed,"
                     + " GS is probably missing on this system")

        return

    #---------------------------------------------------------------------------
    # Display the algorithm result.
    #---------------------------------------------------------------------------
    @cherrypy.expose
    @init_app
    def result(self):
        """Display the algorithm result."""

        try:
            # if image is too small add space for archive link
            h = max(70, image(self.work_dir + 'input_0.sel.png').size[1])
            png = True
        except Exception:
            h = 70
            png = False

        return self.tmpl_out("result.html", with_png=png, height=h)

#-------------------------------------------------------------------------------
