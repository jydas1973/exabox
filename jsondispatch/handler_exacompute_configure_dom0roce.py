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

class ExaComputeConfigureDom0Roce(JDHandler):
    # EXIT CODES
    SUCCESS = 0

    def __init__(self, aOptions, aRequestObj = None, aDb=None):

        super().__init__(aOptions, aRequestObj, aDb)
        self.mSetSchemaFile(os.path.abspath(
            "exabox/jsondispatch/schemas/configuredom0roce.json"))

    def mExecute(self) -> Tuple[int, dict]:
        """
        Driver func to configure dom0 roce stre0 and stre1 interfaces.

        :returns: a tuple[int, dict] containing the return code and a dictionary
                  representing the results
        """

        _rc = 0
        _response = {}
        _roce_configured = False
        _clucontrol = exaBoxCluCtrl(get_gcontext())


        if not self.mGetOptions().jsonconf or "roce_config_dom0_name" not in self.mGetOptions().jsonconf or "stre0_ip" not in self.mGetOptions().jsonconf:
            raise ExacloudRuntimeError(0x0811, 0xA, f'Missing roce config details in the payload')

        _dom0 = self.mGetOptions().jsonconf.get("roce_config_dom0_name")
        _ip = self.mGetOptions().jsonconf.get("stre0_ip")
        ebLogInfo(f'mConfigureDom0Roce: {_dom0} : {_ip}')
        _vlan_id = get_gcontext().mCheckConfigOption('exadbxs_storage_vlanid')
        if _vlan_id is None:
            _vlan_id = "3999"
            #3999 is the vlan allocated for exadbxs exadata storage
        _netmask = get_gcontext().mCheckConfigOption('exadbxs_stre_netmask')
        if _netmask is None:
            _netmask = "255.255.0.0"
            #stre interfaces are allocated 'class B' address from ecra. Hence this netmask of 255.255.0.0

        with connect_to_host(_dom0, get_gcontext()) as _node:
            _cmd = f'/usr/sbin/vm_maker --set --storage-vlan {_vlan_id} --ip {_ip} --netmask {_netmask}'
            _node.mExecuteCmdLog(_cmd)
            _ret = _node.mGetCmdExitStatus()
            if _ret != 0:
                _msg = f'mConfigureDom0Roce: Unable to configure the stre interface'
                ebLogError(_msg)
                raise ExacloudRuntimeError(0x0811, 0xA, _msg)
            else:
                ebLogInfo(f'mConfigureDom0Roce: stre iface configuration done. Will reboot the node now')
            _clucontrol.mRebootNode(_dom0)

        with connect_to_host(_dom0, get_gcontext()) as _node:
            #Validate interfaces are properly set.
            #stre0 should be set to the input ip.
            _node.mExecuteCmdLog(f'/usr/sbin/ip a s stre0 | grep {_ip}')
            _ret = _node.mGetCmdExitStatus()
            if _ret == 0:
                ebLogInfo(f'mCheckDom0Roce: Interface stre0 is configured successfully.')
            else:
                _msg = f'mCheckDom0Roce: Interface stre0 is not configured.'
                ebLogError(_msg)
                raise ExacloudRuntimeError(0x0811, 0xA, _msg)

            #stre1 will be set with the next subsequent ip-adress. Hence check if any ip is configured.
            _node.mExecuteCmdLog(f'/usr/sbin/ip a s stre1 | grep inet')
            _ret = _node.mGetCmdExitStatus()
            if _ret == 0:
                ebLogInfo(f'mCheckDom0Roce: Interface stre1 is configured successfully.')
            else:
                _msg = f'mCheckDom0Roce: Interface stre1 is not configured.'
                ebLogError(_msg)
                raise ExacloudRuntimeError(0x0811, 0xA, _msg)

        return _rc, _response
                                                                                                                                                            
