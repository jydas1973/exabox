import re
import unittest
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import *
from exabox.log.LogMgr import ebLogError
from unittest.mock import patch, MagicMock, PropertyMock, mock_open
from exabox.ovm.csstep.cs_postginid import csPostGINID
from exabox.ovm.csstep.cs_util import csUtil
import warnings

def mGetMajorityHostVersion(aParam):
    return 'OL7'

def mPingHost(aParam):
    return True

def mGetMajorityHostVersionOl6(aParam):
    return 'OL6'

def mPingHostNotPingable(aParam):
    return False

def mUpdateRpm(aParam, aUndo=True):
    raise Exception

class ebTestCluControlPostGinid(ebTestClucontrol):
    @classmethod
    def setUpClass(self):
        super().setUpClass(True,True)
        warnings.filterwarnings("ignore", category=ResourceWarning)

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetGridHome', return_value=("/u01/app/19.0.0.0/grid", None))
    def test_srvctl(self, mock_mGetGridHome):

        _cmds = {
            self.mGetRegexVm(): [[
                    exaMockCommand("srvctl setenv nodeapps*",  aPersist=True),
                    exaMockCommand("crsctl modify res*",  aPersist=True)
                ]],
            self.mGetRegexLocal(): [[
                    exaMockCommand("rm.*", aRc=0,  aPersist=True),
                    exaMockCommand("ping .*", aRc=0,  aPersist=True)
                ]]
        }

        self.mPrepareMockCommands(_cmds)
        cluctrl = self.mGetClubox()
        cluctrl.mApplyExtraSrvctlConfig()

    def test_undoExecute(self):
        _steplist = ['ESTP_POSTGI_NID']

        _step = csPostGINID()
        _options = self.mGetClubox().mGetOptions()
        with patch('exabox.ovm.csstep.cs_postginid.csUtil.mExecuteOEDAStep'):
            _step.undoExecute(self.mGetClubox(), _options, _steplist)
        self.mGetClubox().mGetMajorityHostVersion = mGetMajorityHostVersion
        self.mGetClubox().mPingHost = mPingHost
        self.mGetClubox().mSetOciExacc(False)
        self.mGetClubox().mSetExabm(True)
        with patch('exabox.ovm.csstep.cs_postginid.csUtil.mExecuteOEDAStep'):
            _step.undoExecute(self.mGetClubox(), _options, _steplist)
        self.mGetClubox().mSetOciExacc(True)
        self.mGetClubox().mSetExabm(False)
        with patch('exabox.ovm.csstep.cs_postginid.csUtil.mExecuteOEDAStep'):
            _step.undoExecute(self.mGetClubox(), _options, _steplist)
        self.mGetClubox().mGetMajorityHostVersion = mGetMajorityHostVersionOl6
        with patch('exabox.ovm.csstep.cs_postginid.csUtil.mExecuteOEDAStep'):
            _step.undoExecute(self.mGetClubox(), _options, _steplist)
        self.mGetClubox().mSetExabm(True)
        with patch('exabox.ovm.csstep.cs_postginid.csUtil.mExecuteOEDAStep'):
            _step.undoExecute(self.mGetClubox(), _options, _steplist)
        self.mGetClubox().mPingHost = mPingHostNotPingable
        with patch('exabox.ovm.csstep.cs_postginid.csUtil.mExecuteOEDAStep'):
            _step.undoExecute(self.mGetClubox(), _options, _steplist)
            
            
    def test_mGetDbaastoolRpmName_default(self):
        _options = self.mGetClubox().mGetOptions()
        _csu = csUtil()
        _default_rpm = 'dbaastools_exa_main.rpm'
        _dbaastools_rpm = _csu.mGetDbaastoolRpmName(_options)
        self.assertEqual(_dbaastools_rpm, _dbaastools_rpm)
        
    
    def test_mGetDbaastoolRpmName_rpm_missing_in_images_folder(self):
        _options = self.mGetClubox().mGetOptions()
        _csu = csUtil()
        _options.jsonconf['location'] = {}
        _options.jsonconf['location']["dbaastoolsrpm"] = 'dbaastools_exa_azure_main.rpm'
        _options.jsonconf['location']["dbaastoolsrpm_checksum"] = 'a256sdfsakjdflk'
        _default_rpm = 'dbaastools_exa_main.rpm'
        # Properly assert that the exception is raised
        with self.assertRaises(ExacloudRuntimeError) as context:
            _csu.mGetDbaastoolRpmName(_options)
        self.assertIn('RPM doest not exist in images folder', str(context.exception))
    
    @patch('subprocess.check_output')
    def test_mGetDbaastoolRpmName_rpm_checksum_matches(self, mock_check_output):
        _options = self.mGetClubox().mGetOptions()
        _csu = csUtil()
        _multicloud_rpm = 'dbaastools_exa_azure_main.rpm'
        _default_rpm = 'dbaastools_exa_main.rpm'
        _multicloud_rpm_path = os.path.join('images/',_multicloud_rpm)
        open(_multicloud_rpm_path, "w").close()
        expected_checksum = 'abc123_hash'
        mock_output = f"{expected_checksum}".encode('utf8')
        mock_check_output.return_value = mock_output
        _options.jsonconf['location'] = {}
        _options.jsonconf['location']["dbaastoolsrpm"] = _multicloud_rpm
        _options.jsonconf['location']["dbaastoolsrpm_checksum"] = expected_checksum
        _dbaastools_rpm = _csu.mGetDbaastoolRpmName(_options)
        self.assertEqual(_dbaastools_rpm, _multicloud_rpm)
        os.remove(_multicloud_rpm_path)
        
    @patch('subprocess.check_output')
    def test_mGetDbaastoolRpmName_rpm_wrong_checksum(self, mock_check_output):
        _options = self.mGetClubox().mGetOptions()
        _csu = csUtil()
        _multicloud_rpm = 'dbaastools_exa_azure_main.rpm'
        _default_rpm = 'dbaastools_exa_main.rpm'
        _multicloud_rpm_path = os.path.join('images/',_multicloud_rpm)
        open(_multicloud_rpm_path, "w").close()
        expected_checksum = 'abc123_hash'
        mock_output = f"{expected_checksum}".encode('utf8')
        mock_check_output.return_value = mock_output
        _options.jsonconf['location'] = {}
        _options.jsonconf['location']["dbaastoolsrpm"] = _multicloud_rpm
        _options.jsonconf['location']["dbaastoolsrpm_checksum"] = 'abc'
        with self.assertRaises(ExacloudRuntimeError) as context:
            _csu.mGetDbaastoolRpmName(_options)
        self.assertIn('*** RPM checksum does not match with payload ***', str(context.exception))
        os.remove(_multicloud_rpm_path)
        
    def test_mGetDbaastoolRpmName_only_check_payload(self):
        _options = self.mGetClubox().mGetOptions()
        _csu = csUtil()
        _multicloud_rpm = 'dbaastools_exa_azure_main.rpm'
        _options.jsonconf['location'] = {}
        _options.jsonconf['location']["dbaastoolsrpm"] = _multicloud_rpm
        _options.jsonconf['location']["dbaastoolsrpm_checksum"] = 'a256sdfsakjdflk'
        _dbaastools_rpm = _csu.mGetDbaastoolRpmName(_options, aLocalPath=None)
        self.assertEqual(_dbaastools_rpm, _multicloud_rpm)

if __name__ == "__main__":
    unittest.main()
