#
# dom0handlerclusterless.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates. 
#
#    NAME
#      dom0handlerclusterless.py - Clusterless Dom0 Patching Functionality
#
#    DESCRIPTION
#      Provide basic/core dom0 clusterless patching API (prereq, patch,
#      rollback_prereq, and rollback) for managing the Exadata patching in
#      the cluster implementation.
#
#      This handler extends the dom0handler class and it overrides the methods
#      which are required for clusterless patching of cell. Taskhandler will create
#      an object of this class for clusterless patching of cell
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    antamil     07/29/25 - Bug 38221892 Cleanup known_host file at the end of patch
#    antamil     01/31/25 - Enh 37300427 -Creation: Enable clusterless dom0 patching
#                           using management host


import datetime
import os, sys
import time
import json
import traceback
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler import InfraPatchManager
from exabox.infrapatching.utils.utility import mGetFirstDirInZip, PATCH_BASE, mRegisterInfraPatchingHandlers, flocked, \
    mGetLaunchNodeConfig
from exabox.infrapatching.core.clupatchmetadata import mWritePatchInitialStatesToLaunchNodes, \
    mUpdateAllPatchStatesForNode, mGetPatchStatesForNode, mGetLaunchNodeForTargetType, mUpdatePatchMetadata, \
    mUpdateMetadataLaunchNode
from exabox.infrapatching.utils.constants import *
from exabox.infrapatching.core.infrapatcherror import *
from exabox.exakms.ExaKmsEndpoint import ExaKmsEndpoint
from exabox.infrapatching.helpers.crshelper import CrsHelper
from exabox.infrapatching.helpers.clusterlesshelper import ClusterlessPatchHelper
from exabox.infrapatching.handlers.targetHandler.dom0handler import Dom0Handler
from exabox.ovm.clumisc import ebCluSshSetup
#from exabox.ovm.userutils import ebUserUtils
sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))




