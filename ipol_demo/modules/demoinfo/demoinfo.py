#!/usr/bin/python
# -*- coding:utf-8 -*-

"""
Demo Info metadata module
Provides a set of stateless JSON webservices

todo: secure webservices
todo: secure db access

to test POST WS:
curl -d demo_id=1  -X POST 'http://127.0.0.1:9002/demo_get_authors_list'

or use Ffox plugin: Poster

"""

import cherrypy
import sys
import errno
import logging

from model import *


#GLOBAL VARS
from tools import is_json, Payload

LOGNAME = "demoinfo_log"



class DemoInfo(object):

	def __init__(self, configfile=None):

		# Cherrypy Conf
		if not configfile:
			sys.exit(1)
		else:
			cherrypy.config.update(configfile)

		status = self.check_config()
		if not status:
			sys.exit(1)

		self.logs_dir = cherrypy.config.get("logs_dir")
		self.mkdir_p(self.logs_dir)
		self.logger = self.init_logging()

		# Database
		self.database_dir = cherrypy.config.get("database_dir")
		self.database_name = cherrypy.config.get("database_name")
		self.database_file = os.path.join(self.database_dir, self.database_name)
		status = createDb(self.database_name)
		if not status:
			sys.exit(1)
		else:
			print "DB created"
		initDb(self.database_name)

		# db testing purposes only!, better use unittests in test folder
		# testDb(self.database_name)

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

		:rtype: bool
		"""
		if not (
				cherrypy.config.has_key("database_dir") and
				cherrypy.config.has_key("database_name") and
				cherrypy.config.has_key("logs_dir") ):
			print "Missing elements in configuration file."
			return False
		else:
			return True


	def init_logging(self):
		"""
		Initialize the error logs of the module.
		"""
		logger = logging.getLogger(LOGNAME)
		logger.setLevel(logging.ERROR)
		handler = logging.FileHandler(os.path.join(self.logs_dir,
												   'error.log'))
		formatter = logging.Formatter('%(asctime)s ERROR in %(message)s',
									  datefmt='%Y-%m-%d %H:%M:%S')
		handler.setFormatter(formatter)
		logger.addHandler(handler)
		return logger


	def error_log(self, function_name, error):
		"""
		Write an error log in the logs_dir defined in archive.conf
		"""
		error_string = function_name + ": " + error
		self.logger.error(error_string)
 

	@cherrypy.expose
	def index(self):
		return ("Welcome to IPOL demoInfo !")


	@cherrypy.expose
	def demo_list(self):
		data = {}
		data["status"] = "KO"
		demo_list=list()
		try:
			conn = lite.connect(self.database_file)
			demo_dao = DemoDAO(conn)
			for d in demo_dao.list():
				#convert to Demo class to json
				demo_list.append(d.__dict__)


			data["demo_list"] = demo_list
			data["status"] = "OK"
			conn.close()
		except Exception as ex:
			print "demo_list  ",str(ex)
			self.error_log("demo_list",str(ex))
			try:
				conn.close()
			except Exception as ex:
				print "demo_list  ",str(ex)

		return json.dumps(data)


	@cherrypy.expose
	def author_list(self):
		data = {}
		data["status"] = "KO"
		author_list=list()
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
			print str(ex)
			self.error_log("author_list",str(ex))
			try:
				conn.close()
			except Exception as ex:
				print str(ex)
		return json.dumps(data)


	@cherrypy.expose
	def editor_list(self):
		data = {}
		data["status"] = "KO"
		editor_list=list()
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
			print str(ex)
			self.error_log("editor_list",str(ex))
			try:
				conn.close()
			except Exception as ex:
				print str(ex)
		return json.dumps(data)


	@cherrypy.expose
	def demo_get_authors_list(self,demo_id):
		data = {}
		data["status"] = "KO"
		author_list=list()
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
			print str(ex)
			self.error_log("demo_get_authors_list",str(ex))
			try:
				conn.close()
			except Exception as ex:
				print str(ex)
		return json.dumps(data)


	@cherrypy.expose
	def author_get_demos_list(self,author_id):
		data = {}
		data["status"] = "KO"
		demo_list=list()
		try:
			conn = lite.connect(self.database_file)
			da_dao = DemoAuthorDAO(conn)

			for d in da_dao.read_author_demos(int(author_id)):
				#convert to Demo class to json
				demo_list.append(d.__dict__)


			data["demo_list"] = demo_list
			data["status"] = "OK"
			conn.close()
		except Exception as ex:
			print str(ex)
			self.error_log("author_get_demos_list",str(ex))
			try:
				conn.close()
			except Exception as ex:
				print str(ex)
		return json.dumps(data)


	@cherrypy.expose
	def demo_get_editors_list(self,demo_id):
		data = {}
		data["status"] = "KO"
		editor_list=list()
		try:
			conn = lite.connect(self.database_file)
			de_dao = DemoEditorDAO(conn)

			for e in de_dao.read_demo_editors(int(demo_id)):
				#convert to Demo class to json
				editor_list.append(e.__dict__)


			data["editor_list"] = editor_list
			data["status"] = "OK"
			conn.close()
		except Exception as ex:
			print str(ex)
			self.error_log("demo_get_authors_list",str(ex))
			try:
				conn.close()
			except Exception as ex:
				print str(ex)
		return json.dumps(data)


	@cherrypy.expose
	def editor_get_demos_list(self,editor_id):
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
			data["status"] = "OK"
			conn.close()
		except Exception as ex:
			print str(ex)
			self.error_log("author_get_demos_list",str(ex))
			try:
				conn.close()
			except Exception as ex:
				print str(ex)
		return json.dumps(data)


	@cherrypy.expose
	@cherrypy.tools.allow(methods=['POST']) #allow only post
	def add_demo_description(self):
		#def add_demo_description(self, demojson):
		#recieves a valid json as a string AS POST DATA
		#http://stackoverflow.com/questions/3743769/how-to-receive-json-in-a-post-request-in-cherrypy

		data = {}
		data["status"] = "KO"

		cl = cherrypy.request.headers['Content-Length']
		rawbody = cherrypy.request.body.read(int(cl))
		# print
		# print "++++ rawbody",rawbody
		# print "++++ is_json",is_json(rawbody)
		# print "++++ rawbody type: ",type(rawbody) #json str
		# print
		# demojson = json.loads(rawbody)
		# print
		# print "++++ demojson: ",demojson
		# print "++++ is_json: ",is_json(demojson)
		# print "++++ demojson type: ",type(demojson) #dict unicode
		# print
		# #http://stackoverflow.com/questions/956867/how-to-get-string-objects-instead-of-unicode-ones-from-json-in-python
		# import yaml
		# demojson = yaml.safe_load(rawbody)
		# print
		# print "++++ demojson: ",demojson
		# print "++++ is_json: ",is_json(demojson)
		# print "++++ demojson type: ",type(demojson) #dict, not unicode
		# print



		demojson=rawbody
		if not is_json(demojson):
			print
			print "add_demo_description demojson is not a valid json "
			print "+++++ demojson: ",demojson
			print "+++++ demojson type: ",type(demojson)
			raise Exception

		try:
			conn = lite.connect(self.database_file)
			dao = DemoDescriptionDAO(conn)
			id = dao.add(demojson)
			conn.close()
			#return id
			data["status"] = "OK"
			data["demo_description_id"] = id

		except Exception as ex:
			error_string=("WS add_demo_description  e:%s"%(str(ex)))
			print (error_string)
			conn.close()
			raise Exception


		return json.dumps(data)


	@cherrypy.expose
	@cherrypy.tools.allow(methods=['POST']) #allow only post
	def update_demo_description(self, demodescriptionID):

		data = {}
		data["status"] = "KO"

		cl = cherrypy.request.headers['Content-Length']
		rawbody = cherrypy.request.body.read(int(cl))
		demojson = rawbody

		if not is_json(demojson):
			print "add_demo_description demojson is not a valid json "
			raise Exception

		try:
			conn = lite.connect(self.database_file)
			dao = DemoDescriptionDAO(conn)
			id = dao.update(int(demodescriptionID),demojson)
			conn.close()
			#return id
			data["status"] = "OK"

		except Exception as ex:
			error_string=("WS add_demo_description  e:%s"%(str(ex)))
			print (error_string)
			conn.close()
			raise Exception


		return json.dumps(data)


	#For unittests and internal use, in other case you should use add_demo_description instead
	#@cherrypy.expose
	#@cherrypy.tools.allow(methods=['POST']) #allow only post
	def add_demo_description_using_param(self, demojson):
		#recieves a valid json as a string AS PARAMETER
		#http://stackoverflow.com/questions/3743769/how-to-receive-json-in-a-post-request-in-cherrypy

		data = {}
		data["status"] = "KO"
		demojson=str(demojson)

		if not is_json(demojson):
			print "add_demo_description_using_param demojson is not a validjson "
			print "+++++ demojson: ",demojson
			print "+++++ demojson type: ",type(demojson)
			raise Exception

		try:
			conn = lite.connect(self.database_file)
			dao = DemoDescriptionDAO(conn)
			id = dao.add(demojson)
			conn.close()
			#return id
			data["status"] = "OK"
			data["demo_description_id"] = id

		except Exception as ex:
			error_string=("WS add_demo_description_using_param  e:%s"%(str(ex)))
			print (error_string)
			conn.close()
			raise Exception

		return json.dumps(data)


	@cherrypy.expose
	def read_demo_description(self, demodescriptionID):
		data = {}
		data["status"] = "KO"
		data["demo_description"] = None
		try:
			id =int(demodescriptionID)
			#print "---- read_demo_description"
			conn = lite.connect(self.database_file)
			dao = DemoDescriptionDAO(conn)
			data["demo_description"] = dao.read(id)
			conn.close()
		except Exception as ex:
			error_string=("WS read_demo_description  e:%s"%(str(ex)))
			print (error_string)
			conn.close()

		return json.dumps(data)

	@cherrypy.expose
	def read_demo(self, demoid):
		demo=None
		try:
			id =int(demoid)
			conn = lite.connect(self.database_file)
			dao = DemoDAO(conn)
			demo = dao.read(id)
			conn.close()
		except Exception as ex:
			error_string=("WS read_demo  e:%s"%(str(ex)))
			print (error_string)
			conn.close()

		return demo

	@cherrypy.expose
	@cherrypy.tools.allow(methods=['POST']) #allow only post
	def add_demo(self,editorsdemoid, title, abstract, zipURL, active, stateID, demodescriptionID=None, demodescriptionJson=None):

		try:

			conn = lite.connect(self.database_file)

			if demodescriptionJson:
				#creates a demodescription and asigns it to demo
				dao = DemoDescriptionDAO(conn)
				id = dao.add(demodescriptionJson)
				d = Demo(int(editorsdemoid), title, abstract, zipURL, int(active), int(stateID), int(id))

			elif demodescriptionID:
				#asigns to demo an existing demodescription
				d = Demo(int(editorsdemoid), title, abstract, zipURL, int(active), int(stateID), int(demodescriptionID))

			else:
				#demo created without demodescription
				d = Demo(int(editorsdemoid), title, abstract, zipURL, int(active), int(stateID))

			dao = DemoDAO(conn)
			dao.add(d)

			conn.close()
		except Exception as ex:
			error_string=("WS add_demo  e:%s"%(str(ex)))
			print (error_string)
			conn.close()
			raise Exception

	@cherrypy.expose
	@cherrypy.tools.allow(methods=['POST']) #allow only post
	def delete_demo(self,demo_id,hard_delete = False):

		try:

			conn = lite.connect(self.database_file)

			if not hard_delete:
				# do not delete, activate /deactivate

				demo_dao = DemoDAO(conn)
				demo_dao.set_active_flag(int(demo_id),int(False))

			else:
				# delete demo and all authors related, do not delete editors, just remove relations

				# We do not need to do this because of the delete on cascade
				# demo_author_dao = DemoAuthorDAO(conn)
				# demo_author_dao.delete_all_authors_for_demo(int(demo_id))
				# demo_editor_dao = DemoEditorDAO(conn)
				# demo_editor_dao.delete_all_editors_for_demo(int(demo_id))

				print
				print "demoid to delete ", demo_id
				demo_dao = DemoDAO(conn)
				#read demo
				demo = demo_dao.read(int(demo_id))

				print "demodescriptionID to delete ", demo.demodescriptionID
				print demo.__dict__
				#delete demo
				demo_dao.delete(int(demo_id))

				#delete demo decription if any
				print "demodescriptionID to delete ", demo.demodescriptionID
				demo_description_dao = DemoDescriptionDAO(conn)
				demo_description_dao.delete(demo.demodescriptionID)



			conn.close()


		except Exception as ex:
			error_string=("WS delete_demo  e:%s"%(str(ex)))
			print (error_string)
			conn.close()
			raise Exception


	@cherrypy.expose
	@cherrypy.tools.allow(methods=['POST']) #allow only post
	def add_author(self,name, mail):
		try:
			a = Author( name, mail)
			conn = lite.connect(self.database_file)
			dao = AuthorDAO(conn)
			dao.add(a)
			conn.close()
		except Exception as ex:
			error_string=("WS add_author  e:%s"%(str(ex)))
			print (error_string)
			conn.close()
			raise Exception


	@cherrypy.expose
	@cherrypy.tools.allow(methods=['POST']) #allow only post
	def add_editor(self,name, mail):
		try:
			e = Editor( name, mail)
			conn = lite.connect(self.database_file)
			dao = EditorDAO(conn)
			dao.add(e)
			conn.close()
		except Exception as ex:
			error_string=("WS add_author  e:%s"%(str(ex)))
			print (error_string)
			conn.close()
			raise Exception


	@cherrypy.expose
	@cherrypy.tools.allow(methods=['POST']) #allow only post
	def add_author_to_demo(self,demo_id ,author_id):
		try:
			conn = lite.connect(self.database_file)
			dao = DemoAuthorDAO(conn)
			dao.add(int(demo_id),int(author_id))
			conn.close()
		except Exception as ex:
			error_string=("WS add_author_to_demo  e:%s"%(str(ex)))
			print (error_string)
			conn.close()
			raise Exception


	@cherrypy.expose
	@cherrypy.tools.allow(methods=['POST']) #allow only post
	def add_editor_to_demo(self,demo_id ,editor_id):
		try:
			conn = lite.connect(self.database_file)
			dao = DemoEditorDAO(conn)
			dao.add(int(demo_id),int(editor_id))
			conn.close()
		except Exception as ex:
			error_string=("WS add_author_to_demo  e:%s"%(str(ex)))
			print (error_string)
			conn.close()
			raise Exception


	@cherrypy.expose
	@cherrypy.tools.allow(methods=['POST']) #allow only post
	def remove_editor_from_demo(self,demo_id ,editor_id):
		try:
			conn = lite.connect(self.database_file)
			dao = DemoEditorDAO(conn)
			dao.remove_editor_from_demo(int(demo_id),int(editor_id))
			conn.close()
		except Exception as ex:
			error_string=("WS add_author_to_demo  e:%s"%(str(ex)))
			print (error_string)
			conn.close()
			raise Exception


	@cherrypy.expose
	@cherrypy.tools.allow(methods=['POST']) #allow only post
	def remove_author_from_demo(self,demo_id ,author_id):
		try:
			conn = lite.connect(self.database_file)
			dao = DemoAuthorDAO(conn)
			dao.remove_author_from_demo(int(demo_id),int(author_id))
			conn.close()
		except Exception as ex:
			error_string=("WS add_author_to_demo  e:%s"%(str(ex)))
			print (error_string)
			conn.close()
			raise Exception


	@cherrypy.expose
	@cherrypy.tools.allow(methods=['POST']) #allow only post
	def update_demo(self,demo):


		#get payload from json object
		p = Payload(demo)
		#convert payload to Author object
		d = Demo(p.editorsdemoid, p.title, p.abstract, p.zipURL, p.active, p.stateID, p.demodescriptionID, p.id, p.creation, p.modification)
		#update Demo
		try:

			conn = lite.connect(self.database_file)
			dao = DemoDAO(conn)
			dao.update(d)
			conn.close()
		except Exception as ex:
			error_string=("WS update_demo  e:%s"%(str(ex)))
			print (error_string)
			conn.close()
			raise Exception



	@cherrypy.expose
	@cherrypy.tools.allow(methods=['POST']) #allow only post
	def update_author(self,author):

		#get payload from json object
		# #{"mail": "authoremail1@gmail.com", "creation": "2015-12-03 20:53:07", "id": 1, "name": "Author Name1"}
		p = Payload(author)

		#convert payload to Author object
		a=Author(p.name,p.mail,p.id,p.creation)

		#update Author
		try:

			conn = lite.connect(self.database_file)
			dao = AuthorDAO(conn)
			dao.update(a)
			conn.close()
		except Exception as ex:
			error_string=("WS update_author  e:%s"%(str(ex)))
			print (error_string)
			conn.close()
			raise Exception


	@cherrypy.expose
	@cherrypy.tools.allow(methods=['POST']) #allow only post
	def update_editor(self,editor):

		#get payload from json object
		p = Payload(editor)
		#convert payload to Author object
		e=Editor(p.name,p.mail,p.id,p.active,p.creation)

		#update Editor
		try:
			conn = lite.connect(self.database_file)
			dao = EditorDAO(conn)
			dao.update(e)
			conn.close()
		except Exception as ex:
			error_string=("WS update_editor  e:%s"%(str(ex)))
			print (error_string)
			conn.close()
			raise Exception


	@cherrypy.expose
	def ping(self):
		data = {}
		data["status"] = "OK"
		data["ping"] = "pong"
		return json.dumps(data)


	#TODO protect THIS
	@cherrypy.expose
	def shutdown(self):
		data = {}
		data["status"] = "KO"
		try:
			cherrypy.engine.exit()
			data["status"] = "OK"
		except Exception as ex:
			self.error_log("shutdown", str(ex))
		return json.dumps(data)


	@cherrypy.expose
	def stats(self):
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
			self.error_log("stats", str(ex))
			try:
				conn.close()
			except Exception as ex:
				pass
		return json.dumps(data)





