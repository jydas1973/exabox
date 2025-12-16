#!/bin/python
#
# $Header: ecs/exacloud/exabox/jsondispatch/handler_exacompute_generate_sshkey.py /main/3 2023/06/08 10:52:44 jesandov Exp $
#
# handler_exacompute_generate_sshkey.py
#
# Copyright (c) 2023, Oracle and/or its affiliates.
#
#    NAME
#      handler_exacompute_generate_sshkey.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    06/07/23 - Bug 35470728 - Add validation in case of folder missing
#    jesandov    05/29/23 - 35437791: Correct typo in cmd
#    jesandov    05/18/23 - Creation
#

from multiprocessing import Pool, TimeoutError
import time
import os

from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace
from exabox.utils.common import mCompareModel
from exabox.utils.node import (connect_to_host, node_cmd_abs_path_check,
                               node_exec_cmd, node_read_text_file, node_write_text_file)
from exabox.jsondispatch.jsonhandler import JDHandler


class ExaComputeGenerateSSHHandler(JDHandler):

    def __init__(self, aOptions, aRequestObj = None, aDb=None):

        super().__init__(aOptions, aRequestObj, aDb)
        self.mSetSchemaFile(os.path.abspath("exabox/jsondispatch/schemas/exacompute_generate_ssh_handler.json"))

    def mExecute(self):

        _rc = 0
        _response = {}


        _hostname = self.mGetOptions().jsonconf.get("hostname")
        _fqdn = self.mGetOptions().jsonconf.get("fqdn")

        with connect_to_host(_fqdn, get_gcontext(), timeout=5) as _node:

            # Create folder for the key
            _cmd = "/bin/mkdir -p /root/wallet"
            _node.mExecuteCmdLog(_cmd)

            # Create the key
            _cmd = "/opt/oracle/dbserver/dbms/bin/escli mkkey"
            _cmd = f"{_cmd} --attributes privateKeyFile=/root/wallet/private.key.pem,publicKeyFile=/root/wallet/public.key.pem"
            _node.mExecuteCmd(_cmd)

            # Save the key
            _public = node_read_text_file(_node, "/root/wallet/public.key.pem")
            _private = node_read_text_file(_node, "/root/wallet/private.key.pem")

            _exakms = get_gcontext().mGetExaKms()

            if _private:
                _entry = _exakms.mBuildExaKmsEntry(f"EDV{_fqdn}", "root", _private)
                _exakms.mInsertExaKmsEntry(_entry)

            # Return public key
            _response["publickey"] = _public.strip()

        return (0, _response)


# end of the file
