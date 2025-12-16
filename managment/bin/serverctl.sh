#!/bin/bash
#
# $Header: 
#
# serverctl.sh
#
# Copyright (c) 2018, 2021, Oracle and/or its affiliates. 
#
#    NAME
#      serverctl.sh - command line tool to manipulate managment Server
#
#    DESCRIPTION
#      This script can start, stop, status and restart the managment Server
#
#    NOTES
#      Usage: $0 {start {-da} |stop {-fk}|restart {-da} |status}
#
#    MODIFIED   (DD/MM/YY)
#      hgaldame    26/05/21 - 32926864 - start of remotemgmtagent fails with
#                             port already in use
#      jesandov    26/03/19 - Creation of the file for exacloud unit test
#

abspath=$( cd ${0%/*} && echo $PWD/${0##*/} )
self=$( dirname $abspath )
port=$( cat $self/../config/basic.conf | grep "port" | awk -F":" '{print $2}' | tr -d " "| tr -d "'" | tr -d '"' | tr -d ",")

function portstatus {
    netstat -tulpn 2>&1 | grep LISTEN | awk '{print $4}'| grep ":$port" > /dev/null
    return $?
}

function startcmd {
    portstatus 
    if [ $? == 0 ]; then
        echo "Port already in use, Exiting"
        exit 1
    else

        pythonpath=${self}/../../../bin/python
        if [ "$1" == "-da" ]; then
            ${pythonpath} ${self}/../src/ManagmentServer.py -da

            portstatus
            if [ $? == 0 ]; then
                echo "Server has started"
            else
                echo "Server could not start, check the log for information"
            fi

        else
            echo "Server has started"
            ${pythonpath} ${self}/../src/ManagmentServer.py

        fi
    fi
}

function stopcmd {
    portstatus 
    if [ $? != 0 ]; then
        echo "Port not in use, Exiting"
        exit 2
    else
        #TODO: Implement clean shutdown
        ps -ax | grep "${self}" | awk '{print $1}' | xargs kill -9 > /dev/null 2>&1
        rc=0

        (find ${self}/../../ | grep ".pyc$" | xargs rm) 2>&1 > /dev/null
        if [ $rc == 0 ]; then
            echo "Server has stopped"
        else
            echo "Could not stop server"
            exit 3
        fi
    fi
}

function statuscmd {
    portstatus 
    if [ $? != 0 ]; then
        echo "Server is not running"
        return 1
    else
        echo "Server is running"
        return 0
    fi
}

function restartcmd {
    statuscmd

    if [ $? != 0 ]; then
        startcmd $1
    else
        stopcmd
        startcmd $1
    fi
}

#main function
case "$1" in 
    start)
        startcmd $2
        ;;

    stop)
        stopcmd $2
        ;;

    status)
        statuscmd
        ;;

    restart)
        restartcmd $2
        ;;
    *)
        echo $"Usage: $0 {start {-da} |stop |restart {-da} |status}"
        exit 7
esac

exit 0

