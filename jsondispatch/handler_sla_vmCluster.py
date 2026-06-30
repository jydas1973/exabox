#!/bin/python
#
# $Header: ecs/exacloud/exabox/jsondispatch/handler_sla_vmCluster.py /main/6 2026/02/09 06:20:21 atgandhi Exp $
#
# handler_sla_vmCluster.py
#
# Copyright (c) 2023, 2026, Oracle and/or its affiliates.
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
#    atgandhi    04/27/26 - Bug 39263024 - EXACS - SECURITY SCAN FINDINGS IN
#                           EXABOX/JSONDISPATCH/HANDLER_SLA_VMCLUSTER.PY
#    atgandhi    02/01/26 - Bug 38910261 - EXACS:SLA NOT SET TO 0 AFTER
#                           SLA_SERVER_MAX_TIMEOUT EXPIRY WHEN ADMIN NETWORK
#                           (ETH0) IS DOWN
#    atgandhi    11/26/25 - 38675169: No SLA collection during blackout
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
import random
from concurrent.futures import ProcessPoolExecutor
import concurrent.futures
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace
from exabox.utils.common import mCompareModel
from exabox.utils.node import (connect_to_host, node_cmd_abs_path_check,
                               node_exec_cmd, node_read_text_file)
from exabox.jsondispatch.jsonhandler import JDHandler

_SLA_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
_SAFE_HOSTNAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")

def _to_epoch(time_str):
    try:
        return int(time.mktime(time.strptime(time_str, _SLA_TIME_FORMAT)))
    except Exception:
        return 0

