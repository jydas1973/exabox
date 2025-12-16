"""

 $Header: 

 Copyright (c) 2020, 2025, Oracle and/or its affiliates.

 NAME:
      tests_x9discovery.py - Unitest for clunetdiscover.py module

 DESCRIPTION:
      Run tests for the methods of module

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
       aararora 06/27/24 - Bug 36285522: Add error fields for healthcheck in
                           case of network detection failure.
       aararora 08/07/23 - Bug 34841404: Add test for hardware fault if 3 of
                           the interfaces are up instead of 4.
       ffrrodri 03/03/21 - Enh 32490987: Add tests for support half_net extra
                           parameter functionality
       ffrrodri 01/06/21 - Enh 32350429: Modify test to consider absolute paths in
                           commands and tests added for validation of
                           supportedNetwork.json structure; clunetworkdetect module
                           path and data paths were updated
       vgerard  12/18/20 - Creation of the file
"""

import unittest
import re
import jsonschema
from jsonschema import validate

from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import *
from exabox.ovm.clunetworkdetect import ebOEDANetworkConfiguration, ebDiscoverOEDANetwork, ebNetworkType, \
    ebPortState
from unittest.mock import patch, Mock

class mockStream():

    def __init__(self, aStreamContents=["None"]):
        self.stream_content = aStreamContents

    def readlines(self):
        return self.stream_content

    def read(self):
        return self.stream_content[0]

