#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/csstep/cs_golden_backup.py /main/13 2025/07/08 18:44:40 jfsaldan Exp $
#
# cs_golden_backup.py
#
# Copyright (c) 2023, 2025, Oracle and/or its affiliates.
#
#    NAME
#      cs_golden_backup.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      Logic used to install the vmbackup tool and take up a Golden Backup
#       of a VM
#
#    NOTES
#      Using as reference vmbackup confluence design:
#       https://confluence.oraclecorp.com/confluence/pages/viewpage.action?spaceKey=EDCS&title=VMBackup+using+Object+storage
#
#    MODIFIED   (MM/DD/YY)
#    jfsaldan    07/04/25 - Bug 38134918 - EXACS:25.2.1.1:RC5: X11 CROSS
#                           PLATFORM: ADD VM FAILS AT CREATEGOLDIMAGEBACKUP:
#                           TIMEOUT HAPPENED WHILE TAKING THE GOLDEN VM BACKUP
#                           | SPAWNED SUBPROCESS GOT STUCK
#    jfsaldan    05/23/25 - Bug 37989477 - EXACLOUD GOLDEN VMBACKUP | SYNTAX TO
#                           CATCH ERRORS NOT COMPLIANT WITH PYTHON 3.11
#    jfsaldan    04/24/25 - Enh 37817347 - EXACLOUD GOLDENVMBACKUP PROVISIONING
#                           STEP | FAILING TO TAKE GOLDEN VM REFLINK DURING
#                           CREATE SERVICE SHOULD NOT CAUSE FAILURE
#    jfsaldan    08/26/24 - Bug 36899424 - EXACLOUD VMBACKUP TO OSS: EXACLOUD
#                           SHOULD ENABLE THE OSSBACKUP FLAG IN VMBACKUP.CONF
#                           BEFORE ANY OSS OPERATION, AND DISABLE AFTER IS DONE
#    jfsaldan    01/19/24 - Bug 36197480 - EXACS - EXACLOUD FAILS TO SET
#                           VMBACKUP.CONF VALUES TO ENABLED VMBACKUP TO OSS
#    jfsaldan    11/01/23 - Bug 35969085 - ECS:EXACLOUD:23.4.1.2:ADD KMS KEY
#                           OCID AND CRYPTO ENDPOINT IN ALREADY PROVISIONED
#                           CLUSTERS IF PARAMETER IS MISSING FROM VMBACKUP.CONF
#    jfsaldan    09/27/23 - Enh 35791811 - VMBACKUP TO OSS:EXACLOUD: REDUCE
#                           TIME WHILE TAKING GOLD IMAGE DURING PROVISIONING
#    ririgoye    09/06/23 - Enh 35688081 - Moved mInstallCurrentVmbackupTool
#                           functionality to vmbackup.py
#    jfsaldan    08/16/23 - Enh 35692408 - EXACLOUD - VMBOSS - CREATE A FLAG IN
#                           EXABOX.CONF THAT TOGGLES BETWEEN INSTANCE
#                           PRINCIPALS AND USERS PRINCIPALS FOR VMBACKUP TO OSS
#                           MODULE
#    jfsaldan    07/04/23 - Enh 35500796 - EXACLOUD TO SUPPORT GOLDEN VMBACKUP
#                           STEP IN ELASTIC ADD COMPUTE
#    jfsaldan    06/13/23 - Enh 35207551 - EXACLOUD - ADD SUPPORT TO TERMINATE
#                           CLUSTER LEVEL VMBACKUP OCI RESOURCES WHEN LAST
#                           CUSTOMER CLUSTER IS TERMINATED
#    jfsaldan    01/10/23 - Enh 34965441 - EXACLOUD TO SUPPORT NEW TASK FOR
#                           GOLD IMAGE BACKUP
#    jfsaldan    01/10/23 - Creation
#

import copy
import datetime
import os
import time
from concurrent import futures

from exabox.exaoci.ExaOCIFactory import ExaOCIFactory
from exabox.core.Context import get_gcontext
from exabox.log.LogMgr import (ebLogError, ebLogInfo, ebLogWarn,
    ebLogTrace, ebLogCritical)
