"""
 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    OVM - Healthcheck functionality

FUNCTION:
    Provide basic healthcheck functionality

NOTE:
    None

History:
    MODIFIED (MM/DD/YY)
    aypaul    07/10/25 - Bug#38161432 Support multiprocessing update for shared
                         dictionary.
    aararora  05/28/25 - Bug 37981919: cellcli alerthistory command output is
                         now on multiple lines from 25.x onwards
    ririgoye  08/28/24 - Bug 36455951 - PREVENT LIST INDEX OUT OF RANGE POST
                         DELETE/ADD VM
    naps      08/14/24 - Bug 36949876 - X11 ipconf path changes.
    aypaul    07/29/24 - Bug#36887651 Extend timeout for healthcheck.
    gparada   07/11/24 - Bug 36564670 Replace Queue by ProcessManager.List
    aypaul    05/30/2024 - Issue#36640253 Replace default multiprocess with asyncprocessing module.
    aararora    04/30/2024 - ER 36485120: IPv6 support in exacloud
    scoral      03/28/2022 - Bug 33979523: Remove the Network and Gateway Subnet validation for Admin networks
                             && Compared the hostname part only of the NSlookup output.
    jesandov    08/02/2022 - bug 33635453: Remove CNS support
    jungnlee    07/02/2018 - bug 28258321: use diag_root to save logstash json
    bhuvnkum    11/24/2017 - Bug 27143491: validate scanip down before provisioning
    bhuvnkum    11/24/2017 - Bug 27143661: validate default gw on admin nw
    dekuckre    11/22/2017 - Bug 27082067: Populate the list of hosts in ebCluHealthCheck.
                             && modularize mValidateCluster.                              
    srtata      10/27/2017 - Bug 26984295: fix cnssetup case
    srtata      10/17/2017 - Bug 26984295: add cnssetup
    bhuvnkum    09/27/2017 - Bug 26755489: Add check to validate nw/gw overalpping
    bhuvnkum    09/26/2017 - Bug 26755789: Add check to validate user and group permissions
    bhuvnkum    09/14/2017 - Bug 26608208: Validate DomUImageName, ImageVersion
    bhuvnkum    09/14/2017 - Bug 26755456: Verify Disk Group Naming Convention
    bhuvnkum    09/14/2017 - Bug 26711080: Check for DB Status on Cell
    srtata      09/12/2017 - bug 26716205 : test_cnstopic ecs property
    bhuvnkum    09/07/2017 - Bug 26637738: Configurable domu and optimize ltwt hc 
    bhuvnkum    08/22/2017 - Bug 26480590: Check to match system image for all Dom0s
    srtata      08/21/2017 - bug 26657194: fix mUpdateJson
    seha        08/08/2017 - restructure healthcheck json report
    srtata      07/31/2017 - Bug 26542358: move CNS code to clucns.py
    bhuvnkum    07/27/2017 - Bug 26435219: Check to match Subnet Mask for DomUs & Cells
    bhuvnkum    07/12/2017 - Bug 24451267: Check for root partition space on dom0/switches
    dekuckre    07/07/2017 - Bug 26021077: Check if scan-names in XML are resolvable
    dekuckre    07/10/2017 - 26413578 : Check if grid disks are already
                             created during pre-prov.
    srtata      07/09/2017 - bug 26309263: CNS file format change
    bhuvnkum    06/29/2017 - Bug 26357100: Refactored exachk code to cluexachk.py
    dekuckre    06/16/2017 - Call mGetImageVersion to collect image version in
                             health check report - bug 26194037
    dekuckre    06/09/2017 - 26187395: Add 'stresstest' option for stress testing
    srtata      06/19/2017 - bug 26306665: minor changes in CNS json file
    dekuckre    06/13/2017 - Bug 26202774: Call mDeleteGD(aListOnly=True) to
                             check if grid disks are already created during pre-prov.
    srtata      06/01/2017 - add cns ( cloud notification support) option
    dekuckre    05/11/2017 - Call mCheckDom0Mem to check for available free
                             memory in dom0 during pre-prov - bug 26035758
    bhuvnkum    05/15/2017 - Optimize hc with multithreading support - bug 25689238
    dekuckre    05/09/2017 - Error if stale domU images found during
                             pre-prov - bug 25902691
    bhuvnkum    02/14/2017 - Bug 22730038: Invoke exachk on target nodes
    bhuvnkum    12/16/2016 - Bug 24451162: check for stale locks on dom0s
    hnvenkat    05/16/2016 - Warning if cell_shredding is enabled - bug 22873200
    hnvenkat    05/10/2016 - Switch related checks - smnode list and pkey - bug 23256519
    hnvenkat    04/15/2016 - Ensure XML file has cdb/pdb type entries only - bug 23100818
    hnvenkat    03/08/2016 - ebtables check and whitelist check during pre-prov - bug 22884073
    hnvenkat    03/08/2016 - dom0 n/w consistency check bridge check - bug 22864766
    hnvenkat    03/01/2016 - Introduction of pre and post provisioning hc - bug 22841229
    hnvenkat    02/26/2016 - Cell summary and alerthistory - bug 22833350
    hnvenkat    02/24/2016 - Cell disk healthcheck - bug 22571582
    hnvenkat    02/23/2016 - Minor bug fixes - bug 22808234
    hnvenkat    02/18/2016 - Provide overall test status in json format
    hnvenkat    02/18/2016 - Check keys exist in conf file before reading - bug 22751372
    hnvenkat    02/09/2016 - delta changes to json format
    hnvenkat    02/02/2016 - results in json format
    hnvenkat    12/28/2015 - handle blank dnsServer/ntpServer entries - bug 22444727
    hnvenkat    12/10/2015 - v6 additions
    hnvenkat    12/08/2015 - v5.2 additions
    hnvenkat    11/18/2015 - v4 additions
    hnvenkat    11/05/2015 - v3 additions
    hnvenkat    10/28/2015 - Bunch of v2 additions
    hnvenkat    10/20/2015 - Create file

Changelog:

   03/01/2016 - v9 changes:

       1) Introduce pre and post provisioning options for checks

   02/26/2016 - v8.1 changes:

       1) Provide cell summary and alerthistory details

   02/24/2016 - v8.0 changes:

       1) Check health of physical disks in each cell

   02/18/2016 - v7.2 changes:

       1) Provide overall test status in json format

   02/09/2016 - v7.1 changes:

       1) Log results in separate directory
       2) JSON file to store exacloud version
       3) Return JSON object to caller

   02/02/2016 - v7 changes:

       1) Return results in JSON format, along with text

   12/10/2015 - v6 changes:

       1) Validate ethernet interfaces on Dom0
       2) Validate infiniband interfaces on Dom0
       3) Add dom0 names in log file for easy identification
       4) Ping test from domUs to dom0s (should fail)

   12/08/2015 - v5.2 changes:

       1) 'dig' test for DNS servers during XML file validation
       2) Output more relevant messages to stdout when healthcheck is in progress

   11/18/2015 - v4 changes:
       1) Support for 'user' verification in XML file
       2) Validation of DNS Server entries in XML file
       3) Validation of NTP Server entries in XML file
       4) Validation of diskgroup entries in XML file

   11/05/2015 - v3 changes:
       1) Support for Rack XML file validation
       2) Validation of IP address, ping and nslookup from XML file
       3) Code restructuring - separate methods for xml, conf and cluster validation
       4) Ability to call xml, conf and cluster validation selectively
       5) Introduction of config/healthcheck.conf file

   10/28/2015 - v2 changes:
       1) Ethernet interfaces with IP addresses
       2) Memory on Dom0s (in MB)
       3) Version of ovmutils, perl and python on Dom0s
       4) Display imp elements from exabox.conf
       5) Add a recommendations/warnings section to hc report
       6) Warn if MemSize under vm_size in exabox.conf is > dom0 MemTotal
       7) Recommend change of password for every node that has 'weak' pwd

   10/20/2015 - v1 changes:
       1) Basic check functionality
       2) SSH working yes/no
       3) Password less SSH
       4) Strength of root password for various nodes
       5) Network interfaces on Dom0 that are active
"""

from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogTrace, ebLogWarn, ebLogDebug, ebLogVerbose, ebLogSetHCLogDestination, ebLogRemoveHCLogDestination, ebLogHealth
from exabox.log.LogMgr import ebLogJson
import os, sys, subprocess, uuid, time, os.path, traceback
from exabox.core.Context import get_gcontext
from exabox.core.Core import exaBoxCoreInit
from datetime import datetime
import re
import secrets
import json, copy, socket, crypt
import pickle
import base64
import shutil
from exabox.core.DBStore import ebGetDefaultDB
from multiprocessing import Process
from exabox.ovm.monitor import ebClusterNode
import threading
from exabox.ovm.sysimghandler import (
        getDom0VMImagesInfo, getNewestVMImageArchiveInRepo)
from exabox.ovm.clumisc import ebCluPreChecks, mGetAlertHistoryOptions
from exabox.healthcheck.cluexachk import ebCluExachk
from exabox.ovm.cluconncheck import ebCluConnectivityCheck
from exabox.ovm.hypervisorutils import getHVInstance
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure
from exabox.core.Error import ExacloudRuntimeError

from ipaddress import ip_interface

DEVNULL = open(os.devnull, 'wb')


class ebCluHealthNode(object):

        def __init__(self):

            self.__hostname  = None
            self.__ethifs    = None
            self.__inetlist  = None
            self.__dom0mem   = None
            self.__ovmutilsv = None
            self.__perlv     = None
            self.__pythonv   = None
            self.__vmnum     = None
            self.__ethlink   = None
            self.__ibdevice  = None
            self.__ibports   = None
            self.__ibstate   = None
            self.__ibpstate  = None
            self.__ibpkeylist = None
            self.__domuiso   = None
            self.__cellattr  = None
            self.__celldiskattr = []
            self.__flashattr  = None
            self.__dom0netcons  = None
            self.__dom0bridgelist = None
            self.__dom0bondedifs = []
            self.__dom0ebtables = None

            self.__xmlusers  = None

        def mGetHostname(self):
            return self.__hostname

        def mSetHostname(self, aHostname):
            self.__hostname = aHostname

        def mGetEthifs(self):
            return self.__ethifs

        def mSetEthifs(self, aEthifs):
            self.__ethifs = aEthifs

        def mGetInetlist(self):
            return self.__inetlist

        def mSetInetlist(self, aInetlist):
            self.__inetlist = aInetlist

        def mGetDom0mem(self):
            return self.__dom0mem

        def mSetDom0mem(self, aDom0mem):
            self.__dom0mem = aDom0mem

        def mGetOvmutilsVer(self):
            return self.__ovmutilsv

        def mSetOvmutilsVer(self, aOvmutilsVer):
            self.__ovmutilsv = aOvmutilsVer

        def mGetPerlVer(self):
            return self.__perlv

        def mSetPerlVer(self, aPerlVer):
            self.__perlv = aPerlVer

        def mGetPythonVer(self):
            return self.__pythonv

        def mSetPythonVer(self, aPythonVer):
            self.__pythonv = aPythonVer

        def mGetXmlUsers(self):
            return self.__xmlusers

        def mSetXmlUsers(self, aXmlUsers):
            self.__xmlusers = aXmlUsers

        def mGetVmNum(self):
            return self.__vmnum

        def mSetVmNum(self, aVmNum):
            self.__vmnum = aVmNum

        def mGetEthLink(self):
            return self.__ethlink

        def mSetEthLink(self, aEthLink):
            self.__ethlink = aEthLink

        def mGetIbDevice(self):
            return self.__ibdevice

        def mSetIbDevice(self, aIbDevice):
            self.__ibdevice = aIbDevice

        def mGetIbPorts(self):
            return self.__ibports

        def mSetIbPorts(self, aIbPorts):
            self.__ibports = aIbPorts

        def mGetIbState(self):
            return self.__ibstate

        def mSetIbState(self, aIbState):
            self.__ibstate = aIbState

        def mGetIbPstate(self):
            return self.__ibpstate

        def mSetIbPstate(self, aIbPstate):
            self.__ibpstate = aIbPstate

        def mGetIbPkeylist(self):
            return self.__ibpkeylist

        def mSetIbPkeylist(self, aIbPkeylist):
            self.__ibpkeylist = aIbPkeylist

        def mGetDomuIso(self):
            return self.__domuiso

        def mSetDomuIso(self, aDomuIso):
            self.__domuiso = aDomuIso

        def mGetCellDiskAttr(self):
            return self.__celldiskattr

        def mSetCellDiskAttr(self, aCellDiskAttr):
            self.__celldiskattr = aCellDiskAttr

        def mGetCellAttr(self):
            return self.__cellattr

        def mSetCellAttr(self, aCellAttr):
            self.__cellattr = aCellAttr

        def mGetFlashAttr(self):
            return self.__flashattr

        def mSetFlashAttr(self, aFlashAttr):
            self.__flashattr = aFlashAttr

        def mGetDom0NetCons(self):
            return self.__dom0netcons

        def mSetDom0NetCons(self, aNetCons):
            self.__dom0netcons = aNetCons

        def mGetDom0BridgeList(self):
            return self.__dom0bridgelist

        def mSetDom0BridgeList(self, aBridgeList):
            self.__dom0bridgelist = aBridgeList

        def mGetDom0BondedIfs(self):
            return self.__dom0bondedifs

        def mSetDom0BondedIfs(self, aBondedIfs):
            self.__dom0bondedifs = aBondedIfs

        def mGetDom0Ebtables(self):
            return self.__dom0ebtables

        def mSetDom0Ebtables(self, aEbtables):
            self.__dom0ebtables = aEbtables

