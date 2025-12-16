#!/bin/python
#
# $Header: ecs/exacloud/exabox/exadbxs/edv.py /main/11 2025/09/10 15:17:42 scoral Exp $
#
# edv.py
#
# Copyright (c) 2023, 2025, Oracle and/or its affiliates.
#
#    NAME
#      edv.py - Entrypoint of EDV endpoint.
#
#    DESCRIPTION
#      Utilities to manage EDV volumes in ExaDB-XS.
#
#    NOTES
#      None.
#
#    MODIFIED   (MM/DD/YY)
#    scoral      09/03/25 - Bug 38338038 - Added methods to update the EDVs in
#                           the cluster XML.
#    scoral      07/31/25 - Enh 38190209 - Added methods for resizing the guest
#                           filesystems EDVs.
#    naps        06/27/25 - Bug 38042220 - sanity check for clone operation.
#    scoral      01/04/23 - 36152786: Allow get_hosts_edv_from_cs_payload to
#                           also parse Elastic Compute payload.
#    jesandov    08/15/23 - 35710475: Use payload information in case of
#                           missing FQDN
#    scoral      08/09/23 - 35688858: Remove /etc/fstab entries during stale
#                           GCV EDV unmounting.
#    scoral      08/03/23 - 35646209: Implemented unmount_stale_gcv_edv
#    joysjose    07/13/23 - Bug 35592983 - EDV PROVISIONING IS FAILING IN LAST
#                           WORKFLOW STEP OF EXACLOUD
#    scoral      07/10/23 - 35578289: Renamed OK to ATTACHED_GUEST and
#                           MISSING_GUEST to MOUNTED_HOST.
#    scoral      06/23/23 - 35502608: Implemented get_hosts_edv_from_cs_payload
#    scoral      06/19/23 - Creation
#

import stat
import math
from enum import Enum
from typing import NamedTuple, Mapping, Optional, Sequence, Dict, List

from paramiko import SFTPAttributes
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogWarn, ebLogInfo, ebLogError
from exabox.core.Error import ExacloudRuntimeError
from exabox.tools.ebTree.ebTree import ebTree
from exabox.tools.ebTree.ebTreeNode import ebTreeNode
from exabox.ovm.cludomufilesystems import (GIB, get_node_filesystems,
                                           ebNodeFilesystemInfo)
from exabox.utils.node import (node_exec_cmd, node_exec_cmd_check,
                               node_cmd_abs_path_check, connect_to_host)


##################
### DATA TYPES ###
##################

class EDVAction(Enum):
    PRECHECK        = "precheck"


class EDVState(Enum):
    # Volume is mounted in the host and attached to the guest.
    ATTACHED_GUEST  = "attached_guest"
    # Volume status has not been checked yet.
    NOT_CHECKED     = "not_checked"
    # Volume not mounted in the host.
    NOT_MOUNTED     = "not_mounted"
    # Volume path does not correspond to a block device.
    BAD_VOLUME      = "bad_volume"
    # Volume is mounted to the host but the guest is missing.
    MOUNTED_HOST    = "mounted_host"
    # Volume is mounted to the host but is not attached to the guest.
    NOT_ATTACHED    = "not_attached"


class EDVInfo(NamedTuple):
    vol_id: str
    vol_type: str
    name: str
    size_bytes: int
    device_path: str
    state: EDVState = EDVState.NOT_CHECKED



###############
### METHODS ###
###############


###############
### PARSING ###
###############


