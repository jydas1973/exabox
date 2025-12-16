#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_domufilesystems.py /main/28 2025/11/14 17:04:47 scoral Exp $
#
# tests_domufilesystems.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_domufilesystems.py - Unit tests for cludomufilesystems.py
#
#    DESCRIPTION
#      Unit tests for cludomufilesystems.py
#
#    NOTES
#      None.
#
#    MODIFIED   (MM/DD/YY)
#    rajsag      10/29/25 - bug 38484985 - exascale- exacloud: add vm to
#                           exascale cluster with exascale images failed
#    remamid     09/30/25 - Add unittest for bug 38453991
#    bhpati      07/10/25 - Bug 37997054 - Handle fsresize if more than 1 pv
#                           are assigned to VG
#    nelango     05/19/25 - Bug 37683920 - Improvise
#                           get_last_part_dev_for_disk_cmds
#    prsshukl    04/14/25 - Bug 37820151 - Additional test case for
#                           vm_active_list
#    remamid     02/27/25 - Adding a unittest for shutdown_domu failure to
#                           correctly identify VM to stop Bug 37630591
#    bhpati      02/21/25 - Bug 37609714 - skip grid filesystem check if it
#                           does not exist during filesystem resize
#    asrigiri    10/31/24 - Bug 36981061 - EXACC:LOCAL FS RESIZE FETCHES ALL FS
#                           DETAILS INCLUDING NFS MOUNTS
#    gojoseph    10/14/24 - Bug 37086896 Force vm shudown testcase
#    jfsaldan    07/23/24 - Enh 36776061 - EXACS EXACLOUD OL8 FS ENCRYPTION :
#                           ADD SUPPORT TO RESIZE AN ENCRYPTED U01 DISK
#    jfsaldan    09/01/23 - Bug 35759673 - EXACS:23.4.1:XEN:FILE SYSTEM
#                           ENCRYPTION:SKIP RESIZE OF DOM0 IMAGE IF FS CREATED
#                           ON NON-LVM PARTITION
#    jfsaldan    06/30/23 - XbranchMerge jfsaldan_bug-35545832 from
#                           st_ecs_22.2.1.0.0
#    jfsaldan    06/29/23 - Bug 35545832 - EXACS:22.2.1:DROP4:FILE SYSTEM
#                           ENCRYPTION:XEN:PROVISIONING FAILING AT POSTGI_NID
#                           STEP
#    scoral      09/27/21 - Creation
#

import itertools
import string
import json
import os
from typing import Callable, Dict, List, Optional, NamedTuple, Set, Tuple
import unittest
from exabox.utils.node import connect_to_host
from exabox.core.Error import ExacloudRuntimeError
from unittest.mock import patch, MagicMock
from exabox.ovm.cludomufilesystems import get_edvdisk_path_from_domblklist, get_dom0_edvdisk_for_filesystem
from exabox.ovm.cludomufilesystems import (
    KIB,
    MIB,
    GIB,
    XEN_DOMU_FILESYSTEMS,
    FS_WITH_DUPLICATED_VOLUME,
    ebDomUFilesystem,
    ebDomUFSResizeMode,
    ebNodeFilesystemInfo,
    ebNodeLVInfo,
    ebNodeVGInfo,
    ebNodePVInfo,
    ebNodeFSLayout,
    ebDiskImageInfo,
    ebNodeFSTree,
    get_next_dev,
    get_last_dev,
    get_domu_filesystem_tree,
    get_max_domu_filesystem_sizes,
    expand_domu_filesystem,
    expand_domu_vg,
    shutdown_domu,
    start_domu
)

from exabox.ovm.clucontrol import exaBoxCluCtrl
from exabox.core.Context import get_gcontext
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo



class ebFilesystemsState(NamedTuple):
    fs_layout: ebNodeFSLayout
    disks: List[ebDiskImageInfo]
    space_for_vgs: int
    is_kvm: bool



TEST_ECHO_PATH: exaMockCommand = exaMockCommand('/bin/test -e /bin/echo')
TEST_LSBLK_PATH: exaMockCommand = exaMockCommand('/bin/test -e /bin/lsblk')
TEST_VIRSH_PATH: exaMockCommand = exaMockCommand('/bin/test -e /bin/virsh')
TEST_XM_PATH: exaMockCommand = exaMockCommand('/bin/test -e /sbin/xm')
TEST_QEMU_PATH: exaMockCommand = exaMockCommand('/bin/test -e /bin/qemu-img')
TEST_LS_PATH: exaMockCommand = exaMockCommand('/bin/test -e /bin/ls')
TEST_DF_PATH: exaMockCommand = exaMockCommand('/bin/test -e /bin/df')
TEST_GREP_PATH: exaMockCommand = exaMockCommand('/bin/test -e /bin/grep')
TEST_PARTED_PATH: exaMockCommand = exaMockCommand('/bin/test -e /sbin/parted')
TEST_PVR_PATH: exaMockCommand = exaMockCommand('/bin/test -e /sbin/pvresize')
TEST_LVR_PATH: exaMockCommand = exaMockCommand('/bin/test -e /sbin/lvresize')
TEST_LVS_PATH: exaMockCommand = exaMockCommand('/bin/test -e /sbin/lvs')
TEST_VGS_PATH: exaMockCommand = exaMockCommand('/bin/test -e /sbin/vgs')
TEST_PVS_PATH: exaMockCommand = exaMockCommand('/bin/test -e /sbin/pvs')
TEST_RESIZE2FS_PATH: exaMockCommand = \
    exaMockCommand('/bin/test -e /sbin/resize2fs')
TEST_XFS_GROWFS_PATH: exaMockCommand = \
    exaMockCommand('/bin/test -e /sbin/xfs_growfs')
TEST_PVCREATE_PATH: exaMockCommand = \
    exaMockCommand('/bin/test -e /sbin/pvcreate')
TEST_VGEXTEND_PATH: exaMockCommand = \
    exaMockCommand('/bin/test -e /sbin/vgextend')
TEST_VIRSH_THEN_XM: List[exaMockCommand] = [
    exaMockCommand('/bin/test -e /bin/virsh', aRc = -1),
    exaMockCommand('/bin/test -e /usr/bin/virsh', aRc = -1),
    TEST_XM_PATH
]
TEST_SYSTEMD_ANALYZE: exaMockCommand = \
    exaMockCommand('/bin/test -e /sbin/systemd-analyze')



def get_node_filesystems_cmd(
    filesystems: List[ebNodeFilesystemInfo]
) -> List[exaMockCommand]:
    """
    Gets the mock command that would output the given filesystems info.

    :param filesystems: Filesystems info
    :returns: exaMockCommand
    """

    stdout: List[str] = ['Mounted on   Filesystem   Type   1B-blocks   Avail']

    for fs_info in filesystems:
        stdout.append(
            f"{fs_info.mountpoint} "
            f"{fs_info.device} "
            f"{fs_info.fs_type} "
            f"{fs_info.size_bytes} "
            f"{fs_info.free_bytes} "
        )

    return [
        exaMockCommand(
            "/bin/df --local --output=target,source,fstype,size,avail --block-size=1 | /bin/grep -v 'nfs'",
            aStdout = '\n'.join(stdout)),
        exaMockCommand(
            '/bin/lsblk -rno TYPE.*',
            aStdout = 'lvm',
            aPersist = True)
    ]



def get_node_lvs_cmd(
    lvs: List[ebNodeLVInfo]
) -> exaMockCommand:
    """
    Gets the mock command that would output the given logical volumes info.

    :param lvs: Logical volumes info.
    :returns: exaMockCommand
    """

    stdout: List[str] = []

    for lv_info in lvs:
        stdout.append(
            f"{lv_info.name} "
            f"{lv_info.dm_path} "
            f"{lv_info.vg_name} "
            f"{lv_info.size_bytes}B "
        )

    return exaMockCommand(
        '/sbin/lvs '
        '--noheading -o lv_name,lv_dm_path,vg_name,lv_size --units B',
        aStdout = '\n'.join(stdout)
    )



