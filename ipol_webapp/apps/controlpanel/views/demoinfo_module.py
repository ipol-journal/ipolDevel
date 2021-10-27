# from crispy_forms.utils import render_crispy_form
# from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import json
import os
from urllib import unquote
from django.http import HttpResponse, HttpResponseRedirect, Http404
from apps.controlpanel.forms import DDLform, CreateDemoform, UpdateDemoform, Authorform, DemoAuthorform, ChooseAuthorForDemoform, Editorform, \
        DemoEditorform, ChooseEditorForDemoform
from apps.controlpanel.mixings import NavbarReusableMixinMF

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, FormView
from apps.controlpanel.tools import get_status_and_error_from_json, convert_str_to_bool,get_demoinfo_available_author_list, \
        get_demoinfo_available_editor_list, get_demoinfo_module_states
from apps.controlpanel.views.ipolwebservices.ipoldeserializers import DeserializeDemoinfoDemoList, \
        DeserializeDemoinfoAuthorList, DeserializeDemoinfoEditorList
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
def has_permission(demo_id, user):
    try:
        if user.is_staff or user.is_superuser:
            return True

        editors = json.loads(ipolservices.demoinfo_editor_list_for_demo(demo_id))
        for editor in editors.get('editor_list'):
            if editor.get('mail') == user.email:
                return True
        return False

    except Exception:
        print "has_permission failed"
        return False


class DemoinfoDemosView(NavbarReusableMixinMF,TemplateView):
    template_name = "demoinfo/demoinfo_demos_2.html"

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
            context['createdemoform'] = CreateDemoform
            # context['updatedemoform'] = UpdateDemoform
            context['states'] = get_demoinfo_module_states()
            user = self.request.user
            context['admin'] = user.is_staff or user.is_superuser

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


class DemoinfoDemoEditionView(NavbarReusableMixinMF,TemplateView):
    template_name = "demoinfo/demo_edition.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DemoinfoDemoEditionView, self).dispatch(*args, **kwargs)

    def get_demo_details(self, **kwargs):
        data = {}
        try:
            try:
                demo_id = int(self.kwargs['demo_id'])
            except ValueError:
                msg = "Id is not an integer"
                logger.error(msg)
                raise ValueError(msg)

            demo_result = ipolservices.demoinfo_read_demo(demo_id)
            ddl_result = ipolservices.demoinfo_get_ddl(demo_id)
            editors = ipolservices.demoinfo_editor_list_for_demo(demo_id)

            if demo_result == None or ddl_result == None:
                msg = "DemoinfoDemoEditionView: Something went wrong using demoinfo WS"
                logger.error(msg)
                raise ValueError(msg)

            demo_result = json.loads(demo_result)
            ddl_result = json.loads(ddl_result)
            editors = json.loads(editors)
            if demo_result['status'] == 'KO' or ddl_result['status'] == 'KO':
                msg = "DemoinfoDemoEditionView: DDL not retrieved"
                logger.error(msg)
                raise ValueError(msg)
            
            data['registered'] = has_permission(demo_id, self.request.user)
            data['editorsdemoid'] = demo_id
            data['title'] = demo_result['title']
            data['state'] = demo_result['state']
            data['ddl'] = ddl_result['last_demodescription']['ddl']
            data['modification'] = demo_result['modification']
            data['updatedemoform'] = UpdateDemoform
            data['status'] = 'OK'

        except Exception as ex:
            data['editorsdemoid'] = demo_id
            data['demoform'] = None
            data['status'] = 'KO'
            raise Http404

        return data


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

        if has_permission(demo_id, self.request.user):
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


        result= ipolservices.demoinfo_get_ddl(demo_id)
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

                if is_json(ddlJSON):
                    try:
                        if has_permission(demoid, self.request.user):
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


