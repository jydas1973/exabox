#!/usr/bin/env python
#
# Copyright (c) 2014, 2025, Oracle and/or its affiliates.
#
#    NAME
#     DNSConfig.py
#
#    DESCRIPTION
#     Populate DNS entries
#
#    NOTES
#     Write DNS entries in /etc/hosts.exacc*
#     Configure dnsmasq
#     Reload dnsmasq service
#
#    MODIFIED   (MM/DD/YY)
#    oespinos    07/14/25 - 38189701 - Symlinks not getting updated on encrypted fs
#    oespinos    06/10/25 - 33416778 - Add all clusters nats during cps deploy
#    oespinos    05/15/25 - 37953247 - Preserve symlinks in /etc/hosts.* files
#    oespinos    05/13/25 - Bug 37945144 - Activation failing due to missing
#                           nat hostnames for clu1.
#    oespinos    04/28/25 - Bug 37884454 - Add nat entries during 'guest'
#                           provisioning.
#    hgaldame    04/03/25 - 37787016 - ociexacc: cps sw upgrade fails on
#                           healthcheckmetric configuration
#    oespinos    02/20/25 - 35844182 Add vm entries only for provisioned clusters
#    oespinos    02/20/25 - 37609732 - /etc/hosts.* and /etc/dnsmasq.d/* files
#                           creation is already handled by dnsserver deployer
#    hgaldame    02/15/25 - 37593351 - oci/exacc: cps sw upgrade fails in step
#                           configure heathchk metric
#    ririgoye    08/30/23 - Fix redundant/multiple/deprecated instances of
#                           mConnect
#    akkar       05/26/23 - Bug 35388002: Log the DNS entries
#    hgaldame    03/01/23 - 35134139 - exacc:22.3.1.0.0:bb:x10m:cps sw upgrade
#                           fails at rack_setup:healthcheckmetrics step with
#                           typeerror at mgetallcomputesfromclustersdir
#    oespinos    11/29/22 - 34704795 - MISSING ENTRIES ON SECONDARY CPS HOSTS
#    hgaldame    11/08/22 - 34778659 - ociexacc: exacloud cli command for
#                           health metrics network configuration on cps host
#    oespinos    08/09/22 - 34466345 - Sync to stdby cps failing due to hostkey
#                           verification
#    oespinos    03/23/22 - 33993110 - DNSconfig gives error when scan ip is
#                           none
#    dekuckre    11/19/21 - 33416778 - Add mRemoveHostEntries
#    oespinos    03/04/21 - 32551029 - Fix rsync command wildcard
#    oespinos    02/08/21 - 32472400 - DOMUIB FILE NOT GETTING UPDATED ON 2ND
#                           CPS
#    shavenug    12/28/20 - XbranchMerge shavenug_bug-32149541 from
#                           st_ecs_19.4.3.0.0
#    diyanez     08/11/20 - 31861044 - OCIEXACC: ADBD: EXACLOUD NEEDS TO CREATE SECSCAN USER WITH UID < 3000
#    oespinos    05/25/20 - 31362744 - GENERATE DOMU DNS NAT ENTRIES WITH
#                           <DOMU>-NAT AS HOSTNAME
#    shavenug    11/12/20 - 32149541 OCI-EXACC: PROVISIONING FAILS DNS REVERSE
#                           LOOKUP FAILURE
#    oespinos    05/21/20 - 31388372 - UPDATE CPS DNS ENTRIES FOR KVM IN
#                           OCIEXACC
#    naps        09/28/19 - security vulnerability fixes.
#    oespinos    09/12/19 - 30299328 - FIXES FOR /ETC/HOSTS.EXACC* FILES
#    oespinos    07/23/19 - 30085999 - ociexacc refresh dns after createservice
#    oespinos    10/04/19 - Creation
#

