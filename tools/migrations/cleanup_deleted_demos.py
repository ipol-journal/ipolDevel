#!/usr/bin/env python3

"""
cleanup_deleted_demos.py

Periodic cleanup utility for IPOL.

The script removes data associated with demos that no longer exist in
demoinfo.db.

Cleanup includes:

    1. Demo-specific directories:
        ipol_demo/modules/demorunner/binaries/<demoId>
        shared_folder/demoExtras/<demoId>
        shared_folder/dl_extras/<demoId>
        ipol_demo/modules/core/staticData/demoExtras/<demoId>

    2. Orphaned archive data:
        - experiments belonging to deleted demos
        - correspondence records associated with those experiments
        - blob records that are no longer referenced by active experiments
        - physical archive blob files and thumbnails that are no longer needed

The script performs safety checks before deleting data and supports a
dry-run mode for reviewing the changes without modifying the filesystem
or databases.

Run with:

    python cleanup_deleted_demos.py --dry-run

to preview the cleanup, or:

    python cleanup_deleted_demos.py

to perform the cleanup.
"""

import argparse
import shutil
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

CORE_DIR = PROJECT_ROOT / "ipol_demo" / "modules" / "core"
DEMORUNNER_DIR = PROJECT_ROOT / "ipol_demo" / "modules" / "demorunner"

DEMOINFODB = CORE_DIR / "db" / "demoinfo.db"
ARCHIVEDB = CORE_DIR / "db" / "archive.db"

# Phase 1
DIRECTORIES = {
    "demorunner binaries": DEMORUNNER_DIR / "binaries",
    "shared demoExtras": PROJECT_ROOT / "shared_folder" / "demoExtras",
    "shared dl_extras": PROJECT_ROOT / "shared_folder" / "dl_extras",
    "demoinfo demoExtras": CORE_DIR / "staticData" / "demoExtras",
}

# Phase 2
ARCHIVE_BLOBS_DIR = CORE_DIR / "staticData" / "archive_blobs"
ARCHIVE_THUMBS_DIR = CORE_DIR / "staticData" / "archive_thumbs"



def check_database_exists(path):
    """Fail early if a required database is missing."""

    if not path.is_file():
        raise FileNotFoundError(
            f"Database not found: {path}"
        )


def get_existing_demo_ids():
    """
    Return all demo IDs currently present in demoinfo.db.

    The application uses editor_demo_id as the demo ID throughout
    the system.
    """

    connection = sqlite3.connect(DEMOINFODB)

    try:
        rows = connection.execute(
            """
            SELECT editor_demo_id
            FROM demo
            """
        ).fetchall()

        return {row[0] for row in rows}

    finally:
        connection.close()


#Phase 1 - demo-ID based filesystem cleanup

def cleanup_demo_directories(existing_demo_ids, dry_run=False):
    """
    Remove directories whose names are numeric demo IDs that no longer
    exist in demoinfo.db.

    Returns:
        Number of directories removed/would be removed.
    """

    removed_count = 0

    for description, base_directory in DIRECTORIES.items():

        if not base_directory.is_dir():
            print(
                f"[SKIP] {description}: "
                f"{base_directory} does not exist"
            )
            continue

        for path in sorted(base_directory.iterdir()):

            if not path.is_dir():
                continue

            # Only numeric directory names can represent demo IDs.
            try:
                demo_id = int(path.name)
            except ValueError:
                continue

            if demo_id in existing_demo_ids:
                continue

            print(
                f"[DELETE] {description}: {path}"
            )

            if not dry_run:
                shutil.rmtree(path)

            removed_count += 1

    return removed_count


# Phase 2 - archive database

def attach_demoinfo_database(connection):
    """
    Attach demoinfo.db to the archive database connection.
    """

    connection.execute(
        "ATTACH DATABASE ? AS demoinfo",
        (str(DEMOINFODB),),
    )


def get_orphan_archive_data(connection):
    """
    Find archive demo IDs and experiment IDs whose demo no longer exists
    in demoinfo.db.

    Returns:
        (orphan_demo_ids, orphan_experiment_ids)
    """

    orphan_demo_ids = {
        row[0]
        for row in connection.execute(
            """
            SELECT DISTINCT e.id_demo
            FROM experiments e
            LEFT JOIN demoinfo.demo d
                ON d.editor_demo_id = e.id_demo
            WHERE d.editor_demo_id IS NULL
            ORDER BY e.id_demo
            """
        )
    }

    orphan_experiment_ids = {
        row[0]
        for row in connection.execute(
            """
            SELECT e.id
            FROM experiments e
            LEFT JOIN demoinfo.demo d
                ON d.editor_demo_id = e.id_demo
            WHERE d.editor_demo_id IS NULL
            ORDER BY e.id
            """
        )
    }

    return orphan_demo_ids, orphan_experiment_ids


