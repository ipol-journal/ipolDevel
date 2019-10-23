#!/bin/bash

# This script is ment to run in a cronjob. 
# It will synchronize ipolcore backups to dr1 server

backupsLocation=$HOME"/backups/"
dst=$HOME"/backups"

rsync -azP --delete ${backupsLocation} ipol@ipol_dr1:${dst}
