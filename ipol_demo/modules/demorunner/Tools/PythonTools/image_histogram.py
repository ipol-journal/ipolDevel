#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
compute and save image histograms for a set of images
using the maximum of the first image
histograms are save as the image basename + '_hist.png'
"""

import os
import sys

from PIL import Image, ImageChops, ImageDraw
import numpy


def histogram(im, value_max=None, size=(256, 128), margin=10, padding=3):
    """
    Return an image object displaying the histogram of the input.
    Image mode supported : L, RGB
    """
    if im.mode not in ('L', 'RGB'):
        raise ValueError("Unsuported image mode for histogram computation (mode = {0})".format(im.mode))

    width_border = padding * 2 + 2 + size[0]
    height_border = padding * 2 + 3 + size[1]

    if im.mode == 'L':
        data = im.histogram()
        if not value_max:
            value_max = max(data)
        out = Image.new('L', (width_border, height_border), 255)
        draw = ImageDraw.Draw(out)
        draw_histo(draw, data, 'L', value_max, xy=(padding + 1, padding + 1), size=size, padding=padding)
        del draw
        out.value_max = value_max
        return out

    # polycolor in one frame
    if im.mode == 'RGB':
        data = im.histogram()
        # append gray intensity to data
        im_grey = im.convert("L")
        data += im_grey.histogram()
        if not value_max:
            value_max = max(data)
        out = Image.new('RGB', (width_border, height_border * 4 + margin * 3), (255, 255, 255))
        draw = ImageDraw.Draw(out)
        y = padding + 1
        for channel in ('R', 'G', 'B', 'I'):
            draw_histo(draw, data, channel, value_max, xy=(padding + 1, y), size=size, padding=padding)
            y += margin + height_border
        del draw
        del im
        out.value_max = value_max
        return out

def draw_histo(draw, data, channel, value_max, xy=(0, 0), size=(256, 128), padding=3):
    """
    Draws the histogram of a channel on an image.
    """
    dic = {
        # channel: (data_index, color, color_full, grid)
        'R': {'index': 0, 'color': (255, 0, 0), 'full': (0, 0, 0), 'grid': (192, 192, 192)},
        'G': {'index': 256, 'color': (0, 255, 0), 'full': (0, 0, 0), 'grid': (192, 192, 192)},
        'B': {'index': 512, 'color': (0, 0, 255), 'full': (0, 0, 0), 'grid': (192, 192, 192)},
        'I': {'index': 768, 'color': (128, 128, 128), 'full': (0, 0, 0), 'grid': (192, 192, 192)},
        'L': {'index': 0, 'color': 128, 'full': 0, 'grid': 192}
    }
    for y in (xy[1] + size[1] / 3, xy[1] + 2 * size[1] / 3): # horizontal grid
        draw.line((xy[0], y, xy[0] + size[0] - 1, y), fill=dic[channel]['grid'])
    for x in (xy[0] + size[0] / 3, xy[0] + 2 * size[0] / 3): # vertical grid
        draw.line((x, xy[1], x, xy[1] + size[1]), fill=dic[channel]['grid'])
    draw.rectangle(
        [(xy[0] - padding - 1, xy[1] - padding - 1), (xy[0] + size[0] + padding, xy[1] + size[1] + padding + 1)],
        outline=dic[channel]['full']
    ) # border

    sy = size[1] / float(value_max) # step y
    # loop on all pixelx of width
    for dx in range(0, size[0]):
        # index in data
        i = int(dx*256/float(size[0]))
        value = data[dic[channel]['index']+i]
        x = xy[0] + dx
        if not value:
            continue
        if value > value_max:
            color = dic[channel]['full']
            y2 = xy[1]
        else:
            color = dic[channel]['color']
            y2 = int(round(xy[1] + size[1] - (value * sy)))
        if y2 != xy[1] + size[1]:
            draw.line((x, xy[1] + size[1], x, y2), color)


def pil_4histo(im, bgcolor=(255, 255, 255)):
    """
    Return an image object compatible with histo (ex: resolve transparency…)
    or nothing when it is known that the format is not converted.
    """
    if im.mode == 'L': # should work
        return im
    # Grey with transparency
    if im.mode == 'LA':
        l = im
        bg = int(numpy.round(0.21*bgcolor[0] + 0.72*bgcolor[1] + 0.07*bgcolor[2])) # grey luminosity
        im = Image.new('L', l.size, bg)
        im.paste(l, mask=l.split()[1]) # 1 is the alpha channel
        l.close()
        return im
    # im.info['transparency'], hack from image.py for palette with RGBA
    if im.mode == 'P' and 'transparency' in im.info and im.info['transparency'] is not None:
        im = im.convert('RGBA') # convert Palette with transparency to RGBA, handle just after
    # RGBA, full colors with canal alpha, resolve transparency with a white background
    if im.mode == 'RGBA':
        rgba = im
        im = Image.new('RGB', rgba.size, bgcolor)
        im.paste(rgba, mask=rgba.split()[3]) # 3 is the alpha channel
        rgba.close()
    # test if RGB is a grayscale image (ex JPG)
    if im.mode == 'RGB':
        # find a non grey pixel as fast as possible, on a diagonal
        diag = min(im.width, im.height)
        for i in range(0, diag):
            color = sorted(im.getpixel((i, i)))
            if color[0] != color[-1]:
                return im
        # full comparison of pixels
        rgb = im.split()
        if ImageChops.difference(rgb[0], rgb[1]).getextrema()[1] != 0:
            return im
        if ImageChops.difference(rgb[0], rgb[2]).getextrema()[1] != 0:
            return im
        return im.convert('L')
    # last try
    im = im.convert('RGB')
    return im

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Histogram, need at least one input image to process")
        sys.exit(0)
    # loop on argument, set max size of histogram for first image
    value_max = None
    for src in sys.argv[1:]:
        print(src)
        im = Image.open(src)
        im = pil_4histo(im) # ensure rgb or l
        hist = histogram(im, value_max=value_max)
        # get max value of first image, returned as a field
        if not value_max:
            value_max = hist.value_max
        hist.save(os.path.splitext(src)[0]+'_hist.png')
