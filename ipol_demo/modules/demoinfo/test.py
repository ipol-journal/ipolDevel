#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Demoinfo Test
"""
# Unit tests for the DemoInfo module
import socket
import unittest
import os
import sys
import json
import requests


class DemoinfoTests(unittest.TestCase):
    """
    Demoinfo unit tests
    """

    HOST = socket.gethostbyname(socket.gethostname())
    module = 'demoinfo'

    # Demo
    demo_id = -1
    demo_title = 'Demo test'
    state = 'test'

    # Author
    author_name = 'Author Test'
    author_email = 'authortestmail@email.com'

    # Editor
    editor_name = 'Editor Test'
    editor_email = 'editortestmail@email.com'

    # These variables are initialized in the __main__
    ddl_file = None
    demo_extras_file = None

    #####################
    #       Tests       #
    #####################
    def setUp(self):
        """
        Clean the DB from the tests
        """
        # Delete demo test
        self.delete_demo(self.demo_id)

        # Delete editor test
        response = self.editor_list()
        for editor in response.get('editor_list'):
            if editor.get('name') == self.editor_name:
                self.remove_editor(editor.get('id'))

        # Delete author test
        response = self.author_list()
        for author in response.get('author_list'):
            if author.get('name') == self.author_name:
                self.delete_author(author.get('id'))

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

    def test_add_and_delete_demo(self):
        """
        Test add and delete demo
        """
        add_status = None
        read_status = None
        name = None
        delete_status = None
        try:
            json_response = self.add_demo(self.demo_id, self.demo_title, self.state)
            add_status = json_response.get('status')

            json_response = self.read_demo_metainfo(self.demo_id)
            read_status = json_response.get('status')
            name = json_response.get('title')

            json_response = self.delete_demo(self.demo_id)
            delete_status = json_response.get('status')

        finally:
            self.assertEqual(add_status, 'OK')
            self.assertEqual(read_status, 'OK')
            self.assertEqual(name, self.demo_title)
            self.assertEqual(delete_status, 'OK')

    def test_add_same_demo_again(self):
        """
        Test add same demo again
        """
        status = None
        try:

            self.add_demo(self.demo_id, self.demo_title, self.state)

            json_response = self.add_demo(self.demo_id, self.demo_title, self.state)
            status = json_response.get('status')

            self.delete_demo(self.demo_id)

        finally:
            self.assertEqual(status, 'KO')

    def test_delete_non_existent_demo(self):
        """
        Test delete non existent demo
        """
        status = None
        try:
            json_response = self.delete_demo(self.demo_id)
            status = json_response.get('status')
        finally:
            self.assertEqual(status, 'OK')

    def test_add_ddl_to_new_demo(self):
        """
        Test add ddl to new demo
        """
        add_status = None
        get_status = None
        ddl_read = None
        ddl = None
        try:
            self.add_demo(self.demo_id, self.demo_title, self.state)

            ddl = self.read_ddl()
            json_response = self.save_ddl(self.demo_id, ddl)
            add_status = json_response.get('status')

            # Check if added correctly
            json_response = self.get_ddl(self.demo_id)
            get_status = json_response.get('status')
            ddl_read = json_response.get('last_demodescription').get('ddl')

            self.delete_demo(self.demo_id)
        finally:
            self.assertEqual(add_status, 'OK')
            self.assertEqual(get_status, 'OK')
            self.assertEqual(json.loads(ddl), json.loads(ddl_read))

    def test_add_ddl_to_non_existent_demo(self):
        """
        Test add ddl to non existent demo
        """
        status = None
        try:
            ddl = self.read_ddl()
            json_response = self.save_ddl(self.demo_id, ddl)
            status = json_response.get('status')
        finally:
            self.assertEqual(status, 'KO')

    def test_add_demoextras_to_new_demo(self):
        """
        Test add demoextras to new demo
        """
        add_status = None
        get_status = None
        demo_extras = None
        size = None
        try:
            self.add_demo(self.demo_id, self.demo_title, self.state)

            demo_extras = self.read_demoextras()
            json_response = self.add_demoextras(self.demo_id, demo_extras)
            add_status = json_response.get('status')

            # Check if added correctly
            json_response = self.get_demoextras_info(self.demo_id)
            get_status = json_response.get('status')
            size = json_response.get('size')

            self.delete_demo(self.demo_id)
        finally:
            self.assertEqual(add_status, 'OK')
            self.assertEqual(get_status, 'OK')
            self.assertEqual(size, os.stat(demo_extras.name).st_size)

    def test_add_demoextras_to_non_existent_demo(self):
        """
        Test add demoextras to non existent demo
        """
        status = None
        try:
            demo_extras = self.read_demoextras()
            json_response = self.add_demoextras(self.demo_id, demo_extras)
            status = json_response.get('status')
        finally:
            self.assertEqual(status, 'KO')

    def test_demo_list(self):
        """
        Test demo list
        """
        status = None
        demo_list = None
        try:
            json_response = self.demo_list()
            status = json_response.get('status')
            demo_list = json_response.get('demo_list')
        finally:
            self.assertEqual(status, 'OK')
            self.assertTrue(isinstance(demo_list, list))

    def test_update_demo(self):
        """
        Test update demo
        """
        update_status = None
        read_status = None
        title = None
        new_title = self.demo_title + "2"
        state = None
        new_state = 'published'
        try:
            self.add_demo(self.demo_id, self.demo_title, self.state)
            new_demo = {
                "title": new_title,
                "editorsdemoid": self.demo_id,
                "state": new_state}
            json_response = self.update_demo(new_demo, self.demo_id)
            update_status = json_response.get('status')

            json_response = self.read_demo_metainfo(self.demo_id)
            read_status = json_response.get('status')
            title = json_response.get('title')
            state = json_response.get('state')

            self.delete_demo(self.demo_id)
        finally:
            self.assertEqual(update_status, 'OK')
            self.assertEqual(read_status, 'OK')
            self.assertEqual(title, new_title)
            self.assertEqual(state, new_state)

    def test_add_and_delete_author(self):
        """
        Test add and delete author
        """
        add_status = None
        del_status = None
        author_id = None
        try:
            json_response = self.add_author(self.author_name, self.author_email)
            add_status = json_response.get('status')
            author_id = json_response.get('authorid')

            json_response = self.delete_author(author_id)
            del_status = json_response.get('status')
        finally:
            self.assertEqual(add_status, 'OK')
            self.assertTrue(isinstance(author_id, int))
            self.assertEqual(del_status, 'OK')

    def test_add_already_existing_author(self):
        """
        Test add already existing author
        """
        status = None
        try:
            json_response = self.add_author(self.author_name, self.author_email)
            author_id = json_response.get('authorid')

            json_response = self.add_author(self.author_name, self.author_email)
            status = json_response.get('status')

            self.delete_author(author_id)
        finally:
            self.assertEqual(status, 'KO')

    def test_author_list(self):
        """
        Test author list
        """
        status = None
        author_list = None
        try:
            response = self.post(self.module, 'author_list')
            json_response = response.json()
            status = json_response.get('status')
            author_list = json_response.get('author_list')
        finally:
            self.assertEqual(status, 'OK')
            self.assertTrue(isinstance(author_list, list))

    def test_read_author(self):
        """
        Test read author
        """
        status = None
        name = None
        email = None
        try:
            json_response = self.add_author(self.author_name, self.author_email)
            author_id = json_response.get('authorid')

            json_response = self.read_author(author_id)
            status = json_response.get('status')
            name = json_response.get('name')
            email = json_response.get('mail')

            self.delete_author(author_id)
        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(name, self.author_name)
            self.assertEqual(email, self.author_email)

    def test_read_non_existent_author(self):
        """
        Test read non existent author
        """
        status = None
        try:
            json_response = self.read_author(0)
            status = json_response.get('status')
        finally:
            self.assertEqual(status, 'KO')

    def test_add_author_to_demo(self):
        """
        Test add author to demo
        """
        status = None
        try:
            json_response = self.add_author(self.author_name, self.author_email)
            author_id = json_response.get('authorid')

            self.add_demo(self.demo_id, self.demo_title, self.state)

            json_response = self.add_author_to_demo(self.demo_id, author_id)
            status = json_response.get('status')

            self.delete_author(author_id)

            self.delete_demo(self.demo_id)

        finally:
            self.assertEqual(status, 'OK')

    def test_add_author_to_non_existent_demo(self):
        """
        Test add author to non existent demo
        """
        status = None
        try:
            json_response = self.add_author(self.author_name, self.author_email)
            author_id = json_response.get('authorid')

            json_response = self.add_author_to_demo(self.demo_id, author_id)
            status = json_response.get('status')

            self.delete_author(author_id)

        finally:
            self.assertEqual(status, 'KO')

    def test_add_non_existent_author_to_demo(self):
        """
        Test add non existent author to demo
        """
        status = None
        try:

            self.add_demo(self.demo_id, self.demo_title, self.state)

            json_response = self.add_author_to_demo(self.demo_id, 0)
            status = json_response.get('status')

            self.delete_demo(self.demo_id)

        finally:
            self.assertEqual(status, 'KO')

    def test_demo_get_authors_list(self):
        """
        Test demo get authors list
        """
        status = None
        author_list = None
        author_name = None
        author_email = None

        try:
            json_response = self.add_author(self.author_name, self.author_email)
            author_id = json_response.get('authorid')

            self.add_demo(self.demo_id, self.demo_title, self.state)

            self.add_author_to_demo(self.demo_id, author_id)

            json_response = self.demo_get_authors_list(self.demo_id)
            status = json_response.get('status')
            author_list = json_response.get('author_list')
            author_name = author_list[0].get('name')
            author_email = author_list[0].get('mail')

            self.delete_author(author_id)

            self.delete_demo(self.demo_id)

        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(len(author_list), 1)
            self.assertEqual(author_name, self.author_name)
            self.assertEqual(author_email, self.author_email)

    def test_demo_get_authors_list_in_non_existent_demo(self):
        """
        Test demo get authors list in non existent demo
        """
        status = None

        try:
            json_response = self.demo_get_authors_list(self.demo_id)
            status = json_response.get('status')

        finally:
            self.assertEqual(status, 'KO')

    def test_author_get_demos_list(self):
        """
        Test author get demos list
        """
        status = None
        demo_list = None
        demo_id = None

        try:
            json_response = self.add_author(self.author_name, self.author_email)
            author_id = json_response.get('authorid')

            self.add_demo(self.demo_id, self.demo_title, self.state)

            self.add_author_to_demo(self.demo_id, author_id)

            json_response = self.author_get_demos_list(author_id)
            status = json_response.get('status')
            demo_list = json_response.get('demo_list')
            demo_id = demo_list[0].get('editorsdemoid')

            self.delete_author(author_id)

            self.delete_demo(self.demo_id)

        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(len(demo_list), 1)
            self.assertEqual(demo_id, self.demo_id)

    def test_author_get_demos_list_with_non_existent_author(self):
        """
        Test author get demos list with non existent author
        """
        status = None

        try:
            json_response = self.author_get_demos_list(0)
            status = json_response.get('status')

        finally:
            self.assertEqual(status, 'KO')

    def test_update_author(self):
        """
        Test update author
        """
        status = None
        name = None
        email = None
        new_name = self.author_name + "_new"
        new_email = self.author_email + "_new"
        try:
            json_response = self.add_author(self.author_name, self.author_email)
            author_id = json_response.get('authorid')

            new_author = {'name': new_name,
                          'mail': new_email,
                          'id': author_id}
            params = {'author': json.dumps(new_author)}
            response = self.post(self.module, 'update_author', params=params)
            json_response = response.json()
            status = json_response.get('status')

            json_response = self.read_author(author_id)
            name = json_response.get('name')
            email = json_response.get('mail')

            self.delete_author(author_id)
        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(name, new_name)
            self.assertEqual(email, new_email)

    def test_update_non_existent_author(self):
        """
        Test update non existent author
        """
        status = None
        new_name = self.author_name + "_new"
        new_email = self.author_email + "_new"
        try:
            new_author = {'name': new_name,
                          'mail': new_email,
                          'id': 0}
            params = {'author': json.dumps(new_author)}
            response = self.post(self.module, 'update_author', params=params)
            json_response = response.json()
            status = json_response.get('status')

        finally:
            self.assertEqual(status, 'KO')

    def test_remove_author_from_demo(self):
        """
        Test remove author from demo
        """
        status = None
        author_list = None
        try:
            json_response = self.add_author(self.author_name, self.author_email)
            author_id = json_response.get('authorid')

            self.add_demo(self.demo_id, self.demo_title, self.state)

            self.add_author_to_demo(self.demo_id, author_id)

            json_response = self.remove_author_from_demo(self.demo_id, author_id)
            status = json_response.get('status')

            json_response = self.demo_get_authors_list(self.demo_id)
            author_list = json_response.get('author_list')

            self.delete_author(author_id)

            self.delete_demo(self.demo_id)

        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(len(author_list), 0)

    def test_remove_author_from_non_existent_demo(self):
        """
        Test remove author from non existent demo
        """
        status = None
        try:
            json_response = self.add_author(self.author_name, self.author_email)
            author_id = json_response.get('authorid')

            json_response = self.remove_author_from_demo(self.demo_id, author_id)
            status = json_response.get('status')

            self.delete_author(author_id)

        finally:
            self.assertEqual(status, 'KO')

    def test_remove_non_existent_author_from_demo(self):
        """
        Test remove non existent author from demo
        """
        status = None
        try:

            self.add_demo(self.demo_id, self.demo_title, self.state)

            json_response = self.remove_author_from_demo(self.demo_id, 0)
            status = json_response.get('status')

            self.delete_demo(self.demo_id)

        finally:
            self.assertEqual(status, 'KO')

    def test_add_and_delete_editor(self):
        """
        Test add and delete editor
        """
        add_status = None
        del_status = None
        editor_id = None
        try:
            json_response = self.add_editor(self.editor_name, self.editor_email)
            add_status = json_response.get('status')
            editor_id = json_response.get('editorid')

            json_response = self.remove_editor(editor_id)
            del_status = json_response.get('status')
        finally:
            self.assertEqual(add_status, 'OK')
            self.assertTrue(isinstance(editor_id, int))
            self.assertEqual(del_status, 'OK')

    def test_add_already_existing_editor(self):
        """
        Test add already existing editor
        """
        status = None
        try:
            json_response = self.add_editor(self.editor_name, self.editor_email)
            editor_id = json_response.get('editorid')

            json_response = self.add_editor(self.editor_name, self.editor_email)
            status = json_response.get('status')

            self.remove_editor(editor_id)
        finally:
            self.assertEqual(status, 'KO')

    def test_editor_list(self):
        """
        Test editor list
        """
        status = None
        editor_list = None
        try:
            json_response = self.editor_list()
            status = json_response.get('status')
            editor_list = json_response.get('editor_list')
        finally:
            self.assertEqual(status, 'OK')
            self.assertTrue(isinstance(editor_list, list))

    def test_read_editor(self):
        """
        Test read editor
        """
        status = None
        name = None
        email = None
        try:
            json_response = self.add_editor(self.editor_name, self.editor_email)
            editor_id = json_response.get('editorid')

            json_response = self.read_editor(editor_id)
            status = json_response.get('status')
            name = json_response.get('name')
            email = json_response.get('mail')

            self.remove_editor(editor_id)
        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(name, self.editor_name)
            self.assertEqual(email, self.editor_email)

    def test_read_non_existent_editor(self):
        """
        Test read non existent editor
        """
        status = None
        try:
            json_response = self.read_editor(0)
            status = json_response.get('status')
        finally:
            self.assertEqual(status, 'KO')

    def test_add_editor_to_demo(self):
        """
        Test add editor to demo
        """
        status = None
        try:
            json_response = self.add_editor(self.editor_name, self.editor_email)
            editor_id = json_response.get('editorid')

            self.add_demo(self.demo_id, self.demo_title, self.state)

            json_response = self.add_editor_to_demo(self.demo_id, editor_id)
            status = json_response.get('status')

            self.remove_editor(editor_id)

            self.delete_demo(self.demo_id)

        finally:
            self.assertEqual(status, 'OK')

    def test_add_editor_to_non_existent_demo(self):
        """
        Test add editor to non existent demo
        """
        status = None
        try:
            json_response = self.add_editor(self.editor_name, self.editor_email)
            editor_id = json_response.get('editorid')

            json_response = self.add_editor_to_demo(self.demo_id, editor_id)
            status = json_response.get('status')

            self.remove_editor(editor_id)

        finally:
            self.assertEqual(status, 'KO')

    def test_add_non_existent_editor_to_demo(self):
        """
        Test add non existent editor to demo
        """
        status = None
        try:

            self.add_demo(self.demo_id, self.demo_title, self.state)

            json_response = self.add_editor_to_demo(self.demo_id, 0)
            status = json_response.get('status')

            self.delete_demo(self.demo_id)

        finally:
            self.assertEqual(status, 'KO')

    def test_demo_get_editor_list(self):
        """
        Test demo get editor list
        """
        status = None
        editor_list = None
        editor_name = None
        editor_email = None

        try:
            json_response = self.add_editor(self.editor_name, self.editor_email)
            editor_id = json_response.get('editorid')

            self.add_demo(self.demo_id, self.demo_title, self.state)

            self.add_editor_to_demo(self.demo_id, editor_id)

            json_response = self.demo_get_editors_list(self.demo_id)
            status = json_response.get('status')
            editor_list = json_response.get('editor_list')
            editor_name = editor_list[0].get('name')
            editor_email = editor_list[0].get('mail')

            self.remove_editor(editor_id)

            self.delete_demo(self.demo_id)

        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(len(editor_list), 1)
            self.assertEqual(editor_name, self.editor_name)
            self.assertEqual(editor_email, self.editor_email)

    def test_demo_get_editor_list_in_non_existent_demo(self):
        """
        Test demo get editor list in non existent demo
        """
        status = None

        try:
            json_response = self.demo_get_editors_list(self.demo_id)
            status = json_response.get('status')

        finally:
            self.assertEqual(status, 'KO')

    def test_editor_get_demos_list(self):
        """
        Test editor get demos list
        """
        status = None
        demo_list = None
        demo_id = None

        try:
            json_response = self.add_editor(self.editor_name, self.editor_email)
            editor_id = json_response.get('editorid')

            self.add_demo(self.demo_id, self.demo_title, self.state)

            self.add_editor_to_demo(self.demo_id, editor_id)

            json_response = self.editor_get_demos_list(editor_id)
            status = json_response.get('status')
            demo_list = json_response.get('demo_list')
            demo_id = demo_list[0].get('editorsdemoid')

            self.remove_editor(editor_id)

            self.delete_demo(self.demo_id)

        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(len(demo_list), 1)
            self.assertEqual(demo_id, self.demo_id)

    def test_editor_get_demos_list_with_non_existent_author(self):
        """
        Test editor get demos list with non existent author
        """
        status = None

        try:
            json_response = self.editor_get_demos_list(0)
            status = json_response.get('status')

        finally:
            self.assertEqual(status, 'KO')

    def test_update_editor(self):
        """
        Test update editor
        """
        status = None
        name = None
        email = None
        new_name = self.editor_name + "_new"
        new_email = self.editor_email + "_new"
        try:
            json_response = self.add_editor(self.editor_name, self.editor_email)
            editor_id = json_response.get('editorid')

            new_editor = {'name': new_name,
                          'mail': new_email,
                          'id': editor_id}

            json_response = self.update_editor(new_editor)
            status = json_response.get('status')

            json_response = self.read_editor(editor_id)
            name = json_response.get('name')
            email = json_response.get('mail')

            self.remove_editor(editor_id)
        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(name, new_name)
            self.assertEqual(email, new_email)

    def test_update_non_existent_editor(self):
        """
        Test update non existent editor
        """
        status = None
        new_name = self.editor_name + "_new"
        new_email = self.editor_email + "_new"
        try:
            new_editor = {'name': new_name,
                          'mail': new_email,
                          'id': 0}
            json_response = self.update_editor(new_editor)
            status = json_response.get('status')

        finally:
            self.assertEqual(status, 'KO')

    def test_remove_editor_from_demo(self):
        """
        Test remove editor from demo
        """
        status = None
        editor_list = None
        try:
            json_response = self.add_editor(self.editor_name, self.editor_email)
            editor_id = json_response.get('editorid')

            self.add_demo(self.demo_id, self.demo_title, self.state)

            self.add_editor_to_demo(self.demo_id, editor_id)

            json_response = self.remove_editor_from_demo(self.demo_id, editor_id)
            status = json_response.get('status')

            json_response = self.demo_get_editors_list(self.demo_id)
            editor_list = json_response.get('editor_list')

            self.remove_editor(editor_id)

            self.delete_demo(self.demo_id)

        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(len(editor_list), 0)

    def test_remove_editor_from_non_existent_demo(self):
        """
        Test remove editor from non existent demo
        """
        status = None
        try:
            json_response = self.add_editor(self.editor_name, self.editor_email)
            editor_id = json_response.get('editorid')

            json_response = self.remove_editor_from_demo(self.demo_id, editor_id)
            status = json_response.get('status')

            self.remove_editor(editor_id)

        finally:
            self.assertEqual(status, 'KO')

    def test_remove_non_existent_editor_from_demo(self):
        """
        Test remove non existent editor from demo
        """
        status = None
        try:
            self.add_demo(self.demo_id, self.demo_title, self.state)

            json_response = self.remove_editor_from_demo(self.demo_id, 0)
            status = json_response.get('status')

            self.delete_demo(self.demo_id)

        finally:
            self.assertEqual(status, 'KO')

    def test_read_states(self):
        """
        test read states
        """
        status = None
        state_list = None
        try:
            json_response = self.read_states()
            status = json_response.get('status')
            state_list = json_response.get('state_list')

        finally:
            self.assertEqual(status, 'OK')
            self.assertTrue(isinstance(state_list, list))
            self.assertTrue(len(state_list) > 0)

    def test_stats(self):
        """
        test stats
        """
        status = None
        try:
            json_response = self.stats()
            status = json_response.get('status')

        finally:
            self.assertEqual(status, 'OK')

    #####################
    #       TOOLS       #
    #####################

    def post(self, module, service, params=None, data=None, files=None, servicejson=None):
        """
        post
        """
        url = 'http://{}/api/{}/{}'.format(self.HOST, module, service)
        return requests.post(url, params=params, data=data, files=files, json=servicejson)

    def read_ddl(self):
        """
        read ddl
        """
        with open(self.ddl_file, 'r') as f:
            ddl = f.read()
        return ddl

    def read_demoextras(self):
        """
        read demoextras
        """
        return open(self.demo_extras_file, 'r')

    def add_demo(self, demo_id, title, state):
        """
        add demo
        """
        params = {'editorsdemoid': demo_id, 'title': title, 'state': state}
        response = self.post(self.module, 'add_demo', params=params)
        return response.json()

    def read_demo_metainfo(self, demo_id):
        """
        read demo metainfo
        """
        params = {'demoid': demo_id}
        response = self.post(self.module, 'read_demo_metainfo', params=params)
        return response.json()

    def delete_demo(self, demo_id):
        """
        delete demo
        """
        params = {'demo_id': demo_id}
        response = self.post(self.module, 'delete_demo', params=params)
        return response.json()

    def save_ddl(self, demo_id, ddl):
        """
        save ddl
        """
        params = {'demoid': demo_id}
        response = self.post(self.module, 'save_demo_description', params=params, servicejson=json.loads(ddl))
        return response.json()

    def get_ddl(self, demo_id):
        """
        get ddl
        """
        params = {'demo_id': demo_id}
        response = self.post(self.module, 'get_ddl', params=params)
        return response.json()

    def add_demoextras(self, demo_id, demo_extras):
        """
        add demoextras
        """
        files = {'file_0': demo_extras}
        params = {'demo_id': demo_id}
        response = self.post(self.module, 'add_compressed_file_ws', params=params, files=files)
        return response.json()

    def get_demoextras_info(self, demo_id):
        """
        get demoextras info
        """
        params = {'demo_id': demo_id}
        response = self.post(self.module, 'get_demo_extras_info', params=params)
        return response.json()

    def demo_list(self):
        """
        demo list
        """
        response = self.post(self.module, 'demo_list')
        return response.json()

    def update_demo(self, new_demo, demo_id):
        """
        update demo
        """
        params = {'demo': json.dumps(new_demo), 'old_editor_demoid': demo_id}
        response = self.post(self.module, 'update_demo', params=params)
        return response.json()

    def add_author(self, name, email):
        """
        add author
        """
        params = {'name': name, 'mail': email}
        response = self.post(self.module, 'add_author', params=params)
        return response.json()

    def author_list(self):
        """
        author list
        """
        response = self.post(self.module, 'author_list')
        return response.json()

    def delete_author(self, author_id):
        """
        delete author
        """
        params = {'author_id': author_id}
        response = self.post(self.module, 'remove_author', params=params)
        return response.json()

    def read_author(self, author_id):
        """
        read author
        """
        params = {'authorid': author_id}
        response = self.post(self.module, 'read_author', params=params)
        return response.json()

    def add_author_to_demo(self, demo_id, author_id):
        """
        add author to demo
        """
        params = {'demo_id': demo_id, 'author_id': author_id}
        response = self.post(self.module, 'add_author_to_demo', params=params)
        return response.json()

    def demo_get_authors_list(self, demo_id):
        """
        demo get authors list
        """
        params = {'demo_id': demo_id}
        response = self.post(self.module, 'demo_get_authors_list', params=params)
        return response.json()

    def author_get_demos_list(self, author_id):
        """
        author get demos list
        """
        params = {'author_id': author_id}
        response = self.post(self.module, 'author_get_demos_list', params=params)
        return response.json()

    def remove_author_from_demo(self, demo_id, author_id):
        """
        remove author from demo
        """
        params = {'demo_id': demo_id, 'author_id': author_id}
        response = self.post(self.module, 'remove_author_from_demo', params=params)
        return response.json()

    def add_editor(self, name, email):
        """
        add editor
        """
        params = {'name': name, 'mail': email}
        response = self.post(self.module, 'add_editor', params=params)
        return response.json()

    def remove_editor(self, editor_id):
        """
        remove editor
        """
        params = {'editor_id': editor_id}
        response = self.post(self.module, 'remove_editor', params=params)
        return response.json()

    def editor_list(self):
        """
        editor list
        """
        response = self.post(self.module, 'editor_list')
        return response.json()

    def read_editor(self, editor_id):
        """
        read editor
        """
        params = {'editorid': editor_id}
        response = self.post(self.module, 'read_editor', params=params)
        return response.json()

    def add_editor_to_demo(self, demo_id, editor_id):
        """
        add editor to demo
        """
        params = {'demo_id': demo_id, 'editor_id': editor_id}
        response = self.post(self.module, 'add_editor_to_demo', params=params)
        return response.json()

    def demo_get_editors_list(self, demo_id):
        """
        demo get editors list
        """
        params = {'demo_id': demo_id}
        response = self.post(self.module, 'demo_get_editors_list', params=params)
        return response.json()

    def editor_get_demos_list(self, editor_id):
        """
        editor get demos list
        """
        params = {'editor_id': editor_id}
        response = self.post(self.module, 'editor_get_demos_list', params=params)
        return response.json()

    def update_editor(self, editor):
        """
        update editor
        """
        params = {'editor': json.dumps(editor)}
        response = self.post(self.module, 'update_editor', params=params)
        return response.json()

    def remove_editor_from_demo(self, demo_id, editor_id):
        """
        remove editor from demo
        """
        params = {'demo_id': demo_id, 'editor_id': editor_id}
        response = self.post(self.module, 'remove_editor_from_demo', params=params)
        return response.json()

    def stats(self):
        """
        stats
        """
        response = self.post(self.module, 'stats')
        return response.json()

    def read_states(self):
        """
        read states
        """
        response = self.post(self.module, 'read_states')
        return response.json()

if __name__ == '__main__':
    shared_folder = sys.argv.pop()
    demorunners = sys.argv.pop()
    resources_path = sys.argv.pop()
    DemoinfoTests.ddl_file = os.path.join(resources_path, 'test_ddl.txt')
    DemoinfoTests.demo_extras_file = os.path.join(resources_path, 'test_demo_extras.tar.gz')
    unittest.main()
