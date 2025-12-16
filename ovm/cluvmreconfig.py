#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/cluvmreconfig.py /main/28 2025/09/23 07:26:34 aararora Exp $
#
# cluvmreconfig.py
#
# Copyright (c) 2023, 2025, Oracle and/or its affiliates.
#
#    NAME
#      cluvmreconfig.py - VM reconfig
#
#    DESCRIPTION
#      Code flow to reconfigure a VM after pre-provisoining the env.
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aararora    07/30/25 - ER 38132942: Single stack support for ipv6
#    dekuckre    08/14/24 - 36944098: Recreate griddisks as part of reconfig.
#    dekuckre    08/09/24 - 36933342: update nft rules for domU interconnectivity.
#    dekuckre    07/30/24 - 36896620: Acquire locks around execution of dmgr.py mount.
#    dekuckre    07/30/24 - 36896620: Copy dmgr.py if not present.
#    ririgoye    06/18/24 - Bug 36746656 - PYTHON 3.11 - EXACLOUD NEEDS TO
#    aararora    04/30/24 - ER 36485120: IPv6 support in exacloud
#    gparada     04/27/24 - 36559204 Fix hardcoded grid path
#    dekuckre    02/26/24 - 36323263: Remove sensitive data from the logs/traces
#    dekuckre    02/15/24 - 36298670: Acquire locks when running vm_maker cmd
#    dekuckre    02/14/24 - 36298659: use deepcopy of aOptions for resizing u02
#    dekuckre    01/31/24 - 36098707: Reduce number of steps in vmgi_reconfig flow
#    dekuckre    01/12/24 - 36153523: mount and update network config files in dom0 before VM start
#    dekuckre    12/14/23 - 36102649: Create newVM conf xml in dom0
#    dekuckre    12/07/23 - 36086177: Store customer provided sshkey in the VMs
#    dekuckre    11/17/23 - 35960605: Ensure correct permissions within crs dir
#    scoral      11/09/23 - 35981374: Update network, gateway & netmask bits on DomU.
#    dekuckre    10/25/23 - 35875544: Account for dbaas_acfs and AHF-TFA
#    ndesanto    10/24/23 - 35942375: Copy rsp file for vmgi_reconfig
#    dekuckre    10/19/23 - 35925561: VM keys to be removed in the end..
#    dekuckre    10/16/23 - 35909853: Resize the filesystems as per sizes in payload.
#    dekuckre    10/10/23 - 35881162: Use rsp file from tmp (and not exacloud/scripts dir)
#    dekuckre    09/27/23 - 35751168: Update network filters and hostname in dom0 in Dom0Reconfig step 
#    dekuckre    09/12/23 - 35774564: Update old netmask, gateway with new values 
#    dekuckre    07/27/23 - 35646695: Refresh domU agent certificate
#    dekuckre    07/21/23 - 35629339: Decode adminPassword before using it
#    dekuckre    07/10/23 - 35575438: Run configtools as part of root script execution 
#    aararora    07/06/23 - Bug 35539930: Remove dg id dependency for checking
#                           dg type.
#    dekuckre    02/14/23 - Creation
#


from ipaddress import IPv4Network, IPv6Network
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogJson, ebLogDebug, ebLogVerbose, ebLogWarn
from exabox.core.Context import get_gcontext
import json, re, time, os, datetime, uuid, copy
from base64 import b64decode, b64encode

try:
    from base64 import decodestring
except ImportError:
    from base64 import b64decode as decodestring

from exabox.core.Error import ExacloudRuntimeError
from exabox.core.DBStore import ebGetDefaultDB
from exabox.ovm.clucontrol import exaBoxNode
from exabox.ovm.clustorage import ebCluManageStorage
from exabox.ovm.cludiskgroups import ebDiskgroupOpConstants, ebCluManageDiskgroup
from exabox.ovm.cludomupartitions import ebCluManageDomUPartition
from exabox.ovm.cludomufilesystems import expand_domu_filesystem, expand_domu_vg
from exabox.ovm.cluhealth import ebCluHealthCheck
from exabox.healthcheck.cluexachk import ebCluExachk
from exabox.ovm.hypervisorutils import getHVInstance
from exabox.utils.node import connect_to_host
from exabox.network.NetworkUtils import NetworkUtils

# reconfigure the VM using four steps
def mVMReconfig(aCluObj, aOptions):
    _step = aOptions.steplist

    if 'undo' not in aOptions:
        _undo = False
    elif str(aOptions.undo).lower() == "true":
        _undo = True
    else:
        _undo = False

    _do = not _undo

    # if _step is None, the flow is not executed in stepwise mode
    _json = mGetReconfigParams(aCluObj, aOptions)
    ebLogInfo(f"Reconfig step: {_step}, do: {_do}, undo: {_undo}")
 
    if _step == "Dom0Reconfig" and _do:
        # Brings up VM with new client and backup mac
        mDom0Reconfig(aCluObj, aOptions, _json)

    elif _step == "GridReconfig" and _undo:
        # deconfigure Grid
        aCluObj.mGridDeconfig()

    elif _step == "GridReconfig" and _do:
        # recreate quorum devices
        mUpdateQuorumConfig(aCluObj, aOptions, _json)

        # Remove ASM entries from /etc/oratab
        mGridUpdateOratab(aCluObj, aOptions, _json)

        # execute gridSetup.sh
        mGridReconfig(aCluObj, aOptions, _json)

        # execute root scripts
        mExecRootScrpt(aCluObj, aOptions, _json)

        # bring up ACFS
        mRecreateACFS(aCluObj, aOptions, _json)

    elif _step == "UpdateVM" and _do:
        _options = copy.deepcopy(aOptions)
        # Update ASM Storage based on the new storage value in reconfig
        mUpdateStorage(aCluObj, aOptions)

        # Update cpu count based on the new values in reconfig
        aCluObj.mManageVMCpusCount('resizecpus', '_all_', aOptions)

        # Resize u02 based on the new value in reconfig
        ebLogInfo("Cluster Reconfig: Attempting resize of u02")
        _partitionobj = ebCluManageDomUPartition(aCluObj)
        _partitionobj.mClusterManageDomUPartition("resize", _options)

        ebLogInfo("Cluster Reconfig: Attempting resize of other filesystems")
        expand_domu_filesystem(aCluObj)
        expand_domu_vg(aCluObj)

        # End steps post reconfiguring the cluster.
        mPostdomUReconfig(aCluObj, aOptions, _json)

    else:
        ebLogError(f"{_step}, do: {_do}, undo: {_undo} not supported")
        raise ExacloudRuntimeError(0x0132, 0x0A, "Reconfiguring Cluster VMs failed")

# parse the payload to collect/save the necessary info
def mGetReconfigParams(aCluObj, aOptions):
 
    _obj = aCluObj
    _json = {}

    """

    "customer_network":{
    .
    .

    "scan":{
         "hostname":"atpd-exa-acem9-scan.o1568755525397.v1568755524141.oraclevcn.com",
         "port":1521,
         "ips":[
            "10.0.0.70",
            "10.0.0.71",
            "10.0.0.72"
         ]
    },
    
    "nodes": [
      {
        "backup": {
          "dom0_oracle_name": "iad101608exdd007",
          "domainname": "data.customer2.oraclevcn.com",
          "domu_oracle_name": "iad101608exddu0701",
          "gateway": "10.0.1.1",
          "hostname": "iad101608exddu0701-backup",
          "hw_node_id": 7,
          "ip": "10.0.1.2",
          "mac": "02:00:17:01:2F:C0",
          "netmask": "255.255.255.0",
          "vlantag": "1",
          "mtu": "9000",
          "oldipAddress": "10.0.1.12",
          "oldmacAddress": "02:00:18:11:2F:C0"
        },
        "client": {
          "dom0_oracle_name": "iad101608exdd007",
          "domainname": "backup.customer2.oraclevcn.com",
          "domu_oracle_name": "iad101608exddu0701",
          "gateway": "10.0.0.1",
          "hostname": "iad101608exddu0701-client1",
          "hw_node_id": 7,
          "ip": "10.0.0.2",
          "mac": "00:10:66:e4:94:9c",
          "netmask": "255.255.255.0",
          "vlantag": null,
          "natdomainname": "sea2xx2xx0051qf.adminsea2.oraclevcn.com",
          "natmask": "255.255.240.0",
          "mtu": "9000",
          "oldHostname" : "iad101608exddu0701-old",
          "oldipAddress": "10.0.1.13",
          "oldmacAddress": "03:00:19:11:2F:C0"
        },
        "vip": {
          "domainname": "data.customer2.oraclevcn.com",
          "hostname": "iad101608exddu0701-vip",
          "ip": "10.0.0.4"
        },
        "monitoring": {},
        "fqdn": "iad101608exdd007.sea2xx2xx0051qf.adminsea2.oraclevcn.com"
    .
    .
    .
    .
    "preprov_network":{
    "nodes":[
    {
      "client":{
       "ip":"10.1.2.3"
       "mac":""
       .
       .
      
      },
      "backup":{
        "ip": "10.1.1.1"
        "mac": ""
        .
        .
      },

    }

    https://confluence.oraclecorp.com/confluence/display/EDCS/API+Payloads+from+ECRA+to+ExaCloud

    """

    _json['scan'] ={}
    _json['scan']['hostname'] = aOptions.jsonconf['customer_network']['scan']['hostname']
    _json['adminPassword'] = aOptions.jsonconf['vm']['adminPassword']
    _json['grid_version'] = aOptions.jsonconf['grid_version']
    _nw_utils = NetworkUtils()
    for _entry in aOptions.jsonconf['customer_network']['nodes']:

        domu = _entry['client']['hostname']
        cust_network_dom0 = _entry['client']['dom0_oracle_name']
        _json[domu] = {}

        _json[domu]['hostName'] = _entry['client']['hostname']+'.'+_entry['client']['domainname']
        _json[domu]['vipName'] =  _entry['vip']['hostname']+'.'+_entry['vip']['domainname']
        _vip_single_stack, _vip_v6 = _nw_utils.mGetIPv4IPv6Payload(_entry['vip'])
        if _vip_single_stack:
            _json[domu]['vip'] = _vip_single_stack
        if _vip_v6:
            _json[domu]['v6vip'] = _vip_v6
        _json[domu]['client'] = {}
        _ip_single_stack, _ipv6 = _nw_utils.mGetIPv4IPv6Payload(_entry['client'])
        if _ip_single_stack:
            _json[domu]['client']['ipAddress'] = _ip_single_stack
        if _ipv6:
            _json[domu]['client']['ipv6Address'] = _ipv6
        _client_gateway_single_stack, _client_gatewayv6 = _nw_utils.mGetIPv4IPv6Payload(_entry['client'], key_single_stack='gateway', key_dual_stack='v6gateway')
        _client_netmask_single_stack, _client_netmaskv6 = _nw_utils.mGetIPv4IPv6Payload(_entry['client'], key_single_stack='netmask', key_dual_stack='v6netmask')
        if _client_netmask_single_stack:
            _json[domu]['client']['netmask'] = _client_netmask_single_stack
        if _client_netmaskv6:
            _json[domu]['client']['v6netmask'] = _client_netmaskv6
        if _client_gateway_single_stack:
            _json[domu]['client']['gateway'] = _client_gateway_single_stack
        if _client_gatewayv6:
            _json[domu]['client']['v6gateway'] = _client_gatewayv6
        _json[domu]['client']['macAddress'] = _entry['client']['mac']
        _json[domu]['client']['vlan1'] = _entry['client']['vlantag']

        _json[domu]['backup'] = {}
        _ip_single_stack, _ipv6 = _nw_utils.mGetIPv4IPv6Payload(_entry['backup'])
        if _ip_single_stack:
            _json[domu]['backup']['ipAddress'] = _ip_single_stack
        if _ipv6:
            _json[domu]['backup']['ipv6Address'] = _ipv6
        _json[domu]['backup']['hostname'] = _entry['backup']['hostname']
        _json[domu]['backup']['domainname'] = _entry['backup']['domainname']
        _backup_gateway_single_stack, _backup_gatewayv6 = _nw_utils.mGetIPv4IPv6Payload(_entry['backup'], key_single_stack='gateway', key_dual_stack='v6gateway')
        _backup_netmask_single_stack, _backup_netmaskv6 = _nw_utils.mGetIPv4IPv6Payload(_entry['backup'], key_single_stack='netmask', key_dual_stack='v6netmask')
        if _backup_netmask_single_stack:
            _json[domu]['backup']['netmask'] = _backup_netmask_single_stack
        if _backup_netmaskv6:
            _json[domu]['backup']['v6netmask'] = _backup_netmaskv6
        if _backup_gateway_single_stack:
            _json[domu]['backup']['gateway'] = _backup_gateway_single_stack
        if _backup_gatewayv6:
            _json[domu]['backup']['v6gateway'] = _backup_gatewayv6
        _json[domu]['backup']['macAddress'] = _entry['backup']['mac']
        _json[domu]['backup']['vlan2'] = _entry['backup']['vlantag']
 
        for _entry in aOptions.jsonconf['preprov_network']['nodes']:
            preprov_network_dom0 = _entry['client']['dom0_oracle_name']

            ebLogInfo(f"dom0 c: {cust_network_dom0} dom0 p: {preprov_network_dom0}")
            # if the dom0 matches then record old host details
            if preprov_network_dom0 == cust_network_dom0:
                _ip_single_stack, _ipv6 = _nw_utils.mGetIPv4IPv6Payload(_entry['client'])
                if _ip_single_stack:
                    _json[domu]['client']['oldipAddress'] = _ip_single_stack
                if _ipv6:
                    _json[domu]['client']['oldipv6Address'] = _ipv6
                _client_gateway_single_stack, _client_gatewayv6 = _nw_utils.mGetIPv4IPv6Payload(_entry['client'], key_single_stack='gateway', key_dual_stack='v6gateway')
                _client_netmask_single_stack, _client_netmaskv6 = _nw_utils.mGetIPv4IPv6Payload(_entry['client'], key_single_stack='netmask', key_dual_stack='v6netmask')
                if _client_netmask_single_stack:
                    _json[domu]['client']['oldnetmask'] = _client_netmask_single_stack
                if _client_netmaskv6:
                    _json[domu]['client']['oldv6netmask'] = _client_netmaskv6
                if _client_gateway_single_stack:
                    _json[domu]['client']['oldgateway'] = _client_gateway_single_stack
                if _client_gatewayv6:
                    _json[domu]['client']['oldv6gateway'] = _client_gatewayv6
                _json[domu]['client']['oldmacAddress'] = _entry['client']['mac']
                _json[domu]['client']['oldvlan1'] = _entry['client']['vlantag']
        
                _json[domu]['oldHostname'] = _entry['client']['hostname']+'.'+_entry['client']['domainname']

                _ip_single_stack, _ipv6 = _nw_utils.mGetIPv4IPv6Payload(_entry['backup'])
                if _ip_single_stack:
                    _json[domu]['backup']['oldipAddress'] = _ip_single_stack
                if _ipv6:
                    _json[domu]['backup']['oldipv6Address'] = _ipv6
                _json[domu]['backup']['oldhostname'] = _entry['backup']['hostname']
                _json[domu]['backup']['olddomainname'] = _entry['backup']['domainname']
                _backup_gateway_single_stack, _backup_gatewayv6 = _nw_utils.mGetIPv4IPv6Payload(_entry['backup'], key_single_stack='gateway', key_dual_stack='v6gateway')
                _backup_netmask_single_stack, _backup_netmaskv6 = _nw_utils.mGetIPv4IPv6Payload(_entry['backup'], key_single_stack='netmask', key_dual_stack='v6netmask')
                if _backup_netmask_single_stack:
                    _json[domu]['backup']['oldnetmask'] = _backup_netmask_single_stack
                if _backup_netmaskv6:
                    _json[domu]['backup']['oldv6netmask'] = _backup_netmaskv6
                if _backup_gateway_single_stack:
                    _json[domu]['backup']['oldgateway'] = _backup_gateway_single_stack
                if _backup_gatewayv6:
                    _json[domu]['backup']['oldv6gateway'] = _backup_gatewayv6
                _json[domu]['backup']['oldmacAddress'] = _entry['backup']['mac']
                _json[domu]['backup']['oldvlan2'] = _entry['backup']['vlantag']
        
                break
     
    #ebLogInfo(f"_json: {_json}")
    return _json

