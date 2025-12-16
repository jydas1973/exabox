#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/remote_lock/tests_dom0_lock.py /main/1 2021/09/17 13:35:17 joserran Exp $
#
# test_dom0_lock.py
#
# Copyright (c) 2021, Oracle and/or its affiliates. 
#
#    NAME
#      tests_dom0_lock.py - Unit tests for remote lock functionality
#
#    DESCRIPTION
#      Contains the unit tests for the remote lock functionality used in
#      clucontrol.py
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    joserran    08/06/21 - Bug 32614102: Adding Remote Lock heartbeat mechanism
#    joserran    08/06/21 - Creation
#

import base64
import datetime
import json
from multiprocessing import Process
import os
import shutil
from six.moves import queue
import socket
import threading
import time
from subprocess import Popen, PIPE
import unittest

from exabox.ovm.remotelock import (LockRetCode, dict2base64)

MAIN_DIR = "/tmp/exacloud_locks/"
LOGS_DIR = os.path.join(MAIN_DIR, "logs")
LOGS_FILE = os.path.join(LOGS_DIR, "locks.log")
LOCKS_DIR = os.path.join(MAIN_DIR, "locks")
LOCK_FILE_FILENAME = ".lock_file"
LOCK_INFO_FILENAME = "lock_info.json"

LEGACY_LOCK_FILE = "/tmp/exacs_dom0_lock"
LEGACY_LOCK_INFO_FILE = "/tmp/exacs_dom0_lock_info"

DOM0_LOCK_FILE = "dom0_lock.py"
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "../../../scripts"))
SCRIPT_FILE = os.path.join(SCRIPT_DIR, "network", DOM0_LOCK_FILE)

DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f UTC"

def wait_and_get_results(process):
    process.wait()

    stdout = process.stdout.read().decode("UTF-8").strip()
    stderr = process.stderr.read().decode("UTF-8").strip()
    return_code = process.returncode

    process.stdout.close()
    process.stderr.close()
    return stdout, stderr, return_code

def create_legacy_lock(lock_info, owner_id):
    with open(LEGACY_LOCK_FILE, "w") as fd:
        fd.write(owner_id)

    with open(LEGACY_LOCK_INFO_FILE, "w") as fd:
        lines = []
        for key in lock_info:
            lines.append(key + ":" + lock_info[key] + "\n")

        fd.writelines(lines)

def remove_legacy_lock():
    if os.path.exists(LEGACY_LOCK_FILE):
        os.remove(LEGACY_LOCK_FILE)
    if os.path.exists(LEGACY_LOCK_INFO_FILE):
        os.remove(LEGACY_LOCK_INFO_FILE)

def valid_legacy_lock_file(lock_info, owner_uuid):
    with open(LEGACY_LOCK_FILE) as fd:
        lock_owner = fd.read()

    if lock_owner != owner_uuid:
        return False

    legacy_lock_info = {}
    with open(LEGACY_LOCK_INFO_FILE, "r") as lock_info_fd:
        for line in lock_info_fd:
            if ":" not in line:
                continue
            key = line[0: line.find(":")].strip()
            val = line[line.find(":") + 1: ].strip()

            legacy_lock_info[key] = val

    for expected_key in lock_info:
        if expected_key not in legacy_lock_info:
            return False

        if lock_info[expected_key] != legacy_lock_info[expected_key]:
            return False

    return True

