"""

 $Header: 

 Copyright (c) 2018, 2021, Oracle and/or its affiliates. 

 NAME:
      tests_ociccatppayload.py - Unitest for ATP EXACC

 DESCRIPTION:
      Run tests for ATP EXACC

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
        vgerard     03/09/20 - Adapt test for OCICC
"""

import unittest
import os
import sys
import time
import shutil
import xml.etree.ElementTree as ET
from exabox.ovm.cluexaccatp import ebExaCCAtpSimulatePayload, ebExaCCAtpPatchXML, ebExaCCAtpListener
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol


def override_config(*tags):
    """
    Decorator to specify exabox.conf params for a test class or method.
    """
    def decorator(obj):
        setattr(obj, 'config', tags)
        return obj
    return decorator


class ebTestOciCCAtpListeners(ebTestClucontrol):

    @classmethod
    def setUpClass(self):

        _resources = "exabox/exatest/cluctrl/cluexacc/resources/atpociccpayload/"
        super().setUpClass(aUseOeda=True, aResourceFolder=_resources)

    def test_GenerateListenerCmds(self):
        _nat_struct = []
        for i in range(1,5):
            _vipip = "10.10.10.{}".format(10+i)
            _vip_name = "iad139936exdd00{}nat02-vip.oraclecloud.internal".format(i)
            _client = "scaqak03dv0{}02.us.oracle.com".format(i)
            _nat_struct.append(
            {"ip":_vipip,
            "vipfqdn":_vip_name,
            "viphn":_vip_name.split('.')[0],
            "clienthn":_client.split('.')[0]})

        _listenerInfo = {'aGridHome':"/u01/app/19.0.0.0/grid",
                         'aAdminNetwork':("10.31.112.0","255.255.255.0"),
                         'aNatVips':_nat_struct, 'aListenerPort': 1522}


        _root_cmds,_grid_cmds, _final_grid_cmds, _final_root_cmds = ebExaCCAtpListener.sGenerateListenerCommands(**_listenerInfo)
        
        self.assertEqual(['/u01/app/19.0.0.0/grid/bin/srvctl add network -netnum 2 -subnet 10.31.112.0/255.255.255.0/eth0',
         '/u01/app/19.0.0.0/grid/bin/crsctl start res ora.net2.network -unsupported',
         '/u01/app/19.0.0.0/grid/bin/srvctl add vip -node scaqak03dv0102 -netnum 2 -address iad139936exdd001nat02-vip/255.255.255.0',
         '/u01/app/19.0.0.0/grid/bin/srvctl add vip -node scaqak03dv0202 -netnum 2 -address iad139936exdd002nat02-vip/255.255.255.0',
         '/u01/app/19.0.0.0/grid/bin/srvctl add vip -node scaqak03dv0302 -netnum 2 -address iad139936exdd003nat02-vip/255.255.255.0',
         '/u01/app/19.0.0.0/grid/bin/srvctl add vip -node scaqak03dv0402 -netnum 2 -address iad139936exdd004nat02-vip/255.255.255.0',
         '/u01/app/19.0.0.0/grid/bin/srvctl start vip -netnum 2 -node scaqak03dv0102',
         '/u01/app/19.0.0.0/grid/bin/srvctl start vip -netnum 2 -node scaqak03dv0202',
         '/u01/app/19.0.0.0/grid/bin/srvctl start vip -netnum 2 -node scaqak03dv0302',
         '/u01/app/19.0.0.0/grid/bin/srvctl start vip -netnum 2 -node scaqak03dv0402'],_root_cmds)

        self.assertEqual([
         '/u01/app/19.0.0.0/grid/bin/srvctl add listener -listener LISTENER_BKUP -netnum 2 -endpoints TCP:1522 -oraclehome /u01/app/19.0.0.0/grid',
         '/u01/app/19.0.0.0/grid/bin/srvctl start listener -listener LISTENER_BKUP',
         ],
         _grid_cmds)

        self.assertEqual(['echo "ALTER SYSTEM REGISTER;" | sqlplus -s / as sysasm',
            "/u01/app/19.0.0.0/grid/bin/crsctl modify resourcegroup ora.asmgroup -attr \"START_DEPENDENCIES='weak(global:ora.gns,ora.LISTENER_BKUP.lsnr) dispersion:active(site:type:ora.asmgroup.gtype)'\" -unsupported"],
        _final_grid_cmds)

        self.assertEqual(['/u01/app/19.0.0.0/grid/bin/crsctl stop cluster -all',
                           '/u01/app/19.0.0.0/grid/bin/crsctl start cluster -all'],
                          _final_root_cmds)


