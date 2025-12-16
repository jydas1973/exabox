"""

 $Header: 

 Copyright (c) 2020, 2025, Oracle and/or its affiliates.

 NAME:
      tests_cluconncheck.py - Unitest for cluconncheck.py module

 DESCRIPTION:
      Run tests for the methods of cluconncheck.py

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
       ririgoye 06/03/25 - Bug 38007283 - Add unit tests for mGetChildren
       ajayasin 01/23/22 - cluconncheck.pyUnit testing
       ajayasin 01/23/22 - new ut file for cluconncheck.py
"""

import unittest
from unittest.mock import patch, MagicMock, PropertyMock, mock_open
from random import shuffle
import warnings
from exabox.log.LogMgr import ebLogInfo
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.ovm.cluhealth import ebCluHealthCheck
from exabox.ovm.cluconncheck import ebCluConnectivityCheck, ebXmlConfig
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import *

IPSTATUS_OP = ["15: vmeth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP", "inet 10.133.45.24/21 brd 10.133.47.255 scope global vmeth0"]
FN_GET_IP_STATUS_OP = ({'10.133.45.24': ('255.255.248.0', 'vmeth0', False)},[['eth0', ['BROADCAST', 'MULTICAST', 'UP', 'LOWER_UP'], {'mtu': '1500', 'qdisc': 'noqueue', 'state': 'UP'}]])
IPROUTE_OP = ["default via 10.133.40.1 dev vmeth0  table 220", "local 127.0.0.0/8 dev lo table local proto kernel scope host src 127.0.0.1"]
CHRONY_OP = "ignoreline1\nignoreline2\nignoreline3\n^* 169.254.169.254               2   4   377     9    +61us[  +76us] +/-   20ms"

class remoteTarget():

    def __init__(self, aCheckList, aRemoteMachineId, aRemoteHost):
        self.checklist = aCheckList
        self.remote_machine_id = aRemoteMachineId
        self.remote_host = aRemoteHost
        self.remote_ip = None
        self.nettype = "mock_nettype"

class mockFileHandler():

    def __init__(self, fileoutput=None):
        self.terminal_op = fileoutput

    def read(self):
        return self.terminal_op

class eMockebCluHealthCheck():
    def __init__(self,_ebox, _options):
        self._ebox = _ebox
        self._options = _options
        self._recommend = []
        self._jsonmap = {}
        self.__loghandler = "healthcheck-conf.log"
        self.__preprov = False
        self.__defloghandler = "healthcheck.log"
    def mGetRecommend(self):
        return self._recommend
    def mGetJsonMap(self):
        return self._jsonmap
    def mGetLogHandler(self):
        return self.__loghandler
    def mGetPreProv(self):
        return self.__preprov
    def mGetDefaultLogHandler(self):
        return self.__defloghandler
    def mGetEbox(self):
        return self._ebox

