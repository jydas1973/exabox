#!/bin/python                                                                                                                                                                                                      

import os
from typing import Tuple
from exabox.core.Context import get_gcontext
from exabox.jsondispatch.jsonhandler import JDHandler
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace
from exabox.ovm.cluexascale import ebCluExaScale
from exabox.ovm.clucontrol import exaBoxCluCtrl
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.utils.node import connect_to_host

class ExaComputeDeconfigureDom0Roce(JDHandler):
    # EXIT CODES
    SUCCESS = 0

    def __init__(self, aOptions, aRequestObj = None, aDb=None):

        super().__init__(aOptions, aRequestObj, aDb)
        self.mSetSchemaFile(os.path.abspath(
            "exabox/jsondispatch/schemas/deconfiguredom0roce.json"))

    def mExecute(self) -> Tuple[int, dict]:
        """
        Driver func to check if dom0 roce is configured or not.

        :returns: a tuple[int, dict] containing the return code and a dictionary
                  representing the results
        """

        _rc = 0
        _response = {"iplist": []}
        _clucontrol = exaBoxCluCtrl(get_gcontext())


        _roce_configured = False
        if not self.mGetOptions().jsonconf or "roce_config_dom0_name" not in self.mGetOptions().jsonconf:
            raise ExacloudRuntimeError(0x0811, 0xA, f'Missing roce config details in the payload')

        _dom0 = self.mGetOptions().jsonconf.get("roce_config_dom0_name")

        with connect_to_host(_dom0, get_gcontext()) as _node:
            for stre_iface in ('stre0', 'stre1'):
                #Check if stre interface is configured with ip.
                _cmd = f"/sbin/ifconfig {stre_iface} | grep inet"
                _i, _out, _ = _node.mExecuteCmd(_cmd)
                _ret = _node.mGetCmdExitStatus()
                if _ret == 0:
                    _roce_configured = True
                    ebLogInfo(f'mCheckDom0Roce: Interface {stre_iface} is configured.')
                    if _out:
                        _response["iplist"].append(_out.readlines()[0].strip().split(' ')[1])
                else:
                    ebLogInfo(f'mCheckDom0Roce: Interface {stre_iface} is not configured.')

        if not _roce_configured:
            return _rc, _response

        with connect_to_host(_dom0, get_gcontext()) as _node:
            _cmd = "/usr/sbin/edvutil lsedvnode | grep state"
            _i, _out, _ = _node.mExecuteCmd(_cmd)
            _state = _out.readlines()[0].split(':')[1].strip()

            if _state == "ONLINE":
                _err = "Vault access is still active. Please remove access before deconfiguring RoCE IPs"
                ebLogError(_err)
                raise ExacloudRuntimeError(0x0811, 0xA, _err)

            # VM maker should rollback the RoCE IPs & VLANs setup.
            _cmd = "/opt/exadata_ovm/vm_maker --remove-storage-vlan"
            _node.mExecuteCmdLog(_cmd)

            # Move/Remove qinq file
            _cmd = "mv /etc/exadata/config/initqinq.conf /tmp"
            _node.mExecuteCmdLog(_cmd)

            # Move/Remove stre interfaces
            _cmd = "mv /etc/sysconfig/network-scripts/*stre* /tmp"
            _node.mExecuteCmdLog(_cmd)

            _cmd = "/usr/bin/dbmcli -e \"alter dbserver interconnect1='', interconnect2=''\""
            _node.mExecuteCmdLog(_cmd)

            _clucontrol.mRebootNode(_dom0)

        return _rc, _response

