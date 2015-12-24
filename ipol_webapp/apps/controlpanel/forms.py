import json
from crispy_forms.bootstrap import FormActions, PrependedText
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit
from django.core.urlresolvers import reverse, reverse_lazy
from apps.controlpanel.views.ipolwebservices.ipolservices import demoinfo_get_states

__author__ = 'josearrecio'


from django import forms


# Use bootstrap clases for layout

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

# demoinfo states for the demos, pubhished,etc
def get_demoinfo_module_states():
	state_list=None

	try:
		statesjson = demoinfo_get_states()
		statesdict= json.loads(statesjson)
		print "statesdict", statesdict

		state_list= statesdict['state_list']
	except Exception as e:
		msg=" get_demoinfo_module_states Error %s "%e
		print(msg)

	return state_list

#add_demo(self, editorsdemoid, title, abstract, zipURL, active, stateID, demodescriptionID=None, demodescriptionJson=None):
class Demoform(forms.Form):
	#hidden
	id = forms.IntegerField(label='demoid',required=False)
	editorsdemoid = forms.IntegerField(label='editorsdemoid',required=True)
	#normal
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