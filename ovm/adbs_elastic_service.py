#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/adbs_elastic_service.py /main/7 2025/12/02 17:57:52 ririgoye Exp $
#
# adbs_elastic_service.py
#
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
#
#    NAME
#      adbs_elastic_service.py
#
#    DESCRIPTION
#      Provide basic/core API for handling customization on adbs related cluster for Elastic operations
#
#    NOTES:
#      None
#
#    MODIFIED   (MM/DD/YY)
#    ririgoye    11/26/25 - Bug 38636333 - EXACLOUD PYTHON:ADD INSTANTCLIENT TO
#                           LD_LIBRARY_PATH
#    ririgoye    25/06/24 - Bug 38086929 - CREATE /OPT/ORACLE/SG.JSON DURING 
#                           PROVISIONING OF ADBS CLUSTERS
#    prsshukl    10/21/24 - Bug 37180429 - Cellcli command list feature not
#                           backport to 22.1.X imageversion
#    prsshukl    09/26/24 - Bug 37103101 - ADBS: Create /opt/exacloud directory
#                           and populate it with exacli wallet files.
#    prsshukl    09/20/24 - Bug 37082702 - EXACS: ADBS: ELASTIC STORAGE SUPPORT
#                           ISSUES
#    prsshukl    09/03/24 - Creation
#

from __future__ import print_function

import six
import xml.etree.cElementTree as etree
from time import sleep
import time
import re
import copy
import json
from typing import List, Mapping, Sequence
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogVerbose, ebLogJson, ebLogTrace, ebLogCritical
from exabox.ovm.cludiskgroups import ebDiskgroupOpConstants, ebCluManageDiskgroup
from exabox.ovm.cluexaccsecrets import ebExaCCSecrets
from exabox.core.Error import gDiskgroupError, gReshapeError, ExacloudRuntimeError, ebError
from exabox.core.DBStore import ebGetDefaultDB
from exabox.utils.node import connect_to_host, node_exec_cmd, node_exec_cmd_check, node_cmd_abs_path_check, node_write_text_file
from exabox.utils.common import mCompareModel
from exabox.ovm.clumisc import mWaitForSystemBoot, ebADBSUtil
from exabox.ovm.clustorage import ebCluStorageConfig
from exabox.ovm.cluelastic import getGridHome

def mReturnSrcDom0DomUPair(aExaBoxCluCtrlObj):
    """
    Return a list of list of all the SrcDom0DomUPair
    """
    _ebox = aExaBoxCluCtrlObj
    #Contains all dom0domU Pair
    aAllDom0DomUPair = _ebox.mGetElasticOldDom0DomUPair()

    #Contains only the new domOdomU Pair
    aNewDom0DomUPair = _ebox.mReturnDom0DomUPair()

    for _newdom0domUpair in aNewDom0DomUPair:
        if _newdom0domUpair in aAllDom0DomUPair:
            aAllDom0DomUPair.remove(_newdom0domUpair)

    return aAllDom0DomUPair

def mReturnFirstDom0DomUPair(aExaBoxCluCtrlObj):
    """
    Return the first dom0,domU pair
    """
    _ebox = aExaBoxCluCtrlObj
    aFirstDom0, aFirstDomU = _ebox.mReturnDom0DomUPair()[0]

    return aFirstDom0,aFirstDomU

