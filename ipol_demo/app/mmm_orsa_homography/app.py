"""
Automatic Homographic Registration of a Pair of Images, with A Contrario
Elimination of Outliers
"""

from lib import base_app, image, http, build
from lib.misc import app_expose, ctime
from lib.base_app import init_app
from cherrypy import TimeoutError
import os.path
import time
import cherrypy
import shutil

#
# INTERACTION
#

class NoMatchError(RuntimeError):
    """ Exception raised when ORSA fails """
    pass

class app(base_app):
    """ template demo app """
    
    title = """Automatic Homographic Registration of a Pair of Images, with
A Contrario Elimination of Outliers"""
    xlink_article = 'http://www.ipol.im/pub/art/2012/mmm-oh/'

    input_nb = 2 # number of input images
    input_max_pixels = 1600 * 1200 # max size (in pixels) of an input image
    input_dtype = '3x8i' # input image expected data type
    input_ext = '.png'   # input image expected extension (ie file format)    
    is_test = False      # switch to False for deployment

    def __init__(self):
        """
        app setup
        """
        # setup the parent class
        base_dir = os.path.dirname(os.path.abspath(__file__))
        base_app.__init__(self, base_dir)

        # select the base_app steps to expose
        # index() is generic
        app_expose(base_app.index)

    def build(self):
        """
        program build/update
        """
        # store common file path in variables
        tgz_file = self.dl_dir + "OrsaHomography.tar.gz"
        tgz_url = "http://www.ipol.im/pub/art/2012/mmm-oh/" + \
            "OrsaHomography_20120515.tar.gz"
        build_dir = (self.src_dir
                     + os.path.join("OrsaHomography_20120515", "build")
                     + os.path.sep)
        exe = build_dir + os.path.join("demo","demo_orsa_homography")
        prog = self.bin_dir + "demo_orsa_homography"
        log_file = self.base_dir + "build.log"
        # get the latest source archive
        build.download(tgz_url, tgz_file)
        # test if any of the dest files is missing, or too old
        if os.path.isfile(prog) and ctime(tgz_file) < ctime(prog):
            cherrypy.log("no rebuild needed", context='BUILD', traceback=False)
        else:
            # extract the archive
            build.extract(tgz_file, self.src_dir)
            # build the program
            os.mkdir(build_dir)
            build.run("cmake -D CMAKE_BUILD_TYPE:string=Release ../src",
                      stdout=log_file, cwd=build_dir)
            build.run("make -C %s -j4" % build_dir,
                      stdout=log_file)
            # save into bin dir
            if os.path.isdir(self.bin_dir):
                shutil.rmtree(self.bin_dir)
            os.mkdir(self.bin_dir)
            shutil.copy(exe, prog)
            # cleanup the source dir
            shutil.rmtree(self.src_dir)
        return

    #
    # PARAMETER HANDLING
    #

    @cherrypy.expose
    @init_app
    def params(self, newrun=False, msg=None):
        """
        configure the algo execution
        """
        if newrun:
            self.clone_input()
        width  = max(image(self.work_dir + 'input_0.png').size[0],
                     image(self.work_dir + 'input_1.png').size[0])
        height = max(image(self.work_dir + 'input_0.png').size[1],
                     image(self.work_dir + 'input_1.png').size[1])
        return self.tmpl_out("params.html", width=width, height=height)

    @cherrypy.expose
    @init_app
    def rectangle(self, action=None,
                  x=None, y=None, x0=None, y0=None):
        """
        rectangle selection 
        """
        width  = max(image(self.work_dir + 'input_0.png').size[0],
                     image(self.work_dir + 'input_1.png').size[0])
        height = max(image(self.work_dir + 'input_0.png').size[1],
                     image(self.work_dir + 'input_1.png').size[1])
        if not x0: # draw first corner
            x = int(x)
            y = int(y)
            # draw a cross at the first corner
            img = image(self.work_dir + 'input_0.png')
            img.draw_cross((x, y), size=4, color="white")
            img.draw_cross((x, y), size=2, color="red")
            img.save(self.work_dir + 'input_crop.png')
            return self.tmpl_out("params.html", width=width, height=height,
                                 x0=x, y0=y)
        else: # second corner selection
            x0 = int(x0)
            y0 = int(y0)
            x1 = int(x)
            y1 = int(y)
            # draw rectangle
            img = image(self.work_dir + 'input_0.png')
            img.draw_line([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)],
                          color="red")
            img.save(self.work_dir + 'input_crop.png')
            # reorder the corners
            (x0, x1) = (min(x0, x1), max(x0, x1))
            (y0, y1) = (min(y0, y1), max(y0, y1))
            return self.tmpl_out("params.html", width=width, height=height,
                                 x0=x0, y0=y0, x1=x1, y1=y1)

    @cherrypy.expose
    @init_app
    def wait(self, **kwargs):
        """
        params handling and run redirection
        """
        if 'precision' in kwargs:
            self.cfg['param']['precision'] = kwargs['precision']
        if 'SiftRatio' in kwargs:
            self.cfg['param']['siftratio'] = kwargs['SiftRatio']
        im0 = 'input_0.png'
        if 'rectangle' in kwargs:
            try:
                self.cfg['param']['x0'] = int(kwargs['x0'])
                self.cfg['param']['y0'] = int(kwargs['y0'])
                self.cfg['param']['x1'] = int(kwargs['x1'])
                self.cfg['param']['y1'] = int(kwargs['y1'])
            except ValueError:
                return self.error(errcode='badparams',
                                  errmsg="Incorrect parameters.")
            im0 = 'input_crop.png'

        # no parameter
        http.refresh(self.base_url + 'run?key=%s' % self.key)
        width  = max(image(self.work_dir + im0).size[0],
                     image(self.work_dir + 'input_1.png').size[0])
        height = max(image(self.work_dir + im0).size[1],
                     image(self.work_dir + 'input_1.png').size[1])
        return self.tmpl_out("wait.html", width=width, height=height, im0=im0)

    @cherrypy.expose
    @init_app
    def run(self, **kwargs):
        """
        algorithm execution
        """
        success = False
        try:
            run_time = time.time()
            self.run_algo(timeout=self.timeout)
            self.cfg['info']['run_time'] = time.time() - run_time
        except TimeoutError:
            return self.error(errcode='timeout')
        except NoMatchError:
            self.cfg['info']['run_time'] = time.time() - run_time
            http.redir_303(self.base_url +
                           'result?key=%s&error_nomatch=1' % self.key)
        except RuntimeError:
            return self.error(errcode='runtime')
        else:
            http.redir_303(self.base_url + 'result?key=%s' % self.key)
            success = True

        # archive
        if self.cfg['meta']['original']:
            ar = self.make_archive()
            ar.add_file("input_0.orig.png", info="uploaded #1")
            ar.add_file("input_1.orig.png", info="uploaded #2")
            ar.add_file("input_0.png", info="input #1")
            ar.add_file("input_1.png", info="input #2")
            if 'x0' in self.cfg['param']:
                ar.add_info({"crop": {'x0': self.cfg['param']['x0'],
                                      'y0': self.cfg['param']['y0'],
                                      'x1': self.cfg['param']['x1'],
                                      'y1': self.cfg['param']['y1']}
                             })
            if 'precision' in self.cfg['param']:
                ar.add_info({"precision": self.cfg['param']['precision']})
            if 'siftratio' in self.cfg['param']:
                ar.add_info({"SiftRatio": self.cfg['param']['siftratio']})
            ar.add_file("match.txt", compress=True)
            ar.add_file("matchOrsa.txt", compress=True)
            ar.add_file("outliers.png", info="outliers image")
            if success:
                ar.add_file("inliers.png", info="inliers image")
                ar.add_file("panorama.png", info="panorama")
                ar.add_file("registered_0.png", info="registered image #1")
                ar.add_file("registered_1.png", info="registered image #2")
            ar.add_file("stdout.txt", compress=True)
            ar.save()

        return self.tmpl_out("run.html")

    def run_algo(self, timeout=None):
        """
        the core algo runner
        could also be called by a batch processor
        this one needs no parameter
        """
        cmd = ['demo_orsa_homography',
               self.work_dir + 'input_0.png',
               self.work_dir + 'input_1.png',
               "match.txt",
               "matchOrsa.txt",
               "inliers.png",
               "outliers.png",
               "panorama.png",
               "registered_0.png",
               "registered_1.png"]
        if 'precision' in self.cfg['param']:
            try:
                float(self.cfg['param']['precision'])
                precision = str(self.cfg['param']['precision'])
                cmd[1:1] = ['-p', precision]
            except ValueError:
                pass
        if 'siftratio' in self.cfg['param']:
            try:
                float(self.cfg['param']['siftratio'])
                SiftRatio = str(self.cfg['param']['siftratio'])
                cmd[1:1] = ['-s', SiftRatio]
            except ValueError:
                pass
        if 'x0' in self.cfg['param']:
            x = int(self.cfg['param']['x0'])
            y = int(self.cfg['param']['y0'])
            w = int(self.cfg['param']['x1'])-x
            h = int(self.cfg['param']['y1'])-y
            geom = str(w)+'x'+str(h)+'+'+str(x)+'+'+str(y)
            cmd[1:1] = ['-c', geom]
        print
        print self.work_dir
        for i in cmd:
            print i
        print

        stdout = open(self.work_dir + 'stdout.txt', 'w')
        proc = self.run_proc(cmd, stdout=stdout, stderr=stdout)
        try:
            self.wait_proc(proc, timeout)
        except RuntimeError:
            if 0 != proc.returncode:
                stdout.close()
                raise NoMatchError
            else:
                raise
        stdout.close()
        return

    @cherrypy.expose
    @init_app
    def result(self, error_nomatch=None):
        """
        display the algo results
        """
        inliers = len( open(self.work_dir + 'matchOrsa.txt', 'r').readlines() )
        outliers = len( open(self.work_dir + 'match.txt', 'r').readlines() )
        outliers -= inliers
        self.cfg['info']['inliers'] = inliers
        self.cfg['info']['outliers'] = outliers
        width  = max(image(self.work_dir + 'input_0.png').size[0],
                     image(self.work_dir + 'input_1.png').size[0])
        height = max(image(self.work_dir + 'input_0.png').size[1],
                     image(self.work_dir + 'input_1.png').size[1])
        if error_nomatch:
            return self.tmpl_out("result_nomatch.html",
                                 width=width, height=height)
        else:
            return self.tmpl_out("result.html",
                                 width=width, height=height)
