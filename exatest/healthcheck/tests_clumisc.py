#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/healthcheck/tests_clumisc.py /main/2 2024/08/16 07:40:21 naps Exp $
#
# tests_clumisc.py
#
# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
#
#    NAME
#      tests_clumisc.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    naps        08/14/24 - Bug 36949876 - X11 ipconf path changes.
#    joysjose    03/31/22 - Unit Test for healthcheck/clumisc.py
#    joysjose    03/31/22 - Creation
#
import json
import unittest
import re
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo
from exabox.healthcheck.clumisc import ebCluPreChecks,ebCluSshSetup,OracleVersion
from exabox.healthcheck.clucheck import ebCluCheck
from exabox.healthcheck.cluhealthcheck import ebCluHealth
from exabox.ovm.monitor import ebClusterNode
import warnings

CLUMISC_FAIL = False
CLUMISC_SUCC = True

CMD1  = 'ifconfig ib0 0.0.0.0 ; ifconfig ib1 0.0.0.0 ; ifconfig vmbondeth0 0.0.0.0 ; ifconfig vmbondeth1 0.0.0.0'
CMD1 += ' ; ifconfig eth1 0.0.0.0 ; ifconfig eth2 0.0.0.0 ; ifconfig eth3 0.0.0.0 ; ifconfig eth4 0.0.0.0 ; ifconfig eth5 0.0.0.0'
CMD2 = "if [[ ! `find ~/.ssh -maxdepth 1 -name 'id_rsa'` || ! `find ~/.ssh -maxdepth 1 -name 'id_rsa.pub'` ]]; then ssh-keygen -q -t rsa -N "" -f ~/.ssh/id_rsa <<<y > /dev/null 2>&1; fi; cat ~/.ssh/id_rsa.pub"
IN1 = """ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAAgQCvwrpalGlqCotknKhkTx+Be0EAVQdtb9MC/yyqVbYpWwI3wXEBuMwVoLhpQttTqTWb9GK+VqSe2pilQEJ6rz9kv+vsLUSgPdtFX+us4IDYFlrBVFvGbPy9FMMJGyjPuMgC4HCzTKteezKCPbnAksNZNrwfO/xISkVxXYj1wT8rqw== OEDA_PUB"""
OUT1 = """[Info]: ipconf command line: /usr/local/bin/ipconf -nocodes -conf /opt/oracle.cellos/cell.conf -check-consistency -semantic -at-runtime
Logging started to /var/log/cellos/ipconf.log
[Info]: Verify that the configured values in the Exadata configuration file /opt/oracle.cellos/cell.conf agree with the actual values in use on this system
Loading basic configuration settings from ILOM ...
[Info]: Consistency check PASSED"""

OUT2 = """ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEArCjp6sw0M36Cm1yJasmUeGDnMGyYZqRk+dl01OOTrwDT6mKGVD+UJfU3ACRyejKPW09fZkMFp7nhBf8gTapSwvyhcelO580iWzNCGoB5oeexivaXJpBaD01PKqd1NpgQfs90qIIXeB4ej5Z/kxGwT18Tnl6hSRxscH1tjkRfHxbajDGndd7cBP71asEPZyGIFIncp5Oi4fNmi7xX29HCT5LFaQwbtxC587HkCviRdaZLmYx7FaA9tN5gaXDg8qavF/4ImpwKosWUk9WcXecb1V0W6bxx/DHEuy6MZNHZR0RlRgFmFEZQQBFJUGCnq3JOSLm0dZE2yCUnFDT0VryjoQ== root@scas07adm07.us.oracle.com"""
OUT3 = """free_memory            : 63248
You have new mail in /var/spool/mail/root"""
OUT4 = """# Sun DCS IB partition config file
# This file is generated, do not edit
#! version_number : 838
Default=0x7fff,ipoib,defmember=both:
ALL_CAS=both,
ALL_SWITCHES=full,
SELF=full;
SUN_DCS=0x0001, ipoib :
ALL_SWITCHES=full,
0x0000000000000001; """



class testOptions(object): pass

