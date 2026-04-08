#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/exaoci/tests_ResourceConnector.py /main/2 2025/08/01 04:35:11 asrigiri Exp $
#
# tests_ResourceConnector.py
#
# Copyright (c) 2025, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_ResourceConnector.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    prsshukl    03/12/26 - Codex UT enhancement
#    asrigiri    07/29/25 - Bug 38156507 - OCI: CREATEEXACCCONSOLEHIS FAILED AS
#                           PROXY IS SET TO NULL
#    pbellary    03/10/25 - Test cases for Resource Principals creation
#    pbellary    03/10/25 - Creation
#

import os
import json
import copy
import warnings
import unittest
from unittest.mock import MagicMock, Mock, patch
from unittest import TestCase

from tempfile import NamedTemporaryFile
from exabox.core.Error import ExacloudRuntimeError
from oci._vendor.requests.exceptions import HTTPError as OCIHTTPError
from exabox.exaoci.connectors.ResourceConnector import ResourceConnector
from exabox.exaoci.connectors.OCIConnector import OCIConnector
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo, ebLogTrace

CONFIG_BUNDLE = {"exaccInfrastructureOcid":"ocid1.exadatainfrastructure.region1.sea.anzwkljrjajnm5iamnu6elbibd3ih7zq2yb5jyzckbptxlnpspxzppk6vkdq",
                "corporateProxy":"http://www-proxy-hqdc.us.oracle.com:80",
                "hostUpdate":"https://objectstorage.r1.oracleiaas.com/p/6dIwkufOnPcwzILt1axVPlFFMwNjiO9sRIdLQAo9kErXXm-LUy2XIM4wHpcaE_Hr/n/dbaaspatchstore/b/exacc-infra-config/o/access-exacc.tar.gz",
                "monitoringConfig":{ "monitoringTenancyOcid":"ocid1.tenancy.oc1..aaaaaaaajdal6x7f4qz3w6bskaj43pymcjc5372tsopsafw6nojnxg3w6kpa",
                                      "monitoringUserOcid":"ocid1.user.oc1..aaaaaaaarqvtdw7u2kjjg4xyhvlovzqwjeena2znleablmu5b4ehq7nekedq",
                                      "compartmentId":"ocid1.compartment.oc1..aaaaaaaajgkaamcy3efjo27vnadys2lai5phuu5sbh73gfl6pqah4pngu2ha",
                                      "namespace":"exacc_anzwkljrjajnm5iamnu6elbibd3ih7zq2yb5jyzckbptxlnpspxzppk6vkdq",
                                      "region":"us-phoenix-1",
                                      "commonCompartmentId":"ocid1.compartment.oc1..aaaaaaaa4wu5qxmximpaqks53escghudxoevrtshp5edd5sl4kk3xvqmqlta"},
                "publickey":None, "ad":"ad1", "realmName":"region1", "isCpsOfflineReportEnabled":True,
                "lumberjackCompartmentOCID":"ocid1.compartment.oc1..aaaaaaaaffhrccw7ryyemac2fzyxxrxexzdlkdjliyo7hwnvmarpxqhmwiqq",
                "exaccInfrastructureCompartmentId":"ocid1.compartment.region1..aaaaaaaa7zksicn2durf353j5jqompb2ntznl52jtlu5q73k5udoeuziu6xa",
                "dnsSuffix":"r1.oracleiaas.com", "dnsInternalSuffix":"oracleiaas.com", "databaseUrl":"https://preprod-database.eu-zurich-1.oci.oraclecloud.com" }

CONFIG_BUNDLE1 = {"exaccInfrastructureOcid":"ocid1.exadatainfrastructure.region1.sea.anzwkljrjajnm5iamnu6elbibd3ih7zq2yb5jyzckbptxlnpspxzppk6vkdq",
                "corporateProxy":"http://www-proxy-hqdc.us.oracle.com:80",
                "hostUpdate":"https://objectstorage.r1.oracleiaas.com/p/6dIwkufOnPcwzILt1axVPlFFMwNjiO9sRIdLQAo9kErXXm-LUy2XIM4wHpcaE_Hr/n/dbaaspatchstore/b/exacc-infra-config/o/access-exacc.tar.gz",
                "monitoringConfig":{ "monitoringTenancyOcid":"ocid1.tenancy.oc1..aaaaaaaajdal6x7f4qz3w6bskaj43pymcjc5372tsopsafw6nojnxg3w6kpa",
                                      "monitoringUserOcid":"ocid1.user.oc1..aaaaaaaarqvtdw7u2kjjg4xyhvlovzqwjeena2znleablmu5b4ehq7nekedq",
                                      "compartmentId":"ocid1.compartment.oc1..aaaaaaaajgkaamcy3efjo27vnadys2lai5phuu5sbh73gfl6pqah4pngu2ha",
                                      "namespace":"exacc_anzwkljrjajnm5iamnu6elbibd3ih7zq2yb5jyzckbptxlnpspxzppk6vkdq",
                                      "region":"us-phoenix-1",
                                      "commonCompartmentId":"ocid1.compartment.oc1..aaaaaaaa4wu5qxmximpaqks53escghudxoevrtshp5edd5sl4kk3xvqmqlta"},
                "publickey":None, "ad":"ad1", "isCpsOfflineReportEnabled":True,
                "lumberjackCompartmentOCID":"ocid1.compartment.oc1..aaaaaaaaffhrccw7ryyemac2fzyxxrxexzdlkdjliyo7hwnvmarpxqhmwiqq",
                "exaccInfrastructureCompartmentId":"ocid1.compartment.region1..aaaaaaaa7zksicn2durf353j5jqompb2ntznl52jtlu5q73k5udoeuziu6xa",
                "dnsInternalSuffix":"oracleiaas.com", "databaseUrl":"http://preprod-database.eu-zurich-1.oci.oraclecloud.com" }

CONFIG_BUNDLE2 = {"exaccInfrastructureOcid":"ocid1.exadatainfrastructure.oc4.sea.anzwkljrjajnm5iamnu6elbibd3ih7zq2yb5jyzckbptxlnpspxzppk6vkdq",
                "corporateProxy":"http://www-proxy-hqdc.us.oracle.com:80",
                "hostUpdate":"https://objectstorage.r1.oracleiaas.com/p/6dIwkufOnPcwzILt1axVPlFFMwNjiO9sRIdLQAo9kErXXm-LUy2XIM4wHpcaE_Hr/n/dbaaspatchstore/b/exacc-infra-config/o/access-exacc.tar.gz",
                "monitoringConfig":{ "monitoringTenancyOcid":"ocid1.tenancy.oc1..aaaaaaaajdal6x7f4qz3w6bskaj43pymcjc5372tsopsafw6nojnxg3w6kpa",
                                      "monitoringUserOcid":"ocid1.user.oc1..aaaaaaaarqvtdw7u2kjjg4xyhvlovzqwjeena2znleablmu5b4ehq7nekedq",
                                      "compartmentId":"ocid1.compartment.oc1..aaaaaaaajgkaamcy3efjo27vnadys2lai5phuu5sbh73gfl6pqah4pngu2ha",
                                      "namespace":"exacc_anzwkljrjajnm5iamnu6elbibd3ih7zq2yb5jyzckbptxlnpspxzppk6vkdq",
                                      "region":"us-phoenix-1",
                                      "commonCompartmentId":"ocid1.compartment.oc1..aaaaaaaa4wu5qxmximpaqks53escghudxoevrtshp5edd5sl4kk3xvqmqlta"},
                "publickey":None, "ad":"ad1", "realmName":"sea201608exdd013", "isCpsOfflineReportEnabled":True,
                "lumberjackCompartmentOCID":"ocid1.compartment.oc1..aaaaaaaaffhrccw7ryyemac2fzyxxrxexzdlkdjliyo7hwnvmarpxqhmwiqq",
                "exaccInfrastructureCompartmentId":"ocid1.compartment.region1..aaaaaaaa7zksicn2durf353j5jqompb2ntznl52jtlu5q73k5udoeuziu6xa",
                "dnsInternalSuffix":"oracleiaas.com", "databaseUrl":None }

CONFIG_BUNDLE3 = {"exaccInfrastructureOcid":"ocid1.exadatainfrastructure.oc4.sea.anzwkljrjajnm5iamnu6elbibd3ih7zq2yb5jyzckbptxlnpspxzppk6vkdq",
                "corporateProxy":"http://www-proxy-hqdc.us.oracle.com:80",
                "hostUpdate":"https://objectstorage.r1.oracleiaas.com/p/6dIwkufOnPcwzILt1axVPlFFMwNjiO9sRIdLQAo9kErXXm-LUy2XIM4wHpcaE_Hr/n/dbaaspatchstore/b/exacc-infra-config/o/access-exacc.tar.gz",
                "monitoringConfig":{ "monitoringTenancyOcid":"ocid1.tenancy.oc1..aaaaaaaajdal6x7f4qz3w6bskaj43pymcjc5372tsopsafw6nojnxg3w6kpa",
                                      "monitoringUserOcid":"ocid1.user.oc1..aaaaaaaarqvtdw7u2kjjg4xyhvlovzqwjeena2znleablmu5b4ehq7nekedq",
                                      "compartmentId":"ocid1.compartment.oc1..aaaaaaaajgkaamcy3efjo27vnadys2lai5phuu5sbh73gfl6pqah4pngu2ha",
                                      "namespace":"exacc_anzwkljrjajnm5iamnu6elbibd3ih7zq2yb5jyzckbptxlnpspxzppk6vkdq",
                                      "region":"us-phoenix-1",
                                      "commonCompartmentId":"ocid1.compartment.oc1..aaaaaaaa4wu5qxmximpaqks53escghudxoevrtshp5edd5sl4kk3xvqmqlta"},
                "publickey":None, "ad":"ad1", "realmName":"sea201608exdd013", "isCpsOfflineReportEnabled":True,
                "lumberjackCompartmentOCID":"ocid1.compartment.oc1..aaaaaaaaffhrccw7ryyemac2fzyxxrxexzdlkdjliyo7hwnvmarpxqhmwiqq",
                "exaccInfrastructureCompartmentId":"ocid1.compartment.region1..aaaaaaaa7zksicn2durf353j5jqompb2ntznl52jtlu5q73k5udoeuziu6xa",
                "dnsInternalSuffix":"oracleiaas.com", "databaseUrl":None }

