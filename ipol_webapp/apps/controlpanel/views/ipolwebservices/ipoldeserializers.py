# coding=utf-8
import datetime

__author__ = 'josearrecio'

from rest_framework import serializers
from django.utils.six import BytesIO
from rest_framework.parsers import JSONParser

import logging

logger = logging.getLogger(__name__)

# Serializers , to parse complex JSON to python data structures

#####################
#  DEMOINFO MODULE  #
#####################

def DeserializeDemoinfoStatus(jsonresult):

	#Clases that will contain the json data
	class Stats(object):
		def __init__(self, status,nb_demos,nb_authors,nb_editors):
			self.status = status
			self.nb_demos = nb_demos
			self.nb_authors = nb_authors
			self.nb_editors = nb_editors


	# Serializers
	class StatsSerializer(serializers.Serializer):
		status = serializers.CharField(max_length=200)
		nb_demos = serializers.IntegerField()
		nb_authors = serializers.IntegerField()
		nb_editors = serializers.IntegerField()

		def create(self, validated_data):
			return Stats(**validated_data)


	#JSON TO OBJECTS

	#Using data from WS
	jsondata = jsonresult

	#print jsondata


	#Deserialization.
	mywstats = None
	try:

		#First we parse a stream into Python native datatypes...
		stream = BytesIO(jsondata)
		data = JSONParser().parse(stream)
		#then we restore those native datatypes into a dictionary of validated data.
		serializer = StatsSerializer(data=data)

		if serializer.is_valid(raise_exception=True):
			mywstats = serializer.save()


	except Exception,e:
		msg="Error JSON Deserialization e: %s serializer.errors: "%e
		logger.error(msg)
		#logger.error(serializer.errors)

	#print mywstats.__class__
	return mywstats


def DeserializeDemoinfoDemoList(jsonresult):


	#Clases that will contain the json data
	#demodescriptionID is optional a demo may not have one yet!

	class Demo(object):
		def __init__(self, editorsdemoid, title, abstract, zipURL, active, stateID, id, creation, modification):
			self.editorsdemoid = editorsdemoid
			self.title = title
			self.abstract = abstract
			self.zipURL = zipURL
			self.active = active
			self.stateID = stateID
			self.id = id
			self.creation = creation
			self.modification = modification

	class DemoList(object):
		def __init__(self, demo_list,status):
			self.demo_list = demo_list
			self.status = status

	# Serializers
	class DemoinfoDemoSerializer(serializers.Serializer):

		editorsdemoid = serializers.IntegerField()
		title = serializers.CharField()
		abstract = serializers.CharField()
		zipURL = serializers.URLField()
		active = serializers.IntegerField()
		stateID = serializers.IntegerField()
		#demodescriptionID = serializers.IntegerField(required=False)
		id = serializers.IntegerField()
		creation = serializers.DateTimeField()
		modification = serializers.DateTimeField()

		def create(self, validated_data):
			return Demo(**validated_data)

	class DemoinfoDemoListSerializer(serializers.Serializer):
		demo_list = DemoinfoDemoSerializer(many=True)
		status = serializers.CharField(max_length=200)

		def create(self, validated_data):
			list_demos = validated_data.pop('demo_list')
			status = validated_data.pop('status')
			demo_list = list()
			for demo in list_demos:
				ds = DemoinfoDemoSerializer(data=demo)

				if ds.is_valid(raise_exception=True):
					demo_list.append(ds.save())

			demolist = DemoList(demo_list,status)

			return demolist

	#Using data from WS
	jsondata = jsonresult

	#Deserialization.
	mydl = None
	try:

		#First we parse a stream into Python native datatypes...
		stream = BytesIO(jsondata)
		data = JSONParser().parse(stream)

		#then we restore those native datatypes into a dictionary of validated data.
		serializer = DemoinfoDemoListSerializer(data=data)

		if serializer.is_valid(raise_exception=True):
			mydl = serializer.save()


	except Exception,e:
		msg="Error DeserializeDemoinfoDemoList  JSON Deserialization e: %s serializer.errors: " % e
		logger.error(msg)
		print(msg)
		#logger.error(serializer.errors)

	return mydl


