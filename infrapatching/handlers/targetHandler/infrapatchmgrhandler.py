#
# $Header: ecs/exacloud/exabox/infrapatching/handlers/targetHandler/infrapatchmgrhandler.py /main/19 2025/11/08 08:54:10 araghave Exp $
#
# infrapatchmgrhandler.py
#
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
#
#    NAME
#      infrapatchmgrhandler.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      This is an object representation of patchmgr supported/related operations exposed as 
#      apis via InfraPatchManager class/object extending the base class PatchManager
#      Consumers of InfraPatchManager apis are dom0, domu, cell, ibswitch, roceswitch, adminswitch handlers.
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    araghave    09/11/25 - Enh 38173247 - EXACLOUD CHANGES TO SUPPORT DOMU ELU
#                           INFRA PATCH OPERATIONS
#    araghave    06/24/25 - Enhancement Request 38082882 - HANDLING EXACLOUD
#                           ELU CHANGES FOR DOM0 PATCHING
#    araghave    06/05/25 - Enh 38039225 - RE-RUN PATCHMGR VERIFY CONFIG IN
#                           CASE OF A FAILURE DUE TO SWITCH MISCONFIGURATION
#                           DURING PROVISIONING
#    araghave    03/17/25 - Enh 37713042 - CONSUME ERROR HANDLING DETAILS FROM
#                           INFRAPATCHERROR.PY DURING EXACOMPUTE PATCHING
#    antamil     01/31/25 - Enh 37300427 - Enable clusterless cell patching
#                           using management host
#    araghave    01/27/25 - Enh 37132175 - EXACOMPUTE MUST REUSE INFRA PATCHING
#                           MODULES FOR VALIDATION AND PATCH OPERATIONS
#    araghave    01/23/25 - Enh 37106126 - PROVIDE A MECHANISM TO PATCH SPINE
#                           SWITCHES
#    bhpati      11/06/24 - Enh 37162258 - EXACC GEN2 | PATCHING | DIAG TAR
#                           FILES TO BE COPIED TO OEDA LOCATION EVEN FOR CELL
#                           PATCHING FAILURE
#    antamil     10/04/24 - Enh 37027134 - Modularize single vm patching code
#    antamil     09/17/24 - bug 37068006: Additional fixes for single VM patching
#    araghave    09/16/24 - Enh 36971721 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE TARGET HANDLER FILES
#    diguma      08/21/24 - bug 36871736:REPLACE EXASPLICE WITH ELU(EXADATA
#                           LIVE UPDATE) FOR EXADATA 24.X
#    araghave    08/14/24 - Enh 36923844 - INFRA PATCHING CHANGES TO SUPPORT
#                           PATCHING ADMIN SWITCH
#    emekala     08/13/24 - ENH 36679949 - REMOVE OVERHEAD OF INDEPENDENT
#                           MONITORING PROCESS FROM INFRAPATCHING
#    emekala     07/29/24 - ENH 36794217 - PATCH MANAGER SPECIFIC CHANGES TO
#                           HANDLE EXACOMPUTE AND DOMU PATCHMGR CMDS
#    araghave    06/25/24 - Enh 36522596 - REVIEW PRE-CHECK/PATCHING/ROLLBACK
#                           LOGS AND CLEAN-UP
#    emekala     06/24/24 - ENH 36748433 - PATCH MANAGER SPECIFIC CHANGES TO
#                           HANDLE DOM0, CELL, IBSWITCH AND ROCESWITCH PATCHMGR
#                           CMDS
#

import os
import sys
import glob
import time
import datetime
import traceback
import subprocess
import re
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.infrapatching.handlers.patchmgrhandler import PatchManager
from exabox.infrapatching.utils.utility import runInfraPatchCommandsLocally, mReadPatcherInfo, mExaspliceVersionPatternMatch
from exabox.infrapatching.core.infrapatcherror import PATCH_SUCCESS_EXIT_CODE, PATCHMGR_SESSION_ALREADY_EXIST, NO_PATCHMGR_RESPONSE_DETECTED_ON_DOMU, NO_PATCHMGR_RESPONSE_DETECTED, PATCHMGR_COMMAND_FAILED, DOMU_PATCHMGR_COMMAND_FAILED, EXADATA_PATCHMGR_CONSOLE_READ_TIMEOUT_ERROR, EXADATA_PATCHMGR_CONSOLE_READ_TIMEOUT_ERROR
from exabox.infrapatching.utils.constants import PATCH_DOM0, PATCH_DOMU, PATCH_CELL, PATCH_IBSWITCH, PATCH_ROCESWITCH, PATCH_ADMINSWITCH, STEP_CLEAN_UP, TASK_PREREQ_CHECK, TASK_PATCH, TASK_ROLLBACK_PREREQ_CHECK, TASK_ROLLBACK, TASK_BACKUP_IMAGE, OP_STYLE_ROLLING, OP_BACKUPMODE_NO, RETRY_PATCHMGR_PROCESS_COMPLETION_CHECK_MAX_COUNTER_VALUE, RETRY_PATCH_NOTIFICATION_CHECK_MAX_COUNTER_VALUE, WAIT_PATCH_NOTIFICATION_DIRECTORY_TIMEOUT_IN_SECONDS, WAIT_FOR_PATCHSUCCESSEXIT_IN_SECONDS

sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))

