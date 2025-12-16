"""
 Copyright (c) 2019, 2025, Oracle and/or its affiliates.

NAME:
    cs_createstorage.py - Create Service CREATE STORAGE

FUNCTION:
    Implements the Create Storage step for create service execution 

NOTES:
    Invoked from cs_driver.py 

EXTERNAL INTERFACES: 
    csCreateStorage ESTP_CREATE_STORAGE

INTERNAL CLASSES:

History:
    pbellary  04/20/2023 - 35109538: DISKGROUP CREATION FAILED DUE TO MISSING GRID DISKS 
    siyarlag  01/31/2022 - 31540575: create adbs cloud user
    dekuckre  15/06/2021 - 32982101: Update nonroot password in ZDLRA env
    scoral    05/06/2021 - Added an extra validation to PMEMLOG and PMEMCACHE
                           on cells before OEDA provisioning steps.
    pbellary  04/22/2019 - Bug 	29675019 undo stepwise createservice
    srtata    03/05/2019 - Creation

"""
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogVerbose
from exabox.ovm.clumisc import ebCluPreChecks
from exabox.ovm.csstep.cs_constants import csConstants
from exabox.ovm.csstep.cs_util import csUtil
from exabox.ovm.csstep.cs_base import CSBase
from exabox.ovm.clustorage import ebCluStorageConfig
from exabox.ovm.utils.clu_utils import ebCluUtils
import time

# This class implements doExecute and undoExecute functions
# for the ESTP_CREATE_STORAGE step of create service
# This class primarily invokes OEDA do/undo Setup cell, create cell 
# and create grid disks

