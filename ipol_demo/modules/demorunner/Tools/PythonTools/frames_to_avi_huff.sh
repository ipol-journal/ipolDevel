#!/bin/sh

################################################
#  Convert a list of frames into an MP4 video  #
################################################

# Example:
# ./frames_to_avi_huff.sh input_0/frame_%05d.png 25 spiderman.avi

if [ "$#" -ne 3 ]; then
    echo "Illegal number of parameters"
    exit 1
fi

frame_filename=$1 # Format of the frames. For example: frame_%05d.png
fps=$2 # Frames per second
output=$3 # Output AVI filename

# -y: overwrite output without asking
# -an: drop audio
avconv -framerate ${fps} -f image2 -i ${frame_filename} -y -an -c:v huffyuv -pix_fmt rgb24 ${output}
