#
# cellhandlerclusterless.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates. 
#
#    NAME
#      cellhandlerclusterless.py - Clusterless Cell Patching Functionality
#
#    DESCRIPTION
#      Provide basic/core cell clusterless patching API (prereq, patch,
#      rollback_prereq, and rollback) for managing the Exadata patching in
#      the cluster implementation.
#
#      This handler extends the cellhandler class and it overrides the methods
#      which are required for clusterless patching of cell. Taskhandler will create
#      an object of this class for clusterless patching of cell
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    antamil     08/14/25 - Bug 38299211 Perform ASM disk activation check in 
#                           non-rolling
#    antamil     07/29/25 - Bug 38221892 Cleanup known_host file at the end of patch
#    antamil     01/31/25 - Enh 37300427 -Creation: Enable clusterless cell patching
#                           using management host

import copy
import os, sys
import traceback
import json
import datetime
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.infrapatching.handlers.targetHandler.cellhandler import CellHandler
from exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler import InfraPatchManager
from exabox.infrapatching.helpers.clusterlesshelper import ClusterlessPatchHelper
from exabox.infrapatching.utils.constants import *
from exabox.infrapatching.core.infrapatcherror import *
from exabox.infrapatching.utils.utility import mRegisterInfraPatchingHandlers, PATCH_BASE, mFormatOut, mReadPatcherInfo, mGetFirstDirInZip,\
  mReadCallback, mErrorCallback, mGetInfraPatchingHandler, flocked, mChangeOwnerofDir, mGetLaunchNodeConfig
from exabox.ovm.clumisc import ebCluSshSetup, ebCluPreChecks
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure
from exabox.utils.common import version_compare
sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))