class ebTestNode(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestNode, self).setUpClass()
        warnings.filterwarnings("ignore")

    def test_check_network(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluConnectivityCheck.check_network.")

        _options = self.mGetPayload()
        _ebox = self.mGetClubox()
        _health_check = eMockebCluHealthCheck(_ebox,_options)
        _conn_check = ebCluConnectivityCheck(_health_check,_options)
        _local_node = self.mGetClubox().mGetLocalNode()

        _conn_check.check_network([{ "type": "domU"}], None)
        _conn_check._thread_local.stopped_vm = ["id_1"]
        _conn_check.check_network([{ "type": "dom0", "id": "id_1"}], None)

        _conn_check._thread_local.stopped_vm = []
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mPingHost', side_effect=iter([None, True, True, True])),\
             patch('exabox.ovm.cluconncheck.exaBoxNode.mConnectTimed', side_effect=iter([Exception("mock_message"), ""])),\
             patch('exabox.ovm.cluconncheck.ebCluConnectivityCheck.check_interconnectivity'),\
             patch('exabox.ovm.cluconncheck.ebCluConnectivityCheck.check_network_addresses'),\
             patch('exabox.ovm.cluconncheck.ebCluConnectivityCheck.check_ntp'),\
             patch('exabox.ovm.cluconncheck.ebCluConnectivityCheck.check_route'),\
             patch('exabox.ovm.cluconncheck.exaBoxNode.mDisconnect'):
            _conn_check.check_network([{ "type": "dom0", "id": "id_1", "hostname": "mock_host_name"}], None)
            _conn_check.check_network([{ "type": "ilom", "id": "id_1", "hostname": "mock_host_name"}], None)
            _conn_check.check_network([{ "type": "dom0", "id": "id_1", "hostname": "mock_host_name"}], None)
            _conn_check.check_network([{ "type": "dom0", "id": "id_1", "hostname": "mock_host_name"}], None)
        ebLogInfo("Unit test on ebCluConnectivityCheck.check_network succeeded.")

    def test_check_interconnectivity(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluConnectivityCheck.check_interconnectivity.")

        _options = self.mGetPayload()
        _ebox = self.mGetClubox()
        _health_check = eMockebCluHealthCheck(_ebox,_options)
        _conn_check = ebCluConnectivityCheck(_health_check,_options)
        _local_node = self.mGetClubox().mGetLocalNode()
        _conn_check.check_interconnectivity(_local_node, { "type": "dom0", "hostname": "mockhostname", "connectable_hosts": [remoteTarget(None, None, None)]}, None, None)

        with patch('exabox.ovm.cluconncheck.ebCluConnectivityCheck.check_remote_connection', side_effect=iter(["skipped", '', "mockvalue"])):
            _conn_check.check_interconnectivity(_local_node, { "type": "dom0", "hostname": "mockhostname", "connectable_hosts": [remoteTarget("mockchecklist", "mockmachineid", "mokchostname")]}, None, None)
            _conn_check.check_interconnectivity(_local_node, { "type": "dom0", "hostname": "mockhostname", "connectable_hosts": [remoteTarget("mockchecklist", "mockmachineid", "mokchostname")]}, None, None)
            _conn_check.check_interconnectivity(_local_node, { "type": "dom0", "hostname": "mockhostname", "connectable_hosts": [remoteTarget("mockchecklist", "mockmachineid", "mokchostname")]}, None, None)

        ebLogInfo("Unit test on ebCluConnectivityCheck.check_interconnectivity succeeded.")

    def test_check_chrony(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluConnectivityCheck.check_chrony.")

        _options = self.mGetPayload()
        _ebox = self.mGetClubox()
        _health_check = eMockebCluHealthCheck(_ebox,_options)
        _conn_check = ebCluConnectivityCheck(_health_check,_options)
        _local_node = self.mGetClubox().mGetLocalNode()

        with patch('exabox.core.Node.exaBoxNode.mExecuteCmd', return_value=(None, mockFileHandler(), mockFileHandler("mock_error_message"))):
            _conn_check.check_chrony(_local_node, {"hostname": "mockhostname"})

        with patch('exabox.core.Node.exaBoxNode.mExecuteCmd', return_value=(None, mockFileHandler("mocksuccess"), mockFileHandler("mock_error_message"))),\
             patch('exabox.core.Node.exaBoxNode.mGetCmdExitStatus', return_value=99):
             _conn_check.check_chrony(_local_node, {"hostname": "mockhostname"})

        with patch('exabox.core.Node.exaBoxNode.mExecuteCmd', return_value=(None, mockFileHandler(CHRONY_OP), mockFileHandler("mock_error_message"))),\
             patch('exabox.core.Node.exaBoxNode.mGetCmdExitStatus', return_value=0):
             _conn_check.check_chrony(_local_node, {"hostname": "mockhostname"})

        ebLogInfo("Unit test on ebCluConnectivityCheck.check_chrony succeeded.")

    def test_check_route(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluConnectivityCheck.check_route.")

        _options = self.mGetPayload()
        _ebox = self.mGetClubox()
        _health_check = eMockebCluHealthCheck(_ebox,_options)
        _conn_check = ebCluConnectivityCheck(_health_check,_options)
        _ssh_node = self.mGetClubox().mGetLocalNode()

        with patch('exabox.core.Node.exaBoxNode.mExecuteCmd', return_value=(None, IPROUTE_OP, None)):
            _conn_check.check_route(_ssh_node, {"default_gateway":"255.255.255.0", "type": "dom0", "hostname": "mockhostname", "networks": [{"gateway":"255.192.248.0", "master": "eth0", "netMask": "255.255.248.0", "ipAddress":"10.133.45.24", "shortHostName": "mockhostname", "networkType": "public"}]})

        ebLogInfo("Unit test on ebCluConnectivityCheck.check_route succeeded.")

    def test_check_remote_connection(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluConnectivityCheck.check_remote_connection.")

        _options = self.mGetPayload()
        _ebox = self.mGetClubox()
        _health_check = eMockebCluHealthCheck(_ebox,_options)
        _conn_check = ebCluConnectivityCheck(_health_check,_options)
        _ssh_node = self.mGetClubox().mGetLocalNode()
        _source_type = "cell"
        _curr_host = "mocklocalhost"
        _host_ip = "10.133.45.24"
        _host_net_type = "private"
        _check_list = {"ping": True, "listen_port": [3321], "ssh": ["root"]}

        with patch('exabox.core.Node.exaBoxNode.mExecuteCmd', return_value=(None, mockFileHandler(), mockFileHandler("mock_error_message"))),\
             patch('exabox.core.Node.exaBoxNode.mGetCmdExitStatus', return_value=255):
            _conn_check.check_remote_connection(_ssh_node, _source_type, _curr_host, _host_ip, _host_net_type, _check_list, "root")

        with patch('exabox.core.Node.exaBoxNode.mExecuteCmd', return_value=(None, mockFileHandler(), mockFileHandler(None))),\
             patch('exabox.core.Node.exaBoxNode.mGetCmdExitStatus', return_value=255):
            _conn_check.check_remote_connection(_ssh_node, _source_type, _curr_host, _host_ip, _host_net_type, _check_list, "root")

        _check_list = {"listen_port": [3321], "ssh": ["root"]}
        with patch('exabox.core.Node.exaBoxNode.mExecuteCmd', return_value=(None, mockFileHandler(), mockFileHandler())),\
             patch('exabox.core.Node.exaBoxNode.mGetCmdExitStatus', return_value=255):
            _conn_check.check_remote_connection(_ssh_node, _source_type, _curr_host, _host_ip, _host_net_type, _check_list, "root")

        _check_list = {"ssh": ["root"]}
        with patch('exabox.core.Node.exaBoxNode.mExecuteCmd', return_value=(None, mockFileHandler(), mockFileHandler("@@@@@@@@@\nWarning: Permanently added 'mockhostname,152.68.218.12'\nmock error line"))),\
             patch('exabox.core.Node.exaBoxNode.mGetCmdExitStatus', return_value=255):
            _conn_check.check_remote_connection(_ssh_node, _source_type, _curr_host, _host_ip, _host_net_type, _check_list, "root")

        _check_list = {"ssh": ["opc"]}
        with patch('exabox.core.Node.exaBoxNode.mExecuteCmd', return_value=(None, mockFileHandler(), mockFileHandler("@@@@@@@@@\nWarning: Permanently added 'mockhostname,152.68.218.12'\nmock error line"))),\
             patch('exabox.core.Node.exaBoxNode.mGetCmdExitStatus', return_value=255):
            _conn_check.check_remote_connection(_ssh_node, _source_type, _curr_host, _host_ip, _host_net_type, _check_list, "opc")
        ebLogInfo("Unit test on ebCluConnectivityCheck.check_remote_connection succeeded.")

    def test_check_network_addresses(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluConnectivityCheck.check_network_addresses.")

        _options = self.mGetPayload()
        _ebox = self.mGetClubox()
        _health_check = eMockebCluHealthCheck(_ebox,_options)
        _conn_check = ebCluConnectivityCheck(_health_check,_options)
        _ssh_node = self.mGetClubox().mGetLocalNode()
        with patch('exabox.ovm.cluconncheck.ebCluConnectivityCheck.get_ip_status', return_value=FN_GET_IP_STATUS_OP):
            _conn_check.check_network_addresses(_ssh_node, {"type": "dom0", "hostname": "mockhostname", "networks": [{"ipAddress":"1.1.1.1", "shortHostName": "mockhostname", "networkType": "public"}]})
            _conn_check.check_network_addresses(_ssh_node, {"type": "dom0", "hostname": "mockhostname", "networks": [{"netMask": "255.255.250.0", "ipAddress":"10.133.45.24", "shortHostName": "mockhostname", "networkType": "public"}]})
            _conn_check.check_network_addresses(_ssh_node, {"type": "dom0", "hostname": "mockhostname", "networks": [{"master": "eth0", "netMask": "255.255.248.0", "ipAddress":"10.133.45.24", "shortHostName": "mockhostname", "networkType": "public"}]})
        ebLogInfo("Unit test on ebCluConnectivityCheck.check_network_addresses succeeded.")

    def test_get_ip_status(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluConnectivityCheck.get_ip_status.")

        _options = self.mGetPayload()
        _ebox = self.mGetClubox()
        _health_check = eMockebCluHealthCheck(_ebox,_options)
        _conn_check = ebCluConnectivityCheck(_health_check,_options)
        _ssh_node = self.mGetClubox().mGetLocalNode()
        with patch('exabox.core.Node.exaBoxNode.mExecuteCmd', return_value=(None, IPSTATUS_OP, None)):
            _info1_dict, _info2_list = _conn_check.get_ip_status(_ssh_node)
            self.assertEqual(_info1_dict['10.133.45.24'], ('255.255.248.0', 'vmeth0', True))
        ebLogInfo("Unit test on ebCluConnectivityCheck.get_ip_status succeeded.")

    @patch('exabox.ovm.cluconncheck.ebXmlConfig.mGetNetworkDict')
    def test_mGetSwitchList(self, mock1):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebxmlconfig.mGetSwitchList.")
        ebLogInfo("Unit test on ebxmlconfig.mGetSwitchList succeeded.")

        _xml_config_obj = ebXmlConfig(None)
        _switch_list = _xml_config_obj.mGetSwitchList(self.mGetClubox().mGetConfig())
        for _curr_switch_detail_dict in _switch_list:
            if _curr_switch_detail_dict["switchDescription"] == "Exadata Admin Switch":
                self.assertEqual(_curr_switch_detail_dict["network_id"], "scaqab10sw-adm0.us.oracle.com_admin")
            if _curr_switch_detail_dict["switchDescription"] == "Exadata Spine Switch":
                self.assertEqual(_curr_switch_detail_dict["network_id"], "scaqab10sw-ibs0.us.oracle.com_admin")
        ebLogInfo("Unit test on ebxmlconfig.mGetSwitchList succeeded.")

    def test_mGetChildren(self):
        ebLogInfo("Running unit test on ebxmlconfig.mGetChildren")
        # Initialize ebox
        _ebox = self.mGetClubox()
        _eboxconfig = _ebox.mGetConfig()
        # Read XML
        _xmlConfig = ebXmlConfig(_eboxconfig)
        _children = _xmlConfig.mGetConfigAllElement('machines/machine')
        # Make assertions
        for _child in _children:
            self.assertIn("id", _child.attrib, "id should be in this level of the XML")   
        ebLogInfo("Unit test on ebxmlconfig.mGetChildren succeeded.")

    def test_get_machine_list(self):
        ebLogInfo("Running unit test on ebxmlconfig.mGetMachineList")
        # Initialize ebox
        _ebox = self.mGetClubox()
        _eboxconfig = _ebox.mGetConfig()
        # Read XML
        _xmlConfig = ebXmlConfig(_eboxconfig)
        _machines = _xmlConfig.mGetMachineList(_eboxconfig)
        # Make assertions
        self.assertGreaterEqual(len(_machines), 1)
        ebLogInfo("Unit test on ebxmlconfig.mGetMachineList succeeded.")

    def test_get_cluster_list(self):
        ebLogInfo("Running unit test on ebxmlconfig.mGetClusterList")
        # Initialize ebox
        _ebox = self.mGetClubox()
        _eboxconfig = _ebox.mGetConfig()
        # Read XML
        _xmlConfig = ebXmlConfig(_eboxconfig)
        _clusters = _xmlConfig.mGetClusterList(_eboxconfig)
        # Make assertions
        self.assertGreaterEqual(len(_clusters), 1)
        ebLogInfo("Unit test on ebxmlconfig.mGetClusterList succeeded.")

    def test_ebCluConnectivityCheck_init(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _health_check = eMockebCluHealthCheck(_ebox,_options)
        _conn_check = ebCluConnectivityCheck(_health_check,_options)

    def test_ebCluConnectivityCheck_mRunConnectivityCheck(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _health_check = eMockebCluHealthCheck(_ebox,_options)
        _conn_check = ebCluConnectivityCheck(_health_check,_options)
        _conn_check.mRunConnectivityCheck()

    def test_ebCluConnectivityCheck_check_network_addresses(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("ip addr show | grep*",aRc=0, aStdout = "inet config"),
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _health_check = eMockebCluHealthCheck(_ebox,_options)
        _conn_check = ebCluConnectivityCheck(_health_check,_options)
        _ddp = _ebox.mReturnDom0DomUPair(True)
        _dom0,_domU = _ddp[0]
        _ssh_conn = exaBoxNode(self.mGetContext())
        _ssh_conn.mConnect(_dom0)
        _node = {}
        _node['type'] = 'dom0'
        _conn_check.check_network_addresses(_ssh_conn,_node)

    def test_ebCluConnectivityCheck_check_ntp(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("ntpq -pn*",aRc=0, aStdout = "inet config\ntime line\ncheck status\n"),
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _health_check = eMockebCluHealthCheck(_ebox,_options)
        _conn_check = ebCluConnectivityCheck(_health_check,_options)
        _ddp = _ebox.mReturnDom0DomUPair(True)
        _dom0,_domU = _ddp[0]
        _ssh_conn = exaBoxNode(self.mGetContext())
        _ssh_conn.mConnect(_dom0)
        _data = {}
        _data['hostname'] = "dom0" 
        _conn_check.check_ntp(_ssh_conn,_data)

    def test_ebCluConnectivityCheck_check_ntp_error(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("ntpq -pn*",aRc=0, aStderr = "error"),
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _health_check = eMockebCluHealthCheck(_ebox,_options)
        _conn_check = ebCluConnectivityCheck(_health_check,_options)
        _ddp = _ebox.mReturnDom0DomUPair(True)
        _dom0,_domU = _ddp[0]
        _ssh_conn = exaBoxNode(self.mGetContext())
        _ssh_conn.mConnect(_dom0)
        _data = {}
        _data['hostname'] = "dom0" 
        _conn_check.check_ntp(_ssh_conn,_data)


    def test_ebCluConnectivityCheck_check_ntp_cmd_not_found(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("ntpq -pn*",aRc=0, aStderr = "ntpq: command not found"),
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _health_check = eMockebCluHealthCheck(_ebox,_options)
        _conn_check = ebCluConnectivityCheck(_health_check,_options)
        _ddp = _ebox.mReturnDom0DomUPair(True)
        _dom0,_domU = _ddp[0]
        _ssh_conn = exaBoxNode(self.mGetContext())
        _ssh_conn.mConnect(_dom0)
        _data = {}
        _data['hostname'] = "dom0" 
        _conn_check.check_ntp(_ssh_conn,_data)


def suite():
    """
    This method ensures the execution in the intended order of the tests.
    """
    suite = unittest.TestSuite()
    suite.addTest(ebTestNode('test_check_network'))
    suite.addTest(ebTestNode('test_check_interconnectivity'))
    suite.addTest(ebTestNode('test_check_chrony'))
    suite.addTest(ebTestNode('test_check_route'))
    suite.addTest(ebTestNode('test_check_remote_connection'))
    suite.addTest(ebTestNode('test_check_network_addresses'))
    suite.addTest(ebTestNode('test_mGetSwitchList'))
    suite.addTest(ebTestNode('test_get_ip_status'))
    suite.addTest(ebTestNode('test_ebCluConnectivityCheck_init'))
    suite.addTest(ebTestNode('test_ebCluConnectivityCheck_mRunConnectivityCheck'))
    suite.addTest(ebTestNode('test_ebCluConnectivityCheck_check_ntp'))
    suite.addTest(ebTestNode('test_ebCluConnectivityCheck_check_ntp_error'))
    suite.addTest(ebTestNode('test_ebCluConnectivityCheck_check_ntp_cmd_not_found'))
    #suite.addTest(ebTestNode('test_ebCluConnectivityCheck_check_network_addresses'))
    #suite.addTest(ebTestNode(''))
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner(failfast=True)
    runner.run(suite())
