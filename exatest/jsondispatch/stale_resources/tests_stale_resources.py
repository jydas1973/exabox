#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/jsondispatch/stale_resources/tests_stale_resources.py /main/1 2024/07/16 16:00:25 aararora Exp $
#
# tests_stale_resources.py
#
# Copyright (c) 2024, Oracle and/or its affiliates.
#
#    NAME
#      tests_stale_resources.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aararora    07/12/24 - ER 36759599: Script to detect stale resources.
#    aararora    07/12/24 - Creation
#
import json
import os
import unittest

from unittest import mock
from unittest.mock import patch

from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

from exabox.jsondispatch.handler_stale_resources import StaleResourcesHandler

PAYLOAD = {
    "free_dom0s": ["scaqab10adm01.us.oracle.com"],
    "hostnames":
    [{
       "dom0_fqdn": "scaqab10adm02.us.oracle.com",
       "vm_list": [["scaqab10adm02vm08.us.oracle.com", "scaqab10adm02vm08.us.oracle.com"]]
    }]
}

DOCKER_OUT = """Emulate Docker CLI using podman. Create /etc/containers/nodocker to quiet msg.
CONTAINER ID  IMAGE                                 COMMAND     CREATED     STATUS      PORTS       NAMES
13c783f7a2e5  localhost/exa-hippo-serialmux:latest              5 days ago  Up 5 days               scaqab10adm02vm08-92886-serialmux"""

NAT_RULE = """table ip nat {
    chain PREROUTING {
        type nat hook prerouting priority dstnat; policy accept;
        iifname "vmeth0" ip daddr 10.0.171.52 counter packets 66 bytes 4512 dnat to 169.254.200.2
    }
}"""

BRIDGE_FILTER_RULE="""table bridge filter {
    chain INPUT {
        type filter hook input priority filter; policy accept;
    }
 
    chain FORWARD {
        type filter hook forward priority filter; policy drop;
        counter packets 2627431 bytes 13068535560 jump vm_scaqab10adm02vm08
    }
 
    chain OUTPUT {
        type filter hook output priority filter; policy accept;
    }
 
    chain vm_scaqab10adm02vm08 {
        oifname "vnet*" iifname "bondeth0.637" ip saddr 169.254.169.254 tcp dport 7060 counter packets 26697 bytes 157583298 accept
        oifname "vnet*" iifname "bondeth0.637" ip saddr 169.254.169.254 tcp dport 7070 counter packets 29065 bytes 153734081 accept
        oifname "vnet*" iifname "bondeth0.637" tcp dport 7060 counter packets 0 bytes 0 drop
        oifname "vnet*" iifname "bondeth0.637" tcp dport 7070 counter packets 0 bytes 0 drop
        oifname "vnet*" iifname "bondeth0.638" tcp dport 7060 counter packets 0 bytes 0 drop
        oifname "vnet*" iifname "bondeth0.638" tcp dport 7070 counter packets 0 bytes 0 drop
        oifname "vnet*" iifname "bondeth0.637" counter packets 590233 bytes 3283218779 accept
        iifname "vnet*" oifname "bondeth0.637" counter packets 263779 bytes 32867206 accept
        oifname "vnet*" iifname "bondeth0.638" counter packets 0 bytes 0 accept
        iifname "vnet*" oifname "bondeth0.638" counter packets 6 bytes 168 accept
    }
}"""

class ebTestStaleResourcesHandler(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestStaleResourcesHandler, self).setUpClass(False,False)

    def test_001_mCheckDOM0s(self):

        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = PAYLOAD

        # Prepare mocks
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/brctl show", aRc=0, aStdout="vmbondeth2", aPersist=True),
                ],
                [
                    exaMockCommand("/bin/test -e", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/virsh list --all --name", aRc=0, aStdout="scaqab10adm01vm08.us.oracle.com", aPersist=True),
                    exaMockCommand("/sbin/virsh domiflist", aRc=0, aStdout="vmbondeth3", aPersist=True),
                ],
                [
                    exaMockCommand("/bin/test -e", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ls /EXAVMIMAGES/GuestImages", aRc=0, aStdout="scaqab10adm01vm08.us.oracle.com", aPersist=True),
                    exaMockCommand("/sbin/virsh list --all --name", aRc=0, aStdout="scaqab10adm01vm08.us.oracle.com", aPersist=True)
                ],
                [
                    exaMockCommand("/bin/test -e", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/cat /etc/fstab", aRc=0, aStdout="/dev/VGExaDb/LVDbExaVMImages        /EXAVMIMAGES/GuestImages/scaqab10adm01vm08.us.oracle.com    xfs defaults,nodev  1 0", aPersist=True),
                    exaMockCommand("/sbin/ls /EXAVMIMAGES/GuestImages", aRc=0, aStdout="scaqab10adm01vm08.us.oracle.com", aPersist=True),
                ],
                [
                    exaMockCommand("/bin/test -e", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ls /dev/exc", aRc=0, aStdout="gcv_Vm5687_1_5122", aPersist=True),
                    exaMockCommand("/sbin/cat /etc/fstab", aRc=0, aStdout="/dev/VGExaDb/LVDbExaVMImages        /EXAVMIMAGES/GuestImages/scaqab10adm01vm08.us.oracle.com    xfs defaults,nodev  1 0", aPersist=True),
                ],
                [
                    exaMockCommand("/bin/test -e", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/docker ps", aRc=0, aStdout=DOCKER_OUT, aPersist=True),
                    exaMockCommand("/sbin/ls /dev/exc", aRc=0, aStdout="gcv_Vm5687_1_5122", aPersist=True),
                ],
                [
                    exaMockCommand("/bin/test -e", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/nft list chain ip nat PREROUTING", aRc=0, aStdout=NAT_RULE, aPersist=True),
                ],
                [
                    exaMockCommand("/bin/test -e", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/nft list table bridge filter", aRc=0, aStdout=BRIDGE_FILTER_RULE, aPersist=True),
                    exaMockCommand("/sbin/edvutil volinfo /dev/exc/gcv_Vm5687_1_5122 -l", aRc=1, aPersist=True),
                ],
                [
                    exaMockCommand("/bin/test -e", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/docker ps", aRc=0, aStdout=DOCKER_OUT, aPersist=True),
                ],
                [
                    exaMockCommand("/bin/test -e", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/nft list chain ip nat PREROUTING", aRc=0, aStdout=NAT_RULE, aPersist=True),
                ],
                [
                    exaMockCommand("/bin/test -e", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/virsh domiflist", aRc=0, aStdout="vmbondeth3", aPersist=True),
                ],
                [
                    exaMockCommand("/bin/test -e", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/nft list table bridge filter", aRc=0, aStdout=BRIDGE_FILTER_RULE, aPersist=True),
                ],
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _handler = StaleResourcesHandler(_options)
        _rc, _result = _handler.mExecute()
        print(json.dumps(_result, indent=4))
        self.assertEqual(_rc, 0)

if __name__ == '__main__':
    unittest.main() 