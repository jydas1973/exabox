#
# $Header: ecs/exacloud/exabox/infrapatching/handlers/patchmgrhandler.py /main/4 2025/11/08 08:54:10 araghave Exp $
#
# patchmgrhandler.py
#
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
#
#    NAME
#      patchmgrhandler.py - base patchmanager class 
#
#    DESCRIPTION
#      This is an object representation of patchmgr supported/related operations exposed as 
#      apis via PatchManager base class/object. 
#      Consumers of PatchManager apis are its child classes InfraPatchManager and ExaPatchManager. 
#      infra (rack patching) and exacompute patching extends the base patchmanager class and implements abstract 
#      methods for specific needs
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    araghave    09/11/25 - Enh 38173247 - EXACLOUD CHANGES TO SUPPORT DOMU ELU
#                           INFRA PATCH OPERATIONS
#    sdevasek    02/14/25 - ENH 37496197 - INFRAPATCHING TEST AUTOMATION -
#                           REVIEW AND ADD METHODS INTO METHODS_TO_EXCLUDE_
#                           COVERAGE_REPORT
#    araghave    09/17/24 - Enh 36971721 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE TARGET HANDLER FILES
#    emekala     07/29/24 - ENH 36794217 - PATCH MANAGER SPECIFIC CHANGES TO
#                           HANDLE EXACOMPUTE AND DOMU PATCHMGR CMDS
#    emekala     07/29/24 - Creation
#

import os
import sys
import abc
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.infrapatching.handlers.loghandler import LogHandler
from exabox.infrapatching.utils.constants import PATCH_DOMU, PATCH_CONSOLE_LOG
from exabox.infrapatching.core.infrapatcherror import PATCHMGR_COMMAND_FAILED, DOMU_PATCHMGR_COMMAND_FAILED, PATCH_SUCCESS_EXIT_CODE, EXADATA_PATCHMGR_CONSOLE_READ_TIMEOUT_ERROR, PATCHMGR_SESSION_ALREADY_EXIST

sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))

