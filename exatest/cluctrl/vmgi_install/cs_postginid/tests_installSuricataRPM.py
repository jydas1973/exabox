#!/bin/python
# 
# $Header: ecs/exacloud/exabox/exatest/cluctrl/vmgi_install/cs_postginid/tests_installSuricataRPM.py /main/2 2023/02/02 02:35:59 joysjose Exp $
#
# tests_mInstallSuricataRPM.py
#
# Copyright (c) 2022, 2023, Oracle and/or its affiliates. 
#
#    NAME
#      tests_mInstallSuricataRPM.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    joysjose    03/17/22 - unit testing for mInstallSuricataRPM function in
#                           /scratch/joysjose/view_storage/joysjose_create_Service_RPM_Support/ecs/exacloud/exabox/ovm/csstep/cs_postginid.py
#    joysjose    03/17/22 - Creation
#

import unittest

import re
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import *
from exabox.log.LogMgr import ebLogError
import warnings

cmd1 = "/bin/test -e /tmp/rpm"
cmd2 = "/bin/rm -rf /tmp/rpm"
cmd3 = "/bin/scp*"
cmd4 = "/bin/test -e /tmp/rpm/suricata_installer.tgz"
cmd5 = "/bin/test -e /bin/tar"
cmd6 = "/bin/tar -xzf /tmp/rpm/suricata_installer.tgz"
cmd7 = "/bin/test -e /bin/find"
cmd8 = "/bin/find -name install.py"
cmd9 = "/bin/test -e /bin/python3"
cmd10 = "/bin/python3*"
cmd11 = "/bin/test -e /bin/rm"
cmd12 = "/bin/test -e /usr/bin/tar"
cmd13 = "/bin/test -e /usr/bin/find"
cmd14 = "/bin/test -e /bin/mv"
cmd15 = "/bin/test -e *"
cmd16 = "/bin/mv*"

out1 = "/bin/test"
out2 = "/bin/rm"
out3 = "/bin/scp"
out4 = "/bin/test"
out5 = "/bin/test"
out6 = "/bin/tar"
out7 = "/bin/test"
out8 = "/bin/find"
out9 = "/bin/test"
out10 = "/bin/python3"
out11 = "/bin/test"
out12 = "/bin/mv"

aRcValues = [[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] , [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] , [0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0] , [0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0] ,
 [0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0] , [0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0] , [0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0] , [0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0] ,
  [0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0] , [0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0] , [0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0] , [0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0],
   [0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0], [0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0], [0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0], [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0], [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1]]

class ebTestCluControlCreateVM(ebTestClucontrol):
    @classmethod
    def setUpClass(self):
        # Call ebTestClucontrol, to specify noDB/noOEDA
        super().setUpClass(False,True)
        warnings.filterwarnings("ignore", category=ResourceWarning)

    def test_installsuricatarpm(self):
        for i in range(len(aRcValues)):
            _cmds = {
                self.mGetRegexVm(): [
                    [
                        exaMockCommand(cmd1,aRc=aRcValues[i][0],aStdout=out1,aPersist=True),  
                        exaMockCommand(cmd2,aRc=aRcValues[i][1],aStdout=out2,aPersist=True),  
                        exaMockCommand(cmd3,aRc=aRcValues[i][2],aStdout=out3,aPersist=True),  
                        exaMockCommand(cmd4,aRc=aRcValues[i][3],aStdout=out4,aPersist=True),  
                        exaMockCommand(cmd5,aRc=aRcValues[i][4],aStdout=out5,aPersist=True),  
                        exaMockCommand(cmd6,aRc=aRcValues[i][5],aStdout=out6,aPersist=True),  
                        exaMockCommand(cmd7,aRc=aRcValues[i][6],aStdout=out7,aPersist=True),  
                        exaMockCommand(cmd8,aRc=aRcValues[i][7],aStdout=out8,aPersist=True),  
                        exaMockCommand(cmd9,aRc=aRcValues[i][8],aStdout=out9,aPersist=True),  
                        exaMockCommand(cmd10,aRc=aRcValues[i][9],aStdout=out10,aPersist=True), 
                        exaMockCommand(cmd11,aRc=aRcValues[i][10],aStdout=out11,aPersist=True),  
                        exaMockCommand(cmd12,aRc=aRcValues[i][11],aStdout=out11,aPersist=True),  
                        exaMockCommand(cmd13,aRc=aRcValues[i][12],aStdout=out11,aPersist=True),  
                        exaMockCommand(cmd14,aRc=aRcValues[i][13],aStdout=out11,aPersist=True),  
                        exaMockCommand(cmd15,aRc=aRcValues[i][14],aStdout=out11,aPersist=True),  
                        exaMockCommand(cmd16,aRc=aRcValues[i][15],aStdout=out12,aPersist=True),  

                    ]
                ]

            }
            self.mPrepareMockCommands(_cmds)
            cluctrl = self.mGetClubox()
            try:
                cluctrl.mInstallSuricataRPM()
            except Exception as e:
                ebLogError(f"Exception in mInstallSuricataRPM(): {str(e)}")
                



if __name__ == "__main__":
    unittest.main()
