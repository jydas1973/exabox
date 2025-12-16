#
# $Header: ecs/exacloud/exabox/infrapatching/handlers/pluginHandler/exacloudpluginhandler.py /main/33 2025/11/06 06:48:23 araghave Exp $
#
# exacloudpluginhandler.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
#
#    NAME
#      exacloudpluginhandler.py - This module contains methods to run exacloud plugin on Dom0 and Domu targets.
#
#    DESCRIPTION
#      This module contains methods to run exacloud plugin on Dom0 and Domu targets.
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    sdevasek    10/10/25 - ENH 38437135 - IMPLEMENT ADDITION OF SCRIPTNAME
#                           SCRIPTBUNLDENAME AND SCRIPTBUNDLEHASH ATTRIBUTES
#                           TO ECRA REGISTERED PLUGINS METADATA REGISTRATION
#    araghave    08/13/25 - Enh 38228272 - EXACC GEN2 | PATCHING | SWITCH BACK
#                           TO OPC USER FOR ALL INFRA PATCH USE CASES IN CASE
#                           OF ROOT KEY INJECTION FAILS
#    araghave    03/04/25 - Bug 37417431 - EXACS | DOMU | UNWANTED SSH
#                           CONNECTION FROM 169.254.200.1 LOCKING OPC USER
#    araghave    02/04/25 - Enh 34479463 - PROVIDE EXACLOUD REGISTRATION AND
#                           PLUGIN SUPPORT FOR CELLS
#    araghave    08/27/24 - Enh 36829406 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE CORE, PLUGIN AND TASKHANDLER
#                           FILES
#    araghave    07/15/24 - Enh 36830077 - CLEANUP KSPLICE CODE FROM
#                           INFRAPATCHING FILES
#    araghave    06/13/24 - Enh 36522596 - REVIEW PRE-CHECK/PATCHING/ROLLBACK
#                           LOGS AND CLEAN-UP
#    diguma      06/06/24 - Enh 36691192 - IN CASE OF ADBS, DURING DOM0/KVM
#                           HOST INFRA PATCHING RETRY EXECUTE DOM0DOMU PLUGIN
#    araghave    06/13/24 - Enh 36522596 - REVIEW PRE-CHECK/PATCHING/ROLLBACK
#                           LOGS AND CLEAN-UP
#    araghave    05/17/24 - Enh 36293209 - USE PLUGIN FILES FROM THE NEW
#                           EXADATA VERSION PLUGIN LOCATION
#    araghave    03/13/24 - Enh 36270822 - EXECUTION OF EXACLOUD PLUGINS USING
#                           INFRA PATCHING PLUGIN METADATA
#    araghave    02/28/24 - Enh 36295801 - IMPLEMENT ONEOFFV2 PLUGIN EXACLOUD
#                           CHANGES
#    ririgoye    08/23/23 - Bug 35616435 - Fix redundant/multiple instances of
#                           mConnect
#    sdevasek    07/08/23 - BUG 35555704 - EXACS:BB:INFRAPATCHING:DOM0 PATCH
#                           FAILED AS VM IS NOT ACCESSIBLE
#    araghave    05/11/23 - Enh 35353733 - REFACTOR AND USE NEW SSH CONNECTIVITY
#                           VALIDATION METHODS FROM CLUAPATCHHEALTHCHECK.PY
#    diguma      04/23/23 - Bug 35130530 - adding user hostname in error msg
#                           when executing domu plugins
#    jyotdas     04/17/23 - ENH 35106082 - By default run dom0domu plugin on
#                           autonomous vms
#    antamil     02/02/23 - ENH 34893583 - ENABLE PLUGIN SUPPORT FOR
#                           MONTHLY PATCHING
#    sdevasek    10/31/22 - Bug 34750055 - DISABLE PING CHECK DURING DOM0DOMU
#                           PLUGIN EXECUTION TO SUPPORT BACKWARD COMPATIBILITY
#    araghave    10/20/22 - BUG 34722405 - DURING DOM0 UPGRADE, UNABLE TO COPY
#                           DOM0DOMU PLUGIN TO DOM0'S DOMU
#    araghave    10/04/22 - Bug 34665994 - ADBS DOM0 PATCHING FAILED COPYING
#                           DOM0DOMU PLUGIN WHEN DOM0DOMU PLUGIN ENABLED
#    araghave    06/06/22 - Enh 34239188 - ADD ADDITIONAL, GRANULAR ERROR
#                           CODES FOR PLUG-IN FAILURES
#    araghave    06/16/22 - Enh 34138779 - RUN EXACLOUD PLUGIN ON ALL DOMUS
#                           WHICH ARE PROVISIONED AS PART OF MVM ENV
#    nmallego    04/18/22 - Bug33689792 - Skip dummy VM for exacloud plugins
#    araghave    03/08/22 - ER33689675 - Move MOS NOTE 2829056.1 messages to
#                           ecra_error_catalog.json
#    nmallego    01/12/22 - Bug33689655 - UPDATE DOMU FAIL AND SHOW ERROR
#                           MESSAGE WITH MOS NOTE 2829056.1
#    sdevasek    12/23/21 - Bug 33689708 - INFRA PATCHING CODE IMPROVEMENT
#                           WITH PLUGIN MESSAGE AND ECRACLI HELP
#    araghave    12/08/21 - Enh 33598784 - MOVE ALL INFRA PATCHING ERROR CODES
#                           FROM ERROR.PY TO INFRAPATCHERROR.PY
#    jyotdas     05/14/21 - ENH 32866741 - domu plugin error messages should
#                           have error action as fail_and_show
#    araghave    03/15/21 - Enh 32415170 - Introduce specific Error Codes for
#                           Dom0 and DomU Exacloud Plugins
#    araghave    12/08/20 - Enh 31984849 - RETURN ERROR CODES TO DBCP FROM DOMU
#                           AND PLUGINS
#    nmallego    08/28/20 - Refactor infra patching code
#    nmallego    08/28/20 - Creation
#

import socket
import traceback
from time import sleep
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.infrapatching.handlers.pluginHandler.pluginhandler import PluginHandler
from exabox.infrapatching.utils.utility import mRegisterInfraPatchingHandlers
from exabox.infrapatching.utils.constants import *
from exabox.infrapatching.core.infrapatcherror import *
from exabox.utils.node import connect_to_host
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure
from exabox.infrapatching.utils.utility import *
from exabox.infrapatching.utils.utility import mGetInfraPatchingConfigParam

sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))