class ebTestOciCCAtpXML(ebTestClucontrol):

    @classmethod
    def setUpClass(self):

        _resources = "exabox/exatest/cluctrl/cluexacc/resources/atpociccpayload/"
        super().setUpClass(aUseOeda=True, aResourceFolder=_resources)

        self._xmlpath = '{0}/sample.xml'.format(_resources)

        #Half Rack XML
        self._atpccpatcher = ebExaCCAtpPatchXML(self._xmlpath,

            ['scaqak03dv0102.us.oracle.com', 'scaqak03dv0202.us.oracle.com', 'scaqak03dv0302.us.oracle.com', 'scaqak03dv0402.us.oracle.com'],
            True)

    def test_ExtractNatInfo(self):
        _natNets = self._atpccpatcher.mGetNatNetworksInfo()
        #Check we got good nat infos :)
        _expected = {'scaqak03dv0102': 'iad139936exdd001nat02',
                     'scaqak03dv0202': 'iad139936exdd002nat02',
                     'scaqak03dv0302': 'iad139936exdd003nat02',
                     'scaqak03dv0402': 'iad139936exdd004nat02'}
        # 4 Client nets
        self.assertEqual(4,len(_natNets))
        # Check mappings are good
        for _net in _natNets:
            _gnet = _net[0] # One object per list command
            _hostname = _gnet['hostName']
            self.assertIn(_hostname,_expected)
            self.assertEqual(_expected[_hostname],_gnet['nathostName'])

    def test_mGenNetAdminNetworkCmds(self):
        _adminNetCmds = self._atpccpatcher.mGenNewAdminNetworksCmds()
        # 4 New networks + 4 save action
        self.assertEqual(8,len(_adminNetCmds))
        self.assertIn("ADD NETWORK NETWORKTYPE=ADMIN HOSTNAME=iad139936exdd001nat02 IP=10.10.0.42 NETMASK=255.255.0.0 DOMAINNAME=oraclecloud.internal MASTER=eth0 WHERE hostname=scaqak03dv0102",
        _adminNetCmds)

    def test_mPatching(self):
        _newpath = "/tmp/atpociccpatched.xml"
        shutil.copyfile(self._xmlpath, _newpath)
        ebExaCCAtpPatchXML(_newpath,
            ['scaqak03dv0102.us.oracle.com', 'scaqak03dv0202.us.oracle.com', 'scaqak03dv0302.us.oracle.com', 'scaqak03dv0402.us.oracle.com'],
            True).mPatchXML()
        
         #Confirm XML SUBTYPE by reading with XML parser
        _newconfig = ET.parse(_newpath)
        self.assertEqual('EXACCATP',_newconfig.getroot().attrib['subtype'])
        # Xml from OEDACLI (model NS removed by XMLv1 injector), look that there is the 4 new admin net
        # (with principal hostname = to the nat hostname)
        for i in range(1,4):
            self.assertEqual(1,
                len(_newconfig.findall('./networks/network/[hostName="'+'iad139936exdd00{}nat02'.format(i)+ '"]')))
        os.remove(_newpath)

