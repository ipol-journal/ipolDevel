# -*- coding:utf-8 -*-

import os
import sqlite3 as lite
import datetime
import json
from validoot import validates, inst, typ, between, regex, And, len_between, Or, url, email_address

"""
DATA MODEL

This module will encapsulate all the DB operations, It has the creation scrript,  DAOs to encapsulte sql and , 
a few helper clases that represent the objects modeld in the DB that will be used by the webservices, 
this way I can work with python objects not with queries.

It would be nice to replace all this by orm ,security etc...for example see:
https://groups.google.com/forum/#!topic/cherrypy-users/mpi58-AbBJU
But it has been decided not to use one because of the small scope of the problem

"""


#####################
#  helper clases    #
#####################

class Demo(object):

	editorsdemoid = None
	title = None
	abstract = None
	zipURL = None
	active = None
	stateID = None
	id = None
	creation = None
	modification = None

	@validates(editorsdemoid=typ(int),
	           title=inst(basestring),
	           abstract=inst(basestring),
	           #zipurl=type(url),
	           zipurl=inst(basestring),
	           active=typ(int),
	           stateid=typ(int),
	           id= Or(typ(int) , inst(basestring) ),
	           creation= Or(typ(datetime.datetime) , inst(basestring) ),
	           modification= Or(typ(datetime.datetime) , inst(basestring) )
	           )
	def __init__(self, editorsdemoid, title, abstract, zipurl, active, stateid, id=None, creation=None, modification=None ):

		self.editorsdemoid = editorsdemoid
		self.title = title
		self.abstract = abstract
		self.zipURL = zipurl
		self.active = active
		self.stateID = stateid

		if id:
			self.id = id
		if creation:
			self.creation = creation
		else:
			self.creation = datetime.datetime.now()
		if modification:
			self.modification = modification
		else:
			self.modification = datetime.datetime.now()

	def __eq__(self, other):
		return self.__dict__ == other.__dict__

class Author(object):
	id = None
	name = None
	mail = None
	creation = None
	# And(inst(basestring),len_between(4,100)),
	@validates(
		name=inst(basestring),
		#mail=regex("[^@]+@[^@]+\.[^@]+"),
	    mail=type(email_address),
	    id= Or(typ(int) , inst(basestring) ),
	    creation= Or(typ(datetime.datetime) , inst(basestring) )
	)
	def __init__(self, name, mail, id=None, creation=None):
		self.id = id
		self.name = name
		self.mail = mail
		if creation:
			self.creation = creation
		else:
			self.creation = datetime.datetime.now()


	def __eq__(self, other):
		# print "eq"
		# print self.__dict__
		# print other.__dict__
		return self.__dict__ == other.__dict__

class Editor(object):
	id = None
	name = None
	mail = None
	active = None
	creation = None

	@validates(
		name=inst(basestring),
		#mail=regex("[^@]+@[^@]+\.[^@]+"),
	    mail=type(email_address),
	    id= Or(typ(int) , inst(basestring) ),
		active=typ(int),
	    creation= Or(typ(datetime.datetime) , inst(basestring) )
	)
	def __init__(self, name, mail, id=None, active=None, creation=None):

		self.name = name
		self.mail = mail
		self.id = id
		self.active = active
		if creation:
			self.creation = creation
		else:
			self.creation = datetime.datetime.now()

	def __eq__(self, other):
		return self.__dict__ == other.__dict__

###########################
#  DAO (data access obj ) #
###########################

class DemoDescriptionDAO(object):
	def __init__(self, conn):
		self.conn = conn
		self.cursor = conn.cursor()
		self.cursor.execute(""" PRAGMA foreign_keys=ON""")

	def __del__(self):
		pass

	# conn.close()

	#@validates(inst(Demo))
	def add(self, demojson,inproduction = None):
		try:
			if inproduction is None:
				self.cursor.execute('''INSERT INTO demodescription (json) VALUES(?)''',(demojson,))
			else:
				self.cursor.execute('''INSERT INTO demodescription (json,inproduction) VALUES(?,?)''',(demojson,int(inproduction)))
			self.conn.commit()
			return self.cursor.lastrowid
		except Exception as ex:
			error_string = ("add demo_description  e:%s" % (str(ex)))
			print (error_string)
			raise Exception(error_string)


	@validates(typ(int))
	def delete(self, demo_description_id):
		try:
			self.cursor.execute("DELETE FROM demodescription WHERE id=?", (int(demo_description_id),))
			self.conn.commit()
		except Exception as ex:
			error_string = ("delete_demo_description  e:%s" % (str(ex)))
			print (error_string)
			raise Exception(error_string)


	#@validates(inst(Demo))
	def update(self, demo_description_id,demojson):
		# demojson is a json str (json.dumps(jsonpythondict))
		# carefull doubly-encoding JSON strings

		try:
			self.cursor.execute('''UPDATE demodescription SET json=? WHERE id=?''', (demojson, demo_description_id))
			self.conn.commit()
		except Exception as ex:
			error_string = ("update demo_description  e:%s" % (str(ex)))
			print (error_string)
			raise Exception(error_string)

	@validates(typ(int))
	def read(self, id):
		result = None
		try:
			self.cursor.execute('''SELECT  json,inproduction  FROM demodescription WHERE id=?''',(int(id),))
			self.conn.commit()
			row = self.cursor.fetchone()
			if row:
				result = (row[0],row[1])
		except Exception as ex:
			error_string = ("read demo_description  e:%s" % (str(ex)))
			print (error_string)
		return result


