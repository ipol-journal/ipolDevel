# from crispy_forms.utils import render_crispy_form
# from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import json
from django.http import HttpResponse, HttpResponseRedirect
from apps.controlpanel.forms import DDLform, Demoform, Authorform, DemoAuthorform, ChooseAuthorForDemoform, Editorform, \
        DemoEditorform, ChooseEditorForDemoform
from apps.controlpanel.mixings import NavbarReusableMixinMF

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, FormView
from apps.controlpanel.tools import get_status_and_error_from_json, convert_str_to_bool,get_demoinfo_available_author_list, \
        get_demoinfo_available_editor_list, get_demoinfo_module_states
from apps.controlpanel.views.ipolwebservices.ipoldeserializers import DeserializeDemoinfoDemoList, \
        DeserializeDemoinfoAuthorList, DeserializeDemoinfoEditorList,DeserializeDemoinfoDemoExtrasList
from apps.controlpanel.views.ipolwebservices import ipolservices
import logging
from apps.controlpanel.views.ipolwebservices.ipolservices import is_json, demoinfo_get_states
from django import forms

logger = logging.getLogger(__name__)

__author__ = 'josearrecio'


# pagination settings for demoinfo

PAGINATION_ITEMS_PER_PAGE_DEMO_LIST = 4
PAGINATION_ITEMS_PER_PAGE_AUTHOR_LIST = 4
PAGINATION_ITEMS_PER_PAGE_EDITOR_LIST = 4
PAGINATION_ITEMS_PER_PAGE_DEMO_EXTRAS_LIST = 4


# demos

class DemoinfoDemosView(NavbarReusableMixinMF,TemplateView):
    template_name = "demoinfo/demoinfo_demos.html"


    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        # para las pestanas
        self.request.session['topmenu'] = 'topmenu-demoinfo-demos'
        self.request.session['menu'] = 'menu-demoinfo'
        return super(DemoinfoDemosView, self).dispatch(*args, **kwargs)


    def get_context_data(self, **kwargs):
        # I work with contex because I have to manage the filtering and pagination, so i refere to do this in context
        #  instead of using different functions in the view object like I do in ArchiveDemosView's method list_demos


        #get context
        context = super(DemoinfoDemosView, self).get_context_data(**kwargs)

        try:

            #get data from WS, paginate and filter in CP (using django pagination)

            #dl = ipolservices.demoinfo_demo_list()
            # if dl:
            #       result = DeserializeDemoinfoDemoList(dl)
            # else:
            #       raise ValueError("No response from WS")
            #
            # list_demos = result.demo_list
            # status = result.status
            #
            # #filter result
            # query = self.request.GET.get('q')
            # # print "query",query
            # list_demos_filtered = list()
            # if query:
            #       for demo in list_demos:
            #               # print "demo: ",demo
            #               if query in demo.title or query in demo.abstract :
            #                       print "ok"
            #                       list_demos_filtered.append(demo)
            #
            #       list_demos = list_demos_filtered
            # context['q'] = query
            #
            # #pagination of result
            # paginator = Paginator(list_demos, PAGINATION_ITEMS_PER_PAGE_DEMO_LIST)
            # page = self.request.GET.get('page')
            # try:
            #       list_demos = paginator.page(page)
            # except PageNotAnInteger:
            #       # If page is not an integer, deliver first page.
            #       list_demos = paginator.page(1)
            # except EmptyPage:
            #       # If page is out of range (e.g. 9999), deliver last page of results.
            #       list_demos = paginator.page(paginator.num_pages)


            #get data from WS paginated and filtered

            #filter result
            query = self.request.GET.get('q')
            context['q'] = query
            try:
                page = self.request.GET.get('page')
                page = int(page)
            except :
                # If page is not an integer, deliver first page.
                page = 1


            dl = ipolservices.demoinfo_demo_list_pagination_and_filtering(PAGINATION_ITEMS_PER_PAGE_DEMO_LIST,page,query)
            if dl:
                result = DeserializeDemoinfoDemoList(dl)
            else:
                raise ValueError("No response from WS")

            list_demos = result.demo_list

            print "list_demos",list_demos
            status = result.status

            #pagination of result
            if hasattr(result, 'previous_page_number'):
                context['previous_page_number'] = result.previous_page_number
                context['has_previous'] = True
            else:
                context['has_previous'] = False

            if page:
                context['number'] = page

            if hasattr(result, 'number'):
                context['num_pages'] = result.number

            if hasattr(result, 'next_page_number'):
                context['next_page_number'] = result.next_page_number
                context['has_next'] = True
            else:
                context['has_next'] = False


            #send context vars for template
            context['status'] = status
            context['list_demos'] = list_demos
            context['ddlform'] = DDLform
            context['demoform'] = Demoform
            context['states'] = get_demoinfo_module_states()

        except Exception as e:

            msg=" DemoinfoDemosView Error %s "%e
            logger.error(msg)
            context['status'] = 'KO'
            context['list_demos'] = []
            context['ddlform'] = None
            context['demoform'] = None
            context['states'] = None
            logger.error(msg)
            print(msg)


        return context


class DemoinfoDeleteDemoView(NavbarReusableMixinMF,TemplateView):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DemoinfoDeleteDemoView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):

        try:
            demo_id = int(self.kwargs['demo_id'])
        except ValueError:
            msg= "Id is not an integer"
            logger.error(msg)
            raise ValueError(msg)

        result= ipolservices.demoinfo_delete_demo(demo_id)
        if result == None:
            msg="DemoinfoDeleteDemoView: Something went wrong using demoinfo WS"
            logger.error(msg)
            raise ValueError(msg)

        print result

        return HttpResponse(result, content_type='application/json')