def get_node_vgs_cmd(
    vgs: List[ebNodeVGInfo]
) -> exaMockCommand:
    """
    Gets the mock command that would output the given volume groups info.

    :param vgs: Volume groups info.
    :returns: exaMockCommand
    """

    stdout: List[str] = []

    for vg_info in vgs:
        stdout.append(
            f"{vg_info.name} "
            f"{vg_info.size_bytes}B "
            f"{vg_info.free_bytes}B "
            f"{vg_info.pe_bytes}B "
        )

    return exaMockCommand(
        '/sbin/vgs --noheading '
            '-o vg_name,vg_size,vg_free,vg_extent_size '
            '--units B ',
        aStdout = '\n'.join(stdout)
    )



def get_node_pvs_cmd(
    pvs: List[ebNodePVInfo]
) -> exaMockCommand:
    """
    Gets the mock command that would output the given physical volumes info.

    :param pvs: Physical volumes info.
    :returns: exaMockCommand
    """

    stdout: List[str] = []

    for pv_info in pvs:
        stdout.append(
            f"{pv_info.name} "
            f"{pv_info.vg_name} "
            f"{pv_info.size_bytes} "
        )

    return exaMockCommand(
        '/sbin/pvs --noheading -o pv_name,vg_name,pv_size --units B',
        aStdout = '\n'.join(stdout)
    )



def get_disk_partition_table_cmds(
    disk_path: str,
    part_table: str
) -> List[exaMockCommand]:
    """
    Gets all the exaMockCommand for a get_disk_partition_table call.

    :param disk_path: Disk device path.
    :param part_table: Result partition table.
    :returns: List of exaMockCommand.
    """

    return [
        TEST_PARTED_PATH,
        exaMockCommand(
            f"/sbin/parted {disk_path} print",
            aStdout=f"Partition Table: {part_table}"
        )
    ]



def get_node_fs_layout_cmds(
    fs_layout: ebNodeFSLayout
) -> List[exaMockCommand]:
    """
    Gets all the mock commands hat would output the given filesystem layout.

    :param fs_layout: Filesystems layout.
    :returns: List of exaMockCommand.
    """

    return [
        TEST_DF_PATH,
        TEST_GREP_PATH,
        TEST_LSBLK_PATH,
        TEST_LVS_PATH,
        get_node_lvs_cmd(fs_layout.lvs),
        TEST_VGS_PATH,
        get_node_vgs_cmd(fs_layout.vgs),
        TEST_PVS_PATH,
        get_node_pvs_cmd(fs_layout.pvs)
    ] + get_node_filesystems_cmd(fs_layout.filesystems)




# Auxiliary function, it simply does what its name suggests.
# For example:
#   remove_last_digits('Hello123')          == 'Hello'
#   remove_last_digits('/dev/loop42p39')    == '/dev/loop42p'
#   remove_last_digits('NoDigits')          == ''
remove_last_digits: Callable[[str], str] = lambda x: x[:-list(filter(
    lambda c: not c[0].isdigit(),
    zip(x[::-1], itertools.count())
))[0][1]]



def get_disk_for_part_dev_cmds(
    part_dev: str
) -> Tuple[str, List[exaMockCommand]]:
    """
    Gets all the exaMockCommand for a get_disk_for_part_dev call along with
    the desired disk partition dev.

    :param part_dev: str containing the partition device path.
    :returns: Tuple of str containing the disk device path and the list of
        exaMockCommands.
    """

    cmds: List[exaMockCommand] = []

    result: str = part_dev if not any(c.isdigit() for c in part_dev) \
        else remove_last_digits(part_dev)

    cmds.append(TEST_LSBLK_PATH)
    cmds.append(exaMockCommand(
        f"/bin/lsblk -pno pkname {part_dev}",
        aStdout = result
    ))

    return (result, cmds)



def get_last_part_dev_for_disk_cmds(
    disk_dev: str
) -> Tuple[str, List[exaMockCommand]]:
    """
    Gets the exaMockCommands for a get_last_part_dev_for_disk executuon.
    Since get_last_part_dev_for_disk is currently only meant to be used on
    just created disk images, we'll just append a 1 at the end of the device
    and simulate a lsblk call.

    :param disk_dev: A disk device path.
    :returns: A tuple with the partition dev and the commands meant to be run.
    """
    return (
        f"{disk_dev}1",
        [
            TEST_LSBLK_PATH,
            exaMockCommand(
                f"/bin/lsblk -pno kname {disk_dev}",
                aStdout = f"{disk_dev}"
            ),
            exaMockCommand(
                f"/bin/lsblk -pno kname {disk_dev}",
                aStdout = f"{disk_dev}1"
            )
        ]
    )



######################################
### METHODS TO ALTER THE ENV STATE ###
######################################


def shutdown_domu_cmds(
    domu_state: ebFilesystemsState,
    domu_name: str,
    attempts: int = 0,
    force_on_timeout=False
) -> List[exaMockCommand]:
    """
    Gets all the exaMockCommand for a shutdown_domu call.

    :param domu_state: A DomU state.
    :param domu_name: A DomU FQDN.
    :param attempts: Number of times we will simulate a "list" command before
        we simulate the DomU is completely shut off.
    :returns: List of exaMockCommand.
    """
    cmds: List[exaMockCommand] = []
    hypervisor: str = ''
    if domu_state.is_kvm:
        cmds.append(TEST_VIRSH_PATH)
        hypervisor = '/bin/virsh'
    else:
        cmds += TEST_VIRSH_THEN_XM
        hypervisor = '/sbin/xm'

    cmds.append(exaMockCommand(f"{hypervisor} list", aStdout = domu_name))
    cmds.append(exaMockCommand(f"{hypervisor} shutdown {domu_name}"))
    for _ in range(attempts):
        cmds.append(exaMockCommand(f"{hypervisor} list", aStdout = domu_name))
    if force_on_timeout:
        cmds.append(exaMockCommand(f"{hypervisor} destroy {domu_name}"))
    cmds.append(exaMockCommand(f"{hypervisor} list"))

    return cmds



def start_domu_cmds(
    domu_state: ebFilesystemsState,
    domu_name: str
) -> List[exaMockCommand]:
    """
    Gets all the Dom0 exaMockCommand for a start_domu call.

    :param domu_state: A DomU state.
    :param domu_name: A DomU FQDN.
    :param attempts: Number of times we will simulate a "list" command before
        we simulate the DomU is completely shut off.
    :returns: List of exaMockCommand.
    """
    cmds: List[exaMockCommand] = []
    hypervisor: str = ''
    start_vm_cmd: str = ''
    if domu_state.is_kvm:
        cmds.append(TEST_VIRSH_PATH)
        hypervisor = '/bin/virsh'
        start_vm_cmd = f"{hypervisor} start {domu_name}"
    else:
        cmds += TEST_VIRSH_THEN_XM
        hypervisor = '/sbin/xm'
        start_vm_cmd = \
            f"{hypervisor} create /EXAVMIMAGES/GuestImages/{domu_name}/vm.cfg"

    cmds.append(exaMockCommand(f"{hypervisor} list"))
    cmds.append(exaMockCommand(start_vm_cmd))

    return cmds



def get_dom0_edvdisk_for_filesystem_cmds(
    dom0_disks: List[ebDiskImageInfo],
    domu_name: str,
    filesystem: ebDomUFilesystem
) -> Tuple[Optional[ebDiskImageInfo], List[exaMockCommand]]:
    """
    Gets all the exaMockCommand for a get_dom0_edvdisk_for_filesystem call along
    with the desired disk image info.

    :param domu_state: A DomU filesystems state.
    :param domu_name: A DomU FQDN.
    :param filesystem: A DomU filesystem.
    :returns: List of exaMockCommand.
    """

    cmds: List[exaMockCommand] = []

    fs = "sys"
    if filesystem == ebDomUFilesystem.U01:
        fs = "u01"
    elif filesystem == ebDomUFilesystem.U02:
        fs = "u02"
    elif filesystem == ebDomUFilesystem.GRID:
        fs = "gih01"

    disks_match: List[ebDiskImageInfo] = [
        disk for disk in dom0_disks if f'/{fs}' in disk.path or f'_{fs}_'
    ]

    cmds.append(TEST_VIRSH_PATH)
    cmds.append(exaMockCommand(
        f"/bin/virsh domblklist {domu_name} \| /bin/grep -e /{fs} -e _{fs}_",
        aRc = 0 if disks_match else 1,
        aStdout = f"sdx {disks_match[0].path}" if disks_match else ""
    ))
    
    if not disks_match:
        return (None, cmds)

    disk_info: ebDiskImageInfo = disks_match[0]

    cmds.append(TEST_QEMU_PATH)
    cmds.append(exaMockCommand(
        f"/bin/qemu-img info --output=json {disk_info.path}",
        aStdout = json.dumps({
            'virtual-size': disk_info.size_bytes,
            'format': disk_info.file_format
        })
    ))
    cmds += get_disk_partition_table_cmds(
        disk_info.path,
        disk_info.partition_table
    )

    return (disk_info, cmds)