# Execute gridSetup.sh to reconfigure the clusterware using the updated rsp file
def mGridReconfig(aCluObj, aOptions, aJson):
    _json = aJson
    _obj = aCluObj

    _srcDomU = _obj.mReturnDom0DomUPair()[0][1]
    
    if "grid_version" in aOptions.jsonconf:
        _gi_home = aOptions.jsonconf['grid_version']

    _node = exaBoxNode(get_gcontext())
    _node.mConnect(aHost=_srcDomU)

    _rspfile = "Grid-"+_json[_srcDomU.split('.')[0]]['oldHostname']+".rsp" 
 
    _cmd = f'/usr/bin/su grid -c "{_gi_home}/gridSetup.sh -silent -J-Xss2M -ignorePrereq -J-Doracle.install.grid.validate.CRSInstallLocationUI=false -noCopy -J-Doracle.install.mgmtDB=false -J-Doracle.install.mgmtDB.CDB=false -J-Doracle.install.crs.enableRemoteGIMR=false -responseFile /tmp/{_rspfile}"'
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
    _, _o, _ = _node.mExecuteCmd(_cmd)
    _out = _o.read()
    ebLogInfo("%s: *** Grid setup output::\n %s" % (datetime.datetime.now(), _out))
   
    _node.mDisconnect()

    if "Successfully Setup Software" in _out:
        ebLogInfo("*** Successfully Setup Software, running root.sh")

    else:
        ebLogError("Reconfiguring grid failed")
        raise ExacloudRuntimeError(0x0132, 0x0A, "Reconfiguring grid failed")

# execute root scripts.
def mExecRootScrpt(aCluObj, aOptions, aJson):

    _json = aJson
    _obj = aCluObj

    _srcDomU = _obj.mReturnDom0DomUPair()[0][1]
    if "grid_version" in aOptions.jsonconf:
        _gi_home = aOptions.jsonconf['grid_version']    

    for _, _domU in _obj.mReturnDom0DomUPair():
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_domU)
        _cmd = f'{_gi_home}/root.sh'
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _, _o, _ = _node.mExecuteCmd(_cmd)
        if _node.mGetCmdExitStatus() != 0:
            _err = f"Running root script root.sh failed on {_domU}."
            ebLogError(_err)
            _node.mDisconnect()
            raise ExacloudRuntimeError(0x0133, 0x0A, "Running root script root.sh failed.")

        _out = _o.read()
        ebLogInfo("%s: *** root.sh output::\n %s" % (datetime.datetime.now(), _out))

        _node.mDisconnect()
    
    _rspfile = "Grid-"+_json[_srcDomU.split('.')[0]]['oldHostname']+".rsp"

    _node = exaBoxNode(get_gcontext())
    _node.mSetUser('grid')
    _node.mConnect(aHost=_srcDomU)
    _cmd = f"{_gi_home}/gridSetup.sh -executeConfigTools -responseFile /tmp/{_rspfile} -silent"
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
    _, _o, _ = _node.mExecuteCmd(_cmd)
    if _node.mGetCmdExitStatus() != 0:
        _err = f"Grid Setup config tools failed"
        ebLogError(_err)
        _node.mDisconnect()
        raise ExacloudRuntimeError(0x0132, 0x0A, "Reconfiguring grid software failed")
    
    for _, _domU in _obj.mReturnDom0DomUPair():
        _, _o, _ = _node.mExecuteCmd(f"{_gi_home}/bin/crsctl pin css -n {_domU.split('.')[0]}")

    _node.mDisconnect()

# Bring up proxy instance and mount the ACFS file system.
def mRecreateACFS(aCluObj, aOptions, aJson):
    _obj = aCluObj
    _inputjson = aJson

    _cluster = _obj.mGetClusters().mGetCluster()
    if "grid_version" in aOptions.jsonconf:
        _gi_home = aOptions.jsonconf['grid_version']
    _cludgroups = _cluster.mGetCluDiskGroups()

    _obj.mAddOratabEntry()
    _reconm = None
    _datanm = None

    for _dgid in _cludgroups:
        _dgnm = _obj.mGetStorage().mGetDiskGroupConfig(_dgid).mGetDgName()
        if "RECO" in _dgnm:
            _reconm = _dgnm

        if "DATA" in _dgnm:
            _datanm = _dgnm


    _gi = _inputjson['grid_version'] + "0.0.0"
    _count = 0
    for _dom0, _domU in _obj.mReturnDom0DomUPair():
        # TODO: do we need to do the following for all the domUs
        if not _gi_home:
            _gi_home, _ = _obj.mGetGridHome(_domU)

        _node = exaBoxNode(get_gcontext())
        _node.mSetUser('grid')
        _node.mConnect(aHost=_domU)
        _count = _count + 1

        _node.mExecuteCmd(f"{_gi_home}/bin/asmcmd mount {_reconm}")
        if _node.mGetCmdExitStatus() != 0 and _count == 1:
            _, _o, _ = _node.mExecuteCmd(f"{_gi_home}/bin/kfod op=disks asm_diskstring='o/*/*' disks=all nohdr=TRUE | grep {_reconm}")
            _out = _o.readlines()

            _disklist = []
            for _oline in _out:
                _disk = _oline.strip().split(" ")[1]
                _disklist.append(f"'{_disk}'")
            _diskstr = ",".join(_disklist)

            _, _o, _ = _node.mExecuteCmd(f"{_gi_home}/bin/kfod op=disks asm_diskstring='/dev/exadata_quorum/*' disks=all nohdr=TRUE")
            _out = _o.readlines()

            _disklist = []
            for _oline in _out:
                _disk = _oline.strip().split(" ")[1]
                _disklist.append(_disk)

            _quorumfg = []                                                                                                                                                                                          
            for _, _domU in _obj.mReturnDom0DomUPair():                                                                                                                                                    
                domu = _domU.split('.')[0]  
                _n1hname = _inputjson[domu]['hostName']
                _quorumfg.append( _n1hname.split('.')[0].replace('-','_'))

            _qmdstr=""
            for _disk in _disklist:
                for _fg in _quorumfg:
                    if "quorum" in _disk and _fg.lower() in _disk.lower():
                        _qmdstr = _qmdstr + f"QUORUM FAILGROUP {_fg} disk '{_disk}' "

            _node.mExecuteCmdLog(f"echo \" CREATE DISKGROUP {_reconm} HIGH REDUNDANCY DISK {_diskstr} {_qmdstr} ATTRIBUTE 'cell.smart_scan_capable'='TRUE', 'au_size' = '4M', 'compatible.asm' = '{_gi}', 'compatible.rdbms' = '11.2.0.4', 'compatible.advm' = '{_gi}' ;\" | {_gi_home}/bin/sqlplus / as sysasm")


        _node.mExecuteCmdLog(f"{_gi_home}/bin/srvctl enable asm -proxy -node {_domU}")

        _node.mExecuteCmdLog(f"{_gi_home}/bin/srvctl start asm -proxy -node {_domU}")
        _node.mExecuteCmdLog(f"{_gi_home}/bin/asmcmd  volcreate -G {_datanm} -s 100G acfsvol01")
        _, _o, _ = _node.mExecuteCmd("asmcmd volinfo --all | grep 'Volume Device'")
        _device = _o.read().strip().split(':')[1]
        _node.mDisconnect()

        _node = exaBoxNode(get_gcontext())
        _node.mSetUser('root')
        _node.mConnect(aHost=_domU)

        _node.mExecuteCmdLog("/bin/mkdir -p /acfs01")
        _node.mExecuteCmdLog(f"/sbin/mkfs -t acfs {_device}")
        _node.mExecuteCmdLog(f"/sbin/acfsutil  registry -o nodev -a {_device} /acfs01")

        _res = "ora."+_datanm.lower()+".acfsvol01.acfs"
        _node.mExecuteCmdLog(f"{_gi_home}/bin/crsctl getperm resource {_res}")
        _node.mExecuteCmdLog(f"{_gi_home}/bin/crsctl setperm resource {_res} -u user:oracle:r-x -unsupported")

        _node.mDisconnect()

    # create dbaas_acfs dir
    _obj.mCreateAcfsDirs()

    _dpairs = _obj.mReturnDom0DomUPair()                              
    _domu_list = [ _domu for _ , _domu in _dpairs]                    
    _obj.mCheckCrsIsUp(_domu_list[0], _domu_list)                     

# update the VMs post reconfig
def mPostdomUReconfig(aCluObj, aOptions, aJson):
    _json = aJson

    for _dom0, _domU in aCluObj.mReturnDom0DomUPair():

        _node = exaBoxNode(get_gcontext())
        _node.mSetUser('root')
        _node.mConnect(aHost=_domU)
        # refresh the domu agent certificate
        _node.mExecuteCmdLog("cp -r /opt/oracle/dcs/auth /opt/oracle/dcs/auth.bk")
        _node.mExecuteCmdLog("/opt/oracle/dcs/bin/setupAuthDcs.py")

        # Fix the permissions for successful DB creation.
        _host = _domU.split('.')[0]
        _node.mExecuteCmdLog(f"chmod -f 775 /u01/app/grid/diag/crs/{_host}/crs/*")
        _node.mExecuteCmdLog(f"chmod -f 775 /u01/app/grid/diag/crs/{_host}/crs/log/*")
        _node.mExecuteCmdLog(f"chmod -f 660 /u01/app/grid/diag/crs/{_host}/crs/metadata/*")

        # Reinstall dtrs rpm and restore the dir structures in dtrs dir.
        _node.mExecuteCmdLog("rpm -Uvh /var/opt/oracle/misc/dtrs/*.rpm --force")

        _node.mDisconnect()

    # Remove the rsp file stored in /tmp
    _srcDomU = aCluObj.mReturnDom0DomUPair()[0][1]
    _rspfile = "Grid-"+_json[_srcDomU.split('.')[0]]['oldHostname']+".rsp"
    _node = exaBoxNode(get_gcontext())
    _node.mConnect(aHost=_srcDomU)
    _node.mExecuteCmdLog(f"rm -f /tmp/{_rspfile}")
    _node.mDisconnect()

    # Install AHF (TFA as part of it).
    _hcObj = ebCluHealthCheck(aCluObj, aOptions)
    _hcObjExachk = ebCluExachk(_hcObj, aOptions)
    try:
        _hcObjExachk.mInstallAhf("domU", aOptions)
    except Exception as e:
        ebLogError('*** AHF install failed for domU with error %s' % (str(e)))
        raise ExacloudRuntimeError(0x0129, 0x0A, "Failure during AHF installation setup")
    
    # Store customer provided sshkey in the VMs.
    aCluObj.mPatchVMSSHKey(aOptions)

    # Remove DomU Access if requested through payload
    if "delete_domu_keys" in aOptions.jsonconf and aOptions.jsonconf['delete_domu_keys'].lower() == "true":
        aCluObj.mHandlerRemoveDomUsKeys()

    # Save cluster xml
    aCluObj.mSaveXMLClusterConfiguration()

# change the VM hostname (based on the reconfig payload)
def mDomUChangeHostName(aCluObj, aOptions, aJson):
    _obj = aCluObj
    _inputjson = aJson

    for _dom0, _domU in _obj.mReturnDom0DomUPair():

        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_domU)
        domu = _domU.split('.')[0]
        _n1ohname = _inputjson[domu]['oldHostname']
        _n1oshname = _n1ohname.split('.')[0]
        _n1hname = _inputjson[domu]['hostName']
        _n1shname = _n1hname.split('.')[0]

        _cmd = "sed 's/{0}/{1}/' -i /etc/hosts".format(_n1ohname,_n1hname)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

        _cmd = "sed 's/{0}/{1}/' -i /etc/hosts".format(_n1oshname,_n1shname)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

        _cmd = "sed 's/{0}/{1}/' -i /etc/hostname".format(_n1oshname,_n1shname)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

        _node.mExecuteCmd(f"hostnamectl set-hostname {_n1hname.split('.')[0]}")

        _node.mDisconnect()

def mNetwork(aIP):
    # This is for single stack ipv6 support - even the primary IP received can
    # be ipv6.
    _nw_utils = NetworkUtils()
    if _nw_utils.mIsIPv6(aIP):
        return IPv6Network
    else:
        return IPv4Network

