"""
Conversion tests.
"""
import os
import shutil
import tempfile
import pytest

import magic
import numpy as np

import cv2
from ipolutils.image.Image import Image
from ipolutils.video.Video import Video

from conversion.conversion import ConversionStatus, Converter


# used to find test resources in ci_tests/resources/
ROOT = os.path.dirname(os.path.abspath(__file__)) + "/../../../.."


#####################
#       Image       #
#####################

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

def test_tiff_depths():
    """
    Tests the conversions between all supported dtypes in tiff.
    """
    tif_file = tempfile.NamedTemporaryFile(suffix='.tif', prefix="ipol_", delete=True)
    for src_depth in ('8i', '16i', '32i', '16f', '32f'):
        for dst_depth in ('8i', '16i', '32i'): # float as a destination is not strictly equal
            data = data_matrix(src_depth)
            im = Image(data=data)
            im.convert_depth(dst_depth)
            im.write(tif_file.name)

            im = Image(src=tif_file.name)
            data = data_matrix(dst_depth)
            assert im.data.dtype is data.dtype
            assert (im.data == data).all()
    tif_file.close()

def test_8i_extensions():
    """
    Tests the conversions between 8 bits file formats.
    """
    data = data_matrix('8i')
    # gif is not supported by OpenCV, .jpg do not keep exact colors
    exts = {
        '.bmp': 'image/bmp',
        '.png': 'image/png',
        '.tif': 'image/tiff',
        '.TIFF': 'image/tiff',
    }
    for src_ext, src_mime in list(exts.items()):
        src_file = tempfile.NamedTemporaryFile(suffix=src_ext, prefix="ipol_", delete=True)
        src_im = Image(data=data)
        src_im.write(src_file.name)
        assert magic.from_file(src_file.name, mime=True) == src_mime

        src_im = Image(src=src_file.name)
        for dst_ext, dst_mime in list(exts.items()):
            dst_file = tempfile.NamedTemporaryFile(suffix=dst_ext, prefix="ipol_", delete=True)
            src_im.write(dst_file.name) # write to dest should encoding conversion
            assert magic.from_file(dst_file.name, mime=True) == dst_mime

            dst_im = Image(src=dst_file.name)
            assert (src_im.data == dst_im.data).all()
            dst_file.close()

        src_file.close()

@pytest.fixture
def blob_path(tmpdir):
    blob_path = os.path.join(ROOT, 'ci_tests/resources/test_image.png')
    dst = tmpdir / "input_0.png"
    shutil.copy2(blob_path, dst)
    return str(dst)

@pytest.fixture
def converter():
    return Converter()

def test_convert_change_image_ext(blob_path, converter):
    """
    Tests extension conversion.
    """
    dst_ext = '.bmp'
    dst_mime = 'image/bmp'
    src_im = Image(src=blob_path) # image in resource folder should be not jpeg

    input_dir = os.path.split(blob_path)[0]
    input_desc = [{
        'description': 'input',
        'max_pixels': '1024 * 2000',
        'dtype': '3x8i',
        'ext': dst_ext,
        'type': 'image',
        'max_weight': 5242880,
    }]
    crop_info = None
    result = converter.convert(input_dir, input_desc, crop_info)
    assert result.unwrap()[0].code == ConversionStatus.NotNeededOrWithoutLoss

    dst_file = os.path.split(blob_path)[0] + '/input_0' + dst_ext
    assert magic.from_file(dst_file, mime=True) == dst_mime

    dst_im = Image(src=dst_file)
    assert (src_im.data == dst_im.data).all()

def test_convert_image_that_do_not_need_conversion(blob_path, converter):
    """
    Tests to convert image that does not need conversion.
    """
    ext = '.png'
    input_dir = os.path.split(blob_path)[0]
    src_path = input_dir + '/input_0' + ext
    src_size = os.path.getsize(src_path)
    input_desc = [{
        'description': 'input',
        'max_pixels': '1024 * 2000',
        'dtype': '3x8i',
        'ext': ext,
        'type': 'image',
        'max_weight': 5242880,
    }]
    crop_info = None
    result = converter.convert(input_dir, input_desc, crop_info)
    assert result.unwrap()[0].code == ConversionStatus.NotNeededOrWithoutLoss

    dst_size = os.path.getsize(src_path)
    assert src_size == dst_size