def get_dom0_disk_for_filesystem_cmds(
    dom0_disks: List[ebDiskImageInfo],
    domu_name: str,
    filesystem: ebDomUFilesystem
) -> Tuple[ebDiskImageInfo, List[exaMockCommand]]:
    """
    Gets all the exaMockCommand for a get_dom0_disk_for_filesystem call along
    with the desired disk image info.

    :param domu_state: A DomU filesystems state.
    :param domu_name: A DomU FQDN.
    :param filesystem: A DomU filesystem.
    :returns: List of exaMockCommand.
    """

    disk_info, cmds = get_dom0_edvdisk_for_filesystem_cmds(
        dom0_disks,
        domu_name,
        filesystem
    )
    if disk_info is not None:
        return (disk_info, cmds)

    cmds: List[exaMockCommand] = []

    disk_images: str = os.path.join('/EXAVMIMAGES/GuestImages', domu_name)
    disk_image_name: str = os.path.join(disk_images, 'System.img')

    if filesystem == ebDomUFilesystem.U01:
        u01_disk_image: str = os.path.join(disk_images, 'u01.img')
        u01_disk_image_exists: bool = any(
            disk.path == u01_disk_image for disk in dom0_disks
        )
        cmds.append(exaMockCommand(
            f"/bin/test -e {u01_disk_image}",
            aRc = 0 if u01_disk_image_exists else -1
        ))
        if u01_disk_image_exists:
            disk_image_name = u01_disk_image

    elif filesystem == ebDomUFilesystem.U02:
        disk_image_name = os.path.join(disk_images, 'u02_extra.img')
        cmds.append(exaMockCommand(
            f"/bin/test -e {disk_image_name}",
            aRc = 0 ))

    elif filesystem == ebDomUFilesystem.GRID:
        grid_images: str = os.path.join(disk_images, 'grid\*.img')
        cmds.append(TEST_LS_PATH)
        disk_image_name, *_ = [
            disk.path for disk in dom0_disks
            if 'grid' in disk.path
        ]
        cmds.append(exaMockCommand(
            f"/bin/ls {grid_images}",
            aStdout = disk_image_name
        ))

    disk_info, *_ = filter(
        lambda disk: disk.path == disk_image_name,
        dom0_disks
    )
    cmds.append(TEST_QEMU_PATH)
    cmds.append(exaMockCommand(
        f"/bin/qemu-img info --output=json {disk_image_name}",
        aStdout = json.dumps({
            'virtual-size': disk_info.size_bytes,
            'format': disk_info.file_format
        })
    ))
    cmds += get_disk_partition_table_cmds(
        disk_image_name,
        disk_info.partition_table
    )

    return (disk_info, cmds)



def check_user_space_ready_cmds(exit_code: int) -> List[exaMockCommand]:
    """
    Gets all the exaMockCommand for a check_user_space_ready call.

    :param exit_code: Exit code of systemd-analyze.
    :returns: List of exaMockCommand.
    """

    return [
        TEST_SYSTEMD_ANALYZE,
        exaMockCommand('/sbin/systemd-analyze time', aRc=exit_code)
    ]



def create_new_lvm_disk_image_cmds(
    domu_state: ebFilesystemsState,
    disk_info: ebDiskImageInfo
) -> Tuple[ebFilesystemsState, List[exaMockCommand]]:
    """
    Gets all the ExaMochCommand for a create_new_lvm_disk_image call.

    :param domu_state: A DomU filesystems state.
    :param disk_info: The disk info for the disk that is pretended to be added.
    :returns: A new ebFilesystemState with the updated disk image and the list
        of commands.
    """
    cmds: List[exaMockCommand] = []
    cmds.append(exaMockCommand(f"/bin/test -e {disk_info.path}", aRc = -1))
    cmds.append(TEST_QEMU_PATH)
    cmds.append(exaMockCommand(
        "/bin/qemu-img create "
        f"{disk_info.path} "
        f"{disk_info.size_bytes}B "
        f"-f {disk_info.file_format} "
    ))
    cmds.append(TEST_PARTED_PATH)
    cmds.append(exaMockCommand(f"/sbin/parted -s {disk_info.path} mktable gpt"))
    cmds.append(exaMockCommand(
        f"/sbin/parted -s {disk_info.path} mkpart primary 0% 100%"
    ))
    cmds.append(exaMockCommand(f"/sbin/parted {disk_info.path} set 1 lvm on"))

    domu_state.disks.append(disk_info)
    new_domu_state: ebFilesystemsState = ebFilesystemsState(
        domu_state.fs_layout,
        domu_state.disks,
        domu_state.space_for_vgs + disk_info.size_bytes,
        domu_state.is_kvm
    )
    return (new_domu_state, cmds)



def attach_dom0_disk_image_cmds(
    domu_state: ebFilesystemsState,
    domu_name: str,
    disk_path: str
) -> Tuple[str, List[exaMockCommand]]:
    """
    Gets all the exaMockCommand for a attach_dom0_disk_image call.

    :param domu_state: A DomU filesystem state.
    :param domu_name: A DomU FQDN.
    :param disk_path: A disk image file full path on the Dom0.
    :returns: A tuple with the next device that should be attached to the DomU
        and the list of commands.
    """
    cmds: List[exaMockCommand] = []
    file_exists: bool = any(
        disk_path == disk.path for disk in domu_state.disks
    )
    cmds.append(exaMockCommand(
        f"/bin/test -e {disk_path}",
        aRc = 0 if file_exists else -1
    ))
    if not domu_state.is_kvm:
        cmds += TEST_VIRSH_THEN_XM

        vm_disks_devs: List[str] = [
            f"{unit.split('/')[-1]}" for unit in
            [ 
                remove_last_digits(pv.name) for pv in domu_state.fs_layout.pvs
            ] + [
                fs.device for fs in domu_state.fs_layout.filesystems
                if fs.device.startswith('/dev/xvd')
            ]
        ]
        devs_str: str = ', '.join(f"',{dev},'" for dev in vm_disks_devs)
        cmds.append(exaMockCommand(
            f"/bin/cat /EXAVMIMAGES/GuestImages/{domu_name}/vm.cfg",
            aStdout=f"disk = [{devs_str}]"
        ))
        cmds.append(exaMockCommand('/sbin/xm list', aStdout=domu_name))
        next_vm_disk = get_next_dev(get_last_dev(vm_disks_devs), 3)
        cmds.append(exaMockCommand(
            f"/sbin/xm block-attach "
                f"{domu_name} "
                f"file://{disk_path} "
                f"/dev/{next_vm_disk} "
                f"w "
        ))

    return (next_vm_disk, cmds)