class DemoinfoGetDDLView(NavbarReusableMixinMF,TemplateView):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DemoinfoGetDDLView, self).dispatch(*args, **kwargs)

    def post(self, *args, **kwargs):


        try:
            demo_id = int(self.kwargs['demo_id'])
        except ValueError:
            msg= "Id is not an integer"
            logger.error(msg)
            raise ValueError(msg)


        result= ipolservices.demoinfo_read_last_demodescription_from_demo(demo_id,returnjsons=True)
        if result == None:
            msg="DemoinfoGetDDLView: Something went wrong using demoinfo WS"
            print msg
            logger.error(msg)
            #raise ValueError(msg)
            data=dict()
            data["status"] = "KO"
            data["error"] = "msg"


        import json
        #your_json = '["foo", {"bar":["baz", null, 1.0, 2]}]'
        # parsed = json.loads(result)
        # result = json.dumps(parsed, indent=4, sort_keys=True)

        # print "result: ",result
        # print "result type: ",type(result)

        return HttpResponse(result,content_type='application/json')


class DemoinfoSaveDDLView(NavbarReusableMixinMF,FormView):

    template_name = ''
    form_class = DDLform

    def form_valid(self, form):
        """
        If the request is ajax, save the form and return a json response.
        Otherwise return super as expected.
        """
        jres=dict()
        jres['status'] = 'KO'
        if self.request.is_ajax():

            print "valid ajax form"

            # get form fields and send info to be saved in demoinfo
            demoid = None
            ddlJSON = None
            try:
                demoid = form.cleaned_data['demoid']
                demoid = int(demoid)
                ddlJSON = form.cleaned_data['ddlJSON']
            except Exception as e:
                msg = "DemoinfoSaveDDLView form: %s" % e
                print msg
                logger.error(msg)

            # save
            if ddlJSON is not None:

                print "is_json(ddlJSON)",is_json(ddlJSON)
                if is_json(ddlJSON):
                    try:
                        jsonresult = ipolservices.demoinfo_save_demo_description(pjson=ddlJSON, demoid=demoid)
                        status, error = get_status_and_error_from_json(jsonresult)
                        jres['status'] = status
                        if error is not None:
                            jres['error'] = error

                    except Exception as e:
                        msg = "update ddl error: %s" % e
                        logger.error(msg)
                        print msg

                else:
                    msg='DemoinfoSaveDDLView invalid json'
                    logger.warning(msg)
                    jres['error'] = msg
            else:
                msg='DemoinfoSaveDDLView no json found'
                logger.warning(msg)
                jres['error'] = msg
        else:
            jres['error'] = 'form_valid no ajax'
            #print "check Jquery form submit, something is wrong with ajax call"
            logger.warning('DemoinfoSaveDDLView form_valid ,but no ajax')

        return HttpResponse(json.dumps(jres),content_type='application/json')
        #
        # print "not valid ajax form"
        # return super(DemoinfoSaveDDLView, self).form_valid(form)

    def form_invalid(self, form):
        """
        We have errors in the form. If ajax, return them as json.
        Otherwise, proceed as normal.
        """

        jres = dict()
        if self.request.is_ajax():

            print "invalid ajax form"
            print form.errors
            print form

            #form CON ERORRES, se lo puedo pasar al JS...pero si substituyo el form actual por este..pierdo el submit ajax.
            # form_html = render_crispy_form(form)
            # logger.warning(form_html)

            jres['form_html'] = str(form.errors)
            jres['status'] = 'KO'
        else:
            jres['status'] = 'form_invalid no ajax'
            logger.warning('form_invalid no ajax')

        #return HttpResponseBadRequest(json.dumps(form.errors),mimetype="application/json")
        return HttpResponse(json.dumps(jres),content_type='application/json')
        # return super(DemoinfoSaveDDLView, self).form_invalid(form)


class DemoinfoGetDemoView(NavbarReusableMixinMF,TemplateView):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DemoinfoGetDemoView, self).dispatch(*args, **kwargs)

    def post(self, *args, **kwargs):

            # print "DemoinfoGetDemoView"
        try:
            demo_id = int(self.kwargs['demo_id'])
        except ValueError:
            msg= "Id is not an integer"
            logger.error(msg)
            raise ValueError(msg)

        print "La demo id es:",demo_id
        result= ipolservices.demoinfo_read_demo(demo_id)
        if result == None:
            msg="DemoinfoGetDemoView: Something went wrong using demoinfo WS"
            logger.error(msg)
            raise ValueError(msg)


        # print "Demoinfo  DemoinfoGetDemoView result: ",result
        # print "result type: ",type(result)
        print "la respuesta es ",HttpResponse(result,content_type='application/json')
        return HttpResponse(result,content_type='application/json')


