"""
Noise Clinic ipol demo web app
(c) GNU GLP by Miguel Colom

website: http://mcolom.info
email:   miguel@mcolom.info
"""

from lib import base_app, build, http, image
from lib.misc import ctime
from lib.misc import prod
from lib.base_app import init_app
import shutil
import cherrypy
from cherrypy import TimeoutError
import os.path
import stat
import time

class app(base_app):
    """ Noise Clinic app """

    title = "The Noise Clinic: a Blind Image Denoising Algorithm"
    input_nb = 1
    input_max_pixels = 3200 * 3200 # max size (in pixels) of an input image
    input_max_weight = 10 * 1024 * 1024 # max size (in bytes) of an input file
    input_dtype = '3x8i' # input image expected data type
    input_ext = '.png' # input image expected extension (ie file format)
    is_test = False
    xlink_article = "http://www.ipol.im/pub/art/2015/125/"

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

    #
    # PARAMETER HANDLING
    #

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


    #@cherrypy.expose
    #@init_app
    #def params(self, newrun=False, msg=None, **kwargs):
        #"""
        #configure the algo execution
        #"""
        #if newrun:
            #self.clone_input()
        #return self.tmpl_out("params_angular.html", msg=msg)



    #@cherrypy.expose
    #@init_app
    #def wait(self):
        #"""
        #run redirection
        #"""
        #http.refresh(self.base_url + 'run?key=%s' % ((self.key)))
        #return self.tmpl_out("wait.html")

    @cherrypy.expose
    @init_app
    def run(self):
        """
        algorithm execution
        """
        # read the parameters
        stdfactor = self.cfg['param']['stdfactor']
        nbscales = self.cfg['param']['nbscales']

        # run the algorithm
        try:
            run_time = time.time()
            self.run_algo(stdfactor, nbscales)
            run_time = time.time() - run_time
            self.cfg['info']['run_time'] = run_time
            self.cfg.save()
        except TimeoutError:
            return self.error(errcode='timeout')
        except RuntimeError:
            print "Run time error"
            return self.error(errcode='runtime')

        http.redir_303(self.base_url + 'result?key=%s' % ((self.key)))

        # archive
        if self.cfg['meta']['original']:
            ar = self.make_archive()
            ar.add_file("input_0.orig.png", info="uploaded")
            ar.add_file("input_0.sel.png", info="selected")
            ar.add_file("denoised.png", info="denoised")
            #
            ar.add_info({"stdfactor": stdfactor})
            ar.add_info({"nbscales": nbscales})
            ar.save()
        return self.tmpl_out("run.html")

    # Get number of channels
    @staticmethod
    def get_num_channels(filename):
        '''
        Reads the specified file and returns its number of channels
        '''
        f = open(filename)
        line = f.readline()
        f.close()
        num_channels = len(line.split()) / 2
        return num_channels

    # Get the min and max ranges for the X and Y axes to mantain the
    # same visualization ranges of the noise curves.
    @staticmethod
    def nc_get_min_max(filename):
        '''
        Returns the minimum and maximum ranges for
        the X and Y axes
        '''
        x_min, x_max, y_min, y_max = 1E9, -1E9, 1E9, -1E9

        # Read data
        f = open(filename, 'r')

        EOF = False
        lines = []
        while not EOF:
            line = f.readline()
            s = line.split()
            EOF = (line == '')
            lineStrip = line.strip()
            isWhiteLine = (not EOF and lineStrip == '')
            isComment = lineStrip.startswith('#')
            if not (EOF or isWhiteLine or isComment):
                lines.append(s)
        #
        f.close()

        # Guess number number of channels
        numBins = len(lines)
        if numBins > 0:
            numChannels = len(lines[0])/2
        else:
            numChannels = 0

        # Read data values
        for b in range(numBins):
            line = lines[b]
            #
            for ch in range(numChannels):
                x_value = line[ch].strip().upper()
                y_value = line[ch+numChannels].strip().upper()
                #
                if x_value.upper() != 'X' and y_value.upper() != 'X':
                    x = float(x_value)
                    y = float(y_value)
                    if x < x_min:
                        x_min = x
                    if y < y_min:
                        y_min = y
                    if x > x_max:
                        x_max = x
                    if y > y_max:
                        y_max = y
        #
        return x_min, x_max, y_min, y_max


    def run_algo(self, stdfactor, nbscales, timeout=False):
        """
        the core algo runner
        could also be called by a batch processor
        """
        procOptions = ['MSD', 'input_0.sel.png', 'denoised.png', 'diff.png', \
                              '%d' % nbscales, \
                              '%f' % stdfactor, \
                              '0']
        # The last parameter is "verbose".

        # Run Noise Clinic
        print procOptions
        procDesc = self.run_proc(procOptions)
        self.wait_proc(procDesc, timeout*0.8)

        # Get number of channels
        num_channels = app.get_num_channels(self.work_dir + \
                         'denoised_noiseCurves_H_0.txt')

        # Get noise curve bounds
        x_min, x_max, y_min, y_max = 1E9, -1E9, 1E9, -1E9
        for i in range(nbscales):
            for C in ["L", "H"]:
                filename = "denoised_noiseCurves_%s_%d.txt" % ((C, i))
                x_min_image, x_max_image, \
                  y_min_image, y_max_image = \
                    self.nc_get_min_max(self.work_dir + filename)
                x_min = min(x_min, x_min_image)
                x_max = max(x_max, x_max_image)
                y_min = min(y_min, y_min_image)
                y_max = max(y_max, y_max_image)

        # Generate noise curve figures
        for i in range(nbscales):
            filename = self.work_dir + 'denoised_noiseCurves_H_%d.txt' % i
            for C in ["L", "H"]:
                estimation = "denoised_noiseCurves_%s_%d.txt" % ((C, i))
                figure = "denoised_noiseCurves_%s_%d.png" % ((C, i))
                procOptions = [ os.path.join(self.base_dir,'scripts',
                                             'writeNoiseCurve.sh'), 
                                estimation,
                                '%s' % num_channels,
                                '%f' % (x_min*0.9),
                                '%f' % (x_max*1.1),
                                '%f' % (y_min*0.9),
                                '%f' % (y_max*1.1),
                                figure]
                # Run
                procDesc = self.run_proc(procOptions)
                self.wait_proc(procDesc, timeout*0.8)



    #@cherrypy.expose
    #@init_app
    #def result(self, run_time=0):
        #"""
        #display the algo results
        #"""
        #return self.tmpl_out("result.html")

