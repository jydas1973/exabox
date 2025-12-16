#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/cluvmconsole_deploy.py /main/7 2024/11/16 04:13:17 araghave Exp $
#
# cluvmconsole_deploy.py
#
# Copyright (c) 2023, 2024, Oracle and/or its affiliates.
#
#    NAME
#      cluvmconsole_deploy.py
#
#    DESCRIPTION
#      Deployment actions for Exadata Cloud Services VM Serial Console feature.
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    araghave    11/08/24 - Bug 37260937 - EXACS:24.4.2.1:ADD COMPUTE FLOW
#                           FAILING WITH ATTRIBUTEERROR: 'STRICTVERSION' OBJECT
#                           HAS NO ATTRIBUTE 'VERSION'
#    joysjose    10/04/24 - Bug 37134606 Handle empty directory scenario
#    araghave    05/17/24 - Enh 36293209 - USE PLUGIN FILES FROM THE NEW
#                           EXADATA VERSION PLUGIN LOCATION
#    enrivera    11/10/23 - Bug 35895064 - Serial Console: Return correct values after running deployer actions
#    enrivera    05/04/23 - 35323310 - EXACC:SERIAL CONSOLE: INFRA PATCH WIPED OUT PREVIOUS CONFIGURATION
#                           AND DOES NOT INCLUDE RPM EXA-SERIAL-DEMUX.X86_64
#    pbellary    03/29/23 - 35094869: EXACC SERIAL CONSOLE ADD THE CALL TO EXACLOUD SERIAL CONSOLE INSTALL
#                                         COMMAND IN ELASTIC COMPUTE FLOW
#    enrivera    02/20/23 - Creation
#
import glob
import json
import os
from distutils.version import StrictVersion
from exabox.core.DBStore import ebGetDefaultDB
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn
from exabox.core.Error import ebError, ExacloudRuntimeError

