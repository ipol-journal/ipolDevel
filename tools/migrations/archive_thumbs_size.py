#!/usr/bin/env python3

'''
It was found that blobs_thumbs folder contained huge thumbnails and was using 290 Gb of space.
This script corrected the thumbnails on Feb 07, 2022.
It goes through all entries in the database , checks size/format
and creates the thumb if the thumbnail doesn't exist and recreates in case of
wrong format (not JPEG) or thumb file size too large or image thumb too large.
'''

import PIL.Image
import sqlite3
import argparse
import magic
import os
import cv2
import sys
sys.path.insert(0, '/home/ipol/ipolDevel/ipol_demo/modules/core') 
from ipolutils.utils import thumbnail
from ipolutils.errors import IPOLImageReadError


def read_from_db(db_dir, thumb_dir):
    '''
    Read archive database
    '''
    db_path = os.path.join(db_dir, 'archive.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT hash, format, type FROM blobs')
    data = c.fetchall()

    for item in data:
        blob = item[0]
        media_type = item[1]
        mime_type = item[2]
        thumb_path = os.path.join(thumb_dir, blob[:1], blob[1:2])
        thumb_path = os.path.join(thumb_path, blob) + '.jpeg'

        yield blob, media_type, mime_type, thumb_path

comp_size = (500, 470)
def must_write_thumb(thumb_path):
    '''
    Return write_thumb as True if fileformat
    not JPEG, size and filesize are large
    '''
    mime = magic.Magic(mime=True)
    fileformat = mime.from_file(thumb_path)
    fileformat = fileformat.split('/')[1]
    bytes = os.path.getsize(thumb_path)

    try:
        im = PIL.Image.open(thumb_path)
        file_size = im.size
    except PIL.UnidentifiedImageError:
        print("cannot identify image file:",thumb_path)
        return False
    except ValueError as e:
        print(f"error:{e} at:{thumb_path}")
        return False
    except PIL.Image.DecompressionBombError as e:
        print(f"error:{e} at:{thumb_path}")
        return False

    if fileformat != 'jpeg' or file_size > comp_size or bytes > 100000:
        return True      


# parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("--db_dir", "-d", required=True,
                help="database directory")
ap.add_argument("--thumb_dir", "-t", required=True,
                help="thumb directory")
ap.add_argument("--blobs_dir", "-b", required=True,
                help="blobs directory")
args = ap.parse_args()
db_dir = args.db_dir
thumb_dir = args.thumb_dir
blobs_dir = args.blobs_dir


#create/re-create thumbnails
print("\nRecreating Thumbnails\n")
thumb_height = 128

for blob, media_type, mime_type, thumb_path in read_from_db(db_dir, thumb_dir):
    filename = os.path.basename(thumb_path)

    #create thumbnail if it doesn't exist
    if not os.path.isfile(thumb_path):
        if media_type == 'image' and mime_type not in ('tiff', 'tif'):
            blob_path = os.path.join(blobs_dir, blob[:1], blob[1:2])
            blob_path = os.path.join(blob_path, blob) + '.' + mime_type
            if os.path.isfile(blob_path):
                image = cv2.imread(blob_path)
                if image is not None:                    
                    height, width = image.shape[:2]
                    try:
                        response = thumbnail(src_file=blob_path, height=thumb_height, dst_file=thumb_path)
                        if response:
                            print(f"thumb created:{filename}, imagetype:{mime_type}")
                        else:
                            continue                   
                    except cv2.error as e:
                        print("exception occurred:", e)
                        if width < height:
                            max_size = (width, 128)
                        else: 
                            max_size = (100, height)               
                        data = cv2.resize(image, max_size, cv2.INTER_AREA)
                        cv2.imwrite(thumb_path, data)
                        print(f"thumb created:{filename}, imagetype:{mime_type}")
                else:
                    continue #continue if blob image has no data
            else:
                continue #continue if blob file does not exist
        else:
            continue #continue if media_type is not in image

    #recreate thumbnail if write_thumb is True
    if must_write_thumb(thumb_path):
        try:
            thumbnail(src_file=thumb_path, height=thumb_height, dst_file=thumb_path)
            print(f"thumb recreated:{filename}")
        except IPOLImageReadError:
            print("Image read error")
        except cv2.error as e:
            image = cv2.imread(thumb_path)
            height, width = image.shape[:2]
            print("exception occurred:", e)
            if width < height:
                max_size = (width, 128)
            else: 
                max_size = (100, height)               
            data = cv2.resize(image, max_size, cv2.INTER_AREA)
            cv2.imwrite(thumb_path, data)
            print(f"thumb recreated:{filename}")

print("\nDone Recreating\n")