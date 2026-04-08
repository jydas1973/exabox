#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/tools/ebOedacli/tests_alternative_oeda.py jesandov_bug-39039331/1 2026/03/04 13:58:23 jesandov Exp $
#
# tests_alternative_oeda.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_alternative_oeda.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    03/04/26 - Creation
#

import unittest

from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.tools.ebOedacli.ebOedacli import ebOedacli

#other exacloud imports

class ebAlternativeOeda(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()

    def test_normal_path(self):

        _realOedaPath = "/u02/stack1/admin/exacloud/oeda_sriov"
        _defaultOedaPath = "/root/oeda"

        # Set exabox.conf parameter
        _config = [
              {
                "matching_rules": {
                  "multilist": [
                      {
                        "vmboss": [
                          {
                            "dom0": "dom01"
                          },
                          {
                            "dom0": "dom02"
                          }
                        ]
                      }
                  ],
                  "createservice": [
                    {
                      "customer_network": {
                        "nodes": {
                          "client": {
                            "network_virtualization": "sriov"
                          },
                          "backup": {
                            "network_virtualization": "sriov"
                          }
                        }
                      }
                    }
                  ],
                  "vmgi_reshape": [
                    {
                      "reshaped_node_subset": {
                        "added_computes": {
                          "virtual_compute_info": {
                            "network_info": {
                              "virtualcomputenetworks": {
                                "client": {
                                  "network_virtualization": "sriov"
                                },
                                "backup": {
                                  "network_virtualization": "sriov"
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  ]
                },
                "oeda_path": _realOedaPath
              }
            ]

        self.mGetContext().mSetConfigOption('alternative_oeda', _config)

        # Set payload and cmd
        _payload = {
            "customer_network": {
                "empty_list": [],
                "empty_json": {},
                "nodes": [
                    {
                        "client": {
                            "network_virtualization": "sriov"
                        },
                        "backup": {
                            "network_virtualization": "sriov"
                        }
                    }
                ]
            }
        }

        _payloadMultiList = {
          "vmboss": [
            {
                "dom0": "dom01"
            },
            {
                "dom0": "dom02"
            }
          ]
        }

        self.mGetClubox().mGetArgsOptions().jsonconf = _payload
        self.mGetClubox().mSetCmd("createservice")

        #Execute the clucontrol function
        _oedaPath = ebOedacli.mComputeOedacliPath(self.mGetClubox())
        self.assertEqual(_oedaPath, _realOedaPath)

        # Test without jsonconf
        self.mGetClubox().mGetArgsOptions().jsonconf = None
        _oedaPath = ebOedacli.mComputeOedacliPath(self.mGetClubox())
        self.assertEqual(_oedaPath, _defaultOedaPath)

        # test list
        self.mGetClubox().mSetCmd("multilist")
        self.mGetClubox().mGetArgsOptions().jsonconf = _payloadMultiList
        _oedaPath = ebOedacli.mComputeOedacliPath(self.mGetClubox())
        self.assertEqual(_oedaPath, _realOedaPath)


if __name__ == '__main__':
    unittest.main(warnings='ignore')


# end file 
