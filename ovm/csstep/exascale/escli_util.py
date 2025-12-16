#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/ovm/csstep/exascale/escli_util.py /main/13 2025/11/25 09:58:54 rajsag Exp $
#
# escli_util.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      ebEscliUtils - escli Utility file for escli commands
#
#    DESCRIPTION
#      Implements utilities for escli commands
#
#    NOTES
#      NONE
#
#    MODIFIED   (MM/DD/YY)
#    rajsag      11/20/25 - bug 38673238 - exacloud: vm backup xs migration
#                           failed valueerror: could not convert string to
#                           float
#    scoral      11/13/25 - Bug 38648866 - Make mGetVolumeID support
#                           "vmbackup_restore" EDV volumes.
#    jfsaldan    08/26/25 - Enh 37999800 - EXACLOUD: EXASCALE CONFIG FLOW TO
#                           ENABLE AUTOFILEENCRYPTION=TRUE AFTER EXASCALE IS
#                           CONFIGURED.
#    rajsag      07/25/25 - Enhancement Request 37966939 - exascale vm image &
#                           vm backup vault operations   
#    rajsag      07/08/25 - 38147574 - exacloud: xs pool size not syncing after
#                           xs configure/update w/f
#    pbellary    06/06/25 - Enh 38035467 - EXASCALE: EXACLOUD TO PROVIDE ACFS FILE SYSTEM SIZES IN SYNCH CALL
#    pbellary    06/06/25 - Enh 37768130 - SUPPORT RESHAPE/RESIZE FOR THE ACFS FILESYSTEM CREATED ON EXASCALE CLUSTERS 
#    pbellary    05/26/25 - Enh 37768130 - SUPPORT RESHAPE/RESIZE FOR THE ACFS FILESYSTEM CREATED ON EXASCALE CLUSTERS 
#    pbellary    05/21/25 - Enh 37927692 - EXASCALE: EXACLOUD TO SUPPORT CREATION OF EDV FOR /U02 FOR THE VM IMAGE ON EDV (IMAGE VAULT)
#    pbellary    05/21/25 - Enh 37698277 - EXASCALE: CREATE SERVICE FLOW TO SUPPORT VM STORAGE ON EDV OF IMAGE VAULT 
#    pbellary    04/16/25 - Enh 37842812 - EXASCALE: REFACTOR ACFS CREATION DURING CREATE SERVICE
#    pbellary    04/16/25 - Creation
#

import re
import os
import json
import defusedxml.ElementTree as ET
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.core.DBStore import ebGetDefaultDB
from exabox.ovm.cluconfig import ebCluExascaleConfig
from exabox.core.Error import ebError, ExacloudRuntimeError, gReshapeError, gExascaleError
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogVerbose, ebLogTrace
from exabox.utils.node import connect_to_host, node_cmd_abs_path_check, node_exec_cmd, node_exec_cmd_check, node_read_text_file, node_write_text_file

ESCLI       = "/opt/oracle/cell/cellsrv/bin/escli"
WALLET_LOC  = "/opt/oracle/cell/cellsrv/deploy/config/security/admwallet"
CTRL_PORT   = "5052"