class DemoDAO(object):
	def __init__(self, conn):
		self.conn = conn
		self.cursor = conn.cursor()
		self.cursor.execute(""" PRAGMA foreign_keys=ON""")

	def __del__(self):
		pass

	# conn.close()

	@validates(inst(Demo))
	def add(self, demo):
		try:

			# print 'demo.editorsdemoid: ',demo.editorsdemoid
			# print 'demo.title: ',demo.title
			# print 'demo.abstract: ',demo.abstract
			# print 'demo.zipURL: ',demo.zipURL
			# print 'demo.active: ',demo.active
			# print 'demo.stateID: ',demo.stateID
			# print 'demo.demodescriptionID: ',demo.demodescriptionID
			self.cursor.execute('''
			INSERT INTO demo(editor_demo_id, title, abstract, zipURL,active, stateID) VALUES(?,?,?,?,?,?)''',
			                    (
			                    demo.editorsdemoid, demo.title, demo.abstract, demo.zipURL,  demo.active, demo.stateID,))
			self.conn.commit()
			return self.cursor.lastrowid
		except Exception as ex:
			error_string = (" DAO add_demo e:%s" % (str(ex)))
			print (error_string)
			raise ValueError(error_string)

	@validates(typ(int))
	def delete(self, demo_id):
		try:
			self.cursor.execute("DELETE FROM demo WHERE demo.id=?", (int(demo_id),))
			self.conn.commit()
		except Exception as ex:
			error_string = ("delete_demo  e:%s" % (str(ex)))
			print (error_string)
			raise Exception(error_string)


	@validates(typ(int), And(typ(int), between(0, 1, True, True)))
	def set_active_flag(self, demo_id, active_flag):

		nowtmstmp = datetime.datetime.now()
		try:
			self.cursor.execute('''
			UPDATE demo SET active=?,modification=? WHERE demo.id=?''',
			                    (active_flag, nowtmstmp, demo_id))
			self.conn.commit()
		except Exception as ex:
			error_string = ("set_active_flag  e:%s" % (str(ex)))
			print (error_string)
			raise Exception(error_string)

	@validates(inst(Demo))
	def update(self, demo):

		try:

			nowtmstmp = datetime.datetime.now()
			# print nowtmstmp
			# #nowtmstmp =datetime.datetime.strptime(nowtmstmp, '%Y-%m-%d %H:%M:%S.%fZ')
			# #print nowtmstmp
			# from django.core.serializers.json import json, DjangoJSONEncoder
			# nowtmstmp=json.dumps(nowtmstmp, cls=DjangoJSONEncoder)
			# print nowtmstmp
			# nowtmstmp=demo.creation
			# print nowtmstmp
			# datetime.strptime('2015-02-25T12:58:01.548Z', '%Y-%m-%dT%H:%M:%S.%fZ')

			if demo.creation:

				self.cursor.execute('''
				UPDATE demo SET editor_demo_id=?,title=?, abstract=?, zipURL=?,active=?,stateID=?,modification=?,creation=? WHERE demo.id=?''',
				                    (demo.editorsdemoid, demo.title, demo.abstract, demo.zipURL, demo.active, demo.stateID ,nowtmstmp,demo.creation, demo.id))

			else:
				self.cursor.execute('''
				UPDATE demo SET editor_demo_id=?,title=?, abstract=?, zipURL=?,active=?,stateID=?,modification=?,creation=? WHERE demo.id=?''',
				                    (demo.editorsdemoid, demo.title, demo.abstract, demo.zipURL, demo.active,demo.stateID,nowtmstmp, demo.creation, demo.id))
			self.conn.commit()
		except Exception as ex:
			error_string = ("update_demo  e:%s" % (str(ex)))
			print (error_string)
			raise Exception(error_string)

	@validates(typ(int))
	def read(self, id):
		result = None
		try:
			self.cursor.execute(
				'''SELECT  editor_demo_id, title, abstract, zipURL, active, stateID, id, creation, modification  FROM demo WHERE demo.id=?''',
				(int(id),))

			self.conn.commit()
			row = self.cursor.fetchone()
			if row:
				d = Demo(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8])
				result = d
		except Exception as ex:
			error_string = ("read_demo  e:%s" % (str(ex)))
			print (error_string)
		return result

	@validates(typ(int))
	def read_by_editordemoid(self, editordemoid):

		print "editordemoid: ",editordemoid
		result = None
		try:
			self.cursor.execute(
				'''SELECT  editor_demo_id, title, abstract, zipURL, active, stateID, id, creation, modification  FROM demo WHERE demo.editor_demo_id=?''',
				(int(editordemoid),))

			self.conn.commit()
			row = self.cursor.fetchone()
			if row:
				d = Demo(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8])
				result = d
		except Exception as ex:
			error_string = ("read_by_editordemoid  e:%s" % (str(ex)))
			print (error_string)
		return result

	def list(self, is_active=True):

		demo_list = list()
		try:
			if is_active:
				self.cursor.execute(
					'''SELECT editor_demo_id, title, abstract, zipURL, active, stateID, id, creation, modification  FROM demo WHERE active = 1 ORDER BY id DESC ''')
			else:
				self.cursor.execute(
					'''SELECT editor_demo_id, title, abstract, zipURL, active, stateID, id, creation, modification  FROM demo WHERE active = 0 ORDER BY id DESC ''')
			self.conn.commit()
			for row in self.cursor.fetchall():
				d = Demo(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8])
				demo_list.append(d)

		except Exception as ex:
			error_string = ("list_demos  e:%s" % (str(ex)))
			print (error_string)
		return demo_list


