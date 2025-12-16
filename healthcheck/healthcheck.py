"""
 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    healthcheck.py - added for hc v2 (migrated all checks from ebCluHealth)

FUNCTION:
    define functions for healthcheck

NOTE:
    None

History:

    MODIFIED     (MM/DD/YY)
       aararora   05/28/25 - Bug 37981919: cellcli alerthistory command output
                             is now on multiple lines from 25.x onwards
       rkhemcha   11/11/24 - 37243436 - Fix bridge existence logic for network
                             validation
       akkar      10/13/24 - Bug 37094908: Add sqlplus path to grid
       rkhemcha   09/20/24 - 35979312,35594098 - Network validation changes for
                             selective testing during network reconfiguration
       rkhemcha   09/06/24 - 37031322 - drScan to use DR domain and not client
                             domain
       naps       08/14/24 - Bug 36949876 - X11 ipconf path changes.
       rkhemcha   07/26/24 - 36873285 - Optimizations to network validation
       jesandov   08/17/23 - 35718992: Add validation on exasplit version with
                             dots
       rkhemcha   06/27/23 - 35500683 - Skip test from down interfaces
       rkhemcha   06/14/23 - 35475974 - Make interface up time configurable
       rkhemcha   02/05/23 - 34715457 - Changes to support validation for 3rd
                             network
       rkhemcha   02/22/23 - 35106442 - Nw vldn report to not break if node not
                             sshable
       rkhemcha   10/27/22 - 34731359 - case insensitive DNS lookup from nw
                             vldn
       rkhemcha   09/15/22 - 34508043 - Changes for enabling re-validation for
                             validated nw objects
       rkhemcha   07/14/22 - 34383909 - Get network info for dom0 using API
                             instead of es.properties
       rkhemcha   05/27/22 - 31389414 - Adding availability test for
                             client/backup IPs using arping
       rkhemcha   05/27/22 - 34134702 - Network Validation fix for
                             sharing client/backup networks
       rkhemcha   04/27/22 - 34095979 - Modify NetworkPingTest for Elastic
                             Compute Flow
       rkhemcha   04/07/22 - 33922918 - Network Validation changes to support
                             network reconfiguration
       scoral     03/28/22 - Bug 33979523: Remove the Network and Gateway Subnet validation for Admin networks
                             && Compared the hostname part only of the NSlookup output.
       rkhemcha   02/17/22 - 33820696 - Refactor Network Validation specific
                             code
       rkhemcha   02/09/22 - 33825405 - NtpTest to check for OL version instead
                             of hypervisor
       aypaul     01/20/22 - Enh#33762417 Correcting healthcheck tests.
       rkhemcha   08/09/21 - 33186306/33154526 - LACP support for nw vldn
       ajayasin   07/22/21 - absolute path used for ping/arping command
       aypaul     07/22/21 - Bug#33057521 Adding unit tests for healthcheck.py
       rkhemcha   03/31/21 - 32700925 - Nw vldn changes to make errors readable
                             to customer
       mpedapro   03/30/21 - Bug::32675224 Replace ping with arping
       rkhemcha   03/19/21 - 32649478 - DNS lookup in network
                             validation to skip CNAME resolutions
       jejegonz   11/28/20 - Delete unused LogMgr.py imports
       pvachhan   11/10/20 - Add retry mechanism to NTP test in network
                             validation to overcome rate limiting
       rkhemcha   11/10/20 - 32082144 - Adding exclude options for nw vldn
                             tests from backup network or skipping backup
                             hostname resolutions for DNSTest
       hnvenkat   11/05/20 - 32110632 - Add Exasplice image version where applicable
       rkhemcha   09/21/20 - 31791734 - Enhancing logging for network
                             validation
       mpedapro   09/02/20 - bug::31743321 create and delete bonding in nw
                             validation to resolve arp cache issue
       jlombera   08/06/20 - Bug 31652811: fix typo introduced in bug 31607257
       mpedapro   07/28/20 - Enh::31596666 same vlan support for network
                             validation
       jlombera   07/20/20 - Bug 31607257: handle KVM images
       devbabu    06/19/20 - 31500088 - removing the unwanted spaces from image
                             version
       rkhemcha   05/26/20 - 31389414 - Nw Vldn to verify Scan and Vip address
                             don't ping
       rkhemcha   04/15/20 - bug 31046703 - Network Validation should access
                             dns/ntp directly if in same subnet as domU network
       rkhemcha   02/17/20 - ER 30800764 - Adding Forward and Reverse DNS Lookup
                             for DomU components
       ajayasin   01/28/20 - list vmimage folder content health check added
       aypaul     01/19/20 - 30721615 Exacloud healthcheck gets hung for some
                             healthcheck functions.
       sakskuma   01/07/20 - Lrg 22518816 - Incident File misses
                             /var/log/messages due to invalid ascii characters
       mpedapro   11/22/19 - Enh 30577975 :: Considering no vlan case for
                             oci-exacc network validation
       mpedapro   09/27/19 - bug 30345680: If ntp/dns tests for backup
                             interface fails in n/w validation should give only
                             warning
       vicgupta   09/04/19 - ER-30139456, add extra info in response of
                             CPSVersion
       mpedapro   08/21/19 - FETCHING THE N/W INTERFACE DETAILS FROM THE
                             ES.PROPERTIES FILE INSTEAD OF XML FOR N/W
                             VALIDATION CODE : 30208763
       mpedapro   08/19/19 - Correcting the error in mCheckLinkStatusTest :
                             30197829
       shavenug   07/31/19 - 30117384 OCI-EXACC : BRING UP NETWORK INTERFACES
                             IF DOWN DURING NETWORK SANITY CHECK
       yyingl     07/30/29 - Bug 30111743 EXACLOUD REQUESTS ERROR WITH MESG CRITICAL EXCEPTION CAUGHT ABORTING REQUEST
       bshenoy    07/29/19 - XbranchMerge bshenoy_bug-29875966 from
                             st_ebm_19.1.1.0.0
       gurkasin   16/07/19 - added mCPSVersion check
       devbabu    07/04/19 - added db stats list feature
       yyingl     06/26/19 - ECS sanity check
       sakskuma   06/13/19 - Bug 29909813 - Remove duplicate existence of
                             mCheckEbtables
       mpedapro   05/29/19 - Including the gateway,dns,ntp checks for the
                             network object validation :: 29606740
       mpedapro   05/06/19 - Including new tests for network validation
                             oci-exacc : 29608420
       sakskuma   04/15/19 - Bug 29192199 - Additional Healthcheck V2 DomU
                             tests
       sakskuma   02/11/19 - Bug 29335430 - mgetIlomesList to mGetIlomsList
       jesandov   01/24/19 - XbranchMerge jesandov_bug-29057115 from main
       sakskuma   11/29/18 - adding more comments.
       sakskuma   11/21/18 - Adding changes for DomU Tests. Bug 28614694.
       dekuckre   03/23/18 - copy/modify checks from cluhealth.py to
                             healthcheck.py
       bhuvnkum   03/14/18 - create file

"""

from exabox.tools.AttributeWrapper import wrapStrBytesFunctions
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogInfo, ebLogJson
from exabox.ovm.vmconfig import exaBoxClusterConfig
import os, sys, subprocess, uuid, time, os.path, traceback
from subprocess import Popen, PIPE
import xml.etree.cElementTree as etree
from exabox.core.Context import get_gcontext
from exabox.core.Core import exaBoxCoreInit
from exabox.ovm.vmcontrol import exaBoxOVMCtrl
from tempfile import NamedTemporaryFile
from time import sleep
from datetime import datetime
from base64 import b64decode
import hashlib
import re, random
import json, copy, socket
from exabox.tools.scripts import ebScriptsEngineFetch
from exabox.core.DBStore import ebGetDefaultDB
from multiprocessing import Process
from exabox.ovm.monitor import ebClusterNode
import threading
import csv
import ast

from exabox.healthcheck.hcconstants import HcConstants, LOG_TYPE, CHK_RESULT
from exabox.healthcheck.clucheck import ebCluCheck
from exabox.ovm.sysimghandler import (getDom0VMImagesInfo, getNewestVMImageArchiveInRepo)
from exabox.ovm.clumisc import ebCluSshSetup, mGetAlertHistoryOptions
from exabox.ovm.clumisc import ebCluPreChecks
from exabox.ovm.clunetwork import ebCluNetwork, HostNotConnectable
from exabox.ovm.hypervisorutils import getHVInstance
#from __builtin__ import set, True, False
from six.moves.builtins import set
from collections import Counter

CLIENT = "client"
BACKUP = "backup"
OTHER = "other"
DR = "dr"

