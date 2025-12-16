#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/network/tests_sshgen.py /main/4 2025/03/11 17:06:15 pbellary Exp $
#
# tests_sshgen.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_sshgen.py - Unit tests for exabox/network/osds/sshgen.py
#
#    DESCRIPTION
#      Unit tests for exabox/network/osds/sshgen.py
#
#    NOTES
#      NA
#
#    MODIFIED   (MM/DD/YY)
#    pbellary    03/10/25 - Bug 35816658 - ETF: FIXED test_mSetupPwdLess & test_mSetupSSHKey testcases
#    prsshukl    02/06/25 - Enh 37562404 - ETF: DISABLE TESTS_SSHGEN UNTIL
#                           LOGIC GET FIXED
#    pbellary    05/31/22 - Creation
#

import os
import io
import json
import six
import paramiko
import socket
import unittest
import warnings
import copy
import uuid
import shutil
import re
import builtins
from unittest import mock
from exabox.log.LogMgr import ebLogInfo
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.MockCommand import exaMockCommand
from exabox.core.Error import ExacloudRuntimeError
from unittest.mock import patch, MagicMock, PropertyMock, mock_open
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.network.osds.sshgen import sshconn, execute_local, validate_hostname, validate_user, ping_host, setup_ssh_key, setup_remote_host

SSH_PUB = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDa4Wn/bcdeoOgjWZyBbfJL/snzHraj+c1Purlp2OcZt5m3fEeGz3Hdezlmq252Xjp1Ihv3yD7uErQL4BzxAYH3rYw/MO7u7cy76wuhIjNJ9iSU8SO6mIoZhCGUu9FUGMrnhwZeK8yQEITjsdomswBvJCrRIpRWICYgLAYn53orsmTiUNMrPwAvkruXDrXF80LX2UWqNyB1L+5tphcm+MKM8iNKTWgAvhxw+3MZvOQnR5yc1LfoACU4C84DXBSpSWI2e1w46bf7e6otIS9UpB5ijx5FialUtHj9fD95TqbH8CuW3qo1WD5jB4LqEPO8JToY+IcWn2HT7ZV1UAPIRDajpSrQU9sFel+kRD8ujSN9ythuGaTcGtRuxd1Idu7LFlT7lMbHM9bCaL5Wam5rKAYy5+jkkhOERuCnd/vquAmLO22dpNfJiGtvbzhgh1ISrPvmDxepw5OztDOY3YN2n8wJadJde1snAjgiWZUI724QtIlYr4yr+1dqsK4cddHomBO0="

class testOptions(object): pass

class MockSSHClient(object):
    def __init__(self):
        self.__id = uuid.uuid4()
        self.__policy = None
        self.__transport = MockTransport()
        self.__sftp = MockSFTP()
        self.__buffer = MockBuffer()

    def set_missing_host_key_policy(self, policy):
        self.__policy = policy

    def connect(self, hostname, port=22, username=None, password=None, allow_agent=False, timeout=None):
        pass
    
    def exec_command(self, command):
        return (self.__buffer, self.__buffer, self.__buffer)

    def get_transport(self):
        return self.__transport
    
    def open_sftp(self):
        return self.__sftp

    def close(self):
        pass

class MockTransport(object):
    def __init__(self):
        self.__active = True
        self.__timeout = None
        self.__compression = None
        self.__channel = MockChannel()

    def set_keepalive(self, interval):
        self.__timeout = interval
    
    def start_client(self, event=None, timeout=None):
        pass

    def auth_interactive(self, username, handler, submethods=''):
        pass

    def is_active(self):
        return self.__active

    def is_alive(self):
        return self.__active

    def use_compression(self, compress=True):
        self.__compression = compress
    
    def open_session(self):
        return self.__channel

    def close(self):
        pass

