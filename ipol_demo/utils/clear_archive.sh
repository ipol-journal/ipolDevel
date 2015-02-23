#!/bin/bash
#
# Delete private archive data.


#### ABORT EARLY

HOSTNAME=$( hostname )
if [ "x$HOSTNAME" != "xgreen" ]; then
    echo "This script is made to run only on the IPOL demo server."
    echo "Aborting."
    exit 1
fi

#### SETTINGS

set -e # halt on error
set -x # trace

DEMO_DIR=/srv/ipol/demo

#### FUNCTIONS

# clear_record app key
clear_record() {
    APP="$1"
    KEY="$2"
    DB="$DEMO_DIR/app/$APP/archive/index.db"
    KEY_DIR="$DEMO_DIR/app/$APP/archive/${KEY::2}/${KEY:2}/"

    rm -rf $KEY_DIR
    sqlite3 $DB "DELETE FROM buckets WHERE key == \"$KEY\";"
}

# clear_archive app
clear_archive() {
    APP="$1"
    DB="$DEMO_DIR/app/$APP/archive/index.db"

    # first test if the table exists
    if sqlite3 $DB "SELECT key FROM buckets LIMIT 1;"; then
	sqlite3 $DB "SELECT key FROM buckets WHERE public == 0;" \
	    > /tmp/$APP.keys # dump to avoid locked tables
	cat /tmp/$APP.keys \
	    | while read KEY; do
	    clear_record "$APP" "$KEY"
	done
	rm -f /tmp/$APP.keys
    fi
}

# clear_all
clear_all() {
    find $DEMO_DIR/app/ -maxdepth 1 -mindepth 1 -type d \
	| while read APP_DIR; do
	APP=${APP_DIR##*/}
	clear_archive "$APP"
    done
}

#### DO STUFF

clear_all


