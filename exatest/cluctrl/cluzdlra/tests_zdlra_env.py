"""
Tests exaBoxCluCtrl methods related to setting zdlra flag based on xml.
"""
import unittest

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from string import punctuation

class TestZdlraEnv(ebTestClucontrol):
    """Discovers zdlra type env based on input xml."""

    def test_zdlra_env(self):
        """Test exaBoxCluCtrl.IsZdlraProv()"""
        cluctrl = self.mGetClubox()

        zdlra_xml = \
            'exabox/exatest/cluctrl/cluzdlra/resources/rack_zdlra.xml'

        # load zdlra XML
        jsonconf = cluctrl.mGetArgsOptions().jsonconf

        cluctrl.mSetConfigPath(zdlra_xml)
        cluctrl.mParseXMLConfig(jsonconf)

        # Based on attributes in xml, zdlra flag should be enabled !
        zdlra_flag = cluctrl.mGetZDLRA().mCheckZdlraInEnv()
        self.assertEqual(zdlra_flag, True)

    def test_zdlra_random_pwd(self):
        """Test exaBoxCluCtrl.IsZdlraProv()"""
        cluctrl = self.mGetClubox()

        for i in range(1,1000):
            _pwd_proper = False
            _pwd = cluctrl.mGetZDLRA().mGenerate_random_password()
            if (any(x.isupper() for x in _pwd) and any(x.islower() for x in _pwd) and any(x.isdigit() for x in _pwd) and any(x in _pwd for x in punctuation)):
                _pwd_proper = True
            if _pwd_proper and _pwd[:1].isalpha() and _pwd[-1].isalpha():
                _pwd_proper = True
            else:
                _pwd_proper = False
            self.assertEqual(_pwd_proper, True)

if __name__ == "__main__":
    unittest.main()