class DemoinfoSaveDemoView(NavbarReusableMixinMF,FormView):

    template_name = ''
    form_class = Demoform

    logger.warning("________________DemoinfoSaveDemoView")

    def form_valid(self, form):

        jres = dict()
        jres['status'] = 'KO'

        """
        If the request is ajax, save the form and return a json response.
        Otherwise return super as expected.
        """
        if self.request.is_ajax():

        # print "valid ajax form"
        # print form
        # print

        # get form fields
            id = None
            title = None
            abstract = None
            state = None
            editorsdemoid = None
            zipURL = None
            # creation = None
            # modification = None
            # if form has id field set, I must update, if not, create a new demo
            try:
                old_editor_demoid = form.cleaned_data['id']
                old_editor_demoid = int(old_editor_demoid)
            except Exception :
                pass

            try:
                title = form.cleaned_data['title']
                abstract = form.cleaned_data['abstract']
                state = form.cleaned_data['state']
                editorsdemoid = form.cleaned_data['editorsdemoid']
                editorsdemoid = int(editorsdemoid)

                zipURL = form.cleaned_data['zipURL']
                # creation = form.cleaned_data['creation']
                # modification = form.cleaned_data['modification']
                # print " title ",title
                # print
                #print " json.dumps(ddlJSON) ",json.dumps(ddlJSON, indent=4)
            except Exception as e:
                msg = "DemoinfoSaveDemoView form data error: %s" % e
                print msg
                logger.error(msg)

            #  send info to be saved in demoinfo module
            # save
            if old_editor_demoid is None :

                try:
                    # print (" create demo")
                    # print

                    jsonresult= ipolservices.demoinfo_add_demo(editorsdemoid ,title ,abstract, zipURL, state)
                    print "jsonresult", jsonresult
                    status,error = get_status_and_error_from_json(jsonresult)
                    jres['status'] = status
                    if error is not None:
                        jres['error'] = error

                except Exception as e:
                    msg = "create demo error: %s" % e
                    jres['error'] = msg
                    logger.error(msg)
                    print msg
            else:
                try:
                    # print (" update demo ")
                    # print
                    demojson = {
                                            "title": title,
                                            "abstract": abstract,
                                            "editorsdemoid": editorsdemoid,
                                            "state": state,
                                            # "id": id,
                                            "zipURL": zipURL,
                                            # "creation": creation,
                                            # "modification": modification
                    }
                    jsonresult = ipolservices.demoinfo_update_demo(demojson,old_editor_demoid)
                    status,error = get_status_and_error_from_json(jsonresult)
                    jres['status'] = status
                    if error is not None:
                        jres['error'] = error

                    #TODO todos los WS deben devolver status y errors, asi se lo paso directamente al html
                except Exception as e:
                    msg = "update demo error: %s" % e
                    jres['error'] = msg
                    logger.error(msg)
                    print msg

        else:
            jres['error'] = 'form_valid no ajax'
            logger.error('DemoinfoSaveDemoView form_valid no ajax')


        return HttpResponse(json.dumps(jres),content_type='application/json')
        #
        # print "not valid ajax form"
        # return super(DemoinfoSaveDDLView, self).form_valid(form)

    def form_invalid(self, form):
        """
        We haz errors in the form. If ajax, return them as json.
        Otherwise, proceed as normal.
        """
        jres = dict()
        jres['status'] = 'KO'
        if self.request.is_ajax():


            jres['error'] = str(form.errors)

        else:
            jres['error'] = 'form_invalid no ajax'
            logger.warning('form_invalid no ajax')

        #return HttpResponseBadRequest(json.dumps(form.errors),mimetype="application/json")
        return HttpResponse(json.dumps(jres),content_type='application/json')
        # return super(DemoinfoSaveDDLView, self).form_invalid(form)

#authors

class DemoinfoAuthorsView(NavbarReusableMixinMF,TemplateView):
    template_name = "demoinfo/demoinfo_authors.html"


    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        # para las pestanas
        self.request.session['topmenu'] = 'topmenu-demoinfo-authors'
        return super(DemoinfoAuthorsView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):

        #get context
        context = super(DemoinfoAuthorsView, self).get_context_data(**kwargs)

        try:

            #filter result
            query = self.request.GET.get('q')
            context['q'] = query
            try:
                page = self.request.GET.get('page')
                page = int(page)
            except :
                # If page is not an integer, deliver first page.
                page = 1

            al = ipolservices.demoinfo_author_list_pagination_and_filtering(PAGINATION_ITEMS_PER_PAGE_AUTHOR_LIST,page,query)
            if al:
                result = DeserializeDemoinfoAuthorList(al)
            else:
                raise ValueError("No response from WS")

            list_authors = result.author_list
            # print "list_authors",list_authors
            status = result.status

            #pagination of result
            if hasattr(result, 'previous_page_number'):
                context['previous_page_number'] = result.previous_page_number
                context['has_previous'] = True
            else:
                context['has_previous'] = False

            if page:
                context['number'] = page

            if hasattr(result, 'number'):
                context['num_pages'] = result.number

            if hasattr(result, 'next_page_number'):
                context['next_page_number'] = result.next_page_number
                context['has_next'] = True
            else:
                context['has_next'] = False


            #send context vars for template
            context['status'] = status
            context['list_authors'] = list_authors
            context['authorform'] = Authorform

        except Exception as e:

            msg=" DemoinfoAuthorformView Error %s "%e
            logger.error(msg)
            context['status'] = 'KO'
            context['list_authors'] = []
            context['authorform'] = None
            logger.error(msg)
            print(msg)


        return context


class DemoinfoDeleteAuthorView(NavbarReusableMixinMF,TemplateView):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DemoinfoDeleteAuthorView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):

        try:
            author_id = int(self.kwargs['author_id'])
        except ValueError:
            msg= "Id is not an integer"
            logger.error(msg)
            raise ValueError(msg)

        result= ipolservices.demoinfo_delete_author(author_id)
        if result == None:
            msg="DemoinfoDeleteAuthorView: Something went wrong using demoinfo WS"
            logger.error(msg)
            raise ValueError(msg)

        print result

        return HttpResponse(result, content_type='application/json')


class DemoinfoGetAuthorView(NavbarReusableMixinMF,TemplateView):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DemoinfoGetAuthorView, self).dispatch(*args, **kwargs)

    def post(self, *args, **kwargs):
        # print "DemoinfoGetAuthorView"
        try:
            author_id = int(self.kwargs['author_id'])
        except ValueError:
            msg= "Id is not an integer"
            logger.error(msg)
            raise ValueError(msg)

        result= ipolservices.demoinfo_read_author(author_id)
        if result == None:
            msg="DemoinfoGetAuthorView: Something went wrong using demoinfo WS"
            logger.error(msg)
            raise ValueError(msg)


        # print "Demoinfo  DemoinfoGetAuthorView result: ",result
        # print "result type: ",type(result)

        return HttpResponse(result,content_type='application/json')


