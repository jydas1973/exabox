"""
 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    OVM - Healthcheck functionality

FUNCTION:
    Provide basic healthcheck functionality

NOTE:
    None

History:

    MODIFIED   (MM/DD/YY)
    rkhemcha    04/15/25   - 37819843, 37812793 - Add precheck for received
                             network info, send dummy report to ECRA for
                             internal errors
    rkhemcha    09/20/24   - 35979312,35594098 - Network validation changes for
                             selective testing during network reconfiguration
    aypaul      07/29/24   - Bug#36887651 Extend timeout for healthcheck.
    rkhemcha    06/12/24   - 36721648 - Network validation to have network
                             object name in corresponding report/logs
    rkhemcha    02/01/24   - 36251119 - Fix network validation for backup net
                             reconfig with dr network
    rkhemcha    02/05/23   - 34715457 - Changes to support validation for 3rd
                             network
    rkhemcha    09/15/22   - 34508043 - Changes for enabling re-validation for
                             validated nw objects
    rkhemcha    07/14/22   - 34383909 - Add methods to retrieve dom0 network
                             info
    rkhemcha    04/07/22   - 33922918 - Network Validation changes to support
                             network reconfiguration
    hnvenkat    11/12/2020 - Bug 32119916: Remove sort_keys=True for Python3 compliance
    bhuvnkum    11/24/2017 - Bug 27143491: validate scanip down before provisioning
    bhuvnkum    11/24/2017 - Bug 27143661: validate default gw on admin nw
    dekuckre    11/22/2017 - Bug 27082067: Populate the list of hosts in ebCluHealth.
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
       5) Add a RECOMMENDs/warnings section to hc report
       6) Warn if MemSize under vm_size in exabox.conf is > dom0 MemTotal
       7) Recommend change of password for every node that has 'weak' pwd

   10/20/2015 - v1 changes:
       1) Basic check functionality
       2) SSH working yes/no
       3) Password less SSH
       4) Strength of root password for various nodes
       5) Network interfaces on Dom0 that are active
"""
import six
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogVerbose, ebLogSetHCLogDestination, \
    ebLogRemoveHCLogDestination, ebLogHealth, ebLogTrace
from exabox.log.LogMgr import ebLogJson
from exabox.ovm.vmconfig import exaBoxClusterConfig
import os, sys, subprocess, uuid, time, os.path, traceback
from subprocess import Popen, PIPE
import xml.etree.cElementTree as etree
from exabox.core.Context import get_gcontext
from exabox.core.Core import exaBoxCoreInit
from exabox.ovm.vmcontrol import exaBoxOVMCtrl
from exabox.ovm.clumisc import ebCluSshSetup, ebCluPreChecks
from tempfile import NamedTemporaryFile
from time import sleep
from datetime import datetime
from base64 import b64decode
import hashlib
import re, random
import json, copy, socket
import zipfile
from exabox.tools.scripts import ebScriptsEngineFetch
from exabox.core.DBStore import ebGetDefaultDB
from multiprocessing import Process
from exabox.ovm.monitor import ebClusterNode
import threading
from exabox.ovm.cluconncheck import ebCluConnectivityCheck

from exabox.healthcheck.hcconstants import HcConstants, LOG_TYPE, CHK_RESULT
from exabox.healthcheck.check_parser import CheckParser
from exabox.healthcheck.check_executor import CheckExecutor
from exabox.healthcheck.profile_parser import ProfileParser

from exabox.healthcheck.clucheck import ebCluCheck
from exabox.healthcheck.hclogger import get_logger, init_logging
from exabox.healthcheck.hcutil import mReadConfigFile
from exabox.core.Error import ExacloudRuntimeError

# Configurable config file relative path
HEALTHCHECK_DICT = {}
HEALTHCHECK_DICT['healthcheck'] = '/config/healthcheck.conf'
HEALTHCHECK_DICT['master_checklist'] = '/config/hc_master_checklist.conf'
HEALTHCHECK_DICT['default_profile'] = '/hcprofile/hc_default_profile.prf'