def _validate_sla_time(time_str, allow_empty=False):
    if allow_empty and not time_str:
        return None
    if not isinstance(time_str, str):
        raise ValueError("SLA time must be a string")
    dt = datetime.datetime.strptime(time_str, _SLA_TIME_FORMAT)
    if dt.strftime(_SLA_TIME_FORMAT) != time_str:
        raise ValueError("SLA time must match YYYY-MM-DD HH:MM:SS")
    return time_str

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
        while up_idx < n_up and up_list[up_idx] < down:
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
        safe_start_time = _validate_sla_time(start_time)
        safe_end_time = _validate_sla_time(end_time, allow_empty=True)
        if server_type == 'compute':
            # One single call for all "Stopped" and "Started" entries for libvirtd
            combined_cmd = ["sudo", "journalctl", "-u", "libvirtd", "--since", safe_start_time]
            if safe_end_time:
                combined_cmd.extend(["--until", safe_end_time])
            _, combined_out, _ = node_exec_cmd(node, combined_cmd, timeout=12)
            down_list = []
            up_list = []
            if combined_out:
                for line in combined_out.splitlines():
                    if ("Stopped Virtualization daemon" not in line and
                            "Started Virtualization daemon" not in line):
                        continue
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
            combined_net_cmd = ["journalctl", "-k", "--since", safe_start_time]
            if safe_end_time:
                combined_net_cmd.extend(["--until", safe_end_time])
            _, combined_net_out, _ = node_exec_cmd(node, combined_net_cmd, timeout=10)
            nd_list, nu_list = [], []
            if combined_net_out:
                for line in combined_net_out.splitlines():
                    lower_line = line.lower()
                    if "bondeth0" not in lower_line:
                        continue
                    if ("now running without any active interface!" not in lower_line and
                            "active interface up" not in lower_line):
                        continue
                    m = re.match(r'^(\w+\s+\d+\s+\d+:\d+:\d+)', line)
                    if m:
                        try:
                            dt = _year_aware_strptime(m.group(1), "%b %d %H:%M:%S")
                            if since_epoch < dt.timestamp() < until_epoch:
                                if "now running without any active interface!" in lower_line:
                                    nd_list.append(dt)
                                elif "active interface up" in lower_line:
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
            if not _SAFE_HOSTNAME_RE.match(short_hostname):
                raise ValueError("Unexpected storage hostname format")
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
                "server_status": -1,
                "network_status": -1,
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
        if _servers:
            _servers = random.sample(_servers, len(_servers))
        _max_concurrency = _endpointPayload.get("max_concurrency", len(_servers))
        _max_ssh_timeout = _endpointPayload.get("max_ssh_timeout", 10)
        _max_concurrency = min(_max_concurrency, len(_servers))
        with ProcessPoolExecutor(max_workers=_max_concurrency) as _executor:
            _start_time = time.time()
            ebLogInfo("Started SLA measurements collection.")
            _pool = []
            _future_to_server = {}
            for server in _servers:
                _future = _executor.submit(
                    self.mExecuteSLA,
                    server["hostname"],
                    server["server_type"],
                    _frequency,
                    _max_ssh_timeout,
                    server["start_time"],
                    server["end_time"],
                    server["clusters"],
                    server["blackout_status"]
                )
                _pool.append(_future)
                _future_to_server[_future] = server

            _completed_futures = set()
            _wait_time = _max_exec_time - (time.time() - _start_time)
            _timeout_occurred = False
            try:
                for _res in concurrent.futures.as_completed(
                        _pool,
                        timeout=max(_wait_time, 0)):
                    _completed_futures.add(_res)
                    try:
                        _result = _res.result()
                        _response.update(_result)
                    except Exception as e:
                        _rc = 1
                        ebLogWarn('Exception in handling request[%s]' % (e,))
            except concurrent.futures.TimeoutError as e:
                _timeout_occurred = True
                _rc = 1
                _unfinished = [
                    _future_to_server[_f]["hostname"]
                    for _f in _pool if not _f.done()
                ]
                _unfinished_count = len(_unfinished)
                ebLogWarn(
                    "Timeout while waiting for SLA futures. "
                    f"{_unfinished_count} futures unfinished: {_unfinished}"
                )
            finally:
                for _future in _pool:
                    if _future.done() and _future not in _completed_futures:
                        try:
                            _result = _future.result()
                            _response.update(_result)
                            _completed_futures.add(_future)
                        except Exception as e:
                            _rc = 1
                            ebLogWarn('Exception in handling request[%s]' % (e,))
                    elif not _future.done():
                        _future.cancel()

            if _timeout_occurred:
                ebLogWarn(
                    "Timeout Error. Outstanding futures were cancelled; "
                    "using fallback timeout responses."
                )
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
    def mExecuteSLA(aHostname: str, aType: str, aFrequency: int, aMaxSshTimeout: int, aStartTime: str, aEndTime: str, aClusters: str, aBlackoutStatus: int) -> dict:
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
        _resp_dict["blackout_status"] = aBlackoutStatus
        _errors = _resp_dict["errors"]

        try:
            # check if the host is currently in blackout
            if _resp_dict["blackout_status"] == 1:
                _resp_dict["server_status"] = 1
                if aType == 'compute':
                    _resp_dict["network_status"] = 1
                _resp_dict["timestamp"] = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
                return {aHostname: _resp_dict}

            server_status = -1
            network_status = -1
            if aType == 'compute':
                # Only connect to host ONCE and pass the SSH connection to both checks
                _node = exaBoxNode(get_gcontext())
                if _node.mIsConnectable(aHost=aHostname, aTimeout=aMaxSshTimeout):
                    with connect_to_host(aHostname, get_gcontext(), timeout=aMaxSshTimeout) as node:
                        server_status, network_status = SLAVmClusterHandler.mComputeCheck_with_node(
                            node, aHostname, aFrequency, aStartTime
                        )
                        _resp_dict["downtime_periods"] = mExtractDowntimePeriods_with_node(
                            node, aHostname, aType, aStartTime, aEndTime
                        )
                else:
                    ebLogInfo(f"Host {aHostname} is not connectable. Setting server_status and network_status to -1.")
            elif aType == 'storage':
                _node = exaBoxNode(get_gcontext())
                if _node.mIsConnectable(aHost=aHostname, aTimeout=aMaxSshTimeout):
                    with connect_to_host(aHostname, get_gcontext(), timeout=aMaxSshTimeout) as node:
                        server_status = SLAVmClusterHandler.mCellCheck_with_node(node)
                        _resp_dict["downtime_periods"] = mExtractDowntimePeriods_with_node(
                            node, aHostname, aType, aStartTime, aEndTime
                        )
                else:
                    ebLogInfo(f"Host {aHostname} is not connectable. Setting server_status and network_status to -1.")
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
    def mCellCheck_with_node(node) -> int:
        _bin_grep = node_cmd_abs_path_check(node, "grep")
        _cmd = ("/opt/oracle/cell/cellsrv/bin/cellcli -e list cell detail"
               f" | {_bin_grep} cellsrvStatus")
        _, _stdout, _ = node_exec_cmd(node, _cmd, timeout=10)
        if not _stdout:
            return 0
        _status = _stdout.split(':')[-1]
        return 1 if _status.strip() == 'running' else 0

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

