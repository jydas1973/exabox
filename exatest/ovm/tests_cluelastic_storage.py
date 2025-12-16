#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_cluelastic_storage.py /main/1 2021/12/14 22:51:58 aypaul Exp $
#
# tests_cluelastic_storage.py
#
# Copyright (c) 2021, Oracle and/or its affiliates.
#
#    NAME
#      tests_cluelastic_storage.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      12/06/21 - Creation
#
import json
import unittest
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo
from exabox.ovm.cluelastic import *
import warnings

RESHAPE_CONF = {'ADD_COMPUTES': ({'dom0': {'hostname': 'iad103716exdd017.iad103716exd.adminiad1.oraclevcn.com', 'rack_num': 1, 'uloc': '17', 'priv1': {'fqdn': 'iad103716exdd017-priv1.iad103716exd.adminiad1.oraclevcn.com', 'ipaddr': '192.168.132.4'}, 'priv2': {'fqdn': 'iad103716exdd017-priv2.iad103716exd.adminiad1.oraclevcn.com', 'ipaddr': '192.168.132.5'}, 'admin': {'fqdn': 'iad103716exdd017.iad103716exd.adminiad1.oraclevcn.com', 'gateway': '10.0.7.129', 'ipaddr': '10.0.7.146', 'netmask': '255.255.255.128'}, 'ilom': {'fqdn': 'iad103716exdd017lo.iad103716exd.adminiad1.oraclevcn.com', 'gateway': '10.0.7.129', 'ipaddr': '10.0.7.164', 'netmask': '255.255.255.128'}}, 'domU': {'hostname': 'iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com', 'priv1': {'fqdn': 'iad103716exddu1701-stre0.iad103716exd.adminiad1.oraclevcn.com', 'ipaddr': '100.106.123.16'}, 'priv2': {'fqdn': 'iad103716exddu1701-stre1.iad103716exd.adminiad1.oraclevcn.com', 'ipaddr': '100.106.123.17'}, 'admin': {'fqdn': 'iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com'}, 'client': {'fqdn': 'iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com', 'gateway': '10.0.0.1', 'ipaddr': '10.0.0.84', 'mac': '00:10:C9:C8:D4:CA', 'natdomain': 'iad103716exd.adminiad1.oraclevcn.com', 'nathostname': 'iad103716exddu1701', 'natip': '10.0.7.191', 'natnetmask': '255.255.255.128', 'netmask': '255.255.224.0', 'slaves': 'eth1 eth2', 'vlantag': None}, 'backup': {'fqdn': 'iad103716x8mcompexpn17b.backupsubnet.devx8melastic.oraclevcn.com', 'gateway': '10.0.32.1', 'ipaddr': '10.0.32.35', 'mac': '00:00:17:00:52:1A', 'netmask': '255.255.224.0', 'slaves': 'eth1 eth2', 'vlantag': '1'}, 'interconnect1': {'fqdn': 'iad103716exddu1701-clre0.iad103716exd.adminiad1.oraclevcn.com', 'ipaddr': '100.107.181.16'}, 'interconnect2': {'fqdn': 'iad103716exddu1701-clre1.iad103716exd.adminiad1.oraclevcn.com', 'ipaddr': '100.107.181.17'}, 'vip': {'fqdn': 'iad103716exddu1701-vip.clientsubnet.devx8melastic.oraclevcn.com', 'ipaddr': '10.0.0.90'}}},), 'DELETE_COMPUTES': (), 'ADD_CELLS': ({'hostname': 'iad103712exdcl07.iad103712exd.adminiad1.oraclevcn.com', 'rack_num': 1, 'uloc': 6, 'priv1': {'fqdn': 'iad103712exdcl07-priv1.iad103712exd.adminiad1.oraclevcn.com', 'ipaddr': '100.106.30.24'}, 'priv2': {'fqdn': 'iad103712exdcl07-priv2.iad103712exd.adminiad1.oraclevcn.com', 'ipaddr': '100.106.30.25'}, 'admin': {'fqdn': 'iad103712exdcl07.iad103712exd.adminiad1.oraclevcn.com', 'gateway': '10.0.4.129', 'ipaddr': '10.0.4.136', 'netmask': '255.255.255.128'}, 'ilom': {'fqdn': 'iad103712exdcl07lo.iad103712exd.adminiad1.oraclevcn.com', 'gateway': '10.0.4.129', 'ipaddr': '10.0.4.151', 'netmask': '255.255.255.128'}},), 'DELETE_CELLS': ()}

class testOptions(object): pass

class ebTestCluElasticStorage(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestCluElasticStorage, self).setUpClass(aGenerateDatabase = True, isElasticOperation="add_storage")
        warnings.filterwarnings("ignore")

    def test_extractAddedCells(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on Cluelastic.extractAddedCells")
        fullOptions = testOptions()

        _add_storage_payload = self.mGetClubox().mGetArgsOptions().jsonconf
        _extracted_info_tuple = extractAddedCells(_add_storage_payload)
        for _entry in _extracted_info_tuple:
            self.assertEqual(_entry['hostname'], 'iad103712exdcl07.iad103712exd.adminiad1.oraclevcn.com')
            self.assertEqual(_entry['admin']['ipaddr'], '10.0.4.136')

        ebLogInfo("Unit test on Cluelastic.extractAddedCells successful.")

    def test_extractElasticConf(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on Cluelastic.extractElasticConf")
        fullOptions = testOptions()

        _add_storage_payload = self.mGetClubox().mGetArgsOptions().jsonconf
        _extracted_info_dict = extractElasticConf(_add_storage_payload)
        self.assertEqual(_extracted_info_dict['ADD_COMPUTES'], ())
        self.assertEqual(_extracted_info_dict['ADD_CELLS'][0]['hostname'], 'iad103712exdcl07.iad103712exd.adminiad1.oraclevcn.com')

        ebLogInfo("Unit test on Cluelastic.extractElasticConf successful.")

    def test_mUpdateRequestData(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on Cluelastic.mUpdateRequestData")
        fullOptions = testOptions()
        fullOptions.jsonmode = True
        self.mGetClubox().mSetCmd("elastic_info")

        _add_storage_payload = self.mGetClubox().mGetArgsOptions().jsonconf
        _cluelastic_obj = ebCluElastic(self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
        _cluelastic_obj.mUpdateRequestData(fullOptions, 0, "mock_data", "mock_err")

        ebLogInfo("Unit test on Cluelastic.mUpdateRequestData successful.")



if __name__ == '__main__':
    unittest.main() 