#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/healthcheck/tests_healthcheck.py /main/24 2025/05/29 08:20:07 aararora Exp $
#
# test_dom0.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      test_dom0.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    naps        08/14/24 - Bug 36949876 - X11 ipconf path changes.
#    rkhemcha    02/01/24 - 36251119 - Add tests for update network flow with
#                           dr enabled
#    rkhemcha    05/25/22 - 34134702 - Update network validation changes due to
#                           refactoring v2
#    rkhemcha    04/07/22 - 33922918 - Adding unit test for update network flow
#    rkhemcha    03/02/22 - 33820696 - Fix nw vldn unit tests due to
#                           refactoring
#    naps        03/06/22 - remove virsh layer dependency.
#    aypaul      01/17/22 - Enh#33762417 Unit tests for healthcheck.py
#    aypaul      08/19/21 - Bug#33250436 Fix failing delete bond test.
#    aypaul      07/11/21 - Creation
#
import copy
import json
import unittest
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo
from exabox.healthcheck.cluhealthcheck import ebCluHealth
from exabox.healthcheck.healthcheck import HealthCheck
from exabox.ovm.cluhealth import ebCluHealthCheck, ebCluHealthNode
from exabox.ovm.clunetwork import ebCluNetwork
from exabox.healthcheck.hclogger import get_logger, init_logging
from exabox.healthcheck.clucheck import ebCluCheck
import warnings

HEALTHCHECK_FAIL = 1
HEALTHCHECK_SUCC = 0

FLASHCACHE_NORMAL = """         name:                   scaqab10celadm01_FLASHCACHE
         cellDisk:               FD_03_scaqab10celadm01,FD_00_scaqab10celadm01,FD_02_scaqab10celadm01,FD_01_scaqab10celadm01
         creationTime:           2021-07-06T04:50:51-07:00
         degradedCelldisks:      
         effectiveCacheSize:     5.82122802734375T
         id:                     dc842733-3727-45e0-8bfd-0a99601f8f7f
         size:                   5.82122802734375T
         status:                 normal"""
FLASHCACHE_DEGRADED = """         name:                   scaqab10celadm02_FLASHCACHE
         cellDisk:               FD_03_scaqab10celadm02,FD_00_scaqab10celadm02,FD_02_scaqab10celadm02,FD_01_scaqab10celadm02
         creationTime:           2021-07-06T04:50:51-07:00
         degradedCelldisks:      
         effectiveCacheSize:     5.82122802734375T
         id:                     dc842733-3727-45e0-8bfd-0a99601f8f7f
         size:                   5.82122802734375T
         status:                 warning - degraded"""
CELLDB_LIST_NORMAL = """         ASM"""
CELLDB_LIST_DBPRESENT = """         ASM
         UWHDYFN"""
CELLDB_LIST_ERROR = """CELL-02559: There is a communication error between MS and CELLSRV."""
XM_LIST_OP = """Name                                        ID   Mem VCPUs      State   Time(s)
Domain-0                                     0  8951     4     r----- 6462101.6
scaqab10client01vm08.us.oracle.com                 61 65539     8     r----- 623704.6"""
ORATAB_OP = """orcl16021950:/u01/michelorg/ecra_installs/mdcteam/db_home/oracle/product/19000/dbhome_1:N
orcla0d2:/u01/oracle/ecra_installs/iadsrg/db_home/oracle/product/19000/dbhome_1:N
orclywgf:/u01/oracle/ecra_installs/oracle/ecra_installs/idc/db_home/oracle/product/19000/dbhome_1:N"""
DSNDIG_OP = """scaqab10adm02.us.oracle.com. 228 IN A	10.0.7.144"""
EBTABLES_BRIDGECHAIN_OP = """Bridge chain: INPUT, entries: 0, policy: ACCEPT
Bridge chain: FORWARD, entries: 0, policy: ACCEPT
Bridge chain: OUTPUT, entries: 0, policy: ACCEPT"""
SMNODES_LIST_OP = """10.133.45.66
10.133.45.67
10.133.45.65"""
IBSWITCHES_OP = """Switch  : 0x0010e08028c7a0a0 ports 36 "SUN DCS 36P QDR scas22sw-iba0 10.133.45.66" enhanced port 0 lid 3 lmc 0
Switch  : 0x0010e08028b9a0a0 ports 36 "SUN DCS 36P QDR scas22sw-ibs0 10.133.45.65" enhanced port 0 lid 2 lmc 0
Switch  : 0x0010e080265ca0a0 ports 36 "SUN DCS 36P QDR scas22sw-ibb0 10.133.45.67" enhanced port 0 lid 1 lmc 0"""
IMAGEVERSION_OP = """Image version: 20.1.8.0.0.210317
Image status: success"""
SWTICH_VERSION_OP = """SUN DCS 36p version: 2.2.15-1
BIOS version: SUN0R100"""
SPACEONHOST_OP = """Filesystem                           Size  Used Avail Use% Mounted on
devtmpfs                             811G     0  811G   0% /dev
tmpfs                                1.7T  8.2k  1.7T   1% /dev/shm
tmpfs                                811G   16M  811G   1% /run
tmpfs                                811G     0  811G   0% /sys/fs/cgroup
/dev/mapper/VGExaDb-LVDbSys2          17G  8.3G  7.9G  51% /
/dev/mapper/VGExaDb-LVDbVar2         2.2G  603M  1.6G  29% /var
/dev/sda1                            535M   84M  452M  16% /boot
/dev/mapper/VGExaDb-LVDbHome         4.3G   35M  4.3G   1% /home
/dev/mapper/VGExaDb-LVDbTmp          3.3G   35M  3.2G   2% /tmp
/dev/sda2                            267M  9.0M  258M   4% /boot/efi
/dev/mapper/VGExaDb-LVDbVarLog        20G  5.5G   14G  28% /var/log
/dev/mapper/VGExaDb-LVDbVarLogAudit  1.1G  157M  907M  15% /var/log/audit
/dev/mapper/VGExaDb-LVDbExaVMImages  8.4T  1.1T  7.3T  13% /EXAVMIMAGES
tmpfs                                163G     0  163G   0% /run/user/0"""
VMSTAT_OP = """   1583566336 K total memory
   1475153024 K used memory
      2736320 K active memory
      9389216 K inactive memory
     96144432 K free memory
         9348 K buffer memory
     12259604 K swap cache
     16777212 K total swap
       366592 K used swap
     16410620 K free swap
    261903370 non-nice user cpu ticks
      4180197 nice user cpu ticks
    274851555 system cpu ticks
 114606079003 idle cpu ticks
      1415044 IO-wait cpu ticks
            0 IRQ cpu ticks
       595342 softirq cpu ticks
            0 stolen cpu ticks
   2438198722 pages paged in
   9499132078 pages paged out
        51290 pages swapped in
       124222 pages swapped out
    967576621 interrupts
    587371536 CPU context switches
   1631603543 boot time
   1405039029 forks"""
CRSCTL_CHECKCLUSTER_OP = """**************************************************************
scaqab10client01vm08:
CRS-4537: Cluster Ready Services is online
CRS-4529: Cluster Synchronization Services is online
CRS-4533: Event Manager is online
**************************************************************
scaqab10client02vm08:
CRS-4537: Cluster Ready Services is online
CRS-4529: Cluster Synchronization Services is online
CRS-4533: Event Manager is online
**************************************************************"""
DBSTATUS_OP = """NAME=ora.db190155_uniq.db
TYPE=ora.database.type
TARGET=ONLINE             , ONLINE
STATE=ONLINE on scaqab10client02vm08, ONLINE on scaqab10client01vm08

NAME=ora.db190900_uniq.db
TYPE=ora.database.type
TARGET=ONLINE             , ONLINE
STATE=ONLINE on scaqab10client02vm08, ONLINE on scaqab10client01vm08"""
SVRCTL_STATUS_SCAN_OP = """SCAN VIP scan1 is enabled
SCAN VIP scan1 is running on node scaqab10client02vm08
SCAN VIP scan2 is enabled
SCAN VIP scan2 is running on node scaqab10client01vm08"""
SVRCTL_VIP_OP = """VIP 10.0.123.108 is enabled
VIP 10.0.123.108 is running on node: scaqab10client01vm08"""
CLUVFY_COMP_OP = """
Verifying Single Client Access Name (SCAN) ...
  Verifying DNS/NIS name service 'scaqab10client01vm08-scan' ...
    Verifying Name Service Switch Configuration File Integrity ...PASSED
  Verifying DNS/NIS name service 'scaqab10client01vm08-scan' ...PASSED
Verifying Single Client Access Name (SCAN) ...PASSED

Verification of SCAN was successful.

CVU operation performed:      SCAN
Date:                         Jan 20, 2022 11:48:09 AM
CVU home:                     /u01/app/19.0.0.0/grid/
User:                         grid"""
DBAASCLI_DBSTATUS_CHECK_OP = """DBAAS CLI version 21.4.1.1.0
Executing command database status
Database Status:
Instance db1909001 is running on node scaqab10client01vm08 with online services db190900_pdb.paas.oracle.com,db190900_PDB205.paas.oracle.com,db190900_PDB705.paas.oracle.com. Instance status: Open.
Instance db1909002 is running on node scaqab10client02vm08 with online services db190900_pdb.paas.oracle.com,db190900_PDB205.paas.oracle.com,db190900_PDB705.paas.oracle.com. Instance status: Open.

Database name: db190900
Oracle Database 19c EE Extreme Perf Release 19.0.0.0.0 - Production"""
ETC_ORATAB_OP = """+ASM1:/u01/app/19.0.0.0/grid:N
db190900_uniq:/u02/app/oracle/product/19.0.0.0/dbhome_1:Y
db190155_uniq:/u02/app/oracle/product/19.0.0.0/dbhome_1:Y"""
GRIDDISK_STATUS_OP = """    DATAC01_CD_00_iad103706exdcl04	 ONLINE	 Yes
     DATAC01_CD_01_iad103706exdcl04	 ONLINE	 Yes
     DATAC01_CD_02_iad103706exdcl04	 ONLINE	 Yes
     DATAC01_CD_03_iad103706exdcl04	 ONLINE	 Yes
     DATAC01_CD_04_iad103706exdcl04	 ONLINE	 Yes
     DATAC01_CD_05_iad103706exdcl04	 ONLINE	 Yes
     DATAC01_CD_06_iad103706exdcl04	 ONLINE	 Yes
     DATAC01_CD_07_iad103706exdcl04	 ONLINE	 Yes"""
ASM_CHECK_OP = """no rows selected"""
ASM_MODE_OP = """SYS_CONTEXT('SYS_CLUSTER_PROPERTIES','CLUSTER_STATE')
--------------------------------------------------------------------------------
Normal"""
ASM_POWERLIMIT_OP = """asm_power_limit 		     integer	 4"""
EXAVMIMAGES_DISK_USAGE_OP = """Filesystem                           Size  Used Avail Use% Mounted on
/dev/mapper/VGExaDb-LVDbExaVMImages  8.4T  364G  8.0T   5% /EXAVMIMAGES"""
NODETYPE_OP = """Node type: KVMHOST"""
VIRSH_LIST_OP = """scaqab10client01vm08.us.oracle.com(8)       :    running
scaqab10client02vm08.us.oracle.com(12)       :    running"""
VIRSH_NODEINFO_OP = """CPU model:           x86_64
CPU(s):              104
CPU frequency:       3080 MHz
CPU socket(s):       1
Core(s) per socket:  26
Thread(s) per core:  2
NUMA cell(s):        2
Memory size:         1583466708 KiB"""
REFRESH_DOMU_VIRSH_LISTACTIVE_OP = """ 8    scaqab10client01vm08.us.oracle.com   running
 12   scaqab10client02vm08.us.oracle.com   running"""
VIRSH_CPUINFO_OP = """0
1
2
3
4
5
6
7
8
9
50
51
52
53
54
55
56
57
58
59"""
DOM0_MEMINFO_OP = """MemTotal:       1583466708 kB
MemFree:        11973644 kB
MemAvailable:   84620340 kB"""
BRCTL_OP = """bridge name	bridge id		STP enabled	interfaces
virbr0		8000.525400ef38da	yes		virbr0-nic
vmbondeth0		8000.0010e0ef021b	no		bondeth0
vmbondeth0.724		8000.0010e0ef021b	no		bondeth0.724
							vnet100
vmbondeth0.725		8000.0010e0ef021b	no		bondeth0.725
							vnet101
vmbondeth0.726		8000.0010e0ef021b	no		bondeth0.726
							vnet103
vmbondeth0.727		8000.0010e0ef021b	no		bondeth0.727
							vnet104
vmeth0		8000.0010e0ef021a	no		eth0
vmeth200		8000.76da4ec74454	no		eth200
							vnet102
vmeth201		8000.e6a8f9e76ef1	no		eth201
							vnet105"""
ROUTE_OP = """Kernel IP routing table
Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
default         gateway         0.0.0.0         UG    0      0        0 vmeth0
10.0.6.0        0.0.0.0         255.255.255.128 U     0      0        0 vmeth0
100.104.0.0     0.0.0.0         255.255.252.0   U     0      0        0 re0
100.104.0.0     0.0.0.0         255.255.252.0   U     0      0        0 re1
169.254.200.0   0.0.0.0         255.255.255.252 U     0      0        0 vmeth200
169.254.200.4   0.0.0.0         255.255.255.252 U     0      0        0 vmeth201
192.168.122.0   0.0.0.0         255.255.255.0   U     0      0        0 virbr0"""
IORMPLAN_DETAIL_OP = """	 name:                   scaqab10celadm01_IORMPLAN
	 catPlan:
	 dbPlan:
	 clusterPlan:
	 objective:              auto
	 status:                 active"""

DOM0_NETWORK_INFO = {
    'scaqab10adm01.us.oracle.com': {
        'admin': {
            'bridge': 'vmeth1',
            'bond_master': 'eth1',
            'bond_slaves': ''
        },
        'client': {
            'bridge': 'vmbondeth0',
            'bond_master': 'bondeth0',
            'bond_slaves': 'eth4 eth5'
        },
        'backup': {
            'bridge': 'vmbondeth1',
            'bond_master': 'bondeth1',
            'bond_slaves': 'eth6 eth7'
        }
    },
    'scaqab10adm02.us.oracle.com': {
        'admin': {
            'bridge': 'vmeth1',
            'bond_master': 'eth1',
            'bond_slaves': ''
        },
        'client': {
            'bridge': 'vmbondeth0',
            'bond_master': 'bondeth0',
            'bond_slaves': 'eth4 eth5'
        },
        'backup': {
            'bridge': 'vmbondeth1',
            'bond_master': 'bondeth1',
            'bond_slaves': 'eth6 eth7'
        }
    }
}

DOM0_NETWORK_INFO_ERROR = {
   "ERROR": {
      "scaqab10adm01.us.oracle.com": {
         "CAUSE": "No network found matching runtime interfaces state.",
         "ACTION": "Check the states of physical interfaces on the respective dom0"
      }
   }
}

INT_RESULT = {
   "mCheckGatewayTest": {
      "hcTestResult": 0,
      "hcLogs": [],
      "hcMsgDetail": {
         "hcDisplayString": [],
         "client": {
            "vmbondeth0": {
               "status": "Fail"
            }
         },
         "backup": {
            "vmbondeth1": {
               "status": "Pass"
            }
         }
      },
      "hcCheckParam": {}
   }
}


class testOptions(object): pass