class ebEscliUtils(object):

    def __init__(self, aCluCtrlObj):
        self.__cluctrl = aCluCtrlObj

    def mUpdateRequestData(self, rc, aData, err):
        """
        Updates request object with the response payload
        """
        _reqobj = self.__cluctrl.mGetRequestObj()
        _response = {}
        _response["success"] = "True" if (rc == 0) else "False"
        _response["error"] = err
        _response["output"] = aData
        if _reqobj is not None:
            _db = ebGetDefaultDB()
            _reqobj.mSetData(json.dumps(_response, sort_keys = True))
            _db.mUpdateRequest(_reqobj)

    def mExecuteEscliCmd(self, aCell, aCmd):
        _cell = aCell
        _cmd_str = aCmd
        _ret = 0
        _data_d = {}
        _ebox = self.__cluctrl
        ebLogInfo("*** Executing mExecuteEscliCmd")
        with connect_to_host(_cell, get_gcontext()) as _node:
            if not _node.mFileExists('/opt/oracle/cell/cellsrv/bin/escli'):
                _msg = f'Unable to execute {_cmd_str}, ESCLI path does not exist'
                ebLogError(_msg)
                _ebox.mUpdateErrorObject(gExascaleError["ESCLI_PATH_FAILURE"], _msg)
                self.mUpdateRequestData(_ret, _data_d, _msg)
                raise ExacloudRuntimeError(0x0811, 0xA, _msg)
            return node_exec_cmd(_node, _cmd_str)

    def mParseExascaleAttrib(self, aOptions):
        _exascale_attr = ""
        if aOptions is not None and aOptions.jsonconf is not None and \
            "exascale" in list(aOptions.jsonconf.keys()):
            _exascale_attr = aOptions.jsonconf['exascale']
        elif aOptions is not None and aOptions.jsonconf is not None and \
            "ctrl_network" in list(aOptions.jsonconf.keys()):
            _exascale_attr = aOptions.jsonconf
        elif aOptions is not None and aOptions.jsonconf is not None and \
            "db_vaults" in list(aOptions.jsonconf.keys()):
            _exascale_attr = aOptions.jsonconf['db_vaults'][0]
        return _exascale_attr

    def mIsEFRack(self, aCell):
        _cell = aCell
        _cmdstr = 'cellcli -e LIST CELLDISK WHERE name LIKE \\"CF_.*\\" attributes name;'
        with connect_to_host(_cell, get_gcontext()) as _node:
            ebLogInfo(f"*** Executing the command - {_cmdstr} on cell - {_cell}.")
            _i, _o, _e = _node.mExecuteCmd(_cmdstr)
            _output = _o.readlines()
            if _output:
                ebLogTrace("*** cellcli Output - %s" % _output)
                return True
        return False

    def mGetDBVaultName(self):
        _vault_name = ""
        _ebox = self.__cluctrl
        _patchconfig = _ebox.mGetPatchConfig()
        if _patchconfig and os.path.exists(_patchconfig) and not _ebox.mIsClusterLessXML():
            with open(_patchconfig) as _xmlfile:
                _data = _xmlfile.read()

            _root = ET.fromstring(re.sub('xmlns="\w*"', '', _data))
            _vaults = _root.findall("exascale/vaults/vault")
            for _vault in _vaults:
                _name = _vault.find('name')
                if _name is not None:
                    _vault_name = _name.text
                    ebLogInfo(f"VAULT NAME: {_vault_name}")
                    break
        return _vault_name

    def mGetCtrlIP(self):
        _ipaddress, _ers = "", ""
        _ebox = self.__cluctrl
        try:
            _config = ebCluExascaleConfig(_ebox.mGetConfig())
            _config_list = _config.mGetExascaleClusterConfigList()
            if _config_list:
                _exascale = _config.mGetExascaleClusterConfig(_config_list[0])
                _net_list = _exascale.mGetMacNetworks()
                for _net_id in _net_list:
                    _net_conf = _ebox.mGetNetworks().mGetNetworkConfig(_net_id)
                    _ipaddress = _net_conf.mGetNetIpAddr()
                    _ers = _net_conf.mGetNetHostName() + "." +  _net_conf.mGetNetDomainName()
        except Exception as e:
            ebLogWarn(f"*** mGetCtrlIP failed with Exception: {str(e)}")
        return _ipaddress, _ers

    def mGetERSEndpoint(self, aOptions):
        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mGetERSEndpoint failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT
        ebLogInfo(f"ERS_IP:{_ctrl_ip} ERS_PORT:{_ctrl_port}")
        return _ctrl_ip, _ctrl_port

    def mGetUser(self, aCell, aClusterName, aOptions):
        _ebox = self.__cluctrl
        _cell = aCell
        _clusterName = aClusterName
        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mGetUser failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT
        _giclusterName = ""

        with connect_to_host(_cell, get_gcontext(), username="root") as _node:
            _i, _o, _e = _node.mExecuteCmd(f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} lsuser | /bin/grep {_clusterName}")
            _rc = _node.mGetCmdExitStatus()
            if _rc == 0:
                _lsuser = _o.readlines()
                _giclusterName = _lsuser[0].split()[0].strip()
        ebLogInfo(f"UserId: {_giclusterName} for the Cluster:{_clusterName}")
        return _giclusterName

    def mGetEDVInitiator(self, aCell, aHostName, aOptions):
        _cell = aCell
        _host_name = aHostName
        _initiatorId = ""
        _ebox = self.__cluctrl
        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mGetEDVInitiator failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT
        
        with connect_to_host(_cell, get_gcontext(), username="root") as _node:
            _i, _o, _e = _node.mExecuteCmd(f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} lsinitiator --attributes id,hostName")
            _rc = _node.mGetCmdExitStatus()
            if _rc:
                _err_str = f"{_cell}: Failed to fetch clusterName & clusterID"
                ebLogInfo(_err_str)
                _ebox.mUpdateErrorObject(gExascaleError["GET_CLUSTER_DETAILS_FAILED"], _err_str)
                raise ExacloudRuntimeError(aErrorMsg=_err_str)
            _out = _o.readlines()
            for _ret in _out:
                _output = _ret.split()
                if _output and _host_name == _output[1]:
                    _initiatorId,_ = _output
        ebLogInfo(f"Initiator ID:{_initiatorId} for the host:{_host_name}")
        return _initiatorId

    def mGetClusterID(self, aCell, aOptions):
        _cell = aCell
        _ebox = self.__cluctrl

        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mGetClusterID failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        _giclusterName = ""
        _giClusterId = ""
        _clusterName = _ebox.mGetClusters().mGetCluster().mGetCluName()

        with connect_to_host(_cell, get_gcontext(), username="root") as _node:
            _i, _o, _e = _node.mExecuteCmd(f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} lsinitiator --attributes giClusterName,giClusterId")
            _rc = _node.mGetCmdExitStatus()
            if _rc:
                _err_str = f"{_cell}: Failed to fetch clusterName & clusterID"
                ebLogInfo(_err_str)
                _ebox.mUpdateErrorObject(gExascaleError["GET_CLUSTER_DETAILS_FAILED"], _err_str)
                raise ExacloudRuntimeError(aErrorMsg=_err_str)
            _out = _o.readlines()
            for _ret in _out:
                _output = _ret.split()
                if _output and _clusterName == _output[0]:
                    _giclusterName = self.mGetUser(_cell, _clusterName, aOptions)
                    if _giclusterName:
                        _, _giClusterId = _output
                        break
        ebLogInfo(f"giClusterName:{_giclusterName} giClusterId:{_giClusterId}")
        return _giclusterName, _giClusterId

    def mGetVolumeID(self, aCell, aVolName, aOptions, aVaultName=None):
        _cell = aCell
        _vol_name = aVolName
        _ebox = self.__cluctrl

        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
            _vault_name = str(_exascale_attr['db_vault']['name']).strip()
        except Exception as e:
            ebLogWarn(f"*** mGetVolumeID failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT
            _vault_name = self.mGetDBVaultName()

        _vol_id = ""
        _owners = ""

        if aVaultName:
            _vault_name = aVaultName

        with connect_to_host(_cell, get_gcontext(), username="root") as _node:
            _i, _o, _e = _node.mExecuteCmd(f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} lsvolume --attributes id,vault,name,owners")
            _rc = _node.mGetCmdExitStatus()
            if _rc:
                _err_str = f"{_cell}: Failed to fetch volume id"
                ebLogInfo(_err_str)
                _ebox.mUpdateErrorObject(gExascaleError["GET_VOLUME_DETAILS_FAILED"], _err_str)
                raise ExacloudRuntimeError(aErrorMsg=_err_str)
            _out = _o.readlines()
            for _ret in _out:
                _output = _ret.split()
                if _output and (_vol_name == _output[2] or _output[2].startswith(f"{_vol_name}_vmbackup_restore")):
                    _vol_id = _output[0]
                    _owners = _output[3]
                    break
        ebLogInfo(f"VOLUME ID:{_vol_id}, OWNERS:{_owners}")
        return _vol_id, _owners

    def mGetVolumeAttachments(self, aCell, aVolID, aOptions):
        _cell = aCell
        _vol_id = aVolID
        _ebox = self.__cluctrl
        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mGetVolumeAttachments failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT
        _id = ""
        _volume = ""
        _device_name = ""

        with connect_to_host(_cell, get_gcontext(), username="root") as _node:
            _i, _o, _e = _node.mExecuteCmd(f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} lsvolumeattachment --attributes id,volume,deviceName")
            _rc = _node.mGetCmdExitStatus()
            if _rc:
                _err_str = f"{_cell}: Failed to get edv attachment"
                ebLogInfo(_err_str)
                _ebox.mUpdateErrorObject(gExascaleError["GET_VOLUME_DETAILS_FAILED"], _err_str)
                raise ExacloudRuntimeError(aErrorMsg=_err_str)
            _out = _o.readlines()
            for _ret in _out:
                _output = _ret.split()
                if _output and _vol_id == _output[1]:
                    _id, _volume, _device_name = _output
                    break
        ebLogInfo(f"VOLUME ATTCHMENT ID:{_id} VOLUME ID:{_volume} DEVICE NAME:{_device_name}")
        return _id, _volume, _device_name

    def mGetACFSFileSystem(self, aCell, aVolID, aOptions):
        _cell = aCell
        _vol_id = aVolID
        _acfs_id = ""
        _mount_path = ""
        _size = ""
        _ebox = self.__cluctrl
        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mCreateACFSFileSystem failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        #List ACFS File System
        with connect_to_host(_cell, get_gcontext(), username="root") as _node:
            _i, _o, _e = _node.mExecuteCmd(f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} lsacfsfilesystem --attributes id,volume,mountPath,size")
            _rc = _node.mGetCmdExitStatus()
            if _rc:
                _err_str = f"{_cell}: Failed to get acfs filesystem"
                ebLogInfo(_err_str)
                _ebox.mUpdateErrorObject(gExascaleError["GET_VOLUME_DETAILS_FAILED"], _err_str)
                raise ExacloudRuntimeError(aErrorMsg=_err_str)
            _out = _o.readlines()
            for _ret in _out:
                _output = _ret.split()
                if _output and _vol_id == _output[1]:
                    if len(_output) == 2:
                        _acfs_id, _ = _output
                    elif len(_output) == 4:
                        _acfs_id, _, _mount_path, _size = _output
                    break
        ebLogInfo(f"ACFS FILESYSTEM ID:{_acfs_id} MOUNT PATH:{_mount_path} SIZE:{_size}")
        return _acfs_id, _mount_path, _size

    def mChangeACL(self, aCell, aClusterName, aAclPriv, aOptions, aHost=None, aVaultName=None):
        _cell = aCell
        _acl_priv = aAclPriv
        _clusterName = aClusterName
        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            if not aVaultName:
                _vault_name = str(_exascale_attr['db_vault']['name']).strip()
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mChangeACL failed with Exception: {str(e)}")
            _vault_name = self.mGetDBVaultName()
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        if aHost and aVaultName:
            _vault = "@" + aVaultName
            _acl_string = f"+{aHost}:{_acl_priv}"
        else:
           _vault = "@" + _vault_name
           _acl_string = f"+{_clusterName}:{_acl_priv}"

        with connect_to_host(_cell, get_gcontext(), username="root") as _node:
            _cmd = f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} chacl {_vault} {_acl_string}"
            _node.mExecuteCmdLog(_cmd)

    def mCreateEDVVolume(self, aCell, aSize, aVolName, aOptions, aVaultName=None):
        _cell = aCell
        _size = aSize
        _vol_name = aVolName

        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
            _vault_name = str(_exascale_attr['db_vault']['name']).strip()
        except Exception as e:
            ebLogWarn(f"*** mCreateEDVVolume failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT
            _vault_name = self.mGetDBVaultName()

        if aVaultName:
            _vault_name = aVaultName

        #Create EDV Volume
        with connect_to_host(_cell, get_gcontext(), username="root") as _node:
            _node.mExecuteCmdLog(f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} mkvolume {_size} --vault {_vault_name} --attributes name={_vol_name}")
            _rc = _node.mGetCmdExitStatus()
        return _rc

    def mResizeEDVVolume(self, aCell, aSize, aVolID, aOptions=None):
        _cell = aCell
        _size = aSize
        _vol_id = aVolID

        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mResizeEDVVolume failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        #Resize EDV Volume
        with connect_to_host(_cell, get_gcontext(), username="root") as _node:
            _node.mExecuteCmdLog(f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} chvolume {_vol_id} --attributes size={_size}")
            _rc = _node.mGetCmdExitStatus()
        return _rc

    def mCreateEDVVolumeAttachment(self, aCell, aVolID, aDeviceName, aGIClusterId, aGIClusterName, aOptions, aInitiatorID=None):
        _cell = aCell
        _vol_id = aVolID
        _device_name = aDeviceName
        _gi_cluster_id = aGIClusterId
        _gi_clustername = aGIClusterName
        _initiator_id = aInitiatorID

        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mCreateEDVVolumeAttachment failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT
        
        if aInitiatorID:
            _cmd_str = f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} mkvolumeattachment --protocol edv {_vol_id} {_device_name} --initiator {_initiator_id} --attributes user={_gi_clustername}"
        else:
            _cmd_str = f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} mkvolumeattachment --protocol edv {_vol_id} {_device_name} --attributes giClusterId={_gi_cluster_id},user={_gi_clustername}"

        #Create EDV Volume Attachment
        with connect_to_host(_cell, get_gcontext(), username="root") as _node:
            _node.mExecuteCmdLog(_cmd_str)
            _rc = _node.mGetCmdExitStatus()
        return _rc

    def mCreateACFSFileSystem(self, aCell, aVolID, aMntName, aName, aGIClusterName, aOptions):
        _cell = aCell
        _vol_id = aVolID
        _name = aName
        _gi_clustername = aGIClusterName
        _mount_path = aMntName

        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mCreateACFSFileSystem failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        #Create ACFS File System
        with connect_to_host(_cell, get_gcontext(), username="root") as _node:
            _node.mExecuteCmdLog(f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} mkacfsfilesystem {_vol_id} {_mount_path} --attributes name={_name},user={_gi_clustername},mountLeafOwner=1001,mountLeafGroup=1001,mountLeafMode=0755")
            _rc = _node.mGetCmdExitStatus()
        return _rc

    def mChangeVolume(self, aCell, aVolID, aClusterName, aOptions):
        _cell = aCell
        _vol_id = aVolID
        _clusterName = aClusterName
        _ebox = self.__cluctrl
        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mChangeVolume failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        #chvolume for the grid user
        with connect_to_host(_cell, get_gcontext(), username="root") as _node:
            _cmd_str = f'{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} chvolume {_vol_id} --attributes owners=+{_clusterName}'
            _node.mExecuteCmdLog(_cmd_str)
            _rc = _node.mGetCmdExitStatus()
        return _rc

    def mMountACFSFileSystem(self, aCell, aVolID, aMntName, aGIClusterName, aOptions):
        _cell = aCell
        _vol_id = aVolID
        _mount_path = aMntName
        _gi_clustername = aGIClusterName
        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mMountACFSFileSystem failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        #Mount ACFS File System
        with connect_to_host(_cell, get_gcontext(), username="root") as _node:
            _node.mExecuteCmdLog(f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} acfsctl register {_vol_id} {_mount_path} --attributes mountLeafMode=777,user={_gi_clustername}")
            _rc = _node.mGetCmdExitStatus()
        return _rc

    def mUnMountACFSFileSystem(self, aCell, aAcfsID, aOptions):
        _cell = aCell
        _acfs_id = aAcfsID
        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mUnMountACFSFileSystem failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        #UnMount ACFS File System
        with connect_to_host(_cell, get_gcontext(), username="root") as _node:
            _node.mExecuteCmdLog(f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} acfsctl deregister {_acfs_id}")
            _rc = int(_node.mGetCmdExitStatus())
            if _rc !=0:
                _node.mExecuteCmdLog(f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} acfsctl deregister {_acfs_id} --force")
                _rc = _node.mGetCmdExitStatus()

    def mRemoveACFSFileSystem(self, aCell, aAcfsID, aOptions):
        _cell = aCell
        _acfs_id = aAcfsID

        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mRemoveACFSFileSystem failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        #Remove ACFS File System
        with connect_to_host(_cell, get_gcontext(), username="root") as _node:
            _node.mExecuteCmdLog(f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} rmacfsfilesystem {_acfs_id}")
            _rc = int(_node.mGetCmdExitStatus())
            if _rc !=0:
                _node.mExecuteCmdLog(f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} rmacfsfilesystem {_acfs_id} --force")
                _rc = _node.mGetCmdExitStatus()

    def mRemoveEDVAttachment(self, aCell, aOptions, aID, aForce=False):
        _cell = aCell
        _id = aID
        _ebox = self.__cluctrl
        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mRemoveEDVAttachment failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        _force = ""
        if aForce:
            _force = "--force"
        #Remove EDV volume attachment
        with connect_to_host(_cell, get_gcontext(), username="root") as _node:
            if _id:
                _node.mExecuteCmdLog(f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} rmvolumeattachment {_id} {_force}")

    def mRemoveEDVVolume(self, aCell, aVolID, aOptions):
        _cell = aCell
        _volume_id = aVolID
        _ebox = self.__cluctrl
        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mRemoveEDVVolume failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        #Remove EDV volume
        with connect_to_host(_cell, get_gcontext(), username="root") as _node:
            if _volume_id:
                _node.mExecuteCmdLog(f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} rmvolume {_volume_id}")

    def mRemoveFile(self, aCell, aFiles, aOptions, aForce=False):
        _cell = aCell
        _files = aFiles
        _ebox = self.__cluctrl
        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _vault_name = str(_exascale_attr['db_vault']['name']).strip()
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mRemoveFile failed with Exception: {str(e)}")
            _vault_name = self.mGetDBVaultName()
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        _force = ""
        if aForce:
            _force = "--force"
        with connect_to_host(_cell, get_gcontext(), username="root") as _node:
            _node.mExecuteCmdLog(f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} rmfile {_files} {_force}")

    def mCreateVault(self, aCell, aEFRack, aVaultName, aSize, aOptions):
        _cell = aCell
        _ef_rack = aEFRack
        _vault_name = aVaultName
        _size = aSize
        _data_d = {}
        _ret = 0
        _ebox = self.__cluctrl
        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mCreateVault failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        if _ef_rack:
            _cmd_str = f'{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} --json mkvault @{_vault_name} --provision-space-ef {_size}G' 
        else:
            _cmd_str = f'{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} --json mkvault @{_vault_name} --provision-space-hc {_size}G'

        _ret, _out, _err = self.mExecuteEscliCmd(_cell, _cmd_str)
        return _ret, _out, _err

    def mListVault(self, aCell, aVaultName, aOptions, aDetail=False, aAttributes=[], aJson = False):
        _cell = aCell
        _vault_name = aVaultName
        _detail = aDetail
        _ebox = self.__cluctrl
        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mListVault failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        if aAttributes:
            _attribute = ' '.join(aAttributes)
            _cmd_str = f'{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} lsvault @{_vault_name} --attributes {_attribute}'
            if aJson:
                _cmd_str = f'{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} --json lsvault @{_vault_name} --attributes {_attribute}'
        elif _detail:
            _cmd_str = f'{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} --json lsvault @{_vault_name} --detail'
        else:
            _cmd_str = f'{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} lsvault @{_vault_name}'
        _ret, _out, _err = self.mExecuteEscliCmd(_cell, _cmd_str)
        return _ret, _out, _err

    def mChangeVault(self, aCell, aEFRack, aVaultName, aSize, aOptions):
        _cell = aCell
        _ef_rack = aEFRack
        _vault_name = aVaultName
        _size = aSize
        _ebox = self.__cluctrl
        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mListVault failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        if _ef_rack:
            _attribute = "spaceProvEF"
        else:
            _attribute = "spaceProvHC"

        _cmd_str = f'{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} --json chvault @{_vault_name} --attributes {_attribute}={_size}G'
        _ret, _out, _err = self.mExecuteEscliCmd(_cell, _cmd_str)
        return _ret, _out, _err

    def mRemoveVault(self, aCell, aVaultName, aOptions):
        _cell = aCell
        _vault_name = aVaultName
        _ebox = self.__cluctrl
        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mRemoveVault failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        _cmd_str = f'{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} rmvault @{_vault_name}'
        _ret, _out, _err = self.mExecuteEscliCmd(_cell, _cmd_str)
        return _ret, _out, _err

    def mGetProvisionedValue(self, aCell, aEFRack, aOptions):
        _cell = aCell
        _ef_rack = aEFRack
        _ebox = self.__cluctrl
        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mGetProvisionedValue failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT
        
        if _ef_rack:
            _attribute = "spaceProvEF"
        else:
            _attribute = "spaceProvHC"

        _cmd_str = f'{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} --json  lsvault *xsvlt-* --attributes {_attribute}'
        _ret, _out, _err = self.mExecuteEscliCmd(_cell, _cmd_str)
        return _ret, _out, _err

    def mListStoragePool(self, aCell, aPoolName, aOptions):
        _cell = aCell
        _pool_name = aPoolName
        _ebox = self.__cluctrl
        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mListStoragePool failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        _cmd_str = f'{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} --json  lsstoragepool {_pool_name} --attributes spaceRaw,spaceProvisioned,spaceUsed'
        _ret, _out, _err = self.mExecuteEscliCmd(_cell, _cmd_str)
        return _ret, _out, _err

    def mCurrentStoragePoolSize(self, aCell, aPoolName, aOptions):
        _cell = aCell
        _pool_name = aPoolName
        _ebox = self.__cluctrl
        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mCurrentStoragePoolSize failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        _cmd_str = f'{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} --json  lsstoragepool {_pool_name} --attributes spaceProvisionable,spaceProvisioned,spaceUsed'
        _ret, _out, _err = self.mExecuteEscliCmd(_cell, _cmd_str)
        return _ret, _out, _err

    def mReconfigStoragePool(self, aCell, aPoolName, aOptions):
        _cell = aCell
        _pool_name = aPoolName
        _ebox = self.__cluctrl
        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mReconfigStoragePool failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        _cmd_str = f'{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} chstoragepool {_pool_name} --reconfig --force'
        _ret, _out, _err = self.mExecuteEscliCmd(_cell, _cmd_str)
        return _ret, _out, _err

    def mAlterAutoFileEncryption(self, aCell, aEnable, aOptions):
        """
        :param aCell: cell used to run escli command
        :param aEnable: True to enable auto file encryption, False otherwise
        :param aOptions: aOptions object
        """

        _cell = aCell
        _ebox = self.__cluctrl
        if aEnable:
            _auto_file_encryption = 'true'
        else:
            _auto_file_encryption = 'false'

        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mAlterAutoFileEncryption failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        _cmd_str = f'{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} chcluster --attributes autoFileEncryption={_auto_file_encryption}'
        _ret, _out, _err = self.mExecuteEscliCmd(_cell, _cmd_str)
        ebLogTrace(f"Out is '{_out}' and err is '{_err}'")
        return _ret

    def mGetClusterAttribute(self, aCell, aAttribute, aOptions):
        """
        :param aCell: cell used to run escli command
        :param aOptions: aOptions object
        :param aAttribute: the cluster attribute to check
        """

        _cell = aCell
        _ebox = self.__cluctrl
        ebLogInfo(f"List cluster attribute {aAttribute}")

        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mGetClusterAttribute failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        _cmd_str = f'{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} lscluster --attributes {aAttribute}'
        _ret, _out, _err = self.mExecuteEscliCmd(_cell, _cmd_str)
        ebLogTrace(f"Out is '{_out}' and err is '{_err}'")
        return _ret, _out, _err