def get_guest_edvs_from_cluster_xml(
        cluster_xml: ebTree,
        edvs_info: Dict[str, EDVInfo],
        guest: str) -> List[EDVInfo]:
    """Filters the EDV volumes information of a guest from the cluster XML.

    :param cluster_xml: Cluster XML.
    :param edvs_info: Mapping of EDV volume ID -> EDVInfo.
    :param guest: Guest name (as it appears in "virsh list").
    :returns: List of EDVInfo.
    """
    def _get_guest_edv_ids(xml_node: ebTreeNode, args: dict):
        if xml_node.mGetSortElement() != 'hostName' or \
            guest not in xml_node.mGetElement()['text'] or \
            xml_node.mGetParent().mGetSortElement() != 'machine':
            return

        for child in xml_node.mGetParent().mGetChildren():
            if child.mGetSortElement() != 'edvVolumes':
                continue
            args['edv_ids'] = [ grand_child.mGetElement()['id']
                                for grand_child in child.mGetChildren() ]
            return

    args = { 'edv_ids': [] }
    cluster_xml.mBFS(aStuffCallback=_get_guest_edv_ids, aStuffArgs=args)

    return [ edvs_info[vol_id] for vol_id in args['edv_ids'] ]


def get_edvs_from_cluster_xml(
        cluster_xml: ebTree) -> Dict[str, EDVInfo]:
    """Parses the information of the EDV volumes from the cluster XML.

    :param cluster_xml: Cluster XML.
    :returns: Mapping of EDV volume ID -> EDVInfo.
    """
    def _get_edvs_info(xml_node: ebTreeNode, args: dict):
        if xml_node.mGetSortElement() != 'edvVolume' or \
            not xml_node.mGetChildren():
            return
        
        vol_id: str = xml_node.mGetElement()['id']
        vol_type: str = ''
        vol_name: str = ''
        vol_size_bytes: int = 0
        vol_device_path: str = ''

        for child in xml_node.mGetChildren():
            if child.mGetSortElement() == 'edvVolumeType':
                vol_type = child.mGetElement()["text"]
            elif child.mGetSortElement() == 'edvVolumeName':
                vol_name = child.mGetElement()["text"]
            elif child.mGetSortElement() == 'edvVolumeSize':
                vol_size_bytes = int(
                    ''.join(filter(str.isdigit, child.mGetElement()["text"]))
                ) * GIB
            elif child.mGetSortElement() == 'edvDevicePath':
                vol_device_path = child.mGetElement()["text"]

        args['edvs'][vol_id] = EDVInfo(
            vol_id, vol_type, vol_name, vol_size_bytes, vol_device_path)

    args = { 'edvs': {} }
    cluster_xml.mBFS(aStuffCallback=_get_edvs_info, aStuffArgs=args)

    return args['edvs']


def update_edvs_from_cluster_xml(
        cluster_xml: ebTree,
        edvs: Dict[str, EDVInfo]):
    """Updates the information of the EDV volumes from the cluster XML.

    :param cluster_xml: Cluster XML.
    :param edvs: Mapping of EDV volume ID -> EDVInfo.
    """
    def _update_edvs_info(xml_node: ebTreeNode, args: dict):
        if xml_node.mGetSortElement() != 'edvVolume' or \
            not xml_node.mGetChildren() or \
            xml_node.mGetElement()['id'] not in edvs:
            return

        fields_to_change = [
            child for child in xml_node.mGetChildren()
            if child.mGetSortElement() in (
                "edvVolumeType", "edvVolumeName", "edvVolumeSize",
                "edvDevicePath"
            )
        ]
        for child in fields_to_change:
            child.mRemove()

        edv: EDVInfo = edvs[xml_node.mGetElement()['id']]
        ebTreeNode({ "text": edv.vol_type, "tag": "edvVolumeType" }, xml_node)
        ebTreeNode({ "text": edv.name, "tag": "edvVolumeName" }, xml_node)
        ebTreeNode(
            {
                "text": str(math.ceil(edv.size_bytes / GIB)),
                "tag": "edvVolumeSize" 
            },
            xml_node
        )
        ebTreeNode(
            {
                "text": edv.device_path,
                "tag": "edvDevicePath"
            },
            xml_node
        )

    cluster_xml.mBFS(aStuffCallback=_update_edvs_info, aStuffArgs=None)


