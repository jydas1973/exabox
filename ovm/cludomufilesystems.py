#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/ovm/cludomufilesystems.py /main/45 2025/11/14 17:04:47 scoral Exp $
#
# cludomufilesystems.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      cludomufilesystems.py - Utilities to resize DomU filesystems.
#
#    DESCRIPTION
#      This module includes several functions and methods to obtain
#      information about the currently known ExaData DomU filesystems,
#      along with utilities to resize them.
#
#    NOTES
#      None.
#
#    MODIFIED   (MM/DD/YY)
#    scoral      11/13/25 - Bug 38648866 - Added support of EDV volumes for
#                           Exascale clusters.
#    rajsag      10/23/25 - bug 38484985 - exascale- exacloud: add vm to
#                           exascale cluster with exascale images failed
#    remamid     09/29/25 - Add default snapshot space 2GB for each filesystem Bug
#                           38453991
#    gojoseph    09/10/25 - Bug 38350052 Exclude nfs fstype while df command
#                           execution to avoid hang
#    bhpati      07/10/25 - Bug 37997054 - Handle fsresize if more than 1 pv 
#                            are assigned to VG
#    nelango     05/20/25 - Bug 37683920 - Retry lsblk cmd while getting last
#                           partition device path
#    prsshukl    04/12/25 - Bug 37820151 - EXACS:25.2.1:TC1:RESHAPE VM CLUSTER
#                           FAILING:ERROR WHILE PROCESSING MDISPATCHCLUSTER IN
#                           AGENT[REQUEST: VM_CMD](FAILED TO PING TARGET
#                           NODE/CELL)
#    scoral      04/04/25 - 37788647: Replace "virsh attach-disk" with
#                           "vm_maker --attach --disk-image"
#    jfsaldan    04/03/25 - Bug 37754014 - EXADB-XS-PP: ERRORS REPORTED AT THE
#                           STEP OF EXASCALE_COMPLETE DURING VMC PROVISION
#    dekuckre    03/27/25 - 37740767: Updated attach_dom0_disk_image
#    scoral      03/20/25 - Bug 37736043 - Added two optional parameters to
#                           'attach_dom0_disk_image' to allow changing the
#                           Cache and IO policies in KVM guests.
#    scoral      02/27/25 - Bug 37555450 - Resize the Dom0 image file only with
#                           the needed size for the LVs.
#    remamid     02/25/25 - Modify shutdown_domu to list only running VMs
#                           before shutting them down Bug 37630591
#    bhpati      02/21/25 - Bug 37609714 - skip grid filesystem check if it
#                           does not exist during filesystem resize
#    rajsag      02/03/25 - Enh 37508596 exacloud | postginid
#                           expand_domu_filesystem runs customer fs resize
#                           sequentially on each vm taking close to 4 minutes
#                           more in large clusters | improve large cluster
#                           provisioning time
#    asrigiri    09/19/24 - Bug 36981061 - EXACC:LOCAL FS RESIZE FETCHES ALL FS
#                           DETAILS INCLUDING NFS MOUNTS.
#    jfsaldan    07/19/24 - Enh 36776061 - EXACS EXACLOUD OL8 FS ENCRYPTION :
#                           ADD SUPPORT TO RESIZE AN ENCRYPTED U01 DISK
#    scoral      06/17/24 - Bug 36736995 - Now we skip the filesyste resize if
#                           the filesystem does not exist.
#    scoral      06/04/24 - Bug 36494126 - Now resizing a filesystem with two
#                           LVs makes the LVs sizes match after the resize.
#    prsshukl    05/20/24 - Bug 36630536 - EXACC:BB:23.3.1.3.0:CREATE
#                           CLUSTER:FAILS IN INSTALL CLUSTER STEP WITH ERROR
#                           "NO MORE AVAILABLE PCI SLOTS
#    pbellary    05/03/24 - Bug 36557394 - NODE RECOVERY FAILED AT POSTGINID STEP FOR CUSTOM GI-HOME 
#    scoral      04/04/23 - Bug 36482483 - Introduce an optional parameter
#                           use_defaults in get_max_domu_filesystem_sizes.
#    jfsaldan    09/01/23 - Bug 35759673 - EXACS:23.4.1:XEN:FILE SYSTEM
#                           ENCRYPTION:SKIP RESIZE OF DOM0 IMAGE IF FS CREATED
#                           ON NON-LVM PARTITION
#    scoral      08/25/23 - Implemented perform_dom0_resize in
#                           expand_domu_filesystem
#    joysjose    07/25/23 - Bug 35632032 : To ignore filesystems payload
#                           parameter if it is null
#    scoral      06/30/23 - Enh 35359902 - Now we return a result JSON in
#                           expand_domu_filesystem with a summary of the
#                           resize.
#                           Now expand_domu_filesystem won't throw an exception
#                           if the resize of any filesystem failed, if that is
#                           the case the reason of the failure will be included
#                           in the JSON result.
#                           Now we can also resize the /crashfiles filesystem
#                           in KVM environments.
#                           Now start_domu can accept a condition to wait
#                           before continue and we wait for systemd-analyze in
#                           resize_disk_image_for_filesystem.
#                           Now we can detect if the secondary logical volume
#                           is whether Sys1 or Sys2, or Var1 or Var2 and we
#                           automatically detect if it has an inner filesystem
#                           to resize.
#    jfsaldan    06/30/23 - XbranchMerge jfsaldan_bug-35545832 from
#                           st_ecs_22.2.1.0.0
#    scoral      06/23/23 - Bug 35502608 - Implemented
#                           fill_disk_with_lvm_partition
#    jfsaldan    06/28/23 - Bug 35545832 - EXACS:22.2.1:DROP4:FILE SYSTEM
#                           ENCRYPTION:XEN:PROVISIONING FAILING AT POSTGI_NID
#                           STEP--U02 RESIZE FAILS
#    scoral      05/26/23 - Bug 35426339 - Fixed non-LVM based filesystems
#                           resize.
#                           Now we take the disk image file size as the
#                           filesystem size for non-LVM based filesystems.
#                           Bug 35423276 - Added support for floating point
#                           quantities in parse_size function.
#    scoral      03/21/23 - Enh 34734317 - Included the filesystem free size in
#                           the ebNodeFilesystemInfo structure.
#    scoral      01/05/23 - Bug 34897464 - Included the partition table type in
#                           the ebDiskImageInfo struct.
#    scoral      09/26/22 - Enh 34639458 - Attach disk image file even if the
#                           DomU is down.
#    scoral      05/24/22 - Enh 34176024 - Add support to /home and obtain
#                           sizes from payload.
#    scoral      08/30/21 - Creation
#

import math
import re
import os
import time
import json
import string
import base64
from enum import Enum
from typing import (
    Callable,
    Dict,
    List,
    NamedTuple,
    Optional,
    TYPE_CHECKING,
    Sequence
)
from datetime import datetime
from exabox.core.Node import exaBoxNode
from exabox.utils.node import (
    connect_to_host,
    node_cmd_abs_path,
    node_cmd_abs_path_check,
    node_exec_cmd,
    node_exec_cmd_check,
    node_read_text_file,
    node_write_text_file
)
from exabox.core.Error import ExacloudRuntimeError
from exabox.log.LogMgr import (
    ebLogDiag,
    ebLogWarn,
    ebLogInfo,
    ebLogDebug,
    ebLogError,
    ebLogVerbose,
    ebLogTrace
)
from exabox.core.Context import get_gcontext
from exabox.BaseServer.AsyncProcessing import (
    ProcessManager, 
    ProcessStructure, 
    TimeoutBehavior, 
    ExitCodeBehavior
)

if TYPE_CHECKING:
    from exabox.ovm.clucontrol import exaBoxCluCtrl
else:
    exaBoxCluCtrl = object  # pylint: disable=invalid-name



VM_MAKER = '/opt/exadata_ovm/vm_maker'



################################
### DATA TYPES AND CONSTANTS ###
################################


KIB: int = 2 ** 10
MIB: int = 2 ** 20
GIB: int = 2 ** 30
TIB: int = 2 ** 40


class ebDomUFilesystem(Enum):
    ROOT            = '/'
    U01             = '/u01'
    U02             = '/u02'
    GRID            = 'grid'
    HOME            = '/home'
    TMP             = '/tmp'
    VAR             = '/var'
    VAR_LOG         = '/var/log'
    VAR_LOG_AUDIT   = '/var/log/audit'
    CRASHFILES      = '/crashfiles'


class ebDomUFSResizeMode(Enum):

    # Regular filesystem resize. If the filesystem includes an extra logical
    # volume for reserved operations (such as / or /var), that logical volume
    # will also be resized with the same amount of space specified for the 
    # main filesystem, so that both local volumes sizes are always the same.
    NORMAL          = 0

    # If the filesystem includes an extra logical volume for reserved
    # operations (such as / or /var), we only resize the filesystem of the
    # main volume, ignoring the extra logical volume. Otherwise, it will be
    # the same as NORMAL resize.
    # NOTE: It's is highly recommended that both volumes are always the exact
    # same size, so this resize mode is only recommended for fixing the size
    # of the main volume when it's smaller than the reserved volume.
    FST_VOL_ONLY    = 1

    # If the filesystem includes an extra logical volume for reserved
    # operations (such as / or /var), we only resize the reserved logical
    # volume, ignoring the main volume and the filesystem. Otherwise, it will
    # be the same as NORMAL resize.
    # NOTE: It's is highly recommended that both volumes are always the exact
    # same size, so this resize mode is only recommended for fixing the size
    # of the reserved volume when it's smaller than the main volume.
    SND_VOL_ONLY    = 2

    # Resizes only the logical volume without resizing the filesystem.
    # Useful for filesystem encryption.
    LV_ONLY         = 3

    # Resizes the volume group only without resizing the logical volume nor
    # the filesystem.
    # Useful for reserving space for LVM snapshots.
    VG_ONLY         = 4


XEN_DOMU_FILESYSTEMS: Sequence[ebDomUFilesystem] = (
    ebDomUFilesystem.ROOT,
    ebDomUFilesystem.U01,
    ebDomUFilesystem.U02,
    ebDomUFilesystem.GRID
)


FS_WITH_DUPLICATED_VOLUME: Sequence[ebDomUFilesystem] = (
    ebDomUFilesystem.ROOT,
    ebDomUFilesystem.VAR
)


class ebNodeFilesystemInfo(NamedTuple):
    mountpoint: str
    device: str
    fs_type: str
    size_bytes: int
    free_bytes: int
    encrypted: bool


