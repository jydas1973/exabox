"""
$Header:

 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    OVM - Basic functionality

FUNCTION:
    Provides network related operations on the cluster Dom0's

NOTE:
    None

History:

    MODIFIED   (MM/DD/YY)
    rkhemcha    11/11/24 - 37243436 - Bring bridge up if not
    rkhemcha    07/26/24 - 36873285 - Optimizations to network validation
    aararora    02/05/23 - Add DR network in type of network.
    rkhemcha    07/21/22 - 34394780 - Read LACP info from XML
    rkhemcha    04/07/22 - 33922918 - Changes to support network
                           reconfiguration
    rkhemcha    03/23/22 - 33963167 - Pick bridges for No VLAN scenario
    rkhemcha    02/17/22 - 33820696 - Refactor Network Validation
    rkhemcha    08/09/21 - 33186306/33154526 - LACP support for nw vldn
    rkhemcha    11/10/20 - 32082144 - Reading arping timeout from
                           heathcheck.conf instead of exabox.conf
    mpedapro    09/02/20 - bug::31743321 create and delete bonding in nw
                           validation to resolve arp cache issue
    rkhemcha    09/21/20 - 31791734 - Enhancing logging for network
                           validation
    mpedapro    08/09/20 - bug::31731157 reading arping_timeout param from
                           exabox conf
    mpedapro    08/05/20 - bug 31222840::Adding arping timeout as configurable
                           param
    mpedapro    07/28/20 - Enh::31596666 same vlan support for network
                           validation
    mpedapro    11/22/19 - Enh 30577975 :: Considering no vlan case for
                           oci-exacc network validation
    ndesanto    10/02/19 - Enh 30374491: EXACC PYTHON 3 MIGRATION BATCH 02
    mpedapro    09/29/19 - bug 30345680: doing arping as part of the configure
                           interface
    shavenug    08/06/19 - Fix Build failure
    shavenug    07/31/19 - 30117384 OCI-EXACC : BRING UP NETWORK INTERFACES IF
                           DOWN DURING NETWORK SANITY CHECK
    mpedapro    06/10/19 - Adding/Removing ip table rule for the interface in
                           network validation of oci-exacc : 29880422
    mpedapro    05/29/19 - Functionality to add/delete route entries ::
                           29606740
    mpedapro    05/13/19 - File Creation

"""

import traceback
from time import sleep
from exabox.healthcheck.hcconstants import LOG_TYPE
from exabox.ovm.hypervisorutils import getTargetHVIType, HVIT_XEN, HVIT_KVM

CLIENT = "client"
BACKUP = "backup"
DR = "dr"