class DemoinfoSaveDemo(NavbarReusableMixinMF,FormView):

    template_name = ''
    form_class = CreateDemoform

    def form_valid(self, form):
        jres = dict()
        jres['status'] = 'KO'
        if self.request.is_ajax():
            id = None
            title = None
            state = None
            demo_id = None
            editorid = None
            try:
                title = form.cleaned_data['title']
                state = form.cleaned_data['state']
                demo_id = form.cleaned_data['editorsdemoid']
                demo_id = int(demo_id)
                user = self.request.user
                editors = json.loads(ipolservices.demoinfo_editor_list())

                for editor in editors.get('editor_list'):
                    if editor.get('mail') == user.email:
                        editorid = editor.get('id')

                if editorid is None:
                    editor_name = user.first_name +" "+user.last_name
                    response = json.loads(ipolservices.demoinfo_add_editor(editor_name,user.email))
                    editorid = response.get('editorid')

                jsonresult= ipolservices.demoinfo_add_demo(demo_id ,title, state, editorid)

                status, error = get_status_and_error_from_json(jsonresult)
                jres['status'] = status
                if error is not None:
                    jres['error'] = error
                    return HttpResponse(json.dumps(jres),content_type='application/json')

                # insert a default (empty) DDL for the new Demo
                try:
                    defaultDDL = '{}'
                    jsonresult = ipolservices.demoinfo_save_demo_description(pjson=defaultDDL, demoid=demo_id)
                    status, error = get_status_and_error_from_json(jsonresult)
                    jres['status'] = status
                    if error is not None:
                        jres['error'] = error
                        return HttpResponse(json.dumps(jres),content_type='application/json')

                except Exception as e:
                    msg = "update ddl error: %s" % e
                    logger.error(msg)
                    print msg

            except Exception as e:
                msg = "DemoinfoSaveDemoView form data error: %s" % e
                jres['error'] = msg
                logger.error(msg)
                print msg
        else:
            jres['error'] = 'form_valid no ajax'
            logger.error('DemoinfoSaveDemoView form_valid no ajax')


        return HttpResponse(json.dumps(jres),content_type='application/json')

class DemoinfoUpdateDemo(NavbarReusableMixinMF, FormView):

    template_name = ''
    form_class = UpdateDemoform

    def form_valid(self, form):

        jres = dict()
        jres['status'] = 'KO'

        if self.request.is_ajax():
            id = None
            title = None
            state = None
            editorsdemoid = None
            editorid = None

            # if form has id field set, I must update, if not, create a new demo
            try:
                old_editor_demoid = int(form.cleaned_data['id'])
            except Exception:
                response = {"status": "KO", "error": "Bad editor's ID={}".format(old_editor_demoid)}
                return HttpResponse(json.dumps(response), content_type='application/json')

            # Check if the user is allowed to edit this demo
            if not has_permission(old_editor_demoid, self.request.user):
                response = {"status": "KO", "error": "Editor '{}' not authorized for demo #{}".format(self.request.user, old_editor_demoid)}
                return HttpResponse(json.dumps(response), content_type='application/json')

            try:
                title = form.cleaned_data['title']
                state = form.cleaned_data['state']
                editorsdemoid = int(form.cleaned_data['editorsdemoid'])
                editorid = form.cleaned_data.get('editor')

                demojson = {
                    "title": title,
                    "editorsdemoid": editorsdemoid,
                    "state": state
                }

                jsonresult = ipolservices.demoinfo_update_demo(demojson, old_editor_demoid)
                status, error = get_status_and_error_from_json(jsonresult)
                jres['status'] = status
                if error is not None:
                    jres['error'] = error
                    return HttpResponse(json.dumps(jres), content_type='application/json')

            except Exception as ex:
                msg = "Update demo error: %s" % ex
                logger.error(msg)
                jres['error'] = msg
                return HttpResponse(json.dumps(jres), content_type='application/json')

        else:
            jres['error'] = 'form_valid no ajax'
            logger.error('DemoinfoUpdateDemo form_valid no ajax')

        return HttpResponse(json.dumps(jres), content_type='application/json')

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
        user = self.request.user
        if not (user.is_staff or user.is_superuser):
            context['status'] = 'KO'
            context['list_authors'] = []
            context['authorform'] = None
            return context
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
        data = {}
        try:
            try:
                demo_id = self.kwargs['demo_id']
                demo_id = int(demo_id)
            except Exception as e:
                msg="Error getting param for list_authors_for_demo %s"%e
                print(msg)
                pass

            # print "  list_authors_for_demo demoid: ", demo_id
            data['registered'] = has_permission(demo_id, self.request.user)
            page_json = json.loads(ipolservices.demoinfo_author_list_for_demo(demo_id))
            data['author_list'] = page_json.get('author_list')
            data['status'] = page_json.get('status')
            # result = DeserializeDemoinfoAuthorList(page_json)

        except Exception as e:
            msg="Error list_authors_for_demo %s"%e
            logger.error(msg)
            print(msg)

        return data


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

        user = self.request.user
        if not (user.is_staff or user.is_superuser):
            context['status'] = 'KO'
            context['list_editors'] = []
            context['editorform'] = None
            return context
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

            editors = ipolservices.demoinfo_editor_list_for_demo(demo_id)
            editors = json.loads(editors)

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
        data = {}
        try:
            try:
                demo_id = self.kwargs['demo_id']
                demo_id = int(demo_id)
            except Exception as e:
                msg="Error getting param for list_editors_for_demo %s"%e
                print(msg)
                pass

            data['registered'] = has_permission(demo_id, self.request.user)
            page_json = json.loads(ipolservices.demoinfo_editor_list_for_demo(demo_id))
            # result = DeserializeDemoinfoEditorList(page_json)
            data['status'] = page_json.get('status')
            data['editor_list'] = page_json.get('editor_list')

        except Exception as e:
            msg="Error list_editors_for_demo %s"%e
            logger.error(msg)
            print(msg)

        return data


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
                    if has_permission(demoid, self.request.user):
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
                if has_permission(demoid, self.request.user):
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
        if has_permission(demo_id, self.request.user):
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
        data = {}
        result = None
        try:
            try:
                demo_id = self.kwargs['demo_id']
                demo_id = int(demo_id)
            except Exception as e:
                msg="Error getting param for list_demo_extras_for_demo %s"%e
                print(msg)
                pass

            json_result = json.loads(ipolservices.demoinfo_demo_extras_for_demo(demo_id))
            
            data['registered'] = has_permission(demo_id, self.request.user)
            if json_result.get('url') is not None:
                data['url'] = json_result.get('url')
                data['name'] = unquote(os.path.basename(json_result.get('url')))
            data['status'] = json_result.get('status')

        except Exception as e:
            msg="Error list_demo_extras_for_demo %s"%e
            logger.error(msg)
            print(msg)
        return data

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
        if has_permission(demo_id, self.request.user):
            result = ipolservices.demoinfo_delete_demo_extras_from_demo(demo_id)
        if result == None:
            msg = "DemoinfoDeleteDemoExtrasView: Something went wrong using demoinfo WS"
            logger.error(msg)
            raise ValueError(msg)

        return HttpResponse(result, content_type='application/json')

