"""
 Copyright (c) 2020, 2025, Oracle and/or its affiliates.

NAME:
    OVM - Operator Access Control

FUNCTION:
    Module to provide CCA resource management
    capabilities

Link:
    https://confluence.oci.oraclecorp.com/display/ADBD/CCA+Rest+API
    https://jira.oci.oraclecorp.com/browse/CCA-84

NOTE:
    None

History:
    nisrikan 12/01/25 - Bug 38705859 - EXACLOUD FIX TO HANDLE THE CAGE CREATION FAILURE IF THE INFRA NODE IS NOT REACHABLE
    nisrikan 06/23/24 - Bug 38053933 - FIX THE ISSUES FOR OPCTL SUPPORT FOR EXACS
    nisrikan 09/30/24 - Bug 37109476 - INSTALL OPCTL RPM FAILING AT EXACLOUD
    nisrikan 01/22/24 - ER 36211263 - ER for OPCTL support for ExaCS in ECRA and Exacloud
    nisrikan 12/01/22 - ER 34831389 - backend to support create user by name
    nisrikan 02/17/22 - Bug 33868806 - unit test for opctl in exacloud
    nisrikan 01/17/22 - Bug 33758487 OPCTL BACKEND OPERATIONS ARE FAILING DUE TO INCORRECT SETUP
    nisrikan 10/18/21 - Bug 33479181 OPCTL INSTALLATION IS FAILING WITH USER ACCESS PERMISSION ERROR
    nisrikan 08/30/21 - EXACS-74930 Install failing because of permission issue
    nisrikan 07/08/21 - ER 33089202 ADBD support
    nisrikan 05/16/21 - Bug 32840344 - MERGE OPCTL TO 21.1.1.3.0
    nisrikan 04/26/21   EXACS-66304 - Merge to main
    kkviswan 04/16/21 - 32778389 REMOTE RSYSLOG SERVER CERTIFICATE VALIDATION WITH CA CERT
    nisrikan 04/01/21 - 32689868 EXASSH NOT RETURNING CLUSTER INFO PROPERLY
    nisrikan 03/12/21 - 32616331 OPCTLEXACLOUD.SH SCRIPT RETURNS INCORRECT EXIT CODE AND ERROR STREAM
    nisrikan 02/17/21 - 32520709 Reduce opctl dependency on exacloud
"""

import json
import logging
import logging.handlers
import os
import socket
import sys
import traceback
import getpass

from exabox.core.Context import get_gcontext
from exabox.core.DBStore import ebGetDefaultDB
from exabox.log.LogMgr import ebLogInfo, ebLogError
from exabox.agent.ebJobRequest import ebJobRequest


