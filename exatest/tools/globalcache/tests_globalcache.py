"""

 $Header: 

 Copyright (c) 2018, 2026, Oracle and/or its affiliates.

 NAME:
      tests_ebNode.py - Unitest for ebNode on clucontrol

 DESCRIPTION:
      Run tests for the method of ebNode on clucontrol

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
       joysjose 06/22/26 - Check OEDA replay cp status
       joysjose 06/22/26 - Test OEDA replay cp status failure
       joysjose 06/22/26 - Bug 39588664 validate OEDA alias before shell
                           commands
       joysjose 06/22/26 - Bug 39588664 update global cache replay tests
       joysjose 06/19/26 - Update global cache replay unit test
       joysjose 05/12/26 - Bug 39354509 Add multigi OEDA requiredfile alias fallback
       joysjose 11/07/25 - Bug  38599605 - n-3 naming convention change
       ririgoye 02/20/24 - Bug 36315154 - Fixed unit tests to work with images
                           as dictionaries
       ririgoye 01/19/24 - ABug 36159867 - Added unit test where image
                           validation is skipped when a ExaScale service is ran
       naps     07/10/23 - Bug 35502615 - UT updation.
       aypaul   07/24/22 - Updating test case for error scenario changes.

        jesandov    07/27/18 - Creation of the file for xmlpatching
"""

import unittest

import os
from random import shuffle
from unittest.mock import patch

from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from unittest.mock import MagicMock, Mock, patch

from exabox.globalcache.GlobalCacheWorker import GlobalCacheWorker
from exabox.globalcache.GlobalCacheFactory import GlobalCacheFactory
from exabox.core.Error import ExacloudRuntimeError
from exabox.ovm.clucontrol import exaBoxCluCtrl