class DemoDemoDescriptionDAO(object):
	def __init__(self, conn):
		self.conn = conn
		self.cursor = conn.cursor()
		self.cursor.execute(""" PRAGMA foreign_keys=ON""")

	def __del__(self):
		pass

	# conn.close()

	@validates(typ(int), typ(int))
	def add(self, demoid, demodescriptionid):
		try:

			self.cursor.execute('''
			INSERT INTO demo_demodescription(demoID, demodescriptionID) VALUES(?,?)''',
			                    (int(demoid), int(demodescriptionid),))
			self.conn.commit()

		except Exception as ex:
			error_string = ("add_demo_demodescription  e:%s" % (str(ex)))
			print (error_string)
			raise Exception(error_string)

	@validates(typ(int))
	def delete(self, id):
		try:
			self.cursor.execute("DELETE FROM demo_demodescription WHERE id=?", (int(id),))
			self.conn.commit()
		except Exception as ex:
			error_string = ("delete_demo_demodescription  e:%s" % (str(ex)))
			print (error_string)
			raise Exception(error_string)

	@validates(typ(int))
	def delete_all_demodescriptions_for_demo(self, demoid):
		try:
			#self.cursor.execute("DELETE FROM demo_demodescription WHERE demoID=?", (int(demoid),))
			#self.cursor.execute("DELETE FROM demodescription WHERE demoID=?", (int(demoid),))
			self.cursor.execute("DELETE FROM demodescription WHERE ID in (select demodescriptionid from demo_demodescription where demoID=?)", (int(demoid),))
			self.conn.commit()
		except Exception as ex:
			error_string = ("delete_all_demodescriptions_for_demo  e:%s" % (str(ex)))
			print (error_string)
			raise Exception(error_string)


	@validates(typ(int), typ(int))
	def remove_demodescription_from_demo(self, demoid, demodescriptionid):
		try:
			self.cursor.execute("DELETE FROM demo_demodescription WHERE demoID=? AND demodescriptionID=?", (int(demoid), int(demodescriptionid),))
			self.conn.commit()
		except Exception as ex:
			error_string = ("remove_editor_from_demo  e:%s" % (str(ex)))
			print (error_string)
			raise Exception(error_string)


	@validates(typ(int))
	def read(self, id):

		result = None
		try:
			self.cursor.execute('''SELECT id,demoID,demodescriptionID FROM demo_demodescription WHERE id=?''', (int(id),))
			self.conn.commit()
			row = self.cursor.fetchone()
			if row:
				result = {'id': row[0], 'demoID': row[1], 'editorId': row[2]}

		except Exception as ex:
			error_string = ("read_demo_editor  e:%s" % (str(ex)))
			print (error_string)
		return result


	@validates(typ(int))
	def read_last_demodescription_from_demo(self, demoid,returnjsons=None):

		result = None
		# print
		# print "   +++++++ read_last_demodescription_from_demo"
		# print type(returnjsons)
		try:

			if returnjsons == True or returnjsons == 'True':

				self.cursor.execute(
					'''SELECT ddl.ID,ddl.inproduction,dd.creation,ddl.JSON FROM demo_demodescription as dd, demodescription as ddl
					WHERE  dd.demodescriptionID=ddl.ID and dd.demoID=? ORDER BY ddl.ID DESC LIMIT 1''',
					(int(demoid),))
				self.conn.commit()
				row = self.cursor.fetchone()
				if row:
					result = {'id': row[0], 'inproduction': row[1], 'creation': row[2], 'json': row[3]}
			else:
				self.cursor.execute(
					'''SELECT ddl.ID,ddl.inproduction,dd.creation FROM demo_demodescription as dd, demodescription as ddl
					WHERE  dd.demodescriptionID=ddl.ID and dd.demoID=? ORDER BY ddl.ID DESC LIMIT 1''',
					(int(demoid),))
				self.conn.commit()
				row = self.cursor.fetchone()
				if row:
					result = {'id': row[0], 'inproduction': row[1], 'creation': row[2]}

		except Exception as ex:
			error_string = ("read_last_demodescription_from_demo  e:%s" % (str(ex)))
			print (error_string)
		return result


	@validates(typ(int))
	def read_demodescrption_demos(self, demodescriptionid):
		#todo only one or more then one?
		demo_list = list()
		try:
			self.cursor.execute('''SELECT d.editor_demo_id, d.title, d.abstract, d.zipURL, d.active, d.stateID, d.id, d.creation, d.modification
				FROM demo as d, demo_demodescription as dd WHERE d.id=dd.demoId and dd.demodescriptionID=?''', (int(demodescriptionid),))
			self.conn.commit()
			for row in self.cursor.fetchall():
				d = Demo(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8])
				demo_list.append(d)

		except Exception as ex:
			error_string = ("read_editor_demos  e:%s" % (str(ex)))
			print (error_string)
		return demo_list	\


	@validates(typ(int))
	def read_demo_demodescriptions(self, demoid, returnjsons=None):
		#returns ordered list, by default does not return jsons

		demodescription_list = list()
		try:
			if returnjsons == True or returnjsons == 'True':
				self.cursor.execute(
					'''SELECT ddl.ID,ddl.inproduction,dd.creation,ddl.JSON FROM demo_demodescription as dd, demodescription as ddl
					WHERE  dd.demodescriptionID=ddl.ID and dd.demoID=? ORDER BY ddl.ID DESC''',
					(int(demoid),))
				self.conn.commit()
				for row in self.cursor.fetchall():
					ddl = (row[0], row[1], row[2], row[3])
					demodescription_list.append(ddl)
			else:
				self.cursor.execute(
					'''SELECT ddl.ID,ddl.inproduction,dd.creation FROM demo_demodescription as dd, demodescription as ddl
					WHERE  dd.demodescriptionID=ddl.ID and dd.demoID=? ORDER BY ddl.ID DESC''',
					(int(demoid),))
				self.conn.commit()
				for row in self.cursor.fetchall():
					ddl = (row[0], row[1], row[2])
					demodescription_list.append(ddl)
		except Exception as ex:
			error_string = ("read_demo_demodescriptions  e:%s" % (str(ex)))
			print "read_demo_demodescriptions e: ",error_string
		return demodescription_list


