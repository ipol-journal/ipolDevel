#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public Licence (GPL)
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place, Suite 330, Boston, MA  02111-1307  USA

import os
import sys
import argparse
import magic
import mimetypes
from PIL import Image
import av
import numpy as np
import matplotlib
# matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pydub import AudioSegment



# TOTHINK, multithreading, on the first level folders ? On a big list ?

class ArchiveThumbs(object):
    srcdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))+"/ipol_demo/modules/archive/staticData/blobs/"
    destdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))+"/ipol_demo/modules/archive/staticData/blobs_thumbs"
    # resize to a default height, deisgn : a band of pictures
    height = 256

    @staticmethod
    def main():
        """ Command line parsing """
        parser = argparse.ArgumentParser(description='IPOL, archive module, admin thumbnails.', formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument(
            "action",
            nargs='?',
            choices=['refresh', 'replace', 'clean'],
            default='refresh',
            help='''refresh: loop on all source files, create thumbnails for newer source
replace: loop on all source files, force thumbnail creation
clean: loop on thumbnail files, delete the ones with no correspondant source file'''
        )
        args = parser.parse_args()
        if args.action == 'replace': print("replace")
        elif args.action == 'refresh': print("refresh")
        elif args.action == 'clean': print("clean")
        ArchiveThumbs.walk(ArchiveThumbs.srcdir)

    @staticmethod
    def walk(rootdir, relpath=""):
        """ Recursive exploration of folder, keep relative path for parallel creation of thumbs """
        # first call, normalize root folder
        if not relpath and rootdir:
            # no trailing / to rootdir, see below to optimize concat
            rootdir = rootdir.rstrip('\\/')
        if os.path.isdir(rootdir+relpath):
            files = os.listdir(rootdir+relpath)
            for entry in files:
                ArchiveThumbs.walk(rootdir, relpath+'/'+entry)
            return

        src = rootdir+relpath
        base, ext = os.path.splitext(relpath)
        dest = ArchiveThumbs.destdir+base
        # found in blobs.py, but what for?
        # mimetypes.guess_extension(mime)
        # for efficiency, src file may be open as a file descriptor
        # mesure time before too soon optimisation
        mime = magic.from_file(src, mime=True)
        format = mime.split('/')[0]

        if mime == "image/svg+xml": return # image, not supported by PIL
        if mime == "image/tiff": return # image, not supported by PIL

        if format == "image": dest = dest+".jpeg"
        elif format == "video": dest = dest+".jpeg"
        elif format == "audio": dest = dest+".png" # matplot of
        else: return

        # Create dest folder
        if not os.path.isdir(os.path.dirname(dest)): os.makedirs(os.path.dirname(dest))
        if os.path.exists(dest) and os.path.getmtime(dest) > os.path.getmtime(src): return

        print(format+" "+relpath)
        if format == "image": ArchiveThumbs.image_thumb(src, dest)
        elif format == "video": ArchiveThumbs.video_thumb(src, dest)
        elif format == "audio": ArchiveThumbs.audio_thumb(src, dest)


    @staticmethod
    def image_thumb(src, dest):
        """ From src image path, create a thumbnail to dest path """
        im = Image.open(src)
        """
        Bug seen UserWarning: Palette images with Transparency   expressed in bytes should be converted to RGBA images
        /f/0/f09a51e7c535e946d7ba80256550022fcb91c25b.png
        """
        ArchiveThumbs.pil_thumb(im, dest)

    @staticmethod
    def pil_thumb(im, dest):
        """ From a PIL image object, create a thumbnail to dest path, shared by image and video """
        width = int(round(im.width*ArchiveThumbs.height/im.height));
        im = im.convert('RGB') # RGBA image imposible to convert to JPEG
        # .resize allow better control than thumbnail
        im = im.resize((width, ArchiveThumbs.height), Image.LANCZOS)
        im.save(dest, 'JPEG', progression=True, subsampling='4:4:4')

    @staticmethod
    def video_thumb(src, dest):
        """ From src video path, create a thumbnail to dest path """
        container = av.open(src, mode='r')
        container.seek(int(container.duration/4) - 1)
        # hacky but I haven found way to make work a better writing like next()
        for frame in container.decode(video=0): break
        im = frame.to_image()
        ArchiveThumbs.pil_thumb(im, dest)
        container.close()

    @staticmethod
    def audio_thumb(src, dest):
        sound = AudioSegment.from_file(src)
        samples = sound.get_array_of_samples()
        signal = np.array(samples)

        height = ArchiveThumbs.height
        plt.close('all')
        dpi = 50
        fig = plt.figure(dpi=dpi)
        plt.plot(signal, color="black", linewidth=0.1, alpha=0.9)
        # set image size at the end
        fig.set_size_inches((height*4/3)/dpi, height/dpi)
        # not
        plt.axis('off')
        # important to frame around the graph with no margin
        plt.subplots_adjust(left=-0.04, right=1.04, top=1.1, bottom=-0.1)
        # DO NOT bbox_inches='tight', pad_inches=0, will change final size and layout upper
        fig.savefig(dest, transparent=True)
        plt.close('all')


if __name__ == '__main__':
  ArchiveThumbs.main()
