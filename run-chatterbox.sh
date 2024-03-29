#!/bin/sh
### BEGIN INIT INFO
# Provides:          chatterboxd
# Required-Start:    $local_fs $remote_fs $syslog $network $named $portmap $time
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: run chatterbox daemon
# Description:       chatterbox is a Python program that interconnects the PLCnext
#					 runtime environment with a remote MQTT broker.
### END INIT INFO

DIR=/opt/plcnext/chatterbox/
DAEMON=$DIR/main.py
DAEMON_NAME=chatterboxd
DAEMON_OPTS=""

# Run as root because other users will not have access to PLCnext's persistent storage areas.
DAEMON_USER=root
# The process ID of the script when it runs is stored here:
PIDFILE=/var/run/$DAEMON_NAME.pid

do_start () {
	echo -n "Starting chatterboxd: "
    start-stop-daemon --start --quiet --background --pidfile $PIDFILE --make-pidfile --chuid $DAEMON_USER --startas $DAEMON -- $DAEMON_OPTS
	RETVAL=$?
    if [ $RETVAL -eq 0 ] ; then
        echo "OK"
    else
        echo "FAIL"
    fi
}
do_stop () {
    echo -n "Stopping chatterboxd: "
    start-stop-daemon --stop --quiet --pidfile $PIDFILE
    RETVAL=$?
    if [ $RETVAL -eq 0 ] ; then
        echo "OK"
    else
        echo "FAIL"
    fi
}
case "$1" in
    start|stop)
        do_${1}
        ;;
    restart|reload|force-reload)
        $0 stop && sleep 1 && $0 start
        ;;
    status)
        status_of_proc "$DAEMON_NAME" "$DAEMON" && exit 0 || exit $?
        ;;
    *)
        echo "Usage: /etc/init.d/$DAEMON_NAME {start|stop|restart|status}"
        exit 1
        ;;
esac

exit 0