class DemoinfoSaveAuthorView(NavbarReusableMixinMF,FormView):

    template_name = ''
    form_class = Authorform


    def form_valid(self, form):

        jres = dict()
        jres['status'] = 'KO'

        # print "valid form"


        if self.request.is_ajax():

        # print "valid ajax form"
        # print form
        # print

        # get form fields
            id = None
            name = None
            mail = None
            # creation = None
            # if form has id field set, I must update, if not, create a new demo
            try:
                id = form.cleaned_data['id']
                id = int(id)
                print " id ",id
            except Exception :
                id = None
            try:
                name = form.cleaned_data['name']
                mail = form.cleaned_data['mail']
                # print " name ",name
                # print
                #print " json.dumps(ddlJSON) ",json.dumps(ddlJSON, indent=4)
            except Exception as e:
                msg = "DemoinfoSaveAuthorView form data error: %s" % e
                print msg
                logger.error(msg)

            #  send info to be saved in demoinfo module
            # save
            if id is None :

                try:
                    # print (" create author")
                    # print

                    jsonresult = ipolservices.demoinfo_add_author(name,mail)
                    print "jsonresult", jsonresult
                    status,error = get_status_and_error_from_json(jsonresult)
                    jres['status'] = status
                    if error is not None:
                        jres['error'] = error

                except Exception as e:
                    msg = "create author error: %s" % e
                    jres['error'] = msg
                    logger.error(msg)
                    print msg
            else:
                try:
                    print (" update author ")
                    print
                    demojson = {
                                            "id": id,
                                            "name": name,
                                            "mail": mail
                                            # "creation": creation
                    }
                    jsonresult = ipolservices.demoinfo_update_author(demojson)
                    status,error = get_status_and_error_from_json(jsonresult)
                    jres['status'] = status
                    if error is not None:
                        jres['error'] = error
                        print jres['error']

                    #TODO todos los WS deben devolver status y errors, asi se lo paso directamente al html
                except Exception as e:
                    msg = "update author error: %s" % e
                    jres['error'] = msg
                    logger.error(msg)
                    print msg

        else:
            jres['error'] = 'form_valid no ajax'
            logger.warning('DemoinfoSaveAuthorView form_valid no ajax')


        return HttpResponse(json.dumps(jres),content_type='application/json')


    def form_invalid(self, form):

        jres = dict()
        jres['status'] = 'KO'
        print "invalid form"

        if self.request.is_ajax():

            print " ---invalid ajax form"
            print form.errors
            print form

            #form CON ERORRES, se lo puedo pasar al JS...pero si substituyo el form actual por este..pierdo el submit ajax.
            # form_html = render_crispy_form(form)
            # logger.warning(form_html)

            jres['error'] = str(form.errors)
            jres['status'] = 'KO'

        else:
            jres['error'] = 'form_invalid no ajax'
            logger.warning('form_invalid no ajax')

        return HttpResponse(json.dumps(jres),content_type='application/json')


# demo-authors


class DemoinfoGetDemoAuthorView(NavbarReusableMixinMF,TemplateView):

    template_name = "demoinfo/manage_authors_for_demo.html"


    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DemoinfoGetDemoAuthorView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):

        #get context
        context = super(DemoinfoGetDemoAuthorView, self).get_context_data(**kwargs)

        try:

            demo_id=None
            try:
                demo_id = self.kwargs['demo_id']
                demo_id = int(demo_id)
            except Exception as e:
                msg="Error getting param for list_authors_for_demo %s"%e
                print(msg)

            #send context vars for template
            context['demo_id'] = demo_id

            # ChooseAuthorForDemoform with dropdown select
            # available_autor_list = get_demoinfo_available_author_list(demo_id)
            # initial_author_choicedict={'author':available_autor_list }
            # context['choosedemoauthorform'] = ChooseAuthorForDemoform(initial=initial_author_choicedict)


            # ChooseAuthorForDemoform with autocomplete
            self.request.session['authors_avilable_for_demo_id']= demo_id
            context['choosedemoauthorform'] = ChooseAuthorForDemoform()
            context['demoauthorform'] = DemoAuthorform
            context['authorform'] = Authorform

        except Exception as e:

            msg=" DemoinfoGetDemoAuthorView Error %s "%e
            logger.error(msg)
            context['demo_id'] = None
            context['choosedemoauthorform'] = None
            context['demoauthorform'] = None
            context['authorform'] = None
            logger.error(msg)
            print(msg)


        return context

    # no need for filtering and pagination
    def list_authors_for_demo(self):
        result = None
        try:
            try:
                demo_id = self.kwargs['demo_id']
                demo_id = int(demo_id)
            except Exception as e:
                msg="Error getting param for list_authors_for_demo %s"%e
                print(msg)
                pass

            # print "  list_authors_for_demo demoid: ", demo_id
            page_json = ipolservices.demoinfo_author_list_for_demo(demo_id)
            result = DeserializeDemoinfoAuthorList(page_json)

        except Exception as e:
            msg="Error list_authors_for_demo %s"%e
            logger.error(msg)
            print(msg)

        return result


