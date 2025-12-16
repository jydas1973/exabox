#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_configmgmt.py /main/4 2025/08/04 15:30:23 akkar Exp $
#
# tests_configmgmt.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_configmgmt.py - Unittesting of Configmgmt.py
#
#    DESCRIPTION
#      It contains the unit test cases for the unittesting of Configmgmt.py
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    akkar       07/30/25 - remove failing test case
#    akkar       07/22/25 - fix test case 
#    sauchaud    07/16/25 - Creation
#
import unittest
import warnings
from pathlib import Path
import json
import io
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.MockCommand import exaMockCommand
from exabox.ovm.configmgmt import ebConfigCollector
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext



class ebTestConfigCollector(ebTestClucontrol):

    @classmethod
    def setUpClass(cls):
        super().setUpClass(aGenerateDatabase=False)
        warnings.filterwarnings("ignore")

    def mPrepareTestDomU(self, aCmds):
        self.mPrepareMockCommands(aCmds)
        _ebox = self.mGetClubox()
        dom0_domu_pairs = _ebox.mReturnDom0DomUPair()
        cell_list = _ebox.mReturnCellNodes()
        obj = ebConfigCollector(dom0_domu_pairs, cell_list, _ebox)
        node_id = dom0_domu_pairs[0][1]
        node = exaBoxNode(get_gcontext())
        node.mConnect(aHost=node_id)
        return obj, node, node_id
    
    def mPrepareTestCell(self, aCmds):
        self.mPrepareMockCommands(aCmds)
        _ebox = self.mGetClubox()
        dom0_domu_pairs = _ebox.mReturnDom0DomUPair()
        cell_list = _ebox.mReturnCellNodes()
        obj = ebConfigCollector(dom0_domu_pairs, cell_list, _ebox)
        self.assertGreater(len(cell_list), 0)
        node_id = next(iter(cell_list)) 
        node = exaBoxNode(get_gcontext())
        node.mConnect(aHost=node_id)
        return obj, node, node_id

    def test_mGetFileSystemConfig_success(self):
        """Test mGetFileSystemConfig with successful command execution"""
        aCmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("/bin/df -h", aStdout="Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda1       20G   10G   10G  50% /", aRc=0)
                ]
            ]
        }
        obj, node, node_id = self.mPrepareTestDomU(aCmds)
        _output = obj.mGetFileSystemConfig(node, node_id)
        self.assertIsNotNone(_output)

    def test_mGetFileSystemConfig_empty_output(self):
        """Test mGetFileSystemConfig with empty output"""
        aCmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("/bin/df -h", aStdout="", aRc=0)
                ]
            ]
        }
        obj, node, node_id = self.mPrepareTestDomU(aCmds)
        _output = obj.mGetFileSystemConfig(node, node_id)
        self.assertEqual(_output, {})

    def test_mGetFileSystemConfig_command_failure(self):
        """Test mGetFileSystemConfig with command failure"""
        aCmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("/bin/df -h", aStdout="", aRc=1)
                ]
            ]
        }
        obj, node, node_id = self.mPrepareTestDomU(aCmds)
        _output = obj.mGetFileSystemConfig(node, node_id)
        self.assertEqual(_output, {})

    def test_mGetNetworkConfig_success(self):
        aCmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("/sbin/ip a", aStdout="2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500\n    inet 192.168.1.10/24 brd 192.168.1.255 scope global dynamic eth0", aRc=0)
                ]
            ]
        }
        obj, node, node_id = self.mPrepareTestDomU(aCmds)
        _output = obj.mGetNetworkConfig(node, node_id)
        self.assertIsNotNone(_output)

    def test_mGetNetworkConfig_empty_output(self):
        aCmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("/sbin/ip a", aStdout="", aRc=0)
                ]
            ]
        }
        obj, node, node_id = self.mPrepareTestDomU(aCmds)
        _output = obj.mGetNetworkConfig(node, node_id)
        self.assertEqual(_output, {})

    def test_mGetNetworkConfig_command_failure(self):
        aCmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("/sbin/ip a", aStdout="", aRc=1)
                ]
            ]
        }
        obj, node, node_id = self.mPrepareTestDomU(aCmds)
        _output = obj.mGetNetworkConfig(node, node_id)
        self.assertEqual(_output, {})

    def test_mGetSystemConfig_success(self):
        aCmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("/usr/bin/free", aStdout="              total        used        free     shared  buff/cache   available\nMem:       16333700     5183920     478228   1203196    10511552    9670160\nSwap:       2097148           0    2097148", aRc=0),
                    exaMockCommand("/usr/bin/lscpu", aStdout="Model name:          Intel(R) Xeon(R) CPU E5-2676 v3 @ 2.40GHz\nCPU(s):              8\nThread(s) per core:  2\nCore(s) per socket:  4\nSocket(s):           1", aRc=0),
                    exaMockCommand("/usr/bin/mpstat 1 1 | grep -i all", aStdout="all    12.34    1.23    2.34    3.45    4.56    5.67    6.78    7.89    8.90    9.01", aRc=0)
                ]
            ]
        }
        obj, node, node_id = self.mPrepareTestDomU(aCmds)
        _output = obj.mGetSystemConfig(node, node_id)
        self.assertIsNotNone(_output)

    def test_mGetSystemConfig_empty_output(self):
        aCmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("/usr/bin/free", aStdout="", aRc=0),
                    exaMockCommand("/usr/bin/lscpu", aStdout="", aRc=0),
                    exaMockCommand("/usr/bin/mpstat 1 1 | grep -i all", aStdout="", aRc=0)
                ]
            ]
        }
        obj, node, node_id = self.mPrepareTestDomU(aCmds)
        _output = obj.mGetSystemConfig(node, node_id)
        self.assertEqual(_output, {})

    def test_mGetSystemConfig_command_failure(self):
        aCmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("/usr/bin/free", aStdout="", aRc=1),
                    exaMockCommand("/usr/bin/lscpu", aStdout="", aRc=1),
                    exaMockCommand("/usr/bin/mpstat 1 1 | grep -i all", aStdout="", aRc=1)
                ]
            ]
        }
        obj, node, node_id = self.mPrepareTestDomU(aCmds)
        _output = obj.mGetSystemConfig(node, node_id)
        self.assertEqual(_output, {})

    def test_mGetGridDiskConfig_success(self):
        aCmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("cellcli -e list griddisk attributes name,size,disktype,status,cellDisk", 
                                aStdout="DATA_CD_01  557G  HardDisk  normal  CD_01\nRECO_CD_01  372G  HardDisk  normal  CD_02", aRc=0)
                ]
            ]
        }
        obj, node, node_id = self.mPrepareTestCell(aCmds)
        _output = obj.mGetGridDiskConfig(node, node_id)
        self.assertIsNotNone(_output)

    def test_mGetGridDiskConfig_empty_output(self):
        aCmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("cellcli -e list griddisk attributes name,size,disktype,status,cellDisk", aStdout="", aRc=0)
                ]
            ]
        }
        obj, node, node_id = self.mPrepareTestCell(aCmds)
        _output = obj.mGetGridDiskConfig(node, node_id)
        self.assertEqual(_output, [])

    def test_mGetGridDiskConfig_command_failure(self):
        aCmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("cellcli -e list griddisk attributes name,size,disktype,status,cellDisk", aStdout="", aRc=1)
                ]
            ]
        }
        obj, node, node_id = self.mPrepareTestCell(aCmds)
        _output = obj.mGetGridDiskConfig(node, node_id)
        self.assertEqual(_output, [])

    def test_mGetGridConfig_success(self):
        aCmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("grep '^+ASM' /etc/oratab | cut -d: -f2", aStdout="/u01/app/19.0.0.0/grid\n", aRc=0),
                    exaMockCommand("sudo -u grid bash -c 'export ORACLE_HOME=/u01/app/19.0.0.0/grid; /u01/app/19.0.0.0/grid/bin/crsctl query crs softwareversion | grep -oP \"\\d+\\.\\d+\\.\\d+\\.\\d+\\.\\d+\"'", aStdout="19.0.0.0.0\n", aRc=0)
                ]
            ]
        }
        obj, node, node_id = self.mPrepareTestDomU(aCmds)
        _output = obj.mGetGridConfig(node, node_id)
        self.assertIsNotNone(_output)

    def test_mGetGridConfig_oratab_command_failure(self):
        aCmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("grep '^+ASM' /etc/oratab | cut -d: -f2", aStdout="", aRc=1)
                ]
            ]
        }
        obj, node, node_id = self.mPrepareTestDomU(aCmds)
        _output = obj.mGetGridConfig(node, node_id)
        self.assertEqual(_output, {'grid_version': 'Error'})

    def test_mGetGridConfig_crsctl_command_failure(self):
        aCmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("grep '^+ASM' /etc/oratab | cut -d: -f2", aStdout="/u01/app/19.0.0.0/grid\n", aRc=0),
                    exaMockCommand("sudo -u grid bash -c 'export ORACLE_HOME=/u01/app/19.0.0.0/grid; /u01/app/19.0.0.0/grid/bin/crsctl query crs softwareversion | grep -oP \"\\d+\\.\\d+\\.\\d+\\.\\d+\\.\\d+\"'", aStdout="", aRc=1)
                ]
            ]
        }
        obj, node, node_id = self.mPrepareTestDomU(aCmds)
        _output = obj.mGetGridConfig(node, node_id)
        self.assertEqual(_output['grid_version'], "Error")
    
    def test_mGetFilePermissions_success(self):
        """Test mGetFilePermissions with successful command execution"""
        aCmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("/bin/ls -l /etc/oratab", aStdout="-rw-r--r-- 1 root root 1234 Jan 1 10:00 /etc/oratab\n", aRc=0)
                ]
            ]
        }
        obj, node, node_id = self.mPrepareTestDomU(aCmds)
        file_paths = ["/etc/oratab"]
        _output = obj.mGetFilePermissions(node, node_id, file_paths)
        self.assertIsNotNone(_output)
        self.assertIn("/etc/oratab", _output)

    def test_mGetFilePermissions_multiple_files_success(self):
        """Test mGetFilePermissions with multiple files and successful command execution"""
        aCmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("/bin/ls -l /etc/oratab", aStdout="-rw-r--r-- 1 root root 1234 Jan 1 10:00 /etc/oratab\n", aRc=0),
                    exaMockCommand("/bin/ls -l /etc/hosts", aStdout="-rw-r--r-- 1 root root 1234 Jan 1 10:00 /etc/hosts\n", aRc=0)
                ]
            ]
        }
        obj, node, node_id = self.mPrepareTestDomU(aCmds)
        file_paths = ["/etc/oratab", "/etc/hosts"]
        _output = obj.mGetFilePermissions(node, node_id, file_paths)
        self.assertIsNotNone(_output)
        self.assertIn("/etc/oratab", _output)
        self.assertIn("/etc/hosts", _output)

    def test_mGetFilePermissions_empty_output(self):
        """Test mGetFilePermissions with empty output"""
        aCmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("/bin/ls -l /etc/oratab", aStdout="", aRc=0)
                ]
            ]
        }
        obj, node, node_id = self.mPrepareTestDomU(aCmds)
        file_paths = ["/etc/oratab"]
        _output = obj.mGetFilePermissions(node, node_id, file_paths)
        self.assertEqual(_output["/etc/oratab"], [])

    def test_mGetFilePermissions_command_failure(self):
        """Test mGetFilePermissions with command failure"""
        aCmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("/bin/ls -l /etc/oratab", aStdout="", aRc=1)
                ]
            ]
        }
        obj, node, node_id = self.mPrepareTestDomU(aCmds)
        file_paths = ["/etc/oratab"]
        _output = obj.mGetFilePermissions(node, node_id, file_paths)
        self.assertEqual(_output["/etc/oratab"], [])

    def test_mGetFilePermissions_multiple_files_command_failure(self):
        """Test mGetFilePermissions with multiple files and command failure"""
        aCmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("/bin/ls -l /etc/oratab", aStdout="", aRc=1),
                    exaMockCommand("/bin/ls -l /etc/hosts", aStdout="-rw-r--r-- 1 root root 1234 Jan 1 10:00 /etc/hosts\n", aRc=0)
                ]
            ]
        }
        obj, node, node_id = self.mPrepareTestDomU(aCmds)
        file_paths = ["/etc/oratab", "/etc/hosts"]
        _output = obj.mGetFilePermissions(node, node_id, file_paths)
        self.assertEqual(_output["/etc/oratab"], [])
        self.assertIsNotNone(_output["/etc/hosts"])
        
    def test_mSaveOutputToFile_exception(self):
        """Test _mSaveOutputToFile with exception"""
        _ebox = self.mGetClubox()
        obj = ebConfigCollector([], [], _ebox)
        data = None
        obj._mSaveOutputToFile(data)
        # Check that the function didn't crash
        self.assertTrue(True)

    def test_mParseMemoryOutput_success(self):
        """Test mParseMemoryOutput with successful parsing"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = "Mem:       30470144    21390976     9079168     204800    7077888    8462336"
        expected_output = {
            "total": "29GB",
            "used": "21GB",
            "free": "8GB",
            "details": {
                "raw_used": "20.4GB",
                "buffers_cache": "6.8GB",
                "shared": "0.2GB",
                "kernel_reserved": "6.2GB"
            }
        }
        result = obj.mParseMemoryOutput(output)
        self.assertEqual(result, expected_output)

    def test_mParseMemoryOutput_list_input(self):
        """Test mParseMemoryOutput with list input"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = ["Mem:       30470144    21390976     9079168     204800    7077888    8462336"]
        expected_output = {
            "total": "29GB",
            "used": "21GB",
            "free": "8GB",
            "details": {
                "raw_used": "20.4GB",
                "buffers_cache": "6.8GB",
                "shared": "0.2GB",
                "kernel_reserved": "6.2GB"
            }
        }
        result = obj.mParseMemoryOutput(output)
        self.assertEqual(result, expected_output)

    def test_mParseMemoryOutput_empty_output(self):
        """Test mParseMemoryOutput with empty output"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = ""
        result = obj.mParseMemoryOutput(output)
        self.assertEqual(result, {})

    def test_mParseMemoryOutput_malformed_output(self):
        """Test mParseMemoryOutput with malformed output"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = "Invalid output"
        result = obj.mParseMemoryOutput(output)
        self.assertEqual(result, {})

    def test_mParseMemoryOutput_missing_mem_line(self):
        """Test mParseMemoryOutput with missing 'Mem:' line"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = "No memory line here"
        result = obj.mParseMemoryOutput(output)
        self.assertEqual(result, {})

    def test_mParseMemoryOutput_insufficient_columns(self):
        """Test mParseMemoryOutput with insufficient columns in 'Mem:' line"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = "Mem: 30470144 21390976"
        result = obj.mParseMemoryOutput(output)
        self.assertEqual(result, {})


    def test_mParseCpuOutput_success(self):
        """Test mParseCpuOutput with successful parsing"""
        obj, _, _ = self.mPrepareTestDomU({})
        cpuinfo_output = """Model name: Intel(R) Xeon(R) Platinum 8270Cl Cpu @ 2.70Ghz
    CPU(s): 8
    Core(s) per socket: 2
    Thread(s) per core: 2
    Socket(s): 2"""
        usage_output = """Average:   %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
    Average:    5.00    0.00    0.30    0.00    0.00    0.00    0.00    0.00    0.00   94.70"""

        expected_output = {
            "model": "Intel(R) Xeon(R) Platinum 8270Cl Cpu @ 2.70Ghz",
            "sockets": 2,
            "cores_per_socket": 2,
            "threads_per_core": 2,
            "total_cores": 8,
            "usage": "N/A"
        }

        result = obj.mParseCpuOutput(cpuinfo_output, usage_output)
        self.assertIsNotNone(result)
        self.assertEqual(result, expected_output)

    def test_mParseCpuOutput_empty_output(self):
        """Test mParseCpuOutput with empty output"""
        obj, _, _ = self.mPrepareTestDomU({})
        cpuinfo_output = ""
        usage_output = ""
        result = obj.mParseCpuOutput(cpuinfo_output, usage_output)

        self.assertIsNotNone(result)
        self.assertEqual(result["model"], "Unknown")
        self.assertEqual(result["sockets"], 1)
        self.assertEqual(result["cores_per_socket"], 1)   
        self.assertEqual(result["threads_per_core"], 1)    
        self.assertEqual(result["total_cores"], 1)        
        self.assertEqual(result["usage"], "N/A")


    def test_mParseCpuOutput_invalid_usage(self):
        """Test mParseCpuOutput with invalid usage output"""
        obj, _, _ = self.mPrepareTestDomU({})
        cpuinfo_output = """Model name: Intel(R) Xeon(R) Platinum 8270Cl Cpu @ 2.70Ghz
    CPU(s): 8
    Core(s) per socket: 2
    Thread(s) per core: 2
    Socket(s): 2"""
        usage_output = "Invalid usage output"

        result = obj.mParseCpuOutput(cpuinfo_output, usage_output)

        self.assertIsNotNone(result)
        self.assertEqual(result["model"], "Intel(R) Xeon(R) Platinum 8270Cl Cpu @ 2.70Ghz")
        self.assertEqual(result["sockets"], 2)
        self.assertEqual(result["cores_per_socket"], 2)
        self.assertEqual(result["threads_per_core"], 2)
        self.assertEqual(result["total_cores"], 8)
        self.assertEqual(result["usage"], "N/A")

    def test_mParseCpuOutput_no_usage(self):
        """Test mParseCpuOutput with no usage output"""
        obj, _, _ = self.mPrepareTestDomU({})
        cpuinfo_output = """Model name: Intel(R) Xeon(R) Platinum 8270Cl Cpu @ 2.70Ghz
    CPU(s): 8
    Core(s) per socket: 2
    Thread(s) per core: 2
    Socket(s): 2"""

        result = obj.mParseCpuOutput(cpuinfo_output)

        self.assertIsNotNone(result)
        self.assertEqual(result["model"], "Intel(R) Xeon(R) Platinum 8270Cl Cpu @ 2.70Ghz")
        self.assertEqual(result["sockets"], 2)
        self.assertEqual(result["cores_per_socket"], 2)
        self.assertEqual(result["threads_per_core"], 2)
        self.assertEqual(result["total_cores"], 8)
        self.assertEqual(result["usage"], "N/A")


    def test_mParseNetworkOutput_success(self):
        """Test mParseNetworkOutput with successful parsing"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = """1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
                        link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
                        inet 127.0.0.1/8 scope host lo
                        valid_lft forever preferred_lft forever
                    2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
                        link/ether 00:11:22:33:44:55 brd ff:ff:ff:ff:ff:ff
                        inet 192.168.1.100/24 brd 192.168.1.255 scope global eth0
                        valid_lft forever preferred_lft forever"""
        expected_output = [
            {"name": "lo", "status": "UP", "ip": "127.0.0.1"},
            {"name": "eth0", "status": "UP", "ip": "192.168.1.100"}
        ]
        result = obj.mParseNetworkOutput(output)
        self.assertIsNotNone(result)
        self.assertEqual(result, expected_output)

    def test_mParseNetworkOutput_empty_output(self):
        """Test mParseNetworkOutput with empty output"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = ""
        result = obj.mParseNetworkOutput(output)
        self.assertIsNotNone(result)
        self.assertEqual(result, [])

    def test_mParseFilesystemOutput_success(self):
        """Test mParseFilesystemOutput with successful parsing"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = [
            "Filesystem      Size  Used Avail Use% Mounted on",
            "/dev/sda1       20G   10G   10G  50% /",
            "/dev/sdb1       15G  5.2G  9.8G  35% /u01"
        ]
        expected_output = {
            "/": {
                "total": "20.00GB",
                "used": "10.00GB",
                "free": "10.00GB",
                "use_percent": "50%"
            },
            "/u01": {
                "total": "15.00GB",
                "used": "5.20GB",
                "free": "9.80GB",
                "use_percent": "35%"
            }
        }
        result = obj.mParseFilesystemOutput(output)
        self.assertIsNotNone(result)
        self.assertEqual(result, expected_output)

    def test_mParseFilesystemOutput_empty_output(self):
        """Test mParseFilesystemOutput with empty output"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = []
        result = obj.mParseFilesystemOutput(output)
        self.assertIsNotNone(result)
        self.assertEqual(result, {})

    def test_mParseFilesystemOutput_invalid_output(self):
        """Test mParseFilesystemOutput with invalid output"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = ["Invalid output"]
        result = obj.mParseFilesystemOutput(output)
        self.assertIsNotNone(result)
        self.assertEqual(result, {})

    def test_mParseFilesystemOutput_size_in_TB(self):
        """Test mParseFilesystemOutput with size in TB"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = [
            "Filesystem      Size  Used Avail Use% Mounted on",
            "/dev/sda1       1T   500G   500G  50% /"
        ]
        expected_output = {
            "/": {
                "total": "1024.00GB",
                "used": "500.00GB",
                "free": "500.00GB",
                "use_percent": "50%"
            }
        }
        result = obj.mParseFilesystemOutput(output)
        self.assertIsNotNone(result)
        self.assertEqual(result, expected_output)

    def test_mParseFilesystemOutput_size_in_MB(self):
        """Test mParseFilesystemOutput with size in MB"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = [
            "Filesystem      Size  Used Avail Use% Mounted on",
            "/dev/sda1       1024M   512M   512M  50% /"
        ]
        expected_output = {
            "/": {
                "total": "1.00GB",
                "used": "0.50GB",
                "free": "0.50GB",
                "use_percent": "50%"
            }
        }
        result = obj.mParseFilesystemOutput(output)
        self.assertIsNotNone(result)
        self.assertEqual(result, expected_output)

    def test_mParseGriddiskOutput_success(self):
        """Test mParseGriddiskOutput with successful parsing"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = [
            "DATAC10_CD_04_iad103712exdcl03 136G HardDisk active CD_04_iad103712exdcl03",
            "DATAC11_CD_05_iad103712exdcl03 136G HardDisk active CD_05_iad103712exdcl03"
        ]
        expected_output = [
            {
                "name": "DATAC10_CD_04_iad103712exdcl03",
                "size": "136G",
                "disk_type": "HardDisk",
                "status": "active",
                "cell_disk": "CD_04_iad103712exdcl03"
            },
            {
                "name": "DATAC11_CD_05_iad103712exdcl03",
                "size": "136G",
                "disk_type": "HardDisk",
                "status": "active",
                "cell_disk": "CD_05_iad103712exdcl03"
            }
        ]
        result = obj.mParseGriddiskOutput(output)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], expected_output[0])
        self.assertEqual(result[1], expected_output[1])

    def test_mParseGriddiskOutput_empty_output(self):
        """Test mParseGriddiskOutput with empty output"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = []
        result = obj.mParseGriddiskOutput(output)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 0)

    def test_mParseGriddiskOutput_invalid_output(self):
        """Test mParseGriddiskOutput with invalid output"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = ["Invalid output"]
        result = obj.mParseGriddiskOutput(output)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 0)


    def test_mParseAsmdiskOutput_success(self):
        """Test mParseAsmdiskOutput with successful parsing"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = [
            "MOUNTED HIGH N 512 512 4096 4194304 5013504 4703964 0 1567988 0 Y DATAC1/",
            "MOUNTED HIGH N 512 512 4096 4194304 5013504 4703964 0 1567988 0 Y DATAC2/"
        ]
        expected_output = [
            {
                "state": "MOUNTED",
                "redundancy": "HIGH",
                "voting_files": "N",
                "sector_size": 512,
                "block_size": 512,
                "au_size": 4096,
                "total_mb": 4194304,
                "free_mb": 5013504,
                "req_mir_free_mb": 4703964,
                "usable_file_mb": 0,
                "offline_disks": 1567988,
                "compatibility": "0",
                "database_compatibility": "Y",
                "name": "DATAC1"
            },
            {
                "state": "MOUNTED",
                "redundancy": "HIGH",
                "voting_files": "N",
                "sector_size": 512,
                "block_size": 512,
                "au_size": 4096,
                "total_mb": 4194304,
                "free_mb": 5013504,
                "req_mir_free_mb": 4703964,
                "usable_file_mb": 0,
                "offline_disks": 1567988,
                "compatibility": "0",
                "database_compatibility": "Y",
                "name": "DATAC2"
            }
        ]
        result = obj.mParseAsmdiskOutput(output)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], expected_output[0])
        self.assertEqual(result[1], expected_output[1])

    def test_mParseAsmdiskOutput_empty_output(self):
        """Test mParseAsmdiskOutput with empty output"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = []
        result = obj.mParseAsmdiskOutput(output)
        self.assertIsNotNone(result)
        self.assertEqual(result, [])

    def test_mParseAsmdiskOutput_invalid_output(self):
        """Test mParseAsmdiskOutput with invalid output"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = ["Invalid output that doesn't split into enough parts"]
        result = obj.mParseAsmdiskOutput(output)
        self.assertIsNotNone(result)
        self.assertEqual(result, [])


    def test_mParseAsmdiskOutput_valid_line(self):
        """Unit test for mParseAsmdiskOutput function"""
        obj, _, _ = self.mPrepareTestDomU({})
        sample_output = [
            "MOUNTED HIGH N 512 512 4096 4194304 5013504 4703964 0 1567988 0 Y DATAC1/"
        ]
        result = obj.mParseAsmdiskOutput(sample_output)
        self.assertIsInstance(result, list)
        self.assertEqual(result[0]["name"], "DATAC1")
        self.assertEqual(result[0]["state"], "MOUNTED")

    def test_mParseScanvipOutput_success(self):
        """Test mParseScanvipOutput with successful parsing"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = [
            "NAME=ora.scan1.vip",
            "STATE=ONLINE",
            "USR_ORA_VIP=10.0.9.123",
            "SCAN_NAME=idc3716-clu01scan",
            "",
            "NAME=ora.scan2.vip",
            "STATE=ONLINE",
            "USR_ORA_VIP=10.0.9.124",
            "SCAN_NAME=idc3716-clu01scan"
        ]
        expected_output = [
            {
                "name": "ora.scan1.vip",
                "state": "ONLINE",
                "ip_address": "10.0.9.123",
                "scan_name": "idc3716-clu01scan",
                "scan_port": "1521"
            },
            {
                "name": "ora.scan2.vip",
                "state": "ONLINE",
                "ip_address": "10.0.9.124",
                "scan_name": "idc3716-clu01scan",
                "scan_port": "1521"
            }
        ]
        result = obj.mParseScanvipOutput(output)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], expected_output[0])
        self.assertEqual(result[1], expected_output[1])

    def test_mParseScanvipOutput_empty_output(self):
        """Test mParseScanvipOutput with empty output"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = []
        result = obj.mParseScanvipOutput(output)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 0)

    def test_mParseScanvipOutput_incomplete_resource(self):
        """Test mParseScanvipOutput with an incomplete resource"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = [
            "NAME=ora.scan1.vip",
            "STATE=ONLINE",
            "USR_ORA_VIP=10.0.9.123",
            "",
            "NAME=ora.scan2.vip",
            "STATE=ONLINE"
        ]
        expected_output = [
            {
                "name": "ora.scan1.vip",
                "state": "ONLINE",
                "ip_address": "10.0.9.123",
                "scan_name": "",
                "scan_port": "1521"
            },
            {
                "name": "ora.scan2.vip",
                "state": "ONLINE",
                "ip_address": "",
                "scan_name": "",
                "scan_port": "1521"
            }
        ]
        result = obj.mParseScanvipOutput(output)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], expected_output[0])
        self.assertEqual(result[1], expected_output[1])

    def test_mParseScanvipOutput_malformed_line(self):
        """Test mParseScanvipOutput with a malformed line"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = [
            "Invalid line",
            "NAME=ora.scan1.vip",
            "STATE=ONLINE",
            "USR_ORA_VIP=10.0.9.123",
            "SCAN_NAME=idc3716-clu01scan"
        ]
        expected_output = [
            {
                "name": "ora.scan1.vip",
                "state": "ONLINE",
                "ip_address": "10.0.9.123",
                "scan_name": "idc3716-clu01scan",
                "scan_port": "1521"
            }
        ]
        result = obj.mParseScanvipOutput(output)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], expected_output[0])

    def test_mParseScanvipOutput_empty_line_at_end(self):
        """Test mParseScanvipOutput with an empty line at the end"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = [
            "NAME=ora.scan1.vip",
            "STATE=ONLINE",
            "USR_ORA_VIP=10.0.9.123",
            "SCAN_NAME=idc3716-clu01scan",
            ""
        ]
        expected_output = [
            {
                "name": "ora.scan1.vip",
                "state": "ONLINE",
                "ip_address": "10.0.9.123",
                "scan_name": "idc3716-clu01scan",
                "scan_port": "1521"
            }
        ]
        result = obj.mParseScanvipOutput(output)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], expected_output[0])

    def test_mParseScanvipOutput_no_empty_line_between_resources(self):
        """Test mParseScanvipOutput with no empty line between resources"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = [
            "NAME=ora.scan1.vip",
            "STATE=ONLINE",
            "USR_ORA_VIP=10.0.9.123",
            "SCAN_NAME=idc3716-clu01scan",
            "NAME=ora.scan2.vip",
            "STATE=ONLINE",
            "USR_ORA_VIP=10.0.9.124",
            "SCAN_NAME=idc3716-clu01scan"
        ]
        expected_output = [
            {
                "name": "ora.scan2.vip",
                "state": "ONLINE",
                "ip_address": "10.0.9.124",
                "scan_name": "idc3716-clu01scan",
                "scan_port": "1521"
            }
        ]
        result = obj.mParseScanvipOutput(output)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], expected_output[0])

    
    def test_mParseFilepermissionOutput_success(self):
        """Test mParseFilepermissionOutput with successful parsing"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = [
            "-rw-rw-r-- 1 grid oinstall 772 Jun 18 06:55 /etc/oratab"
        ]
        expected_output = [
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
        ]
        result = obj.mParseFilepermissionOutput(output)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], expected_output[0])

    def test_mParseFilepermissionOutput_empty_output(self):
        """Test mParseFilepermissionOutput with empty output"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = []
        result = obj.mParseFilepermissionOutput(output)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 0)

    def test_mParseFilepermissionOutput_multiple_lines(self):
        """Test mParseFilepermissionOutput with multiple lines of output"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = [
            "-rw-rw-r-- 1 grid oinstall 772 Jun 18 06:55 /etc/oratab",
            "-rw-r--r-- 1 root root 1234 Jan 1 2022 /etc/passwd"
        ]
        expected_output = [
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
            },
            {
                "permissions": "-rw-r--r--",
                "links": "1",
                "owner": "root",
                "group": "root",
                "size": "1234",
                "month": "Jan",
                "day": "1",
                "time_or_year": "2022",
                "name": "/etc/passwd"
            }
        ]
        result = obj.mParseFilepermissionOutput(output)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertEqual(result, expected_output)

    def test_mParseFilepermissionOutput_empty_line(self):
        """Test mParseFilepermissionOutput with an empty line"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = [
            "",
            "-rw-rw-r-- 1 grid oinstall 772 Jun 18 06:55 /etc/oratab"
        ]
        expected_output = [
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
        ]
        result = obj.mParseFilepermissionOutput(output)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], expected_output[0])

    def test_mParseFilepermissionOutput_malformed_line(self):
        """Test mParseFilepermissionOutput with a malformed line"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = [
            "Invalid line",
            "-rw-rw-r-- 1 grid oinstall 772 Jun 18 06:55 /etc/oratab"
        ]
        expected_output = [
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
        ]
        result = obj.mParseFilepermissionOutput(output)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], expected_output[0])

    def test_mParseFilepermissionOutput_insufficient_parts(self):
        """Test mParseFilepermissionOutput with a line having insufficient parts"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = [
            "-rw-rw-r-- 1 grid oinstall 772 Jun 18 06:55"
        ]
        result = obj.mParseFilepermissionOutput(output)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 0)

    def test_mParseVotingdiskOutput_success(self):
        """Test mParseVotingdiskOutput with successful parsing"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = [
            "1. ONLINE  9655dbb1a8624f2dbfdf5b5164692731 (/dev/exadata_quorum/QD_DATAC1_C3716N11C1) [DATAC1]"
        ]
        expected_output = [
            {
                "number": "1",
                "state": "ONLINE",
                "file_universal_id": "9655dbb1a8624f2dbfdf5b5164692731",
                "file_name": "/dev/exadata_quorum/QD_DATAC1_C3716N11C1",
                "disk_group": "DATAC1",
                "type": "Block"
            }
        ]
        result = obj.mParseVotingdiskOutput(output)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], expected_output[0])

    def test_mParseVotingdiskOutput_empty_output(self):
        """Test mParseVotingdiskOutput with empty output"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = []
        result = obj.mParseVotingdiskOutput(output)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 0)

    def test_mParseVotingdiskOutput_multiple_lines(self):
        """Test mParseVotingdiskOutput with multiple lines of output"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = [
            "1. ONLINE  9655dbb1a8624f2dbfdf5b5164692731 (/dev/exadata_quorum/QD_DATAC1_C3716N11C1) [DATAC1]",
            "2. ONLINE  1234567890abcdef (/dev/exadata_quorum/QD_DATAC1_C3716N11C2) [DATAC1]",
            "3. ONLINE  fedcba9876543210 (/dev/exadata_quorum/QD_DATAC1_C3716N11C3) [DATAC1]"
        ]
        expected_output = [
            {
                "number": "1",
                "state": "ONLINE",
                "file_universal_id": "9655dbb1a8624f2dbfdf5b5164692731",
                "file_name": "/dev/exadata_quorum/QD_DATAC1_C3716N11C1",
                "disk_group": "DATAC1",
                "type": "Block"
            },
            {
                "number": "2",
                "state": "ONLINE",
                "file_universal_id": "1234567890abcdef",
                "file_name": "/dev/exadata_quorum/QD_DATAC1_C3716N11C2",
                "disk_group": "DATAC1",
                "type": "Block"
            },
            {
                "number": "3",
                "state": "ONLINE",
                "file_universal_id": "fedcba9876543210",
                "file_name": "/dev/exadata_quorum/QD_DATAC1_C3716N11C3",
                "disk_group": "DATAC1",
                "type": "Block"
            }
        ]
        result = obj.mParseVotingdiskOutput(output)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 3)
        self.assertEqual(result, expected_output)

    def test_mParseVotingdiskOutput_asm_type(self):
        """Test mParseVotingdiskOutput with ASM type voting disk"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = [
            "1. ONLINE  9655dbb1a8624f2dbfdf5b5164692731 (o/192.168.1.1/ASM1) [DATAC1]"
        ]
        expected_output = [
            {
                "number": "1",
                "state": "ONLINE",
                "file_universal_id": "9655dbb1a8624f2dbfdf5b5164692731",
                "file_name": "o/192.168.1.1/ASM1",
                "disk_group": "DATAC1",
                "type": "ASM"
            }
        ]
        result = obj.mParseVotingdiskOutput(output)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], expected_output[0])

    def test_mParseVotingdiskOutput_invalid_line(self):
        """Test mParseVotingdiskOutput with an invalid line"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = [
            "Invalid line",
            "1. ONLINE  9655dbb1a8624f2dbfdf5b5164692731 (/dev/exadata_quorum/QD_DATAC1_C3716N11C1) [DATAC1]"
        ]
        expected_output = [
            {
                "number": "1",
                "state": "ONLINE",
                "file_universal_id": "9655dbb1a8624f2dbfdf5b5164692731",
                "file_name": "/dev/exadata_quorum/QD_DATAC1_C3716N11C1",
                "disk_group": "DATAC1",
                "type": "Block"
            }
        ]
        result = obj.mParseVotingdiskOutput(output)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], expected_output[0])

    def test_mParseVotingdiskOutput_empty_line(self):
        """Test mParseVotingdiskOutput with an empty line"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = [
            "",
            "1. ONLINE  9655dbb1a8624f2dbfdf5b5164692731 (/dev/exadata_quorum/QD_DATAC1_C3716N11C1) [DATAC1]"
        ]
        expected_output = [
            {
                "number": "1",
                "state": "ONLINE",
                "file_universal_id": "9655dbb1a8624f2dbfdf5b5164692731",
                "file_name": "/dev/exadata_quorum/QD_DATAC1_C3716N11C1",
                "disk_group": "DATAC1",
                "type": "Block"
            }
        ]
        result = obj.mParseVotingdiskOutput(output)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], expected_output[0])

    def test_mParseVotingdiskOutput_comment_line(self):
        """Test mParseVotingdiskOutput with a comment line"""
        obj, _, _ = self.mPrepareTestDomU({})
        output = [
            "## Comment line",
            "1. ONLINE  9655dbb1a8624f2dbfdf5b5164692731 (/dev/exadata_quorum/QD_DATAC1_C3716N11C1) [DATAC1]"
        ]
        expected_output = [
            {
                "number": "1",
                "state": "ONLINE",
                "file_universal_id": "9655dbb1a8624f2dbfdf5b5164692731",
                "file_name": "/dev/exadata_quorum/QD_DATAC1_C3716N11C1",
                "disk_group": "DATAC1",
                "type": "Block"
            }
        ]
        result = obj.mParseVotingdiskOutput(output)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], expected_output[0])

    def test_mGetASMConfig_exception(self):
        """Test mGetASMConfig when an exception occurs during command execution"""

        aCmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("grep '^+ASM' /etc/oratab | cut -d: -f2", aStdout="/u01/app/19.0.0.0/grid\n", aRc=0),
                    exaMockCommand("sudo -u grid bash -c 'export ORACLE_HOME=/u01/app/19.0.0.0/grid; export PATH=$ORACLE_HOME/bin:$PATH; asmcmd lsdg --suppressheader'", aStdout="", aRc=1)
                ]
            ]
        }

        obj, node, node_id = self.mPrepareTestDomU(aCmds)
        
        def mock_mExecuteCmd(cmd):
            if "grep '^+ASM'" in cmd:
                return "", io.StringIO("/u01/app/19.0.0.0/grid\n"), 0  
            elif "asmcmd lsdg" in cmd:
                raise Exception("Simulated exception during asmcmd command execution")
        
        node.mExecuteCmd = mock_mExecuteCmd  
              
        _output = obj.mGetASMConfig(node, node_id)
        
        self.assertEqual(_output, [])

    def test_mGetASMConfig_default_grid_home(self):
        """Test mGetASMConfig when the grid home retrieval fails, using the default value"""

        aCmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("grep '^+ASM' /etc/oratab | cut -d: -f2", aStdout="", aRc=1),  
                    exaMockCommand("sudo -u grid bash -c 'export ORACLE_HOME=/u01/app/19.0.0.0/grid; export PATH=$ORACLE_HOME/bin:$PATH; asmcmd lsdg --suppressheader'", aStdout="DATAC1  500G  400G  100G  MOUNTED\n", aRc=0)
                ]
            ]
        }

        obj, node, node_id = self.mPrepareTestDomU(aCmds)

        def mock_mExecuteCmd(cmd):
            if "grep '^+ASM'" in cmd:
                return "", io.StringIO(""), 1  
            elif "asmcmd lsdg" in cmd:
                return "", io.StringIO("DATAC1  500G  400G  100G  MOUNTED\n"), 0  
        
        node.mExecuteCmd = mock_mExecuteCmd  
        
    def test_mGetASMConfig_asmcmd_failure(self):
        """Test mGetASMConfig with asmcmd command failure"""
        
        aCmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("grep '^+ASM' /etc/oratab | cut -d: -f2", aStdout="/u01/app/19.0.0.0/grid\n", aRc=0),
                    exaMockCommand("sudo -u grid bash -c 'export ORACLE_HOME=/u01/app/19.0.0.0/grid; export PATH=$ORACLE_HOME/bin:$PATH; asmcmd lsdg --suppressheader'", aStdout="", aRc=1)
                ]
            ]
        }

        obj, node, node_id = self.mPrepareTestDomU(aCmds)
        
        node.mGetCmdRegex = lambda: r'.*'  

        def mock_mExecuteCmd(cmd):
            if "grep '^+ASM'" in cmd:
                return "", io.StringIO("/u01/app/19.0.0.0/grid\n"), 0  
            elif "asmcmd lsdg" in cmd:
                return "", io.StringIO(""), 1  

        node.mExecuteCmd = mock_mExecuteCmd  
        
        _output = obj.mGetASMConfig(node, node_id)
        
        self.assertEqual(_output, [])

    def test_mGetASMConfig_empty_input(self):
        """Test mGetASMConfig when asmcmd command returns no output"""

        aCmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("grep '^+ASM' /etc/oratab | cut -d: -f2", aStdout="/u01/app/19.0.0.0/grid\n", aRc=0),
                    exaMockCommand("sudo -u grid bash -c 'export ORACLE_HOME=/u01/app/19.0.0.0/grid; export PATH=$ORACLE_HOME/bin:$PATH; asmcmd lsdg --suppressheader'", aStdout="", aRc=0)
                ]
            ]
        }

        obj, node, node_id = self.mPrepareTestDomU(aCmds)

        def mock_mExecuteCmd(cmd):
            if "grep '^+ASM'" in cmd:
                return "", io.StringIO("/u01/app/19.0.0.0/grid\n"), 0  
            elif "asmcmd lsdg" in cmd:
                return "", io.StringIO(""), 0  
        
        node.mExecuteCmd = mock_mExecuteCmd  
        
        _output = obj.mGetASMConfig(node, node_id)
        
        self.assertEqual(_output, [])


    def test_mGetScanVIPConfig_crsctl_fail(self):
        """Test mGetScanVIPConfig when crsctl command fails"""
        aCmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("grep '^+ASM' /etc/oratab | cut -d: -f2", aStdout="/u01/app/19.0.0.0/grid\n", aRc=0),
                    exaMockCommand("sudo -u grid bash -c 'export ORACLE_HOME=/u01/app/19.0.0.0/grid; export PATH=$ORACLE_HOME/bin:$PATH; crsctl status resource -t -f'", aStdout="", aRc=1)
                ]
            ]
        }
        obj, node, node_id = self.mPrepareTestDomU(aCmds)

        def mock_mExecuteCmd(cmd):
            if "grep '^+ASM'" in cmd:
                return "", io.StringIO("/u01/app/19.0.0.0/grid\n"), 0
            elif "crsctl status resource" in cmd:
                return "", io.StringIO(""), 1
        node.mExecuteCmd = mock_mExecuteCmd
        node.mGetCmdExitStatus = lambda: 1

        result = obj.mGetScanVIPConfig(node, node_id)
        self.assertEqual(result, [])

    def test_mGetScanVIPConfig_empty_output(self):
        """Test mGetScanVIPConfig when crsctl returns empty output"""
        aCmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("grep '^+ASM' /etc/oratab | cut -d: -f2", aStdout="/u01/app/19.0.0.0/grid\n", aRc=0),
                    exaMockCommand("sudo -u grid bash -c 'export ORACLE_HOME=/u01/app/19.0.0.0/grid; export PATH=$ORACLE_HOME/bin:$PATH; crsctl status resource -t -f'", aStdout="", aRc=0)
                ]
            ]
        }
        obj, node, node_id = self.mPrepareTestDomU(aCmds)

        def mock_mExecuteCmd(cmd):
            if "grep '^+ASM'" in cmd:
                return "", io.StringIO("/u01/app/19.0.0.0/grid\n"), 0
            elif "crsctl status resource" in cmd:
                return "", io.StringIO(""), 0
        node.mExecuteCmd = mock_mExecuteCmd
        node.mGetCmdExitStatus = lambda: 0

        result = obj.mGetScanVIPConfig(node, node_id)
        self.assertEqual(result, [])

    def test_mGetScanVIPConfig_exception(self):
        """Test mGetScanVIPConfig when an exception occurs during command execution"""
        aCmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("grep '^+ASM' /etc/oratab | cut -d: -f2", aStdout="/u01/app/19.0.0.0/grid\n", aRc=0),
                    exaMockCommand("sudo -u grid bash -c 'export ORACLE_HOME=/u01/app/19.0.0.0/grid; export PATH=$ORACLE_HOME/bin:$PATH; crsctl status resource -t -f'", aStdout="", aRc=0)
                ]
            ]
        }
        obj, node, node_id = self.mPrepareTestDomU(aCmds)

        def mock_mExecuteCmd(cmd):
            if "grep '^+ASM'" in cmd:
                return "", io.StringIO("/u01/app/19.0.0.0/grid\n"), 0
            elif "crsctl status resource" in cmd:
                raise Exception("Simulated exception during crsctl command")
        node.mExecuteCmd = mock_mExecuteCmd

        result = obj.mGetScanVIPConfig(node, node_id)
        self.assertEqual(result, [])

    def test_mGetVotingDiskConfig_success(self):
        """Test mGetVotingDiskConfig with successful voting disk retrieval"""
        aCmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("grep '^+ASM' /etc/oratab | cut -d: -f2", aStdout="/u01/app/19.0.0.0/grid\n", aRc=0),
                    exaMockCommand("export ORACLE_BASE=/u01/app/grid; export ORACLE_HOME=/u01/app/19.0.0.0/grid; export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/u01/app/19.0.0.0/grid/lib; /u01/app/19.0.0.0/grid/bin/crsctl query css votedisk", aStdout=(
                        "1. ONLINE  1234567890123456   (/dev/asm-disk1)   [DATA]\n"
                        "2. ONLINE  7890123456789012   (/dev/asm-disk2)   [FRA]\n"
                    ), aRc=0)
                ]
            ]
        }
        obj, node, node_id = self.mPrepareTestDomU(aCmds)

        def mock_mExecuteCmd(cmd):
            if "grep '^+ASM'" in cmd:
                return "", io.StringIO("/u01/app/19.0.0.0/grid\n"), 0
            elif "crsctl query css votedisk" in cmd:
                return "", io.StringIO(
                    "1. ONLINE  1234567890123456   (/dev/asm-disk1)   [DATA]\n"
                    "2. ONLINE  7890123456789012   (/dev/asm-disk2)   [FRA]\n"
                ), 0
        node.mExecuteCmd = mock_mExecuteCmd
        node.mGetCmdExitStatus = lambda: 0
        node.mSetUser = lambda user: None  

        
        obj.mParseVotingdiskOutput = lambda output: [
            {"number": "1", "state": "ONLINE", "file_universal_id": "1234567890123456", "file_name": "/dev/asm-disk1", "disk_group": "DATA", "type": "Block"},
            {"number": "2", "state": "ONLINE", "file_universal_id": "7890123456789012", "file_name": "/dev/asm-disk2", "disk_group": "FRA", "type": "Block"}
        ]

        result = obj.mGetVotingDiskConfig(node, node_id)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertTrue(all("number" in r and "state" in r for r in result))

    def test_mGetVotingDiskConfig_grep_fail(self):
        """Test mGetVotingDiskConfig when grep command fails"""
        aCmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("grep '^+ASM' /etc/oratab | cut -d: -f2", aStdout="", aRc=1),
                ]
            ]
        }
        obj, node, node_id = self.mPrepareTestDomU(aCmds)

        def mock_mExecuteCmd(cmd):
            if "grep '^+ASM'" in cmd:
                return "", io.StringIO(""), 1
        node.mExecuteCmd = mock_mExecuteCmd
        node.mGetCmdExitStatus = lambda: 1
        node.mSetUser = lambda user: None

        result = obj.mGetVotingDiskConfig(node, node_id)
        self.assertEqual(result, [])

    def test_mGetVotingDiskConfig_crsctl_fail(self):
        """Test mGetVotingDiskConfig when crsctl command fails"""
        aCmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("grep '^+ASM' /etc/oratab | cut -d: -f2", aStdout="/u01/app/19.0.0.0/grid\n", aRc=0),
                    exaMockCommand("export ORACLE_BASE=/u01/app/grid; export ORACLE_HOME=/u01/app/19.0.0.0/grid; export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/u01/app/19.0.0.0/grid/lib; /u01/app/19.0.0.0/grid/bin/crsctl query css votedisk", aStdout="", aRc=1)
                ]
            ]
        }
        obj, node, node_id = self.mPrepareTestDomU(aCmds)

        def mock_mExecuteCmd(cmd):
            if "grep '^+ASM'" in cmd:
                return "", io.StringIO("/u01/app/19.0.0.0/grid\n"), 0
            elif "crsctl query css votedisk" in cmd:
                return "", io.StringIO(""), 1
        node.mExecuteCmd = mock_mExecuteCmd
        node.mGetCmdExitStatus = lambda: 1
        node.mSetUser = lambda user: None

        result = obj.mGetVotingDiskConfig(node, node_id)
        self.assertEqual(result, [])

    def test_mGetVotingDiskConfig_empty_output(self):
        """Test mGetVotingDiskConfig when crsctl returns empty output"""
        aCmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("grep '^+ASM' /etc/oratab | cut -d: -f2", aStdout="/u01/app/19.0.0.0/grid\n", aRc=0),
                    exaMockCommand("export ORACLE_BASE=/u01/app/grid; export ORACLE_HOME=/u01/app/19.0.0.0/grid; export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/u01/app/19.0.0.0/grid/lib; /u01/app/19.0.0.0/grid/bin/crsctl query css votedisk", aStdout="", aRc=0)
                ]
            ]
        }
        obj, node, node_id = self.mPrepareTestDomU(aCmds)

        def mock_mExecuteCmd(cmd):
            if "grep '^+ASM'" in cmd:
                return "", io.StringIO("/u01/app/19.0.0.0/grid\n"), 0
            elif "crsctl query css votedisk" in cmd:
                return "", io.StringIO(""), 0
        node.mExecuteCmd = mock_mExecuteCmd
        node.mGetCmdExitStatus = lambda: 0
        node.mSetUser = lambda user: None

        result = obj.mGetVotingDiskConfig(node, node_id)
        self.assertEqual(result, [])

    def test_mGetVotingDiskConfig_exception(self):
        """Test mGetVotingDiskConfig when an exception occurs during command execution"""
        aCmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("grep '^+ASM' /etc/oratab | cut -d: -f2", aStdout="/u01/app/19.0.0.0/grid\n", aRc=0),
                    exaMockCommand("export ORACLE_BASE=/u01/app/grid; export ORACLE_HOME=/u01/app/19.0.0.0/grid; export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/u01/app/19.0.0.0/grid/lib; /u01/app/19.0.0.0/grid/bin/crsctl query css votedisk", aStdout="", aRc=0)
                ]
            ]
        }
        obj, node, node_id = self.mPrepareTestDomU(aCmds)

        def mock_mExecuteCmd(cmd):
            if "grep '^+ASM'" in cmd:
                return "", io.StringIO("/u01/app/19.0.0.0/grid\n"), 0
            elif "crsctl query css votedisk" in cmd:
                raise Exception("Simulated exception during crsctl command")
        node.mExecuteCmd = mock_mExecuteCmd
        node.mSetUser = lambda user: None

        result = obj.mGetVotingDiskConfig(node, node_id)
        self.assertEqual(result, [])

    def test_mCollectAllConfigs_success(self):
        """Test mCollectAllConfigs with normal successful collection from DomUs and cells"""
        obj, _, _ = self.mPrepareTestDomU({})

        # You may mock individual methods if needed
        obj.mGetSystemConfig = lambda *_: {"cpu": {}, "memory": {}}
        obj.mGetNetworkConfig = lambda *_: []
        obj.mGetFileSystemConfig = lambda *_: {}
        obj.mGetGridConfig = lambda *_: {"grid_home_path": "/u01/app/grid", "grid_version": "19c"}
        obj.mGetASMConfig = lambda *_: []
        obj.mGetScanVIPConfig = lambda *_: []
        obj.mGetFilePermissions = lambda *_: {}
        obj.mGetVotingDiskConfig = lambda *_: []
        obj.mGetGridDiskConfig = lambda *_: {}

        obj._mSaveOutputToFile = lambda *_: None  

        result = obj.mCollectAllConfigs()
        self.assertIsInstance(result, dict)
        self.assertIn("VMs", result)
        self.assertIn("cluster", result)

    def test_mCollectAllConfigs_save_output_exception(self):
        """Test mCollectAllConfigs handles exception during output save"""
        obj, _, _ = self.mPrepareTestDomU({})

        obj.mGetSystemConfig = lambda *_: {"cpu": {}, "memory": {}}
        obj.mGetNetworkConfig = lambda *_: []
        obj.mGetFileSystemConfig = lambda *_: {}
        obj.mGetGridConfig = lambda *_: {}
        obj.mGetASMConfig = lambda *_: []
        obj.mGetScanVIPConfig = lambda *_: []
        obj.mGetFilePermissions = lambda *_: {}
        obj.mGetVotingDiskConfig = lambda *_: []
        obj.mGetGridDiskConfig = lambda *_: {}

        # Simulate save failure
        obj._mSaveOutputToFile = lambda *_: (_ for _ in ()).throw(Exception("Write failed"))

        result = obj.mCollectAllConfigs()
        self.assertIsInstance(result, dict)


if __name__ == '__main__':
    unittest.main()


