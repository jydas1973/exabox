#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/env_info/tests_env_info.py /main/13 2025/06/05 22:52:17 ririgoye Exp $
#
# tests_env_info.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_env_info.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ririgoye    06/03/25 - Bug 38007283 - Add unit test for CS issues with
#                           Python 3.11
#    naps        02/19/25 - Bug 37556553 - UT updation for
#                           mBaseSystemConfiguration.
#    jesandov    10/16/23 - 35729701: Support of OL7 + OL8
#    prsshukl    06/01/23 - Bug 35452228 - Resolving Unittest dif
#    gparada     05/23/23 - 35098923 Add linux version to env_info
#    gparada     02/16/23 - ADD SW_VERSION AND SERIAL_NUMBER TO ENV_INFO ENDPOINT
#    jesandov    08/12/20 - Creation
#

import unittest
import json
import os
import re
import copy

from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Error import ExacloudRuntimeError
from exabox.ovm.bmc import XMLProcessor

from unittest.mock import patch

class testOptions(object): pass

class ebTestEnvInfo(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestEnvInfo, self).setUpClass()
        self.mGetClubox(self).mGetCtx().mSetConfigOption("repository_root", self.mGetPath(self))


    def mCreateInventory(self, aNumDefault=1, aNumLatest=1):

        # Read inventory
        _inventory = None
        with open(os.path.join(self.mGetPath(), "inventory.json"), "r") as _f:
            _inventory = json.loads(_f.read())

        # Update latest and default size
        _counter = 0
        for _klone in _inventory['grid-klones']:

            if _counter >= aNumLatest:
                _klone['xmeta']['latest'] = False
            else:
                _klone['xmeta']['latest'] = True

            if _counter >= aNumDefault:
                _klone['xmeta']['default'] = False
            else:
                _klone['xmeta']['default'] = True

            _counter += 1

        # Save inventory
        _newInventory = os.path.join(self.mGetUtil().mGetOutputDir(), "inventory.json")
        with open(_newInventory, "w") as _f:
            _f.write(json.dumps(_inventory, indent=4, sort_keys=True))

        self.mGetClubox().mGetCtx().mSetConfigOption("repository_root", self.mGetUtil().mGetOutputDir())
        self.mGetClubox().mSetRepoInventory({})

    def test_001_mEnvInfo18(self):
 
        _cmds = {
            self.mGetRegexCell(): [
                [                    
                    exaMockCommand("cat /etc/oracle-release", aRc=0, aStdout="Oracle Linux Server release 8.4"),
                    exaMockCommand("/usr/local/bin/imageinfo -ver", aStdout="18.0.0.0.0.190703"),
                    exaMockCommand("/usr/sbin/dmidecode -s system-serial-number", aStdout="1711NM7810"),                    
                ]
            ],
            self.mGetRegexDom0(aSeqNo="01"): [ # scaqab10adm01.us.oracle.com
                [ 
                    exaMockCommand("test -e /opt/exacloud/clusters/shared_env_enabled"), 
                ],
                [
                    exaMockCommand("imageinfo -version", aStdout="18.0.0.0.0.190703"),
                ],
                [
                    exaMockCommand("cat /etc/oracle-release", aRc=0, aStdout="Oracle Linux Server release 8.4"),
                    exaMockCommand("/usr/local/bin/imageinfo -ver", aStdout="18.0.0.0.0.190703"),
                    exaMockCommand("/usr/sbin/dmidecode -s system-serial-number", aStdout="1711NM7810"),                    
                ]
            ],
            self.mGetRegexDom0(aSeqNo="02"): [ # scaqab10adm02.us.oracle.com
                [ 
                    exaMockCommand("test -e /opt/exacloud/clusters/shared_env_enabled"), 
                ],
                [ 
                    exaMockCommand("cat /etc/oracle-release", aRc=0, aStdout="Oracle Linux Server release 8.4"),
                    exaMockCommand("/usr/local/bin/imageinfo -ver", aStdout="18.0.0.0.0.190703"),
                    exaMockCommand("/usr/sbin/dmidecode -s system-serial-number", aStdout="1711NM7810"),                                        
                ]                
            ],
            self.mGetRegexVm(): [
                [],
                [
                    exaMockCommand("ls /u01/app", aRc=1),
                    exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':' "), aRc=0, aStdout="/u01/app/18.1.0.0/grid" ,aPersist=True),
                    exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/18.1.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="18.0.0.0.0" ,aPersist=True),
                    exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/18.1.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/18.1.0.0/grid" ,aPersist=True),
                ]
            ]
        }

        _result = {            
            "image_version": "18.0.0.0.0.190703",        
            "is_shared_env": True,
            "grids_version": ["121", "122", "181"],
            "hardware": [
                {
                    "hostname": "scaqab10adm01.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "18.0.0.0.0.190703",
                    "node_serial_number": "1711NM7810"
                },
                {
                    "hostname": "scaqab10adm02.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "18.0.0.0.0.190703",
                    "node_serial_number": "1711NM7810"
                },
                {
                    "hostname": "scaqab10celadm01.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "18.0.0.0.0.190703",
                    "node_serial_number": "1711NM7810"
                },
                {
                    "hostname": "scaqab10celadm02.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "18.0.0.0.0.190703",
                    "node_serial_number": "1711NM7810"
                },
                {
                    "hostname": "scaqab10celadm03.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "18.0.0.0.0.190703",
                    "node_serial_number": "1711NM7810"
                }                
            ]
        }
 
        #Init new Args
        self.mGetClubox().mSetUUID("exatest18")
        self.mPrepareMockCommands(_cmds)
 
        _payload = self.mGetPayload()
        self.mGetClubox().mSetOptions(_payload)

        #Execute the clucontrol function        
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mPingHost', return_value=True):
            _info = self.mGetClubox().mEnvInfo()
            self.assertEquals(_info, _result)

        # Check Gi Version from command line
        _payload.grid_version = "121"
        self.mGetClubox().mSetEnableGILatest(False)

        _giver = self.mGetClubox().mGetVersionGi()
        self.assertEquals("121", _giver)

        # Check GI Version latest
        self.mGetClubox().mSetEnableGILatest(True)

        _giver = self.mGetClubox().mGetVersionGi()
        self.assertEquals("190", _giver)

        # Check Gi Version from payload
        self.mGetClubox().mSetEnableGILatest(False)
        _payload.jsonconf['grid_version'] = "18"

        _giver = self.mGetClubox().mGetVersionGi()
        self.assertEquals("181", _giver)

        # Check Gi Required CMD
        self.mGetClubox().mSetEnableGILatest(False)
        _payload = self.mGetPayload()
        self.mGetClubox().mSetOptions(_payload)
        self.mGetClubox().mSetCmd("vmgi_install")

        with self.assertRaises(ExacloudRuntimeError):
            self.mGetClubox().mGetVersionGi()

        # Check Gi Not Required CMD
        self.mGetClubox().mSetEnableGILatest(False)
        _payload = self.mGetPayload()
        self.mGetClubox().mSetOptions(_payload)
        self.mGetClubox().mSetCmd("env_info")

        _giver = self.mGetClubox().mGetVersionGi()
        self.assertEquals("181", _giver)


    def test_002_mEnvInfo20(self):
 
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("cat /etc/oracle-release", aRc=0, aStdout="Oracle Linux Server release 8.4"),
                    exaMockCommand("/usr/local/bin/imageinfo -ver", aStdout="20.2.0.0.0.200803"),
                    exaMockCommand("/usr/sbin/dmidecode -s system-serial-number", aStdout="1711NM7810"),
                ]
            ],
            self.mGetRegexDom0(aSeqNo="01"): [ # scaqab10adm01.us.oracle.com
                [
                    exaMockCommand("cat /etc/oracle-release", aRc=0, aStdout="Oracle Linux Server release 8.4"),
                    exaMockCommand("imageinfo -version", aStdout="20.2.0.0.0.200803"),
                ],
                [
                    exaMockCommand("cat /etc/oracle-release", aRc=0, aStdout="Oracle Linux Server release 8.4"),
                    exaMockCommand("/usr/local/bin/imageinfo -ver", aStdout="20.2.0.0.0.200803"),
                    exaMockCommand("/usr/sbin/dmidecode -s system-serial-number", aStdout="1711NM7810"),
                ],
            ],
            self.mGetRegexDom0(aSeqNo="02"): [ # scaqab10adm02.us.oracle.com
                [
                    exaMockCommand("cat /etc/oracle-release", aRc=0, aStdout="Oracle Linux Server release 8.4"),
                    exaMockCommand("/usr/local/bin/imageinfo -ver", aStdout="20.2.0.0.0.200803"),
                    exaMockCommand("/usr/sbin/dmidecode -s system-serial-number", aStdout="1711NM7810"),
                ],            
            ],
            self.mGetRegexVm(): [
                [],
                [
                    exaMockCommand("ls /u01/app", aRc=1),
                    exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':' "), aRc=0, aStdout="/u01/app/18.1.0.0/grid" ,aPersist=True),
                    exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/18.1.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="18.0.0.0.0" ,aPersist=True),
                    exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/18.1.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/18.1.0.0/grid" ,aPersist=True),
                ]
            ]
        }

        _result = {
            "grids_version": ["121", "122", "181", "190"],
            "image_version": "20.2.0.0.0.200803",
            "is_shared_env": True,
            "hardware": [
                {
                    "hostname": "scaqab10adm01.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "20.2.0.0.0.200803",
                    "node_serial_number": "1711NM7810"
                },
                {
                    "hostname": "scaqab10adm02.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "20.2.0.0.0.200803",
                    "node_serial_number": "1711NM7810"
                },
                {
                    "hostname": "scaqab10celadm01.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "20.2.0.0.0.200803",
                    "node_serial_number": "1711NM7810"
                },
                {
                    "hostname": "scaqab10celadm02.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "20.2.0.0.0.200803",
                    "node_serial_number": "1711NM7810"
                },
                {
                    "hostname": "scaqab10celadm03.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "20.2.0.0.0.200803",
                    "node_serial_number": "1711NM7810"
                }                
            ]
        }
 
        #Init new Args
        self.mGetClubox().mSetUUID("exatest20")
        self.mPrepareMockCommands(_cmds)

        _payload = self.mGetPayload()
        self.mGetClubox().mSetOptions(_payload)
 
        #Execute the clucontrol function
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mPingHost', return_value=True):
            _info = self.mGetClubox().mEnvInfo()
            self.assertEquals(_info, _result)

        # Check Gi Version from command line
        _payload.grid_version = "121"
        self.mGetClubox().mSetEnableGILatest(False)
        _giver = self.mGetClubox().mGetVersionGi()
        self.assertEquals("121", _giver)

        # Check GI Version latest
        self.mGetClubox().mSetEnableGILatest(True)
        _giver = self.mGetClubox().mGetVersionGi()
        self.assertEquals("190", _giver)

        # Check Gi Version from payload
        self.mGetClubox().mSetEnableGILatest(False)
        _payload.jsonconf['grid_version'] = "19"
        _giver = self.mGetClubox().mGetVersionGi()
        self.assertEquals("190", _giver)
 
        # Check Gi Required CMD
        self.mGetClubox().mSetEnableGILatest(False)
        _payload = self.mGetPayload()
        self.mGetClubox().mSetOptions(_payload)
        self.mGetClubox().mSetCmd("vmgi_install")

        with self.assertRaises(ExacloudRuntimeError):
            self.mGetClubox().mGetVersionGi()

        # Check Gi Not Required CMD
        self.mGetClubox().mSetEnableGILatest(False)
        _payload = self.mGetPayload()
        self.mGetClubox().mSetOptions(_payload)
        self.mGetClubox().mSetCmd("env_info")

        _giver = self.mGetClubox().mGetVersionGi()
        self.assertEquals("181", _giver)

    def test_003_empty_grid(self):

        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("cat /etc/oracle-release", aRc=0, aStdout="Oracle Linux Server release 8.4"),
                    exaMockCommand("/usr/local/bin/imageinfo -ver", aStdout="20.2.0.0.0.200803"),
                    exaMockCommand("/usr/sbin/dmidecode -s system-serial-number", aStdout="1711NM7810"),
                ]
            ],
            self.mGetRegexDom0(aSeqNo="01"): [ # scaqab10adm01.us.oracle.com
                [
                    exaMockCommand("cat /etc/oracle-release", aRc=0, aStdout="Oracle Linux Server release 8.4"),
                    exaMockCommand("imageinfo -version", aStdout="18.0.0.0.0.190703"),
                ],
                [
                    exaMockCommand("cat /etc/oracle-release", aRc=0, aStdout="Oracle Linux Server release 8.4"),
                    exaMockCommand("/usr/local/bin/imageinfo -ver", aStdout="20.2.0.0.0.200803"),
                    exaMockCommand("/usr/sbin/dmidecode -s system-serial-number", aStdout="1711NM7810"),
                ],
            ],
            self.mGetRegexDom0(aSeqNo="02"): [ # scaqab10adm02.us.oracle.com
                [
                    exaMockCommand("cat /etc/oracle-release", aRc=0, aStdout="Oracle Linux Server release 8.4"),
                    exaMockCommand("/usr/local/bin/imageinfo -ver", aStdout="20.2.0.0.0.200803"),
                    exaMockCommand("/usr/sbin/dmidecode -s system-serial-number", aStdout="1711NM7810"),
                ],            
            ],            
        }

        _result = {
            "grids_version": ["121", "122", "181"],
            "image_version": "18.0.0.0.0.190703",
            "is_shared_env": True,
            "hardware": [
                {
                    "hostname": "scaqab10adm01.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "20.2.0.0.0.200803",
                    "node_serial_number": "1711NM7810"
                },
                {
                    "hostname": "scaqab10adm02.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "20.2.0.0.0.200803",
                    "node_serial_number": "1711NM7810"
                },
                {
                    "hostname": "scaqab10celadm01.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "20.2.0.0.0.200803",
                    "node_serial_number": "1711NM7810"
                },
                {
                    "hostname": "scaqab10celadm02.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "20.2.0.0.0.200803",
                    "node_serial_number": "1711NM7810"
                },
                {
                    "hostname": "scaqab10celadm03.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "20.2.0.0.0.200803",
                    "node_serial_number": "1711NM7810"
                }                
            ]
        }
 
        # Create new inventory
        self.mCreateInventory(aNumDefault=1, aNumLatest=0)
 
        #Execute the clucontrol function
        self.mPrepareMockCommands(_cmds)
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mPingHost', return_value=True):
            _info = self.mGetClubox().mEnvInfo()
            self.assertEquals(_info, _result)

        # Check GI Version latest
        self.mGetClubox().mSetUUID("exatestEmpty")
        self.mGetClubox().mSetEnableGILatest(True)

        with self.assertRaises(ExacloudRuntimeError):
            self.mGetClubox().mGetVersionGi()

    def test_004_empty_default(self):

        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("cat /etc/oracle-release", aRc=0, aStdout="Oracle Linux Server release 8.4"),
                    exaMockCommand("/usr/local/bin/imageinfo -ver", aStdout="20.2.0.0.0.200803"),
                    exaMockCommand("/usr/sbin/dmidecode -s system-serial-number", aStdout="1711NM7810"),
                ]
            ],
            self.mGetRegexDom0(aSeqNo="01"): [ # scaqab10adm01.us.oracle.com
                [
                    exaMockCommand("cat /etc/oracle-release", aRc=0, aStdout="Oracle Linux Server release 8.4"),
                    exaMockCommand("imageinfo -version", aStdout="18.0.0.0.0.190703"),
                ],
                [
                    exaMockCommand("cat /etc/oracle-release", aRc=0, aStdout="Oracle Linux Server release 8.4"),
                    exaMockCommand("/usr/local/bin/imageinfo -ver", aStdout="20.2.0.0.0.200803"),
                    exaMockCommand("/usr/sbin/dmidecode -s system-serial-number", aStdout="1711NM7810"),
                ],
            ],
            self.mGetRegexDom0(aSeqNo="02"): [ # scaqab10adm02.us.oracle.com
                [
                    exaMockCommand("cat /etc/oracle-release", aRc=0, aStdout="Oracle Linux Server release 8.4"),
                    exaMockCommand("/usr/local/bin/imageinfo -ver", aStdout="20.2.0.0.0.200803"),
                    exaMockCommand("/usr/sbin/dmidecode -s system-serial-number", aStdout="1711NM7810"),
                ],            
            ],               
            self.mGetRegexVm(): [
                [],
                [
                    exaMockCommand("ls /u01/app", aRc=1)
                ]
            ]
        }

        _result = {
            "grids_version": ["121", "122", "181"],
            "image_version": "18.0.0.0.0.190703",
            "is_shared_env": True,
            "hardware": [
                {
                    "hostname": "scaqab10adm01.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "20.2.0.0.0.200803",
                    "node_serial_number": "1711NM7810"
                },
                {
                    "hostname": "scaqab10adm02.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "20.2.0.0.0.200803",
                    "node_serial_number": "1711NM7810"
                },
                {
                    "hostname": "scaqab10celadm01.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "20.2.0.0.0.200803",
                    "node_serial_number": "1711NM7810"
                },
                {
                    "hostname": "scaqab10celadm02.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "20.2.0.0.0.200803",
                    "node_serial_number": "1711NM7810"
                },
                {
                    "hostname": "scaqab10celadm03.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "20.2.0.0.0.200803",
                    "node_serial_number": "1711NM7810"
                }                
            ]
        }
 
        # Create new inventory
        self.mCreateInventory(aNumDefault=0, aNumLatest=1)
 
        #Execute the clucontrol function
        self.mPrepareMockCommands(_cmds)
        
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mPingHost', return_value=True):
            _info = self.mGetClubox().mEnvInfo()
            self.assertEquals(_info, _result)

        # Check Gi Not Required CMD
        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mSetEnableGILatest(False)
        _payload = self.mGetPayload()
        self.mGetClubox().mSetOptions(_payload)
        self.mGetClubox().mSetCmd("env_info")

        with self.assertRaises(ExacloudRuntimeError):
            self.mGetClubox().mGetVersionGi()


    def test_004_multiple_grid_default(self):

        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("cat /etc/oracle-release", aRc=0, aStdout="Oracle Linux Server release 8.4"),
                    exaMockCommand("/usr/local/bin/imageinfo -ver", aStdout="20.2.0.0.0.200803"),
                    exaMockCommand("/usr/sbin/dmidecode -s system-serial-number", aStdout="1711NM7810"),
                ]
            ],
            self.mGetRegexDom0(aSeqNo="01"): [ # scaqab10adm01.us.oracle.com
                [
                    exaMockCommand("cat /etc/oracle-release", aRc=0, aStdout="Oracle Linux Server release 8.4"),
                    exaMockCommand("imageinfo -version", aStdout="18.0.0.0.0.190703"),
                ],
                [
                    exaMockCommand("cat /etc/oracle-release", aRc=0, aStdout="Oracle Linux Server release 8.4"),
                    exaMockCommand("/usr/local/bin/imageinfo -ver", aStdout="20.2.0.0.0.200803"),
                    exaMockCommand("/usr/sbin/dmidecode -s system-serial-number", aStdout="1711NM7810"),
                ],
            ],
            self.mGetRegexDom0(aSeqNo="02"): [ # scaqab10adm02.us.oracle.com
                [
                    exaMockCommand("cat /etc/oracle-release", aRc=0, aStdout="Oracle Linux Server release 8.4"),
                    exaMockCommand("/usr/local/bin/imageinfo -ver", aStdout="20.2.0.0.0.200803"),
                    exaMockCommand("/usr/sbin/dmidecode -s system-serial-number", aStdout="1711NM7810"),
                ],            
            ],
        }

        _result = {
            "grids_version": ["121", "122", "181"],
            "image_version": "18.0.0.0.0.190703",
            "is_shared_env": True,
            "hardware": [
                {
                    "hostname": "scaqab10adm01.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "20.2.0.0.0.200803",
                    "node_serial_number": "1711NM7810"
                },
                {
                    "hostname": "scaqab10adm02.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "20.2.0.0.0.200803",
                    "node_serial_number": "1711NM7810"
                },
                {
                    "hostname": "scaqab10celadm01.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "20.2.0.0.0.200803",
                    "node_serial_number": "1711NM7810"
                },
                {
                    "hostname": "scaqab10celadm02.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "20.2.0.0.0.200803",
                    "node_serial_number": "1711NM7810"
                },
                {
                    "hostname": "scaqab10celadm03.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "20.2.0.0.0.200803",
                    "node_serial_number": "1711NM7810"
                }                
            ]
        }
 
        #Init new Args
        self.mGetClubox().mSetUUID("exatest18")
        self.mPrepareMockCommands(_cmds)
 
        _payload = self.mGetPayload()
        self.mGetClubox().mSetOptions(_payload)

        # Create new inventory
        self.mCreateInventory(aNumDefault=2, aNumLatest=1)
 
        #Execute the clucontrol function
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mPingHost', return_value=True):
            _info = self.mGetClubox().mEnvInfo()
            self.assertEquals(_info, _result)

        # Check Gi Not Required CMD
        self.mGetClubox().mSetEnableGILatest(False)
        _payload = self.mGetPayload()
        self.mGetClubox().mSetOptions(_payload)
        self.mGetClubox().mSetCmd("env_info")

        with self.assertRaises(ExacloudRuntimeError):
            self.mGetClubox().mGetVersionGi()


    def test_004_multiple_grid_latest(self):

        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("cat /etc/oracle-release", aRc=0, aStdout="Oracle Linux Server release 8.4"),
                    exaMockCommand("/usr/local/bin/imageinfo -ver", aStdout="20.2.0.0.0.200803"),
                    exaMockCommand("/usr/sbin/dmidecode -s system-serial-number", aStdout="1711NM7810"),
                ]
            ], 
            self.mGetRegexDom0(aSeqNo="01"): [ # scaqab10adm01.us.oracle.com
                [
                    exaMockCommand("cat /etc/oracle-release", aRc=0, aStdout="Oracle Linux Server release 8.4"),
                    exaMockCommand("imageinfo -version", aStdout="18.0.0.0.0.190703"),
                ],
                [
                    exaMockCommand("cat /etc/oracle-release", aRc=0, aStdout="Oracle Linux Server release 8.4"),
                    exaMockCommand("/usr/local/bin/imageinfo -ver", aStdout="20.2.0.0.0.200803"),
                    exaMockCommand("/usr/sbin/dmidecode -s system-serial-number", aStdout="1711NM7810"),
                ],
            ],
            self.mGetRegexDom0(aSeqNo="02"): [ # scaqab10adm02.us.oracle.com
                [
                    exaMockCommand("cat /etc/oracle-release", aRc=0, aStdout="Oracle Linux Server release 8.4"),
                    exaMockCommand("/usr/local/bin/imageinfo -ver", aStdout="20.2.0.0.0.200803"),
                    exaMockCommand("/usr/sbin/dmidecode -s system-serial-number", aStdout="1711NM7810"),
                ],            
            ],   
        }

        _result = {
            "grids_version": ["121", "122", "181"],
            "image_version": "18.0.0.0.0.190703",
            "is_shared_env": True,
            "hardware": [
                {
                    "hostname": "scaqab10adm01.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "20.2.0.0.0.200803",
                    "node_serial_number": "1711NM7810"
                },
                {
                    "hostname": "scaqab10adm02.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "20.2.0.0.0.200803",
                    "node_serial_number": "1711NM7810"
                },
                {
                    "hostname": "scaqab10celadm01.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "20.2.0.0.0.200803",
                    "node_serial_number": "1711NM7810"
                },
                {
                    "hostname": "scaqab10celadm02.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "20.2.0.0.0.200803",
                    "node_serial_number": "1711NM7810"
                },
                {
                    "hostname": "scaqab10celadm03.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "20.2.0.0.0.200803",
                    "node_serial_number": "1711NM7810"
                }                
            ]
        }
 
        #Init new Args
        self.mGetClubox().mSetUUID("exatest18")
        self.mPrepareMockCommands(_cmds)
 
        _payload = self.mGetPayload()
        self.mGetClubox().mSetOptions(_payload)

        # Create new inventory
        self.mCreateInventory(aNumDefault=1, aNumLatest=2)
 
        #Execute the clucontrol function
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mPingHost', return_value=True):
            _info = self.mGetClubox().mEnvInfo()
            self.assertEquals(_info, _result)

        # Check GI Version latest
        self.mGetClubox().mSetUUID("exatestEmpty")
        self.mGetClubox().mSetEnableGILatest(True)

        with self.assertRaises(ExacloudRuntimeError):
            self.mGetClubox().mGetVersionGi()

    def test_005_different_shared_env(self):

        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("cat /etc/oracle-release", aRc=0, aStdout="Oracle Linux Server release 8.4"),
                    exaMockCommand("/usr/local/bin/imageinfo -ver", aStdout="18.0.0.0.0.190703"),
                    exaMockCommand("/usr/sbin/dmidecode -s system-serial-number", aStdout="1711NM7810"),
                ],
                [
                    exaMockCommand("cat /etc/oracle-release", aRc=0, aStdout="Oracle Linux Server release 8.4"),
                    exaMockCommand("/usr/local/bin/imageinfo -ver", aStdout="18.0.0.0.0.190703"),
                    exaMockCommand("/usr/sbin/dmidecode -s system-serial-number", aStdout="1711NM7810"),
                ]
            ],
            self.mGetRegexDom0(aSeqNo="01"): [ # scaqab10adm01.us.oracle.com
                [
                    exaMockCommand("rm /opt/exacloud/clusters/shared_env_enabled"), #dom0_0, #dom0_1
                ],
                [
                    exaMockCommand("mkdir -p /opt/exacloud/clusters"),
                    exaMockCommand("touch /opt/exacloud/clusters/shared_env_enabled"),
                    exaMockCommand("imageinfo -version", aStdout="18.0.0.0.0.190703"),
                ],
                [
                    exaMockCommand("mkdir -p /opt/exacloud/clusters"),
                    exaMockCommand("touch /opt/exacloud/clusters/shared_env_enabled"),
                    exaMockCommand("cat /etc/oracle-release", aRc=0, aStdout="Oracle Linux Server release 8.4"),
                    exaMockCommand("/usr/local/bin/imageinfo -ver", aStdout="18.0.0.0.0.190703"),
                    exaMockCommand("/usr/sbin/dmidecode -s system-serial-number", aStdout="1711NM7810"),
                ],
                [
                    exaMockCommand("mkdir -p /opt/exacloud/clusters"),
                    exaMockCommand("touch /opt/exacloud/clusters/shared_env_enabled"),
                    exaMockCommand("imageinfo -version", aStdout="18.0.0.0.0.190703"),
                ],
                [
                    exaMockCommand("mkdir -p /opt/exacloud/clusters"),
                    exaMockCommand("cat /etc/oracle-release", aRc=0, aStdout="Oracle Linux Server release 8.4"),
                    exaMockCommand("/usr/local/bin/imageinfo -ver", aStdout="18.0.0.0.0.190703"),
                    exaMockCommand("/usr/sbin/dmidecode -s system-serial-number", aStdout="1711NM7810"),
                ],
                [
                    exaMockCommand("mkdir -p /opt/exacloud/clusters"),
                    exaMockCommand("cat /etc/oracle-release", aRc=0, aStdout="Oracle Linux Server release 8.4"),
                    exaMockCommand("/usr/local/bin/imageinfo -ver", aStdout="18.0.0.0.0.190703"),
                    exaMockCommand("/usr/sbin/dmidecode -s system-serial-number", aStdout="1711NM7810"),
                ],

            ],
            self.mGetRegexDom0(aSeqNo="02"): [ # scaqab10adm02.us.oracle.com
                [
                    exaMockCommand("rm /opt/exacloud/clusters/shared_env_enabled"), #dom0_0, #dom0_1
                ],
                [
                    exaMockCommand("mkdir -p /opt/exacloud/clusters"),
                    exaMockCommand("touch /opt/exacloud/clusters/shared_env_enabled"),
                    exaMockCommand("imageinfo -version", aStdout="18.0.0.0.0.190703"),
                    exaMockCommand("/usr/local/bin/imageinfo -ver", aStdout="18.0.0.0.0.190703"),
                    exaMockCommand("/usr/sbin/dmidecode -s system-serial-number", aStdout="1711NM7810"),
                    exaMockCommand("cat /etc/oracle-release", aRc=0, aStdout="Oracle Linux Server release 8.4"),
                ],
                [
                    exaMockCommand("mkdir -p /opt/exacloud/clusters"),
                    exaMockCommand("touch /opt/exacloud/clusters/shared_env_enabled"),
                    exaMockCommand("imageinfo -version", aStdout="18.0.0.0.0.190703"),
                    exaMockCommand("/usr/local/bin/imageinfo -ver", aStdout="18.0.0.0.0.190703"),
                    exaMockCommand("/usr/sbin/dmidecode -s system-serial-number", aStdout="1711NM7810"),
                    exaMockCommand("cat /etc/oracle-release", aRc=0, aStdout="Oracle Linux Server release 8.4"),
                ],
                [
                    exaMockCommand("mkdir -p /opt/exacloud/clusters"),
                    exaMockCommand("/usr/local/bin/imageinfo -ver", aStdout="18.0.0.0.0.190703"),
                    exaMockCommand("/usr/sbin/dmidecode -s system-serial-number", aStdout="1711NM7810"),
                    exaMockCommand("cat /etc/oracle-release", aRc=0, aStdout="Oracle Linux Server release 8.4"),
                ],
            ],   
        }

        self.maxDiff = None
        _result = {            
            "image_version": "18.0.0.0.0.190703",
            "is_shared_env": True,
            "grids_version": ["121", "122", "181"],
            "hardware": [
                {
                    "hostname": "scaqab10adm01.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "18.0.0.0.0.190703",
                    "node_serial_number": "1711NM7810"
                },
                {
                    "hostname": "scaqab10adm02.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "18.0.0.0.0.190703",
                    "node_serial_number": "1711NM7810"
                },
                {
                    "hostname": "scaqab10celadm01.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "18.0.0.0.0.190703",
                    "node_serial_number": "1711NM7810"
                },
                {
                    "hostname": "scaqab10celadm02.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "18.0.0.0.0.190703",
                    "node_serial_number": "1711NM7810"
                },
                {
                    "hostname": "scaqab10celadm03.us.oracle.com",
                    "oracle-release": "Oracle Linux Server release 8.4",
                    "sw_version": "18.0.0.0.0.190703",
                    "node_serial_number": "1711NM7810"
                }                
            ]
        }

        #Init new Args
        self.mGetClubox().mSetUUID("exatest18")
        self.mPrepareMockCommands(_cmds)

        # Prepare payload
        _payloadOrig = self.mGetPayload()
        self.mGetClubox().mSetOptions(_payloadOrig)

        # Create new inventory
        self.mCreateInventory(aNumDefault=1, aNumLatest=2)

        # Change shared_env to false
        _result['is_shared_env'] = False

        _payload = self.mGetPayload()
        _payload.jsonconf['shared_env'] = False
        self.mGetClubox().mSetOptions(_payload)
        self.mGetClubox().mSetSharedEnv(None)

        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mPingHost', return_value=True):
            _info = self.mGetClubox().mEnvInfo()
            self.assertEquals(_info, _result, msg='DIFF: \r\n_info\r\n{0} \r\n_result\r\n{1}'.format(_info, _result))

        # Change shared_env to true
        _result['is_shared_env'] = True

        _payload = self.mGetPayload()
        _payload.jsonconf['shared_env'] = True
        self.mGetClubox().mSetOptions(_payload)
        self.mGetClubox().mSetSharedEnv(None)

        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mPingHost', return_value=True):
            _info = self.mGetClubox().mEnvInfo()
            self.assertEquals(_info, _result, msg='DIFF: \r\n_info\r\n{0} \r\n_result\r\n{1}'.format(_info, _result))

    def test_mBaseSystemConfiguration(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _local_options = testOptions()
        _local_options.jsonconf = {
            "rack": {
                "size": "BASE-RACK"
            }
        }

        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetExadataDom0Model', return_value="X9"),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNodeModel', return_value="X9"),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mExecuteLocal'):
            self.assertIsNone(_ebox_local.mBaseSystemConfiguration(_local_options))

        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetExadataDom0Model', return_value="X10"),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNodeModel', return_value="X10"),\
             patch('exabox.ovm.bmc.V1OedaXMLRebuilder.SavePropertiesFromTemplate'),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mExecuteLocal'):
            self.assertIsNone(_ebox_local.mBaseSystemConfiguration(_local_options))

        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetExadataDom0Model', return_value="X11"),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNodeModel', return_value="X11"),\
             patch('exabox.ovm.bmc.V1OedaXMLRebuilder.SavePropertiesFromTemplate'),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mExecuteLocal'):
            self.assertIsNone(_ebox_local.mBaseSystemConfiguration(_local_options))

    def test_find_index_of_element(self):
        # Initialize XML
        _path = 'exabox/exatest/common/resources'
        _resourcesPath = os.path.abspath(_path)
        _xmlPath = os.path.join(_resourcesPath, "sample.xml")
        _processor = XMLProcessor(_xmlPath)
        # Run XML index finder
        _tag = "customerName"
        _index = _processor.find_index_of_element(_tag)
        self.assertEqual(0, _index)

    def test_mnonBaseConfiguration(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _local_options = testOptions()
        _local_options.jsonconf = {
            "rack": {
                "size": "QUARTER"
            }
        }

        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetExadataDom0Model', return_value="X11"),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNodeModel', return_value="X11"),\
             patch('exabox.ovm.bmc.V1OedaXMLRebuilder.SavePropertiesFromTemplate'),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mExecuteLocal'):
            self.assertIsNone(_ebox_local.mBaseSystemConfiguration(_local_options))

if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end file