class DemoinfoAddExistingAuthorToDemoView(NavbarReusableMixinMF,FormView):
    ##one save view for all two different forms used in modals? nope, better to have different views for each ajax call

    template_name = ''
    form_class = ChooseAuthorForDemoform


    def form_valid(self, form):

        jres = dict()
        jres['status'] = 'KO'

        if self.request.is_ajax():

            # get form fields
            demoid = None
            authorid = None
            authorid_list = None
            choicefielddata =None

            try:
                demoid = form.cleaned_data['demoid']
                demoid = int(demoid)

                # simple/multiple choicefield data,
                # In ChooseAuthorForDemoform  change author form field to MultipleChoiceField or ChoiceField
                choicefielddata = form.cleaned_data['author']

                if type(choicefielddata) is not list:
                    #simple choicefield
                    authorid = choicefielddata
                    # print "authorid", authorid
                else:
                    #simple choicefield
                    authorid_list = choicefielddata
                    # print "authorid_list", authorid_list


            except Exception as e:
                msg = "DemoinfoAddExistingAuthorToDemoView form data error: %s" % e
                jres['error'] = msg
                print msg
                logger.error(msg)

            #  send info to be saved in demoinfo module to be saved
            try:

                if type(choicefielddata) is not list:
                    #multiple choicefield

                    jsonresult = ipolservices.demoinfo_add_author_to_demo(demoid,authorid)
                    status,error = get_status_and_error_from_json(jsonresult)
                    jres['status'] = status
                    if error is not None:
                        jres['error'] = error
                else:
                    #multiple choicefield
                    #todo improvement: wds in demoinfo that adds a list of authors to demo

                    for id in authorid_list:
                        id=int(id)
                        jsonresult = ipolservices.demoinfo_add_author_to_demo(demoid,id)
                        status,error = get_status_and_error_from_json(jsonresult)
                        jres['status'] = status
                        if error is not None:
                            jres['error'] = error

            except Exception as e:
                msg = " DemoinfoAddExistingAuthorToDemoView error: %s" % e
                jres['error'] = msg
                logger.error(msg)
                print msg
        else:
            jres['error'] = 'form_valid no ajax'
            logger.warning('DemoinfoAddExistingAuthorToDemoView form_valid no ajax')


        return HttpResponse(json.dumps(jres),content_type='application/json')


    def form_invalid(self, form):

        jres = dict()
        jres['status'] = 'KO'
        print "invalid form"

        if self.request.is_ajax():

            # print " invalid ajax ChooseAuthorForDemoform"
            # print form.errors
            # print form
            #form CON ERORRES, se lo puedo pasar al JS...pero si substituyo el form actual por este..pierdo el submit ajax.
            # form_html = render_crispy_form(form)
            # logger.warning(form_html)

            jres['error'] = str(form.errors)
            jres['status'] = 'KO'

        else:
            jres['error'] = 'form_invalid no ajax'
            logger.warning('form_invalid no ajax')

        return HttpResponse(json.dumps(jres),content_type='application/json')


class DemoinfoAddNewAuthorToDemoView(NavbarReusableMixinMF,FormView):

    template_name = ''
    form_class = DemoAuthorform


    def form_valid(self, form):

        jres = dict()
        jres['status'] = 'KO'

        print "valid form"


        if self.request.is_ajax():

            # get form fields
            demoid = None
            name = None
            mail = None

            try:
                demoid = form.cleaned_data['demoid']
                demoid = int(demoid)
                name = form.cleaned_data['name']
                mail = form.cleaned_data['mail']
            except Exception as e:
                msg = "DemoinfoAddNewAuthorToDemoView form data error: %s" % e
                jres['error'] = msg
                print msg
                logger.error(msg)

            #  send info to be saved in demoinfo module to be saved

            # create author
            try:

                jsonresult = ipolservices.demoinfo_add_author(name,mail)
                resultdict = json.loads(jsonresult)
                status = resultdict['status']
                authorid = resultdict['authorid']
                authorid = int(authorid)
                if status != 'OK' or 'error' in resultdict:
                    msg= " DemoinfoAddNewAuthorToDemoView Could not create author "
                    logger.error(msg)
                    raise ValueError(msg+resultdict['error'])


                # add author to demo
                try:
                    jsonresult = ipolservices.demoinfo_add_author_to_demo(demoid,authorid)
                    print "jsonresult author to demo", jsonresult
                    status,error = get_status_and_error_from_json(jsonresult)
                    jres['status'] = status
                    if error is not None:
                        jres['error'] = error
                except Exception as e:
                    msg = " DemoinfoAddNewAuthorToDemoView add author to demo error: %s" % e
                    jres['error'] = msg
                    logger.error(msg)
                    print msg

            except Exception as e:
                msg = " DemoinfoAddNewAuthorToDemoView create author error: %s" % e
                jres['error'] = msg
                logger.error(msg)
                print msg

        else:
            jres['error'] = 'form_valid no ajax'
            logger.warning('DemoinfoAddExistingAuthorToDemoView form_valid no ajax')


        return HttpResponse(json.dumps(jres),content_type='application/json')


    def form_invalid(self, form):

        jres = dict()
        jres['status'] = 'KO'
        print "invalid form"

        if self.request.is_ajax():

            print " invalid ajax form"
            print form.errors
            print form

            jres['error'] = str(form.errors)
            jres['status'] = 'KO'

        else:
            jres['error'] = 'form_invalid no ajax'
            logger.warning('form_invalid no ajax')

        return HttpResponse(json.dumps(jres),content_type='application/json')


class DemoinfoDeleteAuthorFromDemoView(NavbarReusableMixinMF,TemplateView):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DemoinfoDeleteAuthorFromDemoView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):


        try:
            author_id = int(self.kwargs['author_id'])
            demo_id = int(self.kwargs['demo_id'])
        except ValueError:
            msg= "Id is not an integer"
            logger.error(msg)
            raise ValueError(msg)

        result= ipolservices.demoinfo_delete_author_from_demo(demo_id,author_id)
        if result == None:
            msg="DemoinfoDeleteAuthorFromDemoView: Something went wrong using demoinfo WS"
            logger.error(msg)
            raise ValueError(msg)

        print result

        return HttpResponse(result, content_type='application/json')


