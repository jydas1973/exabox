#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/configmgmt.py /main/1 2025/07/21 10:13:43 sauchaud Exp $
#
# configmgmt.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      configmgmt.py - Collects configuration data of Oracle Exadata Cloud Infrastructure Virtual Machines (VMs). 
#
#    DESCRIPTION
#      Contains ConfigCollector Class which contains various configuration gets menthods and their parsing functions.It saves data to the JSON file.
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    sauchaud    07/15/25 - 38157758:ConfigCollector Implementation
#    sauchaud    07/07/25 - Creation
#
import json
import re
from pathlib import Path
import os
from exabox.core.Context import get_gcontext
from exabox.log.LogMgr import ebLogInfo, ebLogTrace, ebLogError, ebLogWarn
from exabox.utils.node import connect_to_host

class ebConfigCollector:
    """
    A class to collect configuration data from Exadata nodes.
    Initializes the ConfigCollector instance.

    :param dom0_domu_pairs: Pairs of dom0 and domu configurations.
    :param cell_list: List of cells to be processed.
    """
    def __init__(self, aDom0DomuPairs, aCellList, aCluCtrl):
        """
        Initializes the ebConfigCollector instance.

        Sets the dom0-domu pairs and cell list for the collector.

        :param aDom0DomuPairs: Pairs of dom0 and domu configurations.
        :param aCellList: List of cells to be processed.
        """
        ebLogTrace(f"Creating ebConfigCollector for dom0_domu_pairs={aDom0DomuPairs} and cell_list={aCellList}")
        self.dom0_domu_pairs = aDom0DomuPairs
        self.cell_list = aCellList
        self._ebox = aCluCtrl

    def mParseMemoryOutput(self, aOutput):
        """
        Parses the output of a memory-related command.

        :param aOutput: Output of the memory-related command, either as a string or a list of lines.
        :return: A dictionary containing memory information.

        Sample Output:
        {
            "total": "29GB",
            "used": "22GB",
            "free": "8GB",
            "details": {
                "raw_used": "20.6GB",
                "buffers_cache": "6.9GB",
                "shared": "0.2GB",
                "kernel_reserved": "0.0GB"
            }
        }
        """
        try:
            lines = aOutput if isinstance(aOutput, list) else aOutput.split(os.linesep)
            mem_line = next((line.split() for line in lines if line.startswith('Mem:')), None)

            mem_fields = ["label", "total", "used", "free", "shared", "buff_cache", "available"]

            if not mem_line or len(mem_line) < len(mem_fields):
                ebLogWarn("Memory line not found or malformed.")
                return {}

            KB_TO_GB_FACTOR = 1048576.0
            total = float(mem_line[1]) / KB_TO_GB_FACTOR
            used = float(mem_line[2]) / KB_TO_GB_FACTOR
            free = float(mem_line[3]) / KB_TO_GB_FACTOR
            shared = float(mem_line[4]) / KB_TO_GB_FACTOR
            buff_cache = float(mem_line[5]) / KB_TO_GB_FACTOR
            available = float(mem_line[6]) / KB_TO_GB_FACTOR

            actual_used = total - available
            actual_free = available
            kernel_reserved = used - (actual_used - buff_cache)

            ebLogTrace(f"Memory stats - total {total:.2f} GB | used {used:.2f} GB | free {free:.2f} GB | available {available:.2f} GB")
            ebLogTrace(f"Calculated - actual_used {actual_used:.2f} GB | kernel_reserved {kernel_reserved:.2f} GB")

            return {
                "total": f"{total:.0f}GB",
                "used": f"{actual_used:.0f}GB",
                "free": f"{actual_free:.0f}GB",
                "details": {
                    "raw_used": f"{used:.1f}GB",
                    "buffers_cache": f"{buff_cache:.1f}GB",
                    "shared": f"{shared:.1f}GB",
                    "kernel_reserved": f"{kernel_reserved:.1f}GB"
                }
            }
        except Exception as e:
            ebLogError(f"Error parsing memory output: {e}")
            return {}

    def mParseCpuOutput(self, aCpuinfoOutput, aUsageOutput=None):
        """
        Parses the output of CPU-related commands.

        :param aCpuinfoOutput: Output of the `lscpu` command.
        :param aUsageOutput: Output of a CPU usage command such as `mpstat`.
        :return: A dictionary containing CPU model, topology, and usage.

        Sample Output:
        {
            "model": "Intel(R) Xeon(R) Platinum 8270Cl Cpu @ 2.70Ghz",
            "sockets": 2,
            "cores_per_socket": 2,
            "threads_per_core": 2,
            "total_cores": 8,
            "usage": "5.3%"
        }
        """
        try:
            cpuinfo_lines = aCpuinfoOutput if isinstance(aCpuinfoOutput, list) else aCpuinfoOutput.split(os.linesep)

            info_keys = {
                "Model name": "model",
                "CPU(s)": "logical_cpus",
                "Core(s) per socket": "cores_per_socket",
                "Thread(s) per core": "threads_per_core",
                "Socket(s)": "sockets"
            }

            cpu_info = {
                "model": "Unknown",
                "logical_cpus": 0,
                "cores_per_socket": 1,
                "threads_per_core": 1,
                "sockets": 1
            }

            for line in cpuinfo_lines:
                line = line.strip()
                for key, field in info_keys.items():
                    if line.startswith(f"{key}:"):
                        try:
                            value = line.split(":", 1)[1].strip()
                            if field == "model":
                                cpu_info[field] = value.title()
                            else:
                                cpu_info[field] = int(value)
                        except Exception as parse_err:
                            ebLogError(f"Failed parsing line '{line}': {parse_err}")

            total_calculated_cores = (
                cpu_info["cores_per_socket"] *
                cpu_info["threads_per_core"] *
                cpu_info["sockets"]
            )
            usage_percent = "N/A"

            # Parse CPU usage output
            if aUsageOutput:
                try:
                    usage_lines = aUsageOutput if isinstance(aUsageOutput, list) else aUsageOutput.split(os.linesep)
                    for line in usage_lines:
                        line = line.strip()
                        if line.lower().startswith("average:") and "all" in line.lower():
                            parts = line.split()
                            if len(parts) > 11:
                                idle = float(parts[11])
                                usage_percent = f"{100 - idle:.1f}%"
                                break
                        elif "%cpu(s):" in line.lower():
                            match = re.search(r'(\d+\.\d+)\s+us', line)
                            if match:
                                usage_percent = f"{match.group(1)}%"
                                break
                except Exception as e:
                    ebLogError(f"Error parsing CPU usage output: {e}")

            ebLogTrace(
                f"CPU stats - model={cpu_info['model']}, total_cores={total_calculated_cores}, usage={usage_percent}"
            )

            return {
                "model": cpu_info["model"],
                "sockets": cpu_info["sockets"],
                "cores_per_socket": cpu_info["cores_per_socket"],
                "threads_per_core": cpu_info["threads_per_core"],
                "total_cores": total_calculated_cores,
                "usage": usage_percent
            }

        except Exception as e:
            ebLogError(f"Error parsing cpuinfo output: {e}")
            return {}

    def mParseNetworkOutput(self, aOutput):
        """
        Parses the output of a network-related command.

        :param output: Output of the network-related command.
        :return: A list of dictionaries containing network interface information.

        Sample Output:
        {
            "interfaces": [
                {
                    "name": "lo",
                    "status": "UP",
                    "ip": "127.0.0.1"
                }
            }
        }
        """
        interfaces = []
        try:
            lines = aOutput.split('\n')
            current_interface = {}
            
            for line in lines:
                line = line.strip()
                
                if re.match(r'^\d+:', line):
                    if current_interface and current_interface.get('ip'):
                        interfaces.append(current_interface)
                    current_interface = {}
                    
                    name_match = re.match(r'^\d+: (\w+):', line)
                    if name_match:
                        current_interface['name'] = name_match.group(1)
                        
                    if '<' in line and '>' in line:
                        flags = line.split('<', 1)[1].split('>', 1)[0]
                        current_interface['status'] = 'UP' if 'UP' in flags else 'DOWN'

                elif re.match(r'^\s*inet ', line):
                    ip_match = re.match(r'^\s*inet (\d+\.\d+\.\d+\.\d+)', line)
                    if ip_match:
                        if 'ip' not in current_interface:
                            current_interface['ip'] = ip_match.group(1)
            
            if current_interface and current_interface.get('ip'):
                interfaces.append(current_interface)

        except Exception as e:
            ebLogError(f"Error parsing network output: {e}")

        return interfaces

    def mParseFilesystemOutput(self, aOutput):
        """
        Parses the output of a filesystem-related command.

        :param output: Output of the filesystem-related command as a list of lines.
        :return: A dictionary containing filesystem configuration information.

        Sample Output:
        {
            "/u01": {
                "total": "15.00GB",
                "used": "5.20GB",
                "free": "9.80GB",
                "use_percent": "35%"
            }
        }
        """
        filesystem_config = {}

        try:
            for line in aOutput:  
                line = line.strip()
                if line:
                    parts = line.split()
                    if len(parts) >= 6:
                        mount_point = parts[5]
                        if mount_point in ['/', '/u01', '/u02', '/var', '/var/log', 
                                        '/home', '/var/log/audit']:
                            
                            size = parts[1]
                            used = parts[2]
                            avail = parts[3]
                            use_pct = parts[4]

                            def to_gb(size_str):
                                """
                                Converts a size string to GB.

                                :param size_str: Size string (e.g., '1T', '1024G', '1024M').
                                :return: Size in GB.
                                """
                                size_str = size_str.upper()
                                if 'T' in size_str:
                                    return float(size_str.replace('T', '')) * 1024
                                elif 'G' in size_str:
                                    return float(size_str.replace('G', ''))
                                elif 'M' in size_str:
                                    return float(size_str.replace('M', '')) / 1024
                                return float(size_str) / (1024**3)

                            filesystem_config[mount_point] = {
                                'total': f"{to_gb(size):.2f}GB",
                                'used': f"{to_gb(used):.2f}GB",
                                'free': f"{to_gb(avail):.2f}GB",
                                'use_percent': use_pct,
                            }
        except Exception as e:
            ebLogError(f"Error parsing filesystem output: {e}")

        return filesystem_config

    def mParseGriddiskOutput(self, aOutput):
        """
        Parses the output of a griddisk-related command.

        :param output: Output of the griddisk-related command.
        :return: A list of dictionaries containing griddisk information.

        Sample Output:
        [
            {
                "cell_disk": "CD_04_iad103712exdcl03",
                "disk_type": "HardDisk",
                "name": "DATAC10_CD_04_iad103712exdcl03",
                "size": "136G",
                "status": "active"
            }
        ]
        """
        griddisks = []
        try:
            for line in aOutput:
                line = line.strip()
                if not line:
                    continue 
                parts = line.split()
                if len(parts) >= 5: 
                    griddisks.append({
                        "name": parts[0],
                        "size": parts[1],
                        "disk_type": parts[2],
                        "status": parts[3],
                        "cell_disk": parts[4]
                    })
        except Exception as e:
            ebLogError(f"Error parsing griddisk output: {e}")

        return griddisks
   
    def mParseAsmdiskOutput(self, aOutput):
        """
        Parses the output of an ASM disk-related command.

        :param output: Output of the ASM disk-related command.
        :return: A list of dictionaries containing ASM disk group information.

        Sample Output: 
        [
            {
                "au_size": 4096,
                "block_size": 512,
                "compatibility": "0",
                "database_compatibility": "Y",
                "free_mb": 5013504,
                "name": "DATAC1",
                "offline_disks": 1567988,
                "redundancy": "HIGH",
                "req_mir_free_mb": 4703964,
                "sector_size": 512,
                "state": "MOUNTED",
                "total_mb": 4194304,
                "usable_file_mb": 0,
                "voting_files": "N"
            }
        ]
        """
        disk_groups = []
        
        for line in aOutput:
            line = line.strip()
            if not line:
                continue
                
            try:
                parts = line.split()
                if len(parts) < 14:  
                    continue

                disk_group = {
                    "state": parts[0],
                    "redundancy": parts[1],
                    "voting_files": parts[2], 
                    "sector_size": int(parts[3]),
                    "block_size": int(parts[4]),
                    "au_size": int(parts[5]),
                    "total_mb": int(parts[6]),
                    "free_mb": int(parts[7]),
                    "req_mir_free_mb": int(parts[8]),
                    "usable_file_mb": int(parts[9]),
                    "offline_disks": int(parts[10]),
                    "compatibility": parts[11],
                    "database_compatibility": parts[12],
                    "name": parts[13].strip('/')  
                }
                disk_groups.append(disk_group)
                
            except (IndexError, ValueError) as e:
                ebLogError(f"Error parsing ASM disk group line: {line}. Error: {str(e)}")
            except Exception as e:
                ebLogError(f"Unexpected error parsing ASM disk group line: {line}. Error: {str(e)}")
                
        return disk_groups

    def mParseScanvipOutput(self, aOutput):
        """
        Parses the output of a scan VIP-related command.

        :param output: Output of the scan VIP-related command.
        :return: A list of dictionaries containing scan VIP resource information.

        Sample Output:
        [
            {
                "ip_address": "10.0.9.124",
                "name": "ora.scan2.vip",
                "scan_name": "idc3716-clu01scan",
                "scan_port": "1521",
                "state": "ONLINE"
            }
        ]
        """
        resources = []
        current_resource = {}
        
        try:
            for line in aOutput:
                line = line.strip()
                
                if not line:
                    if current_resource:  
                        req_resource = {
                            "name": current_resource.get("name", ""),
                            "state": current_resource.get("state", "UNKNOWN"),
                            "ip_address": current_resource.get("usr_ora_vip", ""),
                            "scan_name": current_resource.get("scan_name", ""),
                            "scan_port": "1521"  
                        }
                        resources.append(req_resource)
                        current_resource = {}
                    continue
                    
                if '=' in line:
                    try:
                        key, value = line.split('=', 1)
                        key = key.strip().lower()
                        value = value.strip()

                        if key in ['name', 'state', 'usr_ora_vip', 'scan_name']:
                            current_resource[key] = value
                    except ValueError:
                        continue

            if current_resource:
                req_resource = {
                    "name": current_resource.get("name", ""),
                    "state": current_resource.get("state", "UNKNOWN"),
                    "ip_address": current_resource.get("usr_ora_vip", ""),
                    "scan_name": current_resource.get("scan_name", ""),
                    "scan_port": "1521"
                }
                resources.append(req_resource)
        except Exception as e:
            ebLogError(f"Error parsing scan VIP output: {e}")
            
        return resources
   
    def mParseFilepermissionOutput(self, aOutput):
        """
        Parses the output of a file permission-related command.

        :param output: Output of the file permission-related command.
        :return: A list of dictionaries containing file permission information.

        Sample Output:
        {
            "permissions": "-rw-rw-r--",
            "links": "1",
            "owner": "grid",
            "group": "oinstall",
            "size": "772",
            "month": "Jun",
            "day": "18",
            "time_or_year": "06:55",
            "name": "/etc/oratab"
        }
        """
        permissions_info = []
        try:
            for line in aOutput:
                line = line.strip()
                if not line:
                    continue 
                parts = line.split(None, 8) 
                if len(parts) > 8: 
                    permissions_info.append({
                        "permissions": parts[0],
                        "links": parts[1],
                        "owner": parts[2],
                        "group": parts[3],
                        "size": parts[4],
                        "month": parts[5],
                        "day": parts[6],
                        "time_or_year": parts[7],
                        "name": parts[8] 
                    })
        except Exception as e:
            ebLogError(f"Error parsing file permission output: {e}")
            
        return permissions_info
   
    def mParseVotingdiskOutput(self, aOutput):
        """
        Parses the output of a voting disk-related command.

        :param output: Output of the voting disk-related command.
        :return: A list of dictionaries containing voting disk information.

        Sample Output:
        {
            "disk_group": "DATAC1",
            "file_name": "/dev/exadata_quorum/QD_DATAC1_C3716N11C1",
            "file_universal_id": "9655dbb1a8624f2dbfdf5b5164692731",
            "number": "4",
            "state": "ONLINE",
            "type": "Block"
        }
        """
        voting_disks = []

        try:
            for line in aOutput:
                line = line.strip()

                if line.startswith(("##", "--", "Located")):
                    continue

                if not line:
                    continue

                if line[0].isdigit() and '.' in line:
                    try:
                        parts = line.split()
                        disk_number = parts[0].strip('.')
                        state = parts[1]
                        file_universal_id = parts[2]

                        file_start = line.find('(') + 1
                        file_end = line.find(')')
                        file_name = line[file_start:file_end]

                        dg_start = line.find('[') + 1
                        dg_end = line.find(']')
                        disk_group = line[dg_start:dg_end]

                        disk_type = "ASM" if file_name.startswith("o/") else "Block"

                        voting_disk = {
                            "number": disk_number,
                            "state": state,
                            "file_universal_id": file_universal_id,
                            "file_name": file_name,
                            "disk_group": disk_group,
                            "type": disk_type
                        }
                        voting_disks.append(voting_disk)

                    except (IndexError, ValueError) as e:
                        ebLogError(f"Error parsing voting disk line: {line}. Error: {str(e)}")
                    except Exception as e:
                        ebLogError(f"Unexpected error parsing voting disk line: {line}. Error: {str(e)}")
        except Exception as e:
            ebLogError(f"Unexpected error in parse_votingdisk_output: {str(e)}")

        return voting_disks

    def mGetFileSystemConfig(self, aNode, aNodeId):
        """
        Retrieves the filesystem configuration from a node.

        :param node_connector: Node connector object.
        :param node_id: ID of the node.
        :return: A dictionary representing the filesystem configuration.

        Sample Output:
        Filesystem                                     Size  Used Avail Use% Mounted on
        /dev/mapper/VGExaDb-LVDbSys1                    20G   10G   10G   50%  /
        /dev/mapper/VGExaDbDisk.u01.20.img-LVDBDisk    100G   20G   80G   20%  /u01
        """
        ebLogInfo(f"Collecting file system config for DomU: {aNodeId}")
        _cmd = "/bin/df -h"
        try:
            _, _o, _ = aNode.mExecuteCmd(_cmd)
            _rc = aNode.mGetCmdExitStatus()
            if _rc != 0:
                ebLogError(f"Command '{_cmd}' failed on {aNodeId} with return code {_rc}")
                return {}
            _output = _o.readlines()

            if not _output:
                ebLogError(f"Failed to retrieve file system config from {aNodeId}")
                ebLogError(f"No output received from node {aNodeId} for command '{_cmd}'")
                return {}
            
            ebLogTrace(f"Filesystem configuration from {aNodeId}: ")
            ebLogTrace(json.dumps(self.mParseFilesystemOutput(_output), indent=4))
            return self.mParseFilesystemOutput(_output)
        except Exception as e:
            ebLogError(f"Error retrieving file system config from node {aNodeId}: {str(e)}")
            return {}
        
    def mGetNetworkConfig(self, aNode, aNodeId):
        """
        Retrieves the network configuration from a node.

        :param node_connector: Node connector object.
        :param node_id: ID of the node.
        :return: A dictionary representing the network configuration.

        Sample output:
        2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 ...
            inet 192.168.1.10/24 brd 192.168.1.255 scope global dynamic eth0
        3: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 ...
            inet 127.0.0.1/8 scope host lo
        """
        ebLogInfo(f"Collecting network config for DomU: {aNodeId}")
        _cmd = "/sbin/ip a"
        try:
            _, _o, _ = aNode.mExecuteCmd(_cmd)
            _rc = aNode.mGetCmdExitStatus()
            if _rc != 0:
                ebLogError(f"Command '{_cmd}' failed on {aNodeId} with return code {_rc}")
                return {}
            _output = _o.readlines()
            if _output:
                output = '\n'.join(_output)
                ebLogTrace(f"Network configuration from {aNodeId}: ")
                ebLogTrace(json.dumps(self.mParseNetworkOutput(output), indent=4))
                return self.mParseNetworkOutput(output)
            else:
                ebLogError(f"Failed to retrieve network config from {aNodeId}")
                return {}
        except Exception as e:
            ebLogError(f"Error in mGetNetworkConfig for {aNodeId}: {str(e)}")
            return {}

    def mGetSystemConfig(self, aNode, aNodeId):
        """
        Retrieves the system configuration from a node.

        :param node_connector: Node connector object.
        :param node_id: ID of the node.
        :return: A dictionary representing the system configuration.

        Sample Output:
                        total        used        free     shared  buff/cache   available
            Mem:       16333700     5183920     478228   1203196    10511552    9670160
            Swap:       2097148           0    2097148

        Sample Output (lscpu):
        Model name:          Intel(R) Xeon(R) CPU E5-2676 v3 @ 2.40GHz
        CPU(s):              8
        Thread(s) per core:  2
        Core(s) per socket:  4
        Socket(s):           1
        """
        ebLogInfo(f"Collecting system config for DomU: {aNodeId}")
        memory_cmd = "/usr/bin/free"
        cpuinfo_cmd = "/usr/bin/lscpu"
        usage_cmd = "/usr/bin/mpstat 1 1 | grep -i all" 

        try:
            _, _o, _ = aNode.mExecuteCmd(memory_cmd)
            _rc = aNode.mGetCmdExitStatus()
            if _rc != 0:
                ebLogError(f"Command '{memory_cmd}' failed on {aNodeId} with return code {_rc}")
                return {}
            memory_output = _o.readlines()

            _, _o, _ = aNode.mExecuteCmd(cpuinfo_cmd)
            _rc = aNode.mGetCmdExitStatus()
            if _rc != 0:
                ebLogError(f"Command '{cpuinfo_cmd}' failed on {aNodeId} with return code {_rc}")
                return {}
            cpuinfo_output = _o.readlines()

            _, _o, _ = aNode.mExecuteCmd(usage_cmd)
            _rc = aNode.mGetCmdExitStatus()
            if _rc != 0:
                ebLogError(f"Command '{usage_cmd}' failed on {aNodeId} with return code {_rc}")
                return {}
            usage_output = _o.readlines()
        
            if memory_output and cpuinfo_output and usage_output:
                memory = self.mParseMemoryOutput(memory_output)
                cpu = self.mParseCpuOutput(cpuinfo_output, usage_output)
                ebLogTrace(f"Memory configuration from {aNodeId}: ")
                ebLogTrace(json.dumps(memory, indent=4))
                ebLogTrace(f"CPU configuration from {aNodeId}: ")
                ebLogTrace(json.dumps(cpu, indent=4))
                return {
                    "cpu": cpu,
                    "memory": memory
                }
            else:
                ebLogError(f"Failed to retrieve full system config from {aNodeId}")
                return {}
        except Exception as e:
            ebLogError(f"Error in mGetSystemConfig for {aNodeId}: {str(e)}")
            return {}

    def mGetGridDiskConfig(self, aNode, aCellId):
        """
        Retrieves the Grid Disk configuration from a cell.

        :param node_connector: Node connector object.
        :param cell_id: ID of the cell.
        :return: A list of dictionaries representing the Grid Disk configuration.

        Sample output:
        name        size  disktype  status  cellDisk
        DATA_CD_01  557G  HardDisk  normal  CD_01
        RECO_CD_01  372G  HardDisk  normal  CD_02
        """
        ebLogInfo(f"Collecting grid disk config for DomU: {aCellId}")
        _cmd = "cellcli -e list griddisk attributes name,size,disktype,status,cellDisk"
        try:
            _, _o, _ = aNode.mExecuteCmd(_cmd)
            _rc = aNode.mGetCmdExitStatus()
            if _rc != 0:
                ebLogError(f"Command '{_cmd}' failed on {aCellId} with return code {_rc}")
                return []
            _output = _o.readlines()
            if _output:
                ebLogTrace(f"Grid Disk configuration from {aCellId}: ")
                ebLogTrace(json.dumps(self.mParseGriddiskOutput(_output), indent=4))
                return self.mParseGriddiskOutput(_output)
            else:
                ebLogError(f"Failed to retrieve Grid Disk info from {aCellId}")
                return []
        except Exception as e:
            ebLogError(f"Error in mGetGridDiskConfig for {aCellId}: {str(e)}")
            return []

    def mGetGridConfig(self, aNode, aDomuId):
        """
        Retrieves the Grid configuration from a DomU.

        :param node_connector: Node connector object.
        :param domu_id: ID of the DomU.
        :return: A dictionary representing the Grid configuration.

        Sample output:
        ['/u01/app/19.0.0.0/grid']
        ['19.0.0.0.0']
        """
        ebLogInfo(f"Collecting grid config for DomU: {aDomuId}")
        grid_config = {}
        try:
            # Get grid home from oratab
            _cmd = "grep '^+ASM' /etc/oratab | cut -d: -f2"
            _, _o, _ = aNode.mExecuteCmd(_cmd)
            _rc = aNode.mGetCmdExitStatus()
            if _rc != 0:
                ebLogError(f"Command '{_cmd}' failed on {aDomuId} with return code {_rc}")
                return {}
            _output = _o.readlines()
            grid_home = _output[0].strip() if _output and len(_output) > 0 else "/u01/app/19.0.0.0/grid"
            grid_config['grid_home_path'] = grid_home
            
            # Get grid version
            _cmd = (
                f"sudo -u grid bash -c '"
                f"export ORACLE_HOME={grid_home}; "
                f"{grid_home}/bin/crsctl query crs softwareversion | "
                f"grep -oP \"\\d+\\.\\d+\\.\\d+\\.\\d+\\.\\d+\"'"
            )
            _, _o, _ = aNode.mExecuteCmd(_cmd)
            _rc = aNode.mGetCmdExitStatus()
            if _rc != 0:
                ebLogError(f"Command '{_cmd}' failed on {aDomuId} with return code {_rc}")
                grid_config['grid_version'] = "Unknown"
            _output = _o.readlines()
            grid_config['grid_version'] = _output[0].strip() if _output and len(_output) > 0 else "Unknown"
        except Exception as e:
            ebLogError(f"Error in mGetGridConfig for {aDomuId}: {str(e)}")
            grid_config['grid_version'] = "Error"
        ebLogTrace(f"Grid configuration from {aDomuId}: ")
        ebLogTrace(json.dumps(grid_config, indent=4))
        return grid_config
    

    def mGetFilePermissions(self, aNode, aDomuId, aFilePaths):
        """
        Retrieves the file permissions for a list of file paths on a DomU.

        :param node_connector: Node connector object.
        :param domu_id: ID of the DomU.
        :param file_paths: List of file paths.
        :return: A dictionary representing the file permissions.

        Sample output:
        ['-rw-r--r-- 1 root root 1234 Jan 1 10:00 /etc/oratab']
        """
        ebLogInfo(f"Collecting file permission config for DomU: {aDomuId}")
        permissions_data = {}
        for path in aFilePaths:
            _cmd = f"/bin/ls -l {path}"
            try:
                _, _o, _ = aNode.mExecuteCmd(_cmd)
                _rc = aNode.mGetCmdExitStatus()
                if _rc != 0:
                    ebLogError(f"Command '{_cmd}' failed on {aDomuId} with return code {_rc}")
                    permissions_data[path] = []
                _output = _o.readlines()
                if _output:
                    permissions_data[path] = self.mParseFilepermissionOutput(_output)
                else:
                    ebLogError(f"Failed to retrieve permissions for {path} on {aDomuId}")
                    permissions_data[path] = []
            except Exception as e:
                ebLogError(f"Error retrieving file permissions for {path} on {aDomuId}: {str(e)}")
                permissions_data[path] = []
        ebLogTrace(f"File permissions configuration from {aDomuId}: ")
        ebLogTrace(json.dumps(permissions_data, indent=4))
        return permissions_data
    
    def mGetASMConfig(self, aNode, aDomuId):
        """
        Retrieves the ASM configuration from a DomU.

        :param node_connector: Node connector object.
        :param domu_id: ID of the DomU.
        :return: A list of dictionaries representing the ASM configuration.

        Sample output:
        ['DATAC1  500G  400G  100G  MOUNTED', 'RECOC1  300G  250G  50G  MOUNTED']
        """
        ebLogInfo(f"Collecting ASM config for DomU: {aDomuId}")
        # First get grid home from oratab
        _cmd = "grep '^+ASM' /etc/oratab | cut -d: -f2"
        _, _o, _ = aNode.mExecuteCmd(_cmd)
        _rc = aNode.mGetCmdExitStatus()
        if _rc != 0:
            ebLogError(f"Command '{_cmd}' failed on {aDomuId} with return code {_rc}")
            return {}
        _output = _o.readlines()
        grid_home = _output[0].strip() if _output and len(_output) > 0 else "/u01/app/19.0.0.0/grid"
        
        _cmd = (
            "sudo -u grid bash -c '"
            f"export ORACLE_HOME={grid_home}; "
            "export PATH=$ORACLE_HOME/bin:$PATH; "
            "asmcmd lsdg --suppressheader"
            "'"
        )
        try:
            _, _o, _ = aNode.mExecuteCmd(_cmd)
            _rc = aNode.mGetCmdExitStatus()
            if _rc != 0:
                ebLogError(f"Command '{_cmd}' failed on {aDomuId} with return code {_rc}")
                return []
            _output = _o.readlines()
            if _output:
                ebLogTrace(f"ASM configuration from {aDomuId}: ")
                ebLogTrace(json.dumps(self.mParseAsmdiskOutput(_output), indent=4))
                return self.mParseAsmdiskOutput(_output)
            else:
                ebLogError(f"Failed to retrieve ASM info from {aDomuId}")
                return []
        except Exception as e:
            ebLogError(f"Error in mGetASMConfig for {aDomuId}: {str(e)}")
            return []

    def mGetScanVIPConfig(self, aNode, aDomuId):
        """
        Retrieves the SCAN and VIP configuration from a DomU.

        :param node_connector: Node connector object.
        :param domu_id: ID of the DomU.
        :return: A list of dictionaries representing the SCAN and VIP configuration.

        Sample output:
        [
            "NAME=ora.scan1.vip",
            "STATE=ONLINE",
            "NAME=ora.node1.vip",
            "STATE=ONLINE"
        ]
        """
        ebLogInfo(f"Collecting SCAN and VIP config for DomU: {aDomuId}")
        # First get grid home from oratab
        _cmd = "grep '^+ASM' /etc/oratab | cut -d: -f2"
        _, _o, _ = aNode.mExecuteCmd(_cmd)
        _rc = aNode.mGetCmdExitStatus()
        if _rc != 0:
            ebLogError(f"Command '{_cmd}' failed on {aDomuId} with return code {_rc}")
            return []
        _output = _o.readlines()
        grid_home = _output[0].strip() if _output and len(_output) > 0 else "/u01/app/19.0.0.0/grid"
        
        _cmd = (
            "sudo -u grid bash -c '"
            f"export ORACLE_HOME={grid_home}; "
            "export PATH=$ORACLE_HOME/bin:$PATH; "
            "crsctl status resource -t -f"
            "'"
        )
        try:
            _, _o, _ = aNode.mExecuteCmd(_cmd)
            _rc = aNode.mGetCmdExitStatus()
            if _rc != 0:
                ebLogError(f"Command '{_cmd}' failed on {aDomuId} with return code {_rc}")
                return []
            _output = _o.readlines()
            if _output:
                parsed_output = self.mParseScanvipOutput(_output)
                scan_vips = [
                    res for res in parsed_output 
                    if "ora.scan" in res.get("name", "").lower() 
                    or "ora.vip" in res.get("name", "").lower()
                ]
                
                ebLogTrace(f"SCAN and VIP configuration from {aDomuId}: ")
                ebLogTrace(json.dumps(scan_vips, indent=4))
                return scan_vips
            else:
                ebLogError(f"Failed to retrieve SCAN and VIP info from {aDomuId}")
                return []
        except Exception as e:
            ebLogError(f"Error in mGetScanVIPConfig for {aDomuId}: {str(e)}")
            return []

    def mGetVotingDiskConfig(self, aNode, aDomuId):
        """
        Retrieves the Voting Disk configuration from a DomU.

        :param node_connector: Node connector object.
        :param domu_id: ID of the DomU.
        :return: A list of dictionaries representing the Voting Disk configuration.

        Sample Output:
        ##  STATE  File Universal Id     File Name      Disk group
        1. ONLINE  1234567890123456   (/dev/asm-disk1)   [DATA]
        2. ONLINE  7890123456789012   (/dev/asm-disk2)   [FRA]
        """
        ebLogInfo(f"Collecting Voting Disk config for DomU: {aDomuId}")
        # First get grid home from oratab
        _cmd = "grep '^+ASM' /etc/oratab | cut -d: -f2"
        _, _o, _ = aNode.mExecuteCmd(_cmd)
        _rc = aNode.mGetCmdExitStatus()
        if _rc != 0:
            ebLogError(f"Command '{_cmd}' failed on {aDomuId} with return code {_rc}")
            return []
        _output = _o.readlines()
        grid_home = _output[0].strip() if _output and len(_output) > 0 else "/u01/app/19.0.0.0/grid"
        
        env_cmd = (
            "export ORACLE_BASE=/u01/app/grid; "
            f"export ORACLE_HOME={grid_home}; "
            "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/u01/app/19.0.0.0/grid/lib; "
        )
        _cmd = f"{env_cmd} {grid_home}/bin/crsctl query css votedisk"
        try:
            aNode.mSetUser("grid")
            _, _o, _ = aNode.mExecuteCmd(_cmd)
            _rc = aNode.mGetCmdExitStatus()
            if _rc != 0:
                ebLogError(f"Command '{_cmd}' failed on {aDomuId} with return code {_rc}")
                return []
            _output = _o.readlines()
            if _output:
                ebLogTrace(f"Voting Disk configuration from {aDomuId}: ")
                ebLogTrace(json.dumps(self.mParseVotingdiskOutput(_output), indent=4))
                return self.mParseVotingdiskOutput(_output)
            else:
                ebLogError(f"Failed to retrieve Voting Disk info from {aDomuId}")
                return []
        except Exception as e:
            ebLogError(f"Error in mGetVotingDiskConfig for {aDomuId}: {str(e)}")
            return []

    def mCollectAllConfigs(self):
        """
        Collects all configurations from DomUs and cells.

        :return: A dictionary representing the collected configurations.

        Sample command outputs:
        {
            "VMs": {
                "system": {
                    "cpu": {},
                    "memory": {}
                },
                "network": {
                    "interfaces": []
                },
                "filesystem": {}
            },
            "cluster": {
                "domu": {
                    "grid_configs": {
                        "grid_home_path",
                        "grid_version"
                    },
                    "asm_disk_groups": [],
                    "scan_vips": [],
                    "file_permissions": {},
                    "voting_disks": []
                },
                "cell": {}
            }
        }
        """
        result = {
            "VMs": {},
            "cluster": {
                "domu": {},
                "cell": {}
            }
        }

        for node_id in set([domu for _, domu in self.dom0_domu_pairs] + list(self.cell_list)):
            try:
                with connect_to_host(node_id, get_gcontext()) as _node:
                    ebLogTrace(f"Collecting data for {node_id}")

                    if node_id in [domu for _, domu in self.dom0_domu_pairs]:
                        vm_config = {
                            "system": self.mGetSystemConfig(_node, node_id),
                            "network": {
                                "interfaces": self.mGetNetworkConfig(_node, node_id)
                            },
                            "filesystem": self.mGetFileSystemConfig(_node, node_id)
                        }
                        result["VMs"][node_id] = vm_config

                        cluster_config = {
                            "grid_configs": self.mGetGridConfig(_node, node_id),
                            "asm_disk_groups": self.mGetASMConfig(_node, node_id),
                            "scan_vips": self.mGetScanVIPConfig(_node, node_id),
                            "file_permissions": self.mGetFilePermissions(
                                _node, 
                                node_id, 
                                ["/etc/oratab"]
                            ),
                            "voting_disks": self.mGetVotingDiskConfig(_node, node_id)
                        }
                        result["cluster"]["domu"][node_id] = cluster_config

                    if node_id in self.cell_list:
                        grid_disk_info = self.mGetGridDiskConfig(_node, node_id)
                        result["cluster"]["cell"][node_id] = {
                            "grid_disks": grid_disk_info
                        }
            except Exception as e:
                ebLogError(f"Error collecting data for {node_id}: {str(e)}")

        try:
            self._mSaveOutputToFile(result)
            ebLogTrace(json.dumps(result, indent=4))
        except Exception as e:
            ebLogError(f"Error during final output processing: {str(e)}")

        return result

    def _mSaveOutputToFile(self, aData):
        """
        Saves the output to a file in /exacloud/log/provisioning_configuration/.

        :param aData: Data to save.
        """
        try:
            # Get the path two levels up from the current file
            current_file_path = Path(__file__).resolve()
            exacloud_dir = current_file_path.parents[2]  

            output_dir = exacloud_dir / "log" / "provisioning_configuration"
            output_dir.mkdir(parents=True, exist_ok=True)  

            cluster_name = self._ebox.mGetClusters().mGetCluster().mGetCluName()

            output_file = output_dir / f"{cluster_name}.json"

            if output_file.exists():
                ebLogInfo(f"File {output_file} already exists. Skipping...")
            else:
                with open(output_file, 'w') as f:
                    json.dump(aData, f, indent=4)
                ebLogInfo(f"\nConfiguration saved to: {output_file}")
        except Exception as e:
            ebLogError(f"Error saving configuration to file: {str(e)}")





            
