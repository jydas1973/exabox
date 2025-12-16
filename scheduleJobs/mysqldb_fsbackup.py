#!/bin/python
#
# $Header: ecs/exacloud/exabox/scheduleJobs/mysqldb_fsbackup.py /main/1 2023/05/08 07:24:53 dekuckre Exp $
#
# mysqldb_fsbackup.py
#
# Copyright (c) 2023, Oracle and/or its affiliates.
#
#    NAME
#      mysqldb_fsbackup.py - <one-line expansion of the name>
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
from exabox.core.Context import get_gcontext
from exabox.scheduleJobs.utils import mExecuteLocal
from exabox.log.LogMgr import ebLogInit, ebLogInfo, ebLogError
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.core.Context import get_gcontext
from exabox.core.Core import exaBoxCoreInit
import os

def backupDBToFS():
    exaBoxCoreInit({})
    _options = get_gcontext().mGetArgsOptions()
    ebLogInit(get_gcontext(), _options)                                                                                                                                   
    _backupfile = get_gcontext().mCheckConfigOption("mysql_fsbackup")
    ebLogInfo(f"Backup MySQL DB to filesystem {_backupfile}")
    try:
        if os.path.exists(_backupfile):
            _rc, _, _out, _err = mExecuteLocal(f"/bin/cp {_backupfile} {_backupfile}_bk")
            if _rc != 0:
                ebLogError(f"Return Code: {_rc}, Error: {_out}")

        _rc, _, _out, _err = mExecuteLocal(f"bin/mysql --backup {_backupfile}")
        if _rc != 0:
            ebLogError(f"Return Code: {_rc}, Error: {_out}")

    except Exception as e:
        _msg = f"Failed to backup mysql DB to filesystem: {e}"
        ebLogError(_msg)
        raise ExacloudRuntimeError(_msg) from e

if __name__ == '__main__':
    backupDBToFS()

