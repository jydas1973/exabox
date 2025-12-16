#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/filesystem/clumountpoint_reclaim_space.py /main/3 2025/11/04 06:25:42 aararora Exp $
#
# clumountpoint_reclaim_space.py
#
# Copyright (c) 2023, 2025, Oracle and/or its affiliates.
#
#    NAME
#      clumountpoint_reclaim_space.py - <one-line expansion of the name>
#
#    DESCRIPTION
#
# After out of place patching of grid path, the old grid path is left unused and
# that space is not available to the DOM0. This class in exacloud implements the
# endpoint - "reclaim_mountpoint_space" to reclaim unused space occupied by the
# old grid mountpoint.
# 
# Before triggering the below command, create a new grid home and perform
# new grid home patching to move the services running from old grid home to new
# grid home.
#
# Design document: https://confluence.oraclecorp.com/confluence/x/xj5E1wE
#
# Exacloud command:
# ================
#
# ./bin/exacloud -clu reclaim_mountpoint_space -cf
# clusters/cluster-scaqab10adm0708clu7/config/scaqab10adm0708clu7.xml -jc reclaim
# _mountpoint_space.json
#
# Payload:
# =======
#
# {
#         "mountpoint": "/u01/app/19.0.0.0/grid",
#         "gridVersion": "19.25.0.0.241015"
# }
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aararora    10/29/25 - Bug 38591105: Read grid version using gridVersion
#                           from payload
#    aararora    08/28/25 - ER 38335598: Address additional requirement for
#                           reclaiming mountpoint space
#    aararora    10/06/23 - Bug 35824846: Reclaim unused space from grid
#                           mountpoint on xen and KVM VMs.
#    aararora    10/06/23 - Creation
#
from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace
from exabox.ovm.hypervisorutils import getTargetHVIType, HVIT_XEN, HVIT_KVM
from exabox.utils.node import (connect_to_host, node_cmd_abs_path_check)
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure
from exabox.ovm.vmcontrol import exaBoxOVMCtrl
from exabox.ovm.utils.clu_utils import ebCluUtils

from ast import literal_eval

