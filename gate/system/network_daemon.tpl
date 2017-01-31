#!/bin/sh
#
# Start the network....
#

%### INCLUDES ###
%import os
%if not defined('settings'):
    %from gate.main.manager import settings
%end
%### BASH ###
start() {
    echo "Starting network..."
    /sbin/ifup -a
    %if settings['ip_scheme'] == 'dynamic':
    echo "IP Address will be assigned by DHCP"
    /sbin/udhcpc -b
    %else:
    echo "Assigning static IP Address: {{settings['ip_address']}}"
    /sbin/ifconfig eth0 {{settings['ip_address']}} netmask {{settings['subnet_mask']}}
    %end
}  
stop() {
    echo -n "Stopping network..."
    /sbin/ifdown -a
}
restart() {
    stop
    start
}  

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart|reload)
        restart
        ;;
    *)
        echo $"Usage: $0 {start|stop|restart}"
        exit 1
esac

exit $?