def DeserializeDemoinfoAuthorList(jsonresult):


	#Clases that will contain the json data
	#demodescriptionID is optional a demo may not have one yet!

	class Demo(object):
		def __init__(self, editorsdemoid, title, abstract, zipURL, active, stateID, id, creation, modification, demodescriptionID=None):
			self.editorsdemoid = editorsdemoid
			self.title = title
			self.abstract = abstract
			self.zipURL = zipURL
			self.active = active
			self.stateID = stateID
			self.demodescriptionID = demodescriptionID
			self.id = id
			self.creation = creation
			self.modification = modification


	class DemoList(object):
		def __init__(self, demo_list,status):
			self.demo_list = demo_list
			self.status = status


	# Serializers
	class DemoinfoDemoSerializer(serializers.Serializer):

		editorsdemoid = serializers.IntegerField()
		title = serializers.CharField()
		abstract = serializers.CharField()
		zipURL = serializers.URLField()
		active = serializers.IntegerField()
		stateID = serializers.IntegerField()
		demodescriptionID = serializers.IntegerField(required=False)
		id = serializers.IntegerField()
		creation = serializers.DateTimeField()
		modification = serializers.DateTimeField()

		def create(self, validated_data):
			return Demo(**validated_data)


	class DemoinfoDemoListSerializer(serializers.Serializer):
		demo_list = DemoinfoDemoSerializer(many=True)
		status = serializers.CharField(max_length=200)

		def create(self, validated_data):
			list_demos = validated_data.pop('demo_list')
			status = validated_data.pop('status')
			demo_list = list()
			for demo in list_demos:
				ds = DemoinfoDemoSerializer(data=demo)

				if ds.is_valid(raise_exception=True):
					demo_list.append(ds.save())

			demolist = DemoList(demo_list,status)

			return demolist

	#Using data from WS
	jsondata = jsonresult

	#Deserialization.
	mydl = None
	try:

		#First we parse a stream into Python native datatypes...
		stream = BytesIO(jsondata)
		data = JSONParser().parse(stream)
		print "jsondata: ",jsondata

		#then we restore those native datatypes into a dictionary of validated data.
		serializer = DemoinfoDemoListSerializer(data=data)

		if serializer.is_valid(raise_exception=True):
			mydl = serializer.save()


	except Exception,e:
		msg="Error DeserializeDemoinfoDemoList  JSON Deserialization e: %s serializer.errors: " % e
		logger.error(msg)
		print(msg)
		#logger.error(serializer.errors)

	print mydl
	return mydl



####################
#  ARCHIVE MODULE  #
####################

