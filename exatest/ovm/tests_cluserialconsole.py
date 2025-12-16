#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_cluserialconsole.py /main/1 2023/02/22 08:35:08 pbellary Exp $
#
# tests_cluserialconsole.py
#
# Copyright (c) 2023, Oracle and/or its affiliates.
#
#    NAME
#      tests_cluserialconsole.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    pbellary    01/13/23 - Creation
#

import unittest
import warnings
import os, re, uuid, copy
from unittest import mock
from unittest.mock import MagicMock, Mock, patch, mock_open

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo
from exabox.ovm.cluserialconsole import *
from exabox.exaoci.connectors.OCIConnector import OCIConnector
from exabox.exaoci.ExaOCIFactory import ExaOCIFactory
from exabox.core.Context import get_gcontext


PUB_KEY = """ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDXAonOM3kRgIKgjP1038N2rjMT+YcZgbrPIssyj//yMNFO5mBLugrqhOUjEglZsz+fJBcYfq6sN6gShEMDat8y7vgXYsX5nwsWj6JvOt5dJaLZM0Z/1CRvgiFjZ1bqJhgey3/PuiY7YVCoXPw/YuMLPjh1hQLy4UDmP6mS9jzYZ7u+baHvm9UKcTcCEFlr7c+6+urxeH7PonfMTS9LePf28GqwpKjAvFPyeFnwR81oCgPMBokAOl7ISQadlhTo3mbvqXOqJKArCer+rTZ0TV5MoelgpoAWgva9f/3WM1EYIGqjLCl+Yu+OG83aI5rBg2Ts+iJgWEyLuBxs0/y4CbewXoAasM6WEUFQBNeHeginWIDHESChsRBYuxYSAabw13YpHPCp6QNrFUwhqZkurLise0+6Z8PX2i03mB2gBIZs0JKkOU9NkwBz1f7SAk20PBXb8cu4e6rPrvVEnh8C++0E2hwSnAnaU9mXulcBFFKscexT1Eyell/zdjofDVLwxQM="""
CREATE_SSH_PAYLOAD = {'sshkey' : PUB_KEY}
CAPTURE_CONSOLE_PAYLOAD = {"sshkey": PUB_KEY, "vmid":"scaqar05dv0106.us.oracle.com", "namespace":"sic-dbaas", "bucket_name": "vm_history_console", "object_name":"console-history-20221208-1756"}

class MockObjectStorage(object):
    def __init__(self):
        self.__id = uuid.uuid4()

    def put_object(self, namespace_name, bucket_name, object_name, put_object_body, **kwargs):
        return MockObject()

    def get_object(self, namespace_name, bucket_name, object_name, **kwargs):
        pass
    
    def list_objects(self, namespace_name, bucket_name, **kwargs):
        return MockObject()

class MockObject(object):
    def __init__(self):
        self.headers = {'etag': 'ca096812-8c22-46bd-a075-caa028506592', 'last-modified': 'Fri, 09 Dec 2022 14:49:58 GMT', 'opc-content-md5': 'vPm6A6Y/ZcQrGAw8GqfKSw==', 'version-id': '6ba5399d-732a-4221-b3e0-820045e44fbe', 'Content-Length': '0', 'date': 'Fri, 09 Dec 2022 14:49:58 GMT', 'opc-request-id': 'phx-1:P7jrq3E39Es8tZTZTOs-QJX-v0GsW-wUNgzDUJY4f2a-OuX-fAZQp6o-aS0jjlqe', 'x-api-id': 'native', 'access-control-allow-origin': '*', 'access-control-allow-methods': 'POST,PUT,GET,HEAD,DELETE,OPTIONS', 'access-control-allow-credentials': 'true', 'access-control-expose-headers': 'access-control-allow-credentials,access-control-allow-methods,access-control-allow-origin,content-length,date,etag,last-modified,opc-client-info,opc-content-md5,opc-request-id,version-id,x-api-id'}
        _data = r"{'objects': 'object1'}"
        self.data = _data.replace("\'", "\"")

    def get_object_storage_client(self, aConnector: OCIConnector=None):
        return MockObjectStorage()

