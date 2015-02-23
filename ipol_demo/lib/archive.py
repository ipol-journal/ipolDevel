"""
archive bucket class and index tools
"""

# TODO: split images/files

import os
import time
import shutil
import gzip
import sqlite3
import cPickle as pickle
import cherrypy
import stat

S_644 = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH

from . import config
from .image import thumbnail

def key2url(key):
    """
    url construction scheme
    """
    return "%s/%s/" % (key[:2], key[2:])

def key2path(key):
    """
    path construction scheme
    """
    return os.path.join(key[:2], key[2:])

def path2key(path):
    """
    reverse key2path()
    """
    return ''.join(os.path.split(path))

def list_key(path):
    """
    get a list of all the bucket keys in the path
    """
    # TODO: iterator
    return [path2key(os.path.join(pfx, sfx))
            for pfx in os.listdir(path)
            if os.path.isdir(os.path.join(path, pfx))
            for sfx in os.listdir(os.path.join(path, pfx))
            if os.path.isdir(os.path.join(path, pfx, sfx))]

def _dummy_func():
    """
    do nothing
    """
    pass

    
class UserKeysManager(object):
    """
    Class that handles with cookies the keys of the files uploaded by
    the users to the archive.
    """

    def get_cookie_name(self):
        """
		Gets the name of the cookie
        """
        return "user_archive_keys"
        
    def get_keys_in_cookie(self):
        """
		Gets the keys in the cookie
        """
        if self.get_cookie_name() in cherrypy.request.cookie:
            keys_str = cherrypy.request.cookie[self.get_cookie_name()].value
            return pickle.loads(keys_str) 
        else:
            return []
    
    def key_belongs_to_user(self, key):
        """
		Checks in a given keys belongs to the current user
        """
        return key in self.get_keys_in_cookie()
        
    def add_key(self, key):
        """
		Links a key with the current user, for 24h.
        """
        keys_in_cookie = self.get_keys_in_cookie()
        keys_in_cookie.append(key)
        
        encoded = pickle.dumps(keys_in_cookie)
        cherrypy.response.cookie[self.get_cookie_name()] = encoded
        cherrypy.request.cookie[self.get_cookie_name()] = encoded
        
        cherrypy.response.cookie[self.get_cookie_name()]['max-age'] = 3600*24
        cherrypy.request.cookie[self.get_cookie_name()]['max-age'] = 3600*24



class bucket(object):
    """
    archive bucket class
    """
    def __init__(self, path, key, cwd=None):
        """
        open/read/create an archive bucket

        an archive bucket is
        * a set of files
        * a config dict, with these 3 sections:
          * info : free-form informations
          * file : file legends
          * meta : archive meta-information:
            * date : archive date
            * key : unique key

        @param path: base archive folder
        @param key: unique bucket key
        @param cwd: working directory used when adding files
        """
        date = time.strftime("%Y/%m/%d %H:%M")
        # bucket path
        path = os.path.abspath(path)
        self.path = os.path.join(path, key2path(key))
        # create the folder if needed
        if not os.path.isdir(self.path):
            os.makedirs(self.path)
        # read or init config dictionary
        self.cfg = config.file_dict(self.path, mode=S_644)
        if not (self.cfg.has_key('info')
                and self.cfg.has_key('fileinfo')
                and self.cfg.has_key('meta')
                and self.cfg['meta'].has_key('date')
                and self.cfg['meta'].has_key('key')):
            self.cfg.setdefault('info', {})
            self.cfg.setdefault('fileinfo', {})
            self.cfg.setdefault('meta', {})
            self.cfg['meta'].setdefault('date', date)
            self.cfg['meta'].setdefault('key', key)
            self.cfg.save()
        # working directory for add_file()
        self.cwd = cwd
        # pending files
        self.pend_files = []
        self.pend_zfiles = []
        # hooks
        self.hook = dict()

    def add_file(self, src, dst=None, info='', compress=False):
        """
        save a file in the archive bucket
        the file is copied from self.cwd to self.path
        """
        # TODO add_file() and add_image()
        # source filename
        src = os.path.basename(src)
        src_fname = os.path.join(self.cwd, src)
        # destination filename
        if dst is None:
            dst = src
        dst = os.path.basename(dst)
        if compress:
            dst += '.gz'
        # FIXME: file_dict keys are lowercase
        dst = dst.lower()
        dst_fname = os.path.join(self.path, dst)
        # add to the pending list
        if not compress:
            self.pend_files.append((src_fname, dst_fname))
        else:
            self.pend_zfiles.append((src_fname, dst_fname))
        # add the file info
        self.cfg['fileinfo'][dst] = info
        # add to the ordered files list
        files = self.cfg['meta'].get('files', '').split()
        files.append(dst)
        self.cfg['meta']['files'] = ' '.join(files)

    def add_info(self, info):
        """
        add an info {key: value} in the archive config dict
        """
        self.cfg['info'].update(info)

    def save(self):
        """
        copy the files,
        save the config file
        """
        # TODO: atomic save()
        # save the pending files
        for (src, dst) in self.pend_files:
            shutil.copy(src, dst)
        self.pend_files = []
        for (src, dst) in self.pend_zfiles:
            f_src = open(src, 'rb')
            f_dst = gzip.open(dst, 'wb')
            f_dst.writelines(f_src)
            f_dst.close()
            f_src.close()
        self.pend_zfiles = []
        # update the config
        self.cfg.save()
        # post-save hook
        if self.hook.has_key('post-save'):
            self.hook['post-save']()

