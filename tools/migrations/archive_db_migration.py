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


# This script is intended to correct problems in Archive's database
#   It checks if there is any redundant hash in the blobs table
#   If this happens:
#       1 - For any repeated hash, it will get the minor blob_id with that hash
#       2 - All references to different blobs with same hash,
#       will be pointed to the blob with the minor id obtained previously
#       3 - Any blob that remains without correspondece will be deleted


import os
import sqlite3 as lite

try:
    db_file = '../../ipol_demo/modules/archive/db/archive.db'

    if os.path.isfile(db_file):
        print '> Using DB: ' + db_file
        conn = lite.connect(db_file)
        cursor_db = conn.cursor()

        # find redundant hashes
        cursor_db.execute('''
            SELECT count(*), hash FROM blobs
            GROUP BY hash
            HAVING count(*) > 1
            ''')

        redundant_hashes = []
        for row in cursor_db.fetchall():
            redundant_hashes.append(row[1])

        count = len(redundant_hashes)
        print '>> %d redundant hashes found' % count

        if count > 0:
            # perform corrections for each one of the redundant hashes
            for hash in redundant_hashes:
                # min blob_id for the selected hash
                cursor_db.execute('''
                    SELECT min(id) FROM blobs
                    WHERE hash = ?
                    ''', (hash,))
                new_blob_id = cursor_db.fetchone()[0]

                cursor_db.execute('''
                    SELECT id FROM blobs
                    WHERE hash = ?
                    ''', (hash,))
                blobs_to_correct = cursor_db.fetchall()

                # correct correspondences table for the selected blob
                for blob_id in blobs_to_correct:
                    old_blob_id = blob_id[0]

                    if new_blob_id != old_blob_id:
                        # update id_blob in correspondences
                        cursor_db.execute('''
                            UPDATE correspondence
                            SET id_blob = ?
                            WHERE id_blob = ?
                        ''', (new_blob_id, old_blob_id,))

                        # delete redundant blobs without correspondences
                        cursor_db.execute('''
                            DELETE FROM blobs
                            WHERE id = ?
                        ''', (old_blob_id,))

            print '>> ' + str(conn.total_changes) + ' corrections performed'
            print '>> Migration completed'
        else:
            print '>> Database is OK'

        conn.commit()
        conn.close()
    else:
        print '>> Error: Database file not found'
    print '> Finished'

except Exception as ex:
    print '>> EXCEPTION: ' + str(ex)
    try:
        conn.rollback()
        conn.close()
    except Exception as ex:
        pass