CONFIG_REALM1 = {"exaccInfrastructureOcid":"ocid1.exadatainfrastructure.region1.sea.anzwkljrjajnm5iamnu6elbibd3ih7zq2yb5jyzckbptxlnpspxzppk6vkdq",
                "hostUpdate":"https://objectstorage.r1.oracleiaas.com/p/6dIwkufOnPcwzILt1axVPlFFMwNjiO9sRIdLQAo9kErXXm-LUy2XIM4wHpcaE_Hr/n/dbaaspatchstore/b/exacc-infra-config/o/access-exacc.tar.gz",
                "monitoringConfig":{ "monitoringTenancyOcid":"ocid1.tenancy.oc1..aaaaaaaajdal6x7f4qz3w6bskaj43pymcjc5372tsopsafw6nojnxg3w6kpa",
                                      "monitoringUserOcid":"ocid1.user.oc1..aaaaaaaarqvtdw7u2kjjg4xyhvlovzqwjeena2znleablmu5b4ehq7nekedq",
                                      "compartmentId":"ocid1.compartment.oc1..aaaaaaaajgkaamcy3efjo27vnadys2lai5phuu5sbh73gfl6pqah4pngu2ha",
                                      "namespace":"exacc_anzwkljrjajnm5iamnu6elbibd3ih7zq2yb5jyzckbptxlnpspxzppk6vkdq",
                                      "region":"us-phoenix-1",
                                      "commonCompartmentId":"ocid1.compartment.oc1..aaaaaaaa4wu5qxmximpaqks53escghudxoevrtshp5edd5sl4kk3xvqmqlta"},
                "publickey":None, "ad":"ad1", "realmName":"region1", "isCpsOfflineReportEnabled":True,
                "lumberjackCompartmentOCID":"ocid1.compartment.oc1..aaaaaaaaffhrccw7ryyemac2fzyxxrxexzdlkdjliyo7hwnvmarpxqhmwiqq",
                "exaccInfrastructureCompartmentId":"ocid1.compartment.region1..aaaaaaaa7zksicn2durf353j5jqompb2ntznl52jtlu5q73k5udoeuziu6xa",
                "dnsInternalSuffix":"oracleiaas.com", "databaseUrl":None }

CONFIG_REALM2 = {"exaccInfrastructureOcid":"ocid1.exadatainfrastructure.oc4.sea.anzwkljrjajnm5iamnu6elbibd3ih7zq2yb5jyzckbptxlnpspxzppk6vkdq",
                "monitoringConfig":{ "monitoringTenancyOcid":"ocid1.tenancy.oc1..aaaaaaaajdal6x7f4qz3w6bskaj43pymcjc5372tsopsafw6nojnxg3w6kpa",
                                      "monitoringUserOcid":"ocid1.user.oc1..aaaaaaaarqvtdw7u2kjjg4xyhvlovzqwjeena2znleablmu5b4ehq7nekedq",
                                      "compartmentId":"ocid1.compartment.oc1..aaaaaaaajgkaamcy3efjo27vnadys2lai5phuu5sbh73gfl6pqah4pngu2ha",
                                      "namespace":"exacc_anzwkljrjajnm5iamnu6elbibd3ih7zq2yb5jyzckbptxlnpspxzppk6vkdq",
                                      "region":"us-phoenix-1",
                                      "commonCompartmentId":"ocid1.compartment.oc1..aaaaaaaa4wu5qxmximpaqks53escghudxoevrtshp5edd5sl4kk3xvqmqlta"},
                "publickey":None, "ad":"ad1", "realmName":"sea201608exdd013", "isCpsOfflineReportEnabled":True,
                "lumberjackCompartmentOCID":"ocid1.compartment.oc1..aaaaaaaaffhrccw7ryyemac2fzyxxrxexzdlkdjliyo7hwnvmarpxqhmwiqq",
                "exaccInfrastructureCompartmentId":"ocid1.compartment.region1..aaaaaaaa7zksicn2durf353j5jqompb2ntznl52jtlu5q73k5udoeuziu6xa",
                "dnsInternalSuffix":"oracleiaas.com", "databaseUrl":None }

CONFIG_REALM3 = {"exaccInfrastructureOcid":"ocid1.exadatainfrastructure.region1.sea.anzwkljrjajnm5iamnu6elbibd3ih7zq2yb5jyzckbptxlnpspxzppk6vkdq",
                "monitoringConfig":{ "monitoringTenancyOcid":"ocid1.tenancy.oc1..aaaaaaaajdal6x7f4qz3w6bskaj43pymcjc5372tsopsafw6nojnxg3w6kpa",
                                      "monitoringUserOcid":"ocid1.user.oc1..aaaaaaaarqvtdw7u2kjjg4xyhvlovzqwjeena2znleablmu5b4ehq7nekedq",
                                      "compartmentId":"ocid1.compartment.oc1..aaaaaaaajgkaamcy3efjo27vnadys2lai5phuu5sbh73gfl6pqah4pngu2ha",
                                      "namespace":"exacc_anzwkljrjajnm5iamnu6elbibd3ih7zq2yb5jyzckbptxlnpspxzppk6vkdq",
                                      "region":"us-phoenix-1",
                                      "commonCompartmentId":"ocid1.compartment.oc1.aaaaaaaa4wu5qxmximpaqks53escghudxoevrtshp5edd5sl4kk3xvqmqlta"},
                "publickey":None, "ad":"ad1", "isCpsOfflineReportEnabled":True,
                "lumberjackCompartmentOCID":"ocid1.compartment.oc1..aaaaaaaaffhrccw7ryyemac2fzyxxrxexzdlkdjliyo7hwnvmarpxqhmwiqq",
                "exaccInfrastructureCompartmentId":"ocid1.compartment.region1..aaaaaaaa7zksicn2durf353j5jqompb2ntznl52jtlu5q73k5udoeuziu6xa",
                "dnsInternalSuffix":"oracleiaas.com", "databaseUrl":None }

CONFIG_REALM4 = {"exaccInfrastructureOcid":"ocid1.exadatainfrastructure.oc4",
                "monitoringConfig":{ "monitoringTenancyOcid":"ocid1.tenancy.oc1..aaaaaaaajdal6x7f4qz3w6bskaj43pymcjc5372tsopsafw6nojnxg3w6kpa",
                                      "monitoringUserOcid":"ocid1.user.oc1..aaaaaaaarqvtdw7u2kjjg4xyhvlovzqwjeena2znleablmu5b4ehq7nekedq",
                                      "compartmentId":"ocid1.compartment.oc1..aaaaaaaajgkaamcy3efjo27vnadys2lai5phuu5sbh73gfl6pqah4pngu2ha",
                                      "namespace":"exacc_anzwkljrjajnm5iamnu6elbibd3ih7zq2yb5jyzckbptxlnpspxzppk6vkdq",
                                      "region":"us-phoenix-1",
                                      "commonCompartmentId":"ocid1.compartment.oc1..aaaaaaaa4wu5qxmximpaqks53escghudxoevrtshp5edd5sl4kk3xvqmqlta"},
                "publickey":None, "ad":"ad1", "isCpsOfflineReportEnabled":True,
                "lumberjackCompartmentOCID":"ocid1.compartment.oc1..aaaaaaaaffhrccw7ryyemac2fzyxxrxexzdlkdjliyo7hwnvmarpxqhmwiqq",
                "exaccInfrastructureCompartmentId":"ocid1.compartment.region1..aaaaaaaa7zksicn2durf353j5jqompb2ntznl52jtlu5q73k5udoeuziu6xa",
                "dnsInternalSuffix":"oracleiaas.com", "databaseUrl":None }

CONFIG_REALM5 = {"exaccInfrastructureOcid":"ocid1.exadatainfrastructure.oc4.sea.anzwkljrjajnm5iamnu6elbibd3ih7zq2yb5jyzckbptxlnpspxzppk6vkdq",
                "monitoringConfig":{ "monitoringTenancyOcid":"ocid1.tenancy.oc1..aaaaaaaajdal6x7f4qz3w6bskaj43pymcjc5372tsopsafw6nojnxg3w6kpa",
                                      "monitoringUserOcid":"ocid1.user.oc1..aaaaaaaarqvtdw7u2kjjg4xyhvlovzqwjeena2znleablmu5b4ehq7nekedq",
                                      "compartmentId":"ocid1.compartment.oc1..aaaaaaaajgkaamcy3efjo27vnadys2lai5phuu5sbh73gfl6pqah4pngu2ha",
                                      "namespace":"exacc_anzwkljrjajnm5iamnu6elbibd3ih7zq2yb5jyzckbptxlnpspxzppk6vkdq",
                                      "region":"us-phoenix-1",
                                      "commonCompartmentId":"ocid1.compartment.oc1..aaaaaaaa4wu5qxmximpaqks53escghudxoevrtshp5edd5sl4kk3xvqmqlta"},
                "publickey":None, "ad":"ad1", "isCpsOfflineReportEnabled":True,
                "lumberjackCompartmentOCID":"ocid1.compartment.oc1..aaaaaaaaffhrccw7ryyemac2fzyxxrxexzdlkdjliyo7hwnvmarpxqhmwiqq",
                "exaccInfrastructureCompartmentId":"ocid1.compartment.region1..aaaaaaaa7zksicn2durf353j5jqompb2ntznl52jtlu5q73k5udoeuziu6xa",
                "dnsInternalSuffix":"oracleiaas.com", "databaseUrl":None }

