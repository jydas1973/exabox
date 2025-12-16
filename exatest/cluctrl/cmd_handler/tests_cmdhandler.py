#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/cmd_handler/tests_cmdhandler.py /main/6 2025/10/31 21:59:23 aararora Exp $
#
# tests_cmdhandler.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_cmdhandler.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aararora    10/31/25 - Bug 38595677: Python 3.8 compatability issue
#    prsshukl    10/10/25 - Bug 38180284 - Unittest for mHandlerValidateVolumes
#                           method
#    dekuckre    05/27/25 - Creation
#
import unittest                                                                                                                                                                                                                               
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol                                                                                                                                                                           
from exabox.log.LogMgr import ebLogInfo                                                                                                                                                                                                       
from exabox.core.MockCommand import exaMockCommand                                                                                                                                                                                            
from exabox.ovm.cluresmgr import ebCluResManager                                                                                                                                                                                              
from unittest.mock import patch, MagicMock, PropertyMock, mock_open                                                                                                                                                                           
from exabox.ovm.clucommandhandler import CommandHandler 
#from exabox.exakms.ExaKmsHistoryDB import *
import json, copy
from exabox.core.DBStore import ebGetDefaultDB
from exabox.agent.ebJobRequest import ebJobRequest
from exabox.core.Error import ebError, gSubError, ExacloudRuntimeError, gNodeElasticError 

KEY="LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0tLQpNSUlFb3dJQkFBS0NBUUVBdU1iZHNraHdEZE05cDc2dmZyQnNrdjByM09UTElBYkJ5bzByNmFxajFMczdEbkdHCmFtVUZvTlpwWGdGRkFwM2pLcU9PN0JZc09JbWpKVklDdlY3VEtEUStMRk5lQUx2MHJGaHJtWERVY3BxQUtKYjQKNXVMZHlpS2lNZzRna251OW9iNDVDbjNHV2Q3RVhadzVDK1BHNEdpVXpjbncydVhaTnhTY3NkL1FXVlV4Y3NGRApLbHpzcEFZeFpyMVNvM2wyVGFYN0RkQzRNYlF5V1NMQTg2QW03RlM1aUVKK3h5Q05WbHh6YTVEd0xnUWxjVXgwCnRiWUxaT2tPWmZkMmdZM2g5MG45bEM4aGRHSlR2TytSZWl1TnQvampBa1ZXRGRVUEJkTFlVTzZJMjUxVDlaLzEKSXN4clBqR1FYbms2WWNjOFVkam0wZHlKYTVzZWViWU8vVXIxZVFJREFRQUJBb0lCQURBZHlSbGw5NWdDRENvawpZN3JQNGxZY2kxR0lXc1RLUGFpclBtWW93MlRnSks3TUxUNkRkQVhBRDh3azlIMkw4OTNrblpFbzdQY0VFSEhsCmUwVW83aituNnhETDNNekFKU1RFR2JEcFNzbFZKazVya2dFOXpwZVdrVG9McDd1OWNWSXZJTmQwalRSVjZEaWcKTjlLNnk4MGdMcSt3Q0lKWUhFcFZtY0JRRWdkUTBMcHdoNjJYK1VFMFkxZDlSdkt1dFpGNHRwZ1cybWMydlZwTApQTzZ0MFhwZlZFbnVpVzBvbVZQODZKSVhQd3l4TUtIc09WTzhvVzR0N09xcGJ0WjEwU05lOGdDS05qaHVZcHQ4CjF0SnJNNThGc09ndWx4QUNyRjU5bzdKUENUdzV4ZFBTbWxQNTIwaHZ3UDJxWGxLY2J5RlA3THZWNXVreTFaRWgKRllJVXV5RUNnWUVBMjVkRXVQbXYxNjdRcXoxc082Mkd4V3V6endxYjZjL1FlcDBiOHEzeHRPMitzYkxTaUlvLwp0NUx3aVFIc3VHVEQ0QzV3OHUwd3ovMXVHT3d2Tno1S2RZZERzTWlkcW9rcFJoc3NvTFpJcHB2WGtnN054OFd4CmNLTlZYZGtUQTMxNGJsVVdoT1hsQjhQcGZ4VDZYUTdOS2x6OW1KYWdTR3N4NFpUOTdGU0xhZjBDZ1lFQTEybmkKRjQzR1k5K051Q1VxMU9ZVklPZDk4a2M2SzBQWFdVWjVIeS9FOFozWnBMRGlMNXJJRTZXZ2VDYzR2SkorelptTQpTUDNjOTh5blozaXF1OFRyS29tR1BBQ1R1N091ZmdTblZiTkQ3UXY0UnBLU0hqK1h2MTVaa0c0SlArVm5mN0J1CldGa3BoYlJnMDd1LzZFS0dYQWg5MmV1aCtnaEdkSHgwbDlzMDVDMENnWUVBbGl3ZUNHNWhUaHcwZ2xjd05LUFkKWGh6b3kvZlNacFVEVzBja2ZOTnVVRENpei8yZU0xaHdlTWVaamVqdURiQ0RzRVd5WXIvSk9RUjFEY0JBRGdTZwpnVDJ2RWpBd2V4YndUZ3g1ZWJNUGZqbG50SEJCVkpTalk0ZWY4dDFvUG1QSlA1TWJJbW5pTm14SnUrb0p5aWc4Ck1QT0ZUcHY4STJxRG8yVDBQbklYSWJVQ2dZQTB6UDllUnFJYVdQR2o4WGhPTnhkMnVVZGwyNCttaXpwOTU0aEkKM0t5cGpNZU1WczhhWEJZdXVxcGF5VUplOW9tZVc4VEhIM0xLU3ArOS9SWGNjS2cwQlFHaU00SUN3RWhGRzE3bwo0c2dEa3F1SW9PU3dCV1pzd2ZPeU0wYVJJdW43b29OcHBIRkpGSzJuT0o0UmtEemUwallHOUhyL2pvZTJoY3NPCmJlekpBUUtCZ0VqL3ZFaDI3QWx1Y01GRXc2aXFZc2syaG40ZUU2SkNPRVZDUFlJYkx0eDNxaFMvcDhJMmk1cFEKUHFtcjE5NTh2eGErQ0tzVkQyVkxxMUtXYnB4MFNEVkF3Q2dTS01kcEc3R2lRK0prV2pCVG9tajVRbUtMTi9JZwo2eWkwUHRsQjJuQlpIUkh4aXhxNVR6M1RZS2pPYkJlQlZXMmYySlFLQjA0SjErSm5MMCtVCi0tLS0tRU5EIFJTQSBQUklWQVRFIEtFWS0tLS0t"