class MockSFTP(object):
    def __init__(self):
        self.sock = None
        self.__buffer = MockBuffer()

    def open(self, filename, mode='r', bufsize=-1):
        return self.__buffer

    def put(self, localpath, remotepath, callback=None, confirm=True):
        return 0

    def get(self, remotepath, localpath, callback=None, prefetch=True):
        pass

    def mkdir(self, path, mode=511):
        pass

    def chmod(self, path, mode):
        pass

    def stat(self, path):
        pass

    def close(self):
        pass

class MockChannel(object):
    def __init__(self):
        self.chanid = None
        self.__timeout = None
        self.__combine = None
        self.__blocking = False
        self.__buffer = MockBuffer()
    
    def get_pty(self):
        pass
    
    def invoke_shell(self):
        pass
    
    def settimeout(self, timeout):
        self.__timeout = timeout

    def setblocking(self, blocking):
        self.__blocking = blocking

    def send(self, s):
        pass

    def sendall(self, s):
        pass
    
    def recv(self, nbytes):
        return []

    def recv_stderr(self, nbytes):
        return []

    def recv_ready(self):
        return False
    
    def recv_stderr_ready(self):
        return False

    def exit_status_ready(self):
        return True

    def recv_exit_status(self):
        return True

    def set_combine_stderr(self, combine):
        self.__combine = combine
    
    def exec_command(self, command):
        pass
    
    def makefile_stdin(self, *params):
        pass
    
    def makefile(self, *params):
        return self.__buffer
    
    def makefile_stderr(self, *params):
        return self.__buffer

    def close(self):
        pass

class MockBuffer(object):
    def __init__(self):
        self.chanid = None
        self.__obj = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        return True

    def readlines(self, val=None):
        return ["some data..."]
    
    def read(self):
        return []

    def flush(self):
        pass

    def write(self, data):
        pass