OCPS_SETUP = {
    "exaOcid": "ocid1.exadatainfrastructure.region1.sea.anzwkljs3vfwx6qaj6x4a6dqdz5ffqrvbwsyxfvebf4vwwvgrr65pec3um3a",
    "adminNetworkCidr": "10.106.64.0/18",
    "ibNetworkCidr": "192.168.144.0/23",
    "ntp": [
        "10.132.0.121",
        "10.132.0.122"
    ],
    "dns": [
        "206.223.27.1",
        "206.223.27.2"
    ],
    "serviceType": "nonATP",
    "vpnHeIp": "vpn-he.sic-dbaas.exacc.oc9qadev.com",
    "ossUrl": "https://swiftobjectstorage.us-phoenix-1.oraclecloud.com/v1/intexadatateam/ImageManagement",
    "oracle_home": "/u01/oracleclient",
    "rackName": "iad190676exd-atpmg-scaqax05XXX-clu01",
    "rackBaseName": "iad190676exd-atpmg-scaqax05XXX",
    "cpsCn": "anzwkljs3vfwx6qaj6x4a6dqdz5ffqrvbwsyxfvebf4vwwvgrr65pec3um3a",
    "cpsCnStandby": "anzwkljs3vfwx6qaj6x4a6dqdz5ffqrvbwsyxfvebf4vwwvgrr65pec3um3a-s",
    "patchServer_ip": "10.106.68.60",
    "patchServer_subnet": "10.106.64.0/18",
    "patchServer_gateway": "10.106.64.1",
    "netmask": "255.255.192.0",
    "patchServer_host_network_interface": "eth0",
    "forwardProxy_ip": "10.106.68.62",
    "forwardProxy_port": "3080",
    "forwardProxy_subnet": "10.106.64.0/18",
    "forwardProxy_netmask": "255.255.192.0",
    "forwardProxy_gateway": "10.106.64.1",
    "forwardProxy_host_network_interface": "eth0",
    "dhcp": "false",
    "customer_netmask": "255.255.240.0",
    "customer_gateway": "10.95.112.1",
    "proxy": "http://www-proxy-hqdc.us.oracle.com:80",
    "linux_users": {
        "installation": "ecra",
        "operations": "ops"
    },
    "linux_groups": {
        "installation": "dba",
        "operations": "docker"
    },
    "install_dir": "/opt/oci/exacc",
    "SDO": "",
    "exabox_updates": {
        "ociexacc": "True"
    },
    "pkey": None,
    "vlan": "3320",
    "servers": [
        {
            "hostname": "scaqax05cps01",
            "username": "",
            "agent_port": 7080,
            "worker_port": 9100,
            "remote_mgmt": 7071,
            "cpsagent_port": 2081,
            "dbcpagent_port": 7070,
            "ib_interface_name": "stbondib00",
            "adminIp": "10.106.68.56",
            "ilomIp": "10.106.68.58",
            "ibAdmin": [
                "192.168.145.165",
                "192.168.145.166"
            ],
            "ip": "10.95.116.133"
        },
        {
            "hostname": "scaqax05cps02",
            "username": "",
            "agent_port": 7080,
            "worker_port": 9100,
            "remote_mgmt": 7071,
            "cpsagent_port": 2081,
            "dbcpagent_port": 7070,
            "ib_interface_name": "stbondib00",
            "adminIp": "10.106.68.57",
            "ilomIp": "10.106.68.59",
            "ibAdmin": [
                "192.168.145.167",
                "192.168.145.168"
            ],
            "ip": "10.95.116.134"
        }
    ],
    "adminDomain": "oracle.local",
    "ociAdminHeadEndType": "WSS",
    "wssClientCertPassword": "RFZETldGV1VPNQ==",
    "AdmWSSHeFqdn": [
        "wsshea.oraclesccm.net",
        "wsshea.oraclesccm.net",
        "wsshea.oraclesccm.net"
    ],
    "MgmtWSSHeFqdn": [
        "wsshem.oraclesccm.net",
        "wsshem.oraclesccm.net",
        "wsshem.oraclesccm.net"
    ],
    "iaasDomainComponent": "oracleiaas.com",
    "realmDomainComponent": "oraclecloud.com",
    "ociRegion": "us-ashburn-1",
    "ociRegionShortForm": "IAD",
    "availabilityDomain": [
        "ad1",
        "ad2",
        "ad3",
        "pop1",
        "pop2"
    ],
    "fedramp": "DISABLED"
}