class ebNodeLVInfo(NamedTuple):
    name: str
    dm_path: str
    vg_name: str
    size_bytes: int


class ebNodeVGInfo(NamedTuple):
    name: str
    size_bytes: int
    free_bytes: int
    pe_bytes: int


class ebNodePVInfo(NamedTuple):
    name: str
    vg_name: str
    size_bytes: int


class ebNodeFSLayout(NamedTuple):
    filesystems: List[ebNodeFilesystemInfo]
    lvs: List[ebNodeLVInfo]
    vgs: List[ebNodeVGInfo]
    pvs: List[ebNodePVInfo]


class ebNodeFSTree(NamedTuple):
    filesystem: ebNodeFilesystemInfo
    lv: Optional[ebNodeLVInfo]
    inactive_lv: Optional[ebNodeLVInfo]
    vg: Optional[ebNodeVGInfo]
    pvs: Optional[List[ebNodePVInfo]]


class ebDiskImageInfo(NamedTuple):
    path: str
    size_bytes: int
    file_format: str
    partition_table: str



def parse_size(size_str: str) -> int:
    """
    Parses a string containing a size and returns the number of bytes.

    For example:
    parse_size('2K') == 2048
    parse_size('1 kb') == 1024
    parse_size('42') == 42
    parse_size('64b') == 64
    parse_size('1.1K') == 1127

    :param size_str: String to parse.
    :returns: int with the exact number of bytes the string represents.
    :raises ExacloudRuntimeError: If the string contains an invalid format.
    """

    factors: Dict[str, int] = {
        'K': KIB,
        'M': MIB,
        'G': GIB,
        'T': TIB
    }

    try:
        quantity, _, units = re.match(
            r"([0-9]+(\.[0-9]+)?)[ ]*([KMGT]?)B?$",
            size_str,
            re.IGNORECASE
        ).groups()
    except AttributeError as ex:
        msg: str = f"{size_str} is not a valid string representing a size."
        raise ExacloudRuntimeError(0x10, 0xA, msg) from ex

    return math.ceil(float(quantity) * factors.get(units.upper(), 1))



########################################
### QUERY INFORMATION FROM THE NODES ###
########################################


def get_max_domu_filesystem_sizes(
    clu_ctrl: exaBoxCluCtrl,
    use_defaults: bool = True
) -> Dict[ebDomUFilesystem, int]:
    """
    Calculates the maximum sizes in bytes for each DomU filesystem in this
    particular environment.

    :param clu_ctrl: A Clu Control object.
    :returns: Dict from ebDomUFilesystem to the maximum amount of bytes
        allowed.
    """

    fs_size_limits: Dict[ebDomUFilesystem, int] = {}

    if use_defaults:
        if clu_ctrl.mIsKVM():
            if clu_ctrl.mIsOciEXACC() or clu_ctrl.SharedEnv():
                fs_size_limits = {
                    ebDomUFilesystem.VAR:           5   * GIB,
                    ebDomUFilesystem.VAR_LOG:       18  * GIB,
                    ebDomUFilesystem.VAR_LOG_AUDIT: 3   * GIB,
                    ebDomUFilesystem.U01:           20  * GIB
                }
            else:
                fs_size_limits = {
                    ebDomUFilesystem.VAR:           10  * GIB,
                    ebDomUFilesystem.VAR_LOG:       30  * GIB,
                    ebDomUFilesystem.VAR_LOG_AUDIT: 10  * GIB,
                    ebDomUFilesystem.U01:           250 * GIB,
                    ebDomUFilesystem.TMP:           10  * GIB
                }
        else:
            fs_size_limits[ebDomUFilesystem.ROOT] = parse_size(
                clu_ctrl.mCheckConfigOption('force_vm_rootfs_disksize')
            ) - 2 * GIB

    # The maximum sizes may also be included in the payload.
    payload: Optional[dict] = clu_ctrl.mGetArgsOptions().jsonconf
    fs_size_payload: Dict[str, str] = \
        payload.get('filesystems', {}).get('mountpoints', {}) \
        if payload is not None and payload.get('filesystems') else {}

    for mountpoint, size_str in fs_size_payload.items():
        try:
            fs: ebDomUFilesystem = ebDomUFilesystem(mountpoint)
            fs_size_limits[fs] = parse_size(size_str)
        except ValueError:
            ebLogWarn(f"{mountpoint} is currently not a resizable partition.")

    return fs_size_limits



def get_node_filesystems(node: exaBoxNode) -> List[ebNodeFilesystemInfo]:
    """
    Obtains the info of every filesystem in a given node.
    This includes:
     - Mountpoint
     - Source device
     - Type
     - Size in bytes
     - Free size in bytes

    :param node: Node from which to get the filesystems info.
    :returns: List of ebNodeFilesystemInfo for the node.
    """

    DF: str = node_cmd_abs_path_check(node, 'df')
    LSBLK: str = node_cmd_abs_path_check(node, 'lsblk')
    GREP: str = node_cmd_abs_path_check(node, 'grep')
    _, out, _ = node_exec_cmd_check(
        node,
        f"{DF} --local --output=target,source,fstype,size,avail --block-size=1 | {GREP} -v 'nfs'"
    )

    filesystems: List[ebNodeFilesystemInfo] = []
    for line in out.splitlines()[1:]:
        mountpoint, device, fs_type, size_bytes, free_bytes = line.split()
        encrypted: bool = False
        ret = node_exec_cmd(node, f"{LSBLK} -rno TYPE {device}")
        if 'crypt' in ret.stdout:
            encrypted = True
        filesystems.append(ebNodeFilesystemInfo(
            mountpoint,
            device,
            fs_type,
            int(size_bytes),
            int(free_bytes),
            encrypted
        ))

    return filesystems



def get_node_lvs(node: exaBoxNode) -> List[ebNodeLVInfo]:
    """
    Obtains the info of every logical volume in a given node.
    This includes:
     - Name
     - DM path
     - Volume group
     - Size in bytes

    :param node: Node from which to get the logical volumes info.
    :returns: List of ebNodeLVInfo for the given node.
    """

    LVS: str = node_cmd_abs_path_check(node, 'lvs', sbin=True)
    _, out, _ = node_exec_cmd_check(
        node,
        f"{LVS} --noheading -o lv_name,lv_dm_path,vg_name,lv_size --units B"
    )

    lvs: List[ebNodeLVInfo] = []
    for line in out.splitlines():
        name, dm_path, vg_name, size_bytes = line.split()
        lvs.append(
            ebNodeLVInfo(name, dm_path, vg_name, int(size_bytes[:-1]))
        )

    return lvs



def get_node_vgs(node: exaBoxNode) -> List[ebNodeVGInfo]:
    """
    Obtains the info of every volume group in a given node.
    This includes:
     - Name
     - Size in bytes
     - Free size in bytes
     - Physical extend size in bytes

    :param node: Node from which to get the volume groups info.
    :returns: List of ebNodeVGInfo for the given node.
    """

    VGS: str = node_cmd_abs_path_check(node, 'vgs', sbin=True)
    _, out, _ = node_exec_cmd_check(
        node,
        f"{VGS} --noheading "
            "-o vg_name,vg_size,vg_free,vg_extent_size "
            "--units B "
    )

    vgs: List[ebNodeVGInfo] = []
    for line in out.splitlines():
        name, size_bytes, free_bytes, pe_bytes = line.split()
        vgs.append(
            ebNodeVGInfo(
                name, 
                int(size_bytes[:-1]),
                int(free_bytes[:-1]),
                int(pe_bytes[:-1])
            )
        )

    return vgs



def get_node_pvs(node: exaBoxNode) -> List[ebNodePVInfo]:
    """
    Obtains the info of every physical volume in a given node.
    This includes:
     - Name
     - Volume group
     - Size in bytes

    :param node: Node from which to get the physical volumes info.
    :returns: List of ebNodePVInfo for the given node.
    """

    PVS: str = node_cmd_abs_path_check(node, 'pvs', sbin=True)
    _, out, _ = node_exec_cmd_check(
        node,
        f"{PVS} --noheading -o pv_name,vg_name,pv_size --units B"
    )

    pvs: List[ebNodePVInfo] = []
    for line in out.splitlines():
        name, vg_name, size_bytes = line.split()
        pvs.append(
            ebNodePVInfo(name, vg_name, int(size_bytes[:-1]))
        )

    return pvs



def get_disk_partition_table(node: exaBoxNode, disk_path: str) -> str:
    """
    Obtains the partition table of a disk using the parted tool.

    :param node: Node from which to get the disk partition table.
    :param disk_path: Disk device path.
    :returns: str with the disk partition table type.
    """

    PARTED: str = node_cmd_abs_path_check(node, 'parted', sbin=True)
    _, out, _ = node_exec_cmd_check(
        node,
        f"{PARTED} {disk_path} print"
    )
    partition_table_line, *_ = [
        line for line in out.splitlines()
        if line.startswith('Partition Table:')
    ]
    _, partition_table = [
        part.strip() for part in partition_table_line.split(':')
    ]

    return partition_table



def get_node_fs_layout(node: exaBoxNode) -> ebNodeFSLayout:
    """
    Obtains the whole filesystems layout of a given node.
    This includes:
     - The filesystems
     - Logical volumes
     - Volume groups
     - Physical volumes

    :param node: Node from which to obtain the filesystems layout.
    :returns: ebNodeFSLayout for the given node.
    """
    filesystems: List[ebNodeFilesystemInfo] = get_node_filesystems(node)
    lvs: List[ebNodeLVInfo] = get_node_lvs(node)
    vgs: List[ebNodeVGInfo] = get_node_vgs(node)
    pvs: List[ebNodePVInfo] = get_node_pvs(node)

    fs_layout = ebNodeFSLayout(filesystems, lvs, vgs, pvs)
    return fs_layout