class ebTestClumisc(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestClumisc, self).setUpClass(True, True)
        warnings.filterwarnings("ignore")

    def test_mVMPreChecks(self):
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(re.escape("/bin/test -e /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/vm.cfg"), aRc=0, aPersist=True),
                    exaMockCommand(re.escape("/bin/test -e /EXAVMIMAGES/GuestImages/scaqab10client02vm08.us.oracle.com/vm.cfg"), aRc=1, aPersist=True),
                    
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = ebCluPreChecks(self.mGetClubox(), baseHealthCheckObject)
        currentHealthObject.mVMPreChecks()

    def test_mNetworkBasicChecks(self):
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = ebCluPreChecks(self.mGetClubox(), baseHealthCheckObject)
        currentHealthObject.mNetworkBasicChecks(True)
       
    def test_mCheckUsedSpace(self):
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = ebCluPreChecks(self.mGetClubox(), baseHealthCheckObject)
        commandToExecute = 'df -P / | tail -1 | awk \'0+$5 >= 85 {print}\''

        for dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            _cmds = {
                self.mGetRegexDom0(): [
                    [
                        exaMockCommand(commandToExecute, aRc=0, aStdout="/dev/mapper/VGExaDb-LVDbSys3    30832548 15103436  14139864      10% /" if dom0 == "scaqab10adm02.us.oracle.com" else "", aPersist=True)
                    ]
                ]
            }
            self.mPrepareMockCommands(_cmds)

            returnedResult = currentHealthObject.mCheckUsedSpace(dom0,"/","85")

    def test_mConnectivityChecks(self):

        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = ebCluPreChecks(self.mGetClubox(), baseHealthCheckObject)
        
        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand(re.escape("/bin/ping -c 1 scaqab10adm01.us.oracle.com"), aRc=0, aPersist=True),
                    exaMockCommand(re.escape("/bin/ping -c 1 scaqab10adm02.us.oracle.com"), aRc=0, aPersist=True),
                    exaMockCommand(re.escape("/bin/ping -c 1 scaqab10adm01nat08.us.oracle.com"), aRc=0, aPersist=True),
                    exaMockCommand(re.escape("/bin/ping -c 1 scaqab10adm02nat08.us.oracle.com"), aRc=0, aPersist=True),
                    exaMockCommand(re.escape("/bin/ping -c 1 scaqab10celadm01.us.oracle.com"), aRc=0, aPersist=True),
                    exaMockCommand(re.escape("/bin/ping -c 1 scaqab10celadm02.us.oracle.com"), aRc=0, aPersist=True),
                    exaMockCommand(re.escape("/bin/ping -c 1 scaqab10celadm03.us.oracle.com"), aRc=0, aPersist=True),
                    exaMockCommand(re.escape("/bin/ping -c 1 scaqab10sw-iba0.us.oracle.com"), aRc=0, aPersist=True),
                    exaMockCommand(re.escape("/bin/ping -c 1 scaqab10sw-ibb0.us.oracle.com"), aRc=0, aPersist=True),
                    exaMockCommand(re.escape("/bin/ping -c 1 scaqab10sw-ibs0.us.oracle.com"), aRc=0, aPersist=True),
                ]
            ],
            
            self.mGetRegexSwitch():[

                [
                    exaMockCommand(re.escape("/bin/ping -c 1 scaqab10sw-iba0.us.oracle.com"), aRc=0, aPersist=True),
                    exaMockCommand(re.escape("smpartition list active no-page | head -10"), aRc=0, aStdout= OUT4, aPersist=True),

                ]
            ]
            
        }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mConnectivityChecks()

    def test_mGetSSHPublicKeyFromHost1(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluSshSetup.mGetSSHPublicKeyFromHost")
        currentHealthObject = ebCluSshSetup(self.mGetClubox())
        _cmds = {

            self.mGetRegexDom0(): [

                [
                    exaMockCommand(re.escape("""if [[ ! `find ~/.ssh -maxdepth 1 -name 'id_rsa'` || ! `find ~/.ssh -maxdepth 1 -name 'id_rsa.pub'` ]]; then ssh-keygen -q -t rsa -N "" -f ~/.ssh/id_rsa <<<y > /dev/null 2>&1; fi; cat ~/.ssh/id_rsa.pub"""), aRc=0, aStdout = OUT2, aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mGetSSHPublicKeyFromHost(self.mGetClubox().mReturnDom0DomUPair()[0][0])

    def test_mGetSSHPublicKeyFromHost2(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluSshSetup.mGetSSHPublicKeyFromHost")
        currentHealthObject = ebCluSshSetup(self.mGetClubox())
        _cmds = {

            self.mGetRegexDom0(): [

                [
                    exaMockCommand(re.escape("""if [[ ! `find ~/.ssh -maxdepth 1 -name 'id_rsa'` || ! `find ~/.ssh -maxdepth 1 -name 'id_rsa.pub'` ]]; then ssh-keygen -q -t rsa -N "" -f ~/.ssh/id_rsa <<<y > /dev/null 2>&1; fi; cat ~/.ssh/id_rsa.pub"""), aRc=1, aStdout = "Failed to get public key for host", aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mGetSSHPublicKeyFromHost(self.mGetClubox().mReturnDom0DomUPair()[0][0])

    def test_mAddKeyToHosts(self):
        aRemoteHostList = self.mGetClubox().mReturnDom0DomUPair()[0][0],self.mGetClubox().mReturnDom0DomUPair()[1][0]
        ebLogInfo(f"Remote host list: {aRemoteHostList}")

        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluSshSetup.mGetSSHPublicKeyFromHost")
        currentHealthObject = ebCluSshSetup(self.mGetClubox())
        _cmds = {

            self.mGetRegexDom0(): [

                [
                    exaMockCommand(re.escape("echo ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAAgQCvwrpalGlqCotknKhkTx+Be0EAVQdtb9MC/yyqVbYpWwI3wXEBuMwVoLhpQttTqTWb9GK+VqSe2pilQEJ6rz9kv+vsLUSgPdtFX+us4IDYFlrBVFvGbPy9FMMJGyjPuMgC4HCzTKteezKCPbnAksNZNrwfO/xISkVxXYj1wT8rqw== OEDA_PUB >> ~/.ssh/authorized_keys"), aRc=0, aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mAddKeyToHosts(IN1,aRemoteHostList)

    def test_mRemoveKeyFromHosts(self):
        aRemoteHostList = self.mGetClubox().mReturnDom0DomUPair()[0][0],self.mGetClubox().mReturnDom0DomUPair()[1][0]
        ebLogInfo(f"Remote host list: {aRemoteHostList}")

        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluSshSetup.mGetSSHPublicKeyFromHost")
        currentHealthObject = ebCluSshSetup(self.mGetClubox())
        _cmds = {

            self.mGetRegexDom0(): [

                [
                    exaMockCommand(re.escape("ex '+g/.*ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAAgQCvwrpalGlqCotknKhkTx+Be0EAVQdtb9MC/yyqVbYpWwI3wXEBuMwVoLhpQttTqTWb9GK+VqSe2pilQEJ6rz9kv+vsLUSgPdtFX+us4IDYFlrBVFvGbPy9FMMJGyjPuMgC4HCzTKteezKCPbnAksNZNrwfO/xISkVxXYj1wT8rqw== OEDA_PUB.*/d' -scwq ~/.ssh/authorized_keys"), aRc=0, aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mRemoveKeyFromHosts(IN1,aRemoteHostList)

    def test_mAddToKnownHosts(self):
        aRemoteHostList = self.mGetClubox().mReturnDom0DomUPair()[0][0],self.mGetClubox().mReturnDom0DomUPair()[1][0]
        ebLogInfo(f"Remote host list: {aRemoteHostList}")

        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluSshSetup.mGetSSHPublicKeyFromHost")
        currentHealthObject = ebCluSshSetup(self.mGetClubox())
        _cmds = {

            self.mGetRegexDom0(): [

                [
                    exaMockCommand(re.escape("ssh-keyscan -t rsa scaqab10adm01.us.oracle.com >> ~/.ssh/known_hosts;"), aRc=0, aPersist=True),
                    exaMockCommand(re.escape("ssh-keyscan -t rsa scaqab10adm02.us.oracle.com >> ~/.ssh/known_hosts;"), aRc=0, aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mAddToKnownHosts(self.mGetClubox().mReturnDom0DomUPair()[0][0],aRemoteHostList)

    def test_mRemoveFromKnownHosts(self):
        aRemoteHostList = self.mGetClubox().mReturnDom0DomUPair()[0][0],self.mGetClubox().mReturnDom0DomUPair()[1][0]
        ebLogInfo(f"Remote host list: {aRemoteHostList}")

        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluSshSetup.mGetSSHPublicKeyFromHost")
        currentHealthObject = ebCluSshSetup(self.mGetClubox())
        _cmds = {

            self.mGetRegexDom0(): [

                [
                    exaMockCommand(re.escape("ssh-keygen -R scaqab10adm01.us.oracle.com"), aRc=0, aPersist=True),
                    exaMockCommand(re.escape("ssh-keygen -R scaqab10adm02.us.oracle.com"), aRc=0, aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mRemoveFromKnownHosts(self.mGetClubox().mReturnDom0DomUPair()[0][0],aRemoteHostList)

    def test_mSetSSHPasswordless(self):
        aRemoteHostList = self.mGetClubox().mReturnDom0DomUPair()[0][0],self.mGetClubox().mReturnDom0DomUPair()[1][0]
        ebLogInfo(f"Remote host list: {aRemoteHostList}")

        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluSshSetup.mGetSSHPublicKeyFromHost")
        currentHealthObject = ebCluSshSetup(self.mGetClubox())
        _cmds = {

            self.mGetRegexDom0(): [

                [
                    exaMockCommand(re.escape("""if [[ ! `find ~/.ssh -maxdepth 1 -name 'id_rsa'` || ! `find ~/.ssh -maxdepth 1 -name 'id_rsa.pub'` ]]; then ssh-keygen -q -t rsa -N "" -f ~/.ssh/id_rsa <<<y > /dev/null 2>&1; fi; cat ~/.ssh/id_rsa.pub"""), aRc=0, aPersist=True),
                    exaMockCommand(re.escape("ex '+g/.*scaqab10adm01.us.oracle.com.*/d' -scwq ~/.ssh/authorized_keys"), aRc=0, aPersist=True),

                ],
                [
                    exaMockCommand(re.escape("""if [[ ! `find ~/.ssh -maxdepth 1 -name 'id_rsa'` || ! `find ~/.ssh -maxdepth 1 -name 'id_rsa.pub'` ]]; then ssh-keygen -q -t rsa -N "" -f ~/.ssh/id_rsa <<<y > /dev/null 2>&1; fi; cat ~/.ssh/id_rsa.pub"""), aRc=0, aPersist=True),
                    exaMockCommand(re.escape("ssh-keygen -R scaqab10adm01.us.oracle.com"), aRc=0, aPersist=True),
                    exaMockCommand(re.escape("ssh-keygen -R scaqab10adm02.us.oracle.com"), aRc=0, aPersist=True),
                ],
                [
                    exaMockCommand(re.escape("ssh-keyscan -t rsa scaqab10adm01.us.oracle.com >> ~/.ssh/known_hosts;"), aRc=0, aPersist=True),
                    exaMockCommand(re.escape("ssh-keyscan -t rsa scaqab10adm02.us.oracle.com >> ~/.ssh/known_hosts;"), aRc=0, aPersist=True),
                ],
                [
                    exaMockCommand(re.escape("ex '+g/.*scaqab10adm01.us.oracle.com.*/d' -scwq ~/.ssh/authorized_keys"), aRc=0, aPersist=True),
                    exaMockCommand(re.escape("ex '+g/.*scaqab10adm02.us.oracle.com.*/d' -scwq ~/.ssh/authorized_keys"), aRc=0, aPersist=True),


                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mSetSSHPasswordless(self.mGetClubox().mReturnDom0DomUPair()[0][0],aRemoteHostList)

    def test_mResetNetwork(self):
        _cmds = {

            self.mGetRegexDom0(): [

                [
                    exaMockCommand(CMD1, aRc=0, aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = ebCluPreChecks(self.mGetClubox(), baseHealthCheckObject)
        currentHealthObject.mResetNetwork()

    def test_mNetworkDom0PreChecks1(self):
        ebLogInfo("Running unit test for clumisc")

        #Create args structure
        _cmds = {

            self.mGetRegexDom0(): [

                [
                    exaMockCommand("/bin/test -e /opt/oracle.cellos/cell.conf", aRc=0, aPersist=True),
                    exaMockCommand("/usr/local/bin/ipconf -nocodes -conf /opt/oracle.cellos/cell.conf -check-consistency -semantic -at-runtime", aRc=0, aStdout = OUT1, aPersist=True)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = ebCluPreChecks(self.mGetClubox(), baseHealthCheckObject)
        currentHealthObject.mNetworkDom0PreChecks()

    def test_mNetworkDom0PreChecks2(self):
        ebLogInfo("Running unit test for clumisc")

        #Create args structure
        _cmds = {

            self.mGetRegexDom0(): [

                [
                    exaMockCommand("/bin/test -e /opt/oracle.cellos/cell.conf", aRc=1, aPersist=True),
                    exaMockCommand("/usr/local/bin/ipconf -nocodes -conf /opt/oracle.cellos/cell.conf -check-consistency -semantic -at-runtime", aRc=1, aStdout = OUT1, aPersist=True)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = ebCluPreChecks(self.mGetClubox(), baseHealthCheckObject)
        currentHealthObject.mNetworkDom0PreChecks()
    
    def test_mCompareVersions(self):
        ebLogInfo("")
        currentHealthObject = OracleVersion()
        _cmds = {

            self.mGetRegexDom0(): [

                [
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mCompareVersions()

if __name__ == "__main__":
    unittest.main()
