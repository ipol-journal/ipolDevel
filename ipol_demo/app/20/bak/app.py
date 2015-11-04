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

    title = "Horn-Schunck Optical Flow with a Multi-Scale Strategy"
    xlink_article = 'http://www.ipol.im/pub/art/2013/20/'

    is_test = False           # switch to False for deployment
    is_listed = True
    is_built = True

    xlink_src = "http://www.ipol.im/pub/art/2013/20/phs_3.tar.gz"
    xlink_src_demo = "http://www.ipol.im/pub/art/2013/20/imscript_dec2011.tar.gz"
    xlink_input = "http://dev.ipol.im/~coco/static/flowpairs.tar.gz"

    parconfig = {}
    parconfig['alpha'] = {'type': float, 'default': 15,
                          'changeable': True,
                          'htmlname': '&alpha;',
                          'archived' : True,
                          'order' : 1,
                          'doc': '(weight of the regularization term, e.g. \
                          &alpha;=1 discontinuous flow, \
                          &alpha;=40 smooth flow)'}
    parconfig['epsil'] = {'type': float, 'default': 0.01,
                          'changeable': False,
                          'htmlname': '&epsilon;',
                          'archived' : False,
                          'order' : 2,
                          'doc': 'stopping rule threshold'}
    parconfig['niter'] = {'type': int, 'default': 150,
                          'changeable': False,
                          'htmlname': 'N<sub><small>iter</small></sub>',
                          'archived' : True,
                          'order' : 3,
                          'doc': 'maximum number of iterations'}
    parconfig['nwarp'] = {'type': int, 'default': 5,
                          'changeable': False,
                          'htmlname': 'N<sub><small>warps</small></sub>',
                          'archived' : True,
                          'order' : 4,
                          'doc': 'number of warps per scale'}
    parconfig['nscal'] = {'type': int, 'default': 100,
                          'changeable': False,
                          'htmlname': 'N<sub><small>scales</small></sub>',
                          'archived' : True,
                          'order' : 5,
                          'doc': 'number of scales'}
    parconfig['sstep'] = {'type': float, 'default': 0.65,
                          'changeable': False,
                          'htmlname': '&eta;',
                          'archived' : True,
                          'order' : 6,
                          'doc': 'scale factor'}
    parconfig['nprocs'] = {'type': int, 'default': 8,
                          'changeable': False,
                           'htmlname': 'N<sub><small>procs</small></sub>',
                          'archived' : False,
                          'order' : 7,
                          'doc': 'openmp'}

    def __init__(self):
        """
        app setup
        """
        # setup the parent class
        base_dir = os.path.dirname(os.path.abspath(__file__))
        base_app.__init__(self, base_dir)

        # select the base_app steps to expose
        # index() is generic
        #app_expose(base_app.index)
        #app_expose(base_app.input_select)
        #app_expose(base_app.input_upload)
        # params() is modified from the template
        #app_expose(base_app.params)
        # run() and result() must be defined here


    def build_algo(self):
        """
        program build/update
        """
        ## store common file path in variables
        tgz_file = self.dl_dir + "phs_3.tar.gz"
        prog_file = self.bin_dir + "phs"
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
            build.run("make -C %s" % (self.src_dir +"phs_3"),
                                                   stdout=log_file)
            # save into bin dir
            #if os.path.isdir(self.bin_dir):
            #        shutil.rmtree(self.bin_dir)
            try:
                shutil.copy(self.src_dir +
                           os.path.join("phs_3", "horn_schunck_pyramidal"), prog_file)
            except IOError, e:
                print("Unable to copy file. %s" % e)
            # cleanup the source dir
            shutil.rmtree(self.src_dir)
        return

    def build_demo(self):
        """
        download and built the demo auxiliary programs
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
            #try:
            for f in glob.glob(os.path.join(self.src_dir,
                                          "imscript", "bin", "*")):
                shutil.copy(f, self.bin_dir)
            #except:
            #   print("some error occurred copying files")
            # cleanup the source dir
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
        try:
            for k in app.parconfig:
                typ = app.parconfig[k]['type']
                self.cfg['param'][k] = typ(kwargs[k])
        except ValueError:
            return self.error(errcode='badparams',
                          errmsg='The parameters must be numeric.')
        #self.cfg.save()
        http.refresh(self.base_url + 'run?key=%s' % self.key)
        self.cfg['meta']['height'] = image(self.work_dir + '/a.png').size[1]
        self.cfg['meta']['colorscheme'] = 'ipoln'
        self.cfg['meta']['colorparam'] = '1'
        self.cfg['meta']['pos_inview'] = False
        return self.tmpl_out("wait.html")

    @cherrypy.expose
    @init_app
    def run(self, **kwargs):
        """
        algo execution
        """
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
            ar.add_file("stuff_phs.tiff", info="")
            ar.add_file("stuff_phs.png", info="")
            if (self.cfg['meta']['hastruth']):
                ar.add_file("t.tiff", info="")
            alist = {}
            for k in app.parconfig:
                if app.parconfig[k]['archived']:
                    alist[k] = self.cfg['param'][k]
            #ar.add_file(".png", info="output")
            ar.add_info(alist)
            ar.save()
        return self.tmpl_out("run.html")


    def run_algo(self):
        """
        the core algo runner
        could also be called by a batch processor
        this one needs no parameter
        """
        nprocs = self.cfg['param']['nprocs']
        alpha = self.cfg['param']['alpha']
        epsil = self.cfg['param']['epsil']
        niter = self.cfg['param']['niter']
        nwarp = self.cfg['param']['nwarp']
        nscal = self.cfg['param']['nscal']
        sstep = self.cfg['param']['sstep']

        p = self.run_proc(['run_method_noview.sh',
             str(nprocs),
             str(alpha),
             str(epsil),
             str(niter),
             str(nwarp),
             str(nscal),
             str(sstep)
            ])
        #q = self.run_proc(['zero_stuff.sh'])
        self.wait_proc(p, timeout=self.timeout)
        p = self.run_proc(['view_method.sh', 'ipoln', '1'])
        self.wait_proc(p, timeout=self.timeout)
        return

    @cherrypy.expose
    @init_app
    def recolor(self, **kwargs):
        """
        update the color scheme
        """
        cs = kwargs['colorscheme']
        ##cp = kwargs['colorparam']
        self.cfg['meta']['colorscheme'] = cs
        self.cfg['meta']['colorwheel'] = True
        p = self.run_proc(['view_method.sh', cs, '1'])
        self.wait_proc(p, timeout=self.timeout)
        return self.tmpl_out("result.html")

    @cherrypy.expose
    @init_app
    def reposition(self, **kwargs):
        """
        scroll the page to the "view" location
        """
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
        self.new_key()
        self.init_cfg()
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

        #fnames = input_dict[input_id]['files'].split()
        #for i in range(len(fnames)):
        #    shutil.copy(self.input_dir + fnames[i],
        #                self.work_dir + 'input_%i' % i)
        #msg = self.process_input()
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
        rt = False
        #rt = self.upload_given_file('t.tiff', kwargs['file_t'])

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
        tn_size = 192
        # read the input index as a dict
        inputd = config.file_dict(self.input_dir)
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
        self.cfg['meta']['height'] = image(self.work_dir + '/a.png').size[1]
        colorwheel = True
        if 'colorwheel' in kwargs:
            colorwheel = "True" == kwargs['colorwheel']
        self.cfg['meta']['colorwheel'] = colorwheel
        return self.tmpl_out("result.html")

    def algo_getruntime(self, a):
        """
        return a string containing the running time of the algorithm
        """
        #return subprocess.check_output([self.bin_dir+'cat',\
        #   self.work_dir+'stuff_'+a+'.time'])
        return subprocess.Popen([self.bin_dir+'cat',
                   self.work_dir+'stuff_'+a+'.time'],
                  stdout=subprocess.PIPE).communicate()[0]