class CellHandlerClusterless(CellHandler):
    # Cell and Switch Related  Variables , since they are common for both
    def __init__(self, *initial_data, **kwargs):
        super(CellHandlerClusterless, self).__init__(*initial_data, **kwargs)
        self.mPatchLogInfo("CellHandlerClusterless")
        mRegisterInfraPatchingHandlers(INFRA_PATCHING_HANDLERS, [PATCH_CELL], self)
        self.__ssh_env_setup_switches_cell = ebCluSshSetup(self.mGetCluControl())
        self._cells_switches_remote_base = None
        self.__clusterless_patch_helper=ClusterlessPatchHelper(aHandler=self)


    def mGetClusterlessHelper(self):
        return self.__clusterless_patch_helper

    def mSetcellSwitchesBaseEnvironment(self):

        #Sets all the variables used to select the dom0 that will run the patchmgr.
        if self.mGetCellSwitchesLocalPatchZip():
            # Name of the patch zip file (without the path)
            self.mSetCellIBPatchZipName(self.mGetCellSwitchesLocalPatchZip().split("/")[-1])
            # Base dir to copy the patch onto the remote dom0
            _launch_node_type=self.mGetLaunchNodeType()
            if _launch_node_type == None:
                _launch_node_type=LAUNCHNODE_TYPE_COMPUTE
            self.mSetCellSwitchesPatchBase(mGetLaunchNodeConfig(_launch_node_type, 'patch_base') + self.mGetCellIBPatchZipName() + "/")
            self._cells_switches_remote_base = mGetLaunchNodeConfig(_launch_node_type, 'patch_base')
            # Full path to the zip patch on the remote dom0
            self.mSetCellSwitchesPatchZip(self.mGetCellSwitchesPatchBase() + \
                                                self.mGetCellIBPatchZipName())
            # Full path to the unziped patch folder on the remote dom0
            self.mSetCellSwitchesPatchBaseAfterUnzip(self.mGetCellSwitchesPatchBase() +
                                                              mGetFirstDirInZip(self.mGetCellSwitchesLocalPatchZip()))
            # Full path to the patchmgr script on the remote dom0
            self.mSetCellIBPatchMgr(self.mGetCellSwitchesPatchBaseAfterUnzip() + "patchmgr")
            self.__cells_switches_patch_zip_size_mb = int(os.path.getsize(self.mGetCellSwitchesLocalPatchZip())) >> 20
            # NOTE size is *2 of the zip file because we need to copy the zip, and unzip +
            # EXADATA_PATCH_WORKING_SPACE_MB for any logs generated?
            self.__cells_switches_patch_necessary_space_mb = int((self.__cells_switches_patch_zip_size_mb * 2 +
                                                                self.mGetExadataPatchWorkingSpaceMB()))
            self.mSetPatchmgrLogPathOnLaunchNode(self.mGetCellSwitchesPatchBaseAfterUnzip() + "patchmgr_log_" + self.mGetMasterReqId())
            self.mSetTargetVersion((self.mGetCellSwitchesLocalPatchZip()[::-1].split("/")[0])[::-1].replace(".patch","").replace(".zip",""))


    def mGetCellSwitchesPatchNecessarySpaceMB(self):
        return self.__cells_switches_patch_necessary_space_mb


    def mSetLaunchNodeAsPatchBase(self,
                                   aLaunchNodeCandidates,
                                   aLocalPatchZipFile,
                                   aPatchZipName, aPatchZipSizeMb,
                                   aRemotePatchBase, aRemotePatchZipFile,
                                   aRemotePatchmgr, aRemoteNecessarySpaceMb, aPatchBaseDir,
                                   aSuccessMsg="", aMoreFilesToCopy=None):

        return self.mGetClusterlessHelper().mSetLaunchNodeAsPatchBase(
                                   aLaunchNodeCandidates,
                                   aLocalPatchZipFile,
                                   aPatchZipName, aPatchZipSizeMb,
                                   aRemotePatchBase, aRemotePatchZipFile,
                                   aRemotePatchmgr, aRemoteNecessarySpaceMb, aPatchBaseDir,
                                   aSuccessMsg, aMoreFilesToCopy)



    # Prepare environment before any operation
    def mPrepareEnvironment(self, aDom0, aNodesList, aBaseDir, aAdminSwitch=False):
        """
        Creates the input files and sets passwordless ssh between the dom0
        and the nodes that will be patched.
        """
        _key = None

        # Update status
        self.mUpdatePatchStatus(True, STEP_PREP_ENV + '_' + self.mGetCurrentTargetType())

        # Set passwordless connection between dom0 and cells/ibswitches
        if self.__ssh_env_setup_switches_cell:
            # Setting up passwdless ssh is different in case of RoceSwitches.
            if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForClusterless'):
                with open(LOCK_FILE_NAME, 'a') as file:
                    self.__ssh_env_setup_switches_cell.mConfigureSshForMgmtHost(aDom0, aNodesList,
                                                                                EXAPATCHING_KEY_TAG,
                                                                                self._cells_switches_remote_base)
                    self.mGetCluPatchCheck().mVerifyPatchmgrSshConnectivityBetweenExadataHosts(
                        aNodesList,
                        aDom0,
                        aSshUser='opc')
            else:
                _key = self.__ssh_env_setup_switches_cell.mSetSSHPasswordlessForClusterless(aDom0, aNodesList)

                # From Exadata image 23.x, the target OS will be upgraded to OL8 where
                # dsa keys become obsolete. This block checks presence of any obsolete
                # keys and remove from cells

                _ssh_keys_remove_config = self.mGetSshKeysRemoveConfig()

                if (version_compare(self.mGetTargetVersion(), "23.1.0.0.0") >= 0 and
                        PATCH_CELL in _ssh_keys_remove_config and
                        'auth_keys_remove_patterns' in _ssh_keys_remove_config[PATCH_CELL]):

                    self.mPatchLogInfo(f'Starting obsolete SSH keys check on Cells : {json.dumps(aNodesList, indent=4)}')
                    _auth_keys_remove_patterns = _ssh_keys_remove_config[PATCH_CELL]['auth_keys_remove_patterns']
                    if _auth_keys_remove_patterns:
                        self.mPatchLogInfo(f'SSH Key Patterns to be removed : {_auth_keys_remove_patterns}')
                        self.__ssh_env_setup_switches_cell.mRemoveSshKeysAndFilesFromHosts(aDom0, aNodesList, _auth_keys_remove_patterns)
                self.mPatchLogInfo(f"Passwordless ssh validation performed between {str(aNodesList)} and {aDom0}")
                self.mGetCluPatchCheck().mVerifyPatchmgrSshConnectivityBetweenExadataHosts(aNodesList, aDom0)
            return _key

    # Clean environment after any operation
    def mCleanEnvironment(self, aDom0, aNodesList, aListFilePath, aBaseDir, aLogDir, aNodeType, aPatchExitStatus):
        """
        Deletes input files and passwordless ssh between nodes. It will also
        copy the log files from the remote dom0 to the local log directory.
        """

        self.mPatchLogInfo(f"Copying diagnostic logs to exacloud: {self.mGetLogPath()}")

        # Update status
        self.mUpdatePatchStatus(True, STEP_CLEAN_ENV + '_' + aNodeType)

        self.mGetPatchMgrOutFiles(aDom0, aLogDir, '')

        '''
         Collect patchmgr diag logs for debugging only
         when the final exit code from patch operation 
         is not PATCH_SUCCESS_EXIT_CODE.
        '''
        if aPatchExitStatus != PATCH_SUCCESS_EXIT_CODE:
            self.mGetPatchMgrDiagFiles(aDom0, aNodeType, aNodesList, aLogDir)
        else:
            self.mPatchLogInfo("Patchmgr diag logs are not collected in case of a successful infra patch operation.")

        # Get patchmgr console that we generate using nohup
        self.mGetPatchMgrMiscLogFiles(aDom0, aLogDir)

        # Get <cellname>.log files from the patchmgr_log_<date> location
        self.mGetCellLogs(aDom0, aNodesList, aLogDir)

        '''
         Example snippet of aBaseDir and aLogDir.

         aBaseDir : /EXAVMIMAGES/21.1.0.0.0.210319.switch.patch.zip/patch_switch_21.1.0.0.0.210319/ 
         aLogDir : /EXAVMIMAGES/21.1.0.0.0.210319.switch.patch.zip/patch_switch_21.1.0.0.0.210319/patchmgr_log_db9dd643-cffa-4448-95f0-c530835da603

         When appropriate logs are generate under the above locations, logs are copied onto exacloud 
         log location as below.

         aBaseDir :

            2021-07-26 07:46:37-0700 - RoceSwitchHandler - INFO - Copying switch_admin.log
            file from node - scaqan17adm01.us.oracle.com , location -
            /EXAVMIMAGES/21.2.2.0.0.210709.switch.patch.zip/patch_switch_21.2.2.0.0.210709/

         aLogDir :

            2021-08-16 01:34:06-0700 - INFO - SwitchHandler - INFO - Copying
            upgradeIBSwitch.log file from node - slcs27adm03.us.oracle.com , location -
            /EXAVMIMAGES/21.1.0.0.0.210319.switch.patch.zip/patch_switch_21.1.0.0.0.210319/
            patchmgr_log_db9dd643-cffa-4448-95f0-c530835da603

        '''

        # Print all the log details at the end of log files copy.
        self.mPrintPatchmgrLogFormattedDetails()

        '''
         Clean ssh configuration

         Note : Currently passwordless ssh cleanup is not done for the
                Roceswitches/Adminswitches by default.

                Keys cleanup for admin and roceswitch patching must not 
                go through the below process and need to be handled as part
                of patchmgr process.
        '''
        if self.__ssh_env_setup_switches_cell:
            if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForClusterless'):
                self.__ssh_env_setup_switches_cell.mCleanupSSHConfigForMgmtHost(aDom0,
                                                                                aNodesList)
                self.mGetCluPatchCheck().mVerifyPatchmgrSshConnectivityBetweenExadataHosts(
                    aNodesList,
                    aDom0,
                    aStage="PostPatch",
                    aSshUser='opc')
                with open(LOCK_FILE_NAME, 'a') as file:
                    with flocked(file):
                        self.__ssh_env_setup_switches_cell.mCleanupSSHConfigFileOnMgmtHost(aDom0, aNodesList)
            else:
                self.__ssh_env_setup_switches_cell.mCleanSSHPasswordlessForClusterless(aDom0, aNodesList)
                self.__ssh_env_setup_switches_cell.mRemoveFromKnownHosts(aDom0, aNodesList, False)
                self.mGetCluPatchCheck().mVerifyPatchmgrSshConnectivityBetweenExadataHosts(
                    aNodesList,
                    aDom0,
                    aStage="PostPatch")


        # Delete input file
        self.mDeleteNodesFile(aListFilePath, aDom0)



    def mGetPatchMgrOutFiles(self, aDom0, aRemotePath, aCode=''):
        return self.mGetClusterlessHelper().mGetPatchMgrOutFiles(aDom0, aRemotePath, aCode)


    def mGetCellLogs(self, aDom0, aNodesList, aLogDir):
        """
        Copy cell patching diagnostic files with naming convention as
        <cellhostname>.log and these logs would be generated during cell upgrade
        and same needs to be copied toi ECRA from launch node.
        """

        _node = exaBoxNode(get_gcontext())
        self.mSetConnectionUser(_node)
        _node.mConnect(aHost=aDom0)

        try:
            # Copy <cellnmae>.log files from patchmgr stage location on Dom0 to local node.
            for _cell in aNodesList:
                _cmd = f"ls {os.path.join(aLogDir, _cell + '.' + 'log')}"
                _node.mExecuteCmd(_cmd) 
                if _node.mGetCmdExitStatus() == 0:
                    self.mSetListOfLogsCopiedToExacloudHost(os.path.join(aLogDir, _cell + ".log"))
                    _node.mCopy2Local(os.path.join(aLogDir, _cell + '.' + 'log'),
                                      os.path.join(self.mGetLogPath(), _cell + '.' + 'log'))
                else:
                    self.mPatchLogWarn(
                        f'{os.path.join(aLogDir, _cell + "." + "log")} not found on the launch node : {aDom0}')
        except Exception as e:
            self.mPatchLogWarn(
                f'Error while copying {_cell}.log file from node - {aLogDir} , location - {str(e)} to exacloud location - {self.mGetLogPath()}')
            self.mPatchLogTrace(traceback.format_exc())

        # Disconnect Dom0
        if _node.mIsConnected():
            _node.mDisconnect()
        return

    def mGetPatchMgrDiagFiles(self, aDom0, aNodeType, aNodeList, aRemotePath):

        # First get the files from the DOM0 which ran the patchmgr
        if aNodeType == PATCH_CELL:

            # Notification file.
            _notifications_dir = os.path.join(aRemotePath, "notifications")
            _cmd_list_diag_files = f'find {aRemotePath} -name "patchmgr_diag_*"'
            _patch_failure_cell_nodes = []
            _cell_diag_files = {}
            _patchmgr_xml_data = None

            ### IMPORTANT ###
            # This implementation always will copy the most recent patmgr file
            # found for a given cell. Is there a certain way to know which files
            # were created during a cleanup task?
            ### -------- ###

            _node = exaBoxNode(get_gcontext())
            self.mSetConnectionUser(_node)
            _node.mConnect(aHost=aDom0)

            try:
                _cmd = f"ls {_notifications_dir}"
                _node.mExecuteCmd(_cmd)

                if _node.mGetCmdExitStatus == 0:
                    # Excluding file name starting with "_" from patchnotification directory
                    _cmd_notification_file_cmd = f"ls {_notifications_dir} | grep -v '_$' | tail -1"
                    _i, _o, _e = _node.mExecuteCmd(_cmd_notification_file_cmd)
                    _out = _o.readlines()
                    if len(_out) > 0:
                        _patch_notification_file = _out[0]

                    if _patch_notification_file:
                        _notification_file_path = os.path.join(_notifications_dir, _patch_notification_file)
                        _read_patchmgr_xml_cmd = f"cat {_notification_file_path} 2>/dev/null"
                        _i, _o, _e = _node.mExecuteCmd(_read_patchmgr_xml_cmd)
                        if _o:
                            _patchmgr_xml_data = _o.read()

                if _patchmgr_xml_data:
                    _patch_failure_cell_nodes = self.mParseCellPatchmgrXml(_patchmgr_xml_data)

                # Find all the patchmgr_diag* files availables. It is possible
                # that this patchmgr was used before so it is important to get
                # the last files generated
                for _cell in _patch_failure_cell_nodes:
                    _cell_diag_files[_cell] = {'path': '',
                                               'group': []}

                _in, _out, _err = _node.mExecuteCmd(_cmd_list_diag_files)
                _output = _out.readlines()

                if _output:
                    # For each files, we parse its name (which has the date of
                    # creation).
                    for _o in _output:
                        _file = _o.strip().split("/")[-1]
                        _re_out = re.match("patchmgr_diag_(.+)_([0-9]{4})-" \
                                           "([0-9]{2})-([0-9]{2})_([0-9]{2})_" \
                                           "([0-9]{2})_([0-9]{2})\.tar\.bz2", _file)
                        if _re_out:
                            _group = _re_out.groups()
                            _current = ''
                            for _cell in _patch_failure_cell_nodes:
                                if _cell.startswith(_group[0]):
                                    _current = _cell
                                    break

                            # For each cell, we get only the most recent
                            # patchmgr_diag file created
                            if _current:
                                _update = True
                                if _cell_diag_files[_current]['group']:
                                    for _ind in range(1, 7):
                                        if _group[_ind] != _cell_diag_files[_current]['group'][_ind]:
                                            if _group[_ind] < _cell_diag_files[_current]['group'][_ind]:
                                                _update = False
                                            break

                                if _update:
                                    _cell_diag_files[_current]['path'] = _file
                                    _cell_diag_files[_current]['group'] = _group


                # Each patchmgr file is copied from the dom0 to the localhost.
                self.mPatchLogInfo(f"Collecting diagnostics logs from: {aRemotePath} to: {self.mGetLogPath()}")
                for _cell in _cell_diag_files:
                    if _cell_diag_files[_cell]['path'] != '':
                        _node.mExecuteCmd(f"ls {os.path.join(aRemotePath, _cell_diag_files[_cell]['path'])}")
                        if _node.mGetCmdExitStatus() == 0:
                            self.mSetListOfLogsCopiedToExacloudHost(
                                os.path.join(aRemotePath, _cell_diag_files[_cell]['path']))
                            _node.mCopy2Local(os.path.join(aRemotePath, _cell_diag_files[_cell]['path']),
                                              os.path.join(self.mGetLogPath(), _cell_diag_files[_cell]['path']))
                    else:
                        self.mPatchLogInfo(f"No diagnosis files found for cell {_cell}")
            except Exception as e:
                self.mPatchLogWarn(f'Error while copying cell diagnosis files: {str(e)}')
                self.mPatchLogTrace(traceback.format_exc())
            if _node.mIsConnected():
                _node.mDisconnect()
        return

    def mGetShutDownServices(self):
        self.mPatchLogWarn(f'Returning mGetShutDownServices to true for clusterless non-rolling patching')
        return True

