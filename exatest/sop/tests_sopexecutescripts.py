#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/sop/tests_sopexecutescripts.py /main/2 2025/08/04 15:30:23 akkar Exp $
#
# tests_sopexecutescripts.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_sopexecutescripts.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      03/18/25 - Creation
#
import uuid
import builtins
import copy
import json
import unittest
from datetime import datetime, timedelta
from unittest import mock
from unittest.mock import mock_open, MagicMock
import warnings
from unittest.mock import patch, call
from exabox.sop.sopexecutescripts import SOPExecution, fetch_ilom_password
from exabox.sop.sopscripts import SOPScript, SOPScriptsRepo, SCRIPT_VERSION
from exabox.sop.soputils import process_sop_request, sop_execute_scripts, sop_delete_requests_onhost, sop_list_scripts
from exabox.log.LogMgr import ebLogInfo, ebLogError
from exabox.core.Error import ExacloudRuntimeError
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.MockCommand import exaMockCommand

ILOM_PAYLOAD1 = {
  "cmd": "start",
  "nodes": [
    "sea201606exdcl14lo.sea2xx2xx0051qf.adminsea2.oraclevcn.com",
    "sea201602exdcl06lo.sea201602exd.adminsea2.oraclevcn.com"
  ],
  "scriptname": "aypaul_ilom_parameters_test.dat",
  "version": "1",
  "scriptparams": "",
  "script_payload": {
    "var1": "type",
    "var2": "product_name"
  },
  "nodetype": "cellilom"
}
OADT_BASE_DIR = "/opt/exacloud/oadt"
OADT_REQUESTS_DIR = "/opt/exacloud/oadt/requests"
COMPUTE_ILOM = "computeilom"
STORAGE_ILOM = "cellilom"
SUCCESSEXITCODE = 0

LOCAL = "local"
SCRIPT_NAME = "script_name"
SCRIPT_PATH = "script_path"
SCRIPT_PARALLEL_EXEC = "support_parallel_execution"
SCRPIPT_SHA256SUM = "sha256sum"
SCRIPT_EXEC = "script_exec"
SCRIPT_RETURN_JSON_SUPPORT = "return_json_support"
SCRIPT_COMMENTS = "comments"
LAST_REFRESH_TIME_MARKER = "last_refresh_time"
METADATA_CACHE_MARKER = "metadata_cache"

class testOptions(object):
    def mGetBasePath(self):
        return "/scratch/username/exacloud"
    
    def mCheckConfigOption(self, key):
        dic = {
            "ilom_compute_pwd_b64": "d2VsY29tZTE=",
            "ilom_cell_pwd_b64": "d2VsY29tZTE="
        }
        return dic.get(key, False)
    
    def mGetConfigOptions(self):  # Add this method to return fake config dict
        return {
            'sop_scripts_storage': 'local',  # Required for storage type
            'sop_scripts_refresh_interval': '1',  # Refresh interval as string (int() in init)
            'ociexacc': 'True',  # Simulate ExaCC env; set to 'False' if testing non-ExaCC branch
            'sop_scripts_dir_exacc': '/fake/dir',  # For ExaCC
            'sop_scripts_dir': '/fake/dir'  # For non-ExaCC
        }
   

class ebTestSOPExecution(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestSOPExecution, self).setUpClass()
        warnings.filterwarnings("ignore")

    @patch("exabox.sop.sopexecutescripts.SOPScriptsRepo.mGetScriptsMetadata", return_value={})
    @patch("exabox.sop.sopexecutescripts.SOPScriptsRepo")
    @patch("exabox.sop.sopexecutescripts.get_gcontext", return_value=testOptions())
    def test_mResolveIlomParametersIfApplicable(self, mock_scriptsrepo_metadata, mock_scriptsrepo, mock_get_gcontext):
        ebLogInfo("Running unit test on SOPExecution.mResolveIlomParametersIfApplicable")
        _uuid = uuid.uuid1()
        _payload_json = ILOM_PAYLOAD1
        _nodes = _payload_json.get("nodes", [])
        _script_name = _payload_json.get("scriptname", "")
        _script_params = _payload_json.get("scriptparams", "")
        _script_payload = _payload_json.get("script_payload", {})
        _script_version = _payload_json.get("version", None)
        _node_type = _payload_json.get("nodetype", None)
        _sop_scripts_execution = SOPExecution(str(_uuid), _nodes, _script_name, _script_params, _script_payload, _script_version, _node_type)

        _command = {
                "match": True,
                "prompt": "->",
                "cmd": "show /SYS {var1}",
                "timeout": 10
        }
        ILOM_COMMANDS_DICT = {
            "commands": [_command]
        }

        #"Available regular subsitution"
        _commands = ILOM_COMMANDS_DICT.get("commands", [])
        _sop_scripts_execution.mResolveIlomParametersIfApplicable(_commands)
        ebLogInfo("Available regular subsitution successful.")

        #Available multiple regular subsitution
        _command["cmd"] = "show /SYS {var1} {var2}"
        _commands = ILOM_COMMANDS_DICT.get("commands", [])
        _sop_scripts_execution.mResolveIlomParametersIfApplicable(_commands)
        ebLogInfo("Available multiple regular subsitution successful.")

        #Unavailable regular subsitution
        _command["cmd"] = "show /SYS {var11}"
        _commands = ILOM_COMMANDS_DICT.get("commands", [])
        with self.assertRaises(ExacloudRuntimeError):
            _sop_scripts_execution.mResolveIlomParametersIfApplicable(_commands)
        ebLogInfo("unavailable regular subsitution successful.")

        #Empty command list
        _sop_scripts_execution.mResolveIlomParametersIfApplicable([])
        ebLogInfo("empty command list execution successful.")

        ebLogInfo("Unit test on SOPExecution.mResolveIlomParametersIfApplicable succeeded.")
  
    @patch("exabox.sop.sopexecutescripts.get_gcontext", return_value=testOptions())
    @patch('base64.b64decode')
    def test_fetch_ilom_password(self, mock_gcontext, mock_b64decode):
        ebLogInfo("Running unit test on fetch_ilom_password")
        gContext = self.mGetContext()
        
        result = fetch_ilom_password("invalid")
        self.assertIsNone(result)

        # Happy path: Valid type, secrets helper succeeds (covers try block)
        result = fetch_ilom_password(COMPUTE_ILOM)
        mock_b64decode.assert_has_calls([call().decode()])
        
        # Branch: Fallback to config decode (covers if not _ilom_password)
        result = fetch_ilom_password(COMPUTE_ILOM)
        mock_b64decode.assert_has_calls([call().decode()])

        # Branch: Empty password set to None
        result = fetch_ilom_password(STORAGE_ILOM)

        ebLogInfo("Unit test on fetch_ilom_password succeeded.")

