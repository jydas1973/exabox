#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/vmgi_install/cs_postginid/tests_maxDistanceUpdate.py /main/3 2023/06/27 21:28:17 jfsaldan Exp $
#
# tests_maxDistanceUpdate.py
#
# Copyright (c) 2021, 2023, Oracle and/or its affiliates.
#
#    NAME
#      tests_maxDistanceUpdate.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jfsaldan    06/23/23 - Bug 35501370 - ADB-S NEW EXADATA PROVISIONING THAT
#                           SUPPORT PMEMLOGS - ENABLE PMEMLOGS
#    joysjose    11/11/21 - Creation
#
#Unit testing code

#unit testing for max distance update
import unittest

import re
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import *
from exabox.ovm.csstep.cs_postginid import csPostGINID
import warnings

class ebTestCluControlCreateVM(ebTestClucontrol):
    @classmethod
    def setUpClass(self):
        # Call ebTestClucontrol, to specify noDB/noOEDA
        super().setUpClass(False,True)
        warnings.filterwarnings("ignore", category=ResourceWarning)

    def test_1(self):
           
        _cmds = {
            self.mGetRegexDom0(): [
                [

                    exaMockCommand("/bin/test*",aRc=0,aStdout="/bin/sed",aPersist=True),  
                    exaMockCommand("'/maxdistance/d' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("selection' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("maxdistance 16.0' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("restart chronyd$",aRc=0,aPersist=True),
                    exaMockCommand("'/maxdist/d' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("selection' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("maxdist 16' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("ntpd restart$",aRc=0,aPersist=True)

                ]
            ],
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/test*",aRc=0,aStdout="/bin/sed",aPersist=True),  
                    exaMockCommand("'/maxdistance/d' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("selection' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("maxdistance 16.0' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("restart chronyd$",aRc=0,aPersist=True),
                    exaMockCommand("'/maxdist/d' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("selection' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("maxdist 16' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("ntpd restart$",aRc=0,aPersist=True)

                ]
            ]

        }
        #Init new Args
        self.mPrepareMockCommands(_cmds)
        _testObject=csPostGINID()
        _testObject.maxDistanceUpdate(self.mGetClubox())

    def test_2(self):
           
        _cmds = {
            self.mGetRegexDom0(): [
                [

                    exaMockCommand("/bin/test*",aRc=1,aStdout="/bin/sed",aPersist=True),  
                    exaMockCommand("'/maxdistance/d' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("selection' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("maxdistance 16.0' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("restart chronyd$",aRc=0,aPersist=True),
                    exaMockCommand("'/maxdist/d' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("selection' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("maxdist 16' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("ntpd restart$",aRc=0,aPersist=True)

                ]
            ],
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/test*",aRc=1,aStdout="/bin/sed",aPersist=True),  
                    exaMockCommand("'/maxdistance/d' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("selection' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("maxdistance 16.0' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("restart chronyd$",aRc=0,aPersist=True),
                    exaMockCommand("'/maxdist/d' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("selection' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("maxdist 16' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("ntpd restart$",aRc=0,aPersist=True)

                ]
            ]

        }
        #Init new Args
        self.mPrepareMockCommands(_cmds)
        _testObject=csPostGINID()
        _testObject.maxDistanceUpdate(self.mGetClubox())
    def test_3(self):

    
        _cmds = {
            self.mGetRegexDom0(): [
                [

                    exaMockCommand("/bin/test*",aRc=0,aStdout="/bin/sed",aPersist=True),  
                    exaMockCommand("'/maxdistance/d' /etc/chrony.conf$",aRc=1,aPersist=True),
                    exaMockCommand("selection' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("maxdistance 16.0' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("restart chronyd$",aRc=0,aPersist=True),
                    exaMockCommand("'/maxdist/d' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("selection' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("maxdist 16' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("ntpd restart$",aRc=0,aPersist=True)

                ]
            ],
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/test*",aRc=0,aStdout="/bin/sed",aPersist=True),  
                    exaMockCommand("'/maxdistance/d' /etc/chrony.conf$",aRc=1,aPersist=True),
                    exaMockCommand("selection' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("maxdistance 16.0' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("restart chronyd$",aRc=0,aPersist=True),
                    exaMockCommand("'/maxdist/d' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("selection' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("maxdist 16' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("ntpd restart$",aRc=0,aPersist=True)

                ]
            ]

        }
        #Init new Args
        self.mPrepareMockCommands(_cmds)
        _testObject=csPostGINID()
        _testObject.maxDistanceUpdate(self.mGetClubox())

    def test_4(self):

    
        _cmds = {
            self.mGetRegexDom0(): [
                [

                    exaMockCommand("/bin/test*",aRc=0,aStdout="/bin/sed",aPersist=True),  
                    exaMockCommand("'/maxdistance/d' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("selection' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("maxdistance 16.0' /etc/chrony.conf$",aRc=1,aPersist=True),
                    exaMockCommand("restart chronyd$",aRc=0,aPersist=True),
                    exaMockCommand("'/maxdist/d' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("selection' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("maxdist 16' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("ntpd restart$",aRc=0,aPersist=True)

                ]
            ],
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/test*",aRc=0,aStdout="/bin/sed",aPersist=True),  
                    exaMockCommand("'/maxdistance/d' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("selection' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("maxdistance 16.0' /etc/chrony.conf$",aRc=1,aPersist=True),
                    exaMockCommand("restart chronyd$",aRc=0,aPersist=True),
                    exaMockCommand("'/maxdist/d' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("selection' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("maxdist 16' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("ntpd restart$",aRc=0,aPersist=True)

                ]
            ]

        }
        #Init new Args
        self.mPrepareMockCommands(_cmds)
        _testObject=csPostGINID()
        _testObject.maxDistanceUpdate(self.mGetClubox())
    def test_5(self):

    
        _cmds = {
            self.mGetRegexDom0(): [
                [

                    exaMockCommand("/bin/test*",aRc=0,aStdout="/bin/sed",aPersist=True),  
                    exaMockCommand("'/maxdistance/d' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("selection' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("maxdistance 16.0' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("restart chronyd$",aRc=1,aPersist=True),
                    exaMockCommand("'/maxdist/d' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("selection' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("maxdist 16' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("ntpd restart$",aRc=0,aPersist=True)
                ]
            ],
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/test*",aRc=0,aStdout="/bin/sed",aPersist=True),  
                    exaMockCommand("'/maxdistance/d' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("selection' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("maxdistance 16.0' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("restart chronyd$",aRc=1,aPersist=True),
                    exaMockCommand("'/maxdist/d' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("selection' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("maxdist 16' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("ntpd restart$",aRc=0,aPersist=True)

                ]
            ]

        }
        #Init new Args
        self.mPrepareMockCommands(_cmds)
        _testObject=csPostGINID()
        _testObject.maxDistanceUpdate(self.mGetClubox())
    def test_6(self):
        
        _cmds = {
            self.mGetRegexDom0(): [
                [

                    exaMockCommand("/bin/test*",aRc=0,aStdout="/bin/sed",aPersist=True),  
                    exaMockCommand("'/maxdistance/d' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("selection' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("maxdistance 16.0' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("restart chronyd$",aRc=0,aPersist=True),
                    exaMockCommand("'/maxdist/d' /etc/ntp.conf$",aRc=1,aPersist=True),
                    exaMockCommand("selection' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("maxdist 16' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("ntpd restart$",aRc=0,aPersist=True)

                ]
            ],
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/test*",aRc=0,aStdout="/bin/sed",aPersist=True),  
                    exaMockCommand("'/maxdistance/d' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("selection' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("maxdistance 16.0' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("restart chronyd$",aRc=0,aPersist=True),
                    exaMockCommand("'/maxdist/d' /etc/ntp.conf$",aRc=1,aPersist=True),
                    exaMockCommand("selection' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("maxdist 16' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("ntpd restart$",aRc=0,aPersist=True)
                ]
            ]

        }
        #Init new Args
        self.mPrepareMockCommands(_cmds)
        _testObject=csPostGINID()
        _testObject.maxDistanceUpdate(self.mGetClubox())

    def test_7(self):
        
        _cmds = {
            self.mGetRegexDom0(): [
                [

                    exaMockCommand("/bin/test*",aRc=0,aStdout="/bin/sed",aPersist=True),  
                    exaMockCommand("'/maxdistance/d' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("selection' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("maxdistance 16.0' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("restart chronyd$",aRc=0,aPersist=True),
                    exaMockCommand("'/maxdist/d' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("selection' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("maxdist 16' /etc/ntp.conf$",aRc=1,aPersist=True),
                    exaMockCommand("ntpd restart$",aRc=0,aPersist=True)

                ]
            ],
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/test*",aRc=0,aStdout="/bin/sed",aPersist=True),  
                    exaMockCommand("'/maxdistance/d' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("selection' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("maxdistance 16.0' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("restart chronyd$",aRc=0,aPersist=True),
                    exaMockCommand("'/maxdist/d' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("selection' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("maxdist 16' /etc/ntp.conf$",aRc=1,aPersist=True),
                    exaMockCommand("ntpd restart$",aRc=0,aPersist=True)
                ]
            ]

        }
        #Init new Args
        self.mPrepareMockCommands(_cmds)
        _testObject=csPostGINID()
        _testObject.maxDistanceUpdate(self.mGetClubox())

    def test_8(self):
        
        _cmds = {
            self.mGetRegexDom0(): [
                [

                    exaMockCommand("/bin/test*",aRc=0,aStdout="/bin/sed",aPersist=True),  
                    exaMockCommand("'/maxdistance/d' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("selection' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("maxdistance 16.0' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("restart chronyd$",aRc=0,aPersist=True),
                    exaMockCommand("'/maxdist/d' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("selection' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("maxdist 16' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("ntpd restart$",aRc=1,aPersist=True)

                ]
            ],
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/test*",aRc=0,aStdout="/bin/sed",aPersist=True),  
                    exaMockCommand("'/maxdistance/d' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("selection' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("maxdistance 16.0' /etc/chrony.conf$",aRc=0,aPersist=True),
                    exaMockCommand("restart chronyd$",aRc=0,aPersist=True),
                    exaMockCommand("'/maxdist/d' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("selection' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("maxdist 16' /etc/ntp.conf$",aRc=0,aPersist=True),
                    exaMockCommand("ntpd restart$",aRc=1,aPersist=True)
                ]
            ]

        }
        #Init new Args
        self.mPrepareMockCommands(_cmds)
        _testObject=csPostGINID()
        _testObject.maxDistanceUpdate(self.mGetClubox())


    def test_droppmemlogs_adbs_yes_drop_enabled_success(self):


        _cmds = {
                self.mGetRegexCell():
                        [
                            [
                                exaMockCommand("cellcli -e drop pmemlog all", aRc=0,  aPersist=True)
                            ]
                        ]
        }
        self.mPrepareMockCommands(_cmds)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())

        self.mGetContext().mSetConfigOption('drop_pmemlog_adbs', 'True')
        _options.jsonconf["adb_s"] = "True"

        self.assertEqual(0, self.mGetClubox().mDropPmemlogs(_options))

        _cell_list = ['scaqab10celadm01.us.oracle.com', 'scaqab10celadm02.us.oracle.com']
        self.assertEqual(0, self.mGetClubox().mDropPmemlogs(_options, _cell_list))

    def test_droppmemlogs_adbs_yes_drop_disabled(self):


        _cmds = {
                self.mGetRegexCell():
                        [
                            [
                                exaMockCommand("cellcli -e drop pmemlog all", aRc=0,  aPersist=True)
                            ]
                        ]
        }
        self.mPrepareMockCommands(_cmds)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())

        self.mGetContext().mSetConfigOption('drop_pmemlog_adbs', 'False')
        _options.jsonconf["adb_s"] = "True"

        self.assertEqual(1, self.mGetClubox().mDropPmemlogs(_options))

        _cell_list = ['scaqab10celadm01.us.oracle.com', 'scaqab10celadm02.us.oracle.com']
        self.assertEqual(1, self.mGetClubox().mDropPmemlogs(_options, _cell_list))

    def test_droppmemlogs_adbs_no(self):


        _cmds = {
                self.mGetRegexCell():
                        [
                            [
                                exaMockCommand("cellcli -e drop pmemlog all", aRc=0,  aPersist=True)
                            ]
                        ]
        }
        self.mPrepareMockCommands(_cmds)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())

        _options.jsonconf["adb_s"] = "False"

        self.assertEqual(2, self.mGetClubox().mDropPmemlogs(_options))

        _cell_list = ['scaqab10celadm01.us.oracle.com', 'scaqab10celadm02.us.oracle.com']
        self.assertEqual(2, self.mGetClubox().mDropPmemlogs(_options, _cell_list))


if __name__ == "__main__":
    unittest.main()


