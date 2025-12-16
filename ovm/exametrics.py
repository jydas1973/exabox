"""
 Copyright (c) 2024, Oracle and/or its affiliates.

NAME:
    exametrics - Responsible for adding methods for collection of metrics

FUNCTION:
    Provide basic methods for collection of metrics

NOTE:
    For design specification, refer: https://confluence.oraclecorp.com/confluence/display/EDCS/Exacloud+Metrics+Collection

History:
    MODIFIED   (MM/DD/YY)
    shapatna    06/14/24 -Bug 36732867: Create File
"""
import psutil
import os
import re
import ast
import time
import socket
import resource
import json
from exabox.core.DBStore import ebExacloudDB, ebGetDefaultDB
from exabox.log.LogMgr import ebLogInfo
from exabox.core.Context import get_gcontext
        
class ebExacloudSysMetrics():
    CONVERSION_TO_GB = 1024 ** 3
    CONVERSION_TO_MB = 1024 ** 2

    def __init__(self):
        '''
            Initializes the properties of the class that are to be used extensively: \\
                1. __getFqdn stores the hostname of the system \\
                2. __ebExacloudDb is an instance to the ebExacloudDb class imported from DBStore3.py \\
                3. __cwd is the current working directory \\
                4. __procDetails returns the values of the _parent_agent_pid, _agents_pid, _workers_pid, _scheduler_pid, _supervisor_pid, and _mysql_pid \\
                5. __reqDetails returns the values of the _cmd_types, _error_types, _active_requests to be used in the request metric 
        '''
        self.__getFqdn = socket.getfqdn()
        self.__ebExacloudDb = ebGetDefaultDB()
        self.__cwd = self.mFetchCurrentPath()
        self.__procDetails = self.mFetchEcData()
        self.__reqDetails = self.mFetchReqData()

    @staticmethod
    def mFormatSeconds(_seconds):
        '''
            Provided the input is the total time in seconds till now, this method returns a formatted sring consisting of the number of days, hours, minutes and seconds
        '''
        _days = _seconds // (24 * 3600)
        _seconds = _seconds % (24 * 3600)
        _hours = _seconds // 3600
        _seconds %= 3600
        _minutes = _seconds // 60
        _seconds %= 60
        
        return f"{int(_days)} days, {int(_hours)} hours, {int(_minutes)} minutes, {int(_seconds)} seconds"

    @staticmethod
    def mEnsureNonNegativeValue(value):
        '''
            This method takes in a value and returns the max(value, 0)
        '''
        try:
            _result = max(value, 0)
            return _result
        except (ValueError, TypeError):
            return 0 

    def mGetMySqlPid(self):
        '''
            self.__ebExacloudDb.mGetPidFile() returns the full path to the file which stores in the PID of the MySQL Process \\
            This method parses the file and returns the PID value as an integer
        '''
        _result = self.__ebExacloudDb.mGetPidFile()
        _entry = None
        _path = ""
        
        if _result:
            _entry = _result[0]
            if len(_entry)>1:
                _path = _entry[1]
        
        with open(_path, "r") as file:
            string = file.read().replace("\n", "")

        mysql_pid = int(string)
        return mysql_pid    

    def mFetchCurrentPath(self):
        '''
            This method returns the real path to the exacloud directory on the system
        '''
        _path = get_gcontext().mGetBasePath()
        _cwd = os.path.realpath(_path)
        return _cwd

    def mFetchEcData(self):
        '''
            This method calls in __ebExacloudDb.mGetAgentsPID(), __ebExacloudDb.mGetSpecialWorkerPIDs(), __ebExacloudDb.mGetWorkerPIDs() and mGetMySqlPid() to fetch and return the PIDs of: \\
                1. Parent Agent \\
                2. Agents \\
                3. Workers \\
                4. Scheduler Process \\
                5. Supervisor Process \\
                6. MySQL Daemon Process 
        '''
        # Fetch the agent, special workers and workers PIDs from the database
        _sql_agent_pid = self.__ebExacloudDb.mGetAgentsPID()
        _sql_special_workers_pid = self.__ebExacloudDb.mGetSpecialWorkerPIDs()
        _sql_workers_pid = self.__ebExacloudDb.mGetWorkerPIDs()    
        
        _parent_agent_pid = None
        if _sql_agent_pid:
            if _sql_agent_pid[0]:
                _parent_agent_pid = int(_sql_agent_pid[0][0])
        
        # Fetch the scheduler, supervisor and workers PIDs
        _scheduler_pid = int(_sql_special_workers_pid['scheduler'])
        _supervisor_pid = int(_sql_special_workers_pid['supervisor'])
        _workers_pid = [int(_pid[0]) for _pid in _sql_workers_pid if _pid]
        
        # Fetch the MySQL PID
        _mysql_pid = self.mGetMySqlPid()
        _agents_pid = []

        if _parent_agent_pid is not None:
            _agents_pid = [_proc.pid for _proc in psutil.Process(pid=_parent_agent_pid).children(recursive=True)]

        if _parent_agent_pid not in _agents_pid:
            _agents_pid.append(_parent_agent_pid)

        return _parent_agent_pid, _agents_pid, _workers_pid, _scheduler_pid, _supervisor_pid, _mysql_pid   

    def mFetchReqData(self):
        '''
            This method fetches the following: \\
                1. Number of Active Requests (obtained from the MySQL Database by using __ebExacloudDb.mGetActiveRequestStatus()) \\
                2. Number of Errors (obtained from the MySQL Database by using __ebExacloudDb.mGetRequestStatus("error_str")) \\
                3. Number of commands executed till now (obtained from the MySQL Database by using __ebExacloudDb.mGetRequestStatus("cmdtype"))
        '''
        _cmd_types = self.__ebExacloudDb.mGetRequestStatus("cmdtype")
        _error_types = self.__ebExacloudDb.mGetRequestStatus("error_str")
        _active_requests = self.__ebExacloudDb.mGetActiveRequestStatus()

        return _cmd_types, _error_types, _active_requests
    
    def mGetSysCpuUsage(self):
        '''
            This method returns the count as well as the accumulated counts of user, system, idle, iowait times, ctx switches and interrupts for the whole system
        '''
        _current_cpu_times = psutil.cpu_times()
        _current_cpu_stats = psutil.cpu_stats()
        _current_cpu_percent = psutil.cpu_times_percent(interval=1)

        # Fetch the previous data from the database if it exists
        _prev_data = {
            "user time(seconds)" : 0,
            "system time(seconds)" : 0,
            "idle time(seconds)" : 0,
            "iowait time(seconds)": 0,
            "ctx switches" : 0,
            "interrupts" : 0
        }

        _data_from_db = self.__ebExacloudDb.mGetLatestMetric('sys_metric')
        
        if _data_from_db:
            _dict = json.loads(_data_from_db[0])
            if "mGetSysCpuUsage" in _dict:
                _data_from_db = _dict["mGetSysCpuUsage"]
                _prev_data = {
                    "user time(seconds)" : _data_from_db["accumulated user time(seconds)"],
                    "system time(seconds)" : _data_from_db["accumulated system time(seconds)"],
                    "idle time(seconds)" : _data_from_db["accumulated idle time(seconds)"],
                    "iowait time(seconds)": _data_from_db["accumulated iowait time(seconds)"],
                    "ctx switches" : _data_from_db["accumulated ctx switches"],
                    "interrupts" : _data_from_db["accumulated interrupts"]
                }
        
        return {
            "name" : "system cpu usage",
            "hostname" : self.__getFqdn,
            "user time(seconds)" : self.mEnsureNonNegativeValue(round(_current_cpu_times.user) - _prev_data["user time(seconds)"]),
            "system time(seconds)" : self.mEnsureNonNegativeValue(round(_current_cpu_times.system) - _prev_data["system time(seconds)"]),
            "idle time(seconds)" : self.mEnsureNonNegativeValue(round(_current_cpu_times.idle) - _prev_data["idle time(seconds)"]),
            "iowait time(seconds)": self.mEnsureNonNegativeValue(round(_current_cpu_times.iowait) - _prev_data["iowait time(seconds)"]),

            "ctx switches" : self.mEnsureNonNegativeValue(_current_cpu_stats.ctx_switches - _prev_data["ctx switches"]),
            "interrupts" : self.mEnsureNonNegativeValue(_current_cpu_stats.interrupts - _prev_data["interrupts"]),
            
            "user time(%)" : round(_current_cpu_percent.user, 2),
            "nice time(%)" : round(_current_cpu_percent.nice, 2),
            "system time(%)" : round(_current_cpu_percent.system, 2),
            "idle time(%)" : round(_current_cpu_percent.idle, 2),

            "accumulated user time(seconds)" : round(_current_cpu_times.user),
            "accumulated system time(seconds)" : round(_current_cpu_times.system),
            "accumulated idle time(seconds)" : round(_current_cpu_times.idle),
            "accumulated iowait time(seconds)": round(_current_cpu_times.iowait),
            
            "accumulated ctx switches" : _current_cpu_stats.ctx_switches,
            "accumulated interrupts" : _current_cpu_stats.interrupts,
        }

    def mGetSysMemUsage(self):
        '''
            This method returns the total, available memory (in GB) and percentage of memory used  
        '''
        _virtual_memory = psutil.virtual_memory()
        
        return {
            "name" : "system memory usage",
            "hostname" : self.__getFqdn,
            "total memory(GB)" : round(_virtual_memory.total / self.CONVERSION_TO_GB),
            "available memory(GB)" : round(_virtual_memory.available / self.CONVERSION_TO_GB, 2),
            "percent memory used(%)" : round(_virtual_memory.percent, 2)
        }

    def mGetSysDiskUsage(self):
        '''
            This method returns the count as well as the accumulated counts of read, write, read (in bytes) and write (in bytes) for the whole system.
        '''
        _disk_io = psutil.disk_io_counters(perdisk=False, nowrap=True)

        # Fetch the previous data from the database
        _prev_data = {
            "read count" : 0,
            "write count" : 0,
            "read(bytes)" : 0,
            "write(bytes)" : 0
        }

        _data_from_db = self.__ebExacloudDb.mGetLatestMetric('sys_metric')
        if _data_from_db:
            _dict = json.loads(_data_from_db[0])
            if "mGetSysDiskUsage" in _dict:
                _data_from_db = _dict["mGetSysDiskUsage"]
                _prev_data = {
                    "read count" : _data_from_db["accumulated read count"],
                    "write count" : _data_from_db["accumulated write count"],
                    "read(bytes)" : _data_from_db["accumulated read(bytes)"],
                    "write(bytes)" : _data_from_db["accumulated write(bytes)"] 
                }
        
        return {
            "name" : "disk usage",
            "hostname" : self.__getFqdn,
            "read count" : self.mEnsureNonNegativeValue(_disk_io.read_count - _prev_data["read count"]),
            "write count" : self.mEnsureNonNegativeValue(_disk_io.write_count - _prev_data["write count"]),
            "read(bytes)" : self.mEnsureNonNegativeValue(_disk_io.read_bytes - _prev_data["read(bytes)"]),
            "write(bytes)" : self.mEnsureNonNegativeValue(_disk_io.write_bytes - _prev_data["write(bytes)"]),

            "accumulated read count" : _disk_io.read_count,
            "accumulated write count" : _disk_io.write_count,
            "accumulated read(bytes)" : _disk_io.read_bytes,
            "accumulated write(bytes)" : _disk_io.write_bytes            
        }

    def mGetSysInodeUsage(self):
        '''
            This method returns the count as well as the accumulated counts of total and free inodes for the whole system.
        '''
        _total_inodes, _free_inodes = 0, 0
        
        for _partition in psutil.disk_partitions():
            try:
                _stat_vfs = os.statvfs(_partition.mountpoint)
                _total_inodes += _stat_vfs.f_files
                _free_inodes += _stat_vfs.f_ffree
            except PermissionError:
                continue
        
        # Fetch the previous data from the database
        _prev_data = {
            "total inode" : 0,
            "free inode" : 0
        }

        _data_from_db = self.__ebExacloudDb.mGetLatestMetric('sys_metric')
        if _data_from_db:
            _dict = json.loads(_data_from_db[0])
            if "mGetSysInodeUsage" in _dict:
                _data_from_db = _dict["mGetSysInodeUsage"]
                _prev_data = {
                    "total inode" : _data_from_db["accumulated total inode"],
                    "free inode" : _data_from_db["accumulated free inode"] 
                }

        return {
            "name" : "inode usage",
            "hostname" : self.__getFqdn,
            "total inode" : _total_inodes - _prev_data["total inode"],
            "free inode" : _free_inodes - _prev_data["free inode"],
            "accumulated total inode" : _total_inodes,
            "accumulated free inode" : _free_inodes
        }

    def mGetMemoryDetails(self, pids):
        '''
            This method takes in input: PIDs, then checks if it is a single PID or a list of PIDs and accordingly returns the total RAM Usage by the PID(s)
        '''
        _usage_details = []
        _is_a_list = True 

        if type(pids)!=list:
            pids = [pids]
            _is_a_list = False
        
        for _pid in pids:
            _proc_memory = psutil.Process(pid=_pid).memory_info().rss
            _usage_details.append({
                "pid" : _pid,
                "used memory(MB)" : round(_proc_memory / self.CONVERSION_TO_MB)
            })
        
        if not _is_a_list:
            return _usage_details[0]

        return _usage_details

    def mGetCpuUsageDetails(self, pids):
        '''
            This method takes in input: PIDs, then checks if it is a single PID or a list of PIDs and accordingly returns the total CPU Usage (in %) by the PID(s)
        '''
        _usage_details = []
        _is_a_list = True
        
        if type(pids)!=list:
            pids = [pids]
            _is_a_list = False 
        
        for _pid in pids:
            _proc_cpu_percent = psutil.Process(pid=_pid).cpu_percent(interval=0.1) 
            _usage_details.append({
                "pid" : _pid,
                "used cpu(%)" : _proc_cpu_percent
            })

        if not _is_a_list:
            return _usage_details[0]
        
        return _usage_details

    def mGetCpuTimesDetails(self, pids, process_name):
        '''
            This method takes in input: PIDs, then checks if it is a single PID or a list of PIDs and accordingly returns the CPU Times (user, system, iowait, children user and children system times) by the PID(s)
        '''
        _usage_details = []
        
        if(type(pids)!=list):
            _pid = pids

            _prev_data = {
                "user time" : 0,
                "system time" : 0,
                "iowait time" : 0,
                "children user time" : 0,
                "children system time" : 0,  
            }

            # Fetch the data from the database
            _data_from_db = self.__ebExacloudDb.mGetLatestMetric("ec_proc_metric")
            _current_cpu_times = psutil.Process(pid=_pid).cpu_times()
            
            if _data_from_db:
                _dict = json.loads(_data_from_db[0])
                if "mGetProcCpuTimes" in _dict:
                    _data_from_db = _dict["mGetProcCpuTimes"]
                    if _data_from_db[process_name]["pid"] == _pid:
                        _prev_data = {
                            "user time" : _data_from_db[process_name]["accumulated user time(seconds)"],
                            "system time" : _data_from_db[process_name]["accumulated system time(seconds)"],
                            "iowait time" : _data_from_db[process_name]["accumulated iowait time(seconds)"],
                            "children user time" : _data_from_db[process_name]["accumulated children user time(seconds)"],
                            "children system time" : _data_from_db[process_name]["accumulated children system time(seconds)"],  
                        }
            
            return {
                "pid" : _pid,
                "user time(seconds)" : self.mEnsureNonNegativeValue(round(_current_cpu_times.user) - _prev_data["user time"]),
                "system time(seconds)" : self.mEnsureNonNegativeValue(round(_current_cpu_times.system) - _prev_data["system time"]),
                "iowait time(seconds)" : self.mEnsureNonNegativeValue(round(_current_cpu_times.iowait) - _prev_data["iowait time"]),
                "children user time(seconds)" : self.mEnsureNonNegativeValue(round(_current_cpu_times.children_user) - _prev_data["children user time"]),
                "children system time(seconds)" : self.mEnsureNonNegativeValue(round(_current_cpu_times.children_system) - _prev_data["children system time"]), 

                "accumulated user time(seconds)" : round(_current_cpu_times.user),
                "accumulated system time(seconds)" : round(_current_cpu_times.system),
                "accumulated iowait time(seconds)" : round(_current_cpu_times.iowait),
                "accumulated children user time(seconds)" : round(_current_cpu_times.children_user),
                "accumulated children system time(seconds)" : round(_current_cpu_times.children_system),   
            }
        
        for _pid in pids:
            _prev_data = {
                "user time" : 0,
                "system time" : 0,
                "iowait time" : 0,
                "children user time" : 0,
                "children system time" : 0,  
            }
            
            _data_from_db = self.__ebExacloudDb.mGetLatestMetric("ec_proc_metric")
            _current_cpu_times = psutil.Process(pid=_pid).cpu_times()
            
            if _data_from_db:
                _dict = json.loads(_data_from_db[0])
                if "mGetProcCpuTimes" in _dict:
                    _data_from_db = json.loads(_data_from_db[0])["mGetProcCpuTimes"][process_name] # data_from_db is a list now
            
                    if _data_from_db:
                        _index = None
                        
                        for i in range(len(_data_from_db)):
                            if _data_from_db[i]["pid"] == _pid:
                                _index=i
                                break

                        if _index is not None:
                            _prev_data = {
                                "user time" : _data_from_db[_index]["accumulated user time(seconds)"],
                                "system time" : _data_from_db[_index]["accumulated system time(seconds)"],
                                "iowait time" : _data_from_db[_index]["accumulated iowait time(seconds)"],
                                "children user time" : _data_from_db[_index]["accumulated children user time(seconds)"],
                                "children system time" : _data_from_db[_index]["accumulated children system time(seconds)"],  
                            }
                
            _usage_details.append({
                "pid" : _pid,
                "user time(seconds)" : self.mEnsureNonNegativeValue(round(_current_cpu_times.user) - _prev_data["user time"]),
                "system time(seconds)" : self.mEnsureNonNegativeValue(round(_current_cpu_times.system) - _prev_data["system time"]),
                "iowait time(seconds)" : self.mEnsureNonNegativeValue(round(_current_cpu_times.iowait) - _prev_data["iowait time"]),
                "children user time(seconds)" : self.mEnsureNonNegativeValue(round(_current_cpu_times.children_user) - _prev_data["children user time"]),
                "children system time(seconds)" : self.mEnsureNonNegativeValue(round(_current_cpu_times.children_system) - _prev_data["children system time"]), 

                "accumulated user time(seconds)" : round(_current_cpu_times.user),
                "accumulated system time(seconds)" : round(_current_cpu_times.system),
                "accumulated iowait time(seconds)" : round(_current_cpu_times.iowait),
                "accumulated children user time(seconds)" : round(_current_cpu_times.children_user),
                "accumulated children system time(seconds)" : round(_current_cpu_times.children_system),
            })

        return _usage_details

    def mGetFdUsageDetails(self, pids):
        '''
            This method takes in input: PIDs, then checks if it is a single PID or a list of PIDs and accordingly returns the number of active file descriptors by the PID(s)
        '''
        _usage_details = []
        _is_a_list = True
        
        if type(pids)!=list:
            _is_a_list=False
            pids=[pids]

        for _pid in pids:
            _current_active_fd = psutil.Process(pid=_pid).num_fds() 
            _usage_details.append({
                "pid" : _pid,
                "active fd(s)" : _current_active_fd
            })

        if not _is_a_list:
            return _usage_details[0]

        return _usage_details

    def mGetTcpNumDetails(self, pids):
        '''
            This method takes in input: PIDs, then checks if it is a single PID or a list of PIDs and accordingly returns the TCP Connections and TCP Ports (LISTENING) used by the PID(s)
        '''
        _usage_details = []
        _is_a_list = True
        
        if type(pids)!=list:
            _is_a_list=False
            pids=[pids]
            
        for _pid in pids:
            _tcp_port = None
            _tcp_conn = psutil.Process(pid=_pid).connections(kind="tcp")
            
            for _entry in _tcp_conn:
                if _entry.status=="LISTEN":
                    _tcp_port = _entry[3][1]
                    
            if len(_tcp_conn)==0:
                _tcp_port = "Does not exist"
            
            _usage_details.append({
                "pid" : _pid,
                "tcp count" : len(_tcp_conn),
                "tcp port" : _tcp_port
            })
        
        if not _is_a_list:
            return _usage_details[0]

        return _usage_details

    def mGetMaxFds(self):
        '''
            This method fetches the total hard limit of the file descriptors for the entire system
        '''
        try:
            _ , _hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
            return _hard_limit
        except Exception as e:
            return "Failed to retrieve resource limits"

    def mGetProcMemUsage(self):
        '''
            This method returns the RAM Usage by each of the processes: Agents, Workers, Scheduler, Supervisor and MySQL Daemon
        '''
        _, _agents_pid, _workers_pid, _scheduler_pid, _supervisor_pid, _mysql_pid = self.__procDetails

        return {
            "name" : "process memory usage",
            "hostname" : self.__getFqdn,
            "agent process" : self.mGetMemoryDetails(_agents_pid),
            "worker process" : self.mGetMemoryDetails(_workers_pid),
            "supervisor process" : self.mGetMemoryDetails(_supervisor_pid),
            "scheduler process" : self.mGetMemoryDetails(_scheduler_pid),
            "mysql daemon" : self.mGetMemoryDetails(_mysql_pid)
        }

    def mGetProcCpuUsage(self):
        '''
            This method returns the RAM Usage by each of the processes: Agents, Workers, Scheduler, Supervisor and MySQL Daemon
        '''
        _, _agents_pid, _workers_pid, _scheduler_pid, _supervisor_pid, _mysql_pid = self.__procDetails 

        return {
            "name" : "process cpu usage",
            "hostname" : self.__getFqdn,
            "agent process" : self.mGetCpuUsageDetails(_agents_pid),
            "worker process" : self.mGetCpuUsageDetails(_workers_pid),
            "supervisor process" : self.mGetCpuUsageDetails(_supervisor_pid),
            "scheduler process" : self.mGetCpuUsageDetails(_scheduler_pid),
            "mysql daemon" : self.mGetCpuUsageDetails(_mysql_pid)
        }

    def mGetProcCpuTimes(self):
        '''
            This method returns the CPU Times (user, system, iowait, children user and children system times) by each of the processes: Agents, Workers, Scheduler, Supervisor and MySQL Daemon
        '''
        _, _agents_pid, _workers_pid, _scheduler_pid, _supervisor_pid, _mysql_pid = self.__procDetails 

        return {
            "name" : "process cpu times",
            "hostname" : self.__getFqdn,
            "agent process" : self.mGetCpuTimesDetails(_agents_pid, "agent process"),
            "worker process" : self.mGetCpuTimesDetails(_workers_pid, "worker process"),
            "supervisor process" : self.mGetCpuTimesDetails(_supervisor_pid, "supervisor process"),
            "scheduler process" : self.mGetCpuTimesDetails(_scheduler_pid, "scheduler process"),
            "mysql daemon" : self.mGetCpuTimesDetails(_mysql_pid, "mysql daemon")
        }

    def mGetProcThreadCount(self):
        '''
            This method returns the total number of threads used and subprocesses created by each of the worker process
        '''
        _, _, _workers_pid, _, _, _ = self.__procDetails

        _response = {
            "name": "worker process thread count",
            "hostname": self.__getFqdn,
            "worker process": []
        }

        for _pid in _workers_pid:
            try:
                _proc_thread_count = psutil.Process(pid=_pid).num_threads()
                _proc_subprocess_count = psutil.Process(pid=_pid).children(recursive=True)
                
                _response["worker process"].append({
                    "pid" : _pid,
                    "thread count" :  _proc_thread_count,
                    "subprocess count" : len(_proc_subprocess_count)
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        return _response

    def mGetProcFdCount(self):
        '''
            This method returns the total number of active file descriptors opened up by each of the processes: Agents, Workers, Scheduler, Supervisor and MySQL Daemon
        '''
        _, _agents_pid, _workers_pid, _scheduler_pid, _supervisor_pid, _mysql_pid = self.__procDetails

        return {
            "name" : "active file descriptors",
            "hostname" : self.__getFqdn,
            "max system fd" : self.mGetMaxFds(),
            "agent process" : self.mGetFdUsageDetails(_agents_pid),
            "worker process" : self.mGetFdUsageDetails(_workers_pid),
            "supervisor process" : self.mGetFdUsageDetails(_supervisor_pid),
            "scheduler process" : self.mGetFdUsageDetails(_scheduler_pid),
            "mysql daemon" : self.mGetFdUsageDetails(_mysql_pid)
        }

    def mGetProcTcpConnCount(self):
        '''
            This method returns the number of TCP Connections and Corresponding Port Numbers used by each of the processes: Agents, Workers, Scheduler, Supervisor and MySQL Daemon
        '''
        _, _agents_pid, _workers_pid, _scheduler_pid, _supervisor_pid, _mysql_pid = self.__procDetails
        
        return {
            "name" : "tcp connection count",
            "hostname" : self.__getFqdn,
            "max tcp connections" : self.mGetMaxFds(), #Get the FD Limit
            "agent process" : self.mGetTcpNumDetails(_agents_pid),
            "worker process" : self.mGetTcpNumDetails(_workers_pid),
            "supervisor process" : self.mGetTcpNumDetails(_supervisor_pid),
            "scheduler process" : self.mGetTcpNumDetails(_scheduler_pid),
            "mysql daemon" : self.mGetTcpNumDetails(_mysql_pid)
        }

    def mGetProcCount(self):
        '''
            This method returns a dictionary of the total number of processes and the subprocesses currently running in the system.
        '''
        _response = {
            "name": "total process count",
            "hostname": self.__getFqdn,
            "total process count": len(psutil.pids())
        }
        
        _sub_proc_count=0

        for _proc in psutil.process_iter():
            try:
                _sub_proc_count += len(_proc.children(recursive=True))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        _response["total subprocess count"] = _sub_proc_count
        
        return _response


    def mGetProcAgentUptime(self):
        '''
            This method returns a dictionary consisting of the start date and the total uptime for the parent agent process
        '''
        _parent_agent_pid, _, _, _, _, _ = self.__procDetails
        _proc = psutil.Process(pid=_parent_agent_pid)
        _start_time_for_agent = _proc.create_time()

        _start_time_for_agent_str = time.strftime("%Y-%m-%d %H-%M-%S", time.localtime(_start_time_for_agent))
        
        _current_time = time.time()
        _total_uptime_seconds = _current_time - _start_time_for_agent
        _total_uptime_str = self.mFormatSeconds(_total_uptime_seconds)

        return {
            "name": "exacloud agent uptime",
            "hostname": self.__getFqdn,
            "agent start date(UTC Time)": _start_time_for_agent_str,
            "total uptime": _total_uptime_str
        }

    def mGetProcWorkerUptime(self):
        '''
            This method returns a dictionary consisting of the start date and the total uptime for each of the worker processes
        '''
        _, _, _workers_pid, _, _, _ = self.__procDetails

        _response = {
            "name": "worker process start time",
            "hostname": self.__getFqdn,
            "worker process": []
        }

        for _pid in _workers_pid:
            _proc = psutil.Process(pid=_pid)
            _start_time_for_agent = _proc.create_time()
            
            _start_time_for_agent_str = time.strftime("%Y-%m-%d %H-%M-%S", time.localtime(_start_time_for_agent))
            
            _current_time = time.time()
            _total_uptime_seconds = _current_time - _start_time_for_agent
            _total_uptime_str = self.mFormatSeconds(_total_uptime_seconds)

            _response["worker process"].append({
                "pid": _pid,
                "start date(UTC Time)": _start_time_for_agent_str,
                "total uptime": _total_uptime_str
            })

        return _response
    
    def mGetLogRotatedFiles(self):
        '''
            This method returns a list of log-rotated files
        '''
        _cwd = self.__cwd
        _path = f"{_cwd}/log/"
        _pattern = re.compile(r"^agent\.log\.\d+$")
        _log_rotated_files = []

        for _file in os.listdir(_path):
            if _pattern.match(_file):
                _full_path = os.path.join(_path, _file)
                if os.path.isfile(_full_path): 
                    _log_rotated_files.append(_file)

        return _log_rotated_files
    
    def mParseLogFile(self, file, initialResp={}):
        '''
            This method parses the log file given the name of the file, and returns a dictionary consisting of the accumulated count of each of the HTTP Requests 
        '''
        _cwd = self.__cwd
        _path = f"{_cwd}/log/{file}"
        _response = initialResp

        # Now we shall parse the file and fill out the _response dictionary with the accumulated values
        with open(_path, "r") as ffile:
            _lines = ffile.readlines()
            for _line in _lines:
                if '\"' in _line:
                    _req_type = _line.split('\"')[1].split()[0]
                    if _req_type in ["GET", "POST", "PUT", "DELETE", "PATCH", "CONNECT", "HEAD", "OPTIONS", "TRACE"]:
                        if f"accumulated {_req_type}" in _response:
                            _response[f"accumulated {_req_type}"] += 1
                        else:
                            _response[f"accumulated {_req_type}"] = 1    
        return _response    

    def mHandleLogRotation(self):
        '''
            This method gets the accumulated count of the requests from all the log rotated files: \\
                1. It checks in the registry table if a key corresponding to the name of the file of the rotated log file exists then it is fetched \\
                2. If there is no entry by the file name in the registry table, then a file is parsed and a new entry in the database is created
        '''
        # First step would be to store all the filenames of the form: log1. log.2 and so on
        _log_rotated_files = self.mGetLogRotatedFiles()

        # Query the db for their existence, if nothing is found then parse the file at that path
        _resp = {}

        for _file in _log_rotated_files:
            ebLogInfo(_file)
            _result = self.__ebExacloudDb.mGetRegValueByKey(_file)
            ebLogInfo(_result)
            if _result:
                _stringified_value = _result[0]
                _dict_value = ast.literal_eval(_stringified_value)
                ebLogInfo(_dict_value)
                
                for _key, _value in _dict_value.items():
                    if _key in _resp:
                        _resp[_key] += _value
                    else:
                        _resp[_key] = _value
            else:
                # First we need to parse the file and get the acumulated values
                _dict_value = self.mParseLogFile(_file)
                
                for _key, _value in _dict_value.items():
                    if _key in _resp:
                        _resp[_key] += _value
                    else:
                        _resp[_key] = _value
                
                # Next we need to put it into the database
                self.__ebExacloudDb.mSetRegEntry(_file, str(_dict_value))

        return _resp

    def mGetReqHttpCount(self):
        '''
            This method returns the total number of GET, POST and other HTTP methods and their accumulated counts \\
            This also takes care of the log rotation
        '''
        _cwd = self.__cwd
        _intermediate_response = {} 
        _file = "agent.log"

        # First of all we handle the log rotation and get the accumulated count of https requests if they exist
        _log_rotation_response = self.mHandleLogRotation()

        # Next we parse agent.log and obtain the values of the request counts
        _intermediate_response = self.mParseLogFile(_file, _log_rotation_response) 
        
        # Fetch the previous data from the database
        _data_from_db = self.__ebExacloudDb.mGetLatestMetric('ec_req_metric')
        _prev_data = {}
        
        if _data_from_db:
            _dict = json.loads(_data_from_db[0])
            if "mGetReqHttpCount" in _dict:
                _prev_data = _dict["mGetReqHttpCount"]
        
        _response = {
            "name" : "http request count"
        }

        # Calculate the change in values and also store in the accumulated values
        for _key, _value in _intermediate_response.items():
            if _key in _prev_data:
                _non_accumulated_key = _key.replace("accumulated ", "")
                _response[_non_accumulated_key] = int(_value) - int(_prev_data[_key])
            else:
                _non_accumulated_key = _key.replace("accumulated ", "")
                _response[_non_accumulated_key] = _value

            _response[_key] = _value

        for _key, _value in _prev_data.items():
            if "accumulated" in _key and _key not in _intermediate_response:
                _non_accumulated_key = _key.replace("accumulated ", "")
                _response[_non_accumulated_key] = 0
                _response[_key] = _value

        return _response


    def mGetReqCmdCount(self):
        '''
            This method returns the count, and accumululated count of the commands executed till now
        '''
        _cmd_types, _, _ =  self.__reqDetails
        _intermediate_response = {}

        # Fill out _itermediate_response with the frequency of accumulated commands 
        for _cmd in _cmd_types:
            if f"accumulated {_cmd}" in _intermediate_response:
                _intermediate_response[f"accumulated {_cmd}"] += 1
            else:
                _intermediate_response[f"accumulated {_cmd}"] = 1
        
        _data_from_db = self.__ebExacloudDb.mGetLatestMetric('ec_req_metric')
        _prev_data = {}
        
        # Obtain the previos data from the database
        if _data_from_db:
            _dict = json.loads(_data_from_db[0])
            if "mGetReqCmdCount" in _dict:
                _prev_data = _dict["mGetReqCmdCount"]
        
        _response = {
            "name" : "request command count"
        }

        # Calculate the change in values and also store in the accumulated values
        for _key, _value in _intermediate_response.items():
            if _key in _prev_data:
                _non_accumulated_key = _key.replace("accumulated ", "")
                _response[_non_accumulated_key] = int(_value) - int(_prev_data[_key])
            else:
                _non_accumulated_key = _key.replace("accumulated ", "")
                _response[_non_accumulated_key] = _value

            _response[_key] = _value

        for _key, _value in _prev_data.items():
            if "accumulated" in _key and _key not in _intermediate_response:
                _non_accumulated_key = _key.replace("accumulated ", "")
                _response[_non_accumulated_key] = 0
                _response[_key] = _value

        return _response

    def mGetReqActiveCount(self):
        '''
            This method returns the total number of active requests
        '''
        _, _, _active_requests  = self.__reqDetails

        _response = {
            "name" : "active requests count",
            "active requests" : _active_requests,
        }
        
        return _response; 

    def mGetReqSuccessAndFailureCount(self):
        '''
            This method returns the total number of successes, failures along with their accumulated counts
        '''
        _, _error_types, _ = self.__reqDetails
        
        _intermediate_response = {}
       
       # Fill out the _intermediate_response with frequency of "accumulated successes" and "accumulated failures" 
        for _error in _error_types:
            if _error == "No Errors":
                if "accumulated success" in _intermediate_response:
                    _intermediate_response["accumulated success"] += 1
                else:
                    _intermediate_response["accumulated success"] = 1
            else:
                if "accumulated failure" in _intermediate_response:
                    _intermediate_response["accumulated failure"] += 1
                else:
                    _intermediate_response["accumulated failure"] = 1

        if not _error_types:
            _intermediate_response["accumulated success"] = 0
            _intermediate_response["accumulated failure"] = 0   

        _data_from_db = self.__ebExacloudDb.mGetLatestMetric('ec_req_metric')
        _prev_data = {}
        
        # Fetch the previous data from the database
        if _data_from_db:
            _dict = json.loads(_data_from_db[0])
            if "mGetReqSuccessAndFailureCount" in _dict:
                _prev_data = _dict["mGetReqSuccessAndFailureCount"]
        
        _response = {
            "name" : "success and failure requests count"
        }

        # Calculate the change in values and also store in the accumulated values
        for _key, _value in _intermediate_response.items():
            if _key in _prev_data:
                _non_accumulated_key = _key.replace("accumulated ", "")
                _response[_non_accumulated_key] = int(_value) - int(_prev_data[_key])
            else:
                _non_accumulated_key = _key.replace("accumulated ", "")
                _response[_non_accumulated_key] = _value

            _response[_key] = _value

        for _key, _value in _prev_data.items():
            if "accumulated" in _key and _key not in _intermediate_response:
                _non_accumulated_key = _key.replace("accumulated ", "")
                _response[_non_accumulated_key] = 0
                _response[_key] = _value
        return _response
        
    def mGetDirectorySize(self, path):
        '''
            This method returns the size of a directory given the path to the directory
        '''
        _total_size = 0
        
        for _paths, _, _fnames in os.walk(path):
            for _fname in _fnames:
                _fp = os.path.join(_paths, _fname)
                if not os.path.islink(_fp):
                    _total_size += os.path.getsize(_fp)
        return _total_size / self.CONVERSION_TO_GB

    def mGetFsEcUsage(self):
        '''
            This method returns in a metric dictionary consisting of the path to the exacloud directory, the total change in size (in GB) and the current size (in GB) \\
            For calculating the change in size (in GB), the size of the directory from the previous iteration (if it exists) is obtained, and the difference between the current and the previous sizes are calculated.
        '''
        _path = f"{self.__cwd}/"
        _prev_size = 0
        _size = round(self.mGetDirectorySize(_path), 1)

        _data_from_db = self.__ebExacloudDb.mGetLatestMetric('ec_fs_metric')
        if _data_from_db:
            _dict = json.loads(_data_from_db[0])
            if "mGetFsEcUsage" in _dict and "current size(GB)" in _dict["mGetFsEcUsage"]:
                _prev_size = _dict["mGetFsEcUsage"]["current size(GB)"]
                
        return {
            "name" : "space utilisation by exacloud directory",
            "path" : _path,
            "size change(GB)": round(_size - _prev_size, 1),
            "current size(GB)" : _size
        }

    def mGetFsEcLogFolderUsage(self):
        '''
            This method returns in a metric dictionary consisting of the path to the exacloud logs directory, the total change in size (in GB) and the current size (in GB) \\
            For calculating the change in size (in GB), the size of the directory from the previous iteration (if it exists) is obtained, and the difference between the current and the previous sizes are calculated.
        '''
        _path = f"{self.__cwd}/log/"
        _prev_size = 0
        _size = round(self.mGetDirectorySize(_path), 1)

        _data_from_db = self.__ebExacloudDb.mGetLatestMetric('ec_fs_metric')
        if _data_from_db:
            _dict = json.loads(_data_from_db[0])
            if "mGetFsEcLogFolderUsage" in _dict and "current size(GB)" in _dict["mGetFsEcLogFolderUsage"]:
                _prev_size = _dict["mGetFsEcLogFolderUsage"]["current size(GB)"]
    
        return {
            "name" : "space utilisation by exacloud log directory",
            "path" : _path,
            "size change(GB)": round(_size - _prev_size, 1),
            "current size(GB)" : _size
        }

    def mGetFsEcImagesFolderUsage(self):
        '''
            This method returns in a metric dictionary consisting of the path to the exacloud images directory, the total change in size (in GB) and the current size (in GB) \\
            For calculating the change in size (in GB), the size of the directory from the previous iteration (if it exists) is obtained, and the difference between the current and the previous sizes are calculated.
        '''
        _path = f"{self.__cwd}/images/"
        _prev_size = 0
        _size = round(self.mGetDirectorySize(_path), 1)

        _data_from_db = self.__ebExacloudDb.mGetLatestMetric('ec_fs_metric')
        if _data_from_db:
            _dict = json.loads(_data_from_db[0])
            if "mGetFsEcImagesFolderUsage" in _dict and "current size(GB)" in _dict["mGetFsEcImagesFolderUsage"]:
                _prev_size = _dict["mGetFsEcImagesFolderUsage"]["current size(GB)"]
    
        return {
            "name" : "space utilisation by exacloud images directory",
            "path" : _path,
            "size change(GB)": round(_size - _prev_size, 1),
            "current size(GB)" : _size
        }

    def mGetResults(self):
        '''
            This method returns a dictionary where under each key (metric_category) the corresponding dictionary of the key-value pair (in this case the names of the methods and their respective results) is present.
        '''
        _response = {
            "sys_metric" : {
                "mGetSysCpuUsage" : self.mGetSysCpuUsage(),
                "mGetSysMemUsage" : self.mGetSysMemUsage(),
                "mGetSysDiskUsage" : self.mGetSysDiskUsage(),
                "mGetSysInodeUsage" : self.mGetSysInodeUsage(),
            },

            "ec_proc_metric" : {
                "mGetProcCpuUsage" : self.mGetProcCpuUsage(),
                "mGetProcCpuTimes" : self.mGetProcCpuTimes(),
                "mGetProcMemUsage" : self.mGetProcMemUsage(),
                "mGetProcThreadCount" : self.mGetProcThreadCount(),
                "mGetProcFdCount" : self.mGetProcFdCount(),
                "mGetProcTcpConnCount" : self.mGetProcTcpConnCount(),
                "mGetProcCount" : self.mGetProcCount(),
                "mGetProcAgentUptime" : self.mGetProcAgentUptime(),
                "mGetProcWorkerUptime" : self.mGetProcWorkerUptime(),
            },

            "ec_req_metric" : {
                "mGetReqHttpCount" : self.mGetReqHttpCount(),
                "mGetReqCmdCount" : self.mGetReqCmdCount(),
                "mGetReqActiveCount" : self.mGetReqActiveCount(),
                "mGetReqSuccessAndFailureCount" : self.mGetReqSuccessAndFailureCount()
            },

            "ec_fs_metric" : {
                "mGetFsEcUsage" : self.mGetFsEcUsage(),
                "mGetFsEcLogFolderUsage" : self.mGetFsEcLogFolderUsage(),
                "mGetFsEcImagesFolderUsage" : self.mGetFsEcImagesFolderUsage(),
            }   
        }
        
        return _response

    def mGetOrganizedData(self, metricKey, metricValue):
        '''
            This method takes in the metric_category as metricKey and the corresponding result as metricValue, returns a dictionary consisting of the metricKey, the current timestamp and JSON data of the result.
        '''
        _current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        
        return {
            "category" : metricKey,
            "created_at" : _current_time,
            "data" : json.dumps(metricValue),
        }

    def mInsertDataIntoDb(self):
        '''
            This method calls all the methods and then inserts the results obtained upon each method call into a dictionary: _response \\
            Then organizes the _response dictionary obtained and then finally inserts the data into the database
        '''
        self.__ebExacloudDb.mCreateMetricsTable()
        _response = self.mGetResults()

        for _key, _value in _response.items():
            _metric_info = self.mGetOrganizedData(_key, _value)
            self.__ebExacloudDb.mInsertNewMetrics(_metric_info)

        return "Successfully inserted the data to the db"

    def mInsertUpdatedDataIntoDb(self, functionNames):
        '''
            This method takes in an input a list of functions to be executed and then pushed into the database. \\
            Also stores in the values of the functions listed in functionNames in a dictionary: _response \\
            Lastly, this method calls in the mGetOrganizedData to properly format the data and then inserts the properly formatted data into the metrics table \\
            If the data is successfully inserted to the database then "Successfully inserted the data to the db" \\
            Else if the initial functionNames list is empty then no data is inserted and "Empty config list" is returned by this method
        '''
        if functionNames:
            _response = {}
            for _key, _value in functionNames.items():
                if _value:
                    _response[_key] = {}
                    for _function in _value:
                        _method = getattr(self, _function, None)
                        if callable(_method):
                            _response[_key][_function] = _method()

            if _response:
                self.__ebExacloudDb.mCreateMetricsTable()
                for _key, _value in _response.items():
                    _metric_info = self.mGetOrganizedData(_key, _value)
                    self.__ebExacloudDb.mInsertNewMetrics(_metric_info)

                return "Successfully inserted the data to the db"
        else:
            return "Empty config list"