#!/bin/bash

# Very simple script to make backups
# Miguel Colom, 2016

baksDir="/home/ipol/backups"
orig="/home/ipol/ipolDevel"

filename=$(date +"backup_%m-%d-%Y.tgz")
fullFilename=${baksDir}/${filename}

mkdir -p ${baksDir}
tar -zcvf ${fullFilename} $orig

