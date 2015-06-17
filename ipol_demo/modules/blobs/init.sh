#!/bin/bash

# THIS SCRIPT DELETE TMP DIRECTORY AND FINAL DIRECTORY IMAGES
# FROM CONFIGURATION FILE GIVEN IN PARAMATER
# CALL SCRIPT DATABASE

SCRIPT=`readlink -f "$0"`
PATH_INIT=`dirname $SCRIPT`
DB_SCRIPT='/db/script.sh'
PATH_SCRIPT=$PATH_INIT$DB_SCRIPT

if [[ "$#" -ne 1 || ! -f $1 ]]
then
    echo "Usage: $0 file.conf"
    exit
fi

echo "Script $0 processing"

mapfile < $1
SIZEFILE=`wc -l < $1`

i=0
while [[ "$i" != "$SIZEFILE" ]]
do
    if [[ "${MAPFILE[i]}" =~ "tmp.dir" ]]
    then
	TMP=${MAPFILE[i]:11:-2}
    elif [[ "${MAPFILE[i]}" =~ "final.dir" ]]
    then
	INPUT_DIR=${MAPFILE[i]:13:-2}
    fi
    (( i++ ))
done

if [[ "$INPUT_DIR" != "" ]]
then
    PATH_DIR=$PATH_INIT$INPUT_DIR
    PATH_TMP=$PATH_INIT$TMP
fi

if [ -e $PATH_DIR ]
then
    /bin/rm -r $PATH_DIR
    /bin/rm -r $PATH_TMP
fi

/bin/bash $PATH_SCRIPT

echo "Script $0 ending"
