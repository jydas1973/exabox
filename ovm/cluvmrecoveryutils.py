#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/ovm/cluvmrecoveryutils.py /main/28 2025/09/23 07:26:34 aararora Exp $
#
# cluvmrecoveryutils.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      cluvmrecoveryutils - Implementation layer for the VM recovery
#
#    DESCRIPTION
#      Provide Utility Class for Node recovery
#
#    NOTES
#      NONE
#
#    MODIFIED   (MM/DD/YY)
#    akkar       08/18/25 - Bug 38313259: Fix RTG image copy during node
#                           recovery
#    aararora    08/05/25 - ER 38132942: Single stack support for ipv6
#    rajsag      07/29/25 - bug 38249275 - exacc:24.3.2.4.0:delete node:
#                           clunoderemovegideletetask step is failing due to
#                           stale entries not getting cleaned up
#.   akkar       07/22/25 - Bug 38222695 - Patch xml domuVersion
#    akkar       02/04/25 - Bug 37545630 - Enable root access for node recovery
#    pbellary    01/10/25 - Bug 37234676 - NODE RECOVERY : VMBACKUP RESTORATION FAILED WITH WARNING ABOUT CHECKING AT LEAST 3 VOTING DISK ONLINE
#    naps        10/24/24 - Bug 37192649 - Handle eth0 removal per node instead
#                           of cluster wide.
#    pbellary    10/18/24 - Bug 37186142 - NODE RECOVERY - VM RESTORED FROM BACKUP HAS DBCS AGENT CONNECTION ISSUE: DOM0 NFTABLES DO NOT ALLOW PORT 7060
#    pbellary    06/06/24 - Bug 36698695 - NODE RECOVERY : VM BACKUP FAILED DUE TO TIMEOUT WHILE WAITING FOR SSH PORT
#    pbellary    05/24/24 - Bug 36651236 - NODE RECOVERY: DOMU AFTER VMBACKUP RESTORE HAVE NO ROCE CONNECTIVITY AS IT USES WRONG DOM0 QINQ VF
#    pbellary    05/16/24 - Bug 36411756 - NODE RECOVERY : VM BACKUP FAILED WITH UNBOUNDLOCALERROR 
#    aararora    05/03/24 - ER 36485120: IPv6 support in exacloud
#    pbellary    05/03/24 - Bug 36577256 - NODE RECOVERY - DB INSTANCE ON RECOVERED VM IS IN OFFLINE STATE AFTER NODE RECOVERY COMPLETED
#    pbellary    04/29/24 - Bug 36550891 - NODE RECOVERY : CP SHOULD NOT PASS BADNODES FIELD DURING IN-PLACE RECOVERY
#    pbellary    04/22/24 - Bug 36540390 - NODE RECOVERY : VMBACKUP RESTORE SHOULD ADD FORCE FLAG TO REINSTALL DBCS-AGENT
#    pbellary    04/02/24 - Bug 36447355 - NODE RECOVERY : ADD NODE "EXAUNIT-ATTACH-COMPUTE" FAILED AT TASK "CONFIGURECLUSTERWARE"
#    joysjose    03/07/24 - Bug 36301106 - Fortify - INSECURE RANDOM - CLUVMRECOVERYUTILS.PY
#    pbellary    02/20/24 - Bug 36384090 - NODE RECOVERY : VMBACKUP RESTORE FAILED WITH ERROR "HOOK SCRIPT EXECUTION FAILED"
#    pbellary    02/20/24 - Bug 36312160 - NODE RECOVERY : SOME RPMS ARE MISSING UNDER /U02 ON VM RESTORED FROM VM BACKUP
#    pbellary    02/02/24 - Bug 36253784 - NODE RECOVERY : /U02 ON VM RESTORED FROM VM BACKUP IS NOT MOUNTED PROPERLY RESULTING IN MISSING DATA
#    pbellary    11/10/23 - Bug 35939171 - NODE RECOVERY: POST VM BACKUP RESTORE OPERATION UNABLE TO CONNECT TO DOMU USING ROOT KEYS 
#    pbellary    10/06/23 - Enh 35784380 - NODE RECOVERY: VM SHOULD BE REGISTERED BEFORE INVOKING VMBACKUP RECOVERY
#    pbellary    10/06/23 - Creation
#

from exabox.ovm.cludbaas import ebCluDbaas
from exabox.core.Node import exaBoxNode
import exabox.ovm.clubonding as clubonding
from exabox.core.Context import get_gcontext
from exabox.ovm.csstep.cs_util import csUtil
from exabox.ovm.clumisc import ebCluPreChecks
from exabox.tools.oedacli import OedacliCmdMgr
from exabox.ovm.hypervisorutils import getHVInstance
from exabox.ovm.cluiptablesroce import ebIpTablesRoCE
from exabox.ovm.cluserialconsole import serialConsole
from exabox.ovm.cluvmconsole_deploy import VMConsoleDeploy
from exabox.core.Error import ebError, ExacloudRuntimeError, gNodeElasticError, gReshapeError
from exabox.exakms.ExaKmsEntry import ExaKmsEntry, ExaKmsHostType
from exabox.utils.node import connect_to_host, node_cmd_abs_path_check, node_exec_cmd, node_exec_cmd_check, node_update_key_val_file
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace, ebLogVerbose
from .cludbaas import ebCluDbaas, getDatabaseHomes, getDatabases, cloneDbHome, addInstance, getDatabaseDetails, deleteInstance
import xml.etree.ElementTree as ET
from exabox.ovm.sysimghandler import getDom0VMImagesInfo, getDom0VMImageLocation, getVMImageArchiveInRepo, \
    getNewestVMImageArchiveInRepoNodeRecovery, getNewestVMImageArchiveInRepo, copyVMImageVersionToDom0IfMissing, formatVMImageBaseName, mIsRtgImg
from ast import literal_eval
from datetime import datetime
from functools import cmp_to_key
import xml.etree.ElementTree as ET
import os, time, re, uuid, shutil, random, secrets, string, traceback
import re
from tempfile import NamedTemporaryFile
import traceback
from exabox.utils.common import version_compare
from exabox.network.NetworkUtils import NetworkUtils
from typing import Iterable, Optional, Dict, Any