from exabox.ovm.csstep.cs_base import CSBase
from exabox.ovm.vmbackup import ebCluManageVMBackup
from exabox.ovm.vmboci import ebVMBackupOCI
from exabox.ovm.vmcontrol import ebVgLifeCycle
from exabox.utils.node import connect_to_host, node_exec_cmd, node_exec_cmd_check
from exabox.core.Error import ExacloudRuntimeError
from exabox.ovm.cludomufilesystems import start_domu, shutdown_domu
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure

# This class implements doExecute and undoExecute functions
# for the ESTP_BACKUPVM_GOLDIMAGE step of create service
class csGoldenBackup(CSBase):
    def __init__(self, aStepName=None):

        if aStepName:
            self.step = aStepName
        else:
            self.step = 'ESTP_BACKUPVM_GOLDIMAGE'

    def doExecute(self, aExaBoxCluCtrlObj, aOptions, steplist, aDom0List=None):
        ebLogInfo('csGoldenBackup: Entering doExecute')
        ebox = aExaBoxCluCtrlObj
        ebox.mUpdateStatus('step '+self.step)


        # Make sure the golden backup feature is enabled on exabox.conf
        # under field 'enable_goldvm_backup', if Not just end all this method
        # as a no-operation
        _goldvm_backup_conf =  get_gcontext().mGetConfigOptions().get(
                                    "vmbackup", {}).get("enable_goldvm_backup", "")

        if str(_goldvm_backup_conf).lower() == "false":
            ebLogInfo("The Golden VM Backup feature is disabled in "
                "exabox.conf. This step is a nop.")
            return 0
        else:
            ebLogTrace("The Golden VM Backup feature is not disabled: "
                f"'{_goldvm_backup_conf}")

        # Check if an exception must be raised on Error
        _raise_on_error =  get_gcontext().mGetConfigOptions().get(
                                    "vmbackup", {}).get("raise_gold_backup_on_error", "")
        if str(_raise_on_error).lower() == "true":
            ebLogInfo("The flag to raise an exception on error is ENABLED")
            _raise_on_error = True
        else:
            ebLogInfo("The flag to raise an exception on error is DISABLED")
            _raise_on_error = False

        # Review if the golden vmbackup is to be taken on specific nodes
        # The installation of the tool and update of config parameters will
        # be executed in all the Dom0s from this cluster. The reason is that
        # the vmbackup API 'set_param' by design will update all the parameters
        # from the cluster, as we want all Dom0s from each cluster to have the same
        # config parameters. Yes, we may want to take the Golden Backup of specific
        # nodes, e.g. during an ADD NODE operation
        if aDom0List:
            _dom0_list = aDom0List
        else:
            _dom0_list = [_dom0 for _dom0, _ in ebox.mReturnDom0DomUPair()]

        ebLogTrace(f"Exacloud is working with: '{_dom0_list}'")

        try:
            # Install tool, internally gated by a flag from exabox.conf
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Installing the vmbackup tool')
            self.mInstallCurrentVmbackupTool(ebox, aOptions)
            ebox.mLogStepElapsedTime(_step_time, 'Installing the vmbackup tool')
        except Exception as e:
            _warning = f"Failure during 'Installing the vmbackup tool'\n{e}"
            ebLogWarn(_warning)
            if _raise_on_error:
                raise ExacloudRuntimeError(0x095, 0xA, _warning)


        # If the payload has a non-empty vmboss section, we proceeed with the VMBackup
        # OCI resources setup
        if ebVMBackupOCI.mIsVMBOSSEnabled(aOptions):

            # Enable OSS_BACKUP to take the golden reflink
            try:
                _step_time = time.time()
                ebox.mUpdateStatusCS(True, self.step, steplist, aComment='VMBackup enable config updates')
                _vmbackup_mgr = ebCluManageVMBackup(ebox)
                _vmbackup_mgr.mEnableOssVMBackupConfig(aOptions)
                ebox.mLogStepElapsedTime(_step_time, 'VMBackup enable config updates')
            except Exception as e:
                _warning = f"Failure during 'VMBackup enable config updates'\n{e}"
                ebLogWarn(_warning)
                if _raise_on_error:
                    raise ExacloudRuntimeError(0x095, 0xA, _warning)

            # If Users Principals config is set in exabox.conf:
            # Make sure we have a user created for this Customer Tenancy OCID
            # If not, create one user and add it to the vmbackup group along with its
            # credentials
            try:
                _vmbackup_oci_mgr = ebVMBackupOCI(aOptions)
                if ebVMBackupOCI.mIsForceUsersPrincipalsSet():
                    _step_time = time.time()
                    ebox.mUpdateStatusCS(True, self.step, steplist, aComment='VMBackup user setup')
                    _vmbackup_oci_mgr.mSetupVMBackupCustomerUser()
                    ebox.mLogStepElapsedTime(_step_time, 'VMBackup user setup')
            except Exception as e:
                _warning = f"Failure during 'VMBackup user setup'\n{e}"
                ebLogWarn(_warning)
                if _raise_on_error:
                    raise ExacloudRuntimeError(0x095, 0xA, _warning)

            # Make sure we have a bucket creted for this Customer Tenancy OCID
            # If not, create one in the Compartment specified for vmbackup buckets
            # and very important, TAG IT with the User OCID!
            try:
                _step_time = time.time()
                ebox.mUpdateStatusCS(True, self.step, steplist, aComment='VMBackup bucket setup')
                _vmbackup_oci_mgr.mSetupVMBackupClusterBucket()
                ebox.mLogStepElapsedTime(_step_time, 'VMBackup bucket setup')
            except Exception as e:
                _warning = f"Failure during 'VMBackup bucket setup'\n{e}"
                ebLogWarn(_warning)
                if _raise_on_error:
                    raise ExacloudRuntimeError(0x095, 0xA, _warning)

            # Take Golden backup
            try:
                _step_time = time.time()
                ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Taking Golden VM backup')
                self.mTakeGoldenVMBackup(ebox, aOptions, _dom0_list)
                ebox.mLogStepElapsedTime(_step_time, 'Taking Golden VM backup')
            except Exception as e:
                _warning = f"Failure during 'Taking Golden VM backup'\n{e}"
                ebLogWarn(_warning)
                if _raise_on_error:
                    raise ExacloudRuntimeError(0x095, 0xA, _warning)

            finally:
                # Ensure VM is pingable, if not raise a real exception
                # that bubles up. We try up to 600 times (average of ~10 mins)
                _non_pingable = []
                for _, _domU in ebox.mReturnElasticAllDom0DomUPair():
                    if not ebox.mPingHost(_domU, aCount=600 ):
                        ebLogWarn(f"VM {_domU} is not pingable after rebooting "
                                "for reflink")
                        _non_pingable.append(_domU)
                    else:
                        ebLogInfo(f"VM {_domU} is pingable after rebooting "
                            "for reflink")
                if _non_pingable:
                    _warning = (f"VMs {_non_pingable} are not pingable after "
                        "reflink reboot. This is not ignorable")
                    _action = "Check why VMs are not coming up and retry the step"
                    ebLogCritical(_warning, _action)
                    raise ExacloudRuntimeError(0x095, 0xA, _warning)


            # Disable OSS_BACKUP to take the golden reflink
            try:
                _step_time = time.time()
                ebox.mUpdateStatusCS(True, self.step, steplist, aComment='VMBackup disable config updates')
                _vmbackup_mgr = ebCluManageVMBackup(ebox)
                _vmbackup_mgr.mDisableOSSVMBackupConfig(aOptions)
                ebox.mLogStepElapsedTime(_step_time, 'VMBackup disable config updates')
            except Exception as e:
                _warning = f"Failure during 'VMBackup disable config updates'\n{e}"
                ebLogWarn(_warning)
                if _raise_on_error:
                    raise ExacloudRuntimeError(0x095, 0xA, _warning)

        else:
            ebLogError(f"VMBackup to OSS info is missing in ECRA Payload")

        ebLogInfo('*** Exacloud Operation Successful : Golden VMBackup')
        ebLogInfo('csGoldenBackup: Completed doExecute Successfully')

    def undoExecute(self, aExaBoxCluCtrlObj, aOptions, _steplist):
        ebLogInfo('*** csGoldenBackup: Entering undoExecute')
        ebox = aExaBoxCluCtrlObj

        #
        # Delete Cluster level bucket
        #
        # If the payload has a non-empty vmboss section, we proceeed with the VMBackup
        # OCI resources setup
        if ebVMBackupOCI.mIsVMBOSSEnabled(aOptions):

            # Depending on OCI region we'll need to copy certificates and/or update
            # endpoints in the remote vmbackup.conf
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, _steplist, aComment='Delete Cluster level bucket')
            _vmbackup_oci_mgr = ebVMBackupOCI(aOptions)
            _vmbackup_oci_mgr.mDeleteVMBackupClusterBucket()
            ebox.mLogStepElapsedTime(_step_time, 'Delete Cluster level bucket')

        # TODO We may need to delete the whole compartment if no more Customer clusters
        # buckets are present. If we did them at Infra level we could do it at
        # Infra delete endpoint call

        ebLogInfo('*** csGoldenBackup: Completed undoExecute Successfully')

    def mInstallCurrentVmbackupTool(self, aExaBoxCluCtrlObj, aOptions):
        """
        This method will attempt to install the vmbackup tool currently present in
        exacloud 'images' directory, in all the dom0s from this cluster IF
        we have in exabox.conf the feature flag: 'enable_vmbackup_install' under
        'vmbackup'

        If a given Dom0 already has the current version of the tool, this method will
        do nothing.
        If a given Dom0 has a different version, Exacloud will attempt the installation
        as long as there is no ongoing 'vmbackup' process.
        If there is one ongoing process, Exacloud will raise an exception with an
        appropiate log message to retry once the ongonig process finished

        :param aExaBoxCluCtrlObj: a clucontrol object
        :param aOptions: an aoptions context object

        :raises ExacloudRuntimeError: If we fail to install the tool when we are supposed
            to (another process ongoing)
        """


        ebox = aExaBoxCluCtrlObj
        _vmbackup_mgr = ebCluManageVMBackup(ebox)

        _enable_vmbackup_install = get_gcontext().mGetConfigOptions().get(
                                    "vmbackup", {}).get("enable_vmbackup_install", "")

        if _enable_vmbackup_install and _enable_vmbackup_install.lower() == "true":
            ebLogTrace("The VM Backup Install feature is enabled in exabox.conf on the"
                "field: '_enable_vmbackup_install'")
        else:
            ebLogInfo("The VM Backup Install feature is disabled in "
                "exabox.conf field: '_enable_vmbackup_install'. This step is a nop.")
            return 0

        # Before we even start, we can modify the aOptions.jsonconf in here
        # since the only consumer of it in this method is
        # _vmbackup_mgr.mInstallVMbackupOnDom0
        # Currently, during a 'vmbackup install' triggered from ECRA, they send
        # Exacloud a jsonconf like this:
        # {
        #     "DELETE_LOCAL_BACKUP": "False",
        #     "OSS_BACKUP": "disabled",
        #     "REMOTE_BACKUP": "disabled",
        #     "SKIP_CHECKSUM": "True",
        #     "SKIP_IMG": "False"
        # }
        # We want to keep the same structure but enabling OSS_BACKUP

        # We create a copy of aOptions here to not mess with the original in
        # case we need it somewhere else
        _options = copy.deepcopy(aOptions)

        _options.jsonconf = {}
        _options.jsonconf["DELETE_LOCAL_BACKUP"] = "False"
        _options.jsonconf["OSS_BACKUP"] = "enabled"
        _options.jsonconf["REMOTE_BACKUP"] = "disabled"
        _options.jsonconf["SKIP_CHECKSUM"] = "True"
        _options.jsonconf["SKIP_IMG"] = "False"

        # Call vmbackup.py to perform the VM Backup Tool update/install
        ebLogInfo("Initiating VM backup tool install.")
        for _dom0, _ in ebox.mReturnDom0DomUPair():
            _rc = _vmbackup_mgr.mInstallNewestVMBackupTool(_dom0, _options)
            if _rc:
                ebLogInfo("VM backup tool install failed during Golden Backup CS step.")
                raise ExacloudRuntimeError(0x095, 0xA, f"VM Backup tool install failed in dom0: {_dom0}")
        return 0


    def mTakeGoldenVMBackup(self, aExaBoxCluCtrlObj, aOptions, aDom0List):
        """
        This method will attempt to create the Golden VMBackup of the new VMs
        provisioned in aDom0List. We take the golden backup with the VMs shutdown, so
        this method will ensure that happens, as well as making sure we boot them up
        once the backup finishes

        :param aOptions: an aOptions context object
        :param aExaBoxCluCtrlObj: a clucontrol object
        :param aDom0DomUList: a list of two element's list, each of this being
            dom0/domU pairs
        """

        ebox = aExaBoxCluCtrlObj
        _vmbackup_mgr = ebCluManageVMBackup(ebox)
        _dom0_domU_pair = {}

        # Since we only get the Dom0 list and each Dom0 can have multiple VMs, we check
        # which VMs are part of this cluster XML, and then get the list of Dom0DomU pairs
        # TODO: jfsaldan: get all nodes from payload with new change agreed
        for _dom0, _domU in ebox.mReturnDom0DomUPair():
            if _dom0 in aDom0List:
                _dom0_domU_pair[_dom0] = _domU

        if not _dom0_domU_pair:
            _msg = (f"No VMs part of this cluster are present in: '{aDom0List}'")
            ebLogError(_msg)
            raise ExacloudRuntimeError(0x095, 0xA, _msg)

        ebLogInfo("Exacloud will attempt to take the Golden VMBackup of: "
            f"{_dom0_domU_pair}'")

        # Make sure vmbackup tool is installed in all dom0s
        _list_dom0s_missing_tool = set()
        for _dom0, _domU in _dom0_domU_pair.items():
            with connect_to_host(_dom0, get_gcontext()) as _node:
                _vmbackup_installed = _vmbackup_mgr.mCheckVMbackupInstalled(_node)
                ebLogTrace(f"Log from vmbackup operation: {_vmbackup_mgr.mGetVMBackupData()}")

            if  _vmbackup_installed is False:
                _list_dom0s_missing_tool.add(_dom0)

        # If any dom0 is missing the tool, raise an exception
        if _list_dom0s_missing_tool:
            _msg = (f"Exacloud requires the VMBackup tool to be installed so that we "
                "can take the golden backup and push it to OSS. If you want to install "
                "the vmbackup tool when retrying this step, you can set to 'True' the "
                "field 'enable_vmbackup_install' in exabox.conf, reload the "
                "Exacloud agent/workers with: '$EC_ROOT/bin/agent --reload' and retry "
                "this step (this will not interrupt any other exacloud ongoing process "
                "List of dom0s without the tool installed: "
                f"'{_list_dom0s_missing_tool}'")
            ebLogError(_msg)
            raise ExacloudRuntimeError(0x095, 0xA, _msg)

        ebLogInfo("Exacloud detected the vmbackup tool to be present in all Dom0s")

        # Copy User Creds to the dom0s from the payload
        _vmbackup_oci_mgr = ebVMBackupOCI(aOptions)
        _vmbackup_oci_mgr.mSetupVMBackupDom0Cache()

        if ebVMBackupOCI.mIsForceUsersPrincipalsSet():
            _vmbackup_oci_mgr.mUploadCustomerUserCredentialsToDom0()

        _vmbackup_oci_mgr.mUploadCertificatesToDom0()

        # To take the golden backup we need to shutdown the VM.
        ebLogInfo(f"Exacloud will perform the vmbackup of: '{_dom0_domU_pair.items()}'")
        self.mStopVMAndTakeGoldenBackup(aOptions, ebox, _dom0_domU_pair.items())

        return 0

    def mStopVMAndTakeGoldenBackup(self, aOptions, aExaBoxCluCtrlObj, aDom0DomUList):
        """
        This method will shutdown the VMs from aDom0DomUList serially.
        Then, it will take the Golden VM Backup from each VM in parallel.
        Then, it will start up the VMs from aDom0DomUList serially.

        :param aOptions: an aOptions context object
        :param aExaBoxCluCtrlObj: a clucontrol object
        :param aDom0DomUList: a list of two element's list, each of this being
            dom0/domU pairs

        """

        ebox = aExaBoxCluCtrlObj

        # Get max timeout for taking the golden backup
        _timeout_default = "3600"
        _timeout_max_seconds =  get_gcontext().mGetConfigOptions().get(
                "vmbackup", {}).get("max_timeout_backup", _timeout_default)
        try:
            _timeout_max_seconds = int(_timeout_max_seconds)
        except Exception as e:
            _warn = ("Detected invalid value for "
                f"'max_timeout_backup': '{_timeout_max_seconds}'"
                f". Using default value: '{_timeout_default}'."
                f"Error: '{e}'")
            ebLogWarn(_warn)
            _timeout_max_seconds = int(_timeout_default)

        ebLogTrace("Setting max timeout for golden backup to: "
            f"'{_timeout_max_seconds}'")

        try:

            # We try to shutdown all the VMs serially
            for _dom0, _domU in aDom0DomUList:

                with connect_to_host(_dom0, get_gcontext()) as _node:

                    shutdown_domu(_node, _domU, timeout_seconds=600, force_on_timeout=True)
                    ebLogTrace(f"*** VM shutdown: {_domU}")


            # Now let's take the golden backup in parallel
            ebLogTrace(f"Will spawn workers to handle: '{aDom0DomUList}'")

            _plist = ProcessManager()
            _rc_status = _plist.mGetManager().dict()

            # Parallelize execution on dom0s
            for _dom0, _domU in aDom0DomUList:
                _p = ProcessStructure(
                        self.mTakeGoldenReflinkCallback,
                        [_dom0, _domU, _timeout_max_seconds, _rc_status], _dom0)
                _p.mSetMaxExecutionTime(_timeout_max_seconds)
                _p.mSetJoinTimeout(10)
                _p.mSetLogTimeoutFx(ebLogWarn)
                _plist.mStartAppend(_p)

            _plist.mJoinProcess()

            # validate the return codes
            _errors = 0
            for _dom0, _domU in aDom0DomUList:
                if _rc_status[_dom0]:
                    _errors += 1
                    ebLogError(f"Error detected while taking Golden Backup Reflink for {_domU}")
                    _cmd_str = "/bin/rm -rf /opt/oracle/vmbackup/ociconf"
                    with connect_to_host(_dom0, get_gcontext()) as _node:
                        ebLogInfo(f"Cleaning up 'ociconf' dir in {_dom0}")
                        node_exec_cmd(_node, _cmd_str)
            if _errors:
                raise ExacloudRuntimeError(0x095, 0xA, f"Error while taking GoldenBackup Reflink on {_errors} nodes")

        except Exception as e:
            _msg = f"Exception {e}"
            ebLogError(_msg)
            raise

        finally:

            # If an error happened before or not, we try to let all the VM' back up
            for _dom0, _domU in aDom0DomUList:

                with connect_to_host(_dom0, get_gcontext()) as _node:
                    start_domu(_node, _domU, wait_for_connectable=False)


    def mTakeGoldenReflinkCallback(self, aDom0, aDomU, aTimeout, aDictStatus):
        """
        This method is meant to be the callback to trigger the creation of
        the Golden VM Backup reflink of aDomU, from it's aDom0, which will
        be used later on to complete the Golden Backup push to OCI

        Important note:
        Ideally we want this to be part of vmbackup.py to keep vmbackup operations
        in a single place, but there are 2 reasons not to put this method in that file:
        1- To not expose the Golden Backup API, and avoid overriding the golden backup
            of a given VM
        2- The class from vmbackup.py constructor receives a clucontrol object, and we
            saw issues when using multiprocessing with that big object

        :param aDom0: a string representing the Dom0 where to trigger the backup
        :param aDomU: a string representing the DomU of which to take the
            golden vm backup
        :param aTimeout: an integer representing how much seconds to set as
            timeout for the callback execution
        :param aDictStatus: a proxy dict used to collect the result status
            by the process manager
        """

        ebLogInfo(f"Triggering golden vmbackup of: '{aDomU}' from: '{aDom0}'")
        _cmd_str = (f"source {ebCluManageVMBackup.VMBACKUPENV_FILE}; "
            f"timeout {aTimeout} vmbackup backup --vm {aDomU} --gold")
        ebLogTrace(f"Executing: '{_cmd_str}' in: '{aDom0}'")

        with connect_to_host(aDom0, get_gcontext()) as _node:
            _output_vmbackup = node_exec_cmd(_node, _cmd_str)
            ebLogTrace(f"VMBackup output in: '{aDom0}': '{_output_vmbackup}'")

            if _output_vmbackup.exit_code == 0:
                ebLogInfo("Exacloud completed the Golden VMBackup process "
                    f"in: '{aDom0}' for: '{aDomU}'")
                aDictStatus[aDom0] = 0
            else:
                _msg = ("Exacloud failed to complete the Golden VMBackup "
                    f"process in: '{aDom0}' for: '{aDomU}'")
                ebLogError(_msg)
                aDictStatus[aDom0] = 0x095

        return 0