def mUpdateQuorumDiskConfig(aExaBoxCluCtrlObj):
    """
    Step 1. Configuring the new Quorum Disk on the new domU
    # /opt/oracle.SupportTools/quorumdiskmgr --create --config --owner="grid" --group="asmadmin" --network-iface-list="clre0,clre1"

    Step 2. On the Src DomUs -> update the target to make it aware of the new domU
    # /opt/oracle.SupportTools/quorumdiskmgr --alter --target --asm-disk-group={_datanm} --visible-to="{_visibleips}" --host-name="{_shname}" --force

    Step 3. Creating the new Quorum disk on the New DomU, supplied with the targetips
    # /opt/oracle.SupportTools/quorumdiskmgr --create --device --target-ip-list="{_targetips}"

    Step 4. List the Quorum disk associated with the domU
    # /opt/oracle.SupportTools/quorumdiskmgr --list --device
    """
    ebLogInfo(" *** mUpdateQuorumDiskConfig() ***")
    _ebox = aExaBoxCluCtrlObj

    #Executed on New DomU
    for _, _domU in _ebox.mReturnDom0DomUPair():
        with connect_to_host(_domU, get_gcontext(), username="root") as _node:
            _node.mExecuteCmdLog('/opt/oracle.SupportTools/quorumdiskmgr --create --config --owner="grid" --group="asmadmin" --network-iface-list="clre0,clre1"')
    
    _visibleips =  ""
    _targetips = ""

    count = 0
    #mGetElasticOldDom0DomUPair() provides all the dom0 domU pair (source and new dom0,domU pair)
    for _, _domU in _ebox.mGetElasticOldDom0DomUPair():
        with connect_to_host(_domU, get_gcontext(), username="root") as _node:
            
            # get value 
            _, _o, _ = _node.mExecuteCmd("ip -4 addr show clre0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}'")  
            _clre0ip = _o.read().strip()                             
            _, _o, _ = _node.mExecuteCmd("ip -4 addr show clre1 | grep -oP '(?<=inet\s)\d+(\.\d+){3}'")
            _clre1ip = _o.read().strip()                             
            _visibleips = _visibleips + _clre0ip + "," + _clre1ip + ","
            # reason for only taking 2 clre0 clre1 ips for target ip is we need for the first 2 domUs only
            if count < 2:
                _targetips = _targetips + _clre0ip + "," + _clre1ip + ","

            count = count + 1

    _targetips = _targetips[:-1]
    _visibleips = _visibleips[:-1]

    ebLogInfo(f"_targetips: {_targetips}")
    ebLogInfo(f"_visibleips: {_visibleips}")

    _cluster = _ebox.mGetClusters().mGetCluster()
    _cludgroups = _cluster.mGetCluDiskGroups()

    _reconm = None
    _datanm = None

    for _dgid in _cludgroups:
        _dgnm = _ebox.mGetStorage().mGetDiskGroupConfig(_dgid).mGetDgName()
        if "RECO" in _dgnm:
            _reconm = _dgnm

        if "DATA" in _dgnm:
            _datanm = _dgnm

    ebLogInfo(f"data: {_datanm}")
    ebLogInfo(f"reco: {_reconm}")

    for _, _domU in mReturnSrcDom0DomUPair(_ebox):
        with connect_to_host(_domU, get_gcontext(), username="root") as _node:
            _shname = _domU.split('.')[0].replace('-','') 

            _cmd = f'/opt/oracle.SupportTools/quorumdiskmgr --alter --target --asm-disk-group={_datanm} --visible-to="{_visibleips}" --host-name="{_shname}" --force'
            _node.mExecuteCmdLog(_cmd)

            _cmd = f'/opt/oracle.SupportTools/quorumdiskmgr --alter --target --asm-disk-group={_reconm} --visible-to="{_visibleips}" --host-name="{_shname}" --force'
            _node.mExecuteCmdLog(_cmd)

    #mReturnDom0DomUPair will send the new dom0 domU pair
    for _, _domU in _ebox.mReturnDom0DomUPair():
        with connect_to_host(_domU, get_gcontext(), username="root") as _node:
 
            _cmd = f'/opt/oracle.SupportTools/quorumdiskmgr --create --device --target-ip-list="{_targetips}"'
            _node.mExecuteCmdLog(_cmd)

            _, _o, _ = _node.mExecuteCmd("/opt/oracle.SupportTools/quorumdiskmgr --list --device")
            ebLogInfo(f"List of new quorum devices created:")
            _out = _o.readlines()
            for _oline in _out:
                ebLogInfo(f"{_oline}")

