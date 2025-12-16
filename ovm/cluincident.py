"""
 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    Incident file module implementation

FUNCTION:
    Diagnostics implementation for Incident File

NOTE:
    None

Changelog:
   03/22/2019 - v1 changes:
       1) Basic incident file module functionality

History:
    MODIFIED (MM/DD/YY)
    aypaul   01/30/25 - ER#36802805 Add support for generating tfactl logs for
                        reshape failures.
    akkar    09/05/24 - Bug 36477144: Remove addb install
    aararora 12/07/23 - Bug 36083555: Optimize Incident zip file creation to
                        only include active worker logs.
    ririgoye 09/19/23 - Bug 35784523 - CORRECTION OF OEDA REQUESTS DIRECTORY
                        PATH INTRODUCED IN BUG 35570587
    joysjose 09/06/23 - Enh 35686660 - INCIDENT LOGS COLLECTION IS FAILING POST
                        PATCHING OF DOMU
    aararora 02/21/23 - Add separate zip file for tfactl log collection.
    aararora 08/08/22 - Need to generate crs and asm logs when incident zip
                        file is created
    aypaul   06/17/21 - Bug#32677660 Generate exception policies on
                        create_service/vmgi_reshape failure.
    gurkasin 03/16/21 - Removing exawatcher log collection
    ajayasin 01/21/21 - 32404567 - json sorting issue
    araghave 02/17/20 - BUG 30908200 - DISABLE EXAWATCHER LOG COLLECTION FOR
                        PATCHING DURING INCIDENT LOG COLLECTION.
"""
import glob
import psutil
import os
import re
import json
import zipfile
import errno
import tempfile
import shutil
from exabox.core.Context import get_gcontext
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebThreadLocalLog, ebLogAgent
from exabox.healthcheck.cluhealthcheck import ebCluHealth
from exabox.healthcheck.hcconstants import HcConstants, gCreateServiceStepIncidentTestsMap, gCreateServiceMapDO, gCreateServiceMapUNDO
from exabox.healthcheck.clucheck import NodeConnection
from exabox.ovm.exawatcher import exaBoxExaWatcher
from exabox.config.Config import ebCluCmdCheckOptions, ebCsSubCmdCheckOptions

from exabox.core.DBStore import ebGetDefaultDB

TFACTL_PREFIX = "Tfactl_"

