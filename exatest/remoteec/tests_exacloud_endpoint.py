#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/remoteec/tests_exacloud_endpoint.py /main/1 2023/12/01 00:48:35 hgaldame Exp $
#
# tests_exacloud_endpoint.py
#
# Copyright (c) 2023, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_exacloud_endpoint.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    shapatna    04/16/26 - Bug 39111671 Enhance UT Coverage for exabox/managment directory
#    hgaldame    11/29/23 - 36055367 - oci/exacc: unrecognized arguments error
#                           executing exacloud commands through remote manager
#    hgaldame    11/29/23 - Creation
#
import unittest
import uuid
import os

from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

from exabox.managment.src.ExacloudCmdEndpoint import ExacloudCmdEndpoint
from unittest.mock import patch, Mock, MagicMock, mock_open

class ebTestExacloudCmdEndpoint(ebTestClucontrol):


    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateRemoteEC=True)
        os.makedirs("log/threads", exist_ok=True)

    def test_000_exacloud_split_cmd(self):

        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        _body = {
            "args": "--help --debug --verbose"
        }

        _response = {}
        _endpoint = ExacloudCmdEndpoint(None, _body, _response, _shared)
        with patch.object(_endpoint, "mCreateBashProcess") as _spy_method:
            exacloud_bin_path = os.path.join(self.mGetUtil().mGetExacloudPath(),"bin","exacloud")
            _endpoint.mPost()
            _spy_method.assert_called_once_with([[exacloud_bin_path,"--help","--debug","--verbose"]],aName="execute [--help --debug --verbose]")

    def _mMakeEndpoint(self, aBody=None, aResponse=None, aShared=None):
        if aBody is None:
            aBody = {}
        if aResponse is None:
            aResponse = {}
        if aShared is None:
            aShared = self.mGetUtil().mGetRemoteEC().mGetShared()
        return ExacloudCmdEndpoint(None, aBody, aResponse, aShared)

    def _mPatchConfig(self, aEndpoint, aPath="/tmp/exacloud/exabox/managment/src/ExacloudCmdEndpoint.py", aRepoRoot="/repo"):
        _config = Mock()
        _config.mGetPath.return_value = aPath
        _config.mGetExacloudConfigValue.return_value = aRepoRoot
        return patch.object(aEndpoint, "mGetConfig", return_value=_config)

    # Auto-generated test for mPost
    def test_001_exacloud_mpost_ignores_commands_after_semicolon(self):
        _response = {}
        _endpoint = self._mMakeEndpoint({
            "args": "--version; rm -rf /tmp/ignored"
        }, _response)
        with self._mPatchConfig(_endpoint), \
             patch.object(_endpoint, "mCreateBashProcess", return_value="started") as _spy_method:
            _endpoint.mPost()
        self.assertEqual(_response["text"], "started")
        _spy_method.assert_called_once_with(
            [["/tmp/exacloud/bin/exacloud", "--version"]],
            aName="execute [--version]"
        )

    # Auto-generated test for mPatch
    def test_002_exacloud_mpatch_reports_existing_upgrade_operation(self):
        _response = {}
        _endpoint = self._mMakeEndpoint({"mode": "only_upgrade"}, _response)
        with self._mPatchConfig(_endpoint), \
             patch("exabox.managment.src.ExacloudCmdEndpoint.os.path.exists", return_value=True):
            _endpoint.mPatch()
        self.assertEqual(_response["status"], 500)
        self.assertEqual(_response["error"], "Error, already an upgrade operation begin executed")
        self.assertEqual(_response["text"], "Error, already an upgrade operation begin executed")

    # Auto-generated test for mPatch
    def test_003_exacloud_mpatch_dispatches_clean_even_when_upgrade_exists(self):
        _endpoint = self._mMakeEndpoint({"mode": "clean"}, {})
        with self._mPatchConfig(_endpoint), \
             patch("exabox.managment.src.ExacloudCmdEndpoint.os.path.exists", return_value=True), \
             patch.object(_endpoint, "mClean") as _clean_method:
            _endpoint.mPatch()
        _clean_method.assert_called_once_with("/tmp/exacloud/", "/tmp/upgrade", "/tmp")

    # Auto-generated test for mPatch
    def test_004_exacloud_mpatch_dispatches_modes(self):
        for _mode, _method_name in [("only_upgrade", "mOnlyUpgrade"), ("list_bk", "mListBk"), ("rollback", "mRollback")]:
            _endpoint = self._mMakeEndpoint({"mode": _mode}, {})
            with self.subTest(mode=_mode):
                with self._mPatchConfig(_endpoint), \
                     patch("exabox.managment.src.ExacloudCmdEndpoint.os.path.exists", return_value=False), \
                     patch.object(_endpoint, _method_name) as _method:
                    _endpoint.mPatch()
                _method.assert_called_once_with("/tmp/exacloud/", "/tmp/upgrade", "/tmp")

    # Auto-generated test for mGetExacloudBackups
    def test_005_exacloud_mgetexacloudbackups_filters_backup_names(self):
        _endpoint = self._mMakeEndpoint()
        with self._mPatchConfig(_endpoint), \
             patch("exabox.managment.src.ExacloudCmdEndpoint.os.listdir", return_value=["first.bak", "second.txt", "third.bak"]):
            self.assertEqual(_endpoint.mGetExacloudBackups(), ["first.bak", "third.bak"])

    # Auto-generated test for mHasOngoingOperations
    def test_006_exacloud_mhasongoingoperations_handles_none_empty_and_pending(self):
        _db = Mock()
        _db.mFilterRequests.side_effect = [None, [], [{"status": "Pending"}]]
        _endpoint = self._mMakeEndpoint()
        with patch.object(_endpoint, "mGetShared", return_value={"db": _db}):
            self.assertTrue(_endpoint.mHasOngoingOperations())
            self.assertFalse(_endpoint.mHasOngoingOperations())
            self.assertTrue(_endpoint.mHasOngoingOperations())
        self.assertEqual(_db.mFilterRequests.call_count, 3)

    # Auto-generated test for mFindLite
    def test_007_exacloud_mfindlite_returns_first_matching_bundle(self):
        _endpoint = self._mMakeEndpoint()
        _walk_output = [
            ("bundle/first", [], ["README.txt"]),
            ("bundle/second", [], ["exacloud_lite_1.tgz", "another.tgz"])
        ]
        with patch("exabox.managment.src.ExacloudCmdEndpoint.os.walk", return_value=_walk_output):
            self.assertEqual(_endpoint.mFindLite("bundle"), "bundle/second/exacloud_lite_1.tgz")

    # Auto-generated test for mOnlyUpgrade
    def test_008_exacloud_monlyupgrade_rejects_ongoing_operations(self):
        _response = {}
        _endpoint = self._mMakeEndpoint({}, _response)
        with patch.object(_endpoint, "mHasOngoingOperations", return_value=True):
            _endpoint.mOnlyUpgrade("/tmp/exacloud/", "/tmp/upgrade", "/tmp")
        self.assertEqual(_response["status"], 500)
        self.assertEqual(_response["error"], "There are ongoing operations on exacloud")
        self.assertEqual(_response["text"], "There are ongoing operations on exacloud")

    # Auto-generated test for mOnlyUpgrade
    def test_009_exacloud_monlyupgrade_errors_when_repository_file_is_missing(self):
        _response = {}
        _endpoint = self._mMakeEndpoint({}, _response)
        with self._mPatchConfig(_endpoint, aRepoRoot="/repo") as _config_patch, \
             patch.object(_endpoint, "mHasOngoingOperations", return_value=False), \
             patch("exabox.managment.src.ExacloudCmdEndpoint.os.path.exists", return_value=False) as _exists:
            _endpoint.mOnlyUpgrade("/tmp/exacloud/", "/tmp/upgrade", "/tmp")
        self.assertEqual(_response["status"], 500)
        self.assertEqual(_response["error"], "Error, exacloud_lite location not found")
        self.assertEqual(_response["text"], "Error, exacloud_lite location not found")
        self.assertEqual(_exists.call_args_list[0][0][0], "/repo/activeVersion.json")

    # Auto-generated test for mOnlyUpgrade
    def test_010_exacloud_monlyupgrade_reports_json_load_errors(self):
        _response = {}
        _endpoint = self._mMakeEndpoint({}, _response)
        with self._mPatchConfig(_endpoint, aRepoRoot="/repo"), \
             patch.object(_endpoint, "mHasOngoingOperations", return_value=False), \
             patch("exabox.managment.src.ExacloudCmdEndpoint.os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data="{}")), \
             patch("exabox.managment.src.ExacloudCmdEndpoint.json.load", side_effect=ValueError("broken json")) as _json_load:
            _endpoint.mOnlyUpgrade("/tmp/exacloud/", "/tmp/upgrade", "/tmp")
        self.assertEqual(_response["status"], 500)
        self.assertEqual(_response["error"], "Error, exacloud_lite location not found")
        self.assertEqual(_response["text"], "Error, exacloud_lite location not found")
        _json_load.assert_called_once_with(unittest.mock.ANY)

    # Auto-generated test for mOnlyUpgrade
    def test_011_exacloud_monlyupgrade_errors_when_lite_is_not_found(self):
        _response = {}
        _endpoint = self._mMakeEndpoint({}, _response)
        with self._mPatchConfig(_endpoint, aRepoRoot="/repo"), \
             patch.object(_endpoint, "mHasOngoingOperations", return_value=False), \
             patch("exabox.managment.src.ExacloudCmdEndpoint.os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data="{}")), \
             patch("exabox.managment.src.ExacloudCmdEndpoint.json.load", return_value={
                 "active": {"cpssw": {"download_location": "/repo/lite"}}
             }), \
             patch.object(_endpoint, "mFindLite", return_value=""):
            _endpoint.mOnlyUpgrade("/tmp/exacloud/", "/tmp/upgrade", "/tmp")
        self.assertEqual(_response["status"], 500)
        self.assertEqual(_response["error"], "Error, exacloud_lite location not found")
        self.assertEqual(_response["text"], "Error, exacloud_lite location not found")

    # Auto-generated test for mOnlyUpgrade
    def test_012_exacloud_monlyupgrade_builds_command_list_with_explicit_lite(self):
        _response = {}
        _endpoint = self._mMakeEndpoint({"lite_location": "/repo/exacloud_lite.tgz"}, _response)
        with patch.object(_endpoint, "mHasOngoingOperations", return_value=False), \
             patch("exabox.managment.src.ExacloudCmdEndpoint.uuid.uuid1", return_value="fixed-upgrade-id"), \
             patch("exabox.managment.src.ExacloudCmdEndpoint.os.makedirs") as _makedirs, \
             patch("exabox.managment.src.ExacloudCmdEndpoint.Path.touch") as _touch, \
             patch.object(_endpoint, "mCreateBashProcess", return_value="upgrade-process") as _create_process:
            _endpoint.mOnlyUpgrade("/tmp/exacloud/", "/tmp/upgrade", "/tmp")
        self.assertEqual(_response["text"], "upgrade-process")
        _makedirs.assert_called_once_with("/tmp/upgrade")
        _touch.assert_called_once_with()
        _create_process.assert_called_once_with(
            [
                ["cp", "/tmp/exacloud//scripts/xpatch.py", "/tmp/upgrade"],
                ["ln", "-sf", "/repo/exacloud_lite.tgz", "/tmp/upgrade/exacloud_lite.tgz"],
                ["/tmp/exacloud//bin/python", "/tmp/upgrade/xpatch.py", "upgrade", "-ni", "-e", "/tmp"],
                ["echo", "Running Clean up"],
                ["cp", "/tmp/upgrade/mgnt-fixed-upgrade-id.log", "/tmp/exacloud///log/threads/"],
                ["rm", "-rf", "/tmp/upgrade"]
            ],
            aId="fixed-upgrade-id",
            aLogFile="/tmp/upgrade/mgnt-fixed-upgrade-id.log",
            aName="upgrade",
            aOnFinish=_endpoint.mFinish
        )

    # Auto-generated test for mOnlyUpgrade
    def test_013_exacloud_monlyupgrade_builds_command_list_from_repository_metadata(self):
        _response = {}
        _endpoint = self._mMakeEndpoint({}, _response)
        with self._mPatchConfig(_endpoint, aRepoRoot="/repo"), \
             patch.object(_endpoint, "mHasOngoingOperations", return_value=False), \
             patch("exabox.managment.src.ExacloudCmdEndpoint.os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data="{}")), \
             patch("exabox.managment.src.ExacloudCmdEndpoint.json.load", return_value={
                 "active": {"cpssw": {"download_location": "/repo/bundles"}}
             }), \
             patch.object(_endpoint, "mFindLite", return_value="/repo/bundles/exacloud_lite_v1.tgz") as _find_lite, \
             patch("exabox.managment.src.ExacloudCmdEndpoint.uuid.uuid1", return_value="repo-upgrade-id"), \
             patch("exabox.managment.src.ExacloudCmdEndpoint.os.makedirs"), \
             patch("exabox.managment.src.ExacloudCmdEndpoint.Path.touch"), \
             patch.object(_endpoint, "mCreateBashProcess", return_value="upgrade-process"):
            _endpoint.mOnlyUpgrade("/tmp/exacloud/", "/tmp/upgrade", "/tmp")
        _find_lite.assert_called_once_with("/repo/bundles")
        self.assertEqual(_response["text"], "upgrade-process")

    # Auto-generated test for mFinish
    def test_014_exacloud_mfinish_changes_directory_to_exacloud_root(self):
        _endpoint = self._mMakeEndpoint()
        with self._mPatchConfig(_endpoint), \
             patch("exabox.managment.src.ExacloudCmdEndpoint.os.chdir") as _chdir:
            _endpoint.mFinish()
        _chdir.assert_called_once_with("/tmp/exacloud/")

    # Auto-generated test for mListBk
    def test_015_exacloud_mlistbk_sets_backup_listing_in_response(self):
        _response = {}
        _endpoint = self._mMakeEndpoint({}, _response)
        with patch("exabox.managment.src.ExacloudCmdEndpoint.os.listdir", return_value=["snap.bak"]), \
             patch.object(_endpoint, "mGetExacloudBackups", return_value=["snap.bak"]) as _get_backups:
            _endpoint.mListBk("/tmp/exacloud/", "/tmp/upgrade", "/tmp")
        _get_backups.assert_called_once_with()
        self.assertEqual(_response["text"], ["snap.bak"])

    # Auto-generated test for mClean
    def test_016_exacloud_mclean_builds_cleanup_commands(self):
        _response = {}
        _endpoint = self._mMakeEndpoint({}, _response)
        with patch("exabox.managment.src.ExacloudCmdEndpoint.os.listdir", return_value=["one.bak", "notes.txt", "two.bak"]), \
             patch.object(_endpoint, "mCreateBashProcess", return_value="clean-process") as _create_process:
            _endpoint.mClean("/tmp/exacloud/", "/tmp/upgrade", "/tmp")
        self.assertEqual(_response["text"], "clean-process")
        _create_process.assert_called_once_with(
            [
                ["echo", "Running cleanup of backup"],
                ["rm", "-rf", "/tmp/one.bak"],
                ["rm", "-rf", "/tmp/two.bak"],
                ["rm", "-rf", "/tmp/upgrade"],
                ["echo", "Cleanup done"]
            ],
            aName="upgrade [clean]"
        )

    # Auto-generated test for mRollback
    def test_017_exacloud_mrollback_requires_backup_name(self):
        _response = {}
        _endpoint = self._mMakeEndpoint({}, _response)
        _endpoint.mRollback("/tmp/exacloud/", "/tmp/upgrade", "/tmp")
        self.assertEqual(_response["status"], 500)
        self.assertEqual(_response["error"], "Error, missing 'backup_name' param")
        self.assertEqual(_response["text"], "Error, missing 'backup_name' param")

    # Auto-generated test for mRollback
    def test_018_exacloud_mrollback_rejects_ongoing_operations(self):
        _response = {}
        _endpoint = self._mMakeEndpoint({"backup_name": "snap.bak"}, _response)
        with patch.object(_endpoint, "mHasOngoingOperations", return_value=True):
            _endpoint.mRollback("/tmp/exacloud/", "/tmp/upgrade", "/tmp")
        self.assertEqual(_response["status"], 500)
        self.assertEqual(_response["error"], "There are ongoing operations on exacloud")
        self.assertEqual(_response["text"], "There are ongoing operations on exacloud")

    # Auto-generated test for mRollback
    def test_019_exacloud_mrollback_validates_requested_backup(self):
        _response = {}
        _endpoint = self._mMakeEndpoint({"backup_name": "missing.bak"}, _response)
        with patch.object(_endpoint, "mHasOngoingOperations", return_value=False), \
             patch.object(_endpoint, "mGetExacloudBackups", return_value=["snap.bak"]):
            _endpoint.mRollback("/tmp/exacloud/", "/tmp/upgrade", "/tmp")
        self.assertEqual(_response["status"], 500)
        self.assertEqual(_response["error"], "Error, backup: 'missing.bak' does not exists")
        self.assertEqual(_response["text"], "Error, backup: 'missing.bak' does not exists")

    # Auto-generated test for mRollback
    def test_020_exacloud_mrollback_builds_rollback_commands(self):
        _response = {}
        _endpoint = self._mMakeEndpoint({"backup_name": "snap.bak"}, _response)
        with patch.object(_endpoint, "mHasOngoingOperations", return_value=False), \
             patch.object(_endpoint, "mGetExacloudBackups", return_value=["snap.bak"]), \
             patch("exabox.managment.src.ExacloudCmdEndpoint.uuid.uuid1", return_value="fixed-rollback-id"), \
             patch.object(_endpoint, "mCreateBashProcess", return_value="rollback-process") as _create_process:
            _endpoint.mRollback("/tmp/exacloud/", "/tmp/upgrade", "/tmp")
        self.assertEqual(_response["text"], "rollback-process")
        _create_process.assert_called_once_with(
            [
                ["echo", "Stopping Exacloud..."],
                ["/tmp/exacloud//bin/exacloud", "--agent stop"],
                ["echo", "Restore backup exacloud..."],
                ["rm", "-rf", "/tmp/exacloud"],
                ["mv", "-v", "/tmp/snap.bak", "/tmp/exacloud"],
                ["cd"],
                ["cd", "-"],
                ["echo", "Start Exacloud..."],
                ["/tmp/exacloud//bin/exacloud", "--agent start -da"],
                ["echo", "Rollback Done"],
                ["mv", "/tmp/mgnt-fixed-rollback-id.log", "/tmp/exacloud///log/threads/"]
            ],
            aId="fixed-rollback-id",
            aLogFile="/tmp/mgnt-fixed-rollback-id.log",
            aName="upgrade [rollback]",
            aOnFinish=_endpoint.mFinish
        )

    # Auto-generated test for mPost
    def test_021_exacloud_mpost_handles_empty_args(self):
        _response = {}
        _endpoint = self._mMakeEndpoint({
            "args": ""
        }, _response)
        with self._mPatchConfig(_endpoint), \
             patch.object(_endpoint, "mCreateBashProcess", return_value="started") as _spy_method:
            _endpoint.mPost()
        self.assertEqual(_response["text"], "started")
        _spy_method.assert_called_once_with(
            [["/tmp/exacloud/bin/exacloud"]],
            aName="execute []"
        )

    # Auto-generated test for mFindLite
    def test_022_exacloud_mfindlite_returns_empty_string_when_bundle_is_missing(self):
        _endpoint = self._mMakeEndpoint()
        _walk_output = [
            ("bundle/first", [], ["README.txt"]),
            ("bundle/second", [], ["notes.log"])
        ]
        with patch("exabox.managment.src.ExacloudCmdEndpoint.os.walk", return_value=_walk_output):
            self.assertEqual(_endpoint.mFindLite("bundle"), "")

    # Auto-generated test for mPatch
    def test_023_exacloud_mpatch_ignores_unsupported_mode(self):
        _response = {}
        _endpoint = self._mMakeEndpoint({"mode": "unsupported"}, _response)
        with self._mPatchConfig(_endpoint), \
             patch("exabox.managment.src.ExacloudCmdEndpoint.os.path.exists", return_value=False), \
             patch.object(_endpoint, "mOnlyUpgrade") as _only_upgrade, \
             patch.object(_endpoint, "mClean") as _clean, \
             patch.object(_endpoint, "mListBk") as _list_bk, \
             patch.object(_endpoint, "mRollback") as _rollback:
            _endpoint.mPatch()
        _only_upgrade.assert_not_called()
        _clean.assert_not_called()
        _list_bk.assert_not_called()
        _rollback.assert_not_called()
        self.assertEqual(_response.get("status"), 200)
        self.assertNotIn("text", _response)
        self.assertNotIn("error", _response)

    # Auto-generated test for mOnlyUpgrade
    def test_024_exacloud_monlyupgrade_empty_explicit_lite_reports_not_found(self):
        _response = {}
        _endpoint = self._mMakeEndpoint({"lite_location": ""}, _response)
        with patch.object(_endpoint, "mHasOngoingOperations", return_value=False), \
             patch.object(_endpoint, "mGetConfig") as _get_config, \
             patch.object(_endpoint, "mFindLite") as _find_lite:
            _endpoint.mOnlyUpgrade("/tmp/exacloud/", "/tmp/upgrade", "/tmp")
        _get_config.assert_not_called()
        _find_lite.assert_not_called()
        self.assertEqual(_response["status"], 500)
        self.assertEqual(_response["error"], "Error, exacloud_lite location not found")
        self.assertEqual(_response["text"], "Error, exacloud_lite location not found")

    # Auto-generated test for mPatch
    def test_025_exacloud_mpatch_dispatches_clean_without_existing_upgrade_operation(self):
        _endpoint = self._mMakeEndpoint({"mode": "clean"}, {})
        with self._mPatchConfig(_endpoint), \
             patch("exabox.managment.src.ExacloudCmdEndpoint.os.path.exists", return_value=False), \
             patch.object(_endpoint, "mClean") as _clean_method:
            _endpoint.mPatch()
        _clean_method.assert_called_once_with("/tmp/exacloud/", "/tmp/upgrade", "/tmp")



if __name__ == '__main__':
    unittest.main(warnings='ignore')