from exabox.tools.AttributeWrapper import wrapStrBytesFunctions
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug
from exabox.ovm.vmconfig import exaBoxClusterConfig
from exabox.ovm.cluconfig import ebCluNetworksConfig, ebCluClustersConfig, ebCluClusterScansConfig, ebCluMachinesConfig
from exabox.core.Context import get_gcontext
from exabox.ovm.clumisc import validateIpOrHostname
from exabox.ovm.atp import ebCluATPConfig
from exabox.core.Node import exaBoxNode
from exabox.utils.node import node_connect_to_host
from subprocess import Popen, PIPE
from glob import glob
from time import sleep
import json
import os
import re
import shlex
import traceback


class ebDNSConfig(object):

    def __init__(self, aOptions, aConfigpath=None):

        self.__options = aOptions
        self.__configoptions = get_gcontext().mGetConfigOptions()
        self.__configpath = aConfigpath if aConfigpath is not None else aOptions.configpath
        self.__network_config = None
        self.__cluster_config = None
        self.__cluster_scans = None
        self.__machines_config = None
        self.__config = None
        if self.__configpath is not None:
            self.__config = exaBoxClusterConfig(None, self.__configpath)
            self.__network_config = ebCluNetworksConfig(self.__config)
            self.__cluster_config = ebCluClustersConfig(self.__config, self.__options)
            self.__cluster_scans = ebCluClusterScansConfig(self.__config)
            self.__machines_config = ebCluMachinesConfig(self.__config)
        self.__remote_cps = self.__configoptions.get("remote_cps_host", "")
        self.__is_atp = ebCluATPConfig(aOptions).isATP()
        self.__target = None

    def mGetNetworkIDs(self):
        return self.__network_config.mGetNetworkIdList()

    def mGetNetwork(self, aId):
        return self.__network_config.mGetNetworkConfig(aId)

    def mGetMachineIDs(self):
        return self.__cluster_config.mGetClusterMachines()

    def mGetMachine(self, aId):
        return self.__machines_config.mGetMachineConfig(aId)

    def mGetClusterIDs(self):
        return self.__cluster_config.mGetClusters()

    def mGetCluster(self, aId):
        return self.__cluster_config.mGetCluster(aId)

    def mGetClusterScanIDs(self):
        return self.__cluster_scans.mGetScans()

    def mGetClusterScan(self, aId):
        return self.__cluster_scans.mGetScan(aId)

    def mShortname(self, aHostname):
        return aHostname.split('.')[0]

    def mFullname(self, aHostname, aDomain):
        return '.'.join([aHostname, aDomain])

    def mFqdn(self, aNetwork):
        return self.mFullname(aNetwork.mGetNetHostName(), aNetwork.mGetNetDomainName())

    def mNatFqdn(self, aNetwork):
        return self.mFullname(aNetwork.mGetNetNatHostName(), aNetwork.mGetNetNatDomainName())

    def mDomuNatFqdn(self, aNetwork):
        return self.mFullname(aNetwork.mGetNetHostName() + "-nat", aNetwork.mGetNetNatDomainName())

    def mVipFqdn(self, aNetwork):
        return self.mFullname(aNetwork.mGetCVIPName(), aNetwork.mGetCVIPDomainName())

    def mNatFqdnJson(self, aNetworkJson): # from jsonconf (*control_plane_server_network_conf.json)
        return self.mFullname(aNetworkJson['nat_hostname'], self.mGetNatVipDomain())

    def mNatVipFqdn(self, aNetworkJson): # from jsonconf (*control_plane_server_network_conf.json)
        return self.mFullname(aNetworkJson['nat_vip_hostname'], self.mGetNatVipDomain())

    def mHasNatVips(self):
        return self.__options.jsonconf and 'nat_vips' in self.__options.jsonconf.keys()

    def mGetNatVipDomain(self):
        return self.__options.jsonconf['nat_vips']['domain']

    def mGetNatVipHosts(self):
        return self.__options.jsonconf['nat_vips']['hosts']

    def mIsAdminNetwork(self, aNetwork):
        return aNetwork.mGetNetType() == "admin"

    def mIsIlomNetwork(self, aNetwork):
        return aNetwork.mGetNetType() == "Ilom"

    def mIsClientNetwork(self, aNetwork):
        return aNetwork.mGetNetType() == "client"

    def mIsBackupNetwork(self, aNetwork):
        return aNetwork.mGetNetType() == "backup"

    def mIsPrivateNetwork(self, aNetwork):
        return aNetwork.mGetNetType() == "private"

    def mIsStorageNetwork(self, aNetwork):
        return aNetwork.mGetPkeyName().startswith("stib") or aNetwork.mGetInterfaceName().startswith("stre")

    def mHasNatAddress(self, aNetwork):
        return aNetwork.mGetNetNatAddr(aFallBack=False) is not None

    def mConfigureDNS(self, aType='all'):
        if not self.__configpath:
            ebLogError("mConfigureDNS: No config xml provided")
            return

        try:
            self.__target = aType
            self.mAddDNSEntries()
            self.mUpdateRemoteNode()
            self.mRestartDnsmasq(self.__remote_cps)
        except Exception as exception:
            ebLogWarn("** Failed to configure dnsmasq **")
            ebLogDebug(str(exception))
            raise

    def mRemoveDNSEntries(self, aType='guest'):
        if not self.__configpath:
            ebLogError("mRemoveDNSEntries: No config xml provided")
            return

        try:
            self.__target = aType
            self.mDeleteDNSEntries()
            self.mUpdateRemoteNode()
            self.mRestartDnsmasq(self.__remote_cps)
        except Exception as exception:
            ebLogWarn("** Failed to remove entries from dnsmasq **")
            ebLogDebug(str(exception))
            raise

    def mAddDNSEntries(self):
        ebLogInfo("** Writing /etc/hosts.exacc* files **")

        # Admin networks
        self.mAddAdminNetworks()
        # Cluster machines networks (Guest networks)
        self.mAddGuestNetworks()
        # Cluster VIP networks
        self.mAddVipNetworks()
        # Cluster SCANs
        self.mAddScanNetworks()
        # NATS & NAT-VIPS
        self.mAddNatVipNetworks()

    def mAddAdminNetworks(self):
        # Admin networks
        for network_id in self.mGetNetworkIDs():
            network = self.mGetNetwork(network_id)

            if self.mIsAdminNetwork(network) or self.mIsIlomNetwork(network):
                if self.__target in ["admin", "all"]:
                    self.mAddInfraEntry(self.mFqdn(network), network.mGetNetIpAddr())

    def mAddGuestNetworks(self):
        # Cluster machines networks (Guest networks)
        for machine_id in self.mGetMachineIDs():
            machine_config = self.mGetMachine(machine_id)

            for network_id in machine_config.mGetMacNetworks():
                self.mAddMachineNetwork(self.mGetNetwork(network_id))

    def mAddMachineNetwork(self, aNetwork):
        # Priv networks
        if self.mIsPrivateNetwork(aNetwork) and self.mIsStorageNetwork(aNetwork):
            if self.__target in ["guest", "all"]:
                self.mAddIBEntry(self.mFqdn(aNetwork), aNetwork.mGetNetIpAddr())

        # Guest networks
        elif self.mIsClientNetwork(aNetwork) or self.mIsBackupNetwork(aNetwork):
            if self.__target in ["guest", "all"]:
                self.mAddServiceEntry(self.mFqdn(aNetwork), aNetwork.mGetNetIpAddr())

        # NAT info (for client network only)
        if self.mIsClientNetwork(aNetwork) and self.mHasNatAddress(aNetwork):
            self.mAddNatNetwork(aNetwork)

    def mAddNatNetwork(self, aNetwork):
        # NAT info (for client network only)
        if self.__target in ["admin", "guest", "all"]:
            self.mAddInfraEntry(self.mNatFqdn(aNetwork), aNetwork.mGetNetNatAddr())

        if self.__is_atp:
            if self.__target in ["guest", "all"]:
                self.mAddADBDEntry(self.mDomuNatFqdn(aNetwork), aNetwork.mGetNetNatAddr())

    def mAddVipNetworks(self):
        # Cluster VIP networks
        for cluster_id in self.mGetClusterIDs():
            cluster = self.mGetCluster(cluster_id)

            for clu_vip in cluster.mGetCluVips().values():
                if self.__target in ["guest", "all"]:
                    self.mAddServiceEntry(self.mVipFqdn(clu_vip), clu_vip.mGetCVIPAddr())

    def mRemoveVipNetwork(self, aMachine):
        for cluster_id in self.mGetClusterIDs():
            cluster = self.mGetCluster(cluster_id)

            for clu_vip in cluster.mGetCluVips().values():
                if aMachine.mGetMacId() in clu_vip.mGetCVIPMachines():
                    self.mDeleteServiceEntry(clu_vip.mGetCVIPAddr())

    def mAddScanNetworks(self):
        # Cluster SCANs
        for scan_id in self.mGetClusterScanIDs():
            scan_network = self.mGetClusterScan(scan_id)

            scan_name = scan_network.mGetScanName()
            scan_ip_list = scan_network.mGetScanIps()

            if scan_ip_list is None or all(ip is None for ip in scan_ip_list):
                ebLogWarn("** Scan IP is None for hostname {0}**".format(scan_name))
                continue

            if self.__target in ["guest", "all"]:
                self.mAddServiceEntries(scan_name, scan_ip_list)

    def mAddNatVipNetworks(self):
        # NATS & NAT-VIPS from *control_plane_server_network_conf.json
        if self.mHasNatVips():
            for nat_vip_host in self.mGetNatVipHosts():
                self.mAddInfraEntry(self.mNatFqdnJson(nat_vip_host), nat_vip_host['nat_ip'])
                self.mAddInfraEntry(self.mNatVipFqdn(nat_vip_host), nat_vip_host['nat_vip_ip'])

    def mAddInfraEntry(self, aHostname, aAddress):
        self.mAddDNSEntry(aHostname, aAddress, "/etc/hosts.exacc_infra")

    def mAddServiceEntry(self, aHostname, aAddress):
        return self.mAddDNSEntry(aHostname, aAddress, "/etc/hosts.exacc_domu")

    def mAddADBDEntry(self, aHostname, aAddress):
        self.mAddDNSEntry(aHostname, aAddress, "/etc/hosts.adbd_domu")

    # For 1 hostname with many ip addresses (SCAN network)
    def mAddServiceEntries(self, aHostname, aAddressList):
        self.mAddDNSEntryList(aHostname, aAddressList, "/etc/hosts.exacc_domu")

    def mAddIBEntry(self, aHostname, aAddress):
        self.mAddDNSEntry(aHostname, aAddress, "/etc/hosts.exacc_domuib")

    def mAddDNSEntry(self, aHostname, aAddress, aHostFile):
        """ Add a dns entry to the given file, reusing the method for multiple ip address """
        return self.mAddDNSEntryList(aHostname, [aAddress], aHostFile)

    def mAddDNSEntryList(self, aHostname, aAddressList, aHostFile):
        """ Add dns entries for one hostname with many ip addresses """
        # Make sure the file exists
        if not os.path.exists(aHostFile):
            raise FileNotFoundError("Expected file not found {0}".format(aHostFile))

        # Delete any stale entry (cleanup)
        _result = self.mExecute(self.mBuildDeleteCmd(aHostname, aHostFile))

        # Add the new entries
        for aAddress in aAddressList:
            dns_entry = self.mBuildDNSEntry(aAddress, aHostname)
            ebLogInfo(f"Adding entry: '{dns_entry}' in file:  {aHostFile}")

            _result = self.mExecute(self.mBuildAppendCmd(dns_entry, aHostFile))

        return _result

    def mBuildDNSEntry(self, aAddress, aHostname):
        return "{0}\t{1}\t{2}".format(aAddress.ljust(15), aHostname.ljust(50), self.mShortname(aHostname))

    def mBuildAppendCmd(self, aDNSEntry, aFilename):
        return ["/usr/bin/sudo", "/usr/bin/sed", "-i", "--follow-symlinks", "$a " + aDNSEntry, aFilename]

    def mBuildDeleteCmd(self, aHostname, aFilename):
        return ["/usr/bin/sudo", "/usr/bin/sed", "-i", "--follow-symlinks", "/" + aHostname + "/d", aFilename]


    def mRemoveHostEntries(self, aHostname):
        machine = self.mGetMachine(aHostname)
        for network_id in machine.mGetMacNetworks():
            network = self.mGetNetwork(network_id)

            if self.mIsPrivateNetwork(network):
                self.mDeleteIBEntry(network.mGetNetIpAddr())

            elif self.mIsBackupNetwork(network) or self.mIsClientNetwork(network):
                self.mDeleteServiceEntry(network.mGetNetIpAddr())

            if self.mIsClientNetwork(network) and self.mHasNatAddress(network):
                if self.__is_atp:
                    self.mDeleteADBDEntry(network.mGetNetNatAddr())

        self.mRemoveVipNetwork(machine)


    def mDeleteDNSEntries(self):
        ebLogInfo("** Deleting entries from /etc/hosts.adbd_domu file **")

        for network_id in self.mGetNetworkIDs():
            network = self.mGetNetwork(network_id)

            #At the moment, we only want to delete the <customer_domu>-nat entries from
            #/etc/hosts.adbd_domu and nothing else
            if self.mIsClientNetwork(network) and self.mHasNatAddress(network):
                self.mDeleteADBDEntry(network.mGetNetNatAddr())

    def mDeleteInfraEntry(self, aAddress):
        self.mDeleteDNSEntry(aAddress, "/etc/hosts.exacc_infra")

    def mDeleteServiceEntry(self, aAddress):
        self.mDeleteDNSEntry(aAddress, "/etc/hosts.exacc_domu")

    def mDeleteIBEntry(self, aAddress):
        self.mDeleteDNSEntry(aAddress, "/etc/hosts.exacc_domuib")

    def mDeleteADBDEntry(self, aAddress):
        self.mDeleteDNSEntry(aAddress, "/etc/hosts.adbd_domu")

    def mDeleteDNSEntry(self, aHostname, aHostFile):
        if os.path.exists(aHostFile):
            return self.mExecute(self.mBuildDeleteCmd(aHostname, aHostFile))


    def mUpdateRemoteNode(self):
        """ In case of two CPS nodes, sync the /etc/hosts.exacc entries """
        if not self.__remote_cps:
            return

        if not validateIpOrHostname(self.__remote_cps):
            ebLogError('** Error: __remote_cps is not in correct format ! **')
            return

        ebLogInfo(f"** Syncing /etc/hosts.exacc* to the remote node {self.__remote_cps} **")
        self.mExecute(self.mRsyncCmd(self.mGetFileList()))

    def mGetFileList(self):
        file_list = glob("/etc/hosts.exacc*")
        file_list.append("/etc/hosts.adbd_domu")
        return [os.readlink(path) if os.path.islink(path) else path for path in file_list]

    def mGetDestDir(self, aFileList):
        return os.path.dirname(aFileList[0])

    def mBaseRsyncCmd(self):
        return ["/usr/bin/sudo", "/usr/bin/rsync", "-e", "ssh -o StrictHostKeyChecking=no", "-av"]

    def mRsyncCmd(self, aFileList):
        return self.mBaseRsyncCmd() + aFileList + [self.mRemotePath(aFileList)]

    def mRemotePath(self, aFileList):
        return self.__remote_cps + ":" + self.mGetDestDir(aFileList)


    @staticmethod
    def mRestartDnsmasq(remote_cps=None):
        """ Call the command to restart the dnsmasq service """

        restart_cmd = ebDNSConfig.mBuildReloadCmd()
        ebLogInfo("** Restarting dnsmasq using command: {0} **".format(" ".join(restart_cmd)))
        rcode, out, err = ebDNSConfig.mExecute(restart_cmd)

        if rcode:
            ebLogWarn("** Failed to restart dnsmasq on localhost, please restart manually **")
            ebLogDebug(err)

        if remote_cps:
            # Give time for dns on node1 to be up before restarting on node2
            sleep(10)
            ebLogInfo("** Restart dnsmasq on the remote node {0} **".format(remote_cps))
            restart_cmd = ebDNSConfig.mBuildReloadCmd(remote_cps)
            ebDNSConfig.mExecute(restart_cmd)

    @staticmethod
    def mBuildReloadCmd(aRemoteCps=None):
        cmd = ["/usr/bin/sudo", "/usr/bin/systemctl", "reload", "dnsmasq"]

        if aRemoteCps:
            cmd = ["/bin/ssh", aRemoteCps] + cmd

        return cmd

    @staticmethod
    def mExecute(aCmd):
        """ Execute a command in the shell """
        process = Popen(aCmd, shell=False, stdout=PIPE, stderr=PIPE)
        std_out, std_err = wrapStrBytesFunctions(process).communicate()
        ret_code = process.returncode

        if ret_code:
            ebLogDebug("Error running command: {0}".format(" ".join(aCmd)))
            if len(std_out) or len(std_err):
                msg = "Out: {0}".format(std_out)
                msg += "\nError: {0}".format(std_err)
                ebLogDebug(msg)

        return ret_code, std_out, std_err

    def mConfigureHealthCheckMetrics(self, aType, aCriticalError=True, aInstall_dir=None, aProcessAllConfFiles=False):
        _failure = 1
        _success = 0
        _local_install_dir = aInstall_dir or "/opt/oci/exacc"
        try:
            _ip_compute_list = self.mGetIpListFromComputes()
            if not _ip_compute_list:
                ebLogWarn("mConfigureHealthCheckMetrics: No computes ip founded. Skip confguration")
                return _success
            _fwd_proxy_arg = ",".join(_ip_compute_list)
            _ocps_json_path = self.__configoptions.get("ocps_jsonpath", None)
            if not _ocps_json_path:
                ebLogWarn("mConfigureHealthCheckMetrics: ocps_json_path not configured")
                return _failure
            _local_install_dir = aInstall_dir or "/opt/oci/exacc"
            _fwd_proxy_dpy = os.path.join(_local_install_dir, "forwardproxy", "ship", "deploy_forwardproxy.py")
            _fwd_proxy_cmd = "/usr/bin/sudo -n {0} --action updateconfig -c {1} --allowhosts {2} --service domuHealthMetrics".format(
                _fwd_proxy_dpy, _ocps_json_path, _fwd_proxy_arg)
            _remote_host = self.__remote_cps.strip() if self.__remote_cps else None
            if aType == "remotehost" and not _remote_host:
                ebLogWarn("mConfigureHealthCheckMetrics: No remote host configure for type {0}".format(aType))
                return _failure
            _host_list = []
            if aType in ["localhost"]:
                _host_list.append("localhost")
            elif aType in ["remotehost"]:
                _host_list.append(_remote_host)
            elif aType in ["all"]:
                _host_list.append("localhost")
                if _remote_host:
                    _host_list.append(_remote_host)
            for _host in _host_list:
                _is_localhost = True if _host == 'localhost' else False
                _exanode = exaBoxNode(get_gcontext(), aLocal=_is_localhost)
                with node_connect_to_host(_exanode, _host) as _node:
                    ebLogInfo(
                        'mConfigureHealthCheckMetrics: Configure health check metrics on host: {0} '.format(_host))
                    ebLogInfo('mConfigureHealthCheckMetrics: Command : {0} '.format(_fwd_proxy_cmd))
                    _, _o, _e = _node.mExecuteCmd(_fwd_proxy_cmd)
                    _out = _o.readlines()
                    _err = _e.readlines()
                    _rc = _node.mGetCmdExitStatus()
                    if _rc != _success:
                        ebLogError(
                            'mConfigureHealthCheckMetrics: Failed execution on host: {0}, command: {1} '.format(_host,
                                                                                                                _fwd_proxy_cmd))
                        ebLogError("\n out: {0} \n err:{1}".format(_out, _err))
                        if aCriticalError:
                            return _rc
                    else:
                        ebLogInfo(
                            'mConfigureHealthCheckMetrics: process completed on host {0} , {1} : {2}'.format(_host,
                                                                                                             _out,
                                                                                                             _err))
        except:
            if aCriticalError:
                raise
            ebLogWarn("mConfigureHealthCheckMetrics: Exception captured: {0}".format(traceback.format_exc()))
        return _success

    def mGetIpListFromComputes(self):
        """
        Get ip list from computes. 
        Returns:
           list<str>: list of Dom0's ip
        """
        return self.mGetAllComputesFromDnsFile()

    def mGetAllComputesFromDnsFile(self):
        exacc_infra = "/etc/hosts.exacc_infra"
        ebLogInfo(f'mConfigureHealthCheckMetrics: Reading file : {exacc_infra}')
        _ip_compute_list = []
        try:
            cmd = f'/usr/bin/sudo -n /bin/cat {exacc_infra}'
            ret_code, std_out, std_err = self.mExecute(shlex.split(cmd))
            if ret_code != 0:
                ebLogWarn(
                    f'mConfigureHealthCheckMetrics: Can not read {exacc_infra}. Skip. std_out: {std_out} , std_err: {std_err} ')
                return _ip_compute_list
        except Exception:
            ebLogWarn(f'mConfigureHealthCheckMetrics: Failed to read file: {exacc_infra} : {traceback.format_exc()}')
            return _ip_compute_list
        domain_name = self.mGetDomainName()
        file_content = std_out.split("\n")
        if not file_content or len(file_content) <= 0:
            ebLogWarn(f'mConfigureHealthCheckMetrics: Empty file : {exacc_infra}. Skip')
            return _ip_compute_list
        dict_content = {}
        qa_regex = r'sca.*[0-9]{1,2}adm[0-9]{1,2}.' + domain_name + '$'
        prod_regex = r'.*exdd[0-9]{1,3}.' + domain_name + '$'
        for _line in file_content:
            _strip_line = _line.lstrip()
            if not _strip_line.startswith("#"):  #skip commented lines
                current_token_list = _line.split()
                if len(current_token_list) == 3:
                    ip_host, fqdn_host, short_name = current_token_list
                    if re.search(qa_regex, fqdn_host):
                        if dict_content.get(short_name, None) is None:
                            dict_content[short_name] = ip_host
                    elif re.search(prod_regex, fqdn_host):
                        if dict_content.get(short_name, None) is None:
                            dict_content[short_name] = ip_host
        if dict_content:
            ebLogInfo('mConfigureHealthCheckMetrics: Dom0 list found: {0}'.format(dict_content.keys()))
            _ip_compute_list = list(dict_content.values())
        return _ip_compute_list

    def mGetDomainName(self):
        result_domain = ""
        default_domain = "us.oracle.com"
        try:
            ocps_jsonpath = self.__configoptions.get("ocps_jsonpath", None)
            if ocps_jsonpath:
                with open(ocps_jsonpath, "r") as _json_file:
                    _token_json = json.load(_json_file)
                    result_domain = _token_json.get("adminDomain", default_domain).strip()
        except:
            ebLogWarn("get_domain_name: Exception captured reading ocps_jsonpath: {0}".format(traceback.format_exc()))
            result_domain = default_domain
        return result_domain
