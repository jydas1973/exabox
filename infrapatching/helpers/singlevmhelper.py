#
# singlevmhelper.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
#
#    NAME
#      singlevmherlper.py - Place holder for common functionalities for  
#      single vm patching
#
#    DESCRIPTION
#      This module contains common methods which are shared between EXACC and EXACS 
#      single VM patching operations
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#    antamil     07/02/25  - Bug 38135681 Dbserver patch files cleanup for
#                            single vm patching for EXACC
#    antamil     06/25/25  - Bug 38089462 Dbserver patch files cleanup for
#                            single vm patching for EXACS
#    antamil     05/23/25  - Bug 37969822 Changes to make infrapatching key tag to be
#                            used for all patch operations
#    antamil     11/27/24   - Bug 37236994 - Changes on cleanup of passwordless ssh
#                             for single vm patching
#    antamil     11/05/24 - Bug 37222448 - Fix for copying dbserver file, handling
#                           recut bundle and cleanup ssh entries


import os, sys, logging
import traceback
from datetime import time
from time import sleep
import json
from exabox.infrapatching.utils.utility import flocked, mChangeOwnerofDir
from exabox.ovm.clumisc import ebCluSshSetup
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.infrapatching.utils.constants import *
from exabox.infrapatching.core.infrapatcherror import *
from exabox.infrapatching.utils.utility import runInfraPatchCommandsLocally, mGetInfraPatchingConfigParam
from exabox.infrapatching.handlers.loghandler import LogHandler
from exabox.infrapatching.utils.constants import EXAPATCHING_KEY_TAG
import glob


sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))
log = logging.getLogger(__name__)