def resize_disk_image_cmds(
    domu_state: ebFilesystemsState,
    dom0_name: str,
    domu_name: str,
    filesystem: ebDomUFilesystem,
    extra_bytes: int
) -> Tuple[ebFilesystemsState, Dict[str, Optional[List[exaMockCommand]]]]:
    """
    Gets all the exaMockCommand for a resize_disk_image_for_filesystem call.

    :param domu_state: A DomU filesystems state.
    :param dom0_name: A Dom0 FQDN.
    :param domu_name: A DomU FQDN.
    :param filesystem: A DomU filesystem.
    :param extra_bytes: Extra bytes to expand the image.
    :returns: A new ebFilesystemState with the updated disk image and a Dict of
        Node FQDN -> Optional List of ExaMockCommands.
    """

    cmds: List[exaMockCommand] = []
    disk, get_disk_cmds = get_dom0_disk_for_filesystem_cmds(
        domu_state.disks,
        domu_name,
        filesystem
    )
    cmds += get_disk_cmds

    domu_cmds: Optional[List[exaMockCommand]] = None
    new_bytes: int = disk.size_bytes + extra_bytes
    if domu_state.is_kvm:
        cmds.append(TEST_VIRSH_PATH)
        cmds.append(exaMockCommand(
            f"/bin/virsh blockresize {domu_name} {disk.path} {new_bytes}B"
        ))
    else:
        cmds += TEST_VIRSH_THEN_XM
        cmds.append(TEST_QEMU_PATH)
        cmds += shutdown_domu_cmds(domu_state, domu_name)
        cmds.append(exaMockCommand(
            f"/bin/qemu-img resize "
                f"{disk.path} "
                f"-f {disk.file_format} "
                f"{new_bytes}"
        ))
        cmds += start_domu_cmds(domu_state, domu_name)
        domu_cmds = check_user_space_ready_cmds(1) + \
            check_user_space_ready_cmds(0)


    new_disk: ebDiskImageInfo = ebDiskImageInfo(
        disk.path,
        new_bytes,
        disk.file_format,
        disk.partition_table
    )
    domu_state.disks[domu_state.disks.index(disk)] = new_disk

    cmds += get_dom0_disk_for_filesystem_cmds(
        domu_state.disks,
        domu_name,
        filesystem
    )[1]

    return (
        ebFilesystemsState(
            domu_state.fs_layout,
            domu_state.disks,
            domu_state.space_for_vgs + extra_bytes,
            domu_state.is_kvm
        ),
        { dom0_name: cmds, domu_name: domu_cmds }
    )



def expand_domu_fs_using_mountpoint_cmds(
    domu_state: ebFilesystemsState,
    domu_fs_tree: ebNodeFSTree,
    filesystem: ebDomUFilesystem
) -> Tuple[ebFilesystemsState, List[exaMockCommand]]:
    """
    Gets all the exaMockcommands for a expand_domu_fs_using_mountpoint call.

    :param domu_state: A DomU state.
    :param domu_fs_tree: A DomU filesystem tree.
    :param filesystem: A Filesystem to resize.
    :returns A tuple with the updated ebFilesystemsState along with the list
        of exaMockCommands.
    """
    cmds: List[exaMockCommand] = []

    if domu_fs_tree.filesystem.fs_type.startswith('ext'):
        cmds.append(TEST_RESIZE2FS_PATH)
        cmds.append(exaMockCommand(
            f"/sbin/resize2fs {domu_fs_tree.filesystem.device}"
        ))
    elif domu_fs_tree.filesystem.fs_type == 'xfs':
        cmds.append(TEST_XFS_GROWFS_PATH)
        cmds.append(exaMockCommand(
            f"/sbin/xfs_growfs {domu_fs_tree.filesystem.device}"
        ))

    ix: int = domu_state.fs_layout.filesystems.index(domu_fs_tree.filesystem)
    domu_state.fs_layout.filesystems[ix] = ebNodeFilesystemInfo(
        domu_state.fs_layout.filesystems[ix].mountpoint,
        domu_state.fs_layout.filesystems[ix].device,
        domu_state.fs_layout.filesystems[ix].fs_type,
        domu_state.fs_layout.filesystems[ix].size_bytes + \
            domu_state.space_for_vgs,
        domu_state.fs_layout.filesystems[ix].free_bytes + \
            domu_state.space_for_vgs,
        domu_state.fs_layout.filesystems[ix].encrypted,
    )
    cmds += get_node_fs_layout_cmds(domu_state.fs_layout)

    return (
        ebFilesystemsState(
            domu_state.fs_layout,
            domu_state.disks,
            0,
            domu_state.is_kvm
        ),
        cmds
    )



def expand_domu_fs_using_free_vg_cmds(
    domu_state: ebFilesystemsState,
    domu_fs_tree: ebNodeFSTree,
    filesystem: ebDomUFilesystem,
    extra_bytes: int,
    resize_mode: ebDomUFSResizeMode,
    secondary_lv_occupied: bool = True
) -> Tuple[ebFilesystemsState, List[exaMockCommand]]:
    """
    Gets all the exaMockcommands for a expand_domu_fs_using_free_vg run.

    :param domu_state: A DomU state.
    :param domu_fs_tree: A DomU filesystem tree.
    :param filesystem: A DomU filesystem to resize.
    :param extra_bytes: Extra bytes to resize.
    :returns: A tuple with the updated ebFilesystemsState along with the list
        of exaMockcommands.
    """
    cmds: List[exaMockCommand] = []
    cmds.append(TEST_LVR_PATH)

    resize_fs_flag: str = '--resizefs'
    if resize_mode == ebDomUFSResizeMode.LV_ONLY or \
        domu_fs_tree.filesystem.device.endswith('crypt'):
        resize_fs_flag = ''

    if extra_bytes > 0 and resize_mode != ebDomUFSResizeMode.SND_VOL_ONLY:
        cmds.append(exaMockCommand(
            f"/sbin/lvresize "
                f"{resize_fs_flag} "
                f"-L \+{extra_bytes}B "
                f"{domu_fs_tree.lv.dm_path} "
        ))

    if filesystem in FS_WITH_DUPLICATED_VOLUME and \
        resize_mode != ebDomUFSResizeMode.FST_VOL_ONLY:
        secondary_lv: str = domu_fs_tree.lv.dm_path[:-1] + \
            ('2' if domu_fs_tree.lv.dm_path[-1] == '1' else '1')
        cmds += get_disk_partition_table_cmds(
            secondary_lv,
            'loop' if secondary_lv_occupied else 'unknown'
        )
        if not secondary_lv_occupied:
            resize_fs_flag = ''
        cmds.append(exaMockCommand(
            f"/sbin/lvresize "
                f"{resize_fs_flag} "
                f"-L \+{extra_bytes}B "
                f"{domu_fs_tree.lv.dm_path[:-1]}2 "
        ))

    vg_ix: int = [ vg.name for vg in domu_state.fs_layout.vgs].index(
        domu_fs_tree.vg.name
    )
    domu_state.fs_layout.vgs[vg_ix] = ebNodeVGInfo(
        domu_fs_tree.vg.name,
        domu_fs_tree.vg.size_bytes + domu_state.space_for_vgs,
        domu_fs_tree.vg.free_bytes,
        domu_fs_tree.vg.pe_bytes
    )
    domu_state.fs_layout.lvs[
        domu_state.fs_layout.lvs.index(domu_fs_tree.lv)
    ] = ebNodeLVInfo(
        domu_fs_tree.lv.name,
        domu_fs_tree.lv.dm_path,
        domu_fs_tree.lv.vg_name,
        domu_fs_tree.lv.size_bytes + domu_state.space_for_vgs
    )
    cmds += get_node_fs_layout_cmds(domu_state.fs_layout)

    return (
        ebFilesystemsState(
            domu_state.fs_layout,
            domu_state.disks,
            0,
            domu_state.is_kvm
        ),
        cmds
    )