class ebCluHealthCheck(object):

        def __init__(self, aExaBoxCluCtrl, aOptions):

            self.__config = get_gcontext().mGetConfigOptions()
            self.__basepath = get_gcontext().mGetBasePath()
            self.__confpath = self.__basepath + "/config/healthcheck.conf"
            self.__hcnameconfpath = self.__basepath + "/config/hcname.conf"
            self.__clusterpath = None
            self.__xmlpath = aOptions.configpath
            self.__ebox = aExaBoxCluCtrl
            self.__eboxnetworks = None
            self.__vmmem = None
            self.__recommend = []
            self.__datetime = None

            # We need the two of them separate for the 'all' option
            self.__preprov = False
            self.__postprov = True
            self.__connectcheck = False
            self.__longruncheck = False
            self.__stresstest = False

            self.__dom0s = {}
            self.__cluster_host_d = {}
            self.__cluster_health_d = {}


            self.__hcconfig = self.mReadHcConfig()
            if self.__hcconfig is None:
                ebLogWarn('*** Healthcheck Config file not found:' + self.__confpath)
            # load hcname.conf that contains predefined pair of hcID and hcName
            self.__hcnameconfig = self.mReadHcNameConfig()
            if self.__hcnameconfig is None:
                ebLogWarn('*** hcName Config file not found:' + self.__hcnameconfpath)

            self.__datetime = datetime.now().strftime('%m%d%y_%H%M%S')
            self.__defloghandler = "healthcheck.log"
            self.__jsonresult = []
            self.__jsonmap = {}
            # jsonresmap dict and testresultList list
            self.__jsonresmap = {}
            self.__testresultList = ['Pass', 'Info', 'Warn', 'Fail']

            if aOptions.healthcheck == 'conf':
                self.__loghandler = "healthcheck-conf-" + self.mGetDateTime() + ".log"
                self.__recohandler = self.mGetLogHandler().split(".")[0]+".tmp"

                self.__jsonhandler = self.__basepath + "/log/checkcluster/" + "healthcheck-conf-" + self.mGetDateTime() + ".json"
            else:
                _eBox = self.mGetEbox()
                _eBoxNetworks = _eBox.mGetNetworks()
                self.mSetEboxNetworks(_eBoxNetworks)
                _eBoxKey = _eBox.mGetKey()
                self.__clusterpath = _eBox.mGetClusterPath()

                if not _eBox.mIsKVM():
                    _dom0s, _domUs, _cells, _switches = _eBox.mReturnAllClusterHosts()
                else:
                    _dom0s, _domUs, _cells, _ = _eBox.mReturnAllClusterHosts()
                    _switches = []

                _domUs_filtered = []
                for _host in _domUs:
                    _ctx = get_gcontext()
                    if _ctx.mCheckRegEntry('_natHN_' + _host):
                       _host = _ctx.mGetRegEntry('_natHN_' + _host)
                    _domUs_filtered.append(_host)

                _cluhosts = _dom0s + _domUs_filtered + _cells + _switches
                _jconf = aOptions.jsonconf
                # Use the hosts mentioned in targetHosts to populate the list
                # of hosts for health check to be run on.
                if (_jconf is not None and "targetHosts" in _jconf.keys()):
                    targetHosts = _jconf["targetHosts"].split(",")
                    _cluhosts = []
                    for host in targetHosts:
                        host = host.lower()
                        if "dom0s" == host:
                            _cluhosts.extend(_dom0s)

                        if "domus" == host:
                            _cluhosts.extend(_domUs_filtered)

                        if "cells" == host:
                            _cluhosts.extend(_cells)

                        if "switches" == host:
                            _cluhosts.extend(_switches)

                #skip adding domus in case of connection check
                if aOptions.healthcheck == 'connection':
                    _jconf = aOptions.jsonconf
                    if _jconf is not None and "domuCheck" in _jconf.keys() and _jconf["domuCheck"] == "True":
                        pass
                    else:
                        _cluhosts = _dom0s + _cells + _switches 

                ebLogInfo("ebCluHealthCheck: List of hosts initialized (_cluhosts) = %s" % (_cluhosts))
                _cluster_host_d = self.mGetClusterHostD()
                _cluster_health_d = self.mGetClusterHealthD()
                self.mSetDom0s(_dom0s)


                #
                # Collect info on all hosts
                #
                for _host in _cluhosts:
                    if _eBox.mIsExabm() or _eBox.mIsOciEXACC():
                        if _host in _domUs_filtered: 
                            _neto = _eBoxNetworks.mGetNetworkConfigByNatName(_host)
                        else: 
                            _neto = _eBoxNetworks.mGetNetworkConfigByName(_host)
                    else: 
                        _neto = _eBoxNetworks.mGetNetworkConfigByName(_host)
                    _clunode = ebClusterNode()
                    _cluhealth = ebCluHealthNode()
                    _cluster_host_d[_host] = _clunode
                    _cluster_health_d[_host] = _cluhealth
                    _clunode.mSetClusterId(_eBoxKey)
                    _clunode.mSetHostname(_host)
                    _cluhealth.mSetHostname(_host)
                    _clunode.mSetNetworkIp(_neto.mGetNetNatAddr())
                    if _host in _dom0s:
                        _clunode.mSetNodeType('dom0')
                    elif _host in _domUs_filtered:
                        _clunode.mSetNodeType('domu')
                    elif _host in _cells:
                        _clunode.mSetNodeType('cell')
                    elif _host in _switches:
                        _clunode.mSetNodeType('switch')

                _rackstr = aExaBoxCluCtrl.mGetClusterName()

                self.__loghandler = "healthcheck-" +_rackstr + "-" + self.mGetDateTime() + ".log"
                self.__recohandler = self.mGetLogHandler().split(".")[0]+".tmp"
                if aOptions.healthcheck == 'stresstest':
                    self.__jsonhandler = self.__basepath + "/log/checkcluster/" + "stresstest-" + _rackstr + "-" + self.mGetDateTime() + ".json"
                else:
                    self.__jsonhandler = self.__basepath + "/log/checkcluster/" + "healthcheck-" + _rackstr + "-" + self.mGetDateTime() + ".json"
                    # if there is a diagnostic directory use that instead of
                    # the log directory under exacloud/log/checkcluster for the restructured report
                    if "diag_root" in self.mGetHcConfig():
                        _healthcheckdir = self.mGetHcConfig()["diag_root"] + "/diagnostic/results/healthcheck/"
                        try:
                            os.stat(_healthcheckdir)
                        except:
                            os.makedirs(_healthcheckdir)
                        self.__jsonreshandler = _healthcheckdir + "hc_" + _rackstr + "_" + self.mGetDateTime() + "_healthcheck.json"
                        # create healthcheck dir, if running healthcheck first time
                        try:
                            os.stat(_healthcheckdir)
                        except:
                            os.mkdir(_healthcheckdir)
                    else:
                        _healthcheckdir = self.__basepath + "/log/checkcluster/"
                        self.__jsonreshandler = _healthcheckdir + "hc_" + _rackstr + "_" + self.mGetDateTime() + "_healthcheck.json"
                        ebLogWarn('*** Healthcheck reports will be copied under exacloud, and wont be pushed to ES server')

        def mDoHealthCheck(self, aOptions):

            _LogHandler = self.mGetLogHandler()
            _defaultLogHandler = self.mGetDefaultLogHandler()
            _jsonHandler = self.mGetJsonHandler()

            # Setup the JSON object for returning results
            _jsonResult = self.mGetJsonResult()
            _jsonObject = []
            _jsonMap = self.mGetJsonMap()

            _doxml = False
            _doconf = False
            _docluster = False
            _doall = False
            _doexachk = False
            _dostresstest = False

            _recommend = self.mGetRecommend()
            _eBox = self.mGetEbox()

            # Dump the JSON object
            def _mUpdateRequestData(aDataD):
                _data_d = aDataD
                _reqobj = _eBox.mGetRequestObj()
                if _reqobj is not None:
                    _reqobj.mSetData(json.dumps(_data_d))
                    _db = ebGetDefaultDB()
                    _db.mUpdateRequest(_reqobj)
                elif aOptions.jsonmode:
                    ebLogJson(json.dumps(_data_d, indent = 4))

            if aOptions.healthcheck:
                if aOptions.healthcheck == 'xml':
                    _doxml = True
                elif aOptions.healthcheck == 'conf':
                    _doconf = True
                elif aOptions.healthcheck == 'preprov':
                    self.mSetPostProv(False)
                    self.mSetPreProv(True)
                    _docluster = True # We will only skip some tests
                elif aOptions.healthcheck == 'connection':
                    self.mSetConnectCheck(True)
                    _docluster = True
                elif aOptions.healthcheck == 'exachk':
                    _doexachk = True
                elif aOptions.healthcheck == 'stresstest':
                    _dostresstest = True
                    self.mSetStressTest(True)
                else:
                    _docluster = True
            else:
                _doall = True

            _hcconf = self.mGetHcConfig()
            #run long run checks which may take longer duration to execute
            if ("longrun_check" in _hcconf and _hcconf["longrun_check"] == "True"):
                self.mSetLongRunCheck(True)
            #
            # Set Ping Status of Nodes
            #
            self.mSetPingStatus()

            try:

                #
                # Validate the XML file
                #
                if (_doall == True) or (_doxml == True) or (self.mGetPreProv() == True):
                    self.mValidateXML()
                else:
                    ebLogInfo('Skipping XML Validation')

                #
                # Validate the exabox.conf file
                #
                if (_doall == True) or (_doconf == True) or (self.mGetPreProv() == True):
                    self.mValidateConf()
                else:
                    ebLogInfo('Skipping exabox.conf validation')

                # Run Connectivity Check
                if ("connectivity_check" in _hcconf and _hcconf["connectivity_check"] == "True"):
                    _objConnCheck = ebCluConnectivityCheck(self, aOptions)
                    _objConnCheck.mRunConnectivityCheck()
 
                #
                # Validate the cluster
                #
                if (_doall == True) or (_docluster == True):
                    _jsonResMap = self.mGetJsonResMap()
                    _jsonResHandler = self.mGetJsonResHandler()
                    # initialize jsonResMap
                    self.mRestructJSON(aOptions, _jsonResMap)
                    self.mValidateCluster()
                    # dump jsonResMap to JSON
                    self.mDumpJSON(_jsonResMap, _jsonResHandler)
                else:
                    ebLogInfo('Skipping cluster validation')
                    ebLogInfo('\n')

                #
                # Run healthcheck using exachk
                #
                if (_doexachk == True):
                    _hcobj = ebCluExachk(self, aOptions)
                    _hcobj.mRunExachk(aOptions)

                #
                # Stress testing of Exadata nodes
                #
                if _dostresstest:
                    self.mRunStressTest()

            except Exception as e:
                ebLogError('*** Exception occured while running healthcheck with error %s, on line %s' % (str(e), str(sys.exc_info()[-1].tb_lineno)))
                ebLogHealth('NFO', '*** Exception occured while running healthcheck with error %s, on line %s' % (str(e), str(sys.exc_info()[-1].tb_lineno)))
                ebLogError(traceback.format_exc())
                if "Error while multiprocessing(Process timeout)" in str(e):
                    raise ExacloudRuntimeError(0x0756, 0xA, str(e))

            _log_destination = ebLogSetHCLogDestination(_LogHandler, True)

            ebLogHealth('NFO', '*** Errors, Recommendations and Warnings ***')
            ebLogInfo('*** Errors, Recommendations and Warnings ***')

            # Results - TXT format
            for _line in sorted(_recommend):
                ebLogHealth('NFO', '*** %s ***' %(_line))
                ebLogInfo('*** %s ***' %(_line))

            ebLogInfo('\n')
            ebLogInfo('The healthcheck activity is completed')
            ebLogInfo('Detailed status is available at <exacloud>/log/checkcluster/%s' %(_LogHandler))

            ebLogRemoveHCLogDestination(_log_destination)
            ebLogSetHCLogDestination(_defaultLogHandler)

            _mUpdateRequestData(_jsonMap)
            return 0

        def mRestructJSON(self, aOptions, aJsonResMap):
            """
            initialize restructured JSON
            TEMPLATE:
            {
            "hcExecTimestamp":"2017-05-15 06:14:00 PDT",
            "hcID":"0101010001",               # 10-length code
            "hcType":"CLUSTER",                # (XML,CLUSTER,CONNECTION,PREPROV,POSTPROV)
            "hcName":"Ping test for Dom0",     # manually defined on conf
            "hcNodeType":"dom0",               # (dom0, domu, cell, switch)
            "hcTestResult":"FAIL",             # (PASS, INFO, WARN, FAIL)
            "hcStatus":"3",                    # (0: PASS, 1: INFO, 2: WARN, 3: FAIL)
            "hcLogs":"ERROR:Host not pingable" # put all logs as string added in current healthcheck
            "hcMsgDetail":"{logs:...}",        # put all json as string added in current healthcheck
            "hcNodeName":"slcs08adm06"         # hostname
            }
            hcID:
            01:Healthcheck + [01:xml | 02:connection | 03:preprov | 04:cluster | 05 postprov]
                           + [01:dom0 | 02:domu | 03:cell | 04:switch | 05:NW | 06:etc] + 0001:chk#
            02:Exachk      + [01:Tier1 | 02:Tier2 | 03:Specific]
            04:patchReq    + [01:Basic | 02:Advanced]
            """
            _jsonResMap = aJsonResMap
            _cluster_host_d = self.mGetClusterHostD()

            # initialize jsonResMap
            for _host in _cluster_host_d.keys():
                _jsonResMap[_host] = {}
                _jsonResMap[_host]['hcExecTimestamp'] = ""
                _jsonResMap[_host]['hcType'] = ""
                _jsonResMap[_host]['hcNodeType'] = ""
                _jsonResMap[_host]['hcNodeName'] = ""
                _jsonResMap[_host]['hcChecks'] = []
                _jsonResMap[_host]['hcID'] = ""
                _jsonResMap[_host]['hcName'] = ""
                _jsonResMap[_host]['hcTestResult'] = ""
                _jsonResMap[_host]['hcStatus'] = ""
                _jsonResMap[_host]['hcLogs'] = ""
                _jsonResMap[_host]['hcMsgDetail'] = ""

            for _host in _cluster_host_d.keys():
                _clunode = _cluster_host_d[_host]
                # set hcExecTimestamp
                _datetime = datetime.strptime(self.mGetDateTime(), '%m%d%y_%H%M%S')
                _jsonResMap[_host]['hcExecTimestamp'] = _datetime.strftime('%Y-%m-%d %H:%M:%S')+' '+time.strftime('%Z')
                # set hcType
                if aOptions.healthcheck:
                    _jsonResMap[_host]['hcType'] = aOptions.healthcheck.upper()
                else:
                    _jsonResMap[_host]['hcType'] = "ALL"
                # set hcNodeType
                _jsonResMap[_host]['hcNodeType'] = _clunode.mGetNodeType()
                # set hcNodeName
                _jsonResMap[_host]['hcNodeName'] = _host.split('.')[0]

        def mDumpJSON(self, aJsonResMap, aJsonResHandler):
            """
            dump restructured JSON
            dump hcChecks(_hcid, _hcname, _hctestresult, _hcstatus, _hclogs) by host
            """
            _jsonResMap = aJsonResMap
            _jsonResHandler = aJsonResHandler
            _cluster_host_d = self.mGetClusterHostD()

            with open(_jsonResHandler, 'a+') as outfile:
                for _host in _cluster_host_d.keys():
                    _hcCheckList = _jsonResMap[_host]['hcChecks']
                    _jsonResMap[_host].pop('hcChecks')
                    for _hcid, _hcname, _hctestresult, _hcstatus, _hclogs in _hcCheckList:
                        _jsonResMap[_host]['hcID'] = _hcid
                        _jsonResMap[_host]['hcName'] = _hcname
                        _jsonResMap[_host]['hcTestResult'] = _hctestresult
                        _jsonResMap[_host]['hcStatus'] = _hcstatus
                        _jsonResMap[_host]['hcLogs'] = _hclogs
                        json.dump(_jsonResMap[_host],outfile,sort_keys=True,skipkeys=True,indent=4,ensure_ascii=False)
                        outfile.write("\n")
            outfile.close()

        def mUpdateJSON(self, alist, value, hcid = None, hclogs = None):
            """
            update restructured JSON
            alist: [_type, _checktype, _host, _logtype] (e.g. ['Cluster', 'hostcheck', _host, 'logs'])
            value: testResult(Pass or Fail) or MsgDetail(json as string)
            hcid/hclogs: set to None if _logtype == 'MsgDetail'
            """
            _jsonResMap = self.mGetJsonResMap()
            healthcheck_cfg = self.mGetHcNameConfig()
            _type, _checktype, _host, _logtype = alist

            if _logtype == 'logs':
                # set hcID and hcName
                _hcid = hcid
                _hcname = healthcheck_cfg[_hcid]
                # set hcTestResult and hcStatus
                _hctestresult = value.upper()
                _hcstatus = self.mGetTestResultList().index(value)
                # set hcLogs
                _hclogs = hclogs
                # set hcChecks
                _jsonResMap[_host]['hcChecks'].append((_hcid, _hcname, _hctestresult, _hcstatus, _hclogs))
            elif _logtype == 'MsgDetail':
                # set hcMsgDetail
                _jsonResMap[_host]['hcMsgDetail'] = json.dumps(value[_type][_checktype][_host])

        # Log some basic info about the control plane
        def mLogCPData(self, aOptions):

            _recommend = self.mGetRecommend()
            _totalErr = 0
            _totalWarn = 0
            _totalReco = 0

            _ebCore = exaBoxCoreInit(aOptions)

            _jsonMap = self.mGetJsonMap()
            _jsonMap['ControlPlane'] = {}

            _exaVersion = "%s (%s)" %(_ebCore.mGetVersion())
            _jsonMap['ControlPlane']['exacloudVersion'] = _exaVersion

            _oedaVersion = get_gcontext().mGetOEDAVersion()
            _jsonMap['ControlPlane']['oedaVersion'] = _oedaVersion.rstrip()

            _datetime = self.mGetDateTime()
            _jsonMap['ControlPlane']['dateTime'] = _datetime

            for _line in sorted(_recommend):
                if "ERROR" in _line:
                    _totalErr += 1
                elif "WARNING" in _line:
                    _totalWarn += 1
                elif "RECOMMENDATION" in _line:
                    _totalReco += 1

            _jsonMap['ControlPlane']['totalErrors'] = _totalErr
            _jsonMap['ControlPlane']['totalWarnings'] = _totalWarn
            _jsonMap['ControlPlane']['totalRecommendations'] = _totalReco

            if _totalErr > 0:
                _overallStatus = "Fail"
            else:
                _overallStatus = "Pass"

            _jsonMap['ControlPlane']['overallStatus'] = _overallStatus

        # End

        def mReadHcConfig(self):

            _cf = None
            try:
                _cf = json.load(open(self.__confpath))
            except:
                ebLogError('*** Could not access/read healthcheck.conf file')
                return {}
            return _cf

        def mReadHcNameConfig(self):
            _cf = None
            try:
                _cf = json.load(open(self.__hcnameconfpath))
            except:
                ebLogInfo('*** Could not access/read hcname.conf file')
                return {}
            return _cf

        def mGetRecommend(self):
            return self.__recommend

        def mGetDateTime(self):
            return self.__datetime

        def mGetJsonResult(self):
            return self.__jsonresult

        def mGetJsonMap(self):
            return self.__jsonmap

        def mGetJsonResMap(self):
            return self.__jsonresmap

        def mGetExaConfig(self):
            return self.__config

        def mGetHcConfig(self):
            return self.__hcconfig

        def mGetHcNameConfig(self):
            return self.__hcnameconfig

        def mGetLogHandler(self):
            return self.__loghandler

        def mGetDefaultLogHandler(self):
            return self.__defloghandler

        def mGetJsonHandler(self):
            return self.__jsonhandler

        def mGetJsonResHandler(self):
            return self.__jsonreshandler

        def mGetTestResultList(self):
            return self.__testresultList

        def mGetEbox(self):
            return self.__ebox

        def mSetEboxNetworks(self, aEboxNetworks):
            self.__eboxnetworks = aEboxNetworks

        def mGetEboxNetworks(self):
            return self.__eboxnetworks

        def mGetBoxClusterPath(self):
            return self.__clusterpath

        def mGetXMLPath(self):
            return self.__xmlpath

        def mGetClusterHostD(self):
            return self.__cluster_host_d

        def mGetClusterHealthD(self):
            return self.__cluster_health_d

        def mSetVmmem(self, aVmmem):
            self.__vmmem = aVmmem

        def mGetVmmem(self):
            return self.__vmmem

        def mGetDom0s(self):
            return self.__dom0s

        def mSetDom0s(self, aDom0s):
            self.__dom0s = aDom0s

        def mGetPreProv(self):
            return self.__preprov

        def mSetPreProv(self, aPreProv):
            self.__preprov = aPreProv

        def mSetPostProv(self, aPostProv):
            self.__postprov = aPostProv

        def mGetConnectCheck(self):
            return self.__connectcheck

        def mSetConnectCheck(self, aConnectCheck):
            self.__connectcheck = aConnectCheck

        def mGetLongRunCheck(self):
            return self.__longruncheck

        def mSetLongRunCheck(self, aLongRunCheck):
            self.__longruncheck = aLongRunCheck

        def mSetStressTest(self, aValue):
            self.__stresstest = aValue

        def mSetPingStatus(self):

            _ebox = self.mGetEbox()
            _verbose = _ebox.mGetVerbose()
            #utility function to set ping status for each node
            def _mSetPingstatusUtil(aHost, aList):
                _host = aHost
                _list = aList
                _clunode = _clu_ping_host[_host]
                if not self.mGetEbox().mPingHost(_host):
                    _list.append([_host, False])
                else:
                    _list.append([_host, True])

            _clu_ping_host = self.mGetClusterHostD()
            _plist = ProcessManager()
            _list = _plist.mGetManager().list()
            for _host in _clu_ping_host.keys():
                _p = ProcessStructure(_mSetPingstatusUtil, [_host, _list], _host)
                _p.mSetMaxExecutionTime(30*60) # 30 minutes
                _p.mSetJoinTimeout(60)
                _p.mSetLogTimeoutFx(ebLogWarn)
                _plist.mStartAppend(_p)
            _plist.mJoinProcess()

            for _entry in _list:
                _clunode = _clu_ping_host[_entry[0]]
                _clunode.mSetPingable(_entry[1])

        #
        # Run Stress Testing
        #
        def mRunStressTest(self):

            ebLogInfo('*********** Running stress testing using -stresstest option ***********')
            _jsonMap = self.mGetJsonMap()
            self.__stressTestNodes(_jsonMap)

        #
        # Stress Test Exadata nodes for the number of iterations mentioned in
        # 'stress_count' in healthcheck-conf
        #
        def __stressTestNodes(self, aJsonMap):

            _recommend = self.mGetRecommend()
            _jsonMap = aJsonMap
            _jsonMap['Cluster'] = {}
            _jsonMap['Cluster']['hostCheck'] = {}

            _cluster_host_d = self.mGetClusterHostD()
            count = 3
            _hcconf = self.mGetHcConfig()

            if ("stresstest_count" in _hcconf):
                count = _hcconf["stresstest_count"]
            ebLogInfo('Number of iterations to stress test the nodes is set to %d' % count)

            # Iterate through 'count' number of iterations and pick a random
            # node in Exadata system to run a random non-destructive command
            # like 'ls' or 'find' as part of the stress test.
            for x in range(count):

                _host = secrets.choice(list(_cluster_host_d.keys()))

                _clunode = _cluster_host_d[_host]

                if _host not in _jsonMap['Cluster']['hostCheck']:
                    _jsonMap['Cluster']['hostCheck'][_host] = {}
                    _jsonMap['Cluster']['hostCheck'][_host]['Log'] = []

                if _clunode.mGetPingable():

                    _node = exaBoxNode(get_gcontext())

                    sec = secrets.randbelow(91) + 10
                    ebLogInfo('Sleeping for %d seconds'% sec)
                    time.sleep(sec)
                    _currtime = time.ctime()

                    try:
                        _node.mConnect(aHost=_host)
                        _trace = "Iteration %d: Connected to the host %s successfully at time %s" % (x, _host, _currtime)
                        ebLogInfo(_trace)
                        _jsonMap['Cluster']['hostCheck'][_host]['Log'].append(_trace)
                    except:
                        _trace = "ERROR: Iteration %d: Connection to the host %s failed at time %s" % (x, _host, _currtime)
                        _recommend.append(_trace)
                        ebLogError(_trace)
                        _jsonMap['Cluster']['hostCheck'][_host]['Log'].append(_trace)
                        _clunode.mSetSSHConnection(False)
                        continue
                    _clunode.mSetSSHConnection(True)

                    _cmdList = ["find . -name abcd", "ls /", "ls ~", "find . -name xyz"]

                    _cmd = secrets.choice(_cmdList)

                    _i, _o, _e = _node.mExecuteCmd(_cmd, aTimeout=180)
                    if _o:
                         ebLogInfo('Executed the command \'%s\' on the host %s' % (_cmd, _host))

                    _node.mDisconnect()


        # end stress testing Exadata nodes



        def mEstablishSSH(self, aHost, acluNode, aNode):
            _host = aHost
            _clunode = acluNode
            _node = aNode
            try:
                _ssh_timeout = "10"
                _hcconf = self.mGetHcConfig()
                if (self.mGetConnectCheck() == True) and ("lthc_ssh_timeout" in _hcconf):
                    _ssh_timeout = _hcconf["lthc_ssh_timeout"]
                _node.mConnectTimed(aHost=_host, aTimeout=_ssh_timeout)
            except:
                ebLogHealth('WRN','*** CheckInfo failed to connect to: %s (pingable though)' % (_host))
                _clunode.mSetSSHConnection(False)
                return
            _clunode.mSetSSHConnection(True)

        #end mEstablishSSH

        #
        # Validate the cluster
        #
        def mValidateCluster(self):

            _ebox = self.mGetEbox()
            _verbose = _ebox.mGetVerbose()
            _eboxnetworks = self.mGetEboxNetworks()

            _recommend = self.mGetRecommend()
            _jsonMap = self.mGetJsonMap()
            _jsonMap['Cluster'] = {}
            _jsonMap['Cluster']['hostCheck'] = {}

            _switchcas = None
            _pkeylist = None
            _cellflashlist = []

            ebLogInfo('*** Validating Cluster Configuration ***\n')
            ebLogSetHCLogDestination(self.mGetDefaultLogHandler(), True)

            _cluster_host_d = self.mGetClusterHostD()
            _cluster_health_d = self.mGetClusterHealthD()

            _hostjsonmap_folder = os.path.join(self.__basepath, f"log/checkcluster/{uuid.uuid1()}")
            os.makedirs(_hostjsonmap_folder)
            ebLogTrace(f"Created {_hostjsonmap_folder} folder for storing host based healthcheck records.")

            #
            # Utility function to run healthcheck
            # Will be called from separate thread to optimize healthcheck time
            #
            def _mValidateClusterUtil(aHost):
                _host = aHost
                _clunode = _cluster_host_d[_host]
                _cluhealth = _cluster_health_d[_host]

                if (_clunode.mGetNodeType() == 'domu') and (self.mGetPreProv() == True):
                   return

                ebLogInfo('*** *** Validating configuration for %s' %(_host))
                ebLogHealth('NFO', '*** Checking configuration for %s' %(_host))

                _jsonMap['Cluster']['hostCheck'][_host] = {}
                _jsonMap['Cluster']['hostCheck'][_host]['logs'] = {}
                _jsonMap['Cluster']['hostCheck'][_host]['logs']['generic'] = []
                _jsonMap['Cluster']['hostCheck'][_host]['logs']['network'] = {}
                _jsonMap['Cluster']['hostCheck'][_host]['logs']['switch'] = {}
                _jsonMap['Cluster']['hostCheck'][_host]['smnodes'] = []
                _jsonMap['Cluster']['hostCheck'][_host]['ibswitches'] = []

                # Set to pass always (for now)
                _jsonMap['Cluster']['hostCheck'][_host]['TestResult'] = "Pass"

                #
                # Check if SSH and PWD status
                #
                if _clunode.mGetPingable():
                    _node = exaBoxNode(get_gcontext())
                    self.mEstablishSSH(_host, _clunode, _node)
                   
                    # Skip running cmds on vm if ssh connection failed
                    if (_clunode.mGetSSHConnection() == False):
                        return
                    #
                    # Check password login and w/o password login
                    #
                    _cmd_str  = 'grep "^PermitRootLogin without-password" /etc/ssh/sshd_config'
                    _cmd2_str = 'grep "^PasswordAuthentication no" /etc/ssh/sshd_config'

                    _node.mExecuteCmdLog(_cmd_str, aTimeout=180)
                    if not _node.mGetCmdExitStatus():
                        _clunode.mSetRootSSHDMode(True)     # Close
                    else:
                        _clunode.mSetRootSSHDMode(False)    # Open

                    _node.mExecuteCmdLog(_cmd2_str, aTimeout=180)
                    if not _node.mGetCmdExitStatus():
                        _clunode.mSetPwdAuthentication(False)       # Close
                    else:
                        _clunode.mSetPwdAuthentication(True)        # Open

                    #
                    # Check strong or weak password (e.g. default password)
                    #
                    _cmd3_str = 'grep "^root:" /etc/shadow'
                    _i, _o, _e = _node.mExecuteCmd(_cmd3_str, aTimeout=180)
                    _out = _o.readlines()
                    if _out:
                        _pwd = _out[0].split(':')[1]
                        if not _pwd[:2] in [ '$6', '$1' ]:
                            ebLogHealth('WRN','CheckInfo: %s - Unknown hash or invalid passwd entry' % _host)
                            ebLogHealth('WRN','CheckInfo: hash/pwd entry == %s' % (_pwd))
                            return
                        _, _hash_t, _hash_d, _hash_v = _pwd.split('$')

                        _salt = '$'+_hash_t+'$'+_hash_d+'$'

                        _coptions_for_pwd = get_gcontext().mGetConfigOptions()
                        _default_pwd = _coptions_for_pwd["default_pwd"]
                       
                        if crypt.crypt(_default_pwd,_salt) == _salt+_hash_v:
                            _clunode.mSetWeakPassword(True)
                        else:
                            _clunode.mSetWeakPassword(False)
                    if not _clunode.mGetNodeType() == 'switch':
                        _img_version = _ebox.mGetImageVersion(_host)
                        if _img_version:
                            _jsonMap['Cluster']['hostCheck'][_host]['Image Version'] = _img_version

                    # Skip the rest if we are doing just connectivity checks
                    if (self.mGetConnectCheck() == True):
                        return

                    # check for shared / multivm environments
                    self.__ebox.mCheckSharedEnvironment()
                    #
                    # Node specific checks/info
                    #
                    if _clunode.mGetNodeType() == 'switch':
                        self.mValidateSwitches(_host, _node, _clunode, _cluhealth, _recommend, _jsonMap)

                    #
                    # Dom0 - Only eth0 should be up
                    #
                    if _clunode.mGetNodeType() == 'dom0':
                        self.mValidateDom0s(_host, _node, _clunode, _cluhealth, _recommend, _jsonMap)

                    # domU related checks
                    if _clunode.mGetNodeType() == 'domu':
                        self.mValidateDomUs(_host, _node, _clunode, _cluhealth, _recommend, _jsonMap)

                    # cell related checks
                    if _clunode.mGetNodeType() == 'cell':
                        self.mValidateCells(_host, _node, _clunode, _cluhealth, _recommend, _jsonMap, _cellflashlist)

                    #
                    # Reset HOST key
                    #
                    _cmd = f"ssh-keygen -R {_host}"
                    _ebox.mExecuteLocal(_cmd, aStdOut=DEVNULL, aStdErr=DEVNULL)
                    _node.mDisconnect()

                _jsonMap['Cluster']['hostCheck'][_host]['clunodeinstance'] = base64.b64encode(pickle.dumps(_clunode)).decode('utf8')
                _jsonMap['Cluster']['hostCheck'][_host]['cluhealthinstance'] = base64.b64encode(pickle.dumps(_cluhealth)).decode('utf8')

                _jsondumpfile = os.path.join(_hostjsonmap_folder, f"{_host}_healthcheck.json")
                with open(_jsondumpfile, 'w') as _fd:
                    json.dump(_jsonMap, _fd, indent=4)
                ebLogTrace(f"Saved {_host} healthcheck data to {_jsondumpfile}")
                ebLogHealth('NFO','*** %s : %s\n ' % (_host, _clunode.mToString()))

                #end  _mValidateClusterUtil

            _exa_config = self.mGetExaConfig()
            _cluvalidate_timeout = 900
            if 'healthcheck_task_timeout' in _exa_config.keys():
                _cluvalidate_timeout = int(_exa_config['healthcheck_task_timeout'])

            _process_manager = ProcessManager()
            for _host in _cluster_host_d.keys():
                _proc_struct = ProcessStructure(_mValidateClusterUtil, [_host,])
                _proc_struct.mSetMaxExecutionTime(_cluvalidate_timeout) #30 minutes timeout
                _proc_struct.mSetJoinTimeout(5)
                _proc_struct.mSetLogTimeoutFx(ebLogWarn)
                _proc_struct.mSetName(f"cluster_validation_{_host}")
                _process_manager.mStartAppend(_proc_struct)
                if _verbose:
                    ebLogVerbose(f'*** {_proc_struct.mGetName()} : mValidateClusterUtil started for {_host} ')
                ebLogTrace(f'*** {_proc_struct.mGetName()} : mValidateClusterUtil started for {_host} ')

            _process_manager.mJoinProcess()
            ebLogTrace('*** all processes completed execution of mValidateClusterUtil ')

            for _host in _cluster_host_d.keys():
                _jsondumpfile = os.path.join(_hostjsonmap_folder, f"{_host}_healthcheck.json")
                if os.path.exists(_jsondumpfile):
                    _json_data = {}
                    with open(_jsondumpfile, 'r') as _json_fd:
                        _json_data = json.load(_json_fd)
                    if _json_data is None or _json_data.get('Cluster') is None \
                    or _json_data.get('Cluster').get('hostCheck') is None \
                    or _json_data.get('Cluster').get('hostCheck').get(_host) is None:
                        ebLogWarn(f"Node healthcheck data for {_host} is empty.")
                        continue
                    
                    _jsonMap['Cluster']['hostCheck'][_host] = copy.deepcopy(_json_data['Cluster']['hostCheck'][_host])

                    if _jsonMap.get('Cluster').get('hostCheck').get(_host).get('clunodeinstance') is not None:
                        _cluster_host_d[_host] = pickle.loads(base64.b64decode(_jsonMap['Cluster']['hostCheck'][_host]['clunodeinstance']))
                    else:
                        ebLogWarn(f"clunodeinstance healthcheck data for {_host} is empty.")
                        
                    if _jsonMap.get('Cluster').get('hostCheck').get(_host).get('cluhealthinstance') is not None:
                        _cluster_health_d[_host] = pickle.loads(base64.b64decode(_jsonMap['Cluster']['hostCheck'][_host]['cluhealthinstance']))
                    else:
                        ebLogWarn(f"cluhealthinstance healthcheck data for {_host} is empty.")

                else:
                    ebLogWarn(f"Missing cluster hostcheck data for {_host}")

            if os.path.exists(_hostjsonmap_folder):
                shutil.rmtree(_hostjsonmap_folder)

            self.mVerifyPkeys(_switchcas, _pkeylist, _recommend, _jsonMap)
            
            if (self.mGetLongRunCheck() == True):
                self.mVerifyVmImageCheckSum(_recommend, _jsonMap)
                
            _log_destination = ebLogSetHCLogDestination(self.mGetLogHandler(), True)

            ebLogHealth('NFO', '\n')
            ebLogHealth('NFO','*** CLUSTER CONFIGURATION STATUS ***\n')
            ebLogHealth('NFO','*** Cluster path is %s ***\n' %(self.mGetBoxClusterPath()))

            self.mPublishHealthCheckReport(_cellflashlist, _recommend, _jsonMap)

            ebLogRemoveHCLogDestination(_log_destination)
            ebLogSetHCLogDestination(self.mGetDefaultLogHandler())
            # END

        def mValidateSwitches(self, aHost, aNode, aClunode, aCluhealth, aRecommend, aJsonMap):

            _host = aHost
            _node = aNode
            _clunode = aClunode
            _cluhealth = aCluhealth
            _recommend = aRecommend
            _jsonMap = aJsonMap
            _cmd4_str = 'smpartition list active no-page | head -10'
            _i, _o, _e = _node.mExecuteCmd(_cmd4_str, aTimeout=180)
            _out = _o.readlines()
            if _out:
                for _line in _out:
                    if _line.find('Default=') != -1:
                        _default = _line[len('Default='):-2]
                        _clunode.mSetSwitchDefault(_default)
                    elif _line.find('ALL_CAS=') != -1:
                        _all_cas = _line[len('ALL_CAS='):-2]
                        _clunode.mSetSwitchAllCas(_all_cas)

            _switchcas = _clunode.mGetSwitchAllCas()

            # Switch - smnodes list should match ibswitches output
            ebLogInfo('*** *** Validating smnodes list on switch - %s' %(_host))
            self.mCheckSmnodesList(_host, _node, _clunode, _cluhealth, _recommend, _jsonMap)

            #check space on root partition
            self.mCheckRootSpace(_host, _node, _clunode, _cluhealth, _recommend, _jsonMap)

        def mValidateDom0s(self, aHost, aNode, aClunode, aCluhealth, aRecommend, aJsonMap):

            _host = aHost
            _node = aNode
            _clunode = aClunode
            _cluhealth = aCluhealth
            _recommend = aRecommend
            _jsonMap = aJsonMap

            _ethstring = ''
            _cmd5_str = 'ip a |grep eth | grep UP'
            _i, _o, _e = _node.mExecuteCmd(_cmd5_str, aTimeout=180)
            _out = _o.readlines()
            if _out:
                for _line in _out:
                    _intf = _line.split(":")[1]
                    if _ethstring == '':
                        _ethstring = _intf
                    else:
                        _ethstring = _ethstring+','+_intf
            _cluhealth.mSetEthifs(_ethstring)

            # Dom0 - List of all i/fs with IP addresses
            _inetstring = ''
            _cmd5_str = 'ip -f inet a |grep inet'
            _i, _o, _e = _node.mExecuteCmd(_cmd5_str, aTimeout=180)
            _out = _o.readlines()
            if _out:
                for _line in _out:
                    _inetstr = _line.lstrip().rstrip('\n').split(" ")
                    if _inetstring == '':
                        _inetstring = _inetstr[-1] + ":" + _inetstr[1].split('/')[0]
                    else:
                        _inetstring = _inetstring+','+_inetstr[-1] + ":" + _inetstr[1].split('/')[0]
            _cluhealth.mSetInetlist(_inetstring)

            # Dom0 - Total Available Memory
            _vm = getHVInstance(_host)
            _totalmem = _vm.getDom0TotalMem()
            _cluhealth.mSetDom0mem(str(_totalmem))

            # Dom0 - ovmutils version
            _cmd5_str = 'rpm -qa | grep ovmutils'
            _i, _o, _e = _node.mExecuteCmd(_cmd5_str, aTimeout=180)
            _out = _o.readlines()
            if _out:
                for _line in _out:
                    _ovmutilsver = _line.split("-")[2]
                _cluhealth.mSetOvmutilsVer(_ovmutilsver)
            else:
                _cluhealth.mSetOvmutilsVer("None")

            # Dom0 - perl version
            _cmd5_str = 'rpm -q perl'
            _i, _o, _e = _node.mExecuteCmd(_cmd5_str, aTimeout=180)
            _out = _o.readlines()
            if _out:
                _estring = "is not installed"
                for _line in _out:
                    if _estring in _line:
                        _cluhealth.mSetPerlVer("None")
                    else:
                        _perlver = _line.rstrip()[5:]
                        _cluhealth.mSetPerlVer(_perlver)
            else:
                _cluhealth.mSetPerlVer("None")

            # Dom0 - python version
            _cmd5_str = 'rpm -q python'
            _i, _o, _e = _node.mExecuteCmd(_cmd5_str, aTimeout=180)
            _out = _o.readlines()
            if _out:
                _estring = "is not installed"
                for _line in _out:
                    if _estring in _line:
                        _cluhealth.mSetPythonVer("None")
                    else:
                        _pythonver = _line.rstrip()[7:]
                        _cluhealth.mSetPythonVer(_pythonver)
            else:
                _cluhealth.mSetPythonVer("None")

            # Dom0 - number of VMs
            _vm_count = _vm.getTotalVMs()
            _cluhealth.mSetVmNum(str(_vm_count))

            #check space on root partition
            self.mCheckRootSpace(_host, _node, _clunode, _cluhealth, _recommend, _jsonMap)

            # Perform below check only if we are in pre-provisioning stage
            if (self.mGetPreProv() == True):

                # check for shared / multivm environments
                if (self.__ebox.SharedEnv() == True):

                    # Dom0 - check all potential stale  locks
                    ebLogInfo('*** *** Checking all potential stale locks on Dom0 - %s' %(_host))
                    self.mCheckStaleLocks(_host, _node, _clunode, _cluhealth, _recommend, _jsonMap)


            # Dom0 - check all ethernet I/Fs
            ebLogInfo('*** *** Validating ethernet interfaces on Dom0 - %s' %(_host))
            self.mCheckNetIfs(_host, _node, _clunode, _cluhealth, _recommend, _jsonMap)
            _pkeylist = _cluhealth.mGetIbPkeylist() # To be used below

            # Dom0 - network consistency check
            ebLogInfo('*** *** Performing network consistency check on Dom0 - %s' %(_host))
            self.mCheckNetConsistency(_host, _node, _clunode, _cluhealth, _recommend, _jsonMap)

            # Perform below tests only if we are in pre-provisioning stage
            if (self.mGetPreProv() == True):

                # Pre-provisioning network checks
                self.mPreProvNetworkChecks(_host, _node, _clunode, _cluhealth, _recommend, _jsonMap)

                # Pre-provisioning system checks
                self.mPreProvSystemChecks(_host, _node, _clunode, _cluhealth, _recommend, _jsonMap)

        # end dom0 Checks

        def mValidateDomUs(self, aHost, aNode, aClunode, aCluhealth, aRecommend, aJsonMap):

            _host = aHost
            _node = aNode
            _clunode = aClunode
            _cluhealth = aCluhealth
            _recommend = aRecommend
            _jsonMap = aJsonMap
            _domuiso = "False"
            _dom0list = self.mGetDom0s()
            _loglist = []
            # Ping to dom0s should fail
            for _d0 in _dom0list:
                _cmd5_str = 'ping -w 2 ' + _d0
                _i, _o, _e = _node.mExecuteCmd(_cmd5_str, aTimeout=180)
                _err = _e.readlines()
                if not _err:
                    _recommend.append("WARNING: Ping from domU %s to dom0 %s is working" %(_host, _d0))
                    _dictLen = len(_jsonMap['Cluster']['hostCheck'][_host]['logs']['network'])
                    _jsonMap['Cluster']['hostCheck'][_host]['logs']['network'][_dictLen] = _recommend[-1]
                    _loglist.append(_recommend[-1])
                else:
                    _domuiso = "True"
            self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Pass', '0104050009', _loglist)
            _cluhealth.mSetDomuIso(_domuiso)

        # end domU checks

        def mValidateCells(self, aHost, aNode, aClunode, aCluhealth, aRecommend, aJsonMap, aCellflashlist):

            _host = aHost
            _node = aNode
            _clunode = aClunode
            _cluhealth = aCluhealth
            _recommend = aRecommend
            _jsonMap = aJsonMap
            _cellflashlist = aCellflashlist
            _ebox = self.mGetEbox()

            _hcconf = self.mGetHcConfig()
            if "cell_verify" in _hcconf:
                if _hcconf["cell_verify"] == "True":
                    _celldiskattr = _cluhealth.mGetCellDiskAttr()
                    self.mCellHealthCheck(_host, _node, _clunode, _cluhealth, _recommend, _jsonMap, _celldiskattr)

            # Check for presence of flashcache
            ebLogInfo('*** *** Verifying if flashcache is present on %s' %(_host))
            self.mCheckFlashCache(_host, _node, _clunode, _cluhealth, _recommend, _jsonMap, _cellflashlist)

            if (self.mGetPreProv() == True):
                if (self.__ebox.SharedEnv() == False):
                    #check DB status in case of non-shared env
                    self.mCheckDBStatusOnCell(_host, _node, _clunode, _cluhealth, _recommend, _jsonMap)
                ebLogInfo('*** *** Pre-provisioning check: verifying if grid disk is present in %s' %(_host))
                # Check if grid disks are already created for the cluster.
                # mDeleteGD(aListOnly = True) will not delete the grid disks.
                # It will return 1 if there are no grid disks created
                # for the cluster, otherwise return 0.
                if not _ebox.mGetStorage().mDeleteGD(aListOnly=True, aCell=_host):
                    ebLogInfo("ERROR: Grid Disks in the cell %s are already created for the cluster." % _host)
                    _recommend.append("ERROR: Grid Disks in the cell %s are already created for the cluster." % _host)
                    _jsonMap['Cluster']['hostCheck'][_host]['logs']['generic'].append(_recommend[-1])
                    self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Fail', '0103030010', _recommend[-1])
                else:
                    self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Pass', '0103030010')

        # end cell checks

        def mPublishHealthCheckReport(self, aCellflashlist, aRecommend, aJsonMap):

            _cellflashlist = aCellflashlist
            _recommend = aRecommend
            _jsonMap = aJsonMap
            _ebox = self.mGetEbox()
            _cluster_host_d = self.mGetClusterHostD()
            _cluster_health_d = self.mGetClusterHealthD()

            for _host in _cluster_host_d.keys():
                _clunode = _cluster_host_d[_host]
                _cluhealth = _cluster_health_d[_host]

                if (_clunode.mGetNodeType() == 'domu') and (self.mGetPreProv() == True):
                    continue

                ebLogHealth('NFO','Cluster Host \t %s' %(_host))
                ebLogHealth('NFO','***                         Node Type: \t %s' %(_clunode.mGetNodeType()))
                ebLogHealth('NFO','***                       Ping Status: \t %s' %(_clunode.mGetPingable()))
                ebLogHealth('NFO','***                       SSH Working: \t %s' %(_clunode.mGetSSHConnection()))

                if _host not in _jsonMap['Cluster']['hostCheck'].keys():
                    ebLogWarn(f"Skipping cluster hostcheck report for host {_host} since it is unavailable.")
                    continue

                _jsonMap['Cluster']['hostCheck'][_host]['NodeType'] = _clunode.mGetNodeType()
                _jsonMap['Cluster']['hostCheck'][_host]['pingable'] = _clunode.mGetPingable()
                _jsonMap['Cluster']['hostCheck'][_host]['sshStatus'] = _clunode.mGetSSHConnection()
                _loglist, _loglist_ping, _loglist_ssh, _loglist_pwd, _loglist_weakpwd = [], [], [], [], []

                _msgType = "ERROR"
                if (_clunode.mGetNodeType() == 'domu'):
                    _msgType = "WARNING"

                if not _jsonMap['Cluster']['hostCheck'][_host]['pingable']:
                    _recommend.append("%s: Host %s is not pingable" %(_msgType, _host))
                    _loglist.append(_recommend[-1])
                    _loglist_ping.append(_recommend[-1])
                    if (_clunode.mGetNodeType() != 'domu'):
                        _jsonMap['Cluster']['hostCheck'][_host]['TestResult'] = "Fail"

                if not _jsonMap['Cluster']['hostCheck'][_host]['sshStatus']:
                    _recommend.append("%s: SSH not working for %s" %(_msgType, _host))
                    _loglist.append(_recommend[-1])
                    if (_clunode.mGetNodeType() != 'domu'):
                        _jsonMap['Cluster']['hostCheck'][_host]['TestResult'] = "Fail"

                ebLogHealth('NFO','*** Root SSH without password allowed: \t %s' %(_clunode.mGetRootSSHDMode()))
                ebLogHealth('NFO','***        Password based SSH allowed: \t %s' %(_clunode.mGetPwdAuthentication()))

                _jsonMap['Cluster']['hostCheck'][_host]['pwdlessSSH'] = _clunode.mGetRootSSHDMode()

                if not _jsonMap['Cluster']['hostCheck'][_host]['pwdlessSSH']:
                    _recommend.append("WARNING: Passwordless SSH not setup for %s" %(_host))
                    _loglist.append(_recommend[-1])
                    _loglist_pwd.append(_recommend[-1])

                if _clunode.mGetWeakPassword() == True:
                    ebLogHealth('NFO','***               Quality of Password: \t Weak \n')
                    _recommend.append("RECOMMENDATION: root password for %s is weak. Consider changing it to a stronger one" %(_host))
                    _loglist.append(_recommend[-1])
                    _loglist_weakpwd.append(_recommend [-1])
                elif _clunode.mGetWeakPassword() == None:
                    ebLogHealth('NFO','***               Quality of Password: \t None \n')
                else:
                    ebLogHealth('NFO','***               Quality of Password: \t Strong \n')
                _jsonMap['Cluster']['hostCheck'][_host]['weakPassword'] = _clunode.mGetWeakPassword()

                if (self.mGetConnectCheck() == True):
                    for i in range(len(_loglist)):
                        _jsonMap['Cluster']['hostCheck'][_host]['logs']['generic'].append(_loglist[i])
                    if len(_loglist_ping) > 0:
                        if (_clunode.mGetNodeType() != 'domu'):
                            self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Fail', '0102060001', _loglist_ping)
                        else:
                            self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Pass', '0102020002', _loglist_ping)
                    else:
                        if (_clunode.mGetNodeType() != 'domu'):
                            self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Pass', '0102060001')
                        else:
                            self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Pass', '0102020002')
                    if len(_loglist_ssh) > 0:
                        if (_clunode.mGetNodeType() != 'domu'):
                            self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Fail', '0102060003', _loglist_ssh)
                        else:
                            self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Pass', '0102020004', _loglist_ssh)
                    else:
                        if (_clunode.mGetNodeType() != 'domu'):
                            self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Pass', '0102060003')
                        else:
                            self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Pass', '0102020004')
                    if len(_loglist_pwd) > 0:
                        self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Pass', '0102060005', _loglist_pwd)
                    if len(_loglist_weakpwd) > 0:
                        self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Pass', '0102060006', _loglist_weakpwd)
                    continue

                if _clunode.mGetNodeType() == 'switch':
                    self.mPublishSwitchesReport(_host, _clunode, _jsonMap)

                if _clunode.mGetNodeType() == 'dom0':
                    self.mPublishDom0sReport(_host, _cluhealth, _recommend, _jsonMap)

                if _clunode.mGetNodeType() == 'domu':
                    ebLogHealth('NFO', '***          domU isolation from dom0: \t %s' %(_cluhealth.mGetDomuIso()))
                    _jsonMap['Cluster']['hostCheck'][_host]['domuIsolation'] = _cluhealth.mGetDomuIso()

                if _clunode.mGetNodeType() == 'cell':
                    self.mPublishCellsReport(_cluhealth)

                # end cell type

                for i in range(len(_loglist)):
                    _jsonMap['Cluster']['hostCheck'][_host]['logs']['generic'].append(_loglist[i])

                # set hcMsgDetail
                self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'MsgDetail'], _jsonMap)

            for _host in _cluster_host_d.keys():

                _clunode = _cluster_host_d[_host]
                if (_clunode.mGetNodeType() == 'domu') and (self.mGetPreProv() == True):
                    continue
                if _host not in _jsonMap['Cluster']['hostCheck'].keys():
                    ebLogWarn(f"Skipping cluster hostcheck report for host {_host} since it is unavailable.")
                    continue

                # Purge stale entries in JSON
                if len(_jsonMap['Cluster']['hostCheck'][_host]['logs']) == 0:
                    _jsonMap['Cluster']['hostCheck'][_host].pop('logs', None)
                else:
                    _logset = ['generic', 'network', 'switch']
                    for _entry in _logset:
                        if len(_jsonMap['Cluster']['hostCheck'][_host]['logs'][_entry]) == 0:
                            _jsonMap['Cluster']['hostCheck'][_host]['logs'].pop(_entry, None)

            # Flashcache is on all, or none of the, cells
            if (len(_ebox.mReturnCellNodes()) != len(_cellflashlist)) and (len(_cellflashlist) > 0):
               _jsonMap['Cluster']['hostCheck']['logs'] = []
               _recommend.append("ERROR: Flashcache is missing on some of the cells. Unbalanced Configuration")
               _jsonMap['Cluster']['hostCheck']['logs'].append(_recommend[-1])

            ebLogInfo('\n')
            ebLogInfo('*** Completed Cluster validation\n')


        def mPublishSwitchesReport(self, aHost, aClunode, aJsonMap):

            _host = aHost
            _clunode = aClunode
            _jsonMap = aJsonMap

            ebLogHealth('NFO','***                   Switch Defaults: \t %s' %(_clunode.mGetSwitchDefault()))
            ebLogHealth('NFO','***                ALL_CAS membership: \t %s' %(_clunode.mGetSwitchAllCas()))
            _jsonMap['Cluster']['hostCheck'][_host]['switchDefaults'] = _clunode.mGetSwitchDefault()
            _jsonMap['Cluster']['hostCheck'][_host]['allCasMembership'] = _clunode.mGetSwitchAllCas()

            _smnlist = ''
            for _smnd in _jsonMap['Cluster']['hostCheck'][_host]['smnodes']:
                _smnlist = _smnlist + "," + _smnd
            ebLogHealth('NFO','***                      SmNodes List: \t %s' %(_smnlist[1:]))

            _ibswlist = ''
            for _ibsw in _jsonMap['Cluster']['hostCheck'][_host]['ibswitches']:
                _ibswlist = _ibswlist + "," + _ibsw.split("\"")[1]
            ebLogHealth('NFO','***                   IbSwitches List: \t %s' %(_ibswlist[1:]))


        def mPublishDom0sReport(self, aHost, aCluhealth, aRecommend, aJsonMap):

            _host = aHost
            _cluhealth = aCluhealth
            _recommend = aRecommend
            _jsonMap = aJsonMap
            _loglist = []

            ebLogHealth('NFO', '***  Ethernet interfaces currently UP: \t %s' %(_cluhealth.mGetEthifs().lstrip()))
            _jsonMap['Cluster']['hostCheck'][_host]['ethIfsUp'] = _cluhealth.mGetEthifs().lstrip()

            ebLogHealth('NFO', '*** \t\t\t   Interface: \t IP Address')
            _printIPString = _cluhealth.mGetInetlist()
            _printIPList = _printIPString.split(',')
            for i in _printIPList:
                _j = i.split(':')
                if len(_j) <= 1:
                    ebLogHealth('NFO','***    \t\t\t   %s' %(_j))
                    continue    
                ebLogHealth('NFO','***    \t\t\t   %s   \t %s' %(_j[0], _j[1]))
            _jsonMap['Cluster']['hostCheck'][_host]['ethIpList'] = _cluhealth.mGetInetlist()

            _totaldom0mem = _cluhealth.mGetDom0mem()
            ebLogHealth('NFO', '***    Total Memory Available on Dom0: \t %s GB' %(_totaldom0mem))
            _jsonMap['Cluster']['hostCheck'][_host]['dom0Mem'] = _cluhealth.mGetDom0mem()
            _tvmmem = self.mGetVmmem()
            if _tvmmem == None:
                _tvmmem = "0gb"
            if (int(float(_totaldom0mem)) <= int(_tvmmem[:-2])) and (int(_cluhealth.mGetVmNum()) == 0):
                _recommend.append("WARNING: Total memory on %s is %sGB while VM memory requirement is %sGB" %(_host, _totaldom0mem, _tvmmem[:-2]))
                _loglist.append(_recommend[-1])
                self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Pass', '0104010007', _recommend[-1])
            else:
                self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Pass', '0104010007', _recommend[-1])

            ebLogHealth('NFO', '***                  ovmutils version: \t %s' %(_cluhealth.mGetOvmutilsVer()))
            ebLogHealth('NFO', '***                      perl version: \t %s' %(_cluhealth.mGetPerlVer()))
            ebLogHealth('NFO', '***                    python version: \t %s' %(_cluhealth.mGetPythonVer()))
            ebLogHealth('NFO', '***                     Number of VMs: \t %s' %(_cluhealth.mGetVmNum()))
            ebLogHealth('NFO', '***          Eth interfaces with link: \t %s' %(_cluhealth.mGetEthLink()))
            ebLogHealth('NFO', '***                 Infiniband Device: \t %s' %(_cluhealth.mGetIbDevice()))
            ebLogHealth('NFO', '***        Ports on Infiniband Device: \t %s' %(_cluhealth.mGetIbPorts()))
            ebLogHealth('NFO', '***             Infiniband port state: \t %s' %(_cluhealth.mGetIbState()))
            ebLogHealth('NFO', '***             Infiniband link state: \t %s' %(_cluhealth.mGetIbPstate()))
            ebLogHealth('NFO', '***              Infiniband pkey list: \t %s' %(_cluhealth.mGetIbPkeylist()))
            ebLogHealth('NFO', '***         Network Consistency check: \t %s' %(_cluhealth.mGetDom0NetCons()))
            if (self.mGetPreProv() == True):

                ebLogHealth('NFO', '***                  Dom0 Bridge List: \t %s' %(_cluhealth.mGetDom0BridgeList()))

                # Bonded ifs output
                _bondifs = _cluhealth.mGetDom0BondedIfs()
                for _bif in _bondifs:
                    _bifmaster = _bif.split("::")[0]
                    _bifslaveset = _bif.split("::")[1]
                    ebLogHealth('NFO', '***  Bonded i/f %s - slaves are: \t %s' %(_bifmaster, _bifslaveset))

                # ebtables verification result
                ebLogHealth('NFO', '***        Dom0 ebtables verification: \t %s' %(_cluhealth.mGetDom0Ebtables()))

            _jsonMap['Cluster']['hostCheck'][_host]['ovmUtils'] = _cluhealth.mGetOvmutilsVer()
            _jsonMap['Cluster']['hostCheck'][_host]['perlVersion'] = _cluhealth.mGetPerlVer()
            _jsonMap['Cluster']['hostCheck'][_host]['pythonVersion'] = _cluhealth.mGetPythonVer()
            _jsonMap['Cluster']['hostCheck'][_host]['noOfVms'] = _cluhealth.mGetVmNum()
            _jsonMap['Cluster']['hostCheck'][_host]['ethWithLink'] = _cluhealth.mGetEthLink()
            _jsonMap['Cluster']['hostCheck'][_host]['ibDevice'] = _cluhealth.mGetIbDevice()
            _jsonMap['Cluster']['hostCheck'][_host]['ibPorts'] = _cluhealth.mGetIbPorts()
            _jsonMap['Cluster']['hostCheck'][_host]['ibPortState'] = _cluhealth.mGetIbState()
            _jsonMap['Cluster']['hostCheck'][_host]['ibLinkState'] = _cluhealth.mGetIbPstate()
            _jsonMap['Cluster']['hostCheck'][_host]['ibPkeyList'] = _cluhealth.mGetIbPkeylist()


        def mPublishCellsReport(self, aCluhealth):

            _cluhealth = aCluhealth
            
            _cellattr = _cluhealth.mGetCellAttr()
            if _cellattr is not None:

                ebLogHealth('NFO', '***                  Summary for Cell:')

                _attribstring = _cellattr.split("::", 1)[1]
                _attriblist = _attribstring.split("::")
                for _attrib in _attriblist:
                    _splitattribs = _attrib.split(":")
                    if len(_splitattribs) <= 1:
                        ebLogHealth('NFO', '***                     %s' %(_splitattribs))
                        continue
                    ebLogHealth('NFO', '***                     %s -- %s' %(_splitattribs[0], _splitattribs[1]))

            _flashattr = _cluhealth.mGetFlashAttr()
            if _flashattr is not None:

                ebLogHealth('NFO', '***            Summary for Flashcache:')

                _attribstring = _flashattr.split("::", 1)[1]
                _attriblist = _attribstring.split("::")
                for _attrib in _attriblist:
                    _splitattribs = _attrib.split(":")
                    if len(_splitattribs) <= 1:
                        ebLogHealth('NFO', '***                     %s' %(_splitattribs))
                        continue
                    ebLogHealth('NFO', '***                     %s -- %s' %(_splitattribs[0], _splitattribs[1]))

            _celldiskattr = _cluhealth.mGetCellDiskAttr()

            # Contains multiple lines for every disk
            # If cell_verify is not invoked _celldisk will be empty
            for _celldisk in _celldiskattr:
                # Each _celldisk is a string containing key:value pairs
                _diskname = _celldisk.split("::", 1)[0]
                ebLogHealth('NFO', '***                Physical disk name: \t %s' %(_diskname))

                _attribstring = _celldisk.split("::", 1)[1]
                _attriblist = _attribstring.split("::")
                for _attrib in _attriblist:
                    _splitattribs = _attrib.split(":")
                    if len(_splitattribs) <= 1:
                        ebLogHealth('NFO', '***                     %s' %(_splitattribs))
                        continue
                    ebLogHealth('NFO', '***                     %s -- %s' %(_splitattribs[0], _splitattribs[1]))


        # Check if switch CAS state and dom0 pkey list sync with each other
        def mVerifyPkeys(self, aSwitchcas, aPkeylist, aRecommend, aJsonMap):

            _swcas = aSwitchcas
            _pklist = aPkeylist
            _recommend = aRecommend
            _jsonMap = aJsonMap

            # If ALL_CAS is full, there can only be default pkeys
            if _swcas == "full":
                if len(_pklist.split(",")) > 1:
                    _recommend.append("ERROR: Switch ALL_CAS is set to *full* but multiple pkeys exist")
                    _jsonMap['Cluster']['logs'] = _recommend[-1]

            if _swcas == "both":
                if len(_pklist.split(",")) <= 2:
                    _recommend.append("ERROR: Switch ALL_CAS is set to *both* but only default pkeys exist")
                    _jsonMap['Cluster']['logs'] = _recommend[-1]

        # end

        # Check if system image on dom0s has same checksum
        def mVerifyVmImageCheckSum(self, aRecommend, aJsonMap):
            _recommend = aRecommend
            _jsonMap = aJsonMap
            _imgHashBase = None
            _dom0Base = None
            _testResult = "Pass"
            for _dom0, _ in self.__ebox.mReturnDom0DomUPair():
                if 'SystemImageHash' in _jsonMap['Cluster']['hostCheck'][_dom0]:
                    if _imgHashBase is None:
                        _imgHashBase = _jsonMap['Cluster']['hostCheck'][_dom0]['SystemImageHash']
                        _dom0Base = _dom0
                        continue
                    elif(_imgHashBase != _jsonMap['Cluster']['hostCheck'][_dom0]['SystemImageHash']):
                        ebLogWarn('*** System Image on Dom0 %s differs from System Image on other Dom0 %s' % (_dom0, _dom0Base))
                        ebLogHealth('WRN','*** System Image on Dom0 %s differs from System Image on other Dom0 %s' % (_dom0, _dom0Base))
                        _recommend.append('WARNING: System Image on Dom0 %s differs from System Image on other Dom0 %s' % (_dom0, _dom0Base))
                        _jsonMap['Cluster']['hostCheck'][_dom0]['logs']['generic'].append(_recommend[-1])
                        self.mUpdateJSON(['Cluster', 'hostCheck', _dom0, 'logs'], 'Pass', '0103010039', _recommend[-1])
                        _testResult = "Fail"
        # end mVerifyVmImageCheckSum


        def mUpdateJSONMap(self, alist, value):

           _jsonMap = self.__jsonmap

           def mUpdateJSONMapLevel1(alist, value):
             _jsonMap[alist[1]] = value

           def mUpdateJSONMapLevel2(alist, value):
             _jsonMap[alist[1]][alist[2]] = value

           def mUpdateJSONMapLevel3(alist, value):
              _jsonMap[alist[1]][alist[2]][alist[3]] = value

           def mUpdateJSONMapLevel4(alist, value):
             _jsonMap[alist[0]][alist[1]][alist[2]][alist[3]] = value

           def mUpdateJSONMapLevel5(alist, value):
              _jsonMap[alist[0]][alist[1]][alist[2]][alist[3]][alist[4]] = value

           def mUpdateJSONMapLevel6(alist, value):
              _jsonMap[alist[0]][alist[1]][alist[2]][alist[3]][alist[4]][alist[5]] = value;

           listLen = len(alist)
           if listLen == 1 :
             mUpdateJSONMapLevel1(alist, value)
           elif listLen == 2 :
             mUpdateJSONMapLevel2(alist, value)
           elif listLen == 3 :
             mUpdateJSONMapLevel3(alist, value)
           elif listLen == 4 :
             mUpdateJSONMapLevel4(alist, value)
           elif listLen == 5 :
             mUpdateJSONMapLevel5(alist, value)
           elif listLen == 6 :
             mUpdateJSONMapLevel6(alist, value)

       # end mUpdateJSONMap

        def mUpdateJSONMapdictLen(self, alist, value):
            _jsonMap = self.__jsonmap

            _dictLen = len(_jsonMap[alist[0]][alist[1]][alist[2]][alist[3]][alist[4]])
            _jsonMap[alist[0]][alist[1]][alist[2]][alist[3]][alist[4]][_dictLen] = value
        # end mUpdateJSONMapdictLen

        def mAppendJSONMap(self, alist, value):
           _jsonMap = self.__jsonmap
           _jsonMap[alist[0]][alist[1]][alist[2]][alist[3]].append(value)

        # end  mAppendJSONMap

        #
        # Cell test:
        #   Validate the physical disks in the cell
        #
        def mCellHealthCheck(self, aHost, aNode, aClunode, aCluhealth, aRecommend, aJsonMap, aCelldiskattr):

            _clunode = aNode
            _host = aHost
            _node = aNode
            _recommend = aRecommend
            _cluhealth = aCluhealth
            _jsonMap = aJsonMap
            _celldiskattr = aCelldiskattr
            _testResult = "Pass"
            _loglist, _loglist_cell, _loglist_phy = [], [], []

            ebLogInfo('************* Running Cell Status checks ***************')
            self.mUpdateJSONMap(['Cluster','hostCheck',_host, 'cellDisk'], {})

            self.mUpdateJSONMap(['Cluster','hostCheck',_host, 'cellDisk', 'summary'], {})
            # Check high level status of cell
            _cmd_str = 'cellcli -e list cell detail'
            _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
            _out = _o.readlines()
            if _out:
                _cellstatus = None
                _cellattr = _host
                for _line in _out:
                    _key = _line.lstrip().split(" ")[0].rstrip()

                    if ":" in _line:
                        _value = _line.lstrip().split(":", 1)[1].lstrip().rstrip()
                    else:
                        _key = "***:"
                        _value = _line.lstrip().rstrip()

                    if _value == "":
                        _value = "None"

                    self.mUpdateJSONMap(['Cluster','hostCheck',_host, 'cellDisk', 'summary',_key], _value)

                    _cellattr = _cellattr + "::" + _key + _value

                    if (_key == "bbuStatus:") or (_key == "fanStatus:") or (_key == "powerStatus:") or (_key == "usbStatus:"):
                        _cellstatus = _value

                        if _value != "normal":
                            _recommend.append("ERROR: On Cell %s, %s is not normal" %(_host, _key))
                            _loglist.append(_recommend[-1])
                            _loglist_cell.append(_recommend[-1])


                _cluhealth.mSetCellAttr(_cellattr)

                # Store a 'TestResult'
                if _cellstatus == "normal":
                    self.mUpdateJSONMap(['Cluster','hostCheck',_host,'cellDisk','summary','TestResult'],"Pass")
                else:
                    self.mUpdateJSONMap(['Cluster','hostCheck',_host,'cellDisk','summary','TestResult'], "Fail")
                if len(_loglist_cell) > 0:
                    self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Fail', '0104030013', _loglist_cell)
                else:
                    self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Pass', '0104030013')
            else:
                ebLogInfo("Error trying to read attributes of cell %s" %(_host))

            # Check alert history of cell
            _cellcli_alerthistory_options = mGetAlertHistoryOptions(self.__ebox, _host)
            if "cell_alerthistory_full" in self.mGetHcConfig() and self.mGetHcConfig()["cell_alerthistory_full"] == "False":
                _cmd_str = f'cellcli {_cellcli_alerthistory_options} -e  LIST ALERTHISTORY where endTime=null AND alertType=stateful'
            else:
                _cmd_str = f'cellcli {_cellcli_alerthistory_options} -e list alerthistory'
            _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
            _out = _o.readlines()
            if _out:
                _recommend.append("ALERT: %s  alert history" %(_host.split(".")[0]))
                _jsonMap['Cluster']['hostCheck'][_host]['cellDisk']['alertHistory'] = {}
                _cellstatus = None
                _cellattr = _host
                for _line in _out:
                    _key = _line.lstrip().split(" ")[0].rstrip()
                    _value = _line.lstrip().split(" ", 1)[1].rstrip()
                    _jsonMap['Cluster']['hostCheck'][_host]['cellDisk']['alertHistory'][_key] = _value

                    _recommend.append("ALERT: %s (%s) %s" %(_host.split(".")[0],_key, _value))

            # Check health of each individual disk in the cell
            _cmd_str = 'cellcli -e list physicaldisk'
            _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
            _out = _o.readlines()
            if _out:
                for _line in _out: # Individual physical disk
                    _phydisk = _line.lstrip().split(" ")[0].rstrip()
                    _phydiskattr = _phydisk
                    self.mUpdateJSONMap(['Cluster','hostCheck',_host,'cellDisk',_phydisk], {})
                    _cmd2_str = 'cellcli -e list physicaldisk ' + _phydisk + ' detail'
                    _i2, _o2, _e2 = _node.mExecuteCmd(_cmd2_str, aTimeout=180)
                    _out2 = _o2.readlines()
                    if _out2:
                        _pdstatus = None
                        for _line2 in _out2: # Key value pair of physical disk attribute
                            _key = _line2.lstrip().split(" ")[0].rstrip()
                            _value = _line2.lstrip().split(":", 1)[1].lstrip().rstrip()
                            self.mUpdateJSONMap(['Cluster','hostCheck',_host,'cellDisk',_phydisk, _key], _value)
                            _phydiskattr = _phydiskattr + "::" + _key + _value

                            if _key == "status:":
                                _pdstatus = _value

                                if _value != "normal":
                                    _recommend.append("ERROR: On Cell %s, the status of physical disk %s is not normal" %(_host, _phydisk))
                                    _loglist.append(_recommend[-1])
                                    _loglist_phy.append(_recommend[-1])

                        # Add to the list so we can store it in log file
                        _celldiskattr.append(_phydiskattr)

                        # Store a 'TestResult'
                        if _pdstatus == "normal":
                            self.mUpdateJSONMap(['Cluster','hostCheck',_host,'cellDisk',_phydisk,'TestResult'] ,"Pass")
                        else:
                            self.mUpdateJSONMap(['Cluster','hostCheck',_host,'cellDisk',_phydisk,'TestResult'] , "Fail")
                    else:
                        ebLogInfo("No details found for physical disk %s in cell %s" %(_phydisk, _host))
                if len(_loglist_phy) > 0:
                    self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Fail', '0104030014', _loglist_phy)
                else:
                    self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Pass', '0104030014')
            else:
                ebLogInfo("No physical disks found in cell %s" %(_host))

            if len(_loglist) > 0:
                self.mUpdateJSONMap(['Cluster','hostCheck',_host,'logs','cellDisk'], {})

                for i in range(len(_loglist)):
                    self.mUpdateJSONMap(['Cluster','hostCheck',_host,'logs','cellDisk',i], _loglist[i])

        # end mCellHealthCheck

        #
        # Cell test:
        #   Validate the flashcache on the cell
        #
        def mCheckFlashCache(self, aHost, aNode, aClunode, aCluhealth, aRecommend, aJsonMap, aCellFlashList):

            _clunode = aNode
            _host = aHost
            _node = aNode
            _recommend = aRecommend
            _cluhealth = aCluhealth
            _jsonMap = aJsonMap
            _celllist = aCellFlashList
            _loglist, _loglist_fc = [], []
            ebLogInfo('***** Running Cell FlashCache Status checks ******')

            self.mUpdateJSONMap(['Cluster','hostCheck',_host,'flashCache'],{})
            self.mUpdateJSONMap(['Cluster','hostCheck',_host,'flashCache','TestResult'], "Pass")

            # Check high level status of cell
            _cmd_str = 'cellcli -e list flashcache detail'
            _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
            _out = _o.readlines()
            if _out:
                _fcstatus = "normal"
                self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Pass', '0104030016')
                _flashattr = _host
                for _line in _out:
                    _key = _line.lstrip().split(" ")[0].rstrip()
                    _value = _line.lstrip().split(":", 1)[1].lstrip().rstrip()
                    if _value == "":
                        _value = "None"
                    self.mUpdateJSONMap(['Cluster','hostCheck',_host,'flashCache',_key],_value)
                    _flashattr = _flashattr + "::" + _key + _value

                    if (_key == "status:") and (_value != "normal"):
                        _recommend.append("ERROR: On Cell %s, flashcache status is shown as %s" %(_host, _value))
                        _loglist.append(_recommend[-1])
                        _loglist_fc.append(_recommend[-1])
                        _fcstatus = _value

                _celllist.append(_host)

                _cluhealth.mSetFlashAttr(_flashattr)

                # Store a 'TestResult'
                if _fcstatus != "normal":
                    self.mUpdateJSONMap(['Cluster','hostCheck',_host,'flashCache','TestResult'],"Fail")
                    if len(_loglist_fc) > 0:
                        self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Fail', '0104030015', _loglist)
                else:
                    self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Pass', '0104030015')
            else:
                # Missing flashcache. ERROR only if missing in a subset of the cells (checked later)
                _recommend.append("WARNING: On Cell %s, flashcache is missing!!" %(_host))
                _loglist.append(_recommend[-1])
                self.mUpdateJSONMap(['Cluster','hostCheck',_host,'flashCache','TestResult'],"Fail")

            if len(_loglist) > 0:
                self.mUpdateJSONMap(['Cluster','hostCheck',_host, 'logs', 'flashCache'],{})
                for i in range(len(_loglist)):
                    self.mUpdateJSONMap(['Cluster','hostCheck',_host,'logs','flashCache',i],_loglist[i])

        # end


        def mCheckDBStatusOnCell(self, aHost, aNode, aClunode, aCluhealth, aRecommend, aJsonMap):
            _clunode = aNode
            _host = aHost
            _node = aNode
            _recommend = aRecommend
            _cluhealth = aCluhealth
            _jsonMap = aJsonMap
            _loglist = []
            ebLogInfo('***** Running Database Status on Cell check ******')
            self.mUpdateJSONMap(['Cluster','hostCheck',_host,'DBStatus'],{})
            self.mUpdateJSONMap(['Cluster','hostCheck',_host,'DBStatus','TestResult'], "Pass")

            # Check high level status of cell
            _cmd_str = 'cellcli -e LIST DATABASE'
            _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
            _out = _o.readlines()
            if _out:
                for _line in _out:
                    if 'ASM' in _line or _line.strip() == '':
                        continue
                    if 'CELL-02559' in _line:
                        ebLogWarn('*** CellSrv not set yet in %s' % (_host))
                        _recommend.append('WARNING: CellSrv not set yet in %s' % (_host))
                        _loglist.append(_recommend[-1])

                        continue
                    ebLogWarn('*** Unexpected DB on Cell, DB %s found in cell %s' % (_line.rstrip(), _host))
                    _recommend.append('WARNING: Unexpected DB on Cell, DB %s found in cell %s' % (_line.rstrip(), _host))
                    _loglist.append(_recommend[-1])

              
            if len(_loglist) > 0:
                self.mUpdateJSONMap(['Cluster','hostCheck',_host, 'logs', 'DBStatus'],{})
                for i in range(len(_loglist)):
                    self.mUpdateJSONMap(['Cluster','hostCheck',_host,'logs','DBStatus',i],_loglist[i])

        #end mCheckDBStatusOnCell

        #
        # Dom0 test:
        # Check all stale locks on Dom0
        #
        def mCheckStaleLocks(self, aHost, aNode, aClunode, aCluhealth, aRecommend, aJsonMap):

            _clunode = aNode
            _host = aHost
            _node = aNode
            _recommend = aRecommend
            _jsonMap = aJsonMap
            _testResult = "Fail"
            _uuid = None

            _cmd_str = 'cat /tmp/exacs_dom0_lock'
            _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
            _out = _o.readlines()
            if _out:
                for _line in _out:
                    _uuid = _line.lstrip().rstrip()
                    break

            if _uuid is not None:
                _db = ebGetDefaultDB()
                _req = _db.mGetRequest(_uuid)
                if _req is not None:
                    #check if status is in pending state
                    if _req[1] == 'Pending':
                        _testResult = 'Pass'
            else:
                _testResult = 'Pass'

            if _testResult == "Fail":
                ebLogInfo("WARNING: stale lock with uuid %s found on %s" %(_uuid, _host))
                _recommend.append("WARNING: stale lock with uuid %s found on %s" %(_uuid, _host))
                _jsonMap['Cluster']['hostCheck'][_host]['logs']['generic'].append(_recommend[-1])
                self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Fail', '0103010017', _recommend[-1])
            else:
                self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Pass', '0103010017')
        # end


        #
        # Dom0 test:
        #   Validate eth1/eth2/eth3/eth4/eth5 and ib0/ib1
        #
        def mCheckNetIfs(self, aHost, aNode, aClunode, aCluhealth, aRecommend, aJsonMap):

            _clunode = aNode
            _host = aHost
            _node = aNode
            _recommend = aRecommend
            _cluhealth = aCluhealth
            _jsonMap = aJsonMap
            _testResult = "Pass"
            _loglist, _loglist_eth, _loglist_iba, _loglist_ibl, _loglist_ibs = [], [], [], [], []
            _ethlist = ['eth0', 'eth1', 'eth2', 'eth3', 'eth4', 'eth5']

            # Run ethtool against each eth interface and look for 'yes'
            _ethlink = None
            _ethlinkdown = None
            for _eth in _ethlist:
                _cmd_str = 'ethtool ' + _eth + ' | grep \"Link detected\"'
                _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
                _out = _o.readlines()
                if _out:
                    for _line in _out:
                        _ethstate = _line.split(":")[1].lstrip().rstrip()
                        if _ethstate == "no":
                            _recommend.append("ERROR: On Dom0 %s, no link detected for %s" %(_host, _eth))
                            _loglist.append(_recommend[-1])
                            _loglist_eth.append(_recommend[-1])
                            _testResult = "Fail"
                            if _ethlinkdown == None:
                                _ethlinkdown = _eth
                            else:
                                _ethlinkdown = _ethlinkdown + "," + _eth
                        else:
                            if _ethlink == None:
                                _ethlink = _eth
                            else:
                                _ethlink = _ethlink + "," + _eth
                        break
                else:
                    ebLogInfo('ERROR: Ethernet interface %s not found in Dom0 %s' %(_eth, _host))
                    _testResult = "Fail"

            _cluhealth.mSetEthLink(_ethlink)

            # Run ibstat -l and determine the Infiniband device name
            _ibdevice = None
            _cmd_str = 'ibstat -l'
            _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
            _out = _o.readlines()
            if _out:
                for _line in _out:
                    _ibdevice = _line.lstrip().rstrip()
                    break
            else:
                ebLogInfo('ERROR: Infiniband interface not found in Dom0 %s' %(_host))
                _testResult = "Fail"

            _cluhealth.mSetIbDevice(_ibdevice)

            # Run ibstat -s on the device and determine number of ports
            _numibdevs = 0
            if _ibdevice != None:

                _cmd_str = 'ibstat ' + _ibdevice + ' -s |grep \"Number of ports\"'
                _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
                _out = _o.readlines()
                if _out:
                    for _line in _out:
                        _numibdevs = int(_line.split(":")[1].lstrip().rstrip())
                        break
                else:
                    ebLogInfo('ERROR: Infiniband status not found for device %s' %(_ibdevice))
                    _testResult = "Fail"

            _cluhealth.mSetIbPorts(str(_numibdevs))

            # Run ibstat <device> <portnum> for each port
            # and look for 'State' and 'Physical state'
            _ibstate = None
            _ibphystate = None
            _ibs = None
            _ibps = None

            if _numibdevs != 0:

                for _num in range(1,_numibdevs+1):
                    _cmd_str = 'ibstat ' + _ibdevice + ' ' + str(_num)
                    _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
                    _out = _o.readlines()
                    if _out:
                        for _line in _out:
                            if "State:" in _line:
                                _ibstate = _line.split(":")[1].lstrip().rstrip()
                                if _ibstate != "Active":
                                    _recommend.append("ERROR: On Dom0 %s state of IB device %s on port %d is not Active" %(_host, _ibdevice, _num))
                                    _loglist.append(_recommend[-1])
                                    _loglist_iba.append(_recommend[-1])
                                    _testResult = "Fail"
                                if _ibs == None:
                                    _ibs = "Port:" + str(_num) + "::State:" + _ibstate
                                else:
                                    _ibs = _ibs + ", " + "Port:" + str(_num) + "::State:" + _ibstate
                            if "Physical state:" in _line:
                                _ibphystate = _line.split(":")[1].lstrip().rstrip()
                                if _ibphystate != "LinkUp":
                                    _recommend.append("ERROR: On Dom0 %s state of IB device %s on port %d is not Active" %(_host, _ibdevice, _num))
                                    _loglist.append(_recommend[-1])
                                    _loglist_ibl.append(_recommend[-1])
                                    _testResult = "Fail"
                                if _ibps == None:
                                    _ibps = "Port:" + str(_num) + "::PhysicalState:" + _ibphystate
                                else:
                                    _ibps = _ibps + ", " + "Port:" + str(_num) + "::PhysicalState:" + _ibphystate
                        if _ibstate == None or _ibphystate == None:
                            _recommend.append("ERROR: On Dom0 %s ibstat command failed for IB device %s port %d" %(_host, _ibdevice, _num))
                            _loglist.append(_recommend[-1])
                            _loglist_ibs.append(_recommend[-1])
                            _testResult = "Fail"
                    else:
                        ebLogInfo('ERROR: Infiniband status not found for device %s port %d' %(_ibdevice, _num))
                        _testResult = "Fail"

                _cluhealth.mSetIbState(_ibs)
                _cluhealth.mSetIbPstate(_ibps)

            # Save pkey list from one of the ports for verification later
            if _numibdevs != 0:
                _cmd_str = 'cat /sys/class/infiniband/' + _ibdevice + '/ports/1/pkeys/* | grep -v 0x00'
                _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
                _out = _o.readlines()
                if _out:
                    _ibpkeylist = ''
                    for _line in _out:
                        _ibpkeylist = _ibpkeylist + "," + _line.lstrip().rstrip()
                    _ibpkeylist = _ibpkeylist[1:]
                    _cluhealth.mSetIbPkeylist(_ibpkeylist)
                else:
                    ebLogInfo('ERROR: Infiniband pkey list not found for device %s' %(_ibdevice))
                    _testResult = "Fail"

            # Save results
            _jsonMap['Cluster']['hostCheck'][_host]['TestResult'] = _testResult
            _jsonMap['Cluster']['hostCheck'][_host]['ethLinkDown'] = _ethlinkdown

            for i in range(len(_loglist)):
                _jsonMap['Cluster']['hostCheck'][_host]['logs']['network'][i] = _loglist[i]

            if len(_loglist_eth) > 0:
                self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Fail', '0104010018', _loglist_eth)
            else:
                self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Pass', '0104010018')
            if len(_loglist_iba) > 0:
                self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Fail', '0104010019', _loglist_iba)
            else:
                self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Pass', '0104010019')
            if len(_loglist_ibl) > 0:
                self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Fail', '0104010020', _loglist_ibl)
            else:
                self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Pass', '0104010020')
            if len(_loglist_ibs) > 0:
                self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Fail', '0104010021', _loglist_ibs)
            else:
                self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Pass', '0104010021')
        # end

        #
        # Dom0 test:
        # Perform network consistency check on Dom0 using ipconf
        #
        def mCheckNetConsistency(self, aHost, aNode, aClunode, aCluhealth, aRecommend, aJsonMap):

            _clunode = aNode
            _host = aHost
            _node = aNode
            _recommend = aRecommend
            _cluhealth = aCluhealth
            _jsonMap = aJsonMap
            _testResult = "Fail"
            _loglist = []

            _cmd_str = '/usr/local/bin/ipconf.pl -nocodes -conf /opt/oracle.cellos/cell.conf -check-consistency -semantic -at-runtime'
            _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
            _out = _o.readlines()
            if _out:
                for _line in _out:
                    if "PASSED" in _line:
                        _testResult = "Pass"
            else:
                ebLogInfo("ERROR running network consistency check on %s" %(_host))

            _cluhealth.mSetDom0NetCons(_testResult)

            if _testResult == "Fail":
                ebLogInfo("ERROR: Network consistency check failed on %s" %(_host))
                _recommend.append("ERROR: Network consistency check failed on %s" %(_host))
                _dictLen = len(_jsonMap['Cluster']['hostCheck'][_host]['logs']['network'])
                _jsonMap['Cluster']['hostCheck'][_host]['logs']['network'][_dictLen] = "Failure running /usr/local/bin/ipconf.pl -nocodes -conf /opt/oracle.cellos/cell.conf -check-consistency -semantic -at-runtime"
                self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Fail', '0104010022', _recommend[-1])
            else:
                self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Pass', '0104010022')
            _jsonMap['Cluster']['hostCheck'][_host]['netConsistency'] = _testResult
            _jsonMap['Cluster']['hostCheck'][_host]['TestResult'] = _testResult

        # end

        # Dom0 test:
        # All pre-provisioning network checks invoked from here
        def mPreProvNetworkChecks(self, aHost, aNode, aClunode, aCluhealth, aRecommend, aJsonMap):

            _host = aHost
            _node = aNode
            _clunode = aClunode
            _cluhealth = aCluhealth
            _recommend = aRecommend
            _jsonMap = aJsonMap

            ebLogInfo('*** *** Pre-provisioning check: verifying bridge setup is clean on %s' %(_host))
            self.mCheckBridgeState(_host, _node, _clunode, _cluhealth, _recommend, _jsonMap)

            ebLogInfo('*** *** Pre-provisioning check: verifying bonded interfaces are good on %s' %(_host))
            self.mCheckBondedNetworks(_host, _node, _clunode, _cluhealth, _recommend, _jsonMap)

            ebLogInfo('*** *** Pre-provisioning check: verifying if bridges and bonded i/fs match on %s' %(_host))
            self.mCompareBondedBridges(_host, _node, _clunode, _cluhealth, _recommend, _jsonMap)

            ebLogInfo('*** *** Pre-provisioning check: verifying firewall rules are empty on %s' %(_host))
            self.mCheckEbtables(_host, _node, _clunode, _cluhealth, _recommend, _jsonMap)
        # end

        # Dom0 test:
        # All pre-provisioning system checks invoked from here
        def mPreProvSystemChecks(self, aHost, aNode, aClunode, aCluhealth, aRecommend, aJsonMap):

            _host = aHost
            _node = aNode
            _clunode = aNode
            _cluhealth = aCluhealth
            _recommend = aRecommend
            _jsonMap = aJsonMap

            ebLogInfo('*** *** Pre-provisioning check: verifying vm image versions on %s' %(_host))
            self.mCheckVmImage(_host, _node, _clunode, _cluhealth, _recommend, _jsonMap)

            ebLogInfo('*** *** Pre-provisioning check: for stale domU images in dom0 - %s' %(_host))
            _pchecks = ebCluPreChecks(self.mGetEbox())
            if _pchecks.mVMPreChecks(aHost=_host):
                ebLogInfo("ERROR: stale domU images found in dom0 - %s" %(_host))
                _recommend.append("ERROR: stale domU images found in dom0 - %s" %(_host))
                _jsonMap['Cluster']['hostCheck'][_host]['logs']['generic'].append(_recommend[-1])
                self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Pass', '0103010023', _recommend[-1])

            # environments and set self.__shared_env
            if (self.__ebox.SharedEnv() == True):
                ebLogInfo('*** *** Pre-provisioning check: for available free memory in dom0 - %s' %(_host))
                _precheck = ebCluPreChecks(self.__ebox)
                if not _precheck.mCheckDom0Mem(_host):
                    ebLogInfo("WARNING: memsize in XML is greater than available free memory in dom0 - %s" %(_host))
                    _recommend.append("WARNING: memsize in XML is greater than available free memory in dom0 - %s" %(_host))
                    _jsonMap['Cluster']['hostCheck'][_host]['logs']['generic'].append(_recommend[-1])
                    self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Pass', '0103010024', _recommend[-1])


        # end

        # Dom0/Switch test:
        # Check if root partition has enough space.
        def mCheckRootSpace(self, aHost, aNode, aClunode, aCluhealth, aRecommend, aJsonMap):
            _host = aHost
            _recommend = aRecommend
            _jsonMap = aJsonMap
            #initialize threshold value
            _threshold_root_space = "85"
            _precheck = ebCluPreChecks(self.__ebox)
            if "threshold_root_space" in self.mGetHcConfig():
                #add in healthcheck.conf if want to override default value
                _threshold_root_space = self.mGetHcConfig()["threshold_root_space"]
            #Used '/' to pass root partition
            if not _precheck.mCheckUsedSpace(_host,'/',_threshold_root_space):
                ebLogInfo("WARNING: space used in root partition is more than threshold(%s%%) - %s" %(_threshold_root_space, _host))
                _recommend.append("WARNING: space used in root partition is more than threshold(%s%%) - %s" %(_threshold_root_space, _host))
                _jsonMap['Cluster']['hostCheck'][_host]['logs']['generic'].append(_recommend[-1])
        # end

        # Dom0 test:
        # Check the bridges on the dom0.
        # Called pre-provisioning. Only eth0 related bridges must be present
        #
        def mCheckBridgeState(self, aHost, aNode, aClunode, aCluhealth, aRecommend, aJsonMap):

            _clunode = aNode
            _host = aHost
            _node = aNode
            _recommend = aRecommend
            _cluhealth = aCluhealth
            _jsonMap = aJsonMap
            _testResult = "Pass"
            _loglist, _loglist_sup, _loglist_ver = [], [], []
            _bridgelist = None
            _dom0bridgelist = [ "vmbondeth0", "vmbondeth1", "vmeth0", "vmeth1"]

            _cmd_str = 'brctl show'
            _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
            _out = _o.readlines()
            if _out:
                # Remove the first line from the output (column names)
                _out.pop(0)

                # TODO!! Check if system is freshly (re)imaged
                # If yes, no bridges are expected

                for _line in _out:
                    # First column contains bridge name
                    _bridge = _line.split("\t", 1)[0]
                    if (_bridge == ""):
                        continue

                    if _bridgelist == None:
                        _bridgelist = _bridge
                    else:
                        _bridgelist = _bridgelist + "," + _bridge

                    # We should not have any bridge apart from vmbondeth0 and vmeth0
                    if _bridge not in _dom0bridgelist:
                        _testResult = "Fail"
                        _recommend.append("ERROR: Pre-Provisioning: Bridge %s not supposed to be present in %s" %(_bridge, _host))
                        _loglist_sup.append(_recommend[-1])
                        _dictLen = len(_jsonMap['Cluster']['hostCheck'][_host]['logs']['network'])
                        _jsonMap['Cluster']['hostCheck'][_host]['logs']['network'][_dictLen] = _recommend[-1]

            else:
                ebLogInfo("Bridge verification failed on %s" %(_host))
                _testResult = "Fail"
                _recommend.append("ERROR: Pre-Provisioning: Bridge verification failed on %s" %(_host))
                _loglist_ver.append(_recommend[-1])
                _dictLen = len(_jsonMap['Cluster']['hostCheck'][_host]['logs']['network'])
                _jsonMap['Cluster']['hostCheck'][_host]['logs']['network'][_dictLen] = _recommend[-1]

            _cluhealth.mSetDom0BridgeList(_bridgelist)

            _jsonMap['Cluster']['hostCheck'][_host]['bridgeList'] = _bridgelist
            _jsonMap['Cluster']['hostCheck'][_host]['TestResult'] = _testResult

            if len(_loglist_sup) > 0:
                self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Fail', '0103010025', _loglist_sup)
            else:
                self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Pass', '0103010025')
            if len(_loglist_ver) > 0:
                self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Fail', '0103010026', _loglist_ver)
            else:
                self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Pass', '0103010026')

        # end

        # Dom0 test:
        # Check the bonded interfaces on dom0. Validate against entries in the XML file
        # Called pre-provisioning. Only eth0 related bridges must be present
        #
        def mCheckBondedNetworks(self, aHost, aNode, aClunode, aCluhealth, aRecommend, aJsonMap):

            _clunode = aNode
            _host = aHost
            _node = aNode
            _recommend = aRecommend
            _cluhealth = aCluhealth
            _jsonMap = aJsonMap
            _testResult = "Pass"
            _loglist, _loglist_ver, _loglist_xml = [], [], []
            _bondedifs = []
            _masterslave = {}

            # First get the list of bonded interfaces, and their slaves from the XML
            _eboxnetworks = self.mGetEboxNetworks()

            for _key in _eboxnetworks.mGetNetworkIdList():
                _netmaster = _eboxnetworks.mGetNetworkConfig(_key).mGetNetMaster().lstrip().rstrip()
                if "bond" in _netmaster:
                    _netslave = _eboxnetworks.mGetNetworkConfig(_key).mGetNetSlave().lstrip().rstrip()
                    if "Undefined" in _netslave:
                        _netslave = "none none"

                    # Add the master and slaves to a dict
                    # Since all VMs are configured same, overriding is ok here
                    _masterslave[_netmaster] = _netslave

            _jsonMap['Cluster']['hostCheck'][_host]['bondedIfs'] = {}

            for _master in _masterslave.keys():

                _slaveset = None

                _cmd_str = 'cat /proc/net/bonding/' + _master + "| grep \"Slave Interface\""
                _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
                _out = _o.readlines()
                if _out:
                    for _line in _out:
                        _slave = _line.split(":")[1].lstrip().rstrip()
                        if _slaveset == None:
                            _slaveset = _slave
                        else:
                            _slaveset = _slaveset + " " + _slave
                else:
                    ebLogInfo("Verification of bonded interfaces failed on %s" %(_host))
                    _testResult = "Fail"
                    _recommend.append("ERROR: Pre-Provisioning: Verification of bonded interfaces failed on %s" %(_host))
                    _loglist_ver.append(_recommend[-1])
                    _dictLen = len(_jsonMap['Cluster']['hostCheck'][_host]['logs']['network'])
                    _jsonMap['Cluster']['hostCheck'][_host]['logs']['network'][_dictLen] = _recommend[-1]

                # Store results in JSON and log file
                _jsonMap['Cluster']['hostCheck'][_host]['bondedIfs'][_master] = {}
                _jsonMap['Cluster']['hostCheck'][_host]['bondedIfs'][_master]['slaves'] = _slaveset

                _bondedifs.append(_master + "::" + _slaveset)

                # TODO!! Check if system is freshly (re)imaged
                # If yes, no bonded interfaces are expected

                # Compare output from dom0 with entries in XML
                if _slaveset != _masterslave[_master]:
                    ebLogInfo("Bonded interface verification: Mismatch between XML file and dom0 %s" %(_host))
                    _testResult = "Fail"
                    _recommend.append("ERROR: Pre-provisioning - %s for %s XML file shows slaves as \"%s\" while dom0 shows \"%s\"" %(_host, _master, _masterslave[_master], _slaveset ))
                    _loglist_xml.append(_recommend[-1])
                    _dictLen = len(_jsonMap['Cluster']['hostCheck'][_host]['logs']['network'])
                    _jsonMap['Cluster']['hostCheck'][_host]['logs']['network'][_dictLen] = _recommend[-1]

            # This is for the log file
            _cluhealth.mSetDom0BondedIfs(_bondedifs)
            _jsonMap['Cluster']['hostCheck'][_host]['TestResult'] = _testResult

            if len(_loglist_ver) > 0:
                self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Fail', '0103010027', _loglist_ver)
            else:
                self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Pass', '0103010027')
            if len(_loglist_xml) > 0:
                self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Fail', '0103010028', _loglist_xml)
            else:
                self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Pass', '0103010028')

        # end

        # Dom0 test:
        # Check the bonded interfaces on dom0. Validate against entries in the XML file
        # Called pre-provisioning. Only eth0 related bridges must be present
        #
        def mCompareBondedBridges(self, aHost, aNode, aClunode, aCluhealth, aRecommend, aJsonMap):

            _clunode = aNode
            _host = aHost
            _node = aNode
            _recommend = aRecommend
            _cluhealth = aCluhealth
            _jsonMap = aJsonMap
            _testResult = "Pass"
            _loglist = []

            _bridges = _cluhealth.mGetDom0BridgeList()
            _bondlist = _cluhealth.mGetDom0BondedIfs()
            _numbridges = 0
            _numbonds = 0

            _brlist = _bridges.split(",")
            for _brl in _brlist:
                if "bond" in _brl:
                    _numbridges += 1

            if _numbridges == len(_bondlist):
                ebLogInfo("dom0 %s: Number of bridges correspond to bonded interfaces detected" %(_host))
            else:
                ebLogInfo("dom0 %s: Mismatch between number of bridges and bonded interfaces detected" %(_host))
                _testResult = "Fail"
                _recommend.append("ERROR: Pre-provisioning - %s: %d bond-bridges found while bonded-interfaces detected are %d" %(_host, _numbridges, len(_bondlist) ))
                _loglist.append(_recommend[-1])
                _dictLen = len(_jsonMap['Cluster']['hostCheck'][_host]['logs']['network'])
                _jsonMap['Cluster']['hostCheck'][_host]['logs']['network'][_dictLen] = _recommend[-1]

            _jsonMap['Cluster']['hostCheck'][_host]['TestResult'] = _testResult

            if len(_loglist) > 0:
                self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Fail', '0103010029', _loglist)
            else:
                self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Pass', '0103010029')

        # end

        # Dom0 test:
        # Called during pre-provisioning
        # ebtables -L must not have any entries
        #
        def mCheckEbtables(self, aHost, aNode, aClunode, aCluhealth, aRecommend, aJsonMap):

            _clunode = aClunode
            _host = aHost
            _node = aNode
            _recommend = aRecommend
            _cluhealth = aCluhealth
            _jsonMap = aJsonMap
            _testResult = "Pass"
            _loglist = []

            def _check_vif_whitelist_file_exist():
                _clusterId = _clunode.mGetClusterId()
                # Check for presence of vif-whitelist file
                _ebt_wl_file   = '/opt/exacloud/network/vif-whitelist'+'.'+ _clusterId
                _cmdstr = 'ls -l ' + _ebt_wl_file
                _i, _o, _e = _node.mExecuteCmd(_cmdstr, aTimeout=180)
                if _o is not None:
                    _out = _o.readlines()
                    if len(_out):
                        ebLogError('*** Ebtables whitelist file %s exists on %s. ***' %(_clusterId, _host))
                        return True
                    else:
                        ebLogInfo('*** Ebtables whitelist file does not exist for given cluster %s on host %s ***' %(_clusterId, _host))
                return False

            #for exacm, 'ebtables_setup' in exabox.conf must be false
            if(self.__ebox.mIsExacm() == True):
                if self.__ebox.mGetEbtableSetup():
                    ebLogWarn("ebtables_setup must be False for exacm env for %s" %(_host))
                    _recommend.append("WARNING: ebtables_setup must be False for exacm env for %s" %(_host))
                    _testResult = "Fail"

            if(_check_vif_whitelist_file_exist() == True):
                ebLogWarn("Pre-provisioning: ebtables whitelist file found for %s " %(_host))
                _recommend.append("WARNING: Pre-provisioning: ebtables whitelist file found for %s " %(_host))
                _testResult = "Fail"
            
            #check for ebtable entries if it is not multi-vm
            if(self.__ebox.SharedEnv() == False):

                _cmd_str = 'ebtables -L | grep \"Bridge chain\"'
                _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
                _out = _o.readlines()
                if _out:
                    for _line in _out:
                        _chain = _line.split(",")[0].split(":")[1].lstrip().rstrip()
                        _entries = _line.split(",")[1].split(":")[1].lstrip().rstrip()
                        if _entries != "0":
                            _testResult = "Fail"
                            _recommend.append("ERROR: Pre-provisioning: %s : ebtables for %s show %s entries. Should be empty" %(_host, _chain, _entries))
                            _loglist.append(_recommend[-1])
                            _dictLen = len(_jsonMap['Cluster']['hostCheck'][_host]['logs']['network'])
                            _jsonMap['Cluster']['hostCheck'][_host]['logs']['network'][_dictLen] = _recommend[-1]
                else:
                    ebLogInfo("ERROR running ebtables check on %s" %(_host))
                    _testResult = "Fail"

            if _testResult == "Fail":
                ebLogInfo("Pre-provisioning: Verification of ebtables failed on %s" %(_host))

            # Final result
            _cluhealth.mSetDom0Ebtables(_testResult)
            _jsonMap['Cluster']['hostCheck'][_host]['TestResult'] = _testResult

            if len(_loglist) > 0:
                self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Fail', '0103010031', _loglist)
            else:
                self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Pass', '0103010031')

        # end

        # Switch test:
        # Case 1: If freshly provisioned, smnodes list must be null
        # Case 2: If provisioned at least once, output of smnodes list must match ibswitches
        #
        def mCheckSmnodesList(self, aHost, aNode, aClunode, aCluhealth, aRecommend, aJsonMap):

            _clunode = aNode
            _host = aHost
            _node = aNode
            _recommend = aRecommend
            _cluhealth = aCluhealth
            _jsonMap = aJsonMap
            _testResult = "Pass"
            _loglist = []
            _smnodeslist = []
            _ibswlist = []

            ebLogInfo('************** Validating smnodes List *************')
            _cmd_str = 'smnodes list'
            _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
            _out = _o.readlines()
            if _out:
                # Switch has been provisioned at least once
                for _line in _out:
                    _smnode = _line.lstrip().rstrip()
                    _smnodeslist.append(_smnode)
                    self.mAppendJSONMap(['Cluster','hostCheck',_host,'smnodes'],_smnode)
                self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Pass', '0104040032')
            else:
                # Ok only in case of a freshly provisioned cluster
                ebLogInfo("\'smnodes list\' on %s returned null. OK only if switch is freshly provisioned" %(_host))
                _recommend.append("WARNING: \'smnodes list\' on %s returned null. OK only if switch is freshly provisioned" %(_host))
                self.mUpdateJSONMapdictLen(['Cluster','hostCheck',_host,'logs','switch'],_recommend[-1])
                self.mUpdateJSONMap(['Cluster','hostCheck',_host,'TestResult'], _testResult)
                self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Pass', '0104040032', _recommend[-1])
                return

            # Obtain the output of ibswitches
            _cmd_str = 'ibswitches'
            _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
            _out = _o.readlines()
            if _out:
                for _line in _out:
                    _ibsw = _line.split("\"")[1].split(" ")[-1]
                    _ibswlist.append(_ibsw)
                    self.mAppendJSONMap(['Cluster','hostCheck',_host,'ibswitches'], _line.rstrip())

                # ibswitches entries must match with smnodes list entries
                if ( len(_smnodeslist) != len(_ibswlist)):
                    ebLogInfo("On %s the number of entries returned by ibswitches differs from output of smnodes" %(_host))
                    _recommend.append("ERROR: On %s the number of entries returned by ibswitches differs from output of smnodes" %(_host))
                    self.mUpdateJSONMapdictLen(['Cluster','hostCheck',_host,'logs','switch'],_recommend[-1])
                    self.mUpdateJSONMap(['Cluster','hostCheck',_host,'TestResult'], _testResult)
                    self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Fail', '0104040033', _recommend[-1])
                    _testResult = "Fail"
                else:
                    self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Fail', '0104040033')

                # Entries in both lists must match
                for _ibsw in _ibswlist:
                    if _ibsw not in _smnodeslist:
                        ebLogInfo("On %s ibswitches output %s does not appear in smnodes list" %(_host, _ibsw))
                        _recommend.append("ERROR: On %s ibswitches output %s does not appear in smnodes list" %(_host, _ibsw))
                        _loglist.append(_recommend[-1])
                        _testResult = "Fail"
            else:
                ebLogInfo("ERROR running ibswitches check on %s" %(_host))
                ebLogInfo("smnodes list verification failed on %s" %(_host))
                _testResult = "Fail"

            # Final result
            self.mUpdateJSONMap(['Cluster','hostCheck',_host,'TestResult'], _testResult)

            if len(_loglist) > 0:
                self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Fail', '0104040034', _loglist)
            else:
                self.mUpdateJSON(['Cluster', 'hostCheck', _host, 'logs'], 'Pass', '0104040034')

        # end

        # Dom0 test:
        # Check the vm image versions.
        # Called pre-provisioning
        #
        def mCheckVmImage(self, aHost, aNode, aClunode, aCluhealth, aRecommend, aJsonMap):

            _testResult = "Pass"

            _dom0ImgInfos = getDom0VMImagesInfo(aHost, aComputeSha256Sum=self.mGetLongRunCheck())

            if not _dom0ImgInfos:
                _testResult = "Fail"
                ebLogHealth('ERR',
                            '*** Pre-provisioning - No VM image found on Dom0 {}'.format(aHost))
                aRecommend.append('ERROR: Pre-provisioning - No VM image found on Dom0 {}'
                                    .format(aHost))
                ebLogWarn(aRecommend[-1])
                aJsonMap['Cluster']['hostCheck'][aHost]['logs']['generic'].append(aRecommend[-1])
                self.mUpdateJSON(['Cluster', 'hostCheck', aHost, 'logs'],
                                  'Fail', '0103010035', aRecommend[-1])
            else:
                self.mUpdateJSON(['Cluster', 'hostCheck', aHost, 'logs'], 'Pass', '0103010035')

                if len(_dom0ImgInfos) > 1:
                    ebLogHealth('WRN',
                                ('*** Pre-provisioning - More than 1 VM image found on Dom0 {}'
                                   .format(aHost)))
                    aRecommend.append('WARNING: Pre-provisioning - '
                                        'More than 1 VM image found on Dom0 {}'.format(aHost))
                    ebLogWarn('*** Pre-provisioning - More than 1 VM image found on Dom0 {}'
                                .format(aHost))
                    (aJsonMap['Cluster']['hostCheck'][aHost]['logs']['generic']
                       .append(aRecommend[-1]))
                    self.mUpdateJSON(['Cluster', 'hostCheck', aHost, 'logs'],
                                      'Fail', '0103010036')
                else:   # _dom0ImgInfos has only one item
                    self.mUpdateJSON(['Cluster', 'hostCheck', aHost, 'logs'],
                                     'Pass', '0103010036')
                    _remoteImgInfo = _dom0ImgInfos[0]
                    _remoteImgIsKvm = _remoteImgInfo['isKvmImg']

                    if 'md5sum' in _remoteImgInfo:
                        _imgBaseName = _remoteImgInfo['imgBaseName']
                        _imgHash = _remoteImgInfo['md5sum']

                        if _imgHash is None:
                            _imgHash = -1
                            ebLogHealth('WRN',
                                        ('*** Fail to compute sha256sum for {} on {}'
                                           .format(_imgBaseName, aHost)))
                            ebLogWarn('*** Fail to compute sha256sum for {} on {}'
                                        .format(_imgBaseName, aHost))
                            aRecommend.append('ERROR: Fail to compute sha256sum for {} on {}'
                                                .format(_imgBaseName, aHost))

                        aJsonMap['Cluster']['hostCheck'][aHost]['SystemImageHash'] = _imgHash

                    _localImgInfo = getNewestVMImageArchiveInRepo(aIsKvm=_remoteImgIsKvm)

                    if _localImgInfo is None:
                        _testResult = "Fail"
                        aRecommend.append('ERROR: Pre-provisioning - Local System Image not found')
                        ebLogWarn(aRecommend[-1])
                        (aJsonMap['Cluster']['hostCheck'][aHost]['logs']['generic']
                           .append(aRecommend[-1]))
                        self.mUpdateJSON(['Cluster', 'hostCheck', aHost, 'logs'],
                                         'Fail', '0103010037', aRecommend[-1])
                    else:
                        _localImgVersion = _localImgInfo['imgVersion']
                        _remoteImgVersion = _remoteImgInfo['imgVersion']
                        ebLogDebug('*** Version of Local System Image is {}'
                                     .format(_localImgVersion))
                        self.mUpdateJSON(['Cluster', 'hostCheck', aHost, 'logs'],
                                         'Pass', '0103010037')

                        # Local image version should match Dom0 version
                        if _localImgVersion != _remoteImgVersion:
                            ebLogWarn('*** Local System Image version: {}'
                                        .format(_localImgVersion))
                            ebLogWarn('*** Dom0 System Image version: {}'
                                        .format(_remoteImgVersion))
                            ebLogHealth('WRN',
                                        ('*** Pre-provisioning - System Image on Dom0 {}'
                                           ' differs from local System Image'.format(aHost)))
                            aRecommend.append('WARNING: Pre-provisioning - System Image on Dom0'
                                                '{} differs from local System Image'.format(aHost))
                            ebLogWarn(aRecommend[-1])
                            (aJsonMap['Cluster']['hostCheck'][aHost]['logs']['generic']
                               .append(aRecommend[-1]))
                            self.mUpdateJSON(['Cluster', 'hostCheck', aHost, 'logs'],
                                             'Pass', '0103010038', aRecommend[-1])

            aJsonMap['Cluster']['hostCheck'][aHost]['TestResult'] = _testResult

        # end

        #
        # Validate the rack XML file
        #
        def mValidateXML(self):

            _ebox = self.mGetEbox()
            _eboxconfig = _ebox.mGetConfig()
            _recommend = self.mGetRecommend()

            ebLogInfo('*** Validating Cluster XML file: %s ***\n' %(self.mGetXMLPath()))
            _log_destination = ebLogSetHCLogDestination(self.mGetLogHandler(), True)

            _jsonHandler = self.mGetJsonHandler()
            _jsonResult = self.mGetJsonResult()
            _jsonMap = self.mGetJsonMap()
            _jsonMap['XML'] = {}

            ebLogHealth('NFO', '***                 Cluster XML File Validation          ***\n')

            ## Check if XML contains valid user elements
            ebLogInfo('*** *** Validating user nd group entries in the XML file')
            self.mCheckUserandGroupXML(_ebox, _recommend, _jsonMap)

            # Check if XML contains valid DNS server entries
            ebLogInfo('*** *** Validating DNS server entries in the XML file')
            self.mCheckDnsServers(_eboxconfig, _recommend, _jsonMap)

            # Check if XML contains valid NTP server entries
            ebLogInfo('*** *** Validating NTP server entries in the XML file')
            self.mCheckNtpServers(_eboxconfig, _recommend, _jsonMap)

            # Check if XML contains same netmask for domU and cells
            ebLogInfo('*** *** Validating SubnetMask for domU and cells in the XML file')
            self.mCheckSubnetMask(_eboxconfig, _recommend, _jsonMap)

            # Check if XML contains cdb/pdb type database entries only
            ebLogInfo('*** *** Validating database entries in the XML file')
            self.mCheckDatabases(_ebox, _recommend, _jsonMap)

            # Check if scan-names in XMl are resolvable
            ebLogInfo('*** *** Validating scan-name entries in the XML file')
            self.mCheckScanNames(_ebox, _recommend, _jsonMap)

            # Check Machine Config
            ebLogInfo('*** *** Validating \'machine\' entries in the XML file')
            self.mCheckMachineConfig(_ebox, _recommend, _jsonMap)

            # Check Network Overlapping
            ebLogInfo('*** *** Validating nw and gw entries in the XML file')
            self.mValidateNwOverlap(_ebox, _recommend, _jsonMap)

            # Check DiskGroup Config
            ebLogInfo('*** *** Validating \'diskGroup\' entries in the XML file')
            self.mCheckDiskGroup(_ebox, _recommend, _jsonMap)

            ebLogInfo('*** *** Validating \'network\' entries in the XML file')
            self.mCheckNetworksXml(_ebox, _recommend, _jsonMap)

            ebLogInfo('\n')
            ebLogInfo('*** Completed XML file validation\n')

            ebLogRemoveHCLogDestination(_log_destination)
            ebLogSetHCLogDestination(self.mGetDefaultLogHandler())


        def mCheckDnsServers(self, aConfig, aRecommend, aJsonMap):

            _recommend = aRecommend
            _jsonMap = aJsonMap
            _jsonMap['XML']['dnsServer'] = {}
            _jsonMap['XML']['dnsServer']['logs'] = []

            _testResult = "Pass"
            _dnss_list = []

            #dns servers listed for in machines
            _machines = self.mGetEbox().mGetMachines()
            for _machine in _machines.mGetMachineConfigList():
                _dnss_list += _machines.mGetMachineConfig(_machine).mGetDnsServers()

            #dns servers listed for in iloms (dom0, cells)
            _iloms = self.mGetEbox().mGetIloms()
            for _ilom in _iloms.mGetIlomsList():
                _dnss_list +=_iloms.mGetIlomConfig(_ilom).mGetDnsServers()
            
            # Remove duplicates
            _dnss_list = set(_dnss_list)

            ebLogHealth('NFO','\n')
            ebLogHealth('NFO','*** DNS Server Validation ***')

            # needed for running mDigTest. 
            _pchecks = ebCluPreChecks(self)

            for _dns in _dnss_list:
                ebLogHealth('NFO','DNS Server IP Address: %s' %(_dns))

                if _dns is None:
                    _recommend.append("WARNING: Blank <dnsServer> entries found in XML file")
                    _jsonMap['XML']['dnsServer']['logs'].append(_recommend[-1])
                    continue

                _jsonMap['XML']['dnsServer'][_dns] = {}
                _jsonMap['XML']['dnsServer'][_dns]['logs'] = {}
                _loglist = []

                # Check for IP address validity
                try:
                    socket.inet_aton(_dns)
                    ebLogHealth('NFO','***                  Valid IP Address: \t True')
                    _jsonMap['XML']['dnsServer'][_dns]['validIP'] = "True"
                except socket.error:
                    ebLogHealth('NFO','***                  Valid IP Address: \t False')
                    _recommend.append("ERROR: Incorrect IP Address %s listed as a DNS Server in XML" %(_dns))
                    _loglist.append(_recommend[-1])
                    _jsonMap['XML']['dnsServer'][_dns]['validIP'] = "False"
                    _jsonMap['XML']['dnsServer'][_dns]['TestResult'] = "Fail"
                    _testResult = "Fail"
                    continue

                # Ping test
                if self.mGetEbox().mPingHost(_dns):
                    ebLogHealth('NFO', '***                   Server Pingable: \t True')
                    _jsonMap['XML']['dnsServer'][_dns]['pingable'] = "True"
                else:
                    ebLogHealth('NFO', '***                   Server Pingable: \t False')
                    _recommend.append("ERROR: IP Address %s not pingable listed as a DNS Server in XML" %(_dns))
                    _jsonMap['XML']['dnsServer'][_dns]['pingable'] = "False"
                    _jsonMap['XML']['dnsServer'][_dns]['TestResult'] = "Fail"
                    _testResult = "Fail"
                    continue

                # nslookup
                _fqdn = self.mNslookupTest(_dns, _recommend)
                ebLogHealth('NFO', '***              FQDN as per nslookup: \t %s' %(_fqdn))
                _jsonMap['XML']['dnsServer'][_dns]['fqdn'] = _fqdn

                if _fqdn == "None":
                    _recommend.append("ERROR: nslookup failed for %s listed as DNS Server in XML" %(_dns))
                    _loglist.append(_recommend[-1])
                    _testResult = "Fail"
                    
                elif "dns" not in _fqdn:
                    _recommend.append("WARNING: %s listed as DNS Server in XML does not contain \"dns\" in its FQDN" %(_dns))
                    _loglist.append(_recommend[-1])

                # DIG test
                _digtest = _pchecks.mDigTest(_dns)
                if _digtest == False:
                    _recommend.append("ERROR: DIG test failed for %s listed as DNS Server in XML" %(_dns))
                    _loglist.append(_recommend[-1])
                    _jsonMap['XML']['dnsServer'][_dns]['digTest'] = "False"
                    _testResult = "Fail"
                else:
                    _jsonMap['XML']['dnsServer'][_dns]['digTest'] = "True"

                if _fqdn != "None" and _digtest == True:
                    _jsonMap['XML']['dnsServer'][_dns]['TestResult'] = "Pass"
                else:
                    _jsonMap['XML']['dnsServer'][_dns]['TestResult'] = "Fail"

                for i in range(len(_loglist)):
                    _jsonMap['XML']['dnsServer'][_dns]['logs'][i] = _loglist[i]

                if len(_jsonMap['XML']['dnsServer'][_dns]['logs']) == 0:
                    _jsonMap['XML']['dnsServer'][_dns].pop("logs", None)

            if len(_jsonMap['XML']['dnsServer']['logs']) == 0:
                _jsonMap['XML']['dnsServer'].pop("logs", None)
            _jsonMap['XML']['dnsServer']['TestResult'] = _testResult

        # End

        def mCheckNtpServers(self, aConfig, aRecommend, aJsonMap):

            _recommend = aRecommend
            _jsonMap = aJsonMap
            _jsonMap['XML']['ntpServer'] = {}

            _testResult = "Pass"
            _ntps_list = []

            #ntp servers listed for in machines
            _machines = self.mGetEbox().mGetMachines()
            for _machine in _machines.mGetMachineConfigList():
                _ntps_list += _machines.mGetMachineConfig(_machine).mGetNtpServers()

            #ntp servers listed for in iloms (dom0, cells)
            _iloms = self.mGetEbox().mGetIloms()
            for _ilom in _iloms.mGetIlomsList():
                _ntps_list +=_iloms.mGetIlomConfig(_ilom).mGetNtpServers()

            # Remove duplicates
            _ntps_list = set(_ntps_list)

            ebLogHealth('NFO','\n')
            ebLogHealth('NFO','*** NTP Server Validation ***')

            for _ntp in _ntps_list:

                ebLogHealth('NFO','NTP Server IP Address: %s' %(_ntp))

                if _ntp is None:
                    _recommend.append("ERROR: Blank <ntpServer> entries found in XML file")
                    continue

                _jsonMap['XML']['ntpServer'][_ntp] = {}
                _jsonMap['XML']['ntpServer'][_ntp]['logs'] = {}
                _loglist = []

                # Check for IP address validity
                try:
                    socket.inet_aton(_ntp)
                    ebLogHealth('NFO','***                  Valid IP Address: \t True')
                    _jsonMap['XML']['ntpServer'][_ntp]['validIP'] = "True"
                except socket.error:
                    ebLogHealth('NFO','***                  Valid IP Address: \t False')
                    _recommend.append("ERROR: Incorrect IP Address %s listed as a NTP Server in XML" %(_ntp))
                    _loglist.append(_recommend[-1])
                    _jsonMap['XML']['ntpServer'][_ntp]['validIP'] = "False"
                    _testResult = "Fail"
                    continue

                # Ping test
                if self.mGetEbox().mPingHost(_ntp):
                    ebLogHealth('NFO', '***                   Server Pingable: \t True')
                    _jsonMap['XML']['ntpServer'][_ntp]['pingable'] = "True"
                else:
                    ebLogHealth('NFO', '***                   Server Pingable: \t False')
                    _jsonMap['XML']['ntpServer'][_ntp]['pingable'] = "False"
                    _recommend.append("ERROR: ping failed for %s listed as NTP Server in XML" %(_ntp))
                    _testResult = "Fail"
                    continue

                # nslookup
                _fqdn = self.mNslookupTest(_ntp, _recommend)
                ebLogHealth('NFO', '***              FQDN as per nslookup: \t %s' %(_fqdn))

                if _fqdn == "None":
                    _recommend.append("ERROR: nslookup failed for %s listed as NTP Server in XML" %(_ntp))
                    _loglist.append(_recommend[-1])
                    _testResult = "Fail"
                elif "rtr" not in _fqdn:
                    _recommend.append("WARNING: %s listed as an NTP Server in XML does not contain \"rtr\" in its FQDN" %(_ntp))
                    _loglist.append(_recommend[-1])

                for i in range(len(_loglist)):
                    _jsonMap['XML']['ntpServer'][_ntp]['logs'][i] = _loglist[i]

                if len(_jsonMap['XML']['ntpServer'][_ntp]['logs']) == 0:
                    _jsonMap['XML']['ntpServer'][_ntp].pop("logs", None)
            _jsonMap['XML']['ntpServer']['TestResult'] = _testResult
        # End

        def mCheckDatabases(self, aConfig, aRecommend, aJsonMap):

            _eBox = self.mGetEbox()
            _config = aConfig
            _recommend = aRecommend
            _jsonMap = aJsonMap
            _jsonMap['XML']['databases'] = {}

            _testResult = "Pass"
            _validDBs = ['cdb', 'pdb']

            _databases = _config.mGetDatabases()
            _dblist = _databases.mGetDBconfigs()
            _dbidlist = []

            ebLogHealth('NFO','\n')
            ebLogHealth('NFO','*** XML Database entries validation ***')

            # Collate a list of all DB IDs
            for _db in _dblist:
                _dbid = _dblist[_db].mGetDBId()
                _dbidlist.append(_dbid)

            # Validate all database entries
            for _db in _dblist:

                _dbid = _dblist[_db].mGetDBId()
                _loglist = []
                _dbhome = _dblist[_db].mGetDBHome()
                #check databaseHome if it is for current cluster
                _dbHomeConfig  = _eBox.mGetDBHomes().mGetDBHomeConfig(_dbhome)
                if _dbHomeConfig is None:
                    continue

                _jsonMap['XML']['databases'][_dbid] = {}
                _jsonMap['XML']['databases'][_dbid]['logs'] = {}
                _dbtype = _dblist[_db].mGetDBType()
                _dbSid = _dblist[_db].mGetDBSid()
                _dbtemplate = _dblist[_db].mGetDBTemplate().text

                _jsonMap['XML']['databases'][_dbid]['dbType'] = _dbtype
                _jsonMap['XML']['databases'][_dbid]['dbSid'] = _dbSid
                _jsonMap['XML']['databases'][_dbid]['dbHome'] = _dbhome
                _jsonMap['XML']['databases'][_dbid]['dbTemplate'] = _dbtemplate

                ebLogHealth('NFO', '***                       Database ID: \t %s' %(_dbid))
                ebLogHealth('NFO', '***                     Database Type: \t %s' %(_dbtype))
                ebLogHealth('NFO', '***                      Database Sid: \t %s' %(_dbSid))
                ebLogHealth('NFO', '***                     Database Home: \t %s' %(_dbhome))
                ebLogHealth('NFO', '***                 Database Template: \t %s' %(_dbtemplate))

                #check for DB version
                _dbHomeVersion = str(_dbHomeConfig.mGetDBHomeVersion())
                
                #skip check for cdb/pdb if DB version is 11
                if _dbHomeVersion[:2] == '11':
                    continue

                # Only cdb-pdb type entries are expected
                if _dbtype not in _validDBs:
                    _recommend.append("ERROR: Invalid DB type %s found against DB ID %s" %(_dbtype, _dbid))
                    _loglist.append(_recommend[-1])
                    _testResult = "Fail"

                # The cdbid must be one of the other DB Ids
                _dbcdbid = _dblist[_db].mGetCDBid()
                if _dbtype == "cdb" and _dbcdbid != None:
                    _recommend.append("ERROR: Invalid CDB Id found for DB %s" %(_dbid))
                    _loglist.append(_recommend[-1])
                    _testResult = "Fail"
                elif _dbtype == "pdb" and _dbcdbid == None:
                    _recommend.append("ERROR: In DB %s the CDB ID field is missing" %(_dbid))
                    _loglist.append(_recommend[-1])
                    _testResult = "Fail"
                elif _dbtype == "pdb" and _dbcdbid not in _dbidlist:
                    _recommend.append("ERROR: DB %s has an incorrect CDB ID field %s" %(_dbid, _dbcdbid))
                    _loglist.append(_recommend[-1])
                    _testResult = "Fail"

                if _dbtype == "pdb":
                    _jsonMap['XML']['databases'][_dbid]['dbCdbId'] = _dbcdbid
                    ebLogHealth('NFO', '***                    Database CDBId: \t %s' %(_dbcdbid))

                for i in range(len(_loglist)):
                    _jsonMap['XML']['databases'][_dbid]['logs'][i] = _loglist[i]

                if len(_jsonMap['XML']['databases'][_dbid]['logs']) == 0:
                    _jsonMap['XML']['databases'][_dbid].pop("logs", None)

            _jsonMap['XML']['databases']["TestResult"] = _testResult
        # end

        def mGetSubnet(self, aIpAddr, aNetmask):
            _eBox = self.mGetEbox()
            #generate subnet using netmask and ipaddr
            if ':' not in aIpAddr:
                _mask_cidr = _eBox.mNetMaskToCIDR(aNetmask)
                _ip = aIpAddr
                _netMask = aNetmask
                _subnet = '.'.join([str(int(_pair[0]) & int(_pair[1])) for _pair in zip(_ip.split('.'), _netMask.split('.'))])
            else:
                # For IPv6 address, we can use the ipaddress library to generate subnet/network address.
                _subnet = str(ip_interface(aIpAddr + '/' + aNetmask).network.network_address)
            return _subnet

        #
        # Validate the subnet for domU and cell for storage inteface in XML file
        #
        def mCheckSubnetMask(self, aConfig, aRecommend, aJsonMap):

            _config = aConfig
            _recommend = aRecommend
            _jsonMap = aJsonMap

            _jsonMap['XML']['subnetMask'] = {}
            _jsonMap['XML']['subnetMask']['logs'] = {}
            _loglist = []
            _storage_subnet = None
            _storage_pkey  = None
            _err = False
            _logmsg = None
            _eBox = self.mGetEbox()
            _eBoxNetworks = _eBox.mGetNetworks()
            _, _domUs, _cells, _ = _eBox.mReturnAllClusterHosts()
            _cluhosts = _cells + _domUs
            ebLogHealth('NFO', '\n')
            ebLogHealth('NFO','*** SubnetMask check for DomUs and Cells ***')
            for _host in _cluhosts:
                _host_mac = _eBox.mGetMachines().mGetMachineConfig(_host)
                _net_list = _host_mac.mGetMacNetworks()

                for _net in _net_list:
                    _priv = _eBoxNetworks.mGetNetworkConfig(_net)
                    if _priv.mGetNetType() == 'private':
                        #generate subnet using netmask and ipaddr
                        _ip = _priv.mGetNetNatAddr()
                        if (_eBox.mIsExabm() or _eBox.mIsOciEXACC()) and (_host in _domUs):
                            _netmask = _priv.mGetNetNatMask()
                        else:
                            _netmask = _priv.mGetNetMask()
                        if _netmask != 'UNDEFINED':
                            _subnet = self.mGetSubnet(_ip, _netmask)
                        _pkey = _priv.mGetPkey()
                        _pkeyname = _priv.mGetPkeyName()
                        _hostname = _priv.mGetNetNatHostName()

                        if _pkeyname[:2] == 'st':
                            ebLogHealth('NFO','Mac Hostname: %s' %(_hostname))
                            if _storage_pkey is None:
                                _storage_pkey = _pkey
                                _storage_subnet = _subnet
                            elif _storage_pkey != _pkey:
                                ebLogHealth('NFO','*** Invalid STORAGE PKEY %s detected for %s of %s, skipping subnet check ***' %(_pkey, _hostname, _host))
                                _recommend.append('ERROR: Invalid STORAGE PKEY %s detected for %s of %s, skipping subnet check' %(_pkey, _hostname,_host))
                                _loglist.append(_recommend[-1])
                                _err = True
                                continue
                            else:
                                pass
                        else:
                            #skip for Cluster pkey used for clusterware in case of domu
                            continue

                        ebLogHealth('NFO','***                       host    : \t %s' %(_host))
                        ebLogHealth('NFO','***                       ipAddr  : \t %s' %(_ip))
                        ebLogHealth('NFO','***                       netmask : \t %s' %(_netmask))
                        ebLogHealth('NFO','***                       subnet  : \t %s' %(_subnet))
                        _jsonMap['XML']['subnetMask'][_hostname] = {}
                        _jsonMap['XML']['subnetMask'][_hostname]['IpAddress'] = _ip
                        _jsonMap['XML']['subnetMask'][_hostname]['Netmask'] = _netmask
                        _jsonMap['XML']['subnetMask'][_hostname]['Subnet'] = _subnet
                        _jsonMap['XML']['subnetMask'][_hostname]['HostName'] = _host

                        if(_subnet == _storage_subnet):
                            _jsonMap['XML']['subnetMask'][_hostname]['TestResult'] = "Pass"
                            ebLogHealth('NFO','***                  Subnet Match: \t True')
                        else:
                            _jsonMap['XML']['subnetMask'][_hostname]['TestResult'] = "Fail"
                            ebLogHealth('NFO','***                  Subnet Match: \t False')
                            _recommend.append('ERROR: Subnet %s should match with storage subnet %s for %s of %s' %(_subnet, _storage_subnet, _hostname, _host))
                            _loglist.append(_recommend[-1])
                            _err = True

            if (_err == False):
                _jsonMap['XML']['subnetMask']['TestResult'] = "Pass"
                _jsonMap['XML']['subnetMask']['subnet'] = _storage_subnet
                _jsonMap['XML']['subnetMask']['pkey'] = _storage_pkey
            else:
                _jsonMap['XML']['subnetMask']['TestResult'] = "Fail"
                _jsonMap['XML']['subnetMask']['subnet'] = _storage_subnet
                _jsonMap['XML']['subnetMask']['pkey'] = _storage_pkey
                _recommend.append("ERROR: Mismatch in SubnetMask for domUs and Cells in XML configuration")
                for i in range(len(_loglist)):
                    _jsonMap['XML']['subnetMask']['logs'][i] = _loglist[i]
                if len(_jsonMap['XML']['subnetMask']['logs']) == 0:
                    _jsonMap['XML']['subnetMask'].pop("logs", None)
        # end

        # nslookup test
        def mNslookupTest(self, aIp, aRecommend):

            _recommend = aRecommend
            _found = "False"
            _nslout = "None"

            try:
                _out = subprocess.check_output(['nslookup', aIp]).decode('utf8')
                if _out:
                    _o = _out.split('\n')
                    _nsstr = "name = "
                    for _line in _o:
                        if  _nsstr in _line:
                            _nslout = _line.strip().split('name = ')[1][:-1]
                            _found = "True"
                            break
            except:
                return "None"

            return _nslout

        #
        # Check if scan-names in XMl are resolvable.
        # Otherwise, add the corresponding domain name to /etc/resolv.conf
        #
        def mCheckScanNames(self, aEbox, aRecommend, aJsonMap):
            
            _ebox = aEbox
            _recommend = aRecommend
            _jsonMap = aJsonMap
            _jsonMap['XML']['scanName'] = {}
            _jsonMap['XML']['scanName']['logs'] = []
            _testResult = "Pass"
            ebLogHealth('NFO','\n')
            ebLogHealth('NFO','*** Check if Scan Name Resolvable ***')
            _fqdn = 'None'

            _scan_list = []
            _clusters  = _ebox.mGetClusters().mGetClusters()
            #get scan ip for clusters added in software/clusters/cluster xml
            for _cluId in _clusters:
                _cluster = _ebox.mGetClusters().mGetCluster(_cluId)
                _scan_list  += _cluster.mGetCluScans()
            
            for _sname in _scan_list:
                _scanName = _ebox.mGetScans().mGetScan(_sname).mGetScanName()
                ebLogHealth('NFO','*** scan Id:     %s' %(_sname))
                ebLogHealth('NFO','***                           scanName: \t %s' %(_scanName))
                try:
                    _, _, _out, _ = _ebox.mExecuteLocal('/bin/host %s' % (_scanName))
                    _fqdn = _out.strip().split('\n')[-1].split(' ')[-1]
                    if re.match('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', _fqdn) is None:
                        _fqdn = 'None'
                except:
                    _fqdn = 'None'

                _scanip_list   = _ebox.mGetScans().mGetScan(_sname).mGetScanIps()
                #try reverse lookup by checking ips
                try:
                    for _scanip in _scanip_list:
                        _, _, _out, _ = _ebox.mExecuteLocal('/bin/host %s' % (_scanip))
                        #check of scanName is there in reverse lookup
                        if _out and _out.find(_scanName) != -1:
                            _fqdn = _scanip
                            _recommend.append('RECOMMEND: scanName %s not resolvable, Though reverse lookup passed with ip %s' % (_scanName, _scanip))
                            _jsonMap['XML']['scanName']['logs'].append(_recommend[-1])
                            break
                except:
                    _fqdn = 'None'

                if(self.mGetPreProv() == True):
                    for _scanip in _scanip_list:
                        _cmd = '/bin/ping -c 1 -W 4 %s' % (_scanip)
                        _rc, _, _, _ = _ebox.mExecuteLocal(_cmd)
                        if not _rc:
                            #check if scanip is already up, indicates it has been used by other cluster
                            _recommend.append('WARNING: scanName %s with scanIp %s is pingable, indicating scanip used by other cluster' % (_scanName, _scanip))
                            _jsonMap['XML']['scanName']['logs'].append(_recommend[-1])
                            break
                
                ebLogHealth('NFO','***                               fqdn: \t %s' %(_fqdn))
                _jsonMap['XML']['scanName'][_sname] = {}
                _jsonMap['XML']['scanName'][_sname]['scanName'] = _scanName
                _jsonMap['XML']['scanName'][_sname]['fqdn'] = _fqdn
                if _fqdn == 'None':
                    _recommend.append('WARNING: scanName %s is not resolvable. verify /etc/resolv.conf' % _scanName)
                    _jsonMap['XML']['scanName']['logs'].append(_recommend[-1])
                    _testResult = "Fail"
            _jsonMap['XML']['scanName']['TestResult'] = _testResult
        # end check scan names

        # 
        # Check Users and Groups xml configuration
        #
        def mCheckUserandGroupXML(self, aBox, aRecommend, aJsonMap):

            _ebox = aBox
            _kvm = _ebox.mIsKVM()
            _userlist = []
            _recommend = aRecommend
            _jsonMap = aJsonMap
            _jsonMap['XML']['usersCheck'] = {}
            _jsonMap['XML']['usersCheck']['logs'] = {}
            _loglist = []
            _testResult = "Pass"

            userTypes   =   ['grid', 'oracle']
            grpTypes    =   ['OINSTALLGROUP','DBA_GROUP','OPER_GROUP','OSDBA','OSOPER','OSASM']

            # Retrieve clusterOwner User for current cluster
            # TBD: should we expect more than one cluster
            _cluster = _ebox.mGetClusters().mGetCluster()
            _clusterId = _cluster.mGetCluId()

            ebLogHealth('NFO', '\n')
            ebLogHealth('NFO','*** Validate Users and Groups listed in XML file for cluster: %s' %(_clusterId))

            #e.g. c6_grid
            _clusterOwnerId  = _cluster.mGetClusterOwner()
            _userlist.append(_clusterOwnerId)
            
            #find oracle user
            _dbHomesList = _ebox.mGetDBHomes().mGetDBHomeConfigs()
            _dbHomeConfig = None 
            for _dbHomeId in _dbHomesList:
                if (_clusterId == _dbHomeId.mGetDBClusterId()):
                    _dbHomeConfig = _dbHomeId
                    break
            #get dbhomeowener id e.g. c6_oracle
            if _dbHomeConfig is not None:
                _dbSwOwnerId =  _dbHomeConfig.mGetDBHomeOwner()
                _userlist.append(_dbSwOwnerId)

            _jsonMap['XML']['usersCheck']['userList'] = _userlist
            _usrCnt = 0
            for _userId  in _userlist:
                _jsonMap['XML']['usersCheck'][_userId] = {}
                _userConfig =  _ebox.mGetUsers().mGetUser(_userId)

                if _kvm:
                   _userName = _userConfig.mGetUserName()
                   _userType = _userConfig.mGetUserType()
                   if _userName in userTypes or _userType in userTypes:
                       _usrCnt += 1
                   else:
                       ebLogWarn('*** Expecting userType as %s for userId %s' %(userTypes[_usrCnt],_userId))
                       _recommend.append('WARNING: Expecting userType as %s for userId %s' %(userTypes[_usrCnt],_userId))
                       _loglist.append(_recommend[-1])
                else:
                    if (_userConfig.mGetUserType() == userTypes[_usrCnt]):
                        _usrCnt += 1
                    else:
                        ebLogWarn('*** Expecting userType as %s for userId %s' %(userTypes[_usrCnt],_userId))
                        _recommend.append('WARNING: Expecting userType as %s for userId %s' %(userTypes[_usrCnt],_userId))
                        _loglist.append(_recommend[-1])

                _jsonMap['XML']['usersCheck'][_userId]['userType'] = _userConfig.mGetUserType()    
                _userGroup = _userConfig.mGetUserGroups()

                _grpCnt = 0
                _jsonMap['XML']['usersCheck'][_userId]['groups'] = []
                for _grp  in _userGroup:
                    _groupConfig = _ebox.mGetGroups().mGetGroup(_grp)
                    grpType = _groupConfig.mGetGroupType()
                    _jsonMap['XML']['usersCheck'][_userId]['groups'].append("%s: %s" %(_grp,grpType))
                    if _kvm:
                        if grpType in grpTypes:
                            _grpCnt += 1
                        else:
                            ebLogWarn('*** Expecting grpType as %s for user %s with groupId %s' %(grpTypes[grpId-1],_userId, _grp))
                            _recommend.append('WARNING: Expecting grpType as %s for user %s with groupId %s' %(grpTypes[grpId-1],_userId, _grp))
                            _loglist.append(_recommend[-1])
                    else:
                        grpId = int(_grp[-1:])
                        if(grpType == grpTypes[grpId-1]):
                            _grpCnt += 1
                        else:
                            ebLogWarn('*** Expecting grpType as %s for user %s with groupId %s' %(grpTypes[grpId-1],_userId, _grp))
                            _recommend.append('WARNING: Expecting grpType as %s for user %s with groupId %s' %(grpTypes[grpId-1],_userId, _grp))
                            _loglist.append(_recommend[-1])

                #Expecting: 4 i.e.   1423 - oracle  |   1456 - grid
                if(_grpCnt != 4):
                    ebLogError('*** user %s do not have all required group permissions' %(_userId))
                    _recommend.append('ERROR: user %s do not have all required group permissions' %(_userId))
                    _loglist.append(_recommend[-1])
                    _testResult = "Fail"
                
            #Expecting:  2 oracle & grid user
            if(_usrCnt != len(userTypes)):
                    ebLogError('*** XML file does not contain required user permissions')
                    _recommend.append("ERROR: XML file does not contain required user permisions")
                    _loglist.append(_recommend[-1])
                    _testResult = "Fail"

            _jsonMap['XML']['usersCheck']['TestResult'] = _testResult
            ebLogHealth('NFO','*** Users listed in XML file: %s' %(_userlist))
            

            for i in range(len(_loglist)):
                _jsonMap['XML']['usersCheck']['logs'][i] = _loglist[i]

            if len(_jsonMap['XML']['usersCheck']['logs']) == 0:
                _jsonMap['XML']['usersCheck'].pop("logs", None)



        # 
        # Check Machine Configuration 
        #
        def mCheckMachineConfig(self, aEbox, aRecommend, aJsonMap):
            
            _ebox = aEbox
            _recommend = aRecommend
            _jsonMap = aJsonMap
            _eboxnetworks = self.mGetEboxNetworks()
            _clu_host_d = self.mGetClusterHostD()
            _loglist = []
            _testResult = "Pass"
            ebLogHealth('NFO', '\n')
            ebLogHealth('NFO','*** The nodes listed in the XML file:')
            _jsonMap['XML']['machineCheck'] = {}
            
            _machine_list  = []
            _clusters  = _ebox.mGetClusters().mGetClusters()
            #get machine details from software/clusters/cluster xml
            for _cluId in _clusters:
                _machine_list += _ebox.mGetClusters().mGetClusterMachines(_cluId)

            _mac_list = _ebox.mGetMachines()
            _ml = _mac_list.mGetMachineConfigList()
            for _mac in _machine_list:
                 # Hostname
                 _mac_hostname = _ml[_mac].mGetMacHostName()
                 # IP Address of the machine
                 _neto = None
                 _neto = _eboxnetworks.mGetNetworkConfigByName(_mac_hostname)
                 if _neto != None:
                     #in case of domu with nat support, nat hostname and nat ip should be used
                     _mac_ip = _neto.mGetNetNatAddr()
                     _mac_hostname = _neto.mGetNetNatHostName()
                     _jsonMap['XML']['machineCheck'][_mac_hostname] = {}
                     ebLogHealth('NFO','***                Machine IP Address: \t %s' %(_mac_ip))
                     _jsonMap['XML']['machineCheck'][_mac_hostname]['ipAddress'] = _mac_ip
                 else:
                     ebLogHealth('ERR', '*** Network information not found for %s. Check XML file ***' %(_mac_hostname))
                     _jsonMap['XML']['machineCheck'][_mac_hostname]['TestResult'] = "Fail"
                     continue # Possibly incorrect hostName in XML
                 ebLogHealth('NFO','Machine Hostname: %s' %(_mac_hostname))

                 _jsonMap['XML']['machineCheck'][_mac_hostname]['logs'] = {}
                 _jsonMap['XML']['machineCheck'][_mac_hostname]['hostName'] = _mac_hostname

                 if(_ml[_mac].mGetMacType() == 'compute' and _ml[_mac].mGetMacOsType() == 'LinuxGuest'):
                     _mac_vmImageName = _ml[_mac].mGetMacVMImgName()
                     _mac_vmImageVersion = _ml[_mac].mGetMacVMImgVersion()
                     _jsonMap['XML']['machineCheck'][_mac_hostname]['DomUImageName'] = _mac_vmImageName
                     ebLogHealth('NFO','***                     DomUImageName: \t %s' %(_mac_vmImageName))
                     
                     _jsonMap['XML']['machineCheck'][_mac_hostname]['ImageVersion']  = _mac_vmImageVersion
                     ebLogHealth('NFO','***                      ImageVersion: \t %s' %(_mac_vmImageVersion))

                     if (_mac_vmImageName != 'default'):
                        _recommend.append("WARNING: DomUImageName %s is not set as 'default' for Hostname %s" 
                                          %(_mac_vmImageName, _mac_hostname))
                        _loglist.append(_recommend[-1])
                     
                     if(_mac_vmImageVersion != 'default'):
                         _recommend.append("WARNING: ImageVersion %s is not set as 'default' for Hostname %s" 
                                           %(_mac_vmImageVersion, _mac_hostname))
                         _loglist.append(_recommend[-1])

                 # Type of machine - compute/storage/switch
                 _mac_type = _ml[_mac].mGetMacType()
                 ebLogHealth('NFO','***                      Machine Type: \t %s' %(_mac_type))
                 _jsonMap['XML']['machineCheck'][_mac_hostname]['machineType'] = _mac_type


                 # Check for IP address validity
                 try:
                     socket.inet_aton(_mac_ip)
                     ebLogHealth('NFO','***                  Valid IP Address: \t True')
                     _jsonMap['XML']['machineCheck'][_mac_hostname]['validIP'] = "True"
                 except socket.error:
                     ebLogHealth('NFO','***                  Valid IP Address: \t False')
                     _recommend.append("ERROR: Incorrect IP Address %s for Hostname %s" %(_mac_ip, _mac_hostname))
                     _loglist.append(_recommend[-1])
                     _jsonMap['XML']['machineCheck'][_mac_hostname]['validIP'] = "False"
                     _testResult = "Fail"

                 # Ping status
                 if _mac_hostname in _clu_host_d:
                     _clunode = _clu_host_d[_mac_hostname]
                     ebLogHealth('NFO','***                       Ping Status: \t %s' %(_clunode.mGetPingable()))

                 # nslookup status
                 _found = "False"
                 try:
                     _out = subprocess.check_output(['nslookup', _mac_ip]).decode('utf8')
                     if _out:
                         _o = _out.split('\n')
                         _nsstr = "name = "
                         _nslout = "Not found"
                         for _line in _o:
                             if  _nsstr in _line:
                                 _nslout = _line.strip().split('name = ')[1][:-1]
                                 _found = "True"
                                 break
                         ebLogHealth('NFO','***          Hostname as per nslookup: \t %s' %(_nslout))
                         _jsonMap['XML']['machineCheck'][_mac_hostname]['fqdn'] = _nslout
                         if _nslout.split('.')[0] != _mac_hostname.split('.')[0]:
                             _recommend.append("WARNING: Hostname via nslookup for %s is %s while in XML it is %s" %(_mac_ip, _nslout, _mac_hostname))
                             _loglist.append(_recommend[-1])
                             _testResult = "Fail"
                 except:
                     if _found == "False":
                         _recommend.append("WARNING: nslookup failed for IP Address %s" %(_mac_ip))
                         _loglist.append(_recommend[-1])
                         _testResult = "Fail"

                 _jsonMap['XML']['machineCheck'][_mac_hostname]['TestResult'] = _testResult

                 for i in range(len(_loglist)):
                     _jsonMap['XML']['machineCheck'][_mac_hostname]['logs'][i] = _loglist[i]

                 if len(_jsonMap['XML']['machineCheck'][_mac_hostname]['logs']) == 0:
                     _jsonMap['XML']['machineCheck'][_mac_hostname].pop("logs", None)
            
            
        # end mCheckMachineConfig

        #
        # Check Network Configuration
        #
        def mCheckNetworksXml(self, aEbox, aRecommend, aJsonMap):

            _ebox = aEbox
            _kvm = _ebox.mIsKVM()
            _recommend = aRecommend
            _jsonMap = aJsonMap
            _loglist = []
            _testResult = "Pass"
            ebLogHealth('NFO', '\n')
            ebLogHealth('NFO','*** The networks listed in the XML file:')
            _jsonMap['XML']['networkCheck'] = {}
            _jsonMap['XML']['networkCheck']['logs'] = []

            _ipList = []

            for _, _domU in aEbox.mReturnDom0DomUPair():
                _domU_mac = aEbox.mGetMachines().mGetMachineConfig(_domU)
                _domU_net_list = _domU_mac.mGetMacNetworks()
                for _net in _domU_net_list:
                    _net_obj = aEbox.mGetNetworks().mGetNetworkConfig(_net)

                    _jsonMap['XML']['networkCheck'][_net] = {}
                    _jsonMap['XML']['networkCheck'][_net]['netId'] = _net_obj.mGetNetId()
                    _jsonMap['XML']['networkCheck'][_net]['netName'] = _net_obj.mGetNetName()
                    _jsonMap['XML']['networkCheck'][_net]['netType'] = _net_obj.mGetNetType()
                    _jsonMap['XML']['networkCheck'][_net]['netHostName'] = _net_obj.mGetNetHostName()
                    _jsonMap['XML']['networkCheck'][_net]['netDomainName'] = _net_obj.mGetNetDomainName()
                    _jsonMap['XML']['networkCheck'][_net]['netIpAddr'] = _net_obj.mGetNetIpAddr()
                    _jsonMap['XML']['networkCheck'][_net]['netNatHostName'] = _net_obj.mGetNetNatHostName(aFallBack=False)
                    _jsonMap['XML']['networkCheck'][_net]['netNatDomainName'] = _net_obj.mGetNetNatDomainName()
                    _jsonMap['XML']['networkCheck'][_net]['netNatIpAddr'] = _net_obj.mGetNetNatAddr(aFallBack=False)

                    _ipList.append(_net_obj.mGetNetIpAddr())

                    if _net_obj.mGetNetNatAddr(aFallBack=False):
                        _ipList.append(_net_obj.mGetNetNatAddr(aFallBack=False))

            _ipList = sorted(_ipList)
            _uniqIps = list(sorted(set(_ipList)))

            if _ipList == _uniqIps:
                ebLogHealth('NFO','*** Valid network information, only unique ips: \t True')
                _jsonMap['XML']['networkCheck']['TestResult'] = "Pass"
            else:

                ebLogHealth('NFO','*** Invalid network information, ips duplicated')
                for _uniqIp in _uniqIps:
                    _count = _ipList.count(_uniqIp)
                    if _count >= 2:
                        ebLogHealth('NFO',f'*** Duplicated IP: {_uniqIp}')

                _jsonMap['XML']['networkCheck']['logs'].append(_recommend[-1])
                _jsonMap['XML']['networkCheck']['TestResult'] = "Fail"


        # 
        # Check Machine Configuration 
        #
        def mCheckDiskGroup(self, aEbox, aRecommend, aJsonMap):
            
            _ebox = aEbox
            _kvm = _ebox.mIsKVM()
            _recommend = aRecommend
            _jsonMap = aJsonMap
            _loglist = []
            _testResult = "Pass"
            ebLogHealth('NFO', '\n')
            ebLogHealth('NFO','*** The diskGroups listed in the XML file:')
            _jsonMap['XML']['diskgroupCheck'] = {}
            _jsonMap['XML']['diskgroupCheck']['logs'] = []

            #
            # Fetch ClusterID
            #
            _cluster = _ebox.mGetClusters().mGetCluster()
            ebLogHealth('NFO','***                         cluster ID: \t %s' %(_cluster.mGetCluId()))
            _jsonMap['XML']['diskgroupCheck']['clusterID'] = _cluster.mGetCluId()

            _dgl = _cluster.mGetCluDiskGroups()
            for _dg in _dgl:
                _dgc = _ebox.mGetStorage().mGetDiskGroupConfig(_dg)
                _dg_id = _dgc.mGetDgId()
                _dg_name = _dgc.mGetDgName()
                _dg_slsz = _dgc.mGetSliceSize()
                _dg_dgsz = _dgc.mGetDiskGroupSize()

                _jsonMap['XML']['diskgroupCheck'][_dg] = {}
                _jsonMap['XML']['diskgroupCheck'][_dg]['dgId'] = _dg_id
                _jsonMap['XML']['diskgroupCheck'][_dg]['dgName'] = _dg_name
                _jsonMap['XML']['diskgroupCheck'][_dg]['dgSliceSize'] = _dg_slsz
                _jsonMap['XML']['diskgroupCheck'][_dg]['dgGroupSize'] = _dg_dgsz

                ebLogHealth('NFO','          Disk Group ID: %s' %(_dg_id))
                ebLogHealth('NFO','***                   Disk Group Name: \t %s' %(_dg_name))

                # verify disk group naming convention
                # NAMECX where the DG ends with CX and X equals to the cluster id. e.g. DBFSC1, RECOC2.
                # not checking for ACFS, as it has been asigned at runtime with ACFSC1_DG1/DG2
                _dg_name_pattern = re.compile("^(DBFS|DATA|RECO|SPR)C(\d+)$")
                _dg_match = _dg_name_pattern.match(_dg_name)
                #fetch cluster id, subtracted by -1 as dg id starts with 1 while cluster id starting with 0
                if _kvm:
                    if _dg_match is not None:
                        ebLogHealth('NFO','***             Valid Disk Group Name: \t True')
                        _jsonMap['XML']['diskgroupCheck'][_dg]['TestResult'] = "Pass"
                    else:
                        _testResult = "Fail"
                        ebLogHealth('NFO','***             Valid Disk Group Name: \t False')
                        _recommend.append("ERROR: Invalid Disk Group Name %s" %(_dg_name))
                        _jsonMap['XML']['diskgroupCheck']['logs'].append(_recommend[-1])
                        _jsonMap['XML']['diskgroupCheck'][_dg]['TestResult'] = "Fail"
                else:
                    _cluId = int(_cluster.mGetCluId().split('_')[0][1:])
                    if _dg_match is not None and (int(_dg_match.group(2)) - 1) == _cluId:
                        ebLogHealth('NFO','***             Valid Disk Group Name: \t True')
                        _jsonMap['XML']['diskgroupCheck'][_dg]['TestResult'] = "Pass"
                    else:
                        _testResult = "Fail"
                        ebLogHealth('NFO','***             Valid Disk Group Name: \t False')
                        _recommend.append("ERROR: Invalid Disk Group Name %s" %(_dg_name))
                        _jsonMap['XML']['diskgroupCheck']['logs'].append(_recommend[-1])
                        _jsonMap['XML']['diskgroupCheck'][_dg]['TestResult'] = "Fail"

                ebLogHealth('NFO','***             Disk Group Slice Size: \t %s' %(_dg_slsz))
                ebLogHealth('NFO','***                   Disk Group Size: \t %s' %(_dg_dgsz))

            _jsonMap['XML']['diskgroupCheck']['TestResult'] = _testResult

        # end mCheckDiskGroup

        #
        # Validate the exabox.conf file
        #
        def mValidateConf(self):

            # Exabox config related
            _oedahost  = None
            _vmdetails = None
            _vmsize    = None
            _vmcpu     = None
            _vmdisk    = None
            _logincred = None
            _oedauser  = None
            _oedapwd   = None
            _cellshred = None
            _shredpass = None

            _recommend = self.mGetRecommend()
            _clu_host_d = self.mGetClusterHostD()
            _clu_health_d = self.mGetClusterHealthD()
            _exaconfig = self.mGetExaConfig()

            _log_destination = ebLogSetHCLogDestination(self.mGetLogHandler(), True)

            _jsonHandler = self.mGetJsonHandler()
            _jsonResult = self.mGetJsonResult()
            _jsonMap = self.mGetJsonMap()
            _jsonMap['Conf'] = {}
            _jsonMap['Conf']['exaBox'] = {}
            _jsonMap['Conf']['exaBox']['logs'] = []

            ebLogInfo('*** Validating exabox.conf file ***\n')
            ebLogHealth('NFO', '\n')
            ebLogHealth('NFO', '*** Exacloud Configuration Details ***\n')

            if 'default_vmsize' in _exaconfig.keys():
                _vmdetails =  _exaconfig['default_vmsize']
                if "MemSize" in _vmdetails:
                    _vmsize = _vmdetails["MemSize"]
                if "cpuCount" in _vmdetails:
                    _vmcpu  = _vmdetails["cpuCount"]
                if "DiskSize" in _vmdetails:
                    _vmdisk = _vmdetails["DiskSize"]

                self.mSetVmmem(_vmsize)

            if 'oeda_host' in _exaconfig.keys():
                _oedahost = _exaconfig['oeda_host'] 

            if 'login_credentials' in _exaconfig.keys():
                _logincred = _exaconfig['login_credentials']
                if _oedahost in _logincred.keys():
                    _oedauser = _logincred[_oedahost][0]
                    _oedapwd  = _logincred[_oedahost][1]
                    if _oedapwd != "":
                        _recommend.append("RECOMMENDATION: OEDA host password found in config file. Make sure host is setup for password-less ssh")
                        _jsonMap['Conf']['exaBox']['logs'].append(_recommend[-1])

            if 'shredding_enabled' in _exaconfig.keys():
                _cellshred = _exaconfig['shredding_enabled']

            if 'cellerase_pass' in _exaconfig.keys():
                _shredpass = _exaconfig['cellerase_pass']

            if (_cellshred is not None) and (_shredpass is not None):
                if (_cellshred.lower() == "true") and (_shredpass.lower() != "0pass"):
                    _recommend.append("WARNING: Cell & VM Image shredding is set to %s. Delete service can take a very long time" %(_shredpass))
                    _jsonMap['Conf']['exaBox']['logs'].append(_recommend[-1])

            ebLogHealth('NFO','***                   Default VM Size: \t %s' %(_vmsize))
            ebLogHealth('NFO','***              Default VM CPU Count: \t %s' %(_vmcpu))
            ebLogHealth('NFO','***              Default VM Disk Size: \t %s' %(_vmdisk))
            ebLogHealth('NFO','***                         OEDA Host: \t %s' %(_oedahost))
            ebLogHealth('NFO','***                     OEDA Username: \t %s' %(_oedauser))
            ebLogHealth('NFO','***                     OEDA Password: \t %s' %(_oedapwd))
            ebLogHealth('NFO','***            Cell Shredding Enabled: \t %s' %(_cellshred))
            ebLogHealth('NFO','***             Cell Erase Iterations: \t %s' %(_shredpass))

            _jsonMap['Conf']['exaBox']['vmSize'] = _vmsize
            _jsonMap['Conf']['exaBox']['vmCpuCount'] = _vmcpu
            _jsonMap['Conf']['exaBox']['vmDisk'] = _vmdisk
            _jsonMap['Conf']['exaBox']['oedaHost'] = _oedahost
            _jsonMap['Conf']['exaBox']['oedaUser'] = _oedauser
            _jsonMap['Conf']['exaBox']['oedaPwd'] = _oedapwd
            _jsonMap['Conf']['exaBox']['cellShredEnable'] = _cellshred
            _jsonMap['Conf']['exaBox']['cellShredPass'] = _shredpass

            # In other tests, below will be conditional
            _jsonMap['Conf']['exaBox']['TestResult'] = "Pass"

            if len(_jsonMap['Conf']['exaBox']['logs']) == 0:
                _jsonMap['Conf']['exaBox'].pop("logs", None)

            ebLogInfo('*** Completed exabox.conf validation\n')
            ebLogRemoveHCLogDestination(_log_destination)
            ebLogSetHCLogDestination(self.mGetDefaultLogHandler())

        def mGetDomUList(self, aBox):
            _eBox = aBox
            _domU_list = []
            _cname = _eBox.mGetClusters().mGetClusters()
            _cnode = _eBox.mGetClusters().mGetCluster(_cname[0])
            _vip_list = _cnode.mGetCluVips()
            for _vip in list(_vip_list.keys()):
                _vip_name = _vip_list[_vip].mGetCVIPMachines()[0]
                _mac_config = _eBox.mGetMachines().mGetMachineConfig(_vip_name)
                _mac_name   = _mac_config.mGetMacHostName()
                _domU_list.append(_mac_name)
            return _domU_list

        def mValidateNwOverlap(self, aBox, aRecommend, aJsonMap):

            _eBox = aBox
            _recommend = aRecommend
            _jsonMap = aJsonMap
            _jsonMap['XML']['nwOverlap'] = {}
            _jsonMap['XML']['nwOverlap']['logs'] = {}
            _loglist = []
            _testResult = "Pass"
            _nwTypes = ['admin', 'backup', 'client', 'Ilom']
            _nwIntfList = []

            _cluster_host_d = self.mGetClusterHostD()
            _eBoxNetworks = _eBox.mGetNetworks()

            ebLogHealth('NFO', '\n')
            ebLogHealth('NFO', '*** Check for network overlapping ***\n')

            _domU_list = self.mGetDomUList(_eBox)

            for _host in _cluster_host_d.keys():
                _clunode = _cluster_host_d[_host]
                if _clunode.mGetNodeType() == 'switch':
                    continue
                if _clunode.mGetNodeType() == 'domu' and (_eBox.mIsExabm() or _eBox.mIsOciEXACC()):
                    _host = _domU_list.pop(0)
                _host_mac = _eBox.mGetMachines().mGetMachineConfig(_host)
                _nwIntfList += _host_mac.mGetMacNetworks()

            #add all ilom nw ids for dom0, cells
            _ilomCfg = _eBox.mGetIloms()
            _nwIntfList += _ilomCfg.mGetIlomsNetworkId()

            #add admin interface for switches
            _switchCfg = _eBox.mGetSwitches()
            for _switchId in _switchCfg.mGetSwitchesList():
                _nwIntfList.append(_switchCfg.mGetSwitchConfig(_switchId).mGetSwitchNetworkId())
            
            #no_of_dom0*2(admin+ilom)* + no_of_domu*3(admin+backup+client) + no_of_cell*2(admin + ilom) + no_of_switch*1(admin)
            #for QR:  #2*2 + 2*3 + 3*2 + 3*1 = 19
            _gwlist = []
            for _nwId in _nwIntfList:
                _nwConfig   = _eBoxNetworks.mGetNetworkConfig(_nwId)
                if _nwConfig.mGetNetType() not in _nwTypes:
                    continue

                _ip         = _nwConfig.mGetNetIpAddr()
                _netName    = _nwConfig.mGetNetName()
                _netMask    = _nwConfig.mGetNetMask()
                _netType    = _nwConfig.mGetNetType()
                _gw         = _nwConfig.mGetNetGateWay()
                _intf       = _nwConfig.mGetNetMaster()

                if _gw == 'UNDEFINED':
                    ebLogInfo('gateway UNDEFINED, taking default mac gateway ')
                    _loglist.append('gateway UNDEFINED, taking default mac gateway ')
                    _gw = _eBox.mGetMachines().mGetMacGateWay()

                #PingTest/ArpTest for gateway
                if _eBox.mIsOciEXACC():
                    if (_gw not in _gwlist) and  (not _eBox.mArpingHost(_intf, _gw)):
                        _gwlist.append(_gw)
                        _recommend.append("ERROR: Unable to connect to the IP Address (%s) listed as a gateway in XML." %(_gw))
                        _loglist.append(_recommend[-1])
                        _testResult = "Fail"
                else:
                    if (_gw not in _gwlist) and  (not _eBox.mPingHost(_gw)):
                        _gwlist.append(_gw)
                        _recommend.append("ERROR: Unable to connect to the IP Address (%s) listed as a gateway in XML." %(_gw))
                        _loglist.append(_recommend[-1])
                        _testResult = "Fail"

                # BUG 33979523 - Remove the Network and Gateway Subnet validation for Admin networks
                if _netType == 'admin':
                    continue

                _subnetIp = self.mGetSubnet(_ip, _netMask)
                _subnetGw = self.mGetSubnet(_gw, _netMask)
                _jsonMap['XML']['nwOverlap'][_netName] = {}

                ebLogHealth('NFO','***                       netName: \t %s' %(_netName))
                ebLogHealth('NFO','***                       ipAddr  : \t %s' %(_ip))
                ebLogHealth('NFO','***                       netmask : \t %s' %(_netMask))
                ebLogHealth('NFO','***                       gw      : \t %s' %(_gw))
                _jsonMap['XML']['nwOverlap'][_netName] = {}
                _jsonMap['XML']['nwOverlap'][_netName]['ipAddress']   = _ip
                _jsonMap['XML']['nwOverlap'][_netName]['netMask']     = _netMask
                _jsonMap['XML']['nwOverlap'][_netName]['gw']          = _gw

                #compare subnet for ip/netmask and gateway/netmask 
                if(_subnetIp == _subnetGw):
                    ebLogHealth('NFO','***                       subnet  : \t %s' %(_subnetIp))
                    _jsonMap['XML']['nwOverlap'][_netName]['subnet']      = _subnetIp
                    _jsonMap['XML']['nwOverlap'][_netName]['TestResult'] = "Pass"
                    ebLogHealth('NFO','***                  Subnet Match: \t True')
                else:
                    ebLogWarn('*** ip %s and gw %s should be on same subnet for nw interface %s' %(_ip, _gw, _netName))
                    _recommend.append('WARNING: ip %s and gw %s should be on same subnet for nw interface %s' %(_ip, _gw, _netName))
                    _loglist.append(_recommend[-1])
                    _testResult = "Fail"
                    _jsonMap['XML']['nwOverlap'][_netName]['TestResult'] = "Fail"
                    ebLogHealth('NFO','***                       ipSubnet: \t %s' %(_subnetIp))
                    ebLogHealth('NFO','***                       gwSubnet: \t %s' %(_subnetGw))
                    _jsonMap['XML']['nwOverlap'][_netName]['ipSubnet']      = _subnetIp
                    _jsonMap['XML']['nwOverlap'][_netName]['gwSubnet']      = _subnetGw
                    ebLogHealth('NFO','***                  Subnet Match: \t False')
        
            _jsonMap['XML']['nwOverlap']['TestResult'] = _testResult

            for i in range(len(_loglist)):
                _jsonMap['XML']['nwOverlap']['logs'][i] = _loglist[i]

            if len(_jsonMap['XML']['nwOverlap']['logs']) == 0:
                _jsonMap['XML']['nwOverlap'].pop("logs", None)
