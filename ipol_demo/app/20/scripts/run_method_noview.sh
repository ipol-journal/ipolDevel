#!/bin/bash

# usage:
# /path/to/stuff.sh alpha niter

# IMPLICIT INPUT FILES
#  input_0.png
#  input_1.png
#  input_2.tiff (OP)
#
# IMPLICIT OUTPUT FILES
#
#  stuff_tvl1.{tiff,png}       "F"
#  stuff_tvl1_div.{tiff,png}   "divF"
#  stuff_tvl1_abs.{tiff,png}   "|F|"
#  stuff_tvl1_inv.png          "F*B"
#  stuff_tvl1_apinv.png        "(A+F*B)/2"
#  stuff_tvl1_aminv.{tiff,png} "A-F*B"
#  stuff_tvl1_fmt.{tiff,png}   "F-T"
#  stuff_tvl1_afmt.{tiff,png}  "|F-T|"
#

DIVRANG=4
FLORANG=10
IDIFRAD=50
FDIFRAD=4

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

echo STUFF ARGC: $#
echo STUFF ARGV: $*

# check input
if [ $# != "7" ]; then
	usgexit
fi

echo STUFF ARGS: $*

test -f input_0.png || (echo "I need a file \"input_0.png\"!" ; exit 1)
test -f input_1.png || (echo "I need a file \"input_1.png\"!" ; exit 1)
#test -f input_2.tiff || (echo "I need a file \"input_2.tiff\"!" ; exit 1)
if test -f input_2.tiff; then
	HASTRUTH="yes"
else
	HASTRUTH=""
fi

mv input_0.png orig.input_0.png
mv input_1.png orig.input_1.png
unalpha orig.input_0.png input_0.png
unalpha orig.input_1.png input_1.png

if test $HASTRUTH; then
	mv input_2.tiff orig.input_2.tiff
	plambda orig.input_2.tiff "x[0] x[1] hypot 1000 > >1 <1 nan x[0] if <1 nan x[1] if join" > input_2.tiff
fi

NPROCS=$1
ALPHA=$2
EPSIL=$3
NITER=$4
NWARP=$5
NSCAL=$6
SSTEP=$7

export MRANGE=4
VIEWFLOWPARAM=nan

FTYPE=phs
P=stuff_phs

echo "NPROCS = ${NPROCS}"
echo "ALPHA = ${ALPHA}"
echo "EPSIL = ${EPSIL}"
echo "NITER = ${NITER}"
echo "NWARP = ${NWARP}"
echo "NSCAL = ${NSCAL}"
echo "SSTEP = ${SSTEP}"

echo "FTYPE = ${FTYPE}"
echo "P = ${P}"

#if [ $FTYPE = "truth" ]; then
#	cp input_2.tiff ${P}.tiff
#else
#	flowany.sh ${FTYPE} input_0.png input_1.png > ${P}.tiff
#fi

testex hs_uniform.sh

#jzach 1 input_0.png input_1.png $TAU $LAMBDA $THETA $NSCALES 0.5 $NITER ${P}.tiff 0
#echo /usr/bin/time -f "stufftime %e s" tvl1flow $NPROCS input_0.png input_1.png $TAU $LAMBDA $THETA $NSCALES 0.5 $NWARPS $EPSILON ${P}.tiff 0
export OMP_NUM_THREADS=$NPROCS
/usr/bin/time -f "stufftime %e s" hs_uniform.sh j3 input_0.png input_1.png ${P}.tiff $ALPHA $EPSIL $NITER $NWARP $NSCAL $SSTEP 2> ${P}.stime
cat ${P}.stime | /bin/grep stufftime  | cut -c11- > ${P}.time

iion ${P}.tiff ${P}.uv
iion ${P}.tiff ${P}.flo


#hs $NITER $ALPHA input_0.png input_1.png ${P}.tiff

#  stuff_X.{tiff,png}       "F"
#  stuff_X_div.{tiff,png}   "divF"
#  stuff_X_abs.{tiff,png}   "|F|"
#  stuff_X_inv.png          "F*B"
#  stuff_X_apinv.png        "(A+F*B)/2"
#  stuff_X_aminv.{tiff,png} "A-F*B"
#  stuff_X_ofce.png         "|grad(A)*F + dA/dt|"

flowdiv ${P}.tiff ${P}_div.tiff
qeasy -$DIVRANG $DIVRANG  ${P}_div.tiff ${P}_div.png
flowgrad ${P}.tiff ${P}_grad.tiff
plambda ${P}_grad.tiff "x[0] x[1] hypot x[2] x[3] hypot join" | viewflow 10 - ${P}_grad.png
fnorm ${P}.tiff ${P}_abs.tiff
if test $HASTRUTH; then
	export MRANGE=`fnorm input_2.tiff -|imprintf "%a" -`
	#viewflow $VIEWFLOWPARAM input_2.tiff t.png
else
	export MRANGE=`imprintf "%q[99]" ${P}_abs.tiff`
fi
if test $COCOCOLORS; then
	export $VIEWFLOWPARAM=-$MRANGE
fi
FLORANG=$MRANGE
qeasy 0 $FLORANG ${P}_abs.tiff ${P}_abs.png
backflow ${P}.tiff input_1.png ${P}_inv.tiff; qeasy 0 255 ${P}_inv.tiff ${P}_inv.png
plambda input_0.png ${P}_inv.png "x y + 0 512 qe" | iion - PNG:- > ${P}_apinv.png
plambda input_0.png ${P}_inv.tiff "x y -" |tee ${P}_aminv.txt | qeasy -${IDIFRAD} ${IDIFRAD}  |iion - ${P}_aminv.png
#viewflow $VIEWFLOWPARAM ${P}.tiff ${P}.png
#ofc input_0.png input_1.png ${P}.tiff | plambda - "x fabs" | qeasy 0 100 | pnmtopng > ${P}_ofce.png


#  stuff_X_fmt.{tiff,png}   "F-T"
#  stuff_X_afmt.{tiff,png}  "|F-T|"
#  stuff_X_aerr.png  "angle(F,T)"

if test $FTYPE != "truth" && test $HASTRUTH; then
	plambda ${P}.tiff input_2.tiff "x y -" > ${P}_fmt.tiff
	plambda ${P}_fmt.tiff "x x = x 0 0 join if" > ${P}_fmt_nonan.tiff
	#viewflow $VIEWFLOWPARAM ${P}_fmt.tiff ${P}_fmt.png
	fnorm ${P}_fmt.tiff ${P}_afmt.tiff
	qeasy 0 $FDIFRAD ${P}_afmt.tiff ${P}_afmt.png
	plambda input_2.tiff ${P}.tiff "x[0] y[0] * x[1] y[1] * 1 + + x[0] x[1] 1 hypot hypot y[0] y[1] 1 hypot hypot * / acos pi / 180 *" | tee ${P}_aerr.txt | qeasy 0 180 - ${P}_aerr.png
fi

if [ $FTYPE == "truth" ]; then
	SIXE_BACK=`imprintf "%e %r" ${P}_aminv.txt`
	SIXE_EUCL="0 0"
	SIXE_ANGL="0 0"
else
	SIXE_BACK=`imprintf "%e %r" ${P}_aminv.txt`
	if test $HASTRUTH; then
		SIXE_EUCL=`imprintf "%e %r" ${P}_afmt.tiff`
		SIXE_ANGL=`imprintf "%e %r" ${P}_aerr.txt`
	else
		SIXE_EUCL="nan nan"
		SIXE_ANGL="nan nan"
	fi
fi

echo "$SIXE_BACK $SIXE_EUCL $SIXE_ANGL" > sixerror_$FTYPE.txt

#flowany.sh $FTYPE input_0.png input_1.png > f.tiff
#viewflow -1 f.tiff f.png
#flowdiv f.2d