def expand_domu_fs_using_new_dev_cmds(
    domu_state: ebFilesystemsState,
    domu_fs_tree: ebNodeFSTree,
    filesystem: ebDomUFilesystem,
    new_disk_id: str,
    resize_mode: ebDomUFSResizeMode
) -> Tuple [ebFilesystemsState, List[exaMockCommand]]:
    """
    Gets all the exaMockcommand for a expand_domu_fs_using_new_dev call.

    :param domu_state: A DomU filesystems state.
    :param domu_fs_tree: A DomU filesystem tree.
    :param filesystem: A DomU  filesystem to resize.
    :param new_disk_id: A str representing the device of the disk that we
        previously inserted.
    :param resize_mode: A resize mode.
    :returns: A tuple with the updated ebFilesystemsState along with the list
        of exaMockcommands.
    """
    cmds: List[exaMockCommand] = []
    disk_dev: str = f"/dev/{new_disk_id}"
    part_dev, get_part_cmds = get_last_part_dev_for_disk_cmds(disk_dev)
    cmds += get_part_cmds
    cmds.append(TEST_PVCREATE_PATH)
    cmds.append(TEST_VGEXTEND_PATH)
    cmds.append(exaMockCommand(f"/sbin/pvcreate {part_dev}"))
    domu_state.fs_layout.pvs.append(ebNodePVInfo(
        part_dev,
        domu_fs_tree.vg.name,
        domu_state.space_for_vgs - domu_fs_tree.vg.pe_bytes
    ))

    cmds.append(exaMockCommand(
        f"/sbin/vgextend {domu_fs_tree.vg.name} {part_dev}"
    ))
    extra_bytes: int = domu_state.space_for_vgs - domu_fs_tree.vg.pe_bytes
    vg_ix: int = domu_state.fs_layout.vgs.index(domu_fs_tree.vg)
    domu_state.fs_layout.vgs[vg_ix] = ebNodeVGInfo(
        domu_fs_tree.vg.name,
        domu_fs_tree.vg.size_bytes + extra_bytes,
        domu_fs_tree.vg.free_bytes + extra_bytes,
        domu_fs_tree.vg.pe_bytes
    )
    cmds += get_node_fs_layout_cmds(domu_state.fs_layout)

    if resize_mode == ebDomUFSResizeMode.VG_ONLY:
        return (domu_state, cmds)

    if filesystem in FS_WITH_DUPLICATED_VOLUME:
        extra_bytes //= 2

    domu_state, resize_cmds = expand_domu_fs_using_free_vg_cmds(
        domu_state,
        domu_fs_tree,
        filesystem,
        extra_bytes,
        resize_mode
    )

    return (domu_state, cmds + resize_cmds)



def expand_domu_fs_using_existing_dev_cmds(
    domu_state: ebFilesystemsState,
    domu_fs_tree: ebNodeFSTree,
    filesystem: ebDomUFilesystem,
    extra_bytes: int,
    resize_mode: ebDomUFSResizeMode = ebDomUFSResizeMode.NORMAL
) -> Tuple[ebFilesystemsState, List[exaMockCommand]]:
    """
    Gets all the exaMockCommand for a expand_domu_fs_using_existing_dev call.

    :param domu_state: A DomU filesystems state.
    :param domu_fs_tree: A DomU filesystem tree.
    :param filesystem: A filesystem to resize.
    :param extra_bytes: Extra bytes to resize.
    :param resize_mode: A resize mode.
    :returns: A tuple containing the updated ebFilesystemsState along with the
        List of exaMockCommand.
    """

    cmds: List[exaMockCommand] = []

    part_devs: List[str] = [pv.name for pv in domu_fs_tree.pvs] if domu_fs_tree.pvs \
        else [domu_fs_tree.filesystem.device]
    for part_dev in part_devs:
        disk_dev, new_cmds = get_disk_for_part_dev_cmds(part_dev)
        cmds += new_cmds
        cmds.append(TEST_ECHO_PATH)
        cmds.append(TEST_PARTED_PATH)
        cmds.append(exaMockCommand(
            f"/bin/echo 'Fix\nFix' | "
                f"/sbin/parted {disk_dev} ---pretend-input-tty print"
        ))

        if domu_fs_tree.lv is None:
            domu_state, resize_cmds = expand_domu_fs_using_mountpoint_cmds(
                domu_state,
                domu_fs_tree,
                filesystem
            )
            return (domu_state, cmds + resize_cmds)

        cmds.append(TEST_PVR_PATH)

        part_num: int = int(''.join(filter(
            lambda c: c in string.digits,
            part_dev[len(disk_dev):]
        )))

        cmds.append(exaMockCommand(
            f"/sbin/parted {disk_dev} resizepart {part_num} 100%"
        ))
        cmds.append(exaMockCommand(
            f"/sbin/pvresize {part_dev}"
        ))

    vg_ix: int = domu_state.fs_layout.vgs.index(domu_fs_tree.vg)
    domu_state.fs_layout.vgs[vg_ix] = ebNodeVGInfo(
        domu_fs_tree.vg.name,
        domu_fs_tree.vg.size_bytes + domu_state.space_for_vgs,
        domu_fs_tree.vg.free_bytes + domu_state.space_for_vgs,
        domu_fs_tree.vg.pe_bytes
    )
    cmds += get_node_fs_layout_cmds(domu_state.fs_layout)

    # TODO: Mock the case where we want to resize the Volume Group only.

    domu_state, resize_cmds = expand_domu_fs_using_free_vg_cmds(
        domu_state,
        domu_fs_tree,
        filesystem,
        extra_bytes,
        resize_mode
    )

    return (domu_state, cmds + resize_cmds)



def expand_domu_filesystem_cmds(
    clu_ctrl: exaBoxCluCtrl,
    domu_states: Dict[str, ebFilesystemsState],
    dom0_name: Optional[str] = None,
    domu_name: Optional[str] = None,
    filesystem: Optional[ebDomUFilesystem] = None,
    extra_bytes: Optional[int] = None,
    check_max_size: bool = True,
    resize_mode: ebDomUFSResizeMode = ebDomUFSResizeMode.NORMAL
) -> Dict[str, List[List[str]]]:
    """
    Gets a dictionary of exaMockCommands that are meant to be executed for a
    whole expand_domu_filesystem routine call.

    :param clu_ctrl: 
    """
    # clu_ctrl: exaBoxCluCtrl = self.mGetClubox()

    filesystems: List[ebDomUFilesystem] = \
        ebDomUFilesystem if clu_ctrl.mIsKVM() \
            else XEN_DOMU_FILESYSTEMS

    if filesystem is not None:
        filesystems = [ filesystem ]

    fs_size_limits: Dict[ebDomUFilesystem, int] = \
        get_max_domu_filesystem_sizes(clu_ctrl)

    vg_size_limits: Dict[str, int] = {
	    'VGExaDb': 2 * GIB
	}

    connections: Dict[str, List[List[exaMockCommand]]] = {}
    # dom0, domu = (self.mGetRegexDom0(), self.mGetRegexVm())

    nodes: List[List[str]] = clu_ctrl.mReturnDom0DomUPair()
    if dom0_name is not None and domu_name is not None:
        nodes = [[dom0_name, domu_name]]

    for dom0, domu in nodes:
        connections[dom0] = []
        connections[domu] = []
        domu_state: ebFilesystemsState = domu_states[domu]

        connections[domu].append(
            get_node_fs_layout_cmds(domu_state.fs_layout)
        )

        for fs in filesystems:

            fs_tree: Optional[ebNodeFSTree] = \
                get_domu_filesystem_tree(domu_state.fs_layout, fs)
            if fs_tree is None:
                continue
            fs_disk_bytes: int = 0
            if fs_tree.lv is None:
                fs_disk, fs_disk_cmds = get_dom0_disk_for_filesystem_cmds(
                    domu_state.disks,
                    domu,
                    fs
                )
                connections[dom0].append(fs_disk_cmds)
                fs_disk_bytes = fs_disk.size_bytes
            fs_bytes: int = fs_tree.inactive_lv.size_bytes \
                if fs in FS_WITH_DUPLICATED_VOLUME and \
                resize_mode == ebDomUFSResizeMode.SND_VOL_ONLY \
	            else fs_tree.lv.size_bytes if fs_tree.lv else fs_disk_bytes

            fs_max_bytes: Optional[int] = fs_size_limits.get(fs)
            fs_extra_bytes: int = extra_bytes
            if fs_extra_bytes is None:
                if fs_max_bytes is None:
                    continue
                if fs in FS_WITH_DUPLICATED_VOLUME and resize_mode in (
                    ebDomUFSResizeMode.NORMAL, ebDomUFSResizeMode.LV_ONLY):
                    fs_max_bytes = max(
                        fs_max_bytes,
                        fs_tree.lv.size_bytes,
                        fs_tree.inactive_lv.size_bytes
                    )
                elif fs_max_bytes <= fs_bytes:
                    continue
                fs_extra_bytes = fs_max_bytes - fs_bytes

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

            if clu_ctrl.mIsKVM() or fs_tree.lv is None:
                if dom0_extra_bytes > 0:
                    domu_state, connection_cmds = resize_disk_image_cmds(
                        domu_state,
                        dom0,
                        domu,
                        fs,
                        dom0_extra_bytes
                    )
                    connections[dom0].append(connection_cmds[dom0])
                    domu_cmds: Optional[List[exaMockCommand]] = \
                        connection_cmds[domu]
                    if domu_cmds is not None:
                        connections[domu].append(domu_cmds)

                domu_state, domu_connection = \
                    expand_domu_fs_using_existing_dev_cmds(
                        domu_state,
                        fs_tree,
                        fs,
                        fs_extra_bytes
                    )
                connections[domu].append(domu_connection)
            else:
                if dom0_extra_bytes <= 0:
                    domu_state, domu_connection = \
                        expand_domu_fs_using_existing_dev_cmds(
                            domu_state,
                            fs_tree,
                            fs,
                            fs_extra_bytes
                        )
                    connections[domu].append(domu_connection)
                else:
                    disk_info: ebDiskImageInfo = ebDiskImageInfo(
                        f"/EXAVMIMAGES/GuestImages/{domu}/fs_resize_\S*.img",
                        dom0_extra_bytes + fs_tree.vg.pe_bytes,
                        'raw',
                        'gpt'
                    )
                    domu_state, disk_create_cmds = \
                        create_new_lvm_disk_image_cmds(
                            domu_state,
                            disk_info
                        )
                    next_disk_dev, disk_attach_cmds = \
                        attach_dom0_disk_image_cmds(
                            domu_state,
                            domu,
                            disk_info.path
                        )

                    domu_state, domu_resize_cmds = \
                        expand_domu_fs_using_new_dev_cmds(
                            domu_state,
                            fs_tree,
                            fs,
                            next_disk_dev,
                            resize_mode
                        )

                    connections[dom0].append(
                        disk_create_cmds + disk_attach_cmds
                    )
                    connections[domu].append(domu_resize_cmds)

    return connections



