"""
Ponomarenko et al. IPOL demo web app

Miguel Colom
http://mcolom.info/
"""

from lib import base_app, build, http, image
from lib.misc import ctime
from lib.misc import prod
from lib.base_app import init_app
import shutil
import cherrypy
from cherrypy import TimeoutError
import os
import stat
import time
from math import sqrt


class app(base_app):
    """ Ponomarenko et al. noise estimation app """

    title = "Analysis and Extension of the Ponomarenko et al Method, " \
        + "Estimating a Noise Curve from a Single Image"
    input_nb = 1
    input_max_pixels = 5000 * 5000 # max size (in pixels) of an input image
    input_max_weight = 10 * 1024 * 1024 # max size (in bytes) of an input file
    input_dtype = '3x8i' # input image expected data type
    input_copy_png = True
    input_ext = '.png' # input image expected extension (ie file format)
    is_test = False

    xlink_article = 'http://www.ipol.im/pub/art/2013/45/'

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
        base_app.input_select_angular.im_func.exposed = True
        base_app.input_upload.im_func.exposed = True
        # params() is modified from the template
        base_app.params.im_func.exposed = True
        # result() is modified from the template
        base_app.result.im_func.exposed = True

    def build(self):
        """
        program build/update
        """
        version = 4
        zip_filename = 'ponomarenko_v%d.zip' % ((version))
        src_dir_name = 'ponomarenko_v%d' % ((version))
        prog_filename = 'ponomarenko'
        # store common file path in variables
        tgz_file = self.dl_dir + zip_filename
        prog_file = self.bin_dir + prog_filename
        log_file = self.base_dir + "build.log"
        # get the latest source archive
        build.download('http://www.ipol.im/pub/art/2013/45/' + \
                       zip_filename, tgz_file)

        # test if the dest file is missing, or too old
        if (os.path.isfile(prog_file)
            and ctime(tgz_file) < ctime(prog_file)):
            cherrypy.log("not rebuild needed",
                         context='BUILD', traceback=False)
        else:
            # extract the archive
            build.extract(tgz_file, self.src_dir)

            # delete and create bin dir
            if os.path.isdir(self.bin_dir):
                shutil.rmtree(self.bin_dir)
            os.mkdir(self.bin_dir)

            # build the programs
            programs = ('fnoise', 'subscale', 'ponomarenko')
            for program in programs:
                # build
                build.run("make -j4 -C %s %s" %
                       (
                         os.path.join(self.src_dir, src_dir_name, program),
                         os.path.join(".", program)
                       ), stdout=log_file)
                # move binary to bin dir
                shutil.copy(os.path.join(self.src_dir, \
                                         src_dir_name, \
                                         program, program),
                            os.path.join(self.bin_dir, program))

            # Move scripts to the base dir
            corr_dirs = ['../scripts']
            for corr_dir in corr_dirs:
                shutil.move(os.path.join(self.src_dir, src_dir_name,    \
                                         prog_filename, corr_dir), \
                            os.path.join(src_dir_name, self.base_dir))

            # Give exec permission to the script
            os.chmod(
                     os.path.join(
                                  src_dir_name, self.base_dir,
                                  "scripts", "writeNoiseCurve.sh"
                                 ),
                     stat.S_IREAD | stat.S_IEXEC
                    )

            # cleanup the source dir
            shutil.rmtree(self.src_dir)
        return

    #
    # PARAMETER HANDLING
    #

    @cherrypy.expose
    @init_app
    def params(self, newrun=False, msg=None, \
               x0=None, y0=None, x1=None, y1=None, \
               percentile=None, block=None, \
               curvefilter=None, removeequals=None, bins=None, \
               anoise=None, bnoise=None, mean_type=None):
        """
        configure the algo execution
        """

        if newrun:
            self.clone_input()

        if x0:
            self.select_subimage(int(x0), int(y0), int(x1), int(y1))

        perc_val = float(percentile) if percentile is not None else 0.005
        return self.tmpl_out("params_angular.html",
                             msg=msg, x0=x0, y0=y0, x1=x1, y1=y1, \
                             percentile='%.4f' % perc_val, \
                             block=block, \
                             curvefilter=curvefilter, \
                             removeequals=removeequals, \
                             bins=bins, \
                             anoise=anoise, \
                             bnoise=bnoise, \
                             mean_type=mean_type)

    @cherrypy.expose
    @init_app
    def run(self):
        """
        algorithm execution
        """

        # read the parameters
        percentile = self.cfg['param']['percentile']
        block = self.cfg['param']['block']
        curvefilter = self.cfg['param']['curvefilter']
        removeequals = self.cfg['param']['removeequals']
        bins = self.cfg['param']['bins']
        anoise = self.cfg['param']['anoise']
        bnoise = self.cfg['param']['bnoise']
        mean_type = self.cfg['param']['mean_type']

        # run the algorithm
        try:
            run_time = time.time()
            self.run_algo(percentile, \
                          block, curvefilter, removeequals, bins, \
                          anoise, bnoise, mean_type)
            self.cfg['info']['run_time'] = time.time() - run_time
            self.cfg.save()
        except TimeoutError:
            return self.error(errcode='timeout') 
        except RuntimeError:
            return self.error(errcode='runtime')

        http.redir_303(self.base_url + 'result?key=%s' % self.key)

        # archive
        if self.cfg['meta']['original']:
            ar = self.make_archive()
            ar.add_file("input_0.orig.png", info="uploaded image")
            ar.add_file("input_0.sel.png", info="selected subimage")
            #
            ar.add_info({"percentile": percentile})
            ar.add_info({"block": block})
            ar.add_info({"curvefilter": curvefilter})
            ar.add_info({"removeequals": removeequals})
            ar.add_info({"bins": bins})
            ar.add_info({"anoise": anoise})
            ar.add_info({"bnoise": bnoise})
            ar.add_info({"mean_type": mean_type})
            #
            ar.save()
        return self.tmpl_out("run.html")

    @classmethod
    def RMSE_scale(cls, filename, A, B, scale):
        """
        Computes the RMSE at each scale knowing the A and B parameters
        """
        f = open(filename)
        #
        line = f.readline()
        values = line.strip().split()
        num_stds = len(values)/2
        MSE = 0.0
        num_bins = 0
        while len(values) > 0:
            for i in range(num_stds):
                mean = float(values[i])
                tilde_std = float(values[i+num_stds])
                std = sqrt(A + B*mean) / (2.0**scale)
                err = tilde_std - std
                MSE += err ** 2.0
            #
            line = f.readline()
            values = line.strip().split()
            num_bins += 1
        #
        f.close()
        #
        MSE /= float(num_bins) * num_stds
        return sqrt(MSE)

    @classmethod
    def get_compatible_size(cls, sizeX, sizeY):
        """
        Returns a compatible known size given an arbitrary size
        """
        image_pixels = sizeX * sizeY
        pixels = [6000000.0, 1500000.0, 375000.0, 93750.0, 23438.0]
        #
        minimum_idx = 0
        min_err = abs(pixels[minimum_idx] - image_pixels)
        for i in range(len(pixels)):
            err = abs(pixels[i] - image_pixels)
            if err < min_err:
                min_err = err
                minimum_idx = i
        #
        return minimum_idx

    @classmethod
    def get_num_bins(cls, size):
        """
        Returns a recommended number of bins given the size of the image
        """
        nb = [0, 0, 0, 4, 1]
        return nb[size]

    # Get number of channels
    @classmethod
    def get_num_channels(cls, filename):
        """
        Returns the number of channels given an estimation file
        """
        f = open(filename)
        line = f.readline()
        f.close()
        num_channels = len(line.split()) / 2
        return num_channels

    # Remove last bin
    @classmethod
    def remove_last_bin(cls, filename):
        """
        removes the last bin from the noise estimation file
        """
        lines = []

        # Read lines structure
        f = open(filename, 'r')  

        EOF = False
        while not EOF:
            line = f.readline()
            s = line.split()
            EOF = (line == '')
            lineStrip = line.strip()
            isWhiteLine = (not EOF and lineStrip == '')
            isComment = lineStrip.startswith('#')
            if not (EOF or isWhiteLine or isComment):
                lines.append(s)

        f.close()

        if len(lines) < 2:
            return

        # Re-write file
        f = open(filename, 'w')  
        #
        for line in lines[0:len(lines)-1]:
            for intensity_str in line[0:len(line)/2]:
                f.write(intensity_str + " ")
            for std_str in line[len(line)/2:]:
                f.write(std_str + " ")
            f.write("\n")
        #
        f.close()

    # Correct quantization error
    @classmethod
    def correct_quantization_error(cls, filename, scale):
        """
        sustracts the quantization error from the noise estimation file
        """

        lines = []

        # Read lines structure
        f = open(filename, 'r')  

        EOF = False
        while not EOF:
            line = f.readline()
            s = line.split()
            EOF = (line == '')
            lineStrip = line.strip()
            isWhiteLine = (not EOF and lineStrip == '')
            isComment = lineStrip.startswith('#')
            if not (EOF or isWhiteLine or isComment):
                lines.append(s)

        f.close()

        # Correct stds and re-write file
        f = open(filename, 'w')
        #
        for line in lines:
            for intensity_str in line[0:len(line)/2]:
                intensity = float(intensity_str)
                f.write(str(intensity) + " ")
            for std_str in line[len(line)/2:]:
                std = float(std_str)
                D = std**2.0 - (1.0/4)**scale * (1.0/12)                
                std = sqrt(D) if D >= 0 else 0
                f.write(str(std) + " ")
            f.write("\n")
        #
        f.close()


    def run_algo(self, percentile, block, \
                 curvefilter, removeequals, bins, \
                 anoise, bnoise, mean_type, timeout=False):
        """
        the core algo runner
        could also be called by a batch processor
        """

        # Increment the number of bins, since the last will be
        # removed later
        if bins > 0:
            bins += 1

        # Get input size
        ima = image(self.work_dir + 'input_0.sel.png')
        sizeX, sizeY = ima.size

        # Convert input to RGB format.
        procOptions = ['fnoise', \
                       '-A%f' % anoise, '-B%f' % bnoise, \
                       'input_0.sel.png', \
                       'scale_s0.rgb']
        # Run
        procDesc1 = self.run_proc(procOptions)

        # Convert noisy input to PNG, only for visualization
        procOptions = ['fnoise', \
                       '-A%f' % anoise, '-B%f' % bnoise, \
                       '-t', \
                       'input_0.sel.png', \
                       'scale_s0.png']
        # Run
        procDesc2 = self.run_proc(procOptions)
        #
        self.wait_proc([procDesc1, procDesc2], timeout*0.8)

        # Determine the number of scales
        num_scales = 0
        scale_OK = (num_scales <= 4 and sizeX*sizeY >= 20000)
        sizes = {}
        while scale_OK:
            sizes[num_scales] = (sizeX, sizeY)
            # Data for the next scale
            sizeX /= 2
            sizeY /= 2
            # Next scale
            num_scales += 1
            scale_OK = (num_scales <= 4 and sizeX*sizeY >= 20000)

        # Create sub-scales
        for scale in range(num_scales):
            if scale != num_scales - 1:
                # Create next subscale scale s{i+1} for s{i}.
                procOptions = ['subscale', \
                               '-s2', \
                               'scale_s%d.rgb' % ((scale)), \
                               'scale_s%d.rgb' % ((scale+1))]
                procDesc = self.run_proc(procOptions)
                self.wait_proc(procDesc, timeout*0.8)


        # Estimate the noise, in parallel,
        processes = []
        fds = []
        for scale in range(num_scales):
            sizeX, sizeY = sizes[scale]
            # Number of bins
            compatible_size = self.get_compatible_size(sizeX, sizeY)
            num_bins = (self.get_num_bins(compatible_size) \
if bins == 0 else bins / 2**scale)

            # Estimate noise
            fd = open(self.work_dir + 'estimation_s%d.txt' % scale, "w")
            if percentile < 0:
                percentile = 0 # Use algorithm's K

            procOptions = ['ponomarenko', \
                           '-p%.4f' % percentile , \
                           '-b%d' % num_bins, \
                           '-w%d' % block, \
                           '-m%d' % mean_type, \
                           '-g%d' % curvefilter]
            #          
            if removeequals == 1:
                procOptions.append('-r')
            #
            procOptions.append('scale_s%d.rgb' % scale)

            # Run
            #pid = self.run_proc(procOptions, stdout=fd, stderr=fd)
            #self.wait_proc(pid, timeout*0.8)
            #fd.close()

            processes.append(self.run_proc(procOptions, stdout=fd, stderr=fd))
            fds.append(fd)

        # Wait for the parallel processes to end
        self.wait_proc(processes, timeout*0.8)

        # Close the file descriptors
        for fd in fds:
            fd.close()

        # Remove last bin, correct quantization error and draw noise curves
        RMSEs = ''
        for scale in range(num_scales):
            estimation_filename = self.work_dir + 'estimation_s%d.txt' % scale

            # Remove the last bin
            self.remove_last_bin(estimation_filename)

            self.correct_quantization_error(estimation_filename, scale)

            # Compute RMSE of the current scale
            if anoise > 0.0 or bnoise > 0.0: # Only if user added noise
                RMSE = self.RMSE_scale(
                         estimation_filename, \
                         anoise, bnoise, scale)
                RMSEs += '%f,' % RMSE

            # Get number of channels
            num_channels = self.get_num_channels(estimation_filename)

            # Generate figure
            procOptions = [os.path.join(self.base_dir, \
                           'scripts', \
                           'writeNoiseCurve.sh'), \
                           'estimation_s%d.txt' % scale, \
                           '%d' % num_channels, \
                           'curve_s%d.png' % scale]
            # Run
            procDesc = self.run_proc(procOptions)
            self.wait_proc(procDesc, timeout*0.8)


        self.cfg['param']['scales'] = num_scales
        self.cfg['param']['rmses'] = RMSEs
        self.cfg.save()

        # Cleanup
        for i in range(num_scales):
            os.unlink(self.work_dir + 'scale_s%d.rgb' % ((i)))

    @cherrypy.expose
    @init_app
    def result(self):
        """
        display the algo results
        """

        # read parameters
        percentile = self.cfg['param']['percentile']
        block = self.cfg['param']['block']
        curvefilter = self.cfg['param']['curvefilter']
        removeequals = self.cfg['param']['removeequals']
        bins = self.cfg['param']['bins']
        scales = self.cfg['param']['scales']
        anoise = self.cfg['param']['anoise']
        bnoise = self.cfg['param']['bnoise']
        mean_type = self.cfg['param']['mean_type']
        RMSEs = self.cfg['param']['rmses']

        try:
            x0 = self.cfg['param']['x0']
        except KeyError:
            x0 = None
        try:
            y0 = self.cfg['param']['y0']
        except KeyError:
            y0 = None
        try:
            x1 = self.cfg['param']['x1']
        except KeyError:
            x1 = None
        try:
            y1 = self.cfg['param']['y1']
        except KeyError:
            y1 = None

        (sizeX, sizeY) = image(self.work_dir + 'input_0.sel.png').size
        zoom_factor = None

        perc_val = float(percentile) if percentile is not None else 0.005
        return self.tmpl_out("result.html",
                             percentile='%.4f' % perc_val, \
                             block=block, \
                             curvefilter=curvefilter, \
                             removeequals=removeequals, \
                             bins=bins, \
                             scales=scales, \
                             anoise=anoise, \
                             bnoise=bnoise, \
                             mean_type=mean_type, \
                             RMSEs=RMSEs, \
                             x0=x0, y0=y0, x1=x1, y1=y1, \
                             sizeX=sizeX, sizeY=sizeY, \
                             zoom_factor=zoom_factor)