class ebTestX9NetworkDetect(ebTestClucontrol):
    SUPPORTED_NETWORK_PATH = 'properties/supportedNetworks.json'
    SUPPORTED_NETWORK_SCHEMA_PATH = 'properties/supportedNetworks-schema.json'

    def mGetNodeModel(self, aHostName):
        return 'X9'

    def mGetNodeModelX8(self, aHostName):
        return 'X8'

    @classmethod
    def setUpClass(self):
        # Surcharge ebTestClucontrol, to specify noDB/noOEDA
        super().setUpClass(False, True)

    def setUp(self):
        # Ensure every test begin with standard conf
        self.mGetClubox()._exaBoxCluCtrl__ociexacc = True
        self.mGetClubox().mGetNodeModel = self.mGetNodeModel
        _node = Mock()
        self.net_class = ebDiscoverOEDANetwork(_node, 'X9', self.mGetClubox())

    def mMockCmmandsGen(self, aCachedValue=None, aCacheWrong=False, aStraightUpInterfaces=[],
                        aUpAfterBounceInterfaces=[], aDownInterfaces=[], aFiberInterfaces=[], aCopperInterfaces=[]):

        _cache_rc = 1 if aCachedValue == None else 0
        _dom0_cmds = [exaMockCommand("/bin/test -e /opt/exacloud/network/DETECTED_NETWORK", aRc=_cache_rc)]

        if aCachedValue:
            _dom0_cmds.append(exaMockCommand('/bin/cat /opt/exacloud/network/DETECTED_NETWORK', aStdout=aCachedValue))
            _dom0_cmds.append(exaMockCommand('/bin/rm -f /opt/exacloud/network/DETECTED_NETWORK'))

        # For test testing wrong cache value (either plain invalid, or not matching Interfaces up)
        if aCacheWrong:
            _dom0_cmds.append(exaMockCommand('/bin/rm -f /opt/exacloud/network/DETECTED_NETWORK'))

        # An interfaces that is not up or up after bounce or Down is MISSING
        # Inspected X9 IFs Goes from eth1 to eth12
        _if_states = {}
        _if_types = {}
        # Initialize all states to empty list
        for _state in ebPortState:
            _if_states[_state] = []

        # Initialize all network types
        for _type in ebNetworkType:
            _if_types[_type] = []

        for _if in map("eth{}".format, range(1, 13)):
            # LINK STATE
            if _if in aStraightUpInterfaces:
                _if_states[ebPortState.UP].append(_if)
            elif _if in aUpAfterBounceInterfaces:
                _if_states[ebPortState.UP_AFTER_BOUNCE].append(_if)
            elif _if in aDownInterfaces:
                _if_states[ebPortState.DOWN].append(_if)
            else:
                _if_states[ebPortState.MISSING].append(_if)

            # PORT TYPE
            if _if in aFiberInterfaces:
                _if_types[ebNetworkType.FIBER].append(_if)
            elif _if in aCopperInterfaces:
                _if_types[ebNetworkType.COPPER].append(_if)
            else:
                _if_types[ebNetworkType.UNKNOWN].append(_if)

        aLinkOutput = {ebPortState.UP: (lambda x: [
            exaMockCommand(re.escape(fr'/sbin/ethtool {x} | /bin/grep "Link detected"'), aPersist=True,
                           aStdout="  Link detected: yes")]),
                       ebPortState.UP_AFTER_BOUNCE: (lambda x: [
                           exaMockCommand(re.escape(fr'/sbin/ethtool {x} | /bin/grep "Link detected"'),
                                          aStdout="  Link detected : no"),
                           exaMockCommand(re.escape(
                               fr'/sbin/ifdown {x} ; /bin/sleep 5 ; /sbin/ifup {x} ; /bin/sleep 15 ; /sbin/ifconfig  {x} up ; /bin/sleep 5 ;'),
                               aStdout="Connection successfully activated (D-Bus active path:/org/freedesktop/NetworkManager/ActiveConnection/20"),
                           exaMockCommand(re.escape(
                               fr'/sbin/ethtool {x} | /bin/grep "Link detected"'),
                               aStdout="Link detected : yes")]),
                       ebPortState.DOWN: (lambda x: [
                           exaMockCommand(re.escape(fr'/sbin/ethtool {x} | /bin/grep "Link detected"'), aPersist=True,
                                          aStdout="  Link detected: no")]),
                       ebPortState.MISSING: (lambda x: [
                           exaMockCommand(re.escape(fr'/sbin/ethtool {x} | /bin/grep "Link detected"'), aPersist=True,
                                          aRc=1)])}

        aPortOutput = {ebNetworkType.FIBER: (lambda x: [
            exaMockCommand(re.escape(fr'/sbin/ethtool {x} | /bin/grep Port'), aPersist=True, aStdout="  Port: FIBRE")]),
                       ebNetworkType.COPPER: (lambda x: [
                           exaMockCommand(re.escape(fr'/sbin/ethtool {x} | /bin/grep Port'), aPersist=True,
                                          aStdout="  Port: Twisted Pair")]),
                       ebNetworkType.UNKNOWN: (lambda x: [
                           exaMockCommand(re.escape(fr'/sbin/ethtool {x} | /bin/grep Port'), aPersist=True,
                                          aStdout="  Port: Unknown!")])
                       }

        # Generate expected ethtool command from data structures above
        for _ifstatus in _if_states:
            for _ifcmds in map(aLinkOutput[_ifstatus], _if_states[_ifstatus]):
                _dom0_cmds.extend(_ifcmds)

        for _if_type in _if_types:
            for _ifcmds in map(aPortOutput[_if_type], _if_types[_if_type]):
                _dom0_cmds.extend(_ifcmds)

        # Cache creation

        _dom0_cmds.append(exaMockCommand(re.escape('/bin/mkdir -p /opt/exacloud/network')))
        _dom0_cmds.append(exaMockCommand(r"/bin/sh -c '/bin/echo .* > /opt/exacloud/network/DETECTED_NETWORK'"))

        _cmds = {
            self.mGetRegexDom0(): [_dom0_cmds]}

        return _cmds

    def mGenericTest(self, aExpectedResult=None, *args, **kwargs):
        _cmds = self.mMockCmmandsGen(*args, **kwargs)
        self.mPrepareMockCommands(_cmds)
        # First dom0 of default XML
        _dom0, _ = self.mGetClubox().mReturnDom0DomUPair()[0]

        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_dom0)
        _net = ebDiscoverOEDANetwork(_node, 'X9', self.mGetClubox(), True).mGetNetwork()
        if aExpectedResult is not None:
            self.assertEqual(aExpectedResult.name, _net.name)

    def validateSupportedNetworksJSON(self, aErrorScenario=False):
        """
        Validate JSON data supportedNetwork.json
        with its supportedNetworks-schema.json schema
        """

        supportedNetworks = None
        schema = None

        try:
            abs_path = get_gcontext().mGetBasePath()
            supported_network_file = os.path.join(abs_path, self.SUPPORTED_NETWORK_PATH)
            supported_network_schema_file = os.path.join(abs_path, self.SUPPORTED_NETWORK_SCHEMA_PATH)
            # Open the JSON data and the schema from their files
            with open(supported_network_file) as json_data_file:
                supportedNetworks = json.load(json_data_file)
            with open(supported_network_schema_file) as json_data_file:
                schema = json.load(json_data_file)
        except Exception as e:
            print(e)

        if aErrorScenario and supportedNetworks:
            del supportedNetworks['models']['x9']

        try:
            # Validates the data with the schema
            validate(supportedNetworks, schema)
        except jsonschema.exceptions.ValidationError as e:
            raise e

        return True

    def test_validate_network_supported_data_json(self):
        self.assertIs(self.validateSupportedNetworksJSON(), True)

    def test_validate_network_supported_data_json_error_scenario(self):
        try:
            self.validateSupportedNetworksJSON(True)
        except jsonschema.exceptions.ValidationError as e:
            self.assertRaises(Exception, e)

    def test_network_x9_no_cache_one_interface_down(self):
        self.mGenericTest(None,
                          aStraightUpInterfaces=['eth11', 'eth9', 'eth10'],
                          aCopperInterfaces=['eth9', 'eth10', 'eth11'])

    def test_network_x9_cache_one_interface_down(self):
        self.mGenericTest(None,
                          aCachedValue='OCIEXACC_FULL_COPPER',
                          aStraightUpInterfaces=['eth11', 'eth9', 'eth10'],
                          aCopperInterfaces=['eth9', 'eth10', 'eth11'])

    def test_network_x9_no_cache_all_missing(self):
        # No network info/ all missing DOWN
        self.mGenericTest(None)

    def test_network_x9_no_cache_full_fiber(self):
        self.mGenericTest(self.net_class.SupportedX9Network.OCIEXACC_FULL_FIBER,
                          aStraightUpInterfaces=['eth1', 'eth2', 'eth9', 'eth10'],
                          aFiberInterfaces=['eth1', 'eth2', 'eth9', 'eth10'])

    def test_network_x9_no_cache_full_fiber_with_BUMP(self):
        self.mGenericTest(self.net_class.SupportedX9Network.OCIEXACC_FULL_FIBER, aStraightUpInterfaces=['eth1', 'eth9'],
                          aUpAfterBounceInterfaces=['eth2', 'eth10'],
                          aFiberInterfaces=['eth1', 'eth2', 'eth9', 'eth10'])

    def test_network_x9_no_cache_full_copper(self):
        self.mGenericTest(self.net_class.SupportedX9Network.OCIEXACC_FULL_COPPER,
                          aStraightUpInterfaces=['eth9', 'eth10', 'eth11', 'eth12'],
                          aCopperInterfaces=['eth9', 'eth10', 'eth11', 'eth12'])

    def test_network_x9_no_cache_base_half_copper(self):
        self.mGenericTest(self.net_class.SupportedX9Network.OCIEXACC_BASE_HALF_COPPER, aStraightUpInterfaces=['eth9', 'eth10'],
                          aCopperInterfaces=['eth9', 'eth10'])

    def test_network_x9_no_cache_mixed_copper_client(self):
        self.mGenericTest(self.net_class.SupportedX9Network.OCIEXACC_CLIENT_COPPER_BACKUP_FIBER,
                          aStraightUpInterfaces=['eth1', 'eth2', 'eth9', 'eth10'], aFiberInterfaces=['eth1', 'eth2'],
                          aCopperInterfaces=['eth9', 'eth10'])

    def test_network_x9_no_cache_mixed_fiber_client(self):
        self.mGenericTest(self.net_class.SupportedX9Network.OCIEXACC_CLIENT_FIBER_BACKUP_COPPER,
                          aStraightUpInterfaces=['eth1', 'eth2', 'eth11', 'eth12'], aFiberInterfaces=['eth1', 'eth2'],
                          aCopperInterfaces=['eth11', 'eth12'])

    # Code coverage for Cache path (Good Value, express code path, no need for aFiber since just interfaces aliveness checked)
    def test_network_x9_cache(self):
        self.mGenericTest(self.net_class.SupportedX9Network.OCIEXACC_FULL_FIBER, aCachedValue='OCIEXACC_FULL_FIBER',
                          aStraightUpInterfaces=['eth1', 'eth2', 'eth9', 'eth10'])

    # Code coverage for Cache path (Wrong Value, FULL REDETECTION)
    def test_network_x9_cache_EXCEPTION(self):
        self.mGenericTest(self.net_class.SupportedX9Network.OCIEXACC_FULL_FIBER, aCachedValue='GARBAGE', aCacheWrong=True,
                          aStraightUpInterfaces=['eth1', 'eth2', 'eth9', 'eth10'],
                          aFiberInterfaces=['eth1', 'eth2', 'eth9', 'eth10'])

    # Code coverage for Cache path (Wrong interfaces are catched and full redetection is done)
    def test_network_x9_cache_WRONG(self):
        self.mGenericTest(self.net_class.SupportedX9Network.OCIEXACC_FULL_FIBER, aCachedValue='OCIEXACC_FULL_COPPER', aCacheWrong=True,
                          aStraightUpInterfaces=['eth1', 'eth2', 'eth9', 'eth10'],
                          aFiberInterfaces=['eth1', 'eth2', 'eth9', 'eth10'])

    # Test Generation of OEDA properties from network object
    def test_oedaproperties(self):
        self.assertEqual('vmbondeth0:eth1,eth2:bondeth0',
                         str(self.net_class.SupportedX9Network.OCIEXACC_FULL_FIBER.value.mGetClientNet()))
        self.assertEqual('vmbondeth1:eth9,eth10:bondeth1',
                         str(self.net_class.SupportedX9Network.OCIEXACC_FULL_FIBER.value.mGetBackupNet()))
        self.assertEqual('vmeth0::eth0', str(self.net_class.SupportedX9Network.OCIEXACC_FULL_FIBER.value.mGetAdminNet()))

    def test_nonX9(self):
        _dom0, _ = self.mGetClubox().mReturnDom0DomUPair()[0]
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_dom0)
        _netClass = ebDiscoverOEDANetwork(_node, 'X7', self.mGetClubox(), True)
        self.assertRaises(NotImplementedError, _netClass.mGetNetwork)

    def test_network_x9_critical_log(self):
        self.mGenericTest(None, aStraightUpInterfaces=['eth1', 'eth3'], aFiberInterfaces=['eth2', 'eth6'])

    # Half_net tests
    def test_network_x9_no_cache_mixed_fiber_client_half_net(self):
        self.mGenericTest(self.net_class.SupportedX9Network.OCIEXACC_CLIENT_FIBER_BACKUP_COPPER_HALF_NET,
                          aStraightUpInterfaces=['eth1', 'eth2'], aFiberInterfaces=['eth1', 'eth2'],
                          aCopperInterfaces=['eth11', 'eth12'])

    # Detect degrated_net over half_net
    def test_network_x9_no_cache_base_half_fiber(self):
        self.mGenericTest(self.net_class.SupportedX9Network.OCIEXACC_BASE_HALF_FIBER, aStraightUpInterfaces=['eth5', 'eth6'],
                          aFiberInterfaces=['eth6', 'eth5'])

    def test_oedaproperties_half_net(self):
        self.assertEqual('vmbondeth0:eth1,eth2:bondeth0',
                         str(self.net_class.SupportedX9Network.OCIEXACC_CLIENT_FIBER_BACKUP_COPPER_HALF_NET.value.mGetClientNet()))
        self.assertEqual('vmbondeth0:eth1,eth2:bondeth1',
                         str(self.net_class.SupportedX9Network.OCIEXACC_CLIENT_FIBER_BACKUP_COPPER_HALF_NET.value.mGetBackupNet()))
        self.assertEqual('vmeth0::eth0',
                         str(self.net_class.SupportedX9Network.OCIEXACC_CLIENT_FIBER_BACKUP_COPPER_HALF_NET.value.mGetAdminNet()))

    def mGetCmd(self):
        return 'checkcluster'

    def mGetCmdCreateService(self):
        return 'createservice'

    def test_mGetNetworkSetupInformation(self):
        _dom0, _ = self.mGetClubox().mReturnDom0DomUPair()[0]
        self.mGetClubox().mGetCmd = self.mGetCmd
        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmd', return_value=(None, mockStream(['yes']), None)),\
             patch('exabox.utils.node.exaBoxNode.mGetHostname', return_value='lhr118875exdd002.oraclecloud.internal'):
            print(self.mGetClubox().mGetNetworkSetupInformation("all", _dom0))
        self.mGetClubox().mGetNodeModel = self.mGetNodeModelX8
        _node = Mock()
        self.net_class = ebDiscoverOEDANetwork(_node, 'X8', self.mGetClubox())
        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmd', return_value=(None, mockStream(['no']), None)),\
             patch('exabox.utils.node.exaBoxNode.mGetHostname', return_value='lhr118875exdd002.oraclecloud.internal'):
            print(self.mGetClubox().mGetNetworkSetupInformation("all", _dom0))
        # below is to test for DR network when the links are up for X8 hardware
        self.mGetClubox().mSetDRNetPresent(True)
        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmd', return_value=(None, mockStream(['yes']), None)),\
             patch('exabox.utils.node.exaBoxNode.mGetHostname', return_value='lhr118875exdd002.oraclecloud.internal'):
            print(self.mGetClubox().mGetNetworkSetupInformation("all", _dom0))
        self.mGetClubox().mGetNodeModel = self.mGetNodeModel
        _node = Mock()
        self.net_class = ebDiscoverOEDANetwork(_node, 'X9', self.mGetClubox())
        # Below is a test for DR network when client and backup networks are half nets
        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmd', return_value=(None, mockStream(['yes']), None)),\
             patch('exabox.utils.node.exaBoxNode.mGetHostname', return_value='lhr118875exdd002.oraclecloud.internal'),\
             patch('exabox.ovm.clunetworkdetect.ebDiscoverOEDANetwork.mGetNetwork', return_value=self.net_class.SupportedX9Network.OCIEXACC_BASE_HALF_FIBER):
            _previous_network_info = self.mGetClubox().mGetNetworkSetupInformation("all", _dom0)
            print(_previous_network_info)
        # Below is a test for DR network when client and backup networks are full fiber but some of the links are down
        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmd', return_value=(None, mockStream(['no']), None)),\
             patch('exabox.utils.node.exaBoxNode.mGetHostname', return_value='lhr118875exdd002.oraclecloud.internal'),\
             patch('exabox.ovm.clunetworkdetect.ebDiscoverOEDANetwork.mGetNetwork', return_value=self.net_class.SupportedX9Network.OCIEXACC_FULL_FIBER):
            print(self.mGetClubox().mGetNetworkSetupInformation("all", _dom0))
        # Below is a test for DR network when client and backup networks are full fiber but some of the links are down
        # And there is an error information already present in the error dictionary
        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmd', return_value=(None, mockStream(['no']), None)),\
             patch('exabox.utils.node.exaBoxNode.mGetHostname', return_value='lhr118875exdd002.oraclecloud.internal'),\
             patch('exabox.ovm.clunetworkdetect.ebDiscoverOEDANetwork.mGetNetwork', return_value=self.net_class.SupportedX9Network.OCIEXACC_FULL_FIBER):
            self.mGetClubox().mSetNetDetectError(_dom0, _previous_network_info["ERROR"][_dom0])
            print(self.mGetClubox().mGetNetworkSetupInformation("all", _dom0))
        self.mGetClubox().mGetCmd = self.mGetCmdCreateService
        # Below flow is for createservice - so exception will be raised for the case when DR net links are down
        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmd', return_value=(None, mockStream(['no']), None)),\
             patch('exabox.utils.node.exaBoxNode.mGetHostname', return_value='lhr118875exdd002.oraclecloud.internal'),\
             patch('exabox.ovm.clunetworkdetect.ebDiscoverOEDANetwork.mGetNetwork', return_value=self.net_class.SupportedX9Network.OCIEXACC_FULL_FIBER),\
             self.assertRaises(ExacloudRuntimeError):
            self.mGetClubox().mSetNetDetectError(_dom0, _previous_network_info["ERROR"][_dom0])
            print(self.mGetClubox().mGetNetworkSetupInformation("all", _dom0))
        # Below is a test for DR network when client and backup networks are half nets - but createservice is the cmd so exception is raised
        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmd', return_value=(None, mockStream(['yes']), None)),\
             patch('exabox.utils.node.exaBoxNode.mGetHostname', return_value='lhr118875exdd002.oraclecloud.internal'),\
             patch('exabox.ovm.clunetworkdetect.ebDiscoverOEDANetwork.mGetNetwork', return_value=self.net_class.SupportedX9Network.OCIEXACC_BASE_HALF_FIBER),\
             self.assertRaises(ExacloudRuntimeError):
            _previous_network_info = self.mGetClubox().mGetNetworkSetupInformation("all", _dom0)
            print(_previous_network_info)
        # Below flow is for createservice - when DR net links are up
        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmd', return_value=(None, mockStream(['yes']), None)),\
             patch('exabox.utils.node.exaBoxNode.mGetHostname', return_value='lhr118875exdd002.oraclecloud.internal'),\
             patch('exabox.ovm.clunetworkdetect.ebDiscoverOEDANetwork.mGetNetwork', return_value=self.net_class.SupportedX9Network.OCIEXACC_FULL_FIBER):
            self.mGetClubox().mSetNetDetectError(_dom0, _previous_network_info["ERROR"][_dom0])
            print(self.mGetClubox().mGetNetworkSetupInformation("all", _dom0))
        self.mGetClubox().mSetDRNetPresent(False)

if __name__ == '__main__':
    unittest.main()
