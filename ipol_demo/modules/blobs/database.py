"""
Blobs database
"""
from errors import IPOLBlobsDataBaseError


def store_blob(conn, blob_hash, blob_format, extension, credit):
    """
    Store the blob in the Blobs table and returns the blob id
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO blobs (hash, format, extension, credit)
            VALUES (?,?,?,?)
            """, (blob_hash, blob_format, extension, credit))
        return cursor.lastrowid
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def demo_exist(conn, editor_demo_id):
    """
    Verify if the editor_demo_id references an existing demo
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS(SELECT *
                        FROM demos
                        WHERE editor_demo_id=?);
            """, (editor_demo_id,))
        return cursor.fetchone()[0] == 1
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def create_demo(conn, editor_demo_id):
    """
    Creates a new demo
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO demos (editor_demo_id)
            VALUES (?)
            """, (editor_demo_id,))
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def add_blob_to_demo(conn, editor_demo_id, blob_id, blob_set, blob_pos, blob_title):
    """
    Associates the blob to a demo in demos_blobs table
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO demos_blobs (demo_id, blob_id, blob_set, pos_in_set, blob_title)
            VALUES ((SELECT id
                    FROM demos
                    WHERE editor_demo_id = ?), ?, ?, ?, ?)
            """, (editor_demo_id, blob_id, blob_set, blob_pos, blob_title))
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def all_templates_exist(conn, template_names):
    """
    Verify if ALL the template_names references an existing template
    """
    try:
        for name in template_names:
            if not template_exist(conn, name):
                return False
        return True
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def template_exist(conn, template_id):
    """
    Verify if the template_id references an existing template
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
                SELECT COUNT(*)
                FROM templates
                WHERE id = ?
                """, (template_id,))
        return cursor.fetchone()[0] >= 1
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def create_template(conn, template_name):
    """
    Creates a new template
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO templates (name)
            VALUES (?)
            """, (template_name,))
        return cursor.lastrowid
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def add_blob_to_template(conn, template_id, blob_id, pos_set, blob_set, blob_title):
    """
    Associates the blob to a template in templates_blobs table
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO templates_blobs (template_id, blob_id, blob_set, pos_in_set, blob_title)
            VALUES (?, ?, ?, ?, ?)
            """, (template_id, blob_id, blob_set, pos_set, blob_title))
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def add_template_to_demo(conn, template_id, editor_demo_id):
    """
    Associates a template to the demo in demos_templates table
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS(SELECT *
                        FROM demos_templates
                        WHERE demo_id=(SELECT id
                                    FROM demos
                                    WHERE editor_demo_id=?)
                        AND template_id=?);
            """, (editor_demo_id, template_id))

        if cursor.fetchone()[0] != 1:
            cursor.execute("""
                INSERT INTO demos_templates (demo_id, template_id)
                VALUES ((SELECT id
                        FROM demos
                        WHERE editor_demo_id = ?),?)
                """, (editor_demo_id, template_id))
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def get_demo_owned_blobs(conn, editor_demo_id):
    """
    Get all the blobs owned by the demo
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT blobs.id, hash, format, extension, blob_title, credit, blob_set, pos_in_set
            FROM blobs, demos, demos_blobs
            WHERE demo_id = demos.id
            AND blob_id = blobs.id
            AND demos.editor_demo_id = ?
            """, (editor_demo_id,))
        blobs = []
        for row in cursor.fetchall():
            blobs.append({"id": row[0], "hash": row[1], "format": row[2], "extension": row[3], "title": row[4],
                          "credit": row[5], "blob_set": row[6], "pos_set": row[7]})

        return blobs
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def get_template_blobs(conn, template_id):
    """
    Get all the blobs owned by the template
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT blobs.id, hash, format, extension, blob_title, credit, blob_set, pos_in_set
            FROM blobs, templates, templates_blobs
            WHERE template_id = ?
            AND blob_id = blobs.id
            """, (template_id,))
        blobs = []
        for row in cursor.fetchall():
            blobs.append({"id": row[0], "hash": row[1], "format": row[2], "extension": row[3], "title": row[4],
                          "credit": row[5], "blob_set": row[6], "pos_set": row[7]})

        return blobs
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def get_demo_templates(conn, editor_demo_id):
    """
    Get all the templates owned by the demo
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name
            FROM templates
            WHERE id IN (SELECT template_id
                        FROM demos_templates
                        WHERE demo_id = (SELECT id
                                        FROM demos
                                        WHERE editor_demo_id = ?))
            """, (editor_demo_id,))
        templates = []
        for id, name in cursor.fetchall():
            templates.append({'id': id, 'name': name})
        return templates
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def get_blob_data(conn, blob_id):
    """
    Return the blob data from blob_id or None if the id is wrong
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT hash, format, extension, credit
            FROM blobs
            WHERE id = ?
            """, (blob_id,))
        data = cursor.fetchone()
        if data is None:
            return None
        result = {'hash': data[0], 'format': data[1], 'extension': data[2], 'credit': data[3]}
        return result
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def get_blob_data_from_demo(conn, editor_demo_id, blob_set, pos_set):
    """
    Return the blob data from the position of the set in the demo or
    None if there is not blob for the given parameters
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT blobs.id, hash, format, extension, blob_title, credit
            FROM blobs, demos_blobs, demos
            WHERE editor_demo_id = ?
            AND blob_set = ?
            AND pos_in_set = ?
            AND demo_id = demos.id
            AND blobs.id = blob_id
            """, (editor_demo_id, blob_set, pos_set))
        data = cursor.fetchone()
        if data is None:
            return None
        result = {'id': data[0], 'hash': data[1], 'format': data[2], 'extension': data[3],
                  'title': data[4], 'credit': data[5]}
        return result
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def get_blob_data_from_template(conn, template_id, blob_set, pos_set):
    """
    Return the blob data from the position of the set in the template or
    None if there is not blob for the given parameters
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT blobs.id, hash, format, extension, blob_title, credit
            FROM blobs, templates_blobs
            WHERE template_id = ?
            AND blob_set = ?
            AND pos_in_set = ?
            AND blobs.id = blob_id
            """, (template_id, blob_set, pos_set))
        data = cursor.fetchone()
        if data is None:
            return None
        result = {'id': data[0], 'hash': data[1], 'format': data[2], 'extension': data[3],
                  'title': data[4], 'credit': data[5]}
        return result

    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def remove_blob_from_demo(conn, editor_demo_id, blob_set, pos_set):
    """
    Remove the blob from the demo
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""PRAGMA FOREIGN_KEYS = ON""")
        cursor.execute("""
                DELETE
                FROM demos_blobs
                WHERE demo_id = (SELECT id
                                FROM demos
                                WHERE editor_demo_id = ?)
                AND blob_set = ?
                AND pos_in_set = ?
                """, (editor_demo_id, blob_set, pos_set))

    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def remove_blob_from_template(conn, template_id, blob_set, pos_set):
    """
    Remove the blob from the template
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""PRAGMA FOREIGN_KEYS = ON""")
        cursor.execute("""
                DELETE
                FROM templates_blobs
                WHERE template_id = ?
                AND blob_set = ?
                AND pos_in_set = ?
                """, (template_id, blob_set, pos_set))

    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def get_blob_refcount(conn, blob_id):
    """
    Get number of references of the given blob
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*)
            FROM(
                SELECT id FROM demos_blobs WHERE blob_id = ?
                UNION ALL
                SELECT id FROM templates_blobs WHERE blob_id = ?
            )
                """, (blob_id, blob_id))
        return cursor.fetchone()[0]

    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def remove_blob(conn, blob_id):
    """
    Remove the blob from the DB
    """
    try:
        cursor = conn.cursor()

        cursor.execute("""PRAGMA foreign_keys = ON""")
        cursor.execute("""
            DELETE
            FROM blobs
            WHERE id = ?
            """, (blob_id,))

    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def remove_demo(conn, editor_demo_id):
    """
    Remove the demo
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""PRAGMA FOREIGN_KEYS = ON""")
        cursor.execute("""
            DELETE
            FROM demos
            WHERE editor_demo_id = ?
            """, (editor_demo_id,))

    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def remove_template(conn, template_id):
    """
    Remove the template
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""PRAGMA FOREIGN_KEYS = ON""")
        cursor.execute("""
            DELETE
            FROM templates
            WHERE id = ?
            """, (template_id,))

    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def remove_demo_blobs_association(conn, editor_demo_id):
    """
    Remove association between blobs and the demo
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""PRAGMA FOREIGN_KEYS = ON""")
        cursor.execute("""
            DELETE
            FROM demos_blobs
            WHERE demo_id = (SELECT id
                            FROM demos
                            WHERE editor_demo_id = ?)
            """, (editor_demo_id,))

    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def remove_template_blobs_association(conn, template_id):
    """
    Remove association between blobs and the template
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""PRAGMA FOREIGN_KEYS = ON""")
        cursor.execute("""
            DELETE
            FROM templates_blobs
            WHERE template_id = ?
            """, (template_id,))

    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def remove_template_from_demo(conn, editor_demo_id, template_id):
    """
    Remove the template from the demo in the demos_template table
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""PRAGMA FOREIGN_KEYS = ON""")
        cursor.execute("""
            DELETE
            FROM demos_templates
            WHERE demo_id = (SELECT id
                            FROM demos
                            WHERE editor_demo_id = ?)
            AND template_id = ?
            """, (editor_demo_id, template_id))
        return cursor.rowcount > 0

    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def edit_blob_from_demo(conn, editor_demo_id, set_name, new_set_name, pos, new_pos, blob_title, credit):
    """
    Edit information of the blob in a demo
    """
    try:
        cursor = conn.cursor()

        # Change credit from blobs table
        cursor.execute("""
            UPDATE blobs
            SET credit = ?
            WHERE id = (SELECT blob_id
                        FROM demos, demos_blobs
                        WHERE demos.id = demo_id
                        AND editor_demo_id= ?
                        AND blob_set = ?
                        AND pos_in_set = ?)
            """, (credit, editor_demo_id, set_name, pos))

        # Change title, set and pos from demos_blobs table
        cursor.execute("""
            UPDATE demos_blobs
            SET blob_set = ?, pos_in_set = ?, blob_title = ?
            WHERE blob_set = ?
            AND pos_in_set = ?
            AND demo_id = (SELECT id
                            FROM demos
                            WHERE editor_demo_id = ?)
            """, (new_set_name, new_pos, blob_title, set_name, pos, editor_demo_id))

    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def edit_blob_from_template(conn, template_id, set_name, new_set_name, pos, new_pos, blob_title, credit):
    """
    Edit information of the blob in a template
    """
    try:
        cursor = conn.cursor()

        # Change title and credit from blobs table
        cursor.execute("""
            UPDATE blobs
            SET credit = ?
            WHERE id = (SELECT blob_id
                        FROM templates_blobs
                        WHERE template_id= ?
                        AND blob_set = ?
                        AND pos_in_set = ?)
            """, (credit, template_id, set_name, pos))
        # Change set and pos from templates_blobs table
        cursor.execute("""
            UPDATE templates_blobs
            SET  blob_title = ?, blob_set = ?, pos_in_set = ?
            WHERE blob_set = ?
            AND pos_in_set = ?
            AND template_id = ?
            """, (blob_title, new_set_name, new_pos, set_name, pos, template_id))
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def is_pos_occupied_in_demo_set(conn, editor_demo_id, blob_set, pos):
    """
    Check if the position given is already used by other blob in the same set
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*)
            FROM demos_blobs
            WHERE blob_set = ?
            AND pos_in_set = ?
            AND demo_id = (SELECT id
                            FROM demos
                            WHERE editor_demo_id = ?)
        """, (blob_set, pos, editor_demo_id))

        return cursor.fetchone()[0] >= 1

    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def is_pos_occupied_in_template_set(conn, template_id, blob_set, pos):
    """
    Check if the position given is already used by other blob in the same set
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*)
            FROM templates_blobs
            WHERE blob_set = ?
            AND pos_in_set = ?
            AND template_id = ?
        """, (blob_set, pos, template_id))

        return cursor.fetchone()[0] >= 1

    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def get_available_pos_in_demo_set(conn, editor_demo_id, blob_set):
    """
    Return the first available position value of the set in the demo
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT pos_in_set + 1
            FROM demos_blobs
            WHERE demo_id = ?
            AND pos_in_set + 1 NOT IN 
                (
                SELECT pos_in_set 
                FROM demos_blobs
                WHERE demo_id = ?
                AND blob_set = ?
                )
            ORDER BY pos_in_set
            LIMIT 1
        """, (editor_demo_id, editor_demo_id, blob_set,))

        return cursor.fetchone()[0]

    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def get_available_pos_in_template_set(conn, template_id, blob_set):
    """
    Return the first available position value of the set in the demo
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT pos_in_set + 1
            FROM templates_blobs
            WHERE template_id = ?
            AND pos_in_set + 1 NOT IN 
                (
                SELECT pos_in_set 
                FROM templates_blobs
                WHERE template_id = ?
                AND blob_set = ?
                )
            ORDER BY pos_in_set
            LIMIT 1
        """, (template_id, template_id, blob_set,))

        return cursor.fetchone()[0]

    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def get_all_templates(conn):
    """
    get all templates
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name
            FROM templates
            """)
        templates = []
        for id, name in cursor.fetchall():
            templates.append({'id': id, 'name': name})
        return templates
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def update_demo_id(conn, old_editor_demo_id, new_editor_demo_id):
    """
    Update the given old editor demo id by the given new editor demo id
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE demos
            SET editor_demo_id = ?
            WHERE editor_demo_id = ?
            """, (new_editor_demo_id, old_editor_demo_id))
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def get_blob_id(conn, blob_hash):
    """
    Return the blob id or None if the hash is not stored in the DB
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id
            FROM blobs
            WHERE hash = ?
            """, (blob_hash,))
        data = cursor.fetchone()
        if data is None:
            return None
        return data[0]
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def get_demos_using_the_template(conn, template_id):
    """
    Return the list of demos that uses the given template
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
                SELECT editor_demo_id
                FROM demos, demos_templates
                WHERE template_id = ?
                AND demos.id = demo_id
                """, (template_id,))
        demos = []
        for demo in cursor.fetchall():
            demos.append(demo[0])

        return demos
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def get_nb_of_blobs(conn):
    """
    Return the number of blobs in the DB
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
               SELECT COUNT(*)
               FROM blobs
               """)
        data = cursor.fetchone()
        if data is None:
            return 0
        return data[0]
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def get_demo_id(conn, demo_id):
    """
    Return the editor demo id
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id
            FROM demos
            WHERE editor_demo_id = ?
        """, (demo_id,))
        return cursor.fetchone()[0]
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)


def get_template_id(conn, template_name):
    """
    Return the template id
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id
            FROM templates
            WHERE name = ?
        """, (template_name,))
        return cursor.fetchone()[0]
    except Exception as ex:
        raise IPOLBlobsDataBaseError(ex)
