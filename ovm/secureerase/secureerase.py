#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/secureerase/secureerase.py /main/3 2024/12/06 04:46:57 aararora Exp $
#
# secureerase.py
#
# Copyright (c) 2024, Oracle and/or its affiliates.
#
#    NAME
#      secureerase.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aararora    11/25/24 - Bug 37067118: Use cellcli drop command for
#                           performing secure erase.
#    aararora    09/10/24 - Bug 37041670: Provide list of serial numbers for
#                           secure erase
#    aararora    08/06/24 - ER 36904128: Add API for secure erase
#    aararora    08/06/24 - Creation
#
import os
from exabox.core.DBStore import ebGetDefaultDB
from exabox.utils.common import version_compare
from exabox.utils.node import node_cmd_abs_path_check
from exabox.core.Error import ExacloudRuntimeError
from exabox.log.LogMgr import ebLogError, ebLogInfo
from base64 import b64encode

from datetime import datetime

class SecureErase(object):

    def __init__(self, aExaBoxCluCtrl):
        self.__cluctrl = aExaBoxCluCtrl

    def mSerializeData(self, aNode, aHtmlLocation):
        _html_file_content = aNode.mReadFile(aHtmlLocation)
        _enc_base64_data = b64encode(_html_file_content)
        _str_encoded_data = _enc_base64_data.decode('utf-8')
        return _str_encoded_data

    def mGetPhysicalCellDisks(self, aNode, aType):
        """
        Get physicals disks from the cell based on type
        """
        _node = aNode
        _type = aType
        _cmdstr = f"cellcli -e LIST CELLDISK ATTRIBUTES physicalDisk where diskType='{_type}'"
        _, _o, _e = _node.mExecuteCmdCellcli(_cmdstr)
        if _node.mGetCmdExitStatus():
            ebLogError(f'*** CMD_OUT: {_o.read()}, _ERR: {_e.read()}')
            raise ExacloudRuntimeError(0x0825, 0xA, f'mExecuteCmd Failed on {_node.mGetHostname()}, with cmd: {_cmdstr}')
        
        physicalDisks = []
        for _line in _o.readlines():
            # For flashdisks, there can be comma separated serial numbers present here
            _disks = _line.strip()
            if _disks:
                _disks = _disks.split(',')
                physicalDisks.extend(_disks)
        ebLogInfo(f'Physical disks obtained for {_type} are: {physicalDisks}.')
        return physicalDisks

    def mGetSerialNumbersDisks(self, aNode, aAbsolutePathPython, aFlashDisks, aHardDisks):
        """
        Get comma separated serial numbers of the disks
        """
        _node = aNode
        _python = aAbsolutePathPython
        _flashdisks = aFlashDisks
        _harddisks = aHardDisks
        # Below command is to get serial number of each hdd
        _cmd_list_hdds = f"{_python} /opt/oracle.cellos/lib/python/secureeraser --list --hdd "\
                          "| awk '{ print $4 }' | tail -n +2"
        _i, _o, _e = _node.mExecuteCmd(_cmd_list_hdds)
        if _node.mGetCmdExitStatus():
            ebLogError(f'*** CMD_OUT: {_o.read()}, _ERR: {_e.read()}')
            raise ExacloudRuntimeError(0x0825, 0xA, f'mExecuteCmd Failed on {_node.mGetHostname()}, with cmd: {_cmd_list_hdds}')
        _hdd_list_secureeraser = []
        for _line in _o.readlines():
            _disk = _line.strip()
            if _disk:
                _hdd_list_secureeraser.append(_disk)
        ebLogInfo(f"HDD List from secureeraser command are: {_hdd_list_secureeraser}.")
        _final_hdd_list = []
        for _disk in _harddisks:
            for _serial_number in _hdd_list_secureeraser:
                if _disk in _serial_number:
                    _final_hdd_list.append(_serial_number)
                    break
        _final_disk_list = _flashdisks + _final_hdd_list
        return ','.join(_final_disk_list)

    def mSecureEraseCertificate(self, aCellName, aNode, aExadataImage, aCertDict, aFlashDisks, aHardDisks):
        """
        Utility method for securely erasing a cell and generating/copying the certificate to exacloud node
        """
        _cell_name = aCellName
        _cert_dict = aCertDict
        _flashdisks = aFlashDisks
        _harddisks = aHardDisks
        _node = aNode
        _exadataImage = aExadataImage
        _cert_path = self.__cluctrl.mCheckConfigOption('secure_erase_cert_path')
        _technician_cert = self.__cluctrl.mCheckConfigOption('technician_name_cert')
        _witness_cert = self.__cluctrl.mCheckConfigOption('witness_name_cert')
        _serialized_cert_content = None
        # If exadata image version is greater than or equal to 19.1.0, secureeraser command
        # with crypto option is supported. If crypto is not supported, default erasure method will be used
        if version_compare(_exadataImage, "19.1.0") >= 0:
            ebLogInfo(f'Securely erasing flash disks and harddisks on cell {_cell_name}.')
            _python_abs_path = node_cmd_abs_path_check(_node, "python")
            _cert_id = self.__cluctrl.mGenerateUUID()
            _cert_path = os.path.join(_cert_path, _cert_id)
            if not _node.mFileExists(_cert_path):
                _node.mExecuteCmdLog(f"/bin/mkdir -p {_cert_path}")
            _serial_list = self.mGetSerialNumbersDisks(_node, _python_abs_path, _flashdisks, _harddisks)
            _cmd_secureerase = f"{_python_abs_path} /opt/oracle.cellos/lib/python/secureeraser --erase --erasure_method_optional"\
                f" --devices_to_erase {_serial_list} --flash_erasure_method=crypto --hdd_erasure_method=crypto --output={_cert_path} --quiet --technician={_technician_cert}"\
                f" --witness={_witness_cert}"
            _node.mExecuteCmdLog(_cmd_secureerase)
            if _node.mGetCmdExitStatus() != 0:
                _msg = f"ERROR: There was an issue while performing secure erase on cell {_cell_name}."
                ebLogError(_msg)
                _node.mExecuteCmdLog(f"/usr/bin/rm -rf {_cert_path}")
                _cert_dict[_cell_name] = _msg
                raise ExacloudRuntimeError(aErrorMsg=_msg)
            ebLogInfo(f'Flash disks and hard disks are securely erased. Certificate path on the cell {_cell_name} is {_cert_path}.')
            _ls_cmd_html_cert = f"/usr/bin/ls {_cert_path}/*.html"
            _stdin, _stdout, _stderr = _node.mExecuteCmd(_ls_cmd_html_cert)
            _rc = _node.mGetCmdExitStatus()
            if _rc != 0:
                _msg = f"ERROR: We could not find the html certificate on the cell {_cell_name} under path {_cert_path}. Please check the path on the cell."
                ebLogError(_msg)
                _cert_dict[_cell_name] = _msg
            else:
                try:
                    _out = _stdout.read().strip()
                    _serialized_cert_content = self.mSerializeData(_node, _out)
                    # Remove the certificate path on the cell after reading the certificate in exacloud
                    _node.mExecuteCmdLog(f"/usr/bin/rm -rf {_cert_path}")
                    _cert_dict[_cell_name] = _serialized_cert_content
                except Exception as ex:
                    _msg = f"ERROR: Could not serialize secure erase certificate. Certificate will be available on the cell at {_cert_path}. Error: {ex}."
                    ebLogError(_msg)
                    _cert_dict[_cell_name] = _msg

    def mSecureEraseUseCellcli(self, aCellName, aNode, aCertDict):
        """
        Utility method for securely erasing a cell using cellcli drop command and 
        generating/copying the certificate to exacloud node
        """
        _cell_name = aCellName
        _cert_dict = aCertDict
        _node = aNode
        _serialized_cert_content = None
        ebLogInfo(f'Securely erasing flash disks and harddisks on cell {_cell_name} using cellcli drop command.')
        _cert_path = self.__cluctrl.mCheckConfigOption("secure_erase_cert_path_using_cellcli")
        if not _node.mFileExists(_cert_path):
            _node.mExecuteCmdLog(f"/bin/mkdir -p {_cert_path}")
        _stdin, _stdout, _stderr = _node.mExecuteCmd("/bin/date +%s")
        _current_timestamp = int(_stdout.read().strip())
        # According to discussion with exadata team, this will call crypto erasure in the background
        # i.e. secureeraser command will be called
        _cmd_secureerase = f"cellcli -e DROP CELLDISK ALL ERASE=7pass"
        _node.mExecuteCmdLog(_cmd_secureerase)
        if _node.mGetCmdExitStatus() != 0:
            _msg = f"ERROR: There was an issue while performing secure erase on cell {_cell_name}."
            ebLogError(_msg)
            _cert_dict[_cell_name] = _msg
            raise ExacloudRuntimeError(aErrorMsg=_msg)
        _stdin, _stdout, _stderr = _node.mExecuteCmd(f"/bin/ls -Art {_cert_path}/secureeraser*cert*.html | tail -n 1")
        if _node.mGetCmdExitStatus() != 0:
            _msg = f"ERROR: We could not find the html certificate on the cell {_cell_name} under path {_cert_path}. Please check the path on the cell."
            ebLogError(_msg)
            _cert_dict[_cell_name] = _msg
            return
        _cert_generated = _stdout.read().strip()
        _stdin, _stdout, _stderr = _node.mExecuteCmd(f"/bin/stat -c '%Y' {_cert_generated}")
        if _node.mGetCmdExitStatus() != 0:
            _msg = f"ERROR: We could stat the html certificate on the cell {_cell_name} under path {_cert_path}. Please check the path on the cell."
            ebLogError(_msg)
            _cert_dict[_cell_name] = _msg
            return
        _certificate_timestamp = int(_stdout.read().strip())
        ebLogInfo(f'Flash disks and hard disks are securely erased. Certificate path on the cell {_cell_name} is {_cert_generated}.')
        if _certificate_timestamp < _current_timestamp:
            _msg = f"ERROR: We could not find the html certificate on the cell {_cell_name} under path {_cert_path}. Please check the path on the cell."
            ebLogError(_msg)
            _cert_dict[_cell_name] = _msg
        else:
            try:
                _serialized_cert_content = self.mSerializeData(_node, _cert_generated)
                _cert_dict[_cell_name] = _serialized_cert_content
            except Exception as ex:
                _msg = f"ERROR: Could not serialize secure erase certificate. Certificate will be available on the cell at {_cert_generated}. Error: {ex}."
                ebLogError(_msg)
                _cert_dict[_cell_name] = _msg