class ebTestCmdHandler(ebTestClucontrol):
   
    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateDatabase=True)


    @patch("exabox.exakms.ExaKmsHistoryDB.ExaKmsHistoryDB.mPutExaKmsHistory")
    @patch("exabox.ovm.clucommandhandler.ExaOCIFactory")
    def test_mHandlerADBSInsertKey(self, mock_mPutExaKmsHistory, aMockOCIFactory):
        ebLogInfo("Running unit test on clucommandhandler.py:mHandlerADBSInsertKey")

        _cmds = {                                           
                self.mGetRegexLocal():
                [
                    [
                        exaMockCommand("/bin/rm -f *", aRc=0, aStdout="" ,aPersist=True)
                    ]
                ]
                }                                        
        self.mGetClubox().mGetArgsOptions().jsonconf['user'] = 'root'
        self.mGetClubox().mGetArgsOptions().jsonconf['privkey'] = KEY
        self.mGetClubox().mGetArgsOptions().jsonconf['vault_id'] = "vault"

        self.mPrepareMockCommands(_cmds)
        _obj = CommandHandler(self.mGetClubox())  
        _obj.mHandlerADBSInsertKey()
        ebLogInfo("Unit test on clucommandhandler.py:mHandlerADBSInsertKey successful")

    def test_mHandlerAddVmExtraSize(self):
        ebLogInfo("Running unit test on clucommandhandler.py:mHandlerAddVmExtraSize")

        _cmds = {                                           
                self.mGetRegexVm():
                [
                    [
                        exaMockCommand("/bin/test -e *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/sbin/lvs --noheading *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/sbin/vgs --noheading *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/sbin/pvs --noheading *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/bin/df --output=target *", aRc=0, aStdout="" ,aPersist=True)
                    ],
                    [
                        exaMockCommand("/bin/test -e *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/bin/df --output=target,source,fstype,size,avail --block-size=1 *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/sbin/lvs --noheading -o lv_name,lv_dm_path,vg_name,lv_size *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/sbin/vgs --noheading -o vg_name,vg_size,vg_free,vg_extent_size *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/sbin/pvs --noheading -o pv_name,vg_name,pv_size --units B *", aRc=0, aStdout="" ,aPersist=True),
                    ],
                    [
                        exaMockCommand("/bin/test -e *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/bin/df --output=target,source,fstype,size,avail --block-size=1 | /bin/grep -v 'nfs' *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/sbin/lvs --noheading -o lv_name,lv_dm_path,vg_name,lv_size --units B *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/sbin/vgs --noheading -o vg_name,vg_size,vg_free,vg_extent_size --units B*", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/sbin/pvs --noheading -o pv_name,vg_name,pv_size --units B*", aRc=0, aStdout="" ,aPersist=True),
                    ],
                    [
                        exaMockCommand("/bin/test -e *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/bin/df --output=target,source,fstype,size,avail --block-size=1 | /bin/grep -v 'nfs' *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/sbin/lvs --noheading -o lv_name,lv_dm_path,vg_name,lv_size --units B *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/sbin/vgs --noheading -o vg_name,vg_size,vg_free,vg_extent_size --units B*", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/sbin/pvs --noheading -o pv_name,vg_name,pv_size --units B*", aRc=0, aStdout="" ,aPersist=True),
                    ],
                    [
                        exaMockCommand("/bin/test -e *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/bin/df --output=target,source,fstype,size,avail --block-size=1 | /bin/grep -v 'nfs' *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/sbin/lvs --noheading -o lv_name,lv_dm_path,vg_name,lv_size --units B *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/sbin/vgs --noheading -o vg_name,vg_size,vg_free,vg_extent_size --units B*", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/sbin/pvs --noheading -o pv_name,vg_name,pv_size --units B*", aRc=0, aStdout="" ,aPersist=True),
                    ],
                ],
                }                                        
        #self.mGetClubox().mGetArgsOptions().jsonconf["routes"][0]["cidr"] = '1.2.3.4'
        #self.mGetClubox().mGetArgsOptions().jsonconf['privkey'] = KEY

        self.mPrepareMockCommands(_cmds)
        _obj = CommandHandler(self.mGetClubox())
        with self.assertRaises(AttributeError):
            _obj.mHandlerAddVmExtraSize()
           
        self.mGetClubox().mGetArgsOptions().jsonconf = json.loads('{"filesystem" : "root"}')
        with self.assertRaises(ExacloudRuntimeError):
            _obj.mHandlerAddVmExtraSize()

        self.mGetClubox().mGetArgsOptions().jsonconf = json.loads('{"filesystem" : "rootfs"}')
        with self.assertRaises(AttributeError):
            _obj.mHandlerAddVmExtraSize()
        
        self.mGetClubox().mGetArgsOptions().jsonconf = json.loads('{"extra_size" : "512"}')
        with self.assertRaises(AttributeError):
            _obj.mHandlerAddVmExtraSize()
        
        self.mGetClubox().mGetArgsOptions().jsonconf["validate_max_size"] = False
        with self.assertRaises(AttributeError):
            _obj.mHandlerAddVmExtraSize()
        
        self.mGetClubox().mGetArgsOptions().jsonconf = json.loads('{"resize_mode" : "normal"}')
        with self.assertRaises(AttributeError):
            _obj.mHandlerAddVmExtraSize()
         


    def test_mHandlerATPBackupRoutes(self):
        ebLogInfo("Running unit test on clucommandhandler.py:mHandlerATPBackupRoutes")

        _cmds = {                                           
                self.mGetRegexVm():
                [
                    [
                        exaMockCommand("/bin/test -e *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/var/opt/oracle/misc/db-route *", aRc=0, aStdout="" ,aPersist=True)
                    ]
                ],
                }                                        

        self.mPrepareMockCommands(_cmds)
        _obj = CommandHandler(self.mGetClubox())  
        try : 
            _obj.mHandlerATPBackupRoutes()
        except:
            ebLogInfo("Unit test on clucommandhandler.py:mHandlerATPBackupRoutes successful")


        self.mGetClubox().mGetArgsOptions().jsonconf = json.loads('{"routes":[{"cidr":"10.10.10.0/25"},{"cidr":"5.5.5.5/19"}]}')
        self.mGetClubox().mGetArgsOptions().jsonconf["action"] = "add"
        _obj.mHandlerATPBackupRoutes()

    def test_mHandlerAdminSwitchConnect(self):
        ebLogInfo("Running unit test on clucommandhandler.py:mHandlerAdminSwitchConnect")

        _cmds = {                                           
                self.mGetRegexVm():
                [
                    [
                        exaMockCommand("/bin/test -e *", aRc=0, aStdout="" ,aPersist=True)
                    ]
                ],
                }                                        

        self.mPrepareMockCommands(_cmds)
        _obj = CommandHandler(self.mGetClubox())  
        _obj.mHandlerAdminSwitchConnect()

    def test_mHandlerATPIPTables(self):
        ebLogInfo("Running unit test on clucommandhandler.py:mHandlerATPIPTables")

        _cmds = {                                           
                self.mGetRegexVm():
                [
                    [
                        exaMockCommand("/bin/test -e *", aRc=0, aStdout="" ,aPersist=True)
                    ]
                ],
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("/bin/scp *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/sbin/iptables -nL *", aRc=0, aStdout="" ,aPersist=True)
                    ]
                ],
                }                                        

        self.mPrepareMockCommands(_cmds)
        _obj = CommandHandler(self.mGetClubox())  
        try : 
            _obj.mHandlerATPIPTables()
        except:
            ebLogInfo("Unit test on clucommandhandler.py:test_mHandlerATPIPTables successful")

        #self.mGetClubox().mGetArgsOptions().jsonconf = json.loads('{"routes":[{"cidr":"10.10.10.0/25"},{"cidr":"5.5.5.5/19"}]}')
        self.mGetClubox().mGetArgsOptions().jsonconf = json.loads('{"rule" : "IP|CIDR@Port@in|out@Protocol"}')
        self.mGetClubox().mGetArgsOptions().jsonconf["action"] = "add"
        _obj.mHandlerATPIPTables()

    def test_mHandlerClusterDetails(self):
        ebLogInfo("Running unit test on clucommandhandler.py:mHandlerATPIPTables")

        _cmds = {                                           
                self.mGetRegexVm():
                [
                    [
                        exaMockCommand("/bin/test -e *", aRc=0, aStdout="" ,aPersist=True)
                    ]
                ],
                }                                        

        self.mPrepareMockCommands(_cmds)
        _obj = CommandHandler(self.mGetClubox())  
        _obj.mHandlerClusterDetails()


    def test_mHandlerATPIPTables(self):
        ebLogInfo("Running unit test on clucommandhandler.py:mHandlerATPIPTables")

        _cmds = {                                           
                self.mGetRegexVm():
                [
                    [
                        exaMockCommand("/bin/test -e *", aRc=0, aStdout="" ,aPersist=True)
                    ]
                ],
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("/bin/scp *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/sbin/iptables -nL *", aRc=0, aStdout="" ,aPersist=True)
                    ]
                ],
                }                                        

        self.mPrepareMockCommands(_cmds)
        _obj = CommandHandler(self.mGetClubox())  
        try : 
            _obj.mHandlerATPIPTables()
        except:
            ebLogInfo("Unit test on clucommandhandler.py:test_mHandlerATPIPTables successful")

        #self.mGetClubox().mGetArgsOptions().jsonconf = json.loads('{"routes":[{"cidr":"10.10.10.0/25"},{"cidr":"5.5.5.5/19"}]}')
        self.mGetClubox().mGetArgsOptions().jsonconf = json.loads('{"rule" : "IP|CIDR@Port@in|out@Protocol"}')
        self.mGetClubox().mGetArgsOptions().jsonconf["action"] = "add"
        _obj.mHandlerATPIPTables()


    def test_mHandlerGenIncidentFile(self):
        ebLogInfo("Running unit test on clucommandhandler.py:mHandlerATPIPTables")

        _cmds = {                                           
                self.mGetRegexVm():
                [
                    [
                        exaMockCommand("/bin/test -e *", aRc=0, aStdout="" ,aPersist=True)
                    ]
                ],
                }                                        

        self.mPrepareMockCommands(_cmds)
        _obj = CommandHandler(self.mGetClubox())  
        _obj.mHandlerGenIncidentFile()

    def test_mHandlerSnmpPasswords(self):
        fname = "mHandlerSnmpPasswords"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")

        _cmds = {                                           
                self.mGetRegexVm():
                [
                    [
                        exaMockCommand("/var/opt/oracle/ocde/rops get_creg_key *", aRc=0, aStdout="asmsnmppasswd" ,aPersist=True)
                    ]
                ],
                }                                        

        self.mGetClubox().mGetArgsOptions().dbsid = "dbsid"
        self.mPrepareMockCommands(_cmds)
        _obj = CommandHandler(self.mGetClubox())  
        _obj.mHandlerSnmpPasswords()

    def test_mHandlerJumboOper(self):
        fname = "mHandlerJumboOper"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _obj = CommandHandler(self.mGetClubox())  
        self.mGetClubox().mGetArgsOptions().jumboframes = None
        _obj.mHandlerJumboOper()
        _cmds = {                                           
                self.mGetRegexDom0(): [
                    [
                        exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/bin/test -e /sbin/ip *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/sbin/ip -oneline link show *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/bin/test -e /bin/cat *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/sys/class/net/vmbondeth0/mtu *", aRc=0, aStdout="255" ,aPersist=True),
                    ],
                    [
                        exaMockCommand("/bin/test -e *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/sbin/ip -oneline link show *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("bin/cat /sys/class/net/vmbondeth0/mtu *", aRc=0, aStdout="255" ,aPersist=True),
                    ],
                    [
                        exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="" ,aPersist=True)
                    ],
                ],
                self.mGetRegexVm(): [
                    [
                        exaMockCommand("/bin/cat /sys/class/net/bondeth0/mtu *", aRc=0, aStdout="255" ,aPersist=True),
                        exaMockCommand("/bin/cat /sys/class/net/bondeth1/mtu *", aRc=0, aStdout="255" ,aPersist=True),
                        exaMockCommand("/bin/test -e *", aRc=0, aStdout="" ,aPersist=True)
                    ],
                ],
                }                                        
        self.mPrepareMockCommands(_cmds)

        self.mGetClubox().mGetArgsOptions().jumboframes = 'state'
        _obj.mHandlerJumboOper()
        self.mGetClubox().mGetArgsOptions().jumboframes = 'stateless'
        _obj.mHandlerJumboOper()

    def test_mHandlerUpdateBlockState(self):
        fname = "mHandlerUpdateBlockState"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _obj = CommandHandler(self.mGetClubox())  
        self.mGetClubox().mGetArgsOptions().blockstate = None
        try:
            _obj.mHandlerUpdateBlockState()
        except:
            ebLogInfo("Excpetion handled for Exacloud Run time error")

        self.mGetClubox().mGetArgsOptions().blockstate = 'True'
        _obj.mHandlerUpdateBlockState()
 

    def test_mHandlerGetCellIBInfo(self):
        fname = "mHandlerGetCellIBInfo"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        self.mGetClubox().mSetEnableKVM(True)
        _obj = CommandHandler(self.mGetClubox())  
        _obj.mHandlerGetCellIBInfo()
        
        _cmds = {                                           
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("smpartition list active no-page | grep *", aRc=0, aStdout="" ,aPersist=True)
                    ]
                ],
                self.mGetRegexSwitch():
                [
                    [
                        exaMockCommand("smpartition list active *", aRc=0, aStdout="" ,aPersist=True)
                    ]
                ],
                }                                        
        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mSetEnableKVM(False)
        _obj = CommandHandler(self.mGetClubox())  
        _obj.mHandlerGetCellIBInfo()

    def test_mHandlerGetVMCoreLogs(self):
        fname = "mHandlerGetVMCoreLogs"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _obj = CommandHandler(self.mGetClubox())  
        try:
            _obj.mHandlerGetVMCoreLogs()
        except:
            ebLogInfo("Excpetion handled for Exacloud Run time error")
        self.mGetClubox().mGetArgsOptions().jsonconf = json.loads('{"vm_name" : "vmname"}')
        _cmds = {                                           
                self.mGetRegexLocal():
                [
                    [
                        exaMockCommand("/usr/bin/mkdir -p *", aRc=0, aStdout="" ,aPersist=True)
                    ]
                ],
                }                                        
        self.mPrepareMockCommands(_cmds)
        _obj.mHandlerGetVMCoreLogs()


    def test_mHandlerCheckConnection(self):
        fname = "mHandlerCheckConnection"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _cmds = {                                           
                self.mGetRegexLocal():
                [
                    [
                        exaMockCommand("/bin/ping -c  *", aRc=0, aStdout="" ,aPersist=True)
                    ]
                ],
                }                                        
        self.mPrepareMockCommands(_cmds)
        _obj = CommandHandler(self.mGetClubox())  
        _obj.mHandlerCheckConnection()


    def test_mHandlerCheckConnection_ping_fail(self):
        fname = "mHandlerCheckConnection"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _cmds = {                                           
                self.mGetRegexLocal():
                [
                    [
                        exaMockCommand("/bin/ping -c  *", aRc=-1, aStdout="" ,aPersist=True)
                    ]
                ],
                }                                        
        self.mPrepareMockCommands(_cmds)
        _obj = CommandHandler(self.mGetClubox())  
        _obj.mHandlerCheckConnection()

    def test_mHandlerCheckConfig(self):
        fname = "mHandlerCheckConfig"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _cmds = {                                           
                self.mGetRegexLocal():
                [
                    [
                        exaMockCommand("/bin/bash install.sh -cf  *", aRc=-1, aStdout="" ,aPersist=True)
                    ]
                ],
                }                                        
        self.mPrepareMockCommands(_cmds)
        _obj = CommandHandler(self.mGetClubox())  
        _obj.mHandlerCheckConfig()

    def test_mHandlerHealthCheckPostProv(self):
        fname = "mHandlerHealthCheckPostProv"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _cmds = {                                           
                self.mGetRegexLocal():
                [
                    [
                        exaMockCommand("/bin/bash install.sh -cf  *", aRc=-1, aStdout="" ,aPersist=True)
                    ]
                ],
                }                                        
        self.mPrepareMockCommands(_cmds)
        _obj = CommandHandler(self.mGetClubox())  
        _obj.mHandlerHealthCheckPostProv()

        _db = ebGetDefaultDB()
        _reqobj = ebJobRequest('cluctrl.dom0_details', {}, aDB=_db)
        self.mGetClubox().mSetRequestObj(_reqobj)
        _reqobj = self.mGetClubox().mGetRequestObj()
        _reqobj.mSetUUID("9419f694-9494-11ec-ba6e-565c06664853")
        with patch('exabox.agent.ebJobRequest.ebJobRequest.mGetUUID', return_value="9419f694-9494-11ec-ba6e-565c06664853"):
            _db.mUpdateRequest(_reqobj)
        _obj.mHandlerHealthCheckPostProv()
        

    def test_mHandlerFetchKeys(self):
        fname = "mHandlerFetchKeys"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _obj = CommandHandler(self.mGetClubox())  
        _obj.mHandlerFetchKeys()


    def test_mHandlerElasticInfo(self):
        fname = "mHandlerElasticInfo"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _obj = CommandHandler(self.mGetClubox())
        with self.assertRaises(ExacloudRuntimeError):
            _obj.mHandlerElasticInfo()
        _cmds = {                                           
                self.mGetRegexLocal():
                [
                    [
                        exaMockCommand("/bin/mkdir -p log/exascale_exatest*", aRc=0, aStdout="" ,aPersist=True)
                    ]
                ],
                }                                        
        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mSetExaScale(True)
        with self.assertRaises(AttributeError):
            _obj.mHandlerElasticInfo()
        self.mGetClubox().mGetArgsOptions().jsonconf['adb_s'] = 'True'
        with self.assertRaises(AttributeError):
            _obj.mHandlerElasticInfo()

    def test_mHandlerMountVolume(self):
        fname = "mHandlerMountVolume"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _obj = CommandHandler(self.mGetClubox())  
        with self.assertRaises(ExacloudRuntimeError):
            _obj.mHandlerMountVolume()
        self.mGetClubox().mSetExaScale(True)
        with self.assertRaises(ExacloudRuntimeError):
            _obj.mHandlerMountVolume()
    
    def test_mHandlerUnmountVolume(self):
        fname = "mHandlerUnmountVolume"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _obj = CommandHandler(self.mGetClubox())  
        with self.assertRaises(ExacloudRuntimeError):
            _obj.mHandlerUnmountVolume()
        self.mGetClubox().mSetExaScale(True)
        with self.assertRaises(ExacloudRuntimeError):
            _obj.mHandlerUnmountVolume()

    def test_mHandlerAddOEDAKey(self):
        fname = "mHandlerAddOEDAKey"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _obj = CommandHandler(self.mGetClubox())  
        with self.assertRaises(KeyError):
            _obj.mHandlerAddOEDAKey()

    def test_mHandlerPrepareCompute(self):
        fname = "mHandlerPrepareCompute"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _obj = CommandHandler(self.mGetClubox())  
        _obj.mHandlerPrepareCompute()

    def test_mHandlerAddOEDAKeyByHost(self):
        fname = "mHandlerAddOEDAKeyByHost"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _obj = CommandHandler(self.mGetClubox())  
        _cmds = {                                           
                self.mGetRegexLocal():
                [
                    [
                        exaMockCommand("/bin/ping -c 1 *", aRc=0, aStdout="" ,aPersist=True),
                    ],
                ],
                }                                        
        self.mPrepareMockCommands(_cmds)
        with self.assertRaises(KeyError):
            _obj.mHandlerAddOEDAKeyByHost()
        self.mGetClubox().mGetArgsOptions().jsonconf['oracle_hostnames'] = '/u01/app/19.0.0'
        with self.assertRaises(KeyError):
            _obj.mHandlerAddOEDAKeyByHost()

    def test_mHandlerCollectLog(self):
        fname = "mHandlerCollectLog"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        self.mGetClubox().mSetCmd("sim_install")
        _obj = CommandHandler(self.mGetClubox())  
        _obj.mHandlerCollectLog()

    def test_mHandlerRunCompTool(self):
        fname = "mHandlerRunCompTool"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        self.mGetClubox().mSetCmd("sim_install")
        _obj = CommandHandler(self.mGetClubox())  
        _obj.mHandlerRunCompTool()

    def test_mHandlerVmTmpKeyOp(self):
        fname = "mHandlerVmTmpKeyOp"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _obj = CommandHandler(self.mGetClubox())  
        with self.assertRaises(ExacloudRuntimeError):
            _obj.mHandlerVmTmpKeyOp()
        self.mGetClubox().mGetArgsOptions().jsonconf['op'] = 'get'
        with self.assertRaises(ExacloudRuntimeError) as exc:
            _obj.mHandlerVmTmpKeyOp()
            self.assertIn("Missing 'user' key in jsonconf", str(exc.exception))

        self.mGetClubox().mGetArgsOptions().jsonconf['op'] = 'clean'
        with self.assertRaises(ExacloudRuntimeError) as exc:
            _obj.mHandlerVmTmpKeyOp()
            self.assertIn("Missing 'user' key in jsonconf", str(exc.exception))

        self.mGetClubox().mGetArgsOptions().jsonconf['op'] = 'validate'
        with self.assertRaises(ExacloudRuntimeError) as exc:
            _obj.mHandlerVmTmpKeyOp()
            self.assertIn("Missing 'user' key in jsonconf", str(exc.exception))
    
    def test_mHandlerGetEnvInfo(self):
        fname = "mHandlerGetEnvInfo"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _cmds = {                                           
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("/bin/test -e  *", aRc=0, aStdout="" ,aPersist=True)
                    ],
                    [
                        exaMockCommand("/usr/local/bin/imageinfo  *", aRc=0, aStdout="" ,aPersist=True)
                    ],
                    [
                        exaMockCommand("/usr/local/bin/imageinfo  *", aRc=0, aStdout="" ,aPersist=True)
                    ],
                ],
                }                                        
        self.mPrepareMockCommands(_cmds)
        _obj = CommandHandler(self.mGetClubox())  
        with self.assertRaises(ExacloudRuntimeError) as exc:
            _obj.mHandlerGetEnvInfo()
            self.assertIn("No image repository configured. Check repository_root value at exabox.conf", str(exc.exception))

        _db = ebGetDefaultDB()
        _reqobj = ebJobRequest('cluctrl.dom0_details', {}, aDB=_db)
        self.mGetClubox().mSetRequestObj(_reqobj)
        _reqobj = self.mGetClubox().mGetRequestObj()
        _reqobj.mSetUUID("9419f694-9494-11ec-ba6e-565c06664853")
        with patch('exabox.agent.ebJobRequest.ebJobRequest.mGetUUID', return_value="9419f694-9494-11ec-ba6e-565c06664853"):
            _db.mUpdateRequest(_reqobj)
        with self.assertRaises(ExacloudRuntimeError):
            _obj.mHandlerGetEnvInfo()

    def test_mHandlerEXACCInfraPatchPayloadList(self):
        fname = "mHandlerEXACCInfraPatchPayloadList"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _obj = CommandHandler(self.mGetClubox())  
        _obj.mHandlerEXACCInfraPatchPayloadList()


    def test_mHandlerResetEnv(self):
        fname = "mHandlerResetEnv"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _cmds = {                                           
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("hostname", aRc=0, aStdout="scaqab10adm02" ,aPersist=True),
                        exaMockCommand("[ -d /root/oeda ]", aRc=0, aStdout="" ,aPersist=True)
                    ],
                    [
                        exaMockCommand("/usr/local/bin/imageinfo  *", aRc=0, aStdout="" ,aPersist=True)
                    ]
                ],
                }                                        
        self.mPrepareMockCommands(_cmds)
        _obj = CommandHandler(self.mGetClubox())  
        _obj.mHandlerResetEnv()

    def test_mHandlerInfo(self):
        fname = "mHandlerInfo"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _cmds = {                                           
                self.mGetRegexLocal():
                [
                    [
                        exaMockCommand("/bin/bash install.sh -cf", aRc=0, aStdout="" ,aPersist=True),
                    ],
                ],
                }                                        
        self.mPrepareMockCommands(_cmds)
        _obj = CommandHandler(self.mGetClubox())  
        _obj.mHandlerInfo()

    def test_mHandlerOpctlCmd(self):
        fname = "mHandlerOpctlCmd"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _obj = CommandHandler(self.mGetClubox())  
        _obj.mHandlerOpctlCmd()

    def test_mHandlerValidateCell(self):
        fname = "mHandlerValidateCell"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _obj = CommandHandler(self.mGetClubox())  
        _obj.mHandlerValidateCell()

    def test_mHandlerExaComputePatch(self):
        fname = "mHandlerExaComputePatch"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _cmds = {                                           
                self.mGetRegexLocal():
                [
                    [
                        exaMockCommand("/bin/mkdir -p *", aRc=0, aStdout="" ,aPersist=True),
                    ],
                ],
                }                                        
        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mSetOedaPath("exacloud")
        _obj = CommandHandler(self.mGetClubox())  
        _obj.mHandlerExaComputePatch()


    def test_mHandlerPostCompute(self):
        fname = "mHandlerPostCompute"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _obj = CommandHandler(self.mGetClubox())  
        _obj.mHandlerPostCompute()


    def test_mHandlerConfigureHostAcess(self):
        fname = "mHandlerConfigureHostAcess"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _cmds = {                                           
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("/usr/bin/sha256sum *", aRc=0, aStdout="" ,aPersist=True),
                    ],
                ],
                }                                        
        self.mPrepareMockCommands(_cmds)
        _obj = CommandHandler(self.mGetClubox())  
        with self.assertRaises(ExacloudRuntimeError):
            _obj.mHandlerConfigureHostAcess()


    def test_mHandleConfigureVMConsole(self):
        fname = "mHandleConfigureVMConsole"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _cmds = {                                           
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("/bin/test -e *", aRc=0, aStdout="" ,aPersist=True),
                    ],
                ],
                }                                        
        self.mPrepareMockCommands(_cmds)
        _obj = CommandHandler(self.mGetClubox())  
        _obj.mHandleConfigureVMConsole()

    def test_mHandlerNetworkReconfig(self):
        fname = "mHandlerNetworkReconfig"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _cmds = {                                           
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("/bin/test -e *", aRc=0, aStdout="" ,aPersist=True),
                    ],
                ],
                }                                        
        self.mPrepareMockCommands(_cmds)
        _obj = CommandHandler(self.mGetClubox())  
        with self.assertRaises(ExacloudRuntimeError) as exc:
            _obj.mHandlerNetworkReconfig()
            self.assertIn("EXACLOUD : Detected non-OCIEXACC environment. Network reconfiguration is not supported", str(exc.exception))


    def test_mHandlerRevertNetworkReconfig(self):
        fname = "mHandlerRevertNetworkReconfig"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _cmds = {                                           
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("/bin/test -e *", aRc=0, aStdout="" ,aPersist=True),
                    ],
                ],
                }                                        
        self.mPrepareMockCommands(_cmds)
        _obj = CommandHandler(self.mGetClubox())  
        with self.assertRaises(ExacloudRuntimeError) as exc:
            _obj.mHandlerRevertNetworkReconfig()
            self.assertIn("EXACLOUD : Detected non-OCIEXACC environment. Network reconfiguration is not supported", str(exc.exception))


    def test_mHandlerNetworkBondingModification(self):
        fname = "mHandlerNetworkBondingModification"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _cmds = {                                           
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("/bin/test -e *", aRc=0, aStdout="" ,aPersist=True),
                    ],
                ],
                }                                        
        self.mPrepareMockCommands(_cmds)
        _obj = CommandHandler(self.mGetClubox())  
        with self.assertRaises(ExacloudRuntimeError) as exc:
            _obj.mHandlerNetworkBondingModification()
            self.assertIn("EXACLOUD : Detected non-OCIEXACC environment. Network Bonding change is not supported", str(exc.exception))

    def test_mHandlerNetworkBondingValidation(self):
        fname = "mHandlerNetworkBondingValidation"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _cmds = {                                           
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("/bin/test -e *", aRc=0, aStdout="" ,aPersist=True),
                    ],
                ],
                }                                        
        self.mPrepareMockCommands(_cmds)
        _obj = CommandHandler(self.mGetClubox())  
        with self.assertRaises(ExacloudRuntimeError) as exc:
            _obj.mHandlerNetworkBondingValidation()
            self.assertIn("EXACLOUD : Detected non-OCIEXACC environment. Network Bonding change is not supported", str(exc.exception))

    def test_mHandlerCelldiskStorage(self):
        fname = "mHandlerCelldiskStorage"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _cmds = {                                           
                self.mGetRegexCell():
                [
                    [
                        exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get *", aRc=0, aStdout="ORACLE SERVER X8-2L" ,aPersist=True),
                    ],
                    [
                        exaMockCommand("cellcli -e LIST CELLDISK WHERE name LIKE *", aRc=0, aStdout="" ,aPersist=True),
                    ],
                    [
                        exaMockCommand("cellcli -e LIST CELLDISK WHERE name LIKE *", aRc=0, aStdout="CD_00_iad103712exdcl01  12.4737091064453125T    11.975616455078125T" ,aPersist=True),
                    ],
                ],
                }                                        
        self.mPrepareMockCommands(_cmds)
        _obj = CommandHandler(self.mGetClubox())  
        _obj.mHandlerCelldiskStorage()


    def test_mHandlerReclaimMountpointSpace(self):
        fname = "mHandlerReclaimMountpointSpace"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _cmds = {                                           
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("/bin/test -e *", aRc=0, aStdout="" ,aPersist=True),
                    ],
                ],
                }                                        
        self.mPrepareMockCommands(_cmds)
        _obj = CommandHandler(self.mGetClubox())  
        with self.assertRaises(ExacloudRuntimeError):
            _obj.mHandlerReclaimMountpointSpace()



    def test_mHandlerCheckRoceConfiguredDom0(self):
        fname = "mHandlerCheckRoceConfiguredDom0"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _cmds = {                                           
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("/bin/test -e *", aRc=0, aStdout="" ,aPersist=True),
                    ],
                ],
                }                                        
        self.mPrepareMockCommands(_cmds)
        _obj = CommandHandler(self.mGetClubox())  
        with self.assertRaises(ExacloudRuntimeError) as exc:
            _obj.mHandlerCheckRoceConfiguredDom0()
            self.assertIn("Missing roce config details in the payload", str(exc.exception))

    def test_mHandlerCaviumColletDiag(self):
        fname = "mHandlerCaviumColletDiag"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _obj = CommandHandler(self.mGetClubox())  
        _obj.mHandlerCaviumColletDiag()
        self.mGetClubox().mGetArgsOptions().jsonconf["ilom_hostname"] = 'ilom_localhost'
        self.mGetClubox().mGetArgsOptions().jsonconf["domain_name"] = 'us.oracle.com'
        _obj.mHandlerCaviumColletDiag()
    
    def test_mHandlerCheckCluster(self):
        fname = "mHandlerPrepareCompute"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _obj = CommandHandler(self.mGetClubox())  
        self.mGetClubox().mGetArgsOptions().healthcheck = 'custom'
        _obj.mHandlerCheckCluster()
        self.mGetClubox().mGetArgsOptions().healthcheck = 'exachk'
        with self.assertRaises(AttributeError):
            _obj.mHandlerCheckCluster()

    def test_mHandlerConfigureDom0Roce(self):
        fname = "mHandlerPrepareCompute"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _obj = CommandHandler(self.mGetClubox())  
        with self.assertRaises(ExacloudRuntimeError):
            _obj.mHandlerConfigureDom0Roce()

    def test_mHandlerConfigDns(self):
        fname = "mHandlerPrepareCompute"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _obj = CommandHandler(self.mGetClubox())  
        _obj.mHandlerConfigDns()
        self.mGetClubox().mGetArgsOptions().setupdns = True
        _obj.mHandlerConfigDns()

    def test_mHandlerXsVaultOperation(self):
        fname = "mHandlerPrepareCompute"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _obj = CommandHandler(self.mGetClubox())  
        #with self.assertRaises(KeyError):
        _obj.mHandlerXsVaultOperation()
        self.mGetClubox().mGetArgsOptions().jsonconf['vault_op'] = 'create'
    
    def test_mHandlerCaviumReset_test1(self):
        fname = "mHandlerCaviumReset"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _cmds = {                                           
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model*", aRc=0, aStdout="E5-2L" ,aPersist=True),
                    ],
                    [
                        exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model*", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/bin/rpm -q bondmonitor*", aRc=0, aStdout="True" ,aPersist=True),
                        exaMockCommand("/bin/test -e /sbin/initctl*", aRc=0, aStdout="True" ,aPersist=True),
                        exaMockCommand("/sbin/initctl status bondmonitor*", aRc=0, aStdout="True" ,aPersist=True),
                        exaMockCommand("/sbin/ip link set up eth1*", aRc=0, aStdout="True" ,aPersist=True),
                    ],
                    [
                        exaMockCommand("/bin/rpm -q bondmonitor*", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/sbin/ip link set up eth1*", aRc=0, aStdout="" ,aPersist=True),
                    ],
                ],
                }                                        
        self.mPrepareMockCommands(_cmds)
        _obj = CommandHandler(self.mGetClubox())  
        _obj.mHandlerCaviumReset()
        self.mGetClubox().mGetArgsOptions().jsonconf["hostname"] = 'scaqab10adm01'
        self.mGetClubox().mGetArgsOptions().jsonconf["ilom_hostname"] = 'ilom_localhost'
        self.mGetClubox().mGetArgsOptions().jsonconf["domain_name"] = 'us.oracle.com'
        self.mGetClubox().mGetArgsOptions().jsonconf["etherface"] = 'eth9'
        _obj.mHandlerCaviumReset()
        self.mGetClubox().mGetArgsOptions().jsonconf["etherface"] = 'eth1'
        self.mGetClubox().mGetArgsOptions().jsonconf["target_device"] = 'dom0'
        self.mGetClubox().mGetArgsOptions().jsonconf["action"] = 'start'
        _obj.mHandlerCaviumReset()
        self.mGetClubox().mGetArgsOptions().jsonconf["target_device"] = 'ilom'
        _obj.mHandlerCaviumReset()

    def test_mHandlerCaviumReset_test2(self):
        fname = "mHandlerCaviumReset"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        _cmds = {                                           
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model*", aRc=0, aStdout="E6-2L" ,aPersist=True),
                    ],
                    [
                        exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model*", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/bin/rpm -q bondmonitor*", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/bin/test -e /sbin/initctl*", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/sbin/initctl status bondmonitor*", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/sbin/ip link set up eth1*", aRc=0, aStdout="True" ,aPersist=True),
                    ],
                    [
                        exaMockCommand("/bin/rpm -q bondmonitor*", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/sbin/ip link set up eth1*", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/sbin/ip link set down eth1*", aRc=0, aStdout="" ,aPersist=True),
                    ],
                ],
                }                                        
        self.mPrepareMockCommands(_cmds)
        _obj = CommandHandler(self.mGetClubox())  
        _obj.mHandlerCaviumReset()
        self.mGetClubox().mGetArgsOptions().jsonconf["hostname"] = 'scaqab10adm01'
        self.mGetClubox().mGetArgsOptions().jsonconf["ilom_hostname"] = 'ilom_localhost'
        self.mGetClubox().mGetArgsOptions().jsonconf["domain_name"] = 'us.oracle.com'
        self.mGetClubox().mGetArgsOptions().jsonconf["etherface"] = 'eth9'
        _obj.mHandlerCaviumReset()
        self.mGetClubox().mGetArgsOptions().jsonconf["etherface"] = 'eth1'
        self.mGetClubox().mGetArgsOptions().jsonconf["target_device"] = 'dom0'
        self.mGetClubox().mGetArgsOptions().jsonconf["action"] = 'reset'
        _obj.mHandlerCaviumReset()
        self.mGetClubox().mGetArgsOptions().jsonconf["target_device"] = 'ilom'
        _obj.mHandlerCaviumReset()


    def test_mHandlerValidateVolumes(self):
        fname = "mHandlerValidateVolumes"
        ebLogInfo(f"Running unit test on clucommandhandler.py: {fname}")
        self.mGetClubox().mSetExaScale(False)
        _obj = CommandHandler(self.mGetClubox())
        with self.assertRaises(ExacloudRuntimeError):
            _obj.mHandlerValidateVolumes()
        self.mGetClubox().mGetArgsOptions().jsonconf["edvvolume"] = 'edvvolume'
        with self.assertRaises(ExacloudRuntimeError):
            _obj.mHandlerValidateVolumes()
        self.mGetClubox().mGetArgsOptions().jsonconf["client_hostname"] = 'scaqab10adm01vm1'
        with self.assertRaises(ExacloudRuntimeError):
            _obj.mHandlerValidateVolumes()

       


