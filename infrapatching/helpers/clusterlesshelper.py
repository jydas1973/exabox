#
# singlevmhelper.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates. 
#
#    NAME
#      clusterlesshelper.py - Place holder for common functionalities for
#      clusterless patching
#
#    DESCRIPTION
#      This module contains common methods which are shared between clusterless patching of
#      dom0 and cell
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    antamil     01/31/25 - Enh 37300427 -Creation: Enable clusterless cell patching
#                           using management host

import copy
import os, sys
import traceback
import json
import datetime
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler import InfraPatchManager
from exabox.infrapatching.utils.constants import *
from exabox.infrapatching.core.infrapatcherror import *
from exabox.infrapatching.utils.utility import MANAGEMENT_HOST_LAUNCH_NODE_PATCH_BASE, mRegisterInfraPatchingHandlers, PATCH_BASE, mFormatOut, mReadPatcherInfo, mGetFirstDirInZip,\
  mReadCallback, mErrorCallback, mGetInfraPatchingHandler, flocked, mChangeOwnerofDir
from exabox.ovm.clumisc import ebCluSshSetup, ebCluPreChecks
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure
from exabox.utils.common import version_compare
from exabox.infrapatching.handlers.loghandler import LogHandler
sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))


class ClusterlessPatchHelper(LogHandler):
    def __init__(self, aHandler=None):
        self.__handler = aHandler

    def mGetHandler(self):
        return self.__handler

    def mSetLaunchNodeAsPatchBase(self, aLaunchNodeCandidates, aLocalPatchZipFile,
                                  aPatchZipName, aPatchZipSizeMb,
                                  aRemotePatchBase, aRemotePatchZipFile,
                                  aRemotePatchmgr, aRemoteNecessarySpaceMb, aPatchBaseDir,
                                  aSuccessMsg="", aMoreFilesToCopy=None):
        """
        Makes sure the patchmgr is installed alog with any other files for
        its correct use. Generic method to install patchmgr on a given node to
        patch cells/ibswitches, dom0s or domus
        """

        # Update db status
        self.mGetHandler().mUpdatePatchStatus(True, STEP_SELECT_LAUNCH_NODE)

        # Exadata patch cleanup is skipped if launch node is localhost or mgmt host
        if self.mGetHandler().mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForClusterless'):
            self.mPatchLogInfo("Skipping cleanup of exadata patches on launch node")
        else:
            # Cleanup old patches before validating for space requirements
            # and copying patches.
            try:
                self.mGetHandler().mCleanupExadataPatches(aLaunchNodeCandidates)
            except Exception as e:
                self.mPatchLogWarn(
                    f'Exadata patches not cleaned properly on launch nodes {str(aLaunchNodeCandidates)}. Message: {str(e)}')
                self.mPatchLogTrace(traceback.format_exc())

        # If there are directories in the remote patch base that do not
        # contain the patchmgr file, the remote patch base dir must be removed.
        self.mGetHandler().mVerifyAndCleanupMissingPatchmgrRemotePatchBase(aRemotePatchBase, aLaunchNodeCandidates)
        self.mPatchLogInfo(f"aLocalPatchZipFile {aLocalPatchZipFile}")
        self.mPatchLogInfo(f"aPatchZipName {aPatchZipName}")
        self.mPatchLogInfo(f"aRemotePatchBase {aRemotePatchBase}")

        _local_patch_path = os.path.dirname(aLocalPatchZipFile)
        _ret, _errmsg = self.mValidateImageCheckSumWithRetry(aPatchZipName, _local_patch_path, aRemotePatchBase,
                                                             aLaunchNodeCandidates, aRemoteNecessarySpaceMb)
        if _ret != PATCH_SUCCESS_EXIT_CODE:
            raise Exception(_errmsg)

        if aMoreFilesToCopy:
            for _file, _copy_to in aMoreFilesToCopy:
                _file_name = _file.split("/")[-1]
                _local_patch_path = os.path.dirname(_file)
                _ret, _errmsg = self.mValidateImageCheckSumWithRetry(_file_name, _local_patch_path, _copy_to,
                                                                     aLaunchNodeCandidates, aRemoteNecessarySpaceMb)
                if _ret != PATCH_SUCCESS_EXIT_CODE:
                    raise Exception(_errmsg)

        for _launch_node in aLaunchNodeCandidates:

            # TODO: fix all the disconnect calls. Can maybe connect/disconnect
            # during each cmd? whats the best way?
            _node = exaBoxNode(get_gcontext())
            self.mGetHandler().mSetConnectionUser(_node)
            _node.mConnect(aHost=_launch_node)
            _node.mExecuteCmd(f"ls -l {aRemotePatchmgr}")
            _exit_code = _node.mGetCmdExitStatus()

            # make sure we can get the patch to the directory that came out of unziping the patch
            if int(_exit_code) != 0:
                if _node.mIsConnected():
                    _node.mDisconnect()
                _suggestion_msg = f"Expected patchmgr script {_launch_node}:{aRemotePatchmgr} but it was not found.Patch zip structure may have changed"
                _ret = PATCHMGR_SCRIPT_MISSING_ON_LAUNCH_NODE
                self.mGetHandler().mAddError(_ret, _suggestion_msg)
                # TODO give it another shot on a different  dom0 (continue), or just error out (return None)
                continue

            self.mPatchLogInfo(
                f"Selecting {str(_launch_node)} as a patch base for {aSuccessMsg}. patchmgr is at {aRemotePatchmgr}")
            if _node.mIsConnected():
                _node.mDisconnect()
            return _launch_node
        else:
            self.mPatchLogError(f"None of {str(aLaunchNodeCandidates)} were eligible bases for the patch manager")
            return None

    def mCopyDbserverPatchFile(self, _remote_node, _local_patch_file, _remote_patch_file, _node):
        _tmp_local_patch_file = _local_patch_file
        _local_patch_file = f'{_local_patch_file}_{self.mGetHandler().mGetMasterReqId()}'
        self.mGetHandler().mGetCluControl().mExecuteCmd(f'cp {_tmp_local_patch_file} {_local_patch_file}')
        _node.mSetUser('opc')
        _node.mConnect(aHost=_remote_node)
        _node.mCopyFile(_local_patch_file, _remote_patch_file)
        self.mGetHandler().mPatchLogInfo(f"Deleting {_local_patch_file}")
        self.mGetHandler().mGetCluControl().mExecuteCmd(f'rm -f {_local_patch_file}')

    def mValidateImageCheckSumWithRetry(self, aPatchFile, aPatchRepo, aRemotePatchBase, aNodeList,
                                        aRemoteNecessarySpaceMb):
        """
         This method calls mValidateImageCheckSum with 2 retries
         if there is any issue in any iteration
         Return:-
          PATCH_SUCCESS_EXIT_CODE                 --> if checksum evaluation and files copy are successful.
          Non PATCH_SUCCESS_EXIT_CODE error codes --> If there any failures
        """
        _rc = PATCH_SUCCESS_EXIT_CODE
        _errmsg = ""
        _max_retries = self.mGetHandler().mGetMaxRetriesForValidateImageChecksum()
        _retries = 0
        while _retries < _max_retries:
            try:
                _rc, _errmsg = self.mValidateImageCheckSum(aPatchFile, aPatchRepo, aRemotePatchBase, aNodeList,
                                                           aRemoteNecessarySpaceMb)
                if _rc == PATCH_SUCCESS_EXIT_CODE:
                    break
                else:
                    self.mPatchLogWarn(
                        f"Retry ({(_retries + 1):d}/{_max_retries:d}) to copy {aPatchFile} file due to error {str(_errmsg)}.")
            except Exception as e:
                _rc = PATCH_COPY_AND_IMAGE_CHECKSUM_VALIDATION_EXCEPTION
                _errmsg = e
                self.mPatchLogError(
                    f'Exception encountered while retrying ({(_retries + 1):d}/{_max_retries:d}) to copy {aPatchFile} file to the destination node. Error : {str(_errmsg)}')
                self.mPatchLogTrace(traceback.format_exc())

            _retries += 1
        else:
            self.mPatchLogError(
                f'Max {_max_retries:d} retries reached. File {aPatchFile} copying still failed and the error details are {str(_errmsg)}.')
        return _rc, _errmsg

    def mValidateImageCheckSum(self, aPatchFile, aPatchRepo, aRemotePatchBase, aNodeList, aRemoteNecessarySpaceMb):
        """
         This method checks for existence of patch file on remote node and if the
         file is available, it validates the checksum of the file with the local
         file's checksum and if there is any mismatch then remote file get replaced
         with the local file.

         Return:-
          PATCH_SUCCESS_EXIT_CODE                 --> if checksum evaluation and files copy are successful.
          Non PATCH_SUCCESS_EXIT_CODE error codes --> If there any failures
        """

        self.mPatchLogInfo(f"aPatchRepo {aPatchRepo}")
        self.mPatchLogInfo(f"aRemotePatchBase {aRemotePatchBase}")
        self.mPatchLogInfo(f"aPatchFile {aPatchFile}")
        # Validate ssh connectivity between Exacloud/CPS nodes to launch nodes
        # to ensure passwdless ssh connectivity exists.
        self.mPatchLogInfo(
            "Passwdless ssh connectivity is validated between Exacloud/CPS nodes to target launch nodes.")
        if self.mGetHandler().mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForClusterless'):
            self.mGetHandler().mGetCluPatchCheck().mVerifyExacloudExadataHostSshConnectivity(aNodeList, aSshUser='opc')
        else:
            self.mGetHandler().mGetCluPatchCheck().mVerifyExacloudExadataHostSshConnectivity(aNodeList)

        def _mValidateRemotePatchFileChecksum(_remote_node):
            '''
             Common method to perform remote patch file checksum
            '''
            _ret = False
            _remote_patch_file_checksum = None
            _cmd = (f"{_checksum_cmd} {_remote_patch_file} | {_awk_cmd}")
            _ls_cmd = f'ls _checksum_cmd'
            if _remote_node.mExecuteCmd(_ls_cmd) == 0:
                _cmd = (f"{_checksum_cmd_in_usr_bin} {_remote_patch_file} | {_awk_cmd}")
            _in, _out, _err = _remote_node.mExecuteCmd(_cmd)
            if _out:
                for _output in _out.readlines():
                    _remote_patch_file_checksum = _output.strip()

            self.mPatchLogInfo(f"Local Patch file : {_local_patch_file}  checksum : {_local_patch_file_checksum}")
            self.mPatchLogInfo(f"Remote Patch file : {_remote_patch_file}  checksum : {_remote_patch_file_checksum}")
            if _remote_patch_file_checksum and _local_patch_file_checksum == _remote_patch_file_checksum:
                _ret = True
            return _ret

        def _mCopyFile(aStatus):
            '''
             Common method to perform mCopyFile based on the conditions
             in _mExecute_FileCopy method.
            '''
            _node = exaBoxNode(get_gcontext())
            try:

                # Incase of EXACS single VM patching copying dbserver patch file mechanism is different
                # This is required for handling multiple patching session on the same launch node

                if self.mGetHandler().mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForClusterless'):
                    self.mCopyDbserverPatchFile(_remote_node, _local_patch_file, _remote_patch_file, _node)
                else:
                    _node.mConnect(aHost=_remote_node)
                    if (os.path.exists(_local_patch_file)):
                        _node.mCopyFile(_local_patch_file, _remote_patch_file)
                self.mPatchLogInfo(
                    f'Patch file : {_remote_patch_file} copied to node : {_remote_node}. Re-validating copied patch file checksum before extracting...')
                _checksum_status = _mValidateRemotePatchFileChecksum(_node)
                if not _checksum_status:
                    _node.mExecuteCmdLog(f"ls -l {_remote_patch_file}")
                    _patch_copy_end_time = datetime.datetime.now()
                    self.mGetHandler().mGetPatchRunningTime(_task_type, _patch_copy_start_time, _patch_copy_end_time)
                    _suggestion_msg = f"Patch file : {_remote_patch_file} corrupted on node : {_remote_node} as checksum of patch files different. Skipping patch file extraction on this node!"
                    _ret = PATCH_COPY_ERROR
                    self.mGetHandler().mAddError(_ret, _suggestion_msg)
                    aStatus.append(
                        {'node': _remote_node, 'status': 'failed', 'errorcode': _ret, 'errormessage': _suggestion_msg})
                else:
                    self.mPatchLogInfo(
                        f'Patch file: {_remote_patch_file} correctly copied to node: {_remote_node}. Proceeding with patch file extraction...')
                    _i, _o, _e = _node.mExecuteCmd(_patch_unzip_cmd)
                    _exit_code = _node.mGetCmdExitStatus()
                    if int(_exit_code) != 0:
                        _node.mExecuteCmdLog(f"ls -l {_remote_patch_file}")
                        _patch_copy_end_time = datetime.datetime.now()
                        self.mGetHandler().mGetPatchRunningTime(_task_type, _patch_copy_start_time, _patch_copy_end_time)
                        _suggestion_msg = f"Error while unziping the patch : {_remote_patch_file} on {str(_remote_node)}, skipping this Node. Error : {_e}"
                        _ret = PATCH_UNZIP_ERROR
                        self.mGetHandler().mAddError(_ret, _suggestion_msg)
                        aStatus.append({'node': _remote_node, 'status': 'failed', 'errorcode': _ret,
                                        'errormessage': _suggestion_msg})
                    else:
                        #
                        # When management host is used as launch node, the permission
                        # on dbserver patch dir should be 775
                        #
                        if self.mGetHandler().mGetInfrapatchExecutionValidator().mCheckCondition(
                                'mIsManagementHostLaunchNodeForClusterless'):
                            _first_patchdir = mGetFirstDirInZip(_local_patch_file)
                            if _first_patchdir:
                                _remote_dbserver_patchdir = _first_patchdir.split("/")[-1]
                                _node.mExecuteCmdLog(
                                    f"/usr/bin/chmod 775 {aRemotePatchBase}/{_remote_dbserver_patchdir}")
                        self.mPatchLogInfo(
                            f'*** Patch file : {_local_patch_file} >>>> {_remote_patch_file} transferred to Node : {_remote_node}')
            except Exception as e:
                if _node.mIsConnected():
                    _suggestion_msg = f"Copy operation failed with errors on Node : {_remote_node} Error : {str(e)}."
                    _ret = PATCH_COPY_ERROR
                else:  # mConnect() failed
                    _suggestion_msg = f"Connect to Node : {_remote_node} failed with {str(e)}"
                    _ret = PATCHING_CONNECT_FAILED
                self.mGetHandler().mAddError(_ret, _suggestion_msg)
                aStatus.append(
                    {'node': _remote_node, 'status': 'failed', 'errorcode': _ret, 'errormessage': _suggestion_msg})
                self.mPatchLogTrace(traceback.format_exc())

            finally:
                if _node.mIsConnected():
                    _node.mDisconnect()

            # End of _mCopyFile sub function.

        def _mExecute_FileCopy(_remote_node, aStatus):
            '''
             Sub function to copy patches parallely
             to multiple target nodes.
            '''

            _node = exaBoxNode(get_gcontext())
            self.mGetHandler().mSetConnectionUser(_node)

            try:
                _node.mConnect(aHost=_remote_node)

                # Create Patch and Images directory if missing.
                _exec_code = f"mkdir -p {aRemotePatchBase}"

                _node.mExecuteCmdLog(_exec_code)

                # Calculating the free disk space on remote node.
                _patch_base_df_cmd = (f"df -mP {aRemotePatchBase} | tail -n1 | awk '{{print $(NF - 2); }}'")
                _exec_code = f"ExecuteCmd {_patch_base_df_cmd}"

                #
                # When management host is used as launch node, the permission
                # on aRemotePatchBase should be 775
                #
                if self.mGetHandler().mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForClusterless'):
                    _node.mExecuteCmdLog(f"/usr/bin/chmod 775 {aRemotePatchBase}")
                    if  self.mGetHandler().mGetCurrentTargetType() in [ PATCH_CELL]:
                        _node.mExecuteCmdLog(f"/usr/bin/chmod 775 {self.mGetHandler()._cells_switches_remote_base}")
                    if  self.mGetHandler().mGetCurrentTargetType() in [ PATCH_DOM0]:
                        _node.mExecuteCmdLog(f"/usr/bin/chmod 775 {self.mGetHandler().mGetDom0PatchBase()}")

                _i, _o, _e = _node.mExecuteCmd(_patch_base_df_cmd)
                _patch_base_space_available = int(mFormatOut(_o))

                # If the space to copy patch is not available on the target node
                # this node will be skipped.

                self.mPatchLogInfo(f"Clusterless aRemoteNecessarySpaceMb {aRemoteNecessarySpaceMb}")
                self.mPatchLogInfo(f"Clusterless _patch_base_space_available {_patch_base_space_available}")
                if _patch_base_space_available < (aRemoteNecessarySpaceMb * 3):
                    if _node.mIsConnected():
                        _node.mDisconnect()
                    _suggestion_msg = f"{_remote_node} does not have enough space in {aRemotePatchBase} to be used as the patching base. Needed {((aRemoteNecessarySpaceMb * 3) / 1024):.2f} GB({(aRemoteNecessarySpaceMb * 3):.2f} MB), got {(_patch_base_space_available / 1024):.2f} GB({(_patch_base_space_available):.2f} MB)."
                    _ret = INSUFFICIENT_SPACE_ON_PATCH_BASE
                    self.mGetHandler().mAddError(_ret, _suggestion_msg)
                    aStatus.append(
                        {'node': _remote_node, 'status': 'failed', 'errorcode': _ret, 'errormessage': _suggestion_msg})
                else:
                    self.mPatchLogInfo(
                        f"Sufficient space available to stage patches on Node : {_remote_node}, Location : {aRemotePatchBase}, Required : {(aRemoteNecessarySpaceMb / 1024):.2f} GB({(aRemoteNecessarySpaceMb):.2f} MB), Available Space : {(_patch_base_space_available / 1024):.2f} GB({(_patch_base_space_available):.2f} MB)")

                    if not _node.mFileExists(_remote_patch_file):
                        '''
                         Patch file not yet staged. Go ahead and copy 
                        '''
                        self.mPatchLogInfo(
                            f'*** Patch file : {aPatchFile} missing on node : {_remote_node} . Copying in progress...')
                        if _node.mIsConnected():
                            _node.mDisconnect()
                        _mCopyFile(aStatus)

                    else:
                        '''
                         Patch file already present. 
                         Get the remote file checksum and compare with local file checksum.
                         On checksum mismatch, copy local file to remote node.
                        '''
                        _checksum_status = _mValidateRemotePatchFileChecksum(_node)
                        if not _checksum_status:
                            self.mPatchLogInfo(
                                f'*** Deleting remote patch file : {_remote_patch_file} on node : {_remote_node} as checksum of patch files different.')
                            _node.mExecuteCmdLog(f"rm -f {_remote_patch_file}")
                            self.mPatchLogInfo(
                                f'*** Copying patch file : {aPatchFile}  to node : {_remote_node} in progress...')
                            if _node.mIsConnected():
                                _node.mDisconnect()
                            _mCopyFile(aStatus)
                        else:
                            self.mPatchLogInfo(
                                f"Patch file : {_remote_patch_file} already staged on node : {_remote_node} and matches with source file checksum.")

            except ValueError as e:
                _suggestion_msg = f"Could not parse {aRemotePatchBase} for free space on {str(_remote_node)}. Expected a number, got {str(e)}. Trying a different node"
                _ret = PATCH_COPY_ERROR
                aStatus.append(
                    {'node': _remote_node, 'status': 'failed', 'errorcode': _ret, 'errormessage': _suggestion_msg})
                if _node.mIsConnected():
                    _node.mDisconnect()

            except Exception as e:
                if _node.mIsConnected():
                    # disambiguate dir creation or df execution
                    _suggestion_msg = f"Prior to copy, {_exec_code} execution on Node : {str(_remote_node)} failed with {str(e)}"
                    _ret = PATCH_COPY_ERROR
                    _node.mDisconnect()
                else:  # mConnect() failed
                    _suggestion_msg = f"Connect to Node : {_remote_node} failed with {str(e)}"
                    _ret = PATCHING_CONNECT_FAILED
                self.mGetHandler().mAddError(_ret, _suggestion_msg)
                aStatus.append(
                    {'node': _remote_node, 'status': 'failed', 'errorcode': _ret, 'errormessage': _suggestion_msg})
                self.mPatchLogTrace(traceback.format_exc())

        # End of _mExecute_FileCopy sub function.

        _patch_copy_start_time = datetime.datetime.now()
        _ret = PATCH_SUCCESS_EXIT_CODE
        
        self.mPatchLogInfo(f"aPatchRepo {aPatchRepo}")
        self.mPatchLogInfo(f"aRemotePatchBase {aRemotePatchBase}")
        self.mPatchLogInfo(f"aPatchFile {aPatchFile}")
        _local_patch_file = os.path.join(aPatchRepo, aPatchFile)
        _remote_patch_file = os.path.join(aRemotePatchBase, aPatchFile)
        _task_type = "Patch_copy"

        # If patch file does not exist at source, Patch copy exits with error.
        self.mPatchLogInfo(f"*** Generating checksum for the patch file : {_local_patch_file} ***")

        _checksum_cmd = '/bin/sha256sum'
        _checksum_cmd_in_usr_bin = '/usr/bin/sha256sum'
        _awk_cmd = "/bin/awk '{print $1}'"

        _local_patch_file_checksum = None
        _cmd = f'{_checksum_cmd} {_local_patch_file}'
        if os.path.isfile(_checksum_cmd) is False:
            _cmd = f'{_checksum_cmd_in_usr_bin} {_local_patch_file}'
        _in, _out, _err = self.mGetHandler().mGetCluControl().mExecuteCmd(_cmd)
        if _out:
            _in, _out, _err = self.mGetHandler().mGetCluControl().mExecuteCmd(_awk_cmd, aStdIn=_out)
            if _out:
                for _output in _out.readlines():
                    _local_patch_file_checksum = _output.strip()

        if _local_patch_file_checksum is None:
            _suggestion_msg = f"Local Patch file : {_local_patch_file} not found, unable to transfer file. Aborting."
            _ret = PATCH_COPY_ERROR
            self.mGetHandler().mAddError(_ret, _suggestion_msg)
            return _ret

        _cmd = f"/bin/du -sh {_local_patch_file} "
        _in, _out, _err = self.mGetHandler().mGetCluControl().mExecuteCmd(_cmd)

        _cmd_size = "/bin/awk '{print $1}'"
        _in, _out, _err = self.mGetHandler().mGetCluControl().mExecuteCmd(_cmd_size, aStdIn=_out)
        _file_size = ""
        for _output in _out.readlines():
            _file_size = _output.strip()

        # Patch unzip command is prepared based on patch file extension.
        if _remote_patch_file.endswith('.zip'):
            _patch_unzip_cmd = f"unzip -d {aRemotePatchBase} -o {_remote_patch_file}"

        """
         Parallelize execution on all target nodes. In case
         of Dom0/DomU patching, patches are copied to multiple
         nodes. In case of Cell and IBSwitches patching, patches
         are copied to one launch node. For more details regarding
         parallel file copy, please refer mParallelFileLoad and
         mCheckSystemImage methods in clucontrol file.
        """
        _plist = ProcessManager()
        _rc_status = _plist.mGetManager().list()

        for _remote_node in aNodeList:
            if _remote_node not in self.mGetHandler().mGetCluControl().mGetHostList():
                # Only in clusterless CELL, the launch node will not be part of HostList
                self.mGetHandler().mGetCluControl().mAppendToHostList(_remote_node)
                self.mGetHandler().mGetCluControl().mHandlerImportKeys()
            _p = ProcessStructure(_mExecute_FileCopy, [_remote_node, _rc_status], _remote_node)

            '''
             Timeout parameter configurable in Infrapatching.conf
             Currently it is set to 30 minutes
            '''
            _p.mSetMaxExecutionTime(self.mGetHandler().mGetValidateChecksumExecutionTimeoutInSeconds())

            '''
             BUG 32888598 - Increase timeout from 5 seconds to 15 seconds.

             In case of EXACC environments, delay in command response are
             observed in a few use cases and as a results, patch commands
             fail. Increasing the below timeout parameter avoids patch
             commands from failing and wait for the command to respond.
            '''
            _p.mSetJoinTimeout(PARALLEL_OPERATION_TIMEOUT_IN_SECONDS)
            _p.mSetLogTimeoutFx(self.mPatchLogWarn)
            _plist.mStartAppend(_p)

        _plist.mJoinProcess()

        if _plist.mGetStatus() == "killed":
            _suggestion_msg = f'Timeout while copying patches to launch nodes : {str(aNodeList)}.'
            self.mGetHandler().mAddError(PATCH_COPY_ERROR, _suggestion_msg)
            raise Exception(_suggestion_msg)

        # validate the return codes
        for _rc_details in _rc_status:
            if _rc_details['status'] == "failed":
                _err_msg = f"Patch copy method encountered error. {_rc_details['errormessage']}"
                self.mPatchLogError(_err_msg)
                return _rc_details['errorcode'], _err_msg
        return PATCH_SUCCESS_EXIT_CODE, None


    def mGetPatchMgrOutFiles(self, aDom0, aRemotePath, aCode=''):
        """
        Copies patchmgr.stdout/stderr/trc/log to /log
        """

        patchmgr_files = [PATCH_STDOUT, PATCH_STDERR,
                          PATCH_TRC, PATCH_LOG]
        if aCode != '':
            for i, patchmgr_file in enumerate(patchmgr_files):
                patchmgr_files[i] = patchmgr_file + '.' + aCode

        _context = get_gcontext()
        _oeda_path_logs = os.path.join(_context.mGetOEDAPath(), "log")

        if self.mGetHandler().mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForClusterless'):
            mChangeOwnerofDir(aDom0, aRemotePath, 'opc', 'opc')

        _node = exaBoxNode(_context)
        self.mGetHandler().mSetConnectionUser(_node)
        _node.mConnect(aHost=aDom0)

        for patchmgr_file in patchmgr_files:
            try:
                _cmd = f"ls {os.path.join(aRemotePath, patchmgr_file)}"
                _node.mExecuteCmd(_cmd)
                if _node.mGetCmdExitStatus() == 0:
                    self.mGetHandler().mSetListOfLogsCopiedToExacloudHost(os.path.join(aRemotePath, patchmgr_file))
                    _node.mCopy2Local(os.path.join(aRemotePath, patchmgr_file),
                                      os.path.join(self.mGetHandler().mGetLogPath(), patchmgr_file + '.' + \
                                                   self.mGetHandler().mGetCurrentTargetType()))
                    # symlinks used for chainsaw2/lumberjack
                    #  ln -s <file> <symlink>
                    # example:
                    #   ln -s /opt/oci/exacc/exacloud/oeda/requests/f829406a-15cb-11ec-8770-0010e0efc742/log/patchmgr_logs/patchmgr.stderr.cell
                    #         /opt/oci/exacc/exacloud/oeda/log/1ef39fbd-9be8-450c-8512-1e633cdf89b5_patchmgr.stderr.cell
                    #
                    _in, _out, _err = self.mGetHandler().mGetCluControl().mExecuteCmd(
                        f"ln -s {os.path.join(self.mGetHandler().mGetLogPath(), patchmgr_file + '.' + self.mGetHandler().mGetCurrentTargetType())} {os.path.join(_oeda_path_logs, self.mGetHandler().mGetMasterReqId() + '_' + patchmgr_file + '.' + self.mGetHandler().mGetCurrentTargetType())}")
                else:
                    self.mPatchLogWarn(
                        f'{os.path.join(aRemotePath, patchmgr_file)} not found on the launch node : {aDom0}')
            except Exception as e:
                self.mPatchLogWarn(
                    f'Error while copying {patchmgr_file}: {str(e)} from node - {aDom0} , location - {aRemotePath} to exacloud location - {self.mGetHandler().mGetLogPath()}')
                self.mPatchLogTrace(traceback.format_exc())
        if _node.mIsConnected():
            _node.mDisconnect()