def mAddExacliPasswdToNewDomUs(aExaBoxCluCtrlObj, aSrcDomU, _newdomUList):

    _ebox = aExaBoxCluCtrlObj
    _srcdomU = aSrcDomU

    _ebox.mCopyCreateVIP()

    # Fetch the exacli password from src domU and store it in new domU
    with connect_to_host(_srcdomU, get_gcontext()) as _node:
        if _node.mFileExists('/opt/exacloud/get_cs_data.py'):
            _, _o, _ = _node.mExecuteCmd('/opt/exacloud/get_cs_data.py --dataonly')
            if _node.mGetCmdExitStatus() != 0:
                _warn_msg = f"Failure in getting the Exacli password"
                ebLogWarn(_warn_msg)
                return
        else:
            ebLogWarn(f"/opt/exacloud/get_cs_data.py file is not present in {_srcdomU}")
            return
    _passwd = _o.read().strip()
    for _newdomU in _newdomUList:
        try:
            ebExaCCSecrets([_newdomU]).mPushExacliPasswdToDomUs(_passwd)
        except Exception as e:
            ebLogError(f"Failure during ExaCLI password push to domU: {_newdomU}")
            ebLogError(f"Error caused by the following exception: {e}")
            # If the corresponding flag is enabled, we will raise runtime error when invalid ExaCLI pwd is passed
            if _ebox.mCheckConfigOption('enforce_exacli_password_update', 'True'):
                raise ExacloudRuntimeError(0x0757, 0xA, f"Exception during ExaCLI password push to domU: {_newdomU}") from e

def mCreateGriddiskADBS(aExaBoxCluCtrlObj, aCell):
    _ebox = aExaBoxCluCtrlObj

    _cluster = _ebox.mGetClusters().mGetCluster()
    _cludgroups = _cluster.mGetCluDiskGroups()
    _reconm = None
    _datanm = None
    _spnm = None

    for _dgid in _cludgroups:
        _dg = _ebox.mGetStorage().mGetDiskGroupConfig(_dgid)
        _dgnm = _dg.mGetGridDiskPrefix()

        if "RECO" in _dgnm:
            _reconm = _dgnm
            _recogd = _dg.mGetSliceSize()

        if "DATA" in _dgnm:
            _datanm = _dgnm
            _datagd = _dg.mGetSliceSize()

        if "SPRC" in _dgnm:
            _spnm = _dgnm
            _spgd = _dg.mGetSliceSize()

        ebLogInfo(f"data: {_datanm}")
        ebLogInfo(f"reco: {_reconm}")
        ebLogInfo(f"sparse: {_spnm}")

  # create griddisks in the cells
    with connect_to_host(aCell, get_gcontext()) as _cell_node:
        if _spnm:
            _cmd = f"create griddisk all HARDDISK prefix='{_datanm}', size={_datagd}"
            _cell_node.mExecuteCmdLog(f'cellcli -e "{_cmd}"')
            _cmd = f"create griddisk all HARDDISK prefix='{_reconm}', size={_recogd}"
            _cell_node.mExecuteCmdLog(f'cellcli -e "{_cmd}"')
            _cmd = f"create griddisk all HARDDISK prefix='{_spnm}', size={_spgd}"
            _cell_node.mExecuteCmdLog(f'cellcli -e "{_cmd}"')
        else:
            _cmd = f"create griddisk all HARDDISK prefix='{_datanm}', size={_datagd}"
            _cell_node.mExecuteCmdLog(f'cellcli -e "{_cmd}"')
            _cmd = f"create griddisk all HARDDISK prefix='{_reconm}', size={_recogd}"
            _cell_node.mExecuteCmdLog(f'cellcli -e "{_cmd}"')
        

def mDeleteGriddiskADBS(aExaBoxCluCtrlObj, aCell):
    _ebox = aExaBoxCluCtrlObj

    with connect_to_host(aCell, get_gcontext()) as _cell_node:
        _cluster = _ebox.mGetClusters().mGetCluster()
        _cluster_groups = _cluster.mGetCluDiskGroups()
        for _dgid in _cluster_groups:
            _dgName = _ebox.mGetStorage().mGetDiskGroupConfig(_dgid).mGetDgName()
            _cmd = f"cellcli -e DROP GRIDDISK ALL prefix={_dgName} force"
            _cell_node.mExecuteCmdLog(_cmd)