def create_orphan_experiment_table(connection, orphan_experiment_ids):
    """
    Store orphan experiment IDs in a temporary table.

    This avoids large IN (...) parameter lists and keeps the cleanup
    scalable for thousands of experiments.
    """

    connection.execute(
        """
        CREATE TEMP TABLE orphan_experiments (
            id INTEGER PRIMARY KEY
        )
        """
    )

    connection.executemany(
        """
        INSERT INTO orphan_experiments (id)
        VALUES (?)
        """,
        ((experiment_id,) for experiment_id in orphan_experiment_ids),
    )


def get_orphan_blob_ids(connection):
    """
    Return distinct blob IDs referenced by orphan experiments.
    """

    return {
        row[0]
        for row in connection.execute(
            """
            SELECT DISTINCT c.id_blob
            FROM correspondence c
            JOIN orphan_experiments oe
                ON oe.id = c.id_experiment
            """
        )
    }


def get_shared_blob_ids(connection):
    """
    Return blob IDs that are referenced by both:
      - an orphan experiment, and
      - an active experiment.

    Such blob records must not be deleted.
    """

    return {
        row[0]
        for row in connection.execute(
            """
            SELECT DISTINCT c.id_blob
            FROM correspondence c
            JOIN orphan_experiments oe
                ON oe.id = c.id_experiment
            JOIN correspondence active_c
                ON active_c.id_blob = c.id_blob
            JOIN experiments active_e
                ON active_e.id = active_c.id_experiment
            JOIN demoinfo.demo active_d
                ON active_d.editor_demo_id = active_e.id_demo
            """
        )
    }


def get_safe_blob_rows(connection):
    """
    Return blob records referenced only by orphan experiments.

    Returns:
        (blob_id, hash, type, format)
    """

    return connection.execute(
        """
        SELECT DISTINCT
            b.id,
            b.hash,
            b.type,
            b.format
        FROM blobs b
        JOIN correspondence c
            ON c.id_blob = b.id
        JOIN orphan_experiments oe
            ON oe.id = c.id_experiment
        WHERE NOT EXISTS (
            SELECT 1
            FROM correspondence active_c
            JOIN experiments active_e
                ON active_e.id = active_c.id_experiment
            JOIN demoinfo.demo active_d
                ON active_d.editor_demo_id = active_e.id_demo
            WHERE active_c.id_blob = b.id
        )
        ORDER BY b.id
        """
    ).fetchall()


def get_active_physical_identities(connection):
    """
    Return physical archive identities used by active experiments.

    Physical blob identity is (hash, type).

    This is deliberately checked independently of blob.id because
    duplicate blob records can point to the same physical file.
    """

    return {
        (row[0], row[1])
        for row in connection.execute(
            """
            SELECT DISTINCT
                b.hash,
                b.type
            FROM blobs b
            JOIN correspondence c
                ON c.id_blob = b.id
            JOIN experiments e
                ON e.id = c.id_experiment
            JOIN demoinfo.demo d
                ON d.editor_demo_id = e.id_demo
            """
        )
    }


def get_active_hashes(connection):
    """
    Return hashes used by active experiments.

    Thumbnails are identified by hash only, so a thumbnail must not be
    deleted when its hash is still used by an active archive blob.
    """

    return {
        row[0]
        for row in connection.execute(
            """
            SELECT DISTINCT b.hash
            FROM blobs b
            JOIN correspondence c
                ON c.id_blob = b.id
            JOIN experiments e
                ON e.id = c.id_experiment
            JOIN demoinfo.demo d
                ON d.editor_demo_id = e.id_demo
            """
        )
    }


def archive_blob_path(hash_name, blob_type):
    """
    Calculate the physical archive blob path without creating directories.

    This matches the archive storage layout:

        archive_blobs/<first>/<second>/<hash>.<type>
    """

    if hash_name is None:
        return None

    subdirectory = Path(*hash_name[:2])

    return (
        ARCHIVE_BLOBS_DIR
        / subdirectory
        / f"{hash_name}.{blob_type}"
    )