class ebTestGlobalCache(ebTestClucontrol, unittest.TestCase):

    @classmethod
    def setUpClass(self):
        super().setUpClass()

    def test_000_test_single_worker(self):

        _imagesInfoTxt = self.mGetResourcesTextFile("ImagesInformationexatest_kloneimage.tgz.json")

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [

                [
                    # Initial image Stat
                    exaMockCommand("stat.*exatest_image.tgz", aRc=1),
                    exaMockCommand("cat.*ImagesInformation.json", aRc=1),
                    exaMockCommand("test.*exatest_image.tgz", aRc=1),

                    # Free space
                    exaMockCommand("/bin/df /EXAVMIMAGES", aStdout="100000000"),

                    # Local to Dom0 Copy Image
                    exaMockCommand("mkdir.*GlobalCache"),

                    exaMockCommand("/usr/bin/scp.*exatest_kloneimage.tgz"),
                    exaMockCommand("/bin/scp images/exatest_kloneimage.tgz /EXAVMIMAGES/GlobalCache/exatest_kloneimage.tgz"),
 
                    # Verify local copy
                    exaMockCommand(
                        "stat.*exatest_kloneimage.tgz",
                        aStdout="2021-10-29 08:51:04.099997488,2021-10-29 08:51:04.099997488,126077625"
                    ),
                    exaMockCommand(
                        "sha256sum.*exatest_kloneimage.tgz",
                        aStdout="881a730834393b84af0d4d9b5201ccaadeefa585177518e1987748f783d3bcfa"
                    ),
                    exaMockCommand("/bin/cat /EXAVMIMAGES/GlobalCache/ImagesInformationexatest_kloneimage.tgz.json", aStdout=_imagesInfoTxt),
                    exaMockCommand("/bin/cat /EXAVMIMAGES/GlobalCache/ImagesInformationexatest_kloneimage.tgz.json", aStdout=_imagesInfoTxt),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/GlobalCache/exatest_kloneimage.tgz", aRc=0)

                ],

            ],
        }

        self.mPrepareMockCommands(_cmds)

        _repoImages = [
            {
                "filename"     : "exatest_kloneimage.tgz",
                "shortversion" : 10,
                "longversion"  : 10,
                "map"          : "exatest_kloneimage.tgz",
                "dom0"         : "/EXAVMGUESTIMAGES/GlobalCache/exatest_kloneimage.tgz",
                "local"        : "images/exatest_kloneimage.tgz",
                "service"      : "EXACS",
                "cdb"          : "False",
                "sha256sum"    : "881a730834393b84af0d4d9b5201ccaadeefa585177518e1987748f783d3bcfa"
            }
        ]

        _dyndepImages = {
            "dyndep_version": "2019.288"
        }

        self.mGetClubox().mSetImageFiles(_repoImages)
        self.mGetClubox().mSetDyndepFiles(_dyndepImages)

        _factory = GlobalCacheFactory(self.mGetClubox())
        _factory.mDoParallelCopy()

    def test_001_test_passwordless(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test.*global_cache_key", aRc=1),
                    exaMockCommand("global_cache_key"),
                    exaMockCommand("chmod.*global_cache_key"),
                    exaMockCommand("ssh-keygen -R", aPersist=True),
                ],
                [
                    exaMockCommand("test.*global_cache_key", aRc=1),
                    exaMockCommand("global_cache_key"),
                    exaMockCommand("chmod.*global_cache_key"),
                    exaMockCommand("ssh-keygen -R", aPersist=True),
                    exaMockCommand("authorized_keys", aPersist=True),
                ],
                [
                    exaMockCommand("rm.*global_cache_key"),
                    exaMockCommand("sed.*authorized_keys"),
                ],
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Execute passwordless
        _factory = GlobalCacheFactory(self.mGetClubox())
        _factory.mCreatePasswordless()
        _factory.mCleanPassordless()

    def test_002_test_invalid_hash_images(self):

        #Create args structure
        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand(
                        "sha256sum.*exatest_image.tgz",
                        aStdout="457a730834343b84af024d9b52014caadeefa555177518e1982748f781d3b178"
                    ),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _repoImages = [
            {
                "filename"     : "exatest_image.tgz",
                "shortversion" : 10,
                "longversion"  : 10,
                "map"          : "exatest_image.tgz",
                "dom0"         : "/EXAVMGUESTIMAGES/GlobalCache/exatest_image.tgz",
                "local"        : "images/exatest_image.tgz",
                "service"      : "EXACS",
                "cdb"          : "False",
                "sha256sum"    : "881a730834393b84af0d4d9b5201ccaadeefa585177518e1987748f783d3bcfa"
            }
        ]

        _dyndepImages = {
            "dyndep_version": "2019.288"
        }

        self.mGetClubox().mSetImageFiles(_repoImages)
        self.mGetClubox().mSetDyndepFiles(_dyndepImages)

        # Execute passwordless
        _factory = GlobalCacheFactory(self.mGetClubox())

        _factory.mValidateImageInventory()

    @patch('exabox.BaseServer.AsyncProcessing.ProcessManager.mStartAppend')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsExaScale')
    def test_003_skip_image_validation_during_exascale(self, mock_manager_append, mock_is_exascale):
        # Create mock images
        mock_is_exascale.return_value = True
        _repoImages = [
            {
                "filename"     : "exatest_image.tgz",
                "shortversion" : 10,
                "longversion"  : 10,
                "map"          : "exatest_image.tgz",
                "dom0"         : "/EXAVMGUESTIMAGES/GlobalCache/exatest_image.tgz",
                "local"        : "images/db-klone-exatest_image.tgz",
                "service"      : "EXACS",
                "cdb"          : "False",
                "sha256sum"    : "881a730834393b84af0d4d9b5201ccaadeefa585177518e1987748f783d3bcfa"
            }
        ]
        _dyndepImages = [
            {
                "dyndep_version": "2019.288",
                "grid-klone"    : "mock_value",
                "sha256sum"     : "881a730834393b84af0d4d9b5201ccaadeefa585177518e1987748f783d3bcfa"
            }
        ]
        # Set mock images
        self.mGetClubox().mSetImageFiles(_repoImages)
        self.mGetClubox().mSetDyndepFiles(_dyndepImages)
        # Create factory and run image inventory validation
        _clubox = self.mGetClubox()
        _factory = GlobalCacheFactory(_clubox)
        _factory.mValidateImageInventory()
        # Assert that process manager append is not called
        self.assertFalse(mock_manager_append.called)       

    @patch("exabox.globalcache.GlobalCacheFactory.mGetMultiGIOedaSelection")
    @patch("exabox.globalcache.GlobalCacheFactory.GlobalCacheWorker")
    @patch("exabox.globalcache.GlobalCacheFactory.mStartWorker")
    @patch("exabox.BaseServer.AsyncProcessing.ProcessManager.mJoinProcess")
    @patch("exabox.BaseServer.AsyncProcessing.ProcessManager.mStartAppend")
    def test_004_replay_multigi_oeda_alias_last(self, mock_manager_append,
                                                mock_manager_join,
                                                mock_start_worker,
                                                mock_worker_class,
                                                mock_get_selection):
        _repoImages = [
            {
                "filename": "grid-klone-Linux-x86-64-232600251021.zip",
                "shortversion": 10,
                "longversion": 10,
                "map": "grid-klone-Linux-x86-64-232600251021.zip",
                "local": "images/grid-klone-Linux-x86-64-232600251021.zip",
                "service": "EXACS",
                "cdb": "False",
                "sha256sum": "hash-old"
            },
            {
                "filename": "grid-klone-Linux-x86-64-232610260115.zip",
                "shortversion": 10,
                "longversion": 10,
                "map": "grid-klone-Linux-x86-64-232610260115.zip",
                "local": "images/grid-klone-Linux-x86-64-232610260115.zip",
                "service": "EXACS",
                "cdb": "False",
                "sha256sum": "hash-new"
            }
        ]
        _dyndepImages = {
            "dyndep_version": "2019.288"
        }
        self.mGetClubox().mSetImageFiles(_repoImages)
        self.mGetClubox().mSetDyndepFiles(_dyndepImages)
        mock_get_selection.return_value = {
            "staged_basename": "grid-klone-Linux-x86-64-232610260115.zip",
            "required_basename": "grid-klone-Linux-x86-64-2300026000.zip"
        }

        _events = []
        _mock_worker = MagicMock()
        _mock_worker.mReplayOedaRequiredReflink.side_effect = lambda *_args, **_kwargs: _events.append("replay")
        mock_worker_class.return_value = _mock_worker
        mock_manager_append.side_effect = lambda *_args, **_kwargs: _events.append("append")
        mock_manager_join.side_effect = lambda *_args, **_kwargs: _events.append("join")

        _dom0s, _, _, _ = self.mGetClubox().mReturnAllClusterHosts()
        _factory = GlobalCacheFactory(self.mGetClubox())
        _factory.mDoParallelCopy()

        self.assertEqual(mock_manager_append.call_count, 2)
        mock_start_worker.assert_not_called()
        self.assertEqual(_events, ["append", "append", "join", "replay"])
        mock_worker_class.assert_called_once_with(
            "images/grid-klone-Linux-x86-64-232610260115.zip",
            "hash-new",
            _dom0s
        )
        _mock_worker.mReplayOedaRequiredReflink.assert_called_once_with(
            "grid-klone-Linux-x86-64-2300026000.zip")


    @patch('exabox.globalcache.GlobalCacheFactory.mGetMultiGIOedaSelection')
    @patch('exabox.globalcache.GlobalCacheFactory.mStartWorker')
    @patch('exabox.BaseServer.AsyncProcessing.ProcessManager.mJoinProcess')
    @patch('exabox.BaseServer.AsyncProcessing.ProcessManager.mStartAppend')
    def test_005_skip_replay_when_alias_matches_staged_name(self, mock_manager_append,
                                                            mock_manager_join,
                                                            mock_start_worker,
                                                            mock_get_selection):
        _repoImages = [
            {
                "filename": "grid-klone-Linux-x86-64-232610260115.zip",
                "shortversion": 10,
                "longversion": 10,
                "map": "grid-klone-Linux-x86-64-232610260115.zip",
                "local": "images/grid-klone-Linux-x86-64-232610260115.zip",
                "service": "EXACS",
                "cdb": "False",
                "sha256sum": "hash-new"
            }
        ]
        self.mGetClubox().mSetImageFiles(_repoImages)
        self.mGetClubox().mSetDyndepFiles({"dyndep_version": "2019.288"})
        mock_get_selection.return_value = {
            "staged_basename": "grid-klone-Linux-x86-64-232610260115.zip",
            "required_basename": "grid-klone-Linux-x86-64-232610260115.zip"
        }

        _factory = GlobalCacheFactory(self.mGetClubox())
        _factory.mDoParallelCopy()

        mock_manager_append.assert_called_once()
        mock_manager_join.assert_called_once()
        mock_start_worker.assert_not_called()

    @patch("exabox.globalcache.GlobalCacheFactory.mGetMultiGIOedaSelection")
    @patch("exabox.globalcache.GlobalCacheFactory.GlobalCacheWorker")
    @patch("exabox.globalcache.GlobalCacheFactory.mStartWorker")
    @patch("exabox.BaseServer.AsyncProcessing.ProcessManager.mJoinProcess")
    @patch("exabox.BaseServer.AsyncProcessing.ProcessManager.mStartAppend")
    def test_006_replay_multigi_oeda_alias_propagates_worker_failure(
            self, mock_manager_append, mock_manager_join, mock_start_worker,
            mock_worker_class, mock_get_selection):
        _repoImages = [
            {
                "filename": "grid-klone-Linux-x86-64-232610260115.zip",
                "shortversion": 10,
                "longversion": 10,
                "map": "grid-klone-Linux-x86-64-232610260115.zip",
                "local": "images/grid-klone-Linux-x86-64-232610260115.zip",
                "service": "EXACS",
                "cdb": "False",
                "sha256sum": "hash-new"
            }
        ]
        self.mGetClubox().mSetImageFiles(_repoImages)
        self.mGetClubox().mSetDyndepFiles({"dyndep_version": "2019.288"})
        mock_get_selection.return_value = {
            "staged_basename": "grid-klone-Linux-x86-64-232610260115.zip",
            "required_basename": "grid-klone-Linux-x86-64-2300026000.zip"
        }
        _mock_worker = MagicMock()
        _mock_worker.mReplayOedaRequiredReflink.side_effect = ExacloudRuntimeError(
            0x0754, 0x0A, "Staged image missing")
        mock_worker_class.return_value = _mock_worker

        _factory = GlobalCacheFactory(self.mGetClubox())
        with self.assertRaises(ExacloudRuntimeError):
            _factory.mDoParallelCopy()

        mock_manager_append.assert_called_once()
        mock_manager_join.assert_called_once()
        mock_start_worker.assert_not_called()
        _mock_worker.mReplayOedaRequiredReflink.assert_called_once_with(
            "grid-klone-Linux-x86-64-2300026000.zip")
        

