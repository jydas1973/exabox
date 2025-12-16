"""
 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    CpsEndpoint - Basic functionality

FUNCTION:
    CPS endpoint of the managment

NOTE:
    None    

History:
    hgaldame    08/26/2025 - 38359085 - oci/exacc: cps sw upgrade enhancement 
                             for report any error after cps deployer completes 
                             successfully
    hgaldame    06/20/2025 - enh 38036854 - exacc gen 2| infra patching | 
                             enhance ecra remoteec command
    hgaldame    05/06/2025 - 37911448 - oci/exacc: oel 7 to oel 8 cps os
                             migration ecra wf task
                             runcpsosstandbyadditionalconfigs failure due to
                             iptables missing
    hgaldame    04/03/2025 - 37687664 - oci/exacc: forwardproxy deployment 
                             fails on oel 7 to oel 8 migration exadata 
                             image 24
    hgaldame    03/10/2025 - 37687625 - oci/exacc: remote manager returns false
                             positive on oel 7 to oel 8 migration exadata image
                             24
    hgaldame    10/25/2024 - enh 37236624 - oci/exacc: remote manager endpoint
                             for execute cps software oel 7 to oel 8 migration
    hgaldame    08/17/2024 - 36959621 - oci/exacc fedramp: change keepalived
                             manual-switchover.sh script location on cps remote
                             manager
    hgaldame    05/16/2024 - 36612813 - oci/exacc gen2 | cpssw fleet upgrade |
                             enhance cps sw upgrade prechecks for run only on
                             primary cps
    hgaldame    02/21/2024 - oci/exacc: enhanced switchover remote manager
                             endpoint on cps
    hgaldame    07/20/2024 - 35626691 - oci/exacc: remoteec enhancement for 
                             allow to create custom log name
    hgaldame    06/16/2023 - 35509904 - oci/exacc: fix error codes on remote
                             manager for match with ecra error catalog
    hgaldame    08/03/2023 - 35160674 - oci/exacc: cps sw upgrade sanity 
                             precheck fail on x10m oel8 env
    hgaldame    10/06/2022 - enh 34676631 - exacc: replicate cps deployer bits
                             under /u01/downloads from primary to standby node on
                             cps sw precheck
    oespinos    30/08/2022 - 34544144 - cps switchover failing with ongoing ops
    hgaldame    09/30/2022 - 34627398 - exacc:bb:22.3.1:cps-sw upgrade: provide
                             proper error code for precheck failure instead of
                             returning generic error
    josedelg    08/17/2022 - 34352494 - CPS OS V2 make sure management logs
                             send to the same path at CPS.
    hgaldame    22/07/2022 - 34352482 - cps sw v2 - make sure that all logs during sw
                             upgrade goes to the same path at cps
    hgaldame    06/30/2022 - 34335012 - exacc:22.3.1.0: restore previous cps deployer 
                             version once cps sw rolling upgrade succeed for 2 cps hosts
    oespinos    06/29/2022 - 34290701 - Provide fqdn for current host in
                             /management/cps endpoint
    hgaldame    06/15/2022 - 34282113 - exacc:bb:cps: after cps upgrade
                             /opt/oci/exacc/deployer/ocps-full/config/version.json
                             file doesnt exist
    hgaldame    05/06/2022 - 34146854 - oci/exacc: persists exacloud remote 
                             ec async request status 
    hgaldame    03/25/2022 - 34003113 - oci/exacc: remote ec endpoint for run 
                             cps sw upgrade needs to be idempotent.
    oespinos    03/17/2022 - 33936934 - Switchover Endpoint For Cpssw Upgrade v2
    hgaldame    03/08/2022 - 33931631 - oci/exacc: enable cps rolling upgrade 
                             action on remote manager endpoint
    hgaldame    03/26/2021 - 32683469 - exacc-oci vpn to wss migration: 
                             version pre-check should handle differences in label
    jesandov    14/04/2019 - Add cps monitor script compatibility
    jesandov    26/03/2019 - File Creation
"""



import re
import os
import sys
import json
import copy
import math
import uuid
import base64
import time
import datetime
import shlex
import subprocess
import glob
import socket
import traceback
import pathlib
from collections import namedtuple
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.managment.src.AsyncTrackEndpoint import AsyncTrackEndpoint
from exabox.managment.src.utils.CpsExaccUtils import CpsLogType, mGenerateUUID, mProcessCpsLog, mBuildProccessResult, generate_custom_log_path
from exabox.utils.node import connect_to_host
import exabox.managment.src.utils.CpsExaccError as error_fwk

