#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_cluvmreconfig.py /main/5 2024/09/20 08:49:28 dekuckre Exp $
#
# tests_cluvmreconfig.py
#
# Copyright (c) 2023, 2024, Oracle and/or its affiliates.
#
#    NAME
#      tests_cluvmreconfig.py - Unit tests for cluvmreconfig.py
#
#    DESCRIPTION
#      Unit tests for cluvmreconfig.py
#
#    NOTES
#      None.
#
#    MODIFIED   (MM/DD/YY)
#    dekuckre    08/06/24 - Added test_mUpdateQuorumConfig
#    aararora    05/16/24 - ER 36485120: IPv6 support in exacloud
#    scoral      11/10/23 - Creation
#

from ipaddress import IPv4Network
import re
from typing import Dict, List
import unittest
from unittest.mock import patch
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.clucontrol import exaBoxCluCtrl
from exabox.ovm.cluvmreconfig import mDomUReconfig, mUpdateQuorumConfig


ConnCmds = List[exaMockCommand]
NodeCmds = List[ConnCmds]
TestCmds = Dict[str, NodeCmds]



def mDomUReconfigCmds(aCluCtrl: exaBoxCluCtrl, aJson: dict) -> TestCmds:
    cmds: TestCmds = {}
    for dom0, domu in aCluCtrl.mReturnDom0DomUPair():
        domu_cmds: NodeCmds = []
        conn_cmds: ConnCmds = []

        domu_hostname, *_ = domu.split('.')

        n1coip = aJson[domu_hostname]['client']['oldipAddress']
        n1cip = aJson[domu_hostname]['client']['ipAddress']
        n1conm = aJson[domu_hostname]['client']['oldnetmask']
        n1cnm = aJson[domu_hostname]['client']['netmask']
        n1cogt = aJson[domu_hostname]['client']['oldgateway']
        n1cgt = aJson[domu_hostname]['client']['gateway']
        n1conmb = IPv4Network(f"0.0.0.0/{n1conm}").prefixlen
        n1cnmb = IPv4Network(f"0.0.0.0/{n1cnm}").prefixlen
        n1con = IPv4Network(f"{n1cogt}/{n1conm}",
                            strict=False).network_address
        n1cn = IPv4Network(f"{n1cgt}/{n1cnm}",
                           strict=False).network_address
        n1cobc = IPv4Network(f"{n1cogt}/{n1conm}",
                             strict=False).broadcast_address
        n1cbc = IPv4Network(f"{n1cgt}/{n1cnm}",
                            strict=False).broadcast_address

        n1boip = aJson[domu_hostname]['backup']['oldipAddress']
        n1bip = aJson[domu_hostname]['backup']['ipAddress']
        n1bonm = aJson[domu_hostname]['backup']['oldnetmask']
        n1bnm = aJson[domu_hostname]['backup']['netmask']
        n1bogt = aJson[domu_hostname]['backup']['oldgateway']
        n1bgt = aJson[domu_hostname]['backup']['gateway']
        n1bonmb = IPv4Network(f"0.0.0.0/{n1bonm}").prefixlen
        n1bnmb = IPv4Network(f"0.0.0.0/{n1bnm}").prefixlen
        n1bon = IPv4Network(f"{n1bogt}/{n1bonm}",
                            strict=False).network_address
        n1bn = IPv4Network(f"{n1bgt}/{n1bnm}",
                           strict=False).network_address
        n1bobc = IPv4Network(f"{n1bogt}/{n1bonm}",
                             strict=False).broadcast_address
        n1bbc = IPv4Network(f"{n1bgt}/{n1bnm}",
                            strict=False).broadcast_address

        cmd: str = f"sed -i 's/{n1coip}/{n1cip}/g' /etc/ssh/sshd_config"
        conn_cmds.append(exaMockCommand(cmd))

        cmd = f"sed -i 's/{n1coip}/{n1cip}/g' /etc/hosts"
        conn_cmds.append(exaMockCommand(cmd))

        cmd = f"sed -i 's/{n1boip}/{n1bip}/g' /etc/hosts"
        conn_cmds.append(exaMockCommand(cmd))

        for _ , vm in aCluCtrl.mReturnDom0DomUPair():
            if vm != domu:
                n = vm.split('.')[0]
                ip = aJson[n]['client']['ipAddress']
                host = aJson[n]['hostName']
                cmd = f"echo '{ip} {host} {host.split('.')[0]}' >> /etc/hosts"
                conn_cmds.append(exaMockCommand(cmd))

                cmd = re.escape(
                    f"sed '/{aJson[n]['oldHostname'].split('.')[0]}$/d' "
                    "/etc/hosts"
                )
                conn_cmds.append(exaMockCommand(cmd))

        cmd = (f"sed -i 's/{n1coip}/{n1cip}/g' "
               "/etc/sysconfig/network-scripts/ifcfg-bondeth0")
        conn_cmds.append(exaMockCommand(cmd))

        cmd = (f"sed -i 's/{n1conm}/{n1cnm}/g' "
               "/etc/sysconfig/network-scripts/ifcfg-bondeth0")
        conn_cmds.append(exaMockCommand(cmd))

        cmd = (f"sed -i 's/{n1cogt}/{n1cgt}/g' "
               "/etc/sysconfig/network-scripts/ifcfg-bondeth0")
        conn_cmds.append(exaMockCommand(cmd))

        cmd = (f"sed -i 's/{n1con}/{n1cn}/g' "
               "/etc/sysconfig/network-scripts/ifcfg-bondeth0")
        conn_cmds.append(exaMockCommand(cmd))

        cmd = (f"sed -i 's/{n1cobc}/{n1cbc}/g' "
               "/etc/sysconfig/network-scripts/ifcfg-bondeth0")
        conn_cmds.append(exaMockCommand(cmd))

        cmd = (f"sed -i 's/{n1cogt}/{n1cgt}/g' "
               "/etc/sysconfig/network-scripts/route-bondeth0")
        conn_cmds.append(exaMockCommand(cmd))

        cmd = (f"sed -i 's@{n1con}/{n1conmb}@{n1cn}/{n1cnmb}@g' "
               "/etc/sysconfig/network-scripts/route-bondeth0")
        conn_cmds.append(exaMockCommand(cmd))

        cmd = (f"sed -i 's@{n1con}/{n1conmb}@{n1cn}/{n1cnmb}@g' "
               "/etc/sysconfig/network-scripts/rule-bondeth0")
        conn_cmds.append(exaMockCommand(cmd))

        cmd = (f"sed -i 's/{n1boip}/{n1bip}/g' "
               "/etc/sysconfig/network-scripts/ifcfg-bondeth1")
        conn_cmds.append(exaMockCommand(cmd))

        cmd = (f"sed -i 's/{n1bonm}/{n1bnm}/g' "
               "/etc/sysconfig/network-scripts/ifcfg-bondeth1")
        conn_cmds.append(exaMockCommand(cmd))

        cmd = (f"sed -i 's/{n1bogt}/{n1bgt}/g' "
               "/etc/sysconfig/network-scripts/ifcfg-bondeth1")
        conn_cmds.append(exaMockCommand(cmd))

        cmd = (f"sed -i 's/{n1bon}/{n1bn}/g' "
               "/etc/sysconfig/network-scripts/ifcfg-bondeth1")
        conn_cmds.append(exaMockCommand(cmd))

        cmd = (f"sed -i 's/{n1bobc}/{n1bbc}/g' "
               "/etc/sysconfig/network-scripts/ifcfg-bondeth1")
        conn_cmds.append(exaMockCommand(cmd))

        cmd = (f"sed -i 's/{n1bogt}/{n1bgt}/g' "
               "/etc/sysconfig/network-scripts/route-bondeth1")
        conn_cmds.append(exaMockCommand(cmd))

        cmd = (f"sed -i 's@{n1bon}/{n1bonmb}@{n1bn}/{n1bnmb}@g' "
               "/etc/sysconfig/network-scripts/route-bondeth1")
        conn_cmds.append(exaMockCommand(cmd))

        cmd = (f"sed -i 's@{n1bon}/{n1bonmb}@{n1bn}/{n1bnmb}@g' "
               "/etc/sysconfig/network-scripts/rule-bondeth1")
        conn_cmds.append(exaMockCommand(cmd))

        cmd = f"grep {n1cip} /etc/ssh/sshd_config"
        conn_cmds.append(exaMockCommand(cmd))

        cmd = f"grep {n1cip} /etc/sysconfig/network-scripts/ifcfg-bondeth0"
        conn_cmds.append(exaMockCommand(cmd))

        cmd = f"grep {n1bip} /etc/sysconfig/network-scripts/ifcfg-bondeth1"
        conn_cmds.append(exaMockCommand(cmd))

        cmd = "service network restart"
        conn_cmds.append(exaMockCommand(cmd))

        cmd = "service sshd restart"
        conn_cmds.append(exaMockCommand(cmd))

        domu_cmds.append(conn_cmds)
        cmds[domu] = domu_cmds
    return cmds