class AuthorDAO(object):
	def __init__(self, conn):
		self.conn = conn
		self.cursor = conn.cursor()
		self.cursor.execute(""" PRAGMA foreign_keys=ON""")

	def __del__(self):
		pass

	# conn.close()

	@validates(inst(Author))
	def add(self, author):
		try:
			# todo validate user input
			self.cursor.execute('''
			INSERT INTO author(name, mail) VALUES(?,?)''',
			                    (author.name, author.mail,))
			self.conn.commit()
			return self.cursor.lastrowid

		except Exception as ex:
			error_string = ("add_author,  %s " % (str(ex)))
			print (error_string)
			raise Exception(error_string)

	@validates(typ(int))
	def delete(self, id):

		try:
			self.cursor.execute("DELETE FROM author WHERE id=?", (int(id),))
			self.conn.commit()
		except Exception as ex:
			error_string = ("delete_author  e:%s" % (str(ex)))
			print (error_string)
			raise Exception(error_string)

	@validates(inst(Author))
	def update(self, author):
		try:

			# todo validate user input
			if author.creation:
				self.cursor.execute('''
				UPDATE author SET name=?, mail=?,creation=? WHERE id=?''',
				                    (author.name, author.mail, author.creation, author.id))
			else:
				self.cursor.execute('''
				UPDATE author SET name=?, mail=? WHERE id=?''',
				                    (author.name, author.mail, author.id))
			self.conn.commit()
		except Exception as ex:
			error_string = ("update_author  e:%s" % (str(ex)))
			print (error_string)
			raise Exception(error_string)

	@validates(typ(int))
	def read(self, id):
		result = None
		try:
			self.cursor.execute('''SELECT  name, mail,id, creation FROM author WHERE id=?''', (int(id),))
			self.conn.commit()
			row = self.cursor.fetchone()
			if row:
				a = Author(row[0], row[1], row[2], row[3])
				result = a
		except Exception as ex:
			error_string = ("read_author  e:%s" % (str(ex)))
			print (error_string)
		return result

	def list(self):
		author_list = list()
		try:
			self.cursor.execute('''SELECT name, mail,id, creation FROM author ORDER BY id DESC ''')
			self.conn.commit()
			for row in self.cursor.fetchall():
				a = Author(row[0], row[1], row[2], row[3])
				author_list.append(a)

		except Exception as ex:
			error_string = ("list_author  e:%s" % (str(ex)))
			print (error_string)
		return author_list


