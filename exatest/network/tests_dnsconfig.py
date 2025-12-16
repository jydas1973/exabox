#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/network/tests_dnsconfig.py /main/6 2025/09/30 18:16:00 oespinos Exp $
#
# tests_dnsconfig.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_dnsconfig.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    hgaldame    02/15/25 - 37593351 - oci/exacc: cps sw upgrade fails in step
#                           configure heathchk metric
#    hgaldame    03/01/23 - 35134139 - exacc:22.3.1.0.0:bb:x10m:cps sw upgrade
#                           fails at rack_setup:healthcheckmetrics step with
#                           typeerror at mgetallcomputesfromclustersdir
#    hgaldame    11/08/22 - 34778659 - ociexacc: exacloud cli command for
#                           health metrics network configuration on cps host
#    hgaldame    11/08/22 - 34778659 - ociexacc: exacloud cli command for health
#                           metrics network configuration on cps host 
#    hgaldame    11/08/22 - Creation
# 

import os
import io
import json
import six
import paramiko
import socket
import unittest
import warnings
import copy
import uuid
import shutil
import re
import builtins
from unittest.mock import patch, Mock, call, ANY, mock_open
from exabox.log.LogMgr import ebLogInfo
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.MockCommand import exaMockCommand
from exabox.core.Error import ExacloudRuntimeError
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.network.dns import DNSConfig


