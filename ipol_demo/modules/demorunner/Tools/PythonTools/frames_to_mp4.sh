#!/bin/sh

################################################
#  Convert a list of frames into an MP4 video  #
################################################

# https://wiki.libav.org/Snippets/avconv#Create_video_from_image_sequence

# Example:
# ./frames_to_mp4.sh input_0/frame_%05d.png 25 spiderman.mp4

if [ "$#" -ne 3 ]; then
    echo "Illegal number of parameters"
    exit 1
fi

frame_filename=$1 # Format of the frames. For example: input_0/frame_%05d.png
fps=$2 # Frames per second
output=$3 # Output MP4 filename

# High quality
#avconv -i "$1" -y -c:v libx264 -crf 1 -c:a aac -b:a 320k -strict experimental "${filename}_out.mp4"

# -y: overwrite output without asking
# -an: drop audio
#avconv -i "$1" -y -an -c:v libx264 -crf 1 "${filename}_out.mp4"
avconv -framerate ${fps} -f image2 -i ${frame_filename} -y -an -c:v libx264 -crf 1 ${output}
