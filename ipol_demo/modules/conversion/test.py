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
import cv2
import requests
import magic
import numpy as np
from ipolutils.image.Image import Image
from ipolutils.video.Video import Video


#####################
#       Image       #
#####################
class ConversionImageTests(unittest.TestCase):
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
    def data_matrix(depth):
        """
        Creates a standard image matrix for tests.
        """
        dtype = Image.DEPTH_DTYPE[depth]
        if np.issubdtype(dtype, np.integer):
            dtype_max = np.iinfo(dtype).max
        else:
            dtype_max = 1
        data = np.zeros((32, 48, 3), dtype=dtype)
        data[0:16, :, 0] = dtype_max
        data[:, 0:32, 1] = dtype_max
        data[:, 0:16, 2] = dtype_max
        return data

    def test_tiff_depths(self):
        """
        Tests the conversions between all supported dtypes in tiff.
        """
        tif_file = tempfile.NamedTemporaryFile(suffix='.tif', prefix="ipol_", delete=True)
        for src_depth in ('8i', '16i', '32i', '16f', '32f'):
            for dst_depth in ('8i', '16i', '32i'): # float as a destination is not strictly equal
                data = self.data_matrix(src_depth)
                im = Image.data(data)
                im.convert_depth(dst_depth)
                im.write(tif_file.name)

                im = Image.load(tif_file.name)
                data = self.data_matrix(dst_depth)
                self.assertTrue(
                    im.data.dtype is data.dtype,
                    msg="dtype expected={} found={}, conversion failed {} > {}".format(
                        data.dtype, im.data.dtype, src_depth, dst_depth
                    )
                )
                self.assertTrue((im.data == data).all(), msg="data alteration during conversion {} > {}".format(src_depth, dst_depth))
        tif_file.close()


    def test_8i_extensions(self):
        """
        Tests the conversions between 8 bits file formats.
        """
        data = self.data_matrix('8i')
        # gif is not supported by OpenCV, .jpg do not keep exact colors
        exts = {
            '.bmp': 'image/x-ms-bmp',
            '.png': 'image/png',
            '.tif': 'image/tiff',
            '.TIFF': 'image/tiff',
        }
        for src_ext, src_mime in exts.iteritems():
            src_file = tempfile.NamedTemporaryFile(suffix=src_ext, prefix="ipol_", delete=True)
            src_im = Image.data(data)
            src_im.write(src_file.name)
            self.assertTrue(
                magic.from_file(src_file.name, mime=True) == src_mime,
                msg="Bad file encoding, {} is not {}".format(src_file.name, src_mime)
            )
            src_im = Image.load(src_file.name)
            for dst_ext, dst_mime in exts.iteritems():
                dst_file = tempfile.NamedTemporaryFile(suffix=dst_ext, prefix="ipol_", delete=True)
                src_im.write(dst_file.name) # write to dest should encoding conversion
                self.assertTrue(
                    magic.from_file(dst_file.name, mime=True) == dst_mime,
                    msg="Bad file encoding, {} is not {}".format(dst_file.name, dst_mime)
                )
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
            dst_ext = '.bmp'
            dst_mime = 'image/x-ms-bmp'
            input_dir = os.path.split(self.blob_path)[0]
            src_im = Image.load(self.blob_path) # image in resource folder should be not jpeg
            input_desc = [{'description': 'input', 'max_pixels': '1024 * 2000', 'dtype': '3x8i', 'ext': dst_ext,
                           'type': 'image', 'max_weight': 5242880}]
            crop_info = None
            response = self.convert(input_dir, input_desc, crop_info)
            status = response.get('status')
            code = response.get('info').get('0').get('code')
            dst_file = os.path.split(self.blob_path)[0] + '/input_0' + dst_ext
            good_mime = (magic.from_file(dst_file, mime=True) == dst_mime)
            dst_im = Image.load(dst_file)
            os.remove(dst_file)
        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(str(code), '0')
            self.assertTrue(good_mime, msg="Bad file encoding, {} is not {}".format(dst_file, dst_mime))
            self.assertTrue((src_im.data == dst_im.data).all(), msg="Changing image extension has change the data.")

    def test_convert_image_that_do_not_need_conversion(self):
        """
        Tests to convert image that does not need conversion.
        """
        status = None
        code = None
        try:
            ext = '.png'
            input_dir = os.path.split(self.blob_path)[0]
            src_path = input_dir + '/input_0' + ext
            src_size = os.path.getsize(src_path)
            input_desc = [{'description': 'input', 'max_pixels': '1024 * 2000', 'dtype': '3x8i', 'ext': ext,
                           'type': 'image', 'max_weight': 5242880}]
            crop_info = None
            response = self.convert(input_dir, input_desc, crop_info)
            status = response.get('status')
            code = response.get('info').get('0').get('code')
            dst_size = os.path.getsize(src_path)
            os.remove(src_path)
        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(str(code), '0')
            self.assertEqual(src_size, dst_size, msg="{} != {}, file have been modified")

    def test_convert_resize_image(self):
        """
        Tests to downsize a picture to max_pixels.
        """
        status = None
        code = None
        try:
            ext = '.png'
            input_dir = os.path.split(self.blob_path)[0]
            max_pixels = 150
            input_desc = [{'description': 'input', 'max_pixels': max_pixels, 'dtype': '3x8i', 'ext': ext,
                           'type': 'image', 'max_weight': 5242880}]
            response = self.convert(input_dir, input_desc, None)
            status = response.get('status')
            code = response.get('info').get('0').get('code')
            dst_file = os.path.split(self.blob_path)[0] + '/input_0' + ext
            dst_im = Image.load(dst_file)
            dst_pixels = dst_im.width() * dst_im.height()
            os.remove(dst_file)
        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(str(code), '1')
            self.assertTrue(dst_pixels < max_pixels, msg="Input image has not be reduced under max_pixels {} >= {}".format(dst_pixels, max_pixels))

    def test_convert_resize_image_with_crop(self):
        """
        Tests conversion with crop.
        """
        status = None
        code = None
        try:
            ext = '.png'
            input_dir = os.path.split(self.blob_path)[0]
            input_desc = [{'description': 'input', 'max_pixels': '1024 * 2000', 'dtype': '3x8i', 'ext': ext,
                           'type': 'image', 'max_weight': 5242880}]
            width = 105
            height = 79.6
            crop_info = json.dumps({"x":81, "y":9.2, "width": width, "height": height, "rotate":0, "scaleX":1, "scaleY":1})
            response = self.convert(input_dir, input_desc, crop_info)
            status = response.get('status')
            code = response.get('info').get('0').get('code')
            dst_file = os.path.split(self.blob_path)[0] + '/input_0' + ext
            dst_im = Image.load(dst_file)
            os.remove(dst_file)
        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(str(code), '1')
            self.assertTrue(
                dst_im.width() == round(width) and dst_im.height() == round(height),
                msg="Input image {}x{} has not be cropped to {}x{}".format(dst_im.width(), dst_im.height(), width, height)
            )

    def test_convert_conversion_needed_but_forbiden(self):
        """
        Tests conversion needed but forbidden.
        """
        status = None
        code = None
        try:
            src_im = Image.load(self.blob_path) # image in resource folder should be not jpeg
            ext = '.png'
            input_dir = os.path.split(self.blob_path)[0]
            input_desc = [{'description': 'input', 'max_pixels': '10 * 9', 'dtype': '3x8i', 'ext': ext,
                           'type': 'image', 'max_weight': 5242880, 'forbid_preprocess': 'true'}]
            response = self.convert(input_dir, input_desc, None)
            status = response.get('status')
            code = response.get('info').get('0').get('code')
            dst_file = os.path.split(self.blob_path)[0] + '/input_0' + ext
            dst_im = Image.load(dst_file)
            os.remove(dst_file)
        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(str(code), '2')
            self.assertTrue((src_im.data == dst_im.data).all(), msg="Preprocess is forbidden but the image data have been modified.")

    def test_convert_conversion_not_needed_and_forbiden(self):
        """
        Tests conversion not needed but forbidden.
        """
        status = None
        code = None
        try:
            src_im = Image.load(self.blob_path) # image in resource folder should be not jpeg
            ext = '.png'
            input_dir = os.path.split(self.blob_path)[0]
            input_desc = [{'description': 'input', 'max_pixels': '1024 * 2000', 'dtype': '3x8i', 'ext': ext,
                           'type': 'image', 'max_weight': 5242880, 'forbid_preprocess': 'true'}]
            response = self.convert(input_dir, input_desc, None)
            status = response.get('status')
            code = response.get('info').get('0').get('code')
            dst_file = os.path.split(self.blob_path)[0] + '/input_0' + ext
            dst_im = Image.load(dst_file)
            os.remove(dst_file)
        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(str(code), '0')
            self.assertTrue((src_im.data == dst_im.data).all(), msg="Preprocess is forbidden but the image data have been modified.")

    ####################
    #      TOOLS       #
    ####################

    def post(self, module, service, params=None, data=None, files=None, servicejson=None):
        """
        Do a post
        """
        url = 'http://{}/api/{}/{}'.format(self.HOST, module, service)
        return requests.post(url, params=params, data=data, files=files, json=servicejson)

    def convert(self, input_dir, input_desc, crop_info):
        """
        Calls the convert method in the conversion module
        """
        params = {'work_dir': input_dir, 'inputs_description': json.dumps(input_desc), 'crop_info': crop_info}
        response = self.post(self.module, 'convert', params=params)
        return response.json()

