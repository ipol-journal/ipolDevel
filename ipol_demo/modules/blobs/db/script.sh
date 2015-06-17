#!/bin/bash

# THIS SCRIPT DELETE DATABASE (*.db)
# CREATE A NEW DATABASE FROM SQL FILE
# COPY THE NEW DB FILE IN CURRENT DIRECTORY

echo "Script $0 processing"

SCRIPT=`readlink -f "$0"`
PATH_SCRIPT=`dirname $SCRIPT`
DB='/blob.db'
SQL='/blob.sql'
PATH_DB=$PATH_SCRIPT$DB
PATH_SQL=$PATH_SCRIPT$SQL
DEST=${PATH_SCRIPT%/*}


if [ -f $PATH_DB ]
then
    /bin/rm $PATH_DB
fi

/usr/bin/sqlite3 $PATH_DB < $PATH_SQL
/bin/cp $PATH_DB $DEST

echo "Script $0 ending"
