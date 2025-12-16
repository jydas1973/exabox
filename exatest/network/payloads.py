#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/network/payloads.py /main/4 2025/11/03 21:24:24 scoral Exp $
#
# payloads.py
#
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
#
#    NAME
#      payloads.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aararora    08/06/25 - ER 38132942: Single stack support for ipv6
#    aararora    10/01/24 - Bug 37105761: Oedacli command is failing for
#                           elastic_info call in ipv6
#    aararora    05/27/24 - ER 36485120: Payloads used for network tests
#    aararora    05/27/24 - Creation
#
CUSTOM_VIPS_IPv4_PAYLOAD = {
    "customvip": [
        {
            "interfacetype": "client",
            "ip": "10.0.0.5",
            "standby_vnic_mac": "00:09:A9:78:67"
        },
        {
            "interfacetype": "backup",
            "ip": "10.0.0.6",
            "standby_vnic_mac": "00:09:A9:78:68"
        }
    ]
}

CUSTOM_VIPS_IPv6_PAYLOAD = {
    "customvip": [
        {
            "interfacetype": "client",
            "ip": "0.0.0.0",
            "ipv6": "fe80::17ff:fe13:5659",
            "standby_vnic_mac": "00:09:A9:78:67"
        },
        {
            "interfacetype": "backup",
            "ip": "0.0.0.0",
            "ipv6": "fe80::17ff:fe13:5670",
            "standby_vnic_mac": "00:09:A9:78:68"
        }
    ]
}

CUSTOM_VIPS_DUAL_STACK_PAYLOAD = {
    "customvip": [
        {
            "interfacetype": "client",
            "ip": "10.0.0.5",
            "ipv6": "fe80::17ff:fe13:5659",
            "standby_vnic_mac": "00:09:A9:78:67"
        },
        {
            "interfacetype": "backup",
            "ip": "10.0.0.6",
            "ipv6": "fe80::17ff:fe13:5670",
            "standby_vnic_mac": "00:09:A9:78:68"
        }
    ]
}

VIPS_CONFIG_FILE_V4 = {
        "scaqab10adm02vm01":[
            {
                "type": "app_vip",
                "ip": "10.0.0.5",
                "ipv6": "::",
                "interface_type": "client",
                "mac": "00:00:17:01:4C:65",
                "standby_vnic_mac": "00:00:17:01:DC:4A",
                "vlantag": "1",
                "floating": True
            },
            {
                "type": "app_vip",
                "ip": "10.0.0.6",
                "ipv6": "::",
                "interface_type": "backup",
                "mac": "00:00:17:01:56:05",
                "standby_vnic_mac": "00:00:17:01:ED:1F",
                "vlantag": "2",
                "floating": True
            }
        ]
    }

VIPS_CONFIG_FILE_V6 = {
        "scaqab10adm02vm01":[
            {
                "type": "app_vip",
                "ip": "0.0.0.0",
                "ipv6": "fe80::17ff:fe13:5659",
                "interface_type": "client",
                "mac": "00:00:17:01:4C:65",
                "standby_vnic_mac": "00:00:17:01:DC:4A",
                "vlantag": "1",
                "floating": True
            },
            {
                "type": "app_vip",
                "ip": "0.0.0.0",
                "ipv6": "fe80::17ff:fe13:5670",
                "interface_type": "backup",
                "mac": "00:00:17:01:56:05",
                "standby_vnic_mac": "00:00:17:01:ED:1F",
                "vlantag": "2",
                "floating": True
            }
        ]
    }

VIPS_CONFIG_FILE_DUAL_STACK = {
        "scaqab10adm02vm01":[
            {
                "type": "app_vip",
                "ip": "10.0.0.5",
                "ipv6": "fe80::17ff:fe13:5659",
                "interface_type": "client",
                "mac": "00:00:17:01:4C:65",
                "standby_vnic_mac": "00:00:17:01:DC:4A",
                "vlantag": "1",
                "floating": True
            },
            {
                "type": "app_vip",
                "ip": "10.0.0.6",
                "ipv6": "fe80::17ff:fe13:5670",
                "interface_type": "backup",
                "mac": "00:00:17:01:56:05",
                "standby_vnic_mac": "00:00:17:01:ED:1F",
                "vlantag": "2",
                "floating": True
            }
        ]
    }

PAYLOAD_CREATE_SERVICE = {
    "cmd": "createservice",
    "debug": "true",
    "disablepkey": "false",
    "enablegilatest": "true",
    "exaunitid": "242",
    "frompath_cmd": "true",
    "hostname": "iad1zdlraecra3.ecramgmt.adminiad1.oraclevcn.com",
    "jsonconf": {
        "adb_s": "False",
        "bonding_operation": "create-service",
        "customer_network": {
            "network_services": {
                "dns": [
                    "169.254.169.254"
                ],
                "ntp": [
                    "169.254.169.254"
                ]
            },
            "nodes": [
                {
                    "backup": {
                        "dom0_oracle_name": "iad103716exdd011",
                        "domainname": "backupsubnet.devx8melastic.oraclevcn.com",
                        "domu_oracle_name": "iad103716exddu1101",
                        "gateway": "10.0.32.1",
                        "hostname": "c3716n11b1",
                        "hw_node_id": 5,
                        "ip": "10.0.38.38",
                        "mac": "00:00:17:00:11:3F",
                        "netmask": "255.255.224.0",
                        "vlantag": "2"
                    },
                    "client": {
                        "dom0_oracle_name": "iad103716exdd011",
                        "domainname": "clientsubnet.devx8melastic.oraclevcn.com",
                        "domu_oracle_name": "iad103716exddu1101",
                        "gateway": "10.0.0.1",
                        "hostname": "c3716n11c1",
                        "hw_node_id": 5,
                        "ip": "10.0.8.185",
                        "mac": "02:00:17:12:15:D4",
                        "natdomainname": "iad103716exd.adminiad1.oraclevcn.com",
                        "natmask": "255.255.255.128",
                        "netmask": "255.255.224.0",
                        "vlantag": "1"
                    },
                    "fqdn": "iad103716exdd011.iad103716exd.adminiad1.oraclevcn.com",
                    "monitoring": {
                        "bond0": {
                            "cavium_ids": [
                                {
                                    "id": "4.0G2004-GBC000913",
                                    "networkinterface": "eth1"
                                },
                                {
                                    "id": "4.0G2001-GBC001819",
                                    "networkinterface": "eth2"
                                }
                            ],
                            "gateway": "192.168.1.1",
                            "ip": "192.168.1.145",
                            "netmask": "255.255.255.0",
                            "preferred_interface": "eth1",
                            "vlantag": 0
                        }
                    },
                    "vip": {
                        "domainname": "clientsubnet.devx8melastic.oraclevcn.com",
                        "hostname": "c3716n11c1-vip",
                        "ip": "10.0.3.203"
                    }
                },
                {
                    "backup": {
                        "dom0_oracle_name": "iad103716exdd012",
                        "domainname": "backupsubnet.devx8melastic.oraclevcn.com",
                        "domu_oracle_name": "iad103716exddu1201",
                        "gateway": "10.0.32.1",
                        "hostname": "c3716n12b1",
                        "hw_node_id": 5,
                        "ip": "10.0.33.197",
                        "mac": "02:00:17:03:58:72",
                        "netmask": "255.255.224.0",
                        "vlantag": "2"
                    },
                    "client": {
                        "dom0_oracle_name": "iad103716exdd012",
                        "domainname": "clientsubnet.devx8melastic.oraclevcn.com",
                        "domu_oracle_name": "iad103716exddu1201",
                        "gateway": "10.0.0.1",
                        "hostname": "c3716n12c1",
                        "hw_node_id": 5,
                        "ip": "10.0.11.73",
                        "mac": "02:00:17:12:BD:52",
                        "natdomainname": "iad103716exd.adminiad1.oraclevcn.com",
                        "natmask": "255.255.255.128",
                        "netmask": "255.255.224.0",
                        "vlantag": "1"
                    },
                    "fqdn": "iad103716exdd012.iad103716exd.adminiad1.oraclevcn.com",
                    "monitoring": {
                        "bond0": {
                            "cavium_ids": [
                                {
                                    "id": "4.0G2001-GBC001134",
                                    "networkinterface": "eth1"
                                },
                                {
                                    "id": "4.0G1949-GBC000006",
                                    "networkinterface": "eth2"
                                }
                            ],
                            "gateway": "192.168.1.1",
                            "ip": "192.168.1.209",
                            "netmask": "255.255.255.0",
                            "preferred_interface": "eth2",
                            "vlantag": 0
                        }
                    },
                    "vip": {
                        "domainname": "clientsubnet.devx8melastic.oraclevcn.com",
                        "hostname": "c3716n12c1-vip",
                        "ip": "10.0.27.136"
                    }
                }
            ],
            "scan": {
                "hostname": "idc3716-clu01scan",
                "ips": [
                    "10.0.9.124",
                    "10.0.25.120",
                    "10.0.0.121"
                ],
                "port": 1521
            },
            "timezone": "UTC"
        },
        "dbaas_api": {
            "FLAGS": "",
            "action": "set",
            "object": "os",
            "operation": "cloud_properties",
            "outputfile": "/tmp/cloudProperties_2024.05.20.12.50.29",
            "params": {
                "adb_s": {
                    "enabled": "False"
                },
                "atp": {
                    "enabled": "False"
                },
                "cns": {
                    "enabled": "False"
                },
                "common": {
                    "fedramp": "disabled",
                    "fips_compliance": "disabled",
                    "oss_url": "https://swiftobjectstorage.us-ashburn-1.oraclecloud.com",
                    "se_linux": "disabled"
                },
                "diag": {},
                "ords": {
                    "enable": "False"
                }
            }
        },
        "delete_domu_keys": "false",
        "dom0_bonding": "true",
        "eth0_removed": "false",
        "fedramp": "N",
        "filesystems": {
            "mountpoints": {
                "/": "15G",
                "/home": "4G",
                "/tmp": "10G",
                "/u01": "250G",
                "/var": "10G",
                "/var/log": "30G",
                "/var/log/audit": "3G",
                "grid": "50G"
            }
        },
        "grid_version": "19",
        "kvmroce": {
            "ComputeNetmask": "255.255.0.0",
            "StorageNetmask": "255.255.0.0",
            "computeNetwork": {
                "c3716n11c1.clientsubnet.devx8melastic.oraclevcn.com": {
                    "clusterInterconnectIps": [
                        "100.107.0.2",
                        "100.107.0.3"
                    ],
                    "storageIps": [
                        "100.106.64.0",
                        "100.106.64.1"
                    ]
                },
                "c3716n12c1.clientsubnet.devx8melastic.oraclevcn.com": {
                    "clusterInterconnectIps": [
                        "100.107.0.4",
                        "100.107.0.5"
                    ],
                    "storageIps": [
                        "100.106.64.2",
                        "100.106.64.3"
                    ]
                }
            },
            "computeVlanId": "541",
            "storageNetwork": {
                "iad103712exdcl01.iad103712exd.adminiad1.oraclevcn.com": {
                    "storageIps": [
                        "100.106.30.6",
                        "100.106.30.7"
                    ]
                },
                "iad103712exdcl02.iad103712exd.adminiad1.oraclevcn.com": {
                    "storageIps": [
                        "100.106.30.14",
                        "100.106.30.15"
                    ]
                },
                "iad103712exdcl03.iad103712exd.adminiad1.oraclevcn.com": {
                    "storageIps": [
                        "100.106.30.16",
                        "100.106.30.17"
                    ]
                }
            },
            "storageVlanId": "551"
        },
        "operation": "create-service",
        "rack": {
            "asmss": "true",
            "backup_disk": "false",
            "cores": 30,
            "create_sparse": "false",
            "ecra_db_rack_name": "iad1-d2-cl3-025ac6a3-0f7e-4e61-a008-01d7847825d0-clu01",
            "gb_memory": "90",
            "gb_storage": 30720,
            "id": "b773f219-3344-4b00-a07b-02da6d0e6354",
            "model": "X8M-2",
            "model_subtype": "elastic",
            "name": "myclu1",
            "size": "ELASTIC-RACK",
            "tb_storage_": "30.0"
        },
        "shared_env": "true",
        "skip_sysimage_version_check": "true",
        "vm": {
            "adminPassword": "UnY0I0R5NSMjXzVfTyM=",
            "cores": 15,
            "gb_memory": 45,
            "gb_ohsize": 200,
            "size": "Large",
            "sshkey": "c3NoLXJzYSBBQUFBQjNOemFDMXljMkVBQUFBREFRQUJBQUFCQVFEckVxZ2N3aGR6RzVXRHE4SU4xR0ZYODg0YStwdUZWeWRZUU5iZlNPbXRQVnFkQnoxWXJlL3QwM21FWXA4K1EzYktFZjR4RVRKM1F1R0k1YnZiOFBHcVVqOW1kdW9MSncwbDlPdTRLSGxCNFJHMmxiYit0QnlEMzVLck1FeHdycTVzVFg0U254eE5obmtXc0k0anM4UU40bXgxZzZZVlF3V0lrWFk5cXF0dkE1bVRoSkkwakFpYVVkc1pDVlFsQXN6b2Iyd0NPL1RpUXhiV3dKWWg5OXFzRXNQQUtkUFJHd2VjZ2tZMHhaQ2dKZXVxeEFGQ0Z3WW5IRzQ1YWNzMksrVjhZOElaKzRORnBTN3pwbDdMNEtXSEdNOE1wZkV4U3czVWl3SUdsVVVYVWJEa2s4ZldSWEpZMTNjNFdaelFQQUF3WTRtWm1BWDU2d0NJVm1TbDZ6amIgb3JhY2xlQGlhZDFkZXZlY3JhMQ=="
        }
    },
    "operation_uuid": "b442ab5c-93bd-4610-bb4e-4fbf52e94002",
    "patchcluinterface": "false",
    "pkeyconf": "false",
    "requestid": "db1d277f-5f6c-480f-8fa3-44e34894817c",
    "scriptname": "",
    "skip_serase": "true",
    "sshkey": "",
    "steplist": "ESTP_CREATE_USER",
    "undo": "false",
    "verbose": "true",
    "wf_uuid": "7c0380a9-db25-43fe-a3e4-32d841d2fef7"
}