class VMConsoleDeploy(object):
    DEST_DIR = "/opt/exacloud/vmconsole_deployer/"
    DEPLOYER_SCRIPT = os.path.join(DEST_DIR, "vm_serial_console_deployer.py")
    IMAGES_BUNDLE_DIR = "images/"
    EXACS_PLUGINS_BUNDLE_DIR = "exadataPrePostPlugins/dbnu_plugins/"
    EXACC_PLUGINS_BUNDLE_DIR = "/u01/downloads/exadata/exadataPrePostPlugins/dbnu_plugins/"
    VERSION_INFO_FILE = "version.info"
    PATCH_TGZ_FILENAME_REGEX = "vm_serial_console_patch.*[0-9].tgz"
    INSTALLER_BUNDLE_FILENAME = "vm_serial_console.tgz"

    def __init__(self, aCluCtrlObj, aOptions):
        self.__cluctrl = aCluCtrlObj
        self.__options = aOptions

    def mGetCluCtrlObj(self):
        return self.__cluctrl

    def mGetOptions(self):
        return self.__options

    def mGetDom0List(self):
        """
        VMConsoleDeploy actions are executed on all dom0s by default,
        to execute only on a specific dom0 'dom0' key has to exist in jsonconf parameter
        E.g.
            {
                "dom0": "<dom0 hostname/FQDN>"
            }
        """
        aDom0 = None
        _dom0s = self.mGetCluCtrlObj().mReadComputes()
        _options = self.mGetOptions()
        #If this parameter exists, then we only run in the selected dom0, otherwise in all of them
        if _options.jsonconf is not None and _options.jsonconf.get("dom0", None) is not None:
            ebLogInfo("'dom0' key in config json is present, verifying dom0 exists..")
            aDom0 = _options.jsonconf.get("dom0", None)
            if any(aDom0 in _dom0 for _dom0 in _dom0s):
                ebLogInfo(f"Action wil be executed only on Dom0 '{aDom0}'")
                _dom0s = [aDom0]
            else:
                raise ExacloudRuntimeError(0x0119, 0xA, "Selected dom0 in jsonconf does not exist.")
        return _dom0s

    def mGetExadataVersionPathIfAvailable(self):
        """
         This method returns the exadata plugin stage based on
         the files found under the new exadata version stage location.
         If the file was not found, common plugin stage location is
         returned.
        """
        _common_plugin_path = None
        _exadata_bundle_stage_path = None
        _exadata_bundle_validation_path = None
        _cluctrl = self.mGetCluCtrlObj()
        if _cluctrl.mIsOciEXACC():
            _common_plugin_path = self.EXACC_PLUGINS_BUNDLE_DIR
            _exadata_bundle_stage_path = os.path.join("/u01/downloads/exadata/", "PatchPayloads")
        else:
            _common_plugin_path = self.EXACS_PLUGINS_BUNDLE_DIR
            _exadata_bundle_stage_path = "PatchPayloads/"

        # By default, plugins should be available in the common plugin stage location.
        _final_plugin_path = _common_plugin_path
        if os.path.exists(_exadata_bundle_stage_path):
            '''
             PatchPayloads directory may contain other directories
             like DBPATCHFILE other than exadata bundle directories
             and version details must be checked only in case of a 
             directory name starting with 2 digits.

              -bash-4.4$ ls -tlr PatchPayloads/
              total 0
              drwxr-xr-x 8 araghave wheel 148 Oct 21 05:53 23.1.19.0.0.241015
              drwxr-xr-x 2 araghave wheel  32 Oct 21 15:51 DBPatchFile
              -bash-4.4$
            '''
            _sub_dirs = glob.glob(os.path.join(_exadata_bundle_stage_path, '[2-9][0-9].[0-9]*/'))
            if _sub_dirs:
                latest_exadata_version_specific_dir = max(_sub_dirs, key=os.path.getmtime)
                '''
                Check for existence for exadataPrePostplugins in the exadata
                version specific stage location.
                '''
                _exadata_bundle_validation_path = os.path.join(latest_exadata_version_specific_dir, "exadataPrePostPlugins/dbnu_plugins/")
                if os.path.exists(_exadata_bundle_validation_path) and len(os.listdir(_exadata_bundle_validation_path)) != 0:
                    ebLogInfo("Exadata plugins were found in the new exadata version specific stage location : %s." % _exadata_bundle_validation_path)
                    _final_plugin_path = _exadata_bundle_validation_path
                else:
                    ebLogInfo("Exadata plugins were not found in the new exadata version specific stage location. Fetching the same from the common plugin stage location : %s." % _common_plugin_path)
        return _final_plugin_path

    def mGetLatestInstallerAvailable(self):
        """
        """
        _vmconsole_bits = None
        _plugins_tgz_path = None
        _plugin_exadata_bundle_stage_path = None
        _cluctrl = self.mGetCluCtrlObj()
        _plugin_exadata_bundle_stage_path = self.mGetExadataVersionPathIfAvailable()
        if _plugin_exadata_bundle_stage_path:
            _plugins_tgz_path = os.path.join(_plugin_exadata_bundle_stage_path, self.INSTALLER_BUNDLE_FILENAME)

        if os.path.exists(_plugins_tgz_path):
            _cluctrl.mExecuteLocal("/bin/tar -xzf {} {}".format(_plugins_tgz_path, self.VERSION_INFO_FILE))
            _, _, _out, _ = _cluctrl.mExecuteLocal("/bin/cat " + self.VERSION_INFO_FILE)
            _plugin_ver = _out.strip()
            _cluctrl.mExecuteLocal("/bin/rm " + self.VERSION_INFO_FILE)
            ebLogInfo("Version found in plugins dir is " + _plugin_ver)
        else:
            ebLogWarn("'{}' does not exist.".format(_plugins_tgz_path))
            _plugin_ver = "0.1"

        _images_tgz_path = glob.glob(self.IMAGES_BUNDLE_DIR + self.PATCH_TGZ_FILENAME_REGEX)
        if _images_tgz_path:
            _images_tgz_path = _images_tgz_path.pop()
            _images_tgz_filename = os.path.basename(_images_tgz_path)
            _images_ver = ".".join(_images_tgz_filename.split(".")[1:4])
            ebLogInfo("Version found in exacloud/images dir is " + _images_ver)
        else:
            ebLogWarn("Could not find suitable bundle in " + self.IMAGES_BUNDLE_DIR)
            _images_ver = "0.1"

        if _images_ver == "0.1" and _plugin_ver == "0.1":
            raise ExacloudRuntimeError(0x2FF, 0xA, "Could not find suitable bundle for VM Serial Console")
        if StrictVersion(_images_ver) > StrictVersion(_plugin_ver):
            ebLogInfo("'{}' has a higher version".format(_images_tgz_path))
            _vmconsole_bits = _images_tgz_path
        else:
            ebLogInfo("'{}' has a higher version".format(_plugins_tgz_path))
            _vmconsole_bits = _plugins_tgz_path

        if _vmconsole_bits is None or not os.path.exists(_vmconsole_bits):
            raise ExacloudRuntimeError(0x2FF, 0xA, "Could not find suitable bundle for VM Serial Console")
        return _vmconsole_bits

    def mDeployerExists(self, aDom0):
        _node = exaBoxNode(get_gcontext())
        try:
            _node.mConnect(aHost=aDom0)
            _node.mExecuteCmd("/bin/ls " + self.DEPLOYER_SCRIPT)
            _rt = _node.mGetCmdExitStatus()
        except Exception as e:
            raise ExacloudRuntimeError(0x2c5, 0xA, "Exception caught while verifying if vmconsole installer exists")
        finally:
            _node.mDisconnect()
        return _rt == 0

    def mCopyInstaller(self, aDom0, aInstallerBundle):
        _res = 0
        _remote_bits = os.path.join(self.DEST_DIR, os.path.basename(aInstallerBundle))
        _remote_installer_bundle = os.path.join(self.DEST_DIR, self.INSTALLER_BUNDLE_FILENAME)

        _node = exaBoxNode(get_gcontext())
        try:
            _node.mConnect(aHost=aDom0)
            _node.mExecuteCmd("/bin/rm -rf " + self.DEST_DIR)
            _node.mExecuteCmd("/bin/mkdir -p " + self.DEST_DIR)
            _node.mCopyFile(aInstallerBundle, _remote_bits)
            _node.mExecuteCmd("/bin/tar -xzf {} -C {}".format(_remote_bits, self.DEST_DIR))
            _, _, _err = _node.mExecuteCmd("/bin/tar -xzf {} -C {}".format(_remote_installer_bundle, self.DEST_DIR))
            _rt = _node.mGetCmdExitStatus()
            if _rt != 0:
                ebLogInfo("Failed to extract new VM serial console package on dom0" + aDom0)
                ebLogError(_err.read())
                _res = 1
            #cleanup tgz files
            _node.mExecuteCmd(f"/bin/rm -f {_remote_bits} {_remote_installer_bundle}")
            #This file will be detected by main installer script
            if self.mGetCluCtrlObj().mIsOciEXACC():
                _node.mExecuteCmd("/bin/touch " + os.path.join(self.DEST_DIR, "images/is_exacc"))
        except Exception as e:
            _msg = "Exception caught while copying new bits to {} :\n{}"
            ebLogError(_msg.format(aDom0, str(e)))
            _res = 1
        finally:
            _node.mDisconnect()
        return _res

    def mRunDeployerScript(self, aDom0, aAction):
        _node = exaBoxNode(get_gcontext())
        try:
            _node.mConnect(aHost=aDom0)
            _cmd = f"/bin/python3 {self.DEPLOYER_SCRIPT} {aAction}"
            _, _out, _err = _node.mExecuteCmd(_cmd)
            _rc = _node.mGetCmdExitStatus()
            _out = _out.read()
            _err = _err.read()
            ebLogInfo(_out)
            ebLogInfo(_err)
        except Exception as e:
            ebLogError("Exception caught while executing action {} on {} :\n{}"\
                       .format(aAction, aDom0, str(e)))
            _rc = 1
        finally:
            _node.mDisconnect()
        return _rc

    def mSetEcraResponse(self, **kwargs):
        _reqobj = self.mGetCluCtrlObj().mGetRequestObj()
        if _reqobj is not None:
            if "aStatusInfo" in kwargs and kwargs["aStatusInfo"]:
                _reqobj.mSetStatusInfo(kwargs["aStatusInfo"])

            if "aErrorStr" in kwargs and kwargs["aErrorStr"]:
                _reqobj.mSetErrorStr(kwargs["aErrorStr"])

            if "aData" in kwargs and json.dumps(kwargs["aData"]):
                _reqobj.mSetData(json.dumps(kwargs["aData"]))
            _db = ebGetDefaultDB()
            _db.mUpdateRequest(_reqobj)
        else:
            ebLogWarn("Could not find request object. Ignore if this was executed directly from exacloud.")

