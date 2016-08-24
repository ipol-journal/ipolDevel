#!/bin/bash

# argument is the position of the reference image
# switch its name with input_0.png
ref=$1
if [ $ref -ne 0 ] && [ -f input_$ref.png ]
then
  mv input_0.png tmp
  mv input_$ref.png input_0.png
  mv tmp input_$ref.png
fi

# create symbolic links for all input_XX.png files as iiXX.png
for f in  `ls input_?.png`;  do ln -s  $f i0`echo $f | cut -b 7-` ; done
if [ -f input_10.png ]
then
  for f in  `ls input_??.png`; do ln -s  $f i`echo $f | cut -b 7-` ; done
fi