class DemoAuthorDAO(object):
	"""
	This class implements database management
	The database architecture is defined in file /db/blob.sql
	One instance of this object represents one connection to the database

			 demoID INTEGER,
			autorId INTEGER,

	"""

	def __init__(self, conn):
		self.conn = conn
		self.cursor = conn.cursor()
		self.cursor.execute(""" PRAGMA foreign_keys=ON""")

	def __del__(self):
		pass

	# conn.close()

	@validates(typ(int), typ(int))
	def add(self, demoid, authorid):
		try:
			self.cursor.execute('''
			INSERT INTO demo_author(demoID, authorId) VALUES(?,?)''',
			                    (int(demoid), int(authorid),))
			self.conn.commit()

		except Exception as ex:
			error_string = ("add_demo_author  e:%s" % (str(ex)))
			print (error_string)
			raise Exception(error_string)

	@validates(typ(int))
	def delete(self, id):
		try:
			self.cursor.execute("DELETE FROM demo_author WHERE id=?", (int(id),))
			self.conn.commit()
		except Exception as ex:
			error_string = ("delete_demo_author  e:%s" % (str(ex)))
			print (error_string)
			raise Exception(error_string)

	@validates(typ(int))
	def delete_all_authors_for_demo(self, demoid):
		try:
			self.cursor.execute("DELETE FROM demo_author WHERE demoID=?", (int(demoid),))
			self.conn.commit()
		except Exception as ex:
			error_string = ("delete_all_authors_for_demo  e:%s" % (str(ex)))
			print (error_string)
			raise Exception(error_string)

	@validates(typ(int), typ(int))
	def remove_author_from_demo(self, demoid, authorid):
		try:
			self.cursor.execute("DELETE FROM demo_author WHERE demoID=? AND authorId=?", (int(demoid), int(authorid),))
			self.conn.commit()
		except Exception as ex:
			error_string = ("remove_author_from_demo  e:%s" % (str(ex)))
			print (error_string)
			raise Exception(error_string)

	@validates(typ(int))
	def read(self, id):
		result = None
		try:
			self.cursor.execute('''SELECT id,demoID, authorId FROM demo_author WHERE id=?''', (int(id),))
			self.conn.commit()
			row = self.cursor.fetchone()
			if row:
				result = {'id': row[0], 'demoID': row[1], 'authorId': row[2]}

		except Exception as ex:
			error_string = ("read_demo_author  e:%s" % (str(ex)))
			print (error_string)
		return result

	@validates(typ(int))
	def read_author_demos(self, authorid):
		demo_list = list()
		try:
			self.cursor.execute('''SELECT d.editor_demo_id, d.title, d.abstract, d.zipURL, d.active, d.stateID, d.id, d.creation, d.modification
				FROM demo as d, demo_author as da WHERE d.id=da.demoId and da.authorId=?''', (int(authorid),))
			self.conn.commit()
			for row in self.cursor.fetchall():
				d = Demo(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8])
				demo_list.append(d)

		except Exception as ex:
			error_string = ("read_author_demos  e:%s" % (str(ex)))
			print (error_string)
		return demo_list

	@validates(typ(int))
	def read_demo_authors(self, demoid):
		author_list = list()
		try:
			self.cursor.execute(
				'''SELECT a.name, a.mail,a.id, a.creation FROM author as a, demo_author as da WHERE a.id=da.authorId and da.demoID=?''',
				(int(demoid),))
			self.conn.commit()
			for row in self.cursor.fetchall():
				a = Author(row[0], row[1], row[2], row[3])
				author_list.append(a)

		except Exception as ex:
			error_string = ("read_demo_authors  e:%s" % (str(ex)))
			print (error_string)
		return author_list


