"""
Automatic Lens Distortion Correction Using One Parameter Division Models
"""
from lib import base_app, build, http
from lib.misc import ctime
from lib.base_app import init_app
from lib.config import cfg_open
import shutil

import cherrypy
from cherrypy import TimeoutError

import os.path
import time
import build_demo

#
# INTERACTION
#
class NoMatchError(RuntimeError):
    """ NoMatchError function """
    pass



class app(base_app):
    """ Automatic Lens Distortion Correction \
    Using One Parameter Division Models app """

    title = 'Automatic Lens Distortion Correction \
            Using One-Parameter Division Model'
    description = ''

    input_nb = 1                 # number of input files
    input_max_pixels = 1024000   # max size (in pixels) of an input image
    input_max_weight = 5242880   # max size (in bytes) of an input file
    input_dtype = '3x8i'         # input image expected data type
    input_ext = '.png'           # input image expected extention
    is_test = False

    xlink_article = 'http://www.ipol.im/pub/pre/106/'

    def __init__(self):
        """
        app setup
        """
        # setup the parent class
        base_dir = os.path.dirname(os.path.abspath(__file__))
        base_app.__init__(self, base_dir)

        # select the base_app steps to expose
        # index() and input_xxx() are generic
        base_app.index.im_func.exposed = True
        base_app.input_select.im_func.exposed = True
        base_app.input_upload.im_func.exposed = True

        # params() is modified from the template
        base_app.params.im_func.exposed = True

        # result() is modified from the template
        base_app.result.im_func.exposed = True

        # Generate a new timestamp
        self.timestamp = int(100*time.time())

        ## run() is defined in local.py
        #from local import run_algo as local_run
        ## redefine app.run()
        #app.run_algo = local_run

    def build(self):
        bd = build_demo.BuildDemo(os.path.dirname(os.path.abspath(__file__)))
        bd.make()

    @cherrypy.expose
    @init_app
    def run(self): ##, **kwargs):
        """
        algorithm execution
        """
        stdout = open(self.work_dir + 'stdout.txt', 'w')

        try:
            run_time = time.time()
            self.run_algo(stdout=stdout) #, timeout=self.timeout )
            self.cfg['info']['run_time'] = time.time() - run_time
            self.cfg.save()
        except TimeoutError:
            return self.error(errcode='timeout',
                              errmsg="Try again with simpler images.")
        except NoMatchError:
            http.redir_303(self.base_url + 'result?key=%s&error_nomatch=1' % \
                           self.key)
        except RuntimeError:
            return self.error(errcode='runtime')

        stdout.close()
        http.redir_303(self.base_url + 'result?key=%s' % self.key)

        # archive
        if self.cfg['meta']['original']:
            ar = self.make_archive()
            ar.add_file("input_0.png", info="Input", compress=False)
            ar.add_info({'high_threshold_canny':                            \
                          self.cfg['param']['high_threshold_canny']})
            ar.add_info({'initial_distortion_parameter':                    \
                          self.cfg['param']['initial_distortion_parameter']})
            ar.add_info({'final_distortion_parameter':                      \
                          self.cfg['param']['final_distortion_parameter']})
            ar.add_info({'distance_point_line_max_hough' :                   \
                          self.cfg['param']['distance_point_line_max_hough']})
            ar.add_info({'angle_point_orientation_max_difference':          \
                          self.cfg['param']\
                                  ['angle_point_orientation_max_difference']})
            ar.add_file("output_canny.png", info="Canny", compress=False)
            ar.add_file("output_hough.png", info="Hough", compress=False)
            ar.add_file("output_corrected_image.png", info="Output",          \
                        compress=False)
            ar.add_file("primitives.txt", info="Primitives", compress=False)
            ar.add_info({"run time" : self.cfg['info']['run_time']})
            ar.save()

        return self.tmpl_out("run.html")


    def run_algo(self, stdout=None): #, timeout=False):
        """
        The core algo runner
        could also be called by a batch processor
        this one needs no parameter
        """

        high_threshold_canny = self.cfg['param']['high_threshold_canny']
        initial_distortion_parameter =                                        \
                            self.cfg['param']['initial_distortion_parameter']
        final_distortion_parameter =                                          \
                            self.cfg['param']['final_distortion_parameter']
        distance_point_line_max_hough =                                       \
                            self.cfg['param']['distance_point_line_max_hough']
        angle_point_orientation_maxdif =                                      \
                    self.cfg['param']['angle_point_orientation_max_difference']

        # Run the code
        self.wait_proc(self.run_proc([                                        \
            'lens_distortion_correction_division_model_1p',
            'input_0.png', 'output_canny.png', 'output_hough.png',            \
            'output_corrected_image.png',
            str(high_threshold_canny), str(initial_distortion_parameter),
            str(final_distortion_parameter),                                  \
            str(distance_point_line_max_hough),
            str(angle_point_orientation_maxdif), 'primitives.txt'],           \
            stdout=stdout, stderr=stdout), self.timeout) # , timeout)



    @cherrypy.expose
    @init_app
    def result(self, error_nomatch=None):
        """
        display the algo results
        """
        if error_nomatch:
            return self.tmpl_out("result_nomatch.html")
        else:
            return self.tmpl_out("result.html")