# added to provide backward compatibility for earlier defined hc options
HEALTHCHECK_DICT['connection'] = '/hcprofile/hc_connection.prf'
HEALTHCHECK_DICT['xml'] = '/hcprofile/hc_xml.prf'
HEALTHCHECK_DICT['conf'] = '/hcprofile/hc_conf.prf'
HEALTHCHECK_DICT['stresstest'] = '/hcprofile/hc_stresstest.prf'
HEALTHCHECK_DICT['preprov'] = '/hcprofile/hc_preprov.prf'
HEALTHCHECK_DICT['postprov'] = '/hcprofile/hc_postprov.prf'
HEALTHCHECK_DICT['all'] = '/hcprofile/hc_all.prf'
HEALTHCHECK_DICT['cluster'] = '/hcprofile/hc_cluster.prf'
HEALTHCHECK_DICT['exachk'] = '/hcprofile/hc_exachk.prf'

# adding list of supported networks for network validation
SUPPORTED_NETWORKS = [HcConstants.CLIENT, HcConstants.BACKUP, HcConstants.DR]

INTERNAL_ERROR_REPORT = {
    "hcDisplayString": {
        "Network_Validation": ["Internal Error. Please try again, if issue persists please contact Oracle support."]
    }
}

# TBD
# HEALTHCHECK_DICT['tags_checklist'] =    '/config/tags_checklist.conf'
# HEALTHCHECK_DICT['profile_checklist'] = '/config/profile_checklist.conf'

