#!/bin/sh -e
#
# System-V init script to start or stop the IPOL demo service
#

### BEGIN INIT INFO
# Provides:          ipol-demo
# Required-Start:    $all
# Required-Stop:     $all
# Should-Start:      
# Should-Stop:       
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: start and stop the IPOL demo service
# Description:       
### END INIT INFO

BASEDIR=/srv/ipol
SCRIPT=${BASEDIR}/demo/demo.py
SCRIPTNAME=${SCRIPT##*/}
SUID=www-data
PIDFILE_RUN=/var/run/ipol_demo_run.pid
PIDFILE_BUILD=/var/run/ipol_demo_build.pid

test -x $SCRIPT || exit 0

. /lib/lsb/init-functions

export CCACHE_DIR=/tmp/.ccache

case "$1" in
    build)
	# (re)build command-line binaries
	log_daemon_msg "(Re)building IPOL demos (in background)"
	log_progress_msg "${SCRIPT} build ... "
	# start the process in the background as www-data
	# save the PID
	# fail (exit 1) if it is still running from a previous invocation
	# we expect the process to die by itself in a reasonable time
	/sbin/start-stop-daemon --start \
	    --startas ${SCRIPT} \
	    --pidfile ${PIDFILE_BUILD} --make-pidfile \
	    --user ${SUID} --chuid ${SUID} \
	    --background -- build
	log_end_msg 0
    ;;

    start)
        # set memory limits
        ulimit -s 16384   # 16M stack (guidelines say 8M)
        ulimit -v 4194304 # 4G  total (guidelines say 1G)
        # set process limits
        # WARNING: this is sh (dash) syntax, NOT bash syntax
        ulimit -p 1024    # avoid fork bombs
        # start the web service
	log_daemon_msg "Starting IPOL demo"
	log_progress_msg "${SCRIPT} run ... "
	# start the process in the background as www-data
	# save the PID
	# do nothing if it is already running
	/sbin/start-stop-daemon --start --oknodo \
	    --startas ${SCRIPT} \
	    --pidfile ${PIDFILE_RUN} --make-pidfile \
	    --user ${SUID} --chuid ${SUID} \
	    --background -- run
	sleep 1
	PID=$(cat ${PIDFILE_RUN})
	if [ -f /proc/$PID/stat ]; then # is running
	    log_end_msg 0
            $0 build # (re)build demos in background
	else                            # failed to start, error
	    log_end_msg 1
	    rm ${PIDFILE_RUN}
	    exit 1
	fi
    ;;

    stop)
	# stop the web service
	log_daemon_msg "Stopping IPOL demo ... "
	if [ ! -f ${PIDFILE_RUN} ]; then # no pidfile
	    log_end_msg 0
	    log_progress_msg "PID file not found ... "
	    log_end_msg 0
	    exit 1
	fi
	PID=$(cat ${PIDFILE_RUN})
	log_progress_msg "PID ${PID} ... "
	/sbin/start-stop-daemon --stop --oknodo \
	    --pidfile ${PIDFILE_RUN} \
	    --user ${SUID} \
	    --retry 5
	if [ -f /proc/$PID/stat ]; then # failed to stop, error
	    log_end_msg 1
	    exit 1
	else                            # is stopped
	    log_end_msg 0
	    rm ${PIDFILE_RUN}
	fi
    ;;

    status)
	# check if it is running
	if [ -f ${PIDFILE_RUN} ]; then
	    PID=$(cat ${PIDFILE_RUN})
	    if [ -f /proc/$PID/stat ]; then
		echo "running"
	    else
		echo "not running"
		rm ${PIDFILE_RUN}
	    fi
	else
	    echo "probably not running (no PID file)"
	fi
	# check if it is running
	if [ -f ${PIDFILE_BUILD} ]; then
	    PID=$(cat ${PIDFILE_BUILD})
	    if [ -f /proc/$PID/stat ]; then
		echo "building"
	    else
		echo "not building"
		rm ${PIDFILE_BUILD}
	    fi
	else
	    echo "probably not building (no PID file)"
	fi
    ;;

    restart)
        $0 stop
        $0 start
    ;;

    *)
	log_action_msg "Usage: $0 {start|stop|restart|status|build}"
	log_end_msg 1
	exit 1
    ;;
esac

exit 0
