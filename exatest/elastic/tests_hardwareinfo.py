"""

 $Header: 

 Copyright (c) 2020, 2021, Oracle and/or its affiliates.

 NAME:
      tests_hardwareinfo.py - Unitest for hardwareinfo

 DESCRIPTION:
      Run tests for hardwareinfo

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
       naps  11/30/21 - code coverage for hardwareinfo
       naps  11/30/21 - Creation of the file
"""

import unittest

from exabox.core.Context import get_gcontext
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo

from exabox.elastic.HardwareInfo import ebHardwareInfo
cell_detail_out = """	 name:                   scaqae14celadm01
	 accessLevelPerm:        remoteLoginEnabled
	 bbuStatus:              normal
	 cellVersion:            OSS_21.2.0.0.0_LINUX.X64_210514
	 cpuCount:               64/64
	 diagHistoryDays:        7
	 doNotServiceLEDStatus:  off
	 fanCount:               8/8
	 fanStatus:              normal
	 flashCacheMode:         WriteBack
	 httpsAccess:            ALL
	 id:                     1809XC20F4
	 ilomIpAddress:          10.31.26.232
	 interconnectCount:      2
	 interconnect1:          re0
	 interconnect2:          re1
	 iormBoost:              0.0
	 ipaddress1:             192.168.115.244/24
	 ipaddress2:             192.168.115.245/24
	 kernelVersion:          4.14.35-2047.502.5.el7uek.x86_64
	 locatorLEDStatus:       off
	 makeModel:              Oracle Corporation ORACLE SERVER X8-2L High Capacity
	 managementIpAddress:    10.31.26.210
	 memoryGB:               188
	 metricHistoryDays:      7
	 offloadGroupEvents:    
	 powerCount:             2/2
	 powerStatus:            normal
	 releaseImageStatus:     success
	 releaseVersion:         21.2.1.0.0.210514
	 rpmVersion:             cell-21.2.1.0.0_LINUX.X64_210514-1.x86_64
	 releaseTrackingBug:     32849515
	 status:                 online
	 syslogFormat:           "%TIMESTAMP:::date-rfc3339% %HOSTNAME% %syslogtag%%syslogseverity-text%:%msg:::sp-if-no-1st-sp%%msg:::drop-last-lf%\n"
	 temperatureReading:     32.0
	 temperatureStatus:      normal
	 upTime:                 37 days, 11:05
	 usbStatus:              normal
	 cellsrvStatus:          running
	 msStatus:               running
	 rsStatus:               running
"""

cell_detail_phy_out = """	 8.91015625T
	 8.91015625T
	 8.91015625T
	 8.91015625T
	 8.91015625T
	 8.91015625T
	 8.91015625T
	 8.91015625T
	 8.91015625T
	 8.91015625T
	 8.91015625T
	 8.91015625T
	 2.910957656800746917724609375T
	 2.910957656800746917724609375T
	 2.910957656800746917724609375T
	 2.910957656800746917724609375T
	 2.910957656800746917724609375T
	 2.910957656800746917724609375T
	 2.910957656800746917724609375T
	 2.910957656800746917724609375T
	 139.698386669158935546875G
	 139.698386669158935546875G
"""

xm_info_out = """host                   : scaqak01adm04.us.oracle.com
release                : 4.1.12-124.52.4.el6uek.x86_64
version                : #2 SMP Tue Jun 22 20:34:01 PDT 2021
machine                : x86_64
nr_cpus                : 104
nr_nodes               : 2
cores_per_socket       : 26
threads_per_core       : 2
cpu_mhz                : 2693
hw_caps                : bfebfbff:2c100800:00000000:05747f00:77fefbff:00000000:00000121:d39ff7eb
virt_caps              : hvm hvm_directio
total_memory           : 785066
free_memory            : 528187
free_cpus              : 0
xen_major              : 4
xen_minor              : 4
xen_extra              : .4OVM
xen_caps               : xen-3.0-x86_64 xen-3.0-x86_32p hvm-3.0-x86_32 hvm-3.0-x86_32p hvm-3.0-x86_64 
xen_scheduler          : credit
xen_pagesize           : 4096
platform_params        : virt_start=0xffff800000000000
xen_changeset          : 
xen_commandline        : dom0_mem=9G,max:9G dom0_max_vcpus=4 no-bootscrub loglvl=all guest_loglvl=error/all com1=115200,8n1 conring_size=1m console=com1 console_to_ring crashkernel=448M@128M xsave=1
cc_compiler            : gcc (GCC) 4.4.7 20120313 (Red Hat 4.4.7-18.0.7)
cc_compile_by          : mockbuild
cc_compile_domain      : us.oracle.com
cc_compile_date        : Tue Jun 15 09:39:51 PDT 2021
xend_config_format     : 4
"""
class ebTestebHardwareInfo(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestebHardwareInfo, self).setUpClass(False, False)

    def test_cell_hwinfo(self):
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("hostname -i", aStdout="10.31.115.36"),
                    exaMockCommand("hostname", aStdout="scaqae14celadm01.us.oracle.com"),
                    exaMockCommand("cellcli -e list cell detail", aStdout=cell_detail_out),
                    exaMockCommand("cellcli -e list physicaldisk attributes physicalSize", aStdout=cell_detail_phy_out)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        _hwInfoObj = ebHardwareInfo('cell', 'scaqae14celadm01.us.oracle.com')
        _hwInfo = _hwInfoObj.mGetInfo()
        self.assertEqual(_hwInfo['ipaddress'], '10.31.115.36')
        self.assertEqual(_hwInfo['fullhostname'], 'scaqae14celadm01.us.oracle.com')
        self.assertEqual(_hwInfo['local_storage_gb'], '419409.92')

    def test_compute_hwinfo(self):
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("exadata.img.hw --get model", aStdout="ORACLE SERVER X8-2"),
                    exaMockCommand("hostname -i", aStdout="10.31.115.37"),
                    exaMockCommand("hostname", aStdout="scaqae14adm01.us.oracle.com"),
                    exaMockCommand("xm info", aStdout=xm_info_out),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        _hwInfoObj = ebHardwareInfo('compute', 'scaqae14adm01.us.oracle.com')
        _hwInfo = _hwInfoObj.mGetInfo()
        self.assertEqual(_hwInfo['model'], 'ORACLE SERVER X8-2')
        self.assertEqual(_hwInfo['fullhostname'], 'scaqae14adm01.us.oracle.com')
        self.assertEqual(_hwInfo['ipaddress'], '10.31.115.37')
        self.assertEqual(_hwInfo['total_cores'], 52)

if __name__ == '__main__':
    unittest.main() 