class NodeRecovery(object):

    def __init__(self, aCluCtrlObj, aOptions):

        self.__cluctrl = aCluCtrlObj
        self.__options = aOptions
        self.__dbaasobj = ebCluDbaas(self.__cluctrl, aOptions)
        self.__srcdomU = ""
        self.__srcdom0 = ""
        self.__adminNetwork = {
            "IPADDR": "",
            "NETMASK": "",
            "GATEWAY": "",
            "NETWORK":"",
            "BROADCAST":""
        }
    
    # Constants for known image prefixes  
    SYSTEM_BOOT_PREFIX = "System.first.boot"
    GRID_KLONE_PREFIX = "grid-klone"
    TARGET_DIR_PREFIX = "/EXAVMIMAGES/"

    def mGetAdminIpAddr(self):
        return self.__adminNetwork.get("IPADDR", "")

    def mGetAdminNetMask(self):
        return self.__adminNetwork.get("NETMASK", "")

    def mGetAdminGateway(self):
        return self.__adminNetwork.get("GATEWAY", "")

    def mGetAdminNetwork(self):
        return self.__adminNetwork.get("NETWORK", "")

    def mGetAdminBroadcast(self):
        return self.__adminNetwork.get("BROADCAST", "")

    def mSetSrcDom0DomU(self, aNewDom0, aNewDomU):
        _dom0 = aNewDom0
        _domU = aNewDomU
        _ebox = self.__cluctrl
        _connectableDomU = None
        _olsNodeList=[]
        _newNodeList = []
        _newNodeList.append(_domU)
        for _, _domU in _ebox.mReturnDom0DomUPair():
            if _domU in _newNodeList:
                continue
            _node = exaBoxNode(get_gcontext())
            _node.mSetUser('root')
            if not _node.mIsConnectable(_domU):
                ebLogWarn(f"*** mSetSrcDom0DomU: DomU {_domU} is not connectable. Run the temporal keys addition workflow for existing VMs. Root ssh access is required for this operation.")
                continue

            if _ebox.mIsExaScale():
                _node.mDisconnect()
                _connectableDomU = _domU.split('.')[0]
                ebLogInfo(f"ExaScale environment, setting src domU as: {_connectableDomU}")
                break

            _node.mConnect(aHost=_domU)
            _cmd = "/usr/bin/cat /etc/oratab | /usr/bin/grep '^+ASM.*'"
            _i, _o, _e = _node.mExecuteCmd(_cmd)
            if _node.mGetCmdExitStatus() != 0:
                _node.mDisconnect()
                continue
            _out = _o.readlines()
            _path = _out[0].split(':')[1].strip()
            _, _o, _e = _node.mExecuteCmd(_path + '/bin/crsctl check crs')
            if _node.mGetCmdExitStatus() != 0:
                _node.mDisconnect()
                continue

            if not _olsNodeList:
                _, _o, _e = _node.mExecuteCmd(_path + '/bin/olsnodes -s -n|grep Active')
                _out = _o.readlines()
                ebLogInfo(f"olsnodes reported: {_out}")
                if _node.mGetCmdExitStatus() != 0:
                    _node.mDisconnect()
                    _detail_error = "No active node in the cluster"
                    _ebox.mUpdateErrorObject(gNodeElasticError['NO_ACTIVE_NODE'], _detail_error)
                    raise ExacloudRuntimeError(0x0757, 0xA, _detail_error)
                else:
                    for _entry in _out:
                        _olsNodeList.append(_entry.split("\t")[0].strip())

            _node.mDisconnect()
            if _domU.split('.')[0] in _olsNodeList:
                _connectableDomU = _domU.split('.')[0]
            else:
                continue
            ebLogInfo(f"Connectable DomU:{_connectableDomU} detected.")
            break
        if _connectableDomU is None:
            _detail_error = "No Pingable/Active node in the cluster"
            _ebox.mUpdateErrorObject(gNodeElasticError['NO_ACTIVE_NODE'], _detail_error)
            raise ExacloudRuntimeError(0x0757, 0xA, _detail_error )

        for _dom0, _domU in _ebox.mReturnDom0DomUPair():
            if _connectableDomU == _domU.split('.')[0]:
                self.__srcdomU = _domU
                self.__srcdom0 = _dom0
                break

        ebLogInfo(f"Selected source node - {self.__srcdom0} : {self.__srcdomU} for the operation.")

    def mGetSrcDomU(self):
        return self.__srcdomU

    def mGetSrcDom0(self):
        return self.__srcdom0

    def mCopyPubKey(self, aDom0, aLocalFile, aRemoteFile):
        """ Copy File to remote node
        """
        _dom0 = aDom0
        try:
            _remote_dir = os.path.dirname(aRemoteFile)
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost = _dom0)
            if _node.mFileExists(_remote_dir):
                _node.mCopyFile(aLocalFile, aRemoteFile)
                _node.mExecuteCmdLog(f"/usr/bin/chmod 600 {aRemoteFile}")
            else:
                ebLogError(f"*** Failed to copy {aLocalFile} to dom0:{_dom0}  {_remote_dir} directory not exists")
        except Exception as e:
            ebLogError(f"*** Failed to copy {aLocalFile} to dom0:{_dom0} at location:{aRemoteFile}, ERROR: {e}")
        finally:
            _node.mDisconnect()

    def mConfigurePasswordlessAllUsers(self):
        _userNames = []
        _ebox = self.__cluctrl
        for _userId in _ebox.mGetUsers().mGetUsers():
            _userConfig = _ebox.mGetUsers().mGetUser(_userId)
            _userName = _userConfig.mGetUserName()
            _userNames.append(_userName)

        for _userName in set(_userNames):
            ebLogInfo(f"Configuring passwordless on user {_userName}")
            self.mConfigurePasswordLessDomU(_userName)

    def mConfigurePasswordLessDomU(self, aUser):

        _ebox = self.__cluctrl
        _domUs = [x[1] for x in _ebox.mReturnElasticAllDom0DomUPair()]

        if aUser == 'root':
            _home_dir = '/root'
        else:
            _home_dir = f'/home/{aUser}'

        _keyType = "rsa"

        _exakms = get_gcontext().mGetExaKms()
        if _exakms.mGetDefaultKeyAlgorithm() == "ECDSA":
            _keyType = "ecdsa"

        for _actualDomU in _domUs:

            #Create key on actual domu
            ebLogInfo(f'Create key for user: {aUser} on {_actualDomU}')

            try:
                _node = exaBoxNode(get_gcontext())
                #Lets connect with default root user, since non-root users would be not be available.
                #root user does have permission to setup keys for other users.
                _node.mSetUser('root')
                _node.mConnect(aHost=_actualDomU)

                node_exec_cmd_check(_node, f'/bin/su - {aUser} -c "/bin/mkdir -p {_home_dir}/.ssh"')
                node_exec_cmd_check(_node, f'/bin/su - {aUser} -c "/bin/chown `id -u {aUser}`:`id -g {aUser}` {_home_dir}/.ssh"')
                node_exec_cmd_check(_node, f'/bin/su - {aUser} -c "/bin/chmod 700 {_home_dir}/.ssh"')

                if not _node.mFileExists(f'{_home_dir}/.ssh/id_{_keyType}') and not _node.mFileExists(f'{_home_dir}/.ssh/id_{_keyType}.pub'):

                    if _keyType == "ecdsa":
                        _cmd = f'/bin/su - {aUser} -c "echo y | /bin/ssh-keygen -t ecdsa -b 384 -q -C \'USER_KEY\' -N \'\' -f {_home_dir}/.ssh/id_{_keyType}"'
                        node_exec_cmd_check(_node, _cmd)
                    else:
                        _cmd = f'/bin/su - {aUser} -c "echo y | /bin/ssh-keygen -q -C \'USER_KEY\' -N \'\' -f {_home_dir}/.ssh/id_{_keyType}"'
                        node_exec_cmd_check(_node, _cmd)

                _cmd = f'/bin/su - {aUser} -c "/bin/chmod 600 {_home_dir}/.ssh/id_{_keyType}*"'
                node_exec_cmd_check(_node, _cmd)
                _cmd = f'/bin/su - {aUser} -c "/bin/chown `id -u {aUser}`:`id -g {aUser}` {_home_dir}/.ssh/id_{_keyType}*"'
                node_exec_cmd_check(_node, _cmd)

                _i, _o, _e = _node.mExecuteCmd(f'/bin/su - {aUser} -c "/bin/cat {_home_dir}/.ssh/id_{_keyType}.pub"')
                _keyContent = _o.readlines()[0].strip()
                _node.mExecuteCmd(f'/bin/su - {aUser} -c "/bin/echo {_keyContent}  >> {_home_dir}/.ssh/authorized_keys"')
                node_exec_cmd_check(_node, f'/bin/su - {aUser} -c "/bin/chmod 600 {_home_dir}/.ssh/authorized_keys"')
                node_exec_cmd_check(_node, f'/bin/su - {aUser} -c "/bin/chown `id -u {aUser}`:`id -g {aUser}` {_home_dir}/.ssh/authorized_keys"')

                #Add self fingerprints
                node_exec_cmd(_node, f'/bin/su - {aUser} -c "/bin/ssh-keygen -R localhost"')
                node_exec_cmd(_node, f'/bin/su - {aUser} -c "/bin/ssh-keygen -R {_actualDomU}"')
                node_exec_cmd(_node, f'/bin/su - {aUser} -c "/bin/ssh-keygen -R {_actualDomU.split(".")[0]}"')
                node_exec_cmd_check(_node, f'/bin/su - {aUser} -c "/bin/ssh-keyscan -H localhost >> {_home_dir}/.ssh/known_hosts"')
                node_exec_cmd_check(_node, f'/bin/su - {aUser} -c "/bin/ssh-keyscan -H {_actualDomU} >> {_home_dir}/.ssh/known_hosts"')
                node_exec_cmd_check(_node, f'/bin/su - {aUser} -c "/bin/ssh-keyscan -H {_actualDomU.split(".")[0]} >> {_home_dir}/.ssh/known_hosts"')

                #Inject the key to the rest of the DomUs
                for _rest in _domUs:
                    if _rest == _actualDomU:
                        continue

                    ebLogInfo(f'Share key with {_rest}')

                    try:
                        _restnode = exaBoxNode(get_gcontext())
                        _restnode.mSetUser('root')
                        _restnode.mConnect(aHost=_rest)
                        node_exec_cmd(_restnode, f'/bin/su - {aUser} -c "/bin/mkdir -p {_home_dir}/.ssh"')
                        node_exec_cmd(_restnode, f'/bin/su - {aUser} -c "/bin/chmod 700 {_home_dir}/.ssh"')
                        _restnode.mExecuteCmd(f'/bin/su - {aUser} -c "/bin/echo {_keyContent}  >> {_home_dir}/.ssh/authorized_keys"')
                        node_exec_cmd_check(_restnode, f'/bin/su - {aUser} -c "/bin/chmod 600 {_home_dir}/.ssh/authorized_keys"')
                        node_exec_cmd_check(_restnode, f'/bin/su - {aUser} -c "/bin/chown `id -u {aUser}`:`id -g {aUser}` {_home_dir}/.ssh/authorized_keys"')
                    except Exception as exp:
                        _msg = f'::mConfigurePasswordLessDomU failed for user {aUser} on {_actualDomU}: {exp}'
                        ebLogError(_msg)
                        raise ExacloudRuntimeError(aErrorMsg=_msg) from exp
                    finally:
                        _restnode.mDisconnect()

                    #Add the access to the rest of the hosts
                    node_exec_cmd_check(_node, f'/bin/su - {aUser} -c "/bin/ssh-keygen -R {_rest}"')
                    node_exec_cmd_check(_node, f'/bin/su - {aUser} -c "/bin/ssh-keygen -R {_rest.split(".")[0]}"')
                    node_exec_cmd_check(_node, f'/bin/su - {aUser} -c "/bin/ssh-keyscan -T 30 -H {_rest} >> {_home_dir}/.ssh/known_hosts"')
                    node_exec_cmd_check(_node, f'/bin/su - {aUser} -c "/bin/ssh-keyscan -T 30 -H {_rest.split(".")[0]} >> {_home_dir}/.ssh/known_hosts"')

            except Exception as exp:
                _msg = f'::mConfigurePasswordLessDomU failed for user {aUser} on {_actualDomU}: {exp}'
                ebLogError(_msg)
                raise ExacloudRuntimeError(aErrorMsg=_msg) from exp
            finally:
                _node.mDisconnect()

    def mFetchNetworkInfo(self, aDom0, aDomU, aDom0Bonding):
        """Convert vmbackup restore node payload to common node payload.

        See module documentation for a description of the payload.

        :param node_payload: vmbackup restore node payload.
        :param bonding_operation: Specifies bonding operation
        :returns: create-service node payload.
        :raises Exception: if payload is invalid or malformed.
        """
        _dom0 = aDom0
        _domU = aDomU
        _dom0_bonding = aDom0Bonding
        _ebox = self.__cluctrl
        new_payload = { "client": {}, "backup": {}, "vip": {}}
        new_payload["fqdn"] = _dom0
        new_payload["bonding_operation"] = "vmbackup-restore"
        new_payload["dom0_bonding"] = _dom0_bonding
        _nw_utils = NetworkUtils()

        _domu_conf = _ebox.mGetMachines().mGetMachineConfig(_domU)
        _domu_conf_net = _domu_conf.mGetMacNetworks()
        _cluster   = _ebox.mGetClusters().mGetCluster()
        _vip_list  = _cluster.mGetCluVips()
        _vip_ips  = []
        for _vip in list(_vip_list.keys()):
            _vip_name = _vip_list[_vip].mGetCVIPMachines()[0]
            _vip_domain = _vip_list[_vip].mGetCVIPDomainName()
            _ip = _vip_list[_vip].mGetCVIPAddr()
            _mac_config = _ebox.mGetMachines().mGetMachineConfig(_vip_name)
            _mac_name   = _mac_config.mGetMacHostName()
            if _mac_name == _domU:
                _vip_name = _vip_list[_vip].mGetCVIPName()
                new_payload["vip"]["fqdn"] = _vip_name + _vip_domain
                if not _nw_utils.mIsIPv6(_ip):
                    new_payload["vip"]["ip"] = _ip
                elif _nw_utils.mIsIPv6(_ip):
                    new_payload["vip"]["ipv6"] = _ip
        # Single stack support
        if "ip" not in new_payload["vip"] and "ipv6" in new_payload["vip"]:
            new_payload["vip"]["ip"] = new_payload["vip"]["ipv6"]
            del new_payload["vip"]["ipv6"]

        for _net_id in _domu_conf_net:
            _net_conf = _ebox.mGetNetworks().mGetNetworkConfig(_net_id)
            _fqdn = _net_conf.mGetNetHostName() + _net_conf.mGetNetDomainName()
            _gateway = _net_conf.mGetNetGateWay()
            _mac = _net_conf.mGetNetMacAddr()
            _mask = _net_conf.mGetNetMask()
            _slaves = _net_conf.mGetNetSlave()
            _vlantag = _net_conf.mGetNetVlanId()
            _ip = _net_conf.mGetNetIpAddr()

            if _net_conf.mGetNetType() == "client":
                _nat_dn = _net_conf.mGetNetNatDomainName()
                _nat_ip = _net_conf.mGetNetNatAddr()
                _nat_mask = _net_conf.mGetNetNatMask()
                _nat_hn = _net_conf.mGetNetNatHostName()

                new_payload["client"]["fqdn"] = _fqdn
                new_payload["client"]["mac"] = _mac
                new_payload["client"]["natdomain"] = _nat_dn
                new_payload["client"]["natip"] = _nat_ip
                new_payload["client"]["natnetmask"] = _nat_mask
                new_payload["client"]["slaves"] = _slaves
                new_payload["client"]["vlantag"] = _vlantag
                new_payload["client"]["domu_oracle_name"] = _nat_hn
                if not _nw_utils.mIsIPv6(_ip):
                    new_payload["client"]["ip"] = _ip
                    new_payload["client"]["gateway"] = _gateway
                    new_payload["client"]["netmask"] = _mask
                elif _nw_utils.mIsIPv6(_ip):
                    new_payload["client"]["v6gateway"] = _gateway
                    new_payload["client"]["v6netmask"] = _mask
                    new_payload["client"]["ipv6"] = _ip
            elif _net_conf.mGetNetType() == "backup":
                new_payload["backup"]["fqdn"] = _fqdn
                new_payload["backup"]["mac"] = _mac
                new_payload["backup"]["slaves"] = _slaves
                new_payload["backup"]["vlantag"] = _vlantag
                if not _nw_utils.mIsIPv6(_ip):
                    new_payload["backup"]["ip"] = _ip
                    new_payload["backup"]["gateway"] = _gateway
                    new_payload["backup"]["netmask"] = _mask
                elif _nw_utils.mIsIPv6(_ip):
                    new_payload["backup"]["v6gateway"] = _gateway
                    new_payload["backup"]["v6netmask"] = _mask
                    new_payload["backup"]["ipv6"] = _ip
        _network_types = ["client", "backup"]
        _ipv6_fields = ["v6gateway", "v6netmask", "ipv6"]
        # Single stack ipv6 support
        for _network in _network_types:
            for _field in _ipv6_fields:
                if _network in new_payload:
                    if _field in new_payload[_network] and _field.replace("v6", "") not in new_payload[_network]:
                        new_payload[_network][_field.replace("v6", "")] = new_payload[_network][_field]
                        del new_payload[_network][_field]
        return new_payload

    def mExecutePreVMStep(self, aDom0, aDomU, aPayload):
        _dom0 = aDom0
        _domU = aDomU
        _payload = aPayload
        _ebox = self.__cluctrl
        _options = self.__options

        _ebox.mAcquireRemoteLock()

        # Bonded-bridge configuration might cause OEDA CREATE_VM to
        # fail, thus cleanup bonding first.  Bonding will be configured
        # later after the VMs are created.
        #
        # This operation is only required if static bonded-bridge creation is
        # not supported in the cluster.
        # In case static bonded-bridges are supported for this cluster, we'll
        # try to make sure the bridges are configured as dynamic to avoid
        # cleanup during provisioning.
        clubonding.migrate_static_bridges(_ebox, _payload)
        if not clubonding.is_static_monitoring_bridge_supported(
                _ebox, payload=_payload):
            clubonding.cleanup_bonding_if_enabled(
                _ebox, payload=_payload, cleanup_bridge=True,
                cleanup_monitor=False)

        #
        # Update bonding configuration only if static bridges are supported.
        #
        if clubonding.is_static_monitoring_bridge_supported(
                _ebox, payload=_payload):
            clubonding.update_bonded_bridges(_ebox, payload=_payload)

        _ebox.mReleaseRemoteLock()

    def mExecutePostVMStep(self, aDom0, aDomU, aPayload):
        _dom0 = aDom0
        _domU = aDomU
        _payload = aPayload
        _ebox = self.__cluctrl
        _options = self.__options

        # Configure bonding.
        #
        # Configure bridge only if static monitoring bridge is not supported.
        conf_bridge = \
            not clubonding.is_static_monitoring_bridge_supported(
                    _ebox, payload=_payload)
        clubonding.configure_bonding_if_enabled(
            _ebox, payload=_payload,
            configure_bridge=conf_bridge, configure_monitor=True)

    def mUpdateLibvirtXML(self, aDom0, aDomU):
        _dom0 = aDom0
        _domU = aDomU

        try:
            _old_mac = ""
            _new_mac = ""
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_dom0)

            _guest_dir = f"/EXAVMIMAGES/GuestImages/{_domU}"

            _hv = getHVInstance(_dom0)
            _new_uuid = _hv.mGetVMUUID(_domU)
            _admin_bridge, _new_mac = _hv.mGetVMAdminBridge(_domU)

            _libvirt_xml = f"/etc/libvirt/qemu/{_domU}.xml"
            _restored_xml = f"{_guest_dir}/{_domU}.xml.libvirt.qemu"
            _restored_backup_xml = f"{_restored_xml}.backup"
            _cmd = f"/bin/cp -p {_restored_xml} {_restored_backup_xml}"
            _node.mExecuteCmdLog(_cmd)

            _admin_bridge_xml = f"{_guest_dir}/{_admin_bridge}.xml"
            _admin_backup_xml = f"{_admin_bridge_xml}.backup"
            _cmd = f"/bin/cp -p {_admin_bridge_xml} {_admin_backup_xml}"
            _node.mExecuteCmdLog(_cmd)

            _cmd = """/bin/cat %s | /bin/grep 'mac address=' | /bin/awk -F "[=/]" '{print $2}' """ %(_admin_bridge_xml)
            _i, _o, _e = _node.mExecuteCmd(_cmd)
            if _node.mGetCmdExitStatus() != 0:
                _msg = f'*** mac address is missing from {_admin_bridge_xml}'
                _node.mDisconnect()
                ebLogError(_msg)
                raise ExacloudRuntimeError(aErrorMsg=_msg)
            _old_mac = literal_eval(_o.readlines()[0].strip())

            _cmd = f"/bin/sed -i 's|{_old_mac}|{_new_mac}|g' {_admin_bridge_xml}"
            _node.mExecuteCmdLog(_cmd)

            _cmd = f"/bin/cp -p {_libvirt_xml} {_restored_xml}"
            _node.mExecuteCmdLog(_cmd)

        except Exception as e:
            _msg = f'Failed to updated libvirt XML from VMBackup XML'
            ebLogError(_msg)

        finally:
            _node.mDisconnect()

    def mGetRoceInterfaces(self, aNode, aVMXML):
        _node = aNode
        _interface_xml = aVMXML
        _roce_intf = {}

        # Fetch the mac address & PCI address from libvirt XML
        # Virtual functions do not have the udev_address as the PCI address.
        # Instead, the bus is 0xff.
        #<interface type='network'>
        #    <mac address='52:54:00:3b:a6:27'/>
        #    <source network='re1_vf_pool'/>
        #    <address type='pci' domain='0x0000' bus='0x04' slot='0x00' function='0x1'/>
        #</interface>
        #_udev_address = "0000:ff:00." + _intf.find("address").get("function")[2:]

        _vm_xml = _node.mReadFile(_interface_xml)
        _root = ET.fromstring(_vm_xml)
        for _intf in _root.findall("./devices/interface/[@type='network']"):
            _mac = _intf.find('mac').attrib['address']
            _udev_address = "0000:ff:00." + _intf.find("address").get("function")[2:]
            _roce_intf[_mac] = _udev_address
        return _roce_intf

    def mGetVFConfig(self, aNode, aQinqXML, aRoceList):
        _node = aNode
        _roce_intf = aRoceList
        _interface = ""
        _udev_address = ""
        _interconnect_vifs = {}

        #Map mac address from libvirt XML with qinq.xml & fetch the interface & PCI address
        _qinqXml = _node.mReadFile(aQinqXML)
        _root = ET.fromstring(_qinqXml)
        for _iter in _root.findall('interface'):
            _mac_address = _iter.find('mac').text
            _interface = _iter.find('guest_interface').text
            if _mac_address in list(_roce_intf.keys()):
                _udev_address = _roce_intf[_mac_address]
                ebLogInfo(f"UDEV ADDRESS:{_udev_address}, MAC:{_mac_address} INTERFACE:{_interface}")
                _interconnect_vifs[_interface] = _udev_address
        return _interconnect_vifs

    def mGetInterConnectVifs(self, aDom0, aDomU):
        _dom0 = aDom0
        _domU = aDomU
        _interconnect_vifs = {}

        _qinq = f"/EXAVMIMAGES/GuestImages/{_domU}/qinq.xml"
        _interface_xml = f"/etc/libvirt/qemu/{_domU}.xml"
        try:
            with connect_to_host(_dom0, get_gcontext(), username="root") as _node:
                _roce_intf = self.mGetRoceInterfaces(_node, _interface_xml)
                _interconnect_vifs = self.mGetVFConfig(_node, _qinq, _roce_intf)
        except Exception as e:
            _error_str = f"*** Failed to fetch interconnect vifs for VM:{_domU} on dom0:{_dom0}"
            ebLogError(_error_str)

        return _interconnect_vifs

    def mUpdatePersistentRules(self, aDomU, aVFDict):
        _domU = aDomU
        _interconnect_vifs = aVFDict

        try:
            with connect_to_host(_domU, get_gcontext(), username="root") as _node:
                _file = "/etc/udev/rules.d/70-persistent-net.rules"
                _file_bk = "/etc/udev/rules.d/70-persistent-net.rules_bk"

                if not _node.mFileExists(_file_bk):
                    _node.mExecuteCmdLog(f"/bin/cp -p {_file} {_file_bk}")
                    _node.mExecuteCmdLog(f"/bin/sed -i '/clre0/d' {_file_bk}")
                    _node.mExecuteCmdLog(f"/bin/sed -i '/clre1/d' {_file_bk}")
                    _node.mExecuteCmdLog(f"/bin/sed -i '/stre0/d' {_file_bk}")
                    _node.mExecuteCmdLog(f"/bin/sed -i '/stre1/d' {_file_bk}")

                ebLogInfo(f"Updating file {_file} in domU {_domU}")
                for _intf, _kernel in _interconnect_vifs.items():
                    _cmd_str = f"/bin/grep PCI_SLOT_NAME /sys/class/net/{_intf}/device/uevent"
                    _i, _o, _e = _node.mExecuteCmd(_cmd_str)
                    _output = _o.readlines()
                    if not _output:
                        _error_str = f"*** Failed to get PCI_SLOT_NAME for {_intf} for VM:{_domU}"
                        ebLogError(_error_str)
                        return
                    _pci_slot_name = _output[0].strip().split('=')[1]
                    ebLogInfo(f"PCI SLOT NAME for {_intf}:{_pci_slot_name}")
                    _old_value = f"{_pci_slot_name}"
                    _new_value =  f"{_kernel}"
                    if _node.mFileExists(_file):
                        _cmd = f"/bin/grep {_intf} {_file}"
                        _i, _o, _e = _node.mExecuteCmd(_cmd)
                        _output = _o.read()
                        if not _output:
                            _error_str = f"*** Failed to get VIF addreses for {_intf} for VM:{_domU}"
                            ebLogError(_error_str)
                            return
                        _output = _output.strip()
                        _sed_cmd = f"/bin/sed 's|{_old_value}|{_new_value}|g'"
                        _cmd = """/bin/echo '{0}' | {1}""".format(_output, _sed_cmd)
                        _i, _o, _e = _node.mExecuteCmd(_cmd)
                        _output = _o.read()
                        _node.mWriteFile(_file_bk, _output, aAppend=True)
                _node.mExecuteCmdLog(f"/bin/mv {_file_bk} {_file}")
        except Exception as e:
            _error_str = f"*** Failed to Update interconnect vifs for VM:{_domU}"
            ebLogError(_error_str)

    def mFetchAdminNWDetails(self, aDom0, aDomU):
        _dom0 = aDom0
        _domU = aDomU

        try:
            with connect_to_host(_domU, get_gcontext(), username="root") as _node:
                _cmd_str = "/bin/grep '^IPADDR' /etc/sysconfig/network-scripts/ifcfg-eth0"
                _i, _o, _e = _node.mExecuteCmd(_cmd_str)
                _output = _o.readlines()
                if not _output or len(_output) == 0:
                    _node.mDisconnect()
                    ebLogError(f'*** DomU:{_domU}:: IPADDR not configured in ifcfg-eth0')
                    raise ExacloudRuntimeError(0x0109, 0xA, 'IPADDR not configured in ifcfg-eth0')

                _ip = self.__adminNetwork["IPADDR"] = _output[0].strip().split('=')[1].strip()
                ebLogTrace(f"IPADDR:{_ip} for eth0 on domU:{_domU}")

                _cmd_str = "/bin/grep '^NETMASK' /etc/sysconfig/network-scripts/ifcfg-eth0"
                _i, _o, _e = _node.mExecuteCmd(_cmd_str)
                _output = _o.readlines()
                if not _output or len(_output) == 0:
                    _node.mDisconnect()
                    ebLogError(f'*** DomU:{_domU}:: NETMASK not configured in ifcfg-eth0')
                    raise ExacloudRuntimeError(0x0109, 0xA, 'NETMASK not configured in ifcfg-eth0')

                _netmask = self.__adminNetwork["NETMASK"] = _output[0].strip().split('=')[1].strip()
                ebLogTrace(f"NETMASK:{_netmask} for eth0 on domU:{_domU}")

                _cmd_str = "/bin/grep '^GATEWAY' /etc/sysconfig/network-scripts/ifcfg-eth0"
                _i, _o, _e = _node.mExecuteCmd(_cmd_str)
                _output = _o.readlines()
                if not _output or len(_output) == 0:
                    _gateway = self.__adminNetwork["GATEWAY"] = ""
                    ebLogWarn(f'*** DomU:{_domU}:: Gateway not configured in ifcfg-eth0')
                else:
                    _gateway = self.__adminNetwork["GATEWAY"] = _output[0].strip().split('=')[1].strip()
                    ebLogTrace(f"GATEWAY:{_gateway} for eth0 on domU:{_domU}")

                _cmd_str = "/bin/grep '^NETWORK' /etc/sysconfig/network-scripts/ifcfg-eth0"
                _i, _o, _e = _node.mExecuteCmd(_cmd_str)
                _output = _o.readlines()
                if not _output or len(_output) == 0:
                    _node.mDisconnect()
                    ebLogError(f'*** DomU:{_domU}:: NETWORK not configured in ifcfg-eth0')
                    raise ExacloudRuntimeError(0x0109, 0xA, 'NETWORK not configured in ifcfg-eth0')

                _network = self.__adminNetwork["NETWORK"] = _output[0].strip().split('=')[1].strip()
                ebLogTrace(f"NETWORK:{_network} for eth0 on domU:{_domU}")

                _cmd_str = "/bin/grep '^BROADCAST' /etc/sysconfig/network-scripts/ifcfg-eth0"
                _i, _o, _e = _node.mExecuteCmd(_cmd_str)
                _output = _o.readlines()
                if not _output or len(_output) == 0:
                    _node.mDisconnect()
                    ebLogError(f'*** DomU:{_domU}:: BROADCAST not configured in ifcfg-eth0')
                    raise ExacloudRuntimeError(0x0109, 0xA, 'BROADCAST not configured in ifcfg-eth0')

                _broadcast = self.__adminNetwork["BROADCAST"] = _output[0].strip().split('=')[1].strip()
                ebLogTrace(f"BROADCAST:{_broadcast} for eth0 on domU:{_domU}")
        except Exception as e:
            _error_str = f"*** Failed to get admin network for VM:{_domU}"
            ebLogError(_error_str)

    def mPatchCellConfig(self, aNode, aIP, aNetMask, aGateway, aMaster, aCellConfig):
        _node = aNode
        _ip = aIP
        _netmask = aNetMask
        _gateway = aGateway
        _master = aMaster
        _cellConf = aCellConfig

        _conf = _node.mReadFile(_cellConf)
        _root = ET.fromstring(_conf)
        _intf = _root.find("./Interfaces/[Name='{}']".format(_master))
        _intf.find("IP_address").text = _ip
        _intf.find("Netmask").text = _netmask
        _intf.find("Gateway").text = _gateway

        _conf = ET.tostring(_root)
        _conf = "<?xml version='1.0' standalone='yes'?>\n".encode("utf-8") + _conf
        return _conf

    def mUpdateNetworkConfig(self, aDom0, aDomU, aMountPoint, aUser="root"):
        _dom0 = aDom0
        _domU = aDomU
        _mount_point = aMountPoint
        _user = aUser

        if _user == "root":
            _file_path  = "opt/oracle.cellos/cell.conf"
            _now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            _file_path_bk  = f"opt/oracle.cellos/cell.conf.bak.{_now}"
            _ifcfg = "etc/sysconfig/network-scripts/ifcfg-eth0"
            _route = "etc/sysconfig/network-scripts/route-eth0"
            _rule = "etc/sysconfig/network-scripts/rule-eth0"
            _hosts = "etc/hosts"
            _ssh_config = "etc/ssh/sshd_config"

        _cell_conf = os.path.join(_mount_point, _file_path)
        _cell_conf_bk = os.path.join(_mount_point, _file_path_bk)
        _ifcfg_path = os.path.join(_mount_point, _ifcfg)
        _route_path = os.path.join(_mount_point, _route)
        _rule_path = os.path.join(_mount_point, _rule)
        _hosts_path = os.path.join(_mount_point, _hosts)
        _sshconfig_path = os.path.join(_mount_point, _ssh_config)

        try:
            ebLogTrace(f"Updating Network Configuration on domU:{_domU}")
            with connect_to_host(_dom0, get_gcontext(), username="root") as _node:
                _node.mExecuteCmdLog(f"/bin/cp -p {_cell_conf} {_cell_conf_bk}")

                _ip = self.mGetAdminIpAddr()
                _netmask = self.mGetAdminNetMask()
                _gateway = self.mGetAdminGateway()
                _network = self.mGetAdminNetwork()
                _broadcast = self.mGetAdminBroadcast()

                #Update admin ipaddress to ListenAddress in /etc/ssh/sshd_config
                if _node.mFileExists(_sshconfig_path):
                    _cmd_str = f"/bin/grep 169.254.200* {_sshconfig_path}"
                    _i, _o, _e = _node.mExecuteCmd(_cmd_str)
                    _output = _o.readlines()
                    if not _output or len(_output) == 0:
                        _node.mDisconnect()
                        ebLogError(f'*** DomU:{_domU}:: LISTEN ADDRESS not configured in /etc/ssh/sshd_config')
                        raise ExacloudRuntimeError(0x0109, 0xA, 'LISTEN ADDRESS not configured in /etc/ssh/sshd_config')

                    _old_value = _output[0].split()[1].strip()
                    _new_value = _ip
                    _sed_cmd = f"/bin/sed 's|{_old_value}|{_new_value}|g' -i {_sshconfig_path}"
                    _node.mExecuteCmdLog(_sed_cmd)

                #Update domU NAT address in /opt/oracle.cellos/cell.conf
                _newCellConf = self.mPatchCellConfig(_node, _ip, _netmask, _gateway, "eth0", _cell_conf)
                _node.mWriteFile(_cell_conf, _newCellConf, aAppend=False)

                #Update domU admin address in ifcfg-eth0
                if _node.mFileExists(_ifcfg_path):
                    node_update_key_val_file(_node, _ifcfg_path, {'IPADDR': _ip})
                    node_update_key_val_file(_node, _ifcfg_path, {'NETMASK': _netmask})
                    node_update_key_val_file(_node, _ifcfg_path, {'GATEWAY': _gateway})
                    node_update_key_val_file(_node, _ifcfg_path, {'NETWORK': _network})
                    node_update_key_val_file(_node, _ifcfg_path, {'BROADCAST': _broadcast})

                #Update admin route rule(route-eth0)
                if _node.mFileExists(_route_path):
                    _cmd_str = f"/bin/head -1 {_route_path}"
                    _i, _o, _e = _node.mExecuteCmd(_cmd_str)
                    _output = _o.readlines()
                    if not _output or len(_output) == 0:
                        _node.mDisconnect()
                        ebLogError(f'*** DomU:{_domU}:: route not configured in /etc/sysconfig/network-scripts/route-eth0')
                        raise ExacloudRuntimeError(0x0109, 0xA, 'route not configured in /etc/sysconfig/network-scripts/route-eth0')

                    _old_value = _output[0].split()[0].strip()[:-3]
                    _new_value = _network
                    _sed_cmd = f"/bin/sed 's|{_old_value}|{_new_value}|g' -i {_route_path}"
                    _node.mExecuteCmdLog(_sed_cmd)

                    _cmd_str = f"/bin/tail -1 {_route_path}"
                    _i, _o, _e = _node.mExecuteCmd(_cmd_str)
                    _output = _o.readlines()
                    if not _output or len(_output) == 0:
                        _node.mDisconnect()
                        ebLogError(f'*** DomU:{_domU}:: route not configured  in /etc/sysconfig/network-scripts/route-eth0')
                        raise ExacloudRuntimeError(0x0109, 0xA, 'route not configured in /etc/sysconfig/network-scripts/route-eth0')

                    if _gateway:
                        _old_value = _output[0].split()[2].strip()
                        _new_value = _gateway
                        _sed_cmd = f"/bin/sed 's|{_old_value}|{_new_value}|g' -i {_route_path}"
                        _node.mExecuteCmdLog(_sed_cmd)

                #Update admin rule(rule-eth0)
                if _node.mFileExists(_rule_path):
                    _cmd_str = f"/bin/head -1 {_rule_path}"
                    _i, _o, _e = _node.mExecuteCmd(_cmd_str)
                    _output = _o.readlines()
                    if not _output or len(_output) == 0:
                        _node.mDisconnect()
                        ebLogError(f'*** DomU:{_domU}:: route not configured in /etc/sysconfig/network-scripts/rule-eth0')
                        raise ExacloudRuntimeError(0x0109, 0xA, 'route not configured in /etc/sysconfig/network-scripts/rule-eth0')

                    _old_value = _output[0].split()[1].strip()[:-3]
                    _new_value = _network
                    _sed_cmd = f"/bin/sed 's|{_old_value}|{_new_value}|g' -i {_rule_path}"
                    _node.mExecuteCmdLog(_sed_cmd)

                #Update GATEWAY IP/NAT-IP in /etc/hosts
                if _node.mFileExists(_hosts_path):
                    _ctx = get_gcontext()
                    _cps = _domU.split('.')[0] + "cps"
                    _localdomain = _domU.split('.')[0] + ".localdomain"
                    _nat_host = ""
                    if _ctx.mCheckRegEntry('_natHN_' + _domU):
                        _nat_fqdn = _ctx.mGetRegEntry('_natHN_' + _domU)
                        _nat_host = _nat_fqdn.split('.')[0]
                        _cps = _nat_host + "cps"
                        _localdomain = _nat_host + ".localdomain"

                    _cmd_str = f"/bin/grep -E '{_cps}|{_localdomain}' {_hosts_path}"
                    _i, _o, _e = _node.mExecuteCmd(_cmd_str)
                    _output = _o.readlines()
                    if not _output or len(_output) == 0:
                        _node.mDisconnect()
                        ebLogError(f'*** DomU:{_domU}:: GATEWAY IP not configured in /etc/hosts')
                        raise ExacloudRuntimeError(0x0109, 0xA, 'GATEWAY IP not configured in /etc/hosts')

                    if _gateway:
                        _old_value = _output[0].split()[0].strip()
                        _new_value = _gateway
                        _sed_cmd = f"/bin/sed 's|{_old_value}|{_new_value}|g' -i {_hosts_path}"
                        _node.mExecuteCmdLog(_sed_cmd)

                    _cmd_str = f"/bin/grep {_nat_host} {_hosts_path}"
                    _i, _o, _e = _node.mExecuteCmd(_cmd_str)
                    _output = _o.readlines()
                    if not _output or len(_output) == 0:
                        _node.mDisconnect()
                        ebLogError(f'*** DomU:{_domU}:: NAT-IP not configured in /etc/hosts')
                        raise ExacloudRuntimeError(0x0109, 0xA, 'NAT-IP not configured in /etc/hosts')

                    _old_value = _output[0].split()[0].strip()
                    _new_value = _ip
                    _sed_cmd = f"/bin/sed 's|{_old_value}|{_new_value}|g' -i {_hosts_path}"
                    _node.mExecuteCmdLog(_sed_cmd)
        except Exception as e:
            _error_str = f"*** Failed to Update admin ip in network configuration files for VM:{_domU}"
            ebLogError(_error_str)

    def mAttachU02Disk(self, aDom0, aDomU):
        _dom0 = aDom0
        _domU = aDomU
        _ddpair = [[_dom0, _domU]]
        _ebox = self.__cluctrl
        _options = self.__options

        _gridhome, _, _ora_base = _ebox.mGetOracleBaseDirectories(aDomU = _domU)

        _ebox.mAcquireRemoteLock()
        _step_time = time.time()
        _ebox.mPatchVMCfg(_options, _gridhome, aDom0DomUPair=_ddpair)             # Customize VM.CFG (e.g. additional images, partitions,...)
        _ebox.mLogStepElapsedTime(_step_time, 'Patching VM Configuration')
        _ebox.mReleaseRemoteLock()

    def mRestoreVM(self, aDom0, aDomU):
        _dom0 = aDom0
        _domU = aDomU
        _ebox = self.__cluctrl
        try:
            _ebox = self.__cluctrl
            _options = self.__options
            self.mSetSrcDom0DomU(aNewDom0=_dom0, aNewDomU=_domU)
            _srcdomU = self.mGetSrcDomU()

            _dpairs = [[_dom0, _domU]]
            _domU_list = [ _domu for _ , _domu in _dpairs]

            #Enable ssh connectivity for root/opc
            self.mEnableSSHConnectivity(_dom0, _domU)
            self.mStartVM(_dom0, _domU)
            self.mRestoreRootAccessForRestoredNode(_domU)
            if _ebox.mIsKVM():
                #Update /etc/udev/rules.d/70-persistent-net.rules with new interconnect address
                _interconnect_vifs = self.mGetInterConnectVifs(_dom0, _domU)
                if _interconnect_vifs:
                    self.mUpdatePersistentRules(_domU, _interconnect_vifs)
            self.mUpdateSecurityRules(_dom0, _domU)
            self.mUpdateArpCheckFlag(_dom0, _domU)
            self.mAttachU02Disk(_dom0, _domU)
            #Waiting for CRS/ASM to be up & running
            _ebox.mCheckCrsIsUp(_domU, _domU_list, aNodeRecovery=True)
            _ebox.mCheckAsmIsUp(_domU, _domU_list)
            self.mPinNode(_domU)
            self.mAddVIP(_domU)
            self.mCreateQuorumDevices(_domU)
            self.mInstallRpm(_dom0, _domU)
            self.mStartServices(_dom0, _domU)
            #self.mUpdateLibvirtXML(_dom0, _domU)

            _db_info = ""
            _new_dblist = []
            _json = _options.jsonconf
            _jconf_keys = list(_json.keys())
            if _jconf_keys is not None and 'db_info' in _jconf_keys and _json['db_info']:
               for _dbName in _json['db_info']:
                  _db_unique, _location = self.mGetDBUniqueName(_srcdomU, _dbName)
                  _is_running = self.mCheckDBInstanceIsUp(_domU, _db_unique, _location, _options, aRaiseError=False)
                  if _is_running:
                      self.mAddOratab(_domU, _db_unique, _location)
                  else:
                      _new_dblist.append(_dbName)
               if _new_dblist:
                   _db_info = ",".join(_dbinfo for _dbinfo in _new_dblist)
            if _db_info:
                _ebox.mStoreDomUInterconnectIps()
                _data = self.mAddDBHomes(_options, _srcdomU, _domU, _db_info)
        except Exception as e:
            _error_str = f"*** Failed to recover VM:{_domU} on dom0:{_dom0}"
            ebLogError(_error_str)
            self.mDeleteVM(_dom0, _domU, aNodeRecovery=True)
            raise

    def mPostRestoreValidation(self, aDom0, aDomU):
        _dom0 = aDom0
        _domU = aDomU
        _ebox = self.__cluctrl
        _options = self.__options

        try:
            self.mSetSrcDom0DomU(aNewDom0=_dom0, aNewDomU=_domU)
            _srcdomU = self.mGetSrcDomU()

            _domU_list = []
            _domU_list.append(_domU)

            _exadata_model =  _ebox.mGetExadataCellModel()
            _exadata_model_gt_X7 = False
            _compare_exadata = _ebox.mCompareExadataModel(_exadata_model, 'X7')
            if _compare_exadata >= 0:
                _exadata_model_gt_X7 = True

            # Checking cluster integrity
            self.mConfigurePasswordlessAllUsers()
            _pchecks = ebCluPreChecks(_ebox)
            _pchecks.mCheckClusterIntegrity(True, False, _domU_list)
            _gridhome, _, _ = _ebox.mGetOracleBaseDirectories(aDomU = _domU)
            self.mAddCheckClusterAsm(_options, _domU, _gridhome)
        except Exception as e:
            ebLogWarn('Exception in handling request[%s]' % (e,))
            ebLogError(traceback.format_exc())
            ebLogError("*** Error in running Post Reshape Validation")

        ebLogInfo('*** Exacloud Operation Successful : Post Restore Operation Completed')

    def mParseXMLForNodeRecovery(self, aDom0, aXmlFilePath):
        """  
        Reads an XML file from the given path and returns a list of values  
        found within all <domuVolume> tags.  

        Args:  
            aXmlFilePath (str): The path to the XML file.  

        Returns:  
            list: A list of strings, where each string is the text content  
                of a <domuVolume> element. Returns an empty list if the  
                file is not found, cannot be parsed, or no <domuVolume>  
                tags are found.  
        """
        ebLogTrace(f'Parsing XML : {aXmlFilePath}')
        _dom0 = aDom0
        _domu_xml_path = aXmlFilePath
        _vm_xml = None

        try:
            with connect_to_host(_dom0, get_gcontext()) as _node:
                _vm_xml = _node.mReadFile(_domu_xml_path)
        except Exception as e:
            _msg = f"Error: Failed to connect or read file '{_domu_xml_path}' from '{_dom0}'. Details: {e}"
            ebLogError(_msg)
        
        extracted_files = []  
        target_prefix = "/EXAVMIMAGES/"  

        try:  
            # Parse the XML string  
            _root = ET.fromstring(_vm_xml)

            # Find all 'domuVolume' elements under 'disk' elements
            #  XPath './/disk/domuVolume' is more specific to the structure shown
            for volume_element in _root.findall('.//disk/domuVolume'):
                volume_text = volume_element.text
                # Check if the text matches the criteria
                if (volume_text and
                        volume_text.startswith(target_prefix) and  
                        (volume_text.endswith('.img') or volume_text.endswith('.zip'))):
                    # Extract the filename using os.path.basename
                    filename = os.path.basename(volume_text)
                    if filename:
                        ebLogTrace(f'XML Parsing : {filename}')
                        extracted_files.append(filename)
                        
            return extracted_files
        
        except ET.ParseError as parse_err:
            ebLogError(f"Error: Could not parse XML file '{_domu_xml_path}' from '{_dom0}'. Details: {parse_err}")
        except Exception as e:  
            ebLogError(f"An unexpected error occurred during XML processing for '{_domu_xml_path}' from '{_dom0}'. Details: {e}")
  
    def mUpdateXMLTagValue(self, aDom0, aXmlFilePath, aNewImagePath):
        """
        Reads an XML file, selectively updates specific <domuVolume> tags under
        <disk> tags based on image type matching, and writes the modified XML
        back to the file.

        - Operates only on <domuVolume> tags whose value starts with '/EXAVMIMAGES/'.
        - Determines the 'type' of the aNewImagePath (System Boot or Grid Klone)
          based on its filename.
        - Updates existing <domuVolume> tags only if they start with '/EXAVMIMAGES/'
        - Preserves the XML declaration header.

        Args:
            aDom0 (str): The hostname of the target node.
            aXmlFilePath (str): The path to the XML file on the target node.
            aNewImagePath (str): The full path of the new image file

        Returns:
            bool: True if the file was read, updated, and written
                  successfully ,False otherwise.
        """
        # Helper to extract version from an image filename
        def extract_version(image_filename):
            # expects something.boot.<version>[.rtg].img
            match = re.search(r'\.boot\.((?:\d+\.)*\d+)(?:\.rtg)?\.img$', image_filename)
            return match.group(1) if match else None
        
        _dom0 = aDom0
        _xml_path = aXmlFilePath
        _new_full_path = aNewImagePath

        _original_xml = None
        _modified_xml_string = None
        _updated = False # Flag to track if any changes were made

        # Input Validation and Type Detection
        if not _new_full_path or not _new_full_path.startswith(self.TARGET_DIR_PREFIX):
             ebLogError(f"Error: New image path ('{_new_full_path}') must be non-empty and start with '{self.TARGET_DIR_PREFIX}'.")  
             return False

        _new_basename = os.path.basename(_new_full_path)
        _input_image_type = None
        if _new_basename.startswith(self.SYSTEM_BOOT_PREFIX):
            _input_image_type = "SYSTEM"
        elif _new_basename.startswith(self.GRID_KLONE_PREFIX):
            _input_image_type = "GRID"
        else:
            ebLogError(f"Error: Could not determine image type (System/Grid) for input basename '{_new_basename}'. Update aborted.")
            return False
        ebLogTrace(f"Input image type detected as: {_input_image_type} for path '{_new_full_path}'")

        try:
            with connect_to_host(_dom0, get_gcontext()) as _node:
                # Read the original XML file content  
                try:
                    _original_xml = _node.mReadFile(_xml_path)
                    if not _original_xml:
                         ebLogError(f"Error: File '{_xml_path}' from '{_dom0}' is empty or could not be read.")
                         return False
                except Exception as e:
                    ebLogError(f"Error: Failed to read file '{_xml_path}' from '{_dom0}'. Details: {e}")
                    return False

                # Parse the XML  
                try:
                    _root = ET.fromstring(_original_xml)
                except ET.ParseError as parse_err:
                    ebLogError(f"Error: Could not parse XML from '{_xml_path}' on '{_dom0}'. Details: {parse_err}")
                    return False

                disk_elements = _root.findall('.//disk')

                if not disk_elements:
                    ebLogTrace(f"No <disk> elements found in '{_xml_path}' on '{_dom0}'. No update needed.")
                    return True

                for disk in disk_elements:
                    domu_volume_elem = disk.find('domuVolume')
                    domu_version_elem = disk.find('domuVersion')
                    if domu_volume_elem is None:
                        continue

                    current_text = domu_volume_elem.text

                    # CONDITION 1: Must exist and start with the target prefix  
                    if not current_text or not current_text.startswith(self.TARGET_DIR_PREFIX):
                        ebLogTrace(f"Skipping <domuVolume>: Value '{current_text}' does not start with prefix '{self.TARGET_DIR_PREFIX}'.")
                        continue

                    current_basename = os.path.basename(current_text)

                    # CONDITION 2: Type must match the input type
                    tag_matches_input_type = False
                    if _input_image_type == "SYSTEM" and current_basename.startswith(self.SYSTEM_BOOT_PREFIX):
                        tag_matches_input_type = True
                    elif _input_image_type == "GRID" and current_basename.startswith(self.GRID_KLONE_PREFIX):
                        tag_matches_input_type = True

                    if not tag_matches_input_type:
                        ebLogTrace(f"Skipping <domuVolume>: Type mismatch. Current base '{current_basename}' type does not match input type '{_input_image_type}'.")
                        continue

                    # CONDITION 3: Update only if the value is actually different  
                    if current_text != _new_full_path:
                        ebLogTrace(f"Updating <domuVolume> (Type: {_input_image_type}): '{current_text}' -> '{_new_full_path}'")
                        domu_volume_elem.text = _new_full_path
                        _updated = True # Mark that we made a change

                        # Additional Change: For SYSTEM type, also update <domUVersion> in the same <disk>
                        if _input_image_type == "SYSTEM" and domu_version_elem is not None:
                            version_str = extract_version(os.path.basename(_new_full_path))
                            if not version_str:
                                ebLogError(f"Failed to extract version from image filename '{os.path.basename(_new_full_path)}'")
                                continue
                            current_domu_version = domu_version_elem.text
                            if current_domu_version != version_str:
                                ebLogTrace(f"Updating <domUVersion> (Type: {_input_image_type}): '{current_domu_version}' -> '{version_str}'")
                                domu_version_elem.text = version_str
                                _updated = True
                            else:
                                ebLogTrace(f"Skipping <domUVersion>: Value '{current_domu_version}' already matches target.")
                                
                        elif _input_image_type == "SYSTEM" and domu_version_elem is None:
                            ebLogError(f"No <domUVersion> found in <disk> for <domuVolume> '{current_text}' in '{_xml_path}' on '{_dom0}'. Skipping <domUVersion> update.")
                    else:
                        ebLogTrace(f"Skipping update for <domuVolume>: Value '{current_text}' already matches target.")


                # If changes were made, convert back to string and write back  
                if _updated:
                    try:
                        _xml_body = ET.tostring(_root, encoding='unicode', method='xml')
                        _declaration = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                        _modified_xml_string = _declaration + _xml_body

                        # Write the modified XML string back to the file
                        _node.mWriteFile(_xml_path, _modified_xml_string)
                        ebLogTrace(f"Successfully updated relevant <domuVolume> tags (Type: {_input_image_type}) and wrote file '{_xml_path}' on '{_dom0}'.")
                    except Exception as e:
                        ebLogError(f"Error: Failed to write updated XML to '{_xml_path}' on '{_dom0}'. Details: {e}")
                        return False # Write failed
                else:  
                    ebLogTrace(f"No applicable <domuVolume> tags matching type '{_input_image_type}' required updating in '{_xml_path}' on '{_dom0}'. File not modified.")
                    return False

        except Exception as e:
            ebLogError(f"Error: Failed to connect to '{_dom0}' or unexpected issue during update of '{_xml_path}'. Details: {e}")
            return False

        return True
        
    def mGetLatestSystemImg(self, aImageVersions: Iterable[str]) -> Optional[str]:
        """
        Return the latest image version using version_compare.
        aImageVersions: iterable of version strings (not full filenames).
        """
        versions = list(aImageVersions)
        if not versions:
            return None
        return max(versions, key=cmp_to_key(version_compare))

    def mParseSystemImgVersion(self, aImageName: str) -> Optional[str]:
        """
        Extract the version segment from an image filename.
        Handles RTG vs non-RTG by convention; replace with a robust regex if needed.
        Expected pattern (example): <prefix>.<...>.version[.rtg].img or .kvm.img
        """
        parts = aImageName.split(".")
        if len(parts) < 5:
            ebLogError(f"Unexpected image name format: {aImageName}")
            return None
        if "rtg" in parts:
            # e.g., <x>.<y>.<z>.<version...>.rtg.<ext>
            version = ".".join(parts[3:-2]) or None
        else:
            version = ".".join(parts[3:-1]) or None
        return version
    
    def mGetSystemImageOndomO(self, aDom0: str) -> Optional[str]:
        """
        Check dom0 for available system images and return the latest version string.
        """
        try:
            images_list = getDom0VMImagesInfo(aDom0)  # [{'imgVersion': 'x.y', ...}, ...]
            ebLogTrace(f"System images found in {aDom0}: {images_list}")
            if not images_list:
                ebLogInfo(f"No system image present on {aDom0}")
                return None

            versions = [d.get("imgVersion") for d in images_list if d.get("imgVersion")]
            _latest_version = self.mGetLatestSystemImg(versions)
            ebLogTrace(f'Latest version found in dom0 : {_latest_version}')
            return _latest_version
        except Exception:
            error_details = traceback.format_exc()
            ebLogError(f"Error while checking for image in dom0: {aDom0}. Details: {error_details}")
            return None

    
    def mGetSystemImage(self, aDom0: str, aSystemImageName: str) -> Optional[str]:
        """
        Determine which image name to use by:
        1) Looking for exact version on dom0 or copying from repo if missing
        2) If not available, using the latest available version on dom0
        3) If not compatible, using the latest available in the repo (try RTG, KVM and non-KVM)
        Returns the base image name to patch into XML, or None if not found.
        """
        try:
            version = self.mParseSystemImgVersion(aSystemImageName)
            if not version:
                ebLogError(f"Unable to parse version from image name: {aSystemImageName}")
                return None

            ebox = self.__cluctrl
            is_kvm = ebox.mIsKVM()

            ebLogTrace(f"System image version to check: {version}")
            found, info, copied = copyVMImageVersionToDom0IfMissing(aDom0, version, is_kvm)
            ebLogInfo(f"Image for {version} found in dom0 -> {found}, info -> {info}, copied -> {copied}")

            if not found and not copied:
                ebLogInfo(f"Version {version} not found in dom0 or local repo; searching for latest available image in dom0")
                latest_dom0_version = self.mGetSystemImageOndomO(aDom0)
                ebLogTrace(f"Latest image found in dom0: {latest_dom0_version}")
                if latest_dom0_version:
                    found, info, copied = copyVMImageVersionToDom0IfMissing(aDom0, latest_dom0_version, is_kvm)
                    ebLogInfo(f"Latest image {latest_dom0_version} compatible -> {found}, info -> {info}, copied -> {copied}")

                if not found and not copied:
                    # Look in repo for newest compatible image
                    latest_repo = getNewestVMImageArchiveInRepoNodeRecovery()
                    if latest_repo:
                        img_version = latest_repo["imgVersion"]
                        found, info, copied = copyVMImageVersionToDom0IfMissing(aDom0, img_version, is_kvm)
                        ebLogInfo(f"Latest repo image {img_version} -> found: {found}, info: {info}, copied: {copied}")

            if (found or copied) and info:
                if info.get("isRtgImg"):
                    return info.get("imgBaseName")
                if info.get("isKvmImg"):
                    # imgBaseName for KVM may differ; normalize to actual image name without .kvm suffix
                    return formatVMImageBaseName(info.get("imgVersion"), aIsKvm=False)
                # Default: return base name if available
                return info.get("imgBaseName")

            ebLogInfo("No suitable system image could be determined.")
            return None

        except Exception:
            error_details = traceback.format_exc()
            ebLogError(f"Error while checking system image {aSystemImageName} in dom0 {aDom0}. Details: {error_details}")
         
    def mCheckGridImageOndomO(self, aDom0, aGridImage):
        _dom0 = aDom0
        _grid_img_xml = aGridImage
        _latest_system_img = None
        
        # Check the grid image presence in recovery dom0
        try:
            with connect_to_host(_dom0, get_gcontext()) as _node:
                _grid_image_destination = f'{getDom0VMImageLocation()}{_grid_img_xml}'
                remoteImgFound = _node.mFileExists(_grid_image_destination)
                if remoteImgFound:
                    ebLogTrace(f'Grid image: {_grid_img_xml} present in dom0: {_dom0}')
                    return True               
        except Exception as e:
            _msg = f'Grid image: {_grid_img_xml} missing in dom0: {_dom0} !'
            ebLogError(_msg)
            
    def mGetGridImageFromDom0(self, aDom0):
        """
        Get list of grid images from dom0 and returns the first  
        one found.
        """
        _dom0 = aDom0
        remote_dir="/EXAVMIMAGES"
        pattern="grid-klone-Linux-x86-64-*.zip"
        # re pattern to look for grid images without minor version
        valid_pattern = re.compile(r"^(.*)-(\d{2})(0)(\d{8,})(\.zip)$")
        list_command = f"ls -1 {os.path.join(remote_dir, pattern)}"
        try:
            with connect_to_host(_dom0, get_gcontext()) as _node:
                 _, out, err = _node.mExecuteCmd(list_command)
                 if _node.mGetCmdExitStatus() == 0:
                     for full_path in out.read().splitlines():
                        filename = os.path.basename(full_path.strip())
                        match = valid_pattern.match(filename)
                        if match:
                            # found a grid filename
                            ebLogTrace(f"Found valid image: {full_path.strip()}")
                            return full_path.strip()
                         
        except Exception as e:  
            ebLogError(f"Error cheking grid image in dom0 {_dom0}, error: {e}")
            return
        ebLogTrace("No valid grid image found in the list.")
        return
        
    def mVerifySystemAndGridImages(self, aDom0, aDomU):
        
        def _parseXMLValues(values):
            _sys, _grid = None, None
            for filename in values:
                if filename.endswith('.img'):
                    _sys = filename
                elif filename.endswith('.zip'):
                    _grid = filename
            return _sys, _grid
                    
        _recovery_dom0 = aDom0
        _new_domu = aDomU
        _ebox = self.__cluctrl
        ebLogTrace('Starting to verify System.first.boot and grid images...')
        # '/EXAVMIMAGES/conf/c3716n16c1.clientsubnet.devx8melastic.oraclevcn.com-vm.xml'
        _domU_xml_path = f'/EXAVMIMAGES/conf/{_new_domu}-vm.xml'
        # Read XML and get the system and grid image name 
        _xml_values = self.mParseXMLForNodeRecovery(_recovery_dom0, _domU_xml_path)
        if not _xml_values:
            _msg = f'Unable to parsel XML {_domU_xml_path}'
            ebLogError(_msg)
            raise ExacloudRuntimeError(aErrorMsg=_msg)
        
        _system_img_xml , _grid_image_xml = _parseXMLValues(_xml_values)
        
        _copied_system_img = self.mGetSystemImage(_recovery_dom0, _system_img_xml)
        if _copied_system_img is None:
            _msg = f'System image {_system_img_xml} not present in dom0 {aDom0} and exacloud image repo'
            ebLogError(_msg)
            raise ExacloudRuntimeError(aErrorMsg=_msg)

        if _copied_system_img != _system_img_xml:
            # xml image not present in the dom0, another available image has been copied
            _copied_system_img_path = f'/EXAVMIMAGES/{_copied_system_img}'
            _updated = self.mUpdateXMLTagValue(_recovery_dom0, _domU_xml_path, _copied_system_img_path)
            if not _updated:
                _msg = f'System image {_copied_system_img_path} could not be updated in XML'
                ebLogError(_msg)
                raise ExacloudRuntimeError(aErrorMsg=_msg)
        
        # Validate grid image in recovery dom0
        if self.mCheckGridImageOndomO(_recovery_dom0, _grid_image_xml):
            return
        
        # if image not present, check for other images on dom0
        _grid_image = self.mGetGridImageFromDom0(_recovery_dom0)
        if not _grid_image:
            # if no grid images present on dom0, call copy process
            _ebox.mUpdateDepFiles()
            # check if xml image copied to dom0
            if self.mCheckGridImageOndomO(_recovery_dom0, _grid_image_xml):
                return
            # Else get any grid image copied recently to dom0
            _grid_image = self.mGetGridImageFromDom0(_recovery_dom0)
        _updated = self.mUpdateXMLTagValue(_recovery_dom0, _domU_xml_path, _grid_image)
        if not _updated:
            _msg = f'System image {_grid_image} could not be updated in XML'
            ebLogError(_msg)
            raise ExacloudRuntimeError(aErrorMsg=_msg)

    def mRegisterVM(self, aDom0, aDomU):
        _dom0 = aDom0
        _domU = aDomU
        _ebox = self.__cluctrl
        _rc = 0
        try:
            _remotefile = ""
            _pubKey = ""
            _user = "root"
            _exakms = get_gcontext().mGetExaKms()
            _cparam = {"FQDN": _domU, "user": _user}
            _entry = _exakms.mGetExaKmsEntry(_cparam)

            if not _entry:
                ebLogWarn(f"No key found for {_user}@{_domU}.")
                _msg = f"Failed to create VM:{_domU}. SSH_KEYS are not available."
                raise ExacloudRuntimeError(0x0107, 0xA, _msg)
            else:
                _pubKey = _entry.mGetPublicKey()

            #Copy domU public key to dom0
            _key_file = f"id_rsa.{_domU}.root.pub"
            _remotefile = f"/tmp/{_key_file}"
            with NamedTemporaryFile(delete=False) as _tmp_file:
                _tmp_file.write(_pubKey.encode('utf8'))
                _tmp_file.close()
                self.mCopyPubKey(_dom0, _tmp_file.name, _remotefile)
                os.unlink(_tmp_file.name)

            _newdom0List = []
            _newdom0UList = []
            _newdom0List.append(_dom0)
            _newdom0UList.append([_dom0, _domU])
            #copy /opt/exacloud/config_info.json to dom0
            _ebox.mConfigureVMConsole(self.__options, _newdom0UList)
            
            # Copy system and grid images in dom0
            self.mVerifySystemAndGridImages(_dom0, _domU)

            _hv = getHVInstance(_dom0)
            _ebox.mAcquireRemoteLock()
            _hv.mCreateVM(_domU, _remotefile)
            _ebox.mReleaseRemoteLock()

            if not _ebox.mCheckIfVMExists(_domU, _dom0):
                _rc = 1
                self.mDeleteVM(_dom0, _domU, aNodeRecovery=True)
            else:
                _rc = 0
                ebLogInfo(f"Successfully completed creating guest {_domU}")

            #
            # Wait for the node to come back online
            #
            _retry_periods = 7
            _retry_interval = 30

            if _ebox.mCheckConfigOption('vm_time_sleep_reboot') is not None:
                _retry_interval = _ebox.mCheckConfigOption('vm_time_sleep_reboot') * 3

            _timeout_ecops = _ebox.mGetTimeoutEcops()
            _aTotalTime = _retry_periods * _timeout_ecops

            _natDomU = _domU
            if self.mCheckSshd(_natDomU, aTotalTime=_aTotalTime, aTimeout=_retry_interval):
                # even if port is open, wait one interval more for resiliency
                time.sleep(_retry_interval)
                _vmnode = exaBoxNode(get_gcontext())
                _vmnode.mSetUser('root')
                _vmnode.mConnect(aHost=_natDomU)
                _vmnode.mExecuteCmd("ip addr show | grep 'ib0\|ib1\|inet '")
                _vmnode.mDisconnect()
                ebLogInfo('VM ' + _domU + ' is now up and running.')

                #INSTALL SERIAL CONSOLE BITS IN NEW DOM0
                _vmc_dpy = VMConsoleDeploy(_ebox, self.__options)
                _vmc_dpy.mInstall(_newdom0List)

                #Start Containers exa-hippo-serialmux|exa-hippo-sshd for serial Console
                _consoleobj = serialConsole(_ebox, self.__options)
                _consoleobj.mRunContainer(_dom0, _domU)
                _consoleobj.mRestartContainer(_dom0, _domU, aMode="start")
            else:
                _rc = 1
                ebLogError(f"*** Failed to create VM:{_domU} on dom0:{_dom0}")

        except Exception as e:
            ebLogError(f"*** Failed to create VM:{_domU} on dom0:{_dom0} ,ERROR: {e}")
            _rc = 1
        return _rc

    def mStartVM(self, aDom0, aDomU):
        _dom0 = aDom0
        _domU = aDomU
        try:
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_dom0)

            _compHandler = self.__cluctrl.mGetComponentRegistry()
            _vmhandler = _compHandler.mGetComponent("vm_operations")
            if _vmhandler:
                _vmhandler.mSetOVMCtrl(aCtx=get_gcontext(), aNode=_node)

                #Start the VM after restoring from the backup
                _rc = self.__cluctrl.mRestartVM(_domU, aVMHandle=_vmhandler)
                if _rc != 0:
                    ebLogError('*** FATAL :: vmcmd: start and vmid: %s - Could not be started' % (_domU))
                    _hv = getHVInstance(_dom0)
                    _hv.mDestroyVM(_domU, True)
                    raise ExacloudRuntimeError(0x0411, 0xA, 'VM was not able to restart')
        finally:
            _node.mDisconnect()

    def mShutdownVM(self, aDom0, aDomU):
        _dom0 = aDom0
        _domU = aDomU
        _rc = 0
        try:
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_dom0)
            _compHandler = self.__cluctrl.mGetComponentRegistry()
            _vmhandler = _compHandler.mGetComponent("vm_operations")
            if _vmhandler:
                _vmhandler.mSetOVMCtrl(aCtx=get_gcontext(), aNode=_node)
                _vmhandler.mSetOVMCtrl(aCtx=get_gcontext(), aNode=_node)
                _rc = _vmhandler.mDispatchEvent("shutdown", None, _domU, self.__cluctrl)
        finally:
            _node.mDisconnect()
        return _rc

    def mDeleteVM(self, aDom0, aDomU, aNodeRecovery=False):
        _dom0 = aDom0
        _domU = aDomU
        _node_recovery = aNodeRecovery
        _ebox = self.__cluctrl
        _oeda_cleanup_success = False
        _ddpair = [[_dom0, _domU]]
        _exabm = self.__cluctrl.mIsExabm()

        _options = self.__options
        self.mSetSrcDom0DomU(aNewDom0=_dom0, aNewDomU=_domU)
        _srcdomU = self.mGetSrcDomU()

        _csu = csUtil()
        _bridges = _csu.mFetchBridges(self.__cluctrl, aDom0DomUPairs=_ddpair)

        #
        # Try to clean up via OEDA first
        #
        if _ebox.mCheckConfigOption('oeda_vm_delete_step', 'True'):
            #remove vm using oedacli first
            _non_oeda_cleanup = False
            try:
                _oeda_path  = _ebox.mGetOedaPath()
                _oedacli_bin = os.path.join(_oeda_path, "oedacli")
                _savexmlpath = os.path.join(_oeda_path, "exacloud.conf")
                _oedacli_mgr = OedacliCmdMgr( _oedacli_bin, _savexmlpath)

                _uuid = str(uuid.uuid1())
                _file = "deletenode_" + _uuid + ".xml"
                _deletenodexml = os.path.join(_oeda_path, "exacloud.conf", _file)
                _patchconfig = _ebox.mGetPatchConfig()
                shutil.copyfile(_patchconfig, _deletenodexml)

                # Update es.properties with non-root password
                ebLogInfo("Updating non-root password in es.properties for oedacli delete guest execution")
                _srcDomU = self.mGetSrcDomU()
                if _ebox.IsZdlraProv():
                    _pswd = _ebox.mGetZDLRA().mGetWalletViewEntry('passwd', _srcDomU)
                else:
                    _pswd = _ebox.mGetSysPassword(_srcDomU)
                _ebox.mUpdateOedaUserPswd(_ebox.mGetOedaPath(), "non-root", _pswd)

                _ebox.mAcquireRemoteLock()
                # OEDACLI: Delete Guest
                _oedacli_mgr.mVMOperation(_domU, _deletenodexml, _savexmlpath+'/deletedvm.xml', 'delete')
            except Exception as e:
                _non_oeda_cleanup = True
                ebLogInfo(f"Error while deleting the VM {_domU} using oedacli")
            finally:
                _ebox.mReleaseRemoteLock()

        # Kill any ongoing start-domain of same domU (bug 31349800)
        _step_time = time.time()
        self.__cluctrl.mKillOngoingStartDomains(aDom0DomUPair=_ddpair)
        self.__cluctrl.mLogStepElapsedTime(_step_time, 'Force VM shutdown')

        # Force delete unnamed
        _step_time = time.time()
        self.__cluctrl.mForceDeleteDomainUnnamed(self.__options, aDom0DomUPair=_ddpair)
        self.__cluctrl.mCleanUpStaleVm(_oeda_cleanup_success, aDom0DomUPair=_ddpair, aNodeRecovery=_node_recovery)

        if self.__cluctrl.mCheckConfigOption('min_vm_cycles_reboot') is not None:
            self.__cluctrl.mCheckVMCyclesAndReboot(aDom0DomUPair=_ddpair, aNodeRecovery=_node_recovery)

        _csu.mDeleteBridges(self.__cluctrl, _bridges)
        self.__cluctrl.mLogStepElapsedTime(_step_time, 'Force residual VM deletion')

        _consoleobj = serialConsole(self.__cluctrl, self.__options)
        for _dom0, _domU in _ddpair:
            _consoleobj.mRemoveSSH(_dom0, _domU)

        #
        # Removing libvirt network filters in kvm
        #
        _dom0s = [_dom0]
        if _exabm and self.__cluctrl.mIsKVM():
            if self.__cluctrl.mIsHostOL7(_dom0) or self.__cluctrl.mIsHostOL6(_dom0):
                ebIpTablesRoCE.mRemoveSecurityRulesExaBM(self.__cluctrl, aDom0s=_dom0s)

        # Cleanup entries from CRS
        self.mRemoveNodeFromCRS(_domU, _srcdomU)

    def mRemoveNodeFromCRS(self, aNodeToDelete, aSourceNode):
        _ebox = self.__cluctrl
        _vip = ""
        _deletenode = aNodeToDelete.split('.')[0]
        _srcdomU = aSourceNode

        with connect_to_host(_srcdomU, get_gcontext(), username="root") as _node:
            _cat_cmd = node_cmd_abs_path_check(node=_node, cmd="cat")
            _grep_cmd = node_cmd_abs_path_check(node=_node, cmd="grep")
            _cut_cmd = node_cmd_abs_path_check(node=_node, cmd="cut")
            _cmd = f"{_cat_cmd} /etc/oratab | {_grep_cmd} '^+ASM.*' | {_cut_cmd} -f 2 -d ':'"
            _i, _o, _e = _node.mExecuteCmd(_cmd)
            _out = _o.readlines()
            _path = _out[0].strip()

            _delnode = aNodeToDelete.split('.')[0]
            ebLogInfo(f"Removing stale entries of VM {_delnode} in the node {_srcdomU}")

            _node.mExecuteCmdLog(f'{_path}/bin/crsctl unpin css -n {_delnode}')
            _node.mExecuteCmdLog(f'{_path}/bin/crsctl stop cluster -n {_delnode}')
            _node.mExecuteCmdLog(f'{_path}/bin/crsctl delete node -n {_delnode}')

            _i, _o, _e = _node.mExecuteCmd(f'{_path}/bin/srvctl config vip -n {_delnode} | grep "VIP IPv4 Address"')
            if _node.mGetCmdExitStatus() == 0:
                _out = _o.readlines()
                for _vip_out in _out:
                    _vip = _vip_out.split(":")[1].strip()
                    ebLogInfo(f'Cleanup stale entries of {_delnode}/{_vip} from clusterware')
                    _node.mExecuteCmdLog(f'{_path}/bin/srvctl stop vip -vip {_vip} -force')
                    _node.mExecuteCmdLog(f'{_path}/bin/srvctl remove vip -vip {_vip} -force')

            _i, _o, _e = _node.mExecuteCmd(f'{_path}/bin/srvctl config vip -n {_delnode} | grep "VIP IPv6 Address"')
            if _node.mGetCmdExitStatus() == 0:
                _out = _o.readlines()
                for _vip_out in _out:
                    """
                    From https://confluence.oraclecorp.com/confluence/x/Oq308QE
                    [root@diagvmcl21-nxgt61 ~]# /u01/app/19.0.0.0/grid/bin/srvctl config vip -n diagvmcl21-nxgt62 | grep "VIP IPv6 Address"
                    VIP IPv6 Address: 2607:9b80:9a00:f521:b269:ebfd:53bb:83bc (inactive)
                    """
                    try:
                        _vip_list = _vip_out.split(" ")
                        if len(_vip_list) > 3:
                            _vip = _vip_list[3].strip()
                            ebLogInfo(f'Cleanup stale entries of {_delnode}/{_vip} from clusterware')
                            _node.mExecuteCmdLog(f'{_path}/bin/srvctl stop vip -vip {_vip} -force')
                            _node.mExecuteCmdLog(f'{_path}/bin/srvctl remove vip -vip {_vip} -force')
                    except Exception as ex:
                        ebLogError(f"Could not remove entry for IPv6 vip {_delnode}/{_vip} from clusterware. Error: {ex}.")

            _node.mExecuteCmdLog(f'{_path}/bin/olsnodes -s -t | grep {_delnode}')

            if _node.mGetCmdExitStatus() == 0:
                _node.mExecuteCmdLog(f'{_path}/bin/crsctl delete node -n {_delnode} -purge')
                _node.mExecuteCmdLog(f'{_path}/bin/olsnodes -s -t | grep {_delnode}')
                if _node.mGetCmdExitStatus() == 0:
                    _detail_error = f'Failed to cleanup stale entries of VM {_delnode} from clusterware'
                    _ebox.mUpdateErrorObject(gNodeElasticError['STALE_ENTRY_EXIST'], _detail_error)
                    ebLogError(_detail_error)
                    raise ExacloudRuntimeError(0x0801, 0xA, _detail_error)

        for _, _domU in _ebox.mGetOrigDom0sDomUs():

            _node = exaBoxNode(get_gcontext())
            _node.mSetUser('root')
            if not _node.mIsConnectable(_domU):                                                                                               
                ebLogWarn(f"*** DomU {_domU} is not connectable.")
                continue

            with connect_to_host(_domU, get_gcontext(), username="root") as _node:
                _node.mExecuteCmdLog(f'{_path}/bin/olsnodes -s -t | grep {_delnode}')
                if _node.mGetCmdExitStatus() == 0:
                    _node.mExecuteCmdLog(f'{_path}/bin/crsctl delete node -n {_delnode} -purge')
                    _node.mExecuteCmdLog(f'{_path}/bin/olsnodes -s -t | grep {_delnode}')

                    if _node.mGetCmdExitStatus() == 0:
                        _detail_error = f'Failed to cleanup stale entry of VM {_delnode} in the node {_domU}'
                        _ebox.mUpdateErrorObject(gNodeElasticError['STALE_ENTRY_EXIST'], _detail_error)
                        ebLogError(_detail_error)
                        raise ExacloudRuntimeError(0x0801, 0xA, _detail_error)

                # Remove the deleted node from /etc/hosts in existing domUs
                _node.mExecuteCmdLog(f"/bin/sed -i '/{_deletenode}/d' /etc/hosts")
                _node.mExecuteCmdLog(f"/bin/sed -i '/{_delnode}/d' /etc/hosts")

    def mUpdateArpCheckFlag(self, aDom0, aDomU):
        _dom0 = aDom0
        _domU = aDomU
        _ddpair = [[_dom0, _domU]]

        self.__cluctrl.mSetupArpCheckFlag(aDom0DomUPair=_ddpair, aUser="root")

    def mUpdateSecurityRules(self, aDom0, aDomU):
        _dom0 = aDom0
        _domU = aDomU
        _dom0s = [_dom0]
        _ebox = self.__cluctrl
        #
        # Setup ExaCS IPtables in KVM
        #
        if _ebox.mIsExabm() and _ebox.mIsKVM():
            _nftDom0s = _ebox.mGetHostsByTypeAndOLVersion(ExaKmsHostType.DOM0, ["OL8"])
            _iptDom0s = _ebox.mGetHostsByTypeAndOLVersion(ExaKmsHostType.DOM0, ["OL7", "OL6"])

            if _nftDom0s:
                ebIpTablesRoCE.mSetupSecurityRulesExaBM(_ebox, self.__options.jsonconf, aDom0s=_dom0s)

            if _iptDom0s:
                ebIpTablesRoCE.mPrevmSetupIptables(_ebox, aDom0s=_dom0s)

    def mPinNode(self, aDomU):
        _domU = aDomU
        try:
            _node = exaBoxNode(get_gcontext())
            _node.mSetUser('root')
            _node.mConnect(aHost=_domU)
            _cmd = "/usr/bin/cat /etc/oratab | /usr/bin/grep '^+ASM.*'"
            _i, _o, _e = _node.mExecuteCmd(_cmd)
            if _node.mGetCmdExitStatus() != 0:
                _node.mDisconnect()
                ebLogError('*** ORATAB entry missing')
                return
            _out = _o.readlines()
            _path = _out[0].split(':')[1].strip()
            _host = _domU.split('.')[0]
            _cmd = f"{_path}/bin/crsctl pin css -n {_host}"
            _node.mExecuteCmdLog(_cmd)
        finally:
            _node.mDisconnect()

    def mCheckSshd(self, aDomU, aTotalTime, aTimeout):
        _host = aDomU
        _start_time   = time.time()
        _time_elapsed = 0
        _loop_count = 0

        _ctx = get_gcontext()
        if _ctx.mCheckRegEntry('_natHN_' + _host):
            _host = _ctx.mGetRegEntry('_natHN_' + _host)
        _localNode = exaBoxNode(get_gcontext(), aLocal=True)
        try:
            _localNode.mConnect()
            while _time_elapsed < aTotalTime:
                #Check remote ssh port
                if _localNode.mCheckPortSSH(_host):
                    ebLogInfo('SSH port is alive on domU')
                    return True

                #Update time
                time.sleep(aTimeout)
                _time_elapsed = time.time() - _start_time
                if _loop_count % 10:
                    ebLogWarn('Waiting for VM: {0} to come up. Time elapsed: {1}s'.format(aDomU, _time_elapsed))
                _loop_count += 1
        finally:
            _localNode.mDisconnect()

        ebLogError("*** Timeout while waiting for ssh port")
        return False

    def mUpdateSSHKeys(self, aDom0, aDomU, aMountPoint, aUser="root"):
        _dom0 = aDom0
        _domU = aDomU
        _mount_point = aMountPoint
        _user = aUser

        try:
            _exakms = get_gcontext().mGetExaKms()
            _cparam = {"FQDN": _domU, "user": _user}
            _entry = _exakms.mGetExaKmsEntry(_cparam)

            if not _entry:
                ebLogWarn(f"No key found for {_user}@{_domU}. Generating {_user} key.")
                _dummyEntry = _exakms.mBuildExaKmsEntry("dummy", _user, _exakms.mGetEntryClass().mGeneratePrivateKey())
                _newEntry = _exakms.mBuildExaKmsEntry(_domU, _user, _dummyEntry.mGetPrivateKey(), ExaKmsHostType.DOMU)
                _exakms.mInsertExaKmsEntry(_newEntry)
                _pubKey = _newEntry.mGetPublicKey()
            else:
                _pubKey = _entry.mGetPublicKey()

            if _user == "root":
                _file_path  = "root/.ssh/authorized_keys"
            elif _user == "opc":
               _file_path = "opc/.ssh/authorized_keys"
            elif _user == "grid":
               _file_path =  "grid/.ssh/authorized_keys"
            elif _user == "oracle":
               _file_path =  "oracle/.ssh/authorized_keys"
            _path = os.path.join(_mount_point, _file_path)

            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost = _dom0)
            #
            # Injected root/opc pub keys to .ssh/authorized_keys file
            #
            _pubKey = _pubKey.strip()
            _cmd = """! /bin/cat {0} | grep "{1}" && """.format(_path, _pubKey)
            _cmd += """/bin/echo "{0}" >> {1}""".format(_pubKey, _path)
            _node.mExecuteCmdLog(_cmd)

        finally:
            _node.mDisconnect()

    def mEnableSSHConnectivity(self, aDom0, aDomU):
        _dom0 = aDom0
        _domU = aDomU

        try:
            _host = _domU.split('.')[0]
            _sys_mp = f"/mnt/vmsys1_{_host}"
            _home_mp = f"/mnt/vmhome_{_host}"

            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost = _dom0)

            if not _node.mFileExists("/opt/exacloud/bin/dmgr.py"):
                _script = 'scripts/images/dmgr.py'
                _path = '/opt/exacloud/bin/'
                _cmd  = '/bin/mkdir -p /opt/exacloud/bin'
                _node.mExecuteCmdLog(_cmd)
                _node.mCopyFile(_script, _path + 'dmgr.py')

            #Update root keys
            _cmd_str = f"/usr/bin/python3 /opt/exacloud/bin/dmgr.py mount {_domU} -ml LVDbSys1 -mp {_sys_mp}"
            _node.mExecuteCmdLog(_cmd_str)
            self.mUpdateSSHKeys(_dom0, _domU, _sys_mp, "root")
            self.mUpdateNetworkConfig(_dom0, _domU, _sys_mp, "root")
            _cmd_str = f"/usr/bin/python3 /opt/exacloud/bin/dmgr.py umount {_domU} -mp {_sys_mp}"
            _node.mExecuteCmdLog(_cmd_str)

            #Update grid/opc keys
            _cmd_str = f"/usr/bin/python3 /opt/exacloud/bin/dmgr.py mount {_domU} -ml LVDbHome -mp {_home_mp}"
            _node.mExecuteCmdLog(_cmd_str)
            self.mUpdateSSHKeys(_dom0, _domU, _home_mp, "oracle")
            self.mUpdateSSHKeys(_dom0, _domU, _home_mp, "grid")
            self.mUpdateSSHKeys(_dom0, _domU, _home_mp, "opc")
            _cmd_str = f"/usr/bin/python3 /opt/exacloud/bin/dmgr.py umount {_domU} -mp {_home_mp}"
            _node.mExecuteCmdLog(_cmd_str)
        finally:
            _node.mDisconnect()

    def mCreateQuorumDevices(self, aDomU):
        _domU = aDomU
        _diskgroup_suffix = self.__cluctrl.mGetClusterSuffix()
        _quorum_mgr = QuorumDiskManager(self.__cluctrl, "root", self.__options)
        _quorum_mgr.mDeleteQuorum(_domU, _diskgroup_suffix)
        _quorum_mgr.mCreateQuorum(_domU, _diskgroup_suffix)

    def mGetVIPHost(self, aDomU):
        _domU = aDomU
        _vip_host = ""
        _vip_dict = {}
        _vip_list = self.__cluctrl.mGetClusters().mGetCluster().mGetCluVips()
        for _vip in list(_vip_list.keys()):
            _vip_id = _vip_list[_vip].mGetCVIPMachines()[0]
            _vip_name = _vip_list[_vip].mGetCVIPName()
            _vip_domain = _vip_list[_vip].mGetCVIPDomainName()
            _ip = _vip_list[_vip].mGetCVIPAddr()
            _mac_config = self.__cluctrl.mGetMachines().mGetMachineConfig(_vip_id)
            _mac_name   = _mac_config.mGetMacHostName()
            if _mac_name == _domU:
                _vip_host = _vip_name + "." + _vip_domain
                if ':' in _ip:
                    # It is possible to have a single stack ipv6 - so update
                    # hostname info in both cases
                    _vip_dict.update({"ipv6": _ip, "vip_host": _vip_host})
                else:
                    _vip_dict.update({"ip": _ip, "vip_host": _vip_host})
        return _vip_dict

    def mAddVIP(self, aDomU):
        _domU = aDomU
        try:
            _netnum = ""
            _netmask_v4 = None
            _netmask_v6 = None
            _host = _domU.split('.')[0]
            _gihome, _, _ = self.__cluctrl.mGetOracleBaseDirectories(aDomU = _domU)
            _vip_dict = self.mGetVIPHost(_domU)
            _vip_host = _vip_dict["vip_host"]

            _node = exaBoxNode(get_gcontext())
            _node.mSetUser('root')
            _node.mConnect(aHost = _domU)

            _node.mExecuteCmdLog(f"{_gihome}/bin/srvctl config vip -node {_host}")
            _rc = _node.mGetCmdExitStatus()
            if _rc == 0:
                ebLogInfo(f"{_vip_host} is already started on nodes: {_host}")
                return

            """
            srvctl config network should look like below
            (root)# srvctl config network
            Network 1 exists
            Subnet IPv4: 198.51.100.0/255.255.255.0/bondeth0, static (inactive)
            Subnet IPv6: 2001:0db8:418:1ea4:0:0:0:0/64/bondeth0, static
            Ping Targets:
            Network is enabled
            Network is individually enabled on nodes:
            Network is individually disabled on nodes:
            """
            _cmd_str = f"{_gihome}/bin/srvctl config network"
            _i, _o, _e = _node.mExecuteCmd(_cmd_str)
            _out = _o.readlines()
            if _out:
                for line in _out:
                    if line.strip().startswith("Network") and line.strip().endswith("exists"):
                        _netnum = line.strip().split()[1].strip()
                    if line.strip().startswith("Subnet IPv4"):
                        try:
                            if len(line.strip().split()) > 2:
                                _netmask_v4 = line.strip().split()[2].split('/', 1)[1].split(',')[0]
                        except Exception as ex:
                            ebLogWarn(f"Could not get IPv4 netmask. Error: {ex}.")
                    if line.strip().startswith("Subnet IPv6"):
                        try:
                            if len(line.strip().split()) > 2:
                                _netmask_v6 = line.strip().split()[2].split('/', 1)[1].split(',')[0]
                        except Exception as ex:
                            ebLogWarn(f"Could not get IPv6 netmask. Error: {ex}.")

            _vip_ipv6 = _vip_dict.get("ipv6")
            _vip_ipv4 = _vip_dict.get("ip")
            if _vip_ipv4 and _vip_ipv6 and _vip_ipv4 != "0.0.0.0" and _vip_ipv6 != "::":
                _cmd_str = f"{_gihome}/bin/srvctl add vip -node {_host} -netnum {_netnum} -address {_vip_ipv4}/{_netmask_v4}"
                _node.mExecuteCmdLog(_cmd_str)
                _cmd_str = f"{_gihome}/bin/srvctl modify vip -node {_host} -address {_vip_ipv6}/{_netmask_v6}"
                _node.mExecuteCmdLog(_cmd_str)
            elif _vip_ipv4 and _vip_ipv4 != "0.0.0.0":
                _cmd_str = f"{_gihome}/bin/srvctl add vip -node {_host} -netnum {_netnum} -address {_vip_host}/{_netmask_v4}"
                _node.mExecuteCmdLog(_cmd_str)
            elif _vip_ipv6 and _vip_ipv6 != "::":
                _cmd_str = f"{_gihome}/bin/srvctl add vip -node {_host} -netnum {_netnum} -address {_vip_host}/{_netmask_v6}"
                _node.mExecuteCmdLog(_cmd_str)

            _cmd_str = f"{_gihome}/bin/srvctl start vip -node {_host}"
            _node.mExecuteCmdLog(_cmd_str)

            _cmd_str = f"{_gihome}/bin/srvctl config vip -node {_host}"
            _node.mExecuteCmdLog(_cmd_str)
        finally:
            _node.mDisconnect()

    def mAddCheckClusterAsm(self, aOptions, aDomU, aGridHome):
        _domu = aDomU
        _ebox = self.__cluctrl
        _vmnode = exaBoxNode(get_gcontext())
        _grid_home = aGridHome
        _vmnode.mSetUser('grid')
        _vmnode.mConnect(_domu)
        _cmd = "export ORACLE_HOME={0}; {0}/bin/lsnrctl services | grep -m1 -oP '\+ASM\d'"
        _i, _o, _e = _vmnode.mExecuteCmd(_cmd.format(_grid_home))
        _count = 0
        while (_vmnode.mGetCmdExitStatus() and _count < 20):
            time.sleep(30)
            _count = _count + 1
            ebLogWarn(f"*** Waiting for listener to report ASM in {_domu} post patching vm configuration")
            _i, _o, _e = _vmnode.mExecuteCmd(_cmd.format(_grid_home))

        if _vmnode.mGetCmdExitStatus():
            _detail_error = f"Listener service for ASM in {_domu} are not running." 
            ebLogError("*** Error: " + _detail_error)

        _vmnode.mDisconnect()

    def mGetDbList(self, aDomU):
        """
            Return list of databases for domU
        """
        _domU = aDomU
        _ebox = self.__cluctrl
        _path, _, _ = _ebox.mGetOracleBaseDirectories(aDomU = _domU)
        _node = exaBoxNode(get_gcontext())
        _node.mSetUser('root')
        _node.mConnect(aHost=_domU)
        _cmd = f'{_path}/bin/srvctl config database'
        _i, _o, _e = _node.mExecuteCmd(_cmd)
        _out = _o.readlines()
        _node.mDisconnect()
        if not _out or len(_out) == 0:
            return []
        ebLogInfo('*** mGetDbList:  %s ' % (_out))
        return _out

    def mGetDBUniqueName(self, aDomU, aDBName):
        _domU = aDomU
        _dbName = aDBName
        _db_unique = ""
        _location = ""

        try:
            _node = exaBoxNode(get_gcontext())
            _node.mSetUser('root')
            _node.mConnect(aHost = _domU)

            _cmd = "cat /etc/oratab | grep '^{0}.*'".format(_dbName)
            _, _out, _ = _node.mExecuteCmd(_cmd)
            _dbinfo  = _out.read()
            if _dbinfo:
                _dbinfo = _dbinfo.split(":")
                _db_unique = _dbinfo[0]
                _location = _dbinfo[1]
            ebLogTrace(f"dbUniqueName:{_db_unique} homePath:{_location}")
        finally:
            _node.mDisconnect()

        return _db_unique, _location

    def mStartDBInstanceIfOffline(self, aSrcDomU, aNewDomU, aDBName, aDBUnique, aDBHome):
        _srcdomU = aSrcDomU
        _newdomU = aNewDomU
        _dbname = aDBName
        _db_unique = aDBUnique
        _location = aDBHome
        _ebox = self.__cluctrl
        _newdomU_shrtnm = _newdomU.split('.')[0]
        _rc = 1

        _gihome, _, _ = _ebox.mGetOracleBaseDirectories(aDomU = _srcdomU)

        with connect_to_host(_newdomU, get_gcontext(), username="root") as _node:
            _db_unique_str = _db_unique.lower()
            _cmd_str = f"{_gihome}/bin/crsctl stat res ora.{_db_unique_str}.db | /bin/grep STATE |  /bin/cut -f 2 -d '=' "
            _i, _o, _e = _node.mExecuteCmd(_cmd_str)
            _out = _o.readlines()
            if _out:
                _db_state = [_line.strip() for _line in _out[0].strip().split(',')]
                _cmd_str =  f"{_gihome}/bin/srvctl status database -d {_db_unique} | /bin/grep {_newdomU_shrtnm} | /bin/grep 'not running' |  /bin/cut -f 2 -d ' ' "
                _i, _o, _e = _node.mExecuteCmd(_cmd_str)
                _output = _o.readlines()
                if _output:
                    _instance = _output[0].strip()
                    if 'OFFLINE' in _db_state and _node.mGetCmdExitStatus() == 0:
                        _node.mExecuteCmdLog(f"{_gihome}/bin/srvctl start instance -d {_db_unique} -i {_instance}")
                        _rc = _node.mGetCmdExitStatus()
                        if _rc == 0:
                            self.mAddOratab(_newdomU, _db_unique, _location)
        return _rc

    def mCheckDBInstanceIsUp(self, aDomU, aDatabase, aLocation,  aOptions, aRaiseError=True):

        _domU = aDomU
        _database = aDatabase
        _location = aLocation
        _ebox = self.__cluctrl

        _domU_list = []
        _dpairs = _ebox.mReturnDom0DomUPair()
        _domU_list = [ _domu for _ , _domu in _dpairs]

        _node = exaBoxNode(get_gcontext())
        _node.mSetUser('oracle')
        _node.mConnect(aHost = _domU)

        ebLogInfo("Wait for DB to be up")
        _db_cmd_pfx = _location
        _db_cmd_pfx = 'export ORACLE_HOME={0}; {0}'.format(_db_cmd_pfx)
        _db_cmd_pfx += '/bin/srvctl '
        if _ebox.mCheckConfigOption('db_timeout') is not None:
            _timeout = int(_ebox.mCheckConfigOption('db_timeout'))
        else:
            _timeout = 5 * 60

        _initial_time = time.time()
        _rc = 1
        while _rc != 0:
            _node.mExecuteCmd(_db_cmd_pfx + 'status database -d {0} | grep -c "is running" | grep -w {1}'.format(_database, len(_domU_list)))
            _rc = _node.mGetCmdExitStatus()
            _elapsed_time = time.time() - _initial_time
            if _timeout < _elapsed_time:
                _node.mDisconnect()
                if aRaiseError:
                    raise ExacloudRuntimeError(0x0114, 0xA, 'Timeout while waiting for db instance to be online. Aborting')
                else:
                    ebLogInfo(f"DB Instance are not up on {_domU_list[0]}")
                    return False
            ebLogTrace("Wait for DB to be up: {0}".format(_elapsed_time))
            time.sleep(3)

        _node.mDisconnect()
        ebLogInfo(f"DB Instance is up on {_domU}")
        return True

    def mAddOratab(self, aDomU, aDatabase, aLocation):
        _domU = aDomU
        _database = aDatabase
        _location = aLocation

        _node = exaBoxNode(get_gcontext())
        _node.mSetUser('oracle')
        _node.mConnect(aHost = _domU)

        _cmd = f"/bin/grep ^{_database} /etc/oratab"
        _node.mExecuteCmd(_cmd)
        if _node.mGetCmdExitStatus():
            ebLogInfo('Adding entry - %s:%s:Y to oratab' % (_database, _location))
            _cmd = "echo '{}:{}:Y' >> /etc/oratab"
            _node.mExecuteCmd(_cmd.format(_database, _location))
            _node.mDisconnect()
        else:
            ebLogInfo(f'*** {_database} is already in oratab')
            _node.mDisconnect()

    def mAddDBHomes(self, aOptions, aSrcDomU, aNewDomU, aDBInfo):
        """
        The function attempts to sync DB Homes on the new domU with the already
        existing domU (_srcdomU). 
        :param aOptions
        :param aSrcDomU
        :param aNewDomU
        :param aDBInfo Databases that are to be synced
        """
        _srcdomU = aSrcDomU
        _newdomU = aNewDomU
        _newdomU_shrtnm = _newdomU.split('.')[0]
        _ebox = self.__cluctrl
        _data = {}
        _db_info = aDBInfo

        ebLogInfo(f"List of databases requested by ECRA to be synced: {_db_info}")
        
        # Clean up /u02/opt/dbaas_images/* from newdomU
        ebLogInfo("Cleaning up /u02/opt/dbaas_images/dbnid before copying images in the VM: %s" % _newdomU)
        _username = "oracle"
        with connect_to_host(_newdomU, get_gcontext(), username=_username) as _node:
            _node.mExecuteCmdLog("/bin/rm -rf /u02/opt/dbaas_images/dbnid/*")

        # Update nodelist in grid.ini of all nodes (existing and new nodes) to contain
        # the correct set of nodes.
        _nodelist = " ".join([_domU.split('.')[0] for _, _domU in _ebox.mGetOrigDom0sDomUs()])

        _username = "root"
        for _, _domU in _ebox.mGetOrigDom0sDomUs():
            try:
                with connect_to_host(_domU, get_gcontext(), username=_username) as _node:
                    _node.mExecuteCmdLog(f"/var/opt/oracle/ocde/rops set_creg_key grid nodelist '{_nodelist}'")
            except Exception as e:
                ebLogError(f"Failed to set grid nodelist with error: {e}")


        try:
            with connect_to_host(_srcdomU, get_gcontext(), username=_username) as _node:
                _out = node_exec_cmd(_node, f"/usr/bin/sudo -u oracle /bin/scp -r /u02/opt/dbaas_images oracle@{_newdomU}:/u02/opt/")
                ebLogTrace(_out)
        except Exception as e:
            ebLogError(f'Error while copying /u02/opt/dbaas_images from {_srcdomU} to {_newdomU : }{e}')


        if _db_info:  # not None/empty
            _syncdblist = _db_info.split(',')
        else:
            _syncdblist = []
        _data[_newdomU] = { _db: "Fail" for _db in _syncdblist }
        _json = {}
        _dbaasobj = self.__dbaasobj
        
        _dbhomes = getDatabaseHomes(_srcdomU)
        ebLogTrace(f'DBHomes list from {_srcdomU} : {_dbhomes}')

        for _dbhome in _dbhomes:
            _version = _dbhomes[_dbhome]["version"]
            _dbhome_path = _dbhomes[_dbhome]["homePath"]
            cloneDbHome(_srcdomU, _version, _dbhome_path, _newdomU_shrtnm)

        _databases = getDatabases(_srcdomU)
        ebLogTrace(f'List of Databases from {_srcdomU}: {_databases}')

        _domainname = _newdomU.split('.',1)[1]

        for _dbname in _databases:
            _instance_added = False
            _data[_newdomU][_dbname] = "Fail"
            if not _ebox.mIsOciEXACC():
                if not _syncdblist or _dbname not in _syncdblist:
                    continue

            with connect_to_host(_srcdomU, get_gcontext(), username=_username) as _node:
                _node.mExecuteCmdLog(f"/var/opt/oracle/ocde/rops add_creg {_dbname} {_newdomU_shrtnm}")
            
            for _node in _databases[_dbname]['dbNodeLevelDetails']:
                # add instance will work only on nodes instance is running
                if _databases[_dbname]['dbNodeLevelDetails'][_node]['status'] == 'OPEN':
                    _nodefqdn  = _node + "." + _domainname
                    ebLogTrace(f'Db {_dbname} is running on node {_nodefqdn}')
                    
                    addInstance(_nodefqdn, _dbname, _newdomU_shrtnm)
                    _instance_added = True
                    break # only one running node is required
            
            if not _instance_added:
                continue

            _database_details = getDatabaseDetails(_srcdomU, _dbname)
            ebLogTrace(f'Details of db status {_database_details}')

            for _node in _database_details["dbNodeLevelDetails"]:
                if _node == _newdomU_shrtnm:
                    if _database_details["dbNodeLevelDetails"][_node]["status"] == "OPEN" and _data[_newdomU][_dbname] == 'Fail':
                        ebLogTrace(f'{_dbname} instance is added on node {_node}')
                        _data[_newdomU][_dbname] = "Pass"
                    else:
                        try:
                            _db_unique = _database_details["dbUniqueName"]
                            _location = _database_details["dbNodeLevelDetails"][_node]["homePath"]
                            _recoveryObj = NodeRecovery(_ebox, aOptions)
                            _rc = _recoveryObj.mStartDBInstanceIfOffline(_srcdomU, _newdomU, _dbname, _db_unique, _location)
                            if _rc == 0:
                                _data[_newdomU][_dbname] = "Pass"
                        except Exception as e:
                            ebLogError(f"Failed to start the database {_dbname} with error: {e}")

        ebLogInfo("Status of databases on the new node {}: {}".format(_newdomU, _data))
        return _data

    def mInstallRpm(self, aDom0, aDomU):
        _dom0 = aDom0
        _domU = aDomU
        _ddpair = [[_dom0, _domU]]
        _domUs = [_domU]
        _ebox = self.__cluctrl

        ebLogInfo(f"Reinstalling DBCS Agent rpm")
        _majorityVersion = _ebox.mGetOracleLinuxVersion(_domU)
        if (_majorityVersion in ["OL7", "OL8"]):
            if _ebox.mIsExabm():
                _ebox.mUpdateRpm('dbcs-agent.OL7.x86_64.rpm', aUndo = True, aDom0DomUPair=_ddpair)
                _ebox.mUpdateRpm('dbcs-agent.OL7.x86_64.rpm', aDom0DomUPair=_ddpair, aForce=True)
            else:
                if _ebox.mIsOciEXACC():
                    _ebox.mUpdateRpm('dbcs-agent-exacc.OL7.x86_64.rpm', aUndo = True, aDom0DomUPair=_ddpair)
                    _ebox.mUpdateRpm('dbcs-agent-exacc.OL7.x86_64.rpm', aDom0DomUPair=_ddpair, aForce=True)
        else:
            if _ebox.mIsExabm():
                _ebox.mUpdateRpm('dbcs-agent.OL6.x86_64.rpm', aUndo = True, aDom0DomUPair=_ddpair)
                _ebox.mUpdateRpm('dbcs-agent.OL6.x86_64.rpm', aDom0DomUPair=_ddpair, aForce=True)
            else:
                if _ebox.mIsOciEXACC():
                    _ebox.mUpdateRpm('dbcs-agent-exacc.OL6.x86_64.rpm', aUndo = True, aDom0DomUPair=_ddpair)
                    _ebox.mUpdateRpm('dbcs-agent-exacc.OL6.x86_64.rpm', aDom0DomUPair=_ddpair, aForce=True)

    def mGetServiceStatus(self, aDomU, aService):
        _domU = aDomU
        _service = aService
        _status = ""

        try:
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_domU)

            _cmd = f"/bin/systemctl is-active {_service}"
            _, _o, _ = _node.mExecuteCmd(_cmd)
            if _o:
                _out = _o.readlines()
                if not _out:
                    ebLogError(f"*** {_service} service stopped on DOMU:{_domU}")
                    _status = "stopped"
                else:
                    _status = _out[0].strip()
                    if _status == "active":
                        ebLogInfo(f"*** {_service} service running on DOMU:{_domU}")
                        _status = "running"
                    else:
                        ebLogError(f"*** {_service} service stopped on DOMU:{_domU}")
                        _status = "stopped"
        finally:
            _node.mDisconnect()
        return _status

    def mStartService(self, aDomU, aService):
        _domU = aDomU
        _service = aService

        try:
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_domU)

            _cmd = f"/bin/systemctl start {_service}"
            _node.mExecuteCmdLog(_cmd)
        finally:
            _node.mDisconnect()

    def mStartServices(self, aDom0, aDomU):
        _dom0 = aDom0
        _domU = aDomU

        _ebox = self.__cluctrl
        _options = self.__options
        _ddpair = [[_dom0, _domU]]

        #Start dbcsagent.service
        _status = self.mGetServiceStatus(_domU, aService="dbcsagent")
        if _status == "stopped":
            self.mStartService(_domU, aService="dbcsagent")

        #Start dbcsadmin.service
        _status = self.mGetServiceStatus(_domU, aService="dbcsadmin")
        if _status == "stopped":
            self.mStartService(_domU, aService="dbcsadmin")

        #Start syslens.service
        _status = self.mGetServiceStatus(_domU, aService="syslens")
        if _status == "stopped":
            self.mStartService(_domU, aService="syslens")

        #
        # Attach virtio serial device to KVM Guest.
        # Update the chasis information to GuestVM.
        #
        if _ebox.mIsKVM():
            _ebox.mUpdateVmetrics('vmexacs_kvm')
            _ebox.mStartVMExacsService(_options, aDom0DomUPair=_ddpair)
            
    def mRestoreRootAccessForRestoredNode(self, aDomU):
        """
        Connects to the specified node and enables root SSH access.
        Args:
            aDomU (str): The hostname or IP address of the Domain U node to restore root access on.

        Returns:
            None

        Raises:
            Exception: If an error occurs during the connection attempt or command execution.
        """
        try:
            with connect_to_host(aDomU, get_gcontext(), username='opc') as _node:
                # Provide root access
                _node.mExecuteCmdLog("sh -c '/opt/oracle.cellos/host_access_control rootssh -u'")
        except Exception as e:
            ebLogError(f"Failed to restore root access on {aDomU}: {str(e)}")
            raise

