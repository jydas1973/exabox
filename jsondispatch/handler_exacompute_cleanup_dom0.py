#!/bin/python                                                                                                                                                                                                      

import os
from typing import Tuple
from exabox.core.Context import get_gcontext
from exabox.jsondispatch.jsonhandler import JDHandler
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace
from exabox.ovm.cluexascale import ebCluExaScale
from exabox.ovm.clucontrol import exaBoxCluCtrl
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.utils.node import connect_to_host, node_exec_cmd, node_exec_cmd_check
from exabox.ovm.clunetupdate import get_kvm_guest_bridges

GUEST_IMAGES = '/EXAVMIMAGES/GuestImages'
VM_MAKER = '/opt/exadata_ovm/vm_maker'

class ExaComputeCleanupDom0(JDHandler):
    # EXIT CODES
    SUCCESS = 0

    def __init__(self, aOptions, aRequestObj = None, aDb=None):

        super().__init__(aOptions, aRequestObj, aDb)
        self.mSetSchemaFile(os.path.abspath(
            "exabox/jsondispatch/schemas/exacompute_cleanup_dom0.json"))

    def mExecute(self) -> Tuple[int, dict]:
        """
        Driver func to check if dom0 roce is configured or not.

        :returns: a tuple[int, dict] containing the return code and a dictionary
                  representing the results
        """

        _rc = 0
        _response = {}
        _clucontrol = exaBoxCluCtrl(get_gcontext())

        if not self.mGetOptions().jsonconf or "dom0_name" not in self.mGetOptions().jsonconf:
            raise ExacloudRuntimeError(0x0811, 0xA, f'Missing dom0 details in the payload')

        _dom0 = self.mGetOptions().jsonconf.get("dom0_name")

        with connect_to_host(_dom0, get_gcontext()) as _node:
            _cmd = "/bin/virsh list --all --name"
            _srcVMs = node_exec_cmd_check(_node, _cmd).stdout.strip().split()
            for _vmName in _srcVMs:
                _vmBridges = get_kvm_guest_bridges(_node, _vmName)
                _cmd = f"/bin/virsh destroy {_vmName}"
                node_exec_cmd(_node, _cmd)
                _cmd = f"/bin/virsh undefine {_vmName}"
                node_exec_cmd(_node, _cmd)
                _cmd = f"umount /EXAVMIMAGES/GuestImages/{_vmName}"
                node_exec_cmd(_node, _cmd)
                _cmd = f"rmdir /EXAVMIMAGES/GuestImages/{_vmName}"
                node_exec_cmd(_node, _cmd)

            _cmd = "umount /EXAVMIMAGES/GuestImages/*"
            node_exec_cmd(_node, _cmd)

            _cmd = "rmdir /EXAVMIMAGES/GuestImages/*"
            node_exec_cmd(_node, _cmd)

            _cmd = 'sed -i "/\/dev\/exc\/gcv/d" /etc/fstab'
            node_exec_cmd(_node, _cmd)

            _cmd = "brctl show | grep vm | awk '{ print $1 }' | tac"
            _vmBridges = node_exec_cmd_check(_node, _cmd).stdout.strip().split()

            for _bridge in _vmBridges:
                _cmd = f"{VM_MAKER} --remove-bridge {_bridge}"
                node_exec_cmd(_node, _cmd)
                ebLogInfo(f"Bridge {_bridge} removed from {_dom0}")

            _cmd = "rm -f /etc/sysconfig/network-scripts/*eth2??"
            node_exec_cmd(_node, _cmd)
            _cmd = "rm -f /etc/sysconfig/network-scripts/*eth3??"
            node_exec_cmd(_node, _cmd)
            _cmd = "rm -f /etc/sysconfig/network-scripts/ifcfg-eth0.???"
            node_exec_cmd(_node, _cmd)
            _cmd = "rm -f /etc/sysconfig/network-scripts/ifcfg-vmeth0.*"
            node_exec_cmd(_node, _cmd)
            _cmd = "rm -f /etc/sysconfig/network-scripts/ifcfg-vmeth0:*"
            node_exec_cmd(_node, _cmd)

            _clucontrol.mRebootNode(_dom0)

        return _rc, _response

