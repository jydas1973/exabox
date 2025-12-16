"""
$Header:

 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    OVM - Basic functionality

FUNCTION:
    Provide basic/core API for managing OVM Cluster (Cluster Lifecycle,...)

NOTE:
    None

History:

    MODIFIED   (MM/DD/YY)
    pbellary    11/24/25 - Enh 38685113 - EXASCALE: POST CONFIGURE EXASCALE EXACLOUD SHOULD FETCH STRE0/STE1 FROM DOM0
    aypaul      05/28/25 - Bug#37903672 Use existing patch config path to save
                           latest xml configuration.
    pbellary    05/26/25 - Bug 37982976 - EXACC:ELASTIC INFO:DELETE CELL SHOULD REMOVE CELL FROM STORAGEPOOL IF EXISTS
    prsshukl    04/25/25 - Bug 37861890 - EXADB-XS: EXACLOUD: ELASTIC INFO CALL
                           FAILING IN ADD COMPUTE
    pbellary    03/06/25 - Bug 37665040 - EXACC:BB:ELASTIC: ATTACH CELL OPERATION COMPLETED 
                           BUT IT NOT PART OF ESCLUSTER AND POOLDISKS NOT EXTENDED. 
    aararora    12/18/24 - ER 37402747: Add NTP and DNS entries in xml
    aararora    09/26/24 - Bug 37105761: Oedacli command is failing for
                           elastic_info call in ipv6
    prsshukl    08/30/24 - ER 36553793 - EXACS | ADBS | ELASTIC CELL AND
                           COMPUTE OPERATION ENHANCEMENTS -> IMPLEMENT PHASE 1
    dekuckre    02/29/24 - 36339845: patch private networks
    joysjose    06/27/23 - 34708961 - INSTALL SURICATA RPM AS A PART OF
                           ACTIVATECOMPUTE DURING ELASTIC COMPUTE NODE ADDITION
    jfsaldan    04/13/23 - Bug 35144841 - EXACS:22.2.1:DROP2:230224.1626:FS
                           ENCRYPTION:MULTI-VM:STEPWISE ADD COMPUTE FAILING AT
                           CREATE_GUEST STEP:ERROR:OEDA-1070: CANNOT CONNECT TO
                           HOST
    aararora    03/06/23 - Check for network slaves info for DR and add DR
                           network in xml.
    pbellary    03/03/23 - 35142856: ADD NODE FAILS AT FETCHUPDATEDXMLFROMECFORNODELISTUPDATE WITH ERROR: INVALID RACK NUMBER : 2
    prsshukl    02/13/23 - Bug 34914914: Exacloud is not saving newly generated
                           exakms entries for the command oedaaddkey_host.
    pbellary    10/17/22 - 34661392: VM CLUSTER CREATION FAILS |IMAGEVERSION 22.1.1.0.0 NOT FOUND IN PROPERTIES FILE
    dekuckre    09/22/22 - 34627247: Call 'CONFIG_CELL' step as part of mAddCell
    rajsag      12/01/21 - 33594977 :adding error code handling for the node
                           subsetting in exacloud
    siyarlag    10/21/21 - 33484723: pass date string to imageversion command
    dekuckre    13/05/21 - 32880259: Ensure racksetup/keys is created-owned using sudo
    siyarlag    03/03/21 - 32214702: multiple image version support
    jlombera    01/28/21 - Bug 32214629: support multiple compute/cell add/del
                           in elastic_info endpoint.
    dekuckre    10/23/20 - 31992073: Add mDeleteDomU, mDeleteCell 
    dekuckre    05/22/20 - 31389081: Make Add Dom0 KVM compatible
    dekuckre    05/19/20 - 31367484: Fix clustername in Add cell call.
    dekuckre    05/07/20 - 30858257: Make elastic compute KVM compatible
    dekuckre    05/07/20 - 30858268: Make elastic cell KVM compatible
    hgaldame    01/25/19 - 29266837 : elastic support - register inventory
                           fails
    pverma      01/17/19 - Remove extra update of response body
    pbellary    12/26/18 - File Creation

"""
from exabox.core.Error import ebError, gSubError, ExacloudRuntimeError, gNodeElasticError 
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogVerbose, ebLogJson,ebLogTrace
from exabox.core.DBStore import ebGetDefaultDB
from exabox.tools.oedacli import OedacliCmdMgr
from exabox.ovm.vmconfig import exaBoxClusterConfig
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.ovm.bmc import XMLProcessor
from exabox.ovm.clumisc import ebMiscFx, mPatchPrivNetworks
from exabox.ovm.cluencryption import isEncryptionRequested, patchXMLForEncryption
from exabox.ovm.utils.clu_utils import ebCluUtils
from exabox.utils.node import connect_to_host,node_exec_cmd_check
import json
import hashlib
import uuid
import os
import tempfile
import shutil
import re
import glob
from typing import Any, Mapping, Sequence, Tuple

DEVNULL = open(os.devnull, 'wb')
Payload = Mapping[str, Any]

ReshapeConf = Mapping[str, Sequence[Any]]
"""Elastic reshape configuration.

Mapping with fields:
    'ADD_COMPUTES',
    'DELETE_COMPUTES',
    'ADD_CELLS',
    'REMOVE_CELLS'

With the computes/cells to add/delete (any field can have an empty sequence).
"""

