#!/usr/bin/env python3

import PIL.Image
import sqlite3
import argparse
import magic
import os
import sys
sys.path.insert(0, '/home/ipol/ipolDevel/ipol_demo/modules/core') 
from ipolutils.utils import thumbnail


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
        hash = item[0]
        format = item[1]
        type = item[2]
        thumb_path = os.path.join(thumb_dir, hash[:1], hash[1:2])
        thumb_path = os.path.join(thumb_dir, hash[:1], hash[1:2])
        thumb_path = os.path.join(thumb_path, hash) + '.jpeg'

        yield hash, format, type, thumb_path

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
comp_size = (500, 470)
thumb_height = 128

for hash, format, type, thumb_path in read_from_db(db_dir, thumb_dir):
    src_file = thumb_path
    thumb_file = thumb_path
    filename = os.path.basename(thumb_path)

    #create thumbnail if it doesn't exist
    if not os.path.isfile(thumb_path):
        if format in ('image') and type not in ('tiff'):
            blob_path = os.path.join(blobs_dir, hash[:1], hash[1:2])
            blob_path = os.path.join(blob_path, hash) + '.' + type
            src_file = blob_path
            response = thumbnail(src_file, thumb_height, thumb_file)
            if response:
                print(f"thumb created:{filename}, imagetype:{type}")
            else:
                continue
        else:
            continue

    mime = magic.Magic(mime=True)
    fileformat = mime.from_file(thumb_path)
    fileformat = fileformat.split('/')[1]

    im = PIL.Image.open(thumb_path)
    file_size = im.size

    bytes = os.path.getsize(thumb_path)

    #recreate thumbnail if format not JPEG, size and filesize large
    if fileformat != "jpeg" or file_size > comp_size or bytes > 100000:
        thumbnail(src_file, thumb_height, thumb_file)
        print(f"thumb recreated:{filename} oldext:{fileformat} oldsize:{file_size}")

print("\nDone Recreating\n")