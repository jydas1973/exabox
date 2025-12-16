"""
 Copyright (c) 2019, 2025, Oracle and/or its affiliates.

NAME:
    kvmdiskmgr - Disk management for KVM.

FUNCTION:
    Disk resize operation for KVM.

NOTE:
    None

History:
    scoral    10/14/25 - Bug 38500655: Add filesystem pattern compatible with
                         Exascale EDVs.
    scoral    03/26/24 - Bug 36447615: Wrap piped commands with sudo.
    scoral    03/13/24 - Bug 36343989: Improve logging.
    scoral    02/23/24 - Bug 36324929: Make code compatible with ExaDB-XS and
                         non-ExaDB-XS.
    scoral    02/14/24 - Bug 36300231: Avoid retrieving the disk image size
                         from the Dom0 in ExaDB-XS since we can't control the
                         EDV disk size in the Dom0.
                         Avoid clusterware restart if it is not available.
    scoral    02/06/24 - Enh 36242967: Add support for ExaDB-XS.
    scoral    10/11/21 - Bug 33265977: DomU filesystems API refactoring.
    rajsag    06/09/21 - 33102660 - exacc elastic : meaning full exception along with notify customer through console 
    nmallego  21/06/21 - Bug32991330 - Referring path for ebCluPatchHealthCheck
    dekuckre  21/05/21 - 32899744: Acquire locks before executing vm_maker cmds  
    naps      04/04/20 - Create file

"""

import time
from exabox.log.LogMgr import ebLogDiag, ebLogWarn, ebLogInfo,  ebLogError, ebLogVerbose, ebLogTrace
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.core.Error import ebError, ExacloudRuntimeError, gPartitionError, gReshapeError
from exabox.infrapatching.core.clupatchhealthcheck import ebCluPatchHealthCheck
from exabox.utils.node import (
    node_cmd_abs_path,
    node_cmd_abs_path_check,
    node_exec_cmd,
    node_exec_cmd_check,
    connect_to_host
)
from exabox.ovm.cluencryption import getMountPointInfo, getDiskLabel
from exabox.ovm.utils.clu_utils import ebCluUtils
import json, re
import math
import os

