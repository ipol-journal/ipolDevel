#!/bin/sh

# Run PHS algorithm with unified interface

# usage:
# RUNPHS {j|e} a b f alpha epsilon niter nwarp nscales scalestep
#         1    2 3 4 5     6       7     8     9       10

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
	echo "usage:\n\t `basename $0` {j|e} a b f alpha epsilon niter nwarp nscales scalestep"
	exit 1
}

if [ "$#" != "10" ]; then
	echo "[got $#]"
	usgexit
fi

METHOD=$1
FILEA=$2
FILEB=$3
FILEF=$4
ALPHA=$5
EPSIL=$6
NITER=$7
NWARP=$8
NSCAL=$9
SSTEP=${10}

testex phs
#testex ephs

echo "UNIFORM PHS method \"$METHOD\""
echo "\timage  A = $FILEA"
echo "\timage  B = $FILEB"
echo "\toutput F = $FILEF"
echo "\talpha    = $ALPHA"
echo "\tepsil    = $EPSIL"
echo "\tniter    = $NITER"
echo "\tnwarp    = $NWARP"
echo "\tnscal    = $NSCAL"
echo "\tsstep    = $SSTEP"

case "$METHOD" in
"j")
	ZFACT=$SSTEP
	echo "running javier's PHS (zfactor = $ZFACT)"
	phs $FILEA $FILEB $FILEF 4 5 $ALPHA $NSCAL $ZFACT $NWARP $EPSIL $NITER 1
	;;
"j3")
	ZFACT=$SSTEP
	echo "running javier's PHS (zfactor = $ZFACT)"
  echo "phs $FILEA $FILEB $FILEF 8 $ALPHA $NSCAL $ZFACT $NWARP $EPSIL $NITER 0"
	phs $FILEA $FILEB $FILEF 8 $ALPHA $NSCAL $ZFACT $NWARP $EPSIL $NITER 0
	;;
"e")
	ZFACT=`echo "1.0/$SSTEP" | gp -f -q`
	echo "running enric's PHS"
	export PRESMOOTH=0.8
	NWARPS=$NWARP ephs $FILEA $FILEB $ALPHA $NITER $EPSIL $SSTEP $NSCAL $FILEF 2>&1
	;;
*)
	echo "unrecognized method \"$METHOD\""
	usgexit
	;;
esac
