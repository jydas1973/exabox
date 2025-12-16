#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/tests_healthcheck_postprov.py /main/3 2022/06/01 22:13:28 siyarlag Exp $
#
# tests_healthcheck_postprov.py
#
# Copyright (c) 2021, 2022, Oracle and/or its affiliates.
#
#    NAME
#      tests_healthcheck_postprov.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    siyarlag    05/24/22 - 34169987: GARP env set
#    jfsaldan    01/19/21 - Creation
#

import unittest
import re
import json
from exabox.log.LogMgr import ebLogInfo
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.MockCommand import exaMockCommand
from exabox.ovm.cluhealthpostprov import executeHealthPostProv, checkDriver
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext

class ebTestHealCheckPostProv(ebTestClucontrol):
    
    @classmethod
    def setUpClass(self):
        super(ebTestHealCheckPostProv, self).setUpClass(False, False)
        
        self.maxDiff = None      
        
        self._json_new_valid =  {
                                  "domU": {
                                    "/dev": {
                                      "type": "filesystem",
                                      "expected": "355",
                                      "metric": "G"
                                    },
                                    "/dev/shm": {
                                      "type": "filesystem",
                                      "expected": "709",
                                      "metric": "G"
                                    },
                                    "/run": {
                                      "type": "filesystem",
                                      "expected": "355",
                                      "metric": "G"
                                    },
                                    "/sys/fs/cgroup": {
                                      "type": "filesystem",
                                      "expected": "355",
                                      "metric": "G"
                                    },
                                    "/run/user/0": {
                                      "type": "filesystem",
                                      "expected": "71",
                                      "metric": "G"
                                    },
                                    "/acfs01": {
                                      "type": "filesystem",
                                      "expected": "800",
                                      "metric": "G"
                                    },
                                    "/": {
                                      "type": "filesystem",
                                      "expected": "50",
                                      "metric": "G"
                                    },
                                    "/u01": {
                                      "type": "filesystem",
                                      "expected": "150",
                                      "metric": "G"
                                    },
                                    "/u02": {
                                      "type": "filesystem",
                                      "expected": "1.1",
                                      "metric": "T"
                                    },
                                    "/boot": {
                                      "type": "filesystem",
                                      "expected": "488",
                                      "metric": "M"
                                    },
                                    "$GRID_HOME": {
                                      "type": "filesystem",
                                      "expected": "50",
                                      "metric": "G"
                                    },
                                    "srvctl_ORA_NET_DEEP_CHECK": {
                                      "type": "command",
                                      "command": "$GRID_HOME/bin/srvctl",
                                      "argument": "getenv nodeapps -envs ORA_NET_DEEP_CHECK -viponly",
                                      "expected": "1",
                                      "expected_return_code": "0"
                                    },
                                    "srvctl_ORA_NET_PING_RETRIES": {
                                      "type": "command",
                                      "command": "$GRID_HOME/bin/srvctl",
                                      "argument": "getenv nodeapps -envs ORA_NET_PING_RETRIES -viponly",
                                      "expected": "8",
                                      "expected_return_code": "0"
                                    },
                                    "srvctl_ORA_NET_PING_TIMEOUT": {
                                      "type": "command",
                                      "command": "$GRID_HOME/bin/srvctl",
                                      "argument": "getenv nodeapps -envs ORA_NET_PING_TIMEOUT -viponly",
                                      "expected": "300",
                                      "expected_return_code": "0"
                                    },
                                    "srvctl_ORA_VIP_GARP_AFTER": {
                                      "type": "command",
                                      "command": "$GRID_HOME/bin/srvctl",
                                      "argument": "getenv nodeapps -envs ORA_VIP_GARP_AFTER -viponly",
                                      "expected": "30",
                                      "expected_return_code": "0"
                                    },
                                    "srvctl_ORA_VIP_GARP_RETRIES": {
                                      "type": "command",
                                      "command": "$GRID_HOME/bin/srvctl",
                                      "argument": "getenv nodeapps -envs ORA_VIP_GARP_RETRIES -viponly",
                                      "expected": "3",
                                      "expected_return_code": "0"
                                    }
                                  },
                                  "dom0": {
                                    "cat_bondeth1": {
                                      "type": "command",
                                      "command": "/bin/cat",
                                      "argument": "/sys/class/net/bondeth1/mtu",
                                      "expected": "<REPLACE_0>",
                                      "expected_return_code": "0"
                                    },
                                    "cat_bondeth2": {
                                      "type": "command",
                                      "command": "/bin/cat",
                                      "argument": "/sys/class/net/bondeth2/mtu",
                                      "expected": "<REPLACE_0>",
                                      "expected_return_code": "0"
                                    }
                                  },
                                  "cell": {}
                                }
        
    # def test_fileSystemCheck(self):
    #     """
    #     This functions stresses filesystemCheck()
    #     """
    #     _u01 =  ['Filesystem                   1073741824-blocks  Used Available Capacity Mounted on\n', '/dev/mapper/VGExaDb-LVDbOra1               20G    9G       11G      46% /u01\n']
    #     _u02 =  ['Filesystem     1073741824-blocks  Used Available Capacity Mounted on\n', '/dev/xvdi                    59G   29G       28G      52% /u02\n']
    #     _cmds = {
    #         self.mGetRegexVm(): [
    #             [
    #                 exaMockCommand("/usr/bin/findmnt /u01", aRc=0),
    #                 exaMockCommand("/usr/bin/findmnt /u02", aRc=0),
    #                 exaMockCommand("/usr/bin/findmnt /tmp", aRc=1),
    #                 exaMockCommand("/usr/bin/findmnt /acfs", aRc=1),
    #                 exaMockCommand("/usr/bin/df /u02 -PBG", aStdout="".join(_u02), aStderr="some error"),
    #                 exaMockCommand("/usr/bin/df /u01 -PBG", aStdout="".join(_u01), aStderr="some error")
    #             ]
    #         ]
    #     }

    #     #Init new Args
    #     self.mPrepareMockCommands(_cmds)

    #     ebLogInfo("Test- fileSystemCheck: \n")
    #     _mandatory_fs_keys = ("metric", "expectedValue", "name")
    #     _fs_tuple = [
    #                     {
    #                         "expectedValue": "10",
    #                         "metric": "G",
    #                         "name": "/u01"
    #                     },
    #                     {
    #                         "expectedValue": "3",
    #                         "metric": "G",
    #                         "name": "/tmp"
    #                     },
    #                     {
    #                         "expectedValue": "3",
    #                         "metric": "G",
    #                         "name": "/acfs"
    #                     }
    #                 ]
    #     _list_results = []
        
        
    #     list_compare = (
    #         {'name': '/u01', 'expectedValue': '10', 'metric': 'G', 'currentValue': '20G', 'result': 'fail'},
    #         {'name': '/tmp', 'expectedValue': '3', 'metric': 'G', 'result':     'error', 'err_msg': 'Invalid mount point: /tmp'}, 
    #         {'name': '/acfs', 'expectedValue': '3', 'metric': 'G', 'result': 'error', 'err_msg': 'Invalid mount point: /acfs'}
    #     ) 
    #     for _, _domU in self.mGetClubox().mReturnDom0DomUPair():
    #         _node = exaBoxNode(get_gcontext())
    #         _node.mConnect(aHost=_domU)
    #         _list_results.append(fileSystemCheck(_node, _mandatory_fs_keys, _fs_tuple))
    #         _node.mDisconnect()
    #     self.assertEqual(_list_results, [list_compare, list_compare])
             

    def template_test_healcheck(self, aJsonConf):
        """
        Template to trigger test on healtcheck post prov endpoint
        """

        _options = self.mGetPayload()
        _ebox = self.mGetClubox()
        _u01 =  ['Filesystem                   1073741824-blocks  Used Available Capacity Mounted on\n', '/dev/mapper/VGExaDb-LVDbOra1               20G    9G       11G      46% /u01\n']
        _u02 =  ['Filesystem     1073741824-blocks  Used Available Capacity Mounted on\n', '/dev/xvdi                    59G   29G       28G      52% /u02\n']
        _root =  ['Filesystem                   1073741824-blocks  Used Available Capacity Mounted on\n', '/dev/mapper/VGExaDb-LVDbSys1               49G   12G       35G      25% /\n']
        _options.jsonconf = aJsonConf
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/usr/bin/findmnt /u01", aRc=0),
                    exaMockCommand("/usr/bin/findmnt /u02", aRc=0),
                    exaMockCommand("/usr/bin/findmnt /tmp", aRc=1),
                    exaMockCommand("/usr/bin/findmnt /acfs", aRc=1),
                    exaMockCommand("/usr/bin/df /u02 -PBG", aStdout="".join(_u02), aStderr="some error"),
                    exaMockCommand("/usr/bin/df /u01 -PBG", aStdout="".join(_u01), aStderr="some error")
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        #Additional resources goes here

        #Execute the clucontrol function
        _returned_dict = executeHealthPostProv(_ebox, _options)
        ebLogInfo(json.dumps(_returned_dict, sort_keys=True, indent=4))


    def test_ebHealthPostProv(self):
        _json_invalid =   {
                                  "domU": {
                                    "/dev": {
                                      "type": "filesystem",
                                      "expected": "355",
                                      "metric": "G"
                                    },
                                    "/dev/shm": {
                                      "type": "filesystem",
                                      "expected": "709",
                                      "metric": "G"
                                    },
                                    "/run": {
                                      "type": "filesystem",
                                      "expected": "355",
                                      "metric": "G"
                                    },
                                    "/sys/fs/cgroup": {
                                      "type": "filesystem",
                                      "expected": "355",
                                      "metric": "G"
                                    },
                                    "/run/user/0": {
                                      "type": "filesystem",
                                      "expected": "71",
                                      "metric": "G"
                                    },
                                    "/acfs01": {
                                      "type": "filesystem",
                                      "expected": "800",
                                      "metric": "G"
                                    },
                                    "/": {
                                      "type": "filesystem",
                                      "expected": "50",
                                      "metric": "G"
                                    },
                                    "/u01": {
                                      "type": "filesystem",
                                      "expected": "150",
                                      "machine": "G"
                                    },
                                    "/u02": {
                                      "type": "filesystem",
                                      "expected": "1.1",
                                      "metric": "T"
                                    },
                                    "/boot": {
                                      "type": "filesystem",
                                      "expecteeed": "488",
                                      "metric": "M"
                                    },
                                    "$GRID_HOME": {
                                      "type": "filesystem",
                                      "expected": "50",
                                      "metric": "G"
                                    },
                                    "srvctl_ORA_NET_DEEP_CHECK": {
                                      "type": "command",
                                      "command": "$GRID_HOME/bin/srvctl",
                                      "argument": "getenv nodeapps -envs ORA_NET_DEEP_CHECK -viponly",
                                      "expected": "1",
                                      "expected_return_code": "0"
                                    },
                                    "srvctl_ORA_NET_PING_RETRIES": {
                                      "type": "command",
                                      "command": "$GRID_HOME/bin/srvctl",
                                      "argument": "getenv nodeapps -envs ORA_NET_PING_RETRIES -viponly",
                                      "expected": "8",
                                      "expected_return_code": "0"
                                    },
                                    "srvctl_ORA_NET_PING_TIMEOUT": {
                                      "type": "command",
                                      "command": "$GRID_HOME/bin/srvctl",
                                      "argument": "getenv nodeapps -envs ORA_NET_PING_TIMEOUT -viponly",
                                      "expected": "300",
                                      "expected_return_code": "0"
                                    },
                                    "srvctl_ORA_VIP_GARP_AFTER": {
                                      "type": "command",
                                      "command": "$GRID_HOME/bin/srvctl",
                                      "argument": "getenv nodeapps -envs ORA_VIP_GARP_AFTER -viponly",
                                      "expected": "30",
                                      "expected_return_code": "0"
                                    },
                                    "srvctl_ORA_VIP_GARP_RETRIES": {
                                      "type": "command",
                                      "command": "$GRID_HOME/bin/srvctl",
                                      "argument": "getenv nodeapps -envs ORA_VIP_GARP_RETRIES -viponly",
                                      "expected": "3",
                                      "expected_return_code": "0"
                                    }
                                  },
                                  "dom0": {
                                    "cat_bondeth1": {
                                      "type": "command",
                                      "command": "/bin/cat",
                                      "argument": "/sys/class/net/bondeth1/mtu",
                                      "expected": "<REPLACE_0>",
                                      "expected_return_code": "0"
                                    },
                                    "cat_bondeth2": {
                                      "type": "command",
                                      "command": "/bin/cat",
                                      "argument": "/sys/class/net/bondeth2/mtu",
                                      "expected": "<REPLACE_0>",
                                      "expected_return_code": "0"
                                    }
                                  },
                                  "cell": {}
                                }
        
        _json_valid =  {
                                  "domU": {
                                    "/dev": {
                                      "type": "filesystem",
                                      "expected": "355",
                                      "metric": "G"
                                    },
                                    "/dev/shm": {
                                      "type": "filesystem",
                                      "expected": "709",
                                      "metric": "G"
                                    },
                                    "/run": {
                                      "type": "filesystem",
                                      "expected": "355",
                                      "metric": "G"
                                    },
                                    "/sys/fs/cgroup": {
                                      "type": "filesystem",
                                      "expected": "355",
                                      "metric": "G"
                                    },
                                    "/run/user/0": {
                                      "type": "filesystem",
                                      "expected": "71",
                                      "metric": "G"
                                    },
                                    "/acfs01": {
                                      "type": "filesystem",
                                      "expected": "800",
                                      "metric": "G"
                                    },
                                    "/": {
                                      "type": "filesystem",
                                      "expected": "50",
                                      "metric": "G"
                                    },
                                    "/u01": {
                                      "type": "filesystem",
                                      "expected": "150",
                                      "metric": "G"
                                    },
                                    "/u02": {
                                      "type": "filesystem",
                                      "expected": "1.1",
                                      "metric": "T"
                                    },
                                    "/boot": {
                                      "type": "filesystem",
                                      "expected": "488",
                                      "metric": "M"
                                    },
                                    "$GRID_HOME": {
                                      "type": "filesystem",
                                      "expected": "50",
                                      "metric": "G"
                                    },
                                    "srvctl_ORA_NET_DEEP_CHECK": {
                                      "type": "command",
                                      "command": "$GRID_HOME/bin/srvctl",
                                      "argument": "getenv nodeapps -envs ORA_NET_DEEP_CHECK -viponly",
                                      "expected": "1",
                                      "expected_return_code": "0"
                                    },
                                    "srvctl_ORA_NET_PING_RETRIES": {
                                      "type": "command",
                                      "command": "$GRID_HOME/bin/srvctl",
                                      "argument": "getenv nodeapps -envs ORA_NET_PING_RETRIES -viponly",
                                      "expected": "8",
                                      "expected_return_code": "0"
                                    },
                                    "srvctl_ORA_NET_PING_TIMEOUT": {
                                      "type": "command",
                                      "command": "$GRID_HOME/bin/srvctl",
                                      "argument": "getenv nodeapps -envs ORA_NET_PING_TIMEOUT -viponly",
                                      "expected": "300",
                                      "expected_return_code": "0"
                                    },
                                    "srvctl_ORA_VIP_GARP_AFTER": {
                                      "type": "command",
                                      "command": "$GRID_HOME/bin/srvctl",
                                      "argument": "getenv nodeapps -envs ORA_VIP_GARP_AFTER -viponly",
                                      "expected": "30",
                                      "expected_return_code": "0"
                                    },
                                    "srvctl_ORA_VIP_GARP_RETRIES": {
                                      "type": "command",
                                      "command": "$GRID_HOME/bin/srvctl",
                                      "argument": "getenv nodeapps -envs ORA_VIP_GARP_RETRIES -viponly",
                                      "expected": "3",
                                      "expected_return_code": "0"
                                    }
                                  },
                                  "dom0": {
                                    "cat_bondeth1": {
                                      "type": "command",
                                      "command": "/bin/cat",
                                      "argument": "/sys/class/net/bondeth1/mtu",
                                      "expected": "<REPLACE_0>",
                                      "expected_return_code": "0"
                                    },
                                    "cat_bondeth2": {
                                      "type": "command",
                                      "command": "/bin/cat",
                                      "argument": "/sys/class/net/bondeth2/mtu",
                                      "expected": "<REPLACE_0>",
                                      "expected_return_code": "0"
                                    }
                                  },
                                  "cell": {}
                                }
        
        ebLogInfo("Test- Complete ebHealthPostProv: Payload is build ok!\n")
        self.template_test_healcheck(_json_invalid)
        self.template_test_healcheck(_json_valid)
        self.template_test_healcheck({})
        
    def test_domUDriverCheck(self):
        """
        Test domUProperties check
        """
        _u01 =  ['Filesystem                   1073741824-blocks  Used Available Capacity Mounted on\n', '/dev/mapper/VGExaDb-LVDbOra1               20G    9G       11G      46% /u01\n']
        _u02 =  ['Filesystem     1073741824-blocks  Used Available Capacity Mounted on\n', '/dev/xvdi                    59G   29G       28G      52% /u02\n']
        _root =  ['Filesystem                   1073741824-blocks  Used Available Capacity Mounted on\n', '/dev/mapper/VGExaDb-LVDbSys1               49G   12G       35G      25% /\n']
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/usr/bin/findmnt /u01", aRc=0),
                    exaMockCommand("/usr/bin/findmnt /u02", aRc=0),
                    exaMockCommand("/usr/bin/findmnt /tmp", aRc=1),
                    exaMockCommand("/usr/bin/findmnt /acfs", aRc=1),
                    exaMockCommand("/usr/bin/df /u02 -PBG", aStdout="".join(_u02), aStderr="some error"),
                    exaMockCommand("/usr/bin/df /u01 -PBG", aStdout="".join(_u01), aStderr="some error")
                ]
            ]
        }
        
        _json_new_valid =  {
                                  "domU": {
                                    "/dev": {
                                      "type": "filesystem",
                                      "expected": "355",
                                      "metric": "G"
                                    },
                                    "/dev/shm": {
                                      "type": "filesystem",
                                      "expected": "709",
                                      "metric": "G"
                                    },
                                    "/run": {
                                      "type": "filesystem",
                                      "expected": "355",
                                      "metric": "G"
                                    },
                                    "/sys/fs/cgroup": {
                                      "type": "filesystem",
                                      "expected": "355",
                                      "metric": "G"
                                    },
                                    "/run/user/0": {
                                      "type": "filesystem",
                                      "expected": "71",
                                      "metric": "G"
                                    },
                                    "/acfs01": {
                                      "type": "filesystem",
                                      "expected": "800",
                                      "metric": "G"
                                    },
                                    "/": {
                                      "type": "filesystem",
                                      "expected": "50",
                                      "metric": "G"
                                    },
                                    "/u01": {
                                      "type": "filesystem",
                                      "expected": "150",
                                      "metric": "G"
                                    },
                                    "/u02": {
                                      "type": "filesystem",
                                      "expected": "1.1",
                                      "metric": "T"
                                    },
                                    "/boot": {
                                      "type": "filesystem",
                                      "expected": "488",
                                      "metric": "M"
                                    },
                                    "$GRID_HOME": {
                                      "type": "filesystem",
                                      "expected": "50",
                                      "metric": "G"
                                    },
                                    "srvctl_ORA_NET_DEEP_CHECK": {
                                      "type": "command",
                                      "command": "$GRID_HOME/bin/srvctl",
                                      "argument": "getenv nodeapps -envs ORA_NET_DEEP_CHECK -viponly",
                                      "expected": "1",
                                      "expected_return_code": "0"
                                    },
                                    "srvctl_ORA_NET_PING_RETRIES": {
                                      "type": "command",
                                      "command": "$GRID_HOME/bin/srvctl",
                                      "argument": "getenv nodeapps -envs ORA_NET_PING_RETRIES -viponly",
                                      "expected": "8",
                                      "expected_return_code": "0"
                                    },
                                    "srvctl_ORA_NET_PING_TIMEOUT": {
                                      "type": "command",
                                      "command": "$GRID_HOME/bin/srvctl",
                                      "argument": "getenv nodeapps -envs ORA_NET_PING_TIMEOUT -viponly",
                                      "expected": "300",
                                      "expected_return_code": "0"
                                    },
                                    "srvctl_ORA_VIP_GARP_AFTER": {
                                      "type": "command",
                                      "command": "$GRID_HOME/bin/srvctl",
                                      "argument": "getenv nodeapps -envs ORA_VIP_GARP_AFTER -viponly",
                                      "expected": "30",
                                      "expected_return_code": "0"
                                    },
                                    "srvctl_ORA_VIP_GARP_RETRIES": {
                                      "type": "command",
                                      "command": "$GRID_HOME/bin/srvctl",
                                      "argument": "getenv nodeapps -envs ORA_VIP_GARP_RETRIES -viponly",
                                      "expected": "3",
                                      "expected_return_code": "0"
                                    }
                                  },
                                  "dom0": {
                                    "cat_bondeth1": {
                                      "type": "command",
                                      "command": "/bin/cat",
                                      "argument": "/sys/class/net/bondeth1/mtu",
                                      "expected": "<REPLACE_0>",
                                      "expected_return_code": "0"
                                    },
                                    "cat_bondeth2": {
                                      "type": "command",
                                      "command": "/bin/cat",
                                      "argument": "/sys/class/net/bondeth2/mtu",
                                      "expected": "<REPLACE_0>",
                                      "expected_return_code": "0"
                                    }
                                  },
                                  "cell": {}
                                }
        
        #Init new Args
        self.mPrepareMockCommands(_cmds)
        ebLogInfo("Test- domUcheckdriver")
        _ebox = self.mGetClubox()
        _json = _json_new_valid
        _json["domU"]
        _dom0 = []
        _domU = []
        _ebox = self.mGetClubox()
        pairs = _ebox.mReturnDom0DomUPair()
        for pair in pairs:
            _dom0.append(pair[0])
            _domU.append(pair[1])
        checkDriver(_domU, _json["domU"],"domU")

if __name__ == "__main__":
    unittest.main()

