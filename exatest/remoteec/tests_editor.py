#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/remoteec/tests_editor.py /main/2 2022/11/14 13:51:02 hgaldame Exp $
#
# tests_help.py
#
# Copyright (c) 2021, 2022, Oracle and/or its affiliates.
#
#    NAME
#      tests_help.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    hgaldame    11/01/22 - 33995798 - exacc remoteec enhancements exaccops-hot
#    jesandov    04/05/21 - Creation
#

import os
import base64
import unittest
import uuid
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

from exabox.managment.src.EditorEndpoint import EditorEndpoint
from unittest.mock import patch, Mock
from pathlib import Path

class ebTestRemoteManagmentEditor(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateRemoteEC=True)
    
    def setUp(self):       
        self.ec_log_dir = os.path.join(self.mGetUtil().mGetExacloudPath(), "log", "threads", "0000-0000-0000-0000")
        if not os.path.exists(self.ec_log_dir):
            os.makedirs(self.ec_log_dir, mode=0o777, exist_ok=True)

    def test_000_list_files(self):

        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        # Execute endpoint
        _args = {
            "folder": self.mGetUtil().mGetExacloudPath()
        }
        _response1 = {}
        _endpoint = EditorEndpoint(_args, None, _response1, _shared)
        _endpoint.mGet()

        # Execute endpoint
        _response2 = {}
        _endpoint = EditorEndpoint(None, None, _response2, _shared)
        _endpoint.mGet()

        self.assertTrue(_response1, _response2)

        # Test get file
        _endpoint.mGetPath("README")

        # Test list files
        _endpoint.mListFiles(self.mGetUtil().mGetExacloudPath(), ".*")
        self.assertTrue(len(_endpoint.mGetResponse()['text']['files']) > 0)

        # Test list files
        _endpoint.mListFiles("/fdsaf/fdsaf/")
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)

    def test_001_file_content(self):

        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        # Execute endpoint
        _args = {
            "folder": self.mGetUtil().mGetExacloudPath(),
            "regex": ".*",
            "file": "exabox"
        }

        _response = {}
        _endpoint = EditorEndpoint(_args, None, _response, _shared)
        _endpoint.mGet()

        self.assertTrue("files" in _response['text'])
        self.assertTrue(len(_response['text']['files']) > 0)

        # Execute endpoint
        _args = {
            "folder": self.mGetUtil().mGetExacloudPath(),
            "regex": ".*",
            "offset": 5,
            "limit": 1,
            "file": "README"
        }

        _response = {}
        _endpoint = EditorEndpoint(_args, None, _response, _shared)
        _endpoint.mGet()

        self.assertTrue("filecontent" in _response['text'])
        self.assertEqual(len(_response['text']['filecontent']), 1)
        self.assertTrue("05" in _response['text']['filecontent'])

        self.assertEqual(_endpoint.mGetFileContent(aFile="/fdsaf/fdsa"), None)
        _endpoint.mGetFileContent(aFile="README", aOffset=0, aRegex="[0-9]{1,}")
        _endpoint.mGetFileContent(aFile="README", aLimit=3)


    def test_002_mGet_errors(self):

        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        # Invalid folder
        _args = {
            "folder": "/"
        }
        _endpoint = EditorEndpoint(_args, None, {}, _shared)
        self.assertEqual(_endpoint.mGet(), False)

        # Invalid offset, limit and file
        _args = {
            "folder": self.mGetUtil().mGetExacloudPath(),
            "file": "README_not_exists",
            "offset": "a",
            "limit": "a"
        }
        _endpoint = EditorEndpoint(_args, None, {}, _shared)
        _endpoint.mGet()
        self.assertEqual(_endpoint.mGetResponse()['status'], 404)

        # file outside boundary
        _args = {
            "file": "/etc/ssh/sshd_config",
        }
        _endpoint = EditorEndpoint(_args, None, {}, _shared)
        _endpoint.mGet()
        self.assertEqual(_endpoint.mGetResponse()['status'], 404)


    def test_003_create_files(self):

        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        # Create a folder
        _body = {
            "file": os.path.join(self.mGetUtil().mGetOutputDir(), "remoteec"),
            "type": "folder"
        }
        _endpoint = EditorEndpoint(None, _body, {}, _shared)
        _endpoint.mPost()

        self.assertTrue("text" in _endpoint.mGetResponse())

        # Create a file
        _body = {
            "file": "sample.txt",
            "folder": os.path.join(self.mGetUtil().mGetOutputDir(), "remoteec"),
            "type": "file",
            "text": "sample\n1\n2\n3\n4\n5\n"
        }
        _endpoint = EditorEndpoint(None, _body, {}, _shared)
        _endpoint.mPost()

        self.assertTrue("text" in _endpoint.mGetResponse())

    def test_004_create_files_errors(self):

        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        # Invalid Folder
        _body = {
            "file": "/etc/ssh/sshd_config",
            "type": "file"
        }
        _endpoint = EditorEndpoint(None, _body, {}, _shared)
        _endpoint.mPost()
        self.assertEqual(_endpoint.mGetResponse()['status'], 404)

        # Invalid Folder
        _body = {
            "folder": "/etc/ssh/",
            "file": "sshd_config",
            "type": "file"
        }
        _endpoint = EditorEndpoint(None, _body, {}, _shared)
        _endpoint.mPost()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)

        # File already exists
        _body = {
            "file": "README",
            "folder": self.mGetUtil().mGetExacloudPath() + "/../",
            "type": "file"
        }
        _endpoint = EditorEndpoint(None, _body, {}, _shared)
        _endpoint.mPost()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)

        # File already exists
        _body = {
            "file": "README",
            "type": "file"
        }
        _endpoint = EditorEndpoint(None, _body, {}, _shared)
        _endpoint.mPost()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)

    def test_005_change_files(self):

        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        # Change a file
        _body = {
            "folder": os.path.join(self.mGetUtil().mGetOutputDir(), "remoteec"),
            "file": "sample.txt",
            "offset": 0,
            "limit": 1,
            "text": "exatest"
        }
        _endpoint = EditorEndpoint(None, _body, {}, _shared)
        _endpoint.mPut()

        # Change a file
        _body = {
            "folder": os.path.join(self.mGetUtil().mGetOutputDir(), "remoteec"),
            "file": "sample.txt",
            "offset": "x",
            "limit": "x",
            "text": "exatest"
        }
        _endpoint = EditorEndpoint(None, _body, {}, _shared)
        _endpoint.mPut()

    def test_006_change_file_errors(self):

        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        # Invalid Folder
        _body = {
            "file": "/etc/ssh/sshd_config",
            "text": "x"
        }
        _endpoint = EditorEndpoint(None, _body, {}, _shared)
        _endpoint.mPut()
        self.assertEqual(_endpoint.mGetResponse()['status'], 404)

        # Invalid Folder
        _body = {
            "folder": "/etc/ssh/",
            "file": "sshd_config",
            "text": "x"
        }
        _endpoint = EditorEndpoint(None, _body, {}, _shared)
        _endpoint.mPut()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)

        # File not exists
        _body = {
            "file": "README2",
            "text": "x"
        }
        _endpoint = EditorEndpoint(None, _body, {}, _shared)
        _endpoint.mPut()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)

        # File is a directory
        _body = {
            "file": "exabox",
            "text": "x"
        }
        _endpoint = EditorEndpoint(None, _body, {}, _shared)
        _endpoint.mPut()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)


        _endpoint.mReplaceFile("/fdsfa/fdsaf", "x")


    def test_007_delete_file(self):

        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        # Delete a file
        _body = {
            "file": "sample.txt",
            "folder": os.path.join(self.mGetUtil().mGetOutputDir(), "remoteec"),
        }
        _endpoint = EditorEndpoint(None, _body, {}, _shared)
        _endpoint.mDelete()
        self.assertTrue("text" in _endpoint.mGetResponse())

        # Delete a folder
        _body = {
            "file": os.path.join(self.mGetUtil().mGetOutputDir(), "remoteec"),
        }
        _endpoint = EditorEndpoint(None, _body, {}, _shared)
        _endpoint.mDelete()
        self.assertTrue("text" in _endpoint.mGetResponse())

    def test_008_delete_files_errors(self):

        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        # Invalid Folder
        _body = {
            "file": "/etc/ssh/sshd_config",
            "text": "x"
        }
        _endpoint = EditorEndpoint(None, _body, {}, _shared)
        _endpoint.mDelete()
        self.assertEqual(_endpoint.mGetResponse()['status'], 404)

        # Invalid Folder
        _body = {
            "folder": "/etc/ssh/",
            "file": "sshd_config"
        }
        _endpoint = EditorEndpoint(None, _body, {}, _shared)
        _endpoint.mDelete()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)

        # Invalid Folder
        _body = {
            "file": "README2",
        }
        _endpoint = EditorEndpoint(None, _body, {}, _shared)
        _endpoint.mDelete()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)

        # Invalid folder
        _file = os.path.join(self.mGetUtil().mGetExacloudPath(), "x")
        self.mGetUtil().mGetRemoteEC().mExecuteLocal("mkdir -p {0}".format(_file))
        self.mGetUtil().mGetRemoteEC().mExecuteLocal("chmod 000 {0}".format(_file))

        _body = {
            "file": _file
        }
        _endpoint = EditorEndpoint(None, _body, {}, _shared)
        _endpoint.mDelete()
        self.mGetUtil().mGetRemoteEC().mExecuteLocal("rm -rf {0}".format(_file))
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)

        # Invalid file
        _rar ="/usr/local/packages/aime/install/run_as_root"
        _file = os.path.join(self.mGetUtil().mGetExacloudPath(), "y")
        self.mGetUtil().mGetRemoteEC().mExecuteLocal("touch {0}".format(_file))
        self.mGetUtil().mGetRemoteEC().mExecuteLocal('{0} "chattr +i {1}"'.format(_rar, _file))

        _body = {
            "file": _file
        }

        _endpoint = EditorEndpoint(None, _body, {}, _shared)
        _endpoint.mDelete()
        self.mGetUtil().mGetRemoteEC().mExecuteLocal('{0} "chattr -i {1}"'.format(_rar, _file))
        self.mGetUtil().mGetRemoteEC().mExecuteLocal("rm -rf {0}".format(_file))
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)

    def test_009_transfer(self):

        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        # Upload a file
        _body = {
            "mode": "upload",
            "remote": "a.txt",
            "local":  base64.b64encode(b"sample").decode('utf8')
        }
        _endpoint = EditorEndpoint(None, _body, {}, _shared)
        _endpoint.mPatch()

        # Download a file
        _body = {
            "mode": "download",
            "remote": "a.txt",
        }
        _endpoint = EditorEndpoint(None, _body, {}, _shared)
        _endpoint.mPatch()

    def test_010_transfer_errors(self):

        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        # Upload invalid
        _body = {
            "mode": "upload",
            "remote": "/etc/ssh/sshd_config",
            "local":  base64.b64encode(b"sample").decode('utf8')
        }
        _endpoint = EditorEndpoint(None, _body, {}, _shared)
        _endpoint.mPatch()

        # Download invalid
        _body = {
            "mode": "download",
            "remote": "/etc/ssh/sshd_config",
        }
        _endpoint = EditorEndpoint(None, _body, {}, _shared)
        _endpoint.mPatch()

        # Upload invalid
        _body = {
            "mode": "upload",
            "remote": "opt",
            "local":  base64.b64encode(b"sample").decode('utf8')
        }
        _endpoint = EditorEndpoint(None, _body, {}, _shared)
        _endpoint.mPatch()

        # Download invalid
        _body = {
            "mode": "download",
            "remote": "opt",
        }
        _endpoint = EditorEndpoint(None, _body, {}, _shared)
        _endpoint.mPatch()
    
    def test_011_list_filtered_exacloud_log_files(self):
        """
            Scenario: Get filtered exacloud logs
            Given a request for retrieve exacloud logs
            When regex parameter is not provided
            Then response should not include the log files who name does not match whith logs black list
        """
        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        # Execute endpoint
        _args = {
            "folder": os.path.join(self.mGetUtil().mGetExacloudPath(), "log/threads/0000-0000-0000-0000")
        }
        _response1 = {}
        _endpoint = EditorEndpoint(_args, None, _response1, _shared)

        mockListFiles = [] 
        for _log_name in _endpoint._EditorEndpoint__exacloudLogsBlackList:
            mockListFiles.append("{0}_{1}.log".format(str(uuid.uuid1(clock_seq=1)), _log_name))
        _valid_log = "{0}/{1}_cluctrl.createservice.ESTP_POSTGI_NID.log".format(self.ec_log_dir, str(uuid.uuid1(clock_seq=1)))
        mockListFiles.append(_valid_log)
        if os.path.exists(_valid_log):
            os.unlink(_valid_log)

        Path(_valid_log).touch()

        with patch('os.path.exists', side_effect = [True, True]),\
            patch('os.path.isdir', side_effect = [True]),\
            patch('os.listdir', return_value = mockListFiles):
            _endpoint.mGet()
        self.assertEqual(_endpoint.mGetResponse()['status'], 200)
        self.assertTrue("text" in _endpoint.mGetResponse())
        self.assertTrue(len(_endpoint.mGetResponse()['text']['files']) == 1)
        self.assertEqual(_endpoint.mGetResponse()['text']['files'][0]["name"], _valid_log)
        if os.path.exists(_valid_log):
            os.unlink(_valid_log)

    def test_012_list_ordered_files(self):
        """
            Scenario: Get a list of files from directory ordered by mtime
            Given a request for retrieve files from a directory
            When limit  parameter is provided
            Then response should include at most "limit" files
            and files has to be ordered by mtime
        """
        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _limit_files = 5
        # Execute endpoint
        _args = {
            "folder": self.mGetUtil().mGetExacloudPath(),
            "limit": _limit_files
        }
        _order_list = sorted(os.listdir(self.mGetUtil().mGetExacloudPath()), key= lambda _path : os.path.getmtime(_path), reverse=True)
        _response = {}
        _endpoint = EditorEndpoint(_args, None, _response, _shared)
        _endpoint.mGet()
        self.assertEqual(_endpoint.mGetResponse()['status'], 200)
        self.assertTrue("text" in _endpoint.mGetResponse())
        self.assertTrue(len(_endpoint.mGetResponse()['text']['files']) == _limit_files)
        for _index in range(_limit_files):
            with self.subTest(" Comparing orderer files at index: {0}".format(_index), _index=_index):
                self.assertEqual(_endpoint.mGetResponse()['text']['files'][_index]["name"], 
                os.path.join(self.mGetUtil().mGetExacloudPath(),_order_list[_index]))

if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end file
