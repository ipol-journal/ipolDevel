#!/bin/sh

################################################
#  Convert a video into a browser-viewable MP4 #
################################################

# https://thehelloworldprogram.com/web-development/encode-video-and-audio-for-html5-with-avconv/

# Example:
# ./website_mp4.sh spiderman.wmv spiderman.mp4

if [ "$#" -ne 2 ]; then
    echo "Illegal number of parameters"
    exit 1
fi

# Extract filename without extension
filename=$(basename "$1")
filename="${filename%.*}"

output=$2

# High quality
#avconv -i "$1" -y -c:v libx264 -crf 1 -c:a aac -b:a 320k -strict experimental "${filename}_out.mp4"

# -y: overwrite output without asking
# -an: drop audio
avconv -i "$1" -y -an -c:v libx264 -crf 1 "$2"