class QuorumDiskManager(object):

    def __init__(self, aCluCtrlObj, aUser, aOptions):

        self.__cluctrl = aCluCtrlObj
        self.__options = aOptions
        self.__user = aUser
        self.fake_hosts = {}

    def mCreateQuorum(self, aDomU, aSuffix="C1"):
        _domU = aDomU
        ebLogInfo('*** Create Steps')
        _num_cells = int(self.mGetCellCount(_domU))
        if _num_cells >= 5:
           ebLogInfo('*** Quorum disks are not needed since there are '+ str(_num_cells) + ' cells.')
           return

        if not self.mVerifyVD(_domU):
            self.mCreateQDConfig()
            self.mCreateQT(aSuffix)
            self.mCreateQD()
            self.mAddQD(_domU, aSuffix)
            self.mVerifyVD(_domU)

    def mDeleteQuorum(self, aDomU, aSuffix="C1"):
        _domU = aDomU
        ebLogInfo("*** Delete Steps")
        if not self.mVerifyVD(_domU):
            _qdconfig_nodes = self.mQDConfigNodes(_domU)
            self.mDropQD(_domU, aSuffix)
            if self.mIsQDdropped(_domU):
                self.mDeleteQD(_qdconfig_nodes)
                self.mDeleteQT(_qdconfig_nodes)
                self.mDeleteQDConfig(_qdconfig_nodes)
        else:
            ebLogInfo('*** nothing to be done')

    def mNormalizeHost(self, hostname):
        ebLogInfo('*** Normalize hostname {}'.format(hostname))
        fake_hostname = hostname.replace('-','')
        rndStr = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(2))
        fake_hostname = fake_hostname[-9:]
        fake_hostname = 'qm' + rndStr + fake_hostname
        self.fake_hosts[hostname] = fake_hostname
        return fake_hostname

    def mDetectVirtEnv(self, aDomU):
        _domU = aDomU
        _cmd = '/usr/bin/systemd-detect-virt'
        with connect_to_host(_domU, get_gcontext(), username="root") as _node:
            _, _o, _e = _node.mExecuteCmd(_cmd)
            _out = _o.read().strip()
            ebLogInfo(f"{_out} environment detected.")
        return _out

    def mGetClusterNodes(self, aDomU, aGIHome):
        _domU = aDomU
        _gihome = aGIHome
        _olsNodeList = []
        with connect_to_host(_domU, get_gcontext(), username=self.__user) as _node:
            _, _o, _e = _node.mExecuteCmd(_gihome + '/bin/olsnodes -s -n|grep Active')
            _out = _o.readlines()
            ebLogInfo(f"olsnodes reported: {_out}")
            if _node.mGetCmdExitStatus() != 0:
                ebLogError('*** No active node in the cluster')
            else:
                for _entry in _out:
                    _olsNodeList.append(_entry.split("\t")[0].strip())
        return _olsNodeList

    def mQDList(self, aDomU):
        _domU = aDomU
        _ebox = self.__cluctrl
        ebLogInfo("*** Quorum devices name list for DATA/RECO dg")
        qd_list = []

        _gridhome, _, _ = _ebox.mGetOracleBaseDirectories(aDomU = _domU)
        with connect_to_host(_domU, get_gcontext(), username="grid") as _node:
            _cmd_pfx = "cd %s/bin;"%(_gridhome)
            _cmd = _cmd_pfx + "echo \"select name from v\$asm_disk where name like 'QD_%'; \" | ./sqlplus -s / as sysasm"
            _i, _o, _e = _node.mExecuteCmd(_cmd)
            _count = 0
            while (_node.mGetCmdExitStatus() and _count < 2):
                time.sleep(30)
                _count = _count + 1
                ebLogTrace(f"*** Waiting for sql connection...")
                _i, _o, _e = _node.mExecuteCmd(_cmd)
            _output = _o.read()
            ebLogTrace(f"SQL CMD OUTPUT:{_output}")
            for line in _output.splitlines():
                if line != "" and "NAME" not in line and "------" not in line and "rows selected" not in line and 'QD_' in line:
                    qd_list.append(line)
        ebLogInfo("Quorum disks {}".format(qd_list))
        return qd_list

    def mGetCellCount(self, aDomU):
        _domU = aDomU
        with connect_to_host(_domU, get_gcontext(), username=self.__user) as _node:
            _cmd = 'cat /etc/oracle/cell/network-config/cellip.ora |wc -l'
            _i, _o, _e = _node.mExecuteCmd(_cmd)
            _output = _o.read().strip()
        return _output

    def mQDConfigNodes(self, aSrcDomU):
        _srcdomU = aSrcDomU
        ebLogInfo("*** Retrieve the list of Nodes that have Quorum Disks Configured")
        _qdconfig_nodes = []

        _dpairs = self.__cluctrl.mReturnDom0DomUPair()
        for _, _domU in _dpairs:
            with connect_to_host(_domU, get_gcontext(), username=self.__user) as _node:
                _cmd = "/opt/oracle.SupportTools/quorumdiskmgr --list --config"
                _i, _o, _e = _node.mExecuteCmd(_cmd)
                _rc = _node.mGetCmdExitStatus()
                if _rc == 0:
                    _qdconfig_nodes.append(_domU)
        ebLogInfo("Nodes that have Quorum Disks Configured {}".format(_qdconfig_nodes))
        return _qdconfig_nodes

    def mDropQD(self, aDomU, aSuffix="C1"):
        _domU = aDomU
        ebLogInfo("*** Drop the DATA/RECO QDs from ASM diskgroups")
        qd_list = self.mQDList(_domU)
        with connect_to_host(_domU, get_gcontext(), username="grid") as _node:
            for qd in qd_list:
                if "DATA" in qd:
                    dg = "DATA" + aSuffix
                elif "RECO" in qd:
                    dg = "RECO" + aSuffix
                _path, _sid = self.__cluctrl.mGetGridHome(_domU)
                _cmd_pfx = 'ORACLE_HOME=%s;export ORACLE_HOME;ORACLE_SID=%s; export ORACLE_SID;PATH=$PATH:$ORACLE_HOME/bin;export PATH;'%(_path, _sid)
                _cmd = _cmd_pfx + "echo \"alter diskgroup %s drop quorum disk %s force;\" | sqlplus -s / as sysasm" % (dg, qd)
                _i, _o, _e = _node.mExecuteCmd(_cmd)
                _output = _o.read()
                ebLogInfo(_output)

    def mIsQDdropped(self, aDomU):
        _domU = aDomU
        ebLogInfo("*** Check if all offline DATA/RECO QDs are dropped")
        with connect_to_host(_domU, get_gcontext(), username="grid") as _node:
            _path, _sid = self.__cluctrl.mGetGridHome(_domU)
            _cmd_pfx = 'ORACLE_HOME=%s;export ORACLE_HOME;ORACLE_SID=%s; export ORACLE_SID;PATH=$PATH:$ORACLE_HOME/bin;export PATH;'%(_path, _sid)
            _failgroupType = "QUORUM"
            _cmd = _cmd_pfx + "echo \"select name from v\$asm_disk where failgroup_type='" + _failgroupType + "' ;\" | sqlplus -s / as sysasm"
            _i, _o, _e = _node.mExecuteCmd(_cmd)
            _output = _o.read()
            for line in _output.splitlines():
                if line != "" and "NAME" not in line and "------" not in line and "rows selected" not in line:
                    if '_DROPPED_' not in line:
                        ebLogInfo(line)
                        return False
            return True

    def mDeleteQD(self, aQDNodes):
        _qdconfig_nodes = aQDNodes
        ebLogInfo("*** Delete the Quorum devices on all the cluster nodes where Quorum is configured")
        for _domU in _qdconfig_nodes:
            with connect_to_host(_domU, get_gcontext(), username=self.__user) as _node:
                _cmd = "/opt/oracle.SupportTools/quorumdiskmgr --delete --device"
                _node.mExecuteCmdLog(_cmd)

    def mDeleteQT(self, aQDNodes):
        _qdconfig_nodes = aQDNodes
        ebLogInfo("*** Delete the Quorum targets on the two base cluster nodes only")
        for _domU in _qdconfig_nodes:
            with connect_to_host(_domU, get_gcontext(), username=self.__user) as _node:
                _cmd = "/opt/oracle.SupportTools/quorumdiskmgr --delete --target"
                _node.mExecuteCmdLog(_cmd)

    def mDeleteQDConfig(self, aQDNodes):
        _qdconfig_nodes = aQDNodes
        ebLogInfo("*** Delete Quorum Config on all the cluster nodes")
        for _domU in _qdconfig_nodes:
            with connect_to_host(_domU, get_gcontext(), username=self.__user) as _node:
                _cmd = "/opt/oracle.SupportTools/quorumdiskmgr --delete --config"
                _node.mExecuteCmdLog(_cmd)

    def mVerifyVD(self, aDomU):
        _domU = aDomU
        ebLogInfo('*** Verify Clusterware automatically adds/uses quorum devices')

        with connect_to_host(_domU, get_gcontext(), username=self.__user) as _node:
            _cmd = "cat /etc/oratab | grep '^+ASM.*' | cut -f 2 -d ':'"
            _crs_cmd_pfx = _node.mSingleLineOutput(_cmd)
            _crs_cmd_pfx += '/bin/crsctl '

            _cmd = _crs_cmd_pfx + "query css votedisk;"
            _i, _o, _e = _node.mExecuteCmd(_cmd)
            _output = _o.read()
            _count = 0
            for _line in _output.splitlines():
                if 'ONLINE' in _line and 'exadata_quorum' in _line:
                    _count += 1
            if _count == 2:
               ebLogInfo('*** SUCCESS: Located 2 QD based voting disks')
               return True
            ebLogError('*** ERROR: Located less than 2 QD based voting disks')
            return False

    def mVerifyQD(self, aDomU):
        _domU = aDomU
        _count = 0
        ebLogInfo('*** Ensure ASM can discover the quorum devices')
        _gihome, _, _obase = self.__cluctrl.mGetOracleBaseDirectories(_domU)
        with connect_to_host(_domU, get_gcontext(), username="root") as _node:
            _cmd = "export ORACLE_HOME={0}; {0}/bin/kfod op=disks disks=all".format(_gihome)
            _i, _o, _e = _node.mExecuteCmd(_cmd)
            _output = _o.read()
            for line in _output.splitlines():
                if 'exadata_quorum' in line:
                    _count += 1
            if _count == 4:
               return True
        return False

    def mCreateQDConfig(self):
        ebLogInfo("*** Create Quorum Config on all the cluster nodes")
        _dpairs = self.__cluctrl.mReturnDom0DomUPair()
        for _dom0, _domU in _dpairs:
            _env = self.mDetectVirtEnv(_domU)

            with connect_to_host(_domU, get_gcontext(), username=self.__user) as _node:
                if _env == "xen":
                    _cmd = "/opt/oracle.SupportTools/quorumdiskmgr --create --config --owner=\'grid\' --group=\'asmadmin\' --network-iface-list=\'clib0,clib1\'"
                else:
                    _cmd = "/opt/oracle.SupportTools/quorumdiskmgr --create --config --owner=\'grid\' --group=\'asmadmin\' --network-iface-list=\'clre0,clre1\'"
                _node.mExecuteCmdLog(_cmd)

    def mCreateQT(self, aSuffix="C1"):
        ebLogInfo('*** Create Quorum targets on RECO dg across base Nodes and make them visible to all nodes')
        if aSuffix:
            _data = "DATA" + aSuffix
            _reco = "RECO" + aSuffix

        status=''
        output=''
        _dpairs = self.__cluctrl.mReturnDom0DomUPair()
        ic = ''
        for _dom0, _domU in _dpairs:
            _env = self.mDetectVirtEnv(_domU)
            with connect_to_host(_domU, get_gcontext(), username=self.__user) as _node:
                if _env == 'xen':
                    _cmd = "/usr/sbin/ip a s clib0|grep inet | awk {{'print $2'}} | cut -f 1 -d '/'"
                    _i, _o, _e = _node.mExecuteCmd(_cmd)
                    _output = _o.read()
                    for line in _output.splitlines():
                       ic += line
                       ic += ','

                    _cmd = "/usr/sbin/ip a s clib1|grep inet | awk {{'print $2'}} | cut -f 1 -d '/'"
                    _i, _o, _e = _node.mExecuteCmd(_cmd)
                    _output = _o.read()
                    for line in _output.splitlines():
                       ic += line
                       ic += ','
                else:
                    _cmd = "/usr/sbin/ip a s clre0|grep inet|grep inet  | awk {{'print $2'}}  | cut -f 1 -d '/'"
                    _i, _o, _e = _node.mExecuteCmd(_cmd)
                    _output = _o.read()
                    for line in _output.splitlines():
                       ic += line
                       ic += ','

                    _cmd = "/usr/sbin/ip a s clre1|grep inet|grep inet  | awk {{'print $2'}}  | cut -f 1 -d '/'"
                    _i, _o, _e = _node.mExecuteCmd(_cmd)
                    _output = _o.read()
                    for line in _output.splitlines():
                       ic += line
                       ic += ','
        ic = ic.rstrip(',')

        # check for hostname length
        # chars reserved for asm-disk-group
        _dpairs = self.__cluctrl.mReturnDom0DomUPair()
        for _dom0, _domU in _dpairs:
            _host = _domU.split('.')[0]
            _fakeHost = _host
            if len(_host) > 20:
                _fakeHost = self.mNormalizeHost(_host)
            with connect_to_host(_domU, get_gcontext(), username=self.__user) as _node:
                _cmd = "/opt/oracle.SupportTools/quorumdiskmgr --create --target --asm-disk-group={0} --visible-to=\"{1}\" --host-name=\"{2}\" --force".format(_data, ic, _fakeHost)
                _node.mExecuteCmdLog(_cmd)

                _cmd = "/opt/oracle.SupportTools/quorumdiskmgr --create --target --asm-disk-group={0} --visible-to=\"{1}\" --host-name=\"{2}\" --force".format(_reco, ic, _fakeHost)
                _node.mExecuteCmdLog(_cmd)

    def mCreateQD(self):
        ebLogInfo('*** Create Quorum devices on DATA/RECO dg across all nodes')
        bic = ''
        status=''
        output=''
        _dpairs = self.__cluctrl.mReturnDom0DomUPair()
        for _dom0, _domU in _dpairs:
            _env = self.mDetectVirtEnv(_domU)
            with connect_to_host(_domU, get_gcontext(), username=self.__user) as _node:
                if _env == 'xen':
                    _cmd = "/usr/sbin/ip a s clib0|grep inet | awk {{'print $2'}} | cut -f 1 -d '/'"
                    _i, _o, _e = _node.mExecuteCmd(_cmd)
                    _output = _o.read()
                    for line in _output.splitlines():
                        bic += line
                        bic += ','
                    _cmd = "/usr/sbin/ip a s clib1|grep inet | awk {{'print $2'}} | cut -f 1 -d '/'"
                    _i, _o, _e = _node.mExecuteCmd(_cmd)
                    _output = _o.read()
                    for line in _output.splitlines():
                        bic += line
                        bic += ','
                else:
                    _cmd = "/usr/sbin/ip a s clre0|grep inet|grep inet  | awk {{'print $2'}}  | cut -f 1 -d '/'"
                    _i, _o, _e = _node.mExecuteCmd(_cmd)
                    _output = _o.read()
                    for line in _output.splitlines():
                        bic += line
                        bic += ','
                    _cmd = "/usr/sbin/ip a s clre1|grep inet|grep inet  | awk {{'print $2'}}  | cut -f 1 -d '/'"
                    _i, _o, _e = _node.mExecuteCmd(_cmd)
                    _output = _o.read()
                    for line in _output.splitlines():
                        bic += line
                        bic += ','
        bic = bic.rstrip(',')
        ebLogInfo('*** Following operation takes 2 mins per node...')
        _dpairs = self.__cluctrl.mReturnDom0DomUPair()
        for _dom0, _domU in _dpairs:
            with connect_to_host(_domU, get_gcontext(), username=self.__user) as _node:
                _cmd = "/opt/oracle.SupportTools/quorumdiskmgr --create --device --target-ip-list=\"{}\"".format(bic)
                _node.mExecuteCmdLog(_cmd)

    def mAddQD(self, aDomU, aSuffix="C1"):
        _domU = aDomU
        if not self.mVerifyQD(_domU):
           ebLogError('*** ERROR:  ASM cannot discover the quorum devices')
        ebLogInfo('*** Add the quorum disks back to ASM disk groups')

        with connect_to_host(_domU, get_gcontext(), username="grid") as _node:
            _cmd = "ls -ld /dev/exadata_quorum/* | awk {'print $9'}"
            _i, _o, _e = _node.mExecuteCmd(_cmd)
            _output = _o.read()
            dstr = 'alter diskgroup DATA{0} add '.format(aSuffix)
            rstr = 'alter diskgroup RECO{0} add '.format(aSuffix)

            for line in _output.splitlines():
                if 'DATA' in line:
                    fgn = line.rsplit('/', 1)[1]
                    dstr += "quorum failgroup {0} disk \'{1}\' ".format(fgn, line)
                if 'RECO' in line:
                   fgn = line.rsplit('/', 1)[1]
                   rstr += "quorum failgroup {0} disk \'{1}\' ".format(fgn, line)

            dstr += ';'
            rstr += ';'

            _cmd = "echo \"{}\" | sqlplus -s / as sysasm".format(dstr)
            _node.mExecuteCmdLog(_cmd)

            _cmd = "echo \"{}\" | sqlplus -s / as sysasm".format(rstr)
            _node.mExecuteCmdLog(_cmd)
