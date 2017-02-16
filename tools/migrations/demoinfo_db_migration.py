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


# This script move the "creation" field from demo_demodescription to demodescription.

from sys import argv, exit
import sqlite3 as lite

def main():
    if len(argv) != 2:
        print "Usage : ./demoinfo_db_migration.py <demoinfo database>"
        exit()
    db = str(argv[1])
    try:
        conn = lite.connect(db)
        cursor_db = conn.cursor()
        cursor_db.execute("""
        PRAGMA foreign_keys = OFF;
        """)
        conn.commit()

        # The following operation is required because SQLite does not handle 
        # default timestamp value in timestamp field creation via ALTER TABLE query.
        print "Creating demodescription buffer table"
        
        cursor_db.execute("""
        CREATE TABLE IF NOT EXISTS "demodescription_buf" (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        inproduction INTEGER(1) DEFAULT 1,
        JSON BLOB
        );
        """)
        conn.commit()
        cursor_db.execute("""
        INSERT INTO demodescription_buf (ID, inproduction, JSON)
        SELECT ID, inproduction, JSON 
        FROM demodescription;
        """)
        conn.commit()

        print "Moving creations timestamp into demodescription buffer table"
        
        cursor_db.execute("""
        SELECT creation, demodescriptionId FROM demo_demodescription;
        """)
        conn.commit()
        creation_dates = cursor_db.fetchall()
        for row in creation_dates:
            cursor_db.execute("""
            UPDATE demodescription_buf
            SET creation=?
            WHERE ID=?
            """, row)
            conn.commit()

        # The following operation is required because SQLite does not handle
        # column removal inside tables using ALTER TABLE query.
        print "Correcting demo_demodescription schema"
            
        cursor_db.execute("""
        CREATE TABLE IF NOT EXISTS "demo_demodescription_buf" (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        demoID INTEGER NOT NULL,
        demodescriptionId INTEGER NOT NULL,
        FOREIGN KEY(demodescriptionId) REFERENCES demodescription(id) ON DELETE CASCADE,
        FOREIGN KEY(demoID) REFERENCES demo(id) ON DELETE CASCADE
        );
        """)
        cursor_db.execute("""
        INSERT INTO demo_demodescription_buf (ID, demoID, demodescriptionId)
        SELECT ID, demoID, demodescriptionId
        FROM demo_demodescription;
        """)
        conn.commit()
        cursor_db.execute("""
        DROP TABLE demo_demodescription;
        """)
        conn.commit()
        cursor_db.execute("""
        ALTER TABLE demo_demodescription_buf RENAME TO demo_demodescription;
        """)
        conn.commit()

        print "Making demodescription buffer table as the new demodescription table"
        
        cursor_db.execute("""
        DROP TABLE demodescription;
        """)
        conn.commit()
        cursor_db.execute("""
        ALTER TABLE demodescription_buf RENAME TO demodescription;
        """)
        conn.commit()

        cursor_db.execute("""
        PRAGMA foreign_keys = ON;
        """)
        conn.commit()

        cursor_db.execute("""
        VACUUM;
        """)
        conn.commit()

        conn.close()
        
        print "OK"
        
    except Exception as ex:
        print "KO"
        print str(ex)
        print "Database probably jeopardized... Do not use the file the script was run on."
        conn.rollback()
        conn.close()

main()