class ebTestSshConn(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestSshConn, self).setUpClass(aUseOeda = True, aGenerateDatabase = True)
        warnings.filterwarnings("ignore")

    def test_mConnect(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on sshcon.mConnect")
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        with mock.patch.object(paramiko, "SSHClient", mock.Mock(return_value=MockSSHClient()) ):
            _node = sshconn("iad103712exdcl09.iad103712exd.adminiad1.oraclevcn.com", _options)
            _node.mSetUser("opc")
            _node.mConnect(aTimeout=None, aKeyOnly=None, aRetryStrategy=True)
            _node.mDisconnect()
    
    def test_mIsConnectable(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on sshcon.mIsConnectable")
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        with mock.patch.object(paramiko, "SSHClient", mock.Mock(return_value=MockSSHClient()) ):
            _node = sshconn("iad103712exdcl09.iad103712exd.adminiad1.oraclevcn.com", _options)
            _node.mSetUser("opc")
            self.assertEqual(_node.mIsConnectable(aTimeout=None, aKeyOnly=None), True)
    
    def test_mExecuteCmdAsync(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on sshcon.mExecuteCmdAsync")
        _cmd = "virsh list"
        _call_back = ["", "", "", ""]
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        with mock.patch.object(paramiko, "SSHClient", mock.Mock(return_value=MockSSHClient()) ):
            _node = sshconn("iad103712exdcl09.iad103712exd.adminiad1.oraclevcn.com", _options)
            _node.mSetUser("opc")
            _node.mConnect()
            _node.mExecuteCmdAsync(_cmd, _call_back)
            _node.mDisconnect()

    def test_mExecuteCmd(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on sshcon.mExecuteCmd")
        _cmd = "virsh list"
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        with mock.patch.object(paramiko, "SSHClient", mock.Mock(return_value=MockSSHClient()) ):
            _node = sshconn("iad103712exdcl09.iad103712exd.adminiad1.oraclevcn.com", _options)
            _node.mSetUser("opc")
            _node.mConnect()
            _node.mExecuteCmd(_cmd)
            self.assertEqual(_node.mGetCmdExitStatus(), True)
            _node.mDisconnect()

    def test_mExecuteCmdLog(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on sshcon.mExecuteCmdLog")
        _cmd = "virsh list"
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        with mock.patch.object(paramiko, "SSHClient", mock.Mock(return_value=MockSSHClient()) ):
            _node = sshconn("iad103712exdcl09.iad103712exd.adminiad1.oraclevcn.com", _options)
            _node.mSetUser("opc")
            _node.mConnect()
            _node.mExecuteCmdLog(_cmd)
            self.assertEqual(_node.mGetCmdExitStatus(), True)
            _node.mDisconnect()

    def test_mFileExists(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on sshcon.mFileExists")
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        with mock.patch.object(paramiko, "SSHClient", mock.Mock(return_value=MockSSHClient()) ):
            _node = sshconn("iad103712exdcl09.iad103712exd.adminiad1.oraclevcn.com", _options)
            _node.mSetUser("opc")
            _node.mConnect()
            self.assertEqual(_node.mFileExists("/opt/exacloud/clusters/shared_env_enabled"), False)
            _node.mDisconnect()

    def test_mMakeDir(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on sshcon.mMakeDir")
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        with mock.patch.object(paramiko, "SSHClient", mock.Mock(return_value=MockSSHClient()) ):
            _node = sshconn("iad103712exdcl09.iad103712exd.adminiad1.oraclevcn.com", _options)
            _node.mSetUser("opc")
            _node.mConnect()
            self.assertEqual(_node.mMakeDir('/opt/oracle/vmbackup/conf/'), False)
            _node.mDisconnect()

    def test_mChmodFile(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on sshcon.mChmodFile")
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        with mock.patch.object(paramiko, "SSHClient", mock.Mock(return_value=MockSSHClient()) ):
            _node = sshconn("iad103712exdcl09.iad103712exd.adminiad1.oraclevcn.com", _options)
            _node.mSetUser("opc")
            _node.mConnect()
            self.assertEqual(_node.mChmodFile('/opt/oracle/vmbackup/conf/', "777"), True)
            _node.mDisconnect()
    
    def test_mReadFile(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on sshcon.mReadFile")
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        with mock.patch.object(paramiko, "SSHClient", mock.Mock(return_value=MockSSHClient()) ):
            _node = sshconn("iad103712exdcl09.iad103712exd.adminiad1.oraclevcn.com", _options)
            _node.mSetUser("opc")
            _node.mConnect()
            self.assertEqual(_node.mReadFile('/opt/exacloud/clusters/shared_env_enabled'), [])
            _node.mDisconnect()

    def test_mWriteFile(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on sshcon.mWriteFile")
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        with mock.patch.object(paramiko, "SSHClient", mock.Mock(return_value=MockSSHClient()) ):
            _node = sshconn("iad103712exdcl09.iad103712exd.adminiad1.oraclevcn.com", _options)
            _node.mSetUser("opc")
            _node.mConnect()
            _node.mWriteFile('/opt/exacloud/clusters/shared_env_enabled', "Some data...")
            _node.mDisconnect()

    def test_mCopyFile(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on sshcon.mCopyFile")
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        with mock.patch.object(paramiko, "SSHClient", mock.Mock(return_value=MockSSHClient()) ):
            _node = sshconn("iad103712exdcl09.iad103712exd.adminiad1.oraclevcn.com", _options)
            _node.mSetUser("opc")
            _node.mConnect()
            _node.mCopyFile("scripts/dbaasapi_script.xml", "dbaasapi_script.xml")
            _node.mCopyFile("scripts/dbaasapi_script.xml")
            _node.mDisconnect()

    def test_mCopy2Local(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on sshcon.mCopy2Local")
    
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        with mock.patch.object(paramiko, "SSHClient", mock.Mock(return_value=MockSSHClient())):
            _node = sshconn("iad103712exdcl09.iad103712exd.adminiad1.oraclevcn.com", _options)
            _node.mSetUser("opc")
            _node.mConnect()
            _node.mCopy2Local("/opt/exacloud/clusters/shared_env_enabled", "/tmp")
            _node.mCopy2Local("/opt/exacloud/clusters/shared_env_enabled")
            _node.mDisconnect()

    def test_mConnectAuthInteractive(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on sshcon.mConnectAuthInteractive")
    
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        with mock.patch.object(paramiko, "SSHClient", mock.Mock(return_value=MockSSHClient())), \
             mock.patch.object(paramiko, "Transport", mock.Mock(return_value=MockTransport())), \
             mock.patch('socket.socket'):
            _node = sshconn("iad103712exdcl09.iad103712exd.adminiad1.oraclevcn.com", _options)
            _node.mSetUser("opc")
            _node.mConnect()
            _node.mConnectAuthInteractive()
            _node.mDisconnect()

    def test_mCreateHaltSRGTestsFile(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on sshcon.mCreateHaltSRGTestsFile")
    
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        with mock.patch.object(paramiko, "SSHClient", mock.Mock(return_value=MockSSHClient())):
            _node = sshconn("iad103712exdcl09.iad103712exd.adminiad1.oraclevcn.com", _options)
            _node.mSetUser("opc")
            _node.mConnect()
            _node.mCreateHaltSRGTestsFile()
            _node.mDisconnect()

    def test_mExecuteLocal(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on mExecuteLocal")
    
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _cmd_list = ['echo', '-n', '-e', six.u('\u0263')] 
        _, _out, _ = execute_local(_cmd_list)
        self.assertEqual(_out, six.u('\u0263'))

    def test_validate_hostname(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on validate_hostname")

        _hostname = "iad103712exdcl09.iad103712exd.adminiad1.oraclevcn.com"
        
        self.assertEqual(validate_hostname(_hostname), True)

    def test_validate_user(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on validate_user")
        
        self.assertEqual(validate_user("root"), True)

    def test_ping_host(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ping_host")
        
        self.assertEqual(ping_host("localhost"), True)

    def test_mSetupPwdLess(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on mSetupPwdLess")

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.sshkey = SSH_PUB
        with mock.patch.object(paramiko, "SSHClient", mock.Mock(return_value=MockSSHClient())),\
             mock.patch("builtins.open", mock_open(read_data="data")):
            _node = sshconn("iad103712exdcl09.iad103712exd.adminiad1.oraclevcn.com", _options)
            _node.mSetUser("opc")
            _node.mConnect()
            _node.mSetupPwdLess("opc", "welcome1")
            _node.mDisconnect()

    def test_mSetupSSHKey(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on mSetupSSHKey")

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.sshkey = SSH_PUB
        with mock.patch.object(paramiko, "SSHClient", mock.Mock(return_value=MockSSHClient())),\
             mock.patch("builtins.open", mock_open(read_data="data")):
            _node = sshconn("iad103712exdcl09.iad103712exd.adminiad1.oraclevcn.com", _options)
            _node.mSetUser("opc")
            _node.mConnect()
            _node.mSetupSSHKey("opc", "welcome1")
            _node.mDisconnect()

    def test_setup_ssh_key(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on setup_ssh_key")

        with mock.patch.object(paramiko, "SSHClient", mock.Mock(return_value=MockSSHClient())),\
             mock.patch("builtins.open", mock_open(read_data="data")):
            setup_ssh_key("localhost", "opc", "welcome1", "id_rsa_iad103712exdcl09.opc", True)

    def test_setup_remote_host(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on setup_remote_host")

        with mock.patch.object(paramiko, "SSHClient", mock.Mock(return_value=MockSSHClient())),\
             mock.patch("builtins.open", mock_open(read_data="data")):
            setup_remote_host("localhost", "opc", "welcome1", "id_rsa_iad103712exdcl09.opc")

    def test_mDisconnect(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on sshcon.mDisconnect")

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        with mock.patch.object(paramiko, "SSHClient", mock.Mock(return_value=MockSSHClient()) ):
            _node = sshconn("iad103712exdcl09.iad103712exd.adminiad1.oraclevcn.com", _options)
            _node.mSetUser("opc")
            _node.mConnect()
            _node.mDisconnect()

if __name__ == '__main__':
    unittest.main() 