def extractNetConfs(aNetPayload: Sequence[Payload]) -> Payload:
    """Extract Dom0/DomU/Cell Net config from elastic reshape Net payload.

    :param aNetPayload: net payload.
    :returns: Net config.
    :raises Exception: on error parsing the payload.
    """
    private = None
    admin = None
    client = None
    backup = None
    interconnect = None
    vip = None
    ilom = None
    dr = None
    drVip = None
    ntp = None
    dns = None

    for net in aNetPayload:
        private = net.get('private', private)
        admin = net.get('admin', admin)
        client = net.get('client', client)
        backup = net.get('backup', backup)
        interconnect = net.get('interconnect', interconnect)
        vip = net.get('vip', vip)
        ilom = net.get('ilom', ilom)
        dr = net.get('dr', dr)
        drVip = net.get('drVip', drVip)
        ntp = net.get('ntp', ntp)
        dns = net.get('dns', dns)

    nets = {}

    if private:
        nets['priv1'] = private[0]
        nets['priv2'] = private[1]

    if admin:
        nets['admin'] = admin[0]
    else:
        nets['admin'] = ""

    if client:
        ebMiscFx.mReplaceDiscover(client[0])
        nets['client'] = client[0]

    if backup:
        ebMiscFx.mReplaceDiscover(backup[0])
        nets['backup'] = backup[0]

    if interconnect:
        nets['interconnect1'] = interconnect[0]
        nets['interconnect2'] = interconnect[1]

    if vip:
        nets['vip'] = vip[0]

    if ilom:
        nets['ilom'] = ilom[0]

    if dr:
        nets['dr'] = dr[0]

    if drVip:
        nets['drVip'] = drVip[0]

    if ntp:
        nets['ntp'] = ntp

    if dns:
        nets['dns'] = dns

    return nets

def extractAddedComputes(aPayload: Payload, eBox=None) -> Sequence[Payload]:
    """Extract computes to add from elastic reshape payload.

    :param aPayload: elastic reshape payload.
    :returs: sequence of computes to add (can be empty).
    :raises Exception: on error parsing the payload.
    """
    def __extractCompute(aComputePayload: Payload, eBox=None) -> Payload:
        _ebox = eBox
        dom0 = aComputePayload
        dom0_nets = extractNetConfs(dom0['network_info']['computenetworks'])

        domu = aComputePayload['virtual_compute_info']
        domu_nets = extractNetConfs(
            domu['network_info']['virtualcomputenetworks'])

        if ('priv1' in domu_nets.keys()) and ('priv2' in domu_nets.keys()) and (_ebox is not None) and (_ebox.isDBonVolumes() or _ebox.isBaseDB()):
            domu_nets['priv1'] = ""
            domu_nets['priv2'] = ""

        if ('interconnect1' in domu_nets.keys()) and ('interconnect2' in domu_nets.keys()) and (_ebox is not None) and _ebox.isBaseDB():
            domu_nets['interconnect1'] = ""
            domu_nets['interconnect2'] = ""

        if 'racknum' in dom0['rack_info'].keys():
            _rack_num = dom0['rack_info']['racknum']
        else:
            _rack_num = "1"

        return {
            'dom0': {
                'hostname': dom0['compute_node_hostname'],
                'rack_num': _rack_num,
                'uloc': dom0['rack_info']['uloc'],
                **dom0_nets
            },
            'domU': {
                'hostname': domu['compute_node_hostname'],
                **domu_nets
            }
        }

    computes = aPayload['reshaped_node_subset'].get('added_computes', ())

    return tuple(__extractCompute(c, eBox) for c in computes)

def extractRemovedComputes(aPayload: Payload) -> Sequence[Payload]:
    """Extract computes to remove from elastic reshape payload.

    :param aPayload: elastic reshape payload.
    :returns: sequence of computes to remove (can be empty).
    :raises Exception: on error parsing the payload.
    """
    def __extractCompute(aComputePayload: Payload) -> Payload:
        return {
            'dom0': {'hostname': aComputePayload['compute_node_hostname']},
            'domU': {'hostname': None},
            'keep_dyndep_cache': aComputePayload.get('keep_dyndep_cache',
                                                     'False')
        }

    computes = aPayload['reshaped_node_subset'].get('removed_computes', ())

    return tuple(map(__extractCompute, computes))

def extractAddedCells(aPayload: Payload) -> Sequence[Payload]:
    """Extract cells to add form elastic reshape payload.

    :param aPayload: elastic reshape payload.
    :returns: sequence of cells to add (can be empty).
    :raises Exception: on error parsing the payload.
    """
    def __extractCell(aCellPayload: Payload) -> Payload:

        if 'racknum' in aCellPayload['rack_info'].keys():
            _rack_num = aCellPayload['rack_info']['racknum']
        else:
            _rack_num = "1"

        cell_nets = extractNetConfs(
            aCellPayload['network_info']['cellnetworks'])
        return {
            'hostname': aCellPayload['cell_hostname'],
            'rack_num': _rack_num,
            'uloc': aCellPayload['rack_info']['uloc'],
            **cell_nets
        }

    cells = aPayload['reshaped_node_subset'].get('added_cells', ())

    return tuple(map(__extractCell, cells))

