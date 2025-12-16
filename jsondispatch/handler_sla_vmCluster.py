#!/bin/python
#
# $Header: ecs/exacloud/exabox/jsondispatch/handler_sla_vmCluster.py /main/4 2025/11/05 06:12:56 atgandhi Exp $
#
# handler_sla_vmCluster.py
#
# Copyright (c) 2023, 2025, Oracle and/or its affiliates.
#
#    NAME
#      handler_sla_vmCluster.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    atgandhi    10/01/25 - Enh 38459507 - LOG BASED SLA COLLECTION AND STORE
#                           DOWNTIMES IN DB
#    jiacpeng    02/29/24 - exacs-127809: When server is not connectable,
#                           should return 0 instead of False
#    jiacpeng    08/26/23 - chagne the default status to be -1 to avoid JSON
#                           exception when getting called by ECRA
#    jiacpeng    07/10/23 - vm cluster level SLA handler
#    jiacpeng    07/10/23 - Creation
#

import time
import os
import datetime
import re
from concurrent.futures import ProcessPoolExecutor
import concurrent.futures
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace
from exabox.utils.common import mCompareModel
from exabox.utils.node import (connect_to_host, node_cmd_abs_path_check,
                               node_exec_cmd, node_read_text_file)
from exabox.jsondispatch.jsonhandler import JDHandler

def _to_epoch(time_str):
    try:
        return int(time.mktime(time.strptime(time_str, '%Y-%m-%d %H:%M:%S')))
    except Exception:
        return 0

def _year_aware_strptime(value, fmt):
    now_year = datetime.datetime.utcnow().year
    if fmt == "%b %d %H:%M:%S":
        return datetime.datetime.strptime(f"{value} {now_year}", "%b %d %H:%M:%S %Y")
    return datetime.datetime.strptime(value, fmt)

def _find_intervals(down_list, up_list):
    periods = []
    up_idx = 0
    n_down = len(down_list)
    n_up = len(up_list)

    # Allow "loner" up: if first up is before first down
    if n_up > 0 and (n_down == 0 or up_list[0] < down_list[0]):
        periods.append({
            'down': None,
            'up': up_list[0].strftime("%Y-%m-%d %H:%M:%S")
        })
        up_idx = 1  # Skip the first up, already counted

    for di, down in enumerate(down_list):
        up = None
        while up_idx < n_up and up_list[up_idx] <= down:
            up_idx += 1
        if up_idx < n_up:
            up = up_list[up_idx]
            up_idx += 1
        periods.append({
            'down': down.strftime("%Y-%m-%d %H:%M:%S"),
            'up': up.strftime("%Y-%m-%d %H:%M:%S") if up else None
        })
    return periods

def mExtractDowntimePeriods_with_node(node, host, server_type, start_time, end_time):
    results = {
        'compute': [],
        'network': [],
        'storage': []
    }
    since_epoch = _to_epoch(start_time)
    until_epoch = _to_epoch(end_time) if end_time else float("inf")
    try:
        if server_type == 'compute':
            # One single call for all "Stopped" and "Started" entries for libvirtd
            combined_cmd = (
                f'sudo journalctl -u libvirtd --since "{start_time}" --until "{end_time}" | grep -E "Stopped Virtualization daemon|Started Virtualization daemon"'
            )
            _, combined_out, _ = node_exec_cmd(node, combined_cmd, timeout=12)
            down_list = []
            up_list = []
            if combined_out:
                for line in combined_out.splitlines():
                    m = re.match(r'^(\w+\s+\d+\s+\d+:\d+:\d+)', line)
                    if m:
                        try:
                            dt = _year_aware_strptime(m.group(1), "%b %d %H:%M:%S")
                            if since_epoch < dt.timestamp() < until_epoch:
                                if "Stopped Virtualization daemon" in line:
                                    down_list.append(dt)
                                elif "Started Virtualization daemon" in line:
                                    up_list.append(dt)
                        except Exception:
                            pass
            down_list.sort()
            up_list.sort()
            results['compute'] = _find_intervals(down_list, up_list)

            # NETWORK: unify interface events in a single grep
            combined_net_cmd = (
                f'journalctl -k --since "{start_time}" --until "{end_time}" | grep -i "bondeth0" | grep -Ei "now running without any active interface!|active interface up"'
            )
            _, combined_net_out, _ = node_exec_cmd(node, combined_net_cmd, timeout=10)
            nd_list, nu_list = [], []
            if combined_net_out:
                for line in combined_net_out.splitlines():
                    m = re.match(r'^(\w+\s+\d+\s+\d+:\d+:\d+)', line)
                    if m:
                        try:
                            dt = _year_aware_strptime(m.group(1), "%b %d %H:%M:%S")
                            if since_epoch < dt.timestamp() < until_epoch:
                                if "now running without any active interface!" in line:
                                    nd_list.append(dt)
                                elif "active interface up" in line:
                                    nu_list.append(dt)
                        except Exception:
                            pass
            nd_list.sort()
            nu_list.sort()
            results['network'] = _find_intervals(nd_list, nu_list)
        elif server_type == 'storage':
            log_dir_cmd = "hostname -s"
            _, short_hostname, _ = node_exec_cmd(node, log_dir_cmd, timeout=3)
            short_hostname = short_hostname.strip()
            alert_log_path = f"/opt/oracle/cell/log/diag/asm/cell/{short_hostname}/alert/"
            grep_cmd = (
                f'grep -B 4 -E "Stopped Service CELLSRV|Started Service CELLSRV" {alert_log_path}*log*xml | grep -E "msg time|Stopped Service CELLSRV|Started Service CELLSRV"'
            )
            _, out, _ = node_exec_cmd(node, grep_cmd, timeout=18)
            down_list, up_list = [], []
            acc_time = None
            lines = out.split('\n') if out else []
            for line in lines:
                line = line.strip()
                m_time = re.search(r"msg time=['\"]([^'\"]+)", line)
                if m_time:
                    curr_time_raw = m_time.group(1)
                    try:
                        dt = datetime.datetime.strptime(curr_time_raw[:19], "%Y-%m-%dT%H:%M:%S")
                        acc_time = dt
                    except Exception:
                        acc_time = None
                elif ("Stopped Service CELLSRV" in line or "Started Service CELLSRV" in line) and acc_time:
                    if since_epoch < acc_time.timestamp() < until_epoch:
                        if "Stopped Service CELLSRV" in line:
                            down_list.append(acc_time)
                        elif "Started Service CELLSRV" in line:
                            up_list.append(acc_time)
                    acc_time = None
            down_list.sort()
            up_list.sort()
            results['storage'] = _find_intervals(down_list, up_list)
    except Exception as e:
        pass
    return results

