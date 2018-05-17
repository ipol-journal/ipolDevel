#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Conversion tests.
"""
# Unit tests for the Conversion module
import socket
import json
import unittest
import shutil
import os
import sys
import tempfile
import requests
import numpy as np
from ipolutils.image.Image import Image



class ConversionTests(unittest.TestCase):
    """
    Dispatcher tests.
    """
    HOST = socket.gethostbyname(socket.gethostname())
    module = 'conversion'
    blob_path = None

    #####################
    #       Tests       #
    #####################

    def setUp(self):
        """
        Creates a copy of the image before convert it.
        """
        try:
            copy_image = os.path.split(self.blob_path)[0] + '/input_0' + os.path.splitext(self.blob_path)[1]
            shutil.copy2(self.blob_path, copy_image)
        except Exception:
            pass

    def tearDown(self):
        """
        Restores the copy of the image.
        """
        try:
            copy_image = os.path.split(self.blob_path)[0] + '/input_0' + os.path.splitext(self.blob_path)[1]
            os.remove(copy_image)
        except Exception:
            pass

    @staticmethod
    def bgr_test(depth):
        """
        Creates a standard image matrix.
        """
        depth_dtypes = {'8i': np.uint8, '16i': np.uint16, '32i': np.uint32, '16f': np.float16, '32f': np.float32}
        dtype = depth_dtypes[depth]
        if np.issubdtype(dtype, np.integer):
            dtype_max = np.iinfo(dtype).max
        else:
            dtype_max = 1
        bgr = np.zeros((32, 48, 3))
        bgr[0:16, :, 0] = dtype_max
        bgr[:, 0:32, 1] = dtype_max
        bgr[:, 0:16, 2] = dtype_max
        bgr = bgr.astype(dtype, copy=False)
        return bgr

    def test_tiff_depths(self):
        """
        Tests the conversions between all supported dtypes in tiff.
        """
        tif_file = tempfile.NamedTemporaryFile(suffix='.tif', prefix="ipol_", delete=True)
        for src_depth in ['8i', '16i', '32i', '16f', '32f']:
            for dst_depth in ['8i', '16i', '32i']: # float as a destination is not strictly equal
                data = self.bgr_test(src_depth)
                im = Image.data(data)
                im.convert_depth(dst_depth)
                im.write(tif_file.name)
                im = im.load(tif_file.name)
                data = self.bgr_test(dst_depth)
                self.assertTrue((im.data == data).all(), msg="{} > {}".format(src_depth, dst_depth))
        tif_file.close()

    def test_8i_extensions(self):
        """
        Tests the conversions between 8 bits file formats.
        """
        data = self.bgr_test('8i')
        # gif is not supported by OpenCV, .jpg do not keep exact colors
        exts = ['.bmp', '.png', '.tif']
        for src_ext in exts:
            src_file = tempfile.NamedTemporaryFile(suffix=src_ext, prefix="ipol_", delete=True)
            src_im = Image.data(data)
            src_im.write(src_file.name)
            src_im = Image.load(src_file.name)
            for dst_ext in exts:
                dst_file = tempfile.NamedTemporaryFile(suffix=dst_ext, prefix="ipol_", delete=True)
                src_im.write(dst_file.name)
                dst_im = Image.load(dst_file.name)
                self.assertTrue((src_im.data == dst_im.data).all(), msg="{} > {}".format(src_ext, dst_ext))
                dst_file.close()
            src_file.close()

    def test_ping(self):
        """
        Tests ping.
        """
        status = None
        try:
            response = self.post(self.module, 'ping')
            json_response = response.json()
            status = json_response.get('status')
        finally:
            self.assertEqual(status, 'OK')

    def test_convert_change_image_ext(self):
        """
        Tests extension conversion.
        """
        status = None
        code = None
        try:
            ext = '.bmp'
            input_file = os.path.split(self.blob_path)[0]
            input_desc = [{'description': 'input', 'max_pixels': '1024 * 2000', 'dtype': '3x8i', 'ext': ext,
                           'type': 'image', 'max_weight': 5242880}]
            crop_info = None
            response = self.convert(input_file, input_desc, crop_info)
            status = response.get('status')
            code = response.get('info').get('0').get('code')
            os.remove(os.path.split(self.blob_path)[0] + '/input_0' + ext)
        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(str(code), '1')

    def test_convert_image_that_do_not_need_conversion(self):
        """
        Tests to convert image that does not need conversion.
        """
        status = None
        code = None
        try:
            ext = '.png'
            input_file = os.path.split(self.blob_path)[0]
            input_desc = [{'description': 'input', 'max_pixels': '1024 * 2000', 'ext': ext,
                           'type': 'image', 'max_weight': 5242880}]
            crop_info = None
            response = self.convert(input_file, input_desc, crop_info)
            status = response.get('status')
            code = response.get('info').get('0').get('code')
            os.remove(os.path.split(self.blob_path)[0] + '/input_0' + ext)
        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(str(code), '0')

    def test_convert_resize_image(self):
        """
        Tests to downsize a picture to max_pixels.
        """
        status = None
        code = None
        try:
            ext = '.png'
            input_file = os.path.split(self.blob_path)[0]
            input_desc = [{'description': 'input', 'max_pixels': '150', 'ext': ext,
                           'type': 'image', 'max_weight': 5242880}]
            response = self.convert(input_file, input_desc, None)
            status = response.get('status')
            code = response.get('info').get('0').get('code')
            os.remove(os.path.split(self.blob_path)[0] + '/input_0' + ext)
        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(str(code), '1')

    def test_convert_resize_image_with_crop(self):
        """
        Tests conversion with crop.
        """
        status = None
        code = None
        try:
            ext = '.png'
            input_file = os.path.split(self.blob_path)[0]
            input_desc = [{'description': 'input', 'max_pixels': '1024 * 2000', 'ext': ext,
                           'type': 'image', 'max_weight': 5242880}]
            crop_info = json.dumps({"x":81, "y":9.2, "width":105, "height":79.6, "rotate":0, "scaleX":1, "scaleY":1})
            response = self.convert(input_file, input_desc, crop_info)
            status = response.get('status')
            code = response.get('info').get('0').get('code')
            os.remove(os.path.split(self.blob_path)[0] + '/input_0' + ext)
        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(str(code), '1')

    def test_convert_conversion_needed_but_forbiden(self):
        """
        Tests conversion needed but forbidden.
        """
        status = None
        code = None
        try:
            ext = '.png'
            input_file = os.path.split(self.blob_path)[0]
            input_desc = [{'description': 'input', 'max_pixels': '10 * 9', 'ext': ext,
                           'type': 'image', 'max_weight': 5242880, 'forbid_preprocess': 'true'}]
            response = self.convert(input_file, input_desc, None)
            status = response.get('status')
            code = response.get('info').get('0').get('code')
            os.remove(os.path.split(self.blob_path)[0] + '/input_0' + ext)
        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(str(code), '2')

    def test_convert_conversion_not_needed_and_forbiden(self):
        """
        Tests conversion not needed but forbidden.
        """
        status = None
        code = None
        try:
            ext = '.png'
            input_file = os.path.split(self.blob_path)[0]
            input_desc = [{'description': 'input', 'max_pixels': '1024 * 2000', 'ext': ext,
                           'type': 'image', 'max_weight': 5242880, 'forbid_preprocess': 'true'}]
            response = self.convert(input_file, input_desc, None)
            status = response.get('status')
            code = response.get('info').get('0').get('code')
            os.remove(os.path.split(self.blob_path)[0] + '/input_0' + ext)
        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(str(code), '0')

    #####################
    #       TOOLS       #
    #####################

    def post(self, module, service, params=None, data=None, files=None, servicejson=None):
        """
        Do a post
        """
        url = 'http://{}/api/{}/{}'.format(self.HOST, module, service)
        return requests.post(url, params=params, data=data, files=files, json=servicejson)

    def convert(self, input_file, input_desc, crop_info):
        """
        Calls the convert method in the conversion module
        """
        params = {'work_dir': input_file, 'inputs_description': json.dumps(input_desc), 'crop_info': crop_info}
        response = self.post(self.module, 'convert', params=params)
        return response.json()


if __name__ == '__main__':
    shared_folder = sys.argv.pop()
    demorunners = sys.argv.pop()
    resources_path = sys.argv.pop()
    ConversionTests.blob_path = os.path.join(resources_path, 'test_image.png')
    unittest.main()
