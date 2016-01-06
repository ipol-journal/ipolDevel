import json
from crispy_forms.bootstrap import FormActions, PrependedText
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit
from django.core.urlresolvers import reverse, reverse_lazy
from apps.controlpanel.views.ipolwebservices.ipolservices import demoinfo_get_states, demoinfo_demo_list, \
	demoinfo_author_list

__author__ = 'josearrecio'
from django import forms


# Forms use bootstrap clases for layout

class DDLform(forms.Form):

	#hidden
	demoid = forms.IntegerField(label='demoid',required=True)
	ddlid = forms.IntegerField(label='ddlid',required=False)
	#normal
	ddlJSON = forms.CharField(label='ddlJSON',widget=forms.Textarea)

	helper = FormHelper()
	helper.form_id = "DDLform"
	helper.form_action = reverse_lazy('ipol.cp.demoinfo.save_ddl')
	helper.form_method = 'POST'
	helper.form_class = 'form-horizontal'

	helper.layout = Layout(
		Field('demoid', type='hidden'),
		Field('ddlid', type='hidden'),
		Field('ddlJSON', rows="8", css_class='form-control'),
		FormActions(
			Submit('save_ddl', 'Save', css_class="btn-primary"),
		)
	)


# demoinfo states for the demos form, pubhished,etc
def get_demoinfo_module_states():
	state_list=None

	try:
		statesjson = demoinfo_get_states()
		statesdict= json.loads(statesjson)
		#print "statesdict", statesdict

		state_list= statesdict['state_list']
	except Exception as e:
		msg=" get_demoinfo_module_states Error %s "%e
		print(msg)

	return state_list


#todo podria tener un ws q solo devolviera los dos campos q nececisto para el select del form
def get_demoinfo_demo_list():
	demo_list_option=list()

	try:
		demo_list_json = demoinfo_demo_list()
		demo_list_dict= json.loads(demo_list_json)
		# print "demo_list_dict", demo_list_dict

		demo_list= demo_list_dict['demo_list']

		demo_list_option.append( (0,"None selected") )
		for d in demo_list:
			d = (d["id"],str(d["editorsdemoid"])+", "+str(d["title"]))
			demo_list_option.append(d)

		print "demo_list_option", demo_list_option

	except Exception as e:
		msg=" get_demoinfo_demo_list Error %s "%e
		print(msg)

	return demo_list_option


#todo podria tener un ws q solo devolviera los dos campos q nececisto para el select del form
# todo no mostrar los autores que ya pertenecen a la demo en question
def get_demoinfo_author_list(demoid=None):


	author_list_option=list()

	try:
		print "get_demoinfo_author_list"
		author_list_json = demoinfo_author_list()
		author_list_dict= json.loads(author_list_json)
		# print "demo_list_dict", demo_list_dict

		author_list= author_list_dict['author_list']

		author_list_option.append( (0,"None selected") )
		for a in author_list:
			a = (a["id"],str(a["name"])+", "+str(a["mail"]))
			author_list_option.append(a)

		print "get_demoinfo_author_list", author_list_option

	except Exception as e:
		msg=" get_demoinfo_author_list Error %s "%e
		print(msg)

	return author_list_option


class Demoform(forms.Form):
	#hidden
	id = forms.IntegerField(label='demoid',required=False)
	#normal
	editorsdemoid = forms.IntegerField(label='editorsdemoid',required=True)
	title = forms.CharField(label='title',required=True)
	zipURL = forms.URLField(label='zipURL',required=True)
	# must not be displayed, always true! its what we use to delete a demo
	# active = forms.BooleanField(label='active',required=False,initial=True)
	state = forms.ChoiceField(label='state',required=True)
	abstract = forms.CharField(label='abstract',widget=forms.Textarea,required=True)
	# optional
	# demoddlid = forms.IntegerField(label='demodescriptionID',required=False)
	# demoddlJSON = forms.CharField(label='ddlJSON',widget=forms.Textarea,required=False)

	helper = FormHelper()
	helper.form_id = "Demoform"
	helper.form_action = reverse_lazy('ipol.cp.demoinfo.save_demo')
	helper.form_method = 'POST'
	helper.form_class = 'form-horizontal'

	helper.layout = Layout(

		Field('id', type='hidden'),
		Field('editorsdemoid'),
		Field('title', css_class='form-control'),
		Field('zipURL', css_class='form-control'),
		# PrependedText('active', ''),
		Field('state'),
		Field('abstract', rows="8", css_class='form-control'),
		# Field('demoddlid', type='hidden'),
		# Field('demoddlJSON', rows="8", css_class='form-control'),
		FormActions(
			Submit('save_demo', 'Save', css_class="btn-primary"),
		)
	)
	def __init__(self, *args, **kwargs):
		#dinamic way to get staes of demo in demoinfo module
		super(Demoform, self).__init__(*args, **kwargs)
		self.fields['state'] = forms.ChoiceField(label='state',required=True, choices=get_demoinfo_module_states() )