class exaBoxKvmDiskMgr(object):

    def __init__(self, aCluDomuPartObject):
        self.__edp = aCluDomuPartObject

    def logDebugInfo(self, aOutLines=None, aErrorStream=None):
        _outLines = aOutLines
        _errorStream = aErrorStream

        ebLogInfo("Command Output : ")
        if len(_outLines):
            for _line in _outLines:
                ebLogInfo(_line)

        if _errorStream is not None:
            ebLogInfo("Command Error : ")
            _err = _errorStream.readlines()
            for _line in _err:
                ebLogInfo(_line)

    def mUnmountOedaDbHomes(self, aDom0Name, aGuestName, aHostNode=None, aGuestNode=None):
        """
            Unmount from DomU, removes from /etc/fstab, detach from Virsh
            And remove DB home image file.  
            :param str aDom0Name          Hostname of Dom0
            :param str aGuestName         Client Hostname non-NAT of domU
            :param exaBoxNode aHostNode  (OPTIONAL) connected Node to dom0
            :param exaBoxNode aGuestNode (OPTIONAL) connected Node to domU
        """

        if not aGuestNode:
            _guest_node = exaBoxNode(get_gcontext())
            _guest_node.mConnect(aHost=aGuestName)
        else:
            _guest_node = aGuestNode
 
        _db_paths = []
        _i, _o, _e = _guest_node.mExecuteCmd('/usr/bin/cat /etc/fstab')
        # Capture dev and path of DB Homes from /etc/fstab
        #  /dev/VGExaDbDisk.db19.0.0.0.200414-3.img/LVDBDisk    /u01/app/oracle/product/19.0.0.0/dbhome_1  xfs ...
        db_home_regex = re.compile(r'\s*/dev/VGExaDbDisk\.(.*)/LVDBDisk\s+(.*dbhome_1)\s+')
        for _line in _o.readlines():
            db_home = db_home_regex.match(_line)
            if db_home:
                _db_img,_db_mountpoint = db_home.groups()
                _db_paths.append(_db_mountpoint)

        for _db in _db_paths:
            # Umount from DomU
            _guest_node.mExecuteCmd("/usr/bin/umount {}".format(_db))
        # Remove all dbhomes from /etc/fstab
        _guest_node.mExecuteCmd("/usr/bin/sed -i '/dbhome_1/d' /etc/fstab")

        if not aGuestNode:
            _guest_node.mDisconnect()

        from exabox.ovm.clucontrol import exaBoxCluCtrl
        try:
            if isinstance(self.__edp, exaBoxCluCtrl):
                self.__edp.mAcquireRemoteLock()
            else:
                self.__edp.mGetEbox().mAcquireRemoteLock()

            # Connect to dom0, detach disk with vm_maker
            if not aHostNode:
                _host_node = exaBoxNode(get_gcontext())
                _host_node.mConnect(aHost=aDom0Name)
            else:
                _host_node = aHostNode

            # There exist environments where the DBHomes DomU VG name is
            # VGExaDbDisk.db-klone-Linux-x86-64-19000200414.50.img instead of
            # VGExaDbDisk.db19.0.0.0.200414-3.img so, we're going to look for
            # all possible DBHome images in the Dom0, dettach them and delete
            # them now that we're sure that they've been unmounted.
            _disk_image = f"/EXAVMIMAGES/GuestImages/{aGuestName}/db*.img"
            _, _o, _ = _host_node.mExecuteCmd(f"/bin/ls {_disk_image}")
            _db_paths = map(str.strip, _o.readlines())

            for _db in _db_paths:
                _host_node.mExecuteCmdLog("/opt/exadata_ovm/vm_maker --detach --disk-image {} --domain {}".format(_db,aGuestName))
                # Delete unmounted and detached image
                _host_node.mExecuteCmd("/usr/bin/rm -f {}".format(_db))

        finally:
            if not aHostNode:
                _host_node.mDisconnect()
       
            if isinstance(self.__edp, exaBoxCluCtrl):
                self.__edp.mReleaseRemoteLock()
            else:
                self.__edp.mGetEbox().mReleaseRemoteLock()


    def mExecuteDomUDownsizeStepsEncrypted(self, aDomU, aFilesystem, aNewSizeGB):
        """
        This method is very similar to mExecuteDomUDownsizeSteps(), but it contains
        a few different steps to accomplish the resize if the volume is
        encrypted using LUKS

        :param aDomU: The DomU where we will resize the fs aFilesystem
        :param aFilesystem: string representing the mountpoint/fs where the fs
            we will resize is mounted
        :param aNewSizeGB: the new size
        """

        _domU = aDomU
        _filesystem = aFilesystem
        _new_sizeGB = aNewSizeGB

        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_domU)
        _eBoxCluCtrl = self.__edp.mGetEbox()

        # Get info about block devices supporting our filesystem to resize
        _cmdstr = "/usr/bin/lsblk -p -r | /usr/bin/grep -B 3 " + _filesystem
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        ebLogTrace("Executing cmd : %s"%(_cmdstr))
        _out = _o.readlines()
        ebLogTrace("Command output : " + '\n'.join(_out))

        if _out is None:
            self.logDebugInfo(_out, _e)
            _detail_error = 'Could not perform filesystem check on ' + _domU + ' for filesystem ' + _filesystem
            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_FILE_SYS_CHECK_FAILED'], _detail_error)
            return self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)

        # Store disk, partition, and lv to use later
        _imgdisk = _out[0].strip().split(' ')[0]
        _diskpart = _out[1].strip().split(' ')[0]
        _lvpath = _out[2].strip().split(' ')[0]

        ebLogInfo("image disk is : %s"%(_imgdisk))
        ebLogInfo("partition name is : %s"%(_diskpart))
        ebLogInfo("lv path is : %s"%(_lvpath))

        # Confirm that the partition is MSDOS, if not we raise an ERROR
        # See Linux bug 36858945
        _disk_label = getDiskLabel(_node, _imgdisk)
        if _disk_label == "msdos":
            ebLogInfo(f"Disk label {_domU} for {_imgdisk} is already {_disk_label}")

        # if label is GPT, check if gdisk is installed in dom0
        elif _disk_label == "gpt":
            _detail_error = (f"The {_imgdisk} partition is detected as GPT. "
                "The shrink cannot continue, please engage support to convert "
                "this partition to MSDOS")
            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_PARTED_CMD_FAIL'], _detail_error)
            return self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)

        # Confirm LUKS keyapi is available before even start
        _keyapi_file = "/usr/lib/dracut/modules.d/99exacrypt/VGExaDbDisk.u02_extra_encrypted.img#LVDBDisk.key-api.sh"
        if not _node.mFileExists(_keyapi_file):
            _detail_error = f'the keyapi script {_keyapi_file} is not present in domU'
            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_KEYAPI_FAIL'], _detail_error)
            return self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)

        # Force a check on the FS first
        _bin_e2fsck = node_cmd_abs_path_check(_node, "e2fsck", sbin=True)
        _cmdstr = f"{_bin_e2fsck} -fy {_filesystem}"
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        ebLogTrace("Executing cmd : %s"%(_cmdstr))
        _out = _o.readlines()
        if _out is None:
            self.logDebugInfo(_out, _e)
            _detail_error = 'Could not perform filesystem check on ' + _domU + ' for filesystem ' + _filesystem
            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_FILE_SYS_CHECK_FAILED'], _detail_error)
            return self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)

        # Resize FS to it's minimum size
        _bin_resize2fs = node_cmd_abs_path_check(_node, "resize2fs", sbin=True)
        _cmdstr = f"{_bin_resize2fs} -M {_filesystem}"
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        ebLogTrace("Executing cmd : %s"%(_cmdstr))
        _out = _o.readlines()
        if _node.mGetCmdExitStatus() != 0:
            self.logDebugInfo(_out, _e)
            _detail_error = 'filesystem resize command failed in domU'
            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_FSRESIZE_FAIL'], _detail_error)
            return self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)

        # Close the luks volume
        _bin_cryptsetup = node_cmd_abs_path_check(_node, "cryptsetup", sbin=True)
        _luks_size = None
        _cmdstr = f"{_bin_cryptsetup} close {_filesystem} -v"
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        ebLogTrace("Executing cmd : %s"%(_cmdstr))
        _out = _o.readlines()
        if _node.mGetCmdExitStatus() != 0:
            self.logDebugInfo(_out, _e)
            _detail_error = 'cryptsetup resize command failed in domU'
            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_LUKSRESIZE_FAIL'], _detail_error)
            return self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)

        # LV Shrink/Resize
        ## We are offsetting by 100MB to accomodate for later partitioning.
        _lvsize = None
        if _eBoxCluCtrl.mCheckConfigOption('disable_lvm_snapshot_space','True'):
            _lvsize = float(_new_sizeGB) - 0.1
        else:
            _lvsize = float(_new_sizeGB) - 2.1 # 2 GB space for snapshot

        _partsize = float(_new_sizeGB) - 0.05
        try:
            _cmdstr = "/usr/sbin/lvresize -L " + str(_lvsize) + "G " + _lvpath + " --force"
            _i, _o, _e = _node.mExecuteCmd(_cmdstr)
            _out = _o.read()
            _err = _e.read()
            if _node.mGetCmdExitStatus() != 0:
                ebLogTrace("stdout: {_out}\nstderr: {_err}")

                # Ref, check if stdout/stderr includes
                _full_out = _out + _err
                if re.search("New\s+size\s+.*matches\s+existing\s+size", _full_out):
                    ebLogInfo(f"LVresize failure detected to be caused by using "
                        "same Target Size. Ignoring error")
                else:
                    _detail_error = 'lvresize command failed in domU'
                    _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_LVRESIZE_FAIL'], _detail_error)
                    return self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)
        finally:
            # Open Luks volume regardless of LVResize success or Error
            # It will automatically fill up to use the new LV size or
            # stay with older size
            # First try to get keyapi data
            _out_file = None
            _i, _o, _e = _node.mExecuteCmd(_keyapi_file)
            ebLogTrace("Executing cmd : %s"%(_cmdstr))
            _out = _o.readlines()
            if _out:
                _out_file = _out[0].strip()
            if _node.mGetCmdExitStatus() != 0:
                self.logDebugInfo(_out, _e)
                _detail_error = 'calling keyapi command failed in domU'
                _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_KEYAPI_FAIL'], _detail_error)
                return self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)

            _bin_cryptsetup = node_cmd_abs_path_check(_node, "cryptsetup", sbin=True)
            _crypto_name = os.path.basename(_filesystem)
            _cmdstr = f"{_bin_cryptsetup} open {_lvpath} {_crypto_name} --key-file={_out_file} -v"
            _i, _o, _e = _node.mExecuteCmd(_cmdstr)
            ebLogTrace("Executing cmd : %s"%(_cmdstr))
            _out = _o.readlines()
            if _node.mGetCmdExitStatus() != 0:
                self.logDebugInfo(_out, _e)
                _detail_error = 'cryptsetup open command failed in domU'
                _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_LUKSRESIZE_FAIL'], _detail_error)
                return self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)
            if _out_file and _node.mFileExists(_out_file):
                ebLogWarn(f"Deleting keyapi {_out_file}")
                node_exec_cmd(_node, f"/bin/shred -fu {_out_file}")
            else:
                ebLogWarn(f"No keyapi to delete")

        # Increase the fs to use the new maximum available
        _bin_resize2fs = node_cmd_abs_path_check(_node, "resize2fs", sbin=True)
        _cmdstr = f"{_bin_resize2fs} {_filesystem}"
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        ebLogTrace("Executing cmd : %s"%(_cmdstr))
        _out = _o.readlines()
        if _node.mGetCmdExitStatus() != 0:
            self.logDebugInfo(_out, _e)
            _detail_error = 'filesystem resize command failed in domU'
            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_FSRESIZE_FAIL'], _detail_error)
            return self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)

        # Decrease PV Size
        _cmdstr = "/usr/sbin/pvresize -y --setphysicalvolumesize " + str(_partsize) + "G " +_diskpart
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        ebLogTrace("Executing cmd : %s"%(_cmdstr))
        _out = _o.readlines()
        if _node.mGetCmdExitStatus() != 0:
            self.logDebugInfo(_out, _e)
            _detail_error = 'pvresize command failed in domU'
            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_PVRESIZE_FAIL'], _detail_error)
            return self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)

        # Decrease Partition Size
        # Parted takes 'GiB' for base 1024 to match LVM 'G' (parted 'G' is base 1000 and not a real Gigabyte)
        _cmdstr = f"/bin/echo '1\n{_partsize}GiB\nYes' | /bin/sudo /usr/sbin/parted -a none {_imgdisk} ---pretend-input-tty resizepart"
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        ebLogTrace("Executing cmd : %s"%(_cmdstr))
        _out = _o.readlines()
        if _node.mGetCmdExitStatus() != 0:
            self.logDebugInfo(_out, _e)
            _detail_error = 'Parted command failed in domU with error ' + str(_node.mGetCmdExitStatus())
            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_PARTED_CMD_FAIL'], _detail_error)
            return self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)

        return 0

    def mExecuteDomUDownsizeSteps(self, aDomU, aFilesystem, aNewSizeGB):
        _domU = aDomU
        _filesystem = aFilesystem
        _new_sizeGB = aNewSizeGB

        #Check if Bug 36343848 applies
        def _fsMetacsumChk(aFilesystem):
            #_domU = aDomu
            _filesystem = aFilesystem
            _fs = _filesystem.split("/")[-1]
            
            if _fs == "VGExaDbDisk.u02_extra.img-LVDBDisk":
                _cmdstr = "/usr/sbin/e2fsck -fn " + _filesystem
                _e2fsckFlagchk = "Journal superblock has an unknown incompatible feature flag set."
                _e2fsprogsFailure = ""
                _, _o, _e = _node.mExecuteCmd(_cmdstr)
                _rc = _node.mGetCmdExitStatus()
                if _rc != 0:
                    _out = _o.readlines()
                    for _op in _out:
                        _op = _op.strip()
                        if _e2fsckFlagchk in _op:
                            _e2fsprogsFailure = True
                            break
                return _e2fsprogsFailure
        
        #Copy e2fsck binaries for Bug 36343848
        def _mCopyfsprogs(aNode):
            _node = aNode

            ebLogInfo("*** e2fsck failed due to Journal superblock has an unknown incompatible feature flag set, copying compatible e2fsprogs binaries into domu")
            #check if the e2fsprogs rpm exist in images directory
            _e2fsprogsRpm1 = "images/e2fsprogs.tar.gz"
            if os.path.isfile(_e2fsprogsRpm1):
                #copy checksum file too for comparision
                ebLogInfo("*** e2fsck reporting incompatible feature set, copying required e2fsprogs binaries")
                _node.mExecuteCmd("mkdir /opt/exacloud/fstools")
                _remotePath = "/opt/exacloud/fstools/"
                _node.mCopyFile(_e2fsprogsRpm1, _remotePath)
                node_exec_cmd_check(_node, "cd /opt/exacloud/fstools;tar xvf e2fsprogs.tar.gz")
                node_exec_cmd_check(_node, "cd /opt/exacloud/fstools;/usr/bin/sha256sum -c e2fsprogs_sha256.out --status")
                node_exec_cmd_check(_node, "cd /opt/exacloud/fstools;rpm2cpio e2fsprogs-1.45.4-3.0.7.el7.x86_64.rpm | cpio -id")
                node_exec_cmd_check(_node, "cd /opt/exacloud/fstools;rpm2cpio e2fsprogs-libs-1.45.4-3.0.7.el7.x86_64.rpm | cpio -id")
            else:
                _detail_error = 'images/e2fsprogs.tar.gz tar not found. lvresize may fail.'
                return self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)
        
        #This method sets e2fsck path to extracted binaries-Bug 36343848
        def _lvszPrefx(aFilesystem):
            _filesystem = aFilesystem
            _ldLibPath = "export LD_LIBRARY_PATH=/opt/exacloud/fstools/usr/lib64/;"
            _e2fsbin = "/opt/exacloud/fstools/usr/sbin/e2fsck -fy " + _filesystem
            _fsckcmdstr = _ldLibPath + _e2fsbin
            _Prefx = _fsckcmdstr + ";"
            _nofsck = " --no-fsck ;" + _e2fsbin

            return _Prefx, _nofsck

        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_domU)
        _eBoxCluCtrl = self.__edp.mGetEbox()

        _cmdstr = "/usr/bin/lsblk -p -r | /usr/bin/grep -B 2 " + _filesystem
        ebLogTrace("Executing cmd : %s"%(_cmdstr))
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        _out = _o.readlines()

        ebLogVerbose("Command output : " + '\n'.join(_out))

        if _out is None:
            self.logDebugInfo(_out, _e)
            _detail_error = 'Could not perform filesystem check on ' + _domU + ' for filesystem ' + _filesystem
            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_FILE_SYS_CHECK_FAILED'], _detail_error)
            return self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)
            

        _imgdisk = _out[0].strip().split(' ')[0]
        _diskpart = _out[1].strip().split(' ')[0]
        ebLogInfo("image disk is : %s"%(_imgdisk))
        ebLogInfo("partition name is : %s"%(_diskpart))

        #e2fsck reporting issues due to unsupported feature enabled
        _lvrzPrefix = "/usr/sbin/"
        _nofsck = ""
        if _fsMetacsumChk(_filesystem):
            _mCopyfsprogs(_node)
            _lvrzPrefix, _nofsck = _lvszPrefx(_filesystem)
        
        ## We are offsetting by 100MB to accomodate for later partitioning.
        _lvsize = None
        if _eBoxCluCtrl.mCheckConfigOption('disable_lvm_snapshot_space','True'):
            _lvsize = float(_new_sizeGB) - 0.1
        else:
            _lvsize = float(_new_sizeGB) - 2.1 # 2 GB space for snapshot
        _partsize = float(_new_sizeGB) - 0.05
        _cmdstr = _lvrzPrefix + "lvresize --resizefs -L" + str(_lvsize) + "G " + _filesystem + _nofsck
        ebLogTrace("Executing cmd : %s"%(_cmdstr))
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        _out = _o.readlines()
        if _node.mGetCmdExitStatus() != 0:
            self.logDebugInfo(_out, _e)
            _detail_error = 'lvresize command failed in domU'
            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_LVRESIZE_FAIL'], _detail_error)
            return self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)

        _cmdstr = "/usr/sbin/pvresize -y --setphysicalvolumesize " + str(_partsize) + "G " +_diskpart
        ebLogTrace("Executing cmd : %s"%(_cmdstr))
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        _out = _o.readlines()
        if _node.mGetCmdExitStatus() != 0:
            self.logDebugInfo(_out, _e)
            _detail_error = 'pvresize command failed in domU'
            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_PVRESIZE_FAIL'], _detail_error)
            return self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)

        # Parted takes 'GiB' for base 1024 to match LVM 'G' (parted 'G' is base 1000 and not a real Gigabyte)
        _cmdstr = f"/bin/echo '1\n{_partsize}GiB\nYes' | /bin/sudo /usr/sbin/parted -a none {_imgdisk} ---pretend-input-tty resizepart"
        ebLogTrace("Executing cmd : %s"%(_cmdstr))
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        _out = _o.readlines()
        if _node.mGetCmdExitStatus() != 0:
            self.logDebugInfo(_out, _e)
            _detail_error = 'Parted command failed in domU with error ' + str(_node.mGetCmdExitStatus())
            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_PARTED_CMD_FAIL'], _detail_error)
            return self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)

        return 0

    def mExecuteDomUUpsizeSteps(self, aDomU, aFilesystem, aNewSizeGB):
        _domU = aDomU
        _filesystem = aFilesystem
        _new_sizeGB = aNewSizeGB

        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_domU)
        _eBoxCluCtrl = self.__edp.mGetEbox()

        _cmdstr = "/usr/bin/lsblk -p -r | /usr/bin/grep -B 2 " + _filesystem
        ebLogTrace("Executing cmd : %s"%(_cmdstr))
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        _out = _o.readlines()

        ebLogVerbose("Command output : " + '\n'.join(_out))
      
        if _out is None:
            self.logDebugInfo(_out, _e)
            _detail_error = 'Could not perform filesystem check on ' + _domU + ' for filesystem ' + _filesystem
            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_FILE_SYS_CHECK_FAILED'], _detail_error)
            return self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)


        _imgdisk = _out[0].strip().split(' ')[0]
        _diskpart = _out[1].strip().split(' ')[0]
        ebLogInfo("image disk is : %s"%(_imgdisk))
        ebLogInfo("partition name is : %s"%(_diskpart))

        _cmdstr = "/usr/sbin/parted -a none " + _imgdisk + " resizepart 1 100%"
        ebLogTrace("Executing cmd : %s"%(_cmdstr))
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        _out = _o.readlines()
        if _node.mGetCmdExitStatus() != 0:
            self.logDebugInfo(_out, _e)
            _detail_error = 'Parted command failed in domU'
            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_PARTED_CMD_FAIL'], _detail_error)
            return self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)
            

        _cmdstr = "/usr/sbin/pvresize " + _diskpart
        ebLogTrace("Executing cmd : %s"%(_cmdstr))
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        _out = _o.readlines()
        if _node.mGetCmdExitStatus() != 0:
            self.logDebugInfo(_out, _e)
            _detail_error = 'pvresize command failed in domU'
            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_PVRESIZE_FAIL'], _detail_error)
            return self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)
        if _eBoxCluCtrl.mCheckConfigOption('disable_lvm_snapshot_space','True'):
            _cmdstr = "/usr/sbin/lvresize --resizefs -l +100%FREE " + _filesystem
        else:
            _lvsize = float(_new_sizeGB) - 2 # 2 GB space for snapshot
            _cmdstr = "/usr/sbin/lvresize --resizefs -L" + str(_lvsize) + "G " + _filesystem
        ebLogTrace("Executing cmd : %s"%(_cmdstr))
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        _out = _o.readlines()
        if _node.mGetCmdExitStatus() != 0:
            self.logDebugInfo(_out, _e)
            _detail_error = 'lvresize command failed in domU'
            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_LVRESIZE_FAIL'], _detail_error)
            return self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)

        return 0

    def mExecuteDomUUpsizeStepsEncrypted(self, aDomU, aFilesystem, aNewSizeGB):
        """
        This method is very similar to mExecuteDomUUpsizeSteps(), but it contains
        a few different steps to accomplish the resize if the volume is
        encrypted using LUKS

        :param aDomU: The DomU where we will resize the fs aFilesystem
        :param aFilesystem: string representing the mountpoint/fs where the fs
            we will resize is mounted
        :param aNewSizeGB: the new size
        """
        _domU = aDomU
        _filesystem = aFilesystem
        _new_sizeGB = aNewSizeGB

        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_domU)
        _eBoxCluCtrl = self.__edp.mGetEbox()

        # Get info about block devices supporting our filesystem to resize
        _cmdstr = "/usr/bin/lsblk -p -r | /usr/bin/grep -B 3 " + _filesystem
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        ebLogTrace("Executing cmd : %s"%(_cmdstr))
        _out = _o.readlines()

        ebLogTrace("Command output : " + '\n'.join(_out))

        if _out is None:
            self.logDebugInfo(_out, _e)
            _detail_error = 'Could not perform filesystem check on ' + _domU + ' for filesystem ' + _filesystem
            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_FILE_SYS_CHECK_FAILED'], _detail_error)
            return self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)


        # Store disk/part/lv info to use later
        _imgdisk = _out[0].strip().split(' ')[0]
        _diskpart = _out[1].strip().split(' ')[0]
        _lvpath = _out[2].strip().split(' ')[0]

        ebLogInfo("image disk is : %s"%(_imgdisk))
        ebLogInfo("partition name is : %s"%(_diskpart))
        ebLogInfo("lv path is : %s"%(_lvpath))

        # Confirm LUKS keyapi is available before even start
        _keyapi_file = "/usr/lib/dracut/modules.d/99exacrypt/VGExaDbDisk.u02_extra_encrypted.img#LVDBDisk.key-api.sh"
        if not _node.mFileExists(_keyapi_file):
            _detail_error = f'the keyapi script {_keyapi_file} is not present in domU'
            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_KEYAPI_FAIL'], _detail_error)
            return self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)

        # Fix partition
        _cmdstr = f"/bin/echo 'Fix\nFix' | /usr/sbin/parted {_imgdisk} ---pretend-input-tty print"
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        ebLogTrace("Executing cmd : %s"%(_cmdstr))
        _out = _o.readlines()
        if _node.mGetCmdExitStatus() != 0:
            self.logDebugInfo(_out, _e)
            _detail_error = 'Parted command failed to fix table in domU'
            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_PARTED_CMD_FAIL'], _detail_error)
            return self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)

        # Resize partition
        _cmdstr = "/usr/sbin/parted -a none " + _imgdisk + " resizepart 1 100%"
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        ebLogTrace("Executing cmd : %s"%(_cmdstr))
        _out = _o.readlines()
        if _node.mGetCmdExitStatus() != 0:
            self.logDebugInfo(_out, _e)
            _detail_error = 'Parted command failed in domU'
            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_PARTED_CMD_FAIL'], _detail_error)
            return self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)


        # Resize PV
        _cmdstr = "/usr/sbin/pvresize " + _diskpart
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        ebLogTrace("Executing cmd : %s"%(_cmdstr))
        _out = _o.readlines()
        if _node.mGetCmdExitStatus() != 0:
            self.logDebugInfo(_out, _e)
            _detail_error = 'pvresize command failed in domU'
            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_PVRESIZE_FAIL'], _detail_error)
            return self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)

        # Resize LV
        if _eBoxCluCtrl.mCheckConfigOption('disable_lvm_snapshot_space','True'):
            _cmdstr = "/usr/sbin/lvresize -l +100%FREE " + _lvpath
        else:
            _lvsize = float(_new_sizeGB) - 2 # 2 GB space for snapshot
            _cmdstr = "/usr/sbin/lvresize -L " + str(_lvsize) + "G " + _lvpath
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        _out = _o.read()
        _err = _e.read()
        if _node.mGetCmdExitStatus() != 0:
            ebLogTrace("stdout: {_out}\nstderr: {_err}")

            # Ref, check if stdout/stderr includes
            _full_out = _out + _err
            if re.search("New\s+size\s+.*matches\s+existing\s+size", _full_out):
                ebLogInfo(f"LVresize failure detected to be caused by using same Target Size")
            else:
                _detail_error = 'lvresize command failed in domU'
                _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_LVRESIZE_FAIL'], _detail_error)


        # Resize LUKS Device
        try:
            # Try to get keyapi data
            _out_file = None
            _i, _o, _e = _node.mExecuteCmd(_keyapi_file)
            ebLogTrace("Executing cmd : %s"%(_cmdstr))
            _out = _o.readlines()
            if _out:
                _out_file = _out[0].strip()
            if _node.mGetCmdExitStatus() != 0:
                self.logDebugInfo(_out, _e)
                _detail_error = 'calling keyapi command failed in domU'
                _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_KEYAPI_FAIL'], _detail_error)
                return self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)


            _bin_cryptsetup = node_cmd_abs_path_check(_node, "cryptsetup", sbin=True)
            _cmdstr = f"{_bin_cryptsetup} resize {_filesystem} --key-file={_out_file} -v"
            _i, _o, _e = _node.mExecuteCmd(_cmdstr)
            ebLogTrace("Executing cmd : %s"%(_cmdstr))
            _out = _o.readlines()
            if _node.mGetCmdExitStatus() != 0:
                self.logDebugInfo(_out, _e)
                _detail_error = 'cryptsetup resize command failed in domU'
                _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_LUKSRESIZE_FAIL'], _detail_error)
                return self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)
        finally:
            if _out_file and _node.mFileExists(_out_file):
                ebLogWarn(f"Deleting keyapi {_out_file}")
                node_exec_cmd(_node, f"/bin/shred -fu {_out_file}")
            else:
                ebLogWarn(f"No keyapi to delete")

        # Resize Filsystem
        _fs_info = getMountPointInfo(_node, f"{_filesystem}")
        if _fs_info.fs_type == "xfs":
            _bin_xfs_growfs = node_cmd_abs_path_check(_node, "xfs_growfs", sbin=True)
            _cmdstr = (f"{_bin_xfs_growfs} {_fs_info.mount_point}")
            _i, _o, _e = _node.mExecuteCmd(_cmdstr)
            ebLogTrace("Executing cmd : %s"%(_cmdstr))
            _out = _o.readlines()
            if _node.mGetCmdExitStatus() != 0:
                self.logDebugInfo(_out, _e)
                _detail_error = 'filesystem resize command failed in domU'
                _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_FSRESIZE_FAIL'], _detail_error)
                return self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)

        elif _fs_info.fs_type == "ext4":
            _bin_resize2fs = node_cmd_abs_path_check(_node, "resize2fs", sbin=True)
            _cmdstr = f"{_bin_resize2fs} {_filesystem}"
            _i, _o, _e = _node.mExecuteCmd(_cmdstr)
            ebLogTrace("Executing cmd : %s"%(_cmdstr))
            _out = _o.readlines()
            if _node.mGetCmdExitStatus() != 0:
                self.logDebugInfo(_out, _e)
                _detail_error = 'filesystem resize command failed in domU'
                _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_FSRESIZE_FAIL'], _detail_error)
                return self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)

        return 0

    def mExecuteDom0ResizeSteps(self, aDom0, aDomU, aNewSizeGB, aImageName):
        _dom0 = aDom0
        _domU = aDomU
        _new_sizeGB = aNewSizeGB
        _image_name = aImageName

        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_dom0)
        _eBoxCluCtrl = self.__edp.mGetEbox()
        _xs_utils = _eBoxCluCtrl.mGetExascaleUtils()

        # For Exascale EDVs, resize the EDV first using ESCLI before
        # libvirt resize even for shrinking...
        # Ironically, since this code doesn't need to be run in ExaDB-XS
        # clusters because we cannot control the EDV size in those clusters,
        # we need to check if it is an ExaDB-XS cluster, but due to historical
        # reasons, the function name to check that is called "mIsExaScale".
        if _image_name.startswith('/dev/exc/') and not _eBoxCluCtrl.mIsExaScale():
            _volname = '_'.join(os.path.basename(_image_name).split('_')[:-1])
            _xs_utils.mResizeEDVVolume(_volname, f"{_new_sizeGB}g")
        
        ## No need to detatch disk before up upscale disk
        ebLogInfo("*** Resizing image " + _image_name + " on " + _dom0)
        _cmdstr = "virsh blockresize " + _domU + " " +_image_name + " --size " + str(_new_sizeGB) + "G" 
        #"qemu-img resize " + _image_name +  " " + str(_new_sizeGB) + "G"
        ebLogTrace("Executing cmd : %s"%(_cmdstr))
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        _out = _o.readlines()
        if _node.mGetCmdExitStatus() != 0:
            self.logDebugInfo(_out, _e)
            _detail_error = 'Could not resize image on ' + _dom0
            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_IMAGE_RESIZE'], _detail_error)
            return self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)

        return 0


    def mClusterPartitionResize(self, aOptions):

        #_e2fsPath is created to set path to extracted e2fsck binaries-Bug 36343848
        def _e2fsPath(aFilesystem, aNode=None):
            _node = aNode
            _filesystem = aFilesystem
            _fs = _filesystem.split("/")[-1]
            _e2fsckbinPath = "/usr/sbin/"
            if _fs == "VGExaDbDisk.u02_extra.img-LVDBDisk":
                _, _o, _ = _node.mExecuteCmd("export LD_LIBRARY_PATH=/opt/exacloud/fstools/usr/lib64;/opt/exacloud/fstools/usr/sbin/e2fsck -V")
                _rc = _node.mGetCmdExitStatus()
                if _rc == 0:
                    ebLogInfo("*** Check if e2fsprogs binaries are copied over")
                    _e2fsckbinPath = "export LD_LIBRARY_PATH=/opt/exacloud/fstools/usr/lib64;/opt/exacloud/fstools/usr/sbin/"

            return _e2fsckbinPath

        # This method will remove the files copied over for Bug 36343848
        def _rmFstools(fsbinPath=None, aNode=None):
            _e2fsckbinPath = fsbinPath
            _node = aNode
            _defpath = "/usr/sbin/"
            if _e2fsckbinPath != _defpath:
                ebLogInfo("*** Removing copied over e2fsprogs binaries in /opt/exacloud/fstools")
                _node.mExecuteCmd("rm -rf /opt/exacloud/fstools")

        ebLogInfo("*** ebCluManageDomUPartition:mClusterPartitionResize >>>")
        _options = aOptions
        # Get the cluctrl handle to fetch current details
        _eBoxCluCtrl = self.__edp.mGetEbox()
        _clu_utils = ebCluUtils(_eBoxCluCtrl)
        # Get the constants object for use in the scope of this function
        _constantsObj = self.__edp.mGetConstantsObj()

        _partitionData = self.__edp.mGetPartitionOperationData()
        _partitionData["Status"] = "Pass"
        _partitionData["ErrorCode"] = "0"

        _partition_name_key = _constantsObj._partitionname_key

        _inparams = {}
        _rc = self.__edp.mClusterParseInput(_options, _inparams)
        current_step = 0
        _percentage_increase = 0.0
        _lastNode = []
        step_list = ["EvaluateResources", "PartitionResize", "Complete"]
        if _rc == 0:
            _eBoxCluCtrl.mUpdateStatusOEDA(True, step_list[current_step], step_list,
                                       ' Partition resize operation for ' + _inparams[_partition_name_key])
            _eBoxCluCtrl.mUpdateStatus('Partition resize operation for ' + _inparams[_partition_name_key] + ' performing step ' + step_list[current_step])
            _dpairs = self.__edp.mGetDom0DomUpairs()
            shrink = 1
            _node_toUpdate_list = []  # list of node which will require resize
            max_used_space = 0
            existing_partition_info = {}
            image_names = {}
            _percentageStepSize = 20.0/len(_dpairs)
            for _dom0, _domU in _dpairs:
                ## 1. We fetch the size information of the mount-point to be resized from each node on the cluster
                ##    and perform checks if the same can be resized.
                _stepSpecificDetails = _clu_utils.mStepSpecificDetails("reshapeDetails", 'ONGOING', "OH reshape in progress", "","OH")
                _clu_utils.mUpdateTaskProgressStatus(_lastNode, _percentage_increase, "OH Reshape", "In Progress", _stepSpecificDetails)
                _percentage_increase = _percentage_increase + _percentageStepSize
                _lastNode.append(_domU)
                _rc, _this_node_infoobj = self.__edp.mClusterPartitionInfo2(_options, _inparams[_partition_name_key], _domU)
                if _rc != 0:
                    _detail_error = 'Could not fetch info for partition ' + _inparams[_partition_name_key] + ' on ' + _domU
                    _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_FETCHING_PARTITION_INFO'], _detail_error)
                    return self.__edp.mRecordError(gPartitionError['ErrorFetchingDetails'], "*** " + _detail_error)
                if max_used_space < int(_this_node_infoobj[_constantsObj._usedsizeGB_key]): 
                    max_used_space = int(_this_node_infoobj[_constantsObj._usedsizeGB_key])

                existing_partition_info[_domU] = _this_node_infoobj
                _filesystem = _this_node_infoobj[_constantsObj._filesystem_key]
                with connect_to_host(_domU, get_gcontext()) as _node:

                    ebLogInfo('*** Fetching raw device size of %s on Node %s' %(_filesystem, _domU))
                    _cmdstr = '/sbin/fdisk -l \'' + _filesystem + '\' | /usr/bin/grep Disk'
                    ## Sample output for "/sbin/fdisk -l /dev/xvdg | grep Disk"
                    ##   [root@scas07adm03vm04 ~]#  /sbin/fdisk -l /dev/xvdg | grep Disk
                    ##   Disk /dev/xvdg: 64.4 GB, 64424509440 bytes
                    ##   Disk identifier: 0x00000000
                    ebLogInfo("Executing cmd : %s"%(_cmdstr))
                    _i, _o, _e = _node.mExecuteCmd(_cmdstr)
                    _out = _o.readlines()
                    if _out is None:
                        self.logDebugInfo(_out, _e)
                        _detail_error = 'Could not fetch fdisk info for partition ' + _inparams[_partition_name_key] + ' on ' + _domU
                        _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_FETCHING_PARTITION_INFO'], _detail_error)
                        return self.__edp.mRecordError(gPartitionError['ErrorFetchingDetails'], "*** " + _detail_error)

                    ebLogInfo("Command output : " + '\n'.join(_out))

                    # Sample output of cmd: /sbin/fdisk -l /dev/xvdh | grep Disk
                    # Disk /dev/xvdh: 48.3 GB, 48318382080 bytes, 94371840 sectors
                    _partitionAttrs = _out[0].strip().replace(","," ").split()  ## Take 1st line, remove "," by spaces, create list of output
                    _index=_partitionAttrs.index("bytes") ## get the index of the "bytes" in the list
                    # From above, size: 48318382080 bytes
                    if _index > 0:
                        _partitionsize_bytes_domU = _partitionAttrs[_index - 1].strip() ## look for the value just before the string bytes
                    else:
                        _detail_error = 'Could not read the disk size in bytes for partition ' + _inparams[_partition_name_key] + ' on ' + _domU
                        _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_READING_DISKSIZE'], _detail_error)
                        return self.__edp.mRecordError(gPartitionError['ErrorFetchingDetails'], "*** " + _detail_error)

                    ebLogInfo("Fdisk info for FS %s on host %s : %s"%(_filesystem, _domU, _partitionAttrs))

                    ## Save size for Dom U to cross-verify against size on Dom 0
                    ## From above, size: 48318382080 bytes 
                    _devname = _filesystem.split('/')[-1]

                if self.__edp.mClusterPartitionTargetDiff(_this_node_infoobj[_constantsObj._totalsizeGB_key], _inparams[_constantsObj._newsizeGB_key]):
                    _node_toUpdate_list.append(_domU)

                with connect_to_host(_dom0, get_gcontext()) as _thisNode:

                    # Get disk image/device path
                    _fs = _inparams[_partition_name_key]
                    _cmdstr = f"/bin/virsh domblklist {_domU} | /bin/grep -e /{_fs} -e _{_fs}_"
                    _, _image_name = node_exec_cmd_check(_thisNode, _cmdstr).stdout.split()
                    image_names[_domU] = _image_name

                    if not _eBoxCluCtrl.mIsExaScale():

                        _cmdstr = "/usr/bin/ls -l " + _image_name
                        ebLogInfo("Executing cmd : %s"%(_cmdstr))
                        _i, _o, _e = _thisNode.mExecuteCmd(_cmdstr)
                        _out = _o.readlines()
                        if _out is None:
                            self.logDebugInfo(_out, _e)
                            _detail_error = 'Could not retrieve device size for partition ' + _inparams[_partition_name_key] + ' from filesystem on ' + _dom0
                            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_READING_DEVICE_INFO'], _detail_error)
                            return self.__edp.mRecordError(gPartitionError['ErrorFetchingDetails'], "*** " + _detail_error)


                        ebLogInfo("Command output : " + '\n'.join(_out))
                        _partitionsize_bytes_dom0 = _out[0].strip()
                        _partitionsize_bytes_dom0 = " ".join(_partitionsize_bytes_dom0.split())
                        _partitionsize_bytes_dom0 = _partitionsize_bytes_dom0.split()[4]

                        if _partitionsize_bytes_domU != _partitionsize_bytes_dom0:
                            ebLogWarn(
                                "*** Partition " + _inparams[_partition_name_key] + " has inconsistent size Dom 0 [" + _partitionsize_bytes_dom0 +
                                    "] and DomU [" + _partitionsize_bytes_domU + "]")
                        ##TODO Finding a deviation of few kb btw dom0 and domU. This needs more digging to figure this out. !



            if int(_inparams[_constantsObj._newsizeGB_key]) > int(_this_node_infoobj[_constantsObj._totalsizeGB_key]):
                shrink = 0


            ## Shrink/Expand only if change in value is by at least 2% in any of the  node
            if  not _node_toUpdate_list:
                ebLogInfo("*** New partition size very close to original size. No resize done. Task completed")
                return 0

            if shrink == 1:
                ## Shrink only if it will leave >= 10% of free space after resize
                expected_fspace_on_resize = int(_inparams[_constantsObj._newsizeGB_key]) - int(max_used_space)
                if expected_fspace_on_resize < 0:
                    _detail_error = 'Partition ' + _inparams[_partition_name_key] + ' cannot be modified as it is smaller than current utilization'
                    _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_USAGE_SIZE_MORE'], _detail_error)
                    return self.__edp.mRecordError(gPartitionError['NonModifiable'], "*** " + _detail_error)
                percent_fspace_on_resize = float(expected_fspace_on_resize * 100) / int(_inparams[_constantsObj._newsizeGB_key])
                if percent_fspace_on_resize < 10.0:
                    _detail_error = 'Partition ' + _inparams[_partition_name_key] + ' cannot be modified as it will leave less than 10% of free space after resize'
                    _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_LESS_FREE_SPACE'], _detail_error)
                    return self.__edp.mRecordError(gPartitionError['NonModifiable'], "*** " + _detail_error)

            current_step += 1

            _eBoxCluCtrl.mUpdateStatusOEDA(True, step_list[current_step], step_list,
                                       ' Partition resize operation for ' + _inparams[_partition_name_key])
            _eBoxCluCtrl.mUpdateStatus('Partition resize operation for ' + _inparams[_partition_name_key] + ' performing step ' + step_list[current_step])
            _percentage_increase = 20
            _percentageStepSize= 79.0/len(_dpairs)
            for _dom0, _domU in _dpairs:
                ebLogInfo("*** Working on resize operation for (Dom-0, Dom-U) : (%s, %s)"%(_dom0, _domU))
                _stepSpecificDetails = _clu_utils.mStepSpecificDetails("reshapeDetails", 'ONGOING', "OH reshape in progress", "","OH")
                _clu_utils.mUpdateTaskProgressStatus(_lastNode, _percentage_increase, "OH Reshape", "In Progress", _stepSpecificDetails)
                percentage_increase = _percentage_increase + _percentageStepSize
                _lastNode.append(_domU)
                if _domU not in _node_toUpdate_list:
                    if _eBoxCluCtrl.mCheckIfCrsDbsUp(_domU):
                        ebLogInfo("*** node already at the resize Value. Continuing with next node")
                        continue
                _this_node_infoobj = existing_partition_info[_domU]
                _filesystem = _this_node_infoobj[_constantsObj._filesystem_key]
                ebLogInfo("partition size from %s -> %s" %(_this_node_infoobj[_constantsObj._totalsizeGB_key], _inparams[_constantsObj._newsizeGB_key]))    
                _tfa_status = 0 # value 0 is for no tfactl. use this variable to identify the running status of tfa and tfactl script location
                # value 1 for the tfactl at GIHome/bin/tfactl
                # value 2 for the tfactl at /usr/bin/tfactl
                # and start it if needed after resize.

                _oracleHome_in_u02 = False # added for the case where oracle home is on u02 partition
                _isDatabaseInstanceRunning = False # added for the case where no active database instances detected
                _gi_home, _, _ = _eBoxCluCtrl.mGetOracleBaseDirectories(_domU)
                _db_List = _eBoxCluCtrl.mGetActiveDbInstances(_domU)
                if len(_db_List):
                    _isDatabaseInstanceRunning = True
                    ebLogWarn(f'*** Active database instances {_db_List} have been detected on : {_domU}')
                else:
                    ebLogWarn(f'*** There are NO active database instances detected on : {_domU}')

                ## We dont have to stop cluster services if disk is going to be expanded.. live expansion is possible !
                if shrink == 1 and _inparams[_partition_name_key] == 'u02' and _gi_home is not None:
                    ebLogInfo("*** Resize(Shrink) triggered for u02; will stop cluster services if running")
                    ebLogInfo("*** Checking cluster services on " + _domU)
                    with connect_to_host(_domU, get_gcontext()) as _node:
                        _crsctl_path = _gi_home
                        _oracleHome_in_u02 = True if _crsctl_path.split('/')[1].lower()=='u02' else False
                        _crs_home = _crsctl_path
                        _rhphelper = _crs_home
                        _rhphelper += "/srvm/admin/rhphelper"
                        _tfactl_path = _crsctl_path
                        _crsctl_path += "/bin/crsctl"
                        _tfactl_path += "/bin/tfactl"
                        _cmdstr = "/usr/bin/ls -l " + _tfactl_path
                        ebLogTrace("Executing cmd : %s"%(_cmdstr)) 
                        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
                        if _node.mGetCmdExitStatus() != 0:
                            _tfa_status = 2
                            _tfactl_path = "/usr/bin/tfactl"
                        else:
                            _tfa_status = 1

                        ebLogInfo("*** TFACTL script path is %s" %(_tfactl_path)) 
                        ebLogInfo("*** Checking TFA services on " + _domU)
                        _cmdstr = _tfactl_path + " -check"
                        ebLogTrace("Executing cmd : %s"%(_cmdstr))
                        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
                        _out = _o.readlines()
                        if _node.mGetCmdExitStatus() != 0:
                            _tfa_status = 0
                            self.logDebugInfo(_out, _e)

                        ebLogInfo("*** Stopping TFA services on " + _domU)
                        _cmdstr = _tfactl_path + " stop"
                        ebLogTrace("Executing cmd : %s"%(_cmdstr))
                        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
                        _out = _o.readlines()
                        _rc = _node.mGetCmdExitStatus()
                        if _rc not in [0,11]:
                            self.__edp.logDebugInfo(_out, _e)
                            _detail_error = 'Could not stop TFA services on ' + _domU
                            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_TFA_STOP'], _detail_error)
                            self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)

                        _cmdstr = "/usr/bin/ls -l " + _rhphelper
                        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
                        if _node.mGetCmdExitStatus() == 0:
                            ebLogInfo('*** rhphelper found on the host')
                            _cmdstr = _crsctl_path + " query crs activeversion | /usr/bin/cut -d[ -f2 | /usr/bin/cut -d] -f1"
                            _i, _o, _e = _node.mExecuteCmd(_cmdstr)
                            _out = _o.readlines()
                            if _out is None:
                                #Lets not error out ,since this this not a hard error.
                                ebLogWarn("Could not fetch Oracle version")
                            else:
                                _ora_ver = _out[0].strip()
                                ebLogInfo("*** Draining services using rhphelper")
                                _cmdstr = _rhphelper + " " +_crs_home + " " + _ora_ver + " -stopInstance -relocate_service 300 -relocate_racone NOT_SPECIFIED NOT_SPECIFIED"
                                ebLogInfo("Executing cmd : %s"%(_cmdstr))
                                _i, _o, _e = _node.mExecuteCmd(_cmdstr)
                                _out = _o.readlines()
                                if _node.mGetCmdExitStatus() != 0:
                                    #Lets not error out ,since this this not a hard error.
                                    ebLogWarn("phphelper command failed")
                                    self.logDebugInfo(_out, _e)

                        ebLogInfo("*** Stopping cluster services on " + _domU)
                        _cmdstr = _crsctl_path + " stop cluster -n " + _domU.split(".")[0]
                        ebLogTrace("Executing cmd : %s"%(_cmdstr))
                        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
                        _out = _o.readlines()
                        if _node.mGetCmdExitStatus() != 0:
                            self.logDebugInfo(_out, _e)
                            _detail_error = 'Could not stop cluster services on ' + _domU
                            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_CRS_STOP'], _detail_error)
                            self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)
                        if len(_out):
                            ebLogVerbose("Command output : " + '\n'.join(_out))
                        if _oracleHome_in_u02:
                            ebLogInfo("*** Stopping crs on " + _domU)
                            _cmdstr = _crsctl_path + " stop crs -f "
                            ebLogTrace("Executing cmd : %s"%(_cmdstr))
                            _i, _o, _e = _node.mExecuteCmd(_cmdstr)
                            _out = _o.readlines()
                            if _node.mGetCmdExitStatus() != 0:
                                self.logDebugInfo(_out, _e)
                                self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'],
                                    "*** Could not stop crs on " + _domU)
                            _cmdstr = "/usr/sbin/advmutil blogtext -c force_reopen"
                            ebLogInfo('*** Executing Command: %s'%(_cmdstr))
                            _node.mExecuteCmdLog(_cmdstr)
                            if len(_out):
                                ebLogVerbose("Command output : " + '\n'.join(_out))

                _this_node_infoobj = existing_partition_info[_domU]
                _filesystem = _this_node_infoobj[_constantsObj._filesystem_key] 

                # Check if volume is encrypted
                with connect_to_host(_domU, get_gcontext()) as _vm_node:
                    if getMountPointInfo(_vm_node, f"{_filesystem}").is_luks:
                        ebLogInfo(f"Filesystem {_filesystem} is LUKS encrypted in {_domU}")
                        _is_encrypted = True
                    else:
                        ebLogTrace(f"Filesystem {_filesystem} is NOT LUKS encrypted in {_domU}")
                        _is_encrypted = False

                if shrink == 1:
                    ebLogInfo("*** Shrinking partition : " + _inparams[_partition_name_key])


                    _rc = self.__edp.mExecuteDomUUmountPartition(_domU,
                            _inparams[_partition_name_key])
                    if _rc != 0:
                        return _rc

                    if _is_encrypted:
                        _rc = self.mExecuteDomUDownsizeStepsEncrypted(_domU,
                            _this_node_infoobj[_constantsObj._filesystem_key],
                            _inparams[_constantsObj._newsizeGB_key])
                    else:
                        _rc = self.mExecuteDomUDownsizeSteps(_domU,
                            _this_node_infoobj[_constantsObj._filesystem_key],
                            _inparams[_constantsObj._newsizeGB_key])

                    if _rc != 0:
                        return _rc

                    _rc = self.mExecuteDom0ResizeSteps(_dom0, _domU,
                            _inparams[_constantsObj._newsizeGB_key], image_names[_domU])
                    if _rc != 0:
                        return _rc
                else:
                    ebLogInfo("*** Increasing partition : " + _inparams[_partition_name_key])

                    _rc = self.mExecuteDom0ResizeSteps(_dom0, _domU, \
                            _inparams[_constantsObj._newsizeGB_key],
                            image_names[_domU])
                    if _rc != 0:
                        return _rc

                    if _is_encrypted:
                        _rc = self.mExecuteDomUUpsizeStepsEncrypted(_domU,
                            _this_node_infoobj[_constantsObj._filesystem_key],
                            _inparams[_constantsObj._newsizeGB_key])
                    else:
                        _rc = self.mExecuteDomUUpsizeSteps(_domU,
                            _this_node_infoobj[_constantsObj._filesystem_key],
                            _inparams[_constantsObj._newsizeGB_key])

                    if _rc != 0:
                        return _rc


                
                with connect_to_host(_domU, get_gcontext()) as _node:
                    ebLogInfo('*** Fetching raw device size of %s on Node %s after resize' %(_filesystem, _domU))
                    _cmdstr = '/sbin/fdisk -l \'' + _filesystem + '\' | /usr/bin/grep Disk'
                    ebLogTrace("Executing cmd : %s"%(_cmdstr))
                    _i, _o, _e = _node.mExecuteCmd(_cmdstr)
                    _out = _o.readlines()
                    if _out is None:
                        self.logDebugInfo(_out, _e)
                        _detail_error = 'Could not fetch fdisk info for partition ' + _inparams[_partition_name_key] + ' on ' + _domU
                        _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_IMG_FILE_CHECK_FAILED'], _detail_error)
                        return self.__edp.mRecordError(gPartitionError['ErrorFetchingDetails'], "*** " + _detail_error)

                    if len(_out):
                        ebLogVerbose("Command output : " + '\n'.join(_out))
                    # Sample output of cmd: /sbin/fdisk -l /dev/xvdh | grep Disk
                    # Disk /dev/xvdh: 48.3 GB, 48318382080 bytes, 94371840 sectors
                    _partitionAttrs = _out[0].strip().replace(","," ").split()  ## Take 1st line, remove "," by spaces, create list of output
                    _index=_partitionAttrs.index("bytes") ## get the index of the "bytes" in the list
                    # From above, size: 48318382080 bytes
                    if _index > 0:
                        _partitionsize_bytes_domU = _partitionAttrs[_index - 1].strip() ## look for the value just before the string bytes
                    else:
                        _detail_error = 'Could read the disk size in bytes for partition ' + _inparams[_partition_name_key] + ' on ' + _domU
                        _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_IMG_FILE_CHECK_FAILED'], _detail_error)
                        return self.__edp.mRecordError(gPartitionError['ErrorFetchingDetails'], "*** " + _detail_error)

                    _new_size_bytes = int(_inparams[_constantsObj._newsizeGB_key]) * 1024 * 1024 * 1024

                    ebLogInfo('_new_size_bytes: %d, _partitionsize_bytes_domU: %d' %(int(_new_size_bytes), int(_partitionsize_bytes_domU)))
                    ## There should not be offset of more than 2% after resize
                    if abs(int(_new_size_bytes) - int(_partitionsize_bytes_domU)) * 100.0 / float(_partitionsize_bytes_domU) > 2.0:
                        _deviation = abs(int(_new_size_bytes) - int(_partitionsize_bytes_domU)) * 100.0 / float(_partitionsize_bytes_domU)
                        ebLogWarn("*** Disk not accurately resized on " + _domU + ". It has deviation of : " +str(_deviation) + "% from requested size.")
                    #TODO : This deviation shold be a hard failure and debugged further instead of just logging a warning message.

                    if shrink != 1:
                        _node.mDisconnect()
                        ebLogInfo("*** DONE with resize operation for (Dom-0, Dom-U) : (%s, %s)"%(_dom0, _domU))
                        continue

                    ebLogInfo("*** Performing filesystem check of " + _filesystem + " on " + _domU + " after resize")
                    _e2fsckbinPath = _e2fsPath(_filesystem, _node)
                    _cmdstr = _e2fsckbinPath + "e2fsck -f " + _filesystem
                    ebLogTrace("Executing cmd : %s"%(_cmdstr))
                    _i, _o, _e = _node.mExecuteCmd(_cmdstr)
                    _out = _o.readlines()
                    if _out is None:
                        self.logDebugInfo(_out, _e)
                        _detail_error = 'Could not perform filesystem check on ' + _domU + ' for filesystem ' + _filesystem
                        _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_FILE_SYS_CHECK_FAILED'], _detail_error)
                        return self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)
                    if len(_out):
                        ebLogVerbose("Command output : " + '\n'.join(_out))

                    for outentry in _out:
                        if re.search("errors", outentry):
                            _detail_error = 'Errors found in filesystem check on ' + _domU + ' for filesystem ' + _filesystem
                            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_FILE_SYS_CHECK_FAILED'], _detail_error)
                            return self.__edp.mRecordError(gPartitionError['InvalidState'], "*** " + _detail_error)
                    #Remove e2fsck binaries copied over for 36343848
                    _rmFstools(_e2fsckbinPath, _node)

                    ebLogInfo("*** Mounting filesystem " + _filesystem + " on " + _domU + " after resize")
                    _cmdstr = "/usr/bin/mount " + _this_node_infoobj[_constantsObj._filesystem_key] + " /" + _inparams[_partition_name_key]
                    ebLogTrace("Executing cmd : %s"%(_cmdstr))
                    _i, _o, _e = _node.mExecuteCmd(_cmdstr)
                    _out = _o.readlines()
                    _exitstatus = _node.mGetCmdExitStatus()
                    # Escape error out if the cmd executed with success or if the file system was 
                    # already mounted (exit status: 32).
                    if _exitstatus != 0 and _exitstatus != 32:
                        self.logDebugInfo(_out, _e)
                        _detail_error = 'Could not mount filesystem ' + _inparams[_partition_name_key] + ' on ' + _domU
                        _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_MOUNTING_FILE_SYS'], _detail_error)
                        return self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)

                    if _inparams[_partition_name_key] == 'u02' and _gi_home is not None:
                        ebLogInfo("*** Resize was done for u02; will start cluster services")
                        ebLogInfo("*** Attempting on " + _domU)
                        _crsctl_path = _gi_home
                        _tfactl_path = _crsctl_path
                        _crsctl_path += "/bin/crsctl"
                        _tfactl_path += "/bin/tfactl"
                        if _tfa_status == 2:
                            _tfactl_path = "/usr/bin/tfactl"

                        if _oracleHome_in_u02:
                            ebLogInfo("*** Starting crs on " + _domU)
                            _cmdstr = _crsctl_path + " start crs "
                            ebLogTrace("Executing cmd : %s"%(_cmdstr))
                            _i, _o, _e = _node.mExecuteCmd(_cmdstr)
                            _out = _o.readlines()
                            if _node.mGetCmdExitStatus() != 0:
                                self.logDebugInfo(_out, _e)
                                self.__edp.mRecordError(gPartitionError['ErrorRunningRemoteCmd'],
                                    "*** Could not start crs on " + _domU)

                            if len(_out):
                                ebLogVerbose("Command output : " + '\n'.join(_out))

                        ebLogInfo("*** Starting cluster services on " + _domU)
                        _cmdstr = _crsctl_path + " start cluster -n " + _domU.split(".")[0]
                        ebLogTrace("Executing cmd : %s"%(_cmdstr))
                        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
                        _out = _o.readlines()
                        _exitstatus = _node.mGetCmdExitStatus()
                        if _out is None and _exitstatus != 1:
                            self.logDebugInfo(_o, _e)
                            _detail_error = 'Could not start cluster services on ' + _domU
                            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_CRS_START'], _detail_error)
                            return self.__edp.mRecordError(gPartitionError['ErrorFetchingDetails'], "*** " + _detail_error)

                        _tvl = _eBoxCluCtrl.mCheckConfigOption('crs_timeout')
                        if _tvl is not None:
                            _timeout_crs = int(_tvl) * 60
                        else:
                            _timeout_crs = 60*60
                        #Default of 60 minute timeout

                        _total_time = 0
                        _check_itr  = 5

                        while _total_time < _timeout_crs:
                            ebLogInfo("*** Waiting for cluster services to come up...")
                            _crs_started = _eBoxCluCtrl.mCheckCrsUp(_domU)
                            if _crs_started:
                                break
                            time.sleep(_check_itr)
                            _total_time += _check_itr

                        if _crs_started:
                            ebLogInfo("*** CRS has come up")
                        else:
                            ebLogError("*** CRS has failed to come up")
                            _detail_error = 'Could not start cluster services on ' + _domU
                            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_CRS_START'], _detail_error)
                            return self.__edp.mRecordError(gPartitionError['ErrorFetchingDetails'], "*** " + _detail_error)
                        

                        if _isDatabaseInstanceRunning:
                            while _total_time < _timeout_crs:
                                ebLogInfo("*** Waiting for DB to come up...")
                                _db_started = _eBoxCluCtrl.mCheckDBIsUp(_domU)
                                if _db_started:
                                    break
                                time.sleep(_check_itr)
                                _total_time += _check_itr

                            if _db_started:
                                ebLogInfo("*** DB has come up")
                            else:
                                ebLogError("*** DB has failed to come up")
                                _detail_error = 'Could not start DB on ' + _domU
                                _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_DB_START'], _detail_error)
                                return self.__edp.mRecordError(gPartitionError['ErrorFetchingDetails'], "*** " + _detail_error)
                        else:
                            ebLogWarn(f'*** Skipping the DB check as NO active database instances were found on {_domU} prior to the reshape.')


                        if _tfa_status != 0:
                            ebLogInfo("*** Starting TFA services on " + _domU)
                            _cmdstr = _tfactl_path + " start"
                            ebLogTrace("Executing cmd : %s"%(_cmdstr))
                            _i, _o, _e = _node.mExecuteCmd(_cmdstr)
                            _out = _o.readlines()
                            _exitstatus = _node.mGetCmdExitStatus()
                            if _exitstatus != 0:
                                self.logDebugInfo(_o, _e)
                                ebLogWarn("*** Could not start TFA services on " + _domU)
                                _partitionData["Log"] = "Could not start TFA services on " + _domU
                                self.__edp._mUpdateRequestData(_options, _partitionData, _eBoxCluCtrl)


                        if len(_out):
                            ebLogVerbose("Command output : " + '\n'.join(_out))


                    ebLogInfo("*** DONE with resize operation for (Dom-0, Dom-U) : (%s, %s)"%(_dom0, _domU))

            # end for    

        else:
            _detail_error = 'Returning due to input args related error' 
            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['INVALID_INPUT_PARAMETER'], _detail_error)
            ebLogError(_detail_error)
            return _rc

        current_step += 1
        _eBoxCluCtrl.mUpdateStatusOEDA(True, step_list[current_step], step_list,
                                       ' Partition resize operation for ' + _inparams[_partition_name_key])
        _eBoxCluCtrl.mUpdateStatus('Partition resize operation for ' + _inparams[_partition_name_key] + ' performing step ' + step_list[current_step]) 
        ebLogInfo("*** ebCluManageDomUPartition:mClusterPartitionResize <<<")
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("reshapeDetails", 'DONE', "OH reshape completed", "","OH")
        _clu_utils.mUpdateTaskProgressStatus(_lastNode, 100, "OH Reshape", "DONE", _stepSpecificDetails)
        return 0


