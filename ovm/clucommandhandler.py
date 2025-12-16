#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/clucommandhandler.py /main/9 2025/10/24 17:07:44 ravirr Exp $
#
# clucommandhandler.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      clucommandhandler.py - Exacloud endpoint handlers
#
#    DESCRIPTION
#      Handlers for various exacloud endpoints.
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ravirr      10/17/25 - Bug 38553893 - EXADB-XS: VM FILESYSTEM RESIZE FEATURE
#	                    FOR EXADB-XS - RESHAPE-EXACOMPUTE - KEYERROR: 'U01' 
#    rajsag      09/17/25 - enh 38389132 - exacloud: autoencryption support for
#                           exascale configuration
#    jfsaldan    08/26/25 - Enh 37999800 - EXACLOUD: EXASCALE CONFIG FLOW TO
#                           ENABLE AUTOFILEENCRYPTION=TRUE AFTER EXASCALE IS
#                           CONFIGURED
#    dekuckre    08/13/25 - 38126833: fetch priv key from vault (not payload)
#    prsshukl    07/01/25 - Enh 37747083 - EXADB-XS -> New endpoint to validate
#                           volumes attached to the vm and verify with the
#                           volumes present in the xml
#    ajayasin    06/05/25 - 37982865 : clucontrol refactor : move handler
#                           functions
#    dekuckre    05/13/25 - Creation
#

import json, copy, crypt
from typing import Any, Dict, List, Mapping, Sequence, Optional, Tuple, Set
import fnmatch, re
import operator
from base64 import b64decode, b64encode  
from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.ovm.cluexascale import ebCluExaScale
from exabox.ovm.cluelasticcells import ebCluElasticCellManager
from exabox.exakms.ExaKmsEntry import ExaKmsEntry, ExaKmsHostType
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogTrace, ebLogVerbose
from exabox.ovm.cludomufilesystems import expand_domu_filesystem, ebDomUFilesystem, parse_size, ebDomUFSResizeMode, ebDiskImageInfo, attach_dom0_disk_image, create_new_lvm_disk_image, fill_disk_with_lvm_partition, get_max_domu_filesystem_sizes, shutdown_domu, start_domu, GIB, TIB
from exabox.core.Error import ebError, ExacloudRuntimeError, gReshapeError, gPartialError, gProvError, gNodeElasticError
from exabox.core.DBStore import ebGetDefaultDB
from exabox.ovm.clumisc import (ebCluPreChecks, ebCluFetchSshKeys, 
                                ebCluScheduleManager, ebCluCellValidate, 
                                ebCluServerSshConnectionCheck, 
                                ebCluReshapePrecheck, ebCluNodeSubsetPrecheck,
                                mGetDom0sImagesListSorted,
                                ebCopyDBCSAgentpfxFile, ebCluEthernetConfig, mPatchPrivNetworks,ebCluStartStopHostFromIlom, ebCluSshSetup, mGetGridListSupportedByOeda)
from exabox.ovm.atpaddroutes import ATPAddBackupRoutes
from exabox.ovm.cluiptablesroce import ebIpTablesRoCE
from exabox.core.Node import exaBoxNode, exaBoxNodePool
import exabox.ovm.clubonding as clubonding
from exabox.utils.node import (connect_to_host, node_connect_to_host, node_exec_cmd,
                               node_exec_cmd_check, node_update_key_val_file,
                               node_cmd_abs_path_check,
                               node_write_text_file, node_read_text_file, node_replace_file)
from exabox.ovm.cluincident import ebIncidentNode
import exabox.ovm.clujumboframes as clujumboframes
from exabox.ovm.vmcorecollection import ebVMCoreCollector
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure, TimeoutBehavior, ExitCodeBehavior
from exabox.ovm.cluhealthpostprov import executeHealthPostProv
from exabox.ovm.cluexascale import ebCluExaScale
from exabox.ovm.cluelastic import ebCluElastic
from exabox.ovm.cluhealth import ebCluHealthCheck
from exabox.healthcheck.cluhealthcheck import ebCluHealth
from exabox.ovm.cludiag import exaBoxDiagCtrl
from exabox.infrapatching.core.cluinfrapatch import ebCluInfraPatch
from exabox.ovm.csstep.exascale.exascaleutils import ebExascaleUtils
from exabox.network.dns.DNSConfig import ebDNSConfig
from exabox.ovm.filesystem.clumountpoint_reclaim_space import ebCluMountpointReclaimSpace
from exabox.ovm.utils.clu_utils import ebCluUtils
from exabox.ovm.clunetworkbonding import ebCluNetworkBonding
from exabox.ovm.clurevertnetworkreconfig import ebCluRevertNetworkReconfig
from exabox.ovm.clunetworkreconfig import ebCluNetworkReconfig
from exabox.ovm.clumisc import ebSubnetSet, ebCluPostComputeValidate, ebMiscFx, ebCluFaultInjection, ebMigrateUsersUtil
from exabox.infrapatching.exacompute.core.exacomputepatch import ebCluExaComputePatch
from exabox.ovm.opctlMgr import ebOpctlMgr
from exabox.core.DBStore import ebGetDefaultDB
from exabox.ovm.cluencryption import (isEncryptionRequested,
    encryptionSetupDomU, patchEncryptedKVMGuest, patchXMLForEncryption,
    addEncryptionProperties, executeLuksOperation, mSetLuksPassphraseOnDom0Exacc,
    luksCharchannelExistsInDom0, mSetLuksChannelOnDom0Exacc,
    exacc_get_fsencryption_passphrase, exacc_save_fsencryption_passphrase,
    exacc_fsencryption_requested, exacc_del_fsencryption_passphrase,
    resizeOEDAEncryptedFS, getMountPointInfo, validateMinImgEncryptionSupport)
from exabox.ovm.clustorage import ebCluStorageConfig, ebCluManageStorage
from exabox.exadbxs.edv import get_hosts_edv_from_cs_payload, get_hosts_edv_state, EDVState, EDVInfo, get_guest_edvs_from_cluster_xml, get_edvs_from_cluster_xml
from exabox.tools.ebTree.ebTree import ebTree
from exabox.exaoci.ExaOCIFactory import ExaOCIFactory
from OpenSSL import crypto
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogJson 
from exabox.core.DBStore import ebGetDefaultDB

OSTP_VALIDATE_CNF = 1

