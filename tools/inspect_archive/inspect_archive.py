#!/usr/bin/env python3

import argparse
import math
import os
import sqlite3


def _validate_identifiers(*names):
    for name in names:
        if not name.isidentifier():
            raise ValueError(f"Invalid table or column name: {name}")


def get_blob_sizes(db_path, table_name, hash_column, type_column, file_directory):
    # Connect to the SQLite database in read-only mode to reduce writer contention
    # (requires sqlite >= 3.7.0 and that the file is accessible)
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    cursor = conn.cursor()

    _validate_identifiers(table_name, hash_column, type_column)
    query = f"SELECT {hash_column}, {type_column} FROM {table_name}"
    cursor.execute(query)

    blob_info = []
    batch_size = 1000

    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            break

        for hash_value, type_value in rows:
            filename = f"{hash_value}.{type_value}"
            subdir1 = hash_value[:1]
            subdir2 = hash_value[1:2]
            filepath = os.path.join(file_directory, subdir1, subdir2, filename)
            if os.path.exists(filepath):
                size_mb = math.ceil(os.path.getsize(filepath) / (1024 * 1024))
                blob_info.append((filename, size_mb))
            else:
                blob_info.append((filename, None))

    # Sort and print as before
    blob_info.sort(key=lambda x: x[1] if x[1] is not None else -1, reverse=True)

    for filename, size_mb in blob_info:
        if size_mb is not None and size_mb >= min_size:
            print(f"Blob Name: {filename}, Size: {size_mb} MB")
        elif size_mb is None:
            print(f"Blob Name: {filename} not found")

    conn.close()


if __name__ == "__main__":
    core = os.path.expanduser("~/ipolDevel/ipol_demo/modules/core")
    db_path = os.path.join(core, "db", "archive.db")
    table_name = "blobs"
    hash_column = "hash"
    type_column = "type"
    file_directory = os.path.join(core, "staticData", "archive_blobs")
    min_size = 0  # Default minimum size in MB

    parser = argparse.ArgumentParser(
        description="Inspect archive blobs and their sizes."
    )
    parser.add_argument(
        "--min-size", type=int, default=0, help="Minimum blob size in MB to display"
    )
    args = parser.parse_args()
    min_size = args.min_size

    get_blob_sizes(db_path, table_name, hash_column, type_column, file_directory)
