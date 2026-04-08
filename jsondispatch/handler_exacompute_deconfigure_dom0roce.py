#!/bin/python
#
# $Header: ecs/exacloud/exabox/jsondispatch/handler_exacompute_deconfigure_dom0roce.py /main/4 2026/03/03 22:28:50 siyarlag Exp $
#
# handler_exacompute_deconfigure_dom0roce.py
#
# Copyright (c) 2024, 2026, Oracle and/or its affiliates.
#
#    NAME
#      handler_exacompute_deconfigure_dom0roce.py - JSON dispatch handler to deconfigure Dom0 RoCE networking
#
#    DESCRIPTION
#      Handles the Dom0 RoCE deconfigure workflow, validating payload, checking interface state, disabling services,
#      and rolling back network artifacts through VM maker and dbmcli.
#
#    NOTES
#      None
#
#    MODIFIED   (MM/DD/YY)
#    oespinos    03/11/26 - Bug 39040693 - Add option to pass a list of dom0s.
#    siyarlag    03/03/26 - Bug 38939248 - Toggle exaComputeHost via dbmcli only for 
#                            Dom0 image versions 26.1 and newer.
#    scoral      11/25/25 - Bug 38674332 - Invoke vm_maker rollback to remove storage VLANs
#                            during RoCE deconfigure.
#    dekuckre    02/28/25 - Bug 37614674 - Reset interconnect assignments with dbmcli
#                            when deconfiguring Dom0 RoCE.
#    dekuckre    08/20/24 - Bug 36797873 - Creation.
#

import os
from typing import Tuple
from exabox.core.Context import get_gcontext
from exabox.jsondispatch.jsonhandler import JDHandler
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace
from exabox.ovm.cluexascale import ebCluExaScale
from exabox.ovm.clucontrol import exaBoxCluCtrl
from exabox.utils.common import version_compare
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

        for _dom0 in self.mGetDom0List():
            if self.mCheckDom0Roce(_dom0, _response):
                self.mDeconfigDom0Roce(_dom0)

        return _rc, _response


    def mGetDom0List(self):
        if self.mGetOptions().jsonconf:
            if "roce_config_dom0_name" in self.mGetOptions().jsonconf:
                return [self.mGetOptions().jsonconf.get("roce_config_dom0_name")]
            elif "roce_config_dom0_list" in self.mGetOptions().jsonconf:
                return self.mGetOptions().jsonconf.get("roce_config_dom0_list")

        raise ExacloudRuntimeError(0x0811, 0xA, f'Missing roce config details in the payload')


    def mCheckDom0Roce(self, aDom0, aResponse):
        _dom0 = aDom0
        _response = aResponse
        _roce_configured = False

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

        return _roce_configured


    def mDeconfigDom0Roce(self, aDom0):
        _dom0 = aDom0

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

            _clucontrol = exaBoxCluCtrl(get_gcontext())
            _image_version = _clucontrol.mGetImageVersion(_dom0)
            if _image_version and version_compare(_image_version, "26.1") >= 0:
                _cmd = "/usr/bin/dbmcli -e alter dbserver exaComputeHost=False"
                _node.mExecuteCmdLog(_cmd)
            else:
                ebLogInfo(f"Skipping exaComputeHost disable; image version {_image_version or 'unknown'} is below 26.1")

            _clucontrol.mRebootNode(_dom0)