class InfraPatchManager(PatchManager):

    def __init__(self, aTarget, aOperation, aPatchBaseAfterUnzip, aLogPathOnLaunchNode, aHandler):
        super(InfraPatchManager, self).__init__(aTarget=aTarget, aOperation=aOperation, aPatchBaseAfterUnzip=aPatchBaseAfterUnzip, aLogPathOnLaunchNode=aLogPathOnLaunchNode, aHandler=aHandler)
        self.mPatchLogInfo("InfraPatchManager")

    def mGetNodesToBePatchedFile(self):
        return os.path.join(self.mGetPatchBaseAfterUnzip(), self.mGetHandler().mGetDbNodesFileName())

    def mGetListOfSwitchesToBePatchedWithAppropriateTagsFile(self):
        return os.path.join(self.mGetPatchBaseAfterUnzip(), f"{self.mGetHandler().mGetMasterReqId()}.txt")

    def mCreateNodesToBePatchedFile(self, aLaunchNode, aHostList, aExclude=""):
        """
        Creates the input file with the list of nodes to be patched.
        """

        _nodes_to_be_patched_file = self.mGetNodesToBePatchedFile()
        self.mPatchLogInfo(f"Creating patch input file: {_nodes_to_be_patched_file}")
        aHostList.sort()

        #
        # When CPS or Management host is used as the launch node, we need to pass NAT domu hostname
        # to patchmgr, since customer hostname cannot be pinged from launch node
        #
        _h_list = [_h for _h in aHostList if _h != aExclude]
        if self.mGetHandler().mGetInfrapatchExecutionValidator().mCheckCondition('mIsCpsLaunchNodeForDomU'):
            _nat_remote_node_list = [self.mGetHandler().mGetDomUNatHostNameforDomuCustomerHostName(_domu_name) \
                                     for _domu_name in _h_list]
            _h_list = _nat_remote_node_list
            self.mPatchLogInfo("Create node list: %s" % _h_list)
            _cmd_list = (["echo", "\\n".join(_h_list)], ["tee", _nodes_to_be_patched_file])
            runInfraPatchCommandsLocally(_cmd_list)
        else:
            _node = exaBoxNode(get_gcontext())
            self.mGetHandler().mSetConnectionUser(_node)
            _node.mConnect(aHost=aLaunchNode)
            if self.mGetHandler().mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForDomuOrClusterless'):
                if self.mGetTarget() == PATCH_DOMU:
                    _nat_remote_node_list = [self.mGetHandler().mGetDomUNatHostNameforDomuCustomerHostName(_domu_name) \
                                         for _domu_name in _h_list]
                    _h_list = _nat_remote_node_list
                self.mPatchLogInfo("Create node list: %s" % _h_list)
                _node.mExecuteCmdLog('printf "%s" | sudo tee  %s' % ("\\n".join(_h_list), _nodes_to_be_patched_file))
            else:
                self.mPatchLogInfo("Create node list: %s" % _h_list)
                _node.mExecuteCmdLog('printf "%s" > %s' % ("\\n".join(_h_list), _nodes_to_be_patched_file))

            if _node.mIsConnected():
                _node.mDisconnect()

        self.mSetNodesToBePatchedFile(aNodesToBePatchedFile=_nodes_to_be_patched_file)
        return _nodes_to_be_patched_file

    
    def mGetNodeListFromNodesToBePatchedFile(self, aHost=None):
        """
         Get the list of nodes from the nodes to be patched file
         aHost is mandatory except for cps as launch node
        """
        _output = []
        _node = None
        _file_output = []
        _file_path = self.mGetNodesToBePatchedFile()
        try:
            # block specific to getting the file contents. 
            # even if there is a failure doing this... execution of the patchmgr cmd should continue as it was before
            if self.mGetHandler().mGetInfrapatchExecutionValidator().mCheckCondition('mIsCpsLaunchNodeForDomU'):
                _cmd_list = [['cat', _file_path]]
                _rc, _o = runInfraPatchCommandsLocally(_cmd_list)
                if _o:
                    _file_output = _o.split("\n")
            else:
                _node = exaBoxNode(get_gcontext())
                self.mGetHandler().mSetConnectionUser(_node=_node)
                _node.mConnect(aHost=aHost)
                _i, _o, _e = _node.mExecuteCmd(f"cat {_file_path}")
                _file_output = _o.readlines()
            if _file_output:
                for ln in _file_output:
                    _output.append(ln.replace("\n", "").strip())
        except Exception as e:
            self.mPatchLogError(traceback.format_exc())
        finally:
            if _node and _node.mIsConnected():
                _node.mDisconnect()
        return _output


    def __mGetPatchMgrTarget(self):
        """
         private method to get patchmgr target value for the current target
        """
        _patchmgr_target = None
        _target = self.mGetTarget()

        if _target in [PATCH_DOM0, PATCH_DOMU]:
            _patchmgr_target = "dbnodes"
        elif _target == PATCH_CELL:
            _patchmgr_target = "cells"
        elif _target == PATCH_IBSWITCH:
            _patchmgr_target = "ibswitches"
        elif _target == PATCH_ROCESWITCH:
            _patchmgr_target = "roceswitches"
        elif _target == PATCH_ADMINSWITCH:
            _patchmgr_target = "adminswitches"

        return _patchmgr_target


    def __mGetPatchMgrBaseCmd(self, aPrepareRoceVerifyCfgCmd=False):
        """
         private method to get patchmgr minimal base cmd
        """
        _patchmgr_base_command = None

        if not aPrepareRoceVerifyCfgCmd and self.mGetTarget() in [ PATCH_ROCESWITCH ]:
            _nodes_to_be_patched_file = self.mGetListOfSwitchesToBePatchedWithAppropriateTagsFile()
        else:
            _nodes_to_be_patched_file = self.mGetNodesToBePatchedFile()

        _patchmgr_target = self.__mGetPatchMgrTarget()

        _patchmgr_base_command = f"cd {self.mGetPatchBaseAfterUnzip()};"

        # For infra components, _nodes_to_be_patched_file name used instead of the full file path
        _nodes_to_be_patched_file_name = _nodes_to_be_patched_file.split("/")[-1]
        if self.mGetTarget() == PATCH_CELL and self.mGetOperation() == STEP_CLEAN_UP:
            if self.mGetHandler().mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForClusterless'):
                _patchmgr_base_command = f"{self.mGetPatchBaseAfterUnzip()}/patchmgr"
                _nodes_to_be_patched_file_name = _nodes_to_be_patched_file
            else:
                _patchmgr_base_command += f"./patchmgr"
        elif self.mGetTarget() in [ PATCH_ROCESWITCH ] and aPrepareRoceVerifyCfgCmd:
            '''
             Since Roceswitch patch verify command is light weight and the exit status is required to
             determine if the input file is valid and environment is as per configuration. It should 
             not be run in nohup or in background.
            '''
            _patchmgr_base_command += f"./patchmgr"
        else:
            _patchmgr_base_command += f" nohup ./patchmgr"

            if self.mGetTarget() in [ PATCH_DOMU, PATCH_DOM0, PATCH_CELL ]:
                # For domu management host or cps host as launch node, patchmgr cmd with full path used while executing
                if self.mGetHandler().mGetInfrapatchExecutionValidator().mCheckCondition('mIsCpsLaunchNodeForDomU'):
                    _patchmgr_base_command = f"sudo nohup {self.mGetPatchBaseAfterUnzip()}/patchmgr"
                    _nodes_to_be_patched_file_name = _nodes_to_be_patched_file
                elif self.mGetHandler().mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForDomuOrClusterless'):
                    _patchmgr_base_command = f"nohup {self.mGetPatchBaseAfterUnzip()}/patchmgr"
                    _nodes_to_be_patched_file_name = _nodes_to_be_patched_file


        _patchmgr_base_command += f" --{_patchmgr_target} {_nodes_to_be_patched_file_name}"
        
        return _patchmgr_base_command

    def mGetPatchMgrCmd(self, aPrepareRoceVerifyCfgCmd=False):
        """
         one consolidated api exposed to get patchmgr cmd for 
         various targets and its corresponding operations
        """
        _patchmgr_command = None
        _target = self.mGetTarget()
        _patchmgr_base_command = self.__mGetPatchMgrBaseCmd(aPrepareRoceVerifyCfgCmd=aPrepareRoceVerifyCfgCmd)

        if _target in [PATCH_DOM0, PATCH_DOMU]:
            if self.mGetHandler().mIsElu() and self.mGetApplyOutstandingWorkDuringEluPatchFlag():
                _patchmgr_command = self.__mRebootApplyOutstandingWorkDuringElu(aPatchMgrBaseCommand=_patchmgr_base_command)
            else:
                _patchmgr_command = self.__mGetDom0DomUPatchMgrCmd(aPatchMgrBaseCommand=_patchmgr_base_command)
        elif _target == PATCH_CELL:
            _patchmgr_command = self.__mGetCellPatchMgrCmd(aPatchMgrBaseCommand=_patchmgr_base_command)
        elif _target == PATCH_IBSWITCH:
            _patchmgr_command = self.__mGetIBSwitchPatchMgrCmd(aPatchMgrBaseCommand=_patchmgr_base_command)
        elif _target == PATCH_ROCESWITCH:
            if aPrepareRoceVerifyCfgCmd:
                _patchmgr_command = self.__mGetPatchmgrRoceVerifyConfigCmd(aPatchMgrBaseCommand=_patchmgr_base_command)
            else:
                _patchmgr_command = self.__mGetRoceSwitchPatchMgrCmd(aPatchMgrBaseCommand=_patchmgr_base_command)
        elif _target == PATCH_ADMINSWITCH:
            _patchmgr_command = self.__mGetAdminSwitchPatchMgrCmd(aPatchMgrBaseCommand=_patchmgr_base_command)

        # patchmgr cmd is ready for execution. return to the caller
        self.mPatchLogInfo(f"\n\nFor rack={self.mGetHandler().mGetRackName()} target={_target} op={self.mGetOperation()} patchmgr command prepared for execution is: \n\n{_patchmgr_command}\n")

        return _patchmgr_command

    def __mGetDom0DomUPatchMgrCmd(self, aPatchMgrBaseCommand):
        """
         private method to get dom0 patchmgr cmd
        """
        _patchmgr_command = aPatchMgrBaseCommand

        _operation = self.mGetOperation()
        _log_path_on_launch_node = self.mGetLogPathOnLaunchNode()

        if _operation == TASK_PREREQ_CHECK:
            _patchmgr_operation = "precheck"
        elif _operation == TASK_PATCH:
            _patchmgr_operation = "upgrade"
        elif _operation == TASK_ROLLBACK:
            _patchmgr_operation = "rollback"
        elif _operation == TASK_BACKUP_IMAGE:
            _patchmgr_operation = "backup"

        _patchmgr_command += f" --{_patchmgr_operation}"

        if _operation in [TASK_PREREQ_CHECK, TASK_PATCH]:
            if self.mGetTarget() in [ PATCH_DOM0, PATCH_DOMU ] and self.mIsExaSpliceEnabled():
                if mExaspliceVersionPatternMatch(self.mGetTargetVersion()):
                    _patchmgr_command += f" --exasplice_repo {self.mGetIsoRepo()}"
                else:
                    _patchmgr_command += f" --repo {self.mGetIsoRepo()}"
                    _patchmgr_command += f" --target_version {self.mGetTargetVersion()}"
                    if self.mGetTarget() == PATCH_DOM0:
                        _patchmgr_command += f" --live-update-target allcvss"
                        if _operation in [TASK_PATCH]:
                            _patchmgr_command += f" --live-update-schedule-outstanding-work never"
                    elif self.mGetTarget() == PATCH_DOMU:
                        '''
                         In case of Domu patching, valid cases are
                         highcvss, allcvss, full, applypending.
                        '''
                        if self.mGetHandler().mGetEluOptions():
                            _patchmgr_command += f" --live-update-target {self.mGetHandler().mGetEluOptions()}"
            else:
                if self.mGetHandler().mGetInfrapatchExecutionValidator().mCheckCondition('mIsSingleDomUVMCluster') or self.mGetHandler().mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForDomuOrClusterless'):
                    _patchmgr_command += f" --iso_repo {self.mGetPatchBaseAfterUnzip()}{self.mGetIsoRepo()}"
                else:
                    _patchmgr_command += f" --iso_repo {self.mGetIsoRepo()}"
                _patchmgr_command += f" --target_version {self.mGetTargetVersion()}"

        if _operation in [TASK_PATCH, TASK_ROLLBACK]:
            if self.mGetOperationStyle() == OP_STYLE_ROLLING:
                _patchmgr_command += " --rolling"

            if _operation == TASK_PATCH:
                # Perform system consistency check only during patch operation.
                if not self.mGetSystemConsistencyState():
                    '''
                     In case of system consistency fails,
                      - skip taking backup and validate for successful upgrade completion.
                      - Append -nobackup option to patch upgrade command to skip backup
                    '''
                    self.mPatchLogInfo("System consistency check during upgrade operation failed. Running upgrade operation with -nobackup option.")
                    _patchmgr_command += " --nobackup"
                else:
                    # Default option with patchmgr on dom0U is to take backup. If
                    # specified not to take backup, then do the same for upgrade only.
                    if self.mGetHandler().mGetBackUpMode() == OP_BACKUPMODE_NO:
                        _patchmgr_command += " --nobackup"

        _patchmgr_command += f" --log_dir {_log_path_on_launch_node}"
        _patchmgr_command += self.mGetHandler().mCheckAdditionalOptions('', _operation, self.mGetTarget())

        if self.mGetTarget() == PATCH_DOMU:
            if self.mGetHandler().mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForDomU'):
                _patchmgr_command += f" </dev/null | sudo tee {self.mGetPatchMgrConsoleOutputFile()} &"
            elif not self.mGetHandler().mGetInfrapatchExecutionValidator().mCheckCondition('mIsCpsLaunchNodeForDomU'):
                # For cps as launch node, console log file details specified at the time of patchmgr cmd execution in __mExecuteLocalNodePatchMgrCmd
                _patchmgr_command += f" </dev/null &> {self.mGetPatchMgrConsoleOutputFile()} &"
        else:
            if self.mGetHandler().mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForClusterless'):
                _patchmgr_command += f" </dev/null | sudo tee {self.mGetPatchMgrConsoleOutputFile()} &"
            else:
                _patchmgr_command += f" </dev/null &> {self.mGetPatchMgrConsoleOutputFile()} &"

        return _patchmgr_command

    def __mRebootApplyOutstandingWorkDuringElu(self, aPatchMgrBaseCommand):
        """
         private method to get dom0 patchmgr cmd to apply
         outstanding items.
        """
        _patchmgr_command = aPatchMgrBaseCommand
        _log_path_on_launch_node = self.mGetLogPathOnLaunchNode()

        _patchmgr_command += f" --live-update-reboot-apply-outstanding-work"
        _patchmgr_command += f" --log_dir {_log_path_on_launch_node}"

        if self.mGetTarget() == PATCH_DOMU:
            if self.mGetHandler().mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForDomU'):
                _patchmgr_command += f" </dev/null | sudo tee {self.mGetPatchMgrConsoleOutputFile()} &"
            elif not self.mGetHandler().mGetInfrapatchExecutionValidator().mCheckCondition('mIsCpsLaunchNodeForDomU'):
                # For cps as launch node, console log file details specified at the time of patchmgr cmd execution in __mExecuteLocalNodePatchMgrCmd
                _patchmgr_command += f" </dev/null &> {self.mGetPatchMgrConsoleOutputFile()} &"
        else:
            if self.mGetHandler().mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForClusterless'):
                _patchmgr_command += f" </dev/null | sudo tee {self.mGetPatchMgrConsoleOutputFile()} &"
            else:
                _patchmgr_command += f" </dev/null &> {self.mGetPatchMgrConsoleOutputFile()} &"

        return _patchmgr_command

    def __mGetCellPatchMgrCmd(self, aPatchMgrBaseCommand):
        """
         private method to get cell patchmgr cmd
        """
        _patchmgr_command = aPatchMgrBaseCommand

        _operation = self.mGetOperation()
        _log_path_on_launch_node = self.mGetLogPathOnLaunchNode()

        if _operation == TASK_PREREQ_CHECK:
            _patchmgr_operation = "patch_check_prereq"
        elif _operation == TASK_PATCH:
            _patchmgr_operation = "patch"
        elif _operation == TASK_ROLLBACK_PREREQ_CHECK:
            _patchmgr_operation = "rollback_check_prereq"
        elif _operation == TASK_ROLLBACK:
            _patchmgr_operation = "rollback"
        elif _operation == STEP_CLEAN_UP:
            _patchmgr_operation = "cleanup"

        _patchmgr_command += f" --{_patchmgr_operation} --log_dir {_log_path_on_launch_node}"

        if _operation not in [STEP_CLEAN_UP]:
            if self.mGetOperationStyle() == OP_STYLE_ROLLING:
                _patchmgr_command += " --rolling"        
            _patchmgr_command += self.mGetHandler().mCheckAdditionalOptions('', _operation, self.mGetTarget())
            if self.mGetHandler().mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForClusterless'):
                _patchmgr_command += f" </dev/null | sudo tee {self.mGetPatchMgrConsoleOutputFile()} &"
            else:
                _patchmgr_command += f" </dev/null &> {self.mGetPatchMgrConsoleOutputFile()} &"

        return _patchmgr_command


    def __mGetIBSwitchPatchMgrCmd(self, aPatchMgrBaseCommand):
        """
         private method to get ibswitch patchmgr cmd
        """
        _patchmgr_command = aPatchMgrBaseCommand

        _operation = self.mGetOperation()
        _log_path_on_launch_node = self.mGetLogPathOnLaunchNode()

        if _operation == TASK_PREREQ_CHECK:
            _patchmgr_operation = "upgrade -ibswitch_precheck -force"
        elif _operation == TASK_PATCH:
            _patchmgr_operation = "upgrade -force"
        elif _operation == TASK_ROLLBACK_PREREQ_CHECK:
            _patchmgr_operation = "downgrade -ibswitch_precheck -force"
        elif _operation == TASK_ROLLBACK:
            _patchmgr_operation = "downgrade -force"

        _patchmgr_command += f" --{_patchmgr_operation}"
        _patchmgr_command += f" --log_dir {_log_path_on_launch_node}"
        _patchmgr_command += f" </dev/null &> {self.mGetPatchMgrConsoleOutputFile()} &"

        return _patchmgr_command

    def __mGetRoceSwitchPatchMgrCmd(self, aPatchMgrBaseCommand):
        """
         private method to get roceswitch patchmgr cmd
        """
        _patchmgr_command = aPatchMgrBaseCommand

        _operation = self.mGetOperation()
        _log_path_on_launch_node = self.mGetLogPathOnLaunchNode()

        if _operation == TASK_PREREQ_CHECK:
            _patchmgr_operation = "upgrade --roceswitch-precheck"
        elif _operation == TASK_PATCH:
            _patchmgr_operation = "upgrade"
        elif _operation == TASK_ROLLBACK_PREREQ_CHECK:
            _patchmgr_operation = "downgrade --roceswitch-precheck"
        elif _operation == TASK_ROLLBACK:
            _patchmgr_operation = "downgrade"

        _patchmgr_command += f" --{_patchmgr_operation}"
        if self.mGetHandler().mGetRevokeRoceswitchPasswdlessSshSettings():
            '''
             Pass unkey option to patchmgr only if REVOKE_ROCESWITCH_PASSWDLESS_SSH 
             is set to True in constants.py. 

             By default passwdless ssh between dom0 and roceswitch is not 
             revoked post patching. To revoke passwordless ssh, 
             revoke_roceswitch_passwdless_ssh_settings must be set to True 
             in infrapatching.conf
            '''
            _patchmgr_command += " --unkey"

        _patchmgr_command += f" --log_dir {_log_path_on_launch_node}"
        _patchmgr_command += f" </dev/null &> {self.mGetPatchMgrConsoleOutputFile()} &"

        return _patchmgr_command

    def __mGetPatchmgrRoceVerifyConfigCmd(self, aPatchMgrBaseCommand):
        """
         private method to get roceswitch verify config patchmgr cmd
         This command is not run in nohup or in background as the exit
         status is required to determine of the configuration of switches
         are correct.
        """
        _patchmgr_command = aPatchMgrBaseCommand
        _currenttime = (datetime.datetime.now()).strftime("%Y-%m-%d_%H_%M_%S")

        _operation = self.mGetOperation()
        _log_path_on_launch_node = self.mGetLogPathOnLaunchNode()

        _patchmgr_command += f" --verify-config --newswitchlist {self.mGetHandler().mGetMasterReqId()}.txt"
        '''
         In case of a patchmgr verify command failure, there is a possibility of
         a retry of verify command run post appending the required tag details to
         switch list file. To distinguish both the verify config iteration runs, 
         timestamp is appended to verify config command. 
        '''
        _patchmgr_command += f" --log_dir {_log_path_on_launch_node}_{_currenttime}"

        return _patchmgr_command

    def __mGetAdminSwitchPatchMgrCmd(self, aPatchMgrBaseCommand):
        """
         private method to get Admin switch patchmgr cmd
        """
        _patchmgr_command = aPatchMgrBaseCommand

        _operation = self.mGetOperation()
        _log_path_on_launch_node = self.mGetLogPathOnLaunchNode()

        if _operation == TASK_PREREQ_CHECK:
            _patchmgr_operation = "upgrade --adminswitch-precheck"
        elif _operation == TASK_PATCH:
            _patchmgr_operation = "upgrade"
        elif _operation == TASK_ROLLBACK_PREREQ_CHECK:
            _patchmgr_operation = "downgrade --adminswitch-precheck"
        elif _operation == TASK_ROLLBACK:
            _patchmgr_operation = "downgrade"

        _patchmgr_command += f" --{_patchmgr_operation}"
        if self.mGetHandler().mGetRevokeRoceswitchPasswdlessSshSettings():
            '''
             Pass unkey option to patchmgr only if REVOKE_ROCESWITCH_PASSWDLESS_SSH 
             is set to True in constants.py. 

             By default passwdless ssh between dom0 and admin switch is not 
             revoked post patching. To revoke passwordless ssh, 
             revoke_roceswitch_passwdless_ssh_settings must be set to True 
             in infrapatching.conf
            '''
            _patchmgr_command += " --unkey"

        _patchmgr_command += f" --log_dir {_log_path_on_launch_node}"
        _patchmgr_command += f" </dev/null &> {self.mGetPatchMgrConsoleOutputFile()} &"

        return _patchmgr_command

    def mExecutePatchMgrCmd(self, aPatchMgrCmd, aPrepareRoceVerifyCfgCmd=False):
        """
          This method helps create a log directory prior to running a patchmgr
            and starts the command in nohup mode
          aPatchMgrCmd - patchmgr command being executed

          return
           PATCH_SUCCESS_EXIT_CODE - if notification directory was created
           and patchmgr session is running.
           
           DOMU_PATCHMGR_COMMAND_FAILED - otherwise(In case of DomU target)
           PATCHMGR_COMMAND_FAILED - otherwise(In case of Dom0, Cell and Switches)
        """

        if self.mGetTarget() == PATCH_DOMU and self.mGetHandler().mGetInfrapatchExecutionValidator().mCheckCondition('mIsCpsLaunchNodeForDomU'):
            self.__mExecuteLocalNodePatchMgrCmd(aPatchMgrCmd=aPatchMgrCmd)
            return


        _rack_name = self.mGetHandler().mGetRackName()
        _target = self.mGetTarget()
        _operation = self.mGetOperation()
        _launch_node = self.mGetLaunchNode()
        _log_path_on_launch_node = self.mGetLogPathOnLaunchNode()
        _node_list_from_nodes_file = self.mGetNodeListFromNodesToBePatchedFile(aHost=_launch_node)

        self.mGetHandler().mUpdateCurrentLaunchNodeDetailsInCorrespondingTaskHandlerInstance(_launch_node, _log_path_on_launch_node)
        _ret = PATCH_SUCCESS_EXIT_CODE
        _exit_code = PATCH_SUCCESS_EXIT_CODE

        _node = exaBoxNode(get_gcontext())
        self.mGetHandler().mSetConnectionUser(_node=_node)
        _user = _node.mGetUser()
        try:
            _node.mConnect(aHost=_launch_node)
            if _user == 'opc':
                _cmd = "mkdir "+_log_path_on_launch_node
                _node.mExecuteCmd(_cmd)
            else: 
                _node.mMakeDir(_log_path_on_launch_node)

            self.mPatchLogInfo(f"\n\n-----------\n For rack={_rack_name}, patchmgr session will be executed with the following details -- \n Rack Name -- {_rack_name}\n Target Type -- {_target}\n Patch Operation -- {_operation}\n Launch Node using for patching -- {_launch_node}\n Patchmgr log location on Launch Node -- {_log_path_on_launch_node}\n Patchmgr command running in the background --\n\t\t {aPatchMgrCmd}\n-----------\n\n")

            # print the node list details.
            self.mPatchLogInfo(f"Printing the node list file details before patchmgr command is run - {self.mGetNodesToBePatchedFile()}.")
            _cmd_cat_console_log = f"cat {self.mGetNodesToBePatchedFile()}"
            _i, _o, _e = _node.mExecuteCmd(_cmd_cat_console_log)
            for _line in _o.readlines():
                self.mPatchmgrLogInfo(_line.strip())

            self.mPatchLogInfo(f"\n\n")

            # Execute patchmgr command
            _node.mExecuteCmdLog(aPatchMgrCmd)

            if aPrepareRoceVerifyCfgCmd and int(_node.mGetCmdExitStatus()) != 0:
                '''
                  Verify config can fail in some environements due to misconfiguration
                  during provisioning. Depending on the environment type, tags are added
                  to switch list files and verify config is run, so that the configuration
                  is correct and switch verify config is successful.
                '''
                self.mPatchLogInfo(f"verify config with the current input list is not successful. Tag details will be computed as part of infra patching and verify config will be retried.")
                self.mGenerateSwitchConfigsInCaseOfVerifyConfigFailure()
                self.mPatchLogInfo(f"\n\n-----------\n Patchmgr verify config command run in the second iteration with the updated tag details --\n\t\t {aPatchMgrCmd}\n-----------\n\n")
                _node.mExecuteCmdLog(aPatchMgrCmd)
                if int(_node.mGetCmdExitStatus()) != 0:
                    self.mPatchLogError("Verify config command not successful even after the tags were added to switch list file and re-run. Manual intervention required.")
                    self.mSetStatusCode(aStatusCode=PATCHMGR_COMMAND_FAILED)
                    return PATCHMGR_COMMAND_FAILED
                else:
                    self.mPatchLogInfo("Verify config command successful after the tags were added to switch list file and re-run.")
                
            # Notifications files are not generated in case of a
            # patchmgr verify config option specified.
            if aPrepareRoceVerifyCfgCmd:
                self.mSetStatusCode(aStatusCode=_exit_code)
                return _exit_code

            '''
              In case of Exacc environments, it is observed that there has been slight delays
              in exection of commands and as a result Infra patching either proceeds executing
              other commands in the list or terminates. Hence, loop though, sleep and check
              for existence. This check is necessary for all targets.
            '''
            _retry_check_for_folder_counter = RETRY_PATCH_NOTIFICATION_CHECK_MAX_COUNTER_VALUE
            _notifications_dir = os.path.join(_log_path_on_launch_node, "notifications")
            while _retry_check_for_folder_counter > 0:
                _file_exists = False
                if _user == 'opc':
                    _cmd = f"ls -l {_notifications_dir}"
                    _in, _out, _err = _node.mExecuteCmd(_cmd)
                    if _node.mGetCmdExitStatus() == 0:
                        _file_exists = True
                else:
                    _file_exists = _node.mFileExists(_notifications_dir)

                if _file_exists:
                    _cmd_list_dir = f"ls -l {_notifications_dir} | wc -l"
                    _in, _out, _err = _node.mExecuteCmd(_cmd_list_dir)
                    _output = _out.readlines()
                    if int(_output[0].strip()) > 0:
                        self.mPatchLogInfo(f"Patch notification log location exists : {_notifications_dir}")
                        break
                else:
                    self.mPatchLogWarn(
                        f"Patch notification log location : '{_notifications_dir}' does not exist. Checking again after {WAIT_PATCH_NOTIFICATION_DIRECTORY_TIMEOUT_IN_SECONDS} seconds")
                    time.sleep(WAIT_PATCH_NOTIFICATION_DIRECTORY_TIMEOUT_IN_SECONDS)
                    _retry_check_for_folder_counter -= 1
   
            '''
             In case of patchmgr command did not run, patch notification
             directory is not created. Since notification thread runs as an
             independent thread, it start polling and checking to read log 
             to update node progress details until timeout is reached.

             Patchmgr does not write exit status message in all error scenarios 
             into patchmgr console out file. Infra patching expects an exit staus 
             to terminate patch. Below code checks for the patchmgr 
             process to be not running in case of notification log is not
             generated and terminates patch to avoid unecessarily polling
             of notification thread until timeout.
            '''
            if not _file_exists and int(_retry_check_for_folder_counter) == 0:
                # Check patchmgr session existence
                _ret, _patchmgr_active_node = self.mCheckForPatchMgrSessionExistence(aUpdateExacloudDB=False)
                if _ret != PATCHMGR_SESSION_ALREADY_EXIST:
                    if _target == PATCH_DOMU:
                        _exit_code = NO_PATCHMGR_RESPONSE_DETECTED_ON_DOMU
                    else:
                        _exit_code = NO_PATCHMGR_RESPONSE_DETECTED
                    _suggestion_msg = f"Patch notification log location : '{_notifications_dir}' was not found on Node : {_launch_node} even after the timeout was reached. Infra patch request will be terminated."
                    self.mGetHandler().mAddError(_exit_code, _suggestion_msg)

        except Exception as e:
            if _target == PATCH_DOMU:
                _exit_code = NO_PATCHMGR_RESPONSE_DETECTED_ON_DOMU
            else:
                _exit_code = NO_PATCHMGR_RESPONSE_DETECTED
            _suggestion_msg = f"Error while executing patchmgr commands on Node : {_launch_node}, Error : {str(e)}."
            self.mGetHandler().mAddError(_exit_code, _suggestion_msg)
            self.mPatchLogTrace(traceback.format_exc())
        finally:
            if _node.mIsConnected():
                _node.mDisconnect()
            return _exit_code


    def __mSaveNodeProgressStatusToDB(self, aRemoteNode=None, aFinalLastCns=False):
        """
        Reads the patchmgr notification xml data fron
        localhost in case of mIsCpsLaunchNodeForDomU else from launchnode for all other cases
        Updates the patchmgr node progress data to exacloud database
        """

        # get the patchmgr node progress data from notification xml file
        _patchmgr_notification_xml_data = None

        try:
            _patchmgr_notification_xml_loc = None
            _patchmgr_log_dir = self.mGetLogPathOnLaunchNode()
            _patchmgr_notification_xml_path_cmd = f"ls -t {_patchmgr_log_dir}/notifications/notification_patchmgr* | head -1"
            _suggested_failure_msg = f"Failed to get patchmgr notification xml file with cmd {_patchmgr_notification_xml_path_cmd} on launchnode {self.mGetLaunchNode()}"

            # get patchmgr notification xml file location
            self.mPatchLogTrace('__mSaveNodeProgressStatusToDB: Get the patchmgr notification xml data...')
            if self.mGetHandler().mGetInfrapatchExecutionValidator().mCheckCondition('mIsCpsLaunchNodeForDomU'):
                _patchmgr_notification_xml_path_cmd = f"{_patchmgr_log_dir}/notifications/notification_patchmgr*"
                _files = glob.glob(_patchmgr_notification_xml_path_cmd)
                if len(_files) > 0:
                    _patchmgr_notification_xml_loc = _files[0]
                else:
                    _suggested_failure_msg = f"Failed to get patchmgr notification xml file under {_patchmgr_notification_xml_path_cmd} on localhost"
            else:
                _i, _o, _e = aRemoteNode.mExecuteCmd(_patchmgr_notification_xml_path_cmd)
                _patchmgr_notification_xml_loc = _o.read().strip('\n')

            if _patchmgr_notification_xml_loc:
                # read the content of patchmgr notification xml file
                _read_patchmgr_xml_cmd = f"cat {_patchmgr_notification_xml_loc} 2>/dev/null"
                if self.mGetHandler().mGetInfrapatchExecutionValidator().mCheckCondition('mIsCpsLaunchNodeForDomU'):
                    _read_patchmgr_xml_cmd_list = []
                    _read_patchmgr_xml_cmd_list.append(['cat', _patchmgr_notification_xml_loc])
                    _rc, _o = runInfraPatchCommandsLocally(_read_patchmgr_xml_cmd_list)
                    _patchmgr_notification_xml_data = _o
                else:
                    if aRemoteNode.mFileExists(_patchmgr_notification_xml_loc):
                        _i, _o, _e = aRemoteNode.mExecuteCmd(_read_patchmgr_xml_cmd)
                        _patchmgr_notification_xml_data = _o.read()
            else:
                self.mPatchLogTrace(f"__mSaveNodeProgressStatusToDB: {_suggested_failure_msg}")

        except Exception as e:
            self.mPatchLogWarn(f"__mSaveNodeProgressStatusToDB: Failed to get the patch notification xml data: {str(e)}\n")
            self.mPatchLogTrace(traceback.format_exc())

        # save patchmgr node progress data into database
        if _patchmgr_notification_xml_data:
            self.mPatchLogTrace('__mSaveNodeProgressStatusToDB: Preparing patch report JSON with patchmgr notification xml data...')
            _patch_report_json = {}
            try:
                # Parse patchmgr notification details and prepare the patch report json
                self.mPatchLogTrace('__mSaveNodeProgressStatusToDB: Invoking mParsePatchmgrXml to get the patch report JSON...')
                _patch_report_json = self.mGetHandler().mParsePatchmgrXml(_patchmgr_notification_xml_data, aFinalLastCns)
            except Exception as e:
                self.mPatchLogError(f"__mSaveNodeProgressStatusToDB: Failed to get the patch report JSON: {str(e)}")
                self.mPatchLogTrace(traceback.format_exc())

            try:
                # Save patch report json to database
                self.mPatchLogTrace('__mSaveNodeProgressStatusToDB: Invoking mUpdateCnsJsonPayload to save patch report json to database...')
                self.mGetHandler().mUpdateCnsJsonPayload(_patch_report_json)
            except Exception as e:
                self.mPatchLogWarn(f"__mSaveNodeProgressStatusToDB: Failed to save patch report JSON to database: {str(e)}")
                self.mPatchLogTrace(traceback.format_exc())
        else:
            self.mPatchLogTrace('__mSaveNodeProgressStatusToDB: Patchmgr notification xml not yet populated hence skipping preparing patch report JSON!')


    def mWaitForPatchMgrCmdExecutionToComplete(self, aInputListFile=None, aPatchStates=None):
        """
         Here we connect to the launch node and try to check for progress reading
          Patchmgr Console out file. It returns:

             zero     --> when patchmgr end with success
             non-zero --> when patchmgr end with failure

          Since the patchmgr is run in the background using nohup, the below section
           of code monitors the log file for completion and returns the exit status of the
          patchmgr command.
        """

        if self.mGetTarget() == PATCH_DOMU and self.mGetHandler().mGetInfrapatchExecutionValidator().mCheckCondition('mIsCpsLaunchNodeForDomU'):
            self.__mWaitForLocalPatchMgrCmdExecutionToComplete(aInputListFile=aInputListFile, aPatchStates=aPatchStates)
            return


        _launch_node = self.mGetLaunchNode()
        _log_path_on_launch_node = self.mGetLogPathOnLaunchNode()
        _target = self.mGetTarget()
        _operation = self.mGetOperation()
        _rack_name = self.mGetHandler().mGetRackName()

        self.mPatchLogInfo(f"Read patchmgr console from node = {_launch_node} and log loc = {_log_path_on_launch_node}")

        self.mPatchLogInfo("\n\n--------> Patchmgr output starts here <--------\n")
        _node = exaBoxNode(get_gcontext())
        self.mGetHandler().mSetConnectionUser(_node=_node)
        _node.mConnect(aHost=_launch_node)
        _patch_mgr_run = True
        _patchmgr_prev = None
        _elapsed_time_in_sec = 0
        _nodes_already_upgraded = []
        _exit_code = PATCHMGR_COMMAND_FAILED
        _count_of_nodes = 0
        _finished_d = 0
        _patchmgr_timeout_in_sec = 0
        _patchmgr_console_output_file = self.mGetPatchMgrConsoleOutputFile()

        if _target == PATCH_DOMU:
            _exit_code = DOMU_PATCHMGR_COMMAND_FAILED

        if aInputListFile:
            _finished_nodes = 0
            _count_of_nodes = self.mGetHandler().mGetNodeCount(_launch_node, aInputListFile)
            self.mPatchLogInfo(
                f"**** [ Nodes already upgraded / Total number of Nodes ] : [ {_finished_d:d} / {_count_of_nodes:d} ]")
            self.mGetHandler().mUpdateRequestStatusFromList(True, aPatchStates, f"[0/{_count_of_nodes:d}]_{_rack_name}")

        _patchmgr_find = f"egrep -i 'Working|SUCCESS|INFO' {_patchmgr_console_output_file} | tail -1 | cut -d'[' -f3,4,5 | cut -d':' -f2,3,4,5 | sed -E 's/\]/->/g;/^$/d'"
        _patchmgr_seek = f'grep -i "Exit status" {_patchmgr_console_output_file}'
        _patchmgr_start_time = datetime.datetime.now()
        if self.mGetTimeoutInSeconds():
            _patchmgr_timeout_in_sec = self.mGetTimeoutInSeconds()
        else:
            _patchmgr_timeout_in_sec = self.mGetHandler().mGetExadataPatchmgrConsoleReadTimeoutSec()

        self.mPatchLogInfo(f"\nPatchmgr console logs can be found under {_launch_node}:{_patchmgr_console_output_file}\n")

        def _mWaitForPatchMgrSessionCompletion():
            """
             This method validates for any patchmgr sessions before proceeding
             with other patching tasks. If there are patchmgr sessions running,
             it waits for the patchmgr/dbnodeupdate session to complete.
            """

            # Check patchmgr session existence
            _ret, _patchmgr_active_node = self.mCheckForPatchMgrSessionExistence(aUpdateExacloudDB=False)
            if _ret == PATCHMGR_SESSION_ALREADY_EXIST:
                _retry_check_for_folder_counter = RETRY_PATCHMGR_PROCESS_COMPLETION_CHECK_MAX_COUNTER_VALUE
                _counter_to_display_iteration_count = 0
                while _retry_check_for_folder_counter > 0:
                    time.sleep(WAIT_FOR_PATCHSUCCESSEXIT_IN_SECONDS)
                    # Retry checking for patchmgr process existence.
                    _ret, _patchmgr_active_node = self.mCheckForPatchMgrSessionExistence(aUpdateExacloudDB=False)
                    _retry_check_for_folder_counter -= 1
                    _counter_to_display_iteration_count += 1
                    self.mPatchLogError(f"\n\nFor rack={_rack_name} target={_target} op={_operation} patchmgr session is still running. Polling for {_counter_to_display_iteration_count} iteration(s) of 10 seconds each for 60 seconds for the patchmgr command to complete.\n")
                    if _ret == PATCH_SUCCESS_EXIT_CODE or _retry_check_for_folder_counter == 0:
                        break
        while _patch_mgr_run and _elapsed_time_in_sec < _patchmgr_timeout_in_sec:

            # Notification xml files are monitored every 5 minutes for change in status,
            # Change in status to Success or Failure for any of the cells and ibswitches
            # requests table will be updated and update details are written into thread
            # logs.
       
            # We dont want to poll the PatchmgrConsole.out continously as it increases 
            # cpu usage, hence sleeping for certain time
            time.sleep(self.mGetHandler().mGetPatchmgrConsoleReadIntervalInSeconds())

            if aInputListFile and ( _elapsed_time_in_sec % 300 ) == 0:
                _input_status_file = f'{_log_path_on_launch_node}/notifications/notification_patchmgr_*_'
                _patch_filter_cmd = f"egrep -i 'NAME=' {_input_status_file} | cut -d'=' -f2 | tr -d '>'"
                _i, _o, _e = _node.mExecuteCmd(_patch_filter_cmd)
                _out_cellswitch_list = _o.readlines()
                for _out_celswitch_name in _out_cellswitch_list:
                    _out_celswitch_name = _out_celswitch_name.strip()
                    _patch_get_status = f"egrep -i -A 15 {_out_celswitch_name} {_input_status_file} | cut -d '\"' -f2,6 | sed 's/4\"//g; s/5\"//g' | egrep -i 'Succeeded|Failed' | tail -1 | awk '{{print $1}}'"
                    _i, _o, _e = _node.mExecuteCmd(_patch_get_status)
                    _out_get_status = _o.readlines()
                    for _output_get_status in _out_get_status:
                        _output_get_status = _output_get_status.strip()
                        if _out_celswitch_name not in _nodes_already_upgraded:
                            self.mPatchLogInfo(
                                f"**** Current status of Node : {_out_celswitch_name} -> {_output_get_status}")
                            _finished_d += 1
                            _nodes_already_upgraded.append(_out_celswitch_name)
                            self.mGetHandler().mUpdateRequestStatusFromList(True, aPatchStates,
                                                                            f"[{_finished_d:d}/{_count_of_nodes:d}]_{_rack_name}")
                            self.mPatchLogInfo(
                                f"**** [ Nodes already upgraded / Total number of Nodes ] : [ {_finished_d:d} / {_count_of_nodes:d} ]")

            _i, _o, _e = _node.mExecuteCmd(_patchmgr_find)
            _out = _o.readlines()
            for _output in _out:
                _output = _output.strip()
                if _patchmgr_prev != _output:
                    self.mPatchmgrLogInfo(f"{_output}")
                    _patchmgr_prev = _output

            # save patchmgr node progress data into database
            self.__mSaveNodeProgressStatusToDB(aRemoteNode=_node)

            _patch_progress_time = datetime.datetime.now()
            _elapsed_time_in_sec = int((_patch_progress_time - _patchmgr_start_time).total_seconds())

            _i, _o, _e = _node.mExecuteCmd(_patchmgr_seek)
            _exit_check = _node.mGetCmdExitStatus()
            _out = _o.readlines()

            if _exit_check == 0:
                _patch_mgr_run = False
                _cmd_get_summary = f"egrep -i 'ERROR|WARNING|For details, check the following files' -A 5 {_patchmgr_console_output_file} | egrep -vi 'Do not interrupt|Do not resize|Do not reboot|Do not open logfiles' | cut -d'[' -f3,4,5 | cut -d':' -f2,3,4,5 | sed -E 's/\]/->/g;/^$/d'"
                _i, _o, _e = _node.mExecuteCmd(_cmd_get_summary)
                _out_summary = _o.readlines()
                if _out_summary:
                    for _output_summary in _out_summary:
                        _output_summary = _output_summary.strip()
                        self.mPatchmgrLogInfo(_output_summary)

                for _output in _out:
                    self.mPatchmgrLogInfo(f"{_output}")
                    if "Exit status:0" in _output:
                        _exit_code = PATCH_SUCCESS_EXIT_CODE
                    else:
                        _suggestion_msg = f"Patchmgr command failed on Target : {str(self.mGetHandler().mGetTargetTypes())} for Patch Operation : {_operation}. Patchmgr logs are available on the node : {_launch_node} at location : {_log_path_on_launch_node}."
                        self.mGetHandler().mAddError(_exit_code, _suggestion_msg)

                    # Team preferred adding the final call to update the patchmgr notification status here which
                    # is closer to the patchmgr success/failure check
                    # There was also a suggestion to not to invoke this call from timeout block below as patchmgr
                    # status updated before to the timeout is the source of truth.
                    # Team also preferred to remove the calls from taskhandler files, which is an exit gate in the
                    # request completion flow as that requires computing launch node and extra logic to get patchmgr
                    # notification xml details

                    # save patchmgr node progress data into database
                    self.__mSaveNodeProgressStatusToDB(aRemoteNode=_node, aFinalLastCns=True)

                    self.mSetStatusCode(aStatusCode=_exit_code)

                    # Dump content of PatchmgrConsole.out at the end irrespective if success/failure
                    self.mPatchLogInfo(
                        f"\n\n --------> Start dumping entire patchmgr Console log at the end of patchMgr operation from {_launch_node}:{_log_path_on_launch_node} <--------\n\n")
                    _cmd_dump_console_log = f"cat {_patchmgr_console_output_file}"
                    _in, _op, _ex = _node.mExecuteCmd(_cmd_dump_console_log)
                    for _line in _op.readlines():
                        self.mPatchmgrLogInfo(_line.strip())
                    self.mPatchLogInfo(
                        f"\n\n --------> End dumping entire patchmgr Console log at the end of patchMgr operation from {_launch_node}:{_log_path_on_launch_node} <--------\n\n")

                    if _node.mIsConnected():
                        _node.mDisconnect()
                    self.mPatchLogInfo("\n\n--------> Patchmgr output ends here <--------\n")

                    # Wait for patchmgr session to complete.
                    _mWaitForPatchMgrSessionCompletion()
                    self.mSetCompleted(aCompleted=True)
                    # return to break the loop and exit the function
                    return

        '''
         In case of Exadata patchmgr timeout, Infra patching will terminate with
         exit code.

         EXADATA_PATCHMGR_CONSOLE_READ_TIMEOUT_ERROR requires action to be taken
         exacloud side/Operation team, hence it is by default retained as 
         PAGE_ONCALL
        '''
        if _elapsed_time_in_sec >= _patchmgr_timeout_in_sec:
            _exit_code = EXADATA_PATCHMGR_CONSOLE_READ_TIMEOUT_ERROR
            _suggestion_msg = f"Exadata Infra patching Timeout occurred after {_patchmgr_timeout_in_sec:d} seconds, Could not validate patch operation completion on launch node : {_launch_node}."
            self.mGetHandler().mAddError(_exit_code, _suggestion_msg)
            self.mSetStatusCode(aStatusCode=_exit_code)

        if _node.mIsConnected():
            _node.mDisconnect()


    def __mExecuteLocalNodePatchMgrCmd(self, aPatchMgrCmd):
        """
          This method helps create a log directory prior to running a patchmgr
            and starts the command in nohup mode
          aPatchMgrCmd - patchmgr command being executed
        """
        _rack_name = self.mGetHandler().mGetRackName()
        _target = self.mGetTarget()
        _operation = self.mGetOperation()
        _launch_node = self.mGetLaunchNode()
        _log_path_on_launch_node = self.mGetLogPathOnLaunchNode()

        _node_list_from_nodes_file = self.mGetNodeListFromNodesToBePatchedFile(aHost=_launch_node)
        self.mPatchLogInfo(f"\n\n-----------\n For rack={_rack_name}, patchmgr session will be executed on launch node={_launch_node} with the following details -- \n Target Type -- {_target}\n Patch Operation -- {_operation}\n Nodes to be patched file contents -- {_node_list_from_nodes_file}\n Patchmgr log location on Launch Node -- {_log_path_on_launch_node}\n Patchmgr command running in the background --\n\t\t {aPatchMgrCmd}\n-----------\n\n")

        self.mGetHandler().mUpdateCurrentLaunchNodeDetailsInCorrespondingLocalNodeTaskHandlerInstance(_log_path_on_launch_node)
        try:
            _cmd_list = []
            _cmd_list.append(['mkdir', '-p', _log_path_on_launch_node])
            runInfraPatchCommandsLocally(_cmd_list)

            _patch_mgr_cmd_list = aPatchMgrCmd.split()
            _cmd_list = []
            _cmd_list.append(_patch_mgr_cmd_list)
            _cmd_list.append(['tee', self.mGetPatchMgrConsoleOutputFile()])
            self.mPatchLogInfo(f"Patchmgr command {str(_cmd_list)}")
            _cmd_exec_first = subprocess.Popen(_cmd_list[0], stdout=subprocess.PIPE)
            subprocess.Popen(_cmd_list[1], stdin=_cmd_exec_first.stdout, stdout=subprocess.PIPE)
            
            '''
              In case of Exacc environments, it is observed that there has been slight delays
              in exection of commands and as a result Infra patching either proceeds executing
              other commands in the list or terminates. Hence, loop though, sleep and check
              for existence. This check is necessary for all targets.
            '''
            _retry_check_for_folder_counter = RETRY_PATCH_NOTIFICATION_CHECK_MAX_COUNTER_VALUE
            _notifications_dir = os.path.join(_log_path_on_launch_node, "notifications")
            while _retry_check_for_folder_counter > 0:
                if os.path.exists(_notifications_dir):
                    _cmd_list =[]
                    _cmd_list.append(['ls', '-l', _notifications_dir])
                    _cmd_list.append(['wc', '-l'])
                    _rc, _output = runInfraPatchCommandsLocally(_cmd_list)
                    if int(_output) > 0:
                        self.mPatchLogInfo(f"Patch notification log location exists : {_notifications_dir}")
                        break
                else:
                    self.mPatchLogWarn(
                        f"Patch notification log location : '{_notifications_dir}' does not exist. Checking again after {WAIT_PATCH_NOTIFICATION_DIRECTORY_TIMEOUT_IN_SECONDS} seconds")
                    time.sleep(WAIT_PATCH_NOTIFICATION_DIRECTORY_TIMEOUT_IN_SECONDS)
                    _retry_check_for_folder_counter -= 1
        except Exception as e:
            self.mPatchLogError(f"Error while executing patchmgr commands. \n\n {str(e)}")
            self.mPatchLogError(traceback.format_exc())


    def __mWaitForLocalPatchMgrCmdExecutionToComplete(self, aInputListFile=None, aPatchStates=None):
        """
         Here we connect to the launch node and try to check for progress reading
          Patchmgr Console out file. It returns:

             zero     --> when patchmgr end with success
             non-zero --> when patchmgr end with failure

          Since the patchmgr is run in the background using nohup, the below section
           of code monitors the log file for completion and returns the exit status of the
          patchmgr command.
        """

        _log_path_on_launch_node = self.mGetLogPathOnLaunchNode()
        _external_launch_node = self.mGetHandler().mGetExternalLaunchNode()

        self.mPatchLogInfo(
            f"Read patchmgr console from node = {str(_external_launch_node)} and log loc = {_log_path_on_launch_node}")

        self.mPatchLogInfo("\n\n--------> Patchmgr output starts here <--------\n")
        _patch_mgr_run = True
        _patchmgr_prev = None
        _elapsed_time_in_sec = 0
        _nodes_already_upgraded = []
        _exit_code = PATCHMGR_COMMAND_FAILED
        _count_of_nodes = 0
        _finished_d = 0
        _patchmgr_timeout_in_sec = self.mGetHandler().mGetExadataPatchmgrConsoleReadTimeoutSec()

        if self.mGetTarget() == PATCH_DOMU:
            _exit_code = DOMU_PATCHMGR_COMMAND_FAILED

        if aInputListFile is not None:
            _finished_nodes = 0
            _count_of_nodes = self.mGetHandler().mGetLocalNodeCount(aInputListFile)
            self.mPatchLogInfo(
                f"**** [ Nodes already upgraded / Total number of Nodes ] : [ {_finished_d:d} / {_count_of_nodes:d} ]")
            self.mGetHandler().mUpdateRequestStatusFromList(True, aPatchStates,
                                                            f"[0/{_count_of_nodes:d}]_{self.mGetHandler().mGetRackName()}")

        _seek_cmd_list = [['grep', '-i', 'Exit status', _log_path_on_launch_node+'/'+'PatchmgrConsole.out']]
        _patchmgr_start_time = datetime.datetime.now()

        self.mPatchLogInfo(
            f"\nPatchmgr console logs can be found under {str(_external_launch_node)}:{_log_path_on_launch_node}/PatchmgrConsole.out\n")


        def _mCheckForLocalNodePatchMgrSessionExistence(aUpdateExacloudDB=True):
            """
             This method checks for existing of patchmgr session.

             Return values:
              1) Non-zero (EB ERROR - 613) : One or more patchmgr sessions
                  OR
                 Zero: No patchmgr session are running
              2) In case of aUpdateExacloudDB set to False patchmgr
                 existence check is only required to be performed and not
                 update the exacloud DB as in such cases, there is an
                 existing error code on the Exacloud DB and do not want
                 error code from mCheckPatchmgrSessionExistence to overwite
                 the previous Error code.
            """

            def _patchmgr_session_hint():
                """
                 Return:
                   PATCHMGR_SESSION_ALREADY_EXIST : One or more patchmgr sessions are running or had patchmgr ran
                   PATCH_SUCCESS_EXIT_CODE        : No patchmgr sessions are running.
                """

                # Search of 'patchmgr -' in the grep command.
                _cmd_list = []
                _out = []
                _cmd_list.append(['ps', '-ef', 'patchmgr -'])
                _cmd_list.append(['grep', _log_path_on_launch_node])
                _cmd_list.append(['egrep', '-vi', 'grep|tail'])
                _rc, _o = runInfraPatchCommandsLocally(_cmd_list)
                if _o:
                    _out = _o.split("\n")
                if _log_path_on_launch_node in _out:
                    self.mPatchLogInfo(
                        f"The patchmgr session is active on this cluster. Patchmgr Active Node = '{str(_external_launch_node)}'.")
                    return PATCHMGR_SESSION_ALREADY_EXIST

                return PATCH_SUCCESS_EXIT_CODE

            # end of _patchmgr_session_hint

            ret = PATCH_SUCCESS_EXIT_CODE
            _patchmgr_session_active_node = None
            _log_path_on_launch_node = self.mGetLogPathOnLaunchNode()
            _external_launch_node = self.mGetHandler().mGetExternalLaunchNode()

            self.mPatchLogInfo(
                f"*** Checking for existence of patchmgr/dbnodeupdate.sh sessions in the cluster on the external launch node : {str(_external_launch_node)}.")

            # Find patchmgr session in the given list of nodes
            ret = _patchmgr_session_hint()
            if ret != PATCH_SUCCESS_EXIT_CODE:
                if aUpdateExacloudDB:
                    _suggestion_msg = f"Patchmgr session already exists on launch node : {str(_external_launch_node)}"
                    self.mGetHandler().mAddError(ret, _suggestion_msg)
                self.mPatchLogInfo(f"*** Patchmgr session found on {_external_launch_node}")
            return ret


        def _mWaitForLocalNodePatchMgrSessionCompletion():
            """
             This method validates for any patchmgr sessions before proceeding
             with other patching tasks. If there are patchmgr sessions running,
             it waits for the patchmgr/dbnodeupdate session to complete.
            """

            # Check patchmgr session existence
            _ret = _mCheckForLocalNodePatchMgrSessionExistence(aUpdateExacloudDB=False)
            if _ret == PATCHMGR_SESSION_ALREADY_EXIST:
                _retry_check_for_folder_counter = RETRY_PATCHMGR_PROCESS_COMPLETION_CHECK_MAX_COUNTER_VALUE
                _counter_to_display_iteration_count = 0
                while _retry_check_for_folder_counter > 0:
                    time.sleep(WAIT_FOR_PATCHSUCCESSEXIT_IN_SECONDS)
                    # Retry checking for patchmgr process existence.
                    _ret = _mCheckForLocalNodePatchMgrSessionExistence(aUpdateExacloudDB=False)
                    _retry_check_for_folder_counter -= 1
                    _counter_to_display_iteration_count += 1
                    self.mPatchLogError(
                        f"Patchmgr session is still running. Polling for {_counter_to_display_iteration_count:d} iteration(s) of 10 seconds each for 60 seconds for the patchmgr command to complete.")
                    if _ret == PATCH_SUCCESS_EXIT_CODE or _retry_check_for_folder_counter == 0:
                        break

        while _patch_mgr_run and _elapsed_time_in_sec < _patchmgr_timeout_in_sec:

            # Notification xml files are monitored every 5 minutes for change in status,
            # Change in status to Success or Failure for any of the cells and ibswitches
            # requests table will be updated and update details are written into thread
            # logs.

            # We dont want to poll the PatchmgrConsole.out continously as it increases 
            # cpu usage, hence sleeping for certain time
            time.sleep(self.mGetHandler().mGetPatchmgrConsoleReadIntervalInSeconds())

            if aInputListFile is not None and (_elapsed_time_in_sec % 300) == 0:
                _input_status_file = f'{_log_path_on_launch_node}/notifications/notification_patchmgr_*_'
                _patch_filter_cmd_list = []
                _patch_filter_cmd_list.append(['egrep', '-i', '\'NAME=\'', _input_status_file])
                _patch_filter_cmd_list.append(['cut', '-d\'=\'', '-f2'])
                _patch_filter_cmd_list.append(['tr', '-d', '\'>\''])
                _rc, _o = runInfraPatchCommandsLocally(_patch_filter_cmd_list)

                _out_cellswitch_list = _o.split("\n")
                for _out_celswitch_name in _out_cellswitch_list:
                    _out_celswitch_name = _out_celswitch_name.strip()
                    _patch_get_status_cmd_list = []
                    _patch_get_status_cmd_list.append(['egrep', '-i', '-A 15', _out_celswitch_name, _input_status_file]) 
                    _patch_get_status_cmd_list.append(['cut', '-d', '\'\"\'', '-f2,6'])
                    _patch_get_status_cmd_list.append(['sed', '\'s/4\"//g; s/5\"//g\''])
                    _patch_get_status_cmd_list.append(['egrep', '-i', '\'Succeeded|Failed\''])
                    _patch_get_status_cmd_list.append(['tail', '-1'])
                    _patch_get_status_cmd_list.append(['awk', '\'{print $1}\''])
                    _rc, _o = runInfraPatchCommandsLocally(_patch_get_status_cmd_list)

                    _out_get_status = _o.split("\n")
                    for _output_get_status in _out_get_status:
                        _output_get_status = _output_get_status.strip()
                        if _out_celswitch_name not in _nodes_already_upgraded:
                            self.mPatchLogInfo(
                                f"**** Current status of Node : {_out_celswitch_name} -> {_output_get_status}")
                            _finished_d += 1
                            _nodes_already_upgraded.append(_out_celswitch_name)
                            self.mGetHandler().mUpdateRequestStatusFromList(True, aPatchStates,
                                                                            f"[{_finished_d:d}/{_count_of_nodes:d}]_{self.mGetHandler().mGetRackName()}")
                            self.mPatchLogInfo(
                                f"**** [ Nodes already upgraded / Total number of Nodes ] : [ {_finished_d:d} / {_count_of_nodes:d} ]")

            _cmd_list_patchmgr_find = []
            _cmd_list_patchmgr_find.append(['egrep', '-i', 'Working|SUCCESS|INFO', _log_path_on_launch_node+"/PatchmgrConsole.out"])
            _cmd_list_patchmgr_find.append(['tail', '-1'])
            _cmd_list_patchmgr_find.append(['cut', '-d\'[\'', '-f3,4,5'])
            _cmd_list_patchmgr_find.append(['cut', '-d\'[\'', '-f2,3,4,5'])
            #_cmd_list_patchmgr_find.append(['sed', '-E', '\'s/\]/->/g;/^$/d\''])
            _rc, _o = runInfraPatchCommandsLocally(_cmd_list_patchmgr_find)
            if _o:
                _out = _o.split("\n")
            else:
                _out = []
            for _output in _out:
                _output = _output.strip()
                if _patchmgr_prev != _output:
                    self.mPatchmgrLogInfo(f"{_output}")
                    _patchmgr_prev = _output

            # save patchmgr node progress data into database
            self.__mSaveNodeProgressStatusToDB()

            _patch_progress_time = datetime.datetime.now()
            _elapsed_time_in_sec = int((_patch_progress_time - _patchmgr_start_time).total_seconds())

            _rc, _out = runInfraPatchCommandsLocally(_seek_cmd_list)

            if _out and "Exit status" in _out:
                _patch_mgr_run = False

                _cmd_list_summary = []
                _cmd_list_summary.append(['egrep', '-i', 'ERROR|WARNING|For details, check the following files', '-A 5', _log_path_on_launch_node+"/PatchmgrConsole.out"])
                _cmd_list_summary.append(['egrep', '-vi', 'Do not interrupt|Do not resize|Do not reboot|Do not open logfiles'])
                _cmd_list_summary.append(['cut', '-d\'[\'', '-f3,4,5'])
                _cmd_list_summary.append(['cut', '-d\':\'', '-f2,3,4,5'])
            #    _cmd_list_summary.append(['sed', '-E', '\'s/\]/->/g;/^$/d\''])
                _rc, _summary_out = runInfraPatchCommandsLocally(_cmd_list_summary)
                if _summary_out:
                    for _each_summary in _summary_out:
                        self.mPatchmgrLogInfo(_each_summary)

                self.mPatchmgrLogInfo(f"Before split: {_out}")
                for _output in _out.split("\n"):
                    self.mPatchmgrLogInfo(f"{_output}")
                    if "Exit status:0" in _output:
                        _exit_code = PATCH_SUCCESS_EXIT_CODE
                    else:
                        _suggestion_msg = f"Patchmgr command failed on Target : {str(self.mGetHandler().mGetTargetTypes())} for Patch Operation : {self.mGetOperation()}. Patchmgr logs are available on the node : {str(_external_launch_node)} at location : {_log_path_on_launch_node}."
                        self.mGetHandler().mAddError(_exit_code, _suggestion_msg)

                    # Team preferred adding the final call to update the patchmgr notification status here which
                    # is closer to the patchmgr success/failure check
                    # There was also a suggestion to not to invoke this call from timeout block below as patchmgr
                    # status updated before to the timeout is the source of truth.
                    # Team also preferred to remove the calls from taskhandler files, which is an exit gate in the
                    # request completion flow as that requires computing launch node and extra logic to get patchmgr
                    # notification xml details

                    # save patchmgr node progress data into database
                    self.__mSaveNodeProgressStatusToDB(aFinalLastCns=True)

                    self.mSetStatusCode(aStatusCode=_exit_code)

                    # Dump content of PatchmgrConsole.out at the end irrespective if success/failure
                    self.mPatchLogInfo(
                        f"\n\n --------> Start dumping entire patchmgr Console log at the end of patchMgr operation from {str(_external_launch_node)}:{_log_path_on_launch_node} <--------\n\n")
                    _cmd_list = []
                    _cmd_list.append(['cat', f'{_log_path_on_launch_node}/PatchmgrConsole.out'])
                    _rc, _o = runInfraPatchCommandsLocally(_cmd_list)
                    _out_log = _o.split("\n")
                    for _line in _out_log:
                        self.mPatchmgrLogInfo(_line.strip())
                    self.mPatchLogInfo(
                        f"\n\n --------> End dumping entire patchmgr Console log at the end of patchMgr operation from {str(_external_launch_node)}:{_log_path_on_launch_node} <--------\n\n")

                    self.mPatchLogInfo("\n\n--------> Patchmgr output ends here <--------\n")

                    # Wait for patchmgr commands to complete.
                    _mWaitForLocalNodePatchMgrSessionCompletion()
                    self.mSetCompleted(aCompleted=True)
                    # return to break the loop and exit the function
                    return

        '''
         In case of Exadata patchmgr timeout, Infra patching will terminate with
         exit code.

         EXADATA_PATCHMGR_CONSOLE_READ_TIMEOUT_ERROR requires action to be taken
         exacloud side/Operation team, hence it is by default retained as 
         PAGE_ONCALL
        '''
        if _elapsed_time_in_sec >= _patchmgr_timeout_in_sec:
            _exit_code = EXADATA_PATCHMGR_CONSOLE_READ_TIMEOUT_ERROR
            _suggestion_msg = f"Exadata Infra patching Timeout occurred after {_patchmgr_timeout_in_sec} seconds, Could not validate patch operation completion on launch node : {str(_external_launch_node)}."
            self.mSetStatusCode(aStatusCode=_exit_code)
            self.mGetHandler().mAddError(_exit_code, _suggestion_msg)

    def mWaitForExacomputePatchMgrCmdExecutionToComplete(self, aInputListFile=None, aPatchStates=None):
        """
         Here we connect to the launch node and try to check for progress reading
          Patchmgr Console out file. It returns:

             zero     --> when patchmgr end with success
             non-zero --> when patchmgr end with failure

          Since the patchmgr is run in the background using nohup, the below section
           of code monitors the log file for completion and returns the exit status of the
          patchmgr command.
        """

        _launch_node = self.mGetLaunchNode()
        _log_path_on_launch_node = self.mGetLogPathOnLaunchNode()

        self.mPatchLogInfo(f"Read patchmgr console from node = {_launch_node} and log loc = {_log_path_on_launch_node}")

        self.mPatchLogInfo("\n\n--------> Patchmgr output starts here <--------\n")
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_launch_node)
        _patch_progressing_status_json = {}
        _patch_mgr_run = True
        _patchmgr_prev = None
        _elapsed_time_in_sec = 0
        _nodes_already_upgraded = []
        _patch_failure_nodes = []
        _exit_code=PATCH_SUCCESS_EXIT_CODE

        _patchmgr_find = f"egrep -i 'Working|SUCCESS|INFO' {_log_path_on_launch_node}/PatchmgrConsole.out | tail -1 | cut -d'[' -f3,4,5 | cut -d':' -f2,3,4,5 | sed -E 's/\]/->/g;/^$/d'"
        _patchmgr_seek = f'grep -i "Exit status" {_log_path_on_launch_node}/PatchmgrConsole.out'
        _patchmgr_start_time = datetime.datetime.now()
        
        # Need to update node progress data with already upgraded nodes and precheck failed nodes so that node_progress_data
        # has data for all the nodes passed in the input
        _npdata_for_precheck_failed_and_already_upgraded = None
        _npdata_for_precheck_failed_and_already_upgraded = self.mGetHandler().mGetNodeProgressData(self.mGetHandler().mGetRequestObj().mGetUUID(),"Failed", aIncludeDataForAlreadyUpgradedNodes=True)
        _patchmgr_timeout_in_sec = self.mGetHandler().mGetExadataPatchmgrConsoleReadTimeoutSec()

        while _patch_mgr_run and _elapsed_time_in_sec < _patchmgr_timeout_in_sec:

            _i, _o, _e = _node.mExecuteCmd(_patchmgr_find)
            _out = _o.readlines()
            for _output in _out:
                _output = _output.strip()
                if _patchmgr_prev != _output:
                    self.mPatchmgrLogInfo(f"{_output}")
                    _patchmgr_prev = _output

            # Collect patchmgr notification or node progress details here.
            _patch_progressing_status_json, _patch_failure_nodes = self.mGetHandler().mUpdatePatchProgressStatus(aNode=_launch_node, aMergeableNPDataList=_npdata_for_precheck_failed_and_already_upgraded)

            _patch_progress_time = datetime.datetime.now()
            _elapsed_time_in_sec = int((_patch_progress_time - _patchmgr_start_time).total_seconds())

            _i, _o, _e = _node.mExecuteCmd(_patchmgr_seek)
            _exit_check = _node.mGetCmdExitStatus()
            _out = _o.readlines()

            if _exit_check == 0:
                _patch_mgr_run = False

                _cmd_get_summary = "egrep -i 'ERROR|WARNING|For details, check the following files' -A 5 {0}/PatchmgrConsole.out | egrep -vi 'Do not interrupt|Do not resize|Do not reboot|Do not open logfiles' | cut -d'[' -f3,4,5 | cut -d':' -f2,3,4,5 | sed -E 's/\]/->/g;/^$/d'".format(_log_path_on_launch_node)
                _i, _o, _e = _node.mExecuteCmd(_cmd_get_summary)
                _out_summary = _o.readlines()
                if _out_summary:
                    for _output_summary in _out_summary:
                        _output_summary = _output_summary.strip()
                        self.mPatchmgrLogInfo(_output_summary)

                for _output in _out:
                    self.mPatchmgrLogInfo(f"{_output}")
                    if "Exit status:0" in _output:
                        _exit_code = PATCH_SUCCESS_EXIT_CODE
                    else:
                        _suggestion_msg = f"Patchmgr command failed on Target : {str(self.mGetHandler().mGetCurrentTargetType())} for Patch Operation : {self.mGetOperation()}. Patchmgr logs are available on the node : {_launch_node} at location : {_log_path_on_launch_node}."
                        _exit_code = self.mGetHandler().mAddError(PATCHMGR_COMMAND_FAILED, _suggestion_msg)

                    if _node.mIsConnected():
                        _node.mDisconnect()
                    self.mPatchLogInfo("\n\n--------> Patchmgr output ends here <--------\n")

                    self.mSetStatusCode(aStatusCode=_exit_code)
                    self.mSetPatchFailedNodeList(aPatchFailedNodeList=_patch_failure_nodes)
                    # return to break the loop and exit the function
                    return

        '''
         In case of Exadata patchmgr timeout, Infra patching will terminate with
         exit code.

         EXADATA_PATCHMGR_CONSOLE_READ_TIMEOUT_ERROR requires action to be taken
         exacloud side/Operation team, hence it is by default retained as 
         PAGE_ONCALL
        '''
        if _elapsed_time_in_sec >= _patchmgr_timeout_in_sec:
            _suggestion_msg = f"Exadata Infra patching Timeout occurred after {_patchmgr_timeout_in_sec} seconds, Could not validate patch operation completion on launch node : {_launch_node}."
            _exit_code = self.mGetHandler().mAddError(EXADATA_PATCHMGR_CONSOLE_READ_TIMEOUT_ERROR, _suggestion_msg)

        if _node.mIsConnected():
            _node.mDisconnect()
        self.mSetStatusCode(aStatusCode=_exit_code)
        self.mSetPatchFailedNodeList(aPatchFailedNodeList=_patch_failure_nodes)

    def mWaitForExaComputePatchMgrCmdExecutionToComplete(self, aInputListFile=None, aPatchStates=None):
        """
         Here we connect to the launch node and try to check for progress reading
          Patchmgr Console out file. It returns:

             zero     --> when patchmgr end with success
             non-zero --> when patchmgr end with failure

          Since the patchmgr is run in the background using nohup, the below section
           of code monitors the log file for completion and returns the exit status of the
          patchmgr command.
        """

        _launch_node = self.mGetLaunchNode()
        _log_path_on_launch_node = self.mGetLogPathOnLaunchNode()

        self.mPatchLogInfo(f"Read patchmgr console from node = {_launch_node} and log loc = {_log_path_on_launch_node}")

        self.mPatchLogInfo("\n\n--------> Patchmgr output starts here <--------\n")
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_launch_node)
        _patch_progressing_status_json = {}
        _patch_mgr_run = True
        _patchmgr_prev = None
        _elapsed_time_in_sec = 0
        _nodes_already_upgraded = []
        _patch_failure_nodes = []
        _exit_code=PATCH_SUCCESS_EXIT_CODE

        _patchmgr_find = f"egrep -i 'Working|SUCCESS|INFO' {_log_path_on_launch_node}/PatchmgrConsole.out | tail -1 | cut -d'[' -f3,4,5 | cut -d':' -f2,3,4,5 | sed -E 's/\]/->/g;/^$/d'"
        _patchmgr_seek = f'grep -i "Exit status" {_log_path_on_launch_node}/PatchmgrConsole.out'
        _patchmgr_start_time = datetime.datetime.now()
        
        # Need to update node progress data with already upgraded nodes and precheck failed nodes so that node_progress_data
        # has data for all the nodes passed in the input
        _npdata_for_precheck_failed_and_already_upgraded = None
        _npdata_for_precheck_failed_and_already_upgraded = self.mGetHandler().mGetNodeProgressData(self.mGetHandler().mGetRequestObj().mGetUUID(),"Failed", aIncludeDataForAlreadyUpgradedNodes=True)
        _patchmgr_timeout_in_sec = self.mGetHandler().mGetExadataPatchmgrConsoleReadTimeoutSec()

        while _patch_mgr_run and _elapsed_time_in_sec < _patchmgr_timeout_in_sec:

            _i, _o, _e = _node.mExecuteCmd(_patchmgr_find)
            _out = _o.readlines()
            for _output in _out:
                _output = _output.strip()
                if _patchmgr_prev != _output:
                    self.mPatchmgrLogInfo(f"{_output}")
                    _patchmgr_prev = _output

            # Collect patchmgr notification or node progress details here.
            _patch_progressing_status_json, _patch_failure_nodes = self.mGetHandler().mUpdatePatchProgressStatus(aNode=_launch_node, aMergeableNPDataList=_npdata_for_precheck_failed_and_already_upgraded)

            _patch_progress_time = datetime.datetime.now()
            _elapsed_time_in_sec = int((_patch_progress_time - _patchmgr_start_time).total_seconds())

            _i, _o, _e = _node.mExecuteCmd(_patchmgr_seek)
            _exit_check = _node.mGetCmdExitStatus()
            _out = _o.readlines()

            if _exit_check == 0:
                _patch_mgr_run = False

                _cmd_get_summary = "egrep -i 'ERROR|WARNING|For details, check the following files' -A 5 {0}/PatchmgrConsole.out | egrep -vi 'Do not interrupt|Do not resize|Do not reboot|Do not open logfiles' | cut -d'[' -f3,4,5 | cut -d':' -f2,3,4,5 | sed -E 's/\]/->/g;/^$/d'".format(_log_path_on_launch_node)
                _i, _o, _e = _node.mExecuteCmd(_cmd_get_summary)
                _out_summary = _o.readlines()
                if _out_summary:
                    for _output_summary in _out_summary:
                        _output_summary = _output_summary.strip()
                        self.mPatchmgrLogInfo(_output_summary)

                for _output in _out:
                    self.mPatchmgrLogInfo(f"{_output}")
                    if "Exit status:0" in _output:
                        _exit_code = PATCH_SUCCESS_EXIT_CODE
                    else:
                        _suggestion_msg = f"Patchmgr command failed on Target : {str(self.mGetHandler().mGetCurrentTargetType())} for Patch Operation : {self.mGetOperation()}. Patchmgr logs are available on the node : {_launch_node} at location : {_log_path_on_launch_node}."
                        _exit_code = self.mGetHandler().mAddError(PATCHMGR_COMMAND_FAILED, _suggestion_msg)

                    if _node.mIsConnected():
                        _node.mDisconnect()
                    self.mPatchLogInfo("\n\n--------> Patchmgr output ends here <--------\n")

                    self.mSetStatusCode(aStatusCode=_exit_code)
                    self.mSetPatchFailedNodeList(aPatchFailedNodeList=_patch_failure_nodes)
                    # return to break the loop and exit the function
                    return

        '''
         In case of Exadata patchmgr timeout, Infra patching will terminate with
         exit code.

         EXADATA_PATCHMGR_CONSOLE_READ_TIMEOUT_ERROR requires action to be taken
         exacloud side/Operation team, hence it is by default retained as 
         PAGE_ONCALL
        '''
        if _elapsed_time_in_sec >= _patchmgr_timeout_in_sec:
            _suggestion_msg = f"Exadata Infra patching Timeout occurred after {_patchmgr_timeout_in_sec} seconds, Could not validate patch operation completion on launch node : {_launch_node}."
            _exit_code = self.mGetHandler().mAddError(EXADATA_PATCHMGR_CONSOLE_READ_TIMEOUT_ERROR, _suggestion_msg)

        if _node.mIsConnected():
            _node.mDisconnect()
        self.mSetStatusCode(aStatusCode=_exit_code)
        self.mSetPatchFailedNodeList(aPatchFailedNodeList=_patch_failure_nodes)

    def mGenerateSwitchConfigsInCaseOfVerifyConfigFailure(self):
        '''
         Due to misconfiguration during provisioning or
         addition of switch, patchmgr verify config option
         could fail with errors. We will need to manually attach tags to switch
         hostnames at the first time execution so that misconfiguration is fixed
         and patchmgr commands during switch patching will work as expected.
        '''
        _switch_name_with_tags = []
        _product_name = None
        _switch_tag = None
        rocea0_counter = 101
        roceb0_counter = 102
        roces0_counter = 201
        _launch_node = self.mGetLaunchNode()
        _node_list_from_nodes_file = self.mGetNodeListFromNodesToBePatchedFile(aHost=_launch_node)

        if not self.mGetHandler().mIsMultiRackEnv():
            # Single rack environment and the tag will sfleaf.
            _switch_tag = "sfleaf"
        else:
            _product_name_list = []
            '''
             Get the system product type based on the ipmitool output
             in case of a multirack environment and add the required
             switch tags.
             As per Exadata dev, X8m, X9m can be combined to form a
             multirack and in such cases, use 14 uplink(u14 tag) config 
             on all switches.

             For Example 
             - If only x8m are combined to form a multirack.
             Switch name and tag will be convention - scaqau01sw-rocea0.us.oracle.com:msfleaf.101
             - If x8m and x9m are combined to form a multirack or have all racks greater then equal
             to x9m. Switch name and tag will be convention - scaqau01sw-rocea0.us.oracle.com:msfleaf_u14.101
            '''
            for _dom0 in self.mGetHandler().mGetCustomizedDom0List(): 
                _node = exaBoxNode(get_gcontext())
                try:
                    _node.mConnect(aHost=_dom0)
                    '''
          		[root@scaqau06adm03 ~]# ipmitool sunoem cli 'show /system model' | grep Exadata | awk '{print $4}' | cut -d"-" -f1
	        	X10M
		        [root@scaqau06adm03 ~]#

		        [root@iad127488exdd001 ~]# ipmitool sunoem cli 'show /system model' | grep Exadata | awk '{print $4}' | cut -d"-" -f1
		        X10M
		        [root@iad127488exdd001 ~]#
                    '''
                    _in, _out, _err = _node.mExecuteCmd("ipmitool sunoem cli 'show /system model' | grep Exadata | awk '{print $4}' | cut -d'-' -f1")
                    for _output in _out.readlines():
                        _product_name_list.append(_output.strip())
                    self.mPatchLogInfo(f"System model number - {_output.strip()} detected on {_dom0}")
                except Exception as e:
                    self.mPatchLogError("Error in fetching the system-product-name details using ipmitool command on Dom0.")
                    self.mPatchLogTrace(traceback.format_exc())
                if _node.mIsConnected():
                    _node.mDisconnect()
       
            _switch_tag = "msfleaf_u14"
            if _product_name_list:
                nums = {int(re.search(r'\d+', m).group()) for m in _product_name_list if re.search(r'\d+', m)}
                if nums and all(n <= 8 for n in nums):
                    _switch_tag = "msfleaf"
 
        '''
         Switch list from cluster xml can come in any order.
         It is important to sort it before adding the tags.
         Add port details only in case of a multirack.
        '''
        _sorted_switch_list = sorted(set(self.mGetHandler().mGetSwitchList()))
        for _switch_name in _sorted_switch_list:
            if self.mGetHandler().mIsMultiRackEnv():
                if "rocea0" in _switch_name:
                    _switch_name_with_tags.append(f"{_switch_name}:{_switch_tag}.{rocea0_counter}")
                    rocea0_counter += 2
                elif "roceb0" in _switch_name:
                    _switch_name_with_tags.append(f"{_switch_name}:{_switch_tag}.{roceb0_counter}")
                    rocea0_counter += 2
                elif self.mGetHandler().mIsMultiRackEnv() and "roces0" in _switch_name:
                    _switch_name_with_tags.append(f"{_switch_name}:{_switch_tag}.{roces0_counter}")
                    roces0_counter += 1
                else:
                    self.mPatchLogError(f"Switch name and type - {_switch_name} not recognised and the switch will not be patched.")
            else:
                 _switch_name_with_tags.append(f"{_switch_name}:{_switch_tag}")

        self.mPatchLogInfo("Newly generated switch list file with tags are as follows -")
        self.mPatchLogInfo(", ".join(_switch_name_with_tags))
        try:
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_launch_node)
            if _node.mFileExists(self.mGetNodesToBePatchedFile()):
                _node.mExecuteCmd(f"rm -rf {self.mGetNodesToBePatchedFile()}")
                _node.mExecuteCmdLog('printf "%s" > %s' % ("\\n".join(_switch_name_with_tags), self.mGetNodesToBePatchedFile()))

                # print the node list details.
                self.mPatchLogInfo(f"\n\nPrinting the switch list tag file - {self.mGetNodesToBePatchedFile()} details.")
                _cmd_cat_console_log = f"cat {self.mGetNodesToBePatchedFile()}"
                _i, _o, _e = _node.mExecuteCmd(_cmd_cat_console_log)
                for _line in _o.readlines():
                    self.mPatchmgrLogInfo(_line.strip())
                self.mPatchLogInfo(f"\n\n")

        except Exception as e:
            self.mPatchLogError("Error in writing switch list with tag details to the input list file on the launch node.")
            self.mPatchLogTrace(traceback.format_exc())
        finally:
            if _node.mIsConnected():
                _node.mDisconnect()
