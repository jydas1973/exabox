"""
Tests exaBoxCluCtrl methods related to setting zdlra cores.
"""
import unittest

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol


class TestZdlraCoreRatio(ebTestClucontrol):

    """Discovers correct cores for zdlra type env"""

    def test_zdlra_core_ratio(self):

        cluctrl = self.mGetClubox()

        zdlra_xml = \
            'exabox/exatest/cluctrl/cluzdlra/resources/rack_zdlra.xml'

        # load zdlra XML
        jsonconf = cluctrl.mGetArgsOptions().jsonconf

        cluctrl.mSetConfigPath(zdlra_xml)
        cluctrl.mParseXMLConfig(jsonconf)

        _cores = '6'
        if cluctrl.mGetZDLRA().mCheckZdlraInEnv():
            if cluctrl.mCheckConfigOption('zdlra_core_to_vcpu_ratio') is not None:
                _ratio = int(cluctrl.mCheckConfigOption('zdlra_core_to_vcpu_ratio'))
            else:
                _ratio = 1
        else:
            _ratio = 2

        _cores = str(int(_cores) * _ratio)

        for _, _domU in cluctrl.mReturnDom0DomUPair():
            _domUConfig  = cluctrl.mGetMachines().mGetMachineConfig(_domU)
            _domUConfig.mSetMacCores(_cores)

        for _, _domU in cluctrl.mReturnDom0DomUPair():
            _domUConfig  = cluctrl.mGetMachines().mGetMachineConfig(_domU)
            x = _domUConfig.mGetGuestCores()
            if x:
                self.assertEqual(x, '6')

if __name__ == "__main__":
    unittest.main()
