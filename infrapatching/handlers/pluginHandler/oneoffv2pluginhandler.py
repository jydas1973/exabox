#!/bin/python
#
# $Header: ecs/exacloud/exabox/infrapatching/handlers/pluginHandler/oneoffv2pluginhandler.py /main/11 2025/10/22 08:33:53 sdevasek Exp $
#
# oneoffv2pluginhandler.py
#
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
#
#    NAME
#      oneoffv2pluginhandler.py - This module contains methods to run oneoff v2 plugin on all targets.
#                                 based on the infra plugin ecra metadata details.
#
#    DESCRIPTION
#      This module contains methods to run oneoff plugin on all targets(Dom0, DomU, Cells).
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    sdevasek    10/10/25 - ENH 38437135 - IMPLEMENT ADDITION OF SCRIPTNAME
#                           SCRIPTBUNLDENAME AND SCRIPTBUNDLEHASH ATTRIBUTES
#                           TO ECRA REGISTERED PLUGINS METADATA REGISTRATION
#    araghave    03/04/25 - Enh 37541740 - UPDATE ALL MISCONNECTABLE API INFRA
#                           PATCHING REFERENCES TO TAKE AKEY AS TRUE
#    araghave    03/04/25 - Bug 37417431 - EXACS | DOMU | UNWANTED SSH
#                           CONNECTION FROM 169.254.200.1 LOCKING OPC USER
#    diguma      12/06/24 - bug 37365122 - EXACS:24.4.2.1:X11M: ROLLING DOM0
#                           PATCHING FAILS WITH SSH CONNECTIVITY CHECK FAILED
#                           DURING PATCHING EVEN THOUGH EXASSH TO DOMUS WORK
#    araghave    10/08/24 - Enh 36505637 - IMPROVE POLLING MECHANISM IN CASE
#                           OF INFRA PATCHING OPERATIONS
#    araghave    08/27/24 - Enh 36829406 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE CORE, PLUGIN AND TASKHANDLER
#                           FILES
#    araghave    07/15/24 - Enh 36830077 - CLEANUP KSPLICE CODE FROM
#                           INFRAPATCHING FILES
#    araghave    06/13/24 - Enh 36522596 - REVIEW PRE-CHECK/PATCHING/ROLLBACK
#                           LOGS AND CLEAN-UP
#    araghave    03/13/24 - Enh 36270822 - EXECUTION OF EXACLOUD PLUGINS USING
#                           INFRA PATCHING PLUGIN METADATA
#    araghave    02/28/24 - Enh 36295801 - IMPLEMENT ONEOFFV2 PLUGIN EXACLOUD
#                           CHANGES
#    araghave    02/14/24 - Creation
#
from time import sleep
from exabox.infrapatching.handlers.pluginHandler.pluginhandler import PluginHandler
from exabox.infrapatching.utils.utility import *
from exabox.infrapatching.core.infrapatcherror import *
from exabox.infrapatching.utils.constants import *
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure
from exabox.infrapatching.utils.utility import mGetInfraPatchingConfigParam

sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))