def extractRemovedCells(aPayload: Payload) -> Sequence[Payload]:
    """Extract cells to remove from elastic reshape payload.

    :param aPayload: elastic reshape payload.
    :returns: sequence of cells to remove (can be empty).
    :raises Exception: on error parsing the payload.
    """
    cells = aPayload['reshaped_node_subset'].get('removed_cells', ())

    return tuple({'hostname': cell['cell_node_hostname']} for cell in cells)

def extractElasticConf(aPayload: Payload, eBox=None) -> ReshapeConf:
    """Extract elastic reshape config from payload.
    :param aPayload: elastic reshape payload.
    :returs: elastic reshape config (see ReshapeConf).
    :raises Exception: if there was an error parsing the payload.
    """
    return {
        'ADD_COMPUTES': extractAddedComputes(aPayload, eBox),
        'DELETE_COMPUTES': extractRemovedComputes(aPayload),
        'ADD_CELLS': extractAddedCells(aPayload),
        'DELETE_CELLS': extractRemovedCells(aPayload)
    }

def getImageVersion(aHost):
    # type: (str) -> str
    """Get Image Version for a host 'aHost'
    :param str aHost: Hostname to find its image version
    :return: Host image version
    :rtype: str
    """

    _host = aHost
    _node = exaBoxNode(get_gcontext())
    _node.mConnect(aHost=_host)
    _imgver = ""

    _cmdstr = '/usr/local/bin/imageinfo -version'
    _i, _o, _e = _node.mExecuteCmd(_cmdstr)
    _out = _o.readlines()
    if _out:
        _imgver = _out[0].strip()

    if not _out or not _imgver:
        ebLogError('*** Unable to extract image version from imageinfo for the host %s' % _host)

    _node.mDisconnect()
    ebLogVerbose('getImageVersion _imgver={}'.format(_imgver))
    return _imgver

def getGridHome(aHost):
    """
    Returns the GridHome path in the domU
    """
    with connect_to_host(aHost, get_gcontext()) as _node:
        _cmdstr = "ps -ef | grep ocssd | grep grid"
        _, _o, _ = node_exec_cmd_check(_node, _cmdstr)

        if _o is None:
            return None
        
        _output = _o.split()
        for _out in _output:
            if _out.endswith('/bin/ocssd.bin'):
                _grid_path = _out.replace('/bin/ocssd.bin', '')
                ebLogTrace(f"The Grid Home path is {_grid_path}")
                return _grid_path

def getClusterName(aHost):
    """
    Returns the ClusterName in the domU
    """
    with connect_to_host(aHost, get_gcontext()) as _node:
        _grid_path = getGridHome(aHost)
        if _grid_path is None:
            return None
        
        _olsnodes_path = os.path.join(_grid_path, "bin/olsnodes")
        _cmdstr = f"{_olsnodes_path} -c"
        _, _o, _ = node_exec_cmd_check(_node, _cmdstr)

        _clustername = _o.strip()
        ebLogTrace(f"The clustername is {_clustername}")

        return _clustername

def getDiskGroupNames(aHost):
    """
    Returns a list of the DiskGroupNames
    """
    with connect_to_host(aHost, get_gcontext()) as _node:
        _grid_path = getGridHome(aHost)
        if _grid_path is None:
            return None

        _asmcmd_path = os.path.join(_grid_path, "bin/asmcmd")
        _cmdstr = f"{_asmcmd_path} lsdg"
        _, _o, _ = node_exec_cmd_check(_node, _cmdstr)

        if _o is None:
            return None
        
        _lines = _o.splitlines()
        diskgroupnames = [_line.split()[-1].rstrip('/') for _line in _lines[1:]]

        return diskgroupnames

