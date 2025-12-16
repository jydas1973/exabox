#!/bin/python
#
# $Header: ecs/exacloud/exabox/jsondispatch/jsondispatch.py /main/26 2025/12/02 08:46:19 jesandov Exp $
#
# jsondispatch.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      jsondispatch.py - jsondispatch basic functionality
#
#    DESCRIPTION
#      Provide basic/core API for exacloud json-only endpoints
#
#    NOTES
#      None
#
#    MODIFIED   (MM/DD/YY)
#    jepalomi    11/12/25 - 38529119: Manage services on infra hosts
#    prsshukl    08/20/25 - Enh 38180284 - EXADB-XS -> VALIDATE_VOLUME TO WORK
#                           AT THE HOST/DOM0 LEVEL
#    gparada     07/08/25 - 37996087-jsondisp-reset-ilom-pwd
#    kkviswan    05/28/25 - 37928955 Delegation Management New ER
#    dekuckre    12/09/24 - 37327394: Cleanup dom0
#    piyushsi    12/13/24 - BUG 36933899 Marking Exacloud Task Success
#    dekuckre    10/07/24 - 36644925: Added precheck for exacompute
#    joysjose    07/21/24 - ER 36190797 exabox.conf update API
#    aararora    07/09/24 - ER 36759599: Script to detect stale resources.
#    aypaul      06/19/24 - Enh#36362540 Support for adding host access control
#                           for dom0 and cells.
#    gparada     06/14/24 - 36628459 Handle ssk keys for secscan user
#    dekuckre    05/27/24 - XbranchMerge dekuckre_bug-36663068 from
#                           st_ecs_23.4.1.2.5
#    naps        05/27/24 - Bug 36663120 - exadbxs jsondispatch endpoint for
#                           dom0 roce config support.
#    jesandov    01/08/24 - 35141267: Add profiler endpoint
#    akkar       12/08/23 - Bug 35569058: GI support for n-4 images, add
#                           endpoint to jsondispatch
#    jiacpeng    08/30/23 - change the sla to new endpoint
#    gparada     05/18/23 - 35370215 Handle InitiatorID for ECRA
#    jfsaldan    03/23/23 - Enh 35135691 - EXACLOUD - ADD SUPPORT FOR VMBACKUP
#                           LOCAL BACKUP WITH ECRA SCHEDULER
#    alsepulv    02/11/22 - Creation
#

import json
import uuid

from exabox.agent.ebJobRequest import ebJobRequest
from exabox.core.Context import exaBoxContext
from exabox.core.DBStore import ebExacloudDB, ebGetDefaultDB
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.log.LogMgr import (ebLogDebug, ebLogError, ebLogInfo, ebLogTrace,
                               ebLogWarn)

# PLEASE KEEP Sorted alphabetically
from exabox.jsondispatch.handler_exabox_conf_operations import ExaboxConfOperationsHandler
from exabox.jsondispatch.handler_exacloud_updaterequest import ExaCloudUpdateRequest
from exabox.jsondispatch.handler_exacompute_check_dom0roce import ExaComputeCheckDom0Roce
from exabox.jsondispatch.handler_exacompute_cleanup_dom0 import ExaComputeCleanupDom0
from exabox.jsondispatch.handler_exacompute_configure_dom0roce import ExaComputeConfigureDom0Roce
from exabox.jsondispatch.handler_exacompute_generate_sshkey import ExaComputeGenerateSSHHandler
from exabox.jsondispatch.handler_exacompute_ingestion import ExacomputeIngestionHandler
from exabox.jsondispatch.handler_exacompute_vault_delete import ExaComputeDeleteVault
from exabox.jsondispatch.handler_exacompute_vault_details import ExaComputeVaultDetails
from exabox.jsondispatch.handler_exacompute_check_dom0roce import ExaComputeCheckDom0Roce
from exabox.jsondispatch.handler_exacompute_configure_dom0roce import ExaComputeConfigureDom0Roce
from exabox.jsondispatch.handler_exacompute_deconfigure_dom0roce import ExaComputeDeconfigureDom0Roce
from exabox.jsondispatch.handler_dactl import DaCtlHandler
from exabox.jsondispatch.handler_giconfig import GIConfigHandler
from exabox.jsondispatch.handler_hostaccesscontrol import ECHostAccessControlHandler
from exabox.jsondispatch.handler_ilom_pwd import IlomPasswordHandler
from exabox.jsondispatch.handler_manage_service import ManageServiceHandler
from exabox.jsondispatch.handler_prechecks import ExacomputePrechecks
from exabox.jsondispatch.handler_profiler import ProfilerHandler
from exabox.jsondispatch.handler_requests import RequestsHandler
from exabox.jsondispatch.handler_sla_vmCluster import SLAVmClusterHandler
from exabox.jsondispatch.handler_user_keys import UserHandler
from exabox.jsondispatch.handler_vmbackup import VMBackupHandler
from exabox.jsondispatch.handler_stale_resources import StaleResourcesHandler
from exabox.jsondispatch.handler_validate_volumes import ValidateVolumesHandler
from exabox.jsondispatch.handler_imagebase_copy_volumes import ImagebaseCopyVolume