PAYLOAD_CREATE_SERVICE_DUAL_STACK = {
    "cmd": "createservice",
    "debug": "true",
    "disablepkey": "false",
    "enablegilatest": "true",
    "exaunitid": "242",
    "frompath_cmd": "true",
    "hostname": "iad1zdlraecra3.ecramgmt.adminiad1.oraclevcn.com",
    "jsonconf": {
        "adb_s": "False",
        "bonding_operation": "create-service",
        "customer_network": {
            "network_services": {
                "dns": [
                    "169.254.169.254"
                ],
                "ntp": [
                    "169.254.169.254"
                ]
            },
            "nodes": [
                {
                    "backup": {
                        "dom0_oracle_name": "iad103716exdd011",
                        "domainname": "backupsubnet.devx8melastic.oraclevcn.com",
                        "domu_oracle_name": "iad103716exddu1101",
                        "gateway": "10.0.32.1",
                        "v6gateway": "fe80::17ff:fe13:5d90",
                        "hostname": "c3716n11b1",
                        "hw_node_id": 5,
                        "ip": "10.0.38.38",
                        "ipv6": "fe80::17ff:fe13:5d91",
                        "mac": "00:00:17:00:11:3F",
                        "netmask": "255.255.224.0",
                        "v6netmask": "64",
                        "vlantag": "2",
                        "v6vip": "fe80::17ff:fe13:5d92"
                    },
                    "client": {
                        "dom0_oracle_name": "iad103716exdd011",
                        "domainname": "clientsubnet.devx8melastic.oraclevcn.com",
                        "domu_oracle_name": "iad103716exddu1101",
                        "gateway": "10.0.0.1",
                        "v6gateway": "fe80::17ff:fe13:5c90",
                        "hostname": "c3716n11c1",
                        "hw_node_id": 5,
                        "ip": "10.0.8.185",
                        "ipv6": "fe80::17ff:fe13:5c91",
                        "mac": "02:00:17:12:15:D4",
                        "natdomainname": "iad103716exd.adminiad1.oraclevcn.com",
                        "natmask": "255.255.255.128",
                        "netmask": "255.255.224.0",
                        "v6netmask": "64",
                        "vlantag": "1"
                    },
                    "fqdn": "iad103716exdd011.iad103716exd.adminiad1.oraclevcn.com",
                    "monitoring": {
                        "bond0": {
                            "cavium_ids": [
                                {
                                    "id": "4.0G2004-GBC000913",
                                    "networkinterface": "eth1"
                                },
                                {
                                    "id": "4.0G2001-GBC001819",
                                    "networkinterface": "eth2"
                                }
                            ],
                            "gateway": "192.168.1.1",
                            "ip": "192.168.1.145",
                            "netmask": "255.255.255.0",
                            "preferred_interface": "eth1",
                            "vlantag": 0
                        }
                    },
                    "vip": {
                        "domainname": "clientsubnet.devx8melastic.oraclevcn.com",
                        "hostname": "c3716n11c1-vip",
                        "ip": "10.0.3.203",
                        "ipv6": "fe80::17ff:fe13:5c92"
                    }
                },
                {
                    "backup": {
                        "dom0_oracle_name": "iad103716exdd012",
                        "domainname": "backupsubnet.devx8melastic.oraclevcn.com",
                        "domu_oracle_name": "iad103716exddu1201",
                        "gateway": "10.0.32.1",
                        "v6gateway": "fe80::17ff:fe13:5d90",
                        "hostname": "c3716n12b1",
                        "hw_node_id": 5,
                        "ip": "10.0.33.197",
                        "ipv6": "fe80::17ff:fe13:5d93",
                        "mac": "02:00:17:03:58:72",
                        "netmask": "255.255.224.0",
                        "v6netmask": "64",
                        "vlantag": "2"
                    },
                    "client": {
                        "dom0_oracle_name": "iad103716exdd012",
                        "domainname": "clientsubnet.devx8melastic.oraclevcn.com",
                        "domu_oracle_name": "iad103716exddu1201",
                        "gateway": "10.0.0.1",
                        "v6gateway": "fe80::17ff:fe13:5c90",
                        "hostname": "c3716n12c1",
                        "hw_node_id": 5,
                        "ip": "10.0.11.73",
                        "ipv6": "fe80::17ff:fe13:5c94",
                        "mac": "02:00:17:12:BD:52",
                        "natdomainname": "iad103716exd.adminiad1.oraclevcn.com",
                        "natmask": "255.255.255.128",
                        "netmask": "255.255.224.0",
                        "v6netmask": "64",
                        "vlantag": "1"
                    },
                    "fqdn": "iad103716exdd012.iad103716exd.adminiad1.oraclevcn.com",
                    "monitoring": {
                        "bond0": {
                            "cavium_ids": [
                                {
                                    "id": "4.0G2001-GBC001134",
                                    "networkinterface": "eth1"
                                },
                                {
                                    "id": "4.0G1949-GBC000006",
                                    "networkinterface": "eth2"
                                }
                            ],
                            "gateway": "192.168.1.1",
                            "ip": "192.168.1.209",
                            "netmask": "255.255.255.0",
                            "preferred_interface": "eth2",
                            "vlantag": 0
                        }
                    },
                    "vip": {
                        "domainname": "clientsubnet.devx8melastic.oraclevcn.com",
                        "hostname": "c3716n12c1-vip",
                        "ip": "10.0.27.136",
                        "ipv6": "fe80::17ff:fe13:5c93"
                    }
                }
            ],
            "scan": {
                "hostname": "idc3716-clu01scan",
                "ips": [
                    "10.0.9.124",
                    "10.0.25.120",
                    "10.0.0.121"
                ],
                "v6ips": [
                    "fe80::17ff:fe13:5c95",
                    "fe80::17ff:fe13:5c96",
                    "fe80::17ff:fe13:5c97"
                ],
                "port": 1521
            },
            "timezone": "UTC"
        },
        "dbaas_api": {
            "FLAGS": "",
            "action": "set",
            "object": "os",
            "operation": "cloud_properties",
            "outputfile": "/tmp/cloudProperties_2024.05.20.12.50.29",
            "params": {
                "adb_s": {
                    "enabled": "False"
                },
                "atp": {
                    "enabled": "False"
                },
                "cns": {
                    "enabled": "False"
                },
                "common": {
                    "fedramp": "disabled",
                    "fips_compliance": "disabled",
                    "oss_url": "https://swiftobjectstorage.us-ashburn-1.oraclecloud.com",
                    "se_linux": "disabled"
                },
                "diag": {},
                "ords": {
                    "enable": "False"
                }
            }
        },
        "delete_domu_keys": "false",
        "dom0_bonding": "true",
        "eth0_removed": "false",
        "fedramp": "N",
        "filesystems": {
            "mountpoints": {
                "/": "15G",
                "/home": "4G",
                "/tmp": "10G",
                "/u01": "250G",
                "/var": "10G",
                "/var/log": "30G",
                "/var/log/audit": "3G",
                "grid": "50G"
            }
        },
        "grid_version": "19",
        "kvmroce": {
            "ComputeNetmask": "255.255.0.0",
            "StorageNetmask": "255.255.0.0",
            "computeNetwork": {
                "c3716n11c1.clientsubnet.devx8melastic.oraclevcn.com": {
                    "clusterInterconnectIps": [
                        "100.107.0.2",
                        "100.107.0.3"
                    ],
                    "storageIps": [
                        "100.106.64.0",
                        "100.106.64.1"
                    ]
                },
                "c3716n12c1.clientsubnet.devx8melastic.oraclevcn.com": {
                    "clusterInterconnectIps": [
                        "100.107.0.4",
                        "100.107.0.5"
                    ],
                    "storageIps": [
                        "100.106.64.2",
                        "100.106.64.3"
                    ]
                }
            },
            "computeVlanId": "541",
            "storageNetwork": {
                "iad103712exdcl01.iad103712exd.adminiad1.oraclevcn.com": {
                    "storageIps": [
                        "100.106.30.6",
                        "100.106.30.7"
                    ]
                },
                "iad103712exdcl02.iad103712exd.adminiad1.oraclevcn.com": {
                    "storageIps": [
                        "100.106.30.14",
                        "100.106.30.15"
                    ]
                },
                "iad103712exdcl03.iad103712exd.adminiad1.oraclevcn.com": {
                    "storageIps": [
                        "100.106.30.16",
                        "100.106.30.17"
                    ]
                }
            },
            "storageVlanId": "551"
        },
        "operation": "create-service",
        "rack": {
            "asmss": "true",
            "backup_disk": "false",
            "cores": 30,
            "create_sparse": "false",
            "ecra_db_rack_name": "iad1-d2-cl3-025ac6a3-0f7e-4e61-a008-01d7847825d0-clu01",
            "gb_memory": "90",
            "gb_storage": 30720,
            "id": "b773f219-3344-4b00-a07b-02da6d0e6354",
            "model": "X8M-2",
            "model_subtype": "elastic",
            "name": "myclu1",
            "size": "ELASTIC-RACK",
            "tb_storage_": "30.0"
        },
        "shared_env": "true",
        "skip_sysimage_version_check": "true",
        "vm": {
            "adminPassword": "UnY0I0R5NSMjXzVfTyM=",
            "cores": 15,
            "gb_memory": 45,
            "gb_ohsize": 200,
            "size": "Large",
            "sshkey": "c3NoLXJzYSBBQUFBQjNOemFDMXljMkVBQUFBREFRQUJBQUFCQVFEckVxZ2N3aGR6RzVXRHE4SU4xR0ZYODg0YStwdUZWeWRZUU5iZlNPbXRQVnFkQnoxWXJlL3QwM21FWXA4K1EzYktFZjR4RVRKM1F1R0k1YnZiOFBHcVVqOW1kdW9MSncwbDlPdTRLSGxCNFJHMmxiYit0QnlEMzVLck1FeHdycTVzVFg0U254eE5obmtXc0k0anM4UU40bXgxZzZZVlF3V0lrWFk5cXF0dkE1bVRoSkkwakFpYVVkc1pDVlFsQXN6b2Iyd0NPL1RpUXhiV3dKWWg5OXFzRXNQQUtkUFJHd2VjZ2tZMHhaQ2dKZXVxeEFGQ0Z3WW5IRzQ1YWNzMksrVjhZOElaKzRORnBTN3pwbDdMNEtXSEdNOE1wZkV4U3czVWl3SUdsVVVYVWJEa2s4ZldSWEpZMTNjNFdaelFQQUF3WTRtWm1BWDU2d0NJVm1TbDZ6amIgb3JhY2xlQGlhZDFkZXZlY3JhMQ=="
        }
    },
    "operation_uuid": "b442ab5c-93bd-4610-bb4e-4fbf52e94002",
    "patchcluinterface": "false",
    "pkeyconf": "false",
    "requestid": "db1d277f-5f6c-480f-8fa3-44e34894817c",
    "scriptname": "",
    "skip_serase": "true",
    "sshkey": "",
    "steplist": "ESTP_CREATE_USER",
    "undo": "false",
    "verbose": "true",
    "wf_uuid": "7c0380a9-db25-43fe-a3e4-32d841d2fef7"
}

