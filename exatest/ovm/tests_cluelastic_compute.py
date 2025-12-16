#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_cluelastic_compute.py /main/8 2025/11/27 16:55:04 pbellary Exp $
#
# tests_cluelastic.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_cluelastic.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    pbellary    11/24/25 - Enh 38685113 - EXASCALE: POST CONFIGURE EXASCALE EXACLOUD SHOULD FETCH STRE0/STE1 FROM DOM0
#    pbellary    05/26/25 - Bug 37982976 - EXACC:ATTACH SECOND CELL:SEARCHING FOR MAC NETWORK OF NON-EXISTING CLUSTER
#    pbellary    03/24/25 - Bug 37665040 - EXACC:ATTACH CELL OPERATION COMPLETED BUT IT NOT PART OF ESCLUSTER AND POOLDISKS NOT EXTENDED.
#    joysjose    06/27/23 - Addition of test_mPrepareCompute test.
#    aypaul      12/06/21 - Creation
#
import json
import unittest
import hashlib
from unittest import mock
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from unittest.mock import patch
from exabox.log.LogMgr import ebLogInfo
from exabox.ovm.csstep.exascale.exascaleutils import *
from exabox.ovm.cluelastic import *
from exabox.ovm.cluelastic import ebCluElastic
import warnings
import shutil
import uuid
import copy
import os

RESHAPE_CONF = {'ADD_COMPUTES': ({'dom0': {'hostname': 'iad103716exdd017.iad103716exd.adminiad1.oraclevcn.com', 'rack_num': 1, 'uloc': '17', 'priv1': {'fqdn': 'iad103716exdd017-priv1.iad103716exd.adminiad1.oraclevcn.com', 'ipaddr': '192.168.132.4'}, 'priv2': {'fqdn': 'iad103716exdd017-priv2.iad103716exd.adminiad1.oraclevcn.com', 'ipaddr': '192.168.132.5'}, 'admin': {'fqdn': 'iad103716exdd017.iad103716exd.adminiad1.oraclevcn.com', 'gateway': '10.0.7.129', 'ipaddr': '10.0.7.146', 'netmask': '255.255.255.128'}, 'ilom': {'fqdn': 'iad103716exdd017lo.iad103716exd.adminiad1.oraclevcn.com', 'gateway': '10.0.7.129', 'ipaddr': '10.0.7.164', 'netmask': '255.255.255.128'}}, 'domU': {'hostname': 'iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com', 'priv1': {'fqdn': 'iad103716exddu1701-stre0.iad103716exd.adminiad1.oraclevcn.com', 'ipaddr': '100.106.123.16'}, 'priv2': {'fqdn': 'iad103716exddu1701-stre1.iad103716exd.adminiad1.oraclevcn.com', 'ipaddr': '100.106.123.17'}, 'admin': {'fqdn': 'iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com'}, 'client': {'fqdn': 'iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com', 'gateway': '10.0.0.1', 'ipaddr': '10.0.0.84', 'mac': '00:10:C9:C8:D4:CA', 'natdomain': 'iad103716exd.adminiad1.oraclevcn.com', 'nathostname': 'iad103716exddu1701', 'natip': '10.0.7.191', 'natnetmask': '255.255.255.128', 'netmask': '255.255.224.0', 'slaves': 'eth1 eth2', 'vlantag': None}, 'backup': {'fqdn': 'iad103716x8mcompexpn17b.backupsubnet.devx8melastic.oraclevcn.com', 'gateway': '10.0.32.1', 'ipaddr': '10.0.32.35', 'mac': '00:00:17:00:52:1A', 'netmask': '255.255.224.0', 'slaves': 'eth1 eth2', 'vlantag': '1'}, 'interconnect1': {'fqdn': 'iad103716exddu1701-clre0.iad103716exd.adminiad1.oraclevcn.com', 'ipaddr': '100.107.181.16'}, 'interconnect2': {'fqdn': 'iad103716exddu1701-clre1.iad103716exd.adminiad1.oraclevcn.com', 'ipaddr': '100.107.181.17'}, 'vip': {'fqdn': 'iad103716exddu1701-vip.clientsubnet.devx8melastic.oraclevcn.com', 'ipaddr': '10.0.0.90'}}},), 'DELETE_COMPUTES': (), 'ADD_CELLS': ({'hostname': 'iad103712exdcl08.iad103712exd.adminiad1.oraclevcn.com', 'rack_num': 1, 'uloc': 6, 'priv1': {'fqdn': 'iad103712exdcl08-priv1.iad103712exd.adminiad1.oraclevcn.com', 'ipaddr': '100.106.30.26'}, 'priv2': {'fqdn': 'iad103712exdcl08-priv2.iad103712exd.adminiad1.oraclevcn.com', 'ipaddr': '100.106.30.27'}, 'admin': {'fqdn': 'iad103712exdcl08.iad103712exd.adminiad1.oraclevcn.com', 'gateway': '10.0.4.129', 'ipaddr': '10.0.4.137', 'netmask': '255.255.255.128'}, 'ilom': {'fqdn': 'iad103712exdcl08lo.iad103712exd.adminiad1.oraclevcn.com', 'gateway': '10.0.4.129', 'ipaddr': '10.0.4.152', 'netmask': '255.255.255.128'}},), 'DELETE_CELLS': ()}
OEDA_ADDKEY = {'cleanup':'true', 'host_type':'dom0', 'ilom_hostnames':[ 'iad103716exdd015lo', 'iad103716exdd016lo'], 'oracle_hostnames':['iad103716exdd015.iad103716exd.adminiad1.oraclevcn.com','iad103716exdd016.iad103716exd.adminiad1.oraclevcn.com']}
PREPARE_COMPUTE = {"newdom0_list":["test143260exdd003","test143260exdd004"], "rpm_to_be_installed":["suricata"]}
DELETE_CELL1 = { "reshaped_node_subset": { "added_cells": [], "removed_cells": [ { "cell_node_hostname": "scaqau11celadm09"}], "xs_cell_attach": False}}
DELETE_CELL2 = { "reshaped_node_subset": { "added_cells": [], "removed_cells": [ { "cell_node_hostname": "iad103712exdcl05"}], "xs_cell_attach": True}}


