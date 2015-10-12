#!/bin/sh
# Write Noise Curve Script
#
# Copyright(c) 2011 Miguel Colom
# miguel.colom@cmla.ens-cachan.fr
#
# This file may be licensed under the terms of of the
# GNU General Public License Version 2 (the ``GPL'').

file=$1
columns=$2

x1=$3
x2=$4
y1=$5
y2=$6

output=$7

gnu_nox=/usr/bin/gnuplot-nox
gnu_no_nox=/usr/bin/gnuplot
executable="NOT_FOUND"

if [ -f $gnu_nox ]; then
  executable=$gnu_nox
else
  if [ -f $gnu_no_nox ]; then
    executable=$gnu_no_nox
  fi
fi

if [ "$executable" = "NOT_FOUND" ]; then
  echo "ERROR: gnuplot executable not found"
  exit 1
fi

$executable << EOF
reset

set terminal png size 832,624
set output "$output"

set xlabel "Mean"
set ylabel "Standard deviation"

set key outside

set title "Noise curve"

set grid

set xr [$x1:$x2]
set yr [$y1:$y2]

if (${columns} == 3) \
  plot "${file}" using 1:4 title "" with linespoints lt 1 pt 6 pointsize 1.5, \
  "" using 2:5 title "" with linespoints lt 2 pt 6 pointsize 1.5, \
  "" using 3:6 title "" with linespoints lt 3 pt 6 pointsize 1.5; \
else \
  plot "${file}" using 1:2 title "" with linespoints lt 3 pt 6 pointsize 1.5;
exit
EOF