class ebOpctlMgr(object):
    def __init__(self, aExaBoxCluCtrl, key, patchConfig, host_info):
        self.__ebox = aExaBoxCluCtrl
        self.__config = get_gcontext().mGetConfigOptions()
        self.__dom0domuName = key
        self.__patchconfig = patchConfig
        self.__ocpsJsonPath = self.__config.get('ocps_jsonpath')
        self.__host_info = host_info
        self.__sudoPath = "/usr/bin/sudo"
        self.__findPath = "/usr/bin/find"
        self.__rpmPath = "/bin/rpm"
        self.__mkdirPath = "/usr/bin/mkdir"
        self.__rmdirPath = "/usr/bin/rmdir"
        self.__chownPath = "/usr/bin/chown"
        self.options = None

        self.__current_user = getpass.getuser()

    def mExecuteCmd(self, aOptions):
        """
        receive the command from the clucontrol and process it accordingly
        the 'usercmd' holds which command need to be executed
        """
        self.options = aOptions

        self.__resourceType = self.mGetJsonValue("resourceType")
        if self.__resourceType is None:
            _err = "input needs resourceType which is not present"
            ebLogError(_err)
            _data_d = {}
            _data_d["error"] = _err
            _data_d["status"] = 301  # specific error code
            self.mUpdateRequestData(_data_d, _err)
            return -1

        # short circuit ExaCS operations. ExaCC operations still have to moved to the new class structure
        if self.__resourceType == "cloudexadatainfrastructure":
            exacs_obj = ExaCloudWrapper.set_infra_type(self.__ebox, "create_logger", options=self.options)
            exacs_obj.init_logging_folders(self.__resourceType)
            exacs_obj.init_status_folders(self.__resourceType)
            return exacs_obj.execute_cmd(self.__host_info)

        self.mInitOpctlLogger()
        self.__logHandler = logging.getLogger('exacloud-opctlMgr')

        # check key and patchconfig
        if self.__dom0domuName is None:
            _err = "input needs key or clustername"
            ebLogError(_err)
            _data_d = {}
            _data_d["error"] = _err
            _data_d["status"] = 400
            self.mUpdateRequestData(_data_d, _err)
            return -1

        if self.__patchconfig is None:
            _err = "input needs patch xml config"
            ebLogError(_err)
            _data_d = {}
            _data_d["error"] = _err
            _data_d["status"] = 400
            self.mUpdateRequestData(_data_d, _err)
            return -1

        _user_cmd = self.mGetJsonValue('usercmd')
        _operation = None
        _err = ''
        _retVal = 0

        self.logInfo(f"cmd is {_user_cmd}")

        if _user_cmd == 'assign':
            _operation = self.mGetJsonValue('operation')
            self.logInfo(f"operation under assign {_operation}")
            if _operation == 'install' or _operation == 'upgrade':  # install is special as it needs to install locally as well
                _retVal, _err = self.mInstallInCPS()
                if _retVal == 0:
                    _retVal = self.mExecuteWrapperScript(_operation)
                elif _retVal == 2:
                    _data_d = dict()
                    _data_d["warning"] = _err
                    _data_d["status"] = 200
                    self.mUpdateRequestData(_data_d, str(_err))
                    _retVal = 0
                else:
                    _data_d = dict()
                    _data_d["error"] = _err
                    _data_d["status"] = 400
                    self.mUpdateRequestData(_data_d, str(_err))
            else:  # all other assign operation like deploy, undeploy, getVersion, updateParUrl
                _retVal = self.mExecuteWrapperScript(_operation)
        else:
            if _user_cmd:
                _retVal = self.mExecuteWrapperScript(_user_cmd)
            else:
                _operation = self.mGetJsonValue('operation')
                _retVal = self.mExecuteWrapperScript(_operation)

        _success = _retVal == 0
        self.logInfo("%s %s %s" % (_user_cmd, _operation if _operation != None else '', 'succeeded' if _success else 'failed'))
        return _retVal

    def mExecuteWrapperScript(self, operation):
        """
        call the main opctl shell script with parameters and process the errors
        """
        _dataD = dict()
        _rc = -1
        _operationStr = ''
        try:
            _dataD['status'] = 202
            self.mUpdateRequestData(_dataD, 'in progress')
            self.logInfo(f"operation {operation} is in progress")

            _opctlExacloudWrapperPath = '/usr/local/opctl/shell'
            _opctlExacloudScript = 'opctlExacloud.sh'

            _remoteCPS = self.__ebox.mCheckConfigOption('remote_cps_host')
            _jsonInput = json.dumps(self.options.jsonconf)

            _cmd = """{sudoPath} -u ecra sh {wrapperPath}/{script} {operation} '{jsonInput}' {clusterName}""".format(
                sudoPath=self.__sudoPath, wrapperPath=_opctlExacloudWrapperPath, script=_opctlExacloudScript,
                operation=operation, jsonInput=_jsonInput, clusterName=self.__dom0domuName)

            if _remoteCPS is not None:
                _cmd += """ {remoteCPS}""".format(remoteCPS=_remoteCPS)
                self.logInfo(f"remote CPS is {_remoteCPS}")
            else:
                _cmd += " None "
                self.logInfo("no remote CPS")

            _cmd += """ {ocpsJsonPath} """.format(ocpsJsonPath=self.__ocpsJsonPath)
            self.logInfo(f"ocpsJsonPath is {self.__ocpsJsonPath}")

            _cmd += """{xmlPath} """.format(xmlPath=self.__patchconfig)
            self.logInfo(f"trying to run {_cmd}")

            _rc, _, _out, _err = self.__ebox.mExecuteLocal(_cmd)
            # return from script comes as returncode, jsonObject
            self.logInfo(f"operation {operation} _rc {_rc} _out {_out} _err {_err}")
            if len(_err) != 0:
                _rc = -1
                _dataD['status'] = 500
                _dataD['error'] = str(_err)
                _operationStr = operation + " failure"
                self.mUpdateRequestData(_dataD, _operationStr)
                return _rc

            if _out != 0:
                self.logInfo(f"return value for {operation} is {_out}")
                _outLines = str(_out).splitlines()
                _e = _outLines[len(_outLines) - 1]
                _rc = _e[_e.find('(') + 1:_e.find(',')]
                _retData = _e[_e.find('{'):_e.rfind('}') + 1]
                _dataD = json.loads(str(_retData))
                if _rc == '0':
                    _rc = 0
                    _operationStr = operation + " success"
                else:
                    _rc = -1
        except Exception as e:
            self.logError(f"exception while executing {operation} {self.mGetStackTrace()}")
            self.logError(f"return value {e}")
            _rc = -1
            _dataD['status'] = 500
            _dataD['error'] = str(e)

        self.logInfo(f"return code {_rc} data sent back {_dataD} : {_operationStr}")
        self.mUpdateRequestData(_dataD, _operationStr)
        return _rc

    def mGetJsonValue(self, tagName):
        """
        function to read jsonconf and populate the value to the local code after validation
        """
        if self.options.jsonconf is not None and tagName in list(self.options.jsonconf.keys()):
            return self.options.jsonconf[tagName]
        else:
            return None

    def mUpdateRequestData(self, aDataD, _status_info):
        """
        update request table with the status of the task so that it can
        send back to user for the status request response.
        """
        _data_d = aDataD
        _reqobj = self.__ebox.mGetRequestObj()
        if _reqobj is not None:
            _reqobj.mSetData(json.dumps(_data_d))
            _reqobj.mSetStatusInfo(_status_info)
            _db = ebGetDefaultDB()
            _db.mUpdateRequest(_reqobj)

    def mGetStackTrace(self):
        _tb = sys.exc_info()[2]
        _tb = traceback.format_tb(_tb)
        return '\n'.join(_tb)

    def mInitOpctlLogger(self):
        """
        log to both exacloud and opctl logger maintaining same format
        """
        # create the log directory if it does not exist
        _opctlBasePath = "/opt/oci/exacc/opctl"
        if hasattr(self.options, 'unittest') and self.options.unittest is True:
            _opctlBasePath = os.getcwd()

        _opctlResourcePath = os.path.join(_opctlBasePath, self.__resourceType)
        _opctlLogPath = os.path.join(_opctlResourcePath, "log")

        # check for base path
        if not os.path.exists(_opctlBasePath) or os.path.isfile(_opctlBasePath):
            if os.path.isfile(_opctlBasePath):
                _rmdirCmd = """{sudoPath} {rmdirPath} -rf {opctlPath}""".format(sudoPath=self.__sudoPath,
                                                                                rmdirPath=self.__rmdirPath,
                                                                                opctlPath=_opctlBasePath)
                self.__ebox.mExecuteLocal(_rmdirCmd)
                ebLogInfo(f"{_opctlBasePath} path was a file")

            # create the base dir and others
            _mkdirCmd = f"{self.__sudoPath} {self.__mkdirPath} -p -m 744 {_opctlLogPath}"
            self.__ebox.mExecuteLocal(_mkdirCmd)

            _chownCmd = f"{self.__sudoPath} {self.__chownPath} -R {self.__current_user} {_opctlBasePath}"
            self.__ebox.mExecuteLocal(_chownCmd)

            ebLogInfo(f"{_opctlLogPath} is created")
        elif not os.path.exists(_opctlResourcePath) or os.path.isfile(_opctlResourcePath):
            if os.path.isfile(_opctlResourcePath):
                _rmdirCmd = f"{self.__sudoPath} {self.__rmdirPath} -rf {_opctlResourcePath}"
                self.__ebox.mExecuteLocal(_rmdirCmd)

                ebLogInfo(f"{_opctlResourcePath} path was a file")

            # create resource dir and others
            _mkdirCmd = f"{self.__sudoPath} {self.__mkdirPath} -p -m 744 {_opctlLogPath}"
            self.__ebox.mExecuteLocal(_mkdirCmd)

            _chownCmd = f"{self.__sudoPath} {self.__chownPath} -R {self.__current_user} {_opctlResourcePath}"
            self.__ebox.mExecuteLocal(_chownCmd)

            ebLogInfo(f"{_opctlLogPath} is created")
        elif not os.path.exists(_opctlLogPath) or os.path.isfile(_opctlLogPath):
            if os.path.isfile(_opctlLogPath):
                _rmdirCmd = f"{self.__sudoPath} {self.__rmdirPath} -rf {_opctlLogPath}"
                self.__ebox.mExecuteLocal(_rmdirCmd)

                ebLogInfo(f"{_opctlLogPath} path was a file")

            # create log dir and others
            _mkdirCmd = f"{self.__sudoPath} {self.__mkdirPath} -p -m 744 {_opctlLogPath}"
            self.__ebox.mExecuteLocal(_mkdirCmd)

            _chownCmd = f"{self.__sudoPath} {self.__chownPath} -R {self.__current_user} {_opctlLogPath}"
            self.__ebox.mExecuteLocal(_chownCmd)
            ebLogInfo(f"{_opctlLogPath} is created")
        else:
            ebLogInfo(f"{_opctlLogPath} exists")

        # get format of the dfltlog
        dfltLogger = logging.getLogger('dfltlog')
        h = dfltLogger.__dict__
        oldHandlerList = h['handlers']
        oldHandler = oldHandlerList[0]
        oldHandlerfmt = getattr(oldHandler, 'formatter', None)

        # create new logger and set its format
        exaCloudOpctlLog = logging.getLogger('exacloud-opctlMgr')
        exaCloudOpctlLog.propagate = False
        logFileName = os.path.join(_opctlLogPath, "opctl-exacloud-wrapper-%(host)s.log")
        log_filename = logFileName % {'host': socket.gethostname()}
        logRotationSize = 10000000
        logRotationNum = 20
        handler = logging.handlers.RotatingFileHandler(log_filename, maxBytes=logRotationSize, backupCount=logRotationNum)
        handler.setFormatter(oldHandlerfmt)
        exaCloudOpctlLog.setLevel(logging.INFO)
        exaCloudOpctlLog.addHandler(handler)
        exaCloudOpctlLog.disabled = False

        # change the mode so that root can also write into log
        os.chmod(log_filename, 0o666)

    def logInfo(self, aString):
        self.__logHandler.info(aString)

    def logError(self, aString):
        self.__logHandler.error(aString)

    def mInstallInCPS(self):
        """
        install RPM in local CPS
        """
        _rpmVersion = None
        _assignInfo = self.mGetJsonValue('assignInfo')
        try:
            _rpmVersion = _assignInfo['rpmVersion']
        except:
            _rpmVersion = None

        if _rpmVersion is None:
            _err = "rpm version to install is None"
            self.logError(_err)
            return -1, _err

        self.logInfo(f"rpm version to install is {_rpmVersion}")
        _rpmName = _rpmVersion + ".rpm"

        # check if the rpm version is present
        _dirPath = "/u01/downloads/opctl/"  # where opctl RPMs are supposed to be present
        _findCmd = """{findPath} {dirPath} -name {_rpmName}""".format(findPath=self.__findPath, dirPath=_dirPath,
                                                                      _rpmName=_rpmName)
        _rc, _, _rpmPath, _e = self.__ebox.mExecuteLocal(_findCmd)
        if _rc != 0 or _e or _rpmPath is None:
            _err = f"rpm {_rpmName} is not present"
            self.logError(_err)
            return -1, _err

        self.logInfo(f"rpm {_rpmName} is present in {_rpmPath}")

        # install rpm
        _installCmd = """{sudoPath} {rpmExecPath} -U --force {rpmPath}""".format(sudoPath=self.__sudoPath,
                                                                                 rpmExecPath=self.__rpmPath,
                                                                                 rpmPath=_rpmPath)
        _rc, _, _, _e = self.__ebox.mExecuteLocal(_installCmd)
        if _rc != 0:
            _err = f"rpm {_rpmName} installation error {_e}"
            self.logError(_err)
            return -1, _err

        self.logInfo("installed rpm, rechecking")

        # check if the rpm is actually installed
        newVersion = self.check_rpm_version()
        if newVersion is None or newVersion != _rpmVersion:
            _err = f"rpm {_rpmName} installation error {_e}"
            self.logError(_err)
            return -1, _err

        self.logInfo(f"successfully check version {_rpmVersion}")
        return 0, None

    def check_rpm_version(self):
        _checkCmd = """{rpmExecPath} -qa opctl-backend-core*""".format(rpmExecPath=self.__rpmPath)
        _rc, _, _out, _err = self.__ebox.mExecuteLocal(_checkCmd)
        if _rc != 0:
            _err = f"rpm check error {_err}"
            self.logError(_err)
            return None

        version = _out.strip()
        self.logError(f"returned rpm version {version}")
        return version


