#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/ovm/cluexascale.py /main/144 2025/12/02 17:57:52 ririgoye Exp $
#
# cluexascale.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      cluexascale.py - ExaCloud utilities to set up/configure ExaScale envs.
#
#    DESCRIPTION
#      this module includes subroutines to take care of the XML patching and
#      and special configuration required for ExaScale/ExaCompute envs.
#
#    NOTES
#      None.
#
#    MODIFIED   (MM/DD/YY)
#    ririgoye    11/26/25 - Bug 38636333 - EXACLOUD PYTHON:ADD INSTANTCLIENT TO
#                           LD_LIBRARY_PATH
#    prsshukl    11/19/25 - Bug 38037088 - BASE DB -> MOVE THE DO/UNDO STEPS
#                           FOR BASEDB TO A NEW FILE IN CSSTEP , REMOVE CODE
#                           THAT IS UNNECESSARY FOR BASEDB
#    gsundara    11/15/25 - Bug 38656874 - EXADB-XS:VM MOVE : UMOUNT FAILS WITH
#                           TARGET IS BUSY DURING PREPARE VM MOVE and DELETES
#                           CONSOLE DIRS
#    scoral      10/07/25 - Enh 38452359 - Support up to 199 VMs.
#    scoral      09/26/25 - Bug 38474589 - Update Dom0&DomU pairs after cloning
#                           the source Dom0 and before placing the Dom0 keys in
#                           OEDA work directory in mExecuteVmMoveOEDA.
#    siyarlag    09/25/25 - 38471201: live migration aStrict=False for umount
#    scoral      09/19/25 - Bug 38448719 - Avoid failing during removing backup
#                           bridge XMLs of VMs during VM move.
#    scoral      08/29/25 - Bug 38319226 - Re-added the workaround that updates
#                           automatically vmeth2xx.xml during VM move but this
#                           time only during VM move force.
#    jesandov    08/26/25 - Bug 38337015 - Add cleanup of stale bridges
#    prsshukl    08/20/25 - Enh 38180284 - EXADB-XS -> VALIDATE_VOLUME TO WORK
#                           AT THE HOST/DOM0 LEVEL AND VALIDATE VOLUMES API TO
#                           SEND THE JSON JOB REPORT TO ECRA
#    prsshukl    07/31/25 - Bug 38257488 - EXADB-XS: 19C CLUSTER, FORCED VM
#                           MIGRATION FAILED, OEDA-2002: INVALID INPUT VALUE:
#                           TGTHOST IS REQUIRED
#    prsshukl    07/23/25 - Enh 38227111 - EXADB-XS -> BASE DB -> ATTACH SW
#                           VOLUME AS PART OF PROVISIONING
#    prsshukl    07/11/25 - Bug 38176800 -> For Validate Volume skip gcv vol in
#                           xml and u02 vol in vm
#    jesandov    07/07/25 - 37783445: Live migration prechecks
#    naps        06/27/25 - Bug 38042220 - sanity check for clone operation.
#    naps        06/27/25 - Bug 38116390 - Copy weblogic cert for R1 with
#                           basedb launches.
#    dekuckre    06/26/25 - 37842347: support vm move for basedb
#    dekuckre    06/24/25 - 38103998: Ignore stale GCV precheck on target dom0
#    siyarlag    06/19/25 - Bug/38049854: use symlink in udev rule
#    dekuckre    06/18/25 - 37956937: Acquire locks before volume attach/resize
#    siyarlag    06/09/25 - Bug/38048369: use ID_SCSI_SERIAL in udev rules
#    scoral      06/04/25 - Bug 38034833 - Removed the workaround that
#                           re-attaches the /u02 EDV during VM move because
#                           it breaks if a /u02 EDV snapshot was created and
#                           because it is not needed anymore because the
#                           original issue has been fixed.
#    scoral      05/23/25 - Bug 37969030 - Removed the workaround that updates
#                           automatically vmeth2xx.xml during VM move.
#    prsshukl    05/16/25 - Bug 37878649 - EXADBXS 19C ADDNODE PRVF-9992 GROUP
#                           OF DEVICE DID NOT MATCH THE EXPECTED GROUP
#    dekuckre    05/15/25 - 37947889: update uuid for u02 snapshots.
#    scoral      05/13/25 - Bug 37945590 - Call mRestoreOEDASSHKeys in
#                           mVolAttach.
#    scoral      05/12/25 - Bug 37939535 - Make sure mAddRoceSshEntry is
#                           executed in the source host only if available.
#    jesandov    05/05/25 - Bug 37621577 - Add reconfigure of stre0 and stre1
#    dekuckre    04/28/25 - 37873369: Use new oedacli cmd to attach-detach volumes
#    prsshukl    04/23/25 - Bug 37857887 - REMOVE CELLINIT.ORA FILE FOR EXADBXS
#                           (BLOCK STORAGE) AND UPDATE ATTACH_DOM0_DISK_IMAGE
#                           METHOD CALL
#    dekuckre    04/23/25 - 37855242: Use virsh attach-disk to attach the db volumes
#    prsshukl    04/21/25 - Enh 37747083 - EXADB-XS 19C -> VMMOVE POSTCHECK
#                           VERIFICATION CHANGES FOR 19C DB SUPPORT IN EXADB-XS
#    prsshukl    04/17/25 - Bug 37841906 - EXADB-XS 19C: EXACLOUD - CREATE
#                           SERVICE FAILING WITH KEYERROR: 'GUESTDEVICENAME'
#                           ERROR AND UPDATE 66-dbvolume.rules file name
#    prsshukl    04/16/25 - Enh 37827765 - EXADB-XS 19C : ADDITIONAL CHANGES IN
#                           CS AND ADD COMPUTE WORKFLOW -> REMOVAL OF INTERFACE
#                           STREX / CLREX AND CREATE USER STEP
#    prsshukl    04/10/25 - Enh 37807155 - EXADB-XS 19C :CS AND ADD COMPUTE
#                           ENDPOINT UPDATE -> USE OEDACLI CMD TO ATTACH
#                           DBVOLUME VOLUMES TO GUEST VMS
#    dekuckre    04/09/25 - 37789879: Use oedacli cmd to attach-detach-resize db vol
#    prsshukl    04/03/25 - Enh 37740750 - EXADB-XS 19C :CS AND ADD COMPUTE
#                           ENDPOINT UPDATE-> ATTACH DBVOLUME VOLUMES TO GUEST
#                           VMS
#    dekuckre    03/27/25 - 37748575: Add support for live migration.
#    scoral      03/27/25 - 37758937: Make sure client and backup bridges are
#                           created after VM move and before starting the VM.
#                           37710413: Make sure /u02 EDV is attached after
#                           VM move and before starting the VM.
#    dekuckre    03/27/25 - 37740767: Add support for vol attach, detach, repair
#    scoral      03/18/25 - 37665235: Validate the VM XMLs are in the GCV EDV
#                           during move pre-checks.
#    jesandov    03/11/25 - 37675915: Cleanup residual files and add stre0/1 ip in ssh config
#    dekuckre    02/12/25 - 37579201: Fix mGetLVDev
#    dekuckre    02/05/25 - 37549471: Remove VM serial console containers from src dom0.
#    scoral      01/27/24 - 37524984: Make sure we remove any stale bridges and
#                           stale EDVs from target Dom0 before VM move.
#    scoral      12/18/24 - 37409614: Open host access control for RoCE network
#                           on source Dom0 during VM move.
#    scoral      11/25/24 - 37312115: Update Dom0 private network section in
#                           cluster XML with correct stre0/1 interfaces
#                           information during VM move.
#                           37312183: Open host access control for RoCE network
#                           on target Dom0 during VM move.
#    scoral      11/25/24 - 37236176: Read ECRA CIDR blocks from VM move
#                           payload.
#    dekuckre    10/22/24 - Use gExaDbXSError
#    dekuckre    10/16/24 - 37176952: Use variable name for VG for u02 snapshot
#    dekuckre    10/07/24 - 36644925: Updated precheck for exacompute
#    dekuckre    09/18/24 - 37010952: Support mount/unmount of snapshots of u02.
#    naps        09/09/24 - Bug 37030085 - Acquire dom0 lock during bridge
#                           removal.
#    pbellary    08/26/24 - Enh 36984591 - EXASCALE EXACLOUD - ADD STORAGESIZE AND STOARGETYPE FOR XML GENERATION IN EXACS
#    dekuckre    08/14/24 - 36932575: skip vm start for zero core
#    jesandov    07/23/24 - Bug 36869902 - Add support of delete node in elastic info ExaDB-XS
#    jesandov    07/19/24 - 36862472: Configure Bond Monitor after volume mount
#    dekuckre    07/12/24 - 36799943: Log Vm move operation in dom0 file
#    dekuckre    07/08/24 - 36695533: Acquire locks before checking list of stale VMs
#    dekuckre    07/02/24 - 36790970: Create the GuestImages/VM dir in dom0 
#    scoral      06/21/24 - 36741009: Clean stale resources of source DomU
#                           if available at the end of VM move.
#    scoral      06/20/24 - 36740875: Copy bondmonitor config files from VM
#                           files under GCV EDV.
#    scoral      06/07/24 - 36315105: Detect VLAN tag for each DomU.
#    rajsag      06/03/24 - Exascale support utility files
#    scoral      05/31/24 - 36681522: Avoid OEDA to validate prematurely the
#                           NAT VLAN in the target hosy during prepare move.
#    scoral      05/29/24 - 36670840: Fixed typo in VM move pre-checks.
#                           Added a check for bonding setup during VM move
#                           pre-checks.
#                           Make sure client & backup bridges are up after
#                           VM move.
#    dekuckre    05/27/24 - XbranchMerge dekuckre_bug-36663068 from
#                           st_ecs_23.4.1.2.5
#    naps        05/24/24 - Bug 36644852 - exadbxs dom0 roce config support.
#    dekuckre    05/23/24 - 36644875: Add precheck for ExaDB-XS
#    dekuckre    05/22/24 - 36644786: Acquire locks around move
#    dekuckre    05/17/24 - 36627797: use src dom0 for undo of vm move cmd
#    jesandov    05/09/24 - 36569682: Add cleanup function for vm_move
#    jesandov    05/13/24 - 36612175: Remove code that early remove the oedacli
#                           folder
#    jesandov    05/09/24 - 36569655: Undo of Move Prepare 
#    jesandov    05/09/24 - 36484384: Add lock in vm_move and move prepare
#    pbellary    05/07/24 - 36546125 - EXADB-XS: EXASCALE : STALE EDV VOLUMES UP 
#                           ON FORCE DETACHMENT FROM A HOST
#    scoral      05/03/24 - 36554412: Implement offlineforce in VM move.
#    jesandov    04/30/24 - 36535335: Change ip in clone dom0
#    scoral      04/29/24 - 36535498: Enhance mRemoveVMmount to try to remove
#                           stale EDVs.
#                           Enhance mPostVMMoveSteps to detect any stale EDVs
#                           in source host after move.
#    scoral      04/25/24 - 36555122: Fix type error in VM move sanity checks.
#    jesandov    04/22/24 - 36535335: Update natips
#    scoral      04/14/24 - 36283110: Enhance VM move prechecks for OEDA
#                           VM move.
#    jesandov    04/04/24 - 36482990 - Optimization of oeda properties
#    dekuckre    04/03/24 - 36503657: Add mRemoveVolume
#    jesandov    04/02/24 - 36457353: Add validation to ignore action and
#                           subcommand tags in XML on clone guest for vm_move
#    scoral      03/26/24 - 36405934: Implement an undo mechanism for VM move
#    dekuckre    03/20/24 - 35286033: Add mMountVolume and mUnmountVolume
#    dekuckre    03/07/24 - 36339845: remove src dom0 from xml as part of move cmd
#    scoral      02/23/24 - 36324828: Copy VM maker XML from GuestImages to
#                           /EXAVMIMAGES/conf as part of mPostVMMoveSteps.
#    jesandov    02/22/24 - 36326706: Move logic of migrate ssh key in vm_move
#    scoral      02/16/24 - 36309292: Moved KMS key renaming to
#                           mPostVMMoveSteps.
#                           Fixed NFTables migration.
#    jesandov    02/12/24 - 36283172: Add validation for volumes in payload
#    scoral      02/06/24 - 36268588: Implemented update_guest_vm_maker_xml_nat
#                           during mPrepareVmMoveOEDA as well.
#                           Moved bonding configuration migration to
#                           mPrepareVmMoveOEDA due to NAT migration.
#    jesandov    01/25/24 - 36207260: Add function to read/write sysctl
#                           parameters
#    scoral      01/22/24 - 36197938: Implemented add_kvm_guest_nat_routing
#                           during mPostVMMoveSteps and 
#                           update_guest_vm_maker_xml_nat during
#                           mPerformVmMoveOEDA.
#    scoral      05/01/23 - 36160405: Enhance mConfigureHugePage to parse
#                           Add Compute payload also.
#    jesandov    10/30/23 - 35935420: Update lookup of nat hostname in exascale
#    jesandov    10/26/23 - 35950036: Add support of Add Node in ExaScale
#    gparada     10/10/23 - 35891714 VMMove shouldn't check img file if EDV
#    jesandov    10/04/23 - 35875442: Add new steps for vm_move
#    jesandov    09/01/23 - Bug  35742791: OEDA Properties for ExaScale
#    gparada     07/28/23 - 35630484 Remove VmMoveSanityChecks on EDV
#    jesandov    07/21/23 - 35539443: Integration of VM MOVE with OEDA API
#    jesandov    06/13/23 - 35480217: Add validation for EDV Volumen
#                           information from ECRA payload
#    scoral      06/05/23 - 35435421: Fixed typos in EDV volumes names.
#                           Added NFTables support for VM move.
#    jesandov    05/26/23 - 35426500: Change mGetEntryClass() by mBuildExaKmsEntry()
#    jesandov    05/17/23 - 35395484: Add support of EDV commands from payload
#                           values
#    scoral      03/21/23 - Enh 34734317: Implemented mPerformVmMovesanityChecks
#    scoral      10/26/22 - Enh 34529500: Added bonding and iptables setup for
#                           VM move.
#    scoral      10/14/22 - Enh 34639458: Implemented a VM move API that is
#                           independent from OEDA.
#    ffrrodri    09/21/22 - Enh 34514529: Added OEDA cli commands to support
#                           EDV volumes
#    scoral      01/11/22 - Creation
#

import re
import os
import itertools
import math
import json
import shlex
import socket
import subprocess
import time
from ipaddress import IPv4Network
from typing import List, Sequence, Set
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.globalcache.GlobalCacheFactory import GlobalCacheFactory
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace, ebLogJson
from exabox.ovm.clubonding import get_bond_monitor_installed, REMOTE_MONITOR_CONFIG_FILE_FMT, REMOTE_MONITOR_CONFIG_VM_FILE_FMT, REMOTE_VM_CUSTOM_VIP_FILE_FMT, REMOTE_VM_CUSTOM_VIP_VM_FILE_FMT, restart_bond_monitor, add_remove_entry_monitor_admin_conf
from exabox.ovm.cludomufilesystems import attach_dom0_disk_image, shutdown_domu, get_node_filesystems, start_domu
from exabox.ovm.cluiptablesroce import ebIpTablesRoCE
from exabox.ovm.clujumboframes import cluctrlGetDom0Bridges
from exabox.ovm.clunetupdate import add_kvm_guest_nat_routing, get_ifcfg_contents, get_kvm_guest_bridges, get_node_bridges, update_guest_vm_maker_xml_nat
from exabox.core.DBStore import ebGetDefaultDB
from exabox.tools.ebTree.ebTreeNode import ebTreeNode
from exabox.utils.node import connect_to_host, node_cmd_abs_path_check, node_exec_cmd, node_exec_cmd_check, node_read_text_file, node_write_text_file
from exabox.tools.ebTree.ebTree import ebTree
from exabox.tools.ebOedacli.ebOedacli import ebOedacli
from exabox.ovm.vmcontrol import exaBoxOVMCtrl, ebVgLifeCycle
from exabox.core.Error import ebError, ExacloudRuntimeError, gReshapeError, gPartialError, gExaDbXSError
from exabox.exakms.ExaKmsEntry import ExaKmsHostType
from datetime import datetime
import exabox.ovm.clubonding as clubonding
from exabox.ovm.cluserialconsole import serialConsole
from exabox.agent.ExaLock import ExaLock
from exabox.ovm.csstep.cs_util import csUtil
from exabox.ovm.remotelock import RemoteLock
from exabox.exadbxs.edv import get_hosts_edv_from_cs_payload, get_hosts_edv_state, EDVState, build_hosts_edv_json

GUEST_IMAGES = '/EXAVMIMAGES/GuestImages'
VM_MAKER = '/opt/exadata_ovm/vm_maker'

##########################
### CALLBACK FUNCTIONS ###
##########################

def mReplaceDom0sFx(aNode, aArgs):

    if "text" in aNode.mGetElement():

        if aArgs["past_dom0_fqdn"] in aNode.mGetElement()['text']:
            aNode.mGetElement()["text"] = aNode.mGetElement()["text"].replace(aArgs["past_dom0_fqdn"], aArgs["new_dom0_fqdn"])

        if aArgs["past_dom0_host"] in aNode.mGetElement()['text']:
            aNode.mGetElement()["text"] = aNode.mGetElement()["text"].replace(aArgs["past_dom0_host"], aArgs["new_dom0_host"])

        if aArgs["past_dom0_ip"] == aNode.mGetElement()['text']:
            aNode.mGetElement()["text"] = aArgs["new_dom0_ip"]

    if "id" in aNode.mGetElement():

        if aArgs["past_dom0_fqdn"] in aNode.mGetElement()['id']:
            aNode.mGetElement()["id"] = aNode.mGetElement()["id"].replace(aArgs["past_dom0_fqdn"], aArgs["new_dom0_fqdn"])

        if aArgs["past_dom0_host"] in aNode.mGetElement()['id']:
            aNode.mGetElement()["id"] = aNode.mGetElement()["id"].replace(aArgs["past_dom0_host"], aArgs["new_dom0_host"])

def mPrepareForClone(aNode, aArgs):

    if aArgs["target_found"]:
        return

    if aNode.mGetParent() and \
       ( aNode.mGetSortElement() == "name" and aNode.mGetParent().mGetSortElement() == "vault" ):
        return

    # Ignore action metadata
    # TODO: Determine if the target dom0 is already in the XML by definition and not just string comparition
    if "action" in aNode.mGetSortElement() or \
       "subCommand" in aNode.mGetSortElement():
        return

    if aNode.mGetParent() and \
        (aNode.mGetSortElement() == "kvmHostName" and aNode.mGetParent().mGetSortElement() == "guestDisk"):
        return

    _toClone = False
    _element = aNode.mGetElement()

    if "text" in _element:

        if aArgs["source_name"].split(".")[0] in _element["text"]:
            _toClone = True

        if aArgs["target_name"].split(".")[0] in _element["text"]:
             aArgs["target_found"] = True

    if "id" in _element:

        if aArgs["source_name"].split(".")[0] in _element["id"]:
            _toClone = True

        if aArgs["target_name"].split(".")[0] in _element["id"]:
            aArgs["target_found"] = True

    if _toClone and aNode.mGetChildren():
        aArgs["source_nodes"].append(aNode)

def mRemoveVMmount(aCluObj, aDom0, aVMName, aStrict=False): 

    node_exec_cmd_callback = node_exec_cmd_check if aStrict else node_exec_cmd
    with connect_to_host(aDom0, get_gcontext()) as _node:

        # Make sure the VM is shut off
        shutdown_domu(_node, aVMName, force_on_timeout=True)

        _cmd = f"/bin/grep {aVMName} /etc/fstab | /bin/awk '{{ print $1 }}'"
        _srcGCV = node_exec_cmd(_node, _cmd).stdout.strip()
        ebLogInfo(f"source GCV: {_srcGCV} for vm: {aVMName}")

        _cmd = f"/bin/ls -ld {_srcGCV} | /bin/awk '{{ print $6 }}'"
        _gcv_minor = node_exec_cmd(_node, _cmd).stdout.strip()
        ebLogInfo(f"GCV minor: {_gcv_minor} for vm: {aVMName}")

        ebLogTrace(f"GCV device in {aDom0} ...")
        _cmd = f"/bin/ls -ld {_srcGCV}"
        ebLogTrace("******")
        _node.mExecuteCmdLog(_cmd)
        ebLogTrace("******")

        ebLogTrace(f"Current filesystem layout in {aDom0} ...")
        ebLogTrace("******")
        _node.mExecuteCmdLog("/bin/df -h")
        ebLogTrace("******")

        ebLogTrace(f"fuser {aVMName} in {aDom0} BEFORE umount...")
        _cmd = f"/sbin/fuser -muv /EXAVMIMAGES/GuestImages/{aVMName}"
        ebLogTrace("******")
        _node.mExecuteCmdLog(_cmd)
        ebLogTrace("******")

        ebLogTrace(f"dmesg dev{_gcv_minor} in {aDom0} BEFORE umount ...")
        ebLogTrace("******")
        _cmd = f"/bin/dmesg | /bin/grep dev{_gcv_minor}"
        _node.mExecuteCmdLog(_cmd)
        ebLogTrace("******")

        _cmd = f"/usr/bin/umount /EXAVMIMAGES/GuestImages/{aVMName}"
        node_exec_cmd_callback(_node, _cmd)

        ebLogTrace(f"fuser {_srcGCV} in {aDom0} AFTER umount...")
        _cmd = f"/sbin/fuser -muv {_srcGCV}"
        ebLogTrace("******")
        _node.mExecuteCmdLog(_cmd)
        ebLogTrace("******")

        ebLogTrace(f"Current filesystem layout in {aDom0} ...")
        ebLogTrace("******")
        _node.mExecuteCmdLog("/bin/df -h")
        ebLogTrace("******")

        ebLogTrace(f"dmesg dev{_gcv_minor} in {aDom0} AFTER umount ...")
        ebLogTrace("******")
        _cmd = f"/bin/dmesg | /bin/grep dev{_gcv_minor}"
        _node.mExecuteCmdLog(_cmd)
        ebLogTrace("******")

        _cmd = f"/usr/bin/rm -f /EXAVMIMAGES/GuestImages/{aVMName}/monitor*"
        node_exec_cmd_callback(_node, _cmd)

        _cmd = f"/usr/bin/rm -rf /EXAVMIMAGES/GuestImages/{aVMName}"
        node_exec_cmd_callback(_node, _cmd)

        _cmd = f'/bin/sed -i "/{aVMName}/d" /etc/fstab'
        node_exec_cmd_callback(_node, _cmd)

        # Update in-memory volume information
        _cmd = "/usr/bin/systemctl daemon-reload"
        node_exec_cmd(_node, _cmd)

def mSearchVolumesByVM(aNode, aArgs):

    if "volInfo" not in aArgs:
        aArgs["volInfo"] = []

    if aNode.mGetSortElement() == "hostName" and \
       aArgs["vmName"] in aNode.mGetElement()["text"]:

        if aNode.mGetParent().mGetSortElement() == "machine":

            _parent = aNode.mGetParent()
            for _child in _parent.mGetChildren():

                if _child.mGetSortElement() == "edvVolumes":

                    for _grandchild in _child.mGetChildren():
                        aArgs["volInfo"].append(_grandchild.mGetElement()["id"])


# Ideally call this function after mSearchVolumesByVM
def mSearchGcvVolDevicePath(aNode, aArgs):

    if "volInfo" not in aArgs:
        return

    if aNode.mGetSortElement() == "edvVolume" and \
       aNode.mGetChildren() and \
       aNode.mGetElement()["id"] in  aArgs["volInfo"]:

        _isGcv = False
        _devicePath = ""

        for _child in aNode.mGetChildren():

            if _child.mGetSortElement() == "edvVolumeName":
                _devicePath = _child.mGetElement()["text"]

            if _child.mGetSortElement() == "edvVolumeType" and \
               _child.mGetElement()["text"] == "GCVVOL":
                _isGcv = True

        if _isGcv:
            aArgs["gcvDevicePath"] = _devicePath

# Ideally call this function after mSearchVolumesByVM
# Gets all the edvdevicepath of all the volumes attached to vm as per xml except GCV volume
def mSearchEdvDevicePath(aNode, aArgs):

    if "volInfo" not in aArgs:
        return

    if "edvDevicePath" not in aArgs:
        aArgs["edvDevicePath"] = []

    if aNode.mGetSortElement() == "edvVolume" and \
       aNode.mGetChildren() and \
       aNode.mGetElement()["id"] in  aArgs["volInfo"]:

        _isGcv = False
        _edvdevicePath = ""

        for _child in aNode.mGetChildren():

            if _child.mGetSortElement() == "edvVolumeType" and \
               _child.mGetElement()["text"] == "GCVVOL":
                _isGcv = True

            if _child.mGetSortElement() == "edvDevicePath":
                _edvdevicePath = _child.mGetElement()["text"]

        if not _isGcv:
            aArgs["edvDevicePath"].append(_edvdevicePath)


######################
### EXASCALE CLASS ###
######################


