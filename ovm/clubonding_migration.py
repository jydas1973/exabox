#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/clubonding_migration.py /main/1 2022/07/28 07:14:38 scoral Exp $
#
# clubonding_migration.py
#
# Copyright (c) 2022, Oracle and/or its affiliates.
#
#    NAME
#      clubonding_migration.py - Bonding migration utilities.
#
#    DESCRIPTION
#      This module contains utilities for bonding migration such as the
#      migration prechecks.
#
#    NOTES
#      Most of the relevant logic for bonding migration is still contained in
#      clunetupdate.py
#
#    MODIFIED   (MM/DD/YY)
#    scoral      07/20/22 - Creation
#

from typing import TYPE_CHECKING, List, Mapping, Optional, Sequence

from exabox.ovm.clubonding_config import Payload
from exabox.utils.common import build_dict_from_table
from exabox.utils.node import (
    connect_to_host, node_exec_cmd, node_exec_cmd_check
)
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogInfo, ebLogError, ebLogTrace, ebLogWarn
from exabox.core.Error import ExacloudRuntimeError


if TYPE_CHECKING:
    from exabox.ovm.clucontrol import exaBoxCluCtrl
else:
    exaBoxCluCtrl = object  # pylint: disable=invalid-name



CELLCLI = "/opt/oracle/cell/cellsrv/bin/cellcli"



def get_griddisks_info(
        node: exaBoxNode,
        attributes: List[str] = ('ASMDeactivationOutcome', 'ASMModeStatus')
        ) -> Mapping[str, Mapping[str, str]]:
    """Gets a dictionary with the info of all the grid disks for a given cell.

    Example dictionary returned:

    {
        'DATAC1_CD_00_sea201507exdcl04': {
            'ASMDeactivationOutcome': 'Yes',
            'ASMModeStatus': 'ONLINE'
        },
        'DATAC1_CD_01_sea201507exdcl04': {
            'ASMDeactivationOutcome': 'No',
            'ASMModeStatus': 'OFFLINE'
        },
        'DATAC1_CD_02_sea201507exdcl04': {
            'ASMDeactivationOutcome': 'Yes',
            'ASMModeStatus': 'SYNC'
        },
        ...
    }

    :param node: cell node.
    :param attributes: list of attributes to obtain.
    :returns: grid disks info.
    """
    cmd: str = (
        f'{CELLCLI} -e list griddisk attributes '
        f'name,{",".join(attributes)}'
    )
    _, out, _ = node_exec_cmd_check(node, cmd)
    return build_dict_from_table(out.splitlines(), attributes)


def valid_cell_griddisks(node: exaBoxNode) -> bool:
    """Validate the grid disks status for potential data loss.

    According to the following article:
    https://www.oracle.com/technical-resources/articles/enterprise-manager/exadata-commands-part3.html

    If any grid disk in a cell has the ASMDeactivationOutcome property set to
    No, and the ASMModeStatus property is other than ONLINE or SYNC, there
    could potentially be data loss. So we verify that is not the case in this
    method.

    :param node: cell node.
    :returns: a boolean which indicates if the grid disks are ok.
    """
    result: bool = True
    griddisks: Mapping[str, Mapping[str, str]] = get_griddisks_info(node)
    for griddisk, properties in griddisks.items():
        asm_status: Optional[str] = properties.get('ASMModeStatus')
        asm_deactivable: Optional[str] = \
            properties.get('ASMDeactivationOutcome')

        if asm_status.upper() in ('ONLINE', 'SYNC'):
            continue

        msg: str = (
            f'Grid Disk {griddisk} in Cell {node.mGetHostname()} '
            f'ASMModeStatus is {asm_status}'
        )

        if asm_deactivable.upper() == 'YES':
            ebLogWarn(f'{msg}.')
        else:
            ebLogError(
                f'{msg} but ASMDeactivationOutcome is {asm_deactivable} '
                'which could potentially lead to data loss!'
            )
            result = False

    return result


def bonding_migration_prechecks(
        cluctrl: exaBoxCluCtrl,
        payload: Payload) -> None:
    """Performs the bonding migration prechecks a given cluster.

    Performs a series of tests to make sure the bonding migration will (have
    higher chances to) succeed.
    Currently we validate the state of the grid disks of the cells of the
    cluster to make sure the ASM is in a good state. See valid_cell_griddisks

    :param cluctrl: cluster object.
    :param payload: bonding migration prechecks payload.
    :returns: nothing.
    :raises ExacloudRuntimeError: if an error occurred.
    """
    ebLogInfo(f'BONDING: Starting Bonding migration prechecks.')
    ctx = cluctrl.mGetCtx()
    good: bool = True

    for cell in cluctrl.mReturnCellNodes():
        with connect_to_host(cell, ctx) as node:
            if not valid_cell_griddisks(node):
                good = False

    if not good:
        msg: str = ('Errors occurred, it is strongly recommended to attend '
                    'these issues before proceeding with Bonding migration.')
        ebLogError(msg)
        raise ExacloudRuntimeError(0x804, 0xA, msg)

    ebLogInfo(f'BONDING: Bonding migration prechecks finished successfully.')
