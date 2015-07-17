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
from module import use_web_service
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

        i = 42

        data = {"name": i, "path": image, "tag": ["BW", ""], "ext": ".png"}
        res = use_web_service('/add_blob_ws', data)

        print >> self.error_file, res[0]

        data = {"name": i, "path": image2, "tag": ["BW", ""], "ext": ".png"}
        res = use_web_service('/add_blob_ws', data)
        print >> self.error_file, res[0]

        data = {"hash_blob": '87659853a31b299f62785552ecf00a6b64b9b6a0'}
        res = use_web_service('/get_demo_ws', data)

        print >> self.error_file, res[0]

        data = {"tag": 'BW'}
        res = use_web_service('/get_blob_ws', data)
        print >> self.error_file, res

        data = {"demo": i, "hash_blob":
                "87659853a31b299f62785552ecf00a6b64b9b6a0"}
        res = use_web_service('/delete_blob_ws', data)
        print >> self.error_file, res[0]

        data = {"demo": i, "hash_blob":
                "20692be1e865ca4149a1c6894579e03b8575dc3"}
        res = use_web_service('/delete_blob_ws', data)
        print >> self.error_file, res[0]

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