class ebTestebDNSConfig(ebTestClucontrol):
    BASE_PKG = "exabox.network.dns.DNSConfig"

    DUMMY_ENTRY = "10.31.112.4    \tscaqab10adm01.us.oracle.com                       \tscaqab10adm01"
    APPEND_CMD = ["/usr/bin/sudo", "/usr/bin/sed", "-i", "--follow-symlinks", f"$a {DUMMY_ENTRY}", "/etc/hosts.exacc_infra"]
    DELETE_CMD = ["/usr/bin/sudo", "/usr/bin/sed", "-i", "--follow-symlinks", "/scaqab10adm01.us.oracle.com/d", "/etc/hosts.exacc_infra"]


    @classmethod
    def setUpClass(self):
        super(ebTestebDNSConfig, self).setUpClass(aUseOeda = False, aGenerateDatabase = False)
        warnings.filterwarnings("ignore")

    def setUp(self):
        self.__instance = DNSConfig.ebDNSConfig(self.mGetClubox().mGetArgsOptions())


    def __build_expected_fwd_proxy_call(self, aIpList):
        _expected_cmd = ["/usr/bin/sudo -n"]
        _expected_cmd.append("/opt/oci/exacc/forwardproxy/ship/deploy_forwardproxy.py")
        _expected_cmd.append("--action updateconfig")
        _expected_cmd.append("-c {0}".format("/opt/oci/config_bundle/ocpsSetup.json")) 
        _expected_cmd.append("--allowhosts {0} --service domuHealthMetrics".format((",".join(aIpList))))
        return " ".join(_expected_cmd)
    
    def __build_mock_exabox_node(self, aReturnCode=0):
        _node_mock = Mock(**{
            "mConnect.return_value": None,
            "mGetCmdExitStatus.return_value": aReturnCode,
            "mDisconnect.return_value": None,
            "mExecuteCmd.return_value":(None, io.StringIO("sysout"), io.StringIO("syserr"))
        })
        return _node_mock

    def test_000_get_domain_name_no_admin_domain(self):
        """
            Scenario: Return default domain name if no 'adminDomain' key on ocpsSetup.json 
            Given ocpsSetup.json file
            When get the domain name is no on json file
            Then result should the default domain name
        """
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.ocps_jsonpath = "/opt/oci/config_bundle/ocpsSetup.json"
        _instance = DNSConfig.ebDNSConfig(_options, _options.get("configpath"))
        with patch.object(_instance,"_ebDNSConfig__configoptions", _options),\
            patch('builtins.open', mock_open(read_data='{}')):
            result = _instance.mGetDomainName()
            self.assertEqual(result, "us.oracle.com")


    def test_001_get_domain_name_exception(self):
        """
            Scenario: Return default domain name on exception  
            Given ocpsSetup.json file
            When there is and exception reading json file
            Then result should the default domain name
        """
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.ocps_jsonpath = "/opt/oci/config_bundle/ocpsSetup.json"
        _instance = DNSConfig.ebDNSConfig(_options, _options.get("configpath"))
        with patch.object(_instance,"_ebDNSConfig__configoptions", _options),\
            patch('builtins.open', mock_open(read_data='{not valid json')):
            result = _instance.mGetDomainName()
            self.assertEqual(result, "us.oracle.com")
    
    def test_002_get_domain_name(self):
        """
            Scenario: Return the domain name from ocpsSetup.json 
            Given ocpsSetup.json file
            When 'adminDomain' key on  json file
            Then result should be value from json file
        """
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.ocps_jsonpath = "/opt/oci/config_bundle/ocpsSetup.json"
        _instance = DNSConfig.ebDNSConfig(_options, _options.get("configpath"))
        with patch.object(_instance,"_ebDNSConfig__configoptions", _options),\
            patch('builtins.open', mock_open(read_data=json.dumps({'adminDomain':'oraclecloud.internal'}))):
            result = _instance.mGetDomainName()
            self.assertEqual(result, "oraclecloud.internal")

    def test_003_get_computes_read_file_non_zero(self):
        """
            Scenario: Return code non-zero trying to read dns file
            Given dns configuration file
            When return code of reading file is non-zero
            Then result should be empty list
        """
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.ocps_jsonpath = "/opt/oci/config_bundle/ocpsSetup.json"
        _instance = DNSConfig.ebDNSConfig(_options, None)
        with patch(f'{ebTestebDNSConfig.BASE_PKG}.ebDNSConfig.mExecute', return_value=(1,"mockout","mockerr")) as _spy_node:
            _result_ip_address = _instance.mGetAllComputesFromDnsFile()
            self.assertFalse(_result_ip_address, msg="For non-zero error code reading file, list should be empty")
            _spy_node.assert_called_once_with(["/usr/bin/sudo","-n", "/bin/cat", "/etc/hosts.exacc_infra"])

    def test_004_get_computes_exception(self):
        """
            Scenario: Return code non-zero trying to read dns file
            Given dns configuration file
            When there is an exception executing a command
            Then result should be empty list
        """
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.ocps_jsonpath = "/opt/oci/config_bundle/ocpsSetup.json"
        _instance = DNSConfig.ebDNSConfig(_options, None)
        with patch(f'{ebTestebDNSConfig.BASE_PKG}.ebDNSConfig.mExecute', side_effect=IOError("error reading file")) as _spy_node:
            _result_ip_address = _instance.mGetAllComputesFromDnsFile()
            self.assertFalse(_result_ip_address, msg="When there is an exception executing cmd, list should be empty")
            _spy_node.assert_called_once_with(["/usr/bin/sudo","-n", "/bin/cat", "/etc/hosts.exacc_infra"])

    def test_005_get_computes_non_computes_dev(self):
        """
            Scenario: Read read dns file with no dom0's on dev enviroment
            Given dns configuration file
            and a domain name
            When there no dom0's on the list
            Then result should be empty list
        """
        mock_sysout="""
#Created by CPS Deployer
10.31.31.46     scaqak01adm01-c.us.oracle.com                           scaqak01adm01-c
# 10.31.31.27     scaqak01adm02.us.oracle.com                             scaqak01adm02
10.31.31.47     scaqak01adm02-c.us.oracle.com                           scaqak01adm02-c
10.31.31.34     scaqak01celadm01.us.oracle.com                          scaqak01celadm01
10.31.31.54     scaqak01celadm01-c.us.oracle.com                        scaqak01celadm01-c
10.31.31.35     scaqak01celadm02.us.oracle.com                          scaqak01celadm02
10.31.31.55     scaqak01celadm02-c.us.oracle.com                        scaqak01celadm02-c
# 10.31.31.27     scaqak01adm01.us.oracle.com                             scaqak01adm02
"""
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.ocps_jsonpath = "/opt/oci/config_bundle/ocpsSetup.json"
        _instance = DNSConfig.ebDNSConfig(_options, None)
        with patch(f'{ebTestebDNSConfig.BASE_PKG}.ebDNSConfig.mGetDomainName', return_value="us.oracle.com"),\
            patch(f'{ebTestebDNSConfig.BASE_PKG}.ebDNSConfig.mExecute', return_value=(0,mock_sysout,"")) as _spy_node:
            _result_ip_address = _instance.mGetAllComputesFromDnsFile()
            self.assertFalse(_result_ip_address, msg="When there no dom0 on dns file, list should be empty")
            _spy_node.assert_called_once_with(["/usr/bin/sudo","-n", "/bin/cat", "/etc/hosts.exacc_infra"])

    def test_006_get_computes_non_computes_prod(self):
        """
            Scenario: Read read dns file with no dom0's on prod enviroment
            Given dns configuration file
            and a domain name
            When there no dom0's on the list
            Then result should be empty list
        """
        mock_sysout="""
# Manual entry for elastic resources
#Created by CPS Deployer
100.104.0.15    iad116433exdcl01.oraclecloud.internal                   iad116433exdcl01
100.104.0.16    iad116433exdcl02.oraclecloud.internal                   iad116433exdcl02
100.104.0.17    iad116433exdcl03.oraclecloud.internal                   iad116433exdcl03
100.104.0.76    iad116433exdcl04.oraclecloud.internal                   iad116433exdcl04
100.104.0.78    iad116433exdcl05.oraclecloud.internal                   iad116433exdcl05
100.104.0.80    iad116433exdcl06.oraclecloud.internal                   iad116433exdcl06
100.104.0.18    iad116433exdd001lo.oraclecloud.internal                 iad116433exdd001lo
100.104.0.19    iad116433exdd002lo.oraclecloud.internal                 iad116433exdd002lo
100.104.0.20    iad116433exdcl01lo.oraclecloud.internal                 iad116433exdcl01lo
    #100.104.0.13    iad116433exdd001.oraclecloud.internal                   iad116433exdd001

100.104.0.21    iad116433exdcl02lo.oraclecloud.internal                 iad116433exdcl02l
#100.104.0.14    iad116433exdd002.oraclecloud.internal                   iad116433exdd002

"""
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.ocps_jsonpath = "/opt/oci/config_bundle/ocpsSetup.json"
        _instance = DNSConfig.ebDNSConfig(_options, None)
        with patch(f'{ebTestebDNSConfig.BASE_PKG}.ebDNSConfig.mGetDomainName', return_value="oraclecloud.internal"),\
            patch(f'{ebTestebDNSConfig.BASE_PKG}.ebDNSConfig.mExecute', return_value=(0,mock_sysout,"")) as _spy_node:
            _result_ip_address = _instance.mGetAllComputesFromDnsFile()
            self.assertFalse(_result_ip_address, msg="When there no dom0 on dns file, list should be empty")
            _spy_node.assert_called_once_with(["/usr/bin/sudo","-n", "/bin/cat", "/etc/hosts.exacc_infra"])

    def test_007_get_computes_computes_dev(self):
        """
            Scenario: Read read dns file with no dom0's on dev enviroment
            Given dns configuration file
            and a domain name
            When there dom0's on the list
            Then result should a list with dom0 IP's
        """
        mock_sysout="""
#Created by CPS Deployer
10.31.31.46     scaqak01adm01-c.us.oracle.com                           scaqak01adm01-c
10.31.31.27     scaqak01adm02.us.oracle.com                             scaqak01adm02
10.31.31.47     scaqak01adm02-c.us.oracle.com                           scaqak01adm02-c
10.31.31.34     scaqak01celadm01.us.oracle.com                          scaqak01celadm01
10.31.31.54     scaqak01celadm01-c.us.oracle.com                        scaqak01celadm01-c
10.31.31.35     scaqak01celadm02.us.oracle.com                          scaqak01celadm02
10.31.31.55     scaqak01celadm02-c.us.oracle.com                        scaqak01celadm02-c
10.31.31.28     scaqak01adm01.us.oracle.com                             scaqak01adm01
# 10.31.31.51     scaqak01adm01.us.oracle.com                             scaqak01adm02

"""
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.ocps_jsonpath = "/opt/oci/config_bundle/ocpsSetup.json"
        _instance = DNSConfig.ebDNSConfig(_options, None)
        with patch(f'{ebTestebDNSConfig.BASE_PKG}.ebDNSConfig.mGetDomainName', return_value="us.oracle.com"),\
            patch(f'{ebTestebDNSConfig.BASE_PKG}.ebDNSConfig.mExecute', return_value=(0,mock_sysout,"")) as _spy_node:
            _result_ip_address = _instance.mGetAllComputesFromDnsFile()
            self.assertTrue(_result_ip_address, msg="When there dom0 on dns file, result list should not be empty")
            self.assertEqual(len(_result_ip_address),2, msg="Exact two ip's are expected on result list")
            for _ip in ["10.31.31.27","10.31.31.28"]:
                self.assertIn(_ip, _result_ip_address, msg=f'Ip {_ip} should be contained on result list' )
            self.assertNotIn("10.31.31.51", _result_ip_address, msg=f'Commented Ip {_ip} should not be contained on result list' )
            _spy_node.assert_called_once_with(["/usr/bin/sudo","-n", "/bin/cat", "/etc/hosts.exacc_infra"])

    def test_008_get_computes_computes_prod(self):
        """
            Scenario: Read read dns file with no dom0's on prod enviroment
            Given dns configuration file
            and a domain name
            When there dom0's on the list
            Then result should a list with dom0 IP's
        """
        mock_sysout="""
#Created by CPS Deployer
100.104.0.13   	iad116433exdd001.oraclecloud.internal             	iad116433exdd001
100.104.0.15   	iad116433exdcl01.oraclecloud.internal             	iad116433exdcl01
100.104.0.16   	iad116433exdcl02.oraclecloud.internal             	iad116433exdcl02
100.104.0.17   	iad116433exdcl03.oraclecloud.internal             	iad116433exdcl03
100.104.0.76   	iad116433exdcl04.oraclecloud.internal             	iad116433exdcl04
100.104.0.78   	iad116433exdcl05.oraclecloud.internal             	iad116433exdcl05
100.104.0.14   	iad116433exdd002.oraclecloud.internal             	iad116433exdd002
100.104.0.80   	iad116433exdcl06.oraclecloud.internal             	iad116433exdcl06
#Created by CPS Deployer
100.104.0.18   	iad116433exdd001lo.oraclecloud.internal           	iad116433exdd001lo
100.104.0.19   	iad116433exdd002lo.oraclecloud.internal           	iad116433exdd002lo
100.104.0.20   	iad116433exdcl01lo.oraclecloud.internal           	iad116433exdcl01lo
100.104.0.21   	iad116433exdcl02lo.oraclecloud.internal           	iad116433exdcl02lo
100.104.0.22   	iad116433exdcl03lo.oraclecloud.internal           	iad116433exdcl03lo
#    100.104.0.10   	iad116433exdd001.oraclecloud.internal             	iad116433exdd001
100.104.0.23   	iad116433exdd003.oraclecloud.internal             	iad116433exdd003

"""
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.ocps_jsonpath = "/opt/oci/config_bundle/ocpsSetup.json"
        _instance = DNSConfig.ebDNSConfig(_options, None)
        with patch(f'{ebTestebDNSConfig.BASE_PKG}.ebDNSConfig.mGetDomainName', return_value="oraclecloud.internal"),\
            patch(f'{ebTestebDNSConfig.BASE_PKG}.ebDNSConfig.mExecute', return_value=(0,mock_sysout,"")) as _spy_node:
            _result_ip_address = _instance.mGetAllComputesFromDnsFile()
            self.assertTrue(_result_ip_address, msg="When there dom0 on dns file, result list should not be empty")
            self.assertEqual(len(_result_ip_address),3, msg="Exact two ip's are expected on result list")
            for _ip in ["100.104.0.13","100.104.0.14","100.104.0.23"]:
                self.assertIn(_ip, _result_ip_address, msg=f'Ip {_ip} should be contained on result list' )
            self.assertNotIn("100.104.0.10", _result_ip_address, msg=f'Commented Ip {_ip} should not be contained on result list' )
            _spy_node.assert_called_once_with(["/usr/bin/sudo","-n", "/bin/cat", "/etc/hosts.exacc_infra"])


            


    def test_009_get_computes_non_dom0(self):
        """
            Scenario: Filter non-dom0's hosts
            Given an empty list of dom's ip
            When the ip's from dom0's are required
            Then result should be empty list
        """
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.ocps_jsonpath = "/opt/oci/config_bundle/ocpsSetup.json"
        _instance = DNSConfig.ebDNSConfig(_options, None)
        with patch(f'{ebTestebDNSConfig.BASE_PKG}.ebDNSConfig.mGetIpListFromComputes', return_value=[]) as _spy_node:
            _result_ip_address = _instance.mGetIpListFromComputes()
            self.assertFalse(_result_ip_address, msg="For Non-dom0's configuration, list should be empty")

    def test_010_configure_health_check_metrics_no_ocps_setup(self):
        """
            Scenario: Execute healthmetrics configuration with no ocpsSetup.json configuration
            Given list of dom's ip
            And invalid ocpsSetup.json 
            When healtmetrics configuration is required
            Then return code should not be succeed
        """
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.ocps_jsonpath = ""
        with patch(f'{ebTestebDNSConfig.BASE_PKG}.ebDNSConfig.mGetIpListFromComputes', return_value=["10.20.30.40","10.20.30.41"]) as _spy_node:
            _instance = DNSConfig.ebDNSConfig(_options, _options.get("configpath"))
            _return_code = _instance.mConfigureHealthCheckMetrics("all")
            self.assertNotEquals(_return_code, 0) 

    def test_011_configure_health_check_metrics_remote_cps_single_host(self):
        """
            Scenario: Execute healthmetrics configuration with type "remotehost" 
                      on a single host environment
            Given list of dom's ip
            And type is equals to "remotehost"
            And "remote_cps_host"  is not configured
            When healtmetrics configuration is required
            Then return code should not be succeed
        """
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.ocps_jsonpath = "/opt/oci/config_bundle/ocpsSetup.json"
        _instance = DNSConfig.ebDNSConfig(_options, _options.get("configpath"))
        _ip_dom0_list = ["10.20.30.40","10.20.30.41"]
        with patch.object(_instance,"_ebDNSConfig__configoptions", _options),\
            patch(f'{ebTestebDNSConfig.BASE_PKG}.ebDNSConfig.mGetIpListFromComputes', return_value=_ip_dom0_list):
            _return_code = _instance.mConfigureHealthCheckMetrics("remotehost")
            self.assertNotEquals(_return_code, 0) 

    def test_012_configure_health_check_metrics_all_two_hosts(self):
        """
            Scenario: Execute healthmetrics configuration on two hosts 
            Given list of dom's ip
            And type is equals to "all"
            And two hosts exists for run healthmetrics configuration
            When healtmetrics configuration is required
            Then forwardproxy deployer should be invoked with ip's from dom0's
            on both hosts
        """
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.ocps_jsonpath = "/opt/oci/config_bundle/ocpsSetup.json"
        _instance = DNSConfig.ebDNSConfig(_options, _options.get("configpath"))
        _ip_dom0_list = ["10.20.30.40","10.20.30.41"]
        _expected_cmd = self.__build_expected_fwd_proxy_call(_ip_dom0_list)
        _exabox_node_mock = self.__build_mock_exabox_node()
        with patch.object(_instance,"_ebDNSConfig__configoptions", _options),\
            patch.object(_instance,"_ebDNSConfig__remote_cps", "remotehostname"),\
            patch(f'{ebTestebDNSConfig.BASE_PKG}.ebDNSConfig.mGetIpListFromComputes', return_value=_ip_dom0_list),\
            patch(f'{ebTestebDNSConfig.BASE_PKG}.exaBoxNode', return_value=_exabox_node_mock) as _spy_node:
            _return_code = _instance.mConfigureHealthCheckMetrics("all")
            self.assertEquals(_return_code, 0) 
            _calls_init = [call(ANY, aLocal=True), call(ANY, aLocal=False)]
            _spy_node.assert_has_calls(_calls_init)
            _calls_cmd = [call(_expected_cmd), call(_expected_cmd)]
            _spy_node.return_value.mExecuteCmd.assert_has_calls(_calls_cmd)


    def test_013_configure_health_check_metrics_all_single_host(self):
        """
            Scenario: Execute healthmetrics configuration on single 
            host with type "all"
            Given list of dom's ip
            And type is equals to "all"
            And single host exists for run healthmetrics configuration
            When healtmetrics configuration is required
            Then forwardproxy deployer should be invoked with ip's from dom0's
            only in one host
        """
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.ocps_jsonpath = "/opt/oci/config_bundle/ocpsSetup.json"
        _instance = DNSConfig.ebDNSConfig(_options, _options.get("configpath"))
        _ip_dom0_list = ["10.20.30.50"]
        _expected_cmd = self.__build_expected_fwd_proxy_call(_ip_dom0_list)
        _exabox_node_mock = self.__build_mock_exabox_node()
        with patch.object(_instance,"_ebDNSConfig__configoptions", _options),\
            patch.object(_instance,"_ebDNSConfig__remote_cps", ""),\
            patch(f'{ebTestebDNSConfig.BASE_PKG}.ebDNSConfig.mGetIpListFromComputes', return_value=_ip_dom0_list),\
            patch(f'{ebTestebDNSConfig.BASE_PKG}.exaBoxNode', return_value=_exabox_node_mock) as _spy_node:
            _return_code = _instance.mConfigureHealthCheckMetrics("all")
            self.assertEquals(_return_code, 0)
            _spy_node.assert_called_once_with(ANY, aLocal=True)
            _spy_node.return_value.mExecuteCmd.assert_called_once_with(_expected_cmd)

    def test_014_configure_health_check_metrics_localhost(self):
        """
            Scenario: Execute healthmetrics configuration on single 
            host with type "localhost"
            Given list of dom's ip
            And type is equals to "localhost"
            And single host exists for run healthmetrics configuration
            When healtmetrics configuration is required
            Then forwardproxy deployer should be invoked with ip's from dom0's
            only localhost
        """
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.ocps_jsonpath = "/opt/oci/config_bundle/ocpsSetup.json"
        _instance = DNSConfig.ebDNSConfig(_options, _options.get("configpath"))
        _ip_dom0_list = ["10.20.30.50"]
        _expected_cmd = self.__build_expected_fwd_proxy_call(_ip_dom0_list)
        _exabox_node_mock = self.__build_mock_exabox_node()
        with patch.object(_instance,"_ebDNSConfig__configoptions", _options),\
            patch.object(_instance,"_ebDNSConfig__remote_cps", ""),\
            patch(f'{ebTestebDNSConfig.BASE_PKG}.ebDNSConfig.mGetIpListFromComputes', return_value=_ip_dom0_list),\
            patch(f'{ebTestebDNSConfig.BASE_PKG}.exaBoxNode', return_value=_exabox_node_mock) as _spy_node:
                _return_code = _instance.mConfigureHealthCheckMetrics("localhost")
                self.assertEquals(_return_code, 0)
                _spy_node.assert_called_once_with(ANY, aLocal=True)
                _spy_node.return_value.mExecuteCmd.assert_called_once_with(_expected_cmd)

    def test_015_configure_health_check_metrics_remotehost(self):
        """
            Scenario: Execute healthmetrics configuration on single 
            host with type "remotehost"
            Given list of dom's ip
            And type is equals to "remotehost"
            And single host exists for run healthmetrics configuration
            When healtmetrics configuration is required
            Then forwardproxy deployer should be invoked with ip's from dom0's
            only on remotehost
        """
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.ocps_jsonpath = "/opt/oci/config_bundle/ocpsSetup.json"
        _options.remote_cps_host = "remotehostname"
        _instance = DNSConfig.ebDNSConfig(_options, _options.get("configpath"))
        _ip_dom0_list = ["10.20.30.50"]
        _expected_cmd = self.__build_expected_fwd_proxy_call(_ip_dom0_list)
        _exabox_node_mock = self.__build_mock_exabox_node()
        with patch.object(_instance,"_ebDNSConfig__configoptions", _options),\
            patch.object(_instance,"_ebDNSConfig__remote_cps", "remotehostname"),\
            patch(f'{ebTestebDNSConfig.BASE_PKG}.ebDNSConfig.mGetIpListFromComputes', return_value=_ip_dom0_list),\
            patch(f'{ebTestebDNSConfig.BASE_PKG}.exaBoxNode', return_value=_exabox_node_mock) as _spy_node:
                _return_code = _instance.mConfigureHealthCheckMetrics("remotehost")
                self.assertEquals(_return_code, 0)
                _spy_node.assert_called_once_with(ANY, aLocal=False)
                _spy_node.return_value.mExecuteCmd.assert_called_once_with(_expected_cmd)

    def test_016_fwd_proxy_fails_health_metrics_config(self):
        """
            Scenario: Forward proxy component fails on  healthmetrics configuration 
            Given list of dom's ip
            And type is equals to "localhost"
            And single host exists for run healthmetrics configuration
            When healtmetrics configuration is required
            and forward proxy returns 1
            Then return code should not be succeed
        """
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.ocps_jsonpath = "/opt/oci/config_bundle/ocpsSetup.json"
        _instance = DNSConfig.ebDNSConfig(_options, _options.get("configpath"))
        _ip_dom0_list = ["10.20.30.50"]
        _expected_cmd = self.__build_expected_fwd_proxy_call(_ip_dom0_list)
        _exabox_node_mock = self.__build_mock_exabox_node(aReturnCode=1)
        with patch.object(_instance,"_ebDNSConfig__configoptions", _options),\
            patch.object(_instance,"_ebDNSConfig__remote_cps", ""),\
            patch(f'{ebTestebDNSConfig.BASE_PKG}.ebDNSConfig.mGetIpListFromComputes', return_value=_ip_dom0_list),\
            patch(f'{ebTestebDNSConfig.BASE_PKG}.exaBoxNode', return_value=_exabox_node_mock) as _spy_node:
                _return_code = _instance.mConfigureHealthCheckMetrics("localhost")
                self.assertNotEquals(_return_code, 0)
                _spy_node.assert_called_once_with(ANY, aLocal=True)
                _spy_node.return_value.mExecuteCmd.assert_called_once_with(_expected_cmd)


    def test_017_add_admin_networks(self):
        """
            Scenario: Add admin dns networks
            Given the sample.xml (scaqab10adm0102clu08)
            When the options set to target 'admin'
            Then the admin networks should be added
        """

        with patch.object(self.__instance, "_ebDNSConfig__target", "admin"),\
            patch.object(self.__instance, "mAddDNSEntry") as _mock_add:

            self.__instance.mAddAdminNetworks()

            _mock_add.assert_any_call("scaqab10adm01.us.oracle.com", "10.31.112.4", "/etc/hosts.exacc_infra")
            _mock_add.assert_any_call("scaqab10adm01-c.us.oracle.com", "10.31.16.103", "/etc/hosts.exacc_infra")
            _mock_add.assert_any_call("scaqab10celadm01.us.oracle.com", "10.31.112.12", "/etc/hosts.exacc_infra")
            _mock_add.assert_any_call("scaqab10celadm01-c.us.oracle.com", "10.31.16.111", "/etc/hosts.exacc_infra")
            _mock_add.assert_any_call("scaqab10sw-adm0.us.oracle.com", "10.31.16.125", "/etc/hosts.exacc_infra")
            self.assertNotIn(call("scaqab10client01vm08.us.oracle.com", "77.0.0.9", "/etc/hosts.exacc_domu"), _mock_add.call_args_list)
            self.assertNotIn(call("scaqab10adm01vm08-bk.us.oracle.com", "76.0.0.4", "/etc/hosts.exacc_domu"), _mock_add.call_args_list)
            self.assertNotIn(call("scaqab10db01vm08str-priv1.us.oracle.com", "192.168.12.29", "/etc/hosts.exacc_domuib"), _mock_add.call_args_list)


    def test_018_add_guest_networks(self):
        """
            Scenario: Add guest dns networks
            Given the sample.xml (scaqab10adm0102clu08)
            When the options set to target 'guest'
            Then the guest networks should be added
        """

        with patch.object(self.__instance, "_ebDNSConfig__target", "guest"),\
            patch.object(self.__instance, "mAddDNSEntry") as _mock_add:

            self.__instance.mAddGuestNetworks()

            _mock_add.assert_any_call("scaqab10client01vm08.us.oracle.com", "77.0.0.9", "/etc/hosts.exacc_domu")
            _mock_add.assert_any_call("scaqab10adm01nat08.us.oracle.com", "10.31.112.34", "/etc/hosts.exacc_infra")
            _mock_add.assert_any_call("scaqab10client01vm08-nat.us.oracle.com", "10.31.112.34", "/etc/hosts.adbd_domu")
            _mock_add.assert_any_call("scaqab10adm01vm08-bk.us.oracle.com", "76.0.0.4", "/etc/hosts.exacc_domu")
            _mock_add.assert_any_call("scaqab10db01vm08str-priv1.us.oracle.com", "192.168.12.29", "/etc/hosts.exacc_domuib")
            self.assertNotIn(call("scaqab10adm01.us.oracle.com", "10.31.112.4", "/etc/hosts.exacc_infra"), _mock_add.call_args_list)
            self.assertNotIn(call("scaqab10adm01-c.us.oracle.com", "10.31.16.103", "/etc/hosts.exacc_infra"), _mock_add.call_args_list)
            self.assertNotIn(call("scaqab10celadm01.us.oracle.com", "10.31.112.12", "/etc/hosts.exacc_infra"), _mock_add.call_args_list)


    def test_019_add_vip_networks(self):
        """
            Scenario: Add vip hostname dns networks
            Given the sample.xml (scaqab10adm0102clu08)
            When the options set to target 'guest'
            Then the vip networks should be added
        """

        with patch.object(self.__instance, "_ebDNSConfig__target", "guest"),\
            patch.object(self.__instance, "mAddDNSEntry") as _mock_add:

            self.__instance.mAddVipNetworks()

            _mock_add.assert_any_call("scaqab10client01vm08-vip.us.oracle.com", "77.0.0.10", "/etc/hosts.exacc_domu")
            _mock_add.assert_any_call("scaqab10client02vm08-vip.us.oracle.com", "77.0.0.12", "/etc/hosts.exacc_domu")


    def test_020_add_scan_networks(self):
        """
            Scenario: Add the scan networks
            Given the sample.xml (scaqab10adm0102clu08)
            When the options set to target 'guest'
            Then the scan networks should be added
        """

        with patch.object(self.__instance, "_ebDNSConfig__target", "guest"),\
            patch.object(self.__instance, "mAddDNSEntryList") as _mock_add:

            self.__instance.mAddScanNetworks()

            _mock_add.assert_any_call("scaqab10vm08-scan1", ["77.0.0.13", "77.0.0.14", "77.0.0.15"], "/etc/hosts.exacc_domu")


    def test_021_add_nat_vips(self):
        """
            Scenario: Add nat_vip networks
            Given the sample.xml (scaqab10adm0102clu08)
            When the options set to target 'guest'
            Then the nat and nat-vip networks should be added
        """

        with patch.object(self.__instance, "_ebDNSConfig__target", "guest"),\
            patch.object(self.__instance, "mAddDNSEntry") as _mock_add:

            self.__instance.mAddNatVipNetworks()

            _mock_add.assert_any_call("scaqab10adm01nat08-vip.us.oracle.com", "10.31.112.139", "/etc/hosts.exacc_infra")
            _mock_add.assert_any_call("scaqab10adm02nat08-vip.us.oracle.com", "10.31.112.243", "/etc/hosts.exacc_infra")
            _mock_add.assert_any_call("scaqab10adm01nat08.us.oracle.com", "10.31.112.34", "/etc/hosts.exacc_infra")
            _mock_add.assert_any_call("scaqab10adm02nat08.us.oracle.com", "10.31.112.42", "/etc/hosts.exacc_infra")


    def test_022_build_append_cmd(self):
        """
            Scenario: Build the command to append an entry
            Given the dom0 hostname/ip and the filename
            Then the expected append command should be returned
        """
        _returned_cmd = self.__instance.mBuildAppendCmd(ebTestebDNSConfig.DUMMY_ENTRY, "/etc/hosts.exacc_infra")
        self.assertEquals(_returned_cmd, ebTestebDNSConfig.APPEND_CMD)

    def test_023_build_delete_cmd(self):
        """
            Scenario: Build command to delete a dns entry
            Given the dom0 hostname
            Then the expected cmd should be returned
        """
        _returned_cmd = self.__instance.mBuildDeleteCmd("scaqab10adm01.us.oracle.com", "/etc/hosts.exacc_infra")
        self.assertEquals(_returned_cmd, ebTestebDNSConfig.DELETE_CMD)

    def test_024_build_dns_entry(self):
        """
            Scenario: Build the dns entry string
            Given the dom0 hostname and ip
            Then the expected entry format should be returned
        """
        _returned_entry = self.__instance.mBuildDNSEntry("10.31.112.4", "scaqab10adm01.us.oracle.com")
        self.assertEquals(_returned_entry, ebTestebDNSConfig.DUMMY_ENTRY)


    def test_025_add_dns_entry(self):
        """
            Scenario: Add a dns entry
            Given a hostname and address
            Then the expected delete and append commands should be called
        """

        with patch("os.path.exists", return_value=True),\
            patch(f'{ebTestebDNSConfig.BASE_PKG}.ebDNSConfig.mExecute') as _mock_exec:

            self.__instance.mAddDNSEntry("scaqab10adm01.us.oracle.com", "10.31.112.4", "/etc/hosts.exacc_infra")

            _mock_exec.assert_any_call(ebTestebDNSConfig.DELETE_CMD)
            _mock_exec.assert_called_with(ebTestebDNSConfig.APPEND_CMD)


    def test_026_add_dns_entry_list(self):
        """
            Scenario: Add a list of dns entries
            Given a hostname with multiple ip addresses
            When called to add the dns entries
            Then the append command should be called for each address
        """

        with patch("os.path.exists", return_value=True),\
            patch(f'{ebTestebDNSConfig.BASE_PKG}.ebDNSConfig.mExecute') as _mock_exec:

            self.__instance.mAddDNSEntryList("scaqab10adm01.us.oracle.com", ["10.31.112.4", "10.31.112.4"], "/etc/hosts.exacc_infra")

            _mock_exec.assert_any_call(ebTestebDNSConfig.DELETE_CMD)
            _mock_exec.assert_any_call(ebTestebDNSConfig.APPEND_CMD)
            _mock_exec.assert_called_with(ebTestebDNSConfig.APPEND_CMD)


    def test_027_delete_dns_entry(self):
        """
            Scenario: Delete a dns entry
            Given a hostname and filename
            Then the expected delete command should be called
        """ 

        with patch("os.path.exists", return_value=True),\
            patch(f'{ebTestebDNSConfig.BASE_PKG}.ebDNSConfig.mExecute') as _mock_exec:

            self.__instance.mDeleteDNSEntry("scaqab10adm01.us.oracle.com", "/etc/hosts.exacc_infra")

            _mock_exec.assert_called_once_with(ebTestebDNSConfig.DELETE_CMD)


if __name__ == '__main__':
    unittest.main(warnings='ignore')