class EditorDAO(object):
	def __init__(self, conn):
		self.conn = conn
		self.cursor = conn.cursor()
		self.cursor.execute(""" PRAGMA foreign_keys=ON""")

	def __del__(self):
		pass

	# conn.close()

	@validates(inst(Editor))
	def add(self, editor):
		try:
			# todo validate user input
			self.cursor.execute('''
			INSERT INTO editor(name, mail) VALUES(?,?)''',
			                    (editor.name, editor.mail,))
			self.conn.commit()
			return self.cursor.lastrowid
		except Exception as ex:
			error_string = ("add_editor  e:%s" % (str(ex)))
			print (error_string)
			raise Exception(error_string)

	@validates(typ(int))
	def delete(self, id):
		try:
			self.cursor.execute("DELETE FROM editor WHERE id=?", (int(id),))
			self.conn.commit()
		except Exception as ex:
			error_string = ("delete_editor  e:%s" % (str(ex)))
			print (error_string)
			raise Exception(error_string)

	@validates(inst(Editor))
	def update(self, editor):

		try:

			# todo validate user input
			if editor.creation:
				self.cursor.execute('''
				UPDATE editor SET name=?, mail=?,active=?,creation=? WHERE id=?''',
				                    (editor.name, editor.mail, editor.active, editor.creation, editor.id))
			else:
				self.cursor.execute('''
				UPDATE editor SET name=?, mail=?,active=? WHERE id=?''',
				                    (editor.name, editor.mail, editor.active, editor.id))
			self.conn.commit()
		except Exception as ex:
			error_string = ("update_editor  e:%s" % (str(ex)))
			print (error_string)
			raise Exception(error_string)

	@validates(typ(int))
	def read(self, id):
		try:
			self.cursor.execute('''SELECT name, mail, id, active, creation FROM editor WHERE id=?''', (int(id),))
			# name, mail, id=None,active=None, creation=None):
			self.conn.commit()
			row = self.cursor.fetchone()

		except Exception as ex:
			error_string = ("read_editor  e:%s" % (str(ex)))
			print (error_string)
		return Editor(row[0], row[1], row[2], row[3], row[4])

	def list(self):
		editor_list = list()
		try:
			# name, mail, id=None,active=None, creation=
			self.cursor.execute('''SELECT  name, mail,  id, active, creation FROM editor ORDER BY id DESC ''')
			self.conn.commit()
			for row in self.cursor.fetchall():
				e = Editor(row[0], row[1], row[2], row[3], row[4])
				# print 'editor list'
				# print e.__dict__
				editor_list.append(e)

		except Exception as ex:
			error_string = ("list_editor  e:%s" % (str(ex)))
			print (error_string)
		return editor_list


class DemoEditorDAO(object):
	def __init__(self, conn):
		self.conn = conn
		self.cursor = conn.cursor()
		self.cursor.execute(""" PRAGMA foreign_keys=ON""")

	def __del__(self):
		pass

	# conn.close()

	@validates(typ(int), typ(int))
	def add(self, demoid, editorid):
		try:

			self.cursor.execute('''
			INSERT INTO demo_editor(demoID, editorId) VALUES(?,?)''',
			                    (int(demoid), int(editorid),))
			self.conn.commit()

		except Exception as ex:
			error_string = ("add_demo_editor  e:%s" % (str(ex)))
			print (error_string)
			raise Exception(error_string)

	@validates(typ(int))
	def delete(self, id):
		try:
			self.cursor.execute("DELETE FROM demo_editor WHERE id=?", (int(id),))
			self.conn.commit()
		except Exception as ex:
			error_string = ("delete_demo_editor  e:%s" % (str(ex)))
			print (error_string)
			raise Exception(error_string)

	@validates(typ(int))
	def delete_all_editors_for_demo(self, demoid):
		try:
			self.cursor.execute("DELETE FROM demo_editor WHERE demoID=?", (int(demoid),))
			self.conn.commit()
		except Exception as ex:
			error_string = ("delete_all_editors_for_demo  e:%s" % (str(ex)))
			print (error_string)
			raise Exception(error_string)

	@validates(typ(int), typ(int))
	def remove_editor_from_demo(self, demoid, editorid):
		try:
			self.cursor.execute("DELETE FROM demo_editor WHERE demoID=? AND editorId=?", (int(demoid), int(editorid),))
			self.conn.commit()
		except Exception as ex:
			error_string = ("remove_editor_from_demo  e:%s" % (str(ex)))
			print (error_string)
			raise Exception(error_string)

	@validates(typ(int))
	def read(self, id):

		result = None
		try:
			self.cursor.execute('''SELECT id,demoID, editorId FROM demo_editor WHERE id=?''', (int(id),))
			self.conn.commit()
			row = self.cursor.fetchone()
			if row:
				result = {'id': row[0], 'demoID': row[1], 'editorId': row[2]}

		except Exception as ex:
			error_string = ("read_demo_editor  e:%s" % (str(ex)))
			print (error_string)
		return result

	@validates(typ(int))
	def read_editor_demos(self, editorid):
		demo_list = list()
		try:
			self.cursor.execute('''SELECT d.editor_demo_id, d.title, d.abstract, d.zipURL, d.active, d.stateID, d.id, d.creation, d.modification
				FROM demo as d, demo_editor as de WHERE d.id=de.demoId and de.editorId=?''', (int(editorid),))
			self.conn.commit()
			for row in self.cursor.fetchall():
				d = Demo(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8])
				demo_list.append(d)

		except Exception as ex:
			error_string = ("read_editor_demos  e:%s" % (str(ex)))
			print (error_string)
		return demo_list

	@validates(typ(int))
	def read_demo_editors(self, demoid):
		editor_list = list()
		try:
			# self.cursor.execute('''SELECT id,demoID, editorId FROM demo_editor WHERE demoID=?''', (int(demoid),))
			self.cursor.execute(
				'''SELECT e.name, e.mail,e.id, e.active,e.creation FROM editor as e, demo_editor as de WHERE e.id=de.editorId and de.demoID=?''',
				(int(demoid),))
			self.conn.commit()
			for row in self.cursor.fetchall():
				e = Editor(row[0], row[1], row[2], row[3], row[4])
				editor_list.append(e)

		except Exception as ex:
			error_string = ("read_demo_editors  e:%s" % (str(ex)))
			print (error_string)
		return editor_list


