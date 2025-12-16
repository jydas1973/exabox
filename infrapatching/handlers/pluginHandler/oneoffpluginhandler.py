#
# $Header: ecs/exacloud/exabox/infrapatching/handlers/pluginHandler/oneoffpluginhandler.py /main/15 2025/03/25 10:03:33 araghave Exp $
#
# oneoffpluginhandler.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
#
#    NAME
#      oneoffpluginhandler.py - This module contains methods to run oneoff plugin on all targets.
#
#    DESCRIPTION
#      This module contains methods to run oneoff plugin on all targets(Dom0, DomU, Cells, Switches).
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    araghave    03/13/25 - ER 37701317 - ONEOFF PATCH SHOULD GENERATE UNIQUE
#                           LOG FILE
#    araghave    03/04/25 - Bug 37417431 - EXACS | DOMU | UNWANTED SSH
#                           CONNECTION FROM 169.254.200.1 LOCKING OPC USER
#    avimonda    11/14/24 - Bug 37201334 - AIM4ECS:0X030D0000 - ONE OFF PATCH
#                           APPLY FAILED.
#    araghave    11/06/24 - Bug 37247140 - ALLOW DOMU ONEOFF PATCH TO COPY AND
#                           EXECUTE PLUGINS BASED ON AVAILABLE KEYS
#    araghave    08/27/24 - Enh 36829406 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE CORE, PLUGIN AND TASKHANDLER
#                           FILES
#    araghave    06/13/24 - Enh 36522596 - REVIEW PRE-CHECK/PATCHING/ROLLBACK
#                           LOGS AND CLEAN-UP
#    araghave    04/11/22 - Enh 34048154 - ONEOFF PATCH OPERATION TO SUPPORT A
#                           PLUGIN FRAMEWORK WITH GENERIC OPTIONS
#    araghave    12/08/21 - Enh 33598784 - MOVE ALL INFRA PATCHING ERROR CODES
#                           FROM ERROR.PY TO INFRAPATCHERROR.PY
#    araghave    07/08/21 - BUG 33081173 - Remove older error codes from Infra
#                           patching core files
#    araghave    12/03/20 - Enh 31604386 - RETURN ERROR CODES TO DBCP TO CELLS
#                           AND SWITCHES
#    nmallego    08/28/20 - Refactor infra patching code
#    nmallego    08/28/20 - Creation
#

import os, sys
import traceback
import time
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.infrapatching.handlers.pluginHandler.pluginhandler import PluginHandler
from exabox.infrapatching.utils.utility import mRegisterInfraPatchingHandlers, mGetInfraPatchingConfigParam
from exabox.infrapatching.utils.constants import *
from exabox.infrapatching.core.infrapatcherror import *

sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))