class TestGlobalCacheWorker(ebTestClucontrol, unittest.TestCase):
    def setUp(self):
        # Create a GlobalCacheWorker instance
        imagehash = "881a730834393b84af0d4d9b5201ccaadeefa585177518e1987748f783d3bcfa"
        local     = "images/exatest_image.tgz"
        _ebox = self.mGetClubox()
        _dom0s, _, _, _ = _ebox.mReturnAllClusterHosts()
        _dom0 = _dom0s[0]
        self.worker = GlobalCacheWorker(local,imagehash,_dom0s)
        # Mock the connections attribute
        self.dummy_node = MagicMock()
        self.worker._GlobalCacheWorker__connections = {'dom0-test': self.dummy_node}

    @patch.object(GlobalCacheWorker, 'mGetImageRemotePath')
    def test_mCreateSymbolicLink_grid_klone(self, mock_mGetImageRemotePath):
        # Arrange
        mock_mGetImageRemotePath.return_value = '/EXAVMIMAGES/GlobalCache/grid-klone-Linux-x86-64-232600251021.zip'
        # Patch os.path.basename
        with patch('os.path.basename', return_value='grid-klone-Linux-x86-64-232600251021.zip'):
            # Act
            self.worker.mCreateSymbolicLink('dom0-test')
        
        self.dummy_node.mExecuteCmd.assert_any_call('/bin/rm -f /EXAVMIMAGES/grid-klone-Linux-x86-64-232600251021.zip')
        self.dummy_node.mExecuteCmd.assert_any_call(
            '/bin/cp --reflink /EXAVMIMAGES/GlobalCache/grid-klone-Linux-x86-64-232600251021.zip /EXAVMIMAGES/grid-klone-Linux-x86-64-2300026000.zip')
        self.dummy_node.mExecuteCmd.assert_any_call(
            '/bin/cp --reflink /EXAVMIMAGES/GlobalCache/grid-klone-Linux-x86-64-232600251021.zip /EXAVMIMAGES/grid-klone-Linux-x86-64-2300026000.zip'
        )
        self.assertGreaterEqual(self.dummy_node.mExecuteCmd.call_count, 3)

    @patch.object(GlobalCacheWorker, 'mGetImageRemotePath')
    def test_mCreateSymbolicLink_grid_klone_with_oeda_alias(self, mock_mGetImageRemotePath):
        mock_mGetImageRemotePath.return_value = '/EXAVMIMAGES/GlobalCache/grid-klone-Linux-x86-64-232610260115.zip'
        self.worker._GlobalCacheWorker__additionalAliases = ['grid-klone-Linux-x86-64-2300026000.zip']
        with patch('os.path.basename', return_value='grid-klone-Linux-x86-64-232610260115.zip'):
            self.worker.mCreateSymbolicLink('dom0-test')

        self.dummy_node.mExecuteCmd.assert_any_call(
            '/bin/rm -f /EXAVMIMAGES/grid-klone-Linux-x86-64-2300026000.zip')
        self.dummy_node.mExecuteCmd.assert_any_call(
            '/bin/cp --reflink /EXAVMIMAGES/GlobalCache/grid-klone-Linux-x86-64-232610260115.zip /EXAVMIMAGES/grid-klone-Linux-x86-64-2300026000.zip')

    @patch.object(GlobalCacheWorker, 'mGetImageRemotePath')
    def test_mCreateSymbolicLink_rejects_invalid_oeda_alias(self, mock_mGetImageRemotePath):
        mock_mGetImageRemotePath.return_value = '/EXAVMIMAGES/GlobalCache/grid-klone-Linux-x86-64-232610260115.zip'
        self.worker._GlobalCacheWorker__additionalAliases = ['../grid-klone.zip']
        with patch('os.path.basename', return_value='grid-klone-Linux-x86-64-232610260115.zip'):
            with self.assertRaises(ExacloudRuntimeError):
                self.worker.mCreateSymbolicLink('dom0-test')

        self.dummy_node.mExecuteCmd.assert_not_called()

    @patch.object(GlobalCacheWorker, 'mGetImageRemotePath')
    def test_mCreateSymbolicLink_rejects_invalid_image_basename(self, mock_mGetImageRemotePath):
        mock_mGetImageRemotePath.return_value = '/EXAVMIMAGES/GlobalCache/grid-klone-Linux-x86-64-latest.zip'
        with patch('os.path.basename', return_value='grid-klone-Linux-x86-64-latest.zip'):
            with self.assertRaises(ExacloudRuntimeError):
                self.worker.mCreateSymbolicLink('dom0-test')

        self.dummy_node.mExecuteCmd.assert_not_called()

    @patch.object(GlobalCacheWorker, 'mGetImageRemotePath')
    def test_mCreateSymbolicLink_skips_duplicate_oeda_alias(self, mock_mGetImageRemotePath):
        mock_mGetImageRemotePath.return_value = '/EXAVMIMAGES/GlobalCache/grid-klone-Linux-x86-64-232600251021.zip'
        self.worker._GlobalCacheWorker__additionalAliases = ['grid-klone-Linux-x86-64-2300026000.zip']
        with patch('os.path.basename', return_value='grid-klone-Linux-x86-64-232600251021.zip'):
            self.worker.mCreateSymbolicLink('dom0-test')

        self.assertEqual(self.worker.mGetAdditionalAliases(), ['grid-klone-Linux-x86-64-2300026000.zip'])
        self.assertEqual(self.dummy_node.mExecuteCmd.call_count, 3)



    def test_mCreateOedaRequiredReflink_uses_staged_global_cache_image(self):
        _worker = GlobalCacheWorker(
            "images/grid-klone-Linux-x86-64-232610260115.zip",
            "hash-new",
            ["dom0-test"])
        _node = MagicMock()
        _node.mFileExists.return_value = True
        _node.mGetCmdExitStatus.return_value = 0
        _worker._GlobalCacheWorker__connections = {"dom0-test": _node}

        _worker.mCreateOedaRequiredReflink(
            "dom0-test",
            "grid-klone-Linux-x86-64-2300026000.zip")

        _node.mFileExists.assert_called_once_with(
            "/EXAVMIMAGES/GlobalCache/grid-klone-Linux-x86-64-232610260115.zip")
        _node.mExecuteCmd.assert_any_call(
            "/bin/rm -f /EXAVMIMAGES/grid-klone-Linux-x86-64-2300026000.zip")
        _node.mExecuteCmd.assert_any_call(
            "/bin/cp --reflink /EXAVMIMAGES/GlobalCache/grid-klone-Linux-x86-64-232610260115.zip "
            "/EXAVMIMAGES/grid-klone-Linux-x86-64-2300026000.zip")

    def test_mCreateOedaRequiredReflink_fails_when_cp_reflink_fails(self):
        _worker = GlobalCacheWorker(
            "images/grid-klone-Linux-x86-64-232610260115.zip",
            "hash-new",
            ["dom0-test"])
        _node = MagicMock()
        _node.mFileExists.return_value = True
        _node.mGetCmdExitStatus.return_value = 1
        _worker._GlobalCacheWorker__connections = {"dom0-test": _node}

        with self.assertRaises(ExacloudRuntimeError) as _err:
            _worker.mCreateOedaRequiredReflink(
                "dom0-test",
                "grid-klone-Linux-x86-64-2300026000.zip")

        _msg = _err.exception.mGetErrorMsg()
        self.assertIn("dom0-test", _msg)
        self.assertIn(
            "/EXAVMIMAGES/GlobalCache/grid-klone-Linux-x86-64-232610260115.zip",
            _msg)
        self.assertIn(
            "/EXAVMIMAGES/grid-klone-Linux-x86-64-2300026000.zip",
            _msg)
        _node.mExecuteCmd.assert_any_call(
            "/bin/cp --reflink /EXAVMIMAGES/GlobalCache/grid-klone-Linux-x86-64-232610260115.zip "
            "/EXAVMIMAGES/grid-klone-Linux-x86-64-2300026000.zip")

    def test_mCreateOedaRequiredReflink_fails_when_staged_missing(self):
        _worker = GlobalCacheWorker(
            "images/grid-klone-Linux-x86-64-232610260115.zip",
            "hash-new",
            ["dom0-test"])
        _node = MagicMock()
        _node.mFileExists.return_value = False
        _worker._GlobalCacheWorker__connections = {"dom0-test": _node}

        with self.assertRaises(ExacloudRuntimeError):
            _worker.mCreateOedaRequiredReflink(
                "dom0-test",
                "grid-klone-Linux-x86-64-2300026000.zip")

        _node.mFileExists.assert_called_once_with(
            "/EXAVMIMAGES/GlobalCache/grid-klone-Linux-x86-64-232610260115.zip")
        _node.mExecuteCmd.assert_not_called()

    def test_mReplayOedaRequiredReflink_uses_worker_lock(self):
        _worker = GlobalCacheWorker(
            "images/grid-klone-Linux-x86-64-232610260115.zip",
            "hash-new",
            ["dom0-test"])
        _node = MagicMock()
        _node.mFileExists.return_value = True
        _node.mGetCmdExitStatus.return_value = 0
        _worker._GlobalCacheWorker__connections = {"dom0-test": _node}

        with patch.object(_worker, "mCreateConnections"), \
             patch.object(_worker, "mCloseConnections"), \
             patch("exabox.globalcache.GlobalCacheWorker.ExaLock") as mock_lock:
            _worker.mReplayOedaRequiredReflink(
                "grid-klone-Linux-x86-64-2300026000.zip")

        mock_lock.assert_called_once_with(
            "dom0_global_cache_grid-klone-Linux-x86-64-232610260115.zip")
        _node.mExecuteCmd.assert_any_call(
            "/bin/rm -f /EXAVMIMAGES/grid-klone-Linux-x86-64-2300026000.zip")
        _node.mExecuteCmd.assert_any_call(
            "/bin/cp --reflink /EXAVMIMAGES/GlobalCache/grid-klone-Linux-x86-64-232610260115.zip "
            "/EXAVMIMAGES/grid-klone-Linux-x86-64-2300026000.zip")

    def test_mReplayOedaRequiredReflink_rejects_invalid_required_basename(self):
        _worker = GlobalCacheWorker(
            "images/grid-klone-Linux-x86-64-232610260115.zip",
            "hash-new",
            ["dom0-test"])

        with patch.object(_worker, "mCreateConnections") as mock_create_connections:
            with self.assertRaises(ExacloudRuntimeError):
                _worker.mReplayOedaRequiredReflink("../grid-klone.zip")

        mock_create_connections.assert_not_called()

if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end file