class ebTestFomUFilesystems(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestFomUFilesystems, self).setUpClass(True, True)

    def test_mDomUReconfigCmds(self):
        cluctrl: exaBoxCluCtrl = self.mGetClubox()
        payload: dict = {}
        for dom0, domu  in cluctrl.mReturnDom0DomUPair():
            domu_json = {
                'client': {
                    'oldipAddress': '10.0.57.208',
                    'ipAddress': '10.0.5.5',
                    'oldnetmask': '255.255.192.0',
                    'netmask': '255.255.254.0',
                    'oldgateway': '10.0.0.1',
                    'gateway': '10.0.4.1'
                },
                'backup': {
                    'oldipAddress': '10.0.96.113',
                    'ipAddress': '10.0.2.74',
                    'oldnetmask': '255.255.192.0',
                    'netmask': '255.255.254.0',
                    'oldgateway': '10.0.64.1',
                    'gateway': '10.0.2.1'
                },
                'oldHostname': f"old{domu}",
                'hostName': domu,
            }

            domu_hostname, *_ = domu.split('.')
            payload[domu_hostname] = domu_json

        cmds = mDomUReconfigCmds(cluctrl, payload)
        self.mPrepareMockCommands(cmds)
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl'
                   '.mConfigurePasswordLessDomU'):
            mDomUReconfig(cluctrl, None, payload)

    def test_mUpdateQuorumConfig(self):

        cluctrl: exaBoxCluCtrl = self.mGetClubox()
        payload: dict = {}
        cmds = {       
                self.mGetRegexVm():                                    
                [       
                     [  
                         exaMockCommand("/opt/oracle.SupportTools/quorumdiskmgr *", aRc=0, aStdout=" ",aPersist=True),                
                         exaMockCommand(re.escape("ip "), aRc=0, aStdout="", aPersist=True)                           
                     ],
                     [
                         exaMockCommand("/opt/oracle.SupportTools/quorumdiskmgr *", aRc=0, aStdout=" " ,aPersist=True)
                     ],
                     [
                         exaMockCommand("/opt/oracle.SupportTools/quorumdiskmgr *", aRc=0, aStdout=" " ,aPersist=True)
                     ],
                     [
                         exaMockCommand("/opt/oracle.SupportTools/quorumdiskmgr *", aRc=0, aStdout=" ",aPersist=True)
                     ],
                     [
                         exaMockCommand("/opt/oracle.SupportTools/quorumdiskmgr *", aRc=0, aStdout=" ",aPersist=True)
                     ]
                ],  
                self.mGetRegexCell():
                        [
                            [
                                exaMockCommand("cellcli *", aRc=0,aPersist=True)
                            ]
                        ]
                }       


        self.mPrepareMockCommands(cmds)
        mUpdateQuorumConfig(cluctrl, None, payload)

if __name__ == '__main__':
    unittest.main() 