class ExaCloudWrapper(object):
    def __init__(self, infra, ebox, logger, options, base_path):
        self.ebox = ebox
        self.options = options
        self.infra_type = infra
        self.current_user = getpass.getuser()

        self.rpm_exec_path = "/bin/rpm"
        self.find_exec_path = "/usr/bin/find"
        self.sudo_exec_path = ""
        self.rmdir_path = "/usr/bin/rmdir"
        self.chown_path = "/usr/bin/chown"
        self.mkdir_path = "/usr/bin/mkdir"
        self.rpm_storage_path = "/u01/downloads/opctl/"

        self.opctl_base_path = base_path
        self.opctl_resource_path = None
        self.opctl_log_path = None

        if options:
            self.json_input = self.options.jsonconf

        # create logger or use an already existing one
        if logger == "create_logger":
            self.init_logging_folders(infra)
            self.logger = logging.getLogger('exacloud-opctlMgr')
        else:
            self.opctl_resource_path = os.path.join(self.opctl_base_path, self.infra_type)
            self.opctl_log_path = os.path.join(self.opctl_resource_path, "log")
            self.logger = logging.getLogger('exacloud-opctlMgr')

    @classmethod
    def set_infra_type(self, ebox=None, logger=None, options=None, infra="cloudexadatainfrastructure"):
        """
        set the infra type, currently support only ExaCS
        """
        if infra == "cloudexadatainfrastructure":
            return ExaCSExacloudWrapper(infra, ebox, logger, options)

    def execute_cmd(self, cluster_name):
        raise NotImplementedError

    def get_rpm_version(self):
        rpm_version_check = f"""{self.rpm_exec_path} -qa opctl-backend-core*"""
        return_code, _, output, error = self.execute_local(rpm_version_check)
        if return_code != 0:
            error = f"rpm check error {error}"
            return None, error
        version = output.strip()
        return version, None

    def get_json_value(self, key):
        if self.options.jsonconf:
            return self.options.jsonconf.get(key, None)
        return None

    def execute_local(self, cmd):
        _rc, _io, _out, _err = self.ebox.mExecuteLocal(cmd)
        ebLogInfo(f"execution results of cmd {cmd}: return code {_rc} output {_out} error {_err}")
        return _rc, _io, _out, _err

    def execute_backend_script(self, backend_json_input):
        return NotImplementedError

    def install_rpm_on_local_node(self):
        """
        install opctl RPM on the current node
        """
        assign_info = self.get_json_value('assignInfo')
        rpm_version = assign_info.get('rpmVersion', None)
        if not rpm_version:
            error_str = "rpm version to install is None"
            self.logger.error(error_str)
            return -1, None, error_str

        self.logger.info(f"rpm version to install {rpm_version}")

        # check if the rpm version is present
        find_cmd = f"""{self.find_exec_path} {self.rpm_storage_path} -name {rpm_version}"""
        return_code, _, rpm_path, error = self.execute_local(find_cmd)
        if return_code != 0 or error or rpm_path is None:
            error_str = f"rpm {rpm_version} is not present"
            self.logger.error(error_str)
            return -1, rpm_path, error_str

        self.logger.info(f"rpm {rpm_version} is present in {rpm_path}")

        # install rpm
        install_cmd = f"""{self.sudo_exec_path} {self.rpm_exec_path} -U --force {rpm_path} --nodeps"""
        return_code, _, output, error = self.execute_local(install_cmd)
        if return_code != 0:
            error_str = f"rpm {rpm_version} installation error {error}"
            self.logger.error(error_str)
            return -1, output, error_str

        self.logger.info("installed rpm, rechecking")

        # check if the rpm is actually installed
        new_version, _ = self.get_rpm_version()
        installed_version = new_version + ".rpm"
        if installed_version is None or installed_version != rpm_version:
            error_str = f"rpm {rpm_version} installation error {error}"
            self.logger.error(error_str)
            return -1, None, error_str

        self.logger.info(f"successfully check version {rpm_version}")
        return 0, None, None

    def update_exacloud_db(self, status, data, aParams):
        """
        update request table with the status of the task so that it can
        send back to user for the status request response.
        """
        if status == 202:
            status_info = "inprogress"
        elif status == 200:
            status_info = "success"
        else:
            status_info = "failed"

        db = ebGetDefaultDB()
        # for requests that come from mShowStatus from agent.py
        if aParams:
            ebLogInfo(f"from agent updating status {status} data {data} uuid {aParams['uuid']}")
            req_obj = db.mGetRequest(aParams["uuid"])
            if not req_obj:
                self.logger.error(f"could not get request object for uuid {aParams['uuid']}")
                return req_obj

            opctlJobReq = ebJobRequest(None, aParams)
            opctlJobReq.mPopulate(req_obj)

            # set statusinfo, data, error_str
            if data:
                opctlJobReq.mSetData(json.dumps(data))

            if status_info == "inprogress":
                opctlJobReq.mSetStatus("Pending")
            else:
                opctlJobReq.mSetStatus("Done")

            if status_info == "failed":
                opctlJobReq.mSetError(int(status))
                opctlJobReq.mSetErrorStr(json.dumps(data.get("error_message")))

            db.mUpdateRequest(opctlJobReq, aInternal=True)
            return opctlJobReq
        else:  # for the requests that are got as part of clucontrol
            req_obj = self.ebox.mGetRequestObj()
            if req_obj is None:
                self.logger.error("could not get request object")
                return req_obj

            self.logger.info(f"from clucontrol updating status of {req_obj.mGetUUID()} to {status_info}")

            if status_info == "inprogress":
                req_obj.mSetStatus("Pending")
            else:
                req_obj.mSetStatus("Done")

            if data:
                req_obj.mSetData(json.dumps(data))

            if status_info == "failed":
                req_obj.mSetError(int(status))
                error_message = data.get("error_message") if isinstance(data, dict) else None
                req_obj.mSetErrorStr(error_message)

            db.mUpdateRequest(req_obj, aInternal=True)
            return req_obj

    def get_status_for_idemtoken(self, idemtoken):
        raise NotImplementedError

    def check_status_for_idemtoken(self, uuid, idemtoken):
        raise NotImplementedError

    def get_stack_trace(self):
        trace_back = sys.exc_info()[2]
        trace_back = traceback.format_tb(trace_back)
        return '\n'.join(trace_back)

    def create_dir(self, path, user=None, permissions="744"):
        """
        create a directory with required permissions, mostly used for logging
        """
        # check for base path
        if not user:
            user = self.current_user

        # check for the path
        if os.path.exists(path) and os.path.isdir(path):
            ebLogInfo(f"path {path} exists")  # do not use self.logger, this function is used to create log dir
            chown_cmd = f"{self.sudo_exec_path} {self.chown_path} -R {user} {path}"
            self.execute_local(chown_cmd)
            return

        # if it is not present, start looking at parents
        needed_paths = []
        needed_paths.append(path)
        parent_dir = os.path.dirname(path)
        while parent_dir:
            if os.path.exists(parent_dir) and os.path.isdir(parent_dir):
                break
            needed_paths.append(parent_dir)
            parent_dir = os.path.dirname(parent_dir)

        if needed_paths:
            path_to_create = needed_paths.pop(0)
            if not os.path.exists(path_to_create) or os.path.isfile(path_to_create):
                if os.path.isfile(path_to_create):
                    rmdir_cmd = f"{self.sudo_exec_path} {self.rmdir_path} -rf {path_to_create}"
                    self.execute_local(rmdir_cmd)
                    ebLogInfo(f"path_to_create path was a file")

                mkdir_cmd = f"{self.sudo_exec_path} {self.mkdir_path} -p -m 744 {path_to_create}"
                self.execute_local(mkdir_cmd)
                ebLogInfo(f"{path_to_create} is created")

                chown_cmd = f"{self.sudo_exec_path} {self.chown_path} -R {user} {path_to_create}"
                self.execute_local(chown_cmd)
                ebLogInfo(f"{path_to_create} is created")

    def init_logging_folders(self, resource_type, opctl_base_path=None):
        """
        log to both exacloud and opctl logger maintaining same format
        """
        # create the log directory if it does not exist
        if hasattr(self.options, 'unittest') and self.options.unittest is True:
            _opctlBasePath = os.getcwd()

        if not opctl_base_path:
            opctl_base_path = self.opctl_base_path

        self.opctl_resource_path = os.path.join(opctl_base_path, resource_type)
        self.opctl_log_path = os.path.join(self.opctl_resource_path, "log")

        # create logging path
        self.create_dir(self.opctl_log_path)

        # get format of the dfltlog
        dfltLogger = logging.getLogger('dfltlog')
        h = dfltLogger.__dict__
        oldHandlerList = h['handlers']
        oldHandler = oldHandlerList[0]
        oldHandlerfmt = getattr(oldHandler, 'formatter', None)

        # create new logger and set its format
        exaCloudOpctlLog = logging.getLogger('exacloud-opctlMgr')
        exaCloudOpctlLog.propagate = False
        logFileName = os.path.join(self.opctl_log_path, "opctl-exacloud-wrapper-%(host)s.log")
        log_filename = logFileName % {'host': socket.gethostname()}
        logRotationSize = 10000000
        logRotationNum = 20
        handler = logging.handlers.RotatingFileHandler(log_filename, maxBytes=logRotationSize,
                                                       backupCount=logRotationNum)
        handler.setFormatter(oldHandlerfmt)
        exaCloudOpctlLog.setLevel(logging.INFO)
        exaCloudOpctlLog.addHandler(handler)
        exaCloudOpctlLog.disabled = False

        # change the mode so that root can also write into log
        os.chmod(log_filename, 0o666)

    def init_status_folders(self, resource_type):
        raise NotImplementedError