def DeserializePage(jsonresult):





	#Clases that will contain the json data
	class ExperimentFiles(object):
		def __init__(self, url,url_thumb,id,name):
			self.url = url
			self.url_thumb = url_thumb
			self.id = id
			self.name = name

	class ExperimentPage(object):
		def __init__(self, files,id, parameters, date=None):
			self.files = files
			self.id = id
			self.parameters = parameters
			self.date = date or datetime.now()

	class WsPage(object):
		def __init__(self, id_demo,nb_pages, status,experiments):
			self.id_demo = id_demo
			self.nb_pages = nb_pages
			self.status = status
			self.experiments = experiments

	# #JSON DATA EXAMPLE
	# expfiles1 = ExperimentFiles(url='http://boucantrin.ovh.hw.ipol.im:9000/blobs/f4bcd150c547414c6d50dba1c7b27c3fa6b860a3.jpeg',
	# 					  url_thumb='http://boucantrin.ovh.hw.ipol.im:9000/blobs_thumbs/f4bcd150c547414c6d50dba1c7b27c3fa6b860a3.jpeg',
	# 					  id=3,
	# 					  name='input')
	# expfiles2 = ExperimentFiles(url='http://boucantrin.ovh.hw.ipol.im:9000/blobs/b4fac111a641d16dfffe2e9cda8e8e40f1e0a0f9.jpeg',
	# 					  url_thumb='http://boucantrin.ovh.hw.ipol.im:9000/blobs_thumbs/b4fac111a641d16dfffe2e9cda8e8e40f1e0a0f9.jpeg',
	# 					  id=4,
	# 					  name='water')
	# ExpPage = ExperimentPage(files=[expfiles1,expfiles2],id=8,parameters='test')
	# wspage = WsPage(id_demo = -1,nb_pages =3 , status = "OK", experiments=[ExpPage])


	# Serializers
	class ExperimentFileSerializer(serializers.Serializer):
		url = serializers.URLField()
		url_thumb = serializers.URLField()
		id = serializers.IntegerField()
		name = serializers.CharField(max_length=200)

		def create(self, validated_data):
			return ExperimentFiles(**validated_data)

	class ExperimentPageSerializer(serializers.Serializer):
		files=ExperimentFileSerializer(many=True)
		id=serializers.IntegerField()
		parameters = serializers.CharField(max_length=200)
		date = serializers.DateTimeField()

		def create(self, validated_data):
			#print("CREATE ExperimentPageSerializer Object")

			files = validated_data.pop('files')
			file_list=list()
			for f in files:
				efs = ExperimentFileSerializer(data=f)
				if efs.is_valid(raise_exception=True):
					file_list.append(efs.save())

			exppage = ExperimentPage(
									file_list,
									validated_data.pop('id'),
									validated_data.pop('parameters'),
									validated_data.pop('date')
				)
			return exppage

	class WsPageSerializer(serializers.Serializer):
		id_demo = serializers.IntegerField()
		nb_pages = serializers.IntegerField()
		status = serializers.CharField(max_length=200)
		experiments = ExperimentPageSerializer(many=True)

		def create(self, validated_data):
			#print("CREATE WsPageSerializer Object")

			experiments = validated_data.pop('experiments')
			experiments_list=list()
			for e in experiments:
				eps = ExperimentPageSerializer(data=e)
				if eps.is_valid(raise_exception=True):
					experiments_list.append(eps.save())

			wspage = WsPage(
							validated_data.pop('id_demo'),
							validated_data.pop('nb_pages'),
							validated_data.pop('status'),
							experiments_list
						)
			return wspage

	#OBJECTS TO JSON
	# #serializer = ExperimentFileSerializer(expfiles1)
	# #serializer = ExperimentPageSerializer(ExpPage)
	# serializer = WsPageSerializer(wspage)
	#
	# print("-- serializer.data")
	# print(serializer.data)
	# print


	#JSON TO OBJECTS
	#Using JSON DATA EXAMPLE
	#jsonexpdata = JSONRenderer().render(serializer.data)

	#Using data from WS
	jsondata = jsonresult

	#print jsondata


	#Deserialization.
	mywspage = None
	try:

		#First we parse a stream into Python native datatypes...
		stream = BytesIO(jsondata)
		data = JSONParser().parse(stream)
		#serializer = ExperimentFilesSerializer(data=data)
		#serializer = ExperimentPageSerializer(data=data)

		#then we restore those native datatypes into a dictionary of validated data.
		serializer = WsPageSerializer(data=data)

		if serializer.is_valid(raise_exception=True):
			mywspage = serializer.save()

		# print("== serializer.is_valid()")
		# print(serializer.is_valid())
		# print
		# print("== serializer.validated_data")
		# print(serializer.validated_data)
		# print

	except Exception,e:
		msg="Error JSON Deserialization e: %s serializer.errors: "%e
		logger.error(msg)
		#logger.error(serializer.errors)



	# print "== convert to python obj"
	# print "== python obj class"
	# print mywspage.__class__
	# print mywspage.id_demo
	# print mywspage.experiments.__class__
	# print mywspage.experiments[0].__class__
	# print mywspage.experiments[0]
	# print mywspage.experiments[0].id
	# print mywspage.experiments[0].files[0].url

	return mywspage


