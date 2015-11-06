"""
online image processing
"""

from lib import base_app, build, http, image, config, thumbnail
from lib.misc import ctime, prod
from lib.base_app import init_app
import cherrypy
from cherrypy import TimeoutError
import os.path
import shutil
import subprocess
import glob

class app(base_app):
    """ template demo app """

    title = "An Implementation of Combined Local-Global Optical Flow"
    xlink_article = "http://www.ipol.im/pub/pre/44/"

    is_test = False       # switch to False for deployment
    is_listed = True
    is_built = True

    xlink_src = "http://www.ipol.im/pub/pre/44/clg_6.1.tgz"

    xlink_src_demo = "http://www.ipol.im/pub/pre/44/imscript_dec2011.tar.gz"
    xlink_input = "http://dev.ipol.im/~coco/static/flowpairs.tar.gz"

    parconfig = {}
    parconfig['alpha'] = {'type': float,
            'default': 200.0, 'changeable': True,
            'htmlname': '&alpha;',
            'doc': 'global regularization parameter\
                   (&alpha;>0. Higher values produce more homogeneus fields, &nbsp;\
                lower values allow more variating displacement vectors in a given image region)' 
            }
    parconfig['rho'] = {'type': float,
                        'default': 10.0, 'changeable': True,
                        'htmlname': '&rho;',
                        'doc': 'neighborhood size in local approach\
                               (size of Gaussian kernel = 2 &rho; + 1, &nbsp;\
                               &rho; = 0 implies no local smoothing)'
                        }
    parconfig['sigma'] = {'type': float,
                        'default': 0.85, 'changeable': True,
                        'htmlname': '&sigma;',
                        'doc': 'Pre-processing Gaussian smoothing variance'
                        }
    parconfig['numit'] = {'type': int,
             'default': 1000, 'changeable': False,
             'htmlname': 'numit',
            'doc': 'number of iterations'
            }

    parconfig['w'] = {'type': float,
                      'default': 1.9, 'changeable': False,
                      'htmlname': 'w',
                      'doc': 'SOR relaxaction factor, between 0 and 2.'
                      }

    parconfig['numscales'] = {'type': int,
             'default': 10, 'changeable': False,
             'htmlname': 'numscales',
            'doc': 'number of scales'
            }

    parconfig['zoomfactor'] = {'type': float,
             'default': 0.65, 'changeable': False,
             'htmlname': 'zoomfactor',
            'doc': 'Scale factor, between 0 and 1.'
            }

    parconfig['coupledmode'] = {'type': int,
             'default': 1, 'changeable': False,
             'htmlname': 'coupledmode',
            'doc': 'Iteration type, 1 for Gauss-Seidel, 0 for SOR.'
            }

    parconfig['verbose'] = {'type': int,
             'default': 0, 'changeable': False,
             'htmlname': 'verbose',
            'doc': 'shows (1) or hides debug messages.'
            }

    def __init__(self):
        """
        app setup
        """
        # setup the parent class
        base_dir = os.path.dirname(os.path.abspath(__file__))
        base_app.__init__(self, base_dir)

    def build_algo(self):
        """
        program build/update
        """
        ## store common file path in variables
        tgz_file = self.dl_dir + "clg_6.1.tar.gz"
        prog_file = self.bin_dir + "test_clgof"
        log_file = self.base_dir + "build.log"

        ## get the latest source archive
        build.download(app.xlink_src, tgz_file)
        ## test if the dest file is missing, or too old
        if (os.path.isfile(prog_file)
            and ctime(tgz_file) < ctime(prog_file)):
            cherrypy.log("no rebuild needed",
                          context='BUILD', traceback=False)
        else:
            # extract the archive
            build.extract(tgz_file, self.src_dir)
            # build the program
            srcdir  = self.src_dir + "clg_6.1"
            srcdir1 = self.src_dir + "clg_6.1/build"
            build.run("cmake ..", stdout=log_file, cwd=srcdir1)
            build.run("make", stdout=log_file, cwd=srcdir1)

            cherrypy.log("before copy",
                      context='BUILD', traceback=False)

            # save into bin dir
            if os.path.isdir(self.bin_dir):
                shutil.rmtree(self.bin_dir)
            os.mkdir(self.bin_dir)
            shutil.copy(srcdir + "/bin/test_clgof", prog_file)
            cherrypy.log("copy ok",
                          context='BUILD', traceback=False)

        return



    def build_demo(self):
        """
        download and build the demo auxiliary programs
        """
        ## store common file path in variables
        tgz_file = self.dl_dir + "imscript.tar.gz"
        prog_file = self.bin_dir + "plambda"
        log_file = self.base_dir + "build_imscript.log"
        ## get the latest source archive
        build.download(app.xlink_src_demo, tgz_file)
        ## test if the dest file is missing, or too old
        if (os.path.isfile(prog_file)
            and ctime(tgz_file) < ctime(prog_file)):
            cherrypy.log("no rebuild needed",
                      context='BUILD', traceback=False)
        else:
            # extract the archive
            build.extract(tgz_file, self.src_dir)
            # build the program
            build.run("make -j CFLAGS=-O3 -C %s" %
                         (self.src_dir +"imscript"),
                            stdout=log_file)
            # save into bin dir
            for f in glob.glob(os.path.join(self.src_dir,
                            "imscript", "bin", "*")):
                shutil.copy(f, self.bin_dir)
            # copy scripts from "demo" dir
            for f in glob.glob(os.path.join(self.base_dir,
                            "demo", "*")):
                shutil.copy(f, self.bin_dir)
            shutil.rmtree(self.src_dir)
        return

    def grab_input(self):
        """
        download the input images from "xlink_input"
        """
        tgz_file = self.dl_dir + "input.tar.gz"
        input_cfg = self.input_dir + "index.cfg"
        ## get the latest source archive
        build.download(app.xlink_input, tgz_file)
        ## test if the dest file is missing, or too old
        if (os.path.isfile(input_cfg)
            and ctime(tgz_file) < ctime(input_cfg)):
            cherrypy.log("no rebuild needed",
                      context='BUILD', traceback=False)
        else:
            # extract the archive
            build.extract(tgz_file, self.src_dir)
            shutil.rmtree(self.input_dir)
            shutil.move(self.src_dir + "flowpairs", self.input_dir)

            # cleanup the source dir
            shutil.rmtree(self.src_dir)
        return

    def build(self):
        self.build_algo()
        self.build_demo()
        self.grab_input()
        return


    @cherrypy.expose
    @init_app
    def wait(self, **kwargs):
        """
        params handling and run redirection
        """
        print("ENTER wait")
        print("kwargs = " + str(kwargs))
        try:
            for k in app.parconfig:
                typ = app.parconfig[k]['type']
                self.cfg['param'][k] = typ(kwargs[k])
        except ValueError:
            return self.error(errcode='badparams',
                     errmsg='The parameters must be numeric.')
        http.refresh(self.base_url + 'run?key=%s' % self.key)

        self.cfg['meta']['height'] = image(self.work_dir + '/a.png').size[1]
        self.cfg['meta']['colorscheme'] = 'ipoln'
        self.cfg['meta']['colorparam'] = '1'
        self.cfg['meta']['pos_inview'] = False

        self.cfg.save()
        return self.tmpl_out("wait.html")

    @cherrypy.expose
    @init_app
    def run(self, **kwargs):
        """
        algo execution
        """
        print("ENTER run")
        print("kwargs = " + str(kwargs))
        ## run the algorithm
        try:
            self.run_algo()
        except TimeoutError:
            return self.error(errcode='timeout')
        except RuntimeError:
            return self.error(errcode='runtime')
        http.redir_303(self.base_url + 'result?key=%s' % self.key)

        ## archive
        if self.cfg['meta']['original']:
            ar = self.make_archive()
            ar.add_file("a.png", "a.png", info="")
            ar.add_file("b.png", "b.png", info="")
            ar.add_file("stuff_clg.tiff", info="")
            ar.add_file("stuff_clg.png", info="")
            if (self.cfg['meta']['hastruth']):
                ar.add_file("t.tiff", info="")
            #ar.add_file(".png", info="output")
            ar.add_info({"alpha": self.cfg['param']['alpha'],
                    "rho": self.cfg['param']['rho'],
                    "sigma": self.cfg['param']['sigma'],
                    "numit": self.cfg['param']['numit'],
                    "w": self.cfg['param']['w'],
                    "numscales": self.cfg['param']['numscales'],
                    "zoomfactor": self.cfg['param']['zoomfactor'],
                    "coupledmode": self.cfg['param']['coupledmode'],
                    "verbose": self.cfg['param']['verbose']})
            ar.save()
        return self.tmpl_out("run.html")


    def run_algo(self):
        """
        the core algo runner
        could also be called by a batch processor
        this one needs no parameter
        """
        alpha = self.cfg['param']['alpha']
        rho = self.cfg['param']['rho']
        sigma = self.cfg['param']['sigma']
        numit = self.cfg['param']['numit']
        w     = self.cfg['param']['w']
        numscales = self.cfg['param']['numscales']
        zoomfactor = self.cfg['param']['zoomfactor']
        coupledmode = self.cfg['param']['coupledmode']
        verbose = self.cfg['param']['verbose']

        print('ENTERING run_algo')
        for k in app.parconfig:
            print(k + ' = ' + str(self.cfg['param'][k]))
        p = self.run_proc(['run_clg_noview.sh',
             str(alpha),
             str(rho),
             str(sigma),
             str(numit),
             str(w),
             str(numscales),
             str(zoomfactor),
             str(coupledmode),
             str(verbose)
            ])
        self.wait_proc(p, timeout=self.timeout)
        p = self.run_proc(['view_clg.sh', 'ipoln', '1'])
        self.wait_proc(p, timeout=self.timeout)
        return

    @cherrypy.expose
    @init_app
    def recolor(self, **kwargs):
        """
        update the color scheme
        """
        print("RECOLOR KWARGS = " + str(kwargs))
        cs = kwargs['colorscheme']
        self.cfg['meta']['colorscheme'] = cs
        self.cfg['meta']['colorwheel'] = True
        p = self.run_proc(['view_clg.sh', cs, '1'])
        self.wait_proc(p, timeout=self.timeout)
        return self.tmpl_out("result.html")

    @cherrypy.expose
    @init_app
    def reposition(self, **kwargs):
        """
        update the scroll state on the web-page
        """
        print("REPOSITION KWARGS = " + str(kwargs))
        self.cfg['meta']['pos_inview'] = True
        return self.tmpl_out("result.html")

    def tralara(self, f):
        """
        the string returned by this function will be used
        as the tooltip text of image "f"
        """
        msg = f + self.work_dir
        msg = "-"
        return msg


    @cherrypy.expose
    def input_select(self, **kwargs):
        """
        use the selected available input images
        """
        print("ENTERING input_select")
        self.new_key()
        self.init_cfg()
        print("key = " + self.key)
        # kwargs contains input_id.x and input_id.y
        input_id = kwargs.keys()[0].split('.')[0]
        assert input_id == kwargs.keys()[1].split('.')[0]
        # get the images
        input_dict = config.file_dict(self.input_dir)
        idir = self.input_dir + input_dict[input_id]['subdir'] + '/'
        fnames = "a.png b.png".split()
        for f in fnames:
            shutil.copy(idir + f, self.work_dir + f)
        hastruth = os.path.isfile(idir + "t.tiff")
        self.cfg['meta']['hastruth'] = hastruth
        if (hastruth):
            shutil.copy(idir + "t.tiff", self.work_dir + "t.tiff")
            shutil.copy(idir + "t.png", self.work_dir + "t.png")

        self.log("input selected : %s" % input_id)
        self.cfg['meta']['original'] = False
        self.cfg['meta']['height'] = image(self.work_dir + '/a.png').size[1]
        self.cfg.save()
        # jump to the params page
        return self.params(msg="(no message)", key=self.key)

    def upload_given_file(self, i, fi):
        """
        upload a file
        """
        file_up = fi
        if '' == file_up.filename:
            # missing file
            return False
        file_save = file(self.work_dir + i, 'wb')
        size = 0
        while True:
            # T O D O larger data size
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
        return True

    @cherrypy.expose
    def input_upload(self, **kwargs):
        """
        use the uploaded input images
        """
        self.new_key()
        self.init_cfg()

        ra = self.upload_given_file('a', kwargs['file_a'])
        rb = self.upload_given_file('b', kwargs['file_b'])
        rt = self.upload_given_file('t.tiff', kwargs['file_t'])

        if not ra:
            return self.error(errcode='badparams',
                         errmsg='(MISSING FIRST IMAGE)')
        if not rb:
            return self.error(errcode='badparams',
                         errmsg='(MISSING SECOND IMAGE)')

        try:
            ima = image(self.work_dir + 'a')
            imb = image(self.work_dir + 'b')
        except IOError:
            return self.error(errcode='badparams',
                     errmsg='(INPUT IMAGE FORMAT ERROR)')

        msg = "no message"


        if self.input_max_pixels and prod(ima.size) > (self.input_max_pixels):
            ima.resize(self.input_max_pixels)
            imb.resize(self.input_max_pixels)
            msg = """The image has been resized
                  for a reduced computation time."""

        if ima.size[0] != imb.size[0] or ima.size[1] != imb.size[1]:
            ss = "%dx%d - %dx%d" % (ima.size[0], ima.size[1],
                           imb.size[0], imb.size[1])
            return self.error(errcode='badparams',
             errmsg='(INPUT IMAGES MUST HAVE THE SAME SIZE %s)'%ss)

        if len(ima.im.getbands()) != len(imb.im.getbands()):
            return self.error(errcode='badparams',
             errmsg='(DO NOT MIX COLOR AND GRAY)')
        if rt:
            sizetruth = subprocess.Popen([self.bin_dir + 'imprintf',
                  '%w %h %c' , self.work_dir + 't.tiff'],
                  stdout=subprocess.PIPE).communicate()[0]
            ts = [int(f) for f in sizetruth.split()]
            if len(ts) != 3 or ts[2] != 2:
                return self.error(errcode='badparam',
                      errmsg='(CAN NOT READ GROUND TRUTH FILE)')
            if ts[0] != ima.size[0] or ts[1] != ima.size[1]:
                return self.error(errcode='badparams',
                  errmsg='(GROUND TRUTH IMAGE HAS DIFFERENT SIZE)')

        ima.save(self.work_dir + 'a.png')
        imb.save(self.work_dir + 'b.png')

        self.log("input uploaded")
        self.cfg['meta']['original'] = True
        self.cfg['meta']['height'] = image(self.work_dir + '/a.png').size[1]
        self.cfg['meta']['hastruth'] = rt

        self.cfg.save()
        # jump to the params page
        return self.params(msg=msg, key=self.key)

    @cherrypy.expose
    def index(self):
        """
        demo presentation and input menu
        """
        print("ENTERING index")
        tn_size = 192
        # read the input index as a dict
        inputd = config.file_dict(self.input_dir)
        print(inputd)
        for (input_id, input_info) in inputd.items():
            fname = ["a.png", "b.png", "t.png"]
            tn_fname = [thumbnail(self.input_dir + \
                 input_info['subdir'] \
                           + '/a.png',(tn_size,tn_size))]
            inputd[input_id]['hastruth'] = os.path.isfile(
                self.input_dir + input_info['subdir']+'/t.tiff')
            inputd[input_id]['height'] = image(self.input_dir
                       + input_info['subdir'] + '/a.png').size[1]
            inputd[input_id]['baseinput'] = \
                self.input_url + input_info['subdir'] + '/'
            inputd[input_id]['url'] = [self.input_url
                            + input_info['subdir']
                    + '/' + os.path.basename(f)
                  for f in fname]
            inputd[input_id]['tn_url'] = [self.input_url
                         + input_info['subdir']
                         + '/'
                         + os.path.basename(f)
                 for f in tn_fname]

        return self.tmpl_out("input.html", inputd=inputd)

    @cherrypy.expose
    @init_app
    def result(self, **kwargs):
        """
        display the algo results
        """
        self.cfg['meta']['height'] = image(self.work_dir + 'a.png').size[1]
        colorwheel = True
        if 'colorwheel' in kwargs:
            colorwheel = "True" == kwargs['colorwheel']
        self.cfg['meta']['colorwheel'] = colorwheel
        return self.tmpl_out("result.html")

    def algo_getruntime(self, a):
        """
        return a string containing the running time of the algorithm
        """
        return subprocess.Popen([self.bin_dir+'cat',
                   self.work_dir+'stuff_'+a+'.time'],
                  stdout=subprocess.PIPE).communicate()[0]

# vim: set ts=8 noexpandtab list:
