#!/bin/bash

# pdflatex compilation report
# Miguel Colom, 2016

me=$(whoami)
docsDir="/home/${me}/ipolDevel/doc"
report="/home/${me}/ipolDevel/ci_tests/pdflatex_report.txt"
files="control_panel/control_panel.tex ddl/ddl.tex system/ipol.tex"

send=0

#truncate -s 0 ${report}
today=$(date)
echo "IPOL pdflatex test on ${today}" > ${report}
echo >> ${report}

# PyLint test on each IPOL module
for file in ${files}
    do
    cd $(dirname ${docsDir}/${file})
    
    pdflatex -halt-on-error ${docsDir}/${file} > $(dirname ${report})/pdflatex_tmp.txt
    if [ $? != 0 ] ; then
        echo "*** Failed compilation of ${docsDir}/${file}:" >> ${report}
        cat pdflatex_tmp.txt >> ${report}
        echo >> ${report}
        send=1
    fi    
done

# Send email only if errors
if [ ${send} != 0 ] ; then
    # Send report by email
    sendTo=$(cat /home/ipol/ipolDevel/ci_tests/send_to.txt)
    echo "pdflatex doc compilation report" | mutt -a ${report} -s "[ipolDevel] CI test: pdflatex" -- ${sendTo}
fi    