# for edit
class Authorform(forms.Form):
	#hidden
	id = forms.IntegerField(label='id',required=False)
	#normal
	name = forms.CharField(label='name',required=True)
	mail = forms.EmailField(label='mail',required=True)

	helper = FormHelper()
	helper.form_id = "Authorform"
	helper.form_action = reverse_lazy('ipol.cp.demoinfo.save_author')
	# helper.form_action = reverse_lazy('ipol.cp.demoinfo.save_demo')
	helper.form_method = 'POST'
	helper.form_class = 'form-horizontal'
	helper.layout = Layout(
		Field('id', type='hidden'),
		Field('name'),
		Field('mail', css_class='form-control'),
		FormActions(
			Submit('save_author', 'Save', css_class="btn-primary"),
		)
	)


#for new (lets the user create and  assign author to one demo...)
class DemoAuthorform(forms.Form):
	#hidden
	demoid = forms.IntegerField(label='demoid',required=False)
	# no need for author id, whe add it from the select or create it
	#normal
	name = forms.CharField(label='name',required=True)
	mail = forms.EmailField(label='mail',required=True)

	helper = FormHelper()
	helper.form_id = "DemoAuthorform"
	helper.form_action = reverse_lazy('ipol.cp.demoinfo.add_new_author_to_demo')
	helper.form_method = 'POST'
	helper.form_class = 'form-horizontal'
	helper.layout = Layout(
		Field('demoid', type='hidden'),
		Field('name'),
		Field('mail', css_class='form-control'),
		FormActions(
			Submit('save_author', 'Save', css_class="btn-primary"),
		)
	)


#for existing author (lets the user select and assign  author to one demo...)
class ChooseAuthorForDemoform(forms.Form):
	#hidden
	demoid = forms.IntegerField(label='demoid',required=False)
	# no need for author id, whe add it from the select or create it
	# select a demo for this author
	author = forms.ChoiceField(label='author(name,email)',required=True)

	helper = FormHelper()
	helper.form_id = "ChooseAuthorForDemoform"
	helper.form_action = reverse_lazy('ipol.cp.demoinfo.add_existing_author_to_demo')
	helper.form_method = 'POST'
	helper.form_class = 'form-horizontal'
	helper.layout = Layout(
		Field('demoid', type='hidden'),
		Field('author', css_class='form-control'),
		FormActions(
			Submit('save_selected_author_for_demo', 'Save', css_class="btn-primary"),
		)
	)
	def __init__(self, *args, **kwargs):
		#dinamic way to get staes of demo in demoinfo module
		super(ChooseAuthorForDemoform, self).__init__(*args, **kwargs)
		self.fields['author'] = forms.ChoiceField(label='author(name,email)',required=True, choices=get_demoinfo_author_list() )


# class DemoAuthorform(forms.Form):
#   #Add a author to a certain demo
# 	#hidden
# 	demoid = forms.IntegerField(label='id',required=False)
# 	# no need for author id, whe add it from the select or create it
# 	#normal
# 	name = forms.CharField(label='name',required=True)
# 	mail = forms.EmailField(label='mail',required=True)
#
# 	# select a demo for this author
# 	demo = forms.ChoiceField(label='demo(editorid,title)',required=True)
#
# 	helper = FormHelper()
# 	helper.form_id = "DemoAuthorform"
# 	helper.form_action = reverse_lazy('ipol.cp.demoinfo.save_author')
# 	helper.form_method = 'POST'
# 	helper.form_class = 'form-horizontal'
# 	helper.layout = Layout(
# 		Field('demoid', type='hidden'),
# 		Field('name'),
# 		Field('mail', css_class='form-control'),
# 		Field('demo', css_class='form-control'),
# 		FormActions(
# 			Submit('save_author', 'Save', css_class="btn-primary"),
# 		)
# 	)
# 	def __init__(self, *args, **kwargs):
# 		#dinamic way to get staes of demo in demoinfo module
# 		super(DemoAuthorform, self).__init__(*args, **kwargs)
# 		self.fields['demo'] = forms.ChoiceField(label='demo(editorid,title)',required=True, choices=get_demoinfo_demo_list() )
#
