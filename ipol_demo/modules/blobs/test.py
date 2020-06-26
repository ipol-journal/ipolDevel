#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blobs tests
"""
import os
# Unit tests for the Blobs module
import socket
import sys
import unittest

import requests


class BlobsTests(unittest.TestCase):
    """
    BlobsTests
    """
    HOST = socket.getfqdn()
    module = 'blobs'

    # Blob info
    blob_path = ''
    blob_set = 'TestSet'
    pos_in_set = 0
    title = 'Test Image'
    credit = 'Credit Test'

    # Demo
    demo_id = -1

    # Template
    template_name = 'Test Template'

    #####################
    #       Tests       #
    #####################
    def setUp(self):
        """
        Clean the DB from the tests
        """
        self.delete_demo(self.demo_id)
        self.delete_template(self.template_name)

    def test_ping(self):
        """
        Test ping
        """
        status = None
        try:
            response = self.post(self.module, 'ping')
            json_response = response.json()
            status = json_response.get('status')
        finally:
            self.assertEqual(status, 'OK')

    def test_add_blob_to_demo_without_visual_representation(self):
        """
        Test add blob to demo without visual representation
        """
        add_blob_status = None
        get_blob_status = None
        blob_title = None
        blob_url = None
        blob_vr = None
        delete_demo_status = None
        try:
            with open(self.blob_path, 'rb') as blob:
                json_response = self.add_blob_to_demo(blob=blob, demo_id=self.demo_id, blob_set=self.blob_set,
                                                      pos_set=self.pos_in_set, title=self.title)
            add_blob_status = json_response.get('status')

            json_response = self.get_blobs(self.demo_id)
            get_blob_status = json_response.get('status')
            try:
                blob_list = json_response.get('sets')[0].get('blobs').get(str(self.pos_in_set))
                blob_title = blob_list.get('title')
                blob_url = blob_list.get('blob')
                blob_vr = blob_list.get('vr')
            except Exception:
                pass

            json_response = self.delete_demo(self.demo_id)
            delete_demo_status = json_response.get('status')

        finally:
            self.assertEqual(add_blob_status, 'OK')
            self.assertEqual(get_blob_status, 'OK')
            self.assertEqual(blob_title, self.title)
            self.assertTrue(blob_url is not None)
            self.assertTrue(blob_vr is None)
            self.assertEqual(delete_demo_status, 'OK')

    def test_add_blob_to_demo_with_visual_representation(self):
        """
        Test add blob to demo with visual representation
        """
        add_blob_status = None
        get_blob_status = None
        blob_title = None
        blob_url = None
        blob_vr = None
        delete_demo_status = None
        try:
            with open(self.blob_path, 'rb') as blob, open(self.blob_path, 'rb') as vr:
                json_response = self.add_blob_to_demo(blob=blob, demo_id=self.demo_id, blob_set=self.blob_set,
                                                      pos_set=self.pos_in_set, title=self.title, blob_vr=vr)
            add_blob_status = json_response.get('status')

            json_response = self.get_blobs(self.demo_id)
            get_blob_status = json_response.get('status')
            try:
                blob_list = json_response.get('sets')[0].get('blobs').get(str(self.pos_in_set))
                blob_title = blob_list.get('title')
                blob_url = blob_list.get('blob')
                blob_vr = blob_list.get('vr')
            except Exception:
                pass

            json_response = self.delete_demo(self.demo_id)
            delete_demo_status = json_response.get('status')

        finally:
            self.assertEqual(add_blob_status, 'OK')
            self.assertEqual(get_blob_status, 'OK')
            self.assertEqual(blob_title, self.title)
            self.assertTrue(blob_url is not None)
            self.assertTrue(blob_vr is not None)
            self.assertEqual(delete_demo_status, 'OK')

    def test_create_template(self):
        """
        Test create template
        """
        create_status = None
        delete_status = None
        try:

            response = self.create_template(self.template_name)
            create_status = response.get('status')

            response = self.delete_template(self.template_name)
            delete_status = response.get('status')

        finally:
            self.assertEqual(create_status, 'OK')
            self.assertEqual(delete_status, 'OK')

    def test_add_blob_to_template_without_visual_representation(self):
        """
        Test add blob to template without visual representation
        """
        add_blob_status = None
        get_blob_status = None
        blob_title = None
        blob_url = None
        blob_vr = None
        delete_template_status = None
        try:
            self.create_template(self.template_name)

            with open(self.blob_path, 'rb') as blob:
                json_response = self.add_blob_to_template(blob=blob, template_name=self.template_name, blob_set=self.blob_set,
                                                          pos_set=self.pos_in_set, title=self.title)
            add_blob_status = json_response.get('status')

            json_response = self.get_template_blobs(self.template_name)
            get_blob_status = json_response.get('status')
            try:
                blob_list = json_response.get('sets')[0].get('blobs').get(str(self.pos_in_set))
                blob_title = blob_list.get('title')
                blob_url = blob_list.get('blob')
                blob_vr = blob_list.get('vr')
            except Exception:
                pass

            response = self.delete_template(self.template_name)
            delete_template_status = response.get('status')

        finally:
            self.assertEqual(add_blob_status, 'OK')
            self.assertEqual(get_blob_status, 'OK')
            self.assertEqual(blob_title, self.title)
            self.assertTrue(blob_url is not None)
            self.assertTrue(blob_vr is None)
            self.assertEqual(delete_template_status, 'OK')

    def test_add_blob_to_template_with_visual_representation(self):
        """
        Test add blob to template with visual representation
        """
        add_blob_status = None
        get_blob_status = None
        blob_title = None
        blob_url = None
        blob_vr = None
        delete_template_status = None
        try:
            self.create_template(self.template_name)

            with open(self.blob_path, 'rb') as blob, open(self.blob_path, 'rb') as vr:
                json_response = self.add_blob_to_template(blob=blob, template_name=self.template_name, blob_set=self.blob_set,
                                                          pos_set=self.pos_in_set, title=self.title, blob_vr=vr)
            add_blob_status = json_response.get('status')

            json_response = self.get_template_blobs(self.template_name)
            get_blob_status = json_response.get('status')
            try:
                blob_list = json_response.get('sets')[0].get('blobs').get(str(self.pos_in_set))
                blob_title = blob_list.get('title')
                blob_url = blob_list.get('blob')
                blob_vr = blob_list.get('vr')
            except Exception:
                pass

            response = self.delete_template(self.template_name)
            delete_template_status = response.get('status')

        finally:
            self.assertEqual(add_blob_status, 'OK')
            self.assertEqual(get_blob_status, 'OK')
            self.assertEqual(blob_title, self.title)
            self.assertTrue(blob_url is not None)
            self.assertTrue(blob_vr is not None)
            self.assertEqual(delete_template_status, 'OK')

    def test_add_blob_to_non_existent_template(self):
        """
        Test add blob to non existent template
        """
        status = None
        try:

            with open(self.blob_path, 'rb') as blob:
                json_response = self.add_blob_to_template(blob=blob, template_name=self.template_name, blob_set=self.blob_set,
                                                          pos_set=self.pos_in_set, title=self.title)
            status = json_response.get('status')

        finally:
            self.assertEqual(status, 'KO')

    def test_remove_blob_from_demo(self):
        """
        Test remove blob from demo
        """
        status = None
        set_list = None
        try:
            with open(self.blob_path, 'rb') as blob:
                self.add_blob_to_demo(blob=blob, demo_id=self.demo_id, blob_set=self.blob_set,
                                      pos_set=self.pos_in_set, title=self.title)

            response = self.remove_blob_from_demo(self.demo_id, self.blob_set, self.pos_in_set)
            status = response.get('status')

            json_response = self.get_blobs(self.demo_id)
            set_list = json_response.get('sets')
            self.delete_demo(self.demo_id)

        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(len(set_list), 0)

    def test_remove_blob_from_template(self):
        """
        Test remove blob from template
        """
        status = None
        set_list = None
        try:
            self.create_template(self.template_name)

            with open(self.blob_path, 'rb') as blob:
                self.add_blob_to_template(blob=blob, template_name=self.template_name, blob_set=self.blob_set,
                                          pos_set=self.pos_in_set, title=self.title)

            response = self.remove_blob_from_template(self.template_name, self.blob_set, self.pos_in_set)
            status = response.get('status')

            json_response = self.get_template_blobs(self.template_name)
            set_list = json_response.get('sets')

            self.delete_template(self.template_name)

        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(len(set_list), 0)

    def test_remove_non_existent_blob_from_demo(self):
        """
        Test remove non existent blob from demo
        """
        status = None
        try:

            response = self.remove_blob_from_demo(self.demo_id, self.blob_set, self.pos_in_set)
            status = response.get('status')

        finally:
            self.assertEqual(status, 'KO')

    def test_remove_non_existent_blob_from_template(self):
        """
        Test remove non existent blob from template
        """
        status = None
        try:

            response = self.remove_blob_from_template(self.template_name, self.blob_set, self.pos_in_set)
            status = response.get('status')

        finally:
            self.assertEqual(status, 'KO')

    def test_get_blob_from_non_existent_demo(self):
        """
        Test get blob from non existent demo
        """
        status = None
        try:

            response = self.get_blobs(self.demo_id)
            status = response.get('status')

        finally:
            # This should be OK because the demo can exist in the demoinfo DB
            self.assertEqual(status, 'OK')

    def test_get_blob_from_non_existent_template(self):
        """
        Test get blob from non existent template
        """
        status = None
        try:

            response = self.get_template_blobs(self.template_name)
            status = response.get('status')

        finally:
            self.assertEqual(status, 'KO')

    def test_add_template_to_demo(self):
        """
        Test add template to demo
        """
        status = None
        template_list = None
        template = None
        try:
            with open(self.blob_path, 'rb') as blob:
                self.add_blob_to_demo(blob=blob, demo_id=self.demo_id, blob_set=self.blob_set,
                                      pos_set=self.pos_in_set, title=self.title)

            self.create_template(self.template_name)

            self.add_templates_to_demo(self.demo_id, self.template_name)

            response = self.get_demo_templates(self.demo_id)
            status = response.get('status')
            template_list = response.get('templates')
            template = template_list[0]

            self.delete_demo(self.demo_id)
            self.delete_template(self.template_name)

        finally:
            self.assertEqual(status, 'OK')
            self.assertTrue(isinstance(template_list, list))
            self.assertEqual(len(template_list), 1)
            self.assertEqual(template, self.template_name)

    def test_add_non_existent_template_to_demo(self):
        """
        Test add non existent template to demo
        """
        status = None
        try:
            with open(self.blob_path, 'rb') as blob:
                self.add_blob_to_demo(blob=blob, demo_id=self.demo_id, blob_set=self.blob_set, pos_set=self.pos_in_set,
                                      title=self.title)

            response = self.add_templates_to_demo(self.demo_id, self.template_name)
            status = response.get('status')

            self.delete_demo(self.demo_id)

        finally:
            self.assertEqual(status, 'KO')

    def test_add_template_to_non_existent_demo(self):
        """
        Test add template to non existent demo
        """
        status = None
        try:

            self.create_template(self.template_name)

            response = self.add_templates_to_demo(self.demo_id, self.template_name)
            status = response.get('status')

            self.delete_template(self.template_name)

        finally:
            # This should be OK because the demo can exist in the demoinfo DB
            self.assertEqual(status, 'OK')

    def test_remove_template_from_demo(self):
        """
        Test remove template from demo
        """
        status = None
        template_list = None
        try:
            with open(self.blob_path, 'rb') as blob:
                self.add_blob_to_demo(blob=blob, demo_id=self.demo_id, blob_set=self.blob_set,
                                      pos_set=self.pos_in_set, title=self.title)

            self.create_template(self.template_name)
            self.add_templates_to_demo(self.demo_id, self.template_name)

            response = self.remove_template_from_demo(self.demo_id, self.template_name)
            status = response.get('status')

            response = self.get_demo_templates(self.demo_id)
            template_list = response.get('templates')

            self.delete_template(self.template_name)
            self.delete_demo(self.demo_id)

        finally:
            self.assertEqual(status, 'OK')
            self.assertTrue(isinstance(template_list, list))
            self.assertEqual(len(template_list), 0)

    def test_remove_non_existent_template_from_demo(self):
        """
        Test remove non existent template from demo
        """
        status = None
        try:
            with open(self.blob_path, 'rb') as blob:
                self.add_blob_to_demo(blob=blob, demo_id=self.demo_id, blob_set=self.blob_set,
                                      pos_set=self.pos_in_set, title=self.title)

            response = self.remove_template_from_demo(self.demo_id, self.template_name)
            status = response.get('status')

            self.delete_demo(self.demo_id)

        finally:
            self.assertEqual(status, 'KO')

    def test_remove_template_from_non_existent_demo(self):
        """
        Test remove template from non existent demo
        """
        status = None
        try:

            self.create_template(self.template_name)
            self.add_templates_to_demo(self.demo_id, self.template_name)

            response = self.remove_template_from_demo(self.demo_id, self.template_name)
            status = response.get('status')

            self.delete_template(self.template_name)

        finally:
            # This should be OK because the demo can exist in the demoinfo DB
            self.assertEqual(status, 'OK')

    def test_edit_blob_from_demo(self):
        """
        Test edit blob from demo
        """
        status = None
        new_title = self.title + '_new'
        title = None
        new_set = self.blob_set + '_new'
        the_set = None
        new_pos_in_set = self.pos_in_set + 1
        try:
            with open(self.blob_path, 'rb') as blob:
                self.add_blob_to_demo(blob=blob, demo_id=self.demo_id, blob_set=self.blob_set,
                                      pos_set=self.pos_in_set, title=self.title)

            response = self.edit_blob_from_demo(demo_id=self.demo_id, blob_set=self.blob_set,
                                                new_blob_set=new_set, pos_set=self.pos_in_set,
                                                new_pos_set=new_pos_in_set, title=new_title)
            status = response.get('status')

            json_response = self.get_blobs(self.demo_id)
            try:
                blob_list = json_response.get('sets')[0].get('blobs').get(str(new_pos_in_set))
                the_set = json_response.get('sets')[0].get('name')
                title = blob_list.get('title')
            except Exception:
                pass

            self.delete_demo(self.demo_id)

        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(new_title, title)
            self.assertEqual(new_set, the_set)

    def test_edit_non_existent_blob_from_demo(self):
        """
        Test edit non existent blob from demo
        """
        status = None
        new_title = self.title + '_new'
        new_set = self.blob_set + '_new'
        new_pos_in_set = self.pos_in_set + 1
        try:

            response = self.edit_blob_from_demo(demo_id=self.demo_id, blob_set=self.blob_set, new_blob_set=new_set,
                                                pos_set=self.pos_in_set, new_pos_set=new_pos_in_set, title=new_title)
            status = response.get('status')

        finally:
            self.assertEqual(status, 'KO')

    def test_edit_blob_from_template(self):
        """
        Test edit blob from template
        """
        status = None
        new_title = self.title + '_new'
        title = None
        new_set = self.blob_set + '_new'
        the_set = None
        new_pos_in_set = self.pos_in_set + 1
        try:
            self.create_template(self.template_name)

            with open(self.blob_path, 'rb') as blob:
                self.add_blob_to_template(blob=blob, template_name=self.template_name,
                                          blob_set=self.blob_set, pos_set=self.pos_in_set, title=self.title)

            response = self.edit_blob_from_template(template_name=self.template_name, title=new_title,
                                                    blob_set=self.blob_set, new_blob_set=new_set,
                                                    pos_set=self.pos_in_set, new_pos_set=new_pos_in_set)
            status = response.get('status')

            json_response = self.get_template_blobs(self.template_name)
            try:
                blob_list = json_response.get('sets')[0].get('blobs').get(str(new_pos_in_set))
                the_set = json_response.get('sets')[0].get('name')
                title = blob_list.get('title')
            except Exception:
                pass

            self.delete_template(self.template_name)

        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(new_title, title)
            self.assertEqual(new_set, the_set)

    def test_edit_non_existent_blob_from_template(self):
        """
        Test edit non existent blob from template
        """
        status = None
        new_title = self.title + '_new'
        new_set = self.blob_set + '_new'
        new_pos_in_set = self.pos_in_set + 1
        try:

            response = self.edit_blob_from_template(template_name=self.template_name, title=new_title,
                                                    blob_set=self.blob_set, new_blob_set=new_set,
                                                    pos_set=self.pos_in_set, new_pos_set=new_pos_in_set)
            status = response.get('status')

        finally:
            self.assertEqual(status, 'KO')

    def test_get_all_templates(self):
        """
        Test get all templates
        """
        status = None
        templates = None
        try:
            self.create_template(self.template_name)

            response = self.get_all_templates()
            status = response.get('status')
            templates = response.get('templates')

            self.delete_template(self.template_name)
        finally:
            self.assertEqual(status, 'OK')
            self.assertTrue(isinstance(templates, list))
            self.assertTrue(len(templates) > 0)

    def test_remove_visual_representation_from_blob(self):
        """
        Test remove visual representation from blob
        """
        status = None
        blob_vr = None
        try:
            with open(self.blob_path, 'rb') as blob, open(self.blob_path, 'rb') as vr:
                self.add_blob_to_demo(blob=blob, demo_id=self.demo_id, blob_vr=vr,
                                      blob_set=self.blob_set, pos_set=self.pos_in_set, title=self.title)
            json_response = self.get_blobs(self.demo_id)
            blob_id = None
            try:
                blob_list = json_response.get('sets')[0].get('blobs').get(str(self.pos_in_set))
                blob_id = blob_list.get('id')
            except Exception:
                pass

            response = self.delete_vr_from_blob(blob_id)
            status = response.get('status')

            json_response = self.get_blobs(self.demo_id)
            try:
                blob_list = json_response.get('sets')[0].get('blobs').get(str(self.pos_in_set))
                blob_vr = blob_list.get('vr')
            except Exception:
                pass

            self.delete_demo(self.demo_id)

        finally:
            self.assertEqual(status, 'OK')
            self.assertTrue(blob_vr is None)

    def test_remove_visual_representation_from_non_existent_blob(self):
        """
        Test remove visual representation from non existent blob
        """
        status = None
        try:
            response = self.delete_vr_from_blob(0)
            status = response.get('status')
        finally:
            self.assertEqual(status, 'KO')

    #####################
    #       TOOLS       #
    #####################

    def post(self, module, service, params=None, data=None, files=None, servicejson=None):
        """
            post
        """
        url = 'http://{}/api/{}/{}'.format(self.HOST, module, service)
        return requests.post(url, params=params, data=data, files=files, json=servicejson)

    def add_blob_to_demo(self, blob=None, demo_id=None, blob_set=None, pos_set=None, title=None,
                         credit=None, blob_vr=None):
        """
        add blob to demo
        """
        params = {}
        if demo_id is not None:
            params['demo_id'] = demo_id
        if blob_set is not None:
            params['blob_set'] = blob_set
        if pos_set is not None:
            params['pos_set'] = pos_set
        if title is not None:
            params['title'] = title
        if credit is not None:
            params['credit'] = credit
        files = {}
        if blob is not None:
            files['blob'] = blob
        if blob_vr is not None:
            files['blob_vr'] = blob_vr
        response = self.post(self.module, 'add_blob_to_demo', params=params, files=files)
        return response.json()

    def add_blob_to_template(self, blob=None, template_name=None, blob_set=None, pos_set=None, title=None,
                             credit=None, blob_vr=None):
        """
        add blob to template
        """
        params = {}
        if template_name is not None:
            params['template_name'] = template_name
        if blob_set is not None:
            params['blob_set'] = blob_set
        if pos_set is not None:
            params['pos_set'] = pos_set
        if title is not None:
            params['title'] = title
        if credit is not None:
            params['credit'] = credit
        files = {}
        if blob is not None:
            files['blob'] = blob
        if blob_vr is not None:
            files['blob_vr'] = blob_vr
        response = self.post(self.module, 'add_blob_to_template', params=params, files=files)
        return response.json()

    def delete_demo(self, demo_id):
        """
        delete demo
        """
        params = {'demo_id': demo_id}
        response = self.post(self.module, 'delete_demo', params=params)
        return response.json()

    def get_blobs(self, demo_id):
        """
        get blobs
        """
        params = {'demo_id': demo_id}
        response = self.post(self.module, 'get_blobs', params=params)
        return response.json()

    def get_template_blobs(self, template_name):
        """
        get template blobs
        """
        params = {'template_name': template_name}
        response = self.post(self.module, 'get_template_blobs', params=params)
        return response.json()

    def remove_blob_from_demo(self, demo_id, blob_set, pos_set):
        """
        remove blob from demo
        """
        params = {'demo_id': demo_id, 'blob_set': blob_set, 'pos_set': pos_set}
        response = self.post(self.module, 'remove_blob_from_demo', params=params)
        return response.json()

    def create_template(self, template_name):
        """
        create template
        """
        params = {'template_name': template_name}
        response = self.post(self.module, 'create_template', params=params)
        return response.json()

    def delete_template(self, template_name):
        """
        delete template
        """
        params = {'template_name': template_name}
        response = self.post(self.module, 'delete_template', params=params)
        return response.json()

    def remove_blob_from_template(self, template_name, blob_set, pos_set):
        """
        remove blob from template
        """
        params = {'template_name': template_name, 'blob_set': blob_set, 'pos_set': pos_set}
        response = self.post(self.module, 'remove_blob_from_template', params=params)
        return response.json()

    def add_templates_to_demo(self, demo_id, template_names):
        """
        add templates to demo
        """
        params = {'demo_id': demo_id, 'template_names': template_names}
        response = self.post(self.module, 'add_templates_to_demo', params=params)
        return response.json()

    def get_demo_templates(self, demo_id):
        """
        get demo templates
        """
        params = {'demo_id': demo_id}
        response = self.post(self.module, 'get_demo_templates', params=params)
        return response.json()

    def remove_template_from_demo(self, demo_id, template_name):
        """
        remove template from demo
        """
        params = {'demo_id': demo_id, 'template_name': template_name}
        response = self.post(self.module, 'remove_template_from_demo', params=params)
        return response.json()

    def edit_blob_from_demo(self, demo_id=None, blob_set=None, new_blob_set=None, pos_set=None,
                            new_pos_set=None, title=None, credit=None, vr=None):
        """
        edit blob from demo
        """
        params = {}
        if demo_id is not None:
            params['demo_id'] = demo_id
        if blob_set is not None:
            params['blob_set'] = blob_set
        if new_blob_set is not None:
            params['new_blob_set'] = new_blob_set
        if pos_set is not None:
            params['pos_set'] = pos_set
        if new_pos_set is not None:
            params['new_pos_set'] = new_pos_set
        if title is not None:
            params['title'] = title
        if credit is not None:
            params['credit'] = credit
        files = {}
        if vr is not None:
            files['blob_vr'] = vr
        response = self.post(self.module, 'edit_blob_from_demo', params=params, files=files)
        return response.json()

    def edit_blob_from_template(self, template_name=None, blob_set=None, new_blob_set=None, pos_set=None,
                                new_pos_set=None, title=None, credit=None, vr=None):
        """
        edit blob from template
        """
        params = {}
        if template_name is not None:
            params['template_name'] = template_name
        if blob_set is not None:
            params['blob_set'] = blob_set
        if new_blob_set is not None:
            params['new_blob_set'] = new_blob_set
        if pos_set is not None:
            params['pos_set'] = pos_set
        if new_pos_set is not None:
            params['new_pos_set'] = new_pos_set
        if title is not None:
            params['title'] = title
        if credit is not None:
            params['credit'] = credit
        files = {}
        if vr is not None:
            files['blob_vr'] = vr
        response = self.post(self.module, 'edit_blob_from_template', params=params, files=files)
        return response.json()

    def get_all_templates(self):
        """
        get all templates
        """
        response = self.post(self.module, 'get_all_templates')
        return response.json()

    def delete_vr_from_blob(self, blob_id):
        """
        delete vr from blob
        """
        params = {'blob_id': blob_id}
        response = self.post(self.module, 'delete_vr_from_blob', params=params)
        return response.json()


if __name__ == '__main__':
    shared_folder = sys.argv.pop()
    demorunners = sys.argv.pop()
    resources_path = sys.argv.pop()
    BlobsTests.blob_path = os.path.join(resources_path, 'test_image.png')
    unittest.main()