class ebTestDom0HealthCheck(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestDom0HealthCheck, self).setUpClass(True, True)
        warnings.filterwarnings("ignore")

    def test_mCheckSundiagOsw_mCheckIptables_mCheckVarLogMessages_mCheckAllCellosLogs_mCheckIpAddrShow_mCheckIbstat(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckSundiagOsw_mCheckIptables_mCheckVarLogMessages_mCheckAllCellosLogs_mCheckIpAddrShow_mCheckIbstat")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexDom0(): [
                        [
                            exaMockCommand("/opt/oracle.SupportTools/sundiag.sh", aStdout="Mock output", aRc=0, aPersist=True)
                        ],
                        [
                            exaMockCommand("iptables -L", aStdout="Mock output", aRc=0, aPersist=True)
                        ],
                        [
                            exaMockCommand("tail -n", aStdout="Mock output", aRc=0, aPersist=True)
                        ],
                        [
                            exaMockCommand("tail -n", aStdout="Mock output", aRc=0, aPersist=True)
                        ],
                        [
                            exaMockCommand("ip addr show", aStdout="Mock output", aRc=0, aPersist=True)
                        ],
                        [
                            exaMockCommand("ibstat", aStdout="Mock output", aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mCheckSundiagOsw(self.mGetClubox().mReturnDom0DomUPair()[0][0])
        currentHealthObject.mCheckIptables(self.mGetClubox().mReturnDom0DomUPair()[0][0])
        currentHealthObject.mCheckVarLogMessages(self.mGetClubox().mReturnDom0DomUPair()[0][0])
        currentHealthObject.mCheckAllCellosLogs(self.mGetClubox().mReturnDom0DomUPair()[0][0])
        currentHealthObject.mCheckIpAddrShow(self.mGetClubox().mReturnDom0DomUPair()[0][0])
        currentHealthObject.mCheckIbstat(self.mGetClubox().mReturnDom0DomUPair()[0][0])

    def test_mCheckIORMPlan(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckIORMPlan")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexCell(): [
                        [
                            exaMockCommand("cellcli -e list iormplan detail", aStdout=IORMPLAN_DETAIL_OP, aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mCheckIORMPlan("scaqab10celadm01.us.oracle.com")

    def test_mCheckCellosTgz_mCheckIpconfpl(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckCellosTgz_mCheckIpconfpl")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexDom0(): [
                        [
                            exaMockCommand("find /var/log/ -iname", aStdout="/var/log/cellos.1.tgz", aRc=0, aPersist=True)
                        ],
                        [
                            exaMockCommand("/opt/oracle.cellos/ipconf", aStdout="Mock output", aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mCheckCellosTgz(self.mGetClubox().mReturnDom0DomUPair()[0][0])
        currentHealthObject.mCheckIpconfpl(self.mGetClubox().mReturnDom0DomUPair()[0][0])

    def test_mCheckListEXAVMIMAGESContents(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckListEXAVMIMAGESContents")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexDom0(): [
                        [
                            exaMockCommand("/usr/bin/ls -R", aStdout="Mock output", aRc=0, aPersist=True),
                            exaMockCommand("ls -R /EXAVMIMAGES/GuestImgs", aStdout="Mock output", aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mCheckListEXAVMIMAGESContents(self.mGetClubox().mReturnDom0DomUPair()[0][0])

    def test_mCheckCellFlashLog_mCheckCellFlashCache_mCheckCellGridDisk_mCheckCellPhysicalDisk_mCheckCellAlertHistory_mCheckCellDetail_mCheckCellDatabase(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckCellFlashLog_mCheckCellFlashCache_mCheckCellGridDisk_mCheckCellPhysicalDisk_mCheckCellAlertHistory_mCheckCellDetail_mCheckCellDatabase")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexCell(): [
                        [
                            exaMockCommand("cellcli -e list flashlog", aStdout="Mock output", aRc=0, aPersist=True)
                        ],
                        [
                            exaMockCommand("cellcli -e list flashcache", aStdout="Mock output", aRc=0, aPersist=True)
                        ],
                        [
                            exaMockCommand("cellcli -e list griddisk", aStdout="Mock output", aRc=0, aPersist=True)
                        ],
                        [
                            exaMockCommand("cellcli -e list physicaldisk", aStdout="Mock output", aRc=0, aPersist=True)
                        ],
                        [
                            exaMockCommand("cellcli -e list alerthistory", aStdout="Mock output", aRc=0, aPersist=True),
                            exaMockCommand("/usr/local/bin/imageinfo -version", aStdout="22.1.0", aRc=0, aPersist=True),
                        ],
                        [
                            exaMockCommand("cellcli -e list cell detail", aStdout="Mock output", aRc=0, aPersist=True),
                            exaMockCommand("cellcli  -e list alerthistory", aStdout="Mock output", aRc=0, aPersist=True)
                        ],
                        [
                            exaMockCommand("cellcli -e list database", aStdout="Mock output", aRc=0, aPersist=True),
                            exaMockCommand("cellcli -e list cell detail", aStdout="Mock output", aRc=0, aPersist=True)
                        ],
                        [
                            exaMockCommand("cellcli -e list database", aStdout="Mock output", aRc=0, aPersist=True),
                            exaMockCommand("cellcli -e list cell detail", aStdout="Mock output", aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mCheckCellFlashLog("scaqab10celadm01.us.oracle.com")
        currentHealthObject.mCheckCellFlashCache("scaqab10celadm01.us.oracle.com")
        currentHealthObject.mCheckCellGridDisk("scaqab10celadm01.us.oracle.com")
        currentHealthObject.mCheckCellPhysicalDisk("scaqab10celadm01.us.oracle.com")
        currentHealthObject.mCheckCellAlertHistory("scaqab10celadm01.us.oracle.com")
        currentHealthObject.mCheckCellDetail("scaqab10celadm01.us.oracle.com")
        currentHealthObject.mCheckCellDatabase("scaqab10celadm01.us.oracle.com")

    def test_mCheckBrctlShow_mCheckIfconfig_mCheckRoute(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckBrctlShow_mCheckIfconfig_mCheckRoute")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexDom0(): [
                        [
                            exaMockCommand("brctl show", aStdout=BRCTL_OP, aRc=0, aPersist=True)
                        ],
                        [
                            exaMockCommand("ifconfig", aStdout="Dummy output", aRc=0, aPersist=True)
                        ],
                        [
                            exaMockCommand("route", aStdout=ROUTE_OP, aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mCheckBrctlShow(self.mGetClubox().mReturnDom0DomUPair()[0][0])
        currentHealthObject.mCheckIfconfig(self.mGetClubox().mReturnDom0DomUPair()[0][0])
        currentHealthObject.mCheckRoute(self.mGetClubox().mReturnDom0DomUPair()[0][0])

    def test_mCheckCellOSConf(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckCellOSConf")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexDom0(): [
                        [
                            exaMockCommand("cat /opt/oracle.cellos/cell.conf", aStdout="Dummy cellos.conf", aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mCheckCellOSConf(self.mGetClubox().mReturnDom0DomUPair()[0][0])

    def test_mCheckDom0MemInfo(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckDom0MemInfo")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexDom0(): [
                        [
                            exaMockCommand("cat /proc/meminfo | grep Mem", aStdout=DOM0_MEMINFO_OP, aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mCheckDom0MemInfo(self.mGetClubox().mReturnDom0DomUPair()[0][0])

    def test_mCheckDomUUptime(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckDomUUptime")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexDom0(): [
                        [
                            exaMockCommand("imageinfo | grep 'Node type:'", aStdout=NODETYPE_OP, aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mCheckDomUUptime(self.mGetClubox().mReturnDom0DomUPair()[0][0])

    def test_mCheckXenVcpuList(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckXenVcpuList")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexDom0(): [
                        [
                            exaMockCommand("imageinfo | grep 'Node type:'", aStdout=NODETYPE_OP, aRc=0, aPersist=True)
                        ],
                        [
                            exaMockCommand("/usr/sbin/vm_maker --list-domains | /bin/grep 'running'.*", aStdout=REFRESH_DOMU_VIRSH_LISTACTIVE_OP, aRc=0, aPersist=True),
                            exaMockCommand("virsh vcpuinfo", aStdout=VIRSH_CPUINFO_OP, aRc=0, aPersist=True),
                            exaMockCommand("virsh list", aStdout=VIRSH_LIST_OP, aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mCheckXenVcpuList(self.mGetClubox().mReturnDom0DomUPair()[0][0])

    def test_mCheckXenLog(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckXenLog")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexDom0(): [
                        [
                            exaMockCommand("imageinfo | grep 'Node type:'", aStdout=NODETYPE_OP, aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mCheckXenLog(self.mGetClubox().mReturnDom0DomUPair()[0][0])

    def test_mCheckXenInfo(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckXenInfo")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexDom0(): [
                        [
                            exaMockCommand("imageinfo | grep 'Node type:'", aStdout=NODETYPE_OP, aRc=0, aPersist=True)
                        ],
                        [
                            exaMockCommand("virsh nodeinfo", aStdout=VIRSH_NODEINFO_OP, aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mCheckXenInfo(self.mGetClubox().mReturnDom0DomUPair()[0][0])

    def test_mCheckDomUList(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckDomUList")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexDom0(): [
                        [
                            exaMockCommand("imageinfo | grep 'Node type:'", aStdout=NODETYPE_OP, aRc=0, aPersist=True)
                        ],
                        [
                            exaMockCommand("/usr/sbin/vm_maker --list-domains | /bin/grep running", aStdout=VIRSH_LIST_OP, aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mCheckDomUList(self.mGetClubox().mReturnDom0DomUPair()[0][0])

    def test_mCheckEXAVMIMAGESSpace(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckEXAVMIMAGESSpace")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexDom0(): [
                        [
                            exaMockCommand("df -kHP /EXAVMIMAGES", aStdout=EXAVMIMAGES_DISK_USAGE_OP, aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mCheckEXAVMIMAGESSpace(self.mGetClubox().mReturnDom0DomUPair()[0][0])

    def test_mValidateXML(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mValidateXML")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        fullOptions.healthcheck = "custom"
        fullOptions.jsonconf = {"targetHosts": "dom0"}

        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        baseHealthCheckObject = ebCluHealthCheck(self.mGetClubox(), fullOptions)
        baseHealthCheckObject.mValidateXML()

    def test_mCheckAsmPowerLimit(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckAsmPowerLimit")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexVm(): [
                        [
                            exaMockCommand("export ORACLE_SID", aStdout=ASM_POWERLIMIT_OP, aRc=0, aPersist=True),
                            exaMockCommand("cat /etc/oratab", aStdout=ETC_ORATAB_OP, aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mCheckAsmPowerLimit(self.mGetClubox().mReturnDom0DomUPair()[0][1])

    def test_mCheckAsmMode(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckAsmMode")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexVm(): [
                        [
                            exaMockCommand("export ORACLE_SID", aStdout=ASM_MODE_OP, aRc=0, aPersist=True),
                            exaMockCommand("cat /etc/oratab", aStdout=ETC_ORATAB_OP, aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mCheckAsmMode(self.mGetClubox().mReturnDom0DomUPair()[0][1])

    def test_mCheckAsmOperation(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckAsmOperation")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexVm(): [
                        [
                            exaMockCommand("export ORACLE_SID", aStdout=ASM_CHECK_OP, aRc=0, aPersist=True),
                            exaMockCommand("cat /etc/oratab", aStdout=ETC_ORATAB_OP, aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mCheckAsmOperation(self.mGetClubox().mReturnDom0DomUPair()[0][1])

    def test_mCheckCellDeactivation(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckCellDeactivation")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        _hosts = ["scaqab10celadm01.us.oracle.com","scaqab10celadm02.us.oracle.com"]

        for _host in _hosts:
            _cmds = {
                        self.mGetRegexLocal(): [
                            [
                                exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                            ]
                        ],
                        self.mGetRegexCell(): [
                            [
                                exaMockCommand("cellcli -e list griddisk attributes name, asmmodestatus, asmdeactivationoutcome", aStdout=GRIDDISK_STATUS_OP if _host == "scaqab10celadm01.us.oracle.com" else None, aRc=0, aPersist=True)
                            ]
                        ]
                    }
            self.mPrepareMockCommands(_cmds)
            currentHealthObject.mCheckCellDeactivation(_host)

    def test_mCheckCDBStatusCheck(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckCDBStatusCheck")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexVm(): [
                        [
                            exaMockCommand("dbaascli database status", aStdout=DBAASCLI_DBSTATUS_CHECK_OP, aRc=0, aPersist=True),
                            exaMockCommand("cat /etc/oratab", aStdout=ETC_ORATAB_OP, aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mCheckCDBStatusCheck(self.mGetClubox().mReturnDom0DomUPair()[0][1])

    def test_mCheckSCANCluvfy(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckSCANCluvfy")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexVm(): [
                        [
                            exaMockCommand("cluvfy comp scan", aStdout=CLUVFY_COMP_OP, aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mCheckSCANCluvfy(self.mGetClubox().mReturnDom0DomUPair()[0][1])

    def test_mCheckVipStatus(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckVipStatus")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexVm(): [
                        [
                            exaMockCommand("srvctl status vip -n", aStdout=SVRCTL_VIP_OP, aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mCheckVipStatus(self.mGetClubox().mReturnDom0DomUPair()[0][1])

    def test_mCheckScanStatus(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckScanStatus")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexVm(): [
                        [
                            exaMockCommand("srvctl status scan", aStdout=SVRCTL_STATUS_SCAN_OP, aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mCheckScanStatus(self.mGetClubox().mReturnDom0DomUPair()[0][1])

    def test_mDbInstanceStatusCheck(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mDbInstanceStatusCheck")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexVm(): [
                        [
                            exaMockCommand("crsctl   stat res", aStdout=DBSTATUS_OP, aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mDbInstanceStatusCheck(self.mGetClubox().mReturnDom0DomUPair()[0][1])

    def test_mCheckGridInfra(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckGridInfra")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexVm(): [
                        [
                            exaMockCommand("crsctl check cluster -all", aStdout=CRSCTL_CHECKCLUSTER_OP, aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mCheckGridInfra(self.mGetClubox().mReturnDom0DomUPair()[0][1])

    def test_mCheckMemory(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckMemory")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexDom0(): [
                        [
                            exaMockCommand("vmstat -s", aStdout=VMSTAT_OP, aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mCheckMemory(self.mGetClubox().mReturnDom0DomUPair()[0][0])

    def test_mCheckNodeSpace(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckNodeSpace")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexDom0(): [
                        [
                            exaMockCommand("df -kHP", aStdout=SPACEONHOST_OP, aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mCheckNodeSpace(self.mGetClubox().mReturnDom0DomUPair()[0][0])

    def test_mCheckImageVersion(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckImageVersion")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        def mCalculateSwitches(aClubox, aFilter):
            _switches = []
            _list = aClubox.mGetSwitches().mGetSwitchesNetworkId(aFilter)
            for _h in _list:
                _neto = self.mGetClubox().mGetNetworks().mGetNetworkConfig(_h)
                _switches.append(_neto.mGetNetHostName()+'.'+_neto.mGetNetDomainName())
            return _switches
        switchList = mCalculateSwitches(self.mGetClubox(), False)

        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexDom0(): [
                        [
                            exaMockCommand("/usr/local/bin/imageinfo -version -status", aStdout=IMAGEVERSION_OP, aRc=0, aPersist=True),
                            exaMockCommand("/usr/local/bin/imageinfo -verexasplice", aStdout="201026", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexSwitch():[
                        [
                            exaMockCommand("/usr/local/bin/version | grep -i version", aStdout=SWTICH_VERSION_OP, aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mCheckImageVersion(self.mGetClubox().mReturnDom0DomUPair()[0][0])
        currentHealthObject.mCheckImageVersion(switchList[1])

    def test_mValidateNwOverlap(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mValidateNwOverlap")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        fullOptions.healthcheck = "custom"
        fullOptions.jsonconf = {"targetHosts": "dom0"}
        baseHealthCheckObject = ebCluHealthCheck(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)
        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=1, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mValidateNwOverlap()

    def test_mCheckDiskGroup(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckDiskGroup")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        fullOptions.healthcheck = "custom"
        fullOptions.jsonconf = {"targetHosts": "dom0"}
        baseHealthCheckObject = ebCluHealthCheck(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        currentHealthObject.mCheckDiskGroup()

    def test_mCheckMachineConfig(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckMachineConfig")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        fullOptions.healthcheck = "custom"
        fullOptions.jsonconf = {"targetHosts": "dom0"}
        baseHealthCheckObject = ebCluHealthCheck(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        currentHealthObject.mCheckMachineConfig()

    def test_mCheckUserandGroupXML(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckUserandGroupXML")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        fullOptions.healthcheck = "custom"
        fullOptions.jsonconf = {"targetHosts": "dom0"}
        baseHealthCheckObject = ebCluHealthCheck(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        currentHealthObject.mCheckUserandGroupXML()

    def test_mCheckScanNames(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckScanNames")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        fullOptions.healthcheck = "custom"
        fullOptions.jsonconf = {"targetHosts": "dom0"}
        baseHealthCheckObject = ebCluHealthCheck(self.mGetClubox(), fullOptions)
        baseHealthCheckObject.mSetPreProv(False)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)
        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=1, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mCheckScanNames()

    def test_mCheckSubnetMask(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckSubnetMask")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        currentHealthObject.mCheckSubnetMask()

    def test_mGetSubnet(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mGetSubnet")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        self.assertEqual(currentHealthObject.mGetSubnet('10.248.152.26', '255.255.248.0'), "10.248.152.0")

    def test_mCheckDatabases(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckDatabases")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        currentHealthObject.mCheckDatabases()

    def test_mCheckNtpServers(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckNtpServers")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        jsonMap = dict()
        currentHealthObject.mCheckNtpServers(None, None, jsonMap)

    def test_mCheckDnsServers(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckDnsServers")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        jsonMap = dict()
        currentHealthObject.mCheckDnsServers(None, None, jsonMap)

    def test_mCheckVmImage(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckVmImage")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        fullOptions.healthcheck = "custom"
        fullOptions.jsonconf = {"targetHosts": "dom0"}
        baseHealthCheckObject = ebCluHealthCheck(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)
        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexDom0():[
                        [
                            exaMockCommand("ls /EXAVMIMAGES/System.first.boot", aStdout="/EXAVMIMAGES/System.first.boot.20.1.8.0.0.210317.img", aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        thisNode = currentHealthObject.mGetNode(self.mGetClubox().mReturnDom0DomUPair()[0][0])
        recommendList = list()
        currentHealthObject.mCheckVmImage(self.mGetClubox().mReturnDom0DomUPair()[0][0], thisNode, None, None, recommendList, None)

    def test_mCheckSmnodesList(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckSmnodesList")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        def mCalculateSwitches(aClubox, aFilter):
            _switches = []
            _list = aClubox.mGetSwitches().mGetSwitchesNetworkId(aFilter)
            for _h in _list:
                _neto = self.mGetClubox().mGetNetworks().mGetNetworkConfig(_h)
                _switches.append(_neto.mGetNetHostName()+'.'+_neto.mGetNetDomainName())
            return _switches

        switchList = mCalculateSwitches(self.mGetClubox(), False)
        ebLogInfo(switchList)
        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexSwitch():[
                        [
                            exaMockCommand("smnodes list", aRc=0, aPersist=True),
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mCheckSmnodesList(switchList[1])

        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexSwitch():[
                        [
                            exaMockCommand("smnodes list", aStdout=SMNODES_LIST_OP, aRc=0, aPersist=True),
                            exaMockCommand("ibswitches", aStdout=IBSWITCHES_OP, aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mCheckSmnodesList(switchList[2])

    def test_mCheckEbtables(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckEbtables")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)
        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexDom0():[
                        [
                            exaMockCommand("/opt/exacloud/network/vif-whitelist", aRc=0, aPersist=True),
                            exaMockCommand("ebtables -L", aStdout=EBTABLES_BRIDGECHAIN_OP, aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        sharedEnvValue = self.mGetClubox().mGetSharedEnv()
        self.mGetClubox().mSetSharedEnv(False)
        currentHealthObject.mCheckEbtables(self.mGetClubox().mReturnDom0DomUPair()[0][0])
        self.mGetClubox().mSetSharedEnv(sharedEnvValue)

        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexDom0():[
                        [
                            exaMockCommand("/opt/exacloud/network/vif-whitelist", aStdout="EBTables exist.", aRc=0, aPersist=True),
                            exaMockCommand("ebtables -L", aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        sharedEnvValue = self.mGetClubox().mGetSharedEnv()
        self.mGetClubox().mSetSharedEnv(False)
        currentHealthObject.mCheckEbtables(self.mGetClubox().mReturnDom0DomUPair()[1][0])
        self.mGetClubox().mSetSharedEnv(sharedEnvValue)

    def test_mCheckNetConsistency(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckNetConsistency")

        baseHealthCheckObject = ebCluHealthNode()
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)
        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexDom0():[
                        [
                            exaMockCommand("/opt/oracle.cellos/ipconf", aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mCheckNetConsistency(self.mGetClubox().mReturnDom0DomUPair()[0][0])

        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexDom0():[
                        [
                            exaMockCommand("/opt/oracle.cellos/ipconf", aStdout="PASSED", aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        currentHealthObject.mCheckNetConsistency(self.mGetClubox().mReturnDom0DomUPair()[1][0])

    # Start - Network Validation unit tests

    def test_aHelperfunctions(self):
        ebLogInfo("")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        dom0 = "scaqab10adm01.us.oracle.com"
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        baseHealthCheckObject.mSetDom0s([dom0])
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)
        nwVldnHelperObject = currentHealthObject.NetworkValidationHelpers(dom0, get_logger(), currentHealthObject)

        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping -c 1 -W 4 scaqab10adm01.us.oracle.com", aRc=0, aPersist=True)
                ],
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth0/operstate", aRc=1, aStdout="down", aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth1/operstate", aRc=0, aStdout="up", aPersist=True),
                    exaMockCommand("/opt/exadata_ovm/exadata.img.domu_maker add-bonded-bridge-dom0", aRc=0, aPersist=True)
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)

        self.assertEqual(nwVldnHelperObject.convNetmasktoPrefix('255.255.255.128'), 25)
        self.assertEqual(nwVldnHelperObject.ipTo32bitBinary('255.255.255.255'), "11111111111111111111111111111111")
        self.assertEqual(nwVldnHelperObject.checkifSameNw('10.0.4.134', '10.0.4.133', '255.255.255.128'), True)
        self.assertEqual(nwVldnHelperObject.checkifSameNw('10.3.4.134', '10.0.4.133', '255.255.255.128'), False)


    def test_is_valid_ipv4_address_is_valid_ipv6_address(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.is_valid_ipv4_address and HealthCheck.is_valid_ipv6_address")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        dom0 = "scaqab10adm01.us.oracle.com"
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        baseHealthCheckObject.mSetDom0s([dom0])
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)
        nwVldnHelpersObject = currentHealthObject.NetworkValidationHelpers(dom0, get_logger(), currentHealthObject)

        ipAddressesResults = {
            "192.168.1.0": True,
            "203.0.113.0.1": False,
            "2001:db8:3333:4444:5555:6666:7777:8888": True,
            "56FE::2159:5BBC::6594": False
        }

        ipv4Addresses = ["192.168.1.0", "203.0.113.0.1"]
        ipv6Addresses = ["2001:db8:3333:4444:5555:6666:7777:8888", "56FE::2159:5BBC::6594"]
        for ipv4Address in ipv4Addresses:
            ebLogInfo("Validating ipaddress {}".format(ipv4Address))
            returnedResult = nwVldnHelpersObject.is_valid_ipv4_address(ipv4Address)
            self.assertEqual(ipAddressesResults[ipv4Address], returnedResult)

        for ipv6Address in ipv6Addresses:
            ebLogInfo("Validating ipaddress {}".format(ipv6Address))
            returnedResult = nwVldnHelpersObject.is_valid_ipv6_address(ipv6Address)
            self.assertEqual(ipAddressesResults[ipv6Address], returnedResult)

    def test_mCheckCreateBondTestXEN(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckCreateBondTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        dom0 = "scaqab10adm01.us.oracle.com"
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        baseHealthCheckObject.mSetDom0s([dom0])
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        resultsExpected = {"scaqab10adm01.us.oracle.com": HEALTHCHECK_SUCC}

        # executing for one dom0 since flow is same
        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping -c 1 -W 4 scaqab10adm01.us.oracle.com", aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth0/operstate", aRc=1, aStdout="down", aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth1/operstate", aRc=0, aStdout="up", aPersist=True),
                    exaMockCommand("/opt/exadata_ovm/exadata.img.domu_maker add-bonded-bridge-dom0", aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0", aPersist=True)
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)
        returnedResult = currentHealthObject.mCheckCreateBondTest(dom0)
        ebLogInfo("Healthcheck results: {}".format(returnedResult))
        self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])

    def test_mCheckCreateBondTestKVM(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckCreateBondTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        dom0 = "scaqab10adm02.us.oracle.com"
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        baseHealthCheckObject.mSetDom0s([dom0])
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)
        # will test failure path for bridge creation with this test
        resultsExpected = {"scaqab10adm02.us.oracle.com": HEALTHCHECK_FAIL}

        # executing for one dom0 since flow is same

        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping -c 1 -W 4 scaqab10adm02.us.oracle.com", aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth0/operstate", aRc=1, aStdout="down", aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth1/operstate", aRc=0, aStdout="up", aPersist=True),
                    exaMockCommand("/usr/sbin/vm_maker --add-bonded-bridge", aRc=1, aPersist=True)
                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: KVMHOST", aPersist=True)
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)
        returnedResult = currentHealthObject.mCheckCreateBondTest(dom0)
        ebLogInfo("Healthcheck results: {}".format(returnedResult))
        self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])

    def test_mCheckDeleteBondTest_NoBond(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckDeleteBondTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)
        currentHealthObject.bondInfo = {
            "scaqab10adm01.us.oracle.com": {},
            "scaqab10adm02.us.oracle.com": {
                "backup": {"bridgeName": "vmbondeth1", "intfs": ["eth2", "eth3"],
                           "lacp": True, "bondName": "bondeth1", "vlanId": "999"}
            }
        }

        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_SUCC,
            "scaqab10adm02.us.oracle.com": HEALTHCHECK_FAIL
        }
        baseHealthCheckObject.mSetDom0s(resultsExpected.keys())

        for dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            _cmds = {
                self.mGetRegexLocal(): [
                    [
                        exaMockCommand("/bin/ping -c 1 -W 4 scaqab10adm01.us.oracle.com ", aRc=0, aPersist=True),
                        exaMockCommand("/bin/ping -c 1 -W 4 scaqab10adm02.us.oracle.com ", aRc=0, aPersist=True)
                    ]
                ],
                self.mGetRegexDom0(): [
                    [
                        exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0",
                                       aPersist=True),
                        exaMockCommand("/opt/exadata_ovm/exadata.img.domu_maker remove-bridge-dom0",
                                       aRc=1 if dom0 == "scaqab10adm02.us.oracle.com" else 0,
                                       aPersist=True),
                        exaMockCommand("/sbin/ip link set", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0",
                                       aPersist=True),
                        exaMockCommand("/opt/exadata_ovm/exadata.img.domu_maker remove-bridge-dom0",
                                       aRc=1 if dom0 == "scaqab10adm02.us.oracle.com" else 0,
                                       aPersist=True),
                        exaMockCommand("/sbin/ip link set", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0",
                                       aPersist=True),
                        exaMockCommand("/opt/exadata_ovm/exadata.img.domu_maker remove-bridge-dom0",
                                       aRc=1 if dom0 == "scaqab10adm02.us.oracle.com" else 0,
                                       aPersist=True),
                        exaMockCommand("/sbin/ip link set", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0",
                                       aPersist=True),
                        exaMockCommand("/opt/exadata_ovm/exadata.img.domu_maker remove-bridge-dom0",
                                       aRc=1 if dom0 == "scaqab10adm02.us.oracle.com" else 0,
                                       aPersist=True),
                        exaMockCommand("/sbin/ip link set", aRc=0, aPersist=True)
                    ]
                ]
            }
            self.mPrepareMockCommands(_cmds)

            returnedResult = currentHealthObject.mCheckDeleteBondTest(dom0)
            ebLogInfo("Healthcheck results: {}".format(returnedResult))
            self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])

    def test_mCheckDeleteBondTestXEN(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckDeleteBondTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)
        currentHealthObject.bondInfo = {
            "scaqab10adm01.us.oracle.com": {
                "client": {"bridgeName": "vmbondeth0", "intfs": ["eth4", "eth5"],
                           "lacp": False, "bondName": "bondeth0", "vlanId": None}
            },
            "scaqab10adm02.us.oracle.com": {
                "backup": {"bridgeName": "vmbondeth1", "intfs": ["eth2", "eth3"],
                           "lacp": True, "bondName": "bondeth1", "vlanId": "999"}
            }
        }

        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_SUCC,
            "scaqab10adm02.us.oracle.com": HEALTHCHECK_SUCC
        }
        baseHealthCheckObject.mSetDom0s(resultsExpected.keys())

        for dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            _cmds = {
                self.mGetRegexLocal(): [
                    [
                        exaMockCommand("/bin/ping -c 1 -W 4 scaqab10adm01.us.oracle.com ", aRc=0, aPersist=True),
                        exaMockCommand("/bin/ping -c 1 -W 4 scaqab10adm02.us.oracle.com ", aRc=0, aPersist=True)
                    ]
                ],
                self.mGetRegexDom0(): [
                    [
                        exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0", aPersist=True),
                        exaMockCommand("/opt/exadata_ovm/exadata.img.domu_maker remove-bridge-dom0 vmbondeth1", aRc=0,
                                       aPersist=True),
                        exaMockCommand("/opt/exadata_ovm/exadata.img.domu_maker remove-bridge-dom0 vmbondeth0", aRc=0,
                                       aPersist=True),
                        exaMockCommand("/sbin/ip link set", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0",
                                       aPersist=True),
                        exaMockCommand("/opt/exadata_ovm/exadata.img.domu_maker remove-bridge-dom0 vmbondeth1", aRc=0,
                                       aPersist=True),
                        exaMockCommand("/opt/exadata_ovm/exadata.img.domu_maker remove-bridge-dom0 vmbondeth0", aRc=0,
                                       aPersist=True),
                        exaMockCommand("/sbin/ip link set", aRc=0, aPersist=True)
                    ]
                ]
            }
            self.mPrepareMockCommands(_cmds)

            returnedResult = currentHealthObject.mCheckDeleteBondTest(dom0)
            ebLogInfo("Healthcheck results: {}".format(returnedResult))
            self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])

    def test_mCheckDeleteBondTestKVM(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckDeleteBondTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)
        currentHealthObject.bondInfo = {
            "scaqab10adm01.us.oracle.com": {
                "client": {"bridgeName": "vmbondeth0", "intfs": ["eth4", "eth5"],
                           "lacp": False, "bondName": "bondeth0", "vlanId": None}
            },
            "scaqab10adm02.us.oracle.com": {
                "backup": {"bridgeName": "vmbondeth1", "intfs": ["eth2", "eth3"],
                          "lacp": True, "bondName": "bondeth1", "vlanId": "999"}
            }
        }

        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_SUCC,
            "scaqab10adm02.us.oracle.com": HEALTHCHECK_SUCC
        }
        baseHealthCheckObject.mSetDom0s(resultsExpected.keys())

        for dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            _cmds = {
                self.mGetRegexLocal(): [
                    [
                        exaMockCommand("/bin/ping -c 1 -W 4 scaqab10adm01.us.oracle.com", aRc=0, aPersist=True),
                        exaMockCommand("/bin/ping -c 1 -W 4 scaqab10adm02.us.oracle.com", aRc=0, aPersist=True)
                    ]
                ],
                self.mGetRegexDom0(): [
                    [
                        exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: KVMHOST",
                                       aPersist=True),
                        exaMockCommand("/usr/sbin/vm_maker --remove-bridge vmbondeth1", aRc=0, aPersist=True),
                        exaMockCommand("/usr/sbin/vm_maker --remove-bridge vmbondeth0", aRc=0, aPersist=True),
                        exaMockCommand("/sbin/ip link set", aRc=0, aPersist=True)
                    ],
                    [
                        exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: KVMHOST",
                                       aPersist=True),
                        exaMockCommand("/usr/sbin/vm_maker --remove-bridge vmbondeth1", aRc=0, aPersist=True),
                        exaMockCommand("/usr/sbin/vm_maker --remove-bridge vmbondeth0", aRc=0, aPersist=True),
                        exaMockCommand("/sbin/ip link set", aRc=0, aPersist=True)
                    ]
                ]
            }
            self.mPrepareMockCommands(_cmds)
            returnedResult = currentHealthObject.mCheckDeleteBondTest(dom0)
            ebLogInfo("Healthcheck results: {}".format(returnedResult))
            self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])

    def test_mCheckLinkStatusTest_pass(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckLinkStatusTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_SUCC,
            "scaqab10adm02.us.oracle.com": HEALTHCHECK_SUCC
        }
        baseHealthCheckObject.mSetDom0s(resultsExpected.keys())

        for dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            if dom0 == "scaqab10adm01.us.oracle.com":
                _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexDom0(): [
                        [
                            exaMockCommand("/bin/cat /sys/class/net/", aRc=1, aStdout="5", aPersist=False),
                            exaMockCommand("/bin/cat /sys/class/net/", aRc=0, aStdout="5", aPersist=False),
                            exaMockCommand("/bin/cat /sys/class/net/", aRc=0, aStdout="1", aPersist=True),
                            exaMockCommand("/sbin/ip link set", aRc=0, aPersist=True)
                        ]
                    ]
                }
            else:
                # making separate section for second dom0 to try alternate path of trying to bring up
                _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexDom0(): [
                        [
                            exaMockCommand("/bin/cat /sys/class/net/eth6/carrier", aRc=0, aStdout="0", aPersist=False),
                            exaMockCommand("/bin/cat /sys/class/net/eth7/carrier", aRc=0, aStdout="0", aPersist=False),
                            exaMockCommand("/bin/cat /sys/class/net/eth4/carrier", aRc=0, aStdout="0", aPersist=False),
                            exaMockCommand("/bin/cat /sys/class/net/eth5/carrier", aRc=0, aStdout="0", aPersist=False),
                            exaMockCommand("/bin/cat /sys/class/net/eth6/carrier", aRc=0, aStdout="1", aPersist=True),
                            exaMockCommand("/bin/cat /sys/class/net/eth7/carrier", aRc=0, aStdout="1", aPersist=True),
                            exaMockCommand("/bin/cat /sys/class/net/eth4/carrier", aRc=0, aStdout="1", aPersist=True),
                            exaMockCommand("/bin/cat /sys/class/net/eth5/carrier", aRc=0, aStdout="1", aPersist=True),
                            exaMockCommand("/sbin/ip link set", aRc=0, aPersist=True)
                        ]
                    ]
                }
            self.mPrepareMockCommands(_cmds)

            returnedResult = currentHealthObject.mCheckLinkStatusTest(dom0)
            ebLogInfo("Healthcheck results: {}".format(returnedResult))
            self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])

    def test_mCheckLinkStatusTest_fail(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckLinkStatusTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        expectedLogs = [
            '* WARNING * Trying last time to check the interface eth7 on the host scaqab10adm01.us.oracle.com.',
            '* ERROR * Interface eth7 on the host scaqab10adm01.us.oracle.com is not working.',
            '* WARNING * Trying last time to check the interface eth5 on the host scaqab10adm01.us.oracle.com.',
            '* ERROR * Interface eth5 on the host scaqab10adm01.us.oracle.com is not working.'
        ]
        expectedHcDisplayStr = [
            'Cable fault or cable not detected for eth5 in host scaqab10adm01.us.oracle.com. Please check the cables connected to ExaCC.',
            'Cable fault or cable not detected for eth7 in host scaqab10adm01.us.oracle.com. Please check the cables connected to ExaCC.'
        ]

        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_FAIL,
            "scaqab10adm02.us.oracle.com": HEALTHCHECK_SUCC,
        }
        baseHealthCheckObject.mSetDom0s(resultsExpected.keys())

        for dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            _cmds = {
                self.mGetRegexLocal(): [
                    [
                        exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                    ]
                ],
                self.mGetRegexDom0(): [
                    [
                        exaMockCommand("/bin/cat /sys/class/net/eth6/carrier", aRc=0, aStdout="1", aPersist=True),
                        exaMockCommand("/bin/cat /sys/class/net/eth7/carrier", aRc=0,
                                       aStdout="0" if dom0 == "scaqab10adm01.us.oracle.com" else "1",
                                       aPersist=True),
                        exaMockCommand("/bin/cat /sys/class/net/eth4/carrier", aRc=0, aStdout="1", aPersist=True),
                        exaMockCommand("/bin/cat /sys/class/net/eth5/carrier", aRc=0,
                                       aStdout="0" if dom0 == "scaqab10adm01.us.oracle.com" else "1",
                                       aPersist=True),
                        exaMockCommand("/sbin/ip link set", aRc=0, aPersist=True)
                    ]
                ]
            }
            self.mPrepareMockCommands(_cmds)

            returnedResult = currentHealthObject.mCheckLinkStatusTest(dom0)
            ebLogInfo("Healthcheck results: {}".format(returnedResult))
            self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])

            if dom0 == "scaqab10adm01.us.oracle.com":
                self.assertEqual(set(expectedLogs), set(returnedResult["hcLogs"]))
                self.assertEqual(set(expectedHcDisplayStr), set(returnedResult["hcMsgDetail"]["hcDisplayString"]))
                self.assertEqual({"eth5", "eth7"}, set(currentHealthObject.downIntfs[dom0]))
            elif dom0 == "scaqab10adm02.us.oracle.com":
                self.assertEqual(set(), set(currentHealthObject.downIntfs[dom0]))

    def test_mCheckArping(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckArping")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        dom0s = ["scaqab10adm01.us.oracle.com", "scaqab10adm02.us.oracle.com"]
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        baseHealthCheckObject.mSetDom0s(dom0s)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        for dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            _cmds = {
                self.mGetRegexLocal(): [
                    [
                        exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                    ]
                ],
                self.mGetRegexDom0(): [
                    [
                        exaMockCommand("/sbin/arping -c", aRc=0 if dom0 == "scaqab10adm01.us.oracle.com" else 1, aPersist=True)
                    ]
                ]
            }

            self.mPrepareMockCommands(_cmds)
            nodeObj = currentHealthObject.mGetNode(dom0)
            cluNetObj = ebCluNetwork(dom0, {}, {}, nodeObj, baseHealthCheckObject, get_logger())
            returnedResult = currentHealthObject.mCheckArping("eth2", "255.255.0.0", cluNetObj)
            self.assertEqual(returnedResult, True if dom0 == "scaqab10adm01.us.oracle.com" else False)

    def test_checkUpdateNetworkFlow_allSkip(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckGatewayTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        dom0 = "scaqab10adm01.us.oracle.com"
        domU = "scaqab10client01vm08.us.oracle.com"
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        baseHealthCheckObject.mSetDom0s([dom0])
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)
        baseHealthCheckObject.mSetReconfiguration(True)
        baseHealthCheckObject.mSetUpdateNetworkServices()
        baseHealthCheckObject.mSetUpdateNetwork("scaqab10adm01.us.oracle.com")
        baseHealthCheckObject.mSetUpdateNetwork("scaqab10adm01.us.oracle.com", "client", False)
        baseHealthCheckObject.mSetUpdateNetwork("scaqab10adm01.us.oracle.com", "backup", False)

        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_SUCC
        }

        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/sbin/brctl show | grep 'vnet\|vif'", aRc=1, aPersist=True),
                    exaMockCommand("/bin/uname", aRc=0, aStdout="4.1.12-124.52.4.el6uek.x86_64", aPersist=True)
                ],
                [
                    exaMockCommand("/usr/sbin/brctl show | grep 'vnet\|vif'", aRc=1, aPersist=True),
                    exaMockCommand("/bin/uname", aRc=0, aStdout="4.1.12-124.52.4.el6uek.x86_64", aPersist=True)
                ],
                [
                    exaMockCommand("/usr/sbin/brctl show | grep 'vnet\|vif'", aRc=1, aPersist=True),
                    exaMockCommand("/bin/uname", aRc=0, aStdout="4.1.12-124.52.4.el6uek.x86_64", aPersist=True)
                ],
                [
                    exaMockCommand("/usr/sbin/brctl show | grep 'vnet\|vif'", aRc=1, aPersist=True),
                    exaMockCommand("/bin/uname", aRc=0, aStdout="4.1.12-124.52.4.el6uek.x86_64", aPersist=True)
                ]
            ]
        }

        def skipAssertions(dom0, result):
            self.assertEqual(resultsExpected[dom0], result["hcTestResult"])
            for network in ["client", "backup"]:
                self.assertEqual("Skipped", result["hcMsgDetail"][network]["status"])
                self.assertEqual("This network not selected for reconfiguration on this host",
                                 result["hcMsgDetail"][network]["cause"])

        self.mPrepareMockCommands(_cmds)

        for test in [currentHealthObject.mCheckGatewayTest(dom0),
                     currentHealthObject.mCheckVlanIdTest(dom0),
                     currentHealthObject.mCheckNetworkPingTest(dom0)]:
            returnedResult = test
            skipAssertions(dom0, returnedResult)

        tests = [currentHealthObject.mCheckDnsTest(dom0), currentHealthObject.mCheckNtpTest(dom0)]
        testNames = ["DnsTest", "NtpTest"]
        for test, testname in zip(tests, testNames):
            returnedResult = test
            self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])
            self.assertEqual("Skipped", returnedResult["hcMsgDetail"]["status"])
            self.assertEqual(f"Client network unchanged for {dom0}. Please check results for {testname} from corresponding VM {domU}.", returnedResult["hcMsgDetail"]["cause"])


    def test_checkUpdateNetworkFlowDom0_reconfigBackupWithoutDnsNtp(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckGatewayTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        dom0 = "scaqab10adm01.us.oracle.com"
        updatingProperties = ["gateway", "netmask", "vlantag", "ip", "hostname"]
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        baseHealthCheckObject.mSetDom0s([dom0])
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)
        baseHealthCheckObject.mSetReconfiguration(True)
        baseHealthCheckObject.mSetUpdateNetworkServices()
        baseHealthCheckObject.mSetUpdateNetwork("scaqab10adm01.us.oracle.com")
        baseHealthCheckObject.mSetUpdateNetwork("scaqab10adm01.us.oracle.com", "client", False)
        baseHealthCheckObject.mSetUpdateNetwork("scaqab10adm01.us.oracle.com", "backup", True, updatingProperties)

        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_SUCC
        }

        dom0 = "scaqab10adm01.us.oracle.com"

        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/sbin/brctl show | grep 'vnet\|vif'",
                                   aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0, aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth1/operstate",
                                   aRc=0, aStdout="up", aPersist=True),
                    exaMockCommand("/sbin/ifconfig", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/iptables -nvL", aRc=1, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/iptables -I INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/iptables -D INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/arping", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip link del", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip addr del", aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth1/operstate",
                                   aRc=0, aStdout="up", aPersist=True),
                    exaMockCommand("/sbin/ifconfig", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/iptables -nvL", aRc=1, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/iptables -I INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/iptables -D INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/arping", aRc=0, aPersist=False),
                    exaMockCommand("/sbin/arping", aRc=1, aPersist=True),
                    exaMockCommand("/sbin/ip link del", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip addr del", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        def assertions(result, testname=None):
            # client network
            self.assertEqual("Skipped", result["hcMsgDetail"]["client"]["status"])
            self.assertEqual("This network not selected for reconfiguration on this host",
                                 result["hcMsgDetail"]["client"]["cause"])
            # backup network
            if testname in ["NetworkPingTest"]:
                self.assertEqual("Pass", result["hcMsgDetail"]["backup"]["vmbondeth1"]["BackupIPs"]["76.0.0.4"]["status"])
            elif testname in ["VlanIdTest"]:
                self.assertEqual("Pass", result["hcMsgDetail"]["backup"]["bondeth1"]["status"])
            else:
                self.assertEqual("Pass", result["hcMsgDetail"]["backup"]["vmbondeth1"]["status"])

        returnedResult = currentHealthObject.mCheckGatewayTest(dom0)
        assertions(returnedResult)
        returnedResult = currentHealthObject.mCheckVlanIdTest(dom0)
        assertions(returnedResult, "VlanIdTest")
        returnedResult = currentHealthObject.mCheckNetworkPingTest(dom0)
        assertions(returnedResult, "NetworkPingTest")

    def test_checkUpdateNetworkFlowDomU_reconfigBackupWithDnsNtp(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckGatewayTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        dom0 = self.mGetClubox().mReturnDom0DomUPair()[0][0]
        domU = self.mGetClubox().mReturnDom0DomUPair()[0][1]

        updatingProperties = ["gateway", "netmask", "vlantag", "ip", "hostname"]
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        baseHealthCheckObject.mSetDomUs([domU])
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)
        baseHealthCheckObject.mSetReconfiguration(True)
        baseHealthCheckObject.mSetUpdateNetworkServices()
        baseHealthCheckObject.mSetUpdateNetworkServices('dns', True)
        baseHealthCheckObject.mSetUpdateNetworkServices('ntp', True)
        baseHealthCheckObject.mSetUpdateNetwork(dom0)
        baseHealthCheckObject.mSetUpdateNetwork(dom0, "client", False)
        baseHealthCheckObject.mSetUpdateNetwork(dom0, "backup", True, updatingProperties)

        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexDomU(): [
                [
                   exaMockCommand("/sbin/arping", aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("/usr/bin/dig", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/uname -r", aRc=0, aStdout="4.1.12-124.52.4.el7uek.x86_64", aPersist=True),
                    exaMockCommand("/usr/sbin/chronyd -Q 'server", aPersist=True, aRc=0)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        returnedResult = currentHealthObject.mCheckGatewayTest(domU)
        self.assertEqual("Skipped", returnedResult["hcMsgDetail"]["status"])
        self.assertEqual(f"Please check results for GatewayTest from corresponding dBServer {dom0}.", returnedResult["hcMsgDetail"]["cause"])
        returnedResult = currentHealthObject.mCheckDnsTest(domU)
        self.assertEqual(HEALTHCHECK_FAIL, returnedResult["hcTestResult"])
        returnedResult = currentHealthObject.mCheckNtpTest(domU)
        self.assertEqual(HEALTHCHECK_SUCC, returnedResult["hcTestResult"])

    def test_checkUpdateNetworkFlowDomU_reconfigBothWithDnsNtp(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckGatewayTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        dom0 = self.mGetClubox().mReturnDom0DomUPair()[0][0]
        domU = self.mGetClubox().mReturnDom0DomUPair()[0][1]

        updatingProperties = ["gateway", "netmask", "vlantag", "ip", "hostname"]
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        baseHealthCheckObject.mSetDomUs([domU])
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)
        baseHealthCheckObject.mSetReconfiguration(True)
        baseHealthCheckObject.mSetUpdateNetworkServices()
        baseHealthCheckObject.mSetUpdateNetworkServices('dns', True)
        baseHealthCheckObject.mSetUpdateNetworkServices('ntp', True)
        baseHealthCheckObject.mSetUpdateNetwork(dom0)
        baseHealthCheckObject.mSetUpdateNetwork(dom0, "client", True)
        baseHealthCheckObject.mSetUpdateNetwork(dom0, "backup", True, updatingProperties)

        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexDomU(): [
                [
                   exaMockCommand("/sbin/arping", aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("/usr/bin/dig", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/uname -r", aRc=0, aStdout="4.1.12-124.52.4.el7uek.x86_64", aPersist=True),
                    exaMockCommand("/usr/sbin/chronyd -Q 'server", aPersist=True, aRc=0)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        tests = [currentHealthObject.mCheckGatewayTest(domU),
                 currentHealthObject.mCheckDnsTest(domU),
                 currentHealthObject.mCheckNtpTest(domU)]
        causes = [
            f"Please check results for GatewayTest from corresponding dBServer {dom0}.",
            f"Client network changes identified for {domU}. Please check results for DnsTest from corresponding dBServer {dom0}.",
            f"Client network changes identified for {domU}. Please check results for NtpTest from corresponding dBServer {dom0}."
        ]
        for test, cause in zip(tests, causes):
            returnedResult = test
            self.assertEqual("Skipped", returnedResult["hcMsgDetail"]["status"])
            self.assertEqual(cause, returnedResult["hcMsgDetail"]["cause"])

    def test_checkUpdateNetworkFlow_reconfigBoth(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckGatewayTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        dom0 = "scaqab10adm01.us.oracle.com"
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        baseHealthCheckObject.mSetDom0s([dom0])
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)
        baseHealthCheckObject.mSetReconfiguration(True)
        baseHealthCheckObject.mSetUpdateNetworkServices()
        baseHealthCheckObject.mSetUpdateNetwork("scaqab10adm01.us.oracle.com")
        baseHealthCheckObject.mSetUpdateNetwork("scaqab10adm01.us.oracle.com", "client", True)
        baseHealthCheckObject.mSetUpdateNetwork("scaqab10adm01.us.oracle.com", "backup", True)

        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_SUCC
        }

        dom0 = "scaqab10adm01.us.oracle.com"

        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/sbin/brctl show | grep 'vnet\|vif'",
                                   aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0, aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth0/operstate",
                                   aRc=0, aStdout="up", aPersist=False),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth1/operstate",
                                   aRc=0, aStdout="up", aPersist=False),
                    exaMockCommand("/sbin/ifconfig", aRc=0, aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth", aRc=0, aStdout="up", aPersist=True),
                    exaMockCommand("/sbin/iptables -nvL", aRc=1, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/iptables -I INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/iptables -D INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/arping", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip link del", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip addr del", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        def skipAssertions(dom0, result, cause):
            self.assertEqual(resultsExpected[dom0], result["hcTestResult"])
            for network in ["client", "backup"]:
                self.assertEqual("Skipped", result["hcMsgDetail"][network]["status"])
                self.assertEqual(cause, result["hcMsgDetail"][network]["cause"])

        returnedResult = currentHealthObject.mCheckGatewayTest(dom0)
        self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])
        for network, bridge in zip(["client", "backup"], ["vmbondeth0", "vmbondeth1"]):
            self.assertEqual("Pass", returnedResult["hcMsgDetail"][network][bridge]["status"])

        tests = [currentHealthObject.mCheckVlanIdTest(dom0), currentHealthObject.mCheckNetworkPingTest(dom0)]
        causes = ["VLAN is not being reconfigured for this network.",
                  "IP addresses are not being reconfigured for this network."]
        for test, cause in zip(tests, causes):
            returnedResult = test
            skipAssertions(dom0, returnedResult, cause)

        for test, cause in zip([currentHealthObject.mCheckDnsTest(dom0), currentHealthObject.mCheckNtpTest(dom0)],
                        ["None of the DNS servers, client gateway, or any hostnames/IPs are being changed for this cluster.",
                        "Neither of the NTP servers nor client gateway is being changed for this cluster."]):
            returnedResult = test
            self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])
            self.assertEqual("Skipped", returnedResult["hcMsgDetail"]["status"])
            self.assertEqual(cause, returnedResult["hcMsgDetail"]["cause"])

    def test_mCheckVlanIdTest(self):
        # Tested paths:
        #     "scaqab10adm01.us.oracle.com" -> Pass thru tcpdump
        #     "scaqab10adm02.us.oracle.com" -> Fail thru tcpdump

        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckVlanIdTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_SUCC,
            "scaqab10adm02.us.oracle.com": HEALTHCHECK_FAIL
        }
        baseHealthCheckObject.mSetDom0s(resultsExpected.keys())

        # to test the vlan path, we override the vlan ID temporarily for the test by changing the data in
        # the clucontrol objects. This is restored before exiting the test, in-spite of success/failure.
        # check vlan path for one dom0
        oldVlan = None
        changedNetObjs = []
        for dom0, domU in self.mGetClubox().mReturnDom0DomUPair():
            domU_mac = self.mGetClubox().mGetMachines().mGetMachineConfig(domU)
            net_list = domU_mac.mGetMacNetworks()
            eBoxNetworks = self.mGetClubox().mGetNetworks()
            for net in net_list:
                netobj = eBoxNetworks.mGetNetworkConfig(net)
                if netobj.mGetNetType() in ["backup"]:
                    changedNetObjs.append(netobj)
                    oldVlan = netobj.mGetNetVlanId()
                    netobj.mSetNetVlanId("999")

        for dom0, domU in self.mGetClubox().mReturnDom0DomUPair():
            _cmds = {
                self.mGetRegexLocal(): [
                    [
                        exaMockCommand("/bin/ping -c 1 -W 4", aRc=0, aPersist=True)
                    ]
                ],
                self.mGetRegexDom0(): [
                    [
                        exaMockCommand("/usr/sbin/brctl show | grep 'vnet\|vif'",
                                       aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0, aPersist=True),
                        exaMockCommand("/bin/cat /sys/class/net/vmbondeth0/operstate",
                                       aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0,
                                       aStdout="down" if dom0 == "scaqab10adm01.us.oracle.com" else "up",
                                       aPersist=True),
                        exaMockCommand("/bin/cat /sys/class/net/vmbondeth1/operstate",
                                       aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0,
                                       aStdout="down" if dom0 == "scaqab10adm01.us.oracle.com" else "up",
                                       aPersist=True),
                        exaMockCommand("timeout 10 tcpdump -i", aRc=0, aPersist=True),
                        exaMockCommand("/bin/grep", aRc=0 if dom0 == "scaqab10adm01.us.oracle.com" else 1,
                                       aStdout="35" if dom0 == "scaqab10adm01.us.oracle.com" else "0",
                                       aPersist=True),
                        exaMockCommand("/bin/ls -l /tmp/", aRc=0, aPersist=True),
                        exaMockCommand("/bin/rm -rf /tmp/", aRc=0, aPersist=True)
                    ]
                ]
            }
            self.mPrepareMockCommands(_cmds)

            returnedResult = currentHealthObject.mCheckVlanIdTest(dom0)
            ebLogInfo("Healthcheck results: {}".format(returnedResult))
            self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])
            self.assertEqual("Pass", returnedResult["hcMsgDetail"]["client"]["bondeth0"]["status"])
            if dom0 == "scaqab10adm02.us.oracle.com":
                self.assertEqual("WARNING: No traffic seen on the interface bondeth1 tagged with vlanId 999.",
                                 returnedResult["hcMsgDetail"]["backup"]["bondeth1"]["cause"])

        # restore the Vlan ID back to original
        for netobj in changedNetObjs:
            netobj.mSetNetVlanId(oldVlan)

    def test_mCheckVlanIdTest_skipBackup(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckVlanIdTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_SUCC
        }
        baseHealthCheckObject.mSetDom0s(resultsExpected.keys())

        baseHealthCheckObject.mGetHcConfig()["network_validation"]["skip_backup_gateway/vlan_check"] = "True"

        dom0 = "scaqab10adm01.us.oracle.com"

        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping -c 1 -W 4", aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/sbin/brctl show | grep 'vnet\|vif'",
                                   aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0, aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth0/operstate",
                                   aRc=0, aStdout="up", aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth1/operstate",
                                   aRc=0, aStdout="up", aPersist=True),
                    exaMockCommand("timeout 10 tcpdump -i", aRc=1, aPersist=True),
                    exaMockCommand("/bin/grep", aRc=0 , aPersist=True),
                    exaMockCommand("/bin/ls -l /tmp/", aRc=0, aPersist=True),
                    exaMockCommand("/bin/rm -rf /tmp/", aRc=1, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        returnedResult = currentHealthObject.mCheckVlanIdTest(dom0)
        ebLogInfo("Healthcheck results: {}".format(returnedResult))

        self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])

    def test_mCheckVlanIdTest_Pass(self):
        # Tested paths:
        # "scaqab10adm01.us.oracle.com" -> Pass thru arping
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckVlanIdTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)
        oldVlan = None
        changedNetObjs = []

        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_SUCC
        }
        baseHealthCheckObject.mSetDom0s(resultsExpected.keys())

        dom0 = "scaqab10adm01.us.oracle.com"
        domU = "scaqab10client01vm08.us.oracle.com"

        # override vlan for dom0
        domU_mac = self.mGetClubox().mGetMachines().mGetMachineConfig(domU)
        net_list = domU_mac.mGetMacNetworks()
        eBoxNetworks = self.mGetClubox().mGetNetworks()
        for net in net_list:
            netobj = eBoxNetworks.mGetNetworkConfig(net)
            if netobj.mGetNetType() in ["backup"]:
                changedNetObjs.append(netobj)
                oldVlan = netobj.mGetNetVlanId()
                netobj.mSetNetVlanId("999")

        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping -c 1 -W 4", aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/sbin/brctl show | grep 'vnet\|vif'",
                                   aRc=1, aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth0/operstate",
                                   aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0,
                                   aStdout="down" if dom0 == "scaqab10adm01.us.oracle.com" else "up",
                                   aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth1/operstate",
                                   aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0,
                                   aStdout="down" if dom0 == "scaqab10adm01.us.oracle.com" else "up",
                                   aPersist=True),
                    exaMockCommand("timeout 10 tcpdump -i", aRc=1, aPersist=True),
                    exaMockCommand("/bin/grep", aRc=0, aStdout="82", aPersist=True),
                    exaMockCommand("/bin/ls -l /tmp/", aRc=0, aPersist=True),
                    exaMockCommand("/bin/rm -rf /tmp/", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        returnedResult = currentHealthObject.mCheckVlanIdTest(dom0)
        ebLogInfo("Healthcheck results: {}".format(returnedResult))

        # restore the Vlan ID back to original
        for netobj in changedNetObjs:
            netobj.mSetNetVlanId(oldVlan)

        self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])

    def test_mCheckGatewayTest(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckGatewayTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_SUCC,
            "scaqab10adm02.us.oracle.com": HEALTHCHECK_FAIL
        }
        baseHealthCheckObject.mSetDom0s(resultsExpected.keys())

        for dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            _cmds = {
                self.mGetRegexLocal(): [
                    [
                        exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                    ]
                ],
                self.mGetRegexDom0(): [
                    [
                        exaMockCommand("/usr/sbin/brctl show | grep 'vnet\|vif'",
                                       aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0, aPersist=True),
                        exaMockCommand("/bin/cat /sys/class/net/vmbondeth0/operstate",
                                       aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0,
                                       aStdout="down" if dom0 == "scaqab10adm01.us.oracle.com" else "up",
                                       aPersist=False),
                        exaMockCommand("/bin/cat /sys/class/net/vmbondeth1/operstate",
                                       aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0,
                                       aStdout="down" if dom0 == "scaqab10adm01.us.oracle.com" else "up",
                                       aPersist=False),
                        exaMockCommand("/sbin/ifconfig", aRc=0, aPersist=True),
                        exaMockCommand("/bin/cat /sys/class/net/vmbondeth", aRc=0, aStdout="up", aPersist=True),
                        exaMockCommand("/sbin/iptables -nvL", aRc=1, aStdout="random O/P", aPersist=True),
                        exaMockCommand("/sbin/iptables -I INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                        exaMockCommand("/sbin/iptables -D INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                        exaMockCommand("/sbin/arping", aRc=0 if dom0 == "scaqab10adm01.us.oracle.com" else 1, aPersist=True),
                        exaMockCommand("/sbin/ip link del", aRc=0, aPersist=True),
                        exaMockCommand("/sbin/ip addr del", aRc=0, aPersist=True)
                    ]
                ]
            }
            self.mPrepareMockCommands(_cmds)
            returnedResult = currentHealthObject.mCheckGatewayTest(dom0)
            self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])

    def test_mCheckGatewayTest_skipBackup(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckGatewayTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_SUCC
        }
        baseHealthCheckObject.mSetDom0s(resultsExpected.keys())
        baseHealthCheckObject.mGetHcConfig()["network_validation"]["skip_all_backup_checks"] = "True"

        dom0 = "scaqab10adm01.us.oracle.com"

        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/sbin/brctl show | grep 'vnet\|vif'",
                                   aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0, aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth0/operstate",
                                   aRc=0, aStdout="up", aPersist=False),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth1/operstate",
                                   aRc=0, aStdout="up", aPersist=False),
                    exaMockCommand("/sbin/ifconfig", aRc=0, aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth", aRc=0, aStdout="up", aPersist=True),
                    exaMockCommand("/sbin/iptables -nvL", aRc=1, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/iptables -I INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/iptables -D INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/arping", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip link del", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip addr del", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        returnedResult = currentHealthObject.mCheckGatewayTest(dom0)
        self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])

    def test_mCheckGatewayTestDomU(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckGatewayTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        resultsExpected = {
            "scaqab10client01vm08.us.oracle.com": HEALTHCHECK_SUCC,
            "scaqab10client02vm08.us.oracle.com": HEALTHCHECK_FAIL
        }
        baseHealthCheckObject.mSetDomUs(resultsExpected.keys())

        for dom0, domU in self.mGetClubox().mReturnDom0DomUPair():
            _cmds = {
                self.mGetRegexLocal(): [
                    [
                        exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                    ]
                ],
                self.mGetRegexDomU(): [
                    [
                        exaMockCommand("/sbin/arping", aRc=0 if domU == "scaqab10client01vm08.us.oracle.com" else 1, aPersist=True)
                    ]
                ]
            }
            self.mPrepareMockCommands(_cmds)
            returnedResult = currentHealthObject.mCheckGatewayTest(domU)
            self.assertEqual(resultsExpected[domU], returnedResult["hcTestResult"])

    def test_mDnsdig_part1(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mDnsdig")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        dom0s = ["scaqab10adm01.us.oracle.com", "scaqab10adm02.us.oracle.com"]
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        baseHealthCheckObject.mSetDom0s(dom0s)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        DNSDIG_OP_FWD = "scaqab10adm02.us.oracle.com. 3668 IN    A       10.31.112.5"
        UNREACHABLE = "no servers could be reached"

        # covers case of unreachable server and successful fwd lookup
        for dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            _cmds = {
                self.mGetRegexLocal(): [
                    [
                        exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                    ]
                ],
                self.mGetRegexDom0(): [
                    [
                        exaMockCommand("/usr/bin/dig", aRc=0,
                                       aStdout=UNREACHABLE if dom0 == "scaqab10adm01.us.oracle.com" else DNSDIG_OP_FWD,
                                       aPersist=True)
                    ]
                ],
            }
            self.mPrepareMockCommands(_cmds)

            nodeObj = currentHealthObject.mGetNode(dom0)
            cluNetObj = ebCluNetwork(dom0, {}, {}, nodeObj, baseHealthCheckObject, get_logger())
            nwVldnHelpersObject = currentHealthObject.NetworkValidationHelpers(dom0, get_logger(), currentHealthObject)
            returnedResultFwd, _, _, _ = currentHealthObject.mDnsdig("sample_hostname", set(("10.31.112.5",)), "255.255.0.0", cluNetObj, nwVldnHelpersObject)
            self.assertEqual(returnedResultFwd, False if dom0 == "scaqab10adm01.us.oracle.com" else True)

            # add failure case for fwd lookup
            if dom0 == "scaqab10adm02.us.oracle.com":
                returnedResultFwd, _, _, _ = currentHealthObject.mDnsdig("sample_hostname", set(("1.2.3.4",)), "255.255.0.0", cluNetObj, nwVldnHelpersObject)
                self.assertEqual(returnedResultFwd, False)

    def test_mDnsdig_part2(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mDnsdig")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        dom0s = ["scaqab10adm01.us.oracle.com", "scaqab10adm02.us.oracle.com"]
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        baseHealthCheckObject.mSetDom0s(dom0s)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)
        DNSDIG_OP_REV_PASS = "5.112.31.10.in-addr.arpa. 8676  IN      PTR     scaqab10adm02.us.oracle.com."
        DNSDIG_OP_REV_FAIL = "5.112.31.10.in-addr.arpa. 8676  IN      PTR     random-hostname$.oracle.com."

        # covers case of successful reverse lookup and un-successful fwd lookup
        for dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            _cmds = {
                self.mGetRegexLocal(): [
                    [
                        exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                    ]
                ],
                self.mGetRegexDom0(): [
                    [
                        exaMockCommand("/usr/bin/dig", aRc=0,
                                       aStdout=DNSDIG_OP_REV_FAIL if dom0 == "scaqab10adm01.us.oracle.com" else DNSDIG_OP_REV_PASS,
                                       aPersist=False)
                    ]
                ],
            }
            self.mPrepareMockCommands(_cmds)

            nodeObj = currentHealthObject.mGetNode(dom0)
            cluNetObj = ebCluNetwork(dom0, {}, {}, nodeObj, baseHealthCheckObject, get_logger())
            nwVldnHelpersObject = currentHealthObject.NetworkValidationHelpers(dom0, get_logger(), currentHealthObject)
            returnedResultRev, _, _, _ = currentHealthObject.mDnsdig("10.31.112.5", set(("scaqab10adm02.us.oracle.com",)), "255.255.0.0", cluNetObj, nwVldnHelpersObject)
            self.assertEqual(returnedResultRev, False if dom0 == "scaqab10adm01.us.oracle.com" else True)

    def test_mCheckDnsTest(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckDnsTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        UNREACHABLE = "no servers could be reached"
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)
        INT_RESULT_PASS = copy.deepcopy(INT_RESULT)
        INT_RESULT_PASS["mCheckGatewayTest"]["hcMsgDetail"]["client"]["vmbondeth0"]["status"] = "Pass"
        currentHealthObject.intermediateResult = INT_RESULT_PASS

        # DNS resolutions will fail, hence both tests compared for failure assertion
        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_FAIL,
            "scaqab10adm02.us.oracle.com": HEALTHCHECK_FAIL
        }
        baseHealthCheckObject.mSetDom0s(resultsExpected.keys())

        for dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            _cmds = {
                self.mGetRegexLocal(): [
                    [
                        exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                    ]
                ],
                self.mGetRegexDom0(): [
                    [
                        exaMockCommand("/usr/sbin/brctl show | grep 'vnet\|vif'",
                                       aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0, aPersist=True),
                        exaMockCommand("/bin/cat /sys/class/net/vmbondeth0/operstate",
                                       aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0,
                                       aStdout="down" if dom0 == "scaqab10adm01.us.oracle.com" else "up",
                                       aPersist=True),
                        exaMockCommand("/bin/cat /sys/class/net/vmbondeth1/operstate",
                                       aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0,
                                       aStdout="down" if dom0 == "scaqab10adm01.us.oracle.com" else "up",
                                       aPersist=True),
                        exaMockCommand("/bin/cat /sys/class/net/eth",
                                       aRc=0 if dom0 == "scaqab10adm01.us.oracle.com" else 0, aStdout="up",
                                       aPersist=True),
                        exaMockCommand("/sbin/ifconfig", aRc=0, aPersist=True),
                        exaMockCommand("/sbin/iptables -nvL", aRc=1, aStdout="random O/P", aPersist=True),
                        exaMockCommand("/sbin/iptables -I INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                        exaMockCommand("/sbin/iptables -D INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                        exaMockCommand("/sbin/arping", aRc=0 if dom0 == "scaqab10adm01.us.oracle.com" else 1,
                                       aPersist=True),
                        exaMockCommand("/sbin/ip route add", aRc=0, aPersist=True),
                        exaMockCommand("/sbin/ip route del", aRc=0, aPersist=True),
                        exaMockCommand("/usr/bin/dig", aRc=0,
                                       aStdout=UNREACHABLE if dom0 == "scaqab10adm01.us.oracle.com" else "",
                                       aPersist=False),
                        exaMockCommand("/usr/bin/dig", aRc=0 if dom0 == "scaqab10adm01.us.oracle.com" else 1,
                                       aPersist=True),
                        exaMockCommand("/sbin/ip link del", aRc=0, aPersist=True),
                        exaMockCommand("/sbin/ip addr del", aRc=0, aPersist=True)
                    ]
                ]
            }
            self.mPrepareMockCommands(_cmds)

            returnedResult = currentHealthObject.mCheckDnsTest(self.mGetClubox().mReturnDom0DomUPair()[1][0])
            self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])

    def test_mCheckDnsTest_skipBackup(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckDnsTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        # DNS resolutions will fail, hence both tests compared for failure assertion
        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_FAIL
        }
        baseHealthCheckObject.mSetDom0s(resultsExpected.keys())
        baseHealthCheckObject.mGetHcConfig()["network_validation"]["skip_backup_DNS_check"] = "True"

        dom0 = "scaqab10adm01.us.oracle.com"
        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/sbin/brctl show | grep 'vnet\|vif'",
                                   aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0, aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth0/operstate",
                                   aRc=0, aStdout="up", aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth1/operstate",
                                   aRc=0, aStdout="up", aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/eth", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ifconfig", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/iptables -nvL", aRc=1, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/iptables -I INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/iptables -D INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/arping", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip route add", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip route del", aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/dig", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip link del", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip addr del", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        returnedResult = currentHealthObject.mCheckDnsTest(dom0)
        self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])

    def test_mCheckDnsTest2(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckDnsTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        UNREACHABLE = "no servers could be reached"
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)
        DNSDIG_OP_FWD = "scaqab10client01vm08.us.oracle.com. 3668 IN    A       77.0.0.9\n" \
                        "scaqab10client01vm08.us.oracle.com. 3668 IN    A       77.0.0.99"

        # DNS resolutions will fail, hence both tests compared for failure assertion
        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_FAIL,
            "scaqab10adm02.us.oracle.com": HEALTHCHECK_FAIL
        }
        baseHealthCheckObject.mSetDom0s(resultsExpected.keys())

        for dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            _cmds = {
                self.mGetRegexLocal(): [
                    [
                        exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                    ]
                ],
                self.mGetRegexDom0(): [
                    {
                        exaMockCommand("/usr/sbin/brctl show | grep 'vnet\|vif'", aRc=0, aPersist=True),
                        exaMockCommand("/bin/cat /sys/class/net/vmbondeth0/operstate",
                                       aRc=0, aStdout="up", aPersist=True),
                        exaMockCommand("/bin/cat /sys/class/net/vmbondeth1/operstate",
                                       aRc=0, aStdout="up", aPersist=True),
                        exaMockCommand("/bin/cat /sys/class/net/eth",
                                       aRc=0, aStdout="up", aPersist=True),
                        exaMockCommand("/sbin/ifconfig", aRc=0, aPersist=True),
                        exaMockCommand("/sbin/iptables -nvL", aRc=1, aStdout="random O/P", aPersist=True),
                        exaMockCommand("/sbin/iptables -I INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                        exaMockCommand("/sbin/iptables -D INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                        exaMockCommand("/sbin/arping", aRc=0, aPersist=True),
                        exaMockCommand("/sbin/ip route add", aRc=0, aPersist=True),
                        exaMockCommand("/sbin/ip route del", aRc=0, aPersist=True),
                        exaMockCommand("/usr/bin/dig", aRc=0,
                                       aStdout=UNREACHABLE if dom0 == "scaqab10adm01.us.oracle.com" else DNSDIG_OP_FWD,
                                       aPersist=True),
                        exaMockCommand("/sbin/ip link del", aRc=0, aPersist=True),
                        exaMockCommand("/sbin/ip addr del", aRc=0, aPersist=True)
                    }
                ]
            }
            self.mPrepareMockCommands(_cmds)

            returnedResult = currentHealthObject.mCheckDnsTest(self.mGetClubox().mReturnDom0DomUPair()[1][0])
            self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])

    def test_mCheckDnsTest3(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckDnsTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)
        DNSDIG_OP_FWD = "scaqab10client01vm08.us.oracle.com. 3668 IN    A       77.0.0.9"
        DNSDIG_OP_REV = "5.112.31.10.in-addr.arpa. 8676  IN      PTR     scaqab10client01vm08.us.oracle.com.\n" \
                        "5.112.31.10.in-addr.arpa. 8676  IN      PTR     scaqab20client01vm08.us.oracle.com."

        # DNS resolutions will fail, hence both tests compared for failure assertion
        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_FAIL,
            "scaqab10adm02.us.oracle.com": HEALTHCHECK_FAIL
        }
        baseHealthCheckObject.mSetDom0s(resultsExpected.keys())

        for dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            _cmds = {
                self.mGetRegexLocal(): [
                    [
                        exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                    ]
                ],
                self.mGetRegexDom0(): [
                    {
                        exaMockCommand("/usr/sbin/brctl show | grep 'vnet\|vif'", aRc=0, aPersist=True),
                        exaMockCommand("/bin/cat /sys/class/net/vmbondeth0/operstate",
                                       aRc=0, aStdout="up", aPersist=True),
                        exaMockCommand("/bin/cat /sys/class/net/vmbondeth1/operstate",
                                       aRc=0, aStdout="up", aPersist=True),
                        exaMockCommand("/bin/cat /sys/class/net/eth",
                                       aRc=0, aStdout="up", aPersist=True),
                        exaMockCommand("/sbin/ifconfig", aRc=0, aPersist=True),
                        exaMockCommand("/sbin/iptables -nvL", aRc=1, aStdout="random O/P", aPersist=True),
                        exaMockCommand("/sbin/iptables -I INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                        exaMockCommand("/sbin/iptables -D INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                        exaMockCommand("/sbin/arping", aRc=0, aPersist=True),
                        exaMockCommand("/sbin/ip route add", aRc=0, aPersist=True),
                        exaMockCommand("/sbin/ip route del", aRc=0, aPersist=True),
                        exaMockCommand("/usr/bin/dig", aRc=0,
                                       aStdout=DNSDIG_OP_FWD if dom0 == "scaqab10adm01.us.oracle.com" else DNSDIG_OP_REV,
                                       aPersist=True),
                        exaMockCommand("/sbin/ip link del", aRc=0, aPersist=True),
                        exaMockCommand("/sbin/ip addr del", aRc=0, aPersist=True)
                    }
                ]
            }
            self.mPrepareMockCommands(_cmds)

            returnedResult = currentHealthObject.mCheckDnsTest(self.mGetClubox().mReturnDom0DomUPair()[1][0])
            self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])

    def test_mCheckDnsTest_addRoute(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckDnsTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        # Set other DNS servers
        _machines = self.mGetClubox().mGetMachines()
        _domU_mac = _machines.mGetMachineConfig("scaqab10client01vm08.us.oracle.com")
        old_dns = _domU_mac.mGetDnsServers()
        _domU_mac.mSetDnsServers(["8.8.8.8"])

        # DNS resolutions will fail, hence both tests compared for failure assertion
        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_FAIL,
            "scaqab10adm02.us.oracle.com": HEALTHCHECK_FAIL
        }
        baseHealthCheckObject.mSetDom0s(resultsExpected.keys())

        for dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            _cmds = {
                self.mGetRegexLocal(): [
                    [
                        exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                    ]
                ],
                self.mGetRegexDom0(): [
                    {
                        exaMockCommand("/usr/sbin/brctl show | grep 'vnet\|vif'", aRc=0, aPersist=True),
                        exaMockCommand("/bin/cat /sys/class/net/vmbondeth0/operstate",
                                       aRc=0, aStdout="up", aPersist=True),
                        exaMockCommand("/bin/cat /sys/class/net/vmbondeth1/operstate",
                                       aRc=0, aStdout="up", aPersist=True),
                        exaMockCommand("/bin/cat /sys/class/net/eth",
                                       aRc=0, aStdout="up", aPersist=True),
                        exaMockCommand("/sbin/ifconfig", aRc=0, aPersist=True),
                        exaMockCommand("/sbin/iptables -nvL", aRc=1, aStdout="random O/P", aPersist=True),
                        exaMockCommand("/sbin/iptables -I INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                        exaMockCommand("/sbin/iptables -D INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                        exaMockCommand("/sbin/arping", aRc=0, aPersist=True),
                        exaMockCommand("/sbin/ip route add", aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0,
                                       aPersist=True),
                        exaMockCommand("/sbin/ip route del", aRc=0, aPersist=True),
                        exaMockCommand("/usr/bin/dig", aRc=0, aPersist=True),
                        exaMockCommand("/sbin/ip link del", aRc=0, aPersist=True),
                        exaMockCommand("/sbin/ip addr del", aRc=0, aPersist=True)
                    }
                ]
            }
            self.mPrepareMockCommands(_cmds)

            returnedResult = currentHealthObject.mCheckDnsTest(self.mGetClubox().mReturnDom0DomUPair()[1][0])
            self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])

        # revert the DNS's back
        _domU_mac.mSetDnsServers(old_dns)

    def test_mCheckDnsTestDomU(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckDnsTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)
        DNSDIG_OP_FWD1 = "scaqab10client01vm08.us.oracle.com. 3668 IN    A       77.0.0.9\n"
        DNSDIG_OP_FWD2 = "scaqab10client02vm08.us.oracle.com. 3668 IN    A       77.0.0.11\n"

        # DNS resolutions will fail, hence both tests compared for failure assertion
        resultsExpected = {
            "scaqab10client01vm08.us.oracle.com": HEALTHCHECK_SUCC,
            "scaqab10client02vm08.us.oracle.com": HEALTHCHECK_FAIL
        }
        baseHealthCheckObject.mSetDomUs(resultsExpected.keys())
        baseHealthCheckObject.mSetReNetValidation(True)

        for dom0, domU in self.mGetClubox().mReturnDom0DomUPair():
            _cmds = {
                self.mGetRegexLocal(): [
                    [
                        exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                    ]
                ],
                self.mGetRegexDomU(): [
                    [
                        exaMockCommand("/usr/bin/dig", aRc=0, aPersist=False,
                                       aStdout=DNSDIG_OP_FWD1 if domU == "scaqab10client01vm08.us.oracle.com" else ""),
                        exaMockCommand("/usr/bin/dig", aRc=0, aPersist=False,
                                       aStdout=DNSDIG_OP_FWD2 if domU == "scaqab10client01vm08.us.oracle.com" else "")
                    ]
                ]
            }
            self.mPrepareMockCommands(_cmds)

            returnedResult = currentHealthObject.mCheckDnsTest(domU)
            self.assertEqual(resultsExpected[domU], returnedResult["hcTestResult"])

    def test_mNtpTest(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mNtpTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        for dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            _cmds = {
                self.mGetRegexDom0(): [
                    [
                        exaMockCommand("/usr/sbin/ntpdate", aRc=0 if dom0 == "scaqab10adm01.us.oracle.com" else 1, aPersist=True),
                        exaMockCommand("/usr/sbin/chronyd -Q", aRc=0 if dom0 == "scaqab10adm01.us.oracle.com" else 1, aPersist=True)
                    ]
                ],
                self.mGetRegexLocal(): [
                    [
                        exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                    ]
                ]
            }
            self.mPrepareMockCommands(_cmds)

            nodeObj = currentHealthObject.mGetNode(dom0)
            cluNetObj = ebCluNetwork(dom0, {}, {}, nodeObj, baseHealthCheckObject, get_logger())
            # Set returnedResult = 0 if mNtpTest returns True, else 1 for False
            returnedResultOL6 = currentHealthObject.mNtpTest("OL6", "255.255.0.0", cluNetObj)
            self.assertEqual(returnedResultOL6, True if dom0 == "scaqab10adm01.us.oracle.com" else False)
            returnedResultOL7 = currentHealthObject.mNtpTest("OL7", "255.255.0.0", cluNetObj)
            self.assertEqual(returnedResultOL7, True if dom0 == "scaqab10adm01.us.oracle.com" else False)
            returnedResultOL8 = currentHealthObject.mNtpTest("OL8", "255.255.0.0", cluNetObj)
            self.assertEqual(returnedResultOL8, True if dom0 == "scaqab10adm01.us.oracle.com" else False)

    def test_mCheckNtpTest(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckNtpTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_SUCC,
            "scaqab10adm02.us.oracle.com": HEALTHCHECK_FAIL
        }
        baseHealthCheckObject.mSetDom0s(resultsExpected.keys())

        for dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            _cmds = {
                self.mGetRegexLocal(): [
                    [
                        exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                    ]
                ],
                self.mGetRegexDom0(): [
                    [
                        exaMockCommand("/usr/sbin/brctl show | grep 'vnet\|vif'",
                                       aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0, aPersist=True),
                        exaMockCommand("/bin/cat /sys/class/net/vmbondeth0/operstate",
                                       aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0,
                                       aStdout="down" if dom0 == "scaqab10adm01.us.oracle.com" else "up",
                                       aPersist=False),
                        exaMockCommand("/bin/cat /sys/class/net/vmbondeth1/operstate",
                                       aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0,
                                       aStdout="down" if dom0 == "scaqab10adm01.us.oracle.com" else "up",
                                       aPersist=False),
                        exaMockCommand("/bin/uname -r", aRc=0,
                                       aStdout="4.1.12-124.52.4.el6uek.x86_64" if dom0 == "scaqab10adm01.us.oracle.com"
                                       else "4.1.12-124.52.4.el7uek.x86_64",
                                       aPersist=True),
                        exaMockCommand("/sbin/ifconfig", aRc=0, aPersist=True),
                        exaMockCommand("/bin/cat /sys/class/net/vmbondeth", aRc=0,
                                       aStdout="up", aPersist=True),
                        exaMockCommand("/sbin/iptables -nvL", aRc=1, aStdout="random O/P", aPersist=True),
                        exaMockCommand("/sbin/iptables -I INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                        exaMockCommand("/sbin/iptables -D INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                        exaMockCommand("/sbin/arping", aRc=0, aPersist=True),
                        exaMockCommand("/sbin/ip route add", aRc=0 if dom0 == "scaqab10adm01.us.oracle.com" else 1,
                                       aPersist=True),
                        exaMockCommand("/sbin/ip route del", aRc=0, aPersist=True),
                        exaMockCommand("/usr/sbin/ntpdate -q", aRc=0 if dom0 == "scaqab10adm01.us.oracle.com" else 1,
                                       aPersist=True),
                        exaMockCommand("/usr/sbin/chronyd -Q 'server", aRc=0 if dom0 == "scaqab10adm01.us.oracle.com" else 1,
                                       aPersist=True),
                        exaMockCommand("/sbin/ip link del", aRc=0, aPersist=True),
                        exaMockCommand("/sbin/ip addr del", aRc=0, aPersist=True)
                    ]
                ]
            }
            self.mPrepareMockCommands(_cmds)

            returnedResult = currentHealthObject.mCheckNtpTest(self.mGetClubox().mReturnDom0DomUPair()[1][0])
            self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])

    def test_mCheckNtpTest_skipBackup(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckNtpTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_SUCC
        }
        baseHealthCheckObject.mSetDom0s(resultsExpected.keys())
        baseHealthCheckObject.mGetHcConfig()["network_validation"]["skip_backup_NTP_check"] = "True"

        dom0 = "scaqab10adm01.us.oracle.com"
        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/sbin/brctl show | grep 'vnet\|vif'",
                                   aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0, aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth0/operstate",
                                   aRc=0, aStdout="up", aPersist=False),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth1/operstate",
                                   aRc=0, aStdout="up", aPersist=False),
                    exaMockCommand("/bin/uname -r", aRc=0,
                                   aStdout="4.1.12-124.52.4.el7uek.x86_64", aPersist=True),
                    exaMockCommand("/sbin/ifconfig", aRc=0, aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth", aRc=0,
                                   aStdout="up", aPersist=True),
                    exaMockCommand("/sbin/iptables -nvL", aRc=1, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/iptables -I INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/iptables -D INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/arping", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip route add", aRc=0 if dom0 == "scaqab10adm01.us.oracle.com" else 1,
                                   aPersist=True),
                    exaMockCommand("/sbin/ip route del", aRc=0, aPersist=True),
                    exaMockCommand("/usr/sbin/chronyd -Q 'server", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip link del", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip addr del", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        returnedResult = currentHealthObject.mCheckNtpTest(dom0)
        self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])

    def test_mCheckNtpTest_addRoute(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckNtpTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        # Set other NTP servers
        _machines = self.mGetClubox().mGetMachines()
        _domU_mac = _machines.mGetMachineConfig("scaqab10client01vm08.us.oracle.com")
        old_ntp = _domU_mac.mGetNtpServers()
        _domU_mac.mSetNtpServers(["77.0.0.1"])

        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_SUCC,
            "scaqab10adm02.us.oracle.com": HEALTHCHECK_FAIL
        }
        baseHealthCheckObject.mSetDom0s(resultsExpected.keys())

        for dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            _cmds = {
                self.mGetRegexLocal(): [
                    [
                        exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                    ]
                ],
                self.mGetRegexDom0(): [
                    [
                        exaMockCommand("/usr/sbin/brctl show | grep 'vnet\|vif'",
                                       aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0, aPersist=True),
                        exaMockCommand("/bin/cat /sys/class/net/vmbondeth0/operstate",
                                       aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0,
                                       aStdout="down" if dom0 == "scaqab10adm01.us.oracle.com" else "up",
                                       aPersist=False),
                        exaMockCommand("/bin/cat /sys/class/net/vmbondeth1/operstate",
                                       aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0,
                                       aStdout="down" if dom0 == "scaqab10adm01.us.oracle.com" else "up",
                                       aPersist=False),
                        exaMockCommand("/bin/uname -r", aRc=0,
                                       aStdout="4.1.12-124.52.4.el6uek.x86_64" if dom0 == "scaqab10adm01.us.oracle.com"
                                       else "4.1.12-124.52.4.el7uek.x86_64",
                                       aPersist=True),
                        exaMockCommand("/sbin/ifconfig", aRc=0, aPersist=True),
                        exaMockCommand("/bin/cat /sys/class/net/vmbondeth", aRc=0,
                                       aStdout="up", aPersist=True),
                        exaMockCommand("/sbin/iptables -nvL", aRc=1, aStdout="random O/P", aPersist=True),
                        exaMockCommand("/sbin/iptables -I INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                        exaMockCommand("/sbin/iptables -D INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                        exaMockCommand("/sbin/arping", aRc=0, aPersist=True),
                        exaMockCommand("/sbin/ip route add", aRc=0 if dom0 == "scaqab10adm01.us.oracle.com" else 1,
                                       aPersist=True),
                        exaMockCommand("/sbin/ip route del", aRc=0, aPersist=True),
                        exaMockCommand("/usr/sbin/ntpdate -q", aRc=0 if dom0 == "scaqab10adm01.us.oracle.com" else 1,
                                       aPersist=True),
                        exaMockCommand("/usr/sbin/chronyd -Q 'server", aRc=0 if dom0 == "scaqab10adm01.us.oracle.com" else 1,
                                       aPersist=True),
                        exaMockCommand("/sbin/ip link del", aRc=0, aPersist=True),
                        exaMockCommand("/sbin/ip addr del", aRc=0, aPersist=True)
                    ]
                ]
            }
            self.mPrepareMockCommands(_cmds)

            returnedResult = currentHealthObject.mCheckNtpTest(self.mGetClubox().mReturnDom0DomUPair()[1][0])
            self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])

        # revert the NTP's back
        _domU_mac.mSetNtpServers(old_ntp)

    def test_mCheckNtpTest_OSNone(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckNtpTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_FAIL
        }
        baseHealthCheckObject.mSetDom0s(resultsExpected.keys())
        dom0 = "scaqab10adm01.us.oracle.com"

        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/sbin/brctl show | grep 'vnet\|vif'",
                                   aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0, aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth0/operstate",
                                   aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0,
                                   aStdout="down" if dom0 == "scaqab10adm01.us.oracle.com" else "up",
                                   aPersist=False),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth1/operstate",
                                   aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0,
                                   aStdout="down" if dom0 == "scaqab10adm01.us.oracle.com" else "up",
                                   aPersist=False),
                    exaMockCommand("/bin/uname -r", aRc=1, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        returnedResult = currentHealthObject.mCheckNtpTest(dom0)
        self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])

    def test_mCheckNtpTestDomUOL6(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckNtpTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        resultsExpected = {
            "scaqab10client01vm08.us.oracle.com": HEALTHCHECK_SUCC,
            "scaqab10client02vm08.us.oracle.com": HEALTHCHECK_FAIL
        }
        baseHealthCheckObject.mSetDomUs(resultsExpected.keys())

        for dom0, domU in self.mGetClubox().mReturnDom0DomUPair():
            _cmds = {
                self.mGetRegexLocal(): [
                    [
                        exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                    ]
                ],
                self.mGetRegexDomU(): [
                    [
                        exaMockCommand("/bin/uname -r", aRc=0,
                                       aStdout="4.1.12-124.52.4.el6uek.x86_64",
                                       aPersist=True),
                        exaMockCommand("/usr/sbin/ntpdate -q", aPersist=True,
                                       aRc=0 if domU == "scaqab10client01vm08.us.oracle.com" else 1)
                    ]
                ]
            }
            self.mPrepareMockCommands(_cmds)

            returnedResult = currentHealthObject.mCheckNtpTest(domU)
            self.assertEqual(resultsExpected[domU], returnedResult["hcTestResult"])

    def test_mCheckNtpTestDomUOL7_OL8(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckNtpTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        resultsExpected = {
            "scaqab10client01vm08.us.oracle.com": HEALTHCHECK_SUCC,
            "scaqab10client02vm08.us.oracle.com": HEALTHCHECK_FAIL
        }
        baseHealthCheckObject.mSetDomUs(resultsExpected.keys())

        for dom0, domU in self.mGetClubox().mReturnDom0DomUPair():
            _cmds = {
                self.mGetRegexLocal(): [
                    [
                        exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                    ]
                ],
                self.mGetRegexDomU(): [
                    [
                        exaMockCommand("/bin/uname -r", aRc=0,
                                       aStdout="4.1.12-124.52.4.el7uek.x86_64" if domU == "scaqab10client01vm08.us.oracle.com"
                                       else "5.4.17-2136.312.3.4.el8uek.x86_64",
                                       aPersist=True),
                        exaMockCommand("/usr/sbin/chronyd -Q 'server", aPersist=True,
                                       aRc=0 if domU == "scaqab10client01vm08.us.oracle.com" else 1)
                    ]
                ]
            }
            self.mPrepareMockCommands(_cmds)

            returnedResult = currentHealthObject.mCheckNtpTest(domU)
            self.assertEqual(resultsExpected[domU], returnedResult["hcTestResult"])

    def test_mNetworkPing(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mNetworkPing")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        dom0s = ["scaqab10adm01.us.oracle.com", "scaqab10adm02.us.oracle.com"]
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        baseHealthCheckObject.mSetDom0s(dom0s)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        for dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            _cmds = {
                self.mGetRegexDom0(): [
                    [
                        exaMockCommand("/bin/ping", aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0,
                                       aPersist=True)
                    ]
                ],
                self.mGetRegexLocal(): [
                    [
                        exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                    ]
                ]
            }
            self.mPrepareMockCommands(_cmds)

            nodeObj = currentHealthObject.mGetNode(dom0)
            cluNetObj = ebCluNetwork(dom0, {}, {}, nodeObj, baseHealthCheckObject, get_logger())
            returnedResult = currentHealthObject.mNetworkPing("1.2.3.4", cluNetObj)
            self.assertEqual(returnedResult, True if dom0 == "scaqab10adm01.us.oracle.com" else False)

    def test_mCheckNetworkPingTest(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckNetworkPingTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO

        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_SUCC,
            "scaqab10adm02.us.oracle.com": HEALTHCHECK_FAIL
        }
        baseHealthCheckObject.mSetDom0s(resultsExpected.keys())

        for dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            _cmds = {
                self.mGetRegexLocal(): [
                    [
                        exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                    ]
                ],
                self.mGetRegexDom0(): [
                    [
                        exaMockCommand("/usr/sbin/brctl show | grep 'vnet\|vif'",
                                       aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0, aPersist=True),
                        exaMockCommand("/bin/cat /sys/class/net/vmbondeth0/operstate",
                                       aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0,
                                       aStdout="down" if dom0 == "scaqab10adm01.us.oracle.com" else "up",
                                       aPersist=False),
                        exaMockCommand("/bin/cat /sys/class/net/vmbondeth1/operstate",
                                       aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0,
                                       aStdout="down" if dom0 == "scaqab10adm01.us.oracle.com" else "up",
                                       aPersist=False),
                        exaMockCommand("/sbin/ifconfig", aRc=0, aPersist=True),
                        exaMockCommand("/bin/cat /sys/class/net/vmbondeth",
                                       aRc=0 if dom0 == "scaqab10adm01.us.oracle.com" else 0, aStdout="up",
                                       aPersist=True),
                        exaMockCommand("/sbin/iptables -nvL", aRc=1, aStdout="random O/P", aPersist=True),
                        exaMockCommand("/sbin/iptables -I INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                        exaMockCommand("/sbin/iptables -D INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                        exaMockCommand("/sbin/arping -I", aRc=0 if dom0 == "scaqab10adm01.us.oracle.com" else 1,
                                       aPersist=True),
                        exaMockCommand("/sbin/arping -c", aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0,
                                       aPersist=True),
                        exaMockCommand("/bin/ping", aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0,
                                       aPersist=True),
                        exaMockCommand("/sbin/ip link del", aRc=0, aPersist=True),
                        exaMockCommand("/sbin/ip addr del", aRc=0, aPersist=True)
                    ]
                ]
            }
            self.mPrepareMockCommands(_cmds)

            returnedResult = currentHealthObject.mCheckNetworkPingTest(self.mGetClubox().mReturnDom0DomUPair()[1][0])
            self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])

    def test_mCheckNetworkPingTestinRevalidationAndElastic(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckNetworkPingTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO

        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_SUCC,
            "scaqab10adm02.us.oracle.com": HEALTHCHECK_FAIL
        }
        baseHealthCheckObject.mSetDom0s(resultsExpected.keys())

        for dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            if dom0 == "scaqab10adm01.us.oracle.com":
                baseHealthCheckObject.mSetReNetValidation(True)
                baseHealthCheckObject.mSetAnyRunningVMs(True)
            else:
                baseHealthCheckObject.mSetAnyRunningVMs(False)
                baseHealthCheckObject.mSetDeltaNetValidation(True)

            _cmds = {
                self.mGetRegexLocal(): [
                    [
                        exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                    ]
                ],
                self.mGetRegexDom0(): [
                    [
                        exaMockCommand("/usr/sbin/brctl show | grep 'vnet\|vif'",
                                       aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0, aPersist=True),
                        exaMockCommand("/bin/cat /sys/class/net/vmbondeth0/operstate",
                                       aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0,
                                       aStdout="down" if dom0 == "scaqab10adm01.us.oracle.com" else "up",
                                       aPersist=False),
                        exaMockCommand("/bin/cat /sys/class/net/vmbondeth1/operstate",
                                       aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0,
                                       aStdout="down" if dom0 == "scaqab10adm01.us.oracle.com" else "up",
                                       aPersist=False),
                        exaMockCommand("/sbin/ifconfig", aRc=0, aPersist=True),
                        exaMockCommand("/bin/cat /sys/class/net/vmbondeth",
                                       aRc=0 if dom0 == "scaqab10adm01.us.oracle.com" else 0, aStdout="up",
                                       aPersist=True),
                        exaMockCommand("/sbin/iptables -nvL", aRc=1, aStdout="random O/P", aPersist=True),
                        exaMockCommand("/sbin/iptables -I INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                        exaMockCommand("/sbin/iptables -D INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                        exaMockCommand("/sbin/arping -I", aRc=0 if dom0 == "scaqab10adm01.us.oracle.com" else 1,
                                       aPersist=True),
                        exaMockCommand("/sbin/arping -c", aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0,
                                       aPersist=True),
                        exaMockCommand("/bin/ping", aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0,
                                       aPersist=True),
                        exaMockCommand("/sbin/ip link del", aRc=0, aPersist=True),
                        exaMockCommand("/sbin/ip addr del", aRc=0, aPersist=True)
                    ]
                ]
            }
            self.mPrepareMockCommands(_cmds)

            returnedResult = currentHealthObject.mCheckNetworkPingTest(self.mGetClubox().mReturnDom0DomUPair()[1][0])
            self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])

    def test_mConfigureInterfaceFail_Vlan_Gateway(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckNetworkPingTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        # override NoVLAN to VLAN flow
        oldVlan = None
        changedNetObjs = []
        domU_mac = self.mGetClubox().mGetMachines().mGetMachineConfig("scaqab10client01vm08.us.oracle.com")
        net_list = domU_mac.mGetMacNetworks()
        eBoxNetworks = self.mGetClubox().mGetNetworks()
        for net in net_list:
            netobj = eBoxNetworks.mGetNetworkConfig(net)
            if netobj.mGetNetType() in ["backup"]:
                changedNetObjs.append(netobj)
                oldVlan = netobj.mGetNetVlanId()
                netobj.mSetNetVlanId("999")

        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_FAIL
        }
        baseHealthCheckObject.mSetDom0s(resultsExpected.keys())
        dom0 = "scaqab10adm01.us.oracle.com"

        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/sbin/brctl show | grep 'vnet\|vif'", aRc=0, aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/", aRc=-1, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        returnedResult = currentHealthObject.mCheckVlanIdTest(dom0)
        self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])

        # restore the Vlan ID back to original
        for netobj in changedNetObjs:
            netobj.mSetNetVlanId(oldVlan)

        returnedResult = currentHealthObject.mCheckGatewayTest(dom0)
        self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])

    def test_mConfigureInterfaceFail_Ntp_NetworkPing(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckNetworkPingTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_FAIL
        }
        baseHealthCheckObject.mSetDom0s(resultsExpected.keys())
        dom0 = "scaqab10adm01.us.oracle.com"

        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/uname -r", aRc=0,
                                   aStdout="4.1.12-124.52.4.el7uek.x86_64",
                                   aPersist=True),
                    exaMockCommand("/usr/sbin/brctl show | grep 'vnet\|vif'", aRc=0, aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/", aRc=-1, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        returnedResult = currentHealthObject.mCheckNtpTest(dom0)
        self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])

        returnedResult = currentHealthObject.mCheckNetworkPingTest(dom0)
        self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])

    def test_mCheckGatewayTest_skipIntfDown(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckGatewayTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)
        currentHealthObject.downIntfs = {"scaqab10adm01.us.oracle.com": ["eth5", "eth7"]}

        dom0 = "scaqab10adm01.us.oracle.com"
        domU = "scaqab10client01vm08.us.oracle.com"
        expectedCause = "This interface is down on the host"

        # override NoVLAN to VLAN flow
        oldVlan = None
        changedNetObjs = []
        domU_mac = self.mGetClubox().mGetMachines().mGetMachineConfig(domU)
        net_list = domU_mac.mGetMacNetworks()
        eBoxNetworks = self.mGetClubox().mGetNetworks()
        for net in net_list:
            netobj = eBoxNetworks.mGetNetworkConfig(net)
            if netobj.mGetNetType() in ["client", "backup"]:
                changedNetObjs.append(netobj)
                oldVlan = netobj.mGetNetVlanId()
                netobj.mSetNetVlanId("999")

        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_SUCC
        }
        baseHealthCheckObject.mSetDom0s(resultsExpected.keys())

        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/sbin/brctl show | grep 'vnet\|vif'",
                                   aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0, aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth0/operstate",
                                   aRc=0, aStdout="up", aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth1/operstate",
                                   aRc=0, aStdout="up", aPersist=True),
                    exaMockCommand("/sbin/ifconfig", aRc=0, aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/eth", aRc=0, aStdout="up", aPersist=True),
                    exaMockCommand("/sbin/iptables -nvL", aRc=1, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/iptables -I INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/iptables -D INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/arping", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip link del", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip addr del", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        returnedResult = currentHealthObject.mCheckGatewayTest(dom0)

        # restore the Vlan ID back to original
        for netobj in changedNetObjs:
            netobj.mSetNetVlanId(oldVlan)

        self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])
        self.assertEqual(returnedResult["hcMsgDetail"]["backup"]["eth7"]["status"], "Skipped")
        self.assertEqual(returnedResult["hcMsgDetail"]["client"]["eth5"]["status"], "Skipped")
        self.assertEqual(returnedResult["hcMsgDetail"]["backup"]["eth7"]["cause"], expectedCause)
        self.assertEqual(returnedResult["hcMsgDetail"]["client"]["eth5"]["cause"], expectedCause)

    def test_mCheckVlanIdTest_skipIntfDown(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckGatewayTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)
        currentHealthObject.downIntfs = {"scaqab10adm01.us.oracle.com": ["eth5", "eth7"]}

        dom0 = "scaqab10adm01.us.oracle.com"
        domU = "scaqab10client01vm08.us.oracle.com"
        expectedCause = "This interface is down on the host"

        # override NoVLAN to VLAN flow
        oldVlan = None
        changedNetObjs = []
        domU_mac = self.mGetClubox().mGetMachines().mGetMachineConfig(domU)
        net_list = domU_mac.mGetMacNetworks()
        eBoxNetworks = self.mGetClubox().mGetNetworks()
        for net in net_list:
            netobj = eBoxNetworks.mGetNetworkConfig(net)
            if netobj.mGetNetType() in ["client", "backup"]:
                changedNetObjs.append(netobj)
                oldVlan = netobj.mGetNetVlanId()
                netobj.mSetNetVlanId("999")

        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_SUCC
        }
        baseHealthCheckObject.mSetDom0s(resultsExpected.keys())

        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/sbin/brctl show | grep 'vnet\|vif'",
                                   aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0, aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth0/operstate",
                                   aRc=0, aStdout="up", aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth1/operstate",
                                   aRc=0, aStdout="up", aPersist=True),
                    exaMockCommand("/sbin/ifconfig", aRc=0, aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/eth", aRc=0, aStdout="up", aPersist=True),
                    exaMockCommand("/sbin/iptables -nvL", aRc=1, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/iptables -I INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/iptables -D INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/arping", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip link del", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip addr del", aRc=0, aPersist=True),
                    exaMockCommand("timeout 10 tcpdump -i", aRc=1, aPersist=True),
                    exaMockCommand("/bin/grep", aRc=1, aPersist=True),
                    exaMockCommand("/bin/ls -l /tmp/", aRc=0, aPersist=True),
                    exaMockCommand("/bin/rm -rf /tmp/", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        returnedResult = currentHealthObject.mCheckGatewayTest(dom0)

        # restore the Vlan ID back to original
        for netobj in changedNetObjs:
            netobj.mSetNetVlanId(oldVlan)

        self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])
        self.assertEqual(returnedResult["hcMsgDetail"]["backup"]["eth7"]["status"], "Skipped")
        self.assertEqual(returnedResult["hcMsgDetail"]["client"]["eth5"]["status"], "Skipped")
        self.assertEqual(returnedResult["hcMsgDetail"]["backup"]["eth7"]["cause"], expectedCause)
        self.assertEqual(returnedResult["hcMsgDetail"]["client"]["eth5"]["cause"], expectedCause)

    def test_mCheckDnsTest_skipIntfDown(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckGatewayTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)
        currentHealthObject.downIntfs = {"scaqab10adm01.us.oracle.com": ["eth5", "eth7"]}
        expectedHcDisplayStr = [
            'WARNING: Skipped test from down interface eth5 on the host scaqab10adm01.us.oracle.com.'
        ]
        dom0 = "scaqab10adm01.us.oracle.com"
        domU = "scaqab10client01vm08.us.oracle.com"
        expectedCause = "This interface is down on the host"

        # override NoVLAN to VLAN flow
        oldVlan = None
        changedNetObjs = []
        domU_mac = self.mGetClubox().mGetMachines().mGetMachineConfig(domU)
        net_list = domU_mac.mGetMacNetworks()
        eBoxNetworks = self.mGetClubox().mGetNetworks()
        for net in net_list:
            netobj = eBoxNetworks.mGetNetworkConfig(net)
            if netobj.mGetNetType() in ["client", "backup"]:
                changedNetObjs.append(netobj)
                oldVlan = netobj.mGetNetVlanId()
                netobj.mSetNetVlanId("999")

        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_FAIL
        }
        baseHealthCheckObject.mSetDom0s(resultsExpected.keys())

        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/sbin/brctl show | grep 'vnet\|vif'",
                                   aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0, aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth0/operstate",
                                   aRc=0, aStdout="up", aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth1/operstate",
                                   aRc=0, aStdout="up", aPersist=True),
                    exaMockCommand("/sbin/ifconfig", aRc=0, aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/eth", aRc=0, aStdout="up", aPersist=True),
                    exaMockCommand("/sbin/iptables -nvL", aRc=1, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/iptables -I INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/iptables -D INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/arping", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip route add", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip route del", aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/dig", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip link del", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip addr del", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        returnedResult = currentHealthObject.mCheckDnsTest(dom0)

        # restore the Vlan ID back to original
        for netobj in changedNetObjs:
            netobj.mSetNetVlanId(oldVlan)

        self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])
        self.assertEqual(returnedResult["hcMsgDetail"]["client"]["eth5"]["status"], "Skipped")
        self.assertEqual(returnedResult["hcMsgDetail"]["client"]["eth5"]["cause"], expectedCause)

    def test_mCheckNtpTest_skipIntfDown(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckGatewayTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)
        currentHealthObject.downIntfs = {"scaqab10adm01.us.oracle.com": ["eth5", "eth7"]}

        dom0 = "scaqab10adm01.us.oracle.com"
        domU = "scaqab10client01vm08.us.oracle.com"
        expectedCause = "This interface is down on the host"

        # override NoVLAN to VLAN flow
        oldVlan = None
        changedNetObjs = []
        domU_mac = self.mGetClubox().mGetMachines().mGetMachineConfig(domU)
        net_list = domU_mac.mGetMacNetworks()
        eBoxNetworks = self.mGetClubox().mGetNetworks()
        for net in net_list:
            netobj = eBoxNetworks.mGetNetworkConfig(net)
            if netobj.mGetNetType() in ["client"]:
                changedNetObjs.append(netobj)
                oldVlan = netobj.mGetNetVlanId()
                netobj.mSetNetVlanId("999")

        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_SUCC
        }
        baseHealthCheckObject.mSetDom0s(resultsExpected.keys())

        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/sbin/brctl show | grep 'vnet\|vif'",
                                   aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0, aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth0/operstate",
                                   aRc=0, aStdout="up", aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth1/operstate",
                                   aRc=0, aStdout="up", aPersist=True),
                    exaMockCommand("/bin/uname -r", aRc=0,
                                   aStdout="4.1.12-124.52.4.el6uek.x86_64" if dom0 == "scaqab10adm01.us.oracle.com"
                                   else "4.1.12-124.52.4.el7uek.x86_64",
                                   aPersist=True),
                    exaMockCommand("/sbin/ifconfig", aRc=0, aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/eth", aRc=0, aStdout="up", aPersist=True),
                    exaMockCommand("/sbin/iptables -nvL", aRc=1, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/iptables -I INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/iptables -D INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/arping", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip route add", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip route del", aRc=0, aPersist=True),
                    exaMockCommand("/usr/sbin/ntpdate -q", aRc=0, aPersist=True),
                    exaMockCommand("/usr/sbin/chronyd -Q 'server", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip link del", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip addr del", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        returnedResult = currentHealthObject.mCheckNtpTest(dom0)

        # restore the Vlan ID back to original
        for netobj in changedNetObjs:
            netobj.mSetNetVlanId(oldVlan)

        self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])
        self.assertEqual(returnedResult["hcMsgDetail"]["client"]["eth5"]["status"], "Skipped")
        self.assertEqual(returnedResult["hcMsgDetail"]["client"]["eth5"]["cause"], expectedCause)

    def test_mCheckNetworkPingTest_skipIntfDown(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckGatewayTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)
        currentHealthObject.downIntfs = {"scaqab10adm01.us.oracle.com": ["eth5", "eth7"]}

        dom0 = "scaqab10adm01.us.oracle.com"
        domU = "scaqab10client01vm08.us.oracle.com"
        expectedCause = "This interface is down on the host"

        # override NoVLAN to VLAN flow
        oldVlan = None
        changedNetObjs = []
        domU_mac = self.mGetClubox().mGetMachines().mGetMachineConfig(domU)
        net_list = domU_mac.mGetMacNetworks()
        eBoxNetworks = self.mGetClubox().mGetNetworks()
        for net in net_list:
            netobj = eBoxNetworks.mGetNetworkConfig(net)
            if netobj.mGetNetType() in ["client", "backup"]:
                changedNetObjs.append(netobj)
                oldVlan = netobj.mGetNetVlanId()
                netobj.mSetNetVlanId("999")

        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_SUCC
        }
        baseHealthCheckObject.mSetDom0s(resultsExpected.keys())

        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/sbin/brctl show | grep 'vnet\|vif'",
                                   aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0, aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth0/operstate",
                                   aRc=0, aStdout="up", aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth1/operstate",
                                   aRc=0, aStdout="up", aPersist=True),
                    exaMockCommand("/sbin/ifconfig", aRc=0, aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/eth", aRc=0, aStdout="up", aPersist=True),
                    exaMockCommand("/sbin/iptables -nvL", aRc=1, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/iptables -I INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/iptables -D INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/arping", aRc=0, aPersist=True),
                    exaMockCommand("/bin/ping", aRc=1, aPersist=True),
                    exaMockCommand("/sbin/ip link del", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip addr del", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        returnedResult = currentHealthObject.mCheckGatewayTest(dom0)

        # restore the Vlan ID back to original
        for netobj in changedNetObjs:
            netobj.mSetNetVlanId(oldVlan)

        self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])
        self.assertEqual(returnedResult["hcMsgDetail"]["backup"]["eth7"]["status"], "Skipped")
        self.assertEqual(returnedResult["hcMsgDetail"]["client"]["eth5"]["status"], "Skipped")
        self.assertEqual(returnedResult["hcMsgDetail"]["backup"]["eth7"]["cause"], expectedCause)
        self.assertEqual(returnedResult["hcMsgDetail"]["client"]["eth5"]["cause"], expectedCause)

    def test_mCheckDnsTest_skipGatewayUnreachable(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckDnsTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)
        currentHealthObject.intermediateResult = INT_RESULT

        # Set other DNS servers
        _machines = self.mGetClubox().mGetMachines()
        _domU_mac = _machines.mGetMachineConfig("scaqab10client01vm08.us.oracle.com")
        old_dns = _domU_mac.mGetDnsServers()
        new_dns = "8.8.8.8"
        _domU_mac.mSetDnsServers([new_dns])

        # DNS resolutions will fail, hence both tests compared for failure assertion
        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_FAIL
        }
        baseHealthCheckObject.mSetDom0s(resultsExpected.keys())

        dom0 = "scaqab10adm01.us.oracle.com"
        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/sbin/brctl show | grep 'vnet\|vif'",
                                   aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0, aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth0/operstate",
                                   aRc=0, aStdout="up", aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth1/operstate",
                                   aRc=0, aStdout="up", aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/eth", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ifconfig", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/iptables -nvL", aRc=1, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/iptables -I INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/iptables -D INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/arping", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip route add", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip route del", aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/dig", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip link del", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip addr del", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        returnedResult = currentHealthObject.mCheckDnsTest(dom0)
        self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])
        self.assertEqual(returnedResult["hcMsgDetail"]["client"]["vmbondeth0"][new_dns]["status"], "Skipped")
        self.assertEqual(returnedResult["hcMsgDetail"]["client"]["vmbondeth0"][new_dns]["cause"],
                         "Gateway is not reachable from the interface vmbondeth0 and DNS IP 8.8.8.8 not in the same subnet as the client network.")
        _domU_mac.mSetDnsServers(old_dns)

    def test_mCheckNtpTest_skipGatewayUnreachable(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckNtpTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)
        currentHealthObject.intermediateResult = INT_RESULT

        # Set other DNS servers
        _machines = self.mGetClubox().mGetMachines()
        _domU_mac = _machines.mGetMachineConfig("scaqab10client01vm08.us.oracle.com")
        old_ntp = _domU_mac.mGetNtpServers()
        new_ntp = "8.8.8.8"
        _domU_mac.mSetNtpServers([new_ntp])

        # DNS resolutions will fail, hence both tests compared for failure assertion
        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_FAIL
        }
        baseHealthCheckObject.mSetDom0s(resultsExpected.keys())

        dom0 = "scaqab10adm01.us.oracle.com"
        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/sbin/brctl show | grep 'vnet\|vif'",
                                   aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0, aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth0/operstate",
                                   aRc=0, aStdout="up", aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/vmbondeth1/operstate",
                                   aRc=0, aStdout="up", aPersist=True),
                    exaMockCommand("/bin/cat /sys/class/net/eth", aRc=0, aPersist=True),
                    exaMockCommand("/bin/uname -r", aRc=0,
                                   aStdout="4.1.12-124.52.4.el6uek.x86_64" if dom0 == "scaqab10adm01.us.oracle.com"
                                   else "4.1.12-124.52.4.el7uek.x86_64",
                                   aPersist=True),
                    exaMockCommand("/sbin/ifconfig", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/iptables -nvL", aRc=1, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/iptables -I INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/iptables -D INPUT -i", aRc=0, aStdout="random O/P", aPersist=True),
                    exaMockCommand("/sbin/arping", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip route add", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip route del", aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/dig", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip link del", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/ip addr del", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        returnedResult = currentHealthObject.mCheckNtpTest(dom0)
        self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])
        self.assertEqual(returnedResult["hcMsgDetail"]["client"]["vmbondeth0"][new_ntp]["status"], "Skipped")
        self.assertEqual(returnedResult["hcMsgDetail"]["client"]["vmbondeth0"][new_ntp]["cause"],
                         "Gateway is not reachable from the interface vmbondeth0 and NTP IP 8.8.8.8 not in the same subnet as the client network.")

    def test_networkDetectionError_allTests(self):
        ebLogInfo("")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        dom0 = "scaqab10adm01.us.oracle.com"
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks[dom0] = DOM0_NETWORK_INFO_ERROR
        baseHealthCheckObject.mSetDom0s([dom0])
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_FAIL
        }

        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                ]
            ]
        }

        def commonAssertions(returnedResult):
            self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])
            self.assertEqual(returnedResult["hcMsgDetail"]["status"], "Fail")
            self.assertEqual(returnedResult["hcMsgDetail"]["cause"], "Skipped.")

        self.mPrepareMockCommands(_cmds)
        # Link status test
        returnedResult = currentHealthObject.mCheckLinkStatusTest(dom0)
        self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])
        self.assertEqual(returnedResult["hcMsgDetail"]["status"], "Fail")
        self.assertEqual(returnedResult["hcMsgDetail"]["cause"],
                         "The runtime state of physical interfaces on host 'scaqab10adm01.us.oracle.com', does not match any predefined configuration for ExaCC.")
        self.assertEqual(returnedResult["hcMsgDetail"]["resolution"],
                         "Please check the status of physical interfaces.")
        # Create bond test
        returnedResult = currentHealthObject.mCheckCreateBondTest(dom0)
        commonAssertions(returnedResult)
        # Delete bond test
        returnedResult = currentHealthObject.mCheckDeleteBondTest(dom0)
        commonAssertions(returnedResult)
        # Gateway test
        returnedResult = currentHealthObject.mCheckGatewayTest(dom0)
        commonAssertions(returnedResult)
        # Vlan ID test
        returnedResult = currentHealthObject.mCheckVlanIdTest(dom0)
        commonAssertions(returnedResult)
        # Dns test
        returnedResult = currentHealthObject.mCheckDnsTest(dom0)
        commonAssertions(returnedResult)
        # Ntp test
        returnedResult = currentHealthObject.mCheckNtpTest(dom0)
        commonAssertions(returnedResult)
        # Network ping test
        returnedResult = currentHealthObject.mCheckNetworkPingTest(dom0)
        commonAssertions(returnedResult)

    def test_hostNotConnectable_allTests(self):
        ebLogInfo("")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        dom0 = "scaqab10adm01.us.oracle.com"
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks[dom0] = DOM0_NETWORK_INFO_ERROR
        baseHealthCheckObject.mSetDom0s([dom0])
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_FAIL
        }

        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping", aRc=1, aPersist=True)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        CAUSE = "Unable to connect to host scaqab10adm01.us.oracle.com."
        RESOLUTION = "Please try again, if issue persists please contact Oracle support."

        def commonAssertions(returnedResult):
            self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])
            self.assertEqual(returnedResult["hcMsgDetail"]["status"], "Fail")
            self.assertEqual(returnedResult["hcMsgDetail"]["cause"], CAUSE)
            self.assertEqual(returnedResult["hcMsgDetail"]["resolution"], RESOLUTION)
        
        # Config setup test
        returnedResult = currentHealthObject.mCheckConfigSetup(dom0)
        commonAssertions(returnedResult)
        # Config revert test
        returnedResult = currentHealthObject.mCheckConfigRevert(dom0)
        commonAssertions(returnedResult)
        # Link status test
        returnedResult = currentHealthObject.mCheckLinkStatusTest(dom0)
        commonAssertions(returnedResult)
        # Create bond test
        returnedResult = currentHealthObject.mCheckCreateBondTest(dom0)
        commonAssertions(returnedResult)
        # Delete bond test
        returnedResult = currentHealthObject.mCheckDeleteBondTest(dom0)
        commonAssertions(returnedResult)
        # Gateway test
        returnedResult = currentHealthObject.mCheckGatewayTest(dom0)
        commonAssertions(returnedResult)
        # Vlan ID test
        returnedResult = currentHealthObject.mCheckVlanIdTest(dom0)
        commonAssertions(returnedResult)
        # Dns test
        returnedResult = currentHealthObject.mCheckDnsTest(dom0)
        commonAssertions(returnedResult)
        # Ntp test
        returnedResult = currentHealthObject.mCheckNtpTest(dom0)
        commonAssertions(returnedResult)
        # Network ping test
        returnedResult = currentHealthObject.mCheckNetworkPingTest(dom0)
        commonAssertions(returnedResult)

    def test_mCheckConfigSetup(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckConfigSetup")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_SUCC,
            "scaqab10adm02.us.oracle.com": HEALTHCHECK_SUCC
        }
        baseHealthCheckObject.mSetDom0s(resultsExpected.keys())

        for dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            _cmds = {
                self.mGetRegexLocal(): [
                    [
                        exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                    ]
                ],
                self.mGetRegexDom0(): [
                    [
                        exaMockCommand("/usr/sbin/brctl show | grep 'vnet\|vif'",
                                       aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0, aPersist=True),
                        exaMockCommand("/bin/cat /sys/class/net/vmbondeth0/operstate",
                                       aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0,
                                       aStdout="down" if dom0 == "scaqab10adm01.us.oracle.com" else "up",
                                       aPersist=False),
                        exaMockCommand("/bin/cat /sys/class/net/vmbondeth1/operstate",
                                       aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0,
                                       aStdout="down" if dom0 == "scaqab10adm01.us.oracle.com" else "up",
                                       aPersist=False),
                        exaMockCommand("/usr/sbin/sysctl -n net.ipv4.conf.all.arp_ignore", aRc=0, aStdout="0",
                                       aPersist=False),
                        exaMockCommand("/usr/sbin/sysctl -n net.ipv4.conf.all.arp_announce", aRc=0, aStdout="2",
                                       aPersist=True),
                        exaMockCommand("/bin/cat sysctl.conf | grep 'net.ipv4.conf.all.arp_ignore'",
                                       aRc=0, aStdout="net.ipv4.conf.all.arp_ignore=0", aPersist=False),
                        exaMockCommand("/bin/cat sysctl.conf | grep 'net.ipv4.conf.all.arp_announce'",
                                       aRc=0, aStdout="net.ipv4.conf.all.arp_announce=2", aPersist=True),
                        exaMockCommand("/bin/cp", aRc=0, aPersist=True),
                        exaMockCommand("/bin/sed", aRc=0, aPersist=True),
                        exaMockCommand("/usr/sbin/sysctl -p", aRc=0, aStdout="random O/P", aPersist=True),
                        exaMockCommand("/usr/sbin/sysctl -n net.ipv4.conf.all.arp_ignore", aRc=0, aStdout="1",
                                       aPersist=True),
                        exaMockCommand("/bin/cat sysctl.conf | grep 'net.ipv4.conf.all.arp_ignore'",
                                       aRc=0, aStdout="net.ipv4.conf.all.arp_ignore=1", aPersist=True)
                    ]
                ]
            }
            self.mPrepareMockCommands(_cmds)
            returnedResult = currentHealthObject.mCheckConfigSetup(dom0)
            self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])

    def test_mCheckConfigRevert(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckConfigRevert")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        baseHealthCheckObject._dom0Networks = DOM0_NETWORK_INFO
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)
        currentHealthObject.updatedSysctlProperties = [("net.ipv4.conf.all.arp_ignore", 0)]

        resultsExpected = {
            "scaqab10adm01.us.oracle.com": HEALTHCHECK_SUCC,
            "scaqab10adm02.us.oracle.com": HEALTHCHECK_SUCC
        }
        baseHealthCheckObject.mSetDom0s(resultsExpected.keys())

        for dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            _cmds = {
                self.mGetRegexLocal(): [
                    [
                        exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                    ]
                ],
                self.mGetRegexDom0(): [
                    [
                        exaMockCommand("/usr/sbin/brctl show | grep 'vnet\|vif'",
                                       aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0, aPersist=True),
                        exaMockCommand("/bin/cat /sys/class/net/vmbondeth0/operstate",
                                       aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0,
                                       aStdout="down" if dom0 == "scaqab10adm01.us.oracle.com" else "up",
                                       aPersist=False),
                        exaMockCommand("/bin/cat /sys/class/net/vmbondeth1/operstate",
                                       aRc=1 if dom0 == "scaqab10adm01.us.oracle.com" else 0,
                                       aStdout="down" if dom0 == "scaqab10adm01.us.oracle.com" else "up",
                                       aPersist=False),
                        exaMockCommand("/usr/sbin/sysctl -n net.ipv4.conf.all.arp_ignore", aRc=0, aStdout="1",
                                       aPersist=False),
                        exaMockCommand("/bin/cat sysctl.conf | grep 'net.ipv4.conf.all.arp_ignore'",
                                       aRc=0, aStdout="net.ipv4.conf.all.arp_ignore=1", aPersist=False),
                        exaMockCommand("/bin/cp", aRc=0, aPersist=True),
                        exaMockCommand("/bin/sed", aRc=0, aPersist=True),
                        exaMockCommand("/usr/sbin/sysctl -p", aRc=0, aStdout="random O/P", aPersist=True),
                        exaMockCommand("/usr/sbin/sysctl -n net.ipv4.conf.all.arp_ignore", aRc=0, aStdout="0",
                                       aPersist=True),
                        exaMockCommand("/bin/cat sysctl.conf | grep 'net.ipv4.conf.all.arp_ignore'",
                                       aRc=0, aStdout="net.ipv4.conf.all.arp_ignore=0", aPersist=True)
                    ]
                ]
            }
            self.mPrepareMockCommands(_cmds)
            returnedResult = currentHealthObject.mCheckConfigRevert(dom0)
            self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])

    # End - Network Validation Unit Tests

    def test_mParseOratab(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mParseOratab")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)
        commandToExecute = "cat /etc/oratab"
        _cmds = {
                self.mGetRegexDom0(): [
                    [
                        exaMockCommand(commandToExecute, aRc=0, aStdout=ORATAB_OP, aPersist=True)
                    ]
                ],
                self.mGetRegexLocal(): [
                    [
                        exaMockCommand("/bin/ping", aRc=0, aPersist=True)
                    ]
                ]
            }
        self.mPrepareMockCommands(_cmds)

        dom0 = self.mGetClubox().mReturnDom0DomUPair()[0][0]
        thisNode = currentHealthObject.mGetNode(dom0)
        returnedResult = currentHealthObject.mParseOratab(thisNode)
        self.assertEqual(len(returnedResult), 3)
        self.assertEqual(returnedResult[0][0], 'orcl16021950')

    def test_mPreProvSystemChecks(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mPreProvSystemChecks")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)
        self.mGetClubox()._exaBoxCluCtrl__shared_env = True

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/System.img", aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/GuestImages/scaqab10client02vm08.us.oracle.com/System.img", aRc=1, aPersist=True),
                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0", aPersist=True)
                ],
                [
                    exaMockCommand("xm info |grep 'free_memory'", aRc=0, aStdout="free_memory            : 1800", aPersist=True)
                ],
                [
                    exaMockCommand("xm list", aRc=0, aStdout = XM_LIST_OP, aPersist=True)
                ]
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("ping -c 1 -W 4 scaqab10adm01.us.oracle.com ", aRc=0, aPersist=True),
                    exaMockCommand("ping -c 1 -W 4 scaqab10adm02.us.oracle.com ", aRc=0, aPersist=True)
                ]
            ]
        }

        resultsExpected = {"scaqab10adm01.us.oracle.com": HEALTHCHECK_FAIL, "scaqab10adm02.us.oracle.com": HEALTHCHECK_SUCC}

        self.mPrepareMockCommands(_cmds)

        for dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            returnedResult = currentHealthObject.mPreProvSystemChecks(dom0)
            self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])

    def test_mCheckRootSpace(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckRootSpace")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        resultsExpected = {"scaqab10adm01.us.oracle.com": HEALTHCHECK_SUCC, "scaqab10adm02.us.oracle.com": HEALTHCHECK_FAIL}
        commandToExecute = 'df -P / | tail -1 | awk \'0+$5 >= 85 {print}\''

        for dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            _cmds = {
                self.mGetRegexDom0(): [
                    [
                        exaMockCommand(commandToExecute, aRc=0, aStdout="/dev/mapper/VGExaDb-LVDbSys3    30832548 15103436  14139864      10% /" if dom0 == "scaqab10adm02.us.oracle.com" else "", aPersist=True)
                    ]
                ]
            }
            self.mPrepareMockCommands(_cmds)

            returnedResult = currentHealthObject.mCheckRootSpace(dom0)
            self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])

    def test_mCheckSshTest_mCheckPingTest(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckSshTest and HealthCheck.mCheckPingTest")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("ping -c 1 -W 4 scaqab10adm01.us.oracle.com ", aRc=1, aPersist=True),
                    exaMockCommand("ping -c 1 -W 4 scaqab10adm02.us.oracle.com ", aRc=0, aPersist=True)
                ]
            ]
        }

        resultsExpected = {"scaqab10adm01.us.oracle.com": HEALTHCHECK_FAIL, "scaqab10adm02.us.oracle.com": HEALTHCHECK_SUCC}

        self.mPrepareMockCommands(_cmds)

        for dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            returnedResult = currentHealthObject.mCheckSshTest(dom0)
            self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])
            returnedResult = currentHealthObject.mCheckPingTest(dom0)
            self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])

    def test_mCheckStaleLocks(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckStaleLocks")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        baseHealthCheckObject = ebCluHealth(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), baseHealthCheckObject)

        resultsExpected = {"scaqab10adm01.us.oracle.com": HEALTHCHECK_SUCC, "scaqab10adm02.us.oracle.com": HEALTHCHECK_FAIL}
        for dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            _cmds = {
                self.mGetRegexLocal(): [
                    [
                        exaMockCommand("ping -c 1 -W 4 scaqab10adm01.us.oracle.com ", aRc=0, aPersist=True),
                        exaMockCommand("ping -c 1 -W 4 scaqab10adm02.us.oracle.com ", aRc=0, aPersist=True)
                    ]
                ],
                self.mGetRegexDom0(): [
                    [
                        exaMockCommand("cat /tmp/exacs_dom0_lock", aRc=0, aStdout="4c5a9a1e-e4fb-11eb-babf-0000170085cb" if dom0 == "scaqab10adm02.us.oracle.com" else "", aPersist=True)
                    ]
                ]
            }
            self.mPrepareMockCommands(_cmds)
            returnedResult = currentHealthObject.mCheckStaleLocks(dom0)
            self.assertEqual(resultsExpected[dom0], returnedResult["hcTestResult"])

    def test_mCheckFlashCache(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckFlashCache")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        fullOptions.healthcheck = "custom"
        fullOptions.jsonconf = {"targetHosts": "cells"}
        cluHealthCheck = ebCluHealthCheck(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), cluHealthCheck)

        resultsExpected = {
            "scaqab10celadm01.us.oracle.com": [HEALTHCHECK_SUCC, "normal"],
            "scaqab10celadm02.us.oracle.com": [HEALTHCHECK_FAIL, "warning - degraded"],
            "scaqab10celadm03.us.oracle.com": [HEALTHCHECK_FAIL, None]
            }

        for cell in self.mGetClubox().mReturnCellNodes():
            flashCacheOutput = FLASHCACHE_NORMAL
            if cell == "scaqab10celadm02.us.oracle.com":
                flashCacheOutput = FLASHCACHE_DEGRADED
            elif cell == "scaqab10celadm03.us.oracle.com":
                flashCacheOutput = ""
            _cmds = {
            self.mGetRegexCell(): [
                        [
                            exaMockCommand("cellcli -e list flashcache detail", aRc=0, aStdout= flashCacheOutput, aPersist=True)
                        ]
                    ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("ping -c 1 -W 4 scaqab10celadm01.us.oracle.com ", aRc=0, aPersist=True),
                    exaMockCommand("ping -c 1 -W 4 scaqab10celadm02.us.oracle.com ", aRc=0, aPersist=True),
                    exaMockCommand("ping -c 1 -W 4 scaqab10celadm03.us.oracle.com ", aRc=0, aPersist=True)
                ]
            ]
                }
            self.mPrepareMockCommands(_cmds)

            returnedResult = currentHealthObject.mCheckFlashCache(cell)
            cellStatus = returnedResult.get("hcMsgDetail").get("status:", None)
            self.assertEqual(resultsExpected[cell][0], returnedResult["hcTestResult"])
            self.assertEqual(resultsExpected[cell][1], cellStatus)

    def test_mCheckDBStatusOnCell(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckDBStatusOnCell")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        fullOptions.healthcheck = "custom"
        fullOptions.jsonconf = {"targetHosts": "cells"}
        cluHealthCheck = ebCluHealthCheck(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), cluHealthCheck)

        resultsExpected = {
            "scaqab10celadm01.us.oracle.com": HEALTHCHECK_SUCC,
            "scaqab10celadm02.us.oracle.com": HEALTHCHECK_SUCC,
            "scaqab10celadm03.us.oracle.com": HEALTHCHECK_FAIL
            }

        for cell in self.mGetClubox().mReturnCellNodes():
            cellDBList = CELLDB_LIST_NORMAL
            if cell == "scaqab10celadm02.us.oracle.com":
                cellDBList = CELLDB_LIST_DBPRESENT
            elif cell == "scaqab10celadm03.us.oracle.com":
                cellDBList = CELLDB_LIST_ERROR
            _cmds = {
            self.mGetRegexCell(): [
                        [
                            exaMockCommand("cellcli -e LIST DATABASE", aRc=0, aStdout= cellDBList, aPersist=True)
                        ]
                    ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("ping -c 1 -W 4 scaqab10celadm01.us.oracle.com ", aRc=0, aPersist=True),
                    exaMockCommand("ping -c 1 -W 4 scaqab10celadm02.us.oracle.com ", aRc=0, aPersist=True),
                    exaMockCommand("ping -c 1 -W 4 scaqab10celadm03.us.oracle.com ", aRc=0, aPersist=True)
                ]
            ]
                }
            self.mPrepareMockCommands(_cmds)

            returnedResult = currentHealthObject.mCheckDBStatusOnCell(cell)
            self.assertEqual(resultsExpected[cell], returnedResult["hcTestResult"])

if __name__ == "__main__":
    unittest.main()