def mGetKeyValueCellkey(aExaBoxCluCtrlObj):
    """
    Get the key value pair from /etc/oracle/cell/network-config/cellkey.ora
    return:
    _key_value_pair = {'key': 'analnhfilajgvjnagv', 'asm': 'adbsenv2'}
    """
    _ebox = aExaBoxCluCtrlObj
    _cellkey_ora_path = "/etc/oracle/cell/network-config/cellkey.ora"
    _dom0,_domU = mReturnFirstDom0DomUPair(_ebox)
    _key_value_pair = {}

    with connect_to_host(_domU, get_gcontext()) as _node:
        _cat_cmd = node_cmd_abs_path_check(_node, "cat")
        _cmd = f"{_cat_cmd} {_cellkey_ora_path}"
        _, _out, _ = node_exec_cmd_check(_node, _cmd)
        for _line in _out.splitlines():
            if '=' in _line:
                _key, _value = _line.split('=', 1)  # Split only on the first '='
                _key_value_pair[_key.strip()] = _value.strip()

    return _key_value_pair

def mAssignKeyToCell(aExaBoxCluCtrlObj, aCell):
    """"
    To Assign Security key in the new cell
    """
    ebLogInfo(" *** mAssignKeyToCell() ***")
    _ebox = aExaBoxCluCtrlObj
    _key_value_pair = mGetKeyValueCellkey(_ebox)
    _asm = ""
    if ('key' in _key_value_pair) and ('asm' in _key_value_pair): 
        _key = _key_value_pair["key"]
        _asm = _key_value_pair["asm"]
    else:
        _err_msg = f"Failure in assigning key to {aCell} through cellcli as key or asm key value not present in cellkey.ora"
        ebLogError(_err_msg)
        raise ExacloudRuntimeError(_err_msg)

    with connect_to_host(aCell, get_gcontext()) as _cell_node:
        _cmd = f"cellcli -e ASSIGN KEY FOR ASMCLUSTER '{_asm}'='{_key}'"
        _cell_node.mExecuteCmdLog(_cmd)
        if _cell_node.mGetCmdExitStatus() != 0:
            _err_msg = f"Failure in assigning key to {aCell} through cellcli"
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(_err_msg)
    ebLogInfo(f"Assigned security key in the new cell {aCell}")

def mRemoveKeyFromCell(aExaBoxCluCtrlObj, aCell):
    """
    To Remove Security key in the new cell
    """
    ebLogInfo(" *** mRemoveKeyFromCell() ***")
    _ebox = aExaBoxCluCtrlObj
    _key_value_pair = mGetKeyValueCellkey(_ebox)
    _key = ''
    _asm = None

    if 'asm' in _key_value_pair: 
        _asm = _key_value_pair["asm"]
    else:
        _warn_msg = f"Failure in removing key from {aCell} through cellcli as asm key value not present in cellkey.ora"
        ebLogWarn(_warn_msg)

    if not _asm:
        _err_msg = f"Invalid asm key value: {_asm}"
        ebLogError(_err_msg)
        raise ExacloudRuntimeError(_err_msg)

    with connect_to_host(aCell, get_gcontext()) as _cell_node:
        _cmd = f"ASSIGN KEY FOR ASMCLUSTER '{_asm}'='{_key}'"
        _cell_node.mExecuteCmdLog(f'cellcli -e "{_cmd}"')
        if _cell_node.mGetCmdExitStatus() != 0:
            _warn_msg = f"Failure in dropping key from {aCell} through cellcli"
            ebLogWarn(_warn_msg)
        else:
            ebLogInfo(f"Dropped security key in the new cell {aCell}")

def mCheckASMScopeSecurity(aExaBoxCluCtrlObj):
    _ebox = aExaBoxCluCtrlObj
    _asmss = _ebox.mGetClusters().mGetCluster().mGetCluAsmScopedSecurity()
    _cellkey_ora_path = "/etc/oracle/cell/network-config/cellkey.ora"
    _cellkey_path_exist = False

    _dom0,_domU = mReturnFirstDom0DomUPair(_ebox)
    with connect_to_host(_domU, get_gcontext(), username="root") as _node:
        if _node.mFileExists(_cellkey_ora_path):
            _cellkey_path_exist = True

    if (_asmss.upper() == "TRUE") and _cellkey_path_exist:
        return True
    return False