class SingleVMHandler(LogHandler):

    def __init__(self, is_exacc):
        self.__is_exacc = is_exacc

    def mGetIsExaCC(self):
        return self.__is_exacc   

    def mCpsGetSSHPublicKeyFromHost(self, aCpsHost, aKeyComment="CpsLaunchNodeKey"):
        """
        Returns aHost's public ssh key value. If the key doesn't exist, then it is created with ssh-keygen command.
        """

        _exakms = get_gcontext().mGetExaKms()
        _ssh_file_missing = False

        _is_rsa = True
        if _exakms.mGetDefaultKeyAlgorithm() == "ECDSA":
            _is_rsa = False

        _ssh_key = ''
        _cmd = ""
        _priv_key_rc = 0
        _pub_key_rc = 0

        if _is_rsa:
            _cmd_list = []
            _cmd_list.append(['sudo', 'ls', '-l', '/root/.ssh/id_rsa'])
            _priv_key_rc, _o = runInfraPatchCommandsLocally(_cmd_list)

            _cmd_list = []
            _cmd_list.append(['sudo', 'ls', '-l', '/root/.ssh/id_rsa.pub'])
            _pub_key_rc, _o = runInfraPatchCommandsLocally(_cmd_list)
            if _pub_key_rc != 0  or _priv_key_rc != 0:
                _ssh_file_missing = True
                _cmd_list = []
                _cmd_list.append(
                    ['sudo', 'ssh-keygen', '-C', aKeyComment, '-q', '-t', 'rsa', '-N', '', '-f', '/root/.ssh/id_rsa'])
            _key_cmd_list = []
            _key_cmd_list.append(['sudo', 'cat', '/root/.ssh/id_rsa.pub'])
        else:
            _cmd_list = []
            _cmd_list.append(['sudo', 'ls', '-l', '/root/.ssh/id_ecdsa'])
            _priv_key_rc, _o = runInfraPatchCommandsLocally(_cmd_list)

            _cmd_list = []
            _cmd_list.append(['sudo', 'ls', '-l', '/root/.ssh/id_ecdsa.pub'])
            _pub_key_rc, _o = runInfraPatchCommandsLocally(_cmd_list)
            if _pub_key_rc != 0 or _priv_key_rc != 0:
                _ssh_file_missing = True
                # _cmd = "ssh-keygen -C '%s' -q -t rsa -N '' -f /root/.ssh/id_ecdsa <<<y > /dev/null 2>&1; cat /root/.ssh/id_ecdsa.pub" % aKeyComment
                _cmd_list = []
                _cmd_list.append(
                    ['sudo', 'ssh-keygen', '-C', aKeyComment, '-q', '-t', 'ecdsa', '-N', '', '-f',
                     '/root/.ssh/id_ecdsa'])
            _key_cmd_list = []
            _key_cmd_list.append(['sudo', 'cat', '/root/.ssh/id_ecdsa.pub'])

        if _ssh_file_missing:
            # Create new SSH Key
            runInfraPatchCommandsLocally(_cmd_list)

        _rc, _output = runInfraPatchCommandsLocally(_key_cmd_list)

        if _output:
            _ssh_key = _output.strip()
            ebLogInfo(f'Obtained SSH public key for host {aCpsHost} key: {_ssh_key}')
            # Retain the key comment which can be used when cleanup
            self.__hostkey = aKeyComment
        else:
            self.mPatchLogError(
                f'Failed to get public key for host {aCpsHost}')

        return _ssh_key

    def mCpsAddToKnownHosts(self, aCpsHost, aRemoteHostList):
        """
        Adds all nodes listed in aRemoteHostList to the known_hosts file in aHost.
        """
        _completed_nodes_list = []

        _cmd_add_ecdsa_keys = 'sudo ssh-keyscan -t ecdsa %s'
        _cmd_add_rsa_keys = 'sudo ssh-keyscan -t rsa %s'
        _cmd_add_available_keys = 'sudo ssh-keyscan %s'

        ebLogInfo(f'{aCpsHost}: Start updating known_hosts file for target nodes: {aRemoteHostList}')

        for _h in aRemoteHostList:
            _cmd_list_scan_ssh_keys = []
            _cmd_list_scan_ssh_keys.append(['sudo', 'ssh-keyscan', _h])
            _rc, _out = runInfraPatchCommandsLocally(_cmd_list_scan_ssh_keys)
            '''_output is list of lines like below.
               [ 
                 'nodename ssh-rsa AAAAB3NzaC1yXXXXXXXXX',
                 'nodename ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYXXXXXX'
               ]
            '''
            _output = _out.split("\n")
            try:
                # Sample _scanned_keys = ['ecdsa-sha2-nistp256', 'ssh-rsa']
                _scanned_keys = [_line.split()[1] for _line in _output]
                ebLogInfo(f"{aCpsHost}: scanned keys from node {_h} : {_scanned_keys}")

                if 'ecdsa' in " ".join(_scanned_keys):
                    ebLogInfo(f'{aCpsHost}: Adding ECDSA key for {_h}')

                    _cmd_list = []
                    _cmd_list.append(['sudo', 'ssh-keyscan', '-t', 'ecdsa', _h])
                    _cmd_list.append(['sudo', 'tee', '-a', '/root/.ssh/known_hosts'])
                    _rc, _o = runInfraPatchCommandsLocally(_cmd_list)

                if 'rsa' in " ".join(_scanned_keys):
                    ebLogInfo(f'{aCpsHost}: Adding RSA key for {_h}')
                    _cmd_list = []
                    _cmd_list.append(['sudo', 'ssh-keyscan', '-t', 'rsa', _h])
                    _cmd_list.append(['sudo', 'tee', '-a', '/root/.ssh/known_hosts'])
                    _rc, _o = runInfraPatchCommandsLocally(_cmd_list)
                
                if not 'ecdsa' in " ".join(_scanned_keys) and not 'rsa' in " ".join(_scanned_keys):
                    self.mPatchLogWarn(f'{aCpsHost}: Neither ECDSA nor RSA key found for {_h}')
                    self.mPatchLogWarn(f'{aCpsHost}: Trying to add default available keys for {_h}')
                    _cmd_list = []
                    _cmd_list.append(['sudo', 'ssh-keyscan', _h])
                    _cmd_list.append(['sudo', 'tee', '-a', '/root/.ssh/known_hosts'])
                    _rc, _o = runInfraPatchCommandsLocally(_cmd_list)
                else:
                    _completed_nodes_list.append(_h)
            except:
                self.mPatchLogError(f"{aCpsHost}: ssh-keyscan could not get list of keys scanned from node {_h}")

        if len(aRemoteHostList) == len(_completed_nodes_list):
            ebLogInfo(f'{aCpsHost}: Completed updating known_hosts file for target nodes: {aRemoteHostList}')
        else:
            _pending_nodes = [_n for _n in aRemoteHostList if not _n in _completed_nodes_list]
            self.mPatchLogError(f'{aCpsHost}: known_hosts not updated for some nodes {_pending_nodes}')

    def mCpsRemoveFromKnownHosts(self, aRemoteHostList):
        """
        Removes all nodes listed in aRemoteHostList from the known_hosts file in Cps.
        """

        # fetch IPs  of all remote nodes
        _remoteHostIPList = []

        _node = exaBoxNode(get_gcontext())
        for _remoteNode in aRemoteHostList:
            try:
                _node.mConnect(aHost=_remoteNode)
                # Get ip of the node.
                _i, _o, _e = _node.mExecuteCmd("/bin/hostname -i")
                _ip = _o.readlines()[0].strip()
                _remoteHostIPList.append(_ip)
            except Exception as e:
                self.mPatchLogWarn(
                    "Exception caught while fetching IP of remote node %s for cleaning known_hosts file. %s" % (
                    _remoteNode, str(e)))
                self.mPatchLogTrace(traceback.format_exc())
            finally:
                if _node.mIsConnected():
                    _node.mDisconnect()

            #
            # Cleanup known_host file based on Nat IP of DomU
            #
            _cmd_list = []
            _cmd_list.append(['/usr/bin/nslookup', _remoteNode])
            _cmd_list.append(['/usr/bin/grep', 'Address'])
            _cmd_list.append(['/usr/bin/grep', '-v', '#'])
            _cmd_list.append(['/usr/bin/awk', '{print $2}'])
            _rc, _out = runInfraPatchCommandsLocally(_cmd_list)
            if _out:
                _ip = _out
                ebLogInfo(f'Nat Ip of {_remoteNode} is {_ip}')
                _remoteHostIPList.append(_ip)
            else:
                self.mPatchLogError(f'Unable to get the NatIp for {_remoteNode}')
    


        # remove known_hosts file entries
        # _cmd = 'ssh-keygen -R %s > /dev/null 2>&1'
        # _cmd = 'sudo ssh-keygen -R %s'

        for _h in aRemoteHostList:
            _cmd_list = []
            _cmd_list.append(['sudo', 'ssh-keygen', '-R', _h])
            self.mPatchLogInfo("Removing IP/Hostname : %s entries from known_hosts file." % _h)
            runInfraPatchCommandsLocally(_cmd_list)
            _sh = _h.split(".")[0]
            if _h != _sh:
                _cmd_list = []
                _cmd_list.append(['sudo', 'ssh-keygen', '-R', _sh])
                runInfraPatchCommandsLocally(_cmd_list)
        # remove ip based entries
        for _remoteIP in _remoteHostIPList:
            _cmd_list = []
            _cmd_list.append(['sudo', 'ssh-keygen', '-R', _remoteIP])
            runInfraPatchCommandsLocally(_cmd_list)

    def mCpsSetSSHPasswordlessForInfraPatching(self, aCpsHost, aRemoteHostList, _ssh_env):
        """
        Set ssh passwordless between cps and a list of remote hosts.
        """

        # Get ssh public key from the host
        _key = self.mCpsGetSSHPublicKeyFromHost(self, aCpsHost)

        self.mCpsRemoveFromKnownHosts(aRemoteHostList)
        self.mCpsAddToKnownHosts(aCpsHost, aRemoteHostList)

        # RoceSwitch equivalence set up is completely different business logic
        # than other components, hence the if check
        _ssh_env.mAddKeyToHostsIfKeyDoesNotExist(aCpsHost, _key, aRemoteHostList)
        return _key

    def mGetLocalNodePatchMgrDiagFiles(self, _domu_target_instance, aNodeType, aNodeList, aRemotePath):
        """
        Copies the last patchmgr_files found for various node types to /log.
        Incase of EXACC , it collects the logs from CPS host
        """

        aRemotePath = _domu_target_instance.mGetPatchmgrLogPathOnLaunchNode()
        _patchmgr_diag_tar = aRemotePath.split('/')[-1] + ".tar"

        self.mPatchLogInfo("aRemotePath = %s\n_patchmgr_diag_tar = %s\n"
                           " dirname = %s\n basename = %s\n" % (
                               aRemotePath, _patchmgr_diag_tar,
                               os.path.dirname(aRemotePath),
                               os.path.basename(aRemotePath)
                           ))

        # tar the diagnostic files
        tar_cmd_list = []
        tar_cmd_list.append(['tar', 'cvf', os.path.dirname(aRemotePath) + "/" + _patchmgr_diag_tar,
                             os.path.basename(aRemotePath)])
        try:
            self.mPatchLogInfo("Taring patch manager diagnosis files from "
                               "DOM0 %s\n " % (str(_domu_target_instance.mGetExternalLaunchNode())))

            runInfraPatchCommandsLocally(tar_cmd_list)
        except Exception as e:
            self.mPatchLogWarn("Error while taring the diagnosis files(%s)"
                               % (str(tar_cmd_list)))
            self.mPatchLogTrace(traceback.format_exc())

        # copy the tar to local
        try:
            self.mPatchLogInfo(
                "Copying diagnosis '%s' file from node - %s , location - %s to exacloud location - %s" % (
                    _patchmgr_diag_tar, str(_domu_target_instance.mGetExternalLaunchNode()), aRemotePath, _domu_target_instance.mGetLogPath()))
            _source_patchmgr_log_loc = os.path.dirname(aRemotePath) + '/' + _patchmgr_diag_tar
            _dest_patchmgr_log_loc = os.path.join(_domu_target_instance.mGetLogPath(), _patchmgr_diag_tar)
            _cmd_list = []
            _cmd_list.append(['cp', '-rf', _source_patchmgr_log_loc, _dest_patchmgr_log_loc])
            runInfraPatchCommandsLocally(_cmd_list)
        except Exception as e:
            self.mPatchLogWarn(
                "Error while copying the diagnosis files from DOM0 error=%s\n rfile=%s\n lfile=%s to exacloud location - %s"
                % (str(e), os.path.dirname(aRemotePath) + '/' + _patchmgr_diag_tar,
                   os.path.join(_domu_target_instance.mGetLogPath(), _patchmgr_diag_tar), _domu_target_instance.mGetLogPath()))
            self.mPatchLogTrace(traceback.format_exc())
            _cmd_list = []
            _cmd_list.append(['ls', os.path.dirname(aRemotePath)])
            _rc, _out, = runInfraPatchCommandsLocally(_cmd_list)
            self.mPatchLogInfo(
                "We have following files in dir (%s) in node (%s) that dont have the exected %s " % (
                    _out, str(_domu_target_instance.mGetExternalLaunchNode()), _patchmgr_diag_tar))

        # remove the tar file
        try:
            if os.path.exists(os.path.join(os.path.dirname(aRemotePath), _patchmgr_diag_tar)):
                _cmd_list = []
                _cmd_list.append(['rm', '-f', os.path.dirname(aRemotePath) + "/" + _patchmgr_diag_tar])
                runInfraPatchCommandsLocally(_cmd_list)
        except Exception as e:
            self.mPatchLogWarn("Error while removing the diagnosis files from "
                               "DOM0 %s" % str(e))
            self.mPatchLogTrace(traceback.format_exc())

        # secondly get the files from the individual DOMUs
        for _domu in aNodeList:
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_domu)
            _cmd_list_diag_files = (
                    'find %s -type f -name "*package*"|grep -v tmp' % ('/var/log/cellos'))
            self.mPatchLogInfo(
                "Copying patch manager diagnosis files from DOMU %s to exacloud location - %s" % (
                    _domu, _domu_target_instance.mGetLogPath()))
            try:
                _in, _out, _err = _node.mExecuteCmd(_cmd_list_diag_files)
                _output = _out.readlines()

                if _output:
                    for _o in _output:
                        _file = _o.strip().split("/")[-1]
                        if _node.mFileExists(os.path.join('/var/log/cellos/', _file)):
                            _domu_target_instance.mSetListOfLogsCopiedToExacloudHost(os.path.join('/var/log/cellos/', _file))
                            _node.mCopy2Local(os.path.join('/var/log/cellos/', _file),
                                              os.path.join(_domu_target_instance.mGetLogPath(), _domu + '.' + _file))
            except Exception as e:
                self.mPatchLogWarn(
                    'Error while copying DOMU diagnosis files: %s from %s node to exacloud location - %s.' % \
                    (str(e), _domu, _domu_target_instance.mGetLogPath()))
                self.mPatchLogTrace(traceback.format_exc())

            if _node.mIsConnected():
                _node.mDisconnect()

        return

    def mConfigureSSHForSingleVM(self, _initial_node, _nodes_to_patch_except_initial, _ssh_env_setup, _domu_handler):
        _nat_domu_node_list = [_domu_handler.mGetDomUNatHostNameforDomuCustomerHostName(_domu_name) \
                               for _domu_name in _nodes_to_patch_except_initial]
        if self.mGetIsExaCC():
            self.mCpsSetSSHPasswordlessForInfraPatching(_initial_node, _nat_domu_node_list, _ssh_env_setup)
        else:
            with open(LOCK_FILE_NAME, 'a') as file:
                with flocked(file):
                    _ssh_env_setup.mConfigureSshForMgmtHost(_initial_node, _nat_domu_node_list,
                                                            EXAPATCHING_KEY_TAG,
                                                            _domu_handler.mGetDomUPatchBaseDir())
        return _nat_domu_node_list

    def mGetPatchMgrDiagFilesForSingleVM(self, _domu_target_instance, _node_patcher, _node_to_patch, _patchmgr_log_path):
        if self.mGetIsExaCC():
            self.mGetLocalNodePatchMgrDiagFiles(_domu_target_instance, PATCH_DOMU,
                                                _node_to_patch,
                                                _patchmgr_log_path)
        else:
            mChangeOwnerofDir(_node_patcher, _patchmgr_log_path, 'opc', 'opc')
            _domu_target_instance.mGetPatchMgrDiagFiles(_node_patcher,
                                       PATCH_DOMU,
                                       _node_to_patch,
                                       _patchmgr_log_path)

    def mCpsRestoreSSHKey(self):

        _exakms = get_gcontext().mGetExaKms()

        # Backup key
        _filename = "/root/.ssh/id_rsa"
        if _exakms.mGetDefaultKeyAlgorithm() == "ECDSA":
            _filename = "/root/.ssh/id_ecdsa"
        _cmd_list = []
        _cmd_list.append(['ls', '-l', _filename + "_keybackup"])
        _rc, _o = runInfraPatchCommandsLocally(_cmd_list)
        if int(_rc) == 0:
            _cmd_list = []
            _cmd_list.append(['/bin/mv', _filename + "_keybackup", _filename])
            _rc, _o = runInfraPatchCommandsLocally(_cmd_list)
            if int(_rc) != 0:
                self.mPatchLogWarn(f"Backup not available: {_o.read()}")

    def mCpsCleanSSHPasswordless(self, aHost, aRemoteHostList, _domu_handler):
        """
        Cleans the ssh passwordless configuration.
        """

        # Removes the ssh key based on both host name and key comment if found.
        # Infact, removes the ssh key based on the comment would be
        # sufficient in future.
        _sshEnvDict = _domu_handler.mGetSSHEnvSetUp()
        if _sshEnvDict:
            _ssh_env = _sshEnvDict["sshEnv"]
            _ssh_env.mRemoveKeyFromHosts(aHost.split('.')[0], aRemoteHostList)
            _ssh_env.mRemoveKeyFromHostsByComment(self.__hostkey, aRemoteHostList)
            self.mCpsRestoreSSHKey()


    def mCleanupSSHForSingleVM(self, fromHost, remoteHostLists, _ssh_env, _domu_handler):
        # Performing the cleanup based on NAT domu name
        _nat_domu_node_list = [_domu_handler.mGetDomUNatHostNameforDomuCustomerHostName(_domu_name) \
                               for _domu_name in remoteHostLists]
        if self.mGetIsExaCC():
            self.mCpsCleanSSHPasswordless(fromHost, _nat_domu_node_list, _domu_handler)
            _domu_handler.mGetCluPatchCheck().mVerifyPatchmgrSshConnectivityBetweenExadataHosts(_nat_domu_node_list,
                                                                                       fromHost,
                                                                                       aStage="PostPatch")
        else:
            #Cleanup of passwordless ssh between the management host and target domu will follow the steps below:
            #    a. Remove the keys on target domu
            #    b. Cleanup known host file
            #    c. Delete the private key file in /var/odo/InfraPatchBase/keys
            #    d. Perform ssh validation, this will fail
            #    e. cleanup the entries on the config file
            #    Step a to c is performed by mCleanupSSHConfigForMgmtHost
            #    Step e is performed by mCleanupSSHConfigFileOnMgmtHost

            _ssh_env.mCleanupSSHConfigForMgmtHost(fromHost, _nat_domu_node_list)
            _domu_handler.mGetCluPatchCheck().mVerifyPatchmgrSshConnectivityBetweenExadataHosts(_nat_domu_node_list,
                                                                                       fromHost,
                                                                                       aStage="PostPatch",
                                                                                       aSshUser='opc')
            with open(LOCK_FILE_NAME, 'a') as file:
                with flocked(file):
                    _ssh_env.mCleanupSSHConfigFileOnMgmtHost(fromHost, _nat_domu_node_list)


    def mGetLocalDom0FileCode(self, aRemotePath):
        """
        Gets the most recent code. File name is patchmgr.stdout.<code>
        """
        _code = ''
        if aRemotePath[-1] != '/':
            aRemotePath += '/'
        _cmd_list_files = []
        _cmd_list_files.append(['ls', '-t', os.path.join(aRemotePath, PATCH_STDOUT)+"*"])
        _cmd_list_files.append(['head', '-1'])
        _rc, _out = runInfraPatchCommandsLocally(_cmd_list_files)
        if _out:
            _output = _out.split("\n")
            _file = _output[0].strip().split("/")[-1]
            self.mPatchLogInfo(f"Log file from output {_file} ")
            # return patchmgr.stdout , else if patchmgr.stdout.<code> , then return the proper code
            if _file is not None and _file.find("stdout.") < 0:
                return _code
            _re_out = re.match(".*stdout([.0-9a-zA-Z]+)", _file)
            if _re_out:
                _code = int(_re_out.groups()[0])
        return _code

    def mCopyDbserverPatchFile(self, _remote_node, _local_patch_file, _remote_patch_file, _domu_handler, _node):
        _tmp_local_patch_file = _local_patch_file
        _local_patch_file = f'{_local_patch_file}_{_domu_handler.mGetMasterReqId()}'
        _domu_handler.mGetCluControl().mExecuteCmd(f'cp {_tmp_local_patch_file} {_local_patch_file}')
        _node.mSetUser('opc')
        _max_number_of_ssh_retries = mGetInfraPatchingConfigParam('max_number_of_ssh_retries')
        _node.mSetMaxRetries(int(_max_number_of_ssh_retries))
        _node.mConnect(aHost=_remote_node)
        _node.mCopyFile(_local_patch_file, _remote_patch_file)
        _domu_handler.mPatchLogInfo(f"Deleting {_local_patch_file}")
        _domu_handler.mGetCluControl().mExecuteCmd(f'rm -f {_local_patch_file}')

    def mCleanupExadataPatchesSingleVMForExaCS(self, _domu_target_instance, aLaunchNodeCandidate, aDomU, aPatchBase):
        """
        This method Purges all the exadata patch files with versions
        other than that of the current target version passed, active
        and inactive exadata versions. Patches are purged on the launch
        nodes like managment host.

        Return "0x00000000" -> PATCH_SUCCESS_EXIT_CODE if success,
        otherwise return error code.
        """

        _return_status = PATCH_SUCCESS_EXIT_CODE

        _node = exaBoxNode(get_gcontext())
        _launch_node = exaBoxNode(get_gcontext())
        _launch_node.mSetUser('opc')
        _active_image_version = None
        _inactive_image_version = None
        _list_of_files_to_be_retained_string = None
        _purge_patches = True


        try:
            _node.mConnect(aHost=aDomU)
            _launch_node.mConnect(aHost=aLaunchNodeCandidate)
            '''
            Fetching Exadata active exadata version using imageinfo command and inactive 
            exadata version details using dbserver_backup.sh script output. Exadata patches 
            from the current Exadata version, previous exadata and current target version
            (It may be same as the active version at times if the patch is applied and upgrade 
            fails.) will be preserved,all other Exadata patch files will be purged.

            Example of an "ls -ltr" command output from the launch nodes.

                drwxr-xr-x 3 root root        3896 May  6 05:55
                dbserver.patch.zip_exadata_ovs_21.2.11.0.0.220414.1_Linux-x86-64.zip
                drwxr-xr-x 2 root root        3896 May  6 06:24 crashfiles
                drwxr-xr-x 2 root root        3896 May  6 09:43 13.2.9.0.0.220216.patch.zip
                drwxr-xr-x 2 root root        3896 May  6 09:43 14.2.9.0.0.220216.patch.zip
                drwxr-xr-x 2 root root        3896 May  6 09:43 13.2.7.0.0.211221.switch.patch.zip
                drwxr-xr-x 2 root root        3896 May  6 09:43 14.2.7.0.0.211221.switch.patch.zip
                drwxr-xr-x 2 root root        3896 May  6 09:43 15.2.7.0.0.211221.switch.patch.zip
                drwxr-xr-x 2 root root        3896 May  6 09:43 16.2.7.0.0.211221.switch.patch.zip
                drwxr-xr-x 2 root root        3896 May  6 09:43 dbserver.patch.zip_exadata_ovs_13.2.11.0.0.220414.1_Linux-x86-64.zip
                drwxr-xr-x 2 root root        3896 May  6 09:43 dbserver.patch.zip_exadata_ovs_14.2.11.0.0.220414.1_Linux-x86-64.zip
                drwxr-xr-x 2 root root        3896 May  6 09:43 dbserver.patch.zip_exadata_ovs_15.2.11.0.0.220414.1_Linux-x86-64.zip
                drwxr-xr-x 8 root root        3896 May  6 09:44 dbnodeupdate.patchmgr
                [root@slcs27adm03 EXAVMIMAGES]#
                '''
            _cmd_get_active_image_version = "/usr/local/bin/imageinfo -ver"
            _i, _o, _e = _node.mExecuteCmd(_cmd_get_active_image_version)
            _exit_code = int(_node.mGetCmdExitStatus())
            if int(_exit_code) == 0:
                _o = _o.readlines()
                _active_image_version = _o[0].strip()
                self.mPatchLogInfo(f"Active image version fetched  : {_active_image_version}")
            else:
                self.mPatchLogWarn(f"Unable to get image version on the launch node : {aDomU}")
                _purge_patches = False

            # imagehistory | grep '^Version' | tail -2 | head -1 | awk '{print $3}'
            # [root@sea201323exdd008 ~]# imagehistory | grep '^Version' | tail -2 | head -1 | awk '{print $3}'
            # 24.1.8.0.0.250208
            _cmd_get_inactive_image_version = "imagehistory | grep '^Version' | tail -2 | head -1 | awk '{print $3}'"
            _i, _o, _e = _node.mExecuteCmd(_cmd_get_inactive_image_version)
            _exit_code = int(_node.mGetCmdExitStatus())
            if int(_exit_code) == 0:
                _inactive_image_version = (_o.readlines()[-1]).strip()

                if (_inactive_image_version is not None and _inactive_image_version == _active_image_version) or (
                        _active_image_version and _active_image_version == _domu_target_instance.mGetTargetVersion()):
                    _purge_patches = False

            '''
            If active image version is empty or None, patch purge will be skipped.
            '''
            if _purge_patches:
                if _active_image_version:
                    _list_of_files_to_be_retained_string = _active_image_version

                if _active_image_version and _active_image_version != _domu_target_instance.mGetTargetVersion():
                    self.mPatchLogInfo(
                        "Target version patches will be preserved on launch nodes only in case current active version and target version are different.")
                    self.mPatchLogInfo(
                        f"Active Exadata version : {str(_active_image_version)}, Target Exadata version : {str(_domu_target_instance.mGetTargetVersion())}")
                    _list_of_files_to_be_retained_string = _list_of_files_to_be_retained_string + "|" + _domu_target_instance.mGetTargetVersion()

                '''
                    In case of a newly provisioned environment, backup version 
                    will not be available.
                '''
                if _inactive_image_version:
                    self.mPatchLogInfo(
                        f"Inactive image version fetched to purge patches : {_inactive_image_version}")
                    _list_of_files_to_be_retained_string = _list_of_files_to_be_retained_string + "|" + _inactive_image_version

                if _list_of_files_to_be_retained_string:
                    _cmd = f"ls -d {aPatchBase}/*/dbserver_patch_*/*_progress.txt"
                    _in, _out, _err = _launch_node.mExecuteCmd(_cmd)
                    _exit_code = int(_launch_node.mGetCmdExitStatus())
                    if _exit_code == 0:
                        _output = _out.readlines()
                        for _dir in _output:
                            _patch_version = _dir.split("/")[-3]
                            _list_of_files_to_be_retained_string = _list_of_files_to_be_retained_string + "|" + _patch_version 
                    self.mPatchLogInfo(f"Versions to be retained {_list_of_files_to_be_retained_string}")
                    _cmd_list_files_patch_to_be_purged = f"ls -ld {aPatchBase}/*patch.zip* | egrep -v '{_list_of_files_to_be_retained_string}' | /usr/bin/awk '{{print $9}}' | sudo xargs rm -rfv"
                    _launch_node.mExecuteCmdLog(_cmd_list_files_patch_to_be_purged)

        except Exception as e:
            self.mPatchLogWarn(f"Unable to purge exadata patches on Node : {aLaunchNodeCandidate}. Error : {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
            _return_status = EXADATA_PATCHES_CLEANUP_FAILED
        finally:
            self.mPatchLogInfo("Purging of Exadata patches task completed.")
            if _node.mIsConnected():
                _node.mDisconnect()
            else:
                _return_status = PATCHING_CONNECT_FAILED

            if _launch_node.mIsConnected():
                _launch_node.mDisconnect()
            else:
                _return_status = PATCHING_CONNECT_FAILED
        return _return_status

    def mCleanupExadataPatchesSingleVMForExaCC(self, _domu_target_instance, aDomU, aPatchBase):
        """
        This method Purges all the exadata patch files with versions
        other than that of the current target version passed, active
        and inactive exadata versions. Patches are purged on the launch
        nodes like managment host.

        Return "0x00000000" -> PATCH_SUCCESS_EXIT_CODE if success,
        otherwise return error code.
        """

        _return_status = PATCH_SUCCESS_EXIT_CODE

        _node = exaBoxNode(get_gcontext())
        _active_image_version = None
        _inactive_image_version = None
        _list_of_files_to_be_retained_string = None
        _purge_patches = True
        try:
            _node.mConnect(aHost=aDomU)
            '''
            Fetching Exadata active exadata version using imageinfo command and inactive 
            exadata version details using dbserver_backup.sh script output. Exadata patches 
            from the current Exadata version, previous exadata and current target version
            (It may be same as the active version at times if the patch is applied and upgrade 
            fails.) will be preserved,all other Exadata patch files will be purged.

            Example of an "ls -ltr" command output from the launch nodes.

                drwxr-xr-x 3 root root        3896 May  6 05:55
                dbserver.patch.zip_exadata_ovs_21.2.11.0.0.220414.1_Linux-x86-64.zip
                drwxr-xr-x 2 root root        3896 May  6 06:24 crashfiles
                drwxr-xr-x 2 root root        3896 May  6 09:43 13.2.9.0.0.220216.patch.zip
                drwxr-xr-x 2 root root        3896 May  6 09:43 14.2.9.0.0.220216.patch.zip
                drwxr-xr-x 2 root root        3896 May  6 09:43 13.2.7.0.0.211221.switch.patch.zip
                drwxr-xr-x 2 root root        3896 May  6 09:43 14.2.7.0.0.211221.switch.patch.zip
                drwxr-xr-x 2 root root        3896 May  6 09:43 15.2.7.0.0.211221.switch.patch.zip
                drwxr-xr-x 2 root root        3896 May  6 09:43 16.2.7.0.0.211221.switch.patch.zip
                drwxr-xr-x 2 root root        3896 May  6 09:43 dbserver.patch.zip_exadata_ovs_13.2.11.0.0.220414.1_Linux-x86-64.zip
                drwxr-xr-x 2 root root        3896 May  6 09:43 dbserver.patch.zip_exadata_ovs_14.2.11.0.0.220414.1_Linux-x86-64.zip
                drwxr-xr-x 2 root root        3896 May  6 09:43 dbserver.patch.zip_exadata_ovs_15.2.11.0.0.220414.1_Linux-x86-64.zip
                drwxr-xr-x 8 root root        3896 May  6 09:44 dbnodeupdate.patchmgr
                [root@slcs27adm03 EXAVMIMAGES]#
                '''
            _cmd_get_active_image_version = "/usr/local/bin/imageinfo -ver"
            _i, _o, _e = _node.mExecuteCmd(_cmd_get_active_image_version)
            _exit_code = int(_node.mGetCmdExitStatus())
            if int(_exit_code) == 0:
                _o = _o.readlines()
                _active_image_version = _o[0].strip()
                self.mPatchLogInfo(f"Active image version fetched  : {_active_image_version}")
            else:
                self.mPatchLogWarn(f"Unable to get image version on the launch node : {aDomU}")
                _purge_patches = False

            # imagehistory | grep '^Version' | tail -2 | head -1 | awk '{print $3}'
            # [root@sea201323exdd008 ~]# imagehistory | grep '^Version' | tail -2 | head -1 | awk '{print $3}'
            # 24.1.8.0.0.250208
            _cmd_get_inactive_image_version = "imagehistory | grep '^Version' | tail -2 | head -1 | awk '{print $3}'"
            _i, _o, _e = _node.mExecuteCmd(_cmd_get_inactive_image_version)
            _exit_code = int(_node.mGetCmdExitStatus())
            if int(_exit_code) == 0:
                _inactive_image_version = (_o.readlines()[-1]).strip()

                if (_inactive_image_version and _inactive_image_version == _active_image_version) or (
                        _active_image_version and _active_image_version == _domu_target_instance.mGetTargetVersion()):
                    _purge_patches = False
                    

            '''
            If active image version is empty or None, patch purge will be skipped.
            '''
            if _purge_patches:
                if _active_image_version:
                    _list_of_files_to_be_retained_string = _active_image_version

                if _active_image_version and _active_image_version != _domu_target_instance.mGetTargetVersion():
                    self.mPatchLogInfo(
                        "Target version patches will be preserved on launch nodes only in case current active version and target version are different.")
                    self.mPatchLogInfo(
                        f"Active Exadata version : {str(_active_image_version)}, Target Exadata version : {str(_domu_target_instance.mGetTargetVersion())}")
                    _list_of_files_to_be_retained_string = _list_of_files_to_be_retained_string + "|" + _domu_target_instance.mGetTargetVersion()

                '''
                    In case of a newly provisioned environment, backup version 
                    will not be available.
                '''
                if _inactive_image_version:
                    self.mPatchLogInfo(
                        f"Inactive image version fetched to purge patches : {_inactive_image_version}")
                    _list_of_files_to_be_retained_string = _list_of_files_to_be_retained_string + "|" + _inactive_image_version

                if _list_of_files_to_be_retained_string:
                    _file = f"{aPatchBase}/*/dbserver_patch_*/*_progress.txt"
                    _dirs = glob.glob(_file)
                    if _dirs:
                        for _dir in _dirs:
                            self.mPatchLogInfo(f" LINES:{_dir}")
                            _patch_version = _dir.split("/")[-3]
                            _list_of_files_to_be_retained_string = _list_of_files_to_be_retained_string + "|" + _patch_version
                    self.mPatchLogInfo(f"Versions to be retained {_list_of_files_to_be_retained_string}")
                    _dirs = glob.glob(f'{aPatchBase}/*patch.zip*')
                    if _dirs:
                        _dirs_str="\n".join(_dirs)
                        _cmd_list = []
                        _cmd_list.append(['echo', '-e', f'{_dirs_str}'])
                        _cmd_list.append(['egrep', '-v', f'{_list_of_files_to_be_retained_string}'])
                        _cmd_list.append(['sudo', 'xargs', 'rm', '-rfv'])
                        runInfraPatchCommandsLocally(_cmd_list)
        except Exception as e:
            self.mPatchLogWarn(f"Unable to purge exadata patches CPS host. Error : {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
            _return_status = EXADATA_PATCHES_CLEANUP_FAILED
        finally:
            self.mPatchLogInfo("Purging of Exadata patches task completed.")
            if _node.mIsConnected():
                _node.mDisconnect()
            else:
                _return_status = PATCHING_CONNECT_FAILED
        return _return_status
