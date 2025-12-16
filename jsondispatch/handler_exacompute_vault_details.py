#!/bin/python
#
# $Header: ecs/exacloud/exabox/jsondispatch/handler_exacompute_vault_details.py /main/8 2025/09/20 16:54:53 rbhandar Exp $
#
# handler_exacompute_generate_sshkey.py
#
# Copyright (c) 2023, 2025, Oracle and/or its affiliates.
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
#    rbhandar    09/09/25 - Bug 38338607 - OCI: EXADB-XS: EXACLOUD DOESN'T
#                           UPDATE /ETC/NFTABLES/EXADATA.NFT
#    dekuckre    02/12/25 - 37569625: Use dbmcli to update cellinit.ora
#    aararora    11/29/24 - Bug 37025316: Fix nft rules during vault access
#                           creation
#    jesandov    08/02/23 - 35631645: Review status of EDV after startup
#    jesandov    06/28/23 - 35529335: Update endpoint of exacompute_vault_details
#    jesandov    05/18/23 - Creation
#

from multiprocessing import Pool, TimeoutError
import time
import os
import re

from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace
from exabox.utils.common import mCompareModel
from exabox.utils.node import (connect_to_host, node_cmd_abs_path_check, node_exec_cmd_check,
                               node_exec_cmd, node_read_text_file, node_write_text_file)
from exabox.jsondispatch.jsonhandler import JDHandler
from exabox.core.Error import ExacloudRuntimeError


