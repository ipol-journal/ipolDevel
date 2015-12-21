from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit

__author__ = 'josearrecio'


from django import forms


# Use bootstrap clases for layout

class DDLform(forms.Form):

    ddlid = forms.IntegerField(label='ddlid')
    ddlJSON = forms.CharField(label='ddlJSON', max_length=100,widget=forms.Textarea)

    helper = FormHelper()
    helper.form_id="DDLform"
    helper.form_action="/announce"
    helper.form_method = 'POST'
    helper.form_class = 'form-horizontal'

    helper.layout = Layout(
        Field('ddlid', type='hidden'),
        Field('ddlJSON', rows="8", css_class='form-control'),
        FormActions(
            Submit('save_ddl', 'Save', css_class="btn-primary"),

        )
    )
