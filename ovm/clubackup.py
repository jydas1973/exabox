"""
$Header:

 Copyright (c) 2019, 2023, Oracle and/or its affiliates. 

NAME:
    RequestsBackupContext - Stores date information and presents easy to use methods for handling the request backup

FUNCTION:
    Used to habdle the request to request archive backup capability on the supervisor

NOTE:
    None

History:

    MODIFIED   (MM/DD/YY)
    ririgoye    08/30/23 - Fix redundant/deprecated mConnect calls
    ndesanto    12/14/21 - Increase coverage for ndesanto files.
    ndesanto    12/10/21 - Increase coverage on ndesanto files.
    ndesanto    08/06/19 - bug 30139439: Fixing exception when file is being updated during tar process
    ndesanto    06/24/19 - Create file
"""

import datetime
from exabox.core.Node import exaBoxNode
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogVerbose
from exabox.utils.node import connect_to_host


def backupCreateVMLogs(clu_context, dom_pairs, created_log_path, uuid):
    for _dom0, _ in dom_pairs:
        with connect_to_host(_dom0, clu_context) as _node:
            _dmesg_file_name = "/tmp/dmesg_{}_{}.txt".format(_dom0, uuid)
            _tar_file_name = "create_vm_log_{}_{}.tar.gz".format(_dom0, uuid)
            _remote_file_path = "/tmp/{}".format(_tar_file_name)
            _local_file_path = "{}/{}".format(created_log_path, _tar_file_name)
            _files_to_backup = "/var/log/cellos/* /var/log/xen/*.log /var/log/messages {}".format(_dmesg_file_name)

            _backupCreateVMLogs(_node, _dmesg_file_name, _files_to_backup, _remote_file_path, _local_file_path)

def _backupCreateVMLogs(node, dmesg_path, files_to_backup, remote_path, local_path):
    _backup_log(node.mExecuteCmd, node.mGetCmdExitStatus, node.mCopy2Local, 
                node.mGetHostname(), files_to_backup, dmesg_path, 
                remote_path, local_path)

def _backup_log(mExecute, mValidate, mCopy, hostname, files_to_backup, dmesg_path, remote_path, local_path):
    # TODO Enhance/refactor this method, testability should be done with a better node API, not by passing 
    #      functions/methods. A general purpose mock should be used instead.
    _dmesg_cmd = "dmesg > {}".format(dmesg_path)
    _, _o, _e = mExecute(_dmesg_cmd)
    if mValidate():  # pragma: no cover
        ebLogInfo("dmesg Log Backup cmd {} returned {}, error {}".format(_dmesg_cmd, str(_o.readlines()), str(_e.readlines())))
        ebLogError("dmesg Log Backup Failed Node: {} , cmd {}".format(hostname, _dmesg_cmd))
        raise ExacloudRuntimeError(0x0411, 0xA, 'dmesg Log Backup')
    else:
        _tar_cmd = "tar --warning=no-file-changed -czf {} {}".format(remote_path, files_to_backup)
        _, _o, _e = mExecute(_tar_cmd)
        if mValidate() > 1:  # pragma: no cover
            ebLogInfo("Tar Log Backup cmd {} returned {}, error {}".format(_tar_cmd, str(_o.readlines()), str(_e.readlines())))
            ebLogError("Tar Log Backup Failed Node: {} , cmd {}".format(hostname, _tar_cmd))
            raise ExacloudRuntimeError(0x0411, 0xA, 'Tar Log Backup')
        else:
            mCopy(remote_path, local_path)

            _del_cmd = "rm -f {}".format(remote_path)
            _, _o, _e = mExecute(_del_cmd)
            if mValidate():  # pragma: no cover
                ebLogInfo("Del Log Backup cmd {} returned {}, error {}".format(_del_cmd, str(_o.readlines()), str(_e.readlines())))
                ebLogError("Del Log Backup Failed Node: {} , cmd {}".format(hostname, _del_cmd))
                raise ExacloudRuntimeError(0x0411, 0xA, 'Del Log Backup')