class SLAVmClusterHandler(JDHandler):
    def __init__(self, aOptions, aRequestObj = None, aDb=None):
        super().__init__(aOptions, aRequestObj, aDb)
        self.mSetSchemaFile(os.path.abspath("exabox/jsondispatch/schemas/sla_vmCluster.json"))

    def mExecute(self) -> tuple:
        def _getTimeoutResponse(aName, aType, aStartTime, aEndTime, aClusters):
            return {
                "type": aType,
                "server_status": 0,
                "network_status": 0,
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
                "errors": [
                    (f"Timeout for {aType} server {aName}.")
                ],
                "downtime_periods": {'compute': [], 'network': [], 'storage': []},
                "start_time": aStartTime,
                "end_time": aEndTime,
                "clusters": aClusters
            }
        _rc = 0
        _response = {}
        _endpointPayload = self.mGetOptions().jsonconf.get("SLA")
        _frequency = _endpointPayload["scheduler_frequency"]
        _max_exec_time = _frequency - 30
        _servers = _endpointPayload.get("servers")
        _max_concurrency = _endpointPayload.get("max_concurrency", len(_servers))
        _max_concurrency = min(_max_concurrency, len(_servers))
        with ProcessPoolExecutor(max_workers=_max_concurrency) as _executor:
            _start_time = time.time()
            ebLogInfo("Started SLA measurements collection.")
            _pool = [
                _executor.submit(
                    self.mExecuteSLA,
                    server["hostname"],
                    server["server_type"],
                    _frequency,
                    server["start_time"],
                    server["end_time"],
                    server["clusters"]
                ) for server in _servers
            ]
            try:
                _wait_time = _max_exec_time - (time.time() - _start_time)
                for _res in concurrent.futures.as_completed(_pool, timeout=_wait_time):
                    _response.update(_res.result())
            except TimeoutError:
                ebLogWarn("Timeout Error.")
            except Exception as e:
                ebLogWarn('Exception in handling request[%s]' % (e,))
        for server in _servers:
            _name = server["hostname"]
            _type = server["server_type"]
            _collection_start_time = server["start_time"],
            _collection_end_time = server["end_time"]
            _collection_clusters = server["clusters"]
            if not _response.get(_name):
                _response[_name] = _getTimeoutResponse(_name, _type, _collection_start_time, _collection_end_time, _collection_clusters)
                ebLogWarn("Timeout while performing SLA measurements on "
                    f"cluster {_name}. Try increasing the max_concurrency"
                    " value if this continues to happen for many clusters")
        ebLogInfo("SLA measurements collection finished.")
        return (_rc, _response)

    @staticmethod
    def mExecuteSLA(aHostname: str, aType: str, aFrequency: int, aStartTime: str, aEndTime: str, aClusters: str) -> dict:
        ebLogTrace(f"Running SLA measurement for {aType} server with hostname: {aHostname}")
        _resp_dict = {}
        _resp_dict['type'] = aType
        _resp_dict["timestamp"] = ""
        _resp_dict["server_status"] = -1
        _resp_dict["network_status"] = -1
        _resp_dict["errors"] = []
        _resp_dict["downtime_periods"] = {'compute': [], 'network': [], 'storage': []}
        _resp_dict["start_time"] = aStartTime
        _resp_dict["end_time"] = aEndTime
        _resp_dict["clusters"] = aClusters
        _errors = _resp_dict["errors"]

        try:
            server_status = -1
            network_status = -1
            if aType == 'compute':
                # Only connect to host ONCE and pass the SSH connection to both checks
                with connect_to_host(aHostname, get_gcontext(), timeout=10) as node:
                    server_status, network_status = SLAVmClusterHandler.mComputeCheck_with_node(
                        node, aHostname, aFrequency, aStartTime
                    )
                    _resp_dict["downtime_periods"] = mExtractDowntimePeriods_with_node(
                        node, aHostname, aType, aStartTime, aEndTime
                    )
            elif aType == 'storage':
                with connect_to_host(aHostname, get_gcontext(), timeout=10) as node:
                    server_status = SLAVmClusterHandler.mCellCheck(aHostname)
                    _resp_dict["downtime_periods"] = mExtractDowntimePeriods_with_node(node, aHostname, aType, aStartTime, aEndTime)
            else:
                ebLogWarn(f"Unknown type of server {aType}, allowed server type: compute, cell. Skip SLA status check for {aHostname}")
                _errors.append(f'Unknown type {aType} for server {aHostname} ')
            _resp_dict["start_time"] = aStartTime
            _resp_dict["end_time"] = aEndTime
            _resp_dict["clusters"] = aClusters
            _resp_dict['server_status'] = server_status
            _resp_dict['network_status'] = network_status
            _resp_dict["timestamp"] = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
            return {aHostname: _resp_dict}
        except Exception as e:
            _err_msg = f"Exception during SLA measurement for on server {aHostname}: {e}"
            ebLogWarn(_err_msg)
            _errors.append(_err_msg)
            return {aHostname: _resp_dict}

    @staticmethod
    def mComputeCheck_with_node(node, aDom0: str, aFrequency: int, aLastRunTime: str = "") -> tuple:
        server_status = -1
        network_status = -1

        # ---- server_status based on libvirtd status ----
        # Try systemctl first; fallback to ps/grep if unavailable
        _bin_systemctl = node_cmd_abs_path_check(node, "systemctl")
        if _bin_systemctl:
            _cmd = f"{_bin_systemctl} is-active libvirtd"
            _, _stdout, _ = node_exec_cmd(node, _cmd, timeout=5)
            server_status = 1 if _stdout and _stdout.strip() == "active" else 0
            ebLogInfo(f"Here is the output of check is-active libvirtd {_stdout[0].strip() if _stdout and hasattr(_stdout, '__getitem__') else _stdout}")
        else:
            # Fallback method
            _bin_ps = node_cmd_abs_path_check(node, "ps")
            _bin_grep = node_cmd_abs_path_check(node, "grep")
            _cmd = f"{_bin_ps} -ef | {_bin_grep} libvirtd | {_bin_grep} -v grep"
            _, _stdout, _ = node_exec_cmd(node, _cmd, timeout=5)
            server_status = 1 if _stdout else 0

        _bin_ip = node_cmd_abs_path_check(node, "ip", sbin=True)
        _bin_grep = node_cmd_abs_path_check(node, "grep")
        _cmd = f"{_bin_ip} a s bondeth0 | {_bin_grep} 'state UP'"
        _, _stdout, _ = node_exec_cmd(node, _cmd, timeout=5)
        network_status = 1 if _stdout else 0
        _bin_awk = node_cmd_abs_path_check(node, "awk")
        _cmd = ("/opt/oracle.cellos/exadata.img.hw --get model"
                f" | {_bin_awk} '{{print $NF}}'")
        _, _stdout, _ = node_exec_cmd(node, _cmd, timeout=5)
        if _stdout and _stdout[0] == "X" and mCompareModel(_stdout, "X7") < 0:
            _cmd = f"{_bin_ip} a s bondeth1 | {_bin_grep} 'state UP'"
            _, _stdout, _ = node_exec_cmd(node, _cmd, timeout=5)
            network_status = 1 if _stdout else 0
        return (server_status, network_status)

    @staticmethod
    def mCellCheck(aCell: str) -> int:
        _node = exaBoxNode(get_gcontext())
        if not _node.mIsConnectable(aHost=aCell, aTimeout=5) :
            return 0
        with connect_to_host(aCell, get_gcontext(), timeout=5) as _node2:
            _bin_grep = node_cmd_abs_path_check(_node2, "grep")
            _cmd = ("/opt/oracle/cell/cellsrv/bin/cellcli -e list cell detail"
                   f" | {_bin_grep} cellsrvStatus")
            _, _stdout, _ = node_exec_cmd(_node2, _cmd, timeout=30)
            if not _stdout:
                return 0
            _status = _stdout.split(':')[-1]
            if _status.strip() != 'running':
                return 0
            return 1
        return 0