class ExaCSExacloudWrapper(ExaCloudWrapper):
    def __init__(self, infra, ebox, logger, options):
        self.resource_type = infra
        self.opctl_exacs_base_path = "/u01/.opctl/"
        super().__init__(infra, ebox, logger, options, self.opctl_exacs_base_path)

        # current file will be in path like /u01/ecra_stacks/oracle/ecra_installs/cpdev/mw_home/user_projects/domains/exacloud/exabox/ovm
        # paramiko installed python will be in /u01/ecra_stacks/oracle/ecra_installs/cpdev/mw_home/user_projects/domains/exacloud/bin/python3
        self.python3_path = os.path.dirname(os.path.abspath(__file__))
        self.python3_path = f"{self.python3_path}/../../bin/python3"
        self.backend_script_path = f"{self.python3_path} /usr/local/opctl/opctlexacswrapper/opctlWrapper.py"
        self.backend_status_path = os.path.join(self.opctl_resource_path, ".idemtoken")

    def transform_host_info(self, host_info):
        self.host_info = {}
        self.host_info["host_info"] = {}
        for dom0 in host_info.get("dom0s"):
            self.host_info["host_info"][dom0] = {"type": "dom0"}

        for cell in host_info.get("cells"):
            self.host_info["host_info"][cell] = {"type": "cell"}

    def execute_backend_script(self, backend_json_input):
        self.idemtoken = self.json_input.get("idemtoken", None)
        cmd = f"""{self.backend_script_path} -i {self.idemtoken} -o {self.operation} -j '{json.dumps(backend_json_input)}' -c '{json.dumps(self.host_info)}' """
        return_code, _, out, error = self.execute_local(cmd)
        return return_code, out, error

    def execute_cmd(self, host_info):
        self.transform_host_info(host_info)
        idemtoken = self.get_json_value("idemtoken")

        if (os.path.exists(self.opctl_exacs_base_path) is False) or (os.path.isdir(self.opctl_exacs_base_path) is False):
            error = f"{self.opctl_exacs_base_path} does not exist"
            self.logger.error(error)
            return_value = -1
            status = 500
            data = {"error": error}
            self.update_exacloud_db(status, data, aParams=None)
            return return_value

        user_cmd = self.get_json_value("usercmd")
        if user_cmd == "assign":
            return_value, output, error = self.handle_assign_operations()
        elif user_cmd == "create_user":
            return_value, output, error = self.handle_create_user()
        elif user_cmd == "delete_user":
            return_value, output, error = self.handle_delete_user()
        else:
            error = f"{user_cmd} is not supported"
            output = error
            self.logger.error(error)
            return_value = -1

        status = 500
        data = self.get_status_for_idemtoken(idemtoken)
        if data and "status" in data:
            status = data["status"]
        else:
            if error is not None:
                data = {"error_message": error}
            else:
                data = {"error_message": f"Unknown error during backend operation return {return_value} output {output}"}

        # update exacloud DB
        self.update_exacloud_db(status, data, aParams=None)
        return return_value

    def handle_assign_operations(self):
        self.operation = self.get_json_value("operation")
        if self.operation in ["install", "upgrade"]:
            return_value, output, error = self.handle_install_rpm()
        elif self.operation in ["deploy", "undeploy"]:
            return_value, output, error = self.handle_deploy_undeploy()
        elif self.operation == "getVersion":
            return_value, output, error = self.get_rpm_version()
        elif self.operation in ["collectDebugLog"]:
            return_value, output, error = self.handle_other_assign_operations()
        else:
            return_value = -1
            output = "not implemented"
            error = "not implemented"
        return return_value, output, error

    def handle_install_rpm(self):
        return_value, output, error = self.execute_backend_script(self.json_input.get("assignInfo"))
        if return_value == 0:
           self.enable_disable_exassh(self.operation)
        return return_value, output, error

    def handle_deploy_undeploy(self):
        return_value, output, error = self.execute_backend_script(self.json_input.get("assignInfo"))
        if return_value == 0:
            self.enable_disable_exassh(self.operation)
        return return_value, output, error

    def handle_other_assign_operations(self):
        return self.execute_backend_script(self.json_input.get("assignInfo"))

    def handle_create_user(self):
        self.operation = "create_user"
        return self.execute_backend_script(self.json_input)

    def handle_delete_user(self):
        self.operation = "delete_user"
        return self.execute_backend_script(self.json_input)

    def get_status_for_idemtoken(self, idemtoken):
        data = None
        status_file_for_idemtoken = os.path.join(self.backend_status_path, idemtoken, "status")
        ebLogInfo(f"status file for idemtoken {idemtoken} is {status_file_for_idemtoken}")
        if os.path.exists(status_file_for_idemtoken):
            with open(status_file_for_idemtoken, 'r') as f:
                data = json.load(f)
        return data

    def check_status_for_idemtoken(self, aParams, idemtoken):
        data = self.get_status_for_idemtoken(idemtoken)

        if data:
            status = data["status"]
            return self.update_exacloud_db(status=int(status), data=data, aParams=aParams)
        return None

    def init_status_folders(self, resource_type):
        status_path = os.path.join(self.opctl_resource_path, ".idemtoken")
        self.create_dir(status_path)

    def enable_disable_exassh(self, operation):
        if self.ebox.mCheckConfigOption("enable_block_opctl", "True"):
            # Add enable opctl flag to keys
            if operation in ["deploy", "undeploy", "install"]:
                exakms = get_gcontext().mGetExaKms()
                dom0s, _, cells, switches = self.ebox.mReturnAllClusterHosts()
                hosts = dom0s + cells + switches
                for host in hosts:
                    entries = exakms.mSearchExaKmsEntries({"FQDN": host})
                    if entries:
                        for entry in entries:
                            if operation in ["deploy"]:
                                if "OPCTL_ENABLE" in entry.mGetKeyValueInfo():
                                    self.logger.info(f"ExaKms entry already with OPCTL_ENABLE: {entry}")
                                else:
                                    self.logger.info(f"Adding OPCTL_ENABLE to ExaKms entry: {entry}")
                                    entry.mGetKeyValueInfo()["OPCTL_ENABLE"] = "TRUE"
                                    exakms.mUpdateKeyValueInfo(entry)
                            if operation in ["undeploy"]:
                                if "OPCTL_ENABLE" in entry.mGetKeyValueInfo():
                                    self.logger.info(f"Deleting OPCTL_ENABLE to ExaKms entry: {entry}")
                                    entry.mGetKeyValueInfo().pop("OPCTL_ENABLE")
                                    exakms.mUpdateKeyValueInfo(entry)
                                else:
                                    self.logger.info(f"ExaKms entry already without OPCTL_ENABLE: {entry}")