class testOptions(object): pass

class ebTestCluElasticCompute(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestCluElasticCompute, self).setUpClass(aGenerateDatabase = True, aUseOeda = True, isElasticOperation="add_compute")
        self.mGetClubox(self).mSetUt(True)
        warnings.filterwarnings("ignore")

    def test_extractNetConfs(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on Cluelastic.extractNetConfs")
        fullOptions = testOptions()

        _add_compute_payload = self.mGetClubox().mGetArgsOptions().jsonconf
        _computes = _add_compute_payload['reshaped_node_subset'].get('added_computes', ())
        for _compute in _computes:
            _dom0_network_cfg = extractNetConfs(_compute['network_info']['computenetworks'])
            self.assertEqual(_dom0_network_cfg['priv1']['fqdn'], 'iad103716exdd017-priv1.iad103716exd.adminiad1.oraclevcn.com')
            self.assertEqual(_dom0_network_cfg['admin']['gateway'], '10.0.7.129')

            _domu_network_cfg = extractNetConfs(_compute['virtual_compute_info']['network_info']['virtualcomputenetworks'])
            self.assertEqual(_domu_network_cfg['client']['fqdn'], 'iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com')
            self.assertEqual(_domu_network_cfg['interconnect1']['ipaddr'], '100.107.181.16')

        ebLogInfo("Unit test on Cluelastic.extractNetConfs successful.")

    def test_extractAddedComputes(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on Cluelastic.extractAddedComputes")
        fullOptions = testOptions()

        _add_compute_payload = self.mGetClubox().mGetArgsOptions().jsonconf
        _extracted_info_tuple = extractAddedComputes(_add_compute_payload)
        for _entry in _extracted_info_tuple:
            self.assertEqual(_entry['dom0']['hostname'],'iad103716exdd017.iad103716exd.adminiad1.oraclevcn.com')
            self.assertEqual(_entry['domU']['hostname'],'iad103716x8mcompexpn17c.clientsubnet.devx8melastic.oraclevcn.com')

        ebLogInfo("Unit test on Cluelastic.extractAddedComputes successful.")

    def test_getImageVersion(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on Cluelastic.getImageVersion")
        fullOptions = testOptions()
        _testcase_map = {0:"20.1.8.0.0.210317", 1:''}

        for _testcase_index in range(2):
            _cmds = {
            self.mGetRegexDom0():
                        [
                            [
                                exaMockCommand("/usr/local/bin/imageinfo -version", aRc=0, aStdout= _testcase_map[_testcase_index], aPersist=True)
                            ]
                        ]
                    }
            self.mPrepareMockCommands(_cmds)

            _add_compute_payload = self.mGetClubox().mGetArgsOptions().jsonconf
            _img_ver = getImageVersion("iad103716exdd016.iad103716exd.adminiad1.oraclevcn.com")
            self.assertEqual(_img_ver,_testcase_map[_testcase_index])

        ebLogInfo("Unit test on Cluelastic.getImageVersion successful.")

    def test_patchOedaXmlForElastic(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on Cluelastic.patchOedaXmlForElastic")
        fullOptions = testOptions()

        _cmds = {
            self.mGetRegexVm():
                        [
                            [
                                exaMockCommand("/usr/local/bin/imageinfo -version", aRc=0, aStdout= "20.1.8.0.0.210317", aPersist=True)
                            ]
                        ],
            self.mGetRegexLocal():
                        [
                            [
                                exaMockCommand("/bin/sed *", aRc=0, aStdout="" ,aPersist=True),
                                exaMockCommand("/bin/cp *", aRc=0, aStdout="" ,aPersist=True),
                            ]
                        ]
        }
        self.mPrepareMockCommands(_cmds)

        _existing_dom0_domu_pairs = [['iad103716exdd015.iad103716exd.adminiad1.oraclevcn.com', 'iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com'],\
        ['iad103716exdd016.iad103716exd.adminiad1.oraclevcn.com', 'iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com']]
        _existing_cell_names = ['iad103712exdcl04.iad103712exd.adminiad1.oraclevcn.com', 'iad103712exdcl05.iad103712exd.adminiad1.oraclevcn.com', \
        'iad103712exdcl06.iad103712exd.adminiad1.oraclevcn.com', 'iad103712exdcl07.iad103712exd.adminiad1.oraclevcn.com']
        _cell_power = "4"
        _cluster_name = "c6-d89"
        _new_xml = "/tmp/{}.xml".format(uuid.uuid1())
        shutil.copyfile(self.mGetClubox().mGetConfigPath(), _new_xml)
        _oedacli_bin = os.path.join(self.mGetClubox().mGetOedaPath(), 'oedacli')
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", "19.0.0.0.0", "/u01/app/grid")):
            patchOedaXmlForElastic(RESHAPE_CONF, _existing_dom0_domu_pairs, _existing_cell_names, _cell_power,\
            _cluster_name, False, _new_xml, _oedacli_bin, False, self.mGetClubox())

        ebLogInfo("Unit test on Cluelastic.patchOedaXmlForElastic successful.")

    def test_mSaveCurrentXMLConfiguration(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on Cluelastic.mSaveCurrentXMLConfiguration")
        fullOptions = testOptions()
        self.mGetClubox().mSetCmd("elastic_info")
        _add_compute_payload = self.mGetClubox().mGetArgsOptions().jsonconf
        _cluelastic_obj = ebCluElastic(self.mGetClubox(), self.mGetClubox().mGetArgsOptions())

        _xml_save_dir = os.getcwd() + '/' + 'clusters/' + self.mGetClubox().mGetKey() + '/config'
        if not os.path.exists(_xml_save_dir):
            os.makedirs(_xml_save_dir)
        ebLogInfo(f"ConfigPath: {self.mGetClubox().mGetConfigPath()}")
        _cluelastic_obj.mSaveCurrentXMLConfiguration(self.mGetClubox().mGetConfigPath())
        ebLogInfo(f"PatchConfig: {self.mGetClubox().mGetPatchConfig()}")
        self.assertEqual(os.path.exists(self.mGetClubox().mGetPatchConfig()), True)
        self.assertEqual(hashlib.md5(open(self.mGetClubox().mGetConfigPath(),"rb").read()).hexdigest(), \
        hashlib.md5(open(self.mGetClubox().mGetPatchConfig(), "rb").read()).hexdigest())

        ebLogInfo("Unit test on Cluelastic.mSaveCurrentXMLConfiguration successful.")

    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mPatchStorageInterconnctIps')
    def test_mPatchXMLForElastic(self, mock_mPatchStr):
        ebLogInfo("")
        ebLogInfo("Running unit test on Cluelastic.mPatchXMLForElastic")
        fullOptions = testOptions()
        self.mGetClubox().mSetCmd("elastic_info")

        _cmds = {
            self.mGetRegexVm():
                        [
                            [
                                exaMockCommand("/usr/local/bin/imageinfo -version", aRc=0, aStdout= "20.1.8.0.0.210317", aPersist=True)
                            ]
                        ],
            self.mGetRegexLocal():
                        [
                            [
                                exaMockCommand("/bin/sed *", aRc=0, aStdout="" ,aPersist=True),
                                exaMockCommand("/bin/cp *", aRc=0, aStdout="" ,aPersist=True),
                            ]
                        ]
            }
        self.mPrepareMockCommands(_cmds)
        _xml_save_dir = os.getcwd() + '/' + 'clusters/' + self.mGetClubox().mGetKey() + '/config'
        if not os.path.exists(_xml_save_dir):
            os.makedirs(_xml_save_dir)
        _cluelastic_obj = ebCluElastic(self.mGetClubox(), self.mGetClubox().mGetArgsOptions())

        self.mGetClubox().mSetPatchConfig(self.mGetClubox().mGetConfigPath())
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", "19.0.0.0.0", "/u01/app/grid")):
            _cluelastic_obj.mPatchXMLForElastic(fullOptions)
        ebLogInfo("Unit test on Cluelastic.mPatchXMLForElastic successful.")

    def test_mBuildClusterPath(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on Cluelastic.mBuildClusterPath")
        fullOptions = testOptions()
        self.mGetClubox().mSetCmd("elastic_info")

        _cluelastic_obj = ebCluElastic(self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
        self.assertEqual(_cluelastic_obj.mBuildClusterPath(self.mGetClubox().mReturnDom0DomUPair()), \
        "iad103716exdd015iad103716x8mcompexpn15ciad103716exdd016iad103716x8mcompexpn16c")
        ebLogInfo("Unit test on Cluelastic.mBuildClusterPath successful.")

    def test_mOedaAddKeyByHost_P01(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on Cluelastic.mOedaAddKeyByHost")
        fullOptions = testOptions()

        _cmds = {
                self.mGetRegexLocal():                           
                [
                     [
                         exaMockCommand("/bin/ping *", aRc=0, aStdout="" ,aPersist=True)
                     ]
                ],
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("test -e *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("sh -c *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("grep *", aRc=0, aStdout="", aPersist=True),

                    ]
                ],
            }
        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mSetCmd('oedaaddkey_host')

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _json_object = json.dumps(OEDA_ADDKEY)
        _options.jsonconf = json.loads(_json_object)

        _cluelastic_obj = ebCluElastic(self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
        _cluelastic_obj.mOedaAddKeyByHost(_options)
        ebLogInfo("Postive Unit testcase on Cluelastic.mOedaAddKeyByHost is successful.")

    def test_mOedaAddKeyByHost_N01(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on Cluelastic.mOedaAddKeyByHost")
        fullOptions = testOptions()

        _cmds = {
                self.mGetRegexLocal():                           
                [
                     [
                         exaMockCommand("/bin/ping *", aRc=-1, aStdout="" ,aPersist=True)
                     ]
                ],
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("test -e *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("sh -c *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("grep *", aRc=0, aStdout="", aPersist=True),

                    ]
                ],
            }
        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mSetCmd('oedaaddkey_host')

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _json_object = json.dumps(OEDA_ADDKEY)
        _options.jsonconf = json.loads(_json_object)

        _cluelastic_obj = ebCluElastic(self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
        try:
            _cluelastic_obj.mOedaAddKeyByHost(_options)
        except Exception as e:
            ebLogError('>>> '+str(e))

        ebLogInfo("Negative Unit testcase on Cluelastic.mOedaAddKeyByHost is successful.")
    
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mInstallSuricataRPM")
    def test_mPrepareCompute(self,mock_mInstallSuricataRPM):
        ebLogInfo("Running unit test on Cluelastic.mPrepareCompute")
        mock_mInstallSuricataRPM.side_effect = None
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _json_object = json.dumps(PREPARE_COMPUTE)
        _options.jsonconf = json.loads(_json_object)
        _elasticobj = ebCluElastic(self.mGetClubox(), self.mGetClubox().mGetArgsOptions())
        try:
            _elasticobj.mPrepareCompute(_options)
        except Exception as e:
            ebLogError(f"Exception caught:{str(e)}")

    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mPatchStorageInterconnctIps')
    def test_mDeleteCell(self, mock_mPatchStr):
        ebLogInfo("")
        ebLogInfo("Running unit test on Cluelastic.mPatchXMLForElastic")
        fullOptions = testOptions()
        self.mGetClubox().mSetCmd("elastic_info")

        _cmds = {
            self.mGetRegexVm():
                        [
                            [
                                exaMockCommand("/usr/local/bin/imageinfo -version", aRc=0, aStdout= "20.1.8.0.0.210317", aPersist=True)
                            ]
                        ],
            self.mGetRegexLocal():
                        [
                            [
                                exaMockCommand("/bin/sed *", aRc=0, aStdout="" ,aPersist=True),
                                exaMockCommand("/bin/cp *", aRc=0, aStdout="" ,aPersist=True),
                            ]
                        ]
            }
        self.mPrepareMockCommands(_cmds)
        _xml_save_dir = os.getcwd() + '/' + 'clusters/' + self.mGetClubox().mGetKey() + '/config'
        if not os.path.exists(_xml_save_dir):
            os.makedirs(_xml_save_dir)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _json_object = json.dumps(DELETE_CELL1)
        _options.jsonconf = json.loads(_json_object)

        self.mGetClubox().mSetOciExacc(True)
        _cluelastic_obj = ebCluElastic(self.mGetClubox(), _options)

        self.mGetClubox().mSetPatchConfig(self.mGetClubox().mGetConfigPath())
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", "19.0.0.0.0", "/u01/app/grid")), \
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetArgsOptions', return_value=_options):
            _cluelastic_obj.mPatchXMLForElastic(_options)
        self.mGetClubox().mSetOciExacc(False)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _json_object = json.dumps(DELETE_CELL2)
        _options.jsonconf = json.loads(_json_object)

        self.mGetClubox().mSetOciExacc(True)
        _cluelastic_obj = ebCluElastic(self.mGetClubox(), _options)

        self.mGetClubox().mSetPatchConfig(self.mGetClubox().mGetConfigPath())
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", "19.0.0.0.0", "/u01/app/grid")), \
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetArgsOptions', return_value=_options):
            _cluelastic_obj.mPatchXMLForElastic(_options)
        self.mGetClubox().mSetOciExacc(False)

        ebLogInfo("Unit test on Cluelastic.mPatchXMLForElastic successful.")
            
        

if __name__ == '__main__':
    unittest.main() 