def mSetAvailableToOnGriddisk(aExaBoxCluCtrlObj, aCell):
    _ebox = aExaBoxCluCtrlObj

    _cluster = _ebox.mGetClusters().mGetCluster()
    _cludgroups = _cluster.mGetCluDiskGroups()

    _reconm = None
    _datanm = None

    for _dgid in _cludgroups:
        _dg = _ebox.mGetStorage().mGetDiskGroupConfig(_dgid)
        _dgnm = _dg.mGetGridDiskPrefix()
        if "RECO" in _dgnm:
            _reconm = _dgnm

        if "DATA" in _dgnm:
            _datanm = _dgnm

    ebLogInfo(f"data: {_datanm}")
    ebLogInfo(f"reco: {_reconm}")

    _key_value_pair = mGetKeyValueCellkey(_ebox)

    _clustername = _key_value_pair['asm']
    ebLogInfo(f"asm={_clustername} in cell")


    with connect_to_host(aCell, get_gcontext()) as _cell_node:
        # Get the list of the griddisk for the cell
        _cellcli_cmd_list_data_griddisk = f"cellcli -e 'list griddisk attributes name where name like \"{_datanm}.*\"'"
        _cellcli_cmd_list_reco_griddisk = f"cellcli -e 'list griddisk attributes name where name like \"{_reconm}.*\"'"
        _, _out, _err = _cell_node.mExecuteCmdCellcli(_cellcli_cmd_list_data_griddisk)
        if _cell_node.mGetCmdExitStatus() != 0:
            _err_msg = f"Failure in getting the {_datanm} prefix griddisk in {aCell}"
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(_err_msg)
        _data_griddisk_list = _out.read().split()

        _, _out, _err = _cell_node.mExecuteCmdCellcli(_cellcli_cmd_list_reco_griddisk)
        if _cell_node.mGetCmdExitStatus() != 0:
            _err_msg = f"Failure in getting the {_reconm} prefix griddisk in {aCell}"
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(_err_msg)
        _reco_griddisk_list = _out.read().split()

        _griddisk_list = _data_griddisk_list + _reco_griddisk_list

        for _griddisk in _griddisk_list:
            _cmd_set_available_to = f"cellcli -e 'ALTER GRIDDISK {_griddisk} availableTo=\"{_clustername}\"'"
            _cell_node.mExecuteCmdLog(_cmd_set_available_to)

    ebLogInfo(f"availableTo tag set to {_clustername} in {aCell} Griddisk for {_datanm} and {_reconm} prefix")

def mGetIpsForCellipOra(aExaBoxCluCtrlObj, aCell):
    """
    To get the stre0 and stre1 ip for the new cell
    """

    _ebox = aExaBoxCluCtrlObj
    _cellip_ora_path = '/etc/oracle/cell/network-config/cellip.ora'
    with connect_to_host(aCell, get_gcontext()) as _cell_node:
        _ip_bin = node_cmd_abs_path_check(_cell_node, "ip",sbin=True)
        _grep_bin = node_cmd_abs_path_check(_cell_node, "grep",sbin=True)

        _cmd_stre0_ip = f"{_ip_bin} a s stre0 | {_grep_bin} -Po 'inet \K[\d.]+'"
        _cmd_stre1_ip =  f"{_ip_bin} a s stre1 | {_grep_bin} -Po 'inet \K[\d.]+'"

        _, _o, _ = _cell_node.mExecuteCmd(_cmd_stre0_ip, aTimeout=30)
        if _cell_node.mGetCmdExitStatus() != 0:
            _err_msg = f"Failure in getting the stre0 ip in {aCell}"
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(_err_msg)
        _stre0_ip = _o.read().strip()
        _, _o, _ = _cell_node.mExecuteCmd(_cmd_stre1_ip, aTimeout=30)
        if _cell_node.mGetCmdExitStatus() != 0:
            _err_msg = f"Failure in getting the stre1 ip in {aCell}"
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(_err_msg)
        _stre1_ip = _o.read().strip()

    _cell_ip_to_append = f'cell=\"{_stre0_ip};{_stre1_ip}\"'

    return _cell_ip_to_append

