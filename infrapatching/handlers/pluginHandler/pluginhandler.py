#
# $Header: ecs/exacloud/exabox/infrapatching/handlers/pluginHandler/pluginhandler.py /main/33 2025/11/06 06:48:23 araghave Exp $
#
# pluginhandler.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
#
#    NAME
#      pluginhandler.py - This module contains common methods to support DBNU and Exacloud plugins.
#
#    DESCRIPTION
#       This module contains common methods to support DBNU and Exacloud plugins.
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    araghave    08/13/25 - Enh 38228272 - EXACC GEN2 | PATCHING | SWITCH BACK
#                           TO OPC USER FOR ALL INFRA PATCH USE CASES IN CASE
#                           OF ROOT KEY INJECTION FAILS
#    sdevasek    07/24/25 - Enh 38120913 - TIMEOUT RUNNING OF CUSTOM_DOMU.SH
#                           IF IT EXCEEDS 60 MINS
#    araghave    03/04/25 - Bug 37417431 - EXACS | DOMU | UNWANTED SSH
#                           CONNECTION FROM 169.254.200.1 LOCKING OPC USER
#    diguma      02/28/25 - Bug 37072935: EXADB-XS:ERROR HANDLING:DOMU PATCH
#                           FAILURE SENDING WRONG ERROR MESSAGE FROM ECRA
#    araghave    02/04/25 - Enh 34479463 - PROVIDE EXACLOUD REGISTRATION AND
#                           PLUGIN SUPPORT FOR CELLS
#    diguma      12/06/24 - bug 37365122 - EXACS:24.4.2.1:X11M: ROLLING DOM0
#                           PATCHING FAILS WITH SSH CONNECTIVITY CHECK FAILED
#                           DURING PATCHING EVEN THOUGH EXASSH TO DOMUS WORK
#    araghave    08/27/24 - Enh 36829406 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE CORE, PLUGIN AND TASKHANDLER
#                           FILES
#    remamid     08/02/24 - Validate existence of custom_domu.sh script before
#                           execution during patching Bug 36912407
#    araghave    07/15/24 - Enh 36830077 - CLEANUP KSPLICE CODE FROM
#                           INFRAPATCHING FILES
#    araghave    06/13/24 - Enh 36522596 - REVIEW PRE-CHECK/PATCHING/ROLLBACK
#                           LOGS AND CLEAN-UP
#    araghave    03/13/24 - Enh 36270822 - EXECUTION OF EXACLOUD PLUGINS USING
#                           INFRA PATCHING PLUGIN METADATA
#    araghave    02/28/24 - Enh 36295801 - IMPLEMENT ONEOFFV2 PLUGIN EXACLOUD
#                           CHANGES
#    jyotdas     02/05/24 - ER 36108549 - adbd dom0domu plugins should be
#                           enabled in case user specified dom0 plugin type
#    ririgoye    08/23/23 - Bug 35616435 - Fix redundant/multiple instances of
#                           mConnect
#    araghave    07/24/23 - Enh 35629517 - RENAME ERROR CODE SPECIFIC TO CUSTOM
#                           PLUGINS
#    sdevasek    07/08/23 - BUG 35555704 - EXACS:BB:INFRAPATCHING:DOM0 PATCH
#                           FAILED AS VM IS NOT ACCESSIBLE
#    diguma      04/25/23 - bug 34392890 - check connectivity of domu if
#                           dom0domu is enabled in precheck
#    diguma      04/23/23 - Bug 35130530 - adding user hostname in error msg
#                           when executing domu plugins
#    jyotdas     04/17/23 - ENH 35106082 - By default run dom0domu plugin on
#                           autonomous vms
#    vmallu      03/17/23 - Enh 32298104 - ENABLE DBNU PLUGIN SUPPORT FOR DOMU
#    antamil     02/02/23 - ENH 34893583 - ENABLE PLUGIN SUPPORT FOR
#                           MONTHLY PATCHING
#    jyotdas     11/30/22 - BUG 34777710 - Plugin failures no longer report the
#                           customer domu name in error
#    araghave    11/03/22 - Bug 34751185 - EXACS:22.2.1:MULTI-VM: DOM0 APPLY
#                           (DOM0+DOM0DOMU PLUGIN): EXACLOUDPLUGINHANDLER
#                           MARKING EXECUTION OF CUSTOM_DOM0_DOMU.SH AS FAILURE
#                           INSTEAD OF SUCCESS
#    pkandhas    08/17/22 - Bug 34245376 - Remove code related to dom0.txt
#    araghave    06/06/22 - Enh 34239188 - ADD ADDITIONAL, GRANULAR ERROR
#                           CODES FOR PLUG-IN FAILURES
#    araghave    04/11/22 - Enh 34048154 - ONEOFF PATCH OPERATION TO SUPPORT A
#                           PLUGIN FRAMEWORK WITH GENERIC OPTIONS
#    sdevasek    03/10/22 - Bug 33912517 - DOM0 PATCHING:INFRA PATCHING LOGS 
#                           SHOW MISLEADING ERRORS MESSAGES
#    sdevasek    01/27/22 - Bug 33732985 - EXACLOUD PLUGIN CONSOLE LOG IS NOT
#                           COPIED TO EXACLOUD FROM DOMU NODE FOR OPC USER
#    araghave    08/04/21 - Enh 33182904 - Move all configurable parameters
#                           from constants.py to Infrapatching.conf
#    jyotdas     06/30/21 - Bug 32813015 - non-rolling patching should not run
#                           dom0domu plugin
#    nmallego    08/28/20 - Refactor infra patching code
#    nmallego    08/28/20 - Creation
#