PAYLOAD_CREATE_SERVICE_IPv6 = {
    "cmd": "createservice",
    "debug": "true",
    "disablepkey": "false",
    "enablegilatest": "true",
    "exaunitid": "242",
    "frompath_cmd": "true",
    "hostname": "iad1zdlraecra3.ecramgmt.adminiad1.oraclevcn.com",
    "jsonconf": {
        "adb_s": "False",
        "bonding_operation": "create-service",
        "customer_network": {
            "network_services": {
                "dns": [
                    "169.254.169.254"
                ],
                "ntp": [
                    "169.254.169.254"
                ]
            },
            "nodes": [
                {
                    "backup": {
                        "dom0_oracle_name": "iad103716exdd011",
                        "domainname": "backupsubnet.devx8melastic.oraclevcn.com",
                        "domu_oracle_name": "iad103716exddu1101",
                        "gateway": "fe80::17ff:fe13:5d90",
                        "hostname": "c3716n11b1",
                        "hw_node_id": 5,
                        "ip": "fe80::17ff:fe13:5d91",
                        "mac": "00:00:17:00:11:3F",
                        "netmask": "64",
                        "vlantag": "2",
                        "vip": "fe80::17ff:fe13:5d92"
                    },
                    "client": {
                        "dom0_oracle_name": "iad103716exdd011",
                        "domainname": "clientsubnet.devx8melastic.oraclevcn.com",
                        "domu_oracle_name": "iad103716exddu1101",
                        "gateway": "fe80::17ff:fe13:5c90",
                        "hostname": "c3716n11c1",
                        "hw_node_id": 5,
                        "ip": "fe80::17ff:fe13:5c91",
                        "mac": "02:00:17:12:15:D4",
                        "natdomainname": "iad103716exd.adminiad1.oraclevcn.com",
                        "natmask": "255.255.255.128",
                        "netmask": "64",
                        "vlantag": "1"
                    },
                    "fqdn": "iad103716exdd011.iad103716exd.adminiad1.oraclevcn.com",
                    "monitoring": {
                        "bond0": {
                            "cavium_ids": [
                                {
                                    "id": "4.0G2004-GBC000913",
                                    "networkinterface": "eth1"
                                },
                                {
                                    "id": "4.0G2001-GBC001819",
                                    "networkinterface": "eth2"
                                }
                            ],
                            "gateway": "192.168.1.1",
                            "ip": "192.168.1.145",
                            "netmask": "255.255.255.0",
                            "preferred_interface": "eth1",
                            "vlantag": 0
                        }
                    },
                    "vip": {
                        "domainname": "clientsubnet.devx8melastic.oraclevcn.com",
                        "hostname": "c3716n11c1-vip",
                        "ip": "fe80::17ff:fe13:5c92"
                    }
                },
                {
                    "backup": {
                        "dom0_oracle_name": "iad103716exdd012",
                        "domainname": "backupsubnet.devx8melastic.oraclevcn.com",
                        "domu_oracle_name": "iad103716exddu1201",
                        "gateway": "fe80::17ff:fe13:5d90",
                        "hostname": "c3716n12b1",
                        "hw_node_id": 5,
                        "ip": "fe80::17ff:fe13:5d93",
                        "mac": "02:00:17:03:58:72",
                        "netmask": "64",
                        "vlantag": "2"
                    },
                    "client": {
                        "dom0_oracle_name": "iad103716exdd012",
                        "domainname": "clientsubnet.devx8melastic.oraclevcn.com",
                        "domu_oracle_name": "iad103716exddu1201",
                        "gateway": "fe80::17ff:fe13:5c90",
                        "hostname": "c3716n12c1",
                        "hw_node_id": 5,
                        "ip": "fe80::17ff:fe13:5c94",
                        "mac": "02:00:17:12:BD:52",
                        "natdomainname": "iad103716exd.adminiad1.oraclevcn.com",
                        "natmask": "255.255.255.128",
                        "netmask": "64",
                        "vlantag": "1"
                    },
                    "fqdn": "iad103716exdd012.iad103716exd.adminiad1.oraclevcn.com",
                    "monitoring": {
                        "bond0": {
                            "cavium_ids": [
                                {
                                    "id": "4.0G2001-GBC001134",
                                    "networkinterface": "eth1"
                                },
                                {
                                    "id": "4.0G1949-GBC000006",
                                    "networkinterface": "eth2"
                                }
                            ],
                            "gateway": "192.168.1.1",
                            "ip": "192.168.1.209",
                            "netmask": "255.255.255.0",
                            "preferred_interface": "eth2",
                            "vlantag": 0
                        }
                    },
                    "vip": {
                        "domainname": "clientsubnet.devx8melastic.oraclevcn.com",
                        "hostname": "c3716n12c1-vip",
                        "ip": "fe80::17ff:fe13:5c93"
                    }
                }
            ],
            "scan": {
                "hostname": "idc3716-clu01scan",
                "ips": [
                    "fe80::17ff:fe13:5c95",
                    "fe80::17ff:fe13:5c96",
                    "fe80::17ff:fe13:5c97"
                ],
                "port": 1521
            },
            "timezone": "UTC"
        },
        "dbaas_api": {
            "FLAGS": "",
            "action": "set",
            "object": "os",
            "operation": "cloud_properties",
            "outputfile": "/tmp/cloudProperties_2024.05.20.12.50.29",
            "params": {
                "adb_s": {
                    "enabled": "False"
                },
                "atp": {
                    "enabled": "False"
                },
                "cns": {
                    "enabled": "False"
                },
                "common": {
                    "fedramp": "disabled",
                    "fips_compliance": "disabled",
                    "oss_url": "https://swiftobjectstorage.us-ashburn-1.oraclecloud.com",
                    "se_linux": "disabled"
                },
                "diag": {},
                "ords": {
                    "enable": "False"
                }
            }
        },
        "delete_domu_keys": "false",
        "dom0_bonding": "true",
        "eth0_removed": "false",
        "fedramp": "N",
        "filesystems": {
            "mountpoints": {
                "/": "15G",
                "/home": "4G",
                "/tmp": "10G",
                "/u01": "250G",
                "/var": "10G",
                "/var/log": "30G",
                "/var/log/audit": "3G",
                "grid": "50G"
            }
        },
        "grid_version": "19",
        "kvmroce": {
            "ComputeNetmask": "255.255.0.0",
            "StorageNetmask": "255.255.0.0",
            "computeNetwork": {
                "c3716n11c1.clientsubnet.devx8melastic.oraclevcn.com": {
                    "clusterInterconnectIps": [
                        "100.107.0.2",
                        "100.107.0.3"
                    ],
                    "storageIps": [
                        "100.106.64.0",
                        "100.106.64.1"
                    ]
                },
                "c3716n12c1.clientsubnet.devx8melastic.oraclevcn.com": {
                    "clusterInterconnectIps": [
                        "100.107.0.4",
                        "100.107.0.5"
                    ],
                    "storageIps": [
                        "100.106.64.2",
                        "100.106.64.3"
                    ]
                }
            },
            "computeVlanId": "541",
            "storageNetwork": {
                "iad103712exdcl01.iad103712exd.adminiad1.oraclevcn.com": {
                    "storageIps": [
                        "100.106.30.6",
                        "100.106.30.7"
                    ]
                },
                "iad103712exdcl02.iad103712exd.adminiad1.oraclevcn.com": {
                    "storageIps": [
                        "100.106.30.14",
                        "100.106.30.15"
                    ]
                },
                "iad103712exdcl03.iad103712exd.adminiad1.oraclevcn.com": {
                    "storageIps": [
                        "100.106.30.16",
                        "100.106.30.17"
                    ]
                }
            },
            "storageVlanId": "551"
        },
        "operation": "create-service",
        "rack": {
            "asmss": "true",
            "backup_disk": "false",
            "cores": 30,
            "create_sparse": "false",
            "ecra_db_rack_name": "iad1-d2-cl3-025ac6a3-0f7e-4e61-a008-01d7847825d0-clu01",
            "gb_memory": "90",
            "gb_storage": 30720,
            "id": "b773f219-3344-4b00-a07b-02da6d0e6354",
            "model": "X8M-2",
            "model_subtype": "elastic",
            "name": "myclu1",
            "size": "ELASTIC-RACK",
            "tb_storage_": "30.0"
        },
        "shared_env": "true",
        "skip_sysimage_version_check": "true",
        "vm": {
            "adminPassword": "UnY0I0R5NSMjXzVfTyM=",
            "cores": 15,
            "gb_memory": 45,
            "gb_ohsize": 200,
            "size": "Large",
            "sshkey": "c3NoLXJzYSBBQUFBQjNOemFDMXljMkVBQUFBREFRQUJBQUFCQVFEckVxZ2N3aGR6RzVXRHE4SU4xR0ZYODg0YStwdUZWeWRZUU5iZlNPbXRQVnFkQnoxWXJlL3QwM21FWXA4K1EzYktFZjR4RVRKM1F1R0k1YnZiOFBHcVVqOW1kdW9MSncwbDlPdTRLSGxCNFJHMmxiYit0QnlEMzVLck1FeHdycTVzVFg0U254eE5obmtXc0k0anM4UU40bXgxZzZZVlF3V0lrWFk5cXF0dkE1bVRoSkkwakFpYVVkc1pDVlFsQXN6b2Iyd0NPL1RpUXhiV3dKWWg5OXFzRXNQQUtkUFJHd2VjZ2tZMHhaQ2dKZXVxeEFGQ0Z3WW5IRzQ1YWNzMksrVjhZOElaKzRORnBTN3pwbDdMNEtXSEdNOE1wZkV4U3czVWl3SUdsVVVYVWJEa2s4ZldSWEpZMTNjNFdaelFQQUF3WTRtWm1BWDU2d0NJVm1TbDZ6amIgb3JhY2xlQGlhZDFkZXZlY3JhMQ=="
        }
    },
    "operation_uuid": "b442ab5c-93bd-4610-bb4e-4fbf52e94002",
    "patchcluinterface": "false",
    "pkeyconf": "false",
    "requestid": "db1d277f-5f6c-480f-8fa3-44e34894817c",
    "scriptname": "",
    "skip_serase": "true",
    "sshkey": "",
    "steplist": "ESTP_CREATE_USER",
    "undo": "false",
    "verbose": "true",
    "wf_uuid": "7c0380a9-db25-43fe-a3e4-32d841d2fef7"
}

