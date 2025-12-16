#!/bin/python
#
# $Header: ecs/exacloud/exabox/jsondispatch/handler_exacompute_vault_delete.py /main/1 2023/09/19 11:32:11 jesandov Exp $
#
# handler_exacompute_vault_delete.py
#
# Copyright (c) 2023, Oracle and/or its affiliates.
#
#    NAME
#      handler_exacompute_vault_delete.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    09/14/23 - Creation
#

from multiprocessing import Pool, TimeoutError
import time
import os

from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace
from exabox.utils.common import mCompareModel
from exabox.utils.node import (connect_to_host, node_cmd_abs_path_check,
                               node_exec_cmd_check, node_read_text_file, node_write_text_file)
from exabox.jsondispatch.jsonhandler import JDHandler


class ExaComputeDeleteVault(JDHandler):

    def __init__(self, aOptions, aRequestObj = None, aDb=None):

        super().__init__(aOptions, aRequestObj, aDb)
        self.mSetSchemaFile(os.path.abspath("exabox/jsondispatch/schemas/exacompute_delete_vault.json"))

    def mExecute(self):

        _rc = 0
        _response = {}


        _hostname = self.mGetOptions().jsonconf.get("hostname")
        _fqdn = self.mGetOptions().jsonconf.get("fqdn")

        with connect_to_host(_fqdn, get_gcontext(), timeout=5) as _node:

            # Disable EDV
            _cmd = "dbmcli -e alter dbserver disable services edv"
            node_exec_cmd_check(_node, _cmd)

            # Disable ESNP
            _cmd = "dbmcli -e alter dbserver disable services esnp"
            node_exec_cmd_check(_node, _cmd)

            # Delete Wallet
            _cmd = "/bin/rm -rf /opt/oracle/dbserver/dbms/deploy/config/eswallet"
            node_exec_cmd_check(_node, _cmd)

            # Delete SSH KEY
            _cmd = "/bin/rm -rf /root/wallet/public.key.pem"
            node_exec_cmd_check(_node, _cmd)

            _cmd = "/bin/rm -rf /root/wallet/private.key.pem"
            node_exec_cmd_check(_node, _cmd)

            # Delete ExaKms Entry
            _exakms = get_gcontext().mGetExaKms()
            _cparams = {"FQDN": f"EDV{_fqdn}"}
            _entries = _exakms.mSearchExaKmsEntries(_cparams)

            for _entry in _entries:
                _exakms.mDeleteExaKmsEntry(_entry)

        return (0, _response)


# end of the file
