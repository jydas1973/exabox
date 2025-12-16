#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/csstep/tests_cs_postdbinstall.py /main/2 2022/06/23 02:48:32 naps Exp $
#
# tests_cs_postdbinstall.py
#
# Copyright (c) 2021, 2022, Oracle and/or its affiliates.
#
#    NAME
#      tests_cs_postdbinstall.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    naps        06/20/22 - check es.properties file.
#    aypaul      09/15/21 - Creation
#

import unittest
import re
import itertools
from random import shuffle
from typing import Dict

from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import *
from exabox.log.LogMgr import ebLogInfo
from exabox.ovm.csstep.cs_postdbinstall import csPostDBInstall
from exabox.agent.ebJobRequest import ebJobRequest
from exabox.ovm.csstep.cs_constants import csConstants

oedaVersionOutput = """
  install.sh -cf <config.xml> -l [options]
  install.sh -cf <config.xml> -s <step #> | -r <num-num> 
  install.sh 
  ARGUMENTS:
   -l                 List all the steps that exist
   -cf                Use to specify the full path for the config file
   -s <step #>        Run only the specified step
   -r <num-num>       Run the steps one after the other as long as no errors
                      are encountered
   -u <num-num> | <step#> Undo a range of steps or a particular step
                      For a range of steps, specify the steps in reverse order
   -h                 Print usage information
   -override          Force to run undo steps related to celldisk and grid disk
   -force             Delete binaries under grid home and database home when
                      uninstalling clusterware and database software
   -delete            Delete staging area/directories
   -nocalibratecell   Create the installation summary file without running the calibrate cell command
   -noinfinicheck     Create the installation summary file without running InfiniBand verification
   -p                 Prompts for root password for each or all the nodes. This option allows
                      deployments in Exadata environments with non-default and/or different
                       root passwords on each of the nodes in the rack
   -usesu             Use SU with root account to run commands for grid/oracle users
   -sshkeys           Run deployment with root SSH Keys that are setup by setuprootssh.sh or oedacli. Must be used with "-usesu"
   -customstep        Run custom actions. Actions can be:
                           updatecellroute:  generate cellroute.ora in domUs
   -clustername       Specify the cluster name, or All. Only used with -customstep to specify
                       the cluster on which to run the custom action
   -upgradeNetworkFirmware  X7 Broadcom network card Firmware upgrade
  Version : 210511
"""
oedaVersionInfo = """  Version : 210511"""

class testOptions(object): pass

class ebTestCSPostDBInstall(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestCSPostDBInstall, self).setUpClass(True,True)
    
    def test_doExecute(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on csPostDBInstall.doExecute.")

        mockCommands = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/test -e .*es.properties", aRc=0,  aPersist=True),
                    exaMockCommand("/bin/bash install.sh -h", aStdout=oedaVersionOutput, aRc=0, aPersist=True),
                    exaMockCommand("/bin/grep Version", aStdout=oedaVersionInfo, aRc=0, aPersist=True),
                    exaMockCommand("/bin/rm -rf", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)

        dummyOptions = testOptions()
        dummyOptions.jsonconf = {"fedramp" : "Y"}
        self.mGetClubox().mDispatchCluster("version", dummyOptions)
        self.mGetClubox().mSetClusterPath("/opt/oci/exacc/exacloud/clusters")
        dummyRequest = ebJobRequest("version", {})
        self.mGetClubox().mSetRequestObj(dummyRequest)
        csPostDBInstallInstance = csPostDBInstall()
        csPostDBInstallInstance.doExecute(self.mGetClubox(), dummyOptions, list())

    def test_undoExecute(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on csPostDBInstall.undoExecute.")

        mockCommands = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/test -e .*es.properties", aRc=0,  aPersist=True),
                    exaMockCommand("/bin/bash install.sh -h", aStdout=oedaVersionOutput, aRc=0, aPersist=True),
                    exaMockCommand("/bin/grep Version", aStdout=oedaVersionInfo, aRc=0, aPersist=True),
                    exaMockCommand("/bin/rm -rf", aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexVm(): [
                [
                    exaMockCommand("cat /etc/oratab | grep", aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("cat /etc/oratab | grep", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)

        dummyOptions = testOptions()
        dummyOptions.jsonconf = None
        self.mGetClubox().mDispatchCluster("version", dummyOptions)
        self.mGetClubox().mSetClusterPath("/opt/oci/exacc/exacloud/clusters")
        dummyRequest = ebJobRequest("version", {})
        self.mGetClubox().mSetRequestObj(dummyRequest)
        csPostDBInstallInstance = csPostDBInstall()
        csPostDBInstallInstance.undoExecute(self.mGetClubox(), dummyOptions, [csConstants.OSTP_CREATE_PDB, csConstants.OSTP_APPLY_FIX, 'ESTP_POSTDB_INSTALL'])


if __name__ == '__main__':
    unittest.main() 