def patchOedaXmlForElastic(
        aReshapeConf: ReshapeConf,
        aCurrentDom0DomUPairs: Sequence[Tuple[str, str]],
        aCurrentCells: Sequence[str],
        aCellPower: int,
        aClusterName: str,
        aIsKvm: bool,
        aXmlPath: str,
        aOedacliBin: str,
        aIsExacc: bool,
        aCluCtrlObj) -> None:
    """Patch given OEDA XML for Elastic reshape.

    :param aReshapeConf: elastic reshape config (see ReshapeConf).
    :param aCurrentDom0DomUPairs: current (Dom0,DomU) pairs in the XML.
    :param aCurrentCells: current cell hostnames in the the XML.
    :param aCellPower: cell power.
    :param aClusterName: cluster name to patch XML for.
    :param aIsKvm: whether a KVM XML.
    :param aXmlPath: path to the XML to patch.
    :param aOedaCliBin: path to oedacli binary.
    :returns: Nothing.
    :raises ExacloudRuntimeError: if an error occurred while patching XML.
    """
    _ociexacc = aIsExacc
    _ebox = aCluCtrlObj
    xmlv1reinjector = V1OedaXMLRebuilder()
    xmlv1reinjector.SavePropertiesInitialXML(aXmlPath)
    _clu_utils = ebCluUtils(_ebox)
    _options = _ebox.mGetArgsOptions()
    _xs_cell_attach = False
    if _options is not None and _ebox.mGetCmd() in ['elastic_info']:
        _jconf = _options.jsonconf
        if _jconf and "reshaped_node_subset" in _jconf and "xs_cell_attach" in _jconf["reshaped_node_subset"]:
            _xs_cell_attach = _jconf["reshaped_node_subset"]["xs_cell_attach"]

    with tempfile.TemporaryDirectory() as tmp_dir:
        oedacli_mgr = OedacliCmdMgr(aOedacliBin, tmp_dir)

        # add computes
        for compute in aReshapeConf['ADD_COMPUTES']:
            dom0 = compute['dom0']['hostname']
            domU = compute['domU']['hostname']

            for src_dom0, src_domU in aCurrentDom0DomUPairs:
                if src_dom0 != dom0:
                    break
            else:
                raise ExacloudRuntimeError(
                    0x0767, 0xA,
                    f'Unable to find src Dom0 for {dom0} in added_computes')

            if not _ebox.mIsExaScale():
                _imgVersion = getImageVersion(src_domU)
            else:
                _imgVersion = getImageVersion(src_dom0)

            # Update OEDA properties file for image version to match with image version of source domU
            _ebox.mSetImageVersionProperty(_imgVersion)

            ebLogVerbose(f"Source dom0: {src_dom0}, Source domU: {src_domU}")

            oedacli_mgr.mAddDom0(src_dom0, aXmlPath, aXmlPath, compute,
                                 aKVM=aIsKvm)
            _dns_servers, _ntp_servers = _clu_utils.mExtractNtpDnsPayload(compute['dom0'])
            if _dns_servers or _ntp_servers:
                oedacli_mgr.mUpdateDnsNtpServers(dom0, aXmlPath, aXmlPath, _dns_servers, _ntp_servers)

            _net_info = None
            if 'dr' in compute['domU'] and _ociexacc:
                _ebox.mSetDRNetPresent(True)
                _net_info = _ebox.mGetNetworkSetupInformation(aNetworkType="dr", aDom0=dom0)
            oedacli_mgr.mAddDomU(src_domU, domU, aXmlPath, aXmlPath, compute, _ebox,
                                 aKVM=aIsKvm, aSrcVer=_imgVersion, aIsOciExacc=_ociexacc, aNetInfo=_net_info)

            if not _ebox.mIsExaScale():
                _clusterName = _ebox.mGetClusters().mGetCluster().mGetCluName()
                _cluver = _ebox.mGetClusters().mGetCluster().mGetCluVersion()
                _gridhome, _, _ora_base = _ebox.mGetOracleBaseDirectories(aDomU = src_domU)

                oedacli_mgr.mUpdateGIHome(_clusterName, _cluver, _gridhome, aXmlPath, aXmlPath)

            # If encryption is requested, reset XML and add encryption again.
            # This will make sure that the keyapi is added to the new nodes from
            # the cluster
            if isEncryptionRequested(_ebox.mGetArgsOptions(), 'domU') and not _ebox.mIsOciEXACC() and _ebox.mIsKVM():
                patchXMLForEncryption(_ebox, aXmlPath)

        # add cells
        add_cells = aReshapeConf['ADD_CELLS']
        if add_cells:
            new_cell_names = {cell['hostname'] for cell in add_cells}

            for src_cell_name in aCurrentCells:
                if src_cell_name not in new_cell_names:
                    break
            else:
                raise ExacloudRuntimeError(
                    0x0767, 0xA,
                    ('No src cell name found to add cells to XML. '
                     f'new_cells={new_cell_names}; '
                     f'curr_cells={aCurrentCells}'))

            ebLogVerbose("Source cell: %s" % (src_cell_name))

            oedacli_mgr.mAddCell(
                src_cell_name, aSrcXml=aXmlPath, aDestXml=aXmlPath,
                aJson={'cells': add_cells}, aDeploy=False, aKVM=aIsKvm,
                aCluName=aClusterName, aWait="false", aStep="CONFIG_CELL")
            for cell in add_cells:
                _dns_servers, _ntp_servers = _clu_utils.mExtractNtpDnsPayload(cell)
                if _dns_servers or _ntp_servers:
                    oedacli_mgr.mUpdateDnsNtpServers(cell['hostname'], aXmlPath, aXmlPath, _dns_servers, _ntp_servers)

        # delete computes
        for del_node in aReshapeConf['DELETE_COMPUTES']:
            reshape_dom0 = del_node['dom0']['hostname']

            for dom0, domU in aCurrentDom0DomUPairs:
                if dom0 == reshape_dom0:
                    reshape_domu = domU
                    break
            else:
                raise ExacloudRuntimeError(
                    0x0767, 0xA,
                    ('DomU not found for the removed_computes node in json '
                     'payload'))

            # del_node['domU']['hostname'] = reshape_domu

            oedacli_mgr.mDelNode(
                reshape_domu, reshape_dom0, aSrcXml=aXmlPath,
                aDestXml=aXmlPath, aDeploy=False)

        # delete cells
        cell_names = [c['hostname'] for c in aReshapeConf['DELETE_CELLS']]
        ebLogInfo(f"CellList from input payload: {cell_names}")
        if _ociexacc and _xs_cell_attach:
            #For exacc:
            #elastic_info should remove new cell from the inputXML, when infra is in attached state
            _currentCells = [_cell.split('.')[0] for _cell in aCurrentCells]
            ebLogInfo(f"Existing cell list:{_currentCells}")
            for src_cell_name in _currentCells:
                if src_cell_name in cell_names:
                    _sp_list = _ebox.mGetStorage().mGetStoragePoolConfigList()
                    if _sp_list:
                        _cell_list = _ebox.mReturnCellNodes(aIsXS=True)
                        _xs_cell_list = [_cell.split('.')[0] for _cell in _cell_list.keys()]
                        if src_cell_name in _xs_cell_list:
                            _user_data = { "exascale": {"pool_name": "hcpool"} }
                            oedacli_mgr.mDropCell(
                                aSrcXml=aXmlPath, aDestXml=aXmlPath, aCellList=cell_names, 
                                aDeploy=False, aPower=aCellPower, aKVM=True,
                                aCluName=aClusterName, aXmlOnly=False, aUserData=_user_data)
                    oedacli_mgr.mDropCell(
                        aSrcXml=aXmlPath, aDestXml=aXmlPath, aCellList=cell_names, 
                        aDeploy=False, aPower=aCellPower, aKVM=True,
                        aCluName=aClusterName, aXmlOnly=False, aStep="CREATE_GRIDDISKS")
                    oedacli_mgr.mDropCell(aSrcXml=aXmlPath, aDestXml=aXmlPath, aCellList=cell_names, 
                        aDeploy=False, aPower=aCellPower, aKVM=True,
                        aCluName=aClusterName, aXmlOnly=True, aStep="CONFIG_CELL")
        else:
            if cell_names:
                oedacli_mgr.mDropCell(
                    aSrcXml=aXmlPath, aDestXml=aXmlPath, aCellList=cell_names,
                    aDeploy=False, aPower=aCellPower, aKVM=aIsKvm,
                    aCluName=aClusterName, aXmlOnly=True)

    xmlv1reinjector.ProcessOedaCliXML(aXmlPath, None, None)

