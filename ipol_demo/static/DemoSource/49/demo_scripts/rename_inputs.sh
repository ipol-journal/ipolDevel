#!/bin/bash

# create symbolic links for all input_XX.png files as iiXX.png

for f in  `ls input_?.png`;  do ln -s  $f ii`echo $f | cut -b 7-` ; done
if [ -f input_10.png ]
then
  for f in  `ls input_??.png`; do ln -s  $f ii`echo $f | cut -b 7-` ; done
fi
