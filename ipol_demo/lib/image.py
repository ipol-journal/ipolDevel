"""
image tools
"""

#
# IMAGE THUMBNAILER
#

import os.path
import PIL.Image
import PIL.ImageOps
import PIL.ImageDraw

import subprocess

def _deinterlace_png(path):
    """
    PIL 1.6 can't handle interlaced PNG
    temporary workaround, fixed in PIL 1.7
    """
    im = PIL.Image.open(path)
    if im.format == 'PNG':
        try:
            im.getpixel((0, 0))
        except IOError:
            # check the file exists
            assert os.path.isfile(path)
            # convert it to non-interlaced
            os.system("/usr/bin/convert %s %s"
                      % (path, path))
            im = PIL.Image.open(path)
            # try once again, in case there is another problem
            im.getpixel((0, 0))
    return

# This function is kept here for information but not used; we prefer
# to run the optimizations on all the files (thumbnails and full-size)
# via cron
def _optimize_png(fname):
    """
    Try to compress a png image with optipng.

    The returned compress can be ignored to let the optimization run
    in background. If optipng is not on the system, this will fail
    without touching the file and will not disturb the program
    execution.
    """

    # We use a temporary outfile because optipng (version 0.6.5) is
    # not atomic. UNIX mv is atomic, so this file strategy ensures we
    # always have a valid file.
    # This implies a shell and "&&" because we don't want to wait for
    # the end of the process. If optipng is not on the machine, the
    # shell fails but sends no exception.
    #
    # With an atomic optipng (feature request sent 2011-02-25), we
    # could do:
    # try:
    #     p = subprocess.Popen(["optipng", "-q", "-o2",
    #                           os.path.basename(fname)],
    #                          cwd=os.path.dirname(fname),
    #                          stdout=subprocess.PIPE,
    #                          stderr=subprocess.STDOUT)
    # except OSError:
    #     p = None
    # return p

    cmdline = ("optipng -o 2 -out %(tmpfile)s %(infile)s"
               + " && mv -f %(tmpfile)s %(infile)s") \
               % {'infile': os.path.basename(fname),
                  'tmpfile': os.path.basename(fname) + ".tmp"}
    p = subprocess.Popen(cmdline, shell=True,
                         cwd=os.path.dirname(fname),
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p

def thumbnail(fname, size=(128, 128), ext=".png"):
    """
    image thumbnailing function

    @param fname: full-size file name
    @param size: thumbnail size, default 128x128
    @param ext: thumbnail file extension (and format), default ".png"

    @return: thumbnail file name
    """
    fname = os.path.abspath(fname)
    # split dirname and basename
    (fname_dir, fname_base) = os.path.split(fname)
    fname_noext = os.path.splitext(fname_base)[0]

    tn_fname = os.path.join(fname_dir, ".__%ix%i__" % size
                           + fname_noext + ext)
    if not os.path.isfile(tn_fname):
        # no thumbnail, create it
        #TODO: no more deinterlacing
        _deinterlace_png(fname)
        im = PIL.Image.open(fname)
        tn = PIL.Image.new('RGBA', size, (0, 0, 0, 0))
        im.thumbnail(size, resample=True)
        offset = ((size[0] - im.size[0]) / 2,
                  (size[1] - im.size[1]) / 2)
        box = offset + (im.size[0] + offset[0],
                        im.size[1] + offset[1])
        tn.paste(im, box)
        tn.save(tn_fname)

    return tn_fname

def drawhistogram(imout, h, ymax, ymin, scaleH, color):
    """
    draws in imout the histogram values stored in h
    """
    draw = PIL.ImageDraw.Draw(imout)
    for x in range(0, 256):
        if (ymax-int(h[x] * scaleH)) < ymin:
            #saturated value
            draw.line([(x, ymax),
                       (x, ymin)],
                       fill=0)
        else:
            draw.line([(x, ymax),
                       (x, ymax-int(h[x] * scaleH))],
                       fill=color)
    del draw

#
# IMAGE CLASS
#

class image(object):
    """
    manipulable image object

    This class is basically a PIL abstraction, with a different
    method model: each method is an action modifying the object.
    Nothing is written to a file until explicitly asked.
    """

    im = None

    def __init__(self, src=None):
        """
        initialize an image from a file

        @param src: origin image, can be
          - a string : it is read as an image file name
          - a  PIL image object : it is used as the internal image structure
          - omitted : the image is initialy empty
        """
        if isinstance(src, PIL.Image.Image):
            self.im = src
        if isinstance(src, basestring):
            _deinterlace_png(src)
            self.im = PIL.Image.open(src)

    def __getattr__(self, attr):
        """
        direct access to some image attributes
        """
        if attr == 'size':
            return self.im.size
        else:
            return object.__getattribute__(self, attr)

    def save(self, fname):
        """
        save the image file

        @param fname: file name
        """
        # TODO handle optional arguments
        # TODO handle external TIFF compression
        self.im.save(fname)
        return fname

    def crop(self, box):
        """
        crop the image, in-place

        @param box: crop coordinates (x0, y0, x1, x1)
        """
        self.im = self.im.crop(box)
        return self

    def resize(self, size, method="bicubic"):
        """
        resize the image, in-place

        @param size: target size, given as an integer number of pixels,
               a float scale ratio, or a pair (width, height)
        @param method: interpolation method, can be "nearest",
               "bilinear", "bicubic", "antialias" or "pixeldup"
        """
        if isinstance(size, int):
            # size is a number of pixels -> convert to a float scale
            size = (float(size) / (self.im.size[0] * self.im.size[1])) ** .5

        if isinstance(size, float):
            # size is a scale -> convert to (x, y)
            size = (int(self.im.size[0] * size),
                    int(self.im.size[1] * size))

        try:
            method_kw = {"nearest" : PIL.Image.NEAREST,
                         "bilinear" : PIL.Image.BILINEAR,
                         "bicubic" : PIL.Image.BICUBIC,
                         "antialias" : PIL.Image.ANTIALIAS,
                         "pixeldup" : None}[method]
        except KeyError:
            raise KeyError("method must be 'nearest', 'bilinear',"
                           + " 'bicubic', 'antialias' or 'pixeldup'")

        if method == "pixeldup":
            # rescaling by pixel duplication
            # PIL "nearest" filter is buggy
            # http://mail.python.org/pipermail/image-sig/2011-March/006699.html
            if size == self.im.size:
                # no resize needed
                pass
            else:
                # scaling ratio
                if not (size[0] >= self.im.size[0] and
                        size[0] % self.im.size[0] == 0 and
                        size[1] >= self.im.size[1] and
                        size[1] % self.im.size[1] == 0):
                    raise ValueError('the scale factor must be'
                                     + ' a positive integer number')
                # scaling ratio
                rX = size[0] // self.im.size[0]
                rY = size[1] // self.im.size[1]
                # create a new image
                imout = PIL.Image.new(self.im.mode, size)
                pix = self.im.load()
                pixout = imout.load()
                # duplicate the pixels
                for y in range(0, size[1]):
                    for x in range(0, size[0]):
                        pixout[x, y] = pix[x//rX, y//rY]
                self.im = imout
        else:
            # use resize function from PIL.Image class
            self.im = self.im.resize(size, method_kw)

        return self

    def convert(self, mode):
        """
        convert the image pixel array to another numeric type

        @param mode: the data type, can be '1x8i' (8bit gray) or '3x8i'
        (RGB)
        """
        # TODO handle other modes (binary, 16bits, 32bits int/float)
        # TODO rename param to dtype
        try:
            mode_kw = {'1x8i' : 'L',
                       '3x8i' : 'RGB'}[mode]
        except KeyError:
            raise KeyError('mode must be "1x8i" or "3x8i"')
        self.im = self.im.convert(mode_kw)
        return self

    def split(self, nb, margin=0, fname=None):
        """
        split an image vertically into tiles tiles,
        with an optional margin

        @param nb: number of strips
        @param margin: overlapping margin, default 0

        @return: list of images if fname is not specified,
        or a list of filenames where these images are saved
        """
        # TODO refactor, don't automatically save

        assert nb >= 2

        xmax, ymax = self.im.size
        dy = float(ymax) / nb

        # list of the crop boxes
        boxes = [(0, 0, xmax, int(dy) + margin)]
        boxes += [(0, int(n * dy) - margin, xmax, int((n + 1) * dy) + margin)
                 for n in range(1, nb - 1)]
        boxes += [(0, int((nb - 1) * dy) - margin, xmax, ymax)]

        # cut the image
        tiles = [image(self.im.crop(box)) for box in boxes]

        if not fname:
            return tiles
        else:
            basename, ext = os.path.splitext(fname)
            return [tiles[i].save(basename + ".__%0.2i__" % i + ext)
                    for i in range(len(tiles))]

    def join(self, tiles, margin=0):
        """
        read some tiles and join them vertically

        @param tiles: a list of images
        @param margin: overlapping margin, default 0
        """
        # compute the full image size
        xmax = tiles[0].im.size[0]
        ymax = 0
        for tile in tiles:
            assert tile.im.size[0] == xmax
            ymax += tile.im.size[1] - 2 * margin
        ymax += 2 * margin

        self.im = PIL.Image.new(tiles[0].im.mode, (xmax, ymax))

        # join the images
        ystart = 0
        tile = tiles[0].im
        dy = tile.size[1] - margin
        self.im.paste(tile.crop((0, 0, xmax, dy)), (0, ystart))
        ystart += dy
        for tile in tiles[1:-1]:
            tile = tile.im
            dy = tile.size[1] - 2 * margin
            self.im.paste(tile.crop((0, margin, xmax, dy + margin)),
                          (0, ystart))
            ystart += dy
        tile = tiles[-1].im
        dy = tile.size[1] - margin
        self.im.paste(tile.crop((0, margin, xmax, dy + margin)),
                      (0, ystart))

        return self

    def draw_line(self, coords, color="white"):
        """
        draw a line in an image

        @param coords: a list of coordinates [(x1,y1), (x2,y2), ...]
        @param color: an optional color code, following PIL syntax[1],
        default white
        @return: the image object

        [1]http://www.pythonware.com/library/pil/handbook/imagedraw.htm
        """
        draw = PIL.ImageDraw.Draw(self.im)
        draw.line(coords, fill=color)
        del draw
        return self

    def draw_grid(self, step, offset=(0, 0), color="white"):
        """
        draw a grid on the input image

        @param step: the grid step
        @param offset: the grid offset
        @param color: the grid color
        @return: the image object
        """
        assert step > 0
        # vertical lines
        y = self.im.size[1]
        for x in range(offset[0], self.im.size[0], step):
            self.draw_line(((x, 0), (x, y)), color)
        # horizontal lines
        x = self.im.size[0]
        for y in range(offset[1], self.im.size[1], step):
            self.draw_line(((0, y), (x, y)), color)
        return self

    def draw_cross(self, position, size=2, color="white"):
        """
        draw a cross on the input image

        @param position: the cross center position
        @param size: the cross size (length of each branch)
        @param color: the grid color
        @return: the image object
        """
        assert size >= 0
        (x, y) = position
        # vertical line
        self.draw_line(((x, y - size), (x, y + size)), color=color)
        # horizontal
        self.draw_line(((x - size, y), (x + size, y)), color=color)
        return self

    def invert(self):
        """
        invert the image colors
        @return: the inverted image object
        """
        self.im = PIL.ImageOps.invert(self.im)
        return self

    def max_histogram(self, option="all"):
        """
        returns the maximum value of the histogram of image values,
        only for '1x8i' (8bit gray) or '3x8i' (RGB) modes

        @param option: "R" histogram of R values, "G" histogram of G values,
                       "B" histogram of B values, "I" histogram of I values,
                       "all" histograms of R, G, B and I values
        """

        # constant values
        offsetH = {"R":0, "G":256, "B":512, "I":768}
        rgb2I = (
            0.333333, 0.333333, 0.333333, 0,
            0, 0, 0, 0,
            0, 0, 0, 0)

        # check image mode
        if self.im.mode not in ("L", "RGB"):
            raise ValueError("Unsuported image mode for histogram computation")

        if self.im.mode == "RGB":
            # compute grey level image: I = (R + G + B) / 3
            if (option == "I") or (option == "all"):
                imgray = self.im.convert("L", rgb2I)
            # compute histograms of R,G and B values
            h = self.im.histogram()
            # compute histograms of I values
            if (option == "I") or (option == "all"):
                # concatenate I histogram to RGB histograms
                h = h + imgray.histogram()
            # get maximum of histograms of R, G, B and I values
            if option != "all":
                maxH = max(h[offsetH[option]:offsetH[option]+256])
            else:
                maxH = max(h)
        else:
            # compute histogram of I values
            h = self.im.histogram()
            # get maximum of histogram of I values
            maxH = max(h[0:256])

        return maxH

    def histogram(self, option="all", sizeH=(256, 128), margin=10, maxRef=None):
        """
        creates an image displaying the histogram of image values,
        only for '1x8i' (8bit gray) or '3x8i' (RGB) modes

        @param option: "R" histogram of R values, "G" histogram of G values,
                       "B" histogram of B values, "I" histogram of I values,
                       "all" histograms of R, G, B and I values
        """

        # constant values
        offsetH = {"R":0, "G":256, "B":512, "I":768}
        offsetY = {"R": sizeH[1]-1,
                   "G": 2*sizeH[1]+margin-1,
                   "B": 3*sizeH[1]+2*margin-1,
                   "I": 4*sizeH[1]+3*margin-1}
        color = {"R":(255, 0, 0),
                 "G":(0, 255, 0),
                 "B":(0, 0, 255),
                 "I":(192, 192, 192)}
        rgb2I = (
            0.333333, 0.333333, 0.333333, 0,
            0, 0, 0, 0,
            0, 0, 0, 0)

        # check image mode
        if self.im.mode not in ("L", "RGB"):
            raise ValueError("Unsuported image mode for histogram computation")

        if self.im.mode == "RGB":
            # compute grey level image: I = (R + G + B) / 3
            if (option == "I") or (option == "all"):
                imgray = self.im.convert("L", rgb2I)
            # compute histograms of R,G and B values
            h = self.im.histogram()
            # compute histograms of I values
            if (option == "I") or (option == "all"):
                # concatenate I histogram to RGB histograms
                h = h + imgray.histogram()
            # create a white output image
            if option == "all":
                size = (sizeH[0], 4*sizeH[1]+3*margin)
            else:
                size = sizeH
            imout = PIL.Image.new('RGB', size, (255, 255, 255))
            # draw histograms of R, G, B and I values
            if option != "all":
                maxH = max(h[offsetH[option]:offsetH[option]+256])
                if maxRef:
                    scaleH = float(sizeH[1]-1)/float(maxRef)
                else:
                    scaleH = float(sizeH[1]-1)/float(maxH)
                drawhistogram(imout, h[offsetH[option]:offsetH[option]+256],
                              sizeH[1]-1, 0, scaleH, color[option])
            else:
                maxH = max(h)
                if maxRef:
                    scaleH = float(sizeH[1]-1)/float(maxRef)
                else:
                    scaleH = float(sizeH[1]-1)/float(maxH)
                for i in ['R', 'G', 'B', 'I']:
                    drawhistogram(imout, h[offsetH[i]:offsetH[i]+256],
                                  offsetY[i], offsetY[i]-(sizeH[1]-1),
                                  scaleH, color[i])
        else:
            # compute histogram of I values
            h = self.im.histogram()
            # create a white output image
            size = sizeH
            imout = PIL.Image.new('L', size, 255)
            # draw histogram of I values
            maxH = max(h[0:256])
            if maxRef:
                scaleH = float(sizeH[1]-1)/float(maxRef)
            else:
                scaleH = float(sizeH[1]-1)/float(maxH)
            # histogram color: light gray
            drawhistogram(imout, h[0:256], sizeH[1]-1, 0, scaleH, 192)

        self.im = imout
        return self

    def clone(self):
        '''
        Clone the image object
        '''
        new_obj = image()
        new_obj.im = self.im.copy()
        return new_obj


