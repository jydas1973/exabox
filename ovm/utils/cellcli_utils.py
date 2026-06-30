#!/bin/python
#
# $Header: cellcli_utils.py 15-may-2026.19:43:50 pbellary Exp $
#
# cellcli_utils.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      cellcli_utils.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    rajsag      05/29/26 - Bug 39283211 - support X11 no-XRMEM cell types
#    pbellary    05/15/26 - Bug 39238514 - X11M:ADD CELL SUPPORT FOR EXASCALE WITH EF MEDIA TYPE
#    pbellary    05/15/26 - Creation
#

import re

from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.core.Error import ebError, ExacloudRuntimeError, gReshapeError, gExascaleError
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogVerbose, ebLogTrace
from exabox.utils.node import connect_to_host, node_cmd_abs_path_check, node_exec_cmd, node_exec_cmd_check, node_read_text_file, node_write_text_file

X11_HC_NOXRMEM_MACHINE_TYPE = "X11MHCNOXRMEM"
X11_EF_NOXRMEM_MACHINE_TYPE = "X11MEFNOXRMEM"
X11_NOXRMEM_ONLINE_MEMORY_LIMIT_GB = 270
_X11_NOXRMEM_MACHINE_TYPES = {
    "HC": X11_HC_NOXRMEM_MACHINE_TYPE,
    "EF": X11_EF_NOXRMEM_MACHINE_TYPE
}