OXPA_INPUT = { "OciExaCapacityParam": { "idemtoken": "7ca6631f-7261-4be3-8fe6-b2966c602581",
                                        "tenantOcid": "ocid1.tenancy.region1..aaaaaaaagyw5okosjg54csr3u5qgaxvtjufz55537h44mjy2umiqur4z5w3a",
                "tenantName": "atpmgmt", "exaName": "scaqax05adm0102", "racksize": "elastic",
                "exaOcid": "ocid1.exadatainfrastructure.region1.sea.anzwkljs3vfwx6qaj6x4a6dqdz5ffqrvbwsyxfvebf4vwwvgrr65pec3um3a", 
                "dns": [ "206.223.27.1", "206.223.27.2" ], "ntp": [ "10.132.0.121", "10.132.0.122" ],
                "timezone": "America/Mexico_City", "multiVM": 1, "nodeSubset": 1, "model": "X11M", "env": "ociExaCC",
                "adminNwCidr": "10.106.64.0/18", "ibNwCidr": "192.168.144.0/22", "cores": 2280, "memoryGb": 4170,
                "cellServerCount": 4, "computeCount": 3, "ociUpgrade": None, "ociMigrateGen2Gen2": None, "ociMigrateGen2Gen2UUID": None,
                "controlPlaneServerAttribs": { "ip1": "10.95.116.133", "ip2": "10.95.116.134", "gateway": "10.95.112.1",
                                               "netmask": "255.255.240.0", "proxy": "http://www-proxy-hqdc.us.oracle.com:80", "dhcp": False },
      "compartmentOcid": "ocid1.compartment.region1..aaaaaaaabfznrkmfwp4smp42jc5xkey27akmrez54gddolf56s6pcr62cnia",
      "multiRack": 1, "drNetworkBondingMode": None, "computeType": "X11M", "cellType": "X11M", "storageGb": 327680, "clusterCount": 24,
      "sarJsonFile": "ewogICAgImdlbmVyYXRpb24iOiAiWDExTSIsCiAgICAidG90YWwgcmFja3MiOiAyLAogICAgInRvdGFsIGNvbXB1dGUiOiAzLAogICAgInRvdGFsIHN0b3JhZ2UiOiA0LAogICAgInRvdGFsIGV4aXN0aW5nIHJhY2tzIjogMCwKICAgICJ0b3RhbCBleGlzdGluZyBjb21wdXRlIjogMCwKICAgICJ0b3RhbCBleGlzdGluZyBzdG9yYWdlIjogMCwKICAgICJyYWNrcyI6IFsKICAgICAgICB7CiAgICAgICAgICAgICJyYWNrX251bSI6IDEsCiAgICAgICAgICAgICJuZXcgcmFjayI6ICJ5ZXMiLAogICAgICAgICAgICAibnVtYmVyIGNvbXB1dGUiOiAyLAogICAgICAgICAgICAibnVtYmVyIHN0b3JhZ2UiOiAzLAogICAgICAgICAgICAiZXhpc3RpbmcgY29tcHV0ZSI6IDAsCiAgICAgICAgICAgICJleGlzdGluZyBzdG9yYWdlIjogMCwKICAgICAgICAgICAgImNvbXBvbmVudHMiOiBbCiAgICAgICAgICAgICAgICB7CiAgICAgICAgICAgICAgICAgICAgInR5cGUiOiAic3BpbmUiLAogICAgICAgICAgICAgICAgICAgICJ1bG9jIjogMSwKICAgICAgICAgICAgICAgICAgICAidWhlaWdodCI6IDEsCiAgICAgICAgICAgICAgICAgICAgIm5ldyBjb21wb25lbnQiOiAieWVzIgogICAgICAgICAgICAgICAgfSwKICAgICAgICAgICAgICAgIHsKICAgICAgICAgICAgICAgICAgICAidHlwZSI6ICJzdG9yYWdlIiwKICAgICAgICAgICAgICAgICAgICAidWxvYyI6IDIsCiAgICAgICAgICAgICAgICAgICAgInVoZWlnaHQiOiAyLAogICAgICAgICAgICAgICAgICAgICJuZXcgY29tcG9uZW50IjogInllcyIKICAgICAgICAgICAgICAgIH0sCiAgICAgICAgICAgICAgICB7CiAgICAgICAgICAgICAgICAgICAgInR5cGUiOiAic3RvcmFnZSIsCiAgICAgICAgICAgICAgICAgICAgInVsb2MiOiA0LAogICAgICAgICAgICAgICAgICAgICJ1aGVpZ2h0IjogMiwKICAgICAgICAgICAgICAgICAgICAibmV3IGNvbXBvbmVudCI6ICJ5ZXMiCiAgICAgICAgICAgICAgICB9LAogICAgICAgICAgICAgICAgewogICAgICAgICAgICAgICAgICAgICJ0eXBlIjogInN0b3JhZ2UiLAogICAgICAgICAgICAgICAgICAgICJ1bG9jIjogNiwKICAgICAgICAgICAgICAgICAgICAidWhlaWdodCI6IDIsCiAgICAgICAgICAgICAgICAgICAgIm5ldyBjb21wb25lbnQiOiAieWVzIgogICAgICAgICAgICAgICAgfSwKICAgICAgICAgICAgICAgIHsKICAgICAgICAgICAgICAgICAgICAidHlwZSI6ICJjb21wdXRlIiwKICAgICAgICAgICAgICAgICAgICAidWxvYyI6IDE2LAogICAgICAgICAgICAgICAgICAgICJ1aGVpZ2h0IjogMSwKICAgICAgICAgICAgICAgICAgICAibmV3IGNvbXBvbmVudCI6ICJ5ZXMiCiAgICAgICAgICAgICAgICB9LAogICAgICAgICAgICAgICAgewogICAgICAgICAgICAgICAgICAgICJ0eXBlIjogImNvbXB1dGUiLAogICAgICAgICAgICAgICAgICAgICJ1bG9jIjogMTcsCiAgICAgICAgICAgICAgICAgICAgInVoZWlnaHQiOiAxLAogICAgICAgICAgICAgICAgICAgICJuZXcgY29tcG9uZW50IjogInllcyIKICAgICAgICAgICAgICAgIH0sCiAgICAgICAgICAgICAgICB7CiAgICAgICAgICAgICAgICAgICAgInR5cGUiOiAiY3BzIiwKICAgICAgICAgICAgICAgICAgICAidWxvYyI6IDM3LAogICAgICAgICAgICAgICAgICAgICJ1aGVpZ2h0IjogMSwKICAgICAgICAgICAgICAgICAgICAibmV3IGNvbXBvbmVudCI6ICJ5ZXMiCiAgICAgICAgICAgICAgICB9LAogICAgICAgICAgICAgICAgewogICAgICAgICAgICAgICAgICAgICJ0eXBlIjogImNwcyIsCiAgICAgICAgICAgICAgICAgICAgInVsb2MiOiAzOSwKICAgICAgICAgICAgICAgICAgICAidWhlaWdodCI6IDEsCiAgICAgICAgICAgICAgICAgICAgIm5ldyBjb21wb25lbnQiOiAieWVzIgogICAgICAgICAgICAgICAgfQogICAgICAgICAgICBdCiAgICAgICAgfSwKICAgICAgICB7CiAgICAgICAgICAgICJyYWNrX251bSI6IDIsCiAgICAgICAgICAgICJuZXcgcmFjayI6ICJ5ZXMiLAogICAgICAgICAgICAibnVtYmVyIGNvbXB1dGUiOiAxLAogICAgICAgICAgICAibnVtYmVyIHN0b3JhZ2UiOiAxLAogICAgICAgICAgICAiZXhpc3RpbmcgY29tcHV0ZSI6IDAsCiAgICAgICAgICAgICJleGlzdGluZyBzdG9yYWdlIjogMCwKICAgICAgICAgICAgImNvbXBvbmVudHMiOiBbCiAgICAgICAgICAgICAgICB7CiAgICAgICAgICAgICAgICAgICAgInR5cGUiOiAic3BpbmUiLAogICAgICAgICAgICAgICAgICAgICJ1bG9jIjogMSwKICAgICAgICAgICAgICAgICAgICAidWhlaWdodCI6IDEsCiAgICAgICAgICAgICAgICAgICAgIm5ldyBjb21wb25lbnQiOiAieWVzIgogICAgICAgICAgICAgICAgfSwKICAgICAgICAgICAgICAgIHsKICAgICAgICAgICAgICAgICAgICAidHlwZSI6ICJzdG9yYWdlIiwKICAgICAgICAgICAgICAgICAgICAidWxvYyI6IDI5LAogICAgICAgICAgICAgICAgICAgICJ1aGVpZ2h0IjogMiwKICAgICAgICAgICAgICAgICAgICAibmV3IGNvbXBvbmVudCI6ICJ5ZXMiCiAgICAgICAgICAgICAgICB9LAogICAgICAgICAgICAgICAgewogICAgICAgICAgICAgICAgICAgICJ0eXBlIjogImNvbXB1dGUiLAogICAgICAgICAgICAgICAgICAgICJ1bG9jIjogMzksCiAgICAgICAgICAgICAgICAgICAgInVoZWlnaHQiOiAxLAogICAgICAgICAgICAgICAgICAgICJuZXcgY29tcG9uZW50IjogInllcyIKICAgICAgICAgICAgICAgIH0KICAgICAgICAgICAgXQogICAgICAgIH0KICAgIF0KfQo=",
      "clientNetworkBondingMode": "active-backup", "backupNetworkBondingMode": "active-backup",
      "requestId": "7ca6631f-7261-4be3-8fe6-b2966c602581",
      "exaccocid": "ocid1.exadatainfrastructure.region1.sea.anzwkljs3vfwx6qaj6x4a6dqdz5ffqrvbwsyxfvebf4vwwvgrr65pec3um3a",
      "firstRackName": "iad190676exd-atpmg-scaqax05XXX-clu01",
      "rackBaseName": "iad190676exd-atpmg-scaqax05XXX",
      "rackPrefix": "iad190676exd",
      "q_in_q": True,
      "ConfigBundleBasePath": "/scratch2/oracle/ecra_installs/ecramain/mw_home/tmp/iad190676exd-atpmg-scaqax05XXX-clu01",
      "oxpaCluListJsonFile": "/scratch2/oracle/ecra_installs/ecramain/mw_home/tmp/iad190676exd-atpmg-scaqax05XXX-clu01/iad190676exd-atpmg-scaqax05XXX-clu01.oxpaCluList.json",
      "oxpaOcpsNwCfgJsonFile": "/scratch2/oracle/ecra_installs/ecramain/mw_home/tmp/iad190676exd-atpmg-scaqax05XXX-clu01/iad190676exd-atpmg-scaqax05XXX-clu01_control_plane_server_network_conf.json",
      "oxpaNodeInfoJsonFile": "/scratch2/oracle/ecra_installs/ecramain/mw_home/tmp/iad190676exd-atpmg-scaqax05XXX-clu01/iad190676exd-atpmg-scaqax05XXX-clu01node_info.json",
      "oxpaComputeInfoJsonFile": "/scratch2/oracle/ecra_installs/ecramain/mw_home/tmp/iad190676exd-atpmg-scaqax05XXX-clu01/iad190676exd-atpmg-scaqax05XXX-clu01compute_info.json",
      "keysDirPath": "/scratch2/oracle/ecra_installs/ecramain/mw_home/tmp/iad190676exd-atpmg-scaqax05XXX-clu01/keys",
      "wssServerAdminCert": "/scratch2/oracle/ecra_installs/ecramain/mw_home/tmp/iad190676exd-atpmg-scaqax05XXX-clu01/ADMIN-encoded.crt",
      "adminWssHeFqdn": "/scratch2/oracle/ecra_installs/ecramain/mw_home/tmp/iad190676exd-atpmg-scaqax05XXX-clu01/admwssclient.conf",
      "wssAdminP12": "/tmp/websocket/ocid1.exadatainfrastructure.region1.sea.anzwkljs3vfwx6qaj6x4a6dqdz5ffqrvbwsyxfvebf4vwwvgrr65pec3um3a/ocid1.exadatainfrastructure.region1.sea.anzwkljs3vfwx6qaj6x4a6dqdz5ffqrvbwsyxfvebf4vwwvgrr65pec3um3a-a.p12",
      "wssServerMgmtCert": "/scratch2/oracle/ecra_installs/ecramain/mw_home/tmp/iad190676exd-atpmg-scaqax05XXX-clu01/MGMT-encoded.crt",
      "mgmtWssHeFqdn": "/scratch2/oracle/ecra_installs/ecramain/mw_home/tmp/iad190676exd-atpmg-scaqax05XXX-clu01/mgmtwssclient.conf",
      "wssMgmtP12": "/tmp/websocket/ocid1.exadatainfrastructure.region1.sea.anzwkljs3vfwx6qaj6x4a6dqdz5ffqrvbwsyxfvebf4vwwvgrr65pec3um3a/ocid1.exadatainfrastructure.region1.sea.anzwkljs3vfwx6qaj6x4a6dqdz5ffqrvbwsyxfvebf4vwwvgrr65pec3um3a-m.p12",
      "cpsAgentWallet": "/scratch2/oracle/ecra_installs/ecramain/mw_home/tmp/iad190676exd-atpmg-scaqax05XXX-clu01/CPSAgentWallet.b64",
      "dbcsAgentWallet": "/scratch2/oracle/ecra_installs/ecramain/mw_home/tmp/iad190676exd-atpmg-scaqax05XXX-clu01/DBCSAgentWallet.b64",
      "jsonSarFile": "/scratch2/oracle/ecra_installs/ecramain/mw_home/tmp/iad190676exd-atpmg-scaqax05XXX-clu01/iad190676exd-atpmg-scaqax05XXX-clu01_sar.json",
      "ocpsSetupJsonFile": "/scratch2/oracle/ecra_installs/ecramain/mw_home/tmp/iad190676exd-atpmg-scaqax05XXX-clu01/iad190676exd-atpmg-scaqax05XXX-clu01.ocpsSetup.json",
      "controlServerPayload": {
        "exa_ocid": "ocid1.exadatainfrastructure.region1.sea.anzwkljs3vfwx6qaj6x4a6dqdz5ffqrvbwsyxfvebf4vwwvgrr65pec3um3a",
        "ip_control_server1": "10.95.116.133",
        "ip_control_server2": "10.95.116.134",
        "gateway": "10.95.112.1",
        "netmask": "255.255.240.0",
        "proxy": "http://www-proxy-hqdc.us.oracle.com:80",
        "dhcp": "N",
        "cps_cn": "anzwkljs3vfwx6qaj6x4a6dqdz5ffqrvbwsyxfvebf4vwwvgrr65pec3um3a",
        "cps_cn_standby": "anzwkljs3vfwx6qaj6x4a6dqdz5ffqrvbwsyxfvebf4vwwvgrr65pec3um3a-s",
        "ssh_pub_key": "ssh-rsa MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA+KsHQZfJmLyQosjE5em/TULtzRd4ioaeSMDPLx35qvIhhXPl7T5WRyuMmX3SkHm5Rb8nxt2FyvKfb+ECpS8Avzq7zGb5lrgQRwBOltWWhdHcYFJ1A7H7KkdM1eKE4yRBpVm3w7kYVsIJwqXpwwcs+Pv8imq2gkxmgyKCQedBHunawpF6lp91zcgk6XF+/LHCl6hs9NAyN6ZznvRWF7Q/moZmhIZxGf3OxNB5J5vcWNkcPGKgB2xoOojOArQHtIuSxWTSAyzbzanXvNnfeU2QeEGG1efjJ9R2X+pe4WqlBWILOWUrQ1oX3mP9aqYa7psHir74dOMdo41wcE8twk6GvwIDAQAB",
        "ssh_priv_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQD4qwdBl8mYvJCi\nyMTl6b9NQu3NF3iKhp5IwM8vHfmq8iGFc+XtPlZHK4yZfdKQeblFvyfG3YXK8p9v\n4QKlLwC/OrvMZvmWuBBHAE6W1ZaF0dxgUnUDsfsqR0zV4oTjJEGlWbfDuRhWwgnC\npenDByz4+/yKaraCTGaDIoJB50Ee6drCkXqWn3XNyCTpcX78scKXqGz00DI3pnOe\n9FYXtD+ahmaEhnEZ/c7E0Hknm9xY2Rw8YqAHbGg6iM4CtAe0i5LFZNIDLNvNqde8\n2d95TZB4QYbV5+Mn1HZf6l7haqUFYgs5ZStDWhfeY/1qphrumweKvvh04x2jjXBw\nTy3CToa/AgMBAAECggEAFAJjG5aUrLsjok2odl2oPJXRn8qvMuphKzaElWSClgxU\nwTHRwxTciW6KKkGzI1gAHgojL7/ch7edN7nx5gvRshGOUgTJOaUG/keai02VhqAb\n7Q5Fhy4XqU/CcYWALuzYcW82N8QZnsWPVn/WPxDBQCm6qQKsO/Dc4NlyhM4QceWz\nzlpfkQBLKuV9qhv1Ij+XiZXIaFSiBR1HK+ItdGBre98SGOLJGegf9uSaJvat+7Lp\nDXilO2qjwiXnIDvkWmM0/qAlXeeTaOxEJU1viqsXd/QVXT7DtS+tP51mpRStBOvc\nvSa9aODY4goPpPAMTL0z7KWLoeBetcxFOfmhwfA3VQKBgQD/vM0BRtJQS7PlCrDR\nk4ZYDpxEdd2ZFqz6nKfK92XKl+d2kfN6b516WW5qH3KlevA/z891tCAW5q/DYFJC\nUNF4gKTUfg2p5ZqCJonduW5qOwVq/4eNZ44QvUIEz7yCtu+UbCbfQjwbIhS9wjRb\nUUOx4tTJuJa/es1T+kVdjhQ3ewKBgQD47F60OgkwIVJuo1P/nHIuKVm7mtWmB5hx\nQh5Dl9RTWsyq97/w1LI7FAxNbsre1ksULvAYGAgH/KdkMUWo1O4Zf/3oyfw0CuHS\nByaIdKtrHy7joY2zwpYie+lpzGQ4URMEgLa7rO2l/euaGL4x2bTMny2fKyyRH3SA\nc3jrrUZojQKBgAC5znMkelBUBqytvRa7LnRthjADjZ9zmwYTD77ZuOY8TCHgBCri\nyjWgr1mJwU+K68eilVomKrkl6nXJfjJF/HI1G0KnIO7MggXAij+g2RlgFYHaO85A\n7vxJLTjKRiSw1Dk9nVag337MN/bZ6EAiGOkWVbhE19ivRonoee3sC06lAoGBALU7\nSvxG4Nek+yJIUejhm5QWURmw8mpOT2PucqBd053YlvjHJn0OLrGquAZMavHw7XrF\nbdLs9DP0dF8TLJduZ+gy8sdg//lYDu/eeuSQpRl5+6aJweSmAK8crmV0BWenR4RY\nvjJIBkJ7a+SmrRsYWXU9U3b2dR033JeE+v4ECyYlAoGBAMbTl61TeMMV1xac8n+b\nyDKQLVr60dLwrD8Z/H/pS/Zc58ejl96S8C62u3qj9THrdxvNt7US/Rv0JVDEt2XE\nqAGpgNqBPI+req97vcSND7JYAMbe0CQZomV3MC5LlDn2WcsJiBzvnF4zxm2yaidY\ncGGOA8Mh8aqJNM6yHW5/UvC7\n-----END RSA PRIVATE KEY-----\n"
      },
      "wssClientCertPassword": "RFZETldGV1VPNQ==",
      "prefix": "iad190676exd",
      "rackname": "iad190676exd-atpmg-scaqax05XXX-clu01",
      "cell_count": 4
    }
  }