class ebCluMountpointReclaimSpace(object):

    def __init__(self, aExaBoxCluCtrlObj, aOptions):
        self.__cluctrl = aExaBoxCluCtrlObj
        self.__options = aOptions

    def mPerformPayloadValidations(self, aPayload):
        ebLogTrace("Entering method mPerformPayloadValidations.")
        if not aPayload:
            _msg = "Please provide valid json as payload."
            ebLogError(_msg)
            raise ExacloudRuntimeError(0x0207, 0xA, _msg)
        if "mountpoint" not in aPayload or "gridVersion" not in aPayload:
            _msg = "Please provide mountpoint and gridVersion value in the "\
                   "payload. Mountpoint should be a string parameter "\
                   "mentioning the mountpoint which needs to be unmounted."\
                   " gridVersion should be the grid version for the grid"\
                   " being unmounted."
            ebLogError(_msg)
            raise ExacloudRuntimeError(0x0207, 0xA, _msg)
        if aPayload["mountpoint"] == '' or aPayload["gridVersion"] == '':
            _msg = "Please provide valid mountpoint and gridVersion value in the payload."
            ebLogError(_msg)
            raise ExacloudRuntimeError(0x0207, 0xA, _msg)
        ebLogTrace("Exiting method mPerformPayloadValidations.")

    def mCheckPathUsed(self, aNode, aMountpoint, aDOMU):
        """
        Check if the aMountpoint path is currently in use
        """
        _lsof_cmd = node_cmd_abs_path_check(aNode, "lsof", sbin=True)
        _grep_cmd = node_cmd_abs_path_check(aNode, "grep")
        _wc_cmd = node_cmd_abs_path_check(aNode, "wc")
        _awk_cmd = node_cmd_abs_path_check(aNode, "awk")
        _cmd = f"{_lsof_cmd} | {_grep_cmd} {aMountpoint} | {_wc_cmd} | {_awk_cmd} " + "'{print $1}'"
        _i, _o, _e = aNode.mExecuteCmd(_cmd)
        _output = _o.read()
        if _output.strip() != "0":
            # Error out since the path is being currently used
            _msg = f"Path {aMountpoint} is currently in use in "\
                    f"DOMU {aDOMU}. Cannot proceed further."
            ebLogError(_msg)
            raise ExacloudRuntimeError(0x0208, 0xA, _msg)
        return False

    def mGetDiskUsageOutput(self, aNode, aMountpoint, aDOMU):
        """
        Get du -sh output for the given mountpoint
        """
        _du_cmd = node_cmd_abs_path_check(aNode, "du")
        _i, _o, _e = aNode.mExecuteCmd(f"{_du_cmd} -sh {aMountpoint}")
        _output = _o.read()
        if not _output or _output == '':
            # Log a warning since the du command output could not be
            # obtained for the given mountpoint
            _msg = "Disk usage could not be obtained for the given "\
                   f"mountpoint {aMountpoint} on DOMU {aDOMU}."
            ebLogWarn(_msg)
            return None
        else:
            return _output

    def mRemoveFstabEntry(self, aNode, aMountpoint, aDOMU):
        """
        Remove entry for mountpoint from /etc/fstab
        """
        _sed_cmd = node_cmd_abs_path_check(aNode, "sed")
        # We need to escape the forward slashes in the mountpoint
        _mountpoint = aMountpoint.replace('/', '\/')
        _cmd = f'{_sed_cmd} -i "/{_mountpoint}/d" /etc/fstab'
        aNode.mExecuteCmdLog(_cmd)
        if aNode.mGetCmdExitStatus() != 0:
            # continuable error - this can be done manually if the mountpoint could not
            # be removed for this domu
            _msg = f"{aMountpoint} could not be removed from /etc/fstab "\
                    f"for DOMU {aDOMU}. Please remove manually."
            ebLogWarn(_msg)

    def mRemoveGridImgFile(self, aNode, aDOMU, aDOM0, aVersion):
        """
        Remove grid img file on the DOM0 for the DOMU.
        """
        _grid_img_file = f"/EXAVMIMAGES/GuestImages/{aDOMU}/grid{aVersion}*.img"
        _test_cmd = node_cmd_abs_path_check(aNode, "test")
        _cmd_check = f"{_test_cmd} -f {_grid_img_file}"
        aNode.mExecuteCmdLog(_cmd_check)
        if aNode.mGetCmdExitStatus() != 0:
            _msg = f"{_grid_img_file} file does not exist on DOM0 {aDOM0}."
            ebLogWarn(_msg)
        else:
            # Remove the grid img file on the DOM0
            _rm_cmd = node_cmd_abs_path_check(aNode, "rm")
            _cmd = f"{_rm_cmd} -rf {_grid_img_file}"
            aNode.mExecuteCmdLog(_cmd)
            if aNode.mGetCmdExitStatus() == 0:
                _msg = f"{_grid_img_file} file is removed on DOM0 {aDOM0}."
                ebLogInfo(_msg)
            else:
                _msg = f"{_grid_img_file} file could not be removed on "\
                       f"DOM0 {aDOM0}. Please remove the file manually."
                ebLogWarn(_msg)

    def mRemoveDeviceEntryVMCfg(self, aNode, aDOMU, aDevice):
        """
        Gets disk value in vm cfg for the DOMU and removes the device entry
        for the mountpoint from the list
        """
        _vmhandle = exaBoxOVMCtrl(aCtx=get_gcontext(), aNode=aNode)
        _vmhandle.mReadRemoteCfg(aDOMU)
        _cfg = _vmhandle.mGetOVSVMConfig(aDOMU)
        if _cfg is None:
            ebLogWarn(f"vm.cfg for DomU {aDOMU} is not available. Not "\
                       "removing grid mountpoint entry.")
            return
        _disk_data = literal_eval(_cfg.mGetValue('disk'))
        _disk_data_new = []
        for _disk in _disk_data:
            if aDevice not in _disk:
                _disk_data_new.append(_disk)
        _cfg.mSetValue('disk', str(_disk_data_new))
        # Save the edited vm cfg
        self.__cluctrl.mSaveVMCfg(aNode, aDOMU, _cfg.mRawConfig())

    def mExecuteXenSteps(self, aDOM0, aDOMU, aMountpoint, aVersion, aRcStatus):
        """
        Execute steps for Xen environment if the hypervisor is Xen
        """
        ebLogTrace(f"Entering method mExecuteXenSteps for DOMU {aDOMU}.")
        _device_name = None
        _rc_status = aRcStatus
        _rc_status[aDOMU] = 0
        with connect_to_host(aDOMU, get_gcontext()) as _node:
            # Step 2: Find the device name for the given mountpoint
            _lsblk_cmd = node_cmd_abs_path_check(_node, "lsblk")
            _grep_cmd = node_cmd_abs_path_check(_node, "grep")
            _cmd = f"{_lsblk_cmd} | {_grep_cmd} {aMountpoint}"
            _i, _o, _e = _node.mExecuteCmd(_cmd)
            _output = _o.read()
            if not _output or _output == '':
                # Error out since the device name could not be extracted from
                # the given mountpoint
                # non-continuable error - device name is essential for further operation
                _msg = "Device name could not be obtained for the given "\
                       f"{aMountpoint} on DOMU {aDOMU}."
                ebLogError(_msg)
                _rc_status[aDOMU] = 1
                return
            _device_name = _output.strip().split()[0]
            # Step 3: Print du -sh {aMountpoint} output before detach
            _output = self.mGetDiskUsageOutput(_node, aMountpoint, aDOMU)
            if _output:
                ebLogTrace(f"du -sh {aMountpoint} output is {_output} before"\
                           f" detach on DOMU {aDOMU}.")
        with connect_to_host(aDOM0, get_gcontext()) as _node:
            # Step 4: Detach device on DOM0
            _xm_cmd = node_cmd_abs_path_check(_node, "xm", sbin=True)
            _cmd = f"{_xm_cmd} block-detach {aDOMU} {_device_name}"
            _node.mExecuteCmdLog(_cmd)
            if _node.mGetCmdExitStatus() != 0:
                # Error out since the detach was not successful
                # non-continuable error - we know that device name was obtained
                # but detach of device was not successful
                _msg = f"Could not detach the device {_device_name} from DOMU"\
                       f" {aDOMU}. Either the resource is busy or there was "\
                        "an error running the detach command."
                ebLogError(_msg)
                _rc_status[aDOMU] = 1
                return
            ebLogInfo(f"Detached device {_device_name} from the DOMU {aDOMU}.")
            # Step 5: Remove xvdb device entry in disk parameter of vm.cfg file
            # continuable error - since in previous attempt - vm cfg entry removal could have been successful
            try:
                self.mRemoveDeviceEntryVMCfg(_node, aDOMU, _device_name)
            except Exception as ex:
                ebLogWarn(f"Could not remove device entry from vm.cfg file for {aDOMU}."\
                    f" Device name: {_device_name}. Error: {ex}.")
            # Step 6: Remove the grid img file on DOM0
            self.mRemoveGridImgFile(_node, aDOMU, aDOM0, aVersion)
        with connect_to_host(aDOMU, get_gcontext()) as _node:
            # Step 7: Remove the /etc/fstab entry for the mountpoint.
            # This should be done after detach is successful from DOM0
            self.mRemoveFstabEntry(_node, aMountpoint, aDOMU)
            # Step 8: Print du -sh {aMountpoint} output after detach
            _output = self.mGetDiskUsageOutput(_node, aMountpoint, aDOMU)
            if _output:
                ebLogTrace(f"du -sh {aMountpoint} output is {_output} after"\
                           f" detach on DOMU {aDOMU}.")
        ebLogTrace(f"Exiting method mExecuteXenSteps for DOMU {aDOMU}.")

    def mExecuteKVMSteps(self, aDOM0, aDOMU, aMountpoint, aVersion, aRcStatus):
        """
        Execute steps for KVM environment if the hypervisor is KVM
        """
        ebLogTrace("Entering method mExecuteKVMSteps.")
        _rc_status = aRcStatus
        _rc_status[aDOMU] = 0
        with connect_to_host(aDOMU, get_gcontext()) as _node:
            # Step 2: Get the filesystem path using df command
            _df_cmd = node_cmd_abs_path_check(_node, "df")
            _grep_cmd = node_cmd_abs_path_check(_node, "grep")
            _cmd = f"{_df_cmd} | {_grep_cmd} {aMountpoint}"
            _i, _o, _e = _node.mExecuteCmd(_cmd)
            _output = _o.read()
            if not _output or _output == '':
                # Log a warning message since the filesystem path could not be extracted from
                # the given mountpoint
                # continuable error - since in previous attempt - unmount could have been successful
                _msg = "Filesystem path could not be obtained for the given "\
                       f"{aMountpoint} on DOMU {aDOMU}."
                ebLogWarn(_msg)
            else:
                _filesystem_path = _output.strip().split()[0]
                # Step 3: Log the du -sh output for the given mountpoint
                _output = self.mGetDiskUsageOutput(_node, aMountpoint, aDOMU)
                if _output:
                    ebLogTrace(f"du -sh {aMountpoint} output is {_output} before"\
                            f" detach on DOMU {aDOMU}.")
                # Step 4: Unmount the filesystem obtained in Step 2 from the DOMU
                _umount_cmd = node_cmd_abs_path_check(_node, "umount", sbin=True)
                _cmd = f"{_umount_cmd} {_filesystem_path}"
                _node.mExecuteCmdLog(_cmd)
                if _node.mGetCmdExitStatus() != 0:
                    # non-continuable error - we know that filesystem path exists and we are not
                    # able to unmount the same
                    _msg = f"Could not unmount {_filesystem_path} filesystem path"\
                        f" on DOMU {aDOMU}."
                    ebLogError(_msg)
                    _rc_status[aDOMU] = 1
                    return
                ebLogInfo(f"Filesystem path {_filesystem_path} unmounted "\
                        f"successfully on DOMU {aDOMU}.")
            # Step 5: Remove the /etc/fstab entry for the mountpoint.
            self.mRemoveFstabEntry(_node, aMountpoint, aDOMU)
        with connect_to_host(aDOM0, get_gcontext()) as _node:
            # Step 6: Detach the disk from DOM0
            # Run virsh domblklist to get the image path to detach
            _virsh_cmd = node_cmd_abs_path_check(_node, "virsh")
            _grep_cmd = node_cmd_abs_path_check(_node, "grep")
            _cmd = f"{_virsh_cmd} domblklist {aDOMU} | {_grep_cmd} "\
                   f"grid{aVersion}"
            _i, _o, _e = _node.mExecuteCmd(_cmd)
            _output = _o.read()
            if not _output or _output == '':
                # log a warning message since the image path could not be extracted from
                # the given mountpoint
                # continuable error - since it can happen that in previous attempt, this would have
                # been removed
                _msg = "Image path could not be obtained for the given "\
                       f"{aMountpoint} on DOMU {aDOMU} for grid version "\
                       f"{aVersion}."
                ebLogWarn(_msg)
            else:
                _device_output = _output.strip().split()
                _img_path = _device_output[1]
                # Detach disk
                _cmd = f"{_virsh_cmd} detach-disk {aDOMU} "\
                    f"{_img_path} --config --live"
                _node.mExecuteCmdLog(_cmd)
                if _node.mGetCmdExitStatus() != 0:
                    # non-continuable error - we know that image path exists and we are not
                    # able to detach the same
                    _msg = f"Could not detach disk {_img_path} for DOMU "\
                        f"{aDOMU}."
                    ebLogError(_msg)
                    _rc_status[aDOMU] = 1
                    return
                ebLogInfo(f"Disk {_img_path} detached successfully for DOMU "\
                        f"{aDOMU}.")
            # Step 7: Remove grid img file on DOM0 for the DOMU
            self.mRemoveGridImgFile(_node, aDOMU, aDOM0, aVersion)
        # Step 8: Print du -sh {aMountpoint} output after detach
        with connect_to_host(aDOMU, get_gcontext()) as _node:
            _output = self.mGetDiskUsageOutput(_node, aMountpoint, aDOMU)
            if _output:
                ebLogTrace(f"du -sh {aMountpoint} output is {_output} after"\
                           f" detach on DOMU {aDOMU}.")
        ebLogTrace("Exiting method mExecuteKVMSteps.")

    def mReclaimMountpointSpace(self):
        """
        API entry point to reclaim space on DOMU and DOM0 after detaching
        the given grid mountpoint
        Design document: https://confluence.oraclecorp.com/confluence/x/xj5E1wE
        """
        ebLogTrace("Entering method mReclaimMountpointSpace.")
        _payload = self.__options.jsonconf
        # Perform payload validations
        self.mPerformPayloadValidations(_payload)
        _mountpoint = _payload["mountpoint"]
        _version = _payload["gridVersion"]
        _dpairs = self.__cluctrl.mReturnDom0DomUPair()
        # Perform a precheck
        for _, _domu in _dpairs:
            with connect_to_host(_domu, get_gcontext()) as _node:
                # Step 1: Precheck for mountpoint in-use
                # Below will error out if the path is being used for any of the DOMU
                self.mCheckPathUsed(_node, _mountpoint, _domu)
        _plist = ProcessManager()
        _rc_status = _plist.mGetManager().dict()
        # Check for matching domu from the payload in the registered dom0
        # domu pairs and according to the hypervisor, execute the steps as
        # provided in the design document
        for _dom0, _domu in _dpairs:
            _hypervisor = getTargetHVIType(_dom0)
            if _hypervisor == HVIT_KVM:
                _p = ProcessStructure(
                    self.mExecuteKVMSteps,
                    [_dom0,_domu,_mountpoint,_version, _rc_status], _domu)
            elif _hypervisor == HVIT_XEN:
                _p = ProcessStructure(
                    self.mExecuteXenSteps,
                    [_dom0,_domu,_mountpoint,_version, _rc_status], _domu)
            else:
                continue
            _p.mSetMaxExecutionTime(7200) # 2 hours should be sufficient
            _p.mSetJoinTimeout(5)
            _p.mSetLogTimeoutFx(ebLogWarn)
            _plist.mStartAppend(_p)
        _plist.mJoinProcess()
        _success_domus = []
        _failed_domus = []
        for _dom0, _domu in _dpairs:
            if _domu in _rc_status and _rc_status[_domu] == 0:
                _success_domus.append(_domu)
            elif _domu in _rc_status and _rc_status[_domu] != 0:
                _failed_domus.append(_domu)
        if _failed_domus:
            _msg = "There was an issue reclaiming space for mountpoint "\
                    f"{_mountpoint} on DOMUs : {_failed_domus}. Check the "\
                    "exacloud error logs for these DOMUs."
            ebLogError(_msg)
            raise ExacloudRuntimeError(_msg)
        else:
            ebLogInfo("Successfully reclaimed space for mountpoint "\
                 f"{_mountpoint} on DOMUs : {_success_domus}.")