#editors


class DemoinfoEditorsView(NavbarReusableMixinMF,TemplateView):

    template_name = "demoinfo/demoinfo_editors.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        # para las pestanas
        self.request.session['topmenu'] = 'topmenu-demoinfo-editors'
        return super(DemoinfoEditorsView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):

        #get context
        context = super(DemoinfoEditorsView, self).get_context_data(**kwargs)

        try:

            #filter result
            query = self.request.GET.get('q')
            context['q'] = query
            try:
                page = self.request.GET.get('page')
                page = int(page)
            except :
                # If page is not an integer, deliver first page.
                page = 1

            el = ipolservices.demoinfo_editor_list_pagination_and_filtering(PAGINATION_ITEMS_PER_PAGE_AUTHOR_LIST,page,query)
            if el:
                result = DeserializeDemoinfoEditorList(el)
            else:
                raise ValueError("No response from WS")

            list_editors = result.editor_list
            # print "list_editors",list_editors
            status = result.status

            #pagination of result
            if hasattr(result, 'previous_page_number'):
                context['previous_page_number'] = result.previous_page_number
                context['has_previous'] = True
            else:
                context['has_previous'] = False

            if page:
                context['number'] = page

            if hasattr(result, 'number'):
                context['num_pages'] = result.number

            if hasattr(result, 'next_page_number'):
                context['next_page_number'] = result.next_page_number
                context['has_next'] = True
            else:
                context['has_next'] = False


            #send context vars for template
            context['status'] = status
            context['list_editors'] = list_editors
            context['editorform'] = Editorform

        except Exception as e:

            msg=" DemoinfoEditorsView Error %s "%e
            logger.error(msg)
            context['status'] = 'KO'
            context['list_editors'] = []
            context['editorform'] = None
            logger.error(msg)
            print(msg)


        return context


class DemoinfoDeleteEditorView(NavbarReusableMixinMF,TemplateView):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DemoinfoDeleteEditorView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):

            #todo could validate a form to get hard_delete checkbox from user
        try:
            editor_id = int(self.kwargs['editor_id'])
        except ValueError:
            msg= "Id is not an integer"
            logger.error(msg)
            raise ValueError(msg)

        result= ipolservices.demoinfo_delete_editor(editor_id)
        if result == None:
            msg="DemoinfoDeleteEditorView: Something went wrong using demoinfo WS"
            logger.error(msg)
            raise ValueError(msg)

        print result

        return HttpResponse(result, content_type='application/json')


class DemoinfoGetEditorView(NavbarReusableMixinMF,TemplateView):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DemoinfoGetEditorView, self).dispatch(*args, **kwargs)

    def post(self, *args, **kwargs):
        # print "DemoinfoGetEditorView"
        try:
            editor_id = int(self.kwargs['editor_id'])
        except ValueError:
            msg= "Id is not an integer"
            logger.error(msg)
            raise ValueError(msg)

        result= ipolservices.demoinfo_read_editor(editor_id)
        if result == None:
            msg="DemoinfoGetEditorView: Something went wrong using demoinfo WS"
            logger.error(msg)
            raise ValueError(msg)


        # print "Demoinfo  DemoinfoGetEditorView result: ",result
        # print "result type: ",type(result)

        return HttpResponse(result,content_type='application/json')


class DemoinfoSaveEditorView(NavbarReusableMixinMF,FormView):

    template_name = ''
    form_class = Editorform

    def form_valid(self, form):

        jres = dict()
        jres['status'] = 'KO'

        # print "valid form"


        if self.request.is_ajax():

            print "valid ajax form"
            print form
            print

            # get form fields
            id = None
            name = None
            mail = None
            # creation = None
            # if form has id field set, I must update, if not, create a new demo
            try:
                id = form.cleaned_data['id']
                id = int(id)
                print " id ",id
            except Exception :
                id = None
            try:
                name = form.cleaned_data['name']
                mail = form.cleaned_data['mail']
                # print " name ",name
                # print
                #print " json.dumps(ddlJSON) ",json.dumps(ddlJSON, indent=4)
            except Exception as e:
                msg = "DemoinfoSaveEditorView form data error: %s" % e
                print msg
                logger.error(msg)

            #  send info to be saved in demoinfo module
            # save
            if id is None :

                try:
                    # print (" create editor")
                    # print

                    jsonresult = ipolservices.demoinfo_add_editor(name,mail)
                    print "jsonresult", jsonresult
                    status,error = get_status_and_error_from_json(jsonresult)
                    jres['status'] = status
                    if error is not None:
                        jres['error'] = error

                except Exception as e:
                    msg = "create editor error: %s" % e
                    jres['error'] = msg
                    logger.error(msg)
                    print msg
            else:
                try:
                    print (" update editor ")
                    print
                    demojson = {
                                            "id": id,
                                            "name": name,
                                            "mail": mail
                                            # "creation": creation
                    }
                    jsonresult = ipolservices.demoinfo_update_editor(demojson)
                    status,error = get_status_and_error_from_json(jsonresult)
                    jres['status'] = status
                    if error is not None:
                        jres['error'] = error
                        print jres['error']


                except Exception as e:
                    msg = "update editor error: %s" % e
                    jres['error'] = msg
                    logger.error(msg)
                    print msg

        else:
            jres['error'] = 'form_valid no ajax'
            logger.warning('DemoinfoSaveEditorView form_valid no ajax')


        return HttpResponse(json.dumps(jres),content_type='application/json')


    def form_invalid(self, form):

        jres = dict()
        jres['status'] = 'KO'
        print "invalid form"

        if self.request.is_ajax():

            print " ---invalid ajax form"
            print form.errors
            print form

            #form CON ERORRES, se lo puedo pasar al JS...pero si substituyo el form actual por este..pierdo el submit ajax.
            # form_html = render_crispy_form(form)
            # logger.warning(form_html)

            jres['error'] = str(form.errors)
            jres['status'] = 'KO'

        else:
            jres['error'] = 'form_invalid no ajax'
            logger.warning('form_invalid no ajax')

        return HttpResponse(json.dumps(jres),content_type='application/json')