def mAppendCellipOraForDomU(aExaBoxCluCtrlObj, aCell):
    """"
    To Append the stre0 and stre1 ip for the new cell in /etc/oracle/cell/network-config/cellip.ora from all the domUs
    """

    _ebox = aExaBoxCluCtrlObj
    _cellip_ora_path = '/etc/oracle/cell/network-config/cellip.ora'

    _cell_ip_to_append = mGetIpsForCellipOra(_ebox, aCell)

    _, _domUs, _, _ = _ebox.mReturnAllClusterHosts()

    for _domU in _domUs:
        with connect_to_host(_domU, get_gcontext(), username="root") as _node:
            _cat_cmd = node_cmd_abs_path_check(_node, "cat")
            _cmd = f"{_cat_cmd} {_cellip_ora_path}"
            _, _out, _ = node_exec_cmd_check(_node, _cmd)
            if _cell_ip_to_append in _out:
                ebLogInfo(f"{_cell_ip_to_append} is already present in {_cellip_ora_path} for {_domU}")
            else:
                ebLogInfo(f"Appending {_cell_ip_to_append} value in {_cellip_ora_path} for {_domU}")
                node_write_text_file(_node, _cellip_ora_path, f'{_cell_ip_to_append}\n', append=True)

def mRemoveCellipOraForDomU(aExaBoxCluCtrlObj, aCell):
    """
    To remove the stre0 and stre1 ip for the new cell in /etc/oracle/cell/network-config/cellip.ora from all the domUs
    """

    _ebox = aExaBoxCluCtrlObj
    _cellip_ora_path = '/etc/oracle/cell/network-config/cellip.ora'

    _cell_ip_to_remove = mGetIpsForCellipOra(_ebox, aCell)

    _, _domUs, _, _ = _ebox.mReturnAllClusterHosts()

    for _domU in _domUs:
        with connect_to_host(_domU, get_gcontext(), username="root") as _node:

            _cat_cmd = node_cmd_abs_path_check(_node, "cat")
            _cmd = f"{_cat_cmd} {_cellip_ora_path}"
            _, _out, _ = node_exec_cmd_check(_node, _cmd)
            if _cell_ip_to_remove in _out:
                _sed_cmd = node_cmd_abs_path_check(_node, "sed")
                _remove_cellip_cmd = f"{_sed_cmd} -i '/{_cell_ip_to_remove}/d' {_cellip_ora_path}"
                node_exec_cmd_check(_node, _remove_cellip_cmd)
                ebLogInfo(f"{_cell_ip_to_remove} is removed from {_cellip_ora_path} for {_domU}")
            else:
                ebLogInfo(f"{_cell_ip_to_remove} not present in {_cellip_ora_path} for {_domU}")

def mCreateADBSSiteGroupConfig(aExaBoxCluCtrlObj):
    """
    To add on every domU the Site Group configuration JSON file, which will be located at /var/opt/oracle/location.json
    """
    # Retrieve domUs from the cluster
    _ebox = aExaBoxCluCtrlObj
    _options = _ebox.mGetArgsOptions()
    _dpairs = _ebox.mReturnDom0DomUPair()
    _domUs = list(map(lambda x: x[1], _dpairs))
    # On each domU, write the info passed from ECRA payload
    _adbs_util = ebADBSUtil(_options)
    _exit_code = 0
    for _domU in _domUs:
        _exit_code = _adbs_util.mCreateSiteGroupConfigFile(_domU)
    return _exit_code

def mGetorCreateDomUObj(aDomU, aDomUDict):
    """
    Function to create or retrieve a domU
    """
    if aDomU not in aDomUDict:
        aDomUDict[aDomU] = ebAdbsGrid(aDomU)
    return aDomUDict[aDomU]