def parse_edv_info_from_dict(edv_info: Mapping[str, str]) -> EDVInfo:
    """Parses the information of an EDV volume from a dictionary.

    Input example:
    {
        "volumeid"" "system",
        "volumetype": "system",
        "volumename": "system",
        "volumesizegb": "42",
        "volumedevicepath": "vol_sys_vm1_1608011"
    }

    :param edv_info: Mapping of EDV volume info (like the example above).
    :returns: EDVInfo
    """
    size_str: str = edv_info.get('volumesizegb', '')
    size: int = int(size_str) * GIB if size_str.strip() else 0

    return EDVInfo(edv_info.get('volumeid', ''),
                   edv_info['volumetype'],
                   edv_info.get('volumename', ''),
                   size,
                   edv_info['volumedevicepath'],
                   EDVState(edv_info.get('volumestatus', "not_checked")))


def convert_edv_info_to_dict(edv_info: EDVInfo) -> Dict[str, str]:
    """Converts an EDV info structure to a dictionary.

    Output example:
    {
        "volumeid"" "system",
        "volumetype": "system",
        "volumename": "system",
        "volumesizegb": "42",
        "volumedevicepath": "vol_sys_vm1_1608011",
        "volumestatus": "attached_guest"
    }

    :param edv_info: EDVInfo
    :returns: Mapping of EDV volume info (like the example above).
    """
    return { 'volumeid': edv_info.vol_id,
             'volumetype': edv_info.vol_type,
             'volumename': edv_info.name,
             'volumesizegb': str(math.ceil(edv_info.size_bytes / GIB)),
             'volumedevicepath': edv_info.device_path,
             'volumestatus': edv_info.state.value }


def get_hosts_edv_from_cs_payload(
        payload: dict) -> Dict[str, Dict[str, List[EDVInfo]]]:
    """Extracts the EDV volumes info from a Create Service or Add Node payload.

    Input example for Create Service:
    {
      "customer_network": {
        "nodes": [
          {
            "fqdn": "sea201605exdd010.sea2xx2xx0051qf.adminsea2.oraclevcn.com",
            "client": {
              "hostname": "edvtest-otpiq1-7661",
              "domainname": "exacsx8mtest.bemeng.oraclevcn.com",
              "dom0_oracle_name": "sea201605exdd010"
            },
            "volumes": [
              "volumedevicepath": "vol_u02_vm1_1605010",
              "volumeid": "",
              "volumename": "",
              "volumesizegb": "",
              "volumetype": "u02"
            ]
          }
        ]
      }
    }

    Input Example for Add Node:
    {
      "reshaped_node_subset": {
        "added_computes": [
          {
            "compute_node_hostname": "sea201605exdd010.sea2xx2xx0051qf.adminsea2.oraclevcn.com",
            "virtual_compute_info": {
              "compute_node_hostname": "edvtest-otpiq1-7661.exacsx8mtest.bemeng.oraclevcn.com"
            },
            "volumes": [
              "volumedevicepath": "vol_u02_vm1_1605010",
              "volumeid": "",
              "volumename": "",
              "volumesizegb": "",
              "volumetype": "u02"
            ]
          }
        ]
      }
    }

    :param payload: Exacloud Create Service payload.
    :returns: Mapping of Host -> Guest -> [EDV volumes]
    """
    return {
        node['fqdn'] if "fqdn" in node else node['client']['dom0_oracle_name']:{
            f"{node['client']['hostname']}.{node['client']['domainname']}": [
                parse_edv_info_from_dict(edv) for edv in node['volumes']
            ]
        } for node in payload['customer_network']['nodes']
    } if 'customer_network' in payload else {
        node['compute_node_hostname']: {
            node['virtual_compute_info']['compute_node_hostname']: [
                parse_edv_info_from_dict(edv) for edv in node['volumes']
            ]
        } for node in payload['reshaped_node_subset']['added_computes']
    }