# update rsp file with the info as per payload 
def mGridUpdateOratab(aCluObj, aOptions, aJson):
    _obj = aCluObj
    _inputjson = aJson

    _cluster = _obj.mGetClusters().mGetCluster()
    if "grid_version" in aOptions.jsonconf:
        _gi_home = aOptions.jsonconf['grid_version']    
    _cludgroups = _cluster.mGetCluDiskGroups()

    _datanm = None

    for _dgid in _cludgroups:
        _dgnm = _obj.mGetStorage().mGetDiskGroupConfig(_dgid).mGetDgName()

        if "DATA" in _dgnm:
            _datanm = _dgnm
    
    _quorumfg = ""
    _clusterNodes = ""
    _n1con = None
    _n1cn = None
    _n1cov6n = None
    _n1cv6n = None
    for _, _domU in _obj.mReturnDom0DomUPair():
        domu = _domU.split('.')[0]
        _n1conm = None
        _n1cov6nm = None
        _n1cnm = None
        _n1cv6nm = None
        _n1cogt = None
        _n1cov6gt = None
        _n1cgt = None
        _n1cv6gt = None
        if 'oldnetmask' in _inputjson[domu]['client']:
            _n1conm = _inputjson[domu]['client']['oldnetmask']
        if 'oldv6netmask' in _inputjson[domu]['client']:
            _n1cov6nm = _inputjson[domu]['client']['oldv6netmask']
        if 'netmask' in _inputjson[domu]['client']:
            _n1cnm = _inputjson[domu]['client']['netmask']
        if 'v6netmask' in _inputjson[domu]['client']:
            _n1cv6nm = _inputjson[domu]['client']['v6netmask']
        if 'oldgateway' in _inputjson[domu]['client']:
            _n1cogt = _inputjson[domu]['client']['oldgateway']
        if 'oldv6gateway' in _inputjson[domu]['client']:
            _n1cov6gt = _inputjson[domu]['client']['oldv6gateway']
        if 'gateway' in _inputjson[domu]['client']:
            _n1cgt = _inputjson[domu]['client']['gateway']
        if 'v6gateway' in _inputjson[domu]['client']:
            _n1cv6gt = _inputjson[domu]['client']['v6gateway']
        if _n1cogt and _n1conm:
            # Single stack ipv6 support
            _n1con = mNetwork(_n1cogt)(f"{_n1cogt}/{_n1conm}", strict=False).network_address
        if _n1cgt and _n1cnm:
            _n1cn = mNetwork(_n1cgt)(f"{_n1cgt}/{_n1cnm}", strict=False).network_address
        if _n1cov6gt and _n1cov6nm:
            _n1cov6n = mNetwork(_n1cov6gt)(f"{_n1cov6gt}/{_n1cov6nm}", strict=False).network_address
        if _n1cv6gt and _n1cv6nm:
            _n1cv6n = mNetwork(_n1cv6gt)(f"{_n1cv6gt}/{_n1cv6nm}", strict=False).network_address
        _n1hname = _inputjson[domu]['hostName']
        _n1vname = _inputjson[domu]['vipName']
        _clusterNodes = _clusterNodes + _n1hname+":"+_n1vname + ","
        _quorumfg = _quorumfg + _n1hname.split('.')[0].replace('-','_') + ","

    _clusterNodes = _clusterNodes[:-1]
    _quorumfg = _quorumfg[:-1]
    _scanName = _inputjson['scan']['hostname']

    _cells = _obj.mReturnCellNodes()
    _fglist = _quorumfg.split(',') + [_cell.split('.')[0] for _cell in _cells]
    _fgstr = ",".join(_fglist)

    _pswd = b64decode(_inputjson['adminPassword']).decode('utf8')

    _domU = _obj.mReturnDom0DomUPair()[0][1]                              
    domu = _domU.split('.')[0]           
    _node = exaBoxNode(get_gcontext())   
        
    _node.mConnect(aHost=_domU)         

    # Use the rspfile stored in /tmp (as part of preprovisioning)
    _rspfile = "Grid-"+_inputjson[domu]['oldHostname']+".rsp"             
    _node.mExecuteCmd(f"mv /u01/{_rspfile} /tmp/{_rspfile}")

    _, _o, _ = _node.mExecuteCmd(f"{_gi_home}/bin/kfod op=disks asm_diskstring='/dev/exadata_quorum/*,o/*/*' disks=all nohdr=TRUE | grep {_datanm}")
    _out = _o.readlines()

    _disklist = []
    for _oline in _out:
        _disk = _oline.strip().split(" ")[1]
        _disklist.append(_disk)
    _diskstr = ",".join(_disklist)

    _diskfgmap={}
    for _disk in _disklist:
        for _fg in _fglist:
            if "quorum" in _disk and _fg.lower() in _disk.lower():
                _diskfgmap[_disk] = _fg
            elif "quorum" not in _disk and _fg in _disk:
                _diskfgmap[_disk] = _fg

    _diskfgstr = ""
    for k,v in _diskfgmap.items():
        _diskfgstr = _diskfgstr + k + "," + v + ","
    _diskfgstr = _diskfgstr[:-1]

    if _n1con and _n1cn:
        _cmd = "/bin/sed 's/bondeth0:{0}/bondeth0:{1}/'g -i /tmp/{2}".format(_n1con, _n1cn, _rspfile)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    if _n1cov6n and _n1cv6n:
        _cmd = "/bin/sed 's/bondeth0:{0}/bondeth0:{1}/'g -i /tmp/{2}".format(_n1cov6n, _n1cv6n, _rspfile)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    _cmd = "/bin/sed 's/.*clusterNodes=.*/oracle.install.crs.config.clusterNodes={0}/'g -i /tmp/{1}".format(_clusterNodes, _rspfile)              
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))                             
    _node.mExecuteCmd(_cmd)   
        
    _cmd = "/bin/sed 's/.*scanName=.*/oracle.install.crs.config.gpnp.scanName={0}/'g -i /tmp/{1}".format(_scanName, _rspfile)        
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))                            
    _node.mExecuteCmd(_cmd) 

    _cmd = "/bin/sed 's/oracle.install.asm.SYSASMPassword=.*/oracle.install.asm.SYSASMPassword={0}/'g -i /tmp/{1}".format(_pswd, _rspfile)
    _node.mExecuteCmd(_cmd)

    _cmd = "/bin/sed 's/oracle.install.asm.monitorPassword=.*/oracle.install.asm.monitorPassword={0}/'g -i /tmp/{1}".format(_pswd, _rspfile)
    _node.mExecuteCmd(_cmd)

    _cmd = "/bin/sed 's/oracle.install.asm.diskGroup.FailureGroups=.*/oracle.install.asm.diskGroup.FailureGroups={0}/'g -i /tmp/{1}".format(_fgstr, _rspfile)
    _node.mExecuteCmd(_cmd)
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
   
    _cmd = "/bin/sed -i '/oracle.install.asm.diskGroup.disksWithFailureGroupNames=.*/d' /tmp/{0}".format(_rspfile)
    _node.mExecuteCmd(_cmd)
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))     
 
    #_cmd = "sed -i 's/oracle.install.asm.diskGroup.disksWithFailureGroupNames=.*/oracle.install.asm.diskGroup.disksWithFailureGroupNames={0}/'g /tmp/{1}".format(_diskfgstr, _rspfile)
    _cmd = "echo 'oracle.install.asm.diskGroup.disksWithFailureGroupNames={0}' >> /tmp/{1}".format(_diskfgstr, _rspfile)
    _node.mExecuteCmd(_cmd)
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
    
    _cmd = "/bin/sed -i '/oracle.install.asm.diskGroup.disks=.*/d' /tmp/{0}".format(_rspfile)
    _node.mExecuteCmd(_cmd)
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))

    _cmd = "echo 'oracle.install.asm.diskGroup.disks={0}' >> /tmp/{1}".format(_diskstr, _rspfile)
    #_cmd = "sed -i 's/oracle.install.asm.diskGroup.disks=.*/oracle.install.asm.diskGroup.disks={0}/'g /tmp/{1}".format(_diskstr, _rspfile)
    _node.mExecuteCmd(_cmd)
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))

    _cmd = "sed 's/oracle.install.asm.diskGroup.quorumFailureGroupNames=.*/oracle.install.asm.diskGroup.quorumFailureGroupNames={0}/'g -i /tmp/{1}".format(_quorumfg, _rspfile)
    _node.mExecuteCmd(_cmd)
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))

    _node.mDisconnect()

    for _, _domU in _obj.mReturnDom0DomUPair():

        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_domU)

        _cmd = "sed 's/^+ASM.*//' -i /etc/oratab"
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

        _cmd = f"chown grid:oinstall {_gi_home}/crs/config/rootconfig.sh"
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

        _shrtname = _domU.split('.')[0]
        _cmd = f"rm -rf {_gi_home}/gpnp/{_shrtname}*"
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)
        
        _node.mExecuteCmd("chown grid:oinstall -R /u01/app/grid/diag/crs/")
        _host = _domU.split('.')[0]  
        _oldhost = _inputjson[_host]['oldHostname'].split('.')[0]
        _node.mExecuteCmd(f"rm -rf /u01/app/grid/crsdata/@global ")
        _node.mExecuteCmd(f"rm -rf /u01/app/grid/crsdata/{_host}")
        _node.mExecuteCmd(f"rm -rf /u01/app/grid/crsdata/{_oldhost}")
        _node.mExecuteCmdLog(f"ls -l /u01/app/grid/crsdata/")
        _node.mExecuteCmd(f"rm -rf {_gi_home}/gpnp/{_host}*")
        _node.mExecuteCmd(f"rm -rf {_gi_home}/gpnp/{_oldhost}*")
        _node.mExecuteCmdLog(f"ls -l {_gi_home}/gpnp/")
        _node.mExecuteCmdLog("rm -f /etc/oracle/ocr.loc*")
        _node.mExecuteCmdLog("rm -f /etc/oracle/olr.loc*")
        _node.mExecuteCmdLog("ls -l /etc/oracle/")
        _node.mExecuteCmdLog(f"chmod -f 775 /u01/app/grid/diag/crs/{_host}/crs/*")
        _node.mExecuteCmdLog(f"chmod -f 775 /u01/app/grid/diag/crs/{_host}/crs/log/*")
        _node.mExecuteCmdLog(f"chmod -f 660 /u01/app/grid/diag/crs/{_host}/crs/metadata/*")

        _node.mDisconnect()

# Create new /EXAVMIMAGES/conf/<newVMname>-vm.xml containing new network info
def mUpdateConfXml(aDomU, aDom0Node, aJson, aXml):

    _node = aDom0Node
    _inputjson = aJson
    _xml = aXml
    domu = aDomU.split('.')[0]
    _coip = None
    _coipv6 = None
    _conm = None
    _cov6nm = None
    _cogw = None
    _cov6gw = None

    _host = _inputjson[domu]['hostName']
    _oldhost = _inputjson[domu]['oldHostname']
    _comac = _inputjson[domu]['client']['oldmacAddress']
    if 'oldipAddress' in _inputjson[domu]['client']:
        _coip = _inputjson[domu]['client']['oldipAddress']
    if 'oldipv6Address' in _inputjson[domu]['client']:
        _coipv6 = _inputjson[domu]['client']['oldipv6Address']
    if 'oldnetmask' in _inputjson[domu]['client']:
        _conm = _inputjson[domu]['client']['oldnetmask']
    if 'oldv6netmask' in _inputjson[domu]['client']:
        _cov6nm = _inputjson[domu]['client']['oldv6netmask']
    if 'oldgateway' in _inputjson[domu]['client']:
        _cogw = _inputjson[domu]['client']['oldgateway']
    if 'oldv6gateway' in _inputjson[domu]['client']:
        _cov6gw = _inputjson[domu]['client']['oldv6gateway']
    _covlan = _inputjson[domu]['client']['oldvlan1']

    _boip = None
    _boipv6 = None
    _bonm = None
    _bov6nm = None
    _bogw = None
    _bov6gw = None
    _bomac = _inputjson[domu]['backup']['oldmacAddress']
    if 'oldipAddress' in _inputjson[domu]['backup']:
        _boip = _inputjson[domu]['backup']['oldipAddress']
    if 'oldipv6Address' in _inputjson[domu]['backup']:
        _boipv6 = _inputjson[domu]['backup']['oldipv6Address']
    if 'oldnetmask' in _inputjson[domu]['backup']:
        _bonm = _inputjson[domu]['backup']['oldnetmask']
    if 'oldv6netmask' in _inputjson[domu]['backup']:
        _bov6nm = _inputjson[domu]['backup']['oldv6netmask']
    if 'oldgateway' in _inputjson[domu]['backup']:
        _bogw = _inputjson[domu]['backup']['oldgateway']
    if 'oldv6gateway' in _inputjson[domu]['backup']:
        _bov6gw = _inputjson[domu]['backup']['oldv6gateway']
    _bovlan = _inputjson[domu]['backup']['oldvlan2']
    _bohostnm = _inputjson[domu]['backup']['oldhostname']+"."+_inputjson[domu]['backup']['olddomainname']

    _cip = None
    _cipv6 = None
    _cnm = None
    _cv6nm = None
    _cgw = None
    _cv6gw = None
    _cmac = _inputjson[domu]['client']['macAddress']
    if 'ipAddress' in _inputjson[domu]['client']:
        _cip = _inputjson[domu]['client']['ipAddress']
    if 'ipv6Address' in _inputjson[domu]['client']:
        _cipv6 = _inputjson[domu]['client']['ipv6Address']
    if 'netmask' in _inputjson[domu]['client']:
        _cnm = _inputjson[domu]['client']['netmask']
    if 'v6netmask' in _inputjson[domu]['client']:
        _cv6nm = _inputjson[domu]['client']['v6netmask']
    if 'gateway' in _inputjson[domu]['client']:
        _cgw = _inputjson[domu]['client']['gateway']
    if 'v6gateway' in _inputjson[domu]['client']:
        _cv6gw = _inputjson[domu]['client']['v6gateway']
    _cvlan = _inputjson[domu]['client']['vlan1']

    _bip = None
    _bipv6 = None
    _bgw = None
    _bv6gw = None
    _bnm = None
    _bv6nm = None
    _bmac = _inputjson[domu]['backup']['macAddress']
    if 'ipAddress' in _inputjson[domu]['backup']:
        _bip = _inputjson[domu]['backup']['ipAddress']
    if 'ipv6Address' in _inputjson[domu]['backup']:
        _bipv6 = _inputjson[domu]['backup']['ipv6Address']
    if 'gateway' in _inputjson[domu]['backup']:
        _bgw = _inputjson[domu]['backup']['gateway']
    if 'v6gateway' in _inputjson[domu]['backup']:
        _bv6gw = _inputjson[domu]['backup']['v6gateway']
    if 'netmask' in _inputjson[domu]['backup']:
        _bnm = _inputjson[domu]['backup']['netmask']
    if 'v6netmask' in _inputjson[domu]['backup']:
        _bv6nm = _inputjson[domu]['backup']['v6netmask']
    _bvlan = _inputjson[domu]['backup']['vlan2']
    _bhostnm = _inputjson[domu]['backup']['hostname']+"."+_inputjson[domu]['backup']['domainname']

    
    _cmd = f"sed -i 's/<Hostname>{_oldhost}/<Hostname>{_host}/g' {_xml}"
    _node.mExecuteCmd(_cmd)

    _cmd = f"sed -i 's/<Hostname>{_bohostnm}/<Hostname>{_bhostnm}/g' {_xml}"
    _node.mExecuteCmd(_cmd)

    _cmd = f"sed -i 's/<domuName>{_oldhost}/<domuName>{_host}/g' {_xml}"
    _node.mExecuteCmd(_cmd)

    if _coip and _cip:
        _cmd = f"sed -i 's/<IP_address>{_coip}/<IP_address>{_cip}/g' {_xml}"
        _node.mExecuteCmd(_cmd)

    if _coipv6 and _cipv6:
        _cmd = f"sed -i 's/<IP_address>{_coipv6}/<IP_address>{_cipv6}/g' {_xml}"
        _node.mExecuteCmd(_cmd)

    if _boip and _bip:
        _cmd = f"sed -i 's/<IP_address>{_boip}/<IP_address>{_bip}/g' {_xml}"
        _node.mExecuteCmd(_cmd)

    if _boipv6 and _bipv6:
        _cmd = f"sed -i 's/<IP_address>{_boipv6}/<IP_address>{_bipv6}/g' {_xml}"
        _node.mExecuteCmd(_cmd)

    _cmd = f"sed -i 's/<Mac_address>{_comac}/<Mac_address>{_cmac}/gi' {_xml}"
    _node.mExecuteCmd(_cmd) 

    _cmd = f"sed -i 's/<Mac_address>{_bomac}/<Mac_address>{_bmac}/gi' {_xml}"
    _node.mExecuteCmd(_cmd)  

    if _cogw and _cgw:
        _cmd = f"sed -i 's/<Gateway>{_cogw}/<Gateway>{_cgw}/g' {_xml}"
        _node.mExecuteCmd(_cmd)

    if _cov6gw and _cv6gw:
        _cmd = f"sed -i 's/<Gateway>{_cov6gw}/<Gateway>{_cv6gw}/g' {_xml}"
        _node.mExecuteCmd(_cmd)

    if _bogw and _bgw:
        _cmd = f"sed -i 's/<Gateway>{_bogw}/<Gateway>{_bgw}/g' {_xml}"
        _node.mExecuteCmd(_cmd)

    if _bov6gw and _bv6gw:
        _cmd = f"sed -i 's/<Gateway>{_bov6gw}/<Gateway>{_bv6gw}/g' {_xml}"
        _node.mExecuteCmd(_cmd)

    if _conm and _cnm:
        _cmd = f"sed -i 's/<Netmask>{_conm}/<Netmask>{_cnm}/g' {_xml}"
        _node.mExecuteCmd(_cmd)

    if _cov6nm and _cv6nm:
        _cmd = f"sed -i 's/<Netmask>{_cov6nm}/<Netmask>{_cv6nm}/g' {_xml}"
        _node.mExecuteCmd(_cmd)

    if _bonm and _bnm:
        _cmd = f"sed -i 's/<Netmask>{_bonm}/<Netmask>{_bnm}/g' {_xml}"
        _node.mExecuteCmd(_cmd)

    if _bov6nm and _bv6nm:
        _cmd = f"sed -i 's/<Netmask>{_bov6nm}/<Netmask>{_bv6nm}/g' {_xml}"
        _node.mExecuteCmd(_cmd)

    _cmd = f"sed -i 's/<Vlan_id>{_covlan}/<Vlan_id>{_cvlan}/g' {_xml}"
    _node.mExecuteCmd(_cmd)

    _cmd = f"sed -i 's/<Vlan_id>{_bovlan}/<Vlan_id>{_bvlan}/g' {_xml}"
    _node.mExecuteCmd(_cmd)