class ebTestResourceConnector(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestResourceConnector, self).setUpClass(aGenerateDatabase = True, aUseOeda = True)
        self.mGetClubox(self).mSetUt(True)
        warnings.filterwarnings("ignore")

    def test_mObtainRealm(self):

        ebLogInfo("Running unit test on mObtainRealm")
        _json_object = json.dumps(CONFIG_REALM1)
        _config_bundle = copy.deepcopy(json.loads(_json_object))
        with patch ('exabox.exaoci.connectors.ResourceConnector.load_config_bundle', return_value=_config_bundle):
            _connector = ResourceConnector()
            _realm = _connector.mObtainRealm()
            self.assertEqual(_realm, "r1")

        _json_object = json.dumps(CONFIG_REALM2)
        _config_bundle = copy.deepcopy(json.loads(_json_object))
        with patch ('exabox.exaoci.connectors.ResourceConnector.load_config_bundle', return_value=_config_bundle):
            _connector = ResourceConnector()
            _realm = _connector.mObtainRealm()
            self.assertNotEqual(_realm, "r1")

        _json_object = json.dumps(CONFIG_REALM3)
        _config_bundle = copy.deepcopy(json.loads(_json_object))
        with patch ('exabox.exaoci.connectors.ResourceConnector.load_config_bundle', return_value=_config_bundle):
            _connector = ResourceConnector()
            _realm = _connector.mObtainRealm()
            self.assertEqual(_realm, "r1")

    def test_mObtainRegion(self):

        ebLogInfo("Running unit test on mObtainRegion")
        _json_object = json.dumps(CONFIG_BUNDLE)
        _config_bundle = copy.deepcopy(json.loads(_json_object))
        with patch ('exabox.exaoci.connectors.ResourceConnector.load_config_bundle', return_value=_config_bundle):
            _connector = ResourceConnector()
            _region = _connector.mObtainRegion()
            self.assertEqual(_region, "r1")

        _json_object = json.dumps(CONFIG_BUNDLE1)
        _config_bundle = copy.deepcopy(json.loads(_json_object))
        with patch ('exabox.exaoci.connectors.ResourceConnector.load_config_bundle', return_value=_config_bundle):
            _connector = ResourceConnector()
            _region = _connector.mObtainRegion()
            self.assertEqual(_region, "r1")

        try:
            _json_object = json.dumps(CONFIG_REALM4)
            _config_bundle = copy.deepcopy(json.loads(_json_object))
            with patch ('exabox.exaoci.connectors.ResourceConnector.load_config_bundle', return_value=_config_bundle):
                _connector = ResourceConnector()
                _connector.mObtainRegion()
        except Exception as e:
            ebLogInfo(f'Error in fetching region from exaccInfrastructureOcid:')

        _json_object = json.dumps(CONFIG_BUNDLE2)
        _config_bundle = copy.deepcopy(json.loads(_json_object))
        with patch ('exabox.exaoci.connectors.ResourceConnector.load_config_bundle', return_value=_config_bundle):
            _connector = ResourceConnector()
            _region = _connector.mObtainRegion()
            self.assertEqual(_region, "sea")

    def test_mObtainDnsSuffix(self):

        ebLogInfo("Running unit test on mObtainRegion")
        _json_object = json.dumps(CONFIG_BUNDLE)
        _config_bundle = copy.deepcopy(json.loads(_json_object))
        with patch ('exabox.exaoci.connectors.ResourceConnector.load_config_bundle', return_value=_config_bundle):
            _connector = ResourceConnector()
            _dns_suffix = _connector.mObtainDnsSuffix()
            self.assertEqual(_dns_suffix, "r1.oracleiaas.com")

        _json_object = json.dumps(CONFIG_BUNDLE2)
        _config_bundle = copy.deepcopy(json.loads(_json_object))
        with patch ('exabox.exaoci.connectors.ResourceConnector.load_config_bundle', return_value=_config_bundle):
            _connector = ResourceConnector()
            _dns_suffix = _connector.mObtainDnsSuffix()
            self.assertEqual(_dns_suffix, "sea.oci.oraclecloud.com")

        _json_object = json.dumps(CONFIG_REALM5)
        _config_bundle = copy.deepcopy(json.loads(_json_object))
        with patch ('exabox.exaoci.connectors.ResourceConnector.load_config_bundle', return_value=_config_bundle):
            _connector = ResourceConnector()
            _dns_suffix = _connector.mObtainDnsSuffix()
            self.assertEqual(_dns_suffix, "sea.oraclegovcloud.uk")

    def test_mObtainOxpaFile(self):

        ebLogInfo("Running unit test on mObtainOxpaFile")
        _json_object = json.dumps(CONFIG_BUNDLE)
        _config_bundle = copy.deepcopy(json.loads(_json_object))
        try:
            with patch ('exabox.exaoci.connectors.ResourceConnector.load_config_bundle', return_value=_config_bundle):
                _connector = ResourceConnector()
                _connector.mObtainOxpaFile()
        except Exception as e:
            ebLogInfo(f'Unable to find OXPA file')

    def test_mObtainOcpsSetupFile(self):

        ebLogInfo("Running unit test on mObtainOxpaFile")
        _json_object = json.dumps(CONFIG_BUNDLE)
        _config_bundle = copy.deepcopy(json.loads(_json_object))
        try:
            with patch ('exabox.exaoci.connectors.ResourceConnector.load_config_bundle', return_value=_config_bundle):
                _connector = ResourceConnector()
                _connector.mObtainOcpsSetupFile()
        except Exception as e:
            ebLogInfo(f'Unable to find OCPS Setup file')

    def test_mGetAuthPrinicipalToken(self):
        ebLogInfo("Running unit test on get_auth_principal_token")
        _json_object = json.dumps(CONFIG_BUNDLE)
        _config_bundle = copy.deepcopy(json.loads(_json_object))

        _oxpa_object = json.dumps(OXPA_INPUT)
        _oxpa_file = NamedTemporaryFile(mode='w+', suffix=".json") 
        _oxpa_file.write(_oxpa_object)
        _oxpa_file.seek(0)

        _ocps_object = json.dumps(OCPS_SETUP)
        _ocps_file = NamedTemporaryFile(mode='w+', suffix=".json") 
        _ocps_file.write(_ocps_object)
        _ocps_file.seek(0)

        with patch ('exabox.exaoci.connectors.ResourceConnector.load_config_bundle', return_value=_config_bundle),\
             patch ('exabox.exaoci.connectors.ResourceConnector.get_resource_principals_signer'),\
             patch ('exabox.exaoci.connectors.ResourceConnector.ResourceConnector.mObtainOxpaFile', return_value=_oxpa_file.name), \
             patch ('exabox.exaoci.connectors.ResourceConnector.ResourceConnector.mGetRPKey', return_value=""), \
             patch ('exabox.exaoci.connectors.ResourceConnector.ResourceConnector.mObtainOcpsSetupFile', return_value=_ocps_file.name):
            _connector = ResourceConnector()
            _signer = _connector.get_auth_principal_token()
            _type = _connector.get_connector_type()
            self.assertEqual(_type, "ResourceConnector")
            _config = _connector.get_oci_config()

        with patch ('exabox.exaoci.connectors.ResourceConnector.load_config_bundle', return_value=_config_bundle),\
             patch ('exabox.exaoci.connectors.ResourceConnector.get_resource_principals_signer'),\
             patch ('exabox.exaoci.connectors.ResourceConnector.ResourceConnector.mObtainOxpaFile', return_value=_oxpa_file.name), \
             patch ('exabox.exaoci.connectors.ResourceConnector.ResourceConnector.mObtainOcpsSetupFile', return_value=_ocps_file.name):
            try:
                _connector = ResourceConnector()
                _connector.mGetRPKey()
            except Exception as e:
                ebLogInfo(f'Unable to find Resource principal Key')


    def test_mGetRPAuthEnv_proxy_variants(self):

        ebLogInfo("Running combined test for mGetRPAuthEnv with proxy variants")

        for proxy_value, expected_proxy_env in [
            ("http://www-proxy-hqdc.us.oracle.com:80", "http://www-proxy-hqdc.us.oracle.com:80"),  # Positive
            (None, None),                                                                          # Null proxy
            ("null", None),                                                                        # String "null"
            ("none", None),                                                                        # String "none"
            (1234, None),                                                                          # Invalid type
        ]:
            with self.subTest(proxy_value=proxy_value):
                _oxpa_object = json.dumps(OXPA_INPUT)
                _ocps_object = json.dumps({"proxy": proxy_value})

                _oxpa_file = NamedTemporaryFile(mode='w+', suffix=".json")
                _oxpa_file.write(_oxpa_object)
                _oxpa_file.seek(0)

                _ocps_file = NamedTemporaryFile(mode='w+', suffix=".json")
                _ocps_file.write(_ocps_object)
                _ocps_file.seek(0)

                with patch('exabox.exaoci.connectors.ResourceConnector.load_config_bundle', return_value=CONFIG_BUNDLE), \
                     patch('exabox.exaoci.connectors.ResourceConnector.get_resource_principals_signer'), \
                     patch('exabox.exaoci.connectors.ResourceConnector.ResourceConnector.mObtainOxpaFile', return_value=_oxpa_file.name), \
                     patch('exabox.exaoci.connectors.ResourceConnector.ResourceConnector.mObtainOcpsSetupFile', return_value=_ocps_file.name), \
                     patch('exabox.exaoci.connectors.ResourceConnector.ResourceConnector.mGetRPKey', return_value="fake-key"):

                    _connector = ResourceConnector()
                    _connector.mGetRPAuthEnv()

                    if expected_proxy_env:
                        self.assertEqual(os.environ.get("HTTPS_PROXY"), expected_proxy_env)
                    else:
                        self.assertTrue(
                            "HTTPS_PROXY" not in os.environ or
                            os.environ.get("HTTPS_PROXY") in ["null", "none", "", None]
                        )

                # Always clean up the env variable after subTest
                if "HTTPS_PROXY" in os.environ:
                    del os.environ["HTTPS_PROXY"]

    def test_mSetEndpoint_r1_object_storage_template(self):
        # Auto-generated test for mSetEndpoint
        connector = ResourceConnector.__new__(ResourceConnector)
        connector._ResourceConnector__region = "r1"
        connector._ResourceConnector__realm = "r1"
        connector._ResourceConnector__config_bundle = {"databaseUrl": None}

        with patch('exabox.exaoci.connectors.ResourceConnector.regions.endpoint_for', return_value="endpoint-r1") as mocked_endpoint:
            endpoint = connector.mSetEndpoint("object_storage")

        mocked_endpoint.assert_called_once_with(
            "object_storage",
            service_endpoint_template="https://objectstorage.r1.oracleiaas.com",
            region="r1",
            endpoint=None,
            endpoint_service_name="object_storage"
        )
        self.assertEqual(endpoint, "endpoint-r1")

    def test_mSetEndpoint_database_url_variants(self):
        # Auto-generated test for mSetEndpoint
        scenarios = [
            ("prod-db.example.com", "base-db-endpoint"),
            ("preprod-db.example.com", "https://preprod-db.example.com"),
            ("https://preprod-db.example.com", "https://preprod-db.example.com"),
            (None, "base-db-endpoint"),
        ]

        for database_url, expected_endpoint in scenarios:
            with self.subTest(database_url=database_url):
                connector = ResourceConnector.__new__(ResourceConnector)
                connector._ResourceConnector__region = "eu-zurich-1"
                connector._ResourceConnector__realm = "oc1"
                connector._ResourceConnector__config_bundle = {"databaseUrl": database_url}

                with patch('exabox.exaoci.connectors.ResourceConnector.regions.endpoint_for', return_value="base-db-endpoint") as mocked_endpoint:
                    endpoint = connector.mSetEndpoint("database")

                self.assertEqual(endpoint, expected_endpoint)
                args, kwargs = mocked_endpoint.call_args
                self.assertEqual(args[0], "database")
                self.assertIsNone(kwargs["service_endpoint_template"])
                self.assertEqual(kwargs["region"], "eu-zurich-1")

    def test_get_auth_principal_token_raises_on_oci_http_error(self):
        # Auto-generated test for get_auth_principal_token
        connector = ResourceConnector.__new__(ResourceConnector)
        connector._ResourceConnector__retries = 3

        with patch.object(ResourceConnector, "mGetRPAuthEnv", side_effect=OCIHTTPError("http failure")):
            with self.assertRaises(OCIHTTPError):
                connector.get_auth_principal_token()

    def test_get_auth_principal_token_exhausts_retries(self):
        # Auto-generated test for get_auth_principal_token
        connector = ResourceConnector.__new__(ResourceConnector)
        connector._ResourceConnector__retries = 2

        with patch.object(ResourceConnector, "mGetRPAuthEnv", side_effect=Exception("auth failure")) as mocked_env, \
             patch('exabox.exaoci.connectors.ResourceConnector.sleep', return_value=None) as mocked_sleep:
            with self.assertRaises(ExacloudRuntimeError) as ctx:
                connector.get_auth_principal_token()

        self.assertEqual(mocked_env.call_count, 2)
        self.assertEqual(mocked_sleep.call_count, 2)
        self.assertIn("Please retry operation", str(ctx.exception))
        self.assertIsInstance(ctx.exception.__cause__, Exception)

    def test_mObtainRealm_branches(self):
        # Auto-generated test for mObtainRealm
        connector = ResourceConnector.__new__(ResourceConnector)

        connector._ResourceConnector__config_bundle = {"realmName": "region1"}
        self.assertEqual(connector.mObtainRealm(), "r1")

        connector._ResourceConnector__config_bundle = {"realmName": "oc4"}
        self.assertEqual(connector.mObtainRealm(), "oc4")

        connector._ResourceConnector__config_bundle = {
            "exaccInfrastructureOcid": "ocid1.exadatainfrastructure.region1.sea.example"
        }
        self.assertEqual(connector.mObtainRealm(), "r1")

        connector._ResourceConnector__config_bundle = {
            "exaccInfrastructureOcid": "ocid1.exadatainfrastructure.oc3.eu-frankfurt-1"
        }
        self.assertEqual(connector.mObtainRealm(), "oc3")

    def test_mObtainRegion_variants(self):
        # Auto-generated test for mObtainRegion
        connector = ResourceConnector.__new__(ResourceConnector)

        connector._ResourceConnector__realm = "r1"
        connector._ResourceConnector__config_bundle = {}
        self.assertEqual(connector.mObtainRegion(), "r1")

        connector._ResourceConnector__realm = "oc1"
        connector._ResourceConnector__config_bundle = {
            "exaccInfrastructureOcid": "ocid1.exadatainfrastructure.oc1.eu-zurich-1.extra"
        }
        with patch('exabox.exaoci.connectors.ResourceConnector.regions.get_region_from_short_name', return_value="eu-zurich-1") as mock_region:
            self.assertEqual(connector.mObtainRegion(), "eu-zurich-1")
            mock_region.assert_called_once_with("eu-zurich-1")

        connector._ResourceConnector__realm = "oc1"
        connector._ResourceConnector__config_bundle = {
            "exaccInfrastructureOcid": "ocid1.exadatainfrastructure.oc1"
        }
        with patch('exabox.exaoci.connectors.ResourceConnector.ebLogError') as mock_log:
            with self.assertRaises(ExacloudRuntimeError):
                connector.mObtainRegion()
            mock_log.assert_called_once()

    def test_mObtainDnsSuffix_fallbacks(self):
        # Auto-generated test for mObtainDnsSuffix
        connector = ResourceConnector.__new__(ResourceConnector)

        connector._ResourceConnector__config_bundle = {"dnsSuffix": "custom.domain"}
        self.assertEqual(connector.mObtainDnsSuffix(), "custom.domain")

        connector._ResourceConnector__config_bundle = {}
        connector._ResourceConnector__realm = "r1"
        self.assertEqual(connector.mObtainDnsSuffix(), "r1.oracleiaas.com")

        connector._ResourceConnector__realm = "oc4"
        connector._ResourceConnector__region = "uk-london-1"
        self.assertEqual(connector.mObtainDnsSuffix(), "uk-london-1.oraclegovcloud.uk")

        connector._ResourceConnector__realm = "oc8"
        connector._ResourceConnector__region = "us-ashburn-1"
        self.assertEqual(connector.mObtainDnsSuffix(), "us-ashburn-1.oci.oraclecloud.com")

    def test_mGetConfigOption_uses_exabox_conf(self):
        # Auto-generated test for mGetConfigOption
        connector = ResourceConnector.__new__(ResourceConnector)
        connector._ResourceConnector__basepath = "/base/path"

        with patch('exabox.exaoci.connectors.ResourceConnector.get_value_from_exabox_config', return_value="option-value") as mock_get:
            result = connector.mGetConfigOption("resource_principals_version")

        self.assertEqual(result, "option-value")
        mock_get.assert_called_once_with("resource_principals_version", "/base/path/config/exabox.conf")

    def test_mGetRPKey_reads_from_configured_path(self):
        # Auto-generated test for mGetRPKey
        connector = ResourceConnector.__new__(ResourceConnector)

        with patch.object(ResourceConnector, "mGetConfigOption", return_value="/tmp/key.pem") as mock_option, \
             patch('exabox.exaoci.connectors.ResourceConnector.read_file_into_string', return_value="key-data") as mock_read:
            result = connector.mGetRPKey()

        self.assertEqual(result, "key-data")
        mock_option.assert_called_once_with("resource_principals_key")
        mock_read.assert_called_once_with("/tmp/key.pem")

    def test_mGetRPAuthEnv_populates_environment_and_config(self):
        # Auto-generated test for mGetRPAuthEnv
        connector = ResourceConnector.__new__(ResourceConnector)
        connector._ResourceConnector__basepath = "/ade/view"
        connector._ResourceConnector__realm = "r1"
        connector._ResourceConnector__region = "us-phoenix-1"
        connector._ResourceConnector__casper_endpoint = "casper-endpoint"
        connector._ResourceConnector__dbaas_endpoint = "dbaas-endpoint"
        connector._ResourceConnector__auth_endpoint = "auth-endpoint"
        connector._ResourceConnector__config_bundle = {}

        oxpa_payload = {"OciExaCapacityParam": {"tenantOcid": "tenant-ocid", "exaOcid": "exa-ocid"}}
        ocps_payload = {"proxy": " http://proxy.example.com "}

        with patch('exabox.exaoci.connectors.ResourceConnector.read_json_into_string', side_effect=[oxpa_payload, ocps_payload]), \
             patch.object(ResourceConnector, "mObtainOxpaFile", return_value="/tmp/oxpa.json"), \
             patch.object(ResourceConnector, "mObtainOcpsSetupFile", return_value="/tmp/ocps.json"), \
             patch.object(ResourceConnector, "mGetRPKey", return_value="key-data"), \
             patch.object(ResourceConnector, "mGetConfigOption", return_value="rp-version"), \
             patch('exabox.exaoci.connectors.ResourceConnector.get_resource_principals_signer', return_value="signer"), \
             patch.dict(os.environ, {}, clear=True):
            signer = connector.mGetRPAuthEnv()
            self.assertEqual(signer, "signer")
            self.assertEqual(os.environ["HTTPS_PROXY"], "http://proxy.example.com")
            self.assertEqual(os.environ["OCI_RESOURCE_PRINCIPAL_VERSION"], "rp-version")
            self.assertEqual(os.environ["OCI_RESOURCE_PRINCIPAL_RPT_ENDPOINT"], "dbaas-endpoint")
            self.assertEqual(os.environ["OCI_RESOURCE_PRINCIPAL_RPST_ENDPOINT"], "auth-endpoint")
            self.assertEqual(os.environ["OCI_RESOURCE_PRINCIPAL_RESOURCE_ID"], "exa-ocid")
            self.assertEqual(os.environ["OCI_RESOURCE_PRINCIPAL_TENANCY_ID"], "tenant-ocid")
            self.assertEqual(os.environ["OCI_RESOURCE_PRINCIPAL_PRIVATE_PEM"], "key-data")
            self.assertEqual(os.environ["OCI_RESOURCE_PRINCIPAL_PRIVATE_PEM_PASSPHRASE"], "")
            self.assertEqual(os.environ["OCI_RESOURCE_PRINCIPAL_REGION"], "us-phoenix-1")
            self.assertEqual(os.environ["REQUESTS_CA_BUNDLE"], "/ade/view/exabox/kms/combined_r1.crt")

        self.assertEqual(connector.get_oci_config(), {
            "tenancy": "tenant-ocid",
            "casper_endpoint": "casper-endpoint",
            "ca_bundle_path": "/ade/view/exabox/kms/combined_r1.crt",
            "realm": "r1"
        })

    def test_mGetRPAuthEnv_skips_proxy_when_value_not_string(self):
        # Auto-generated test for mGetRPAuthEnv
        connector = ResourceConnector.__new__(ResourceConnector)
        connector._ResourceConnector__basepath = "/ade/view"
        connector._ResourceConnector__realm = "oc1"
        connector._ResourceConnector__region = "eu-frankfurt-1"
        connector._ResourceConnector__casper_endpoint = "casper-endpoint"
        connector._ResourceConnector__dbaas_endpoint = "dbaas-endpoint"
        connector._ResourceConnector__auth_endpoint = "auth-endpoint"
        connector._ResourceConnector__config_bundle = {}

        oxpa_payload = {"OciExaCapacityParam": {"tenantOcid": "tenant-ocid", "exaOcid": "exa-ocid"}}
        ocps_payload = {"proxy": 12345}

        with patch('exabox.exaoci.connectors.ResourceConnector.read_json_into_string', side_effect=[oxpa_payload, ocps_payload]), \
             patch.object(ResourceConnector, "mObtainOxpaFile", return_value="/tmp/oxpa.json"), \
             patch.object(ResourceConnector, "mObtainOcpsSetupFile", return_value="/tmp/ocps.json"), \
             patch.object(ResourceConnector, "mGetRPKey", return_value="key-data"), \
             patch.object(ResourceConnector, "mGetConfigOption", return_value="rp-version"), \
             patch('exabox.exaoci.connectors.ResourceConnector.get_resource_principals_signer', return_value="signer"), \
             patch.dict(os.environ, {}, clear=True):
            connector.mGetRPAuthEnv()
            self.assertNotIn("HTTPS_PROXY", os.environ)
            config = connector.get_oci_config()

        self.assertEqual(config["realm"], "oc1")

    def test_mGetRPAuthEnv_ignores_case_insensitive_null_values(self):
        # Auto-generated test for mGetRPAuthEnv
        proxy_variants = ["  NULL  ", "  NONE  "]

        for proxy_value in proxy_variants:
            with self.subTest(proxy_value=proxy_value):
                connector = ResourceConnector.__new__(ResourceConnector)
                connector._ResourceConnector__basepath = "/ade/view"
                connector._ResourceConnector__realm = "r1"
                connector._ResourceConnector__region = "us-phoenix-1"
                connector._ResourceConnector__casper_endpoint = "casper-endpoint"
                connector._ResourceConnector__dbaas_endpoint = "dbaas-endpoint"
                connector._ResourceConnector__auth_endpoint = "auth-endpoint"
                connector._ResourceConnector__config_bundle = {}

                oxpa_payload = {"OciExaCapacityParam": {"tenantOcid": "tenant-ocid", "exaOcid": "exa-ocid"}}
                ocps_payload = {"proxy": proxy_value}

                with patch('exabox.exaoci.connectors.ResourceConnector.read_json_into_string', side_effect=[oxpa_payload, ocps_payload]), \
                     patch.object(ResourceConnector, "mObtainOxpaFile", return_value="/tmp/oxpa.json"), \
                     patch.object(ResourceConnector, "mObtainOcpsSetupFile", return_value="/tmp/ocps.json"), \
                     patch.object(ResourceConnector, "mGetRPKey", return_value="key-data"), \
                     patch.object(ResourceConnector, "mGetConfigOption", return_value="rp-version"), \
                     patch('exabox.exaoci.connectors.ResourceConnector.get_resource_principals_signer', return_value="signer"), \
                     patch.dict(os.environ, {}, clear=True):
                    signer = connector.mGetRPAuthEnv()
                    self.assertEqual(signer, "signer")
                    self.assertNotIn("HTTPS_PROXY", os.environ)
                    self.assertEqual(os.environ["REQUESTS_CA_BUNDLE"], "/ade/view/exabox/kms/combined_r1.crt")
                    config = connector.get_oci_config()

                self.assertEqual(config["realm"], "r1")

    def test_mObtainOxpaFile_success_and_failure(self):
        # Auto-generated test for mObtainOxpaFile
        connector = ResourceConnector.__new__(ResourceConnector)

        with patch('exabox.exaoci.connectors.ResourceConnector.glob.glob', return_value=["/tmp/file.oxpaInput.json"]):
            self.assertEqual(connector.mObtainOxpaFile(), "/tmp/file.oxpaInput.json")

        with patch('exabox.exaoci.connectors.ResourceConnector.glob.glob', return_value=[]), \
             patch('exabox.exaoci.connectors.ResourceConnector.ebLogError') as mock_log:
            with self.assertRaises(ExacloudRuntimeError):
                connector.mObtainOxpaFile()
            mock_log.assert_called_once()

    def test_mObtainOcpsSetupFile_success_and_failure(self):
        # Auto-generated test for mObtainOcpsSetupFile
        connector = ResourceConnector.__new__(ResourceConnector)

        with patch('exabox.exaoci.connectors.ResourceConnector.glob.glob', return_value=["/tmp/file.ocpsSetup.json"]):
            self.assertEqual(connector.mObtainOcpsSetupFile(), "/tmp/file.ocpsSetup.json")

        with patch('exabox.exaoci.connectors.ResourceConnector.glob.glob', return_value=[]), \
             patch('exabox.exaoci.connectors.ResourceConnector.ebLogError') as mock_log:
            with self.assertRaises(ExacloudRuntimeError):
                connector.mObtainOcpsSetupFile()
            mock_log.assert_called_once()

    def test_get_auth_principal_token_success(self):
        # Auto-generated test for get_auth_principal_token
        connector = ResourceConnector.__new__(ResourceConnector)
        connector._ResourceConnector__retries = 3

        with patch.object(ResourceConnector, "mGetRPAuthEnv", return_value="token") as mock_env:
            token = connector.get_auth_principal_token()

        self.assertEqual(token, "token")
        mock_env.assert_called_once()

    def test_get_auth_principal_token_succeeds_after_retry(self):
        # Auto-generated test for get_auth_principal_token
        connector = ResourceConnector.__new__(ResourceConnector)
        connector._ResourceConnector__retries = 3

        with patch.object(ResourceConnector, "mGetRPAuthEnv", side_effect=[Exception("first failure"), "token"]) as mock_env, \
             patch('exabox.exaoci.connectors.ResourceConnector.sleep', return_value=None) as mock_sleep, \
             patch('exabox.exaoci.connectors.ResourceConnector.ebLogTrace') as mock_trace:
            token = connector.get_auth_principal_token()

        self.assertEqual(token, "token")
        self.assertEqual(mock_env.call_count, 2)
        mock_sleep.assert_called_once_with(1)
        mock_trace.assert_called_once()

    def test_autogen_mObtainRealm_handles_realmName(self):
        # Auto-generated test for mObtainRealm
        connector = ResourceConnector.__new__(ResourceConnector)
        connector._ResourceConnector__config_bundle = {"realmName": "region1"}
        self.assertEqual(connector.mObtainRealm(), "r1")

        connector._ResourceConnector__config_bundle = {"realmName": "oc4"}
        self.assertEqual(connector.mObtainRealm(), "oc4")

    def test_autogen_mObtainRealm_extracts_from_ocid(self):
        # Auto-generated test for mObtainRealm
        connector = ResourceConnector.__new__(ResourceConnector)

        connector._ResourceConnector__config_bundle = {
            "exaccInfrastructureOcid": "ocid1.exadatainfrastructure.region1.sea.instance"
        }
        self.assertEqual(connector.mObtainRealm(), "r1")

        connector._ResourceConnector__config_bundle = {
            "exaccInfrastructureOcid": "ocid1.exadatainfrastructure.oc3.eu-frankfurt-1"
        }
        self.assertEqual(connector.mObtainRealm(), "oc3")

    def test_autogen_mObtainRegion_paths(self):
        # Auto-generated test for mObtainRegion
        connector = ResourceConnector.__new__(ResourceConnector)
        connector._ResourceConnector__config_bundle = {}

        connector._ResourceConnector__realm = "r1"
        self.assertEqual(connector.mObtainRegion(), "r1")

        connector._ResourceConnector__realm = "oc1"
        connector._ResourceConnector__config_bundle = {
            "exaccInfrastructureOcid": "ocid1.exadatainfrastructure.oc1.eu-zurich-1.extra"
        }
        with patch('exabox.exaoci.connectors.ResourceConnector.regions.get_region_from_short_name',
                   return_value="eu-zurich-1") as mocked_region:
            self.assertEqual(connector.mObtainRegion(), "eu-zurich-1")
            mocked_region.assert_called_once_with("eu-zurich-1")

        connector._ResourceConnector__config_bundle = {
            "exaccInfrastructureOcid": "ocid1.exadatainfrastructure.oc1"
        }
        with patch('exabox.exaoci.connectors.ResourceConnector.ebLogError') as mocked_log:
            with self.assertRaises(ExacloudRuntimeError):
                connector.mObtainRegion()
            mocked_log.assert_called_once()

    def test_autogen_mObtainDnsSuffix_modes(self):
        # Auto-generated test for mObtainDnsSuffix
        connector = ResourceConnector.__new__(ResourceConnector)

        connector._ResourceConnector__config_bundle = {"dnsSuffix": "custom.domain"}
        self.assertEqual(connector.mObtainDnsSuffix(), "custom.domain")

        connector._ResourceConnector__config_bundle = {}
        connector._ResourceConnector__realm = "r1"
        self.assertEqual(connector.mObtainDnsSuffix(), "r1.oracleiaas.com")

        connector._ResourceConnector__realm = "oc4"
        connector._ResourceConnector__region = "uk-london-1"
        self.assertEqual(connector.mObtainDnsSuffix(), "uk-london-1.oraclegovcloud.uk")

        connector._ResourceConnector__realm = "oc3"
        connector._ResourceConnector__region = "us-ashburn-1"
        self.assertEqual(connector.mObtainDnsSuffix(), "us-ashburn-1.oci.oraclecloud.com")

    def test_autogen_mSetEndpoint_non_r1_preprod(self):
        # Auto-generated test for mSetEndpoint
        connector = ResourceConnector.__new__(ResourceConnector)
        connector._ResourceConnector__region = "eu-zurich-1"
        connector._ResourceConnector__config_bundle = {"databaseUrl": "preprod-db.example.com"}

        with patch('exabox.exaoci.connectors.ResourceConnector.regions.endpoint_for',
                   side_effect=["base-first", "base-second"]) as mocked_endpoint:
            endpoint = connector.mSetEndpoint("database")
            self.assertEqual(endpoint, "https://preprod-db.example.com")

            connector._ResourceConnector__config_bundle = {"databaseUrl": "https://preprod-db.example.com"}
            endpoint_https = connector.mSetEndpoint("database")
            self.assertEqual(endpoint_https, "https://preprod-db.example.com")

        self.assertEqual(mocked_endpoint.call_count, 2)

    def test_autogen_mGetRPAuthEnv_configures_environment(self):
        # Auto-generated test for mGetRPAuthEnv
        connector = ResourceConnector.__new__(ResourceConnector)
        connector._ResourceConnector__basepath = "/ade/view"
        connector._ResourceConnector__realm = "r1"
        connector._ResourceConnector__region = "us-phoenix-1"
        connector._ResourceConnector__casper_endpoint = "casper"
        connector._ResourceConnector__dbaas_endpoint = "dbaas"
        connector._ResourceConnector__auth_endpoint = "auth"
        connector._ResourceConnector__config_bundle = {}

        oxpa_payload = {"OciExaCapacityParam": {"tenantOcid": "tenant-ocid", "exaOcid": "exa-ocid"}}
        ocps_payload = {"proxy": " http://proxy.example.com "}

        with patch('exabox.exaoci.connectors.ResourceConnector.read_json_into_string',
                   side_effect=[oxpa_payload, ocps_payload]), \
             patch.object(ResourceConnector, "mObtainOxpaFile", return_value="/tmp/oxpa.json"), \
             patch.object(ResourceConnector, "mObtainOcpsSetupFile", return_value="/tmp/ocps.json"), \
             patch.object(ResourceConnector, "mGetRPKey", return_value="key-data"), \
             patch.object(ResourceConnector, "mGetConfigOption", return_value="2.1"), \
             patch('exabox.exaoci.connectors.ResourceConnector.get_resource_principals_signer',
                   return_value="signer"), \
             patch('exabox.exaoci.connectors.ResourceConnector.ebLogInfo'), \
             patch.dict(os.environ, {}, clear=True):
            signer = connector.mGetRPAuthEnv()
            self.assertEqual(signer, "signer")
            self.assertEqual(os.environ["HTTPS_PROXY"], "http://proxy.example.com")
            self.assertEqual(os.environ["OCI_RESOURCE_PRINCIPAL_VERSION"], "2.1")
            self.assertEqual(os.environ["OCI_RESOURCE_PRINCIPAL_RPT_ENDPOINT"], "dbaas")
            self.assertEqual(os.environ["OCI_RESOURCE_PRINCIPAL_RPST_ENDPOINT"], "auth")
            self.assertEqual(os.environ["OCI_RESOURCE_PRINCIPAL_RESOURCE_ID"], "exa-ocid")
            self.assertEqual(os.environ["OCI_RESOURCE_PRINCIPAL_TENANCY_ID"], "tenant-ocid")
            self.assertEqual(os.environ["REQUESTS_CA_BUNDLE"], "/ade/view/exabox/kms/combined_r1.crt")

        self.assertEqual(connector.get_oci_config(), {
            "tenancy": "tenant-ocid",
            "casper_endpoint": "casper",
            "ca_bundle_path": "/ade/view/exabox/kms/combined_r1.crt",
            "realm": "r1"
        })
        self.assertEqual(connector.get_connector_type(), "ResourceConnector")

    def test_autogen_mGetRPAuthEnv_invalid_proxy_cases(self):
        # Auto-generated test for mGetRPAuthEnv
        connector = ResourceConnector.__new__(ResourceConnector)
        connector._ResourceConnector__basepath = "/ade/view"
        connector._ResourceConnector__realm = "oc1"
        connector._ResourceConnector__region = "eu-frankfurt-1"
        connector._ResourceConnector__casper_endpoint = "casper"
        connector._ResourceConnector__dbaas_endpoint = "dbaas"
        connector._ResourceConnector__auth_endpoint = "auth"
        connector._ResourceConnector__config_bundle = {}

        oxpa_payload = {"OciExaCapacityParam": {"tenantOcid": "tenant", "exaOcid": "exa"}}

        with patch('exabox.exaoci.connectors.ResourceConnector.read_json_into_string',
                   side_effect=[oxpa_payload, {"proxy": 123}, oxpa_payload, {"proxy": "null"}]), \
             patch.object(ResourceConnector, "mObtainOxpaFile", return_value="/tmp/oxpa.json"), \
             patch.object(ResourceConnector, "mObtainOcpsSetupFile", return_value="/tmp/ocps.json"), \
             patch.object(ResourceConnector, "mGetRPKey", return_value="key"), \
             patch.object(ResourceConnector, "mGetConfigOption", return_value="2.2"), \
             patch('exabox.exaoci.connectors.ResourceConnector.get_resource_principals_signer',
                   return_value="signer"), \
             patch.dict(os.environ, {}, clear=True):
            connector.mGetRPAuthEnv()
            self.assertNotIn("HTTPS_PROXY", os.environ)

            connector.mGetRPAuthEnv()
            self.assertNotIn("HTTPS_PROXY", os.environ)

    def test_autogen_get_auth_principal_token_error_paths(self):
        # Auto-generated test for get_auth_principal_token
        connector = ResourceConnector.__new__(ResourceConnector)
        connector._ResourceConnector__retries = 2

        with patch.object(ResourceConnector, "mGetRPAuthEnv", side_effect=OCIHTTPError("http failure")):
            with self.assertRaises(OCIHTTPError):
                connector.get_auth_principal_token()

        connector._ResourceConnector__retries = 3
        with patch.object(ResourceConnector, "mGetRPAuthEnv", side_effect=[Exception("boom")] * 3), \
             patch('exabox.exaoci.connectors.ResourceConnector.sleep', return_value=None) as mocked_sleep, \
             patch('exabox.exaoci.connectors.ResourceConnector.ebLogTrace') as mocked_trace, \
             patch('exabox.exaoci.connectors.ResourceConnector.ebLogError') as mocked_error:
            with self.assertRaises(ExacloudRuntimeError):
                connector.get_auth_principal_token()

        self.assertEqual(mocked_sleep.call_count, 3)
        self.assertEqual(mocked_trace.call_count, 3)
        self.assertEqual(mocked_error.call_count, 1)

    def test_mSetEndpoint_r1_non_object_storage(self):
        # Auto-generated test for mSetEndpoint
        connector = ResourceConnector.__new__(ResourceConnector)
        connector._ResourceConnector__region = "r1"
        connector._ResourceConnector__realm = "r1"
        connector._ResourceConnector__config_bundle = {"databaseUrl": None}

        with patch('exabox.exaoci.connectors.ResourceConnector.regions.endpoint_for', return_value="endpoint-r1-auth") as mocked_endpoint:
            endpoint = connector.mSetEndpoint("auth")

        mocked_endpoint.assert_called_once_with(
            "auth",
            service_endpoint_template="https://auth.r1.oracleiaas.com",
            region="r1",
            endpoint=None,
            endpoint_service_name="auth"
        )
        self.assertEqual(endpoint, "endpoint-r1-auth")

    def test_mGetRPAuthEnv_no_requests_ca_bundle_for_non_r1(self):
        # Auto-generated test for mGetRPAuthEnv
        connector = ResourceConnector.__new__(ResourceConnector)
        connector._ResourceConnector__basepath = "/ade/view"
        connector._ResourceConnector__realm = "oc2"
        connector._ResourceConnector__region = "us-ashburn-1"
        connector._ResourceConnector__casper_endpoint = "casper"
        connector._ResourceConnector__dbaas_endpoint = "dbaas"
        connector._ResourceConnector__auth_endpoint = "auth"
        connector._ResourceConnector__config_bundle = {}

        oxpa_payload = {"OciExaCapacityParam": {"tenantOcid": "tenant", "exaOcid": "exa"}}
        ocps_payload = {"proxy": "http://proxy.example.com"}

        with patch('exabox.exaoci.connectors.ResourceConnector.read_json_into_string', side_effect=[oxpa_payload, ocps_payload]), \
             patch.object(ResourceConnector, "mObtainOxpaFile", return_value="/tmp/oxpa.json"), \
             patch.object(ResourceConnector, "mObtainOcpsSetupFile", return_value="/tmp/ocps.json"), \
             patch.object(ResourceConnector, "mGetRPKey", return_value="key-data"), \
             patch.object(ResourceConnector, "mGetConfigOption", return_value="2.0"), \
             patch('exabox.exaoci.connectors.ResourceConnector.get_resource_principals_signer', return_value="signer"), \
             patch.dict(os.environ, {}, clear=True):
            connector.mGetRPAuthEnv()
            self.assertEqual(os.environ["HTTPS_PROXY"], "http://proxy.example.com")
            self.assertNotIn("REQUESTS_CA_BUNDLE", os.environ)

        self.assertEqual(connector.get_oci_config()["realm"], "oc2")


if __name__ == '__main__':
    unittest.main()
