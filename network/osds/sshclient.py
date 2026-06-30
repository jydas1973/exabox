#!/bin/python
#
# $Header: sshclient.py 10-jun-2026.14:39:09 jesandov Exp $
#
# sshclient.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      sshclient.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    06/10/26 - 39462050: Add secure client
#    jesandov    06/10/26 - Creation
#

import os
import re
import uuid
import paramiko
from pathlib import Path

import subprocess
from   subprocess import PIPE

from exabox.tools.AttributeWrapper import wrapStrBytesFunctions

try:
    from subprocess import DEVNULL # Python 3X
except ImportError:
    DEVNULL = open(os.devnull, 'wb')

def mExecuteLocal(aCmdList, aStdOut=PIPE, aStdErr=PIPE, aDir=None, aFailOnRc=False):

    #print(f"Executing: {[' '.join(aCmdList)]}")

    _cmd_list = aCmdList
    _stdout = aStdOut
    _stderr = aStdErr

    # Call the process
    with subprocess.Popen(_cmd_list, cwd=aDir, shell=False, stdout=_stdout, stderr=_stderr) as _proc:
        _std_out, _std_err = wrapStrBytesFunctions(_proc).communicate()
        _rc = _proc.returncode

    if aFailOnRc:
        _msg = f"Failed to execute the command: {_cmd_list}\n"
        _msg += f"RC: {_rc}\n"
        _msg += f"STDOUT: {_stdout}\n"
        _msg += f"STDERR: {_stderr}"
        raise RuntimeError(_msg)

    return _rc, _std_out, _std_err

class SshClient:

    def __init__(self, aHost):
        self.__host = aHost
        self.__uuid = str(uuid.uuid4()).replace("-", "")

        _home = Path.home()
        self.__newKnownHostFile = f"{_home}/.ssh/known_hosts_exacloud_{self.__uuid}"
        self.__origKnownHostFile = f"{_home}/.ssh/known_hosts"
        self.mCalculateKnownHostFile()

    def mCreateSshClient(self):

        # Create new know_host file
        _hostname = self.__host.split(".")[0]
        with open(self.__origKnownHostFile, "r") as _orig:
            with open(self.__newKnownHostFile, "w") as _new:
                _lines = _orig.readlines()
                for _entry in _lines:
                    if _hostname in _entry:
                        _new.write(_entry.strip())
                        _new.write("\n")

        _client = paramiko.SSHClient()
        _client.load_host_keys(self.__newKnownHostFile)
        _client.set_missing_host_key_policy(paramiko.RejectPolicy())

        return _client

    def mGetOrigKnownHostFile(self):
        return self.__origKnownHostFile

    def mAddToKnownHost(self):

        _cmd_list = ["/bin/sed", "-i", f"/{self.__host}/d"]
        _cmd_list.append(self.__origKnownHostFile)
        mExecuteLocal(_cmd_list, aStdOut=DEVNULL, aStdErr=DEVNULL)

        _cmd_list = ["/bin/sed", "-i", f"/{self.__host.split('.')[0]}/d"]
        _cmd_list.append(self.__origKnownHostFile)
        mExecuteLocal(_cmd_list, aStdOut=DEVNULL, aStdErr=DEVNULL)

        _cmd_list = ["/bin/ssh"]
        _cmd_list += ["-o", f"UserKnownHostsFile={self.__origKnownHostFile}"]
        _cmd_list += ["-o", "StrictHostKeyChecking=accept-new"]
        _cmd_list += ["-o", "PasswordAuthentication=no"]
        _cmd_list += [f"root@{self.__host}", '/bin/echo new']
        mExecuteLocal(_cmd_list, aStdOut=DEVNULL, aStdErr=DEVNULL)

        _cmd_list = ["/bin/cat", self.__origKnownHostFile]
        _, _o, _ = mExecuteLocal(_cmd_list)
        if self.__host not in _o:
            raise RuntimeError(f"Could not add host {self.__host} to known_host file {self.__origKnownHostFile}")

    def mCalculateKnownHostFile(self):

        _baseCmd = ["/bin/ssh", "-vvv", "-o", "StrictHostKeyChecking=accept-new", "-o", "PasswordAuthentication=no"]
        _cmd_list = _baseCmd + [f"root@localhost", '/bin/echo new']
        _, _o, _e = mExecuteLocal(_cmd_list)

        for _line in _e.split("\n"):
            if "known_host" in _line:
                _known = re.findall("/.*?known_hosts", _line)[-1]
                self.__origKnownHostFile = _known
                self.__newKnownHostFile = _known.replace("known_hosts", f"known_hosts_exacloud_{self.__uuid}")
                break


    def mCleanUp(self):
        if os.path.exists(self.__newKnownHostFile):
            os.unlink(self.__newKnownHostFile)

    def __del__(self):
        self.mCleanUp()


# end of file
