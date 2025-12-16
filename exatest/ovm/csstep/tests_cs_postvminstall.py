import unittest

from unittest.mock import patch

from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import *
from exabox.log.LogMgr import ebLogInfo
from exabox.ovm.csstep.cs_util import csUtil

class testOptions(object): pass

class ebTestCSPostVmInstall(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestCSPostVmInstall, self).setUpClass(False,False)

    def test_mCCIDomUs_t1(self):

        ebLogInfo("")
        ebLogInfo("Running test_mCCIDomUs")

        _cmds = {
            self.mGetRegexVm():
            [
                [
                    exaMockCommand("curl *", aRc=0, aStdout="SUCCESS", aPersist=True)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mCCIDomUs()

    def test_mCCIDomUs_t2(self):

        ebLogInfo("")
        ebLogInfo("Running test_mCCIDomUs")

        _cmds = {
            self.mGetRegexVm():
            [
                [
                    exaMockCommand("curl *", aRc=1, aPersist=True)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mCCIDomUs()

if __name__ == "__main__":
    unittest.main(warnings='ignore')
