#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/ovm/csstep/exascale/escli_util.py pbellary_bug-38972840/4 2026/02/24 07:31:09 pbellary Exp $
#
# escli_util.py
#
# Copyright (c) 2021, 2026, Oracle and/or its affiliates.
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
#    pbellary    05/12/26 - Bug 39120670 - VALIDATE EXASCALE SERVICES POST CONFIGURE EXASCALE
#    pbellary    04/30/26 - ER 39187148 - ECRACLI API TO UPDATE HIGH REDUNDANCY AND 
#                           ENSURE DEFAULT VLT_INSPECT PRVILEGE IS UNSET FOR VMCLUSTER USERID
#    pbellary    02/24/26 - Bug 38972840 - DELETE-SERVICE WF FAILED TO VERIFY ACL USER ID
#    pbellary    02/24/26 - Bug 38858318 - IF CHACL COMMAND FAILS CREATE SERVICE FLOW SHOULD FAIL
#    pbellary    02/24/26 - Bug 38883255 - VM BACKUP OPERATION IS NOT TAKING BACKUP OF 3RD NODE
#    shapatna    02/10/26 - Enh: 38900613 - EXACLOUD SHOULD USE THE JSON FORMAT
#                           OUTPUT FOR ALL ESCLI GET COMMANDS
#    siyarlag    02/02/26 - 38894750: use --json option for escli command
#    rajsag      01/29/26 - 38890844 - exacc-exascale- exacloud respond with
#                           vault size as zero incase of cellcli command fails
#                           to get storage type as ef or hc
#    pbellary    01/09/26 - Bug 38830473 - EXASCALE CLUSTER FAILED TO CREATE EDV VOLUME ATTACHMENT 
#    pbellary    01/06/26 - Enh 38650337 - EXACLOUD API FOR ADDITIONAL ACFS EXTRACTION
#    siyarlag    12/17/25 - Add escli mkuser helper
#    pbellary    11/30/25 - Enh 38708130 - EXASCALE: DELETE SERVICE SHOULD DELETE ADDITIONAL ACFS FILESYSTEMS
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
BYTES_TO_GB_CONVERSION = 1024*1024*1024

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

    def mGetByPath(self, data, path):
        _current = data
        for _key in path.split("."):
            if not isinstance(_current, dict):
                return None
            _current = _current.get(_key)
        return _current
    
    def mParseEscliJson(self, json_output, match_dict=None, return_keys=None, exclude=None):
        ebLogTrace(f"*** JSON output is as follows: {json_output}")
        
        if not json_output:
            return []

        _data_list = json_output.get("data", [])
        if not _data_list:
            return []

        if match_dict is None:
            _match_mode = "none"
            _match_items = []
        elif isinstance(match_dict, dict):
            _match_mode = "key_value"
            _match_items = list(match_dict.items())
        else:
            _match_mode = "keys"
            _match_items = list(match_dict)

        if exclude is None:
            _exclude_mode = "none"
            _exclude_items = []
        elif isinstance(exclude, dict):
            _exclude_mode = "key_value"
            _exclude_items = list(exclude.items())
        else:
            _exclude_mode = "keys"
            _exclude_items = list(exclude)

        _matches = []
        for _item in _data_list:
            if not isinstance(_item, dict):
                continue

            _exclude_hit = False
            if _exclude_mode == "key_value":
                for _ex_key, _ex_value in _exclude_items:
                    _value_to_check = self.mGetByPath(_item, _ex_key)
                    if callable(_ex_value):
                        if _ex_value(_value_to_check):
                            _exclude_hit = True
                            break
                    else:
                        if _value_to_check == _ex_value:
                            _exclude_hit = True
                            break
            elif _exclude_mode == "keys":
                for _ex_key in _exclude_items:
                    _value_to_check = self.mGetByPath(_item, _ex_key)
                    if _value_to_check is not None:
                        _exclude_hit = True
                        break

            if _exclude_hit:
                continue

            _match_found = True
            if _match_mode == "key_value":
                for _match_key, _match_value in _match_items:
                    _value_to_check = self.mGetByPath(_item, _match_key)

                    if(callable(_match_value)):
                        _match_found = _match_value(_value_to_check)
                    else:
                        _match_found = (_value_to_check == _match_value)
                    
                    if not _match_found:
                        break
            elif _match_mode == "keys":
                for _match_key in _match_items:
                    _value_to_check = self.mGetByPath(_item, _match_key)
                    if _value_to_check is None:
                        _match_found = False
                        break

            if not _match_found:
                continue

            _result = {}
            for _key in return_keys or []:
                _last_splitted_key = _key.split(".")[-1]
                _result[_last_splitted_key] = self.mGetByPath(_item, _key)
            _matches.append(_result)

        return _matches       
    
    def mGetDictFromOutputString(self, out, cmd, eBox):
        """
            Parses the output to return a dictionary
        """
        _ebox = eBox
        try:
            _raw_output = out.read().strip()
            
            if not _raw_output:
                _msg = f"Output of the command: {cmd} is empty"
                ebLogError(_msg)
                _ebox.mUpdateErrorObject(gExascaleError["EMPTY_ESCLI_OUTPUT"], _msg)
                raise ExacloudRuntimeError(0x0811, 0xA, _msg)
            
            _json_out = json.loads(_raw_output)

        except Exception as e:
            _msg = f"Unable to parse the output of the command: {cmd} to JSON format."
            ebLogError(_msg)
            _ebox.mUpdateErrorObject(gExascaleError["EMPTY_ESCLI_OUTPUT"], _msg)
            raise ExacloudRuntimeError(0x0811, 0xA, _msg)
        
        return _json_out
           
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

    def mCreateEsWalletUser(self, aOptions, aCell, aWalletUser, aPubKeyFile=None, aVaultName=None):
        _cell = aCell
        _wallet_user = aWalletUser
        _ebox = self.__cluctrl

        if not _wallet_user:
            ebLogWarn("eswallet user identifier is empty; skipping mkuser execution")
            return None

        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mGetVolumeID failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        with connect_to_host(_cell, get_gcontext()) as _node:
            if not _node.mFileExists(ESCLI):
                _msg = f'Unable to execute ESCLI commands on {_cell}, ESCLI path does not exist'
                ebLogError(_msg)
                raise ExacloudRuntimeError(0x0811, 0xA, _msg)

            _cmd = (f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} mkuser oracle --id {_wallet_user}")
            ebLogInfo(f"Invoking ESCLI mkuser on cell {_cell} for oracle wallet user {_wallet_user}")
            _ret, _out, _err = _node.mExecuteCmd(_cmd)

            if aPubKeyFile:
                _chuser_cmd = (f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} chuser {_wallet_user} --public-key-file1 {aPubKeyFile}")
                ebLogInfo(f"Updating oracle wallet user {_wallet_user} public key on cell {_cell}")
                _node.mExecuteCmd(_chuser_cmd)
                _node.mExecuteCmd(f"/bin/rm -f {aPubKeyFile}")

            if aVaultName:
                _cmd = (f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} --json lsacl {aVaultName}")
                ebLogInfo(f"Fetching ACL for vault {aVaultName} on cell {_cell}")
                _r, _o, _e = _node.mExecuteCmd(_cmd)

                _acl_output = ""
                _raw_output = ''.join(_o.readlines())
                if _raw_output:
                    _json_text = str(_raw_output).strip()
                    if _json_text:
                        try:
                            _json_out = json.loads(_json_text)
                            _data_obj = _json_out.get("data", {})
                            if isinstance(_data_obj, dict):
                                _attributes = _data_obj.get("attributes", {})
                                if isinstance(_attributes, dict):
                                    _acl_value = _attributes.get("acl")
                                    if _acl_value is not None:
                                        _acl_output = str(_acl_value)
                        except ValueError as _json_exc:
                            ebLogWarn(f"Failed to parse escli JSON output: {_json_exc}")

                if not _acl_output:
                    _err_str = f"{_cell}: Failed to fetch vault '{aVaultName}' acls"
                    ebLogInfo(_err_str)
                    _ebox.mUpdateErrorObject(gExascaleError["VAULT_GET_ACL_FAILED"], _err_str)
                    raise ExacloudRuntimeError(aErrorMsg=_err_str)

                if _wallet_user not in _acl_output:
                    _chacl_cmd = (f'{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} chacl {aVaultName} "{_acl_output};{_wallet_user}:I"')
                    ebLogInfo(f"Updating ACL for vault {aVaultName} with user {_wallet_user} on cell {_cell}")
                    node_exec_cmd_check(_node, _chacl_cmd)
                else:
                    ebLogInfo(f"Vault {aVaultName} on cell {_cell} already contains {_wallet_user} in ACL; skipping update")

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
            _cmd_line = f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} --json lsuser"
            _i, _o, _e = _node.mExecuteCmd(_cmd_line)
            _rc = _node.mGetCmdExitStatus()

            if _rc == 0:
                _json_output = self.mGetDictFromOutputString(_o, _cmd_line, _ebox)
                _result = self.mParseEscliJson(_json_output, match_dict = {"id" : "grid" + _clusterName}, return_keys=["id"])
                for _res in _result:
                    if "id" in _res:
                        _giclusterName = "grid" + _clusterName
                        break
                    else:
                        _giclusterName = ""

        ebLogInfo(f"UserId: {_giclusterName} for the Cluster:{_clusterName}")
        return _giclusterName

    def mGetUserDetails(self, aCell, aOptions, aMatchDict=None, aReturnKeys=[]):
        _match_dict = aMatchDict
        _return_keys = aReturnKeys
        _ebox = self.__cluctrl
        _cell = aCell

        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mGetUser failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        with connect_to_host(_cell, get_gcontext(), username="root") as _node:
            _cmd_line = f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} --json lsuser --detail"
            _i, _o, _e = _node.mExecuteCmd(_cmd_line)
            _rc = _node.mGetCmdExitStatus()

            if _rc == 0:
                _json_output = self.mGetDictFromOutputString(_o, _cmd_line, _ebox)
                _result = self.mParseEscliJson(_json_output, match_dict = _match_dict, return_keys=_return_keys)
        return _result

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
            _cmd_line = f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} --json lsinitiator --attributes id,hostName"
            _i, _o, _e = _node.mExecuteCmd(_cmd_line)
            _rc = _node.mGetCmdExitStatus()
            if _rc:
                _err_str = f"{_cell}: Failed to fetch clusterName & clusterID"
                ebLogInfo(_err_str)
                _ebox.mUpdateErrorObject(gExascaleError["GET_CLUSTER_DETAILS_FAILED"], _err_str)
                raise ExacloudRuntimeError(aErrorMsg=_err_str)

            _json_output = self.mGetDictFromOutputString(_o, _cmd_line, _ebox)
            _result = self.mParseEscliJson(_json_output, match_dict = {"attributes.hostName" : _host_name}, return_keys=["id"]) 

            for _res in _result:
                if "id" in _res:
                    _initiatorId = _res.get("id")  

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
            _cmd_line = f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} --json lsinitiator --attributes giClusterName,giClusterId"
            _i, _o, _e = _node.mExecuteCmd(_cmd_line)
            _rc = _node.mGetCmdExitStatus()
            if _rc:
                _err_str = f"{_cell}: Failed to fetch clusterName & clusterID"
                ebLogInfo(_err_str)
                _ebox.mUpdateErrorObject(gExascaleError["GET_CLUSTER_DETAILS_FAILED"], _err_str)
                raise ExacloudRuntimeError(aErrorMsg=_err_str)
            
            _json_output = self.mGetDictFromOutputString(_o, _cmd_line, _ebox)
            _result = self.mParseEscliJson(_json_output, match_dict = {"attributes.giClusterName" : _clusterName}, return_keys=["attributes.giClusterName", "attributes.giClusterId"]) 
            
            _giclusterName = self.mGetUser(_cell, _clusterName, aOptions)
            for _res in _result:
                if _giclusterName and "giClusterId" in _res:
                    _giClusterId = _res.get("giClusterId")
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
            _cmd_line = f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} --json lsvolume --attributes id,vault,name,owners"
            _i, _o, _e = _node.mExecuteCmd(_cmd_line)
            _rc = _node.mGetCmdExitStatus()
            
            if _rc:
                _err_str = f"{_cell}: Failed to fetch volume id"
                ebLogInfo(_err_str)
                _ebox.mUpdateErrorObject(gExascaleError["GET_VOLUME_DETAILS_FAILED"], _err_str)
                raise ExacloudRuntimeError(aErrorMsg=_err_str)
            
            def match_volume_pattern(value):
                return (value and (value == _vol_name or value.startswith(f"{_vol_name}_vmbackup_restore")))
            
            _json_output = self.mGetDictFromOutputString(_o, _cmd_line, _ebox)
            _result = self.mParseEscliJson(
                _json_output,
                match_dict = {
                    "attributes.name": match_volume_pattern
                },
                return_keys = [
                    "id",
                    "attributes.owners"
                ]
            )

            for _res in _result:
                if "id" in _res and "owners" in _res:
                    _vol_id = _res.get("id")
                    _owners = _res.get("owners")
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
            _cmd_line = f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} --json lsvolumeattachment --attributes id,volume,deviceName"
            _i, _o, _e = _node.mExecuteCmd(_cmd_line)
            _rc = _node.mGetCmdExitStatus()
            if _rc:
                _err_str = f"{_cell}: Failed to get edv attachment"
                ebLogInfo(_err_str)
                _ebox.mUpdateErrorObject(gExascaleError["GET_VOLUME_DETAILS_FAILED"], _err_str)
                raise ExacloudRuntimeError(aErrorMsg=_err_str)

            _json_output = self.mGetDictFromOutputString(_o, _cmd_line, _ebox)
            _result = self.mParseEscliJson(_json_output, match_dict = {"attributes.volume" : _vol_id}, return_keys=["id", "attributes.volume", "attributes.deviceName"]) 

            for _res in _result:
                if "id" in _res and "volume" in _res and "deviceName" in _res:
                    _id = _res.get("id")
                    _volume = _res.get("volume")
                    _device_name = _res.get("deviceName")

        ebLogInfo(f"VOLUME ATTCHMENT ID:{_id} VOLUME ID:{_volume} DEVICE NAME:{_device_name}")
        return _id, _volume, _device_name

    def mGetACFSFileSystem(self, aCell, aVolID, aOptions):
        _cell = aCell
        _vol_id = aVolID
        _acfs_id, _mount_path, _size, _total_free  = "", "", "", ""
        _ebox = self.__cluctrl
        
        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mGetACFSFileSystem failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        #List ACFS File System
        with connect_to_host(_cell, get_gcontext(), username="root") as _node:
            _cmd_line = f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} --json lsacfsfilesystem --attributes id,volume,mountPath,size,totalFree"
            _i, _o, _e = _node.mExecuteCmd(_cmd_line)
            _rc = _node.mGetCmdExitStatus()
            if _rc:
                _err_str = f"{_cell}: Failed to get acfs filesystem"
                ebLogInfo(_err_str)
                _ebox.mUpdateErrorObject(gExascaleError["GET_VOLUME_DETAILS_FAILED"], _err_str)
                raise ExacloudRuntimeError(aErrorMsg=_err_str)
            
            _json_output = self.mGetDictFromOutputString(_o, _cmd_line, _ebox)
            _result = self.mParseEscliJson(_json_output, match_dict = {"attributes.volume" : _vol_id}, return_keys=["id", "attributes.mountPath", "attributes.size", "attributes.totalFree"]) 
            
            for _res in _result:
                if "id" in _res and "mountPath" in _res:
                    _acfs_id = _res.get("id")
                    _mount_path = _res.get("mountPath")
                    try:
                        _size = int(_res.get("size")) / BYTES_TO_GB_CONVERSION
                    except (TypeError, ValueError):
                        ebLogError(f"Cannot convert {_res.get('size')} to a valid integer")
                        _size = ""

                    try:
                        _total_free = int(_res.get("totalFree")) / BYTES_TO_GB_CONVERSION
                    except (TypeError, ValueError):
                        ebLogError(f"Cannot convert {_res.get('totalFree')} to a valid integer")
                        _total_free = ""
            
        ebLogInfo(f"ACFS FILESYSTEM ID:{_acfs_id} MOUNT PATH:{_mount_path} SIZE:{_size} TOTAL_FREE:{_total_free}")
        return _acfs_id, _mount_path, _size, _total_free

    def mGetACFSFileSystemByJsonFormat(self, aCell, aOptions):
        _cell = aCell
        _acfs_id, _mount_path, _size, _total_free  = "", "", "", ""
        _ebox = self.__cluctrl
        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mGetACFSFileSystemByJsonFormat failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        #List ACFS File System
        _cmd_str = f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} --json lsacfsfilesystem --attributes id,volume,mountPath,size,totalFree"
        _ret, _out, _err = self.mExecuteEscliCmd(_cell, _cmd_str)
        return _ret, _out, _err

    def mGetDBServerStatus(self, aHost=None, aService=None):
        _host = aHost
        _service = aService
        _status = ""
        with connect_to_host(_host, get_gcontext(), username="root") as _node:
            _cmd_str = f"/usr/sbin/dbmcli -e LIST DBSERVER ATTRIBUTES {_service}"
            _i, _o, _e = _node.mExecuteCmd(_cmd_str)
            _rc = _node.mGetCmdExitStatus()
            _output = _o.readlines()
            if _output:
                _status = _output[0].strip()
        return _rc, _status

    def mChangeACL(self, aCell, aClusterName, aAclPriv, aOptions, aHost=None, aVaultName=None):
        _cell = aCell
        _acl_priv = aAclPriv
        _clusterName = aClusterName
        _vault_name = aVaultName
        _ebox = self.__cluctrl
        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            if not aVaultName:
                _vault_name = str(_exascale_attr['db_vault']['name']).strip()
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mChangeACL failed with Exception: {str(e)}")
            if not aVaultName:
                _vault_name = self.mGetDBVaultName()
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        if aHost and aVaultName:
            _hostname = aHost.split('.')[0]
            _vault = "@" + aVaultName
            _acl_string = f"+{_hostname}:{_acl_priv}"

            _rc, _esnp_status = self.mGetDBServerStatus(aHost, aService="esnpStatus")
            if _rc != 0:
                _err_str = f"{_hostname}: Failed to fetch esnpStatus (rc={_rc})."
                ebLogWarn(_err_str)
                _err_str = f"ESNP service is not configured on compute node {_hostname}. Skip updating acl permissions"
                ebLogWarn(_err_str)
                return
            if _esnp_status and _esnp_status.lower() == "disabled":
                _err_str = f"ESNP service is disabled on compute node {_hostname}. Skip updating acl permissions"
                ebLogWarn(_err_str)
                return
            elif _esnp_status and _esnp_status.lower() != "running":
                _err_str = f"{_hostname}: DBSERVER esnpStatus is '{_esnp_status}'. Expected 'running'."
                ebLogError(_err_str)
                _ebox.mUpdateErrorObject(gExascaleError["UPDATE_ACL"], _err_str)
                raise ExacloudRuntimeError(aErrorMsg=_err_str)
        else:
           _vault = "@" + _vault_name
           _acl_string = f"+{_clusterName}:{_acl_priv}"

        with connect_to_host(_cell, get_gcontext(), username="root") as _node:
            _cmd = f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} chacl {_vault} {_acl_string}"
            _node.mExecuteCmdLog(_cmd)
            _rc = _node.mGetCmdExitStatus()
            if _rc:
                _err_str = f"{_cell}: Failed to update acl permissions"
                ebLogInfo(_err_str)
                _ebox.mUpdateErrorObject(gExascaleError["UPDATE_ACL"], _err_str)
                raise ExacloudRuntimeError(aErrorMsg=_err_str)

    def mCreateEDVVolume(self, aCell, aSize, aVolName, aOptions, aVaultName=None):
        _cell = aCell
        _size = aSize
        _vol_name = aVolName
        _ebox = self.__cluctrl
        _rc = -1

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
            if _rc:
                _err_str = f"{_cell}: Failed to create EDV Volume"
                ebLogInfo(_err_str)
                _ebox.mUpdateErrorObject(gExascaleError["CREATE_EDV_VOLUME_FAILED"], _err_str)
                raise ExacloudRuntimeError(aErrorMsg=_err_str)
        return _rc

    def mResizeEDVVolume(self, aCell, aSize, aVolID, aOptions=None):
        _cell = aCell
        _size = aSize
        _vol_id = aVolID
        _ebox = self.__cluctrl
        _rc = -1

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
            if _rc:
                _err_str = f"{_cell}: Failed to resize EDV Volume"
                ebLogInfo(_err_str)
                _ebox.mUpdateErrorObject(gExascaleError["RESIZE_EDV_VOLUME"], _err_str)
                raise ExacloudRuntimeError(aErrorMsg=_err_str)
        return _rc

    def mCreateEDVVolumeAttachment(self, aCell, aVolID, aDeviceName, aGIClusterId, aGIClusterName, aOptions, aInitiatorID=None):
        _cell = aCell
        _vol_id = aVolID
        _device_name = aDeviceName
        _gi_cluster_id = aGIClusterId
        _gi_clustername = aGIClusterName
        _initiator_id = aInitiatorID
        _ebox = self.__cluctrl
        _rc = -1

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
            if _rc:
                _err_str = f"{_cell}: Failed to create EDV Volume Attachment"
                ebLogInfo(_err_str)
                _ebox.mUpdateErrorObject(gExascaleError["CREATE_EDV_ATTACH_FAILED"], _err_str)
                raise ExacloudRuntimeError(aErrorMsg=_err_str)
        return _rc

    def mCreateACFSFileSystem(self, aCell, aVolID, aMntName, aName, aGIClusterName, aOptions):
        _cell = aCell
        _vol_id = aVolID
        _name = aName
        _gi_clustername = aGIClusterName
        _mount_path = aMntName
        _ebox = self.__cluctrl
        _rc = -1

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
            if _rc:
                _err_str = f"{_cell}: Failed to create acfs filesystem"
                ebLogInfo(_err_str)
                _ebox.mUpdateErrorObject(gExascaleError["CREATE_ACFS_FAILED"], _err_str)
                raise ExacloudRuntimeError(aErrorMsg=_err_str)
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
            if _rc:
                _err_str = f"{_cell}: Failed to update EDV volume owners list"
                ebLogInfo(_err_str)
                _ebox.mUpdateErrorObject(gExascaleError["UPDATE_EDV_VOLUME_OWNERS"], _err_str)
                raise ExacloudRuntimeError(aErrorMsg=_err_str)
        return _rc

    def mMountACFSFileSystem(self, aCell, aVolID, aMntName, aGIClusterName, aOptions):
        _cell = aCell
        _vol_id = aVolID
        _mount_path = aMntName
        _gi_clustername = aGIClusterName
        _ebox = self.__cluctrl
        _rc = -1
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
            _node.mExecuteCmdLog(f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} acfsctl register {_vol_id} {_mount_path} --attributes mountLeafOwner=1001,mountLeafGroup=1001,mountLeafMode=0755,user={_gi_clustername}")
            _rc = _node.mGetCmdExitStatus()
            if _rc:
                _err_str = f"{_cell}: Failed to mount acfs filesystem"
                ebLogInfo(_err_str)
                _ebox.mUpdateErrorObject(gExascaleError["MOUNT_ACFS_FAILED"], _err_str)
                raise ExacloudRuntimeError(aErrorMsg=_err_str)
        return _rc

    def mUnMountACFSFileSystem(self, aCell, aAcfsID, aOptions, aRaiseError=True):
        _cell = aCell
        _acfs_id = aAcfsID
        _ebox = self.__cluctrl
        _rc = -1
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
            if _rc and aRaiseError:
                _err_str = f"{_cell}: Failed to unmount acfs filesystem"
                ebLogInfo(_err_str)
                _ebox.mUpdateErrorObject(gExascaleError["UMOUNT_ACFS_FAILED"], _err_str)
                raise ExacloudRuntimeError(aErrorMsg=_err_str)

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

    def mRemoveUser(self, aCell, aClusterName, aOptions):
        _cell = aCell
        _cluster_name = aClusterName
        _ebox = self.__cluctrl
        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mRemoveUser failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        with connect_to_host(_cell, get_gcontext(), username="root") as _node:
            _node.mExecuteCmdLog(f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} rmuser {_cluster_name}")

    def mListFiles(self, aCell, aFiles=None, aOptions=None, aJson=False, aVault=None, aFilter={}):
        _cell = aCell
        _files = aFiles
        _output = []
        _ebox = self.__cluctrl
        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mListFiles failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        if aJson:
            with connect_to_host(_cell, get_gcontext(), username="root") as _node:
                if aFilter:
                    _filter_cmd = ""
                    for _key, _value in list(aFilter.items()):
                        _filter_cmd += f"{_key}={_value} "
                    if aVault:
                        _cmd_str = f'{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} --json ls {aVault}/ --filter {_filter_cmd}'
                    else:
                        _cmd_str = f'{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} --json ls {_filter_cmd}'
                else:
                    _cmd_str = f'{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} --json ls'
                _i, _o, _e = _node.mExecuteCmd(_cmd_str)
                _rc = _node.mGetCmdExitStatus()

            if _rc == 0:
                _json_output = self.mGetDictFromOutputString(_o, _cmd_str, _ebox)
                _output = self.mParseEscliJson(_json_output, match_dict = {f"attributes.name"}, 
                                               return_keys=[f"attributes.name"],
                                               exclude={"id": lambda v: isinstance(v, str) and v.startswith("$")})
        else:
            _cmd_str = f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} ls {_files}"
            with connect_to_host(_cell, get_gcontext(), username="root") as _node:
                _ret, _out, _err = self.mExecuteEscliCmd(_cell, _cmd_str)
                if _out:
                    _output = _out.splitlines()
        return _output

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
            _attribute = ','.join(aAttributes)
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

    def mGetClusterAttribute(self, aCell, aAttributes=[], aOptions=None, aJson=False):
        """
        :param aCell: cell used to run escli command
        :param aOptions: aOptions object
        :param aAttributes: the cluster attributes to check
        """

        _cell = aCell
        _ebox = self.__cluctrl
        _attributes = ""
        if aAttributes:
            _attributes = ','.join(aAttributes)
        ebLogInfo(f"List cluster attributes {_attributes}")

        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mGetClusterAttribute failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        if aJson:
            with connect_to_host(_cell, get_gcontext(), username="root") as _node:
                _cmd_str = f'{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} --json lscluster --attributes {_attributes}'
                _i, _o, _e = _node.mExecuteCmd(_cmd_str)
                _rc = _node.mGetCmdExitStatus()

            if _rc == 0:
                _json_output = self.mGetDictFromOutputString(_o, _cmd_str, _ebox)
                _result = self.mParseEscliJson(_json_output, match_dict = {f"attributes.{attribute}" for attribute in aAttributes}, 
                                               return_keys=[f"attributes.{attribute}" for attribute in aAttributes])
                return _rc, _result, ""
            else:
                return _rc, [], ""
        else:
            _cmd_str = f'{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} lscluster --attributes {_attributes}'
            _ret, _out, _err = self.mExecuteEscliCmd(_cell, _cmd_str)
            ebLogTrace(f"Out is '{_out}' and err is '{_err}'")
        return _ret, _out, _err
    
    def mRemoveVMUserPrivilege(self, aCell, aUserId, aOptions):
        _cell = aCell
        _userId = aUserId
        _ebox = self.__cluctrl

        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mRemoveVMUserPrivilege failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        with connect_to_host(_cell, get_gcontext(), username="root") as _node:
            _cmd_str = f'{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} chuser {_userId} --attributes privilege="no_privilege"'
            _node.mExecuteCmdLog(_cmd_str)

    def mChangeClusterAtributes(self, aCell, aOptions, aAttribute={}):
        """
        :param aCell: cell used to run escli command
        :param aEnable: True to enable auto file encryption, False otherwise
        :param aOptions: aOptions object
        """

        _cell = aCell
        _ebox = self.__cluctrl
        _rc = -1

        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mChangeClusterAtributes failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        _attr_cmd = ""
        if aAttribute:
            for _key, _value in list(aAttribute.items()):
                _attr_cmd += f"{_key}={_value} "

        with connect_to_host(_cell, get_gcontext(), username="root") as _node:
            _cmd_str = f'{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} chcluster --attributes {_attr_cmd}'
            _node.mExecuteCmdLog(_cmd_str)
            _rc = _node.mGetCmdExitStatus()

        return _rc

    def mListExascaleServices(self, aCell, aOptions):
        _cell = aCell
        _ebox = self.__cluctrl
        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mListExascaleServices failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        with connect_to_host(_cell, get_gcontext()) as _node:
            _cmd_str = f"{ESCLI} --wallet {WALLET_LOC} --ctrl {_ctrl_ip}:{_ctrl_port} --json lsservice --attributes name,status"
            _i, _o, _e = _node.mExecuteCmd(_cmd_str)
            _rc = _node.mGetCmdExitStatus()
            if _rc:
                _err_str = f"{_cell}: Failed to fetch exascale services"
                ebLogInfo(_err_str)
                _ebox.mUpdateErrorObject(gExascaleError["GET_EXASCALE_SERVICE_FAILED"], _err_str)
                raise ExacloudRuntimeError(aErrorMsg=_err_str)

            _json_output = self.mGetDictFromOutputString(_o, _cmd_str, _ebox)
            _result = self.mParseEscliJson(_json_output, return_keys=["attributes.name", "attributes.status"]) 

        return _result

    def mCheckWalletExists(self, aHost, aOptions, aType="cell"):
        _host = aHost
        _type = aType
        _ebox = self.__cluctrl
        _rc = -1

        try:
            _exascale_attr = self.mParseExascaleAttrib(aOptions)
            _ctrl_ip = str(_exascale_attr['ctrl_network']['ip']).strip()
            _ctrl_port = str(_exascale_attr['ctrl_network']['port']).strip()
        except Exception as e:
            ebLogWarn(f"*** mCheckWalletExists failed with Exception: {str(e)}")
            _ctrl_ip, _ = self.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        with connect_to_host(_host, get_gcontext()) as _node:
            if _type == "cell":
                _wallet = "/opt/oracle/cell/cellsrv/deploy/config/eswallet"
            elif _type == "dom0":
                _wallet = "/opt/oracle/dbserver/dbms/deploy/config/eswallet"

            _cmd_str = f"/usr/bin/test -e {_wallet}"
            _i, _o, _e = _node.mExecuteCmd(_cmd_str)
            _rc = _node.mGetCmdExitStatus()
        return _rc
