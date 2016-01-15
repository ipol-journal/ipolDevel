
import autocomplete_light.shortcuts as al
from crispy_forms.bootstrap import FormActions, PrependedText
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit
from django.core.urlresolvers import reverse, reverse_lazy
from apps.controlpanel.tools import get_demoinfo_module_states, get_demoinfo_available_author_list, \
	get_demoinfo_available_editor_list
from apps.controlpanel.views.ipolwebservices.ipolservices import demoinfo_get_states, demoinfo_demo_list, \
	demoinfo_available_author_list_for_demo, demoinfo_author_list

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


class Demoform(forms.Form):
	#hidden
	id = forms.IntegerField(label='demoid',required=False)
	#normal
	editorsdemoid = forms.IntegerField(label='editorsdemoid',required=True)
	title = forms.CharField(label='title',required=True)
	zipURL = forms.URLField(label='zipURL',required=True)

	# must not be displayed, always true! its what we use to delete a demo
	active = forms.IntegerField(label='active',required=True)
	# problems using bool in form, just use int...
	# active = forms.BooleanField(label='active',required=False,initial=True)

	state = forms.ChoiceField(label='state',required=True)
	abstract = forms.CharField(label='abstract',widget=forms.Textarea,required=True)


	helper = FormHelper()
	helper.form_id = "Demoform"
	helper.form_action = reverse_lazy('ipol.cp.demoinfo.save_demo')
	helper.form_method = 'POST'
	helper.form_class = 'form-horizontal'

	helper.layout = Layout(

		Field('id', type='hidden'),
		Field('active', type='hidden'),
		# PrependedText('active', ''),
		Field('editorsdemoid'),
		Field('title', css_class='form-control'),
		Field('zipURL', css_class='form-control'),
		Field('state'),
		Field('abstract', rows="8", css_class='form-control'),
		FormActions(
			Submit('save_demo', 'Save', css_class="btn-primary"),
		)
	)
	def __init__(self, *args, **kwargs):
		#dinamic way to get staes of demo in demoinfo module
		super(Demoform, self).__init__(*args, **kwargs)
		self.fields['state'] = forms.ChoiceField(label='state',required=True, choices=get_demoinfo_module_states() )


# for edit Author
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


# for new Author (lets the user create and  assign author to one demo...)
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


# # for existing Author (allows the user to select and assign an author to one demo...)
# class ChooseAuthorForDemoform(forms.Form):
# 	#hidden
# 	demoid = forms.IntegerField(label='demoid',required=False)
# 	# no need for author id, whe add it from the select or create it
# 	# select a demo for this author
# 	author = forms.ChoiceField(label='author(name,email)',required=True)
#
# 	helper = FormHelper()
# 	helper.form_id = "ChooseAuthorForDemoform"
# 	helper.form_action = reverse_lazy('ipol.cp.demoinfo.add_existing_author_to_demo')
# 	helper.form_method = 'POST'
# 	helper.form_class = 'form-horizontal'
# 	helper.layout = Layout(
# 		Field('demoid', type='hidden'),
# 		Field('author', css_class='form-control'),
# 		FormActions(
# 			Submit('save_selected_author_for_demo', 'Save', css_class="btn-primary"),
# 		)
# 	)
# 	def __init__(self, *args, **kwargs):
# 		#dinamic way to get choice values
# 		initial =  kwargs.get('initial', {})
# 		author = initial.get('author', None)
#
# 		# set just the initial value
# 		if author:
# 			kwargs['initial']['author'] = author[0]
#
# 		# create the form
# 		super(ChooseAuthorForDemoform, self).__init__(*args, **kwargs)
#
# 		# self.fields only exist after, so a double validation is needed
# 		if  author :
# 			# initial authors available for demo (initialized in the view with the proper demoid)
# 			self.fields['author'].choices = author
# 		else:
# 			# all authors
# 			self.fields['author'].choices=get_demoinfo_available_author_list()
#
# 	# cannot do this, i only know the demmid in the view
# 	# def __init__(self, *args, **kwargs):
# 	# 	#dinamic way to get staes of demo in demoinfo module
# 	# 	print "AKI __init__"
# 	# 	super(ChooseAuthorForDemoform, self).__init__(*args, **kwargs)
# 	# 	self.fields['author'] = forms.ChoiceField(label='author(name,email)',required=True, choices=get_demoinfo_available_author_list() )
# 	#
#

# for existing Author (allows the user to select and assign an author to one demo...)
class ChooseAuthorForDemoform(forms.Form):
	#hidden
	demoid = forms.IntegerField(label='demoid',required=False)
	# no need for author id, whe add it from the select or create it
	# select a demo for this author
	# author = forms.ChoiceField(label='author(name,email)',required=True)

	# author = al.ChoiceField('AuthorAutocomplete',label='author(name,email)',required=True)
	author = al.MultipleChoiceField('AuthorAutocomplete',label='author(name,email)',required=True)

	helper = FormHelper()
	helper.form_id = "ChooseAuthorForDemoform"
	helper.form_action = reverse_lazy('ipol.cp.demoinfo.add_existing_author_to_demo')
	helper.form_method = 'POST'
	helper.form_class = 'form-horizontal'
	helper.layout = Layout(
		Field('demoid', type='hidden'),
		# Field('author', css_class='form-control'),
		Field('author', css_class='form-control'),
		FormActions(
			Submit('save_selected_author_for_demo', 'Save', css_class="btn-primary"),
		)
	)

	# ChooseAuthorForDemoform with dropdown select, this is to initialice choice list
	# def __init__(self, *args, **kwargs):
	# 	#dinamic way to get choice values
	# 	initial =  kwargs.get('initial', {})
	# 	author = initial.get('author', None)
	#
	# 	# set just the initial value
	# 	if author:
	# 		kwargs['initial']['author'] = author[0]
	#
	# 	# create the form
	# 	super(ChooseAuthorForDemoform, self).__init__(*args, **kwargs)
	#
	# 	# self.fields only exist after, so a double validation is needed
	# 	if  author :
	# 		# initial authors available for demo (initialized in the view with the proper demoid)
	# 		self.fields['author'].choices = author
	#
	# 	else:
	#
	# 		# all authors
	# 		self.fields['author'].choices=get_demoinfo_available_author_list()

	# cannot do this, i only know the demmid in the view
	# def __init__(self, *args, **kwargs):
	# 	#dinamic way to get staes of demo in demoinfo module
	# 	print "AKI __init__"
	# 	super(ChooseAuthorForDemoform, self).__init__(*args, **kwargs)
	# 	self.fields['author'] = forms.ChoiceField(label='author(name,email)',required=True, choices=get_demoinfo_available_author_list() )
	#