###########################
#    DB setup functions   #
###########################

def createDb(database_name):
	"""
	Initialize the database used by the module if it doesn't exist.

	:return: False if there was an error. True otherwise.
	:rtype: bool
	"""
	status = True
	dbname = database_name

	if not os.path.isfile(dbname):

		try:
			conn = lite.connect(dbname)
			cursor_db = conn.cursor()
			cursor_db.execute(""" PRAGMA foreign_keys=ON""")

			cursor_db.execute(
				"""CREATE TABLE IF NOT EXISTS "state" (
				ID INTEGER PRIMARY KEY AUTOINCREMENT,
				name VARCHAR(500),
				description TEXT,
				creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				UNIQUE(name)
				);"""
			)
			cursor_db.execute(
				"""CREATE TABLE IF NOT EXISTS "ddlschema" (
				ID INTEGER PRIMARY KEY AUTOINCREMENT,
				active INTEGER(1) DEFAULT 1,
				creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				schema BLOB
				);"""
			)

			cursor_db.execute(
				"""CREATE TABLE IF NOT EXISTS "demodescription" (
				ID INTEGER PRIMARY KEY AUTOINCREMENT,
				inproduction INTEGER(1) DEFAULT 1,
				JSON BLOB
				);"""
			)
			cursor_db.execute(
				"""CREATE TABLE IF NOT EXISTS "demo" (
				ID INTEGER PRIMARY KEY AUTOINCREMENT,
				editor_demo_id INTEGER,
				title VARCHAR,
				abstract TEXT,
				zipURL VARCHAR,
				active INTEGER(1) DEFAULT 1,
				creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				stateID INTEGER,
				FOREIGN KEY(stateID) REFERENCES state(id),
				UNIQUE(title)
				);"""
			)

			cursor_db.execute(
				"""CREATE TABLE IF NOT EXISTS "demo_demodescription" (
				ID INTEGER PRIMARY KEY AUTOINCREMENT,
				demoID INTEGER NOT NULL,
				demodescriptionId INTEGER NOT NULL,
				creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				FOREIGN KEY(demodescriptionId) REFERENCES demodescription(id) ON DELETE CASCADE,
				FOREIGN KEY(demoID) REFERENCES demo(id) ON DELETE CASCADE,
				UNIQUE(demoID, demodescriptionId)

				);"""
			)


			cursor_db.execute(
				"""CREATE TABLE IF NOT EXISTS "author" (
				ID INTEGER PRIMARY KEY AUTOINCREMENT,
				name VARCHAR ,
				mail VARCHAR(320),
				creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				UNIQUE(mail)
				);"""
			)
			cursor_db.execute(
				"""CREATE TABLE IF NOT EXISTS "editor" (
				ID INTEGER PRIMARY KEY AUTOINCREMENT,
				name VARCHAR ,
				mail VARCHAR(320),
				active INTEGER(1) DEFAULT 1,
				creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				UNIQUE(mail)
				);"""
			)
			cursor_db.execute(
				"""CREATE TABLE IF NOT EXISTS "demo_author" (
				ID INTEGER PRIMARY KEY AUTOINCREMENT,
				demoID INTEGER NOT NULL,
				authorId INTEGER NOT NULL,
				FOREIGN KEY(authorId) REFERENCES author(id) ON DELETE CASCADE,
				FOREIGN KEY(demoID) REFERENCES demo(id) ON DELETE CASCADE,
				UNIQUE(demoID, authorId)

				);"""
			)
			cursor_db.execute(
				"""CREATE TABLE IF NOT EXISTS "demo_editor" (
				ID INTEGER PRIMARY KEY AUTOINCREMENT,
				demoID INTEGER,
				editorId INTEGER,
				FOREIGN KEY(editorId) REFERENCES editor(id) ON DELETE CASCADE,
				FOREIGN KEY(demoID) REFERENCES demo(id) ON DELETE CASCADE,
				UNIQUE(demoID, editorId)
				);"""
			)

			conn.commit()
			conn.close()
		except Exception as ex:

			error_string = ("createDb e:%s" % (str(ex)))
			print(error_string)

			if os.path.isfile(dbname):
				try:
					os.remove(dbname)
				except Exception as ex:
					error_string = ("createDb remove e:%s" % (str(ex)))
					print (error_string)
			status = False

		print "DB Created"
	else:
		print "Create DB pass"
	return status


