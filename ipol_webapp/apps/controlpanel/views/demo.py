__author__ = 'josearrecio'

from django.shortcuts import render
from django.views.generic import TemplateView
import services
from datetime import datetime
from rest_framework import serializers
from rest_framework.renderers import JSONRenderer
from django.utils.six import BytesIO
from rest_framework.parsers import JSONParser

import logging
logger = logging.getLogger(__name__)



#Utilities
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
		logger.error(serializer.errors)



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



#VIEWS
class PageView2(TemplateView):
	template_name = "demo_result_page.html"

	def get(self,request):
		r = services.get_page(1,1)
		return render(request, 'demo_result_page.html',r)

class PageView1(TemplateView):
	# template_name = "photogallery/video.html"
	template_name = "demo_test_result_page.html"

	def dispatch(self, *args, **kwargs):
		# para las pestanas
		#self.request.session['menu'] = 'menu-'
		return super(PageView1, self).dispatch(*args, **kwargs)


	#http://reinout.vanrees.org/weblog/2014/05/19/context.html
	def result(self):
		result =None
		try:
			result = services.get_page(-1,1)
			# se ordenan en el admin. order no es necesario
			print("result1")
			print(result)
		except Exception as e:
			print(e)
		return result

class PageView(TemplateView):
	# template_name = "photogallery/video.html"
	template_name = "demo_result_page.html"

	def dispatch(self, *args, **kwargs):
		return super(PageView, self).dispatch(*args, **kwargs)


	#http://reinout.vanrees.org/weblog/2014/05/19/context.html
	def result(self):
		id = self.kwargs['id']
		#todo validate id, debe ser un numero
		#print(id)

		result =None
		try:
			print(" demo_id: %d"%int(id))

			#obtengo el jsonpara la pagina 1
			page_json = services.get_page(int(id),1)

			result = DeserializePage(page_json)


		except Exception , e:
			msg="Error %s"%e
			logger.error(msg)

		return result

class DemosView(TemplateView):
	template_name = "demo_list.html"

	def dispatch(self, *args, **kwargs):
		# para las pestanas
		#self.request.session['menu'] = 'menu-'
		return super(DemosView, self).dispatch(*args, **kwargs)


	#http://reinout.vanrees.org/weblog/2014/05/19/context.html
	def result(self):
		result =None
		try:
			result = services.get_demo_list()
			# se ordenan en el admin. order no es necesario

		except Exception as e:
			print(e)
		return result









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