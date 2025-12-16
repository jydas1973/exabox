#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/cluhostaccesscontrol.py /main/1 2025/02/07 17:53:57 jfsaldan Exp $
#
# cluhostaccesscontrol.py
#
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
#
#    NAME
#      cluhostaccesscontrol.py
#
#    DESCRIPTION
#      File to add host_access_control business logic
#
#    NOTES
#      Host access control log is in /var/log/cellos in each node
#      Host access control uses access.conf standard rules,
#       see 'man access.conf'
#
#    MODIFIED   (MM/DD/YY)
#    jfsaldan    11/27/24 - Creation
#

import re
import time
from ipaddress import IPv4Network

from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace
from exabox.utils.node import connect_to_host, node_exec_cmd
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure

def addRoceNetworkHostAccessControl(aOptions):
    """

    Gets the RoCE network values from the payload and will add them
    to the node's exadata access.conf rules, using the 'host_access_control'
    script

    We expect the payload to have a new section 'roce_information'
    "roce_information": {     <<<<<======= NEW DICTIONARY
        "iad103494exdd006.iad1xx4xx0301qf.adminiad1.oraclevcn.com": {
            "stre0_ip": "100.105.74.24",
            "stre1_ip": "100.105.74.25",
            "subnet_mask": "255.255.0.0",
            "vlan_id": "3999"
        }
    }
    """

    # This implementation relies on the guarantee we where given that
    # all the Dom0s RoCE IPs will be in the same network
    def _addRoceNetworkHostAccessControlOnHost(aDom0, aRoceEntry):
        """
        Callback used to set the RoceEntries
        """

        ebLogInfo(f"Detected entry {aRoceEntry} for node {aDom0}")

        # Check a valid network is created
        # It's safe to assume stre0 and stre1 will be in the smae
        # network.
        _ip = aRoceEntry.get("stre0_ip")
        _subnet_mask = aRoceEntry.get("subnet_mask")

        try:
            _roce_network = str(IPv4Network(
                f"{_ip}/{_subnet_mask}",
                strict=False))
        except Exception as e:
            ebLogError("Failed to calculate RoCE Network for entry "
                f"{aRoceEntry}, error: {e}")
            raise e
        else:
            ebLogInfo(f"Adding Network {_roce_network} to {aDom0}")


        # Add network(s) to access.conf rules with host_access_control
        # Retry this one if it fails!
        _bin_hac = "/opt/oracle.cellos/host_access_control"
        _user = "root"
        _entry_exists = False
        with connect_to_host(aDom0, get_gcontext()) as _node:

            # Get current origins-list for root
            _out_status = node_exec_cmd(_node, f"{_bin_hac} access --status")
            ebLogTrace(f"Access control status in {aDom0} is \n{_out_status}")

            _stdout = _out_status.stdout.strip()
            _origins_list = ""
            for _line in _stdout.splitlines():
                if _user in _line:
                    ebLogInfo(f"Found rule for {_user}: {_line}")
                    if str(_roce_network) in _line:
                        ebLogWarn(f"The RoCE network {_roce_network} is "
                            f"already part of the rules for user {_user}, in "
                            f"{aDom0}. Not adding it again")
                        _entry_exists = True
                        continue

                    else:
                        # Create origins list

                        # Remove the starting portion with the user
                        _line = re.sub(f".*:\s+{_user}\s+:\s+", "", _line)

                        # Then we substritute each space with a comma
                        _line = _line.replace(" ", ",")
                        _origins_list = f"{_line},{_roce_network}"
                        ebLogInfo(f"Adding the RoCE network {_roce_network} "
                            f"to the rules for user {_user}. "
                            f"Origins list: \n{_origins_list}")

            if _entry_exists:
                ebLogTrace(f"Skipping node since {aDom0} already "
                    "has entry")
                return
            # Fail if no rule found for user
            if not _origins_list:
                raise ExacloudRuntimeError(
                    0x0811, 0xA, f"No entry found for user {_user}")

            # Build new origins list with the RoCE network
            _out_update = node_exec_cmd(
                _node, f"{_bin_hac} access --add --user={_user} "
                f"--origins='{_origins_list}'")
            _rc = _out_update.exit_code
            ebLogTrace(f"Access control status in {aDom0} is \n{_out_status}")

            _count = 0
            _max_tries = 5
            while _rc != 0 and _count < _max_tries:
                ebLogInfo('Retrying host_access_control update')
                time.sleep(15)

                # Retry
                _out_update = node_exec_cmd(
                    _node, f"{_bin_hac} access --add --user={_user} "
                    f"--origins='{_origins_list}'")
                _rc = _out_update.exit_code

                ebLogTrace(f"Access control status in {aDom0} is \n{_out_status}")
                _count = _count + 1

            if _rc != 0:
                raise ExacloudRuntimeError(
                    0x0808, 0xA,
                    f"Failed to update host access control in {aDom0} after "
                    f"{_max_tries} tries")

        ebLogInfo(f"Updated with success host_access_control rules in {aDom0}")

        # End of inner callback

    if str(get_gcontext().mGetConfigOptions().get(
        "skip_roce_access_control_setup", "false")).lower() == "true":
        ebLogWarn(f"Skipping RoCE Host_Access_Control setup by exabox.conf "
            f"flag")
        return 1

    # Get IP and Network from payload
    if not aOptions.jsonconf:
        raise ExacloudRuntimeError(
            0x0811, 0xA, f'Missing jsonconf')

    _field_roce_information = "roce_information"
    _dict_nodes_roce_info = aOptions.jsonconf.get(_field_roce_information, {})

    if not _dict_nodes_roce_info:
        raise ExacloudRuntimeError(
            0x0811, 0xA, f"Missing field '{_field_roce_information}' in json")


    # Trigger in parallel
    _plist = ProcessManager()

    for _dom0, _entry in _dict_nodes_roce_info.items():
        _p = ProcessStructure(_addRoceNetworkHostAccessControlOnHost, [_dom0, _entry], _dom0)
        _p.mSetMaxExecutionTime(30*60) #30 minutes timeout
        _p.mSetJoinTimeout(5)
        _p.mSetLogTimeoutFx(ebLogWarn)
        _plist.mStartAppend(_p)

    _plist.mJoinProcess()

    return 0
