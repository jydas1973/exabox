#!/bin/python
#
# $Header: ecs/exacloud/exabox/jsondispatch/handler_vmbackup.py /main/10 2024/11/06 18:19:05 jfsaldan Exp $
#
# handler_vmbackup.py
#
# Copyright (c) 2023, 2024, Oracle and/or its affiliates.
#
#    NAME
#      handler_vmbackup.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jfsaldan    10/30/24 - Bug 37202899 - EXACS:24.4.1:VMBACKUP TO OSS :
#                           DOWNLOAD GOLD BACKUP RETURN COMPLETED/SUCCESS POST
#                           GOLD BACKUP FAILED TO OSS
#    gsundara    09/25/24 - Bug 36741285 - EXADB-XS: DISABLING VM BACKUP WHILE
#                           INGESTION FROM EXACS TO EXACOMPUTE
#    jfsaldan    05/29/24 - Enh 36474098 - EXACLOUD TO SUPPORT VM RESTORE ON
#                           INDIVIDUAL FILESYSTEMS
#    aypaul      12/21/23 - Enh#35866197 Support reload option using osslist.
#    jfsaldan    09/27/23 - Enh 35791811 - VMBACKUP TO OSS:EXACLOUD: REDUCE
#                           TIME WHILE TAKING GOLD IMAGE DURING PROVISIONING
#    jfsaldan    06/22/23 - Enh 35399269 - EXACLOUD TO SUPPORT RETRIEVAL OF
#                           METADATA FILES FROM DOM0 FOR BACKUP OPERATION.
#    jfsaldan    06/20/23 - Enh 35207469 - EXACLOUD ENDPOINT TO INJECT OCI
#                           CONFIGURATIONS AND KEYS TO DOM0 FOR VMBACKUP
#                           OPERATIONS
#    jfsaldan    03/23/23 - Enh 35135691 - EXACLOUD - ADD SUPPORT FOR VMBACKUP
#                           LOCAL BACKUP WITH ECRA SCHEDULER
#    jfsaldan    03/23/23 - Creation
#

import os
from typing import Tuple
from exabox.core.Context import get_gcontext
from exabox.jsondispatch.jsonhandler import JDHandler
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace
from exabox.ovm.vmbackup import ebCluManageVMBackup
from exabox.ovm.clucontrol import exaBoxCluCtrl


class VMBackupHandler(JDHandler):

    # Class attributes
    SUCCESS = 0

    # EXIT CODES
    ERR_INVALID_OPERATION = 1
    ERR_EXECUTE_VMBACKUP = 2


    def __init__(self, aOptions, aRequestObj = None, aDb=None):

        super().__init__(aOptions, aRequestObj, aDb)
        self.mSetSchemaFile(os.path.abspath(
            "exabox/jsondispatch/schemas/vmbackup.json"))

    def mExecute(self) -> Tuple[int, dict]:
        """
        Driver function for the VMBackup endpoint module
        This module is meant to allow the execution of 'vmbackup' operations
        on specific Nodes, and will NOT require an XML as input (only
        a payload in JSON format with a predefined JSON Schema)

        :returns: a tuple[int, dict] containing the return code and a dictionary
                  representing the results
        """

        # We will execute below the corresponding method from
        # 'ebCluManageVMBackup.mExecuteOperation' which
        # internally uses 'aOptions.vmbackup_operation' to determine
        # the operation to run. We want to make sure the operation received
        # is valid to be run on this endpoint where we don't expect any XML
        _valid_jsondispatch_operations = {
                "list_oss",
                "backup_host",
                "export_keys_dom0",
                "get_host_status",
                "golden_backup",
                "restore_oss",
                "restore_local",
                "setcron"
                }

        _options = self.mGetOptions()
        _vmbackup_op = _options.vmbackup_operation
        ebLogInfo(f"Received vmbackup operation: '{_vmbackup_op}'")

        if _vmbackup_op not in _valid_jsondispatch_operations:
            _err_msg = (f"Exacloud received an invalid operation: "
                f"'{_vmbackup_op}', valid operations on this endpoint are: "
                f"'{_valid_jsondispatch_operations}'")
            ebLogError(_err_msg)

            return VMBackupHandler.ERR_INVALID_OPERATION, {}

        _rc = VMBackupHandler.SUCCESS
        _response = {}

        # Create vmbackup and clucontrol object
        # Beware that not all methods from ebCluManageVMBackup will
        # work if we don't have a cluster XML file, but at this point we
        # already checked if the operation received is valid without XML
        _clucontrol = exaBoxCluCtrl(get_gcontext())
        _vmbackup_mgr = ebCluManageVMBackup(_clucontrol)

        try:
            _rc = _vmbackup_mgr.mExecuteOperation(_options)

        # Ref 37202899
        # We supress exceptions in here, as long as _rc is
        # non-zero, the request will be marked as error
        # with Worker.py logic
        except Exception as e:
            _err_msg = ("Exception happened while running: "
                f"'{_vmbackup_op}', error is: '{e}'")
            ebLogError(_err_msg)
            _rc = VMBackupHandler.ERR_EXECUTE_VMBACKUP

        # If request is successful, we asssign the json-dispatch
        # response to be the vmbackup manager response
        else:
            _response = _vmbackup_mgr.mGetVMBackupData()

        # Regardless of error or success, we'll try to log the contents of
        # the _vmbackup_mgr object
        finally:
            ebLogTrace("VMBackup manager output: "
                f"'{_vmbackup_mgr.mGetVMBackupData()}'")

        return _rc, _response
