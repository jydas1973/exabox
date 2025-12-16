#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/clubasedb.py /main/5 2025/11/21 09:43:16 prsshukl Exp $
#
# clubasedb.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      clubasedb.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    prsshukl    11/20/25 - Bug 38675257 - BASEDB PROVISIONING FAILING IN
#                           FETCHUPDATEDXMLFROMEXACLOUD
#    scoral      10/28/25 - Enh 38452359: Support separate "admin" network
#                           section in payload.
#    aararora    07/30/25 - ER 38132942: Single stack support for ipv6
#    prsshukl    06/11/25 - Bug 38048906 - EXADB-XS -> BASE DB -> OPC USER CREATION IN EXACLOUD LAYER
#    prsshukl    05/26/25 - Creation
#

import time
import os
import base64
from base64 import b64decode, b64encode

try:
    from base64 import decodestring
except ImportError:
    from base64 import b64decode as decodestring
import re, operator
from ipaddress import IPv4Address, IPv4Network, IPv6Address, ip_interface, ip_address, IPv6Network
from typing import Any, Dict, List, Mapping, Sequence, Optional, Tuple, Set
from exabox.utils.common import check_string_base64, version_compare
from exabox.log.LogMgr import ebLogDiag, ebLogWarn, ebLogInfo, ebLogDebug, ebLogError, ebLogVerbose, ebLogTrace
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.core.DBStore import ebGetDefaultDB
from exabox.ovm.hypervisorutils import getHVInstance, ebVgCompRegistry
from exabox.ovm.bmc import XMLProcessor
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure
from exabox.utils.common import mCompareModel
from exabox.config.Config import ebVmCmdCheckOptions, ebCluCmdCheckOptions
from exabox.ovm.cluexascale import ebCluExaScale
from exabox.utils.node import connect_to_host, node_cmd_abs_path_check
from exabox.network.NetworkUtils import NetworkUtils
from exabox.ovm.clunetwork import CLIENT, BACKUP, DR
from exabox.core.Mask import umask, umaskSensitiveData, maskSensitiveData
import exabox.ovm.clujumboframes as clujumboframes
from exabox.core.Error import ExacloudRuntimeError
import random, string
import json

DEVNULL = open(os.devnull, 'wb')

