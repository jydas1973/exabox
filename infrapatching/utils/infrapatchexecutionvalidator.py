#!/bin/python
#
# $Header: ecs/exacloud/exabox/infrapatching/utils/infrapatchexecutionvalidator.py /main/28 2025/08/29 06:28:17 araghave Exp $
#
# infrapatchexecutionvalidator.py
#
# Copyright (c) 2023, 2025, Oracle and/or its affiliates.
#
#    NAME
#      infrapatchexecutionvalidator.py - Validates whether the API will be executed or not
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    araghave    06/24/25 - Enhancement Request 38082882 - HANDLING EXACLOUD
#                           ELU CHANGES FOR DOM0 PATCHING
#    sdevasek    02/14/25 - ENH 37496197 - INFRAPATCHING TEST AUTOMATION -
#                           REVIEW AND ADD METHODS INTO METHODS_TO_EXCLUDE_
#                           COVERAGE_REPORT
#    antamil     01/31/25 - Enh 37300427 - Enable clusterless cell patching
#                           using management host
#    diguma      11/14/24 - bug 37249413: EXACS:23.4.1.2.7: ON PREPROD ENV:
#                           DOMU FAILED TO CHECK CURL
#                           HTTP://127.0.0.1:18181CONNECTION REFUSED
#    antamil     10/04/24 - Enh 37027134 - Modularize single vm patching code
#    araghave    09/09/24 - Enh 36977545 - REMOVE SYSTEM FIRST BOOT IMAGE
#                           SPECIFIC CODE FROM INFRA PATCHING FILES
#    araghave    08/27/24 - Enh 36829406 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE CORE, PLUGIN AND TASKHANDLER
#                           FILES
#    diguma      08/21/24 - bug 36871736:REPLACE EXASPLICE WITH ELU(EXADATA
#                           LIVE UPDATE) FOR EXADATA 24.X
#    sdevasek    05/22/24 - ENH 36296976 - VALIDATE FOR PDBS RUNNING STATE AND
#                           FOR PDBS IN RESTRICTED MODE DURING DOMU PATCHING 
#    sdevasek    05/03/24 - ENH 36578549 - CONTROL EXECUTION OF DB HEALTH CHECK
#                           BASED ON ENABLEDBHEALTHCHECKS FLAG IN ADDITIONAL
#                           OPTIONS OF INFRAPATCHING PAYLOAD
#    antamil     03/11/24 - Enh 36372221 - Code changes for single VM EXACS
#                           patching support
#    araghave    02/08/24 - Enh 36234905 - ENABLE SERVICESTATE OF INFRA ILOM
#                           DURING UPGRADE & DISABLE THEM AFTER UPGRADE
#    sdevasek    02/01/24 - ENH 35306246 - ADD DB HEALTH CHECKS
#                           DURING DOMU OS PATCHING
#    antamil     02/02/23 - 36109360 - Codes changes for Cps as launch node
#    sdevasek    12/11/23 - Enh 35244586 - 36092892 - VALIDATE FOR RDS_PING
#                           ONLY IN EXACS ENV IF HEARTBEAT CHECK FAILS
#    sdevasek    10/27/23 - BUG 35949486 - RESTORING INFRA PATCHING CHANGES  
#                           DONE AS PART OF 35825510
#    araghave    10/20/23 - Bug 35747726 - PATCHING FAILING WITH | ERROR -
#    antamil     10/17/23 - Bug 35835537 - Implement support for multiple external
#                                          launch node
#    araghave    08/14/23 - Enh 35244586 - DISABLE PRE AND POST CHECKS NOT
#                           APPLICABLE DURING MONTHLY PATCHING
#    vikasras    08/03/23 - Bug 35671592 - AFTER REFRESHING TO THE RECENT LABEL
#                           TEST FILES ARE REPORTING COMPILATION ERROR
#    sdevasek    08/09/23 - ENH 35687013 - CREATE AND DELETE MARKER FILE DURING
#                           PATCHING WHEN CPS IS USED AS LAUNCHNODE
#    antamil     08/03/23 - ENH 35621978 - ENABLE CPS AS LAUNCHNODE FOR
#                           DOMU PATCH OPERATION
#    jyotdas     07/31/23 - ENH 35641075 - Develop a generic framework for
#                           infrapatching api validation execution
#    jyotdas     07/31/23 - Creation
#

