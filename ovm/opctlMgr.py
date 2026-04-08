"""
 Copyright (c) 2020, 2026, Oracle and/or its affiliates.

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