#####################
#       Video       #
#####################
class ConversionVideoTests(unittest.TestCase):
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
        Creates a copy of the video before convert it.
        """
        try:
            copy_video = os.path.split(self.video_blob_path)[0] + '/input_0' + os.path.splitext(self.video_blob_path)[1]
            shutil.copy2(self.video_blob_path, copy_video)
        except Exception:
            pass

    def tearDown(self):
        """
        Restores the copy of the video.
        """
        try:
            copy_video = os.path.split(self.video_blob_path)[0] + '/input_0' + os.path.splitext(self.video_blob_path)[1]
            os.remove(copy_video)
        except Exception:
            pass

    def test_convert_video_to_frames(self):
        """
        Tests video conversion to frames. No resize or frame crop needed.
        """
        status = None
        code = None
        try:
            work_dir = os.path.split(self.video_blob_path)[0]
            input_desc = [{'description': 'input', 'max_pixels': '15000 * 10000',
                           'type': 'video', 'max_weight': 5242880, 'as_frames': True, 'max_frames': 250}]

            response = self.convert(work_dir, input_desc, None)
            status = response.get('status')
            code = response.get('info').get('0').get('code')[0]

            frame_count = len(os.listdir(os.path.split(self.video_blob_path)[0] + '/input_0'))
            frame = cv2.imread(os.path.split(self.video_blob_path)[0] + '/input_0/frame_00000.png')
            frame_width, frame_height, _ = frame.shape
            input_video = ConversionVideoTests.load_video(work_dir + '/input_0.mp4')
        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(str(code), '0')
            self.assertEqual(frame_count, input_video["frame_count"])
            self.assertEqual(frame_width * frame_height, input_video["width"] * input_video["height"])
            shutil.rmtree(os.path.split(self.video_blob_path)[0] + '/input_0')

    def test_convert_video_to_frames_with_resize(self):
        """
        Tests video conversion to frames with resize.
        """
        status = None
        code = None
        try:
            work_dir = os.path.split(self.video_blob_path)[0]
            input_desc = [{'description': 'input', 'max_pixels': '150 * 100',
                           'type': 'video', 'max_weight': 5242880, 'as_frames': True, 'max_frames': 500}]

            response = self.convert(work_dir, input_desc, None)
            status = response.get('status')
            code = response.get('info').get('0').get('code')[0]

            frame_count = len(os.listdir(os.path.split(self.video_blob_path)[0] + '/input_0'))
            frame = cv2.imread(os.path.split(self.video_blob_path)[0] + '/input_0/frame_00000.png')
            frame_width, frame_height, _ = frame.shape
            input_video = ConversionVideoTests.load_video(work_dir + '/input_0.mp4')
        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(str(code), '1')
            self.assertEqual(frame_count, input_video["frame_count"])
            self.assertLessEqual(frame_width * frame_height, 150 * 100)
            shutil.rmtree(os.path.split(self.video_blob_path)[0] + '/input_0')

    def test_convert_video_to_frames_with_max_frames(self):
        """
        Tests video conversion to frames with max frames.
        """
        status = None
        code = None
        try:
            work_dir = os.path.split(self.video_blob_path)[0]
            input_desc = [{'description': 'input', 'max_pixels': '15000 * 10000',
                           'type': 'video', 'max_weight': 5242880, 'as_frames': True, 'max_frames': 5}]

            response = self.convert(work_dir, input_desc, None)
            status = response.get('status')
            code = response.get('info').get('0').get('code')[0]

            frame_count = len(os.listdir(os.path.split(self.video_blob_path)[0] + '/input_0'))
            frame = cv2.imread(os.path.split(self.video_blob_path)[0] + '/input_0/frame_00000.png')
            frame_width, frame_height, _ = frame.shape
            input_video = ConversionVideoTests.load_video(work_dir + '/input_0.mp4')
        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(str(code), '1')
            self.assertEqual(frame_count, 5)
            self.assertEqual(frame_width * frame_height, input_video["width"] * input_video["height"])
            shutil.rmtree(os.path.split(self.video_blob_path)[0] + '/input_0')

    def test_convert_video_to_frames_with_resize_and_max_frames(self):
        """
        Tests video conversion to frames with resize and max frames.
        """
        status = None
        code = None
        try:
            work_dir = os.path.split(self.video_blob_path)[0]
            input_desc = [{'description': 'input', 'max_pixels': '150 * 100',
                           'type': 'video', 'max_weight': 5242880, 'as_frames': True, 'max_frames': 5}]

            response = self.convert(work_dir, input_desc, None)
            status = response.get('status')
            code = response.get('info').get('0').get('code')[0]

            frame_count = len(os.listdir(os.path.split(self.video_blob_path)[0] + '/input_0'))
            frame = cv2.imread(os.path.split(self.video_blob_path)[0] + '/input_0/frame_00000.png')
            frame_width, frame_height, _ = frame.shape
        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(str(code), '1')
            self.assertEqual(frame_count, 5)
            self.assertLessEqual(frame_width * frame_height, 150 * 100)
            shutil.rmtree(os.path.split(self.video_blob_path)[0] + '/input_0')

    def test_convert_video_to_avi(self):
        """
        Tests video conversion to AVI.
        """
        status = None
        code = None
        try:
            work_dir = os.path.split(self.video_blob_path)[0]
            input_desc = [{'description': 'input', 'max_pixels': '15000 * 10000',
                           'type': 'video', 'max_weight': 5242880, 'max_frames': 600}]

            response = self.convert(work_dir, input_desc, None)
            status = response.get('status')
            code = response.get('info').get('0').get('code')[0]

            avi_video = ConversionVideoTests.load_video(os.path.split(self.video_blob_path)[0] + '/input_0.avi')
            input_video = ConversionVideoTests.load_video(work_dir + '/input_0.mp4')
        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(str(code), '0')
            self.assertEqual(avi_video["frame_count"], input_video["frame_count"])
            self.assertEqual(avi_video["width"] * avi_video["height"], input_video["width"] * input_video["height"])
            os.remove(os.path.split(self.video_blob_path)[0] + '/input_0.avi')

    def test_convert_video_to_avi_with_resize(self):
        """
        Tests video conversion to AVI with resize.
        """
        status = None
        code = None
        try:
            work_dir = os.path.split(self.video_blob_path)[0]
            input_desc = [{'description': 'input', 'max_pixels': '150 * 100',
                           'type': 'video', 'max_weight': 5242880, 'max_frames': 600}]

            response = self.convert(work_dir, input_desc, None)
            status = response.get('status')
            code = response.get('info').get('0').get('code')[0]

            avi_video = ConversionVideoTests.load_video(os.path.split(self.video_blob_path)[0] + '/input_0.avi')
            input_video = ConversionVideoTests.load_video(work_dir + '/input_0.mp4')
        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(str(code), '1')
            self.assertEqual(avi_video["frame_count"], input_video["frame_count"])
            self.assertLessEqual(avi_video["width"] * avi_video["height"], 150 * 100)
            os.remove(os.path.split(self.video_blob_path)[0] + '/input_0.avi')

    def test_convert_video_to_avi_with_max_frames(self):
        """
        Tests video conversion to AVI with max frames.
        """
        status = None
        code = None
        try:
            work_dir = os.path.split(self.video_blob_path)[0]
            input_desc = [{'description': 'input', 'max_pixels': '15000 * 10000',
                           'type': 'video', 'max_weight': 5242880, 'max_frames': 6}]

            response = self.convert(work_dir, input_desc, None)
            status = response.get('status')
            code = response.get('info').get('0').get('code')[0]

            avi_video = ConversionVideoTests.load_video(os.path.split(self.video_blob_path)[0] + '/input_0.avi')
            input_video = ConversionVideoTests.load_video(work_dir + '/input_0.mp4')
        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(str(code), '1')
            self.assertEqual(avi_video["frame_count"], 6)
            self.assertEqual(avi_video["width"] * avi_video["height"], input_video["width"] * input_video["height"])
            os.remove(os.path.split(self.video_blob_path)[0] + '/input_0.avi')

    def test_convert_video_to_avi_with_resize_and_max_frames(self):
        """
        Tests video conversion to AVI with resize and max frames.
        """
        status = None
        code = None
        try:
            work_dir = os.path.split(self.video_blob_path)[0]
            input_desc = [{'description': 'input', 'max_pixels': '150 * 100',
                           'type': 'video', 'max_weight': 5242880, 'max_frames': 6}]

            response = self.convert(work_dir, input_desc, None)
            status = response.get('status')
            code = response.get('info').get('0').get('code')[0]

            avi_video = ConversionVideoTests.load_video(os.path.split(self.video_blob_path)[0] + '/input_0.avi')
        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(str(code), '1')
            self.assertEqual(avi_video["frame_count"], 6)
            self.assertLessEqual(avi_video["width"] * avi_video["height"], 150 * 100)
            os.remove(os.path.split(self.video_blob_path)[0] + '/input_0.avi')


    def test_negative_max_frames_as_avi(self):
        """
        Tests negative max_frames when convert to AVI.
        """
        status = None
        try:
            work_dir = os.path.split(self.video_blob_path)[0]
            input_desc = [{'description': 'input', 'max_pixels': '150 * 100',
                           'type': 'video', 'max_weight': 5242880, 'max_frames': -1}]
            response = self.convert(work_dir, input_desc, None)
            status = response.get('status')
        finally:
            self.assertEqual(status, 'KO')

    def test_negative_max_frames_as_frames(self):
        """
        Tests negative max_frames when convert to frames.
        """
        status = None
        try:
            work_dir = os.path.split(self.video_blob_path)[0]
            input_desc = [{'description': 'input', 'max_pixels': '150 * 100',
                           'type': 'video', 'max_weight': 5242880, 'as_frames': True, 'max_frames': -1}]
            response = self.convert(work_dir, input_desc, None)
            status = response.get('status')
        finally:
            self.assertEqual(status, 'KO')

    def test_float_max_frames_as_frames(self):
        """
        Tests float max_frames value when convert to frames.
        """
        status = None
        try:
            work_dir = os.path.split(self.video_blob_path)[0]
            input_desc = [{'description': 'input', 'max_pixels': '150 * 100',
                           'type': 'video', 'max_weight': 5242880, 'as_frames': True, 'max_frames': 2.5}]
            response = self.convert(work_dir, input_desc, None)
            status = response.get('status')
        finally:
            self.assertEqual(status, 'KO')

    def test_float_max_frames_as_avi(self):
        """
        Tests float max_frames value when convert to AVI.
        """
        status = None
        try:
            work_dir = os.path.split(self.video_blob_path)[0]
            input_desc = [{'description': 'input', 'max_pixels': '150 * 100',
                           'type': 'video', 'max_weight': 5242880, 'max_frames': 2.5}]
            response = self.convert(work_dir, input_desc, None)
            status = response.get('status')
        finally:
            self.assertEqual(status, 'KO')

    def test_get_middle_frame_even(self):
        """
        Tests calculate the middle frame when the video frame count is even.
        """
        try:
            video = Video(self.video_blob_path)
            middle_frame = video.get_middle_frame()
        finally:
            self.assertEqual(middle_frame, 125)

    def test_get_middle_frame_odd(self):
        """
        Tests calculate the middle frame when the video frame count is odd.
        """
        try:
            work_dir = os.path.split(self.video_blob_path)[0]
            input_desc = [{'description': 'input', 'max_pixels': '150 * 100',
                           'type': 'video', 'max_weight': 5242880, 'max_frames': 11}]
            response = self.convert(work_dir, input_desc, None)
            status = response.get('status')

            video = Video(os.path.split(self.video_blob_path)[0] + '/input_0.avi')
            middle_frame = video.get_middle_frame()
        finally:
            self.assertEqual(status, 'OK')
            self.assertEqual(middle_frame, 5)
            os.remove(os.path.split(self.video_blob_path)[0] + '/input_0.avi')

    def test_get_from_to_frames_from_even_max_frames(self):
        """
        Tests calculate the first and last frame to extracts when the max frames is even.
        """
        try:
            video = Video(self.video_blob_path)
            middle_frame = video.get_middle_frame()
            from_frame, to_frame = video.get_from_to_frames(middle_frame, 10)
        finally:
            self.assertEqual(middle_frame, 125)
            self.assertEqual(from_frame, 120)
            self.assertEqual(to_frame, 129)

    def test_get_from_to_frames_from_odd_max_frames(self):
        """
        Tests calculate the first and last frame to extracts when the max frames is odd.
        """
        try:
            video = Video(self.video_blob_path)
            middle_frame = video.get_middle_frame()
            from_frame, to_frame = video.get_from_to_frames(middle_frame, 11)
        finally:
            self.assertEqual(middle_frame, 125)
            self.assertEqual(from_frame, 120)
            self.assertEqual(to_frame, 130)


    ###################
    ##      TOOLS    ##
    ###################

    def post(self, module, service, params=None, data=None, files=None, servicejson=None):
        """
        Do a post
        """
        url = 'http://{}/api/{}/{}'.format(self.HOST, module, service)
        return requests.post(url, params=params, data=data, files=files, json=servicejson)

    def convert(self, work_dir, input_desc, crop_info):
        """
        Calls the convert method in the conversion module
        """
        params = {'work_dir': work_dir, 'inputs_description': json.dumps(
            input_desc), 'crop_info': crop_info}
        response = self.post(self.module, 'convert', params=params)
        return response.json()

    @staticmethod
    def load_video(src):
        """
        Return video properties for tests (frame_count, width, height).
        """
        capture = cv2.VideoCapture(src)
        capture.set(cv2.CAP_PROP_POS_FRAMES, 0)

        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

        return {"frame_count": frame_count, "width": width, "height": height}

if __name__ == '__main__':
    shared_folder = sys.argv.pop()
    demorunners = sys.argv.pop()
    resources_path = sys.argv.pop()
    ConversionImageTests.blob_path = os.path.join(resources_path, 'test_image.png')
    ConversionVideoTests.video_blob_path = os.path.join(resources_path, 'test_video.mp4')
    unittest.main()