import os
import sys
from exabox.infrapatching.utils.utility import mGetInfraPatchingConfigParam, mGetInfraPatchingHandler, \
     mExaspliceVersionPatternMatch
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogDebug
from exabox.infrapatching.utils.constants import *

class InfrapatchExecutionValidator:

    def __init__(self, aTargetTypes = None):
        self.__targetHandlerInstance = None
        if aTargetTypes:
            self.__target_type = aTargetTypes[0]

    def mIsSpaceValidationEnabledForTarget(self, **kwargs):
        if self.__targetHandlerInstance is None:
            ebLogInfo("TargetHandler Instance is None in mIsSpaceValidationEnabled. Returning True")
            return True
        ebLogInfo(
            f"Current target Type from mIsSpaceValidationEnabledForTarget is {self.__targetHandlerInstance.mGetCurrentTargetType()}")
        _is_free_space_check_validation_enabled_flag = False
        _is_free_space_check_validation_enabled = mGetInfraPatchingConfigParam('free_space_check_validation_enabled_on_' + self.__targetHandlerInstance.mGetCurrentTargetType())

        if _is_free_space_check_validation_enabled and _is_free_space_check_validation_enabled.lower() in ['true']:
            ebLogInfo(
                f"_is_free_space_check_validation_enabled from mIsSpaceValidationEnabledForTarget is {_is_free_space_check_validation_enabled}")
            _is_free_space_check_validation_enabled_flag = True

        return _is_free_space_check_validation_enabled_flag

    def mIsStaleMountCheckEnabled(self, **kwargs):
        """
        Default value for enable_stale_mount_check is True in infrapatching.conf and parameter stored in the below format.
        "enable_stale_mount_check": "True"

        True/False values are stored as string so string comparison is done to get whether stale_mount_check is
        enabled or not.
        """
        _enable_stale_mount_check = mGetInfraPatchingConfigParam('enable_stale_mount_check')
        if _enable_stale_mount_check and _enable_stale_mount_check.lower() in ['true']:
            ebLogInfo(f"_enable_stale_mount_check from mIsStaleMountCheckEnabled is {_enable_stale_mount_check}")
            return True
        else:
            return False

    def mIsCDBDowntimeCheckEnabled(self, **kwargs):
        """
        Default value for enable_cdb_downtime_check is True in infrapatching.conf and parameter stored in the below format.
        "enable_cdb_downtime_check ": "True"
        """
        _enable_cdb_downtime_check = mGetInfraPatchingConfigParam('enable_cdb_downtime_check')
        if _enable_cdb_downtime_check and _enable_cdb_downtime_check.lower() in ['true']:
            ebLogInfo(f"_enable_cdb_downtime_check from mIsCDBDowntimeCheckEnabled is {_enable_cdb_downtime_check}")
            return True
        else:
            return False

    def mIsCDBDegradationCheckEnabled(self, **kwargs):
        """
        Default value for enable_cdb_degradation_check is True in infrapatching.conf and parameter stored in the below format.
        "enable_cdb_degradation_check": "True"
        """
        _enable_cdb_degradation_check = mGetInfraPatchingConfigParam('enable_cdb_degradation_check')
        if _enable_cdb_degradation_check and _enable_cdb_degradation_check.lower() in ['true']:
            ebLogInfo(
                f"_enable_cdb_degradation_check from mIsCDBDegradationCheckEnabled is {_enable_cdb_degradation_check}")
            return True
        else:
            return False

    def mIsPDBDowntimeCheckEnabled(self, **kwargs):
        """
        Default value for enable_pdb_downtime_check is True in infrapatching.conf and parameter stored in the below format.
        "enable_pdb_downtime_check ": "True"
        """
        _enable_pdb_downtime_check = mGetInfraPatchingConfigParam('enable_pdb_downtime_check')
        if _enable_pdb_downtime_check and _enable_pdb_downtime_check.lower() in ['true']:
            ebLogInfo(f"_enable_pdb_downtime_check from mIsPDBDowntimeCheckEnabled is {_enable_pdb_downtime_check}")
            return True
        else:
            return False

    def mIsPDBDegradationCheckEnabled(self, **kwargs):
        """
        Default value for enable_pdb_degradation_check is True in infrapatching.conf and parameter stored in the below format.
        "enable_pdb_degradation_check": "True"
        """
        _enable_pdb_degradation_check = mGetInfraPatchingConfigParam('enable_pdb_degradation_check')
        if _enable_pdb_degradation_check and _enable_pdb_degradation_check.lower() in ['true']:
            ebLogInfo(
                f"_enable_pdb_degradation_check from mIsPDBDegradationCheckEnabled is {_enable_pdb_degradation_check}")
            return True
        else:
            return False

    def mIsRDSPingCheckEnabled(self, **kwargs):
        """
        Validate rds_ping when enable_rds_ping_check is True in infrapatching.conf and only in EXACS env
        Default value for enable_rds_ping_check is True in infrapatching.conf and parameter stored in the below format.
        "enable_rds_ping_check": "True"
        """
        if self.__targetHandlerInstance is None:
            ebLogInfo("TargetHandler Instance is None in mIsRDSPingCheckEnabled. Returning False")
            return False

        _enable_rds_ping_check = False
        # Currently there is no requirement to enable this check for ExaCC, so return False for EXACC
        if self.__targetHandlerInstance.mIsExaCC():
            return _enable_rds_ping_check

        _enable_rds_ping_check_param = mGetInfraPatchingConfigParam('enable_rds_ping_check')
        if _enable_rds_ping_check_param and _enable_rds_ping_check_param.lower() in ['true']:
            _enable_rds_ping_check =  True

        ebLogInfo(f"_enable_rds_ping_check from mIsRDSPingCheckEnabled is {str(_enable_rds_ping_check)}")
        return _enable_rds_ping_check

    @staticmethod
    def isSwitchFabricLockingMechanismEnabled(**kwargs):
        '''
         This method is used to determine whether ib fabric locking
         mechanism is required to be acquired prior to patching.

         - If enable_switch_fabric_locking_mechanism is set to True
           in infrapatching.conf, switch fabric based locking will be acquired.

         - If enable_switch_fabric_locking_mechanism is set to False
           in infrapatching.conf, switch fabric based locking will not be acquired.

         - Since this method is used both in worker and dispatcher, it is defined as
           static.
        '''
        _enable_switch_fabric_locking_mechanism = mGetInfraPatchingConfigParam('enable_switch_fabric_locking_mechanism')
        if _enable_switch_fabric_locking_mechanism and _enable_switch_fabric_locking_mechanism.lower() in ['true']:
            ebLogInfo("Switch fabric based locking will be acquired prior to patching.")
            return True
        else:
            ebLogInfo("Switch fabric based locking will not be acquired prior to patching.")
            return False

    def checkHeartbeatValidationPriorToPatchmgrRun(self, **kwargs):
        '''
         This method is used to determine whether cluster wide CRS checks can 
         be performed prior to patchmgr command run in case of patch and rollback.

         This check is skipped in case of exasplice patching or run
         otherwise.
        '''
        _perform_heartbeat_validation_prior_to_patchmgr_run = mGetInfraPatchingConfigParam('enable_crs_validation_prior_to_patchmgr_run')
        if self.performValidationsDuringExasplicePatchOrPreCheck(**kwargs):
            ebLogInfo("Heartbeat/CRS validations are not performed during exasplice patching.")
            return False
        elif _perform_heartbeat_validation_prior_to_patchmgr_run and _perform_heartbeat_validation_prior_to_patchmgr_run.lower() in ['true']:
            ebLogInfo("Heartbeat/CRS validations are run as part of the current infra patching operation.")
            return True
        else:
            ebLogInfo("Heartbeat/CRS validations are not performed as the check is disabled.")
            return False

    def checkHAChecksOnDom0(self, **kwargs):
        '''
         This method is used to determine whether to perform High 
         availability checks on DomU belonging to a cluster during 
         dom0 patching.

         This check is skipped in case of exasplice patching or in
         case of clusterless patching or by default.

         It is validated only in case the check is enabled in 
         infrapatching.conf
        '''
        if self.__targetHandlerInstance is None:
            ebLogInfo("TargetHandler Instance is None in checkHAChecksOnDom0. Returning False")
            return False

        _perform_high_availability_checks_on_dom0 = mGetInfraPatchingConfigParam('enable_high_availability_checks_on_dom0')
        if self.performValidationsDuringExasplicePatchOrPreCheck(**kwargs):
            ebLogInfo("DomU high availability checks are not performed during exasplice patching.")
            return False
        elif self.__targetHandlerInstance.mIsClusterLessUpgrade():
            ebLogInfo("DomU high availability checks are not performed in case of clusterless patching")
            return False
        elif _perform_high_availability_checks_on_dom0 and _perform_high_availability_checks_on_dom0.lower() in ['true']:
            ebLogInfo("Domu High Availability validations are run as part of the current infra patching operation.")
            return True
        else:
            ebLogInfo("DomU high availability checks are not performed on this environment as the parameter 'enable_high_availability_checks_on_dom0' in infrapatching.conf is set to 'False'.")
            return False

    def enableValidationOfVifBridge(self, **kwargs):
        '''
         This method is used to determine whether to perform vif bridge 
         validations post dom0 patching and rollback. It is validated 
         only in case the check is enabled in infrapatching.conf, skipped
         otherwise.
        '''
        _enable_vif_bridge_validation_param_value = mGetInfraPatchingConfigParam('vif_bridge_symlink_post_check')
        if _enable_vif_bridge_validation_param_value and _enable_vif_bridge_validation_param_value.lower() in ['true']:
            ebLogInfo("Vif Bridge validations run as part of the current infra patching operation.")
            return True
        else:
            ebLogInfo("Vif bridge validations are not performed as the check is disabled.")
            return False

    def checkValidationOfVifBridge(self, **kwargs):
        '''
         This method is used to determine whether vif bridge 
         validations are performed post dom0 patching and rollback. 
        
         This check is skipped in case of exasplice patch operations
         or in case the environment is EXACC and Xen and the list of 
         Domu passed are less than or equal to zero or validated
         otherwise.
        '''
        _domu_list = []
        _domu_list = kwargs['dom0sdomulist']

        if self.__targetHandlerInstance is None:
            ebLogInfo("TargetHandler Instance is None in checkValidationOfVifBridge. Returning False")
            return False

        if self.performValidationsDuringExasplicePatchOrPreCheck(**kwargs):
            ebLogInfo("Vif bridge symbolic link check are not performed during an exasplice patch operation.")
            return False
        elif not self.__targetHandlerInstance.mIsExaCC() and not self.__targetHandlerInstance.mIsKvmEnv() and len(_domu_list) > 0:
            '''
             Original condition is retained and check need to be performed
             only in case of the above conditions satisfies, not otherwise.
            '''
            ebLogInfo("Vif bridge symbolic link check are performed on EXACS Xen environments and the list of Domu count argument passed is greater than zero.")
            return True
        else:
            ebLogInfo("Vif bridge symbolic link checks are not performed as part of the current infra patching operation.")
            return False

    def performValidationsDuringExasplicePatchOrPreCheck(self, **kwargs):
        '''
         Skip this check in case of an exasplice infra patching 
         operation and patch operation type is patch_prereq_check 
         or patch.
        '''
        if self.__targetHandlerInstance is None:
            ebLogInfo("TargetHandler Instance is None in performValidationsDuringExasplicePatchOrPreCheck. Returning False")
            return False

        if self.__targetHandlerInstance.mIsExaSplice() and self.__targetHandlerInstance.mGetTask() in [ TASK_PREREQ_CHECK, TASK_PATCH ]:
            ebLogInfo(
                f"Patch operation type is Exasplice and the patch operation is {str(self.__targetHandlerInstance.mGetTask())}, some of the validations not relevant for Exasplice patching will be skipped.")
            return True
        else:
            ebLogInfo(
                f"Patch operation type is QMR and the patch operation is {str(self.__targetHandlerInstance.mGetTask())}. Relevant validations will be performed.")
            return False

    def checkStartIptablesService(self, **kwargs):
        '''
         This method is used to determine whether this validation 
         and startup of IP table service can be performed post 
         dom0 patching.

         Skip this check in case of an exasplice patch operation
         or the patch operation type is patch_prereq_check.
         or the operation type is clusterless patching. Since there
         are no provisioned clusters on clusterless environments, no
         ip rules are applicable.
        '''
        if self.__targetHandlerInstance is None:
            ebLogInfo("TargetHandler Instance is None in checkStartIptablesService. Returning False")
            return False

        if self.performValidationsDuringExasplicePatchOrPreCheck(**kwargs):
            ebLogInfo("mStartIptablesService check and startup are not performed in case of exasplice patching.")
            return False
        elif self.__targetHandlerInstance.mIsExaCC():
            ebLogInfo("mStartIptablesService check and startup are not performed in case of env is EXACC.")
            return False
        elif self.__targetHandlerInstance.mGetTask() in [TASK_PREREQ_CHECK]:
            ebLogInfo("mStartIptablesService check and startup are not performed in case of Patch precheck operation.")
            return False
        elif self.__targetHandlerInstance.mIsClusterLessUpgrade():
            ebLogInfo("mStartIptablesService check and startup are not performed in case of clusterless patching.")
            return False
        else:
            ebLogInfo("mStartIptablesService check and startup are performed as part of the current infra patching operation.")
            return True

    def checkValidationsToPerformAutoStartupRequired(self, **kwargs):
        '''
         This method is used to determine whether validations 
         regarding DomU auto startup are required to be 
         performed post dom0 patching.

         Skip this check in case of exasplice patch operation
         or the patch style is rolling
         and the domu is less than or equal to zero
         and Discarded Flag is set to False.
        '''
        _discarded_node_list_check = True
        _domu_list = []
        _discarded_node_list_check = kwargs['discardedNodeListCheck']
        _domu_list = kwargs['dom0sdomulist']

        if self.__targetHandlerInstance is None:
            ebLogInfo("TargetHandler Instance is None in checkValidationsToPerformAutoStartupRequired. Returning False")
            return False

        if self.performValidationsDuringExasplicePatchOrPreCheck(**kwargs):
            ebLogInfo("Validations to perform DomU auto startup checks are not performed in case of exasplice patching.")
            return False
        elif self.__targetHandlerInstance.mGetOpStyle() == OP_STYLE_NON_ROLLING and len(_domu_list) <= 0 and not _discarded_node_list_check:
            ebLogInfo("DomU Auto startup checks are performed as part of the current infra patching operation.")
            return True
        else:
            ebLogInfo("DomU Auto startup checks are not performed as part of the current infra patching operation.")
            return False

    def checkIfSystemImagesCanBeCleanedUp(self, **kwargs):
        '''
         This method is used to determine whether system
         first boot images can be cleaned up post dom0 QMR
         patching.
        '''
        if self.__targetHandlerInstance is None:
            ebLogInfo("TargetHandler Instance is None in checkIfSystemImagesCanBeCleanedUp. Returning False.")
            return False
        elif self.__targetHandlerInstance.mGetCurrentTargetType() != PATCH_DOM0:
            ebLogInfo("System first boot images cannot be cleaned up during a non-dom0 target patching. Returning False.")
            return False
        elif self.__targetHandlerInstance.mIsExaSplice():
            ebLogInfo("System first boot images cannot be cleaned up during an exasplice patch operation. Returning False.")
            return False
        elif self.__targetHandlerInstance.mGetTask() != TASK_PATCH:
            ebLogInfo("System first boot images cannot be cleaned up only during an upgrade operation. Returning False.")
            return False
        else:
            ebLogInfo("System first boot images will be cleaned up during the infra patch operation.")
            return True

    def checkValidateHeartbeatRequired(self, **kwargs):
        '''
         This method is used to determine whether heartbeat validations
         are required to be performed post dom0 patching.

         Skip this check in case of exasplice patch operation
          or 
         the discarded node list check flag is set to False
        '''
        _is_discarded_node_list_check = True
        _is_discarded_node_list_check = kwargs['isDiscardedNodeListCheck']

        if self.performValidationsDuringExasplicePatchOrPreCheck(**kwargs):
            ebLogInfo("Heartbeat validation checks are not performed in case of exasplice patching.")
            return False
        elif not _is_discarded_node_list_check:
            ebLogInfo("Heartbeat validation checks are performed as part of the current infra patching operation.")
            return True
        else:
            ebLogInfo("Heartbeat validation checks are not performed as part of the current infra patching operation.")
            return False

    def mEnableDBHealthChecks(self, **kwargs):
        if self.__targetHandlerInstance is None:
            ebLogInfo("TargetHandler Instance is None in mEnableDBHealthChecks. Returning False")
            return False

        _enable_db_health_checks = False

        if self.__targetHandlerInstance.mGetTask() in [TASK_PATCH] and (
                self.__targetHandlerInstance.mGetAdditionalOptions()
                and 'EnableDBHealthChecks' in (self.__targetHandlerInstance.mGetAdditionalOptions()[0]) and
                self.__targetHandlerInstance.mGetAdditionalOptions()[0]['EnableDBHealthChecks'].lower() == 'yes'):
            _enable_db_health_checks = True

        ebLogInfo(f"_enable_db_health_checks value from mEnableDBHealthChecks is {str(_enable_db_health_checks)}")

        return _enable_db_health_checks

    def mIsSingleDomUVMCluster(self, **kwargs):
        if PATCH_DOMU not in self.__target_type:
            return False
        if self.__targetHandlerInstance is None:
            ebLogInfo("TargetHandler Instance is None in isSingleVMCluster. Returning False")
            return False
        is_single_vm_cluster = False
        _single_vm_clusters = self.__targetHandlerInstance.mGetClustersWithSingleVM()
        if self.__targetHandlerInstance.mGetRackName() in _single_vm_clusters:
            is_single_vm_cluster = True
        return is_single_vm_cluster

    def mIsCpsLaunchNodeForDomU(self, **kwargs):
        if PATCH_DOMU not in self.__target_type:
            return False
        if self.__targetHandlerInstance is None:
            ebLogInfo("TargetHandler Instance is None in mIsCpsLaunchNodeForDomU. Returning False")
            return False
        _is_cps_launch_node_for_domu_flag = False
        _single_vm_clusters = self.__targetHandlerInstance.mGetClustersWithSingleVM()
        if self.__targetHandlerInstance.mIsExaCC() and len(_single_vm_clusters) > 0 and  \
                self.__targetHandlerInstance.mGetRackName() in _single_vm_clusters:
            # Need to add the check for single VM cluster
            _is_cps_launch_node_for_domu_flag = True
        return _is_cps_launch_node_for_domu_flag

    def mIsManagementHostLaunchNodeForClusterless(self, **kwargs):
        if self.__target_type not in [ PATCH_CELL, PATCH_DOM0]:
            return False

        if self.__targetHandlerInstance is None:
            ebLogInfo("TargetHandler Instance is None in mIsManagementHostLaunchNodeForClusterless." \
                      " Returning False")
            return False

        _is_mgmt_host_launch_node = False
        if not self.__targetHandlerInstance.mIsExaCC() and self.mIsExternalLaunchNodePassed(**kwargs) \
            and self.__targetHandlerInstance.mIsClusterLessUpgrade() and self.__targetHandlerInstance.mGetLaunchNodeType() == LAUNCHNODE_TYPE_MANAGEMENT_HOST:
            _is_mgmt_host_launch_node = True

        return _is_mgmt_host_launch_node

    def mIsManagementHostLaunchNodeForDomU(self, **kwargs):
        if PATCH_DOMU not in self.__target_type:
            return False
        if self.__targetHandlerInstance is None:
            ebLogInfo("TargetHandler Instance is None in mIsManagementHostLaunchNodeForDomU. Returning False")
            return False
        _is_mgmt_host_launch_node_for_domu_flag = False
        _single_vm_clusters = self.__targetHandlerInstance.mGetClustersWithSingleVM()
        if not self.__targetHandlerInstance.mIsExaCC() and self.mIsExternalLaunchNodePassed(**kwargs) \
            and len(_single_vm_clusters) > 0 and  \
            self.__targetHandlerInstance.mGetRackName() in _single_vm_clusters:
                _is_mgmt_host_launch_node_for_domu_flag = True
        return _is_mgmt_host_launch_node_for_domu_flag


    def mIsManagementHostLaunchNodeForDomuOrClusterless(self, **kwargs):
        return (self.mIsManagementHostLaunchNodeForDomU(**kwargs) or self.mIsManagementHostLaunchNodeForClusterless(**kwargs))
    

    def mIsLocalHostLaunchNode(self, **kwargs):
        if self.__targetHandlerInstance is None:
            ebLogInfo("TargetHandler Instance is None in mIsLocalHostLaunchNode. Returning False")
            return False
        _is_localhost_launch_node = False
        aLaunchNodeCandidates = self.__targetHandlerInstance.mGetExternalLaunchNode()
        if len(aLaunchNodeCandidates) > 0 and aLaunchNodeCandidates[0] == 'localhost':
            _is_localhost_launch_node = True
        return _is_localhost_launch_node

    def mIsExternalLaunchNodePassed(self, **kwargs):
        _is_launch_node_passed = False
        if self.__targetHandlerInstance is None:
            ebLogInfo("TargetHandler Instance is None in mIsExternalLaunchNodePassed. Returning False")
            return False
        if self.__targetHandlerInstance.mGetAdditionalOptions() and 'LaunchNode' in self.__targetHandlerInstance.mGetAdditionalOptions()[0] \
            and self.__targetHandlerInstance.mGetAdditionalOptions()[0]['LaunchNode'] and  \
                self.__targetHandlerInstance.mGetAdditionalOptions()[0]['LaunchNode'] != 'none':
            _is_launch_node_passed = True
        return _is_launch_node_passed

    def mIsPatchBaseMarkerFileApplicable(self, **kwargs):
        if self.__targetHandlerInstance is None:
            ebLogInfo("TargetHandler Instance is None in mIsPatchBaseMarkerFileApplicable. Returning False")
            return False
        _is_patchbase_marker_file_applicable = False
        if self.mIsCpsLaunchNodeForDomU(**kwargs) or self.mIsManagementHostLaunchNodeForDomU(**kwargs):
            _is_patchbase_marker_file_applicable = True
        return _is_patchbase_marker_file_applicable

    def enableServiceStateOnIlomsPriorToDom0CellPatchingEnabled(self, **kwargs):
        '''
         This method is used to determine whether to enable
         or disable service state on iloms during upgrade.

         Skip this check in case of an exasplice patch operation
         or the patch operation type is not upgrade.
         or the environment is not EXACC
         or the parameter enable_service_state_on_iloms_priorto_dom0_cell_patching
         is set to False in infrapatching.conf.
        '''
        if self.__targetHandlerInstance is None:
            ebLogInfo("TargetHandler Instance is None in enableServiceStateOnIlomsPriorToDom0CellPatchingEnabled. Returning False")
            return False

        if not self.__targetHandlerInstance.mIsExaCC():
            ebLogInfo("enableServiceStateOnIlomsPriorToDom0CellPatchingEnabled method is applicable only to EXACC environments.")
            return False

        _enable_service_state_on_iloms_priorto_dom0_cell_patching = mGetInfraPatchingConfigParam('enable_service_state_on_iloms_priorto_dom0_cell_patching')
        if self.performValidationsDuringExasplicePatchOrPreCheck(**kwargs) and self.__target_type == PATCH_DOM0:
            ebLogInfo("enableServiceStateOnIlomsPriorToDom0CellPatchingEnabled method is not called in case of dom0 smr patching.")
            return False
        elif _enable_service_state_on_iloms_priorto_dom0_cell_patching and _enable_service_state_on_iloms_priorto_dom0_cell_patching.lower() in ['false']:
            ebLogInfo("Enabling and disabling of servicestate during dom0/cell patching are not performed as _enable_service_state_on_iloms_priorto_dom0_cell_patching is set to False.")
            return False
        elif self.__targetHandlerInstance.mGetTask() not in [ TASK_PATCH ]:
            ebLogInfo("enableServiceStateOnIlomsPriorToDom0CellPatchingEnabled method is called only in case of infra patch operation type is PATCH.")
            return False
        else:
            ebLogInfo("enableServiceStateOnIlomsPriorToDom0CellPatchingEnabled method is called as part of the current infra patching operation.")
            return True

    def mCheckCondition(self, functionName, **kwargs):
        if  self.__target_type and self.__targetHandlerInstance is None:
            self.__targetHandlerInstance = mGetInfraPatchingHandler(INFRA_PATCHING_HANDLERS,self.__target_type)

        if hasattr(self, functionName) and callable(getattr(self, functionName)):
            func = getattr(self, functionName)
            return func(**kwargs)
        else:
            # If the functionName is not defined , return True
            ebLogInfo(f"Function {functionName} not found in mCheckCondition. Returning True")
            return True


    # this method checks for the exasplice version
    # it returns true if current version is equal or higher than aVersion
    #            false otherwise
    def mIsNodeAlreadyAtOrHigherExaspliceVersion(self, **kwargs):
        if self.__targetHandlerInstance is None:
            ebLogInfo("TargetHandler Instance is None in mIsExaspliceVersionHigher. Returning False")
            return False
        _compare = False
        _target_handler_instance = self.__targetHandlerInstance
        _node = kwargs['node']
        _version = kwargs['version']
        _node_type = kwargs['nodeType']
        _currExaspliceVersion = _target_handler_instance.mGetCluPatchCheck().mCheckTargetVersion(_node,
                                                          _node_type, aVersionToCompare=None, aIsexasplice=True)
        # if there is no exaplice version, use lower portion of current version
        if (_currExaspliceVersion == "000000"):
            _currVersion = _target_handler_instance.mGetCluPatchCheck().mCheckTargetVersion(_node,
                                                     _node_type, aVersionToCompare=None, aIsexasplice=False)
            # if current quaterly version on machine is 21.2.17.0.0.221020.1, _lowerCurrVersion will be 221020.1
            _currVersionDateCode = _currVersion.split(".", 5)[-1]
            _targetVersion = _target_handler_instance.mGetTargetVersion().split(".", 0)[-1]

            ebLogInfo(f"No exasplice version, using current lower version {_currVersionDateCode}")

            if _currVersionDateCode >= _targetVersion:
                _compare = True
        # if there is an exasplice version, compare
        else:
            _status = _target_handler_instance.mGetCluPatchCheck().mCheckTargetVersion(_node,
                                                _node_type, _version, aIsexasplice=True)
            if (_status >= 0):
                _compare = True
        return _compare

    def mNeedRestartMetricService(self, **kwargs):
        if self.__targetHandlerInstance is None:
            ebLogInfo("TargetHandler Instance is None in mNeedRestartMetricService. Returning False")
            return False
        _target_handler_instance = self.__targetHandlerInstance
        # coming from TargetVersion
        _postVersion = kwargs['postVersion']
        _majorPostVersion = int(_postVersion.split(".")[0])
        # if not exasplice and majorPost version is 23 (OL8)
        if _target_handler_instance.mIsKvmEnv() and not _target_handler_instance.mIsExaSplice() and _majorPostVersion >= 23:
            return True
        return False

# Sample Caller
# if __name__ == '__main__':
#     if self.mGetInfrapatchExecutionValidator().mCheckCondition('mValidateVIFBridgeInDom0', domuList=aDomUList):