def test_convert_resize_image(blob_path, converter):
    """
    Tests to downsize a picture to max_pixels.
    """
    ext = '.png'
    input_dir = os.path.split(blob_path)[0]
    max_pixels = 150
    input_desc = [{
        'description': 'input',
        'max_pixels': max_pixels,
        'dtype': '3x8i',
        'ext': ext,
        'type': 'image',
        'max_weight': 5242880,
    }]
    result = converter.convert(input_dir, input_desc, None)
    assert result.unwrap()[0].code == ConversionStatus.Done

    dst_file = os.path.split(blob_path)[0] + '/input_0' + ext
    dst_im = Image(src=dst_file)
    dst_pixels = dst_im.width() * dst_im.height()
    assert dst_pixels < max_pixels

def test_convert_resize_image_with_crop(blob_path, converter):
    """
    Tests conversion with crop.
    """
    ext = '.png'
    input_dir = os.path.split(blob_path)[0]
    input_desc = [{
        'description': 'input',
        'max_pixels': '1024 * 2000',
        'dtype': '3x8i',
        'ext': ext,
        'type': 'image',
        'max_weight': 5242880,
    }]
    width = 105
    height = 79.6
    crop_info = {
        "x": 81,
        "y": 9.2,
        "width": width,
        "height": height,
        "rotate": 0,
        "scaleX": 1,
        "scaleY": 1,
    }
    result = converter.convert(input_dir, input_desc, crop_info)
    assert result.unwrap()[0].code == ConversionStatus.Done

    dst_file = os.path.split(blob_path)[0] + '/input_0' + ext
    dst_im = Image(src=dst_file)
    assert dst_im.width() == round(width)
    assert dst_im.height() == round(height)

def test_convert_conversion_needed_but_forbiden(blob_path, converter):
    """
    Tests conversion needed but forbidden.
    """
    src_im = Image(src=blob_path) # image in resource folder should be not jpeg
    ext = '.png'
    input_dir = os.path.split(blob_path)[0]
    input_desc = [{
        'description': 'input',
        'max_pixels': '10 * 9',
        'dtype': '3x8i',
        'ext': ext,
        'type': 'image',
        'max_weight': 5242880,
        'forbid_preprocess': 'true',
    }]
    result = converter.convert(input_dir, input_desc, None)
    assert result.unwrap()[0].code == ConversionStatus.NeededButForbidden

    dst_file = os.path.split(blob_path)[0] + '/input_0' + ext
    dst_im = Image(src=dst_file)
    assert (src_im.data == dst_im.data).all()

def test_convert_conversion_not_needed_and_forbiden(blob_path, converter):
    """
    Tests conversion not needed but forbidden.
    """
    src_im = Image(src=blob_path) # image in resource folder should be not jpeg
    ext = '.png'
    input_dir = os.path.split(blob_path)[0]
    input_desc = [{
        'description': 'input',
        'max_pixels': '1024 * 2000',
        'dtype': '3x8i',
        'ext': ext,
        'type': 'image',
        'max_weight': 5242880,
        'forbid_preprocess': 'true',
    }]
    result = converter.convert(input_dir, input_desc, None)
    assert result.unwrap()[0].code == ConversionStatus.NotNeededOrWithoutLoss

    dst_file = os.path.split(blob_path)[0] + '/input_0' + ext
    dst_im = Image(src=dst_file)
    assert (src_im.data == dst_im.data).all()


#####################
#       Video       #
#####################

@pytest.fixture
def video_blob_path(tmpdir):
    blob_path = os.path.join(ROOT, 'ci_tests/resources/test_video.mp4')
    dst = tmpdir / "input_0.mp4"
    shutil.copy2(blob_path, dst)
    return str(dst)