def archive_thumbnail_path(hash_name):
    """
    Calculate the physical archive thumbnail path.

    Thumbnail layout:

        archive_thumbs/<first>/<second>/<hash>.jpeg
    """

    if hash_name is None:
        return None

    subdirectory = Path(*hash_name[:2])

    return (
        ARCHIVE_THUMBS_DIR
        / subdirectory
        / f"{hash_name}.jpeg"
    )


def delete_archive_files(
    physical_blobs,
    active_hashes,
    dry_run=False,
):
    """
    Delete physical archive blob files and thumbnails.

    physical_blobs contains unique (hash, type) identities.

    A thumbnail is deleted only if its hash is not used by any
    active experiment.

    Returns:
        (
            blob_files_deleted,
            thumbnail_files_deleted,
            missing_blob_files,
            missing_thumbnail_files,
        )
    """

    blob_files_deleted = 0
    thumbnail_files_deleted = 0
    missing_blob_files = 0
    missing_thumbnail_files = 0

    for hash_name, blob_type in sorted(physical_blobs):

        blob_path = archive_blob_path(
            hash_name,
            blob_type,
        )

        thumbnail_path = archive_thumbnail_path(
            hash_name,
        )

        # Archive blob

        if blob_path is not None and blob_path.is_file():

            if dry_run:
                print(
                    f"[DELETE] archive blob: {blob_path}"
                )
            else:
                try:
                    blob_path.unlink()
                    print(
                        f"[DELETE] archive blob: {blob_path}"
                    )
                except OSError as exc:
                    print(
                        f"[WARNING] Could not delete blob file "
                        f"{blob_path}: {exc}"
                    )
                    continue

            blob_files_deleted += 1

        else:
            missing_blob_files += 1

        # Thumbnail

        # The thumbnail is identified by hash only. Never delete it
        # if the hash is still used by an active experiment.
        if hash_name in active_hashes:
            continue

        if thumbnail_path is not None and thumbnail_path.is_file():

            if dry_run:
                print(
                    f"[DELETE] archive thumbnail: {thumbnail_path}"
                )
            else:
                try:
                    thumbnail_path.unlink()
                    print(
                        f"[DELETE] archive thumbnail: {thumbnail_path}"
                    )
                except OSError as exc:
                    print(
                        f"[WARNING] Could not delete thumbnail "
                        f"{thumbnail_path}: {exc}"
                    )
                    continue

            thumbnail_files_deleted += 1

        else:
            missing_thumbnail_files += 1

    return (
        blob_files_deleted,
        thumbnail_files_deleted,
        missing_blob_files,
        missing_thumbnail_files,
    )