def initDb(database_name):
	"""
	Initialize the database (could be replaced by SOUTH migrations)
	"""
	status = True
	dbname = database_name



	try:
		conn = lite.connect(dbname)
		cursor_db = conn.cursor()
		cursor_db.execute(""" PRAGMA foreign_keys=ON""")

		# init state inactive,preprint, published
		cursor_db.execute('''INSERT INTO state (name,description) VALUES(?, ?)''', ('published', 'published',))
		cursor_db.execute('''INSERT INTO state (name,description) VALUES(?, ?)''', ('preprint', 'preprint',))
		cursor_db.execute('''INSERT INTO state (name,description) VALUES(?, ?)''', ('inactive', 'inactive',))

		conn.commit()
		conn.close()

	except Exception as ex:

		error_string = ("initDb e:%s" % (str(ex)))
		print(error_string)
		status = False

	print "DB Initialized"



	return status


def testDb(database_name):
	"""
	Initialize the database for TESTING PURPOSES! (South migrations should be used instead od scripts)
	"""
	status = True
	dbname = database_name
	print
	print "STARTING DB TESTS"

	try:
		conn = lite.connect(dbname)
		cursor_db = conn.cursor()
		cursor_db.execute(""" PRAGMA foreign_keys=ON""")

		# demo
		print "* DB DemoDAO"
		demo_dao = DemoDAO(conn)
		editorsdemoid = 24
		title = 'Demo TEST Title'
		abstract = 'Demo Abstract'
		zipURL = 'https://www.sqlite.org/lang_createtable.html'
		active = 1
		stateID = 1
		d = Demo(editorsdemoid, title, abstract, zipURL, active, stateID)
		demo_dao.add(d)
		print d.__dict__

		d = demo_dao.read(1)
		d.zipURL = 'https://www.sqlite.org'
		d.stateID = 2
		demo_dao.update(d)
		# demo.delete(1)
		d = demo_dao.read(1)
		print d.__dict__

		editorsdemoid = 43
		title = 'Demo 2 TEST Title'
		abstract = 'Demo2 Abstract'
		zipURL = 'https://www.sqlite.org/demo2'
		active = 1
		stateID = 1
		d2 = Demo(editorsdemoid, title, abstract, zipURL, active, stateID)
		demo_dao.add(d2)


		# author
		print "* DB AuthorDAO"
		author_dao = AuthorDAO(conn)
		name = 'jose Arrecio Kubon'
		mail = 'jak@gmail.com'
		a = Author(name, mail)
		author_dao.add(a)
		a = author_dao.read(1)
		a.name = 'Pepe Arrecio Kubon'
		author_dao.update(a)
		# author.delete(1)
		a = author_dao.read(1)
		print a.__dict__

		# demo-author
		print '* DB demo-author'
		da_dao = DemoAuthorDAO(conn)
		print a.id, d.id
		da_dao.add(d.id, a.id)
		da_dao.add(2, a.id)
		print da_dao.read_author_demos(a.id)
		print da_dao.read_demo_authors(d.id)
		print da_dao.read(1)

		# editor
		print "* DB EditorDAO"
		editor_dao = EditorDAO(conn)
		name = 'Editor1'
		mail = 'editor1@gmail.com'
		e = Editor(name, mail)
		editor_dao.add(e)
		e = editor_dao.read(1)
		e.name = 'Editor2'
		editor_dao.update(e)
		# editor.delete(1)
		e = editor_dao.read(1)
		print e.__dict__

		# demo-editor
		print '* DB demo-editor'
		de_dao = DemoEditorDAO(conn)
		print e.id, e.id
		de_dao.add(e.id, e.id)
		de_dao.add(2, e.id)
		print de_dao.read_editor_demos(e.id)
		print de_dao.read_demo_editors(d.id)
		print de_dao.read(3)
		print de_dao.read(1)

		conn.commit()
		conn.close()

	except Exception as ex:

		error_string = ("testDb e:%s" % (str(ex)))
		print(error_string)
		status = False

	print "DB test ok"
	return status