PAYLOAD_ADD_COMPUTE = {
    "cmd": "vmgi_reshape",
    "debug": "true",
    "disablepkey": "false",
    "exaunitid": 242,
    "frompath_cmd": "true",
    "hostname": "iad1zdlraecra3.ecramgmt.adminiad1.oraclevcn.com",
    "jsonconf": {
        "adb_s": "False",
        "bonding_operation": "add-compute",
        "delete_domu_keys": "false",
        "dom0_bonding": "true",
        "domu_image_version": "23.1.12.0.0.240322",
        "exaunitid": 242,
        "filesystems": {
            "mountpoints": {
                "/": "15G",
                "/home": "4G",
                "/tmp": "10G",
                "/u01": "250G",
                "/var": "10G",
                "/var/log": "30G",
                "/var/log/audit": "3G",
                "grid": "50G"
            }
        },
        "fips_compliance": "disabled",
        "grid_version": "19",
        "model_subtype": "elastic",
        "name": "myclu1",
        "operation_uuid": "1ecd1d2c-1c73-4a59-8d5e-4c9b1d8149df",
        "rackname": "iad1-d2-cl3-025ac6a3-0f7e-4e61-a008-01d7847825d0-clu01",
        "reshaped_node_subset": {
            "added_computes": [
                {
                    "compute_node_alias": "dbserver-3",
                    "compute_node_hostname": "iad103716exdd013.iad103716exd.adminiad1.oraclevcn.com",
                    "db_info": [],
                    "model": "X8M-2",
                    "network_info": {
                        "computenetworks": [
                            {
                                "admin": [
                                    {
                                        "fqdn": "iad103716exdd013.iad103716exd.adminiad1.oraclevcn.com",
                                        "gateway": "10.0.7.129",
                                        "ipaddr": "10.0.7.142",
                                        "master": "eth0",
                                        "netmask": "255.255.255.128"
                                    }
                                ]
                            },
                            {
                                "private": [
                                    {
                                        "fqdn": "iad103716exdd013-priv1.iad103716exd.adminiad1.oraclevcn.com",
                                        "ipaddr": "192.168.132.12"
                                    },
                                    {
                                        "fqdn": "iad103716exdd013-priv2.iad103716exd.adminiad1.oraclevcn.com",
                                        "ipaddr": "192.168.132.13"
                                    }
                                ]
                            },
                            {
                                "ilom": [
                                    {
                                        "fqdn": "iad103716exdd013lo.iad103716exd.adminiad1.oraclevcn.com",
                                        "gateway": "10.0.7.129",
                                        "ipaddr": "10.0.7.160",
                                        "netmask": "255.255.255.128"
                                    }
                                ]
                            }
                        ]
                    },
                    "rack_info": {
                        "uheight": "1",
                        "uloc": "13"
                    },
                    "racktype": "1035",
                    "virtual_compute_info": {
                        "compute_node_hostname": "c3716n13c1.clientsubnet.devx8melastic.oraclevcn.com",
                        "network_info": {
                            "virtualcomputenetworks": [
                                {
                                    "private": [
                                        {
                                            "fqdn": "iad103716exddu1301-stre0.iad103716exd.adminiad1.oraclevcn.com",
                                            "ipaddr": "100.106.64.4"
                                        },
                                        {
                                            "fqdn": "iad103716exddu1301-stre1.iad103716exd.adminiad1.oraclevcn.com",
                                            "ipaddr": "100.106.64.5"
                                        }
                                    ]
                                },
                                {
                                    "admin": [
                                        {
                                            "fqdn": "c3716n13c1.clientsubnet.devx8melastic.oraclevcn.com"
                                        }
                                    ]
                                },
                                {
                                    "client": [
                                        {
                                            "fqdn": "c3716n13c1.clientsubnet.devx8melastic.oraclevcn.com",
                                            "gateway": "10.0.0.1",
                                            "ipaddr": "10.0.23.112",
                                            "mac": "02:00:17:0E:1C:18",
                                            "natdomain": "iad103716exd.adminiad1.oraclevcn.com",
                                            "nathostname": "iad103716exddu1301",
                                            "natip": "10.0.7.187",
                                            "natnetmask": "255.255.255.128",
                                            "netmask": "255.255.224.0",
                                            "slaves": "eth1 eth2",
                                            "vlantag": "1"
                                        }
                                    ]
                                },
                                {
                                    "backup": [
                                        {
                                            "fqdn": "c3716n13b1.backupsubnet.devx8melastic.oraclevcn.com",
                                            "gateway": "10.0.32.1",
                                            "ipaddr": "10.0.54.220",
                                            "mac": "02:00:17:0A:CE:AD",
                                            "netmask": "255.255.224.0",
                                            "slaves": "eth1 eth2",
                                            "vlantag": "2"
                                        }
                                    ]
                                },
                                {
                                    "interconnect": [
                                        {
                                            "fqdn": "iad103716exddu1301-clre0.iad103716exd.adminiad1.oraclevcn.com",
                                            "ipaddr": "100.107.0.6"
                                        },
                                        {
                                            "fqdn": "iad103716exddu1301-clre1.iad103716exd.adminiad1.oraclevcn.com",
                                            "ipaddr": "100.107.0.7"
                                        }
                                    ]
                                },
                                {
                                    "vip": [
                                        {
                                            "fqdn": "c3716n13c1-vip.clientsubnet.devx8melastic.oraclevcn.com",
                                            "ipaddr": "10.0.21.220"
                                        }
                                    ]
                                },
                                {
                                    "monitoring": {
                                        "bond0": {
                                            "cavium_ids": [
                                                {
                                                    "id": "4.0G2001-GBC001341",
                                                    "networkinterface": "eth1"
                                                },
                                                {
                                                    "id": "4.0G2001-GBC000265",
                                                    "networkinterface": "eth2"
                                                }
                                            ],
                                            "gateway": "192.168.1.1",
                                            "ip": "192.168.1.182",
                                            "netmask": "255.255.255.0",
                                            "preferred_interface": "eth1",
                                            "vlantag": 0
                                        }
                                    }
                                }
                            ]
                        },
                        "vm": {
                            "cores": 15,
                            "gb_memory": 45,
                            "gb_ohsize": 200,
                            "size": "Large"
                        }
                    },
                    "volumes": []
                }
            ],
            "full_compute_to_virtualcompute_list": [
                {
                    "compute_node_hostname": "iad103716exdd012.iad103716exd.adminiad1.oraclevcn.com",
                    "compute_node_virtual_hostname": "c3716n12c1.clientsubnet.devx8melastic.oraclevcn.com"
                },
                {
                    "compute_node_hostname": "iad103716exdd013.iad103716exd.adminiad1.oraclevcn.com",
                    "compute_node_virtual_hostname": "c3716n13c1.clientsubnet.devx8melastic.oraclevcn.com"
                },
                {
                    "compute_node_hostname": "iad103716exdd011.iad103716exd.adminiad1.oraclevcn.com",
                    "compute_node_virtual_hostname": "c3716n11c1.clientsubnet.devx8melastic.oraclevcn.com"
                }
            ],
            "participating_computes": [
                {
                    "compute_node_alias": "dbserver-1",
                    "compute_node_hostname": "iad103716exdd011.iad103716exd.adminiad1.oraclevcn.com",
                    "model": "X8M-2",
                    "racktype": "1035",
                    "volumes": []
                },
                {
                    "compute_node_alias": "dbserver-2",
                    "compute_node_hostname": "iad103716exdd012.iad103716exd.adminiad1.oraclevcn.com",
                    "model": "X8M-2",
                    "racktype": "1035",
                    "volumes": []
                },
                {
                    "compute_node_alias": "dbserver-3",
                    "compute_node_hostname": "iad103716exdd013.iad103716exd.adminiad1.oraclevcn.com",
                    "model": "X8M-2",
                    "racktype": "1035",
                    "volumes": []
                }
            ],
            "removed_computes": [],
            "retained_computes": [
                {
                    "compute_node_alias": "dbserver-1",
                    "compute_node_hostname": "iad103716exdd011.iad103716exd.adminiad1.oraclevcn.com",
                    "model": "X8M-2",
                    "racktype": "1035",
                    "volumes": []
                },
                {
                    "compute_node_alias": "dbserver-2",
                    "compute_node_hostname": "iad103716exdd012.iad103716exd.adminiad1.oraclevcn.com",
                    "model": "X8M-2",
                    "racktype": "1035",
                    "volumes": []
                }
            ]
        },
        "shared_env": "true",
        "wf_uuid": "bc5d8163-9e95-48b3-8934-435e86c49183"
    },
    "operation_uuid": "85929880-0b74-47f5-9860-2e24c84690d7",
    "patchcluinterface": "false",
    "pkeyconf": "false",
    "scriptname": "",
    "skip_serase": "true",
    "sshkey": "",
    "steplist": "CREATE_GUEST",
    "undo": "true",
    "verbose": "true",
    "wf_uuid": "bc5d8163-9e95-48b3-8934-435e86c49183"
}

NEW_PAYLOAD_ADD_COMPUTE = {
    'fqdn': 'iad103716exdd013.iad103716exd.adminiad1.oraclevcn.com',
    'client':
        {
            'fqdn': 'c3716n13c1.clientsubnet.devx8melastic.oraclevcn.com',
            'gateway': '10.0.0.1',
            'mac': '02:00:17:0E:1C:18',
            'natdomain': 'iad103716exd.adminiad1.oraclevcn.com',
            'natip': '10.0.7.187',
            'natnetmask': '255.255.255.128',
            'netmask': '255.255.224.0',
            'slaves': 'eth1 eth2',
            'vlantag': '1',
            'domu_oracle_name': 'iad103716exddu1301',
            'ip': '10.0.23.112'
        },
    'backup':
        {
            'fqdn': 'c3716n13b1.backupsubnet.devx8melastic.oraclevcn.com',
            'gateway': '10.0.32.1',
            'mac': '02:00:17:0A:CE:AD',
            'netmask': '255.255.224.0',
            'slaves': 'eth1 eth2',
            'vlantag': '2',
            'ip': '10.0.54.220'
        },
    "admin": {                            
        "fqdn": "c3716n13c1.clientsubnet.devx8melastic.oraclevcn.com"
    },
    'vip':
        {
            'fqdn': 'c3716n13c1-vip.clientsubnet.devx8melastic.oraclevcn.com',
            'ip': '10.0.21.220'
        },
    'monitoring':
        {
            'bond0':
                {
                    'cavium_ids':
                        [
                            {
                                'id': '4.0G2001-GBC001341',
                                'networkinterface': 'eth1'
                            },
                            {
                                'id': '4.0G2001-GBC000265',
                                'networkinterface': 'eth2'
                            }
                        ],
                    'gateway': '192.168.1.1',
                    'ip': '192.168.1.182',
                    'netmask': '255.255.255.0',
                    'preferred_interface': 'eth1',
                    'vlantag': 0
                }
        }
}

