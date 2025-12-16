#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/ovm/csstep/exascale/exascaleutils.py /main/86 2025/11/27 16:55:04 pbellary Exp $
#
# exascaleutils.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      exaScaleUtils - Exascale Utility file for Create Service & CRED operations
#
#    DESCRIPTION
#      Implements utilities used during exascale create service execution 
#
#    NOTES
#      NONE
#
#    MODIFIED   (MM/DD/YY)
#    pbellary    11/24/25 - Enh 38685113 - EXASCALE: POST CONFIGURE EXASCALE EXACLOUD SHOULD FETCH STRE0/STE1 FROM DOM0
#    rajsag      11/20/25 - bug 38673238 - exacloud: vm backup xs migration
#                           failed valueerror: could not convert string to
#                           float
#    pbellary    11/19/25 - Bug 38653608 - MIGRATE VMBACKUP TO XS:FAILING FOR ASM CLUSTER
#    pbellary    11/19/25 - Bug 38653608 MIGRATE VMBACKUP TO XS:FAILING FOR ASM CLUSTER
#    scoral      11/18/25 - Bug 38667668 - Improved EDV volume ID reading to be
#                           compatible with 25.2.X Exadata image format.
#    rajsag      11/10/25 - bug 38631588 - exacc gen-2 - exascale phase-2
#                           testing: sync call is failing for xsvault bug
#                           38631571 - exacc gen-2 - exascale testing: config
#                           exascle is failing where asm cluster does not have
#                           active db
#    scoral      11/07/25 - Bug 38625156 - Read VM maker output for "vm_maker --check"
#    pbellary    11/05/25 - Bug 38473536 - EXASCALE VM STORAGE CONFIGURATION FAILING:ERROR:INVALID EXASCALECLUSTER NAME
#    siyarlag    10/31/25 - Bug 38500170 - add mCreateOracleWallet
#    pbellary    10/30/25 - Enh 38596691 - ASM/EXASCALE TO SUPPORT ADD NODE WITH EDV IMAGE
#    rajsag      10/30/25 - 38581052 - exacs:25.4.1:exascale integration on
#    pbellary    10/28/25 - Bug 38512539 - INCORRECT VM BACKUP CONF FILE AFTER MIGRATE FROM LOCAL TO EXASCALE BACKUP (EXASCALE IMAGES)
#    pbellary    10/27/25 - Bug 38568039 - XSCONFIG IF TRIGGERED AFTER CELL DISKS HAVE BEEN DELETED WHOULD TRIGGER OEDA STEP TO CREATE CELL DISKS
#    scoral      10/23/25 - Bug 38571211 - EXACC:BB:25.3.1.0.0:CREATE SERVICE:FAILED IN POSTGINID STEP WITH ERROR CANNOT RESIZE LOGICAL VOLUME LVDBVAR1
#    pbellary    10/22/25 - Bug 38435268 - OEDACLI: RESET VLANID FOR CELLS IS UPDATING FLASHCACHEMODE TO WRITETHROUGH 
#    scoral      10/17/25 - Bug 38500655 - Added mResizeEDVVolume.
#    scoral      10/13/25 - Bug 38520443 - Add grid EDV size to mPatchEDVVolumes
#    rajsag      09/17/25 - enh 38389132 - exacloud: autoencryption support for
#                           exascale configuration
#    pbellary    09/22/25 - Bug 38458617 - CREATE DATABASE FAILED BECAUSE SAME CLUSTER ASSOCIATED TO TWO VAULTS 
#    pbellary    09/20/25 - Bug 38452464 - CREATE-SERVICE MISSING DOM0 IN OWNERS LIST IN VOLUME EDV CASE EXASCALE IMAGE / LEGACY BACKUP 
#    pbellary    09/19/25 - Bug 38450242 - EXACLOUD SHOULD UPDATE FLASHCACHEMODE TO WRITEBACK AFTER UPDATING VLANID ON CELLS 
#    scoral      09/29/25 - Bug 38338038 - Update EDV sizes in cluster XML
#                           during mPatchEDVVolumes.
#    rajsag      08/29/25 - 38360364 EXASCALE: EXACLOUD FAILURE IN MGETRACKSIZE
#                           DURING XSCONFIG FLOW ON ECS MAIN LABELS 38363129
#                           OCIEXACC: EXASCALE: EXACLOUD SHOULD CHECK TO SEE IF
#                           AT LEAST 1 EXASCALECLUSTER IS DEFINED IN ES.XML TO
#                           DETERMINE IF XML IS EXASCALE OR NOT
#    jfsaldan    08/26/25 - Enh 37999800 - EXACLOUD: EXASCALE CONFIG FLOW TO
#                           ENABLE AUTOFILEENCRYPTION=TRUE AFTER EXASCALE IS
#                           CONFIGURED.
#    scoral      08/26/25 - Bug 38338613 - EXASCALE: EXACLOUD SHOULD EITHER
#                           REBOOT THE DOMUS OR THE DOM0 DEPENDING ON THE
#                           EXADATA VERSION DURING EXASCALE SETUP
#    rajsag      08/20/25 - bug 38330988 - exacc:24.3.2.4.0:xsconfig:update
#                           exascale size when no db vault exists does not
#                           syncs usedstoragexsgb metadata
#    pbellary    08/15/25 - Enh 38318848 - CREATE ASM CLUSTERS TO SUPPORT VM STORAGE ON EDV OF IMAGE VAULT
#    pbellary    08/12/25 - Bug 38294104 - VAULT DELETION SKIPPED DUE TO INVALID CLUSTER NAME AS PART OF THE CLUSTER DELETION WORKFLOW 
#    rajsag      08/06/25 - Enh 38208138 exascale phase 2: fetch stre0 and
#                           stre1 ips from exacloud for add node operation
#    rajsag      07/08/25 - 38147574 - exacloud: xs pool size not syncing after
#                           xs configure/update w/f
#    pbellary    06/27/25 - Bug 38123526 - EXASCALE: EXACLOUD SHOULD PATCH DNS/NTP SERVER DETAILS FOR XSCONFIG COMMAND 
#    pbellary    06/25/25 - Enh 37698307 - CREATE SERVICE FLOW TO CREATE VM BACKUP CONF FILE FOR EACH VM TO IDENTIFY VM BACKUP TYPE AS LOCAL OR EXASCALE
#    scoral      06/11/25 - Bug 38044288 - Retry RoCE network configuration
#                           after QinQ configuration during mEnableQinQ.
#    pbellary    06/06/25 - Enh 38035467 - EXASCALE: EXACLOUD TO PROVIDE ACFS FILE SYSTEM SIZES IN SYNCH CALL
#    rajsag      06/09/25 - Enhancement Request 37966939 - exascale vm image &
#                           vm backup vault operations
#    scoral      06/05/25 - Bug 37514524 - Add NFTables rules for stre0 & stre1
#                           interfaces in Dom0s as part of mEnableQinQ.
#    rajsag      05/28/25 - 38003730 - exacs:25.2.1.1:rc2:exascale vault resize
#                           failing:error - 22173 - critical exception caught
#                           aborting request ['nonetype' object is not
#                           iterable]
#    pbellary    05/26/25 - Enh 37768130 - SUPPORT RESHAPE/RESIZE FOR THE ACFS FILESYSTEM CREATED ON EXASCALE CLUSTERS 
#    pbellary    05/21/25 - Enh 37927692 - EXASCALE: EXACLOUD TO SUPPORT CREATION OF EDV FOR /U02 FOR THE VM IMAGE ON EDV (IMAGE VAULT)
#    pbellary    05/21/25 - Enh 37698277 - EXASCALE: CREATE SERVICE FLOW TO SUPPORT VM STORAGE ON EDV OF IMAGE VAULT 
#    pbellary    04/16/25 - Enh 37842812 - EXASCALE: REFACTOR ACFS CREATION DURING CREATE SERVICE
#    pbellary    04/16/25 - Bug 37778364: CONFIGURE EXASCALE IS FAILING IN X11 ENV FOR EXTREME FLASH STORAGE TYPES
#    pbellary    02/28/25 - Bug 37650925 - EXASCALE: TERMINATE EXASCALE CLUSTER NOT DELETING THE CLUSTER FILES IN VAULT
#    pbellary    02/21/25 - Bug 37614526 - EXACC 24.3.2 :EXASCALE: TERMINATE EXASCALE CLUSTER NOT DELETING THE VAULT ACL ASSOCIATION
#    pbellary    06/02/24 - Bug 37517052 - EDV detach is failing with 'operation in progress'
#    rajsag      01/31/25 - 7540192 - exacc:bb:exascale:ecraerror:exacloud :
#                           unable to resize the storage pool hcpool??
#    rajsag      01/30/25 - Enh 37532331 - exascale: enhance the qinq check to
#                           enable qinq on those nodes only where the qinq
#                           check failed. make sure to validate the store IPs
#                           too
#    rajsag      01/28/25 - bug 37498922 - exacc:bb:exascale: configure
#                           exascale failed - exacloud : menableqinq: interface
#                           stre0 is not configured on
#                           scaqan04adm09.us.oracle.com
#    pbellary    01/23/25 - Bug 37506231 - EXACALE:CLUSTER PROVISIONING FAILING DUE TO EDV SERVICES STARTUP FAILURE
#    pbellary    01/21/25 - Bug 37501771 - EXASCALE: ASM PROVISIOING FAILED DUE TO EXISTING HCPOOL GRIDDISKS
#    rajsag      01/10/25 - 37463527 - exacc:bb:xs: 24.4.1 exacloud to support
#                           creating and updating vaults to match the available
#                           storage pool size
#    rajsag      12/06/24 - Enh 37363259 - exacs:exascale: update storage vlan
#                           in new cell during add cell operation
#    rajsag      11/28/24 - bug 37332438 - exacc:x11m:exascale: delete vault
#                           failed in exacloud [typerror: 'nonetype' object is
#                           not iterable] for the last db vault
#    abyayada    11/20/24 - 37304453 - STORAGE POOL SYNC ISSUE
#    rajsag      11/11/24 - Enh 37258868 - 24.3.2 exacloud: add storage pool
#                           info to create/update vault response payload
#    rajsag      11/07/24 - 37249835 - EXACC:EXASCALE: CONFIGURE EXASCALE FAILS
#                           IN EXACLOUD SANITY CHECKS AFTER QINQ SETUP / REBOOT
#                           DOM0S
#    rajsag      11/07/24 - enh 37255833 - exacc 24.3.2: exascale storage pool
#                           and vault size allocation need to account for high
#                           redundancy
#    rajsag      11/06/24 - 37249903 - exacc exascale:remove step 4 in xsconfig
#                           step list in exacloud
#    pbellary    26/19/24 - Bug 37220441 - EXASCALE: SKIP UPDATING CLOUD USER DURING ADD NODE
#    dekuckre    10/07/24 - 37133277: Update mUnRegisterACFS
#    rajsag      09/27/24 - ER 37107833 - exacc 24.3.2 : support exascale
#                           configuration on x8m/x9m/x10m base rack with 6
#                           physical disks per cell??
#    rajsag      09/23/24 - 37091441 - exacc gen2- exascale testing - xs config
#                           api returned success for validation failure
#    rajsag      09/05/24 - 36987178 - exacloud : capacity info return actual
#                           available exascale storage pool sizes and vaults
#                           info
#    pbellary    09/04/24 - Enh 36976333 - EXASCALE:ADD NODE CHANGES FOR EXASCALE CLUSTERS 
#    rajsag      08/28/24 - 36984040 - exacloud: celldisks need to be created
#                           if not already present in exascale config flow.
#    pbellary    08/27/24 - Bug 36992509 - MAIN:EXASCALE: ATTACHING INCORRECT VOLUME ID TO ACFS LEADS TO INCONSISTENT STATE
#    rajsag      08/26/24 - 36964589 - exacloud: exascale config flow to
#                           support validations on domu post dom0 reboot
#    pbellary    08/19/24 - Bug 36958015 - SETUP BONDING FAILING:CRITICAL EXCEPTION CAUGHT ['NONETYPE' OBJECT IS NOT ITERABLE] 
#    pbellary    08/12/24 - ENH 36945014 - CREATE AND BRING UP ACFS / MOUNT THE VOLUMES TOO ON THE DB VAULTS
#    pbellary    08/09/24 - Bug 36932003 - EXACLOUD SHOULD PATCH EXASCALE TAG FOR CONFIGURE EXASCALE 
#    rajsag      08/07/24 - enh 36894620 - exacc:24.3.2.0.0:exascale: define
#                           and create proper error codes mapping for exacloud
#                           exascale flow??
#    rajsag      08/02/24 - ER 36907966 - exacloud: exacloud to support undo
#                           operation for exascale config
#    pbellary    08/02/24 - Bug 36911874 - EXASCALE: CONFIGURE EXISTING INFRA TO USE EXASCALE - OEDA : OEDA STEP 3 FAILED
#    rajsag      08/01/24 - 36900535 - exacc:24.3.2.0.0:exascale:vault command
#                           should respond to size in integer and not float
#    rajsag      07/30/24 - 36894222 - EXACC:24.3.2.0.0:EXASCALE:VAULT
#                           CONFIGURE FAILED IN ECRA/EXACLOUD
#    rajsag      07/25/24 - 36883472 -
#                           exacc:bb:24.3.2.0.0:exascale:updatestoragepool
#                           failed due to code looking for vault details in xs
#                           config updatestoragepool payload
#    pbellary    07/02/24 - ENH 36690772 - EXACLOUD: IMPLEMENT PRE-VM STEPS FOR EXASCALE SERVICE
#    rajsag      06/24/24 - Enh 36603947 - exacloud : exascale storage pool
#                           resize operation
#    pbellary    06/21/24 - ENH 36690743 - EXACLOUD: IMPLEMENT OEDA STEPS FOR EXASCALE CREATE SERVICE
#    rajsag      06/14/24 - enh 36534545 - EXACLOUD : CONFIGURE EXASCALE
#                           SUPPORT IN EXACLOUD
#    rajsag      06/13/24 - 36603931 - EXACLOUD : EXASCALE DB VAULT CREATION
#                           SUPPORT36534554 - EXACLOUD : EXACLOUD CHANGES TO
#                           SUPPORT EXASCALE VAULT LCM OPERATIONS
#    pbellary    06/06/24 - ENH 36603820 - REFACTOR CREATE SERVICE FLOW FOR ASM/XS/EXADB-XS
#    pbellary    06/06/24 - Creation
#

import re
import os
import math
import json
import shlex
import socket
import itertools
import ipaddress
import subprocess
import time
import ipaddress
import defusedxml.ElementTree as ET
from tempfile import TemporaryDirectory
from exabox.exadbxs.edv import get_guest_edvs_from_cluster_xml, get_edvs_from_cluster_xml, update_edvs_from_cluster_xml
from exabox.ovm.cludomufilesystems import GIB, ebDomUFilesystem, get_max_domu_filesystem_sizes
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.ovm.csstep.cs_util import csUtil
from exabox.tools.ebTree.ebTree import ebTree
from exabox.core.DBStore import ebGetDefaultDB
from exabox.tools.oedacli import OedacliCmdMgr
from exabox.ovm.cluconfig import ebCluExascaleConfig
from exabox.ovm.clustorage import ebCluStorageConfig
from exabox.config.Config import ebCluCmdCheckOptions
from exabox.tools.ebOedacli.ebOedacli import ebOedacli
from exabox.ovm.csstep.cs_constants import csXSConstants, csXSEighthConstants
from tempfile import NamedTemporaryFile, TemporaryDirectory
from exabox.ovm.csstep.exascale.escli_util import ebEscliUtils
from exabox.core.Error import ebError, ExacloudRuntimeError, gReshapeError, gExascaleError
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogVerbose, ebLogTrace, ebLogCritical
from exabox.utils.node import connect_to_host, node_cmd_abs_path_check, node_exec_cmd, node_exec_cmd_check, node_read_text_file, node_write_text_file
from exabox.ovm.cludomufilesystems import shutdown_domu, start_domu
from exabox.utils.common import version_compare

DEVNULL = open(os.devnull, 'wb')
ACFS_VOL    = "/dev/exc/xacfsvol"
DEVICE_NAME = "xacfsvol"
CTRL_PORT   = "5052"
REDUNDANCY_FACTOR = 3.0
ATTR_AUTO_FILE_ENCRYPTION = "autoFileEncryption"