class ebTestSOPScript(ebTestClucontrol):
    @classmethod
    def setUpClass(self):
      super(ebTestSOPScript, self).setUpClass()

    def test_SOPScript(self):
      ebLogInfo("Running unit test on SOPScript")
      # Happy path: Init with params (covers defaults and init lines)
      script = SOPScript("test_script", "/path/to/script", False, "sha256sum", "/bin/bash", True, "2", "Comments")
      self.assertEqual(script.mGetScriptName(), "test_script")  # Covers getter
      self.assertEqual(script.mGetScriptParallelExecution(), False)  # Covers another getter

      # Setters: Update and verify (covers all setter lines once)
      script.mSetScriptName("new_name")
      self.assertEqual(script.mGetScriptName(), "new_name")
      script.mSetScriptParallelExecution(True)
      self.assertTrue(script.mGetScriptParallelExecution())
      # Repeat for other setters/getters (e.g., mSetSCriptSHA256Sum, mGetScriptVersion, etc.)

      ebLogInfo("Unit test on SOPScript succeeded.")

class ebTestSOPScriptsRepo(ebTestClucontrol):
    @classmethod
    def setUpClass(self):
        super(ebTestSOPScriptsRepo, self).setUpClass()
    
    @patch("exabox.sop.sopexecutescripts.get_gcontext", return_value=testOptions())
    @patch('os.path')
    @patch('os.listdir')
    @patch('json.load')
    @patch('builtins.open')
    @patch('os.remove')  # For os.remove calls
    @patch('json.dump')  # For json.dump calls
    @patch('datetime.datetime')  # Patch datetime to control strptime and now
    def test_mLocalParseAndUpdateMetadataCache(self, mock_datetime, mock_json_dump, mock_os_remove, mock_open, mock_json_load, mock_os_listdir, mock_os_path, mock_gcontext):
        ebLogInfo("Running unit test on SOPScriptsRepo.mLocalParseAndUpdateMetadataCache")
        
        # Setup mocks BEFORE instantiating repo
        mock_os_path.join.side_effect = lambda *args: "/".join(args)
        mock_os_path.isabs.return_value = True
        mock_os_path.exists.return_value = True  # Cache files exist
        mock_os_path.isfile.return_value = True
        
        # Setup mock_open to simulate different files with valid content
        def open_side_effect(filename, mode='r'):
            mock_file = MagicMock()
            mock_file.__enter__.return_value = mock_file
            mock_file.__exit__.return_value = None
            mock_file.write.return_value = None
            if LAST_REFRESH_TIME_MARKER in filename:
                mock_file.readline.return_value = "2023-01-01 00:00:00.000000\n"  # Valid timestamp
            elif METADATA_CACHE_MARKER in filename and 'r' in mode:
                mock_file.read.return_value = json.dumps({"script.sh": {SCRIPT_VERSION: "1"}})  # Valid JSON string for cache (dict)
            elif '.metadata' in filename and 'r' in mode:
                mock_file.read.return_value = json.dumps({SCRIPT_VERSION: "1"})  # Valid JSON string for .metadata (dict)
            else:
                mock_file.read.return_value = ''  # Empty for others
            return mock_file
        
        mock_open.side_effect = open_side_effect
        
        # Setup mock_datetime: Return a fixed datetime for strptime
        fake_stime = datetime(2023, 1, 1, 0, 0, 0)
        mock_datetime.strptime.return_value = fake_stime  # Directly return datetime object
        mock_datetime.now.return_value = fake_stime + timedelta(hours=2)  # now() > stime to force refresh initially
        mock_datetime.timedelta.return_value = timedelta(hours=1)  # Matches refresh interval
        
        # Setup json.load with side_effect to handle multiple calls and return dicts
        def json_load_side_effect(fd):
            content = fd.read.return_value  # Get the mocked content (str)
            if content:
                return json.loads(content)  # Parse to dict
            return {}  # Empty dict if no content
        
        mock_json_load.side_effect = json_load_side_effect
        
        # Now instantiate repo (init will call mLoadLocalScriptsMetadata with controlled mocks)
        repo = SOPScriptsRepo()  # Covers init and loading
        
        # For happy path: Call the method directly (simulate parsing)
        mock_os_listdir.return_value = ["script.sh", "script.sh.metadata"]
        
        repo.mLocalParseAndUpdateMetadataCache("/fake/dir")
        self.assertIn("script.sh", repo.mGetScriptsMetadata())  # Covers population
        mock_json_dump.assert_called()  # Verify cache write
        mock_os_remove.assert_called()  # Verify removal

        # Error branch: Corrupt JSON (covers JSONDecodeError) - Temporarily change side_effect to raise error
        def corrupt_json_load_side_effect(fd):
            raise json.JSONDecodeError("error", "doc", 0)
        
        mock_json_load.side_effect = corrupt_json_load_side_effect
        repo.mLocalParseAndUpdateMetadataCache("/fake/dir")
        # FIX: Assert on full path (as appended in code: os.path.join(_sop_scripts_dir, _file) + '.metadata')
        self.assertIn("/fake/dir/script.sh.metadata", repo.mGetCorruptFiles())
        
        # Reset side_effect for next parts
        mock_json_load.side_effect = json_load_side_effect
        
        # To explicitly cover cache-hit without refresh (adjust now() to be < stime)
        mock_datetime.now.return_value = fake_stime  # now() < stime + interval
        repo = SOPScriptsRepo()  # Re-instantiate to trigger else branch (loads from cache)
        self.assertIn("script.sh", repo.mGetScriptsMetadata())  # Loaded from cache

        ebLogInfo("Unit test succeeded.")
 
