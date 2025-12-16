"""
 Copyright (c) 2019, 2025, Oracle and/or its affiliates.

NAME:
    cs_base.py - Abstract file for create service steps

FUNCTION:
    Returns the Abstract CSBase object

NOTES:
   This is the abstract base class (abc) for all the create service 
   step implementation classes

EXTERNAL INTERFACES:
    CSBase

INTERNAL CLASSES:

History: 
    pbellary    08/15/2025 - Enh 38318848 - CREATE ASM CLUSTERS TO SUPPORT VM STORAGE ON EDV OF IMAGE VAULT
    aararora    08/07/2025 - ER 37858683: Add tcps config if present in the payload
    dekuckre    07/02/2025 - Add support for clone VM for basedb
    abflores    06/20/2025 - Bug 38003663 - Remove large FQDN before applying fs encryption
    avimonda    04/03/2025 - Bug 37742228 - EXACS: PROVISIONING FAILED WITH
                             ERROR:OEDA-1602: INVALID BOND FOR BRIDGE BONDETH1
                             ON HOST <DOM0>
    jfsaldan    04/02/2025 - Bug 37609603: Skip stale vm removal if vm_maker
                             process is running for it
    aararora    03/18/2025 - Bug 37508799: Optimize call to mValidateGridDisks
                             - parallel execution on cells
    dekuckre    03/06/2025 - 37363507: Cleanup vmbackup logs for the vm
    kukrakes    12/16/2024 - Bug 37396797 - CREATE SERVICE FAILED DUE TO /EXAVMIMAGES/GUESTIMAGES
                             WAS MISSING IN THE DOM0, BUT IT HAD A VM IN SHUTDOWN STATE. 
    prsshukl    09/16/2024 - Bug 37058304 - Check if the domU is connectable 
                             before connecting to it for deleting .ssh 
                             directory for opc user
    prsshukl    07/24/2024 - Bug 34014317 - Remove Storage Pool from libvirt definition on dom0s
    aararora    07/22/2024 - Bug 36864046: Cleanup ssh directory for opc user
                             during undo step of create user.
    pbellary    07/02/2024 - ENH 36690772 - EXACLOUD: IMPLEMENT PRE-VM STEPS FOR EXASCALE SERVICE
    pbellary    06/21/2024 - ENH 36690846 - IMPLEMENT POST-VM STEPS FOR EXASCALE SERVICE
    pbellary    06/21/2024 - ENH 36690743 - EXACLOUD: IMPLEMENT OEDA STEPS FOR EXASCALE CREATE SERVICE
    pbellary    06/14/2024 - ENH 36721696 - IMPLEMENT DELETE SERVICE STEPS FOR EXASCALE SERVICE
    pbellary    06/06/2024 - ENH 36603820 - REFACTOR CREATE SERVICE FLOW FOR ASM/XS/EXADB-XS
    srtata      04/19/2019 - fix comments and notes
    pbellary    03/29/2019 - Creation
"""

import abc
import operator
import time, string, random
from typing import Sequence
from datetime import datetime
from exabox.core.Node import exaBoxNode
import exabox.ovm.clubonding as clubonding
from exabox.ovm.vmboci import ebVMBackupOCI
from exabox.ovm.csstep.cs_util import csUtil
from exabox.core.Context import get_gcontext
from exabox.core.Context import exaBoxContext
from exabox.ovm.cluresmgr import ebCluResManager
from exabox.ovm.cluhealth import ebCluHealthCheck
from exabox.ovm.cluexascale import mRemoveVMmount
import exabox.ovm.clujumboframes as clujumboframes
from exabox.ovm.vmbackup import ebCluManageVMBackup
from exabox.ovm.sysimghandler import hasDomUCustomOS
from exabox.ovm.clustorage import ebCluStorageConfig
from exabox.ovm.clustorage import ebCluManageStorage
from exabox.ovm.kvmdgrpvmkr import exaBoxKvmDgrpVmkr
from exabox.healthcheck.cluexachk import ebCluExachk
from exabox.exakms.ExaKmsEntry import ExaKmsHostType
from exabox.network.dns.DNSConfig import ebDNSConfig
from exabox.ovm.cluserialconsole import serialConsole
from exabox.ovm.cluiptablesroce import ebIpTablesRoCE
from exabox.ovm.cluvmconsole_deploy import VMConsoleDeploy
from exabox.ovm.csstep.cs_constants import csConstants, csXSConstants, csBaseDBXSConstants, csXSEighthConstants
from exabox.tools.ebOedacli.ebOedacli import ebOedacli
from exabox.core.Error import ebError, ExacloudRuntimeError, gProvError
from exabox.ovm.cluexaccatp_filtering import ebExaCCAtpFiltering
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure
from exabox.ovm.cluencryption import (isEncryptionRequested, createAndPushRemotePassphraseSetup,
        deleteRemotePassphraseSetup, ensureSystemFirstBootEncryptedExistsParallelSetup,
        useLocalPassphrase, deleteOEDAKeyApiFromDom0, createEncryptionMarkerFileForVM,
        deleteEncryptionMarkerFileForVM, exacc_fsencryption_requested, exacc_save_fsencryption_passphrase,
        exacc_del_fsencryption_passphrase, patchXMLForEncryption)
from exabox.utils.node import (connect_to_host, node_exec_cmd,
        node_cmd_abs_path_check, node_exec_cmd_check, node_read_text_file,
        node_write_text_file, node_list_process)
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogTrace, ebLogWarn, ebLogDebug, ebLogVerbose, ebLogCritical
from exabox.ovm.bom_manager import ImageBOM
from exabox.ovm.clumisc import ebMigrateUsersUtil
from exabox.tools.oedacli import OedacliCmdMgr