class OneOffPluginHandler(PluginHandler):

    def __init__(self, *initial_data, **kwargs):
        super(OneOffPluginHandler, self).__init__(*initial_data, **kwargs)
        mRegisterInfraPatchingHandlers(INFRA_PATCHING_HANDLERS, [TASK_ONEOFF], self)
        self.mPatchLogInfo("OneOffPluginHandler")

    def mGetOneoffPatchLogRetentioninDays(self):
        return int(mGetInfraPatchingConfigParam('oneoff_log_retention_in_days'))

    def mGetOneoffOperationLogsRetentionSettings(self):
        _retain_oneoff_logs_post_oneoff_operation = mGetInfraPatchingConfigParam('oneoff_retain_logs_post_execution')
        if _retain_oneoff_logs_post_oneoff_operation.lower() in ['false']:
            return False
        else:
            return True

    def mApply(self):
        ret = PATCH_SUCCESS_EXIT_CODE
        self.mPatchLogInfo("Executing One-off patch operation...\n")
        _plugin_remote_dir = "/opt/exacloud/customs/plugins/oneoff_patches/"
        _plugin_remote_log_dir = "/opt/exacloud/customs/plugins/oneoff_logs/"
        _script_file = "oneoff_patch.sh"

        '''
         Example of a _plugin_local_staged_file below. It will
         contain the absolute path of the plugin script.

         _plugin_local_staged_file = "/tmp/devoneoffplugin/devoneoffplugin.sh"
        '''
        _plugin_local_staged_file = self.mGetOneoffPluginFileLocation()
        if _plugin_local_staged_file is None:
            _plugin_local_staged_file = "exadataPrePostPlugins/oneoff_patch/oneoff_patch.sh"
        _plugin_log = "/opt/exacloud/customs/plugins/oneoff_patches/oneoff_console.log"

        if _plugin_local_staged_file is not None:
            _script_file = os.path.basename(_plugin_local_staged_file)

        _node_list = self.mGetNodeList()
        '''
         Below code snippet validates for existence of oneoff patch
         directories locally on the exacloud as well as the
         target nodes.
        '''

        # Location of oneoff plugins (on exacloud and on target node)
        try:
            if not os.path.exists(_plugin_local_staged_file):
                self.mPatchLogError(
                    f"Parent plugins for '{self.mGetPluginTarget()}' are not found on '{_plugin_local_staged_file}'")
                _suggestion_msg = f"Parent plugins for '{self.mGetPluginTarget()}' are not found on '{_plugin_local_staged_file}'"
                ret = PARENT_PLUGINS_MISSING
                self.mAddError(ret, _suggestion_msg)
                return ret

            if os.path.isdir(_plugin_local_staged_file):
                _suggestion_msg = f"Input script file passed is a directory, a script in the format : {'/tmp/devoneoffplugins/devoneoffplugin.sh'} need to be passed as input. Current input : {_plugin_local_staged_file}"
                ret = PARENT_PLUGINS_MISSING
                self.mAddError(ret, _suggestion_msg)
                return ret

        except Exception as e:
            _suggestion_msg = f"Exception in Validating the presence of One off patches: {str(e)}"
            ret = ONEOFF_APPLY_FAILED
            if self.mGetPluginTarget() == PATCH_DOMU:
                ret = ONEOFF_DOMU_APPLY_FAILED
            self.mPatchLogTrace(traceback.format_exc())
            self.mAddError(ret, _suggestion_msg)
            return ret

        _patch_file = os.path.join(_plugin_remote_dir, _script_file)

        # Step 1. Copy One-off patches.
        ret = self.mCopyOneOffPatch(_plugin_remote_dir, _plugin_remote_log_dir, _plugin_local_staged_file, _node_list)
        if ret != PATCH_SUCCESS_EXIT_CODE:
            self.mCleanupOneoffPluginScript(_node_list, _patch_file, _plugin_remote_dir, _plugin_remote_log_dir, _plugin_log)
            return ret

        # Step 2. Run one off patch operation.

        ret = self.mExecuteOneOffPatch(_node_list, _patch_file, _plugin_remote_dir, _plugin_remote_log_dir, _plugin_log)
        self.mCleanupOneoffPluginScript(_node_list, _patch_file, _plugin_remote_dir, _plugin_remote_log_dir, _plugin_log)
        return ret

    def mCopyOneOffPatch(self, aPluginRemoteDir, aPluginRemoteLogDir, aPluginLocalStagedFile, aNodeList):
        """
         This method cpoies the one off scripts from local plugin staged to
         remote plug in directory.

          -> return PATCH_SUCCESS_EXIT_CODE if successful.
          -> return ONEOFF_PATCH_COPY_FAILED error code other than PATCH_SUCCESS_EXIT_CODE if failure.
        """

        ret = PATCH_SUCCESS_EXIT_CODE
        _rc = True
        _plugin_local_staged_location = os.path.dirname(os.path.realpath(aPluginLocalStagedFile))
        for _node_name in aNodeList:

            try:
                _node = exaBoxNode(get_gcontext())
                if self.mGetPluginTarget() == PATCH_DOMU and self.mGetADBS().upper() == "TRUE":
                    _node.mSetUser('opc')
                    _node.mSetMaxRetries(self.mGetMaxNumberofSshRetries())

                if not _node.mIsConnectable(aHost=_node_name, aKeyOnly=True):
                    _suggestion_msg = f"Unable to connect to {_node_name} either using root or opc keys. Oneoff patch operation failed."
                    ret = ONEOFF_APPLY_FAILED
                    if self.mGetPluginTarget() == PATCH_DOMU:
                        ret = ONEOFF_DOMU_APPLY_FAILED
                    self.mAddError(ret, _suggestion_msg)
                    return ret

                _node.mConnect(aHost=_node_name)

                # Create remote plugin stage directory before copying patches.
                _node.mExecuteCmdLog(f'mkdir -p {aPluginRemoteDir}')
                _node.mExecuteCmdLog(f'mkdir -p {aPluginRemoteLogDir}')

                for _entry_file in os.listdir(_plugin_local_staged_location):
                    self.mPatchLogDebug(
                        f"Target Node: {_node_name}, Copy plugins: Source = {aPluginLocalStagedFile}, Destination file = {os.path.join(aPluginRemoteDir, _entry_file)}")
                    if os.path.isdir(os.path.join(_plugin_local_staged_location, _entry_file)):
                        self.mPatchLogInfo(
                            f"The '{os.path.join(_plugin_local_staged_location, _entry_file)}' is a directory, we skip to copy directory.")
                        continue
                    else:
                        self.mPatchLogInfo(
                            f"Copying {os.path.join(_plugin_local_staged_location, _entry_file)} from exacloud plugin location to target node : {_node_name} Location : {os.path.join(aPluginRemoteDir, _entry_file)}")
                        if os.path.exists(os.path.join(_plugin_local_staged_location, _entry_file)):
                            _rc = _node.mCopyFile(os.path.join(_plugin_local_staged_location, _entry_file),
                                            os.path.join(aPluginRemoteDir, _entry_file))

                            '''
                             Currently mCopyFile returns None in case of successful copy and not True
                             and hence None is considered for validation.

                             2024-11-06 08:39:20,159 - dfltlog - INFO - 14732 - Copy with No retry. Exit
                             code: None
                             2024-11-06 08:39:20,173 - dfltlog - INFO - 14732 - OneOffPluginHandler - Copying
                             /scratch/sdevasek/ecra_installs/automate/mw_home/user_projects/domains/exacloud/exadataPrePostPlugins/oneoff_patch/oneoff_postbonding.sh
                             from exacloud plugin location to target node : scaqag01adm05.us.oracle.com
                             Location : /opt/exacloud/customs/plugins/oneoff_patches/oneoff_postbonding.sh
                             2024-11-06 08:39:20,849 - dfltlog - INFO - 14732 - Copy with No retry. Exit
                             code: None
                            '''
                            if _rc is not None:
                                ret = ONEOFF_PATCH_COPY_FAILED
                                if self.mGetPluginTarget() == PATCH_DOMU:
                                    ret = ONEOFF_DOMU_PATCH_COPY_FAILED
                                _suggestion_msg = f"Unable to copy {os.path.join(_plugin_local_staged_location, _entry_file)} from exacloud plugin location to target node : {_node_name} Location : {os.path.join(aPluginRemoteDir, _entry_file)}"
                                self.mAddError(ret, _suggestion_msg)
                                return ret

            except Exception as e:
                _suggestion_msg = f"Exception: Error in Copying One off patches to target node: {_node_name} Error : {str(e)}"
                self.mPatchLogTrace(traceback.format_exc())
                ret = ONEOFF_PATCH_COPY_FAILED
                if self.mGetPluginTarget() == PATCH_DOMU:
                    ret = ONEOFF_DOMU_PATCH_COPY_FAILED
                self.mAddError(ret, _suggestion_msg)
                return ret
            finally:
                if _node.mIsConnected():
                    _node.mDisconnect()

        return ret


    def mCleanupOneoffPluginScript(self, aNodeList, aPatchFile, aPluginRemoteDir, aPluginRemoteLogDir, aPluginLog):
        '''
         Clean up scripts and config files on the
         Target nodes.
        '''
        ret = PATCH_SUCCESS_EXIT_CODE
        _oneoff_log_name_convention = 'oneoff_console.log.' + (time.strftime("%m_%d_%y_%H_%M", time.localtime()))

        # Step 3. Clean-up
        for _node_name in aNodeList:

            try:
                _node = exaBoxNode(get_gcontext())

                if self.mGetPluginTarget() == PATCH_DOMU and self.mGetADBS().upper() == "TRUE":
                    _node.mSetUser('opc')
                    _node.mSetMaxRetries(self.mGetMaxNumberofSshRetries())

                if not _node.mIsConnectable(aHost=_node_name, aKeyOnly=True):
                    _suggestion_msg = f"Unable to connect to {_node_name} either using root or opc keys. Oneoff patch operation failed."
                    ret = ONEOFF_APPLY_FAILED
                    if self.mGetPluginTarget() == PATCH_DOMU:
                        ret = ONEOFF_DOMU_APPLY_FAILED
                    self.mAddError(ret, _suggestion_msg)
                    continue

                _node.mConnect(aHost=_node_name)

                # 3 a. Copy all the relevant log to local.
                if _node.mFileExists(aPluginLog):
                    self.mPatchLogInfo(
                        f"Copying the logs from Node : {_node_name}, Location : {aPluginLog} to Local Directory : {self.mGetLogPath()} ")
                    _node.mExecuteCmdLog("cp -rp %s %s/%s" % (aPluginLog, aPluginRemoteLogDir, _oneoff_log_name_convention))
                    _node.mCopy2Local(aPluginLog, self.mGetLogPath() + '/' + TASK_ONEOFF + '.' + _node_name + '.' + 'log')

                    # Purge oneoff logs if the purge parameter is enabled and retention is specified in infrapatching.conf.
                    if not self.mGetOneoffOperationLogsRetentionSettings() and _node.mFileExists(aPluginRemoteLogDir):
                        self.mPatchLogInfo(f"One plugin logs older than {self.mGetOneoffPatchLogRetentioninDays()} days will be purged.")
                        _cmd_del_oneoff_logs = f"find {aPluginRemoteLogDir} -type f -mtime +{self.mGetOneoffPatchLogRetentioninDays()} -delete -print"
                        _i, _o, _e = _node.mExecuteCmd(_cmd_del_oneoff_logs)
                        if int(_node.mGetCmdExitStatus()) == 0:
                            _out = _o.readlines()
                            if _out:
                                self.mPatchLogInfo(f"Folowing oneoff plugin logs were cleaned up based on the retention settings - \n {_out}")

                # 3 b. Delete One-off patches.
                # if os.path.isdir(_plugin_remote_dir):
                if _node.mFileExists(aPatchFile):
                    self.mPatchLogInfo(
                        f"Deleting plugin directory = {aPluginRemoteDir} from target node : {_node_name}")
                    _node.mExecuteCmdLog(f" rm -rf {aPluginRemoteDir}")
                if _node.mIsConnected():
                    _node.mDisconnect()
            except Exception as e:
                self.mPatchLogError(f"Exception: Error in deleting One off patch directories on target nodes: {str(e)}")
                _suggestion_msg = f"Exception: Error in deleting One off patch directories on Node : {_node_name}"
                self.mPatchLogTrace(traceback.format_exc())
                ret = ONEOFF_PATCH_CLEANUP_FAILED
                if self.mGetPluginTarget() == PATCH_DOMU:
                    ret = ONEOFF_PATCH_CLEANUP_DOMU_FAILED
                self.mAddError(ret, _suggestion_msg)

        return ret

    def mExecuteOneOffPatch(self, aNodeList, aPatchFile, aPluginRemoteDir, aLogDir, aLogFile):
        """
         This method executes the one off scripts and options specified
         by user. Currently a one off script is checked in and
         will always return success. User can customise this file
         as per their requirement.

          -> return PATCH_SUCCESS_EXIT_CODE if successful.
          -> return any other error code other than PATCH_SUCCESS_EXIT_CODE if failure.
        """

        ret = PATCH_SUCCESS_EXIT_CODE
        _connected_as_non_root_user = False
        _sudo_str = ''

        _oneoff_args = self.mGetOneOffPluginArguments()
        for aNode in aNodeList:
            _node = exaBoxNode(get_gcontext())

            # Try to connect as opc user to domu. If not exist, then try with root user
            if self.mGetPluginTarget() == PATCH_DOMU and self.mGetADBS().upper() == "TRUE":
                _node.mSetUser('opc')
                _node.mSetMaxRetries(self.mGetMaxNumberofSshRetries())

                _connected_as_non_root_user = True
                self.mPatchLogInfo(f"One-off Patch run: Connecting as opc user to '{self.mGetPluginTarget()}' to run plugins.")
            else:
                self.mPatchLogInfo(f"One-off Patch run: Connecting as root user to '{self.mGetPluginTarget()}' to run plugins.")

            if not _node.mIsConnectable(aHost=aNode, aKeyOnly=True):
                _suggestion_msg = f"Unable to connect to {aNode} either using root or opc keys. Oneoff patch operation failed."
                ret = ONEOFF_APPLY_FAILED
                if self.mGetPluginTarget() == PATCH_DOMU:
                    ret = ONEOFF_DOMU_APPLY_FAILED
                self.mAddError(ret, _suggestion_msg)
                return ret

            if _connected_as_non_root_user:
                _sudo_str = 'sudo '
                # sudo chown -R opc:opc /opt/exacloud/customs/plugins/oneoff_patches; else will have permission denied problem
                _cmd_oneoff_run = f" chown -R opc:opc {aPluginRemoteDir} {aLogDir}; {_sudo_str}chmod +x {aPatchFile}; {_sudo_str}{aPatchFile} {_oneoff_args} > {aLogFile} "
            else:
                _cmd_oneoff_run = f"chmod +x {aPatchFile};{aPatchFile} {_oneoff_args} > {aLogFile} "  #for Dom0, cells and Switches

            self.mPatchLogInfo(f"One off command is : {_cmd_oneoff_run}")

            _node.mConnect(aHost=aNode)
            if not _node.mFileExists(aPatchFile):
                if _node.mIsConnected():
                    _node.mDisconnect()
                _suggestion_msg = f"Unable to find one off patch file : {aPatchFile}"
                ret = ONEOFF_PATCHES_MISSING
                if self.mGetPluginTarget() == PATCH_DOMU:
                    ret = ONEOFF_DOMU_PATCHES_MISSING
                self.mAddError(ret, _suggestion_msg)
                return ret

            _i, _o, _e = _node.mExecuteCmd(_cmd_oneoff_run)
            _out = _o.readlines()
            for _output in _out:
                self.mPatchLogInfo(f"{_output.strip()}")
            _rc = _node.mGetCmdExitStatus()
            self.mPatchLogInfo(f"One Off Patch Exit Command Status {_rc} ")
            if int(_rc) == 0:
                self.mPatchLogInfo(f"\nOne-off Patch apply completed successfully on {aNode}.\n")
            else:
                _suggestion_msg = f"Running one-off patch failed on node = {aNode}"
                ret = ONEOFF_APPLY_FAILED
                if self.mGetPluginTarget() == PATCH_DOMU:
                    ret = ONEOFF_DOMU_APPLY_FAILED
                self.mAddError(ret, _suggestion_msg)
            if _node.mIsConnected():
                _node.mDisconnect()

        return ret