class ebTestCluSerialConsole(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestCluSerialConsole, self).setUpClass(aGenerateDatabase = True)
        warnings.filterwarnings("ignore")

    @patch("exabox.exaoci.ExaOCIFactory.ExaOCIFactory.get_object_storage_client", return_value=MockObjectStorage())
    def test_mUploadFile(self, aObjectStorage):
        ebLogInfo("Running unit test on cluserialconsole.py:mUploadFile")

        _namespace   = "sic-dbaas"
        _bucket      = "vm_history_console"
        _object_name = "console-history-20221208-1755"
        _dir         = "config"
        _file        = "exabox.conf"

        _consoleobj = serialConsole(self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
        _consoleobj.mUploadFile(_namespace, _bucket, _object_name, _dir, _file)
        ebLogInfo("Unit test on cluserialconsole.py:mUploadFile successful")

    @patch("exabox.exaoci.ExaOCIFactory.ExaOCIFactory.get_object_storage_client")
    def test_mGetObject(self, aObjectStorage):
        ebLogInfo("Running unit test on cluserialconsole.py:mGetObject")

        aObjectStorage.return_value = MockObjectStorage()

        _namespace   = "sic-dbaas"
        _bucket      = "vm_history_console"
        _object_name = "console-history-20221208-1755"
        _dir         = "config"
        _file        = "exabox.conf"

        _consoleobj = serialConsole(self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
        _consoleobj.mGetObject(_namespace, _bucket, _object_name)
        ebLogInfo("Unit test on cluserialconsole.py:mGetObject successful")

    @patch("exabox.exaoci.ExaOCIFactory.ExaOCIFactory.get_object_storage_client")
    def test_mListObject(self, aObjectStorage):
        ebLogInfo("Running unit test on cluserialconsole.py:mListObject")

        aObjectStorage.return_value = MockObjectStorage()

        _namespace   = "sic-dbaas"
        _bucket      = "vm_history_console"
        _object_name = "console-history-20221208-1755"
        _dir         = "config"
        _file        = "exabox.conf"

        _consoleobj = serialConsole(self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
        _consoleobj.mListObject(_namespace, _bucket)
        ebLogInfo("Unit test on cluserialconsole.py:mListObject successful")

    @patch("exabox.exaoci.ExaOCIFactory.ExaOCIFactory.get_object_storage_client")
    def test_mCreateSSH(self, aObjectStorage):
        ebLogInfo("Running unit test on cluserialconsole.py:mCreateSSH")

        _cmds = {                                           
                self.mGetRegexVm():
                [
                    [                        
                        exaMockCommand("/bin/mkdir -p /opt/oracle/vmbackup/conf/", aRc=0, aStdout="op1" ,aPersist=True), 

                    ]                                                      
                ],
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("/bin/uname -r", aRc=0, aStdout="4.14.35-2047.517.3.1.el7uek.x86_64", aPersist=True),
                        exaMockCommand("/bin/mkdir -p *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/test -e *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/scp *", aRc=0, aStdout="", aPersist=True)
                    ],
                    [
                        exaMockCommand("/bin/uname -r", aRc=0, aStdout="4.14.35-2047.517.3.1.el7uek.x86_64", aPersist=True),
                        exaMockCommand("/bin/scp *", aRc=0, aStdout="", aPersist=True),
                    ],
                    [
                        exaMockCommand("timeout 30s docker ps *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("timeout 30s docker images | egrep 'exa-hippo-serialmux|exa-hippo-sshd'", aRc=0, aStdout="", aPersist=True),
                    ],
                    [
                        exaMockCommand("/bin/uname -r", aRc=0, aStdout="4.14.35-2047.517.3.1.el7uek.x86_64", aPersist=True),
                    ],
                    [
                        exaMockCommand("/bin/uname -r", aRc=0, aStdout="4.14.35-2047.517.3.1.el7uek.x86_64", aPersist=True),
                        exaMockCommand("timeout 30s docker restart *", aRc=0, aStdout="", aPersist=True),
                    ],
                    [
                        exaMockCommand("timeout 30s docker images *", aRc=0, aStdout="", aPersist=True),
                    ],
                    [
                        exaMockCommand("timeout 30s docker restart *", aRc=0, aStdout="", aPersist=True),
                    ]
                ],
                self.mGetRegexLocal():
                [
                    [
                        exaMockCommand("/bin/rm vmbackup.conf", aRc=0, aStdout="", aPersist=True)
                    ]
                ]
                }                                        
        self.mPrepareMockCommands(_cmds)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _json_object = json.dumps(CREATE_SSH_PAYLOAD)
        _options.jsonconf = json.loads(_json_object)

        aObjectStorage.return_value = MockObjectStorage()

        _namespace   = "sic-dbaas"
        _bucket      = "vm_history_console"
        _object_name = "console-history-20221208-1755"
        _dir         = "config"
        _file        = "exabox.conf"

        _consoleobj = serialConsole(self.mGetClubox(), _options)
        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():
            _consoleobj.mCreateSSH(_dom0, _domU)
        ebLogInfo("Unit test on cluserialconsole.py:mCreateSSH successful")

    @mock.patch("exabox.ovm.cluserialconsole.serialConsole.mUploadFile")
    @patch("exabox.exaoci.ExaOCIFactory.ExaOCIFactory.get_object_storage_client")
    def test_mCaptureConsoleHistory(self, aObjectStorage, aUploadFile):
        ebLogInfo("Running unit test on cluserialconsole.py:mCaptureConsoleHistory")

        _cmds = {                                           
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("/bin/uname -r", aRc=0, aStdout="4.14.35-2047.517.3.1.el7uek.x86_64", aPersist=True),
                        exaMockCommand("/bin/mkdir -p *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/test -e *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/usr/bin/python3 *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/rm -rf *", aRc=0, aStdout="", aPersist=True),
                    ],
                    [
                        exaMockCommand("timeout 30s docker ps *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/scp *", aRc=0, aStdout="", aPersist=True),
                    ],
                    [
                        exaMockCommand("timeout 30s docker restart *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/usr/bin/python3 /opt/exacloud/vmconsole/history_console.py *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/test -e *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/rm -rf *", aRc=0, aStdout="", aPersist=True),

                    ]
                ]
                }                                        
        self.mPrepareMockCommands(_cmds)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _json_object = json.dumps(CAPTURE_CONSOLE_PAYLOAD)
        _options.jsonconf = json.loads(_json_object)

        aObjectStorage.return_value = MockObjectStorage()
        aUploadFile.return_value = MockObject()

        _namespace   = "sic-dbaas"
        _bucket      = "vm_history_console"
        _object_name = "console-history-20221208-1755"
        _dir         = "config"
        _file        = "exabox.conf"

        _consoleobj = serialConsole(self.mGetClubox(), _options)
        with patch ('os.path.exists', return_value=True),\
             patch ('os.remove'),\
             patch ("builtins.open", mock_open(read_data="file_name".encode())):
             for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():
                 _consoleobj.mCaptureConsoleHistory(_dom0, _domU)
        ebLogInfo("Unit test on cluserialconsole.py:mCaptureConsoleHistory successful")

    @patch("exabox.exaoci.ExaOCIFactory.ExaOCIFactory.get_object_storage_client")
    def test_mRemoveSSH(self, aObjectStorage):
        ebLogInfo("Running unit test on cluserialconsole.py:mRemoveSSH")

        _cmds = { 
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("/bin/mkdir -p *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/test -e *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/scp *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/rm -rf *", aRc=0, aStdout="", aPersist=True),
                    ],
                    [
                        exaMockCommand("/bin/scp *", aRc=0, aStdout="", aPersist=True),
                    ],
                    [
                        exaMockCommand("/bin/uname -r", aRc=0, aStdout="4.14.35-2047.517.3.1.el7uek.x86_64", aPersist=True),

                    ],
                    [
                        exaMockCommand("timeout 30s docker restart *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("timeout 30s docker stop *", aRc=0, aStdout="", aPersist=True)

                    ]
                ]
                }                                        
        self.mPrepareMockCommands(_cmds)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _json_object = json.dumps(CREATE_SSH_PAYLOAD)
        _options.jsonconf = json.loads(_json_object)

        aObjectStorage.return_value = MockObjectStorage()

        _namespace   = "sic-dbaas"
        _bucket      = "vm_history_console"
        _object_name = "console-history-20221208-1755"
        _dir         = "config"
        _file        = "exabox.conf"

        _consoleobj = serialConsole(self.mGetClubox(), _options)
        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():
            _consoleobj.mRemoveSSH(_dom0, _domU)
        ebLogInfo("Unit test on cluserialconsole.py:mRemoveSSH successful")

if __name__ == '__main__':
    unittest.main()