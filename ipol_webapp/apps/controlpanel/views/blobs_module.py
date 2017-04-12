import json
from urlparse import urlparse
from django.http import HttpResponse, HttpResponseRedirect
from apps.controlpanel.mixings import NavbarReusableMixinMF

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.utils.six import BytesIO
import collections

from apps.controlpanel.views.ipolwebservices.ipoldeserializers import DeserializeArchiveDemoList, DeserializePage, \
        DeserializeDemoList, DeserializeDemoinfoDemoList
from apps.controlpanel.views.ipolwebservices import ipolservices

import logging
from rest_framework.parsers import JSONParser

logger = logging.getLogger(__name__)


class EditBlobFromDemoView(NavbarReusableMixinMF, TemplateView):
    template_name = "blobs/edit_blob_from_demo.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(EditBlobFromDemoView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        # get context
        context = super(EditBlobFromDemoView, self).get_context_data(**kwargs)

        try:
            demo = self.request.GET.get('demo')
            set = self.request.GET.get('set')
            pos = self.request.GET.get('pos')
            context['status'] = 'OK'
            context['demo'] = demo
            context['set'] = set
            context['pos'] = pos

            page_json = ipolservices.get_demo_owned_blobs(int(demo))
            response = json.loads(page_json)

            context['status'] = response['status']
            for blob in response['sets']:

                if blob['name'] == set:
                    context['blob'] = blob['blobs'][pos]
                    break


        except Exception as e:
            print "EditBlobFromDemoView. Error:",e
            logger.error(e)

        return context

class AddBlobDemoView(NavbarReusableMixinMF, TemplateView):
    template_name = "blobs/add_blob_demo.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(AddBlobDemoView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(AddBlobDemoView, self).get_context_data(**kwargs)
        return context


class ManageBlobsForDemoView(NavbarReusableMixinMF, TemplateView):
    template_name = "demoinfo/manage_blobs_for_demo.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ManageBlobsForDemoView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):

        # get context
        context = super(ManageBlobsForDemoView, self).get_context_data(**kwargs)
        demo_id = self.kwargs['id']

        try:
            query = self.request.GET.get('q')
            context['q'] = query

            page_json = ipolservices.get_demo_owned_blobs(int(demo_id))

            response_sets = json.loads(page_json, object_pairs_hook=collections.OrderedDict)

            page_json = ipolservices.get_demo_templates(int(demo_id))
            response_templates = json.loads(page_json)
            used_templates = response_templates['templates']

            page_json = ipolservices.get_all_templates()
            response_all_templates = json.loads(page_json)
            all_templates = response_all_templates['templates']
            unused_templates = []

            for template in all_templates:
                if template not in used_templates:
                    unused_templates.append(template)

            context['status'] = response_sets['status']
            context['sets'] = response_sets['sets']
            context['templates'] = used_templates
            context['unused_templates'] = unused_templates

        except Exception as e:
            msg = "ManageBlobsForDemoView. Error %s "%e
            logger.error(msg)
            context['parsed_data'] = []
            logger.error(msg)
            print(msg)

        return context

class DemoBlobSaveInfo(NavbarReusableMixinMF, TemplateView):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DemoBlobSaveInfo, self).dispatch(*args, **kwargs)


    def post(self, request, *args, **kwargs):
        try:
            response = self.request.POST
            dict_response = dict(response.iterlists())

            id = dict_response['demo'][0]
            tags = dict_response['tags'][0]
            set = dict_response['set'][0]
            new_set = dict_response['new_set'][0]

            if new_set == "":
                new_set = set

            pos = dict_response['pos'][0]
            new_pos = dict_response['new_pos'][0]
            title = dict_response['title'][0]
            credit = dict_response['credit'][0]
            ipolservices.edit_blob_from_demo(request,id,tags,set,new_set,pos,new_pos,title,credit)
        except Exception as ex:
            msg = "DemoBlobSaveInfo. Error %s " % ex
            logger.error(msg)
            print(msg)

        return HttpResponseRedirect('/cp/blob_demo?demo='+id+'&set='+new_set+'&pos='+new_pos)

class RemoveBlobFromDemo(NavbarReusableMixinMF,TemplateView):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(RemoveBlobFromDemo, self).dispatch(*args, **kwargs)


    def post(self, request, *args, **kwargs):
        try:
            response = self.request.POST
            dict_response = dict(response.iterlists())
            ipolservices.remove_blob_from_demo(dict_response['demo_id'], dict_response['set'], dict_response['pos'])
        except Exception as ex:
            msg = "RemoveBlobFromDemo. Error %s " % ex
            logger.error(msg)
            print(msg)

        return HttpResponseRedirect('')