PAYLOAD_ADD_COMPUTE_DUAL_STACK = {
    "cmd": "vmgi_reshape",
    "debug": "true",
    "disablepkey": "false",
    "exaunitid": 242,
    "frompath_cmd": "true",
    "hostname": "iad1zdlraecra3.ecramgmt.adminiad1.oraclevcn.com",
    "jsonconf": {
        "adb_s": "False",
        "bonding_operation": "add-compute",
        "delete_domu_keys": "false",
        "dom0_bonding": "true",
        "domu_image_version": "23.1.12.0.0.240322",
        "exaunitid": 242,
        "filesystems": {
            "mountpoints": {
                "/": "15G",
                "/home": "4G",
                "/tmp": "10G",
                "/u01": "250G",
                "/var": "10G",
                "/var/log": "30G",
                "/var/log/audit": "3G",
                "grid": "50G"
            }
        },
        "fips_compliance": "disabled",
        "grid_version": "19",
        "model_subtype": "elastic",
        "name": "myclu1",
        "operation_uuid": "1ecd1d2c-1c73-4a59-8d5e-4c9b1d8149df",
        "rackname": "iad1-d2-cl3-025ac6a3-0f7e-4e61-a008-01d7847825d0-clu01",
        "reshaped_node_subset": {
            "added_computes": [
                {
                    "compute_node_alias": "dbserver-3",
                    "compute_node_hostname": "iad103716exdd013.iad103716exd.adminiad1.oraclevcn.com",
                    "db_info": [],
                    "model": "X8M-2",
                    "network_info": {
                        "computenetworks": [
                            {
                                "admin": [
                                    {
                                        "fqdn": "iad103716exdd013.iad103716exd.adminiad1.oraclevcn.com",
                                        "gateway": "10.0.7.129",
                                        "ipaddr": "10.0.7.142",
                                        "master": "eth0",
                                        "netmask": "255.255.255.128"
                                    }
                                ]
                            },
                            {
                                "private": [
                                    {
                                        "fqdn": "iad103716exdd013-priv1.iad103716exd.adminiad1.oraclevcn.com",
                                        "ipaddr": "192.168.132.12"
                                    },
                                    {
                                        "fqdn": "iad103716exdd013-priv2.iad103716exd.adminiad1.oraclevcn.com",
                                        "ipaddr": "192.168.132.13"
                                    }
                                ]
                            },
                            {
                                "ilom": [
                                    {
                                        "fqdn": "iad103716exdd013lo.iad103716exd.adminiad1.oraclevcn.com",
                                        "gateway": "10.0.7.129",
                                        "ipaddr": "10.0.7.160",
                                        "netmask": "255.255.255.128"
                                    }
                                ]
                            }
                        ]
                    },
                    "rack_info": {
                        "uheight": "1",
                        "uloc": "13"
                    },
                    "racktype": "1035",
                    "virtual_compute_info": {
                        "compute_node_hostname": "c3716n13c1.clientsubnet.devx8melastic.oraclevcn.com",
                        "network_info": {
                            "virtualcomputenetworks": [
                                {
                                    "private": [
                                        {
                                            "fqdn": "iad103716exddu1301-stre0.iad103716exd.adminiad1.oraclevcn.com",
                                            "ipaddr": "100.106.64.4"
                                        },
                                        {
                                            "fqdn": "iad103716exddu1301-stre1.iad103716exd.adminiad1.oraclevcn.com",
                                            "ipaddr": "100.106.64.5"
                                        }
                                    ]
                                },
                                {
                                    "admin": [
                                        {
                                            "fqdn": "c3716n13c1.clientsubnet.devx8melastic.oraclevcn.com"
                                        }
                                    ]
                                },
                                {
                                    "client": [
                                        {
                                            "fqdn": "c3716n13c1.clientsubnet.devx8melastic.oraclevcn.com",
                                            "gateway": "10.0.0.1",
                                            "v6gateway": "fe80::17ff:fe13:5c90",
                                            "ipaddr": "10.0.23.112",
                                            "ipv6addr": "fe80::17ff:fe13:5c96",
                                            "mac": "02:00:17:0E:1C:18",
                                            "natdomain": "iad103716exd.adminiad1.oraclevcn.com",
                                            "nathostname": "iad103716exddu1301",
                                            "natip": "10.0.7.187",
                                            "natnetmask": "255.255.255.128",
                                            "netmask": "255.255.224.0",
                                            "natgateway": "10.1.0.1",
                                            "v6netmask": "64",
                                            "slaves": "eth1 eth2",
                                            "vlantag": "1"
                                        }
                                    ]
                                },
                                {
                                    "backup": [
                                        {
                                            "fqdn": "c3716n13b1.backupsubnet.devx8melastic.oraclevcn.com",
                                            "gateway": "10.0.32.1",
                                            "v6gateway": "fe80::17ff:fe13:5d90",
                                            "ipaddr": "10.0.54.220",
                                            "ipv6addr": "fe80::17ff:fe13:5d96",
                                            "mac": "02:00:17:0A:CE:AD",
                                            "netmask": "255.255.224.0",
                                            "v6netmask": "64",
                                            "slaves": "eth1 eth2",
                                            "vlantag": "2"
                                        }
                                    ]
                                },
                                {
                                    "interconnect": [
                                        {
                                            "fqdn": "iad103716exddu1301-clre0.iad103716exd.adminiad1.oraclevcn.com",
                                            "ipaddr": "100.107.0.6"
                                        },
                                        {
                                            "fqdn": "iad103716exddu1301-clre1.iad103716exd.adminiad1.oraclevcn.com",
                                            "ipaddr": "100.107.0.7"
                                        }
                                    ]
                                },
                                {
                                    "vip": [
                                        {
                                            "fqdn": "c3716n13c1-vip.clientsubnet.devx8melastic.oraclevcn.com",
                                            "ipaddr": "10.0.21.220",
                                            "ipv6addr": "fe80::17ff:fe13:5c97"
                                        }
                                    ]
                                },
                                {
                                    "monitoring": {
                                        "bond0": {
                                            "cavium_ids": [
                                                {
                                                    "id": "4.0G2001-GBC001341",
                                                    "networkinterface": "eth1"
                                                },
                                                {
                                                    "id": "4.0G2001-GBC000265",
                                                    "networkinterface": "eth2"
                                                }
                                            ],
                                            "gateway": "192.168.1.1",
                                            "ip": "192.168.1.182",
                                            "netmask": "255.255.255.0",
                                            "preferred_interface": "eth1",
                                            "vlantag": 0
                                        }
                                    }
                                }
                            ]
                        },
                        "vm": {
                            "cores": 15,
                            "gb_memory": 45,
                            "gb_ohsize": 200,
                            "size": "Large"
                        }
                    },
                    "volumes": []
                }
            ],
            "full_compute_to_virtualcompute_list": [
                {
                    "compute_node_hostname": "iad103716exdd012.iad103716exd.adminiad1.oraclevcn.com",
                    "compute_node_virtual_hostname": "c3716n12c1.clientsubnet.devx8melastic.oraclevcn.com"
                },
                {
                    "compute_node_hostname": "iad103716exdd013.iad103716exd.adminiad1.oraclevcn.com",
                    "compute_node_virtual_hostname": "c3716n13c1.clientsubnet.devx8melastic.oraclevcn.com"
                },
                {
                    "compute_node_hostname": "iad103716exdd011.iad103716exd.adminiad1.oraclevcn.com",
                    "compute_node_virtual_hostname": "c3716n11c1.clientsubnet.devx8melastic.oraclevcn.com"
                }
            ],
            "participating_computes": [
                {
                    "compute_node_alias": "dbserver-1",
                    "compute_node_hostname": "iad103716exdd011.iad103716exd.adminiad1.oraclevcn.com",
                    "model": "X8M-2",
                    "racktype": "1035",
                    "volumes": []
                },
                {
                    "compute_node_alias": "dbserver-2",
                    "compute_node_hostname": "iad103716exdd012.iad103716exd.adminiad1.oraclevcn.com",
                    "model": "X8M-2",
                    "racktype": "1035",
                    "volumes": []
                },
                {
                    "compute_node_alias": "dbserver-3",
                    "compute_node_hostname": "iad103716exdd013.iad103716exd.adminiad1.oraclevcn.com",
                    "model": "X8M-2",
                    "racktype": "1035",
                    "volumes": []
                }
            ],
            "removed_computes": [],
            "retained_computes": [
                {
                    "compute_node_alias": "dbserver-1",
                    "compute_node_hostname": "iad103716exdd011.iad103716exd.adminiad1.oraclevcn.com",
                    "model": "X8M-2",
                    "racktype": "1035",
                    "volumes": []
                },
                {
                    "compute_node_alias": "dbserver-2",
                    "compute_node_hostname": "iad103716exdd012.iad103716exd.adminiad1.oraclevcn.com",
                    "model": "X8M-2",
                    "racktype": "1035",
                    "volumes": []
                }
            ]
        },
        "shared_env": "true",
        "wf_uuid": "bc5d8163-9e95-48b3-8934-435e86c49183"
    },
    "operation_uuid": "85929880-0b74-47f5-9860-2e24c84690d7",
    "patchcluinterface": "false",
    "pkeyconf": "false",
    "scriptname": "",
    "skip_serase": "true",
    "sshkey": "",
    "steplist": "CREATE_GUEST",
    "undo": "true",
    "verbose": "true",
    "wf_uuid": "bc5d8163-9e95-48b3-8934-435e86c49183"
}

NEW_PAYLOAD_ADD_COMPUTE_DUAL_STACK = {
    'fqdn': 'iad103716exdd013.iad103716exd.adminiad1.oraclevcn.com',
    'client':
        {
            'fqdn': 'c3716n13c1.clientsubnet.devx8melastic.oraclevcn.com',
            'gateway': '10.0.0.1',
            'v6gateway': 'fe80::17ff:fe13:5c90',
            'mac': '02:00:17:0E:1C:18',
            'natdomain': 'iad103716exd.adminiad1.oraclevcn.com',
            'natip': '10.0.7.187',
            'natnetmask': '255.255.255.128',
            'netmask': '255.255.224.0',
            'natgateway': '10.1.0.1',
            'v6netmask': '64',
            'slaves': 'eth1 eth2',
            'vlantag': '1',
            'domu_oracle_name': 'iad103716exddu1301',
            'ip': '10.0.23.112',
            'ipv6': 'fe80::17ff:fe13:5c96'
        },
    'backup':
        {
            'fqdn': 'c3716n13b1.backupsubnet.devx8melastic.oraclevcn.com',
            'gateway': '10.0.32.1',
            'v6gateway': 'fe80::17ff:fe13:5d90',
            'mac': '02:00:17:0A:CE:AD',
            'netmask': '255.255.224.0',
            'v6netmask': '64',
            'slaves': 'eth1 eth2',
            'vlantag': '2',
            'ip': '10.0.54.220',
            'ipv6': 'fe80::17ff:fe13:5d96'
        },
    "admin": {
        "fqdn": "c3716n13c1.clientsubnet.devx8melastic.oraclevcn.com"
    },
    'vip':
        {
            'fqdn': 'c3716n13c1-vip.clientsubnet.devx8melastic.oraclevcn.com',
            'ip': '10.0.21.220',
            'ipv6': 'fe80::17ff:fe13:5c97'
        },
    'monitoring':
        {
            'bond0':
                {
                    'cavium_ids':
                        [
                            {
                                'id': '4.0G2001-GBC001341',
                                'networkinterface': 'eth1'
                            },
                            {
                                'id': '4.0G2001-GBC000265',
                                'networkinterface': 'eth2'
                            }
                        ],
                    'gateway': '192.168.1.1',
                    'ip': '192.168.1.182',
                    'netmask': '255.255.255.0',
                    'preferred_interface': 'eth1',
                    'vlantag': 0
                }
        }
}