def expand_domu_vg_cmds(
    clu_ctrl: exaBoxCluCtrl,
    domu_states: Dict[str, ebFilesystemsState],
    dom0_name: Optional[str] = None,
    domu_name: Optional[str] = None,
    vg_name: Optional[str] = None,
    extra_bytes: Optional[int] = None,
    check_max_size: bool = True
):
    """
    Gets a dictionary of exaMockCommands that are meant to be executed for a
    whole expand_domu_vg routine call.
    """

    connections: Dict[str, List[List[exaMockCommand]]] = {}

    nodes: List[List[str]] = clu_ctrl.mReturnDom0DomUPair()
    if dom0_name is not None and domu_name is not None:
        nodes = [[dom0_name, domu_name]]

    vg_size_limits: Dict[str, int] = {} if clu_ctrl.mIsKVM() else {
        'VGExaDb': 2 * GIB
    }

    for dom0, domu in nodes:
        connections[dom0] = []
        connections[domu] = []
        domu_state: ebFilesystemsState = domu_states[domu]

        connections[domu].append(
            get_node_fs_layout_cmds(domu_state.fs_layout)
        )

        vgs: List[ebNodeVGInfo] = domu_state.fs_layout.vgs

        if vg_name is not None:
            vgs = [ vg for vg in vgs if vg.name == vg_name ]

        for vg in vgs:

            vg_max_free_bytes: Optional[int] = vg_size_limits.get(vg.name)
            vg_extra_bytes: Optional[int] = extra_bytes
            if vg_extra_bytes is None:
                if vg_max_free_bytes is None or \
                    vg_max_free_bytes <= vg.free_bytes:
                    continue

                vg_extra_bytes = vg_max_free_bytes - vg.free_bytes

            lv_info, *_ = [
                lv for lv in domu_state.fs_layout.lvs
                if lv.vg_name == vg.name
            ]
            fs_info, *_ = [
                fs for fs in domu_state.fs_layout.filesystems
                if fs.device == lv_info.dm_path
            ]
            fs: ebDomUFilesystem = ebDomUFilesystem(fs_info.mountpoint)

            resize_connections = expand_domu_filesystem_cmds(
                clu_ctrl,
                { domu: domu_state },
                dom0,
                domu,
                fs,
                vg_extra_bytes,
                False,
                ebDomUFSResizeMode.VG_ONLY
            )
            connections[dom0] += resize_connections[dom0]
            connections[domu] += resize_connections[domu]

    return connections



###################
### TESTS CLASS ###
###################