def DeserializeArchiveStatus(jsonresult):

	#Clases that will contain the json data
	class Stats(object):
		def __init__(self, status,nb_blobs,nb_experiments):
			self.status = status
			self.nb_blobs = nb_blobs
			self.nb_experiments = nb_experiments


	# Serializers
	class StatsSerializer(serializers.Serializer):
		status = serializers.CharField(max_length=200)
		nb_blobs = serializers.IntegerField()
		nb_experiments = serializers.IntegerField()

		def create(self, validated_data):
			return Stats(**validated_data)


	#JSON TO OBJECTS

	#Using data from WS
	jsondata = jsonresult

	#print jsondata


	#Deserialization.
	mywstats = None
	try:

		#First we parse a stream into Python native datatypes...
		stream = BytesIO(jsondata)
		data = JSONParser().parse(stream)
		#then we restore those native datatypes into a dictionary of validated data.
		serializer = StatsSerializer(data=data)

		if serializer.is_valid(raise_exception=True):
			mywstats = serializer.save()


	except Exception,e:
		msg="Error JSON Deserialization e: %s serializer.errors: "%e
		logger.error(msg)
		#logger.error(serializer.errors)

	#print mywstats.__class__
	return mywstats


def DeserializeArchiveDemoList(jsonresult):


	#Clases that will contain the json data
	class Demo(object):
		def __init__(self, demo_id):
			self.demo_id = demo_id

	class DemoList(object):
		def __init__(self, demo_list,status):
			self.demo_list = demo_list
			self.status = status


	# Serializers
	class ArchiveDemoSerializer(serializers.Serializer):

		demo_id = serializers.IntegerField()
		def create(self, validated_data):
			return Demo(**validated_data)


	class ArchiveDemoListSerializer(serializers.Serializer):
		demo_list = ArchiveDemoSerializer(many=True)
		status = serializers.CharField(max_length=200)

		def create(self, validated_data):
			list_demos = validated_data.pop('demo_list')
			demo_list = list()
			for demo in list_demos:
				ds = ArchiveDemoSerializer(data=demo)
				if ds.is_valid(raise_exception=True):
					demo_list.append(ds.save())
			demolist = DemoList(
					demo_list,
					validated_data.pop('status')
				)
			return demolist



	#JSON TO OBJECTS
	#Using JSON DATA EXAMPLE
	#jsonexpdata = JSONRenderer().render(serializer.data)

	#Using data from WS
	jsondata = jsonresult


	#Deserialization.
	mydl = None
	try:

		#First we parse a stream into Python native datatypes...
		stream = BytesIO(jsondata)
		data = JSONParser().parse(stream)
		print jsondata

		#then we restore those native datatypes into a dictionary of validated data.
		serializer = ArchiveDemoListSerializer(data=data)

		if serializer.is_valid(raise_exception=True):
			mydl = serializer.save()


	except Exception,e:
		msg="Error JSON Deserialization e: %s serializer.errors: " % e
		logger.error(msg)
		print(msg)
		#logger.error(serializer.errors)

	print mydl
	return mydl

####################
#   BLOBS MODULE   #
####################

def DeserializeDemoList(jsonresult):


	#Clases that will contain the json data
	class Demo(object):
		def __init__(self, id,is_template,template_id,name):
			self.is_template = is_template
			self.template_id = template_id
			self.name = name
			self.id = id

	class DemoList(object):
		def __init__(self, list_demos,status):
			self.list_demos = list_demos
			self.status = status


	# Serializers
	class DemoSerializer(serializers.Serializer):

		is_template = serializers.IntegerField()
		template_id = serializers.IntegerField()
		name = serializers.CharField(max_length=200)
		id = serializers.IntegerField()

		def create(self, validated_data):
			#print("CREATE DemoSerializer Object")
			return Demo(**validated_data)


	class DemoListSerializer(serializers.Serializer):
		list_demos = DemoSerializer(many=True)
		status = serializers.CharField(max_length=200)

		def create(self, validated_data):
			#print("CREATE DemoListSerializer Object")

			list_demos = validated_data.pop('list_demos')

			demo_list = list()
			for demo in list_demos:
				ds = DemoSerializer(data=demo)
				if ds.is_valid(raise_exception=True):
					demo_list.append(ds.save())

			demolist = DemoList(
					demo_list,
					validated_data.pop('status')
				)
			return demolist



	#JSON TO OBJECTS
	#Using JSON DATA EXAMPLE
	#jsonexpdata = JSONRenderer().render(serializer.data)

	#Using data from WS
	jsondata = jsonresult


	#Deserialization.
	mydl = None
	try:

		#First we parse a stream into Python native datatypes...
		stream = BytesIO(jsondata)
		data = JSONParser().parse(stream)
		print jsondata

		#then we restore those native datatypes into a dictionary of validated data.
		serializer = DemoListSerializer(data=data)

		if serializer.is_valid(raise_exception=True):
			mydl = serializer.save()


	except Exception,e:
		msg="Error JSON Deserialization e: %s serializer.errors: "%e
		logger.error(msg)
		print(msg)
		#logger.error(serializer.errors)

	return mydl