class CSBase(metaclass=abc.ABCMeta):
    @property
    def name(self):
        return self.step

    @name.setter
    def name(self, name):
        self.step = name

    @abc.abstractmethod
    def doExecute(self, aExaBoxCluCtrlObj, aOptions, aStepList):
        pass

    @abc.abstractmethod
    def undoExecute(self, aExaBoxCluCtrlObj, aOptions, aStepList):
        pass

    def mInstallAhfonDom0(self,aExaBoxCluCtrlObj,steplist):
        _step_time = time.time()
        aExaBoxCluCtrlObj.mUpdateStatusCS(True, self.step, steplist, aComment='AHF install on Dom0')
        _options = aExaBoxCluCtrlObj.mGetArgsOptions()
        _hcObj = ebCluHealthCheck(aExaBoxCluCtrlObj, _options)
        _hcObjExachk = ebCluExachk(_hcObj, _options)
        _hcObjExachk.mInstallAhf("dom0",_options)
        aExaBoxCluCtrlObj.mLogStepElapsedTime(_step_time, 'AHF install on Dom0 : completed')

    def mRpmCheck(self, aExaBoxCluCtrlObj):
        for _dom0,_domU in aExaBoxCluCtrlObj.mReturnDom0DomUPair():
            with connect_to_host(_dom0, aExaBoxCluCtrlObj.mGetCtx()) as _node:
                _node.mExecuteCmd('/bin/rpm -qa')
                _ret = _node.mGetCmdExitStatus()
                if(_ret != 0):
                    ebLogWarn('The RPM database is corrupt. Now Rebuilding it')
                    _node.mExecuteCmd('/bin/rpm -vv --rebuilddb')
                    _rebuild_ret = _node.mGetCmdExitStatus()
                    if(_rebuild_ret == 0):
                        _node.mExecuteCmd('/bin/rpm -qa')
                        _rpm_ret = _node.mGetCmdExitStatus()
                        if(_rpm_ret == 0):
                            ebLogInfo('Rebuilding and Querying the RPM database is successful')
                        else:
                            _msg = f'RPM database Query Command failed on {_dom0}'
                            ebLogError(_msg)
                            raise ExacloudRuntimeError(0x391, 0xA, _msg)
                    else:
                        _msg = f'RPM database is corrupt. RPM database Rebuild command failed on {_dom0}'
                        ebLogError(_msg)
                        raise ExacloudRuntimeError(0x391, 0xA, _msg)
                else:
                    ebLogInfo('RPM database Precheck Passed')

    def mDetectAndRemoveStaleBondethInterface(self, aExaBoxCluCtrlObj):

        for _dom0, _domU in aExaBoxCluCtrlObj.mReturnDom0DomUPair():
            with connect_to_host(_dom0, aExaBoxCluCtrlObj.mGetCtx()) as _node:

                _bondMaster = '/sys/class/net/bonding_masters'

                _ls = node_cmd_abs_path_check(_node, "ls", sbin=True)
                _cmd = f'{_ls} /proc/net/bonding/bondeth*'
                _ret, _out, _err = node_exec_cmd(_node, _cmd, log_warning=True, log_stdout_on_error=True)
                if _ret:
                    _msg = f'The {_cmd} failed on dom0: {_dom0}. Stdout is: {_out}, Stderr is: {_err}'
                    ebLogWarn(_msg)
                    return

                _entries = _out.strip().split('\n')
                for _line in _entries:
                    _bridgeName = _line.split('/')[-1]
                    if (_bridgeName != 'bondeth0'):
                        msg = f'Invalid bond for bridge {_bridgeName} has been detected on host {_dom0}'
                        ebLogError(msg)

                        _rm = node_cmd_abs_path_check(_node, "rm", sbin=True)

                        _cmd = f'{_ls} /etc/exadata/ovm/bridge.conf.d/*.{_bridgeName}.*.xml'
                        _ret, _out, _err = node_exec_cmd(_node, _cmd, log_warning=True, log_stdout_on_error=True)
                        if _ret == 0:
                            _confEntries = _out.strip().split('\n')
                            for _conf in _confEntries:
                                _cmd = f'{_rm} -rf {_conf}'
                                ebLogTrace('*** Running command: ' + _cmd)
                                _node.mExecuteCmdLog(_cmd)

                        _ip = node_cmd_abs_path_check(_node, "ip", sbin=True)
                        _cmd = f'/usr/sbin/vm_maker --remove-bridge vm{_bridgeName} --force'
                        ebLogTrace('*** Running command: ' + _cmd)
                        _ret, _out, _err = node_exec_cmd(_node, _cmd, log_warning=True, log_stdout_on_error=True,)
                        if _ret:
                            _cmd = f'{_rm} -rf /etc/sysconfig/network-scripts/ifcfg-vm{_bridgeName}'
                            ebLogTrace('*** Running command: ' + _cmd)
                            _node.mExecuteCmdLog(_cmd)

                            _cmd = f'{_ip} link delete vm{_bridgeName}'
                            ebLogTrace('*** Running command: ' + _cmd)
                            _node.mExecuteCmdLog(_cmd)

                        _cmd = f'{_rm} -rf /etc/sysconfig/network-scripts/ifcfg-{_bridgeName}'
                        ebLogTrace('*** Running command: ' + _cmd)
                        _node.mExecuteCmdLog(_cmd)

                        _cmd = f'{_ip} link delete {_bridgeName}'
                        ebLogTrace('*** Running command: ' + _cmd)
                        _node.mExecuteCmdLog(_cmd)

                        _cat = node_cmd_abs_path_check(_node, "cat", sbin=True)
                        _cmd = f'{_cat} {_bondMaster}'
                        _ret, _out, _err = node_exec_cmd(_node, _cmd, log_warning=True, log_stdout_on_error=True)
                        if _ret == 0:
                            _interfaces = _out.strip().split()
                            ebLogTrace(f'_interfaces = {_interfaces}')
                            if _bridgeName in _interfaces:
                                _echo = node_cmd_abs_path_check(_node, "echo", sbin=True)
                                _cmd = f'{_echo} "-{_bridgeName}" > {_bondMaster}'
                                ebLogTrace('*** Running command: ' + _cmd)
                                _node.mExecuteCmdLog(_cmd)

                        _cmd = f'{_rm} -rf {_line}'
                        ebLogTrace('*** Running command: ' + _cmd)
                        _node.mExecuteCmdLog(_cmd)

    def mDetectAndRemoveStaleVMdirs(self, aExaBoxCluCtrlObj):

        for _dom0,_domU in aExaBoxCluCtrlObj.mReturnDom0DomUPair():
            with connect_to_host(_dom0, aExaBoxCluCtrlObj.mGetCtx()) as _node:

                _all_domain_list = []
                _libvirt_domain_xml_list = []
                _domain_on_disk_list = []
                _domain_on_disk_list1 = []
                _stale_domain_list = []


                _cmd = f"/bin/ls /EXAVMIMAGES/GuestImages"
                ebLogTrace('*** Running command: ' + _cmd)
                _, _o, _e = _node.mExecuteCmd(_cmd)
                _out = _o.read().strip()
                _err = _e.read().strip()
                _msg = f'Stdout is:{_out}, Stderr is:{_err}'
                ebLogTrace(_msg)
                if _node.mGetCmdExitStatus():
                    _msg = f'csPreVMChecks: {_cmd} command failed on dom0: {_dom0}.\nStdout is:\n{_out}\nStderr is:\n{_err}\n'
                    ebLogWarn(_msg)
                    return
                else:
                    _domain_on_disk_list = _out.split('\n')
                    ebLogInfo(f'csPreVMChecks: Domains on disk on dom0: {_dom0} are {_domain_on_disk_list}')


                _cmd = f"/usr/bin/virsh list --all --name"
                ebLogTrace('*** Running command: ' + _cmd)
                _, _o, _e = _node.mExecuteCmd(_cmd)
                _out = _o.read().strip()
                _err = _e.read().strip()
                if _node.mGetCmdExitStatus():
                    _msg = f'csPreVMChecks: {_cmd} command failed on dom0: {_dom0}.\nStdout is:\n{_out}\nStderr is:\n{_err}\n'
                    ebLogWarn(_msg)
                    return
                else:
                    _all_domain_list = _out.split('\n')
                    ebLogInfo(f'csPreVMChecks: All VM domains on dom0: {_dom0} are {_all_domain_list}')


                _cmd = f"/bin/ls /etc/libvirt/qemu/*.xml"
                ebLogTrace('*** Running command: ' + _cmd)
                _, _o, _e = _node.mExecuteCmd(_cmd)
                _out = _o.read().strip()
                _err = _e.read().strip()
                if _node.mGetCmdExitStatus():
                    _msg = f'csPreVMChecks: {_cmd} command failed on dom0: {_dom0}.\nStdout is:\n{_out}\nStderr is:\n{_err}\n'
                    ebLogWarn(_msg)
                    return
                else:
                    _out = _out.split('\n')
                    _libvirt_domain_xml_list = [line.split('/')[-1] for line in _out if line.split('/')[-1]]
                    ebLogInfo(f'csPreVMChecks: All domain libvirt xml files on dom0: {_dom0} are {_libvirt_domain_xml_list}')


                if _domain_on_disk_list and _all_domain_list and _libvirt_domain_xml_list:
                    for _domain in _domain_on_disk_list:
                        if _domain not in _all_domain_list and f'{_domain}.xml' not in _libvirt_domain_xml_list:
                            if  _domain.strip() == '' :
                                ebLogWarn("*** Skipping empty domain. ***")
                            else:
                                _stale_domain_list.append(_domain)
                    ebLogInfo(f'csPreVMChecks: Stale domain list on dom0: {_dom0} are {_stale_domain_list}')


                if _stale_domain_list:
                    for _stale_domain in _stale_domain_list:

                        # If vm_maker is running for a given guest
                        # we don't check
                        # anything to avoid interferring with
                        # a possible guest creation/removal
                        _list_proc = node_list_process(
                            _node, f"vm_maker.*{_stale_domain}")
                        if _list_proc:
                            ebLogWarn("A vm_maker process was detected in "
                                f"{_dom0} for {_stale_domain}. "
                                f"Skipping undefine/removal for it.")
                            continue

                        _cmd = f"/usr/bin/virsh undefine {_stale_domain}"
                        ebLogTrace('*** Running command: ' + _cmd)
                        _node.mExecuteCmdLog(_cmd)
                        _cmd = f"/usr/bin/rm -rf /EXAVMIMAGES/GuestImages/{_stale_domain}" 
                        ebLogTrace('*** Running command: ' + _cmd)
                        _node.mExecuteCmdLog(_cmd)

    def check_sys_img_version_consistency(self,
        hostnames: Sequence[str],
        ctx: exaBoxContext) -> None:
        """Check all hosts have the same System Image version.

        :param hostnames: list of hostnames to check.
        :param ctx: exaBoxContext to stablish connections to hosts.
        :returns: nothing
        :raises ExacloudRuntimeError: if the check failed or an error occurred.
        """

        def __get_version(host: str) -> str:
            with connect_to_host(host, ctx) as node:
                ret = node_exec_cmd_check(
                    node, '/usr/local/bin/imageinfo -version')

                return ret.stdout.strip()

        try:
            host_versions = {host: __get_version(host) for host in hostnames}
        except Exception as exp:
            msg = f'System Image version check failed: {exp}'
            ebLogError(msg)
            raise ExacloudRuntimeError(0x390, 0xA, msg) from exp

        if len(set(host_versions.values())) > 1:
            # there is at least one host with different system image version
            msg = \
                'System Image version check failed: System Image versions mismatch'
            ebLogError(f'{msg}:\n{host_versions}')
            raise ExacloudRuntimeError(0x390, 0xA, msg)

    def log_cells_pmem_components(self, ebox):
        """
        Logs the name, status and cell disks of the PMEMLOG and PMEMCACHE
        components of the cells, if they include errors, those will be fixed
        during create storage step.

        :param ebox: A clucontrol object.
        """
        for _cell in ebox.mReturnCellNodes():
            with connect_to_host(_cell, ebox.mGetCtx()) as node:
                _pmemlog = ebCluStorageConfig.mListPMEMDetails(node, 'log')
                _pmemcache = ebCluStorageConfig.mListPMEMDetails(node, 'cache')
                ebLogInfo(
                    f"*** Cell {_cell} "
                    f"PMEMCACHE: {_pmemcache.get('name')} "
                    f"status is {_pmemcache.get('status')} "
                    f"with celldisks {_pmemcache.get('cellDisk')} "
                )
                ebLogInfo(
                    f"*** Cell {_cell} "
                    f"PMEMLOG: {_pmemlog.get('name')} "
                    f"status is {_pmemlog.get('status')} "
                    f"with celldisks {_pmemlog.get('cellDisk')} "
                )

    def mChangeForwardAccept(self, ebox):
        """
        Change $iptables_bin -P FORWARD DROP to $iptables_bin -P FORWARD ACCEPT for dev and (x5 or x6) systems
        """
        _iptables_script = "/opt/exacloud/network/dom0_iptables_setup.sh"
        for _dom0, _ in ebox.mReturnDom0DomUPair():
            with connect_to_host(_dom0, get_gcontext()) as _node:
                try:
                    ebLogInfo(f"*** Modifying FORWARD rule on dom0_iptables_setup.sh in Dom0: {_dom0} ***")
                    # Copy dom0_iptables_setup.sh script to dom0s
                    ebLogInfo(f"*** Copying dom0_iptables_setup.sh to Dom0: {_dom0} ***")
                    # Create directory /opt/exacloud/network/ if needed
                    _, _, _e = _node.mExecuteCmd('/bin/mkdir -p /opt/exacloud/network/')
                    _rc = _node.mGetCmdExitStatus()
                    if _rc:
                        ebLogError(f"*** Could not create /opt/exacloud/network/ directory on {_dom0} error:{_e.readlines()} ***")
                    try:
                        _node.mCopyFile('scripts/network/dom0_iptables_setup.sh', '/opt/exacloud/network/dom0_iptables_setup.sh')
                    except Exception as exp:
                        ebLogError(f"Exception occured while copying dom0_iptables_setup.sh to Dom0: {_dom0}. Exception: {str(exp)}")
                        raise
                    ebLogInfo(f"*** File copied to {_dom0} ***")
                    # Replace the line
                    _node.mExecuteCmd("/bin/sed -i 's/\$iptables_bin -P FORWARD DROP$/$iptables_bin -P FORWARD ACCEPT/g' %s"%(_iptables_script))
                    _dom0_script_success = (_node.mGetCmdExitStatus() == 0)
                    if _dom0_script_success:
                        ebLogInfo(f"*** Modified FORWARD rule on dom0_iptables_setup.sh in Dom0 to ACCEPT successfully: {_dom0} ***")
                    else:
                        ebLogWarn(f"*** Could not modify FORWARD rule on dom0_iptables_setup.sh in Dom0 to ACCEPT: {_dom0} ***")
                except Exception as ex:
                    ebLogError(f"Exception occured while modifying FORWARD rule in Dom0 {_dom0}. Exception: {str(ex)}")
                    raise

    def mCopyVifFiles(self, ebox):
        """
        Copy vif EBT files to dom0 and link them for dev pdit clusters and x5/x6 systems
        This part of code is copied from mSetupEbtablesOnDom0 method in clucontrol.py
        """
        if ebox.mIsKVM():
            ebLogInfo("*** KVM environment detected - Not copying vif files. ***")
            return
        if ebox.mIsOciEXACC():
            ebLogInfo("*** ExaCC environment detected - Not copying vif files. ***")
            return
        _dpairs = ebox.mReturnDom0DomUPair()
        _ebt_wl_script = '/etc/xen/scripts/vif-bridge'
        _ebt_wl_script_cmn = '/etc/xen/scripts/vif-common.sh'
        _ebt_wl_script_orig = _ebt_wl_script+'.ORIG'
        _ebt_wl_script_cmn_orig = _ebt_wl_script_cmn+'.ORIG'
        _ebt_wl_script_ebt  = _ebt_wl_script+'.EBT'
        _ebt_wl_script_cmn_ebt  = _ebt_wl_script_cmn+'.EBT'

        for _dom0, _ in _dpairs:
            with connect_to_host(_dom0, get_gcontext()) as _node:
                try:
                    _cmdstr = ''
                    if not _node.mFileExists(_ebt_wl_script_ebt):
                        _node.mCopyFile('scripts/network/vif-bridge', _ebt_wl_script_ebt)
                        _node.mCopyFile('scripts/network/vif-common.sh', _ebt_wl_script_cmn_ebt)
                        _cmdstr = _cmdstr + '/bin/cp -f '+_ebt_wl_script+' '+_ebt_wl_script_orig + ' ; /bin/chmod 755 ' + _ebt_wl_script_ebt + " ; "
                        _cmdstr = _cmdstr + '/bin/cp -f '+_ebt_wl_script_cmn+' '+_ebt_wl_script_cmn_orig + ' ; /bin/chmod 755 ' + _ebt_wl_script_cmn_ebt + " ; "
                        ebLogInfo('*** Installing ebtables vif-bridge')
                    else:
                        # BUG: 22114518 - overwrite existing vif-bridge script with newer version
                        _node.mCopyFile('scripts/network/vif-bridge', _ebt_wl_script_ebt)
                        _node.mCopyFile('scripts/network/vif-common.sh', _ebt_wl_script_cmn_ebt)
                        ebLogInfo('*** ebtables vif-bridge already installed (update done to latest release)')
                    _cmdstr = _cmdstr + '/bin/ln -sf '+_ebt_wl_script_ebt+' '+ _ebt_wl_script + " ; "
                    _cmdstr = _cmdstr + '/bin/chmod 755 ' + _ebt_wl_script_cmn_ebt + ' ; /bin/ln -sf '+_ebt_wl_script_cmn_ebt+' '+ _ebt_wl_script_cmn + " ; "

                    _node.mExecuteCmdLog(_cmdstr)
                    if _node.mGetCmdExitStatus():
                        raise Exception(f"*** Could not copy/link vif files in Dom0: {_dom0} ***", _node.mGetHostname(), _cmdstr)
                except Exception as ex:
                    ebLogError(f"Exception occured while copying/linking vif files in Dom0: {_dom0}. Exception: {str(ex)}")
                    raise

    def mPostVMDeleteSteps(self, aExaBoxCluCtrlObj, aOptions, aStepList):
        ebLogInfo("csPreVMSetup: Entering mPostVMDeleteSteps")

        _ebox = aExaBoxCluCtrlObj
        steplist = aStepList
        _csu = csUtil()

        #
        # Delete VMBackups of the VM for this cluster
        #
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Delete VMBackups from Dom0')
        _vmbkupobj = ebCluManageVMBackup(_ebox)

        # Delete local and OSS non-golden VMBackups of the VM for this cluster
        _vmbkupobj.mCleanVMbackup(aOptions, _ebox.mReturnDom0DomUPair(), aCleanGoldBackup=False)
        _vmbackup_data = _vmbkupobj.mGetVMBackupData()
        if _vmbackup_data['Exacloud Cmd Status'] == _vmbkupobj.FAIL:
            ebLogWarn(f"Failed to delete vmbackups for the current cluster. Reason: {_vmbackup_data['Log']}")
        else:
            ebLogInfo("Successfully deleted all vmbackups for the current cluster")

        # Clean Golden backups in OCI (Golden backups are never kept locally in the dom0)
        _vmbkupobj.mCleanVMbackup(aOptions, _ebox.mReturnDom0DomUPair(), aCleanGoldBackup=True)
        _vmbackup_data = _vmbkupobj.mGetVMBackupData()
        if _vmbackup_data['Exacloud Cmd Status'] == _vmbkupobj.FAIL:
            ebLogWarn(f"Failed to delete golden vmbackups for the current cluster. Reason: {_vmbackup_data['Log']}")
        else:
            ebLogInfo("Successfully deleted all golden vmbackups for the current cluster")

        # Remove VMbackup Json
        _utils = _ebox.mGetExascaleUtils()
        _utils.mRemoveVMbackupJson(aOptions)

        _ebox.mLogStepElapsedTime(_step_time, 'Delete VMBackups from Dom0')


        #
        # Delete VMBackup bucket for this cluster
        #
        if ebVMBackupOCI.mIsVMBOSSEnabled(aOptions):

            # Depending on OCI region we'll need to copy certificates and/or update
            # endpoints in the remote vmbackup.conf
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Delete Cluster vmbackup level bucket')
            _vmbackup_oci_mgr = ebVMBackupOCI(aOptions)
            _vmbackup_oci_mgr.mDeleteVMBackupClusterBucket()
            _ebox.mLogStepElapsedTime(_step_time, 'Delete Cluster vmbackup level bucket')

            # Trigger an osslist with reload to gurantee we have an
            # up to date cache file
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, steplist, aComment='VMBackup Osslist reload')
            _vmbkupobj.mListOSSVMbackup(aOptions, aReload=True)
            _ebox.mLogStepElapsedTime(_step_time, 'VMBackup Osslist reload')

        for _dom0, _domU in _ebox.mReturnDom0DomUPair():
            with connect_to_host(_dom0, get_gcontext(), username="root") as _node:
                ebLogInfo(f"Cleanup vmbackup logs for {_domU}")
                _node.mExecuteCmdLog(f"rm /opt/oracle/vmbackup/log/vmbackup_{_domU.split('.')[0]}.log")
        #
        # Check if Cell services are running
        #
        _cells_services_up = True
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Running cell services checks')
        if not _ebox.mIsXS() and not _ebox.mCheckCellsServicesUp():
            ebLogWarn('*** Cell services are still down after one restart attempt ***')
            _cells_services_up = False
        _ebox.mLogStepElapsedTime(_step_time, 'Running cell services check')

        #
        # Grid Disk Force Delete (Griddisks drop is supported on SVM and MVM, CellSecureShredding has logic to
        # run only on supported scenarios internally (Exascale, singleVM or last cluster of MVM...)
        # Should not be run on Exascale
        #
        if _cells_services_up and not _ebox.mIsExaScale() and not _ebox.mIsXS():
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Running Delete Force Grid Disks POSTVM')
            if _ebox.mGetStorage().mCheckGridDisks():
                if _ebox.mGetStorage().mDeleteForceGridDisks():
                    ebLogInfo("Griddisks of the cells in this cluster are deleted. Secure cell shredding will be performed during infra delete.")
                else:
                    _err_msg = ("Exacloud was not able to delete all the GridDisks of the cells "
                        "in this cluster being deleted")
                    _action_msg = ("Review the Exacloud errors above in this log, if a Cell has an "
                        "issue that prevents GridDisks deletion please fix it, then attempt this "
                        "step again")
                    ebLogCritical(_err_msg, _action_msg)
                    raise ExacloudRuntimeError(0x407, 0xA, _err_msg)
            _ebox.mLogStepElapsedTime(_step_time, 'Running Delete Force Grid Disks POSTVM')

        #
        # Reset storage vlan for Cells (Only for KVM ROCE single VM)
        #
        if _ebox.mIsKVM() and _ebox.mIsExabm() and not _ebox.SharedEnv():
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Reset storage vlan for Cells')
            _ebox.mRestoreStorageVlan(_ebox.mReturnCellNodes())
            _ebox.mLogStepElapsedTime(_step_time, 'Reset storage vlan for Cells')

            #
            # Drop all the celldisks from the cells
            # IMPORTANT: Execute this after restoring the stre0/1 vlanID in the cells
            # Reason: BUG 33993510
            #
            if not _ebox.mIsExaScale() and not _ebox.mIsXS():
                _step_time = time.time()
                _ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Drop all the celldisks in the Cells')
                _ebox.mGetStorage().mDropCellDisks(_ebox.mReturnCellNodes())
                _ebox.mLogStepElapsedTime(_step_time, 'Drop all the celldisks in the Cells')

        #
        # Remove ClusterConfiguration from Dom0s
        #
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Remove Cluster Configuration')
        _ebox.mRemoveClusterConfiguration()
        _ebox.mLogStepElapsedTime(_step_time, 'Remove Cluster Configuration')
        #
        # Update request status
        #
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Running External POSTVM Scripts')
        _ebox.mRunScript(aType='*',aWhen='post.vm_delete')
        _ebox.mLogStepElapsedTime(_step_time, 'Running External POSTVM Scripts')
        #
        # Remove ebtables whitelist if present
        #
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Remove and flush ebtables from Dom0')
        _ebox.mSetupEbtablesOnDom0(aMode=False)
        _ebox.mLogStepElapsedTime(_step_time, 'Remove and flush ebtables from Dom0')

        #
        # Remove the VM related NFTables rules
        #
        if _ebox.mIsExabm() and _ebox.mIsKVM():
            _nftDom0s = _ebox.mGetHostsByTypeAndOLVersion(ExaKmsHostType.DOM0, ["OL8"])
            if _nftDom0s:
                ebIpTablesRoCE.mRemoveSecurityRulesExaBM(_ebox, aDom0s=_nftDom0s)

        for _dom0, _domU in _ebox.mReturnDom0DomUPair():
            _myfilename = '/opt/exacloud/network/vif-all-client-ips' + "." + _domU
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_dom0)
            _node.mExecuteCmd('rm -f %s 2>/dev/null' % _myfilename)
            if _ebox.mIsOciEXACC():
                ebExaCCAtpFiltering.sCleanupDom0EBtables(_node, _domU)
            
            _node.mDisconnect()
        #
        # Reset IORM DB Plan
        #
        if not _ebox.mIsXS() and not _ebox.SharedEnv():
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Resetting IORM DB Plan')
            _ioptions = aOptions
            _ioptions.resmanage = "resetdbplan"
            _iormobj = ebCluResManager(_ebox, _ioptions)
            _iormobj.mClusterIorm(_ioptions)
            _ebox.mLogStepElapsedTime(_step_time, 'Resetting IORM DB Plan')
        #
        # Delete Pkey Cell
        #
        if not _ebox.mIsXS():
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Delete PKey Cell')
            _ebox.mDeletePKeyCell()
            if _ebox.mIsExabm() and not _ebox.mGetSharedEnv() and not _ebox.mIsKVM():
                ebCluManageStorage.mEnsureEmptyXenCellsInterconnect(_ebox.mReturnCellNodes())
            _ebox.mLogStepElapsedTime(_step_time, 'Delete PKey Cell')

        #
        # Delete DomU keys KMS
        #
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Delete DomU keys KMS')
        _ebox.mRemoveSshKeys()
        _ebox.mLogStepElapsedTime(_step_time, 'Delete DomU keys KMS')

        #delete ADB-S marker files if exists from Dom0s
        _ebox.mDeleteVnumaMarker()

        if not _ebox.mIsXS() and _ebox.IsZdlraHThread() is False:
            _ebox.mGetZDLRA().mEnableDisableHT("Enabled", aOptions)
        #
        # PRE-VM Delete remote luks devices passphrase and keyapi shell wrapper from the dom0s
        #
        if isEncryptionRequested(aOptions, 'domU') and not _ebox.mIsOciEXACC():

            # Delete the Remote passphrase from SiV only if local passphrase is not
            # enabled. This is regardless of KVM or XEN
            if not useLocalPassphrase():
                _step_time = time.time()
                _ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Delete remote luks devices passphrase')
                _domu_list = [ _domu for _ , _domu in _ebox.mReturnDom0DomUPair()]
                deleteRemotePassphraseSetup(aOptions, _domu_list)
                _ebox.mLogStepElapsedTime(_step_time, 'Delete remote luks devices passphrase')

            # On KVM we use OEDA to handle Filesystem Encryption. To accomplish
            # this Exacloud copies one shell wrapper to the Dom0s during the Create
            # service. This file is used by OEDA on Step2 to create the VMs.
            # This is to make sure we delete the keyapi corresponding to this cluster
            if _ebox.mIsKVM():
                _step_time = time.time()
                _ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Delete keyapi from Dom0s')
                _dom0_list = [ _dom0 for _dom0 , _ in _ebox.mReturnDom0DomUPair()]
                deleteOEDAKeyApiFromDom0(_ebox, _dom0_list)
                _ebox.mLogStepElapsedTime(_step_time, 'Delete keyapi from Dom0s')

            # Delete Marker file for Encryption
            _ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Delete crypto luks marker file')
            for _dom0, _domU in _ebox.mReturnDom0DomUPair():
                deleteEncryptionMarkerFileForVM(_dom0, _domU)
            _ebox.mLogStepElapsedTime(_step_time, 'Delete crypto luks marker file')

        # 
        # PRE-VM Delete ExaKMSDB luks passphrase for ExaCC
        #
        if exacc_fsencryption_requested(aOptions) and _ebox.mIsOciEXACC():
            _ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Delete ExaKMSDB luks passphrase for ExaCC')
            for _, _domU in _ebox.mReturnDom0DomUPair():
                exacc_del_fsencryption_passphrase(_domU)
            _ebox.mLogStepElapsedTime(_step_time, 'Delete ExaKMSDB luks passphrase for ExaCC')

            # Delete Marker file for Encryption
            _ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Delete crypto luks marker file')
            for _dom0, _domU in _ebox.mReturnDom0DomUPair():
                deleteEncryptionMarkerFileForVM(_dom0, _domU)
            _ebox.mLogStepElapsedTime(_step_time, 'Delete crypto luks marker file')

        # Ensure bonded-bridge remains configured after cleanup.
        #
        # This operation is only required if static bonded-bridge creation is
        # not supported in the cluster.
        if not clubonding.is_static_monitoring_bridge_supported(
                aExaBoxCluCtrlObj, payload=aOptions.jsonconf):
            clubonding.configure_bonding_if_enabled(
                aExaBoxCluCtrlObj, payload=aOptions.jsonconf,
                configure_bridge=True, configure_monitor=False)

        #
        # Delete nat-rules file to support NAT RULES recreation via dom0_iptables_setup.sh script
        #
        _ebox.mDeleteNatIptablesRulesFile()

        #
        # Remove Storage Pool from libvirt definition on the dom0s
        #
        if _ebox.mIsKVM() and _ebox.mCheckConfigOption('remove_storage_pool','True'):
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Remove Storage Pool from libvirt definition on dom0s')
            _csu.mRemoveStoragePool(_ebox)
            _ebox.mLogStepElapsedTime(_step_time, 'Remove Storage Pool from libvirt definition on dom0s')

        ebLogInfo("csPreVMSetup: Completed mPostVMDeleteSteps")
        ebLogInfo('*** Exacloud Operation Successful : Delete Service completed')

    def mGetCellinitIP(self,_node, aHostType):
        """
        mGetCellinitIP() function retrieves the IPs of DomUs and cells from cellinit.ora.
        Returns:
            list: list of IPs from cellinit.ora file
        """
        _cell_init_ip = []

        if aHostType == "DOMU":

            _find_cmd = node_cmd_abs_path_check(node=_node, cmd="find")
            _cmd_str = f"{_find_cmd} /etc -name cellinit.ora"
            _i, _o, _e = _node.mExecuteCmd(_cmd_str)
            _output = [_line.strip() for _line in _o.readlines()]
            if _output:
                for _path in _output:
                    _cmd_str = f"/bin/grep -E 'ipaddress1|ipaddress2' {_path}"
                    _i, _o, _e = _node.mExecuteCmd(_cmd_str)
                    _op = [_line.strip() for _line in _o.readlines()]
                    if _op:
                        ebLogInfo(f"Cellinit.ora file from which IPs are retrieved: {_path}")
                        for _line in _op:
                            _name, _addr = _line.split('=')
                            _cell_init_ip.append(_addr.split('/')[0])
                        break

        else:

            _cmd_str = f"cellcli -e 'list cell attributes ipaddress1'"
            _, _o, _e = _node.mExecuteCmd(_cmd_str)
            _output = _o.read().strip()

            if _output:
                _cell_init_ip.append(_output.split('/')[0])

            _cmd_str = f"cellcli -e 'list cell attributes ipaddress2'"
            _, _o, _e = _node.mExecuteCmd(_cmd_str)
            _output = _o.read().strip()

            if _output:
                _cell_init_ip.append(_output.split('/')[0])


        ebLogTrace(f" IPs of host {_node.mGetHostname()} from cellinit.ora  : {_cell_init_ip}")
        return _cell_init_ip

    def mGetIfaceAdress(self, aInt, _node):
        """
        mGetIfaceAdress() retrieves interface IP as per the interface name passed as the parameter.
        Args:
            aInt: Interface name
            _node: Node
        Returns:
            string: _ip_addr
        """
        _ip_bin = node_cmd_abs_path_check(node=_node, cmd="ip", sbin=True)
        _iface = aInt
        _ip_addr = ""
        _cmd_str = _ip_bin + " addr show dev " + _iface + " | /bin/grep 'inet' | /bin/cut -d: -f2 | /bin/awk '{print $2}' "
        _i, _o, _e = _node.mExecuteCmd(_cmd_str)
        _output = [_line.strip() for _line in _o.readlines()]
        if _output:
            _ip_addr = _output[0].split('/')[0]

        return _ip_addr

    def getAllPrivateIPs(self, _host_list,_ebox):
        """
        getAllPrivateIPs() function retrieves all private IPs of the host from XML.
        Args:
            _host_list (list): list of domUs or cells to retrieve the XML IPs
            _ebox: aExaBoxCluCtrlObj
        Returns:
            list: list of private IPs from XML
        """
        _IPList = []
        for _host in _host_list:
            _host_mac = _ebox.mGetMachines().mGetMachineConfig(_host)
            if _host_mac is None:
                ebLogError(f'*** failed to retrieve machine config for {_host}')
            _host_net_list = _host_mac.mGetMacNetworks()
            for _net in _host_net_list:
                _netcnf = _ebox.mGetNetworks().mGetNetworkConfig(_net)
                if _netcnf.mGetNetType() in [ 'private' ]:
                    _IPList.append(_netcnf.mGetNetIpAddr())
        return _IPList
    
    def mGetIfaceIP(self, _node, _ebox, _iface_type):
        """
        mGetIfaceIP function retrieves the cluster interface IPs of domUs and storage interface IPs of DomUs and cells. 
        It gets the respective interface names and fetches the corresponding IPs of that interface by invoking mGetIfaceAdress() function
        which internally runs ip addr show dev <iface> | grep 'inet' | cut -d: -f2 | awk '{print $2}' command.
        Args:
            _node: _description_
            _ebox: aExaBoxCluCtrlObj
            _iface_type: String to specify Cluster or Storage interface
        Returns:
            strings: _ip_addr1, _ip_addr2
        """
        _ifaceList = []
        _includes = ()
        _excludes = ()
        if _iface_type == "cluster":
            _includes = ('clre0', 'clre1','clib0','clib1')
            _excludes = ('stre0', 'stre1','stib0', 'stib1')
        elif _iface_type == "storage":
            if _ebox.mIsKVM():
                _includes = ('stre0', 'stre1', 're0', 're1')
            else:
                _includes = ('stib0', 'stib1')
            _excludes = ('clre0','clre1','clib0','clib1')
            
        _ls_cmd = node_cmd_abs_path_check(node=_node, cmd="ls")
        _cmd_str = f"{_ls_cmd} /etc/sysconfig/network-scripts/ifcfg-*"
        _i, _o, _e = _node.mExecuteCmd(_cmd_str)
        _output = [_line.strip() for _line in _o.readlines()]
        
        if _output:
            for _intf in _output:
                if _intf.endswith(_includes) and not _intf.endswith(_excludes):
                    _ifaceList.append(_intf.split('-')[-1])
        ebLogTrace(f"{_iface_type} interface list for host {_node.mGetHostname()}  : {_ifaceList}")
        _ip_addr1=None
        _ip_addr2=None
        if len(_ifaceList) == 2:
            _ip_addr1 = self.mGetIfaceAdress(f"{_ifaceList[0]}",_node)
            _ip_addr2 = self.mGetIfaceAdress(f"{_ifaceList[1]}",_node)
            ebLogTrace(f"{_iface_type} interface IP1 for host {_node.mGetHostname()}  : {_ip_addr1}")
            ebLogTrace(f"{_iface_type} interface IP2 for host {_node.mGetHostname()}  : {_ip_addr2}")

        else:
            ebLogWarn(f"Could not find the required {_iface_type} interfaces for host {_node.mGetHostname()}")
        return _ip_addr1, _ip_addr2

    def getIPDict(self,_ebox,_host,_IPDict,_iptype,_cellinitIP, aHostType):
        """
        Function to get cluster interface IPs for DomUs and storage interface IPs of DomUs and cells according to the _iptype. 
        This function also populates the cellinitIP list for DomUs and cells, if the _iptype is storage_interface.
        Args:
            _ebox: aExaBoxCluCtrlObj
            _host: domU or cell
            _IPDict: Dictionary to store IPs of hosts
            _iptype: string to specify cluster or storage interface
            _cellinitIP: list to store cellinit.ora IPs for storage interface
        """
        _IPDict[_host] = {}
        _node = exaBoxNode(get_gcontext())
        with connect_to_host(_host, get_gcontext(), "root") as _node:
            if _iptype=="cluster_interface":
                _ipaddr1, _ipaddr2 = self.mGetIfaceIP(_node,_ebox,"cluster")
                
            elif _iptype=="storage_interface": 
                _ipaddr1, _ipaddr2 = self.mGetIfaceIP(_node,_ebox,"storage")
                _cellinitIP.extend(self.mGetCellinitIP(_node, aHostType))
            if not _ipaddr1 or not _ipaddr2:
                raise Exception(f"Failed to retrieve interface IPs for {_host}")
            _IPDict[_host]["IP1"] = _ipaddr1
            _IPDict[_host]["IP2"] = _ipaddr2
  
    def mVerifyIPs(self,_IPdict, _IP_list, _IP_list_name):
        """The function mVerifyIPs is a generic function which takes in a dictionary, list and a string as parameters and checks if the dictionary items are present in the list or not.
        This is for verifying if the IPs retrieved from various sources (IPs retrieved by running ip command on the respective interfaces, private IPs from the XML, IPs from cellinit.ora) are the same or not.
        If IP mismatch is present, the RDS ping cannot continue.
        Args:
            _IPdict: The dictionary of IPs formed for cluster and storage interfaces of DomUs and cells respectively
            _IP_list: The list of IPs formed from XML and cellinit.ora
            _IP_list_name: This just describes the type of list passed in _IP_list, either XML or cellinit.ora. This is for logging info.
        Raises:
            Exception: if IP mismatch occurs.
        """
        for _ip in [_ip for _src in _IPdict for _ip in _IPdict[_src].values()]:
            if _ip in _IP_list:
                continue
            else:
                _err_str = f"IP: {_ip} mismatch with {_IP_list_name}/{_IP_list}"
                ebLogError(_err_str)
                raise Exception(_err_str)
                    
    def executeRDSPing(self,_src_IP, _target_IP,_node,_target):
        _cmd = f"/bin/rds-ping -c 3 -I {_src_IP} {_target_IP}"
        _, _o, _e = _node.mExecuteCmd(_cmd)
        if _o:
            _output = [_line.strip() for _line in _o.readlines()]
            ebLogTrace("output from rds-ping:")
            ebLogTrace(_output)
        
        _rc = _node.mGetCmdExitStatus()
        if _rc:
            if _e:
                _error = [_line.strip() for _line in _e.readlines()]
                ebLogTrace("error from rds-ping:")
                ebLogTrace(_error)
            raise Exception(f"{_cmd} failed to execute from {_node.mGetHostname()} to {_target}")
        ebLogTrace(f"rds ping command {_cmd} success from {_node.mGetHostname()} to {_target}")

    def rdsPing(self,_srcIPDict,_targetIPDict,_skip_str_interface_domu):
        """
        rdsPing() invokes executeRDSPing() with the src and target IPs. 
        For storage interface IPs of domU, the rds ping is skipped.
        Args:
            _srcIPDict: Dictionary of source IP for RDS ping
            _targetIPDict: Dictionary of target IP for RDS ping
            _skip_str_interface_domu (Bool): Set to False, if Storage interface IPs of DomU are passed. This is to skip rds ping between storage interface IPs of domUs.
        """
        try:
            for _src in _srcIPDict:
                _node = exaBoxNode(get_gcontext(), Cluctrl = self)
                _node.mConnect(aHost=_src)
                for _target in _targetIPDict:
                    if _skip_str_interface_domu == True and _src==_target:
                        continue
                    elif _src==_target:
                        self.executeRDSPing(_srcIPDict[_src]['IP1'],_targetIPDict[_target]['IP2'],_node,_target)
                        self.executeRDSPing(_srcIPDict[_src]['IP2'],_targetIPDict[_target]['IP1'],_node,_target)
                    else:
                        self.executeRDSPing(_srcIPDict[_src]['IP1'],_targetIPDict[_target]['IP1'],_node,_target)
                        self.executeRDSPing(_srcIPDict[_src]['IP1'],_targetIPDict[_target]['IP2'],_node,_target)
                        self.executeRDSPing(_srcIPDict[_src]['IP2'],_targetIPDict[_target]['IP1'],_node,_target)
                        self.executeRDSPing(_srcIPDict[_src]['IP2'],_targetIPDict[_target]['IP2'],_node,_target)
        except Exception as e:
            raise Exception(f"Exception in rdsPing(): {str(e)}")
        finally:
            _node.mDisconnect()

    def rdsPingDriver(self,aExaBoxCluCtrlObj):
        _ebox = aExaBoxCluCtrlObj
        _val = _ebox.mCheckConfigOption("exacloud_precheck_install_cluster", "True")
        ebLogInfo(f"Value of ebox.mCheckConfigOption('exacloud_precheck_install_cluster', 'True') : {_val}")
        try:
            ebLogInfo("Collecting IPs for cluster and storage interfaces for domUs and cells")
            _all_domU = list(map(operator.itemgetter(1),_ebox.mReturnDom0DomUPair()))
            domUXML_IPlist = self.getAllPrivateIPs(_all_domU,_ebox)
            ebLogTrace(f"DomU private IP list  for domUs {_all_domU} from xml= {domUXML_IPlist}")
            _all_cells = _ebox.mReturnCellNodes().keys()
            cellXML_IPlist = self.getAllPrivateIPs(_all_cells,_ebox)
            ebLogTrace(f"cells private IP list for cells {_all_cells} from xml= {cellXML_IPlist}")
            _domUClusterIPDict = {}
            _domUStorageIPDict = {}
            _cellStorageIPDict = {}
            _cellinit_IP_cell = []
            _cellinit_IP_domU = []

            for _domU_name in _all_domU:   
                ebLogTrace(f"Running getIPDict for domU : {_domU_name}")
                self.getIPDict(_ebox,_domU_name,_domUClusterIPDict,"cluster_interface",None, "DOMU")
            
            for _domU_name in _all_domU:   
                ebLogTrace(f"Running getIPDict for domU : {_domU_name}")
                self.getIPDict(_ebox,_domU_name,_domUStorageIPDict,"storage_interface",_cellinit_IP_domU, "DOMU")

            for _cell_name in _all_cells:   
                ebLogTrace(f"Running getIPDict for CELL : {_cell_name}")
                self.getIPDict(_ebox,_cell_name,_cellStorageIPDict,"storage_interface",_cellinit_IP_cell, "CELL")

            ebLogTrace(f"cellinit.ora IPs for DomUs {_all_domU} in _cellinit_IP_domU : {_cellinit_IP_domU}")
            ebLogTrace(f"cellinit.ora IPs for cells {_all_cells} in _cellinit_IP_cell : {_cellinit_IP_cell}")
            ebLogTrace(f"Cluster interface IP Dict for DomUs {_all_domU} in _domUClusterIPDict: \n {_domUClusterIPDict}")
            ebLogTrace(f"Storage interface IP Dict for DomUs {_all_domU} in _domUStorageIPDict: \n {_domUStorageIPDict}")
            ebLogTrace(f"Storage interface IP Dict for Cells {_all_cells} in _cellStorageIPDict: \n {_cellStorageIPDict}")
            ebLogInfo("Collecting IPs for cluster and storage interfaces for domUs and cells Successful.")
            ebLogInfo("Proceeding to IP verification")
            self.mVerifyIPs(_domUClusterIPDict,domUXML_IPlist,"XML")
            self.mVerifyIPs(_domUStorageIPDict,domUXML_IPlist,"XML")
            self.mVerifyIPs(_cellStorageIPDict,cellXML_IPlist,"XML")
            self.mVerifyIPs(_domUStorageIPDict,_cellinit_IP_domU,"cellinit.ora")
            self.mVerifyIPs(_cellStorageIPDict,_cellinit_IP_cell,"cellinit.ora")
            ebLogInfo(f"IP verification successful for DomUs {_all_domU} and Cells {_all_cells}")
            ebLogInfo("Proceeding to RDS Ping")
            ebLogInfo("RDS-ping cluster interface between domus:")
            self.rdsPing(_domUClusterIPDict,_domUClusterIPDict,False)
            ebLogInfo("RDS-ping storage interface from domus to cells:")
            self.rdsPing(_domUStorageIPDict,_cellStorageIPDict,True)
            ebLogInfo("RDS-ping storage interface between cells:")
            self.rdsPing(_cellStorageIPDict,_cellStorageIPDict,False)
            ebLogInfo("RDS-ping storage interface from cells to domus:")
            self.rdsPing(_cellStorageIPDict,_domUStorageIPDict,False)
            ebLogInfo("RDS-ping successful")
        except Exception as e:
            _error_str = f"Precheck Exception in rdsPingDriver: {str(e)}"
            ebLogError(f"Precheck Exception in rdsPingDriver: {str(e)}")
            raise ExacloudRuntimeError(0x0390, 0xA,_error_str)

    def mXmlPatchAddVolume(self,aExaBoxCluCtrlObj):
        _ebox = aExaBoxCluCtrlObj
        _oeda_version = _ebox.mGetOedaVersYYMMDD()
        _image_version = ""
        for _dom0, _ in _ebox.mReturnDom0DomUPair():
            _image_version = _ebox.mGetImageVersion(_dom0)
            break
        try:
            ebLogInfo(f"mXmlPatchAddVolume: Xml patch: Add Vol: Image version of {_dom0} is {_image_version}")
            ebLogInfo(f"mXmlPatchAddVolume: Xml patch: Add Vol: OEDA version in YYMMDD is {_oeda_version}")
            addVolumeXmlPatch = False
            _image_version = _image_version.split(".")
            if int(_oeda_version[0:4]) >= 2104:
                if (int(_image_version[0]) == 21 and int(_image_version[1]) >= 1) or int(_image_version[0]) > 21:
                    addVolumeXmlPatch = True

            if addVolumeXmlPatch:
                _oedacli_bin = get_gcontext().mGetOEDAPath() + '/oedacli'
                _oedacli = ebOedacli(_oedacli_bin, "oeda/log", aLogFile="oedacli_add_volume.log")
                _pathU01 = "/u01"
                _size = "20Gb"
                for _, _domU in _ebox.mReturnDom0DomUPair():
                    _domU = _domU.split(".")[0]
                    _oedacli.mAppendCommand(f"ADD VOLUME MOUNTPATH=\"{_pathU01}\" SIZE=\"{_size}\" WHERE HOSTNAME=\"{_domU}\"")
                    _oedacli.mRun(_ebox.mGetRemoteConfig(), _ebox.mGetRemoteConfig())
        except Exception as err:
            _error_str = '*** Fatal ERROR while patching xml while Add volume for u01 - {0}'.format(str(err))
            raise ExacloudRuntimeError(0x0660, 0xA, _error_str,aStackTrace=True,aStep=self.step, aDo=True)

    def mCreateVM(self, aCluCtrlObj, aOptions, aStepList):
        _ebox = aCluCtrlObj
        steplist = aStepList
        _csu = csUtil()
        imageBom = ImageBOM(_ebox)

        _ebox.mUpdateStatus('createservice step '+ self.step)

        if not imageBom.mIsSubStepExecuted(self.step, "KVM_CPU_MANAGE"):
            if _ebox.mIsKVM():
                _valid_modes = ['dg_vmmaker', 'dg_oedacli']
                _cpu_manage_mode = _ebox.mCheckConfigOption('kvm_cpu_manage_mode')

                if _cpu_manage_mode is not None and _cpu_manage_mode in _valid_modes:
                    ebLogInfo('*** Enabling Domaingroup with mode: %s' %_cpu_manage_mode)
                    _exacpueobj = exaBoxKvmDgrpVmkr(self)
                    _exacpueobj.createDG(_ebox)

        # Cleanup Leftover NAT bridge here to allow step to be retried.
        if not imageBom.mIsSubStepExecuted(self.step, "CLEANUP_OLD_PROVISIONING"):
            _ebox.mCleanUpBackupsQemu()
            _ebox.mCleanUpOvsDom0()
            _ebox.mCleanupSingleVMNatBridge()

            #Cleanup Stale serial console connection & directory if exists
            _consoleobj = serialConsole(_ebox, aOptions)
            for _dom0, _domU in _ebox.mReturnDom0DomUPair():
                _consoleobj.mRemoveSSH(_dom0, _domU)

        if not imageBom.mIsSubStepExecuted(self.step, "DELETE_STALE_DUMMY_BRIDGE"):
            if _ebox.mIsKVM():
                #defect 32860518 : EXACC - GEN2: KVM GUESTS: X8M: U01 DISK IMAGE MISSING - OEDA issue-xml patching fix
                self.mXmlPatchAddVolume(_ebox)
                #Clear if any stale bridge exist, before VM Creation,applicable only for kvm

                _grabLock = False
                if _ebox.mCheckConfigOption("skip_dom0_lock_oeda_createvm", "False") or not _ebox.mIsExaScale():
                    _grabLock = True

                if _grabLock:
                    _ebox.mAcquireRemoteLock()

                try:

                    if _ebox.mCheckConfigOption("skip_completely_stale_bridge_removal", "True") and _ebox.mIsExaScale():
                        ebLogInfo("Skip mDeleteStaleDummyBridge")
                    else:
                        _csu.mDeleteStaleDummyBridge(_ebox)

                except Exception as e:
                    raise e
                finally:
                    if _grabLock:
                        _ebox.mReleaseRemoteLock()

        _isclone = aOptions.jsonconf.get("isClone", None)
        # Skip updating system image version in the xml in clone VM (basedb)
        # flow. Otherwise, OEDA - vm_maker uses it to look for the image 
        # ignoring the cloned sys volume passed.
        if not imageBom.mIsSubStepExecuted(self.step, "CHECK_SYSTEM_IMAGE") and (not _isclone or str(_isclone).lower() == "false"):
            #
            # system image check
            #
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Check System Image')

            #
            # PRE-VM Ensure Custom OS is valid, can be downloaded and XML is patched
            #
            _custom_img_ver = hasDomUCustomOS(_ebox)

            # If _custom_img_ver is None, fn mCheckSystemImage will take care.
            with _ebox.remote_lock():
                _ebox.mCheckSystemImage(_custom_img_ver)

            _ebox.mLogStepElapsedTime(_step_time, 'CREATEVM INSTALL : Check System Image completed')


        if not imageBom.mIsSubStepExecuted(self.step, "ENSURE_ENCRYPTED_BOOT"):

            # Ensure Encrypted First Boot exists
            # Create and push luks devices passphrase
            # Patch XML to add encryption tag/section
            if (isEncryptionRequested(aOptions, 'domU') and _ebox.mIsKVM() and
                    get_gcontext().mGetConfigOptions().get(
                        "force_full_guest_encryption", "false").lower() == "true"):

                _step_time = time.time()
                _ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Ensure Encrypted First Boot image exists')
                _dom0_list = [ _dom0 for _dom0 , _ in _ebox.mReturnDom0DomUPair()]
                ensureSystemFirstBootEncryptedExistsParallelSetup(_ebox, _dom0_list)
                _ebox.mLogStepElapsedTime(_step_time, 'Ensure Encrypted First Boot image exists')

                # We Patch the XML to add encryption details (keyapi)
                _ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Patch XML to add encryption tag')
                patchXMLForEncryption(_ebox, _ebox.mGetRemoteConfig())
                _ebox.mLogStepElapsedTime(_step_time, 'Patch XML to add encryption tag')

        if not imageBom.mIsSubStepExecuted(self.step, "CONFIGURE_OEDA_PASS_AND_CONSOLE"):
            #FOR EXACC-HETERO ENV PATCH THE XML WITH CLIENT/BACKUP SLAVES & ENABLE SKIPPASSPROPERTY FLAG
            _ebox.mOEDASkipPassProperty(aOptions)

            # Patch xml with DR Network addition oeda command if it is exacc environment and dr network info
            # is passed in the payload
            if _ebox.mIsOciEXACC():
                _ebox.mUpdateDRNetworkSlaves(aOptions)

            #copy /opt/exacloud/config_info.json to dom0
            _ebox.mConfigureVMConsole(aOptions)

        if not imageBom.mIsSubStepExecuted(self.step, "CONFIGURE_ACCESS_AND_MEMORY"):
            #
            # Setup the temporary iptables for wide open VM traffic
            #
            if _ebox.mIsExabm() and _ebox.mIsKVM():

                _iptDom0s = _ebox.mGetHostsByTypeAndOLVersion(ExaKmsHostType.DOM0, ["OL7", "OL6"])
                if _iptDom0s:
                    ebIpTablesRoCE.mPrevmSetupIptables(_ebox, aDom0s=_iptDom0s)

            #ADD 2T MEMORY SUPPORT
            _model_subType: str = ""
            _inputjson = aOptions.jsonconf
            if _inputjson:
                if ( 'rack' in _inputjson ) and ( 'model_subtype' in _inputjson['rack'] ):
                    _model_subType = str(_inputjson['rack']['model_subtype'])

            if _ebox.mIsKVM() and not _ebox.mIsOciEXACC():
                _enable_2t_support = _ebox.mCheckConfigOption('enable_2t_memory_support')
                if _enable_2t_support == "True" and _model_subType in ["ELASTIC_LARGE", "ELASTIC_EXTRA_LARGE"]:
                    for _dom0, _domU in _ebox.mReturnDom0DomUPair():
                        _exadata_model = _ebox.mGetNodeModel(_dom0)
                        _is_supported = _ebox.mCheck2TMemoryRequirements(_dom0, _model_subType)
                        if not _is_supported:
                            ebLogInfo(f"Dom0 {_dom0} not meeting minumum requirement for 2TB memory")
                            break
                    if _is_supported:
                        _ebox.mAdd2TMemorySupport(aOptions, _exadata_model, _model_subType)
                else:
                    ebLogInfo('*** enable_2t_memory_support flag is False. 2T memory not supported')

        if not imageBom.mIsSubStepExecuted(self.step, "OEDA_STEP"):
            #
            # OEDA CREATE VM
            #
            _grabLock = False
            if _ebox.mCheckConfigOption("skip_dom0_lock_oeda_createvm", "False") or not _ebox.mIsExaScale():
                _grabLock = True

            ebLogInfo(f"Grab Dom0 Lock?: {_grabLock}")
            _isclone = aOptions.jsonconf.get("isClone", None)
            # set REUSEEDVVOLUMEIFEXIST=true in es.properties for clone VM (basedb) request
            if _ebox.isBaseDB() and _isclone and str(_isclone).lower() == "true":
                _oeda_path  = _ebox.mGetOedaPath()
                _oedacli_bin = _oeda_path + '/oedacli'
                _cmd = "alter property name=REUSEEDVVOLUMEIFEXIST value=true"
                _ebox.mExecuteLocal(f"{_oedacli_bin} -e '{_cmd}'")
                
            elif _ebox.isBaseDB() or _ebox.isExacomputeVM():
                _ebox.mGetBaseDB().mUpdateOedaPropertiesInterface()
            _csConstants = _csu.mGetConstants(_ebox, aOptions)
            _csu.mExecuteOEDAStep(_ebox, self.step, steplist, aOedaStep=_csConstants.OSTP_CREATE_VM, dom0Lock=_grabLock)

        #Install Serial Console bits on dom0 if not present (non ExaCC only)
        if not imageBom.mIsSubStepExecuted(self.step, "CONFIGURE_DOCKER_CONSOLE"):
            _consoleobj = serialConsole(_ebox, aOptions)
            if not _ebox.mIsOciEXACC():
                _dom0List = []
                for _dom0 , _ in _ebox.mReturnDom0DomUPair():
                    _OLVersion = _ebox.mGetOLVersion(_dom0)
                    _exists = _consoleobj.mCheckDockerImages(_dom0, _OLVersion)
                    if not _exists:
                        ebLogInfo(f"Install serial console bits on dom0:{_dom0}")
                        _dom0List.append(_dom0)
                if _dom0List:
                    _vmc_dpy = VMConsoleDeploy(_ebox, aOptions)
                    _vmc_dpy.mInstall(_dom0List)

            #Start Containers exa-hippo-serialmux|exa-hippo-sshd for serial Console
            def _restartContainers(_dom0, _domU):
                _consoleobj.mRunContainer(_dom0, _domU)
                _consoleobj.mRestartContainer(_dom0, _domU, aMode="start")

            _plist = ProcessManager()
            for _dom0, _domU in _ebox.mReturnDom0DomUPair():
                _p = ProcessStructure(_restartContainers, [_dom0, _domU,])
                _p.mSetMaxExecutionTime(30*60) #30 minutes timeout
                _p.mSetJoinTimeout(5)
                _p.mSetLogTimeoutFx(ebLogWarn)
                _plist.mStartAppend(_p)

            _plist.mJoinProcess()

        #
        # CREATE-VM Update SSH Keys from OEDA staging area
        #
        if not imageBom.mIsSubStepExecuted(self.step, "SAVE_OEDA_KEYS"):
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Save OEDA SSH Keys')
            _ebox.mSaveOEDASSHKeys(aOptions)

        #
        # CONFIGURE EDV VMBACKUP/LOCAL VMBACKUP
        #
        if not imageBom.mIsSubStepExecuted(self.step, "CONFIGURE_EDV_BACKUP") and not _ebox.isBaseDB() and not _ebox.mIsExaScale():
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Configure EDV Backup')
            _utils = _ebox.mGetExascaleUtils()
            _utils.mConfigureEDVbackup(aOptions)

        #
        # Configure bridge only if static monitoring bridge is not supported.
        if not imageBom.mIsSubStepExecuted(self.step, "RECONFIGURE_BONDING_AND_NETWORK") and not _ebox.isBaseDB() and not _ebox.isExacomputeVM():
            conf_bridge = \
                not clubonding.is_static_monitoring_bridge_supported(
                    _ebox, payload=aOptions.jsonconf)
            clubonding.configure_bonding_if_enabled(
                _ebox, payload=aOptions.jsonconf, configure_bridge=conf_bridge,
                configure_monitor=True)

            _isHetero, _ = _ebox.IsHeteroConfig()
            _ociexacc = _ebox.mIsOciEXACC()
            if _isHetero and _ociexacc:
                ebLogInfo("HETERO ENVIRONMENT DETECTED...")
                ebLogInfo("CONFIGURING DEFAULT GATEWAY TO BONDETH0 ...")
                for _dom0, _domU in _ebox.mReturnDom0DomUPair():
                    _ebox.mConfigureDefaultGateway(_dom0, _domU, aOptions)

            if not _ebox.mCheckConfigOption("_skip_jumbo_frames_config", "True"):
                clujumboframes.configureJumboFrames(_ebox, aOptions.jsonconf)

            #
            # Setup ARP flag onf domus
            #
            _ebox.mSetupArpCheckFlag()

            #
            # Setup ExaCS IPtables in KVM
            #
            if _ebox.mIsExabm() and _ebox.mIsKVM():
                _iptDom0s = _ebox.mGetHostsByTypeAndOLVersion(ExaKmsHostType.DOM0, ["OL7", "OL6"])
                if _iptDom0s:
                    ebIpTablesRoCE.mSetupSecurityRulesExaBM(_ebox, aOptions.jsonconf, aDom0s=_iptDom0s)


            #
            # Perform Postchecks for ip route and dns validation after vm creation
            #

            if _ebox.mIsOciEXACC() and _ebox.mCheckRouterAndDnsAfterVMInstall():
                _error_str = '*** ERROR while performing Postchecks for ip route/dns validation after vm creation'
                raise ExacloudRuntimeError(0x0662, 0xA, _error_str, aStackTrace=True, aStep=self.step, aDo=True)

    def mCreateUser(self, aExaBoxCluCtrlObj, aOptions, aStepList):
        _ebox = aExaBoxCluCtrlObj
        steplist = aStepList
        _csu = csUtil()
        imageBom = ImageBOM(_ebox)

        _ebox.mUpdateStatus('createservice step ' + self.step)

        #
        # Execute OEDA CREATE USER
        #
        if not imageBom.mIsSubStepExecuted(self.step, "OEDA_STEP"):
            _csConstants = _csu.mGetConstants(_ebox, aOptions, False)
            _csu.mExecuteOEDAStep(_ebox, self.step, steplist, aOedaStep=_csConstants.OSTP_CREATE_USER, dom0Lock=False)
        if not imageBom.mIsSubStepExecuted(self.step, "OPC_USER"):

            _opcid = "2000"
            _opcgid = None

            _remapUtil = ebMigrateUsersUtil(_ebox)
            _usrConfig = _remapUtil.mMergeUsersGroupsConfigPayload()

            if "opc" in _usrConfig:
                _opccfg = _usrConfig["opc"]
                if _opccfg:
                    if "uid" in _opccfg:
                        _opcid = str(_opccfg["uid"])
                    if "gid" in _opccfg:
                        _opcgid = str(_opccfg["gid"])

            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Create opc user')
            _ebox.mAddUserDomU("opc", _opcid, aSudoAccess=True, aPasswordLess=True, aGID=_opcgid)
            _ebox.mLogStepElapsedTime(_step_time, 'Create opc user')
        else:
            _ebox.mConfigurePasswordLessDomU("opc")

        if not imageBom.mIsSubStepExecuted(self.step, "SAVE_SSH_KEYS"):
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Saving OEDA SSH Keys')
            _ebox.mSaveOEDASSHKeys()
            _ebox.mRotateVmKeys()
            _ebox.mLogStepElapsedTime(_step_time, 'Saving OEDA SSH Keys')

        if not imageBom.mIsSubStepExecuted(self.step, "PASSWORDLESS"):
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Configure Passwordless All Users')
            _ebox.mConfigurePasswordlessAllUsers()
            _ebox.mLogStepElapsedTime(_step_time, 'Configure Passwordless All Users')

        if not imageBom.mIsSubStepExecuted(self.step, "REMAP_USERS"):
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Remapping Users and Groups IDs')
            _remapUtil = ebMigrateUsersUtil(_ebox)
            _remapUtil.mExecuteRemap()
            _ebox.mLogStepElapsedTime(_step_time, 'Remapping Users and Groups IDs')

        if not imageBom.mIsSubStepExecuted(self.step, "LOCK_DBUSERS"):
            _step_time = time.time()
            _ebox.mUpdateStatusCS(True, self.step, steplist, aComment='Lock dbmadmin/dbmmonitor users')
            _ebox.mLockDBMUsers()
            _ebox.mLogStepElapsedTime(_step_time, 'Lock dbmadmin/dbmmonitor users')

            self.setMemLockDomU(_ebox)

    def mDeleteOpcSSHDirectory(self, aExaBoxCluCtrlObj):
        _ebox = aExaBoxCluCtrlObj
        for _, _domU in _ebox.mReturnDom0DomUPair():
            _node = exaBoxNode(get_gcontext())
            # Ensure host is connectable first
            if not _node.mIsConnectable(aHost=_domU):
                ebLogError(f"Node {_domU} is not connectable. Could not remove /home/opc/.ssh directory during undo step")
                continue
            with connect_to_host(_domU, get_gcontext()) as _node:
                # Remove the .ssh directory during undo of create user step
                _node.mExecuteCmdLog("/bin/rm -rf /home/opc/.ssh")

    def mDeleteVM(self, aExaBoxCluCtrlObj, aOptions, aStepList):
        ebLogVerbose("csCreateVM: Entering mDeleteVM")

        _ebox = aExaBoxCluCtrlObj
        step_list = aStepList
        _oeda_path = _ebox.mGetOedaPath()
        _debug = _ebox.mIsDebug()
        _exabm = _ebox.mIsExabm()
        _ociexacc = _ebox.mIsOciEXACC()
        _remoteconfig = _ebox.mGetRemoteConfig()
        _csu = csUtil()

        _bridges = _csu.mFetchBridges(_ebox)
        
        #
        # VGE: 09 2018 : Reenable OEDA DeleteVM
        #
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, step_list, aComment='Force VM shutdown')
        #
        # Populate final config (new OEDA requirement)
        #
        if not _ebox.mIsKVM():
            _ebox.mCopyFinalVMConfig(_oeda_path)
        else:
            ebLogWarn('*** mCopyFinalVMConfig() not supported on KVM - FIXME')

        # Kill any ongoing start-domain of same domU (bug 31349800)
        _ebox.mKillOngoingStartDomains()
        _ebox.mLogStepElapsedTime(_step_time, 'Force VM shutdown')
        #
        # Try to clean up via OEDA first
        #
        # Option is not in template, setting it to False will revert to old behavior

        _oeda_cleanup_success = False
        if not _ebox.mCheckConfigOption('oeda_vm_delete_step', 'False'):
            try:
                _csConstants = _csu.mGetConstants(_ebox, aOptions)
                _csu.mExecuteOEDAStep(_ebox, self.step, step_list, aOedaStep=_csConstants.OSTP_CREATE_VM, undo=True)
                _oeda_cleanup_success = True
            except:
                ebLogError('*** Delete Virtual Machine (OEDA) returned with errors')

        # Force delete unnamed
        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, self.step, step_list, aComment='Force residual VM deletion')
        _ebox.mForceDeleteDomainUnnamed(aOptions)
        _ebox.mCleanUpReconfig()
        _ebox.mCleanUpStaleVm(_oeda_cleanup_success)

        if _ebox.mCheckConfigOption('min_vm_cycles_reboot') is not None:
            _ebox.mCheckVMCyclesAndReboot()

        _csu.mDeleteBridges(_ebox, _bridges)
        _ebox.mLogStepElapsedTime(_step_time, 'Force residual VM deletion')

        _consoleobj = serialConsole(_ebox, aOptions)
        for _dom0, _domU in _ebox.mReturnDom0DomUPair():
            _consoleobj.mRemoveSSH(_dom0, _domU)
            if _ebox.mIsExaScale():
                mRemoveVMmount(_ebox, _dom0, _domU)

        #
        # Removing libvirt network filters in kvm
        #
        if _exabm and _ebox.mIsKVM():

            _iptDom0s = _ebox.mGetHostsByTypeAndOLVersion(ExaKmsHostType.DOM0, ["OL7", "OL6"])

            if _iptDom0s:
                ebIpTablesRoCE.mRemoveSecurityRulesExaBM(_ebox, aDom0s=_iptDom0s)

        # remove the clustersjson file created for the given cluster
        _ebox.mDeleteClusterDomUList()
        # 31861044
        # Remove DomU-nat entries from /etc/hosts.adbd_domu on delete service
        if _ociexacc:
            ebDNSConfig(aOptions, _ebox.mGetPatchConfig()).mRemoveDNSEntries('guest')

        # For ASM & EXASCALE, Remove EDV Volumes for the GuestVM
        if not _ebox.isBaseDB() and not _ebox.mIsExaScale():
            try:
                _utils = _ebox.mGetExascaleUtils()
                _utils.mRemoveGuestEDVVolumes(aOptions)
                _utils.mRemoveDefaultAcfsVolume(aOptions)
                _utils.mRemoveACFS(aOptions)
            except Exception as e:
                ebLogWarn(f"*** mRemoveGuestEDVVolumes failed with Exception: {str(e)}")

        ebLogVerbose("csCreateVM: Completed mDeleteVM")

    def setMemLockDomU(self, aExaBoxCluCtrlObj):
        ebLogInfo('csCreateUser: Changing memlock to unlimited for all the domUs')
        _ebox = aExaBoxCluCtrlObj
        _node = exaBoxNode(get_gcontext())
        for _,_domU in _ebox.mReturnDom0DomUPair():
            _node.mSetUser('root')
            _node.mConnect(aHost=_domU)
            _cmd1 = "/bin/sed 's/oracle    soft     memlock .*/oracle    soft     memlock     unlimited/g' -i /etc/security/limits.conf; "
            _cmd2 = "/bin/sed 's/oracle    hard     memlock .*/oracle    hard     memlock     unlimited/g' -i /etc/security/limits.conf; "
            _node.mExecuteCmdLog(_cmd1 + _cmd2)
            _node.mDisconnect()

    def mSetDRScanVip(self, aExaBoxCluCtrlObj):
        _dbaascli_short_name = "dbaascli"
        _cmd_dr_vip_scan = f"{_dbaascli_short_name} dataguard createDrConfig"
        ebox = aExaBoxCluCtrlObj
        
        _options = ebox.mGetArgsOptions()
        _tcp_ssl_port = None
        if _options and _options.jsonconf and 'customer_network' in _options.jsonconf and\
            'drScan' in _options.jsonconf['customer_network'] and\
                'tcp_ssl_port' in _options.jsonconf['customer_network']['drScan']:
                    _tcp_ssl_port = _options.jsonconf['customer_network']['drScan']['tcp_ssl_port']
                    if _tcp_ssl_port:
                        _tcp_ssl_port = str(_tcp_ssl_port)
                        _tcp_ssl_port = _tcp_ssl_port.strip()
        # Run the dbaascli command to set dr scan and dr vip config if present in the payload
        if ebox.mGetDRVips():
            _dr_vips = ebox.mGetDRVips()
            _dr_vips_ip_list = []
            for _domu,_dr_vip in _dr_vips.items():
                _dr_vips_ip_list.append(f"{_domu.split('.')[0]}:{_dr_vip.mGetDRVIPAddr()}")
            _cmd_dr_vip_scan += f" --drVipList {','.join(_dr_vips_ip_list)} "
            # Scan is optional but dr vip needs to be present to run the dbaascli command
            if ebox.mGetDRScans():
                _dr_scan = ebox.mGetDRScans()
                _dr_scan_name = _dr_scan.mGetScanName()
                _dr_scan_port = _dr_scan.mGetScanPort()
                _cmd_dr_vip_scan += f" --drScanName {_dr_scan_name} --drListenerPort {_dr_scan_port} "
                if _tcp_ssl_port:
                    _cmd_dr_vip_scan += f" --drListenerTcpsPort {_tcp_ssl_port} "
            else:
                ebLogInfo(f"Not configuring DR Scans on the DOMUs. DR Scans were not found in the payload during cluster provisioning.")
            _dpairs = ebox.mReturnDom0DomUPair()
            _domu_list = [ _domu for _ , _domu in _dpairs]
            # Need to run the dbaascli command only on one DOMU
            with connect_to_host(_domu_list[0], get_gcontext(), username="root") as _node:
                _dbaascli_full_path = node_cmd_abs_path_check(_node, _dbaascli_short_name)
                # Replace the first occurrence of dbaascli with full path
                _cmd_dr_vip_scan = _cmd_dr_vip_scan.replace(_dbaascli_short_name, _dbaascli_full_path, 1)
                _node.mExecuteCmdLog(_cmd_dr_vip_scan)
                if _node.mGetCmdExitStatus() != 0:
                    _err_msg = f"*** Error: dbaascli command '{_cmd_dr_vip_scan}' failed to configure dr-vips/dr-scans on the DOMU {_domu_list[0]}"
                    ebLogError(_err_msg)
                    raise ExacloudRuntimeError(0x0116, 0xA, _err_msg,
                                                aStackTrace=True, aStep=self.step, aDo=True)
                else:
                    ebLogInfo(f"The dbaascli command '{_cmd_dr_vip_scan}' ran successfully on the DOMU {_domu_list[0]} to configure dr-vips/dr-scans.")
        else:
            ebLogInfo(f"Not configuring DR VIPs on the DOMUs. DR VIPs were not found in the payload during cluster provisioning.")

    def maxDistanceUpdate(self, ebox):
        _dom0s, _domUs, _ , _ = ebox.mReturnAllClusterHosts()
        _hosts = _dom0s + _domUs
        def _maxDistanceUpdate(_host):
            try:
                _node = exaBoxNode(get_gcontext())
                _node.mConnect(aHost=_host)                 

            
                if _node.mFileExists("/etc/chrony.conf"):
                    _sed_cmd = node_cmd_abs_path_check(_node, "sed")                        
                    #to delete the value in file if it already exist.                        
                    _cmd = f"{_sed_cmd} -i '/maxdistance/d' /etc/chrony.conf"
                    _node.mExecuteCmdLog(_cmd)
                    if _node.mGetCmdExitStatus() != 0:
                        _node.mDisconnect()
                        _msg = "Could not succesfully run the command {}".format(_cmd)
                        ebLogError("*** {0} ***".format(_msg))
                        return

                    
                    _cmd = f"{_sed_cmd} -i '$ a # maxdistance directive sets the maximum allowed root distance of the sources to not be rejected by the source selection' /etc/chrony.conf"
                    _node.mExecuteCmdLog(_cmd)
                    _cmd = f"{_sed_cmd} -i '$ a maxdistance 16.0' /etc/chrony.conf"
                    _node.mExecuteCmdLog(_cmd)
                    if _node.mGetCmdExitStatus() != 0:
                        _node.mDisconnect()
                        _msg = "Could not succesfully run the command {}".format(_cmd)
                        ebLogError("*** {0} ***".format(_msg))
                        return
                    else:
                        ebLogInfo(f"Chrony conf file update successful on {_host}")

                    _systemctl_cmd = node_cmd_abs_path_check(_node, "systemctl")                        
                    _cmd = f"{_systemctl_cmd} restart chronyd"
                    _node.mExecuteCmdLog(_cmd)
                    if _node.mGetCmdExitStatus() != 0:
                        _node.mDisconnect()
                        _msg = "Could not succesfully run the command {}".format(_cmd)
                        ebLogError("*** {0} ***".format(_msg))
                        return
                    

                if _node.mFileExists("/etc/ntp.conf"):
                    _sed_cmd = node_cmd_abs_path_check(_node, "sed")
                    #to delete the value in file if it already exist.
                    _cmd = f"{_sed_cmd} -i '/maxdist/d' /etc/ntp.conf"
                    _node.mExecuteCmdLog(_cmd)
                    if _node.mGetCmdExitStatus() != 0:
                        _node.mDisconnect()
                        _msg = "Could not succesfully run the command {}".format(_cmd)
                        ebLogError("*** {0} ***".format(_msg))
                        return

                    _cmd = f"{_sed_cmd} -i '$ a # maxdistance directive sets the maximum allowed root distance of the sources to not be rejected by the source selection' /etc/ntp.conf"
                    _node.mExecuteCmdLog(_cmd)
                    _cmd = f"{_sed_cmd} -i '$ a tos maxdist 16' /etc/ntp.conf"
                    _node.mExecuteCmdLog(_cmd)
                    if _node.mGetCmdExitStatus() != 0:
                        _node.mDisconnect()
                        _msg = "Could not succesfully run the command {}".format(_cmd)
                        ebLogError("*** {0} ***".format(_msg))
                        return
                    else:
                        ebLogInfo(f"ntp.conf file update successful on {_host}")

                    _service_cmd = node_cmd_abs_path_check(_node, "service")                        
                    _cmd = f"{_service_cmd} ntpd restart"
                    _node.mExecuteCmdLog(_cmd)
                    if _node.mGetCmdExitStatus() != 0:
                        _node.mDisconnect()
                        _msg = "Could not succesfully run the command {}".format(_cmd)
                        ebLogError("*** {0} ***".format(_msg))
                        return
                  

                _node.mDisconnect()

            except Exception as ere:
                ebLogWarn('*** Exception Message Detail on host {0} {1}'.format(_host,ere))
                return


        _plist = ProcessManager()

        for _host in _hosts:
            _p = ProcessStructure(_maxDistanceUpdate, [_host,])
            _p.mSetMaxExecutionTime(30*60) #30 minutes timeout
            _p.mSetJoinTimeout(5)
            _p.mSetLogTimeoutFx(ebLogWarn)
            _plist.mStartAppend(_p)

        _plist.mJoinProcess()

    def mSeedOCIDonDomU(self,eBox,aOptions):
        if (aOptions.jsonconf is not None and 'vmClusterOcid' in aOptions.jsonconf.keys()):
            _exa_ocid = aOptions.jsonconf['vmClusterOcid']
            _seed_file_name = "/var/opt/oracle/exacc.props" 
            for _, _domu in eBox.mReturnDom0DomUPair():
                _cmd =""
                _node = exaBoxNode(get_gcontext())
                _node.mConnect(aHost=_domu)
                _echo_cmd = node_cmd_abs_path_check(_node, "echo")
                if _node.mFileExists("/var/opt/oracle/exacc.props"):
                    # sed and echo can live either in /bin or /usr/bin depending on
                    # Exadata's version so just get the right path
                    _sed_cmd = node_cmd_abs_path_check(_node, "sed")
                    _cmd += f"{_sed_cmd} -i '/d' {_seed_file_name} && "
                else:
                    _cmd += f"/bin/touch {_seed_file_name} && "
                _cmd += f"{_echo_cmd} 'vmcluster_ocid={_exa_ocid}' >> {_seed_file_name}; "
                ebLogDebug(f"mSeedOCIDonDomU : command: {_cmd}")
                _, _, _err = _node.mExecuteCmd(_cmd)
                _exit_code = _node.mGetCmdExitStatus()
                if _exit_code:
                    ebLogError(f"OCID seed failed on {_domu}: {_cmd} exit code: {_exit_code} stderr: {_err}")
                else:
                    ebLogInfo(f"OCID seeded on {_domu}: file path:{_seed_file_name}")

    def mSanitizeDomUSysctlConf(self, aCluctrl):
        if aCluctrl.mIsKVM():
            return

        SYSCTL_CONF = '/etc/sysctl.conf'
        ebLogInfo(f"*** Sanitizing DomUs {SYSCTL_CONF} ***")
        _props_to_remove = ['net.ipv6.conf.ib100.accept_ra',
                            'net.ipv6.conf.ib101.accept_ra'] + \
                           (['net.ipv6.conf.bondeth1.accept_ra']
                           if aCluctrl.isATP() else [])
        for _, _domu in aCluctrl.mReturnDom0DomUPair():
            with connect_to_host(_domu, get_gcontext(), 'root') as node:
                _sysctl_conf_lines = \
                    node_read_text_file(node, SYSCTL_CONF).splitlines()
                if not any(any(prop in line for prop in _props_to_remove)
                            for line in _sysctl_conf_lines):
                    ebLogInfo(f"Skipping DomU {_domu}")
                    continue

                # Create a backup first
                _now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                _sysctl_conf_bak = f"{SYSCTL_CONF}.{_now}.sanitize.bak"
                _cmd = f"/bin/cp {SYSCTL_CONF} {_sysctl_conf_bak}"
                node_exec_cmd_check(node, _cmd)

                # Remove bad properties and save
                _sysctl_conf_fixed = '\n'.join([
                    ('# ' if any(prop in line for prop in _props_to_remove)
                    else '') + line for line in _sysctl_conf_lines + [''] ])
                node_write_text_file(node, SYSCTL_CONF, _sysctl_conf_fixed)

                # Reload changes
                node_exec_cmd_check(node, "/usr/sbin/sysctl -p")
                ebLogInfo(f"*** Removed {_props_to_remove} from "
                            f"{SYSCTL_CONF} in {_domu} ; "
                            f"Backup at {_sysctl_conf_bak}")

        ebLogInfo(f"*** Sanitized DomUs {SYSCTL_CONF} succesfully! ***")

    def mParallelValidateGriddisks(self, aCluctrl):
        ebox = aCluctrl
        #Create the multiprocess structure
        _plist = ProcessManager()
        _rc_status = _plist.mGetManager().dict()
        _cells = list(ebox.mReturnCellNodes().keys())
        def _validate_griddisks(_cell, _rc_status):
            _rc_status[_cell] = ebox.mValidateGridDisks(aCell=_cell)

        for _cell in _cells:
            _p = ProcessStructure(_validate_griddisks, (_cell, _rc_status))
            _p.mSetMaxExecutionTime(30*60) # 30 minutes
            _p.mSetJoinTimeout(5)
            _p.mSetLogTimeoutFx(ebLogWarn)
            _plist.mStartAppend(_p)
        _plist.mJoinProcess()
        _err_cells = []
        for _cell in _cells:
            if _rc_status[_cell] != 0:
                _err_cells.append(_cell)
        if _err_cells:
            _err_msg = f"Failed to validate grid disks on {_err_cells}"
            ebLogError(_err_msg)
            ebox.mUpdateErrorObject(gProvError['ERROR_GDCOUNT_MISMATCH'], _err_msg)
            raise ExacloudRuntimeError(0x0418, 0xA, _err_msg)