def test_convert_video_to_frames(video_blob_path, converter):
    """
    Tests video conversion to frames. No resize or frame crop needed.
    """
    work_dir = os.path.split(video_blob_path)[0]
    input_desc = [{'description': 'input', 'max_pixels': '15000 * 10000',
                   'type': 'video', 'max_weight': 5242880, 'as_frames': True, 'max_frames': 250}]

    result = converter.convert(work_dir, input_desc, None)
    assert result.unwrap()[0].code == ConversionStatus.NotNeededOrWithoutLoss

    frame_count = len(os.listdir(os.path.split(video_blob_path)[0] + '/input_0'))
    frame = cv2.imread(os.path.split(video_blob_path)[0] + '/input_0/frame_00000.png')
    frame_width, frame_height, _ = frame.shape
    input_video = load_video(work_dir + '/input_0.mp4')
    assert frame_count == input_video["frame_count"]
    assert frame_width * frame_height == input_video["width"] * input_video["height"]

def test_convert_video_to_frames_with_resize(video_blob_path, converter):
    """
    Tests video conversion to frames with resize.
    """
    work_dir = os.path.split(video_blob_path)[0]
    input_desc = [{'description': 'input', 'max_pixels': '150 * 100',
                   'type': 'video', 'max_weight': 5242880, 'as_frames': True, 'max_frames': 500}]

    result = converter.convert(work_dir, input_desc, None)
    assert result.unwrap()[0].code == ConversionStatus.Done

    frame_count = len(os.listdir(os.path.split(video_blob_path)[0] + '/input_0'))
    frame = cv2.imread(os.path.split(video_blob_path)[0] + '/input_0/frame_00000.png')
    frame_width, frame_height, _ = frame.shape
    input_video = load_video(work_dir + '/input_0.mp4')
    assert frame_count == input_video["frame_count"]
    assert frame_width * frame_height <= 150 * 100

def test_convert_video_to_frames_with_max_frames(video_blob_path, converter):
    """
    Tests video conversion to frames with max frames.
    """
    work_dir = os.path.split(video_blob_path)[0]
    input_desc = [{'description': 'input', 'max_pixels': '15000 * 10000',
                   'type': 'video', 'max_weight': 5242880, 'as_frames': True, 'max_frames': 5}]

    result = converter.convert(work_dir, input_desc, None)
    assert result.unwrap()[0].code == ConversionStatus.Done

    frame_count = len(os.listdir(os.path.split(video_blob_path)[0] + '/input_0'))
    frame = cv2.imread(os.path.split(video_blob_path)[0] + '/input_0/frame_00000.png')
    frame_width, frame_height, _ = frame.shape
    input_video = load_video(work_dir + '/input_0.mp4')
    assert frame_count == 5
    assert frame_width * frame_height == input_video["width"] * input_video["height"]

def test_convert_video_to_frames_with_resize_and_max_frames(video_blob_path, converter):
    """
    Tests video conversion to frames with resize and max frames.
    """
    work_dir = os.path.split(video_blob_path)[0]
    input_desc = [{'description': 'input', 'max_pixels': '150 * 100',
                   'type': 'video', 'max_weight': 5242880, 'as_frames': True, 'max_frames': 5}]

    result = converter.convert(work_dir, input_desc, None)
    assert result.unwrap()[0].code == ConversionStatus.Done

    frame_count = len(os.listdir(os.path.split(video_blob_path)[0] + '/input_0'))
    frame = cv2.imread(os.path.split(video_blob_path)[0] + '/input_0/frame_00000.png')
    frame_width, frame_height, _ = frame.shape
    assert frame_count == 5
    assert frame_width * frame_height <= 150 * 100

def test_convert_video_to_avi(video_blob_path, converter):
    """
    Tests video conversion to AVI.
    """
    work_dir = os.path.split(video_blob_path)[0]
    input_desc = [{'description': 'input', 'max_pixels': '15000 * 10000',
                   'type': 'video', 'max_weight': 5242880, 'max_frames': 600}]

    result = converter.convert(work_dir, input_desc, None)
    assert result.unwrap()[0].code == ConversionStatus.NotNeededOrWithoutLoss

    avi_video = load_video(os.path.split(video_blob_path)[0] + '/input_0.avi')
    input_video = load_video(work_dir + '/input_0.mp4')
    assert avi_video["frame_count"] == input_video["frame_count"]
    assert avi_video["width"] * avi_video["height"] == input_video["width"] * input_video["height"]