# update dom0-domU pair to dom0-preprov VM pair
def mUpdateDom0DomUPair(aOptions, aCluObj):

    _obj = aCluObj

    # If aClusterId is not defined return the first cluster
    # By default contains only entry corresponding to the cluster at hand
    _clusterId = _obj.mGetClusters().mGetCluster().mGetCluId()

    _list = []
    for _dom0, _ in _obj.mReturnDom0DomUPair():
        for _entry in aOptions.jsonconf['preprov_network']['nodes']:
            preprov_network_dom0 = _entry['client']['dom0_oracle_name']
            if preprov_network_dom0 == _dom0.split('.')[0]:
                _list.append([_dom0, _entry['client']['hostname']+'.'+_entry['client']['domainname']])

    _obj.mSetDomUsDom0s(_clusterId, _list)

# update the VM configuration at dom0 level.
def mDom0Reconfig(aCluObj, aOptions, aJson):
    _obj = aCluObj
    _inputjson = aJson

    _newlist = copy.deepcopy(_obj.mReturnDom0DomUPair())

    # update dom0-domU Pair (to dom0-preprovVM pair) to update the VM memory before starting
    mUpdateDom0DomUPair(aOptions, _obj)

    _obj.mManageVMMemory('memset', '_all_', aOptions)

    # reset the dom0-domU pair (to dom0-reconfigVM pair)
    _clusterId = _obj.mGetClusters().mGetCluster().mGetCluId() 
    _obj.mSetDomUsDom0s(_clusterId, _newlist)

    for _dom0, _domU in _obj.mReturnDom0DomUPair():

        domu = _domU.split('.')[0]
        _n1comac = _inputjson[domu]['client']['oldmacAddress']
        _n1bomac = _inputjson[domu]['backup']['oldmacAddress']
        _oldhost = _inputjson[domu]['oldHostname']
        _oldvlan1 = _inputjson[domu]['client']['oldvlan1']
        _oldvlan2 = _inputjson[domu]['backup']['oldvlan2']

        _n1cmac = _inputjson[domu]['client']['macAddress']
        _n1bmac = _inputjson[domu]['backup']['macAddress']
        _vlan1 = _inputjson[domu]['client']['vlan1']
        _vlan2 = _inputjson[domu]['backup']['vlan2']
         
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_dom0)
 
        _obj.mAcquireRemoteLock()
        mUpdateNWScripts(_node, _oldhost, _domU, aJson, _obj, _dom0, aOptions)
        _obj.mReleaseRemoteLock()

        ebLogInfo(f"_oldhost: {_oldhost}, _domU: {_domU}")

        # Update /EXAVMIMAGES/conf/*xml and /EXAVMIMAGES/GuestImages/<VM>/*.conf
        mUpdateConf(_node, _oldhost, _domU, aJson)

        mUpdateLibvirtXml(_node, _oldhost, _domU, aJson)

        mUpdateVlans(_obj, _node, _oldhost, _domU, aJson)

        _cmd = f"grep 'serial.sock' /etc/libvirt/qemu/{_domU}.xml"
        _, _o, _ = _node.mExecuteCmd(_cmd)
        _consoleid = ''.join(_o.read().strip().split("path=")[1].split("/serial.sock")[0])
        ebLogInfo(f"_consoleid: {_consoleid}")

        _cmd = "/usr/bin/virsh undefine {0}".format(_oldhost)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmdLog(_cmd)

        #
        # Update libvirt VM xml with new hostname amd uuid
        #
        _oldentry = f"<name>{_oldhost}"
        _newentry = f"<name>{_domU}"
        _cmd = "sed -i 's/{0}/{1}/g' /etc/libvirt/qemu/{2}.xml".format(_oldentry, _newentry, _domU)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmdLog(_cmd)

        _cmd = "sed -i 's/GuestImages\/{0}/GuestImages\/{1}/g' /etc/libvirt/qemu/{2}.xml".format(_oldhost, _domU, _domU)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmdLog(_cmd)
        
        """
        _uuid = uuid.uuid4()
        _oldentry = "<uuid>.*"
        _newentry = f"<uuid>{_uuid}</uuid>"
        _cmd = "sed -Ei 's|{0}|{1}|g' /etc/libvirt/qemu/{2}.xml".format(_oldentry, _newentry, _domU)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmdLog(_cmd)
        """

        _node.mExecuteCmdLog(f"mv /EXAVMIMAGES/GuestImages/{_oldhost} /EXAVMIMAGES/GuestImages/{_domU}")

        _node.mExecuteCmdLog(f"ln -sf /EXAVMIMAGES/GuestImages/{_domU}/console/write-qemu  {_consoleid}")

        mUpdateNetworkInfo(_obj, _node, _oldhost, _domU, _dom0, _inputjson)

        _cmd = "/usr/bin/virsh define /etc/libvirt/qemu/{0}.xml".format(_domU)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmdLog(_cmd)

        _cmd = "/usr/bin/virsh start {0}".format(_domU)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmdLog(_cmd)

        if _node.mGetCmdExitStatus() != 0:
            _err = f"Failed to start VM {_domU}"
            _node.mDisconnect()
            raise ExacloudRuntimeError(0x0133, 0x0A, _err)

        _node.mDisconnect()

    for _dom0, _domU in _obj.mReturnDom0DomUPair():
        _count = 60
        while not _node.mIsConnectable(aHost=_domU) and _count > 0:
            time.sleep(5)
            _count = _count - 1
        if not _node.mIsConnectable(aHost=_domU):    
            ebLogError("VMs are not connectable")
            raise ExacloudRuntimeError(0x0133, 0x0A, "Failed to start VMs")

    # set password less ssh connectivity for grid and oracle uesrs
    ebLogInfo("set password less ssh connectivity")
    for _user in ["oracle", "grid", "opc"]:
        _obj.mConfigurePasswordLessDomU(_user)

def mUpdateNetworkInfo(aCluObj, aNode, aOldHost, aDomU, aDom0, aJson):
    _obj = aCluObj
    _node = aNode
    _domU = aDomU
    _dom0 = aDom0
    _oldhost = aOldHost
    _inputjson = aJson 
    domu = _domU.split('.')[0]
    _vlan1 = _inputjson[domu]['client']['vlan1']
    _vlan2 = _inputjson[domu]['backup']['vlan2']

    if _obj.mIsHostOL7(_dom0):
        #
        # Update netowork filters for the new hostnames
        #
        _cmd = f"/usr/bin/virsh nwfilter-dumpxml {_oldhost}-net0-exabm > /tmp/{_domU}-net0-exabm.xml"
        _node.mExecuteCmdLog(_cmd)

        _cmd = f"/usr/bin/virsh nwfilter-undefine {_oldhost}-net0-exabm"
        _node.mExecuteCmdLog(_cmd)

        _cmd = f"sed -i 's/{_oldhost}-net0-exabm/{_domU}-net0-exabm/g' /tmp/{_domU}-net0-exabm.xml"
        _node.mExecuteCmdLog(_cmd)

        _cmd = f"/usr/bin/virsh nwfilter-define /tmp/{_domU}-net0-exabm.xml"
        _node.mExecuteCmdLog(_cmd)

        _cmd = f"sed -i 's/{_oldhost}-net0-exabm/{_domU}-net0-exabm/g' /etc/libvirt/qemu/{_domU}.xml"
        _node.mExecuteCmdLog(_cmd)

        _cmd = f"/usr/bin/virsh nwfilter-dumpxml {_oldhost}-net1-exabm > /tmp/{_domU}-net1-exabm.xml"
        _node.mExecuteCmdLog(_cmd)

        _cmd = f"/usr/bin/virsh nwfilter-undefine {_oldhost}-net1-exabm"
        _node.mExecuteCmdLog(_cmd)

        _cmd = f"sed -i 's/{_oldhost}-net1-exabm/{_domU}-net1-exabm/g' /tmp/{_domU}-net1-exabm.xml"
        _node.mExecuteCmdLog(_cmd)

        _cmd = f"/usr/bin/virsh nwfilter-define /tmp/{_domU}-net1-exabm.xml"
        _node.mExecuteCmdLog(_cmd)

        _cmd = f"sed -i 's/{_oldhost}-net1-exabm/{_domU}-net1-exabm/g' /etc/libvirt/qemu/{_domU}.xml"
        _node.mExecuteCmdLog(_cmd)

    elif _obj.mIsHostOL8(_dom0):
        _ctx = get_gcontext()
        _natname = _ctx.mGetRegEntry('_natHN_' +  _domU)
        _chain = f"vm_{_natname.split('.')[0]}"

        _cmd = f"nft flush chain bridge filter {_chain}"
        _node.mExecuteCmdLog(_cmd)

        _cmd = f'nft add rule bridge filter {_chain} oifname "vnet*" iifname bondeth0.{_vlan1} counter accept'
        _node.mExecuteCmdLog(_cmd)

        _cmd = f'nft add rule bridge filter {_chain} iifname "vnet*" oifname bondeth0.{_vlan1} counter accept'
        _node.mExecuteCmdLog(_cmd)

        _cmd = f'nft add rule bridge filter {_chain} oifname "vnet*" iifname bondeth0.{_vlan2} counter accept'
        _node.mExecuteCmdLog(_cmd)

        _cmd = f'nft add rule bridge filter {_chain} iifname "vnet*" oifname bondeth0.{_vlan2} counter accept'
        _node.mExecuteCmdLog(_cmd)

        _curr_time = str(datetime.datetime.now()).replace(" ","T")
        _cmd = f"/bin/cp /etc/nftables/exadata.nft /etc/nftables/exadata.nft.{_curr_time}"
        _node.mExecuteCmdLog(_cmd)

        _cmd = "/usr/sbin/nft list ruleset > /etc/nftables/exadata.nft"
        _node.mExecuteCmdLog(_cmd)

        _cmd = "systemctl restart nftables.service"
        _node.mExecuteCmdLog(_cmd)

        """
        _cmd = "/usr/bin/virsh define /etc/libvirt/qemu/{0}.xml".format(_domU)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmdLog(_cmd)
        """