PAYLOAD_ADD_COMPUTE_IPv6 = {
    "cmd": "vmgi_reshape",
    "debug": "true",
    "disablepkey": "false",
    "exaunitid": 242,
    "frompath_cmd": "true",
    "hostname": "iad1zdlraecra3.ecramgmt.adminiad1.oraclevcn.com",
    "jsonconf": {
        "adb_s": "False",
        "bonding_operation": "add-compute",
        "delete_domu_keys": "false",
        "dom0_bonding": "true",
        "domu_image_version": "23.1.12.0.0.240322",
        "exaunitid": 242,
        "filesystems": {
            "mountpoints": {
                "/": "15G",
                "/home": "4G",
                "/tmp": "10G",
                "/u01": "250G",
                "/var": "10G",
                "/var/log": "30G",
                "/var/log/audit": "3G",
                "grid": "50G"
            }
        },
        "fips_compliance": "disabled",
        "grid_version": "19",
        "model_subtype": "elastic",
        "name": "myclu1",
        "operation_uuid": "1ecd1d2c-1c73-4a59-8d5e-4c9b1d8149df",
        "rackname": "iad1-d2-cl3-025ac6a3-0f7e-4e61-a008-01d7847825d0-clu01",
        "reshaped_node_subset": {
            "added_computes": [
                {
                    "compute_node_alias": "dbserver-3",
                    "compute_node_hostname": "iad103716exdd013.iad103716exd.adminiad1.oraclevcn.com",
                    "db_info": [],
                    "model": "X8M-2",
                    "network_info": {
                        "computenetworks": [
                            {
                                "admin": [
                                    {
                                        "fqdn": "iad103716exdd013.iad103716exd.adminiad1.oraclevcn.com",
                                        "gateway": "10.0.7.129",
                                        "ipaddr": "10.0.7.142",
                                        "master": "eth0",
                                        "netmask": "255.255.255.128"
                                    }
                                ]
                            },
                            {
                                "private": [
                                    {
                                        "fqdn": "iad103716exdd013-priv1.iad103716exd.adminiad1.oraclevcn.com",
                                        "ipaddr": "192.168.132.12"
                                    },
                                    {
                                        "fqdn": "iad103716exdd013-priv2.iad103716exd.adminiad1.oraclevcn.com",
                                        "ipaddr": "192.168.132.13"
                                    }
                                ]
                            },
                            {
                                "ilom": [
                                    {
                                        "fqdn": "iad103716exdd013lo.iad103716exd.adminiad1.oraclevcn.com",
                                        "gateway": "10.0.7.129",
                                        "ipaddr": "10.0.7.160",
                                        "netmask": "255.255.255.128"
                                    }
                                ]
                            }
                        ]
                    },
                    "rack_info": {
                        "uheight": "1",
                        "uloc": "13"
                    },
                    "racktype": "1035",
                    "virtual_compute_info": {
                        "compute_node_hostname": "c3716n13c1.clientsubnet.devx8melastic.oraclevcn.com",
                        "network_info": {
                            "virtualcomputenetworks": [
                                {
                                    "private": [
                                        {
                                            "fqdn": "iad103716exddu1301-stre0.iad103716exd.adminiad1.oraclevcn.com",
                                            "ipaddr": "100.106.64.4"
                                        },
                                        {
                                            "fqdn": "iad103716exddu1301-stre1.iad103716exd.adminiad1.oraclevcn.com",
                                            "ipaddr": "100.106.64.5"
                                        }
                                    ]
                                },
                                {
                                    "admin": [
                                        {
                                            "fqdn": "c3716n13c1.clientsubnet.devx8melastic.oraclevcn.com"
                                        }
                                    ]
                                },
                                {
                                    "client": [
                                        {
                                            "fqdn": "c3716n13c1.clientsubnet.devx8melastic.oraclevcn.com",
                                            "gateway": "fe80::17ff:fe13:5c90",
                                            "ipaddr": "fe80::17ff:fe13:5c96",
                                            "mac": "02:00:17:0E:1C:18",
                                            "natdomain": "iad103716exd.adminiad1.oraclevcn.com",
                                            "nathostname": "iad103716exddu1301",
                                            "natip": "10.0.7.187",
                                            "natnetmask": "255.255.255.128",
                                            "netmask": "64",
                                            "slaves": "eth1 eth2",
                                            "vlantag": "1"
                                        }
                                    ]
                                },
                                {
                                    "backup": [
                                        {
                                            "fqdn": "c3716n13b1.backupsubnet.devx8melastic.oraclevcn.com",
                                            "gateway": "fe80::17ff:fe13:5d90",
                                            "ipaddr": "fe80::17ff:fe13:5d96",
                                            "mac": "02:00:17:0A:CE:AD",
                                            "netmask": "64",
                                            "slaves": "eth1 eth2",
                                            "vlantag": "2"
                                        }
                                    ]
                                },
                                {
                                    "interconnect": [
                                        {
                                            "fqdn": "iad103716exddu1301-clre0.iad103716exd.adminiad1.oraclevcn.com",
                                            "ipaddr": "100.107.0.6"
                                        },
                                        {
                                            "fqdn": "iad103716exddu1301-clre1.iad103716exd.adminiad1.oraclevcn.com",
                                            "ipaddr": "100.107.0.7"
                                        }
                                    ]
                                },
                                {
                                    "vip": [
                                        {
                                            "fqdn": "c3716n13c1-vip.clientsubnet.devx8melastic.oraclevcn.com",
                                            "ipaddr": "fe80::17ff:fe13:5c97"
                                        }
                                    ]
                                },
                                {
                                    "monitoring": {
                                        "bond0": {
                                            "cavium_ids": [
                                                {
                                                    "id": "4.0G2001-GBC001341",
                                                    "networkinterface": "eth1"
                                                },
                                                {
                                                    "id": "4.0G2001-GBC000265",
                                                    "networkinterface": "eth2"
                                                }
                                            ],
                                            "gateway": "192.168.1.1",
                                            "ip": "192.168.1.182",
                                            "netmask": "255.255.255.0",
                                            "preferred_interface": "eth1",
                                            "vlantag": 0
                                        }
                                    }
                                }
                            ]
                        },
                        "vm": {
                            "cores": 15,
                            "gb_memory": 45,
                            "gb_ohsize": 200,
                            "size": "Large"
                        }
                    },
                    "volumes": []
                }
            ],
            "full_compute_to_virtualcompute_list": [
                {
                    "compute_node_hostname": "iad103716exdd012.iad103716exd.adminiad1.oraclevcn.com",
                    "compute_node_virtual_hostname": "c3716n12c1.clientsubnet.devx8melastic.oraclevcn.com"
                },
                {
                    "compute_node_hostname": "iad103716exdd013.iad103716exd.adminiad1.oraclevcn.com",
                    "compute_node_virtual_hostname": "c3716n13c1.clientsubnet.devx8melastic.oraclevcn.com"
                },
                {
                    "compute_node_hostname": "iad103716exdd011.iad103716exd.adminiad1.oraclevcn.com",
                    "compute_node_virtual_hostname": "c3716n11c1.clientsubnet.devx8melastic.oraclevcn.com"
                }
            ],
            "participating_computes": [
                {
                    "compute_node_alias": "dbserver-1",
                    "compute_node_hostname": "iad103716exdd011.iad103716exd.adminiad1.oraclevcn.com",
                    "model": "X8M-2",
                    "racktype": "1035",
                    "volumes": []
                },
                {
                    "compute_node_alias": "dbserver-2",
                    "compute_node_hostname": "iad103716exdd012.iad103716exd.adminiad1.oraclevcn.com",
                    "model": "X8M-2",
                    "racktype": "1035",
                    "volumes": []
                },
                {
                    "compute_node_alias": "dbserver-3",
                    "compute_node_hostname": "iad103716exdd013.iad103716exd.adminiad1.oraclevcn.com",
                    "model": "X8M-2",
                    "racktype": "1035",
                    "volumes": []
                }
            ],
            "removed_computes": [],
            "retained_computes": [
                {
                    "compute_node_alias": "dbserver-1",
                    "compute_node_hostname": "iad103716exdd011.iad103716exd.adminiad1.oraclevcn.com",
                    "model": "X8M-2",
                    "racktype": "1035",
                    "volumes": []
                },
                {
                    "compute_node_alias": "dbserver-2",
                    "compute_node_hostname": "iad103716exdd012.iad103716exd.adminiad1.oraclevcn.com",
                    "model": "X8M-2",
                    "racktype": "1035",
                    "volumes": []
                }
            ]
        },
        "shared_env": "true",
        "wf_uuid": "bc5d8163-9e95-48b3-8934-435e86c49183"
    },
    "operation_uuid": "85929880-0b74-47f5-9860-2e24c84690d7",
    "patchcluinterface": "false",
    "pkeyconf": "false",
    "scriptname": "",
    "skip_serase": "true",
    "sshkey": "",
    "steplist": "CREATE_GUEST",
    "undo": "true",
    "verbose": "true",
    "wf_uuid": "bc5d8163-9e95-48b3-8934-435e86c49183"
}

NEW_PAYLOAD_ADD_COMPUTE_IPv6 = {
    'fqdn': 'iad103716exdd013.iad103716exd.adminiad1.oraclevcn.com',
    'client':
        {
            'fqdn': 'c3716n13c1.clientsubnet.devx8melastic.oraclevcn.com',
            'gateway': 'fe80::17ff:fe13:5c90',
            'mac': '02:00:17:0E:1C:18',
            'natdomain': 'iad103716exd.adminiad1.oraclevcn.com',
            'natip': '10.0.7.187',
            'natnetmask': '255.255.255.128',
            'netmask': '64',
            'slaves': 'eth1 eth2',
            'vlantag': '1',
            'domu_oracle_name': 'iad103716exddu1301',
            'ip': 'fe80::17ff:fe13:5c96'
        },
    'backup':
        {
            'fqdn': 'c3716n13b1.backupsubnet.devx8melastic.oraclevcn.com',
            'gateway': 'fe80::17ff:fe13:5d90',
            'mac': '02:00:17:0A:CE:AD',
            'netmask': '64',
            'slaves': 'eth1 eth2',
            'vlantag': '2',
            'ip': 'fe80::17ff:fe13:5d96'
        },
    "admin": {
        "fqdn": "c3716n13c1.clientsubnet.devx8melastic.oraclevcn.com"
    },
    'vip':
        {
            'fqdn': 'c3716n13c1-vip.clientsubnet.devx8melastic.oraclevcn.com',
            'ip': 'fe80::17ff:fe13:5c97'
        },
    'monitoring':
        {
            'bond0':
                {
                    'cavium_ids':
                        [
                            {
                                'id': '4.0G2001-GBC001341',
                                'networkinterface': 'eth1'
                            },
                            {
                                'id': '4.0G2001-GBC000265',
                                'networkinterface': 'eth2'
                            }
                        ],
                    'gateway': '192.168.1.1',
                    'ip': '192.168.1.182',
                    'netmask': '255.255.255.0',
                    'preferred_interface': 'eth1',
                    'vlantag': 0
                }
        }
}

mGetReconfigParams_OUT = {
    'scan': 
        {
            'hostname': 'idc3716-clu01scan'
        },
    'adminPassword': 'UnY0I0R5NSMjXzVfTyM=',
    'c3716n11c1':
        {
            'hostName': 'c3716n11c1.clientsubnet.devx8melastic.oraclevcn.com',
            'vipName': 'c3716n11c1-vip.clientsubnet.devx8melastic.oraclevcn.com',
            'vip': '10.0.3.203',
            'v6vip': 'fe80::17ff:fe13:5c92',
            'client':
                {
                    'ipAddress': '10.0.8.185',
                    'ipv6Address': 'fe80::17ff:fe13:5c91',
                    'netmask': '255.255.224.0',
                    'v6netmask': '48',
                    'gateway': '10.0.0.1',
                    'v6gateway': 'fe80::17ff:fe13:5c90',
                    'macAddress': '02:00:17:12:15:D4',
                    'vlan1': '1',
                    'oldipAddress': '10.0.8.185',
                    'oldipv6Address': 'fe80::17ff:fe13:5c91',
                    'oldnetmask': '255.255.224.0',
                    'oldv6netmask': '48',
                    'oldgateway': '10.0.0.1',
                    'oldv6gateway': 'fe80::17ff:fe13:5c90',
                    'oldmacAddress': '02:00:17:12:15:D4',
                    'oldvlan1': '1'
                },
            'backup':
                {
                    'ipAddress': '10.0.38.38',
                    'ipv6Address': 'fe80::17ff:fe13:5d91',
                    'hostname': 'c3716n11b1',
                    'domainname': 'backupsubnet.devx8melastic.oraclevcn.com',
                    'netmask': '255.255.224.0',
                    'v6netmask': '48',
                    'gateway': '10.0.32.1',
                    'v6gateway': 'fe80::17ff:fe13:5d90',
                    'macAddress': '00:00:17:00:11:3F',
                    'vlan2': '2',
                    'oldipAddress': '10.0.38.38',
                    'oldipv6Address': 'fe80::17ff:fe13:5d91',
                    'oldhostname': 'c3716n11b1',
                    'olddomainname': 'backupsubnet.devx8melastic.oraclevcn.com',
                    'oldnetmask': '255.255.224.0',
                    'oldv6netmask': '48',
                    'oldgateway': '10.0.32.1',
                    'oldv6gateway': 'fe80::17ff:fe13:5d90',
                    'oldmacAddress': '00:00:17:00:11:3F',
                    'oldvlan2': '2'
                },
            'oldHostname': 'c3716n11c1.clientsubnet.devx8melastic.oraclevcn.com'
        },
    'c3716n12c1':
        {
            'hostName': 'c3716n12c1.clientsubnet.devx8melastic.oraclevcn.com',
            'vipName': 'c3716n12c1-vip.clientsubnet.devx8melastic.oraclevcn.com',
            'vip': '10.0.27.136',
            'v6vip': 'fe80::17ff:fe13:5c93',
            'client':
                {
                    'ipAddress': '10.0.11.73',
                    'ipv6Address': 'fe80::17ff:fe13:5c94',
                    'netmask': '255.255.224.0',
                    'v6netmask': '48',
                    'gateway': '10.0.0.1',
                    'v6gateway': 'fe80::17ff:fe13:5c90',
                    'macAddress': '02:00:17:12:BD:52',
                    'vlan1': '1',
                    'oldipAddress': '10.0.11.73',
                    'oldipv6Address': 'fe80::17ff:fe13:5c94',
                    'oldnetmask': '255.255.224.0',
                    'oldv6netmask': '48',
                    'oldgateway': '10.0.0.1',
                    'oldv6gateway': 'fe80::17ff:fe13:5c90',
                    'oldmacAddress': '02:00:17:12:BD:52',
                    'oldvlan1': '1'
                },
            'backup':
                {
                    'ipAddress': '10.0.33.197',
                    'ipv6Address': 'fe80::17ff:fe13:5d93',
                    'hostname': 'c3716n12b1',
                    'domainname': 'backupsubnet.devx8melastic.oraclevcn.com',
                    'netmask': '255.255.224.0',
                    'v6netmask': '48',
                    'gateway': '10.0.32.1',
                    'v6gateway': 'fe80::17ff:fe13:5d90',
                    'macAddress': '02:00:17:03:58:72',
                    'vlan2': '2',
                    'oldipAddress': '10.0.33.197',
                    'oldipv6Address': 'fe80::17ff:fe13:5d93',
                    'oldhostname': 'c3716n12b1',
                    'olddomainname': 'backupsubnet.devx8melastic.oraclevcn.com',
                    'oldnetmask': '255.255.224.0',
                    'oldv6netmask': '48',
                    'oldgateway': '10.0.32.1',
                    'oldv6gateway': 'fe80::17ff:fe13:5d90',
                    'oldmacAddress': '02:00:17:03:58:72',
                    'oldvlan2': '2'
                },
            'oldHostname': 'c3716n12c1.clientsubnet.devx8melastic.oraclevcn.com'
        }
}

