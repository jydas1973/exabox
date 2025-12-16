#!/bin/python
#
# $Header: ecs/exacloud/exabox/scheduleJobs/utils.py /main/1 2023/05/08 07:24:53 dekuckre Exp $
#
# utils.py
#
# Copyright (c) 2023, Oracle and/or its affiliates.
#
#    NAME
#      utils.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    dekuckre    03/27/23 - Creation
#
import shlex
import subprocess
from  subprocess import PIPE
from exabox.log.LogMgr import ebLogInit, ebLogInfo

def mExecuteLocal(aCmd, aCurrDir=None, aStdIn=PIPE, aStdOut=PIPE, aStdErr=PIPE):
    ebLogInfo(f"Executing Cmd: {aCmd}")
    _args = shlex.split(aCmd)
    _current_dir = aCurrDir
    _stdin = aStdIn
    _std_out = aStdOut
    _stderr = aStdErr
    _proc = subprocess.Popen(_args, stdin=_stdin, stdout=_std_out, stderr=_stderr, cwd=_current_dir)
    _std_out, _std_err = _proc.communicate()
    _rc = _proc.returncode
    return _rc, None, _std_out, _std_err

