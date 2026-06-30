#!/bin/python
#
# $Header: ecs/exacloud/exabox/tools/Utils.py /main/2 2025/05/06 06:50:19 aypaul Exp $
#
# Utils.py
#
# Copyright (c) 2024, 2026, Oracle and/or its affiliates.
#
#    NAME
#      Utils.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      This file acts as a business-related set of common functions that
#      could act as static functions.
#
#    NOTES
#      None
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      04/23/25 - Bug#37535214 Utility function to backup a file.
#    ririgoye    02/16/24 - Bug 36215212 - Added file for business-related
#                           utils that could be used as static functions.
#    ririgoye    02/16/24 - Creation
#

import os
import psutil
import shutil
import uuid
from datetime import datetime
from typing import List

from exabox.core.Error import ExacloudRuntimeError
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogInit, ebLogInfo, ebLogError, ebLogVerbose, ebLogWarn, ebLogTrace
from exabox.utils.common import remove_algorithms
from exabox.utils.node import (
    node_cmd_abs_path_check,
    node_exec_cmd_check,
    node_read_text_file,
    node_write_text_file)

# Get current exacloud root using this file's location as reference
def mGetExacloudRoot():
    _filepath = os.path.abspath(__file__)
    _exabox_root = os.path.dirname(os.path.dirname(_filepath))
    _ec_root = os.path.dirname(_exabox_root)
    return _ec_root

# Get current memory diagnostics and return a dictionary containing the results
def mGetUsageMetrics():
    _ec_root = mGetExacloudRoot()
    _cpu_percent = psutil.cpu_percent()
    _mem_percent = psutil.virtual_memory().percent
    _swap_percent = psutil.swap_memory().percent
    _disk_usage = psutil.disk_usage(_ec_root).percent
    _diag_obj = {
        "cpu": _cpu_percent,
        "memory": _mem_percent,
        "swap": _swap_percent,
        "disk": _disk_usage
    }
    return _diag_obj

def mBackupFile(aSourcefilepath: str=None, aRaiseException: bool=False) -> bool:
    _src_file_path = aSourcefilepath
    _raise_exception = aRaiseException
    
    if not os.path.isabs(_src_file_path):
        if _raise_exception:
            raise ExacloudRuntimeError(0x0827, 0xA, f"Source file path is not an absolute path: {_src_file_path}") 
        else:
            return False

    if not os.path.exists(_src_file_path):
        if _raise_exception:
            raise ExacloudRuntimeError(0x0827, 0xA, f"Source file path does not exist: {_src_file_path}") 
        else:
            return False

    _dest_file_path = f"{_src_file_path}.backup"
    if os.path.exists(_dest_file_path):
        ebLogWarn(f"Backup file: {_dest_file_path} already exists.")
        _dest_file_path = f"{_src_file_path}.backup.{uuid.uuid4()}"

    try:
        shutil.copy2(_src_file_path, _dest_file_path)
    except PermissionError:
        ebLogError(f"Error: Permission denied to copy '{_src_file_path}'")
        if _raise_exception:
            raise ExacloudRuntimeError(0x0827, 0xA, f"Error: Permission denied to copy '{_src_file_path}'")
        else:
            return False
    except Exception as e:
        ebLogError(f"An unexpected error occurred: {e}")
        if _raise_exception:
            raise ExacloudRuntimeError(0x0827, 0xA, f"An unexpected error occurred: {e}")
        else:
            return False

    if _dest_file_path != f"{_src_file_path}.backup":
        try:
            shutil.move(f"{_src_file_path}.backup", f"{_src_file_path}.backup.2")
            shutil.move(_dest_file_path, f"{_src_file_path}.backup")
            os.remove(f"{_src_file_path}.backup.2")
        except Exception as e:
            ebLogError(f"An unexpected error occurred: {e}")
            if _raise_exception:
                raise ExacloudRuntimeError(0x0827, 0xA, f"An unexpected error occurred during file move: {e}")
            else:
                return False

    return True


def mRemoveSshAlgorithmsFromNode(
        aNode: exaBoxNode,
        aAlgorithmsToRemove: List[str]) -> None:
    """
    Remove SSH algorithms from sshd_config on a remote node.

    The routine backs up the current sshd_config, applies the pruning using
    remove_algorithms(), and restarts sshd so the update is effective
    immediately.

    :param aNode: already connected exaBoxNode instance.
    :param aAlgorithmsToRemove: list of algorithms to remove.
    :raises ExacloudRuntimeError: on connection or command failures.
    """
    if not aNode or not aNode.mIsConnected():
        raise ExacloudRuntimeError(
            0x10,
            0xA,
            "Node must be a connected exaBoxNode instance")

    if not aAlgorithmsToRemove:
        ebLogInfo("No algorithms provided to remove from sshd_config.")
        return

    sshd_config_path = "/etc/ssh/sshd_config"
    ebLogInfo(
        f"Removing algorithms {aAlgorithmsToRemove} from {sshd_config_path} "
        f"on {aNode.mGetHostname()}")

    current_config = node_read_text_file(aNode, sshd_config_path)
    updated_config = remove_algorithms(current_config, aAlgorithmsToRemove)

    if current_config == updated_config:
        ebLogInfo("sshd_config already excludes the requested algorithms.")
        return

    now_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = f"{sshd_config_path}_{now_str}"

    cp_cmd = node_cmd_abs_path_check(aNode, "cp")
    node_exec_cmd_check(
        aNode,
        f"{cp_cmd} {sshd_config_path} {backup_path}",
        log_error=True,
        log_stdout_on_error=True)
    ebLogInfo(f"Created sshd_config backup at {backup_path}.")

    if not updated_config.endswith("\n"):
        updated_config = f"{updated_config}\n"

    node_write_text_file(aNode, sshd_config_path, updated_config)
    ebLogInfo("Updated sshd_config with filtered algorithms.")

    systemctl_cmd = node_cmd_abs_path_check(aNode, "systemctl", sbin=True)
    node_exec_cmd_check(
        aNode,
        f"{systemctl_cmd} restart sshd",
        log_error=True,
        log_stdout_on_error=True)
    ebLogInfo("Restarted sshd service to apply the configuration changes.")