class ExacloudPluginHandler(PluginHandler):

    def __init__(self, *initial_data, **kwargs):
        super(ExacloudPluginHandler, self).__init__(*initial_data, **kwargs)
        self.mPatchLogInfo("ExacloudPluginHandler")
        mRegisterInfraPatchingHandlers(INFRA_PATCHING_HANDLERS, [PLUGIN_EXACLOUD], self)
        #Initialize all variables required for plugins to run
        self.initializePluginMetadata()

    # validate the existance of the plugin scripts
    def mValidatePluginstoExecute(self, aNodeType, aNode):
        _plugins_base_dir = f"PatchPayloads/{self.mGetTargetVersion()}/exadataPrePostPlugins"
        if not os.path.exists(_plugins_base_dir):
            _plugins_base_dir = "exadataPrePostPlugins"
        if os.path.isdir(_plugins_base_dir) and os.listdir(_plugins_base_dir):
            _plugins_exacloud_dir = os.path.join(_plugins_base_dir, "exacloud_plugins")
        else:
            _suggestion_msg = "Plugins directory not found at exacloud layer"
            ret = EXACLOUD_PLUGINS_DIRECTORY_MISSING
            self.mAddError(ret, _suggestion_msg)
            return ret, None

        _plugins_to_run = {"exacloud_plugins": {'plugin_loc_dir': _plugins_exacloud_dir,
                                                'plugin_remote_dir': '/opt/exacloud/customs/plugins/exacloud_plugins/'}
                           }

        _flag_plugins_exist = False
        ret = PATCH_SUCCESS_EXIT_CODE

        try:
            for _plugin_type, _plugin_list in _plugins_to_run.items():
                if os.path.isdir(_plugin_list['plugin_loc_dir']) and os.listdir(_plugin_list['plugin_loc_dir']):
                    _flag_plugins_exist = True

            if not _flag_plugins_exist:
                self.mPatchLogError(
                    f"No exadata parent plugins to run from {('DomU' if (aNodeType == PATCH_DOMU) else 'DOM0')} '{aNode}'. Please ensure to have parents plugins script. Plugins location: '{_plugins_to_run}'")
                _suggestion_msg = f"No exadata parent plugins to run from {('DomU' if (aNodeType == PATCH_DOMU) else 'DOM0')} '{(aNode if (aNodeType == PATCH_DOM0) else self.mGetDomUCustomerNameforDomuNatHostName(aNode))}'. Please ensure to have parent plugins script. Plugins location: '{_plugins_to_run}'"
                ret = EXACLOUD_PARENT_PLUGINS_MISSING
                self.mAddError(ret, _suggestion_msg)
                return ret
        except Exception as e:
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()
            if _child_request_error_already_exists_in_db:
                ret = _rc
            else:
                if aNodeType == PATCH_DOM0:
                    _suggestion_msg = f"Exception: Validating presence of plugins, Error details : {str(e)} on {aNodeType} target."
                    ret = EXACLOUD_PLUGIN_MISSING_DOM0_EXCEPTION_ERROR
                elif aNodeType == PATCH_DOMU:
                    _suggestion_msg = f"Exception: Validating presence of plugins on {self.mGetDomUCustomerNameforDomuNatHostName(aNode)}, Error details : {str(e)} on {aNodeType} target."
                    ret = EXACLOUD_PLUGIN_MISSING_DOMU_EXCEPTION_ERROR
                self.mAddError(ret, _suggestion_msg)
        return ret, _plugins_to_run

    #Currently this does on each node as aNode is passed as launch Node is passed as an argument from the main call ?
    #same as #_mPrePostPluginsRun method
    def mApply(self, aNode, aNodeType, aStage, aRollback=False):
        """
          -> Returns PATCH_SUCCESS_EXIT_CODE if all checks pass.
          -> Return non PATCH_SUCCESS_EXIT_CODE if any of the checks failed.

          This method helps to:
          1) Do nothing if there are no plugins to run
          2) Copy exacloud pre-post scripts to dom0/domU and can be used before and after patchmgr run.
             Args passed:
             aNode => Node on which plugins needs to run
             aNodeType => type of node (dom0/domU)
             aStage => Patch phase - pre or post stage
             aRollback => The operation type is rollback or not
        """

        # Set exacloud plugin locations
        _dom0U_list = []

        self.mPatchLogInfo(
            f"\nRunning '{('PRE' if (aStage == PRE_PATCH) else 'POST')}' Exacloud plugins during '{('ROLLBACK' if (aRollback) else 'UPGRADE')}' on '{('DomU' if (aNodeType == PATCH_DOMU) else 'Dom0')}' : '{aNode}'")

        '''
          Bug33689792 - No need to operate exacloud plugin on dummy VMs,
          especially, dom0 which is not part of provision cluster and in
          that case, VMs/domUs won't be created.

          on MVM environments, we will need to traverse through
          multiple DomUs running on the current Dom0.

          SSH validations are already in place for the current target patch type.
          Since the exacloud plugin type is Dom0DomU here, ssh validations need
          to be performed separately for all the DomUs running on the current Dom0
          target host as the validation is not covered under the existing ssh validations.
        '''
        ret, _plugins_to_run = self.mValidatePluginstoExecute(aNodeType, aNode)
        if ret != PATCH_SUCCESS_EXIT_CODE:
            return ret

        _remote_plugin_dir_exacloud = _plugins_to_run['exacloud_plugins']['plugin_remote_dir']
        _pre_post_str = None
        try:
            '''
             1. Copy only exacloud plugins to dom0 and domu when
                pluginTypes=dom0 or pluginTypes=domu.
            '''
            if (aNodeType == PATCH_DOM0):
                if self.mGetRunUserPluginsonDom0Node():
                    ret = self.mCopyPluginsToTargetNode(aNode, aNodeType, _plugins_to_run)
                    if ret != PATCH_SUCCESS_EXIT_CODE:
                        return ret
                    # 3. Prepare required script to be executed from infra patching
                    if self.mIsExaSplice():
                        _pre_post_str = "dom0_exasplice.sh"
                    else:
                        _pre_post_str = "dom0.sh"
            elif (aNodeType == PATCH_DOMU and self.mGetRunUserPluginsonDomuNode()):
                ret = self.mCopyPluginsToTargetNode(aNode, aNodeType, _plugins_to_run)
                if ret != PATCH_SUCCESS_EXIT_CODE:
                    return ret
                # 3. Prepare required script to be executed from infra patching
                _pre_post_str = "domu.sh"
        except Exception as e:
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()
            if _child_request_error_already_exists_in_db:
                ret = _rc
            else:
                if aNodeType == PATCH_DOM0:
                    ret = EXACLOUD_PLUGIN_APPLY_DOM0_EXCEPTION_ERROR
                    _suggestion_msg = f"Exception: Exacloud apply failed, Error details : {str(e)} on {aNodeType} target."
                elif aNodeType == PATCH_DOMU:
                    ret = EXACLOUD_PLUGIN_APPLY_DOMU_EXCEPTION_ERROR
                    _suggestion_msg = f"Exception: Exacloud apply failed on {self.mGetDomUCustomerNameforDomuNatHostName(aNode)}, Error details : {str(e)} on {aNodeType} target."
                self.mAddError(ret, _suggestion_msg)
            return ret


        _plugin_log_file = ''
        _plugin_log_file_local_path = ''
        try:
            '''
             2. Run Exacloud Plugins on respective dom0 and domu nodes during
                pluginTypes=dom0 or pluginTypes=domu
            '''
            # Run plugins for domu if user requested
            if aNodeType == PATCH_DOMU and self.mGetRunUserPluginsonDomuNode():
                ret = self.mExecutePrePostExacloudPlugins(aNode, PATCH_DOMU, _remote_plugin_dir_exacloud, _pre_post_str,
                                                          aStage, aRollback)

                '''
                 Copy exacloud plugins to local node only
                 in case of plugin failure.
                '''
                self.mGetpluginsLog(aNode, PATCH_DOMU, aStage)

                # Cleanup plugins from required nodes
                self.mCleanupPluginsfromTargetNode(aNode, PATCH_DOMU, _plugins_to_run, aStage)

            # Run plugins for dom0 if user requested
            elif aNodeType == PATCH_DOM0 and self.mGetRunUserPluginsonDom0Node():
                ret = self.mExecutePrePostExacloudPlugins(aNode, PATCH_DOM0, _remote_plugin_dir_exacloud, _pre_post_str,
                                                          aStage, aRollback)

                '''
                 Copy exacloud plugins to local node only
                 in case of plugin failure.
                '''
                self.mGetpluginsLog(aNode, PATCH_DOM0, aStage)

                # Cleanup plugins from required nodes
                self.mCleanupPluginsfromTargetNode(aNode, PATCH_DOM0, _plugins_to_run, aStage)

            if ret != PATCH_SUCCESS_EXIT_CODE:
                return ret

        except Exception as e:
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()
            if _child_request_error_already_exists_in_db:
                ret = _rc
            else:
                if aNodeType == PATCH_DOM0:
                    ret = EXACLOUD_PLUGIN_GENERIC_DOM0_EXCEPTION_ERROR
                    _suggestion_msg = f"Exception: Executing plugins, Error details : {str(e)} on {aNodeType} target."
                elif aNodeType == PATCH_DOMU:
                    ret = EXACLOUD_PLUGIN_GENERIC_DOMU_EXCEPTION_ERROR
                    _suggestion_msg = f"Exception: Executing plugins on {self.mGetDomUCustomerNameforDomuNatHostName(aNode)}, Error details : {str(e)} on {aNodeType} target."
                self.mAddError(ret, _suggestion_msg)
                return ret

        return self.mExecuteDom0DomU(aNode, aNodeType, aStage, aRollback)

    def mExecuteDom0DomU(self, aNode, aNodeType, aStage, aRollback=False, aDom0DomUList=None):

        # validate plugin scripts
        ret, _plugins_to_run = self.mValidatePluginstoExecute(aNodeType, aNode)
        if ret != PATCH_SUCCESS_EXIT_CODE:
            return ret

        _remote_plugin_dir_exacloud = _plugins_to_run['exacloud_plugins']['plugin_remote_dir']
        _pre_post_dom0_domU_str = ''
        try:
            '''
              1. Copy only exacloud plugins to domu when
                 pluginTypes=dom0domu and during dom0 patching
            '''
            _dom0U_list = None
            if aDom0DomUList is not None:
                _dom0U_list = aDom0DomUList
            else:
                if self.isADBDImplicitPluginEnabled() == True:
                    _dom0U_list = self.mGetAutonomousVMList()
                    self.mPatchLogInfo(
                        f"AutonomousVM list on which implicit dom0domu plugin will be copied are {str(_dom0U_list)} ")
                else:
                    _dom0U_list = self.mReturnPatchingDom0DomUListFromEcra()
                    self.mPatchLogInfo("AutonomousVM list is none, explicit exacloud dom0domu plugin will be copied to all domu")

            if (aNodeType == PATCH_DOM0) and self.mGetRunUserPluginsonDom0sdomuNode():
                # Copy plugins to domu of it's own dom0, like in FA, ADW, ATP env.
                for _dom0_hostname, _dom0s_domU in _dom0U_list:
                    # if first node in a pair is dom0 then copy corresponding domU
                    if aNode == _dom0_hostname:
                        self.mPatchLogInfo(
                            f"Copying Exacloud plugins to Dom0's : {str(_dom0_hostname)} DomU : {str(_dom0s_domU)}")

                        # SSH validation in parallel.
                        try:
                            self.mPatchLogInfo(
                                "Connectivity between Exacloud node and Guest VMs are expected to be enabled during PluginType=Dom0DomU exacloud plugin run. Verifying ssh connectivity with opc user.")
                            self.mGetCluPatchCheck().mVerifyExacloudExadataHostSshConnectivity(_dom0s_domU, aSshUser='opc')
                        except Exception as e:
                            self.mPatchLogInfo(
                                "Connectivity between Exacloud node and Guest VMs failed with opc user so trying with root user.")
                            self.mGetCluPatchCheck().mVerifyExacloudExadataHostSshConnectivity(_dom0s_domU)

                        for _domUs in _dom0s_domU:
                            if _domUs.split(".")[0].find(DUMMYDOMU) > -1:
                                self.mPatchLogWarn(
                                    f"DOM0 '{aNode}' is not having guest vm since it is not part of any node subset group. Skipping exacloud copy plugin on dummy VM = '{_domUs}'")
                                continue

                            ret = self.mCopyPluginsToTargetNode(_domUs, PATCH_DOMU, _plugins_to_run)
                            if ret != PATCH_SUCCESS_EXIT_CODE:
                                return ret

                # Get pre post pattern for dom0_domu, and user require this on adw/atp/fa env to run
                _pre_post_dom0_domU_str = "dom0_domu.sh"
        except Exception as e:
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()
            if _child_request_error_already_exists_in_db:
                ret = _rc
            else:
                _suggestion_msg = f"Exception: Exacloud apply failed, Error details : {str(e)} on {aNodeType} target."
                if aNodeType == PATCH_DOM0:
                    ret = EXACLOUD_PLUGIN_APPLY_DOM0_EXCEPTION_ERROR
                elif aNodeType == PATCH_DOMU:
                    ret = EXACLOUD_PLUGIN_APPLY_DOMU_EXCEPTION_ERROR
                self.mAddError(ret, _suggestion_msg)
            return ret

        _plugin_log_file = ''
        _plugin_log_file_local_path = ''
        _userHostname = None
        try:
            '''
             2. Run Exacloud Plugins on respective domu nodes during
                pluginTypes=dom0domu and dom0 patching
            '''
            _dom0U_list = None
            if aDom0DomUList:
                _dom0U_list = aDom0DomUList
            elif self.isADBDImplicitPluginEnabled() == True:
                _dom0U_list = self.mGetAutonomousVMList()
                self.mPatchLogInfo(
                    f"AutonomousVM list on which implicit dom0domu plugin will be run are {str(_dom0U_list)} ")
            else:
                _dom0U_list = self.mReturnPatchingDom0DomUListFromEcra()
                self.mPatchLogInfo("AutonomousVM list is none, explicit exacloud dom0domu plugin will be executed on all domu")

            # Run plugins on domu (if anything exist) when upgrading dom0 and only when
            # user asked to run dom0's domu node
            if aNodeType == PATCH_DOM0 and self.mGetRunUserPluginsonDom0sdomuNode():
                for _dom0_hostname, _dom0s_domU in _dom0U_list:
                    # first node in a pair is dom0 and copy corresponding domU
                    if aNode == _dom0_hostname:
                        self.mPatchLogInfo(
                            f"Exacloud Plugin : Executing Dom0's : {str(_dom0_hostname)} DomU : {str(_dom0s_domU)} scripts:")
                        '''
                          Bug33689792 - No need to operate exacloud plugin on dummy VMs,
                          especially, dom0 which is not part of provision cluster and in
                          that case, VMs/domUs won't be created.

                          on MVM environments, we will need to traverse through
                          multiple DomUs running on the current Dom0.
                        '''
                        for _domUs in _dom0s_domU:
                            if _domUs.split(".")[0].find(DUMMYDOMU) > -1:
                                self.mPatchLogWarn(
                                    f"DOM0 '{aNode}' is not having VMs since it is not part of any node subset group. Skipping exacloud plugin execution on dummy VM = '{_domUs}'")
                                continue
                            _userHostname = self.mGetDomUCustomerNameforDomuNatHostName(_domUs)
                            ret = self.mExecutePrePostExacloudPlugins(_domUs, PATCH_DOMU, _remote_plugin_dir_exacloud, _pre_post_dom0_domU_str, aStage, aRollback)
                            '''
                             Copy exacloud plugins to local node only
                             in case of plugin failure.
                            '''
                            self.mGetpluginsLog(_domUs, PATCH_DOMU, aStage)

                            # Cleanup plugins from required nodes
                            self.mCleanupPluginsfromTargetNode(_domUs, PATCH_DOMU, _plugins_to_run, aStage)
                            _userHostname = None
                            if ret != PATCH_SUCCESS_EXIT_CODE:
                                self.mPatchLogError(
                                    f"Dom0DomU plugins failed on DomU : '{self.mGetDomUCustomerNameforDomuNatHostName(_domUs)}' ({_domUs}) during {_dom0_hostname} Dom0 patching.")
                                return ret

            self.mPatchLogInfo(
                f"\nCompleted '{('PRE' if (aStage == PRE_PATCH) else 'POST')}' plugins during '{('ROLLBACK' if (aRollback) else 'UPGRADE')}' on '{('DomU' if (aNodeType == PATCH_DOMU) else 'Dom0')}' : '{aNode}'\n")

        except Exception as e:
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()
            if _child_request_error_already_exists_in_db:
                ret = _rc
            else:
                if _userHostname:
                    _suggestion_msg = f"Exception: Executing plugins on {_userHostname}, Error details : {str(e)} on {aNodeType} target."
                else:
                    _suggestion_msg = f"Exception: Executing plugins, Error details : {str(e)} on {aNodeType} target."
                ret = EXACLOUD_PLUGIN_GENERIC_DOMU_EXCEPTION_ERROR
                self.mAddError(ret, _suggestion_msg)

        return ret

    def mExecuteDom0DomuPlugininADBSforCompletedNodes(self, _dom0, _pluginEnabled):
        # The dom0 being passed is the one in the discarded node list, so it is already 
        # upgraded and it is the only node passed by CP
        _ret = PATCH_SUCCESS_EXIT_CODE
        if self.mGetADBS().upper() == "TRUE" and self.mGetTask() == TASK_PATCH and _pluginEnabled:
            self.mPatchLogInfo(f"ADBS env. Node {_dom0} is already upgraded, running pre dom0domu plugin.")
            # build the list to be passed with the dom0 and respective domU's
            _completeList = self.mReturnPatchingDom0DomUListFromEcra()
            _singleList = []
            for _dom0_hostname, _dom0s_domU in _completeList:
                if _dom0 == _dom0_hostname:
                    _singleList.append((_dom0_hostname, _dom0s_domU))
                    break
            self.mPatchLogInfo(f"Calling pre plugin on node {_dom0}.")
            _ret = self.mExecuteDom0DomU(_dom0, PATCH_DOM0, PRE_PATCH, False, aDom0DomUList=_singleList)
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogInfo("Failed to execute pre plugin on ADBS env");
            else:
                self.mPatchLogInfo(f"Calling post plugin on node {_dom0}.")
                _ret = self.mExecuteDom0DomU(_dom0, PATCH_DOM0, POST_PATCH, False, aDom0DomUList=_singleList)
        else:
            self.mPatchLogInfo("Not ADBS or not patching or dom0domu plugin not enabled")
        return _ret

    def mCopyPluginsToTargetNode(self, aDom0UNode, aNodeType, aPluginsToCopy):
        """
                Check existence of plugins on local node and copy them to target node,
                if it's dom0 and aAdwAtpFA Env, then even copy to dom0's domU.
                Return:
                    PATCH_SUCCESS_EXIT_CODE  - if copy success
                    Any other error code other than PATCH_SUCCESS_EXIT_CODE - if copy is failed
                """

        _connected_as_non_root_user = False
        ret = PATCH_SUCCESS_EXIT_CODE
        _sudo_str = ''
        _node_type_name = ("DOMU" if (aNodeType == PATCH_DOMU) else "DOM0")

        try:
            self.mPatchLogInfo(f"Copying plugins to {_node_type_name} '{aDom0UNode}':")
            _node = exaBoxNode(get_gcontext())
            # Connect as opc for domU if exist, otherwise, as root user
            _user_to_connect_with = self.mGetUserDetailsBasedOnDomUhostnameToRunPlugins(aDom0UNode)
            if aNodeType == PATCH_DOMU and _user_to_connect_with:
                if _user_to_connect_with != 'root':
                    _connected_as_non_root_user = True
            with connect_to_host(aDom0UNode, get_gcontext(), username=_user_to_connect_with) as _dom0U:
                # Need to run as sudo for all non root user
                if _connected_as_non_root_user:
                    _sudo_str = 'sudo '

                # Copy all plugins to target node
                for _plugin_type, _plugin_list in aPluginsToCopy.items():
                    self.mPatchLogInfo(f"Copy {_plugin_type.upper()} to {_node_type_name} '{aDom0UNode}':")
                    _plugin_loc_dir = _plugin_list['plugin_loc_dir']
                    _plugin_remote_dir = _plugin_list['plugin_remote_dir']
                    if os.path.isdir(_plugin_loc_dir) and os.listdir(_plugin_loc_dir):
                        # Connect as opc for domU case if opc user exist
                        if aNodeType == PATCH_DOMU and _connected_as_non_root_user:
                            _dom0U.mExecuteCmdLog(_sudo_str + f"mkdir -p {_plugin_remote_dir}")
                            # Need write access for non root user
                            _dom0U.mExecuteCmdLog(_sudo_str + f"chmod 777 {_plugin_remote_dir}")
                        # as a root user for dom0/domU
                        else:
                            _dom0U.mExecuteCmdLog(f'mkdir -p {_plugin_remote_dir}')

                        for _entry_file in os.listdir(_plugin_loc_dir):
                            self.mPatchLogInfo(
                                f"Copy plugins: Source = {os.path.join(_plugin_loc_dir, _entry_file)}, Destination file = {os.path.join(_plugin_remote_dir, _entry_file)}")
                            # if listed entry is directory, then we skip it, since we expect
                            # all files in plugin directory itself.
                            if os.path.isdir(os.path.join(_plugin_loc_dir, _entry_file)):
                                self.mPatchLogInfo(
                                    f"The '{os.path.join(_plugin_loc_dir, _entry_file)}' is a directory and copying directories are skipped.")
                                continue
                            else:
                                '''
                                In case of mCleanupPluginsfromTargetNode fails to
                                purge plugin scripts, some "Permission denied" errors
                                could be observed in future executions. To avoid such scenarios,
                                files are checked if they exist and are purged before copying
                                plugin files again.
                                '''
                                if _dom0U.mFileExists(os.path.join(_plugin_remote_dir, _entry_file)):
                                    self.mPatchLogInfo(
                                        f"The '{(os.path.join(_plugin_remote_dir, _entry_file))}' file was found on {aDom0UNode} and is purged before re-copying a new copy of the file.")
                                    if aNodeType == PATCH_DOMU and _connected_as_non_root_user:
                                        _dom0U.mExecuteCmdLog(
                                            f" {_sudo_str} rm -f {os.path.join(_plugin_remote_dir, _entry_file)}")
                                    else:
                                        _dom0U.mExecuteCmdLog(f"rm -f {os.path.join(_plugin_remote_dir, _entry_file)}")

                                if os.path.exists(os.path.join(_plugin_loc_dir, _entry_file)):
                                    _dom0U.mCopyFile(os.path.join(_plugin_loc_dir, _entry_file),
                                                    os.path.join(_plugin_remote_dir, _entry_file))
                        _dom0U.mExecuteCmdLog(_sudo_str + f"chmod +x -R {_plugin_remote_dir}")
                    else:
                        self.mPatchLogInfo(f"No {_plugin_type.upper()} scripts to copy from '{_plugin_loc_dir}'")

        except Exception as e:
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()
            if _child_request_error_already_exists_in_db:
                ret = _rc
            else:
                if aNodeType == PATCH_DOM0:
                    ret = EXACLOUD_PLUGIN_COPY_DOM0_EXCEPTION_ERROR
                    _suggestion_msg = f"Exception in copying plugins, Error details : {str(e)} on {aNodeType} target."
                elif aNodeType == PATCH_DOMU:
                    ret = EXACLOUD_PLUGIN_COPY_DOMU_EXCEPTION_ERROR
                    _suggestion_msg = f"Exception in copying plugins to {self.mGetDomUCustomerNameforDomuNatHostName(aDom0UNode)}, Error details : {str(e)} on {aNodeType} target."
                self.mAddError(ret, _suggestion_msg)

        finally:
            return ret

    def mExacloudPluginMetadataExecutor(self, aNodeList, aStage):
        _ret = PATCH_SUCCESS_EXIT_CODE
        self.mPatchLogInfo(
            f"Executing Plugin metadata based exacloud plugins operation in {self.mGetOpStyle()} style")

        # By default Plugin Metadata based Exacloud plugins are executed in rolling fashion.
        self.mPatchLogInfo(
            f"List of nodes where plugin metadata based exacloud plugins will be run : {str(aNodeList)}.")
        self.mPatchLogInfo(
            f"Plugin metadata based exacloud plugin will be run as part of {str(aStage)} infra patch operation.")
        if self.mGetOpStyle() in OP_STYLE_ROLLING:
            _ret = self.mRunExacloudPluginV2inRolling(aNodeList, aStage)
        elif self.mGetOpStyle() in OP_STYLE_NON_ROLLING:
            _ret = self.mRunExacloudPluginV2inNonRolling(aNodeList, aStage)
        return _ret

    def mRunExacloudPluginV2inRolling(self, aNodeList, aStage):
        """
        This method executes Exacloud plugins
        in rolling fashion.
        :return: PATCH_SUCCESS_EXIT_CODE in case of successful patch execution
                or FailOnError flag was set to false
            else
                return error code as per error details returned
                from below execution flow.
        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        _rc = PATCH_SUCCESS_EXIT_CODE
        _plugin_type = None
        _stage = None

        self.mPatchLogInfo(
            f"Starting execution of Exacloud plugins in rolling fashion for nodes: {aNodeList} and stage: {aStage}")
        # Step 1. Copy Plugin metadata based exacloud plugins.
        for _node_name in aNodeList:
            for _exacloud_plugin_data in self.mGetPluginMetadata():
                _plugin_type = mGetPluginType(_exacloud_plugin_data)
                if (_plugin_type).lower() != "exacloud":
                    self.mPatchLogInfo(
                        f"Only exacloud plugins will be run, current Plugin target type is : {_plugin_type}")
                    continue

                _stage = mGetPhase(_exacloud_plugin_data)
                if (aStage).lower() != _stage.lower():
                    continue
                else:
                    self.mPatchLogInfo(
                        f"Current exacloud plugin scripts will be run with the following input : {json.dumps(_exacloud_plugin_data, indent=4)}")

                if mGetPluginTargetV2(_exacloud_plugin_data).lower() in [ "dom0", "cell" ] and str(mGetPluginTargetV2(_exacloud_plugin_data).lower()) in str(self.mGetTargetTypes()[0].lower()):

                    # Validate the script bundle on exacloud node only once for the first node
                    if _node_name == aNodeList[0]:
                        # Step1. Validate the script bundle
                        self.mPatchLogInfo(f"Validating exacloud plugin script bundle for node {_node_name}")
                        _rc = self.mValidateExacloudPluginScriptBundle(_exacloud_plugin_data)
                        if _rc != PATCH_SUCCESS_EXIT_CODE and mGetFailonError(_exacloud_plugin_data):
                            self.mAddError(_rc,"")
                    else:
                        # Assume validation is successful for subsequent nodes
                        _rc = PATCH_SUCCESS_EXIT_CODE

                    if _rc == PATCH_SUCCESS_EXIT_CODE:
                        # Step 2. Copy exacloud plugins.
                        self.mPatchLogInfo(f"Copying exacloud plugins to node {_node_name}")
                        _rc = self.mCopyPluginsToTargetNodesV2(_node_name, _exacloud_plugin_data)
                        if _rc == PATCH_SUCCESS_EXIT_CODE:
                            # Step 3. Run Exacloud plugin operation.
                            self.mPatchLogInfo(
                                f"Copy of exacloud plugins is successful. Executing exacloud plugin on node {_node_name}")
                            _rc = self.mExecuteMetadataExadataPlugins(_node_name, _exacloud_plugin_data)

                        # Step 4. Cleanup exacloud plugins and copy logs to exacloud
                        # irrespetive of plugin operation was successful or failed.
                        self.mPatchLogInfo(f"Cleaning up exacloud plugin on node {_node_name}")
                        self.mCleanupExacloudPluginV2Script(_node_name, _exacloud_plugin_data)
                else:
                    if self.mGetRunUserPluginsonDom0sdomuInCaseOfPluginMetadata() and mGetPluginTargetV2(_exacloud_plugin_data) == "dom0domu":
                        '''
                         Call dom0domu plugin flow in case of PluginTarget specified contains dom0domu.
                         dom0domu plugins are supported only in case of rolling patch.
                         In case of Non-rolling DomUs are already down and dom0domu plugins
                         cannot be executed.
                        '''
                        _rc = self.mRunDom0DomuPluginsFromInfraPatchMetadata(_node_name, _exacloud_plugin_data, aStage)

                if _rc != PATCH_SUCCESS_EXIT_CODE and mGetFailonError(_exacloud_plugin_data):
                    _ret = _rc
        self.mPatchLogInfo(f"Completed execution of exacloud plugins with return code {_ret}")
        return _ret

    def mRunExacloudPluginV2inNonRolling(self, aNodeList, aPhase):
        """
        This method executes exacloud plugins
        in non-rolling fashion.
        :return: PATCH_SUCCESS_EXIT_CODE in case of successful patch execution
                or FailOnError flag was set to false
            else
                return error code as per error details returned
                from below execution flow.
        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        _list_of_hosts_where_exacloud_plugin_execution_failed = []
        _cur_target = self.mGetTargetTypes()[0].lower()
        self.mPatchLogInfo(
            f"Starting execution of exacloud plugins in non-rolling fashion for nodes: {aNodeList} and phase: {aPhase}")

        def _run_exacloud_pluginv2_in_non_rolling(aNode, aStatus):

            self.mPatchLogInfo(f"Executing exacloud plugins on Node : {aNode}.")
            try:
                if str(mGetPluginTargetV2(_exacloud_plugin_data).lower()) in str(self.mGetTargetTypes()[0].lower()):
                    # Step1. Validate the script bundle
                    self.mPatchLogInfo(f"Validating exacloud plugin script bundle for node {aNode}")
                    _ret = self.mValidateExacloudPluginScriptBundle(_exacloud_plugin_data)
                    if _ret != PATCH_SUCCESS_EXIT_CODE:
                        aStatus.append({'node': aNode, 'status': 'failed', 'errorcode': _ret})
                    else:
                        # Step 2. Copy exacloud plugins.
                        self.mPatchLogInfo(f"Copying exacloud plugins to node {aNode}")
                        _ret = self.mCopyPluginsToTargetNodesV2(aNode, _exacloud_plugin_data)
                        if _ret != PATCH_SUCCESS_EXIT_CODE:
                            aStatus.append({'node': aNode, 'status': 'failed', 'errorcode': _ret})
                        else:
                            # Step 3. Run exacloud patch operation.
                            self.mPatchLogInfo(f"Executing exacloud plugin operation on node {aNode}")
                            _ret = self.mExecuteMetadataExadataPlugins(aNode, _exacloud_plugin_data)
                            if _ret != PATCH_SUCCESS_EXIT_CODE:
                                aStatus.append({'node': aNode, 'status': 'failed', 'errorcode': _ret})

                        # Step 4. Cleanup exacloud plugins and copy logs to exacloud
                        # irrespetive of plugin operation was successful or failed.
                        self.mPatchLogInfo(f"Cleaning up exacloud plugin on node {aNode}")
                        self.mCleanupExacloudPluginV2Script(aNode, _exacloud_plugin_data)

            except Exception as e:
                self.mPatchLogError(f"Error while running exacloud plugins on specified targets. Error : {str(e)}")

        # End of _run_exacloud_pluginv2_in_non_rolling method

        """
         Parallelly execute exacloud plugins
        """
        _list_of_hosts_where_exacloud_plugin_execution_failed = []
        _plist = ProcessManager()
        _rc_status = _plist.mGetManager().list()
        _exacloud_plugin_data = {}
        _ret = PATCH_SUCCESS_EXIT_CODE
        _plugin_type = None
        _phase = None

        for _exacloud_plugin_data in self.mGetPluginMetadata():
            # Get relevant infra patch plugins ecra metadata

            _plugin_type = mGetPluginType(_exacloud_plugin_data)
            if (_plugin_type).lower() != "exacloud":
                self.mPatchLogInfo(f"Only exacloud plugins will be run, current Plugin target type is : {_plugin_type}")
                continue

            _phase = mGetPhase(_exacloud_plugin_data)
            if (aPhase).lower() != (_phase).lower():
                continue
            else:
                self.mPatchLogInfo(
                    f"Current exacloud plugin scripts will be run with the following input : {json.dumps(_exacloud_plugin_data, indent=4)}")


            self.mPatchLogInfo(
                f"List of nodes where plugin metadata based exacloud plugins will be run : {str(aNodeList)}.")
            for _remote_node in aNodeList:
                _p = ProcessStructure(_run_exacloud_pluginv2_in_non_rolling, [_remote_node, _rc_status], _remote_node)

                '''
                 Timeout parameter configurable in Infrapatching.conf
                 Currently it is set to 10 minutes
                '''
                _p.mSetMaxExecutionTime(self.mGetExacloudPluginV2ExecutionTimeoutInSeconds())

                _p.mSetJoinTimeout(PARALLEL_OPERATION_TIMEOUT_IN_SECONDS)
                _p.mSetLogTimeoutFx(self.mPatchLogWarn)
                _plist.mStartAppend(_p)

            _plist.mJoinProcess()

            if _plist.mGetStatus() == "killed":
                if mGetFailonError(_exacloud_plugin_data):
                    if _cur_target == PATCH_DOM0:
                        _ret = DOM0_EXACLOUD_METADATA_BASED_PLUGIN_EXECUTION_FAILED
                    elif _cur_target == PATCH_DOMU:
                        _ret = DOMU_EXACLOUD_METADATA_BASED_PLUGIN_EXECUTION_FAILED
                    elif _cur_target == PATCH_CELL:
                        _ret = CELL_EXACLOUD_METADATA_BASED_PLUGIN_EXECUTION_FAILED

                    _suggestion_msg = "Timeout while executing exacloud plugin execution in parallel."
                    self.mAddError(_ret, _suggestion_msg)
                else:
                    self.mPatchLogWarn("Timeout while executing exacloud plugin execution in parallel.")
                return _ret

            # validate the return codes
            _list_of_hosts_where_exacloud_plugin_execution_failed = []
            for _rc_details in _rc_status:
                if _rc_details['status'] == "failed":
                    _list_of_hosts_where_exacloud_plugin_execution_failed.append(_rc_details['node'])

            if len(_list_of_hosts_where_exacloud_plugin_execution_failed) > 0:
                if mGetFailonError(_exacloud_plugin_data):
                    if _cur_target == PATCH_DOM0:
                        _ret = DOM0_EXACLOUD_METADATA_BASED_PLUGIN_EXECUTION_FAILED
                    elif _cur_target == PATCH_DOMU:
                        _ret = DOMU_EXACLOUD_METADATA_BASED_PLUGIN_EXECUTION_FAILED
                    elif _cur_target == PATCH_CELL:
                        _ret = CELL_EXACLOUD_METADATA_BASED_PLUGIN_EXECUTION_FAILED

                    _suggestion_msg = f"Error while running exacloud plugin on specified targets : {_list_of_hosts_where_exacloud_plugin_execution_failed}. \n"
                    self.mAddError(_ret, _suggestion_msg)
                    break
                else:
                    self.mPatchLogWarn(
                        f"Errors while running exacloud plugin on specified targets {_list_of_hosts_where_exacloud_plugin_execution_failed} are ignored based on InfraPatchPluginMetadata ignore error attribute. \n")
        return _ret

    def mValidateExacloudPluginScriptBundle(self, aExacloudPluginsdata):
        """
        Validates exacloud plugin script bundle.

        :param aExacloudPluginsdata: Exacloud plugin metadata
        :return: PATCH_SUCCESS_EXIT_CODE if validation is successful, otherwise an error code
        """
        _ret = PATCH_SUCCESS_EXIT_CODE

        # Location of exacloud plugins (on exacloud and on target node)
        try:

            # Extract script bundle name and hash from the plugin metadata
            _script_bundle_name = mGetScriptBundleName(aExacloudPluginsdata)
            _script_bundle_hash = mGetScriptBundleHash(aExacloudPluginsdata)

            # Construct the relative path to the script bundle on Exacloud
            _relative_script_path_on_exacloud = f"{get_gcontext().mGetBasePath()}/exadataPrePostPlugins/exacloud_plugins/"
            _plugin_target = mGetPluginTargetV2(aExacloudPluginsdata)

            self.mPatchLogInfo(
                f"Validating Exacloud plugin script bundle: bundle name={_script_bundle_name}, bundle hash={_script_bundle_hash}, relative path on Exacloud={_relative_script_path_on_exacloud}, plugin target={_plugin_target}")

            # Check if the relative script path on Exacloud exists
            if not os.path.exists(_relative_script_path_on_exacloud):
                self.mPatchLogError(f"Parent plugins directory is missing: {_relative_script_path_on_exacloud}")
                _ret = PARENT_PLUGINS_MISSING
                return _ret


            # Construct the full path to the script bundle tar file
            _bundle_tar = os.path.join(_relative_script_path_on_exacloud, f"{_script_bundle_name}")
            self.mPatchLogInfo(f"Script bundle tar file: {_bundle_tar}")

            # Check if the script bundle tar file exists
            if not os.path.exists(_bundle_tar):
                self.mPatchLogError(f"Exacloud plugin script bundle is missing: {_bundle_tar}")
                _ret = EXACLOUD_PLUGIN_SCRIPT_BUNDLE_MISSING
                return _ret

            # Compute the SHA256 checksum of the script bundle tar file
            _computed_hash = self.mComputeSha256Checksum(_bundle_tar)
            self.mPatchLogInfo(f"Computed SHA256 checksum of the bundle tar : {_computed_hash}")

            # Compare the computed hash with the expected hash
            if _computed_hash:
                if _computed_hash != _script_bundle_hash:
                    self.mPatchLogError(
                        f"SHA256sum mismatch for script bundle. Expected: {_script_bundle_hash}, Computed: {_computed_hash}")
                    _ret = EXACLOUD_PLUGIN_SCRIPT_BUNDLE_HASH_MISMATCH
                    return _ret                    
            else:
                self.mPatchLogError("Failed to compute SHA256 checksum for script bundle")
                _ret = EXACLOUD_PLUGIN_SCRIPT_BUNDLE_HASH_MISMATCH
                return _ret

        except Exception as e:
            self.mPatchLogError(
                f"An error occurred while validating the exacloud plugin, script bundle validation failed: {str(e)}")
            _ret = EXACLOUD_PLUGIN_SCRIPT_VALIDATION_EXCEPTION
        return _ret

    def mCopyPluginsToTargetNodesV2(self, aNode, aExacloudPluginsdata):
        '''
          This method copies plugin and other
          config files to target nodes specified.
        '''
        _ret = PATCH_SUCCESS_EXIT_CODE
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=aNode, aTimeout=20)
        _plugin_target = None
        _script_dir_name = None
        _fail_on_error = None
        _cur_target = self.mGetTargetTypes()[0].lower()
        '''
         Below code snippet validates for existence of 
         Exacloud plugin directories locally on the exacloud as well as the 
         target nodes.
        '''
        _script_dir_name = None
        # Location of exacloud plugins (on exacloud and on target node)
        try:
            _script_dir_name = f"{get_gcontext().mGetBasePath()}/exadataPrePostPlugins/exacloud_plugins"
            _plugin_target = mGetPluginTargetV2(aExacloudPluginsdata)
            _fail_on_error = mGetFailonError(aExacloudPluginsdata)

            if not os.path.exists(_script_dir_name):
                _ret = PARENT_PLUGINS_MISSING
                if _fail_on_error:
                    _suggestion_msg = f"Parent plugins for '{_plugin_target}' are not found on '{_script_dir_name}'"
                    self.mAddError(_ret, _suggestion_msg)
                else:
                    self.mPatchLogWarn(
                        f"Parent plugins for '{_plugin_target}' are not found on '{_script_dir_name}'")
                return _ret
        except Exception as e:
            self.mPatchLogError(f"Exception: Validating presence of exacloud plugins : {str(e)}")

        try:
            # Create remote plugin stage directory before copying patches.
            _remote_script_dir = mGetScriptAlias(aExacloudPluginsdata)
            _script_bundle_tar = mGetScriptBundleName(aExacloudPluginsdata)
            _plugin_target = mGetPluginTargetV2(aExacloudPluginsdata)

            self.mPatchLogInfo(
                f"Creating exacloud patch stage directory : {os.path.join(EXACLOUD_PLUGIN_REMOTE_STAGE_DIR, _remote_script_dir)} on remote node : {aNode}")
            _node.mExecuteCmdLog(
                f'mkdir -p {os.path.join(EXACLOUD_PLUGIN_REMOTE_STAGE_DIR, _remote_script_dir)}')

            self.mPatchLogInfo(
                f"Target Node: {aNode}, Copy plugins: Source = {_script_dir_name}/{_script_bundle_tar}, Destination location = {os.path.join(EXACLOUD_PLUGIN_REMOTE_STAGE_DIR, _remote_script_dir)}")

            if os.path.exists(os.path.join(_script_dir_name, _script_bundle_tar)):
                _node.mCopyFile(os.path.join(_script_dir_name, _script_bundle_tar),
                                os.path.join(EXACLOUD_PLUGIN_REMOTE_STAGE_DIR, _remote_script_dir))

            if _node.mFileExists(os.path.join(EXACLOUD_PLUGIN_REMOTE_STAGE_DIR, _remote_script_dir, _script_bundle_tar)):
                _node.mExecuteCmdLog(
                    f"cd {os.path.join(EXACLOUD_PLUGIN_REMOTE_STAGE_DIR, _remote_script_dir)}; tar -xvzf {_script_bundle_tar}")
            else:
                self.mPatchLogError(f"Exacloud plugin script bundle is missing on target node: {aNode}")
                _ret = EXACLOUD_PLUGIN_SCRIPT_BUNDLE_MISSING

        except Exception as e:
            if _cur_target == PATCH_DOM0:
                _ret = EXACLOUD_PLUGIN_COPY_DOM0_EXCEPTION_ERROR
            elif _cur_target == PATCH_DOMU:
                _ret = EXACLOUD_PLUGIN_COPY_DOMU_EXCEPTION_ERROR
            elif _cur_target == PATCH_CELL:
                _ret = EXACLOUD_PLUGIN_COPY_CELL_EXCEPTION_ERROR

            if _fail_on_error:
                _suggestion_msg = f"Exception: Error in Copying Exacloud plugins to target node: {aNode} and location : {os.path.join(EXACLOUD_PLUGIN_REMOTE_STAGE_DIR, mGetScriptAlias(aExacloudPluginsdata))}"
                self.mAddError(_ret, _suggestion_msg)
            else:
                self.mPatchLogWarn(
                    f"Exception: Error in Copying Exacloud plugins to target node: {aNode} and location : {os.path.join(EXACLOUD_PLUGIN_REMOTE_STAGE_DIR, mGetScriptAlias(aExacloudPluginsdata))}")
            self.mPatchLogWarn(traceback.format_exc())
        finally:
            if _node.mIsConnected():
                _node.mDisconnect()
            self.mPatchLogInfo(f"mCopyPluginsToTargetNodesV2 exited with return code: {_ret}")
            return _ret

    def mCleanupExacloudPluginV2Script(self, aNode, aExacloudPluginsdata):
        '''
         Clean up scripts and config files on the
         Target nodes.
        '''
        _node = exaBoxNode(get_gcontext())
        _suggestion_msg = None
        _script_dir_name = None
        _plugin_log = None
        try:
            _plugin_log = self.mGetPluginLog(aExacloudPluginsdata)
            _script_dir_name = mGetScriptAlias(aExacloudPluginsdata)
            _node.mConnect(aHost=aNode, aTimeout=20)

            # 3 a. Copy all the relevant log to local.
            self.mPatchLogInfo(
                f"Copying the logs from Node : {aNode}, Location : {_plugin_log} to Local Directory : {self.mGetLogPath()} ")
            _exacloud_log_path = f"{self.mGetLogPath()}/{mGetPhase(aExacloudPluginsdata)}_{TASK_PATCH}_{aNode}_{mGetScriptAlias(aExacloudPluginsdata)}.log"
            self.mPatchLogInfo(f"Exacloud log path for plugin console log : {_exacloud_log_path}")
            if _node.mFileExists(_plugin_log):
                _node.mCopy2Local(_plugin_log, _exacloud_log_path)

            # 3 b. Delete Plugin metadata based exacloud plugins.
            _plugin_dir_to_be_cleaned_up = os.path.join(EXACLOUD_PLUGIN_REMOTE_STAGE_DIR, mGetScriptAlias(aExacloudPluginsdata))
            if _node.mFileExists(_plugin_dir_to_be_cleaned_up):
                self.mPatchLogInfo(
                    f"Deleting plugin directory : {_plugin_dir_to_be_cleaned_up} from target node : {aNode}")
                _node.mExecuteCmdLog(f"rm -rfv {_plugin_dir_to_be_cleaned_up}")

        except Exception as e:
            self.mPatchLogWarn(
                f"Exception: Error in deleting Exacloud Plugin directories on Node : {aNode} and location : {os.path.join(EXACLOUD_PLUGIN_REMOTE_STAGE_DIR, _script_dir_name)}")
            self.mPatchLogWarn(traceback.format_exc())
        finally:
            if _node.mIsConnected():
                _node.mDisconnect()

    def mExecuteMetadataExadataPlugins(self, aNode, aExacloudPluginsdata):
        """
         This method executes the exacloud plugin scripts and options specified
         by user. Currently a exacloud plugin script is checked in and
         will always return success. User can customise this file
         as per their requirement.

          -> return PATCH_SUCCESS_EXIT_CODE if successful.
          -> return any other error code other than PATCH_SUCCESS_EXIT_CODE if failure.
        """

        _ret = PATCH_SUCCESS_EXIT_CODE
        _connected_as_non_root_user = False
        _sudo_str = ''
        _plugin_log = None
        _plugin_target = None
        _fail_on_error = None
        _cur_target = self.mGetTargetTypes()[0].lower()

        _exacloud_plugin_args = self.mGetOneOffPluginArguments()
        _node = exaBoxNode(get_gcontext())
        try:
            _plugin_log = self.mGetPluginLog(aExacloudPluginsdata)
            _plugin_target = mGetPluginTargetV2(aExacloudPluginsdata)
            _remote_script_name_for_exacloud_plugins = self.mGetRemoteScriptNameForExacloudPlugins(aExacloudPluginsdata)
            _fail_on_error = mGetFailonError(aExacloudPluginsdata)

            # Connect as opc for domU if exist, otherwise, as root user
            _user_to_connect_with = self.mGetUserDetailsBasedOnDomUhostnameToRunPlugins(aNode)
            if str(mGetPluginTargetV2(aExacloudPluginsdata)).lower() == PATCH_DOMU and _user_to_connect_with:
                _node.mSetUser(_user_to_connect_with)
                _node.mSetMaxRetries(self.mGetMaxNumberofSshRetries())
                self.mPatchLogInfo(
                    f"Plugin metadata based exacloud plugins run: Connecting as {_user_to_connect_with} user to '{_plugin_target}' to run plugins on node - {aNode}.")
                if _user_to_connect_with != 'root':
                    _connected_as_non_root_user = True
            else:
                self.mPatchLogInfo(
                    f"Plugin metadata based exacloud plugins run: Connecting as root user to '{_plugin_target}' to run plugins on node - {aNode}.")

            if _connected_as_non_root_user:
                _sudo_str = 'sudo '
                _cmd_exacloud_run = f"{_sudo_str}chown -R opc:opc {EXACLOUD_PLUGIN_REMOTE_STAGE_DIR}; {_sudo_str}chmod +x {_remote_script_name_for_exacloud_plugins}; {_sudo_str}{_remote_script_name_for_exacloud_plugins} {_exacloud_plugin_args} > {_plugin_log} "
            else:
                _cmd_exacloud_run = f"chmod +x {_remote_script_name_for_exacloud_plugins};{_remote_script_name_for_exacloud_plugins} {_exacloud_plugin_args} > {_plugin_log} "

            self.mPatchLogInfo(f"exacloud plugin run command is : {_cmd_exacloud_run}")

            _node.mConnect(aHost=aNode, aTimeout=20)
            if not _node.mFileExists(_remote_script_name_for_exacloud_plugins):
                if _cur_target == PATCH_DOM0:
                    _ret = EXACLOUD_PLUGIN_MISSING_DOM0_EXCEPTION_ERROR
                elif _cur_target == PATCH_DOMU:
                    _ret = EXACLOUD_PLUGIN_MISSING_DOMU_EXCEPTION_ERROR
                elif _cur_target == PATCH_CELL:
                    _ret = EXACLOUD_PLUGIN_MISSING_CELL_EXCEPTION_ERROR

                if _fail_on_error:
                    _suggestion_msg = f"Unable to find exacloud plugins file : {_remote_script_name_for_exacloud_plugins} on node - {aNode}."
                    self.mAddError(_ret, _suggestion_msg)
                else:
                    self.mPatchLogWarn(
                        f"Unable to find exacloud plugins file : {_remote_script_name_for_exacloud_plugins} on node - {aNode}.")
                if _node.mIsConnected():
                    _node.mDisconnect()
                return _ret

            _i, _o, _e = _node.mExecuteCmd(_cmd_exacloud_run)
            _out = _o.readlines()
            for _output in _out:
                self.mPatchLogInfo(f"{_output.strip()}")
            _rc = _node.mGetCmdExitStatus()
            self.mPatchLogInfo(f"Exacloud Plugin Exit Command Status {_rc} on node - {aNode}.")
            if int(_rc) == 0:
                self.mPatchLogInfo(
                    f"\nPlugin metadata based exacloud plugins Patch apply completed successfully on {aNode}.\n")
            else:
                if _cur_target == PATCH_DOM0:
                    _ret = DOM0_EXACLOUD_METADATA_BASED_PLUGIN_EXECUTION_FAILED
                elif _cur_target == PATCH_DOMU:
                    _ret = DOMU_EXACLOUD_METADATA_BASED_PLUGIN_EXECUTION_FAILED
                elif _cur_target == PATCH_CELL:
                    _ret = CELL_EXACLOUD_METADATA_BASED_PLUGIN_EXECUTION_FAILED

                if _fail_on_error:
                    _suggestion_msg = f"Running Plugin metadata based exacloud plugins failed on node = {aNode}"
                    self.mAddError(_ret, _suggestion_msg)
                else:
                    self.mPatchLogWarn(
                        f"Running Plugin metadata based exacloud plugins failed on node = {aNode} and since FailOnError is set to 'no', plugin operations will continue.")
        except Exception as e:
            if _cur_target == PATCH_DOM0:
                _ret = EXACLOUD_PLUGIN_APPLY_DOM0_EXCEPTION_ERROR
            elif _cur_target == PATCH_DOMU:
                _ret = EXACLOUD_PLUGIN_APPLY_DOMU_EXCEPTION_ERROR
            elif _cur_target == PATCH_CELL:
                _ret = EXACLOUD_PLUGIN_APPLY_CELL_EXCEPTION_ERROR

            if _fail_on_error:
                _suggestion_msg = f"Unable to execute exacloud plugins on {aNode}. Error : {str(e)}"
                self.mAddError(_ret, _suggestion_msg)
            else:
                self.mPatchLogWarn(f"Unable to execute exacloud plugins on {aNode}. Error : {str(e)}")
            self.mPatchLogWarn(traceback.format_exc())
        finally:
            if _node.mIsConnected():
                _node.mDisconnect()
            return _ret

    def mRunDom0DomuPluginsFromInfraPatchMetadata(self, aNode, aExacloudPluginsdata, aPhase):
        """
         This method executes plugin metadata based exacloud
         plugins on the DomUs during a dom0 patching and Dom0DomU
         PluginTarget is specified.
        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        _rc = PATCH_SUCCESS_EXIT_CODE
        _child_request_error_already_exists_in_db = None
        _fail_on_error = None
        _cur_target = self.mGetTargetTypes()[0].lower()

        try:
            _fail_on_error = mGetFailonError(aExacloudPluginsdata)
            _dom0U_list = []
            if self.isADBDImplicitPluginEnabled() == True:
                _dom0U_list = self.mGetAutonomousVMList()
                self.mPatchLogInfo(
                    f"AutonomousVM list on which implicit dom0domu plugin will be copied are {str(_dom0U_list)} ")
            else:
                _dom0U_list = self.mReturnPatchingDom0DomUListFromEcra()
                self.mPatchLogInfo("AutonomousVM list is none, explicit exacloud dom0domu plugin will be copied to all domu")

            for _dom0_hostname, _dom0s_domU in _dom0U_list:
                # if first node in a pair is dom0 then copy corresponding domU
                if aNode == _dom0_hostname:
                    # SSH validation in parallel.
                    try:
                        self.mPatchLogInfo(
                            "Connectivity between Exacloud node and Guest VMs are expected to be enabled during PluginTarget=Dom0DomU exacloud plugin run. Verifying ssh connectivity with opc user.")
                        self.mGetCluPatchCheck().mVerifyExacloudExadataHostSshConnectivity(_dom0s_domU, aSshUser='opc')
                    except Exception as e:
                        self.mPatchLogInfo("Connectivity between Exacloud node and Guest VMs failed with opc user so trying with root user.")
                        self.mGetCluPatchCheck().mVerifyExacloudExadataHostSshConnectivity(_dom0s_domU)

                    for _domUs in _dom0s_domU:
                        if _domUs.split(".")[0].find(DUMMYDOMU) > -1:
                            self.mPatchLogWarn(
                                f"DOM0 '{aNode}' is not having guest vm since it is not part of any node subset group. Skipping exacloud copy plugin on dummy VM = '{_domUs}'")
                            continue                        
                    # Execute dom0domu plugins in parallel on the current dom0
                    _ret = self.mRunExacloudPluginV2inRolling(_dom0s_domU, aPhase)

        except Exception as e:
            if _fail_on_error:
                _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()
            if _child_request_error_already_exists_in_db:
                _ret = _rc
            else:
                if _cur_target == PATCH_DOM0:
                    _ret = EXACLOUD_PLUGIN_APPLY_DOM0_EXCEPTION_ERROR
                elif _cur_target == PATCH_DOMU:
                    _ret = EXACLOUD_PLUGIN_APPLY_DOMU_EXCEPTION_ERROR
                elif _cur_target == PATCH_CELL:
                    _ret = EXACLOUD_PLUGIN_APPLY_CELL_EXCEPTION_ERROR

                if _fail_on_error:
                    _suggestion_msg = f"Exception: Exacloud apply failed, Error details : {str(e)} on {_cur_target} target."
                    self.mAddError(_ret, _suggestion_msg)
                else:
                    self.mPatchLogWarn(
                        f"Exception: Exacloud apply failed, Error details : {str(e)} on {_cur_target} target.")
        finally:
            return _ret

    def mGetPluginLog(self, aExacloudPluginsdata):
        _current_plugin_log_name = f"exacloud_plugins_{mGetScriptAlias(aExacloudPluginsdata)}.log"
        return os.path.join(EXACLOUD_PLUGIN_REMOTE_STAGE_DIR, _current_plugin_log_name)

    def mGetRemoteScriptNameForExacloudPlugins(self, aExacloudPluginsdata):
        _patch_file = os.path.join(EXACLOUD_PLUGIN_REMOTE_STAGE_DIR, mGetScriptAlias(aExacloudPluginsdata) + "/" + mGetScriptName(aExacloudPluginsdata))
        return _patch_file

    def mGetExacloudPluginV2ExecutionTimeoutInSeconds(self):
        return int(mGetInfraPatchingConfigParam('exacloud_plugin_execution_timeout_in_seconds'))