class ebJsonDispatcher:

    def __init__(self, aCtx: exaBoxContext, aOptions: object = None):
        """Initializes the ebJsonDispatcher object

        :param aCtx: the global context - an object of type exaBoxContext
        :param aOptions: the exacloud arguments and options
        """

        # NOTE: For clarity, please add new endpoints keeping the
        # alphabetical order.

        self.__endpointDict = {
            "check_dom0_roce": ExaComputeCheckDom0Roce,
            "check_stale_resources": StaleResourcesHandler,
            "cleanup_dom0": ExaComputeCleanupDom0,
            "configure_dom0_roce": ExaComputeConfigureDom0Roce,
            "dactl_cmd": DaCtlHandler,
            "deconfigure_dom0_roce": ExaComputeDeconfigureDom0Roce,
            "deletevault": ExaComputeDeleteVault,
            "exabox_conf_operations": ExaboxConfOperationsHandler,
            "generatesshkeys": ExaComputeGenerateSSHHandler,
            "hac": ECHostAccessControlHandler,
            "ilom_pwd_reset": IlomPasswordHandler,
            "imageConfig": GIConfigHandler,
            "imagebase_copy_volumes": ImagebaseCopyVolume,
            "initialingestion": ExacomputeIngestionHandler,
            "capacity_move_prechecks": ExacomputePrechecks,
            "manage_service": ManageServiceHandler,
            "profiler": ProfilerHandler,
            "requests" : RequestsHandler,
            "sla" : SLAVmClusterHandler,                        
            "updatevaultaccessdetails": ExaComputeVaultDetails,
            "userHandler": UserHandler,
            "validate_volumes": ValidateVolumesHandler,
            "vmbackup": VMBackupHandler,
            "updaterequest": ExaCloudUpdateRequest
        }

        self.__ctx = aCtx
        self.__options = aOptions
        self.__base_path = None
        self.__cmd  = None

        self.__requestobj  = None
        self.__uuid = None
        self.__db = None

    def mGetArgsOptions(self) -> object:
        if self.__options is None:
            return self.__ctx.mGetArgsOptions()
        else:
            return self.__options

    def mSetRequestObj(self, aReqObj: object) -> None:
        self.__requestobj = aReqObj
        self.__uuid = self.__requestobj.mGetUUID()

    def mSetDB(self, aDB: ebExacloudDB):
        self.__db = aDB


    def mDispatch(self, aCmd: str = None, aOptions: object = None) -> int:
        """Runs the given command. This is the main driver method.

        :param aCmd: the command to execute
        :param aOptions: the exacloud options
        :param aJob: the ECRA job (if there is one)

        :returns an int representing the error code, with 0 being no error.
        """

        ebLogTrace(f"mDispatch: aCmd = {aCmd}")

        _rc = ebError(0x0000)

        self.__base_path = self.__ctx.mGetBasePath()
        self.__cmd  = aCmd

        if not self.__uuid:
            self.__uuid = str(uuid.uuid1())

        try:
            _rc = self.mExecuteEndpoint(aCmd, aOptions)

        except Exception as oops:
            if type(oops) != type(ExacloudRuntimeError()):
                ebLogWarn((f"*** Oops Caught - {type(oops)}\n"
                           f"*** Exception: {oops}"))

            raise

        return _rc

    def mExecuteEndpoint(self, aCmd: str, aOptions: object) -> int:
        """Executes the given function

        :param aCmd: the command to be executed
        :param aOptions: the exacloud options
        """

        _options = aOptions
        if not _options:
            _options = self.mGetArgsOptions()

        if aCmd in self.__endpointDict.keys():
            ebLogInfo(f"*** Running the cmd - {aCmd}")

            _handler = self.__endpointDict[aCmd](_options, self.__requestobj, self.__db)
            return _handler.mHandleEndpoint()

        ebLogError(f"Cmd {aCmd} not supported")
        raise ExacloudRuntimeError(0x0825, 0xA, f"Cmd {aCmd} not supported")

# end of file
