"""
 Copyright (c) 2019, 2025, Oracle and/or its affiliates.

NAME:
    cs_dbinstall.py - Create Service DB INSTALL

FUNCTION:
   Implements the starter DB creation 

NOTES:
    Invoked from cs_driver.py
    Same as "db_install" command

EXTERNAL INTERFACES: 
    csDBInstall         ESTP_DB_INSTALL

INTERNAL CLASSES:

History:
    srtata      04/23/2019 - 29556301: implement doExecute
    dekuckre    04/05/2019 - Creation

"""

import time
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogVerbose
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.ovm.csstep.cs_constants import csConstants
from exabox.ovm.AtpUtils import ebAtpUtils
from exabox.ovm.csstep.cs_base import CSBase
from exabox.ovm.atp import AtpSetupSecondListener, AtpSetupASMListener, AtpAddScanname2EtcHosts
from exabox.ovm.cluexaccatp import ebExaCCAtpListener
from exabox.ovm.utils.clu_utils import ebCluUtils

# This class implements doExecute and undoExecute functions
# for the ESTP_DB_INSTALL step of create service
class csDBInstall(CSBase):
    def __init__(self):
        self.__step = 'ESTP_DB_INSTALL'

    def doExecute(self, aExaBoxCluCtrlObj, aOptions, steplist):
        ebLogInfo('csDBInstall: Entering doExecute')
        ebox = aExaBoxCluCtrlObj
        ebox.mUpdateStatus('createservice step '+self.__step)
        _clu_utils = ebCluUtils(ebox)
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("createServiceDetails", 'ONGOING', "DB Install in progress", 'ESTP_DB_INSTALL')
        _clu_utils.mUpdateTaskProgressStatus([], 0, "DB Install", "In Progress", _stepSpecificDetails)

        if not ebox.mCheckNIDEnvironment():
            # checking if recreate is necessary
            ebLogInfo('Verifying GI/Clusterware version')
            _mrecreategridrequired = ebox.mCheckGridVersion()
            if _mrecreategridrequired is True:
                ebLogInfo("*** Recreate service necessary. GI/Clusterware not at the required version ***")
                return ebError(0x0725)

            ebLogInfo("*** Updating the environment to support NID")
            # 2- patching the vms
            ebLogInfo("*** Update bits in the domU image")
            _rt = ebox.mUpdateDBNIDBits(aOptions)
            if _rt:
               # add error code in case of NID update
               return ebError(0x0510)
            ebLogInfo('csDBInstall: Entering mExecuteInstallPostGINID')
            ebox.mExecuteInstallPostGINID()
            ebLogInfo('csDBInstall: Completed mExecuteInstallPostGINID')
        step_list = [csConstants.OSTP_PREDB_INSTALL, csConstants.OSTP_DBNID_INSTALL, csConstants.OSTP_APPLY_FIX_NID, csConstants.OSTP_POSTDB_INSTALL, csConstants.OSTP_DG_CONFIG, csConstants.OSTP_END_INSTALL]
        _enable_exachk = ebox.mCheckConfigOption('enable_exachk')
        if _enable_exachk:
            if 'post_create_starterdb' in _enable_exachk and _enable_exachk['post_create_starterdb'] == 'True':
                ebLogInfo('csDBInstall: inserting EXACHK sub step')
                step_list.insert(step_list.index(csConstants.OSTP_END_INSTALL), csConstants.OSTP_INSTALL_EXCHK)
        db_step_list = [csConstants.OSTP_APPLY_FIX_NID]

        aCmd = self.__step
        ebLogInfo('csDBInstall: Entering mExecuteInstallStarterDBNID')
        _rc = ebox.mExecuteInstallStarterDBNID(aCmd, aOptions, ebox.mGetOedaPath(), step_list, db_step_list)
        ebLogInfo('csDBInstall: Completed mExecuteInstallStarterDBNID')

        # Only Setup ATP Backup Listener if StarterDBNID is successful
        if _rc == 0:
            for _dom0, _domU in ebox.mReturnDom0DomUPair():
                if ebAtpUtils.isVMAtp(_dom0) and ebox.mCheckClusterNetworkType() and not ebox.mIsOciEXACC():
                    ebLogInfo("*** ATP etc/hosts on %s ***" % _domU)
                    AtpAddScanname2EtcHosts(None, ebox.mGetATP(), _domU).mExecute()
                ### Only need to be run on one dom0
                if ebAtpUtils.isVMAtp(_dom0) and ebox.mCheckClusterNetworkType() and not ebox.mIsOciEXACC():
                    ebLogInfo("*** ATP Listener on %s ***" % _domU)
                    AtpSetupSecondListener(None, ebox.mGetATP(), ebox.mReturnDom0DomUPair(), ebox.mGetMachines(), ebox.mGetNetworks(), None, ebox.mGetClusters, aOptions).mExecute()
                    ebLogInfo("*** Completed AtpSetupSecondListener")
                    AtpSetupASMListener(None, ebox, None).mExecute()
                    ebLogInfo("*** Completed AtpSetupASMListener")

                if ebox.isATP() and ebox.mIsOciEXACC():
                        _node = exaBoxNode(get_gcontext())
                        # First domU
                        _node.mConnect(aHost=ebox.mReturnDom0DomUPair()[0][1])
                        _listener_info = ebExaCCAtpListener.sExtractInfoFromDomU(_node)
                        if ebox.mIsDebug():
                            ebLogDebug("ExaCCAtp Listener Info: {}".format(_listener_info))
                        
                        if not _listener_info:
                            ebLogWarn("Error on obtaining ATP Listener info, skip setup")
                        else:
                            # Previous function gave a tuple of the arguments, hence the *
                            _listener_commands = ebExaCCAtpListener.sGenerateListenerCommands(*_listener_info)
                            for _cmd in _listener_commands:
                                _node.mExecuteCmdLog(_cmd)
                        _node.mDisconnect()

        ebLogInfo("*** _rc from mExecuteInstallStarterDBNID: %s ***" % str(_rc))
        ebLogInfo('csDBInstall: Completed doExecute Successfully')
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("createServiceDetails", 'DONE', "DB Install completed", 'ESTP_DB_INSTALL')
        _clu_utils.mUpdateTaskProgressStatus([], 100, "DB Install", "Done", _stepSpecificDetails)
        return _rc

    def undoExecute(self, aExaBoxCluCtrlObj, aOptions, steplist):
        _ebox = aExaBoxCluCtrlObj

        ebLogVerbose('csDBInstall: Entered undoExecute')
        _clu_utils = ebCluUtils(_ebox)
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("deleteServiceDetails", 'ONGOING', "Undo DB Install in progress", 'ESTP_DB_INSTALL')
        _clu_utils.mUpdateTaskProgressStatus([], 0, "Undo DB Install", "In Progress", _stepSpecificDetails)

        # For starter db nid
        # the delete db is the same as the additional
        if _ebox.mCheckNIDStarterDB():

            _elastic_op,_nodelist = _ebox.mCheckNodeListParam()
            if _elastic_op is True:
                _dom0U = _ebox.mCheckNodeList(_nodelist)
                _db_install = _ebox.mCheckInstallDB(_dom0U)
                if _db_install is False:
                    return ebError(0x0514)

            _rc, _cmd = _ebox.mRunCmdScript("addb_delete")
            if _rc:
                return ebError(0x0504)
            else:
                _ebox.mATPUnlockListeners() #ATP will be detected from inside the function
                return 0

        _ebox.mUpdateStatus('db_delete')

        #
        # Update XML configuration 
        #
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.__step, steplist, aComment='Copy/Update Cluster Configuration in DOM0')
        _ebox.mCopyFileToClusterConfiguration(_ebox.mGetConfigPath(), 'db_delete_cluster.xml')
        _ebox.mLogStepElapsedTime(_step_time, 'PREDB DELETE : Copy/Update Cluster Configuration in DOM0')
        #
        # Run External Scripts
        #
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.__step, steplist, aComment='Running External PREDB Scripts')
        _ebox.mRunScript(aType='*',aWhen='pre.db_delete')
        _ebox.mLogStepElapsedTime(_step_time, 'PREDB DELETE : Running External Scripts')

        ebLogVerbose('csDBInstall: Completed undoExecute Successfully')
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("deleteServiceDetails", 'DONE', "Undo DB Install completed", 'ESTP_DB_INSTALL')
        _clu_utils.mUpdateTaskProgressStatus([], 100, "Undo DB Install", "Done", _stepSpecificDetails)