def mUpdateVlans(aCluObj, aNode, aOldHost, aDomU, aJson):
    _obj = aCluObj
    _node = aNode
    _domU = aDomU
    _inputjson = aJson
    _oldhost = aOldHost

    domu = _domU.split('.')[0]
    _n1comac = _inputjson[domu]['client']['oldmacAddress']
    _n1bomac = _inputjson[domu]['backup']['oldmacAddress']
    _oldhost = _inputjson[domu]['oldHostname']
    _oldvlan1 = _inputjson[domu]['client']['oldvlan1']
    _oldvlan2 = _inputjson[domu]['backup']['oldvlan2']

    _n1cmac = _inputjson[domu]['client']['macAddress']
    _n1bmac = _inputjson[domu]['backup']['macAddress']
    _vlan1 = _inputjson[domu]['client']['vlan1']
    _vlan2 = _inputjson[domu]['backup']['vlan2']

    _cmd = "brctl show"
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
    _node.mExecuteCmdLog(_cmd)

    _obj.mAcquireRemoteLock()

    _cmd = f"/opt/exadata_ovm/vm_maker --remove-bridge vmbondeth0.{_oldvlan1} --force"
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
    _node.mExecuteCmdLog(_cmd)
   
    _cmd = f"/opt/exadata_ovm/vm_maker --remove-bridge vmbondeth0.{_oldvlan2} --force"
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
    _node.mExecuteCmdLog(_cmd)

    _cmd = f"/opt/exadata_ovm/vm_maker --add-bonded-bridge vmbondeth0 --first-slave eth1 --second-slave  eth2 --vlan {_vlan1}  --bond-mode active-backup"
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
    _node.mExecuteCmdLog(_cmd)

    _cmd = f"/opt/exadata_ovm/vm_maker --add-bonded-bridge vmbondeth0 --first-slave eth1 --second-slave  eth2 --vlan {_vlan2} --bond-mode active-backup"
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
    _node.mExecuteCmdLog(_cmd)
    
    _obj.mReleaseRemoteLock()

    _cmd = "brctl show"
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
    _node.mExecuteCmdLog(_cmd)

    #
    # Update vmbondeth vlan xmls
    #
    _dir = f"/EXAVMIMAGES/GuestImages/{_oldhost}"
    _cmd = f"cp {_dir}/vmbondeth0.{_oldvlan1}.xml {_dir}/vmbondeth0.{_vlan1}.xml"
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
    _node.mExecuteCmdLog(_cmd)

    _cmd = f"sed -i 's/vmbondeth0.{_oldvlan1}/vmbondeth0.{_vlan1}/g' {_dir}/vmbondeth0.{_vlan1}.xml"
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
    _node.mExecuteCmdLog(_cmd)

    _cmd = f"sed -i 's/{_n1comac}/{_n1cmac}/g' {_dir}/vmbondeth0.{_vlan1}.xml"
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
    _node.mExecuteCmdLog(_cmd)

    _cmd = f"mv {_dir}/vmbondeth0.{_oldvlan1}.xml {_dir}/vmbondeth0.{_oldvlan1}.xml_bkup"
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
    _node.mExecuteCmdLog(_cmd)

    _cmd = f"cp {_dir}/vmbondeth0.{_oldvlan2}.xml {_dir}/vmbondeth0.{_vlan2}.xml"
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
    _node.mExecuteCmdLog(_cmd)
    
    _cmd = f"sed -i 's/vmbondeth0.{_oldvlan2}/vmbondeth0.{_vlan2}/g' {_dir}/vmbondeth0.{_vlan2}.xml"
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
    _node.mExecuteCmdLog(_cmd)
    
    _cmd = f"sed -i 's/{_n1bomac}/{_n1bmac}/g' {_dir}/vmbondeth0.{_vlan2}.xml"
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
    _node.mExecuteCmdLog(_cmd) 

    _cmd = f"mv {_dir}/vmbondeth0.{_oldvlan2}.xml {_dir}/vmbondeth0.{_oldvlan2}.xml_bkup"
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
    _node.mExecuteCmdLog(_cmd)

def mUpdateLibvirtXml(aNode, aOldHost, aDomU, aJson):
    _node = aNode
    _domU = aDomU
    _inputjson = aJson
    _oldhost = aOldHost

    domu = _domU.split('.')[0]
    _n1comac = _inputjson[domu]['client']['oldmacAddress']
    _n1bomac = _inputjson[domu]['backup']['oldmacAddress']
    _oldhost = _inputjson[domu]['oldHostname']
    _oldvlan1 = _inputjson[domu]['client']['oldvlan1']
    _oldvlan2 = _inputjson[domu]['backup']['oldvlan2']

    _n1cmac = _inputjson[domu]['client']['macAddress']
    _n1bmac = _inputjson[domu]['backup']['macAddress']
    _vlan1 = _inputjson[domu]['client']['vlan1']
    _vlan2 = _inputjson[domu]['backup']['vlan2']

    _cmd = "cp /etc/libvirt/qemu/{0}.xml /tmp/{1}.xml".format(_oldhost, _oldhost)
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
    _node.mExecuteCmdLog(_cmd)
    
    _cmd = "cp /etc/libvirt/qemu/{0}.xml /etc/libvirt/qemu/{1}.xml".format(_oldhost, _domU)
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
    _node.mExecuteCmdLog(_cmd)

    # 
    # Update client and backup mac in libvirt VM xml
    #
    _cmd = "sed -i 's/{0}/{1}/gi' /etc/libvirt/qemu/{2}.xml".format(_n1comac,_n1cmac, _domU)
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
    _node.mExecuteCmd(_cmd)

    _cmd = "sed -i 's/{0}/{1}/gi' /etc/libvirt/qemu/{2}.xml".format(_n1bomac,_n1bmac, _domU)
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
    _node.mExecuteCmd(_cmd)

    # 
    # Update libvirt VM xml with new vlan
    #
    _cmd = "sed -i 's/vmbondeth0.{0}/vmbondeth0.{1}/gi' /etc/libvirt/qemu/{2}.xml".format(_oldvlan1, _vlan1, _domU)
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
    _node.mExecuteCmd(_cmd)

    _cmd = "sed -i 's/vmbondeth0.{0}/vmbondeth0.{1}/gi' /etc/libvirt/qemu/{2}.xml".format(_oldvlan2, _vlan2, _domU)
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
    _node.mExecuteCmd(_cmd)

    _cmd = f"/usr/bin/virsh dumpxml {_oldhost} | grep 'source bridge'"
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
    _node.mExecuteCmdLog(_cmd)
    
    _cmd = f"/usr/bin/virsh define /etc/libvirt/qemu/{_domU}.xml"
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
    _node.mExecuteCmdLog(_cmd)

    _cmd = f"/usr/bin/virsh dumpxml {_oldhost} | grep 'source bridge'"
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
    _node.mExecuteCmdLog(_cmd)

#Update /EXAVMIMAGES/conf/*xml and /EXAVMIMAGES/GuestImages/<VM>/*.conf 
def mUpdateConf(aNode, aOldHost, aDomU, aJson):

    _node = aNode
    _inputjson = aJson
    _domU = aDomU
    _oldhost = aOldHost

    _xml = f"/EXAVMIMAGES/conf/{aDomU}-vm.xml"
    _oldxml = f"/EXAVMIMAGES/conf/{_oldhost}-vm.xml"
    _cmd = f"cp {_oldxml} {_xml}"
    _node.mExecuteCmd(_cmd)

    _node.mExecuteCmd(f"cp {_oldxml} /tmp/{_oldhost}-vm.xml")
    # Create /EXAVMIMAGES/conf/<newVMname>-vm.xml containing new network info    
    mUpdateConfXml(_domU, _node, _inputjson, _xml)

    _cmd = f"/bin/ls /EXAVMIMAGES/GuestImages/{_oldhost}/*.conf"
    _, _out, _err = _node.mExecuteCmd(_cmd)
    _rc = _node.mGetCmdExitStatus()                     
                  
    if _rc != 0:  
        _node.mDisconnect()                             
        raise ExacloudRuntimeError(aErrorMsg="Error in listing conf files")                  
    
    # Create copy of the following preprov VM conf files with the reconfig VM name
    # and update the network configurations in the the new conf files
    # /EXAVMIMAGES/GuestImages/r16-uxf2x1.client2.examvm.oraclevcn.com/c1608n12c5.client.preprovvcnmain.oraclevcn.com.cell.a73b4ecc86094ba2a8d96221400f8eea.conf
    # and 
    # c1608n12c5.client.preprovvcnmain.oraclevcn.com.virtualmachine.a73b4ecc86094ba2a8d96221400f8eea.conf
    _oldconfs = _out.readlines()            
    for _entry in _oldconfs:
        _oldconf = _entry.strip()
        _node.mExecuteCmd(f"cp {_oldconf} {_oldconf}_bk")
        # construct the reconfigVM conf file name
        # reconfigVM.client.preprovvcnmain.oraclevcn.com.virtualmachine.a73b4ecc86094ba2a8d96221400f8eea.conf
        _conf = "/".join(_oldconf.split('/')[0:-1]) + "/" + _oldconf.split('/')[-1].replace(_oldhost, _domU)
        _node.mExecuteCmd(f"cp {_oldconf} {_conf}")
        mUpdateConfXml(_domU, _node, _inputjson, _conf)

