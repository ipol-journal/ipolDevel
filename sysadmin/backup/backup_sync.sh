#! /bin/sh
#
# This script copies a correct (last changes and exported SQLite
# files) ipolDevel directory from Core to the remote backup destination.
#
# In order to avoid incomplete file copies, this script should be
# executed in a different day from Core's backup job.

# run as root


# DEBUG OPTIONS
#
#set -x
#alias logger="echo logger"

RSYNC_OPT="--quiet --archive --compress --delete-excluded \
           --acls --xattrs --relative"

RSYNC_SRC="\
/etc \
/root \
/home/ipol/backups/ipolDevelCopy/ipolDevel"

RSYNC_EXC="--exclude=/home/ipol/backups/ipolDevelCopy/ipolDevel/shared_folder/ \
	   --exclude=/home/ipol/backups/ipolDevelCopy/ipolDevel/ipol_demo/modules/demorunner/binaries/ \
	   --exclude=/home/ipol/.cache/ \
	   --exclude=/home/ipol/backups/ipolDevelCopy/ipolDevel/ipol_demo/modules/archive/staticData/blobs_thumbs/ \
	   --exclude=/home/ipol/backups/ipolDevelCopy/ipolDevel/ci_tests/compilation_folder/ "

RSYNC_DEST="backup-data@navy.hw.ipol.im:/srv/backup/sync/ipolcore/"

RSYNC_CMD="/usr/bin/rsync $RSYNC_OPT $RSYNC_EXC $RSYNC_SRC $RSYNC_DEST"

export RSYNC_RSH="ssh -p 2332 -i $HOME/.ssh/id_navy_backup "

echo $RSYNC_CMD --rsync-path="rsync --fake-super" \

$RSYNC_CMD --rsync-path="/usr/bin/rsync --fake-super" \
    && logger -t backup "successful sync" \
    || logger -t backup "sync failed : $RSYNC_CMD"