class DemoinfoAddDemoExtrasView(NavbarReusableMixinMF, TemplateView):

    template_name = "demoinfo/manage_demo_extras_for_demo.html"
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DemoinfoAddDemoExtrasView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):

        url = request.META.get('HTTP_REFERER').split('?')[0]
        error_parameter=''
        try:
            demo_id = int(self.kwargs['demo_id'])
            myfile = request.FILES['myfile']
        except ValueError:
            msg = "Id is not an integer"
            logger.error(msg)
        if has_permission(demo_id, self.request.user):
            result = ipolservices.demoinfo_add_demo_extra_to_demo(demo_id, request)
            response = json.loads(result)
            if (response['status'] != 'OK'):
                error_parameter = '?msg=' + response['error_message']
        if result == None:
            msg = "DemoinfoDeleteDemoExtrasView: Something went wrong using demoinfo WS"
            logger.error(msg)
            raise ValueError(msg)
        
        return HttpResponseRedirect(url+error_parameter)

class DemoinfoDDLHistoryView(NavbarReusableMixinMF, TemplateView):
    template_name = "demoinfo/manage_history_ddl_for_demo.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DemoinfoDDLHistoryView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        # get context
        context = super(DemoinfoDDLHistoryView, self).get_context_data(**kwargs)
        try:
            demo_id = int(self.kwargs['demo_id'])
            page_json = ipolservices.get_ddl_history(int(demo_id))
            response = json.loads(page_json)

            context['status'] = response['status']
            if response['status'] != 'OK':
                context['error'] = response['error']
                return context
            history = []
            for ddl in response['ddl_history'][::-1]:
                history.append({'creation':ddl.get('creation'),'ddl':json.dumps(ddl.get('ddl'))})
            context['status'] = response['status']
            context['demo_id'] = demo_id
            context['ddl_history'] = history
        except Exception as e:
            print "DemoinfoDDLHistoryView. Error:", e
            logger.error(e)

        return context

class RestoreDDL(NavbarReusableMixinMF,TemplateView):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(RestoreDDL, self).dispatch(*args, **kwargs)


    def post(self, request, *args, **kwargs):
        try:
            response = self.request.POST
            dict_response = dict(response.iterlists())
            ddl = dict_response['ddl'][0]
            demo_id = dict_response['demo_id'][0]
            ipolservices.demoinfo_save_demo_description(ddl, demo_id)
        except Exception as ex:
            msg = "RestoreDDL. Error %s " % ex
            logger.error(msg)
            print(msg)

        return HttpResponseRedirect('')