mGetReconfigParams_OUT_IPV6 = {
    'scan': 
        {
            'hostname': 'idc3716-clu01scan'
        },
    'adminPassword': 'UnY0I0R5NSMjXzVfTyM=',
    'c3716n11c1':
        {
            'hostName': 'c3716n11c1.clientsubnet.devx8melastic.oraclevcn.com',
            'vipName': 'c3716n11c1-vip.clientsubnet.devx8melastic.oraclevcn.com',
            'vip': 'fe80::17ff:fe13:5c92',
            'client':
                {
                    'ipAddress': 'fe80::17ff:fe13:5c91',
                    'netmask': '48',
                    'gateway': 'fe80::17ff:fe13:5c90',
                    'macAddress': '02:00:17:12:15:D4',
                    'vlan1': '1',
                    'oldipAddress': 'fe80::17ff:fe13:5c91',
                    'oldnetmask': '48',
                    'oldgateway': 'fe80::17ff:fe13:5c90',
                    'oldmacAddress': '02:00:17:12:15:D4',
                    'oldvlan1': '1'
                },
            'backup':
                {
                    'ipAddress': 'fe80::17ff:fe13:5d91',
                    'hostname': 'c3716n11b1',
                    'domainname': 'backupsubnet.devx8melastic.oraclevcn.com',
                    'netmask': '48',
                    'gateway': 'fe80::17ff:fe13:5d90',
                    'macAddress': '00:00:17:00:11:3F',
                    'vlan2': '2',
                    'oldipAddress': 'fe80::17ff:fe13:5d91',
                    'oldhostname': 'c3716n11b1',
                    'olddomainname': 'backupsubnet.devx8melastic.oraclevcn.com',
                    'oldnetmask': '48',
                    'oldgateway': 'fe80::17ff:fe13:5d90',
                    'oldmacAddress': '00:00:17:00:11:3F',
                    'oldvlan2': '2'
                },
            'oldHostname': 'c3716n11c1.clientsubnet.devx8melastic.oraclevcn.com'
        },
    'c3716n12c1':
        {
            'hostName': 'c3716n12c1.clientsubnet.devx8melastic.oraclevcn.com',
            'vipName': 'c3716n12c1-vip.clientsubnet.devx8melastic.oraclevcn.com',
            'vip': 'fe80::17ff:fe13:5c93',
            'client':
                {
                    'ipAddress': 'fe80::17ff:fe13:5c94',
                    'netmask': '48',
                    'gateway': 'fe80::17ff:fe13:5c90',
                    'macAddress': '02:00:17:12:BD:52',
                    'vlan1': '1',
                    'oldipAddress': 'fe80::17ff:fe13:5c94',
                    'oldnetmask': '48',
                    'oldgateway': 'fe80::17ff:fe13:5c90',
                    'oldmacAddress': '02:00:17:12:BD:52',
                    'oldvlan1': '1'
                },
            'backup':
                {
                    'ipAddress': 'fe80::17ff:fe13:5d93',
                    'hostname': 'c3716n12b1',
                    'domainname': 'backupsubnet.devx8melastic.oraclevcn.com',
                    'netmask': '48',
                    'gateway': 'fe80::17ff:fe13:5d90',
                    'macAddress': '02:00:17:03:58:72',
                    'vlan2': '2',
                    'oldipAddress': 'fe80::17ff:fe13:5d93',
                    'oldhostname': 'c3716n12b1',
                    'olddomainname': 'backupsubnet.devx8melastic.oraclevcn.com',
                    'oldnetmask': '48',
                    'oldgateway': 'fe80::17ff:fe13:5d90',
                    'oldmacAddress': '02:00:17:03:58:72',
                    'oldvlan2': '2'
                },
            'oldHostname': 'c3716n12c1.clientsubnet.devx8melastic.oraclevcn.com'
        }
}

mFetchNetworkInfo_OUT = {
    'client':
        {
            'fqdn': 'c3716n11c1clientsubnet.devx8melastic.oraclevcn.com',
            'gateway': '10.0.0.1',
            'v6gateway': 'fe80::17ff:fe13:5c90',
            'mac': '02:00:17:12:15:d4',
            'natdomain': 'iad103716exd.adminiad1.oraclevcn.com',
            'natip': '10.0.7.185',
            'natnetmask': '255.255.255.128',
            'netmask': '255.255.224.0',
            'v6netmask': '64',
            'slaves': 'eth1 eth2',
            'vlantag': '1',
            'domu_oracle_name': 'iad103716exddu1101',
            'ip': '10.0.8.185',
            'ipv6': 'fe80::17ff:fe13:5c91'
        },
    'backup':
        {
            'fqdn': 'c3716n11b1backupsubnet.devx8melastic.oraclevcn.com',
            'gateway': '10.0.32.1',
            'v6gateway': 'fe80::17ff:fe13:5d90',
            'mac': '00:00:17:00:11:3f',
            'netmask': '255.255.224.0',
            'v6netmask': '64',
            'slaves': 'eth1 eth2',
            'vlantag': '2',
            'ip': '10.0.38.38',
            'ipv6': 'fe80::17ff:fe13:5d91'
        },
    'vip':
        {
            'fqdn': 'c3716n11c1-vipclientsubnet.devx8melastic.oraclevcn.com',
            'ip': '10.0.3.203',
            'ipv6': 'fe80::17ff:fe13:5c92'
        },
    'fqdn': 'iad103716exdd011.iad103716exd.adminiad1.oraclevcn.com',
    'bonding_operation': 'vmbackup-restore',
    'dom0_bonding': True
}

mFetchNetworkInfo_OUT_IPV6 = {
    'client':
        {
            'fqdn': 'c3716n11c1clientsubnet.devx8melastic.oraclevcn.com',
            'gateway': 'fe80::17ff:fe13:5c90',
            'mac': '02:00:17:12:15:d4',
            'natdomain': 'iad103716exd.adminiad1.oraclevcn.com',
            'natip': '10.0.7.185',
            'natnetmask': '255.255.255.128',
            'netmask': '64',
            'slaves': 'eth1 eth2',
            'vlantag': '1',
            'domu_oracle_name': 'iad103716exddu1101',
            'ip': 'fe80::17ff:fe13:5c91'
        },
    'backup':
        {
            'fqdn': 'c3716n11b1backupsubnet.devx8melastic.oraclevcn.com',
            'gateway': 'fe80::17ff:fe13:5d90',
            'mac': '00:00:17:00:11:3f',
            'netmask': '64',
            'slaves': 'eth1 eth2',
            'vlantag': '2',
            'ip': 'fe80::17ff:fe13:5d91'
        },
    'vip':
        {
            'fqdn': 'c3716n11c1-vipclientsubnet.devx8melastic.oraclevcn.com',
            'ip': 'fe80::17ff:fe13:5c92'
        },
    'fqdn': 'iad103716exdd011.iad103716exd.adminiad1.oraclevcn.com',
    'bonding_operation': 'vmbackup-restore',
    'dom0_bonding': True
}

