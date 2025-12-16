import re
import unittest
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import *
from exabox.log.LogMgr import ebLogError
from unittest.mock import patch, MagicMock, PropertyMock, mock_open
from exabox.ovm.csstep.cs_prevmchecks import csPreVMChecks
import warnings
from exabox.exadbxs.edv import get_hosts_edv_from_cs_payload, get_hosts_edv_state, EDVState, build_hosts_edv_json

class ebTestCluControlPreVMChecks(ebTestClucontrol):
    @classmethod
    def setUpClass(self):
        super().setUpClass(True,True)
        warnings.filterwarnings("ignore", category=ResourceWarning)


    @patch("exabox.ovm.clumisc.ebCluPreChecks.mVMPreChecks", return_value=0)
    @patch("exabox.ovm.clumisc.ebCluPreChecks.mFetchHardwareAlerts", return_value=1)
    @patch("exabox.utils.node.exaBoxNode.mFileExists", return_value="virsh")
    @patch("exabox.utils.node.exaBoxNode.mGetFileInfo", return_value=None)
    def test_doExecuteBaseDB(self, aMockf1, aMockf2, aMockf3, aMockf4):

        _cmds = {
            self.mGetRegexDom0():
                [[
                    exaMockCommand(".*dumpxml.*", aStdout="", aPersist=True),
                    exaMockCommand("/bin/stat.*", aRc=0,  aPersist=True)
                ]]
        }

        self.mPrepareMockCommands(_cmds)

        _steplist = ['ESTP_PREVM_CHECKS']
        _step = csPreVMChecks()
        _options = self.mGetClubox().mGetOptions()
        _options.jsonconf = self.mGetResourcesJsonFile("payload_basedbclone.json")
        #_options.jsonconf["isClone"] = "True"

        with self.assertRaises(ExacloudRuntimeError):
            _step.doExecute(self.mGetClubox(), _options, _steplist)

if __name__ == '__main__':
    unittest.main()

