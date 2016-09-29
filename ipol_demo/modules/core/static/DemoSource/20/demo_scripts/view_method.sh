#!/bin/bash

# usage:
# /path/to/.sh method parameter

# IMPLICIT INPUT FILES
#  input_2.tiff (OP)
#  stuff_tvl1.tiff
#  stuff_tvl1_fmt.tiff (OP)
#
# IMPLICIT OUTPUT FILES
#
#  t.method.parameter.png
#  stuff_tvl1.method.parameter.png
#  colorwheel.method.parameter.png
#  stuff_tvl1_fmt.method.parameter.png (OP)
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

echo "BASH_SOURCE path = `dirname $BASH_SOURCE`"
COLORWHEEL=`dirname "$BASH_SOURCE"`/colorwheel.tiff


if test -f input_2.tiff; then
	HASTRUTH="yes"
else
	HASTRUTH=""
fi

VMETHOD=$1
VPARAM=$2

FTYPE=phs
P=stuff_phs
S=${VMETHOD}.${VPARAM}
S=${VMETHOD}.1

if test $HASTRUTH; then
	COMPUTED_RANGE=`fnorm input_2.tiff -|imprintf "%a" -`
else
	COMPUTED_RANGE=`imprintf "%q[99]" ${P}_abs.tiff`
fi
echo $COMPUTED_RANGE > computed_range.txt


case "$VMETHOD" in
"ipol")
	#VIEWFLOWPARAM=-$COMPUTED_RANGE
	VIEWFLOWPARAM=-1
	viewflow $VIEWFLOWPARAM ${P}.tiff ${P}.${S}.png
	if test $HASTRUTH; then
		viewflow $VIEWFLOWPARAM input_2.tiff t.${S}.png
		viewflow $VIEWFLOWPARAM ${P}_fmt_nonan.tiff ${P}_fmt.${S}.png
	fi
	viewflow -1 $COLORWHEEL | downsa v 2 | qeasy 0 255 - cw.${S}.png
	;;
"ipoln")
	VIEWFLOWPARAM=$COMPUTED_RANGE
	viewflow $VIEWFLOWPARAM ${P}.tiff ${P}.${S}.png
	if test $HASTRUTH; then
		viewflow $VIEWFLOWPARAM input_2.tiff t.${S}.png
		viewflow $VIEWFLOWPARAM ${P}_fmt_nonan.tiff ${P}_fmt.${S}.png
	fi
	viewflow 1 $COLORWHEEL | downsa v 2 | qeasy 0 255 - cw.${S}.png
	;;
"mid")
	export MRANGE=${COMPUTED_RANGE}
	viewflow nan ${P}.tiff ${P}.${S}.png
	if test $HASTRUTH; then
		viewflow nan input_2.tiff t.${S}.png
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
		flowarrows $APA $GSP input_2.tiff | qeasy 0 255 - t.${S}.png
		flowarrows $APA $GSP ${P}_fmt_nonan.tiff | qeasy 0 255 - ${P}_fmt.${S}.png
	fi
	flowarrows 0.1 19 $COLORWHEEL | downsa v 2 | qeasy 0 255 - cw.${S}.png
	#MRANGE=1.0 viewflow nan $COLORWHEEL | downsa v 2 | qeasy 0 255 - cw.${S}.png
	;;
"gridback")
	GRIDSPACE=10
	plambda input_0.png "x del :i $GRIDSPACE fmod 0 = :j $GRIDSPACE fmod 0 = + -1 *" | qeasy -2 0 - grid.png
	backflow ${P}.tiff grid.png ${P}.${S}.png
	if test $HASTRUTH; then
		backflow input_2.tiff grid.png t.${S}.png
		backflow ${P}_fmt_nonan.tiff grid.png ${P}_fmt.${S}.png
	fi
	plambda $COLORWHEEL "x del :i $GRIDSPACE fmod 0 = :j $GRIDSPACE fmod 0 = + -1 *" | qeasy -2 0 - cgrid.png
	plambda $COLORWHEEL "x 16 *" | backflow - cgrid.png cw.${S}.png
	;;
esac

cp ${P}.${S}.png ${P}.png