def patchOedaXmlForElasticADBS(
        aCurrentDom0DomUPairs: Sequence[Tuple[str, str]],
        aXmlPath: str,
        aOedacliBin: str,
        aCluCtrlObj) -> None:
    """Patching given OEDA XML for Elastic reshape. 
    by patching the customised value in the oeda xml

    :param aCurrentDom0DomUPairs: current (Dom0,DomU) pairs in the XML.
    :param aXmlPath: path to the XML to patch.
    :param aOedaCliBin: path to oedacli binary.
    :returns: Nothing.
    :raises ExacloudRuntimeError: if an error occurred while patching XML.
    """
    _ebox = aCluCtrlObj
    xmlv1reinjector = V1OedaXMLRebuilder()
    xmlv1reinjector.SavePropertiesInitialXML(aXmlPath)

    with tempfile.TemporaryDirectory() as tmp_dir:
        oedacli_mgr = OedacliCmdMgr(aOedacliBin, tmp_dir)

        if aCurrentDom0DomUPairs:
            _,_srcdomU = aCurrentDom0DomUPairs[0]
        else:
            _detail_error = f"Dom0DomU Pair is empty in :{aCurrentDom0DomUPairs}"
            raise ExacloudRuntimeError(0x0753, 0xA, _detail_error)

        _clusterName = getClusterName(_srcdomU)
        _cluver = _ebox.mGetClusters().mGetCluster().mGetCluVersion()
        _clusterID = _ebox.mGetClusters().mGetCluster().mGetCluId()
        _diskGroupIds = _ebox.mGetClusters().mGetCluster().mGetCluDiskGroups()
        _newdiskgroupNames = getDiskGroupNames(_srcdomU)
        _id_diskgroup_mapping = dict(zip(_diskGroupIds, _newdiskgroupNames))
        _gridhome = getGridHome(_srcdomU)

        if _clusterName and _gridhome and (_newdiskgroupNames is not None):
            ebLogInfo(f"Updating the ClusterName={_clusterName} and GridHomePath={_gridhome}")

            oedacli_mgr.mUpdateClusterName(_clusterName, _clusterID, aXmlPath, aXmlPath)
            oedacli_mgr.mUpdateGIHome(_clusterName, _cluver, _gridhome, aXmlPath, aXmlPath)
            # don't need to update diskgroupName in Phase 1
            # for _diskGroupId,_newdiskgroupName in _id_diskgroup_mapping.items():
            #     ebLogInfo(f"The diskGroup id={_diskGroupId} and diskGroupName={_newdiskgroupName}")
            #     oedacli_mgr.mUpdateDiskGroupName(_newdiskgroupName, _diskGroupId, aXmlPath, aXmlPath)
        else:
            _detail_error = f"Customised -> ClusterName:{_clusterName} or GridHomePath:{_gridhome} is empty"
            raise ExacloudRuntimeError(0x0753, 0xA, _detail_error)
 
    xmlv1reinjector.ProcessOedaCliXML(aXmlPath, None, None)


