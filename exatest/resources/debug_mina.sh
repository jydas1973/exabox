#!/bin/sh
#
# $Header: ecs/exacloud/exabox/exatest/resources/debug_mina.sh /main/1 2025/01/07 14:09:31 jesandov Exp $
#
# debug_mina.sh
#
# Copyright (c) 2025, Oracle and/or its affiliates. 
#
#    NAME
#      debug_mina.sh - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    01/06/25 - Creation
#

#!/bin/bash
thisdir=`dirname $0`
. ./jre

#add more stack for xslt process
$JRE_PATH/java -cp .:Lib/*:out/*:properties/:config/*: org.apache.sshd.cli.client.SshClientMain {_debug} -i {_keyfile} {_user}@{_host} {_cmd}
STAT=$?
exit $STAT