class ebIncidentNode(object):

        def __init__(self, level, destdir, uuid, cluctrl, options, step, do, aOP=None):
                assert (level in ["None", "Normal", "Verbose"])
                self._diag_level = level
                self._uuid = uuid
                self._options = options
                self._cluctrl = cluctrl
                self._step = step
                self._do = do
                self._op = aOP
                self._zipPath = destdir + "/Incident_" + self._uuid + ".zip"
                self._destdir = destdir
                _tfactl_log_path = os.path.join(get_gcontext().mGetBasePath(), "log", "tfactl_logs")
                if not os.path.exists(_tfactl_log_path):
                    os.makedirs(_tfactl_log_path)
                self._zipPathTfactl = os.path.join(_tfactl_log_path, f"{TFACTL_PREFIX}{self._uuid}.zip")
                self._zipfTfactl = None

                try:
                        self._zipF = zipfile.ZipFile(self._zipPath, 'w', zipfile.ZIP_DEFLATED)
                except Exception as ex:
                        _exception_template = "ebIncidentNode(): An exception of type {0} occurred. Arguments:\n{1!r}"
                        _exception_str = _exception_template.format(type(ex).__name__, ex.args)
                        ebLogError(_exception_str)

        # Fetch final xml from exavmimages/conf from dom0 and add this file to zip incident file
        def mFetchExavmImagesFinalXml(self):
                ebLogInfo("*** start mFetchExavmImagesFinalXml() ***")
                _exavmimages_finalxml_dir = self._options.get('exavmimages_finalxml_dir', None)
                if _exavmimages_finalxml_dir is None:
                        _exavmimages_finalxml_dir = '/EXAVMIMAGES/conf/'

                _tmpdirname = tempfile.mkdtemp()
                for _dom0, _domu in self._cluctrl.mReturnDom0DomUPair():
                        try:
                                _nc = NodeConnection(self._cluctrl)
                                _node = _nc.mGetNode(_dom0)
                                _file_name = 'final-' + _domu + '-vm.xml'
                                _src_file_path = _exavmimages_finalxml_dir + _file_name
                                _dest_file_path = _tmpdirname + '/' + _file_name
                                _node.mCopy2Local(_src_file_path, _dest_file_path)
                                if os.path.exists(_dest_file_path):
                                        _path_inside_zip = 'EXAVMIMAGES-CONF-finalxml/'+ _file_name 
                                        self._zipF.write(_dest_file_path, _path_inside_zip)
                                else:
                                        ebLogWarn("Couldn't fetch " + _file_name + "from dom0: "+ _dom0)
                        except Exception as ex:
                                _exception_template = "mFetchExavmImagesFinalXml(): An exception of type {0} occurred. Arguments:\n{1!r}"        
                                _exception_str = _exception_template.format(type(ex).__name__, ex.args)
                                ebLogError(_exception_str)
                shutil.rmtree(_tmpdirname)
                ebLogInfo("*** end mFetchExavmImagesFinalXml() ***")
                                         
                                
                               
                        
        # Put exacloud log, dflt worker logs, thread uuid log into the zip
        def __process_log(self):
                _exacloud_base_path = get_gcontext().mGetBasePath()
                exacloud_log   = _exacloud_base_path + "log/exacloud.log"
                dflt_path = _exacloud_base_path + "log/workers"
                thread_log_path = _exacloud_base_path + "log/threads"
                crashes_path = _exacloud_base_path + "log/crashes"
                _oeda_req_path = self._destdir
    
                oeda_zip_dir = _oeda_req_path + "/WorkDir/"
                infra_patch_dir = _oeda_req_path + "/log/patchmgr_logs/"
                infra_plugin_dir = _oeda_req_path + "/log/patch_logs/"

                try:
                        if os.path.exists(exacloud_log): 
                                self._zipF.write(exacloud_log)

                        try:
                                # Worker logs to put in Incident zip file
                                _log_names = ["dflt_schedule*log", "dflt_schedule*trc", "dflt_schedule*err",
                                        "dflt_supervisor*log", "dflt_supervisor*trc", "dflt_supervisor*err"]
                                # Get current active worker ports from DB to put dflt_worker logs in Incident zip
                                _db = ebGetDefaultDB()
                                _ports_workers = _db.mGetWorkerPorts()
                                # For each port, append the worker log file name to the final list of logs to be zipped
                                for _port in _ports_workers:
                                        _file_types = ["log", "err", "trc"]
                                        for _file_type in _file_types:
                                                _log_names.append(f"dflt_worker_{_port}*{_file_type}")
                                # Get the active agent and their forked agent processes
                                # There will be only one parent Agent and we need the first row (pid)
                                _pid_parent = _db.mGetAgentsPID()[0][0]
                                _parent_process = psutil.Process(int(_pid_parent))
                                _children = _parent_process.children(recursive=True)
                                for _child_agent in _children:
                                        _child_pid = _child_agent.pid
                                        _log_names.append(f"agent_{_child_pid}_*log")
                                # Zip the log files obtained if they exist
                                for _log_name in _log_names:
                                        _log_files_to_write = list(glob.glob(os.path.join(dflt_path, _log_name)))
                                        for _log_file in _log_files_to_write:
                                                if os.path.exists(_log_file):
                                                        self._zipF.write(_log_file)
                        except Exception as ex:
                                ebLogError(f"Error occurred while fetching logs for workers. Error: {ex}.")

                        #Zip the crashes folder for an incident if needed
                        #Get list of all matching files in the exacloud/log/crashes directory.
                        try:
                                _path_exp_crashes = crashes_path + "/**/*.log"
                                _crashdump_files = list(glob.glob(_path_exp_crashes, recursive=True))
                                for _file in _crashdump_files:
                                        if os.path.exists(_file):
                                                self._zipF.write(_file)
                        except Exception as ex:
                                ebLogError(f"Error occurred while fetching crash logs. Error: {ex}.")

                        uuid_regex_log = re.compile(self._uuid + "*.*.log")
                        uuid_regex_trc = re.compile(self._uuid + "*.*.trc")
                        for root, dirs, files in os.walk(thread_log_path):
                                for fh in files:
                                        if uuid_regex_log.match(fh) or uuid_regex_trc.match(fh):
                                                self._zipF.write(os.path.join(root, fh))
                        
                        for fname in os.listdir(oeda_zip_dir):
                                if fname.startswith('Diag') and fname.endswith('zip'):
                                        self._zipF.write(os.path.join(oeda_zip_dir, fname))

                        # To collect exadata patchmgr patch logs only during 
                        # infra patching activity.
                        if self._op == 'patching':
                            for dname in [ infra_plugin_dir, infra_patch_dir]:
                                if os.path.exists(dname):
                                    for pname in os.listdir(dname):
                                        self._zipF.write(os.path.join(dname,pname))
                        
                except EnvironmentError as ex:
                        if ex.errno == errno.ENOSPC:
                                _no_spc_errstr = "Got ENOSPC error while trying to include a file within Incident zip"
                                ebLogError(_no_spc_errstr)
                        _exception_template = "ebIncidentNode.__process_log(): An exception of type {0} occurred. Arguments:\n{1!r}"
                        _exception_str = _exception_template.format(type(ex).__name__, ex.args)
                        ebLogError(_exception_str)
                        return -1

                return 0

        # helper function to execute health checks defined in an array
        def __execute_list(self, _stepnam, _do):
            _list = []
            if _do:
                _list = gCreateServiceStepIncidentTestsMap[_stepnam][gCreateServiceMapDO]
            else:
                _list = gCreateServiceStepIncidentTestsMap[_stepnam][gCreateServiceMapUNDO]

            _exclude_list = ["VlanIdTest", "NtpTest", "GatewayTest", "DeleteBondTest", "CreateBondTest", "DnsTest", "LinkStatusTest", "NetworkPingTest"]
             
            _hcdict = {}
            _hcdict[HcConstants.PROFILE_NAME] = "Profile for %s DO=%s"%(_stepnam,_do)
            _hcdict[HcConstants.CHECK_LIST] = {}
            _hcdict[HcConstants.CHECK_LIST][HcConstants.PROFILE_INCLUDE] = _list[0]
            _hcdict[HcConstants.CHECK_LIST][HcConstants.PROFILE_EXCLUDE] = _exclude_list
            _hcdict[HcConstants.CHECK_LIST][HcConstants.PROFILE_TARGET] = _list[1]
            _hcdict[HcConstants.CHECK_LIST][HcConstants.PROFILE_TAGS] = []
            _hcdict[HcConstants.CHECK_LIST][HcConstants.PROFILE_ALERT_LEVEL] = "all"
            _hcdict[HcConstants.RESULT_LEVEL] = "recommend"

            _hcdict_jsonified = json.dumps(_hcdict)

            try:
                self._options.healthcheck = "custom"

                self._options.jsonconf = json.loads(_hcdict_jsonified)

                _hcobj = ebCluHealth(self._cluctrl, self._options)
                _hcobj.mDoHealthCheck(self._options,aIncident=True)

                _result_zip_name = _hcobj.mGetResultDir()[:-1]+".zip"
                self._zipF.write(_result_zip_name)

            except EnvironmentError as ex:
                if ex.errno == errno.ENOSPC:
                    _no_spc_errstr = "Got ENOSPC error while trying to include a file within Incident zip"
                    ebLogError(_no_spc_errstr)
                _exception_template = "ebIncidentNode.__execute_list(): An exception of type {0} occurred. Arguments:\n{1!r}"
                _exception_str = _exception_template.format(type(ex).__name__, ex.args)
                ebLogError(_exception_str)
                return -1
                
            return 0

        # helper function to execute the health check for the profile entered.
        def __execute_diag(self):
                _fp = get_gcontext().mGetBasePath()+'hcprofile/hc_Incident.prf'

                self._options.healthcheck = "custom"

                try:
                        _tmpfile = open(_fp)
                        self._options.jsonconf = json.load(_tmpfile)

                        _hcobj = ebCluHealth(self._cluctrl, self._options)
                        _hcobj.mDoHealthCheck(self._options)

                        _result_zip_name = _hcobj.mGetResultDir()[:-1]+".zip"
                        self._zipF.write(_result_zip_name)

                except EnvironmentError as ex:
                        if ex.errno == errno.ENOSPC:
                                _no_spc_errstr = "Got ENOSPC error while trying to include a file within Incident zip"
                                ebLogError(_no_spc_errstr)
                        _exception_template = "ebIncidentNode.__execute_diag(): An exception of type {0} occurred. Arguments:\n{1!r}"
                        _exception_str = _exception_template.format(type(ex).__name__, ex.args)
                        ebLogError(_exception_str)
                        return -1
                
                return 0

        def __create_zip_tfactl_object(self):
                try:
                        self._zipfTfactl = zipfile.ZipFile(self._zipPathTfactl, 'w', zipfile.ZIP_DEFLATED)
                except Exception as ex:
                        _exception_template = "ebIncidentNode(): An exception of type {0} occurred in __create_zip_tfactl_object. Arguments:\n{1!r}"
                        _exception_str = _exception_template.format(type(ex).__name__, ex.args)
                        ebLogError(_exception_str)

        def __close_zip_tfactl_object(self):
                self._zipfTfactl.close()

        def __process_tfactl_log(self):
            """This method is to process tfactl logs when an incident happens."""
            try:
                if (not os.path.exists(os.path.join(self._destdir, "log/tfactl_logs"))):
                    # Collect asm and crs logs and add it to the Tfactl zip file
                    # if the tfactl logs are already not collected and the step failure is in ESTP_POSTGI_NID or ESTP_INSTALL_CLUSTER
                    # if the tfactl logs are not collected already and it is a DO operation of cell or node addition.
                    # And remove tfactl log path
                    if (self._step and ebCsSubCmdCheckOptions(self._step, ['gather_tfactl_logs_onfailure'])) or (self._op and ebCluCmdCheckOptions(self._op, ['gather_tfactl_logs_onfailure'])):
                        _domus = [_domu for _, _domu in self._cluctrl.mReturnDom0DomUPair()]
                        _dest_dir = self._cluctrl.mFetchCrsAsmLogs(_domus)
                        if _dest_dir and os.path.exists(_dest_dir):
                            self.__create_zip_tfactl_object()
                            for _file_name in os.listdir(_dest_dir):
                                if self._zipfTfactl:
                                    self._zipfTfactl.write(os.path.join(_dest_dir, _file_name))
                                else:
                                    return -1
                            self.__close_zip_tfactl_object()
                            shutil.rmtree(_dest_dir)
                            ebLogInfo(f"Added tfactl logs to tfactl zip file path {self._zipPathTfactl} and removed {_dest_dir}.")
                elif os.path.exists(os.path.join(self._destdir, "log/tfactl_logs")):
                    # If tfactl logs are generated in one of the elastic steps - add it to Tfactl zip file
                    # And remove tfactl log path
                    _tfactl_logs = os.path.join(self._destdir, "log/tfactl_logs")
                    self.__create_zip_tfactl_object()
                    for _file_name in os.listdir(_tfactl_logs):
                        if self._zipfTfactl:
                            self._zipfTfactl.write(os.path.join(_tfactl_logs, _file_name))
                        else:
                            return -1
                    self.__close_zip_tfactl_object()
                    shutil.rmtree(_tfactl_logs)
                    ebLogInfo(f"Added tfactl logs to tfactl zip file path {self._zipPathTfactl} and removed {_tfactl_logs}.")
            except EnvironmentError as ex:
                if ex.errno == errno.ENOSPC:
                    _no_spc_errstr = "Got ENOSPC error while trying to include tfactl logs within Tfactl zip"
                    ebLogError(_no_spc_errstr)
                _exception_template = "ebIncidentNode.__process_tfactl_log(): An exception of type {0} occurred. Arguments:\n{1!r}"
                _exception_str = _exception_template.format(type(ex).__name__, ex.args)
                ebLogError(_exception_str)
                if self._zipfTfactl:
                    self.__close_zip_tfactl_object()
                    os.remove(self._zipPathTfactl)
                return -1
            return 0

        # called if there is an error; delete the zip
        def __cleanup(self):
                if os.path.exists(self._zipPath):
                        self._zipF.close()
                        os.remove(self._zipPath)                

        def __del__(self):
                if os.path.exists(self._zipPath):
                        self._zipF.close()

        def process(self):
                err = 0
                if self._diag_level == "None":
                        return None

                if not os.path.exists(self._zipPath):
                       return None

                self._cluctrl.mGenerateCustomPolicyFileForThisRequest()
                err = self.__process_log()
                # Even if Incident zip file creation errored out, tfactl log
                # collection should still happen
                if not self._cluctrl.mIsExaScale():
                        self.__process_tfactl_log()

                if err != 0:
                        self.__cleanup()
                        return None

                if self._diag_level == "Normal":
                    if self._step:
                        err = self.__execute_list(self._step, self._do)
                    if self._op in ['db_install']:
                        err = self.__execute_list("ESTP_DB_INSTALL",True)
                elif self._diag_level == "Verbose":
                        #Fetch final xml of Vms from exavmimage dir from dom0
                        self.mFetchExavmImagesFinalXml()

                        err = self.__execute_diag()
                        if err != 0:
                                self.__cleanup()
                                return None
                self._zipF.close()
                return self._zipPath