class RemoveTemplateFromDemo(NavbarReusableMixinMF, TemplateView):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(RemoveTemplateFromDemo, self).dispatch(*args, **kwargs)


    def post(self, request, *args, **kwargs):
        try:
            response = self.request.POST
            dict_response = dict(response.iterlists())
            ipolservices.remove_template_from_demo(dict_response['demo_id'], dict_response['template'])
        except Exception as ex:
            msg = "RemoveTemplateFromDemo. Error %s " % ex
            logger.error(msg)
            print(msg)

        return HttpResponseRedirect('')

class AddTemplateToDemo(NavbarReusableMixinMF,TemplateView):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(AddTemplateToDemo, self).dispatch(*args, **kwargs)


    def post(self, request, *args, **kwargs):
        try:
            response = self.request.POST
            dict_response = dict(response.iterlists())
            ipolservices.add_template_to_demo(dict_response['demo_id'], dict_response['template'])
        except Exception as ex:
            msg = "AddTemplateToDemo. Error %s " % ex
            logger.error(msg)
            print(msg)

        return HttpResponseRedirect('')

class AddBlobToDemo(NavbarReusableMixinMF,TemplateView):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(AddBlobToDemo, self).dispatch(*args, **kwargs)


    def post(self, request, *args, **kwargs):
        try:
            response = self.request.POST
            dict_response = dict(response.iterlists())
            id = dict_response['demo'][0]
            tags = dict_response['tags'][0]
            set = dict_response['set'][0]
            pos = dict_response['pos'][0]
            title = dict_response['title'][0]
            credit = dict_response['credit'][0]
            ipolservices.add_blob_to_demo(request, id, tags, set, pos, title, credit)
        except Exception as ex:
            msg = "AddBlobToDemo. Error %s " % ex
            logger.error(msg)
            print(msg)

        return HttpResponseRedirect('/cp/blob_demo/'+id)

class RemoveVRFromDemo(NavbarReusableMixinMF,TemplateView):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(RemoveVRFromDemo, self).dispatch(*args, **kwargs)


    def post(self, request, *args, **kwargs):
        try:
            response = self.request.POST
            dict_response = dict(response.iterlists())
            demo_id = dict_response['demo_id'][0]
            set = dict_response['set'][0]
            pos = dict_response['pos'][0]
            ipolservices.remove_vr_from_demo(demo_id, set, pos)
        except Exception as ex:
            msg = "RemoveVRFromDemo. Error %s " % ex
            logger.error(msg)
            print(msg)

        return HttpResponseRedirect("")


# Templates
class TemplatePageView(NavbarReusableMixinMF, TemplateView):
    template_name = "blobs/manage_blobs_for_template.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(TemplatePageView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        self.request.session['menu'] = 'menu-templates'
        context = super(TemplatePageView, self).get_context_data(**kwargs)
        name = self.kwargs['name']


        try:

            page_json = ipolservices.get_template_blobs(name)
            response_sets = json.loads(page_json, object_pairs_hook=collections.OrderedDict)
            context['status'] = response_sets['status']
            context['sets'] = response_sets['sets']

        except Exception as e:
            msg = "TemplatePageView. Error %s "%e
            logger.error(msg)
            print(msg)

        return context

class AddBlobTemplateView(NavbarReusableMixinMF, TemplateView):
    template_name = "blobs/add_blob_template.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(AddBlobTemplateView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(AddBlobTemplateView, self).get_context_data(**kwargs)
        return context

class AddBlobToTemplate(NavbarReusableMixinMF,TemplateView):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(AddBlobToTemplate, self).dispatch(*args, **kwargs)


    def post(self, request, *args, **kwargs):
        try:
            response = self.request.POST
            dict_response = dict(response.iterlists())
            name = dict_response['name'][0]
            tags = dict_response['tags'][0]
            set = dict_response['set'][0]
            pos = dict_response['pos'][0]
            title = dict_response['title'][0]
            credit = dict_response['credit'][0]
            ipolservices.add_blob_to_template(request, name, tags, set, pos, title, credit)
        except Exception as ex:
            msg = "AddBlobToTemplate Error %s " % ex
            logger.error(msg)
            print(msg)

        return HttpResponseRedirect('/cp/blob_template/'+name)


