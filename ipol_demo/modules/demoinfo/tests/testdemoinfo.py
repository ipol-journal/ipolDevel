import unittest
import sys
import os

from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

from module import DemoInfo

__author__ = 'josearrecio'

CONFIGFILE = "./testdemoinfo.conf"
DBNAME= "testdemoinfo.db"

# run with
# ../tests$ python -m unittest discover

class TestDemoinfo(unittest.TestCase):

	demoinfo = DemoInfo(CONFIGFILE)

	####################
	# individual tests #
	####################

	def delete_db(self):
		# after running all tests clean db, its gets created and init when you instance DemoInfo
		dbname = DBNAME
		test_passed = True
		try:
			if os.path.isfile(dbname):
				try:
					os.remove(dbname)
				except Exception as ex:
					error_string=("DBremove e:%s"%(str(ex)))
					print (error_string)
			status = False
		except Exception as ex:
			error_string=("TEST delete_db  e:%s"%(str(ex)))
			print error_string
			test_passed = False

		self.failUnless(test_passed, 'failure , test_add_demo_1 Failed creating two demos')


	def add_demo_1(self):
		test_passed = True
		try:
			editorsdemoid = 24
			title = 'DemoTEST1 Title'
			abstract = 'DemoTEST1 Abstract'
			zipURL = 'https://DemoTEST1.html'
			active = 1
			stateID = 1
			self.demoinfo.add_demo(editorsdemoid,title, abstract, zipURL,active,stateID)

			editorsdemoid = 24
			title = 'DemoTEST2 Title'
			abstract = 'DemoTEST2 Abstract'
			zipURL = 'https://DemoTEST2.html'
			active = 1
			stateID = 1
			self.demoinfo.add_demo(editorsdemoid,title, abstract, zipURL,active,stateID)
		except Exception as ex:
			test_passed = False

		self.failUnless(test_passed, 'failure , test_add_demo_1 Failed creating two demos')


	def add_demo_2(self):
		test_passed = False
		try:
			editorsdemoid = 24
			title = 'DemoTEST3 Title'
			abstract = 'DemoTEST3 Abstract'
			zipURL = 'https://DemoTEST3.html'
			active = 1
			stateID = 1
			self.demoinfo.add_demo(editorsdemoid,title, abstract, zipURL,active,stateID)

			editorsdemoid = 24
			title = 'DemoTEST3 Title'
			abstract = 'DemoTEST3 Abstract'
			zipURL = 'https://DemoTEST3.html'
			active = 1
			stateID = 1
			self.demoinfo.add_demo(editorsdemoid,title, abstract, zipURL,active,stateID)
		except Exception as ex:
			test_passed = True

		self.failUnless(test_passed, 'failure , test_add_demo_2 does not fail creating demo with the same tile')


	def add_author_1(self):
		test_passed = True
		try:
			name='Author Name1'
			mail = 'authoremail1@gmail.com'
			self.demoinfo.add_author(name, mail)

			name='Author Name2'
			mail = 'authoremail2@gmail.com'
			self.demoinfo.add_author(name, mail)
		except Exception as ex:
			test_passed = False

		self.failUnless(test_passed, 'failure , add_author_1 Failed creating two authors')


	def add_author_2(self):
		test_passed = False
		try:
			name='Author Name3'
			mail = 'authoremail3@gmail.com'
			self.demoinfo.add_author(name, mail)

			name='Author Name3'
			mail = 'authoremail3@gmail.com'
			self.demoinfo.add_author(name, mail)
		except Exception as ex:
			test_passed = True

		self.failUnless(test_passed, 'failure , add_author_2 does not fail creating two authors  with the same email ')


	def add_editor_1(self):
		test_passed = True
		try:
			name='editor Name1'
			mail = 'editoremail1@gmail.com'
			self.demoinfo.add_editor(name, mail)

			name='editor Name2'
			mail = 'editoremail2@gmail.com'
			self.demoinfo.add_editor(name, mail)
		except Exception as ex:
			test_passed = False

		self.failUnless(test_passed, 'failure , add_editor_1 Failed creating two authors')


	def add_editor_2(self):
		test_passed = False
		try:
			name='editor Name3'
			mail = 'editoremail3@gmail.com'
			self.demoinfo.add_editor(name, mail)

			name='editor Name3'
			mail = 'editoremail3@gmail.com'
			self.demoinfo.add_editor(name, mail)
		except Exception as ex:
			test_passed = True

		self.failUnless(test_passed, 'failure , add_editor_2 does not fail creating two editors  with the same email ')


	def add_authors_and_editors_to_demo_1(self):
		test_passed = True
		try:

			self.demoinfo.add_author_to_demo(1 ,1)
			self.demoinfo.add_editor_to_demo(1 ,1)
			self.demoinfo.add_author_to_demo(1 ,3)
			self.demoinfo.add_editor_to_demo(1 ,3)
			self.demoinfo.add_author_to_demo(2 ,2)
			self.demoinfo.add_editor_to_demo(2 ,2)

		except Exception as ex:
			test_passed = False

		self.failUnless(test_passed, 'failure , add_editor_1 Failed adding editor/author to a demo  ')


	def add_authors_to_demo_2(self):
		test_passed = False
		try:

			self.demoinfo.add_author_to_demo(1 ,1)
		except Exception as ex:
			test_passed = True

		self.failUnless(test_passed, 'failure , add_authors_to_demo_2 does not fail creating two duplicate authors  with the same demo ')


	def add_editors_to_demo_3(self):
		test_passed = False
		try:

			self.demoinfo.add_editor_to_demo(1 ,1)
		except Exception as ex:
			test_passed = True

		self.failUnless(test_passed, 'failure , add_editors_to_demo_3 does not fail creating two duplicate editors  with the same demo ')


	def remove_authors_and_editors_to_demo_1(self):
		test_passed = True
		try:

			self.demoinfo.remove_author_from_demo(1 ,3)
			self.demoinfo.remove_editor_from_demo(1 ,3)

			ajson = self.demoinfo.demo_get_authors_list(1)
			# print ajson
			if not "\"id\": 1" in ajson or "\"id\": 3" in ajson:
				print "only author 1 not found in demo 1"
				raise Exception

			ejson = self.demoinfo.demo_get_editors_list(1)
			#print ejson
			if not "\"id\": 1" in ejson or "\"id\": 3" in ejson:
				print "only editor 1 not found in demo 1"
				raise Exception

		except Exception as ex:
			test_passed = False

		self.failUnless(test_passed, 'failure , remove_authors_and_editors_to_demo_1 Failed removing editor/author to a demo  ')


	def edit_demo(self):
		test_passed = True
		try:

			# ajson = self.demoinfo.demo_list()
			# print ajson

			json_demo_1='{"modification": "2015-12-02 13:24:43", "title": "newdemo1", "abstract": "newdemo1abstract", "creation": "2015-12-02 13:24:43", "editorsdemoid": 1, "active": 1, "stateID": 1, "id": 1, "zipURL": "http://demo1updated.com"}'
			self.demoinfo.update_demo(json_demo_1)
			ajson = self.demoinfo.demo_list()

			if not "newdemo1" in ajson or not "newdemo1abstract" in ajson or not "http://demo1updated.com" in ajson:
				print "Demo update failed"
				raise Exception

		except Exception as ex:
			print ex
			test_passed = False

		self.failUnless(test_passed, 'failure , edit_demo  updating  authors')


	def edit_author(self):

		test_passed = True
		try:

			#ajson = self.demoinfo.demo_get_authors_list(1)
			#print ajson


			json_author_1='{"mail": "authoremail1_updated@gmail.com", "creation": "2015-12-03 20:53:07", "id": 1, "name": "Author_Name1_updated"}'
			self.demoinfo.update_author(json_author_1)
			ajson = self.demoinfo.demo_get_authors_list(1)
			#print ajson

			if not "authoremail1_updated" in ajson or not "Author_Name1_updated" in ajson:
				print "Author update failed"
				raise Exception

		except Exception as ex:
			print ex
			test_passed = False

		self.failUnless(test_passed, 'failure , edit_author  updating  authors')


	def edit_editor(self):
		test_passed = True
		try:

			#ejson = self.demoinfo.demo_get_authors_list(1)
			#print ejson

			json_editor_1='{"mail": "editoremail1_updated@gmail.com", "creation": "2015-12-03 20:53:07","active": 1, "id": 1, "name": "Editor_Name1_updated"}'
			self.demoinfo.update_editor(json_editor_1)
			ejson = self.demoinfo.demo_get_editors_list(1)
			#print ejson

			if not "editoremail1_updated" in ejson or not "Editor_Name1_updated" in ejson:
				print "Editor update failed"
				raise Exception



		except Exception as ex:
			print ex
			test_passed = False

		self.failUnless(test_passed, 'failure , edit_editor  updating  editor')


	def remove_demo(self):
		test_passed = True
		try:

			#initial
			dl0 = self.demoinfo.demo_list()

			#no hard_delete demo 1
			self.demoinfo.delete_demo(1)
			dl1 = self.demoinfo.demo_list()
			al_demo1= self.demoinfo.demo_get_authors_list(1)
			if  ('"id": 1' in dl0) and ('"id": 1' in dl1) and (not "\"id\": 1" in al_demo1) :
				print "Demo 1 delete failed"
				raise Exception


			# hard_delete demo 2
			al_demo2_init = self.demoinfo.demo_get_authors_list(2)
			self.demoinfo.delete_demo(2,hard_delete = True)
			dl2 = self.demoinfo.demo_list()
			al_demo2 = self.demoinfo.demo_get_authors_list(2)
			if ('"id": 2' in dl0) and ('"id": 2' in dl2) and ("\"id\": 2" in al_demo2_init) and ("\"id\": 2" in al_demo2):
				print "Demo 2 hard delete failed"
				raise Exception


			# print
			# print " Initial Demo list"
			# print dl0
			# print
			# print " Demo list after delete demo 1 no hard delete"
			# print dl1
			# print
			# print "al_demo1"
			# print al_demo1
			# print
			# print " Initial Author list for demo 2"
			# print al_demo2_init
			# print
			# print "  Demo list after hard delete demo 2"
			# print dl2
			# print
			# print "al_demo2"
			# print al_demo2

		except Exception as ex:
			print ex
			test_passed = False

		self.failUnless(test_passed, 'failure , removing demos ')


	##########################
	# run all tests in order #
	##########################

	def test_steps(self):
		#run in order all tests
		try:

			print
			print(" Monothic Test Started")
			print(" From the initialized Db, whit no demos,authors o editors, create them and manipulate them using the WS provided by demoInfo module")
			print " ---1"
			self.add_demo_1()
			print " ---2"
			self.add_demo_2()
			print " ---3"
			self.add_author_1()
			print " ---4"
			self.add_author_2()
			print " ---5"
			self.add_editor_1()
			print " ---6"
			self.add_editor_2()
			print " ---7"
			self.add_authors_and_editors_to_demo_1()
			print " ---8"
			self.add_authors_to_demo_2()
			print " ---9"
			self.add_editors_to_demo_3()
			print " ---10"
			self.remove_authors_and_editors_to_demo_1()
			print " ---11"
			self.edit_demo()
			print " ---12"
			self.edit_author()
			print " ---13"
			self.edit_editor()
			print " ---14"
			self.remove_demo()
			print " ---cleanup"
			self.delete_db()
			print(" Monothic Test Ended")

		except Exception as ex:
			print " ---cleanup"
			self.delete_db()
			raise ex


def main():
	unittest.main()


if __name__ == '__main__':
	main()