xmlGenerationPayload = {
    "exaunitid": 161,
    "mock_mode": "FALSE",
    "operation_uuid": "e1a47afe-00e7-4dcc-87f3-aef000418809",
    "reshaped_node_subset": {
        "added_cells": [
            {
                "cell_hostname": "sea202225exdcl04.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                "model": "X11M",
                "network_info": {
                    "cellnetworks": [
                        {
                            "admin": [
                                {
                                    "fqdn": "sea202225exdcl04.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                    "gateway": "10.0.176.1",
                                    "ipaddr": "10.0.179.133",
                                    "netmask": "255.255.240.0"
                                }
                            ]
                        },
                        {
                            "private": [
                                {
                                    "fqdn": "sea202225exdcl04-priv1.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                    "gateway": "100.106.0.1",
                                    "ipaddr": "100.106.0.98",
                                    "netmask": "255.255.0.0"
                                },
                                {
                                    "fqdn": "sea202225exdcl04-priv2.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                    "gateway": "100.106.0.1",
                                    "ipaddr": "100.106.0.99",
                                    "netmask": "255.255.0.0"
                                }
                            ]
                        },
                        {
                            "ilom": [
                                {
                                    "fqdn": "sea202225exdcl04lo.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                    "gateway": "10.0.176.1",
                                    "ipaddr": "10.0.179.148",
                                    "netmask": "255.255.240.0"
                                }
                            ]
                        },
                        {
                            "ntp": [
                                {
                                    "ipaddr": "169.254.169.254"
                                }
                            ]
                        },
                        {
                            "dns": [
                                {
                                    "ipaddr": "169.254.169.254"
                                }
                            ]
                        }
                    ]
                },
                "rack_info": {
                    "uheight": "1",
                    "uloc": "3"
                },
                "racktype": "1224",
                "storageSize": "22TB",
                "storageType": "HC"
            },
            {
                "cell_hostname": "sea202225exdcl03.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                "model": "X11M",
                "network_info": {
                    "cellnetworks": [
                        {
                            "admin": [
                                {
                                    "fqdn": "sea202225exdcl03.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                    "gateway": "10.0.176.1",
                                    "ipaddr": "10.0.179.132",
                                    "netmask": "255.255.240.0"
                                }
                            ]
                        },
                        {
                            "private": [
                                {
                                    "fqdn": "sea202225exdcl03-priv1.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                    "gateway": "100.106.0.1",
                                    "ipaddr": "100.106.0.96",
                                    "netmask": "255.255.0.0"
                                },
                                {
                                    "fqdn": "sea202225exdcl03-priv2.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                    "gateway": "100.106.0.1",
                                    "ipaddr": "100.106.0.97",
                                    "netmask": "255.255.0.0"
                                }
                            ]
                        },
                        {
                            "ilom": [
                                {
                                    "fqdn": "sea202225exdcl03lo.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                    "gateway": "10.0.176.1",
                                    "ipaddr": "10.0.179.147",
                                    "netmask": "255.255.240.0"
                                }
                            ]
                        },
                        {
                            "ntp": [
                                {
                                    "ipaddr": "169.254.169.254"
                                }
                            ]
                        },
                        {
                            "dns": [
                                {
                                    "ipaddr": "169.254.169.254"
                                }
                            ]
                        }
                    ]
                },
                "rack_info": {
                    "uheight": "1",
                    "uloc": "4"
                },
                "racktype": "1224",
                "storageSize": "22TB",
                "storageType": "HC"
            },
            {
                "cell_hostname": "sea202225exdcl02.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                "model": "X11M",
                "network_info": {
                    "cellnetworks": [
                        {
                            "admin": [
                                {
                                    "fqdn": "sea202225exdcl02.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                    "gateway": "10.0.176.1",
                                    "ipaddr": "10.0.179.131",
                                    "netmask": "255.255.240.0"
                                }
                            ]
                        },
                        {
                            "private": [
                                {
                                    "fqdn": "sea202225exdcl02-priv1.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                    "gateway": "100.106.0.1",
                                    "ipaddr": "100.106.0.94",
                                    "netmask": "255.255.0.0"
                                },
                                {
                                    "fqdn": "sea202225exdcl02-priv2.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                    "gateway": "100.106.0.1",
                                    "ipaddr": "100.106.0.95",
                                    "netmask": "255.255.0.0"
                                }
                            ]
                        },
                        {
                            "ilom": [
                                {
                                    "fqdn": "sea202225exdcl02lo.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                    "gateway": "10.0.176.1",
                                    "ipaddr": "10.0.179.146",
                                    "netmask": "255.255.240.0"
                                }
                            ]
                        },
                        {
                            "ntp": [
                                {
                                    "ipaddr": "169.254.169.254"
                                }
                            ]
                        },
                        {
                            "dns": [
                                {
                                    "ipaddr": "169.254.169.254"
                                }
                            ]
                        }
                    ]
                },
                "rack_info": {
                    "uheight": "1",
                    "uloc": "5"
                },
                "racktype": "1224",
                "storageSize": "22TB",
                "storageType": "HC"
            },
            {
                "cell_hostname": "sea202225exdcl01.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                "model": "X11M",
                "network_info": {
                    "cellnetworks": [
                        {
                            "admin": [
                                {
                                    "fqdn": "sea202225exdcl01.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                    "gateway": "10.0.176.1",
                                    "ipaddr": "10.0.179.130",
                                    "netmask": "255.255.240.0"
                                }
                            ]
                        },
                        {
                            "private": [
                                {
                                    "fqdn": "sea202225exdcl01-priv1.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                    "gateway": "100.106.0.1",
                                    "ipaddr": "100.106.0.92",
                                    "netmask": "255.255.0.0"
                                },
                                {
                                    "fqdn": "sea202225exdcl01-priv2.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                    "gateway": "100.106.0.1",
                                    "ipaddr": "100.106.0.93",
                                    "netmask": "255.255.0.0"
                                }
                            ]
                        },
                        {
                            "ilom": [
                                {
                                    "fqdn": "sea202225exdcl01lo.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                    "gateway": "10.0.176.1",
                                    "ipaddr": "10.0.179.145",
                                    "netmask": "255.255.240.0"
                                }
                            ]
                        },
                        {
                            "ntp": [
                                {
                                    "ipaddr": "169.254.169.254"
                                }
                            ]
                        },
                        {
                            "dns": [
                                {
                                    "ipaddr": "169.254.169.254"
                                }
                            ]
                        }
                    ]
                },
                "rack_info": {
                    "uheight": "1",
                    "uloc": "6"
                },
                "racktype": "1224",
                "storageSize": "22TB",
                "storageType": "HC"
            }
        ],
        "added_computes": [
            {
                "compute_node_alias": "dbserver-1",
                "compute_node_hostname": "sea202123exdd006.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                "model": "X11M",
                "network_info": {
                    "computenetworks": [
                        {
                            "admin": [
                                {
                                    "fqdn": "sea202123exdd006.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                    "gateway": "10.0.176.1",
                                    "ipaddr": "10.0.176.135",
                                    "master": "vmbondeth0",
                                    "netmask": "255.255.240.0"
                                }
                            ]
                        },
                        {
                            "private": [
                                {
                                    "fqdn": "sea202123exdd006-priv1.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                    "gateway": "192.168.132.1",
                                    "ipaddr": "192.168.132.18",
                                    "netmask": "255.255.254.0"
                                },
                                {
                                    "fqdn": "sea202123exdd006-priv2.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                    "gateway": "192.168.132.1",
                                    "ipaddr": "192.168.132.19",
                                    "netmask": "255.255.254.0"
                                }
                            ]
                        },
                        {
                            "ilom": [
                                {
                                    "fqdn": "sea202123exdd006lo.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                    "gateway": "10.0.176.1",
                                    "ipaddr": "10.0.176.149",
                                    "netmask": "255.255.240.0"
                                }
                            ]
                        },
                        {
                            "ntp": [
                                {
                                    "ipaddr": "169.254.169.254"
                                }
                            ]
                        },
                        {
                            "dns": [
                                {
                                    "ipaddr": "169.254.169.254"
                                }
                            ]
                        }
                    ]
                },
                "rack_info": {
                    "uheight": "1",
                    "uloc": "1"
                },
                "racktype": "1224",
                "virtual_compute_info": [
                    {
                        "compute_node_hostname": "sea202123exddu0601.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                        "network_info": {
                            "virtualcomputenetworks": [
                                {
                                    "private": [
                                        {
                                            "fqdn": "sea202123exddu0601-stre0.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                            "gateway": "erased",
                                            "ipaddr": "192.168.136.2",
                                            "netmask": "255.255.254.0"
                                        },
                                        {
                                            "fqdn": "sea202123exddu0601-stre1.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                            "gateway": "erased",
                                            "ipaddr": "192.168.136.3",
                                            "netmask": "255.255.254.0"
                                        }
                                    ]
                                },
                                {
                                    "client": [
                                        {
                                            "fqdn": "sea202123exddu0601.us.oracle.com",
                                            "gateway": "fe80::200:17ff:fee4:6f22",
                                            "ipaddr": "fe80::17ff:fe13:5d89",
                                            "mac": "00:10:7a:c0:2c:0d",
                                            "natdomain": "sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                            "nathostname": "sea202123exddu0601",
                                            "natip": "10.0.176.180",
                                            "netmask": "64",
                                            "slave": "eth2 eth1",
                                            "vlantag": "1"
                                        }
                                    ]
                                },
                                {
                                    "backup": [
                                        {
                                            "fqdn": "sea202123exddu0601-backup.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                            "gateway": "fe80::200:17ff:fee4:6f22",
                                            "ipaddr": "fe80::17ff:fe13:5d90",
                                            "mac": "02:00:17:01:69:c0",
                                            "netmask": "64",
                                            "slave": "eth2 eth1",
                                            "vlantag": "1"
                                        }
                                    ]
                                },
                                {
                                    "interconnect": [
                                        {
                                            "fqdn": "sea202123exddu0601-clre0.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                            "gateway": "erased",
                                            "ipaddr": "192.168.138.2",
                                            "netmask": "255.255.254.0"
                                        },
                                        {
                                            "fqdn": "sea202123exddu0601-clre1.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                            "gateway": "erased",
                                            "ipaddr": "192.168.138.3",
                                            "netmask": "255.255.254.0"
                                        }
                                    ]
                                },
                                {
                                    "vip": [
                                        {
                                            "fqdn": "sea202123exddu0601-vip.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                            "gateway": "fe80::200:17ff:fee4:6f22",
                                            "ipaddr": "fe80::17ff:fe13:5d91",
                                            "netmask": "64"
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ]
            },
            {
                "compute_node_alias": "dbserver-2",
                "compute_node_hostname": "sea202123exdd007.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                "model": "X11M",
                "network_info": {
                    "computenetworks": [
                        {
                            "admin": [
                                {
                                    "fqdn": "sea202123exdd007.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                    "gateway": "10.0.176.1",
                                    "ipaddr": "10.0.176.136",
                                    "master": "vmbondeth0",
                                    "netmask": "255.255.240.0"
                                }
                            ]
                        },
                        {
                            "private": [
                                {
                                    "fqdn": "sea202123exdd007-priv1.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                    "gateway": "192.168.132.1",
                                    "ipaddr": "192.168.132.16",
                                    "netmask": "255.255.254.0"
                                },
                                {
                                    "fqdn": "sea202123exdd007-priv2.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                    "gateway": "192.168.132.1",
                                    "ipaddr": "192.168.132.17",
                                    "netmask": "255.255.254.0"
                                }
                            ]
                        },
                        {
                            "ilom": [
                                {
                                    "fqdn": "sea202123exdd007lo.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                    "gateway": "10.0.176.1",
                                    "ipaddr": "10.0.176.150",
                                    "netmask": "255.255.240.0"
                                }
                            ]
                        },
                        {
                            "ntp": [
                                {
                                    "ipaddr": "169.254.169.254"
                                }
                            ]
                        },
                        {
                            "dns": [
                                {
                                    "ipaddr": "169.254.169.254"
                                }
                            ]
                        }
                    ]
                },
                "rack_info": {
                    "uheight": "1",
                    "uloc": "2"
                },
                "racktype": "1224",
                "virtual_compute_info": [
                    {
                        "compute_node_hostname": "sea202123exddu0701.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                        "network_info": {
                            "virtualcomputenetworks": [
                                {
                                    "private": [
                                        {
                                            "fqdn": "sea202123exddu0701-stre0.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                            "gateway": "erased",
                                            "ipaddr": "192.168.136.4",
                                            "netmask": "255.255.254.0"
                                        },
                                        {
                                            "fqdn": "sea202123exddu0701-stre1.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                            "gateway": "erased",
                                            "ipaddr": "192.168.136.5",
                                            "netmask": "255.255.254.0"
                                        }
                                    ]
                                },
                                {
                                    "client": [
                                        {
                                            "fqdn": "sea202123exddu0701.us.oracle.com",
                                            "gateway": "fe80::200:17ff:fee4:6f22",
                                            "ipaddr": "fe80::17ff:fe13:5d92",
                                            "mac": "00:10:f4:52:4a:b6",
                                            "natdomain": "sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                            "nathostname": "sea202123exddu0701",
                                            "natip": "10.0.176.181",
                                            "netmask": "64",
                                            "slave": "eth1 eth2",
                                            "vlantag": "2"
                                        }
                                    ]
                                },
                                {
                                    "backup": [
                                        {
                                            "fqdn": "sea202123exddu0701-backup.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                            "gateway": "fe80::200:17ff:fee4:6f22",
                                            "ipaddr": "fe80::17ff:fe13:5d93",
                                            "mac": "02:00:17:01:a6:52",
                                            "netmask": "64",
                                            "slave": "eth1 eth2",
                                            "vlantag": "1"
                                        }
                                    ]
                                },
                                {
                                    "interconnect": [
                                        {
                                            "fqdn": "sea202123exddu0701-clre0.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                            "gateway": "erased",
                                            "ipaddr": "192.168.138.4",
                                            "netmask": "255.255.254.0"
                                        },
                                        {
                                            "fqdn": "sea202123exddu0701-clre1.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                            "gateway": "erased",
                                            "ipaddr": "192.168.138.5",
                                            "netmask": "255.255.254.0"
                                        }
                                    ]
                                },
                                {
                                    "vip": [
                                        {
                                            "fqdn": "sea202123exddu0701-vip.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                            "gateway": "fe80::200:17ff:fee4:6f22",
                                            "ipaddr": "fe80::17ff:fe13:5d94",
                                            "netmask": "64"
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ]
            }
        ],
        "added_switches": [
            {
                "network_info": {
                    "switchnetworks": [
                        {
                            "admin": [
                                {
                                    "fqdn": "sea202123exdre02.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                    "gateway": "10.0.176.1",
                                    "ipaddr": "192.168.0.2",
                                    "netmask": "255.255.240.0"
                                }
                            ]
                        }
                    ]
                }
            },
            {
                "network_info": {
                    "switchnetworks": [
                        {
                            "admin": [
                                {
                                    "fqdn": "sea202123exdre01.sea2xx2xx0111qf.adminsea2.oraclevcn.com",
                                    "gateway": "10.0.176.1",
                                    "ipaddr": "192.168.0.1",
                                    "netmask": "255.255.240.0"
                                }
                            ]
                        }
                    ]
                }
            }
        ],
        "exadata_info": {
            "description": "X11M Elastic Rack HC 22TB",
            "model": "X11M",
            "rackid": "1",
            "rackname": "sea2-d3-cl3-d5d6dfb2-60c2-4cfd-82be-479a1c422022-clu01",
            "racktype": "1224"
        },
        "ostype": "kvm"
    },
    "wf_uuid": "5f4f67d2-2ca8-4924-9d01-a7389559e152"
}