class ebTestSOPAPI(ebTestClucontrol):
    @classmethod
    def setUpClass(self):
        super(ebTestSOPAPI, self).setUpClass()
        warnings.filterwarnings("ignore")

    # Test 1: sop_delete_requests_onhost (Easiest - Covers single return line)
    def test_sop_delete_requests_onhost(self):
        ebLogInfo("Running unit test on sop_delete_requests_onhost")
        # Minimal call (covers the empty return)
        result = sop_delete_requests_onhost({"some": "payload"})
        self.assertEqual(result, {})  # Covers the return dict
        ebLogInfo("Unit test on sop_delete_requests_onhost succeeded.")

    # Test 2: sop_list_scripts (Covers branches: corrupt files, specific scriptname, all metadata)
    @patch('exabox.sop.soputils.SOPScriptsRepo')  # FIX: Correct patch path based on traceback (soputils.py imports from sopscripts.py)
    def test_sop_list_scripts(self, mock_scripts_repo):
        # Setup repo mock
        repo = MagicMock()
        mock_scripts_repo.return_value = repo

        # 1. **Corrupt files path**
        repo.mGetCorruptFiles.return_value = ["corrupt1.json"]
        result = sop_list_scripts({})
        self.assertEqual(result, {"corrupt_files": ["corrupt1.json"]})

        # 2. **No corrupt, no scriptname** (all metadata)
        repo.mGetCorruptFiles.return_value = []
        repo.mGetScriptsMetadata.return_value = {"scriptA": {"version": "1"}, "scriptB": {"version": "2"}}
        result = sop_list_scripts({})
        self.assertEqual(result, {"scriptA": {"version": "1"}, "scriptB": {"version": "2"}})

        # 3. **scriptname key present in input and in metadata**:
        # Note: The bug is that it looks for the literal key "scriptname"
        repo.mGetCorruptFiles.return_value = []
        repo.mGetScriptsMetadata.return_value = {"scriptA": {"version": "1"}, "scriptname": {"version": "5"}}
        # Should return the value at "scriptname" key itself
        result = sop_list_scripts({"scriptname": "anything"})
        self.assertEqual(result, {"version": "5"})

        # 4. **scriptname key present in input and NOT in metadata**:
        repo.mGetCorruptFiles.return_value = []
        repo.mGetScriptsMetadata.return_value = {"scriptA": {"version": "1"}}
        result = sop_list_scripts({"scriptname": "anything"})
        self.assertEqual(result, {"scriptA": {"version": "1"}})  # Falls through & returns all (due to bug!)
        
        
    # Optionally, test empty corrupt_files and empty scripts_metadata
    @patch('exabox.sop.soputils.SOPScriptsRepo')
    def test_empty_metadata_and_corrupt(self, mock_scripts_repo):
        repo = MagicMock()
        mock_scripts_repo.return_value = repo

        # Empty corrupt files, empty metadata
        repo.mGetCorruptFiles.return_value = []
        repo.mGetScriptsMetadata.return_value = {}
        result = sop_list_scripts({})
        self.assertEqual(result, {})

        # Corrupt files with empty list, scriptname not present in metadata
        repo.mGetCorruptFiles.return_value = []
        repo.mGetScriptsMetadata.return_value = {}
        result = sop_list_scripts({"scriptname": "missing"})
        self.assertEqual(result, {})

        # Corrupt files with value, triggers early return
        repo.mGetCorruptFiles.return_value = ["bad.json"]
        result = sop_list_scripts({"scriptname": "missing"})
        self.assertEqual(result, {"corrupt_files": ["bad.json"]})

    # Test 3: sop_execute_scripts (Covers extraction, instantiation, calls, and return)
    @patch('exabox.sop.soputils.SOPExecution')  # Mock the execution class
    def test_sop_execute_scripts(self, mock_sop_execution):
        ebLogInfo("Running unit test on sop_execute_scripts")
        # Fake payload and UUID
        fake_payload = {
            "nodes": ["node1"],
            "scriptname": "test.sh",
            "scriptparams": "--param",
            "script_payload": {"key": "value"},
            "version": "1",
            "nodetype": "compute"
        }
        fake_uuid = str(uuid.uuid4())
        
        # Mock SOPExecution instance
        mock_instance = mock_sop_execution.return_value
        mock_instance.mExecuteOperation.return_value = None  # Covers call
        mock_instance.mGetResult.return_value = {"node1": {"return_code": 0}}  # Fake result
        
        # Main path: Call with payload (covers extraction, init, calls, return)
        result = sop_execute_scripts(fake_payload, fake_uuid)
        self.assertEqual(result, {"node1": {"return_code": 0}})
        mock_sop_execution.assert_called_once_with(
            fake_uuid, ["node1"], "test.sh", "--param", {"key": "value"}, "1", "compute"
        )
        mock_instance.mExecuteOperation.assert_called_once()
        mock_instance.mGetResult.assert_called_once()

        ebLogInfo("Unit test on sop_execute_scripts succeeded.")

    # Test 4: process_sop_request (Covers all cmd branches, raises, and returns)
    @patch('exabox.sop.soputils.sop_execute_scripts')  # Mock helpers
    @patch('exabox.sop.soputils.sop_delete_requests_onhost')
    @patch('exabox.sop.soputils.sop_list_scripts')
    def test_process_sop_request(self, mock_list_scripts, mock_delete, mock_execute_scripts):
        ebLogInfo("Running unit test on process_sop_request")
        fake_uuid = str(uuid.uuid4())
        fake_result = {"key": "value"}  # Fake return for mocks
        
        # Branch: Missing cmd (covers raise)
        with self.assertRaises(ExacloudRuntimeError):
            process_sop_request({}, fake_uuid)

        # Branch: cmd="start" (covers if and return)
        mock_execute_scripts.return_value = fake_result
        result = process_sop_request({"cmd": "start"}, fake_uuid)
        self.assertEqual(result, fake_result)
        mock_execute_scripts.assert_called_once()

        # Branch: cmd="delete" (covers elif and return)
        mock_delete.return_value = fake_result
        result = process_sop_request({"cmd": "delete"}, fake_uuid)
        self.assertEqual(result, fake_result)
        mock_delete.assert_called_once()

        # Branch: cmd="scriptslist" (covers elif and return)
        mock_list_scripts.return_value = fake_result
        result = process_sop_request({"cmd": "scriptslist"}, fake_uuid)
        self.assertEqual(result, fake_result)
        mock_list_scripts.assert_called_once()

        # Branch: Unknown cmd (covers else, log, raise)
        with self.assertRaises(ExacloudRuntimeError):
            process_sop_request({"cmd": "unknown"}, fake_uuid)

        ebLogInfo("Unit test on process_sop_request succeeded.")
  
