import json
from apps.controlpanel.mixings import NavbarReusableMixinMF

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.utils.six import BytesIO
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render

from django.contrib.auth.models import User

from apps.controlpanel.views.ipolwebservices.ipoldeserializers import DeserializeArchiveDemoList, DeserializePage, \
        DeserializeDemoList, DeserializeDemoinfoDemoList
from apps.controlpanel.views.ipolwebservices import ipolservices

import logging
from rest_framework.parsers import JSONParser

logger = logging.getLogger(__name__)

__author__ = 'josearrecio'

# pagination settings for archive
PAGINATION_ITEMS_PER_PAGE_ARCHIVE_LIST = 4

#todo remove, this is used in terminal app
class ArchiveShutdownView(NavbarReusableMixinMF,TemplateView):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ArchiveShutdownView, self).dispatch(*args, **kwargs)

    def render_to_response(self, context, **response_kwargs):
        #just return the JSON from the ws, this json has no interesting data, no template is needed
        result= ipolservices.archive_shutdown()
        if result is None:
            msg="ArchiveShutdownView: Something went wrong using archive shutdown WS"
            logger.error(msg)
            raise ValueError(msg)


        return HttpResponse(result, content_type='application/json')


class ArchiveDemosView(NavbarReusableMixinMF,TemplateView):
    template_name = "archive/archive.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        self.request.session['menu'] = 'menu-archive'
        return super(ArchiveDemosView, self).dispatch(*args, **kwargs)


    def list_demos(self):
        result = None
        result2 = None
        #for special demo with id= -1 for testing in archive
        archivetestdemo=False
        try:
            #get demos from archive module
            page_json = ipolservices.archive_demo_list()
            result = DeserializeArchiveDemoList(page_json)

            #get demo info for those demos from demoinfo module
            if result:
                idlist=list()

                for d in result.demo_list:
                    demoid= d.demo_id
                    #special case demo -1 in archive, this Id will not exist in demoinfo module
                    if demoid > 0 and isinstance( demoid, ( int, long ) ):
                        idlist.append(demoid)
                    else:
                        archivetestdemo = True
                result2json = ipolservices.demoinfo_demo_list_by_demoeditorid(idlist)
                if result2json:
                    result2 = DeserializeDemoinfoDemoList(result2json)
                else:
                    # I expect a dict for template
                    result2 = {"status": "KO","error": "No demos in archive"}


            # print "result2",result2


        except Exception as e:
            msg="Error %s"%e
            logger.error(msg)
            print(msg)

        return result2,archivetestdemo


class ArchiveDeleteExperimentView(NavbarReusableMixinMF,TemplateView):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ArchiveDeleteExperimentView, self).dispatch(*args, **kwargs)

    def render_to_response(self, context, **response_kwargs):
        #just return the JSON from the ws, this json has no interesting data, no template is needed

        try:
            experiment_id = int(self.kwargs['experiment_id'])
        except ValueError:
            msg= "Id is not an integer"
            logger.error(msg)
            raise ValueError(msg)

        result= ipolservices.archive_delete_experiment(experiment_id)
        if result is None:
            msg="DeleteExperimentView: Something went wrong using archive WS"
            logger.error(msg)
            raise ValueError(msg)


        return HttpResponse(result, content_type='application/json')


class ArchiveDeleteDemoView(NavbarReusableMixinMF,TemplateView):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ArchiveDeleteDemoView, self).dispatch(*args, **kwargs)

    def render_to_response(self, context, **response_kwargs):
        #just return the JSON from the ws, no template is needed

        try:
            demo_id = int(self.kwargs['demo_id'])
        except ValueError:
            msg= "Id is not an integer"
            logger.error(msg)
            raise ValueError(msg)

        result= ipolservices.archive_delete_demo(demo_id)
        if result is None:
            msg="ArchiveDeleteDemoView: Something went wrong using archive WS"
            logger.error(msg)
            raise ValueError(msg)


        return HttpResponse(result, content_type='application/json')


class ArchiveDeleteExperimentFileView(NavbarReusableMixinMF,TemplateView):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ArchiveDeleteExperimentFileView, self).dispatch(*args, **kwargs)

    def render_to_response(self, context, **response_kwargs):
        #just return the JSON from the ws, no template is needed

        try:
            demo_id = int(self.kwargs['file_id'])
        except ValueError:
            msg= "Id is not an integer"
            logger.error(msg)
            raise ValueError(msg)

        result= ipolservices.archive_delete_file(demo_id)
        if result is None:
            msg="DeleteFileView: Something went wrong using archive WS"
            logger.error(msg)
            raise ValueError(msg)


        return HttpResponse(result, content_type='application/json')


class ArchiveAddExpToTestDemoView(NavbarReusableMixinMF,TemplateView):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ArchiveAddExpToTestDemoView, self).dispatch(*args, **kwargs)

    def render_to_response(self, context, **response_kwargs):
        #just return the JSON from the ws, no template is needed

        result= ipolservices.archive_add_experiment_to_test_demo()
        if result is None:
            msg="AddExpToTestDemoView: Something went wrong using archive WS"
            logger.error(msg)
            raise ValueError(msg)

        return HttpResponse(result, content_type='application/json')