class HealthCheck(ebCluCheck):

    def __init__(self, aCluCtrlObj, aCluHealthObj=None):
        super(HealthCheck, self).__init__(aCluCtrlObj, aCluHealthObj)
        # Network validation specific metadata to be used across different tests
        # NOTE: Each dictionary below is specific to every NODE running the test
        self.bondInfo = {}
        self.downIntfs = {}
        self.updatedSysctlProperties = []
        self.intermediateResult = {}
        self.nwVldnUtils = None

    def __del__(self):
        super(HealthCheck, self).__del__()

    def getNetworkValidationUtils(self):
        return self.nwVldnUtils

    # Class containing exacloud healthcheck param details to be used by tests in network validation.
    class NetworkValidationUtils:

        noVlanList = ['UNDEFINED', '', '1']

        def __init__(self, aHost, jsonMap, nodeObj, healthObj):

            # cluHealth Obj
            self.hc = healthObj.mGetHc()

            # flags to set according to host type
            self.isDom0 = self.isHostDom0(aHost)
            self.isDomU = self.isHostDomU(aHost)

            # cluControl Obj
            self.eBox = healthObj.mGetEbox()
            # logger Obj
            self.logger = healthObj.logger
            self.nodeObj = nodeObj

            try:
                # node connection Obj
                self.nodeObj = healthObj.mGetNode(aHost, aForceRetry=True)
            except Exception as e:
                self.logger.mAppendLog(LOG_TYPE.ERROR, f"Unable to connect to host {aHost}.")
                raise HostNotConnectable(aHost)

            # dict of interfaces with corresponding cluConfig Obj
            if self.isDom0:
                self.interfaceInfo = self.mGetDomuNetworkForDom0(aHost, jsonMap)
            elif self.isDomU:
                self.interfaceInfo = self.mGetDomuNetwork(aHost, jsonMap)

            # /ovm/cluNetwork Obj
            if "ERROR" in self.interfaceInfo:
                self.cluNetworkObj = ebCluNetwork(aHost, {}, self.eBox, self.nodeObj, self.hc, healthObj.logger)
            else:
                self.cluNetworkObj = ebCluNetwork(aHost, self.interfaceInfo, self.eBox, self.nodeObj, self.hc, healthObj.logger)

            # read network validation config from healthcheck.conf
            self.vldnConfig = self.hc.mGetHcConfig()["network_validation"]
            self.logger.mAppendLog(LOG_TYPE.VERBOSE, f"Validation config being used: - {json.dumps(self.vldnConfig, indent=4)}")

        def isNetworkReconfiguring(self, aHost, networkType):
            """
            Returns true if networkType is reconfiguring
            :param aHost: dom0 FQDN
            :param networkType: client, backup, dr
            :return: Boolean
            """
            return self.hc.mGetUpdateNetwork().get(aHost).get(networkType).get('isReconfiguring')

        def isReconfiguration(self):
            return self.hc.mGetReconfiguration()

        def isReValidation(self):
            return self.hc.mGetReNetValidation()

        def getUpdateProperties(self, aHost, networkType):
            updatePropertyList = self.hc.mGetUpdateNetwork().get(aHost).get(networkType).get('updateProperties')
            if not updatePropertyList:
                return []
            return self.hc.mGetUpdateNetwork().get(aHost).get(networkType).get('updateProperties')

        def getServiceChange(self, service):
            return self.hc.mGetUpdateNetwork().get('networkServices').get(service)

        def anyFqdnIpChange(self):
            """
            Return Boolean value based on if any hostname/IP/domain name is changing across any network
            :return:
            """
            for key, details in self.hc.mGetUpdateNetwork().items():
                if key in ['networkServices']:
                    continue
                for _, updateNet in details.items():
                    if updateNet.get('updateProperties'):
                        if any(x in updateNet.get('updateProperties') for x in ["hostname", "domainname", "ip"]):
                            return True
            return False

        def isDrNetConfigured(self):
            return self.hc.mGetDrNetConfigured()

        def getDom0forDomU(self, domU):
            for pair in self.eBox.mReturnDom0DomUPair():
                if pair[1] == domU:
                    return pair[0]

        def getDomUforDom0(self, dom0):
            for pair in self.eBox.mReturnDom0DomUPair():
                if pair[0] == dom0:
                    return pair[1]

        def getIntfMap(self):
            return self.interfaceInfo

        def getCluNetworkObj(self):
            return self.cluNetworkObj

        def setNodeObj(self, nodeObj):
            self.nodeObj = nodeObj

        def getNodeObj(self):
            return self.nodeObj

        def getParam(self, param):
            return self.vldnConfig[param]

        def ifSkipBackupNwChecks(self, testName):
            """
            Function that reads healthcheck.conf params to decide skipping of test/(s)
            from the backup network.
            :param testName:
            :return: Bool
            """
            if (self.vldnConfig["skip_all_backup_checks"]).lower() == "true":
                return True
            if "gateway" in testName:
                if (self.vldnConfig["skip_backup_gateway/vlan_check"]).lower() == "true":
                    return True
            elif "dns" in testName:
                if (self.vldnConfig["skip_backup_DNS_check"]).lower() == "true":
                    return True
            return False

        def mGetDomuNetworkForDom0(self, aHost, _jsonMap):
            """
            Function to get the dictionary of client/backup network info, including:
            interfaces(keys), netobj, bonding master and bridge for the domU of the dom0 passed.

            Returned Dict format:
            {   "client": {
                    "interfaces": ["intf1", "intf2"],
                    "netobj": ebCluConfig OBJ,
                    "bridge": "vmbondeth0",
                    "bonding": "bondeth0"
            }

            :param aHost: dom0 FQDN
            :param _jsonMap: Result JSON of the invoker
            :return: Dictionary of interfaces
            """

            _domU = None
            for _dom0domU in self.eBox.mReturnDom0DomUPair():
                if _dom0domU[0] == aHost:
                    self.logger.mAppendLog(LOG_TYPE.DEBUG, "Dom0 is {} and corresponding DomU is {}".format(aHost, _dom0domU[1]))
                    _domU = _dom0domU[1]
            _eBoxNetworks = self.eBox.mGetNetworks()
            interfacemap = {}
            if not _domU:
                return interfacemap

            _domU_mac = self.eBox.mGetMachines().mGetMachineConfig(_domU)
            _net_list = _domU_mac.mGetMacNetworks()
            _net_info = self.hc.mGetDom0Networks(aHost)
            self.logger.mAppendLog(LOG_TYPE.DEBUG, "Network Info detected for the host {}:\n {}".format(aHost, json.dumps(_net_info, indent=4)))

            for _net in _net_list:
                netobj = _eBoxNetworks.mGetNetworkConfig(_net)
                networkType = netobj.mGetNetType()
                if networkType in [CLIENT, BACKUP, OTHER]:
                    # rename other network to show as dr network in result JSON
                    if networkType == OTHER:
                        networkType = "dr"

                    if "ERROR" in _net_info:
                        return _net_info

                    netMap = interfacemap[networkType] = {}
                    netMap["netobj"] = netobj
                    netMap["bridge"] = _net_info[networkType]["bridge"].strip()
                    netMap["bonding"] = _net_info[networkType]["bond_master"].strip()
                    netMap["interfaces"] = _net_info[networkType]["bond_slaves"].split()

            return interfacemap

        def mGetDomuNetwork(self, aHost, _jsonMap):
            """
            Function to get the dictionary of client/backup network info, including:
            interfaces(keys) and netobj for the domU
            Returned Dict format if aHost is domU:
            {   "client": {
                    "interfaces": ["bondeth0"],
                    "netobj": ebCluConfig OBJ
                    }
            }
            :param aHost: domU FQDN
            :param _jsonMap: Result JSON of the invoker
            :return: Dictionary of interfaces
            """

            interfacemap = {}

            _domU = aHost
            _eBoxNetworks = self.eBox.mGetNetworks()
            _domU_mac = self.eBox.mGetMachines().mGetMachineConfig(_domU)
            _net_list = _domU_mac.mGetMacNetworks()

            for _net in _net_list:
                netobj = _eBoxNetworks.mGetNetworkConfig(_net)
                networkType = netobj.mGetNetType()
                if networkType in [CLIENT, BACKUP, OTHER]:
                    if networkType == OTHER:
                        networkType = "dr"
                    netMap = interfacemap[networkType] = {}
                    netMap["netobj"] = netobj
                    if networkType == CLIENT:
                        netMap["interfaces"] = ["bondeth0"]
                    elif networkType == BACKUP:
                        netMap["interfaces"] = ["bondeth1"]
                    elif networkType == DR:
                        netMap["interfaces"] = ["bondeth2"]

            return interfacemap

        def isHostDom0(self, host):
            if host in self.hc.mGetDom0s():
                return True
            return False

        def isHostDomU(self, host):
            if host in self.hc.mGetDomUs():
                return True
            return False


    # Class containing custom helper functions used by tests in network validation.
    class NetworkValidationHelpers:

        PASS = "Pass"
        FAIL = "Fail"
        SKIP = "Skipped"

        INTERNAL_ERROR = "INTERNAL_ERROR"
        BACKUP_NW_SKIP = "BACKUP_NW_SKIP"
        UPDATE_NW_SKIP = "UPDATE_NW_SKIP"
        DOWN_INTF_SKIP = "DOWN_INTF_SKIP"

        REACH_ORA_SUP = "REACH_ORA_SUP"
        CHECK_NW_ENTITIES = "CHECK_NW_ENTITIES"
        CHECK_GW_TEST = "CHECK_GW_TEST"

        preDefCauses = {
            INTERNAL_ERROR: "Internal Error.",
            BACKUP_NW_SKIP: "Backup network test(s) configured to skip from healthcheck.conf",
            UPDATE_NW_SKIP: "This network not selected for reconfiguration on this host",
            DOWN_INTF_SKIP: "This interface is down on the host"
        }

        preDefResolutions = {
            CHECK_NW_ENTITIES: "Please ensure network entities like VLAN Id, Gateway, IP addresses and Server IP's are correct.",
            CHECK_GW_TEST: "Please check result for Gateway Test for this VLAN.",
            REACH_ORA_SUP: "Please try again, if issue persists please contact Oracle support."
        }

        def __init__(self, aHost, logger, healthObj):
            self.host = aHost
            self.logger = logger
            self.hcObj = healthObj

        def convNetmasktoPrefix(self, netmask):
            """
            :param netmask: Netmask in IP format
            :return: Prefix /32 version of the netmask
            """
            nw = netmask.split('.')
            prefix = 32
            for byte in nw:
                byte = int(byte)
                byte = (1 << 8) - 1 - byte
                while byte:
                    prefix = prefix - 1
                    byte = byte >> 1
            return prefix

        def ipTo32bitBinary(self, ipaddr):
            """
            :param ipaddr: IP address
            :return: 32 bit representation of the IP
            """
            octets = ipaddr.split('.')
            binStr = ""
            for octet in octets:
                octet = int(octet)
                bnr = '{0:08b}'.format(octet)
                binStr = binStr + bnr
            return binStr

        def checkifSameNw(self, ip1, ip2, mask):
            """
            :param ip1: IP address 1
            :param ip2: IP address 2
            :param mask: Netmask in IP format
            :return: Bool, True if both IP's belong to same network
            """
            maskSetBits = self.convNetmasktoPrefix(mask)
            binIp1 = self.ipTo32bitBinary(ip1)
            binIp2 = self.ipTo32bitBinary(ip2)
            for bit in range(maskSetBits):
                if binIp1[bit] == binIp2[bit]:
                    continue
                else:
                    return False
            return True

        def is_valid_ipv4_address(self, address):
            """
            :param address: IP address
            :return: Bool, True if IP address is a valid IPv4 address
            """
            try:
                socket.inet_pton(socket.AF_INET, address)
            except socket.error:
                return False
            return True

        def is_valid_ipv6_address(self, address):
            """
            :param address: IP address
            :return: Bool, True if IP address is a valid IPv6 address
            """
            try:
                socket.inet_pton(socket.AF_INET6, address)
            except socket.error:
                return False
            return True

        def isGatewayReachable(self, result, network, intf):
            """
            :param result: intermediate result dictionary
            :param network: client/backup/DR
            :param intf: ethX/vmbondethX
            :return: Boolean

                result format:
                "mCheckGatewayTest":{
                    "hcTestResult":0,
                    "hcLogs":[],
                    "hcMsgDetail":{
                        "hcDisplayString":[],
                        "client":{
                            "eth1":{"status":"Pass"},
                            "eth2":{"status":"Pass"}
                        }
                    },
                    "hcCheckParam":{}
                },
            """
            try:
                if result.get("mCheckGatewayTest").get("hcMsgDetail").get(network).get(intf).get('status') == self.PASS:
                    return True
            except:
                self.logger.mAppendLog(LOG_TYPE.INFO, "Gateway test result unavailable. Will not skip any tests.")
                return True

            return False

        def updateResMap(self, resMap, status, param1, param2=None, param3=None, param4=None, cause=None, resolution=None):
            """
            Helper function to update the Result JSON of the invoking test
            :param resMap:
            :param param1: Interface Type like client/backup
            :param param2: Physical interface/bridge over which test is performed
            :param param3: Server IP in case of DNS/NTP test
            :param param4: hostname FDQN / IP address for DNS/NetworkPing Test
            :return: updated resMap
            """

            resMapLocal = resMap
            # identify the level of resMap
            for param in [param1, param2, param3, param4]:
                if param:
                    resMapLocal = resMapLocal[param]

            resMapLocal["status"] = status

            # Adding this to support custom cause/resolutions
            if self.preDefCauses.get(cause):
                cause = self.preDefCauses[cause]
            if self.preDefResolutions.get(resolution):
                resolution = self.preDefResolutions[resolution]

            if status == self.SKIP:
                resMapLocal["cause"] = cause
            elif status == self.FAIL:
                resMapLocal["cause"] = cause
                resMapLocal["resolution"] = resolution
                resMap["hcDisplayString"].add("{} {}".format(cause, resolution))

        def testFooter(self, testname, result, jsonMap):

            jsonMap["hcDisplayString"] = list(jsonMap["hcDisplayString"])
            _msg = "FAILED" if result else "SUCCESSFUL"
            self.logger.mAppendLog(LOG_TYPE.INFO, f"Finished {testname} Test, Host - {self.host}, STATUS - {_msg}")

        def connectToHost(self, aHost):
            try:
                # node connection Obj
                return self.hcObj.mGetNode(aHost, aForceRetry=True)
            except Exception as e:
                self.logger.mAppendLog(LOG_TYPE.ERROR, f"Unable to connect to host {aHost}.")
                raise HostNotConnectable(aHost)

        def getNetworkValidationUtils(self, aHost, _jsonMap):
            # create connection to host
            nodeObj = self.connectToHost(aHost)

            utils = self.hcObj.getNetworkValidationUtils()
            if utils is not None:
                # update node connection object since every test creates a new connection
                utils.setNodeObj(nodeObj)
                utils.getCluNetworkObj().setNodeObj(nodeObj)
                return utils
            else:
                self.hcObj.nwVldnUtils = self.hcObj.NetworkValidationUtils(aHost, _jsonMap, nodeObj, self.hcObj)
                return self.hcObj.nwVldnUtils

        def skipTest(self, testname, node, jsonMap):
            self.hcObj.mDisconnectNode(node)
            self.logger.mAppendLog(LOG_TYPE.WARNING, "Skipping {} test from {}.".format(testname, self.host), jsonMap)
            self.updateResMap(jsonMap, self.FAIL, None, cause="Skipped.", resolution="")
            self.testFooter(testname, CHK_RESULT.FAIL, jsonMap)

        def startNWTestLogger(self, testName):
            ebLogInfo(f"Starting {testName} test for Network Validation, Host - {self.host}")
            self.logger.mAppendLog(LOG_TYPE.INFO,
                                   "{}{:->80}{}{:-<80}".format('\n', '\n', "Starting {} Test, Host - {}".format(testName, self.host), '\n'))

    def mGetResultDir(self):
        return self.mGetHc().mGetResultDir()

    def mRemoveBlankLinesHelper(self, aLines):
        _lines2 = []
        for _line in aLines:
            _line = _line.strip()
            _skip = _line.count('-') == len(_line)
            if len(_line)>0 and not _skip:
                _lines2.append(_line)
        return _lines2


    def mParseOratab(self, aNode):
        _cmd_str = "cat /etc/oratab"
        _result = []
        _i, _o, _e = aNode.mExecuteCmd(_cmd_str, aTimeout=180)
        if _o:
            _output_lines = _o.readlines()
            _output_lines = self.mRemoveBlankLinesHelper(_output_lines)
            for _line in _output_lines:
                if _line[0] not in ['#']:
                    _line2 = _line.split(':')
                    _result.append(_line2)
        return _result

    def mCopyResultHelper(self, aLines):
        _res_info = {}
        _res_index = 0
        for _line in aLines:
            _res_index += 1
            _res_info[_res_index] =  _line.encode('utf-8','ignore').decode('utf8')
        return _res_info

    def mWriteResultToFile(self, filename, lines):
        _file = open(filename, 'w')
        for _line in lines:
            _file.write(_line.encode('utf-8','ignore').decode('utf8'))
        _file.close()

    def mPreProvSystemChecks(self, aHost):
        _hc = self.mGetHc()
        _ebox = self.mGetEbox()
        _host = aHost
        _jsonMap = {}
        _testResult = CHK_RESULT.PASS

        _node = self.mGetNode(_host)

        self.logger.mAppendLog(LOG_TYPE.INFO, '*** *** Pre-provisioning check: for stale domU images in dom0 - %s' %(_host))
        _pchecks = ebCluPreChecks(_ebox)
        if _pchecks.mVMPreChecks(aHost=_host):
            self.logger.mAppendLog(LOG_TYPE.ERROR, "stale domU images found in dom0 - %s" %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        # environments and set self.__shared_env
        if (_ebox.SharedEnv() == True):
            self.logger.mAppendLog(LOG_TYPE.INFO, '*** *** Pre-provisioning check: for available free memory in dom0 - %s' %(_host))
            _precheck = ebCluPreChecks(_ebox)
            if not _precheck.mCheckDom0Mem(_host):
                self.logger.mAppendLog(LOG_TYPE.WARNING, "memsize in XML is greater than available free memory in dom0 - %s" %(_host), _jsonMap)

        self.mDisconnectNode(_node)
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    # Dom0/Switch test:
    # Check if root partition has enough space.
    def mCheckRootSpace(self, aHost):

        _hc = self.mGetHc()
        _ebox = self.mGetEbox()
        _host = aHost

        _testResult = CHK_RESULT.PASS
        _jsonMap = {}
        _chkParam = {}

        # initialize threshold value
        _threshold_root_space = "85"
        _precheck = ebCluPreChecks(_ebox)
        if "threshold_root_space" in _hc.mGetHcConfig():
            # add in healthcheck.conf if want to override default value
            _threshold_root_space = _hc.mGetHcConfig()["threshold_root_space"]
            _chkParam["threshold_root_space"] =  _threshold_root_space
        # Used '/' to pass root partition
        if not _precheck.mCheckUsedSpace(_host, '/', _threshold_root_space):
            self.logger.mAppendLog(LOG_TYPE.WARNING, "space used in root partition is more than threshold(%s%%) - %s" % (_threshold_root_space, _host), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        return self.logger.mUpdateResult(_testResult, _jsonMap, _chkParam)
    # end

    def mCheckSshTest(self, aHost, aCheckParam = None):

        _testResult = CHK_RESULT.PASS
        _jsonMap = {}

        _hc = self.mGetHc()
        _host = aHost

        _ssh_timeout = self.mGetCheckParam("lthc_ssh_timeout", "10", aCheckParam)

        if self.mGetNodeConnection().mSshTest(aHost):
            self.logger.mAppendLog(LOG_TYPE.INFO, "ssh test successful for %s" % (_host), _jsonMap)
        else:
            _testResult = CHK_RESULT.FAIL
            self.logger.mAppendLog(LOG_TYPE.CRITICAL, "ssh test failed for %s" % (_host), _jsonMap)


        return self.logger.mUpdateResult(_testResult, _jsonMap, aCheckParam)

    def mCheckPingTest(self, aHost, aCheckParam = None):
        _testResult = CHK_RESULT.PASS
        _jsonMap = {}
        _hc = self.mGetHc()
        _host = aHost
        _ping_retry_count = self.mGetCheckParam("ping_retry_count", "2",aCheckParam)
        _ping_timeout = self.mGetCheckParam("ping_timeout", "4",aCheckParam)

        if self.mGetNodeConnection().mPingTest(aHost, _ping_retry_count, _ping_timeout):
            self.logger.mAppendLog(LOG_TYPE.INFO, "ping test successful for %s" % (_host), _jsonMap)
        else:
            _testResult = CHK_RESULT.FAIL
            self.logger.mAppendLog(LOG_TYPE.CRITICAL, "ping test failed for %s" % (_host), _jsonMap)


        return self.logger.mUpdateResult(_testResult, _jsonMap)

    def mCheckEcsSanity(self):
        # ECS sanity check
        _testResult = CHK_RESULT.PASS
        _jsonMap = {}
        _hc = self.mGetHc()
        _ebox = self.mGetEbox()

        _ecs_sanity_tool_location = _ebox.mCheckConfigOption('ecs_sanity_tool_location')
        self.logger.mAppendLog(LOG_TYPE.INFO, "ECS sanity tool location: %s" % (_ecs_sanity_tool_location), _jsonMap)
        if _ecs_sanity_tool_location is None or not os.path.exists(_ecs_sanity_tool_location):
            self.logger.mAppendLog(LOG_TYPE.ERROR, "ECS sanity tool does not exist.", _jsonMap)
            _testResult = CHK_RESULT.FAIL
            return self.logger.mUpdateResult(_testResult, _jsonMap)

        _xml = _hc.mGetXMLPath()
        _xmlPath = ""
        _rewriteXmlPath = False
        if _xml.startswith('<'):
            _rewriteXmlPath = True
            _currTime = int(round(time.time() * 1000))
            _xmlPath = os.path.join(_ecs_sanity_tool_location,\
                                     'cluster-{}.xml'.format(_currTime))
            with open(_xmlPath,'w') as _f:
                _f.write(_xml)
        else:
            _xmlPath = _xml

        _baseSystem = False
        if "Eighth" in _ebox.mGetEsracks().mDumpEsRackDesc():
            _baseSystem = True
            self.logger.mAppendLog(LOG_TYPE.INFO, '**** Base System Configuration detected')

        _sanity_check_command = "./ecssanitychk"
        _param1 = "--preprov"
        _param2 = "--xml=" + _xmlPath
        _param3 = "--env=ociexacc"

        if _baseSystem:
            _param4 = "--base_system"
            self.logger.mAppendLog(LOG_TYPE.INFO, "ECS sanity check command: %s %s %s %s %s" % (_ecs_sanity_tool_location, _param1, _param2, _param3, _param4), _jsonMap)
            _cmdList = [_sanity_check_command, _param1, _param2, _param3, _param4]
        else:
            self.logger.mAppendLog(LOG_TYPE.INFO, "ECS sanity check command: %s %s %s %s" % (_ecs_sanity_tool_location, _param1, _param2, _param3), _jsonMap)
            _cmdList = [_sanity_check_command, _param1, _param2, _param3]

        # run sanity check tool
        p = Popen(_cmdList, cwd= _ecs_sanity_tool_location, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)
        _output = wrapStrBytesFunctions(p).communicate()[0]

        if _rewriteXmlPath:
            os.remove(_xmlPath)

        _result_file_path = os.path.join(_ecs_sanity_tool_location, re.search('Detailed results will be at (.*).log', _output).group(1)[2:] + '.csv')
        self.logger.mAppendLog(LOG_TYPE.INFO, "ECS sanity check result: %s" % (_result_file_path), _jsonMap)
        if os.path.isfile(_result_file_path) == False:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "ECS sanity test result does not exist.", _jsonMap)
            _testResult = CHK_RESULT.FAIL
            return self.logger.mUpdateResult(_testResult, _jsonMap)

        # construct result json
        _failure_count = 0
        _failed_output = []
        _fieldnames = ("Category","CheckMethod","Result","Source","Dest","Message","Level")
        with open(_result_file_path) as _csvfile:
            _reader = csv.DictReader(_csvfile, _fieldnames)
            _out = json.dumps([ row for row in _reader ])
            _jdata = json.loads(_out)
            for obj in _jdata:
                if obj['Result'] == 'FAIL':
                    _failure_count += 1
                    _failed_output.append(obj)

        if _failure_count > 0:
            _jsonMap['totalFailures'] = _failure_count
            _testResult = CHK_RESULT.FAIL
            self.logger.mAppendLog(LOG_TYPE.ERROR, "ECS sanity test has errors", _jsonMap)

        _jsonMap['output'] = _failed_output
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    #
    # Cell test:
    #   Validate the flashcache on the cell
    #
    def mCheckFlashCache(self, aHost):

        _host = aHost
        _node = self.mGetNode(_host)

        _ebox = self.mGetEbox()
        _jsonMap = {}
        _testResult = CHK_RESULT.PASS
        self.logger.mAppendLog(LOG_TYPE.INFO, '*** Running Cell FlashCache Status checks ***')

        # Check high level status of cell
        _cmd_str = 'cellcli -e list flashcache detail'
        _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
        _out = _o.readlines()
        if _out:
            _fcstatus = "normal"
            _flashattr = _host
            _celllist = []
            for _line in _out:
                _key = _line.lstrip().split(" ")[0].rstrip()
                _value = _line.lstrip().split(":", 1)[1].lstrip().rstrip()
                if _value == "":
                    _value = "None"
                _jsonMap[_key] = _value
                _flashattr = _flashattr + "::" + _key + _value

                if (_key == "status:") and (_value != "normal"):
                    self.logger.mAppendLog(LOG_TYPE.ERROR, "On Cell %s, flashcache status is shown as %s" %(_host, _value), _jsonMap)
                    _fcstatus = _value

            _celllist.append(_host)

            _cluhealth = self.mGetHc()
            _cluhealth.mGetClusterHealthD()[_host].mSetFlashAttr(_flashattr)

            # Store a 'TestResult'
            if _fcstatus != "normal":
                _testResult = CHK_RESULT.FAIL

        else:
            # Missing flashcache. ERROR only if missing in a subset of the cells (checked later)
            self.logger.mAppendLog(LOG_TYPE.WARNING, "On Cell %s, flashcache is missing!!" %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    # end


    def mCheckDBStatusOnCell(self, aHost):

        _ebox = self.mGetEbox()
        _jsonMap = {}
        _testResult = CHK_RESULT.PASS
        _node = self.mGetNode(aHost)

        self.logger.mAppendLog(LOG_TYPE.INFO,'*** Running Database Status on Cell check ***')

        # Check high level status of cell
        _cmd_str = 'cellcli -e LIST DATABASE'
        _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
        _out = _o.readlines()
        if _out:
            for _line in _out:
                if 'ASM' in _line or _line.strip() == '':
                    continue
                if 'CELL-02559' in _line:
                    self.logger.mAppendLog(LOG_TYPE.WARNING, '*** CellSrv not set yet in %s' % (aHost), _jsonMap)
                    _testResult = CHK_RESULT.FAIL

                    continue
                self.logger.mAppendLog(LOG_TYPE.WARNING, 'Unexpected DB on Cell, DB %s found in cell %s' % (_line.rstrip(), aHost), _jsonMap)

        self.mDisconnectNode(_node)
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    #end mCheckDBStatusOnCell


    #
    # Dom0 test:
    # Check all stale locks on Dom0
    #
    def mCheckStaleLocks(self, aHost):

        _host = aHost
        _node = self.mGetNode(_host)

        _ebox = self.mGetEbox()
        _jsonMap = {}
        _testResult = CHK_RESULT.FAIL
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
                    _testResult = CHK_RESULT.PASS
        else:
            _testResult = CHK_RESULT.PASS

        if _testResult == CHK_RESULT.FAIL:
            self.logger.mAppendLog(LOG_TYPE.WARNING, "stale lock with uuid %s found on %s" %(_uuid, _host), _jsonMap)
        else:
            self.logger.mAppendLog(LOG_TYPE.INFO, "No stale lock with uuid %s found on %s" %(_uuid, _host), _jsonMap)

        self.mDisconnectNode(_node)
        return self.logger.mUpdateResult(_testResult, _jsonMap)
    # end

    '''
    Begin Section for tests pertaining to Network Validation
    '''

    def mCheckConfigSetup(self, aHost):
        testName = "Config Setup"
        helpers = self.NetworkValidationHelpers(aHost, self.logger, self)
        helpers.startNWTestLogger(testName)

        _testResult = CHK_RESULT.PASS
        _jsonMap = {"hcDisplayString": set()}

        desiredSysctlProperties = [
            ("net.ipv4.conf.all.arp_ignore", 1),
            ("net.ipv4.conf.all.arp_announce", 2)
        ]

        try:
            utils = helpers.getNetworkValidationUtils(aHost, _jsonMap)
        except HostNotConnectable as e:
            _testResult = CHK_RESULT.FAIL
            helpers.updateResMap(_jsonMap, helpers.FAIL, None, cause=e.message, resolution=helpers.REACH_ORA_SUP)
            helpers.testFooter(testName, _testResult, _jsonMap)
            return self.logger.mUpdateResult(_testResult, _jsonMap)

        try:
            for property, desiredValue in desiredSysctlProperties:
                _, _runtimeValue = self.mGetEbox().mGetSysCtlConfigValue(utils.getNodeObj(), property)

                if _runtimeValue is not None and int(_runtimeValue) == desiredValue:
                    self.logger.mAppendLog(LOG_TYPE.INFO, f"Property '{property}' already found '{_runtimeValue}' in {aHost}. No change needed.")
                else:
                    self.updatedSysctlProperties.append((property, _runtimeValue))
                    self.logger.mAppendLog(LOG_TYPE.INFO, f"Setting '{property}' to '{desiredValue}' in {aHost} for network validation.")
                    self.mGetEbox().mSetSysCtlConfigValue(utils.getNodeObj(), property, desiredValue)

                helpers.updateResMap(_jsonMap, helpers.PASS, None)

        except Exception as e:      # pragma: no cover
            _testResult = CHK_RESULT.FAIL
            helpers.updateResMap(_jsonMap, helpers.FAIL, None, cause=helpers.INTERNAL_ERROR, resolution=helpers.REACH_ORA_SUP)
            self.logger.mAppendLog(LOG_TYPE.ERROR, "Unable to set custom config on host {}".format(aHost))
            self.logger.mAppendLog(LOG_TYPE.VERBOSE, "Exception {} occurred, stacktrace:\n {}".format(str(e), traceback.format_exc()))

        self.mDisconnectNode(utils.getNodeObj())
        helpers.testFooter(testName, _testResult, _jsonMap)
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    def mCheckConfigRevert(self, aHost):
        testName = "Config Revert"
        helpers = self.NetworkValidationHelpers(aHost, self.logger, self)
        helpers.startNWTestLogger(testName)

        _testResult = CHK_RESULT.PASS
        _jsonMap = {"hcDisplayString": set()}

        try:
            utils = helpers.getNetworkValidationUtils(aHost, _jsonMap)
        except HostNotConnectable as e:
            _testResult = CHK_RESULT.FAIL
            helpers.updateResMap(_jsonMap, helpers.FAIL, None, cause=e.message, resolution=helpers.REACH_ORA_SUP)
            helpers.testFooter(testName, _testResult, _jsonMap)
            return self.logger.mUpdateResult(_testResult, _jsonMap)

        try:
            if len(self.updatedSysctlProperties) == 0:
                self.logger.mAppendLog(LOG_TYPE.INFO, f"No custom configurations set in {aHost} for reverting.")

            for property, originalValue in self.updatedSysctlProperties:
                self.logger.mAppendLog(LOG_TYPE.INFO, f"Reverting '{property}' to original value '{originalValue}' in {aHost}.")
                self.mGetEbox().mSetSysCtlConfigValue(utils.getNodeObj(), property, originalValue)

            helpers.updateResMap(_jsonMap, helpers.PASS, None)
        except Exception as e:  # pragma: no cover
            _testResult = CHK_RESULT.FAIL
            helpers.updateResMap(_jsonMap, helpers.FAIL, None, cause=helpers.INTERNAL_ERROR, resolution=helpers.REACH_ORA_SUP)
            self.logger.mAppendLog(LOG_TYPE.ERROR, "Unable to revert custom config on host {}".format(aHost))
            self.logger.mAppendLog(LOG_TYPE.VERBOSE,
                                   "Exception {} occurred, stacktrace:\n {}".format(str(e), traceback.format_exc()))

        self.mDisconnectNode(utils.getNodeObj())
        helpers.testFooter(testName, _testResult, _jsonMap)
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    # Test to check and create vm bridges for Network Validation.
    def mCheckCreateBondTest(self, aHost):
        testName = "Create Bond"
        helpers = self.NetworkValidationHelpers(aHost, self.logger, self)
        helpers.startNWTestLogger(testName)

        _testResult = CHK_RESULT.PASS
        _jsonMap = {"hcDisplayString": set()}

        try:
            utils = helpers.getNetworkValidationUtils(aHost, _jsonMap)
        except HostNotConnectable as e:
            _testResult = CHK_RESULT.FAIL
            helpers.updateResMap(_jsonMap, helpers.FAIL, None, cause=e.message, resolution=helpers.REACH_ORA_SUP)
            helpers.testFooter(testName, _testResult, _jsonMap)
            return self.logger.mUpdateResult(_testResult, _jsonMap)

        # Skip test in case no matching network returned by exacloud for X9 and above
        if "ERROR" in utils.getIntfMap():
            helpers.skipTest(testName, utils.getNodeObj(), _jsonMap)
            return self.logger.mUpdateResult(CHK_RESULT.FAIL, _jsonMap)

        _clunetwork = utils.getCluNetworkObj()

        # bondInfo is a list of dictionaries for every node containing details about bridges created by network validation
        if aHost not in self.bondInfo:
            self.bondInfo.update({aHost: {}})

        bridgeMap = {}
        # Create dictionary containing bridge details for every network for which the bridge is to be created
        for _intftype, _intfMap in utils.getIntfMap().items():
            bridgeMap[_intftype] = {}
            netobj = _intfMap["netobj"]
            bridgeMap[_intftype]["intfs"] = _intfMap["interfaces"]
            if netobj.mGetNetVlanId() not in utils.noVlanList:
                bridgeMap[_intftype]["vlanId"] = netobj.mGetNetVlanId()
            else:
                bridgeMap[_intftype]["vlanId"] = None
            bridgeMap[_intftype]["bondName"] = _intfMap["bonding"]
            bridgeMap[_intftype]["bridgeName"] = _intfMap["bridge"]
            bridgeMap[_intftype]["lacp"] = netobj.mGetNetLacp()

        self.logger.mAppendLog(LOG_TYPE.INFO, "Bridges Info for CreateBondTest on host %s :%s" % (aHost, json.dumps(bridgeMap, indent=4)))

        try:
            for networkType, networkDetails in bridgeMap.items():
                bridgeName = networkDetails.get("bridgeName")
                bridgeIntfs = networkDetails.get("intfs")
                lacpFlag = networkDetails.get("lacp")
                bondName = networkDetails.get("bondName")
                vlan = networkDetails.get("vlanId")

                # For lacp enabled network, if vlan defined -> create vlan bridge like vmbondethX.vlan
                # if vlan not defined or non-lacp bonding -> create base bridge like vmbondethX
                if lacpFlag and vlan:
                    vmBridge = bridgeName + '.' + vlan
                else:
                    vmBridge = bridgeName
                _jsonMap[networkType] = {vmBridge: {}}

                # check if bridge is already present. create only if not present.
                cmd = "/bin/cat /sys/class/net/{}/operstate".format(vmBridge)
                _, _outstring, _e, _rc = _clunetwork.mLogCmd(cmd, "info", testName)
                if _rc == 0:
                    _jsonMap[networkType][vmBridge]["status"] = "Bridge Exists"
                    self.logger.mAppendLog(LOG_TYPE.INFO, "vmbridge {} already present in the host {}".format(vmBridge, aHost))
                    continue

                if bridgeIntfs.__len__() == 2:
                    retStatus = _clunetwork.mCreateVmBridge(bridgeIntfs, bridgeName, lacpFlag, vlan)
                    lacpBondReady = False

                    if retStatus:
                        # only if bridge created successfully, we need to wait for negotiations in LACP scenario
                        if lacpFlag:
                            actorStr = "Actor Churn State: none"
                            partnerStr = "Partner Churn State: none"
                            timeout_start = time.time()
                            timeout = int(utils.getParam("lacp_timeout"))

                            while time.time() < timeout_start + timeout:
                                cmd = "/bin/cat /proc/net/bonding/{} | grep 'Churn State'".format(bondName)
                                _, _out, _err, _rc = _clunetwork.mLogCmd(cmd, "debug", testName)

                                counts = Counter(_out)
                                self.logger.mAppendLog(LOG_TYPE.VERBOSE, "Current LACP bond status: {}, Host - {}".format(counts, aHost))

                                if counts[actorStr] == 2 and counts[partnerStr] == 2:
                                    lacpBondReady = True
                                    self.logger.mAppendLog(LOG_TYPE.INFO, "LACP negotiations complete for {}, Host - {}".format(bondName, aHost))
                                    break
                                # sleep in case LACP negotiations are not yet complete before retrying
                                time.sleep(5)

                            if lacpBondReady:
                                helpers.updateResMap(_jsonMap, helpers.PASS, networkType, vmBridge)
                            else:
                                _testResult = CHK_RESULT.FAIL
                                helpers.updateResMap(_jsonMap, helpers.FAIL, networkType, vmBridge,
                                                   cause="LACP negotiations failed or could not complete within the defined timeout.",
                                                   resolution=helpers.REACH_ORA_SUP)
                                self.logger.mAppendLog(LOG_TYPE.ERROR, "Unable to create VM Bridges on host {}".format(aHost))
                        else:
                            # Non LACP scenario
                            helpers.updateResMap(_jsonMap, helpers.PASS, networkType, vmBridge)

                        # Common section for LACP / Non-LACP paths if bond creation is successful
                        self.bondInfo[aHost].update({networkType: bridgeMap[networkType]})
                        self.logger.mAppendLog(LOG_TYPE.INFO, "{} bridge created in host {}".format(vmBridge, aHost))
                    else:
                        _testResult = CHK_RESULT.FAIL
                        helpers.updateResMap(_jsonMap, helpers.FAIL, networkType, vmBridge,
                                           cause=helpers.INTERNAL_ERROR, resolution=helpers.REACH_ORA_SUP)
                        self.logger.mAppendLog(LOG_TYPE.ERROR, "Unable to create VM Bridges on host {}".format(aHost))

        except Exception as e:      # pragma: no cover
            _testResult = CHK_RESULT.FAIL
            helpers.updateResMap(_jsonMap, helpers.FAIL, networkType, vmBridge,
                               cause=helpers.INTERNAL_ERROR, resolution=helpers.REACH_ORA_SUP)
            self.logger.mAppendLog(LOG_TYPE.ERROR, "Unable to create VM Bridges on host {}".format(aHost))
            self.logger.mAppendLog(LOG_TYPE.VERBOSE, "Exception {} occurred, stacktrace:\n {}".format(str(e), traceback.format_exc()))

        self.mDisconnectNode(utils.getNodeObj())
        helpers.testFooter(testName, _testResult, _jsonMap)
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    # Test to delete created vm bridges for network validation.
    def mCheckDeleteBondTest(self, aHost):
        testName = "Delete Bond"
        helpers = self.NetworkValidationHelpers(aHost, self.logger, self)
        helpers.startNWTestLogger(testName)

        _testResult = CHK_RESULT.PASS
        _jsonMap = {"hcDisplayString": set()}

        try:
            utils = helpers.getNetworkValidationUtils(aHost, _jsonMap)
        except HostNotConnectable as e:
            _testResult = CHK_RESULT.FAIL
            helpers.updateResMap(_jsonMap, helpers.FAIL, None, cause=e.message, resolution=helpers.REACH_ORA_SUP)
            helpers.testFooter(testName, _testResult, _jsonMap)
            return self.logger.mUpdateResult(_testResult, _jsonMap)

        # Skip test in case no matching network returned by exacloud for X9 and above
        if "ERROR" in utils.getIntfMap():
            helpers.skipTest(testName, utils.getNodeObj(), _jsonMap)
            return self.logger.mUpdateResult(CHK_RESULT.FAIL, _jsonMap)

        if not self.bondInfo[aHost]:
            self.logger.mAppendLog(LOG_TYPE.INFO, "No vmBridges created by network validation tool to delete in host {}".format(aHost))
            _jsonMap["status"] = "No bridge created on this host to delete"
        else:
            _clunetwork = utils.getCluNetworkObj()

            for networkType, bridgeDetails in self.bondInfo[aHost].items():
                # bridgeDetails contains details of bridge for particular network type
                lacp = bridgeDetails["lacp"]
                vlan = bridgeDetails["vlanId"]
                slaves = bridgeDetails["intfs"]

                if lacp and vlan:
                    vmBridge = bridgeDetails["bridgeName"] + '.' + vlan
                else:
                    vmBridge = bridgeDetails["bridgeName"]

                _jsonMap[networkType] = {vmBridge: {}}

                try:
                    # Try utmost 3 times in case of failure to delete a vmbridge.
                    delResult = False
                    for tryCnt in range(0, 3):
                        self.logger.mAppendLog(LOG_TYPE.INFO, "Trying to delete vmBridge {} with slaves {} in host {}".format(vmBridge, slaves, aHost))
                        retStatus = _clunetwork.mDeleteVmBridge(bridgeDetails["bridgeName"], slaves, lacp, vlan)
                        if retStatus:
                            helpers.updateResMap(_jsonMap, helpers.PASS, networkType, vmBridge)
                            delResult = True
                            break
                        else:
                            delResult = False

                    if not delResult:
                        _testResult = CHK_RESULT.FAIL
                        helpers.updateResMap(_jsonMap, helpers.FAIL, networkType, vmBridge,
                                           cause=helpers.INTERNAL_ERROR, resolution=helpers.REACH_ORA_SUP)
                        self.logger.mAppendLog(LOG_TYPE.ERROR, "Unable to delete VM Bridges from host {}".format(aHost))

                except Exception as e:      # pragma: no cover
                    _testResult = CHK_RESULT.FAIL
                    helpers.updateResMap(_jsonMap, helpers.FAIL, networkType, vmBridge,
                                       cause=helpers.INTERNAL_ERROR, resolution=helpers.REACH_ORA_SUP)
                    self.logger.mAppendLog(LOG_TYPE.WARNING, "Unable to delete VM Bridge {} on host {}".format(vmBridge, aHost))
                    self.logger.mAppendLog(LOG_TYPE.VERBOSE, "Exception {} occurred, stacktrace:\n {}".format(str(e), traceback.format_exc()))


        self.mDisconnectNode(utils.getNodeObj())
        helpers.testFooter(testName, _testResult, _jsonMap)
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    # Helper function for mCheckLinkStatusTest of Network Validation
    def mCheckLinks(self, aHost, intftype, intf, clunetworkObj, utils, helpers, _jsonMap, tryBringUp=True, reportErr=True):
        testName = "Link Status"
        ret = False

        try:
            cmd = "/bin/cat /sys/class/net/{}/carrier".format(intf)
            """
                Indicates the current physical link state of the interface.

                Possible values are:
                == =====================
                0  physical link is down -->  (disconnected)
                1  physical link is up   -->  (connected)
                == =====================
            """
            _i, _out, _err, _rc = clunetworkObj.mLogCmd(cmd, "info", testName)
            self.logger.mAppendLog(LOG_TYPE.INFO, "Checking the physical interface {} on {}".format(intf, aHost))
            if _rc == 0:
                # interface is administratively up (physical carrier may be connected/disconnected)
                line = int(_out[0])
                if line == 1:
                    helpers.updateResMap(_jsonMap, helpers.PASS, intftype, intf)
                    ret = True
                else:
                    self.logger.mAppendLog(LOG_TYPE.INFO, "Interface {} on the host {} is down.".format(intf, aHost), _jsonMap)
                    if tryBringUp:
                        # Try to bring up the interface and check it again.
                        self.logger.mAppendLog(LOG_TYPE.INFO, "Will try to bring up interface {} on the host {}.".format(intf, aHost), _jsonMap)
                        _ = clunetworkObj.mBringUpInterface(intf)
                        maxRecheckTimes = int(utils.getParam("interface_up_retries"))
                        while maxRecheckTimes:
                            ret = self.mCheckLinks(aHost, intftype, intf, clunetworkObj, utils, helpers, _jsonMap, False, False)
                            maxRecheckTimes -= 1
                            if ret:
                                break
                            sleep(2)

                        if not ret:
                            self.logger.mAppendLog(LOG_TYPE.WARNING, "Trying last time to check the interface {} on the host {}.".format(intf, aHost), _jsonMap)
                            # Retry again for last time
                            return self.mCheckLinks(aHost, intftype, intf, clunetworkObj, utils, helpers, _jsonMap, False)
                        else:
                            self.logger.mAppendLog(LOG_TYPE.INFO, "Interface {} on the host {} is finally up.".format(intf, aHost), _jsonMap)
                            return ret

                    # This section of the code is just for the root call that initiates the recursion
                    if reportErr:
                        self.logger.mAppendLog(LOG_TYPE.ERROR, "Interface {} on the host {} is not working.".format(intf, aHost), _jsonMap)
                        helpers.updateResMap(_jsonMap, helpers.FAIL, intftype, intf,
                                           cause="Cable fault or cable not detected for {} in host {}.".format(intf, aHost),
                                           resolution="Please check the cables connected to ExaCC.")
            else:
                # interface is administratively down
                self.logger.mAppendLog(LOG_TYPE.INFO, "Interface {} on the host {} is down.".format(intf, aHost), _jsonMap)
                if tryBringUp:
                    # Try to bring up the interface and check it again.
                    self.logger.mAppendLog(LOG_TYPE.INFO, "Will try to bring up interface {} on the host {}.".format(intf, aHost), _jsonMap)
                    _ = clunetworkObj.mBringUpInterface(intf)
                    maxRecheckTimes = int(utils.getParam("interface_up_retries"))
                    while maxRecheckTimes:
                        ret = self.mCheckLinks(aHost, intftype, intf, clunetworkObj, utils, helpers, _jsonMap, False, False)
                        maxRecheckTimes -= 1
                        if ret:
                            break
                        sleep(2)

                    if not ret:
                        self.logger.mAppendLog(LOG_TYPE.WARNING, "Trying last time to check the interface {} on the host {}.".format(intf, aHost), _jsonMap)
                        # Retry again for last time
                        return self.mCheckLinks(aHost, intftype, intf, clunetworkObj, utils, helpers, _jsonMap, False)
                    else:
                        self.logger.mAppendLog(LOG_TYPE.INFO, "Interface {} on the host {} is finally up.".format(intf, aHost), _jsonMap)
                        return ret

                # This section of the code is just for the root call that initiates the recursion
                if reportErr:
                    self.logger.mAppendLog(LOG_TYPE.ERROR, "Interface {} on the host {} is not working.".format(intf, aHost), _jsonMap)
                    helpers.updateResMap(_jsonMap, helpers.FAIL, intftype, intf,
                                       cause="Interface {} is down. Please check status in {}.".format(intf, aHost),
                                       resolution=helpers.REACH_ORA_SUP)

        except Exception as e:      # pragma: no cover
            helpers.updateResMap(_jsonMap, helpers.FAIL, intftype, intf,
                               cause=helpers.INTERNAL_ERROR, resolution=helpers.REACH_ORA_SUP)
            self.logger.mAppendLog(LOG_TYPE.ERROR, "Unable to check status of physical links for interface {} on the host {}".format(intf, aHost), _jsonMap)
            self.logger.mAppendLog(LOG_TYPE.VERBOSE, "Exception {} occurred, stacktrace:\n {}".format(str(e), traceback.format_exc()))

        return ret

    # Network Validation Test to check physical status of interfaces
    def mCheckLinkStatusTest(self, aHost):
        testName = "Link Status"
        helpers = self.NetworkValidationHelpers(aHost, self.logger, self)
        helpers.startNWTestLogger(testName)

        _testResult = CHK_RESULT.PASS
        _jsonMap = {"hcDisplayString": set()}

        try:
            utils = helpers.getNetworkValidationUtils(aHost, _jsonMap)
        except HostNotConnectable as e:
            _testResult = CHK_RESULT.FAIL
            helpers.updateResMap(_jsonMap, helpers.FAIL, None, cause=e.message, resolution=helpers.REACH_ORA_SUP)
            helpers.testFooter(testName, _testResult, _jsonMap)
            return self.logger.mUpdateResult(_testResult, _jsonMap)

        _clunetwork = utils.getCluNetworkObj()

        # donwIntfs is a list of interfaces which are down for every node, if any
        if aHost not in self.downIntfs:
            self.downIntfs.update({aHost: []})

        # Section to generate report in case no matching network returned by exacloud
        # This is only applicable for new network detection API for X9 and above
        if "ERROR" in utils.getIntfMap():
            cause = ("The runtime state of physical interfaces on host '{}', "
                     "does not match any predefined configuration for ExaCC.").format(aHost)
            resolution = "Please check the status of physical interfaces."
            _testResult = CHK_RESULT.FAIL
            # Log the error from exacloud network detection
            try:
                self.logger.mAppendLog(LOG_TYPE.ERROR,
                                       utils.getIntfMap()["ERROR"][aHost]["CAUSE"] + ' ' +
                                       utils.getIntfMap()["ERROR"][aHost]["ACTION"] + ', ' + aHost, _jsonMap)
            except:
                # In case of missing information from exacloud in the network discovery dictionary
                self.logger.mAppendLog(LOG_TYPE.ERROR, "No network found matching runtime interfaces state for host '{}'.".format(aHost), _jsonMap)
            helpers.updateResMap(_jsonMap, helpers.FAIL, None, cause=cause, resolution=resolution)
        else:
            # Running test for every physical interface of the dom0.
            for _intftype, _intfMap in utils.getIntfMap().items():
                _jsonMap[_intftype] = {}
                for intf in _intfMap["interfaces"]:
                    _jsonMap[_intftype][intf] = {}
                    result = self.mCheckLinks(aHost, _intftype, intf, _clunetwork, utils, helpers, _jsonMap)
                    _status = "PASS" if result else "FAIL"
                    self.logger.mAppendLog(LOG_TYPE.INFO, "Checked interface {} on the host {}, result: {}".format(intf, aHost, _status), _jsonMap)
                    if not result:
                        _testResult = CHK_RESULT.FAIL
                        # add the non-working interface to the list
                        self.downIntfs[aHost].append(intf)

        self.mDisconnectNode(utils.getNodeObj())
        helpers.testFooter(testName, _testResult, _jsonMap)
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    # Helper function to test arping to passed IP
    def mCheckArping(self, intf, ipAddr, cluNetworkObj, aCount=2, aTimeout=8):
        """
        Helper function for mCheckGatewayTest of Network Validation
        :param intf: Interface to arping from
        :param ipAddr: IP Address to check arping to
        :param aCount: no. of successful packets to be received before breaking
        :param aTimeout: time in sec to wait for response
        :return: Bool, True if arp responses received within timeout, False otherwise
        """
        testName = "{}/{}".format(self.__class__.__name__, self.mCheckArping.__name__)

        cmd = "/sbin/arping -c {} -w {} -I {} {}".format(aCount, aTimeout, intf, ipAddr)
        _, _o, _e, _rc = cluNetworkObj.mLogCmd(cmd, "info", testName)

        if _rc == 0:
            return True

        return False

    # Network Validation Test to test the VLAN Ids
    def mCheckVlanIdTest(self, aHost):
        testName = "Vlan ID"
        helpers = self.NetworkValidationHelpers(aHost, self.logger, self)
        helpers.startNWTestLogger(testName)

        _testResult = CHK_RESULT.PASS
        _jsonMap = {"hcDisplayString": set()}

        try:
            utils = helpers.getNetworkValidationUtils(aHost, _jsonMap)
        except HostNotConnectable as e:
            _testResult = CHK_RESULT.FAIL
            helpers.updateResMap(_jsonMap, helpers.FAIL, None, cause=e.message, resolution=helpers.REACH_ORA_SUP)
            helpers.testFooter(testName, _testResult, _jsonMap)
            return self.logger.mUpdateResult(_testResult, _jsonMap)

        _clunetwork = utils.getCluNetworkObj()

        # Skip test in case no matching network returned by exacloud for X9 and above
        if "ERROR" in utils.getIntfMap():
            helpers.skipTest(testName, utils.getNodeObj(), _jsonMap)
            return self.logger.mUpdateResult(CHK_RESULT.FAIL, _jsonMap)

        for _intftype, _intfMap in utils.getIntfMap().items():
            _jsonMap[_intftype] = {}

            # skip tests from backup network based on healthcheck.conf
            if _intftype == BACKUP:
                if utils.ifSkipBackupNwChecks("gateway"):
                    helpers.updateResMap(_jsonMap, helpers.SKIP, _intftype, cause=helpers.BACKUP_NW_SKIP)
                    continue

            # skip tests during network reconfiguration
            if utils.isReconfiguration():
                # skip test from network which is not changing
                if not utils.isNetworkReconfiguring(aHost, _intftype):
                    helpers.updateResMap(_jsonMap, helpers.SKIP, _intftype, cause=helpers.UPDATE_NW_SKIP)
                    continue

                # skip test from network which is changing, but VLAN is not changing
                if "vlantag" not in utils.getUpdateProperties(aHost, _intftype):
                    helpers.updateResMap(_jsonMap, helpers.SKIP, _intftype,
                                         cause="VLAN is not being reconfigured for this network.")
                    continue

            intf = resultIntf = _intfMap["bonding"]
            netobj = _intfMap["netobj"]
            _vlanId = netobj.mGetNetVlanId()
            _jsonMap[_intftype][resultIntf] = {}

            # Mark test PASS if No-VLAN scenario
            if _vlanId in utils.noVlanList:
                self.logger.mAppendLog(LOG_TYPE.INFO, "No VLAN scenario for {} network, marking this test Pass for host {}.".format(_intftype, aHost))
                helpers.updateResMap(_jsonMap, helpers.PASS, _intftype, resultIntf)
                continue

            try:
                filename = intf + "." + datetime.now().strftime('%Y-%m-%d+%H:%M:%S')
                # perform the test on the bonded interface, i.e bondethX
                cmd = "/usr/bin/timeout 10 /usr/sbin/tcpdump -i {} -nn -vv -e vlan > /tmp/{}.lst".format(_intfMap["bonding"], filename)
                _, _o, _e, _rc = _clunetwork.mLogCmd(cmd, "debug", testName)
                # check the count of "vlan <ID>" in grep output
                cmd = "/bin/grep \'vlan {}\' -c /tmp/{}.lst".format(_vlanId, filename)
                _, _o, _e, _rc = _clunetwork.mLogCmd(cmd, "info", testName)

                # This executes when the traffic is there from the control plane.
                # In case no traffic is seen, VLAN is validated using GatewayTest
                if _rc == 0 and int(_o[0]) > 0:
                    helpers.updateResMap(_jsonMap, helpers.PASS, _intftype, resultIntf)
                else:
                    causeStr = "No traffic seen on the interface {} tagged with vlanId {}.".format(intf, _vlanId)
                    helpers.updateResMap(_jsonMap, helpers.FAIL, _intftype, resultIntf,
                                       cause=f"WARNING: {causeStr}", resolution=helpers.CHECK_GW_TEST)
                    self.logger.mAppendLog(LOG_TYPE.WARNING, causeStr, _jsonMap)
                    _testResult = CHK_RESULT.FAIL

                # removing the temporary file, if it is created.
                cmd = "/bin/ls -l /tmp/{}.lst".format(filename)
                _, _o, _e, _rc = _clunetwork.mLogCmd(cmd, "debug", testName)
                if _rc == 0:
                    cmd = "/bin/rm -rf /tmp/{}.lst".format(filename)
                    _, _o, _e, _rc = _clunetwork.mLogCmd(cmd, "debug", testName)
                    if _rc != 0:
                        self.logger.mAppendLog(LOG_TYPE.WARNING, "Failed to remove the temp file {} from host {} in vlanId test".format(filename, aHost), _jsonMap)

            except Exception as e:      # pragma: no cover
                _testResult = CHK_RESULT.FAIL
                helpers.updateResMap(_jsonMap, helpers.FAIL, _intftype, resultIntf,
                                   cause=helpers.INTERNAL_ERROR, resolution=helpers.REACH_ORA_SUP)
                self.logger.mAppendLog(LOG_TYPE.ERROR, "Unable to validate the Vlan configuration for interface {} on the host {}".format(intf, aHost), _jsonMap)
                self.logger.mAppendLog(LOG_TYPE.VERBOSE, "Exception {} occurred, stacktrace:\n {}".format(str(e), traceback.format_exc()))

        self.mDisconnectNode(utils.getNodeObj())
        helpers.testFooter(testName, _testResult, _jsonMap)
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    # Network Validation Test to test the Client and Backup Gateways
    def mCheckGatewayTest(self, aHost):
        testName = "Gateway"
        helpers = self.NetworkValidationHelpers(aHost, self.logger, self)
        helpers.startNWTestLogger(testName)

        _testResult = CHK_RESULT.PASS
        _jsonMap = {"hcDisplayString": set()}

        try:
            utils = helpers.getNetworkValidationUtils(aHost, _jsonMap)
        except HostNotConnectable as e:
            _testResult = CHK_RESULT.FAIL
            helpers.updateResMap(_jsonMap, helpers.FAIL, None, cause=e.message, resolution=helpers.REACH_ORA_SUP)
            helpers.testFooter(testName, _testResult, _jsonMap)
            return self.logger.mUpdateResult(_testResult, _jsonMap)

        # skip GatewayTest from domU for reconfiguration flow
        if utils.isReconfiguration() and utils.isDomU:
            helpers.updateResMap(_jsonMap, helpers.SKIP, None,
                                 cause=f"Please check results for GatewayTest from corresponding dBServer {utils.getDom0forDomU(aHost)}.")
            self.mDisconnectNode(utils.getNodeObj())
            helpers.testFooter("Gateway", _testResult, _jsonMap)
            return self.logger.mUpdateResult(_testResult, _jsonMap)

        _clunetwork = utils.getCluNetworkObj()
        skipOtherIntfs = {CLIENT: False, BACKUP: False, DR: False}

        # Skip test in case no matching network returned by exacloud for X9 and above
        if "ERROR" in utils.getIntfMap():
            helpers.skipTest(testName, utils.getNodeObj(), _jsonMap)
            return self.logger.mUpdateResult(CHK_RESULT.FAIL, _jsonMap)

        for _intftype, _intfMap in utils.getIntfMap().items():

            _jsonMap[_intftype] = {}
            # skip tests from backup network based on healthcheck.conf
            if _intftype == BACKUP:
                if utils.ifSkipBackupNwChecks("gateway"):
                    helpers.updateResMap(_jsonMap, helpers.SKIP, _intftype, cause=helpers.BACKUP_NW_SKIP)
                    continue

            if (utils.isReconfiguration() and
                    utils.isDom0 and
                    not utils.isNetworkReconfiguring(aHost, _intftype)):
                helpers.updateResMap(_jsonMap, helpers.SKIP, _intftype, cause=helpers.UPDATE_NW_SKIP)
                continue

            for intf in _intfMap["interfaces"]:
                resultIntf = intf
                netobj = _intfMap["netobj"]
                _ipaddr = netobj.mGetNetIpAddr()
                _gateway = netobj.mGetNetGateWay()

                # interface needs to be configured only if running host is dom0
                if utils.isDom0:
                    _intf_name = _clunetwork.interfaceMap[_intftype][intf]

                    if _clunetwork.useBridge[_intftype]:
                        resultIntf = _intfMap["bridge"]
                        if skipOtherIntfs[_intftype]:
                            continue
                        else:
                            skipOtherIntfs[_intftype] = True
                    _jsonMap[_intftype][resultIntf] = {}

                    # skip test for a down physical interface
                    if aHost in self.downIntfs and intf in self.downIntfs[aHost]:
                        self.logger.mAppendLog(LOG_TYPE.WARNING,
                                               "Skipping Gateway test from down interface {} on the host {}.".format(intf, aHost))
                        helpers.updateResMap(_jsonMap, helpers.SKIP, _intftype, resultIntf,
                                             cause=helpers.DOWN_INTF_SKIP)
                        continue

                    _ret = _clunetwork.mConfigureInterface(intf, netobj)
                    if not _ret:
                        helpers.updateResMap(_jsonMap, helpers.FAIL, _intftype, resultIntf,
                                           cause=helpers.INTERNAL_ERROR, resolution=helpers.REACH_ORA_SUP)
                        self.logger.mAppendLog(LOG_TYPE.ERROR, "Failed to configure the interface {} on the host {}".format(_intf_name, aHost), _jsonMap)
                        # Un-configure interface
                        _clunetwork.mUnConfigureInterface(intf, netobj)
                        _testResult = CHK_RESULT.FAIL
                        continue

                elif utils.isDomU:
                    _intf_name = intf
                    _jsonMap[_intftype][resultIntf] = {}

                # If we configure the interface then proceed with the actual Gateway test.
                try:
                    _gwStatus = self.mCheckArping(_intf_name, _gateway, _clunetwork)
                    # gateway arping is not successful.
                    if not _gwStatus:
                        _status = "FAIL"
                        causeStr = "Gateway {} is not accessible from source {} through {}.".format(_gateway, _ipaddr, _intf_name)
                        helpers.updateResMap(_jsonMap, helpers.FAIL, _intftype, resultIntf,
                                           cause=causeStr, resolution=helpers.CHECK_NW_ENTITIES)
                        self.logger.mAppendLog(LOG_TYPE.ERROR, causeStr, _jsonMap)
                        _testResult = CHK_RESULT.FAIL
                    # gateway arping is successful
                    else:
                        _status = "PASS"
                        helpers.updateResMap(_jsonMap, helpers.PASS, _intftype, resultIntf)

                    self.logger.mAppendLog(LOG_TYPE.INFO, "Reachability for gateway {} from host {} through {}, result: {}".format(_gateway, aHost, _intf_name, _status))

                except Exception as e:      # pragma: no cover
                    _testResult = CHK_RESULT.FAIL
                    helpers.updateResMap(_jsonMap, helpers.FAIL, _intftype, resultIntf,
                                       cause=helpers.INTERNAL_ERROR, resolution=helpers.REACH_ORA_SUP)
                    self.logger.mAppendLog(LOG_TYPE.ERROR, "Unable to validate the Gateways for interface {} on the host {}".format(intf, aHost), _jsonMap)
                    self.logger.mAppendLog(LOG_TYPE.VERBOSE, "Exception {} occurred, stacktrace:\n {}".format(str(e), traceback.format_exc()))

                if utils.isDom0:
                    _clunetwork.mUnConfigureInterface(intf, netobj)

        self.mDisconnectNode(utils.getNodeObj())
        helpers.testFooter(testName, _testResult, _jsonMap)
        result = self.logger.mUpdateResult(_testResult, _jsonMap)
        self.intermediateResult.update({self.mCheckGatewayTest.__name__: result})
        return result

    def mDnsdig(self, hostname, checkset, dnsIp, cluNetworkObj, helpers):
        """
        :param hostname: hostname FQDN / IP address (for rev lookup)
        :param checkset: set of hostname/IPs from the XML to be compared against from the server output
        :param dnsIp: DNS server IP
        :return: ( Bool, Status_Code, extra_set, absent_set)
            STATUS CODES :
            0 : success
            1 : unreachable
            2 : dns configuration issue (wrong/missing entries)
            3 : exception
        """
        testName = "{}/{}".format(self.__class__.__name__, self.mDnsdig.__name__)
        serverResultSet = set()
        extraSet = set()
        unreachableMsg = "no servers could be reached"

        _reverse = False
        if helpers.is_valid_ipv4_address(hostname) or helpers.is_valid_ipv6_address(hostname):
            _reverse = True

        missedSet = copy.deepcopy(checkset)
        if _reverse:
            cmd = "/usr/bin/dig +noall +answer -x {} @{}".format(hostname, dnsIp)
        else:
            cmd = "/usr/bin/dig +noall +answer {} @{}".format(hostname, dnsIp)
        try:
            _, _out, _err, _rc = cluNetworkObj.mLogCmd(cmd, "info", testName)
            digOut = "Lookup of {} yields {} from DNS {}".format(hostname, _out, dnsIp)
            self.logger.mAppendLog(LOG_TYPE.DEBUG, digOut)
            if _out:
                for _line in _out:
                    if unreachableMsg in _line:
                        return False, 1, missedSet, extraSet
                    # this will split the result in the following format
                    # ['query name/IP', 'TTL', 'Class', 'Type(A/PTR etc)', 'answer name/IP']
                    _line = _line.split()
                    if _reverse:
                        # if there are CNAME records in answer, skip those and only select PTR record
                        if _line[3] == "PTR":
                            serverResultSet.add(_line[4][:-1].lower())
                    else:
                        # if there are CNAME records in answer, skip those and only select A record
                        if _line[3] == "A" or _line[3] == "AAAA":
                            serverResultSet.add(_line[4])
                extraSet = copy.deepcopy(serverResultSet)
            else:
                return False, 2, missedSet, extraSet

            missedSet = missedSet.difference(serverResultSet)
            extraSet = extraSet.difference(checkset)

            if missedSet.__len__() != 0 or extraSet.__len__() != 0:
                return False, 2, missedSet, extraSet
        except Exception:
            return False, 3, missedSet, extraSet

        return True, 0, missedSet, extraSet

    def mReturnHostnameIpMapping(self, _eBox, host, dom0domUSpecificMapping=False, drNet=False):
        """
        Helper function that reads the XML and extracts Client/Backup/VIP/Scan IPs for all dom0domU pairs
        :param _eBox: cluControl Obj
        :param host: dom0 FQDN
        :param dom0domUSpecificMapping: Bool, if True, extract client/backup/vip info only specific to the dom0
        :param drNet: Boolean specifying if DR network is configured
        :return: dictionary of hostname-IP mapping, divided by types (Client/Backup/VIP/Scan)
        """
        _hostname_ip_pairs = {"ClientIPs": {}, "BackupIPs": {}, "ScanIPs": {}, "VIPs": {}}

        if drNet:
            _hostname_ip_pairs.update({"drIPs": {}, "drVIPs": {}, "drScanIPs": {}})

        _scans = _eBox.mGetScans()
        _machines = _eBox.mGetMachines()
        _networks = _eBox.mGetNetworks()
        _clusters = _eBox.mGetClusters()
        _cluid_list = _clusters.mGetClusters()

        for _dom0, _domU in _eBox.mReturnDom0DomUPair():
            # only fetch IP's corresponding to the specific dom0-domU pair
            # if dom0domUSpecificMapping is True
            if dom0domUSpecificMapping:
                if host not in _dom0:
                    continue

            _domU_mac = _machines.mGetMachineConfig(_domU)
            _domU_mac_id = _domU_mac.mGetMacId()
            _domU_networks = _domU_mac.mGetMacNetworks()

            _client_domain_name = None
            _dr_domain_name = None
            # Fetch Client / Backup IP's
            for _net_id in _domU_networks:
                if _net_id.endswith("_client") or _net_id.endswith("_backup") \
                        or (drNet and _net_id.endswith("_other")):
                    _net_config = _networks.mGetNetworkConfig(_net_id)

                    if _net_config.mGetNetDomainName() in _net_config.mGetNetHostName():
                        _hostname_full = _net_config.mGetNetHostName()
                    else:
                        _hostname_full = _net_config.mGetNetHostName() + "." + _net_config.mGetNetDomainName()

                    # convert to lower for case-insensitive DNS Lookup
                    _hostname_full = _hostname_full.lower()
                    if _net_config.mGetNetType() == CLIENT:
                        _client_domain_name = _net_config.mGetNetDomainName()
                        _hostname_ip_pairs["ClientIPs"][_hostname_full] = _net_config.mGetNetIpAddr()
                    elif _net_config.mGetNetType() == BACKUP:
                        _hostname_ip_pairs["BackupIPs"][_hostname_full] = _net_config.mGetNetIpAddr()
                    elif _net_config.mGetNetType() == OTHER:
                        _dr_domain_name = _net_config.mGetNetDomainName()
                        _hostname_ip_pairs["drIPs"][_hostname_full] = _net_config.mGetNetIpAddr()

            for _clu_id in _cluid_list:
                _clu_obj = _clusters.mGetCluster(_clu_id)
                _scan_ids = _clu_obj.mGetCluScans()

                # Fetch cluster SCAN IP's
                for _scanId in _scan_ids:
                    _scan_obj = _scans.mGetScan(_scanId)
                    if _client_domain_name in _scan_obj.mGetScanName():
                        _scan_fqdn = _scan_obj.mGetScanName()
                    else:
                        _scan_fqdn = _scan_obj.mGetScanName() + "." + _client_domain_name

                    # convert to lower for case-insensitive DNS Lookup
                    _hostname_ip_pairs["ScanIPs"][_scan_fqdn.lower()] = _scan_obj.mGetScanIps()

                # Fetch cluster VIP's
                _clu_vip_dict = _clu_obj.mGetCluVips()
                for _vip_id in _clu_vip_dict:
                    _vip_obj = _clu_vip_dict[_vip_id]
                    # add only vip corresponding to the specific dom0-domU pair
                    if _domU_mac_id not in _vip_obj.mGetCVIPMachines():
                        continue

                    if _vip_obj.mGetCVIPDomainName() in _vip_obj.mGetCVIPName():
                        _vip_fqdn = _vip_obj.mGetCVIPName()
                    else:
                        _vip_fqdn = _vip_obj.mGetCVIPName() + "." + _vip_obj.mGetCVIPDomainName()

                    # convert to lower for case-insensitive DNS Lookup
                    _hostname_ip_pairs["VIPs"][_vip_fqdn.lower()] = _vip_obj.mGetCVIPAddr()

            if drNet:
                # Fetch DR VIP's
                drVipObj = _eBox.mGetDRVips()[_domU]
                if drVipObj.mGetDRVIPDomainName() not in drVipObj.mGetDRVIPName():
                    _hostname_full = drVipObj.mGetDRVIPName().strip() + '.' + drVipObj.mGetDRVIPDomainName().strip()
                else:
                    _hostname_full = drVipObj.mGetDRVIPName().strip()
                _hostname_ip_pairs["drVIPs"][_hostname_full.lower()] = drVipObj.mGetDRVIPAddr()
                # Fetch DR Scan's
                drScanObj = _eBox.mGetDRScans()
                if _dr_domain_name not in drScanObj.mGetScanName():
                    _hostname_full = drScanObj.mGetScanName().strip() + '.' + _dr_domain_name
                else:
                    _hostname_full = drScanObj.mGetScanName().strip()
                _hostname_ip_pairs["drScanIPs"][_hostname_full.lower()] = drScanObj.mGetScanIpsList()

        return _hostname_ip_pairs

    # Network Validation Test to query customer DNS Servers
    def mCheckDnsTest(self, aHost):
        testName = "DNS"
        helpers = self.NetworkValidationHelpers(aHost, self.logger, self)
        helpers.startNWTestLogger(testName)

        _testResult = CHK_RESULT.PASS
        _jsonMap = {"hcDisplayString": set()}

        try:
            utils = helpers.getNetworkValidationUtils(aHost, _jsonMap)
        except HostNotConnectable as e:
            _testResult = CHK_RESULT.FAIL
            helpers.updateResMap(_jsonMap, helpers.FAIL, None, cause=e.message, resolution=helpers.REACH_ORA_SUP)
            helpers.testFooter(testName, _testResult, _jsonMap)
            return self.logger.mUpdateResult(_testResult, _jsonMap)

        _clunetwork = utils.getCluNetworkObj()
        skipOtherIntfs = {CLIENT: False, BACKUP: False, DR: False}

        # Skip test in case no matching network returned by exacloud for X9 and above
        if "ERROR" in utils.getIntfMap():
            helpers.skipTest(testName, utils.getNodeObj(), _jsonMap)
            return self.logger.mUpdateResult(CHK_RESULT.FAIL, _jsonMap)

        if utils.isReconfiguration():
            skip = False
            host = aHost if utils.isDom0 else utils.getDom0forDomU(aHost)

            # skip test if network is being reconfigured, but none of the DNS servers,
            # client gateway, or any hostnames/IPs are changing
            if (not utils.anyFqdnIpChange()
                    and not utils.getServiceChange('dns')
                    and not 'gateway' in utils.getUpdateProperties(host, 'client')):
                helpers.updateResMap(_jsonMap, helpers.SKIP, None,
                                     cause="None of the DNS servers, client gateway, or any hostnames/IPs are being changed for this cluster.")
                skip = True

            # skip DNS test from domU if client network changing
            if utils.isNetworkReconfiguring(host, 'client'):
                if utils.isDomU:
                    helpers.updateResMap(_jsonMap, helpers.SKIP, None,
                                         cause=f"Client network changes identified for {aHost}. "
                                               f"Please check results for DnsTest from corresponding dBServer {utils.getDom0forDomU(aHost)}.")
                    skip = True
            # skip DNS test from dom0 if client network NOT changing
            else:
                if utils.isDom0:
                    helpers.updateResMap(_jsonMap, helpers.SKIP, None,
                                         cause=f"Client network unchanged for {aHost}. "
                                               f"Please check results for DnsTest from corresponding VM {utils.getDomUforDom0(aHost)}.")
                    skip = True

            if skip:
                self.mDisconnectNode(utils.getNodeObj())
                helpers.testFooter("DNS", _testResult, _jsonMap)
                return self.logger.mUpdateResult(_testResult, _jsonMap)

        # Fetch DNS Servers
        _dnsServers = []
        for _, _domU in self.mGetEbox().mReturnDom0DomUPair():
            _machines = self.mGetEbox().mGetMachines()
            _domU_mac = _machines.mGetMachineConfig(_domU)
            _dnsServers = _domU_mac.mGetDnsServers()
            break

        _hostname_ip_pairs = self.mReturnHostnameIpMapping(self.mGetEbox(), aHost, drNet=utils.isDrNetConfigured())
        _resolve_dict_fwd = {}
        _resolve_dict_rev = {}

        # Populating the forward and reverse dictionaries
        for iptype in _hostname_ip_pairs:
            _resolve_dict_fwd[iptype] = {}
            _resolve_dict_rev[iptype] = {}
            if iptype == "ScanIPs" or iptype == "drScanIPs":
                for host in _hostname_ip_pairs[iptype]:
                    _resolve_dict_fwd[iptype][host] = set(_hostname_ip_pairs[iptype][host])
                    for ip in _hostname_ip_pairs[iptype][host]:
                        _resolve_dict_rev[iptype][ip] = set((host,))
            else:
                for key in _hostname_ip_pairs[iptype]:
                    _resolve_dict_fwd[iptype][key] = set((_hostname_ip_pairs[iptype][key],))
                    _resolve_dict_rev[iptype][_hostname_ip_pairs[iptype][key]] = set((key,))

        _dns_status_dict = {}
        for _dns in _dnsServers:
            _dns_status_dict[_dns] = False

        self.logger.mAppendLog(LOG_TYPE.INFO, "Forward Entry Pairs to be resolved : {} \n".format(_resolve_dict_fwd))
        self.logger.mAppendLog(LOG_TYPE.INFO, "Reverse Entry Pairs to be resolved : {} \n".format(_resolve_dict_rev))

        # adding sleep to avoid hitting CISCO Rogue EP issue (default 4 flaps in 60 Seconds)
        rogue_ep_sleep = int(utils.getParam("rogue_ep_sleep"))
        if rogue_ep_sleep > 0:
            self.logger.mAppendLog(LOG_TYPE.INFO,
                                   f"Custom timeout of \'{rogue_ep_sleep}\' seconds found from healthcheck config. Sleeping for \'{rogue_ep_sleep}\' seconds.")
            sleep(rogue_ep_sleep)

        # Loop over all interfaces
        for _intftype, _intfMap in utils.getIntfMap().items():
            # This test needs to be done only on Client interfaces
            if _intftype != CLIENT:
                continue

            _jsonMap[_intftype] = {}

            # skip test from dom0 if network 'intftype' not being reconfigured
            if (utils.isReconfiguration() and
                    utils.isDom0 and
                    not utils.isNetworkReconfiguring(aHost, _intftype)):
                helpers.updateResMap(_jsonMap, helpers.SKIP, _intftype, cause=helpers.UPDATE_NW_SKIP)
                continue

            for intf in _intfMap["interfaces"]:
                resultIntf = intf
                netobj = _intfMap["netobj"]
                _ipmask = netobj.mGetNetMask()
                _ipaddr = netobj.mGetNetIpAddr()
                _vlanId = netobj.mGetNetVlanId()
                _gateway = netobj.mGetNetGateWay()

                # interface needs to be configured only if running host is dom0
                if utils.isDom0:
                    if _clunetwork.useBridge[_intftype]:
                        resultIntf = _intfMap["bridge"]
                        if skipOtherIntfs[_intftype]:
                            continue
                        else:
                             skipOtherIntfs[_intftype] = True
                    _jsonMap[_intftype][resultIntf] = {}
                    _intf_name = _clunetwork.interfaceMap[_intftype][intf]

                    # skip test for a down physical interface
                    if aHost in self.downIntfs and intf in self.downIntfs[aHost]:
                        self.logger.mAppendLog(LOG_TYPE.WARNING,
                                               "Skipping DNS test from down interface {} on the host {}.".format(intf, aHost))
                        helpers.updateResMap(_jsonMap, helpers.SKIP, _intftype, resultIntf,
                                             cause=helpers.DOWN_INTF_SKIP)
                        continue

                    _ret = _clunetwork.mConfigureInterface(intf, netobj)
                    if not _ret:
                        helpers.updateResMap(_jsonMap, helpers.FAIL, _intftype, resultIntf,
                                           cause=helpers.INTERNAL_ERROR, resolution=helpers.REACH_ORA_SUP)
                        self.logger.mAppendLog(LOG_TYPE.ERROR, "Failed to configure the interface {} on the host {}".format(_intf_name, aHost), _jsonMap)
                        # Un configure interface
                        _clunetwork.mUnConfigureInterface(intf, netobj)
                        _testResult = CHK_RESULT.FAIL
                        continue

                elif utils.isDomU:
                    _intf_name = intf
                    _jsonMap[_intftype][resultIntf] = {}

                # This dict has info regarding reachability of the DNS from a particular interface
                # This is important for checking latency issues wrt a particular interface
                _dns_reach_info = {}
                for _dns in _dnsServers:
                    _dns_reach_info[_dns] = False

                # Loop over all DNS Servers
                for _dns in _dnsServers:
                    _jsonMap[_intftype][resultIntf][_dns] = {}
                    _dnsSameNwFlag = helpers.checkifSameNw(_dns, _ipaddr, _ipmask)

                    # Skip test if gateway not reachable and NTP is not in the same subnet
                    if not helpers.isGatewayReachable(self.intermediateResult, _intftype, resultIntf) and not _dnsSameNwFlag:
                        causeStr = f"Gateway is not reachable from the interface {resultIntf} and " \
                                   f"DNS IP {_dns} not in the same subnet as the {_intftype} network."
                        self.logger.mAppendLog(LOG_TYPE.WARNING, f"Skipping DNS test for server {_dns} on host {aHost}. {causeStr}")
                        _testResult = CHK_RESULT.FAIL
                        helpers.updateResMap(_jsonMap, helpers.SKIP, _intftype, resultIntf, _dns, cause=causeStr)
                        continue

                    _latency_flag = False
                    try:
                        # route entries only need to be added from configured interface on dom0
                        if utils.isDom0:
                            if not _dnsSameNwFlag:
                                _route_ret = _clunetwork.mAddRouteEntry(_intf_name, _dns, _gateway)
                                if not _route_ret:
                                    _testResult = CHK_RESULT.FAIL
                                    helpers.updateResMap(_jsonMap, helpers.FAIL, _intftype, resultIntf, _dns,
                                                       cause=helpers.INTERNAL_ERROR, resolution=helpers.REACH_ORA_SUP)
                                    self.logger.mAppendLog(LOG_TYPE.ERROR, "Failed to add routing entry for {} from the interface {} on the host {}".format(_dns, _intf_name, aHost), _jsonMap)
                                    _clunetwork.mDeleteRouteEntry(_intf_name, _dns, _gateway)
                                    continue
                            else:
                                self.logger.mAppendLog(LOG_TYPE.INFO, "DNS {} is in the same subnet as the client network, hence skipping adding route through the gateway".format(_dns))

                        _digtest_fwd = True
                        _digtest_rev = True
                        _fwd_pairs = {}
                        _rev_pairs = {}

                        if not _dns_status_dict[_dns]:
                            _fwd_pairs = _resolve_dict_fwd
                            _rev_pairs = _resolve_dict_rev
                        else:
                            # If a DNS has been marked reachable from other interfaces,
                            # just do a resolve of Client IPs to check reachability only
                            _fwd_pairs = {"ClientIPs": _resolve_dict_fwd["ClientIPs"]}
                            _rev_pairs = {}

                        if utils.isDom0:
                            _resolve_dicts = [_fwd_pairs, _rev_pairs]
                        elif utils.isDomU:
                            # for revalidation after LACP we just need to check for reachability,
                            # hence lookup performed for only Client hostnames
                            if utils.isReValidation():
                                _resolve_dicts = [{"ClientIPs": _fwd_pairs["ClientIPs"]}]
                            # for reconfiguration perform checks for all hostname/IPs
                            if utils.isReconfiguration():
                                _resolve_dicts = [_fwd_pairs, _rev_pairs]
                                _resolve_dicts = [_fwd_pairs, _rev_pairs]

                        # Loop for forward and Reverse Lookup Dictionaries
                        for _dict in _resolve_dicts:
                            _reverse = False
                            for iptype in _dict:
                                for entry in _dict[iptype]:
                                    if helpers.is_valid_ipv4_address(entry) or helpers.is_valid_ipv6_address(entry):
                                        _reverse = True
                                        break

                            # Skip reverse lookups if DNS not reachable for any fwd lookup
                            if _reverse and not _dns_reach_info[_dns]:
                                continue

                            # Loop over every hostname-IP pair
                            for iptype in _dict:

                                # Skip remaining fwd lookups if DNS not reachable for any of Client/Backup hostname
                                if iptype not in ["ClientIPs", "BackupIPs"] and not _dns_reach_info[_dns]:
                                    continue

                                for entry in _dict[iptype]:
                                    _jsonMap[_intftype][resultIntf][_dns][entry] = {}
                                    _absent_set = set()
                                    _extra_set = set()

                                    # Option to skip resolution for backup hostnames / IPs
                                    if iptype == "BackupIPs":
                                        if utils.ifSkipBackupNwChecks("dns"):
                                            helpers.updateResMap(_jsonMap, helpers.SKIP, _intftype, resultIntf, _dns, entry,
                                                               cause="DNS Lookup of backup network hosts/IP's configured to skip from healthcheck.conf")
                                            continue

                                    _digtest_local, _cause, _absent_set, _extra_set = self.mDnsdig(entry, _dict[iptype][entry], _dns, _clunetwork, helpers)

                                    if _digtest_local is True:
                                        helpers.updateResMap(_jsonMap, helpers.PASS, _intftype, resultIntf, _dns, entry)
                                        if not _dns_status_dict[_dns]:
                                            _dns_status_dict[_dns] = True
                                        _dns_reach_info[_dns] = True
                                    else:
                                        if _reverse:
                                            _digtest_rev = False
                                        else:
                                            _digtest_fwd = False

                                        # DNS Unreachable
                                        if _cause == 1:
                                            failstr = "DNS {} is not accessible from source {} with Vlan id {} using gateway {}.".format(_dns, _ipaddr, _vlanId, _gateway)
                                            resolstr = helpers.CHECK_NW_ENTITIES
                                            if _dns_reach_info[_dns] is True:
                                                _latency_flag = True

                                        # Mismatch in entries
                                        elif _cause == 2:
                                            abs_failstr = ""
                                            extra_failstr = ""
                                            _dns_reach_info[_dns] = True
                                            if _absent_set.__len__() != 0:
                                                _abs_str = ""
                                                for item in _absent_set:
                                                    _abs_str = _abs_str + item + ", "
                                                _abs_str = _abs_str[:-2]
                                                if _reverse:
                                                    abs_failstr = "Missing reverse DNS entry(ies) {} for {} in the DNS server {}.".format(_abs_str, entry, _dns)
                                                else:
                                                    abs_failstr = "Missing DNS entry(ies) {} for {} in the DNS server {}.".format(_abs_str, entry, _dns)
                                            if _extra_set.__len__() != 0:
                                                _extra_str = ""
                                                for item in _extra_set:
                                                    _extra_str = _extra_str + item + ", "
                                                _extra_str = _extra_str[:-2]
                                                if _reverse:
                                                    extra_failstr = "Wrong reverse DNS entry(ies) {} found for {} in the DNS server {}.".format(_extra_str, entry, _dns)
                                                else:
                                                    extra_failstr = "Wrong DNS entry(ies) {} found for {} in the DNS server {}.".format(_extra_str, entry, _dns)

                                            failstr = abs_failstr + " " + extra_failstr
                                            resolstr = "Please update the DNS Server with appropriate entry(ies)."

                                        # Some other reason for failure
                                        else:
                                            failstr = helpers.INTERNAL_ERROR
                                            resolstr = helpers.REACH_ORA_SUP

                                        helpers.updateResMap(_jsonMap, helpers.FAIL, _intftype, resultIntf, _dns, entry,
                                                           cause=failstr, resolution=resolstr)

                                    _status = "PASS" if _digtest_local else "FAIL"
                                    if _reverse:
                                        self.logger.mAppendLog(LOG_TYPE.INFO, "Reverse DNS lookup for {} in DNS {} from host {} through {}, result: {}".format(entry, _dns, aHost, _intf_name, _status))
                                    else:
                                        self.logger.mAppendLog(LOG_TYPE.INFO, "DNS lookup for {} in DNS {} from host {} through {}, result: {}".format(entry, _dns, aHost, _intf_name, _status))

                        if _latency_flag:
                            latencystr = "DNS server {} is not reachable sometimes through the interface {}. Please check the network latency.".format(_dns, intf)
                            _jsonMap["hcDisplayString"].add(latencystr)

                        if not _digtest_fwd or not _digtest_rev:
                            self.logger.mAppendLog(LOG_TYPE.ERROR, "Failed to resolve all entries for DNS {} from the host {} through {}".format(_dns, aHost, _intf_name), _jsonMap)
                            _testResult = CHK_RESULT.FAIL

                    except Exception as e:      # pragma: no cover
                        _testResult = CHK_RESULT.FAIL
                        helpers.updateResMap(_jsonMap, helpers.FAIL, _intftype, resultIntf, _dns,
                                           cause=helpers.INTERNAL_ERROR, resolution=helpers.REACH_ORA_SUP)
                        self.logger.mAppendLog(LOG_TYPE.ERROR, "Unable to validate the DNS Servers for interface {} on the host {}".format(intf, aHost), _jsonMap)
                        self.logger.mAppendLog(LOG_TYPE.VERBOSE, "Exception {} occurred, stacktrace:\n {}".format(str(e), traceback.format_exc()))

                    if utils.isDom0 and not _dnsSameNwFlag:
                        _clunetwork.mDeleteRouteEntry(_intf_name, _dns, _gateway)

                if utils.isDom0:
                    _clunetwork.mUnConfigureInterface(intf, netobj)

        self.mDisconnectNode(utils.getNodeObj())
        helpers.testFooter(testName, _testResult, _jsonMap)
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    def checkNodeOLversion(self, cluNetworkObj):
        """
        :param cluNetworkObj: ovm/clunetwork.py Obj
        :return: OL version of node in format OL(6/7)
        """
        testName = "{}/{}".format(self.__class__.__name__, self.checkNodeOLversion.__name__)

        hostOS = None
        os_cmd = "/bin/uname -r"
        _, _out, _err, _rc = cluNetworkObj.mLogCmd(os_cmd, "debug", testName)

        if _rc == 0 and _out:
            # extract el?uek from output like el8uek
            # from output of the form 5.4.17-2136.312.3.4.el8uek.x86_64
            uekStr = _out[0].strip().split('.')[-2]
            hostOS = "OL" + uekStr[2]

        return hostOS

    # Helper function for mCheckNtpTest of Network Validation
    def mNtpTest(self, hostOS, ntpIp, cluNetworkObj):
        """
        :param hostOS: OL6/OL7 in string format
        :param ntpIp: NTP server IP
        :return: Bool, True if NTP server responds to query, else False
        """
        testName = "NTP"

        if "OL6" in hostOS:
            # ntpd is the default NTP client for OL6
            cmd = '/usr/sbin/ntpdate -q {}'.format(ntpIp)
        else:
            # chronyd is the default NTP client for OL7/OL8
            cmd = "/usr/sbin/chronyd -Q 'server {} iburst' 'maxdistance 16.0'".format(ntpIp)

        _, _o, _e, _rc = cluNetworkObj.mLogCmd(cmd, "info", testName)
        if _rc == 0:
            return True

        return False

    # Network Validation Test to query customer NTP Servers
    def mCheckNtpTest(self, aHost):
        testName = "NTP"
        helpers = self.NetworkValidationHelpers(aHost, self.logger, self)
        helpers.startNWTestLogger(testName)

        _jsonMap = {"hcDisplayString": set()}
        _testResult = CHK_RESULT.PASS

        try:
            utils = helpers.getNetworkValidationUtils(aHost, _jsonMap)
        except HostNotConnectable as e:
            _testResult = CHK_RESULT.FAIL
            helpers.updateResMap(_jsonMap, helpers.FAIL, None, cause=e.message, resolution=helpers.REACH_ORA_SUP)
            helpers.testFooter(testName, _testResult, _jsonMap)
            return self.logger.mUpdateResult(_testResult, _jsonMap)

        if utils.isReconfiguration():
            skip = False
            host = aHost if utils.isDom0 else utils.getDom0forDomU(aHost)

            # skip test if network is being reconfigured, but neither NTP servers nor client gateway changing
            if (not utils.getServiceChange('ntp') and
                    not 'gateway' in utils.getUpdateProperties(host, 'client')):
                helpers.updateResMap(_jsonMap, helpers.SKIP, None,
                                     cause="Neither of the NTP servers nor client gateway is being changed for this cluster.")
                skip = True

            # skip NTP test from domU if client network changing
            if utils.isNetworkReconfiguring(host, 'client'):
                if utils.isDomU:
                    helpers.updateResMap(_jsonMap, helpers.SKIP, None,
                                         cause=f"Client network changes identified for {aHost}. "
                                               f"Please check results for NtpTest from corresponding dBServer {utils.getDom0forDomU(aHost)}.")
                    skip = True

            # skip NTP test from dom0 if client network NOT changing
            else:
                if utils.isDom0:
                    helpers.updateResMap(_jsonMap, helpers.SKIP, None,
                                         cause=f"Client network unchanged for {aHost}. "
                                               f"Please check results for NtpTest from corresponding VM {utils.getDomUforDom0(aHost)}.")
                    skip = True

            if skip:
                self.mDisconnectNode(utils.getNodeObj())
                helpers.testFooter("NTP", _testResult, _jsonMap)
                return self.logger.mUpdateResult(_testResult, _jsonMap)

        _clunetwork = utils.getCluNetworkObj()

        # Skip test in case no matching network returned by exacloud for X9 and above
        if "ERROR" in utils.getIntfMap():
            helpers.skipTest(testName, utils.getNodeObj(), _jsonMap)
            return self.logger.mUpdateResult(CHK_RESULT.FAIL, _jsonMap)

        # Fetch NTP Servers
        _ntpServers = []
        for _, _domU in self.mGetEbox().mReturnDom0DomUPair():
            _machines = self.mGetEbox().mGetMachines()
            _domU_mac = _machines.mGetMachineConfig(_domU)
            _ntpServers = _domU_mac.mGetNtpServers()
            break

        # determine host OS
        _hostOS = self.checkNodeOLversion(_clunetwork)
        if _hostOS is None:
            _testResult = CHK_RESULT.FAIL
            helpers.updateResMap(_jsonMap, helpers.FAIL, None, cause=helpers.INTERNAL_ERROR, resolution=helpers.REACH_ORA_SUP)
            self.logger.mAppendLog(LOG_TYPE.ERROR, "Could not identify the OL version for host {}.".format(aHost))
        else:
            self.logger.mAppendLog(LOG_TYPE.DEBUG, "Host {} OS identified as {}.".format(aHost, _hostOS))
            # Begin the actual NTP test
            # Initialise the map of interfaces to handle NTP rate limiting
            intf_count = {}
            for _ntp in _ntpServers:
                intf_count[_ntp] = None

            skipOtherIntfs = {CLIENT: False, BACKUP: False, DR: False}

            for _intftype, _intfMap in utils.getIntfMap().items():
                # This test needs to be done only on Client interfaces
                if _intftype != CLIENT:
                    continue

                _jsonMap[_intftype] = {}
                # skip test from dom0 if network '_intftype' not being reconfigured
                if utils.isReconfiguration():
                    if utils.isDom0 and not utils.isNetworkReconfiguring(aHost, _intftype):
                        helpers.updateResMap(_jsonMap, helpers.SKIP, _intftype, cause=helpers.UPDATE_NW_SKIP)
                        continue

                for intf in _intfMap["interfaces"]:
                    resultIntf = intf
                    netobj = _intfMap["netobj"]

                    _ipmask = netobj.mGetNetMask()
                    _ipaddr = netobj.mGetNetIpAddr()
                    _vlanId = netobj.mGetNetVlanId()
                    _gateway = netobj.mGetNetGateWay()

                    # interface needs to be configured only if running host is dom0
                    if utils.isDom0:
                        _intf_name = _clunetwork.interfaceMap[_intftype][intf]

                        if _clunetwork.useBridge[_intftype]:
                            resultIntf = _intfMap["bridge"]
                            if skipOtherIntfs[_intftype]:
                                continue
                            else:
                                skipOtherIntfs[_intftype] = True
                        _jsonMap[_intftype][resultIntf] = {}

                        # skip test for a down physical interface
                        if aHost in self.downIntfs and intf in self.downIntfs[aHost]:
                            self.logger.mAppendLog(LOG_TYPE.WARNING,
                                                   "Skipping NTP test from down interface {} on the host {}.".format(intf, aHost))
                            helpers.updateResMap(_jsonMap, helpers.SKIP, _intftype, resultIntf,
                                                 cause=helpers.DOWN_INTF_SKIP)
                            continue

                        _ret = _clunetwork.mConfigureInterface(intf, netobj)
                        if not _ret:
                            _testResult = CHK_RESULT.FAIL
                            helpers.updateResMap(_jsonMap, helpers.FAIL, _intftype, resultIntf,
                                               cause=helpers.INTERNAL_ERROR, resolution=helpers.REACH_ORA_SUP)
                            self.logger.mAppendLog(LOG_TYPE.ERROR, "Failed to configure the interface {} on the host {}".format(_intf_name, aHost), _jsonMap)
                            # Un-configure interface
                            _clunetwork.mUnConfigureInterface(intf, netobj)
                            continue

                    elif utils.isDomU:
                        _intf_name = intf
                        _jsonMap[_intftype][resultIntf] = {}

                    # loop over all NTP servers
                    for _ntp in _ntpServers:
                        _jsonMap[_intftype][resultIntf][_ntp] = {}
                        _ntpSameNwFlag = helpers.checkifSameNw(_ntp, _ipaddr, _ipmask)

                        # Skip test if gateway not reachable and NTP is not in the same subnet
                        if not helpers.isGatewayReachable(self.intermediateResult, _intftype, resultIntf) and not _ntpSameNwFlag:
                            causeStr = f"Gateway is not reachable from the interface {resultIntf} and "\
                                       f"NTP IP {_ntp} not in the same subnet as the {_intftype} network."
                            self.logger.mAppendLog(LOG_TYPE.WARNING, f"Skipping NTP test for server {_ntp} on host {aHost}. {causeStr}")
                            _testResult = CHK_RESULT.FAIL
                            helpers.updateResMap(_jsonMap, helpers.SKIP, _intftype, resultIntf, _ntp, cause=causeStr)
                            continue

                        try:
                            # route entries only need to be added from configured interface on dom0
                            if utils.isDom0:
                                if not _ntpSameNwFlag:
                                    _route_ret = _clunetwork.mAddRouteEntry(_intf_name, _ntp, _gateway)
                                    if not _route_ret:
                                        _testResult = CHK_RESULT.FAIL
                                        helpers.updateResMap(_jsonMap, helpers.FAIL, _intftype, resultIntf, _ntp,
                                                           cause=helpers.INTERNAL_ERROR, resolution=helpers.REACH_ORA_SUP)
                                        self.logger.mAppendLog(LOG_TYPE.ERROR, "Failed to add routing entry for {} from the interface {} on the host {}".format(_ntp, _intf_name, aHost), _jsonMap)
                                        _clunetwork.mDeleteRouteEntry(_intf_name, _ntp, _gateway)
                                        continue
                                else:
                                    self.logger.mAppendLog(LOG_TYPE.INFO, "NTP {} is in the same subnet as the {} network, hence skipping adding route through the gateway".format(_ntp, _intftype))

                            # Rate limiting in NTP based on configuration may or may not send rate limit response.
                            # NTP rate limiting is based on average gap time between queries. Default required average = 2^3 = 8 seconds.
                            # Hence, we intelligently sleep when required per host and per network type to keep average headaway time more than 8 seconds
                            if utils.getParam("ntp_timeout") and intf_count:
                                ntp_timeout = utils.getParam("ntp_timeout")
                                if ntp_timeout.isdigit() and int(ntp_timeout) > 0:
                                    if intf_count[_ntp]:
                                        sleep(int(ntp_timeout))

                                    intf_count[_ntp] = datetime.now()

                            _ntpStatus = self.mNtpTest(_hostOS, _ntp, _clunetwork)
                            if _ntpStatus:
                                helpers.updateResMap(_jsonMap, helpers.PASS, _intftype, resultIntf, _ntp)
                                self.logger.mAppendLog(LOG_TYPE.INFO, "Validation of NTP {} from host {} through {}, result: PASS".format(_ntp, aHost, _intf_name))
                            else:
                                _testResult = CHK_RESULT.FAIL
                                causeStr = "NTP {} is not accessible from source {} with vlan id {} from gateway {}.".format(_ntp, _ipaddr, _vlanId, _gateway)
                                self.logger.mAppendLog(LOG_TYPE.ERROR, "Validation of NTP {} from host {} through {}, result: FAIL".format(_ntp, aHost, _intf_name), _jsonMap)

                                helpers.updateResMap(_jsonMap, helpers.FAIL, _intftype, resultIntf, _ntp,
                                                   cause=causeStr, resolution=helpers.CHECK_NW_ENTITIES)

                        except Exception as e:      # pragma: no cover
                            _testResult = CHK_RESULT.FAIL
                            helpers.updateResMap(_jsonMap, helpers.FAIL, _intftype, resultIntf, _ntp,
                                               cause=helpers.INTERNAL_ERROR, resolution=helpers.REACH_ORA_SUP)
                            self.logger.mAppendLog(LOG_TYPE.ERROR, "Unable to validate the NTP Servers for interface {} on the host {}".format(intf, aHost), _jsonMap)
                            self.logger.mAppendLog(LOG_TYPE.VERBOSE, "Exception {} occurred, stacktrace:\n {}".format(str(e), traceback.format_exc()))

                        if utils.isDom0 and not _ntpSameNwFlag:
                            _clunetwork.mDeleteRouteEntry(_intf_name, _ntp, _gateway)

                    if utils.isDom0:
                        _clunetwork.mUnConfigureInterface(intf, netobj)

        self.mDisconnectNode(utils.getNodeObj())
        helpers.testFooter(testName, _testResult, _jsonMap)
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    # Helper function for mCheckNetworkPingTest to test ping to passed IP
    def mNetworkPing(self, aIp, cluNetworkObj):
        """
        :param aIp: IPv4 address
        :return: Bool, True if IP address is not pingable, False otherwise
        """
        testName = "Network Ping"

        cmd = "/bin/ping -c 1 -W 4 {}".format(aIp)
        _, _o, _e, _rc = cluNetworkObj.mLogCmd(cmd, "info", testName)
        if _rc == 1:
            return True

        return False

    # Network Validation Test to check availability of SCAN and VIP's
    def mCheckNetworkPingTest(self, aHost):
        testName = "Network Ping"
        helpers = self.NetworkValidationHelpers(aHost, self.logger, self)
        helpers.startNWTestLogger(testName)

        _testResult = CHK_RESULT.PASS
        _jsonMap = {"hcDisplayString": set()}

        try:
            utils = helpers.getNetworkValidationUtils(aHost, _jsonMap)
        except HostNotConnectable as e:
            _testResult = CHK_RESULT.FAIL
            helpers.updateResMap(_jsonMap, helpers.FAIL, None, cause=e.message, resolution=helpers.REACH_ORA_SUP)
            helpers.testFooter(testName, _testResult, _jsonMap)
            return self.logger.mUpdateResult(_testResult, _jsonMap)

        _clunetwork = utils.getCluNetworkObj()

        # Skip test in case no matching network returned by exacloud for X9 and above
        if "ERROR" in utils.getIntfMap():
            helpers.skipTest(testName, utils.getNodeObj(), _jsonMap)
            return self.logger.mUpdateResult(CHK_RESULT.FAIL, _jsonMap)

        _hostname_ip_pairs = self.mReturnHostnameIpMapping(self.mGetEbox(), aHost, True, utils.isDrNetConfigured())
        self.logger.mAppendLog(LOG_TYPE.INFO, "IPs to be checked from host {} : {}\n".format(aHost, json.dumps(_hostname_ip_pairs, indent=4)))

        skipOtherIntfs = {CLIENT: False, BACKUP: False, DR: False}

        # Loop over all interfaces
        for _intftype, _intfMap in utils.getIntfMap().items():

            _jsonMap[_intftype] = {}

            # skip tests during network reconfiguration
            if utils.isReconfiguration():
                # skip test from network which is not changing
                if not utils.isNetworkReconfiguring(aHost, _intftype):
                    helpers.updateResMap(_jsonMap, helpers.SKIP, _intftype, cause=helpers.UPDATE_NW_SKIP)
                    continue

                # skip test from network which is changing, but IPs are not changing
                if not "ip" in utils.getUpdateProperties(aHost, _intftype):
                    helpers.updateResMap(_jsonMap, helpers.SKIP, _intftype,
                                         cause="IP addresses are not being reconfigured for this network.")
                    continue

            for intf in _intfMap["interfaces"]:
                resultIntf = intf
                netobj = _intfMap["netobj"]

                if _clunetwork.useBridge[_intftype]:
                    resultIntf = _intfMap["bridge"]
                    if skipOtherIntfs[_intftype]:
                        continue
                    else:
                        skipOtherIntfs[_intftype] = True
                _jsonMap[_intftype][resultIntf] = {}

                # skip test for a down physical interface
                if aHost in self.downIntfs and intf in self.downIntfs[aHost]:
                    self.logger.mAppendLog(LOG_TYPE.WARNING,
                                           "Skipping NetworkPing test from down interface {} on the host {}.".format(intf, aHost))
                    helpers.updateResMap(_jsonMap, helpers.SKIP, _intftype, resultIntf,
                                         cause=helpers.DOWN_INTF_SKIP)
                    continue

                _intf_name = _clunetwork.interfaceMap[_intftype][intf]
                _ret = _clunetwork.mConfigureInterface(intf, netobj)
                if not _ret:
                    _testResult = CHK_RESULT.FAIL
                    helpers.updateResMap(_jsonMap, helpers.FAIL, _intftype, resultIntf,
                                       cause=helpers.INTERNAL_ERROR, resolution=helpers.REACH_ORA_SUP)
                    self.logger.mAppendLog(LOG_TYPE.ERROR, "Failed to configure the interface {} on the host {}".format(_intf_name, aHost), _jsonMap)
                    # Un-configure interface
                    _clunetwork.mUnConfigureInterface(intf, netobj)
                    continue

                try:
                    for ipType in _hostname_ip_pairs:
                        __ipsToCheck = set()

                        if _intftype in [CLIENT, DR]:
                            if _intftype == CLIENT:
                                viplist = ["VIPs"]
                                scanlist = ["ScanIPs"]
                                nonScanList = ["VIPs", "ClientIPs"]
                            else:
                                viplist = ["drVIPs"]
                                scanlist = ["drScanIPs"]
                                nonScanList = ["drVIPs", "drIPs"]

                            if ipType in nonScanList:
                                _jsonMap[_intftype][resultIntf][ipType] = {}

                                # skip ping test if this is a re-validation flow and Live VMs exist
                                if ipType in viplist:
                                    if utils.hc.mGetReNetValidation() and utils.hc.mGetAnyRunningVMs():
                                        helpers.updateResMap(_jsonMap, helpers.SKIP, _intftype, resultIntf, ipType,
                                                           cause="Re-validation with Running VMs identified.")
                                        continue

                                for _hostname in _hostname_ip_pairs[ipType]:
                                    __ipsToCheck.add(_hostname_ip_pairs[ipType][_hostname])

                            elif ipType in scanlist:
                                _jsonMap[_intftype][resultIntf][ipType] = {}
                                # Skip ping test for SCAN IP's if this is elastic validation flow
                                if utils.hc.mGetDeltaNetValidation():
                                    helpers.updateResMap(_jsonMap, helpers.SKIP, _intftype, resultIntf, ipType,
                                                       cause="Elastic Compute flow identified")
                                    continue

                                # or there are live VM's and this is re-validation flow
                                if utils.hc.mGetReNetValidation() and utils.hc.mGetAnyRunningVMs():
                                    helpers.updateResMap(_jsonMap, helpers.SKIP, _intftype, resultIntf, ipType,
                                                       cause="Re-validation with Running VMs identified.")
                                    continue

                                for _scanName in _hostname_ip_pairs[ipType]:
                                    for _scanip in _hostname_ip_pairs[ipType][_scanName]:
                                        __ipsToCheck.add(_scanip)

                        elif _intftype == BACKUP:
                            if ipType in ["BackupIPs"]:
                                _jsonMap[_intftype][resultIntf][ipType] = {}
                                for _hostname in _hostname_ip_pairs[ipType]:
                                    __ipsToCheck.add(_hostname_ip_pairs[ipType][_hostname])

                        # Do PING test for the shortlisted IPs
                        for _ip in __ipsToCheck:
                            _jsonMap[_intftype][resultIntf][ipType][_ip] = {}
                            if ipType in ["ClientIPs", "BackupIPs", "drIPs"]:
                                _res = not (self.mCheckArping(_intf_name, _ip, _clunetwork))
                            else:
                                _res = self.mNetworkPing(_ip, _clunetwork)

                            if _res:
                                _ipStatus = "PASS"
                                helpers.updateResMap(_jsonMap, helpers.PASS, _intftype, resultIntf, ipType, _ip)
                            else:
                                _ipStatus = "FAIL"
                                _testResult = CHK_RESULT.FAIL
                                failstr = "IP {} is already in use.".format(_ip)
                                self.logger.mAppendLog(LOG_TYPE.ERROR, failstr, _jsonMap)
                                helpers.updateResMap(_jsonMap, helpers.FAIL, _intftype, resultIntf, ipType, _ip,
                                                   cause=failstr, resolution="Please ensure this IP is available.")

                            self.logger.mAppendLog(LOG_TYPE.INFO, "Availability check for IP {}, from host {} through {}, result: {}".format(_ip, aHost, _intf_name, _ipStatus))

                except Exception as e:      # pragma: no cover
                    _testResult = CHK_RESULT.FAIL
                    helpers.updateResMap(_jsonMap, helpers.FAIL, _intftype, resultIntf,
                                       cause=helpers.INTERNAL_ERROR, resolution=helpers.REACH_ORA_SUP)
                    self.logger.mAppendLog(LOG_TYPE.ERROR, "Unable to check for IP Availability for interface {} on the host {}".format(intf, aHost), _jsonMap)
                    self.logger.mAppendLog(LOG_TYPE.VERBOSE, "Exception {} occurred, stacktrace:\n {}".format(str(e), traceback.format_exc()))

                _clunetwork.mUnConfigureInterface(intf, netobj)

        self.mDisconnectNode(utils.getNodeObj())
        helpers.testFooter(testName, _testResult, _jsonMap)
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    '''
    End of Section for tests pertaining to Network Validation
    '''

    #
    # Dom0 test:
    # Perform network consistency check on Dom0 using ipconf
    #
    def mCheckNetConsistency(self, aHost):

        _ebox = self.mGetEbox()
        _jsonMap = {}
        _testResult = CHK_RESULT.FAIL
        _node = self.mGetNode(aHost)
        _cmd_str = '/opt/oracle.cellos/ipconf.pl -nocodes -conf /opt/oracle.cellos/cell.conf -check-consistency -semantic -at-runtime'
        _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
        _out = _o.readlines()
        if _out:
            for _line in _out:
                if "PASSED" in _line:
                    _testResult = CHK_RESULT.PASS
        else:
            self.logger.mAppendLog(LOG_TYPE.ERROR,"running network consistency check on %s" %(aHost))

        _cluhealth = self.mGetHc()
        _cluhealth.mSetDom0NetCons(_testResult)

        if _testResult == CHK_RESULT.FAIL:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "Network consistency check failed on %s" %(aHost), _jsonMap)
            self.logger.mAppendLog(LOG_TYPE.ERROR, "Failure running " + _cmd_str, _jsonMap)
        else:
            self.logger.mAppendLog(LOG_TYPE.INFO, "Network consistency check passed on %s" %(aHost), _jsonMap)


        self.mDisconnectNode(_node)
        return self.logger.mUpdateResult(_testResult, _jsonMap)
    # end

    # Dom0 test:
    # Called during pre-provisioning
    # ebtables -L must not have any entries
    #
    def mCheckEbtables(self, aHost):

        _host = aHost
        _node = self.mGetNode(_host)

        _ebox = self.mGetEbox()
        _jsonMap = {}
        _testResult = CHK_RESULT.PASS
        _clunode = self.mGetClusterNode(_host)

        def _check_vif_whitelist_file_exist():
            _clusterId = _clunode.mGetClusterId()
            # Check for presence of vif-whitelist file
            _ebt_wl_file   = '/opt/exacloud/network/vif-whitelist'+'.'+ _clusterId
            _cmdstr = 'ls -l ' + _ebt_wl_file
            _i, _o, _e = _node.mExecuteCmd(_cmdstr, aTimeout=180)
            if _o is not None:
                _out = _o.readlines()
                if len(_out):
                    self.logger.mAppendLog(LOG_TYPE.ERROR, '*** Ebtables whitelist file %s exists on %s. ***' %(_clusterId, _host))
                    return True
                else:
                    self.logger.mAppendLog(LOG_TYPE.INFO, '*** Ebtables whitelist file does not exist for given cluster %s on host %s ***' %(_clusterId, _host))
            return False

        #for exacm, 'ebtables_setup' in exabox.conf must be false
        if(_ebox.mIsExacm() == True):
            if _ebox.mGetEbtableSetup():
                self.logger.mAppendLog(LOG_TYPE.WARNING,"ebtables_setup must be False for exacm env for %s" %(_host))
                _testResult = CHK_RESULT.FAIL

        if(_check_vif_whitelist_file_exist() == True):
            self.logger.mAppendLog(LOG_TYPE.WARNING, "Pre-provisioning: ebtables whitelist file found for %s " %(_host))
            _testResult = CHK_RESULT.FAIL

        #check for ebtable entries if it is not multi-vm
        if(_ebox.SharedEnv() == False):

            _cmd_str = 'ebtables -L | grep \"Bridge chain\"'
            _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
            _out = _o.readlines()
            if _out:
                for _line in _out:
                    _chain = _line.split(",")[0].split(":")[1].lstrip().rstrip()
                    _entries = _line.split(",")[1].split(":")[1].lstrip().rstrip()
                    if _entries != "0":
                        _testResult = CHK_RESULT.FAIL
                        self.logger.mAppendLog(LOG_TYPE.ERROR, "Pre-provisioning: %s : ebtables for %s show %s entries. Should be empty" %(_host, _chain, _entries), _jsonMap)
            else:
                self.logger.mAppendLog(LOG_TYPE.ERROR, "running ebtables check on %s" %(_host))
                _testResult = CHK_RESULT.FAIL

        if _testResult == CHK_RESULT.FAIL:
            self.logger.mAppendLog(LOG_TYPE.ERROR,"Pre-provisioning: Verification of ebtables failed on %s" %(_host), _jsonMap)
        else:
            self.logger.mAppendLog(LOG_TYPE.INFO,"Pre-provisioning: Verification of ebtables was successful on %s" %(_host), _jsonMap)

        self.mDisconnectNode(_node)
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    # end

    # Switch test:
    # Case 1: If freshly provisioned, smnodes list must be null
    # Case 2: If provisioned at least once, output of smnodes list must match ibswitches
    #
    def mCheckSmnodesList(self, aHost):

        _host = aHost
        _node = self.mGetNode(_host)

        _ebox = self.mGetEbox()
        _jsonMap = {}
        _testResult = CHK_RESULT.PASS
        _eboxnetworks = _ebox.mGetNetworks()
        _smnodeslist = []
        _ibswlist = []
        _jsonMap[_host] = {}

        self.logger.mAppendLog(LOG_TYPE.INFO, '*** Validating smnodes List ***')
        _cmd_str = 'smnodes list'
        _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
        _out = _o.readlines()
        if _out:
            # Switch has been provisioned at least once
            for _line in _out:
                _smnode = _line.lstrip().rstrip()
                _smnodeslist.append(_smnode)
                _jsonMap[_host]['smnodes'] = _smnode
        else:
            # Ok only in case of a freshly provisioned cluster
            self.logger.mAppendLog(LOG_TYPE.WARNING, "\'smnodes list\' on %s returned null. OK only if switch is freshly provisioned" %(_host), _jsonMap)
            return self.logger.mUpdateResult(_testResult, _jsonMap)

        # Obtain the output of ibswitches
        _cmd_str = 'ibswitches'
        _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
        _out = _o.readlines()
        if _out:
            for _line in _out:
                _ibsw = _line.split("\"")[1].split(" ")[-1]
                _ibswlist.append(_ibsw)
                _jsonMap[_host]['ibswitches'] = _line.rstrip()

            # ibswitches entries must match with smnodes list entries
            if ( len(_smnodeslist) != len(_ibswlist)):
                self.logger.mAppendLog(LOG_TYPE.ERROR, "On %s the number of entries returned by ibswitches differs from output of smnodes" %(_host), _jsonMap)
                _testResult = CHK_RESULT.FAIL
            else:
                self.logger.mAppendLog(LOG_TYPE.INFO, "On %s the number of entries returned by ibswitches matches with output of smnodes" %(_host), _jsonMap)

            # Entries in both lists must match
            for _ibsw in _ibswlist:
                if _ibsw not in _smnodeslist:
                    self.logger.mAppendLog(LOG_TYPE.ERROR, "On %s ibswitches output %s does not appear in smnodes list" %(_host, _ibsw), _jsonMap)
                    _testResult = CHK_RESULT.FAIL
        else:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "smnodes list verification failed on %s" %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    # end

    # Dom0 test:
    # Check the vm image versions.
    # Called pre-provisioning
    #
    def mCheckVmImage(self, aHost, aNode, aClunode, aCluhealth, aRecommend, aJsonMap):

        _testResult = CHK_RESULT.PASS
        _jsonmap = {}

        _dom0ImgInfos = getDom0VMImagesInfo(
                aHost, aComputeMd5Sum=self.mGetHc().mGetLongRunCheck())

        if not _dom0ImgInfos:
            _testResult = CHK_RESULT.FAIL
            self.logger.mAppendLog(
                    LOG_TYPE.ERROR,
                    ('Pre-provisioning - No VM image found on Dom0 {}'
                       .format(aHost)),
                    _jsonmap)
        else:
            if len(_dom0ImgInfos) > 1:
                self.logger.mAppendLog(
                        LOG_TYPE.WARNING,
                        ('Pre-provisioning - More than 1 VM image found on '
                           'Dom0 {}'.format(aHost)),
                        _jsonmap)
            else:  # _dom0ImgInfos has only one item
                _remoteImgInfo = _dom0ImgInfos[0]

                if 'md5sum' in _remoteImgInfo:
                    _imgBaseName = _remoteImgInfo['imgBaseName']
                    _imgHash = _remoteImgInfo['md5sum']

                    if _imgHash is None:
                        _imgHash = -1
                        self.logger.mAppendLog(
                                LOG_TYPE.ERROR,
                                ('Fail to compute md5sum for {} on {}'
                                   .format(_imgBaseName, aHost)),
                                _jsonmap)

                    _jsonmap[aHost]['SystemImageHash'] = _imgHash

                _remoteImgVersion = _remoteImgInfo['imgVersion']
                _isRemoteImgKvm = _remoteImgInfo['isKvmImg']
                _localImgInfo = getNewestVMImageArchiveInRepo(_isRemoteImgKvm)

                if _localImgInfo is None:
                    _testResult = CHK_RESULT.FAIL
                    self.logger.mAppendLog(
                            LOG_TYPE.ERROR,
                            "Pre-provisioning - Local System Image not found",
                            _jsonmap)
                else:
                    _localImgVersion = _localImgInfo['imgVersion']

                    if _localImgVersion != _remoteImgVersion:
                        aRecommend.append(
                                ('WARNING: Pre-provisioning - System VM Image '
                                   '{} on Dom0 {} not present in local system'
                                   .format(_remoteImgVersion, aHost)))
                        aRecommend.append(_jsonmap)

        return self.logger.mUpdateResult(_testResult, _jsonmap)

    # end


    def mCheckDnsServers(self, aConfig, aRecommend, aJsonMap):

        _eBox = self.mGetEbox()
        _jsonMap = {}
        _testResult = CHK_RESULT.PASS
        _eboxnetworks = _eBox.mGetNetworks()
        _jsonMap = aJsonMap

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

        self.logger.mAppendLog(LOG_TYPE.INFO, '\n *** DNS Server Validation ***')

        for _dns in _dnss_list:
            self.logger.mAppendLog(LOG_TYPE.INFO, 'DNS Server IP Address: %s' %(_dns))

            if _dns is None:
                self.logger.mAppendLog(LOG_TYPE.WARNING, "Blank <dnsServer> entries found in XML file", _jsonMap)
                continue

            _jsonMap[_dns] = {}
            _jsonMap[_dns]['logs'] = {}

            # Check for IP address validity
            try:
                socket.inet_aton(_dns)
                self.logger.mAppendLog(LOG_TYPE.INFO, '***                  Valid IP Address: \t True', _jsonMap)
                _jsonMap[_dns]['validIP'] = "True"
            except socket.error:
                self.logger.mAppendLog(LOG_TYPE.ERROR, "Incorrect IP Address %s listed as a DNS Server in XML" %(_dns), _jsonMap)
                _jsonMap[_dns]['validIP'] = "False"
                _jsonMap[_dns]['TestResult'] = CHK_RESULT.FAIL
                _testResult = CHK_RESULT.FAIL
                continue

            # Ping test
            if _eBox.mPingHost(_dns):
                self.logger.mAppendLog(LOG_TYPE.INFO, '***                   Server Pingable: \t True', _jsonMap)
                _jsonMap[_dns]['pingable'] = "True"
            else:
                self.logger.mAppendLog(LOG_TYPE.ERROR, "IP Address %s not pingable listed as a DNS Server in XML" %(_dns), _jsonMap)
                _jsonMap[_dns]['pingable'] = "False"
                _jsonMap[_dns]['TestResult'] = CHK_RESULT.FAIL
                _testResult = CHK_RESULT.FAIL
                continue

            # nslookup
            _fqdn = self.mNslookupTest(_dns)
            self.logger.mAppendLog(LOG_TYPE.INFO, '***              FQDN as per nslookup: \t %s' %(_fqdn), _jsonMap)
            _jsonMap[_dns]['fqdn'] = _fqdn

            if _fqdn == "None":
                self.logger.mAppendLog(LOG_TYPE.ERROR, "nslookup failed for %s listed as DNS Server in XML" %(_dns), _jsonMap)
                _testResult = CHK_RESULT.FAIL

            elif "dns" not in _fqdn:
                self.logger.mAppendLog(LOG_TYPE.WARNING, "%s listed as DNS Server in XML does not contain \"dns\" in its FQDN" %(_dns), _jsonMap)

            # DIG test
            _digtest = self.mDigTest(_dns)
            if _digtest == False:
                self.logger.mAppendLog(LOG_TYPE.ERROR, "DIG test failed for %s listed as DNS Server in XML" %(_dns), _jsonMap)
                _jsonMap[_dns]['digTest'] = "False"
                _testResult = CHK_RESULT.FAIL
            else:
                _jsonMap[_dns]['digTest'] = "True"

            if _fqdn != "None" and _digtest == True:
                _jsonMap[_dns]['TestResult'] = CHK_RESULT.PASS
                _testResult = CHK_RESULT.PASS
                self.logger.mAppendLog(LOG_TYPE.INFO, '\n *** DNS Server Validation went successful ***', _jsonMap)
            else:
                _jsonMap[_dns]['TestResult'] = CHK_RESULT.FAIL
                _testResult = CHK_RESULT.FAIL
                self.logger.mAppendLog(LOG_TYPE.ERROR, '\n *** DNS Server Validation failed ***', _jsonMap)


        return self.logger.mUpdateResult(_testResult, _jsonMap)

    # End

    def mCheckNtpServers(self, aConfig, aRecommend, aJsonMap):

        _ebox = self.mGetEbox()
        _jsonMap = {}
        _testResult = CHK_RESULT.PASS
        _jsonMap = aJsonMap

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

        self.logger.mAppendLog(LOG_TYPE.INFO, '\n *** NTP Server Validation ***')

        for _ntp in _ntps_list:

            self.logger.mAppendLog(LOG_TYPE.INFO, 'NTP Server IP Address: %s' %(_ntp))

            if _ntp is None:
                self.logger.mAppendLog(LOG_TYPE.ERROR, "Blank <ntpServer> entries found in XML file")
                continue

            _jsonMap[_ntp] = {}

            # Check for IP address validity
            try:
                socket.inet_aton(_ntp)
                self.logger.mAppendLog(LOG_TYPE.INFO, '***                  Valid IP Address: \t True')
                _jsonMap[_ntp]['validIP'] = "True"
            except socket.error:
                self.logger.mAppendLog(LOG_TYPE.ERROR, "Incorrect IP Address %s listed as a NTP Server in XML" %(_ntp), _jsonMap)
                _jsonMap[_ntp]['validIP'] = "False"
                _testResult = CHK_RESULT.FAIL
                continue

            # Ping test
            if _ebox.mPingHost(_ntp):
                self.logger.mAppendLog(LOG_TYPE.INFO, '***                   Server Pingable: \t True', _jsonMap)
                _jsonMap[_ntp]['pingable'] = "True"
            else:
                _jsonMap['XML']['ntpServer'][_ntp]['pingable'] = "False"
                self.logger.mAppendLog(LOG_TYPE.ERROR, "ping failed for %s listed as NTP Server in XML" %(_ntp))
                _testResult = CHK_RESULT.FAIL
                continue

            # nslookup
            _fqdn = self.mNslookupTest(_ntp)
            self.logger.mAppendLog(LOG_TYPE.INFO, '***              FQDN as per nslookup: \t %s' %(_fqdn))

            if _fqdn == "None":
                self.logger.mAppendLog(LOG_TYPE.ERROR, "nslookup failed for %s listed as NTP Server in XML" %(_ntp), _jsonMap)
                _testResult = CHK_RESULT.FAIL
            elif "rtr" not in _fqdn:
                self.logger.mAppendLog(LOG_TYPE.WARNING, "%s listed as an NTP Server in XML does not contain \"rtr\" in its FQDN" %(_ntp), _jsonMap)

        return self.logger.mUpdateResult(_testResult, _jsonMap)
    # End

    def mCheckDatabases(self):

        _eBox = self.mGetEbox()
        _jsonMap = {}
        _testResult = CHK_RESULT.PASS
        _eboxnetworks = _eBox.mGetNetworks()

        _validDBs = ['cdb', 'pdb']

        _databases = _eBox.mGetDatabases()
        _dblist = _databases.mGetDBconfigs()
        _dbidlist = []

        self.logger.mAppendLog(LOG_TYPE.INFO, '\n *** XML Database entries validation ***')

        # Collate a list of all DB IDs
        for _db in _dblist:
            _dbid = _dblist[_db].mGetDBId()
            _dbidlist.append(_dbid)

        # Validate all database entries
        for _db in _dblist:

            _dbid = _dblist[_db].mGetDBId()
            _dbhome = _dblist[_db].mGetDBHome()
            #check databaseHome if it is for current cluster
            _dbHomeConfig  = _eBox.mGetDBHomes().mGetDBHomeConfig(_dbhome)
            if _dbHomeConfig is None:
                continue

            _jsonMap[_dbid] = {}
            _jsonMap[_dbid]['logs'] = {}
            _dbtype = _dblist[_db].mGetDBType()
            _dbSid = _dblist[_db].mGetDBSid()
            _dbtemplate = _dblist[_db].mGetDBTemplate().text

            _jsonMap[_dbid]['dbType'] = _dbtype
            _jsonMap[_dbid]['dbSid'] = _dbSid
            _jsonMap[_dbid]['dbHome'] = _dbhome
            _jsonMap[_dbid]['dbTemplate'] = _dbtemplate

            self.logger.mAppendLog(LOG_TYPE.INFO, '***                       Database ID: \t %s' %(_dbid))
            self.logger.mAppendLog(LOG_TYPE.INFO, '***                     Database Type: \t %s' %(_dbtype))
            self.logger.mAppendLog(LOG_TYPE.INFO, '***                      Database Sid: \t %s' %(_dbSid))
            self.logger.mAppendLog(LOG_TYPE.INFO, '***                     Database Home: \t %s' %(_dbhome))
            self.logger.mAppendLog(LOG_TYPE.INFO, '***                 Database Template: \t %s' %(_dbtemplate))

            #check for DB version
            _dbHomeVersion = str(_dbHomeConfig.mGetDBHomeVersion())

            #skip check for cdb/pdb if DB version is 11
            if _dbHomeVersion[:2] == '11':
                continue

            # Only cdb-pdb type entries are expected
            if _dbtype not in _validDBs:
                self.logger.mAppendLog(LOG_TYPE.ERROR, "Invalid DB type %s found against DB ID %s" %(_dbtype, _dbid), _jsonMap)
                _testResult = CHK_RESULT.FAIL

            # The cdbid must be one of the other DB Ids
            _dbcdbid = _dblist[_db].mGetCDBid()
            if _dbtype == "cdb" and _dbcdbid != None:
                self.logger.mAppendLog(LOG_TYPE.ERROR, "Invalid CDB Id found for DB %s" %(_dbid), _jsonMap)
                _testResult = CHK_RESULT.FAIL
            elif _dbtype == "pdb" and _dbcdbid == None:
                self.logger.mAppendLog(LOG_TYPE.ERROR, "In DB %s the CDB ID field is missing" %(_dbid), _jsonMap)
                _testResult = CHK_RESULT.FAIL
            elif _dbtype == "pdb" and _dbcdbid not in _dbidlist:
                self.logger.mAppendLog(LOG_TYPE.ERROR, "DB %s has an incorrect CDB ID field %s" %(_dbid, _dbcdbid), _jsonMap)
                _testResult = CHK_RESULT.FAIL

            if _dbtype == "pdb":
                self.logger.mAppendLog(LOG_TYPE.INFO, '***                    Database CDBId: \t %s' %(_dbcdbid), _jsonMap)

        return self.logger.mUpdateResult(_testResult, _jsonMap)

    # end

    def mGetSubnet(self, aIpAddr, aNetmask):
        _eBox = self.mGetEbox()
        #generate subnet using netmask and ipaddr
        _mask_cidr = _eBox.mNetMaskToCIDR(aNetmask)
        _ip = aIpAddr
        _netMask = aNetmask
        _subnet = '.'.join([str(int(_pair[0]) & int(_pair[1])) for _pair in zip(_ip.split('.'), _netMask.split('.'))])
        return _subnet

    #
    # Validate the subnet for domU and cell for storage inteface in XML file
    #
    def mCheckSubnetMask(self):

        _eBox = self.mGetEbox()
        _jsonMap = {}
        _testResult = CHK_RESULT.PASS
        _eBoxNetworks = _eBox.mGetNetworks()
        _config = _eBox.mGetConfig()

        _jsonMap['subnetMask'] = {}
        _storage_subnet = None
        _storage_pkey  = None
        _err = False
        _logmsg = None

        _, _domUs, _cells, _ = _eBox.mReturnAllClusterHosts()
        _cluhosts = _cells + _domUs
        self.logger.mAppendLog(LOG_TYPE.INFO, '\n *** SubnetMask check for DomUs and Cells ***')
        for _host in _cluhosts:
            _neto = _eBoxNetworks.mGetNetworkConfigByName(_host)
            _host_mac = _eBox.mGetMachines().mGetMachineConfig(_host)
            _net_list = _host_mac.mGetMacNetworks()

            for _net in _net_list:
                _priv = _eBoxNetworks.mGetNetworkConfig(_net)
                if _priv.mGetNetType() == 'private':
                    #generate subnet using netmask and ipaddr
                    _ip = _priv.mGetNetIpAddr()
                    _netmask = _priv.mGetNetMask()
                    _subnet = self.mGetSubnet(_ip, _netmask)
                    _pkey = _priv.mGetPkey()
                    _pkeyname = _priv.mGetPkeyName()
                    _hostname = _priv.mGetNetNatHostName()

                    if _pkeyname[:2] == 'st':
                        self.logger.mAppendLog(LOG_TYPE.INFO, 'Mac Hostname: %s' %(_hostname))
                        if _storage_pkey is None:
                            _storage_pkey = _pkey
                            _storage_subnet = _subnet
                        elif _storage_pkey != _pkey:
                            self.logger.mAppendLog(LOG_TYPE.ERROR, 'Invalid STORAGE PKEY %s detected for %s of %s, skipping subnet check' %(_pkey, _hostname,_host), _jsonMap)
                            _err = True
                            continue
                        else:
                            pass
                    else:
                        #skip for Cluster pkey used for clusterware in case of domu
                        continue

                    self.logger.mAppendLog(LOG_TYPE.INFO, '***                       host    : \t %s' %(_host))
                    self.logger.mAppendLog(LOG_TYPE.INFO, '***                       ipAddr  : \t %s' %(_ip))
                    self.logger.mAppendLog(LOG_TYPE.INFO, '***                       netmask : \t %s' %(_netmask))
                    self.logger.mAppendLog(LOG_TYPE.INFO, '***                       subnet  : \t %s' %(_subnet))
                    _jsonMap[_hostname] = {}
                    _jsonMap[_hostname]['IpAddress'] = _ip
                    _jsonMap[_hostname]['Netmask'] = _netmask
                    _jsonMap[_hostname]['Subnet'] = _subnet
                    _jsonMap[_hostname]['HostName'] = _host

                    if(_subnet == _storage_subnet):
                        _jsonMap[_hostname]['TestResult'] = CHK_RESULT.PASS
                        self.logger.mAppendLog(LOG_TYPE.INFO, '***                  Subnet Match: \t True')
                    else:
                        _jsonMap[_hostname]['TestResult'] = CHK_RESULT > CHK_RESULT.FAIL
                        self.logger.mAppendLog(LOG_TYPE.ERROR, 'Subnet %s should match with storage subnet %s for %s of %s' %(_subnet, _storage_subnet, _hostname, _host), _jsonMap)
                        _err = True

        if (_err == False):
            _jsonMap['TestResult'] = CHK_RESULT.PASS
            _testResult = CHK_RESULT.PASS
            _jsonMap['subnet'] = _storage_subnet
            _jsonMap['pkey'] = _storage_pkey
            self.logger.mAppendLog(LOG_TYPE.INFO, "SubnetMask for domUs and Cells matched in XML configuration", _jsonMap)
        else:
            _jsonMap['TestResult'] = CHK_RESULT.FAIL
            _testResult = CHK_RESULT.FAIL
            _jsonMap['subnet'] = _storage_subnet
            _jsonMap['pkey'] = _storage_pkey
            self.logger.mAppendLog(LOG_TYPE.ERROR, "Mismatch in SubnetMask for domUs and Cells in XML configuration", _jsonMap)

        return self.logger.mUpdateResult(_testResult, _jsonMap)

    # end

    # nslookup test

    def mNslookupTest(self, aIp):

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

    # dig test
    def mDigTest(self, aIp):

        try:
            _out = subprocess.check_output(['dig', "@"+aIp, "www.oracle.com", "+short"]).decode('utf8')
            if _out:
                _o = _out.split('\n')
                _digstr = "no servers could be reached"
                for _line in _o:
                    if _digstr in _line:
                        return False
        except:
            return False

        return True

    #
    # Check if scan-names in XMl are resolvable.
    # Otherwise, add the corresponding domain name to /etc/resolv.conf
    #
    def mCheckScanNames(self):

        _ebox = self.mGetEbox()

        _testResult = CHK_RESULT.PASS
        _jsonMap = {}

        self.logger.mAppendLog(LOG_TYPE.INFO, '*** Check if Scan Name Resolvable ***')

        _fqdn = 'None'

        _scan_list = []
        _clusters  = _ebox.mGetClusters().mGetClusters()
        #get scan ip for clusters added in software/clusters/cluster xml
        for _cluId in _clusters:
            _cluster = _ebox.mGetClusters().mGetCluster(_cluId)
            _scan_list  += _cluster.mGetCluScans()

        for _sname in _scan_list:
            _scanName = _ebox.mGetScans().mGetScan(_sname).mGetScanName()
            self.logger.mAppendLog(LOG_TYPE.INFO,'*** scan Id:     %s' %(_sname))
            self.logger.mAppendLog(LOG_TYPE.INFO,'***                           scanName: \t %s' %(_scanName))
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
                        self.logger.mAppendLog(LOG_TYPE.RECOMMEND, 'scanName %s not resolvable, Though reverse lookup passed with ip %s' % (_scanName, _scanip), _jsonMap)
                        break
            except:
                _fqdn = 'None'

            if(self.mGetPreProv() == True):
                for _scanip in _scanip_list:
                    _cmd = '/bin/ping -c 1 -W 4 %s' % (_scanip)
                    _rc, _, _, _ = _ebox.mExecuteLocal(_cmd)
                    if not _rc:
                        #check if scanip is already up, indicates it has been used by other cluster
                        self.logger.mAppendLog(LOG_TYPE.WARNING, 'scanName %s with scanIp %s is pingable, indicating scanip used by other cluster' % (_scanName, _scanip), _jsonMap)
                        break

            self.logger.mAppendLog(LOG_TYPE.INFO,'***                               fqdn: \t %s' %(_fqdn))


            _jsonMap[_sname] = {}
            _jsonMap[_sname]['scanName'] = _scanName
            _jsonMap[_sname]['fqdn'] = _fqdn

            if _fqdn == 'None':
                self.logger.mAppendLog(LOG_TYPE.WARNING, 'scanName %s is not resolvable. verify /etc/resolv.conf' % _scanName, _jsonMap)
                _testResult = CHK_RESULT.FAIL
            else:
                self.logger.mAppendLog(LOG_TYPE.INFO, 'scanName %s is resolvable.' % _scanName, _jsonMap)

        return self.logger.mUpdateResult(_testResult, _jsonMap)
    # end check scan names

    #
    # Check Users and Groups xml configuration
    #
    def mCheckUserandGroupXML(self):

        _ebox = self.mGetEbox()
        _jsonMap = {}
        _testResult = CHK_RESULT.PASS
        _userlist = []

        userTypes   =   ['grid', 'oracle']
        grpTypes    =   ['OINSTALLGROUP','DBA_GROUP','OPER_GROUP','OSDBA','OSOPER','OSASM']

        # Retrieve clusterOwner User for current cluster
        # TBD: should we expect more than one cluster
        _cluster = _ebox.mGetClusters().mGetCluster()
        _clusterId = _cluster.mGetCluId()

        self.logger.mAppendLog(LOG_TYPE.INFO, '\n *** Validate Users and Groups listed in XML file for cluster: %s' %(_clusterId))

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

        _jsonMap['userList'] = _userlist
        _usrCnt = 0
        for _userId  in _userlist:
            _jsonMap[_userId] = {}
            _userConfig =  _ebox.mGetUsers().mGetUser(_userId)

            if (_userConfig.mGetUserType() == userTypes[_usrCnt]):
                _usrCnt += 1
            else:
                self.logger.mAppendLog(LOG_TYPE.WARNING, '*** Expecting userType as %s for userId %s' %(userTypes[_usrCnt],_userId), _jsonMap)

            _jsonMap[_userId]['userType'] = _userConfig.mGetUserType()
            _userGroup = _userConfig.mGetUserGroups()

            _grpCnt = 0
            _jsonMap[_userId]['groups'] = []
            for _grp  in _userGroup:
                _groupConfig = _ebox.mGetGroups().mGetGroup(_grp)
                grpId = int(_grp[-1:])
                grpType = _groupConfig.mGetGroupType()
                _jsonMap[_userId]['groups'].append("%s: %s" %(_grp,grpType))
                if(grpType == grpTypes[grpId-1]):
                    _grpCnt += 1
                else:
                    self.logger.mAppendLog(LOG_TYPE.WARNING, '*** Expecting grpType as %s for user %s with groupId %s' %(grpTypes[grpId-1],_userId, _grp), _jsonMap)

            #Expecting: 4 i.e.   1423 - oracle  |   1456 - grid
            if(_grpCnt != 4):
                self.logger.mAppendLog(LOG_TYPE.ERROR, '*** user %s do not have all required group permissions' %(_userId), _jsonMap)
                _testResult = CHK_RESULT.FAIL

        #Expecting:  2 oracle & grid user
        if(_usrCnt != len(userTypes)):
            self.logger.mAppendLog(LOG_TYPE.ERROR, " XML file does not contain required user permisions", _jsonMap)
            _testResult = CHK_RESULT.FAIL

        _jsonMap['TestResult'] = _testResult
        self.logger.mAppendLog(LOG_TYPE.INFO, '*** Users listed in XML file: %s' %(_userlist), _jsonMap)

        return self.logger.mUpdateResult(_testResult, _jsonMap)


    #
    # Check Machine Configuration
    #
    def mCheckMachineConfig(self):

        _eBox = self.mGetEbox()
        _jsonMap = {}
        _testResult = CHK_RESULT.PASS
        _eboxnetworks = _eBox.mGetNetworks()
        _clu_host_d = self.mGetHc().mGetClusterHostD()

        self.logger.mAppendLog(LOG_TYPE.INFO, '\n *** The nodes listed in the XML file:')

        _machine_list  = []
        _clusters  = _eBox.mGetClusters().mGetClusters()
        #get machine details from software/clusters/cluster xml
        for _cluId in _clusters:
            _machine_list += _eBox.mGetClusters().mGetClusterMachines(_cluId)

        _mac_list = _eBox.mGetMachines()
        _ml = _mac_list.mGetMachineConfigList()
        for _mac in _machine_list:
             # Hostname
             _mac_hostname = _ml[_mac].mGetMacHostName()
             self.logger.mAppendLog(LOG_TYPE.INFO,'Machine Hostname: %s' %(_mac_hostname))

             _jsonMap[_mac_hostname] = {}
             _jsonMap[_mac_hostname]['logs'] = {}
             _jsonMap[_mac_hostname]['hostName'] = _mac_hostname

             if(_ml[_mac].mGetMacType() == 'compute' and _ml[_mac].mGetMacOsType() == 'LinuxGuest'):
                 _mac_vmImageName = _ml[_mac].mGetMacVMImgName()
                 _mac_vmImageVersion = _ml[_mac].mGetMacVMImgVersion()
                 _jsonMap[_mac_hostname]['DomUImageName'] = _mac_vmImageName
                 self.logger.mAppendLog(LOG_TYPE.INFO,'***                     DomUImageName: \t %s' %(_mac_vmImageName), _jsonMap)

                 _jsonMap[_mac_hostname]['ImageVersion']  = _mac_vmImageVersion
                 self.logger.mAppendLog(LOG_TYPE.INFO,'***                      ImageVersion: \t %s' %(_mac_vmImageVersion), _jsonMap)

                 if (_mac_vmImageName != 'default'):
                    self.logger.mAppendLog(LOG_TYPE.WARNING, "DomUImageName %s is not set as 'default' for Hostname %s"
                                      %(_mac_vmImageName, _mac_hostname), _jsonMap)

                 if(_mac_vmImageVersion != 'default'):
                     self.logger.mAppendLog(LOG_TYPE.WARNING, "ImageVersion %s is not set as 'default' for Hostname %s"
                                       %(_mac_vmImageVersion, _mac_hostname), _jsonMap)

             # Type of machine - compute/storage/switch
             _mac_type = _ml[_mac].mGetMacType()
             self.logger.mAppendLog(LOG_TYPE.INFO,'***                      Machine Type: \t %s' %(_mac_type), _jsonMap)
             _jsonMap[_mac_hostname]['machineType'] = _mac_type

             # IP Address of the machine
             _neto = None
             _neto = _eboxnetworks.mGetNetworkConfigByName(_mac_hostname)
             if _neto != None:
                 _mac_ip = _neto.mGetNetIpAddr()
                 self.logger.mAppendLog(LOG_TYPE.INFO,'***                Machine IP Address: \t %s' %(_mac_ip), _jsonMap)
                 _jsonMap[_mac_hostname]['ipAddress'] = _mac_ip
             else:
                 self.logger.mAppendLog(LOG_TYPE.ERROR, '*** Network information not found for %s. Check XML file ***' %(_mac_hostname), _jsonMap)
                 _jsonMap[_mac_hostname]['TestResult'] = CHK_RESULT.FAIL
                 continue # Possibly incorrect hostName in XML

             # Check for IP address validity
             try:
                 socket.inet_aton(_mac_ip)
                 self.logger.mAppendLog(LOG_TYPE.INFO,'***                  Valid IP Address: \t True')
                 _jsonMap[_mac_hostname]['validIP'] = "True"
             except socket.error:
                 self.logger.mAppendLog(LOG_TYPE.ERROR, "Incorrect IP Address %s for Hostname %s" %(_mac_ip, _mac_hostname), _jsonMap)
                 _jsonMap[_mac_hostname]['validIP'] = "False"
                 _testResult = CHK_RESULT.FAIL

             # Ping status
             if _mac_hostname in _clu_host_d:
                 _clunode = _clu_host_d[_mac_hostname]
                 self.logger.mAppendLog(LOG_TYPE.INFO, '***                       Ping Status: \t %s' %(_clunode.mGetPingable()))

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
                     self.logger.mAppendLog(LOG_TYPE.INFO, '***          Hostname as per nslookup: \t %s' %(_nslout))
                     _jsonMap[_mac_hostname]['fqdn'] = _nslout
                     if _nslout.split('.')[0] != _mac_hostname.split('.')[0]:
                         self.logger.mAppendLog(LOG_TYPE.WARNING, "Hostname via nslookup for %s is %s while in XML it is %s" %(_mac_ip, _nslout, _mac_hostname), _jsonMap)
                         _testResult = CHK_RESULT.FAIL
             except:
                 if _found == "False":
                     self.logger.mAppendLog(LOG_TYPE.WARNING, "nslookup failed for IP Address %s" %(_mac_ip), _jsonMap)
                     _testResult = CHK_RESULT.FAIL

             _jsonMap[_mac_hostname]['TestResult'] = _testResult

        return self.logger.mUpdateResult(_testResult, _jsonMap)


    # end mCheckMachineConfig


    #
    # Check Machine Configuration
    #
    def mCheckDiskGroup(self):

        _ebox = self.mGetEbox()
        _jsonMap = {}
        _testResult = CHK_RESULT.PASS

        self.logger.mAppendLog(LOG_TYPE.INFO, '\n *** The diskGroups listed in the XML file:')

        #
        # Fetch ClusterID
        #
        _cluster = _ebox.mGetClusters().mGetCluster()
        _cluId = int(_cluster.mGetCluId().split('_')[0][1:])
        self.logger.mAppendLog(LOG_TYPE.INFO, '***                         cluster ID: \t %s' %(_cluster.mGetCluId()))
        _jsonMap['clusterID'] = _cluster.mGetCluId()

        _dgl = _cluster.mGetCluDiskGroups()
        for _dg in _dgl:
            _dgc = _ebox.mGetStorage().mGetDiskGroupConfig(_dg)
            _dg_id = _dgc.mGetDgId()
            _dg_name = _dgc.mGetDgName()
            _dg_slsz = _dgc.mGetSliceSize()
            _dg_dgsz = _dgc.mGetDiskGroupSize()

            _jsonMap[_dg] = {}
            _jsonMap[_dg]['dgId'] = _dg_id
            _jsonMap[_dg]['dgName'] = _dg_name
            _jsonMap[_dg]['dgSliceSize'] = _dg_slsz
            _jsonMap[_dg]['dgGroupSize'] = _dg_dgsz

            self.logger.mAppendLog(LOG_TYPE.INFO, '          Disk Group ID: %s' %(_dg_id))
            self.logger.mAppendLog(LOG_TYPE.INFO, '***                   Disk Group Name: \t %s' %(_dg_name))

            # verify disk group naming convention
            # NAMECX where the DG ends with CX and X equals to the cluster id. e.g. DBFSC1, RECOC2.
            # not checking for ACFS, as it has been asigned at runtime with ACFSC1_DG1/DG2
            _dg_name_pattern = re.compile("^(DBFS|DATA|RECO|SPR)C(\d+)$")
            _dg_match = _dg_name_pattern.match(_dg_name)
            #fetch cluster id, subtracted by -1 as dg id starts with 1 while cluster id starting with 0
            if _dg_match is not None and (int(_dg_match.group(2)) - 1) == _cluId:
                self.logger.mAppendLog(LOG_TYPE.INFO, '***             Valid Disk Group Name: \t True')
                _jsonMap[_dg]['TestResult'] = "Pass"
            else:
                _testResult = CHK_RESULT.FAIL
                self.logger.mAppendLog(LOG_TYPE.ERROR, "Invalid Disk Group Name %s" %(_dg_name), _jsonMap)
                _jsonMap[_dg]['TestResult'] = CHK_RESULT.FAIL

            self.logger.mAppendLog(LOG_TYPE.INFO, '***             Disk Group Slice Size: \t %s' %(_dg_slsz))
            self.logger.mAppendLog(LOG_TYPE.INFO, 'NFO','***                   Disk Group Size: \t %s' %(_dg_dgsz))

        return self.logger.mUpdateResult(_testResult, _jsonMap)

    # end mCheckDiskGroup


    def mValidateNwOverlap(self):

        _eBox = self.mGetEbox()
        _jsonMap = {}
        _testResult = CHK_RESULT.PASS
        _nwTypes = ['admin', 'backup', 'client', 'Ilom']
        _nwIntfList = []

        _cluster_host_d = self.mGetHc().mGetClusterHostD()
        _eBoxNetworks = _eBox.mGetNetworks()

        self.logger.mAppendLog(LOG_TYPE.INFO, '\n *** Check for network overlapping ***\n')

        for _host in _cluster_host_d.keys():
            _clunode = _cluster_host_d[_host]
            if _clunode.mGetNodeType() == 'switch':
                continue
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
                self.logger.mAppendLog(LOG_TYPE.INFO, 'gateway UNDEFINED, taking default mac gateway ', _jsonMap)
                #TBD
                _gw = _eBox.mGetMachines().mGetMacGateWay()

            #PingTest/ArpTest for gateway
            if _eBox.mIsOciEXACC():
                if (_gw not in _gwlist) and  (not _eBox.mArpingHost(_intf, _gw)):
                    _gwlist.append(_gw)
                    self.logger.mAppendLog(LOG_TYPE.ERROR, "Unable to connect to the IP Address (%s) listed as a gateway in XML." %(_gw), _jsonMap)
                    _testResult = CHK_RESULT.FAIL
            else:
                if (_gw not in _gwlist) and  (not _eBox.mPingHost(_gw)):
                    _gwlist.append(_gw)
                    self.logger.mAppendLog(LOG_TYPE.ERROR, "Unable to connect to the IP Address (%s) listed as a gateway in XML." %(_gw), _jsonMap)
                    _testResult = CHK_RESULT.FAIL

            # BUG 33979523 - Remove the Network and Gateway Subnet validation for Admin networks
            if _netType == 'admin':
                continue

            _subnetIp = self.mGetSubnet(_ip, _netMask)
            _subnetGw = self.mGetSubnet(_gw, _netMask)
            _jsonMap[_netName] = {}

            self.logger.mAppendLog(LOG_TYPE.INFO, '***                       netName: \t %s' %(_netName), _jsonMap)
            self.logger.mAppendLog(LOG_TYPE.INFO, '***                       ipAddr  : \t %s' %(_ip), _jsonMap)
            self.logger.mAppendLog(LOG_TYPE.INFO, '***                       netmask : \t %s' %(_netMask), _jsonMap)
            self.logger.mAppendLog(LOG_TYPE.INFO, '***                       gw      : \t %s' %(_gw), _jsonMap)
            _jsonMap[_netName] = {}
            _jsonMap[_netName]['ipAddress']   = _ip
            _jsonMap[_netName]['netMask']     = _netMask
            _jsonMap[_netName]['gw']          = _gw

            #compare subnet for ip/netmask and gateway/netmask
            if(_subnetIp == _subnetGw):
                self.logger.mAppendLog(LOG_TYPE.INFO, '***                       subnet  : \t %s' %(_subnetIp), _jsonMap)
                _jsonMap[_netName]['subnet']      = _subnetIp
                _jsonMap[_netName]['TestResult'] = CHK_RESULT.PASS
                self.logger.mAppendLog(LOG_TYPE.INFO, '***                  Subnet Match: \t True', _jsonMap)
            else:
                self.logger.mAppendLog(LOG_TYPE.WARNING, 'ip %s and gw %s should be on same subnet for nw interface %s' %(_ip, _gw, _netName), _jsonMap)
                _testResult = CHK_RESULT.FAIL
                _jsonMap[_netName]['TestResult'] = CHK_RESULT.FAIL
                self.logger.mAppendLog(LOG_TYPE.INFO, '***                       ipSubnet: \t %s' %(_subnetIp), _jsonMap)
                self.logger.mAppendLog(LOG_TYPE.INFO, '***                       gwSubnet: \t %s' %(_subnetGw), _jsonMap)
                _jsonMap[_netName]['ipSubnet']      = _subnetIp
                _jsonMap[_netName]['gwSubnet']      = _subnetGw
                self.logger.mAppendLog(LOG_TYPE.INFO, '***                  Subnet Match: \t False', _jsonMap)

        self.logger.mAppendLog(LOG_TYPE.INFO, '\n *** Check for network overlapping completed***\n')
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    #
    # Get Image Version
    #
    def mCheckImageVersion(self, aHost):
        _host = aHost
        _imgver = None
        _exaspliceimgver = None
        _switches = []
        _switch = False

        _ebox = self.mGetEbox()
        _cells = _ebox.mReturnCellNodes()
        if _ebox.mIsOciEXACC() and _ebox.mIsKVM():
            _switches = _ebox.mReturnSwitches(aMode=True, aRoceQinQ=True)
        else:
            _switches = _ebox.mReturnSwitches(aMode=True)

        _jsonMap = {}
        _testResult = CHK_RESULT.PASS
        self.logger.mAppendLog(LOG_TYPE.INFO, '*** Checking Image Version for %s ***' % (_host))

        if _host in _switches:
            if _ebox.mIsOciEXACC() and _ebox.mIsKVM():
                _node = self.mGetNode(_host, aUser='admin')
                _cmd_str = "show version | grep version"
            else:
                _node = self.mGetNode(_host)
                _cmd_str = '/usr/local/bin/version | grep -i version'
            _switch = True
        else:
            _node = self.mGetNode(_host)
            _cmd_str = '/usr/local/bin/imageinfo -version -status'

        _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
        _out = _o.readlines()
        _filename = self.mGetResultDir() + "hc_ImageVersion_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
        self.mWriteResultToFile(_filename,_out)
        if _out:
            ##
            ## The output of /usr/local/bin/imageinfo -version -status resembles:
            ##
            ## Image Version : 12.1.2.3.4.170111
            ## Image Status : success

            _out = self.mRemoveBlankLinesHelper(_out)
            if _switch:
                if _ebox.mIsOciEXACC() and _ebox.mIsKVM():
                    for _ret in _out:
                        if 'BIOS' in _ret:
                            _bios_key = _ret.split(':')[0].strip()
                            _bios_value = _ret.split(':')[1].strip()
                            _jsonMap[_bios_key] = _bios_value

                        if 'NXOS' in _ret:
                            _nxos_key = _ret.split(':')[0].strip()
                            _nxon_value = _ret.split(':')[1].strip()
                            _jsonMap[_nxos_key] = _nxon_value

                        if 'System version' in _ret:
                            _system_key = _ret.split(':')[0].strip()
                            _system_value = _ret.split(':')[1].strip()
                            _jsonMap[_system_key] = _system_value
                else:
                    _sun_dc_key = _out[0].split(':')[0].strip()
                    _sun_dc_value = _out[0].split(':')[1].strip()
                    _jsonMap[_sun_dc_key] = _sun_dc_value

                    _bios_key = _out[1].split(':')[0].strip()
                    _bios_value = _out[1].split(':')[1].strip()
                    _jsonMap[_bios_key] = _bios_value
            else:
                _imgver = _out[0].split(':')[1].strip()
                _imgstat = _out[1].split(':')[1].strip()
                _jsonMap["Image Version"] = _imgver
                _jsonMap["Image Status"] = _imgstat

                self.logger.mAppendLog(LOG_TYPE.INFO, "Image Version on %s: %s, Image Status: %s" %(_host, _imgver, _imgstat), _jsonMap)

                if not _out or not _imgver or not _imgstat:

                    self.logger.mAppendLog(LOG_TYPE.WARNING, "On host %s, failed to get image version or image status" %(_host), _jsonMap)

                    _testResult = CHK_RESULT.FAIL

        if _switch:
            ebLogInfo("Exasplice version is not supported on switches")
        elif _host not in _cells:
            _cmd_str = '/usr/local/bin/imageinfo -verexasplice'
            _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
            _out = _o.readlines()
            self.mWriteResultToFile(_filename,_out)
            if _out:
                ##
                ## The output of /usr/local/bin/imageinfo -verexasplice resembles:
                ##
                ## [root@slcs27adm03 ~]# imageinfo -verexasplice
                ## 201026

                _out = self.mRemoveBlankLinesHelper(_out)
                if re.match("[0-9]{1}[0-9.]*", _out[0].strip()):
                    _exaspliceimgver = _out[0].strip()
                _jsonMap["Exasplice Image Version"] = _exaspliceimgver

                self.logger.mAppendLog(LOG_TYPE.INFO, "Exasplice Image Version on %s: %s" %(_host, _exaspliceimgver), _jsonMap)

            if not _out or not _exaspliceimgver:

                self.logger.mAppendLog(LOG_TYPE.WARNING, "On host %s, failed to get Exasplice image version" %(_host), _jsonMap)
                _jsonMap["Exasplice Image Version"] = ""

        self.mDisconnectNode(_node)
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    ## Checking space on Node
    ## Lists space on various partitions
    def mCheckNodeSpace(self, aHost):

        _host = aHost
        _node = self.mGetNode(_host)

        _ebox = self.mGetEbox()
        _jsonMap = {}
        _resMap={}
        _attributes = []

        _testResult = CHK_RESULT.PASS
        _cmd_str = 'df -kHP'

        _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
        if _o:
            _output_lines = _o.readlines()
            _filename = self.mGetResultDir() + "hc_NodeSpace_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            self.mWriteResultToFile(_filename,_output_lines)

            _output_lines = self.mRemoveBlankLinesHelper(_output_lines)

            #parsing code
            for _index in range(0,len(_output_lines)):
                _candidate = _output_lines[_index].split()
                if len(_candidate) > 1:
                    _attributes = _candidate
                    break

            _attributes[-2] = ' '.join(_attributes[-2:])
            _attributes = _attributes[:-1]


            for _index in range(1,len(_output_lines)):
                _line = _output_lines[_index].split()
                _details = {}
                for _ind in range(0,len(_attributes)):
                    _details[_attributes[_ind]]=_line[_ind]
                _resMap[_index]=_details
            _jsonMap[_host] = _resMap
            self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, space check command successful!!" %(_host), _jsonMap)
            ## Sample Output
            ## "2": {
            ##                "Avail": "16G",
            ##                "Filesystem": "tmpfs",
            ##                "Mounted on": "/dev/shm",
            ##                "Size": "16G",
            ##                "Use%": "5%",
            ##                "Used": "648M"
        else:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, space check command failed!!" %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    ## Checks memory on node
    def mCheckMemory(self, aHost):

        _host = aHost
        _node = self.mGetNode(_host)

        _ebox = self.mGetEbox()
        _jsonMap = {}

        _testResult = CHK_RESULT.PASS
        _cmd_str = 'vmstat -s'

        _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
        if _o:
            _output_lines = _o.readlines()
            _filename = self.mGetResultDir() + "hc_Memory_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            self.mWriteResultToFile(_filename,_output_lines)
            #parsing code
            for _index in range(0,len(_output_lines)-1):
                _line = _output_lines[_index].split()
                if len(_line) > 1:
                    _label = ' '.join(_line[1:])
                    _jsonMap[_label] = _line[0]
            self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, mem check command successful!!" %(_host), _jsonMap)
            ## Sample Output
            ## "CPU context switches": "3793163687",
            ## "IO-wait cpu ticks": "1091113",
            ## "IRQ cpu ticks": "1932",
            ## "active memory": "2111188",
            ## "boot time": "1542279768",
            ## "buffer memory": "202152",
            ## "free memory": "2101760",
        else:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, mem check command failed!!" %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL
        self.mDisconnectNode(_node)
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    ## Checks Grid Infrastructure
    def mCheckGridInfra(self, aHost):

        _host = aHost
        _node = self.mGetNode(_host ,'grid')

        _ebox = self.mGetEbox()
        _jsonMap = {}

        _testResult = CHK_RESULT.PASS
        _cmd_str='crsctl check cluster -all'

        _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
        if _o:
            _output_lines = _o.readlines()
            _filename = self.mGetResultDir() + "hc_GridInfra_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            self.mWriteResultToFile(_filename,_output_lines)
            _output_lines = self.mRemoveBlankLinesHelper(_output_lines)
            _resMap={}
            _label = ''

            for _line in _output_lines:
                if _line[-1] == ':':
                    if len(_label) > 0:
                        _jsonMap[_label] = _resMap
                    _label = _line.split(':')[0]
                    _resMap = {}
                else:
                    _line = _line.split(':')
                    if len(_line) > 1:
                        _resMap[_line[0]] = _line[1]
            if len(_label) > 0:
                _jsonMap[_label] = _resMap
            self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, grid infra check command successful!!" %(_host), _jsonMap)
        ## Sample Output
        ## "CRS-4529": " Cluster Synchronization Services is online",
        ## "CRS-4533": " Event Manager is online",
        ## "CRS-4537": " Cluster Ready Services is online"
        else:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, grid infra check command failed!!" %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL
        self.mDisconnectNode(_node)
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    def mDbInstanceStatusCheck(self, aHost ):
        _host = aHost
        _node = self.mGetNode(_host ,'grid')
        _jsonMap = {}
        _testResult = CHK_RESULT.PASS
        _cmd_str='crsctl   stat res  -w "TYPE = ora.database.type" '
        _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
        if _o:
            _output_lines = _o.readlines()
            _filename = self.mGetResultDir() + "hc_DbInstanceStatusCheck_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            self.mWriteResultToFile(_filename,_output_lines)
            _output_lines = self.mRemoveBlankLinesHelper(_output_lines)
            self.logger.mAppendLog(LOG_TYPE.INFO,
                               " mDbInstanceStatusCheck   op  got is %s type is %s " % (_output_lines, type(_output_lines)))
            _index = 0
            _extractionList = ['TYPE', 'TARGET', 'STATE']
            self.logger.mAppendLog(LOG_TYPE.INFO, "iterating the results  in progress")
            while (_index < len(_output_lines) ) :
                self.logger.mAppendLog(LOG_TYPE.INFO, "iterating %s" %(_output_lines[_index]))
                if ( _output_lines[_index].split('=')[0] == 'NAME') :
                    dbname =  _output_lines[_index].split('=')[1]
                    _inner_index = 0
                    _index += 1
                    valmap =  {}
                    while( _inner_index <  len(_extractionList) )  :
                        # extracting only the  innerlist values from outer result list
                        attribute =  _output_lines[_index].split('=')
                        self.logger.mAppendLog(LOG_TYPE.INFO, "iterating inner attribute  %s" %(attribute))
                        _index +=1
                        key = attribute[0]
                        value = attribute[1]
                        if (key == 'NAME' ) :
                            break ; #break the loop if some attribute missed
                        if (key in _extractionList ) :
                            valmap.update({key : value})
                            _inner_index +=1
                    _jsonMap .update({dbname : valmap})
                else :
                    self.logger.mAppendLog(LOG_TYPE.ERROR, "on the node %s  value   %s is not captured " %(_host,_output_lines[_index]))
                    _index +=1
            self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s,  DbInstanceStatusCheck command successful!!" %(_host), _jsonMap)
        else:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, DbInstanceStatusCheck command failed!!" %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL
        self.mDisconnectNode(_node)
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    ## Checks SCAN Status
    def mCheckScanStatus(self, aHost):

        _host = aHost
        _node = self.mGetNode(_host, 'grid')

        _ebox = self.mGetEbox()
        _jsonMap = {}

        _testResult = CHK_RESULT.PASS
        _cmd_str = 'srvctl status scan'

        _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
        if _o:
            _output_lines = _o.readlines()
            _filename = self.mGetResultDir() + "hc_SCANStatus_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            self.mWriteResultToFile(_filename,_output_lines)
            _jsonMap = self.mCopyResultHelper(_output_lines)
            self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, SCAN Status check command successful!!" %(_host), _jsonMap)
            ## Sample Output
            ## " SCAN VIP scan1 is enabled\n SCAN VIP scan1 is running on node slcs08adm05vm07-v264\n"
        else:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, SCAN Status check command failed!!" %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    ## Checks the status of VIP on the node
    def mCheckVipStatus(self, aHost):

        _host = aHost
        _host_first_name = _host.split('.')[0]
        _node = self.mGetNode(_host, 'grid')

        _ebox = self.mGetEbox()
        _jsonMap = {}

        _testResult = CHK_RESULT.PASS
        _cmd_str = "srvctl status vip -n "+ _host_first_name

        _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
        if _o:
            _output_lines = _o.readlines()
            _filename = self.mGetResultDir() + "hc_VipStatus_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            self.mWriteResultToFile(_filename,_output_lines)
            _jsonMap = self.mCopyResultHelper(_output_lines)
            self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, VIP Status check command successful!!" %(_host), _jsonMap)
            ## Sample Output
            ##" VIP 10.252.165.70 is enabled\n VIP 10.252.165.70 is running on node: slcs08adm05vm07-v264\n"
        else:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, VIP Status check command failed!!" %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        return self.logger.mUpdateResult(_testResult, _jsonMap)


    ## Checks the SCAN using the Cluvfy utility
    def mCheckSCANCluvfy(self, aHost):

        _host = aHost
        _host_first_name = _host.split('.')[0]
        _node = self.mGetNode(_host, 'grid')

        _ebox = self.mGetEbox()
        _jsonMap = {}

        _testResult = CHK_RESULT.PASS
        _cmd_str = "cluvfy comp scan"

        _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
        if _o:
            _output_lines = _o.readlines()
            _filename = self.mGetResultDir() + "hc_SCANCluvfy_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            self.mWriteResultToFile(_filename,_output_lines)
            _jsonMap = self.mCopyResultHelper(_output_lines)
            self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, SCAN Cluvfy check command successful!!" %(_host), _jsonMap)
            ## Sample Output
            ## \n Verifying Single Client Access Name (SCAN) ...\n Verifying DNS/NIS name service 'slcs08vm05-scan7-v214' ...\n Verifying Name Service Switch Configuration File Integrity ..
        else:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, SCAN Cluvfy check command failed!!" %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    ## Checks the status of CDB
    def mCheckCDBStatusCheck(self, aHost):

        _host = aHost
        _host_first_name = _host.split('.')[0]
        _node = self.mGetNode(_host, 'oracle')

        _ebox = self.mGetEbox()
        _jsonMap = {}

        _testResult = CHK_RESULT.PASS
        _oratab_entries = self.mParseOratab(_node)
        _cmd_str_template = "dbaascli database status --dbname "
        for _entry in _oratab_entries:
            if _entry[0][0] != '+':
                _db_name = _entry[0]
                _cmd_str = _cmd_str_template + _db_name   #dbaascli database status --dbname <dbname>
                _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
                if _o:
                    _output_lines = _o.readlines()
                    _filename = self.mGetResultDir() + "hc_CDBStatusCheck_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
                    self.mWriteResultToFile(_filename,_output_lines)
                    _jsonMap = self.mCopyResultHelper(_output_lines)
            ## Sample Output
            ## "Instance db1c4aa21 is running on node slcs08adm05vm07-v264. Instance status: Open,HOME=/u02/app/oracle/product/12.1.0/dbhome_2.\n
                else:
                    self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, CDB Status check command failed!!" %(_host), _jsonMap)
                    _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    ## Checks whether the ASM grid disks are deactivated or not. Patching can proceed only if asm griddisks are deactivated
    def mCheckCellDeactivation(self, aHost):

        _host = aHost
        _host_first_name = _host.split('.')[0]
        _node = self.mGetNode(_host)

        _ebox = self.mGetEbox()
        _jsonMap = {"Status":"PASS"}

        _testResult = CHK_RESULT.PASS

        _cmd_str = "cellcli -e list griddisk attributes name, asmmodestatus, asmdeactivationoutcome where asmmodestatus=\'ONLINE\' and asmdeactivationoutcome ! =\'Yes\'"

        _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)

        if _o:

            _jsonMap = {"Status":"FAILED"}
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On Cell %s, asmdeactivationoutcom is not yes." %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL
        else:
            self.logger.mAppendLog(LOG_TYPE.INFO, "On Cell %s, asmdeactivationoutcom is yes." %(_host), _jsonMap)
        self.mDisconnectNode(_node)
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    ## Checks for running ASM operations.
    def mCheckAsmOperation(self, aHost):

        try:
            _host = aHost
            _node = self.mGetNode(_host, 'grid')

            _ebox = self.mGetEbox()
            _jsonMap = {"Running_Operation":"No"}

            _testResult = CHK_RESULT.PASS

            _oratab_entries = self.mParseOratab(_node)
            _asm_sid = ''
            _asm_home = ''
            for _entry in _oratab_entries:
                if _entry[0][0] =='+':
                    _asm_sid=_entry[0]
                    _asm_home=_entry[1]

            _cmd_str = "export ORACLE_SID={0}; export ORACLE_HOME={1}; echo `select * from v$asm_operation;` | sqlplus / as sysasm".format(_asm_sid,_asm_home)

            _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
            if _o:
                _output_lines = _o.readlines()
                _filename = self.mGetResultDir() + "hc_AsmOperation_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
                self.mWriteResultToFile(_filename,_output_lines)
                _output_lines = self.mRemoveBlankLinesHelper(_output_lines)
                _flag = False
                for _line in _output_lines:
                    _line = str(_line)
                    if "rows" in _line:
                        _flag = True

                if _flag:
                    _jsonMap["Running_Operation"]="Yes"
                    self.logger.mAppendLog(LOG_TYPE.ERROR, "On DomU %s, ASM operation is running." %(_host), _jsonMap)
                    _testResult = CHK_RESULT.FAIL
                else:
                    self.logger.mAppendLog(LOG_TYPE.INFO, "On DomU %s, ASM Operation check successful!!" %(_host), _jsonMap)
            else:
                self.logger.mAppendLog(LOG_TYPE.ERROR, "On DomU %s, ASM Operation check failed!!" %(_host), _jsonMap)
                _testResult = CHK_RESULT.FAIL
        except Exception as e:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On DomU %s, ASM Operation check failed!!" %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    ## Checks whether the ASM mode is normal or not.
    def mCheckAsmMode(self, aHost):

        try:
            _host = aHost
            _node = self.mGetNode(_host, 'grid')

            _ebox = self.mGetEbox()
            _jsonMap = {}

            _testResult = CHK_RESULT.PASS

            _oratab_entries = self.mParseOratab(_node)
            _asm_sid = ''
            _asm_home = ''
            for _entry in _oratab_entries:
                if _entry[0][0] =='+':
                    _asm_sid=_entry[0]
                    _asm_home=_entry[1]
            
            # Add /bin to _asm_home for the full path
            _bin_path = f"{_asm_home}/bin"
            _cmd_str = f"export PATH={_bin_path}:$PATH;export ORACLE_SID={_asm_sid}; export ORACLE_HOME={_asm_home}; echo \"SELECT SYS_CONTEXT(\'sys_cluster_properties\', \'cluster_state\') FROM dual;\" | sqlplus / as sysasm"

            _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
            if _o:
                _output_lines = _o.readlines()
                _filename = self.mGetResultDir() + "hc_AsmMode_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
                self.mWriteResultToFile(_filename,_output_lines)
                _output_lines = self.mRemoveBlankLinesHelper(_output_lines)
                _flag = False
                for _line in _output_lines:
                    if "normal" in _line.lower():
                        _jsonMap["Status"] = "Normal"
                        _flag = True

                if not _flag:
                    _jsonMap["Status"]="Error"
                    self.logger.mAppendLog(LOG_TYPE.ERROR, "On DomU %s, ASM Status is not normal." %(_host), _jsonMap)
                    _testResult = CHK_RESULT.FAIL
                else:
                    self.logger.mAppendLog(LOG_TYPE.INFO, "On DomU %s, ASM Status is normal." %(_host), _jsonMap)
            else:
                self.logger.mAppendLog(LOG_TYPE.ERROR, "On DomU %s, ASM Status is not normal." %(_host), _jsonMap)
                _testResult = CHK_RESULT.FAIL
        except Exception as e:
            _jsonMap["Status"]="Error"
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On DomU %s, ASM Status is not normal." %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    ## Checks whether the ASM power limit is not 0.
    def mCheckAsmPowerLimit(self, aHost):

        try:
            _host = aHost
            _node = self.mGetNode(_host, 'grid')

            _ebox = self.mGetEbox()
            _jsonMap = {}

            _testResult = CHK_RESULT.PASS

            _oratab_entries = self.mParseOratab(_node)
            _asm_sid = ''
            _asm_home = ''
            for _entry in _oratab_entries:
                if _entry[0][0] =='+':
                    _asm_sid=_entry[0]
                    _asm_home=_entry[1]
            
            # Add /bin to _asm_home for the full path
            _bin_path = f"{_asm_home}/bin"
            _cmd_str = f"export PATH={_bin_path}:$PATH;export ORACLE_SID={_asm_sid}; export ORACLE_HOME={_asm_home};echo show parameter limit | sqlplus / as sysasm | grep asm_power_limit"

            _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
            if _o:
                _output_lines = _o.readlines()
                _filename = self.mGetResultDir() + "hc_AsmPowerLimit_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
                self.mWriteResultToFile(_filename,_output_lines)
                _output_lines = self.mRemoveBlankLinesHelper(_output_lines)
                _flag = True
                _value = _output_lines[0].split()[2]
                if _value == "0":
                    _flag = False

                if not _flag:
                    _jsonMap["Status"]="ASM Power Limit Set to 0"
                    self.logger.mAppendLog(LOG_TYPE.ERROR, "On DomU %s, ASM Power Limit is set to 0." %(_host), _jsonMap)
                    _testResult = CHK_RESULT.FAIL
                else:
                    _jsonMap["Status"]="ASM Power Limit is not 0"
                    self.logger.mAppendLog(LOG_TYPE.INFO, "On DomU %s, ASM Power Limit is not set to 0." %(_host), _jsonMap)
            else:
                self.logger.mAppendLog(LOG_TYPE.ERROR, "On DomU %s, ASM Power Limit not retrieved." %(_host), _jsonMap)
                _testResult = CHK_RESULT.FAIL
        except Exception as e:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On DomU %s, ASM Power Limit not retrieved." %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        return self.logger.mUpdateResult(_testResult, _jsonMap)
    def mCheckEXAVMIMAGESSpace(self, aHost):

        try:
            _host = aHost
            _node = self.mGetNode(_host)

            _ebox = self.mGetEbox()
            _jsonMap = {}
            _resMap={}
            _attributes = []

            _testResult = CHK_RESULT.PASS
            _cmd_str = 'df -kHP /EXAVMIMAGES'

            _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
            if _o:
                _output_lines = _o.readlines()
                _filename = self.mGetResultDir() + "hc_EXAVMIMAGESSpace_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
                self.mWriteResultToFile(_filename,_output_lines)

                _jsonMap[_host] = ' '.join(_output_lines)
                _output_lines = self.mRemoveBlankLinesHelper(_output_lines)

                #parsing code
                for _index in range(0,len(_output_lines)):
                    _candidate = _output_lines[_index].split()
                    if len(_candidate) > 1:
                        _attributes = _candidate
                        break

                _attributes[-2] = ' '.join(_attributes[-2:])
                _attributes = _attributes[:-1]

                _line = _output_lines[1].split()
                _details = {}
                for _ind in range(0,len(_attributes)):
                    _details[_attributes[_ind]]=_line[_ind]
                _jsonMap[_host] = _details
                self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, /EXAVMIMAGES space check command successful!!" %(_host), _jsonMap)
            else:
                self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, /EXAVMIMAGES space check command failed!!" %(_host), _jsonMap)
                _testResult = CHK_RESULT.FAIL
        except Exception as e:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, /EXAVMIMAGES space check command failed!!" %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        _jsonMap["hcDescription"] = "result of command: df -kHP /EXAVMIMAGES "
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    ## Checking DomUs on a Dom0 using xm/virsh list
    def mCheckDomUList(self, aHost):

        _host = aHost
        _node = self.mGetNode(_host)

        _ebox = self.mGetEbox()
        _jsonMap = {}
        _resMap={}
        _attributes = []

        _testResult = CHK_RESULT.PASS
        _vm = getHVInstance(_host)
        _cmd_str, _output_lines = _vm.mGetDomUList()

        if _output_lines:
            _filename = self.mGetResultDir() + "hc_DomUList_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            self.mWriteResultToFile(_filename,_output_lines)

            _output_lines = self.mRemoveBlankLinesHelper(_output_lines)

            #parsing code
            for _index in range(0,len(_output_lines)):
                _candidate = _output_lines[_index].split()
                if len(_candidate) > 1:
                    _attributes = _candidate
                    break

            for _index in range(1,len(_output_lines)):
                _line = _output_lines[_index].split()
                _details = {}
                for _ind in range(0,len(_attributes)):
                    _details[_attributes[_ind]]=_line[_ind]
                _resMap[_index]=_details
            _jsonMap[_host] = _resMap
            self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, %s command successful!!" %(_host, _cmd_str), _jsonMap)
        else:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, %s command failed!!" %(_host, _cmd_str), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        _jsonMap["hcDescription"] = "result of command: {}".format(_cmd_str)
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    ## Checking Xen Info on a Dom0 using xm/virsh info
    def mCheckXenInfo(self, aHost):

        _host = aHost
        _node = self.mGetNode(_host)

        _ebox = self.mGetEbox()
        _jsonMap = {}
        _attributes = []

        _testResult = CHK_RESULT.PASS

        _vm = getHVInstance(_host)
        _cmd_str, _output_lines = _vm.mGetDom0Info()
        if _output_lines:
            _filename = self.mGetResultDir() + "hc_XenInfo_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            self.mWriteResultToFile(_filename,_output_lines)

            _output_lines = self.mRemoveBlankLinesHelper(_output_lines)

            for _line in _output_lines:
                _spl = _line.split(':')
                _jsonMap[_spl[0]] = _spl[1]
            self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, %s command successful!!" %(_host, _cmd_str), _jsonMap)
        else:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, %s command failed!!" %(_host, _cmd_str), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        _jsonMap["hcDescription"] = "result of command: {} ".format(_cmd_str)
        return self.logger.mUpdateResult(_testResult, _jsonMap)


    ## Checking Xen Info on a Dom0 using xm/virsh info
    def mCheckXenLog(self, aHost):

        _host = aHost
        _node = self.mGetNode(_host)

        _ebox = self.mGetEbox()
        _jsonMap = {}
        _attributes = []

        _testResult = CHK_RESULT.PASS

        _vm = getHVInstance(_host)
        _cmd_str, _output_lines = _vm.mGetDom0Logs()
        if _output_lines:
            _filename = self.mGetResultDir() + "hc_XenLog_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            self.mWriteResultToFile(_filename,_output_lines)

            #KVM Operation is not supported. This operation is gated with NO_OPERATION keyword
            if _output_lines == "NO_OPERATION":
                _details = { "Status" : "NO_OPERATION" }
                _jsonMap[1]=_details
            else:
                _output_lines = self.mRemoveBlankLinesHelper(_output_lines)

            #_jsonMap["Log"] = '\n'.join(_output_lines)
            _jsonMap = self.mCopyResultHelper(_output_lines)
            self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, %s command successful!!" %(_host, _cmd_str), _jsonMap)
        else:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, %s command failed!!" %(_host, _cmd_str), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        _jsonMap["hcDescription"] = "result of command: {} ".format(_cmd_str)
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    ## Checking Xen Vcpu list on a Dom0 using xm vcpu-list/virsh cpuinfo
    def mCheckXenVcpuList(self, aHost):

        _host = aHost
        _node = self.mGetNode(_host)

        _ebox = self.mGetEbox()
        _jsonMap = {}
        _attributes = []

        _testResult = CHK_RESULT.PASS

        _vm = getHVInstance(_host)
        _cmd_str, _output_lines = _vm.mGetVcpuList()

        if _output_lines:
            _filename = self.mGetResultDir() + "hc_XenVcpuList_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            self.mWriteResultToFile(_filename,_output_lines)

            _output_lines = self.mRemoveBlankLinesHelper(_output_lines)

            #_jsonMap["Log"] = '\n'.join(_output_lines)
            _jsonMap = self.mCopyResultHelper(_output_lines)
            self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, %s  command successful!!" %(_host, _cmd_str), _jsonMap)
        else:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, %s command failed!!" %(_host, _cmd_str), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        _jsonMap["hcDescription"] = "result of command: {} ".format(_cmd_str)
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    ## Checking DomU uptime on a Dom0 using xm/virsh uptime
    def mCheckDomUUptime(self, aHost):

        _host = aHost
        _node = self.mGetNode(_host)

        _ebox = self.mGetEbox()
        _jsonMap = {}
        _resMap={}
        _attributes = []

        _testResult = CHK_RESULT.PASS

        _vm = getHVInstance(_host)
        _cmd_str, _output_lines = _vm.mGetUptime()
        if _output_lines:
            _filename = self.mGetResultDir() + "hc_DomUUptime_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            self.mWriteResultToFile(_filename,_output_lines)

            #KVM Operation is not supported. This operation is gated with NO_OPERATION keyword
            if _output_lines == "NO_OPERATION":
                _details = { "Status" : "NO_OPERATION" }
                _resMap[1]=_details
            else:
                _output_lines = self.mRemoveBlankLinesHelper(_output_lines)

                #parsing code
                for _index in range(0,len(_output_lines)):
                    _candidate = _output_lines[_index].split()
                    if len(_candidate) > 1:
                        _attributes = _candidate
                        break

                for _index in range(1,len(_output_lines)):
                    _line = _output_lines[_index].split()
                    _line[2] = ' '.join(_line[2:])
                    _line = _line[0:3]
                    _details = {}
                    for _ind in range(0,len(_attributes)):
                        _details[_attributes[_ind]]=_line[_ind]
                    _resMap[_index]=_details
            _jsonMap[_host] = _resMap
            self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, %s command successful!!" %(_host, _cmd_str), _jsonMap)
        else:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, %s command failed!!" %(_host, _cmd_str), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        _jsonMap["hcDescription"] = "result of command: {} ".format(_cmd_str)
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    ## Checking Mem Info on a Dom0 using cat /proc/meminfo | grep Mem
    def mCheckDom0MemInfo(self, aHost):

        _host = aHost
        _node = self.mGetNode(_host)

        _ebox = self.mGetEbox()
        _jsonMap = {}

        _testResult = CHK_RESULT.PASS
        _cmd_str = 'cat /proc/meminfo | grep Mem'

        _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
        if _o:
            _output_lines = _o.readlines()
            _filename = self.mGetResultDir() + "hc_Dom0MemInfo_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            self.mWriteResultToFile(_filename,_output_lines)

            _output_lines = self.mRemoveBlankLinesHelper(_output_lines)

            for _line in _output_lines:
                _spl = _line.split(':')
                _jsonMap[_spl[0]] = _spl[1]
            self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, mem info command successful!!" %(_host), _jsonMap)
        else:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, mem info command failed!!" %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        _jsonMap["hcDescription"] = "result of command: cat /proc/meminfo | grep Mem "
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    ## Checking CellOS Conf on a Dom0 using cat /opt/oracle.cellos/cell.conf
    def mCheckCellOSConf(self, aHost):

        _host = aHost
        _node = self.mGetNode(_host)

        _ebox = self.mGetEbox()
        _jsonMap = {}
        _attributes = []

        _testResult = CHK_RESULT.PASS
        _cmd_str = 'cat /opt/oracle.cellos/cell.conf'

        _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
        if _o:
            _output_lines = _o.readlines()
            _filename = self.mGetResultDir() + "hc_CellOSConf_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            self.mWriteResultToFile(_filename,_output_lines)

            _output_lines = self.mRemoveBlankLinesHelper(_output_lines)

            #_jsonMap["Log"] = '\n'.join(_output_lines)
            _jsonMap = self.mCopyResultHelper(_output_lines)
            self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, cellos conf command successful!!" %(_host), _jsonMap)
        else:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, cellos conf command failed!!" %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        _jsonMap["hcDescription"] = "result of command: cat /opt/oracle.cellos/cell.conf "
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    def mCheckBrctlShow(self, aHost):

        _host = aHost
        _node = self.mGetNode(_host)

        _ebox = self.mGetEbox()
        _jsonMap = {}
        _attributes = []

        _testResult = CHK_RESULT.PASS
        _cmd_str = 'brctl show'

        _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
        if _o:
            _output_lines = _o.readlines()
            _filename = self.mGetResultDir() + "hc_BrctlShow_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            self.mWriteResultToFile(_filename,_output_lines)

            _output_lines = self.mRemoveBlankLinesHelper(_output_lines)

            _jsonMap = self.mCopyResultHelper(_output_lines)
            self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, brctl show command successful!!" %(_host), _jsonMap)
        else:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, brctl show command failed!!" %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        _jsonMap["hcDescription"] = "result of command: brctl show "
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    def mCheckIfconfig(self, aHost):

        _host = aHost
        _node = self.mGetNode(_host)

        _ebox = self.mGetEbox()
        _jsonMap = {}
        _attributes = []

        _testResult = CHK_RESULT.PASS
        _cmd_str = 'ifconfig'

        _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
        if _o:
            _output_lines = _o.readlines()
            _filename = self.mGetResultDir() + "hc_Ifconfig_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            self.mWriteResultToFile(_filename,_output_lines)

            _output_lines = self.mRemoveBlankLinesHelper(_output_lines)

            _jsonMap = self.mCopyResultHelper(_output_lines)

            self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, brctl show command successful!!" %(_host), _jsonMap)
        else:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, brctl show command failed!!" %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        _jsonMap["hcDescription"] = "result of command: ifconfig "
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    def mCheckRoute(self, aHost):

        _host = aHost
        _node = self.mGetNode(_host)

        _ebox = self.mGetEbox()
        _jsonMap = {}
        _attributes = []

        _testResult = CHK_RESULT.PASS
        _cmd_str = 'route'

        _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
        if _o:
            _output_lines = _o.readlines()
            _filename = self.mGetResultDir() + "hc_Route_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            self.mWriteResultToFile(_filename,_output_lines)

            _output_lines = self.mRemoveBlankLinesHelper(_output_lines)
            _attributes = _output_lines[1].split()
            _index = 1
            _resMap = {}
            for _iterator in range(2,len(_output_lines)):
                _line = _output_lines[_iterator].split()
                for _i in range(0,len(_attributes)):
                    _resMap[_attributes[_i]] = _line[_i]
                _jsonMap[_index] = _resMap
                _index += 1

       #     _jsonMap = self.mCopyResultHelper(_output_lines)
            self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, route command successful!!" %(_host), _jsonMap)
        else:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, route command failed!!" %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        _jsonMap["hcDescription"] = "result of command: route "
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    def mCheckCellFlashLog(self, aHost):

        _host = aHost
        _node = self.mGetNode(_host)

        _ebox = self.mGetEbox()
        _jsonMap = {}
        _attributes = []

        _testResult = CHK_RESULT.PASS
        _cmd_str = 'cellcli -e list flashlog'

        _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
        if _o:
            _output_lines = _o.readlines()
            _filename = self.mGetResultDir() + "hc_CellFlashLog_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            self.mWriteResultToFile(_filename,_output_lines)

            _output_lines = self.mRemoveBlankLinesHelper(_output_lines)
            _jsonMap["Result"] = _output_lines

            self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, cell list flashlog command successful!!" %(_host), _jsonMap)
        else:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, cell list flashlog command failed!!" %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        _jsonMap["hcDescription"] = "result of command: cellcli -e list flashlog "
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    def mCheckCellFlashCache(self, aHost):

        _host = aHost
        _node = self.mGetNode(_host)

        _ebox = self.mGetEbox()
        _jsonMap = {}
        _attributes = []

        _testResult = CHK_RESULT.PASS
        _cmd_str = 'cellcli -e list flashcache'

        _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
        if _o:
            _output_lines = _o.readlines()
            _filename = self.mGetResultDir() + "hc_CellFlashCache_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            self.mWriteResultToFile(_filename,_output_lines)

            _output_lines = self.mRemoveBlankLinesHelper(_output_lines)
            _jsonMap["Result"] = _output_lines

            self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, cell list flashcache command successful!!" %(_host), _jsonMap)
        else:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, cell list flashcache command failed!!" %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        _jsonMap["hcDescription"] = "result of command: cellcli -e list flashcache "
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    def mCheckCellGridDisk(self, aHost):

        _host = aHost
        _node = self.mGetNode(_host)

        _ebox = self.mGetEbox()
        _jsonMap = {}
        _attributes = []

        _testResult = CHK_RESULT.PASS
        _cmd_str = 'cellcli -e list griddisk'

        _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
        if _o:
            _output_lines = _o.readlines()
            _filename = self.mGetResultDir() + "hc_CellGridDisk_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            self.mWriteResultToFile(_filename,_output_lines)

            _output_lines = self.mRemoveBlankLinesHelper(_output_lines)
            _jsonMap = self.mCopyResultHelper(_output_lines)

            self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, cell list griddisk command successful!!" %(_host), _jsonMap)
        else:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, cell list griddisk command failed!!" %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        _jsonMap["hcDescription"] = "result of command: cellcli -e list griddisk "
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    def mCheckCellPhysicalDisk(self, aHost):

        _host = aHost
        _node = self.mGetNode(_host)

        _ebox = self.mGetEbox()
        _jsonMap = {}
        _attributes = []

        _testResult = CHK_RESULT.PASS
        _cmd_str = 'cellcli -e list physicaldisk'

        _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
        if _o:
            _output_lines = _o.readlines()
            _filename = self.mGetResultDir() + "hc_CellPhysicalDisk_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            self.mWriteResultToFile(_filename,_output_lines)

            _output_lines = self.mRemoveBlankLinesHelper(_output_lines)
            _jsonMap = self.mCopyResultHelper(_output_lines)

            self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, cell list physicaldisk command successful!!" %(_host), _jsonMap)
        else:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, cell list physicaldisk command failed!!" %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        _jsonMap["hcDescription"] = "result of command: cellcli -e list physicaldisk "
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    def mCheckCellAlertHistory(self, aHost):

        _host = aHost
        _node = self.mGetNode(_host)

        _ebox = self.mGetEbox()
        _jsonMap = {}
        _attributes = []

        _testResult = CHK_RESULT.PASS
        _cellcli_alerthistory_options = mGetAlertHistoryOptions(_ebox, _host)
        _cmd_str = f'cellcli {_cellcli_alerthistory_options} -e list alerthistory'

        _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
        if _o:
            _output_lines = _o.readlines()
            _filename = self.mGetResultDir() + "hc_CellAlertHistory_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            self.mWriteResultToFile(_filename,_output_lines)

            _output_lines = self.mRemoveBlankLinesHelper(_output_lines)
            _jsonMap = self.mCopyResultHelper(_output_lines)

            self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, cell list alerthistory command successful!!" %(_host), _jsonMap)
        else:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, cell list alerthistory command failed!!" %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        _jsonMap["hcDescription"] = "result of command: cellcli -e list alerthistory "
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    def mCheckCellDetail(self, aHost):

        _host = aHost
        _node = self.mGetNode(_host)

        _ebox = self.mGetEbox()
        _jsonMap = {}
        _attributes = []

        _testResult = CHK_RESULT.PASS
        _cmd_str = 'cellcli -e list cell detail'

        _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
        if _o:
            _output_lines = _o.readlines()
            _filename = self.mGetResultDir() + "hc_CellDetail_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            self.mWriteResultToFile(_filename,_output_lines)

            _output_lines = self.mRemoveBlankLinesHelper(_output_lines)
            _jsonMap = self.mCopyResultHelper(_output_lines)

            self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, cell list cell detail command successful!!" %(_host), _jsonMap)
        else:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, cell list cell detail command failed!!" %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        _jsonMap["hcDescription"] = "result of command: cellcli -e list cell detail "
        return self.logger.mUpdateResult(_testResult, _jsonMap)


    def mCheckCellDatabase(self, aHost):

        _host = aHost
        _node = self.mGetNode(_host)

        _ebox = self.mGetEbox()
        _jsonMap = {}
        _attributes = []

        _testResult = CHK_RESULT.PASS
        _cmd_str = 'cellcli -e list database'

        _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
        if _o:
            _output_lines = _o.readlines()
            _filename = self.mGetResultDir() + "hc_CellDatabase_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            self.mWriteResultToFile(_filename,_output_lines)

            _output_lines = self.mRemoveBlankLinesHelper(_output_lines)
            _jsonMap = self.mCopyResultHelper(_output_lines)

            self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, cell list database command successful!!" %(_host), _jsonMap)
        else:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, cell list database command failed!!" %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        _jsonMap["hcDescription"] = "result of command: cellcli -e list database "
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    def mCheckListEXAVMIMAGESContents(self, aHost):

        _host = aHost
        _node = self.mGetNode(_host)

        _ebox = self.mGetEbox()
        _jsonMap = {}
        _attributes = []

        _testResult = CHK_RESULT.PASS

        _globalCache = _ebox.mCheckConfigOption("global_cache_dom0_folder")
        _cmd_str = f'/usr/bin/ls -R {_globalCache}'
        _consolidatedOutput = []

        _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
        if _o:
            _output_lines = _o.readlines()
            _consolidatedOutput.append(f"/usr/bin/ls -R {_globalCache}\n")
            _consolidatedOutput.extend(_output_lines)

            _output_lines = self.mRemoveBlankLinesHelper(_output_lines)
            _jsonMap["GlobalCache"] = self.mCopyResultHelper(_output_lines)

            self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, list EXAVMIMAGES Contents successful!!" %(_host), _jsonMap)
        else:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, list EXAVMIMAGES Contents command failed!!" %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        _cmd_str = 'ls -R /EXAVMIMAGES/GuestImgs'

        _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
        if _o:
            _output_lines = _o.readlines()
            _consolidatedOutput.append("ls -R /EXAVMIMAGES/GuestImgs\n")
            _consolidatedOutput.extend(_output_lines)

            _output_lines = self.mRemoveBlankLinesHelper(_output_lines)
            _jsonMap["GuestImgs"] = self.mCopyResultHelper(_output_lines)

            self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, list EXAVMIMAGES Contents successful!!" %(_host), _jsonMap)
        else:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, list EXAVMIMAGES Contents command failed!!" %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        _filename = self.mGetResultDir() + "hc_EXAVMIMAESContents_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
        self.mWriteResultToFile(_filename,_consolidatedOutput)

        self.mDisconnectNode(_node)
        _jsonMap["hcDescription"] = f"result of command: ls -R {_globalCache} and ls -R /EXAVMIMAGES/GuestImgs"
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    def mCheckCellosTgz(self, aHost):

        _host = aHost
        _node = self.mGetNode(_host)

        _ebox = self.mGetEbox()
        _jsonMap = {}
        _attributes = []

        _testResult = CHK_RESULT.PASS
        _cmd_str = "find /var/log/ -iname \"cellos*tgz\" | xargs ls -t | head -1"

        _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
        if _o:
            _output_lines = _o.readlines()
            _output_line = _output_lines[0]
            _startindex = _output_line.find("/var/log")
            _endindex = _output_line.find("tgz")
            _src_filename = _output_line[_startindex:_endindex+3]
            _filename = self.mGetResultDir() + "hc_CellosTgz_%s_%s.tgz"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            _node.mCopy2Local(_src_filename,_filename)

            _output_lines = self.mRemoveBlankLinesHelper(_output_lines)
            _jsonMap = self.mCopyResultHelper(_output_lines)

            self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, cellos tgz read command successful!!" %(_host), _jsonMap)
        else:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, cellos tgz read command failed!!" %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        _jsonMap["hcDescription"] = "result of command: find /var/log/ -iname \"cellos*tgz\" | xargs ls -t | head -1"
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    def mCheckIpconfpl(self, aHost):

        _host = aHost
        _node = self.mGetNode(_host)

        _ebox = self.mGetEbox()
        _jsonMap = {}
        _attributes = []

        _testResult = CHK_RESULT.PASS
        _cmd_str = "/opt/oracle.cellos/ipconf.pl -nocodes -conf /opt/oracle.cellos/cell.conf -check-consistency -semantic -at-runtime; cat /var/log/cellos/ipconf.log"

        _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
        if _o:
            _output_lines = _o.readlines()
            _filename = self.mGetResultDir() + "hc_Ipconfpl_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            self.mWriteResultToFile(_filename,_output_lines)

            _output_lines = self.mRemoveBlankLinesHelper(_output_lines)
            _jsonMap = self.mCopyResultHelper(_output_lines)

            self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, ipconf pl command successful!!" %(_host), _jsonMap)
        else:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, ipconf pl command failed!!" %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        _jsonMap["hcDescription"] = "result of command: /opt/oracle.cellos/ipconf.pl -nocodes -conf /opt/oracle.cellos/cell.conf -check-consistency -semantic -at-runtime; cat /var/log/cellos/ipconf.log"
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    def mCheckIORMPlan(self, aHost):

        _host = aHost
        _node = self.mGetNode(_host)

        _ebox = self.mGetEbox()
        _jsonMap = {}
        _attributes = []

        _testResult = CHK_RESULT.PASS
        _cmd_str = 'cellcli -e list iormplan detail'

        _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
        if _o:
            _output_lines = _o.readlines()
            _filename = self.mGetResultDir() +"hc_IORMPlan_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            self.mWriteResultToFile(_filename,_output_lines)

            _output_lines = self.mRemoveBlankLinesHelper(_output_lines)
            for _line in _output_lines:
                _elem = _line.split(':')
                if len(_elem) > 1:
                    _jsonMap[_elem[0]] = _elem[1].strip()
                else:
                    _jsonMap[_elem[0]] = ""

            self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, cell list iormplan detail command successful!!" %(_host), _jsonMap)
        else:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, cell list iormplan detail command failed!!" %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        _jsonMap["hcDescription"] = "result of command: cellcli -e list iormplan detail "
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    def mCheckSundiagOsw(self, aHost):

        _host = aHost
        _node = self.mGetNode(_host)

        _ebox = self.mGetEbox()
        _jsonMap = {}
        _attributes = []

        _testResult = CHK_RESULT.PASS
        _cmd_str = "/opt/oracle.SupportTools/sundiag.sh osw"

        _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
        if _o:
            _output_lines = _o.readlines()
            _filename = self.mGetResultDir() +"hc_SundiagOsw_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            self.mWriteResultToFile(_filename,_output_lines)

            _output_lines = self.mRemoveBlankLinesHelper(_output_lines)
            _jsonMap = self.mCopyResultHelper(_output_lines)

            self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, sundiag osw command successful!!" %(_host), _jsonMap)
        else:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, sundiag osw command failed!!" %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        _jsonMap["hcDescription"] = "result of command: /opt/oracle.SupportTools/sundiag.sh osw"
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    def mCheckIptables(self, aHost):

        _host = aHost
        _node = self.mGetNode(_host)

        _ebox = self.mGetEbox()
        _jsonMap = {}
        _attributes = []

        _testResult = CHK_RESULT.PASS
        _cmd_str = "iptables -L"

        _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
        if _o:
            _output_lines = _o.readlines()
            _filename = self.mGetResultDir() + "hc_Iptables_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            self.mWriteResultToFile(_filename,_output_lines)

            _output_lines = self.mRemoveBlankLinesHelper(_output_lines)
            _jsonMap = self.mCopyResultHelper(_output_lines)

            self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, iptables -L command successful!!" %(_host), _jsonMap)
        else:
            self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, iptables -L command failed!!" %(_host), _jsonMap)
            _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        _jsonMap["hcDescription"] = "result of command: iptables -L"
        return self.logger.mUpdateResult(_testResult, _jsonMap)


    def mCheckDom0XenLogs(self, aHost):

        try:
            _host = aHost
            _node = self.mGetNode(_host)

            _ebox = self.mGetEbox()
            _jsonMap = {}
            _attributes = []

            _testResult = CHK_RESULT.PASS
            _cmd_str = 'ls /var/log/xen/*.log'

            _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
            if _o:
                _output_lines = _o.readlines()
                _output_lines = self.mRemoveBlankLinesHelper(_output_lines)
                _jsonMap = self.mCopyResultHelper(_output_lines)
                for _output_line in _output_lines:
                    _filename_with_path = _output_line.split("/")
                    _filename = _filename_with_path[-1]
                    _filename = self.mGetResultDir() + "%s_%s_XenLogs_%s"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'), _filename)
                    _node.mCopy2Local(_output_line,_filename)

                self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, XEN Logs command successful!!" %(_host), _jsonMap)
            else:
                self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, XEN Logs command failed!!" %(_host), _jsonMap)
                _testResult = CHK_RESULT.FAIL
        except Exception as e:
                self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, XEN Logs command failed!!" %(_host), _jsonMap)
                _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        _jsonMap["hcDescription"] = "result of command: cat /var/log/xen/*.log "
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    def mCheckVarLogMessages(self, aHost):

        try:
            _host = aHost
            _node = self.mGetNode(_host)

            _ebox = self.mGetEbox()
            _jsonMap = {}
            _attributes = []

            _testResult = CHK_RESULT.PASS
            _cmd_str = 'tail -n 1000 /var/log/messages'

            _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
            if _o:
                _output_lines = _o.readlines()
                _filename = self.mGetResultDir() + "hc_VarLogMessages_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
                self.mWriteResultToFile(_filename, _output_lines)

                _output_lines = self.mRemoveBlankLinesHelper(_output_lines)
                _jsonMap = self.mCopyResultHelper(_output_lines)

                self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, cat /var/log/messages command successful!!" %(_host), _jsonMap)
            else:
                self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, cat /var/log/messages command failed!!" %(_host), _jsonMap)
                _testResult = CHK_RESULT.FAIL
        except Exception as e:
                self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, cat /var/log/messages command failed!!" %(_host), _jsonMap)
                _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        _jsonMap["hcDescription"] = "result of command: cat /var/log/messages "
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    ## Returns CPS  SW Version from active and standby node
    def mCPSVersion(self):
        ebLogInfo("*** Start method mCPSVersion ***")
        _ebox = self.mGetEbox()
        _responseDict = {}
        _remote_cps_host_key = "remote_cps_host"
        _context = get_gcontext()
        _coptions = _context.mGetConfigOptions()

        _cps_sw_version_path = _coptions.get('oci_cps_sw_version_path', None)
        if _cps_sw_version_path is None:
            ebLogInfo("oci_cps_sw_version_path is not available in exabox.cof")
            _cps_sw_version_path = "/opt/oci/exacc/deployer/ocps-full/config/version.json"

        _exacloud_path = _coptions.get('oci_exacloud_path', None)
        if _exacloud_path is None:
            ebLogInfo("oci_exacloud_path is not available in exabox.cof")
            _exacloud_path = "/opt/oci/exacc/exacloud/bin/exacloud"

        _image_info_cmd = _coptions.get('oci_cps_image_info_cmd', None)
        if _image_info_cmd is None:
            ebLogInfo("oci_cps_image_info_cmd is not available in exabox.cof")
            _image_info_cmd = "/usr/local/bin/imageinfo"

        _activeCPS_InfoDict = {}

        #Getting active CPS info
        _ebCore = exaBoxCoreInit(aOptions={})
        _exacloudVersion = "%s (%s)" % _ebCore.mGetVersion()
        _activeCPS_InfoDict["exacloudVersion"] = _exacloudVersion

        #Fetching host name of primary CPS
        _, _, _out, _ = _ebox.mExecuteLocal("/bin/hostname -f")
        _activeCPS_InfoDict["hostname"] = _out.strip()

        #Fetching version and status of image of primary CPS
        _, _, _out, _ = _ebox.mExecuteLocal("sudo "+_image_info_cmd+" -version")
        _activeCPS_InfoDict["image_ver"] = _out.strip()
        _, _, _out, _ = _ebox.mExecuteLocal("sudo "+_image_info_cmd+" -status")
        _activeCPS_InfoDict["image_status"] = _out.strip()

        #Fetching software version of CPS
        _, _, _out, _ = _ebox.mExecuteLocal("/bin/cat "+_cps_sw_version_path)
        try:
            _out = ast.literal_eval(_out.strip())
        except:
            _out = ""
        _activeCPS_InfoDict["cpsSWVersion"] = _out

        _responseDict["active"] = _activeCPS_InfoDict

        #Fetching standby CPS info
        _standbyCPS_InfoDict = {}
        _responseDict["standby"] = _standbyCPS_InfoDict
        try:
            _node = exaBoxNode(_context)
            if _remote_cps_host_key in _context.mGetConfigOptions().keys() and len(_context.mGetConfigOptions()[_remote_cps_host_key])>0:
                _node.mSetUser('ecra')
                _node.mConnect(aHost=_context.mGetConfigOptions()[_remote_cps_host_key])
                _fin, _fout, _ferr = _node.mExecuteCmd("hostname -f")
                _output = _fout.readlines()
                _standbyCPS_InfoDict["hostname"] = _output[0].strip()

                _fin, _fout, _ferr = _node.mExecuteCmd("sudo " +_image_info_cmd+ " -version")
                _output = _fout.readlines()
                _standbyCPS_InfoDict["image_ver"] = _output[0].strip()

                _fin, _fout, _ferr = _node.mExecuteCmd("sudo " + _image_info_cmd + " -status")
                _output = _fout.readlines()
                _standbyCPS_InfoDict["image_status"] = _output[0].strip()

                _fin, _fout, _ferr = _node.mExecuteCmd(_exacloud_path + " -sv")
                _output = _fout.readlines()
                _standbyCPS_InfoDict["exacloudVersion"] = _output[0].strip()

                _fin, _fout, _ferr = _node.mExecuteCmd("cat " + _cps_sw_version_path)
                _output = _fout.readlines()
                try:
                    _standbyCPS_InfoDict["cpsSWVersion"] = ast.literal_eval("".join([x.replace("\n","").strip() for x in _output]))
                except:
                    _standbyCPS_InfoDict["cpsSWVersion"] = ""
                _node.mDisconnect()
                _testResult = CHK_RESULT.PASS
        except:
            _node.mDisconnect()
            _testResult = CHK_RESULT.FAIL

        ebLogInfo("*** mCPSVersion END ***")
        return self.logger.mUpdateResult(_testResult, _responseDict)

    def mCheckAllCellosLogs(self, aHost):

        try:
            _host = aHost
            _node = self.mGetNode(_host)

            _ebox = self.mGetEbox()
            _jsonMap = {}
            _attributes = []

            _testResult = CHK_RESULT.PASS
            _cmd_str = 'tail -n +1 echo `ls /var/log/cellos/*.log` '

            _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
            if _o:
                _output_lines = _o.readlines()

                _filename = self.mGetResultDir() + "hc_AllCellosLogs_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
                self.mWriteResultToFile(_filename, _output_lines)

                _output_lines = self.mRemoveBlankLinesHelper(_output_lines)
                _jsonMap[_host] = _output_lines

                self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, All Cellos Logs  command successful!!" %(_host), _jsonMap)
            else:
                self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, All Cellos Logs command failed!!" %(_host), _jsonMap)
                _testResult = CHK_RESULT.FAIL
        except Exception as e:
                self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, All Cellos Logs command failed!!" %(_host), _jsonMap)
                _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        _jsonMap["hcDescription"] = "result of command: cat /var/log/cellos/*.log "
        return self.logger.mUpdateResult(_testResult, _jsonMap)


    def mCheckIpAddrShow(self, aHost):

        try:
            _host = aHost
            _node = self.mGetNode(_host)

            _ebox = self.mGetEbox()
            _jsonMap = {}
            _attributes = []

            _testResult = CHK_RESULT.PASS
            _cmd_str = "ip addr show"

            _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
            if _o:
                _output_lines = _o.readlines()
                _filename = self.mGetResultDir() + "hc_IpAddrShow_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
                self.mWriteResultToFile(_filename,_output_lines)

                _output_lines = self.mRemoveBlankLinesHelper(_output_lines)
                _jsonMap = self.mCopyResultHelper(_output_lines)

                self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, ip addr show command successful!!" %(_host), _jsonMap)
            else:
                self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, ip addr show command failed!!" %(_host), _jsonMap)
                _testResult = CHK_RESULT.FAIL
        except Exception as e:
                self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, ip addr show command failed!!" %(_host), _jsonMap)
                _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        _jsonMap["hcDescription"] = "result of command: ip addr show"
        return self.logger.mUpdateResult(_testResult, _jsonMap)

    def mCheckIbstat(self, aHost):

        try:
            _host = aHost
            _node = self.mGetNode(_host)

            _ebox = self.mGetEbox()
            _jsonMap = {}
            _attributes = []

            _testResult = CHK_RESULT.PASS
            _cmd_str = "ibstat"

            _i, _o, _e = _node.mExecuteCmd(_cmd_str, aTimeout=180)
            if _o:
                _output_lines = _o.readlines()
                _filename = self.mGetResultDir() + "hc_Ibstat_%s_%s.hcr"%(_host, datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
                self.mWriteResultToFile(_filename,_output_lines)

                _output_lines = self.mRemoveBlankLinesHelper(_output_lines)
                _jsonMap = self.mCopyResultHelper(_output_lines)

                self.logger.mAppendLog(LOG_TYPE.INFO, "On Node %s, ibstat command successful!!" %(_host), _jsonMap)
            else:
                self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, ibstat command failed!!" %(_host), _jsonMap)
                _testResult = CHK_RESULT.FAIL
        except Exception as e:
                self.logger.mAppendLog(LOG_TYPE.ERROR, "On Node %s, ibstat command failed!!" %(_host), _jsonMap)
                _testResult = CHK_RESULT.FAIL

        self.mDisconnectNode(_node)
        _jsonMap["hcDescription"] = "result of command: ibstat"
        return self.logger.mUpdateResult(_testResult, _jsonMap)