class ebCellCliUtils(object):

    def __init__(self, aCluCtrlObj):
        self.__cluctrl = aCluCtrlObj

    def mIsEFRack(self, aCell):
        _cell = aCell
        _ebox = self.__cluctrl
        _cmdstr = 'cellcli -e LIST CELLDISK WHERE name LIKE \\"CF_.*\\" attributes name;'
        with connect_to_host(_cell, get_gcontext()) as _node:
            ebLogInfo(f"*** Executing the command - {_cmdstr} on cell - {_cell}.")
            _i, _o, _e = _node.mExecuteCmd(_cmdstr)
            if _node.mGetCmdExitStatus():
                _msg = f'Unable to execute {_cmdstr}: CMD_OUT: {_o.read()}, _ERR: {_e.read()}'
                ebLogError(_msg)
                _ebox.mUpdateErrorObject(gExascaleError["CELLCLI_CMD_FAILED"], _msg)
                raise ExacloudRuntimeError(0x0825, 0xA, _msg)
            _output = _o.readlines()
            if _output:
                ebLogTrace("*** cellcli Output - %s" % _output)
                return True
        return False

    def mGetCellRackItemDescription(self, aCell):
        _cell = aCell
        _ebox = self.__cluctrl

        try:
            _cell_mac = _ebox.mGetMachines().mGetMachineConfig(_cell)
            if not _cell_mac:
                ebLogWarn(f'*** Unable to find machine config for cell {_cell}.')
                return ""

            _cell_id = _cell_mac.mGetMacId()
            _rack_item = _ebox.mGetEsracks().mGetEsRackItem(_cell_id)
            if not _rack_item:
                ebLogWarn(f'*** Unable to find rack item for cell {_cell}.')
                return ""

            _rack_item_desc = _rack_item.mGetEsRackItemDesc()
            ebLogInfo(f'*** Cell {_cell} rack item description: {_rack_item_desc}')
            return _rack_item_desc or ""
        except Exception as ex:
            ebLogWarn(f'*** Unable to retrieve rack item description for cell {_cell}: {ex}')
            return ""

    def mGetNoXrmemMachineTypeFromDescription(self, aRackItemDescription):
        if not aRackItemDescription:
            return ""

        _rack_item_desc = str(aRackItemDescription).upper()
        if "X11M-" in _rack_item_desc:
            return ""

        _match = re.search(r'\bX11-(HC|EF)\b', _rack_item_desc)
        if not _match:
            return ""

        return _X11_NOXRMEM_MACHINE_TYPES.get(_match.group(1), "")

    def mParseOnlineMemoryGb(self, aMemoryOutput):
        _output = aMemoryOutput
        if isinstance(_output, (list, tuple)):
            _output = "\n".join([str(_line).strip() for _line in _output])
        else:
            _output = str(_output).strip()

        _memory_line = ""
        for _line in _output.splitlines():
            if "Total online memory" in _line:
                _memory_line = _line
                break
        if not _memory_line:
            _memory_line = _output

        _memory_value = _memory_line.split(":", 1)[-1].strip()
        _match = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*([A-Za-z]*)', _memory_value)
        if not _match:
            raise ValueError(f"Invalid lsmem online memory output: {_output}")

        _value = float(_match.group(1))
        _unit = _match.group(2).upper()
        if _unit in ["", "B", "BYTE", "BYTES"]:
            _memory_bytes = _value
        elif _unit in ["K", "KB", "KIB"]:
            _memory_bytes = _value * 1024
        elif _unit in ["M", "MB", "MIB"]:
            _memory_bytes = _value * 1024 ** 2
        elif _unit in ["G", "GB", "GIB"]:
            _memory_bytes = _value * 1024 ** 3
        elif _unit in ["T", "TB", "TIB"]:
            _memory_bytes = _value * 1024 ** 4
        else:
            raise ValueError(f"Unsupported lsmem online memory unit '{_unit}' in output: {_output}")

        return _memory_bytes / float(1024 ** 3)

    def mGetCellOnlineMemoryGb(self, aCell):
        _cell = aCell
        _ebox = self.__cluctrl
        _cmdstr = "/usr/bin/lsmem -b | /bin/grep 'Total online memory'"

        with connect_to_host(_cell, get_gcontext()) as _node:
            ebLogInfo(f"*** Executing the command - {_cmdstr} on cell - {_cell}.")
            _i, _o, _e = _node.mExecuteCmd(_cmdstr)
            _output = _o.readlines() if _o else []
            _error = _e.read() if _e else ""
            if _node.mGetCmdExitStatus():
                _msg = f'Unable to execute {_cmdstr}: CMD_OUT: {_output}, _ERR: {_error}'
                ebLogError(_msg)
                _ebox.mUpdateErrorObject(gExascaleError["CELL_MEMORY_CHECK_FAILED"], _msg)
                raise ExacloudRuntimeError(0x0825, 0xA, _msg)

        try:
            return self.mParseOnlineMemoryGb(_output)
        except Exception as ex:
            _msg = f"Unable to parse online memory for cell {_cell}: {ex}"
            ebLogError(_msg)
            _ebox.mUpdateErrorObject(gExascaleError["CELL_MEMORY_CHECK_FAILED"], _msg)
            raise ExacloudRuntimeError(0x0825, 0xA, _msg)

    def mValidateX11NoXrmemMemory(self, aCell):
        _cell = aCell
        _ret = True
        _online_memory_gb = self.mGetCellOnlineMemoryGb(_cell)
        ebLogInfo(f"*** Cell {_cell} online memory: {_online_memory_gb:.2f}GB")
        if _online_memory_gb > X11_NOXRMEM_ONLINE_MEMORY_LIMIT_GB:
            _msg = (
                f"Cell {_cell} is identified as X11 no-XRMEM but online memory "
                f"{_online_memory_gb:.2f}GB exceeds {X11_NOXRMEM_ONLINE_MEMORY_LIMIT_GB}GB"
            )
            ebLogError(_msg)
            _ret = False
        return _ret
    def mGetX11NoXrmemMachineType(self, aCell, aRackItemDescription=None, aCellType=None):
        _cell = aCell
        for _cell_type_hint in [aRackItemDescription, aCellType]:
            _machine_type = self.mGetNoXrmemMachineTypeFromDescription(_cell_type_hint)
            if _machine_type and self.mValidateX11NoXrmemMemory(_cell):
                return _machine_type

        _rack_item_desc = self.mGetCellRackItemDescription(_cell)
        _machine_type = self.mGetNoXrmemMachineTypeFromDescription(_rack_item_desc)
        if _machine_type and self.mValidateX11NoXrmemMemory(_cell):
            return _machine_type
        return ""

    def mGetMachineType(self, aCell, aRackItemDescription=None, aCellType=None):
        _cell = aCell
        _ebox = self.__cluctrl
        _machine_type = ""

        _machine_type = self.mGetX11NoXrmemMachineType(_cell, aRackItemDescription, aCellType)
        if _machine_type:
            return _machine_type

        _exadata_model = _ebox.mGetExadataDom0Model(_cell)
        _ef_rack = self.mIsEFRack(_cell)
        if _ef_rack and _exadata_model == 'X11':
            _machine_type = "X11MEF"
        elif _ef_rack and _exadata_model == 'X10':
            _machine_type = "X10MEF"
        return _machine_type