#class added for elastic info operations
class ebCluElastic(object):

    def __init__(self, aExaBoxCluCtrlObj, aOptions):

        self.__eboxobj = aExaBoxCluCtrlObj
        if self.__eboxobj.mGetCmd() in ['elastic_info', 'vmgi_reshape', 'elastic_cell_update']:
            self.__reshape_conf = extractElasticConf(aOptions.jsonconf, aExaBoxCluCtrlObj)
        else:
            self.__reshape_conf = None

    def mUpdateRequestData(self, aOptions, rc, aData, err):
        """
        Updates request object with the response payload
        """
        _reqobj = self.__eboxobj.mGetRequestObj()
        _response = {}
        _response["success"] = "True" if (rc == 0) else "False"
        _response["error"] = err
        _response["output"] = aData
        if _reqobj is not None:
            _db = ebGetDefaultDB()
            _reqobj.mSetData(json.dumps(_response, sort_keys = True))
            _db.mUpdateRequest(_reqobj)
        elif aOptions.jsonmode:
            ebLogJson(json.dumps(_response, indent=4, sort_keys = True))

    def mSaveCurrentXMLConfiguration(self, aXmlPath):
        """ Save the current XML file to the cluster directory """

        _ebox = self.__eboxobj
        _srcxmlpath = aXmlPath

        _current_patchconfig_path = _ebox.mGetPatchConfig()
        if _current_patchconfig_path is None or not os.path.exists(_current_patchconfig_path):
            raise ExacloudRuntimeError(0x0753, 0xA, f"Patch configuration file: {_current_patchconfig_path} doesn't exist.")

        _dir = os.path.dirname(_current_patchconfig_path)
        _patchconfig = exaBoxClusterConfig(_ebox.mGetCtx(), _srcxmlpath)
        _conf = _patchconfig.mGetConfigXMLData()

        _sha256  = hashlib.sha256(_conf.encode('utf8'))
        _hash = _sha256.hexdigest()
        _path = os.path.join(_dir, f"{_hash}_{uuid.uuid1()}.xml")
        _ebox.mSetPatchConfig(_path)
        _patchconfig.mWriteConfig(_path)

    def mPatchXMLForElastic(self, aOptions):
        """
        Add Dom0/DOMU/CELL/SWITCH
        :param aOptions:
        :return:
        """
        _ebox = self.__eboxobj
        _ociexacc  = _ebox.mIsOciEXACC()

        if self.__reshape_conf is None:
            _detail_error = f'Reshape config is None; cmd={_ebox.mGetCmd()}'
            _ebox.mUpdateErrorObject(gNodeElasticError['RESHAPE_CONFIG_MISSING'], _detail_error)
            raise ExacloudRuntimeError(
                0x0753, 0xA, _detail_error)

        try:
            _existing_dom0_domu_pairs = _ebox.mReturnDom0DomUPair()
            _existing_cell_names = _ebox.mReturnCellNodes().keys()
            _cell_power = _ebox.mCheckConfigOption('rebal_power')
            _cluster_name = _ebox.mGetClusters().mGetCluster().mGetCluName()
            _is_kvm = _ebox.mIsKVM()
            _oedacli_bin = os.path.join(_ebox.mGetOedaPath(), 'oedacli')

            # work on tmp XML file
            with tempfile.NamedTemporaryFile( suffix='.xml') as _new_xml_fd:
                _new_xml = _new_xml_fd.name

                ebLogInfo(f'Creating {_new_xml}')

                #Patch XML with storage Interconnect Ips from compute nodes
                if _is_kvm and not _ebox.mIsAdbs() and not _ebox.mIsExaScale():
                    _utils = _ebox.mGetExascaleUtils()
                    _utils.mPatchStorageInterconnctIps(aOptions, aDom0DomUList=_existing_dom0_domu_pairs)

                shutil.copyfile(_ebox.mGetPatchConfig(), _new_xml)
                patchOedaXmlForElastic(
                    self.__reshape_conf, _existing_dom0_domu_pairs,
                    _existing_cell_names, _cell_power, _cluster_name,
                    _is_kvm, _new_xml, _oedacli_bin, _ociexacc, _ebox)

                self.mSaveCurrentXMLConfiguration(_new_xml)

                if _ebox.mIsExaScale():
                    # For Exascale env, update <natname>-clre/stre to <clienthostname>-clre/stre
                    _patchconfig = _ebox.mGetPatchConfig()
                    _ebox.mUpdateInMemoryXmlConfig(_patchconfig, aOptions)
                    mPatchPrivNetworks(_ebox)
                    _ebox.mSaveXMLClusterConfiguration()

            _db = ebGetDefaultDB()
            _db.import_file(_ebox.mGetPatchConfig())
            ebLogInfo('ebCluElastic: Saved patched Cluster Config: '
                      f'{_ebox.mGetPatchConfig()}')

            #
            # Update XML path in request obj
            #
            _reqobj = _ebox.mGetRequestObj()
            if _reqobj:
                _reqobj.mSetXml(_ebox.mGetPatchConfig())
                _db.mUpdateRequest(_reqobj)

        except Exception as e:
            _detail_error = str(e)
            _ebox.mUpdateErrorObject(gNodeElasticError['ELASTIC_INFO_CMD_FAILED'], _detail_error)
            raise ExacloudRuntimeError(0x0753, 0xA, str(e)) from e

        return 0  # success

    def mPatchXMLForElasticADBS(self):
        """
        Update the clusterName, clusterHome and diskGroupName
        in the xml
        """

        _ebox = self.__eboxobj

        try:
            _oedacli_bin = os.path.join(_ebox.mGetOedaPath(), 'oedacli')
            _existing_dom0_domu_pairs = _ebox.mReturnDom0DomUPair()

            # work on tmp XML file
            with tempfile.NamedTemporaryFile( suffix='.xml') as _new_xml_fd:
                _new_xml = _new_xml_fd.name

                ebLogInfo(f'Creating {_new_xml}')

                shutil.copyfile(_ebox.mGetPatchConfig(), _new_xml)
                patchOedaXmlForElasticADBS(
                    _existing_dom0_domu_pairs, _new_xml, _oedacli_bin, _ebox)

                self.mSaveCurrentXMLConfiguration(_new_xml)

            _db = ebGetDefaultDB()
            _db.import_file(_ebox.mGetPatchConfig())
            ebLogInfo('ebCluElastic: Saved patched Cluster Config: '
                      f'{_ebox.mGetPatchConfig()}')

            #
            # Update XML path in request obj
            #
            _reqobj = _ebox.mGetRequestObj()
            if _reqobj:
                _reqobj.mSetXml(_ebox.mGetPatchConfig())
                _db.mUpdateRequest(_reqobj)

        except Exception as e:
            _detail_error = str(e)
            _ebox.mUpdateErrorObject(gNodeElasticError['ELASTIC_INFO_CMD_FAILED'], _detail_error)
            raise ExacloudRuntimeError(0x0753, 0xA, str(e)) from e

        return 0  # success
            

    def mBuildClusterPath(self, aDom0DomUPair=None):
        _ebox = self.__eboxobj

        if aDom0DomUPair:
            _ddp = aDom0DomUPair

        _dir  = ''
        _dir2 = ''
        for _dom0, _domU in _ddp:
            _dir = _dir + _dom0.split('.')[0] + _domU.split('.')[0]
            _dir2 = _dir2 + _domU.split('.')[0]
        if len(_dir) >= 255:
            _dir  = _dir2

        return _dir
    
    def mPrepareCompute(self, aOptions):
        """This function handles the necessary operations at time of activation of Dom0.
        Any activities on dom0 at activation phase should be added here.
        Currently it is defined for rpm installation on dom0.
        As part of Enh 34708961, suricata rpm is installed. On event of failure, the flow continues"""
        """payload: {"newdom0_list":["test143260exdd003","test143260exdd004"], "rpm_to_be_installed":["suricata"]}"""
        _ebox = self.__eboxobj
        _dom0_list = []
        _rpm_list = []
        _prep_compute_config = aOptions.jsonconf
        if not _prep_compute_config:
            ebLogError(f"Please provide valid json file as payload. Cannot proceed with rpm installation. Exiting..")
            return
        if "newdom0_list" in list(_prep_compute_config.keys()):
            _dom0_list = _prep_compute_config["newdom0_list"]
        if "rpm_to_be_installed" in list(_prep_compute_config.keys()):
            _rpm_list = _prep_compute_config["rpm_to_be_installed"]
        if _dom0_list and _rpm_list:
            ebLogInfo(f"Initiating Installation of {_rpm_list} rpm on {_dom0_list}")
            for _rpm in _rpm_list:
                try:
                    if _rpm == "suricata":
                        _ebox.mInstallSuricataRPM(_dom0_list,"dom0")
                except Exception as e:
                    ebLogError(f"Installation of {_rpm} rpm on {_dom0_list} Failed. Detailed Error : {str(e)}")
                    continue
        else:
            ebLogInfo(f"Please check 'newdom0_list': {_dom0_list} and 'rpm_to_be_installed': {_rpm_list} in the payload. Cannot Proceed with installation. Exiting..")

    def mOedaAddKey(self, aOptions):
        """ Generate SSH key for the specified host & copy it to cluster path """

        _rc = 0
        _ebox = self.__eboxobj
        _reshape_config = aOptions.jsonconf['reshaped_node_subset']

        _host_type = {
            "added_computes": "DOM0",
            "added_cells": "CELLS",
            "added_switches": "SWITCHES"
        }.get(
            list(_reshape_config.keys())[0],
            'None'
        )

        if _host_type == "DOM0":
            _config = _reshape_config['added_computes'][0]
        elif _host_type == "CELLS":
            _config = _reshape_config['added_cells'][0]
        elif _host_type == "SWITCHES":
            _config = _reshape_config['added_switches'][0]

        _host = _config['hostname']

        _exakms = get_gcontext().mGetExaKms()
        _cparam = {"FQDN": _host, "user": "root"}
        _entry = _exakms.mGetExaKmsEntry(_cparam)
        _res = {}

        _rc = 0
        if not _entry:
            _rc = _ebox.mUpdateAllClusterHostsKeys(True, None, _host, _host_type, _res)
            if _res[_host] == "PASS":
                ebLogInfo(f"Successfully generated SSH key for the host {_host}")
                del _res[_host]
        else:
            ebLogInfo(f"ExaKmsEntry already found: {_entry}")

        _res_keys = list(_res.keys())
        if _res_keys:
            _res_str = ",". join(_res_keys)
            _detail_error = f"Failed to generate SSH key for the hosts {_res_str}"
            ebLogWarn(_detail_error)
            _ebox.mUpdateErrorObject(gNodeElasticError['OEDAADDKEY_HOST_CMD_FAILED'], _detail_error)
            raise ExacloudRuntimeError(0x0108, 0xA, _detail_error)

        return _rc

    def mOedaAddKeyByHost(self, aOptions):

        _ebox = self.__eboxobj
        _hosts = aOptions.jsonconf['oracle_hostnames']
        _host_type = aOptions.jsonconf['host_type']

        _exakms = get_gcontext().mGetExaKms()
        _res = {}

        for _host in _hosts:

            _cparam = {"FQDN": _host, "user": "root"}
            _entry = _exakms.mGetExaKmsEntry(_cparam)

            if not _entry:
                _ebox.mUpdateAllClusterHostsKeys(True, None, _host, _host_type, _res)

                if _res[_host] == "PASS":
                    ebLogInfo(f"Successfully generated SSH key for the host {_host}")
                    del _res[_host]
            else:
                ebLogInfo(f"ExaKmsEntry already found: {_entry}")

        _res_keys = list(_res.keys())
        if _res_keys:
            _detail_error = f"Failed to generate SSH keys for the hosts {_res_keys}"
            ebLogWarn(_detail_error)
            _ebox.mUpdateErrorObject(gNodeElasticError['OEDAADDKEY_HOST_CMD_FAILED'], _detail_error)
            raise ExacloudRuntimeError(0x0108, 0xA, _detail_error)
        _ebox.mSaveOEDASSHKeys()
        return 0

