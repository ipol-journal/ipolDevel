#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
This file implements multithreading Test class
"""

import threading
import cherrypy
import os
import os.path
import sys
from blobs import use_web_service
from error import print_usage_function

class   Test(threading.Thread):
    """
    This class allows to test if the module supports load
    """
    def __init__(self, test_dir):
        """
        Initialize test class
        Call the constructor of the thread library

        :param test_dir: name of the test directory
        :type test_dir: string
        """
        threading.Thread.__init__(self)

        self.test_dir = test_dir
        self.current_directory = os.getcwd()

        path_to_test = os.path.join(self.current_directory, self.test_dir)

        error_path = os.path.join(path_to_test, "error.txt")
        self.error_file = open(error_path, "a")

    def test_function(self):
        """
        Launch test on web service about: add, get and delete
        Write infos on error.txt in test file
        """
        path_to_images = os.path.join(self.current_directory,
                                      self.test_dir, 'images')
        image = os.path.join(path_to_images, 'bag.png')
        image2 = os.path.join(path_to_images, 'IMG_0230_raw_x32.png')

        print >> self.error_file, "\n\n---Test Function---\n\n"

        i = 1

        data = {"name": "denoising", "is_template": 0, "template": ""}
        res = use_web_service('/add_demo_ws', data)

        print >> self.error_file, res["return"]

        data = {"demo_id": i, "path": image, "tag": ["BW", ""], "ext": ".png",
                "blob_set": "", "title": "", "credit": ""}
        res = use_web_service('/add_blob_ws', data)

        print >> self.error_file, res["return"]

        data = {"demo_id": i, "path": image2, "tag": ["BW", ""], "ext": ".png",
                "blob_set": "", "title": "", "credit": ""}
        res = use_web_service('/add_blob_ws', data)
        print >> self.error_file, res["return"]

        data = {"demo_id": i, "blob_id": 1}
        res = use_web_service('/delete_blob_ws', data)
        print >> self.error_file, res["return"]

        data = {"demo_id": i, "blob_id": 2}
        res = use_web_service('/delete_blob_ws', data)
        print >> self.error_file, res["return"]

        data = {"demo_id": i}
        res = use_web_service('/op_remove_demo_ws', data)
        print >> self.error_file, res["return"]

        print >> self.error_file, "---End of Test function---"


    def run(self):
        """
        Overload of the run function of the thread library
        It is called by start()
        """
        print "starting"
        self.test_function()

def test_function(test_dir):
    """
    Create four instances of Test class in multithreading

    :param test_dir: name of the test directory
    :type test_dir: string
    """
    threads = []
    i = 0

    while i < 4:
        item = Test(test_dir)
        item.start()
        threads.append(item)

        for tmp in threads:
            tmp.join()
        i += 1

if __name__ == '__main__':
    if len(sys.argv) != 2 or not os.path.isfile(sys.argv[1]):
        print_usage_function(sys.argv[0])
        sys.exit(1)

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CONF_FILE = os.path.join(BASE_DIR, sys.argv[1])

    cherrypy.config.update(CONF_FILE)

    TEST = cherrypy.config['test.dir']
    PATH = os.path.join(BASE_DIR, TEST, 'error.txt')
    if os.path.exists(PATH):
        os.remove(PATH)
    test_function(TEST)



