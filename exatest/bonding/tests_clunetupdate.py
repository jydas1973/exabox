#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/bonding/tests_clunetupdate.py /main/2 2024/10/09 06:57:20 aararora Exp $
#
# tests_clunetupdate.py
#
# Copyright (c) 2023, 2024, Oracle and/or its affiliates.
#
#    NAME
#      tests_clunetupdate.py - Unit tests for clunetupdate.py
#
#    DESCRIPTION
#      Unit tests for clunetupdate.py
#
#    NOTES
#      None.
#
#    MODIFIED   (MM/DD/YY)
#    aararora    10/09/24 - Bug 37133558: Do not update bondmonitor if it is of
#                           same release version
#    scoral      11/14/23 - Creation
#

import os
from typing import Dict, List, Sequence
import unittest
from unittest.mock import patch
from exabox.core.Context import exaBoxContext, get_gcontext
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.bonding.tests_bonding import install_bond_monitor_rpm_cmds, node_create_bonding_dirs_cmds
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.clubonding import LOCAL_MONITOR_RPM_FILE
from exabox.ovm.clucontrol import exaBoxCluCtrl
from exabox.ovm.clunetupdate import bond_for_vlan, CHANGE_MAC_CMD_FMT, CHANGE_VLAN_CMD_FMT, NetUpdates, NodeVMNetUpdates, update_networks


ConnCmds = List[exaMockCommand]
NodeCmds = List[ConnCmds]
TestCmds = Dict[str, NodeCmds]



def update_networks_cmds(
        updates: Sequence[NodeVMNetUpdates],
        monitor_rpm: str,
        update_nft_rules: bool=True) -> TestCmds:
    """Gets the exaMockCommands for a update_networks call.

    :param updates: network updates to simulate the commands.
    :param monitor_rpm: Local path where bondmonitor RPM is supposed to be
                        placed.
    :param update_nft_rules: Simulate NFTables rules update.
    :returns: Dict of connections and commands per node.
    """
    cmds: TestCmds = {}
    nft_rules = '/etc/nftables/exadata.nft'
    for update in updates:
        dom0_cmds: NodeCmds = []
        conn_cmds: ConnCmds = []
        conn_cmds.append(exaMockCommand("/bin/rpm -qi bondmonitor | grep Release", aRc=1, aPersist=True))

        conn_cmds.append(exaMockCommand(f"/bin/test -e {nft_rules}",
                                        aRc=0 if update_nft_rules else 1))

        conn_cmds += node_create_bonding_dirs_cmds()
        conn_cmds += install_bond_monitor_rpm_cmds(monitor_rpm)

        for net_type, conf in update.net_updates.items():
            if conf.macs:
                curr_vlan, old_mac, new_mac = conf.macs
                cmd = CHANGE_MAC_CMD_FMT.format(
                    update.domu_vm_name, curr_vlan, net_type, new_mac, old_mac)
                conn_cmds.append(exaMockCommand(cmd))

            if conf.vlans:
                old_vlan, new_vlan = conf.vlans
                old_vlan = 0 if old_vlan is None else old_vlan
                new_vlan = 0 if new_vlan is None else new_vlan

                cmd = CHANGE_VLAN_CMD_FMT.format(
                    update.domu_vm_name, net_type, new_vlan, old_vlan)
                conn_cmds.append(exaMockCommand(cmd))

                if update_nft_rules:
                    old_bond = f'"{bond_for_vlan(old_vlan)}"'
                    new_bond = f'"{bond_for_vlan(new_vlan)}"'
                    cmd = (f"/bin/sed -i 's/{old_bond}/{new_bond}/g' "
                            f"{nft_rules}")
                    conn_cmds.append(exaMockCommand(cmd))

        if update_nft_rules:
            conn_cmds.append(exaMockCommand("/bin/systemctl restart nftables"))

        dom0_cmds.append(conn_cmds)
        cmds[update.dom0] = dom0_cmds

    return cmds



class ebTestCluNetUpdate(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestCluNetUpdate, self).setUpClass(True, True)

    def test_update_networks(self):
        ctx: exaBoxContext = get_gcontext()
        cluctrl: exaBoxCluCtrl = self.mGetClubox()
        updates: List[NodeVMNetUpdates] = [
            NodeVMNetUpdates(
                dom0=dom0,
                domu_vm_name=domu,
                net_updates={
                    'client': NetUpdates(
                        vlans=(None, 100),
                        macs=(None, '00:00:17:01:24:7a', '02:00:28:12:35:8b')
                    ),
                    'backup': NetUpdates(
                        vlans=(1, 200),
                        macs=(1, '00:00:17:01:a1:53', '02:00:28:12:b2:64')
                    )
                }
            ) for dom0, domu in cluctrl.mReturnDom0DomUPair()
        ]

        monitor_rpm: str = os.path.realpath(LOCAL_MONITOR_RPM_FILE)
        cmds: TestCmds = update_networks_cmds(updates, monitor_rpm)
        self.mPrepareMockCommands(cmds)
        with patch('exabox.ovm.clubonding.get_bond_monitor_rpm_local_path',
                   return_value=monitor_rpm):
            update_networks(ctx, updates)



if __name__ == '__main__':
    unittest.main() 