def get_domu_filesystem_tree(
    domu_fs_layout: ebNodeFSLayout,
    filesystem: ebDomUFilesystem,
    clu_ctrl: exaBoxCluCtrl = None
) -> ebNodeFSTree:
    """
    Gets all the relevant information of a DomU filesystem.

    This includes:
     - The filesystem info
     - Its logical volume info (if any)
     - Its volume group info (if any)
     - Its first physical volume info (if any)

    If the filesystem is in a logical volume and its volume group contains
    multiple physical volumes, it will be returned the first one only.

    NOTE: The grid home partition returned is actually the initial installed
    GI in the DomU, so if you perform a GI upgrade, you should be aware that
    your actual GI home path changes to the u02 partition, so if you want to
    perform any operations to the current GI home partition, you should refer
    to the u02 partition only if you performed a GI upgrade in you DomU.

    :param domu_fs_layout: The DomU filesystems layout to examine.
    :param filesystem: A known DomU filesystem.
    :returns: ebNodeFSTree with all the information.
    """

    # Code hint: The pattern
    # x, *_ = filter(p, ys)
    # Simply means, "x is the first element in ys such that,
    # for each y in ys, p(y) is True"
    #
    # For example:
    # x, *_ = filter(lambda y: y > 2, [0, 1, 2, 3, 4])
    # print(x) # Will print 3

    mountpoint: str = filesystem.value
    if filesystem == ebDomUFilesystem.GRID:
        _gridhome  = None
        _dir = None
        if clu_ctrl:
            _gridhome = clu_ctrl.mGetClusters().mGetCluster().mGetCluHome()

            _dir = _gridhome.split('/', 2)[1]
            if _dir == "u02":
                ebLogInfo(f"*** GI HOME is at u02 partition, skipping resize ...")
                return None

        grid_fss = [
            fs for fs in domu_fs_layout.filesystems
            if 'grid' in fs.mountpoint
        ]
        if not grid_fss:
            return None
        grid_fs, *_ = grid_fss
        mountpoint = grid_fs.mountpoint

    fss_info = [
        fs for fs in domu_fs_layout.filesystems
        if fs.mountpoint == mountpoint
    ]
    if not fss_info:
        return None
    fs_info, *_ = fss_info
    device: str = fs_info.device

    # Verify this filesystem is included in any LV
    if not any(
        lv.dm_path == device or f"{lv.dm_path}-crypt" == device
        for lv in domu_fs_layout.lvs
    ):
        return ebNodeFSTree(fs_info, None, None, None, None)

    lv_info, *_ = filter(
        lambda lv: lv.dm_path == device or f"{lv.dm_path}-crypt" == device,
        domu_fs_layout.lvs
    )
    vg_name = lv_info.vg_name

    inactive_lv_info: Optional[ebNodeLVInfo] = None
    if filesystem in FS_WITH_DUPLICATED_VOLUME:
        inactive_lv_dm_path: str = lv_info.dm_path[:-1] + \
            ('2' if lv_info.dm_path[-1] == '1' else '1')
        inactive_lv_info, *_ = filter(
            lambda lv: lv.dm_path == inactive_lv_dm_path,
            domu_fs_layout.lvs
        )

    vg_info, *_ = filter(lambda vg: vg.name == vg_name, domu_fs_layout.vgs)

    pv_info = sorted(
        filter(lambda pv: pv.vg_name == vg_name, domu_fs_layout.pvs),
        key = lambda pv: pv.name
    )

    return ebNodeFSTree(fs_info, lv_info, inactive_lv_info, vg_info, pv_info)