# class added for Network operations
class ebCluNetwork(object):

    def __init__(self, host, interfaceInfo, eBox, nodeObj, aCluHealthObj, loggerObj):
        self.logger = loggerObj
        self.logger.mAppendLog(LOG_TYPE.VERBOSE, "Initializing cluNetwork object for host - {}".format(host))

        self.dom0 = host
        self.node = nodeObj
        self.hc = aCluHealthObj
        self.cls = self.__class__.__name__
        # vlan values to consider as no vlan scenario.
        self.noVlanList = ['UNDEFINED', '', '1']

        self.useBridge = {CLIENT: False, BACKUP: False, DR: False}
        self.ifActiveClusters = False
        self.interfaceMap = {}
        if interfaceInfo:
            if host in self.hc.mGetDom0s():
                # identifying if there are any active clusters in the dom0
                self.ifActiveClusters = self.activeClustersCheck()
                self.interfaceMap = self.mSetInterfaceMap(interfaceInfo)

        # setting default arping timeout of 40, before trying to read from config
        self.arping_timeout = 40
        try:
            arpTimeout = self.hc.mGetHcConfig()["network_validation"]["arping_timeout"].strip()
            # checking timeout value is digit and positive
            if arpTimeout.isdigit() and int(arpTimeout) > 0:
                self.arping_timeout = arpTimeout
        except Exception as excp:
            self.logger.mAppendLog(LOG_TYPE.WARNING,
                                   "Could not read arping timeout from healthcheck.conf file, exception - {}. Setting it to default {}.".format(
                                       str(excp), self.arping_timeout))
            self.logger.mAppendLog(LOG_TYPE.VERBOSE, traceback.format_exc())

    def __del__(self):
        pass

    def setNodeObj(self, nodeObj):
        self.node = nodeObj

    # Function to configure the given interface in the given host
    def mConfigureInterface(self, eth, netobj):
        fnSign = "{}/{}".format(self.cls, self.mConfigureInterface.__name__)

        netType = netobj.mGetNetType()
        if netType == "other":
            netType = "dr"
        intfName = self.interfaceMap[netType][eth]
        cmd = "/bin/cat /sys/class/net/{}/operstate".format(intfName)
        _, _o, _e, _rc = self.mLogCmd(cmd, "debug", fnSign)

        if _rc == -1:
            return False
        if _rc != 0:
            # Add the VLAN interface if it does not exist.
            vlanId = netobj.mGetNetVlanId()
            # add link only if vlan id is specified and if this is not lacp or shared VLAN scenario
            if vlanId.strip() not in self.noVlanList and intfName.find("vmbondeth") == -1:
                cmd = "/sbin/ip link add link {} name {} type vlan id {}".format(eth, intfName, vlanId)
                _, _o, _e, _rc = self.mLogCmd(cmd, "debug", fnSign)
                if _rc != 0:
                    self.logger.mAppendLog(LOG_TYPE.ERROR,
                                           "Failed to configure the interface {} on the host {}".format(intfName,
                                                                                                        self.dom0))
                    return False

        # Bring the interface up
        ipaddr = netobj.mGetNetIpAddr()
        netmask = netobj.mGetNetMask()

        cmd = "/sbin/ifconfig {} {} netmask {} up".format(intfName, ipaddr, netmask)
        _, _o, _e, _rc = self.mLogCmd(cmd, "debug", fnSign)
        # Validate whether the interface is up now
        cmd = "/bin/cat /sys/class/net/{}/operstate".format(intfName)
        _, _out, _e, _rc = self.mLogCmd(cmd, "debug", fnSign)

        if _rc != 0 or "down" in _out[0]:
            self.logger.mAppendLog(LOG_TYPE.ERROR,
                                   "Failed to bring up the interface {} on host {}".format(eth, self.dom0))
            return False
        # add IP table rule for the new interface
        _ipRule = self.mAddIptableRule(intfName)
        if _ipRule is False:
            return False

        # ARP answer mode, update neighbours' ARP caches
        cmd = "/sbin/arping -I {} -c 2 -A {}".format(intfName, ipaddr)
        _, _o, _e, _rc = self.mLogCmd(cmd, "debug", fnSign)

        return True

    def mBringUpInterface(self, eth):
        fnSign = "{}/{}".format(self.cls, self.mBringUpInterface.__name__)

        cmd = "/sbin/ip link set {} up".format(eth)
        _, _o, _e, _rc = self.mLogCmd(cmd, "debug", fnSign)
        if _rc == 0:
            return True

        self.logger.mAppendLog(LOG_TYPE.WARNING, "Failed to bring up {}".format(eth))
        return False

    # Function to un-configure the given interface in the given host
    def mUnConfigureInterface(self, eth, netobj):
        fnSign = "{}/{}".format(self.cls, self.mUnConfigureInterface.__name__)

        netType = netobj.mGetNetType()
        if netType == "other":
            netType = "dr"
        intfName = self.interfaceMap[netType][eth]
        cmd = "/bin/cat /sys/class/net/{}/operstate".format(intfName)
        _, _o, _e, _rc = self.mLogCmd(cmd, "debug", fnSign)
        if _rc == -1:
            return False
        if _rc == 0:
            self.mDeleteIptableRule(intfName)
            vlanId = netobj.mGetNetVlanId()
            # delete link only if vlan id is specified and if this is not lacp or not shared VLAN scenario
            if vlanId.strip() not in self.noVlanList and intfName.find("vmbondeth") == -1:
                cmd = "/sbin/ip link del {}".format(intfName)
            else:
                ipaddr = netobj.mGetNetIpAddr()
                netmask = netobj.mGetNetMask()
                cmd = "/sbin/ip addr del {}/{} dev {}".format(ipaddr, netmask, intfName)

            _, _o, _e, _rc = self.mLogCmd(cmd, "debug", fnSign)
            if _rc != 0:
                self.logger.mAppendLog(LOG_TYPE.ERROR,
                                       "Failed to un-configure interface {} on host {}".format(intfName, self.dom0))
                return False

        return True

    # Function to add routing table entry for the given interface in the given host
    def mAddRouteEntry(self, intfName, ip, gateway):
        fnSign = "{}/{}".format(self.cls, self.mAddRouteEntry.__name__)

        cmd = "/sbin/ip route add {}/32 via {} dev {}".format(ip, gateway, intfName)
        _, _o, _e, _rc = self.mLogCmd(cmd, "debug", fnSign)
        if _rc == 0:
            return True

        self.mDeleteRouteEntry(intfName, ip, gateway)
        return False

    # Function to remove routing table entry for the given interface in the given host
    def mDeleteRouteEntry(self, intfName, ip, gateway):
        fnSign = "{}/{}".format(self.cls, self.mDeleteRouteEntry.__name__)

        cmd = "/sbin/ip route del {}/32 via {} dev {}".format(ip, gateway, intfName)
        _, _o, _e, _rc = self.mLogCmd(cmd, "debug", fnSign)
        if _rc == 0:
            return True

        return False

    # Function to add ip table rule for the given interface in the given host
    def mAddIptableRule(self, intfName):
        fnSign = "{}/{}".format(self.cls, self.mAddIptableRule.__name__)

        cmd = "/sbin/iptables -nvL | grep {}".format(intfName)
        _, _out, _e, _rc = self.mLogCmd(cmd, "debug", fnSign)
        for _line in _out:
            if intfName in _line:
                return True

        cmd = "/sbin/iptables -I INPUT -i {} -j ACCEPT".format(intfName)
        _, _o, _e, _rc = self.mLogCmd(cmd, "debug", fnSign)
        if _rc == 0:
            return True

        self.logger.mAppendLog(LOG_TYPE.ERROR, "Failed to add the iptable rule for {}.".format(intfName))
        self.mDeleteIptableRule(intfName)
        return False

    # Function to remove IP table rule for the given interface in the given host
    def mDeleteIptableRule(self, intfName):
        fnSign = "{}/{}".format(self.cls, self.mDeleteIptableRule.__name__)

        cmd = "/sbin/iptables -D INPUT -i {} -j ACCEPT".format(intfName)
        _, _o, _e, _rc = self.mLogCmd(cmd, "debug", fnSign)
        if _rc == 0:
            return True

        self.logger.mAppendLog(LOG_TYPE.ERROR, "Failed to delete the iptable rule on {}.".format(intfName))
        return False

    # Function to check and create vm bridges in dom0.
    # Returns True only when it successfully creates a bridge.
    def mCreateVmBridge(self, slaves, bridgeName, lacpFlag=False, vlan=None):
        fnSign = "{}/{}".format(self.cls, self.mCreateVmBridge.__name__)

        retValue = True
        # check whether it is kvm host (or) xen host.
        # For lacp enabled systems, create vlan bridges, and use the same path
        # as for active-backup bonding's samevlan scenario
        hypervisorType = getTargetHVIType(self.dom0)
        if hypervisorType == HVIT_XEN:
            if lacpFlag:
                if vlan:
                    cmd = "/opt/exadata_ovm/exadata.img.domu_maker add-bonded-bridge-dom0 {} {} {} {} lacp".format(
                        bridgeName, slaves[0], slaves[1], vlan)
                else:
                    cmd = "/opt/exadata_ovm/exadata.img.domu_maker add-bonded-bridge-dom0 {} {} {} lacp".format(
                        bridgeName, slaves[0], slaves[1])
            else:
                cmd = "/opt/exadata_ovm/exadata.img.domu_maker add-bonded-bridge-dom0 {} {} {}".format(bridgeName,
                                                                                                       slaves[0],
                                                                                                       slaves[1])
        elif hypervisorType == HVIT_KVM:
            if lacpFlag:
                if vlan:
                    cmd = "/usr/sbin/vm_maker --add-bonded-bridge {} --first-slave {} --second-slave {} --vlan {} --bond-mode lacp".format(
                        bridgeName, slaves[0], slaves[1], vlan)
                else:
                    cmd = "/usr/sbin/vm_maker --add-bonded-bridge {} --first-slave {} --second-slave {} --bond-mode lacp".format(
                        bridgeName, slaves[0], slaves[1])
            else:
                cmd = "/usr/sbin/vm_maker --add-bonded-bridge {} --first-slave {} --second-slave {}".format(bridgeName,
                                                                                                            slaves[0],
                                                                                                            slaves[1])
        else:
            self.logger.mAppendLog(LOG_TYPE.WARNING,
                                   "Invalid host type {} for creating vmBridge in host {}".format(hypervisorType,
                                                                                                  self.dom0))
            return False

        # execute command to create to vm bridge.
        _, _o, _e, _rc = self.mLogCmd(cmd, "info", fnSign)
        if _rc != 0:
            retValue = False

        if retValue is False:
            for retryCnt in range(0, 3):
                retStatus = self.mDeleteVmBridge(bridgeName, slaves)
                if retStatus:
                    break

        return retValue

    # Function to check and delete vm bridges in dom0.
    def mDeleteVmBridge(self, bridgeName, slaves, lacpFlag=False, vlan=None):
        fnSign = "{}/{}".format(self.cls, self.mDeleteVmBridge.__name__)

        retValue = True
        # check whether it is kvm host (or) xen host.
        hypervisorType = getTargetHVIType(self.dom0)
        if hypervisorType == HVIT_XEN:
            if lacpFlag and vlan:
                cmd = "/opt/exadata_ovm/exadata.img.domu_maker remove-bridge-dom0 {} {} -force".format(bridgeName, vlan)
            else:
                cmd = "/opt/exadata_ovm/exadata.img.domu_maker remove-bridge-dom0 {} -force".format(bridgeName)
        elif hypervisorType == HVIT_KVM:
            if lacpFlag and vlan:
                cmd = "/usr/sbin/vm_maker --remove-bridge {} --vlan {} --force".format(bridgeName, vlan)
            else:
                cmd = "/usr/sbin/vm_maker --remove-bridge {} --force".format(bridgeName)
        else:
            self.logger.mAppendLog(LOG_TYPE.WARNING,
                                   "Invalid host type {} for removing vmbridge in host {}".format(hypervisorType,
                                                                                                  self.dom0))
            return False

        # execute command to delete the vm bridge.
        _, _o, _e, _rc = self.mLogCmd(cmd, "info", fnSign)
        if _rc != 0:
            retValue = False

        # try bringing up the slaves
        for slave in slaves:
            # retry max 3 times if bringup fails.
            for retryCnt in range(0, 3):
                retStatus = self.mBringUpInterface(slave)
                if retStatus:
                    break

        return retValue

    # check if there are active clusters.
    def activeClustersCheck(self):
        fnSign = "{}/{}".format(self.cls, self.activeClustersCheck.__name__)

        self.logger.mAppendLog(LOG_TYPE.VERBOSE, "Identifying presence of active clusters on host {}".format(self.dom0))
        cmd = "/usr/sbin/brctl show | grep 'vnet\|vif'"
        _, _o, _e, _rc = self.mLogCmd(cmd, "debug", fnSign)
        if _rc == 0:
            return True

        return False

    def mSetInterfaceMap(self, interface_info):
        interfaceMap = {}

        for intftype, intfDict in interface_info.items():
            interfaceMap[intftype] = {}
            netObj = intfDict["netobj"]
            vlan = netObj.mGetNetVlanId()
            bridgeName = self.ifUseBridge(intfDict["bridge"], vlan, netObj.mGetNetLacp())

            for intf in intfDict["interfaces"]:
                if bridgeName:
                    self.useBridge[intftype] = True
                    name = bridgeName
                else:
                    name = "{}.{}".format(intf, vlan)

                interfaceMap[intftype][intf] = name

        return interfaceMap

    # Function to check if we need to perform test over vmbridge or not, per network type (client/backup)
    def ifUseBridge(self, bridgeName, vlan, lacp):
        fnSign = "{}/{}".format(self.cls, self.ifUseBridge.__name__)

        # If no-vlan scenario, perform test over bonded bridges
        if vlan.strip() in self.noVlanList:
            return bridgeName
        else:
            bridgeName = bridgeName + "." + vlan

        # return vmBridge in case of lacp
        if lacp:
            return bridgeName

        cmd = '/bin/cat /sys/class/net/{}/operstate'.format(bridgeName)
        _, _out, _e, _rc = self.mLogCmd(cmd, "debug", fnSign)

        # <vmBridge>.<vlan> does not exist
        if _rc != 0:
            self.logger.mAppendLog(LOG_TYPE.VERBOSE, "Bridge {} not found on host {}".format(bridgeName, self.dom0))
        else:
            # <vmBridge>.<vlan> exists and is up
            if "up" in _out[0]:
                self.logger.mAppendLog(LOG_TYPE.VERBOSE, "Bridge {} is up on host {}".format(bridgeName, self.dom0))
                # return bonded interface only when at-least one cluster is present.
                if self.ifActiveClusters:
                    return bridgeName
            # <vmBridge>.<vlan> exists but is not UP
            else:
                self.logger.mAppendLog(LOG_TYPE.VERBOSE, "Bridge {} is not up on host {}, "
                                                         "trying to bring up.".format(bridgeName, self.dom0))
                _, _out, _e, _rc = self.mLogCmd(f"ifup {bridgeName}", "debug", fnSign)
                sleep(5)
                _, _out, _e, _rc = self.mLogCmd(cmd, "debug", fnSign)
                if _rc == 0 and "up" in _out[0]:
                    self.logger.mAppendLog(LOG_TYPE.VERBOSE,
                                           "Bridge {} is up on host {}".format(bridgeName, self.dom0))
                    return bridgeName
                else:
                    self.logger.mAppendLog(LOG_TYPE.VERBOSE, "Unable to bring bridge {} up on host {}. "
                                                         "Defaulting to physical interfaces".format(bridgeName, self.dom0))
        return None

    # Function to log the command and status in the logger
    def mLogCmd(self, cmd, mode="info", testName=None):
        """
        Wrapper function around mExecuteCmd() of exacloud
        :return: input, output, error from a command run, each as an individual list,
                 with each line output as a string in the list, along-with the return code
        """
        _i, _outstring, _errstring = None, None, None
        _rc = -1

        try:
            _i, _o, _e = self.node.mExecuteCmd(cmd, aTimeout=180)
            _rc = self.node.mGetCmdExitStatus()
            _outstring, _errstring = [], []

            _output = _o.readlines()
            if _output:
                for o in _output:
                    _outstring.append(o.strip())
            _error = _e.readlines()
            if _error:
                for e in _error:
                    _errstring.append(e.strip())

            if mode == "debug":
                log_lvl = LOG_TYPE.DEBUG
            else:
                log_lvl = LOG_TYPE.INFO

            self.logger.mAppendLog(log_lvl, "[RC:{}], CMD: << {} >>, Host: {}".format(_rc, cmd, self.dom0))

            if _rc != 0 or mode == "debug":
                if _rc == 1 and testName == "Network Ping":
                    pass
                else:
                    for oline in _outstring:
                        self.logger.mAppendLog(log_lvl, oline)
                    for eline in _errstring:
                        self.logger.mAppendLog(log_lvl, eline)

        except Exception as e:
            self.logger.mAppendLog(LOG_TYPE.ERROR,
                                   "Exception {} occurred for cmd << {} >> from the function {}."
                                   .format(str(e), cmd, testName))
            self.logger.mAppendLog(LOG_TYPE.VERBOSE, traceback.format_exc())

        return _i, _outstring, _errstring, _rc


class HostNotConnectable(Exception):
    """Exception raised for non-connectable nodes

        Attributes:
            host -- hostname to which connection fails
    """

    def __init__(self, aHost):
        self.host = aHost
        self.message = f"Unable to connect to host {self.host}."
        super().__init__(self.message)