class CommandHandler:
    # Handler for exacloud endpoints which contain the exaBoxCluCtrl object

    def __init__(self, aCluCtrl):
        self.__cluctrlobj = aCluCtrl
    def mGetCluCtrlObj(self):
        return self.__cluctrlobj

    # Exacloud endpoint: adbs_insert_key
    # Usecase: Handler to insert keys to KMS for all VMs in an ADBS cluster 
    def mHandlerADBSInsertKey(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        _options = aCluCtrlObj.mGetArgsOptions()
        _exakms = get_gcontext().mGetExaKms()

        if _options.jsonconf:
            _user = _options.jsonconf.get('user')
            _compartment = _options.jsonconf.get('compartment_id')
            _vault = _options.jsonconf.get('vault_id')
            _secret = _options.jsonconf.get('secret_name')

            _factory = ExaOCIFactory()
            _vault_client = _factory.get_vault_client()
            _secrets_client = _factory.get_secrets_client()
            _privkey = None
            if _vault and _secret:
                try: 
                    _response = _secrets_client.get_secret_bundle_by_name(secret_name=_secret, vault_id=_vault)
                    _privkey = b64decode(_response.data.secret_bundle_content.content).decode("utf-8")
                except Exception as e:
                    ebLogError(f"No passphrase/secret present, Error: {e}")
                    raise e
                else:
                    _msg = (f"key found in vault_id={_vault}, secret name={_secret}")
                    ebLogInfo(_msg)

        for _, _domU in self.__cluctrlobj.mReturnDom0DomUPair():

            _cparam = {"FQDN": _domU, "user": _user}
            _entry = _exakms.mGetExaKmsEntry(_cparam)

            if _entry:
                ebLogInfo(f"Kms entry already exists: {_entry}")
                _exakms.mDeleteExaKmsEntry(_entry)

            ebLogInfo(f"Insert new domU key: {_user}@{_domU}")

            _entry = _exakms.mBuildExaKmsEntry(
                _domU,
                _user,
                _privkey,
                ExaKmsHostType.DOMU 
            )
            _exakms.mInsertExaKmsEntry(_entry)

    def mHandlerAddVmExtraSize(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()

        _jconf: dict                        = aOptions.jsonconf
        _nodes: Optional[List[List[str]]]   = None
        _fs: Optional[ebDomUFilesystem]     = None
        _extra_bytes: Optional[int]         = None
        _edvs: Dict[str, str]               = {}
        _validate_max_size: bool            = True
        _resize_mode: ebDomUFSResizeMode    = ebDomUFSResizeMode.NORMAL

        _fs_mapping: Dict[str, ebDomUFilesystem] = {
            'rootfs':       ebDomUFilesystem.ROOT,
            'home':         ebDomUFilesystem.HOME,
            'u01':          ebDomUFilesystem.U01,
            'u02':          ebDomUFilesystem.U02,
            'grid':         ebDomUFilesystem.GRID,
            'tmp':          ebDomUFilesystem.TMP,
            'var':          ebDomUFilesystem.VAR,
            'varlog':       ebDomUFilesystem.VAR_LOG,
            'varlogaudit':  ebDomUFilesystem.VAR_LOG_AUDIT,
            'crashfiles':   ebDomUFilesystem.CRASHFILES
        }

        _resize_mode_mapping: Dict[str, ebDomUFSResizeMode] = {
            'normal':       ebDomUFSResizeMode.NORMAL,
            'fst_vol_only': ebDomUFSResizeMode.FST_VOL_ONLY,
            'snd_vol_only': ebDomUFSResizeMode.SND_VOL_ONLY,
            'lv_only':      ebDomUFSResizeMode.LV_ONLY,
            'vg_only':      ebDomUFSResizeMode.VG_ONLY
        }

        _edv_ecra_to_oeda_type: Dict[str, str] = {
            'U01': 'USERVOL',
            'SYSTEM': 'BASEVOL'
        }

        if _jconf is not None:

            _nodes = _jconf.get('nodes')

            if 'filesystem' in _jconf:
                if _jconf['filesystem'] not in _fs_mapping:
                    msg: str = f"Unknown filesystem {_jconf['filesystem']}"
                    raise ExacloudRuntimeError(0x10, 0xA, msg)
                _fs = _fs_mapping[_jconf['filesystem']]

            if 'extra_size' in _jconf:
                _extra_bytes = parse_size(_jconf['extra_size'])

            if _jconf.get('validate_max_size') == False:
                _validate_max_size = False

            if 'resize_mode' in _jconf:
                if _jconf['resize_mode'] not in _resize_mode_mapping:
                    msg: str = f"Unknown resize mode {_jconf['resize_mode']}"
                    raise ExacloudRuntimeError(0x10, 0xA, msg)
                _resize_mode = _resize_mode_mapping[_jconf['resize_mode']]

            if 'volumes' in _jconf:
                _edvs = _jconf['volumes'].get('volumetypes', {})

        
        # Resize EDVs first if requested
        _xmlTree = ebTree(aCluCtrlObj.mGetPatchConfig())
        _clusterEDVs = get_edvs_from_cluster_xml(_xmlTree)
        for _dom0, _domu in aCluCtrlObj.mReturnDom0DomUPair():
            _domuEDVs = get_guest_edvs_from_cluster_xml(_xmlTree, _clusterEDVs, _domu)
            with connect_to_host(_dom0, get_gcontext()) as _node:
                for _edv, _size_gb in _edvs.items():
                    _edvInfo, *_ = ( _domuEDV for _domuEDV in _domuEDVs
                                    if _domuEDV.vol_type == _edv_ecra_to_oeda_type[_edv] )
                    _size_bytes = parse_size(_size_gb)
                    _cmd = f"/bin/virsh blockresize {_domu} {_edvInfo.device_path} {_size_bytes}B"
                    node_exec_cmd_check(_node, _cmd)


        _fs_size_payload: Dict[str, str] = \
            _jconf.get('filesystems', {}).get('mountpoints', {}) \
            if _jconf is not None and _jconf.get('filesystems') else {}

        _result: Dict[str, Dict[str, Dict[str, str]]] = {}
        for _dom0, _domu in _nodes if _nodes else [[None, None]]:
            _result = expand_domu_filesystem(
                aCluCtrlObj,
                _dom0,
                _domu,
                _fs,
                _extra_bytes,
                _validate_max_size,
                _resize_mode,
                False,
                perform_dom0_resize = not _edvs,
                payload_overrides_default_sizes = True
            )


        _domu_errors = []
        for _dom0, _domu in _nodes if _nodes else aCluCtrlObj.mReturnDom0DomUPair():
            # Check if any FS is encrypted, to resize the luks volume
            with connect_to_host(_domu, get_gcontext()) as _node:
                for mountpoint, _ in _fs_size_payload.items():
                    try:
                        _mount_info  = getMountPointInfo(_node, mountpoint)
                        if _mount_info.is_luks:
                            ebLogInfo(f"Detected an encrypted luks device on "
                                f"{mountpoint} in {_domu}")
                            resizeOEDAEncryptedFS(aCluCtrlObj, _domu, mountpoint)
                        else:
                            ebLogTrace(f"FS {mountpoint} in {_domu} not encrypted")

                    except Exception as e:
                        ebLogWarn(f"Luks Resize steps on {_domu} for {mountpoint} "
                            f"failed, error is {e}")
                        _domu_errors.append(_domu)

        _result_str: str = json.dumps(_result, indent=4)
        ebLogInfo(f"DomU filesystem resize completed. Result: {_result_str}")
        if _domu_errors:
            _err = (f"Exacloud detected an error while doing the FS Resize "
                f"steps for an encrypted volume in {_domu_errors}")
            ebLogError(_err)
            raise ExacloudRuntimeError(0x96, 0x0A, _err)

        req = aCluCtrlObj.mGetRequestObj()
        if req is not None:
            req.mSetData(_result_str)
            db = ebGetDefaultDB()
            db.mUpdateRequest(req)

    def mHandlerAdminSwitchConnectEndpoint(self):
        try:
            self.mHandlerAdminSwitchConnect()
            return 0
        except:
            return 1

    def mHandlerAdminSwitchConnect(self):
        '''
         This method sets up key based access between
         Exacloud and Admin switch and return the Admin
         Switch list to be consumed by Infra Patching and other
         Exacloud operations.
        '''
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()

        _configured_admin_switch_list = []
        if not aCluCtrlObj.mIsOciEXACC():
            ebLogError(f"This feature is only supported for EXACC Currently. Exiting!")
            return
        _sshsetup = ebCluSshSetup(aCluCtrlObj)
        _configured_admin_switch_list, _ = _sshsetup.mSetCiscoSwitchSSHPasswordless(aGenerateSpineSwitchKeys=False, aGenerateAdminSwitchKeys=True)
        return list(set(_configured_admin_switch_list))


    def mHandlerATPBackupRoutes(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()
        _domUs = list(map(operator.itemgetter(1),aCluCtrlObj.mReturnDom0DomUPair()))
        # Safe as already set in so many place as Backup Net VM IF
        # db route script will substitute bondeth1 by veth0 in Namespace mode
        _backup_net = 'bondeth1'
        try:
            _atp_routes = ATPAddBackupRoutes(aOptions.jsonconf, aCluCtrlObj.mGetDebug())
            _atp_routes.mExecute(_domUs,_backup_net)
        # Only catch ValueError for JSON,
        # execution error will already be an Exacloud exception
        except ValueError as e:
            raise ExacloudRuntimeError(0x0654, 0xA, str(e))

    def mHandlerATPIPTables(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()

        _script_path='/opt/exacloud/network/mod_iptables.sh'
        _doms = aCluCtrlObj.mReturnDom0DomUPair()
        try:
            _rule = aOptions.jsonconf["rule"]
            _action = aOptions.jsonconf["action"]
        except ValueError as e:
            raise ExacloudRuntimeError(0x0656, 0xA, str(e))
        
        ebLogInfo("*** iptables rule: %s %s" % (_rule, _action))
        
        if aCluCtrlObj.mIsKVM():
            _protocol = 'tcp'
            _rule_parts = _rule.split('@')
            if len(_rule_parts) > 3:
                _protocol = _rule_parts.pop()
            _rule = '@'.join(_rule_parts)
            _rule_payload = { 'atp': { 'whitelist': { 'client': { 'protocol': { _protocol: [_rule] } } } } }

        for _dom0, _domU in _doms:
            ebLogInfo("*** %s iptables rule on dom0: %s domU:%s" % ('Adding' if _action == 'add' else 'Removing', _dom0, _domU))
            if aCluCtrlObj.mIsKVM():
                ebIpTablesRoCE.mAlterATPIptables(_dom0, _domU, _rule_payload, _action == 'add')
            else:
                _node = exaBoxNode(get_gcontext())
                _node.mConnect(_dom0)
                ## Since this is a very small script, it's ok to update it everytime
                _node.mCopyFile('scripts/network/mod_iptables.sh', _script_path)
                _,_o,_ = _node.mExecuteCmd("/sbin/iptables -nL; sh %s -a %s -r %s -h %s > /tmp/mod_iptables.log 2>&1; /sbin/iptables -nL" % (_script_path, _action, _rule, _domU))
                if not _o:
                    raise ExacloudRuntimeError(0x0657, 0xA, "No output from iptables commands.")
                ebLogDebug(_o.read())
                _node.mDisconnect()

    def mHandlerCaviumColletDiag(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()

        if aOptions is not None and \
           aOptions.jsonconf is not None and \
           aOptions.jsonconf.get("ilom_hostname", None) is not None and \
           aOptions.jsonconf.get("domain_name", None) is not None:

            # Define pass and ilom name
            _lastpwd = aCluCtrlObj.mGetIlomPass()

            _ilomName = "{0}.{1}".format(
                aOptions.jsonconf.get("ilom_hostname"),
                aOptions.jsonconf.get("domain_name")
            )

            # Create connection to ilom
            ebLogInfo("Try authentication: {0}".format(_ilomName))

            _eventList = []
            _numberPages = 3

            _node = exaBoxNode(get_gcontext())

            try:
                _node.mSetPassword(_lastpwd)
                _node.mConnectAuthInteractive(aHost=_ilomName)

                # Diagnositic log extract
                _cmds = []
                _cmds.append(['->', 'show /SP/logs/event/list Severity==(down,critical,major) -o xml'])

                for i in range(1, _numberPages):
                    _cmds.append(["'q'", 'a'])

                _cmds.append(["'q'", 'q'])
                _cmds.append(['->', 'exit'])

                _node.mExecuteCmdsAuthInteractive(_cmds)
                _output = _node.mGetConsoleRawOutput()

                def mExtractTag(aStr, aTag):

                    _pattStart = re.search(f"<{aTag}.*?>", aStr)
                    _pattEnd = re.search(f"</{aTag}>", aStr)

                    if not _pattStart:
                        return None, None

                    _content = aStr[_pattStart.end() : _pattEnd.start()]
                    _rest = aStr[_pattEnd.end():]

                    return _content, _rest

                # Find all entries
                _rest = _output
                _entryContent, _rest = mExtractTag(_rest, "entry")

                _tags = {
                    "dateTime": "DateTime",
                    "class" : "XClass",
                    "type": "Type",
                    "severity": "Severity",
                    "message": "Message"
                }

                while _rest:

                    _dictEvent = {}

                    for _tag, _name in _tags.items():
                        _content, _ = mExtractTag(_entryContent, _tag)
                        _dictEvent[_name] = _content

                    _eventList.append(_dictEvent)
                    _entryContent, _rest = mExtractTag(_rest, "entry")

            finally:
                _node.mDisconnect()

        else:
            ebLogWarn("Missing field in the payload")
            return 1

        _eventResult = {"SP_logs": _eventList}

        # Return reqobj to ECRA
        _reqobj = aCluCtrlObj.mGetRequestObj()
        if _reqobj is not None:
            _reqobj.mSetData(json.dumps(_eventResult))
            _db = ebGetDefaultDB()
            _db.mUpdateRequest(_reqobj)
        else:
            #Console output
            ebLogInfo(json.dumps(_eventResult, sort_keys=True, indent=4))

        return 0

    def mHandlerCaviumReset(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()


        if aOptions is None or \
           aOptions.jsonconf is None or \
           aOptions.jsonconf.get("hostname", None) is None or \
           aOptions.jsonconf.get("ilom_hostname", None) is None or \
           aOptions.jsonconf.get("domain_name", None) is None or \
           aOptions.jsonconf.get("etherface", None) is None:
            ebLogWarn("Missing field in the payload")
            return 1

        _interfaceCaviumMapX9 = {
            "eth1": "6",
            "eth2": "10"
        }

        _interfaceCaviumMapX10 = {
            "eth1": "2",
            "eth2": "6"
        }

        _interfaceCaviumMapX11 = {
            "eth1": "2",
            "eth2": "6"
        }

        _interfaceCaviumMap = _interfaceCaviumMapX9
        _interface = aOptions.jsonconf.get("etherface")
        if _interface not in _interfaceCaviumMap:
            return 1

        # Get target device
        _device = "ilom"
        if aOptions.jsonconf.get("target_device", None) is not None:
            _device = aOptions.jsonconf.get("target_device")

        # Get action
        _action = "reset"
        if aOptions.jsonconf.get("action") in ["reset", "start", "stop"]:
            _action = aOptions.jsonconf.get("action")

        if _device == "dom0":

            _hostName = "{0}.{1}".format(
                aOptions.jsonconf.get("hostname"),
                aOptions.jsonconf.get("domain_name")
            )

            _node = exaBoxNode(get_gcontext())

            try:
                _node.mConnect(aHost=_hostName)

                if aCluCtrlObj.mGetNodeModel(_hostName) == "X10":
                    _interfaceCaviumMap = _interfaceCaviumMapX10
                elif aCluCtrlObj.mGetNodeModel(_hostName) == "X11":
                    _interfaceCaviumMap = _interfaceCaviumMapX11

                if clubonding.get_bond_monitor_installed(_node):
                    if not clubonding.get_bond_monitor_status(_node):
                        ebLogWarn("*** bondmonitor service is down in Dom0: "
                                f"{_hostName}, we will try to restart it...")
                        clubonding.restart_bond_monitor(_node)
                        ebLogInfo("*** bondmonitor service restarted in Dom0: "
                                f"{_hostName}")
                    else:
                        ebLogInfo("*** bondmonitor service up and running in "
                                  f"Dom0: {_hostName}")
                else:
                    ebLogWarn("*** bondmonitor service not installed in Dom0: "
                              f"{_hostName}... Proceed with caution!!! "
                              "forcing a link failover on the eth slaves "
                              "will block the customer network in a "
                              "non-bonded environment!!!")

                if _action in ["reset", "stop"]:
                    _cmd = f"/sbin/ip link set down {_interface}"
                    node_exec_cmd_check(_node, _cmd)

                if _action in ["reset", "start"]:
                    _cmd = f"/sbin/ip link set up {_interface}"
                    node_exec_cmd_check(_node, _cmd)

            finally:
                _node.mDisconnect()


        if _device == "ilom":

            # Define pass and ilom name
            _lastpwd = aCluCtrlObj.mGetIlomPass()

            _ilomName = "{0}.{1}".format(
                aOptions.jsonconf.get("ilom_hostname"),
                aOptions.jsonconf.get("domain_name")
            )

            # Create connection to ilom
            ebLogInfo("Try authentication: {0}".format(_ilomName))

            # Detect version
            _node = exaBoxNode(get_gcontext())
            _syspath = "/SYS/IOU"
            _syssuffix = "00"

            try:
                _node.mSetPassword(_lastpwd)
                _node.mConnectAuthInteractive(aHost=_ilomName)

                _cmds = []
                _cmds.append(['->', 'show /System'])
                _cmds.append(['->', 'exit'])

                _node.mExecuteCmdsAuthInteractive(_cmds)
                _o = _node.mGetConsoleRawOutput()
                ebLogInfo("Read from socket: [{0}]".format(_o))

                if "X10" in _o:
                    _interfaceCaviumMap = _interfaceCaviumMapX10
                    _syspath = "/SYS/MB/RISER"
                    _syssuffix = ""
                elif "X11" in _o:
                    _interfaceCaviumMap = _interfaceCaviumMapX11
                    _syspath = "/SYS/MB/RISER"
                    _syssuffix = ""

            finally:
                _node.mDisconnect()

            # Modify Interfaces
            _slot = _interfaceCaviumMap[_interface]
            _node = exaBoxNode(get_gcontext())

            try:
                _node.mSetPassword(_lastpwd)
                _node.mConnectAuthInteractive(aHost=_ilomName)

                _cmds = []

                if _action in ["reset", "stop"]:
                    _cmds.append(['->', f'stop -script {_syspath}{_slot}/PCIE{_slot}{_syssuffix}'])

                if _action in ["reset", "start"]:
                    _cmds.append(['->', f'start -script {_syspath}{_slot}/PCIE{_slot}{_syssuffix}'])

                _cmds.append(['->', 'exit'])

                _node.mExecuteCmdsAuthInteractive(_cmds)
                _o = _node.mGetConsoleRawOutput()
                ebLogInfo("Read from socket: [{0}]".format(_node.mGetConsoleRawOutput()))

            finally:
                _node.mDisconnect()

        return 0

    def mHandlerClusterDetails(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()
        _dict = {}

        _dict['rackType'] = ""
        _dict['iloms'] = []
        _dict['cells'] = []
        _dict['dom0s'] = []
        _dict['domUs'] = []
        _dict['ibswitches'] = []
        _dict['excloud_clustername'] = aCluCtrlObj.mGetKey().replace("cluster/", "")
        _0s, _Us, _Cs, _Ss = aCluCtrlObj.mReturnAllClusterHosts()

        #Get the Rack type
        for _rack in aCluCtrlObj.mGetEsracks().mGetEsRacksList():
            _dict['rackType'] = aCluCtrlObj.mGetEsracks().mGetEsRackConfig(_rack).mGetEsRackDesc()
            break

        #Get the information of the Iloms
        for _ilom in aCluCtrlObj.mGetIloms().mGetIlomsList():
            _ilomCfg = aCluCtrlObj.mGetIloms().mGetIlomConfig(_ilom)
            if _ilomCfg.mGetIlomId() is not None:
                _dict['iloms'].append(_ilomCfg.mGetDict())

        #Get the information of the Doms, Domus and Cells
        for _machine in aCluCtrlObj.mGetMachines().mGetMachineConfigList():
            _dictM = aCluCtrlObj.mGetMachines().mGetMachineConfig(_machine).mGetDict()
            _type = _dictM["OsType"]
            _nets = _dictM.pop("Networks")

            _dictM['IpAddress'] = ""
            _dictM['BackupIp']  = ""

            if _type in ["LinuxDom0", "LinuxKVM"]:
                if [x for x in _0s if _dictM['HostName'].find(x) != -1]:
                    for _net in _nets:
                        if _net.find("_admin") != -1 and _dictM['IpAddress'] == "":
                            _dictM['IpAddress'] = aCluCtrlObj.mGetNetworks().mGetNetworkConfig(_net).mGetNetIpAddr()
                        if _net.find("_backup") != -1 and _dictM['BackupIp'] == "":
                            _dictM['BackupIp'] = aCluCtrlObj.mGetNetworks().mGetNetworkConfig(_net).mGetNetIpAddr()
                    _dict['dom0s'].append(_dictM)
            elif _type == "LinuxPhysical":
                if [x for x in _Cs if _dictM['HostName'].find(x) != -1]:
                    for _net in _nets:
                        if _net.find("_admin") != -1 and _dictM['IpAddress'] == "":
                            _dictM['IpAddress'] = aCluCtrlObj.mGetNetworks().mGetNetworkConfig(_net).mGetNetIpAddr()
                        if _net.find("_backup") != -1 and _dictM['BackupIp'] == "":
                            _dictM['BackupIp'] = aCluCtrlObj.mGetNetworks().mGetNetworkConfig(_net).mGetNetIpAddr()
                    _dict['cells'].append(_dictM)
            elif _type in ["LinuxGuest", "LinuxKVMGuest"]:
                if [x for x in _Us if _dictM['HostName'].find(x) != -1]:
                    for _net in _nets:
                        if _net.find("_client") != -1 and _dictM['IpAddress'] == "":
                            _neto = aCluCtrlObj.mGetNetworks().mGetNetworkConfig(_net)
                            if _neto.mGetNetNatAddr() != "":
                                _dictM['NatIpAddress'] = _neto.mGetNetNatAddr()

                            if _neto.mGetNetNatHostName() != "":
                                _dictM['NatHostname'] = f"{_neto.mGetNetNatHostName()}.{_neto.mGetNetNatDomainName()}"

                            _dictM['IpAddress'] = _neto.mGetNetIpAddr()
                        if _net.find("_backup") != -1 and _dictM['BackupIp'] == "":
                            _dictM['BackupIp'] = aCluCtrlObj.mGetNetworks().mGetNetworkConfig(_net).mGetNetIpAddr()
                    _dict['domUs'].append(_dictM)

        #Get the information of the switches
        if not aCluCtrlObj.mIsKVM():
            for _sw in aCluCtrlObj.mGetSwitches().mGetSwitchesList():
                _dictM = aCluCtrlObj.mGetSwitches().mGetSwitchConfig(_sw).mGetDict()
                if [x for x in _Ss if _dictM['swid'].find(x) != -1]:
                    _dict['ibswitches'].append(_dictM)

        _reqobj = aCluCtrlObj.mGetRequestObj()
        if _reqobj is not None:
            _reqobj.mSetData(json.dumps(_dict, sort_keys=True))
            _db = ebGetDefaultDB()
            _db.mUpdateRequest(_reqobj)
        else:
            if aCluCtrlObj.mGetDebug():
                ebLogInfo(json.dumps(_dict, sort_keys=True, indent=4))

        ebLogInfo("Cluster details complete")

    def mHandlerGenIncidentFile(self, aOP=None, aUUID=None, aStatusSucc=False):
        """
         Generally, uuid will be get using mGetUUID and it holds good when any exception
         raised by the exacloud. But, many cases we wanted to collect the diag logs
         against a specific UUID / thread. For example, during exadata infra patching, we
         wanted to collect the patching logs for every completed patching request. So,
         this function accept the UUID as an argument and collects the diagnostic for
         exadata patching request.
        """
        aCluCtrlObj = self.mGetCluCtrlObj()
        _options = aCluCtrlObj.mGetArgsOptions()

        _log_str = ""

        if aOP == 'patching':
            _uuid = aUUID
        else:
            _uuid = aCluCtrlObj.mGetUUID()
        _ctx = aCluCtrlObj.mGetCtx()

        # generate incident zip file in case of success case only if param is True
        if aStatusSucc == True and not aCluCtrlObj.mCheckConfigOption("gen_incidentfile_succ_case", "True"): 
            return

        _destdir = _ctx.mGetOEDAPath() + '/requests/' + aCluCtrlObj.mGetExaunitID() + '_' + _uuid
        _ecopt = _ctx.mGetConfigOptions()
        _options = _ctx.mGetArgsOptions()
        if 'diag_level' in list(_ecopt.keys()) and (_ecopt['diag_level'] in ["Verbose", "Normal", "None"]) :
            _lvl = _ecopt['diag_level']
        else:
            _lvl = "None"

        # To collect patch logs only during patching activity.
        if aOP == 'patching':
            dgNode = ebIncidentNode(_lvl, _destdir, _uuid, aCluCtrlObj, _options, None, False, 'patching')
        else:
            dgNode = ebIncidentNode(_lvl, _destdir, _uuid, aCluCtrlObj, _options, None, False)
        tgt = dgNode.process()

        if tgt != None:
            _log_str = "\nGenerated incident file at path:" + tgt
        ebLogInfo(_log_str)

    def mHandlerSnmpPasswords(self, aOptions=None):
        aCluCtrlObj = self.mGetCluCtrlObj()
        if not aOptions: 
            aOptions = aCluCtrlObj.mGetArgsOptions()
        _pchecks = ebCluPreChecks(aCluCtrlObj)
        return _pchecks.mGetAsmDbSnmpPasswords(aOptions)

    def mHandlerJumboOper(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()

        if aOptions.jumboframes:
            if aOptions.jumboframes == 'state':
                state = clujumboframes.jumboFramesState(aCluCtrlObj)
                ebLogInfo(json.dumps(state, indent=4))
            else:
                clujumboframes.configureJumboFrames(
                    aCluCtrlObj, {'jumbo_frames': str(aOptions.jumboframes)})
        else:
            ebLogInfo('aOptions.jumboframes absent')

    def mHandlerUpdateBlockState(self, aOptions=None):
        aCluCtrlObj = self.mGetCluCtrlObj()

        if not aOptions: 
            aOptions = aCluCtrlObj.mGetArgsOptions()

        _state = aOptions.blockstate
        if _state == 'True'or _state == 'False':
            _blkstate = "blocked" if _state == 'True' else "unblocked"
            ebLogInfo("Exacloud is %s for any further operations" % _blkstate)
            _db = ebGetDefaultDB()
            _db.mDelRegEntry('exacloud_block_state')
            _db.mSetRegEntry('exacloud_block_state', _state, '', '')
        else:
            raise ExacloudRuntimeError(0x0788, 0xA, 'Invalid block state')

    def mHandlerGetCellIBInfo(self):
        aCluCtrlObj = self.mGetCluCtrlObj()

        # This method should not be called in the context of KVM -- log a warning and return None as no Pkeys exists
        if aCluCtrlObj.mIsKVM():
            ebLogWarn('*** GetCellIBInfo is an invalid call for KVM based target')
            return None

        ebLogVerbose("mGetCellIBInfo: Get Cell IB Information.")

        _ip_subnets = []
        for _host, _entries in list(aCluCtrlObj.mReturnCellNodes(aNetMask=True).items()):
            _ips = []
            for _, _cell_type, _, _ip, _netmask in _entries:
                if _cell_type != 'admin':
                    _ips.append({'ip': _ip, 'netmask': _netmask})
            _ip_subnets.append({'cell' : _host, 'ips' : _ips})

        _spk, _cpk = aCluCtrlObj.mGetPkeysConfig()

        _switch = aCluCtrlObj.mReturnSwitches(True)[0]
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_switch)
        _cmdstr = 'smpartition list active no-page | grep ' + _spk
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        _node.mDisconnect()

        _result = {'pname' : _o.read().split('=')[0].strip(), 'pkey' : _spk, 'mtu' : 65520, "ip_subnets" : _ip_subnets}
        _reqobj = aCluCtrlObj.mGetRequestObj()
        if _reqobj is not None:
            _reqobj.mSetData(json.dumps(_result, sort_keys=True))
            _db = ebGetDefaultDB()
            _db.mUpdateRequest(_reqobj)
        else:
            print(json.dumps(_result, sort_keys=True))

    def mHandlerGetVMCoreLogs(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        # Initialize response
        ebLogInfo("Collecting VM core logs...")
        # Check if the payload is present
        aOptions = aCluCtrlObj.mGetArgsOptions()
        if not aOptions.jsonconf:
            raise ExacloudRuntimeError(0x0765, 0xA, "Missing json payload")
        # Validate payload
        if not aOptions.jsonconf.get("vm_name"):
            raise ExacloudRuntimeError(0x0765, 0xA, f"VM name not present in payload.")
        # Handle retrieval, compression and OSS upload
        _collector = ebVMCoreCollector(aCluCtrlObj, aOptions.jsonconf)
        _rc = _collector.mHandleLogCollection()
        # After all hosts are iterated, send request object back with bucket and object details
        _responseObj = {"oss_repo_url": "Unable to upload to OSS"}
        if _rc == 0:
            _responseObj = {"oss_repo_url": _collector.mGetTargetOssPath()}
        _reqobj = aCluCtrlObj.mGetRequestObj()
        if _reqobj is not None:
            _reqobj.mSetData(json.dumps(_responseObj))
            _db = ebGetDefaultDB()
            _db.mUpdateRequest(_reqobj)
        ebLogInfo(json.dumps(_responseObj, sort_keys=True))

    def mHandlerCheckConnection(self):
        #
        #  Test connectivity (login/pwd, exabox ssh key, oeda sshkey...)
        #
        # Initialize response
        aCluCtrlObj = self.mGetCluCtrlObj()

        def check_connection(_domX):

            if not aCluCtrlObj.mPingHost(_domX):
                ebLogWarn('*** %s host does not respond to ping (skip ssh connection)' % (_domX))
                return
            _node = exaBoxNode(get_gcontext())
            ebLogInfo('*** Attempting connection to: %s' % (_domX))
            try:
                _node.mConnect(aHost=_domX)
                _node.mExecuteCmdLog('hostname -f')
            except:
                ebLogInfo('*** Authentication Exception caught for: %s(ssh key not found/valid ?)' % (_domX))
            _node.mDisconnect()
        #
        # Parallel Execution on all dom0/domU of the cluster
        #
        _plist = ProcessManager()

        for _dom0, _domU in aCluCtrlObj.mReturnDom0DomUPair():
            _p = ProcessStructure(check_connection, [_dom0])
            _p.mSetMaxExecutionTime(30*60) # 30 minutes timeout
            _p.mSetJoinTimeout(2)
            _p.mSetLogTimeoutFx(ebLogWarn)
            _plist.mStartAppend(_p)

            _p = ProcessStructure(check_connection, [_domU])
            _p.mSetMaxExecutionTime(30*60) # 30 minutes timeout
            _p.mSetJoinTimeout(2)
            _p.mSetLogTimeoutFx(ebLogWarn)
            _plist.mStartAppend(_p)
        
        _plist.mJoinProcess()

    def mHandlerCheckConfig(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        lCmd = "/bin/bash install.sh -cf {0} -u {1} {2}".format(aCluCtrlObj.mGetRemoteConfig(), \
                                                                aCluCtrlObj.mFetchOedaStep(OSTP_VALIDATE_CNF), \
                                                                aCluCtrlObj.mGetOEDAExtraArgs())
        ebLogInfo('Running: ' + lCmd)
        _out = aCluCtrlObj.mExecuteCmdLog(lCmd, aCurrDir=aCluCtrlObj.mGetOedaPath())
        aCluCtrlObj.mParseOEDALog(_out)

    def mHandlerHealthCheckPostProv(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()
        _cfg_check = executeHealthPostProv(aCluCtrlObj, aOptions)

        # Return reqobj to ECRA
        _reqobj = aCluCtrlObj.mGetRequestObj()
        if _reqobj is not None:
            _reqobj.mSetData(json.dumps(_cfg_check, sort_keys=True))
            _db = ebGetDefaultDB()
            _db.mUpdateRequest(_reqobj)
        else:
            #Console output
            ebLogInfo(json.dumps(_cfg_check, sort_keys=True))

        return 0

    def mHandlerFetchKeys(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()

        if 'hostname' in aOptions and aOptions.hostname:                        
            _keysobj = ebCluFetchSshKeys(aCluCtrlObj, aOptions.hostname)               
            return _keysobj.mFetchSshKeys(aOptions)                             

    def mHandlerElasticInfo(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()

        if aCluCtrlObj.mIsExaScale():
            _exascale = ebCluExaScale(aCluCtrlObj)
            _exascale.mUpdateVolumesOedacli(aWhen="DeleteNode")

        _elasticobj = ebCluElastic(aCluCtrlObj, aOptions)                              
        _rc = _elasticobj.mPatchXMLForElastic(aOptions)
        #Patching the customised value by the customer primarily (ADBS)
        if aCluCtrlObj.mIsAdbs():
            _rc = _elasticobj.mPatchXMLForElasticADBS()                    

        if aCluCtrlObj.mIsExaScale():
            _exascale = ebCluExaScale(aCluCtrlObj)
            _exascale.mUpdateVolumesOedacli(aWhen="AddNode")

        return _rc   

    def mHandlerMountVolume(self):  
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()
        
        if aCluCtrlObj.mIsExaScale():                                  
            _exascale = ebCluExaScale(aCluCtrlObj)                     
            return _exascale.mMountVolume(aOptions)                   
        else:
            raise ExacloudRuntimeError(0x0734, 0xA, 'endpoint not supported in non Exascale env')
                                                                
    def mHandlerUnmountVolume(self):                            
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()
        
        if aCluCtrlObj.mIsExaScale():                                  
            _exascale = ebCluExaScale(aCluCtrlObj)                     
            return _exascale.mUnmountVolume(aOptions) 
        else:
            raise ExacloudRuntimeError(0x0734, 0xA, 'endpoint not supported in non Exascale env')

    def mHandlerAddOEDAKey(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()
        
        _elasticobj = ebCluElastic(aCluCtrlObj, aOptions)                              
        _rc = _elasticobj.mOedaAddKey(aOptions)                                 
        return _rc
    
    def mHandlerPrepareCompute(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()
        
        ebLogTrace(f"json payload for 'prepare_compute' workflow: {aOptions.jsonconf}")
        _elasticobj = ebCluElastic(aCluCtrlObj, aOptions)                              
        _elasticobj.mPrepareCompute(aOptions)
        return 0

    def mHandlerAddOEDAKeyByHost(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()
        
        _elasticobj = ebCluElastic(aCluCtrlObj, aOptions)                              
        _rc = _elasticobj.mOedaAddKeyByHost(aOptions)                           
        return _rc  

    def mHandlerCheckCluster(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()
        
        ebLogInfo('Checking cluster configuration')
        if(aOptions.healthcheck == 'custom'):
            _hcobj = ebCluHealth(aCluCtrlObj, aOptions)
        else:
            if aOptions.healthcheck == 'exachk':
                _enable_exachk = aCluCtrlObj.mCheckConfigOption('enable_exachk')
                if _enable_exachk and 'domu' in _enable_exachk:
                    aOptions.jsonconf["domu_verify"] = _enable_exachk["domu"]
                else:
                    aOptions.jsonconf["domu_verify"] = "False"
            _hcobj = ebCluHealthCheck(aCluCtrlObj, aOptions)
        return _hcobj.mDoHealthCheck(aOptions)


    def mHandlerCollectLog(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()
        
        aCmd = aCluCtrlObj.mGetCmd()
        ebLogInfo('Run cluster diagnosis log collection')
        _diagobj = exaBoxDiagCtrl(aCluCtrlObj)
        return _diagobj.mRunDiagnosis(aCmd, aOptions)

    def mHandlerRunCompTool(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()
        
        aCmd = aCluCtrlObj.mGetCmd()
        ebLogInfo('Run cluster compliance tool management')
        _diagobj = exaBoxDiagCtrl(aCluCtrlObj)
        return _diagobj.mRunDiagnosis(aCmd, aOptions)

    def mHandlerVmTmpKeyOp(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()
        
        _jconf = aOptions.jsonconf
        if "op" not in _jconf.keys():
            raise ExacloudRuntimeError(0x0119, 0xA, "Missing 'op' key in jsonconf")

        if _jconf["op"] == "get":
            aCluCtrlObj.mGenerateTmpKeyVm(aOptions)

        elif _jconf["op"] == "clean":
            aCluCtrlObj.mCleanUpTmpKeyVm(aOptions)

        elif _jconf["op"] == "validate":
            aCluCtrlObj.mValidateTmpKeyVm(aOptions)

        else:
            raise ExacloudRuntimeError(0x0119, 0xA, "Invalid 'op' key in jsonconf: {0}".format(_jconf["op"]))

        return 0

    def mHandlerGetEnvInfo(self):
        aCluCtrlObj = self.mGetCluCtrlObj()

        _info = aCluCtrlObj.mEnvInfo()

        # Return reqobj to ECRA
        _reqobj = aCluCtrlObj.mGetRequestObj()
        if _reqobj is not None:
            _reqobj.mSetData(json.dumps(_info, sort_keys=True))
            _db = ebGetDefaultDB()
            _db.mUpdateRequest(_reqobj)
        else:
            #Console output
            ebLogInfo(json.dumps(_info, sort_keys=True))

        return 0

    def mHandlerResetEnv(self):
        aCluCtrlObj = self.mGetCluCtrlObj()

        def _runCmdLog(aNode, aCmd):
            aNode.mExecuteCmdLog(aCmd)

        def _cleanup_fn(aNode,aOpts=None):
            _oeda_path = aCluCtrlObj.mGetCtx().mGetOEDAPath()
            _runCmdLog(aNode, 'hostname')
            _runCmdLog(aNode, '[ -d '+_oeda_path+' ] && ( cd '+_oeda_path+' ; rm -f log/* )')
            _runCmdLog(aNode, '[ -d '+_oeda_path+' ] && ( cd '+_oeda_path+' ; rm -f WorkDir/Diag* )')

        aCluCtrlObj.mExecuteOnClusterDom0(_cleanup_fn)

    def mHandlerEXACCInfraPatchPayloadList(self):
        """
        List Patches Metadata file from /u01/downloads which describes PatchPayloads Directory
        """
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()

        _infrapatchobj = ebCluInfraPatch(aCluCtrlObj, aOptions)
        _rc = _infrapatchobj.mEXACCInfraPatchPayloadList(aOptions)
        return _rc

    def mHandlerInfo(self):
        aCluCtrlObj = self.mGetCluCtrlObj()

        lCmd = "/bin/bash install.sh -cf {0} -l {1}".format(aCluCtrlObj.mGetRemoteConfig(), aCluCtrlObj.mGetOEDAExtraArgs())
        ebLogInfo('Executing: ' + lCmd)
        ebLogInfo("SHARED ENVIRONMENT CONFIG {0}".format(aCluCtrlObj.mGetSharedEnv()).upper())
        aCluCtrlObj.mExecuteCmdLog(lCmd, aCurrDir=aCluCtrlObj.mGetOedaPath())
        aOptions = aCluCtrlObj.mGetArgsOptions()
        _sshkey = aCluCtrlObj.mGetUserkey(aOptions)
        if _sshkey:
            aCluCtrlObj.mValidatesshkey(_sshkey)

    def mHandlerOpctlCmd(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()

        _dom0s, _, _cells, _ = aCluCtrlObj.mReturnAllClusterHosts()
        host_info = {"dom0s": _dom0s, "cells": _cells}
        opctlHandle = ebOpctlMgr(aCluCtrlObj, aCluCtrlObj.mGetKey(), aCluCtrlObj.mGetPatchConfig(), host_info)
        _rc = opctlHandle.mExecuteCmd(aOptions)

    def mHandlerValidateCell(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()

        cluValidateHandle = ebCluCellValidate(aCluCtrlObj,aOptions)
        _rc = cluValidateHandle.mValidateCell(aOptions)

    def mHandlerExaComputePatch(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()

        _log_path = aCluCtrlObj.mGetOedaPath() + '/log/patchmgr_logs'
        exaComputePatchHandle = ebCluExaComputePatch(aCluCtrlObj, aOptions)
        return exaComputePatchHandle.mInvokeExaComputePatch(_log_path)

    def mHandlerPostCompute(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()

        cluPostComputeValidate = ebCluPostComputeValidate(aCluCtrlObj,aOptions)
        _rc = cluPostComputeValidate.mPostComputeValidate(aOptions)

    def mHandlerConfigureHostAcess(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()

        _rc = aCluCtrlObj.mConfigureHostAccess(aOptions)

    def mHandleConfigureVMConsole(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()

        _rc = aCluCtrlObj.mConfigureVMConsole(aOptions)

    def mHandlerNetworkReconfig(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()

        reconfig = ebCluNetworkReconfig(aCluCtrlObj, aOptions)
        reconfig.apply()

    def mHandlerRevertNetworkReconfig(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()

        revertReconfig = ebCluRevertNetworkReconfig(aCluCtrlObj, aOptions)
        revertReconfig.apply()

    def mHandlerNetworkBondingModification(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()

        op = "modification"
        netBonding = ebCluNetworkBonding(aCluCtrlObj, aOptions, operation=op)
        netBonding.mApply(op)

    def mHandlerNetworkBondingValidation(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()

        op = "validation"
        netBonding = ebCluNetworkBonding(aCluCtrlObj, aOptions, operation=op)
        netBonding.mApply(op)

    def mHandlerCelldiskStorage(self):
        """
        Handler method for cell_storage_celldisks REST method call
        """
        aCluCtrlObj = self.mGetCluCtrlObj()

        _storage_config = ebCluStorageConfig(aCluCtrlObj, aCluCtrlObj.mGetConfig())
        (_total_space_output_GB, _free_space_output_GB) = _storage_config.mListCellDisksSize()
        _result = {"total_storage_celldisks_GB": _total_space_output_GB, "free_storage_celldisks_GB": _free_space_output_GB}
        _ovm_utils_obj = ebCluUtils(aCluCtrlObj)
        _ovm_utils_obj.mUpdateRequestObjectData(_result)

    def mHandlerReclaimMountpointSpace(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()

        _reclaimMountpointObject = ebCluMountpointReclaimSpace(aCluCtrlObj, aOptions)
        _reclaimMountpointObject.mReclaimMountpointSpace()

    def mHandlerCheckRoceConfiguredDom0(self):                                                                                                                                                                     
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()

        _exascale = ebCluExaScale(aCluCtrlObj)
        _exascale.mCheckDom0Roce(aOptions)

    def mHandlerConfigureDom0Roce(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()

        _exascale = ebCluExaScale(aCluCtrlObj)
        _exascale.mConfigureDom0Roce(aOptions)

    def mHandlerConfigDns(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()

        _rc = 0
        if aOptions.setupdns:
            ebLogInfo("Configuring DNS entries for type: {0}".format(aOptions.setupdns))
            ebDNSConfig(aOptions, aOptions.configpath).mConfigureDNS(aOptions.setupdns)
            _rc = 0
        else:
            ebLogError('setupdns option required for configuring DNS')
            _rc = ebError(0x0759)

        return _rc
    
    def mHandlerXsVaultOperation(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()

        ebLogInfo("*** Perform vault Operation")
        _utils = aCluCtrlObj.mGetExascaleUtils()
        return _utils.mDoVaultOp(aOptions)
    
    def mHandlerXsGet(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()

        ebLogInfo("*** Perform Xs Get Operation")
        _utils = aCluCtrlObj.mGetExascaleUtils()
        return _utils.mDoXsGetOp(aOptions)
    
    def mHandlerXsPut(self):
        aCluCtrlObj = self.mGetCluCtrlObj()
        aOptions = aCluCtrlObj.mGetArgsOptions()

        ebLogInfo("*** Perform Xs Put Operation")
        _utils = aCluCtrlObj.mGetExascaleUtils()
        return _utils.mDoXsPutOp(aOptions)

    def mHandlerValidateVolumes(self, aOptions=None):
        aCluCtrlObj = self.mGetCluCtrlObj()
        if not aOptions: 
            aOptions = aCluCtrlObj.mGetArgsOptions()

        _data_d = {}
        _err = None
        _rc = -1
        def _mUpdateRequestData(rc, aData, err):
            """
            Updates request object with the response payload
            """
            _reqobj = self.__cluctrlobj.mGetRequestObj()
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

        if self.__cluctrlobj.mIsExaScale():
            _exascale = ebCluExaScale(self.__cluctrlobj)
            _edvvolume_list = []
            if aOptions and aOptions.jsonconf and 'edvvolume' in aOptions.jsonconf and aOptions.jsonconf["edvvolume"]:
                _edvvolume_list = aOptions.jsonconf["edvvolume"]
            if aOptions and aOptions.jsonconf and 'guestname' in aOptions.jsonconf and aOptions.jsonconf["guestname"]:
                for _dom0, _domU in self.__cluctrlobj.mReturnDom0DomUPair():
                    if _domU == aOptions.jsonconf["guestname"]:
                        _rc, _data_d = _exascale.mPerformValidateVolumesCheck(_dom0, _domU, _edvvolume_list)
            else:
                 for _dom0, _domU in self.__cluctrlobj.mReturnDom0DomUPair():
                    _rc, _data_d = _exascale.mPerformValidateVolumesCheck(_dom0, _domU, _edvvolume_list)

            _rc = 0
            _mUpdateRequestData(_rc,_data_d,_err)
        else:
            raise ExacloudRuntimeError(0x0734, 0xA, 'endpoint not supported in non Exascale env')

    def mHandlerXsUpdateExascale(self):
        _ebox = self.__cluctrlobj
        aOptions = _ebox.mGetArgsOptions()

        ebLogInfo('*** Performing Exascale cell management operation')
        _ebox.mPublishNewNodeKey(aOptions)

        _elasticCellManager = ebCluElasticCellManager(_ebox, aOptions, False)
        _rc = _elasticCellManager.mClusterExascaleCellUpdate(aOptions)
        return _rc

    def mHandlerXsAcfsOperations(self, aOptions=None):
        _ebox = self.__cluctrlobj
        if not aOptions:
            aOptions = _ebox.mGetArgsOptions()

        _utils = _ebox.mGetExascaleUtils()
        _operation = aOptions.jsonconf["acfs_op"]
        if _operation == "create":
            _utils.mCreateACFS(aOptions)
        elif _operation == "resize":
            _utils.mResizeACFS(aOptions)
        elif _operation == "get":
            _utils.mGetACFSSize(aOptions)
        elif _operation == "mount":
            _utils.mMountACFS(aOptions)
        elif _operation == "unmount":
            _utils.mUnMountACFS(aOptions)
        elif _operation == "remove":
            _utils.mRemoveACFS(aOptions)
        return 0

    def mHandlerXsUpdateNodesConf(self, aOptions=None):
        _ebox = self.__cluctrlobj
        if not aOptions:
            aOptions = _ebox.mGetArgsOptions()

        _utils = _ebox.mGetExascaleUtils()
        _utils.mCreateVMbackupNodesConf(aOptions)

    def mHandlerXsEnableAutoFileEncryption(self, aOptions=None):
        _ebox = self.__cluctrlobj
        if not aOptions:
            aOptions = _ebox.mGetArgsOptions()

        _utils = _ebox.mGetExascaleUtils()
        _utils.mEnableAutoFileEncryption(aOptions)
        return 0