def get_next_dev(last_dev: str, preffix_len: int) -> str:
    """
    Gets the next dev that can be used to attach a disk image into a DomU.

    For example:
    get_next_dev('sda', 2) == 'sdb'
    get_next_dev('xvdz', 3) == 'xvdba

    :param last_dev: Last dev found.
    :param preffix_len: Number of characters to omit from the dev name.
    :returns: str with the next dev.
    """
    preffix: str = last_dev[:preffix_len]
    dev: str = last_dev[preffix_len:]
    NUM_LETTERS: int = len(string.ascii_lowercase)

    dev = chr(ord(dev[-1]) + 1) + dev[:-1][::-1]
    dev_new: str = ""
    while dev:
        next_val: int = ord(dev[0]) - ord('a')
        dev = dev[1:]
        if next_val >= NUM_LETTERS:
            if not dev:
                dev = 'a'
            else:
                dev = chr(ord(dev[0]) + (next_val // NUM_LETTERS)) + \
                    dev[1:]
            next_val %= NUM_LETTERS
        dev_new += chr(next_val + ord('a'))
    return preffix + dev_new[::-1]



def get_last_dev(disks_devs: List[str]) -> str:
    """
    Returns the longest dev from the lexicographically ordered version from
    the given list.

    :param disks_devs: Unordered list to obtain the last dev.
    :returns: str from the last dev.
    """
    return max(disks_devs, key = lambda disk: (len(disk), disk))



def get_disk_for_part_dev(node: exaBoxNode, part_dev: str) -> str:
    """
    Obtains the proper disk device path for the given partition device path
    in the given node.

    For example:
    get_disk_for_part_dev(node, '/dev/sda3') == '/dev/sda'

    :param node: Node from which to obtain the disk device path.
    :param part_dev: str containing the partition device path.
    :returns: str containing the disk device path.
    """

    LSBLK: str = node_cmd_abs_path_check(node, 'lsblk')
    _, out, _ = node_exec_cmd_check(node, f"{LSBLK} -pno pkname {part_dev}")
    lines: List[str] = [
        line for line in out.splitlines()
        if line.strip() and part_dev.startswith(line)
    ]
    if not lines:
        return part_dev

    disk, *_ = sorted(lines)
    return disk



def get_last_part_dev_for_disk(node: exaBoxNode, disk_dev):
    """
    Obtains the last partition device path for the given node disk dev path.

    For example:
    get_last_part_dev_for_disk(node, '/dev/xvda') = '/dev/xvda3'
    get_disk_for_part_dev(node, get_last_part_dev_for_disk(node, x)) == x

    :param node: Node from which to obtain the partition device path.
    :param disk_dev: str of the disk from which to obtain the partition.
    :returns: str containing the last partition device path.
    :raises ExacloudRuntimeError: In case the specified device is not
        available in the node.
    """

    LSBLK: str = node_cmd_abs_path_check(node, 'lsblk')
    out: str = ''
    for _ in range(5):
        try:
            _, out, _ = node_exec_cmd_check(
                node,
                f"{LSBLK} -pno kname {disk_dev}"
            )
            #Bug 37683920: If the output is disk itself (no partitions),
            #force the retry
            if out.strip() == disk_dev:
                ebLogWarn(f"*** {disk_dev} has no partitions yet.Retrying...")
                time.sleep(1)
                continue
            break
        except ExacloudRuntimeError:
            ebLogWarn(
                f"*** It seems that partition device in {disk_dev} "
                f"is still not available in {node.mGetHostname()}. "
                "Let's retry..."
            )
            time.sleep(1)
    else:
        msg: str = (
            f"Disk device {disk_dev} "
            f"is not available in {node.mGetHostname()}"
        )
        raise ExacloudRuntimeError(0x10, 0xA, msg)

    lines: List[str] = [
        line for line in out.splitlines()
        if line.startswith(disk_dev)
    ]
    return get_last_dev(lines)



def get_dom0_disk_for_filesystem(
    dom0_node: exaBoxNode,
    domu_name: str,
    filesystem: ebDomUFilesystem
) -> ebDiskImageInfo:
    """
    Obtains the info of a proper disk image file that can be used for resizing
    the given DomU filesystem.

    This includes:
     - Full path of the disk image file
     - Virtual size
     - File format
     - Partition table type

    :param dom0_node: Dom0 node in where to look for the disk image.
    :param domu_name: DomU FQDN.
    :param filesystem: The DomU filesystem.
    :returns: ebDiskImageInfo of the desired disk image.
    """

    # Try to get any EDV volume first.
    try:
        return get_dom0_edvdisk_for_filesystem(dom0_node, domu_name, filesystem)
    except:
        pass


    disk_images: str = os.path.join('/EXAVMIMAGES/GuestImages', domu_name)
    disk_image_name: str = os.path.join(disk_images, 'System.img')

    if filesystem == ebDomUFilesystem.U01:
        u01_disk_image: str = os.path.join(disk_images, 'u01.img')
        u01_luks_disk_image: str = os.path.join(disk_images,
                'u01_encrypted.img')
        if dom0_node.mFileExists(u01_disk_image):
            disk_image_name = u01_disk_image
        elif dom0_node.mFileExists(u01_luks_disk_image):
            disk_image_name = u01_luks_disk_image

    elif filesystem == ebDomUFilesystem.U02:
        u02_disk_image: str = os.path.join(disk_images, 'u02_extra.img')
        u02_luks_disk_image: str = os.path.join(disk_images,
                'u02_extra_encrypted.img')

        if dom0_node.mFileExists(u02_disk_image):
            disk_image_name = u02_disk_image
        elif dom0_node.mFileExists(u02_luks_disk_image):
            disk_image_name = u02_luks_disk_image

    elif filesystem == ebDomUFilesystem.GRID:
        grid_images: str = os.path.join(disk_images, 'grid*.img')
        LS: str = node_cmd_abs_path_check(dom0_node, 'ls')
        _, out, _ = node_exec_cmd_check(dom0_node, f"{LS} {grid_images}")
        disk_image_name, *_ = out.splitlines()


    # After obtaining the disk image full path, we obtain its details.
    # First, we obtain the disk image size..
    QEMU_IMG: str = node_cmd_abs_path_check(dom0_node, 'qemu-img')
    _, out, _ = node_exec_cmd_check(
        dom0_node,
        f"{QEMU_IMG} info --output=json {disk_image_name}"
    )
    out_json: dict = json.loads(out)
    disk_image_bytes: int = out_json['virtual-size']
    disk_image_fmt: str = out_json['format']

    # And then we obtain the partition table.
    partition_table = get_disk_partition_table(dom0_node, disk_image_name)

    return ebDiskImageInfo(
        disk_image_name,
        disk_image_bytes,
        disk_image_fmt,
        partition_table
    )

def get_edvdisk_path_from_domblklist(dom0_node, domu_name, filesystem):
    """
    Helper to get the disk path from virsh domblklist output by pattern (e.g., 'u01', 'sys', 'grid').
    """
    VIRSH = node_cmd_abs_path_check(dom0_node, 'virsh')
    cmd = f"{VIRSH} domblklist {domu_name} | /bin/grep -e /{filesystem} -e _{filesystem}_"
    _, out, _ = node_exec_cmd_check(dom0_node, cmd)
    disk_paths = out.split()
    return disk_paths[1] if disk_paths else None

def get_dom0_edvdisk_for_filesystem(
    dom0_node: exaBoxNode,
    domu_name: str,
    filesystem: ebDomUFilesystem
) -> ebDiskImageInfo:
    """
    Obtains the info of a proper disk image file/device from 'virsh domblklist' that can be used
    for resizing the given DomU filesystem.
    """

    _fs = "sys"
    if filesystem == ebDomUFilesystem.U01:
        _fs = "u01"
    elif filesystem == ebDomUFilesystem.U02:
        _fs = "u02"
    elif filesystem == ebDomUFilesystem.GRID:
        _fs = "gih01"

    # Get disk image/device path using domblklist
    disk_image_name = get_edvdisk_path_from_domblklist(dom0_node, domu_name, _fs)
    if not disk_image_name:
        raise Exception(f"No disk matching pattern '{filesystem}' found for domain {domu_name}")

    # Now get disk image/device properties
    QEMU_IMG = node_cmd_abs_path_check(dom0_node, 'qemu-img')
    _, out, _ = node_exec_cmd_check(
        dom0_node, f"{QEMU_IMG} info --output=json {disk_image_name}"
    )
    out_json = json.loads(out)
    disk_image_bytes = out_json['virtual-size']
    disk_image_fmt = out_json['format']

    partition_table = get_disk_partition_table(dom0_node, disk_image_name)

    return ebDiskImageInfo(
        disk_image_name,
        disk_image_bytes,
        disk_image_fmt,
        partition_table
    )

def check_user_space_ready(node: str) -> bool:
    """
    This function check if user-space is ready for a given node.

    - It uses systemd-analyze, so we rely on the DomU using SystemD which is
      the case, at least, from Oracle Linux 7 onwards

    :param node: Node where to check if user-space is ready.
    """

    SYSTEMD_ANALYZE: str = \
        node_cmd_abs_path_check(node, 'systemd-analyze', sbin=True)
    rc, _, _ = node_exec_cmd(node, f"{SYSTEMD_ANALYZE} time")

    return rc == 0



##########################
### ALTER DOM0 METHODS ###
##########################


def fill_disk_with_lvm_partition(
    dom0_node: exaBoxNode,
    disk_path: str,
    partition_table: str
):
    """
    Creates a new partition table for a given disk and an LVM partition.

    :param dom0_node: Dom0 node.
    :param disk_path: A disk device path.
    :param partition_table: A partition table supported by parted.
    :raises ExacloudRuntimeError: If an error occurred.
    """

    PARTED: str = node_cmd_abs_path_check(dom0_node, 'parted', sbin=True)
    node_exec_cmd_check(
        dom0_node,
        f"{PARTED} -s {disk_path} mktable {partition_table}"
    )
    cmd_ret = node_exec_cmd(
        dom0_node,
        f"{PARTED} -s {disk_path} mkpart primary 0% 100%"
    )

    allowed_error: str = \
        'we have been unable to inform the kernel of the change'
    if cmd_ret.exit_code != 0 and not \
        all(word in cmd_ret.stderr for word in allowed_error.split()):
        msg: str = \
            f"Disk {disk_path} partitioning failed with: {cmd_ret.stderr}"
        raise ExacloudRuntimeError(0x10, 0xA, msg)

    cmd_ret = node_exec_cmd(dom0_node, f"{PARTED} {disk_path} set 1 lvm on")
    if cmd_ret.exit_code != 0 and not \
        all(word in cmd_ret.stderr for word in allowed_error.split()):
        msg: str = \
            f"Disk {disk_path} partitioning failed with: {cmd_ret.stderr}"
        raise ExacloudRuntimeError(0x10, 0xA, msg)



def create_new_lvm_disk_image(
    dom0_node: exaBoxNode,
    disk_info: ebDiskImageInfo
):
    """
    Creates a new disk image with an LVM volume of the whole image space.

    NOTE: The size will be automatically rounded up by the next multiple of
    512 bytes. i.e.: 513 bytes will be rounded to 1024 bytes.

    :param dom0_node: Dom0 node.
    :param disk_info: Disk image info
    :raises ExacloudRuntimeError: If the disk image already exists or an error
        occurred when trying to create the disk image.
    """

    if dom0_node.mFileExists(disk_info.path):
        msg: str = f"Disk image file already exists {disk_info.path} "
        raise ExacloudRuntimeError(0x10, 0xA, msg)

    if disk_info.file_format != 'raw':
        msg: str = f"Image format {disk_info.file_format} not supported."
        raise ExacloudRuntimeError(0x10, 0xA, msg)

    QEMU_IMG: str = node_cmd_abs_path_check(dom0_node, 'qemu-img')
    node_exec_cmd_check(
        dom0_node,
        f"{QEMU_IMG} create "
            f"{disk_info.path} "
            f"{disk_info.size_bytes}B "
            f"-f {disk_info.file_format} "
    )
    fill_disk_with_lvm_partition(
        dom0_node,
        disk_info.path,
        disk_info.partition_table
    )

    ebLogInfo(
        f"*** Created disk image {disk_info.path} "
        f"on Dom0: {dom0_node.mGetHostname()} ; "
        f"Size: {disk_info.size_bytes} bytes, "
        f"Image file format: {disk_info.file_format}, "
        f"Partition table: {disk_info.partition_table}"
    )



def attach_dom0_disk_image(
    dom0_node: exaBoxNode,
    domu_name: str,
    disk_path: str,
    kvm_cache: Optional[str]='writethrough',
    kvm_io: Optional[str]=None,
    serial_name: Optional[str]=None
) -> str:
    """
    Attaches a given disk image file to the given DomU.

    :param dom0_node: Dom0 node.
    :param domu_name: DomU FQDN
    :param disk_path: Dom0 path to the disk image to attach.
    :returns: str representing the DomU dev where it was attached.
        NOTE: This dev is not trusty on KVM environments.
    :raises ExacloudRuntimeError: If the disk image does not exist or an error
        occurred when trying to attach the disk image to the DomU.
    """

    if not dom0_node.mFileExists(disk_path):
        msg: str = f"Disk image file does not exist {disk_path} "
        raise ExacloudRuntimeError(0x10, 0xA, msg)

    next_vm_disk: str =''
    VIRSH: Optional[str] = node_cmd_abs_path(dom0_node, 'virsh')
    if not VIRSH:
        XM: str = node_cmd_abs_path_check(dom0_node, 'xm', sbin=True)

        # In order to attach a disk image in a XEN VM, we also need to add it
        # to the VM configuration file, so when the DomU gets rebooted it
        # automatically attaches it again before booting up.
        # To do so, we just need to find this line in the configuration file
        #
        # disk = ['file:///root/disk1.img,xvda,w', 'file:///root/dummy.img...
        #
        # And add our new disk at the end of the list.
        # this is what this code below does.
        VM_CFG_PATH: str = os.path.join(
            os.path.dirname(disk_path),
            'vm.cfg'
        )
        vm_cfg: List[str] = \
            node_read_text_file(dom0_node, VM_CFG_PATH).splitlines() + ['']

        vm_disks_line, *_ = filter(lambda line: 'disk' in line, vm_cfg)
        vm_disks_line_ix: int = vm_cfg.index(vm_disks_line)
        vm_disks_str: str = \
            vm_disks_line[vm_disks_line.find('['):vm_disks_line.find(']')+1]
        vm_disks: List[List[str]] = [
            disk.split(',')
            for disk in json.loads(vm_disks_str.replace("'", '"'))
        ]

        vm_disks_repeated: List[List[str]] = [
            [path, dev, mode]
            for path, dev, mode in vm_disks
            if path.endswith(disk_path)
        ]
        if vm_disks_repeated:
            path, dev, _ = vm_disks_repeated[0]
            ebLogWarn(f"*** Disk {path} already attached in DomU as {dev}")
            return dev

        vm_disks_devs: List[str] = [ disk_dev for _, disk_dev, _ in vm_disks ]
        next_vm_disk = get_next_dev(get_last_dev(vm_disks_devs), 3)

        vm_disks.append([f"file://{disk_path}", next_vm_disk, 'w'])
        vm_disks_strs: List[str] = [
            f"'{','.join(attr for attr in disk)}'" for disk in vm_disks
        ]
        vm_disks_line = f"disk = [{', '.join(vm_disks_strs)}]"
        vm_cfg[vm_disks_line_ix] = vm_disks_line
        node_write_text_file(dom0_node, VM_CFG_PATH, '\n'.join(vm_cfg))

        _, out, _ = node_exec_cmd_check(dom0_node, f"{XM} list")
        if domu_name in out:
            node_exec_cmd_check(
                dom0_node,
                f"{XM} block-attach "
                    f"{domu_name} "
                    f"file://{disk_path} "
                    f"/dev/{next_vm_disk} "
                    f"w "
            )

    else:

        # Check if Guest is using images stored locally in Host
        _rc, out, _ = node_exec_cmd(
            dom0_node,
            f"{VIRSH} domblklist {domu_name} | grep {domu_name}"
        )

        # If not pattern matches, we assume the block files are on top
        # of EDVolumes
        if _rc == 1:
            _, out, _ = node_exec_cmd_check(
                dom0_node,
                f"{VIRSH} domblklist {domu_name} | tail -n +3"
            )

        vm_disks: List[List[str]] = [
            line.strip().split()
            for line in out.splitlines()
            if line.strip()
        ]

        vm_disks_repeated: List[List[str]] = [
            [dev, path]
            for dev, path in vm_disks
            if path == disk_path
        ]
        if vm_disks_repeated:
            dev, path = vm_disks_repeated[0]
            ebLogWarn(f"*** Disk {path} already attached in DomU as {dev}")
            return dev

        serial_opt: str = f'--serial {serial_name} ' if serial_name else ''
        """
        _, out, _ = node_exec_cmd_check(dom0_node, f"{VIRSH} list")
        live_opt: str = '--live' if domu_name in out else ''
        cache_opt: str = f'--cache {kvm_cache}' if kvm_cache else ''
        io_opt: str = f'--io {kvm_io}' if kvm_io else ''

        vm_disks_devs: List[str] = [ disk_dev for disk_dev, _ in vm_disks ]
        next_vm_disk = get_next_dev(get_last_dev(vm_disks_devs), 2)
        node_exec_cmd_check(
            dom0_node,
            f"{VIRSH} attach-disk "
                f"{domu_name} "
                f"{disk_path} "
                f"--target {next_vm_disk} "
                f"{serial_opt}"
                f"{cache_opt} "
                f"{io_opt} "
                f"{live_opt} "
                "--config "
        )
        """

        node_exec_cmd_check(
            dom0_node,
            f"{VM_MAKER} --attach "
                f"--disk-image {disk_path} "
                f"--domain {domu_name} "
                f"{serial_opt}"
        )

    ebLogInfo(
        f"*** Attached {disk_path} as {next_vm_disk} "
        f"on Dom0 {dom0_node.mGetHostname()} for DomU {domu_name}"
    )

    return next_vm_disk

#Return a list of all the active(running, paused and in shutdown) VMs on the dom0
def vm_active_list(dom0_node: exaBoxNode, hypervisor: str ) -> list:
    if "virsh" in hypervisor:
        # virsh list --name by default returns active domains (running, paused and in shutdown)
        _cmd = f"{hypervisor} list --name"
        _, out, _ = node_exec_cmd_check(dom0_node, _cmd)
        out = ([vm for vm in out.split() if vm])
    else:
        # xm list -> first 2 line is Name, Domain 0, so that need to be skipped        
        _cmd = f"{hypervisor} list | tail -n +3 | /usr/bin/awk '{{print $1}}'"
        _, out, _ = node_exec_cmd_check(dom0_node, _cmd)
        out = ([vm for vm in out.split() if vm])
    ebLogInfo(f"*** VMs found running {out}")
    return out

def shutdown_domu(
    dom0_node: exaBoxNode,
    domu_name: str,
    timeout_seconds: int=600,
    force_on_timeout: bool = False
):
    """
    Gracefully shutdowns the specified DomU in the given Dom0 node.
    
    You can also specify the timeout you would like to wait before raising an
    exception in case the DomU does not get shut off before it.
    You can decide also if you want to force the shutdown if the timeout
    reaches.

    :param dom0_node: Dom0 node.
    :param domu_name: DomU FQDN.
    :param timeout_seconds: Seconds to wait before raising an exception if
        the DomU is not shut off.
    :param force_on_timeout: Whether to force the shutdown instead of raising
        an exception if the timeout reaches.
    :raises ExacloudRuntimeError: If the shutdown timed out.
    """

    # Get the hypervisor binary (virsh for KVM or xm for XEN).
    hypervisor: Optional[str] = node_cmd_abs_path(dom0_node, 'virsh')
    if not hypervisor:
        hypervisor = node_cmd_abs_path_check(dom0_node, 'xm', sbin=True)


    # Check if DomU is already shut off.
    out = vm_active_list(dom0_node, hypervisor)
    if domu_name not in out:
        ebLogWarn(f"*** DomU {domu_name} was already in shut off state.")
        return

    # Attempt to shutdown the DomU.
    ebLogInfo(f"*** Performing shutdown of DomU {domu_name} ...")
    t0: float = time.time()
    try:
        node_exec_cmd_check(dom0_node, f"{hypervisor} shutdown {domu_name}")
    except ExacloudRuntimeError as ex:
        if force_on_timeout:
            node_exec_cmd_check(dom0_node, f"{hypervisor} destroy {domu_name}")
        else:
            msg: str = f"Could not shutdown DomU {domu_name} "
            raise ExacloudRuntimeError(0x10, 0xA, msg) from ex


    # Wait for the DomU to be completely shut off.
    CHECK_PERIOD_SECS: int = 10
    for _ in range(timeout_seconds // CHECK_PERIOD_SECS):
        time.sleep(CHECK_PERIOD_SECS)
        out = vm_active_list(dom0_node, hypervisor)
        if domu_name not in out:
            break
    else:
        if force_on_timeout:
            node_exec_cmd_check(dom0_node, f"{hypervisor} destroy {domu_name}")
        else:
            msg: str = (
                f"Could not shutdown DomU {domu_name} "
                f"after {timeout_seconds} seconds."
            )
            raise ExacloudRuntimeError(0x10, 0xA, msg)

    tf: float = time.time()
    ebLogInfo(
        f"*** Successfully shutdown DomU {domu_name} in {tf - t0} seconds."
    )



def start_domu(
    dom0_node: exaBoxNode,
    domu_name: str,
    wait_for_connectable: bool=True,
    timeout_seconds: int=1200,
    wait_condition: Optional[Callable[[exaBoxNode], bool]]=None
):
    """
    Starts a DomU.

    Optionally wait for it to be connectable. We can also specify a timeout
    in case the DomU is not connectable after it was started.

    :param dom0_node: Dom0 node where the DomU can be started.
    :param domu_name: DomU FQDN.
    :param wait_for_connectable: Whether or not to wait for DomU to be
        connectable after starting it.
    :param timeout_seconds: Seconds to wait before raising an exception if
        the DomU is not started.
    """

    # Get the hypervisor binary (virsh for KVM or xm for XEN).
    hypervisor: Optional[str] = node_cmd_abs_path(dom0_node, 'virsh')
    start_vm_cmd: str = f"{hypervisor} start {domu_name}"
    if not hypervisor:
        hypervisor = node_cmd_abs_path_check(dom0_node, 'xm', sbin=True)
        start_vm_cmd: str = \
            f"{hypervisor} create /EXAVMIMAGES/GuestImages/{domu_name}/vm.cfg"
        
    # Check if DomU is already started.
    t0: float = time.time()
    out = vm_active_list(dom0_node, hypervisor)
    if domu_name in out:
        ebLogWarn(f"*** DomU {domu_name} was already in started.")
    else:
        ebLogInfo(f"*** Starting DomU {domu_name} ...")
        node_exec_cmd_check(dom0_node, start_vm_cmd)

    if not wait_for_connectable:
        return

    # Wait for DomU to be connectable
    CHECK_PERIOD_SECS: int = 10
    for _ in range(timeout_seconds // CHECK_PERIOD_SECS):
        if exaBoxNode(get_gcontext()).mIsConnectable(domu_name):
            break
        time.sleep(CHECK_PERIOD_SECS)
    else:
        msg: str = (
            f"Could not start DomU {domu_name} "
            f"after {timeout_seconds} seconds."
        )
        raise ExacloudRuntimeError(0x10, 0xA, msg)

    tf: float = time.time()
    ebLogInfo(
        f"*** Successfully started DomU {domu_name} in {tf - t0} seconds."
    )

    if wait_condition is None:
        return

    ebLogInfo(f"*** Waiting for DomU {domu_name} to be ready...")
    t0: float = time.time()
    with connect_to_host(domu_name, get_gcontext()) as node:
        CHECK_PERIOD_SECS: int = 10
        for _ in range(timeout_seconds // CHECK_PERIOD_SECS):
            if wait_condition(node):
                break
            time.sleep(CHECK_PERIOD_SECS)
        else:
            msg: str = (
                f"DomU {domu_name} services were not started "
                f"after {timeout_seconds} seconds."
            )
            raise ExacloudRuntimeError(0x10, 0xA, msg)

    tf: float = time.time()
    ebLogInfo(f"*** DomU {domu_name} is now ready after {tf - t0} seconds.")



def resize_disk_image_for_filesystem(
    dom0_node: exaBoxNode,
    domu_name: str,
    filesystem: ebDomUFilesystem,
    extra_bytes: int,
    domu_reboot: bool = True,
    pre_resize_callback: Callable[[str, int], None] = None
) -> ebDiskImageInfo:
    """
    Resizes a proper disk image file that can be used for resizing the given
    DomU filesystem.

    NOTE: If the environment is XEN based, the DomU will be rebooted during
    the process to avoid data corruption. Use only to expand non-LVM based
    DomU filesystems such as u02 and grid.

    :param dom0_node: Dom0 node in where to look for the disk image.
    :param domu_name: DomU FQDN.
    :param filesystem: The DomU filesystem.
    :param extra_kb: The extra amount of bytes to expand.
        NOTE: It can be a negative number, but you have to make sure you have
        already shrunk enough the last partition, otherwise this will result
        in a destructive operation.
    :returns: ebDiskImageInfo with the updated disk size after the resize.
    :raises ExacloudRuntimeError: If an error ocurred.
    """

    # Get initial disk image info
    disk_info: ebDiskImageInfo = get_dom0_disk_for_filesystem(
        dom0_node,
        domu_name,
        filesystem
    )


    ebLogInfo(
        f"*** Starting resize of {disk_info.path}, "
        f"initial size: {disk_info.size_bytes} bytes, "
        f"extra size: {extra_bytes} bytes."
    )


    # Perform the actual resize depending on the environment type
    new_bytes: int = disk_info.size_bytes + extra_bytes
    VIRSH: Optional[str] = node_cmd_abs_path(dom0_node, 'virsh')
    if not VIRSH:
        QEMU_IMG: str = node_cmd_abs_path_check(dom0_node, 'qemu-img')

        if domu_reboot:
            shutdown_domu(dom0_node, domu_name)

        if pre_resize_callback is not None:
            pre_resize_callback(disk_info.path, new_bytes)

        node_exec_cmd_check(
            dom0_node,
            f"{QEMU_IMG} resize "
                f"{disk_info.path} "
                f"-f {disk_info.file_format} "
                f"{new_bytes}"
        )

        if domu_reboot:
            start_domu(dom0_node, domu_name, wait_condition=check_user_space_ready)

    else:
        if pre_resize_callback is not None:
            pre_resize_callback(disk_info.path, new_bytes)

        node_exec_cmd_check(
            dom0_node,
            f"{VIRSH} blockresize {domu_name} {disk_info.path} {new_bytes}B"
        )


    # Check the new image size just for logging purposes.
    new_disk_info: ebDiskImageInfo = get_dom0_disk_for_filesystem(
        dom0_node,
        domu_name,
        filesystem
    )

    ebLogInfo(
        f"*** Finished resizing {disk_info.path}, "
        f"final size: {new_disk_info.size_bytes} bytes"
    )

    return new_disk_info



##########################
### ALTER DOMU METHODS ###
##########################


def expand_domu_fs_using_mountpoint(
    domu_node: exaBoxNode,
    domu_fs_tree: ebNodeFSTree,
    filesystem: ebDomUFilesystem
) -> ebNodeFSLayout:
    """
    Expands the specified DomU filesystem to its maximum size using the
    corresponding filesystem resizing tool and the free space of the volume
    in which it's contained.

    :param domu_node: DomU node.
    :param domu_fs_tree: DomU filesystem information tree.
    :param filesystem: Filesystem to resize.
    :returns: ebNodeFSLayout after the resize.
    :raises ExacloudRuntimeError: If an error ocurred or the filesystem type
        is unknown.
    """
    
    fs_dev: str = domu_fs_tree.filesystem.device
    resize_binary_name: str = ''
    if domu_fs_tree.filesystem.fs_type.startswith('ext'):
        resize_binary_name = 'resize2fs'
    elif domu_fs_tree.filesystem.fs_type == 'xfs':
        resize_binary_name = 'xfs_growfs'
    else:
        msg: str = (
            "Unknown filesystem type: "
            f"{domu_fs_tree.filesystem.fs_type}"
        )
        raise ExacloudRuntimeError(0x10, 0xA, msg)

    resize_fs_cmd: str = node_cmd_abs_path_check(
        domu_node,
        resize_binary_name,
        sbin = True
    )
    node_exec_cmd_check(domu_node, f"{resize_fs_cmd} {fs_dev}")

    new_fs_layout: ebNodeFSLayout = get_node_fs_layout(domu_node)
    new_fs_tree: ebNodeFSTree = get_domu_filesystem_tree(
        new_fs_layout,
        filesystem
    )

    ebLogInfo(
        f"*** Finished resize of non-LVM "
        f"{new_fs_tree.filesystem.mountpoint} filesystem "
        f"on {domu_node.mGetHostname()} ; "
        f"Final size: {new_fs_tree.filesystem.size_bytes} bytes."
    )
    return new_fs_layout



def expand_domu_fs_using_free_vg(
    domu_node: exaBoxNode,
    domu_fs_tree: ebNodeFSTree,
    filesystem: ebDomUFilesystem,
    extra_bytes: int,
    resize_mode: ebDomUFSResizeMode = ebDomUFSResizeMode.NORMAL
) -> ebNodeFSLayout:
    """
    Expands the specified DomU filesystem using the free space from its volume
    group. Thus, this method only applies to filesystems within a logical
    volume.

    :param domu_node: DomU node.
    :param domu_fs_tree: DomU filesystem information tree.
    :param filesystem: Filesystem to resize.
    :param extra_bytes: Extra bytes to resize the filesystem.
    :param resize_mode: Resize mode, see ebDomUFSResizeMode to get more info.
    :returns: ebNodeFSLayout after the resize.
    """

    LVRESIZE: str = node_cmd_abs_path_check(domu_node, 'lvresize', sbin=True)

    # If the logical volume contains a LUKS volume, delegate the corresponding
    # module the responsibility to resize it along with the filesystem itself.
    resize_fs_flag: str = '--resizefs'
    if resize_mode == ebDomUFSResizeMode.LV_ONLY or \
        domu_fs_tree.filesystem.device.endswith('crypt'):
        resize_fs_flag = ''

    if extra_bytes <= 0:
        ebLogWarn(
            f"0 extra bytes requested for active LV of {filesystem}"
            ". Skipping resize of active LV..."
        )
    elif resize_mode != ebDomUFSResizeMode.SND_VOL_ONLY:
        node_exec_cmd_check(
            domu_node,
            f"{LVRESIZE} "
                f"{resize_fs_flag} "
                f"-L +{extra_bytes}B "
                f"{domu_fs_tree.lv.dm_path} "
        )

    if filesystem in FS_WITH_DUPLICATED_VOLUME and \
        resize_mode != ebDomUFSResizeMode.FST_VOL_ONLY:
        secondary_lv: str = domu_fs_tree.inactive_lv.dm_path
        final_size_bytes: int = domu_fs_tree.lv.size_bytes + extra_bytes
        extra_bytes_2: int = final_size_bytes - \
            domu_fs_tree.inactive_lv.size_bytes
        if extra_bytes_2 <= 0:
            ebLogWarn(
                f"{filesystem} final size is {final_size_bytes} bytes, but "
                f"inactive LV {secondary_lv} size is already "
                f"{domu_fs_tree.inactive_lv.size_bytes} so it will not be "
                "resized."
            )
        else:
            if get_disk_partition_table(domu_node, secondary_lv) == 'unknown':
                resize_fs_flag = ''
            node_exec_cmd_check(
                domu_node,
                f"{LVRESIZE} "
                    f"{resize_fs_flag} "
                    f"-L +{extra_bytes_2}B "
                    f"{secondary_lv} "
        )

    # Get the filesystem layout one last time to return the final sizes.
    final_fs_layout: ebNodeFSLayout = get_node_fs_layout(domu_node)
    final_fs_tree: ebNodeFSTree = get_domu_filesystem_tree(
        final_fs_layout,
        filesystem
    )

    ebLogInfo(
        f"*** Finished resize of {final_fs_tree.filesystem.mountpoint} "
        f"on {domu_node.mGetHostname()} ; "
        f"Final size: {final_fs_tree.lv.size_bytes} bytes, "
        f"Resize mode: {resize_mode}"
    )

    return final_fs_layout



def expand_domu_fs_using_new_dev(
    domu_node: exaBoxNode,
    domu_fs_tree: ebNodeFSTree,
    filesystem: ebDomUFilesystem,
    disk_id: str,
    resize_mode: ebDomUFSResizeMode = ebDomUFSResizeMode.NORMAL
) -> ebNodeFSLayout:
    """
    Expands the specified DomU filesystem using a newly attached disk. Thus,
    this method only applies to filesystems within logical volumes.

    NOTE: This method is NOT recommended for KVM hosts since the VM SCSi
    controllers have a maximum limit of disks that can be attached and when
    that limit reached, the DomU won't be able to boot anymore. Also, the KVM
    hypervisor never respects the specified disk device ID.

    :param domu_node: DomU node.
    :param domu_fs_tree: DomU filesystem information tree.
    :param filesystem: Filesystem to resize.
    :param disk_id: Disk device ID to be taken for the expansion.
    :param resize_mode: Resize mode, see ebDomUFSResizeMode to get more info.
    :returns: ebNodeFSLayout after the resize.
    """

    ebLogInfo(
        f"*** Start resize of {domu_fs_tree.filesystem.mountpoint} "
        f"on {domu_node.mGetHostname()} ; "
        f"Initial size: {domu_fs_tree.lv.size_bytes} bytes, "
        f"Using dev: {disk_id}, "
        f"Resize mode: {resize_mode}"
    )

    disk_dev: str = f"/dev/{disk_id}"
    part_dev: str = get_last_part_dev_for_disk(domu_node, disk_dev)

    PVCREATE: str = node_cmd_abs_path_check(domu_node, 'pvcreate', sbin=True)
    VGEXTEND: str = node_cmd_abs_path_check(domu_node, 'vgextend', sbin=True)

    node_exec_cmd_check(domu_node, f"{PVCREATE} {part_dev}")
    node_exec_cmd_check(
        domu_node,
        f"{VGEXTEND} {domu_fs_tree.vg.name} {part_dev}"
    )

    new_fs_layout: ebNodeFSLayout = get_node_fs_layout(domu_node)
    new_fs_tree: ebNodeFSTree = get_domu_filesystem_tree(
        new_fs_layout,
        filesystem
    )
    if resize_mode == ebDomUFSResizeMode.VG_ONLY:
        ebLogInfo(
            f"*** Finished resize of {new_fs_tree.vg.name} "
            f"on {domu_node.mGetHostname()} ; "
            f"Initial size: {domu_fs_tree.vg.size_bytes} bytes, "
            f"Final size: {new_fs_tree.vg.size_bytes} bytes."
        )
        return new_fs_layout

    extra_bytes: int = new_fs_tree.vg.free_bytes - domu_fs_tree.vg.free_bytes
    if filesystem in FS_WITH_DUPLICATED_VOLUME:
        extra_bytes //= 2

    return expand_domu_fs_using_free_vg(
        domu_node,
        new_fs_tree,
        filesystem,
        extra_bytes,
        resize_mode
    )



def expand_domu_fs_using_existing_dev(
    domu_node: exaBoxNode,
    domu_fs_tree: ebNodeFSTree,
    filesystem: ebDomUFilesystem,
    extra_bytes: int,
    resize_mode: ebDomUFSResizeMode = ebDomUFSResizeMode.NORMAL
) -> ebNodeFSLayout:
    """
    Expands the specified DomU filesystem using and already existing disk
    device.

    If the filesystem is not LVM based, the whole free space of the disk will
    be used.

    NOTE: The extra_bytes must be a multiple of the Physical Extend (PE) size
    for this volume group, which is commonly 4 mibibytes for most systems.
    If it is not, it will automatically be rounded op to the next PE.
    For example: 7MiB and 5MiB will be rounded to 8MiB.

    NOTE: The initial and final sizes logged are actually the logical volume
    sizes and not the filesystem sizes, this is because the logical volume
    size is commonly an exact number of gigabytes. If the filesystem is not in
    a logical volume, then the size of the filesystem itself will be logged.

    :param domu_node: DomU node.
    :param domu_fs_tree: DomU filesystem information tree.
    :param filesystem: Filesystem to resize.
    :param extra_bytes: Extra bytes to resize the filesystem.
    :param resize_mode: Resize mode, see ebDomUFSResizeMode to get more info.
    :returns: ebNodeFSLayout after the resize.
    :raises ExacloudRuntimeError: If an error ocurred, the filesystem type
        is unknown or there's no enough space in the volume group to perform
        the filesystem expansion.
    """

    fs_bytes: int = domu_fs_tree.lv.size_bytes if domu_fs_tree.lv \
        else domu_fs_tree.filesystem.size_bytes

    ebLogInfo(
        f"*** Start resize of {domu_fs_tree.filesystem.mountpoint} "
        f"on {domu_node.mGetHostname()} ; "
        f"Initial size: {fs_bytes} bytes, "
        f"Requested size {extra_bytes} bytes, "
        f"Resize mode: {resize_mode}"
    )


    # HACK: First we fix the backup GPT table of the disk if needed.
    part_devs: List[str] = [pv.name for pv in domu_fs_tree.pvs] if domu_fs_tree.pvs \
        else [domu_fs_tree.filesystem.device]
    
    for part_dev in part_devs:
        ebLogInfo(f"Processing partition device: {part_dev} "
            f"on {domu_node.mGetHostname()}")
        # See bug: 35545832.
        # Since Exadata only creates GTP disk images for LVM-based filesystems
        # We will skip filesystem resize and backup GPT table fixing if the
        # filesystem is not included in any logical volume and is encrypted
        if domu_fs_tree.lv is None and part_dev.endswith("crypt"):
            ebLogWarn("*** Skipping resize on encrypted fs: "
                f"{domu_fs_tree.filesystem.mountpoint}")
            return get_node_fs_layout(domu_node)

        disk_dev: str = get_disk_for_part_dev(domu_node, part_dev)
        ECHO: str = node_cmd_abs_path_check(domu_node, 'echo')
        PARTED: str = node_cmd_abs_path_check(domu_node, 'parted', sbin=True)
        node_exec_cmd_check(
            domu_node,
            f"{ECHO} 'Fix\nFix' | {PARTED} {disk_dev} ---pretend-input-tty print"
        )

        # Now we check if the filesystem is in a logical volume.
        if domu_fs_tree.lv is None:
            return expand_domu_fs_using_mountpoint(
                domu_node,
                domu_fs_tree,
                filesystem
            )

        # Get the rest of the executables.
        PVRESIZE: str = node_cmd_abs_path_check(domu_node, 'pvresize', sbin=True)

        # Obtain the partition number and resize.
        # We're being quite paranoic here, just in case that for example the disk
        # device looks something like /dev/loop2 and the partition device looks
        # like /dev/loop2p42, so the partition number is 42.
        part_num: int = int(''.join(filter(
            lambda c: c in string.digits,
            part_dev[len(disk_dev):]
        )))

        node_exec_cmd_check(
            domu_node,
            f"{PARTED} {disk_dev} resizepart {part_num} 100%"
        )
        node_exec_cmd_check(domu_node, f"{PVRESIZE} {part_dev}")

    # The layout has changed since we resized the physical volume and thus
    # the volume group free size, let's update that info so that we can check
    # if we have enough space to resize the filesystem.
    new_fs_layout: ebNodeFSLayout = get_node_fs_layout(domu_node)
    new_fs_tree: ebNodeFSTree = get_domu_filesystem_tree(
        new_fs_layout,
        filesystem
    )
    if resize_mode == ebDomUFSResizeMode.VG_ONLY:
        ebLogInfo(
            f"*** Finished resize of {new_fs_tree.vg.name} "
            f"on {domu_node.mGetHostname()} ; "
            f"Initial size: {domu_fs_tree.vg.size_bytes} bytes, "
            f"Final size: {new_fs_tree.vg.size_bytes} bytes."
        )
        return new_fs_layout

    pe_bytes: int = new_fs_tree.vg.pe_bytes
    required_bytes: int = math.ceil(extra_bytes / pe_bytes) * pe_bytes
    if filesystem in FS_WITH_DUPLICATED_VOLUME:
        required_bytes *= 2
    if new_fs_tree.vg.free_bytes < required_bytes:
        msg: str = (
            f"Cannot resize logical volume {new_fs_tree.lv.name} ; "
            f"Required size: {required_bytes} bytes, "
            f"Available size: {new_fs_tree.vg.free_bytes} bytes."
        )
        raise ExacloudRuntimeError(0x10, 0xA, msg)

    return expand_domu_fs_using_free_vg(
        domu_node,
        new_fs_tree,
        filesystem,
        extra_bytes,
        resize_mode
    )



#######################################
### DOMU FILESYSTEMS RESIZE METHODS ###
#######################################


def expand_domu_filesystem(
    clu_ctrl: exaBoxCluCtrl,
    dom0_name: Optional[str] = None,
    domu_name: Optional[str] = None,
    filesystem: Optional[ebDomUFilesystem] = None,
    extra_bytes: Optional[int] = None,
    check_max_size: bool = True,
    resize_mode: ebDomUFSResizeMode = ebDomUFSResizeMode.NORMAL,
    fail_on_error: bool = True,
    perform_dom0_resize: bool = True,
    domu_reboot: bool = True,
    payload_overrides_default_sizes: bool = False,
    run_in_parallel: bool = False
) -> Dict[str, Dict[str, Dict[str, str]]]:
    """
    Expands a DomU filesystem using the preferred method for this system.

    - If the environment is KVM-based, then the resize will be achieved by
      expanding the Dom0 disk image file for the DomU.
    - If the environment is XEN-based and the filesystem is LVM-based, the
      resized will be achieved by creating and attaching a new disk image file
      to the DomU.
    - NOTE: If the environment is XEN-based and the filesystem is NOT
      LVM-based (like /u02 and the grid home filesystem), the resize will be
      achieved by expanding the Dom0 disk image file for the DomU. HOWEVER,
      in order to resize a disk image in XEN-based environments, we need first
      need to shutdown the DomU to avoid data corruption, so make sure you're
      ok with rebooting your DomU if you want to resize any of these
      filesystems.
    - NOTE: If the environment is encryption enabled, XEN-based and the
      filesystem is LVM-based (like /u01), we skip the resize of the
      filesystem on the DomU, but we execute the resize of the Logical Volume.
      Then we'll use cluencryption.py logic to first resize the LUKS device,
      and then we'll resize the underlying filesystem.
    - NOTE: If the environment is encryption enabled, XEN-based and the
      filesystem is NOT LVM-based (like /u02), we skip the resize of the
      LV and filesystem on the DomU. We will use cluencryption.py logic to
      first resize the LUKS device, and then we'll resize the underlying
      filesystem

    If no pair of Dom0 & DomU are specified, all nodes will be taken.
    If no filesystem is specified, all filesystems will be taken.
    If no extra size is specified, the filesystem will be expanded to its
    maximum allowed size for this particular system.

    :param clu_ctrl: A Clu Control object.
    :param dom0_name: Dom0 FQDN.
    :param domu_name: DomU FQDN.
    :param filesystem: DomU filesystem to resize.
    :param extra_bytes: Extra bytes to resize.
    :param check_max_size: Raise an exception if the requested size is greater
        than the maximum allowed size for this partition.
    :param resize_mode: Resize mode, see ebDomUFSResizeMode to get more info.
    :param fail_on_error: Whether to raise an Exception if a filesystem resize
                          failed.
    :param perform_dom0_resize: Whether we should resize the corresponding disk
                                image file in the Dom0 for the DomU filesystem.
    :param payload_overrides_default_sizes: Allow payload values from
                                            from "filesystems" field to
                                            override all the default sizes.
    :raises ExacloudRuntimeError: If an error ocurred or the size specified
        was greater than the maximum allowed size.
    :returns: A mapping of DomU -> Filesystem -> FS Info.
    """
    def singlenode_expand_domu_filesystem(aDom0, aDomU, aResult):
        domu = aDomU
        dom0 = aDom0
        result = aResult
        result[domu] = {}

        fs_layout: ebNodeFSLayout = None
        with connect_to_host(domu, get_gcontext()) as node:
            fs_layout = get_node_fs_layout(node)

        for fs in filesystems:

            if fs == ebDomUFilesystem.GRID and clu_ctrl.mIsExaScale():
                continue

            fs_tree: ebNodeFSTree = get_domu_filesystem_tree(fs_layout, fs, clu_ctrl)
            if not fs_tree:
                msg: str = f"Filesystem {fs.value} is not mounted in {domu}."
                ebLogWarn(msg)
                result[domu][fs.value] = { 'error': msg }
                continue

            # Take the size we're going to resize.
            # For filesystems that do not have an LV, we take the disk image
            # file size as the filesystem size to avoid dealing with the
            # padding size managed by the kernel for the filesystem.
            fs_disk_bytes: int = 0
            if fs_tree.lv is None:
                if fs_tree.filesystem.encrypted:
                    msg: str = \
                        f"*** Skipping resize of encrypted filesystem: {fs}"
                    ebLogWarn(msg)
                    result[domu][fs.value] = {
                        **fs_tree.filesystem._asdict(),
                        'error': msg
                    }
                    continue
                with connect_to_host(dom0, get_gcontext()) as node:
                    fs_disk_bytes = \
                        get_dom0_disk_for_filesystem(node, domu, fs).size_bytes
            fs_bytes: int = fs_tree.inactive_lv.size_bytes \
                if fs in FS_WITH_DUPLICATED_VOLUME and \
                resize_mode == ebDomUFSResizeMode.SND_VOL_ONLY \
                else fs_tree.lv.size_bytes if fs_tree.lv else fs_disk_bytes

            fs_max_bytes: Optional[int] = fs_size_limits.get(fs)
            fs_extra_bytes: Optional[int] = extra_bytes
            if fs_extra_bytes is None:
                if fs_max_bytes is None:
                    msg: str = (
                        f"*** Maximum allowed size for "
                        f"{fs_tree.filesystem.mountpoint} is unknown. "
                        "Skipping."
                    )
                    ebLogWarn(msg)
                    result[domu][fs.value] = {
                        **fs_tree.filesystem._asdict(),
                        'error': msg
                    }
                    continue

                # Here is where it gets tricky, basically, we have to consider
                # 2 different scenarios for filesystems with duplicate LVs and
                # the request is to increase both of them.
                # 1st - Both active and inactive LVs are lower than the max FS
                #       size: In this case we resize both LVs to the max FS
                #       size regardless of their initial size
                # 2nd - Al least one of the LVs is bigger than the max FS size:
                #       For this case, we increase the max FS size to the size
                #       of the biggest LV, so the request will be modified to
                #       always try to keep both LVs at the same size.
                if fs in FS_WITH_DUPLICATED_VOLUME and resize_mode in (
                    ebDomUFSResizeMode.NORMAL, ebDomUFSResizeMode.LV_ONLY):
                    fs_max_bytes = max(
                        fs_max_bytes,
                        fs_tree.lv.size_bytes,
                        fs_tree.inactive_lv.size_bytes
                    )
                elif fs_max_bytes <= fs_bytes:
                    msg: str = (
                        f"*** Maximum allowed size for "
                        f"{fs_tree.filesystem.mountpoint} is "
                        f"{fs_max_bytes} bytes, but filesystem is already "
                        f"{fs_bytes} bytes. Skipping."
                    )
                    ebLogWarn(msg)
                    result[domu][fs.value] = {
                        **fs_tree.filesystem._asdict(),
                        'error': msg
                    }
                    continue

                fs_extra_bytes = fs_max_bytes - fs_bytes


            # Validate we don't exceed the maximum filesystem allowed size.
            if check_max_size and fs_max_bytes is not None:
                if fs_bytes + fs_extra_bytes > fs_max_bytes:
                    msg: str = (
                        f"DomU {domu} "
                        f"filesystem {fs_tree.filesystem.mountpoint} "
                        f"can only grow {fs_max_bytes - fs_bytes} "
                        f"extra bytes, but {fs_extra_bytes} bytes "
                        f"were requested."
                    )
                    ebLogError(msg)
                    result[domu][fs.value] = {
                        **fs_tree.filesystem._asdict(),
                        'error': msg
                    }
                    continue


            # Consider the minimum VG free size for Dom0 resize.
            # It is also possible that Dom0 resize can be skipped if there is
            # enough free size in the VG for LV expansion.
            dom0_extra_bytes: int = fs_extra_bytes
            if resize_mode != ebDomUFSResizeMode.VG_ONLY and fs_tree.lv:
                dom0_required_bytes: int = fs_extra_bytes
                if fs in FS_WITH_DUPLICATED_VOLUME and resize_mode in (
                    ebDomUFSResizeMode.NORMAL, ebDomUFSResizeMode.LV_ONLY):
                    dom0_required_bytes += \
                        fs_max_bytes - fs_tree.inactive_lv.size_bytes
                dom0_extra_bytes = dom0_required_bytes + \
                    vg_size_limits.get(fs_tree.vg.name, 2 * GIB) - \
                    fs_tree.vg.free_bytes


            # Finally, perform the actual resize routine.
            try:
                if clu_ctrl.mIsKVM() or fs_tree.lv is None:
                    if perform_dom0_resize:
                        if dom0_extra_bytes <= 0:
                            ebLogWarn(
                                f"{fs_tree.vg.name} has already "
                                f"{fs_tree.vg.free_bytes} bytes free"
                                ", skipping Dom0 image resize..."
                            )
                        else:
                            with connect_to_host(dom0, get_gcontext()) as node:
                                resize_disk_image_for_filesystem(
                                    node,
                                    domu,
                                    fs,
                                    dom0_extra_bytes,
                                    domu_reboot = domu_reboot,
                                    pre_resize_callback = _resize_xs_edv
                                )

                    with connect_to_host(domu, get_gcontext()) as node:
                        fs_layout = expand_domu_fs_using_existing_dev(
                            node,
                            fs_tree,
                            fs,
                            fs_extra_bytes,
                            resize_mode
                        )

                else:
                    if dom0_extra_bytes <= 0:
                        ebLogWarn(
                            f"{fs_tree.vg.name} has already "
                            f"{fs_tree.vg.free_bytes} bytes free"
                            ", skipping Dom0 image resize..."
                        )
                        with connect_to_host(domu, get_gcontext()) as node:
                            fs_layout = expand_domu_fs_using_existing_dev(
                                node,
                                fs_tree,
                                fs,
                                fs_extra_bytes,
                                resize_mode
                            )
                    else:
                        new_disk_id: str = ''
                        with connect_to_host(dom0, get_gcontext()) as node:
                            now_str: str = \
                                datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                            disk_name: str = f"fs_resize_{now_str}.img"
                            # We're adding an extra Physical Extend to the disk
                            # image size because the first bytes of the disk
                            # image are always used for storing the partition
                            # table metadata, and since we're not able to 
                            # determine the size of that metadata, we simply add
                            # the extra sacrified PE to the disk image size.
                            new_disk = ebDiskImageInfo(
                                f"/EXAVMIMAGES/GuestImages/{domu}/{disk_name}",
                                dom0_extra_bytes + fs_tree.vg.pe_bytes,
                                'raw',
                                'gpt'
                            )
                            create_new_lvm_disk_image(node, new_disk)
                            new_disk_id = attach_dom0_disk_image(
                                node,
                                domu,
                                new_disk.path
                            )

                        with connect_to_host(domu, get_gcontext()) as node:
                            fs_layout = expand_domu_fs_using_new_dev(
                                node,
                                fs_tree,
                                fs,
                                new_disk_id,
                                resize_mode
                            )

            except Exception as ex:
                msg: str = (
                    f"An error ocurrer while resizing the {filesystem} in "
                    f"DomU {domu}. Exception: {ex}"
                )
                ebLogError(msg)
                result[domu][fs.value] = {
                    **fs_tree.filesystem._asdict(),
                    'error': str(ex)
                }
                if fail_on_error:
                    raise ExacloudRuntimeError(0x10, 0xA, msg) from ex
                continue

            fs_tree = get_domu_filesystem_tree(fs_layout, fs)
            result[domu][fs.value] = fs_tree.filesystem._asdict()


    # Take the filesystems we're going to resize.
    filesystems: List[ebDomUFilesystem] = \
        ebDomUFilesystem if clu_ctrl.mIsKVM() \
            else XEN_DOMU_FILESYSTEMS

    if filesystem is None:
        extra_bytes = None
    else:
        if filesystem not in filesystems:
            ebLogWarn(
                f"*** Filesystem {filesystem} not available in this "
                f"environment. Sipping."
            )
        filesystems = [ filesystem ]


    # First we validate the given arguments.
    if extra_bytes is not None and extra_bytes <= 0:
        msg: str = (
            f"Requested resize of {extra_bytes} bytes but "
            f"cannot shrink any filesystem with this method."
        )
        raise ExacloudRuntimeError(0x10, 0xA, msg)


    # Calculate the filesystems maximum sizes for this specific system.
    fs_size_limits: Dict[ebDomUFilesystem, int] = \
        get_max_domu_filesystem_sizes(
            clu_ctrl,
            use_defaults = not payload_overrides_default_sizes
        )

    # Calculate the minimum reserved free sizes for each VG.
    vg_size_limits: Dict[str, int] = {
        'VGExaDb': 2 * GIB
    }


    # Take the nodes we're going to resize.
    nodes: List[List[str]] = clu_ctrl.mReturnDom0DomUPair()
    if dom0_name is not None and domu_name is not None:
        if [dom0_name, domu_name] not in nodes:
            msg: str = (
                f"Dom0 {dom0_name} and DomU {dom0_name} "
                f"are not nodes of this cluster."
            )
            raise ExacloudRuntimeError(0x10, 0xA, msg)
        nodes = [[dom0_name, domu_name]]


    # Helper method to resize Exascale EDVs.
    xs_utils = clu_ctrl.mGetExascaleUtils()
    def _resize_xs_edv(disk_path: str, new_bytes: int):
        if not disk_path.startswith('/dev/exc/'):
            return
        vol_name = '_'.join(os.path.basename(disk_path).split('_')[:-1])
        xs_utils.mResizeEDVVolume(vol_name, f"{new_bytes}b")


    
    if run_in_parallel:
        _plist = ProcessManager()
        result: Dict[str, Dict[str, Dict[str, str]]] = _plist.mGetManager().dict()
        for dom0, domu in nodes:
            _p = ProcessStructure(singlenode_expand_domu_filesystem, [dom0, domu, result], domu)
            _p.mSetMaxExecutionTime(30*60) # 30 minutes
            _p.mSetJoinTimeout(5)
            _p.mSetLogTimeoutFx(ebLogWarn)
            _plist.mStartAppend(_p)

        _plist.mJoinProcess()
        return result
    else:
        result: Dict[str, Dict[str, Dict[str, str]]] = {}
        for dom0, domu in nodes:
            singlenode_expand_domu_filesystem(dom0, domu, result)
        return result

    



def expand_domu_vg(
    clu_ctrl: exaBoxCluCtrl,
    dom0_name: Optional[str] = None,
    domu_name: Optional[str] = None,
    vg_name: Optional[str] = None,
    extra_bytes: Optional[int] = None,
    check_max_size: bool = True
):
    """
    Expands a DomU volume group without expanding any filesystems nor the
    logical volumes, in other words, just expands the free size.
    This method is useful for reserving space needed for LVM snapshots.

    If no pair of Dom0 & DomU are specified, all nodes will be taken.
    If no VG name is specified, all VGs will be taken.
    If no extra size is specified, the VG will be expanded to its maximum
    allowed size for this particular system.

    :param clu_ctrl: A Clu Control object.
    :param dom0_name: Dom0 FQDN.
    :param domu_name: DomU FQDN.
    :param vg_name: DomU VG to resize.
    :param extra_bytes: Extra bytes to resize.
    :param check_max_size: Raise an exception if the requested size is greater
        than the maximum allowed size for this VG.
    :raises ExacloudRuntimeError: If an error ocurred or the size specified
        was greater than the maximum allowed size.
    """

    # Take the nodes we're going to resize.
    nodes: List[List[str]] = clu_ctrl.mReturnDom0DomUPair()
    if dom0_name is not None and domu_name is not None:
        if [dom0_name, domu_name] not in nodes:
            msg: str = (
                f"Dom0 {dom0_name} and DomU {dom0_name} "
                f"are not nodes of this cluster."
            )
            raise ExacloudRuntimeError(0x10, 0xA, msg)
        nodes = [[dom0_name, domu_name]]

    # Calculate the VG maximum free sizes for this specific system.
    vg_size_limits: Dict[str, int] = {} if clu_ctrl.mIsKVM() else {
        'VGExaDb': 2 * GIB
    }

    for dom0, domu in nodes:

        fs_layout: ebNodeFSLayout = None
        with connect_to_host(domu, get_gcontext()) as node:
            fs_layout = get_node_fs_layout(node)

        # Take the VGs we're going to resize.
        vgs: List[ebNodeVGInfo] = fs_layout.vgs

        if vg_name is None:
            extra_bytes = None
        else:
            if vg_name not in ( vg.name for vg in vgs ):
                ebLogWarn(
                    f"*** VG {vg_name} not available in this "
                    f"environment. Sipping."
                )
            vgs = [ vg for vg in vgs if vg.name == vg_name ]

        for vg in vgs:

            # Take the size we're going to resize.
            vg_max_free_bytes: Optional[int] = vg_size_limits.get(vg.name)
            vg_extra_bytes: Optional[int] = extra_bytes
            if vg_extra_bytes is None:
                if vg_max_free_bytes is None:
                    ebLogWarn(
                        f"*** Maximum allowed size for {vg.name} VG "
                        "is unknown. Skipping."
                    )
                    continue

                if vg_max_free_bytes <= vg.free_bytes:
                    ebLogInfo(
                        f"*** Maximum allowed free size for "
                        f"{vg.name} VG is {vg_max_free_bytes} bytes, "
                        f"but VG free size is already "
                        f"{vg.free_bytes} bytes. Skipping."
                    )
                    continue

                vg_extra_bytes = vg_max_free_bytes - vg.free_bytes

            # Validate we don't exceed the maximum VG allowed size.
            if check_max_size and vg_max_free_bytes is not None:
                if vg.free_bytes + vg_extra_bytes > vg_max_free_bytes:
                    msg: str = (
                        f"DomU {domu} "
                        f"VG {vg.name} "
                        f"can only grow {vg_max_free_bytes - vg.free_bytes} "
                        f"extra bytes, but {vg_extra_bytes} bytes "
                        f"were requested."
                    )
                    raise ExacloudRuntimeError(0x10, 0xA, msg)

            # Now just get any filesystem that is in this VG and resize.
            lv_info, *_ = [
                lv for lv in fs_layout.lvs
                if lv.vg_name == vg.name
            ]
            fs_info, *_ = [
                fs for fs in fs_layout.filesystems
                if fs.device == lv_info.dm_path or \
                    fs.device == f"{lv_info.dm_path}-crypt"
            ]
            fs: ebDomUFilesystem = ebDomUFilesystem(fs_info.mountpoint)

            expand_domu_filesystem(
                clu_ctrl,
                dom0,
                domu,
                fs,
                vg_extra_bytes,
                False,
                ebDomUFSResizeMode.VG_ONLY
            )