class ebCluExaScale:

    def __init__(self, aCluCtrl):
        self.__ebox = aCluCtrl
        self.__failed_step = 'ALL'

    def mGetCluCtrl(self):
        return self.__ebox

    def mSetCluCtrl(self, aCluCtrl):
        self.__ebox = aCluCtrl

    def mGetFailedStep(self):
        return self.__failed_step

    # If something goes wrong Exacloud won't be able to handle it, so we
    # want to convey this message very clearly to the user.
    def fail(self,
            aErrorCode,
            aCausePlaceholders={},
            aSuggestionPlaceholders={}):
        # Format placeholders
        _errnum, _causeFmt, _suggestionFmt = gExaDbXSError[aErrorCode]
        _cause = _causeFmt.format(**aCausePlaceholders)
        _suggestion = _suggestionFmt.format(**aSuggestionPlaceholders)

        # Print error message and suggestion
        ebLogError(80*'*'); ebLogError(80*'*'); ebLogError(80*'*')
        ebLogError("******")
        ebLogError(f'****** VM MOVE PRE-CHECKS FAILED WITH "{aErrorCode}" '
                   'ERROR CODE')
        ebLogError("******")
        ebLogError("****** Cause:")
        ebLogError(f"****** {_cause}")
        ebLogError("******")
        ebLogError("****** Suggestion:...")
        ebLogError(f"****** {_suggestion}")
        ebLogError("******")
        ebLogError(80*'*'); ebLogError(80*'*'); ebLogError(80*'*')

        # Write Exacloud response payload for ECRA
        _requestResult = json.dumps(
            {
                "error_code": aErrorCode,
                "cause": _cause,
                "suggestion": _suggestion
            },
            indent=4
        )
        _req = self.__ebox.mGetRequestObj()
        if _req is not None:
            _req.mSetData(_requestResult)
            _db = ebGetDefaultDB()
            _db.mUpdateRequest(_req)

        # Skip failure or proceed
        _exascaleOpts = self.__ebox.mCheckConfigOption('exascale')
        if _exascaleOpts.get('vm_move_strict_errors', {})\
                        .get(aErrorCode, 'True').lower() == 'false':
            ebLogWarn("*** This error will be skipped due to exabox.conf "
                      "param, but please keep in mind that VM move will "
                      "potentially fail if you proceed!!!")
        else:
            raise ExacloudRuntimeError(_errnum, 0xA, _cause)

    def mRunExaDbXsChecks(self, aList = None):
        _ebox = self.mGetCluCtrl()
        if aList:
            _list = aList
        else:
            _list = _ebox.mReturnDom0DomUPair()

        # check if no stale bridges and EDV volumes are present
        _csu = csUtil()
        try:
            _csu.mDeleteStaleDummyBridge(_ebox, _list)
        except Exception as e:
            ebLogError("Stale bridges/EDV volumes present")
            raise ExacloudRuntimeError(0x0719, 0xA, "ExaDBXS Precheck failed")

        for _dom0, _ in _list:
            with connect_to_host(_dom0, get_gcontext()) as _node:
                # check if dom0 is empty
                _cmd = f"/usr/bin/virsh list --all --name"
                _vms = node_exec_cmd_check(_node, _cmd).stdout

                # check if no VM images are present
                _cmd = "/bin/ls /EXAVMIMAGES/GuestImages/"
                _vmimgs = node_exec_cmd_check(_node, _cmd).stdout

                # check status of interfaces
                """
                _cmd = "/bin/cat /sys/class/net/stre0/operstate"
                _opstre0 = node_exec_cmd_check(_node, _cmd).stdout

                _cmd = "/bin/cat /sys/class/net/stre1/operstate"
                _opstre1 = node_exec_cmd_check(_node, _cmd).stdout
                """

                if len(_vms.split()) != 0 or len(_vmimgs.split()) != 0:
                    ebLogInfo(f"vm list: {_vms}")
                    ebLogInfo(f"vm image list: {_vmimgs}")
                    ebLogInfo("For prechecks to PASS - dom0s should not be containing any VMs")
                    raise ExacloudRuntimeError(0x0719, 0xA, "ExaDBXS Precheck failed")

    def mApplyExaScaleXmlPatching(self):

        if not self.__ebox.mIsExaScale():
            return

        def mCleanCellMachinesFx(aNode, aArgs):

            if aNode.mGetSortElement() == "machine":

                # Detect cell
                _isCell = False
                for _child in aNode.mGetChildren():
                    if _child.mGetSortElement() == "machineType":
                        if _child.mGetElement()['text'] == "storage":
                            _isCell = True
                        break

                # Remove hostname
                if _isCell:

                    aArgs['cells_ids'].append(aNode.mGetElement()['id'])
                    for _child in aNode.mGetChildren():

                        if _child.mGetSortElement() == "networks":
                            for _grandChild in _child.mGetChildren():
                                aArgs['networks'].append(_grandChild.mGetElement()['id'])

                        if _child.mGetSortElement() == "hostName":
                            _child.mGetElement()['text'] = "dummy{0}".format(aArgs['count'])
                            aArgs['count'] += 1

        def mCleanCellNetworksFx(aNode, aArgs):

            if aNode.mGetSortElement() == "network" and \
                aNode.mGetElement()['id'] in aArgs['networks'] and \
                aNode.mGetChildren():

                _tagValue = {
                    "gateway": "1.1.1.0",
                    "hostName": "dummy{0}".format(aArgs['count']),
                    "ipAddress": "1.1.1.1"
                }

                aArgs['count'] += 1

                for _child in aNode.mGetChildren():

                    _tag = _child.mGetSortElement()
                    if _tag in _tagValue:
                        _child.mGetElement()['text'] = _tagValue[_tag]

        # Exascale log
        _localprfx = 'log/exascale_{0}'.format(self.__ebox.mGetUUID())
        self.__ebox.mExecuteLocal("/bin/mkdir -p {0}".format(_localprfx), aCurrDir=self.__ebox.mGetBasePath())

        _oedacli_bin = self.__ebox.mGetOedaPath() + '/oedacli'
        _oedacli = ebOedacli(_oedacli_bin, _localprfx, aLogFile="oedacli_exascale.log")

        # Save previous XML
        _initial = "{0}/01_initial.xml".format(_localprfx)
        _cellUpdate = "{0}/02_cellUpdate.xml".format(_localprfx)
        _storagePool = "{0}/03_storagePool.xml".format(_localprfx)

        _xmlTree = ebTree(self.__ebox.mGetPatchConfig())
        _xmlTree.mExportXml(_initial)

        # Cell modification
        _args = {"networks": [], "count": 1, "cells_ids": []}

        _xmlTree.mBFS(aStuffCallback=mCleanCellMachinesFx, aStuffArgs=_args)
        _xmlTree.mBFS(aStuffCallback=mCleanCellNetworksFx, aStuffArgs=_args)
        _xmlTree.mExportXml(_cellUpdate)

        # OEDACLI update
        _oedacliCmds = [
            ["ADD EXASCALECLUSTER", {"NAME": "exaoeda"}, None],
            ["ADD STORAGEPOOL", {"NAME": "hcpool", "SIZE":"42TB", "CELLLIST":"ALL", "TYPE": "HC"}, None],
            ["ADD VAULT", {"NAME": "vault1", "HC":"42TB"}, None],
            ["ALTER CLUSTER", {"VAULT":"vault1"}, {"CLUSTERNUMBER":"1"}],
        ]

        for _ocmd in _oedacliCmds:
            _oedacli.mAppendCommand(_ocmd[0], _ocmd[1], _ocmd[2])

        _oedacli.mRun(_cellUpdate, _storagePool)

        _xmlTree = ebTree(_storagePool)
        _xmlTree.mExportXml(self.__ebox.mGetPatchConfig())

        self.mUpdateVolumesOedacli(aWhen="CS")
        self.mUpdateDom0Network()
        self.mRemoveDomUBackupNetwork()
        self.mRemoveInterfaceInXml()

    def mRemoveInterfaceInXml(self):

        if self.__ebox.isDBonVolumes() or self.__ebox.isBaseDB() or self.__ebox.isExacomputeVM():

            # Exascale log
            _localprfx = 'log/exascale_{0}'.format(self.__ebox.mGetUUID())
            self.__ebox.mExecuteLocal("/bin/mkdir -p {0}".format(_localprfx), aCurrDir=self.__ebox.mGetBasePath())

            # XML to be used
            _initialXml = "{0}/before_interface_removal.xml".format(_localprfx)
            _updateXml = "{0}/after_interface_removal.xml".format(_localprfx)

            _xmlTree = ebTree(self.__ebox.mGetPatchConfig())
            _xmlTree.mExportXml(_initialXml)

            # OEDACLI location
            _oedacli_bin = self.__ebox.mGetOedaPath() + '/oedacli'
            _oedacli = ebOedacli(_oedacli_bin, _localprfx, aLogFile="oedacli_exascale.log")
            _oedacliCmds = []

            #Create the commands,
            # To delete streX and clreX in BaseDB , only streX in ASMonEDV
            _network_id_list = []
            for _, _domU in self.__ebox.mReturnDom0DomUPair():
                _domu_conf = self.__ebox.mGetMachines().mGetMacIdFromMacHostName(_domU)
                _domu_conf = self.__ebox.mGetMachines().mGetMachineConfig(_domu_conf)

                _domu_networks = _domu_conf.mGetMacNetworks()

                for _net_id in _domu_networks:
                    _net_conf = self.__ebox.mGetNetworks().mGetNetworkConfig(_net_id)

                    if _net_conf.mGetNetType() == "private":

                        if _net_conf.mGetInterfaceName().startswith("stre"):
                            _network_id_list.append(_net_id)

                        if (self.__ebox.isBaseDB() or self.__ebox.isExacomputeVM()) and _net_conf.mGetInterfaceName().startswith("clre"):
                            _network_id_list.append(_net_id)

            for _network_id in _network_id_list:

                _oedacliCmds.append(
                    ["DELETE NETWORK", None, {"ID": f"{_network_id}"}]
                )


            # Execute the commands
            if _oedacliCmds:

                ebLogInfo(f"Running DELETE NETWORK OEDACLI commands")

                for _ocmd in _oedacliCmds:
                    _oedacli.mAppendCommand(_ocmd[0], _ocmd[1], _ocmd[2])

                _oedacli.mRun(_initialXml, _updateXml)

                # Update XML to be used
                _xmlTree = ebTree(_updateXml)
                _xmlTree.mExportXml(self.__ebox.mGetPatchConfig())

            else:
                ebLogInfo(f"Skip DELETE NETWORK OEDACLI commands")

    def mRemoveDomUBackupNetwork(self):
        """
        BaseDB doesn't have backup network, so removing it
        """
        if self.__ebox.isBaseDB() or self.__ebox.isExacomputeVM():

            # Exascale log
            _localprfx = 'log/exascale_{0}'.format(self.__ebox.mGetUUID())
            self.__ebox.mExecuteLocal("/bin/mkdir -p {0}".format(_localprfx), aCurrDir=self.__ebox.mGetBasePath())

            # XML to be used
            _initialXml = "{0}/before_backup_network_removal.xml".format(_localprfx)
            _updateXml = "{0}/after_backup_network_removal.xml".format(_localprfx)

            _xmlTree = ebTree(self.__ebox.mGetPatchConfig())
            _xmlTree.mExportXml(_initialXml)

            # OEDACLI location
            _oedacli_bin = self.__ebox.mGetOedaPath() + '/oedacli'
            _oedacli = ebOedacli(_oedacli_bin, _localprfx, aLogFile="oedacli_exascale.log")
            _oedacliCmds = []

            #Create the commands,
            # To delete backup network for DomU
            _network_id_list = []
            for _, _domU in self.__ebox.mReturnDom0DomUPair():
                _domu_conf = self.__ebox.mGetMachines().mGetMacIdFromMacHostName(_domU)
                _domu_conf = self.__ebox.mGetMachines().mGetMachineConfig(_domu_conf)

                _domu_networks = _domu_conf.mGetMacNetworks()

                for _net_id in _domu_networks:
                    _net_conf = self.__ebox.mGetNetworks().mGetNetworkConfig(_net_id)

                    if _net_conf.mGetNetType() == "backup":
                        _network_id_list.append(_net_id)

            for _network_id in _network_id_list:

                _oedacliCmds.append(
                    ["DELETE NETWORK", None, {"ID": f"{_network_id}"}]
                )


            # Execute the commands
            if _oedacliCmds:

                ebLogInfo(f"Running DELETE NETWORK OEDACLI commands")

                for _ocmd in _oedacliCmds:
                    _oedacli.mAppendCommand(_ocmd[0], _ocmd[1], _ocmd[2])

                _oedacli.mRun(_initialXml, _updateXml)

                # Update XML to be used
                _xmlTree = ebTree(_updateXml)
                _xmlTree.mExportXml(self.__ebox.mGetPatchConfig())

            else:
                ebLogInfo(f"Skip DELETE NETWORK OEDACLI commands")


    def mUpdateDom0Network(self):

        # Exascale log
        _localprfx = 'log/exascale_{0}'.format(self.__ebox.mGetUUID())
        self.__ebox.mExecuteLocal("/bin/mkdir -p {0}".format(_localprfx), aCurrDir=self.__ebox.mGetBasePath())

        # XML to be used
        _initialXml = "{0}/12_before_dom0_net_update.xml".format(_localprfx)
        _updateXml = "{0}/13_after_dom0_net_update.xml".format(_localprfx)

        _xmlTree = ebTree(self.__ebox.mGetPatchConfig())
        _xmlTree.mExportXml(_initialXml)

        # OEDACLI location
        _oedacli_bin = self.__ebox.mGetOedaPath() + '/oedacli'
        _oedacli = ebOedacli(_oedacli_bin, _localprfx, aLogFile="oedacli_exascale.log")
        _oedacliCmds = []

        # Create the commands
        if "roce_information" in self.__ebox.mGetOptions().jsonconf:

            for _dom0, _info in self.__ebox.mGetOptions().jsonconf["roce_information"].items():

                _args1 = {
                    "HOSTNAME": f'{_dom0.split(".")[0]}-priv1',
                    "IP": _info["stre0_ip"]
                }
                _args2 = {
                    "HOSTNAME": f'{_dom0.split(".")[0]}-priv2',
                    "IP": _info["stre1_ip"]
                }

                if "subnet_mask" in _info:
                    _args1["NETMASK"] = _info["subnet_mask"]
                    _args2["NETMASK"] = _info["subnet_mask"]

                if "vlan_id" in _info:
                    _args1["VLANID"] = _info["vlan_id"]
                    _args2["VLANID"] = _info["vlan_id"]

                _oedacliCmds.append(
                    ["ALTER NETWORK", _args1, {"ID": f"{_dom0}_priv1"}]
                )

                _oedacliCmds.append(
                    ["ALTER NETWORK", _args2, {"ID": f"{_dom0}_priv2"}]
                )


        # Execute the commands
        if _oedacliCmds:

            ebLogInfo(f"Running ExaDB-XS Dom0 Net OEDACLI commands")

            for _ocmd in _oedacliCmds:
                _oedacli.mAppendCommand(_ocmd[0], _ocmd[1], _ocmd[2])

            _oedacli.mRun(_initialXml, _updateXml)

            # Update XML to be used
            _xmlTree = ebTree(_updateXml)
            _xmlTree.mExportXml(self.__ebox.mGetPatchConfig())

        else:
            ebLogInfo(f"Skip ExaDB-XS Dom0 Net OEDACLI commands")

    def mUpdateVolumesOedacli(self, aWhen="CS"):

        if self.__ebox.mCheckConfigOption("exascale_edv_enable", "True"):

            _clustername = self.__ebox.mGetClusters().mGetCluster().mGetCluName()

            # Exascale log
            _localprfx = 'log/exascale_{0}'.format(self.__ebox.mGetUUID())
            self.__ebox.mExecuteLocal("/bin/mkdir -p {0}".format(_localprfx), aCurrDir=self.__ebox.mGetBasePath())

            # XML to be used
            _initialXml = "{0}/10_before_volumes.xml".format(_localprfx)
            _updateXml = "{0}/11_after_volumes.xml".format(_localprfx)

            _xmlTree = ebTree(self.__ebox.mGetPatchConfig())
            _xmlTree.mExportXml(_initialXml)

            # OEDACLI location
            _oedacli_bin = self.__ebox.mGetOedaPath() + '/oedacli'
            _oedacli = ebOedacli(_oedacli_bin, _localprfx, aLogFile="oedacli_exascale.log")
            _oedacliCmds = []

            def mParseVolumeInformation(aVolumeJsonNode, aHostname, aOedacliComandsList):

                for _volumen in aVolumeJsonNode:

                    _path = _volumen["volumedevicepath"]
                    _voltype = ""
                    _mountpoint = ""

                    if _volumen["volumetype"].lower() == "gcv":
                        _voltype = "gcv"

                    elif _volumen["volumetype"].lower() == "system":
                        _voltype = "sys"

                    elif _volumen["volumetype"].lower() == "gi":
                        _voltype = "gi"

                    elif _volumen["volumetype"].lower() == "db":
                        _voltype = "db"

                    elif _volumen["volumetype"].lower() == "u01":
                        _voltype = "user"
                        _mountpoint = "u01"

                    #elif _volumen["volumetype"].lower() == "u02":
                    #    _voltype = "user"
                    #    _mountpoint = "u02"

                    else:
                        ebLogWarn(f'Invalid volumeType: {_volumen["volumetype"]}')
                        continue

                    if _voltype:

                        _basecmd = "ALTER EDVVOLUME"
                        if _mountpoint == "u02":
                           _basecmd = "ADD EDVVOLUME"

                        _argsJson = {
                            "VOLUMENAME": _path,
                            "DEVICE": f"/dev/exc/{_path}"
                        }

                        _whereJson = {
                            "HOSTNAME": aHostname
                        }

                        if _mountpoint == "u02":
                            _argsJson["MOUNTPATH"] = "/u02"
                            _argsJson["TYPE"] = _voltype
                        else:
                            _whereJson["TYPE"] = _voltype

                        _cmd = [
                            _basecmd,
                            _argsJson,
                            _whereJson
                        ]

                        aOedacliComandsList.append(_cmd)


                # Remove DB and GI
                _cmd = [
                    "DELETE EDVVOLUME",
                    {},
                    {
                        "HOSTNAMES": "all",
                        "TYPE": "gi"
                    }
                ]

                aOedacliComandsList.append(_cmd)

                _cmd = [
                    "DELETE EDVVOLUME",
                    {},
                    {
                        "HOSTNAMES": "all",
                        "TYPE": "db"
                    }
                ]

                aOedacliComandsList.append(_cmd)

            def mParseVolumeInformation_19c(aVolumeJsonNode, aHostname, aOedacliComandsList):

                if self.__ebox.mCheckConfigOption("exadbxs_19c_invoke_oedacli", "True"):

                    for _volumen in aVolumeJsonNode:

                        _path = _volumen["volumedevicepath"]
                        _voltype = ""
                        _mountpoint = ""
                        _guestvol = ""

                        if _volumen["volumetype"].lower() == "gcv":
                            _voltype = "gcv"

                        elif _volumen["volumetype"].lower() == "system":
                            _voltype = "sys"

                        elif _volumen["volumetype"].lower() == "gi":
                            _voltype = "gi"

                        elif _volumen["volumetype"].lower() == "db":
                            _voltype = "db"

                        elif _volumen["volumetype"].lower() == "u01":
                            _voltype = "user"
                            _mountpoint = "u01"

                        elif _volumen["volumetype"].lower() == "dbvolume":
                            _guestvol = _volumen["guestdevicename"]

                        elif _volumen["volumetype"].lower() == "sw" and self.__ebox.isBaseDB():
                            _guestvol = "dbvolume-sw-bdbs"                    


                        #elif _volumen["volumetype"].lower() == "u02":
                        #    _voltype = "user"
                        #    _mountpoint = "u02"

                        else:
                            ebLogWarn(f'Invalid volumeType: {_volumen["volumetype"]}')
                            continue

                        if _voltype:

                            _basecmd = "ALTER EDVVOLUME"
                            if _mountpoint == "u02":
                                _basecmd = "ADD EDVVOLUME"

                            _argsJson = {
                                "VOLUMENAME": _path,
                                "DEVICE": f"/dev/exc/{_path}"
                            }

                            _whereJson = {
                                "HOSTNAME": aHostname
                            }

                            if _mountpoint == "u02":
                                _argsJson["MOUNTPATH"] = "/u02"
                                _argsJson["TYPE"] = _voltype
                            else:
                                _whereJson["TYPE"] = _voltype

                            _cmd = [
                                _basecmd,
                                _argsJson,
                                _whereJson
                            ]

                            aOedacliComandsList.append(_cmd)

                        elif _guestvol:
                            _basecmd = "ADD EDVVOLUME"

                            _argsJson = {
                                "DEVICE": f"/dev/exc/{_path}",
                                "SERIAL": f"{_guestvol}"
                            }

                            _whereJson = {
                                "HOSTNAME": aHostname
                            }

                            _cmd = [
                                _basecmd,
                                _argsJson,
                                _whereJson
                            ]

                            aOedacliComandsList.append(_cmd)


                    # Remove DB and GI
                    _cmd = [
                        "DELETE EDVVOLUME",
                        {},
                        {
                            "HOSTNAMES": "all",
                            "TYPE": "gi"
                        }
                    ]

                    aOedacliComandsList.append(_cmd)

                    _cmd = [
                        "DELETE EDVVOLUME",
                        {},
                        {
                            "HOSTNAMES": "all",
                            "TYPE": "db"
                        }
                    ]

                    aOedacliComandsList.append(_cmd)

                    # For BaseDB remove the uservol also, as the template xml is sending that
                    if self.__ebox.isBaseDB() or self.__ebox.isExacomputeVM():
                        _cmd = [
                            "DELETE EDVVOLUME",
                            {},
                            {
                                "HOSTNAMES": "all",
                                "TYPE": "user"
                            }
                        ]

                        aOedacliComandsList.append(_cmd)

            if aWhen == "CS":

                # Adding commands to support EDV volumes in CS
                if "customer_network" in self.__ebox.mGetOptions().jsonconf and \
                   "nodes" in self.__ebox.mGetOptions().jsonconf["customer_network"]:

                    # Initial oedacli command
                    _oedacliCmds.append(
                        ["ALTER MACHINES ", {"STORAGETYPE":"CELLDISK"}, {"TYPE":"GUEST"}]
                    )

                    if self.__ebox.isDBonVolumes():
                        _oedacliCmds.append(
                            ["ALTER CLUSTER ", {"STORAGETEMPLATE":"ASMonEDV"}, {"CLUSTERNAME": _clustername}]
                        )
                    elif self.__ebox.isBaseDB() or self.__ebox.isExacomputeVM():
                        _oedacliCmds.append(
                            ["ALTER CLUSTER ", {"STORAGETEMPLATE":"BaseDB"}, {"CLUSTERNAME": _clustername}]
                        )

                    _nodes = self.__ebox.mGetOptions().jsonconf["customer_network"]["nodes"]
                    for _jNode in _nodes:

                        if "volumes" in _jNode:

                            _hostname = f'{_jNode["client"]["hostname"]}.{_jNode["client"]["domainname"]}'
                            if self.__ebox.isDBonVolumes() or self.__ebox.isBaseDB() or self.__ebox.isExacomputeVM():
                                mParseVolumeInformation_19c(_jNode["volumes"], _hostname, _oedacliCmds)
                            else:
                                mParseVolumeInformation(_jNode["volumes"], _hostname, _oedacliCmds)

                            _volumeInfoFile = self.__ebox.mCheckConfigOption("override_volume_file")
                            if _volumeInfoFile and os.path.exists(_volumeInfoFile):
                                with open(_volumeInfoFile) as _f:
                                    _moreinfo = json.loads(_f.read())
                                    if _jNode["client"]["dom0_oracle_name"] in _moreinfo:
                                        mParseVolumeInformation(_moreinfo[_jNode["client"]["dom0_oracle_name"]], _hostname, _oedacliCmds)

            if aWhen == "AddNode":

                # Add commands to support EDV volumes in Add Node
                if "reshaped_node_subset" in self.__ebox.mGetOptions().jsonconf and \
                   "added_computes" in self.__ebox.mGetOptions().jsonconf["reshaped_node_subset"]:

                    if self.__ebox.isDBonVolumes():
                        _oedacliCmds.append(
                            ["ALTER CLUSTER ", {"STORAGETEMPLATE":"ASMonEDV"}, {"CLUSTERNAME": _clustername}]
                        )
                    elif self.__ebox.isBaseDB() or self.__ebox.isExacomputeVM():
                        _oedacliCmds.append(
                            ["ALTER CLUSTER ", {"STORAGETEMPLATE":"BaseDB"}, {"CLUSTERNAME": _clustername}]
                        )

                    _nodes = self.__ebox.mGetOptions().jsonconf["reshaped_node_subset"]["added_computes"]
                    for _jNode in _nodes:

                        if "volumes" in _jNode:
                            _hostname = f'{_jNode["virtual_compute_info"]["compute_node_hostname"]}'
                            if self.__ebox.isDBonVolumes() or self.__ebox.isBaseDB() or self.__ebox.isExacomputeVM():
                                mParseVolumeInformation_19c(_jNode["volumes"], _hostname, _oedacliCmds)
                            else:
                                 mParseVolumeInformation(_jNode["volumes"], _hostname, _oedacliCmds)

            if aWhen == "DeleteNode":

                if "reshaped_node_subset" in self.__ebox.mGetOptions().jsonconf and \
                   "removed_computes" in self.__ebox.mGetOptions().jsonconf["reshaped_node_subset"] and \
                   self.__ebox.mGetOptions().jsonconf["reshaped_node_subset"]["removed_computes"]:

                        _nodes = self.__ebox.mGetOptions().jsonconf["reshaped_node_subset"]["removed_computes"]
                        for _jNode in _nodes:
                            _hostname = _jNode["compute_node_virtual_hostname"]
                            _cmd = [
                                "DELETE EDVVOLUME",
                                {},
                                {"HOSTNAMES": _hostname}
                            ]
                        _oedacliCmds.append(_cmd)

            if _oedacliCmds:

                ebLogInfo(f"Running ExaDB-XS Volume OEDACLI commands in {aWhen}")

                for _ocmd in _oedacliCmds:
                    _oedacli.mAppendCommand(_ocmd[0], _ocmd[1], _ocmd[2])

                _oedacli.mRun(_initialXml, _updateXml)

                # Update XML to be used
                _xmlTree = ebTree(_updateXml)
                _xmlTree.mExportXml(self.__ebox.mGetPatchConfig())

            else:
                ebLogInfo(f"Skip ExaDB-XS Volume OEDACLI commands in {aWhen}")

    def mAttachDBVolumetoGuestVMs(self, aWhen="CS"):

        """
        Exacloud implementation for 19c support for Database on Exascale volumes
        """

        def mExecuteAttachDBVolume(aVolumeJsonNode, aDom0Name, aDomUName):

            _domUName = aDomUName
            _dom0Name = aDom0Name
            for _volumen in aVolumeJsonNode:

                if _volumen["volumetype"].lower() == "dbvolume":
                    _dbVolumepath = _volumen["volumedevicepath"]
                    _hostdiskpath = f"/dev/exc/{_dbVolumepath}"
                    _guestvol = _volumen["guestdevicename"]

                    with connect_to_host(_dom0Name, get_gcontext()) as _node:
                        attach_dom0_disk_image(_node, _domUName, _hostdiskpath, 'none', 'native', _guestvol)

        try:
            if aWhen == "CS":
                if "customer_network" in self.__ebox.mGetOptions().jsonconf and \
                    "nodes" in self.__ebox.mGetOptions().jsonconf["customer_network"]:

                    _nodes = self.__ebox.mGetOptions().jsonconf["customer_network"]["nodes"]
                    for _jNode in _nodes:
                        if "volumes" in _jNode:
                            _domUName = f'{_jNode["client"]["hostname"]}.{_jNode["client"]["domainname"]}'

                            _dom0Name = ""
                            for _dom0, _domU in self.__ebox.mReturnDom0DomUPair():
                                if _jNode["client"]["dom0_oracle_name"] in _dom0:
                                    _dom0Name = _dom0
                                    break

                            if not _dom0Name:
                                raise ExacloudRuntimeError(0x0811, 0xA, f'Missing {_jNode["client"]["dom0_oracle_name"]} in dom0-domu list {self.__ebox.mReturnDom0DomUPair()} as per xml')

                            mExecuteAttachDBVolume(_jNode["volumes"], _dom0Name, _domUName)

            if aWhen == "AddNode":
                if "reshaped_node_subset" in self.__ebox.mGetOptions().jsonconf and \
                    "added_computes" in self.__ebox.mGetOptions().jsonconf["reshaped_node_subset"]:

                    _nodes = self.__ebox.mGetOptions().jsonconf["reshaped_node_subset"]["added_computes"]
                    for _jNode in _nodes:

                        if "volumes" in _jNode:
                            _domUName = f'{_jNode["virtual_compute_info"]["compute_node_hostname"]}'
                            _dom0Name = ""
                            for _dom0, _domU in self.__ebox.mReturnDom0DomUPair():
                                if _jNode["compute_node_hostname"] in _dom0:
                                    _dom0Name = _dom0
                                    break
                            if not _dom0Name:
                                raise ExacloudRuntimeError(0x0811, 0xA, f'Missing {_jNode["compute_node_hostname"]} in dom0-domu list {self.__ebox.mReturnDom0DomUPair()} as per xml')

                            mExecuteAttachDBVolume(_jNode["volumes"], _dom0Name, _domUName)
        except Exception as ex:
            _msg = f"*** EXADB-XS: Attaching DBVOLUME to GuestVMs failed with Exception: {ex}"
            ebLogError(_msg)
            raise ExacloudRuntimeError(0x0811, 0xA, _msg)

    def mWriteUdevDbVolumesRules(self):
        """
        Creates and updates /etc/udev/rules.d/66-dbvolume.rules with dbvolume*
        Also reload and applies the udev rules for dbaastools to use
        """

        DBVOLUME_RULES_PATH = "/etc/udev/rules.d/66-dbvolume.rules"

        for _, _domU in  self.__ebox.mReturnDom0DomUPair():
            with connect_to_host(_domU, get_gcontext(), username='root') as _node:
                
                UDEVADM : str = node_cmd_abs_path_check(_node, 'udevadm', sbin=True)
                rules = "\n".join([
                    f'KERNEL=="sd*", ENV{{ID_SCSI_SERIAL}}=="dbvolume*", SYMLINK+="%E{{ID_SCSI_SERIAL}}", OWNER="grid", GROUP="asmadmin", MODE="0660"',
                ]) + "\n"

                _node.mWriteFile(DBVOLUME_RULES_PATH, rules.encode('utf-8'), aAppend=False)
                ebLogInfo(f"{DBVOLUME_RULES_PATH} updated with udev rules")
                
                _cmd = f"{UDEVADM} control --reload-rules"
                node_exec_cmd_check(_node, _cmd)

                _cmd = f"{UDEVADM} trigger"
                node_exec_cmd_check(_node, _cmd)

    def mRemoveCellinitOra(self):
        """
        remove the /etc/oracle/cell/network-config/cellinit.ora file for 19c and base db provisioning,
        as cellinit.ora is empty for this case, but cause failure in root.sh run in dbaas layer
        """

        CELLINIT_ORA_PATH = "/etc/oracle/cell/network-config/cellinit.ora"

        for _, _domU in  self.__ebox.mReturnDom0DomUPair():
            with connect_to_host(_domU, get_gcontext(), username='root') as _node:
                RM: str = node_cmd_abs_path_check(_node, 'rm', sbin=True)
                _cmd = f"{RM} -f {CELLINIT_ORA_PATH}"
                node_exec_cmd_check(_node, _cmd)
        
    def mCreateOedaProperties(self):

        if not self.__ebox.mCheckConfigOption("exascale_oeda_properties_patch", "True"):
            ebLogInfo("Skip mCreateOedaProperties by exabox.conf parameter")
            return

        if self.__ebox.mIsNoOeda():
            ebLogInfo("Skip mCreateOedaProperties since No-OEDA")
            return

        # Cache files of oeda properties
        _exacloudPath = os.path.abspath(__file__)
        _exacloudPath = _exacloudPath[0: _exacloudPath.rfind("exacloud")+8]

        _cachePath = f"{_exacloudPath}/properties/exascale_cache_oeda"
        _reqPath = f"{self.__ebox.mGetOedaPath()}/properties/"

        if os.path.exists(_cachePath):

            # Validate same oeda version
            _cmd = f"/bin/grep BUILDBRANCH {_cachePath}/properties/es.properties"
            _, _, _labelCache, _ = self.__ebox.mExecuteLocal(_cmd)

            _cmd = f"/bin/grep BUILDBRANCH {_reqPath}/es.properties"
            _, _, _labelOeda, _ = self.__ebox.mExecuteLocal(_cmd)

            if _labelCache == _labelOeda:

                _cmd = f"/bin/chmod 755 -R {self.__ebox.mGetOedaPath()}/properties"
                self.__ebox.mExecuteLocal(_cmd)

                _cmd = f"/bin/cp -r {_cachePath}/properties {self.__ebox.mGetOedaPath()}"
                self.__ebox.mExecuteLocal(_cmd)

                ebLogInfo(f"OEDA properties updated from cache: {_cachePath}")
                return

            else:
                _cmd = f"/bin/rm -rf {_cachePath}"
                self.__ebox.mExecuteLocal(_cmd)


        _localprfx = 'log/exascale_{0}'.format(self.__ebox.mGetUUID())
        _propertiesFile = "properties/OEDAProperties_Exascale.json"
        _properties = {}

        if not os.path.exists(_propertiesFile):
            ebLogInfo(f"Missing  file {_propertiesFile}")
            return

        with open(_propertiesFile, "r") as _f:
            _properties = json.load(_f)

        if not _properties:
            ebLogInfo(f"Missing values into file {_propertiesFile}")
            return

        # Create temp file
        _cmds = []
        for _name, _value in _properties.items():

            _cmd = 'ALTER PROPERTY NAME=%s VALUE="%s"' % (_name, _value)
            _cmds.append(_cmd)

        _tmpPath = f"/tmp/tmp_oedacli_commands_{self.__ebox.mGetUUID()}"
        with open(_tmpPath, "w") as _f:
            for _cmd in _cmds:
                _f.write(_cmd)
                _f.write("\n")

        # Invoke oedacli
        _oedacliBin = self.__ebox.mGetOedaPath() + '/oedacli'

        ebLogInfo(f"Patching ExaScale OEDA Properties: {_tmpPath}")

        _applyCmd = f"{_oedacliBin} -f {_tmpPath}"
        _rc, _, _o, _e = self.__ebox.mExecuteLocal(_applyCmd)

        ebLogInfo(_o)
        ebLogInfo(_e)

        # Save cache files
        _cmd = f"/bin/mkdir -p {_cachePath}"
        self.__ebox.mExecuteLocal(_cmd)

        _cmd = f"/bin/cp -r {_reqPath} {_cachePath}"
        self.__ebox.mExecuteLocal(_cmd)

        _cmd = f"/bin/chmod 755 -R {_cachePath}"
        self.__ebox.mExecuteLocal(_cmd)

        if not self.__ebox.mIsDebug():
            self.__ebox.mExecuteLocal(f"/bin/rm {_tmpPath}")


    def mCreateDummyCellsKeys(self):

        def mCountCellMachinesFx(aNode, aArgs):
            if aNode and aNode.mGetSortElement() == "machine":
                # Detect cell
                for _child in aNode.mGetChildren():
                    if _child.mGetSortElement() == "machineType":
                        if _child.mGetElement()['text'] == "storage":
                            aArgs["count"] += 1

        _xmlTree = ebTree(self.__ebox.mGetPatchConfig())
        _args = { "count": 0 }
        _xmlTree.mBFS(aStuffCallback=mCountCellMachinesFx, aStuffArgs=_args)

        # Create dummy keys in workdir
        for _i in range(1, _args['count']+1):

            _oedaFile = f"{self.__ebox.mGetOedaPath()}/WorkDir/id_rsa.dummy{_i}.root"
            open(_oedaFile, 'w').close()

            _oedaFile = f"{self.__ebox.mGetOedaPath()}/WorkDir/id_rsa.dummy{_i}.root.pub"
            open(_oedaFile, 'w').close()


    def mConfigureHugePage(self, aOptions):

        ebLogInfo("Configure Huge Page for ExaScale")

        _options = aOptions
        _jconf = aOptions.jsonconf
        _host_d = {}

        # By the doc, the default page size is 2MB
        # https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/8/html
        # /monitoring_and_managing_system_status_and_performance/configuring-huge-pages_monitoring-and-managing-system-status-and-performance
        _defaultHugePageSizeMB = 2

        # Get memory from Payload
        if 'vms' in _jconf.keys():
            for _h in _jconf['vms']:
                _host_d[_h['hostname']] = int(_h['gb_memory'])

        elif 'vm' in _jconf.keys():
            for _, _h in self.__ebox.mReturnDom0DomUPair():
                _host_d[_h] = int(_jconf["vm"]['gb_memory'])

        elif 'gb_memory' in _jconf.keys():
            for _, _h in self.__ebox.mReturnDom0DomUPair():
                _host_d[_h] = int(_jconf['gb_memory'])

        elif 'reshaped_node_subset' in _jconf.keys():
            for _h in _jconf['reshaped_node_subset']['added_computes']:
                _vci = _h['virtual_compute_info']
                _host_d[_vci['compute_node_hostname']] = int(_vci['vm']['gb_memory'])

        # Get desire memory percentage
        _percentage = 50
        try:
            _percentage = int(self.__ebox.mCheckConfigOption("exascale_hugepage_memory_percentage"))
        except:
            pass

        # Process the new configuration
        for _dom0, _domU in self.__ebox.mReturnDom0DomUPair():

            with connect_to_host(_domU, get_gcontext()) as _node:

                # The actual values are in GB, but the configuration is needed in MB
                _memsizeMB = int( _host_d[_domU] * 1024 )
                _memsizeRatioMB = int( ( _memsizeMB * _percentage ) / 100 )
                _hugePageConfigValue = int( _memsizeRatioMB / _defaultHugePageSizeMB )

                ebLogInfo(f"Requested {_percentage}% of memory, All memory in MB: {_memsizeMB}")
                ebLogInfo(f"New Huge Page in MB (New Sysctl Value [{_hugePageConfigValue}]) * (Default Size in MB [{_defaultHugePageSizeMB}]) = (Total Memory in MB for Huge Pages [{_memsizeRatioMB}])")

                # Set Huge Page
                self.__ebox.mSetSysCtlConfigValue(_node, "vm.nr_hugepages", _hugePageConfigValue, aRaiseException=False)


    def mMigrateXMLNetworkInformation(self, aTargetName, aNetInfo, aOptions):

        def mReplaceNetFx(aNode, aArgs):

            # Locate VM NAT network object
            if "text" in aNode.mGetElement() and \
               aArgs["old_ip"] in aNode.mGetElement()["text"]:

                _parent = aNode.mGetParent()
                _childrenToRemove = [
                    _children for _children in _parent.mGetChildren()
                    if _children.mGetSortElement() in (
                        "natipAddress", "nathostName", "natdomainName",
                        "natGateway", "natnetMask", "natVlanId"
                    )
                ]
                for _children in _childrenToRemove:
                    _children.mRemove()

                ebTreeNode({ "text": aArgs["new_ip"], "tag": "natipAddress" }, _parent)
                ebTreeNode({ "text": aArgs["new_hostname"], "tag": "nathostName" }, _parent)
                ebTreeNode({ "text": aArgs["new_domain"], "tag": "natdomainName" }, _parent)
                ebTreeNode({ "text": aArgs["new_netmask"], "tag": "natnetMask" }, _parent)
                _newNatVlan = aArgs.get("new_vlan")
                if _newNatVlan is not None:
                    ebTreeNode({ "text": _newNatVlan, "tag": "natVlanId" }, _parent)
                _newNatGateway = aArgs.get("new_gateway")
                if _newNatGateway is not None:
                    ebTreeNode({ "text": _newNatGateway, "tag": "natGateway" }, _parent)

            # Locate target Dom0 RoCE network objects
            def mReplaceRoCE(aID, aHostname):
                if aArgs["new_roce"] is not None and \
                    "text" in aNode.mGetElement() and \
                    aNode.mGetElement()["text"] == \
                        f"{aHostname.split('.')[0]}-priv{aID+1}":

                    _parent = aNode.mGetParent()
                    _childrenToRemove = [
                        _children for _children in _parent.mGetChildren()
                        if _children.mGetSortElement() in (
                            "ipAddress", "netMask", "vlanId"
                        )
                    ]
                    for _children in _childrenToRemove:
                        _children.mRemove()

                    ebTreeNode({ "text": aArgs["new_roce"][aHostname][f"stre{aID}_ip"], "tag": "ipAddress" }, _parent)
                    ebTreeNode({ "text": aArgs["new_roce"][aHostname]["subnet_mask"], "tag": "netMask" }, _parent)
                    ebTreeNode({ "text": aArgs["new_roce"][aHostname]["vlan_id"], "tag": "vlanId" }, _parent)

            mReplaceRoCE(0, aArgs["source_dom0_name"])
            mReplaceRoCE(1, aArgs["source_dom0_name"])
            mReplaceRoCE(0, aArgs["target_dom0_name"])
            mReplaceRoCE(1, aArgs["target_dom0_name"])

        # Replace information in the XML
        _localprfx = 'log/exascale_{0}'.format(self.__ebox.mGetUUID())
        self.__ebox.mExecuteLocal("/bin/mkdir -p {0}".format(_localprfx), aCurrDir=self.__ebox.mGetBasePath())

        _initialXml = "{0}/20_vm_move_net_update_initial.xml".format(_localprfx)
        _finalXml = "{0}/20_vm_move_net_update_final.xml".format(_localprfx)

        _xmlTree = ebTree(self.__ebox.mGetPatchConfig())
        _xmlTree.mExportXml(_initialXml)

        _xmlTree.mBFS(aStuffCallback=mReplaceNetFx, aStuffArgs=aNetInfo)
        _xmlTree.mExportXml(_finalXml)
        _xmlTree.mExportXml(self.__ebox.mGetPatchConfig())

        # Refresh dom0-domU pair
        self.mGetCluCtrl().mParseXMLConfig(aOptions)



    def mCleanUpVMMove(self, aOptions):

        # Validate input payload
        _payloadFields: Sequence[str] = \
            ('vm_name', 'target_dom0_name', 'source_dom0_name',
            'new_admin_hostname', 'new_admin_domainname')
        for _field in _payloadFields:
            if _field not in aOptions.jsonconf:
                raise ExacloudRuntimeError(
                    0x0811, 0xA, f'Missing "{_field}" in ExaScale Payload')

        _vmName = aOptions.jsonconf["vm_name"]
        _tgtDom0 = aOptions.jsonconf["target_dom0_name"]
        _srcDom0 = aOptions.jsonconf["source_dom0_name"]
        _newNatHostname = aOptions.jsonconf["new_admin_hostname"]
        _newNatDomainName = aOptions.jsonconf["new_admin_domainname"]

        # Get the client & backup VLAN IDs
        _force = str(aOptions.jsonconf.get('force')).lower() == 'true'

        _oldClientVlan = ""
        _oldBackupVlan = ""
        _machineConfig = self.__ebox.mGetMachines().mGetMachineConfig(_vmName)
        _netIds = _machineConfig.mGetMacNetworks()
        for _netId in _netIds:
            _netConf = self.__ebox.mGetNetworks().mGetNetworkConfig(_netId)
            _net_type = _netConf.mGetNetType()
            if _net_type == 'client':
                _oldClientVlan = _netConf.mGetNetVlanId()
            if _net_type == 'backup':
                _oldBackupVlan = _netConf.mGetNetVlanId()


        _lock = self.mCreateLockObj(aOptions)
        try:
            ebLogInfo(f"Acquiring lock for {_srcDom0} before removing bridge !")
            _lock.acquire()

            if not _force:
                with connect_to_host(_srcDom0, get_gcontext()) as _node:

                    if _oldClientVlan and _oldClientVlan.strip().upper() != "UNDEFINED":
                        _cmd = f"{VM_MAKER} --remove-bridge vmbondeth0.{_oldClientVlan}"
                        node_exec_cmd(_node, _cmd)

                    if _oldBackupVlan and _oldBackupVlan.strip().upper() != "UNDEFINED":
                        _cmd = f"{VM_MAKER} --remove-bridge vmbondeth0.{_oldBackupVlan}"
                        node_exec_cmd(_node, _cmd)

            elif self.mGetCluCtrl().mPingHost(_srcDom0):
                with connect_to_host(_srcDom0, get_gcontext()) as _srcNode:
                    _cmd = "/bin/virsh list --all --name"
                    _srcVMs = node_exec_cmd_check(_srcNode, _cmd).stdout
                    if _vmName not in _srcVMs:
                        ebLogInfo(f"VM {_vmName} not defined in host {_srcDom0}")
                    else:
                        _vmBridges = get_kvm_guest_bridges(_srcNode, _vmName)
                        _cmd = f"/bin/virsh destroy {_vmName}"
                        node_exec_cmd(_srcNode, _cmd)
                        _cmd = f"/bin/virsh undefine {_vmName}"
                        node_exec_cmd(_srcNode, _cmd)
                        for _bridge in _vmBridges:
                            _cmd = f"{VM_MAKER} --remove-bridge {_bridge}"
                            node_exec_cmd(_srcNode, _cmd)
                            ebLogInfo(f"Bridge {_bridge} removed from {_srcDom0}")

            else:
                ebLogWarn(f"*** Source Dom0 {_srcDom0} is not reachable. "
                          "Skipping cleanup...")

        except Exception as ex:
            _msg = f"*** EXASCALE: mCleanUpVMMove: Exception: {ex}"
            ebLogWarn(_msg)
        finally:
            _lock.release()

    def mPostVMMoveSteps(self, aOptions):
        """Performs the remaining steps for VM move that OEDA does not execute.

        This includes the following tasks.
         - Migrate the dynamic iptables or nftables.
        
        :param aOptions: Exacloud options object.
        """

        # Validate input payload
        _payloadFields: Sequence[str] = \
            ('vm_name', 'target_dom0_name', 'source_dom0_name',
            'new_admin_hostname', 'new_admin_domainname')
        for _field in _payloadFields:
            if _field not in aOptions.jsonconf:
                raise ExacloudRuntimeError(
                    0x0811, 0xA, f'Missing "{_field}" in ExaScale Payload')

        _force = str(aOptions.jsonconf.get('force')).lower() == 'true'
        _vmName = aOptions.jsonconf["vm_name"]
        _tgtDom0 = aOptions.jsonconf["target_dom0_name"]
        _srcDom0 = aOptions.jsonconf["source_dom0_name"]
        _newNatHostname = aOptions.jsonconf["new_admin_hostname"]
        _newNatDomainName = aOptions.jsonconf["new_admin_domainname"]

        # Get the client & backup VLAN IDs
        _oldClientVlan = ""
        _oldBackupVlan = ""
        _machineConfig = self.__ebox.mGetMachines().mGetMachineConfig(_vmName)
        _netIds = _machineConfig.mGetMacNetworks()
        for _netId in _netIds:
            _netConf = self.__ebox.mGetNetworks().mGetNetworkConfig(_netId)
            _net_type = _netConf.mGetNetType()
            if _net_type == 'client':
                _oldClientVlan = _netConf.mGetNetVlanId()
            if _net_type == 'backup':
                _oldBackupVlan = _netConf.mGetNetVlanId()

        _live = str(aOptions.jsonconf.get('mode')).lower() == 'live'
        if _live:
            _netInfo = self.mPrepareNetInfo(aOptions)
            self.mUmountVolumesVmMove(_netInfo["source_dom0_name"], aOptions.jsonconf["vm_name"], _netInfo, aStrict=False)

        # Verify there is not stale GCV EDV in the soruce host
        if not _force:
            _tgtGCV = self.mGetGcvDevicePath(aOptions)
            with connect_to_host(_srcDom0, get_gcontext()) as _srcNode:
                _tgtGCVPath = f"/dev/exc/{_tgtGCV}"
                _cmd = f"/bin/ls {_tgtGCVPath}"
                _ret = node_exec_cmd(_srcNode, _cmd).exit_code
                if _ret == 0:
                    ebLogWarn("EXASCALE: WARNING: STALE GCV VOLUME FOUND "
                              f"{_tgtGCVPath} ON HOST {_srcDom0}")

        _newDom0sDomUs: List[List[str]] = [[_tgtDom0, _vmName]]
        _newDom0sDomUsNAT: List[List[str]] = [[_tgtDom0, _newNatHostname]]
        if self.__ebox.isBaseDB() or self.__ebox.isExacomputeVM():
            self.__ebox.mSetDomUsDom0s(_vmName, sorted(_newDom0sDomUs))
        else:
            # Update the Dom0-DomU pairs
            _clusterId = self.__ebox.mGetClusters().mGetCluster().mGetCluId()
            self.__ebox.mSetDomUsDom0s(_clusterId, sorted(_newDom0sDomUs))
        self.__ebox._exaBoxCluCtrl__domus_dom0s_nat = sorted(_newDom0sDomUsNAT)

        with connect_to_host(_tgtDom0, get_gcontext()) as _tgtNode:
            # Migrate the NAT routing tables/rules
            add_kvm_guest_nat_routing(_tgtNode, _vmName)

            """
            # Attach u02 again
            _cmd = f"/bin/virsh domblklist {_vmName} | /bin/tail -n +3"
            _vmDisks = node_exec_cmd_check(_tgtNode, _cmd).stdout.splitlines()
            _vmSystemEDV, *_ = ( 
                _edv.split()[1] for _edv in _vmDisks
                if _edv.strip() and _edv.split()[1].startswith('/dev/exc/system')
            )
            _, _vmEDVID, *_ = _vmSystemEDV.split('_')
            _vmU02EDVFmt = f"/dev/exc/u02_{_vmEDVID}_*"
            _cmd = f"/bin/ls {_vmU02EDVFmt}"
            _vmU02EDV = node_exec_cmd_check(_tgtNode, _cmd).stdout.strip()
            attach_dom0_disk_image(_tgtNode, _vmName, _vmU02EDV, 'none', 'native')
            """

            # Add the serial console symlink if missing
            # TODO: This code is just a workaround and can be removed once the
            #       following fix is included in an official Exadata release.
            # Bug 35923224 - EXADB-XS: OEDA : VM MIGRATION IS NOT CONFIGURING
            #                SERIAL CONSOLE ON TARGET HOST
            _cmd = (f"/bin/virsh dumpxml {_vmName} | "
                    '/bin/grep serial.sock | /bin/cut -d"/" -f4')
            _serialId = node_exec_cmd_check(_tgtNode, _cmd).stdout.strip()
            _cmd = f"/bin/mkdir -p /EXAVMIMAGES/console/{_serialId}"
            node_exec_cmd_check(_tgtNode, _cmd)
            _cmd = ("/bin/ln -s "
                    f"/EXAVMIMAGES/GuestImages/{_vmName}/console/write-qemu "
                    f"/EXAVMIMAGES/console/{_serialId}/write-qemu")
            node_exec_cmd(_tgtNode, _cmd, log_warning=True)

            # Verify the client & backup bridges exist
            _bridges = get_node_bridges(_tgtNode)
            _list = []
            if _oldClientVlan:
                _list.append(_oldClientVlan)
            if _oldBackupVlan:
                _list.append(_oldBackupVlan)
            for _vlan in _list:
                if f"vmbondeth0.{_vlan}" not in _bridges:
                    _cmd = f"{VM_MAKER} --add-bonded-bridge vmbondeth0 --first-slave eth1 --second-slave eth2 --vlan {_vlan} --bond-mode active-backup"
                    node_exec_cmd_check(_tgtNode, _cmd)

            # Verify the client & backup bridges are up and running
            _cmd = f"/sbin/ifup bondeth0.{_oldClientVlan}"
            node_exec_cmd_check(_tgtNode, _cmd)
            if _oldBackupVlan:
                _cmd = f"/sbin/ifup bondeth0.{_oldBackupVlan}"
                node_exec_cmd_check(_tgtNode, _cmd)
            _cmd = f"/sbin/ifup vmbondeth0.{_oldClientVlan}"
            node_exec_cmd_check(_tgtNode, _cmd)
            if _oldBackupVlan:
                _cmd = f"/sbin/ifup vmbondeth0.{_oldBackupVlan}"
                node_exec_cmd_check(_tgtNode, _cmd)

            # Copy VM maker XML from GuestImages to /EXAVMIMAGES/conf
            _srcXml = f"{GUEST_IMAGES}/{_vmName}/{_vmName}.xml"
            _dstXml = f"/EXAVMIMAGES/conf/{_vmName}-vm.xml"
            _cmd = f"/bin/cp -f {_srcXml} {_dstXml}"
            ebLogInfo(f"Copying VM maker XML {_srcXml} => {_dstXml}")
            node_exec_cmd(_tgtNode, _cmd, log_warning=True)


        # Make sure the target Dom0 has the updated firewall rules
        _hasNFTables: bool = False
        with connect_to_host(_tgtDom0, get_gcontext()) as _tgtNode:
            _hasNFTables = _tgtNode.mFileExists('/etc/nftables/exadata.nft')
            _, _out, _ = node_exec_cmd(_tgtNode, f"/usr/sbin/nft add table ip filter")
            _, _out, _ = node_exec_cmd(_tgtNode, f"/usr/sbin/nft add table bridge filter")

            _, _out, _ = node_exec_cmd(_tgtNode, f"ls /EXAVMIMAGES/GuestImages/{_vmName}/snapshots/*u01*xml")                                             
            #  If snapshot of u01 is present then attach it to the VM in the new dom0 as well                                                    
            if _out:                                
                _dev = _out.split('/')[-1].split('.')[0]                                                                                        
                ebLogInfo(f"Create logical volume for {_dev}")
                                                    
                _json = {"storageType": "EXASCALE", "snapshot_device_name": _dev, "dom0": _tgtDom0, "vm": _vmName}                               
                self.mMountVolume(aOptions, _json, aLive=False)                                                                                  
                                                    
            _, _out, _ = node_exec_cmd(_tgtNode, f"ls /EXAVMIMAGES/GuestImages/{_vmName}/snapshots/*u02*xml")                                              
            # If snapshot of u02 is present then attach it to the VM in the new dom0 as well.                                                    
            if _out:                                
                _dev = _out.split('/')[-1].split('.')[0]                                                                                         
                ebLogInfo(f"Create logical volume for {_dev}")
                                                    
                _json = {"storageType": "EXASCALE", "snapshot_device_name": _dev, "dom0": _tgtDom0, "vm": _vmName}                               
                self.mMountVolume(aOptions, _json, aLive=False)                                                                                  

        if _hasNFTables:
            self.__ebox.mSetupNatNfTablesOnDom0v2(aDom0s=[_tgtDom0])
            ebIpTablesRoCE.mSetNfTablesExaBM(self.__ebox, aDom0s=[_tgtDom0])
            if 'cluster_status' in aOptions.jsonconf and aOptions.jsonconf['cluster_status'] != 'SUSPENDED':
                with connect_to_host(_tgtDom0, get_gcontext()) as _tgtNode:
                    start_domu(_tgtNode, _vmName, wait_for_connectable=False)

                try:
                    _consoleobj = serialConsole(self.mGetCluCtrl(), aOptions)
                    _consoleobj.mRunContainer(_tgtDom0, _vmName)
                    _consoleobj.mRestartContainer(_tgtDom0, _vmName, aMode="start")
                except Exception as e:
                    _detail_error = f'Failed to start serial console connection: "{e}"'
                    ebLogWarn(_detail_error)
            return # below code will take care of IPTables
        
        self.__ebox.mSetupNATIptablesOnDom0v2(aDom0s=[_tgtDom0])

        # Move the dynamic iptables
        _clientBridge, _backupBridge = cluctrlGetDom0Bridges(self.__ebox, _vmName)
        if _clientBridge and _backupBridge:
            _bridgesTypesMap = {
                _clientBridge: "client",
                _backupBridge: "backup"
            }   
        elif _backupBridge is None:
            _bridgesTypesMap = {
                _clientBridge: "client"
            }

        _domuXmlSchemasDict = ebIpTablesRoCE.mGetKVMSchemaFromDom0(
            _tgtDom0, _vmName)
        _interfacesAlias = ebIpTablesRoCE._mGetInterfacesAlias(
            _domuXmlSchemasDict["local"], _bridgesTypesMap)

        for _ifType, _ifAlias in _interfacesAlias.items():
            _environment = "exabm"
            _netFilterName = "-".join([_vmName, _ifAlias, _environment])

            ebLogInfo("*** Getting network filter:{0} schema ***"\
                .format(_netFilterName))
            _nwfilterXmlSchemasDict = ebIpTablesRoCE.mGetKVMSchemaFromDom0(
                _srcDom0, _netFilterName, aSchemaType="nwfilter")

            ebLogInfo("*** Defining kvm resource on dom0:{0}".format(_tgtDom0))
            ebIpTablesRoCE.mDefineKVMResourceInDom0(
                _tgtDom0, _nwfilterXmlSchemasDict["local"],
                _nwfilterXmlSchemasDict["remote"], aSchemaType="nwfilter")

            ebIpTablesRoCE.mAddNetFilterToVMSchema(
                _domuXmlSchemasDict["local"], _ifAlias, _netFilterName)

            try:
                ebIpTablesRoCE.mRemoveNetFilter(_srcDom0, _netFilterName)
            except ExacloudRuntimeError:
                ebLogError("*** Unable to undefine existing network filter:"
                           "{0}. Process will continue ***"\
                            .format(_netFilterName))

        ebLogInfo("*** Applying network filter changes to domU schema ***")
        ebIpTablesRoCE.mDefineKVMResourceInDom0(_tgtDom0,
            _domuXmlSchemasDict["local"], _domuXmlSchemasDict["remote"])

        ebLogInfo("*** Rebooting machine via vm_maker reboot to apply schema "
                  "changes ***")
        with connect_to_host(_tgtDom0, get_gcontext()) as _tgtNode:
            shutdown_domu(_tgtNode, _vmName)
            _cmd = f"{VM_MAKER} --start-domain {_vmName}"
            node_exec_cmd_check(_tgtNode, _cmd)

            try:
                _consoleobj = serialConsole(self.mGetCluCtrl(), aOptions)
                _consoleobj.mRunContainer(_tgtDom0, _vmName)
                _consoleobj.mRestartContainer(_tgtDom0, _vmName, aMode="start")
            except Exception as e:
                _detail_error = f'Failed to start serial console connection: "{e}"'
                ebLogWarn(_detail_error)

    def mReturnListEdvDevicePath(self, aDom0, aVMName) -> list:
        """
        Return a List where values are the device path
        e.g,
        [root@zrh101109exdd016 ~]# vm_maker --list --disk --domain b35-chdhi.sub11141713370.arsvpublicvpnzr.oraclevcn.com
        Block /dev/exc/system_Vmyajmn_1_863a
        Block /dev/exc/dbvolume-data-2n2P_Vmyajmn_1
        Block /dev/exc/dbvolume-reco-AdH1_Vmyajmn_1
        Block /dev/exc/dbvolume-sw-afuA_Vmyajmn_1

        Returns:
        ['/dev/exc/system_Vmyajmn_1_863a','/dev/exc/dbvolume-data-2n2P_Vmyajmn_1','/dev/exc/dbvolume-reco-AdH1_Vmyajmn_1','/dev/exc/dbvolume-test19c-kyxvia-givol_Vmxrvde_1','/dev/exc/dbvolume-sw-afuA_Vmyajmn_1']
        """

        _list_edv_device_path = []
        with connect_to_host(aDom0, get_gcontext()) as _node:
            _cmd = f"{VM_MAKER} --list --disk --domain {aVMName}"
            _vmDisks = node_exec_cmd_check(_node, _cmd).stdout.strip().splitlines()
            for _vmDisk in _vmDisks:
                parts = _vmDisk.split(None, 1)  # Split into Block and devicepath
                # Skipping u02 volume, as u02 volume is created by exacloud and not added in the xml -> Bug 38180182
                if (len(parts) == 2) and "/dev/exc/u02_" not in parts[1]:
                    _list_edv_device_path.append(parts[1]) # Add the devicepath in the list

        return _list_edv_device_path

    def mPerformValidateVolumesCheck(self, aDom0, aDomU, aEdvVolumeList=[]):
        """
        Verify that the volumes attached to the vm are same both in the xml and in the host
        """

        def mListMissingEdvDevicePath(aXmlEdvDevicePathList, aAttachedEdvDevicePathList):

            _missing_edv_device_path = []

            for _item in aXmlEdvDevicePathList:
                if _item not in aAttachedEdvDevicePathList:
                    _missing_edv_device_path.append(_item)

            return _missing_edv_device_path

        def mBuildResponse(attached_vols, unattached_vols=[], stale_vols=[]):
            
            response = {"volumes": []}

            # Add attached
            for vol in attached_vols:
                volname = os.path.basename(vol) 
                response["volumes"].append({"volumename": volname, "status": "attached"})

            # Add unattached
            for vol in unattached_vols:
                volname = os.path.basename(vol) 
                response["volumes"].append({"volumename": volname, "status": "unattached"})

            # Add stale
            for vol in stale_vols:
                volname = os.path.basename(vol) 
                response["volumes"].append({"volumename": volname, "status": "stale"})

            ebLogTrace(f"response: {response}") 

            return response

        _dom0 = aDom0
        _domU = aDomU
        _response = {"volumes": []}
        _edvVolume_list = aEdvVolumeList
        _list = []
        if _edvVolume_list:
            for i in range(len(_edvVolume_list)):
                _list.append("/dev/exc/" + _edvVolume_list[i])

        _xml_edv_device_path_list = self.mGetEdvDevicePath(_domU)
        _attached_edv_device_path_list = self.mReturnListEdvDevicePath(_dom0, _domU)

        if _list and _xml_edv_device_path_list and (set(_list).issubset(set(_xml_edv_device_path_list))) and (set(_list).issubset(set(_attached_edv_device_path_list))):
            ebLogInfo(f"Validate Volumes PostCheck is Successful. {_list} block devices is attached to the DomU: {_domU}")
            _response = mBuildResponse(_list)
            return 0, _response

        elif _list and _xml_edv_device_path_list:
            _msg = f"Validate Volumes PostCheck has Failed. {list(set(_list) - set(_attached_edv_device_path_list))} block devices is not attached to the DomU: {_domU}. The block device that are attached as per xml are: {_xml_edv_device_path_list} " \
                f"and the block device attached to the DomU: {_domU} are Block device: {_attached_edv_device_path_list}"
            ebLogWarn(_msg)

            _response = mBuildResponse(list(set(_list) & set(_attached_edv_device_path_list)), unattached_vols= list(set(_list) - set(_attached_edv_device_path_list)))
            return -1, _response


        if _xml_edv_device_path_list and (sorted(_xml_edv_device_path_list) == sorted(_attached_edv_device_path_list)):
            ebLogInfo(f"Validate Volumes PostCheck is Successful. All the block devices are attached to the DomU: {_domU} and the block devices are {_attached_edv_device_path_list}")
            _response = mBuildResponse(_attached_edv_device_path_list)
            return 0, _response
        else:
            _missing_edv_device_path_list_in_dom0 = mListMissingEdvDevicePath(_xml_edv_device_path_list, _attached_edv_device_path_list)
            _msg = f"Validate Volumes PostCheck has Failed. The block device that are attached as per xml are: {_xml_edv_device_path_list} and the block device attached " \
                f"to the DomU: {_domU} are Block device: {_attached_edv_device_path_list}. The block device that are not attached to the DomU: {_domU} is {_missing_edv_device_path_list_in_dom0}"
            ebLogWarn(_msg)

            _response = mBuildResponse(_attached_edv_device_path_list, unattached_vols= _missing_edv_device_path_list_in_dom0)
            return -1, _response

    def mPerformVmMoveSanityChecksExacloud(self, aOptions):
        """Sanity Checks for VM Move.

        Before we attempt to perform VM move, the following Sanity Checks
        should be run to increase the probabilities of the VM move to succeed.

        The current Sanity Checks that will be performed will be:
         - Verify that the source and target nodes have enough free size

        :param aOptions: Exacloud options object.
        """

        # Validate input payload
        _payloadFields: Sequence[str] = \
            ('vm_name', 'target_dom0_name', 'source_dom0_name')
        for _field in _payloadFields:
            if _field not in aOptions.jsonconf:
                raise ExacloudRuntimeError(
                    0x0811, 0xA, f'Missing "{_field}" in ExaScale Payload')

        _vmName = aOptions.jsonconf["vm_name"]
        _tgtDom0 = aOptions.jsonconf["target_dom0_name"]
        _srcDom0 = aOptions.jsonconf["source_dom0_name"]

        _vmMakerXmlPath: str = f"/EXAVMIMAGES/conf/{_vmName}-vm.xml"
        _tgtCurrentImgs: Set[str] = {}
        _tgtFreeSizeBytes: int = 0

        with connect_to_host(_tgtDom0, get_gcontext()) as _tgtNode:

            # Get the binaries paths needed from the target Dom0
            LS: str = node_cmd_abs_path_check(_tgtNode, 'ls')

            # Get the current set of images
            _, _out, _ = node_exec_cmd(_tgtNode, f"{LS} /EXAVMIMAGES/*.zip")
            _tgtCurrentImgs = set(_out.splitlines())

            # Get the free space in the target Dom0
            _fs, *_ = [ fs for fs in get_node_filesystems(_tgtNode)
                       if fs.mountpoint == '/EXAVMIMAGES' ]

            _tgtFreeSizeBytes = _fs.free_bytes

        # Operations in the source node
        with connect_to_host(_srcDom0, get_gcontext()) as _srcNode:

            # Get the binaries paths needed from the source Dom0
            LS: str = node_cmd_abs_path_check(_srcNode, 'ls')

            # Steal the VM Maker XML that was used for creating this VM
            _vmMakerXml = node_read_text_file(_srcNode, _vmMakerXmlPath)

            # Get the VM disk images that we're going compress and copy
            _imagesPath: str = os.path.join(GUEST_IMAGES, _vmName, '*.img')
            _, _out, _ = node_exec_cmd_check(_srcNode, f"{LS} {_imagesPath}")
            _diskImages: List[str] = _out.splitlines()

            # Check the images in the node and check if we need to copy some
            # dependencies
            _imgDep: Set[str] = { _dep.split('>')[1].split('<')[0]
                for _dep in _vmMakerXml.splitlines()
                if 'domuVolume' in _dep and 'EXAVMIMAGES' in _dep } - \
                _tgtCurrentImgs

            # Get the free space in the source Dom0
            _fs, *_ = [ fs for fs in get_node_filesystems(_srcNode)
                       if fs.mountpoint == '/EXAVMIMAGES' ]

            _srcFreeSizeBytes: int = _fs.free_bytes

            # Check if this node is capable to hold the compressed images
            # We will consider the worst case where the compression rate is 0%
            _totalImagesSizeBytes: int = 0
            for _diskImage in _diskImages:
                _imgInfo = _srcNode.mGetFileInfo(_diskImage)
                _totalImagesSizeBytes += _imgInfo.st_size

            if _totalImagesSizeBytes >= _srcFreeSizeBytes:
                _msg = (f"Source Dom0 {_srcDom0} can't hold the compressed "
                        f"DomU disk images. We need {_totalImagesSizeBytes} "
                        f"bytes but only {_srcFreeSizeBytes} bytes are"
                        "available.")
                raise ExacloudRuntimeError(0x0811, 0xA, _msg)

            ebLogInfo(f"*** Source Dom0 {_srcDom0} has {_srcFreeSizeBytes} "
                      f"free bytes, needed {_totalImagesSizeBytes} bytes to "
                      f"compress the DomU {_vmName} disk images files. OK!")

            # Check if the target Dom0 can hold the source DomU disk images
            # and the dependency images files
            _totalImgDepSizeBytes: int = 0
            for _img in _imgDep:
                _imgInfo = _srcNode.mGetFileInfo(_img)
                _totalImgDepSizeBytes += _imgInfo.st_size

            _totalRequiredBytes: int = \
                _totalImagesSizeBytes + _totalImgDepSizeBytes
            if _totalRequiredBytes >= _tgtFreeSizeBytes:
                _msg = (f"Target Dom0 {_tgtDom0} does not have enough space "
                        f"We need {_totalRequiredBytes} bytes but only "
                        f"{_srcFreeSizeBytes} bytes are available.")
                raise ExacloudRuntimeError(0x0811, 0xA, _msg)

            ebLogInfo(f"*** Target Dom0 {_tgtDom0} has {_tgtFreeSizeBytes} "
                      f"free bytes, needed {_totalRequiredBytes} bytes to "
                      f"copy the DomU {_vmName} disk images files and their "
                      "recreation dependencies. OK!")


    def mPerformVmMoveSanityChecksOEDA(self, aOptions, aExascaleOpts):
        """Performs the VM move precheks from the VM move spec.
        https://confluence.oraclecorp.com/confluence/display/EDCS/ExaCompute+-+ExaDB-XS+and+VM+Move#ExaComputeExaDBXSandVMMove-VMMoveSanityCheck

        These include the following checks on the target host:
        - Node is reachable (ping)
        - QinQ is enabled
        - Hypervisor is enabled
        - VM is not registered
        - EDV services are running
        - There are no stale NAT bridges
        - There are no stale VM files

        And these checks on the source host (if available):
        - EDV required files are still available
        """

        # Validate input payload
        _payloadFields: Sequence[str] = \
            ('vm_name', 'target_dom0_name', 'source_dom0_name')
        for _field in _payloadFields:
            if _field not in aOptions.jsonconf:
                self.fail(
                    "INVALID_PAYLOAD",
                    aCausePlaceholders={"missing_field": _field},
                    aSuggestionPlaceholders={"required_fields": _payloadFields}
                )

        _vmName = aOptions.jsonconf["vm_name"]
        _tgtDom0 = aOptions.jsonconf["target_dom0_name"]
        _srcDom0 = aOptions.jsonconf["source_dom0_name"]
        _newNATVLAN = aOptions.jsonconf.get("new_admin_vlan")
        _live = str(aOptions.jsonconf.get('mode')).lower() == 'live'

        ebLogInfo(f"PASSED: Input payload is correct... {aOptions.jsonconf}")

        # Validate target host is reachable
        if not self.mGetCluCtrl().mPingHost(_tgtDom0):
            self.fail(
                "TARGET_HOST_NOT_REACHABLE",
                aCausePlaceholders={"host": _tgtDom0},
                aSuggestionPlaceholders={"host": _tgtDom0}
            )

        with connect_to_host(_tgtDom0, get_gcontext()) as _tgtNode:
            ebLogInfo(f"PASSED: Target Dom0 {_tgtDom0} is reachable.")

            # Validate the host type is correct
            _validHostTypes = ("KVMHOST")
            try:
                _cmd = "/usr/local/bin/imageinfo --node-type"
                _tgtType = node_exec_cmd_check(_tgtNode, _cmd).stdout.strip()
            except:
                self.fail("INVALID_IMAGE", aCausePlaceholders={"host": _tgtDom0})

            if _tgtType not in _validHostTypes:
                self.fail(
                    "INVALID_NODE_TYPE",
                    aCausePlaceholders={"type": _tgtType, "host": _tgtDom0},
                    aSuggestionPlaceholders={"valid_types": _validHostTypes}
                )
            ebLogInfo(f'PASSED: Valid host type "{_tgtType}".')

            # Verify hypervisor services are running
            try:
                _cmd = "/bin/virsh list --all --name"
                _tgtVMs = set(node_exec_cmd_check(
                    _tgtNode, _cmd).stdout.strip().splitlines())
            except:
                self.fail("INVALID_HYPERVISOR", aCausePlaceholders={"host": _tgtDom0})
            ebLogInfo(f"PASSED: Currently registered VMs in Dom0: {_tgtVMs}")

            # Verify VM is not registered already
            if _vmName in _tgtVMs:
                self.fail(
                    "VM_ALREADY_MOVED",
                    aCausePlaceholders={"host": _tgtDom0, "vm": _vmName}
                )
            ebLogInfo(f"PASSED: VM {_vmName} is not registered in target Dom0.")

            # Verify EDV services are running
            _cmd = "/sbin/edvutil lsedvnode | /bin/grep state"
            _EDVState = node_exec_cmd_check(
                _tgtNode, _cmd).stdout.split(':', 1)[1].strip()
            if _EDVState != 'ONLINE':
                self.fail(
                    "EDV_SERVICES_OFFLINE",
                    aCausePlaceholders={"host": _tgtDom0}
                )
            ebLogInfo("PASSED: EDV services are online in Dom0.")

            # Verify there are no stale VM files
            _cmd = "/bin/ls /EXAVMIMAGES/GuestImages"
            _VMFiles = set(node_exec_cmd_check(_tgtNode, _cmd).stdout.split())
            if _tgtVMs != _VMFiles:

                for _staleVm in _VMFiles - _tgtVMs:

                    _cmd = f"/bin/ls /EXAVMIMAGES/GuestImages/{_staleVm}/vm*.xml"
                    _ret = node_exec_cmd(_tgtNode, _cmd).exit_code
                    if _ret == 0:
                        self.fail(
                            "STALE_VM_FILES",
                            aCausePlaceholders={
                                "host": _tgtDom0,
                                "stale_vm_files": _VMFiles - _tgtVMs
                            }
                        )
                    else:
                        ebLogInfo(f"Found stale vm in GuestImages but not XML present: {_staleVm}")
                        ebLogInfo(f"Dumping all the files before cleanup")
                        _tgtNode.mExecuteCmdLog(f"/bin/ls -lthr /EXAVMIMAGES/GuestImages/{_staleVm}/")
                        ebLogInfo(f"Perfoming cleanup")
                        _tgtNode.mExecuteCmdLog(f"/bin/rm -rf /EXAVMIMAGES/GuestImages/{_staleVm}")

            ebLogInfo("PASSED: No stale VM files in Dom0.")

            # Verify there are no corrupted GCV EDVs mounted
            for _vm in _tgtVMs:
                try:
                    _cmd = f"/bin/ls /EXAVMIMAGES/GuestImages/{_vm}/vm*.xml"
                    node_exec_cmd_check(_tgtNode, _cmd)
                except:
                    ebLogError(f"Broken EDV for {_vm}")
                    """
                    self.fail(
                        "BROKEN_EDV",
                        aCausePlaceholders={"host": _tgtDom0, "vm": _vm},
                        aSuggestionPlaceholders={"vm": _vm}
                    )
                    """
            ebLogInfo("PASSED: All GCV EDVs mounted look healthy.")

            # Verify there is no volume descriptor for the VM GCV EDV
            _tgtGCV = self.mGetGcvDevicePath(aOptions)
            if not _tgtGCV:
                self.fail("INVALID_XML", aCausePlaceholders={"vm": _vmName})

            if self.mGetCluCtrl().mPingHost(_srcDom0):
                _tgtGCVPath = f"/dev/exc/{_tgtGCV}"
                _cmd = f"/bin/ls {_tgtGCVPath}"
                _ret = node_exec_cmd(_tgtNode, _cmd).exit_code
                if _ret == 0:
                    self.fail(
                        "STALE_EDV",
                        aCausePlaceholders={"host": _tgtDom0, "edv": _tgtGCVPath},
                        aSuggestionPlaceholders={"edv": _tgtGCVPath}
                    )
                ebLogInfo(f"PASSED: GCV EDV {_tgtGCVPath} is not present "
                          "in target Dom0.")
            else:
                ebLogInfo(f"SKIPPED: Source Dom0 {_srcDom0} is not available. "
                          "GCV EDV will not be checked.")

            # Verify there are no stale bridges
            if _tgtVMs:
                _, _, _VMPreNATs, _VMPostNATs = map(set, zip(*map(
                    lambda _vm: get_kvm_guest_bridges(_tgtNode, _vm), _tgtVMs)))
            else:
                _VMPreNATs, _VMPostNATs = (set(), set())

            _tgtBridges = { _bridge.name
                for _bridge in get_node_bridges(_tgtNode) }
            _tgtPreNATs = set(filter(
                lambda _bridge: _bridge.startswith('vmeth0'), _tgtBridges))
            _tgtPostNATs = set(filter(
                lambda _bridge: _bridge.startswith('vmeth2') or \
                                _bridge.startswith('vmeth3'), _tgtBridges))
            _stalePreNATs = _tgtPreNATs - _VMPreNATs - {'vmeth0'}
            _stalePostNATs = _tgtPostNATs - _VMPostNATs
            if _stalePreNATs or _stalePostNATs:

                ebLogTrace(f"Found stale bridges: {_stalePreNATs | _stalePostNATs}")

                # Manually delete all bridges
                _lock = RemoteLock(self.__ebox, force_host_list=[_tgtNode])

                try:
                    _lock.acquire()

                    for _staleBridge in _stalePreNATs | _stalePostNATs:
                        ebLogTrace(f"Removing stale bridge: {_staleBridge}")
                        node_exec_cmd_check(_tgtNode, f"/usr/sbin/ip link set {_staleBridge} down")
                        node_exec_cmd_check(_tgtNode, f"/usr/sbin/brctl delbr {_staleBridge}")
                        node_exec_cmd_check(_tgtNode, f"/bin/rm /etc/sysconfig/network-scripts/*{_staleBridge}")

                finally:
                    _lock.release()

                # Fetch again the bridges info
                if _tgtVMs:
                    _, _, _VMPreNATs, _VMPostNATs = map(set, zip(*map(
                        lambda _vm: get_kvm_guest_bridges(_tgtNode, _vm), _tgtVMs)))
                else:
                    _VMPreNATs, _VMPostNATs = (set(), set())

                _tgtBridges = { _bridge.name
                    for _bridge in get_node_bridges(_tgtNode) }
                _tgtPreNATs = set(filter(
                    lambda _bridge: _bridge.startswith('vmeth0'), _tgtBridges))
                _tgtPostNATs = set(filter(
                    lambda _bridge: _bridge.startswith('vmeth2') or \
                                    _bridge.startswith('vmeth3'), _tgtBridges))
                _stalePreNATs = _tgtPreNATs - _VMPreNATs - {'vmeth0'}
                _stalePostNATs = _tgtPostNATs - _VMPostNATs

                if _stalePreNATs or _stalePostNATs:
                    self.fail(
                        "STALE_BRIDGES",
                        aCausePlaceholders={
                            "host": _tgtDom0,
                            "stale_bridges": _stalePreNATs | _stalePostNATs
                        }
                    )

            ebLogInfo("PASSED: No stale bridges in Dom0. "
                      f"Current bridges: {_tgtBridges}")

            # Verify target node has bondmonitor installed
            if get_bond_monitor_installed(_tgtNode) is None:
                self.fail(
                    "BONDING_NOT_SETUP",
                    aCausePlaceholders={"host": _tgtDom0}
                )
            ebLogInfo(f"PASSED: Bonding is setup in {_tgtDom0}")

        # Live migration prechecks
        if _live:
            with connect_to_host(_srcDom0, get_gcontext()) as _srcNode:
                with connect_to_host(_tgtDom0, get_gcontext()) as _tgtNode:

                    _filename = f"/tmp/{self.mGetCluCtrl().mGetUUID()}"

                    try:
                        _cmd = f"{VM_MAKER} --precheck-live-migrate-domain > {_filename}"
                        node_exec_cmd_check(_tgtNode, _cmd, log_stdout_on_error=True)

                        _tgtNode.mCopy2Local(_filename, _filename)
                        _srcNode.mCopyFile(_filename, _filename)

                        _cmd = f"{VM_MAKER} --precheck-live-migrate-domain --source {_vmName} --destination-profile {_filename}"
                        node_exec_cmd_check(_srcNode, _cmd, log_stdout_on_error=True)

                    except:
                        self.fail(
                            "LIVE_PRECHECK",
                            aCausePlaceholders={"vm": _vmName, "host": _srcDom0},
                            aSuggestionPlaceholders={"vm": _vmName, "host": _srcDom0}
                        )

                    finally:
                        _cmd = f"/bin/rm -f {_filename}"
                        self.mGetCluCtrl().mExecuteLocal(_cmd)
                        node_exec_cmd(_tgtNode, _cmd)
                        node_exec_cmd(_srcNode, _cmd)


        # Pre-checks on the source host (if available)
        if not self.mGetCluCtrl().mPingHost(_srcDom0):
            ebLogWarn(f"Source Dom0 {_srcDom0} not available. "
                      "Skipping VM move pre-checks on source Dom0...")
            return
        with connect_to_host(_srcDom0, get_gcontext()) as _srcNode:
            
            # Verify the GCV EDV is not broken for this VM
            _clientBridge, _backupBridge, _, _ = \
                get_kvm_guest_bridges(_srcNode, _vmName)
            try:
                _cmd = (f"/bin/ls /EXAVMIMAGES/GuestImages/{_vmName}/"
                        f"{_clientBridge}.xml")
                node_exec_cmd_check(_srcNode, _cmd)
                if _backupBridge:
                    _cmd = (f"/bin/ls /EXAVMIMAGES/GuestImages/{_vmName}/"
                            f"{_backupBridge}.xml")
                    node_exec_cmd_check(_srcNode, _cmd)
                _cmd = (f"/bin/ls /EXAVMIMAGES/GuestImages/{_vmName}/"
                        f"{_vmName}.xml")
                node_exec_cmd_check(_srcNode, _cmd)
                _cmd = (f"/bin/ls /EXAVMIMAGES/GuestImages/{_vmName}/"
                        f"vmeth*.xml")
                node_exec_cmd_check(_srcNode, _cmd)
            except:
                self.fail(
                    "BROKEN_GCV",
                    aCausePlaceholders={"vm": _vmName, "host": _srcDom0},
                    aSuggestionPlaceholders={"vm": _vmName, "host": _srcDom0}
                )
            ebLogInfo(f"PASSED: VM XMLs present in GCV EDV")



    def mVolAttach(self, aOptions, aUndo=False):

        if aUndo:
            _logfile = 'oedacli_exascale_voldetach.log'
        else:
            _logfile = 'oedacli_exascale_volattach.log'
        _oedacli_bin = os.path.join(self.__ebox.mGetOedaPath(), 'oedacli')
        _oedacli = ebOedacli(_oedacli_bin, os.path.join(self.__ebox.mGetOedaPath(), "log"), aLogFile=_logfile)
        _oedacli.mSetAutoSaveActions(True)
        _oedacli.mSetDeploy(True)
        _dom0_list = []

        # Declare command to use
        _vols = aOptions.jsonconf["volumes"]
        for _volinfo in _vols:
            _hostvol = f'/dev/exc/{_volinfo["volumedevicepath"]}'
            _volname = _volinfo["volumedevicepath"]
            _guestvol = _volinfo["guestdevicename"]
            _dom0 = _volinfo["dom0"]
            _vm = _volinfo["vm"]
            _dom0_list.append(_dom0)

            _cmd = (f"ADD EDVVOLUME DEVICE={_hostvol} SERIAL={_guestvol} WHERE HOSTNAME={_vm}")
            if aUndo:
                _cmd = (f"ALTER MACHINE ACTION=DETACHVOLUME VOLNAME={_volname} WHERE HOSTNAME={_vm} STEPNAME=DETACH_VOLUME")

            # Append command to ebOedacli object
            _oedacli.mAppendCommand(_cmd)

            _cmd = (f"ALTER MACHINE ACTION=ATTACHVOLUME VOLNAME={_volname} SERIAL={_guestvol} WHERE HOSTNAME={_vm} STEPNAME=ATTACH_VOLUME")
            if aUndo:
                _cmd = (f"DELETE EDVVOLUME WHERE VOLUMENAME={_volname} HOSTNAME={_vm}")

            # Append command to ebOedacli object
            _oedacli.mAppendCommand(_cmd)

        # Prepare KMS SSH keys for OEDA
        self.__ebox.mRestoreOEDASSHKeys(self.__ebox.mGetOptions(), aForce=True)

        _xml = self.__ebox.mGetPatchConfig()
        _xmlbackup = f"{_xml}_bk"
        self.__ebox.mExecuteLocal(f"cp -f {_xml} {_xmlbackup}")
        _cmdout = _oedacli.mRun(_xmlbackup, _xml)
        ebLogInfo(_cmdout)

        ebLogInfo('ebCluCtrl: Saved patched Cluster Config: ' + _xml)
        _db = ebGetDefaultDB()
        _db.import_file(_xml)
        
    def mVolResize(self, aOptions):

        if not self.__ebox.mCheckConfigOption("exadbxs_19c_invoke_oedacli", "True"):
            _vols = aOptions.jsonconf["volumes"]
            for _volinfo in _vols:
                _hostvol = f'/dev/exc/{_volinfo["volumedevicepath"]}'
                _size = _volinfo["volumesizegb"]
                _dom0 = _volinfo["dom0"]
                _vm = _volinfo["vm"]

                with connect_to_host(_dom0, get_gcontext()) as _node:
                    _, _o, _ = _node.mExecuteCmd(f"virsh blockresize {_vm} {_hostvol} {_size}G")                                                         

        else:
            # OEDA implementation.

            _oedacli_bin = os.path.join(self.__ebox.mGetOedaPath(), 'oedacli')
            _oedacli = ebOedacli(_oedacli_bin, os.path.join(self.__ebox.mGetOedaPath(), "log"), aLogFile="oedacli_exascale_volresize.log")
            _oedacli.mSetAutoSaveActions(True)
            _oedacli.mSetDeploy(True)

            _dom0_list = []
            # Declare command to use
            _vols = aOptions.jsonconf["volumes"]
            for _volinfo in _vols:
                _hostvol = f'/dev/exc/{_volinfo["volumedevicepath"]}'
                _volname = _volinfo["volumedevicepath"] 
                _size = _volinfo["volumesizegb"]
                _dom0 = _volinfo["dom0"]
                _vm = _volinfo["vm"]
                _dom0_list.append(_dom0)

                _cmd = (f"ALTER EDVVOLUME VOLUMESIZE={_size} WHERE HOSTNAME={_vm} VOLUMENAME={_volname}")
                
                _oedacli.mAppendCommand(_cmd)

                _cmd = (f"RESIZE EDVVOLUME DEVICE={_hostvol} WHERE HOSTNAME={_vm}") 

                # Append command to ebOedacli object
                _oedacli.mAppendCommand(_cmd)

            # Prepare KMS SSH keys for OEDA
            self.__ebox.mRestoreOEDASSHKeys(self.__ebox.mGetOptions(), aForce=True)

            # Run command
            _xml = self.__ebox.mGetPatchConfig()
            _xmlbackup = f"{_xml}_bk"
            self.__ebox.mExecuteLocal(f"cp -f {_xml} {_xmlbackup}")
            _cmdout = _oedacli.mRun(_xmlbackup, _xml)
            ebLogInfo(_cmdout)

            ebLogInfo('ebCluCtrl: Saved patched Cluster Config with new vol info: ' + _xml)
            _db = ebGetDefaultDB()
            _db.import_file(_xml)

    def mCloneSourceInXml(self, aXmlTree, aSourceName, aTargetName, aOptions):

        _prepareArgs = {
            "source_nodes": [],
            "source_name": aSourceName,
            "target_name": aTargetName,
            "target_found": False
        }

        aXmlTree.mBFS(aStuffCallback=mPrepareForClone, aStuffArgs=_prepareArgs)

        # Clone every source node into target
        if not _prepareArgs["target_found"]:

            for _node in _prepareArgs["source_nodes"]:

                _tmpXmlTree = ebTree()
                _tmpXmlTree.mSetRoot(_node)
                _tmpXmlTree = _tmpXmlTree.mCopy()

                _replaceArgs = {
                    "past_dom0_fqdn": aSourceName,
                    "past_dom0_host": aSourceName.split(".")[0],
                    "past_dom0_ip": socket.gethostbyname(aSourceName),
                    "new_dom0_fqdn": aTargetName,
                    "new_dom0_host": aTargetName.split(".")[0],
                    "new_dom0_ip": socket.gethostbyname(aTargetName)
                }

                _tmpXmlTree.mBFS(aStuffCallback=mReplaceDom0sFx, aStuffArgs=_replaceArgs)
                _node.mGetParent().mAppendChild(_tmpXmlTree.mGetRoot())

        self.mGetCluCtrl().mParseXMLConfig(aOptions)



    def mDettachGuestMachineFromHostXML(self, aHostname):

        def mSearchHostandRemoveGuest(aNode, aArgs):
            if aNode.mGetSortElement() != "hostName" or \
               aNode.mGetElement()["text"] != aHostname:
                return

            for _children in aNode.mGetParent().mGetChildren():
                if _children.mGetSortElement() == "machine":
                    _children.mRemove()

        _xmlTree = ebTree(self.__ebox.mGetPatchConfig())
        _xmlTree.mBFS(aStuffCallback=mSearchHostandRemoveGuest, aStuffArgs={})
        _xmlTree.mExportXml(self.__ebox.mGetPatchConfig())



    def mUmountVolumesVmMove(self, aDom0, aVMName, aNetInfo, aStrict=True):

        ebLogInfo("Removing serial console container for the VM from source dom0")
        # Remove VM serial console containers from src dom0
        _consoleobj = serialConsole(self.mGetCluCtrl(), self.mGetCluCtrl().mGetOptions())
        _consoleobj.mStopContainer(aDom0, aVMName, aForce=True)
        _consoleobj.mRemoveContainer(aDom0, aVMName)

        mRemoveVMmount(self.__ebox, aDom0, aVMName, aStrict)

        # Update the Dom0-DomU pairs for NFTables cleanup.
        _newDom0sDomUs: List[List[str]] = [[aDom0, aVMName]]
        if self.__ebox.isBaseDB() or self.__ebox.isExacomputeVM():
            self.__ebox.mSetDomUsDom0s(aVMName, sorted(_newDom0sDomUs))
        else:
            _clusterId = self.__ebox.mGetClusters().mGetCluster().mGetCluId()
            self.__ebox.mSetDomUsDom0s(_clusterId, sorted(_newDom0sDomUs))
        get_gcontext().mSetRegEntry(f"_natHN_{aVMName}", aNetInfo["old_hostname"])
        ebIpTablesRoCE.mRemoveSecurityRulesExaBM(self.__ebox, aDom0s=[aDom0])

        ebLogInfo(f"mUmountVolumesVmMove complete in dom0: {aDom0} for vm: {aVMName}")


    def mGetGcvDevicePath(self, aOptions) -> str:         
        """        
        This function parses json args and returns the value of gcvDevicePath
        When gcvDevicePath is present, it is identified as EDV scenario.
        """
        _vmName = aOptions.jsonconf["vm_name"]
        
        # Extract gcvVolDevicePath
        _xmlTree = ebTree(self.__ebox.mGetPatchConfig())
        _args = {"vmName": _vmName}

        _xmlTree.mBFS(aStuffCallback=mSearchVolumesByVM, aStuffArgs=_args)
        _xmlTree.mBFS(aStuffCallback=mSearchGcvVolDevicePath, aStuffArgs=_args)
        
        if "gcvDevicePath" not in _args:
            return None            

        _gcvVolDevicePath = _args["gcvDevicePath"]
        return _gcvVolDevicePath

    def mGetEdvDevicePath(self, aVmName) -> str:
        """        
        This function parses json args and returns the value of edvDevicePath
        of all the volumes for the particular vm.
        """

        _vmName = aVmName
        
        # Extract edvDevicePath
        _xmlTree = ebTree(self.__ebox.mGetPatchConfig())
        _args = {"vmName": _vmName}

        _xmlTree.mBFS(aStuffCallback=mSearchVolumesByVM, aStuffArgs=_args)
        _xmlTree.mBFS(aStuffCallback=mSearchEdvDevicePath, aStuffArgs=_args)
        
        if "edvDevicePath" not in _args:
            return None            

        _edvVolDevicePath = _args["edvDevicePath"]
        return _edvVolDevicePath

    def mGetLVDev(self, aDom0, aDomU, aVol):

        _pv = None
        _lv = None
        _device = None
        with connect_to_host(aDom0, get_gcontext()) as _node:

            _file = f"/etc/libvirt/qemu/{aDomU}.xml" 
            _, _o, _ = _node.mExecuteCmd(f"grep VGExaDbDisk.{aVol} {_file}")                                                         
            if _node.mGetCmdExitStatus():
                return None, None 
            _entry = _o.readlines()[0]
            if _entry:
                _pattern = r"<source dev='(.*?)'"
                match = re.search(_pattern, _entry)
                if match:
                    _lv = match.group(1)
                    _vg = _lv.split('/')[2]
                    _, _out, _ = _node.mExecuteCmd(f"pvdisplay -c | grep {_vg}")
                    if _node.mGetCmdExitStatus() == 0:
                        _entry = _out.readlines()[0]
                        _pv = _entry.split(':')[0].split('/')[3]
                    
            if not _pv:
                return None, None

            _, _out, _ = _node.mExecuteCmd(f"ls /dev/exc/ | grep {aVol}")
            _entries = _out.readlines()
            for _entry in _entries:
                _entry = _entry.strip()
                _, _out, _ = _node.mExecuteCmd(f"kpartx -l /dev/exc/{_entry} | grep {_pv}")
                if _node.mGetCmdExitStatus() == 0:
                    _device = _entry
                    break

            ebLogInfo(f"_lv: {_lv}, _device: {_device}")
            return _lv, _device

    def mUnmountVolume(self, aOptions, aJson=None):

        if aJson:
            _json = aJson
        else:
            _json = aOptions.jsonconf

        # Validate input payload
        if "vm" not in _json:
            raise ExacloudRuntimeError(0x0811, 0xA, 'Missing vm name in ExaScale Payload')

        if "snapshot_device_name" not in _json:
            raise ExacloudRuntimeError(0x0811, 0xA, 'Missing snapshot device name in ExaScale Payload')

        if "lvm" not in _json:
            raise ExacloudRuntimeError(0x0811, 0xA, 'Missing lvm path in ExaScale Payload')

        if "dom0" not in _json:
            raise ExacloudRuntimeError(0x0811, 0xA, 'Missing dom0 name in ExaScale Payload')

        _vm = _json["vm"]
        _lv = _json["lvm"]
        # rw volume snapshot
        _dev = _json["snapshot_device_name"]
        _dom0 = _json["dom0"]
        _devpath = f"/dev/exc/{_dev}"

        if "system" in _dev:
            ebLogError("Mount and unmount of sys filesystem is not supported")
            # To be discussed if we should raise Exception
            return 1

        with connect_to_host(_dom0, get_gcontext()) as _node:

            _, _out, _ = node_exec_cmd_check(_node, "/usr/sbin/vgs")
            ebLogInfo(f"Executing vgs")
            _entries = _out.splitlines()
            for _entry in _entries:
                ebLogInfo(f"{_entry}")

            _, _out, _ = node_exec_cmd(_node, f"/usr/sbin/lvdisplay -c {_lv}")
            _entry = _out.splitlines()[-1]
            _vg = _entry.split(':')[1]

            ebLogInfo(f"Using volume group: {_vg} for logical volume: {_lv}")

            _, _out, _ = node_exec_cmd_check(_node, f"/usr/bin/virsh detach-disk {_vm} {_lv} --live --config")
            ebLogInfo(f"Executing virsh detach-disk {_vm} {_lv} --live --config")         
            _entries = _out.splitlines()    
            for _entry in _entries:         
                ebLogInfo(f"{_entry}")

            _, _out, _ = node_exec_cmd_check(_node, f"/usr/sbin/vgchange -an {_vg}")
            ebLogInfo(f"Executing vgchange -an {_vg}")         
            _entries = _out.splitlines()    
            for _entry in _entries:         
                ebLogInfo(f"{_entry}")

            _, _out, _ = node_exec_cmd_check(_node, f"/usr/sbin/kpartx -d {_devpath}")

            _, _out, _ = node_exec_cmd_check(_node, "/usr/sbin/vgs")
            ebLogInfo(f"Executing vgs")         
            _entries = _out.splitlines()    
            for _entry in _entries:         
                ebLogInfo(f"{_entry}")

            _, _out, _ = node_exec_cmd(_node, f"rm -f /EXAVMIMAGES/GuestImages/{_vm}/snapshots/{_dev}.xml")

            ebLogInfo(f"Unmount completed for {_dom0} : {_vm} : {_lv} : {_dev}")
        return 0

    def mMountVolume(self, aOptions, aJson=None, aLive=True):    
                                                    
        if aJson:                                   
            _json = aJson                           
        else:                                       
            _json = aOptions.jsonconf               
                                                    
        if aLive:                                   
            _live = "--live"                        
        else:                                       
            _live = ""                              
                                                    
        # Validate input payload                    
        if "vm" not in _json:                       
            raise ExacloudRuntimeError(0x0811, 0xA, 'Missing vm name in ExaScale Payload')                                                       
                                                    
        if "snapshot_device_name" not in _json:     
            raise ExacloudRuntimeError(0x0811, 0xA, 'Missing snapshot device name in ExaScale Payload')                                          
                                                    
        if "dom0" not in _json:                     
            raise ExacloudRuntimeError(0x0811, 0xA, 'Missing dom0 name in ExaScale Payload')                                                     
                                                    
        _vm = _json["vm"]                           
        # rw volume snapshot                        
        _dev = _json["snapshot_device_name"]        
        _dom0 = _json["dom0"]                       
        _devpath = f"/dev/exc/{_dev}"               

        if "system" in _dev:
            ebLogError("Mount and unmount of sys filesystem is not supported")
            # To be discussed if we should raise Exception
            return 1

        with connect_to_host(_dom0, get_gcontext()) as _node:

            _loopdevs = []
            _, _out, _ = node_exec_cmd_check(_node, f"/usr/sbin/kpartx -av {_devpath}")
            ebLogInfo(f"Executing kpartx -av {_devpath}")
            _entries = _out.splitlines()
            for _entry in _entries:
                ebLogInfo(f"{_entry}")
                _loopdevs.append(_entry.split(' ')[2])

            _, _out, _ = node_exec_cmd_check(_node, "ls -ltr /dev/mapper")
            ebLogInfo(f"Executing ls -ltr /dev/mapper")
            _entries = _out.splitlines()
            for _entry in _entries:
                ebLogInfo(f"{_entry}")

            _, _out, _ = node_exec_cmd_check(_node, "/usr/sbin/vgs")
            ebLogInfo(f"Executing vgs")
            _entries = _out.splitlines()
            for _entry in _entries:
                ebLogInfo(f"{_entry}")

            if "u02" in _dev:

                _loopdev = _loopdevs[0]
                _, _out, _ = node_exec_cmd_check(_node, f"/usr/sbin/pvscan --listvg /dev/mapper/{_loopdev}")
                _entries = _out.splitlines()
                ebLogInfo(f"pvscan: {_entries}")
                _vg = _entries[0].strip().split(' ')[-1]

                _vmshrt = _vm.split('.')[0]
                if _vmshrt not in _vg:
                    # u02 in _dev
                    _, _out, _ = node_exec_cmd(_node, f"/usr/sbin/vgrename {_vg} {_vg}_{_vmshrt}")
                    _entries = _out.splitlines()
                    ebLogInfo(f"vgrename: {_entries}")
                    _vg = f"{_vg}_{_vmshrt}"

                _, _out, _ = node_exec_cmd(_node, "modprobe dm-mod")
                _entries = _out.splitlines()
                ebLogInfo(f"modprobe: {_entries}")

                _, _out, _ = node_exec_cmd(_node, "vgchange -ay")
                _entries = _out.splitlines()
                ebLogInfo(f"vgchange: {_entries}")

                _, _out, _ = node_exec_cmd(_node, f"lvscan | grep {_vg}")
                _entries = _out.splitlines()
                ebLogInfo(f"lvscan: {_entries}")

                _, _out, _ = node_exec_cmd(_node, f"ls -ltr /dev/mapper/")
                _entries = _out.splitlines()
                ebLogInfo(f"ls of /dev/mapper: {_entries}")

                _, _out, _ = node_exec_cmd(_node, f"/usr/sbin/lvdisplay -c | grep {_vg}")
                ebLogInfo(f"Executing lvdisplay -c")
                _entry = _out.splitlines()[-1]
                _lv = _entry.split(':')[0].strip()

                _, _out, _ = node_exec_cmd(_node, f"/usr/sbin/tune2fs -l {_lv} | grep UUID")
                _entries = _out.splitlines()
                ebLogInfo(f"tune2fs -l: {_entries}")

                # force/full system check
                _, _out, _ = node_exec_cmd(_node, f"/usr/sbin/e2fsck -f -y {_lv}")
                _entries = _out.splitlines()
                ebLogInfo(f"e2fsck -f -y {_lv}: {_entries}")

                _, _out, _ = node_exec_cmd(_node, f"/usr/sbin/tune2fs -l {_lv} | grep UUID")
                _lvuuid = _out.splitlines()[0].split(':')[-1].strip()
                ebLogInfo(f"_lvuuid: {_lvuuid}")
                _updateuuid = False
                _, _out, _ = node_exec_cmd(_node, f"grep -oP '(?<=<!-- uuid=)[0-9a-fA-F-]+' /EXAVMIMAGES/GuestImages/{_vm}/snapshots/{_dev}.xml")
                if not _out:
                    _, _out, _ = node_exec_cmd_check(_node, "/usr/bin/uuidgen")
                    _uuid = _out.splitlines()[0]
                    _updateuuid = True

                elif _lvuuid != _out.splitlines()[0]:
                    _uuid = _out.splitlines()[0]
                    _updateuuid = True

                if _updateuuid:
                    node_exec_cmd(_node, f"mount {_lv} /mnt")
                    node_exec_cmd(_node, f"umount /mnt")
                    node_exec_cmd(_node, f"umount {_lv}")
                    node_exec_cmd(_node, f"/usr/sbin/e2fsck -f -y {_lv}")

                    node_exec_cmd_check(_node, f"yes | /usr/sbin/tune2fs -U {_uuid} {_lv}")


                _, _out, _ = node_exec_cmd(_node, f"/usr/sbin/tune2fs -l {_lv} | grep UUID")
                _entries = _out.splitlines()
                ebLogInfo(f"After uuid update, tune2fs -l: {_entries}")

                #_, _out, _ = node_exec_cmd_check(_node, f"file -sL {_lv}")
                #_entries = _out.splitlines()
                #ebLogInfo(f"file -sL: {_entries}")

                ebLogInfo(f"lv: {_lv}, volume group: {_vg}")

            else:
                # u01 or others

                _loopdev = _loopdevs[0]

                _, _out, _ = node_exec_cmd_check(_node, f"/usr/sbin/pvscan --listvg /dev/mapper/{_loopdev}")
                _entries = _out.splitlines()
                ebLogInfo(f"pvscan: {_entries}")
                _vg = _entries[0].strip().split(' ')[-1]

                _, _out, _ = node_exec_cmd_check(_node, f"/usr/sbin/lvdisplay -c | grep {_vg}")
                ebLogInfo(f"Executing lvdisplay -c")
                _entry = _out.splitlines()[-1]
                _lv = _entry.split(':')[0].strip()

                ebLogInfo(f"lv: {_lv}, volume group: {_vg}")

                _, _out, _ = node_exec_cmd(_node, f"/usr/sbin/xfs_admin -u {_lv}")
                _lvuuid = _out.splitlines()[0].split('=')[-1].strip()
                ebLogInfo(f"_lvuuid: {_lvuuid}")
                _updateuuid = False
                _, _out, _ = node_exec_cmd(_node, f"grep -oP '(?<=<!-- uuid=)[0-9a-fA-F-]+' /EXAVMIMAGES/GuestImages/{_vm}/snapshots/{_dev}.xml")
                if not _out:
                    _, _out, _ = node_exec_cmd_check(_node, "/usr/bin/uuidgen")
                    _uuid = _out.splitlines()[0]
                    _updateuuid = True

                elif _lvuuid != _out.splitlines()[0]:
                    _uuid = _out.splitlines()[0]
                    ebLogInfo(f"uuid: {_uuid}")
                    _updateuuid = True

                if _updateuuid:
                    node_exec_cmd_check(_node, f"mount {_lv} /mnt")
                    node_exec_cmd_check(_node, f"umount /mnt")
                    node_exec_cmd_check(_node, f"/usr/sbin/xfs_admin -U {_uuid} {_lv}")

                _out= node_exec_cmd(_node, f"/usr/sbin/xfs_repair -n {_lv}")
                ebLogInfo(f"Executing xfs_repair -n {_lv}")
                if _out.exit_code:
                    msg = (f'command execution failed: {_out.stdout}; stderr="{_out.stderr}"')
                    ebLogError(msg)
                    """
                    node_exec_cmd_check(_node, f"/usr/sbin/vgchange -an {_vg}")
                    node_exec_cmd_check(_node, f"kpartx -d {_devpath}")
                    raise ExacloudRuntimeError(0x10, 0xA, msg)
                    """

                _entries = _out.stdout.splitlines()
                for _entry in _entries:
                    ebLogInfo(f"{_entry}")

            _out = node_exec_cmd(_node, f"mkdir -p /mnt/restore")
            _out = node_exec_cmd(_node, f"mount {_lv} /mnt/restore")
            if _out.exit_code:
                ebLogError(f"mount failed for dom0: {_dom0}")
            _out = node_exec_cmd(_node, f"umount /mnt/restore")

            _, _out, _ = node_exec_cmd(_node, f"ls /EXAVMIMAGES/GuestImages/{_vm}/snapshots/{_dev}.xml")
            # if u01 snapshot is already created and attached, just return
            # No need to attach it again.
            if _out:
                return

            _s, _xml = self.mPrepareXML(_dom0, _vm, _lv, _dev, _uuid)

            _out= node_exec_cmd(_node, f"/usr/bin/virsh attach-device {_vm} {_xml} {_live} --config")
            ebLogInfo(f"Executing virsh attach-device {_vm} {_xml}")         
            if _out.exit_code:
                msg = (f'command execution failed: {_out.stdout}; stderr="{_out.stderr}"')
                ebLogError(msg)
                node_exec_cmd_check(_node, f"/usr/sbin/vgchange -an {_vg}")
                node_exec_cmd_check(_node, f"kpartx -d {_devpath}")
                raise ExacloudRuntimeError(0x10, 0xA, msg)

            _entries = _out.stdout.splitlines()
            for _entry in _entries:
                ebLogInfo(f"{_entry}")

            # pattern followed for dev - u01_Vm3534_1_29bf_rw, vol captured - u01
            _data = {"alias_string": _s, "lvm" : _lv, "vol": _dev.split('_')[0]}

            _reqobj = self.__ebox.mGetRequestObj()
            if _reqobj is not None:
                _reqobj.mSetData(json.dumps(_data, sort_keys = True))
                _db = ebGetDefaultDB()
                _db.mUpdateRequest(_reqobj)
            elif aOptions.jsonmode:
                ebLogJson(json.dumps(_data, indent = 4, sort_keys = True))

            ebLogInfo(f"Mount completed for {_dom0} : {_vm} : snapshot device name: {_devpath} with alias_string: {_s}, lvm: {_lv}")
        
        return 0

    def mPrepareXML(self, aDom0, aVM, aLV, aDev, aUUID):

        import xml.etree.ElementTree as ET
        import string
        _dv = aDev
        _lv = aLV
        _vm = aVM
        _devices = []
        _units = []
        with connect_to_host(aDom0, get_gcontext()) as _node:
            
            _file = f"/etc/libvirt/qemu/{_vm}.xml" 
            _, _out, _ = node_exec_cmd_check(_node, f"grep 'target dev' /etc/libvirt/qemu/{_vm}.xml")                         
            _entries = _out.splitlines()    
            for _entry in _entries:
                _pattern = r"<target dev='(.*?)'"
                match = re.search(_pattern, _entry)
                if match:
                    _devices.append(match.group(1))

            for letter in string.ascii_lowercase:
                if f"sd{letter}" not in _devices:
                    _dev = f"sd{letter}"
                    break

            ebLogInfo(f"list of existing devices: {_devices}, new device: {_dev}")

            _var = "address type='drive'"   
            _, _out, _ = node_exec_cmd_check(_node, f'grep "{_var}" /etc/libvirt/qemu/{_vm}.xml')                               
            _entries = _out.splitlines()    
            for _entry in _entries:         
                root = ET.fromstring(_entry)
                if root is not None:
                    controller_value = root.attrib.get('controller')
                    bus_value = root.attrib.get('bus')
                    target_value = root.attrib.get('target')
                    unit_value = root.attrib.get('unit')
                    _c = controller_value
                    _b = bus_value
                    _t = target_value
                    #_targets.append(target_value) 
                    _units.append(unit_value)
            
            _units.sort()
            _u = int(_units[-1])+1

            content = f"""<!-- uuid={aUUID} -->
              <disk type='block' device='disk'>
              <driver name='qemu' type='raw' cache='none' io='native'/>
              <source dev='{_lv}'/>
              <backingStore/>
              <target dev='{_dev}' bus='scsi'/>
              <readonly/>
              <address type='drive' controller='{_c}' bus='{_b}' target='{_t}' unit='{_u}'/>
            </disk>"""

            _filename = f"/tmp/vol_{_vm}_{_dv}.xml"
            # Open a file in write mode ('w')
            with open(_filename, "w") as file:
                # Write the content to the file
                file.write(content)

            _node.mCopyFile(_filename, _filename)

            node_exec_cmd(_node, f"mkdir -p /EXAVMIMAGES/GuestImages/{_vm}/snapshots")
            _, _out, _ = node_exec_cmd_check(_node, f'cp -f /tmp/vol_{_vm}_{_dv}.xml /EXAVMIMAGES/GuestImages/{_vm}/snapshots/{_dv}.xml')
            
            _filename = f'/EXAVMIMAGES/GuestImages/{_vm}/snapshots/{_dv}.xml'
            _s = f"{_c}:{_b}:{_t}:{_u}"
            ebLogInfo(f"controller={_c} bus={_b} target={_t} unit={_u}, device xml: {_filename}")
            return _s, _filename


    def mMountVolumesVmMove(self, aOptions):

        # Validate input payload
        if "vm_name" not in aOptions.jsonconf:
            raise ExacloudRuntimeError(0x0811, 0xA, 'Missing vm_name in ExaScale Payload')

        if "target_dom0_name" not in aOptions.jsonconf:
            raise ExacloudRuntimeError(0x0811, 0xA, 'Missing target_dom0_name in ExaScale Payload')

        if "source_dom0_name" not in aOptions.jsonconf:
            raise ExacloudRuntimeError(0x0811, 0xA, 'Missing source_dom0_name in ExaScale Payload')

        _vmName = aOptions.jsonconf["vm_name"]
        _tgtDom0 = aOptions.jsonconf["target_dom0_name"]
        _srcDom0 = aOptions.jsonconf["source_dom0_name"]
        
        _gcvVolDevicePath = self.mGetGcvDevicePath(aOptions)
        if not _gcvVolDevicePath:
            raise ExacloudRuntimeError(0x0811, 0xA, 'Missing gcvDevicePath from XML')

        _mountHost = _tgtDom0
        _undo = str(aOptions.undo).lower() == "true"
        if _undo:
            _mountHost = _srcDom0

        with connect_to_host(_mountHost, get_gcontext()) as _tgtNode:

            _cmd = f"/usr/bin/mkdir -p /EXAVMIMAGES/GuestImages/{_vmName}"
            node_exec_cmd_check(_tgtNode, _cmd)

            _cmd = f"/usr/bin/mount -t xfs /dev/exc/{_gcvVolDevicePath} /EXAVMIMAGES/GuestImages/{_vmName} -o defaults,nodev"

            if _undo:
                node_exec_cmd(_tgtNode, _cmd)
            else:
                node_exec_cmd_check(_tgtNode, _cmd)

            _cmd = f"/bin/cat /etc/fstab | grep '{_gcvVolDevicePath}'"
            _tgtNode.mExecuteCmd(_cmd)

            if _tgtNode.mGetCmdExitStatus() != 0:
                _cmd = f'/bin/echo "/dev/exc/{_gcvVolDevicePath}\t/EXAVMIMAGES/GuestImages/{_vmName} xfs   defaults,nodev  1 0" >> /etc/fstab'
                node_exec_cmd_check(_tgtNode, _cmd)


        ebLogInfo(f"mMountVolumesVmMove complete in dom0: {_mountHost} for vm: {_vmName}")


    def mUpdateVMMakerXML(self, aDom0, aVMName, aNetInfo, aFixDummyBridge=False):
        # TODO: This code is just a workaround and can be removed once the
        #       following fix is included in an official OEDA release.
        # Bug 35923350 - EXADB-XS: OEDA : VM MIGRATION TO USE NEW NAT HOSTNAME
        #                AND IP IN CLOUD ENV

        _newNatGateway = aNetInfo["new_gateway"]
        _newNatMask = aNetInfo["new_netmask"]
        _newNatVlan = aNetInfo["new_vlan"]

        with connect_to_host(aDom0, get_gcontext()) as _node:
            _vmeth0 = get_ifcfg_contents(_node, "vmeth0")
            if _newNatGateway is None:
                _newNatGateway = _vmeth0.gateway
            if _newNatMask is None:
                _newNatMask = _vmeth0.netmask

            _newECRAIPs = list(set(aNetInfo["new_ecras_cidr"]))
            for _server in aNetInfo["new_ecras"]:
                _isIp = re.search("([0-9]{1,3}\.){3}[0-9]{1,3}", _server)
                if _isIp:
                    _newECRAIPs.append(_server)
                else:
                    _newECRAIPs.append(socket.gethostbyname(_server))

            _newNatVlan = 0 if _newNatVlan is None else _newNatVlan

            _vmMakerXml = f"{GUEST_IMAGES}/{aVMName}/{aVMName}.xml"
            _now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            _vmMakerXmlBak = f"{_vmMakerXml}.vm_move.{_now}"
            node_exec_cmd_check(
                _node, f"/bin/cp {_vmMakerXml} {_vmMakerXmlBak}")
            ebLogInfo(f"VM maker XML backup saved at {aDom0}:{_vmMakerXmlBak}")

            update_guest_vm_maker_xml_nat(
                _node, aVMName, aNetInfo["new_ip"], (aNetInfo["old_hostname"], aNetInfo["new_hostname"]),
                (aNetInfo["old_domain"], aNetInfo["new_domain"]), aNetInfo["new_netmask"],
                _newNatGateway, _newNatVlan, _newECRAIPs)
            ebLogInfo(f"Updated VM maker XML {aDom0}:{_vmMakerXml} "
                      f"with the following NAT updates: IP: {aNetInfo['new_ip']} ; "
                      f"Hostname: {aNetInfo['old_hostname']} => {aNetInfo['new_hostname']} ; "
                      f"Domain name: {aNetInfo['old_domain']} => "
                      f"{aNetInfo['new_domain']} ; Gateway: {_newNatGateway} ; "
                      f"Netmask: {_newNatMask} ; VLAN ID: {_newNatVlan} ; "
                      f"ECRA IPs: {_newECRAIPs}")

            if aFixDummyBridge:
                # Update the old dummy bridge file to reflect the current bridge
                _, _, _, _goodPostNAT = get_kvm_guest_bridges(_node, aVMName)
                _goodPostNATPath = \
                    f"/EXAVMIMAGES/GuestImages/{aVMName}/{_goodPostNAT}.xml"
                _cmd = f"/bin/ls /EXAVMIMAGES/GuestImages/{aVMName}/vmeth*.xml"
                _currentPostNATPath = \
                    node_exec_cmd_check(_node, _cmd).stdout.strip()
                _currentPostNAT, *_ = \
                    os.path.basename(_currentPostNATPath).split('.')
                if _currentPostNATPath != _goodPostNATPath:
                    _cmd = f"/bin/mv {_currentPostNATPath} {_goodPostNATPath}"
                    node_exec_cmd_check(_node, _cmd)
                _cmd = (f"/bin/sed -i 's/\"vmeth.*\"/\"{_goodPostNAT}\"/' "
                        f"{_goodPostNATPath}")
                node_exec_cmd_check(_node, _cmd)
                ebLogInfo(f"Bridge file updated {_currentPostNATPath} => "
                        f"{_goodPostNATPath}")


    def mPrepareNetInfo(self, aOptions, aUndo=False):

        # Validate input payload
        _payloadFields: Sequence[str] = \
            ('vm_name', 'target_dom0_name', 'source_dom0_name', 'new_admin_ip',
             'new_admin_hostname', 'new_admin_domainname', 'new_admin_mask')
        for _field in _payloadFields:
            if _field not in aOptions.jsonconf:
                raise ExacloudRuntimeError(
                    0x0811, 0xA, f'Missing "{_field}" in ExaScale Payload')

        _vmName = aOptions.jsonconf["vm_name"]
        _tgtDom0 = aOptions.jsonconf["target_dom0_name"]
        _srcDom0 = aOptions.jsonconf["source_dom0_name"]
        _newNatIp = aOptions.jsonconf["new_admin_ip"]
        _newNatHostname = aOptions.jsonconf["new_admin_hostname"]
        _newNatDomainName = aOptions.jsonconf["new_admin_domainname"]
        _newNatMask = aOptions.jsonconf["new_admin_mask"]
        _newNatGateway = aOptions.jsonconf.get("new_admin_subnet")
        _newNatVlan = aOptions.jsonconf.get("new_admin_vlan")
        _newEcraFQDNs = aOptions.jsonconf.get("ecra", {}).get("servers", [])
        _newEcraCIDRs = aOptions.jsonconf.get("ecra", {}).get("whitelist_cidr", [])
        _newRoCENetwork = aOptions.jsonconf.get("roce_information")


        # Get the current NAT info of the VM before migration.
        _oldNatIp = ""
        _oldNatHostname = ""
        _oldNatDomainName = ""
        _oldNatMask = ""
        _oldNatGateway = ""
        _oldNatVlan = ""


        _machineConfig = self.__ebox.mGetMachines().mGetMachineConfig(_vmName)
        _netIds = _machineConfig.mGetMacNetworks()

        _oldBackupVlan = None
        for _netId in _netIds:
            _netConf = self.__ebox.mGetNetworks().mGetNetworkConfig(_netId)
            _net_type = _netConf.mGetNetType()

            if _net_type == 'client':
                _oldClientVlan = _netConf.mGetNetVlanId()
                _oldNatIp = _netConf.mGetNetNatAddr()
                _oldNatHostname = _netConf.mGetNetNatHostName()
                _oldNatDomainName = _netConf.mGetNetNatDomainName()
                _oldNatMask = _netConf.mGetNetNatMask()
                _oldNatGateway = _netConf.mGetNetGateWay()
                try:
                    _oldNatVlan = str(int(_netConf.mGetNetVlanNatId()))
                except ValueError:
                    _oldNatVlan = None
            if _net_type == 'backup':
                _oldBackupVlan = _netConf.mGetNetVlanId()

        # For undo, swap target with destination
        if aUndo:
            _tgtDom0, _srcDom0 = _srcDom0, _tgtDom0
            _newNatIp, _oldNatIp = _oldNatIp, _newNatIp
            _newNatHostname, _oldNatHostname = _oldNatHostname, _newNatHostname
            _newNatDomainName, _oldNatDomainName = _oldNatDomainName, _newNatDomainName
            _newNatMask, _oldNatMask = _oldNatMask, _newNatMask
            _newNatGateway, _oldNatGateway = _oldNatGateway, _newNatGateway
            _newNatVlan, _oldNatVlan = _oldNatVlan, _newNatVlan

        # Migrate Nat information
        _netInfo = {
            "new_ecras": _newEcraFQDNs,
            "new_ecras_cidr": _newEcraCIDRs,
            "new_ip": _newNatIp,
            "new_hostname": _newNatHostname,
            "new_domain": _newNatDomainName,
            "new_gateway": _newNatGateway,
            "new_netmask": _newNatMask,
            "new_vlan": _newNatVlan,
            "new_roce": _newRoCENetwork,
            "source_dom0_name": _srcDom0,
            "target_dom0_name": _tgtDom0,
            "old_ip": _oldNatIp,
            "old_hostname": _oldNatHostname,
            "old_domain": _oldNatDomainName,
            "old_client_vlan": _oldClientVlan,
            "old_backup_vlan": _oldBackupVlan
        }
        self.mMigrateXMLNetworkInformation(_tgtDom0, _netInfo, aOptions)
        return _netInfo

    def mPrepareVmMoveOEDA(self, aOptions):

        _undo = str(aOptions.undo).lower() == "true"
        _force = str(aOptions.jsonconf.get('force')).lower() == 'true'
        _live = str(aOptions.jsonconf.get('mode')).lower() == 'live'

        if _undo and not _live:
            ebLogInfo("mPrepareVmMoveOEDA Undo, Performing mMountVolumesVmMove")
            self.mMountVolumesVmMove(aOptions)
            return
        elif _force:
            # Verify the NAT VLAN is not being used by any other VM
            _tgtDom0 = aOptions.jsonconf["target_dom0_name"]
            _newNATVLAN = aOptions.jsonconf.get("new_admin_vlan")

            with connect_to_host(_tgtDom0, get_gcontext()) as _tgtNode:
                # Verify hypervisor services are running
                try:
                    _cmd = "/bin/virsh list --all --name"
                    _tgtVMs = set(node_exec_cmd_check(
                        _tgtNode, _cmd).stdout.strip().splitlines())
                except:
                    self.fail("INVALID_HYPERVISOR", aCausePlaceholders={"host": _tgtDom0})
                ebLogInfo(f"PASSED: Currently registered VMs in Dom0: {_tgtVMs}")

                if _tgtVMs:
                    _, _, _VMPreNATs, _VMPostNATs = map(set, zip(*map(
                        lambda _vm: get_kvm_guest_bridges(_tgtNode, _vm), _tgtVMs)))
                else:
                    _VMPreNATs, _VMPostNATs = (set(), set())

                _newNATVLAN = 0 if _newNATVLAN is None else _newNATVLAN
                _newNATBridge = "vmeth0" if _newNATVLAN == 0 \
                    else f"vmeth0.{_newNATVLAN}"
                if _newNATBridge in _VMPreNATs:
                    self.fail(
                        "DUPLICATE_NAT_VLAN",
                        aCausePlaceholders={"host": _tgtDom0, "vlan": _newNATVLAN},
                        aSuggestionPlaceholders={"bridge": _newNATBridge}
                    )
                ebLogInfo(f"PASSED: NAT VLAN {_newNATVLAN} is free in Dom0.")

        _netInfo = self.mPrepareNetInfo(aOptions)
        _srcDom0 = _netInfo["source_dom0_name"]
        if not self.mGetCluCtrl().mPingHost(_srcDom0):
            ebLogInfo(f"Source Dom0 {_srcDom0} is not reachable. "
                      "Skipping prepare...")
            return

        # OEDA steps
        def mInternalVMMakerXMLUpdateCallback(aOedacliCmd, aArgs):
            if "STOP_GUEST" in aOedacliCmd:
                aArgs["exascale_obj"].mUpdateVMMakerXML(
                    aArgs["dom0"], aArgs["vm_name"], aArgs["net_info"])

        def mInternalCleanDom0Callback(aOedacliCmd, aArgs):
            if "DETACH_INTERFACES" in aOedacliCmd:
                aArgs["exascale_obj"].mUmountVolumesVmMove(
                    aArgs["dom0"], aArgs["vm_name"], aArgs["net_info"])


        _actions = [
            "STOP_GUEST",
            "DETACH_INTERFACES"
            #"DETACH_VOLUMES",
            #"CREATE_BRIDGES",
            #"MIGRATE_GUEST",
            #"REMOVE_NAT_BRIDGE_SRC",
            #"CREATE_NAT_BRIDGE_TGT",
            #"ATTACH_VOLUMES",
            #"ATTACH_INTERFACES",
            #"STARTUP_GUEST"
        ]

        _callbacks = [
            {
                "fx": mInternalVMMakerXMLUpdateCallback,
                "args": {
                    "exascale_obj": self,
                    "dom0": _netInfo["source_dom0_name"],
                    "vm_name": aOptions.jsonconf["vm_name"],
                    "net_info": _netInfo
                }
            },
            {
                "fx": mInternalCleanDom0Callback,
                "args": {
                    "exascale_obj": self,
                    "dom0": _netInfo["source_dom0_name"],
                    "vm_name": aOptions.jsonconf["vm_name"],
                    "net_info": _netInfo
                },
                "moment": "AFTER"
            }
        ]

        with connect_to_host(aOptions.jsonconf["source_dom0_name"], get_gcontext()) as _node:
            _, _out, _ = node_exec_cmd(_node, f"ls /EXAVMIMAGES/GuestImages/{aOptions.jsonconf['vm_name']}/*u01*xml")
            _snapdev = []   
            #  Get the u01 snapshot thin clone device if present
            if _out:
                _u01snapshot = _out.split('/')[-1].split('.')[0]
                _snapdev.append(_u01snapshot)

            # Get the u02 snapshot thin clone device if present.
            _, _out, _ = node_exec_cmd(_node, f"ls /EXAVMIMAGES/GuestImages/{aOptions.jsonconf['vm_name']}/*u02*xml")
            if _out:
                _u02snapshot = _out.split('/')[-1].split('.')[0]
                _snapdev.append(_u02snapshot)

            # If snapshot of u01-u02 is present then remove the partitions from the source dom0 as well
            if not _live and not _undo and _snapdev:

                for _dev in _snapdev:
                    # remove the logical volume for u01/u02 snapshot
                    _rc, _out, _ = node_exec_cmd(_node, f"kpartx -l /dev/exc/{_dev}")
                    if not _rc:
                        _part = _out.splitlines()[0].split(' ')[0].strip()

                        _rc, _out, _ = node_exec_cmd(_node, f"pvdisplay -c /dev/mapper/{_part}")
                        if not _rc:
                            _vg = _out.splitlines()[0].split(":")[1]

                            _, _out, _ = node_exec_cmd(_node, f"vgchange -an {_vg}")

                            _rc, _out, _ = node_exec_cmd(_node, f"kpartx -d /dev/exc/{_dev}")
                        if _rc:
                            #_, _out, _ = node_exec_cmd(_node, f"lvdisplay -c {_vg}")
                            #_lv = _out.splitlines()[0].split(":")[0].strip()

                            _rc, _out, _ = node_exec_cmd(_node, f"lsblk -f | grep -A1 {_part} | tail -1")
                            if _out:
                                _lvpart = _out.splitlines()[0].split('xfs')[0].strip()[2:]
                                _, _out, _ = node_exec_cmd(_node, f"dmsetup remove {_lvpart}")
                            _, _out, _ = node_exec_cmd(_node, f"dmsetup remove {_part}")

        _live = str(aOptions.jsonconf.get('mode')).lower() == 'live'
        if not _live:
            self.mUmountVolumesVmMove(_netInfo["source_dom0_name"], aOptions.jsonconf["vm_name"], _netInfo)
        elif not _undo and _live:
            _consoleobj = serialConsole(self.mGetCluCtrl(), self.mGetCluCtrl().mGetOptions())
            _consoleobj.mStopContainer(_netInfo["source_dom0_name"], aOptions.jsonconf["vm_name"], aForce=True)
        elif _undo and _live:
            _consoleobj = serialConsole(self.mGetCluCtrl(), self.mGetCluCtrl().mGetOptions())
            _consoleobj.mRestartContainer(_netInfo["source_dom0_name"], aOptions.jsonconf["vm_name"])

        # TODO: Skip OEDA for now to avoid checking for NAT VLAN in target host prematurely.
        #self.mExecuteVmMoveOEDA(
        #    _actions,
        #    aOptions,
        #    _netInfo["source_dom0_name"],
        #    _netInfo["target_dom0_name"],
        #    aOptions.jsonconf["vm_name"],
        #    aCallbacks=_callbacks
        #)

    def mConfigureBonding(self, aOptions, aNetInfo, aUndo=False, aForce=False):

        ebLogTrace("Running mConfigureBonding")

        _vmName = aOptions.jsonconf["vm_name"]
        _newNatHostname = aNetInfo["new_hostname"]
        _srcDom0 = aNetInfo["source_dom0_name"]
        _tgtDom0 = aNetInfo["target_dom0_name"]
        _oldNatHostname = aNetInfo["old_hostname"]
        _newNatIp = aNetInfo["new_ip"]
        _newNatVlan = aNetInfo["new_vlan"]
        _oldNatIp = aNetInfo["old_ip"]

        # Move the bonding configuration
        _monitorJson = ''
        _monitorJsonPathOld = ''
        _customVips = ''
        _customVipsPathOld = ''
        _bondingOp = f'Copied {_tgtDom0}'

        # Retrieve the previous configuration from the GCV EDV
        with connect_to_host(_tgtDom0, get_gcontext()) as _tgtNode:
            _monitorJsonPathOld = REMOTE_MONITOR_CONFIG_VM_FILE_FMT\
                .format(_vmName, _oldNatHostname)
            if _tgtNode.mFileExists(_monitorJsonPathOld):
                _monitorJson = node_read_text_file(
                    _tgtNode, _monitorJsonPathOld).replace(
                        _oldNatHostname, _newNatHostname)
                node_exec_cmd(_tgtNode, f"/bin/rm -f {_monitorJsonPathOld}")
            else:
                ebLogInfo(f"*** Bondmonitor configuration for {_vmName} "
                      f"not found in {_tgtDom0}:{_monitorJsonPathOld}")

            _customVipsPathOld = REMOTE_VM_CUSTOM_VIP_VM_FILE_FMT\
                .format(_vmName, _oldNatHostname)
            if _tgtNode.mFileExists(_customVipsPathOld):
                _customVips = node_read_text_file(
                    _tgtNode, _customVipsPathOld).replace(
                        _oldNatHostname, _newNatHostname)
                node_exec_cmd(_tgtNode, f"/bin/rm -f {_customVipsPathOld}")
            else:
                ebLogInfo(f"*** Custom VIPs configuration for {_vmName} "
                          f"not found in {_tgtDom0}:{_customVipsPathOld}")

            add_remove_entry_monitor_admin_conf(_tgtNode, _newNatIp, _newNatVlan, add=True)

        # For regular VM move, grant the bonding config of the source host.
        if not aForce:
            _bondingOp = f'Moved {_srcDom0}'
            with connect_to_host(_srcDom0, get_gcontext()) as _srcNode:

                _monitorJsonPathOld = REMOTE_MONITOR_CONFIG_FILE_FMT\
                    .format(_oldNatHostname)
                if _srcNode.mFileExists(_monitorJsonPathOld):
                    _monitorJson = node_read_text_file(
                        _srcNode, _monitorJsonPathOld).replace(
                        _oldNatHostname, _newNatHostname)
                    node_exec_cmd(_srcNode, f"/bin/rm -f {_monitorJsonPathOld}")
                else:
                    ebLogInfo(f"*** Bondmonitor configuration for {_vmName} "
                              f"not found in {_srcDom0}:{_monitorJsonPathOld}")

                _customVipsPathOld = REMOTE_VM_CUSTOM_VIP_FILE_FMT\
                    .format(_oldNatHostname)
                if _srcNode.mFileExists(_customVipsPathOld):
                    _customVips = node_read_text_file(
                        _srcNode, _customVipsPathOld).replace(
                        _oldNatHostname, _newNatHostname)
                    node_exec_cmd(_srcNode, f"/bin/rm -f {_customVipsPathOld}")
                else:
                    ebLogInfo(f"*** Custom VIPs configuration for {_vmName} "
                            f"not found in {_srcDom0}:{_customVipsPathOld}")

                add_remove_entry_monitor_admin_conf(_srcNode, _oldNatIp, add=False)

        # Write in the target host the bonding configuration found
        if _monitorJson:
            with connect_to_host(_tgtDom0, get_gcontext()) as _tgtNode:
                _monitorJsonPathNew = REMOTE_MONITOR_CONFIG_FILE_FMT\
                    .format(_newNatHostname)
                _monitorJsonPathNewVm = REMOTE_MONITOR_CONFIG_VM_FILE_FMT\
                    .format(_vmName, _newNatHostname)

                node_exec_cmd(_tgtNode, f"mkdir -p {GUEST_IMAGES}/{_vmName}")
                node_write_text_file(
                    _tgtNode, _monitorJsonPathNew, _monitorJson)
                node_write_text_file(
                    _tgtNode, _monitorJsonPathNewVm, _monitorJson)

                ebLogInfo(f"*** {_bondingOp}:{_monitorJsonPathOld} to "
                          f"{_tgtDom0}:{_monitorJsonPathNew}")

                if _customVips:
                    _customVipsPathNew = REMOTE_VM_CUSTOM_VIP_FILE_FMT\
                        .format(_newNatHostname)
                    _customVipsPathNewVm = REMOTE_VM_CUSTOM_VIP_VM_FILE_FMT\
                        .format(_vmName, _newNatHostname)
                    node_write_text_file(
                        _tgtNode, _customVipsPathNew, _customVips)
                    node_write_text_file(
                        _tgtNode, _customVipsPathNewVm, _customVips)

                    ebLogInfo(f"*** {_bondingOp}:{_customVipsPathOld} to "
                        f"{_tgtDom0}:{_customVipsPathNew}")

                restart_bond_monitor(_tgtNode)


    def mAddRoceSshEntry(self, aHostname):

        def mAddInterfaceToSsh(aNode, aInterface):

            ebLogInfo(f"Checking for interface {aInterface} in sshd_config of {aNode.mGetHostname()}")

            _, _o, _ = aNode.mExecuteCmd("/usr/sbin/ifconfig %s | /bin/grep 'inet' | /bin/awk '{print $2}'" % aInterface)
            if aNode.mGetCmdExitStatus() == 0:
                _currentIp = _o.read().strip()
                ebLogInfo(f"Interface {aInterface} current ip is {_currentIp} in {aNode.mGetHostname()}")

                aNode.mExecuteCmd(f"/bin/cat /etc/ssh/sshd_config | /bin/grep '{_currentIp}'")
                if aNode.mGetCmdExitStatus() != 0:
                    aNode.mExecuteCmd(f"/bin/echo 'ListenAddress {_currentIp}' >> /etc/ssh/sshd_config")
                    aNode.mExecuteCmd("/usr/sbin/service sshd restart")

            aNode.mExecuteCmd("/etc/sysconfig/network-scripts/ifup-routes stre0")
            aNode.mExecuteCmd("/etc/sysconfig/network-scripts/ifup-routes stre1")

        with connect_to_host(aHostname, get_gcontext()) as _node:
            mAddInterfaceToSsh(_node, "stre0")
            mAddInterfaceToSsh(_node, "stre1")

    def mOpenHostAccessControl(self, aNode, aCIDR, aUser="root"):
        _rulesFile = "/etc/exadata/security/exadata-access.conf"
        if not aNode.mFileExists(_rulesFile):
            ebLogWarn(f"{_rulesFile} is not present in {aNode.mGetHostname()}")
            ebLogWarn("Skipping host access control config for this node...")
            return

        _rules = [ rule.strip() for rule in
                   node_read_text_file(aNode, _rulesFile).splitlines()
                   if rule.strip() ]
        if "- : ALL  : ALL" not in _rules:
            ebLogInfo("Security rules fully open for "
                      f"{aNode.mGetHostname()}")
            ebLogWarn("Skipping host access control config for this node...")
            return

        if not any(line for line in _rules
                   if line.startswith(f"+ : {aUser} : ")):
            ebLogWarn(f"No rules for user \"{aUser}\" in {_rulesFile} in "
                      f"{aNode.mGetHostname()}")
            ebLogWarn("Skipping host access control config for this node...")
            return

        _userIx = _rules.index(next(line for line in _rules
                                    if line.startswith(f"+ : {aUser} : ")))
        if aCIDR in _rules[_userIx]:
            ebLogWarn(f"CIDR {aCIDR} is already added in rules for user "
                      f"{aUser} in {_rulesFile} in {aNode.mGetHostname()}")
            ebLogWarn("Skipping host access control config for this node...")
            return

        ebLogInfo(f"Adding {aCIDR} in rules of user {aUser} in "
                  f"{_rulesFile} in {aNode.mGetHostname()}")
        _rules[_userIx] += f" {aCIDR}"

        node_write_text_file(aNode, _rulesFile, '\n'.join(_rules + ['']))


    def mPerformVmMoveOEDA(self, aOptions, aUndo=False, aForce=False):

        # Validate input payload
        _payloadFields: Sequence[str] = \
            ('vm_name', 'target_dom0_name', 'source_dom0_name', 'new_admin_ip',
             'new_admin_hostname', 'new_admin_domainname', 'new_admin_mask')
        for _field in _payloadFields:
            if _field not in aOptions.jsonconf:
                raise ExacloudRuntimeError(
                    0x0811, 0xA, f'Missing "{_field}" in ExaScale Payload')

        _vmName = aOptions.jsonconf["vm_name"]
        _tgtDom0 = aOptions.jsonconf["target_dom0_name"]
        _srcDom0 = aOptions.jsonconf["source_dom0_name"]
        _newNatIp = aOptions.jsonconf["new_admin_ip"]
        _newNatHostname = aOptions.jsonconf["new_admin_hostname"]
        _newNatDomainName = aOptions.jsonconf["new_admin_domainname"]
        _newNatMask = aOptions.jsonconf["new_admin_mask"]
        _newNatGateway = aOptions.jsonconf.get("new_admin_subnet")
        _newNatVlan = aOptions.jsonconf.get("new_admin_vlan")
        _newEcraFQDNs = aOptions.jsonconf.get("ecra", {}).get("servers", [])
        _newEcraCIDRs = aOptions.jsonconf.get("ecra", {}).get("whitelist_cidr", [])
        _newRoCENetwork = aOptions.jsonconf.get("roce_information")
        _live = str(aOptions.jsonconf.get('mode')).lower() == 'live'

        # Get the current NAT info of the VM before migration.
        _oldNatIp = ""
        _oldNatHostname = ""
        _oldNatDomainName = ""
        _oldNatMask = ""
        _oldNatGateway = ""
        _oldNatVlan = ""
        
        _machineConfig = self.__ebox.mGetMachines().mGetMachineConfig(_vmName)
        _netIds = _machineConfig.mGetMacNetworks()

        _oldBackupVlan = None
        for _netId in _netIds:
            _netConf = self.__ebox.mGetNetworks().mGetNetworkConfig(_netId)
            _net_type = _netConf.mGetNetType()

            if _net_type == 'client':
                _oldClientVlan = _netConf.mGetNetVlanId()
                _oldNatIp = _netConf.mGetNetNatAddr()
                _oldNatHostname = _netConf.mGetNetNatHostName()
                _oldNatDomainName = _netConf.mGetNetNatDomainName()
                _oldNatMask = _netConf.mGetNetNatMask()
                _oldNatGateway = _netConf.mGetNetGateWay()
                try:
                    _oldNatVlan = str(int(_netConf.mGetNetVlanNatId()))
                except ValueError:
                    _oldNatVlan = None
            if _net_type == 'backup':
                _oldBackupVlan = _netConf.mGetNetVlanId()


        # For undo, swap target with destination
        if aUndo:
            _tgtDom0, _srcDom0 = _srcDom0, _tgtDom0
            _newNatIp, _oldNatIp = _oldNatIp, _newNatIp
            _newNatHostname, _oldNatHostname = _oldNatHostname, _newNatHostname
            _newNatDomainName, _oldNatDomainName = _oldNatDomainName, _newNatDomainName
            _newNatMask, _oldNatMask = _oldNatMask, _newNatMask
            _newNatGateway, _oldNatGateway = _oldNatGateway, _newNatGateway
            _newNatVlan, _oldNatVlan = _oldNatVlan, _newNatVlan


        _netInfo = {
            "new_ecras": _newEcraFQDNs,
            "new_ecras_cidr": _newEcraCIDRs,
            "new_ip": _newNatIp,
            "new_hostname": _newNatHostname,
            "new_domain": _newNatDomainName,
            "new_gateway": _newNatGateway,
            "new_netmask": _newNatMask,
            "new_vlan": _newNatVlan,
            "new_roce": _newRoCENetwork,
            "source_dom0_name": _srcDom0,
            "target_dom0_name": _tgtDom0,
            "old_ip": _oldNatIp,
            "old_hostname": _oldNatHostname,
            "old_domain": _oldNatDomainName,
            "old_client_vlan": _oldClientVlan,
            "old_backup_vlan": _oldBackupVlan
        }

        # For "undo" of "force" we just clean the VM and the network bridges
        if aUndo and aForce:
            with connect_to_host(_srcDom0, get_gcontext()) as _srcNode:
                _cmd = "/bin/virsh list --all --name"
                _srcVMs = node_exec_cmd_check(_srcNode, _cmd).stdout
                if _vmName not in _srcVMs:
                    ebLogInfo(f"VM {_vmName} not defined in host {_srcDom0}")
                else:
                    _vmBridges = get_kvm_guest_bridges(_srcNode, _vmName)
                    _cmd = f"/bin/virsh destroy {_vmName}"
                    node_exec_cmd(_srcNode, _cmd)
                    _cmd = f"/bin/virsh undefine {_vmName}"
                    node_exec_cmd(_srcNode, _cmd)
                    for _bridge in _vmBridges:
                        _cmd = f"{VM_MAKER} --remove-bridge {_bridge}"
                        node_exec_cmd(_srcNode, _cmd)
                        ebLogInfo(f"Bridge {_bridge} removed from {_srcDom0}")

            self.mUmountVolumesVmMove(_srcDom0, _vmName, _netInfo, aStrict=False)
            return

        if _live:
            _data = {}
            _data["olddummyNATIP"] = ""
            _oldip = _netInfo["old_ip"]
            with connect_to_host(_srcDom0, get_gcontext()) as _node:
                _out= node_exec_cmd(_node, f"nft list chain ip nat PREROUTING | grep {_oldip}") 
                if not _out.exit_code: 
                    _olddummyNATIP = _out.stdout.split(' ')[-1].strip() 
                    _data["olddummyNATIP"] = _olddummyNATIP

        # Remove the client & backup firewall rules from the source Dom0
        # before OEDA changes the VLANs.
        if aForce:
            ebLogWarn(f"Cannot connect to {_srcDom0}, skipping NFTables cleanup...")
        else:
            ebIpTablesRoCE.mRemoveSecurityRulesExaBM(self.__ebox, aDom0s=[_srcDom0])


        def mInternalMountInterfaceCallback(aOedacliCmd, aArgs):
            if "CREATE_BRIDGES" in aOedacliCmd:

                aArgs["exascale_obj"].mMountVolumesVmMove(aArgs["aOptions"])

                aArgs["exascale_obj"].mConfigureBonding(
                    aArgs["aOptions"],
                    aArgs['net_info'],
                    aArgs["aUndo"],
                    aArgs["aForce"]
                )

                def mAccessControlRoCE(aHostname):
                    _stre0IP = aArgs['net_info']['new_roce'][aHostname]['stre0_ip']
                    _roceSubnet = aArgs['net_info']['new_roce'][aHostname]['subnet_mask']
                    _roceNet = f"{_stre0IP}/{_roceSubnet}"
                    with connect_to_host(aHostname, get_gcontext()) as _node:
                        aArgs["exascale_obj"].mOpenHostAccessControl(
                            _node,
                            str(IPv4Network(_roceNet, strict=False))
                        )

                if aArgs['net_info']['new_roce'] is not None:
                    if not aArgs["aForce"]:
                        mAccessControlRoCE(aArgs['net_info']['source_dom0_name'])
                    mAccessControlRoCE(aArgs['net_info']['target_dom0_name'])

                if not aArgs["aForce"]:
                    aArgs["exascale_obj"].mAddRoceSshEntry(aArgs['net_info']['source_dom0_name'])
                aArgs["exascale_obj"].mAddRoceSshEntry(aArgs['net_info']['target_dom0_name'])

                # Remove the dummy bridge backups to avoid Bug 38350312
                _tgtDom0 = aArgs['net_info']['target_dom0_name']
                _vmName = aArgs['vm_name']
                with connect_to_host(_tgtDom0, get_gcontext()) as _node:
                    _cmd = (f"/bin/ls /EXAVMIMAGES/GuestImages/{_vmName}"
                            "/backup/bridges/bridge.vmeth*.xml")
                    _dummyBridgeBackups = \
                        node_exec_cmd(_node, _cmd).stdout.split()
                    for _dummyBridgeBackup in _dummyBridgeBackups:
                        ebLogWarn(f"Contents of {_dummyBridgeBackup} ...")
                        _node.mExecuteCmdLog(f"/bin/cat {_dummyBridgeBackup}")
                    if _dummyBridgeBackups:
                        ebLogWarn("Removing dummy bridge backup files: "
                                f"{_dummyBridgeBackups} in Dom0 {_tgtDom0}")
                        _cmd = (f"/bin/rm -f /EXAVMIMAGES/GuestImages/{_vmName}"
                                "/backup/bridges/bridge.vmeth*.xml")
                        node_exec_cmd(_node, _cmd, log_warning=True)


        def mInternalVMMakerXMLUpdateCallback(aOedacliCmd, aArgs):
            if any(_step in aOedacliCmd for _step in ("CREATE_NAT_BRIDGE_TGT", "STOP_GUEST")):
                aArgs["exascale_obj"].mUpdateVMMakerXML(
                    aArgs["dom0"], aArgs["vm_name"], aArgs["net_info"], aFixDummyBridge=aArgs["aForce"])

        def mInternalMigrateExaKmsEntryCallback(aOedacliCmd, aArgs):
            if "ATTACH_INTERFACES" in aOedacliCmd:

                ebLogTrace("Running mInternalMigrateExaKmsEntryCallback")

                _oldNatHostname = aArgs["netInfo"]["old_hostname"]
                _oldNatDomainName = aArgs["netInfo"]["old_domain"]
                _newNatHostname = aArgs["netInfo"]["new_hostname"]
                _newNatDomainName = aArgs["netInfo"]["new_domain"]

                # ExaKms keys update
                _exakms = get_gcontext().mGetExaKms()
                _cparam = {"FQDN": f"{_oldNatHostname}.{_oldNatDomainName}"}

                _entries = _exakms.mSearchExaKmsEntries(_cparam)
                if _entries:

                    for _entry in _entries:

                        _entryNew = _exakms.mBuildExaKmsEntry(
                            f"{_newNatHostname}.{_newNatDomainName}",
                            _entry.mGetUser(),
                            _entry.mGetPrivateKey(),
                            _entry.mGetHostType()
                        )

                        _exakms.mDeleteExaKmsEntry(_entry)
                        _exakms.mInsertExaKmsEntry(_entryNew)
                else:
                    ebLogInfo(f"No ExaKmsEntries found for {_cparam}")

        def mInternalCleanDom0Callback(aOedacliCmd, aArgs):
            if "DETACH_INTERFACES" in aOedacliCmd:
                aArgs["exascale_obj"].mConfigureBonding(
                    aArgs["aOptions"],
                    aArgs['net_info'],
                    aArgs["aUndo"],
                    aArgs["aForce"]
                )
                aArgs["exascale_obj"].mUmountVolumesVmMove(
                    aArgs["dom0"], aArgs["vm_name"], aArgs["net_info"], aStrict=False)

        if _live:
            _actions = [                    
                #"STOP_GUEST",              
                #"DETACH_INTERFACES",       
                #"DETACH_VOLUMES",          
                "CREATE_BRIDGES",           
                "CREATE_NAT_BRIDGE_TGT",    
                "MIGRATE_GUEST",            
                #"ATTACH_VOLUMES",          
                "ATTACH_INTERFACES",        
                #"REMOVE_NAT_BRIDGE_SRC",    
                #"STARTUP_GUEST"            
            ] if not aUndo else [           
                "STOP_GUEST",               
                "DETACH_INTERFACES",        
                #"DETACH_VOLUMES",          
                #"CREATE_BRIDGES",          
                "MIGRATE_GUEST",            
                #"REMOVE_NAT_BRIDGE_SRC",    
                #"CREATE_NAT_BRIDGE_TGT",   
                #"ATTACH_VOLUMES",          
                #"ATTACH_INTERFACES",       
                #"STARTUP_GUEST"            
            ]                               
        else: 
            _actions = [
                #"STOP_GUEST",
                #"DETACH_INTERFACES",
                #"DETACH_VOLUMES",
                "CREATE_BRIDGES",
                "MIGRATE_GUEST",
                "REMOVE_NAT_BRIDGE_SRC",
                "CREATE_NAT_BRIDGE_TGT",
                #"ATTACH_VOLUMES",
                "ATTACH_INTERFACES",
                #"STARTUP_GUEST"
            ] if not aUndo else [
                "STOP_GUEST",
                "DETACH_INTERFACES",
                #"DETACH_VOLUMES",
                #"CREATE_BRIDGES",
                "MIGRATE_GUEST",
                "REMOVE_NAT_BRIDGE_SRC",
                #"CREATE_NAT_BRIDGE_TGT",
                #"ATTACH_VOLUMES",
                #"ATTACH_INTERFACES",
                #"STARTUP_GUEST"
            ]

        _callbacks = [
            {
                "fx": mInternalMigrateExaKmsEntryCallback,
                "args": {
                    "exascale_obj": self,
                    "aOptions": aOptions,
                    "netInfo": _netInfo
                },
                "moment": "AFTER"
            },
            {
                "fx": mInternalMountInterfaceCallback,
                "args": {
                    "exascale_obj": self,
                    "aOptions": aOptions,
                    "aUndo": aUndo,
                    "aForce": aForce,
                    "net_info": _netInfo,
                    "vm_name": _vmName
                }
            },
            {
                "fx": mInternalVMMakerXMLUpdateCallback,
                "args": {
                    "exascale_obj": self,
                    "dom0": _srcDom0 if aUndo else _tgtDom0,
                    "vm_name": _vmName,
                    "net_info": _netInfo,
                    "aForce": aForce,
                }
            },
            {
                "fx": mInternalCleanDom0Callback,
                "args": {
                    "exascale_obj": self,
                    "dom0": _srcDom0,
                    "vm_name": _vmName,
                    "aOptions": aOptions,
                    "aUndo": aUndo,
                    "aForce": aForce,
                    "net_info": _netInfo
                },
                "moment": "AFTER"
            }
        ]

        self.mExecuteVmMoveOEDA(_actions, aOptions, _srcDom0, _tgtDom0, _vmName, _callbacks, aUndo)

        if _live:
            _newip = _netInfo["new_ip"]
            _data["newdummyNATIP"] = ""
            with connect_to_host(_tgtDom0, get_gcontext()) as _node:
                _out= node_exec_cmd(_node, f"nft list chain ip nat PREROUTING | grep {_newip}") 
                if not _out.exit_code: 
                    _newdummyNATIP = _out.stdout.split(' ')[-1].strip() 
                    _data["newdummyNATIP"] = _newdummyNATIP

            _reqobj = self.__ebox.mGetRequestObj()
            if _reqobj is not None:
                _reqobj.mSetData(json.dumps(_data, sort_keys = True))
                _db = ebGetDefaultDB()
                _db.mUpdateRequest(_reqobj)


    def mExecuteVmMoveOEDA(self, aActions, aOptions, aSrcDom0, aTgtDom0, aVMName, aCallbacks=[], aUndo=False):

        _force = str(aOptions.jsonconf.get('force')).lower() == 'true'
        _live = str(aOptions.jsonconf.get('mode')).lower() == 'live'
        if not _live:
            _mode = f"offline{'force' if _force else ''}"
        else:
            _mode = "live"

        _config = {
            "HOSTNAME": aVMName,
            "SRCHOST": aSrcDom0,
            "TGTHOST": aTgtDom0,
            "MODE": _mode
        }
        ebLogInfo(f"OEDA VM MOVE with MODE: {_config['MODE']}")

        # Exascale log
        _localprfx = 'log/exascale_{0}'.format(self.__ebox.mGetUUID())
        self.__ebox.mExecuteLocal("/bin/mkdir -p {0}".format(_localprfx), aCurrDir=self.__ebox.mGetBasePath())

        _oedacli_bin = self.__ebox.mGetOedaPath() + '/oedacli'

        # Save previous XML
        _initialXml = "{0}/01_initial.xml".format(_localprfx)
        _clonedXml = "{0}/02_cloned.xml".format(_localprfx)
        _moveVmXml = "{0}/03_movevm.xml".format(_localprfx)

        ebLogInfo(f"OEDA VM MOVE logs: {_localprfx}")

        _xmlTree = ebTree(self.__ebox.mGetPatchConfig())
        _xmlTree.mExportXml(_initialXml)

        # Clone the source
        _existingDom0, _newDom0 = (aTgtDom0, aSrcDom0) if aUndo else (aSrcDom0, aTgtDom0)
        self.mCloneSourceInXml(_xmlTree, _existingDom0, _newDom0, aOptions)
        _xmlTree.mExportXml(_clonedXml)
        _xmlTree.mExportXml(self.__ebox.mGetPatchConfig())

        # Replace information about the natips
        self.mPrepareNetInfo(aOptions, aUndo)

        # In order to acquire the lock for Dom0s in VM move, we will update
        # the Dom0s list.
        _newDom0sDomUs: List[List[str]] = [[aSrcDom0, aVMName], [aTgtDom0, aVMName]]
        if self.__ebox.isBaseDB() or self.__ebox.isExacomputeVM():
            self.__ebox.mSetDomUsDom0s(aVMName, sorted(_newDom0sDomUs))
        else:
            _clusterId = self.__ebox.mGetClusters().mGetCluster().mGetCluId()
            self.__ebox.mSetDomUsDom0s(_clusterId, sorted(_newDom0sDomUs))

        # Create OEDA Workdir and Staging
        _reqobj = self.__ebox.mGetRequestObj()
        self.__ebox.mSetupOedaStaging(_reqobj)
        get_gcontext().mSetConfigOption('info_oeda_req_path', self.__ebox.mGetOedaPath())

        self.__ebox.mRestoreOEDASSHKeys(self.__ebox.mGetOptions(), aForce=True)

        _exakms = get_gcontext().mGetExaKms()
        _exakms.mSaveEntriesToFolder(f"{self.__ebox.mGetOedaPath()}/WorkDir", {aTgtDom0: ExaKmsHostType.DOM0})

        # Actions that we allow to fail and continue
        _nonStrictActions = [
            "REMOVE_NAT_BRIDGE_SRC"
        ]

        # OEDACLI update
        for _action in aActions:
            self.__failed_step = _action
            _oedacli = ebOedacli(_oedacli_bin, _localprfx, aLogFile=f"{_action}.oedacli_exascale_vmmove.log", aDeploy=True)
            _where = {"STEPNAME": _action}
            _ocmd = [
                "MIGRATE GUEST",
                _config,
                _where
            ]
            _oedacli.mAppendCommand(_ocmd[0], _ocmd[1], _ocmd[2])

            # Register Callbacks
            for _callback in aCallbacks:
                _moment = "BEFORE"
                if "moment" in _callback:
                    _moment = _callback["moment"]
                _oedacli.mAddCallback(_callback["fx"], _callback["args"], _moment)

            _force = str(aOptions.jsonconf.get('force')).lower() == 'true'
            _lock = self.mCreateLockObj(aOptions)
            try:
                _lock.acquire()
                _oedacli.mRun(self.__ebox.mGetPatchConfig(), _moveVmXml)
                _xmlTree = ebTree(_moveVmXml)
                _xmlTree.mExportXml(self.__ebox.mGetPatchConfig())
            except Exception as ex:
                if not aUndo and _action not in _nonStrictActions:
                    _msg = f"*** EXASCALE: OEDA VM move step {_action} failed!!!"
                    raise ExacloudRuntimeError(0x0811, 0xA, _msg) from ex
                else:
                    _msg = f"*** EXASCALE: Skipping failed OEDA VM move step {_action}"
                    ebLogWarn(_msg)
            finally:
                _lock.release()

        ebLogInfo(f"OEDA VM MOVE logs: {_localprfx}")
        ebLogInfo(f"Updated XML: {_moveVmXml}")

    def mCreateLockObj(self, aOptions):

        _tgtDom0 = aOptions.jsonconf["target_dom0_name"]
        _srcDom0 = aOptions.jsonconf["source_dom0_name"]
        _force = str(aOptions.jsonconf.get('force')).lower() == 'true'

        if _force:
            _dom0List = [_tgtDom0]
        else:
            _dom0List = [_srcDom0, _tgtDom0]

        _lock = RemoteLock(self.__ebox, force_host_list=_dom0List)
        return _lock

    def mPerformVmMoveExacloud(self, aOptions):
        """Exacloud independent VM move.

        The Exacloud approach executes the following actions:
        
        In the source Dom0:
        - Shutdown the VM
        - Compress the VM .img files
        - Copy the compressed images to the destination Dom0
        - Copy the grid-klone-Linux-x86-64 package to the destination Dom0
        - Copy the VM XML from /EXAVMIMAGES/conf/<DomU>-vm.xml to the destination node
        - Remove the domain using VM maker

        In the destination node:
        - Replace the Nat IP and Hostname in the VM XML
        - Start the VM using VM maker
        - Shutdown the VM
        - Decompress and replace the imges
        - Attach u02 again

        :param aOptions: Exacloud options object.
        """

        # Validate input payload
        _payloadFields: Sequence[str] = \
            ('vm_name', 'target_dom0_name', 'source_dom0_name', 'new_admin_ip',
             'new_admin_hostname', 'new_admin_domainname')
        for _field in _payloadFields:
            if _field not in aOptions.jsonconf:
                raise ExacloudRuntimeError(
                    0x0811, 0xA, f'Missing "{_field}" in ExaScale Payload')

        _vmName = aOptions.jsonconf["vm_name"]
        _tgtDom0 = aOptions.jsonconf["target_dom0_name"]
        _srcDom0 = aOptions.jsonconf["source_dom0_name"]
        _newNatIp = aOptions.jsonconf["new_admin_ip"]
        _newNatHostname = aOptions.jsonconf["new_admin_hostname"]
        _newNatDomainName = aOptions.jsonconf["new_admin_domainname"]

        # Get the NAT info from the VM before moving
        _oldNatIp = ""
        _oldNatHostname = ""
        _oldNatDomainName = ""

        _machineConfig = self.__ebox.mGetMachines().mGetMachineConfig(_vmName)
        _netIds = _machineConfig.mGetMacNetworks()

        for _netId in _netIds:
            _netConf = self.__ebox.mGetNetworks().mGetNetworkConfig(_netId)
            _net_type = _netConf.mGetNetType()

            if _net_type == 'client':
                _oldNatIp = _netConf.mGetNetNatAddr()
                _oldNatHostname = _netConf.mGetNetNatHostName()
                _oldNatDomainName = _netConf.mGetNetNatDomainName()

        _newDom0sDomUs: List[List[str]] = \
            [[_srcDom0, _vmName], [_tgtDom0, _vmName]]
        if self.__ebox.isBaseDB() or self.__ebox.isExacomputeVM():
            self.__ebox.mSetDomUsDom0s(_vmName, sorted(_newDom0sDomUs))
        else:
            # Change the Dom0s to configure the passowrless on them later
            _clusterId = self.__ebox.mGetClusters().mGetCluster().mGetCluId()
            self.__ebox.mSetDomUsDom0s(_clusterId, sorted(_newDom0sDomUs))
        
        # TODO: Patch the XML with the new network data
        # - New Dom0 name (dependency on Bug 34686917)
        # - Updated DomU NAT info

        _tmpImgPath: str = os.path.join(f"{GUEST_IMAGES}VmMove", _vmName)
        _vmMakerXmlPath: str = f"/EXAVMIMAGES/conf/{_vmName}-vm.xml"
        _vmMakerXml: str = ""
        _tgtCurrentImgs: Set[str] = {}


        # We clean and prepare the target node
        with connect_to_host(_tgtDom0, get_gcontext()) as _tgtNode:

            # Get the binaries paths needed from the target Dom0
            MKDIR: str = node_cmd_abs_path_check(_tgtNode, 'mkdir')
            LS: str = node_cmd_abs_path_check(_tgtNode, 'ls')

            # Make sure the temp dir for the images exists.
            node_exec_cmd_check(_tgtNode, f"{MKDIR} -p {_tmpImgPath}")

            # Get the current set of images
            _, _out, _ = node_exec_cmd(_tgtNode, f"{LS} /EXAVMIMAGES/*.zip")

            _tgtCurrentImgs = set(_out.splitlines())


        # Operations in the source node
        with connect_to_host(_srcDom0, get_gcontext()) as _srcNode:

            # Get the binaries paths needed from the source Dom0            
            LS: str = node_cmd_abs_path_check(_srcNode, 'ls')
            BZIP2: str = node_cmd_abs_path_check(_srcNode, 'bzip2')
            SCP: str = node_cmd_abs_path_check(_srcNode, 'scp')

            # Shutdown the VM
            shutdown_domu(_srcNode, _vmName)

            # Steal the VM Maker XML that was used for creating this VM
            # and update the NAT information
            _vmMakerXml = node_read_text_file(_srcNode, _vmMakerXmlPath)\
                .replace(_oldNatIp, _newNatIp)\
                .replace(_oldNatHostname, _newNatHostname)\
                .replace(_oldNatDomainName, _newNatDomainName)

            # Get the VM disk images that we're going compress and copy
            _imagesPath: str = os.path.join(GUEST_IMAGES, _vmName, '*.img')
            _, _out, _ = node_exec_cmd_check(_srcNode, f"{LS} {_imagesPath}")
            _diskImages: List[str] = _out.splitlines()

            # Check the images in the node and check if we need to copy some
            # dependencies
            _imgDep: Set[str] = { _dep.split('>')[1].split('<')[0]
                for _dep in _vmMakerXml.splitlines()
                if 'domuVolume' in _dep and 'EXAVMIMAGES' in _dep } - \
                _tgtCurrentImgs
            
            # Copy the VM disk images to the target Dom0
            ebLogInfo(f"*** Compressing {_vmName} disk image files")
            for _diskImage in _diskImages:
                ebLogInfo(f"*** - Compressing {_diskImage} ...")
                node_exec_cmd_check(_srcNode, f"{BZIP2} {_diskImage}")
            ebLogInfo("*** Compression finished.")

            # Temporary configure Dom0s SSH password-less access
            _lock = self.mCreateLockObj(aOptions)

            try:
                _lock.acquire()

                _globalCacheFactory = GlobalCacheFactory(self.__ebox)
                _globalCacheFactory.mCreatePasswordless()

                # Copy the DomU images to the target Dom0
                _comprImgPath: str = \
                    os.path.join(GUEST_IMAGES, _vmName, '*.bz2')
                ebLogInfo("*** Copying disk images from "
                    f"{_srcDom0}:{_comprImgPath} to {_tgtDom0}:{_tmpImgPath}")
                _cmd: str = (
                    f"{SCP} -i /root/.ssh/global_cache_key "
                    "-o StrictHostKeyChecking=no "
                    "-o UserKnownHostsFile=/dev/null "
                    f"{_comprImgPath} root@{_tgtDom0}:{_tmpImgPath}")
                node_exec_cmd_check(_srcNode, _cmd)
                ebLogInfo("*** Copying disk images complete.")

                # Copy image dependencies
                if _imgDep:
                    ebLogInfo("*** Copying the following dependencies "
                              f"{_imgDep}")
                    for _img in _imgDep:
                        _cmd: str = (
                            f"{SCP} -i /root/.ssh/global_cache_key "
                            "-o StrictHostKeyChecking=no "
                            "-o UserKnownHostsFile=/dev/null "
                            f"{_img} root@{_tgtDom0}:{_img}")
                        node_exec_cmd_check(_srcNode, _cmd)
                    ebLogInfo("*** Copying dependencies complete.")

            finally:
                # Clean the password-less
                _globalCacheFactory.mCleanPassordless()
                _lock.release()

            # Remove the VM
            ebLogInfo(f"Removing VM {_vmName} in {_srcDom0}")
            _cmd = f"{VM_MAKER} --remove-domain {_vmName}"
            node_exec_cmd_check(_srcNode, _cmd)


        # Steps in the target node
        with connect_to_host(_tgtDom0, get_gcontext()) as _tgtNode:

            # Get the binaries paths needed from the target Dom0
            BUNZIP2: str = node_cmd_abs_path_check(_tgtNode, 'bunzip2')
            MKDIR: str = node_cmd_abs_path_check(_tgtNode, 'mkdir')
            LS: str = node_cmd_abs_path_check(_tgtNode, 'ls')
            MV: str = node_cmd_abs_path_check(_tgtNode, 'mv')

            # Create the VM in the target node
            ebLogInfo(f"Creating VM {_vmName} in {_tgtDom0}")
            node_write_text_file(_tgtNode, _vmMakerXmlPath, _vmMakerXml)
            _cmd: str = ("export EXADATA_SKIP_DOMU_NETWORK_CHECK=yes; "
                         f"{VM_MAKER} --start-domain {_vmMakerXmlPath}")
            node_exec_cmd_check(_tgtNode, _cmd)

            # Shutdown the VM
            shutdown_domu(_tgtNode, _vmName, timeout_seconds=10,
                          force_on_timeout=True)

            # Decompress and replace the disk image files.
            _comprImgPath: str = os.path.join(_tmpImgPath, '*.bz2')
            _, _out, _ = node_exec_cmd_check(_tgtNode, f"{LS} {_comprImgPath}")
            _diskImages: str = _out.splitlines()
            ebLogInfo(f"*** Decompressing {_vmName} disk image files")
            for _diskImage in _diskImages:
                ebLogInfo(f"*** - Decompressing {_diskImage} ...")
                node_exec_cmd_check(_tgtNode, f"{BUNZIP2} {_diskImage}")
            ebLogInfo("*** Decompression finished.")

            _srcImgsPath: str = os.path.join(_tmpImgPath, "*.img")
            _vmFilesPath: str = os.path.join(GUEST_IMAGES, _vmName)
            node_exec_cmd_check(_tgtNode,
                                f"{MV} -f {_srcImgsPath} {_vmFilesPath}")

            # Attach u02 again
            _u02ImgPath: str = os.path.join(_vmFilesPath, 'u02_extra.img')
            attach_dom0_disk_image(_tgtNode, _vmName, _u02ImgPath)


        _localprfx = 'log/exascale_{0}'.format(self.__ebox.mGetUUID())
        self.__ebox.mExecuteLocal("/bin/mkdir -p {0}".format(_localprfx), aCurrDir=self.__ebox.mGetBasePath())

        _initial = "{0}/01_initial.xml".format(_localprfx)
        _changed = "{0}/02_changed.xml".format(_localprfx)
        _xmlTree = ebTree(self.__ebox.mGetPatchConfig())

        ebLogInfo(f"Saving Initial XML into: {_initial}")
        _xmlTree.mExportXml(_initial)

        # Modify XML
        _args = {
            "past_dom0_fqdn": _srcDom0,
            "past_dom0_host": _srcDom0.split(".")[0],
            "past_dom0_ip": socket.gethostbyname(_srcDom0),
            "new_dom0_fqdn": _tgtDom0,
            "new_dom0_host": _tgtDom0.split(".")[0],
            "new_dom0_ip": socket.gethostbyname(_tgtDom0)
        }

        _xmlTree.mBFS(aStuffCallback=mReplaceDom0sFx, aStuffArgs=_args)

        ebLogInfo(f"Saving Initial XML into: {_changed}")
        _xmlTree.mExportXml(_changed)
        _xmlTree.mExportXml(self.__ebox.mGetPatchConfig())


    def mPerformVmMove(self, aOptions):
        """Executes VM move.

        The method used will be determined by the exabox.conf parameter
        {
            "exascale": {
                "vm_move_api": "oeda",
                ...
            },
            ...
        }

        Possible options:
         - oeda
         - exacloud

        :param aOptions: Exacloud options object.
        """

        if not self.__ebox.mIsExaScale():
            _msg = 'Operation allowed only in ExaScale'
            raise ExacloudRuntimeError(0x0811, 0xA, _msg)

        # Execute Sanity Checks or actual VM move
        if aOptions.jsonconf is None:
            _msg = 'Missing JSON Payload required for VM move'
            raise ExacloudRuntimeError(0x0811, 0xA, _msg)

        if 'action' not in aOptions.jsonconf:
            _msg = 'Missing "action" field in JSON payload'
            raise ExacloudRuntimeError(0x0811, 0xA, _msg)
        _action = aOptions.jsonconf['action']

        # Undo/retry options
        _undo = str(aOptions.undo).lower() == "true"

        # Move force (ignore source host)
        _force = str(aOptions.jsonconf.get('force')).lower() == 'true'

        # Get method to use for VM move
        _vmMoveApi = None
        _exascaleOpts = self.__ebox.mCheckConfigOption('exascale')
        if _exascaleOpts:
            _vmMoveApi = _exascaleOpts.get('vm_move_api')

        if _vmMoveApi is None:
            _vmMoveApi = 'oeda'
            ebLogWarn('*** EXASCALE: No VM move API specified in exabox.conf, '
                      'we will use OEDA API by defualt.')


        _tgtDom0 = aOptions.jsonconf["target_dom0_name"]
        _srcDom0 = aOptions.jsonconf["source_dom0_name"]
        _vmName = aOptions.jsonconf["vm_name"]

        if _action == 'moveSanityCheck':
            ebLogInfo('*** EXASCALE: Performing VM move Sanity Checks')
            if _vmMoveApi == 'oeda':
                _lock = self.mCreateLockObj(aOptions)
                try:
                    _lock.acquire()
                    #Clear if any stale bridge exist, before VM move
                    csUtil().mDeleteStaleDummyBridge(self.__ebox, [[_tgtDom0, _vmName]])

                    self.mPerformVmMoveSanityChecksOEDA(aOptions, _exascaleOpts)
                finally:
                    _lock.release()
            elif _vmMoveApi == 'exacloud':
                self.mPerformVmMoveSanityChecksExacloud(aOptions)
            ebLogInfo('*** EXASCALE: VM move Sanity Checks passed!')
            return

        if _action != 'move':
            _msg = f'Unkown VM move action "{_action}"'
            raise ExacloudRuntimeError(0x0811, 0xA, _msg)


        self.__ebox.mDom0UpdateCurrentOpLog(aOptions, "VM-Move", "started", [[_tgtDom0, _vmName]])
        # Perform the VM move
        if _vmMoveApi == 'exacloud':
            ebLogInfo('*** EXASCALE: Performing VM move with Exacloud API')
            self.mPerformVmMoveExacloud(aOptions)
        elif _vmMoveApi == 'oeda':
            ebLogInfo('*** EXASCALE: Performing VM move with OEDA API')
            self.mPerformVmMoveOEDA(aOptions, _undo, _force)
        else:
            _msg = f'Unknown VM move API: {_vmMoveApi}'
            raise ExacloudRuntimeError(0x0811, 0xA, _msg)

        self.__ebox.mDom0UpdateCurrentOpLog(aOptions, "VM-Move", "ended", [[_tgtDom0, _vmName]])

        if _undo:
            ebLogInfo("*** EXASCALE: VM move undo completed!")
            return

        self.mPostVMMoveSteps(aOptions)

        ebLogInfo("Update cluster xml to remove src dom0 entries.")
        self.mDettachGuestMachineFromHostXML(aOptions.jsonconf["source_dom0_name"])
        _oedacli_bin = self.__ebox.mGetOedaPath() + '/oedacli'
        _localprfx = 'log/exascale_{0}'.format(self.__ebox.mGetUUID())
        _oedacli = ebOedacli(_oedacli_bin, _localprfx, aLogFile="oedacli_exascale_dom0remove.log")
        _oedacli.mSetAutoSaveActions(True)
        _oedacli.mSetDeploy(False)

        # Declare command to use
        _dom0 = aOptions.jsonconf["source_dom0_name"]
        _cmd = (f"delete compute where srcname={_dom0}")

        # Append command to ebOedacli object
        _oedacli.mAppendCommand(_cmd)

        # Run command
        _xml = self.__ebox.mGetPatchConfig()
        _xmlbackup = f"{self.__ebox.mGetPatchConfig()}_bk"
        self.__ebox.mExecuteLocal(f"cp -f {_xml} {_xmlbackup}")
        _cmdout = _oedacli.mRun(_xmlbackup, _xml)
        ebLogInfo(_cmdout)

        # Clean up
        self.mCleanUpVMMove(aOptions)

        if self.__ebox.mCheckConfigOption("enable_validate_volumes", "True"):
            self.mPerformValidateVolumesCheck(_tgtDom0, _vmName)
        else:
            ebLogInfo(f"enable_validate_volumes config is disabled in exabox.conf. Hence Skipping")

        ebLogInfo('*** EXASCALE: VM move completed!')

    def mCheckDom0Roce(self, aOptions):                                                                                                                                                                            

        _roce_configured = False
        if not aOptions.jsonconf or "roce_config_dom0_name" not in aOptions.jsonconf:
            raise ExacloudRuntimeError(0x0811, 0xA, f'Missing roce config details in the payload')

        _dom0 = aOptions.jsonconf.get("roce_config_dom0_name")

        ebLogInfo(f'mCheckRoceConfig: {_dom0}')
        with connect_to_host(_dom0, get_gcontext()) as _node:
            for stre_iface in ('stre0', 'stre1'):
                #Check if stre interface is configured with ip.
                _cmd = f'/usr/sbin/ip a s {stre_iface} | grep inet'
                _node.mExecuteCmdLog(_cmd)
                _ret = _node.mGetCmdExitStatus()
                if _ret == 0:
                    _roce_configured = True
                    ebLogInfo(f'mCheckDom0Roce: Interface {stre_iface} is already configured.')
                else:
                    _roce_configured = False
                    ebLogInfo(f'mCheckDom0Roce: Interface {stre_iface} is not yet configured.')
                    break

        _req = self.__ebox.mGetRequestObj()
        if _req is not None:
            _res = json.dumps(
                {
                    "roce_dom0_configured": _roce_configured
                },
                indent=4
            )
            _req.mSetData(_res)
            _db = ebGetDefaultDB()
            _db.mUpdateRequest(_req)

        return 0

    def mConfigureDom0Roce(self, aOptions):

        if not aOptions.jsonconf or "roce_config_dom0_name" not in aOptions.jsonconf or "stre0_ip" not in aOptions.jsonconf:
            raise ExacloudRuntimeError(0x0811, 0xA, f'Missing roce config details in the payload')

        _dom0 = aOptions.jsonconf.get("roce_config_dom0_name")
        _ip = aOptions.jsonconf.get("stre0_ip")
        ebLogInfo(f'mConfigureDom0Roce: {_dom0} : {_ip}')
        _vlan_id = self.__ebox.mCheckConfigOption('exadbxs_storage_vlanid')
        if _vlan_id is None:
            _vlan_id = "3999"
            #3999 is the vlan allocated for exadbxs exadata storage
        _netmask = self.__ebox.mCheckConfigOption('exadbxs_stre_netmask')
        if _netmask is None:
            _netmask = "255.255.0.0"
            #stre interfaces are allocated 'class B' address from ecra. Hence this netmask of 255.255.0.0

        with connect_to_host(_dom0, get_gcontext()) as _node:
            _cmd = f'/usr/sbin/vm_maker --set --storage-vlan {_vlan_id} --ip {_ip} --netmask {_netmask}'
            _node.mExecuteCmdLog(_cmd)
            _ret = _node.mGetCmdExitStatus()
            if _ret != 0:
                _msg = f'mConfigureDom0Roce: Unable to configure the stre interface'
                ebLogError(_msg)
                raise ExacloudRuntimeError(0x0811, 0xA, _msg)
            else:
                ebLogInfo(f'mConfigureDom0Roce: stre iface configuration done. Will reboot the node now')
            self.__ebox.mRebootNode(_dom0)

        with connect_to_host(_dom0, get_gcontext()) as _node:
            #Validate interfaces are properly set.
            #stre0 should be set to the input ip.
            _node.mExecuteCmdLog(f'/usr/sbin/ip a s stre0 | grep {_ip}')
            _ret = _node.mGetCmdExitStatus()
            if _ret == 0:
                ebLogInfo(f'mCheckDom0Roce: Interface stre0 is configured successfully.')
            else:
                _msg = f'mCheckDom0Roce: Interface stre0 is not configured.'
                ebLogError(_msg)
                raise ExacloudRuntimeError(0x0811, 0xA, _msg)

            #stre1 will be set with the next subsequent ip-adress. Hence check if any ip is configured.
            _node.mExecuteCmdLog(f'/usr/sbin/ip a s stre1 | grep inet')
            _ret = _node.mGetCmdExitStatus()
            if _ret == 0:
                ebLogInfo(f'mCheckDom0Roce: Interface stre1 is configured successfully.')
            else:
                _msg = f'mCheckDom0Roce: Interface stre1 is not configured.'
                ebLogError(_msg)
                raise ExacloudRuntimeError(0x0811, 0xA, _msg)

        return 0

    def mClonePreCheck(self, aOptions):
        _edv_info = get_hosts_edv_from_cs_payload(aOptions.jsonconf)
        _edv_states = get_hosts_edv_state(_edv_info)
        ebLogInfo(f"_edv_states: {_edv_states}")
        for host, guests in _edv_states.items():
            for guest, edvs in guests.items():
                for edv in edvs:
                    _state = edv.state
                    if _state != EDVState.MOUNTED_HOST:
                        _msg = f'edv device {edv.device_path} is in state:{_state}. Expected state is {EDVState.MOUNTED_HOST}'
                        raise ExacloudRuntimeError(0x0811, 0xA, _msg)
    def mCopyWeblogicCert(self):
        if self.__ebox.mCheckSubConfigOption("weblogic_cert", "Enabled") != "True":
            return

        _local_file = self.__ebox.mCheckSubConfigOption("weblogic_cert", "weblogic_cert_localpath")
        _local_file = os.path.join(self.__ebox.mGetBasePath(), _local_file)
        if not os.path.exists(_local_file):
            _weblogic_cert = self.__ebox.mCheckSubConfigOption("weblogic_cert", "weblogic_cert_oss_link")
            if _weblogic_cert:
                _cmd = f"/usr/bin/curl {_weblogic_cert} -o {_local_file}"
                _rc, _, _o, _e = self.__ebox.mExecuteLocal(_cmd)
                if _rc != 0:
                    _msg = f"Unable to Download file {_weblogic_cert}"
                    raise ExacloudRuntimeError(0x0811, 0xA, _msg)

        if not os.path.exists(_local_file):
            _msg = f"weblogic cert {_local_file} not available on local box !"
            raise ExacloudRuntimeError(0x0811, 0xA, _msg)

        _remote_cert_loc = self.__ebox.mCheckSubConfigOption("weblogic_cert", "weblogic_cert_vmpath")
        if _remote_cert_loc:
            for _, _domU in self.__ebox.mReturnDom0DomUPair():
                 with connect_to_host(_domU, get_gcontext(), username="root") as _node:
                     if not _node.mFileExists(_remote_cert_loc):
                         _rc = _node.mCopyFile(_local_file, _remote_cert_loc)
                         if _rc is not None:
                             _msg = f"Unable to copy weblogic cert to domu under {_remote_cert_loc}!"
                             raise ExacloudRuntimeError(0x0811, 0xA, _msg)

# end of file