class PatchManager(LogHandler):

    def __init__(self, aTarget, aOperation, aPatchBaseAfterUnzip, aLogPathOnLaunchNode, aHandler):
        super(PatchManager, self).__init__()
        self.mPatchLogInfo("PatchManager")

        # patch manager related bare minimum variables
        self.__target = aTarget
        self.__operation = aOperation
        self.__patch_base_after_unzip = aPatchBaseAfterUnzip
        self.__log_path_on_launch_node = aLogPathOnLaunchNode
        # Handler instance of dom0, domU, cell, ibswitch, roceswitch etc.,
        # to access handler and handler's base class apis
        self.__handler = aHandler


        # component's operation specific bare minimum variables 
        self.__nodes_to_be_patched_file = None
        self.__iso_repo = None
        self.__customized_node_list = []
        self.__launch_node = None
        self.__timeout_in_seconds = None

        # Following can be accessed/derived from handler and handler's base class apis
        # but added in PatchManager class to let the caller decide and set some of the optional 
        # patchmgr options for a component's operation and have more control and clarity on what
        # all patchmgr options being set etc.,
        self.__backup_mode = None
        self.__operation_style = None
        self.__target_version = None
        self.__options = None
        self.__system_consistency_state = True
        self.__is_exa_splice_enabled = False
        self.__is_cps_launch_node_for_domu = False
        self.__is_management_host_launch_node_for_domu = False
        self.__apply_outstanding_work_items = False

        # patchmanager related status
        self.__status_code = None
        self.__completed = False

        # patch failed node list. exacompute needs this data
        self.__patch_failed_node_list = []

    # patch manager related bare minimum setter/getters
    def mGetTarget(self):
        return self.__target

    def mGetOperation(self):
        return self.__operation

    def mGetPatchBaseAfterUnzip(self):
        return self.__patch_base_after_unzip

    # component's operation specific bare minimum setter/getters
    def mSetNodesToBePatchedFile(self, aNodesToBePatchedFile):
        self.__nodes_to_be_patched_file = aNodesToBePatchedFile

    def mSetIsoRepo(self, aIsoRepo):
        self.__iso_repo = aIsoRepo

    def mGetIsoRepo(self):
        return self.__iso_repo

    def mSetLogPathOnLaunchNode(self, aLogPathOnLaunchNode):
        self.__log_path_on_launch_node = aLogPathOnLaunchNode

    def mGetLogPathOnLaunchNode(self):
        return self.__log_path_on_launch_node

    def mSetCustomizedNodeList(self, aCustomizedNodeList):
        """
          This is the dom0U node list where patchmgr existing session is checked
        """
        self.__customized_node_list = aCustomizedNodeList

    def mGetCustomizedNodeList(self):
        return self.__customized_node_list

    def mSetLaunchNode(self, aLaunchNode):
        self.__launch_node = aLaunchNode

    def mGetLaunchNode(self):
        return self.__launch_node

    def mSetApplyOutstandingWorkDuringEluPatchFlag(self, aApplyOutstandingWorkDuringEluPatch):
        self.__apply_outstanding_work_items = aApplyOutstandingWorkDuringEluPatch

    def mGetApplyOutstandingWorkDuringEluPatchFlag(self):
        return self.__apply_outstanding_work_items

    def mSetTimeoutInSeconds(self, aTimeoutInSeconds):
        self.__timeout_in_seconds = aTimeoutInSeconds

    def mGetTimeoutInSeconds(self):
        return self.__timeout_in_seconds

    # Handler instance of dom0U, cell, ibswitch, roceswitch etc.,
    # to access handler and handler's base class apis
    def mSetHandler(self, aHandler):
        self.__handler = aHandler

    def mGetHandler(self):
        return self.__handler

    # Following can be accessed/derived from handler and handler's base class apis
    # but added in PatchManager class to let the caller decide and set some of the optional 
    # patchmgr options for a component's operation and have more control and clarity on what
    # all patchmgr options being set etc.,

    def mSetOperationStyle(self, aOperationStyle):
        self.__operation_style = aOperationStyle

    def mGetOperationStyle(self):
        return self.__operation_style

    def mSetTargetVersion(self, aTargetVersion):
        self.__target_version = aTargetVersion

    def mGetTargetVersion(self):
        return self.__target_version

    def mSetSystemConsistencyState(self, aSystemConsistencyState=True):
        self.__system_consistency_state= aSystemConsistencyState

    def mGetSystemConsistencyState(self):
        return self.__system_consistency_state

    def mSetIsExaSpliceEnabled(self, aIsExaSpliceEnabled=False):
        self.__is_exa_splice_enabled = aIsExaSpliceEnabled

    def mIsExaSpliceEnabled(self):
        return self.__is_exa_splice_enabled


    # patchmanager related status setter/getters/boolean
    def mSetStatusCode(self, aStatusCode):
        self.__status_code = aStatusCode
        self.mPatchLogInfo(f"PatchMgr exit status code being set to : {self.__status_code}")

    def mGetStatusCode(self):
        if self.__status_code is None:
            # Default patchmgr status code when there is an error before setting 
            # the value via mSetStatusCode method in mWaitForPatchMgrCmdExecutionToComplete            
            self.__status_code = PATCHMGR_COMMAND_FAILED
            if self.mGetTarget() == PATCH_DOMU:
                self.__status_code = DOMU_PATCHMGR_COMMAND_FAILED
            self.mPatchLogWarn(f"PatchMgr status code not yet set hence assigning the default status code: {self.__status_code}")
        self.mPatchLogInfo(f"PatchMgr exit status code is: {self.__status_code}")
        return self.__status_code

    def mSetCompleted(self, aCompleted=False):
        self.__completed = aCompleted

    def mSetPatchFailedNodeList(self, aPatchFailedNodeList):
        self.__patch_failed_node_list = aPatchFailedNodeList

    def mGetPatchFailedNodeList(self):
        return self.__patch_failed_node_list

    def mGetPatchMgrConsoleOutputFile(self):
        """
         Get the patchmgr PatchmgrConsole.out logfile path
        """
        return os.path.join(self.mGetLogPathOnLaunchNode(), PATCH_CONSOLE_LOG)


    def mIsPatchMgrConsoleOutputFileExists(self, aLaunchNode=None):
        """
         Checks whether patchmgr PatchmgrConsole.out file exists on the launch node or not
         return True - if file exists
         return False - if not not exists
        """
        _file_exists = False
        _launch_node = aLaunchNode
        if _launch_node is None:
            _launch_node = self.mGetLaunchNode()
        if _launch_node:
            _node = exaBoxNode(get_gcontext())
            try:
                _node.mConnect(aHost=_launch_node)
                if _node.mFileExists(self.mGetPatchMgrConsoleOutputFile()):
                    _file_exists = True
            finally:
                if _node.mIsConnected():
                    _node.mDisconnect()
        else:
            self.mPatchLogInfo(f"_launch_node not set hence mIsPatchMgrConsoleOutputFileExists returning False")

        return _file_exists


    def mCheckForPatchMgrSessionExistence(self, aUpdateExacloudDB=True):
        """
         This method checks for existing of patchmgr session.

         Return two values:
          1) Non-zero (EB ERROR - 613) : One or more patchmgr sessions
              OR
             Zero: No patchmgr session are running
          2) Node name which is running pacthmgr
          3) In case of aUpdateExacloudDB set to False patchmgr
             existence check is only required to be performed and not
             update the exacloud DB as in such cases, there is an 
             existing error code on the Exacloud DB and do not want 
             error code from mCheckForPatchMgrSessionExistence to overwite 
             the previous Error code.
             
        """

        def _patchmgr_session_hint(aNode):
            """
             Return:
               PATCHMGR_SESSION_ALREADY_EXIST : One or more patchmgr sessions are running or had patchmgr ran
               PATCH_SUCCESS_EXIT_CODE        : No patchmgr sessions are running.
            """

            _node = exaBoxNode(get_gcontext())
            self.mGetHandler().mSetConnectionUser(_node=_node)
            _node.mConnect(aHost=aNode)

            # Search of 'patchmgr -' in the grep command.

            # TODO: Below code can be used for future requirement:-
            # # See if there any remote console log found
            # if not aPatchmgLogPathLaunchNode:
            # self.mPatchLogInfo("The patchmgr console log found. Active Launch Node = '%s'." % aNode)
            #
            # _patchmgr_console_log_find = 'find %s/PatchmgrConsole.out' % (aPatchmgLogPathLaunchNode)
            # _i, _o, _e = _node.mExecuteCmd(_patchmgr_console_log_find)
            # if int(_node.mGetCmdExitStatus()) == 0:
            # self.mPatchLogInfo("The patchmgr console log found. Active Launch Node = '%s'." % aNode)
            #     _node.mDisconnect()
            # return True

            _cmd = "ps -ef | egrep -i 'patchmgr -' | egrep -vi 'grep|tail'" 
            _i, _o, _e = _node.mExecuteCmd(_cmd)
            if int(_node.mGetCmdExitStatus()) == 0:
                self.mPatchLogInfo(
                    f"The patchmgr session is active on this cluster. Patchmgr Active Node = '{aNode}'.")
                if _o:
                    self.mPatchLogInfo(
                        f"Patchmgr session existence check cmd: {_cmd} output is:\n{str(_o.readlines())}")
                if _node.mIsConnected():
                    _node.mDisconnect()
                return PATCHMGR_SESSION_ALREADY_EXIST

            if _node.mIsConnected():
                _node.mDisconnect()
            return PATCH_SUCCESS_EXIT_CODE

        # end of _patchmgr_session_hint

        ret = PATCH_SUCCESS_EXIT_CODE
        _patchmgr_session_active_node = None

        # This is the dom0U node list where patchmgr existing session is checked
        _node_list = self.mGetCustomizedNodeList()
        _launch_node = self.mGetLaunchNode()
        _rack_name = self.mGetHandler().mGetRackName()

        # Find patchmgr session in the given list of nodes
        if _node_list:
            self.mPatchLogInfo("*** Checking for existence of patchmgr/dbnodeupdate.sh sessions in the cluster.")
            for _dom0domU in _node_list:
                ret = _patchmgr_session_hint(aNode=_dom0domU)
                if ret != PATCH_SUCCESS_EXIT_CODE:
                    if aUpdateExacloudDB:
                        _suggestion_msg = f"Patchmgr session already exists on node : {_dom0domU}"
                        self.mGetHandler().mAddError(ret, _suggestion_msg)
                    _patchmgr_session_active_node = _dom0domU
                    break
            # Find patchmgr session on the launch node
        elif _launch_node:
            self.mPatchLogInfo(
                f"*** Checking for existence of patchmgr/dbnodeupdate.sh sessions in the cluster on Node {_launch_node} ")
            ret = _patchmgr_session_hint(aNode=_launch_node)
            if ret != PATCH_SUCCESS_EXIT_CODE:
                if aUpdateExacloudDB:
                    _suggestion_msg = f"Patchmgr session already exists on launch node : {_launch_node}"
                    self.mGetHandler().mAddError(ret, _suggestion_msg)
                _patchmgr_session_active_node = _launch_node

        if _patchmgr_session_active_node:
            self.mPatchLogInfo(f"*** Patchmgr session found on {_patchmgr_session_active_node}")

        return ret, _patchmgr_session_active_node


    @abc.abstractmethod
    def mGetNodesToBePatchedFile(self):
        pass

    @abc.abstractmethod
    def mCreateNodesToBePatchedFile(self, aLaunchNode, aHostList, aExclude=""):
        pass

    @abc.abstractmethod
    def mGetNodeListFromNodesToBePatchedFile(self, aHost=None):
        pass

    @abc.abstractmethod
    def mGetPatchMgrCmd(self):
        pass

    @abc.abstractmethod
    def mExecutePatchMgrCmd(self, aPatchMgrCmd):
        pass

    @abc.abstractmethod
    def mWaitForPatchMgrCmdExecutionToComplete(self, aInputListFile=None, aPatchStates=None):
        pass
