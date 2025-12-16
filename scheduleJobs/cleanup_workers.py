"""
$Header:

 Copyright (c) 2014, 2023, Oracle and/or its affiliates. 

NAME:
    cleanup_workers.py - Basic functionality

FUNCTION:
    Provide basic/core API for cleanup worker process

NOTE:
    Please if you are adding change to payloads/apis then update this confluence page:
    https://confluence.oraclecorp.com/confluence/display/EDCS/API+Payloads+from+ECRA+to+ExaCloud

History:

       MODIFIED (MM/DD/YY)
       pbellary    09/22/22 - Creation
"""

import sys
import os
import optparse, argparse
import psutil
import shlex
import subprocess
from  subprocess import PIPE

from exabox.core.DBStore3 import *
from exabox.core.Context import get_gcontext
from exabox.core.Core import exaBoxCoreInit
from exabox.log.LogMgr import ebLogInit, ebLogInfo
from exabox.agent.Agent import ebGetRequestObj
from exabox.scheduleJobs.utils import mExecuteLocal

class CleanUpWorkers():

    def __init__(self, aCmd = None, aUuidList = None):
        exaBoxCoreInit({})
        self.__ctx = get_gcontext()
        self.__options = self.__ctx.mGetArgsOptions()
        ebLogInit(self.__ctx, self.__options)

        self.__exacloudPath = os.getcwd()
        self.__exacloudPath = self.__exacloudPath[0: self.__exacloudPath.rfind("exacloud")+8]
        self.__db = ebGetDefaultDB()

    def mExecuteJob(self, aCmd = None, aUuidList = None):
        ebLogInfo("Calling CleanUpWorkers")
        self.__cmd = aCmd
        self._uuid_list = aUuidList

        if self._uuid_list:
            ebLogInfo(f"List of UUID to be cleaned up: {self._uuid_list}")
            for _uuid in self._uuid_list:
                self.mCleanUp(aUUID=_uuid)
        else:
            _uuid_list = self.__db.mGetActiveRequestsUUID(aCmd=self.__cmd)
            ebLogInfo(f"Fetching Active workers for CMD:{self.__cmd}: {_uuid_list}")
            for _index in _uuid_list:
                _uuid = _index[0]
                self.mCleanUp(aUUID=_uuid)

    def mCleanUp(self, aUUID=None):
        _uuid = aUUID

        active_workers_str = self.__db.mDumpActiveWorkers(aUUID=_uuid)  #get workers that are NOT in an idle state
        active_workers_list = self.getWorkerPIDs(active_workers_str) #get PIDs of active 'worker' processes in this instance
        active_workers_str = active_workers_str.replace("),(","\n").replace("u'","").replace("'","")[2:-3] #format for readability

        _tmp_all_workers_list = [str(_worker) for _worker in active_workers_list if isinstance(_worker, int)]
        if _tmp_all_workers_list:
            ebLogInfo(f'Kill Worker Process with UUID:{_uuid} PID:{_tmp_all_workers_list}')
            mExecuteLocal(f"/bin/kill -9 {_tmp_all_workers_list[0]}" )

        # Update entry in request table corresponding to the operation (uuid)
        _reqobj = ebGetRequestObj(_uuid)
        _reqobj.mSetStatus('Done')
        _reqobj.mSetError('709')
        _reqobj.mSetErrorStr('Error in Execution: [Operation Cleanup endpoint called explicitly]')
        self.__db.mUpdateRequest(_reqobj)

        _locks = self.__db.mGetLocksByUUID(_uuid)
        for _lock in _locks:
            _dom0 = _lock['lock_hostname']
            try:
                self.__db.mDeleteLock(_uuid, ebDBLockTypes.DOM0_LOCK_ACQUIRING, _dom0)
            except Exception as e:
                ebLogWarn('Unable to cleanup UUID {} partially acquired lock: {}'.format(_uuid, e))

        # Remove entry from DB, corresponding to the worker process
        self.__db.mClearWorkers(aUUID=_uuid)
        # Delete entry from registry table
        self.__db.mDelRegByUUID(_uuid) 

    def getWorkerPIDs(self, wlist_str): #get PIDs of '-w and --supervisor' processes in this instance of EC

        #wlist_str is return value of exabox.core.DBStore.ebGetDefaultDB.mDumpWorkers()

        pidlist = [] #declare empty list to store the PID's

        if wlist_str == "()": #check if worker list is empty
            return pidlist

        wlist = ast.literal_eval(wlist_str) #convert wlist_str to matrix
        for w in wlist: #iterate through rows (workers)
            if w[1]!='Exited': #check if active worker
                pidlist.append(int(w[8])) #insert PID of every row into list
        
        worker_types = ['-w', '--supervisor']
        for pid in pidlist:
            if pid and psutil.pid_exists(pid):
                _process = psutil.Process(pid).cmdline()
                if not any(worker in _process for worker in worker_types): #check if PID is NOT an open worker
                    pidlist.remove(pid)
            else:
                pidlist.remove(pid)

        return pidlist

def ebLoadProgramArguments():
    """
    This function fills the PROGRAM_ARGUMENTS & the CLU_CMDS_OPTIONS
    dictionaries with the information on
    exacloud/config/program_arguments.conf
    """
    _program_args = {}
    with open('config/program_arguments.conf', 'r') as _file:
        _program_args = json.load(_file)
    
    _clu_cmds_options = { k: set(v) for k, v in _program_args['clusterctrl']['choices'].items() }
    _program_args['clusterctrl']['choices'] = list(_program_args['clusterctrl']['choices'].keys())

    return _program_args, _clu_cmds_options

PROGRAM_ARGUMENTS, CLU_CMDS_OPTIONS = ebLoadProgramArguments()

def main():
    _cmd = None
    _uuid_list = None

    parser = argparse.ArgumentParser()

    for _prog_arg_name, _prog_arg_kw in PROGRAM_ARGUMENTS.items():

        args = ['-' + _prog_arg_kw['shortname']] if 'shortname' in _prog_arg_kw else []
        args.append('--' + _prog_arg_name)

        kwargs = { k: v for k, v in _prog_arg_kw.items() if k != 'shortname' }
        parser.add_argument(*args, **kwargs)

    _arguments = sys.argv[1:]
    _options = parser.parse_args(_arguments)

    if len(_arguments) == 0:
        ebLogInfo('No Arguments specified...')
        return
    
    if _options.clusterctrl:
        _cmd = 'cluctrl.' + _options.clusterctrl
    if _options.uid:
        _uuid_list = _options.uid.split(',')

    clean = CleanUpWorkers()
    clean.mExecuteJob(_cmd, _uuid_list)

if __name__ == '__main__':
    main()