"""
Update the ifcfg-bondeth* files with ip, netmask, gatewayi, broadcast address
#### DO NOT REMOVE THESE LINES ####
#### %GENERATED BY CELL% ####
DEVICE=bondeth0
BOOTPROTO=none
ONBOOT=yes
HOTPLUG=no
IPV6INIT=no
IPADDR=10.0.4.5
NETMASK=255.255.254.0
GATEWAY=10.0.4.1
NETWORK=10.0.4.0
BROADCAST=10.0.5.255
ARPCHECK=no
"""
def mUpdateNWScripts(aNode, aVM, aDomU, aJson, aObj, aDom0, aOptions):
    _vm = aVM
    _obj = aObj
    _dom0 = aDom0
    _domUPassed = aDomU
    domu = _domUPassed.split('.')[0]
    _node = aNode
    _inputjson = aJson
    _n1coip = None
    _n1coipv6 = None
    _n1cip = None
    _n1cipv6 = None
    _n1conm = None
    _n1cov6nm = None
    _n1cnm = None
    _n1cv6nm = None
    _n1cogt = None
    _n1cov6gt = None
    _n1cgt = None
    _n1cv6gt = None
    _nw_utils = NetworkUtils()

    _n1ohname = _inputjson[domu]['oldHostname']
    _n1oshname = _n1ohname.split('.')[0]
    _n1hname = _inputjson[domu]['hostName']
    _n1shname = _n1hname.split('.')[0]
    if 'oldipAddress' in _inputjson[domu]['client']:
        _n1coip = _inputjson[domu]['client']['oldipAddress']
    if 'oldipv6Address' in _inputjson[domu]['client']:
        _n1coipv6 = _inputjson[domu]['client']['oldipv6Address']
    if 'ipAddress' in _inputjson[domu]['client']:
        _n1cip = _inputjson[domu]['client']['ipAddress']
    if 'ipv6Address' in _inputjson[domu]['client']:
        _n1cipv6 = _inputjson[domu]['client']['ipv6Address']
    if 'oldnetmask' in _inputjson[domu]['client']:
        _n1conm = _inputjson[domu]['client']['oldnetmask']
    if 'oldv6netmask' in _inputjson[domu]['client']:
        _n1cov6nm = _inputjson[domu]['client']['oldv6netmask']
    if 'netmask' in _inputjson[domu]['client']:
        _n1cnm = _inputjson[domu]['client']['netmask']
    if 'v6netmask' in _inputjson[domu]['client']:
        _n1cv6nm = _inputjson[domu]['client']['v6netmask']
    if 'oldgateway' in _inputjson[domu]['client']:
        _n1cogt = _inputjson[domu]['client']['oldgateway']
    if 'oldv6gateway' in _inputjson[domu]['client']:
        _n1cov6gt = _inputjson[domu]['client']['oldv6gateway']
    if 'gateway' in _inputjson[domu]['client']:
        _n1cgt = _inputjson[domu]['client']['gateway']
    if 'v6gateway' in _inputjson[domu]['client']:
        _n1cv6gt = _inputjson[domu]['client']['v6gateway']

    _n1conmb = None
    _n1cnmb = None
    # get the netmask
    if _n1conm:
        # Single stack ipv6
        if _nw_utils.mIsIPv6(_n1coip):
            _n1conmb = _n1conm
        else:
            _n1conmb = IPv4Network(f"0.0.0.0/{_n1conm}").prefixlen

    if _n1cnm:
        if _nw_utils.mIsIPv6(_n1cip):
            _n1cnmb = _n1cnm
        else:
            _n1cnmb = IPv4Network(f"0.0.0.0/{_n1cnm}").prefixlen

    # For IPv6 - netmask is passed as prefix length
    _n1cov6nmb = _n1cov6nm
    _n1cv6nmb = _n1cv6nm

    _n1con = None
    _n1cn = None
    _n1cov6n = None
    _n1cv6n = None
    _n1cobc = None
    _n1cbc = None
    _n1cov6bc = None
    _n1cv6bc = None
    # get the network address
    if _n1cogt and _n1conm:
        _n1con = mNetwork(_n1cogt)(f"{_n1cogt}/{_n1conm}", strict=False).network_address

    if _n1cgt and _n1cnm:
        _n1cn = mNetwork(_n1cgt)(f"{_n1cgt}/{_n1cnm}", strict=False).network_address

    # get the IPv6 network address.
    if _n1cov6gt and _n1cov6nm:
        _n1cov6n = IPv6Network(f"{_n1cov6gt}/{_n1cov6nm}", strict=False).network_address

    if _n1cv6gt and _n1cv6nm:
        _n1cv6n = IPv6Network(f"{_n1cv6gt}/{_n1cv6nm}", strict=False).network_address

    # get the broadcast address
    if _n1cogt and _n1conm:
        _n1cobc = mNetwork(_n1cogt)(f"{_n1cogt}/{_n1conm}", strict=False).broadcast_address

    if _n1cgt and _n1cnm:
        _n1cbc = mNetwork(_n1cgt)(f"{_n1cgt}/{_n1cnm}", strict=False).broadcast_address

    # Get the Ipv6 broadcast address
    if _n1cov6gt and _n1cov6nm:
        _n1cov6bc = IPv6Network(f"{_n1cov6gt}/{_n1cov6nm}", strict=False).broadcast_address

    if _n1cv6gt and _n1cv6nm:
        _n1cv6bc = IPv6Network(f"{_n1cv6gt}/{_n1cv6nm}", strict=False).broadcast_address

    _n1boip = None
    _n1boipv6 = None
    _n1bip = None
    _n1bipv6 = None
    _n1bonm = None
    _n1bov6nm = None
    _n1bnm = None
    _n1bv6nm = None
    _n1bogt = None
    _n1bov6gt = None
    _n1bgt = None
    _n1bv6gt = None
    if 'oldipAddress' in _inputjson[domu]['backup']:
        _n1boip = _inputjson[domu]['backup']['oldipAddress']
    if 'oldipv6Address' in _inputjson[domu]['backup']:
        _n1boipv6 = _inputjson[domu]['backup']['oldipv6Address']
    if 'ipAddress' in _inputjson[domu]['backup']:
        _n1bip = _inputjson[domu]['backup']['ipAddress']
    if 'ipv6Address' in _inputjson[domu]['backup']:
        _n1bipv6 = _inputjson[domu]['backup']['ipv6Address']
    if 'oldnetmask' in _inputjson[domu]['backup']:
        _n1bonm = _inputjson[domu]['backup']['oldnetmask']
    if 'oldv6netmask' in _inputjson[domu]['backup']:
        _n1bov6nm = _inputjson[domu]['backup']['oldv6netmask']
    if 'netmask' in _inputjson[domu]['backup']:
        _n1bnm = _inputjson[domu]['backup']['netmask']
    if 'v6netmask' in _inputjson[domu]['backup']:
        _n1bv6nm = _inputjson[domu]['backup']['v6netmask']
    if 'oldgateway' in _inputjson[domu]['backup']:
        _n1bogt = _inputjson[domu]['backup']['oldgateway']
    if 'oldv6gateway' in _inputjson[domu]['backup']:
        _n1bov6gt = _inputjson[domu]['backup']['oldv6gateway']
    if 'gateway' in _inputjson[domu]['backup']:
        _n1bgt = _inputjson[domu]['backup']['gateway']
    if 'v6gateway' in _inputjson[domu]['backup']:
        _n1bv6gt = _inputjson[domu]['backup']['v6gateway']

    _n1bonmb = None
    _n1bnmb = None
    if _n1bonm:
        if _nw_utils.mIsIPv6(_n1boip):
            _n1bonmb = _n1bonm
        else:
            _n1bonmb = IPv4Network(f"0.0.0.0/{_n1bonm}").prefixlen
    if _n1bnm:
        if _nw_utils.mIsIPv6(_n1bip):
            _n1bnmb = _n1bnm
        else:
            _n1bnmb = IPv4Network(f"0.0.0.0/{_n1bnm}").prefixlen

    # netmask received will be a prefix length for IPv6 case
    _n1bov6nmb = _n1bov6nm
    _n1bv6nmb = _n1bv6nm

    _n1bon = None
    _n1bn = None
    # get the network address
    if _n1bogt and _n1bonm:
        _n1bon = mNetwork(_n1bogt)(f"{_n1bogt}/{_n1bonm}", strict=False).network_address
    if _n1bgt and _n1bnm:
        _n1bn = mNetwork(_n1bgt)(f"{_n1bgt}/{_n1bnm}", strict=False).network_address

    _n1bov6n = None
    _n1bv6n = None
    # get the IPv6 network address
    if _n1bov6gt and _n1bov6nm:
        _n1bov6n = IPv6Network(f"{_n1bov6gt}/{_n1bov6nm}", strict=False).network_address
    if _n1bv6gt and _n1bv6nm:
        _n1bv6n = IPv6Network(f"{_n1bv6gt}/{_n1bv6nm}", strict=False).network_address

    _n1bobc = None
    _n1bbc = None
    _n1bov6bc = None
    _n1bv6bc = None
    # get the broadcast address
    if _n1bogt and _n1bonm:
        _n1bobc = mNetwork(_n1bogt)(f"{_n1bogt}/{_n1bonm}", strict=False).broadcast_address
    if _n1bgt and _n1bnm:
        _n1bbc = mNetwork(_n1bgt)(f"{_n1bgt}/{_n1bnm}", strict=False).broadcast_address
    
    if not _node.mFileExists("/opt/exacloud/bin/dmgr.py"):
        _script = 'scripts/images/dmgr.py'
        _path = '/opt/exacloud/bin/'
        _cmd  = '/bin/mkdir -p /opt/exacloud/bin'
        _node.mExecuteCmdLog(_cmd)
        _node.mCopyFile(_script, _path + 'dmgr.py')

    # get the IPv6 broadcast address
    if _n1bov6gt and _n1bov6nm:
        _n1bov6bc = IPv6Network(f"{_n1bov6gt}/{_n1bov6nm}", strict=False).broadcast_address
    if _n1bv6gt and _n1bv6nm:
        _n1bv6bc = IPv6Network(f"{_n1bv6gt}/{_n1bv6nm}", strict=False).broadcast_address

    _fs = f"/mnt/vmfs_{_vm}" 
    _cmd = f'/usr/bin/python3 /opt/exacloud/bin/dmgr.py mount {_vm} -ml LVDbSys1 -mp {_fs}'
    _node.mExecuteCmd(_cmd)

    if _n1coip and _n1cip:
        _cmd = "sed -i 's/{0}/{1}/g' {2}/etc/sysconfig/network-scripts/ifcfg-bondeth0".format(_n1coip,_n1cip, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    if _n1coipv6 and _n1cipv6:
        _cmd = "sed -i 's/{0}/{1}/g' {2}/etc/sysconfig/network-scripts/ifcfg-bondeth0".format(_n1coipv6,_n1cipv6, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    if _n1conm and _n1cnm:
        _cmd = "sed -i 's/{0}/{1}/g' {2}/etc/sysconfig/network-scripts/ifcfg-bondeth0".format(_n1conm,_n1cnm, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    if _n1cov6nm and _n1cv6nm:
        _cmd = "sed -i 's/{0}/{1}/g' {2}/etc/sysconfig/network-scripts/ifcfg-bondeth0".format(_n1cov6nm,_n1cv6nm, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    if _n1cogt and _n1cgt:
        _cmd = "sed -i 's/{0}/{1}/g' {2}/etc/sysconfig/network-scripts/ifcfg-bondeth0".format(_n1cogt,_n1cgt, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    if _n1cov6gt and _n1cv6gt:
        _cmd = "sed -i 's/{0}/{1}/g' {2}/etc/sysconfig/network-scripts/ifcfg-bondeth0".format(_n1cov6gt,_n1cv6gt, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    if _n1con and _n1cn:
        _cmd = "sed -i 's/{0}/{1}/g' {2}/etc/sysconfig/network-scripts/ifcfg-bondeth0".format(_n1con,_n1cn, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    if _n1cov6n and _n1cv6n:
        _cmd = "sed -i 's/{0}/{1}/g' {2}/etc/sysconfig/network-scripts/ifcfg-bondeth0".format(_n1cov6n,_n1cv6n, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    if _n1cobc and _n1cbc:
        _cmd = "sed -i 's/{0}/{1}/g' {2}/etc/sysconfig/network-scripts/ifcfg-bondeth0".format(_n1cobc,_n1cbc, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    if _n1cov6bc and _n1cv6bc:
        _cmd = "sed -i 's/{0}/{1}/g' {2}/etc/sysconfig/network-scripts/ifcfg-bondeth0".format(_n1cov6bc,_n1cv6bc, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    if _n1cogt and _n1cgt:
        _cmd = "sed -i 's/{0}/{1}/g' {2}/etc/sysconfig/network-scripts/route-bondeth0".format(_n1cogt,_n1cgt, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    if _n1cov6gt and _n1cv6gt:
        _cmd = "sed -i 's/{0}/{1}/g' {2}/etc/sysconfig/network-scripts/route-bondeth0".format(_n1cov6gt,_n1cv6gt, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    if _n1con and _n1conmb and _n1cn and _n1cnmb:
        _cmd = "sed -i 's@{0}/{1}@{2}/{3}@g' {4}/etc/sysconfig/network-scripts/route-bondeth0".format(_n1con,_n1conmb,_n1cn,_n1cnmb, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    if _n1cov6n and _n1cov6nmb and _n1cv6n and _n1cv6nmb:
        _cmd = "sed -i 's@{0}/{1}@{2}/{3}@g' {4}/etc/sysconfig/network-scripts/route-bondeth0".format(_n1cov6n,_n1cov6nmb,_n1cv6n,_n1cv6nmb, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    if _n1boip and _n1bip:
        _cmd = "sed -i 's/{0}/{1}/g' {2}/etc/sysconfig/network-scripts/ifcfg-bondeth1".format(_n1boip,_n1bip, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    if _n1boipv6 and _n1bipv6:
        _cmd = "sed -i 's/{0}/{1}/g' {2}/etc/sysconfig/network-scripts/ifcfg-bondeth1".format(_n1boipv6,_n1bipv6, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    if _n1bonm and _n1bnm:
        _cmd = "sed -i 's/{0}/{1}/g' {2}/etc/sysconfig/network-scripts/ifcfg-bondeth1".format(_n1bonm,_n1bnm, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    if _n1bov6nm and _n1bv6nm:
        _cmd = "sed -i 's/{0}/{1}/g' {2}/etc/sysconfig/network-scripts/ifcfg-bondeth1".format(_n1bov6nm,_n1bv6nm, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    if _n1bogt and _n1bgt:
        _cmd = "sed -i 's/{0}/{1}/g' {2}/etc/sysconfig/network-scripts/ifcfg-bondeth1".format(_n1bogt,_n1bgt, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    if _n1bov6gt and _n1bv6gt:
        _cmd = "sed -i 's/{0}/{1}/g' {2}/etc/sysconfig/network-scripts/ifcfg-bondeth1".format(_n1bov6gt,_n1bv6gt, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    if _n1bon and _n1bn:
        _cmd = "sed -i 's/{0}/{1}/g' {2}/etc/sysconfig/network-scripts/ifcfg-bondeth1".format(_n1bon,_n1bn, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    if _n1bov6n and _n1bv6n:
        _cmd = "sed -i 's/{0}/{1}/g' {2}/etc/sysconfig/network-scripts/ifcfg-bondeth1".format(_n1bov6n,_n1bv6n, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    if _n1bobc and _n1bbc:
        _cmd = "sed -i 's/{0}/{1}/g' {2}/etc/sysconfig/network-scripts/ifcfg-bondeth1".format(_n1bobc,_n1bbc, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    if _n1bov6bc and _n1bv6bc:
        _cmd = "sed -i 's/{0}/{1}/g' {2}/etc/sysconfig/network-scripts/ifcfg-bondeth1".format(_n1bov6bc,_n1bv6bc, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    if _n1bogt and _n1bgt:
        _cmd = "sed -i 's/{0}/{1}/g' {2}/etc/sysconfig/network-scripts/route-bondeth1".format(_n1bogt,_n1bgt, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    if _n1bov6gt and _n1bv6gt:
        _cmd = "sed -i 's/{0}/{1}/g' {2}/etc/sysconfig/network-scripts/route-bondeth1".format(_n1bov6gt,_n1bv6gt, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    if _n1bon and _n1bonmb and _n1bn and _n1bnmb:
        _cmd = "sed -i 's@{0}/{1}@{2}/{3}@g' {4}/etc/sysconfig/network-scripts/route-bondeth1".format(_n1bon,_n1bonmb,_n1bn,_n1bnmb, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    if _n1bov6n and _n1bov6nmb and _n1bv6n and _n1bv6nmb:
        _cmd = "sed -i 's@{0}/{1}@{2}/{3}@g' {4}/etc/sysconfig/network-scripts/route-bondeth1".format(_n1bov6n,_n1bov6nmb,_n1bv6n,_n1bv6nmb, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    if _n1coip and _n1cip:
        _cmd = "sed -i 's/{0}/{1}/g' {2}/etc/ssh/sshd_config".format(_n1coip,_n1cip, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    if _n1coipv6 and _n1cipv6:
        _cmd = "sed -i 's/{0}/{1}/g' {2}/etc/ssh/sshd_config".format(_n1coipv6,_n1cipv6, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    _cmd = "sed 's/{0}/{1}/' -i {2}/etc/hosts".format(_n1ohname,_n1hname, _fs)
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
    _node.mExecuteCmd(_cmd)

    _cmd = "sed 's/{0}/{1}/' -i {2}/etc/hosts".format(_n1oshname,_n1shname, _fs)
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
    _node.mExecuteCmd(_cmd)

    _cmd = "sed 's/{0}/{1}/' -i {2}/etc/hostname".format(_n1oshname,_n1shname, _fs)
    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
    _node.mExecuteCmd(_cmd)

    # update
    if _n1coip and _n1cip:
        _cmd = "sed -i 's/{0}/{1}/g' {2}/etc/hosts".format(_n1coip,_n1cip, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    if _n1coipv6 and _n1cipv6:
        _cmd = "sed -i 's/{0}/{1}/g' {2}/etc/hosts".format(_n1coipv6,_n1cipv6, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    if _n1boip and _n1bip:
        _cmd = "sed -i 's/{0}/{1}/g' {2}/etc/hosts".format(_n1boip,_n1bip, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    if _n1boipv6 and _n1bipv6:
        _cmd = "sed -i 's/{0}/{1}/g' {2}/etc/hosts".format(_n1boipv6,_n1bipv6, _fs)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _node.mExecuteCmd(_cmd)

    for _ , _domU in _obj.mReturnDom0DomUPair():
        if _domU != _domUPassed:
            _n = _domU.split('.')[0]
            _ip = None
            _ipv6 = None
            if 'ipAddress' in _inputjson[_n]['client']:
                _ip = _inputjson[_n]['client']['ipAddress']
            if 'ipv6Address' in _inputjson[_n]['client']:
                _ipv6 = _inputjson[_n]['client']['ipv6Address']
            _host = _inputjson[_n]['hostName']
            if _ip:
                _cmd = "echo '{0} {1} {2}' >> {3}/etc/hosts".format(_ip, _host, _host.split('.')[0], _fs)
                ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
                _node.mExecuteCmd(_cmd)

            if _ipv6:
                _cmd = "echo '{0} {1} {2}' >> {3}/etc/hosts".format(_ipv6, _host, _host.split('.')[0], _fs)
                ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
                _node.mExecuteCmd(_cmd)

            # delete old entries related to preprov env
            _cmd = "sed '/{0}$/d' {1}/etc/hosts".format(_inputjson[_n]['oldHostname'].split('.')[0], _fs)
            ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
            _node.mExecuteCmd(_cmd)

    _newmem = int(aOptions.jsonconf['exaunitAllocations']['memoryGb']) * 1024
    _hv = getHVInstance(_dom0)  
    _currmem = _hv.mGetVMMemory(_vm, 'CUR_MEM')

    # update hugepages based on the new memory for the reconfig VM.
    #mUpdateSysctlConf(_node, _currmem, _newmem, "vm.nr_hugepages", _fs)

    _cmd = f'/usr/bin/python3 /opt/exacloud/bin/dmgr.py umount {_vm} -mp /mnt/vmfs_{_vm}'
    _node.mExecuteCmd(_cmd)


# update hugepages (based on the new memory) by updating the already mounted /etc/sysctl.conf in dom0.
def mUpdateSysctlConf(aNode, aCurrMem, aNewMem, aParam, aFs):

    _memsizeMB = aNewMem
    _currvmem = aCurrMem
    _param = aParam
    _fs = aFs
    _node = aNode
    _hugepagesize = None
    if aParam == "vm.nr_hugepages":
        _cmd = "/bin/grep Hugepagesize /proc/meminfo | /usr/bin/awk '{print$2/1024}'"
        _in, _out, _err = _node.mExecuteCmd(_cmd)
        if _out:
            _out = _out.readlines()
            _hugepagesize = _out[0].strip()
            ebLogInfo("Hugepagesize from meminfo: {0}".format(_hugepagesize))
        if not _hugepagesize:
            #Default of 2MB Hugepagesize
            _hugepagesize = "2"
        ebLogInfo("System mem is : {0}".format(_currvmem))
        _hugepagesize = int(_hugepagesize)
        
    _factor = _memsizeMB / float(_currvmem)
    _in, _out, _err = _node.mExecuteCmd("/usr/sbin/sysctl -n " + _param)
    if not _out:
        ebLogError("Failed to get the value of the sysctl parameter: " + _param)

    curr_paramval = _out.readlines()[0].strip()
    ebLogInfo("*** Current value of %s is %s" % (_param, curr_paramval))
    new_paramval = int(int(curr_paramval) * _factor)
    if _param == "vm.nr_hugepages":
        if (_hugepagesize*new_paramval > _memsizeMB*0.6):
            ebLogWarn("Hugepage memory {0} greater than 60% of new system memory of {1}".format(_hugepagesize*new_paramval, _memsizeMB))
            new_paramval = int((_memsizeMB*0.6)/_hugepagesize)
            ebLogInfo("*** hugepage value after setting it to 60% of the memory : {0}".format(new_paramval)) 

        if new_paramval <= 0:
            ebLogInfo("*** Hugepages are disable, current value: '{0}'".format(curr_paramval))
            return
 
        ebLogInfo("*** Setting hugepage to : {0}".format(new_paramval))    

    _node.mExecuteCmd(f"/usr/bin/cp {_fs}/etc/sysctl.conf {_fs}/etc/sysctl.conf.bkup")
    _file = f"{_fs}/etc/sysctl.conf"

    #sed command to look for the string _param e.g 'vm.nr_hugepages' and replace the whole line with _param = new_paramval
    _cmd = '/usr/bin/sed -i "s/^{0}.*/{0} = {1}/" {2}'.format(_param, new_paramval, _file)

    _in, _out, _err = _node.mExecuteCmd(_cmd)

    if len(_out.readlines()):
        ebLogError("Failed to set the value of the sysctl parameter: %s to %d" % (_param, new_paramval))
    else:
        ebLogInfo("*** The value of the sysctl parameter: %s is set to %d" % (_param, new_paramval))
    return 0

# update quorum configuration to reflect the new VM
def mUpdateQuorumConfig(aCluObj, aOptions, aJson):
    _obj = aCluObj
    _inputjson = aJson
    
    _visibleips =  ""
    _targetips = ""

    count = 0
    for _dom0, _domU in _obj.mReturnDom0DomUPair():

        _node = exaBoxNode(get_gcontext())
        _node.mConnect(_domU)
        
        _node.mExecuteCmdLog("/opt/oracle.SupportTools/quorumdiskmgr --delete --device")

        _node.mExecuteCmdLog("/opt/oracle.SupportTools/quorumdiskmgr --delete --target")

        _node.mExecuteCmdLog("/opt/oracle.SupportTools/quorumdiskmgr --delete --config")
        
        # get value 
        _, _o, _ = _node.mExecuteCmd("ip -4 addr show clre0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}'")  
        _clre0ip = _o.read().strip()                             
        _, _o, _ = _node.mExecuteCmd("ip -4 addr show clre1 | grep -oP '(?<=inet\s)\d+(\.\d+){3}'")
        _clre1ip = _o.read().strip()                             
        _visibleips = _visibleips + _clre0ip + "," + _clre1ip + ","
        if count < 2:
            _targetips = _targetips + _clre0ip + "," + _clre1ip + ","
        count = count + 1
        _node.mDisconnect()

    _targetips = _targetips[:-1]
    _visibleips = _visibleips[:-1]

    ebLogInfo(f"_targetips: {_targetips}")
    ebLogInfo(f"_visibleips: {_visibleips}")

    _cluster = _obj.mGetClusters().mGetCluster()
    _cludgroups = _cluster.mGetCluDiskGroups()

    _reconm = None
    _datanm = None
    _spnm = None

    for _dgid in _cludgroups:
        _dg = _obj.mGetStorage().mGetDiskGroupConfig(_dgid)
        _dgnm = _dg.mGetDgName()
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

    # recreate griddisks in the cells
    for _cell_name in list(_obj.mReturnCellNodes().keys()):
        with connect_to_host(_cell_name, get_gcontext()) as _cell_node:
            if _spnm:
                _cmd = f"create griddisk all HARDDISK prefix='{_datanm},{_reconm},{_spnm}', size='{_datagd},{_recogd},{_spgd}'"
            else:
                _cmd = f"create griddisk all HARDDISK prefix='{_datanm},{_reconm}', size='{_datagd},{_recogd}'"
            _cell_node.mExecuteCmdLog(f'cellcli -e "{_cmd}"')

    for _dom0, _domU in _obj.mReturnDom0DomUPair():

        _node = exaBoxNode(get_gcontext())
        _node.mConnect(_domU)

        _node.mExecuteCmdLog('/opt/oracle.SupportTools/quorumdiskmgr --create --config --owner="grid" --group="asmadmin" --network-iface-list="clre0,clre1"')

        _node.mDisconnect()

    for _dom0, _domU in _obj.mReturnDom0DomUPair():
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(_domU)
        _shname = _domU.split('.')[0]

        _cmd = f'/opt/oracle.SupportTools/quorumdiskmgr --create --target --asm-disk-group={_datanm} --visible-to="{_visibleips}" --host-name="{_shname}" --force'
        _node.mExecuteCmdLog(_cmd)

        _cmd = f'/opt/oracle.SupportTools/quorumdiskmgr --create --target --asm-disk-group={_reconm} --visible-to="{_visibleips}" --host-name="{_shname}" --force'
        _node.mExecuteCmdLog(_cmd)

        if _spnm:
            _cmd = f'/opt/oracle.SupportTools/quorumdiskmgr --create --target --asm-disk-group={_spnm} --visible-to="{_visibleips}" --host-name="{_shname}" --force'
            _node.mExecuteCmdLog(_cmd)

        _node.mDisconnect()

    for _dom0, _domU in _obj.mReturnDom0DomUPair():
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(_domU)
 
        _cmd = f'/opt/oracle.SupportTools/quorumdiskmgr --create --device --target-ip-list="{_targetips}"'
        _node.mExecuteCmdLog(_cmd)

        _, _o, _ = _node.mExecuteCmd("/opt/oracle.SupportTools/quorumdiskmgr --list --device")
        ebLogInfo(f"List of new quorum devices created:")
        _out = _o.readlines()
        for _oline in _out:
            ebLogInfo(f"{_oline}")

        _node.mDisconnect()

def mRunReplaceCmd(aFile=None, aNode=None, aOldKey1=None, aNewKey1=None, aOldKey2=None, aNewKey2=None):
    if not aFile or not aNode:
        return
    if aOldKey1 and aNewKey1 and not aOldKey2 and not aNewKey2:
        _cmd = "sed -i 's/{0}/{1}/g' {2}".format(aOldKey1,aNewKey1,aFile)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        aNode.mExecuteCmd(_cmd)
    if aOldKey1 and aNewKey1 and aOldKey2 and aNewKey2:
        _cmd = "sed -i 's@{0}/{1}@{2}/{3}@g' {4}".format(aOldKey1,aOldKey2,aNewKey1,aNewKey2,aFile)
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        aNode.mExecuteCmd(_cmd)

# update configuration within the VM
def mDomUReconfig(aCluObj, aOptions, aJson):
    _obj = aCluObj
    _inputjson = aJson
    _nw_utils = NetworkUtils()
    for _dom0, _domU in _obj.mReturnDom0DomUPair():

        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_domU)
        domu = _domU.split('.')[0]
        _n1coip = None
        _n1cip = None
        _n1conm = None
        _n1cnm = None
        _n1cogt = None
        _n1cgt = None
        _n1coipv6 = None
        _n1cipv6 = None
        _n1cov6nm = None
        _n1cv6nm = None
        _n1cov6gt = None
        _n1cv6gt = None
        if 'oldipAddress' in _inputjson[domu]['client']:
            _n1coip = _inputjson[domu]['client']['oldipAddress']
        if 'ipAddress' in _inputjson[domu]['client']:
            _n1cip = _inputjson[domu]['client']['ipAddress']
        if 'oldnetmask' in _inputjson[domu]['client']:
            _n1conm = _inputjson[domu]['client']['oldnetmask']
        if 'netmask' in _inputjson[domu]['client']:
            _n1cnm = _inputjson[domu]['client']['netmask']
        if 'oldgateway' in _inputjson[domu]['client']:
            _n1cogt = _inputjson[domu]['client']['oldgateway']
        if 'gateway' in _inputjson[domu]['client']:
            _n1cgt = _inputjson[domu]['client']['gateway']
        if 'oldipv6Address' in _inputjson[domu]['client']:
            _n1coipv6 = _inputjson[domu]['client']['oldipv6Address']
        if 'ipv6Address' in _inputjson[domu]['client']:
            _n1cipv6 = _inputjson[domu]['client']['ipv6Address']
        if 'oldv6netmask' in _inputjson[domu]['client']:
            _n1cov6nm = _inputjson[domu]['client']['oldv6netmask']
        if 'v6netmask' in _inputjson[domu]['client']:
            _n1cv6nm = _inputjson[domu]['client']['v6netmask']
        if 'oldv6gateway' in _inputjson[domu]['client']:
            _n1cov6gt = _inputjson[domu]['client']['oldv6gateway']
        if 'v6gateway' in _inputjson[domu]['client']:
            _n1cv6gt = _inputjson[domu]['client']['v6gateway']
        _n1conmb = None
        _n1cnmb = None
        if _n1conm:
            if _nw_utils.mIsIPv6(_n1coip):
                _n1conmb = _n1conm
            else:
                _n1conmb = IPv4Network(f"0.0.0.0/{_n1conm}").prefixlen
        if _n1cnm:
            if _nw_utils.mIsIPv6(_n1cip):
                _n1cnmb = _n1cnm
            else:
                _n1cnmb = IPv4Network(f"0.0.0.0/{_n1cnm}").prefixlen

        # Netmask for ipv6 is prefix length
        _n1cov6nmb = _n1cov6nm
        _n1cv6nmb = _n1cv6nm

        _n1con = None
        _n1cov6n = None
        _n1cn = None
        _n1cv6n = None
        _n1cobc = None
        _n1cov6bc = None
        _n1cbc = None
        _n1cv6bc = None
        if _n1cogt and _n1conm:
            _n1con = mNetwork(_n1cogt)(f"{_n1cogt}/{_n1conm}", strict=False).network_address
        if _n1cov6gt and _n1cov6nm:
            _n1cov6n = IPv6Network(f"{_n1cov6gt}/{_n1cov6nm}", strict=False).network_address
        if _n1cgt and _n1cnm:
            _n1cn = mNetwork(_n1cgt)(f"{_n1cgt}/{_n1cnm}", strict=False).network_address
        if _n1cv6gt and _n1cv6nm:
            _n1cv6n = IPv6Network(f"{_n1cv6gt}/{_n1cv6nm}", strict=False).network_address
        if _n1cogt and _n1conm:
            _n1cobc = mNetwork(_n1cogt)(f"{_n1cogt}/{_n1conm}", strict=False).broadcast_address
        if _n1cov6gt and _n1cov6nm:
            _n1cov6bc = IPv6Network(f"{_n1cov6gt}/{_n1cov6nm}", strict=False).broadcast_address
        if _n1cgt and _n1cnm:
            _n1cbc = mNetwork(_n1cgt)(f"{_n1cgt}/{_n1cnm}", strict=False).broadcast_address
        if _n1cv6gt and _n1cv6nm:
            _n1cv6bc = IPv6Network(f"{_n1cv6gt}/{_n1cv6nm}", strict=False).broadcast_address

        _n1boip = None
        _n1bip = None
        _n1bonm = None
        _n1bnm = None
        _n1bogt = None
        _n1bgt = None
        if 'oldipAddress' in _inputjson[domu]['backup']:
            _n1boip = _inputjson[domu]['backup']['oldipAddress']
        if 'ipAddress' in _inputjson[domu]['backup']:
            _n1bip = _inputjson[domu]['backup']['ipAddress']
        if 'oldnetmask' in _inputjson[domu]['backup']:
            _n1bonm = _inputjson[domu]['backup']['oldnetmask']
        if 'netmask' in _inputjson[domu]['backup']:
            _n1bnm = _inputjson[domu]['backup']['netmask']
        if 'oldgateway' in _inputjson[domu]['backup']:
            _n1bogt = _inputjson[domu]['backup']['oldgateway']
        if 'gateway' in _inputjson[domu]['backup']:
            _n1bgt = _inputjson[domu]['backup']['gateway']

        _n1boipv6 = None
        _n1bipv6 = None
        _n1bov6nm = None
        _n1bv6nm = None
        _n1bov6gt = None
        _n1bv6gt = None
        if 'oldipv6Address' in _inputjson[domu]['backup']:
            _n1boipv6 = _inputjson[domu]['backup']['oldipv6Address']
        if 'ipv6Address' in _inputjson[domu]['backup']:
            _n1bipv6 = _inputjson[domu]['backup']['ipv6Address']
        if 'oldv6netmask' in _inputjson[domu]['backup']:
            _n1bov6nm = _inputjson[domu]['backup']['oldv6netmask']
        if 'v6netmask' in _inputjson[domu]['backup']:
            _n1bv6nm = _inputjson[domu]['backup']['v6netmask']
        if 'oldv6gateway' in _inputjson[domu]['backup']:
            _n1bov6gt = _inputjson[domu]['backup']['oldv6gateway']
        if 'v6gateway' in _inputjson[domu]['backup']:
            _n1bv6gt = _inputjson[domu]['backup']['v6gateway']
        _n1bonmb = None
        _n1bnmb = None
        if _n1bonm:
            if _nw_utils.mIsIPv6(_n1boip):
                _n1bonmb = _n1bonm
            else:
                _n1bonmb = IPv4Network(f"0.0.0.0/{_n1bonm}").prefixlen
        if _n1bnm:
            if _nw_utils.mIsIPv6(_n1bip):
                _n1bnmb = _n1bnm
            else:
                _n1bnmb = IPv4Network(f"0.0.0.0/{_n1bnm}").prefixlen

        # For IPv6 - netmask will be same as prefix
        _n1bov6nmb = _n1bov6nm
        _n1bv6nmb = _n1bv6nm

        _n1bon = None
        _n1bn = None
        _n1bobc = None
        _n1bbc = None
        if _n1bogt and _n1bonm:
            _n1bon = mNetwork(_n1bogt)(f"{_n1bogt}/{_n1bonm}", strict=False).network_address
        if _n1bgt and _n1bnm:
            _n1bn = mNetwork(_n1bgt)(f"{_n1bgt}/{_n1bnm}", strict=False).network_address
        if _n1bogt and _n1bonm:
            _n1bobc = mNetwork(_n1bogt)(f"{_n1bogt}/{_n1bonm}", strict=False).broadcast_address
        if _n1bgt and _n1bnm:
            _n1bbc = mNetwork(_n1bgt)(f"{_n1bgt}/{_n1bnm}", strict=False).broadcast_address

        _n1bov6n = None
        _n1bv6n = None
        _n1bov6bc = None
        _n1bv6bc = None
        if _n1bov6gt and _n1bov6nm:
            _n1bov6n = IPv6Network(f"{_n1bov6gt}/{_n1bov6nm}", strict=False).network_address
        if _n1bv6gt and _n1bv6nm:
            _n1bv6n = IPv6Network(f"{_n1bv6gt}/{_n1bv6nm}", strict=False).network_address
        if _n1bov6gt and _n1bov6nm:
            _n1bov6bc = IPv6Network(f"{_n1bov6gt}/{_n1bov6nm}", strict=False).broadcast_address
        if _n1bv6gt and _n1bv6nm:
            _n1bv6bc = IPv6Network(f"{_n1bv6gt}/{_n1bv6nm}", strict=False).broadcast_address

        if _n1coip and _n1cip:
            _cmd = "sed -i 's/{0}/{1}/g' /etc/ssh/sshd_config".format(_n1coip,_n1cip)
            ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
            _node.mExecuteCmd(_cmd)

            _cmd = "sed -i 's/{0}/{1}/g' /etc/hosts".format(_n1coip,_n1cip)
            ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
            _node.mExecuteCmd(_cmd)

        if _n1coipv6 and _n1cipv6:
            _cmd = "sed -i 's/{0}/{1}/g' /etc/ssh/sshd_config".format(_n1coipv6,_n1cipv6)
            ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
            _node.mExecuteCmd(_cmd)

            _cmd = "sed -i 's/{0}/{1}/g' /etc/hosts".format(_n1coipv6,_n1cipv6)
            ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
            _node.mExecuteCmd(_cmd)

        if _n1boip and _n1bip:
            _cmd = "sed -i 's/{0}/{1}/g' /etc/hosts".format(_n1boip,_n1bip)
            ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
            _node.mExecuteCmd(_cmd)
        if _n1boipv6 and _n1bipv6:
            _cmd = "sed -i 's/{0}/{1}/g' /etc/hosts".format(_n1boipv6,_n1bipv6)
            ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
            _node.mExecuteCmd(_cmd)

        for _ , _vm in _obj.mReturnDom0DomUPair():
            if _vm != _domU:
                _n = _vm.split('.')[0]
                _ip = None
                _ipv6 = None
                if 'ipAddress' in _inputjson[_n]['client']:
                    _ip = _inputjson[_n]['client']['ipAddress']
                if 'ipv6Address' in _inputjson[_n]['client']:
                    _ipv6 = _inputjson[_n]['client']['ipv6Address']
                _host = _inputjson[_n]['hostName']
                if _ip:
                    _cmd = "echo '{0} {1} {2}' >> /etc/hosts".format(_ip, _host, _host.split('.')[0])
                    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
                    _node.mExecuteCmd(_cmd)
                if _ipv6:
                    _cmd = "echo '{0} {1} {2}' >> /etc/hosts".format(_ipv6, _host, _host.split('.')[0])
                    ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
                    _node.mExecuteCmd(_cmd)

                # delete old entries related to preprov env
                _cmd = "sed '/{0}$/d' /etc/hosts".format(_inputjson[_n]['oldHostname'].split('.')[0])
                ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
                _node.mExecuteCmd(_cmd)

        _files_keys_mapping_bondeth0 = [(_n1coip, _n1cip), (_n1conm, _n1cnm), (_n1cogt, _n1cgt),
                                        (_n1con, _n1cn), (_n1cobc, _n1cbc),(_n1coipv6, _n1cipv6),
                                        (_n1cov6nm, _n1cv6nm), (_n1cov6gt, _n1cv6gt),
                                        (_n1cov6n, _n1cv6n), (_n1cov6bc, _n1cv6bc)]
        for _old_key, _new_key in _files_keys_mapping_bondeth0:
            mRunReplaceCmd("/etc/sysconfig/network-scripts/ifcfg-bondeth0", _node, _old_key, _new_key)

        mRunReplaceCmd("/etc/sysconfig/network-scripts/route-bondeth0", _node, _n1cogt, _n1cgt)
        mRunReplaceCmd("/etc/sysconfig/network-scripts/route-bondeth0", _node, _n1cov6gt, _n1cv6gt)

        mRunReplaceCmd("/etc/sysconfig/network-scripts/route-bondeth0", _node, _n1con, _n1cn, _n1conmb, _n1cnmb)
        mRunReplaceCmd("/etc/sysconfig/network-scripts/route-bondeth0", _node, _n1cov6n, _n1cv6n, _n1cov6nmb, _n1cv6nmb)

        mRunReplaceCmd("/etc/sysconfig/network-scripts/rule-bondeth0", _node, _n1con, _n1cn, _n1conmb, _n1cnmb)
        mRunReplaceCmd("/etc/sysconfig/network-scripts/rule-bondeth0", _node, _n1cov6n, _n1cv6n, _n1cov6nmb, _n1cv6nmb)

        _files_keys_mapping_bondeth1 = [(_n1boip, _n1bip), (_n1bonm,_n1bnm), (_n1bogt,_n1bgt),
                                        (_n1bon,_n1bn), (_n1bobc,_n1bbc), (_n1boipv6, _n1bipv6),
                                        (_n1bov6nm,_n1bv6nm), (_n1bov6gt,_n1bv6gt),
                                        (_n1bov6n,_n1bv6n), (_n1bov6bc,_n1bv6bc)]
        for _old_key, _new_key in _files_keys_mapping_bondeth1:
            mRunReplaceCmd("/etc/sysconfig/network-scripts/ifcfg-bondeth1", _node, _old_key, _new_key)

        mRunReplaceCmd("/etc/sysconfig/network-scripts/route-bondeth1", _node, _n1bogt, _n1bgt)
        mRunReplaceCmd("/etc/sysconfig/network-scripts/route-bondeth1", _node, _n1bov6gt, _n1bv6gt)

        mRunReplaceCmd("/etc/sysconfig/network-scripts/route-bondeth1", _node, _n1bon, _n1bn, _n1bonmb, _n1bnmb)
        mRunReplaceCmd("/etc/sysconfig/network-scripts/route-bondeth1", _node, _n1bov6n, _n1bv6n, _n1bov6nmb, _n1bv6nmb)

        mRunReplaceCmd("/etc/sysconfig/network-scripts/rule-bondeth1", _node, _n1bon, _n1bn, _n1bonmb, _n1bnmb)
        mRunReplaceCmd("/etc/sysconfig/network-scripts/rule-bondeth1", _node, _n1bov6n, _n1bv6n, _n1bov6nmb, _n1bv6nmb)

        if _n1cip:
            _cmd = "grep {0} /etc/ssh/sshd_config".format(_n1cip)
            ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
            _, _o, _ = _node.mExecuteCmd(_cmd)
            if _node.mGetCmdExitStatus() == 0:
                _out = _o.read()
                ebLogInfo("%s: *** DomU Reconfig sshd_config output::\n %s" % (datetime.datetime.now(), _out))

            _cmd = "grep {0} /etc/sysconfig/network-scripts/ifcfg-bondeth0".format(_n1cip)
            ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
            _, _o, _ = _node.mExecuteCmd(_cmd)
            if _node.mGetCmdExitStatus() == 0:
                _out = _o.read()
                ebLogInfo("%s: *** DomU Reconfig ifcfg client output::\n %s" % (datetime.datetime.now(), _out))

        if _n1cipv6:
            _cmd = "grep {0} /etc/ssh/sshd_config".format(_n1cipv6)
            ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
            _, _o, _ = _node.mExecuteCmd(_cmd)
            if _node.mGetCmdExitStatus() == 0:
                _out = _o.read()
                ebLogInfo("%s: *** DomU Reconfig IPv6 sshd_config output::\n %s" % (datetime.datetime.now(), _out))

            _cmd = "grep {0} /etc/sysconfig/network-scripts/ifcfg-bondeth0".format(_n1cipv6)
            ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
            _, _o, _ = _node.mExecuteCmd(_cmd)
            if _node.mGetCmdExitStatus() == 0:
                _out = _o.read()
                ebLogInfo("%s: *** DomU Reconfig IPv6 ifcfg client output::\n %s" % (datetime.datetime.now(), _out))

        if _n1bip:
            _cmd = "grep {0} /etc/sysconfig/network-scripts/ifcfg-bondeth1".format(_n1bip)
            ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
            _, _o, _ = _node.mExecuteCmd(_cmd)
            if _node.mGetCmdExitStatus() == 0:
                _out = _o.read()
                ebLogInfo("%s: *** DomU Reconfig ifcfg backup output::\n %s" % (datetime.datetime.now(), _out))

        if _n1bipv6:
            _cmd = "grep {0} /etc/sysconfig/network-scripts/ifcfg-bondeth1".format(_n1bipv6)
            ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
            _, _o, _ = _node.mExecuteCmd(_cmd)
            if _node.mGetCmdExitStatus() == 0:
                _out = _o.read()
                ebLogInfo("%s: *** DomU Reconfig IPv6 ifcfg backup output::\n %s" % (datetime.datetime.now(), _out))

        _cmd = "service network restart"
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _, _o, _ = _node.mExecuteCmd(_cmd)
        if _node.mGetCmdExitStatus() == 0:
            _out = _o.read()
            ebLogInfo("%s: *** DomU Reconfig network restart output::\n %s" % (datetime.datetime.now(), _out))

        _cmd = "service sshd restart"
        ebLogInfo("%s: *** Running command: %s" % (datetime.datetime.now(), _cmd))
        _, _o, _ = _node.mExecuteCmd(_cmd)
        if _node.mGetCmdExitStatus() == 0:
            _out = _o.read()
            ebLogInfo("%s: *** DomU Reconfig sshd restart output::\n %s" % (datetime.datetime.now(), _out))

        _node.mDisconnect()

    # set password less ssh connectivity for grid and oracle uesrs
    ebLogInfo("set password less ssh connectivity")
    for _user in ["oracle", "grid", "opc"]:
        _obj.mConfigurePasswordLessDomU(_user)

# update storage based on the new input storage (from the payload)
def mUpdateStorage(aCluObj, aOptions):

    _ebox = aCluObj
    _options = aOptions
    _cluster = _ebox.mGetClusters().mGetCluster()
    _cludgroups = _cluster.mGetCluDiskGroups()
    _dgConstantsObj = ebDiskgroupOpConstants()
    
    _dg_sizes_dict = {}
    _cluDgObj = ebCluManageDiskgroup(_ebox, aOptions)
    _dgConstantsObj = _cluDgObj.mGetConstantsObj()
    _rc = 0
    _total_gb = 0
    for _dgid in _cludgroups:
        _dg = _ebox.mGetStorage().mGetDiskGroupConfig(_dgid)
        _dg_type = _dg.mGetDiskGroupType().lower()
        if _dg_type in [_dgConstantsObj._data_dg_type_str, _dgConstantsObj._reco_dg_type_str, _dgConstantsObj._sparse_dg_type_str]:
            _dg_name = _dg.mGetDgName()
            _dgrp_properties = []
            _dgrp_properties.append(_dgConstantsObj._propkey_storage)

            _size_dict = {}
            _rc = _cluDgObj.mUtilGetDiskgroupSize(aOptions, _dg_name, _dgConstantsObj)
            if _rc == -1:
                _detail_error = "Could not fetch info for diskgroup " + _dg_name
                ebLogError(_detail_error)
                raise ExacloudRuntimeError(0x0132, 0x0A, _detail_error)

            ## Save the totalgb size (GB) of diskgroups in the dictionary for restoration.
            if _dg_type == _dgConstantsObj._sparse_dg_type_str:
                _size_dict['totalgb'] = int(_rc) / (1024 * _cluDgObj.mGetConstantsObj().mGetSparseVsizeFactor())  # Size is returned in MBs
            else:
                _size_dict['totalgb'] = int(_rc) / 1024 # Size is returned in MBs
            _rc = 0 

            _dg_sizes_dict[_dg_name] = _size_dict
            _total_gb = _total_gb + _size_dict['totalgb']

            # Sample Json for _dg_sizes_dict
            #    "DATAC7": {
            #        "totalgb": 24552,
            #        "usedgb": 637
            #    },

            # sizes of DATA: RECO: SPARSE DG is retained in the following ratios -               
            # 60:20:20 if disk backup is not enabled    
            # 35:50:15 if disk backup is enabled        
            #  
            # if SPARSE diskgroup is not present,       
            # sizes of DATA: RECO DG is retained in the following ratios -                       
            # 80:20 if disk backup is not enabled       
            # 40:60 if disk backup is enabled          
    """
    To-Do for future enhancements -
    If backup is disabled in preprov
    And if reconfig to be done with backup enabled, resize the storage even
    if old and new size is same

    If sparse is disabled in preprov
    and enabled in reconfig, resie storage should take care of creating sparse
    diskgroup and resize the diskgroups accordingly.
    """
    _json = {}
    _json['OLDSIZE_GB'] = float(_total_gb)/3
    _json['NEWSIZE_GB'] = int(_ebox.mGetDbStorage().split('G')[0])

    _ebox.mAcquireRemoteLock()

    ebLogInfo('*** Performing storage resize operation')
    _storage = ebCluManageStorage(_ebox, aOptions)
    _rc = _storage.mClusterStorageResize(aOptions, _json)

    _ebox.mReleaseRemoteLock()
    ebLogInfo(str(_dg_sizes_dict))

    return _rc
            