###### Deployer actions ######

    def mInstall(self, aDom0List=None):
        _res = 0
        _errors = _statuses = list()

        if aDom0List is not None:
            _dom0s = aDom0List
        else:
            _dom0s = self.mGetDom0List()

        _vmconsole_bits = self.mGetLatestInstallerAvailable()
        for _dom0 in _dom0s:
            _error_str = "vmconsole install action FAILED on node " + _dom0
            _success_str = "vmconsole install action was SUCCESSFUL on node " + _dom0
            _rc = self.mCopyInstaller(_dom0, _vmconsole_bits)
            _rc = self.mRunDeployerScript(_dom0, 'install')
            if _rc != 0:
                ebLogError(_error_str)
                _errors.append(_error_str)
                _res = 1
                continue
            else:
                _local_status_json = "/tmp/vmconsole_status.json"
                _status_json = None
                _get_status = self.mGetStatus(aDom0List=[_dom0], aNoCopy=True, aOutputFile=_local_status_json)
                if os.path.exists(_local_status_json):
                    with open(_local_status_json) as _file:
                        _status_json = json.load(_file)
                        _status_json = _status_json[_dom0]
                ebLogInfo(str(_status_json))
                if _get_status != 0 or _status_json == None \
                  or _status_json["serial_demux_rpm"]["status"] != 0 \
                  or _status_json["exa-hippo-serialmux_image"]["status"] != 0 \
                  or _status_json["exa-hippo-sshd_image"]["status"] != 0 \
                  or _status_json["exa-hippo-serialmux_containers_overall"] != 0 \
                  or _status_json["exa-hippo-sshd_containers_overall"] != 0:
                    ebLogError(_error_str)
                    _errors.append(_error_str)
                    _res = 1
                    continue
                ebLogInfo(_success_str)
                _statuses.append(_success_str)

        self.mSetEcraResponse(aStatusInfo=",".join(_statuses), aErrorStr=",".join(_errors))
        return _res

    def mUninstall(self, aDom0List=None):
        _res = 0
        _errors = _statuses = list()
        if aDom0List is not None:
            _dom0s = aDom0List
        else:
            _dom0s = self.mGetDom0List()

        _vmconsole_bits = self.mGetLatestInstallerAvailable()

        for _dom0 in _dom0s:
            self.mCopyInstaller(_dom0, _vmconsole_bits)
            _error_str = "vmconsole uninstall action FAILED on node " + _dom0
            _success_str = "vmconsole uninstall action was SUCCESSFUL on node " + _dom0
            _rc = self.mRunDeployerScript(_dom0, 'uninstall')
            if _rc != 0:
                ebLogError(_error_str)
                _errors.append(_error_str)
                _res = 1
                continue
            else:
                _local_status_json = "/tmp/vmconsole_status.json"
                _status_json = None
                _get_status = self.mGetStatus(aDom0List=[_dom0], aNoCopy=True, aOutputFile=_local_status_json)
                if os.path.exists(_local_status_json):
                    with open(_local_status_json) as _file:
                        _status_json = json.load(_file)
                        _status_json = _status_json[_dom0]

                if _get_status != 0 or _status_json == None \
                  or _status_json["serial_demux_rpm"]["status"] == 0 \
                  or _status_json["exa-hippo-serialmux_image"]["status"] == 0 \
                  or _status_json["exa-hippo-sshd_image"]["status"] == 0 \
                  or _status_json["exa-hippo-serialmux_containers_overall"] == 0 \
                  or _status_json["exa-hippo-sshd_containers_overall"] == 0:
                    ebLogError(_error_str)
                    _errors.append(_error_str)
                    _res = 1
                    continue

                ebLogInfo(_success_str)
                _statuses.append(_success_str)


        self.mSetEcraResponse(aStatusInfo=",".join(_statuses), aErrorStr=",".join(_errors))
        return _res

    def mGetStatus(self, aNoCopy=False, aOutputFile=None, aDom0List=None):
        _res = 0
        _dom0_statuses = dict()
        if aDom0List is not None:
            _dom0s = aDom0List
        else:
            _dom0s = self.mGetDom0List()

        if not aNoCopy:
            _vmconsole_bits = self.mGetLatestInstallerAvailable()
        for _dom0 in _dom0s:
            if not aNoCopy:
                self.mCopyInstaller(_dom0, _vmconsole_bits)
            if not self.mDeployerExists(_dom0):
                _msg = f"Deployer script does not exist in {_dom0} and nocopy "\
                        "flag was set, skipping execution on this dom0..."
                ebLogWarn(_msg)
                _res = 1
                continue
            _rc = self.mRunDeployerScript(_dom0, "get_status")
            if _rc != 0:
                _msg = "Errors caught while running installer script"
                ebLogError(_msg)
                _dom0_statuses[_dom0] = _msg
                _res = 1
                continue
            #get status json from file
            _node = exaBoxNode(get_gcontext())
            try:
                _node.mConnect(aHost=_dom0)
                _, _out, _err = _node.mExecuteCmd("/bin/cat /tmp/vmconsole-dpy_status.json")
                _out = _out.read()
                _err = _err.read()
                if _rc != 0 or not _out:
                    _msg = f"Could not retrieve status json file from {_dom0}:\n{_err}"
                    ebLogError(_msg)
                    _dom0_statuses[_dom0] = _msg
                    _res = 1
            except Exception as e:
                _msg = "Exception caught while retrieving status json file from {} :\n{}"\
                       .format(_dom0, str(e))
                _dom0_statuses[_dom0] = _msg
                ebLogError(_msg)
                _res = 1
            finally:
                _node.mDisconnect()
            _dom0_statuses[_dom0] = json.loads(_out)

        self.mSetEcraResponse(aData=json.dumps(_dom0_statuses))

        if aOutputFile:
            with open(aOutputFile, 'w') as _file:
                json.dump(_dom0_statuses, _file, indent=4)

        return _res