#TEST AND OTHER STUFF
def DeserializePageTest(jsonresult):


	from datetime import datetime
	from rest_framework import serializers
	from rest_framework.renderers import JSONRenderer
	from django.utils.six import BytesIO
	from rest_framework.parsers import JSONParser



	class ExperimentFiles(object):
		def __init__(self, url,url_thumb,id,name):
			self.url = url
			self.url_thumb = url_thumb
			self.id = id
			self.name = name

	class ExperimentPage(object):
		def __init__(self, files,id, parameters, date=None):
			self.files = files
			self.id = id
			self.parameters = parameters
			self.date = date or datetime.now()

	class WsPage(object):
		def __init__(self, id_demo,nb_pages, status,experiments):
			self.id_demo = id_demo
			self.nb_pages = nb_pages
			self.status = status
			self.experiments = experiments

	#parsear el json y devolver variables.
	expfiles1 = ExperimentFiles(url='http://boucantrin.ovh.hw.ipol.im:9000/blobs/f4bcd150c547414c6d50dba1c7b27c3fa6b860a3.jpeg',
						  url_thumb='http://boucantrin.ovh.hw.ipol.im:9000/blobs_thumbs/f4bcd150c547414c6d50dba1c7b27c3fa6b860a3.jpeg',
						  id=3,
						  name='input')
	expfiles2 = ExperimentFiles(url='http://boucantrin.ovh.hw.ipol.im:9000/blobs/b4fac111a641d16dfffe2e9cda8e8e40f1e0a0f9.jpeg',
						  url_thumb='http://boucantrin.ovh.hw.ipol.im:9000/blobs_thumbs/b4fac111a641d16dfffe2e9cda8e8e40f1e0a0f9.jpeg',
						  id=4,
						  name='water')
	ExpPage = ExperimentPage(files=[expfiles1,expfiles2],id=8,parameters='test')
	wspage = WsPage(id_demo = -1,nb_pages =3 , status = "OK", experiments=[ExpPage,ExpPage])


	class ExperimentFileSerializer(serializers.Serializer):
		url = serializers.URLField()
		url_thumb = serializers.URLField()
		id = serializers.IntegerField()
		name = serializers.CharField(max_length=200)

		def create(self, validated_data):
			return ExperimentFiles(**validated_data)

		# def update(self, instance, validated_data):
		# 	instance.url = validated_data.get('url', instance.url)
		# 	instance.url_thumb = validated_data.get('url_thumb', instance.url_thumb)
		# 	instance.id = validated_data.get('id', instance.id)
		# 	instance.name= validated_data.get('name', instance.name)
		# 	instance.save()
		# 	return instance

	class ExperimentPageSerializer(serializers.Serializer):
		files=ExperimentFileSerializer(many=True)
		id=serializers.IntegerField()
		parameters = serializers.CharField(max_length=200)
		date = serializers.DateTimeField()

		def create(self, validated_data):
			print("CREATE ExperimentPageSerializer Object")

			files = validated_data.pop('files')
			file_list=list()
			for f in files:
				efs = ExperimentFileSerializer(data=f)
				if efs.is_valid(raise_exception=True):
					file_list.append(efs.save())

			exppage = ExperimentPage(
									file_list,
									validated_data.pop('id'),
									validated_data.pop('parameters'),
									validated_data.pop('date')
				)
			return exppage


		# def update(self, instance, validated_data):
		# 	instance.files = validated_data.get('files', instance.files)
		# 	#instance.files = validated_data.pop('files')
		# 	instance.id = validated_data.get('id', instance.id)
		# 	instance.parameters = validated_data.get('parameters', instance.parameters)
		# 	instance.expdate = validated_data.get('expdate', instance.expdate)
		# 	instance.save()
		# 	return instance

	class WsPageSerializer(serializers.Serializer):
		id_demo = serializers.IntegerField()
		nb_pages = serializers.IntegerField()
		status = serializers.CharField(max_length=200)
		experiments = ExperimentPageSerializer(many=True)

		def create(self, validated_data):
			print("CREATE WsPageSerializer Object")

			experiments = validated_data.pop('experiments')
			experiments_list=list()
			for e in experiments:
				eps = ExperimentPageSerializer(data=e)
				if eps.is_valid(raise_exception=True):
					experiments_list.append(eps.save())

			wspage=WsPage(
							validated_data.pop('id_demo'),
							validated_data.pop('nb_pages'),
							validated_data.pop('status'),
							experiments_list
						)
			return wspage
			#return WsPage(**validated_data)

		# def update(self, instance, validated_data):
		# 	instance.id_demo = validated_data.get('id_demo', instance.id_demo)
		# 	instance.nb_pages = validated_data.get('nb_pages', instance.nb_pages)
		# 	instance.status = validated_data.get('status', instance.status)
		# 	#instance.experiments= validated_data.get('experiments', instance.experiments)
		# 	instance.experiments= validated_data.pop('experiments')
		# 	instance.save()
		# 	return instance




	#serializer = ExperimentFileSerializer(expfiles1)
	#serializer = ExperimentPageSerializer(ExpPage)
	serializer = WsPageSerializer(wspage)

	print("-- serializer.data")
	print(serializer.data)
	print

	jsonexpdata = JSONRenderer().render(serializer.data)
	print("-- jsonexpdata")
	print(jsonexpdata)
	print(jsonexpdata.__class__)
	print



	#Deserialization is similar. First we parse a stream into Python native datatypes...


	try:
		stream = BytesIO(jsonexpdata)
		data = JSONParser().parse(stream)
		#serializer = ExperimentFilesSerializer(data=data)
		#serializer = ExperimentPageSerializer(data=data)
		serializer = WsPageSerializer(data=data)
		print("== serializer.is_valid()")
		print(serializer.is_valid())
		print
		print("== serializer.validated_data")
		print(serializer.validated_data)
		print

	except Exception,e:
		print("Error Deserialization e:%s"%e)
		print("serializer.errors")
		print serializer.errors




	mywspage = serializer.save()
	print "== convert to python obj"
	print "== python obj class"
	print mywspage.__class__
	print
	# print "== python obj class"
	# print mywspage.files.__class__
	# print mywspage.files
	print
	print mywspage.id_demo
	print mywspage.experiments.__class__
	print mywspage.experiments[0].__class__
	print mywspage.experiments[0]
	print mywspage.experiments[0].id
	print mywspage.experiments[0].files[0].url