class ebAdbsGrid(object):
    """ Class to update the Gridhome Path """

    def __init__(self, aDomU):
        """ Constructor
        :param aDomU:
            DomU Name
        """

        self.__domU  = aDomU
        self.__orig_gridhome_path = ''
        self.__orig_gridini_gridhome_path = ''

    def mUpdateGridHomePath(self):
        """
        To correct the grid path in /var/opt/oracle/creg/grid/grid.ini
        To create the /etc/oratab file and update the 
        """
        _domU = self.__domU
        _gridhome_path = getGridHome(_domU)
        _oratab_path = "/etc/oratab"
        if _gridhome_path is None:
            _detail_error = f"Customised -> GridHomePath:{_gridhome_path} is empty"
            raise ExacloudRuntimeError(0x0753, 0xA, _detail_error)

        with connect_to_host(_domU, get_gcontext(), username="root") as _node:

            # Update in /var/opt/oracle/creg/grid/grid.ini
            _cmd = f"/bin/cat /var/opt/oracle/creg/grid/grid.ini  | /bin/grep '^oracle_home' | /bin/cut -d '=' -f 2 "
            _, _o, _e = _node.mExecuteCmd(_cmd)
            if _node.mGetCmdExitStatus() != 0:
                raise ExacloudRuntimeError(f"Error while executing {_cmd}. Error {str(_e.readlines())}")
            _out = _o.readlines()
            if _out:
                _original_gridini_gridhome_path = _out[0].strip()
            else:
                raise ExacloudRuntimeError(f"Output of {_cmd} is empty")

            _cmd_update_gridhome_gridini = f"/bin/sed -i 's|{_original_gridini_gridhome_path}|{_gridhome_path}|g' /var/opt/oracle/creg/grid/grid.ini"
            _node.mExecuteCmdLog(_cmd_update_gridhome_gridini)
            if _node.mGetCmdExitStatus() != 0:
                _err_msg = f"Failure in updating the GridHome Path to {_gridhome_path} from the old {_original_gridini_gridhome_path} in /var/opt/oracle/creg/grid/grid.ini"
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(_err_msg)

            #Storing the value of original gridini gridhome path
            self.__orig_gridini_gridhome_path = _original_gridini_gridhome_path
            ebLogInfo(f"Updated the GridHome Path to {_gridhome_path} from the old {_original_gridini_gridhome_path} in /var/opt/oracle/creg/grid/grid.ini")

            #Creating/Overwriting /etc/oratab also

            _cmd = f"/bin/cat /var/opt/oracle/creg/grid/grid.ini  | /bin/grep '^sid' | /bin/cut -d '=' -f 2 "
            _, _o, _e = _node.mExecuteCmd(_cmd)
            if _node.mGetCmdExitStatus() != 0:
                raise ExacloudRuntimeError(f"Error while executing {_cmd}. Error {str(_e.readlines())}")
            _out = _o.readlines()
            if _out:
                _asmstr = _out[0].strip()
            else:
                raise ExacloudRuntimeError(f"Output of {_cmd} is empty")

            if _node.mFileExists(_oratab_path):
                _cmd = f"/bin/rm -f {_oratab_path}"
                _node.mExecuteCmd(_cmd)

            _cmd = "echo '{}:{}:N' >> /etc/oratab"
            _node.mExecuteCmd(_cmd.format(_asmstr, _gridhome_path))
            if _node.mGetCmdExitStatus() != 0:
                _err_msg = f"Failure in updating {_oratab_path} with {_asmstr}:{_gridhome_path}:N"
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(_err_msg)

            _cmd = f"chown grid:oinstall {_oratab_path}"
            _node.mExecuteCmd(_cmd)
            _cmd = f"chmod 664 {_oratab_path}"
            _node.mExecuteCmd(_cmd)
            
            ebLogInfo(f"Added entry - {_asmstr}:{_gridhome_path}:N to oratab")

class exaBoxAdbs(object):
    def __init__(self, aCluCtrlObject):
        self.__cluctrl = aCluCtrlObject

    def mGetGridHome(self,aDomU):
        _domU = aDomU

        with connect_to_host(_domU, get_gcontext(), username='root') as _node:

            _cmd = "/bin/cat /etc/oratab | grep '^+ASM.*' | cut -f 2 -d ':'"
            _i, _o, _e = _node.mExecuteCmd(f'/bin/su - grid -c \'{_cmd}\'')
            _out = _o.readlines()
            if not _out or len(_out) == 0:
                ebLogWarn('*** Gridhome entry not found for grid')
                return "", ""
            _path = _out[0].strip()

            _cmd = "/bin/cat /etc/oratab | grep '^+ASM.*' | cut -f 1 -d ':'"
            _i, _o, _e = _node.mExecuteCmd(f'/bin/su - grid -c \'{_cmd}\'')
            _out = _o.readlines()
            if not _out or len(_out) == 0:
                ebLogWarn('*** ASM entry not found for grid')
                return "", ""
            _sid = _out[0].strip()

            ebLogTrace('mGetGridHome:: path:' + _path + ' sid:' + _sid)
        
        return _path, _sid