#if __name__ == "__main__":
#    unittest.main()
def suite():
    """
    This method ensures the execution in the intended order of the tests.
    """
    suite = unittest.TestSuite()
    suite.addTest(ebTestCmdHandler('test_mHandlerADBSInsertKey'))
    suite.addTest(ebTestCmdHandler('test_mHandlerAddVmExtraSize'))
    suite.addTest(ebTestCmdHandler('test_mHandlerAdminSwitchConnect'))
    suite.addTest(ebTestCmdHandler('test_mHandlerATPBackupRoutes'))
    suite.addTest(ebTestCmdHandler('test_mHandlerATPIPTables'))
    suite.addTest(ebTestCmdHandler('test_mHandlerClusterDetails'))
    suite.addTest(ebTestCmdHandler('test_mHandlerGenIncidentFile'))
    suite.addTest(ebTestCmdHandler('test_mHandlerSnmpPasswords'))
    suite.addTest(ebTestCmdHandler('test_mHandlerJumboOper'))
    suite.addTest(ebTestCmdHandler('test_mHandlerUpdateBlockState'))
    suite.addTest(ebTestCmdHandler('test_mHandlerGetCellIBInfo'))
    suite.addTest(ebTestCmdHandler('test_mHandlerGetVMCoreLogs'))
    suite.addTest(ebTestCmdHandler('test_mHandlerCheckConnection'))
    suite.addTest(ebTestCmdHandler('test_mHandlerCheckConnection_ping_fail'))
    suite.addTest(ebTestCmdHandler('test_mHandlerCheckConfig'))
    suite.addTest(ebTestCmdHandler('test_mHandlerHealthCheckPostProv'))
    suite.addTest(ebTestCmdHandler('test_mHandlerFetchKeys'))
    suite.addTest(ebTestCmdHandler('test_mHandlerElasticInfo'))
    suite.addTest(ebTestCmdHandler('test_mHandlerMountVolume'))
    suite.addTest(ebTestCmdHandler('test_mHandlerUnmountVolume'))
    suite.addTest(ebTestCmdHandler('test_mHandlerAddOEDAKey'))
    suite.addTest(ebTestCmdHandler('test_mHandlerPrepareCompute'))
    suite.addTest(ebTestCmdHandler('test_mHandlerAddOEDAKeyByHost'))
    suite.addTest(ebTestCmdHandler('test_mHandlerCollectLog'))
    suite.addTest(ebTestCmdHandler('test_mHandlerRunCompTool'))
    suite.addTest(ebTestCmdHandler('test_mHandlerVmTmpKeyOp'))
    suite.addTest(ebTestCmdHandler('test_mHandlerGetEnvInfo'))
    suite.addTest(ebTestCmdHandler('test_mHandlerEXACCInfraPatchPayloadList'))
    suite.addTest(ebTestCmdHandler('test_mHandlerResetEnv'))
    suite.addTest(ebTestCmdHandler('test_mHandlerInfo'))
    suite.addTest(ebTestCmdHandler('test_mHandlerOpctlCmd'))
    suite.addTest(ebTestCmdHandler('test_mHandlerValidateCell'))
    suite.addTest(ebTestCmdHandler('test_mHandlerExaComputePatch'))
    suite.addTest(ebTestCmdHandler('test_mHandlerPostCompute'))
    suite.addTest(ebTestCmdHandler('test_mHandlerConfigureHostAcess'))
    suite.addTest(ebTestCmdHandler('test_mHandleConfigureVMConsole'))
    suite.addTest(ebTestCmdHandler('test_mHandlerNetworkReconfig'))
    suite.addTest(ebTestCmdHandler('test_mHandlerRevertNetworkReconfig'))
    suite.addTest(ebTestCmdHandler('test_mHandlerNetworkBondingModification'))
    suite.addTest(ebTestCmdHandler('test_mHandlerNetworkBondingValidation'))
    suite.addTest(ebTestCmdHandler('test_mHandlerCelldiskStorage'))
    suite.addTest(ebTestCmdHandler('test_mHandlerReclaimMountpointSpace'))
    suite.addTest(ebTestCmdHandler('test_mHandlerCheckRoceConfiguredDom0'))
    suite.addTest(ebTestCmdHandler('test_mHandlerCaviumColletDiag'))
    suite.addTest(ebTestCmdHandler('test_mHandlerCheckCluster'))
    suite.addTest(ebTestCmdHandler('test_mHandlerConfigureDom0Roce'))
    #suite.addTest(ebTestCmdHandler('test_mHandlerConfigDns'))
    suite.addTest(ebTestCmdHandler('test_mHandlerXsVaultOperation'))
    suite.addTest(ebTestCmdHandler('test_mHandlerCaviumReset_test1'))
    suite.addTest(ebTestCmdHandler('test_mHandlerCaviumReset_test2'))
    suite.addTest(ebTestCmdHandler('test_mHandlerValidateVolumes'))
    
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner(failfast=True)
    runner.run(suite())