def SerializerTest2(jsonresult):

	print("SerializerTest2")

	from datetime import datetime

	class Comment(object):
		def __init__(self, email, content, created=None):
			self.email = email
			self.content = content
			self.created = created or datetime.now()

	comment = Comment(email='leila@example.com', content='foo bar')

	from rest_framework import serializers

	class CommentSerializer(serializers.Serializer):
		email = serializers.EmailField()
		content = serializers.CharField(max_length=200)
		created = serializers.DateTimeField()
	serializer = CommentSerializer(comment)
	print serializer.data
	# {'email': u'leila@example.com', 'content': u'foo bar', 'created': datetime.datetime(2012, 8, 22, 16, 20, 9, 822774)}

	from rest_framework.renderers import JSONRenderer
	json = JSONRenderer().render(serializer.data)
	print json
	print json.__class__
	# '{"email": "leila@example.com", "content": "foo bar", "created": "2012-08-22T16:20:09.822"}'

	from django.utils.six import BytesIO
	from rest_framework.parsers import JSONParser

	stream = BytesIO(json)
	data = JSONParser().parse(stream)
	serializer = CommentSerializer(data=data)
	print serializer.is_valid()
	# True
	print serializer.validated_data
	# {'content': 'foo bar', 'email': 'leila@example.com', 'created': datetime.datetime(2012, 08, 22, 16, 20, 09, 822243)}