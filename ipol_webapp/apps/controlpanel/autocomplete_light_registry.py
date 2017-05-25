from django.utils.encoding import force_text
from apps.controlpanel.tools import get_demoinfo_available_author_list, get_demoinfo_available_editor_list

__author__ = 'josearrecio'


import autocomplete_light.shortcuts as al

# examples and doc
# class OsAutocomplete(al.AutocompleteListBase):
#     choices = ['Linux', 'BSD', 'Minix']

# class OsAutocomplete(al.AutocompleteChoiceListBase):
#     choices = ((1,'Linux'), (2,'BSD'), (3,'Minix'))
#     # choice_html_format = '<span data-value="%s">%s</span>'
#http://django-autocomplete-light.readthedocs.org/en/master/
#http://django-autocomplete-light.readthedocs.org/en/master/autocomplete.html?highlight=shortcuts#examples
#http://django-autocomplete-light.readthedocs.org/en/master/tutorial.html

class AuthorAutocomplete(al.AutocompleteChoiceListBase):
# class AuthorAutocomplete(al.AutocompleteChoiceListTemplate):
    """
    In DemoinfoGetDemoAuthorView I store the demo_id (in session var authors_avilable_for_demo_id)so I can filter the
    author for this demo_id when I prepare the
    form, thanks to choices_for_request

    This is so I can present a list of authors not currently assiged to the demo ChooseAuthorForDemoform form
    """

    choices = []

    def choices_for_request(self):


        # print ""
        # print "choices_for_request", self.choices
        # print ""

        authors_avilable_for_demo_id = self.request.session['authors_avilable_for_demo_id']

        try:
            authors_avilable_for_demo_id=int(authors_avilable_for_demo_id)
            available_autor_list = get_demoinfo_available_author_list(authors_avilable_for_demo_id)
        except Exception as e:
            available_autor_list = get_demoinfo_available_author_list()

        # print " --available_autor_list", available_autor_list

        requests_choices = []
        q = self.request.GET.get('q', '').lower().strip()

        for choice in available_autor_list:
            m = force_text(choice[0]).lower() + force_text(choice[1]).lower()
            if q in m:
                requests_choices.append(choice)

        return self.order_choices(requests_choices)[0:self.limit_choices]


    def choices_for_values(self):
        """
        Return any :py:attr:`choices` that is in :py:attr:`values`.

        used in validate, it only does return len(self.choices_for_values()) == len(self.values)

        self.values=[u'1'] so i must convert choice id from int to str so it finds it and retrns it in values_choices
        this may be a bug of autocomplete


        """
        values_choices = []

        #add choices...its possible that new authors where added
        self.choices = get_demoinfo_available_author_list()

        # print ""
        # print "choices_for_request", self.choices
        # print ""

        #self.values=[1] y salva...es pq le llega self.values=[u'1']
        for choice in self.choices:

            # print "int(choice[0])",force_text(choice[0])
            # print "self.values",self.values
            if force_text(choice[0]) in self.values:
                values_choices.append(choice)

        # print()
        # print " +++ self.choices" , self.choices
        # print " +++ self.values" , self.values
        # print " +++ values_choices" , values_choices
        # print()

        return self.order_choices(values_choices)


al.register(AuthorAutocomplete)



class EditorAutocomplete(al.AutocompleteChoiceListBase):
    """
    In DemoinfoGetDemoEditorView I store the demo_id (in session var editors_avilable_for_demo_id)so I can filter the
    editor for this demo_id when I prepare the
    form, thanks to choices_for_request

    This is so I can present a list of editors not currently assiged to the demo in ChooseEditorForDemoform form
    """

    choices = []

    def choices_for_request(self):

        editors_avilable_for_demo_id = self.request.session.get('editors_avilable_for_demo_id')

        try:
            if editors_avilable_for_demo_id:
                editors_avilable_for_demo_id=int(editors_avilable_for_demo_id)
            available_editor_list = get_demoinfo_available_editor_list(editors_avilable_for_demo_id)
        except Exception as e:
            available_editor_list = get_demoinfo_available_editor_list()

        requests_choices = []
        q = self.request.GET.get('q', '').lower().strip()

        for choice in available_editor_list:
            m = force_text(choice[0]).lower() + force_text(choice[1]).lower()
            if q in m:
                requests_choices.append(choice)

        return self.order_choices(requests_choices)[0:self.limit_choices]


    def choices_for_values(self):
        """
        Return any :py:attr:`choices` that is in :py:attr:`values`.

        used in validate, it only does return len(self.choices_for_values()) == len(self.values)

        self.values=[u'1'] so i must convert choice id from int to str so it finds it and retrns it in values_choices
        this may be a bug of autocomplete


        """
        values_choices = []

        self.choices =  get_demoinfo_available_editor_list()

        #self.values=[1] y salva...es pq le llega self.values=[u'1']
        for choice in self.choices:

            # print "int(choice[0])",force_text(choice[0])
            # print "self.values",self.values
            if force_text(choice[0]) in self.values:
                values_choices.append(choice)

        # print()
        # print " +++ self.choices" , self.choices
        # print " +++ self.values" , self.values
        # print " +++ values_choices" , values_choices
        # print()


        return self.order_choices(values_choices)


al.register(EditorAutocomplete)
