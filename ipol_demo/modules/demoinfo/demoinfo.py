#!/usr/bin/python
# -*- coding:utf-8 -*-

"""
DemoInfo: an information container module

All exposed WS return JSON with a status OK/KO, along with an error
description if that's the case.

To test the POST WS use the following:
        curl -d demo_id=1  -X POST 'http://127.0.0.1:9002/demo_get_authors_list'
        curl -d editorsdemoid=777 -d title='demo1' -d
            abstract='demoabstract' -d zipURL='http://prueba.com'  -d
            state=published -X POST 'http://127.0.0.1:9002/add_demo'
        or use Ffox plugin: Poster

"""

import sys
import errno
import logging
import shutil
import json
from math import ceil
import cherrypy
import re
import socket


import ConfigParser

from model import *
from tools import is_json, Payload, convert_str_to_bool

# GLOBAL VARS
LOGNAME = "demoinfo_log"


class DemoInfo(object):
    """
    Implement the demoinfo webservices.
    """

    instance = None

    @staticmethod
    def get_instance():
        '''
        Singleton pattern
        '''
        if DemoInfo.instance is None:
            DemoInfo.instance = DemoInfo()
        return DemoInfo.instance

    def __init__(self):
        """
        Constructor.
        """
        status = self.check_config()
        if not status:
            sys.exit(1)

        self.logs_dir = cherrypy.config.get("logs_dir")
        self.mkdir_p(self.logs_dir)
        self.logger = self.init_logging()

        self.dl_extras_dir = cherrypy.config.get("dl_extras_dir")
        self.mkdir_p(self.dl_extras_dir)
        self.config_common_dir = cherrypy.config.get("config_common_dir")
        self.demoExtrasFilename = cherrypy.config.get("demoExtrasFilename")

        self.server_address = 'http://{0}:{1}'.format(
            cherrypy.config['server.socket_host'],
            cherrypy.config['server.socket_port'])

        # Security: authorized IPs
        self.authorized_patterns = self.read_authorized_patterns()

        # Database
        self.database_dir = cherrypy.config.get("database_dir")
        self.database_name = cherrypy.config.get("database_name")
        self.database_file = os.path.join(self.database_dir, self.database_name)

        # check if DB already exists
        if not os.path.isfile(self.database_name):

            statuscreateDb = createDb(self.database_name)
            if not statuscreateDb:
                print "DB not created correctly"
                sys.exit(1)

            statusinitDb = initDb(self.database_name)
            if not statusinitDb:
                print "DB not initialized correctly"
                sys.exit(1)

    @staticmethod
    def mkdir_p(path):
        """
        Implement the UNIX shell command "mkdir -p"
        with given path as parameter.
        """
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise


    @staticmethod
    def check_config():
        """
        Check if needed datas exist correctly in the config of cherrypy.
        """
        if not (cherrypy.config.has_key("database_dir") and
                cherrypy.config.has_key("database_name") and
                cherrypy.config.has_key("logs_dir")):
            print "Missing elements in configuration file."
            return False
        else:
            return True

    def authenticate(func):
        '''
        Wrapper to authenticate before using an exposed function
        '''
        def authenticate_and_call(*args,**kwargs):
            '''
            Invokes the wrapped function if authenticated
            '''
            if not is_authorized_ip(cherrypy.request.remote.ip) or \
                    ("X-Real-IP" in cherrypy.request.headers and
                         not is_authorized_ip(cherrypy.request.headers["X-Real-IP"])):
                error = {"status": "KO", "error": "Authentication Failed"}
                return json.dumps(error)
            return func(*args,**kwargs)

        def is_authorized_ip(ip):
            '''
            Validates the given IP
            '''
            demo_info = DemoInfo.get_instance()
            patterns = []
            # Creates the patterns  with regular expresions
            for authorized_pattern in demo_info.authorized_patterns:
                patterns.append(re.compile(authorized_pattern.replace(".","\.").replace("*","[0-9]*")))

            # Compare the IP with the patterns
            for pattern in patterns:
                if pattern.match(ip) is not None:
                    return True
            return False


        return authenticate_and_call

    def read_authorized_patterns(self):
        '''
        Read from the IPs conf file
        '''
        # Check if the config file exists
        authorized_patterns_path = os.path.join(self.config_common_dir, "authorized_patterns.conf")
        if not os.path.isfile(authorized_patterns_path):
            self.error_log("read_authorized_patterns",
                           "Can't open {}".format(authorized_patterns_path))
            return []

        # Read config file
        try:
            cfg = ConfigParser.ConfigParser()
            cfg.read([authorized_patterns_path])
            patterns = []
            for item in cfg.items('Patterns'):
                patterns.append(item[1])
            return patterns
        except ConfigParser.Error:
            self.logger.exception("Bad format in {}".format(authorized_patterns_path))
            return []



    def init_logging(self):
        """
        Initialize the error logs of the module.
        """
        logger = logging.getLogger(LOGNAME)
        logger.setLevel(logging.ERROR)
        handler = logging.FileHandler(os.path.join(self.logs_dir, 'error.log'))
        formatter = logging.Formatter('%(asctime)s ERROR in %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger


    def error_log(self, function_name, error):
        """
        Write a message in the error log.
        """
        error_string = function_name + ": " + error
        self.logger.error(error_string)


    # DEMO
    @staticmethod
    @cherrypy.expose
    def default(attr):
        """
        Default method invoked when asked for a non-existing service.
        """
        data = {}
        data["status"] = "KO"
        data["message"] = "Unknown service '{}'".format(attr)
        return json.dumps(data)

    def get_compressed_file_url(self, demo_id):
        """
        Get the URL of the demo's demoExtras
        """

        extras_folder = os.path.join(self.dl_extras_dir, demo_id)
        compressed_file = os.path.join(extras_folder, self.demoExtrasFilename)

        if os.path.isfile(compressed_file):
            return os.path.join(self.server_address,\
                                               self.dl_extras_dir, \
                                               demo_id,\
                                               self.demoExtrasFilename)
        else:
            return None


    @cherrypy.expose
    @authenticate
    def delete_compressed_file_ws(self, demo_id):
        """
        WS for deleting the compressed demo extra file of a demo
        """
        data = {}
        data['status'] = "OK"

        try:
            extras_folder = os.path.join(self.dl_extras_dir, demo_id)
            shutil.rmtree(extras_folder)
        except Exception as ex:
            data['status'] = "KO"
            self.error_log("Failure in delete_compressed_file_ws ", str(ex))
        return json.dumps(data)


    @cherrypy.expose
    @authenticate
    def add_compressed_file_ws(self, demo_id, **kwargs):
        """
        WS for add a new compressed demo extra file to a demo
        """
        data = {}
        data['status'] = "KO"
        given_file = None
        try:
            given_file = kwargs['file_0']
            extra_folder = os.path.join(self.dl_extras_dir, demo_id)

            if given_file is not None:
                if os.path.exists(extra_folder):
                    shutil.rmtree(extra_folder)

                os.makedirs(extra_folder)
                with open(given_file.filename, 'wb') as the_file:
                    shutil.copyfileobj(given_file.file, the_file)
                    os.rename(given_file.name, self.demoExtrasFilename )
                    shutil.move(self.demoExtrasFilename, extra_folder)
                data['status'] = "OK"
            else:
                print "File not found"
        except Exception as ex:
            print ex

        return json.dumps(data)

    @cherrypy.expose
    def get_demo_extras_info(self, demo_id):
        """
        Return the date of creation, the size of the file and the demoExtras file if exists
        """
        try:
            data = {'status':'KO'}
            demoExtras_url = self.get_compressed_file_url(demo_id)
            if demoExtras_url is None:
                # DemoInfo does not have any demoExtras
                return json.dumps({'status':'OK'})

            demoExtras_path = os.path.join(self.dl_extras_dir, demo_id + "/" + self.demoExtrasFilename)
            file_stats = os.stat(demoExtras_path)
            data['date'] = float(file_stats.st_mtime)
            data['size'] = float(file_stats.st_size)
            data['url'] = demoExtras_url
            data['status'] = 'OK'
            return json.dumps(data)

        except Exception as ex:
            self.logger.exception("Failure in get_demo_extras_info")
            print "get_demo_extras_info. Error: {}".format(ex)
            return json.dumps(data)


    #todo check its not usefull any more and delete...remeber deleting from test/demoinfotest.py
    @cherrypy.expose
    def demo_list(self):
        """
        Return the list of the demos of the module.
        """
        data = {}
        data["status"] = "KO"
        demo_list = list()
        try:
            conn = lite.connect(self.database_file)
            demo_dao = DemoDAO(conn)
            for d in demo_dao.list():
                # convert to Demo class to json
                demo_list.append(d.__dict__)
            data["demo_list"] = demo_list
            data["status"] = "OK"
            conn.close()
        except Exception as ex:
            error_string = "demoinfo demo_list error %s" % str(ex)
            print error_string
            self.error_log("demo_list", error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            # raise Exception
            data["error"] = error_string

        return json.dumps(data)


    @cherrypy.expose
    def demo_list_by_demoeditorid(self, demoeditorid_list):
        """
        return demo metainformation from list of demo editor id.
        """

        data = {}
        data["status"] = "KO"
        demo_list = list()

        #get json list into python object
        if is_json(demoeditorid_list):
            demoeditorid_list = json.loads(demoeditorid_list)
        else:
            raise ValueError("demoeditorid_list is not a valid JSON")

        try:
            conn = lite.connect(self.database_file)
            demo_dao = DemoDAO(conn)
            for d in demo_dao.list():
                #convert to Demo class to json
                if d.editorsdemoid in demoeditorid_list:
                    demo_list.append(d.__dict__)

            data["demo_list"] = demo_list
            data["status"] = "OK"
            conn.close()
        except Exception as ex:
            error_string = "demoinfo demo_list_by_demoeditorid error %s" % str(ex)
            print error_string
            self.error_log("demo_list_by_demoeditorid", error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            #raise Exception
            data["error"] = error_string

        return json.dumps(data)

    @cherrypy.expose
    def demo_list_pagination_and_filter(self, num_elements_page, page, qfilter=None):
        """
        return a paginated and filtered list of demos
        """
        data = {}
        data["status"] = "KO"
        demo_list = list()
        next_page_number = None
        previous_page_number = None

        try:

            #validate params
            num_elements_page = int(num_elements_page)
            page = int(page)
            # print "demo_list_pagination_and_filter"
            # print "num_elements_page",num_elements_page
            # print "page",page
            # print "qfilter",qfilter
            # print

            conn = lite.connect(self.database_file)
            demo_dao = DemoDAO(conn)

            complete_demo_list = demo_dao.list()

            #filter or return all
            if qfilter:
                for demo in complete_demo_list:
                    #print "demo: ",demo
                    if (qfilter.lower() in demo.title.lower()
                            or qfilter.lower() in demo.abstract.lower()
                                or qfilter == str(demo.editorsdemoid)):
                        demo_list.append(demo.__dict__)
            else:
                #convert to Demo class to json
                for demo in complete_demo_list:
                    demo_list.append(demo.__dict__)

            # print
            # print " demo_list",demo_list
            # print
            # print " demo_list",len(demo_list)

            #if demos found, return pagination
            if demo_list:

                # [ToDo] Check if the first float cast r=float(.) is
                # really needed. It seems not, because the divisor is
                # already a float and thus the result must be a float.
                r = float(len(demo_list)) /  float(num_elements_page)

                totalpages = int(ceil(r))

                if page is None:
                    page = 1
                else:
                    if page < 1:
                        page = 1
                    elif page > totalpages:
                        page = totalpages

                next_page_number = page + 1
                if next_page_number > totalpages:
                    next_page_number = None

                previous_page_number = page - 1
                if previous_page_number <= 0:
                    previous_page_number = None


                start_element = (page - 1) * num_elements_page

                demo_list = demo_list[start_element: start_element+num_elements_page]

                # print " totalpages: ",totalpages
                # print " page: ",page
                # print " next_page_number: ",next_page_number
                # print " previous_page_number: ",previous_page_number
                # print " start_element: ", start_element
                # print " demo_list",demo_list

            else:
                totalpages = None


            data["demo_list"] = demo_list
            data["next_page_number"] = next_page_number
            data["number"] = totalpages
            data["previous_page_number"] = previous_page_number
            data["status"] = "OK"
            conn.close()
        except Exception as ex:
            error_string = "demoinfo demo_list_pagination_and_filter error %s" % str(ex)
            print error_string
            self.error_log("demo_list_pagination_and_filter", error_string)
            try:
                conn.close() # [ToDo] It seems that this should do in a
                # finally clause, not in a nested try. Check all similar
                # cases in this file.
            except Exception as ex:
                pass
            #raise Exception
            data["error"] = error_string
        return json.dumps(data)


    @cherrypy.expose
    @authenticate
    def demo_get_authors_list(self, demo_id):
        """
        return the list of authors of a given demo.
        """
        data = {}
        data["status"] = "KO"
        author_list = list()
        try:
            conn = lite.connect(self.database_file)
            da_dao = DemoAuthorDAO(conn)

            for a in da_dao.read_demo_authors(int(demo_id)):
                #convert to Demo class to json
                author_list.append(a.__dict__)


            data["author_list"] = author_list
            data["status"] = "OK"
            conn.close()
        except Exception as ex:
            error_string = "demoinfo demo_get_authors_list error %s" % str(ex)
            print error_string
            self.error_log("demo_get_authors_list", error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            #raise Exception
            data["error"] = error_string
        return json.dumps(data)


    @cherrypy.expose
    @authenticate
    def demo_get_available_authors_list(self, demo_id):
        """
        return the list of all authors that are not currently assigned to a given demo.
        """
        data = {}
        data["status"] = "KO"
        available_author_list = list()

        try:
            conn = lite.connect(self.database_file)

            # get all available authors
            a_dao = AuthorDAO(conn)
            list_of_all_authors = a_dao.list()

            # get the authors of this demo
            da_dao = DemoAuthorDAO(conn)
            list_of_authors_assigned_to_this_demo = da_dao.read_demo_authors(int(demo_id))

            for a in list_of_all_authors:
                if a not in list_of_authors_assigned_to_this_demo:
                    #convert to Demo class to json
                    available_author_list.append(a.__dict__)


            data["author_list"] = available_author_list
            data["status"] = "OK"
            conn.close()
        except Exception as ex:
            error_string = "demoinfo demo_get_available_authors_list error %s" % str(ex)
            print error_string
            self.error_log("demo_get_available_authors_list", error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            #raise Exception
            data["error"] = error_string
        return json.dumps(data)


    @cherrypy.expose
    @authenticate
    def demo_get_editors_list(self, demo_id):
        """
        return the editors of a given demo.
        """
        data = {}
        data["status"] = "KO"
        editor_list = list()
        try:
            conn = lite.connect(self.database_file)
            de_dao = DemoEditorDAO(conn)

            for e in de_dao.read_demo_editors(int(demo_id)):
                #convert to Demo class to json
                editor_list.append(e.__dict__)


            data["editor_list"] = editor_list
            conn.close()
            data["status"] = "OK"
        except Exception as ex:
            error_string = "demoinfo demo_get_editors_list error %s" % str(ex)
            print error_string
            self.error_log("demo_list", error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            #raise Exception
            data["error"] = error_string
        return json.dumps(data)


    @cherrypy.expose
    @authenticate
    def demo_get_available_editors_list(self, demo_id):
        """
        return all editors that are not currently assigned to a given demo
        """
        data = {}
        data["status"] = "KO"
        available_editor_list = list()

        try:
            conn = lite.connect(self.database_file)

            # get all available editors
            a_dao = EditorDAO(conn)
            list_of_all_editors = a_dao.list()

            # get the editors of this demo
            da_dao = DemoEditorDAO(conn)
            list_of_editors_assigned_to_this_demo = da_dao.read_demo_editors(int(demo_id))

            for a in list_of_all_editors:
                if a not in list_of_editors_assigned_to_this_demo:
                    #convert to Demo class to json
                    available_editor_list.append(a.__dict__)

            data["editor_list"] = available_editor_list
            data["status"] = "OK"
            conn.close()
        except Exception as ex:
            error_string = "demoinfo demo_get_available_editors_list error %s" % str(ex)
            print error_string
            self.error_log("demo_get_available_editors_list", error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            #raise Exception
            data["error"] = error_string
        return json.dumps(data)


    @cherrypy.expose
    def demo_get_demodescriptions_list(self, demo_id, returnjsons=None):
        """
        return the descriptions of a given demo id.
        """
        data = {}
        data["status"] = "KO"
        demodescription_list = list()
        try:
            #read all _demodescription for this demo
            conn = lite.connect(self.database_file)
            dd_dao = DemoDemoDescriptionDAO(conn)

            if returnjsons is None:
                demodescription_list = dd_dao.read_demo_demodescriptions(int(demo_id))
            else:
                demodescription_list = dd_dao.read_demo_demodescriptions(int(demo_id),
                                                                         returnjsons=returnjsons)

            data["demodescription_list"] = demodescription_list
            data["status"] = "OK"
            conn.close()

        except Exception as ex:
            error_string = "demoinfo demo_get_demodescriptions_list error %s" % str(ex)
            print error_string
            self.error_log("demo_get_demodescriptions_list", error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            #raise Exception
            data["error"] = error_string
        return json.dumps(data)


    def read_demo(self, demoid):
        """
        Return DAO for given demo.
        """
        demo = None
        try:
            the_id = int(demoid)
            conn = lite.connect(self.database_file)
            dao = DemoDAO(conn)
            demo = dao.read(the_id)
            conn.close()

        except Exception as ex:
            error_string = ("read_demo  e:%s"%(str(ex)))
            print error_string
            conn.close()

        return demo


    def read_demo_by_editordemoid(self, editor_demo_id):
        """
        return the demo DAO from a given association between editor and demo.
        """
        demo = None
        try:
            editordemoid = int(editor_demo_id)
            conn = lite.connect(self.database_file)
            dao = DemoDAO(conn)
            demo = dao.read_by_editordemoid(editordemoid)
            conn.close()

        except Exception as ex:
            error_string = ("read_demo_by_editordemoid  e:%s"%(str(ex)))
            print error_string
            conn.close()

        return demo


    @cherrypy.expose
    def read_demo_metainfo(self, demoid):
        """
        return metainfo of given demo.
        """
        data = dict()
        data["status"] = "KO"
        try:

            demo = self.read_demo(demoid)
            if demo is None:
                raise ValueError("No demo retrieved for this id")
            # data["id"] = demo.id
            data["editorsdemoid"] = demo.editorsdemoid
            data["title"] = demo.title
            data["abstract"] = demo.abstract
            data["zipURL"] = demo.zipURL
            data["state"] = demo.state
            data["creation"] = demo.creation
            data["modification"] = demo.modification
            data["status"] = "OK"

        except Exception as ex:
            error_string = "demoinfo read_demo_metainfo error %s" % str(ex)
            print error_string
            self.error_log("read_demo_metainfo", error_string)
            #raise Exception
            data["error"] = error_string

        return json.dumps(data)

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST']) #allow only post
    @authenticate
    def add_demo(self, editorsdemoid, title, abstract, zipURL, state,
                 demodescriptionID=None, demodescriptionJson=None):
        """
        Allows you to create a demo:
        - only creating the demo
        - creating the demo and assigning an existing ddl (with id demodescriptionID) to it
        - create the demo and create a ddl , whith the json passed by param (demodescriptionJson)
        """
        data = {}
        data["status"] = "KO"

        try:
            conn = lite.connect(self.database_file)
            dao = DemoDAO(conn)

            if demodescriptionJson:
                # print "demodescriptionJson"
                #creates a demodescription and asigns it to demo
                dddao = DemoDescriptionDAO(conn)
                demodescriptionID = dddao.add(demodescriptionJson)
                d = Demo(int(editorsdemoid), title, abstract, zipURL, state)
                editorsdemoid = dao.add(d)
                dddao = DemoDemoDescriptionDAO(conn)
                dddao.add(int(editorsdemoid), int(demodescriptionID))

            elif demodescriptionID:
                # print "demodescriptionID"
                #asigns to demo an existing demodescription
                d = Demo(int(editorsdemoid), title, abstract, zipURL, state)
                editorsdemoid = dao.add(d)
                ddddao = DemoDemoDescriptionDAO(conn)
                ddddao.add(int(editorsdemoid), int(demodescriptionID))

            else:
                #demo created without demodescription
                #careful with Demo init method's validation!
                d = Demo(editorsdemoid=int(editorsdemoid), title=title, abstract=abstract,
                         zipurl=zipURL, state=str(state))

                demoid = dao.add(d)

            conn.close()

            data["status"] = "OK"
            data["demoid"] = demoid
        except Exception as ex:
            error_string = " demoinfo add_demo error %s" % str(ex)
            print error_string
            self.error_log("add_demo", error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            #raise Exception
            data["error"] = error_string

        return json.dumps(data)


    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST']) #allow only post
    @authenticate
    def delete_demo(self, demo_id):
        """
        webservice deleting given demo.
        """
        data = {}
        data["status"] = "KO"

        try:

            conn = lite.connect(self.database_file)

            demo_dao = DemoDAO(conn)
            #read demo
            demo = demo_dao.read(int(demo_id))

            dd_dao = DemoDemoDescriptionDAO(conn)
            
            #delete demo decription history borra ddl id 3
            #d_dd con id 2 , y demoid=2, demodescpid 3 deberia no estar
            dd_dao.delete_all_demodescriptions_for_demo(int(demo_id))
            #delete demo, and delete on cascade demodemodescription
            demo_dao.delete(int(demo_id))
            data["status"] = "OK"
            conn.close()

        except Exception as ex:
            error_string = "demoinfo delete_demo error %s" % str(ex)
            print error_string
            self.error_log("delete_demo", error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            #raise Exception
            data["error"] = error_string

        return json.dumps(data)


    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST']) #allow only post
    @authenticate
    def update_demo(self, demo, old_editor_demoid):
        """
        webservice updating demo.
        """
        data = {}
        data["status"] = "KO"
        #get payload from json object
        p = Payload(demo)

        if hasattr(p, 'creation'):
            #update creatio ndate

            d = Demo(p.editorsdemoid, p.title, p.abstract, p.zipURL, p.state, p.creation)
        else:
            d = Demo(p.editorsdemoid, p.title, p.abstract, p.zipURL, p.state)
        #update Demo
        try:

            conn = lite.connect(self.database_file)
            dao = DemoDAO(conn)
            dao.update(d, int(old_editor_demoid))
            conn.close()

            if old_editor_demoid != p.editorsdemoid \
                    and os.path.isdir(os.path.join(self.dl_extras_dir, str(old_editor_demoid))):
                if os.path.isdir(os.path.join(self.dl_extras_dir, str(p.editorsdemoid))):
                    # If the destination path exists, it should be removed
                    shutil.rmtree(os.path.join(self.dl_extras_dir, str(p.editorsdemoid)))

                os.rename(os.path.join(self.dl_extras_dir, str(old_editor_demoid)),
                          os.path.join(self.dl_extras_dir, str(p.editorsdemoid)))

            data["status"] = "OK"
        except OSError as ex:
            data["error"] = "demoinfo update_demo error".format(ex)
        except Exception as ex:
            error_string = (" demoinfo update_demo error %s"%(str(ex)))
            print error_string
            try:
                conn.close()
            except Exception as ex:
                pass
            #raise Exception
            data["error"] = error_string


        return json.dumps(data)


    # AUTHOR


    #todo check its not usefull any more and delete...
    @cherrypy.expose
    @authenticate
    def author_list(self):
        """
        webservice returning list of authors.
        """
        data = {}
        data["status"] = "KO"
        author_list = list()
        try:
            conn = lite.connect(self.database_file)
            author_dao = AuthorDAO(conn)
            for a in author_dao.list():
                #convert to Demo class to json
                author_list.append(a.__dict__)


            data["author_list"] = author_list
            data["status"] = "OK"
            conn.close()
        except Exception as ex:
            error_string = "demoinfo author_list error %s" % str(ex)
            print error_string
            self.error_log("author_list", error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            #raise Exception
            data["error"] = error_string
        return json.dumps(data)


    @cherrypy.expose
    @authenticate
    def author_list_pagination_and_filter(self, num_elements_page, page,
                                          qfilter=None):
        """
        webservice returning paginated and filtered list of authors.
        """
        data = {}
        data["status"] = "KO"
        author_list = list()
        next_page_number = None
        previous_page_number = None

        try:

            #validate params
            num_elements_page = int(num_elements_page)
            page = int(page)

            conn = lite.connect(self.database_file)
            author_dao = AuthorDAO(conn)

            complete_author_list = author_dao.list()

            #filter or return all
            if qfilter:
                for a in complete_author_list:
                    #print "demo: ", demo
                    if qfilter.lower() in a.name.lower() or qfilter.lower() in a.mail.lower():
                        author_list.append(a.__dict__)
            else:
                #convert to Demo class to json
                for a in complete_author_list:
                    author_list.append(a.__dict__)

            #if demos found, return pagination
            if author_list:

                r = float(len(author_list)) / float(num_elements_page)

                totalpages = int(ceil(r))

                if page is None:
                    page = 1
                else:
                    if page < 1:
                        page = 1
                    elif page > totalpages:
                        page = totalpages

                next_page_number = page + 1
                if next_page_number > totalpages:
                    next_page_number = None

                previous_page_number = page - 1
                if previous_page_number <= 0:
                    previous_page_number = None

                start_element = (page - 1) * num_elements_page
                author_list = author_list[start_element: start_element + num_elements_page]
            else:
                totalpages = None


            data["author_list"] = author_list
            data["next_page_number"] = next_page_number
            data["number"] = totalpages
            data["previous_page_number"] = previous_page_number
            data["status"] = "OK"
            conn.close()
        except Exception as ex:
            error_string = "demoinfo author_list_pagination_and_filter error %s" % str(ex)
            print error_string
            self.error_log("author_list_pagination_and_filter", error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            #raise Exception
            data["error"] = error_string

        return json.dumps(data)


    @cherrypy.expose
    @authenticate
    def read_author(self, authorid):
        """
        webservice returning info on author from id in database.
        """
        data = dict()
        data["status"] = "KO"

        try:

            author = None
            try:
                authorid = int(authorid)
                conn = lite.connect(self.database_file)
                dao = AuthorDAO(conn)
                author = dao.read(authorid)
                conn.close()
            except Exception as ex:
                error_string = ("read_author  e:%s" % (str(ex)))
                print error_string
                #raise ValueError(error_string)

            if author is None:
                raise ValueError("No author retrieved for this id")

            data["id"] = author.id
            data["name"] = author.name
            data["mail"] = author.mail
            data["creation"] = author.creation
            data["status"] = "OK"

        except Exception as ex:
            error_string = "demoinfo read_author error %s" % str(ex)
            print error_string
            self.error_log("read_author", error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            #raise Exception
            data["error"] = error_string

        return json.dumps(data)


    @cherrypy.expose
    def author_get_demos_list(self, author_id):
        """
        webservice returning list of demo associated to a given author.
        """
        data = {}
        data["status"] = "KO"
        demo_list = list()
        try:
            conn = lite.connect(self.database_file)
            da_dao = DemoAuthorDAO(conn)

            for d in da_dao.read_author_demos(int(author_id)):
                #convert to Demo class to json
                demo_list.append(d.__dict__)


            data["demo_list"] = demo_list
            conn.close()
            data["status"] = "OK"

        except Exception as ex:
            error_string = "demoinfo author_get_demos_list error %s" % str(ex)
            print error_string
            self.error_log("author_get_demos_list", error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            #raise Exception
            data["error"] = error_string
        return json.dumps(data)


    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST', 'GET']) #allow only post
    @authenticate
    def add_author(self, name, mail):
        """
        webservice adding author entry.
        """
        data = {}
        data["status"] = "KO"
        try:
            a = Author(name, mail)
            conn = lite.connect(self.database_file)
            dao = AuthorDAO(conn)
            the_id = dao.add(a)
            conn.close()
            data["status"] = "OK"
            data["authorid"] = the_id
        except Exception as ex:
            error_string = "demoinfo add_author error %s" % str(ex)
            print error_string
            self.error_log("add_author", error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            #raise Exception
            data["error"] = error_string
        return json.dumps(data)


    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST']) #allow only post
    @authenticate
    def add_author_to_demo(self, demo_id, author_id):
        """
        webservice adding author to demo.
        """
        data = {}
        data["status"] = "KO"
        try:
            conn = lite.connect(self.database_file)
            dao = DemoAuthorDAO(conn)
            dao.add(int(demo_id), int(author_id))
            conn.close()
            data["status"] = "OK"
        except Exception as ex:
            error_string = "demoinfo add_author_to_demo error %s" % str(ex)
            print error_string
            self.error_log("add_author_to_demo", error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            #raise Exception
            data["error"] = error_string
        return json.dumps(data)

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST']) #allow only post
    @authenticate
    def remove_author_from_demo(self, demo_id, author_id):
        """
        webservice removing given author of given demo.
        """
        data = {}
        data["status"] = "KO"
        try:
            conn = lite.connect(self.database_file)
            dao = DemoAuthorDAO(conn)
            dao.remove_author_from_demo(int(demo_id), int(author_id))
            conn.close()
            data["status"] = "OK"
        except Exception as ex:
            error_string = "demoinfo remove_author_from_demo error %s" % str(ex)
            print error_string
            self.error_log("remove_author_from_demo", error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            #raise Exception
            data["error"] = error_string
        return json.dumps(data)


    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST']) #allow only post
    @authenticate
    def remove_author(self, author_id):
        """
        deleting given author, and its relationship with demos
        """
        data = {}
        data["status"] = "KO"
        try:

            authorid = int(author_id)

            conn = lite.connect(self.database_file)
            dadao = DemoAuthorDAO(conn)
            #deletes the author relation with its demos
            demolist = dadao.read_author_demos(authorid)
            if demolist:
                #remove author from demos
                for demo in demolist:
                    dadao.remove_author_from_demo(demo.editorsdemoid, authorid)

            #deletes the author
            adao = AuthorDAO(conn)
            adao.delete(authorid)

            conn.close()
            data["status"] = "OK"
        except Exception as ex:
            error_string = "demoinfo remove_author error %s" % str(ex)
            print error_string
            self.error_log("remove_author", error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            #raise Exception
            data["error"] = error_string
        return json.dumps(data)


    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST']) #allow only post
    @authenticate
    def update_author(self, author):
        """
        webservice updating author entry.
        """
        data = {}
        data["status"] = "KO"
        #get payload from json object
        # #{"mail": "authoremail1@gmail.com", "creation": "2015-12-03 20:53:07",
             # "id": 1, "name": "Author Name1"}
        p = Payload(author)

        #convert payload to Author object
        if hasattr(p, 'creation'):
            a = Author(p.name, p.mail, p.id, p.creation)
        else:
            a = Author(p.name, p.mail, p.id)

        #update Author
        try:

            conn = lite.connect(self.database_file)
            dao = AuthorDAO(conn)
            dao.update(a)
            conn.close()
            data["status"] = "OK"
        except Exception as ex:
            error_string = "demoinfo update_author error %s" % str(ex)
            print error_string
            self.error_log("update_author", error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            #raise Exception
            data["error"] = error_string
        return json.dumps(data)


    # EDITOR


    @cherrypy.expose
    @authenticate
    def editor_list(self):
        """
        webservice returning editor list
        """
        data = {}
        data["status"] = "KO"
        editor_list = list()
        try:
            conn = lite.connect(self.database_file)
            editor_dao = EditorDAO(conn)
            for e in editor_dao.list():
                #convert to Demo class to json
                editor_list.append(e.__dict__)


            data["editor_list"] = editor_list
            data["status"] = "OK"
            conn.close()
        except Exception as ex:
            error_string = "demoinfo editor_list error %s" % str(ex)
            print error_string
            self.error_log("editor_list", error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            #raise Exception
            data["error"] = error_string
        return json.dumps(data)


    @cherrypy.expose
    @authenticate
    def editor_list_pagination_and_filter(self, num_elements_page, page,
                                          qfilter=None):
        """
        webservice returning paginated and filtered list of editor
        """
        data = {}
        data["status"] = "KO"
        editor_list = list()
        next_page_number = None
        previous_page_number = None

        try:

            #validate params
            num_elements_page = int(num_elements_page)
            page = int(page)

            conn = lite.connect(self.database_file)
            editor_dao = EditorDAO(conn)

            complete_editor_list = editor_dao.list()

            #filter or return all
            if qfilter:
                for a in complete_editor_list:
                    #print "demo: ", demo
                    if qfilter.lower() in a.name.lower() or qfilter.lower() in a.mail.lower():
                        editor_list.append(a.__dict__)
            else:
                #convert to Demo class to json
                for a in complete_editor_list:
                    editor_list.append(a.__dict__)

            #if demos found, return pagination
            if editor_list:

                r = float(len(editor_list)) / float(num_elements_page)

                totalpages = int(ceil(r))

                if page is None:
                    page = 1
                else:
                    if page < 1:
                        page = 1
                    elif page > totalpages:
                        page = totalpages

                next_page_number = page + 1
                if next_page_number > totalpages:
                    next_page_number = None

                previous_page_number = page - 1
                if previous_page_number <= 0:
                    previous_page_number = None

                start_element = (page - 1) * num_elements_page
                editor_list = editor_list[start_element: start_element + num_elements_page]
            else:
                totalpages = None


            data["editor_list"] = editor_list
            data["next_page_number"] = next_page_number
            data["number"] = totalpages
            data["previous_page_number"] = previous_page_number
            data["status"] = "OK"
            conn.close()
        except Exception as ex:
            error_string = "demoinfo editor_list_pagination_and_filter error %s" % str(ex)
            print error_string
            self.error_log("editor_list_pagination_and_filter", error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            #raise Exception
            data["error"] = error_string

        return json.dumps(data)


    @cherrypy.expose
    def editor_get_demos_list(self, editor_id):
        """
        webservice getting a list of demo associated to given editor.
        """
        data = {}
        data["status"] = "KO"
        demo_list = list()
        try:
            conn = lite.connect(self.database_file)
            de_dao = DemoEditorDAO(conn)

            for d in de_dao.read_editor_demos(int(editor_id)):
                #convert to Demo class to json
                demo_list.append(d.__dict__)

            data["demo_list"] = demo_list
            conn.close()
            data["status"] = "OK"
        except Exception as ex:
            error_string = "demoinfo editor_get_demos_list error %s" % str(ex)
            print error_string
            self.error_log("editor_get_demos_list", error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            #raise Exception
            data["error"] = error_string
        return json.dumps(data)


    @cherrypy.expose
    @authenticate
    def read_editor(self, editorid):
        """
        webservice getting info of editor from id.
        """
        data = dict()
        data["status"] = "KO"

        try:
            editor = None
            try:
                editorid = int(editorid)
                conn = lite.connect(self.database_file)
                dao = EditorDAO(conn)
                editor = dao.read(editorid)
                conn.close()
            except Exception as ex:
                error_string = ("read_editor  e:%s" % (str(ex)))
                print error_string
                #raise ValueError(error_string)

            if editor is None:
                raise ValueError("No editor retrieved for this id")

            data["id"] = editor.id
            data["name"] = editor.name
            data["mail"] = editor.mail
            data["creation"] = editor.creation
            data["status"] = "OK"

        except Exception as ex:
            error_string = "demoinfo read_editor error %s" % str(ex)
            print error_string
            self.error_log("read_editor", error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            #raise Exception
            data["error"] = error_string

        return json.dumps(data)


    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST']) #allow only post
    @authenticate
    def add_editor(self, name, mail):
        """
        webservice adding editor entry.
        """
        data = {}
        data["status"] = "KO"
        try:
            e = Editor(name, mail)
            conn = lite.connect(self.database_file)
            dao = EditorDAO(conn)
            the_id = dao.add(e)
            conn.close()
            data["status"] = "OK"
            data["editorid"] = the_id
        except Exception as ex:
            error_string = "demoinfo add_editor error %s" % str(ex)
            print error_string
            self.error_log("add_editor", error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            #raise Exception
            data["error"] = error_string
        return json.dumps(data)


    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST']) #allow only post
    @authenticate
    def add_editor_to_demo(self, demo_id, editor_id):
        """
        webservice adding given editor to given demo.
        """
        data = {}
        data["status"] = "KO"
        try:
            conn = lite.connect(self.database_file)
            dao = DemoEditorDAO(conn)
            dao.add(int(demo_id), int(editor_id))
            conn.close()
            data["status"] = "OK"
        except Exception as ex:
            error_string = "demoinfo add_editor_to_demo error %s" % str(ex)
            print error_string
            self.error_log("add_editor_to_demo", error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            #raise Exception
            data["error"] = error_string
        return json.dumps(data)


    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST']) #allow only post
    @authenticate
    def remove_editor_from_demo(self, demo_id, editor_id):
        """
        webservice removing given editor from given demo.
        """
        data = {}
        data["status"] = "KO"
        try:
            conn = lite.connect(self.database_file)
            dao = DemoEditorDAO(conn)
            dao.remove_editor_from_demo(int(demo_id), int(editor_id))
            conn.close()
            data["status"] = "OK"
        except Exception as ex:
            error_string = "demoinfo remove_editor_from_demo error %s" % str(ex)
            print error_string
            self.error_log("remove_editor_from_demo", error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            #raise Exception
            data["error"] = error_string
        return json.dumps(data)


    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST']) #allow only post
    @authenticate
    def remove_editor(self, editor_id):
        """
        webservice deleting editor and its relationship with the demos
        """

        data = {}
        data["status"] = "KO"
        try:

            editorid = int(editor_id)
            conn = lite.connect(self.database_file)
            dedao = DemoEditorDAO(conn)
            #deletes the author relation with its demos
            demolist = dedao.read_editor_demos(editorid)
            if demolist:
                #remove editor from demos
                for demo in demolist:
                    dedao.remove_editor_from_demo(demo.editorsdemoid, editorid)
            #deletes the editor
            edao = EditorDAO(conn)
            edao.delete(editorid)
            conn.close()
            data["status"] = "OK"
        except Exception as ex:
            error_string = "demoinfo remove_editor error %s" % str(ex)
            print error_string
            self.error_log("remove_editor", error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            #raise Exception
            data["error"] = error_string
        return json.dumps(data)


    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST']) #allow only post
    @authenticate
    def update_editor(self, editor):
        """
        webservice updating editor entry in db.
        """
        data = {}
        data["status"] = "KO"
        #get payload from json object
        p = Payload(editor)
        #convert payload to Editor object
        if hasattr(p, 'creation'):
            e = Editor(p.name, p.mail, p.id, p.creation)
        else:
            e = Editor(p.name, p.mail, p.id)

        #update Editor
        try:
            conn = lite.connect(self.database_file)
            dao = EditorDAO(conn)
            dao.update(e)
            conn.close()
            data["status"] = "OK"
        except Exception as ex:
            error_string = "demoinfo update_editor error %s" % str(ex)
            print error_string
            self.error_log("update_editor", error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            #raise Exception
            data["error"] = error_string
        return json.dumps(data)


    # DDL


    @cherrypy.expose
    def read_demo_description(self, demodescriptionID):
        """
        webservice getting demo description.
        """
        data = {}
        data["status"] = "KO"
        data["demo_description"] = None
        try:
            id = int(demodescriptionID)
            #print "---- read_demo_description"
            conn = lite.connect(self.database_file)
            dao = DemoDescriptionDAO(conn)

            ddl = dao.read(id)
            ddl = str(ddl)
            
            data["demo_description"] = ddl
            conn.close()
            data["status"] = "OK"
        except Exception as ex:
            error_string = "demoinfo read_demo_description error %s" % str(ex)
            print error_string
            self.error_log("read_demo_description", error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            #raise Exception
            data["error"] = error_string

        return json.dumps(data)

    @cherrypy.expose
    def get_interface_ddl(self, demo_id):
        """
        Service getting the DDL of a given demo. It returns the ddl without private fields
        """
        try:
            ddl = self.get_stored_ddl(demo_id)
            ddl = json.loads(ddl["ddl"])
            del ddl['build']
            del ddl['run']
            return json.dumps({'status':'OK', 'last_demodescription': {"ddl": json.dumps(ddl)}})
        except Exception as ex:
            error_string = "Failure in function get_interface_ddl, Error = {}".format(ex)
            print error_string
            self.logger.exception(error_string)
            return json.dumps({'status':'KO', 'error': error_string})
    
    @cherrypy.expose
    @authenticate
    def get_ddl(self, demo_id):
        """
        Service getting last description of the demo.
        """
        try:
            ddl = self.get_stored_ddl(demo_id)
            return json.dumps({'status':'OK', 'last_demodescription': ddl})
        except Exception as ex:
            error_string = "Failure in function get_ddl, Error = {}".format(ex)
            print error_string
            self.logger.exception(error_string)
            return json.dumps({'status':'KO'})

    def get_stored_ddl(self, demo_id):
        """
        Method that gives the stored DDL given a demo_id
        """
        conn = lite.connect(self.database_file)
        dd_dao = DemoDemoDescriptionDAO(conn)
        last_demodescription = dd_dao.get_ddl(int(demo_id))
        conn.close()
        return last_demodescription
      
    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST']) #allow only post
    @authenticate
    def save_demo_description(self, demoid):
        """
        Save the demo description.
        """
        #def save_demo_description(self, demoid):
        #recieves a valid json as a string AS POST DATA
        #stackoverflow.com/questions/3743769/how-to-receive-json-in-a-post-request-in-cherrypy

        data = {}
        data["status"] = "KO"

        cl = cherrypy.request.headers['Content-Length']
        ddl = cherrypy.request.body.read(int(cl))

        if not is_json(ddl):
            print
            print "save_demo_description ddl is not a valid json "
            print "+++++ ddl: ", ddl
            print "+++++ ddl type: ", type(ddl)
            raise Exception

        try:
            conn = lite.connect(self.database_file)
            demo_dao = DemoDAO(conn)
            state = demo_dao.read(int(demoid)).state
            if not state == "published": # If the demo is not published the DDL is overwritten
                dao = DemoDemoDescriptionDAO(conn)
                demodescription = dao.get_ddl(int(demoid))
                del dao
                dao = DemoDescriptionDAO(conn)
                
                if demodescription is None: # Check if is a new demo
                    demodescription_id = dao.add(ddl)
                    
                    dao = DemoDemoDescriptionDAO(conn)
                    dao.add(int(demoid), int(demodescription_id))
                else:
                    dao.update(ddl, demoid)
                 
            else:           #Otherwise it's create a new one
                dao = DemoDescriptionDAO(conn)
                demodescription_id = dao.add(ddl)
                dao = DemoDemoDescriptionDAO(conn)
                dao.add(int(demoid), int(demodescription_id))

            data["added_to_demo_id"] = demoid

            conn.close()
            #return id
            data["status"] = "OK"

        except Exception as ex:
            error_string = "demoinfo save_demo_description error %s" % str(ex)
            print error_string
            self.error_log("save_demo_description", error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            #raise Exception
            data["error"] = error_string


        return json.dumps(data)



    # MISCELLANEA

    @staticmethod
    @cherrypy.expose
    def index():
        """
        index of the module.
        """
        return "Welcome to IPOL demoInfo !"

    @staticmethod
    @cherrypy.expose
    def ping():
        """
        Return a simple information. Meant to check if the module is running.
        """
        data = {}
        data["status"] = "OK"
        data["ping"] = "pong"
        return json.dumps(data)


    #TODO protect THIS
    @cherrypy.expose
    @authenticate
    def shutdown(self):
        """
        shutdown the module.
        """
        data = {}
        data["status"] = "KO"
        try:
            cherrypy.engine.exit()
            data["status"] = "OK"
        except Exception as ex:
            self.error_log("shutdown", str(ex))
        return json.dumps(data)


    #todo hide sql
    @cherrypy.expose
    def stats(self):
        """
        return the count demos, authors and editors.
        """
        data = {}
        data["status"] = "KO"
        try:
            conn = lite.connect(self.database_file)
            cursor_db = conn.cursor()
            cursor_db.execute("""
            SELECT COUNT(*) FROM demo""")
            data["nb_demos"] = cursor_db.fetchone()[0]
            cursor_db.execute("""
            SELECT COUNT(*) FROM author""")
            data["nb_authors"] = cursor_db.fetchone()[0]
            cursor_db.execute("""
            SELECT COUNT(*) FROM editor""")
            data["nb_editors"] = cursor_db.fetchone()[0]
            conn.close()
            data["status"] = "OK"
        except Exception as ex:
            error_string = "demoinfo stats error %s" % str(ex)
            print error_string
            self.error_log("stats", error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            #raise Exception
            data["error"] = error_string
        return json.dumps(data)


    #todo hide sql
    @cherrypy.expose
    def read_states(self):
        """
        Returns the list of defined demo states.
        """
        data = {}
        state_list = list()
        data["status"] = "KO"
        try:
            conn = lite.connect(self.database_file)
            cursor_db = conn.cursor()
            cursor_db.execute('''SELECT s.name FROM state as s ''')
            conn.commit()
            for row in cursor_db.fetchall():
                s = (row[0], row[0])
                state_list.append(s)

            conn.close()

            data["status"] = "OK"
            data["state_list"] = state_list
        except Exception as ex:
            error_string = "demoinfo read_states error %s" % str(ex)
            print error_string
            self.error_log("read_states", error_string)
            try:
                conn.close()
            except Exception as ex:
                pass
            #raise Exception
            data["error"] = error_string
        return json.dumps(data)