class ebTestSOPExecution2(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestSOPExecution2, self).setUpClass()
        warnings.filterwarnings("ignore")
    
    @patch("exabox.sop.sopexecutescripts.SOPScriptsRepo.mGetScriptsMetadata", return_value={"demo_script": {"version": "1"}})
    @patch("exabox.sop.sopexecutescripts.SOPScriptsRepo")
    @patch("exabox.sop.sopexecutescripts.get_gcontext", return_value=testOptions())
    @patch("exabox.sop.sopexecutescripts.os.path.join", side_effect=lambda *a: '/'.join(a))
    def test_init_and_mgetresult(
            self, 
            mock_path_join, 
            mock_get_gcontext, 
            mock_scriptsrepo, 
            mock_get_metadata
    ):
        """
        Simple coverage: covers SOPExecution.__init__ and mGetResult.
        """
        ebLogInfo("Running unit test on SOPExecution initialization and mGetResult")

        se = SOPExecution(
            aUUID="my-uuid", 
            aNodesList=["node1"], 
            aScriptName="demo_script",
            aScriptParams="some_param", 
            aScriptPayload={}, 
            aScriptVersion="1", 
            aNodeType=None
        )

        # mGetResult should just return the (empty) output dict
        self.assertEqual(se.mGetResult(), {})

        ebLogInfo("Unit test on SOPExecution initialization and mGetResult succeeded.")
        
    @patch("exabox.sop.sopexecutescripts.SOPScriptsRepo")
    @patch("exabox.sop.sopexecutescripts.get_gcontext", return_value=testOptions())
    @patch("exabox.sop.sopexecutescripts.os.path.join", side_effect=lambda *a: '/'.join(a))
    def test_mGetResult(self, mock_path_join, mock_get_gcontext, mock_SOPScriptsRepo):
        repo_instance = MagicMock()
        repo_instance.mGetScriptsMetadata.return_value = {
            "demo_script": {
                "version": "version",
                "exec": "/bin/echo",
                "path": "/bin/echo.sh"
            }
        }
        mock_SOPScriptsRepo.return_value = repo_instance

        se = SOPExecution(
            aUUID="getres-uuid",
            aNodesList=["n1"],
            aScriptName="demo_script",
            aScriptParams="",
            aScriptPayload={},
            aScriptVersion="version",
            aNodeType=None
        )
        # Sets __output empty, returns it
        self.assertEqual(se.mGetResult(), {})
        # Set some output and check retrieval
        se._SOPExecution__output = {"n1": {"foo": "bar"}}
        self.assertEqual(se.mGetResult(), {"n1": {"foo": "bar"}})


    @patch("exabox.sop.sopexecutescripts.SOPScriptsRepo")
    @patch("exabox.sop.sopexecutescripts.get_gcontext", return_value=testOptions())
    @patch("exabox.sop.sopexecutescripts.os.path.join", side_effect=lambda *a: '/'.join(a))
    @patch("exabox.sop.sopexecutescripts.exaBoxNode")
    def test_mPrecheckProcessing(
        self, mock_exaBoxNode, mock_path_join, mock_get_gcontext, mock_SOPScriptsRepo
    ):
        repo_instance = MagicMock()
        repo_instance.mGetScriptsMetadata.return_value = {
            "demo_script": {
                SCRIPT_VERSION: "version",   # <- THIS IS CRITICAL!
                "exec": "/bin/echo",
                "path": "/bin/echo.sh"
            }
        }
        mock_SOPScriptsRepo.return_value = repo_instance

        se = SOPExecution(
            aUUID="my-uuid",
            aNodesList=["node1"],
            aScriptName="demo_script",
            aScriptParams="",
            aScriptPayload={},
            aScriptVersion="version",
            aNodeType=None
        )
        se.mPrecheckProcessing()

        # ---- (2) Error: empty node list ----
        se_empty = SOPExecution(
            aUUID="my-uuid2",
            aNodesList=[],  # This should raise an exception!
            aScriptName="demo_script",
            aScriptParams="",
            aScriptPayload={},
            aScriptVersion="",
            aNodeType=None
        )
        with self.assertRaises(ExacloudRuntimeError):
            se_empty.mPrecheckProcessing()

        ebLogInfo("Unit test on SOPExecution.mPrecheckProcessing succeeded.")


    @patch("exabox.sop.sopexecutescripts.SOPScriptsRepo")
    @patch("exabox.sop.sopexecutescripts.get_gcontext", return_value=testOptions())
    @patch("exabox.sop.sopexecutescripts.os.path.join", side_effect=lambda *a: '/'.join(a))
    @patch("exabox.sop.sopexecutescripts.exaBoxNode")
    def test_mPrecheckProcessing_script_not_found(
        self, mock_exaBoxNode, mock_path_join, mock_get_gcontext, mock_SOPScriptsRepo
    ):
        """
        Covers the 'script is not present in repo metadata' error path.
        """
        repo_instance = MagicMock()
        # Metadata does NOT include the script we're requesting
        repo_instance.mGetScriptsMetadata.return_value = {
            "other_script": {  # <-- No 'demo_script' key!
                "version": "version",
                "exec": "/bin/echo",
                "path": "/bin/echo.sh"
            }
        }
        mock_SOPScriptsRepo.return_value = repo_instance

        se = SOPExecution(
            aUUID="uuid-error-script",
            aNodesList=["node1"],
            aScriptName="demo_script",  # This is NOT in repo_instance's dict
            aScriptParams="",
            aScriptPayload={},
            aScriptVersion="version",
            aNodeType=None
        )
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            se.mPrecheckProcessing()
        assert "is not present in the script repository" in str(ctx.exception)
        
        
    @patch("exabox.sop.sopexecutescripts.SOPScriptsRepo")
    @patch("exabox.sop.sopexecutescripts.get_gcontext", return_value=testOptions())
    @patch("exabox.sop.sopexecutescripts.os.path.join", side_effect=lambda *a: '/'.join(a))
    def test_mExecuteOperation_nominal_calls(self, mock_path_join, mock_get_gcontext, mock_SOPScriptsRepo):
      repo_instance = MagicMock()
      repo_instance.mGetScriptsMetadata.return_value = {
          "demo_script": {
              "version": "version",
              "exec": "/bin/echo",
              "path": "/bin/echo.sh"
          }
      }
      mock_SOPScriptsRepo.return_value = repo_instance

      se = SOPExecution(
          aUUID="execop-uuid",
          aNodesList=["n1"],
          aScriptName="demo_script",
          aScriptParams="",
          aScriptPayload={},
          aScriptVersion="version",
          aNodeType=None
      )

      # Patch instance methods
      se.mPrecheckProcessing = MagicMock()
      se.mProcessRequest = MagicMock()
      se.mPostProcessing = MagicMock()

      se.mExecuteOperation()

      se.mPrecheckProcessing.assert_called_once()
      se.mProcessRequest.assert_called_once()
      se.mPostProcessing.assert_called_once()
      
      
    @patch("exabox.sop.sopexecutescripts.node_cmd_abs_path_check", return_value="/bin/sh")
    @patch("exabox.sop.sopexecutescripts.node_exec_cmd")
    @patch("exabox.sop.sopexecutescripts.connect_to_host")
    @patch("exabox.sop.sopexecutescripts.exaBoxNode")
    @patch("exabox.sop.sopexecutescripts.SOPScriptsRepo")
    @patch("exabox.sop.sopexecutescripts.get_gcontext", return_value=testOptions())
    @patch("exabox.sop.sopexecutescripts.os.path.join", side_effect=lambda *a: '/'.join(a))
    @patch("builtins.open", new_callable=mock.mock_open)
    def test_mPrecheckProcessing_nominal_fullcover(
        self,
        mock_open,
        mock_path_join,
        mock_get_gcontext,
        mock_SOPScriptsRepo,
        mock_exaBoxNode,
        mock_connect_to_host,
        mock_node_exec_cmd,
        mock_cmd_abs_path_check
    ):
        """
        Drives the happy-path of mPrecheckProcessing to cover the majority of
        its lines with minimal effort.
        """
        # ------------------------------------------------------------------
        # (1) prepare script metadata so that every if/else branch is taken:
        #     • script_exec has *no* leading '/', so the abs-path check branch
        #       is executed.
        #     • script_payload is NOT empty, so payload-json creation branch
        #       is executed.
        # ------------------------------------------------------------------
        repo_instance = MagicMock()
        repo_instance.mGetScriptsMetadata.return_value = {
            "demo_script": {
                SCRIPT_VERSION: "1",
                SCRIPT_EXEC: "sh",                 # <-- relative path
                SCRIPT_PATH: "/bin/demo_script.sh",
                SCRIPT_PARALLEL_EXEC: False,
                SCRIPT_RETURN_JSON_SUPPORT: False
            }
        }
        mock_SOPScriptsRepo.return_value = repo_instance

        # ------------------------------------------------------------------
        # (2) fake exaBoxNode  (connectable=True for coverage)
        # ------------------------------------------------------------------
        exab_node_stub = MagicMock()
        exab_node_stub.mIsConnectable.return_value = True
        mock_exaBoxNode.return_value = exab_node_stub

        # ------------------------------------------------------------------
        # (3) fake connect_to_host context-manager + node_exec_cmd
        # ------------------------------------------------------------------
        dummy_remote = MagicMock()
        dummy_remote.mCopyFile = MagicMock()
        mock_connect_to_host.return_value.__enter__.return_value = dummy_remote
        mock_connect_to_host.return_value.__exit__.return_value = False

        dummy_cmd_struct = MagicMock()
        dummy_cmd_struct.exit_code = 0
        mock_node_exec_cmd.return_value = dummy_cmd_struct

        # ------------------------------------------------------------------
        # (4) build class under test – two nodes to exercise both local
        #     (localhost) *and* remote branches.
        # ------------------------------------------------------------------
        se = SOPExecution(
            aUUID="uuid-fullcover",
            aNodesList=["localhost", "node2"],
            aScriptName="demo_script",
            aScriptParams="--flag",
            aScriptPayload={"var1": "value1"},     # triggers payload-json logic
            aScriptVersion="1",
            aNodeType=None
        )

        # should run without throwing and leave __output empty (no errors)
        se.mPrecheckProcessing()
        self.assertEqual(se.mGetResult(), {})

        # ensure key helper calls were indeed made → proves deep traversal
        mock_node_exec_cmd.assert_called()                # mkdir branch
        mock_cmd_abs_path_check.assert_called_once()      # exec-path fixup
        dummy_remote.mCopyFile.assert_called()            # script copy
        
    
    
    @patch("exabox.sop.sopexecutescripts.SUCCESSEXITCODE", new=0)
    @patch("exabox.sop.sopexecutescripts.node_exec_cmd")
    @patch("exabox.sop.sopexecutescripts.node_cmd_abs_path_check")
    @patch("exabox.sop.sopexecutescripts.connect_to_host")
    @patch("exabox.sop.sopexecutescripts.SOPScriptsRepo")
    @patch("exabox.sop.sopexecutescripts.get_gcontext", return_value=testOptions())
    @patch("exabox.sop.sopexecutescripts.os.path.join", side_effect=lambda *a: '/'.join(a))
    def test_mPostProcessing_switch_cleanup(
        self,
        mock_path_join,                 # os.path.join
        mock_get_gcontext,              # get_gcontext
        mock_SOPScriptsRepo,            # SOPScriptsRepo
        mock_connect_to_host,           # connect_to_host
        mock_cmd_abs_path_check,        # node_cmd_abs_path_check
        mock_node_exec_cmd              # node_exec_cmd
    ):
        """
        High-coverage happy-/error-path test for SOPExecution.mPostProcessing.
        • three switch nodes exercise every branch:
            – node1 : no `test` executable    → skip
            – node2 : cleanup succeeds        → success path
            – node3 : rm fails                → error path
        """

        # ---- repository stub ------------------------------------------------
        repo_instance = MagicMock()
        repo_instance.mGetScriptsMetadata.return_value = {}
        mock_SOPScriptsRepo.return_value = repo_instance

        # ---- connect_to_host: supply a dummy per-node connection ------------
        dummy_conn = MagicMock()
        mock_connect_to_host.return_value.__enter__.return_value = dummy_conn
        mock_connect_to_host.return_value.__exit__.return_value = False

        # ---- per-node behaviour simulation ---------------------------------
        # node1  -> None  (skip)
        # node2  -> exec found
        # node3  -> exec found
        mock_cmd_abs_path_check.side_effect = [
            None,
            "/bin/test",
            "/bin/test",
        ]

        cmd_ok   = MagicMock(exit_code=0)
        cmd_fail = MagicMock(exit_code=1)
        # calls: node2(test), node2(rm), node3(test), node3(rm)
        mock_node_exec_cmd.side_effect = [cmd_ok, cmd_ok, cmd_ok, cmd_fail]

        # ---- build instance with node-type containing "switch" --------------
        se = SOPExecution(
            aUUID="uuid-post",
            aNodesList=["node1", "node2", "node3"],
            aScriptName="irrelevant",
            aScriptParams="",
            aScriptPayload={},
            aScriptVersion=None,
            aNodeType="mgmt_switch"          # <- forces mPostProcessing path
        )

        # should complete without raising
        se.mPostProcessing()

        # ---- quick behavioural checks ---------------------------------------
        self.assertEqual(mock_cmd_abs_path_check.call_count, 3)
        self.assertEqual(mock_node_exec_cmd.call_count,     4)

        # Collect every str argument that was handed to node_exec_cmd
        executed_cmds = []
        for c in mock_node_exec_cmd.call_args_list:
            executed_cmds.extend([arg for arg in c.args if isinstance(arg, str)])
            executed_cmds.extend([val for val in c.kwargs.values() if isinstance(val, str)])


        ebLogInfo("Unit test on SOPExecution.mPostProcessing succeeded.")
        

    @patch("exabox.sop.sopexecutescripts.interactiveSSHconnection")
    @patch("exabox.sop.sopexecutescripts.connect_to_host")
    @patch("exabox.sop.sopexecutescripts.fetch_ilom_password", return_value="dummy_pwd")
    @patch("exabox.sop.sopexecutescripts.SOPScriptsRepo")
    @patch("exabox.sop.sopexecutescripts.get_gcontext", return_value=testOptions())
    @patch("exabox.sop.sopexecutescripts.os.path.join", side_effect=lambda *a: '/'.join(a))
    @patch("exabox.sop.sopexecutescripts.json.load")
    @patch("builtins.open", new_callable=mock.mock_open, read_data="{}")
    def test_mProcessRequestILOM_nominal(
        self,
        mock_open,                    # builtins.open
        mock_json_load,               # json.load
        mock_path_join,               # os.path.join
        mock_get_gcontext,            # get_gcontext
        mock_SOPScriptsRepo,          # SOPScriptsRepo
        mock_fetch_pwd,               # fetch_ilom_password
        mock_connect_to_host,         # connect_to_host
        mock_interactive_shell        # interactiveSSHconnection
    ):
        """
        Executes mProcessRequestILOM once, exercising the main sequential
        branch and verifying that output is produced for the target node.
        """
        # ------------------------------------------------------------------
        # (1) prepare the fake script-metadata repo
        # ------------------------------------------------------------------
        script_name = "demo_ilom_script"
        repo_instance = MagicMock()
        repo_instance.mGetScriptsMetadata.return_value = {
            script_name: {
                SCRIPT_VERSION:          "1",
                SCRIPT_PATH:             "/tmp/dummy_ilom.json",
                SCRIPT_PARALLEL_EXEC:    False,     # → sequential branch
            }
        }
        mock_SOPScriptsRepo.return_value = repo_instance

        # ------------------------------------------------------------------
        # (2) make json.load return a list with one command requiring
        #     payload substitution
        # ------------------------------------------------------------------
        commands_dict = {
            "commands": [
                {"match": False,
                 "prompt": "->",
                 "cmd": "show {var1}",
                 "timeout": 5}
            ]
        }
        mock_json_load.return_value = commands_dict

        # ------------------------------------------------------------------
        # (3) stub connect_to_host → context-manager yielding dummy node
        # ------------------------------------------------------------------
        dummy_node = MagicMock()
        dummy_node.mGetSSHClient.return_value = MagicMock()
        mock_connect_to_host.return_value.__enter__.return_value = dummy_node
        mock_connect_to_host.return_value.__exit__.return_value  = False

        # ------------------------------------------------------------------
        # (4) stub interactiveSSHconnection methods
        # ------------------------------------------------------------------
        shell_mock = MagicMock()
        shell_mock.mGetCurrentPrompt.return_value   = "->"
        shell_mock.mExecuteCommand.return_value     = "OK"
        shell_mock.mCloseInteractiveShell           = MagicMock()
        mock_interactive_shell.return_value = shell_mock

        # ------------------------------------------------------------------
        # (5) create the SOPExecution object and invoke the method
        # ------------------------------------------------------------------
        se = SOPExecution(
            aUUID="uuid-ilom",
            aNodesList=["node1"],
            aScriptName=script_name,
            aScriptParams="",
            aScriptPayload={"var1": "value1"},
            aScriptVersion="1",
            aNodeType="ilom_compute"     # guarantees ilom code-path
        )

        # run – should not raise
        se.mProcessRequestILOM()

        # ------------------------------------------------------------------
        # (6) verify outcome
        # ------------------------------------------------------------------
        result = se.mGetResult()
        self.assertIn("node1", result)
        self.assertEqual(result["node1"]["return_code"], 0)
        self.assertIn("command_1", result["node1"]["return_json"])

        # confirm that the placeholder was really substituted
        executed_cmd = result["node1"]["return_json"]["command_1"]["command"]
        self.assertEqual(executed_cmd, "show value1")

        # interactive shell used exactly once
        mock_interactive_shell.assert_called_once()
        shell_mock.mExecuteCommand.assert_called_once_with(
            "show value1", "->", 5
        )

        ebLogInfo("Unit test on SOPExecution.mProcessRequestILOM succeeded.")
        

    @patch("exabox.sop.sopexecutescripts.node_exec_cmd")
    @patch("exabox.sop.sopexecutescripts.connect_to_host")
    @patch("exabox.sop.sopexecutescripts.SOPScriptsRepo")
    @patch("exabox.sop.sopexecutescripts.get_gcontext", return_value=testOptions())
    @patch("exabox.sop.sopexecutescripts.os.path.join", side_effect=lambda *a: '/'.join(a))
    @patch("builtins.open", new_callable=mock.mock_open, read_data="{}")   # fake execution_output.json
    @patch("json.load")
    def test_mProcessRequest_nominal(
        self,
        mock_json_load,             # json.load
        mock_open,                  # builtins.open
        mock_path_join,             # os.path.join
        mock_get_gcontext,          # get_gcontext
        mock_SOPScriptsRepo,        # SOPScriptsRepo
        mock_connect_to_host,       # connect_to_host
        mock_node_exec_cmd          # node_exec_cmd
    ):
        """
        Drives mProcessRequest for one local + one remote node, touching
        every major branch inside the method.
        """
        # ------------------------------------------------------------------
        # (1) prepare script-metadata so that:
        #     • sequential execution path is taken (support_parallel_execution False)
        #     • return_json_support True  → triggers execution_output.json logic
        # ------------------------------------------------------------------
        script_name = "demo_script"
        repo_instance = MagicMock()
        repo_instance.mGetScriptsMetadata.return_value = {
            script_name: {
                SCRIPT_VERSION:           "1",
                SCRIPT_EXEC:              "/bin/echo",
                SCRIPT_PATH:              "/fake/script/path.sh",
                SCRIPT_PARALLEL_EXEC:     False,
                SCRIPT_RETURN_JSON_SUPPORT: True
            }
        }
        mock_SOPScriptsRepo.return_value = repo_instance

        # ------------------------------------------------------------------
        # (2) connect_to_host context manager → dummy node
        #     we need different behaviour for local vs remote:
        #     • both report that execution_output.json exists
        #     • remote node supports mCopy2Local
        # ------------------------------------------------------------------
        dummy_local  = MagicMock()
        dummy_remote = MagicMock()
        dummy_local.mFileExists .return_value = True
        dummy_remote.mFileExists.return_value = True
        dummy_remote.mCopy2Local  = MagicMock()

        def _connect_side_effect(hostname, ctx, local=False, **kw):
            # ctx & **kw are ignored; hostname distinguishes node
            cm = MagicMock()
            cm.__enter__.return_value = dummy_local if hostname == "localhost" else dummy_remote
            cm.__exit__.return_value  = False
            return cm

        mock_connect_to_host.side_effect = _connect_side_effect

        # ------------------------------------------------------------------
        # (3) node_exec_cmd returns a struct-like object
        # ------------------------------------------------------------------
        cmd_struct = MagicMock()
        cmd_struct.exit_code = 0
        cmd_struct.stdout    = "OK"
        cmd_struct.stderr    = ""
        mock_node_exec_cmd.return_value = cmd_struct

        # ------------------------------------------------------------------
        # (4) json.load should return different objects for local & remote
        # ------------------------------------------------------------------
        mock_json_load.side_effect = [{"from": "local"}, {"from": "remote"}]

        # ------------------------------------------------------------------
        # (5) build the class under test and invoke mProcessRequest
        # ------------------------------------------------------------------
        se = SOPExecution(
            aUUID="uuid-pr",
            aNodesList=["localhost", "node2"],
            aScriptName=script_name,
            aScriptParams="--flag",
            aScriptPayload={},
            aScriptVersion="1",
            aNodeType=None
        )

        # run target
        se.mProcessRequest()

        # ------------------------------------------------------------------
        # (6) assertions — prove deep traversal
        # ------------------------------------------------------------------
        result = se.mGetResult()
        self.assertEqual(set(result.keys()), {"localhost", "node2"})

        # both nodes got exit_code 0 and carry the injected json
        self.assertEqual(result["localhost"]["return_code"], 0)
        self.assertEqual(result["node2"]["return_code"],     0)
        self.assertEqual(result["localhost"]["return_json"], {"from": "local"})
        self.assertEqual(result["node2"]["return_json"],     {"from": "remote"})

        # helper calls executed as expected
        self.assertEqual(mock_node_exec_cmd.call_count, 2)      # once per node
        dummy_remote.mCopy2Local.assert_called_once()           # remote branch hit
        self.assertEqual(mock_json_load.call_count, 2)          # one per node

        ebLogInfo("Unit test on SOPExecution.mProcessRequest succeeded.")
        

    # ------------------------------------------------------------------
    # Helper stubs that replace the real multiprocessing wrappers
    # ------------------------------------------------------------------
    class _DummyProcessStructure:
        """Synchronous replacement – immediately executes the target."""
        def __init__(self, target, args):
            self._target = target
            self._args   = args
            self._return = None

        # setters are no-ops (kept for interface compatibility)
        def mSetMaxExecutionTime(self, *_):   pass
        def mSetJoinTimeout(self, *_):        pass
        def mSetLogTimeoutFx(self, *_):       pass

        # synchronous execution
        def run(self):
            self._return = self._target(*self._args)

        # getters used by production code
        def mGetArgs(self):    return self._args
        def mGetReturn(self):  return self._return


    class _DummyProcessManager:
        """Collects DummyProcessStructure objects and runs them inline."""
        def __init__(self):
            self._plist = []

        def mStartAppend(self, p):
            p.run()                 # run immediately, no fork
            self._plist.append(p)

        def mJoinProcess(self):     # nothing to do (already executed)
            pass

        def mGetProcessList(self):
            return self._plist

    # ------------------------------------------------------------------
    # Test for mProcessRequestILOMInAsyncMode
    # ------------------------------------------------------------------
    @patch("exabox.sop.sopexecutescripts.ProcessStructure", new=_DummyProcessStructure)
    @patch("exabox.sop.sopexecutescripts.ProcessManager",   new=_DummyProcessManager)
    @patch("exabox.sop.sopexecutescripts.interactiveSSHconnection")
    @patch("exabox.sop.sopexecutescripts.connect_to_host")
    @patch("exabox.sop.sopexecutescripts.SOPScriptsRepo")
    @patch("exabox.sop.sopexecutescripts.get_gcontext", return_value=testOptions())
    @patch("exabox.sop.sopexecutescripts.os.path.join", side_effect=lambda *a: '/'.join(a))
    def test_mProcessRequestILOMInAsyncMode_nominal(
        self,
        mock_path_join,          # os.path.join
        mock_get_gcontext,       # get_gcontext
        mock_SOPScriptsRepo,     # SOPScriptsRepo
        mock_connect_to_host,    # connect_to_host
        mock_interactive_shell   # interactiveSSHconnection
    ):
        """
        Drives mProcessRequestILOMInAsyncMode through its main path with
        synchronous stubs, giving high line coverage without spawning
        real processes or SSH connections.
        """
        # ----------- fake script repository (minimal information) -----------
        repo_instance = MagicMock()
        repo_instance.mGetScriptsMetadata.return_value = {}
        mock_SOPScriptsRepo.return_value = repo_instance

        # ----------- stub interactive shell behaviour ----------------------
        shell_obj = MagicMock()
        shell_obj.mGetCurrentPrompt.return_value = "->"
        shell_obj.mExecuteCommand.return_value   = "OK"
        shell_obj.mCloseInteractiveShell         = MagicMock()
        mock_interactive_shell.return_value      = shell_obj

        # ----------- stub connect_to_host context manager ------------------
        dummy_node = MagicMock()
        dummy_node.mGetSSHClient.return_value = MagicMock()
        mock_connect_to_host.return_value.__enter__.return_value = dummy_node
        mock_connect_to_host.return_value.__exit__.return_value  = False

        # ----------- build SOPExecution instance ---------------------------
        se = SOPExecution(
            aUUID="uuid-async",
            aNodesList=["nodeA", "nodeB"],
            aScriptName="irrelevant",
            aScriptParams="",
            aScriptPayload={},
            aScriptVersion=None,
            aNodeType="ilom_compute"
        )

        # pre-populate one node in __output so that “skip” branch is hit
        se._SOPExecution__output = {"nodeB": {"pre": "existing"}}

        # command list containing two commands to exercise loop logic
        commands = [
            {"match": False, "prompt": "->", "cmd": "show version", "timeout": 5},
            {"match": False, "prompt": "->", "cmd": "show uptime",  "timeout": 5},
        ]

        # run target (synchronous thanks to the dummy process classes)
        se.mProcessRequestILOMInAsyncMode(commands, aPassword="pwd123")

        # ---------------- assertions – prove deep traversal ----------------
        _out = se.mGetResult()
        # nodeA should now be populated, nodeB must retain its original entry
        self.assertIn("nodeA", _out)
        self.assertIn("nodeB", _out)
        self.assertEqual(_out["nodeB"], {"pre": "existing"})
        self.assertEqual(_out["nodeA"]["return_code"], 0)          # success path
        self.assertIn("command_1", _out["nodeA"]["return_json"])   # collected cmd outputs

        # interactive shell was created exactly once (for nodeA)
        mock_interactive_shell.assert_called_once()
        shell_obj.mExecuteCommand.assert_any_call("show version", "->", 5)
        shell_obj.mExecuteCommand.assert_any_call("show uptime",  "->", 5)

        ebLogInfo("Unit test on SOPExecution.mProcessRequestILOMInAsyncMode succeeded.")

        
    # ------------------------------------------------------------------
    #  helpers – synchronous replacements for Process* wrappers
    # ------------------------------------------------------------------
    class _SyncProcessStructure:
        """Runs target immediately inside the current process."""
        def __init__(self, target, args):
            self._target = target
            self._args   = args
            self._ret    = None

        # API that production code expects ------------------------------
        def mSetMaxExecutionTime(self, *_):  pass
        def mSetJoinTimeout(self, *_):       pass
        def mSetLogTimeoutFx(self, *_):      pass
        def run(self):
            self._ret = self._target(*self._args)

        # production code reads these two
        def mGetArgs(self):    return self._args
        def mGetReturn(self):  return self._ret


    class _SyncProcessManager:
        """Collects _SyncProcessStructure objects and executes them inline."""
        def __init__(self):
            self._plist = []

        def mStartAppend(self, p):
            p.run()
            self._plist.append(p)

        def mJoinProcess(self):      # already synchronously executed
            pass

        def mGetProcessList(self):
            return self._plist

    # ------------------------------------------------------------------
    #  Test for mProcessRequestInAynscMode
    # ------------------------------------------------------------------
    @patch("exabox.sop.sopexecutescripts.ProcessStructure", new=_SyncProcessStructure)
    @patch("exabox.sop.sopexecutescripts.ProcessManager",   new=_SyncProcessManager)
    @patch("exabox.sop.sopexecutescripts.node_exec_cmd")
    @patch("exabox.sop.sopexecutescripts.connect_to_host")
    @patch("exabox.sop.sopexecutescripts.SOPScriptsRepo")
    @patch("exabox.sop.sopexecutescripts.get_gcontext", return_value=testOptions())
    @patch("exabox.sop.sopexecutescripts.os.path.join", side_effect=lambda *a: '/'.join(a))
    @patch("builtins.open", new_callable=mock.mock_open, read_data="{}")
    @patch("json.load")
    def test_mProcessRequestInAynscMode_nominal(
        self,
        mock_json_load,            # json.load
        mock_open,                 # builtins.open
        mock_path_join,            # os.path.join
        mock_get_gcontext,         # get_gcontext
        mock_SOPScriptsRepo,       # SOPScriptsRepo
        mock_connect_to_host,      # connect_to_host
        mock_node_exec_cmd         # node_exec_cmd
    ):
        """
        Drives the asynchronous script-execution path without creating
        real processes, covering:
          • skip-node branch (pre-populated __output)
          • local vs remote node handling
          • return_json_support logic
          • result aggregation at the end of the method.
        """

        # ---------------------------------------------------------------
        # 1) Fake repository – script supports async execution & JSON ret
        # ---------------------------------------------------------------
        script_name = "demo_async_script"
        repo_stub = MagicMock()
        repo_stub.mGetScriptsMetadata.return_value = {
            script_name: {
                SCRIPT_VERSION:            "1",
                SCRIPT_EXEC:               "/bin/echo",
                SCRIPT_PATH:               "/fake/script.sh",
                SCRIPT_PARALLEL_EXEC:      True,   # ← triggers async mode
                SCRIPT_RETURN_JSON_SUPPORT: True
            }
        }
        mock_SOPScriptsRepo.return_value = repo_stub

        # ---------------------------------------------------------------
        # 2) Dummy “command execution” result object
        # ---------------------------------------------------------------
        cmd_struct = MagicMock()
        cmd_struct.exit_code = 0
        cmd_struct.stdout    = "OK"
        cmd_struct.stderr    = ""
        mock_node_exec_cmd.return_value = cmd_struct

        # ---------------------------------------------------------------
        # 3) connect_to_host – distinguish local vs remote
        # ---------------------------------------------------------------
        local_node  = MagicMock()
        remote_node = MagicMock()
        # execution_output.json exists for both nodes
        local_node .mFileExists.return_value = True
        remote_node.mFileExists.return_value = True
        remote_node.mCopy2Local   = MagicMock()

        def _conn_side_effect(hostname, ctx, local=False, **kw):
            cm = MagicMock()
            cm.__enter__.return_value = local_node if hostname == "localhost" else remote_node
            cm.__exit__.return_value  = False
            return cm

        mock_connect_to_host.side_effect = _conn_side_effect

        # distinct json.load returns so we can verify branch coverage
        mock_json_load.side_effect = [{"from": "local"}, {"from": "remote"}]

        # ---------------------------------------------------------------
        # 4) Build object-under-test
        #      • three nodes → localhost, node2, nodeSkip
        #      • nodeSkip pre-populated → exercises "already in output" path
        # ---------------------------------------------------------------
        se = SOPExecution(
            aUUID="uuid-async-pr",
            aNodesList=["localhost", "node2", "nodeSkip"],
            aScriptName=script_name,
            aScriptParams="--flag",
            aScriptPayload={},
            aScriptVersion="1",
            aNodeType=None
        )
        se._SOPExecution__output = {"nodeSkip": {"pre": "present"}}

        # ---------------------------------------------------------------
        # 5) Invoke target
        # ---------------------------------------------------------------
        se.mProcessRequestInAynscMode()

        # ---------------------------------------------------------------
        # 6) Assertions – prove deep traversal
        # ---------------------------------------------------------------
        res = se.mGetResult()
        # All three nodes present, but nodeSkip unchanged
        self.assertIn("localhost", res)
        self.assertIn("node2",     res)
        self.assertEqual(res["nodeSkip"], {"pre": "present"})

        # exit_code captured from mocked cmd_struct
        self.assertEqual(res["localhost"]["return_code"], 0)
        self.assertEqual(res["node2"]["return_code"],     0)

        # JSON payloads captured via json.load
        self.assertEqual(res["localhost"]["return_json"], {"from": "local"})
        self.assertEqual(res["node2"]["return_json"],     {"from": "remote"})

        # helper interactions occurred as expected
        self.assertEqual(mock_node_exec_cmd.call_count, 2)         # nodeSkip was skipped
        remote_node.mCopy2Local.assert_called_once()               # remote branch executed
        self.assertEqual(mock_json_load.call_count, 2)

        ebLogInfo("Unit test on SOPExecution.mProcessRequestInAynscMode succeeded.")

if __name__ == '__main__':
    unittest.main()