def cleanup_archive(connection, dry_run=False):
    """
    Clean archive data belonging to demos that no longer exist.

    Database operations are performed explicitly and inside one
    transaction. SQLite foreign-key enforcement is not required.

    Physical files are removed only after the database transaction
    has successfully committed.
    """

    (
        orphan_demo_ids,
        orphan_experiment_ids,
    ) = get_orphan_archive_data(connection)

    print(
        f"[ARCHIVE] Orphaned demos: "
        f"{len(orphan_demo_ids)}"
    )

    print(
        f"[ARCHIVE] Orphaned experiments: "
        f"{len(orphan_experiment_ids)}"
    )

    if not orphan_experiment_ids:
        print("[ARCHIVE] Nothing to clean.")
        return

    create_orphan_experiment_table(
        connection,
        orphan_experiment_ids,
    )

    orphan_blob_ids = get_orphan_blob_ids(connection)

    shared_blob_ids = get_shared_blob_ids(connection)

    safe_blob_rows = get_safe_blob_rows(connection)

    print(
        f"[ARCHIVE] Blob records referenced by orphaned "
        f"experiments: {len(orphan_blob_ids)}"
    )

    print(
        f"[ARCHIVE] Blob records shared with active experiments: "
        f"{len(shared_blob_ids)}"
    )

    print(
        f"[ARCHIVE] Blob records safe to delete: "
        f"{len(safe_blob_rows)}"
    )

    # Determine physical identities.

    safe_physical_blobs = {
        (row[1], row[2])
        for row in safe_blob_rows
    }

    active_physical_blobs = get_active_physical_identities(
        connection
    )

    # An orphan blob record is not sufficient by itself to authorize
    # physical deletion. The physical (hash, type) identity must also
    # have no active reference.
    safe_physical_blobs -= active_physical_blobs

    active_hashes = get_active_hashes(connection)

    print(
        f"[ARCHIVE] Distinct physical blobs safe to delete: "
        f"{len(safe_physical_blobs)}"
    )

    # Sanity checks.

    if len(safe_blob_rows) != len(orphan_blob_ids) - len(shared_blob_ids):
        raise RuntimeError(
            "Archive blob safety check failed: "
            "unexpected blob-record counts."
        )

    # Dry run.

    if dry_run:
        print(
            "[ARCHIVE] DRY RUN: "
            "no archive database records or files were deleted."
        )
        return


    try:

        # Delete correspondence rows first.
        connection.execute(
            """
            DELETE FROM correspondence
            WHERE id_experiment IN (
                SELECT id
                FROM orphan_experiments
            )
            """
        )

        # Delete only blob records that were verified to have no
        # active references.
        if safe_blob_rows:

            connection.executemany(
                """
                DELETE FROM blobs
                WHERE id = ?
                """,
                (
                    (row[0],)
                    for row in safe_blob_rows
                ),
            )

        # Delete the orphan experiments.
        connection.execute(
            """
            DELETE FROM experiments
            WHERE id IN (
                SELECT id
                FROM orphan_experiments
            )
            """
        )

        # Commit all database changes together.
        connection.commit()

    except Exception:

        connection.rollback()

        print(
            "[ERROR] Archive database cleanup failed. "
            "All archive database changes were rolled back. "
            "No physical archive files were deleted."
        )

        raise

    # Database transaction succeeded.
    #
    # Physical files can now be removed.

    (
        deleted_blob_files,
        deleted_thumbnail_files,
        missing_blob_files,
        missing_thumbnail_files,
    ) = delete_archive_files(
        safe_physical_blobs,
        active_hashes,
    )

    print(
        f"[ARCHIVE] Experiment records deleted: "
        f"{len(orphan_experiment_ids)}"
    )

    print(
        f"[ARCHIVE] Blob records deleted: "
        f"{len(safe_blob_rows)}"
    )

    print(
        f"[ARCHIVE] Physical blob files deleted: "
        f"{deleted_blob_files}"
    )

    print(
        f"[ARCHIVE] Thumbnail files deleted: "
        f"{deleted_thumbnail_files}"
    )

    if missing_blob_files:
        print(
            f"[ARCHIVE] Blob files already missing: "
            f"{missing_blob_files}"
        )

    if missing_thumbnail_files:
        print(
            f"[ARCHIVE] Thumbnail files already missing: "
            f"{missing_thumbnail_files}"
        )


# Main

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Clean resources belonging to demos that no longer exist."
        )
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Show what would be deleted without deleting "
            "files or database records."
        ),
    )

    parser.add_argument(
        "--archive-only",
        action="store_true",
        help=(
            "Run only archive cleanup. "
            "Phase 1 filesystem cleanup is skipped."
        ),
    )

    args = parser.parse_args()

    print(
        f"Project root: {PROJECT_ROOT}"
    )

    if args.dry_run:
        print(
            "DRY RUN: no files or database records "
            "will be deleted."
        )
    else:
        print(
            "LIVE RUN: files and database records "
            "WILL be deleted."
        )

    # Required database checks.

    check_database_exists(DEMOINFODB)
    check_database_exists(ARCHIVEDB)

    # IMPORTANT SAFETY GATE
    #
    # This is performed regardless of --archive-only.
    # An empty demoinfo database must never result in mass deletion.

    existing_demo_ids = get_existing_demo_ids()

    print(
        f"Found {len(existing_demo_ids)} existing demos "
        f"in demoinfo.db."
    )

    if not existing_demo_ids:
        raise RuntimeError(
            "No demo IDs found in demoinfo.db. "
            "Cleanup aborted to prevent accidental deletion."
        )

    # Phase 1

    if not args.archive_only:

        print(
            "\n=== Phase 1: filesystem cleanup ==="
        )

        directory_count = cleanup_demo_directories(
            existing_demo_ids,
            dry_run=args.dry_run,
        )

        print(
            f"Phase 1: {directory_count} demo directories "
            f"{'would be ' if args.dry_run else ''}"
            f"removed."
        )

    else:

        print(
            "\n=== Phase 1: skipped "
            "(--archive-only) ==="
        )

    # Phase 2

    print(
        "\n=== Phase 2: archive cleanup ==="
    )

    archive_connection = sqlite3.connect(
        ARCHIVEDB
    )

    try:

        attach_demoinfo_database(
            archive_connection
        )

        cleanup_archive(
            archive_connection,
            dry_run=args.dry_run,
        )

    finally:

        archive_connection.close()

    print(
        "\nCleanup finished."
    )


if __name__ == "__main__":
    main()