# demo-authors


class DemoinfoGetDemoEditorView(NavbarReusableMixinMF,TemplateView):

    template_name = "demoinfo/manage_editors_for_demo.html"


    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DemoinfoGetDemoEditorView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):

        #get context
        context = super(DemoinfoGetDemoEditorView, self).get_context_data(**kwargs)

        try:
            try:
                demo_id = self.kwargs['demo_id']
                demo_id = int(demo_id)
            except Exception as e:
                msg="Error getting param for list_editors_for_demo %s"%e
                print(msg)

            #send context vars for template
            context['demo_id'] = demo_id




            # ChooseEditorForDemoform with dropdown select
            # available_editor_list = get_demoinfo_available_editor_list(demo_id)
            # initial_editor_choicedict={'editor':available_editor_list }
            # context['choosedemoeditorform'] = ChooseEditorForDemoform(initial=initial_editor_choicedict)
            #

            # ChooseAuthorForDemoform with autocomplete
            self.request.session['editors_avilable_for_demo_id']=demo_id
            # context['choosedemoeditorform'] = ChooseEditorForDemoform()
            form = ChooseEditorForDemoform()
            # form.fields['author'].widget.attrs.push("autofocus", True)
            context['choosedemoeditorform'] = form
            context['demoeditorform'] = DemoEditorform
            context['editorform'] = Editorform

        except Exception as e:

            msg=" DemoinfoGetDemoEditorView Error %s "%e
            logger.error(msg)
            context['demo_id'] = None
            context['choosedemoeditorform'] = None
            context['demoeditorform'] = None
            context['editorform'] = None
            logger.error(msg)
            print(msg)


        return context

    # no need for filtering and pagination
    def list_editors_for_demo(self):
        result = None
        try:
            try:
                demo_id = self.kwargs['demo_id']
                demo_id = int(demo_id)
            except Exception as e:
                msg="Error getting param for list_editors_for_demo %s"%e
                print(msg)
                pass

            # print "  list_editors_for_demo demoid: ", demo_id
            page_json = ipolservices.demoinfo_editor_list_for_demo(demo_id)
            result = DeserializeDemoinfoEditorList(page_json)

        except Exception as e:
            msg="Error list_editors_for_demo %s"%e
            logger.error(msg)
            print(msg)

        return result


class DemoinfoAddExistingEditorToDemoView(NavbarReusableMixinMF,FormView):
    ##one save view for all two different forms used in modals? nope, better to have different views for each ajax call

    template_name = ''
    form_class = ChooseEditorForDemoform


    def form_valid(self, form):

        jres = dict()
        jres['status'] = 'KO'


        if self.request.is_ajax():

            # get form fields
            demoid = None
            editorid = None

            try:
                demoid = form.cleaned_data['demoid']
                demoid = int(demoid)
                choicefielddata = form.cleaned_data['editor']

                if type(choicefielddata) is not list:
                    #simple choicefield
                    editorid = choicefielddata
                    print " -editorid", editorid
                else:
                    #simple choicefield
                    editorid_list = choicefielddata
                    print " -editorid_list", editorid_list




            except Exception as e:
                msg = "DemoinfoAddExistingEditorToDemoView form data error: %s" % e
                jres['error'] = msg
                print msg
                logger.error(msg)

            #  send info to be saved in demoinfo module to be saved
            try:

                if type(choicefielddata) is not list:
                    jsonresult = ipolservices.demoinfo_add_editor_to_demo(demoid,editorid)
                    status,error = get_status_and_error_from_json(jsonresult)
                    jres['status'] = status
                    if error is not None:
                        jres['error'] = error
                else:

                    #todo improvement: wds in demoinfo that adds a list of editors to demo
                    for id in editorid_list:

                        print id
                        id =int(id)
                        jsonresult = ipolservices.demoinfo_add_editor_to_demo(demoid,id)
                        status,error = get_status_and_error_from_json(jsonresult)
                        jres['status'] = status
                        if error is not None:
                            jres['error'] = error

            except Exception as e:
                msg = " DemoinfoAddExistingEditorToDemoView error: %s" % e
                jres['error'] = msg
                logger.error(msg)
                print msg


        else:
            jres['error'] = 'form_valid no ajax'
            logger.warning('DemoinfoAddExistingEditorToDemoView form_valid no ajax')


        return HttpResponse(json.dumps(jres),content_type='application/json')


    def form_invalid(self, form):

        jres = dict()
        jres['status'] = 'KO'
        print "invalid form"

        if self.request.is_ajax():

            print " invalid ajax form"
            # print form.errors
            # print form
            #form CON ERORRES, se lo puedo pasar al JS...pero si substituyo el form actual por este..pierdo el submit ajax.
            # form_html = render_crispy_form(form)
            # logger.warning(form_html)

            jres['error'] = str(form.errors)
            jres['status'] = 'KO'

        else:
            jres['error'] = 'form_invalid no ajax'
            logger.warning('form_invalid no ajax')

        return HttpResponse(json.dumps(jres),content_type='application/json')