class ebTestRemoteLock(unittest.TestCase):
    def setUp(self):
        # Clear environment
        shutil.rmtree(MAIN_DIR, ignore_errors=True)
        if os.path.exists(LEGACY_LOCK_FILE):
            os.remove(LEGACY_LOCK_FILE)
        if os.path.exists(LEGACY_LOCK_INFO_FILE):
            os.remove(LEGACY_LOCK_INFO_FILE)

    def test_lock_dir_structure(self):
        """ Check all files and directories by running dom0_lock.py """
        lock_scope = "GLOBAL"
        owner_id = "owner"
        lock_dir = os.path.join(LOCKS_DIR, lock_scope)
        lock_file = os.path.join(MAIN_DIR, LOCK_FILE_FILENAME)
        lock_info_file = os.path.join(lock_dir, LOCK_INFO_FILENAME)
        logs_file = LOGS_FILE

        assert not os.path.exists(LOGS_DIR)
        assert not os.path.exists(lock_dir)
        assert not os.path.exists(lock_file)
        assert not os.path.exists(lock_info_file)
        assert not os.path.exists(logs_file)

        args = [SCRIPT_FILE, "acquire", lock_scope, owner_id]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)

        assert return_code == LockRetCode.NO_ERROR.value
        assert os.path.exists(LOGS_DIR)
        assert os.path.exists(lock_dir)
        assert os.path.exists(lock_file)
        assert os.path.exists(lock_info_file)
        assert os.path.exists(logs_file)

    def test_cmd_acquire(self):
        lock_scope = "GLOBAL"
        owner_id = "owner"

        args = [SCRIPT_FILE, "acquire", lock_scope, owner_id]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value
        assert len(stdout) == 0
        assert len(stderr) == 0

        args = [SCRIPT_FILE, "logs"]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert "Lock {} ACQUIRED by {}".format(lock_scope, owner_id) in \
               stdout.split("\n")[-1]

        args = [SCRIPT_FILE, "acquire", lock_scope, owner_id]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value

        args = [SCRIPT_FILE, "logs"]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert "Lock {} RE-ACQUIRED by {}".format(lock_scope, owner_id) in \
               stdout.split("\n")[-1]

    def test_cmd_release(self):
        lock_scope = "GLOBAL"
        owner_id = "owner"

        args = [SCRIPT_FILE, "acquire", lock_scope, owner_id]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value

        args = [SCRIPT_FILE, "logs"]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert "Lock {} ACQUIRED by {}".format(lock_scope, owner_id) in \
               stdout.split("\n")[-1]

        args = [SCRIPT_FILE, "release", lock_scope, owner_id]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value

        args = [SCRIPT_FILE, "logs"]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value
        assert len(stderr) == 0
        assert "Lock {} RELEASED by {}".format(lock_scope, owner_id) in \
               stdout.split("\n")[-1]

        args = [SCRIPT_FILE, "release", lock_scope, owner_id]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code != 0
        assert len(stderr) != 0
        assert len(stdout) == 0

    def test_cmd_logs(self):
        lock_scope = "GLOBAL"
        owner_id = "owner"

        # Empty log
        args = [SCRIPT_FILE, "logs"]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value
        assert len(stdout) == 0
        assert len(stderr) == 0
        assert os.path.exists(LOGS_FILE)

        args = [SCRIPT_FILE, "acquire", lock_scope, owner_id]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value
        assert os.path.exists(LOGS_FILE)

        # Log is deleted
        args = [SCRIPT_FILE, "logs", "--delete"]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value
        assert len(stderr) == 0
        assert not os.path.exists(LOGS_FILE)

        # Log is created again
        args = [SCRIPT_FILE, "release", lock_scope, owner_id]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value
        assert os.path.exists(LOGS_FILE)

    def test_cmd_get_info(self):
        """ Check lock info fields are extracted """
        owner_id = "owner_a"
        args = [SCRIPT_FILE, "acquire", "GLOBAL", owner_id]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value

        args = [SCRIPT_FILE, "get-info", "--field", "owner_uuid",
                "--lock-scope", "GLOBAL"]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)

        assert return_code == LockRetCode.NO_ERROR.value
        assert stdout.split("\n")[0] == owner_id

    def test_cmd_set_info(self):
        """ Check lock info is properly updated """
        owner_id = "owner_a"
        args = [SCRIPT_FILE, "acquire", "GLOBAL", owner_id]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value

        args = [SCRIPT_FILE, "set-info", "--single-field",
                "duration_hint:FAST", "GLOBAL", "owner_a"]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)

        assert return_code == LockRetCode.NO_ERROR.value

        args = [SCRIPT_FILE, "get-info", "--field", "duration_hint",
                "--lock-scope", "GLOBAL"]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)

        assert return_code == LockRetCode.NO_ERROR.value
        assert stdout.split("\n")[0] == "FAST"

    def test_cmd_refresh(self):
        lock_scope = "GLOBAL"
        owner_id = "owner"

        args = [SCRIPT_FILE, "acquire", lock_scope, owner_id]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value

        args = [SCRIPT_FILE, "get-info", "--field", "expire_date",
                "--lock-scope", lock_scope]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value
        assert len(stdout) != 0
        expire_date1_str = str(stdout)

        args = [SCRIPT_FILE, "refresh", "--valid-for", "12", lock_scope, owner_id]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value

        args = [SCRIPT_FILE, "get-info", "--field", "expire_date",
                "--lock-scope", lock_scope]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value
        assert len(stdout) != 0
        expire_date2_str = str(stdout)

        expire_date1 = datetime.datetime.strptime(expire_date1_str, DATE_FORMAT)
        expire_date2 = datetime.datetime.strptime(expire_date2_str, DATE_FORMAT)

        assert expire_date2 > expire_date1

    def test_cmd_remove(self):
        lock_scope1 = "GLOBAL1"
        lock_scope2 = "GLOBAL2"
        lock_scope3 = "GLOBAL3"
        owner_id = "owner"

        args = [SCRIPT_FILE, "acquire", lock_scope1, owner_id]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value

        args = [SCRIPT_FILE, "acquire", lock_scope2, owner_id]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value

        args = [SCRIPT_FILE, "acquire", lock_scope3, owner_id]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value

        lock_dir1 = os.path.join(LOCKS_DIR, lock_scope1)
        lock_dir2 = os.path.join(LOCKS_DIR, lock_scope2)
        lock_dir3 = os.path.join(LOCKS_DIR, lock_scope2)
        assert os.path.exists(lock_dir1)
        assert os.path.exists(lock_dir2)
        assert os.path.exists(lock_dir3)

        args = [SCRIPT_FILE, "remove", "--lock-scope", lock_scope1]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value
        assert not os.path.exists(lock_dir1)
        assert os.path.exists(lock_dir2)
        assert os.path.exists(lock_dir3)

        args = [SCRIPT_FILE, "remove", "--all"]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value
        assert not os.path.exists(lock_dir1)
        assert not os.path.exists(lock_dir2)
        assert not os.path.exists(lock_dir3)

    def test_locked_lock(self):
        """ Check locked lock is not acquired by other owner """
        lock_scope = "GLOBAL"

        args = [SCRIPT_FILE, "acquire", lock_scope, "owner_a"]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value

        args = [SCRIPT_FILE, "acquire", lock_scope, "owner_b"]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.LOCK_NOT_ACQUIRED.value
        assert len(stdout) == 0
        assert len(stderr) != 0
        expected_stderr = ("Lock {} DENIED to {} "
                           "currently HELD by {}").format(lock_scope,
                                                          "owner_b",
                                                          "owner_a")

        assert expected_stderr in stderr

        args = [SCRIPT_FILE, "release", lock_scope, "owner_a"]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value
        assert len(stdout) == 0
        assert len(stderr) == 0

        args = [SCRIPT_FILE, "release", lock_scope, "owner_a"]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code != 0
        assert len(stdout) == 0
        assert len(stderr) != 0
        expected_stderr = "Lock {} doesn't exist".format(lock_scope)
        assert expected_stderr in stderr

        args = [SCRIPT_FILE, "acquire", lock_scope, "owner_b"]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value

    def test_expired_lock(self):
        """ Check expired lock is acquired by other owner """
        lock_scope = "GLOBAL"
        owner_id1 = "owner_a"
        owner_id2 = "owner_b"

        args = [SCRIPT_FILE, "acquire", lock_scope, owner_id1]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value

        args = [SCRIPT_FILE, "acquire", lock_scope, owner_id2]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.LOCK_NOT_ACQUIRED.value

        args = [SCRIPT_FILE, "refresh", "--valid-for", "1", lock_scope, owner_id1]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value

        time.sleep(2)
        args = [SCRIPT_FILE, "acquire", lock_scope, owner_id2]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.LOCK_EXPIRED_AND_ACQUIRED.value
        assert "Lock {} has EXPIRED and is ACQUIRED now by {}".format(lock_scope,
                                                                      owner_id2) in \
               stdout.split("\n")[0]

    def test_set_info_overwrite(self):
        """ Check lock info is properly overwritten """
        owner_id = "owner_a"
        args = [SCRIPT_FILE, "acquire", "GLOBAL", owner_id]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value

        lock_info = {
            "service_path": "/foo/bar",
            "cluster_name": "cluster.name",
            "duration_hint": "FAST",
            "some_extra_info": "val"
        }
        lock_info_base64_str = dict2base64(lock_info)

        args = [SCRIPT_FILE, "set-info", "--lock-info", lock_info_base64_str,
                "GLOBAL", "owner_a"]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value

        args = [SCRIPT_FILE, "get-info", "--lock-scope", "GLOBAL"]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value

        returned_lock_info = json.loads(stdout)

        for key in lock_info:
            assert key in returned_lock_info
            assert lock_info[key] == returned_lock_info[key]

    def test_logging(self):
        lock_scope = "GLOBAL"
        owner_id = "owner"

        args = [SCRIPT_FILE, "acquire", lock_scope, owner_id]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value

        args = [SCRIPT_FILE, "logs"]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value
        assert "Lock {} ACQUIRED by {}".format(lock_scope, owner_id) in stdout

        args = [SCRIPT_FILE, "release", lock_scope, owner_id]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value

        args = [SCRIPT_FILE, "logs"]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value
        assert "Lock {} RELEASED by {}".format(lock_scope, owner_id) in stdout
        lock_dir = os.path.join(LOCKS_DIR, lock_scope)
        assert not os.path.exists(lock_dir)

    def test_set_info_protected_fields(self):
        """ Check protected fields are not overwritten """
        owner_id = "owner_a"

        args = [SCRIPT_FILE, "acquire", "GLOBAL", owner_id]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value

        args = [SCRIPT_FILE, "get-info", "--lock-scope", "GLOBAL"]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value
        returned_lock_info = json.loads(stdout)

        lock_info = {
            "owner_uuid": "other_owner"
        }
        lock_info_base64_str = dict2base64(lock_info)

        args = [SCRIPT_FILE, "set-info", "--lock-info", lock_info_base64_str,
                "GLOBAL", owner_id]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value

        args = [SCRIPT_FILE, "get-info", "--field", "owner_uuid",
                "--lock-scope", "GLOBAL"]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value
        # Validate owner_uuid was not modified
        assert owner_id == stdout

        args = [SCRIPT_FILE, "get-info", "--lock-scope", "GLOBAL"]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value
        returned_lock_info2 = json.loads(stdout)

        # Validate all lock info remained the same
        assert returned_lock_info == returned_lock_info2

    def test_double_logs_delete(self):
        lock_scope = "GLOBAL"
        owner_id = "owner"

        args = [SCRIPT_FILE, "logs"]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value
        assert len(stdout) == 0
        assert len(stderr) == 0
        assert os.path.exists(LOGS_FILE)

        args = [SCRIPT_FILE, "logs", "--delete"]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value
        assert len(stdout) == 0
        assert len(stderr) == 0
        assert not os.path.exists(LOGS_FILE)

        args = [SCRIPT_FILE, "logs", "--delete"]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value
        assert len(stdout) == 0
        assert len(stderr) == 0
        assert not os.path.exists(LOGS_FILE)

    def test_set_info_non_existing_lock(self):
        lock_scope = "GLOBAL"
        owner_id = "owner_a"

        args = [SCRIPT_FILE, "set-info", "--single-field",
                "duration_hint:FAST", lock_scope, owner_id]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)

        expected_stderr = "Lock {} doesn't exist".format(lock_scope)
        assert return_code != 0
        assert len(stdout) == 0
        assert expected_stderr in stderr

    def test_set_info_non_wrong_lock(self):
        lock_scope = "GLOBAL"
        owner_id = "owner_a"
        owner_id2 = "owner_b"

        args = [SCRIPT_FILE, "acquire", lock_scope, owner_id]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value

        args = [SCRIPT_FILE, "set-info", "--single-field",
                "duration_hint:FAST", lock_scope, owner_id2]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)

        expected_stderr = "Lock {} is not owned by {}".format(lock_scope,
                                                              owner_id2)
        assert return_code != 0
        assert len(stdout) == 0
        assert expected_stderr in stderr

    def test_refresh_non_existig_lock(self):
        lock_scope = "GLOBAL"
        owner_id = "owner_a"

        args = [SCRIPT_FILE, "refresh", "--valid-for", "10", lock_scope, owner_id]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)

        expected_stderr = "Lock {} doesn't exist".format(lock_scope)
        assert return_code != 0
        assert len(stdout) == 0
        assert expected_stderr in stderr

    def test_refresh_wrong_lock(self):
        lock_scope = "GLOBAL"
        owner_id = "owner_a"
        owner_id2 = "owner_b"

        args = [SCRIPT_FILE, "acquire", lock_scope, owner_id]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value

        args = [SCRIPT_FILE, "refresh", "--valid-for", "10", lock_scope, owner_id2]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)

        expected_stderr = "Lock {} is not owned by {}".format(lock_scope,
                                                              owner_id2)
        assert return_code != 0
        assert len(stdout) == 0
        assert expected_stderr in stderr

    def test_acquire_with_lock_info(self):
        lock_scope = "GLOBAL"
        owner_id = "owner"

        lock_info = {
            "user_name": "mir name",
            "hostname": socket.gethostname(),
            "service_path": os.getcwd(),
            "duration_hint": "FAST",
            "cluster_key": "cluster-key-with-some-data",
            "cluster_name": "cluster-name"
        }
        lock_info_base64_str = dict2base64(lock_info)

        args = [SCRIPT_FILE, "acquire", "--lock-info", lock_info_base64_str,
                lock_scope, owner_id]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value
        assert len(stdout) == 0
        assert len(stderr) == 0

        args = [SCRIPT_FILE, "get-info", "--lock-scope", lock_scope]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value
        assert len(stdout) != 0
        assert len(stderr) == 0

        returned_lock_info = json.loads(stdout)

        for key in lock_info:
            assert key in returned_lock_info
            assert lock_info[key] == returned_lock_info[key]

    def test_re_acquired_with_lock_info(self):
        lock_scope = "GLOBAL"
        owner_id = "owner"

        args = [SCRIPT_FILE, "acquire", lock_scope, owner_id]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value

        lock_info = {
            "user_name": "mir name",
            "hostname": socket.gethostname(),
            "service_path": os.getcwd(),
            "duration_hint": "FAST",
            "cluster_key": "cluster-key-with-some-data",
            "cluster_name": "cluster-name"
        }
        lock_info_base64_str = dict2base64(lock_info)

        args = [SCRIPT_FILE, "acquire", "--lock-info", lock_info_base64_str,
                lock_scope, owner_id]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value

        args = [SCRIPT_FILE, "logs"]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value
        assert "Lock {} RE-ACQUIRED by {}".format(lock_scope, owner_id) in \
               stdout.split("\n")[-1]

        args = [SCRIPT_FILE, "get-info", "--lock-scope", lock_scope]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value
        assert len(stdout) != 0
        assert len(stderr) == 0

        returned_lock_info = json.loads(stdout)

        for key in lock_info:
            assert key in returned_lock_info
            assert lock_info[key] == returned_lock_info[key]

    def test_expired_lock_with_lock_info(self):
        lock_scope = "GLOBAL"
        owner_id1 = "owner_a"
        owner_id2 = "owner_b"

        args = [SCRIPT_FILE, "acquire", lock_scope, owner_id1]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value

        args = [SCRIPT_FILE, "refresh", "--valid-for", "1", lock_scope, owner_id1]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value

        time.sleep(2)

        lock_info = {
            "user_name": "mir name",
            "hostname": socket.gethostname(),
            "service_path": os.getcwd(),
            "duration_hint": "FAST",
            "cluster_key": "cluster-key-with-some-data",
            "cluster_name": "cluster-name"
        }
        lock_info_base64_str = dict2base64(lock_info)

        args = [SCRIPT_FILE, "acquire", "--lock-info", lock_info_base64_str,
                lock_scope, owner_id2]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.LOCK_EXPIRED_AND_ACQUIRED.value
        assert "Lock {} has EXPIRED and is ACQUIRED now by {}".format(lock_scope,
                                                                      owner_id2) in \
               stdout.split("\n")[0]

        args = [SCRIPT_FILE, "get-info", "--lock-scope", lock_scope]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value
        assert len(stdout) != 0
        assert len(stderr) == 0

        returned_lock_info = json.loads(stdout)

        for key in lock_info:
            assert key in returned_lock_info
            assert lock_info[key] == returned_lock_info[key]

    def test_legacy_already_acquired_lock(self):
        lock_scope = "GLOBAL"
        owner_id = "owner"
        legacy_owner_id = "owner_2"

        legacy_lock_info2 = {
            "user_name": "mir name",
            "hostname": socket.gethostname(),
            "service_path": os.getcwd(),
            "duration_hint": "FAST",
            "cluster_key": "cluster-key-with-some-data",
            "cluster_name": "cluster-name"
        }
        create_legacy_lock(legacy_lock_info2, legacy_owner_id)

        lock_info = {
            "user_name": "mir name",
            "hostname": socket.gethostname(),
            "service_path": os.getcwd(),
            "duration_hint": "FAST",
            "cluster_key": "cluster-key-with-some-data",
            "cluster_name": "cluster-name"
        }
        lock_info_base64_str = dict2base64(lock_info)

        args = [SCRIPT_FILE, "acquire", "--lock-info", lock_info_base64_str,
                lock_scope, owner_id]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.LOCK_NOT_ACQUIRED_LEGACY_MODE.value
        assert len(stderr) != 0

        remove_legacy_lock()

        args = [SCRIPT_FILE, "acquire", "--lock-info", lock_info_base64_str,
                lock_scope, owner_id]
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr, return_code = wait_and_get_results(p)
        assert return_code == LockRetCode.NO_ERROR.value
        assert len(stderr) == 0

        assert valid_legacy_lock_file(lock_info, owner_id)

    def test_concurrent_acquire(self):
        # Create N threads
        thread_count = 10
        thread_result_queue = queue.Queue(thread_count)

        # Execute acquire from all
        def _acquire_lock(owner_id, result_queue):
            lock_scope = "GLOBAL"
            owner_id = str(owner_id)

            lock_info = {
                "user_name": "mir name",
                "hostname": socket.gethostname(),
                "service_path": os.getcwd(),
                "duration_hint": "FAST",
                "cluster_key": "cluster-key-with-some-data",
                "cluster_name": "cluster-name"
            }

            lock_info_base64_str = dict2base64(lock_info)
            args = [SCRIPT_FILE, "acquire", "--lock-info",
                    lock_info_base64_str,
                    lock_scope, owner_id]
            p = Popen(args, stdout=PIPE, stderr=PIPE)
            stdout, stderr, return_code = wait_and_get_results(p)
            result_queue.put((stdout, stderr, return_code))


        for thread_id in range(thread_count):
            thread = threading.Thread(target=_acquire_lock,
                                      args=(thread_id, thread_result_queue,))
            thread.setDaemon(True)
            thread.start()

        # Verify only one acquired the lock
        while not thread_result_queue.full():
            pass

        acquired_count = 0
        non_acquired_count = 0

        while not thread_result_queue.empty():
            item = thread_result_queue.get()

            if item[2] == 0:
                acquired_count += 1
            else:
                non_acquired_count += 1

        assert acquired_count == 1
        assert non_acquired_count == thread_count - 1

if __name__ == '__main__':
    unittest.main()
