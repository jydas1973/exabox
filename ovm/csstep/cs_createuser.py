"""
 Copyright (c) 2019, 2025, Oracle and/or its affiliates.

NAME:
    cs_createuser.py - Create Service CREATE USER

FUNCTION:
    Implements the Create User step for create service execution 

NOTES:
    Invoked from cs_driver.py 

EXTERNAL INTERFACES: 
    csCreateUser     ESTP_CREATE_USER

INTERNAL CLASSES:

History:
    prsshukl  11/19/2025 - Bug 38037088 - BASE DB -> MOVE THE DO/UNDO STEPS FOR
                           BASEDB TO A NEW FILE IN CSSTEP , REMOVE CODE THAT IS
                           UNNECESSARY FOR BASEDB
    prsshukl  06/11/2025 - Bug 38048906 - EXADB-XS -> BASE DB -> OPC USER CREATION IN EXACLOUD LAYER
    prsshukl  04/16/2024 - Enh 37827765 - EXADB-XS 19C : SKIP CREATE USER STEP STEP FOR BASEDB
    aararora  07/22/2024 - Bug 36864046: Cleanup ssh directory for opc user
                           during undo step of create user.
    pbellary  06/21/2024 - ENH 36690743 - EXACLOUD: IMPLEMENT OEDA STEPS FOR EXASCALE CREATE SERVICE
    dekuckre  05/02/2024 - 36572947: Remove fqdn in create user step and not in install-cluster step.
    jesandov  08/06/2023 - 35479987: Passworless with ECDSA
    dekuckre  07/20/2021 - 33079527: Move mSecureDom0SSH to prevm step 
    dekuckre  06/15/2021 - 32982101: Update nonroot password in ZDLRA env
    pbellary  04/22/2019 - Bug  29675019 undo stepwise createservice
    srtata    03/05/2019 - Creation

"""
from exabox.core.Node import exaBoxNode
from exabox.ovm.csstep.cs_util import csUtil
from exabox.ovm.csstep.cs_base import CSBase
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn
from exabox.ovm.csstep.cs_constants import csConstants
from exabox.ovm.utils.clu_utils import ebCluUtils
from exabox.ovm.csstep.exabasedb.cs_basedb_util import csBaseDbUtil


# This class implements doExecute and undoExecute functions
# for the ESTP_CREATE_USER step of create service
# This class primarily invokes OEDA do/undo create User, secure and remap users
class csCreateUser(CSBase):
    def __init__(self):
        self.step = 'ESTP_CREATE_USER'

    def doExecute(self, aExaBoxCluCtrlObj, aOptions, steplist):
        ebLogInfo('csCreateUser: Entering doExecute')
        _ebox = aExaBoxCluCtrlObj
        _clu_utils = ebCluUtils(_ebox)
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("createServiceDetails", 'ONGOING', "Create User in progress", 'ESTP_CREATE_USER')
        _clu_utils.mUpdateTaskProgressStatus([], 0, "Create User ", "In Progress", _stepSpecificDetails)

        if _ebox.IsZdlraProv():                                         
            # Update non root password (es.properties) in ZDLRA env from wallet
            _pswd = _ebox.mGetZDLRA().mGetWalletViewEntry('passwd')                                                                             
            _ebox.mUpdateOedaUserPswd(_ebox.mGetOedaPath(), "non-root", _pswd) 

        self.mCreateUser(_ebox, aOptions, steplist)

        ebLogInfo('csCreateUser: Completed doExecute Successfully')
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("createServiceDetails", 'DONE', "Create User completed", 'ESTP_CREATE_USER')
        _clu_utils.mUpdateTaskProgressStatus([], 100, "Create User ", "Done", _stepSpecificDetails)

    def undoExecute(self, aExaBoxCluCtrlObj, aOptions, aSteplist):
        ebLogInfo('csCreateUser: Entering undoExecute')
        _ebox = aExaBoxCluCtrlObj
        _step_list = aSteplist
        _clu_utils = ebCluUtils(_ebox)
        _csu = csUtil()
        _csConstants = _csu.mGetConstants(_ebox, False)
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("deleteServiceDetails", 'ONGOING', "Undo Create User in progress", 'ESTP_CREATE_USER')
        _clu_utils.mUpdateTaskProgressStatus([], 0, "Undo Create User ", "In Progress", _stepSpecificDetails)
            
        if _ebox.IsZdlraProv():                        
            # Update non root password (es.properties) in ZDLRA env from wallet
            _pswd = _ebox.mGetZDLRA().mGetWalletViewEntry('passwd')    
            _ebox.mUpdateOedaUserPswd(_ebox.mGetOedaPath(), "non-root", _pswd) 
        
        _csu = csUtil()
        _csu.mExecuteOEDAStep(_ebox, self.step, _step_list, aOedaStep=_csConstants.OSTP_CREATE_USER, undo=True,dom0Lock=False)
        try:
            self.mDeleteOpcSSHDirectory(_ebox)
        except Exception as ex:
            ebLogWarn(f"Could not remove /home/opc/.ssh directory during undo step. Error: {ex}.")

        ebLogInfo('csCreateUser: Completed undoExecute Successfully')
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("deleteServiceDetails", 'DONE', "Undo Create User completed", 'ESTP_CREATE_USER')
        _clu_utils.mUpdateTaskProgressStatus([], 100, "Undo Create User ", "Done", _stepSpecificDetails)


        