class DemoinfoAddNewEditorToDemoView(NavbarReusableMixinMF,FormView):
    template_name = ''
    form_class = DemoEditorform


    def form_valid(self, form):

        jres = dict()
        jres['status'] = 'KO'

        print "valid form"


        if self.request.is_ajax():

            # get form fields
            demoid = None
            name = None
            mail = None

            try:
                demoid = form.cleaned_data['demoid']
                demoid = int(demoid)
                name = form.cleaned_data['name']
                mail = form.cleaned_data['mail']
            except Exception as e:
                msg = "DemoinfoAddNewEditorToDemoView form data error: %s" % e
                jres['error'] = msg
                print msg
                logger.error(msg)

            #  send info to be saved in demoinfo module to be saved

            # create editor
            try:

                jsonresult = ipolservices.demoinfo_add_editor(name,mail)
                resultdict = json.loads(jsonresult)
                status = resultdict['status']
                editorid = resultdict['editorid']
                editorid = int(editorid)
                if status != 'OK' or 'error' in resultdict:
                    msg= " DemoinfoAddNewEditorToDemoView Could not create editor "
                    logger.error(msg)
                    raise ValueError(msg+resultdict['error'])


                # add editor to demo
                try:
                    jsonresult = ipolservices.demoinfo_add_editor_to_demo(demoid,editorid)
                    print "jsonresult editor to demo", jsonresult
                    status,error = get_status_and_error_from_json(jsonresult)
                    jres['status'] = status
                    if error is not None:
                        jres['error'] = error
                except Exception as e:
                    msg = " DemoinfoAddNewEditorToDemoView add editor to demo error: %s" % e
                    jres['error'] = msg
                    logger.error(msg)
                    print msg

            except Exception as e:
                msg = " DemoinfoAddNewEditorToDemoView create editor error: %s" % e
                jres['error'] = msg
                logger.error(msg)
                print msg

        else:
            jres['error'] = 'form_valid no ajax'
            logger.warning('DemoinfoAddExistingEditorToDemoView form_valid no ajax')


        return HttpResponse(json.dumps(jres),content_type='application/json')


    def form_invalid(self, form):

        jres = dict()
        jres['status'] = 'KO'
        print "invalid form"

        if self.request.is_ajax():

            print " invalid ajax form"
            # print form.errors
            # print form

            jres['error'] = str(form.errors)
            jres['status'] = 'KO'

        else:
            jres['error'] = 'form_invalid no ajax'
            logger.warning('form_invalid no ajax')

        return HttpResponse(json.dumps(jres),content_type='application/json')


class DemoinfoDeleteEditorFromDemoView(NavbarReusableMixinMF,TemplateView):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DemoinfoDeleteEditorFromDemoView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):

        try:
            editor_id = int(self.kwargs['editor_id'])
            demo_id = int(self.kwargs['demo_id'])
        except ValueError:
            msg= "Id is not an integer"
            logger.error(msg)
            raise ValueError(msg)

        result= ipolservices.demoinfo_delete_editor_from_demo(demo_id,editor_id)
        if result == None:
            msg="DemoinfoDeleteEditorFromDemoView: Something went wrong using demoinfo WS"
            logger.error(msg)
            raise ValueError(msg)

        print result

        return HttpResponse(result, content_type='application/json')


#Demo Extras
class DemoinfoGetDemoExtrasView(NavbarReusableMixinMF,TemplateView):

    template_name = "demoinfo/manage_demo_extras_for_demo.html"


    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DemoinfoGetDemoExtrasView, self).dispatch(*args, **kwargs)

    # no need for filtering and pagination
    def list_demo_extras_for_demo(self):
        result = None
        try:
            try:
                demo_id = self.kwargs['demo_id']
                demo_id = int(demo_id)
            except Exception as e:
                msg="Error getting param for list_demo_extras_for_demo %s"%e
                print(msg)
                pass

            page_json = ipolservices.demoinfo_demo_extras_list_for_demo(demo_id)
            result = DeserializeDemoinfoDemoExtrasList(page_json)

        except Exception as e:
            msg="Error list_demo_extras_for_demo %s"%e
            logger.error(msg)
            print(msg)
        return result

class DemoinfoDeleteDemoExtrasView(NavbarReusableMixinMF,TemplateView):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DemoinfoDeleteDemoExtrasView, self).dispatch(*args, **kwargs)


    def post(self, request, *args, **kwargs):

        try:
            demo_id = int(self.kwargs['demo_id'])
        except ValueError:
            msg= "Id is not an integer"
            logger.error(msg)

        result = ipolservices.demoinfo_delete_demo_extras_from_demo(demo_id)
        if result == None:
            msg = "DemoinfoDeleteDemoExtrasView: Something went wrong using demoinfo WS"
            logger.error(msg)
            raise ValueError(msg)

        print result

        return HttpResponse(result, content_type='application/json')

class DemoinfoAddDemoExtrasView(NavbarReusableMixinMF, TemplateView):

    template_name = "demoinfo/manage_demo_extras_for_demo.html"
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DemoinfoAddDemoExtrasView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):

        url=request.META.get('HTTP_REFERER')
        try:
            demo_id = int(self.kwargs['demo_id'])
            myfile = request.FILES['myfile']
        except ValueError:
            msg = "Id is not an integer"
            logger.error(msg)

        result = ipolservices.demoinfo_add_demo_extra_to_demo(demo_id, request)

        if result == None:
            msg = "DemoinfoDeleteDemoExtrasView: Something went wrong using demoinfo WS"
            logger.error(msg)
            raise ValueError(msg)

        return HttpResponseRedirect(url)