#
# INDEX ITEMS
#

class item(object):
    """
    content of an index
    """
    def __init__(self, path, info=''):
        """
        create an index_item
        """
        self.path = os.path.abspath(path)
        self.name = os.path.basename(path)
        #self.ctime = misc.ctime(path, format="iso")
        #self.mtime = misc.mtime(path, format="iso")
        self.info = info
        if os.path.isdir(path):
            self.is_file = False
            self.is_dir = True
        if os.path.isfile(path):
            self.is_file = True
            self.is_dir = False
            # thumbnails
            if self.name.endswith((".png", ".jpg", ".jpeg")):
                self.tn_path = thumbnail(self.path, size=(256, 256))
                self.tn_name = os.path.basename(self.tn_path)
                self.has_tn = True
            else:
                self.has_tn = False

#
# DATABASE
#

_filter_listdir = lambda fname: (fname != "index.cfg"
                                  and not fname.startswith('.'))
def _add_record(cursor, ar):
    """
    low-level add an archive bucket record to the index
    """
    # raw unordered files list
    unordered_files = dict([(fname,
                             item(path=os.path.join(ar.path, fname),
                                  info=ar.cfg['fileinfo'].get(fname, '')))
                            for fname in filter(_filter_listdir,
                                                os.listdir(ar.path))])
    # reorder the files
    files = []
    try:
        files = [unordered_files.pop(fname)
                 for fname in ar.cfg['meta'].get('files', '').split()]
    except KeyError:
        cherrypy.log("missing archive file in %s" % (ar.path),
                     context='DEBUG', traceback=False)

    # append the remaining files
    files += unordered_files.values()

    meta = ar.cfg['meta']
    info = ar.cfg['info']

    cursor.execute("insert or replace into buckets "
                   + "(key, date, public, pkl_cache) "
                   + "values (?, ?, ?, ?)",
                   (ar.cfg['meta']['key'], ar.cfg['meta']['date'],
                    int(ar.cfg['meta'].get('public', True)),
                    pickle.dumps((files, meta, info))))
    return

def index_rebuild(indexdb, path):
    """
    create an index of the archive buckets
    """
    # TODO: atomic rebuild
    # (build into another file,and display "rebuilding...")
    cherrypy.log("(re)building the archive index %s" % indexdb,
                 context='SETUP', traceback=False)
    db = sqlite3.connect(indexdb)
    c = db.cursor()
    # (re)create table
    c.execute("drop table if exists buckets")
    # TODO : check SQL index usage
    c.execute("drop index if exists buckets_by_date")
    c.execute("create table buckets "
              + "(key text unique, date text, "
              + "public integer default 0, pkl_cache text)")
    c.execute("create index buckets_index_by_date_public "
              + "on buckets (date, public)")
    # populate the db
    for key in list_key(path):
        try:
            _add_record(c, bucket(path=path, key=key))
        except:
            cherrypy.log("indexing failed : %s %s" % (path, key),
                         context="ERROR", traceback=False)
    db.commit()
    c.close()


def index_read(indexdb, limit=20, offset=0, key=None, public=True, path=None):
    """
    get some data from the index
    """
    # TODO: use iterators
    try:
        db = sqlite3.connect(indexdb)
        c = db.cursor()
        if key:
            c.execute("select key, pkl_cache from buckets "
                      + "where key=?", (key, ))
        else:
            if public:
                c.execute("select key, pkl_cache from buckets where public=1 "
                          + "order by date asc limit ? offset ?",
                          (limit, offset))
            else:
                c.execute("select key, pkl_cache from buckets where public=0 "
                          + "order by date asc limit ? offset ?",
                          (limit, offset))
        return [(str(row[0]), pickle.loads(str(row[1]))) for row in c]
    except sqlite3.Error:
        if path:
            index_rebuild(indexdb, path)
            return index_read(indexdb, limit, offset, key)
        else:
            raise


def index_count(indexdb, path=None, public=True):
    """
    get nb keys in the index
    """

    try:
        db = sqlite3.connect(indexdb)
        c = db.cursor()
        if public:
            c.execute("select count(*) from buckets where public=1")
        else:
            c.execute("select count(*) from buckets where public=0")
        return c.next()[0]
    except sqlite3.Error:
        if path:
            index_rebuild(indexdb, path)
            return index_count(indexdb)
        else:
            raise

def index_first_date(indexdb, path=None):
    """
    get first archive date
    """

    try:
        db = sqlite3.connect(indexdb)
        c = db.cursor()
        c.execute("select date from buckets order by date asc limit 1")
        return c.next()[0]
    except sqlite3.Error:
        if path:
            index_rebuild(indexdb, path)
            return index_count(indexdb)
        else:
            raise

def index_add(indexdb, buc, path=None):
    """
    add an archive bucket to the index
    """
    
    
    try:
        db = sqlite3.connect(indexdb)
        c = db.cursor()
        _add_record(c, buc)
        db.commit()
        c.close()

        ukm = UserKeysManager()
        ukm.add_key(buc.cfg["meta"]["key"])
        
    except sqlite3.Error:
        if path:
            index_rebuild(indexdb, path)
            return index_add(indexdb, buc)
        else:
            raise

def index_delete(indexdb, key, path=None):
    """
    delete an archive bucket from the index
    """
    try:
        db = sqlite3.connect(indexdb)
        c = db.cursor()
        c.execute("DELETE FROM buckets WHERE key=?", (key, ))
        db.commit()
        c.close()
    except sqlite3.Error:
        raise