#Bug 29268921, recents OEDACLI does not generate a valid v1 XML
# If template contains vmSizeName in Machine section of domU, it is a v1
class V1OedaXMLRebuilder(object):
    def __init__(self):
        self.__v1_domUwithVmSizesTags = None

    def SavePropertiesInitialXML(self,templateXmlFullPath):
        _etxml = XMLProcessor(templateXmlFullPath)
        # Find machines of type DomU with tag vmSizeName and save tags into class
        self.__v1_domUwithVmSizesTags = _etxml.findall("./machines/machine/[osType='LinuxGuest']/[vmSizeName]")

    def ProcessOedaCliXML(self, outputXMLPath, sourcedomU, newdomU):
        _source_domu = sourcedomU
        _reshape_domu = newdomU
        _post_modified = False
        # If template is V1, check output for VmSizesTag and reinject them
        if self.__v1_domUwithVmSizesTags:

            _outxml_filename = outputXMLPath
            _outxml = XMLProcessor(_outxml_filename) 
            _num_domu_with_vmsize = len(_outxml.findall("./machines/machine/[osType='LinuxGuest']/[vmSizeName]"))
            #Get All IDs of previous VMs with vmSizeTags
            _v1_domu_ids = {x.attrib['id']:x for x in self.__v1_domUwithVmSizesTags}

            for x in self.__v1_domUwithVmSizesTags:
                for _ret in x.iter('hostName'):
                    if _ret.text == _source_domu:
                        _source_vmsizename = _v1_domu_ids[x.attrib['id']].find('./vmSizeName')

            # If any vmSizeName tags were removed from machines section, add them back
            if not _num_domu_with_vmsize == len(self.__v1_domUwithVmSizesTags):

                #Add template vmNameSize to output XML on matching vm ids
                for _domu_id in list(_v1_domu_ids.keys()):
                    _outdomu = _outxml.find('./machines/machine/[@id="{}"]/[osType="LinuxGuest"]'.format(_domu_id))
                    if _outdomu and not _outdomu.find('./vmSizeName'):
                        if not _post_modified:
                            ebLogWarn('Going to modify OEDACLI output XML to switch it back from v2 to v1 as template provided was v1')
                            ebLogWarn('Writing a copy of original one with name: {}.oeda'.format(_outxml_filename))
                            shutil.copy(_outxml_filename,_outxml_filename+'.oeda')
                            _post_modified = True
                        #Add SAME tag that was in the template with same ID
                        _outxml.insert_after_element('osType', _v1_domu_ids[_domu_id].find('./vmSizeName'),_outdomu)
                        #Template machine was v1, output was switched to v2, remove v2 artifacts
                        _outxml.remove_element('guestCores',_outdomu)
                        _outxml.remove_element('guestMemory',_outdomu)
                        _outxml.remove_element('guestLocalDiskSize',_outdomu)
            if _post_modified:  
                _outxml.writeXml(_outxml_filename)

            if _reshape_domu:
                _outxml_filename = outputXMLPath
                _outxml = XMLProcessor(_outxml_filename)

                _domUTags = _outxml.findall("./machines/machine/[osType='LinuxGuest']")
                for x in _domUTags:
                    for _ret in x.iter('hostName'):
                        if _ret.text == _reshape_domu:
                            _new_domu_id = x.attrib['id']

                _outdomu = _outxml.find('./machines/machine/[@id="{}"]/[osType="LinuxGuest"]'.format(_new_domu_id))
                if _outdomu and not _outdomu.find('./vmSizeName'):
                    shutil.copy(_outxml_filename,_outxml_filename+'.oeda')
                    _outxml.insert_after_element('osType', _source_vmsizename, _outdomu)
                    _outxml.remove_element('guestCores',_outdomu)
                    _outxml.remove_element('guestMemory',_outdomu)
                    _outxml.remove_element('guestLocalDiskSize',_outdomu)
                    _outxml.writeXml(_outxml_filename)