class Dom0HandlerClusterless(Dom0Handler):

    def __init__(self, *initial_data, **kwargs):

        super(Dom0HandlerClusterless, self).__init__(*initial_data, **kwargs)
        mRegisterInfraPatchingHandlers(INFRA_PATCHING_HANDLERS, [PATCH_DOM0], self)
        self.__dom0_local_patch_zip = self.mGetDom0DomUPatchZipFile()[0]
        self.__dom0_local_patch_zip2 = self.mGetDom0DomUPatchZipFile()[1]
        self.mPatchLogInfo("Dom0HandlerClusterless")
        _launch_node_type=self.mGetLaunchNodeType()
        if _launch_node_type == None:
            _launch_node_type=LAUNCHNODE_TYPE_COMPUTE
        self.__dom0_patch_base_dir = mGetLaunchNodeConfig(_launch_node_type, 'patch_base') 
        self.__dom0_patch_zip_name = None
        self.__dom0_patch_zip2_name = None
        self.__dom0_patch_base = None
        self.__dom0_patch_zip = None
        self.__dom0_patch_base_after_unzip = None
        self.__dom0_patchmgr = None
        self.__dom0_patch_zip_size_mb = None
        self.__dom0_patch_zip2_size_mb = None
        self.__dom0_patch_necessary_space_mb = None
        self.__dom0_to_patch_dom0s = None
        self.__dom0_patchmgr_input_file = None
        self.__dom0s_to_patch = []
        self.__crs_helper = None
        self.__clusterless_helper = None
        self.__ssh_env_setup = None
        self.mPrintEnvRelatedDebugStatements()

    def mGetDom0PatchBaseDir(self):
        return self.__dom0_patch_base_dir

    def mGetDom0LocalPatchZip(self):
        return self.__dom0_local_patch_zip

    def mGetDom0LocalPatchZip2(self):
        return self.__dom0_local_patch_zip2

    def mGetDom0PatchZipName(self):
        return self.__dom0_patch_zip_name

    def mGetDom0PatchZip2Name(self):
        return self.__dom0_patch_zip2_name

    def mGetDom0PatchBase(self):
        return self.__dom0_patch_base

    def mGetDom0PatchZip(self):
        return self.__dom0_patch_zip

    def mGetDom0PatchBaseAfterUnzip(self):
        return self.__dom0_patch_base_after_unzip

    def mGetDom0PatchMgr(self):
        return self.__dom0_patchmgr
    def mGetDom0PatchZipSizeMB(self):
        return self.__dom0_patch_zip_size_mb

    def mGetDom0PatchZip2SizeMB(self):
        return self.__dom0_patch_zip2_size_mb

    def mGetDom0PatchNecessarySpaceMB(self):
        return self.__dom0_patch_necessary_space_mb

    def mGetDom0ToPatchDom0(self):
        return self.__dom0_to_patch_dom0s

    def mGetDom0PatchMgrInputFile(self):
        return self.__dom0_patchmgr_input_file

    def mGetDom0sToPatch(self):
        return self.__dom0s_to_patch

    def mGetCRSHelper(self):
        return self.__crs_helper

    def mGetClusterlessHelper(self):
        return self.__clusterless_helper

    def mGetSSHEnvSetUp(self):
        return self.__ssh_env_setup


    def mSetEnvironment(self):

        # self.__dom0_patch_zip2_name: is of the format shown below
        # domains/exacloud/PatchPayloads/19.3.6.0.0.200317/Dom0YumRepository/exadata_ol7_19.3.6.0.0.200317_Linux-x86-64.zip,
        # domains/exacloud/PatchPayloads/19.3.6.0.0.200317/Dom0YumRepository/exadata_ovs_19.3.6.0.0.200317_Linux-x86-64.zip
        # if _target in [PATCH_ALL, PATCH_DOM0] and self.__dom0_local_patch_zip and self.__dom0_local_patch_zip2:
        if self.__dom0_local_patch_zip and self.__dom0_local_patch_zip2:
            # Select the appropriate zip file based on KVM (e.g exadata_ol7_19.3.6.0.0.200317_Linux-x86-64.zip ) or  OVM (e.g exadata_ovs_19.3.6.0.0.200317_Linux-x86-64.zip)
            dom0zip2File = self.__dom0_local_patch_zip2
            if dom0zip2File.find(',') > -1:
                patchFiles = dom0zip2File.strip().split(',')
                for _file in (patchFiles):
                    if self.mIsKvmEnv() and (any(substring in _file for substring in KVM_FILE_IDENTIFIER_LIST)):
                        self.mPatchLogInfo(f"Dom0Repository KVM file is {_file} ")
                        self.__dom0_local_patch_zip2 = _file
                        break
                    elif not self.mIsKvmEnv() and (
                            (any(substring in _file for substring in KVM_FILE_IDENTIFIER_LIST)) == False):
                        self.mPatchLogInfo(f"Dom0Repository NON KVM file is {_file} ")
                        self.__dom0_local_patch_zip2 = _file
                        break

            # Set collect time stats flag
            self.mSetCollectTimeStatsFlag(self.mGetCollectTimeStatsParam(PATCH_DOM0))

            self.mPatchLogInfo(f"Dom0 local patch zip file name {self.__dom0_local_patch_zip}")
            self.mPatchLogInfo(f"Dom0 local patch zip-2 file name {self.__dom0_local_patch_zip2}")

            if not self.__dom0_local_patch_zip2:
                self.mPatchLogError("Dom0 Patch Zip file not found")
                raise Exception("Dom0 Patch Zip file not found")

            _no_action_taken = 0

            _ret = PATCH_SUCCESS_EXIT_CODE
            # Dom0 patching needs 2 zip files. first one has the patchmgr, second one is the actual patch
            self.__dom0_patch_zip_name = self.__dom0_local_patch_zip.split("/")[-1]
            self.__dom0_patch_zip2_name = self.__dom0_local_patch_zip2.split("/")[-1]
            # self.__dom0_patch_base = PATCH_BASE + self.__dom0_patch_zip_name + "_" + self.__dom0_patch_zip2_name + "/"
            self.__dom0_patch_base = self.__dom0_patch_base_dir + self.__dom0_patch_zip_name + "_" + self.__dom0_patch_zip2_name + "/"
            self.__dom0_patch_zip = self.__dom0_patch_base + self.__dom0_patch_zip_name
            self.__dom0_patch_base_after_unzip = (self.__dom0_patch_base +
                                                  mGetFirstDirInZip(self.__dom0_local_patch_zip))
            self.__dom0_patchmgr = self.__dom0_patch_base_after_unzip + "patchmgr"
            self.__dom0_patch_zip_size_mb = int(os.path.getsize(self.__dom0_local_patch_zip)) >> 20
            self.__dom0_patch_zip2_size_mb = int(os.path.getsize(self.__dom0_local_patch_zip2.strip())) >> 20
            self.__dom0_patch_necessary_space_mb = (
                    self.__dom0_patch_zip_size_mb + self.__dom0_patch_zip2_size_mb + int(
                self.mGetExadataPatchWorkingSpaceMB()))
            # Set current patch. Information necessary to update status in db
            self.mSetCurrentTargetType(PATCH_DOM0)
            self.__clusterless_helper  = ClusterlessPatchHelper(aHandler=self)

            _ret, _launchNodes = self.mSetLaunchNodeToPatchOtherDom0Nodes()
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                return _ret
            try:
                self.__dom0_to_patch_dom0s = _launchNodes[0]
                self.mSetDom0ToPatchInitialDom0(_launchNodes[1])
            except IndexError:
                pass

            self.mSetPatchmgrLogPathOnLaunchNode(
                self.__dom0_patch_base_after_unzip + "patchmgr_log_" + self.mGetMasterReqId())
            self.mPatchLogInfo(f"Patch manager Log Path on Launch Node is {self.mGetPatchmgrLogPathOnLaunchNode()}")

            # def mPatchDom0sOrDomus(self, aTargetType, aTaskType):
            # List of launch nodes to update patch state metadata
            _launch_nodes = []

            '''
            # Set target version based on the patch tar file version name.
            Quarterly:
                ./PatchPayloads/19.3.2.0.0.191119/Dom0YumRepository/exadata_ovs_19.3.2.0.0.191119_Linux-x86-64.zip
            Monthly:
                ./PatchPayloads/201015/ExaspliceRepository/exadata_exasplice_update_201015_Linux-x86-64.zip
            '''
            if "ExaspliceRepository" in self.mGetDom0LocalPatchZip2():
                self.mSetTargetVersion(self.mGetDom0LocalPatchZip2().split("/")[-1].split("_")[3])
            else:
                self.mSetTargetVersion(self.mGetDom0LocalPatchZip2().split("/")[-1].split("_")[2])

            # Add to executed targets
            self.mGetExecutedTargets().append(PATCH_DOM0)

            # Update status
            self.mUpdatePatchStatus(True, STEP_PREP_ENV)

            '''
             In this case, for _nodes_to_patch_except_initial All nodes from
             xml need to be considered as passwdless ssh is required to be setup 
             on all nodes and are used during ssh validation, patchmgr existence 
             check and for performing a few config changes during CNS monitor start.
            '''
            _nodes_to_patch_except_initial = list(
                set(self.mGetCustomizedDom0List()) - set([self.__dom0_to_patch_dom0s]))
            _initial_node_list = [self.__dom0_to_patch_dom0s]
            _initial_node = self.__dom0_to_patch_dom0s
            _next_node = self.mGetDom0ToPatchInitialDom0()
            _launch_nodes = [self.__dom0_to_patch_dom0s, _next_node]

            # These variables are defined , but files are created during operation only
            self.mSetPatchStatesBaseDir(os.path.join(self.__dom0_patch_base_after_unzip, "patch_states_data"))
            self.mSetMetadataJsonFile(os.path.join(self.mGetPatchStatesBaseDir(),
                                                   self.mGetMasterReqId() + "_patch_progress_report.json"))
            self.mPatchLogInfo(f"Patch metadata file = {self.mGetMetadataJsonFile()}")

            # Exacloud Plugin already initialized at this stage
            if self.mIsExacloudPluginEnabled():
                self.mGetPluginHandler().mSetPluginsLogPathOnLaunchNode(
                    self.__dom0_patch_base_after_unzip + "plugins_log_" + self.mGetMasterReqId())
                self.mPatchLogInfo("Exacloud Plugin Enabled to run")

            # In case of single launch node, _next_node will be None, because only one launch node
            # has been passed
            # set ssh keys from node patchers to the nodes they will be patching
            _ssh_env_setup = ebCluSshSetup(self.mGetCluControl())
            # Store these in memory for clearing after each operation

            _src_node_list = [_initial_node]
            _remote_node_list = [_nodes_to_patch_except_initial]
            if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForClusterless'):
                with open(LOCK_FILE_NAME, 'a') as file:
                    with flocked(file):
                        _ssh_env_setup.mConfigureSshForMgmtHost(_initial_node, _nodes_to_patch_except_initial,
                                                                EXAPATCHING_KEY_TAG,
                                                                self.mGetDom0PatchBaseDir())
                self.mGetCluPatchCheck().mVerifyPatchmgrSshConnectivityBetweenExadataHosts(
                    _nodes_to_patch_except_initial,
                    _initial_node,
                    aSshUser='opc')
                _sshEnvDict = {
                    "sshEnv": _ssh_env_setup,
                    "fromHost": _src_node_list,
                    "remoteHostLists": _remote_node_list}
                self.__ssh_env_setup = _sshEnvDict
            else:
                # Rotate SSH Keys
                _all_nodes = _initial_node_list + _nodes_to_patch_except_initial
                _exakmsEndpoint = ExaKmsEndpoint(None)
                for _node in _all_nodes:
                    if _node:
                        _exakmsEndpoint.mSingleRotateKey(_node)
                _ssh_env_setup.mSetSSHPasswordlessForClusterless(_initial_node, _nodes_to_patch_except_initial)

                # Remove Obsolete ssh keys emrtires from authorised_keys file
                self.mRemoveObsoleteSshKeysfromAuthKeysFile(_initial_node,
                                                            _nodes_to_patch_except_initial,
                                                            _ssh_env_setup)


                #
                # Configure ssh only if the second launch node is being selected or passed
                #
                if _next_node:
                    _ssh_env_setup.mSetSSHPasswordlessForClusterless(_next_node, _initial_node_list)
                    self.mRemoveObsoleteSshKeysfromAuthKeysFile(_next_node,
                                                                _initial_node_list,
                                                                _ssh_env_setup)
                    _src_node_list.append(_next_node)
                    _remote_node_list.append(_initial_node_list)


                _sshEnvDict = {
                    "sshEnv": _ssh_env_setup,
                    "fromHost": _src_node_list,
                    "remoteHostLists": _remote_node_list}
                self.__ssh_env_setup = _sshEnvDict

            # Fetch user specified exadata env type (like, ecs (is default), adw, atp, fa, higgs, etc).
            if self.mGetAdditionalOptions() and 'EnvType' in self.mGetAdditionalOptions()[0]:
                self.mSetExadataEnvType(self.mGetAdditionalOptions()[0]['EnvType'].lower())

        self.__crs_helper = CrsHelper(aHandler=self)
        self.mPatchLogInfo("Finished Setting up Environment for Dom0")
        return _ret

    def mSetLaunchNodeAsPatchBase(self,
                aLaunchNodeCandidates, aLocalPatchZipFile,
                aPatchZipName, aPatchZipSizeMb, aRemotePatchBase,
                aRemotePatchZipFile, aRemotePatchmgr, aRemoteNecessarySpaceMb,
                aPatchBaseDir, aSuccessMsg="", aMoreFilesToCopy=None):

        return self.mGetClusterlessHelper().mSetLaunchNodeAsPatchBase(
                                    aLaunchNodeCandidates, aLocalPatchZipFile, aPatchZipName,
                                    aPatchZipSizeMb, aRemotePatchBase, aRemotePatchZipFile,
                                    aRemotePatchmgr, aRemoteNecessarySpaceMb, aPatchBaseDir,
                                    aSuccessMsg, aMoreFilesToCopy)

    def mCleanSSHEnvSetUp(self, aSingleVmHandler=None):
        # _sshEnvDict = {
        #     "sshEnv": ebCluSshSetup(self.mGetCluControl()),
        #     "fromHost": ["a", "b"],
        #     "remoteHostLists": [["1", "2"], ["3", "4"]]
        # }
        """
        This method cleans up and refreshes the configurations based on the domU
        type, handling single-node or multi-node setups.
        """
        _sshEnvDict = self.mGetSSHEnvSetUp()
        if _sshEnvDict:
            _ssh_env = _sshEnvDict["sshEnv"]
            for _index in range(len(_sshEnvDict["fromHost"])):

                try:
                    # Add secsacan key
                    #ebUserUtils.mAddSecscanSshdSingle(self.mGetCluControl(),_sshEnvDict["fromHost"][_index])
                    if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForClusterless'):
                       _ssh_env.mCleanupSSHConfigForMgmtHost(_sshEnvDict["fromHost"][_index], _sshEnvDict["remoteHostLists"][_index])
                       self.mGetCluPatchCheck().mVerifyPatchmgrSshConnectivityBetweenExadataHosts(_sshEnvDict["remoteHostLists"][_index],
                                                                                       _sshEnvDict["fromHost"][_index],
                                                                                       aStage="PostPatch",
                                                                                       aSshUser='opc')
                       with open(LOCK_FILE_NAME, 'a') as file:
                           with flocked(file):
                                _ssh_env.mCleanupSSHConfigFileOnMgmtHost(_sshEnvDict["fromHost"][_index], _sshEnvDict["remoteHostLists"][_index])
                    else:
                        _ssh_env.mCleanSSHPasswordlessForClusterless(_sshEnvDict["fromHost"][_index],
                                                   _sshEnvDict["remoteHostLists"][_index])
                        _ssh_env.mRemoveFromKnownHosts(_sshEnvDict["fromHost"][_index], _sshEnvDict["remoteHostLists"][_index], False)
                        '''
                        Below checks are applicable to Dom0 and Domu targets
                        and are used for validating ssh connectivity post patching
                        activity is complete during the passwdless ssh cleanup stage.
                        '''
                        self.mPatchLogInfo(
                           f"Passwordless ssh validation performed between {str(_sshEnvDict['remoteHostLists'][_index])} and [{str(_sshEnvDict['fromHost'][_index])}]")
                        self.mGetCluPatchCheck().mVerifyPatchmgrSshConnectivityBetweenExadataHosts(_sshEnvDict["remoteHostLists"][_index], _sshEnvDict["fromHost"][_index], aStage="PostPatch")

                except Exception as e:

                    self.mPatchLogError(f"Error: [{e}] occurred during SSH environment cleanup, possibly with [{str(_sshEnvDict['fromHost'][_index])}] or {str(_sshEnvDict['remoteHostLists'][_index])}. Moving to the next node.")
                    self.mPatchLogTrace(traceback.format_exc())

    def mPreCheckFilesCleanup(self, aNode, aInputFile, aCnsString):
        '''
         Remove temporary patchmgr log files
        '''
        self.mPatchLogInfo("Remove temporary patchmgr log files")
        _node = exaBoxNode(get_gcontext())
        self.mSetConnectionUser(_node)
        _node.mConnect(aHost=aNode)
        _node.mExecuteCmd(f"ls {aInputFile}")
        if _node.mGetCmdExitStatus() == 0:
            _node.mExecuteCmdLog(f"rm -f {aInputFile}")
        _node.mExecuteCmd(f"ls {self.mGetPatchmgrLogPathOnLaunchNode()}")
        if _node.mGetCmdExitStatus() == 0:
            # Moving log_dir to log_dir_<launch_node>, before starting another one
            _node.mExecuteCmdLog(
                f"mv -f {self.mGetPatchmgrLogPathOnLaunchNode()} {self.mGetPatchmgrLogPathOnLaunchNode()}_{aNode.split('.')[0]}")

        if _node.mIsConnected():
            _node.mDisconnect()

        # Log location is updated in mUpdateNodePatcherLogDir for proper collection of final CNS notification
        self.mUpdateNodePatcherLogDir(aNode, aCnsString)

    def mGetPatchMgrOutFiles(self, aDom0, aRemotePath, aCode=''):
        return self.mGetClusterlessHelper().mGetPatchMgrOutFiles(aDom0, aRemotePath, aCode)

    def mGetPatchMgrDiagFiles(self, aDom0, aNodeType, aNodeList, aRemotePath):
        """
        Copies the last patchmgr_files found for various node types to /log.
        Presently handles the CELLs and DOMUs
        For CELLS, it copies the files from DOM0 to ExaCloud logs
        For DOMUs, along with the files from DOM0 where patchmrg ran it also
        gets the files from DOMUs.
        """
        _node = exaBoxNode(get_gcontext())
        self.mSetConnectionUser(_node)
        _node.mConnect(aHost=aDom0)
        aRemotePath = self.mGetPatchmgrLogPathOnLaunchNode()
        _patchmgr_diag_tar = aRemotePath.split('/')[-1] + ".tar"

        self.mPatchLogInfo(
            f"aRemotePath = {aRemotePath}\n_patchmgr_diag_tar = {_patchmgr_diag_tar}\n dirname = {os.path.dirname(aRemotePath)}\n basename = {os.path.basename(aRemotePath)}\n")

        # tar the diagnostic files
        tar_cmd = f"tar cvf {os.path.dirname(aRemotePath)}/{_patchmgr_diag_tar} {os.path.dirname(aRemotePath)}/{os.path.basename(aRemotePath)};"
        try:
            self.mPatchLogInfo(f"Taring patch manager diagnosis files from DOM0 {aDom0}\n cmd={tar_cmd}")

            _in, _out, _err = _node.mExecuteCmd(tar_cmd)
        except Exception as e:
            self.mPatchLogWarn(f"Error while taring the diagnosis files({tar_cmd}) from DOM0 {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())

        # copy the tar to local
        try:
            ls_cmd = f"ls {os.path.dirname(aRemotePath)}/{_patchmgr_diag_tar}"
            _in, _out, _err = _node.mExecuteCmd(ls_cmd)
            if _node.mGetCmdExitStatus() == 0:
                _node.mExecuteCmd(f"chown opc:opc {os.path.dirname(aRemotePath)}/{_patchmgr_diag_tar}")
                self.mSetListOfLogsCopiedToExacloudHost(os.path.join(aRemotePath, _patchmgr_diag_tar))
                self.mPatchLogInfo(f"Before copying...")
                _node.mCopy2Local(os.path.dirname(aRemotePath) + '/' + _patchmgr_diag_tar,
                                    os.path.join(self.mGetLogPath(), _patchmgr_diag_tar))
                self.mPatchLogInfo(f"Before copying...")
            else:
                self.mPatchLogWarn(
                    f'{os.path.dirname(aRemotePath) + "/" + _patchmgr_diag_tar} not found on the launch node : {aDom0}')
        except Exception as e:
            self.mPatchLogWarn(
                f"Error while copying the diagnosis files from DOM0 error={str(e)}\n rfile={os.path.dirname(aRemotePath) + '/' + _patchmgr_diag_tar}\n lfile={os.path.join(self.mGetLogPath(), _patchmgr_diag_tar)} to exacloud location - {self.mGetLogPath()}")
            self.mPatchLogTrace(traceback.format_exc())
            ls_cmd = f"ls {os.path.dirname(aRemotePath)}"
            _in, _out, _err = _node.mExecuteCmd(ls_cmd)
            self.mPatchLogInfo(
                f"We have following files in dir ({_out.readlines()}) in node ({aDom0}) that dont have the execpected {_patchmgr_diag_tar} ")

        # remove the tar file
        try:
            _in, _out, _err = _node.mExecuteCmd(f"rm {os.path.dirname(aRemotePath)}/{_patchmgr_diag_tar};")
        except Exception as e:
            self.mPatchLogWarn(f"Error while removing the diagnosis files from DOM0 {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
        return


    def mCheckIdemPotency(self, aDiscarded):

        _ret = PATCH_SUCCESS_EXIT_CODE
        _no_action_taken = 0
        _launch_nodes = [self.mGetDom0ToPatchDom0()]
        _patchMgrObj = None
        _launch_node_user = 'root'
        if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForClusterless'):
            _launch_node_user = 'opc'    
        
        if self.mGetDom0ToPatchInitialDom0():
            _launch_nodes.append(self.mGetDom0ToPatchInitialDom0())
        try:
            if not self.mPatchRequestRetried():
                self.mCreateDirOnNodes(_launch_nodes, self.mGetPatchStatesBaseDir())
                mWritePatchInitialStatesToLaunchNodes(PATCH_DOM0, self.mGetCustomizedDom0List(),
                                                      _launch_nodes, self.mGetMetadataJsonFile(), _launch_node_user)
        except Exception as e:
            self.mPatchLogWarn(f"Create Dir Error {str(e)} ")
            self.mPatchLogTrace(traceback.format_exc())

        # create a local patchmgr object with bare minimum arguments to make sure the _patchMgrObj attributes are local for this check only
        _patchMgrObj = InfraPatchManager(aTarget=PATCH_DOM0, aOperation=self.mGetTask(), aPatchBaseAfterUnzip=self.mGetDom0PatchBaseAfterUnzip(),
                                   aLogPathOnLaunchNode=self.mGetPatchmgrLogPathOnLaunchNode(), aHandler=self)

        # check if any patchmgr session running arround in the patch retry and
        # if so, let's wait for it.
        if self.mPatchRequestRetried():
            _p_ses_exist = PATCH_SUCCESS_EXIT_CODE
            _p_active_node = None
            # Skip patchmgr existence check during clusterless patching.
            if self.mPerformPatchmgrExistenceCheck():
                # check for patchmgr session existence
                _patchMgrObj.mSetLaunchNode(aLaunchNode=None)
                _patchMgrObj.mSetCustomizedNodeList(aCustomizedNodeList=self.mGetCustomizedDom0List())

                _p_ses_exist, _p_active_node = _patchMgrObj.mCheckForPatchMgrSessionExistence()

                # Wait for patchmgr to complete
                if _p_ses_exist == PATCHMGR_SESSION_ALREADY_EXIST:
                    # reset the node list to make sure patchmgr cmd execution
                    # only looked at the launch node
                    _patchMgrObj.mSetLaunchNode(aLaunchNode=_p_active_node)
                    _patchMgrObj.mSetCustomizedNodeList(aCustomizedNodeList=None)

                    _patchMgrObj.mWaitForPatchMgrCmdExecutionToComplete()

                    self.mPatchLogInfo("Finished waiting for Patch Manager command execution. Starting to handle exit code from Patch Manager")

                    _ret = _patchMgrObj.mGetStatusCode()
                    if _ret == PATCH_SUCCESS_EXIT_CODE:
                        self.mPatchLogInfo("Patch manager session found and completed successfully in patch retry")
                    else:
                        _suggestion_msg = f"Patch manager failed during patch retry on Dom0 : {_ret}. Exit code = {_p_active_node}"
                        _ret = PATCHMGR_RETRY_EXECUTION_FAILED_ERROR
                        self.mAddError(_ret, _suggestion_msg)
                        return _ret, _no_action_taken

        if self.mGetTask() not in [TASK_ROLLBACK, TASK_PATCH]:
            return _ret, _no_action_taken
        # Below checks for idempotency are done only for patch ot rollback operations
        if self.mGetTask() == TASK_ROLLBACK:
            _taskType = TASK_ROLLBACK
        else:
            _taskType = TASK_PATCH

        # Run post plugins if needed on already completed nodes
        if len(aDiscarded) > 0:
            self.mPatchLogInfo("Run patch manager and plugins for already upgraded nodes if required")
            # If new patch req, then mark completed for upgraded nodes.
            if not self.mPatchRequestRetried():
                self.mPatchLogInfo("Set completed for already upgraded nodes")
                for _n in aDiscarded:
                    mUpdateAllPatchStatesForNode(_launch_nodes, _n, self.mGetMetadataJsonFile(), PATCH_COMPLETED, _launch_node_user)
            elif self.mPatchRequestRetried():
                # Verify last attempted patchmgr and resume if required.
                for _n in aDiscarded:
                    _read_patch_state = mGetPatchStatesForNode(_launch_nodes, self.mGetMetadataJsonFile(), _n,
                                                               PATCH_MGR, _launch_node_user)
                    if _read_patch_state == PATCH_RUNNING:
                        _active_launch_node = mGetLaunchNodeForTargetType(_launch_nodes,
                                                                          self.mGetMetadataJsonFile(),
                                                                          PATCH_DOM0, _launch_node_user)
                        self.mPatchLogInfo(
                            f"Launch node where last patchmgr was run = {_active_launch_node} and log path = {self.mGetPatchmgrLogPathOnLaunchNode()}")

                        """
                        Here PatchmgrConsole.out file presence checked in two directories
                        1.  patchmgr_log_path_on_launch_node
                        2.  patchmgr_log_path_on_launch_node_launch_node_name(At the end of patching patchmgr log directory gets renamed by appending launch_node_name
                        It has to be in one of the directory because before patch retry, patch state was PATCH_RUNNING

                        """
                        _patchmgr_log_directory_to_check = self.mGetPatchmgrLogPathOnLaunchNode()
                        _patchmgr_console_file_before_patchmgr_completion_found = False
                        _patchmgr_console_file_after_patchmgr_completion_found = False

                        # Check for the PatchmgrConsole.out presence in patchmgr_log_before_completion
                        # ( /EXAVMIMAGES/dbserver.patch.zip_exadata_ol7_22.1.10.0.0.230422_Linux-x86-64.zip/dbserver_patch_221130/patchmgr_log_b75f885d-74c0-4979-8219-506d909aff6a)
                        _patchmgr_console_file_before_patchmgr_completion = _patchMgrObj.mGetPatchMgrConsoleOutputFile()
                        _patchmgr_console_file_before_patchmgr_completion_found, _ = self.mCheckFileExistsOnRemoteNodes([_active_launch_node], _patchmgr_console_file_before_patchmgr_completion)

                        if _patchmgr_console_file_before_patchmgr_completion_found:
                            _patchmgr_log_directory_to_check = self.mGetPatchmgrLogPathOnLaunchNode()
                        else:
                            # Check for PatchmgrConsole.out presence in patcmgr_log_after_completion
                            # ( /EXAVMIMAGES/dbserver.patch.zip_exadata_ol7_22.1.10.0.0.230422_Linux-x86-64.zip/dbserver_patch_221130/patchmgr_log_b75f885d-74c0-4979-8219-506d909aff6a_slcs27dv0405m)
                            if _active_launch_node:
                                _patchmgr_console_file_after_patchmgr_completion = f"{self.mGetPatchmgrLogPathOnLaunchNode()}_{_active_launch_node.split('.')[0]}/{'PatchmgrConsole.out'}"
                                _patchmgr_console_file_after_patchmgr_completion_found, _ = self.mCheckFileExistsOnRemoteNodes([_active_launch_node], _patchmgr_console_file_after_patchmgr_completion)
                                if _patchmgr_console_file_after_patchmgr_completion_found:
                                    _patchmgr_log_directory_to_check = f"{self.mGetPatchmgrLogPathOnLaunchNode()}_{_active_launch_node.split('.')[0]}"

                        # If PatchmgrConsole.out does not exists in either of the patch log directories, marking the state as completed since the node is already upgraded
                        # This scenario might not occur at all
                        if not _patchmgr_console_file_before_patchmgr_completion_found and not _patchmgr_console_file_after_patchmgr_completion_found:
                            self.mPatchLogInfo(
                                f"Updating PATCH_MGR patchmetadata as completed for the node {_n} during CheckIdemPotency as node is up to date")
                            mUpdatePatchMetadata(PATCH_DOM0, _launch_nodes, _n,
                                                 self.mGetMetadataJsonFile(), PATCH_MGR, PATCH_COMPLETED,aLaunchNode=_active_launch_node, aUser=_launch_node_user)
                        else:
                            # reset the node list to make sure patchmgr cmd execution
                            # only looked at the launch node
                            _patchMgrObj.mSetLaunchNode(aLaunchNode=_active_launch_node)
                            _patchMgrObj.mSetCustomizedNodeList(aCustomizedNodeList=None)
                            _patchMgrObj.mSetLogPathOnLaunchNode(aLogPathOnLaunchNode=_patchmgr_log_directory_to_check)

                            _patchMgrObj.mWaitForPatchMgrCmdExecutionToComplete()

                            self.mPatchLogInfo("Finished waiting for Patch Manager command execution. Starting to handle exit code from Patch Manager")

                            _ret = _patchMgrObj.mGetStatusCode()
                            if _ret == PATCH_SUCCESS_EXIT_CODE:
                                self.mPatchLogInfo("Patch manager success during patch retry")
                                mUpdatePatchMetadata(PATCH_DOM0, _launch_nodes, _n,
                                                     self.mGetMetadataJsonFile(), PATCH_MGR, PATCH_COMPLETED, aLaunchNode=None, aUser=_launch_node_user)
                            else:
                                mUpdatePatchMetadata(PATCH_DOM0, _launch_nodes, _n,
                                                     self.mGetMetadataJsonFile(), PATCH_MGR, PATCH_FAILED, aLaunchNode=None, aUser=_launch_node_user)
                                _suggestion_msg = f"Patch manager failed during patch retry. Exit code = {_ret} on {_n}"
                                ret = PATCHMGR_RETRY_EXECUTION_FAILED_ERROR
                                self.mAddError(ret, _suggestion_msg)
                                return ret, _no_action_taken
        self.mPatchLogInfo("Finished Check for IdemPotency in Patch Manager session")
        return _ret, _no_action_taken