class OneOffV2PluginHandler(PluginHandler):

    def __init__(self, *initial_data, **kwargs):
        super(OneOffV2PluginHandler, self).__init__(*initial_data, **kwargs)
        mRegisterInfraPatchingHandlers(INFRA_PATCHING_HANDLERS, [TASK_ONEOFFV2], self)
        self.mPatchLogInfo("OneOffV2PluginHandler")

    def mOffV2NodeList(self):
        """
         This method provides the list of
         nodes where oneoff V2 plugins are
         required to be executed based on the
         target type details.
        """
        _node_list = []
        if str(PATCH_DOM0).lower() in str(self.mGetTargetTypes()[0]).lower():
            _node_list = self.mGetCustomizedDom0List()
        elif str(PATCH_DOMU).lower() in str(self.mGetTargetTypes()[0]).lower():
            _node_list = self.mGetCustomizedDomUList()
        elif str(PATCH_CELL).lower() in str(self.mGetTargetTypes()[0]).lower():
            _node_list = self.mGetCustomizedCellList()
        return _node_list

    def mApply(self):
        _ret = PATCH_SUCCESS_EXIT_CODE
        self.mPatchLogInfo(f"Executing One-off patch operation in {self.mGetOpStyle()} style")

        # By default oneoff plugins are executed in rolling manner.
        if self.mGetOpStyle() in OP_STYLE_ROLLING:
            _ret = self.mRunOneOffV2inRolling()
        elif self.mGetOpStyle() in OP_STYLE_NON_ROLLING:
            _ret = self.mRunOneOffV2inNonRolling()
        return _ret

    def mRunOneOffV2inRolling(self):
        """
        This method executed oneoff plugins
        in rolling manner.
        :return: PATCH_SUCCESS_EXIT_CODE in case of successful patch execution
                or FailOnError flag was set to false
            else
                return error code as per error details returned
                from below execution flow.
        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        _rc = PATCH_SUCCESS_EXIT_CODE
        _script_alias = None
        _plugin_target = None
        _fail_on_error = None

        if len(self.mOffV2NodeList()) == 0:
            self.mPatchLogWarn("Input node list is empty. No plugins were executed.")
            return _ret

        _node_list = self.mOffV2NodeList()
        # Step 1. Copy One-off patches.
        for _node_name in _node_list:
            for _oneoff_plugin_data in self.mGetPluginMetadata():
                _script_alias = mGetScriptAlias(_oneoff_plugin_data)
                _plugin_target = mGetPluginTargetV2(_oneoff_plugin_data)
                _fail_on_error = mGetFailonError(_oneoff_plugin_data)
                
                self.mPatchLogInfo(
                    f"Current oneoff plugin scripts will be run with the following input : {json.dumps(_oneoff_plugin_data, indent=4)}")
                # Validte only for the list of scripts passed as part of ScriptAliasList
                if self.mGetScriptAliasListToBeExecuted() and len(self.mGetScriptAliasListToBeExecuted()) > 0:
                    if mGetScriptAlias(_oneoff_plugin_data) in  [_script_alias_name.lower() for _script_alias_name in self.mGetScriptAliasListToBeExecuted()]:
                        self.mPatchLogInfo(
                            f"{str(_script_alias)} found in the Script Alias List : {str(self.mGetScriptAliasListToBeExecuted())} and current oneoff plugin will be run.")
                    else:
                        self.mPatchLogWarn(
                            f"{str(_script_alias)} not found in the Script Alias List : {str(self.mGetScriptAliasListToBeExecuted())} and current oneoff plugin will not be run.")
                        continue
                else:
                    self.mPatchLogInfo("ScriptAliasList passed is empty and no oneoff plugin scripts will be run")
                    continue

                # Currently reboot option supported only on cells.
                # Currently no reboot option is provided for any of the targets.
                if (_plugin_target).lower() in [ PATCH_DOM0, PATCH_CELL, PATCH_DOMU ] and mGetRebootNode(_oneoff_plugin_data):
                    self.mPatchLogWarn("Currently reboot option post oneoff v2 plugin execution is supported only in case of cells. Current plugin will not be run.")
                    continue

                if str(_plugin_target.lower()) in str(self.mGetTargetTypes()[0].lower()):
                    # Validate the script bundle on exacloud node only once for the first node
                    if _node_name == _node_list[0]:
                        # Step1. Validate the script bundle
                        self.mPatchLogInfo(f"Validating oneoff v2 plugin script bundle for node {_node_name}")
                        _rc = self.mValidateOneoffPluginScriptBundle(_oneoff_plugin_data)
                        if _rc != PATCH_SUCCESS_EXIT_CODE and _fail_on_error:
                            self.mAddError(_rc,"")
                    else:
                        # Assume validation is successful for subsequent nodes
                        _rc = PATCH_SUCCESS_EXIT_CODE

                    if _rc == PATCH_SUCCESS_EXIT_CODE:
                        # Step 2. Copy oneoff plugins.
                        self.mPatchLogInfo(f"Copying oneoff v2 plugins to node {_node_name}")
                        _rc = self.mCopyPluginsToTargetNodesV2(_node_name, _oneoff_plugin_data)
                        if _rc == PATCH_SUCCESS_EXIT_CODE:
                            # Step 2. Run one off patch operation.
                            self.mPatchLogInfo(
                                f"Copy of oneoff v2 plugin is successful. Executing oneoff v2 plugin on node {_node_name}")
                            _rc = self.mExecuteOneOffPatchv2(_node_name, _oneoff_plugin_data)

                        # Step 3. Cleanup oneoff plugins and copy logs to exacloud
                        # irrespetive of plugin operation was successful or failed.
                        self.mPatchLogInfo(f"Cleaning up oneoff v2 plugin on node {_node_name}")
                        self.mCleanupOneoffV2PluginScript(_node_name, _oneoff_plugin_data)

                    if _rc != PATCH_SUCCESS_EXIT_CODE and _fail_on_error:
                        _ret = _rc
        return _ret

    def mValidateOneoffPluginScriptBundle(self, aOneoffPluginData):
        """
        Validates oneoff v2 plugin script bundle.

        :param aOneoffPluginData: oneoff plugin metadata
        :return: PATCH_SUCCESS_EXIT_CODE if validation is successful, otherwise an error code
        """
        _ret = PATCH_SUCCESS_EXIT_CODE

        # Location of oneoff plugins (on exacloud and on target node)
        try:

            # Extract script bundle name and hash from the plugin metadata
            _script_bundle_name = mGetScriptBundleName(aOneoffPluginData)
            _script_bundle_hash = mGetScriptBundleHash(aOneoffPluginData)

            # Construct the relative path to the script bundle on Exacloud
            _relative_script_path_on_exacloud = f"{get_gcontext().mGetBasePath()}/exadataPrePostPlugins/oneoff_patch/"

            self.mPatchLogInfo(
                f"Validating Exacloud plugin script bundle: bundle name={_script_bundle_name}, bundle hash={_script_bundle_hash}, relative path on Exacloud={_relative_script_path_on_exacloud}")

            # Check if the relative script path on Exacloud exists
            if not os.path.exists(_relative_script_path_on_exacloud):
                self.mPatchLogError(f"Parent plugins directory is missing: {_relative_script_path_on_exacloud}")
                _ret = PARENT_PLUGINS_MISSING
                return _ret

            # Construct the full path to the script bundle tar file
            _bundle_tar = os.path.join(_relative_script_path_on_exacloud, f"{_script_bundle_name}")
            if not os.path.exists(_bundle_tar):
                self.mPatchLogError(f"Oneoff v2 plugin script bundle is missing: {_bundle_tar}")
                _ret = ONEOFFV2_PLUGIN_SCRIPT_BUNDLE_MISSING
                return _ret

            _computed_hash = self.mComputeSha256Checksum(_bundle_tar)
            self.mPatchLogInfo(f"Computed SHA256 checksum of the bundle tar : {_computed_hash}")

            if _computed_hash:
                if _computed_hash != _script_bundle_hash:
                    self.mPatchLogError(
                        f"SHA256 sum mismatch for script bundle. Expected: {_script_bundle_hash}, Computed: {_computed_hash}")
                    _ret = ONEOFFV2_PLUGIN_SCRIPT_BUNDLE_HASH_MISMATCH
                    return _ret
            else:
                self.mPatchLogError("Failed to compute SHA256 checksum for script bundle")
                _ret = ONEOFFV2_PLUGIN_SCRIPT_BUNDLE_HASH_MISMATCH
                return _ret

        except Exception as e:
            self.mPatchLogError(f"Exception: Validating presence of oneoff plugins : {str(e)}")
            _ret = ONEOFFV2_PLUGIN_SCRIPT_VALIDATION_EXCEPTION

        return _ret

    def mRunOneOffV2inNonRolling(self):
        """
        This method executed oneoff plugins
        in non-rolling manner.
        :return: PATCH_SUCCESS_EXIT_CODE in case of successful patch execution
                or FailOnError flag was set to false
            else
                return error code as per error details returned
                from below execution flow.
        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        _list_of_hosts_where_oneoff_plugin_execution_failed = []
        _script_alias = None
        _plugin_target = None
        _oneoff_plugin_data = {}
        _ret = PATCH_SUCCESS_EXIT_CODE
        _fail_on_error = None

        def _run_oneoffv2_in_non_rolling(aNode, aStatus):

            self.mPatchLogInfo(f"Executing oneoff V2 plugins on Node : {aNode}.")
            try:
                if str(mGetPluginTargetV2(_oneoff_plugin_data).lower()) in str(self.mGetTargetTypes()[0].lower()):
                    # Step1. Validate the script bundle
                    _ret = self.mValidateOneoffPluginScriptBundle(_oneoff_plugin_data)
                    if _ret != PATCH_SUCCESS_EXIT_CODE:
                        aStatus.append({'node': aNode, 'status': 'failed', 'errorcode':_ret})
                    else:
                        # Step 2. Copy oneoff plugins.
                        _ret = self.mCopyPluginsToTargetNodesV2(aNode, _oneoff_plugin_data)
                        if _ret != PATCH_SUCCESS_EXIT_CODE:
                            aStatus.append({'node': aNode, 'status': 'failed', 'errorcode':_ret})
                        else:
                            # Step 3. Run one off patch operation.
                            _ret = self.mExecuteOneOffPatchv2(aNode, _oneoff_plugin_data)
                            if _ret != PATCH_SUCCESS_EXIT_CODE:
                                aStatus.append({'node': aNode, 'status': 'failed', 'errorcode':_ret})

                        # Step 4. Cleanup oneoff plugins and copy logs to exacloud
                        # irrespetive of plugin operation was successful or failed.
                        self.mCleanupOneoffV2PluginScript(aNode, _oneoff_plugin_data)

            except Exception as e:
                 self.mPatchLogError("Error while running oneoff v2 plugin on specified targets. \n" + str(e))
        # End of _run_oneoffv2_in_non_rolling method

        """
         Parallelly execute oneoffv2 plugins
         target hosts
        """
        _list_of_hosts_where_oneoff_plugin_execution_failed = []
        _plist = ProcessManager()
        _rc_status = _plist.mGetManager().list()

        if len(self.mOffV2NodeList()) == 0:
            self.mPatchLogWarn("Input node list is empty. No plugins were executed.")
            return _ret

        for _oneoff_plugin_data in self.mGetPluginMetadata():
            _fail_on_error = mGetFailonError(_oneoff_plugin_data)
            _plugin_target = mGetPluginTargetV2(_oneoff_plugin_data)
            _script_alias = mGetScriptAlias(_oneoff_plugin_data)

            self.mPatchLogInfo(
                f"Current oneoff plugin scripts will be run with the following input : {json.dumps(_oneoff_plugin_data, indent=4)}")
            # Validate only for the list of scripts passed as part of ScriptAliasList
            if self.mGetScriptAliasListToBeExecuted() and len(self.mGetScriptAliasListToBeExecuted()) > 0:
                if mGetScriptAlias(_oneoff_plugin_data) in [_script_alias_name.lower() for _script_alias_name in self.mGetScriptAliasListToBeExecuted()]:
                    self.mPatchLogInfo(
                        f"{str(_script_alias)} found in the Script Alias List : {str(self.mGetScriptAliasListToBeExecuted())} and current oneoff plugin will be run.")
                else:
                    self.mPatchLogWarn(
                        f"{str(_script_alias)} not found in the Script Alias List : {str(self.mGetScriptAliasListToBeExecuted())} and current oneoff plugin will not be run.")
                    continue
            else:
                self.mPatchLogInfo("ScriptAliasList passed is empty and no oneoff plugin scripts will be run")
                continue

            for _remote_node in self.mOffV2NodeList():
                # Currently reboot option supported only on cells.
                if mGetPluginTargetV2(_plugin_target).lower() in [ PATCH_DOM0, PATCH_CELL, PATCH_DOMU ] and mGetRebootNode(_oneoff_plugin_data):
                    self.mPatchLogInfo("Currently reboot option post oneoff v2 plugin execution is supported only in case of cells. Current plugin will not be run.")
                    continue
   
                _p = ProcessStructure(_run_oneoffv2_in_non_rolling, [_remote_node, _rc_status], _remote_node)
        
                '''
                 Timeout parameter configurable in Infrapatching.conf
                 Currently it is set to one Hour.
                '''
                _p.mSetMaxExecutionTime(self.mGetOneoffV2ExecutionTimeoutInSeconds())
     
                _p.mSetJoinTimeout(PARALLEL_OPERATION_TIMEOUT_IN_SECONDS)
                _p.mSetLogTimeoutFx(self.mPatchLogWarn)
                _plist.mStartAppend(_p)
        
            _plist.mJoinProcess()
        
            if _plist.mGetStatus() == "killed":
                if _fail_on_error:
                    _ret = ONEOFFV2_APPLY_FAILED
                    _suggestion_msg = "Timeout while executing oneoff V2 plugin execution in parallel."
                    self.mAddError(_ret, _suggestion_msg)
                else:
                    self.mPatchLogWarn("Timeout while executing oneoff V2 plugin execution in parallel.")
                return _ret
        
            # validate the return codes
            _list_of_hosts_where_oneoff_plugin_execution_failed = []
            for _rc_details in _rc_status:
                if _rc_details['status'] == "failed":
                    _list_of_hosts_where_oneoff_plugin_execution_failed.append(_rc_details['node'])
    
            if len(_list_of_hosts_where_oneoff_plugin_execution_failed) > 0:
                if _fail_on_error:
                    _ret = ONEOFFV2_APPLY_FAILED
                    _suggestion_msg = f"Error while running oneoff v2 plugin on specified targets : {_list_of_hosts_where_oneoff_plugin_execution_failed}. \n"
                    self.mAddError(_ret, _suggestion_msg)
                    break
                else:
                    self.mPatchLogWarn(
                        f"Error while running oneoff v2 plugin on specified targets : {_list_of_hosts_where_oneoff_plugin_execution_failed}. \n")
        return _ret

    def mCopyPluginsToTargetNodesV2(self, aNode, aOneoffPluginData):
        '''
          This method copies plugin and other
          config files to target nodes specified.
        '''
        _ret = PATCH_SUCCESS_EXIT_CODE
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=aNode, aTimeout=20)
        _script_parent_dir_name = None
        _plugin_target = None
        _fail_on_error = None
        _script_dir_name = None

        '''
         Below code snippet validates for existence of
         one off patch directories locally on the exacloud as well as the 
         target nodes.
        '''
        _relative_script_path_on_exacloud = None
        # Location of oneoff plugins (on exacloud and on target node)
        try:
            _script_dir_name = f"{get_gcontext().mGetBasePath()}/exadataPrePostPlugins/oneoff_patch"
            _plugin_target = mGetPluginTargetV2(aOneoffPluginData)
            _fail_on_error = mGetFailonError(aOneoffPluginData)

            if not os.path.exists(_script_dir_name):
                _ret = PARENT_PLUGINS_MISSING
                if _fail_on_error:
                    _suggestion_msg = f"Parent plugins for '{_plugin_target}' are not found on '{_relative_script_path_on_exacloud}'"
                    self.mAddError(_ret, _suggestion_msg)
                else:
                    self.mPatchLogWarn(
                        f"Parent plugins for '{_plugin_target}' are not found on '{_relative_script_path_on_exacloud}'")
                return _ret
        except Exception as e:
            _ret = ONEOFFV2_PATCH_COPY_FAILED
            if _fail_on_error:
                _suggestion_msg = "Exception: Validating presence of One off patches: " + str(e)
                self.mAddError(_ret, _suggestion_msg)
            else:
                self.mPatchLogError("Exception: Validating presence of One off patches: " + str(e))
            return _ret

        try:

            _remote_script_dir = mGetScriptAlias(aOneoffPluginData)
            _script_bundle_tar = mGetScriptBundleName(aOneoffPluginData)
            _plugin_target = mGetPluginTargetV2(aOneoffPluginData)

            # Create remote plugin stage directory before copying patches.
            self.mPatchLogInfo(
                f"Creating oneoff patch stage directory : {os.path.join(ONEOFF_REMOTE_STAGE_DIR, _remote_script_dir)} on remote node : {aNode}")
            _node.mExecuteCmdLog(f"mkdir -p {os.path.join(ONEOFF_REMOTE_STAGE_DIR, _remote_script_dir)}")

            self.mPatchLogInfo(
                f"Target Node: {aNode}, Copy plugins: Source = {_script_dir_name}/{_script_bundle_tar}, Destination location = {os.path.join(ONEOFF_REMOTE_STAGE_DIR, _remote_script_dir)}")

            if os.path.exists(os.path.join(_script_dir_name, _script_bundle_tar)):
                _node.mCopyFile(os.path.join(_script_dir_name, _script_bundle_tar), os.path.join(ONEOFF_REMOTE_STAGE_DIR, _remote_script_dir))

            if _node.mFileExists(os.path.join(ONEOFF_REMOTE_STAGE_DIR, _remote_script_dir, _script_bundle_tar)):
                _node.mExecuteCmdLog(
                    f"cd {os.path.join(ONEOFF_REMOTE_STAGE_DIR, _remote_script_dir)}; tar -xvzf {_script_bundle_tar}")
            else:
                self.mPatchLogError(f"Oneoff plugin script bundle is missing on target node: {aNode}")
                _ret = ONEOFFV2_PLUGIN_SCRIPT_BUNDLE_MISSING

        except Exception as e:
            _ret = ONEOFFV2_PATCH_COPY_FAILED
            if _fail_on_error:
                _suggestion_msg = f"Exception: Error in Copying One off patches to target node: {aNode} and location : {os.path.join(ONEOFF_REMOTE_STAGE_DIR,  mGetScriptAlias(aOneoffPluginData))}"
                self.mAddError(_ret, _suggestion_msg)
            else:
                self.mPatchLogWarn(
                    f"Exception: Error in Copying One off patches to target node: {aNode} and location : {os.path.join(ONEOFF_REMOTE_STAGE_DIR, mGetScriptAlias(aOneoffPluginData))}")
            self.mPatchLogError(traceback.format_exc())
        finally:
            if _node.mIsConnected():
                _node.mDisconnect()
            self.mPatchLogInfo(f"mCopyPluginsToTargetNodesV2 exited with return code: {_ret}")
            return _ret

    def mCleanupOneoffV2PluginScript(self, aNode, aOneoffPluginData):
        '''
         Clean up scripts and config files on the
         Target nodes.
        '''
        _node = exaBoxNode(get_gcontext())
        _plugin_log = None
        _script_parent_dir_name = None

        try:
            _plugin_log = self.mGetPluginLog(aOneoffPluginData)
            _script_parent_dir_name = mGetScriptAlias(aOneoffPluginData)

            _node.mConnect(aHost=aNode, aTimeout=20)
            # 3 a. Copy all the relevant log to local.
            self.mPatchLogInfo(
                f"Copying the logs from Node : {aNode}, Location : {_plugin_log} to Local Directory : {self.mGetLogPath()} ")

            _exacloud_log_path = f"{self.mGetLogPath()}/{TASK_ONEOFFV2}.{aNode}_{mGetScriptAlias(aOneoffPluginData)}.log"
            if _node.mFileExists(_plugin_log):
                _node.mCopy2Local(_plugin_log, _exacloud_log_path)

            # 3 b. Delete One-off patches.
            _plugin_dir_to_be_cleaned_up = os.path.join(ONEOFF_REMOTE_STAGE_DIR, mGetScriptAlias(aOneoffPluginData))
            if _node.mFileExists(_plugin_dir_to_be_cleaned_up):
                self.mPatchLogInfo(
                    f"Deleting plugin directory = {_plugin_dir_to_be_cleaned_up} from target node : {aNode}")
                _node.mExecuteCmdLog(f"rm -rfv {_plugin_dir_to_be_cleaned_up}")
        except Exception as e:
            self.mPatchLogWarn(
                f"Exception: Error in deleting One off patch directories on Node : {aNode} and location : {os.path.join(ONEOFF_REMOTE_STAGE_DIR, _script_parent_dir_name)}")
            self.mPatchLogError(traceback.format_exc())
        finally:
            if _node.mIsConnected():
                _node.mDisconnect()

    def mExecuteOneOffPatchv2(self, aNode, aOneoffPluginData):
        """
         This method executes the one off scripts and options specified
         by user. Currently a one off script is checked in and
         will always return success. User can customise this file
         as per their requirement.

          -> return PATCH_SUCCESS_EXIT_CODE if successful.
          -> return any other error code other than PATCH_SUCCESS_EXIT_CODE if failure.
        """

        _ret = PATCH_SUCCESS_EXIT_CODE
        _connected_as_non_root_user = False
        _sudo_str = ''
        _plugin_target = None
        _remote_script_name_for_oneoff_plugins = None
        _plugin_log = None
        _fail_on_error = None

        _oneoff_args = self.mGetOneOffPluginArguments()
        _node = exaBoxNode(get_gcontext())
        try:
            _plugin_target = mGetPluginTargetV2(aOneoffPluginData)
            _remote_script_name_for_oneoff_plugins = self.mGetRemoteScriptNameForOneOffPlugins(aOneoffPluginData)
            _plugin_log = self.mGetPluginLog(aOneoffPluginData)
            _fail_on_error = mGetFailonError(aOneoffPluginData)

            # Try to connect as opc user to domu. If not exist, then try with root user
            if str(_plugin_target).lower() == PATCH_DOMU and self.mIsOpcUserExists(aNode):
                _node.mSetUser('opc')
                _node.mSetMaxRetries(self.mGetMaxNumberofSshRetries())
                _connected_as_non_root_user = True
                self.mPatchLogInfo(f"One-off Patch run: Connecting as opc user to '{_plugin_target}' to run plugins.")
            else:
                self.mPatchLogInfo(f"One-off Patch run: Connecting as root user to '{_plugin_target}' to run plugins.")

            if _connected_as_non_root_user:
                _sudo_str = 'sudo '
                _cmd_oneoff_run = f"{_sudo_str}chown -R opc:opc {ONEOFF_REMOTE_STAGE_DIR}; {_sudo_str}chmod +x {_remote_script_name_for_oneoff_plugins}; {_sudo_str}{_remote_script_name_for_oneoff_plugins} {_oneoff_args} > {_plugin_log} "
            else:
                _cmd_oneoff_run = f"chmod +x {_remote_script_name_for_oneoff_plugins};{_remote_script_name_for_oneoff_plugins} {_oneoff_args} > {_plugin_log} "

            self.mPatchLogInfo(f"One off command is : {_cmd_oneoff_run}")

            _node.mConnect(aHost=aNode, aTimeout=20)
            if not _node.mFileExists(_remote_script_name_for_oneoff_plugins):
                _ret = ONEOFFV2_PATCHES_MISSING
                if _fail_on_error:
                    _suggestion_msg = f"Unable to find one off patch file : {_remote_script_name_for_oneoff_plugins}"
                    self.mAddError(_ret, _suggestion_msg)
                else:
                    self.mPatchLogWarn(f"Unable to find one off patch file : {_remote_script_name_for_oneoff_plugins}")
                if _node.mIsConnected():
                    _node.mDisconnect()
                return _ret

            _i, _o, _e = _node.mExecuteCmd(_cmd_oneoff_run)
            _out = _o.readlines()
            for _output in _out:
                self.mPatchLogInfo(f"{_output.strip()}")
            _rc = _node.mGetCmdExitStatus()
            self.mPatchLogInfo(f"One Off Patch Exit Command Status {_rc} ")
            if int(_rc) == 0:
                self.mPatchLogInfo(f"\nOne-off Patch apply completed successfully on {aNode}.\n")
                if mGetRebootNode(aOneoffPluginData):
                    self.mPatchLogInfo(
                        f"RebootNode parameter for the oneoff plugin execution flow was set to True. Node : {aNode} will be rebooted.")
                    _ret = self.mRestartNodePostExecutingPluginMetadataScripts(aNode, aOneoffPluginData)
                    '''
                     Irrespective of FailOnError flag was set or not, in case of
                     unable to startup node after reboot
                    '''
                    if _ret != PATCH_SUCCESS_EXIT_CODE:
                        _ret = ONEOFFV2_APPLY_FAILED
                        if _fail_on_error:
                            _suggestion_msg = f"Running one-off patch failed on node = {aNode}"
                            self.mAddError(_ret, _suggestion_msg)
                        else:
                            self.mPatchLogWarn(f"Running one-off patch failed on node = {aNode}")
            else:
                _ret = ONEOFFV2_APPLY_FAILED
                if _fail_on_error:
                    _suggestion_msg = f"Running one-off patch failed on node = {aNode}"
                    self.mAddError(_ret, _suggestion_msg)
                else:
                    self.mPatchLogWarn(
                        f"Running one-off patch failed on node = {aNode} and since FailOnError is set to 'no', plugin operations will continue.")
        except Exception as e:
            _ret = ONEOFFV2_APPLY_FAILED
            if _fail_on_error:
                _suggestion_msg = f"Unable to execute oneoff v2 plugins on {aNode}. Error : {str(e)}"
                self.mAddError(_ret, _suggestion_msg)
            else:
                self.mPatchLogWarn(f"Unable to execute oneoff v2 plugins on {aNode}. Error : {str(e)}")
            self.mPatchLogError(traceback.format_exc())
        finally:
            if _node.mIsConnected():
                _node.mDisconnect()
            return _ret

    def mGetPluginLog(self, aOneoffPluginData):
        _current_plugin_log_name = f"oneoff_plugins_{mGetScriptAlias(aOneoffPluginData)}.log"
        return os.path.join(ONEOFF_REMOTE_STAGE_DIR, _current_plugin_log_name)

    def mGetRemoteScriptNameForOneOffPlugins(self, aOneoffPluginData):
        _patch_file = os.path.join(ONEOFF_REMOTE_STAGE_DIR, mGetScriptAlias(aOneoffPluginData) + "/" + mGetScriptName(aOneoffPluginData))
        return _patch_file

    def mGetRemoteScriptNameForDbnuPlugins(self, aOneoffPluginData):
        _patch_file = os.path.join(DBNU_PLUGIN_REMOTE_STAGE_DIR, mGetScriptAlias(aOneoffPluginData) + "/" + mGetScriptName(aOneoffPluginData))
        return _patch_file

    def mRestartNodePostExecutingPluginMetadataScripts(self, aNode, aOneoffPluginData):
        """
         This method reboots the current node and starts it up
         in case of RebootNode flag set to True.

         return: PATCH_SUCCESS_EXIT_CODE in case of node was
                started up successfully.
        else
            NODE_DID_NOT_STARTUP_POST_ONEOFF_PLUGINS error code in case of unable
            to startup node post reboot
        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        _node_connect_time = 0
        _node = exaBoxNode(get_gcontext())
        _fail_on_error = None
        try:
            _fail_on_error = mGetFailonError(aOneoffPluginData)

            # Reboot node and monitor for it to start up.
            self.mGetCluControl().mRebootNode(aNode, aWait=True, aForce=True)

            # additional polling from infra patching to
            # verify if node started up successfully.
            while(_node_connect_time < self.mGetOneoffV2NodeRebootTimeoutInSeconds()):
                if not _node.mIsConnectable(aNode, aTimeout=mGetSshTimeout(), aKeyOnly=True):
                    self.mPatchLogInfo(
                        f"Node : {aNode} did not start yet, sleeping for 30 seconds before checking for node to be up.")
                    sleep(ONEOFFV2_SLEEP_TIMEOUT_IN_SECONDS)
                    _node_connect_time += ONEOFFV2_SLEEP_TIMEOUT_IN_SECONDS
                else:
                    _node.mConnect(aHost=aNode, aTimeout=20)
                    _in, _out, _err = _node.mExecuteCmd('uptime')
                    _output = _out.readlines()
                    self.mPatchLogInfo(f"Node : {aNode} is accessible and the uptime on the node is {str(_output)}")

                if not _node.mIsConnectable(aNode, aTimeout=mGetSshTimeout(), aKeyOnly=True):
                    _ret = NODE_DID_NOT_STARTUP_POST_ONEOFF_PLUGINS
                    if _fail_on_error:
                        _suggestion_msg = f"Node : {aNode} did not startup post oneoff plugin application and node reboot."
                        self.mAddError(_ret, _suggestion_msg)
                    else:
                        self.mPatchLogWarn(
                            f"Node : {aNode} did not startup post oneoff plugin application and node reboot.")
        except Exception as e:
            _ret = NODE_DID_NOT_STARTUP_POST_ONEOFF_PLUGINS
            if _fail_on_error:
                _suggestion_msg = f"Unable to perform reboot node : {aNode} post applying oneoff v2 plugins. Error : {str(e)}"
                self.mAddError(_ret, _suggestion_msg)
            else:
                self.mPatchLogWarn(
                    f"Unable to perform reboot node : {aNode} post applying oneoff v2 plugins. Error : {str(e)}")
            self.mPatchLogError(traceback.format_exc())
        finally:
            if _node.mIsConnected():
                _node.mDisconnect()
            return _ret

    def mGetOneoffV2ExecutionTimeoutInSeconds(self):
        return int(mGetInfraPatchingConfigParam('oneoffv2_execution_timeout_in_seconds'))

    def mGetOneoffV2NodeRebootTimeoutInSeconds(self):
        return int(mGetInfraPatchingConfigParam('oneoffv2_node_reboot_timeout_in_seconds'))