class ebTestOciCCAtpPayload(ebTestClucontrol):

    @classmethod
    def setUpClass(self):

        _resources = "exabox/exatest/cluctrl/cluexacc/resources/atpociccpayload/"
        super().setUpClass(aUseOeda=True, aResourceFolder=_resources)

    # May be a better way
    def setUp(self):

        method = getattr(self,self._testMethodName)
        config_decorator = getattr(method,'config', {})
        if config_decorator: #[0] to get first tuple elem
            for _configKey, _configValue in list(config_decorator[0].items()):
                self.mGetClubox().mGetCtx().mSetConfigOption(_configKey, _configValue)


    def test_CommandsWithNoConfig(self):
        atpsim = ebExaCCAtpSimulatePayload({'jsonconf':{}},'vmgi_install')
        self.assertTrue(atpsim.mIsATPSimulateEnabled())
        atpsim = ebExaCCAtpSimulatePayload({'jsonconf':{}},'vmgi_wrong')
        self.assertFalse(atpsim.mIsATPSimulateEnabled())

    @override_config({'atp_force':'True'})
    def test_CommandsWithConfigSet(self):
        atpsim = ebExaCCAtpSimulatePayload({'jsonconf':{}},'vmgi_install')
        self.assertTrue(atpsim.mIsATPSimulateEnabled())
        atpsim = ebExaCCAtpSimulatePayload({'jsonconf':{}},'db_install')
        self.assertTrue(atpsim.mIsATPSimulateEnabled())
        atpsim = ebExaCCAtpSimulatePayload({'jsonconf':{}},'vmgi_wrong')
        self.assertFalse(atpsim.mIsATPSimulateEnabled())

    @override_config({'atp_force':'True'})
    def test_AtpOverrideConf(self):
        atpsim = ebExaCCAtpSimulatePayload({'jsonconf':{'atp':{'AutonomousDb':'Y'}}},'vmgi_install')
        self.assertTrue(atpsim.mIsATPSimulateEnabled())
        _payload = {'jsonconf':{'atp':{'AutonomousDb':'N','whitelist':{'client':{'protocol':{'tcp':["@1533@in"]}}}}}}
        atpsim = ebExaCCAtpSimulatePayload(_payload,'vmgi_install')
        self.assertTrue(atpsim.mIsATPSimulateEnabled())
        _new_payload = atpsim.mInjectATPfromAgentWorkaround()
        self.assertEqual('Y',_new_payload['jsonconf']['atp']['AutonomousDb'])
        # Payload modified in place, check that:
        self.assertEqual('Y',_payload['jsonconf']['atp']['AutonomousDb'])

    @override_config({'atp_force':'True','atp_force_dbaas_payload':'exabox/exatest/cluctrl/cluexacc/resources/atpociccpayload/atp_override_sample.json'})
    def test_DefaultDBAASAtpOverrideConf(self):
        _payload = {'jsonconf':{'atp':{'AutonomousDb':'N'},'dbaas_api':{'params':{'existing':'UNTOUCHED'}}}}
        atpsim = ebExaCCAtpSimulatePayload(_payload,'vmgi_install')
        self.assertTrue(atpsim.mIsATPSimulateEnabled())
        _new_payload = atpsim.mInjectATPfromAgentWorkaround()
        self.assertEqual('True',_new_payload['jsonconf']['dbaas_api']['params']['atp']['enabled'])
        self.assertEqual('UNTOUCHED',_new_payload['jsonconf']['dbaas_api']['params']['existing'])

    @override_config({'atp_force':'True'})
    def test_DBVersionOverride(self):
        _payload = {'jsonconf':{'dbParams':{"version":"11204"}}}
        atpsim = ebExaCCAtpSimulatePayload(_payload,'db_install')
        self.assertTrue(atpsim.mIsATPSimulateEnabled())
        self.assertEqual('11204',_payload['jsonconf']['dbParams']['version'])
        atpsim.mInjectATPfromAgentWorkaround()
        # Check version forced to 19000
        self.assertEqual('19000',_payload['jsonconf']['dbParams']['version'])

    @override_config({'atp_force':'True','atp_force_dbaas_payload':'exabox/exatest/cluctrl/cluexacc/resources/atpociccpayload/atp_override_sample.json'})
    def test_CustomDBAASOverride(self):
        _payload = {'jsonconf':{'atp':{'AutonomousDb':'N'},'dbaas_api':{'params':{'existing':'UNTOUCHED'}}}}
        atpsim = ebExaCCAtpSimulatePayload(_payload,'vmgi_install')
        self.assertTrue(atpsim.mIsATPSimulateEnabled())
        atpsim.mInjectATPfromAgentWorkaround()
        self.assertEqual('True',_payload['jsonconf']['dbaas_api']['params']['atp']['enabled'])
        self.assertEqual('UNTOUCHED',_payload['jsonconf']['dbaas_api']['params']['existing'])
        self.assertEqual("Autonomous Transaction Processing - Dedicated",
                        _payload['jsonconf']['dbaas_api']['params']['cns']['line_of_business'])

    @override_config({'atp_force':'True','atp_force_dbaas_payload':'exabox/exatest/cluctrl/cluexacc/resources/atpociccpayload/atp_NOTEXISTS.json'})
    def test_CustomDBAASOverrideWrongFile(self):
        _payload = {'jsonconf':{'atp':{'AutonomousDb':'N'},'dbaas_api':{'params':{'existing':'UNTOUCHED'}}}}
        atpsim = ebExaCCAtpSimulatePayload(_payload,'vmgi_install')
        self.assertRaises(ValueError,atpsim.mInjectATPfromAgentWorkaround)

    @override_config({'atp_force':'True','atp_force_dbaas_payload':'exabox/exatest/cluctrl/cluexacc/resources/atpociccpayload/atp_override_invalid.json'})
    def test_CustomDBAASOverrideInvalidJSON(self):
        _payload = {'jsonconf':{'atp':{'AutonomousDb':'N'},'dbaas_api':{'params':{'existing':'UNTOUCHED'}}}}
        atpsim = ebExaCCAtpSimulatePayload(_payload,'vmgi_install')
        self.assertRaises(ValueError,atpsim.mInjectATPfromAgentWorkaround)


if __name__ == '__main__':
    unittest.main()