class EditBlobFromTemplate(NavbarReusableMixinMF, TemplateView):
    template_name = "blobs/edit_blob_from_template.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(EditBlobFromTemplate, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        # get context
        context = super(EditBlobFromTemplate, self).get_context_data(**kwargs)

        try:
            name = self.request.GET.get('name')
            set = self.request.GET.get('set')
            pos = self.request.GET.get('pos')
            context['status'] = 'OK'
            context['name'] = name
            context['set'] = set
            context['pos'] = pos

            page_json = ipolservices.get_template_blobs(name)
            response = json.loads(page_json)

            context['status'] = response['status']
            for blob in response['sets']:
                if blob['name'] == set:
                    context['blob'] = blob['blobs'][pos]
                    break


        except Exception as e:
            print "error:",e
            context['status'] = 'KO'
            msg = "EditBlobFromTemplate error: %s" % e
            logger.error(msg)

        return context

class RemoveVRFromTemplate(NavbarReusableMixinMF,TemplateView):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(RemoveVRFromTemplate, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            response = self.request.POST
            dict_response = dict(response.iterlists())
            name = dict_response['name'][0]
            set = dict_response['set'][0]
            pos = dict_response['pos'][0]
            ipolservices.remove_vr_from_template(name, set, pos)
        except Exception as ex:
            msg = "RemoveVRFromTemplate Error %s " % ex
            logger.error(msg)
            print(msg)

        return HttpResponseRedirect("")

class SaveBlobInfoFromTemplate(NavbarReusableMixinMF,TemplateView):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(SaveBlobInfoFromTemplate, self).dispatch(*args, **kwargs)


    def post(self, request, *args, **kwargs):
        try:
            response = self.request.POST
            dict_response = dict(response.iterlists())

            name = dict_response['name'][0]
            tags = dict_response['tags'][0]
            set = dict_response['set'][0]
            new_set = dict_response['new_set'][0]

            if new_set == "":
                new_set = set

            pos = dict_response['pos'][0]
            new_pos = dict_response['new_pos'][0]
            title = dict_response['title'][0]
            credit = dict_response['credit'][0]
            ipolservices.edit_blob_from_template(request,name,tags,set,new_set,pos,new_pos,title,credit)
        except Exception as ex:
            msg = "SaveBlobInfoFromTemplate Error %s " % ex
            logger.error(msg)
            print(msg)

        return HttpResponseRedirect('/cp/blob_template?name='+name+'&set='+new_set+'&pos='+new_pos)

class RemoveBlobFromTemplate(NavbarReusableMixinMF,TemplateView):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(RemoveBlobFromTemplate, self).dispatch(*args, **kwargs)


    def post(self, request, *args, **kwargs):
        try:
            response = self.request.POST
            dict_response = dict(response.iterlists())
            ipolservices.remove_blob_from_template(dict_response['name'][0], dict_response['set'][0], dict_response['pos'][0])
        except Exception as ex:
            msg = "RemoveBlobFromTemplate Error %s " % ex
            logger.error(msg)
            print(msg)

        return HttpResponseRedirect('')


class TemplateListView(NavbarReusableMixinMF, TemplateView):
    template_name = "blobs/templates.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(TemplateListView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        # get context
        context = super(TemplateListView, self).get_context_data(**kwargs)

        try:

            page_json = ipolservices.get_all_templates()
            response = json.loads(page_json)

            context['status'] = response['status']
            context['templates'] = response['templates']
            self.request.session['menu'] = 'menu-templates'

        except Exception as e:
            print "TemplateListView Error:",e
            logger.error(e)

        return context

class DeleteTemplate(NavbarReusableMixinMF,TemplateView):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DeleteTemplate, self).dispatch(*args, **kwargs)


    def post(self, request, *args, **kwargs):
        try:
            response = self.request.POST
            dict_response = dict(response.iterlists())
            ipolservices.delete_template(dict_response['name'][0])
        except Exception as ex:
            msg = "DeleteTemplate Error %s " % ex
            logger.error(msg)
            print(msg)

class CreateTemplate(NavbarReusableMixinMF,TemplateView):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(CreateTemplate, self).dispatch(*args, **kwargs)


    def post(self, request, *args, **kwargs):
        try:
            response = self.request.POST
            dict_response = dict(response.iterlists())
            ipolservices.create_template(dict_response['name'][0])
        except Exception as ex:
            msg = "CreateTemplate Error %s " % ex
            logger.error(msg)
            print(msg)