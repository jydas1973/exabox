"""

 $Header: 

 Copyright (c) 2021, 2025, Oracle and/or its affiliates.

 NAME:
      tests_postvminstall.py - Unitest for postvm install steps

 DESCRIPTION:
      Run tests for postvminstall related function of clucontrol

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
       jesandov 01/29/24 - 36207260: Add function to read/write sysctl
                           parameters
       jfsaldan 10/04/22 - Bug 34527636 - Ebtables blocking traffic to retrieve
                           remote passphrase for fsencryption

    pbellary    08/25/21 - Creation of the file
"""

import unittest

import warnings

from exabox.log.LogMgr import ebLogInfo
from exabox.core.MockCommand import exaMockCommand
from unittest.mock import Mock, patch
from exabox.utils.node import CmdRet
from exabox.ovm.clucontrol import exaBoxCluCtrl
from exabox.ovm.csstep.cs_postvminstall import csPostVMInstall
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.userutils import ebUserUtils


class testOptions(object): pass

class ebTestPostVMInstall(ebTestClucontrol):
    @classmethod
    def setUpClass(self):
        super(ebTestPostVMInstall, self).setUpClass(aGenerateDatabase=True,aUseOeda=True)
        warnings.filterwarnings("ignore")
    
    @patch.object(exaBoxCluCtrl, 'mRemoveFqdnOnDomU')
    @patch.object(exaBoxCluCtrl, 'mChangeMinFreeKb')
    @patch.object(ebUserUtils, 'mAddSecscanSshd')
    def test_doExecute(self, mock_mRemoveFqdnOnDomU, mock_mChangeMinFreeKb, mock_mAddSecscanSshd):
        _steplist = ['ESTP_POSTVM_INSTALL']


        _local_commands = [
            exaMockCommand('/bin/ssh-keygen -R *', aPersist=True),
            exaMockCommand('ping -c 1 *', aRc=0, aPersist=True)
        ]

        _dom0_commands2 = [
           exaMockCommand('mkdir -p /opt/exacloud/clusters/config/*', aPersist=True),
           exaMockCommand('/bin/scp *', aPersist=True)
           
        ]

        _dom0_commands3 = [
            exaMockCommand('/opt/oracle.cellos/exadata.img.hw --get model', aStdout='ORACLE SERVER X5-2L', aPersist=True),
            exaMockCommand('mkdir -p /opt/exacloud/clusters/config/*', aPersist=True),
            exaMockCommand('/bin/scp *', aPersist=True)

        ]

        _dom0_commands4 = [
           exaMockCommand('cat.*sshd.*grep', aRc=1, aPersist=True),
           exaMockCommand('mkdir -p /opt/exacloud/clusters/config/*', aPersist=True),
           exaMockCommand('echo.*sshd', aPersist=True),
           exaMockCommand('service.*restart', aPersist=True),
           exaMockCommand('/bin/scp *', aPersist=True)
        ]

        _dom0_commands5 = [
            exaMockCommand("/bin/test -e /opt/exacloud/network/vif-whitelist.*",
                aRc=0),
            exaMockCommand("rm -f /opt/exacloud/network/vif-whitelist.*",
                aRc=0),
            exaMockCommand("xm network-list scaqab10client01vm08.us.oracle.com ",
                aRc=0),
            exaMockCommand("xm network-list scaqab10client02vm08.us.oracle.com ",
                aRc=0),
        ]

        _domu_commands1 = [
           exaMockCommand('mkdir -p /root/.ssh', aPersist=True),
           exaMockCommand('chmod 600 /root/.ssh/authorized_keys', aPersist=True),
           exaMockCommand('grep * ', aPersist=True),
           exaMockCommand('echo * ', aPersist=True),
           exaMockCommand('service sshd restart', aPersist=True),
           exaMockCommand('/usr/local/bin/imageinfo -version', aStdout='20.1.2.0.0.201125.2', aPersist=True),
           exaMockCommand('/bin/test -e * ', aPersist=True),
           exaMockCommand('/sbin/ip * ', aRc=1, aStdout="", aPersist=True)
        ]

        _domu_commands2 = [
           exaMockCommand('mkdir -p /root/.ssh', aPersist=True),
           exaMockCommand('grep * ', aPersist=True),
           exaMockCommand('echo * ', aPersist=True),
           exaMockCommand('service sshd restart', aPersist=True),
           exaMockCommand('/usr/local/bin/imageinfo -version', aStdout='20.1.2.0.0.201125.2', aPersist=True),
           exaMockCommand('chmod 600 /root/.ssh/authorized_keys', aPersist=True)

        ]

        _domu_commands3 = [
            exaMockCommand('grep * ', aPersist=True),
            exaMockCommand('echo * ', aPersist=True),
            exaMockCommand('numactl --hardware | grep "node 1"', aRc=1, aPersist=True),
            exaMockCommand('/usr/local/bin/imageinfo -version', aStdout='20.1.2.0.0.201125.2', aPersist=True),
            exaMockCommand('service sshd restart', aPersist=True),
        ]

        _domu_commands4 = [
           exaMockCommand('numactl --hardware | grep "node 1"', aRc=1, aPersist=True),
           exaMockCommand('/usr/local/bin/imageinfo -version', aStdout='20.1.2.0.0.201125.2', aPersist=True),
           exaMockCommand('sh -c *', aPersist=True)
           
        ]

        _domu_commands5 = [
             exaMockCommand('/bin/ls /etc/sysctl.d/', aStdout="sysctl.conf", aPersist=True),
             exaMockCommand('cp .*', aPersist=True),
             exaMockCommand('echo .*', aPersist=True),
             exaMockCommand('sysctl -p', aPersist=True),
             exaMockCommand('sysctl -n', aPersist=True),
             exaMockCommand('sed -i *', aPersist=True),
             exaMockCommand('sh -c *', aPersist=True),
             exaMockCommand('grep * ', aPersist=True)
        ]

        _domu_commands6 = [
             exaMockCommand('sh -c *', aPersist=True),
             exaMockCommand('grep * ', aPersist=True),
             exaMockCommand('sed * ', aPersist=True)
        ]

        _domu_commands7 = [
             exaMockCommand('sed * ', aPersist=True),
             exaMockCommand('grep * ', aPersist=True)
        ]

        _domu_commands8 = [
             exaMockCommand('mount * ', aPersist=True)
        ]

        _cell_commands1 = [
           exaMockCommand('cellcli -e list flashcache attributes name,size', aStdout='', aPersist=True),
           exaMockCommand('cellcli -e list cell detail | grep flashCacheMode', aStdout='', aPersist=True)
           
        ]
        _cell_commands2 = [
           exaMockCommand('cellcli -e list flashcache attributes name,size', aStdout='', aPersist=True),
           exaMockCommand('cellcli -e list cell detail | grep flashCacheMode', aStdout='', aPersist=True),
           exaMockCommand('cellcli -e drop flashcache', aStdout='', aPersist=True),
           exaMockCommand('cellcli -e list griddisk attributes name,asmmodestatus,asmdeactivationoutcome', aStdout='', aPersist=True),
           exaMockCommand('cellcli -e alter griddisk all inactive', aStdout='', aPersist=True),
           exaMockCommand('cellcli -e alter cell shutdown services cellsrv', aStdout='', aPersist=True),
           exaMockCommand('cellcli -e "alter cell flashCacheMode=writeback', aStdout='', aPersist=True),
           exaMockCommand('cellcli -e alter cell startup services cellsrv', aStdout='', aPersist=True),
           exaMockCommand('cellcli -e alter griddisk all active', aStdout='', aPersist=True),
           exaMockCommand('cellcli -e create flashcache all', aStdout='', aPersist=True)
           
        ]

        _cell_commands4 = [
           exaMockCommand('cat.*sshd', aStdout='', aPersist=True)
        ]

        _switch_commands1 = [
           exaMockCommand('cat.*sshd', aStdout='', aPersist=True)
        ]

        _cmds = {
            self.mGetRegexLocal(): [
                _local_commands
            ],
            self.mGetRegexDom0(): [
                _dom0_commands5,
                _dom0_commands4 + _dom0_commands5,
                _dom0_commands3 + _dom0_commands2,
                _dom0_commands4,
                _dom0_commands2,
            ],
            self.mGetRegexVm(): [
                _domu_commands1,
                _domu_commands2,
                _domu_commands3,
                _domu_commands4,
                _domu_commands5,
                _domu_commands6,
                _domu_commands7,
                _domu_commands8,
            ],
            self.mGetRegexCell(): [
                _cell_commands1,
                _cell_commands2,
                _cell_commands4
            ],
            self.mGetRegexSwitch(): [
                _switch_commands1
            ]
        }
        self.mPrepareMockCommands(_cmds)

        self.mGetClubox().mSetUt(True)
        _step = csPostVMInstall()
        _options = self.mGetClubox().mGetOptions()
        self.mGetClubox().mSetOciExacc(False)
        _step.doExecute(self.mGetClubox(), _options, _steplist)
        self.mGetClubox().mSetUt(False)

    def test_undoExecute(self):
        _steplist = ['ESTP_POSTVM_INSTALL']


        _local_commands = [
            exaMockCommand('ping -c 1 *', aRc=0, aPersist=True)
        ]

        _dom0_commands1 = [
           exaMockCommand('rm -r *', aRc=0, aPersist=True)
        ]

        _cmds = {
            self.mGetRegexLocal(): [
                _local_commands
            ],
            self.mGetRegexDom0(): [
                _dom0_commands1,
            ]
        }
        self.mPrepareMockCommands(_cmds)

        _step = csPostVMInstall()
        _options = self.mGetClubox().mGetOptions()
        self.mGetClubox().mSetOciExacc(False)
        _step.undoExecute(self.mGetClubox(), _options, _steplist)

if __name__ == '__main__':
    unittest.main()