class ebExascaleUtils(object):

    def __init__(self, aCluCtrlObj):

        self.__cluctrl = aCluCtrlObj
        self.__escli = ebEscliUtils(self.__cluctrl)

    def mGetCluCtrl(self):
        return self.__cluctrl

    def mSetCluCtrl(self, aCluCtrl):
        self.__cluctrl = aCluCtrl

    def _mUpdateRequestData(self, rc, aData, err):
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

    def mUpdateDnsNtpServers(self, aHosts, aDnsList, aNtpList):
        _hosts = aHosts
        _dns_list = aDnsList
        _ntp_list = aNtpList
        _ebox = self.__cluctrl
        _uuid = _ebox.mGetUUID()
        _oeda_path  = _ebox.mGetOedaPath()
        _oedacli_bin = _oeda_path + '/oedacli'
        _savexmlpath = _oeda_path + '/exacloud.conf'
        _oedacli_mgr = OedacliCmdMgr( _oedacli_bin, _savexmlpath)

        _patchconfig = _ebox.mGetPatchConfig()
        if not os.path.exists(_savexmlpath):
            os.makedirs(_savexmlpath)
        _updatedxml = _savexmlpath + '/patched_ntp_dns_'  + _uuid + '.xml'
        _ebox.mExecuteLocal("/bin/cp {} {}".format(_patchconfig, _updatedxml))

        for _host in _hosts:
            _oedacli_mgr.mUpdateDnsNtpServers(_host, _updatedxml, _updatedxml, _dns_list, _ntp_list)
        _ebox.mSetPatchConfig(_updatedxml)
        ebLogInfo('ebExascaleUtils: Saved patched Cluster Config: ' + _ebox.mGetPatchConfig())

    def mConvertFromCIDRToNetmask(self, aCIDR):
        _cidr = aCIDR
        return str(ipaddress.IPv4Network('0.0.0.0/' + _cidr).netmask)

    def mParseStorageInterfaceAddress(self, aOutput):
        _output = aOutput
        _iface, _ipaddr, _netmask  = "", "", ""

        for _line in _output.splitlines():
            if _line and not _line.startswith(' '):  # Interface line
                _iface_match = re.match(r'\d+: ([^:]+):', _line)
                if _iface_match:
                    _iface = _iface_match.group(1)
            elif 'inet ' in _line:
                _inet_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)/(\d+)', _line)
                if _inet_match and _iface:
                   _ipaddr = _inet_match.group(1)
                   _cidr = _inet_match.group(2)
                _netmask = self.mConvertFromCIDRToNetmask(_cidr)
                ebLogInfo(f"Interface: {_iface} Ip Address: {_ipaddr} Netmask: {_netmask}")
        return _ipaddr, _netmask

    def mFetchStorageInterconnectIps(self, aDom0=None):
        _ebox = self.__cluctrl
        _dom0 = aDom0
        _storage_ip1, _storage_ip2, _netmask = "", "", ""

        with connect_to_host(_dom0, get_gcontext()) as _node:
            _cmd_str = "/usr/sbin/ip addr show stre0"
            _in, _out, _err = _node.mExecuteCmd(_cmd_str)
            _rc = int(_node.mGetCmdExitStatus())
            _output = None
            if _out:
                _output = _out.readlines()
                _result = ''.join(_output)
                _storage_ip1, _netmask = self.mParseStorageInterfaceAddress(_result)

            _cmd_str = "/usr/sbin/ip addr show stre1"
            _in, _out, _err = _node.mExecuteCmd(_cmd_str)
            _rc = int(_node.mGetCmdExitStatus())
            _output = None
            if _out:
                _output = _out.readlines()
                _result = ''.join(_output)
                _storage_ip2, _netmask = self.mParseStorageInterfaceAddress(_result)
        return _storage_ip1, _storage_ip2, _netmask

    def mPatchStorageInterconnctIps(self, aOptions, aDom0DomUList=None):
        _ebox = self.__cluctrl
        _utils = _ebox.mGetExascaleUtils()
        _patch_xml = False
        _oedacliCmds = []

        if aDom0DomUList:
            _dom0UList = aDom0DomUList
        else:
            _dom0UList = _ebox.mReturnDom0DomUPair()

        for _dom0, _ in _dom0UList:
            _dom0_mac =  _ebox.mGetMachines().mGetMachineConfig(_dom0)
            _net_list = _dom0_mac.mGetMacNetworks()
            _priv_host = []
            for _net in _net_list:
                _priv = _ebox.mGetNetworks().mGetNetworkConfig(_net)
                if _priv.mGetNetType() == 'private':
                    _priv_host.append(_priv.mGetNetHostName())
            _priv1 = _priv_host[0]
            _priv2 = _priv_host[1]
            _storage_ip1, _storage_ip2, _netmask = _utils.mFetchStorageInterconnectIps(aDom0=_dom0)
            if _storage_ip1 and _storage_ip2 and _netmask:
                _patch_xml = True
                _oedacliCmds.append(["ALTER NETWORK", {"INTERFACENAME": "stre0", "IP": _storage_ip1, "NETMASK": _netmask}, {"NETWORKHOSTNAME": _priv1}])
                _oedacliCmds.append(["ALTER NETWORK", {"INTERFACENAME": "stre1", "IP": _storage_ip2, "NETMASK": _netmask}, {"NETWORKHOSTNAME": _priv2}])

        if _patch_xml:
            # XS(Exascale) Service log
            _localprfx = 'log/xs_{0}'.format(_ebox.mGetUUID())
            _ebox.mExecuteLocal("/bin/mkdir -p {0}".format(_localprfx), aCurrDir=_ebox.mGetBasePath())

            # XML to be used
            _initialXml = "{0}/before_xs.xml".format(_localprfx)
            _updateXml = "{0}/after_xs.xml".format(_localprfx)

            _xmlTree = ebTree(_ebox.mGetPatchConfig())
            _xmlTree.mExportXml(_initialXml)

            # Declare/initilaice ebOedacli object
            _oedacli_bin = _ebox.mGetOedaPath() + '/oedacli'
            _oedacli = ebOedacli(_oedacli_bin, _localprfx, aLogFile="oedacli_xs.log")

            # Append command to ebOedacli object
            for _ocmd in _oedacliCmds:
                _oedacli.mAppendCommand(_ocmd[0], _ocmd[1], _ocmd[2], aForce=True)

            # Run command
            _oedacli.mRun(_initialXml, _updateXml)

            # Update XML to be used
            _xmlTree = ebTree(_updateXml)
            _xmlTree.mExportXml(_ebox.mGetPatchConfig())
            _ebox.mUpdateInMemoryXmlConfig(_ebox.mGetPatchConfig(), aOptions)

    def mEnableXSService(self, aOptions):
        ebLogInfo("*** mEnableXSService() >>>")
        _ebox = self.__cluctrl
        _escli = ebEscliUtils(self)
        _storage_intf_list, _cell_list, _ntp_list, _dns_list = [], [], [], []
        _exascale_name, _sre_hostname, _sre_ip, _hc_pool, _pool_size, _vault_name, _vault_size, _vlan_id = "", "", "", "", "", "", "", ""

        _redundancy_factor = 3 #setting redundancy factor to 3 
        _enable_xs_service = _ebox.mCheckConfigOption('enable_xs_service')
        if _enable_xs_service.lower() == "false":
            ebLogInfo('*** enable_xs_service flag is False. XS(Exascale) Service is disabled.')
            _ebox.mSetXS(False)
            return

        _xs_cluster = self.mCheckVaultTag()
        if _xs_cluster:
            _ebox.mSetXS(True)
            _ebox.mSetRemoteConfig(_ebox.mGetPatchConfig())
            ebLogInfo("*** XML is already patched with XS(Exascale) tag. Skipping Patching the XML.")
            return

        if aOptions is not None and aOptions.jsonconf is not None and "exascale" in list(aOptions.jsonconf.keys()):
            _exascale_attr = aOptions.jsonconf['exascale']
            if "exascale_cluster_name" in list(_exascale_attr.keys()):
                _exascale_name = _exascale_attr['exascale_cluster_name']
            if "ctrl_network" in list(_exascale_attr.keys()):
                _sre_hostname = _exascale_attr['ctrl_network']['name']
                _sre_ip = _exascale_attr['ctrl_network']['ip']
            if "storage_pool" in list(_exascale_attr.keys()):
                _hc_pool = _exascale_attr['storage_pool']['name']
                _pool_size = str(int(_exascale_attr['storage_pool']['gb_size'])*_redundancy_factor)+ 'GB'
            if "cell_list" in list(_exascale_attr.keys()):
                _cell_list = _exascale_attr['cell_list']
            if "db_vault" in list(_exascale_attr.keys()):
                _vault_name = _exascale_attr['db_vault']['name']
                _vault_size = str(int(_exascale_attr['db_vault']['gb_size'])*_redundancy_factor) + 'GB'
            if "storage_vlan_id" in list(_exascale_attr.keys()):
                _vlan_id = _exascale_attr['storage_vlan_id']
            if "host_nodes" in list(_exascale_attr.keys()):
                _storage_intf_list = _exascale_attr['host_nodes']
            if "network_services" in list(_exascale_attr.keys()):
                #
                # Update DNS/NTP values into inputxml
                #
                _network_services = _exascale_attr['network_services']
                if "ntp" in list(_exascale_attr['network_services'].keys()):
                    _ntp_list = _network_services['ntp']
                if "dns" in list(_exascale_attr['network_services'].keys()):
                    _dns_list = _network_services['dns']

        if _dns_list or _ntp_list:
            _dpairs = _ebox.mReturnDom0DomUPair()
            _dom0_list = [ _dom0 for _dom0 , _ in _dpairs]
            _hosts = _dom0_list + _cell_list
            self.mUpdateDnsNtpServers(_hosts, _dns_list, _ntp_list)

        # XS(Exascale) Service log
        _localprfx = 'log/xs_{0}'.format(_ebox.mGetUUID())
        _ebox.mExecuteLocal("/bin/mkdir -p {0}".format(_localprfx), aCurrDir=_ebox.mGetBasePath())

        # XML to be used
        _initialXml = "{0}/before_xs.xml".format(_localprfx)
        _updateXml = "{0}/after_xs.xml".format(_localprfx)

        _xmlTree = ebTree(_ebox.mGetPatchConfig())
        _xmlTree.mExportXml(_initialXml)

        #Patch XML with XS(Exascale) Service information
        _oedacli_bin = _ebox.mGetOedaPath() + '/oedacli'
        _oedacli = ebOedacli(_oedacli_bin, _localprfx, aLogFile="oedacli_xs.log")
        _oedacliCmds = []

        _inputjson = aOptions.jsonconf
        if _ebox.mGetCmd() in ["xsconfig"] and _inputjson and "config_op" in list(_inputjson.keys()) and _inputjson["config_op"] == "config":
            _exascale_tag = self.mCheckExascaleTag()
            if not _exascale_tag:
                ebLogInfo("exascale tag or exascale cluster name is not present in the input XML")
                _oedacliCmds.append(["ADD EXASCALECLUSTER", {"NAME": _exascale_name, "VIP": _sre_hostname, "IP": _sre_ip}, {}])
                _oedacliCmds.append(["ADD STORAGEPOOL", {"NAME": _hc_pool, "SIZE": _pool_size, "CELLLIST": "ALL"}, {}])
            else:
                ebLogInfo("exascale tag is present in the input XML")
                #Fetch the EGS clustername from XML
                _, _name = self.mGetExascaleName()
                _ctrl_ip, _ers = self.mGetCtrlIP()

                #For Enabling exascale operation, fetch the egs cluster name from input payload
                _egs_cluster_name = _exascale_name

                if _ers != _sre_hostname:
                    _oedacliCmds.append(["ALTER EXASCALECLUSTER", {"VIP": _sre_hostname}, {"NAME": _name}])
                if _ctrl_ip != _sre_ip:
                    _oedacliCmds.append(["ALTER EXASCALECLUSTER", {"IP": _sre_ip}, {"NAME": _name}])
                if _name != _egs_cluster_name:
                    _oedacliCmds.append(["ALTER EXASCALECLUSTER", {"NAME": _egs_cluster_name}, {"NAME": _name}])
        else:
            #After exascale operation is enabled, fetch the EGS clustername from cells
            _egs_cluster_name = self.mFetchESClusterName(_cell_list)
            if not _egs_cluster_name:
                _err_str = "Unable to fetch the egs clustername from the cells"
                raise ExacloudRuntimeError(aErrorMsg=_err_str)

            _exascale_tag = self.mCheckExascaleTag()
            if not _exascale_tag:
                ebLogInfo("exascale tag is not present in the input XML")
                _oedacliCmds.append(["ADD EXASCALECLUSTER", {"NAME": _egs_cluster_name, "VIP": _sre_hostname, "IP": _sre_ip}, {}])
                _oedacliCmds.append(["ADD STORAGEPOOL", {"NAME": _hc_pool, "SIZE": _pool_size, "CELLLIST": "ALL"}, {}])
            else:
                ebLogInfo("exascale tag is present in the input XML")
                #Fetch the EGS clustername from XML
                _, _name = self.mGetExascaleName()
                _ctrl_ip, _ers = self.mGetCtrlIP()

                if _ers != _sre_hostname:
                    _oedacliCmds.append(["ALTER EXASCALECLUSTER", {"VIP": _sre_hostname}, {"NAME": _name}])
                if _ctrl_ip != _sre_ip:
                    _oedacliCmds.append(["ALTER EXASCALECLUSTER", {"IP": _sre_ip}, {"NAME": _name}])
                if _name != _egs_cluster_name:
                    _oedacliCmds.append(["ALTER EXASCALECLUSTER", {"NAME": _egs_cluster_name}, {"NAME": _name}])

        _cell = _cell_list[0]
        _exadata_model_gt_X8 = False
        _exadata_model = _ebox.mGetNodeModel(aHostName=_cell)
        if _ebox.mCompareExadataModel(_exadata_model, 'X8') >= 0:
            _exadata_model_gt_X8 = True

        if _ebox.mGetStorageType() == "XS":
            _clusterName = _ebox.mGetClusters().mGetCluster().mGetCluName()
            if _escli.mIsEFRack(_cell) and _exadata_model_gt_X8:
                _oedacliCmds.append(["ADD VAULT", {"NAME": _vault_name, "EF": _vault_size}, {}])
            else:
                _oedacliCmds.append(["ADD VAULT", {"NAME": _vault_name, "HC": _vault_size}, {}])
            _oedacliCmds.append(["ALTER CLUSTER", {"VAULT": _vault_name}, {"CLUSTERNAME": _clusterName}])
        #Enable Q-in-Q vlan information to computes (dom0s) on XML
        _priv1, _priv2, _int1, _intf2  = "", "", "stre0", "stre1"
        if _ebox.mGetCmd() in ["xsconfig"] and  _inputjson and "config_op" in list(_inputjson.keys()) and _inputjson["config_op"] == "config":
            for _intf in _storage_intf_list:
                if "priv1" in list(_intf.keys()) and _intf['priv1']:
                   _priv1 = _intf['priv1']
                if "priv2" in list(_intf.keys()) and _intf['priv2']:
                    _priv2 = _intf['priv2']
                if "interface1" in list(_intf.keys()) and _intf['interface1']:
                    _intf1 = _intf['interface1']
                if "interface2" in list(_intf.keys()) and _intf['interface2']:
                    _intf2 = _intf['interface2']
                if "storage_ip1" in list(_intf.keys()) and _intf['storage_ip1'] and "storage_ip2" in list(_intf.keys()) and _intf['storage_ip2'] \
                    and "netmask" in list(_intf.keys()) and _intf['netmask']:
                    _netmask = _intf['netmask']
                    _storage_ip1 = _intf['storage_ip1']
                    _storage_ip2 = _intf['storage_ip2']
                if _vlan_id and _storage_ip1 and _priv1 and _storage_ip2 and _priv2 and _netmask:
                   _oedacliCmds.append(["ALTER NETWORK", {"VLANID": _vlan_id, "INTERFACENAME": _intf1, "IP": _storage_ip1, "NETMASK": _netmask}, {"NETWORKHOSTNAME": _priv1}])
                   _oedacliCmds.append(["ALTER NETWORK", {"VLANID": _vlan_id, "INTERFACENAME": _intf2, "IP": _storage_ip2, "NETMASK": _netmask}, {"NETWORKHOSTNAME": _priv2}])
        else:
            for _dom0, _ in _ebox.mReturnDom0DomUPair():
                _dom0_mac =  _ebox.mGetMachines().mGetMachineConfig(_dom0)
                _net_list = _dom0_mac.mGetMacNetworks()
                _priv_host = []
                for _net in _net_list:
                    _priv = _ebox.mGetNetworks().mGetNetworkConfig(_net)
                    if _priv.mGetNetType() == 'private':
                        _priv_host.append(_priv.mGetNetHostName())
                _storage_ip1, _storage_ip2, _netmask = self.mFetchStorageInterconnectIps(aDom0=_dom0)
                _priv1 = _priv_host[0]
                _priv2 = _priv_host[1]
                if _vlan_id and _storage_ip1 and _priv1 and _storage_ip2 and _priv2 and _netmask:
                    _oedacliCmds.append(["ALTER NETWORK", {"VLANID": _vlan_id, "INTERFACENAME": "stre0", "IP": _storage_ip1, "NETMASK": _netmask}, {"NETWORKHOSTNAME": _priv1}])
                    _oedacliCmds.append(["ALTER NETWORK", {"VLANID": _vlan_id, "INTERFACENAME": "stre1", "IP": _storage_ip2, "NETMASK": _netmask}, {"NETWORKHOSTNAME": _priv2}])

        for _ocmd in _oedacliCmds:
            _oedacli.mAppendCommand(_ocmd[0], _ocmd[1], _ocmd[2], aForce=True)

        _oedacli.mRun(_initialXml, _updateXml)

        # Update XML to be used
        _xmlTree = ebTree(_updateXml)
        _xmlTree.mExportXml(_ebox.mGetPatchConfig())
        _ebox.mUpdateInMemoryXmlConfig(_ebox.mGetPatchConfig(), aOptions)
        ebLogInfo('ebCluCtrl: Saved patched Cluster Config for DR (Updated DR slaves in xml): ' + _ebox.mGetPatchConfig())
        _ebox.mSetRemoteConfig(_ebox.mGetPatchConfig())

        if _ebox.mGetStorageType() == "XS":
            _ebox.mSetXS(True)
            #Fetch the cell list from the storagePool
            _ebox.mReturnCellNodes(aIsXS=True)
            ebLogInfo("*** XS(Exascale) Service is enabled.")

    def mPatchEGSClusterName(self, aOptions):
        _ebox = self.__cluctrl
        #Fetch the EGS clustername from XML
        _, _name = self.mGetExascaleName()

        #After exascale operation is enabled, fetch the EGS clustername from cells
        _egs_cluster_name = self.mFetchESClusterName()
        if not _egs_cluster_name:
            _err_str = "Unable to fetch the egs clustername from the cells"
            raise ExacloudRuntimeError(aErrorMsg=_err_str)

        if _name != _egs_cluster_name:
            ebLogInfo("Apply oedacli commands to XML")
            _uuid = _ebox.mGetUUID()
            _oeda_path = _ebox.mGetOedaPath()
            _patchconfig = _ebox.mGetPatchConfig()
            _savexmlpath = _oeda_path + '/exacloud.conf'
            _updatedxml = _savexmlpath + '/exascale_' + _uuid + '.xml'

            _ebox.mExecuteLocal("/bin/mkdir -p {0}".format(_savexmlpath), aCurrDir=_ebox.mGetBasePath())
            _ebox.mExecuteLocal("/bin/cp {0} {1}".format(_patchconfig, _updatedxml), aCurrDir=_ebox.mGetBasePath())

            _oedacli_bin = os.path.join(_oeda_path, 'oedacli')
            with TemporaryDirectory() as tmp_dir:
                _oedacli_mgr = OedacliCmdMgr(_oedacli_bin, tmp_dir)
                _oedacli_mgr.mUpdateEGSClusterName(_updatedxml, _updatedxml, _name, _egs_cluster_name)
            _ebox.mUpdateInMemoryXmlConfig(_updatedxml, aOptions)
            ebLogInfo('ebCluCtrl: Saved patched Cluster Config: ' + _ebox.mGetPatchConfig())

    def mParseQinQHostInfo(self, aHostList, aComputeHost):
        """Fetches a host dictionary by its compute hostname from the input payload"""
        _host_list = aHostList
        _compute_host = aComputeHost
        for _host in _host_list:
            if _host['compute_hostname'] == _compute_host:
                return _host
        return None

    def mEnableEDVProperty(self, aOptions):
        _ebox = self.__cluctrl
        _oeda_path = _ebox.mGetOEDARequestsPath()
        if self.mIsEDVImageSupported(aOptions):
            _oeda_properties_path = os.path.join(_oeda_path, 'properties', 'es.properties')
            _cmd_str = f"/bin/sed 's/^FORCEEXCCLOUD=false/FORCEEXCCLOUD=true/' -i {_oeda_properties_path}"
            _ebox.mExecuteLocal(_cmd_str, aStdOut=DEVNULL, aStdErr=DEVNULL, aCurrDir=_oeda_path)
        else:
            ebLogInfo(f"ebExascaleUtils: EDV Image is not Supported")

    def mIsEDVImageSupported(self, aOptions):
        _ebox = self.__cluctrl
        _edv_image_support = "false"
        _status = False

        if _ebox.mIsKVM() and _ebox.mCheckConfigOption("xs_edv_enable", "True") \
            and aOptions is not None and aOptions.jsonconf is not None:
            _inputjson = aOptions.jsonconf
            if _inputjson and 'rack' in _inputjson.keys() and 'xsVmImage' in _inputjson['rack'].keys():
                _edv_image_support = _inputjson['rack']['xsVmImage']

        _status = True if _edv_image_support.lower() == "true" else False
        ebLogInfo(f"EDV Image Supported:{_status}")
        return _status

    def mPatchEDVVolumes(self, aOptions):
        _ebox = self.__cluctrl
        _options = aOptions
        _edv_image_support = ""
        _vault_name = ""
        _vault_type = ""
        _inputjson = aOptions.jsonconf

        if _inputjson and 'rack' in _inputjson.keys() and 'xsVmImage' in _inputjson['rack'].keys():
            _edv_image_support = _inputjson['rack']['xsVmImage']
            if "system_vault" in _inputjson['rack'].keys():
                _system_vault_list = aOptions.jsonconf["rack"]['system_vault']
                for _vault_list in _system_vault_list:
                    _vault_type = _vault_list['vault_type']
                    if _vault_type and _vault_type.lower() == "image":
                        _vault_name = _vault_list['name']
                        break
 
        if _ebox.mIsKVM() and _edv_image_support and _edv_image_support.lower() == "true" and _vault_name \
            and _vault_type and _vault_type.lower() == "image":
            _oeda_path  = _ebox.mGetOedaPath()
            _ebox.mExecuteCmd('/bin/mkdir -p '+ _oeda_path +'/exacloud.conf')
            _oedacli_bin = _oeda_path + '/oedacli'
            _savexmlpath = _oeda_path + '/exacloud.conf'
            _oedacli_mgr = OedacliCmdMgr( _oedacli_bin, _savexmlpath)

            _uuid = _ebox.mGetUUID()
            _patchconfig = _ebox.mGetPatchConfig()
            _updatedxml = _oeda_path + '/exacloud.conf/patched_edv_volumes_'  + _uuid + '.xml'

            _ebox.mExecuteLocal("/bin/cp {} {}".format(_patchconfig, _updatedxml))

            _oedacli_mgr.mUpdateEDVVolumes(_patchconfig, _updatedxml, "celldisk", "edv", _vault_name, "guest")

            # Update EDV sizes in XML
            _xml = ebTree(_updatedxml)
            _edvs = get_edvs_from_cluster_xml(_xml)
            _fs_sizes = {
                ebDomUFilesystem.ROOT: 15 * GIB,
                ebDomUFilesystem.U01: 20 * GIB,
                ebDomUFilesystem.HOME: 4 * GIB,
                ebDomUFilesystem.TMP: 3 * GIB,
                ebDomUFilesystem.VAR: 2 * GIB,
                ebDomUFilesystem.VAR_LOG: 18 * GIB,
                ebDomUFilesystem.VAR_LOG_AUDIT: 1 * GIB,
                ebDomUFilesystem.CRASHFILES: 20 * GIB,
                ebDomUFilesystem.GRID: 50 * GIB
            }
            _fs_sizes.update(get_max_domu_filesystem_sizes(_ebox, use_defaults=True))
            _sys_edv_size_bytes = \
                _fs_sizes[ebDomUFilesystem.ROOT] * 2 + \
                _fs_sizes[ebDomUFilesystem.HOME] + \
                _fs_sizes[ebDomUFilesystem.TMP] + \
                _fs_sizes[ebDomUFilesystem.VAR] * 2 + \
                _fs_sizes[ebDomUFilesystem.VAR_LOG] + \
                _fs_sizes[ebDomUFilesystem.VAR_LOG_AUDIT] + \
                _fs_sizes[ebDomUFilesystem.CRASHFILES] + \
                22 * GIB
                # 16G of LVDbSwap1 +
                # 2G of LVDoNotRemoveOrUse +
                # 2G of Free VG reserved size +
                # 1G of /boot and grub partitions +
                # 1G of buffer (like partition table headers)
            _u01_edv_size_bytes = _fs_sizes[ebDomUFilesystem.U01] + 2 * GIB
            _grid_edv_size_bytes = _fs_sizes[ebDomUFilesystem.GRID] + 2 * GIB
            for _edv_id, _edv_info in _edvs.items():
                _edvs[_edv_id] = _edv_info._replace(size_bytes=\
                    _sys_edv_size_bytes if _edv_info.vol_type.upper() == 'BASEVOL' \
                    else _u01_edv_size_bytes if _edv_info.vol_type.upper() == 'USERVOL' \
                    else _grid_edv_size_bytes if _edv_info.vol_type.upper() == 'GRIDVOL' \
                    else _edv_info.size_bytes
                )
            update_edvs_from_cluster_xml(_xml, _edvs)
            _xml.mExportXml(_updatedxml)

            _ebox.mSetPatchConfig(_updatedxml)
            _patchconfig = _ebox.mGetPatchConfig()
            _remotconfig = _ebox.mGetRemoteConfig()
            _ebox.mUpdateInMemoryXmlConfig(_patchconfig, aOptions)
            ebLogInfo('ebCluCtrl: Saved patched Cluster Config: ' + _patchconfig)
            _ebox.mCopyFile(_patchconfig, _remotconfig)
        else:
            ebLogInfo("xsVmImage flag disabled in input payload")

    def mIsEDVBackupSupported(self, aOptions):
        _ebox = self.__cluctrl
        _edv_backup_support = "false"
        _status = False

        if _ebox.mIsKVM() and _ebox.mCheckConfigOption("xs_edv_enable", "True") \
            and aOptions is not None and aOptions.jsonconf is not None:
            _inputjson = aOptions.jsonconf
            if _inputjson and 'rack' in _inputjson.keys() and 'xsVmBackup' in _inputjson['rack'].keys():
                _edv_backup_support = _inputjson['rack']['xsVmBackup']

        _status = True if _edv_backup_support.lower() == "true" else False
        ebLogInfo(f"EDV Backup Supported:{_status}")
        return _status

    def mGetImageBackupVault(self, aOptions):
        _inputjson = aOptions.jsonconf
        _image_vault = ""
        _backup_vault = ""
        if _inputjson and 'rack' in _inputjson.keys() and 'xsVmImage' in _inputjson['rack'].keys():
            _edv_image_support = _inputjson['rack']['xsVmImage']
            if _edv_image_support and "system_vault" in _inputjson['rack'].keys():
                _system_vault_list = aOptions.jsonconf["rack"]['system_vault']
                for _vault_list in _system_vault_list:
                    _vault_type = _vault_list['vault_type']
                    if _vault_type and _vault_type.lower() == "image":
                        _image_vault = _vault_list['name']
                        ebLogInfo(f"Image Vault: {_image_vault}")
                        break
        if _inputjson and 'rack' in _inputjson.keys() and 'xsVmBackup' in _inputjson['rack'].keys():
            _edv_backup_support = _inputjson['rack']['xsVmBackup']
            if _edv_backup_support and "system_vault" in _inputjson['rack'].keys():
                _system_vault_list = aOptions.jsonconf["rack"]['system_vault']
                for _vault_list in _system_vault_list:
                    _vault_type = _vault_list['vault_type']
                    if _vault_type and _vault_type.lower() == "backup":
                        _backup_vault = _vault_list['name']
                        ebLogInfo(f"Backup Vault: {_backup_vault}")
                        break
        return _image_vault, _backup_vault

    def mWriteVMBackupJson(self, aData, aRemoteFile, aDom0=None, aOverWrite=False):
        _data = aData
        _remoteFileName = aRemoteFile
        _dom0 = aDom0

        _remote_path = get_gcontext().mGetConfigOptions().get("vmbackup", {}).get(
            "vmbackup_conf_dir", "/opt/oracle/vmbackup/conf/")
        if not _remote_path:
            _remote_path = "/opt/oracle/vmbackup/conf/"

        _json_object = json.dumps(_data, indent=4)
        with NamedTemporaryFile(mode='w', delete=True) as _tmp_file:
            _tmp_file.write(_json_object)
            _tmp_file.flush()
            with connect_to_host(_dom0, get_gcontext()) as _node:
                #check if vmbackup conf dir exists
                if _node.mFileExists(_remote_path) is False:
                    _node.mExecuteCmdLog(f"/bin/mkdir -p {_remote_path}")
                if aOverWrite and _node.mFileExists(_remoteFileName):
                    _node.mExecuteCmdLog(f"/bin/rm -rf {_remoteFileName}")
                _node.mCopyFile(_tmp_file.name, _remoteFileName)

    def mMigrateVMbackupJson(self, aOptions, aDom0DomUList=None):
        _ebox = self.__cluctrl
        _escli = self.__escli
        if aDom0DomUList:
            _dom0UList = aDom0DomUList
        else:
            _dom0UList = _ebox.mReturnDom0DomUPair()

        _remote_path = get_gcontext().mGetConfigOptions().get("vmbackup", {}).get(
            "vmbackup_conf_dir", "/opt/oracle/vmbackup/conf/")
        if not _remote_path:
            _remote_path = "/opt/oracle/vmbackup/conf/"

        _ctrl_ip, _ctrl_port = _escli.mGetERSEndpoint(aOptions)
        _, _backup_vault = self.mGetImageBackupVault(aOptions)
        for _dom0, _domU in _dom0UList:
            _file_name = _domU + ".json"
            _remoteFileName = os.path.join(_remote_path, _file_name)
            with connect_to_host(_dom0, get_gcontext()) as _node:
                #Create VM.json file if it is not existing
                if not _node.mFileExists(_remoteFileName):
                    _data = self.mGenerateVMbackupJson(aOptions)
                    self.mWriteVMBackupJson(_data, _remoteFileName, aDom0=_dom0)

                #Migrate VMBackup to exascale
                _data = _node.mReadFile(_remoteFileName)
                _data = json.loads(_data)
                _data["backup_type"] =  "Exascale"
                _data["exascale_backup_vault"] = _backup_vault
                _data["exascale_ers_ip_port"] = f"{_ctrl_ip}:{_ctrl_port}"
                self.mWriteVMBackupJson(_data, _remoteFileName, aDom0=_dom0)

    def mGenerateVMbackupJson(self, aOptions):
        _escli = self.__escli
        _data = {}

        _ctrl_ip, _ctrl_port = _escli.mGetERSEndpoint(aOptions)
        _image_vault, _backup_vault = self.mGetImageBackupVault(aOptions)
        if self.mIsEDVBackupSupported(aOptions) and self.mIsEDVImageSupported(aOptions):
            ebLogInfo(f"Creating VMBackup Json file with EDV Image & EDV backup support")
            # Exascale backups + EDV VM images
            _data = {
                "backup_type" : "Exascale",
                "exascale_backup_vault" : _backup_vault,
                "source_vm_images" : "Exascale",
                "exascale_images_vault" : _image_vault,
                "exascale_retention_num" : 2,
                "exascale_ers_ip_port"      : f"{_ctrl_ip}:{_ctrl_port}"
            }
        elif self.mIsEDVImageSupported(aOptions):
            ebLogInfo(f"Creating VMBackup Json file with EDV Image & Local FS backup support")
            # Local FS backups + EDV VM images
            _data = {
                "backup_type" : "Legacy",
                "exascale_backup_vault" : "",
                "source_vm_images" : "Exascale",
                "exascale_images_vault" : _image_vault,
                "exascale_retention_num" : 2,
                "exascale_ers_ip_port"      : f"{_ctrl_ip}:{_ctrl_port}"
            }
        elif self.mIsEDVBackupSupported(aOptions):
            ebLogInfo(f"Creating VMBackup Json file with EDV backup & Local FS Image support")
            # Exascale backups + Local FS VM images
            _data = {
                "backup_type" : "Exascale",
                "exascale_backup_vault" : _backup_vault,
                "source_vm_images" : "Legacy",
                "exascale_images_vault" : "",
                "exascale_retention_num" : 2,
                "exascale_ers_ip_port"      : f"{_ctrl_ip}:{_ctrl_port}"
            }
        else:
            ebLogInfo(f"Creating VMBackup Json file with Local FS backup & Local FS Image support")
            # Local FS backups + Local FS VM images
            _data = {
                "backup_type" : "Legacy",
                "exascale_backup_vault" : "",
                "source_vm_images" : "Legacy",
                "exascale_images_vault" : "",
                "exascale_retention_num" : 2,
                "exascale_ers_ip_port"      : ":"
            }
        return _data

    def mCreateVMbackupJson(self, aOptions, aDom0DomUList=None):
        _ebox = self.__cluctrl
        if aDom0DomUList:
            _dom0UList = aDom0DomUList
        else:
            _dom0UList = _ebox.mReturnDom0DomUPair()

        _remote_path = get_gcontext().mGetConfigOptions().get("vmbackup", {}).get(
            "vmbackup_conf_dir", "/opt/oracle/vmbackup/conf/")
        if not _remote_path:
            _remote_path = "/opt/oracle/vmbackup/conf/"

        _data = self.mGenerateVMbackupJson(aOptions)
        for _dom0, _domU in _dom0UList:
            _file_name = _domU + ".json"
            _remoteFileName = os.path.join(_remote_path, _file_name)
            self.mWriteVMBackupJson(_data, _remoteFileName, aDom0=_dom0, aOverWrite=True)

    def mRemoveVMbackupJson(self, aOptions, aDom0DomUList=None):
        _ebox = self.__cluctrl

        if aDom0DomUList:
            _dom0UList = aDom0DomUList
        else:
            _dom0UList = _ebox.mReturnDom0DomUPair()

        _remote_path = get_gcontext().mGetConfigOptions().get("vmbackup", {}).get(
            "vmbackup_conf_dir", "/opt/oracle/vmbackup/conf/")
        if not _remote_path:
            _remote_path = "/opt/oracle/vmbackup/conf/"

        for _dom0, _domU in _dom0UList:
            _file_name = _domU + ".json"
            _remoteFileName = os.path.join(_remote_path, _file_name)
            with connect_to_host(_dom0, get_gcontext()) as _node:
                if _node.mFileExists(_remoteFileName):
                    ebLogInfo(f"Removing VMBackup Json file from {_dom0}")
                    _node.mExecuteCmdLog(f"/bin/rm -rf {_remoteFileName}")

    def mCreateVMbackupNodesConf(self, aOptions, aDom0DomUList=None):
        _ebox = self.__cluctrl
        _nodes_conf = "nodes.conf"
        _nodes = {}

        if aDom0DomUList:
            _dom0UList = aDom0DomUList
        else:
            _dom0UList = _ebox.mReturnDom0DomUPair()

        _remote_path = get_gcontext().mGetConfigOptions().get("vmbackup", {}).get(
            "vmbackup_conf_dir", "/opt/oracle/vmbackup/conf/")
        if not _remote_path:
            _remote_path = "/opt/oracle/vmbackup/conf/"

        _remoteNodesFile = os.path.join(_remote_path, _nodes_conf)
        _dom0_list = [_dom0.split('.')[0] for _dom0, _ in _dom0UList]
        _nodes["dbnodes"] = _dom0_list
        _dbnode_object = json.dumps(_nodes, indent=4)
        with NamedTemporaryFile(mode='w', delete=True) as _tmp_file:
            _tmp_file.write(_dbnode_object)
            _tmp_file.flush()
            for _dom0, _ in _dom0UList:
                try:
                    _node = exaBoxNode(get_gcontext())
                    _node.mConnect(aHost=_dom0)
                    #check if vmbackup conf dir exists
                    if _node.mFileExists(_remote_path) is False:
                        _node.mExecuteCmdLog(f"/bin/mkdir -p {_remote_path}")
                    if _node.mFileExists(_remoteNodesFile):
                        _node.mExecuteCmdLog(f"/bin/rm -rf {_remoteNodesFile}")
                    ebLogInfo(f"Creating VMBackup nodes.conf on {_dom0}")
                    _node.mCopyFile(_tmp_file.name, _remoteNodesFile)
                finally:
                    _node.mDisconnect()

    def mConfigureEDVbackup(self, aOptions, aDom0DomUList=None):
        _ebox = self.__cluctrl

        if aDom0DomUList:
            _dom0UList = aDom0DomUList
        else:
            _dom0UList = _ebox.mReturnDom0DomUPair()

        self.mCreateVMbackupJson(aOptions, aDom0DomUList=_dom0UList)

        return 0

    #Method Returns Vault Name based on the VaultType
    #If VaultType = image, return image vault
    #If VaultType = backup, return backup vault
    # When No vault vaultType specified, return dbVault
    def mGetVaultName(self, aOptions, aVaultType=None):
        _ebox = self.__cluctrl
        _escli = self.__escli
        _options = aOptions
        _vault_name = ""
        _inputjson = aOptions.jsonconf
        if aVaultType == "image":
            if _inputjson and 'rack' in _inputjson.keys() and 'xsVmImage' in _inputjson['rack'].keys():
                _edv_image_support = _inputjson['rack']['xsVmImage']
                if "system_vault" in _inputjson['rack'].keys():
                    _system_vault_list = aOptions.jsonconf["rack"]['system_vault']
                    for _vault_list in _system_vault_list:
                        _vault_type = _vault_list['vault_type']
                        if _vault_type and _vault_type.lower() == "image":
                            _vault_name = _vault_list['name']
                            ebLogInfo(f"Image Vault: {_vault_name}")
                            break
        elif aVaultType == "backup":
            if _inputjson and 'rack' in _inputjson.keys() and 'xsVmBackup' in _inputjson['rack'].keys():
                _edv_image_support = _inputjson['rack']['xsVmBackup']
                if "system_vault" in _inputjson['rack'].keys():
                    _system_vault_list = aOptions.jsonconf["rack"]['system_vault']
                    for _vault_list in _system_vault_list:
                        _vault_type = _vault_list['vault_type']
                        if _vault_type and _vault_type.lower() == "backup":
                            _vault_name = _vault_list['name']
                            ebLogInfo(f"Backup Vault: {_vault_name}")
                            break
        else:
            _vault_name = _escli.mGetDBVaultName()

        return _vault_name

    def mRemoveVmMachines(self, aOptions):
        """
        This method removes from the XML the KVM Guest machines
        """
        _ebox = self.__cluctrl
        _uuid = _ebox.mGetUUID()
        _oeda_path = _ebox.mGetOedaPath()
        _patchconfig = _ebox.mGetPatchConfig()
        _savexmlpath = _oeda_path + '/exacloud.conf'
        _xsconfigxml = _savexmlpath + '/xsconfig_' + _uuid + '.xml'

        _ebox.mExecuteLocal("/bin/mkdir -p {0}".format(_savexmlpath), aCurrDir=_ebox.mGetBasePath())
        _ebox.mExecuteLocal("/bin/cp {0} {1}".format(_patchconfig, _xsconfigxml), aCurrDir=_ebox.mGetBasePath())

        _oedacli_bin = os.path.join(_oeda_path, 'oedacli')
        with TemporaryDirectory() as tmp_dir:
            _oedacli_mgr = OedacliCmdMgr(_oedacli_bin, tmp_dir)
            for _dom0, _domU in _ebox.mReturnDom0DomUPair():
                _oedacli_mgr.mDelNode(_domU, None, aSrcXml=_xsconfigxml, aDestXml=_xsconfigxml, aDeploy=False)
        _ebox.mUpdateInMemoryXmlConfig(_xsconfigxml, aOptions)
        _ebox.mSetRemoteConfig(_ebox.mGetPatchConfig())

    def mCheckExascaleTag(self):
        _xs_cluster = False
        _ebox = self.__cluctrl
        _patchconfig = _ebox.mGetPatchConfig()
        if _patchconfig and os.path.exists(_patchconfig):
            _it = ET.iterparse(_patchconfig)
            for _, _el in _it:
                _, _, _el.tag = _el.tag.rpartition('}')
            _root = _it.root
            for _child in _root:
                if _child.tag == "exascale":
                    _xs_cluster = True
                    break
        if _xs_cluster:
            _, _name= self.mGetExascaleName()
            if not _name:
                _xs_cluster = False
        return _xs_cluster

    def mGetExascaleName(self):
        _exascale_id, _clusterName = "", ""
        _ebox = self.__cluctrl
        _config = _ebox.mGetConfig()
        _exascale_config = ebCluExascaleConfig(_config)
        _config_list = _exascale_config.mGetExascaleClusterConfigList()
        if _config_list:
            _exascale_id = _config_list[0]
            _exascale = _exascale_config.mGetExascaleClusterConfig(_exascale_id)
            _clusterName = _exascale.mGetClusterName()

        ebLogInfo(f"Exascale ID: {_exascale_id} Exascale clusterName:{_clusterName}")
        return _exascale_id, _clusterName

    def mFetchESClusterName(self, aCellList=None):
        _ebox = self.__cluctrl
        _egs_clusterName = ""

        if aCellList:
            _cell_list = aCellList
        else:
            _cell_list = _ebox.mReturnCellNodes().keys()

        for _cell_name in _cell_list:
            with connect_to_host(_cell_name, get_gcontext()) as _node:
                _cmd_str = "/bin/cat $OSSCONF/egs/excloudinit.ora | /bin/grep exc_egs_cluster_name"
                _in, _out, _err = _node.mExecuteCmd(_cmd_str)
                _rc = int(_node.mGetCmdExitStatus())
                _output = None
                if _rc !=0:
                    ebLogError(f"Failed to get the EGS Cluster name from cell:{_cell_name}")
                    continue
                if _out:
                    _output = _out.readlines()
                    _egs_clusterName = _output[0].split('=')[1].strip()
                    ebLogInfo(f"EGS Cluster name on cell:{_cell_name}: {_egs_clusterName}")
                    break
        return _egs_clusterName

    def mCheckVaultTag(self):
        _xs_cluster = False
        _ebox = self.__cluctrl
        _patchconfig = _ebox.mGetPatchConfig()
        if _patchconfig and os.path.exists(_patchconfig) and not _ebox.mIsClusterLessXML():
            with open(_patchconfig) as _xmlfile:
                _data = _xmlfile.read()

            _root = ET.fromstring(re.sub('xmlns="\w*"', '', _data))
            _clusters = _root.find("software/clusters/cluster")
            for _cluster in _clusters:
                if _cluster.tag == "vault":
                    _vault_id = _cluster.get('id')
                    ebLogInfo(f"VAULT ID: {_vault_id}")
                    _xs_cluster = True
                    break
        return _xs_cluster

    def mGetCtrlIP(self):
        _ipaddress = ""
        _ebox = self.__cluctrl
        _config = ebCluExascaleConfig(_ebox.mGetConfig())
        _config_list = _config.mGetExascaleClusterConfigList()
        _exascale = _config.mGetExascaleClusterConfig(_config_list[0])
        _net_list = _exascale.mGetMacNetworks()
        for _net_id in _net_list:
            _net_conf = _ebox.mGetNetworks().mGetNetworkConfig(_net_id)
            _ipaddress = _net_conf.mGetNetIpAddr()
            _ers = _net_conf.mGetNetHostName() + "." +  _net_conf.mGetNetDomainName()
        return _ipaddress, _ers

    def mParseXMLForXS(self):
        """
        Parse XML to identify if the cluster is XS or not
        """
        _xs_cluster = False
        _ebox = self.__cluctrl
        _enable_xs_service = "false"
        _enable_xs_service = _ebox.mCheckConfigOption('enable_xs_service')
        if _enable_xs_service.lower() == "false":
            ebLogInfo('*** enable_xs_service flag is False. XS(Exascale) Service is disabled.')
            _ebox.mSetXS(False)
            return

        _xs_cluster = self.mCheckVaultTag()
        if not _xs_cluster:           
            _err_msg = "INVALID XML: vault tag is missing in input XML"
            ebLogError('*** ' + _err_msg)
            _ebox.mUpdateErrorObject(gExascaleError["INVALID_INPUT_PARAMETER"], _err_msg)
            raise ExacloudRuntimeError(0x0741, 0xA, _err_msg)

    def mDoVaultOp(self,aOptions):
        """
        function to decide which CRUD operation to run 
        """
        ebLogInfo("*** mDoVaultOp")
        _rc=-1
        _ebox = self.__cluctrl
        _options = aOptions
        _inputjson = _options.jsonconf
        _enable_xs_service = "false"
        _enable_xs_service = self.__cluctrl.mCheckConfigOption('enable_xs_service')
        if _enable_xs_service.lower() == "false":
            _err_msg= "enable_xs_service flag is set to False. XS(Exascale) Service is disabled."
            self.__cluctrl.mSetXS(False)
            _ebox.mUpdateErrorObject(gExascaleError["ERROR_XS_DISABLED"], _err_msg)
            ebLogError(_err_msg)
            return _rc

        if not _inputjson:
            _err_msg='mDoVaultOp params missing'
            ebLogError("*** " + _err_msg)
            _ebox.mUpdateErrorObject(gExascaleError["INVALID_INPUT_PARAMETER"], _err_msg)
            return _rc
        
        if "db_vaults" in list(_inputjson.keys()) and "system_vaults" in list(_inputjson.keys()) and _inputjson["vault_op"] == "get":
            return self.mGetAllVaults(_options)

        if "db_vault" in list(_inputjson.keys()) or  "db_vaults" in list(_inputjson.keys()):
            if _inputjson["vault_op"] == "create":
                return self.mCreateDbVault(_options)
            elif _inputjson["vault_op"] == "delete":
                return self.mDeleteDbVault(_options)
            elif _inputjson["vault_op"] == "update":
                return self.mUpdateDbVault(_options)
            elif _inputjson["vault_op"] == "get":
                return self.mGetDbVault(_options)
            else:
                _err_msg = f'Invalid DBVault operation {(_inputjson["vault_op"])}'
                _ebox.mUpdateErrorObject(gExascaleError["INVALID_EXASCALE_OPERATION"], _err_msg)
                return _rc
            
        if "system_vault" in list(_inputjson.keys()):
            if _inputjson["vault_op"] == "create":
                return self.mCreateSysVault(_options)
            elif _inputjson["vault_op"] == "delete":
                return self.mDeleteSysVault(_options)
            elif _inputjson["vault_op"] == "update":
                return self.mUpdateSysVault(_options)
            else:
                _err_msg = f'Invalid DBVault operation {(_inputjson["vault_op"])}'
                _ebox.mUpdateErrorObject(gExascaleError["INVALID_EXASCALE_OPERATION"], _err_msg)
                return _rc


    # function to create DB vault
    def mCreateDbVault(self, aOptions):
        """
        function to create DB vault
        input: 1. vaultOcid 2. cells [ ] 3. vault size in GB 4. vault name 5. ctrl IP 6. Port details
        response : 1. vaultOcid 2. VaultName 3. VaultSize in GB 4. VaultRefId 5. totalStorageGB 6. usedStorageGB
        """
        ebLogInfo("*** mCreateDbVault")
        _data_d = {}
        _errString = None
        _ret = -1
        _ebox = self.__cluctrl
        _escli = self.__escli
        _options = aOptions
        _inputjson = _options.jsonconf
        _cell_list = _inputjson['cell_list']
        _cell = _cell_list[0]
        _vaultName = _inputjson['db_vault']['name']
        _poolName = _inputjson['storage_pool']
        _vaultSize = str(_inputjson['db_vault']['gb_size'])

        #List Vault
        _ret, _out, _err = _escli.mListVault(_cell, _vaultName, aOptions)
        if _ret == 0:
            _msg = f'Unable to Create DBVault {_vaultName} as it already exists. error detail:{_err} output:{_out}'
            ebLogError(_msg)
            _ebox.mUpdateErrorObject(gExascaleError["VAULT_CREATION_FAILED"], _msg)
            self._mUpdateRequestData(-1,_data_d,_msg)
            raise ExacloudRuntimeError(0x0811, 0xA, _msg)
        _vaultSizeWithRedundancy = int(int(_vaultSize) * REDUNDANCY_FACTOR)

        #Check if the rack is Extreme Flash
        _ef_rack, _suffix = (True, "EF") if _escli.mIsEFRack(_cell) else (False, "HC")

        #Create Vault
        _ret, _out, _err = _escli.mCreateVault(_cell, _ef_rack, _vaultName, _vaultSizeWithRedundancy, aOptions)
        if _ret != 0:
            _msg = f'Unable to Create DBVault {_vaultName} of size {_vaultSize}GB due to error:{_err} output:{_out}'
            ebLogError(_msg)
            _ebox.mUpdateErrorObject(gExascaleError["VAULT_CREATION_FAILED"], _msg)
            self._mUpdateRequestData(-1,_data_d,_msg)
            raise ExacloudRuntimeError(0x0811, 0xA, _msg)
        else:
            _vault = {}
            _json = ''.join( _out.splitlines())
            if _json[0] == '{':
                _jsonOut = json.loads(_json)
                _vault["vault_ocid"]= _inputjson['db_vault']['vault_ocid']
                _vault["name"]= _vaultName
                _vault["ref_id"]= _jsonOut["data"]["id"]
                _totalStorage = float(float(_jsonOut["data"]["attributes"][f"spaceProv{_suffix}"])/(1024*1024*1024))/REDUNDANCY_FACTOR
                _vault["total_storage_gb"]= math.floor(_totalStorage)
                _usedSpace = int(_jsonOut["data"]["attributes"][f"spaceUsed{_suffix}"])
                if _usedSpace > 0:
                    _usedSpace= float(_jsonOut["data"]["attributes"][f"spaceUsed{_suffix}"])/(1024*1024*1024)/REDUNDANCY_FACTOR
                _vault["used_storage_gb"]= math.ceil(_usedSpace)
            _data_d["db_vault"] = _vault
        _data_d["storage_pool"] = self.mGetStoragePoolDetails(_cell, _poolName, aOptions)    
        ebLogInfo(f'mCreateDbVault: Vault Created')
        self._mUpdateRequestData(_ret,_data_d,"")
        return _ret
    
    # function to delete DB vault 
    def mDeleteDbVault(self, aOptions):
        """
        function to delete DB vault 
        input: 1. vaultOcid 2. cells [ ] 3. vault name 4. ctrl IP 5. Port details
        """
        ebLogInfo("*** mDeleteDbVault")
        _data_d = {}
        _errString = None
        _ret = -1
        _ebox = self.__cluctrl
        _escli = self.__escli
        _options = aOptions
        _inputjson = _options.jsonconf
        _cell_list = _inputjson['cell_list']
        _cell = _cell_list[0]
        _vaultName = _inputjson['db_vault']['name']
        _poolName = _inputjson['storage_pool']

        _ret, _out, _err = _escli.mListVault(_cell, _vaultName, aOptions)
        if _ret == 0:
            _ret, _out, _err = _escli.mRemoveVault(_cell, _vaultName, aOptions)
            if _ret != 0:
                _msg = f'Unable to Delete DBVault {_vaultName} due to error: {_err} output:{_out}'
                ebLogError(_msg)
                _ebox.mUpdateErrorObject(gExascaleError["VAULT_DELETION_FAILED"], _msg)
                self._mUpdateRequestData(_ret,_data_d,_msg)
                raise ExacloudRuntimeError(0x0811, 0xA, _msg)
            else:
                ebLogInfo(f'mDeleteDbVault: vault deleted')
                _data_d["storage_pool"] = self.mGetStoragePoolDetails(_cell, _poolName, aOptions)
                self._mUpdateRequestData(_ret,_data_d,"")
        else:
            _msg = f'DBVault {_vaultName} as it doesnot exists. Doing nothing marking the task as success'
            _ret = 0
            ebLogInfo(_msg)
            _data_d["storage_pool"] = self.mGetStoragePoolDetails(_cell, _poolName, aOptions)
            self._mUpdateRequestData(_ret,_data_d,"")
        return _ret
    
    # function to update DB vault 
    def mUpdateDbVault(self, aOptions):
        """
        function to delete DB vault 
        input: 1. vaultOcid 2. cells [ ] 3. vault size in GB 4. vault name 5. ctrl IP 6. Port details
        response : 1. vaultOcid 2. VaultName 3. new VaultSize in GB 4. VaultRefId 5. totalStorageGB 6. usedStorageGB
        """
        ebLogInfo("*** mUpdateDbVault")# function to update DB vault 
        _data_d = {}
        _errString = None
        _ret = -1
        _ebox = self.__cluctrl
        _escli = self.__escli
        _attributes = []
        _options = aOptions
        _inputjson = _options.jsonconf
        _cell_list = _inputjson['cell_list']
        _cell = _cell_list[0]
        _vaultName = _inputjson['db_vault']['name']
        _poolName = _inputjson['storage_pool']
        _vaultNewSize = str(_inputjson['db_vault']['gb_size'])
        _vaultNewSizeWithRedundancy = int(int(_vaultNewSize) * REDUNDANCY_FACTOR)
        _usedSpace = 0
        _ef_rack, _suffix, _attributes = (True, "EF", ["spaceUsedEF"]) if _escli.mIsEFRack(_cell) else (False, "HC", ["spaceUsedHC"])
            
        _ret, _out, _err = _escli.mListVault(_cell, _vaultName, aOptions, aDetail=False, aAttributes=_attributes, aJson=True)
        if _ret != 0:
            _msg = f'Unable to Get System Vault {_vaultName} details due to {_err}. Output is {_out}'
            ebLogError(_msg)
            _ebox.mUpdateErrorObject(gExascaleError["VAULT_GET_SIZE_FAILED"], _msg)
            self._mUpdateRequestData(_ret,_data_d,_msg)
            raise ExacloudRuntimeError(0x0811, 0xA, _msg)
        else:
            _json = ''.join( _out.splitlines())
            if _json[0] == '{':
                _jsonOut = json.loads(_json)
                _vault = {}
                _usedSpace = int(_jsonOut["data"]["attributes"][f"spaceUsed{_suffix}"])
                if _usedSpace > 0:
                    _usedSpace= float(_jsonOut["data"]["attributes"][f"spaceUsed{_suffix}"])/(1024*1024*1024)
                    
        if  float(_vaultNewSizeWithRedundancy) < _usedSpace:
            _msg = f'Unable to update the vault {_vaultName} size as current DBVault used space is more then the resize value. please resize to higher value'
            ebLogError(_msg)
            _ebox.mUpdateErrorObject(gExascaleError["VAULT_UPDATE_SIZE_FAILED"], _msg)
            self._mUpdateRequestData(-1,_data_d,_msg)
            raise ExacloudRuntimeError(0x0811, 0xA, _msg)
        _ret, _out, _err = _escli.mChangeVault(_cell, _ef_rack, _vaultName, _vaultNewSizeWithRedundancy, aOptions)
        if _ret != 0:
            _msg = f'Unable to get current DBVault {_vaultName} size due to error:{_err} output:{_out}'
            ebLogError(_msg)
            _ebox.mUpdateErrorObject(gExascaleError["VAULT_GET_SIZE_FAILED"], _msg)
            self._mUpdateRequestData(_ret,_data_d,_msg)
            raise ExacloudRuntimeError(0x0811, 0xA, _msg)
        else:
            _json = ''.join( _out.splitlines())
            if _json[0] == '{':
                _jsonOut = json.loads(_json)
                _vault = {}
                _vault["vault_ocid"]= _inputjson['db_vault']['vault_ocid']
                _vault["name"]= _vaultName 
                _vault["ref_id"]= _jsonOut["data"]["id"]
                _totalStorage = float(float(_jsonOut["data"]["attributes"][f"spaceProv{_suffix}"])/(1024*1024*1024))/REDUNDANCY_FACTOR
                _vault["total_storage_gb"]= math.floor(_totalStorage)
                _usedSpace = int(_jsonOut["data"]["attributes"][f"spaceUsed{_suffix}"])
                if _usedSpace > 0:
                    _usedSpace= float(_jsonOut["data"]["attributes"][f"spaceUsed{_suffix}"])/(1024*1024*1024)
                _vault["used_storage_gb"]= math.ceil(_usedSpace/REDUNDANCY_FACTOR)
                _data_d["db_vault"] = _vault
        _data_d["storage_pool"] = self.mGetStoragePoolDetails(_cell, _poolName, aOptions)
        ebLogInfo(f'mUpdateDbVault: vault Updated')
        self._mUpdateRequestData(_ret, _data_d, "")
        return _ret

    def mGetDbVault(self, aOptions):
        """
        function to get DB vault details
        """
        ebLogInfo("*** mGetDbVault")
        _data_d = {}
        _vaultList = []
        _errString = None
        _ret = -1
        _ebox = self.__cluctrl
        _escli = self.__escli
        _options = aOptions
        _poolName = _options.jsonconf["storage_pool"]
        _dbVaultList = _options.jsonconf["db_vaults"]
        _cell = None
        if not _dbVaultList:
            _ret = 0 
        for _inputjson in _dbVaultList:
            _cell_list = _inputjson['cell_list']
            _cell = _cell_list[0]
            _suffix = "EF" if _escli.mIsEFRack(_cell) else "HC"
            _vaultName = _inputjson['db_vault']['name']
            _ret, _out, _err = _escli.mListVault(_cell, _vaultName, _options, aDetail=True)
            if _ret != 0:
                _msg = f'Unable to Get DBVault {_vaultName} details due to {_err}. Output is {_out}'
                ebLogWarn(_msg)
            else:
                _json = ''.join( _out.splitlines())
                if _json[0] == '{':
                    _jsonOut = json.loads(_json)
                    _vault = {}
                    _vault["vault_ocid"]= _inputjson['db_vault']['vault_ocid']
                    _vault["name"]= _vaultName
                    _vault["ref_id"]= _jsonOut["data"]["id"]
                    _totalStorage = float(float(_jsonOut["data"]["attributes"][f"spaceProv{_suffix}"])/(1024*1024*1024))/REDUNDANCY_FACTOR
                    _vault["total_storage_gb"]= math.floor(_totalStorage)
                    _usedSpace = int(_jsonOut["data"]["attributes"][f"spaceUsed{_suffix}"])
                    if _usedSpace > 0:
                        _usedSpace= float(_jsonOut["data"]["attributes"][f"spaceUsed{_suffix}"])/(1024*1024*1024)
                    _vault["used_storage_gb"]= math.ceil(_usedSpace/REDUNDANCY_FACTOR)
                    _vaultList.append(_vault)
        _data_d["db_vaults"] = _vaultList
        if not _cell:
            if 'cell_list' in list(_options.jsonconf.keys()) and _options.jsonconf['cell_list']:
                _cell = _options.jsonconf['cell_list'][0]
            elif "exascale" in list(aOptions.jsonconf.keys()):
                _exascale_attr = aOptions.jsonconf['exascale']
                if 'cell_list' in list(_exascale_attr.keys()) and _exascale_attr['cell_list']:
                    _cell = _exascale_attr['cell_list'][0]
        _data_d["storage_pool"] = self.mGetStoragePoolDetails(_cell, _poolName, aOptions, True)
        ebLogInfo(f'mGetDbVault: vault details sent')
        self._mUpdateRequestData(_ret,_data_d,"")
        return _ret

    def mGetStoragePoolDetails(self, aCell, aPoolName, aOptions, aSyncCall=False):
        _cell = aCell
        _pool_name = aPoolName
        _pooldata_d = {}
        _ebox = self.__cluctrl
        _escli = self.__escli

        #Check if the rack is Extreme Flash
        if _escli.mIsEFRack(_cell):
            _ef_rack = True
            _suffix = "EF"
        else:
            _ef_rack = False
            _suffix = "HC"

        _ret, _out, _err = _escli.mListStoragePool(_cell, _pool_name, aOptions)
        if _ret != 0:
            _msg = f'Unable to get current Storage Pool {aPoolName} size due to {_err}. Output is {_out}'
            ebLogError(_msg)
            _ebox.mUpdateErrorObject(gExascaleError["STORAGEPOOL_GET_DETAILS_FAILED"], _msg)
            raise ExacloudRuntimeError(0x0811, 0xA, _msg)
        else:
            _json = ''.join( _out.splitlines())
            if _json[0] == '{':
                _jsonOut = json.loads(_json)
                _usedSpaceGb = float(_jsonOut['data']['attributes']['spaceUsed'])
                if _usedSpaceGb > 0:
                    _usedSpaceGb=  math.ceil(float(float(_jsonOut["data"]["attributes"]["spaceUsed"])/(1024*1024*1024)))
                _totalSpaceGb =  math.floor(float(float(_jsonOut['data']['attributes']['spaceRaw'])/(1024*1024*1024))/REDUNDANCY_FACTOR)
                _currentprovisionedSpaceGb = math.floor(float(float(_jsonOut['data']['attributes']['spaceProvisioned'])/(1024*1024*1024))/REDUNDANCY_FACTOR)
                ebLogInfo(f"*** Storage Pool {aPoolName} detail: total Space={_totalSpaceGb}Gb, spaceProvisioned={_currentprovisionedSpaceGb}Gb, spaceUsed={_usedSpaceGb}Gb")
                _pooldata_d["name"]= aPoolName
                _pooldata_d["gb_total_size"]= _totalSpaceGb
                _pooldata_d["gb_used_size"]= math.ceil(_usedSpaceGb/REDUNDANCY_FACTOR)
                _pooldata_d["gb_provisioned_size"]= _currentprovisionedSpaceGb
        if not aSyncCall:
            ebLogInfo(f'***  Getting the provisioned value as sum of all the vault size')
            _ret, _out, _err = _escli.mGetProvisionedValue(_cell, _ef_rack, aOptions)
            if _ret != 0:
                _msg = f'Unable to get current Storage Pool {aPoolName} size due to {_err}. Output is {_out}'
                ebLogError(_msg)
                _ebox.mUpdateErrorObject(gExascaleError["STORAGEPOOL_GET_DETAILS_FAILED"], _msg)
                raise ExacloudRuntimeError(0x0811, 0xA, _msg)
            else:
                _json = ''.join( _out.splitlines())
                if _json[0] == '{':
                    _vaultList = []
                    _provisionedVaultSpace = 0
                    _jsonOut = json.loads(_json)
                    ebLogTrace(json.dumps(_jsonOut, indent=4, sort_keys=True))
                    _vaultList = _jsonOut["data"]
                    if not _vaultList: 
                        ebLogInfo(f'*** no vaults found')
                        return _pooldata_d
                    for vault in _vaultList:
                        _provisionedVaultSpace += int(vault['attributes'][f'spaceProv{_suffix}']) 
                    _totalUsedSpaceGb =  math.ceil(float(float(_provisionedVaultSpace)/(1024*1024*1024))/REDUNDANCY_FACTOR)
                    ebLogInfo(f'*** total used Space for vault creation is :{_totalUsedSpaceGb} GB')
                    if _totalSpaceGb > 0:
                        _pooldata_d["gb_provisioned_size"]= _totalUsedSpaceGb
        return _pooldata_d
    
    def mCreateSysVault(self, aOptions):
        """
        function to create system vault
        input: 1. vault type 2. cells [ ] 3. vault size in GB 4. vault name 5. ctrl IP 6. Port details
        response : 1. VaultName 2. VaultSize in GB 3. totalStorageGB 4. usedStorageGB
        """
        ebLogInfo("*** mCreateSysVault")
        _data_d = {}
        _errString = None
        _ret = -1
        _ebox = self.__cluctrl
        _escli = self.__escli
        _options = aOptions
        _inputjson = _options.jsonconf
        _cell_list = _inputjson['cell_list']
        _cell = _cell_list[0]
        _vaultName = _inputjson['system_vault']['name']
        _dom0CommandAppend = None
        _domOList = _inputjson["compute_list"]
        _poolName = None
        if "storage_pool" in list(_inputjson.keys()):
            _poolName = _inputjson['storage_pool']
        _vaultSize = str(_inputjson['system_vault']['gb_size'])
        #List Vault
        _ret, _out, _err = _escli.mListVault(_cell, _vaultName, aOptions)
        if _ret == 0:
            _msg = f'Unable to Create System Vault {_vaultName} as it already exists. error detail:{_err} output:{_out}'
            ebLogError(_msg)
            _ebox.mUpdateErrorObject(gExascaleError["VAULT_CREATION_FAILED"], _msg)
            self._mUpdateRequestData(-1,_data_d,_msg)
            raise ExacloudRuntimeError(0x0811, 0xA, _msg)
        _vaultSizeWithRedundancy = int(int(_vaultSize) * REDUNDANCY_FACTOR)

        #Check if the rack is Extreme Flash
        _ef_rack, _suffix = (True, "EF") if _escli.mIsEFRack(_cell) else (False, "HC")
        #Create Vault
        _ret, _out, _err = _escli.mCreateVault(_cell, _ef_rack, _vaultName, _vaultSizeWithRedundancy, aOptions)
        if _ret != 0:
            _msg = f'Unable to Create System Vault {_vaultName} of size {_vaultSize}GB due to error:{_err} output:{_out}'
            ebLogError(_msg)
            _ebox.mUpdateErrorObject(gExascaleError["VAULT_CREATION_FAILED"], _msg)
            self._mUpdateRequestData(-1,_data_d,_msg)
            raise ExacloudRuntimeError(0x0811, 0xA, _msg)
        else:
            for _dom0 in _domOList:
                _host = _dom0.split('.')[0]
                _escli.mChangeACL(_cell, None, "M", aOptions, _host, aVaultName=_vaultName)
            _json = ''.join( _out.splitlines())
            _vault = {}
            if _json[0] == '{':
                _jsonOut = json.loads(_json)
                _vault["name"]= _vaultName
                _vault["vault_ocid"]= _inputjson['system_vault']['vault_ocid']
                _vault["ref_id"]= _jsonOut["data"]["id"]
                _totalStorage = float(float(_jsonOut["data"]["attributes"][f"spaceProv{_suffix}"])/(1024*1024*1024))/REDUNDANCY_FACTOR
                _vault["total_storage_gb"]= math.floor(_totalStorage)
                _usedSpace = int(_jsonOut["data"]["attributes"][f"spaceUsed{_suffix}"])
                if _usedSpace > 0:
                    _usedSpace= float(_jsonOut["data"]["attributes"][f"spaceUsed{_suffix}"])/(1024*1024*1024)/REDUNDANCY_FACTOR
                _vault["used_storage_gb"]= math.ceil(_usedSpace)
                _data_d["system_vault"] = _vault
        if _poolName is not None:
            _data_d["storage_pool"] = self.mGetStoragePoolDetails(_cell, _poolName, aOptions)    
        ebLogInfo(f'mCreateSysVault: Vault Created')
        # Enable Auto File Encryption if not already enabled
        # Skip only if flag is set in exabox.conf
        _flag_encryption = "exascale_autofileencryption_disable"
        if str(get_gcontext().mGetConfigOptions().get(
           _flag_encryption, "False")).upper() == "TRUE":
            ebLogWarn(f"Auto File encryption has been skipped by exabox.conf flag '{_flag_encryption}'!")
        else:
            _rc = self.mEnableAutoFileEncryption(aOptions)
            if _rc:
                ebLogError(f"Failed to enable Auto File Encryption")
            else:
                ebLogInfo('Auto File Encryption Enabled')
        self._mUpdateRequestData(_ret,_data_d,"")
        return _ret
    
    def mDeleteSysVault(self, aOptions):
        """
        function to delete system vault 
        input: 1. vault type 2. cells [ ] 3. vault name 4. ctrl IP 5. Port details
        """
        ebLogInfo("*** mDeleteSysVault")
        _data_d = {}
        _errString = None
        _ret = -1
        _ebox = self.__cluctrl
        _escli = self.__escli
        _options = aOptions
        _inputjson = _options.jsonconf
        _cell_list = _inputjson['cell_list']
        _cell = _cell_list[0]
        _vaultName = _inputjson['system_vault']['name']
        _poolName = None
        if "storage_pool" in list(_inputjson.keys()):
            _poolName = _inputjson['storage_pool']

        _ret, _out, _err = _escli.mListVault(_cell, _vaultName, aOptions)
        if _ret == 0:
            _ret, _out, _err = _escli.mRemoveVault(_cell, _vaultName, aOptions)
            if _ret != 0:
                _msg = f'Unable to Delete System Vault {_vaultName} due to error: {_err} output:{_out}'
                ebLogError(_msg)
                _ebox.mUpdateErrorObject(gExascaleError["VAULT_DELETION_FAILED"], _msg)
                self._mUpdateRequestData(_ret,_data_d,_msg)
                raise ExacloudRuntimeError(0x0811, 0xA, _msg)
            else:
                ebLogInfo(f'mDeleteSysVault: vault deleted')
                if _poolName is not None:
                    _data_d["storage_pool"] = self.mGetStoragePoolDetails(_cell, _poolName, aOptions) 
                self._mUpdateRequestData(_ret,_data_d,"")
        else:
            _msg = f'System Vault {_vaultName} as it doesnot exists. Doing nothing marking the task as success'
            _ret = 0
            ebLogInfo(_msg)
            if _poolName is not None:
                _data_d["storage_pool"] = self.mGetStoragePoolDetails(_cell, _poolName, aOptions)
            self._mUpdateRequestData(_ret,_data_d,"")
        return _ret
    
    def mUpdateSysVault(self, aOptions):
        """
        function to delete DB vault 
        input: 1. cells [ ] 2. vault size in GB 3. vault name 4. ctrl IP 5. Port details
        response : 1.VaultName 2. new VaultSize in GB 3. VaultRefId 4. totalStorageGB 5. usedStorageGB
        """
        ebLogInfo("*** mUpdateDbVault")# function to update DB vault 
        _data_d = {}
        _errString = None
        _ret = -1
        _ebox = self.__cluctrl
        _escli = self.__escli
        _attributes = []
        _options = aOptions
        _inputjson = _options.jsonconf
        _cell_list = _inputjson['cell_list']
        _cell = _cell_list[0]
        _vaultName = _inputjson['system_vault']['name']
        _poolName = None
        _usedSpace = 0
        if "storage_pool" in list(_inputjson.keys()):
            _poolName = _inputjson['storage_pool']
        _vaultNewSize = str(_inputjson['system_vault']['gb_size'])
        _vaultNewSizeWithRedundancy = int(int(_vaultNewSize) * REDUNDANCY_FACTOR)
        _ef_rack, _suffix, _attributes = (True, "EF", ["spaceUsedEF"]) if _escli.mIsEFRack(_cell) else (False, "HC", ["spaceUsedHC"])
        _ret, _out, _err = _escli.mListVault(_cell, _vaultName, aOptions, aDetail=False, aAttributes=_attributes, aJson=True)
        if _ret != 0:
            _msg = f'Unable to Get System Vault {_vaultName} details due to {_err}. Output is {_out}'
            ebLogError(_msg)
            _ebox.mUpdateErrorObject(gExascaleError["VAULT_GET_SIZE_FAILED"], _msg)
            self._mUpdateRequestData(_ret,_data_d,_msg)
            raise ExacloudRuntimeError(0x0811, 0xA, _msg)
        else:
            _json = ''.join( _out.splitlines())
            if _json[0] == '{':
                _jsonOut = json.loads(_json)
                _vault = {}
                _usedSpace = int(_jsonOut["data"]["attributes"][f"spaceUsed{_suffix}"])
                if _usedSpace > 0:
                    _usedSpace= float(_jsonOut["data"]["attributes"][f"spaceUsed{_suffix}"])/(1024*1024*1024)
        if  float(_vaultNewSizeWithRedundancy) < _usedSpace:
            _msg = f'Unable to update the vault {_vaultName} size as current System Vault used space is more then the resize value. please resize to higher value'
            ebLogError(_msg)
            _ebox.mUpdateErrorObject(gExascaleError["VAULT_UPDATE_SIZE_FAILED"], _msg)
            self._mUpdateRequestData(-1,_data_d,_msg)
            raise ExacloudRuntimeError(0x0811, 0xA, _msg)
        _ret, _out, _err = _escli.mChangeVault(_cell, _ef_rack, _vaultName, _vaultNewSizeWithRedundancy, aOptions)
        if _ret != 0:
            _msg = f'Unable to get current DBVault {_vaultName} size due to error:{_err} output:{_out}'
            ebLogError(_msg)
            _ebox.mUpdateErrorObject(gExascaleError["VAULT_GET_SIZE_FAILED"], _msg)
            self._mUpdateRequestData(_ret,_data_d,_msg)
            raise ExacloudRuntimeError(0x0811, 0xA, _msg)
        else:
            _json = ''.join( _out.splitlines())
            if _json[0] == '{':
                _jsonOut = json.loads(_json)
                _vault = {}
                _vault["name"]= _vaultName 
                _vault["ref_id"]= _jsonOut["data"]["id"]
                _vault["vault_ocid"]= _inputjson['system_vault']['vault_ocid']
                _totalStorage = float(float(_jsonOut["data"]["attributes"][f"spaceProv{_suffix}"])/(1024*1024*1024))/REDUNDANCY_FACTOR
                _vault["total_storage_gb"]= math.floor(_totalStorage)
                _usedSpace = int(_jsonOut["data"]["attributes"][f"spaceUsed{_suffix}"])
                if _usedSpace > 0:
                    _usedSpace= float(_jsonOut["data"]["attributes"][f"spaceUsed{_suffix}"])/(1024*1024*1024)
                _vault["used_storage_gb"]= math.ceil(_usedSpace/REDUNDANCY_FACTOR)
                _data_d["system_vault"] = _vault
        if _poolName is not None:
            _data_d["storage_pool"] = self.mGetStoragePoolDetails(_cell, _poolName, aOptions)
        ebLogInfo(f'mUpdateSysVault: vault Updated')
        self._mUpdateRequestData(_ret, _data_d, "")
        return _ret

    def mGetAllVaults(self, aOptions):
        """
        function to get DB vault details
        """
        ebLogInfo("*** mGetDbVault")
        _data_d = {}
        _dbFinalVaultList = []
        _SysFinalVaultList = []
        _errString = None
        _ret = -1
        _suffix = "HC"
        _ebox = self.__cluctrl
        _escli = self.__escli
        _options = aOptions
        _poolName = _options.jsonconf["storage_pool"]
        _dbVaultList = _options.jsonconf["db_vaults"]
        _sysVaultList = _options.jsonconf["system_vaults"]
        _exascale_attr = aOptions.jsonconf['exascale']
        _sysvault_cell_list = _exascale_attr['cell_list']
        _cell = None
        if not _dbVaultList and not _sysVaultList:
            _ret = 0
        for _inputjson in _dbVaultList:
            _cell_list = _inputjson['cell_list']
            _cell = _cell_list[0]
            _vaultName = _inputjson['db_vault']['name']
            _suffix = "EF" if _escli.mIsEFRack(_cell) else "HC"
            _ret, _out, _err = _escli.mListVault(_cell, _vaultName, aOptions, aDetail=True)
            if _ret != 0:
                _msg = f'Unable to Get DBVault {_vaultName} details due to {_err}. Output is {_out}'
                ebLogWarn(_msg)
            else:
                _json = ''.join( _out.splitlines())
                if _json[0] == '{':
                    _jsonOut = json.loads(_json)
                    _vault = {}
                    _vault["vault_ocid"]= _inputjson['db_vault']['vault_ocid']
                    _vault["name"]= _vaultName
                    _vault["ref_id"]= _jsonOut["data"]["id"]

                    _totalStorage = float(float(_jsonOut["data"]["attributes"][f"spaceProv{_suffix}"])/(1024*1024*1024))/REDUNDANCY_FACTOR
                    _vault["total_storage_gb"]= math.floor(_totalStorage)
                    _usedSpace = int(_jsonOut["data"]["attributes"][f"spaceUsed{_suffix}"])
                    if _usedSpace > 0:
                        _usedSpace= float(_jsonOut["data"]["attributes"][f"spaceUsed{_suffix}"])/(1024*1024*1024)
                    _vault["used_storage_gb"]= math.ceil(_usedSpace/REDUNDANCY_FACTOR)
                    _dbFinalVaultList.append(_vault)
        _data_d["db_vaults"] = _dbFinalVaultList            
        for _inputjson in _sysVaultList:
            _vaultName = _inputjson['name']
            _sysvault_cell = _sysvault_cell_list[0]
            _suffix = "EF" if _escli.mIsEFRack(_sysvault_cell) else "HC"
            _ret, _out, _err = _escli.mListVault(_cell, _vaultName, aOptions, aDetail=True)
            if _ret != 0:
                _msg = f'Unable to Get System Vault {_vaultName} details due to {_err}. Output is {_out}'
                ebLogWarn(_msg)
            else:
                _json = ''.join( _out.splitlines())
                if _json[0] == '{':
                    _jsonOut = json.loads(_json)
                    _vault = {}
                    _vault["name"]= _vaultName
                    _vault["vault_type"] = _inputjson["vault_type"]
                    _vault["vault_ocid"]=  _inputjson['vault_ocid']
                    _vault["ref_id"]= _jsonOut["data"]["id"]
                    _totalStorage = float(float(_jsonOut["data"]["attributes"][f"spaceProv{_suffix}"])/(1024*1024*1024))/REDUNDANCY_FACTOR
                    _vault["total_storage_gb"]= math.floor(_totalStorage)
                    _usedSpace = int(_jsonOut["data"]["attributes"][f"spaceUsed{_suffix}"])
                    if _usedSpace > 0:
                        _usedSpace= float(_jsonOut["data"]["attributes"][f"spaceUsed{_suffix}"])/(1024*1024*1024)
                    _vault["used_storage_gb"]= math.ceil(_usedSpace/REDUNDANCY_FACTOR)
                    _SysFinalVaultList.append(_vault)

        _data_d["system_vaults"] = _SysFinalVaultList
        if not _cell:
            if 'cell_list' in list(_options.jsonconf.keys()) and _options.jsonconf['cell_list']:
                _cell = _options.jsonconf['cell_list'][0]
            elif "exascale" in list(aOptions.jsonconf.keys()):
                _exascale_attr = aOptions.jsonconf['exascale']
                if 'cell_list' in list(_exascale_attr.keys()) and _exascale_attr['cell_list']:
                    _cell = _exascale_attr['cell_list'][0]
        _data_d["storage_pool"] = self.mGetStoragePoolDetails(_cell, _poolName, aOptions, True)
        ebLogInfo(f'mGetDbVault: vault details sent')
        self._mUpdateRequestData(_ret,_data_d,"")
        return _ret

    def mEnableQinQIfNeeded(self, aOptions, aDom0List=None):
        ebLogInfo(" *** mEnableQinQIfNeeded() >>")
        _ebox = self.__cluctrl
        _options = aOptions
        _host_list = []
        _exascale_attr = _options.jsonconf['exascale']
        if aDom0List:
            _host_nodes = _exascale_attr['host_nodes']
            for _dom0 in aDom0List:
                _host = self.mParseQinQHostInfo(_host_nodes, _dom0)
                _host_list.append(_host)
        else:
            _host_list = _exascale_attr['host_nodes']

        for _host in _host_list:
            ebLogInfo(f"*** mEnableQinQIfNeeded(): running on host {_host['compute_hostname']}")
            # Make sure QinQ is setup in the Dom0
            _dom0 = _host['compute_hostname']
            with connect_to_host(_dom0, get_gcontext()) as _node:
                # Check if we actually need to configure QinQ for this Dom0
                _cmd = f'/usr/sbin/vm_maker --check'
                _ret, _out, _ = node_exec_cmd(_node, _cmd)
                if _ret != 0 or "The system is not configured for Secure Fabric support" in _out:
                    _msg = f'mEnableQinQIfNeeded: QinQ not configured in Dom0 {_dom0}. Attempting configuration now...'
                    ebLogWarn(_msg)

                    # Check if no VMs are running in the Dom0
                    _cmd = '/bin/virsh list --all --name'
                    _running_domus = \
                        [ vm.strip()
                        for vm in node_exec_cmd(_node, _cmd).stdout.splitlines()
                        if vm.strip() ]
                    if _running_domus:
                        _msg = ("*** mEnableQinQIfNeeded(): Cannot setup "
                                f"QinQ in Dom0 {_dom0} since the following DomUs "
                                f"are still existing: {_running_domus}")
                        ebLogError(_msg)
                        _ebox.mUpdateErrorObject(gExascaleError["CONFIG_STRE_FAILED"], _msg)
                        raise ExacloudRuntimeError(0x0811, 0xA, _msg)

                    # Run the QinQ setup
                    _cmd = '/opt/oracle.SupportTools/switch_to_ovm.sh --qinq'
                    _node.mExecuteCmdLog(_cmd)
                    _ret = _node.mGetCmdExitStatus()
                    if _ret != 0:
                        _msg = f'mEnableQinQIfNeeded: QinQ configuration failed in Dom0 {_dom0}!!! Please review the error. Aborting now...'
                        ebLogError(_msg)
                        _ebox.mUpdateErrorObject(gExascaleError["CONFIG_STRE_FAILED"], _msg)
                        raise ExacloudRuntimeError(0x0811, 0xA, _msg)
                    ebLogInfo(f'mEnableQinQIfNeeded: QinQ configuration succeeded in Dom0 {_dom0}. Will reboot the node now...')
                    self.__cluctrl.mRebootNode(_dom0)

    def mCheckRoCEIPs(self, aOptions, aFailedList, aDom0List=None):
        ebLogInfo(" *** mCheckRoCEIPs() >>")
        _failedList = aFailedList
        _options = aOptions
        _retflag = True
        _host_list = []
        _exascale_attr = _options.jsonconf['exascale']
        if aDom0List:
            _host_nodes = _exascale_attr['host_nodes']
            for _dom0 in aDom0List:
                _host = self.mParseQinQHostInfo(_host_nodes, _dom0)
                _host_list.append(_host)
        else:
            _host_list = _exascale_attr['host_nodes']

        for _host in _host_list:
            ebLogInfo(f"*** mCheckRoCEIPs(): running on host {_host['compute_hostname']}")
            with connect_to_host(_host['compute_hostname'], get_gcontext()) as _node:
                for stre_iface, ipaddress in zip((_host['interface1'], _host['interface2']), (_host['storage_ip1'], _host['storage_ip2'])):
                    #Check if stre interface is configured with ip.
                    _cmd = f'/usr/sbin/ip a s {stre_iface} | /bin/grep inet | grep {ipaddress}'
                    _node.mExecuteCmdLog(_cmd)
                    _ret = _node.mGetCmdExitStatus()
                    if _ret == 0:
                        ebLogInfo(f"mCheckRoCEIPs: Interface {stre_iface} is already configured in {_host['compute_hostname']}.")
                    else:
                        if _host['compute_hostname'] not in _failedList:
                            _failedList.append(_host['compute_hostname'])
                        _retflag = False
                        ebLogWarn(f"mCheckRoCEIPs: Interface {stre_iface} is not yet configured in {_host['compute_hostname']}")   
        return _retflag

    def mSetupRoCEIPs(self, aOptions, aFailedList, aDom0List=None):
        ebLogInfo(" *** mSetupRoCEIPs() >>")
        _ret=-1
        _ebox = self.__cluctrl
        _host_list = []
        _exascale_attr = aOptions.jsonconf['exascale']
        if aDom0List:
            _host_nodes = _exascale_attr['host_nodes']
            for _dom0 in aDom0List:
                _host = self.mParseQinQHostInfo(_host_nodes, _dom0)
                _host_list.append(_host)
        else:
            _host_list = _exascale_attr['host_nodes']

        for _host in _host_list:

            if not aOptions.jsonconf or 'compute_hostname' not in _host or 'storage_ip1' not in _host:
                _msg= f'Missing config details in the payload'
                _ebox.mUpdateErrorObject(gExascaleError["INVALID_INPUT_PARAMETER"], _msg)
                raise ExacloudRuntimeError(0x0811, 0xA, _msg)
            
            if _host['compute_hostname'] not in  aFailedList:
                continue

            _dom0 = _host['compute_hostname']
            _ip = _host['storage_ip1']
            ebLogInfo(f'mSetupRoCEIPs: {_dom0} : {_ip}')
            _vlan_id = _exascale_attr['storage_vlan_id']
            _netmask = _host['netmask']
            if _netmask is None:
                _netmask = "255.255.0.0"
                #stre interfaces are allocated 'class B' address from ecra. Hence this netmask of 255.255.0.0

            _reboot_dom0 = False
            with connect_to_host(_dom0, get_gcontext()) as _node:
                # Remember all the DomUs that are currently alive
                _cmd = '/bin/virsh list --name'
                _running_domus = \
                    [ vm.strip()
                    for vm in node_exec_cmd_check(_node, _cmd).stdout.splitlines()
                    if vm.strip() ]

                # Configure RoCE VLAN and IPs
                _cmd = f'/usr/sbin/vm_maker --set --storage-vlan {_vlan_id} --ip {_ip} --netmask {_netmask}'
                _ret, _out, _err = node_exec_cmd(_node, _cmd)
                if "Shut down all guests" in _out + _err:
                    ebLogWarn("mSetupRoCEIPs: VM maker demanding us to shut off all VMs first!")
                    # Shut off all DomUs
                    _cmd = '/usr/sbin/vm_maker --stop-domain --all'
                    _node.mExecuteCmdLog(_cmd)
                    _ret = _node.mGetCmdExitStatus()
                    if _ret != 0:
                        _msg = f'mSetupRoCEIPs: Unable to shutdown all DomUs before RoCE setup'
                        ebLogError(_msg)
                        _ebox.mUpdateErrorObject(gExascaleError["CONFIG_STRE_FAILED"], _msg)
                        raise ExacloudRuntimeError(0x0811, 0xA, _msg)

                    # Try again
                    _cmd = f'/usr/sbin/vm_maker --set --storage-vlan {_vlan_id} --ip {_ip} --netmask {_netmask}'
                    _ret, _out, _err = node_exec_cmd(_node, _cmd)

                if _ret != 0:
                    _msg = f'mSetupRoCEIPs: Unable to configure the stre interface'
                    ebLogError(_msg)
                    _ebox.mUpdateErrorObject(gExascaleError["CONFIG_STRE_FAILED"], _msg)
                    raise ExacloudRuntimeError(0x0811, 0xA, _msg)

                # Check if Dom0 reboot is required
                if "A reboot is required" in _out + _err:
                    ebLogWarn("mSetupRoCEIPs: VM maker demanding us to reboot the Dom0!")
                    _reboot_dom0 = True

                # Check if re0 & re1 have properly been de-configured
                for _if in ('re0', 're1'):
                    _node.mExecuteCmdLog(f"/usr/sbin/ip a s {_if} | /bin/grep 'inet '")
                    _ret = _node.mGetCmdExitStatus()
                    if _ret == 0:
                        ebLogWarn(f"mSetupRoCEIPs: {_if} still has an IPv4 configured!")
                        _reboot_dom0 = True
                        break

            if _reboot_dom0:
                self.__cluctrl.mRebootNode(_dom0)

            with connect_to_host(_dom0, get_gcontext()) as _node:
                # Start the DomUs again
                for _domu in _running_domus:
                    start_domu(_node, _domu, wait_for_connectable=False)

                #Validate interfaces are properly set.
                #stre0 should be set to the input ip.
                _node.mExecuteCmdLog(f"/usr/sbin/ip a s {_host['interface1']} | /bin/grep {_ip}")
                _ret = _node.mGetCmdExitStatus()
                if _ret == 0:
                    ebLogInfo(f"mSetupRoCEIPs: Interface {_host['interface1']} is configured successfully on {_dom0}.")
                else:
                    _msg = f"mSetupRoCEIPs: Interface {_host['interface1']} is not configured on {_dom0}"
                    ebLogError(_msg)
                    _ebox.mUpdateErrorObject(gExascaleError["CONFIG_STRE_FAILED"], _msg)
                    raise ExacloudRuntimeError(0x0811, 0xA, _msg)

                #stre1 will be set with the next subsequent ip-adress. Hence check if any ip is configured.
                _node.mExecuteCmdLog(f"/usr/sbin/ip a s {_host['interface2']} | /bin/grep inet")
                _ret = _node.mGetCmdExitStatus()
                if _ret == 0:
                    ebLogInfo(f"mSetupRoCEIPs: Interface {_host['interface2']} is configured successfully on {_dom0}.")
                else:
                    _msg = f"mSetupRoCEIPs: Interface {_host['interface2']} is not configured on {_dom0}."
                    ebLogError(_msg)
                    _ebox.mUpdateErrorObject(gExascaleError["CONFIG_STRE_FAILED"], _msg)
                    raise ExacloudRuntimeError(0x0811, 0xA, _msg)
            ebLogInfo(f'mSetupRoCEIPs: Move to next Host')

        # Setup NFTables rules for stre0 & stre1 interfaces in Dom0s
        _dom0s = [ _host['compute_hostname'] for _host in _host_list
                   if _host['compute_hostname'] in aFailedList ]
        if _dom0s:
            _ebox.mSetupNatNfTablesOnDom0v2(aDom0s=_dom0s)

        return _ret

    def mExecuteXSConfigOp(self, aOptions):
        """
        function to decide which operation to run on xsconfig
        """
        ebLogInfo("*** mExecuteXSConfigOp")
        _rc=-1
        _ebox = self.__cluctrl
        _options = aOptions
        _inputjson = _options.jsonconf
        _enable_xs_service = "false"
        _enable_xs_service = self.__cluctrl.mCheckConfigOption('enable_xs_service')
        if _enable_xs_service.lower() == "false":
            _msg = 'enable_xs_service flag is False. XS(Exascale) Service is disabled.'
            ebLogError(_msg)
            _ebox.mUpdateErrorObject(gExascaleError["ERROR_XS_DISABLED"], _msg)
            self.__cluctrl.mSetXS(False)
            return _rc
        if not _inputjson:
            ebLogError("*** mExecuteXSConfigOp params missing ")
            return _rc
        if _inputjson["config_op"] == "config":
            return self.mExecuteXSConfigOedaStep(_options)
        elif _inputjson["config_op"] == "updatestoragepool":
            return self.mExecuteXSConfigReshapePool(_options)
        _msg = "Invalid DBVault operation %s "%(_inputjson["config_op"])
        ebLogError(_msg)
        _ebox.mUpdateErrorObject(gExascaleError["INVALID_EXASCALE_OPERATION"], _msg)
        return _rc

    def mCheckStorageVlanID(self, aCell, aVlanID):
        _cell = aCell
        _vlanId = aVlanID
        _cell_vlanId = 0
        _ebox = self.__cluctrl

        with connect_to_host(_cell, get_gcontext(), username="root") as _node:
            _i, _o, _e = _node.mExecuteCmd(f"/bin/cat /etc/exadata/config/initqinq.conf | /bin/grep VLAN:")
            _out = _o.readlines()
            if _out:
                _cell_vlanId = int(_out[0].strip().split(":")[-1])

            if _cell_vlanId != int(_vlanId):
                _msg = f"Storage vlanID:{_cell_vlanId} on {_cell} not matching with vlanID:{_vlanId} from input payload. Please verify all the cells in the infra"
                ebLogError(_msg)
                raise ExacloudRuntimeError(0x0811, 0xA, _msg)

    def mGetGridDisks(self, aCellList):
        _ebox = self.__cluctrl
        _cell_list = aCellList
        _list_all_griddisk = []
        for _cell_name in _cell_list:
            with connect_to_host(_cell_name, get_gcontext()) as _node:
                try:
                    _list_all_griddisk  += _ebox.mGetStorage().mListCellDG(_node)
                except Exception as e:
                    ebLogError(f"*** Exception Message Detail on host {_cell_name} {e}")
        return _list_all_griddisk

    #Update Storage VlanId on all the cells when no grid disk detected in the cells
    def mUpdateStorageVlan(self, aOptions):
        _ebox = self.__cluctrl
        _csu = csUtil()
        _steplist = ["CREATE_CELL"]
        _exascale_attr = aOptions.jsonconf['exascale']
        _vlanId = _exascale_attr['storage_vlan_id']
        _cell_list = _exascale_attr['cell_list']
        _csConstants = _csu.mGetConstants(_ebox, False)

        if _ebox.mIsKVM() and _ebox.mIsExabm():
            _list_all_griddisk = self.mGetGridDisks(_cell_list)
            if not _list_all_griddisk:
                _ebox.mRestoreStorageVlan(_cell_list, _vlanId)
                _csu.mExecuteOEDAStep(_ebox, "CREATE_CELL", _steplist, aOedaStep=_csConstants.OSTP_CREATE_CELL)
            else:
                ebLogWarn("*** Griddisks are present in the cells. Updating storage vlanID on cells is not allowed.")
                for _cell in _cell_list:
                    self.mCheckStorageVlanID(_cell, _vlanId)

    def mPatchEFRack(self, aHostName, aCellType, aOptions):
        _hostname = aHostName
        _cell_type = aCellType
        _ebox = self.__cluctrl
        _uuid = _ebox.mGetUUID()
        _oeda_path = _ebox.mGetOedaPath()
        _patchconfig = _ebox.mGetPatchConfig()
        _savexmlpath = _oeda_path + '/exacloud.conf'
        _updatedxml = _savexmlpath + '/exascale_ef_' + _uuid + '.xml'
        _ebox.mExecuteLocal("/bin/mkdir -p {0}".format(_savexmlpath), aCurrDir=_ebox.mGetBasePath())
        _ebox.mExecuteLocal("/bin/cp {0} {1}".format(_patchconfig, _updatedxml), aCurrDir=_ebox.mGetBasePath())
        ebLogInfo("Apply oedacli commands to XML")

        _oedacli_bin = os.path.join(_oeda_path, 'oedacli')
        with TemporaryDirectory() as tmp_dir:
            _oedacli_mgr = OedacliCmdMgr(_oedacli_bin, tmp_dir)
            _oedacli_mgr.mUpdateEFRack(_updatedxml, _updatedxml, _hostname, _cell_type)
            _ebox.mUpdateInMemoryXmlConfig(_updatedxml, aOptions)
            ebLogInfo('ebCluCtrl: Saved patched Cluster Config: ' + _ebox.mGetPatchConfig())

    def mGetCellModel(self, aCell):
        _cell = aCell
        _ebox = self.__cluctrl
        _model = ""

        _cell_mac = _ebox.mGetMachines().mGetMachineConfig(_cell)
        if _cell_mac:
            _cell_id = _cell_mac.mGetMacId()
            _model = _ebox.mGetEsracks().mGetEsRackItem(_cell_id).mGetEsRackItemFamily()
            ebLogInfo(f'*** Cell {_cell} Exadata model: {_model}')
        return _model

    def mConfigureExascale(self, aOptions):
        _csu = csUtil()
        _steplist = ["XSCONFIG_STORAGE"]
        _inputjson = aOptions.jsonconf
        _exascale_attr = _inputjson['exascale']
        _cell_list = _exascale_attr['cell_list']
        _ebox = self.__cluctrl
        _escli = self.__escli
        _exadata_model_gt_X8 = False
        _csConstants = _csu.mGetConstants(_ebox, False)

        # Keys need to be pushed to OEDA WorkDir
        if not ebCluCmdCheckOptions(self.__cluctrl.mGetCmd(), ['nooeda']):
            ebLogInfo(f"Restore Keys to OEDA WorkDir")
            self.__cluctrl.mRestoreOEDASSHKeys(aOptions)

        #update the xml with the QinQ details
        self.mEnableXSService(aOptions)

        #Remove KVM Guest Machines from the XML
        self.mRemoveVmMachines(aOptions)

        # create cell disks and Flash Disks if not available on the cell servers
        self.mValidateAndCreateDisks(aOptions)

        #convert XML template to X11EF, if cell disks have extreme flash disks
        for _cell_name in _cell_list:
            _exadata_model = _ebox.mGetNodeModel(aHostName=_cell_name)
            if _ebox.mCompareExadataModel(_exadata_model, 'X8') >= 0:
                _exadata_model_gt_X8 = True

            if _escli.mIsEFRack(_cell_name) and _exadata_model_gt_X8:
                _cell_model = _ebox.mGetNodeModel(aHostName=_cell_name)
                _cell_type = _cell_model + "M" + "EF"
                ebLogInfo(f'*** Cell {_cell_name} Exadata model: {_cell_model} Cell Type: {_cell_type}')
                self.mPatchEFRack(_cell_name, _cell_type, aOptions)

        # For reimaged Dom0s, make sure node type is KVMHOST in imageinfo
        # i.e. Make sure QinQ is enabled.
        self.mEnableQinQIfNeeded(aOptions)

        _failedList = []
        #perform check to deduce if QinQ is enabled
        if not self.mCheckRoCEIPs(aOptions, _failedList):
            # execute command to enable QinQ
            ebLogInfo(f" *** Enabling QinQ on the Host Nodes {_failedList}. Host node will be restarted serially to handle that")
            self.mSetupRoCEIPs(aOptions, _failedList)
            _rc = self.mValidateGuest(aOptions, _failedList)# validate domU after rebooting of dom0s for QinQ enabling
            if _rc != 0:
                 ebLogError("*** DomU Validation failed after enabling QinQ")
                 return _rc

        #Update Storage vlan on the cells
        self.mUpdateStorageVlan(aOptions)

        #
        # OEDA step to be run for Config Storage for Exascale
        #
        _csu.mExecuteOEDAStep(self.__cluctrl, "XSCONFIG_STORAGE", _steplist, aOedaStep=_csConstants.OSTP_CONFIG_STORAGE)

        # Enable Auto File Encryption if not already enabled
        # Skip only if flag is set in exabox.conf
        _flag_encryption = "exascale_autofileencryption_disable"
        if str(get_gcontext().mGetConfigOptions().get(
            _flag_encryption, "False")).upper() == "TRUE":
            ebLogWarn(f"Auto File encryption has been skipped by exabox.conf flag '{_flag_encryption}'!")
        else:
            _rc = self.mEnableAutoFileEncryption(aOptions)
            if _rc:
                ebLogError(f"Failed to enable Auto File Encryption")
                return -1

    def mDeConfigureExascale(self, aOptions):
        _csu = csUtil()
        _steplist = ["XSCONFIG_KVM_HOSTS", "XSCONFIG_STORAGE"]
        _csConstants = _csu.mGetConstants(self.__cluctrl, False)


        # Keys need to be pushed to OEDA WorkDir
        if not ebCluCmdCheckOptions(self.__cluctrl.mGetCmd(), ['nooeda']):
            ebLogInfo(f"Restore Keys to OEDA WorkDir")
            self.__cluctrl.mRestoreOEDASSHKeys(aOptions)

        #Remove KVM Guest Machines from the XML
        self.mRemoveVmMachines(aOptions)
        #
        # OEDA undo step to be run for Config KVM host for exascale
        #
        _csu.mExecuteOEDAStep(self.__cluctrl, "XSCONFIG_KVM_HOSTS", _steplist, aOedaStep=_csConstants.OSTP_CONFIG_KVM_HOSTS, undo=True, dom0Lock = False)
        #
        # OEDA undo step to be run for Config Storage for Exascale
        #
        _csu.mExecuteOEDAStep(self.__cluctrl, "XSCONFIG_STORAGE", _steplist, aOedaStep=_csConstants.OSTP_CONFIG_STORAGE, undo=True, dom0Lock = False, aSkipFail=False, aOverride=True)

    #Configure XS config
    def mExecuteXSConfigOedaStep(self, aOptions):
        ebLogInfo(" *** mExecuteXSConfigOedaStep()>>")
        _undo = False
        if 'undo' not in aOptions:
            _undo = False
        elif str(aOptions.undo).lower() == "true":
            _undo = True
        else:
            _undo = False

        if not _undo:
            self.mConfigureExascale(aOptions)
        else: # undo
            self.mDeConfigureExascale(aOptions)

    #Validate DomUs after dom0 reboot for CRS running and Dbs running
    def mValidateGuest(self, aOptions, aFailedList):
        ebLogInfo(" *** mValidateGuest()>>")
        _ebox = self.__cluctrl
        _rc = -1
        if 'Dom0domUDetails' not in list(aOptions.jsonconf.keys()):
            ebLogInfo("Post validation cannot be done as the payload does not contain the domU details. Skipping Validation")
            return 0
        _domUList = []
        _domUAsmList = []
        _clusterDict = {}
        _domain_attr = aOptions.jsonconf["Dom0domUDetails"]
        for _dom0 in _domain_attr :
            if _dom0 not in aFailedList:
                continue
            _domUdetailList = _domain_attr[_dom0]["domuDetails"]
            for _domUdetail in _domUdetailList:
                if _domUdetail["clusterStorageType"] =="ASM":
                    _domUAsmList.append(_domUdetail["domuNatHostname"])
                    _clusterName = _domUdetail["clusterName"]
                    _clusterDict[_clusterName] = list(_clusterDict.get(_clusterName,""))
                    _clusterDict[_clusterName].append(_domUdetail["domuNatHostname"])
                _domUList.append(_domUdetail["domuNatHostname"])
                    #check if crs and dbs are up and all db instances are running
        _tvl = _ebox.mCheckConfigOption('crs_timeout')
        if _tvl is not None:
            _timeout_crs = int(_tvl) * 60
        else:
            _timeout_crs = 60*60
            #Default of 60 minute timeout
        for _domU in _domUList:
            _total_time = 0
            _check_itr  = 5
            while _total_time < _timeout_crs:
                ebLogInfo("*** Waiting for cluster services to come up...")
                _crs_started = _ebox.mCheckCrsUp(_domU)
                if _crs_started:
                    break
                time.sleep(_check_itr)
                _total_time += _check_itr
            
            if _crs_started:
                ebLogInfo("*** CRS has come up on %s"%(_domU))
                _total_time = 0
            else:
                _detail_error = "vmid: %s - CRS stack did not start after boot"%(_domU)
                ebLogError('***  Validation Failed. ' + _detail_error)
                _ebox.mUpdateErrorObject(gReshapeError['ERROR_CRS_START'],_detail_error)
                raise ExacloudRuntimeError(0x0811, 0xA, _detail_error)
        try:
            for _cluster in list(_clusterDict.keys()):
                #check if ASM is up for a given cluster
                ebLogInfo("*** Checking ASM for cluster " + _cluster)
                _domu_list = _clusterDict[_cluster]
                _ebox.mCheckAsmIsUp(_domu_list[0], _domu_list)
        except Exception as exp:
            _detail_error = f"Failed to validate ASM is running on {_cluster} : {exp}"
            ebLogError('***  Validation Failed. ' + _detail_error)
            _ebox.mUpdateErrorObject(gReshapeError['ERROR_DB_START'],_detail_error)
            raise ExacloudRuntimeError(0x0811, 0xA, _detail_error)   

        for _domU in _domUList:
            _total_time = 0
            _check_itr  = 5             

            while _total_time < _timeout_crs:
                ebLogInfo("*** Waiting for DB to come up...")
                _db_started = _ebox.mCheckDBIsUp(_domU, aExascale=True)
                if _db_started:
                    break
                time.sleep(_check_itr)
                _total_time += _check_itr
            
            if _db_started:
                ebLogInfo("*** DB has come up on %s"%(_domU))
            else:
                _detail_error = "vmid: %s - Database did not start after boot"%(_domU)
                ebLogError('***  Validation Failed. ' + _detail_error)
                _ebox.mUpdateErrorObject(gReshapeError['ERROR_DB_START'],_detail_error)
                raise ExacloudRuntimeError(0x0811, 0xA, _detail_error)
        
        ebLogInfo(" *** mValidateGuest() completed")
        _rc = 0
        return _rc

    # create cell disks and Flash Disks if not available on the cell servers
    def mValidateAndCreateDisks(self, aOptions):   
        ebLogInfo(" *** mValidateAndCreateDisks()>>")
        _csu = csUtil()
        _ebox = self.__cluctrl
        _steplist = ["CREATE_CELL"]
        _inputjson = aOptions.jsonconf
        _exascale_attr = _inputjson['exascale']
        _cell_list = _exascale_attr['cell_list']
        _csConstants = _csu.mGetConstants(_ebox, False)
        _create_celldisks = False
        for _cell in _cell_list:
            with connect_to_host(_cell, get_gcontext()) as _node:
                _cmd_str = "cellcli -e list celldisk attributes name,size where disktype in ('HardDisk','FlashDisk')"
                ebLogInfo("*** Executing the command - %s" % _cmd_str)
                _i, _o, _e = _node.mExecuteCmdCellcli(_cmd_str)
                _output = _o.readlines()
                if not _output:
                    _create_celldisks = True
                    break

        if _create_celldisks:
            ebLogInfo(f"*** Creating Celldisks...")
            _csu.mExecuteOEDAStep(_ebox, "CREATE_CELL", _steplist, aOedaStep=_csConstants.OSTP_CREATE_CELL)

    #Reshape storage pool
    def mExecuteXSConfigReshapePool(self, aOptions):
        ebLogInfo(" *** mExecuteXSConfigReshapePool()>>")
        _ret = -1
        _ebox = self.__cluctrl
        _escli = self.__escli
        _enable_xs_service = "false"
        _enable_xs_service = self.__cluctrl.mCheckConfigOption('enable_xs_service')
        if _enable_xs_service.lower() == "false":
            _msg = 'enable_xs_service flag is False. XS(Exascale) Service is disabled.'
            ebLogError(_msg)
            _ebox.mUpdateErrorObject(gExascaleError["ERROR_XS_DISABLED"], _msg)
            self.__cluctrl.mSetXS(False)
            return _ret
        _options = aOptions
        _inputjson = _options.jsonconf
        _ret = self.mCheckIfPoolResizable(aOptions)
        _data_d = {}
        _exascale_attr = _inputjson['exascale']
        _poolName = _exascale_attr['storage_pool']['name']
        if not _ret:
            _msg = f'Unable to resize the storage pool {_poolName}'
            ebLogError(_msg)
            _ebox.mUpdateErrorObject(gExascaleError["STORAGEPOOL_RESIZE_FAILED"], _msg)
            self._mUpdateRequestData(_ret,_data_d,_msg)
            raise ExacloudRuntimeError(0x0811, 0xA, _msg)
        
        _cell_list = _exascale_attr['cell_list']
        _cell = _cell_list[0]
        _poolsizeGB = _exascale_attr['storage_pool']['gb_size']
        _cell_map = {}
        _cell_disk_count = 0
        _poolsizeGBWithRedundancy = int(int(_poolsizeGB) * REDUNDANCY_FACTOR)
        for _cell in _cell_list:
            with connect_to_host(_cell, get_gcontext()) as _node:
                _cellcli_list_name = "cellcli -e list griddisk attributes name where name like \\'" + _poolName + ".*\\'"
                ebLogInfo("*** Executing the command - %s" % _cellcli_list_name)
                _in, _out, _err = _node.mExecuteCmd(_cellcli_list_name)
                _rc = int(_node.mGetCmdExitStatus())
                _output = None
                if _out:
                    _output = _out.readlines()
                if _rc !=0:
                    _error = _err.read()
                    _msg = f"*** cellcli Err on {_cell}. Error is {_error} Unable to resize the pool {_poolName}"
                    ebLogError(_msg)
                    _ebox.mUpdateErrorObject(gExascaleError["STORAGEPOOL_RESIZE_FAILED"], _msg)
                    self._mUpdateRequestData(_ret,_data_d,_msg)
                    raise ExacloudRuntimeError(0x0811, 0xA, _msg)
                if _output:
                    ebLogInfo(f"*** cellcli Output on {_cell} is {_output}")
                    _cell_map[_cell] = _output
                    _cell_disk_count += len(_output)
        _new_griddisk_size = self.mCalculateNewGridDiskSize(_poolsizeGBWithRedundancy, len(_cell_list), _cell_disk_count)
        _ret = self.mRunResizeGridDisk(_new_griddisk_size, _cell_map)
        if _ret:
            _msg = f'Unable to resize the pool {_poolName} as resize griddisk to new size failed'
            ebLogError(_msg)
            _ebox.mUpdateErrorObject(gExascaleError["STORAGEPOOL_RESIZE_FAILED"], _msg)
            self._mUpdateRequestData(_ret,_data_d,_msg)
            raise ExacloudRuntimeError(0x0811, 0xA, _msg)

        # Resize storage pool
        _ret, _out, _err = _escli.mReconfigStoragePool(_cell, _poolName, aOptions)
        if _ret:
            _msg = f'Unable to resize the pool {_poolName} as escli command failed with error:{_err}'
            ebLogError(_msg)
            _ebox.mUpdateErrorObject(gExascaleError["STORAGEPOOL_RESIZE_FAILED"], _msg)
            self._mUpdateRequestData(_ret,_data_d,_msg)
            raise ExacloudRuntimeError(0x0811, 0xA, _msg)
        return _ret

    def mCalculateNewGridDiskSize(self, aNewPoolSizeGB, aCellCount, aCellDiskCount):
        ebLogInfo(" *** mCalculateNewGridDiskSize()>>")
        _ebox = self.__cluctrl
        _data_d = {}
        _pool_size_new = aNewPoolSizeGB
        _total_griddisk_count = None
        _disk_per_cell = int(aCellDiskCount)/int(aCellCount)
        ebLogInfo(f" *** Cell disk count per cell is {_disk_per_cell}")
        if _disk_per_cell in [6, 8, 12]:
             _total_griddisk_count = aCellDiskCount
        else:
            _msg = f'Unable to resize the pool as the total cell disk count of {aCellDiskCount} on {aCellCount} cells is not proper'
            ebLogError(_msg)
            _ebox.mUpdateErrorObject(gExascaleError["STORAGEPOOL_RESIZE_FAILED"], _msg)
            self._mUpdateRequestData(-1,_data_d,_msg)
            raise ExacloudRuntimeError(0x0811, 0xA, _msg)
        _newsize_per_griddisk_mb = float(_pool_size_new/_total_griddisk_count) * 1024
        _newsize_per_griddisk_mb = math.floor(_newsize_per_griddisk_mb / 16) * 16
        ebLogInfo(f" *** new size per grid is {_newsize_per_griddisk_mb}")
        return _newsize_per_griddisk_mb

    def mRunResizeGridDisk(self, aNewSize, aCellMap):
        ebLogInfo(" *** mRunResizeGridDisk()>>")
        _ret = 0
        for _cell in aCellMap:
            with connect_to_host(_cell.strip(), get_gcontext()) as _node:
                for _griddisk in aCellMap[_cell]:
                    _cmd = f"cellcli -e ALTER GRIDDISK {_griddisk.strip()} SIZE={aNewSize}M"
                    ebLogInfo(f"Command to be executed is: {_cmd}")
                    _node.mExecuteCmdLog(_cmd)
                    if _node.mGetCmdExitStatus() != 0:
                        _ret = -1
        return _ret

    # check if storage pool is resizable to given value 
    def mCheckIfPoolResizable(self, aOptions):
        ebLogInfo(" *** mGetCurrentStoragePoolSize()>>")
        _options = aOptions
        _ebox = self.__cluctrl
        _escli = self.__escli
        _usedSpaceGb= None
        _provisionableSpaceGb= None
        _currentprovisionedSpaceGb = None
        _inputjson = _options.jsonconf
        _exascale_attr = _inputjson['exascale']
        _poolName = _exascale_attr['storage_pool']['name']
        _poolsizeGB = _exascale_attr['storage_pool']['gb_size']
        _poolsizeGBWithRedundancy = int(int(_poolsizeGB) * REDUNDANCY_FACTOR)
        _cell_list = _exascale_attr['cell_list']
        _cell = _cell_list[0]
        _data_d = {}

        _ret, _out, _err = _escli.mCurrentStoragePoolSize(_cell, _poolName, aOptions)
        if _ret != 0:
            _msg = f'Unable to get current Storage Pool {_poolName} size due to {_err}. Output is {_out}'
            ebLogError(_msg)
            _ebox.mUpdateErrorObject(gExascaleError["STORAGEPOOL_RESIZE_FAILED"], _msg)
            self._mUpdateRequestData(_ret,_data_d,_msg)
            raise ExacloudRuntimeError(0x0811, 0xA, _msg)
        else:
            _json = ''.join( _out.splitlines())
            if _json[0] == '{':
                _jsonOut = json.loads(_json)
                _usedSpaceGb = float(_jsonOut['data']['attributes']['spaceUsed'])
                if _usedSpaceGb > 0:
                    _usedSpaceGb= float(float(_jsonOut["data"]["attributes"]["spaceUsed"])/(1024*1024*1024))
                _provisionableSpaceGb = float(float(_jsonOut['data']['attributes']['spaceProvisionable'])/(1024*1024*1024))
                _currentprovisionedSpaceGb = float(float(_jsonOut['data']['attributes']['spaceProvisioned'])/(1024*1024*1024))
                ebLogInfo(f"*** spaceProvisionable={_provisionableSpaceGb}, spaceProvisioned={_currentprovisionedSpaceGb}, spaceUsed={_usedSpaceGb}")
        _storage_config = ebCluStorageConfig(self.mGetCluCtrl(), self.mGetCluCtrl().mGetConfig())
        (_total_space_output_GB, _free_space_output_GB) = _storage_config.mListCellDisksSize(_cell_list)
        ebLogInfo(f" ***  Total space on the cells={_total_space_output_GB}GB, Total free Space on the cells ={_free_space_output_GB}GB")
        _expandPool = False
        if float(_poolsizeGBWithRedundancy) >  _provisionableSpaceGb:
            _expandPool = True
        if float(_poolsizeGBWithRedundancy) == _provisionableSpaceGb:
            ebLogInfo(" *** storage pool is already at the requested value")
            return True
        if _expandPool and float(_poolsizeGBWithRedundancy - _provisionableSpaceGb) <= _free_space_output_GB :
            ebLogInfo(" *** storage pool is up sizable to given value")
            return True
        if  not _expandPool and float(_poolsizeGBWithRedundancy) >= _currentprovisionedSpaceGb:
            ebLogInfo(" *** storage pool is down sizable to given value")
            return True
        else:
            ebLogError(" *** storage pool is not resizable to given value")
            return False

    def mCreateDefaultAcfs(self, aOptions):
        _ebox = self.__cluctrl
        _dpairs = _ebox.mReturnDom0DomUPair()
        _, _domU = _dpairs[0]
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _gihome, _, _ora_base = _ebox.mGetOracleBaseDirectories(aDomU = _domU)
        _acfs_id = self.mRegisterACFS(_cell, aOptions)
        self.mValidateAcfs(_domU, _gihome, aOptions)

    def mRegisterACFS(self, aCell, aOptions):
        _cell = aCell
        _ebox = self.__cluctrl
        _escli = self.__escli
        _acfs_vol_size = _ebox.mCheckConfigOption('xs_acfs_vol_size')
        _gi_clustername, _gi_cluster_id = _escli.mGetClusterID(_cell, aOptions)
        _acfs_volname = "vol" + "_" + _gi_clustername
        _acfs_name = "acfs" + "_" + _gi_clustername
        _acfs_id = ""

        #Create EDV Volume
        _rc = _escli.mCreateEDVVolume(_cell, _acfs_vol_size, _acfs_volname, aOptions)
        if _rc == 0:
            _vol_id, _ = _escli.mGetVolumeID(_cell, _acfs_volname, aOptions)
            ebLogInfo(f"Created acfs volume with id {_vol_id}")

            if _vol_id:
                #Create EDV Volume Attachment
                _rc = _escli.mCreateEDVVolumeAttachment(_cell, _vol_id, "xacfsvol", _gi_cluster_id, _gi_clustername, aOptions)
                _vol_attach, _volume, _device_name = _escli.mGetVolumeAttachments(_cell, _vol_id, aOptions)
                ebLogInfo(f"Created edv attachment with id {_vol_attach}")

                #Create ACFS FileSystem
                _escli.mCreateACFSFileSystem(_cell, _vol_id, "/var/opt/oracle/dbaas_acfs", _acfs_name, _gi_clustername, aOptions)
                _acfs_id, _, _ = _escli.mGetACFSFileSystem(_cell, _vol_id, aOptions)
        return _acfs_id

    def mCreateACFS(self, aOptions):
        _cell = ""
        _acfs_id = ""
        _acfs_list = []
        _gi_clustername = ""
        _gi_cluster_id = ""
        _ebox = self.__cluctrl
        _escli = self.__escli

        if aOptions is not None and aOptions.jsonconf is not None and \
               "exascale" in list(aOptions.jsonconf.keys()):
            _exascale_attr = aOptions.jsonconf['exascale']
            _cell_list = _exascale_attr['cell_list']
            _cell = _cell_list[0]
            _gi_clustername, _gi_cluster_id = _escli.mGetClusterID(_cell, aOptions)

        if aOptions is not None and aOptions.jsonconf is not None and \
               "acfs" in list(aOptions.jsonconf.keys()):
            _acfs_list = aOptions.jsonconf["acfs"]

        for _acfs in _acfs_list:
            _acfs_name = _acfs['name']
            _acfs_size = str(_acfs['gb_size']) + "GB"
            _mount_path = "/" + _acfs['mount_path']
            _acfs_vol = "vol_" + _acfs_name
            _device_name = "dev_" + _acfs_name

            #Create EDV Volume
            _rc = _escli.mCreateEDVVolume(_cell, _acfs_size, _acfs_vol, aOptions)
            if _rc == 0:
                _vol_id, _ = _escli.mGetVolumeID(_cell, _acfs_vol, aOptions)
                ebLogInfo(f"Created acfs volume with id {_vol_id}")

                if _vol_id:
                    #Create EDV Volume Attachment
                    _rc = _escli.mCreateEDVVolumeAttachment(_cell, _vol_id, _device_name, _gi_cluster_id, _gi_clustername, aOptions)
                    _vol_attach, _volume, _device_name = _escli.mGetVolumeAttachments(_cell, _vol_id, aOptions)
                    ebLogInfo(f"Created edv attachment with id {_vol_attach}")

                    #Create ACFS FileSystem
                    _escli.mCreateACFSFileSystem(_cell, _vol_id, _mount_path, _acfs_name, _gi_clustername, aOptions)
                    _acfs_id, _, _ = _escli.mGetACFSFileSystem(_cell, _vol_id, aOptions)

    def mResizeACFS(self, aOptions):
        _cell = ""
        _acfs_id = ""
        _acfs_list = []
        _clusterName = ""
        _ebox = self.__cluctrl
        _escli = self.__escli

        _dpairs = _ebox.mReturnDom0DomUPair()
        _, _domU = _dpairs[0]

        if aOptions is not None and aOptions.jsonconf is not None and \
               "exascale" in list(aOptions.jsonconf.keys()):
            _exascale_attr = aOptions.jsonconf['exascale']
            _cell_list = _exascale_attr['cell_list']
            _cell = _cell_list[0]

        if aOptions is not None and aOptions.jsonconf is not None and \
               "acfs" in list(aOptions.jsonconf.keys()):
            _acfs_list = aOptions.jsonconf["acfs"]

        if not _ebox.mIsOciEXACC() and 'rack' in list(aOptions.jsonconf.keys()) \
            and 'name' in list(aOptions.jsonconf['rack'].keys()):
            _clusterName = "grid" + aOptions.jsonconf['rack']['name']
            ebLogInfo(f"Fetching the Cluster name:{_clusterName} from input payload")
        else:
            _clusterName = "grid" + _ebox.mGetClusters().mGetCluster().mGetCluName()
            ebLogInfo(f"Fetching the Cluster name:{_clusterName} from XML")

        for _acfs in _acfs_list:
            _acfs_name = _acfs['name']
            _acfs_size = str(_acfs['gb_size']) + "GB"
            _acfs_vol = "vol_" + _acfs_name
            _mount_path = "/" + _acfs['mount_path']

            _vol_id, _ = _escli.mGetVolumeID(_cell, _acfs_vol, aOptions)
            _escli.mChangeVolume(_cell, _vol_id, _clusterName, aOptions)

            #Resize ACFS File System
            with connect_to_host(_domU, get_gcontext(), username="root") as _node:
                _cmd_str = f'/usr/sbin/acfsutil size {_acfs_size} {_mount_path}'
                _node.mExecuteCmdLog(_cmd_str)
                _rc = _node.mGetCmdExitStatus()
        return _rc

    def mMountACFS(self, aOptions):
        _cell = ""
        _acfs_id = ""
        _acfs_list = []
        _ebox = self.__cluctrl
        _escli = self.__escli

        if aOptions is not None and aOptions.jsonconf is not None and \
               "exascale" in list(aOptions.jsonconf.keys()):
            _exascale_attr = aOptions.jsonconf['exascale']
            _cell_list = _exascale_attr['cell_list']
            _cell = _cell_list[0]
            _gi_clustername, _gi_cluster_id = _escli.mGetClusterID(_cell, aOptions)

        if aOptions is not None and aOptions.jsonconf is not None and \
               "acfs" in list(aOptions.jsonconf.keys()):
            _acfs_list = aOptions.jsonconf["acfs"]

        for _acfs in _acfs_list:
            _acfs_name = _acfs['name']
            _mount_path = "/" + _acfs['mount_path']
            _acfs_vol = "vol_" + _acfs_name

            _vol_id, _ = _escli.mGetVolumeID(_cell, _acfs_vol, aOptions)
            if _vol_id:
                _escli.mMountACFSFileSystem(_cell, _vol_id, _mount_path, _gi_clustername, aOptions)

    def mUnMountACFS(self, aOptions):
        _cell = ""
        _acfs_id = ""
        _acfs_list = []
        _ebox = self.__cluctrl
        _escli = self.__escli

        if aOptions is not None and aOptions.jsonconf is not None and \
               "exascale" in list(aOptions.jsonconf.keys()):
            _exascale_attr = aOptions.jsonconf['exascale']
            _cell_list = _exascale_attr['cell_list']
            _cell = _cell_list[0]

        if aOptions is not None and aOptions.jsonconf is not None and \
               "acfs" in list(aOptions.jsonconf.keys()):
            _acfs_list = aOptions.jsonconf["acfs"]

        for _acfs in _acfs_list:
            _acfs_name = _acfs['name']
            _acfs_vol = "vol_" + _acfs_name

            _vol_id, _ = _escli.mGetVolumeID(_cell, _acfs_vol, aOptions)
            if _vol_id:
                _acfs_id, _, _ = _escli.mGetACFSFileSystem(_cell, _vol_id, aOptions)
                if _acfs_id:
                    _escli.mUnMountACFSFileSystem(_cell, _acfs_id, aOptions)

    def mGetACFSSize(self, aOptions):
        _ebox = self.__cluctrl
        _escli = self.__escli
        _data_d = {}
        _size = ""
        _ret = 0
        _res_list = []

        if aOptions is not None and aOptions.jsonconf is not None and \
               "exascale" in list(aOptions.jsonconf.keys()):
            _exascale_attr = aOptions.jsonconf['exascale']
            _cell_list = _exascale_attr['cell_list']
            _cell = _cell_list[0]

        if aOptions is not None and aOptions.jsonconf is not None and \
               "acfs" in list(aOptions.jsonconf.keys()):
            _acfs_list = aOptions.jsonconf["acfs"]

        for _acfs in _acfs_list:
            _mount_path = ""
            _acfs_name = _acfs['name']
            _acfs_vol = "vol_" + _acfs_name

            _vol_id, _ = _escli.mGetVolumeID(_cell, _acfs_vol, aOptions)
            if _vol_id:
                _, _mount_path, _size_str = _escli.mGetACFSFileSystem(_cell, _vol_id, aOptions)
                if _size_str:
                    _size_list = re.findall(r'\d+(?:\.\d+)?|\w+', _size_str)
                    _size_gb = math.ceil(float(_size_list[0]))
                _res_list.append({"name": _acfs_name, "gb_size": _size_gb, "mount_path": _mount_path})
        _data_d["acfs"] = _res_list
        ebLogInfo(f"ACFS Size: {_data_d}")
        self._mUpdateRequestData(_ret, _data_d, "")
        return _data_d

    def mRemoveACFSFileSystem(self, aCell, aAcfsName, aOptions):
        _cell = aCell
        _acfs_name = aAcfsName
        _escli = self.__escli

        _acfs_volname = "vol_" + _acfs_name
        _vol_id, _ = _escli.mGetVolumeID(_cell, _acfs_volname, aOptions)
        if _vol_id:
            _vol_attach, _, _ = _escli.mGetVolumeAttachments(_cell, _vol_id, aOptions)
            _acfs_id, _, _ = _escli.mGetACFSFileSystem(_cell, _vol_id, aOptions)

            if _acfs_id:
                _escli.mUnMountACFSFileSystem(_cell, _acfs_id, aOptions)
                _escli.mRemoveACFSFileSystem(_cell, _acfs_id, aOptions)
            if _vol_attach:
                _escli.mRemoveEDVAttachment(_cell, aOptions, _vol_attach, aForce=True)
            if _vol_id:
                _escli.mRemoveEDVVolume(_cell, _vol_id, aOptions)

    def mRemoveACFS(self, aOptions):
        _acfs_list = []

        if aOptions is not None and aOptions.jsonconf is not None and \
               "exascale" in list(aOptions.jsonconf.keys()):
            _exascale_attr = aOptions.jsonconf['exascale']
            _cell_list = _exascale_attr['cell_list']
            _cell = _cell_list[0]

        if aOptions is not None and aOptions.jsonconf is not None and \
               "acfs" in list(aOptions.jsonconf.keys()):
            _acfs_list = aOptions.jsonconf["acfs"]

        for _acfs in _acfs_list:
            _acfs_name = _acfs['name']
            self.mRemoveACFSFileSystem(_cell, _acfs_name, aOptions)

    def mRemoveAcfsDir(self):
        _ebox = self.__cluctrl
        _dpairs = _ebox.mReturnDom0DomUPair()

        try:
            for _, _domU in _dpairs:
                if not _ebox.mPingHost(_domU):
                    ebLogWarn(f'*** Host ({_domU}) is not pingable, thus skipping.')
                    continue
                #Remove acfs directory
                with connect_to_host(_domU, get_gcontext(), username="root") as _node:
                    _node.mExecuteCmdLog("/bin/rm -rf /var/opt/oracle/dbaas_acfs/")
        except Exception as e:
            ebLogWarn(f"*** mRemoveAcfsDir failed with Exception: {str(e)}")

    def mValidateAcfs(self, aDomU, aGIHome, aOptions):
        _ebox = self.__cluctrl
        _escli = self.__escli
        _domU = aDomU
        _gihome = aGIHome
        try:
            if aOptions is not None and aOptions.jsonconf is not None and \
               "exascale" in list(aOptions.jsonconf.keys()):
                _exascale_attr = aOptions.jsonconf['exascale']
                _vault_name = _exascale_attr['db_vault']['name'].strip()
        except Exception as e:
            ebLogWarn(f"*** mValidateAcfs failed with Exception: {str(e)}")
            _vault_name = _escli.mGetDBVaultName()

        if not _gihome:
            _gihome, _, _ = _ebox.mGetOracleBaseDirectories(aDomU = _domU)

        with connect_to_host(_domU, get_gcontext(), username="root") as _node:
            _cmd_str = f"{_gihome}/bin/crsctl stat res ora.dbaasfs.type | /bin/grep STATE |  /bin/cut -f 2 -d '=' "
            _i, _o, _e = _node.mExecuteCmd(_cmd_str)
            _out = _o.readlines()
            if _out:
                _dbaasfs_state = [_line.strip() for _line in _out[0].strip().split(',')]
                if 'OFFLINE' in _dbaasfs_state:
                    _detail_error = "*** Error: ora.dbaasfs.type is in OFFLINE state"
                    ebLogError(f"{_detail_error}")
                    _ebox.mUpdateErrorObject(gExascaleError["ATTACH_ACFS_VOLUME_FAILED"], _detail_error)
                    raise ExacloudRuntimeError(aErrorMsg=_detail_error)

            _cmd_str = f"{_gihome}/bin/crsctl stat res ora.{_vault_name}.{DEVICE_NAME}.acfs | /bin/grep STATE |  /bin/cut -f 2 -d '=' "
            _i, _o, _e = _node.mExecuteCmd(_cmd_str)
            _out = _o.readlines()
            if _out:
                _xacfsvol_state = [_line.strip() for _line in _out[0].strip().split(',')]
                if 'OFFLINE' in _xacfsvol_state:
                    _detail_error = "*** Error: ora.{_vault_name}.{DEVICE_NAME}.acfs is in OFFLINE state"
                    ebLogError(f"{_detail_error}")
                    _ebox.mUpdateErrorObject(gExascaleError["ATTACH_ACFS_VOLUME_FAILED"], _detail_error)
                    raise ExacloudRuntimeError(aErrorMsg=_detail_error)

            _cmd_str = "/usr/bin/df -Th | /bin/grep acfs"
            _node.mExecuteCmdLog(_cmd_str)
            _rc = _node.mGetCmdExitStatus()
            if _rc:
                _err_str = f"{_domU}: Error while running the command:{_cmd_str}"
                ebLogError(_err_str)
                _ebox.mUpdateErrorObject(gExascaleError["ATTACH_ACFS_VOLUME_FAILED"], _err_str)
                raise ExacloudRuntimeError(aErrorMsg=_err_str)

            _cmd_str = f"/usr/sbin/edvutil volinfo {ACFS_VOL}"
            _node.mExecuteCmdLog(_cmd_str)
            _rc = _node.mGetCmdExitStatus()
            if _rc:
                _err_str = f"{_domU}: Error while running the command:{_cmd_str}"
                ebLogError(_err_str)
                _ebox.mUpdateErrorObject(gExascaleError["ATTACH_ACFS_VOLUME_FAILED"], _err_str)
                raise ExacloudRuntimeError(aErrorMsg=_err_str)

    def mRemoveDefaultAcfsVolume(self, aOptions):
        self.mUnRegisterACFS(aOptions)
        self.mDetachAcfsVolume(aOptions)
        self.mRemoveAcfsDir()

    def mUnRegisterACFS(self, aOptions):
        _ebox = self.__cluctrl
        _escli = self.__escli
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        if not _ebox.mIsOciEXACC() and 'rack' in list(aOptions.jsonconf.keys()) \
            and 'name' in list(aOptions.jsonconf['rack'].keys()):
            _clusterName = aOptions.jsonconf['rack']['name']
            ebLogInfo(f"Fetching the Cluster name:{_clusterName} from input payload")
        else:
            _clusterName = _ebox.mGetClusters().mGetCluster().mGetCluName()
            ebLogInfo(f"Fetching the Cluster name:{_clusterName} from XML")

        try:
            _gi_clustername, _ = _escli.mGetClusterID(_cell, aOptions)
            if _gi_clustername:
                _acfs_volname = "vol" + "_" + _gi_clustername
                _volume_id, _ = _escli.mGetVolumeID(_cell, _acfs_volname, aOptions)
            else:
                _gi_clustername = _escli.mGetUser(_cell, _clusterName, aOptions)
                _acfs_volname = "vol" + "_" + _gi_clustername
                _volume_id, _ = _escli.mGetVolumeID(_cell, _acfs_volname, aOptions)
            if _volume_id:
                _acfs_id, _, _ = _escli.mGetACFSFileSystem(_cell, _volume_id, aOptions)
                if _acfs_id:
                    _escli.mUnMountACFSFileSystem(_cell, _acfs_id, aOptions)
                    _escli.mRemoveACFSFileSystem(_cell, _acfs_id, aOptions)
        except Exception as e:
            ebLogWarn(f"*** mUnRegisterACFS failed with Exception: {str(e)}")

    def mDetachAcfsVolume(self, aOptions, aForce=False):
        _force = aForce
        _ebox = self.__cluctrl
        _escli = self.__escli
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        if not _ebox.mIsOciEXACC() and 'rack' in list(aOptions.jsonconf.keys()) \
            and 'name' in list(aOptions.jsonconf['rack'].keys()):
            _clusterName = aOptions.jsonconf['rack']['name']
            ebLogInfo(f"Fetching the Cluster name:{_clusterName} from input payload")
        else:
            _clusterName = _ebox.mGetClusters().mGetCluster().mGetCluName()
            ebLogInfo(f"Fetching the Cluster name:{_clusterName} from XML")

        _gi_clustername, _ = _escli.mGetClusterID(_cell, aOptions)
        if _gi_clustername:
            _acfs_volname = "vol" + "_" + _gi_clustername
            _volume_id, _ = _escli.mGetVolumeID(_cell, _acfs_volname, aOptions)
        else:
            _gi_clustername = _escli.mGetUser(_cell, _clusterName, aOptions)
            _acfs_volname = "vol" + "_" + _gi_clustername
            _volume_id, _ = _escli.mGetVolumeID(_cell, _acfs_volname, aOptions)

        _vol_attach, _, _ = _escli.mGetVolumeAttachments(_cell, _volume_id, aOptions)

        #Remove EDV volume attachment
        if _vol_attach:
            _escli.mRemoveEDVAttachment(_cell, aOptions, _vol_attach, aForce=_force)

            _timeout = _ebox.mCheckConfigOption('volume_detach_timeout')
            if _timeout is not None:
                _timeout_rmvolume = int(_timeout)
            else:
                _timeout_rmvolume = 600
            time.sleep(_timeout_rmvolume)

        if _volume_id:
            #Remove EDV volume
            _escli.mRemoveEDVVolume(_cell, _volume_id, aOptions)

    def mDeleteFilesInDbVault(self, aOptions):
        _ebox = self.__cluctrl
        _escli = self.__escli
        try:
            if aOptions is not None and aOptions.jsonconf is not None and \
               "exascale" in list(aOptions.jsonconf.keys()):
                _exascale_attr = aOptions.jsonconf['exascale']
                _vault_name = _exascale_attr['db_vault']['name'].strip()
                _ctrl_ip = _exascale_attr['ctrl_network']['ip'].strip()
                _ctrl_port = _exascale_attr['ctrl_network']['port'].strip()
        except Exception as e:
            ebLogWarn(f"*** mDeleteFilesInDbVault failed with Exception: {str(e)}")
            _vault_name = _escli.mGetDBVaultName()
            _ctrl_ip, _ = _escli.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        if not _ebox.mIsOciEXACC() and 'rack' in list(aOptions.jsonconf.keys()) \
            and 'name' in list(aOptions.jsonconf['rack'].keys()):
            _clusterName = aOptions.jsonconf['rack']['name']
            ebLogInfo(f"Fetching the Cluster name:{_clusterName} from input payload")
        else:
            _clusterName = _ebox.mGetClusters().mGetCluster().mGetCluName()
            ebLogInfo(f"Fetching the Cluster name:{_clusterName} from XML")

        _vault = "@" + _vault_name
        _cluster = _clusterName.upper()
        _files = f"{_vault}/{_cluster}*"
        _escli.mRemoveFile(_cell, _files, aOptions, aForce=True)

    def mCreateU02Volume(self, aHost, aVolName, aSize, aOptions):
        _host = aHost
        _u02_volname = aVolName
        _u02_size = aSize
        _system_vault = ""
        _device_path = ""
        _ebox = self.__cluctrl
        _escli = self.__escli
        try:
            if aOptions is not None and aOptions.jsonconf is not None and \
               "exascale" in list(aOptions.jsonconf.keys()):
                _exascale_attr = aOptions.jsonconf['exascale']
                _ctrl_ip = _exascale_attr['ctrl_network']['ip'].strip()
                _ctrl_port = _exascale_attr['ctrl_network']['port'].strip()
        except Exception as e:
            ebLogWarn(f"*** mCreateU02Volume failed with Exception: {str(e)}")
            _ctrl_ip, _ = _escli.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _system_vault = self.mGetVaultName(aOptions, aVaultType="image")

        #Create U02 EDV Volume
        _rc = _escli.mCreateEDVVolume(_cell, _u02_size, _u02_volname, aOptions, aVaultName=_system_vault)
        if _rc == 0:
            _vol_id, _ = _escli.mGetVolumeID(_cell, _u02_volname, aOptions, aVaultName=_system_vault)
            ebLogInfo(f"Created volume with id {_vol_id}")

            _initiatorId = _escli.mGetEDVInitiator(_cell, _host, aOptions)
            _device_name = _u02_volname + "_" + _vol_id.split(":")[-1].split("_")[-1]

            #Create EDV Volume Attachment
            _rc = _escli.mCreateEDVVolumeAttachment(_cell, _vol_id, _device_name, None, _host, aOptions, aInitiatorID=_initiatorId)
            _id, _volume, _device_name = _escli.mGetVolumeAttachments(_cell, _vol_id, aOptions)
            _device_path = "/dev/exc/" + _device_name
            ebLogInfo(f"Created edv attachment with id {_id} with device path {_device_path}")
        return _device_path

    def mResizeEDVVolume(self, aVolName, aSize, aOptions=None):
        _volname = aVolName
        _size = aSize
        _system_vault = ""
        _device_path = ""
        _ebox = self.__cluctrl
        _escli = self.__escli
        try:
            if aOptions is not None and aOptions.jsonconf is not None and \
               "exascale" in list(aOptions.jsonconf.keys()):
                _exascale_attr = aOptions.jsonconf['exascale']
                _ctrl_ip = _exascale_attr['ctrl_network']['ip'].strip()
                _ctrl_port = _exascale_attr['ctrl_network']['port'].strip()
        except Exception as e:
            ebLogWarn(f"*** mResizeEDVVolume failed with Exception: {str(e)}")
            _ctrl_ip, _ = _escli.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _vol_id, _ = _escli.mGetVolumeID(_cell, _volname, aOptions)
        _escli.mResizeEDVVolume(_cell, _size, _vol_id, aOptions)

    def mRemoveGuestEDVVolume(self, aHost, aVolName, aOptions):
        _host = aHost
        _vol_name =  aVolName
        _ebox = self.__cluctrl
        _escli = self.__escli
        try:
            if aOptions is not None and aOptions.jsonconf is not None and \
               "exascale" in list(aOptions.jsonconf.keys()):
                _exascale_attr = aOptions.jsonconf['exascale']
                _ctrl_ip = _exascale_attr['ctrl_network']['ip'].strip()
                _ctrl_port = _exascale_attr['ctrl_network']['port'].strip()
        except Exception as e:
            ebLogWarn(f"*** mRemoveU02Volume failed with Exception: {str(e)}")
            _ctrl_ip, _ = _escli.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _system_vault = self.mGetVaultName(aOptions, aVaultType="image")
        _vol_id, _ = _escli.mGetVolumeID(_cell, _vol_name, aOptions, aVaultName=_system_vault)
        if _vol_id:
            _vol_attach, _, _ = _escli.mGetVolumeAttachments(_cell, _vol_id, aOptions)
            _escli.mRemoveEDVAttachment(_cell, aOptions, _vol_attach, aForce=True)
            _escli.mRemoveEDVVolume(_cell, _vol_id, aOptions)
        else:
            ebLogInfo(f"Volume {_vol_name} not existing. Skipping Removing U02 Volume")

    def mUpdateVLanId(self, aOptions):
        ebLogInfo(f"*** mUpdateVLanId >>>")
        _ebox = self.__cluctrl
        _remote_path = "/opt/oracle.cellos/cell.conf"
        _remote_target_path = "/opt/oracle.cellos/cell.conf.new"
        _local_path = "/tmp/cell.conf.new"
        _reshape_config = aOptions.jsonconf['reshaped_node_subset']
        _exascale_attr = aOptions.jsonconf['exascale']
        _vlan_id = str(_exascale_attr['storage_vlan_id'])
        _remote_vlan_id = 0
        _add_cell_list=[]
        for _cell in _reshape_config['added_cells']:
            _add_cell_list.append(_cell['cell_hostname'])
        for _cell in _add_cell_list:
            with connect_to_host(_cell, get_gcontext()) as _node:
                _get_vlan_cmd = "/usr/bin/grep -i '^VLAN:' /etc/exadata/config/initqinq.conf | /usr/bin/awk '{print $2}'"
                if not _node.mFileExists(_remote_path):
                    _msg = f'Unable to find the file {_remote_path} on {_cell}'
                    ebLogError(_msg)
                    _ebox.mUpdateErrorObject(gExascaleError["SET_VLANID_FAILED"], _msg)
                    raise ExacloudRuntimeError(0x0811, 0xA, _msg)
                _i, _o, _e = _node.mExecuteCmd(_get_vlan_cmd)
                _out = _o.readlines()
                if _out :
                    _remote_vlan_id = str(_out[0].strip())
                if _remote_vlan_id == _vlan_id:
                    #skip updating the value
                    ebLogInfo(f'VlanID on {_cell} is already configured with value {_vlan_id}. Will skip the vlan id update on the cell')
                    continue
                _node.mCopy2Local(_remote_path, _local_path)
                self.update_xml_tag(_local_path,"Qinq_vlan_id", _vlan_id)
                _node.mCopyFile(_local_path, _remote_target_path)
                _cmd = f'/usr/local/bin/ipconf -force -newconf {_remote_target_path}'
                _node.mExecuteCmdLog(_cmd)
                _ret = _node.mGetCmdExitStatus()
                if _ret != 0:
                    _msg = f'Unable to configure the cell {_cell} with VLANID {_vlan_id} '
                    ebLogError(_msg)
                    _ebox.mUpdateErrorObject(gExascaleError["SET_VLANID_FAILED"], _msg)
                    raise ExacloudRuntimeError(0x0811, 0xA, _msg)
                else:
                    ebLogInfo(f'VlanID on {_cell} is configured with value {_vlan_id}. Will reboot the node now')
                    _ebox.mRebootNode(_cell)

    def update_xml_tag(self, file_path, tag_name, new_value, output_path=None):
        """
        Updates the value of a specific tag in an XML file and writes it back to the file.
        :param file_path: Path to the XML file.
        :param tag_name: Name of the tag to update.
        :param new_value: New value for the tag.
        :param output_path: Path to save the updated XML. Defaults to overwriting the original file.
        """
        _ebox = self.__cluctrl
        try:
            # Parse the XML file
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Find and update the tag
            found = False
            for elem in root.iter(tag_name):
                elem.text = new_value
                found = True

            if not found:
                _msg = f'Unable to find the tag {tag_name} in {file_path}'
                ebLogError(_msg)
                _ebox.mUpdateErrorObject(gExascaleError["SET_VLANID_FAILED"], _msg)
                raise ExacloudRuntimeError(0x0811, 0xA, _msg)

            # Save the updated XML
            if not output_path:
                output_path = file_path
            tree.write(output_path, encoding='utf-8', xml_declaration=True)
            ebLogInfo(f"Tag '{tag_name}' updated successfully. File saved to {output_path}.")
        except Exception as e:
            _msg = f"An error occurred: {e}"
            ebLogError(_msg)
            _ebox.mUpdateErrorObject(gExascaleError["SET_VLANID_FAILED"], _msg)
            raise ExacloudRuntimeError(0x0811, 0xA, _msg)

    def mCheckXSEnabled(self):
        _ebox = self.__cluctrl
        _xs_enabled = False
        for _cell in _ebox.mReturnCellNodes().keys():
            with connect_to_host(_cell, get_gcontext()) as _node:
                _cmd = "cellcli -e list griddisk ATTRIBUTES name, size | /bin/grep hcpool"
                _node.mExecuteCmdLog(_cmd)
                _rc = _node.mGetCmdExitStatus()
                if not _rc:
                    ebLogInfo("Detected exascale griddisks.Ignoring OEDA Exception...")
                    _xs_enabled = True
        return _xs_enabled

    def mUpdateACL(self, aOptions, aHost=None, aVaultName=None, aAclPriv=None):
        _host = aHost
        _acl_priv = aAclPriv
        _vault = aVaultName
        _ebox = self.__cluctrl
        _escli = self.__escli
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        if not _ebox.mIsOciEXACC() and 'rack' in list(aOptions.jsonconf.keys()) \
            and 'name' in list(aOptions.jsonconf['rack'].keys()):
            _clusterName = "grid" + aOptions.jsonconf['rack']['name']
            ebLogInfo(f"Fetching the Cluster name:{_clusterName} from input payload")
        else:
            _clusterName = "grid" + _ebox.mGetClusters().mGetCluster().mGetCluName()
            ebLogInfo(f"Fetching the Cluster name:{_clusterName} from XML")
        
        if _host and _vault:
            _escli.mChangeACL(_cell, None, _acl_priv, aOptions, _host, aVaultName=_vault)
        else:
           _escli.mChangeACL(_cell, _clusterName, _acl_priv, aOptions)

    def mDetachU02(self, aDom0, aDomU, aU02Name, aDevicePath, aOptions):
        _dom0 = aDom0
        _domU = aDomU
        _ebox = self.__cluctrl

        _dom0_short_name = _dom0.split('.')[0]
        _domU_short_name = _domU.split('.')[0]
        _u02_vol_name = _domU_short_name + "_u02"
        self.mRemoveGuestEDVVolume(_dom0_short_name, _u02_vol_name, aOptions)

        try:
            _new_ref_link = aDevicePath
            _host_node = exaBoxNode(get_gcontext())
            _host_node.mConnect(aHost=aDom0)
            _i, _o, _e = _host_node.mExecuteCmd(f"/opt/exadata_ovm/vm_maker --list --disk-image --domain {aDomU} | grep '{_new_ref_link}'")
            _u02_attached = (_host_node.mGetCmdExitStatus() == 0)

            if _u02_attached:
                _new_ref_link  = _o.readlines()[0].strip().split()[1]
                ebLogInfo('*** /u02 already attached on domu {}'.format(aDomU))

                # Detach the volume first if already attached
                with connect_to_host(aDomU, get_gcontext(), username="root") as _guest_node:
                    node_exec_cmd(_guest_node, "/bin/umount /u02")
                    node_exec_cmd(_guest_node, f"/sbin/vgchange -an VGExaDbDisk.{aU02Name}.img")
                    node_exec_cmd(_guest_node, f"/bin/sed -i '/{aU02Name}/d' /etc/fstab")

                node_exec_cmd(_host_node, f"/bin/virsh detach-disk {aDomU} {_new_ref_link} --live --config")
        except Exception as e:
            ebLogError("*** Unable to detach U02 on domU: {0}".format(aDomU))
        finally:
            _host_node.mDisconnect()
            
    def mDoXsGetOp(self, aOptions):
        """
        function to decide which Xs Get operation to run
        """
        ebLogInfo("*** mDoXsGetOp")
        _rc=-1
        _ebox = self.__cluctrl
        _options = aOptions
        _inputjson = _options.jsonconf
        if not _inputjson.get('operation'):
            _err_msg = f'operation details missing'
            _ebox.mUpdateErrorObject(gExascaleError["INVALID_EXASCALE_OPERATION"], _err_msg)
            return _rc
        
        if _inputjson["operation"] == "fetch_compute_details":
            _rc = self.mGetComputeDetails(_options)
        else:
            _err_msg = f'Invalid XS Get operation {(_inputjson["operation"])}'
            _ebox.mUpdateErrorObject(gExascaleError["INVALID_EXASCALE_OPERATION"], _err_msg)
        return _rc
    
    def mDoXsPutOp(self, aOptions):
        """
        function to decide which Xs Put operation to run
        """
        ebLogInfo("*** mDoXsPutOp")
        _rc=-1
        _ebox = self.__cluctrl
        _options = aOptions
        _inputjson = _options.jsonconf
        if not _inputjson.get('operation'):
            _err_msg = f'operation details missing'
            _ebox.mUpdateErrorObject(gExascaleError["INVALID_EXASCALE_OPERATION"], _err_msg)
            return _rc
        
        if _inputjson["operation"] ==  "config-auto-encryption":
            # Enable Auto File Encryption if not already enabled
            # Skip only if flag is set in exabox.conf
            _flag_encryption = "exascale_autofileencryption_disable"
            if str(get_gcontext().mGetConfigOptions().get(
               _flag_encryption, "False")).upper() == "TRUE":
                ebLogWarn(f"Auto File encryption has been skipped by exabox.conf flag '{_flag_encryption}'!")
                _rc = 0
            else:
                _rc = self.mEnableAutoFileEncryption(aOptions)
                if _rc:
                    ebLogError(f"Failed to enable Auto File Encryption")
            return _rc
        else:
            _err_msg = f'Invalid XS Put operation {(_inputjson["operation"])}'
            _ebox.mUpdateErrorObject(gExascaleError["INVALID_EXASCALE_OPERATION"], _err_msg)
            return _rc
        
            
    def mGetComputeDetails(self, aOptions):
        """
        function to get details of the new compute
        """
        ebLogInfo("*** mGetComputeDetails")
        _ret=-1
        _ebox = self.__cluctrl
        _computeList = []
        _options = aOptions
        _inputjson = _options.jsonconf
        _host_list = _inputjson['host_nodes']
        _data_d= {}
        for _host in _host_list:
            with connect_to_host(_host, get_gcontext()) as _node:
                # Check if we actually need to configure QinQ for this Dom0
                _computedetail = {}
                _computedetail["compute_hostname"] = _host
                _computedetail["qinq_configurable"] = True # default is True
                _cmd = f'/usr/sbin/vm_maker --check'
                _ret, _out, _ = node_exec_cmd(_node, _cmd)
                if _ret != 0 or "The system is not configured for Secure Fabric support" in _out:
                    _msg = f'mEnableQinQIfNeeded: QinQ not configured in Dom0 {_host}'
                    ebLogWarn(_msg)
                    _cmd = '/bin/virsh list --all --name'
                    _running_domus = \
                        [ vm.strip()
                        for vm in node_exec_cmd(_node, _cmd).stdout.splitlines()
                        if vm.strip() ]
                    if _running_domus:
                        _msg = ("*** mEnableQinQIfNeeded(): Cannot setup "
                                f"QinQ in Dom0 {_host} since the following DomUs "
                                f"are still existing: {_running_domus}")
                        ebLogError(_msg)
                        _computedetail["qinq_configurable"] = False  
                        _ret = -1
                    else:
                        _ret = 0
                _computedetail["qinq_enabled"] = True if _ret == 0 else False
                _stre0cmd = "/usr/sbin/ip -o -4 addr show stre0 | /usr/bin/awk '{print $4}' | cut -d/ -f1"
                _stre1cmd = "/usr/sbin/ip -o -4 addr show stre1 | /usr/bin/awk '{print $4}' | cut -d/ -f1"
                _computedetail["stre0ip"]= node_exec_cmd_check(_node, _stre0cmd).stdout.strip()
                _computedetail["stre1ip"]= node_exec_cmd_check(_node, _stre1cmd).stdout.strip()
                _computeList.append(_computedetail)
            
        _data_d["host_nodes"] = _computeList
        ebLogInfo(f'mGetComputeDetails: Compute details sent')
        self._mUpdateRequestData(_ret,_data_d,"")
        return _ret

    def mAlterVolumeAccess(self, aHost, aVolume, aOptions):
        _host = aHost
        _volume = aVolume
        _ebox = self.__cluctrl
        _escli = self.__escli

        try:
            if aOptions is not None and aOptions.jsonconf is not None and \
               "exascale" in list(aOptions.jsonconf.keys()):
                _exascale_attr = aOptions.jsonconf['exascale']
                _ctrl_ip = _exascale_attr['ctrl_network']['ip'].strip()
                _ctrl_port = _exascale_attr['ctrl_network']['port'].strip()
        except Exception as e:
            ebLogWarn(f"*** mAlterVolumeAccess failed with Exception: {str(e)}")
            _ctrl_ip, _ = _escli.mGetCtrlIP()
            _ctrl_port = CTRL_PORT

        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _vol_id, _owners = _escli.mGetVolumeID(_cell, _volume, aOptions)
        if _owners:
            _list_owners = _owners.split(',')
            if len(_list_owners) == 1:
                _matches = [_owner for _owner in _list_owners if _owner == _host]

                if not _matches:
                    _escli.mChangeVolume(_cell, _vol_id, _host, aOptions)

    def mUpdateSystemVaultAccess(self, aOptions):
        _ebox = self.__cluctrl
        if self.mIsEDVImageSupported(aOptions) or self.mIsEDVBackupSupported(aOptions):
            _ddpair = _ebox.mReturnDom0DomUPair()
            for _dom0, _domU in _ddpair:
                _host = _dom0.split('.')[0]

                if _ebox.mGetCmd() == "vmgi_reshape":
                    _image_vault, _backup_vault = self.mGetImageBackupVault(aOptions)
                    if _image_vault:
                        self.mUpdateACL(aOptions, aHost=_host, aVaultName=_image_vault, aAclPriv="M")
                    if _backup_vault:
                        self.mUpdateACL(aOptions, aHost=_host, aVaultName=_backup_vault, aAclPriv="M")

                #Update volume access for the computes
                _domU_mac = _ebox.mGetMachines().mGetMachineConfig(_domU)
                _edv_vol_list = _domU_mac.mGetEdvVolumes()
                for _edv_config in _edv_vol_list:
                    _edvo = _ebox.mGetStorage().mGetEDVVolumesConfig(_edv_config)
                    _vol_name = _edvo.mGetEDVName()
                    self.mAlterVolumeAccess(_host, _vol_name, aOptions)

                #Update u02 volume access for the computes
                _domU_short_name = _domU.split('.')[0]
                _u02_vol_name = _domU_short_name + "_u02"
                self.mAlterVolumeAccess(_host, _u02_vol_name, aOptions)
        else:
            ebLogInfo("System Vault Access on compute is not supported.")

    def mRemoveGuestEDVVolumes(self, aOptions):
        _ebox = self.__cluctrl
        if self.mIsEDVImageSupported(aOptions):
            _ddpair = _ebox.mReturnDom0DomUPair()
            for _dom0, _domU in _ddpair:
                _host = _dom0.split('.')[0]
                _domU_short_name = _domU.split('.')[0]
                _domU_mac = _ebox.mGetMachines().mGetMachineConfig(_domU)
                _edv_vol_list = _domU_mac.mGetEdvVolumes()
                for _edv_config in _edv_vol_list:
                    _edvo = _ebox.mGetStorage().mGetEDVVolumesConfig(_edv_config)
                    _vol_name = _edvo.mGetEDVName()
                    if _vol_name:
                        self.mRemoveGuestEDVVolume(_host, _vol_name, aOptions)

                # If EDV Volume is detected, umount u02 volume from the cells
                _u02_vol_name = _domU_short_name + "_u02"
                _u02_name = _ebox.mCheckConfigOption('u02_name') if _ebox.mCheckConfigOption('u02_name') else 'u02_extra'
                self.mDetachU02(_dom0, _domU, _u02_name, _u02_vol_name, aOptions)
        else:
            ebLogInfo(f"ebExascaleUtils: EDV Image is not Supported")

    def mEnableAutoFileEncryption(self, aOptions):
        """
        Helper method used to enable 'Auto File Encryption'
        using 'escli'. This is a 'cluster attribute' we need to
        modify

        :returns: 0 on success, non-zero on Error
        """

        _options = aOptions
        _inputjson = _options.jsonconf
        if _inputjson.get('cell_list'):
            _cell_list = _inputjson['cell_list']
        elif _inputjson.get('exascale', {}).get('cell_list'):
            _cell_list = _inputjson.get('exascale', {}).get('cell_list')
        else:
            ebLogError(f"Missing Cell List in input Payload")
            return -1

        # Check if all cells are above minimum image req, which is
        # 25.1.7 as per Bug 37999765
        _cells_fail_check = []
        CUT_OFF_VERSION = "25.1.7"
        ebLogTrace("Minimum required version to support Auto File Encryption "
            f"is {CUT_OFF_VERSION}")

        for _cell in _cell_list:
            _cell_version = self.mGetCluCtrl().mGetImageVersion(_cell)
            if version_compare(_cell_version, CUT_OFF_VERSION) >= 0:
                ebLogTrace(f"Cell {_cell} with image {_cell_version} "
                    f"satisfies auto file encryption image requirement")
            else:
                ebLogWarn(f"Cell {_cell} with image {_cell_version} "
                    f"does not satisfy auto file encryption image requirement")
                _cells_fail_check.append(_cell)

        # If one cell fails the version check raise error OR
        # continue if a given flag is present in exabox.conf
        if _cells_fail_check:
            _flag_encryption = "exascale_autofileencryption_skip_version_check"
            if get_gcontext().mGetConfigOptions().get(
                _flag_encryption, "False").upper() == "TRUE":
                ebLogWarn(f"Version check for Auto File encryption has been "
                    f"skipped by exabox.conf flag '{_flag_encryption}'!")
            else:
                ebLogCritical(
                    aString=(f"Version check for Auto File encryption has "
                        f"failed for cells '{_cells_fail_check}'"),
                    aAction=("Option1: Make sure all the cells are at least "
                        f"minimum version: '{CUT_OFF_VERSION}'. Option2: "
                        f"Modify the exabox.conf flag '{_flag_encryption}' to "
                        "'True' to skip this check, please note this may "
                        "cause the operation to fail. Option3: Modify "
                        "exabox.conf flag 'exascale_autofileencryption_disable' "
                        "to skip the auto file encryption setup"))
                return -1

        # Use one of the cells to check current attribute state
        _cell = _cell_list[0]
        ebLogInfo(f"Using cell {_cell} to enable Auto File Encryption")

        # If we can't detect attribute status or we detect false,
        # we attempt to enable it
        _current_auto_file_encryption = False
        _rc, _out, _err = self.__escli.mGetClusterAttribute(
            _cell, ATTR_AUTO_FILE_ENCRYPTION, _options)
        if "true" in _out:
            ebLogInfo(f"The attribute '{ATTR_AUTO_FILE_ENCRYPTION} has "
                "been detected to be 'true' already, will not attempt "
                f"to enable it")
        else:
            ebLogInfo(f"The attribute '{ATTR_AUTO_FILE_ENCRYPTION} has "
                "been detected to be 'false', enabling it...")

            _rc = self.__escli.mAlterAutoFileEncryption(
                aCell=_cell, aEnable=True, aOptions=_options)
            if _rc == 0:
                ebLogInfo(f"The attribute '{ATTR_AUTO_FILE_ENCRYPTION} has "
                    "been enabled")

            # Do a quick validation of the attribute once after enabling it
            # Raise error in case we fail to do so
            _rc, _out, _err = self.__escli.mGetClusterAttribute(
                _cell, ATTR_AUTO_FILE_ENCRYPTION, _options)
            if "true" in _out:
                ebLogInfo(f"The attribute '{ATTR_AUTO_FILE_ENCRYPTION} has "
                    "been enabled to be 'true' with success")
            else:
                ebLogError(f"The attribute '{ATTR_AUTO_FILE_ENCRYPTION} has "
                    "not been enabled with success ")
                return -1

        return 0

    def mGetRackSize(self):
        _ebox = self.__cluctrl
        _rack_type = ""

        for _cell_name in _ebox.mReturnCellNodes().keys():
            _cell_mac = _ebox.mGetMachines().mGetMachineConfig(_cell_name)
            _sub_type = _cell_mac.mGetMacSubType()
            if _sub_type and _sub_type.lower() == "storage_one_eighth":
                _rack_type = "eighthrack"
            elif _sub_type and _sub_type.lower() == "storage_all_hc":
                _rack_type = "zrack"
            else:
                _rack_type = "normal"
        return _rack_type

    def mCreateOracleWallet(self, aOptions):
        _ebox = self.__cluctrl

        # Create eswallet for oracle or DB user
        _srcDomu = None
        _exaRootUrl = None
        _cluster_name = None

        # fetch Grid cluster name
        if not _ebox.mIsOciEXACC() and 'rack' in list(aOptions.jsonconf.keys()) \
            and 'name' in list(aOptions.jsonconf['rack'].keys()):
            _cluster_name = aOptions.jsonconf['rack']['name']
            ebLogInfo(f"Fetching the Cluster name:{_cluster_name} from input payload")
        else:
            _cluster_name = _ebox.mGetClusters().mGetCluster().mGetCluName()
            ebLogInfo(f"Fetching the Cluster name:{_cluster_name} from XML")

        ESCLI = "/usr/bin/escli"
        _gridWallet = "/etc/oracle/cell/network-config/eswallet"
        _oracleWallet = "/u02/app/oracle/admin/eswallet"
        _mkwalletScr = f"/tmp/oracle{_cluster_name}.mkwallet.scr"
        _chwalletScr = f"/tmp/oracle{_cluster_name}.chwallet.scr"
        _privkeyfile = f"/tmp/ExascaleCluster-{_cluster_name}-oracle.priv.key"
        _pubkeyfile = f"/tmp/ExascaleCluster-{_cluster_name}-oracle.pub.key"
        _orawalletuser = f"oracle{_cluster_name}"
        _node = exaBoxNode(get_gcontext())
        for _, _domu in _ebox.mReturnDom0DomUPair():
            if _srcDomu is None:
                # setup wallet on the 1st domU
                # fetch exaRootUrl from grid eswallet that was already setup
                _srcDomu = _domu
                _node.mConnect(aHost=_domu)
                if _node.mFileExists('/etc/oracle/cell/network-config/eswallet'):
                    _cmd = f"sudo -u grid {ESCLI} --wallet {_gridWallet} lswallet --attributes exaRootUrl | grep -v exaRootUrl"
                    _, _o, _ = _node.mExecuteCmd(_cmd)
                    _out = _o.readlines()
                    if _out and len(_out):
                        _exaRootUrl = _out[0].strip()

                # create eswallet directory
                _cmd = f"/bin/mkdir -p {_oracleWallet}"
                _, _o, _ = _node.mExecuteCmd(_cmd)

                # change ownership to oracle:oinstall in oracle eswallet files
                _node.mExecuteCmd(f"/bin/chown -fR oracle:oinstall {_oracleWallet}")

                #  mkwallet --wallet /u02/app/oracle/admin/eswallet
                _cmd = f" mkwallet --wallet {_oracleWallet}"
                _node.mExecuteCmd(f"/bin/echo '{_cmd}' > {_mkwalletScr}")
                _node.mExecuteCmd(f"/bin/echo '{_cmd}' > {_chwalletScr}")

                # mkkey --private-key-file /u02/app/oracle/admin/eswallet/ExascaleCluster1-Cluster-c1-oracle.priv.key --public-key-file /u02/app/oracle/admin/eswallet/ExascaleCluster1-Cluster-c1-oracle.pub.key
                _cmd = f" mkkey --private-key-file {_privkeyfile} --public-key-file {_pubkeyfile}"
                _node.mExecuteCmd(f"/bin/echo '{_cmd}' >> {_mkwalletScr}")

                # chwallet --wallet /u02/app/oracle/admin/eswallet --private-key-file /u02/app/oracle/admin/eswallet/ExascaleCluster1-Cluster-c1-oracle.priv.key
                #    --attributes user=oracleCluster-c1 --attributes exaRootUrl="egs=..."
                _cmd = f"chwallet --wallet {_oracleWallet} --private-key-file {_privkeyfile} --attributes user={_orawalletuser} --attributes exaRootUrl=\"{_exaRootUrl}\""
                _node.mExecuteCmd(f"/bin/echo '{_cmd}' >> {_mkwalletScr}")
                _node.mExecuteCmd(f"/bin/echo '{_cmd}' >> {_chwalletScr}")

                # Execute escli mkwallet script on src domu
                _cmd = f"/usr/bin/sudo -u oracle {ESCLI} < {_mkwalletScr}"
                _, _o, _ = _node.mExecuteCmd(_cmd)

            else:
                # copy the key and escli script files to other domus
                ebLogInfo(f"Copying oracle eswallet setup files from {_srcDomu} to {_domu}.")
                _node.mExecuteCmd(f"/usr/bin/sudo -u oracle /bin/scp {_privkeyfile} oracle@{_domu}:/tmp/")
                _node.mExecuteCmd(f"/usr/bin/sudo -u oracle /bin/scp {_chwalletScr} oracle@{_domu}:/tmp/")

        # cleanup and disconnect from source domu
        _node.mExecuteCmd(f"/usr/bin/rm -f {_privkeyfile} {_pubkeyfile} {_mkwalletScr}")
        _node.mDisconnect()

        # Execute escli chwallet script on remote domus
        _node = exaBoxNode(get_gcontext())
        for _, _domu in _ebox.mReturnDom0DomUPair():
            if not _domu == _srcDomu:
                _node.mConnect(aHost=_domu)
                _cmd = f"/bin/mkdir -p {_oracleWallet}"
                _, _o, _ = _node.mExecuteCmd(_cmd)

                # change ownership to oracle:oinstall in oracle eswallet files
                _node.mExecuteCmd(f"/bin/chown -fR oracle:oinstall {_oracleWallet}")

                # Execute mkwallet script
                _cmd = f"/usr/bin/sudo -u oracle {ESCLI} < {_chwalletScr}"
                _, _o, _ = _node.mExecuteCmd(_cmd)
                # cleanup
                _node.mExecuteCmd(f"/usr/bin/rm -f {_privkeyfile} {_chwalletScr}")
                _node.mDisconnect()