class CpsEndpoint(AsyncTrackEndpoint):

    SSH_BIN_FLAGS = ["-o StrictHostKeyChecking=no", "-o UserKnownHostsFile=/dev/null"]
    SUCCESS = 0
    FAILURE = 1

    def __init__(self, aHttpUrlArgs, aHttpBody, aHttpResponse, aSharedData):

        #Initializate the class
        AsyncTrackEndpoint.__init__(self, aHttpUrlArgs, aHttpBody, aHttpResponse, aSharedData)

    def mFetchActiveVersion(self, aKeyName, aErrorInResponse=True):

        _repoRoot = self.mGetConfig().mGetExacloudConfigValue("repository_root")
        _repoFile = self.mSanitizePath("{0}/{1}".format(_repoRoot, "activeVersion.json"))

        if not os.path.exists(_repoFile) and aErrorInResponse:
            self.mGetResponse()['text']   = "Error, activeVersion.json not found on repo_root: {0}".format(_repoRoot)
            self.mGetResponse()['error']  = "Error, activeVersion.json not found on repo_root: {0}".format(_repoRoot)
            self.mGetResponse()['status'] = 500

        else:

            try:
                with open(_repoFile, "r") as _file:
                    _repoJson = json.load(_file)
                    return _repoJson["active"][aKeyName]["download_location"]
            except Exception as e:
                if aErrorInResponse:
                    self.mGetResponse()['text']   = "Error, {0}".format(e)
                    self.mGetResponse()['error']  = "Error, {0}".format(e)
                    self.mGetResponse()['status'] = 500

        return None

    def mGetImageManagmentDownload(self, aKey, aErrorInResponse=True):

        #Absolute path
        if self.mGetBody()["bundle"].startswith("/"):
            _cpsBundle = self.mGetBody()["bundle"]

        #Bundle Name
        elif self.mGetBody()["bundle"].lower() != "latest":
            _repositoryRoot = self.mGetConfig().mGetExacloudConfigValue("repository_root")
            _cpsBundle = "{0}/{1}/{2}".format(_repositoryRoot, aKey, self.mGetBody()["bundle"])

        #Latest case
        else:
            _cpsBundle = self.mFetchActiveVersion(aKey, aErrorInResponse=aErrorInResponse)

        return _cpsBundle


    def mCpsSwUpgrade(self, aUpgradeType=None):
        _cli_args = ""
        if "args" in list(self.mGetBody().keys()):
            _http_args =  self.mGetBody()['args']
            _args_list = _http_args.split()
            if _args_list:
                _patch_list = [ _arg for _arg in _args_list if _arg not in   ["patch", "-patch", "--patch"] ]
                _cli_args = " ".join(_patch_list)
        _ecsLabel  = self.mGetBody()["ecslabel"] if "ecslabel" in self.mGetBody().keys() else None
        aUpgradeType = aUpgradeType if aUpgradeType else "upgrade"
        custom_args = {
            "cli_args": _cli_args,
            "upgradeType": aUpgradeType,
            "ecsLabel" : _ecsLabel
        }
        _uuid = mGenerateUUID()
        _on_finish_args = { "aId": _uuid, "aLogType": CpsLogType.CPS_DEPLOYER}
        aName="upgrade cpssw [{0}]".format(_cli_args)
        self.mGetResponse()["text"] = self.mCreatePythonProcess(self.__mCpsSwUpgrade, custom_args, aId=_uuid,
                                                                aOnFinish=self.mProcessCpsLogOnFinish,
                                                                aOnFinishArgs=[_on_finish_args],
                                                                aName=aName, aPersistState=True)
        return
    
    def __compareEcsLabel(self, aEcsLabel, aConfigJson):
        state_json = aConfigJson.get("state", None)
        action_key = "action_result"
        skipUpgrade = False
        version_key = "label_version"
        cps_version = aConfigJson.get(version_key, None)
        cps_state = None
        if cps_version and cps_version.strip():
            if cps_version.strip() == aEcsLabel.strip() and state_json and action_key in state_json:
                cps_state = state_json[action_key].strip().upper() 
                if cps_state == "SUCCESS":
                    skipUpgrade = True
        return skipUpgrade, cps_version, cps_state 



    def __mCpsSwUpgrade(self, aLogFilename, aProcessId, aCustomArgs):
        _timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
        _cpsSwDir = self.mSanitizePath(self.mGetImageManagmentDownload("cpssw", aErrorInResponse=False))
        _installDir = self.mGetConfig().mGetConfigValue("install_dir")
        _deployer = "{0}/deployer".format(_installDir) if _installDir else None
        _deployerTgz = '{0}/ocps-full/oci-exacc-dpy.tgz'.format(_deployer)
        _token = self.mSanitizePath(self.mGetConfig().mGetConfigValue("ecra_token"))
        _args =  aCustomArgs.get("cli_args","")
        _upgradeType = aCustomArgs.get("upgradeType", "upgrade")
        _rcUpgrade = 1
        _error_code = None
        _remoteHost = self.mGetConfig().mGetExacloudConfigValue("remote_cps_host")
        _remoteHost = _remoteHost if _remoteHost else None
        _dpyVersionFile = os.path.join(_deployer,"ocps-full","config","version.json") if _deployer else None
        _ecsLabel =  aCustomArgs.get("ecsLabel", None)

        with open(aLogFilename, "w+") as _log:
            if _installDir is None or not os.path.exists(_installDir):
                _errMsg = "install_dir not found on basic.conf on cps host"
                self.mAsyncLog(_log, aProcessId, _errMsg, aDebug=True)
                _rcUpgrade = 1
                return mBuildProccessResult(_rcUpgrade,
                                            aErrorCode=error_fwk.CpsCpsSwUpgradeErrorEnum.CPS_SW_UPGRADE_NO_INSTALL_DIR.value )
            if not os.path.exists(_token):
                _errMsg = "Ecra token: '{0}' does not exists or is not accessible on cps host.".format(_token)
                self.mAsyncLog(_log, aProcessId, _errMsg, aDebug=True)
                self.mAsyncLog(_log, aProcessId, "RemoteManagment Debug - Rc: '{0}'".format(_rcUpgrade), aDebug=True)
                return mBuildProccessResult(_rcUpgrade,
                                            aErrorCode=error_fwk.CpsCpsSwUpgradeErrorEnum.CPS_SW_UPGRADE_NO_ECRA_TOKEN.value)
            _tokenJson = None
            try:
                with open(_token, "r") as _file:
                    _tokenJson = json.load(_file)
            except Exception as ex:
                _errorMsg = "End Error Parsing ecra token on localhost, file: '{1}', Exception: '{2}'".format(_token, ex)
                self.mAsyncLog(_log, aProcessId, _errorMsg , aDebug=True)
                self.mAsyncLog(_log, aProcessId, "RemoteManagment Debug - Rc: '{0}'".format(_rcUpgrade), aDebug=True)
                return mBuildProccessResult(_rcUpgrade,
                                            aErrorCode=error_fwk.CpsCpsSwUpgradeErrorEnum.CPS_SW_UPGRADE_NO_ECRA_TOKEN.value)
            _installUser = _tokenJson["linux_users"]["installation"]
            _installgrp  = _tokenJson["linux_groups"]["installation"]
            self.mAsyncLog(_log, aProcessId, "CPS Image Manager Download Area: {0}".format(_cpsSwDir), aDebug=True)
            self.mAsyncLog(_log, aProcessId, "installDir: {0}".format(_installDir), aDebug=True)
            self.mAsyncLog(_log, aProcessId, "token: {0}".format(_token), aDebug=True)
            self.mAsyncLog(_log, aProcessId, "upgradeType: {0}".format(_upgradeType), aDebug=True)
            self.mAsyncLog(_log, aProcessId, "payload ecsLabel: {0}".format(_ecsLabel), aDebug=True)
            self.mAsyncLog(_log, aProcessId, "remoteHost: {0}".format(_remoteHost), aDebug=True)
            if _upgradeType in ["rollingupgrade"] and _deployer and _remoteHost and _ecsLabel:
                # Idempotency 2 cps hosts
                self.mAsyncLog(_log, aProcessId, "Check Idempotency 2 cps host", aDebug=True)
                _cpsNode = exaBoxNode(get_gcontext())
                _cpsNode.mSetUser(_installUser)
                _cpsNode.mConnect(aHost=_remoteHost)
                _dataContent = _cpsNode.mReadFile(_dpyVersionFile).decode('utf-8')
                _dataJson = json.loads(_dataContent)
                _cpsNode.mDisconnect()
                _skipUpgrade, _cps_version, _cps_state = self.__compareEcsLabel(_ecsLabel, _dataJson)
                _msg = "Deployer State: {0}:{1} , Version:{2} state: {3} ".format(\
                    _remoteHost ,_dpyVersionFile, _cps_version, _cps_state)
                self.mAsyncLog(_log, aProcessId, _msg, aDebug=True)
                if _skipUpgrade:
                    _rcUpgrade = 0
                    self.mAsyncLog(_log, aProcessId, "CPS Deployer already on desired version and state success. skip upgrade", aDebug=True)
                    self.mAsyncLog(_log, aProcessId, "RemoteManagment Debug - Rc: '{0}'".format(_rcUpgrade), aDebug=True)
                    return mBuildProccessResult(_rcUpgrade, aErrorCode=None)
            elif _upgradeType in ["rollingupgrade"] and "servers" in _tokenJson and len(_tokenJson["servers"]) == 1 and _deployer and _ecsLabel:
                # Idempotency 1 cps host
                self.mAsyncLog(_log, aProcessId, "Check Idempotency 1 cps host", aDebug=True)
                try:
                    with open(_dpyVersionFile, "r") as _file:
                        _dataJson = json.load(_file)
                        _skipUpgrade = self.__compareEcsLabel(_ecsLabel, _dataJson)
                        _skipUpgrade, _cps_version, _cps_state = self.__compareEcsLabel(_ecsLabel, _dataJson)
                        _msg = "Deployer State: localhost:{0} , Version:{1} state: {2}".format(\
                            _dpyVersionFile, _cps_version, _cps_state)
                        self.mAsyncLog(_log, aProcessId, _msg, aDebug=True)
                        if _skipUpgrade:
                            _rcUpgrade = 0
                            _msg = "Single CPS support. CPS Deployer already on desired version and state success. skip upgrade"
                            self.mAsyncLog(_log, aProcessId, _msg, aDebug=True)
                            self.mAsyncLog(_log, aProcessId, "RemoteManagment Debug - Rc: '{0}'".format(_rcUpgrade), aDebug=True)
                            return mBuildProccessResult(_rcUpgrade, aErrorCode=None)
                except Exception as e:
                    _errMsg = "Can not read file {0}:{1} on localhost continue with upgrade".format(_dpyVersionFile, e)
                    self.mAsyncLog(_log, aProcessId, _errMsg, aDebug=True)
            


            if _cpsSwDir is None:
                _repoRoot = self.mGetConfig().mGetExacloudConfigValue("repository_root")
                _repoFile = os.path.join(_repoRoot, "activeVersion.json") if _repoRoot else "/u01/downloads/activeVersion.json"
                _errMsg = "Invalid definition of '.active.cpssw' entry on cps host on '{0}'. ".format(_repoFile)
                self.mAsyncLog(_log, aProcessId, _errMsg, aDebug=True)
                _rcUpgrade = 1
                self.mAsyncLog(_log, aProcessId, "RemoteManagment Debug - Rc: '{0}'".format(_rcUpgrade), aDebug=True)
                return mBuildProccessResult(_rcUpgrade,
                                            aErrorCode=error_fwk.CpsCpsSwUpgradeErrorEnum.MISSING_CPSSW_ENTRY.value)

            _cpsTar = os.path.join(_cpsSwDir, "ocps-full.tar")
            if not os.path.exists(_cpsTar):
                _errMsg = "Required file: {0} does not exists on cps host".format(_cpsTar)
                self.mAsyncLog(_log, aProcessId, _errMsg, aDebug=True)
                _rcUpgrade = 1
                self.mAsyncLog(_log, aProcessId, "RemoteManagment Debug - Rc: '{0}'".format(_rcUpgrade), aDebug=True)
                return mBuildProccessResult(_rcUpgrade,
                                     aErrorCode=error_fwk.CpsCpsSwUpgradeErrorEnum.MISSING_IMAGE_MANAGER_ARTIFACT.value)
           # cleanup backups older than 5 days
            _num_days = 5 
            _cleanCmd = '/bin/find {0}/backups -maxdepth 1 -mtime +{1} -name "deployer*" -print'.format(_installDir, _num_days)
            _rcClean, _sysOutClean, _ = self.mBashExecution(shlex.split(_cleanCmd))
            if _rcClean == 0 :
                _dir_bkp_list = _sysOutClean.split("\n") if _sysOutClean else []
                for _dir_bkp in _dir_bkp_list:
                    if _dir_bkp and _dir_bkp.strip():
                        if not (os.path.isabs(_dir_bkp) and _dir_bkp.rstrip('/') == os.path.abspath(_dir_bkp)):
                            _warnMsg = "Invalid absolute path : {0} , skip".format(_dir_bkp)
                            self.mAsyncLog(_log, aProcessId, _warnMsg, aDebug=True)
                        else:
                            self.mAsyncLog(_log, aProcessId, "Cleaning backup {0}".format(_dir_bkp), aDebug=True)
                            self.mBashExecution(shlex.split("/usr/bin/sudo -n /bin/rm -rf {0}".format(_dir_bkp)), aRedirect=_log)

            self.mAsyncLog(_log, aProcessId, "Performing upgrade with {0}".format(_cpsTar), aDebug=False)
            try:                   
                _cmdEcList = []
                if os.path.isdir(_deployer):
                    _backup_name =  "{0}/backups/deployer{1}".format(_installDir, _timestamp)
                    _cmdEcList.append("mkdir -p {0}/backups".format(_installDir))
                    _cmdEcList.append("rm -rf {0} ".format(_backup_name))
                    _cmdEcList.append("mv {0} {1}".format(_deployer, _backup_name))
                _cmdEcList.append('mkdir -p {0}'.format(_deployer))
                _cmdEcList.append('tar xvf {0} -C {1}'.format(_cpsTar, _deployer))
                _cmdEcList.append('tar xvzf {0} -C {1}/ocps-full'.format(_deployerTgz, _deployer))
                _cmdEcList.append('chown root:root -R {0}'.format(_deployer))
                _cmdList = [ "sudo -n {0}".format(x) for x in _cmdEcList]
                for _cmd in _cmdList:
                    _rcBkp, _sysOutBkp, _sysErrorBkp = self.mBashExecution(shlex.split(_cmd), aRedirect=_log)
                    if _rcBkp != 0 :
                        _errorMsg = "Error running cmd: {3} : return code: {0}, sysout: {1} syserror: {2}".format(_rcBkp, _sysOutBkp, _sysErrorBkp, _cmd)
                        self.mAsyncLog(_log, aProcessId, _errorMsg, aDebug=True)
                        self.mAsyncLog(_log, aProcessId, "RemoteManagment Debug - Rc: '{0}'".format(_rcBkp), aDebug=True)
                        return mBuildProccessResult(_rcUpgrade,
                                                    aErrorCode=error_fwk.CpsCpsSwUpgradeErrorEnum.CPS_SW_UPGRADE_OPERATION_FAILED.value)
                _script = "{0}/deployer/ocps-full/cps-exacc-dpy".format(_installDir)
                _cmd_upgrade = "sudo -n {0} -t {1} --action={2} {3}".format(_script, _token, _upgradeType, _args)
                if _upgradeType in ["rollingupgrade"] and _remoteHost:
                        _cmd_upgrade = "sudo -n {0} -t {1} --action={2} --host={3} {4}".format(\
                            _script, _token, _upgradeType, _remoteHost, _args)
                #Run the command and return the response
                _rcUpgrade, _sysOutUpgrade, _sysErrorUpgrade = self.mBashExecution(shlex.split(_cmd_upgrade), aRedirect=_log)
                if _rcUpgrade != 0 :
                    _errorMsg = "Error running CPS SW UPGRADE: {3} : return code: {0}, sysout: {1} syserror: {2}".format(\
                        _rcUpgrade, _sysOutUpgrade, _sysErrorUpgrade, _cmd_upgrade)
                    self.mAsyncLog(_log, aProcessId, _errorMsg, aDebug=True)
                    rc_restore = self.mRestoreCpsSwVersion(_deployer, _tokenJson, _backup_name, _log, aProcessId, _timestamp, "UPGRADE_FAIL")
                    if rc_restore != 0:
                        _errorMsg = "Can not proccess CPS SW UPGRADE Version after UPGRADE_FAIL"
                        self.mAsyncLog(_log, aProcessId, _errorMsg, aDebug=True)
                else:
                    if len(_tokenJson["servers"]) == 2 and _upgradeType in ["rollingupgrade"] :
                        _msg = "Detected 2 cps hosts, revert to the previous deployer version"
                        self.mAsyncLog(_log, aProcessId, _msg, aDebug=True)
                        rc_restore = self.mRestoreCpsSwVersion(_deployer, _tokenJson, _backup_name, _log, aProcessId, _timestamp, "UPGRADE_SUCC")
                        if rc_restore != 0:
                            _errorMsg = "Can not proccess CPS SW UPGRADE Version after UPGRADE_SUCC"
                            self.mAsyncLog(_log, aProcessId, _errorMsg, aDebug=True)
                            _rcUpgrade = 1
                    else:
                        self.mAsyncLog(_log, aProcessId, "Single cps detected, no need to process cps sw upgrade version", aDebug=True)

            except Exception:
                _msg = "Exception detected running cps sw upgrade {0} ".format(traceback.format_exc())
                self.mAsyncLog(_log, aProcessId, _msg, aDebug=True)
                _rcUpgrade = 1
            self.mAsyncLog(_log, aProcessId, "RemoteManagment Debug - Rc: '{0}'".format(_rcUpgrade), aDebug=True)
        return mBuildProccessResult(_rcUpgrade, aErrorCode=None)

    def mRestoreCpsSwVersion(self, aDeployer, aTokenJson, aBkpName, aLog, aProcessId, aTimestamp, aAction ):
        _user_catalogue = {"ecra":"ecra"}
        _group_catalogue = {"dba":"dba"}
        _installUser = _user_catalogue.get(aTokenJson["linux_users"]["installation"], "ecra")
        _installgrp  = _group_catalogue.get(aTokenJson["linux_groups"]["installation"], "dba")
        _installDir = self.mSanitizePath(self.mGetConfig().mGetConfigValue("install_dir"))
        _cmdRollbackList = list()
        glob_list = glob.glob("{0}/ocps-full/logs/oci_exacc_dpy*.log".format(aDeployer))
        _return_code = 0
        _prev_name =  "{0}/backups/deployer_{1}_{2}".format(_installDir, aTimestamp, aAction)
        # preserve cps deployer logs if any
        if glob_list:
            for _log_dpy in glob_list:
                _log_path = os.path.abspath(_log_dpy)
                _cmdRollbackList.append("sudo -n chown {0}:{1} {2}".format(_installUser,_installgrp, _log_path))
                _cmdRollbackList.append("sudo -n cp -rfp {0} {1}/ocps-full/logs/".format(_log_path, aBkpName))
        if os.path.exists(aBkpName):
            _cmdRollbackList.append("mkdir -p {0}/backups".format(_installDir))
            _cmdRollbackList.append("sudo -n cp -rfp {0} {1}".format(aDeployer, _prev_name))
            _cmdRollbackList.append("sudo -n rm -rf {0}".format(aDeployer))
            _cmdRollbackList.append("sudo -n mv {0} {1}".format(aBkpName, aDeployer))
        self.mAsyncLog(aLog, aProcessId, "Executing commands for action: '{0}'".format(aAction), aDebug=True)
        for _cmd in _cmdRollbackList:
            self.mAsyncLog(aLog, aProcessId, "{0}".format(_cmd), aDebug=True)
            _rcLocal, _sysOutLocal, _sysErrorLocal = self.mBashExecution(shlex.split(_cmd))
            if _rcLocal != 0 :
                _errorMsg = "Error running cmd: {3} : return code: {0}, sysout: {1} syserror: {2}".format(\
                    _rcLocal, _sysOutLocal, _sysErrorLocal, _cmd)
                self.mAsyncLog(aLog, aProcessId, _errorMsg, aDebug=True)
                _return_code = _rcLocal
        return _return_code

    def mCpsOsUpgrade(self):
        
        _targetVersion = None  
        _exapath = self.mGetConfig().mGetExacloudPath()
        _script = "{0}/exabox/infrapatching/cps/{1}".format(_exapath, "cps-os-upgrader")
        _cpsosLocation = self.mGetImageManagmentDownload("cpsos")

        '''
         To read path of newly deployed location of cpsos
         upgrade script, refer this section of code, else
         fall back to image downloader path.
        '''

        if os.path.exists(_script):
            '''
               Example of a CPS OS patch location :

                   _cpsosLocation="/u01/downloads/cpsos/21.1.0.0.0_210310"
                   _cpsosLocation="/u01/downloads/cpsos/19.2.15.0.0_200310/"
            '''
            _targetVersion = _cpsosLocation.split('/')[-1]
            if _targetVersion == '':
                _targetVersion = _cpsosLocation.split('/')[-2]

        else:
            '''
             if infrapatching cps-os-upgrader script
             does not exist, fall back to tarball script
            ''' 
            _script = os.path.join(_cpsosLocation, "cps-os-upgrader")

        _args = ""
        if "args" in list(self.mGetBody().keys()):
            _args =  self.mGetBody()['args']

        _remoteCpsHost = self.mGetConfig().mGetExacloudConfigValue("remote_cps_host")
        if _remoteCpsHost:
            _args = '{0} --remote_cps_host={1}'.format(_args, _remoteCpsHost)
            filter_arg = [local_arg for local_arg in _args.split() if local_arg.strip() == "patch"]
            if filter_arg:
                result_pre_migr, _logFile = self.run_pre_cps_os_upgrade(_remoteCpsHost, _targetVersion)
                if result_pre_migr != CpsEndpoint.SUCCESS:
                    error_msg = f'Error running run_pre_cps_os_upgrade, check log file {_logFile}'
                    self.mGetLog().mError(error_msg)
                    self.mGetResponse()['text']   = error_msg
                    self.mGetResponse()['error']  = error_msg
                    self.mGetResponse()['status'] = 500
                    return

                
            
        # Since cps-os-upgrader runs from Infra patching location,
        # target version is required to be passed.
        if _script.find(_exapath) > -1:
            _args = '{0} TargetVersion={1}'.format(_args, _targetVersion)

        if not os.path.exists(_script):
            self.mGetResponse()['text']   = "{0} does not exists".format(_script)
            self.mGetResponse()['error']  = "{0} does not exists".format(_script)
            self.mGetResponse()['status'] = 500

        else:
            _cmdList = []

            if _args == "":
                _cmdList.append([_script])
            else:
                _cmdList.append([_script, _args])

            _customArgs = {"cmd_list": _cmdList}
            #since the call back function is needed to capture the stdout and stderr, using mCreatePythonProcess call for it
            _uuid = mGenerateUUID()
            _on_finish_args = { "aId": _uuid, "aTargetDirName": "cpsos"}
            self.mGetResponse()['text'] = self.mCreatePythonProcess(self.mAsyncBashExecutionStdOut,
                                                                    _customArgs,
                                                                    aOnFinish=self.mProcessCpsLogOnFinish,
                                                                    aOnFinishArgs=[_on_finish_args],
                                                                    aName="upgrade cpsos [{0}]".format(_args))

    def mCpsMonitor(self):

        # Fetch args
        _args = ""
        if "args" in self.mGetBody().keys():
            _args =  self.mGetBody()['args']
        _args += " --cps_monitor_bundle"

        # Get Script location
        _installDir = self.mGetConfig().mGetConfigValue("install_dir")
        _script = "{0}/sanity/sanity_tests/sanity_monitor.py".format(_installDir)

        if not os.path.exists(_script):
            self.mGetResponse()['text']   = "{0} does not exists".format(_script)
            self.mGetResponse()['error']  = "{0} does not exists".format(_script)
            self.mGetResponse()['status'] = 500

        else:
            _cmdList = [["python", _script, _args]]
            self.mGetResponse()['text'] = self.mCreateBashProcess(_cmdList, aName="cps monitor [{0}]".format(_args))


    def mPut(self):
        self.mCpsMonitor()

    def mPost(self, aMock=False):
        if self.mGetBody()['type'] == "cpssw":
            self.mCpsSwUpgrade()

        elif self.mGetBody()['type'] == "cpsswrolling":
            self.mCpsSwUpgrade(aUpgradeType="rollingupgrade")

        elif self.mGetBody()['type'] == "cpsswitchover":
            self.mCpsSwitchover(aMock)

        elif self.mGetBody()['type'] == "cpsos":
            self.mCpsOsUpgrade()

        elif self.mGetBody()['type'] == "cpscheck":
            self.mCpsSwCheck()
        
        elif self.mGetBody()['type'] == "cpscleanup":
            self.mCpsCleanup()
        
        elif self.mGetBody()['type'] == "cpsservicescheck":
            self.mCpsServicesCheck()

        elif self.mGetBody()['type'] == "cpsoel8migr":
            self.mCpsOel8Migration()

    def mGet(self, aMock=False):
        
        # Return the hostname of master and standby cps
        _cps_dict = dict()

        # Return Mock response
        if aMock == True:
            _cps_dict = {"MASTER": {"hostname": "cps1", "cps_version":"", "image_version":""},
                         "STANDBY":{"hostname": "cps2", "cps_version":"", "image_version":""}}
            self.mGetResponse()['text'] = _cps_dict
            return
        # End of Mock

        _masterCps = self._mDetectMasterCps()
        _standbyCps = self._mDetectStandbyCps()
        _localHost = self._mGetLocalCPS()
        if _masterCps is None:
            _errorMsg = "Can not detect master node on local host: {0}".format(_localHost)
            self.mGetResponse()['text'] = "Error, {0}".format(_errorMsg)
            self.mGetResponse()['error'] = "Error, {0}".format(_errorMsg)
            self.mGetResponse()['status'] = 500
            self.mGetLog().mError("mGet errorMsg: {0}".format(_errorMsg))
            return 

        _cps_dict["MASTER"] = {"hostname" : _masterCps, "cps_version":"", "image_version":""}
        _cps_dict["STANDBY"] = {"hostname" : _standbyCps, "cps_version":"", "image_version":""}

        _installDir = self.mGetConfig().mGetConfigValue("install_dir")
        _versionFileLoc = os.path.abspath(os.path.join(_installDir, "deployer/ocps-full/config/version.json"))


        for _state, _cps in _cps_dict.items():

            _swcmd = ["/bin/cat", _versionFileLoc]
            _oscmd = ["/bin/sudo", "/usr/local/bin/imageinfo", "-ver"]
            
            if _cps["hostname"] is None:
                continue
            elif _cps["hostname"] != _localHost:
                _swcmd = ["/bin/ssh", *CpsEndpoint.SSH_BIN_FLAGS, _cps["hostname"], " ".join(_swcmd)]
                _oscmd = ["/bin/ssh", *CpsEndpoint.SSH_BIN_FLAGS, _cps["hostname"], " ".join(_oscmd)]

            # Save sw version
            _rt, _stdout, _stderr = self.mBashExecution(_swcmd)

            try:
                _repoJson = json.loads(_stdout)
            except ValueError as e:
                _errorMsg = "failed to read version.json from cps {0}: [{1}]".format(_cps["hostname"], e)
                self.mGetResponse()['text'] = "Error, {0}".format(_errorMsg)
                self.mGetResponse()['error'] = "Error, {0}".format(_errorMsg)
                self.mGetResponse()['status'] = 500
                self.mGetLog().mError("mGet errorMsg: {0}".format(_errorMsg))
                return

            _cpsVersion = _repoJson["label_version"]
            _cps_state = _repoJson.get("state", None)
            _cps_dict[_state]["cps_version"] = _cpsVersion
            _cps_dict[_state]["cps_sw_action_result"] =  "NOTFOUND"
            _cps_dict[_state]["cps_sw_action_name"] =  "NOTFOUND"
            if _cps_state:
                _cps_dict[_state]["cps_sw_action_result"] = _cps_state.get("action_result",  "NOTFOUND")
                _cps_dict[_state]["cps_sw_action_name"] =   _cps_state.get("action",  "NOTFOUND")

            # Save os version
            _rt, _stdout, _stderr = self.mBashExecution(_oscmd)

            if _rt != 0:
                _errorMsg = "failed to get image version from cps {0}, stdout [{1}] stderr [{2}]".format(_cps["hostname"], _stdout, _stderr)
                self.mGetResponse()['text'] = "Error, {0}".format(_errorMsg)
                self.mGetResponse()['error'] = "Error, {0}".format(_errorMsg)
                self.mGetResponse()['status'] = 500
                self.mGetLog().mError("mGet errorMsg: {0}".format(_errorMsg))
                return

            _cps_dict[_state]["image_version"] = _stdout.strip()

        self.mGetResponse()['text'] = _cps_dict

    def mCpsSwitchover(self, aMock=False):

        # Return mock response
        if aMock == True:
            self.mGetResponse()["text"] = {'id': '0000', 'reqtype': 'async call', 'status': 'pending'}
            return
        # End of mock
        
        _args = ""
        if "args" in self.mGetBody().keys():
            _args =  self.mGetBody()['args']
        _name = "CPS switchover: [{0}]".format(_args)

        _target = None
        if "target" in list(self.mGetBody().keys()):
            _target = self.mGetBody()['target']

        _uuid = mGenerateUUID()
        if _target:
            _on_finish_args = { "aId": _uuid, "aTargetDirName": _target }
        else:
            _on_finish_args = { "aId": _uuid }
        self.mGetResponse()["text"] = self.mCreatePythonProcess(self.__mCpsSwitchoverRun, _args, aId=_uuid,
                                                                aOnFinish=self.mProcessCpsLogOnFinish,
                                                                aOnFinishArgs=[_on_finish_args],
                                                                aName=_name)
        return

    def __mCpsSwitchoverRun(self, aLog, aProcessId, aCustomArgs):

        with open(aLog, "a+") as _log:
            _remoteCpsHost = self._mGetRemoteCPS()
            if not _remoteCpsHost:
                _errorMsg = "No remote cps host detected, cannot run switchover."
                self.mAsyncLog(_log, aProcessId, _errorMsg)
                return mBuildProccessResult(1, aErrorCode=error_fwk.CpsCpsSwUpgradeErrorEnum.CPS_SWITCHOVER_FAIL.value )
            _short_localHost = self._mGetLocalCPS().split(".")[0]
            _short_remoteHost = _remoteCpsHost.split(".")[0]
            if _short_localHost == _short_remoteHost:
                _errorMsg = "Remote cps host and localhost {0} are the same, cannot run switchover. Check values on exabox.conf".format(
                    _short_remoteHost)
                self.mAsyncLog(_log, aProcessId, _errorMsg)
                return mBuildProccessResult(1, aErrorCode=error_fwk.CpsCpsSwUpgradeErrorEnum.CPS_SWITCHOVER_FAIL.value )
            
            if self._mHasOngoingOperations():
                _errorMsg = "Exacloud has ongoing operations, cannot run switchover."
                self.mAsyncLog(_log, aProcessId, _errorMsg)
                return mBuildProccessResult(1, aErrorCode=error_fwk.CpsCpsSwUpgradeErrorEnum.CPS_SWITCHOVER_FAIL.value )
            _force = False
            if "args" in list(self.mGetBody().keys()):
                _args_str = self.mGetBody()['args']
                _args_list = _args_str.split()
                if "--force" in _args_list:
                    _force = True
            if not _force:
                if not os.path.exists("/etc/keepalived/MASTER"):
                    _errorMsg = "Cps switchover request received on Host: {0} , but is not master node. Can not run switchover".format(_short_localHost)
                    self.mAsyncLog(_log, aProcessId, _errorMsg)
                    return mBuildProccessResult(1, aErrorCode=error_fwk.CpsCpsSwUpgradeErrorEnum.CPS_SWITCHOVER_FAIL.value)
            else:
                if not os.path.exists("/etc/keepalived/MASTER"):
                    _Msg = "Cps switchover request received on Host: {0} , but is not master node. Forcing run switchover".format(_short_localHost)
                    self.mAsyncLog(_log, aProcessId, _Msg)

        
            _msg = "CPS switchover: detecting MASTER/STANDBY."
            self.mAsyncLog(_log, aProcessId, _msg)

            # Detect MASTER and STANDBY cps
            _oldMaster = self._mDetectMasterCps()
            _oldStandby = self._mDetectStandbyCps()
            _remoteCps = self._mGetRemoteCPS()

            if _oldMaster is None or _oldStandby is None:
                _errorMsg = "Error, failed to detect MASTER and STANDBY cps."
                self.mAsyncLog(_log, aProcessId, _errorMsg)
                return mBuildProccessResult(1, aErrorCode=error_fwk.CpsCpsSwUpgradeErrorEnum.CPS_SWITCHOVER_FAIL.value)

            _msg = "MASTER detected: " + _oldMaster
            _msg += "\nSTANDBY detected: " + _oldStandby
            self.mAsyncLog(_log, aProcessId, _msg)

            # Execute switchover script, retry a few times
            _retry = 0
            _max_retries = 3
            _sleep_time = 60
            _timewait = 120
            _manual_switchover = "/usr/libexec/keepalived/manual-switchover.sh"
            if not os.path.exists(_manual_switchover):
                _manual_switchover = "/etc/keepalived/manual-switchover.sh"

            _cmd = ["/bin/sudo", "/bin/sh", _manual_switchover, "--switchover", "--sleeptime", str(_sleep_time)]
            if _oldMaster == _remoteCps:
                _cmd = [ "/bin/ssh" , *CpsEndpoint.SSH_BIN_FLAGS, _oldMaster, " ".join(_cmd)]

            while(_retry < _max_retries):
                _msg = "Executing switchover script {0} on host {1}".format(_manual_switchover, _oldMaster)
                self.mAsyncLog(_log, aProcessId, _msg)
                _rt, _stdout, _stderr = self.mBashExecution(_cmd, aRedirect=_log)

                if _rt == 0:
                    _msg = "Switchover script return SUCCESS."
                    self.mAsyncLog(_log, aProcessId, _msg)
                    break
                else:
                    _retry = _retry + 1
                    _msg = "Switchover script FAILED."
                    _msg += "\nNumber of retries: " + str(_retry)
                    self.mAsyncLog(_log, aProcessId, _msg)
                    if _retry < _max_retries:
                        time.sleep(_timewait)
                        continue


            if _retry == _max_retries:
                _errorMsg = "Error, failed to execute switchover script after {0} retries.".format(_retry)
                self.mAsyncLog(_log, aProcessId, _errorMsg)
                return mBuildProccessResult(1, aErrorCode=error_fwk.CpsCpsSwUpgradeErrorEnum.CPS_SWITCHOVER_FAIL.value)

            # Detect MASTER and STANDBY again. Check if master cps has changed
            _retry = 0
            time.sleep(30)
            while(_retry < _max_retries):
                _newMaster = self._mDetectMasterCps()
                _newStandby = self._mDetectStandbyCps()

                _msg = "MASTER detected: " + _newMaster
                _msg += "\nSTANDBY detected: " + _newStandby
                self.mAsyncLog(_log, aProcessId, _msg)

                if _newMaster == _oldMaster or _newStandby == _oldStandby:
                    _retry = _retry + 1
                    time.sleep(_timewait)
                else:
                    break

            if _retry == _max_retries:
                _errorMsg = "Error, master cps flag did not change after executing switchover script."
                self.mAsyncLog(_log, aProcessId, _errorMsg)
                return mBuildProccessResult(1, aErrorCode=error_fwk.CpsCpsSwUpgradeErrorEnum.CPS_SWITCHOVER_FAIL.value)

            # Wait and check MASTER and STANDBY again, in case master flag switched back to old master
            time.sleep(30)
            _newMaster = self._mDetectMasterCps()
            _newStandby = self._mDetectStandbyCps()

            if _newMaster == _oldMaster or _newStandby == _oldStandby:
                _errorMsg = "Error, master cps flag changed back to initial state after switchover."
                self.mAsyncLog(_log, aProcessId, _errorMsg)
                return mBuildProccessResult(1, aErrorCode=error_fwk.CpsCpsSwUpgradeErrorEnum.CPS_SWITCHOVER_FAIL.value)

            self.mAsyncLog(_log, aProcessId, "CPS switchover finished with no errors")
            return  mBuildProccessResult(0, aErrorCode=None)

    def _mGetFQDN(self, aHost=""):
        if aHost is None:
            return None

        _attempts = 1
        while (_attempts <= 3):
            try:
                return socket.getfqdn(aHost)
            except Exception:
                time.sleep(5)
                _attempts += 1

        return None

    def _mGetLocalCPS(self):
        return self._mGetFQDN()

    def _mGetRemoteCPS(self):
        _remote_cps = self.mGetConfig().mGetExacloudConfigValue("remote_cps_host")
        if _remote_cps and _remote_cps.strip():
            return self._mGetFQDN(_remote_cps)
        return None

    def _mDetectMasterCps(self):

        # Detects the MASTER cps based on the date of flag file
        _cmd = ["date", "+%s", "-r", "/etc/keepalived/MASTER"]

        _localHost = self._mGetLocalCPS()
        _remoteHost = self._mGetRemoteCPS()

        _cps_date = dict()
        for _cps in [_localHost, _remoteHost]:
            if _cps is None:
                continue

            if _cps == _remoteHost:
                _cmd = ["/bin/ssh", *CpsEndpoint.SSH_BIN_FLAGS, _remoteHost, " ".join(_cmd)]

            _rt, _stdout, _stderr = self.mBashExecution(_cmd)

            if _rt != 0 or _stdout is None:
                continue

            _cps_date[_cps] = int(_stdout)

        # MASTER flag not found on either of the cps
        if len(_cps_date) == 0:
            return None

        # Return the cps with the most recent MASTER flag
        return max(_cps_date.keys(), key=lambda x : _cps_date[x])

    def _mDetectStandbyCps(self):

        # Detects the MASTER cps and returns the opposite
        _localCps = self._mGetLocalCPS()
        _remoteCps = self._mGetRemoteCPS()
        _masterCps = self._mDetectMasterCps()

        if _masterCps is None:
            return None
        elif _masterCps == _localCps:
            return _remoteCps        
        else:
            return _localCps

    def _mHasOngoingOperations(self):

        _database = self.mGetShared()['db']
        _requests = _database.mGetRegCount()

        return _requests is not None and _requests > 0


    def mCpsServicesCheck(self):
        _args = ""
        if "args" in self.mGetBody().keys():
            _args =  self.mGetBody()['args']
        _aName = "cps health check  {0} ".format(_args)
        _uuid = mGenerateUUID()
        _custom_log_name = generate_custom_log_path(self.mGetConfig(),
                                                    _uuid, 
                                                    aSuffixName="cpssw-cpscheck-sanitycheck")
        _on_finish_args = { "aId": _uuid,"aLogType": CpsLogType.SANITY_TOOL,
                           "custom_log_name": _custom_log_name }
        self.mGetResponse()['text'] = self.mCreatePythonProcess(self.__mCpsServicesCheck, _args,
                                                                aId=_uuid,
                                                                aOnFinish=self.mProcessCpsLogOnFinish,
                                                                aOnFinishArgs=[_on_finish_args],
                                                                aName=_aName, aPersistState=True,
                                                                aLogFile=_custom_log_name)

    def __mCpsServicesCheck(self, aLogFilename, aProcessId, aCustomArgs):
        _rc = 0
        with open(aLogFilename, "w+") as _log:
            _installDir = self.mGetConfig().mGetConfigValue("install_dir")
            _sanityDir = os.path.join(_installDir,"sanity")
            _sanityTestsDir = os.path.join(_sanityDir,"sanity_tests")
            _sanityScript =  os.path.join(_sanityTestsDir,"sanity_driver.py")
            _python_bin = os.path.join(_sanityDir,"python","venv","bin","python")
            _cmd_crontab = "/usr/bin/sudo -n crontab -l"
            _rc_cmd, _sysOut, _sysError = self.mBashExecution(shlex.split(_cmd_crontab))
            if _rc_cmd != 0:
                self.mAsyncLog(_log, aProcessId, "Can not get crontab output, running sanity with {0}".format(_python_bin), aDebug=True)
            else:
                if _sysOut:
                    _crontab_list = []
                    _crontab_list = _sysOut.split("\n")
                    for _cron_entry in _crontab_list:
                        _cron_strip = _cron_entry.strip()
                        if _cron_strip and _sanityScript in _cron_strip:
                            if _python_bin not in _cron_strip:
                                _Msg = "Different python bin detected on {0}".format(_cron_strip)
                                self.mAsyncLog(_log, aProcessId, _Msg , aDebug=True)
                                _split_by_script = _cron_strip.split(_sanityScript)
                                if _split_by_script:
                                    _python_bin = _split_by_script[0].strip().split()[-1]
                                    if not os.path.split(_python_bin)[0]:
                                        _python_bin = os.path.join("/usr","bin", _python_bin)
                            break

            _cmdList = list()
            if not os.path.exists(_sanityScript):
                _cpsTar = self.mSanitizePath(os.path.join(self.mFetchActiveVersion("cpssw"), "ocps-full.tar"))
                _Msg = "File {0} not found , extract from {1}".format(_sanityScript, _cpsTar )
                self.mAsyncLog(_log, aProcessId, _Msg , aDebug=True)
                _cmdList.append("/usr/bin/sudo /usr/bin/cp {0} {0}.bkp".format(_sanityScript))
                _cmdList.append('/usr/bin/sudo /usr/bin/tar xvf {0} --strip-components=2 -C {1} ocps-full/SDO/sanity_tests.tgz'.format( _cpsTar, _sanityDir))
                _cmdList.append('/usr/bin/sudo /usr/bin/tar xvzf {0}/sanity_tests.tgz --strip-components=1 -C {1} sanity_tests'.format(\
                    _sanityDir, _sanityTestsDir))
            self.mAsyncLog(_log, aProcessId, "Running sanity with {0}".format(_python_bin), aDebug=True)
            _cmdList.append("/usr/bin/sudo -n /usr/bin/chmod +x {0}".format(_sanityScript))
            _cmdList.append("/usr/bin/sudo -n {0} {1} -c {2}/sanity/config/sanityconfig.conf {3}".format(_python_bin,_sanityScript, _installDir, aCustomArgs))
            _cmdListSplit = [ shlex.split(_cmd) for _cmd in _cmdList]
            for _cmd in _cmdListSplit:
                self.mAsyncLog(_log, aProcessId, "Running command {0}".format(_cmd), aDebug=True)
                _rc_cmd, _sysOut, _sysError = self.mBashExecution(_cmd,aRedirect=_log)
                if _rc_cmd != 0:
                    _errorMsg = "Error running cmd: {3} : rc: {0}, sysout: {1} syserror: {2}".format(_rc_cmd,
                                                                                                     _sysOut,
                                                                                                     _sysError,
                                                                                                     _cmd)
                    self.mAsyncLog(_log, aProcessId, _errorMsg, aDebug=True)
                    self.mAsyncLog(_log, aProcessId, "RemoteManagment Debug - Rc: '{0}'".format(_rc_cmd), aDebug=True)
                    return mBuildProccessResult(_rc_cmd, aErrorCode=error_fwk.CpsCpsSwUpgradeErrorEnum.CPS_SANITY_SOFTWARE_SERVICES_FAIL.value)
            self.mAsyncLog(_log, aProcessId, "RemoteManagment Debug - Rc: '{0}'".format(_rc), aDebug=True)
        return mBuildProccessResult(_rc, aErrorCode=None )



    def mCpsCleanup(self):
        if not os.path.exists(self.mGetConfig().mGetConfigValue("ecra_token")):
            _errorMsg = "ecra token does not exists on cps host."
            self.mGetResponse()['text']   = "Error, {0}".format(_errorMsg)
            self.mGetResponse()['error']  = "Error, {0}".format(_errorMsg)
            self.mGetResponse()['status'] = 500
            return
        _args = ""
        if "args" in self.mGetBody().keys():
            _args =  self.mGetBody()['args']
        _name = "CPS Cleanup [{0}]".format(_args)
        self.mGetResponse()["text"] = self.mCreatePythonProcess(self.__mCpsCleanupEcBackup, _args, aName=_name)
        return

    def mCpsSwCheck(self):
        _args = ""
        if "args" in self.mGetBody().keys():
            _args =  self.mGetBody()['args']
        _aName = "Precheck cps software upgrade {0} ".format(_args)
        _uuid = mGenerateUUID()
        _on_finish_args = {"aId": _uuid, "aLogType": CpsLogType.CPS_CHECK_TOOL}
        self.mGetResponse()['text'] = self.mCreatePythonProcess(self.__mCpsSwCheck, _args,
                                                                aId=_uuid,
                                                                aOnFinish=self.mProcessCpsLogOnFinish,
                                                                aOnFinishArgs=[_on_finish_args],
                                                                aName=_aName, aPersistState=True)
        return

    def __mCpsSwCheck(self, aLogFilename, aProcessId, aCustomArgs):
        _installDir = self.mGetConfig().mGetConfigValue("install_dir")
        _installDir = _installDir if _installDir else "/opt/oci/exacc"
        _token = self.mGetConfig().mGetConfigValue("ecra_token")
        _activeVersion = self.mFetchActiveVersion("cpssw")
        _rc = 0
        with open(aLogFilename, "w+") as _log:
            _token = self.mGetConfig().mGetConfigValue("ecra_token")
            try:
                with open(_token, "r") as _file:
                    _tokenJson = json.load(_file)
            except Exception as ex:
                _rcUpgrade = 1
                _errorMsg = "Error Parsing ecra token on cps host, file: '{1}', Exception: '{2}'".format(_token, ex)
                self.mAsyncLog(_log, aProcessId, _errorMsg , aDebug=True)
                self.mAsyncLog(_log, aProcessId, "RemoteManagment Debug - Rc: '{0}'".format(_rcUpgrade), aDebug=True)
                return mBuildProccessResult(_rcUpgrade, aErrorCode=error_fwk.CpsCpsSwUpgradeErrorEnum.CPS_SW_UPGRADE_NO_ECRA_TOKEN.value)
            if len(_tokenJson["servers"]) > 1:
                if not os.path.exists("/etc/keepalived/MASTER"):
                    _rc_cmd = 1
                    self.mAsyncLog(_log, aProcessId, "CPS SW check attempted on non-primary node. Verify WSS VCN health", aDebug=True)
                    self.mAsyncLog(_log, aProcessId, "RemoteManagment Debug - Rc: '{0}'".format(_rc_cmd), aDebug=True)
                    return mBuildProccessResult(_rc_cmd, aErrorCode=error_fwk.CpsCpsSwUpgradeErrorEnum.CPS_CHECK_NON_PRIMARY_NODE.value)
            _remoteHost = self.mGetConfig().mGetExacloudConfigValue("remote_cps_host")
            _remoteHost = _remoteHost if _remoteHost else None
            if _activeVersion is None:
                _errMsg = "cpssw check fail. entry not found on activeVersion on image manager download area"
                self.mAsyncLog(_log, aProcessId, _errMsg, aDebug=True)
                _rc = 1
                self.mAsyncLog(_log, aProcessId, "RemoteManagment Debug - Rc: '{0}'".format(_rc), aDebug=True)
                return mBuildProccessResult(_rc, aErrorCode=error_fwk.CpsCpsSwUpgradeErrorEnum.MISSING_CPSSW_ENTRY.value)
            _cpsTar = self.mSanitizePath(os.path.join(self.mFetchActiveVersion("cpssw"), "ocps-full.tar")) 
            if not os.path.exists(_cpsTar):
                _errMsg = "File {0} defined on activeVersion.json does not exists on localhost".format(_cpsTar)
                self.mAsyncLog(_log, aProcessId, _errMsg, aDebug=True)
                _rc = 1
                self.mAsyncLog(_log, aProcessId, "RemoteManagment Debug - Rc: '{0}'".format(_rc), aDebug=True)
                return mBuildProccessResult(_rc, aErrorCode=error_fwk.CpsCpsSwUpgradeErrorEnum.MISSING_IMAGE_MANAGER_ARTIFACT.value)
            if _remoteHost:
                _installUser = self.mGetCpsUser()
                _cpsNode = exaBoxNode(get_gcontext())
                _cpsNode.mSetUser(_installUser)
                _cpsNode.mConnect(aHost=_remoteHost)
                if not _cpsNode.mFileExists(_cpsTar):
                    _msg = "File: '{0}' does not exits on host: '{1}' replicating from localhost".format(_cpsTar, _remoteHost)
                    self.mAsyncLog(_log, aProcessId, _msg, aDebug=True)
                    if not _cpsNode.mFileExists(_activeVersion):
                        aCmdStr = "/usr/bin/mkdir -p {0}".format(_activeVersion)
                        _cpsNode.mExecuteCmd(aCmdStr, aTimeout=3600)
                    _msg = "Replicating : '{0}' to host: {1}:{2}".format(_cpsTar, _remoteHost, _cpsTar)
                    self.mAsyncLog(_log, aProcessId, _msg, aDebug=True)
                    _cmd = "/bin/rsync -avzr {0} {1}:{2}".format(_cpsTar, _remoteHost, _cpsTar)
                    _rc_rsync, _sysout, _syserr = self.mBashExecution(shlex.split(_cmd))
                    if _rc_rsync != 0:
                        _error_msg = "Can not rsync file from localhost file: '{0}' to host: {1}:{2}, sysout:'{3}' , syserr:'{4}'".format(\
                        _cpsTar, _remoteHost, _cpsTar, _sysout, _syserr)
                        self.mAsyncLog(_log, _error_msg, _msg, aDebug=True)
                _cpsNode.mDisconnect()
            _precheckDir  = "{0}/prechecks".format(_installDir)
            _precheckScript = os.path.join(_precheckDir, "cps_sw_check/src/cps_sw_check.py")
            _cmdScriptList = list()
            _cmdScriptList.append("/usr/bin/sudo {0}".format(_precheckScript))
            _cmdScriptList.append("--config {0}".format(_token))
            _cmdScriptList.append(aCustomArgs)
            cmd_run_precheck_script = " ".join(_cmdScriptList)
            _cmdList = list()
            if not os.path.exists(_precheckScript):
                _cmdList.append('/usr/bin/sudo /usr/bin/mkdir -p {0}'.format(_precheckDir))
                _cmdList.append('/usr/bin/sudo /usr/bin/rm -rf {0}'.format(_precheckScript))
                _cmdList.append('/usr/bin/sudo /usr/bin/tar xvf {0} --strip-components=2 -C {1} ocps-full/SDO/cps_sw_check.tgz'.format( _cpsTar, _precheckDir))
                _cmdList.append('/usr/bin/sudo /usr/bin/tar xvzf {0}/prechecks/cps_sw_check.tgz -C {1} '.format( _installDir, _precheckDir))
            _cmdList.append("/usr/bin/sudo /usr/bin/chmod +x {0}".format(_precheckScript))
            _cmdList.append(cmd_run_precheck_script)
            _cmdList = [ shlex.split(_cmd) for _cmd in _cmdList]
            for _cmd in _cmdList:
                _rc_cmd, _sysOut, _sysError = self.mBashExecution(_cmd, aRedirect=_log)
                if _rc_cmd != 0:
                    _errorMsg = "Error running cmd: {3} : rc: {0}, sysout: {1} syserror: {2}".format(_rc_cmd,
                                                                                                     _sysOut,
                                                                                                     _sysError,
                                                                                                     _cmd)
                    self.mAsyncLog(_log, aProcessId, _errorMsg, aDebug=True)
                    _error_code = error_fwk.mGetErrorByPrecheckAction(aCustomArgs)
                    self.mAsyncLog(_log, aProcessId, "RemoteManagment Debug - Rc: '{0}'".format(_rc_cmd), aDebug=True)
                    return mBuildProccessResult(_rc_cmd, aErrorCode=_error_code)
            self.mAsyncLog(_log, aProcessId, "RemoteManagment Debug - Rc: '{0}'".format(_rc), aDebug=True)
        return mBuildProccessResult(_rc, aErrorCode=None)

    def __mCpsCleanupEcBackup(self, aLogFilename, aProcessId, aCustomArgs):
        _args = aCustomArgs
        _ecraToken = self.mSanitizePath(self.mGetConfig().mGetConfigValue("ecra_token"))
        _agentHost = self.mGetConfig().mGetExacloudConfigValue("agent_host")
        with open(aLogFilename, "w+") as _log:
            _tokenJson = None
            try:
                with open(_ecraToken, "r") as _file:
                    _tokenJson = json.load(_file)
            except Exception as ex:
                _errorMsg = "Error Parsing ecra token. Host {0}, file {1}, Exception {2}".format(_agentHost,_ecraToken, ex)
                self.mAsyncLog(_log, aProcessId, _errorMsg , aDebug=False)
                return 1
            _cmdCleanEcList = list()
            _cmdCleanEcList.append("/usr/bin/sudo /usr/bin/find {0}".format(self.mSanitizePath(_tokenJson["install_dir"])))
            _cmdCleanEcList.append("-type d -name exacloud.bak* -exec rm -rf {} +")
            _cmdCleanEc = " ".join(_cmdCleanEcList)
            _rcLocal, _sysOutLocal, _sysErrorLocal = self.mBashExecution(shlex.split(_cmdCleanEc), subprocess.PIPE)
            if _rcLocal != 0 :
                _errorMsg = "Error on local host : return code: {0}, sysout: {1} syserror: {2}".format(_rcLocal, _sysOutLocal, _sysErrorLocal)
                self.mAsyncLog(_log, aProcessId, _errorMsg, aDebug=False)
                return 1
            self.mAsyncLog(_log, aProcessId, "Exacloud Backup directory cleaned on {0}".format(_agentHost), aDebug=True)
            _remoteCpsHost = self.mGetConfig().mGetExacloudConfigValue("remote_cps_host")
            if _remoteCpsHost:
                _installUser = _tokenJson["linux_users"]["installation"]
                with connect_to_host(_remoteCpsHost, get_gcontext(), username=_installUser) as _cpsNode:
                    _fin, _fout, _ferr = _cpsNode.mExecuteCmd(_cmdCleanEc)
                    _sysOutRemote = _fout.readlines()
                    _sysErrorRemote = _ferr.readlines()
                    _rcRemote = _cpsNode.mGetCmdExitStatus()

                    if _rcRemote != 0 :
                        _errorMsg = "Error on: {0} host : return code: {1}, sysout: {2}, syserror: {3} ".format(\
                            _remoteCpsHost, _rcRemote, _sysOutRemote, _sysErrorRemote)
                        self.mAsyncLog(_log, aProcessId, _errorMsg, aDebug=False)
                        return 1
                    self.mAsyncLog(_log, aProcessId, "Exacloud Backup directory cleaned on {0}".format(_remoteCpsHost), aDebug=True)
            self.mAsyncLog(_log, aProcessId, "Exacloud Backup directory Done", aDebug=True)
        return 0

    def mCpsOel8Migration(self):
        _args = ""
        if "args" in self.mGetBody().keys():
            _args =  self.mGetBody()['args']
        _name = "CPSS oel 8 migration: [{0}]".format(_args)
        _uuid = mGenerateUUID()
        _custom_log_name = generate_custom_log_path(self.mGetConfig(),
                                                    _uuid, 
                                                    aSuffixName="cpssw-oel8migr")
        _on_finish_args = { "aId": _uuid,"aLogType": CpsLogType.CPS_MIGRATION,
                           "custom_log_name": _custom_log_name }
        self.mGetResponse()["text"] = self.mCreatePythonProcess(self.__mCpsOel8Migration, _args,
                                                                aId=_uuid,
                                                                aOnFinish=self.mProcessCpsLogOnFinish,
                                                                aOnFinishArgs=[_on_finish_args], 
                                                                aName=_name,
                                                                aLogFile=_custom_log_name
                                                                )
        return

    def __mCpsOel8Migration(self, aLogFilename, aProcessId, aCustomArgs):
        with open(aLogFilename, "w+") as _log:
            _short_localHost = self._mGetLocalCPS().split(".")[0]
            if not os.path.exists("/etc/keepalived/MASTER"):
                _errorMsg = "Cps mCpsOel8Migration request received on Host: {0} , but is not master node. Can not run ".format(_short_localHost)
                self.mAsyncLog(_log, aProcessId, _errorMsg)
                return mBuildProccessResult(1, aErrorCode=error_fwk.CpsCpsSwUpgradeErrorEnum.CPS_CHECK_NON_PRIMARY_NODE.value)
            _remoteCpsHost = self.mGetConfig().mGetExacloudConfigValue("remote_cps_host")
            if not _remoteCpsHost:
                _errorMsg = "Single cps detected, can not proceed with migration"
                self.mAsyncLog(_log, aProcessId, _errorMsg, aDebug=False)
                return mBuildProccessResult(1, aErrorCode=error_fwk.CpsCpsSwUpgradeErrorEnum.CPS_CHECK_SINGLE_CPS.value)
            self.mAsyncLog(_log, aProcessId, f'Extract image history from : {_remoteCpsHost}', aDebug=False)
            rc_extrac_image_info, _sysOutRemote = self.extract_image_history_from_cps(_remoteCpsHost)
            if rc_extrac_image_info != 0:
                self.mAsyncLog(_log, aProcessId, _sysOutRemote, aDebug=False)
                return mBuildProccessResult(1, aErrorCode=error_fwk.CpsCpsSwUpgradeErrorEnum.CPS_OELMIGR_OPERATION_FAILED.value)
            is_migr_required = self.mIsOelMigrRequired("".join(_sysOutRemote))
            if not is_migr_required.is_migr_req:
                self.mAsyncLog(_log, aProcessId, is_migr_required.result_msg, aDebug=False)
                return mBuildProccessResult(0, aErrorCode=None)
            self.mAsyncLog(_log, aProcessId, f'Proceed with migration on host {_remoteCpsHost} : {is_migr_required.result_msg}', aDebug=False)
            _installDir = self.mGetConfig().mGetConfigValue("install_dir")
            _token = self.mGetConfig().mGetConfigValue("ecra_token")
            if not _installDir or not _token:
                _errorMsg = "File or directory not found {0} {1} ".format(_installDir, _token)
                self.mAsyncLog(_log, aProcessId, _errorMsg, aDebug=False)
                return mBuildProccessResult(1, aErrorCode=error_fwk.CpsCpsSwUpgradeErrorEnum.CPS_OELMIGR_OPERATION_FAILED.value)
            _script = os.path.join(_installDir, "deployer/ocps-full/cps-exacc-dpy")        
            if  not os.path.exists(_script)  :
                _errorMsg = "File  not found {0} ".format(_script)
                self.mAsyncLog(_log, aProcessId, _errorMsg, aDebug=False)
                return 1            
            _cmdList = list()
            _cmdList.append("/usr/bin/sudo -n {0} --action oel8migr --reset_history".format(_script))
            if aCustomArgs:
                _cmdList.append("{0}".format(aCustomArgs))
            _cmdList.append("-t {0}".format(_token))
            _cmd = " ".join(_cmdList)
            self.mAsyncLog(_log, aProcessId, _cmd, aDebug=True)
            _rcLocal, _sysOutLocal, _sysErrorLocal = self.mBashExecution(shlex.split(_cmd), aRedirect=_log)
            if _rcLocal != 0 :
                _errorMsg = "Error on local host : return code: {0}, sysout: {1} syserror: {2}".format(_rcLocal, _sysOutLocal, _sysErrorLocal)
                self.mAsyncLog(_log, aProcessId, _errorMsg, aDebug=False)
                return mBuildProccessResult(1, aErrorCode=error_fwk.CpsCpsSwUpgradeErrorEnum.CPS_OELMIGR_OPERATION_FAILED.value)
            _sanity_dir = "/opt/oci/exacc/sanity"
            _sanity_python = "/opt/oci/exacc/sanity/python3/bin/python"
            _cmd_sanity = "/usr/bin/sudo -n {0} {1}/sanity_tests/sanity_driver.py -c {1}/config/sanityconfig.conf -d 4 -p  --cpssw_oel8migr_postcheck".format(_sanity_python, _sanity_dir)
            self.mAsyncLog(_log, aProcessId, f'Running: {_cmd_sanity} on host {_remoteCpsHost}', aDebug=False)
            with connect_to_host(_remoteCpsHost, get_gcontext(), username=self.mGetCpsUser()) as _cpsNode:
                _fin, _fout, _ferr = _cpsNode.mExecuteCmd(_cmd_sanity)
                _sysOutSanity = _fout.readlines()
                _sysErrorSanity = _ferr.readlines()
                _rcSanity = _cpsNode.mGetCmdExitStatus()
                if _rcSanity != 0 :
                    _errorMsg = "Error running sanity : return code: {0}, sysout: {1} syserror: {2}".format(_rcSanity,
                                                                                                            _sysOutSanity,
                                                                                                            _sysErrorSanity)
                    self.mAsyncLog(_log, aProcessId, _errorMsg, aDebug=False)
                    return mBuildProccessResult(1, aErrorCode=error_fwk.CpsCpsSwUpgradeErrorEnum.CPS_OELMIGR_POST_SANITY_FAILED.value)
                _sanityMsg = f'sanity completed on host {_remoteCpsHost} : return code: {_rcSanity}'
                self.mAsyncLog(_log, aProcessId, _sanityMsg, aDebug=False)
        return mBuildProccessResult(0, aErrorCode=None)

    def _mExtractCPSVersion(self, aEcsLabel):
        _searchResult = re.search(r"ECS_(\d{1,2})\.(\d{1,2})\.(\d{1,2})", aEcsLabel)
        if not _searchResult:
            return None
        return "".join(list(_searchResult.groups()))

    def _mValidateMinimunCpsVersion(self, aLog, aProcessId, aPayloadVersion, aInstallDir ):
        _versionFileLoc = os.path.abspath(os.path.join(aInstallDir, "deployer", "ocps-full", "config", "version.json"))
        _cpsVersion = None
        with open(_versionFileLoc, "r") as _file:
            _repoJson = json.load(_file)
            _cpsVersion = _repoJson["label_version"]
            _ecsMainPrefix = "ECS_MAIN"
            _msg = "CPS Label: '{0}'  Payload Label '{1}'".format(_cpsVersion, aPayloadVersion)
            self.mAsyncLog(aLog, aProcessId, _msg, aDebug=False)
            if _ecsMainPrefix in _cpsVersion and _ecsMainPrefix in aPayloadVersion:
                _msg = "Both labels contains {0}, continue".format(_ecsMainPrefix)
                self.mAsyncLog(aLog, aProcessId, _msg, aDebug=False)
                return True
            # Minimun required label version ecs 24.3.2 
            _minEcsLabel = 2432
            _payloadVer = self._mExtractCPSVersion(aPayloadVersion)
            _cpsVer = self._mExtractCPSVersion(_cpsVersion)
            if not _payloadVer or not _cpsVer:
                return False
            _payloadVerNum = int(_payloadVer)
            _cpsVerNum = int(_cpsVer)
            if _cpsVerNum < _minEcsLabel or _payloadVerNum < _minEcsLabel:
                _msg = "Minimum CPS Version required: '{0}' CPS Label: '{1}' Payload Label '{2}', can not continue"
                self.mAsyncLog(aLog, aProcessId, _msg.format(_minEcsLabel, _cpsVerNum, _payloadVerNum), aDebug=False)
                return False 
            if _cpsVerNum >= _payloadVerNum:
                _msg = "CPS Label: '{0}' greater or equal than Payload Label '{1}', continue".format(_cpsVerNum, _payloadVerNum)
                self.mAsyncLog(aLog, aProcessId, _msg, aDebug=False)
                return True
        
            _msg = "CPS Label: '{0}' less than Payload Label '{1}', can not continue".format(_cpsVerNum, _payloadVerNum)
            self.mAsyncLog(aLog, aProcessId, _msg, aDebug=False)
        return False

    def mProcessCpsLogOnFinish(self, *args):
        """
          On finish callback for process logs after cps request.
        """
        _logInfoDict = args[0] if len(args) >= 1 else {}
        if not _logInfoDict or not isinstance(_logInfoDict, dict):
            return
        _uuid = _logInfoDict.get("aId", None)
        if not _uuid:
            return
        _log_type = _logInfoDict.get("aLogType", None)
        _target_dir =_logInfoDict.get("aTargetDirName", None)
        _optional_dir = _logInfoDict.get("aOptionalDirDict", None)
        _custom_log_name =_logInfoDict.get("custom_log_name", None)
        mProcessCpsLog(self, _uuid, aLogType=_log_type, aTargetDirName=_target_dir, aOptionalDirDict=_optional_dir, aCustomLogName=_custom_log_name)
        return

    def mGetCpsUser(self):
        _installUser = "ecra"
        _tokenJson, _ = self.mLoadEcraToken(self.mGetConfig().mGetConfigValue("ecra_token"))
        if _tokenJson:
            _installUser = _tokenJson["linux_users"]["installation"]
        return _installUser

    def mLoadEcraToken(self, aTokeLoc):
        _error_msg = None
        _tokenJson = None
        try:
            with open(aTokeLoc, "r") as _file:
                _tokenJson = json.load(_file)
        except Exception:
            _error_msg = traceback.format_exc()
        return _tokenJson, _error_msg
    
    def mSanitizePath(self, file_path : str) -> str:
        """
        Sanitized path. Fortify checks.
        Only specific paths can be accessed. Avoid access to protected files
        Ensure str is a path like, avoid cmd injection
        """
        sanitized_path=""
        file_path_parts = file_path.split("/")
        white_list_cat = {"u01":"u01","opt":"opt"}
        if len(file_path_parts) > 2:
            white_list_dir = white_list_cat.get(file_path_parts[1], None)
            if  white_list_dir:
                _sub_part_list = [ pathlib.PurePath(_single_part) for _single_part in file_path_parts][2:]
                sanitized_path = pathlib.Path((pathlib.PurePath.joinpath(pathlib.PurePath("/"), pathlib.PurePath(white_list_dir), *_sub_part_list))).resolve().as_posix()
        return sanitized_path
    
    def mIsOelMigrRequired(self, aImgHistoryContent):
        """
        """
        ImageHistory = namedtuple("ImageHistory", "imgvers activation_date imgmode imgstatus")
        ResultMigrReq = namedtuple("ResultMigrReq", "is_migr_req result_msg")

        target_img_label = 23
        prev_img_label = 22
        if not aImgHistoryContent:
            return ResultMigrReq(False, "Provided history empty, can not proceed with migration")
        pattern_list = []
        pattern_list.append('^Version\s*:\s*(?P<imgvers>[\d|.]*)?\s')
        pattern_list.append('(Exadata Live Update Version \s*:\s*(?P<liveversion>.*)\s)?')
        pattern_list.append('Image activation date\s*:\s*(?P<actdate>[\w|-]*\s[\w|:]*\s.*)\s')
        pattern_list.append('Imaging mode\s*:\s*(?P<imgmode>\w*)\s')
        pattern_list.append('Imaging status\s*:\s*(?P<imgstatus>\w*)\s')
        pattern = "".join(pattern_list)
        section_re = re.compile(pattern, re.MULTILINE)
        image_history_list = []
        for match_cert in section_re.finditer(aImgHistoryContent):
            imgvers = None
            activation_date = None
            imgmode = None
            imgstatus = None
            if match_cert.group("imgvers"):
                imgvers = match_cert.group("imgvers")
            if match_cert.group("actdate"):
                activation_date = match_cert.group("actdate")
            if match_cert.group("imgmode"):
                imgmode = match_cert.group("imgmode")
            if match_cert.group("imgstatus"):
                imgstatus = match_cert.group("imgstatus")
            if all([imgvers,activation_date,imgmode,imgstatus]):
                image_history_list.append(ImageHistory(imgvers,activation_date,imgmode,imgstatus))
                       
        if not image_history_list:
            return ResultMigrReq(False, f"Can not match any Image history items, can not proceed with migration, provided history: {aImgHistoryContent}")
        last_entry_img_hist = image_history_list[-1]

        if len(image_history_list) == 1:
            _msg =  "Only one entry on image history: {0}, can not continue with migration".format(last_entry_img_hist)
            return ResultMigrReq(False, _msg)

        if last_entry_img_hist.imgstatus.lower() != "success":
            _msg = "The last entry on image history is  not succes: {0}, can not continue with migration".format(last_entry_img_hist)
            return ResultMigrReq(False, _msg)
        second_last_img_hist = image_history_list[-2]
        try:
            num_last_img_hist = int(last_entry_img_hist.imgvers.split(".")[0])
            num_second_last_img_hist  = int(second_last_img_hist.imgvers.split(".")[0])
        except Exception as ex:
            _msg = "Can not parse version from : {0} {1}, ex: {3} can not continue with migration".format(last_entry_img_hist, second_last_img_hist, ex)
            return ResultMigrReq(False, _msg)
        _msg= f'Last entry on image history: {last_entry_img_hist.imgvers} , evaluate : {num_last_img_hist}'
        _msg= _msg + f', Second last entry on image history: {second_last_img_hist.imgvers} , evaluate : {num_second_last_img_hist}'
        if num_last_img_hist >=  target_img_label and num_second_last_img_hist <= prev_img_label:
            return ResultMigrReq(True, _msg + ", Proceeding with migration")    
        return ResultMigrReq(False, _msg + ", Can not apply migration")  

    def run_pre_cps_os_upgrade(self, _remoteCpsHost, _target_version):
         # Generate manually log file for pre-migration, since is not in async context yet
        _id   = str(uuid.uuid1())
        _exapath = self.mGetConfig().mGetPath()
        _exapath = _exapath[0: _exapath.find("exabox")]
        log_tag = "pre-cps-oel8migr"
        _logFile = "{0}/log/threads/mgnt-{1}-{2}.log".format(_exapath, _id, log_tag)
        
        def mSyncLog(aFd, aSyncLogTag,  aMsg):
            msg = f'Sync - {aSyncLogTag} - {aMsg}'
            self.mGetLog().mInfo(msg)
            aFd.write("{0}\n".format(msg))
            aFd.flush()
            return

        with open(_logFile, "w+") as _log:
            try:
                with connect_to_host(_remoteCpsHost, get_gcontext(), username=self.mGetCpsUser()) as _cpsNode:
                    # Try to get version from remote cps
                    secs_to_wait=20
                    _cmd_version = f'/usr/bin/sudo -n /bin/timeout --signal=SIGKILL {secs_to_wait}s /usr/local/bin/imageinfo -ver'
                    _fin, _fout, _ferr = _cpsNode.mExecuteCmd(_cmd_version)
                    _sysOutRemote = _fout.readlines()
                    _sysErrorRemote = _ferr.readlines()
                    _rcRemote = _cpsNode.mGetCmdExitStatus()
                    if _rcRemote != 0 :
                        _errorMsg = "Error on: {0} host : return code: {1}, sysout: {2}, syserror: {3} ".format(\
                            _remoteCpsHost, _rcRemote, _sysOutRemote, _sysErrorRemote)
                        mSyncLog(_log, log_tag, _errorMsg)
                        return CpsEndpoint.FAILURE, _logFile
                    target_img_label = [23, 24]
                    prev_img_label = 22
                    _sysOutRemote_cps =  _sysOutRemote[0].strip() if _sysOutRemote else None
                    _cps_version = int(_sysOutRemote_cps.split(".")[0]) if _sysOutRemote_cps else None
                    _target_version  = int(_target_version.split(".")[0])
                    _info_msg = f'current image version on cps  {_remoteCpsHost} : {_sysOutRemote_cps}, target version: {_target_version}'
                    mSyncLog(_log, log_tag, _info_msg)
                    if _cps_version:
                        _info_msg = f'Running {log_tag} on host {_remoteCpsHost}'
                        mSyncLog(_log, log_tag, _info_msg)
                        # if target version == 24 and cps image on 22 or lower, proceed with pre-migration
                        if _target_version in target_img_label and _cps_version <= prev_img_label:
                            cmd_list = []
                            _cmd_check = "/usr/bin/sudo -n ls  /opt/oci/exacc/secureocps/iptables.pre_cps_os_upgrade"
                            _ = _cpsNode.mExecuteCmd(_cmd_check)
                            _rcRemote_ls = _cpsNode.mGetCmdExitStatus()
                            if _rcRemote_ls != 0 :
                                    cmd_list.append("/usr/bin/sudo -n /usr/bin/mkdir -p /opt/oci/exacc/secureocps")
                                    cmd_list.append("/usr/bin/sudo -n /usr/bin/chown ecra:dba /opt/oci/exacc/secureocps")
                                    cmd_list.append("/usr/bin/sudo -n /bin/timeout --signal=SIGKILL 20s /usr/sbin/iptables-save > /opt/oci/exacc/secureocps/iptables.pre_cps_os_upgrade")
                            cmd_list.append("/usr/bin/sudo -n /usr/bin/chmod 0755 /opt/oci/exacc/deployer/ocps-full/sh_scripts/oel8_migr/migrate_stbond.sh")
                            cmd_list.append("/usr/bin/sudo -n /bin/timeout --signal=SIGKILL 20s /opt/oci/exacc/deployer/ocps-full/sh_scripts/oel8_migr/migrate_stbond.sh")
                            for _cmd_it in cmd_list:
                                _info_msg = f'Running cmd: {_cmd_it} on host: {_remoteCpsHost}'
                                mSyncLog(_log, log_tag, _info_msg)
                                _fin, _fout, _ferr = _cpsNode.mExecuteCmd(_cmd_it)
                                _sysOutRemote = _fout.readlines()
                                _sysErrorRemote = _ferr.readlines()
                                _rcRemote = _cpsNode.mGetCmdExitStatus()
                                if _rcRemote != 0 :
                                    _errorMsg = f'Error running cmd: {_sysErrorRemote} on host: {_remoteCpsHost}, return code: {_rcRemote}, sysout: {_sysOutRemote}, syserror: {_sysErrorRemote} '
                                    mSyncLog(_log, log_tag, _errorMsg)
                                    return CpsEndpoint.FAILURE, _logFile
                                else:
                                    _info_msg = f'Result cmd: {_cmd_it} on host: {_remoteCpsHost}, return code: {_rcRemote}, sysout: {_sysOutRemote}'
                                    mSyncLog(_log, log_tag, _info_msg)
                        else:
                            _info_msg = f'skip {log_tag} on host {_remoteCpsHost}'
                            mSyncLog(_log, log_tag, _info_msg)

            except Exception:
                _error_msg = traceback.format_exc()
                _errorMsg = f' Exception running  {log_tag} {_error_msg}'
                mSyncLog(_log, log_tag, _error_msg)
                return CpsEndpoint.FAILURE,_logFile
        return CpsEndpoint.SUCCESS, _logFile
    
    def extract_image_history_from_cps(self, aRemoteCps): 
        _sysOutRemote = ""
        with connect_to_host(aRemoteCps, get_gcontext(), username=self.mGetCpsUser()) as _cpsNode:
            _cmd = "/usr/bin/sudo -n /bin/timeout --signal=SIGKILL 20s /usr/local/bin/imagehistory"
            _fin, _fout, _ferr = _cpsNode.mExecuteCmd(_cmd)
            _sysOutRemote = _fout.readlines()
            _sysErrorRemote = _ferr.readlines()
            _rcRemote = _cpsNode.mGetCmdExitStatus()
            if _rcRemote != 0 :
                _errorMsg = "Error running {0} on: {1} host : rc: {2}, sysout: {3}, syserror: {4} ".format(\
                    _cmd, aRemoteCps, _rcRemote, _sysOutRemote, _sysErrorRemote)
                return 1, _errorMsg
            return 0, _sysOutRemote
    
    
