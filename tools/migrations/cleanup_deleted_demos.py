#!/usr/bin/env python3

"""
cleanup_deleted_demos.py
Periodic cleanup utility for IPOL.
The script removes directories belonging to demos that no longer exist in
demoinfo.db.

Directories cleaned:
    ipol_demo/modules/demorunner/binaries/<demoId>
    shared_folder/demoExtras/<demoId>
    shared_folder/dl_extras/<demoId>
    ipol_demo/modules/core/staticData/demoExtras/<demoId>

Run with:
    python cleanup_deleted_demos.py --dry-run
or
    python cleanup_deleted_demos.py (to delete all directories)
"""

import argparse
import logging
import shutil
import sqlite3
import sys

from pathlib import Path



# Configuration
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_DIR = PROJECT_ROOT/"ipol_demo"/"modules"/"core"
DEMORUNNER_DIR = PROJECT_ROOT/"ipol_demo"/"modules"/"demorunner"
DEMOINFODB = CORE_DIR/"db"/"demoinfo.db"


DIRECTORIES = {
    "demorunner binaries": DEMORUNNER_DIR/"binaries",
    "shared demoExtras": PROJECT_ROOT/"shared_folder"/"demoExtras",
    "shared dl_extras": PROJECT_ROOT/"shared_folder"/"dl_extras",
    "demoinfo demoExtras": CORE_DIR/"staticData"/"demoExtras",
}



# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger("cleanup_deleted_demos")



# Statistics
class CleanupStats:

    def __init__(self):
        self.scanned = 0
        self.orphaned = 0
        self.removed = 0
        self.skipped = 0
        self.errors = 0


# Database
def get_existing_demo_ids():
    """
    Read all existing demo IDs from demoinfo.db.
    """

    connection = sqlite3.connect(DEMOINFODB)

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT editor_demo_id
            FROM demo
            """
        )

        rows = cursor.fetchall()

        return {
            int(row[0])
            for row in rows
            if row[0] is not None
        }

    finally:

        connection.close()



# Discovery
def collect_orphan_directories(existing_demo_ids, stats):
    """
    Scan every configured directory and return the orphan directories.
    """

    orphaned = []
    for name, root in DIRECTORIES.items():

        logger.info("Scanning %s (%s)", name, root)

        if not root.exists():

            logger.warning(
                "Directory does not exist: %s",
                root,
            )

            continue

        for entry in sorted(root.iterdir()):

            if not entry.is_dir():

                continue

            # Ignore folders that are not demo IDs.
            if not entry.name.isdigit():

                stats.skipped += 1

                continue

            stats.scanned += 1

            demo_id = int(entry.name)

            if demo_id in existing_demo_ids:

                continue

            logger.info(
                "Found orphan directory for demo %s : %s",
                demo_id,
                entry,
            )

            orphaned.append(
                (
                    demo_id,
                    entry,
                )
            )

    stats.orphaned = len(orphaned)

    return orphaned

# Cleanup
def remove_orphan_directories(orphaned, stats, dry_run):
    """
    Remove all orphaned directories.
    """

    if not orphaned:

        logger.info("No orphaned directories found.")

        return

    for demo_id, directory in orphaned:

        try:

            if dry_run:

                logger.info(
                    "[DRY-RUN] Would remove demo %d -> %s",
                    demo_id,
                    directory,
                )

                continue

            shutil.rmtree(directory)

            stats.removed += 1

            logger.info(
                "Removed demo %d -> %s",
                demo_id,
                directory,
            )

        except Exception:

            stats.errors += 1

            logger.exception(
                "Unable to remove %s",
                directory,
            )


# Reporting
def print_summary(stats):

    logger.info("")
    logger.info("****************************")
    logger.info("Cleanup summary")
    logger.info("****************************")
    logger.info("Directories scanned : %d", stats.scanned)
    logger.info("Orphaned found      : %d", stats.orphaned)
    logger.info("Directories removed : %d", stats.removed)
    logger.info("Skipped entries     : %d", stats.skipped)
    logger.info("Errors              : %d", stats.errors)
    logger.info("****************************")


# Cleanup execution
def run_cleanup(dry_run):

    logger.info("Reading demo IDs from %s", DEMOINFODB)

    existing_demo_ids = get_existing_demo_ids()

    logger.info(
        "Found %d active demos.",
        len(existing_demo_ids),
    )

    stats = CleanupStats()

    orphaned = collect_orphan_directories(
        existing_demo_ids,
        stats,
    )

    logger.info(
        "Found %d orphaned demo directories.",
        len(orphaned),
    )

    remove_orphan_directories(
        orphaned,
        stats,
        dry_run,
    )

    print_summary(stats)

    return 1 if stats.errors else 0


# Main
def build_parser():

    parser = argparse.ArgumentParser(
        description="Cleanup orphaned demo resources."
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without deleting anything.",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging.",
    )

    return parser


def main():

    parser = build_parser()

    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    try:

        exit_code = run_cleanup(
            dry_run=args.dry_run,
        )

    except KeyboardInterrupt:

        logger.warning("Interrupted by user.")

        exit_code = 130

    except Exception:

        logger.exception("Cleanup failed.")

        exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()