import os
import json
import traceback
from time import sleep
from exabox.infrapatching.handlers.generichandler import GenericHandler
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.infrapatching.utils.constants import PATCH_DOM0, PATCH_DOMU, PLUGIN_DBNU, POST_PATCH, OP_STYLE_NON_ROLLING, TASK_ONEOFF, TASK_ONEOFFV2
from exabox.infrapatching.core.infrapatcherror import *
from exabox.infrapatching.utils.constants import *
from exabox.infrapatching.utils.utility import mGetPluginTargetV2, mGetSshTimeout
from exabox.utils.node import connect_to_host

class PluginHandler(GenericHandler):

    def __init__(self, *initial_data, **kwargs):
        super(PluginHandler, self).__init__(*initial_data, **kwargs)
        self.mPatchLogInfo("PluginHandler")

        # Commands to handle
        # patch dom0 slcs08adm07adm08 op=patch EnablePlugins=yes PluginTypes=dom0+dom0domu",
        # patch dom0 slcs08adm07adm08 op=patch EnablePlugins=yes PluginTypes=dom0",
        # patch domu slcs08adm07adm08 op=patch EnablePlugins=yes PluginTypes=domu

        for dictionary in initial_data:
            for key in dictionary:
                if key == "EnablePlugins":
                    self.__enable_plugins = dictionary[key]
                elif key == "PluginTypes":
                    self.__plugin_types = dictionary[key]
                elif key == "OneoffScriptAlias":
                    self.__scriptaliaslist = dictionary[key]
                elif key == "InfraPatchPluginMetaData":
                    self.__pluginsMetadata = dictionary[key]

        '''
         Sample plugin metadata passed from ecra.

           "InfraPatchPluginMetaData": [
             {
               "ScriptPathName": "syslens/syslens.sh",
               "ScriptAlias": "syslens",
               "ChangeRequestID": "CRID-4567",
               "Description": "syslens.sh updates the syslens RPM",
               "PluginType": "oneoff",
               "PluginTarget": "dom0",
               "ScriptOrder": "1000",
               "IsEnabled": "Yes",
               "RebootNode": "No",
               "FailOnError": "No"
             },
             {
               "ScriptPathName": "iptables/iptables.sh",
               "ScriptAlias": "iptables",
               "ChangeRequestID": "CRID-3212",
               "Description": "iptables.sh verifies the iptable entries on dom0 updates the same post patching.",
               "PluginType": "exacloud",
               "PluginTarget": "dom0",
               "ScriptOrder": "1000",
               "IsEnabled": "Yes",
               "RebootNode": "No",
               "FailOnError": "No"
             }
           ]
        '''
        # Flags to indicate whether we should run exadata/exacloud plugins
        self.__run_plugins_enable = True
        self.__run_plugins_disable = False

        # Flag to indicate whether we need to run plugins on domu of it's dom0.
        # Ideally, we can run plugins on domu on ADW or ATP or FA since domu is
        # accessible.
        self.__run_user_plugins_on_dom0s_domu_node = False
        self.__run_user_plugins_on_dom0s_domu_node_plugin_metadata = False
        self.__run_user_plugins_on_dom0_node = False
        self.__run_user_plugins_on_domu_node = False

        # Needed for running plugins
        self.__last_node_patched = None
        self.__plugins_log_path_on_launch_node = ""

        # Required for Kplice/OneOff Plugins
        self.__node_list = []
        self.__plugin_location_dir = None
        self.__plugin_target = None
        self.__oneoff_plugin_arguments = None

        '''
          Additional options for oneoff patch operations.
        '''
        if self.mGetTask() in [ TASK_ONEOFF, TASK_ONEOFFV2, TASK_PATCH, TASK_ROLLBACK ]:
            self.mSetAdditionalOneoffOptions()

    def mGetScriptAliasListToBeExecuted(self):
        return [self.__scriptaliaslist]

    def mGetRunUserPluginsonDom0sdomuInCaseOfPluginMetadata(self):
        return self.__run_user_plugins_on_dom0s_domu_node_plugin_metadata

    def mSetRunUserPluginsonDom0sdomuInCaseOfPluginMetadata(self, aBool):
        self.__run_user_plugins_on_dom0s_domu_node_plugin_metadata = aBool

    def mGetPluginMetadata(self):
        return self.__pluginsMetadata

    def mSetPluginMetadata(self, aPluginMetadata):
        self.__pluginsMetadata = aPluginMetadata

    def mSetAdditionalOneoffOptions(self):
        if self.mGetAdditionalOptions() and 'OneoffCustomPluginFile' in self.mGetAdditionalOptions()[0] \
                and self.mGetAdditionalOptions()[0]['OneoffCustomPluginFile'] != 'none':
            self.mSetOneoffPluginFileLocation(self.mGetAdditionalOptions()[0]['OneoffCustomPluginFile'])
	
        if self.mGetAdditionalOptions() and 'OneoffScriptArgs' in self.mGetAdditionalOptions()[0] \
                and self.mGetAdditionalOptions()[0]['OneoffScriptArgs'] != 'none':
            self.mSetOneOffPluginArguments(self.mGetAdditionalOptions()[0]['OneoffScriptArgs'])
        else:
            self.mPatchLogInfo("No additional arguments passed for the oneoff plugin script.")

    def mGetRunUserPluginsonDom0sdomuNode(self):
        return self.__run_user_plugins_on_dom0s_domu_node

    def mSetRunUserPluginsonDom0sdomuNode(self, aBool):
        self.__run_user_plugins_on_dom0s_domu_node = aBool

    def mGetRunUserPluginsonDom0Node(self):
        return self.__run_user_plugins_on_dom0_node

    def mSetRunUserPluginsonDom0Node(self, aBool):
        self.__run_user_plugins_on_dom0_node = aBool

    def mGetRunUserPluginsonDomuNode(self):
        return self.__run_user_plugins_on_domu_node

    def mSetRunUserPluginsonDomuNode(self, aBool):
        self.__run_user_plugins_on_domu_node = aBool

    def mGetEnablePlugins(self):
        return self.__enable_plugins

    def mGetPluginTypes(self):
        return self.__plugin_types

    def mSetPluginTypes(self, aPluginTypes):
        self.__plugin_types = aPluginTypes

    def mGetPluginsLogPathOnLaunchNode(self):
        return self.__plugins_log_path_on_launch_node

    def mSetPluginsLogPathOnLaunchNode(self, aPluginsLogPathOnLaunchNode):
        self.__plugins_log_path_on_launch_node = aPluginsLogPathOnLaunchNode

    def mGetLastNodePatched(self):
        return self.__last_node_patched

    def mSetLastNodePatched(self, aLastNodePatched):
        self.__last_node_patched = aLastNodePatched

    def mGetNodeList(self):
        return self.__node_list

    def mSetNodeList(self,aList):
        self.__node_list = aList

    def mGetOneoffPluginFileLocation(self):
        return self.__plugin_location_dir

    def mSetOneoffPluginFileLocation(self, aPluginLocDir):
        self.__plugin_location_dir = aPluginLocDir

    def mGetOneOffPluginArguments(self):
        return self.__oneoff_plugin_arguments

    def mSetOneOffPluginArguments(self, aOneoffPluginArguments):
        self.__oneoff_plugin_arguments = aOneoffPluginArguments

    def mGetPluginTarget(self):
        return self.__plugin_target

    def mSetPluginTarget(self, aTarget):
        self.__plugin_target = aTarget

    # equivalent to mUpdatePluginsMetadata in old code
    def initializePluginMetadata(self):
        """
        Update to indicate whether plugins needs to be run on which targets
        """
        if len(self.mGetPluginMetadata()) > 0:
            self.__enable_plugins = 'yes'

        if self.mGetEnablePlugins().lower() == 'yes':
            self.mPatchLogInfo(f"Exadata user plugins enable to run on cluster {self.mGetRackName()} ")

        # Valid plugins types for each target
        # patch dom0 slcs08adm07adm08 op=patch EnablePlugins=yes PluginTypes=dom0+dom0domu
        # patch dom0 slcs08adm07adm08 op=patch EnablePlugins=yes PluginTypes=dom0
        # patch domu slcs08adm07adm08 op=patch EnablePlugins=yes PluginTypes=domu
        # Based on https://confluence.oraclecorp.com/confluence/pages/viewpage.action?pageId=1825342541
        _valid_plugin_types_for_domu = ['domu']
        _valid_plugin_types_for_dom0 = ['dom0', 'dom0+dom0domu', 'dom0domu+dom0']
        _valid_plugin_types_for_dom0_domu = ['dom0domu', 'dom0+dom0domu', 'dom0domu+dom0']

        if self.__plugin_types:
            _mPluginTypes = self.__plugin_types.strip()
            _mPluginTypes = _mPluginTypes.replace(" ", "")
            self.__plugin_types = _mPluginTypes.lower()
            self.mSetPluginTypes(_mPluginTypes.lower())

        # Update to indicate whether domu or cell exacloud plugins needs to be run
        if self.mGetTargetTypes()[0] in [PATCH_DOMU, PATCH_CELL]:
            if self.__plugin_types in _valid_plugin_types_for_domu:
                self.__run_user_plugins_on_domu_node = True
                self.mPatchLogInfo(
                    f"Exadata user plugins enable to run on {self.mGetTargetTypes()} upgrade on cluster {self.mGetRackName()} ")
        # Update to indicate whether dom0 plugins needs to be run and also from dom0's domU
        elif PATCH_DOM0 in self.mGetTargetTypes():
            if self.__plugin_types in _valid_plugin_types_for_dom0:
                self.__run_user_plugins_on_dom0_node = True
                self.mPatchLogInfo(
                    f"Exadata user plugins are enabled to run on dom0 upgrade on cluster {self.mGetRackName()} ")

            if self.__plugin_types in _valid_plugin_types_for_dom0_domu:
                self.__run_user_plugins_on_dom0s_domu_node = True
                self.mPatchLogInfo(
                    f"Exadata user plugins enable to run on domU during dom0 upgrade on cluster {self.mGetRackName()} ")

            if len(self.mGetPluginMetadata()) > 0:
                for _exacloud_plugin_data in self.mGetPluginMetadata():
                    if mGetPluginTargetV2(_exacloud_plugin_data).lower() == "dom0domu":
                        '''
                         domudomu plugins from metadata will only be executed if
                         PluginTypes=dom0+dom0domu" and Enableplugins=yes is specified 
                         in Infrapatch payload.
                        '''
                        self.__run_user_plugins_on_dom0s_domu_node_plugin_metadata = True
                        self.mPatchLogInfo(
                            f"Exadata user plugins enable to run on domU during Dom0 upgrade on cluster {self.mGetRackName()} in case of plugin metadata passed as part of input json")

                        # Break from loop if atleast one occurance of
                        # plugin target type=dom0domu is found.
                        if self.__run_user_plugins_on_dom0s_domu_node_plugin_metadata:
                            break

            # We don't really need to run dom0domu plugins in case of non-rollying patch
            if self.mGetOpStyle() == OP_STYLE_NON_ROLLING:
                self.mTruncatedom0domuPlugins()

    def mExecutePrePostExacloudPlugins(self, aNode, aNodeType, aRemotePluginDir, aPluginsToRun, aStage, aRollback):
        """
          # Connect to a node (dom0 and domU) and run require plugins.
            PATCH_SUCCESS_EXIT_CODE : when successful
            Hexadecimal error code other than PATCH_SUCCESS_EXIT_CODE : when fails
        """
        _domUCustomerName = None
        try:
            ret = PATCH_SUCCESS_EXIT_CODE
            _connected_as_non_root_user = False
            _username = None
            _sudo_str = ''
            _node_type_name = ("DOMU" if (aNodeType == PATCH_DOMU) else "DOM0")
            if _node_type_name == "DOMU":
                _domUCustomerName = self.mGetDomUCustomerNameforDomuNatHostName(aNode)
                if _domUCustomerName:
                    self.mPatchLogInfo(
                        f"Setting Domu CustomerName {_domUCustomerName} for Domu NatHostName {aNode} in mSetLastNodePatched method in plugin ")
                    self.mSetLastNodePatched(_domUCustomerName)

            _node = exaBoxNode(get_gcontext())
            # Connect as opc for domU if exist, otherwise, as root user
            _user_to_connect_with = self.mGetUserDetailsBasedOnDomUhostnameToRunPlugins(aNode)
            if aNodeType == PATCH_DOMU and _user_to_connect_with:
                _username = _user_to_connect_with
                self.mPatchLogInfo(
                    f"mExecutePrePostExacloudPlugins: Connecting as {_username} user to '{_node_type_name}' '{aNode}' to run plugins.")
                if _username != 'root':
                    _connected_as_non_root_user = True
            else:
                self.mPatchLogInfo(
                    f"mExecutePrePostExacloudPlugins: Connecting as root user to '{_node_type_name}' '{aNode}' to run plugins")

            with connect_to_host(aNode, get_gcontext(), username=_username) as _dom0U_local:
                _plugin_file_to_exec = os.path.join(aRemotePluginDir, aPluginsToRun)
                if _dom0U_local.mFileExists(_plugin_file_to_exec):
                    self.mPatchLogInfo(
                        f"Parent {aStage.upper()} script '{_plugin_file_to_exec}' found for {_node_type_name} on target node : {aNode}.")
                else:
                    # Nothing can be done for plugins to run, so error out to let
                    #  user know this
                    _suggestion_msg = f"Parent {aStage.upper()} script '{_plugin_file_to_exec}' not found for {_node_type_name} on target node : {aNode}."
                    if aNodeType == PATCH_DOM0:
                        ret = EXACLOUD_PARENT_PLUGIN_FILES_MISSING_ON_DOM0
                    elif aNodeType == PATCH_DOMU:
                        ret = EXACLOUD_PARENT_PLUGIN_FILES_MISSING_ON_DOMU
                        if _domUCustomerName:
                            _suggestion_msg = f"Parent {aStage.upper()} script '{_plugin_file_to_exec}' not found for {_node_type_name} on target node : {aNode} with CustomerHostName: {_domUCustomerName} "

                    self.mAddError(ret, _suggestion_msg)
                    return ret

                self.mPatchLogInfo(
                    f"{aStage.upper()} plugins are running on {_node_type_name} '{_dom0U_local.mGetHostname()}'")

                # Need to run as sudo for all non-root user
                if _connected_as_non_root_user:
                    _sudo_str = 'sudo '

                '''
                Call the plugin with stage or phase as an argument
                We are also validating if the script is already running.
                
                if not aRollback:
                    _cmd = _sudo_str + "sh " + _plugin_file_to_exec + " patch " + aStage + " " + self.__last_node_patched
                else:
                    _cmd = _sudo_str + "sh " + _plugin_file_to_exec + " rollback " + aStage + " " + self.__last_node_patched
                '''
                if self.mIsExaSplice():
                    _plugin_log_file = f"{self.mGetPluginsLogPathOnLaunchNode()}/plugin_{aStage}_{aNode}_exasplice_console.out"
                else:
                    _plugin_log_file = f"{self.mGetPluginsLogPathOnLaunchNode()}/plugin_{aStage}_{aNode}_console.out"

                self.mPatchLogInfo(f"_plugin_log_file {_plugin_log_file}")

                if self.mGetLastNodePatched() is None:
                    self.mSetLastNodePatched(aNode)
                self.mPatchLogInfo(f"_last_node_patched {self.mGetLastNodePatched()}")

                if not _dom0U_local.mFileExists(_plugin_log_file):
                    if not aRollback:
                        _cmd = f"{_sudo_str}nohup sh {_plugin_file_to_exec} patch {aStage} {_plugin_log_file} {self.mGetLastNodePatched()} &"
                    else:
                        _cmd = f"{_sudo_str}nohup sh {_plugin_file_to_exec} rollback {aStage} {_plugin_log_file} {self.mGetLastNodePatched()} &"

                    # Run the plugin command in nohup.
                    self.mPatchLogInfo(f"{aStage.upper()} script executing cmd: {_cmd}")
                    _cmd_mkdir = f'{_sudo_str} mkdir -p {self.mGetPluginsLogPathOnLaunchNode()}'
                    _dom0U_local.mExecuteCmdLog(_cmd_mkdir)
                    _dom0U_local.mExecuteCmdLog(_cmd)
                else:
                    self.mPatchLogInfo(f"Plugin session is still active: {_plugin_log_file}")

                # Read plugins console log output.
                ret = self.mReadPluginScriptConsoleOut(aNode, _plugin_log_file, aNodeType)

        except Exception as e:
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()
            if _child_request_error_already_exists_in_db:
                ret = _rc
            else:
                _suggestion_msg = f"Exception in executing exadata plugins, Error details : {str(e)} on {aNodeType} target."
                if aNodeType == PATCH_DOM0: 
                    ret = EXACLOUD_PLUGIN_EXECUTION_DOM0_EXCEPTION_ERROR
                    _suggestion_msg = f"Exception in executing exadata plugins, Error details : {str(e)} on {aNodeType} target."
                elif aNodeType == PATCH_DOMU:
                    ret = EXACLOUD_PLUGIN_EXECUTION_DOMU_EXCEPTION_ERROR
                    _suggestion_msg = f"Exception in executing exadata plugins on {_domUCustomerName}, Error details : {str(e)} on {aNodeType} target."
                self.mAddError(ret, _suggestion_msg)

        finally:
            return ret

    def mCleanupPluginsfromTargetNode(self, aDom0UNode, aNodeType, aPluginsDir, aStage):
        """
        Cleanup DBNU plugins only at the end of patcmmgr run which is typically
        during post operation.i.e,
         1. By Default clean up only parents exacloud scripts in both pre and post stage
         2. Cleanup scripts from aPluginsDbnuDir(dbnu plugins) only when post stage
        """

        _connected_as_non_root_user = False
        _username = None
        _sudo_str = ''
        _node_type_name = ("DOMU" if (aNodeType == PATCH_DOMU) else "DOM0")

        self.mPatchLogInfo(f"Cleaning up plugins from {_node_type_name} '{aDom0UNode}'")
        try:
            _node = exaBoxNode(get_gcontext())
            # Connect as opc for domU if exist, otherwise, as root user
            _user_to_connect_with = self.mGetUserDetailsBasedOnDomUhostnameToRunPlugins(aDom0UNode)
            if aNodeType == PATCH_DOMU and _user_to_connect_with:
                _username = _user_to_connect_with

            if _username != 'root':
                _connected_as_non_root_user = True

            with connect_to_host(aDom0UNode, get_gcontext(), username=_username) as _dom0U:
                self.mPatchLogInfo(
                    f"_mCleanupPluginsfromTargetNode: Connected as {('opc' if (_connected_as_non_root_user) else 'root')} user to {_node_type_name} '{aDom0UNode}':")

                # Need to run as sudo for all nont root user
                if _connected_as_non_root_user:
                    _sudo_str = 'sudo '

                    # Cleanup plugins for all types
                for _plugin_type, _plugin_list in aPluginsDir.items():
                    _plugin_loc_dir = _plugin_list['plugin_loc_dir']
                    _plugin_remote_dir = _plugin_list['plugin_remote_dir']
                    # Clean up dbnu plugins only when post patch, usually there will be dom0.sh only,
                    # but deleting all parents scripts in case if those executed in future.
                    if _plugin_type == PLUGIN_DBNU and aStage == POST_PATCH:
                        # Remove dom0s.txt from remote node
                        _dom0U.mExecuteCmdLog(f"{_sudo_str} /bin/rm -rf {_plugin_remote_dir}")
                        if os.path.join(os.path.join(_plugin_remote_dir, "install.sh")):
                            _dom0U.mExecuteCmdLog(
                                f"{_sudo_str} /bin/rm -rf {os.path.join(os.path.join(os.path.dirname(_plugin_remote_dir)), 'install.sh')}")
                    elif not _plugin_type == PLUGIN_DBNU:
                        _dom0U.mExecuteCmdLog(f"{_sudo_str} /bin/rm -rf {_plugin_remote_dir}")

                self.mPatchLogInfo("Cleanup plugins done.")
        except Exception as e:
            self.mPatchLogError("Exception _mCleanupPluginsfromTargetNode: " + str(e))

    def mGetpluginsLog(self, aDom0UNode, aNodeType, aStage):
        """
        Get plugin logs from target node (where plugins run) to local ecra/exacloud node.
        """

        _connected_as_non_root_user = False
        _username = None
        _sudo_str = ''
        _node_type_name = ("DOMU" if (aNodeType == PATCH_DOMU) else "DOM0")

        # The same log file is used by exacloud and dbnu-plugin.sh plugins.
        # _PLUGINS_LOG_LOC = self.__plugins_log_path_on_launch_node
        _PLUGINS_LOG_LOC = self.mGetPluginsLogPathOnLaunchNode()
        self.mPatchLogInfo(f"Copying plugin logs to ecra node from {_node_type_name} '{aDom0UNode}'")
        try:
            _node = exaBoxNode(get_gcontext())
            # Connect as opc for domU if exist, otherwise, as root user
            _user_to_connect_with = self.mGetUserDetailsBasedOnDomUhostnameToRunPlugins(aDom0UNode)
            if aNodeType == PATCH_DOMU and _user_to_connect_with:
                _username = _user_to_connect_with

            if _username != 'root':
                _connected_as_non_root_user = True

            with connect_to_host(aDom0UNode, get_gcontext(), username=_username) as _dom0U_local:
                self.mPatchLogInfo(
                    f"mGetpluginsLog: Connected as {('opc' if (_connected_as_non_root_user) else 'root')} user to {_node_type_name} '{aDom0UNode}' to run plugins.")
                # Need to run as sudo for all non root user
                if _connected_as_non_root_user:
                    _sudo_str = 'sudo '

                if self.mIsExaSplice():
                    _plugin_log_file = f"plugin_{aStage}_{aDom0UNode}_exasplice_console.out"
                else:
                    _plugin_log_file = f"plugin_{aStage}_{aDom0UNode}_console.out"
                if aNodeType == PATCH_DOMU and _connected_as_non_root_user:
                    # Need to access plugin log as opc user to copy to ecra node
                    _cmd = _sudo_str + "cp " + os.path.join(_PLUGINS_LOG_LOC, _plugin_log_file) + " " + os.path.join('/tmp',
                                                                                                                    _plugin_log_file)
                    _dom0U_local.mExecuteCmdLog(_cmd)
                    # As opc user is used to copy the plugin log file, changing ownership to opc
                    _cmd = _sudo_str + f"chown opc:opc {os.path.join('/tmp', _plugin_log_file)}"
                    _dom0U_local.mExecuteCmdLog(_cmd)
                    self.mPatchLogInfo(
                        f"Downloading plugin log from {_node_type_name} '{aDom0UNode}'. Location : {os.path.join('/tmp', _plugin_log_file)} to {os.path.join(self.mGetLogPath(), _plugin_log_file)}")
                    if _dom0U_local.mFileExists(os.path.join('/tmp', _plugin_log_file)):
                        _dom0U_local.mCopy2Local(os.path.join('/tmp', _plugin_log_file),
                                                os.path.join(self.mGetLogPath(), _plugin_log_file))
                else:
                    self.mPatchLogInfo(
                        f"Downloading plugin log from {_node_type_name}  '{aDom0UNode}'. Location : From {os.path.join(_PLUGINS_LOG_LOC, _plugin_log_file)} to {os.path.join(self.mGetLogPath(), _plugin_log_file)}")
                    if _dom0U_local.mFileExists(os.path.join(_PLUGINS_LOG_LOC, _plugin_log_file)):
                        _dom0U_local.mCopy2Local(os.path.join(_PLUGINS_LOG_LOC, _plugin_log_file),
                                                os.path.join(self.mGetLogPath(), _plugin_log_file))

                self.mPatchLogInfo(f"Get plugin logs from '{aDom0UNode}' completed.")
        except Exception as e:
            self.mPatchLogError("Exception Copying plugin logs: " + str(e))

    def mReadPluginScriptConsoleOut(self, aNode, aPluginLogPathLaunchNode, aNodeType):
        """
         Here we connect to the target node and try to check for progress of plugin
         scripts reading Console out file. It returns:

             PATCH_SUCCESS_EXIT_CODE  --> when plugins run ends with success
             Hexadecimal Error Code other than PATCH_SUCCESS_EXIT_CODE --> when the plugin run fails

          Since the plugin scripts are run in the background using nohup, the below section
          of code monitors the log file for completion and returns the exit status of the
          plugin script output.
        """

        _connected_as_non_root_user = False
        _username = None
        _sudo_str = ''
        _exit_code = PATCH_SUCCESS_EXIT_CODE
        _domUCustomerName = None
        _is_adb_cc_domu_plugin_execution = False

        try:
            self.mPatchLogInfo(
                f"Read plugin console from {aNodeType} node = {aNode} and log loc = {aPluginLogPathLaunchNode}")

            _current_time_in_sec = 0
            # For ADB CC domu plugin, plugin console time out is set to 60 mins and for the other cases it is 23hrs
            _plugin_console_wait_time = self.mGetExadataPatchmgrConsoleReadTimeoutSec()

            _node = exaBoxNode(get_gcontext())
            _user_to_connect_with = self.mGetUserDetailsBasedOnDomUhostnameToRunPlugins(aNode)
            if aNodeType == PATCH_DOMU and _user_to_connect_with:
                _username = _user_to_connect_with

                self.mPatchLogInfo(
                    f"mReadPluginScriptConsoleOut: Connecting as {_username} user to '{aNodeType}' '{aNode}' to run plugins.")
                if _username != 'root':
                    _connected_as_non_root_user = True
            else:
                self.mPatchLogInfo(
                    f"mReadPluginScriptConsoleOut: Connecting as root user to '{aNodeType}' '{aNode}' to run plugins")
            with connect_to_host(aNode, get_gcontext(), username=_username) as _node:
                PLUGIN_READ_SLEEP_IN_SECONDS = 3
                _plugin_output_read = True


                # Need to run as sudo for all non-root user
                if _connected_as_non_root_user:
                    _sudo_str = 'sudo '

                '''
                Dom0
                ----
                Grep plugin console cmd = grep "Exit status:" /EXAVMIMAGES/dbserver.patch.zip_exadata
                _ovs_21.2.15.0.0.220816_Linux-x86-64.zip/dbserver_patch_220928/plugins_log_5ab93e25-cd5c
                -4491-a023-840b3b80df3a/plugin_pre_patch_scaqag01adm05.us.oracle.com_console.out
                Exit status:0

                DomU
                ----
                Grep plugin console cmd = sudo grep "Exit status:" /EXAVMIMAGES/dbserver.patch.zip_
                exadata_ovs_21.2.15.0.0.220816_Linux-x86-64.zip/dbserver_patch_220928/plugins_log_5
                ab93e25-cd5c-4491-a023-840b3b80df3a/plugin_pre_patch_scaqag01dv0505m.us.oracle.com_console.out
                2022-11-04 06:48:05-0700 - INFO - ExacloudPluginHandler - INFO - Exit status:0
                '''
                _plugin_exit_seek_cmd = _sudo_str + f'grep "Exit status:" {aPluginLogPathLaunchNode}'
                self.mPatchLogInfo(f"Grep plugin console cmd = {_plugin_exit_seek_cmd}")

                # For ADB CC VM OS patching, customer hostname is received so list is combined with both names for autonomous vm comparison
                _autonomous_vm_list = self.mGetAutonomousVMListWithCustomerHostnames() + self.mGetAutonomousVMList() 

                _autonomous_vm_set = {_automonoums_vm for _, _vmlist in _autonomous_vm_list for _automonoums_vm in _vmlist}
                # Check if the plugin type is domu and is an EXACC env with Autonomous vms and current node is an Autonomous VM
                _is_adb_cc_domu_plugin_execution = self.mGetPluginTypes() in ["domu"] and self.mIsExaCC() and _autonomous_vm_set and aNode in _autonomous_vm_set

                if _is_adb_cc_domu_plugin_execution:
                    self.mPatchLogInfo(f"ADB CC domu plugin execution is in progress")
                    _plugin_console_wait_time = self.mGetPluginConsoleReadCustomTimeoutSec()

                self.mPatchLogInfo(f"The plugin console read timeout is configured to {_plugin_console_wait_time} seconds")
                while _plugin_output_read and _current_time_in_sec < _plugin_console_wait_time:
                    _i, _o, _e = _node.mExecuteCmd(_plugin_exit_seek_cmd)
                    _exit_check = _node.mGetCmdExitStatus()
                    _out = _o.readlines()

                    if _exit_check == 0:
                        _plugin_output_read = False
                        for _output in _out:
                            self.mPatchLogInfo(f"{_output}")
                            '''
                            Sample log output below :

                            This script runs in nohup mode and hence i have added sleep commands here to
                            track and read console output.
                            ill end this script in another 20 seconds
                            existing script
                            [INFO] : [Custom Plugin Message] : Custom plugin script run successfully.
                            Exit status:0

                            '''
                            _pluginexists = True
                            _domUCustomerName = self.mGetDomUCustomerNameforDomuNatHostName(aNode)
                            if "Exit status:0" in _output:
                                self.mPatchLogInfo(f"Exacloud plugins on {aNodeType} '{aNode}' completed successfully")
                                return _exit_code
                            elif "Exit status:2" in _output:
                                _exit_code = EXACLOUD_PLUGIN_MISSING_CUSTOM_PLUGIN_SCRIPT
                                _pluginexists = False
                            else:
                                if (aNodeType == PATCH_DOM0):
                                    _exit_code = EXACLOUD_DOM0_PLUGIN_EXECUTION_FAILED
                                elif (aNodeType == PATCH_DOMU):
                                    _exit_code = EXACLOUD_CUSTOM_PLUGIN_SCRIPT_EXECUTION_FAILED
                                    self.mPatchLogInfo(f"CustomerName Fetched for Domu {aNode} during Domu plugin execution failure is {_domUCustomerName}")

                            _withCustomerHostname = ""
                            if _domUCustomerName:
                                _withCustomerHostname = f"with CustomerHostName {_domUCustomerName}"
                                    
                            if _pluginexists is True:
                                _suggestion_msg = f"Execution of plugin script for {aNodeType} failed on node {aNode} {_withCustomerHostname}. Plugin console log path is {aPluginLogPathLaunchNode}. \
                                                     Correct the plugin script and re-run the {aNodeType} patch operation."
                            else:
                                _suggestion_msg = f"Please review {aPluginLogPathLaunchNode} for missing file information on {aNode} {_withCustomerHostname}. Stage plugin script and rerun patching."

                            self.mAddError(_exit_code, _suggestion_msg)
                        return _exit_code
                    sleep(3)
                    # We are incrementing the counter by 3 as we are
                    # putting the current thread in sleep mode every
                    # 3 seconds unit it exits.
                    _current_time_in_sec += PLUGIN_READ_SLEEP_IN_SECONDS

        except Exception as e:
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()
            if _child_request_error_already_exists_in_db:
                _exit_code = _rc
            else:
                if aNodeType == PATCH_DOM0:
                    _exit_code = EXACLOUD_PLUGIN_CONSOLE_LOG_READ_DOM0_EXCEPTION_ERROR
                    _suggestion_msg = f"Exception in reading plugin console log, Error details : {str(e)} on {aNodeType} target."
                elif aNodeType == PATCH_DOMU:
                    _exit_code = EXACLOUD_PLUGIN_CONSOLE_LOG_READ_DOMU_EXCEPTION_ERROR
                    _suggestion_msg = f"Exception in reading plugin console log on {self.mGetDomUCustomerNameforDomuNatHostName(aNode)}, Error details : {str(e)} on {aNodeType} target."
                self.mAddError(_exit_code, _suggestion_msg)
        else:
            # This block will be executed if no exception is raised in the try block
            if _current_time_in_sec >= _plugin_console_wait_time:
                if aNodeType == PATCH_DOM0:
                    _exit_code = EXACLOUD_CUSTOM_PLUGIN_CONSOLE_READ_TIMEOUT_DOM0_ERROR
                elif aNodeType == PATCH_DOMU:
                    _exit_code = EXACLOUD_CUSTOM_PLUGIN_CONSOLE_READ_TIMEOUT_DOMU_ERROR
                _suggestion_msg = f"Timeout occurred after {_plugin_console_wait_time:d} seconds while reading plugin console from {aNodeType} node = {aNode} ."
                self.mAddError(_exit_code, _suggestion_msg)
        finally:
            return _exit_code

    def mTruncatedom0domuPlugins(self):
        """
        If non-rolling style is opted when dom0 upgrade requested, then dom0domu plugis is not
        feasible. So, ensure to trucate 'dom0domu' if specified by user.
        Return value:
           Nothing
        """

        self.mPatchLogInfo("Disabling running of dom0domu plugin while  patching Dom0 in non rolling style")
        self.mSetRunUserPluginsonDom0sdomuNode(False)
        self.mSetRunUserPluginsonDom0sdomuInCaseOfPluginMetadata(False)
        self.mPatchLogInfo(f"RunUserPluginsonDom0sdomuNode  value is: {self.mGetRunUserPluginsonDom0sdomuNode()}")

        _truncated_flag = False
        self.mPatchLogWarn(
            f"Removing plugin dom0domu from plugin list {self.__plugin_types} if non-rolling style is selected for dom0 upgrade.")
        if 'dom0+dom0domu' in self.__plugin_types:
            self.__plugin_types = self.__plugin_types.replace("+dom0domu", "")
            _truncated_flag = True
        elif 'dom0domu+dom0' in self.__plugin_types:
            self.__plugin_types = self.__plugin_types.replace("dom0domu+", "")
            _truncated_flag = True
        elif 'dom0domu' in self.__plugin_types:
            self.__plugin_types = self.__plugin_types.replace("dom0domu", "")
            _truncated_flag = True

        if _truncated_flag:
            self.mPatchLogWarn(f"The plugin type dom0domu is truncated: {self.__plugin_types}")
        else:
            self.mPatchLogInfo("The plugin type dom0domu is not truncated")


    '''
    mCheckConnectivityPluginScript - it will check for domU connectivity and if it is the case,
                                     if custom plugin script is present
    '''
    def mCheckConnectivityPluginScript(self, aDomu, aUserHostname, aTypePlugin, aCheckScript=False):
        _node = exaBoxNode(get_gcontext())
        _ret = PATCH_SUCCESS_EXIT_CODE
        _user_to_connect_with = None
        # calling mIsConnectable to avoid hangs in case of network issues
        # it also catches exceptions in case of non existent user or any other exception
        _user_to_connect_with = self.mGetUserDetailsBasedOnDomUhostnameToRunPlugins(aDomu)
        if not _user_to_connect_with:
            _ret = PATCHING_CONNECT_FAILED
            _suggestion_msg = f"Exacloud plugin on domu {aUserHostname} ({aDomu}) will not be called due to connectivity issue"
            self.mPatchLogError(_suggestion_msg)
            self.mAddError(_ret, _suggestion_msg)
            return _ret
        # check for custom plugin script
        if aCheckScript:
            # check if custom script is present
            try:
                _node.mConnect(aHost=aDomu)
                if aTypePlugin == "dom0domu":
                    _pluginScript = CUST_PLUGIN_DOM0_DOMU
                else:
                    _pluginScript = CUST_PLUGIN_DOMU
                if not _node.mFileExists(_pluginScript):
                    _ret = EXACLOUD_PLUGIN_MISSING_CUSTOM_PLUGIN_SCRIPT
                    _suggestion_msg = f"Plugin {aTypePlugin} enabled but {_pluginScript} is not present on {aUserHostname} ({aDomu})"
                    self.mPatchLogError(_suggestion_msg)
                    self.mAddError(_ret, _suggestion_msg)
            except Exception as e:
                _suggestion_msg = f'Error occurred while accessing domu {aUserHostname} ({aDomu}). Error : {str(e)}.'
                _ret = PATCHING_CONNECT_FAILED
                self.mPatchLogError(_suggestion_msg)
                self.mAddError(_ret, _suggestion_msg)
            finally:
                if _node.mIsConnected():
                    _node.mDisconnect()
        return _ret