#for now we ignore the editors active flag (true by default)
# for edit Editor
class Editorform(forms.Form):
	#hidden
	id = forms.IntegerField(label='id',required=False)
	#normal
	name = forms.CharField(label='name',required=True)
	mail = forms.EmailField(label='mail',required=True)
	helper = FormHelper()
	helper.form_id = "Editorform"
	helper.form_action = reverse_lazy('ipol.cp.demoinfo.save_editor')
	# helper.form_action = reverse_lazy('ipol.cp.demoinfo.save_demo')
	helper.form_method = 'POST'
	helper.form_class = 'form-horizontal'
	helper.layout = Layout(
		Field('id', type='hidden'),
		Field('name'),
		Field('mail', css_class='form-control'),
		FormActions(
			Submit('save_editor', 'Save', css_class="btn-primary"),
		)
	)


# for new Editor (lets the user create and  assign editor to one demo...)
class DemoEditorform(forms.Form):
	#hidden
	demoid = forms.IntegerField(label='demoid',required=False)
	# no need for editor id, whe add it from the select or create it
	#normal
	name = forms.CharField(label='name',required=True)
	mail = forms.EmailField(label='mail',required=True)
	helper = FormHelper()
	helper.form_id = "DemoEditorform"
	helper.form_action = reverse_lazy('ipol.cp.demoinfo.add_new_editor_to_demo')
	helper.form_method = 'POST'
	helper.form_class = 'form-horizontal'
	helper.layout = Layout(
		Field('demoid', type='hidden'),
		Field('name'),
		Field('mail', css_class='form-control'),
		FormActions(
			Submit('save_editor', 'Save', css_class="btn-primary"),
		)
	)


# # for existing Editor (allows the user to select and assign an editor to one demo...)
# class ChooseEditorForDemoform(forms.Form):
# 	#hidden
# 	demoid = forms.IntegerField(label='demoid',required=False)
# 	# no need for editor id, whe add it from the select or create it
# 	# select a demo for this editor
# 	editor = forms.ChoiceField(label='editor(name,email)',required=True)
# 	helper = FormHelper()
# 	helper.form_id = "ChooseEditorForDemoform"
# 	helper.form_action = reverse_lazy('ipol.cp.demoinfo.add_existing_editor_to_demo')
# 	helper.form_method = 'POST'
# 	helper.form_class = 'form-horizontal'
# 	helper.layout = Layout(
# 		Field('demoid', type='hidden'),
# 		Field('editor', css_class='form-control'),
# 		FormActions(
# 			Submit('save_selected_editor_for_demo', 'Save', css_class="btn-primary"),
# 		)
# 	)
# 	def __init__(self, *args, **kwargs):
# 		#dinamic way to get choice values
# 		initial =  kwargs.get('initial', {})
# 		editor = initial.get('editor', None)
#
# 		# set just the initial value
# 		if editor:
# 			kwargs['initial']['editor'] = editor[0]
#
# 		# create the form
# 		super(ChooseEditorForDemoform, self).__init__(*args, **kwargs)
#
# 		# self.fields only exist after, so a double validation is needed
# 		if  editor :
# 			# initial editors available for demo (initialized in the view with the proper demoid)
# 			self.fields['editor'].choices = editor
# 		else:
# 			# all editors
# 			self.fields['editor'].choices=get_demoinfo_available_editor_list()
#
# 		print
# 		print "self.fields['editor'].choices",self.fields['editor'].choices
# 		print
# for existing Editor (allows the user to select and assign an editor to one demo...)
class ChooseEditorForDemoform(forms.Form):
	#hidden
	demoid = forms.IntegerField(label='demoid',required=False)
	# no need for editor id, whe add it from the select or create it
	# select a demo for this editor
	# editor = al.ChoiceField('EditorAutocomplete',label='editor(name,email)',required=True)
	editor = al.MultipleChoiceField('EditorAutocomplete',label='editor(name,email)',required=True)

	helper = FormHelper()
	helper.form_id = "ChooseEditorForDemoform"
	helper.form_action = reverse_lazy('ipol.cp.demoinfo.add_existing_editor_to_demo')
	helper.form_method = 'POST'
	helper.form_class = 'form-horizontal'
	helper.layout = Layout(
		Field('demoid', type='hidden'),
		Field('editor', css_class='form-control'),
		FormActions(
			Submit('save_selected_editor_for_demo', 'Save', css_class="btn-primary"),
		)
	)


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
