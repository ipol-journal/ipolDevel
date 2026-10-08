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
import re
import shutil
import sqlite3
import tempfile
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

            # A symlink to a directory makes is_dir() return True, but
            # shutil.rmtree() cannot remove directory symlinks. Remove
            # the symlink itself instead of following it.

            if path.is_symlink():

                if not dry_run:
                    path.unlink()

            elif path.is_dir():

                if not dry_run:
                    shutil.rmtree(path)

            else:
                continue

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

def create_active_blob_table(connection):
    """
    Materialize blob IDs referenced by active experiments in a temporary
    table. The primary key provides an index for fast membership checks.
    This avoids repeatedly checking active references in correspondence
    for every candidate blob.
    """

    connection.execute(
        """
        CREATE TEMP TABLE active_blob_ids (
            id INTEGER PRIMARY KEY
        )
        """

    )

    connection.execute(
        """
        INSERT INTO active_blob_ids (id)
        SELECT DISTINCT c.id_blob
        FROM correspondence c
        JOIN experiments e
            ON e.id = c.id_experiment
        JOIN demoinfo.demo d
            ON d.editor_demo_id = e.id_demo
        """

    )

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
            JOIN active_blob_ids a
                ON a.id = c.id_blob
            """
        )
    }

def get_safe_blob_rows(connection):
    """
    Return blob records referenced only by orphan experiments.
    Active blob IDs are materialized in a temporary table, so this uses
    an indexed lookup against the materialized active-blob set.
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
        LEFT JOIN active_blob_ids a
            ON a.id = b.id
        WHERE a.id IS NULL
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
            JOIN active_blob_ids a
                ON a.id = b.id
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
            JOIN active_blob_ids a
                ON a.id = b.id
            """
        )
    }

def _validate_archive_component(value, name):

    """
    Validate a value used as part of an archive file path.
    Hashes must contain only hexadecimal characters. Blob types must
    contain only ASCII letters and digits.
    """

    if not isinstance(value, str) or not value:

        raise ValueError(
            f"Invalid archive {name}: {value!r}"
        )

    if name == "hash":
        valid = re.fullmatch(r"[0-9a-fA-F]+", value)
    else:

        valid = re.fullmatch(r"[A-Za-z0-9]+", value)

    if valid is None:
        raise ValueError(
            f"Invalid archive {name}: {value!r}"
        )

def _archive_path_within_directory(path, directory):

    """
    Ensure a resolved archive path remains inside its expected directory.
    """

    resolved_path = path.resolve(strict=False)

    resolved_directory = directory.resolve(strict=False)

    try:
        resolved_path.relative_to(resolved_directory)

    except ValueError:
        raise ValueError(
            f"Archive path escapes its storage directory: {path}"
        )

    return resolved_path

def archive_blob_path(hash_name, blob_type):

    """
    Calculate the physical archive blob path without creating directories.
    This matches the archive storage layout:
        archive_blobs/<first>/<second>/<hash>.<type>
    """

    if hash_name is None:

        return None

    _validate_archive_component(hash_name, "hash")
    _validate_archive_component(blob_type, "type")
    subdirectory = Path(*hash_name[:2])

    path = (
        ARCHIVE_BLOBS_DIR
        / subdirectory
        / f"{hash_name}.{blob_type}"
    )

    return _archive_path_within_directory(
        path,
        ARCHIVE_BLOBS_DIR,
    )

def archive_thumbnail_path(hash_name):

    """
    Calculate the physical archive thumbnail path.
    Thumbnail layout:
        archive_thumbs/<first>/<second>/<hash>.jpeg
    """

    if hash_name is None:
        return None

    _validate_archive_component(hash_name, "hash")
    subdirectory = Path(*hash_name[:2])

    path = (
        ARCHIVE_THUMBS_DIR
        / subdirectory
        / f"{hash_name}.jpeg"
    )

    return _archive_path_within_directory(
        path,
        ARCHIVE_THUMBS_DIR,
    )

def quarantine_archive_files(
    physical_blobs,
    active_hashes,
):
    """
    Copy physical archive files to a temporary quarantine directory.

    Files are copied while the archive database write transaction is still
    active. The original files remain in place until the database transaction
    commits, so a process crash before commit cannot leave the database
    referencing a file that has already been moved away.
    """
    quarantine_dir = Path(
        tempfile.mkdtemp(
            prefix="cleanup_archive_",
            dir=CORE_DIR / "staticData",
        )
    )
    quarantined_files = []
    blob_files_quarantined = 0
    thumbnail_files_quarantined = 0
    missing_blob_files = 0
    missing_thumbnail_files = 0
    try:
        for hash_name, blob_type in sorted(physical_blobs):
            blob_path = archive_blob_path(hash_name, blob_type)
            thumbnail_path = archive_thumbnail_path(hash_name)
            if blob_path is not None and blob_path.is_file():
                destination = (
                    quarantine_dir
                    / "archive_blobs"
                    / Path(*hash_name[:2])
                    / blob_path.name
                )
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(blob_path, destination)
                quarantined_files.append((destination, blob_path))
                print(f"[QUARANTINE] archive blob: {blob_path}")
                blob_files_quarantined += 1
            else:
                missing_blob_files += 1
            if hash_name in active_hashes:
                continue
            if thumbnail_path is not None and thumbnail_path.is_file():
                destination = (
                    quarantine_dir
                    / "archive_thumbs"
                    / Path(*hash_name[:2])
                    / thumbnail_path.name
                )
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(thumbnail_path, destination)
                quarantined_files.append((destination, thumbnail_path))
                print(f"[QUARANTINE] archive thumbnail: {thumbnail_path}")
                thumbnail_files_quarantined += 1
            else:
                missing_thumbnail_files += 1
    except Exception:
        shutil.rmtree(quarantine_dir, ignore_errors=True)
        raise
    return (
        quarantine_dir,
        quarantined_files,
        blob_files_quarantined,
        thumbnail_files_quarantined,
        missing_blob_files,
        missing_thumbnail_files,
    )

def delete_quarantined_originals(quarantined_files):
    """Delete original files after the database transaction has committed."""
    deletion_failures = []
    for quarantine_path, original_path in quarantined_files:
        try:
            original_path.unlink()
        except FileNotFoundError:
            pass
        except OSError as exc:
            deletion_failures.append((original_path, exc))
    if deletion_failures:
        details = "; ".join(
            f"{path}: {error}"
            for path, error in deletion_failures
        )
        raise RuntimeError(
            "Failed to delete one or more original archive files after "
            f"archive database cleanup committed: {details}"
        )

def cleanup_archive(connection, dry_run=False):

    """

    Clean archive data belonging to demos that no longer exist.
    SQLite's IMMEDIATE transaction prevents another archive database writer
    from changing the data while cleanup is determining and deleting
    orphan records.
    Physical files are quarantined before the database transaction
    is committed.
    """

    if not dry_run:

        connection.execute("BEGIN IMMEDIATE")

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
        if not dry_run:
            connection.commit()

        print("[ARCHIVE] Nothing to clean.")
        return

    create_orphan_experiment_table(

        connection,
        orphan_experiment_ids,
    )

    create_active_blob_table(connection)
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

    safe_physical_blobs = {
        (row[1], row[2])
        for row in safe_blob_rows
    }

    active_physical_blobs = get_active_physical_identities(
        connection
    )

    safe_physical_blobs -= active_physical_blobs
    active_hashes = get_active_hashes(connection)

    print(
        f"[ARCHIVE] Distinct physical blobs safe to delete: "
        f"{len(safe_physical_blobs)}"
    )

    if len(safe_blob_rows) != len(orphan_blob_ids) - len(shared_blob_ids):

        print(
            "[WARNING] Archive blob safety check found a discrepancy: "
            f"orphan blob IDs={len(orphan_blob_ids)}, "
            f"shared blob IDs={len(shared_blob_ids)}, "
            f"safe blob rows={len(safe_blob_rows)}. "
            "This may indicate dangling correspondence references."
        )

    if dry_run:

        print(
            "[ARCHIVE] DRY RUN: "
            "no archive database records or files were deleted."
        )

        return

    quarantine_dir = None
    quarantined_files = []

    try:

        connection.execute(
            """
            DELETE FROM correspondence
            WHERE id_experiment IN (
                SELECT id
                FROM orphan_experiments
            )
            """

        )

        if safe_blob_rows:

            connection.executemany(
                """
                DELETE FROM blobs
                WHERE id = ?
                """,
                ((row[0],) for row in safe_blob_rows),

            )

        connection.execute(

            """
            DELETE FROM experiments
            WHERE id IN (
                SELECT id
                FROM orphan_experiments
            )
            """

        )

        (

            quarantine_dir,
            quarantined_files,
            quarantined_blob_files,
            quarantined_thumbnail_files,
            missing_blob_files,
            missing_thumbnail_files,
        ) = quarantine_archive_files(
            safe_physical_blobs,
            active_hashes,
        )

        connection.commit()

    except Exception:
        connection.rollback()
        if quarantine_dir is not None:
            shutil.rmtree(
                quarantine_dir,
                ignore_errors=True,
            )
        print(
            "[ERROR] Archive database cleanup failed. "
            "All archive database changes were rolled back. "
            "Original physical files were left untouched."
        )
        raise

    if quarantine_dir is not None:
        deletion_succeeded = True

        try:
            delete_quarantined_originals(quarantined_files)
        except RuntimeError as exc:
            deletion_succeeded = False
            print(
                "[WARNING] Archive database cleanup committed, but some "
                "original physical files could not be deleted. The "
                f"quarantine copy is retained at {quarantine_dir}: {exc}"
            )

        if deletion_succeeded:
            try:
                shutil.rmtree(
                    quarantine_dir,
                    ignore_errors=False,
                )
            except OSError as exc:
                print(
                    "[WARNING] Archive database cleanup committed, but the "
                    f"quarantine directory could not be removed: {exc}"
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
        f"[ARCHIVE] Physical blob files quarantined: "
        f"{quarantined_blob_files}"
    )

    print(
        f"[ARCHIVE] Thumbnail files quarantined: "
        f"{quarantined_thumbnail_files}"
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