class ArchivePageView(NavbarReusableMixinMF,TemplateView):
    # template_name = "archive/demo_result_page.html"
    template_name = "demoinfo/manage_archives_for_demo.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ArchivePageView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):

        # get context
        context = super(ArchivePageView, self).get_context_data(**kwargs)
        demo_id = self.kwargs['id']

        try:
            query = self.request.GET.get('q')
            context['q'] = query

            try:
                page = self.request.GET.get('page')
                page = int(page)
            except :
                # If page is not an integer, deliver first page.
                page = 1

            print "-------------------------------------------"
            '''
            print "%%%% demo_id %%%%"
            print demo_id
            print "%%%% query %%%%"
            print query
            print "%%%% page %%%%"
            print page
            '''
            page_json = ipolservices.archive_get_page(int(demo_id), page)

            try:
                # Parse a stream into Python native datatypes...
                # Avoids the use of deserializer
                stream = BytesIO(page_json)
                parsed_data = JSONParser().parse(stream)
                context['parsed_data'] = parsed_data
            except Exception as e:
                msg = "Error on JSON parsing: %s" %e
                logger.error(msg)

            # pagination of result
            '''
            if hasattr(parsed_data.meta, 'previous_page_number'):
                context['previous_page_number'] = parsed_data.previous_page_number
                context['has_previous'] = True
            else:
                context['has_previous'] = False
            '''
            #if page:
            context['number'] = page

            # if hasattr(parsed_data, 'number_of_pages'):
            if 'number_of_pages' in parsed_data['meta']:
                context['num_pages'] = parsed_data['meta']['number_of_pages']
                pages = context['num_pages']

            #has_previous = False
            #has_next = False
            previous_page = -1
            next_page = -1

            # 0 or 1 pages
            if pages <= 1:
                #has_previous = False
                #has_next = False
                previous_page = -1
                next_page = -1

            # more than 1 pages
            else:
                # the page is the first one
                if page == 1:
                    # has_previous = False
                    # has_next = True
                    previous_page = -1
                    next_page = page + 1

                # the page is the last one
                elif page == pages:
                    #has_previous = True
                    #has_next = False
                    previous_page = page - 1
                    next_page = -1

                # the page is between the first and the last one
                else:
                    #has_previous = True
                    #has_next = True
                    previous_page = page - 1
                    next_page = page + 1

            #context['has_next'] = has_next
            #context['has_previous'] = has_previous
            context['next_page_number'] = next_page
            context['previous_page_number'] = previous_page

            '''
            if hasattr(parsed_data, 'next_page_number'):
                context['next_page_number'] = parsed_data.next_page_number
                context['has_next'] = True
            else:
                context['has_next'] = False
            '''
            # print "has_previous"
            # print context['has_previous']

            print "page = %d" % page
            print "pages = %d" % context['num_pages']

            print "prev = %d" % previous_page
            print "next = %d" % next_page

            #print "has_next"
            #print context['has_next']

            # for exp in parsed_data['experiments']:
            #    print "X"

            # send context vars for template

        except Exception as e:
            msg= "ArchivePageView Error %s "%e
            logger.error(msg)
            context['status'] = 'KO'
            context['parsed_data'] = []
            #context['ddlform'] = None
            #context['demoform'] = None
            context['states'] = None
            logger.error(msg)
            print(msg)

        return context

    def listing(request):
        contact_list = User.objects.all()
        paginator = Paginator(contact_list, 25) # Show 25 contacts per page

        page = request.GET.get('page')
        try:
            contacts = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            contacts = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            contacts = paginator.page(paginator.num_pages)

        return render(request, 'list.html', {'contacts': contacts})



'''
#FUNCIONANDO

class ArchivePageView(NavbarReusableMixinMF,TemplateView):
    #template_name = "archive/demo_result_page.html"
    template_name = "demoinfo/manage_archives_for_demo.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ArchivePageView, self).dispatch(*args, **kwargs)

    #http://reinout.vanrees.org/weblog/2014/05/19/context.html
    def result(self):
        demo_id = self.kwargs['id']

        try:
            query = self.kwargs['q']
        except Exception as e:
            query = 'default search'
        print "$$$$$$$ search $$$$$$$$"
        print query


        # optional param for pagination
        pagenum=None
        try:
            pagenum = self.kwargs['pagenum']
        except Exception as e:
            pagenum = 1

        #todo validate id, MUST BE AN INT?
        #print(id)

        try:
            page_json = ipolservices.archive_get_page(int(demo_id),pagenum)

            try:
                # Parse a stream into Python native datatypes...
                # Avoids the use of deserializer
                stream = BytesIO(page_json)
                parsed_data = JSONParser().parse(stream)

            except Exception as e:
                msg = "Error on JSON parsing: %s" %e
                logger.error(msg)

        except Exception as e:
            msg="ArchivePageView Error %s"%e
            logger.error(msg)
            print msg

        return parsed_data

'''