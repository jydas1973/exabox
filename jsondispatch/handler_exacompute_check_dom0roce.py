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

class ExaComputeCheckDom0Roce(JDHandler):
    # EXIT CODES
    SUCCESS = 0

    def __init__(self, aOptions, aRequestObj = None, aDb=None):

        super().__init__(aOptions, aRequestObj, aDb)
        self.mSetSchemaFile(os.path.abspath(
            "exabox/jsondispatch/schemas/checkdom0roce.json"))

    def mExecute(self) -> Tuple[int, dict]:
        """
        Driver func to check if dom0 roce is configured or not.

        :returns: a tuple[int, dict] containing the return code and a dictionary
                  representing the results
        """

        _rc = 0
        _response = {}


        _roce_configured = False
        if not self.mGetOptions().jsonconf or "roce_config_dom0_name" not in self.mGetOptions().jsonconf:
            raise ExacloudRuntimeError(0x0811, 0xA, f'Missing roce config details in the payload')

        _dom0 = self.mGetOptions().jsonconf.get("roce_config_dom0_name")

        ebLogInfo(f'mCheckRoceConfig: {_dom0}')
        with connect_to_host(_dom0, get_gcontext()) as _node:
            for stre_iface in ('stre0', 'stre1'):
                #Check if stre interface is configured with ip.
                _cmd = f'/usr/sbin/ip a s {stre_iface} | grep inet'
                _node.mExecuteCmdLog(_cmd)
                _ret = _node.mGetCmdExitStatus()
                if _ret == 0:
                    _roce_configured = True
                    ebLogInfo(f'mCheckDom0Roce: Interface {stre_iface} is already configured.')
                else:
                    _roce_configured = False
                    ebLogInfo(f'mCheckDom0Roce: Interface {stre_iface} is not yet configured.')
                    break

        _response = {
                "roce_dom0_configured": _roce_configured
            }

        return _rc, _response