class ebCluHealth(object):

    def __init__(self, aExaBoxCluCtrl, aOptions):

        self.__config = get_gcontext().mGetConfigOptions()
        self.__basepath = get_gcontext().mGetBasePath()
        self.__confpath = self.__basepath + "/config/healthcheck.conf"
        self.__clusterpath = None
        self.__xmlpath = aOptions.configpath
        self.__ebox = aExaBoxCluCtrl
        self.__recommend = []
        self.__datetime = None
        self.__dom0s = {}
        self.__domus = {}
        self.__cells = {}
        self.__switches = {}
        self.__drNet = False
        self.__runningVMs = False
        self.__reNetValidation = False
        self.__reconfiguration = False
        self.__deltaNetValidation = False
        self.__datetime = datetime.now().strftime('%m%d%y_%H%M%S')
        self.__resultdir = self.__basepath + "/log/checkcluster/" + aExaBoxCluCtrl.mGetUUID() + "/"
        self.__loghandler = None
        self.__recohandler = None
        self.__jsonhandler = None
        self.__jsonreshandler = None
        self.__preChecksPass = True

        # create healthcheck dir, if running healthcheck first time
        try:
            os.stat(self.__resultdir)
        except:
            os.makedirs(self.__resultdir)

        # objects of classes used for test-based execution
        self.__profile_parser = None
        self.__check_executor = None
        self.__check_parser = None

        # dictionary used for identifying if this is an update network operation
        self.__updateNetwork = {}

        # dictionary used for identifying network info for dom0's
        self._dom0Networks = {}

        self.__hcconfig = self.mReadHcConfig()
        if self.__hcconfig is None:
            ebLogWarn('*** Healthcheck Config file not found:' + self.__confpath)

        def _initHCLogger():

            self.__defloghandler = "healthcheck.log"
            self.__jsonresult = []
            self.__jsonmap = {}
            init_logging(self.mGetEbox(), self)
            get_logger().UpdateHcLogger(self)

            _rackstr = aExaBoxCluCtrl.mGetClusterName()
            self.mSetLogPaths(aOptions, _rackstr)
            self.__tmp_log_destination = ebLogSetHCLogDestination(self.mGetLogHandler(), True)

        _initHCLogger()

    def mSetLogPaths(self, aOptions, clusterName):
        # name result files according to network object name if flow is network validation.
        if self.mCheckIfNetworkValidation(aOptions):
            if aOptions.jsonconf['network'].get('network_name'):
                clusterName = aOptions.jsonconf['network'].get('network_name')

        self.__loghandler = self.__ebox.mGetUUID() + "/" + "healthcheck-" + clusterName + "-" + self.mGetDateTime() + ".log"
        self.__recohandler = self.mGetLogHandler().split(".")[0] + ".tmp"
        self.__jsonreshandler = self.__resultdir + "hc_" + clusterName + "_" + self.mGetDateTime() + "_healthcheck.json"

        if self.mCheckIfNetworkValidation(aOptions):
            self.__jsonhandler = (self.__basepath + "/log/checkcluster/" +
                                  self.__ebox.mGetUUID() + "-healthcheck-" + clusterName + ".json")
        else:
            self.__jsonhandler = (self.__basepath + "/log/checkcluster/" +
                                  "healthcheck-" + clusterName + "-" + self.mGetDateTime() + ".json")

    def mCheckIfNetworkValidation(self, aOptions):
        if hasattr(aOptions, 'jsonconf'):
            jsonconf = aOptions.jsonconf
            if (jsonconf and
                    jsonconf.get("profile_type") in ["custnet_validate", "custnet_revalidate", "nw_vldn_testsuite"] and
                    jsonconf.get("network")):
                return True
        return False

    def mGetCheckParser(self):
        return self.__check_parser

    def mGetProfileParser(self):
        return self.__profile_parser

    def mGetResultLevel(self):
        return self.mGetProfileParser().mGetResultLevel()

    def mGetCustomCheckList(self):
        return self.mGetProfileParser().mGetCustomCheckList()

    def mGetCheckExecutor(self):
        return self.__check_executor

    def mGetCheckList(self):
        return self.__checklist

    def mGetRecommend(self):
        return self.__recommend

    def mGetDateTime(self):
        return self.__datetime

    def mGetJsonResult(self):
        return self.__jsonresult

    def mGetJsonMap(self):
        return self.__jsonmap

    def mGetExaConfig(self):
        return self.__config

    def mGetHcConfig(self):
        return self.__hcconfig

    def mGetLogHandler(self):
        return self.__loghandler

    def mGetRecoHandler(self):
        return self.__recohandler

    def mGetDefaultLogHandler(self):
        return self.__defloghandler

    def mGetJsonHandler(self):
        return self.__jsonhandler

    def mGetJsonResHandler(self):
        return self.__jsonreshandler

    def mGetEbox(self):
        return self.__ebox

    def mGetBoxClusterPath(self):
        return self.__clusterpath

    def mGetXMLPath(self):
        return self.__xmlpath

    def mGetDom0s(self):
        return self.__dom0s

    def mGetDomUs(self):
        return self.__domus

    def mGetCells(self):
        return self.__cells

    def mGetSwitches(self):
        return self.__switches

    def mGetResultDir(self):
        return self.__resultdir

    def mGetDeltaNetValidation(self):
        return self.__deltaNetValidation

    def mGetReNetValidation(self):
        return self.__reNetValidation

    def mGetReconfiguration(self):
        return self.__reconfiguration

    def mGetUpdateNetwork(self):
        return self.__updateNetwork

    def mGetAnyRunningVMs(self):
        return self.__runningVMs

    def mGetDom0Networks(self, dom0=None):
        if dom0:
            return self._dom0Networks[dom0]

        return self._dom0Networks

    def mGetDrNetConfigured(self):
        return self.__drNet

    def mGetPreChecksStatus(self):
        return self.__preChecksPass

    def mSetPreChecksStatus(self, bool):
        self.__preChecksPass = bool

    def mSetDom0s(self, aDom0s):
        self.__dom0s = aDom0s

    def mSetDomUs(self, aDomUs):
        self.__domus = aDomUs

    def mSetCells(self, aCells):
        self.__cells = aCells

    def mSetSwitches(self, aSwitches):
        self.__switches = aSwitches

    def mSetDeltaNetValidation(self, aBool):
        self.__deltaNetValidation = aBool

    def mSetReNetValidation(self, aBool):
        self.__reNetValidation = aBool

    def mSetReconfiguration(self, aBool):
        self.__reconfiguration = aBool

    def mSetAnyRunningVMs(self, aBool):
        self.__runningVMs = aBool

    def mSetUpdateNetwork(self, dom0, networkType=None, aBool=False, properties=None):
        # default initialisation
        if self.__updateNetwork.get(dom0) is None:
            self.__updateNetwork[dom0] = {}
            for network in SUPPORTED_NETWORKS:
                self.__updateNetwork[dom0][network] = {
                    "isReconfiguring": False,
                    "updateProperties": None
                }
        else:
            self.__updateNetwork[dom0][networkType]["isReconfiguring"] = aBool
            if properties:
                self.__updateNetwork[dom0][networkType]["updateProperties"] = properties

    def mSetUpdateNetworkServices(self, service=None, aBool=False):
        # default initialisation
        if self.__updateNetwork.get("networkServices") is None:
            self.__updateNetwork.update({"networkServices": {"dns": False, "ntp": False}})
        else:
            self.__updateNetwork["networkServices"][service] = aBool

    def mSetDom0Networks(self, dom0_list):
        for dom0 in dom0_list:
            self._dom0Networks[dom0] = self.__ebox.mGetNetworkSetupInformation("all", dom0)

    def mSetDrNetConfigured(self, aBool):
        self.__drNet = aBool

    def mReadHcConfig(self):
        _cf = None
        try:
            _cf = json.load(open(self.__confpath))
        except:
            ebLogError('*** Could not access/read healthcheck.conf file')
            return {}
        return _cf

    def mUpdateHcConfig(self):
        """
        update global healthcheck conf params by profile params
        """
        _profileHcConf = self.mGetProfileParser().mGetHcConf()
        _hcConf = self.mGetHcConfig()

        for k, v in six.iteritems(_profileHcConf):
            if k in _hcConf.keys():
                _hcConf[k] = v
            else:
                ebLogError("*** Updating Healthcheck conf params from profile, key %s not found" % (k))

    def mDoHealthCheck(self, aOptions, aIncident=False):

        _LogHandler = self.mGetLogHandler()
        _defaultLogHandler = self.mGetDefaultLogHandler()
        _jsonHandler = self.mGetJsonHandler()
        # Setup the JSON object for returning results
        _jsonResult = self.mGetJsonResult()
        _deltaNetDom0s = []
        _jconf = aOptions.jsonconf
        _logger = get_logger()
        _eBox = self.mGetEbox()
        _jsonMap = self.mGetJsonMap()
        _recommend = self.mGetRecommend()

        _dom0s, _domUs, _cells, _ = _eBox.mReturnAllClusterHosts()

        # Code to take validation profile, if healthcheck is for network validation
        if _jconf and 'profile_type' in _jconf.keys():
            _profilePath = self.__basepath + '/hcprofile/hc_' + _jconf['profile_type'] + '.prf'

            # skip tests based on which network needs to be updated
            if 'updateNetwork' in _jconf.keys():
                self.mSetReconfiguration(True)

                # Set all dom0s and domUs as the target from XML
                _dom0s, _domUs = [], []
                __dom0domUpairs = _eBox.mReturnDom0DomUPair()
                for pair in __dom0domUpairs:
                    _dom0s.append(pair[0])
                    _domUs.append(pair[1])

                # Set default value for reconfiguration of all networkServices to False
                self.mSetUpdateNetworkServices()
                # if updateNetwork operation, check if the passed payload contains delta info for every dom0
                if _dom0s.__len__() == _jconf['updateNetwork']['nodes'].__len__():
                    for (_dom0, _domuNewPayload) in zip(_dom0s, _jconf['updateNetwork']['nodes']):
                        # Set default value for reconfiguration of all network types to False
                        self.mSetUpdateNetwork(_dom0)
                        for net in SUPPORTED_NETWORKS:
                            if _domuNewPayload.get(net):
                                if _domuNewPayload.get('updateProperties'):
                                    self.mSetUpdateNetwork(_dom0, net, True,
                                                           properties=_domuNewPayload.get('updateProperties').get(net))
                                else:
                                    self.mSetUpdateNetwork(_dom0, net, True)

                    # check for update to DNS/NTP servers
                    for servicePayload in _jconf['updateNetwork']['networkServices']:
                        self.mSetUpdateNetworkServices(servicePayload.get('op')[:3], True)
                else:
                    msg = ("Nodes information in the updateNetwork section of the payload does not match the number of dom0s. "
                           "Please check the payload and try again. Exiting healthcheck.")
                    _logger.mAppendLog(LOG_TYPE.ERROR, msg)
                    _jsonMap.update(INTERNAL_ERROR_REPORT)
                    self.mSetPreChecksStatus(False)

            # New section for re-network validation post bonding mode change
            if _jconf and 're-validation' in _jconf.keys() and _jconf.get('re-validation') is True:
                self.mSetReNetValidation(True)
                dom0domUInfo = _jconf.get('dom0domUMapping')
                if not dom0domUInfo:
                    msg = "Missing required dom0-domU mapping for re-validation flow of network object."
                    _logger.mAppendLog(LOG_TYPE.ERROR, msg)
                    _jsonMap.update(INTERNAL_ERROR_REPORT)
                    self.mSetPreChecksStatus(False)

                # reset the hosts for healthcheck and set according to the payload received
                _dom0s, _domUs = [], []

                for _nodeInfo in dom0domUInfo:
                    # for dom0s with running VM, validation needs to happen inside domU
                    if _nodeInfo.get('guest_state') in ['RUNNING']:
                        self.mSetAnyRunningVMs(True)
                        _domUs.append(_nodeInfo['guest_name'])
                    else:
                        _dom0s.append(_nodeInfo['host_FQDN'])

            # If this is an Elastic scenario, set the dom0's accordingly
            if 'newdom0_list' in _jconf.keys() and len(_jconf['newdom0_list']) > 0:
                _deltaNetDom0s = _jconf['newdom0_list']
                if 'False' in (' '.join([elem if type(elem) == str else 'False' for elem in _deltaNetDom0s])):
                    msg = f"Params are not valid. New DomO list given for validation is not proper: {_deltaNetDom0s}"
                    _logger.mAppendLog(LOG_TYPE.ERROR, msg)
                    _jsonMap.update(INTERNAL_ERROR_REPORT)
                    self.mSetPreChecksStatus(False)

                self.mSetDeltaNetValidation(True)
                _dom0s = _deltaNetDom0s

            # create dictionary with dom0 network info
            self.mSetDom0Networks(_dom0s)

            # set flag if dr network details in payload
            if _jconf.get("network") and _jconf["network"].get("drScan"):
                self.mSetDrNetConfigured(True)

            # validate if network info was correctly identified for all dom0's
            for _dom0, _dom0_network in self.mGetDom0Networks().items():
                # check for either client and backup network details in the received network info
                # or ERROR in case network discovery fails (X9 and above)
                _netChecklist = [HcConstants.CLIENT, HcConstants.BACKUP]
                if self.mGetDrNetConfigured():
                    _netChecklist.append(HcConstants.DR)

                if any(item not in _dom0_network for item in _netChecklist):
                    # If there is missing network info, we expect ERROR info
                    if "ERROR" not in _dom0_network:
                        msg = (f"Could not identify network info for some dom0's. "
                               f"Received network info: {json.dumps(self.mGetDom0Networks(), indent=4)}")
                        _logger.mAppendLog(LOG_TYPE.ERROR, msg)
                        _jsonMap.update(INTERNAL_ERROR_REPORT)
                        self.mSetPreChecksStatus(False)
                        break

            _jconf = mReadConfigFile(_profilePath)

        if _eBox.mIsOciEXACC() and _eBox.mIsKVM():
            _switches = _eBox.mReturnSwitches(aMode=True, aRoceQinQ=True)
        else:
            _switches = _eBox.mReturnSwitches(aMode=True)

        self.mSetDom0s(_dom0s)
        self.mSetDomUs(_domUs)
        self.mSetSwitches(_switches)
        self.mSetCells(_cells)

        # code for test based execution
        def _initCheckConfig():

            _ret = True
            try:
                self.__check_parser = CheckParser(_masterCheckListPath)
                if self.__check_parser.mInitCheckParser() == False:
                    return False

                self.__profile_parser = ProfileParser(self.__check_parser, _jconf)
                if self.__profile_parser.mInitProfileParser() == False:
                    return False

                if self.mGetResultLevel() is not None:
                    get_logger().mSetResultLevel(self.mGetResultLevel())

                # TBD: create finalChecklist if profile not passed
                self.__checklist = self.__profile_parser.buildChecklist()
                self.__check_executor = CheckExecutor(self)

            except Exception as e:
                ebLogError('*** Exception occurred while loading checklist %s, on line %s' % (
                    str(e), str(sys.exc_info()[-1].tb_lineno)))
                ebLogHealth('NFO', '*** Exception occurred while loading checklist with error %s, on line %s' % (
                    str(e), str(sys.exc_info()[-1].tb_lineno)))
                ebLogError(traceback.format_exc())
                _ret = False

            return _ret

        def _getProfilePath():

            _profilePath = self.__basepath + HEALTHCHECK_DICT['all']
            if aOptions.healthcheck:
                if aOptions.healthcheck == 'connection':
                    _profilePath = self.__basepath + HEALTHCHECK_DICT['connection']
                elif aOptions.healthcheck == 'xml':
                    _profilePath = self.__basepath + HEALTHCHECK_DICT['xml']
                elif aOptions.healthcheck == 'conf':
                    _profilePath = self.__basepath + HEALTHCHECK_DICT['conf']
                elif aOptions.healthcheck == 'preprov':
                    _profilePath = self.__basepath + HEALTHCHECK_DICT['preprov']

                elif aOptions.healthcheck == 'exachk':
                    _profilePath = self.__basepath + HEALTHCHECK_DICT['exachk']
                elif aOptions.healthcheck == 'stresstest':
                    _profilePath = self.__basepath + HEALTHCHECK_DICT['stresstest']
                elif aOptions.healthcheck == 'cluster':
                    _profilePath = self.__basepath + HEALTHCHECK_DICT['cluster']

                else:
                    _profilePath = self.__basepath + HEALTHCHECK_DICT['all']

            return _profilePath

        _masterCheckListPath = self.__basepath + HEALTHCHECK_DICT['master_checklist']

        if aOptions.healthcheck != 'custom':
            _profilePath = _getProfilePath()
            _jconf = mReadConfigFile(_profilePath)

        # skip adding domus in case of connection check
        if not _initCheckConfig():
            ebLogError("profile initialization failed, exiting from healthcheck")
            return

        # update global healthcheck conf params from profile
        self.mUpdateHcConfig()
        _hcconf = self.mGetHcConfig()

        try:
            if self.mGetPreChecksStatus():
                self.mGetCheckExecutor().execute_checklist()
        except Exception as e:
            ebLogError('*** Exception occurred while running healthcheck with error %s, on line %s' % (
                str(e), str(sys.exc_info()[-1].tb_lineno)))
            ebLogHealth('ERR', '*** Exception occurred while running healthcheck with error %s, on line %s' % (
                str(e), str(sys.exc_info()[-1].tb_lineno)))
            ebLogError(traceback.format_exc())
            if "Error while multiprocessing(Process timeout)" in str(e):
                raise ExacloudRuntimeError(0x0756, 0xA, str(e))

        ebLogHealth('NFO', '*** Errors, RECOMMENDs and Warnings ***')
        ebLogTrace('*** Errors, RECOMMENDs and Warnings ***')
        _recommend = get_logger().mGetRecommend()
        # Results - TXT format
        for _line in sorted(_recommend):
            ebLogHealth('NFO', '*** %s ***' % (_line))
            ebLogInfo('*** %s ***' % (_line))

        # CNS dump is separate file. If not CNS, do the dump
        self.mLogCPData(aOptions)
        # Results - JSON format
        with open(_jsonHandler, 'a') as outfile:
            json.dump(_jsonMap, outfile, skipkeys=True, indent=4, ensure_ascii=False)

        ebLogTrace('\n')
        ebLogTrace('The healthcheck activity is completed')
        ebLogTrace('Detailed status is available at <exacloud>/log/checkcluster/%s' % (_LogHandler))

        ebLogRemoveHCLogDestination(self.__tmp_log_destination)
        ebLogSetHCLogDestination(_defaultLogHandler)
        if aIncident is False:
            self.mUpdateRequestData(aOptions)
        self.mDumpJSON()
        self.mZipResults()

        if "diag_root" in self.mGetHcConfig():
            _dest = self.mGetHcConfig()["diag_root"] + "/diagnostic/results/healthcheck/"
            _src = self.mGetResultDir()[:-1] + ".zip"
            try:
                os.stat(_dest)
            except:
                os.makedirs(_dest)
            if os.path.isfile(_src) and os.path.isdir(_dest):
                _cmd = "cp " + os.path.abspath(_src) + " " + os.path.abspath(_dest)
                _rc, _none, _out, _err = self.mGetEbox().mExecuteLocal(_cmd)
                if _rc:
                    ebLogError("Error copying health check zip to diag_root")
            else:
                ebLogError("Src/dest not valid for cmd: cp " + _src + " " + _dest)
                ebLogError("Error copying health check zip to diag_root")

        return 0

    def mZipResults(self):
        _zippath = self.mGetResultDir()
        _zipF = None

        try:
            _zipF = zipfile.ZipFile(_zippath[:-1] + ".zip", 'w', zipfile.ZIP_DEFLATED)
        except:
            return

        try:
            for _root, _dirs, _files in os.walk(_zippath):
                for _f in _files:
                    _zipF.write(os.path.join(_root, _f))
            _zipF.close()
        except:
            ebLogError("Error Zipping Health check files into zip file")

    # Log some basic info about the control plane
    def mLogCPData(self, aOptions):

        _recommend = get_logger().mGetRecommend()
        _totalCrit = 0
        _totalErr = 0
        _totalWarn = 0
        _totalReco = 0

        _eBox = self.mGetEbox()
        _ebCore = exaBoxCoreInit(aOptions)

        _jsonMap = self.mGetJsonMap()
        _jsonMap['ControlPlane'] = {}

        _exaVersion = "%s (%s)" % (_ebCore.mGetVersion())
        _jsonMap['ControlPlane']['exacloudVersion'] = _exaVersion

        _oedaVersion = get_gcontext().mGetOEDAVersion()
        _jsonMap['ControlPlane']['oedaVersion'] = _oedaVersion.rstrip()

        _datetime = self.mGetDateTime()
        _jsonMap['ControlPlane']['dateTime'] = _datetime

        if _eBox.mIsOciEXACC():
            _cmd = "sudo /usr/local/bin/imageinfo -ver"
            _, _, _o, _ = _eBox.mExecuteLocal(_cmd, aCurrDir=_eBox.mGetBasePath())
            if _o:
                _image_ver = _o.strip()
                _jsonMap['ControlPlane']['cpsImageVersion'] = _image_ver

        for _line in sorted(_recommend):
            if "CRITICAL" in _line:
                _totalCrit += 1
            elif "ERROR" in _line:
                _totalErr += 1
            elif "WARNING" in _line:
                _totalWarn += 1
            elif "RECOMMEND" in _line:
                _totalReco += 1
            else:
                pass

        _jsonMap['ControlPlane']['totalCriticals'] = _totalCrit
        _jsonMap['ControlPlane']['totalErrors'] = _totalErr
        _jsonMap['ControlPlane']['totalWarnings'] = _totalWarn
        _jsonMap['ControlPlane']['totalRecommends'] = _totalReco

        if _totalErr > 0 or _totalCrit > 0:
            _overallStatus = CHK_RESULT.reverse_mapping(CHK_RESULT.FAIL).upper()
        else:
            _overallStatus = CHK_RESULT.reverse_mapping(CHK_RESULT.PASS).upper()
        _jsonMap['ControlPlane']['overallStatus'] = _overallStatus
        # End

    # Dump the JSON object
    def mUpdateRequestData(self, aOptions):

        _data_d = self.mGetJsonMap()
        _reqobj = self.mGetEbox().mGetRequestObj()
        if _reqobj is not None:
            _reqobj.mSetData(json.dumps(_data_d))
            _db = ebGetDefaultDB()
            _db.mUpdateRequest(_reqobj)
        elif aOptions.jsonmode:
            ebLogJson(json.dumps(_data_d, indent=4))

    def mDumpJSON(self):
        """
        dump restructured JSON in form of individual json objects required for ELK
        """
        _jsonResMap = self.mGetJsonMap()
        _jsonResHandler = self.mGetJsonResHandler()
        ebLogTrace('ELK supported healthcheck result is available at %s' % (_jsonResHandler))

        with open(_jsonResHandler, 'a') as outfile:

            json.dump(_jsonResMap['ControlPlane'], outfile, skipkeys=True, indent=4, ensure_ascii=False)
            outfile.write("\n")
            _jsonResMap.pop('ControlPlane')

            for _chkname, _chkResult in six.iteritems(_jsonResMap):
                for _target, _targetResult in six.iteritems(_chkResult):
                    json.dump(_targetResult, outfile, skipkeys=True, indent=4, ensure_ascii=False)
                    outfile.write("\n")