class csCreateStorage(CSBase):
    def __init__(self):
        self.step = 'ESTP_CREATE_STORAGE'

    def doExecute(self, aExaBoxCluCtrlObj, aOptions, steplist):
        ebLogInfo('csCreateStorage: Entering doExecute')
        ebox = aExaBoxCluCtrlObj
        ebox.mUpdateStatus('createservice step '+self.step)
        csu = csUtil()
        _csConstants = csu.mGetConstants(ebox, aOptions)
        _clu_utils = ebCluUtils(ebox)
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("createServiceDetails", 'ONGOING', "Create Storage in progress", 'ESTP_CREATE_STORAGE')
        _clu_utils.mUpdateTaskProgressStatus([], 0, "Create Storage", "In Progress", _stepSpecificDetails)

        if ebox.IsZdlraProv():                                                                                                                 
            # Update non root password (es.properties) in ZDLRA env from wallet 
            _pswd = ebox.mGetZDLRA().mGetWalletViewEntry('passwd')                                                                             
            ebox.mUpdateOedaUserPswd(ebox.mGetOedaPath(), "non-root", _pswd) 

        ebox.mAcquireRemoteLock()

        #Delete stale cloud user IDs on cells
        if (ebox.mCheckConfigOption('delete_cloud_user', 'True')):

           try:
               ebox.mDeleteCloudUser(aOptions, False)
           except:
               ebLogError("Error while deleting cloud user")

        #
        # Execute OEDA SETUP_CELL 
        #
        csu.mExecuteOEDAStep(ebox, self.step, steplist, aOedaStep=_csConstants.OSTP_SETUP_CELL, dom0Lock=False)

        ebox.mReleaseRemoteLock()

        #
        # Execute OEDA CREATE_CELL 
        #
        if ebox.mCheckConfigOption('skip_cell_create', 'True'):
            ebLogInfo('csCreateStorage: skip_cell_create is True')
        elif ebox.mCheckCellConfig(aOptions, aStartup=True) and not ebox.mCheckConfigOption('force_cell_config'):
            # CheckCellConfig return True therefore Cells are already configured
            ebLogInfo('*** CheckCellConfig found Cell to be already setup skipping step : '+ebox.mFetchOedaStep(str(_csConstants.OSTP_CREATE_CELL)))
        else:
            csu.mExecuteOEDAStep(ebox, self.step, steplist, aOedaStep=_csConstants.OSTP_CREATE_CELL)

        #
        # Execute OEDA CREATE GRID DISK
        #
        csu.mExecuteOEDAStep(ebox, self.step, steplist, aOedaStep=_csConstants.OSTP_CREATE_GDISK)

        self.mParallelValidateGriddisks(ebox)

        ebLogInfo('csCreateStorage: Completed doExecute Successfully')
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("createServiceDetails", 'DONE', "Create Storage completed", 'ESTP_CREATE_STORAGE')
        _clu_utils.mUpdateTaskProgressStatus([], 100, "Create Storage", "Done", _stepSpecificDetails)

    def undoExecute(self, aExaBoxCluCtrlObj, aOptions, aSteplist):
        ebLogInfo('csCreateStorage: Entering undoExecute')

        _ebox = aExaBoxCluCtrlObj
        _step_list = aSteplist
        _skip_cell_delete = False
        _csu = csUtil()
        _csConstants = _csu.mGetConstants(_ebox, aOptions)
        _clu_utils = ebCluUtils(_ebox)
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("deleteServiceDetails", 'ONGOING', "Undo Create Storage in progress", 'ESTP_CREATE_STORAGE')
        _clu_utils.mUpdateTaskProgressStatus([], 0, "Undo Create Storage", "In Progress", _stepSpecificDetails)

        if _ebox.IsZdlraProv():              
            # Update non root password (es.properties) in ZDLRA env from wallet 
            _pswd = _ebox.mGetZDLRA().mGetWalletViewEntry('passwd')    
            _ebox.mUpdateOedaUserPswd(_ebox.mGetOedaPath(), "non-root", _pswd) 

        if not _ebox.mCheckConfigOption('run_all_undo_steps','True') and \
           _ebox.mGetCmd() in ['vmgi_delete', 'gi_delete', 'deleteservice']:

            _csu.mDeleteVM(aExaBoxCluCtrlObj, self.step, aSteplist)

        _csu.mExecuteOEDAStep(_ebox, self.step, _step_list, aOedaStep=_csConstants.OSTP_CREATE_GDISK, undo=True, dom0Lock = False)

        _ebox.mAcquireRemoteLock()

        # Delete ADBS cloud_user during delete service
        if _ebox.mGetCmd() in ['deleteservice']:
            _ebox.mDeleteAdbsUser(aOptions)

        #Delete cluster stale cloud user IDs on cells
        try:
            _ebox.mDeleteCloudUser(aOptions, False)
        except:
           ebLogError("Error while deleting cloud user")

        _ebox.mReleaseRemoteLock()

        #
        # Grid Disk Force Delete (this is required as most of the time GridDisks delete step will fail
        # (e.g. ASM/DB not shutdown properly due to inability to access the DomUs/VMs)
        #
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, _step_list, aComment='Running Delete Force Grid Disks POSTVM')
        if _ebox.mCheckCellsServicesUp():
            _ebox.mGetStorage().mDeleteForceGridDisks()
        else:
            ebLogWarn('*** Cell Services are not running, unable to delete Grid disks')
        _ebox.mLogStepElapsedTime(_step_time, 'Running Delete Force Grid Disks')

        if _ebox.mCheckConfigOption('skip_cell_delete', 'True'):
            ebLogWarn('*** Delete Cell Disk has been disabled - skipping OEDA step -')
            _skip_cell_delete = True

        if _ebox.SharedEnv():
            _ebox.mAcquireRemoteLock()
            #do not execute undostep 6 override if any other VM exists
            if not _ebox.mIsLastCluster(_ebox.mReturnCellNodes()):
                ebLogWarn("*** Another cluster's VM exists. skipping OEDA undostep 6 - Delete Cell Disk")
                _skip_cell_delete = True
            _ebox.mReleaseRemoteLock()

        _ebox.mUpdateStatusCS(True, self.step, _step_list, aComment='Checking if cell disks state is normal (this operation can take a long time)')
        _step_time = time.time()
        _ebox.mCellAssertNormalStatus(aOptions)
        _ebox.mLogStepElapsedTime(_step_time, 'Checking cell disks status')

        # Refresh the UI to reflect the correct step by
        if not _skip_cell_delete:
            _csu.mExecuteOEDAStep(_ebox, self.step, _step_list, aOedaStep=_csConstants.OSTP_CREATE_CELL, undo=True, dom0Lock = False)

        try:
            _csu.mExecuteOEDAStep(_ebox, self.step, _step_list, aOedaStep=_csConstants.OSTP_SETUP_CELL, undo=True, dom0Lock = False)
        except:
            ebLogWarn('*** undo OSTP_SETUP_CELL  did not completed successully')

        ebLogInfo('csCreateStorage: Completed undoExecute Successfully')
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("deleteServiceDetails", 'DONE', "Undo Create Storage completed", 'ESTP_CREATE_STORAGE')
        _clu_utils.mUpdateTaskProgressStatus([], 100, "Undo Create Storage", "Done", _stepSpecificDetails)