def get_hosts_edv_from_payload(
        payload: dict) -> Dict[str, Dict[str, List[EDVInfo]]]:
    """Extracts the EDV volumes info from the entire payload.

    Input example:
    {
        "edv_volumes": {
            "sea201605exdd009.sea2xx2xx0051qf.adminsea2.oraclevcn.com": {
                "clu01-9td1b2.dbqadataad2.dbqavcn.oraclevcn.com": [
                    {
                        "volumetype": "system",
                        "volumename": "system",
                        "volumedevicepath": "vol_sys_vm1_1608011"
                    }
                ]
            }
        }
    }

    :param payload: Exacloud request payload.
    :returns: Mapping of Host -> Guest -> [EDV volumes]
    """
    return {
        host: {
            guest: [ parse_edv_info_from_dict(edv) for edv in edvs ]
            for guest, edvs in guests.items()
        } for host, guests in payload.get('edv_volumes', {}).items()
    }


def build_hosts_edv_json(
        hosts_edv: Mapping[str, Mapping[str, List[EDVInfo]]]) -> dict:
    """Builds a JSON serializable dictionary from a hosts EDV volumes info.

    Output example:
    {
        "edv_volumes": {
            "sea201605exdd009.sea2xx2xx0051qf.adminsea2.oraclevcn.com": {
                "clu01-9td1b2.dbqadataad2.dbqavcn.oraclevcn.com": [
                    {
                        "volumetype": "system",
                        "volumename": "system",
                        "volumedevicepath": "vol_sys_vm1_1608011",
                        "volumestatus": "attached_guest"
                    }
                ]
            }
        }
    }

    :param hosts_edv: Mapping of Host -> Guest -> [EDV volumes]
    :returns: JSON serializable dictionary (like the example above).
    """
    return {
        'edv_volumes': {
            host: {
                guest: [ convert_edv_info_to_dict(edv) for edv in edvs ]
                for guest, edvs in guests.items()
            } for host, guests in hosts_edv.items()
        }
    }



#########################
### READ-ONLY METHODS ###
#########################


def get_guest_edv_state(
        host: exaBoxNode,
        guest_xml: Optional[str],
        edvs: Sequence[EDVInfo]) -> List[EDVInfo]:
    """Updates the state of the guest EDV volumes of a given host.

    :param host: Host node.
    :param guest_xml: Guest XML definition if any.
    :param edvs: List of EDV volumes info for a given guest.
    :returns: List of EDV volumes info with status updated.
    """

    edvs_state: List[EDVInfo] = []
    for edv in edvs:

        edv_block: Optional[SFTPAttributes] = None
        edv_paths: List[str] = [ edv.device_path,
                                 f"/dev/exc/{edv.device_path}" ]
        for edv_path in edv_paths:
            edv_block = host.mGetFileInfo(edv_path)
            if edv_block is not None:
                edv = edv._replace(device_path=edv_path)
                break
        if edv_block is None:
            edvs_state.append(edv._replace(state=EDVState.NOT_MOUNTED))
            continue

        if not stat.S_ISBLK(edv_block.st_mode):
            edvs_state.append(edv._replace(state=EDVState.BAD_VOLUME))
            continue

        if guest_xml is None:
            edvs_state.append(edv._replace(state=EDVState.MOUNTED_HOST))
            continue

        if edv.device_path not in guest_xml:
            edvs_state.append(edv._replace(state=EDVState.NOT_ATTACHED))
            continue

        edvs_state.append(edv._replace(state=EDVState.ATTACHED_GUEST))

    return edvs_state


def get_host_edv_state(
        host: exaBoxNode,
        guests_edv: Mapping[str, Sequence[EDVInfo]]
        ) -> Dict[str, List[EDVInfo]]:
    """Updates the state of the guests EDV volumes of a given host.

    :param host: Host node.
    :param guests_edv: Mapping of Guest -> [EDV volumes]
    :returns: Mapping of Guest -> [EDV volumes]
    """

    response: Dict[str, List[EDVInfo]] = {}
    for guest, edvs in guests_edv.items():

        # Get VM definition schema if it exists.
        guest_xml: Optional[str] = None
        VIRSH: str = node_cmd_abs_path_check(host, 'virsh')
        cmd: str = f"{VIRSH} dumpxml {guest}"
        guest_xml_res = node_exec_cmd(host, cmd)

        if guest_xml_res.exit_code == 0:
            guest_xml = guest_xml_res.stdout

        response[guest] = get_guest_edv_state(host, guest_xml, edvs)

    return response


