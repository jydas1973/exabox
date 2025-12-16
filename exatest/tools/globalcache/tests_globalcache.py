"""

 $Header: 

 Copyright (c) 2018, 2025, Oracle and/or its affiliates.

 NAME:
      tests_ebNode.py - Unitest for ebNode on clucontrol

 DESCRIPTION:
      Run tests for the method of ebNode on clucontrol

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
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



if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end file
