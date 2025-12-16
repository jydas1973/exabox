import unittest

from unittest.mock import patch, mock_open

from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.kvmcpumgr import exaBoxKvmCpuMgr
import os


class TestOedaVersion(ebTestClucontrol):

    def setUp(self):
        self.mGetClubox()._exaBoxCluCtrl__ociexacc = False
        self.mGetClubox()._exaBoxCluCtrl__kvm_enabled = True

    def test_oedaver_success(self):

        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/test -e /root/oeda/install.sh", aRc=0,  aPersist=True),
                    exaMockCommand("/bin/test -e .*oeda/properties/es.properties", aRc=0,  aPersist=True),
                    exaMockCommand("/bin/bash install.sh -h", aRc=0,  aPersist=True, aStdout="install.sh -cf <config.xml> -l [options]\n  Version : 220228"),
                    exaMockCommand("/bin/grep Version", aRc=0,  aPersist=True, aStdout="  Version : 220228"),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        _options = self.mGetPayload()
        cluctrl = self.mGetClubox()
        cluctrl.mSetOptions(_options)
        _rc = cluctrl.mExecuteOEDAStep("version", _options, None)
        self.assertEqual(_rc, 0)

    def test_oedaver_fail(self):

        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/test -e /root/oeda/install.sh", aRc=0,  aPersist=True),
                    exaMockCommand("/bin/test -e .*oeda/properties/es.properties", aRc=0,  aPersist=True),
                    exaMockCommand("/bin/bash install.sh -h", aRc=0,  aPersist=True, aStdout="install.sh -cf <config.xml> -l [options]"),
                    exaMockCommand("/bin/grep Version", aRc=0,  aPersist=True),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        _options = self.mGetPayload()
        cluctrl = self.mGetClubox()
        cluctrl.mSetOptions(_options)
        _rc = cluctrl.mExecuteOEDAStep("version", _options, None)
        self.assertNotEqual(_rc, 0)

    def test_mSetScanPropertyFalseOedaHappyPathSetProperty(self):
        """
        Tests the method mSetScanPropertyFalseOeda for happy path where the properties
        file exists and also the property ADDSCANIPTOHOSTSFILEONEXC=true exists.
        Also, it is set successfully by sed.
        """
        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/grep -q ADDSCANIPTOHOSTSFILEONEXC", aRc=0, aPersist=True),
                    exaMockCommand("/bin/sed", aRc=0, aPersist=True),
                    exaMockCommand("/bin/grep -q 'ADDSCANIPTOHOSTSFILEONEXC=false'", aRc=0, aPersist=True)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        cluctrl = self.mGetClubox()
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOedaPath', return_value="/u01/oracle/ecra_installs/etf123/ecs/exacloud/oeda/requests/123556677788"),\
            patch('os.path.exists', return_value=True):
            cluctrl.mSetScanPropertyFalseOeda()

    def test_mSetScanPropertyFalseOedaHappyPathAddProperty(self):
        """
        Tests the method mSetScanPropertyFalseOeda for happy path where the properties
        file exists and the property ADDSCANIPTOHOSTSFILEONEXC does not exist.
        But, it is added successfully using file.write.
        """
        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/grep -q ADDSCANIPTOHOSTSFILEONEXC", aRc=1, aPersist=True),
                    exaMockCommand("/bin/grep -q 'ADDSCANIPTOHOSTSFILEONEXC=false'", aRc=0, aPersist=True)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        cluctrl = self.mGetClubox()
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOedaPath', return_value="/u01/oracle/ecra_installs/etf123/ecs/exacloud/oeda/requests/123556677788"),\
            patch('os.path.exists', return_value=True),\
            patch("builtins.open", mock_open(read_data="data")):
            cluctrl.mSetScanPropertyFalseOeda()

    def test_mSetScanPropertyFalseOedaBadPathFileNotExists(self):
        """
        Tests the method mSetScanPropertyFalseOeda for bad path where the properties
        file does not exists.
        """

        cluctrl = self.mGetClubox()
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOedaPath', return_value="/u01/oracle/ecra_installs/etf123/ecs/exacloud/oeda/requests/123556677788"),\
            patch('os.path.exists', return_value=False):
            cluctrl.mSetScanPropertyFalseOeda()

    def test_mSetScanPropertyFalseOedaBadPathVerifyFailed(self):
        """
        Tests the method mSetScanPropertyFalseOeda for bad path where the properties
        file exists and the property ADDSCANIPTOHOSTSFILEONEXC does not exist.
        And, it is failed to be added successfully using file.write - verification fails.
        """

        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/grep -q ADDSCANIPTOHOSTSFILEONEXC", aRc=1, aPersist=True),
                    exaMockCommand("/bin/grep -q 'ADDSCANIPTOHOSTSFILEONEXC=false'", aRc=1, aPersist=True)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        cluctrl = self.mGetClubox()
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOedaPath', return_value="/u01/oracle/ecra_installs/etf123/ecs/exacloud/oeda/requests/123556677788"),\
            patch('os.path.exists', return_value=True),\
            patch("builtins.open", mock_open(read_data="data")):
            cluctrl.mSetScanPropertyFalseOeda()

    def test_mSetScanPropertyFalseOedaBadPathSetProperty(self):
        """
        Tests the method mSetScanPropertyFalseOeda for bad path where the properties
        file exists and also the property ADDSCANIPTOHOSTSFILEONEXC=true exists.
        But, it is failed to get set by sed.
        """

        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/grep -q ADDSCANIPTOHOSTSFILEONEXC", aRc=0, aPersist=True),
                    exaMockCommand("/bin/sed", aRc=1, aPersist=True)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        cluctrl = self.mGetClubox()
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOedaPath', return_value="/u01/oracle/ecra_installs/etf123/ecs/exacloud/oeda/requests/123556677788"),\
            patch('os.path.exists', return_value=True):
            cluctrl.mSetScanPropertyFalseOeda()

    def test_mSetScanPropertyFalseOedaBadPathAddPropertyException(self):
        """
        Tests the method mSetScanPropertyFalseOeda for bad path where the properties
        file exists and the property ADDSCANIPTOHOSTSFILEONEXC does not exist.
        And, it is failed to be added successfully using file.write such that an exception is raised.
        """

        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/grep -q ADDSCANIPTOHOSTSFILEONEXC", aRc=1, aPersist=True)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        cluctrl = self.mGetClubox()
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOedaPath', return_value="/u01/oracle/ecra_installs/etf123/ecs/exacloud/oeda/requests/123556677788"),\
            patch('os.path.exists', return_value=True):
            cluctrl.mSetScanPropertyFalseOeda()

if __name__ == '__main__':
    unittest.main()