def get_hosts_edv_state(
        hosts_edv: Mapping[str, Mapping[str, Sequence[EDVInfo]]]
        ) -> Dict[str, Dict[str, List[EDVInfo]]]:
    """Obtains the current state of the EDV volumes.

    :param volumes: Mapping of: Host -> Guest -> [EDV volumes]
    :returns: Mapping of: Host -> Guest -> [EDV volumes]
    """

    response: Dict[str, Dict[str, List[EDVState]]] = {}
    for host, guests_edv in hosts_edv.items():
        with connect_to_host(host, get_gcontext()) as node:
            response[host] = get_host_edv_state(node, guests_edv)

    return response



########################
### ALTERING METHODS ###
########################


def unmount_stale_gcv_edv(host: exaBoxNode) -> List[ebNodeFilesystemInfo]:
    """Obtains and unmounts the GCV EDVs that are not linked to any guest.

    :param host: Host node.
    :returns: List of ebNodeFilesystemInfo unmounted.
    """

    # Get the host filesystems
    filesystems: List[ebNodeFilesystemInfo] = get_node_filesystems(host)

    # Get the guests installed in this host
    VIRSH: str = node_cmd_abs_path_check(host, 'virsh')
    cmd: str = f"{VIRSH} list --all --name"
    guests: List[str] = \
        [ vm.strip()
         for vm in node_exec_cmd_check(host, cmd).stdout.splitlines()
         if vm.strip() ]

    # Calculate the filesystems corresponding to mounted stale EDVs
    stale_edvs_fs: List[ebNodeFilesystemInfo] = \
        [ fs for fs in filesystems
          if fs.device.startswith('/dev/exc/') and \
            fs.mountpoint.startswith('/EXAVMIMAGES/GuestImages/') and \
            not any(map(fs.mountpoint.endswith, guests)) ]

    # Unmount the stale EDVs
    UMOUNT: str = node_cmd_abs_path_check(host, 'umount')
    SED: str = node_cmd_abs_path_check(host, 'sed')
    for fs in stale_edvs_fs:
        cmd: str = f"{UMOUNT} {fs.mountpoint}"
        node_exec_cmd_check(host, cmd)
        cmd = f"{SED} -i '\\@{fs.mountpoint}@d' /etc/fstab"
        node_exec_cmd_check(host, cmd)
        ebLogWarn(f"*** Unmounted stale GCV EDV from {fs.mountpoint} "
                  f"from device {fs.device}")

    return stale_edvs_fs



###########################
### ENDPOINT ENTRYPOINT ###
###########################


def perform_edv_action(action: EDVAction, options: object) -> dict:
    """Entrypoint for performing any EDV action.

    :param action: EDVAction.
    :param options: Exacloud options object with Payload object.
    :returns: JSON serializable dictionary depending on the action performed.
    """

    # Read JSON Payload
    if options.jsonconf is None:
        msg: str = 'Please specify a JSON Payload.'
        raise ExacloudRuntimeError(0x10, 0xA, msg)

    payload: dict = options.jsonconf
    if 'edv_volumes' not in payload:
        msg: str = 'Please include "edv_volumes" in Payload.'
        raise ExacloudRuntimeError(0x10, 0xA, msg)

    hosts_edv: Dict[str, Dict[str, List[EDVInfo]]] = \
        get_hosts_edv_from_payload(payload)


    # Perform action
    response: dict = {}
    if action == EDVAction.PRECHECK:
        ebLogInfo('*** EDV: Performing EDV volumes pre-checks... ***')
        hosts_edv_state = get_hosts_edv_state(hosts_edv)
        response = build_hosts_edv_json(hosts_edv_state)
        ebLogInfo('*** EDV: Finished EDV volumes pre-checks successfully ***')

    return response