def test_convert_video_to_avi_with_resize(video_blob_path, converter):
    """
    Tests video conversion to AVI with resize.
    """
    work_dir = os.path.split(video_blob_path)[0]
    input_desc = [{'description': 'input', 'max_pixels': '150 * 100',
                   'type': 'video', 'max_weight': 5242880, 'max_frames': 600}]

    result = converter.convert(work_dir, input_desc, None)
    assert result.unwrap()[0].code == ConversionStatus.Done

    avi_video = load_video(os.path.split(video_blob_path)[0] + '/input_0.avi')
    input_video = load_video(work_dir + '/input_0.mp4')
    assert avi_video["frame_count"] == input_video["frame_count"]
    assert avi_video["width"] * avi_video["height"] <= 150 * 100

def test_convert_video_to_avi_with_max_frames(video_blob_path, converter):
    """
    Tests video conversion to AVI with max frames.
    """
    work_dir = os.path.split(video_blob_path)[0]
    input_desc = [{'description': 'input', 'max_pixels': '15000 * 10000',
                   'type': 'video', 'max_weight': 5242880, 'max_frames': 6}]

    result = converter.convert(work_dir, input_desc, None)
    assert result.unwrap()[0].code == ConversionStatus.Done

    avi_video = load_video(os.path.split(video_blob_path)[0] + '/input_0.avi')
    input_video = load_video(work_dir + '/input_0.mp4')
    assert avi_video["frame_count"] == 6
    assert avi_video["width"] * avi_video["height"] == input_video["width"] * input_video["height"]

def test_convert_video_to_avi_with_resize_and_max_frames(video_blob_path, converter):
    """
    Tests video conversion to AVI with resize and max frames.
    """
    work_dir = os.path.split(video_blob_path)[0]
    input_desc = [{'description': 'input', 'max_pixels': '150 * 100',
                   'type': 'video', 'max_weight': 5242880, 'max_frames': 6}]

    result = converter.convert(work_dir, input_desc, None)
    assert result.unwrap()[0].code == ConversionStatus.Done

    avi_video = load_video(os.path.split(video_blob_path)[0] + '/input_0.avi')
    assert avi_video["frame_count"] == 6
    assert avi_video["width"] * avi_video["height"] <= 150 * 100

def test_get_middle_frame_even(video_blob_path):
    """
    Tests calculate the middle frame when the video frame count is even.
    """
    video = Video(video_blob_path)
    middle_frame = video.get_middle_frame()
    assert middle_frame == 125

def test_get_middle_frame_odd(video_blob_path, converter):
    """
    Tests calculate the middle frame when the video frame count is odd.
    """
    work_dir = os.path.split(video_blob_path)[0]
    input_desc = [{'description': 'input', 'max_pixels': '150 * 100',
                   'type': 'video', 'max_weight': 5242880, 'max_frames': 11}]
    result = converter.convert(work_dir, input_desc, None)
    assert result.unwrap()[0].code == ConversionStatus.Done

    video = Video(os.path.split(video_blob_path)[0] + '/input_0.avi')
    middle_frame = video.get_middle_frame()
    assert middle_frame == 5

def test_get_from_to_frames_from_even_max_frames(video_blob_path):
    """
    Tests calculate the first and last frame to extracts when the max frames is even.
    """
    video = Video(video_blob_path)
    middle_frame = video.get_middle_frame()
    from_frame, to_frame = video.get_from_to_frames(middle_frame, 10)

    assert middle_frame == 125
    assert from_frame == 120
    assert to_frame == 129

def test_get_from_to_frames_from_odd_max_frames(video_blob_path):
    """
    Tests calculate the first and last frame to extracts when the max frames is odd.
    """
    video = Video(video_blob_path)
    middle_frame = video.get_middle_frame()
    from_frame, to_frame = video.get_from_to_frames(middle_frame, 11)

    assert middle_frame == 125
    assert from_frame == 120
    assert to_frame == 130

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
