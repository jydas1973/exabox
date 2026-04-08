#!/bin/python
#
# $Header: ecs/exacloud/exabox/jsondispatch/handler_lockvm.py /main/1 2025/12/16 21:32:07 scoral Exp $
#
# handler_lockvm.py
#
# Copyright (c) 2025, 2026, Oracle and/or its affiliates.
#
#    NAME
#      handler_lockvm.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      Entrypoint for lockvm jsondispatch command. 
#
#    NOTES
#      None.
#
#    MODIFIED   (MM/DD/YY)
#    scoral      12/14/25 - Creation
#

import os
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace
from exabox.utils.node import (connect_to_host, node_cmd_abs_path_check,
                               node_exec_cmd, node_read_text_file)
from exabox.ovm.cluiptablesroce import ebIpTablesRoCE
from exabox.jsondispatch.jsonhandler import JDHandler


class LockVM(JDHandler):
    def __init__(self, aOptions, aRequestObj=None, aDb=None):
        super().__init__(aOptions, aRequestObj, aDb)
        self.mSetSchemaFile(os.path.abspath("exabox/jsondispatch/schemas/lockvm.json"))

    def mExecute(self) -> tuple:
        _payload = self.mGetOptions().jsonconf
        _clientIPs = _payload.get('clientIPs') if _payload.get('clientIPs') else []

        _callback = None
        if self.mGetOptions().lockvm_operation == 'lockvm':
            _callback = lambda _node, _domu: ebIpTablesRoCE.mLockGuestSSHTraffic(_node, _domu, _clientIPs)
        elif self.mGetOptions().lockvm_operation == 'unlockvm':
            _callback = ebIpTablesRoCE.mUnlockGuestSSHTraffic
        else:
            raise ValueError(f'Bad lockvm_operation "{self.mGetOptions().lockvm_operation}"')

        for _dom0_domus in _payload['dom0domUPairs']:
            with connect_to_host(_dom0_domus['dom0'], get_gcontext()) as _node:
                for _domu in _dom0_domus['domus']:
                    _callback(_node, _domu.split('.')[0])

        return (0, {})