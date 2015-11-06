#!/bin/bash

# usage:
# /path/to/.sh method parameter

# IMPLICIT INPUT FILES
#  t.tiff (OP)
#  stuff_clg.tiff
#  stuff_clg_fmt.tiff (OP)
#
# IMPLICIT OUTPUT FILES
#
#  t.method.parameter.png
#  stuff_clg.method.parameter.png
#  colorwheel.method.parameter.png
#  stuff_clg_fmt.method.parameter.png (OP)
#

set -e

testex() {
	if which $1 > /dev/null ; then
		echo > /dev/null
	else
		echo "ERROR: executable file $1 not available" >&2
		exit 1
	fi
}

usgexit() {
	echo -e "usage:\n\t `basename $0` [nico|luis|warp|ldof...]"
	rm -rf $TPD
	exit 1
}

echo VSTUFF ARGC: $#
echo VSTUFF ARGV: $*

# check input
if [ $# != "2" ]; then
	usgexit
fi

echo VSTUFF ARGS: $*

COLORWHEEL=$PWD/../../input/colorwheel.tiff


if test -f t.tiff; then
	HASTRUTH="yes"
else
	HASTRUTH=""
fi

VMETHOD=$1
VPARAM=$2

FTYPE=clg
P=stuff_clg
S=${VMETHOD}.${VPARAM}
S=${VMETHOD}.1

if test $HASTRUTH; then
	COMPUTED_RANGE=`fnorm t.tiff -|imprintf "%a" -`
else
	COMPUTED_RANGE=`imprintf "%q[99]" ${P}_abs.tiff`
fi
echo $COMPUTED_RANGE > computed_range.txt


case "$VMETHOD" in
"ipol")
	#VIEWFLOWPARAM=-$COMPUTED_RANGE
	VIEWFLOWPARAM=1
	viewflow $VIEWFLOWPARAM ${P}.tiff ${P}.${S}.png
	if test $HASTRUTH; then
		viewflow $VIEWFLOWPARAM t.tiff t.${S}.png
		viewflow $VIEWFLOWPARAM ${P}_fmt_nonan.tiff ${P}_fmt.${S}.png
	fi
	viewflow 1 $COLORWHEEL | downsa v 2 | qeasy 0 255 - cw.${S}.png
	;;
"ipoln")
	VIEWFLOWPARAM=$COMPUTED_RANGE
	viewflow $VIEWFLOWPARAM ${P}.tiff ${P}.${S}.png
	if test $HASTRUTH; then
		viewflow $VIEWFLOWPARAM t.tiff t.${S}.png
		viewflow $VIEWFLOWPARAM ${P}_fmt_nonan.tiff ${P}_fmt.${S}.png
	fi
	viewflow 1 $COLORWHEEL | downsa v 2 | qeasy 0 255 - cw.${S}.png
	;;
"mid")
	export MRANGE=${COMPUTED_RANGE}
	viewflow nan ${P}.tiff ${P}.${S}.png
	if test $HASTRUTH; then
		viewflow nan t.tiff t.${S}.png
		viewflow nan ${P}_fmt_nonan.tiff ${P}_fmt.${S}.png
	fi
	MRANGE=1.0 viewflow nan $COLORWHEEL | downsa v 2 | qeasy 0 255 - cw.${S}.png
	;;
"arrows")
	export MRANGE=${COMPUTED_RANGE}
	APA=0.4
	GSP=20
	flowarrows $APA $GSP ${P}.tiff | qeasy 0 255 - ${P}.${S}.png
	if test $HASTRUTH; then
		flowarrows $APA $GSP t.tiff | qeasy 0 255 - t.${S}.png
		flowarrows $APA $GSP ${P}_fmt_nonan.tiff | qeasy 0 255 - ${P}_fmt.${S}.png
	fi
	flowarrows 0.1 19 $COLORWHEEL | downsa v 2 | qeasy 0 255 - cw.${S}.png
	#MRANGE=1.0 viewflow nan $COLORWHEEL | downsa v 2 | qeasy 0 255 - cw.${S}.png
	;;
"gridback")
	GRIDSPACE=10
	plambda a.png "x del :i $GRIDSPACE fmod 0 = :j $GRIDSPACE fmod 0 = + -1 *" | qeasy -2 0 - grid.png
	backflow ${P}.tiff grid.png ${P}.${S}.png
	if test $HASTRUTH; then
		backflow t.tiff grid.png t.${S}.png
		backflow ${P}_fmt_nonan.tiff grid.png ${P}_fmt.${S}.png
	fi
	plambda $COLORWHEEL "x del :i $GRIDSPACE fmod 0 = :j $GRIDSPACE fmod 0 = + -1 *" | qeasy -2 0 - cgrid.png
	plambda $COLORWHEEL "x 16 *" | backflow - cgrid.png cw.${S}.png
	;;
esac

cp ${P}.${S}.png ${P}.png