class ebTestFomUFilesystems(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestFomUFilesystems, self).setUpClass(True, True)

    def setUp(self):
        self.mGetClubox()._exaBoxCluCtrl__ociexacc = False
        self.mGetClubox()._exaBoxCluCtrl__kvm_enabled = True
        get_gcontext().mSetConfigOption('disk_u02_size', '775G')

    def resize_all_fs(
        self,
        is_kvm: bool,
        domu_states: Dict[str, ebFilesystemsState]
    ):
        clu_ctrl: exaBoxCluCtrl = self.mGetClubox()
        clu_ctrl._exaBoxCluCtrl__kvm_enabled = is_kvm

        cmds_fs: Dict[str, List[List[str]]] = expand_domu_filesystem_cmds(
            clu_ctrl,
            domu_states
        )
        cmds_vg: Dict[str, List[List[str]]] = expand_domu_vg_cmds(
            clu_ctrl,
            domu_states
        )
        cmds: Dict[str, List[List[str]]] = {
            hostname: cmds_fs.get(hostname, []) + cmds_vg.get(hostname, [])
            for hostname in set(cmds_fs.keys()) | set(cmds_vg.keys())
        }

        self.mPrepareMockCommands(cmds)
        expand_domu_filesystem(clu_ctrl)
        expand_domu_vg(clu_ctrl)


    def resize_all_fs_kvm(self, remove_filesystems: Set[str]=set()):

        domu_states: Dict[str, ebFilesystemsState] = {
        domu: ebFilesystemsState(
        ebNodeFSLayout(
        [
            fs for fs in [
            ebNodeFilesystemInfo(
                '/',
                '/dev/mapper/vg-root1',
                'xfs',
                15 * GIB - 10 * MIB,
                15 * GIB - 10 * MIB,
                False
            ),
            ebNodeFilesystemInfo(
                '/u01',
                '/dev/mapper/vgu01-u01',
                'xfs',
                20 * GIB - 10 * MIB,
                20 * GIB - 10 * MIB,
                False
            ),
            ebNodeFilesystemInfo(
                '/u02',
                '/dev/mapper/vgu02-u02',
                'ext4',
                773 * GIB - 10 * MIB,
                773 * GIB - 10 * MIB,
                False
            ),
            ebNodeFilesystemInfo(
                '/u01/app/grid/19.0.0.0',
                '/dev/mapper/vggrid-grid',
                'xfs',
                50 * GIB - 10 * MIB,
                50 * GIB - 10 * MIB,
                False
            ),
            ebNodeFilesystemInfo(
                '/home',
                '/dev/mapper/vg-home',
                'xfs',
                4 * GIB - 10 * MIB,
                4 * GIB - 10 * MIB,
                False
            ),
            ebNodeFilesystemInfo(
                '/tmp',
                '/dev/mapper/vg-tmp',
                'xfs',
                3 * GIB - 10 * MIB,
                3 * GIB - 10 * MIB,
                False
            ),
            ebNodeFilesystemInfo(
                '/var',
                '/dev/mapper/vg-var1',
                'xfs',
                2 * GIB - 10 * MIB,
                2 * GIB - 10 * MIB,
                False
            ),
            ebNodeFilesystemInfo(
                '/var/log',
                '/dev/mapper/vg-varlog',
                'xfs',
                18 * GIB - 10 * MIB,
                18 * GIB - 10 * MIB,
                False
            ),
            ebNodeFilesystemInfo(
                '/var/log/audit',
                '/dev/mapper/vg-varlogaudit',
                'xfs',
                1 * GIB - 10 * MIB,
                1 * GIB - 10 * MIB,
                False
            ),
            ebNodeFilesystemInfo(
                '/crashfiles',
                '/dev/mapper/vg-crashfiles',
                'xfs',
                20 * GIB - 10 * MIB,
                20 * GIB - 10 * MIB,
                False
            )
            ] if fs.mountpoint not in remove_filesystems
        ],
        [
            ebNodeLVInfo('root1', '/dev/mapper/vg-root1', 'vg', 15*GIB),
            ebNodeLVInfo('root2', '/dev/mapper/vg-root2', 'vg', 15*GIB),
            ebNodeLVInfo('u01', '/dev/mapper/vgu01-u01', 'vgu01', 20*GIB),
            ebNodeLVInfo('u02', '/dev/mapper/vgu02-u02', 'vg', 773*GIB),
            ebNodeLVInfo('grid', '/dev/mapper/vggrid-grid', 'vggrid', 50*GIB),
            ebNodeLVInfo('home', '/dev/mapper/vg-home', 'vg', 4*GIB),
            ebNodeLVInfo('var1', '/dev/mapper/vg-var1', 'vg', 2*GIB),
            ebNodeLVInfo('var2', '/dev/mapper/vg-var2', 'vg', 2*GIB),
            ebNodeLVInfo('tmp', '/dev/mapper/vg-tmp', 'vg', 3*GIB),
            ebNodeLVInfo('varlog', '/dev/mapper/vg-varlog', 'vg', 18*GIB),
            ebNodeLVInfo(
                'varlogaudit',
                '/dev/mapper/vg-varlogaudit',
                'vg',
                1 * GIB
            ),
            ebNodeLVInfo(
                'crashfiles',
                '/dev/mapper/vg-crashfiles',
                'vg',
                20 * GIB
            )
        ],
        [
            ebNodeVGInfo('vg', 106032*MIB, 2352*MIB, 4*MIB),
            ebNodeVGInfo('vgu01', 22*GIB - 4*MIB, 2*GIB - 4*MIB, 4*MIB),
            ebNodeVGInfo('vgu02', 775*GIB - 4*MIB, 2*GIB - 4*MIB, 4*MIB),
            ebNodeVGInfo('vggrid', 52*GIB - 4*MIB, 2*GIB - 4*MIB, 4*MIB)
        ],
        [
            ebNodePVInfo('/dev/sda3', 'vg', 106032 * MIB),
            ebNodePVInfo('/dev/sdb1', 'vgu02', 775 * GIB - 4 * MIB),
            ebNodePVInfo('/dev/sdc1', 'vgu01', 22 * GIB - 4 * MIB),
            ebNodePVInfo('/dev/sdd1', 'vggrid', 52 * GIB - 4 * MIB)
        ]
        ),
        [
            ebDiskImageInfo(
                f"/EXAVMIMAGES/GuestImages/{domu}/System.img",
                109366477 * KIB,
                'raw',
                'gpt'
            ),
            ebDiskImageInfo(
                f"/EXAVMIMAGES/GuestImages/{domu}/u01.img",
                22 * GIB,
                'raw',
                'gpt'
            ),
            ebDiskImageInfo(
                f"/EXAVMIMAGES/GuestImages/{domu}/u02_extra.img",
                775 * GIB,
                'raw',
                'msdos'
            ),
            ebDiskImageInfo(
                f"/EXAVMIMAGES/GuestImages/{domu}/grid19.img",
                52 * GIB,
                'raw',
                'gpt'
            )
        ],
        0,
        True
        )
        for _, domu in self.mGetClubox().mReturnDom0DomUPair()
        }

        self.resize_all_fs(
            True,
            domu_states
        )



    def test_resize_all_fs_kvm(self):
        self.resize_all_fs_kvm()



    def test_resize_all_fs_kvm_with_missing_fs(self):
        self.resize_all_fs_kvm({'/crashfiles'})
        self.resize_all_fs_kvm({'/u01/app/grid/19.0.0.0'})



    def test_resize_all_fs_xen(self):

        domu_states: Dict[str, ebFilesystemsState] = {
            domu: ebFilesystemsState(
                ebNodeFSLayout(
                [
                    ebNodeFilesystemInfo(
                        '/',
                        '/dev/mapper/vg-root1',
                        'xfs',
                        24 * GIB - 10 * MIB,
                        24 * GIB - 10 * MIB,
                        False
                    ),
                    ebNodeFilesystemInfo(
                        '/u01',
                        '/dev/mapper/vg-u01',
                        'xfs',
                        20 * GIB - 10 * MIB,
                        20 * GIB - 10 * MIB,
                        False
                    ),
                    ebNodeFilesystemInfo(
                        '/u02',
                        '/dev/xvdd',
                        'ext4',
                        61796348 * KIB,
                        61796348 * KIB,
                        False
                    ),
                    ebNodeFilesystemInfo(
                        '/u01/app/grid/19.0.0.0',
                        '/dev/xvdb',
                        'ext4',
                        50 * GIB,
                        50 * GIB,
                        False
                    )
                ],
                [
                    ebNodeLVInfo(
                        'root1',
                        '/dev/mapper/vg-root1',
                        'VGExaDb',
                        15 * GIB
                    ),
                    ebNodeLVInfo(
                        'root2',
                        '/dev/mapper/vg-root2',
                        'VGExaDb',
                        15 * GIB
                    ),
                    ebNodeLVInfo(
                        'u01',
                        '/dev/mapper/vg-u01',
                        'VGExaDb',
                        20 * GIB
                    )
                ],
                [
                    ebNodeVGInfo('VGExaDb', 88568*MIB, 1272*MIB, 4*MIB)
                ],
                [
                    ebNodePVInfo('/dev/xvda3', 'VGExaDb', 24*GIB + 508*MIB),
                    ebNodePVInfo('/dev/xvdc1', 'VGExaDb', 62*GIB - 4*MIB)
                ]
                ),
                [
                    ebDiskImageInfo(
                        f"/EXAVMIMAGES/GuestImages/{domu}/System.img",
                        25 * GIB,
                        'raw',
                        'gpt'
                    ),
                    ebDiskImageInfo(
                        f"/EXAVMIMAGES/GuestImages/{domu}/pv1_vgexadb.img",
                        62 * GIB,
                        'raw',
                        'gpt'
                    ),
                    ebDiskImageInfo(
                        f"/EXAVMIMAGES/GuestImages/{domu}/u02_extra.img",
                        60 * GIB,
                        'raw',
                        'msdos'
                    ),
                    ebDiskImageInfo(
                        f"/EXAVMIMAGES/GuestImages/{domu}/grid18.img",
                        50 * GIB,
                        'raw',
                        'gpt'
                    )
                ],
                0,
                False
            )
            for _, domu in self.mGetClubox().mReturnDom0DomUPair()
        }

        self.resize_all_fs(
            False,
            domu_states
        )



    def test_resize_non_lvm_xen(self):

        domu_states: Dict[str, ebFilesystemsState] = {
        domu: ebFilesystemsState(
            ebNodeFSLayout(
                [
                    ebNodeFilesystemInfo(
                        '/u02',
                        '/dev/xvdd',
                        'ext4',
                        61796348 * KIB,
                        61796348 * KIB,
                        False
                    )
                ],
                [],
                [],
                []
            ),
            [
                ebDiskImageInfo(
                    f"/EXAVMIMAGES/GuestImages/{domu}/u02_extra.img",
                    60 * GIB,
                    'raw',
                    'msdos'
                )
            ],
            0,
            False
        )
        for _, domu in self.mGetClubox().mReturnDom0DomUPair()
        }

        clu_ctrl: exaBoxCluCtrl = self.mGetClubox()
        clu_ctrl._exaBoxCluCtrl__kvm_enabled = False

        cmds: Dict[str, List[List[str]]] = expand_domu_filesystem_cmds(
            clu_ctrl,
            domu_states,
            filesystem = ebDomUFilesystem.U02,
            extra_bytes = 5 * GIB,
            check_max_size = False
        )

        self.mPrepareMockCommands(cmds)
    
        expand_domu_filesystem(
            clu_ctrl,
            filesystem = ebDomUFilesystem.U02,
            extra_bytes = 5 * GIB,
            check_max_size = False,
            run_in_parallel=True
        )


    def test_shutdown_domu_timeout(self):

        (dom0_name, domu_name), *_ = self.mGetClubox().mReturnDom0DomUPair()
        domu_state: ebFilesystemsState = ebFilesystemsState(None, [], 0, True)
        cmds: Dict[str, List[List[str]]] = {
            dom0_name: [ shutdown_domu_cmds(domu_state, domu_name, 2) ]
        }

        self.mPrepareMockCommands(cmds)
        with connect_to_host(dom0_name, get_gcontext()) as node:
            self.assertRaises(ExacloudRuntimeError, shutdown_domu, node, domu_name, 10)

    def test_shutdown_domu_incorrectvm(self):

        (dom0_name, domu_name), *_ = self.mGetClubox().mReturnDom0DomUPair()
        domu_state: ebFilesystemsState = ebFilesystemsState(None, [], 0, True)
        cmds: Dict[str, List[List[str]]] = {
            dom0_name: [ shutdown_domu_cmds(domu_state, domu_name, 2) ]
        }
        
        domu_name = domu_name[3:] #domu name needing shutdown is a subset of another vm name
        self.mPrepareMockCommands(cmds)
        with connect_to_host(dom0_name, get_gcontext()) as node:
            shutdown_domu(node, domu_name)

    def test_shutdown_start_domu(self):

        (dom0_name, domu_name), *_ = self.mGetClubox().mReturnDom0DomUPair()
        domu_state: ebFilesystemsState = ebFilesystemsState(None, [], 0, True)
        cmds: Dict[str, List[List[str]]] = {
            dom0_name: [ shutdown_domu_cmds(domu_state, domu_name, 2) ]
        }
        
        self.mPrepareMockCommands(cmds)
        with connect_to_host(dom0_name, get_gcontext()) as node:
            shutdown_domu(node, domu_name)

        cmds: Dict[str, List[List[str]]] = {
            dom0_name: [ start_domu_cmds(domu_state, domu_name) ]
        }

        self.mPrepareMockCommands(cmds)
        with connect_to_host(dom0_name, get_gcontext()) as node:
            start_domu(node, domu_name) 

    @patch('exabox.ovm.cludomufilesystems.node_cmd_abs_path_check')
    @patch('exabox.ovm.cludomufilesystems.node_exec_cmd_check')
    def test_get_edvdisk_path_from_domblklist_found(self, mock_node_exec_cmd_check, mock_node_cmd_abs_path_check):
        # Mock the node_cmd_abs_path_check to return 'virsh'
        mock_node_cmd_abs_path_check.return_value = 'virsh'

        # Mock the node_exec_cmd_check to return a successful output
        mock_node_exec_cmd_check.return_value = (0, '/dev/sda1  /EXAVMIMAGES/GuestImages/test_domU/u01.img\n', '')

        # Test the function
        dom0_node = MagicMock()
        domu_name = 'test_domU'
        filesystem = 'u01'
        result = get_edvdisk_path_from_domblklist(dom0_node, domu_name, filesystem)
        ebLogInfo(f"output result is:{result}")

        # Assert the result
        self.assertEqual(result, '/EXAVMIMAGES/GuestImages/test_domU/u01.img')

        # Assert the mock calls
        mock_node_cmd_abs_path_check.assert_called_once_with(dom0_node, 'virsh')
        mock_node_exec_cmd_check.assert_called_once()

    @patch('exabox.ovm.cludomufilesystems.node_cmd_abs_path_check')
    @patch('exabox.ovm.cludomufilesystems.node_exec_cmd_check')
    def test_get_edvdisk_path_from_domblklist_not_found(self, mock_node_exec_cmd_check, mock_node_cmd_abs_path_check):
        # Mock the node_cmd_abs_path_check to return 'virsh'
        mock_node_cmd_abs_path_check.return_value = 'virsh'

        # Mock the node_exec_cmd_check to return an empty output
        mock_node_exec_cmd_check.return_value = (0, '', '')

        # Test the function
        dom0_node = MagicMock()
        domu_name = 'test_domU'
        filesystem = 'u01'
        result = get_edvdisk_path_from_domblklist(dom0_node, domu_name, filesystem)

        # Assert the result
        self.assertIsNone(result)

        # Assert the mock calls
        mock_node_cmd_abs_path_check.assert_called_once_with(dom0_node, 'virsh')
        mock_node_exec_cmd_check.assert_called_once()

    @patch('exabox.ovm.cludomufilesystems.node_cmd_abs_path_check')
    @patch('exabox.ovm.cludomufilesystems.node_exec_cmd_check')
    def test_get_edvdisk_path_from_domblklist_exception(self, mock_node_exec_cmd_check, mock_node_cmd_abs_path_check):
        # Mock the node_cmd_abs_path_check to return 'virsh'
        mock_node_cmd_abs_path_check.return_value = 'virsh'

        # Mock the node_exec_cmd_check to raise an exception
        mock_node_exec_cmd_check.side_effect = Exception('Test exception')

        # Test the function
        dom0_node = MagicMock()
        domu_name = 'test_domU'
        filesystem = 'u01'

        # Assert the exception is raised
        with self.assertRaises(Exception):
            get_edvdisk_path_from_domblklist(dom0_node, domu_name, filesystem)

        # Assert the mock calls
        mock_node_cmd_abs_path_check.assert_called_once_with(dom0_node, 'virsh')
        mock_node_exec_cmd_check.assert_called_once()

    @patch('exabox.ovm.cludomufilesystems.get_edvdisk_path_from_domblklist')
    @patch('exabox.ovm.cludomufilesystems.node_cmd_abs_path_check')
    @patch('exabox.ovm.cludomufilesystems.node_exec_cmd_check')
    @patch('exabox.ovm.cludomufilesystems.get_disk_partition_table')
    def test_get_dom0_edvdisk_for_filesystem_u01(self, mock_get_disk_partition_table, mock_node_exec_cmd_check, mock_node_cmd_abs_path_check, mock_get_edvdisk_path_from_domblklist):
        # Mock the get_edvdisk_path_from_domblklist to return a disk path
        mock_get_edvdisk_path_from_domblklist.return_value = '/EXAVMIMAGES/GuestImages/test_domU/u01.img'

        # Mock the node_cmd_abs_path_check to return 'qemu-img'
        mock_node_cmd_abs_path_check.return_value = 'qemu-img'

        # Mock the node_exec_cmd_check to return a successful output
        mock_node_exec_cmd_check.return_value = (0, '{"virtual-size": 1073741824, "format": "raw"}', '')

        # Mock the get_disk_partition_table to return a partition table
        mock_get_disk_partition_table.return_value = 'gpt'

        # Test the function
        dom0_node = MagicMock()
        domu_name = 'test_domU'
        filesystem = ebDomUFilesystem.U01
        result = get_dom0_edvdisk_for_filesystem(dom0_node, domu_name, filesystem)

        # Assert the result
        self.assertIsInstance(result, ebDiskImageInfo)
        self.assertEqual(result.path, '/EXAVMIMAGES/GuestImages/test_domU/u01.img')
        self.assertEqual(result.size_bytes, 1073741824)
        self.assertEqual(result.file_format, 'raw')
        self.assertEqual(result.partition_table, 'gpt')

        # Assert the mock calls
        mock_get_edvdisk_path_from_domblklist.assert_called_once_with(dom0_node, domu_name, 'u01')
        mock_node_cmd_abs_path_check.assert_called_once_with(dom0_node, 'qemu-img')
        mock_node_exec_cmd_check.assert_called_once()
        mock_get_disk_partition_table.assert_called_once_with(dom0_node, '/EXAVMIMAGES/GuestImages/test_domU/u01.img')

    @patch('exabox.ovm.cludomufilesystems.get_edvdisk_path_from_domblklist')
    def test_get_dom0_edvdisk_for_filesystem_not_found(self, mock_get_edvdisk_path_from_domblklist):
        # Mock the get_edvdisk_path_from_domblklist to return None
        mock_get_edvdisk_path_from_domblklist.return_value = None

        # Test the function
        dom0_node = MagicMock()
        domu_name = 'test_domU'
        filesystem = ebDomUFilesystem.U01

        # Assert the exception is raised
        with self.assertRaises(Exception):
            get_dom0_edvdisk_for_filesystem(dom0_node, domu_name, filesystem)

        # Assert the mock calls
        mock_get_edvdisk_path_from_domblklist.assert_called_once_with(dom0_node, domu_name, 'u01')


if __name__ == '__main__':
    unittest.main() 