class ExaComputeVaultDetails(JDHandler):

    def __init__(self, aOptions, aRequestObj = None, aDb=None):

        super().__init__(aOptions, aRequestObj, aDb)
        self.mSetSchemaFile(os.path.abspath("exabox/jsondispatch/schemas/exacompute_vault_details.json"))

    def mGetStateEDV(self, aNode):

        _cmd = f"/usr/sbin/edvutil lsedvnode"
        _, _o, _ = aNode.mExecuteCmd(_cmd)
        _out = _o.read().strip()

        ebLogInfo(f"Result of lsedvnode: {_out}")

        _tokenId = re.search("id:[\s]+(.*)", _out).group(1)
        _state = re.search("state:[\s]+(.*)", _out).group(1)
        _driver = re.search("EDV Driver Version[\s]+(.*)", _out).group(1)

        _result = {
            "token_id": _tokenId,
            "driver_version": _driver,
            "state": _state
        }

        return _result

    def mCheckRulePresent(self, aNode, aInterface):
        """
        Check if the accept rule exist for aInterface on the DOM0
        """
        _node = aNode
        _interface = aInterface
        _cmd = f"/usr/sbin/nft list chain ip filter INPUT | /usr/bin/grep '{_interface}' | /usr/bin/grep 'accept'"
        _node.mExecuteCmdLog(_cmd)
        if _node.mGetCmdExitStatus() != 0:
            return False
        else:
            return True

    def mAddRule(self, aNode, aInterface):
        """
        Add the missing aInterface related nft rule in ol8 environment
        """
        _node = aNode
        _interface = aInterface
        _cmd = f'/usr/sbin/nft insert rule ip filter INPUT iifname "{_interface}" counter packets 0 bytes 0 accept'
        _node.mExecuteCmdLog(_cmd)
        if _node.mGetCmdExitStatus() != 0:
            ebLogWarn(f"We could not add rule for {_interface} in the DOM0.")
        else:
            ebLogInfo(f"Rule for {_interface} was added successfully in DOM0")
    
    def mCommitNFTables(self, aNode):
        """
        Commit the added rule to /etc/nftables/exadata.nft file in ol8 environment
        """
        _cmd = "/bin/cp /etc/nftables/exadata.nft /etc/nftables/exadata.`date +%y.%j.%H.%m.%s`"
        aNode.mExecuteCmdLog(_cmd)
        if aNode.mGetCmdExitStatus() != 0:
            ebLogWarn(f"We could not take a back up /etc/nftables/exadata.nft file")
        else:
            ebLogInfo(f"Back up for /etc/nftables/exadata.nft has taken with date ") 
        _cmd = "/usr/sbin/nft list ruleset > /etc/nftables/exadata.nft"
        aNode.mExecuteCmdLog(_cmd)
        if aNode.mGetCmdExitStatus() != 0:
            ebLogWarn(f"Failed to commit the nft rules to /etc/nftables/exadata.nft file. ")
        else:
            ebLogInfo(f"Successfully committed the nft rules to /etc/nftables/exadata.nft file. ")

    def mExecute(self):

        _rc = 0
        _response = {}

        _hostname = self.mGetOptions().jsonconf.get("fqdn")
        _exarootuser = self.mGetOptions().jsonconf.get("exarootuser")
        _exarooturl = self.mGetOptions().jsonconf.get("exarooturl")
        _vaultaccess = self.mGetOptions().jsonconf.get("vaultaccess")
        _vaultid = self.mGetOptions().jsonconf.get("vaultid")
        _trustcertificates = self.mGetOptions().jsonconf.get("trustcertificates")

        with connect_to_host(_hostname, get_gcontext(), timeout=5) as _node:

            # Check for stre0/stre1 rules - exadb-xs is supported from ol8 onward
            # so, only nft rules are checked
            _rule_addition = False
            _stre0_present = self.mCheckRulePresent(_node, aInterface='stre0')
            _stre1_present = self.mCheckRulePresent(_node, aInterface='stre1')
            if not _stre0_present:
                self.mAddRule(_node, aInterface='stre0')
                _rule_addition = True
            if not _stre1_present:
                self.mAddRule(_node, aInterface='stre1')
                _rule_addition = True
            if _rule_addition:
                self.mCommitNFTables(_node)
            # Create certs.pem
            _cert_str = ""
            for _cert in _trustcertificates:
                _cert_str += _cert

            node_write_text_file(_node, "/root/wallet/certs.pem", _cert_str)

            # Continue with normal commands
            _cmd = f"/opt/oracle/dbserver/dbms/bin/escli mkwallet --wallet /opt/oracle/dbserver/dbms/deploy/config/eswallet"
            node_exec_cmd_check(_node, _cmd, log_stdout_on_error=True)

            _cmd = f'/bin/echo "chwallet --wallet /opt/oracle/dbserver/dbms/deploy/config/eswallet'
            _cmd = f'{_cmd} --attributes exaRootUrl=\\"{_exarooturl}\\"" | /opt/oracle/dbserver/dbms/bin/escli'
            node_exec_cmd_check(_node, _cmd, log_stdout_on_error=True)

            _addWalletCmd = "/opt/oracle/dbserver/dbms/bin/escli chwallet --wallet /opt/oracle/dbserver/dbms/deploy/config/eswallet"
            _cmd = f"{_addWalletCmd} --private-key-file /root/wallet/private.key.pem"
            node_exec_cmd_check(_node, _cmd, log_stdout_on_error=True)

            _cmd = f"{_addWalletCmd} --attributes user={_exarootuser}"
            node_exec_cmd_check(_node, _cmd, log_stdout_on_error=True)

            _cmd = f"{_addWalletCmd} --trusted-cert-file /root/wallet/certs.pem --clear-old-trusted-certs"
            node_exec_cmd_check(_node, _cmd, log_stdout_on_error=True)

            _cmd = f"/bin/chown dbmsvc:dbmusers  /opt/oracle/dbserver/dbms/deploy/config/eswallet"
            node_exec_cmd_check(_node, _cmd, log_stdout_on_error=True)

            _cmd = f"/bin/chown dbmsvc:dbmusers  /opt/oracle/dbserver/dbms/deploy/config/eswallet/*"
            node_exec_cmd_check(_node, _cmd, log_stdout_on_error=True)

            # Ensure MS services are up before updating cellinit.ora below.
            _cmd = "dbmcli -e alter dbserver startup services ms"
            node_exec_cmd_check(_node, _cmd, log_stdout_on_error=True)

            # Create/Update /opt/oracle/dbserver/dbms/deploy/config/cellinit.ora
            _cmd = "dbmcli -e alter dbserver interconnect1=stre0, interconnect2=stre1"
            node_exec_cmd_check(_node, _cmd, log_stdout_on_error=True)

            # Enable EDV
            _cmd = f"/usr/bin/dbmcli -e alter dbserver startup services esnp"
            node_exec_cmd_check(_node, _cmd, log_stdout_on_error=True)

            _cmd = f"/usr/bin/dbmcli -e alter dbserver startup services edv"
            node_exec_cmd_check(_node, _cmd, log_stdout_on_error=True)

            # Wait for EDV to come online
            _state = ""
            _starttime = time.time()
            _elapsed = time.time() - _starttime
            _timeout = 0
            _response = self.mGetStateEDV(_node)

            try:
                _timeout = int(get_gcontext().mCheckConfigOption("exascale_edv_waiting_online_seconds"))
            except (ValueError, TypeError) as e:
                ebLogInfo(f"Invalid value of 'exascale_edv_waiting_online_seconds': {e}")

            if _timeout > 0:

                while _response["state"] != "ONLINE" and _elapsed < _timeout:
                    _response = self.mGetStateEDV(_node)
                    _elapsed = time.time() - _starttime
                    time.sleep(1)

                if _elapsed > _timeout:
                        raise ExacloudRuntimeError(0x0817, 0x0A, 'Exacloud waiting for EDV to come online timedout')

            else:
                ebLogInfo("No timeout specified in 'exascale_edv_waiting_online_seconds'")

        return (0, _response)


# end of the file