class exaBoxBaseDB(object):

    def __init__(self, aCluCtrlObject):
        self.__cluctrl = aCluCtrlObject

    def mUpdateOedaPropertiesInterface(self):

        _ebox = self.__cluctrl
        _oeda_prop_path = _ebox.mGetOedaPath()+'/properties'

        _ebox.mSetNetworkDiscovered(aAdminNet='vmeth0::eth0',
                                    aClientNet='vmbondeth0:eth1,eth2:bondeth0')

        _cmd_str = "/bin/sed 's/^PAAS_CLIENT_IFACE.*/PAAS_CLIENT_IFACE=vmbondeth0:eth1,eth2:bondeth0/' -i "+_oeda_prop_path+'/es.properties'
        _ebox.mExecuteLocal(_cmd_str, aStdOut=DEVNULL, aStdErr=DEVNULL)
        _cmd_str = "/bin/sed 's/^PAAS_ADMIN_IFACE.*/PAAS_ADMIN_IFACE=vmeth0::eth0/' -i " + _oeda_prop_path + '/es.properties'
        _ebox.mExecuteLocal(_cmd_str, aStdOut=DEVNULL, aStdErr=DEVNULL)
        ebLogInfo('*** Updating OEDA properties : for BaseDB to review if oeda is getting the eth value from here')

    def mPatchClusterDB(self, aOptions):

        _ebox = self.__cluctrl

        if not ebCluCmdCheckOptions(_ebox.mGetCmd(), ['dont_update_cell_disk_size']):
            _ebox.mUpdateCelldiskSize()

        _rqdb_json_conf = None
        if aOptions is not None:
            aOptions.jsonconf = umaskSensitiveData(aOptions.jsonconf)
            _jconf = aOptions.jsonconf
        else:
            _jconf = None

        # VCPU ratio calculation
        _ratio = _ebox.mCheckConfigOption('core_to_vcpu_ratio')

        if _ratio is None:
            _ratio = 2
        else:
            _ratio = int(_ratio)

        if _ebox.mIsKVM() and _ebox.IsZdlraProv():
            if _ebox.mCheckConfigOption('zdlra_core_to_vcpu_ratio') is not None:
                _ratio = int(_ebox.mCheckConfigOption('zdlra_core_to_vcpu_ratio'))
            else:
                _ratio = 1

        ebLogInfo('*** mPatchClusterDB: _ratio is : %d' %(_ratio))

        # Retrieve DBHome and DBConfig for the cluster.

        _mac_list = _ebox.mGetMachines().mGetMachineConfigList()
        _dbhome_list = {}
        for _mac in list(_mac_list.keys()):
            # Find the DBHome with the corresponding _mac IDs
            _dbhL = _ebox.mGetDBHomes().mGetDBHomeConfigs()
            _dbhR = []
            for _dbh in _dbhL:
                if _mac in _dbh.mGetDBHomeMacs():
                    _dbhome_list[_dbh.mGetDBHomeId()] = _dbh
                else:
                    _dbhR.append(_dbh)
            #
            # Remove DBHome not used by this cluster ! Currently not an issue (no additional homes)
            #
            for _dbh in _dbhR:
                _ebox.mGetDBHomes().mRemoveDBHomeConfig(_dbh.mGetDBHomeConfig_ptr(), _dbh)
        #
        # Remove all databases/database Entries not used by our cluster (required for CDB/PDB)
        #
        _dbconfig_list = {}
        _dbcL = _ebox.mGetDatabases().mGetDBconfigs()
        _dbcI = []
        for _dbhid in list(_dbhome_list.keys()):
            for _dc in _dbcL:
                if _dbhid == _dbcL[_dc].mGetDBHome():
                    _dbconfig_list[_dbcL[_dc].mGetDBId()] = _dbcL[_dc]
                    _dbcI.append(_dc)
        _dbcX = []
        _dbcL = _ebox.mGetDatabases().mGetDBconfigs()
        for _dc in _dbcL:
            if not _dc in _dbcI:
                _dbcX.append(_dc)
        for _dc in _dbcX:
            _ebox.mGetDatabases().mRemoveDatabaseConfig(_dc)

        #
        # Cleanup XML to reduce size
        #
        if _ebox.mCheckConfigOption('remove_configkeys','True'):
            _xmlr = _ebox.mGetConfig().mConfigRoot()
            _xmlo = _xmlr.find('configKeys')
            _xmlr.remove(_xmlo)

        # Check if ASM diskgroup storage size has been passed
        if 'rack' in list(_jconf.keys()) \
            and 'gb_storage' in list(_jconf['rack'].keys()):
            _ebox.mSetDbStorage(str(_jconf['rack']['gb_storage'])+'G')

        if 'exaunitAllocations' in list(_jconf.keys()) \
            and 'storageTb' in list(_jconf['exaunitAllocations'].keys()):
            _ebox.mSetDbStorage(str(_jconf['exaunitAllocations']['storageTb']*1024)+'G')

        if ( 'rack' in _jconf ) \
            and ( 'ecra_db_rack_name' in _jconf['rack'] ):
            _ebox.mSetRackNameEcra(str(_jconf['rack']['ecra_db_rack_name']))

        if ( 'rack' in _jconf ) \
            and ( 'vmclustertype' in _jconf['rack'] ):
            _ebox.mSetVmClusterType(str(_jconf['rack']['vmclustertype']))

        #
        # Handle SSH Key
        #
        _ssh_public_key = ""
        if 'tools_ssh' in list(_jconf.keys()):
            _ebox.mSetToolsKey(_jconf['tools_ssh']['ssh_public_key'].rstrip())
            _ebox.mSetToolsKeyPrivate(_jconf['tools_ssh']['ssh_private_key'])

        # Search for ssh public key in payload under 'vm' section
        # This should come in base64 encoding
        elif 'vm' in list(_jconf.keys()):
            _ssh_public_key = _jconf.get("vm", {}).get("sshkey", False)
            if _ssh_public_key:
                _ebox.mSetToolsKey(_ssh_public_key.rstrip())
                _ebox.mSetToolsKeyPrivate(None)

                # Verify sshkey is not empty and is base64 encoded
                if not _ebox.mGetToolsKey() or not check_string_base64(_ebox.mGetToolsKey()):
                    _err = ("sshkey given on payload is empty or invalid (base64 encoding)")
                    ebLogError(_err)
                    raise ExacloudRuntimeError(0x0823, 0xA, _err)
                ebLogTrace("Exacloud using sshkey on payload under 'vm' field")
                _ebox.mSetToolsKey(base64.b64decode(
                        _ebox.mGetToolsKey()).decode())

        # Check if present in legacy 'sshkey' section if we didn't find it
        # already under vm section
        if 'sshkey' in list(_jconf.keys()) and not _ssh_public_key:
            if _jconf['sshkey'] is not None:
                _ebox.mSetToolsKey(_jconf['sshkey'].rstrip())
                _ebox.mSetToolsKeyPrivate(None)
            else:
                ebLogError ("*** Error *** SSH Key not provided or incorrect")
                raise ExacloudRuntimeError(0x0406, 0xA, "SSH Key not provided or incorrect", aStackTrace=False)

        if aOptions.debug and _ebox.mGetToolsKey():
            ebLogInfo('*** Tools keys found')

        #
        # Compute and set accordingly in the XML values for cores, memory and disk
        #
        # JSON payload fields: vm.size and vm.cores/gb_memory/gb_disk
        # Default configuration is XML : Large
        #
        # Priority (where the values are taken from first):
        #   1. JSON Payload
        #   2. exabox.conf (see mPatchClusterConfig - for more information)
        #   3. XML - default set is Large
        #
        _default_size = 'Large'
        _cores  = ""
        _memory = ""
        _disk   = ""

        # Priority for add node use case (where the values are taken from first):
        #   1. JSON Payload
        #   2. Pick the values from source domU
        #   3. exabox.conf (see mPatchClusterConfig - for more information)
        #   4. XML - default set is Large
        #

        _cores  = _ebox.mGetVMSizesConfig().mGetVMSize(_default_size).mGetVMSizeAttr('cpuCount')
        _memory = _ebox.mGetVMSizesConfig().mGetVMSize(_default_size).mGetVMSizeAttr('MemSize').upper()
        _disk   = _ebox.mGetVMSizesConfig().mGetVMSize(_default_size).mGetVMSizeAttr('DiskSize').upper()

        #
        # Fetch VM size from payload if present else default is Large
        #
        if 'vm' in list(_jconf.keys()) and \
            'size' in list(_jconf['vm'].keys()):
            _default_size = str(_jconf['vm']['size'])

        if 'vm' in list(_jconf.keys()):
            if 'cores' in list(_jconf['vm'].keys()):
                _cores = str(_jconf['vm']['cores'])
                #
                # _cores needs to translated to vCPUs.
                # For example on X5 the ratio is usually 2 (e.g. 1 core equals 2 vCPUs)
                #
                # Note: The value returned/stashed in the XML is vCPUs not cores except for info request.
                #       The info request is used to return the patched XML to SDI which only manages cores.
                #
                _cores = str(int(_cores) * _ratio)
            if 'gb_memory' in list(_jconf['vm'].keys()) and not _ebox.mCheckConfigOption('ignore_memory_payload','True'):
                _memory = str(_jconf['vm']['gb_memory'])+'GB'
            if 'gb_disk' in list(_jconf['vm'].keys()):
                _disk = str(_jconf['vm']['gb_disk'])+'GB'
            # Parse OH size over here
            if 'gb_ohsize' in list(_jconf['vm'].keys()) and _jconf['vm']['gb_ohsize']:
                _ebox.mSetOHSize(str(_jconf['vm']['gb_ohsize'])+'G')
            if 'gb_tmpsize' in list(_jconf['vm'].keys()):
                _ebox.mSetAdditionalDisks(("/tmp",str(_jconf['vm']['gb_tmpsize'])+'GB'))
            if 'gb_logsize' in list(_jconf['vm'].keys()):
                _ebox.mSetAdditionalDisks(("/var/opt/oracle/logs",str(_jconf['vm']['gb_logsize'])+'GB'))

        if 'exaunitAllocations' in list(_jconf.keys()):
            if 'memoryGb' in list(_jconf['exaunitAllocations'].keys()): 
                _memory = str(_jconf['exaunitAllocations']['memoryGb'])+'GB'
            if 'cores' in list(_jconf['exaunitAllocations'].keys()):
                _cores = str(_jconf['exaunitAllocations']['cores'])
                _cores = str(int(_cores) * _ratio)
            if 'ohomeSizeGb' in list(_jconf['exaunitAllocations'].keys()):
                _ebox.mSetOHSize(str(_jconf['exaunitAllocations']['ohomeSizeGb'])+'G')

        _u01Disksize = _ebox.mCheckConfigOption('force_vm_u01_disksize')
        if not _ebox.mGetSharedEnv() and _u01Disksize is None:
            ebLogInfo("DEDICATED ENV DETECTED & force_vm_u01_disksize flag was not defined in exabox.conf")
            _u01Disksize = '150GB'

        if 'force_vm_u01_disksize' in list(_jconf.keys()):
            ebLogInfo("force_vm_u01_disksize flag defined in input payload")
            _u01Disksize = _jconf['force_vm_u01_disksize']

        if _u01Disksize is not None:
            ebLogInfo(f"*** u01 disksize: {_u01Disksize}")

            _newDisksize = _u01Disksize
            _gbPos = _newDisksize.find("GB")

            if _gbPos == -1:
                _error_str = "Mismatch configuration on 'force_vm_u01_disksize', missing GB at end"
                ebLogError(_error_str)
                raise ExacloudRuntimeError(0x0741, 0xA, _error_str, aStackTrace=False)

            try:
                _newDisksize = int(_newDisksize[0:_gbPos]) - 10 #substract 10 since 10GB is the base size of the VM

                if _newDisksize < 0:
                    _error_str = "Mismatch configuration on 'force_vm_u01_disksize', value must be greater than 10GB"
                    ebLogError(_error_str)
                    raise ExacloudRuntimeError(0x0741, 0xA, _error_str, aStackTrace=False)

            except ValueError as _v:
                _error_str = "Mismatch configuration on 'force_vm_u01_disksize', missing integer before GB"
                ebLogError(_error_str)
                raise ExacloudRuntimeError(0x0741, 0xA, _error_str, aStackTrace=False)

            _oedaReqPath = _ebox.mGetOEDARequestsPath()
            for _pname in ('s_Linux','s_LinuxXen','s_LinuxKvm'):
                _propertyFile = "{0}/properties/{1}.properties".format(_oedaReqPath, _pname)
                ebLogInfo("Change u01 disksize to: 10+{0} on {1}".format(_newDisksize, _propertyFile))
                _ebox.mExecuteLocal("/bin/sed -i 's/VGEXTRASPACE=.*/VGEXTRASPACE={0}/g' {1}".format(_newDisksize, _propertyFile))

        #
        # For now overwrite all size with the default one
        #
        _key   = 'cpuCount'
        _ebox.mGetVMSizesConfig().mGetVMSize('Large').mSetVMSizeAttr( _key, _cores)
        _ebox.mGetVMSizesConfig().mGetVMSize('Medium').mSetVMSizeAttr(_key, _cores)
        _ebox.mGetVMSizesConfig().mGetVMSize('Small').mSetVMSizeAttr( _key, _cores)
        _key   = 'MemSize'
        _ebox.mGetVMSizesConfig().mGetVMSize('Large').mSetVMSizeAttr( _key, _memory)
        _ebox.mGetVMSizesConfig().mGetVMSize('Medium').mSetVMSizeAttr(_key, _memory)
        _ebox.mGetVMSizesConfig().mGetVMSize('Small').mSetVMSizeAttr( _key, _memory)
        _key   = 'DiskSize'
        _ebox.mGetVMSizesConfig().mGetVMSize('Large').mSetVMSizeAttr( _key, _disk)
        _ebox.mGetVMSizesConfig().mGetVMSize('Medium').mSetVMSizeAttr(_key, _disk)
        _ebox.mGetVMSizesConfig().mGetVMSize('Small').mSetVMSizeAttr( _key, _disk)

        #33456175 - UI_OEDAXML IS UPDATING INCORRECTLY IF ONE OF THE VM HAS GUESTCORES
        #self.__guestCores, self.__guestMemory, self.__guestLocalDiskSize should have null check
        #before it access the variables,when self.mGetUiOedaXml() is TRUE & only if one of the domU nodes has Mac cores set.
        if _ebox.mIsKVM() or _ebox.mGetUiOedaXml():
            for _, _domU in _ebox.mReturnDom0DomUPair():
                _domU_mac = _ebox.mGetMachines().mGetMachineConfig(_domU)
                ebLogInfo('Setting domU ' + _domU + " with cores = " +str(_cores))
                _domU_mac.mSetMacCores(_cores)

                ebLogInfo('Setting domU ' + _domU + " with memory = " +str(_memory))
                _domU_mac.mSetMacMemory(_memory)

                ebLogInfo('Setting domU ' + _domU + " with disk = " +str(_disk))
                _domU_mac.mSetMacDisk(_disk)

        if aOptions.debug:
            if _ratio == 1:
                ebLogInfo('*** cpuCount patching done (CORES): '+str(_cores))
            else:
                ebLogInfo('*** cpuCount patching done (VCPUS): '+str(_cores))
            ebLogInfo('*** MemSize  patching done: '+str(_memory))
            ebLogInfo('*** DiskSize patching done: '+str(_disk))
        #
        # Handle TZ (before GI install)
        #
        if _ebox.mIsDebug():
            ebLogInfo('*** TimeZone current GS: %s' % (str(_ebox.mGetTimeZone())))
        if 'rack' in list(_jconf.keys()) \
                and 'timezone' in list(_jconf['rack'].keys()):
            _ebox.mSetTimeZone(_jconf['rack']['timezone'])
        elif 'customer' in list(_jconf.keys()) \
                and 'timezone' in list(_jconf['customer'].keys()):
            _ebox.mSetTimeZone(_jconf['customer']['timezone'])
        elif 'dbParams' in list(_jconf.keys()):
            if 'timezone' in _jconf['dbParams']:
                _timezone = _jconf['dbParams']['timezone']
                _ebox.mSetTimeZone(_timezone)

        _timeZone = 'UNDEFINED'
        if _ebox.mGetTimeZone() is not None:
            for _, _domU in _ebox.mReturnDom0DomUPair():
                _domU_mac = _ebox.mGetMachines().mGetMachineConfig(_domU)
                _domU_mac.mSetMacTimeZone(_ebox.mGetTimeZone())
                _timeZone = _ebox.mGetTimeZone()
        else:
            for _, _domU in _ebox.mReturnDom0DomUPair():
                _domU_mac = _ebox.mGetMachines().mGetMachineConfig(_domU)
                _timeZone = _domU_mac.mGetMacTimeZone()
                break

        if _ebox.mGetMachines() is None:
            ebLogInfo('*** TimeZone not specified in payload assuming default XML TZ : %s' % (_timeZone))
        else:
            ebLogInfo('*** TimeZone included in JSon payload XML updated with TZ : %s' % (_timeZone))


    def mPatchClusterConfig(self, aOptions):
        """
        BaseDB doesn't have cluster info so, this needs to be taken care of
        """
        _ebox = self.__cluctrl

        if _ebox.mSkipGISupportDetection(aOptions):
            ebLogInfo('Skipping mGISupportDetection patching for %s command!'%(_ebox.mGetCmd()))        
        else:
            _ebox.mGISupportDetection()

        #
        # Change VM Configuration (use exabox.conf values) - see mPatchClusterDB for json SDI overwrite
        #
        # TODO: Support Configuration for all the size (Large, Medium, Small) not only one.
        _config = get_gcontext().mGetConfigOptions()

        if 'default_vmsize' in list(_config.keys()):
            _vmsize =  _config['default_vmsize']

        if not _ebox.mIsKVM() and 'default_dedicated_vmsize' in list(_config.keys()) and not _ebox.mGetSharedEnv():
            _vmsize =  _config['default_dedicated_vmsize']

        if 'default_shared_vmsize' in list(_config.keys()) and _ebox.mGetSharedEnv():
            _vmsize =  _config['default_shared_vmsize']

        for key in list(_vmsize.keys()):
            _ebox.mGetVMSizesConfig().mGetVMSize('Large').mSetVMSizeAttr(key, _vmsize[key])
            _ebox.mGetVMSizesConfig().mGetVMSize('Medium').mSetVMSizeAttr(key, _vmsize[key])
            _ebox.mGetVMSizesConfig().mGetVMSize('Small').mSetVMSizeAttr(key, _vmsize[key])

        #remove the xml parts databasehome and database
        # Patch DB configuration
        # Condition to skip patching cluster DB if command has no_check_sw_cell
        if ebCluCmdCheckOptions(_ebox.mGetCmd(), ['no_check_sw_cell']):
            ebLogInfo(f'*** Skip patching cluster DB for {_ebox.mGetCmd()} command')
        else:
            if not ebCluCmdCheckOptions(_ebox.mGetCmd(), ['cluster_info_tool']):
                if _ebox.mIsClusterLessXML():
                    ebLogInfo('Skipping mPatchClusterDB patching for command {}'.format(aOptions.clusterctrl))
                else:
                    self.mPatchClusterDB(aOptions)

        # Update OEDA Properties
        ebLogInfo("Apply change of oeda properties")
        _ebox.mUpdateOEDAProperties(aOptions, aSkipValidation=True)


        # Skip XML Patching
        if not _ebox.mIsOciEXACC():

            if _ebox.mIsSkipXmlPatching():

                _jconf = aOptions.jsonconf
                if _jconf and 'dbaas_api' in list(_jconf.keys()):
                    _ebox.mSetDbaasApiPayload(_jconf['dbaas_api'])

                _ebox.mSaveXMLClusterConfiguration()
                _ebox.mSetConfigPath(_ebox.mGetPatchConfig())

                _ebox.mParseXMLConfig(aOptions)

                if _ebox.mGetCmd() in ['deleteservice']:
                    # Patch VMs in Delete service for reconfigured cluster
                    _util = _ebox.mGetFactoryPreprovReconfig().mCreatePreprovUtil()
                    _util.mUpdateVmNameReconfigDeleteService(aOptions)
                    _ebox.mSaveXMLClusterConfiguration()
                    #self.mSetConfigPath(self.__patchconfig)

                    _patchconfig = _ebox.mGetPatchConfig()
                    _ebox.mUpdateInMemoryXmlConfig(_patchconfig, aOptions)

                ebLogInfo(f"ebCluCtrl: Saved patched Cluster Config: {_ebox.mGetPatchConfig()}")

                return

        #
        # Save new XML Cluster configuration file
        #
        _ebox.mSaveXMLClusterConfiguration()
        
        # #Apply commands OEDACLI
        _ebox.mApplyCommandsOedacli(aOptions=aOptions)


        # Patching of ExaScale
        if _ebox.mIsExaScale():
            _exascale = ebCluExaScale(_ebox)
            _exascale.mCreateOedaProperties()
            if ebCluCmdCheckOptions(_ebox.mGetCmd(), ['exascale_patching']):
                _exascale.mApplyExaScaleXmlPatching()
            _exascale.mCreateDummyCellsKeys()

    def mCustomerNetworkXMLUpdateBaseDB(self,aOptions,aJConf=None):

        """
        In BaseDB in ExaDB-XS, there is client only , no backup, no SCAN, no VIP in payload.
        As this is single instance vm and not needed for High Availability.
        """

        _ebox = self.__cluctrl

        ebLogInfo('*** mCustomerNetworkXMLUpdateBaseDB: CustomerNetwork XML Update for BaseDB...')
        if aJConf is not None:
            _jconf = aJConf
        else:
            if aOptions is not None:
                _jconf = aOptions.jsonconf

        if _jconf is None:
            raise ExacloudRuntimeError(0x0740, 0xA,'payload is empty')

        _nodesubset_conf = ''
        if _ebox.mIsExabm():
            if 'customer_network' in list(_jconf.keys()):
                _customer_conf = _jconf['customer_network']
        elif _ebox.mIsOciEXACC():
            # Fallback to be removed once payload key is clear
            if 'network' in list(_jconf.keys()):
                _customer_conf = _jconf['network']
            else:
                _customer_conf = _jconf['customer_network']

            if "node_subset" in list(_jconf.keys()):
                _nodesubset_conf = _jconf['node_subset']
        else:
            raise ExacloudRuntimeError(0x0740, 0xA,'Network JSON Update requires either exabm or ociexacc flag in configuration')

        try:
            _timeZone = _customer_conf['timezone']
            for _, _domU in _ebox.mReturnDom0DomUPair():
                _domU_mac = _ebox.mGetMachines().mGetMachineConfig(_domU)
                _domU_mac.mSetMacTimeZone(_timeZone)
                _ebox.mSetTimeZone(_timeZone)
            ebLogInfo('*** Customer Network TimeZone set to: %s' % (_timeZone))
        except:
            pass

        _nw_utils = NetworkUtils()
        _nodes_list = _customer_conf['nodes']
        _nb_nodes = len(_nodes_list)
        _dr_net = {}
        _dr_net_list      = []
        _client_net_list  = []
        _dom0_net_dict    = {}
        ebLogInfo('*** Customer Network Configuration for %d nodes detected' % (_nb_nodes))
        # TO BE REMOVED, OCICCv1 may not pass dom0_oracle_name and rely on alpha order
        _tmp_ociexaccv1_activated = False
        _tmp_ociexaccv1_dom0domU = list(sorted(_ebox.mReturnDom0DomUNATPair(),\
                                        key = operator.itemgetter(0)))
        for _node in _nodes_list:
            if 'client' not in list(_node.keys()):
                raise ExacloudRuntimeError(0x0740, 0xA,'Client configuration not found in Customer Network JSON')
            _client_net = _node['client']
            _admin_net = _node.get('admin') or {}
            if 'dr' in list(_node.keys()):
                _dr_net = _node['dr']
                _dr_net_list.append(_dr_net)
                _ebox.mSetDRNetPresent(True)
            else:
                # Set it to empty otherwise in case of wrong payload, this gets info of the previous node.
                _dr_net = {}
            _client_net_list.append(_client_net)
            if 'dom0' not in list(_node.keys()):
                if 'dom0_oracle_name' in list(_client_net.keys()):
                    _dom0_net_key = _client_net['dom0_oracle_name']
                #to be removed in v2
                elif _ebox.mIsOciEXACC():
                    if _nodesubset_conf:
                        _participating_nodes = _nodesubset_conf['participating_computes']
                        _node_alias = _client_net['compute_node_alias']
                        _dom0_net_key = ""
                        for _item in _participating_nodes:
                            if _node_alias == _item['compute_node_alias']:
                                _dom0_net_key = _item['compute_node_hostname']
                                break
                        if not _dom0_net_key:
                            continue
                    else:
                        _tmp_ociexaccv1_activated = True
                        _dom0_net_key = _tmp_ociexaccv1_dom0domU[0][0] #dom0
                    ebLogInfo('*** TEMPORARY WORKAROUND - OCIEXACC V1 - matched client net to dom0: {}'.format(_dom0_net_key))
                else:
                    raise ExacloudRuntimeError(0x0740, 0xA,'DOM0 Key configuration not found in Network JSON (w/ CLIENT/BACKUP IN CONFIG)')
            else:
                _dom0_net_key = _node['dom0']
            if len(_dom0_net_key.split('.')) == 1:  # Append DOM0 domainname

                for _dom0 , _ in _ebox.mReturnDom0DomUPair():
                    _dot_pos = _dom0.find('.')
                    _dom0_domain = _dom0[_dot_pos:]
                    if _dom0_net_key == _dom0[:_dot_pos]:
                        break

                _dom0_net_key = _dom0_net_key + _dom0_domain
                ebLogInfo('*** _dom0_net_key domainame added for: %s' % (_dom0_net_key))
            if 'domu_oracle_name' in list(_client_net.keys()):
                _domu_net_key = _client_net['domu_oracle_name']
            elif _ebox.mIsOciEXACC():
                #Get NatHostname of DomU matching dom0
                if _nodesubset_conf:
                    _domu_net_key = ""
                    for _item in _tmp_ociexaccv1_dom0domU:
                        if _dom0_net_key == _item[0]:
                            _domu_net_key = _item[1]
                            break
                    if not _domu_net_key:
                            continue
                else:
                    _tmp_ociexaccv1_activated = True
                    _domu_net_key = _tmp_ociexaccv1_dom0domU[0][1]

                ebLogInfo('*** TEMPORARY WORKAROUND - OCIEXACC V1 - matched client net to domU NAT: {}'.format(_domu_net_key))
            else:
                raise ExacloudRuntimeError(0x0744, 0xA,'DOMU Key configuration not found in Network JSON')

            # Pop processed dom0/domU at the end
            if _tmp_ociexaccv1_activated:
                _tmp_ociexaccv1_dom0domU.pop(0)

            _dom0_net_dict[_dom0_net_key] = [_client_net, _admin_net, _dr_net, _domu_net_key]

        #
        # DOM0 driven XML Patching / On BM the DomU->Dom0 mapping is important for Cavium/MAC configuration/dependency
        #
        for _dom0_key in list(_dom0_net_dict.keys()):
            _net_master_client = None
            _net_slaves_client = None
            _client_net, _admin_net, _dr_net, _domu_key = _dom0_net_dict[_dom0_key]

            _dom0_conf = _ebox.mGetMachines().mGetMachineConfig(_dom0_key)
            #Allow XMLs with more than one VM in machines to be used
            _domu_ids  = _dom0_conf.mGetMacMachines()
            _domu_id   = None
            # Locate good VM with Nat hostname
            for _domu in _domu_ids:
                _domu_nets = _ebox.mGetMachines().mGetMachineConfig(_domu).mGetMacNetworks()
                _host = None
                for _net_id in _domu_nets:
                    _net_conf = _ebox.mGetNetworks().mGetNetworkConfig(_net_id)
                    _domu_nat = _net_conf.mGetNetNatHostName(aFallBack=True)
                    if _domu_nat == _domu_key:
                        _host = _domu_nat
                        break
                if _host:
                    _domu_id = _domu
                    break
            if not _domu_id:
                raise ExacloudRuntimeError(0x0740, 0xA,'domu_oracle_name in payload must match a domU NAT hostname')

            _domu_conf = _ebox.mGetMachines().mGetMachineConfig(_domu_id)

            ebLogDebug('@@@ Processing Dom0: %s :: DomU: %s' % (_dom0_key, _domu_id))
            #
            # Fetch Client network config for each DomU
            #
            _domu_hostname = _domu_conf.mGetMacHostName()
            _domu_networks = _domu_conf.mGetMacNetworks()
            # List of network support for BM gen1 - any network in this list will trigger an error
            _valid_netlist = [ \
                'backup', 'client', 'private' \
            ]
            # With Worflow, ECRA can sends a Patched XML with a network payload add support that it will contain an admin net
            if _ebox.mIsOciEXACC() and _ebox.isATP():
                _valid_netlist.append('admin')

            if _ebox.mIsOciEXACC() and _ebox.mIsDRNetPresent():
                _valid_netlist.append('other')

            _domu_net_client_single_stack = None
            _domu_net_client_v6 = None
            _client_net_type = _nw_utils.mClassifyStack(_client_net)
            for _net_id in _domu_networks:
                _net_conf = _ebox.mGetNetworks().mGetNetworkConfig(_net_id)
                if _net_conf.mGetNetType() not in _valid_netlist:
                    raise ExacloudRuntimeError(0x0741, 0xA, 'Unsupported Network in DOMU %s / %s' % (_domu_hostname, _net_id))
                #
                # NET/Update only required for client
                #
                elif _net_conf.mGetNetType() == 'client' and _client_net_type == 'single':
                    _domu_net_client_single_stack = _net_conf
                elif _net_conf.mGetNetType() == 'client' and _client_net_type == 'dual':
                    if _net_conf.mGetNetIpAddr() and ':' not in _net_conf.mGetNetIpAddr():
                        _domu_net_client_single_stack = _net_conf
                    elif _net_conf.mGetNetIpAddr() and ':' in _net_conf.mGetNetIpAddr():
                        _domu_net_client_v6 = _net_conf

            if _domu_net_client_single_stack is None:
                raise ExacloudRuntimeError(0x0741, 0xA, 'DOMU %s / Client network config not found' % (_domu_hostname))
            #
            # DUMP Current Client Net Config
            #
            _domu_net_client_single_stack.mDumpConfig()
            if _domu_net_client_v6:
                _domu_net_client_v6.mDumpConfig()
            #
            # Fetch Dom0 domainname / netmask (in case not available in JSON payload)
            #
            _dom0_nat_domainname = None
            _dom0_nat_mask = None
            _mac_conf_list = _ebox.mGetMachines().mGetMachineConfigList()
            for _mac_conf in list(_mac_conf_list.keys()):
                _mac_vml = _mac_conf_list[_mac_conf].mGetMacMachines()
                if len(_mac_vml) != 0:
                    _dom0_hostname = _mac_conf_list[_mac_conf].mGetMacHostName()
                    _dom0_network_list = _mac_conf_list[_mac_conf].mGetMacNetworks()
                    for _dom0_net_id in _dom0_network_list:
                        _dom0_tmp_net_conf = _ebox.mGetNetworks().mGetNetworkConfig(_dom0_net_id)
                        if _dom0_tmp_net_conf.mGetNetType() != 'admin':
                            continue
                        if _dom0_key and _dom0_key != _dom0_hostname:
                            continue
                        _dom0_net_conf = _ebox.mGetNetworks().mGetNetworkConfig(_dom0_net_id)
                        _dom0_nat_domainname =  _dom0_net_conf.mGetNetDomainName()
                        _dom0_nat_mask = _dom0_net_conf.mGetNetMask()
            if 'natdomainname' not in _client_net and 'domainname' not in _admin_net and _dom0_nat_domainname is None:
                raise ExacloudRuntimeError(0x0741, 0xA, 'DOMU %s / Client NAT DomaineName not found' % (_domu_hostname))
            if 'natmask' not in _client_net and 'netmask' not in _admin_net and _dom0_nat_mask is None:
                raise ExacloudRuntimeError(0x0741, 0xA, 'DOMU %s / Client NAT NetMask not found' % (_domu_hostname))
            if 'domainname' in _admin_net:
                _dom0_nat_domainname = _admin_net['domainname']
            elif 'natdomainname' in _client_net:
                _dom0_nat_domainname = _client_net['natdomainname']
            if 'netmask' in _admin_net:
                _dom0_nat_mask = _admin_net['netmask']
            elif 'natmask' in _client_net:
                _dom0_nat_mask = _client_net['natmask']
            #
            # CLIENT - Expanded Update/Patching
            #
            _client_json_fields = ['domainname', 'hostname']
            _client_either_or_fields = {'ip':'ipv6', 'netmask': 'v6netmask', 'gateway': 'v6gateway'}
            if not _ebox.mIsOciEXACC():
                _client_json_fields.append('mac')
            for _field in _client_json_fields:
                if _field not in list(_client_net.keys()):
                    raise ExacloudRuntimeError(0x0740, 0xA, 'Client JSON Payload incomplete missing field: %s' % (_field))
            for _key, _value in _client_either_or_fields.items():
                if _key not in list(_client_net.keys()) and _value not in list(_client_net.keys()):
                    raise ExacloudRuntimeError(0x0740, 0xA, f'Client JSON Payload incomplete missing field: {_key}/{_value}.')

            #
            # Handle case where nathostname/natip are not part of the payload (e.g. already in the XML)
            #
            if ('hostname' not in _admin_net or 'ip' not in _admin_net) and \
               ('nathostname' not in _client_net or 'natip' not in _client_net):
                _nathostname_xml = _domu_net_client_single_stack.mGetNetNatHostName(aFallBack=False)
                _natip_xml = _domu_net_client_single_stack.mGetNetNatAddr(aFallBack=False)
                if _nathostname_xml is None or _natip_xml is None:
                    raise ExacloudRuntimeError(0x0740, 0xA, 'Client NAT hostname/ip are missing')
            else:
                _nathostname_xml = None
                _natip_xml = None
            #
            # Update DomU Client Networks
            #
            _domu_net_client_single_stack.mSetNetHostName(_client_net['hostname'])
            _client_ip_single_stack, _client_ipv6 = _nw_utils.mGetIPv4IPv6Payload(_client_net)
            # IPv6 host IP should be added using oedacli and not by direct patching of xml
            # as per discussion with oeda/oeda spec.
            if _client_ip_single_stack:
                _domu_net_client_single_stack.mSetNetIpAddr(_client_ip_single_stack)
            if _client_ipv6 and _domu_net_client_v6:
                _domu_net_client_v6.mSetNetIpAddr(_client_ipv6)
            if ':' in _client_ip_single_stack:
                _ebox.mSetIPv6SingleStackPresent(True)

            _client_netmask_single_stack, _client_netmaskv6 = _nw_utils.mGetIPv4IPv6Payload(_client_net, key_single_stack='netmask', key_dual_stack='v6netmask')
            # IPv6 netmask should be added using oedacli and not by direct patching of xml
            # as per discussion with oeda/oeda spec. Also, v6netmask will be a prefix for IPv6 case.
            if _client_netmask_single_stack:
                _domu_net_client_single_stack.mSetNetMask(_client_netmask_single_stack)
            if _client_netmaskv6 and _domu_net_client_v6:
                _domu_net_client_v6.mSetNetMask(_client_netmaskv6)

            _client_gateway_single_stack, _client_gatewayv6 = _nw_utils.mGetIPv4IPv6Payload(_client_net, key_single_stack='gateway', key_dual_stack='v6gateway')
            # IPv6 gateway should be added using oedacli and not by direct patching of xml
            # as per discussion with oeda/oeda spec.
            if _client_gateway_single_stack:
                _domu_net_client_single_stack.mSetNetGateWay(_client_gateway_single_stack)
            if _client_gatewayv6 and _domu_net_client_v6:
                _domu_net_client_v6.mSetNetGateWay(_client_gatewayv6)

            _domu_net_client_single_stack.mSetNetDomainName(_client_net['domainname'])
            # Added data from oeda network discovered
            _network_discovered = _ebox.mGetNetworkDiscovered()
            if _network_discovered and 'client_net' in _network_discovered:
                _net_master_client = _network_discovered['client_net']['bond_master']
                _net_slaves_client = _network_discovered['client_net']['bond_slaves']
                _domu_net_client_single_stack.mSetNetMaster(_network_discovered['client_net']['bond_master'])
                _domu_net_client_single_stack.mSetNetSlave(_network_discovered['client_net']['bond_slaves'])
            if not _ebox.mIsOciEXACC():
                _domu_net_client_single_stack.mSetMacAddr(_client_net['mac'].lower())         # Enforce lower case for vm.cfg compliance
            # NAT
            _nat_addr = None
            _nat_host = None
            if _nathostname_xml is None or _natip_xml is None:

                if "ip" in _admin_net and "hostname" in _admin_net or \
                   "natip" in _client_net and "nathostname" in _client_net:

                    _domu_net_client_single_stack.mSetNatHostName(_admin_net.get('hostname', _client_net['nathostname']))
                    _nat_host = _admin_net.get('hostname', _client_net['nathostname'])

                    _domain = ""
                    if "domainname" in _admin_net:
                        _domu_net_client_single_stack.mSetNatDomainName(_admin_net['domainname'])
                        _domain = _admin_net['domainname']
                    elif "natdomainname" in _client_net:
                        _domu_net_client_single_stack.mSetNatDomainName(_client_net['natdomainname'])
                        _domain = _client_net['natdomainname']

                    if _admin_net.get("ip", _client_net["natip"]) == "discover":

                        _nathost = _admin_net.get('hostname', _client_net['nathostname'])

                        if _domain:
                            _nathost = f"{_nathost}.{_domain}"

                        _cmd = f"/usr/bin/nslookup {_nathost}"
                        _rc, _, _o, _e = _ebox.mExecuteLocal(_cmd)

                        if _rc == 0:
                            _hostname = re.search("Address:\s+(([0-9]{1,3}\.){3}[0-9]{1,3})\s", _o)

                            if _hostname:
                                _domu_net_client_single_stack.mSetNatAddr(_hostname.group(1))
                                _nat_addr = _hostname.group(1)

                    else:
                        _domu_net_client_single_stack.mSetNatAddr(_admin_net.get("ip", _client_net["natip"]))
                        _nat_addr = _admin_net.get("ip", _client_net["natip"])

                    # Validate that client 'natip' is a valid ip
                    __natip = _domu_net_client_single_stack.mGetNetNatAddr()
                    try:
                        ip = ip_address(__natip)
                        ebLogTrace(f"Valid IP: {ip} for client natip parameter")
                    except ValueError:
                        _msg = f"Value {__natip} is not a valid IP"
                        ebLogError(_msg)
                        raise ExacloudRuntimeError(0x0740, 0xA, _msg)

            _domu_net_client_single_stack.mSetNatDomainName(_dom0_nat_domainname)
            _domu_net_client_single_stack.mSetNatMask(_dom0_nat_mask)

            # Set VLANID.  If "vlantag" is missing in the payload or its value
            # is "null", set VLANID to an empty value (represented by a None
            # python value).
            _domu_net_client_single_stack.mSetNetVlanId(_client_net.get('vlantag'))

            if _admin_net.get('vlantag'):
                _domu_net_client_single_stack.mSetNetVlanNatId(_admin_net.get('vlantag'))
            elif _client_net.get('natvlantag'):
                _domu_net_client_single_stack.mSetNetVlanNatId(_client_net.get('natvlantag'))

            if _admin_net.get('netgateway'):
                _domu_net_client_single_stack.mSetNetNatGateway(_admin_net.get('netgateway'))
            elif _client_net.get('natgateway'):
                _domu_net_client_single_stack.mSetNetNatGateway(_client_net.get('natgateway'))

            _egressIps = _ebox.mFetchEgressIpsFromPayload(_jconf)

            if _egressIps:
                _egressArgs = ",".join(_egressIps)

                _cmd = [
                    "ALTER NETWORK",
                    {"nategressipaddresses": _egressArgs},
                    {"ID": _domu_net_client_single_stack.mGetNetId()}
                ]

                _ebox.mGetExtrXmlPatchingCmds().append(_cmd)


            _domu_net_client_single_stack.mUpdateNatLookup()
            # Patch hostname in machine (DEFAULT)
            _domu_new_hostname = _client_net['hostname']+'.'+_client_net['domainname']
            _domu_conf.mSetMacHostName(_domu_new_hostname)

            def __lacp_enabled(
                    net_payload: Mapping[str, Any],
                    net_type: str) -> bool:
                if not _ebox.mIsOciEXACC():
                    return False  # LACP only supported in ExaCC

                if "network_types" in net_payload:
                    _net_info = net_payload["network_types"].get(net_type)
                    if _net_info and "bonding_mode" in _net_info:
                        if _net_info.get("bonding_mode").lower() == "lacp":
                            return True
                        else:
                            return False

                # If payload doesn't have attribute "lacp" fallback to global
                # configuration.
                if net_type == CLIENT:
                    config_param = "customer_net_client_lacp"
                else:
                    config_param = "customer_net_dr_lacp"

                return _ebox.mCheckConfigOption(config_param, "True")

            _domu_net_client_single_stack.mSetNetLacp(
                __lacp_enabled(_customer_conf, net_type=CLIENT))

            _mtu_set = None
            client_mtu = _client_net.get("mtu")
            if client_mtu and not clujumboframes.useExacloudJumboFramesAPI(_ebox):
                _domu_net_client_single_stack.mSetNetMtu(int(client_mtu))
                _mtu_set = int(client_mtu)

            # Patch the ipv6 client network information using oedacli
            if _client_ipv6 and _client_netmaskv6 and _client_gatewayv6:
                _ebox.mSetIPv6DualStackPresent(True)
                _dict_oeda_args = {}
                _dict_oeda_args["NETWORKTYPE"] = "client"
                if _net_master_client:
                    _dict_oeda_args["MASTER"] = _net_master_client
                else:
                    _dict_oeda_args["MASTER"] = _domu_net_client_single_stack.mGetNetMaster()
                if _net_slaves_client:
                    _dict_oeda_args["SLAVE"] = _net_slaves_client
                else:
                    _dict_oeda_args["SLAVE"] = _domu_net_client_single_stack.mGetNetSlave()
                _dict_oeda_args["HOSTNAME"] = _client_net['hostname']
                _dict_oeda_args["DOMAINNAME"] = _client_net['domainname']
                _dict_oeda_args["IP"] = _client_ipv6
                _dict_oeda_args["NETMASK"] = _client_netmaskv6
                _dict_oeda_args["GATEWAY"] = _client_gatewayv6
                # Add all NAT entries
                if not _ebox.mIsOciEXACC():
                    _dict_oeda_args["MAC"] = _client_net['mac'].lower()
                if _mtu_set:
                    _dict_oeda_args["MTU"] = str(_mtu_set)
                _dom0_nat_mask = _domu_net_client_single_stack.mGetNetNatMask()
                if _dom0_nat_mask:
                    _dict_oeda_args["NATNETMASK"] = _dom0_nat_mask
                _dom0_nat_domainname = _domu_net_client_single_stack.mGetNetNatDomainName()
                if _dom0_nat_domainname:
                    _dict_oeda_args["NATDOMAINNAME"] = _dom0_nat_domainname
                _nat_host = _domu_net_client_single_stack.mGetNetNatHostName()
                if _nat_host:
                    _dict_oeda_args["NATHOSTNAME"] = _nat_host
                _nat_addr = _domu_net_client_single_stack.mGetNetNatAddr()
                if _nat_addr:
                    _dict_oeda_args["NATIP"] = _nat_addr
                _nat_gateway = _domu_net_client_single_stack.mGetNetNatGateway()
                if _nat_gateway and _nat_gateway != "UNDEFINED":
                    _dict_oeda_args["NATGATEWAY"] = _nat_gateway
                _nat_vlan = _domu_net_client_single_stack.mGetNetVlanNatId()
                if _nat_vlan and _nat_vlan != "UNDEFINED":
                    _dict_oeda_args["NATVLANID"] = _nat_vlan
                if _egressIps:
                    _egressArgs = ",".join(_egressIps)
                    _dict_oeda_args["nategressipaddresses"] = _egressArgs
                if 'vlantag' in _client_net:
                    _vlan = _client_net.get('vlantag')
                    if _vlan:
                        _dict_oeda_args["VLANID"] = _vlan
                _dict_oeda_where = {"HOSTNAME": _domu_new_hostname}
                _cmd = [
                    "ADD NETWORK",
                    _dict_oeda_args,
                    _dict_oeda_where
                ]
                _ebox.mGetExtrXmlPatchingCmds().append(_cmd)
            #
            # DUMP Updated Client/Backup Net Config
            #
            _domu_net_client_single_stack.mDumpConfig()
            #
            # Check Global State (flush domU cached list).
            #
            _ebox.mReturnDom0DomUPair(aForce=True)

        if not _ebox.mIsOciEXACC():
            # Update DNS/NTP values from original xml
            try:
                _dom0s, _, _cells, _ = _ebox.mReturnAllClusterHosts()
                _cluhosts = _dom0s + _cells
                for _host in _cluhosts:
                    _dict_oeda_args = {}
                    _mac = _ebox.mGetMachines().mGetMachineConfig(_host)
                    _dns_servers = _mac.mGetDnsServers()
                    _ntp_servers = _mac.mGetNtpServers()
                    if _dns_servers:
                        _dns_servers = ','.join(_dns_servers)
                        _dict_oeda_args["DNSSERVERS"] = _dns_servers
                    if _ntp_servers:
                        _ntp_servers = ','.join(_ntp_servers)
                        _dict_oeda_args["NTPSERVERS"] = _ntp_servers
                    if _dns_servers or _ntp_servers:
                        _dict_oeda_where = {"HOSTNAME": _host}
                        _cmd = [
                            "ALTER MACHINE",
                            _dict_oeda_args,
                            _dict_oeda_where
                        ]
                        _ebox.mGetExtrXmlPatchingCmds().append(_cmd)
            except Exception as ex:
                ebLogWarn("DNS and NTP server information could not be added to the list of oeda xml patching commands"\
                    " for DOM0s and Cells.")
            try:
                for _ilom in _ebox.mGetIloms().mGetIlomsList():
                    _dict_oeda_args = {}
                    _ilomCfg = _ebox.mGetIloms().mGetIlomConfig(_ilom)
                    _dns_servers = _ilomCfg.mGetDnsServers()
                    _ntp_servers = _ilomCfg.mGetNtpServers()
                    if _dns_servers:
                        _dns_servers = ','.join(_dns_servers)
                        _dict_oeda_args["DNSSERVERS"] = _dns_servers
                    if _ntp_servers:
                        _ntp_servers = ','.join(_ntp_servers)
                        _dict_oeda_args["NTPSERVERS"] = _ntp_servers
                    if _dns_servers or _ntp_servers:
                        _dict_oeda_where = {"ILOMNAME": _ilomCfg.mGetIlomName()}
                        _cmd = [
                            "ALTER ILOM",
                            _dict_oeda_args,
                            _dict_oeda_where
                        ]
                        _ebox.mGetExtrXmlPatchingCmds().append(_cmd)
            except Exception as ex:
                ebLogWarn("DNS and NTP server information could not be added to the list of oeda xml patching commands"\
                    " for ILOMs.")
        #
        # Update DNS/NTP to values in payload
        #
        _ntp_conf = _customer_conf.get('network_services', {}).get('ntp')
        _dns_conf = _customer_conf.get('network_services', {}).get('dns')
        if not _ntp_conf or not _ntp_conf[0]:
            raise ExacloudRuntimeError(0x0744, 0xA, 'JSON Payload incomplete missing field: _ntp_conf')
        if not _dns_conf or not _dns_conf[0]:
            raise ExacloudRuntimeError(0x0744, 0xA, 'JSON Payload incomplete missing field: _dns_conf')
        _ntp_conf = [x for x in _ntp_conf if str(x).strip()]
        _dns_conf = [x for x in _dns_conf if str(x).strip()]
        for _, _domU in _ebox.mReturnDom0DomUPair():
            _domU_mac = _ebox.mGetMachines().mGetMachineConfig(_domU)
            _domU_mac.mSetNtpServers(_ntp_conf)
            _domU_mac.mSetDnsServers(_dns_conf)
    

    def mAddUserDomU(self, aUser, aUID, aGID, aSudoAccess=False):

        _ebox = self.__cluctrl

        def _addUserPerDomU(aDomU, aUser, aUID, aGID, aSudoAccess=False):

            _domU = aDomU
            with connect_to_host(_domU, get_gcontext(), username='root') as _node:

                _node.mExecuteCmd('/usr/sbin/groupadd -g {0} {1}'.format(aGID, aUser))
                _node.mExecuteCmd('/usr/sbin/useradd -u {0} -g {1} -d /home/{2} -s /bin/bash -G adm,wheel,systemd-journal {2}'.format(aUID, aGID, aUser))

                if aSudoAccess:
                    _node.mExecuteCmd("echo '{0} ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers".format(aUser))

                _mkdir_cmd = node_cmd_abs_path_check(node=_node, cmd="mkdir")
                _chmod_cmd = node_cmd_abs_path_check(node=_node, cmd="chmod")
                _chown_cmd = node_cmd_abs_path_check(node=_node, cmd="chown")

                _node.mExecuteCmd(f"{_mkdir_cmd} -p /home/{aUser}/.ssh")
                _node.mExecuteCmd(f"{_chmod_cmd} 700 /home/{aUser}/.ssh")
                _node.mExecuteCmd(f"{_chown_cmd} {aUser}:{aUser} /home/{aUser}/.ssh")

        for _, _domU in _ebox.mReturnDom0DomUPair():
            _addUserPerDomU(_domU, aUser, aUID, aGID, aSudoAccess)

        _ebox.mAddUserPubKey(aUser)

    def mDeleteUserDomU(self, aUser):

        _ebox = self.__cluctrl

        def _deleteUserPerDomU(aDomU, aUser):
            _domU = aDomU
            with connect_to_host(_domU, get_gcontext(), username='root') as _node:
                _node.mExecuteCmd('/usr/sbin/userdel -r {0}'.format(aUser))

        for _, _domU in _ebox.mReturnDom0DomUPair():
            _deleteUserPerDomU(_domU, aUser)
