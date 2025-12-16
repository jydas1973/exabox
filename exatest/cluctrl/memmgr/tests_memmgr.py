from asyncio.log import logger
import unittest
import io
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from unittest.mock import patch, MagicMock, PropertyMock, mock_open, Mock
import os
import re

DB_INFO = """{"id": "123","status":"Pass","min_reqd_hugepages_memory":"4 GB","is_new_mem_sz_allowed":1,"logfile":"/tmp/file.log","Log":"get for ALL clusterDBs succeeded on Node scaqan03dv0101.us.oracle.com","get":{"current_total_sga":"12 GB","min_req_mem":"30GB","consolidated_info":"Demo","error":[],"nodes":[{"node_name":"scaqan03dv0101","vm_mem_info":{"info":"scaqan03dv0101 Used Memory: 15 GB.Available Memory: 13 GB","total_memory":"28 GB","free_memory":"5 GB","buffer":"0 GB","cache":"4 GB","free_hugepages_memory":"8 GB"}},{"node_name":"scaqan03dv0201","vm_mem_info":{"info":"scaqan03dv0201 UsedMemory: 14 GB. Available Memory: 14 GB","buffer":"0 GB","free_hugepages_memory":"8 GB","total_memory":"28 GB","free_memory":"6 GB","cache":"3 GB"}}],"current_total_pga":"0 GB"}}"""


aHaveDBStdout = """
NAME=ora.db121244.db
TYPE=ora.database.type
TARGET=ONLINE                  , ONLINE
STATE=ONLINE on scaqak02dv0503, ONLINE on scaqak02dv0603

NAME=ora.db121960.db
TYPE=ora.database.type
TARGET=ONLINE                  , ONLINE
STATE=ONLINE on scaqak02dv0503, ONLINE on scaqak02dv0603

NAME=ora.db18342.db
TYPE=ora.database.type
TARGET=ONLINE                  , ONLINE
STATE=ONLINE on scaqak02dv0503, ONLINE on scaqak02dv0603
"""

aDBStateStdout = """
STATE=ONLINE
NAME=ora.db112265.db 2 1
TYPE=ora.database.type
TARGET=ONLINE
STATE=ONLINE
"""

aHaveDBretCode = 0

cmdOutput1="""xen
00000000-0000-0000-0000-000000000000
"""



_xmList1 = """Name                                        ID   Mem VCPUs      State   Time(s)
Domain-0                                     0  8746     4     r----- 2145201.6
scaqab10client01vm08.us.oracle.com           8 92163    10     -b----  51637.6
"""

_xmList2 = """Name                                        ID   Mem VCPUs      State   Time(s)
Domain-0                                     0  8746     4     r----- 2145201.6
scaqab10client02vm08.us.oracle.com           8 92163    10     -b----  51637.6
"""

_vm_cfg_prev_list = """/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev1
/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev2
/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev3
/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev4
/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev5
/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev6
/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev7
/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev8
/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev9
/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev10
/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev11
/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev12"""

class TestMemMgr(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateDatabase=True)
        super().setUpClass()

    def setUp(self):
        self.mGetClubox()._exaBoxCluCtrl__ociexacc = False
        #self.mGetClubox()._exaBoxCluCtrl__kvm_enabled = True
        get_gcontext().mSetConfigOption('kvm_var_size',None)
        self.mGetClubox().mRegisterVgComponents()

    @patch('exabox.ovm.clucontrol.node_cmd_abs_path_check')
    @patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', return_value=0)
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog')
    @patch('exabox.ovm.cludbaas.ebCluDbaas.mWaitForJobComplete', return_value=0)
    @patch('exabox.ovm.cludbaas.ebCluDbaas.mBaseCopyFileToDomU', return_value=0)
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckDBIsUp', return_value=True)
    def test_insufficient_mem_dom0(self,mock_pathcheck1,mock_exitstatus,mock_executelog, mock_mwaitforjobtocomplete, mock_mcopyfiletodomu, mock_mcheckdbisup):

        _vmcfg = self.mGetResourcesTextFile("cmd_vmcfg.txt")

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i /var/opt/oracle/log/grid/get_exatest.json.*", aRc=0),
                    exaMockCommand("/bin/cat /etc/oratab .*", aStdout="/u01/app/19.0.0.0/grid"),
                    exaMockCommand(".*crsctl check crs")
                ],
                [
                    exaMockCommand("cat /var/opt/oracle/log/.*", aStdout=DB_INFO, aRc=0),
                    exaMockCommand("/bin/cat /etc/oratab .*", aStdout="/u01/app/19.0.0.0/grid"),
                    exaMockCommand(".*crsctl check crs"),
                    exaMockCommand(".*ls -la /var/opt/oracle/creg/grid | head -2 | grep ...x..x..."),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*sid.*", aStdout="ASM+"),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*oracle_home.*", aStdout="/u01/app/19.0.0.0/grid")
                ],
                [
                    exaMockCommand("cat /var/opt/oracle/log/.*", aStdout=DB_INFO, aRc=0),
                    exaMockCommand(".*ls -la /var/opt/oracle/creg/grid | head -2 | grep ...x..x..."),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*sid.*", aStdout="ASM+"),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*oracle_home.*", aStdout="/u01/app/19.0.0.0/grid"),
                    exaMockCommand(re.escape("/u01/app/19.0.0.0/grid/bin/crsctl stat res -w 'TYPE = ora.database.type'"),aStdout=aHaveDBStdout, aRc=aHaveDBretCode),
                    exaMockCommand(re.escape("/u01/app/19.0.0.0/grid/bin/crsctl stat res -attr TYPE,TARGET,STATE -p -n `hostname -s` | grep -C2 ora.database.type"),aStdout=aDBStateStdout),
                    exaMockCommand(re.escape("/u01/app/19.0.0.0/grid/bin/crsctl stat res -attr TYPE,TARGET,STATE -p -n `hostname -s` | grep -A2 -B1 ora.database.type"),aStdout=aDBStateStdout)
                ],
                [
                    exaMockCommand(".*crsctl check crs"),
                    exaMockCommand("/bin/cat /etc/oratab .*", aStdout="/u01/app/19.0.0.0/grid"),
                    exaMockCommand(".*Hugepagesize.*", aStdout="2"),
                    exaMockCommand("sysctl -n.*", aStdout="1"),
                    exaMockCommand("cp /etc/sysctl.conf /etc/sysctl.conf.bkup"),
                    exaMockCommand("sed -i.*"),
                    exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"),aStdout="19.0.0.0"),
                    exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"),aStdout="/u01/app/grid")
                ],
                [
                    exaMockCommand("/u01/app/19.0.0.0/grid/bin/crsctl check crs"),
                    exaMockCommand(".*ls -la /var/opt/oracle/creg/grid | head -2 | grep ...x..x..."),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*sid.*", aStdout="ASM+"),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*oracle_home.*", aStdout="/u01/app/19.0.0.0/grid")
                ],
                [
                    exaMockCommand(".*srvctl config database", aStdout="db1"),
                    exaMockCommand("cat /etc/oratab | grep %s.*", aStdout="oh1"),
                    exaMockCommand(".*srvctl status database.*", aStdout="""Instance db1 is running on node node1""")
                ],
                [
                    exaMockCommand("/bin/cat /etc/oratab .*", aStdout="/u01/app/19.0.0.0/grid"),
                    exaMockCommand(".*crsctl check crs")
                ],
                [
                    exaMockCommand(".*ls -la /var/opt/oracle/creg/grid | head -2 | grep ...x..x..."),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*sid.*", aStdout="ASM+"),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*oracle_home.*", aStdout="/u01/app/19.0.0.0/grid")
                ],
                [
                    exaMockCommand(re.escape("/u01/app/19.0.0.0/grid/bin/crsctl stat res -w 'TYPE = ora.database.type'"),aStdout=aHaveDBStdout, aRc=aHaveDBretCode),
                    exaMockCommand(re.escape("/u01/app/19.0.0.0/grid/bin/crsctl stat res -attr TYPE,TARGET,STATE -p -n `hostname -s` | grep -C2 ora.database.type"),aStdout=aDBStateStdout),
                    exaMockCommand(re.escape("/u01/app/19.0.0.0/grid/bin/crsctl stat res -attr TYPE,TARGET,STATE -p -n `hostname -s` | grep -A2 -B1 ora.database.type"),aStdout=aDBStateStdout)
                ],
                [
                    exaMockCommand("ip addr show | grep 'ib0\|ib1\|inet '")
                ],
                [
                    exaMockCommand(".*ls -la /var/opt/oracle/creg/grid | head -2 | grep ...x..x..."),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*sid.*", aStdout="ASM+"),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*oracle_home.*", aStdout="/u01/app/19.0.0.0/grid"),
                ],
                [
                    exaMockCommand(re.escape("/u01/app/19.0.0.0/grid/bin/crsctl stat res -w 'TYPE = ora.database.type'"),aStdout=aHaveDBStdout, aRc=aHaveDBretCode),
                    exaMockCommand(re.escape("/u01/app/19.0.0.0/grid/bin/crsctl stat res -attr TYPE,TARGET,STATE -p -n `hostname -s` | grep -C2 ora.database.type"),aStdout=aDBStateStdout),
                    exaMockCommand(re.escape("/u01/app/19.0.0.0/grid/bin/crsctl stat res -attr TYPE,TARGET,STATE -p -n `hostname -s` | grep -A2 -B1 ora.database.type"),aStdout=aDBStateStdout)
                ],
                [
                    exaMockCommand(".*ls -la /var/opt/oracle/creg/grid | head -2 | grep ...x..x..."),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*sid.*", aStdout="ASM+"),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*oracle_home.*", aStdout="/u01/app/19.0.0.0/grid")
                ],
                [
                    exaMockCommand(".*srvctl config database", aStdout="db1"),
                    exaMockCommand("cat /etc/oratab | grep %s.*", aStdout="oh1"),
                    exaMockCommand(".*srvctl status database.*", aStdout="""Instance db1 is running on node node1""")
                ],

                ],

            self.mGetRegexDom0(): [
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="DOM0 DOM0 DOM0"),
                    exaMockCommand("xm li .* | grep .* | awk '{ print $3 }'", aStdout="200")
                ],
                [
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="DOM0 DOM0 DOM0"),
                    exaMockCommand("xm li .* | grep .* | awk '{ print $3 }'", aStdout="200000"),
                    exaMockCommand("xm list", aStdout="scaqab10client01vm08.us.oracle.com              1513 65539     8     r-----  25154.2"),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout="scaqab10client01vm08.us.oracle.com scaqab10client02vm08.us.oracle.com"),
                    exaMockCommand("cat /EXAVMIMAGES/GuestImages/.*/vm.cfg", aStdout=_vmcfg)
                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="DOM0 DOM0 DOM0"),
                    exaMockCommand("xm li .* | grep .* | awk '{ print $3 }'", aStdout="200000")
                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="DOM0 DOM0 DOM0"),
                    exaMockCommand("xm info |grep 'free_memory'", aStdout="free_memory:5")
                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="DOM0 DOM0 DOM0"),
                    exaMockCommand("xm info |grep 'free_memory'", aStdout="free_memory:5"),
                    exaMockCommand("xm li .* | grep .* | awk '{ print $3 }'", aStdout="200000"),
                    exaMockCommand("xm li .* -l | grep '(maxmem' | tr -d ')' | awk '{ print $2 }'", aStdout="400")
                ],
                [
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="DOM0 DOM0 DOM0"),
                    exaMockCommand("xm list", aStdout="scaqab10client01vm08.us.oracle.com              1513 65539     8     r-----  25154.2"),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout="scaqab10client01vm08.us.oracle.com scaqab10client02vm08.us.oracle.com"),
                    exaMockCommand("cat /EXAVMIMAGES/GuestImages/.*/vm.cfg", aStdout=_vmcfg)
                ],
                [
                    exaMockCommand("xm li .* | grep .* | awk '{ print $3 }'", aStdout="200"),
                    exaMockCommand("xm li .* -l | grep '(maxmem' | tr -d ')' | awk '{ print $2 }'", aStdout="4000"),
                    exaMockCommand("xm li scaqab10client01vm08.us.oracle.com | grep scaqab10client01vm08.us.oracle.com | awk '{ print $3 }'", aStdout="32768"),

                ],
                [
                    exaMockCommand("cp /EXAVMIMAGES/GuestImages/.*/vm.cfg /EXAVMIMAGES/GuestImages/.*/vm.cfg.*"),
                    exaMockCommand("/bin/test -e .*", aRc=0,  aPersist=True),
                    exaMockCommand("/bin/find /EXAVMIMAGES/GuestImages/.*/ -name 'vm.cfg.prev*' | /bin/xargs /bin/ls -t",aStdout=_vm_cfg_prev_list),
                    exaMockCommand("/bin/test -e /bin/rm", aRc=0,  aPersist=True),
                    exaMockCommand("/bin/rm -f /EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev11"),
                    exaMockCommand("/bin/rm -f /EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev12"),
                    exaMockCommand("/bin/scp .*", aPersist=True)
                ],
                [
                    exaMockCommand("/bin/cat /etc/oratab .*", aStdout="/u01/app/19.0.0.0/grid"),
                    exaMockCommand(".*crsctl check crs"),
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="DOM0 DOM0 DOM0")

                ],

                ],

            self.mGetRegexLocal(): [
                [
                    exaMockCommand("rm.*", aRc=0,  aPersist=True),
                    exaMockCommand("ping .*", aRc=0,  aPersist=True),
                ],
                [
                    exaMockCommand("/bin/echo EXIT | /usr/bin/nc.*", aRc=0)
                ]
            ]


        }

        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        #_options.jsonconf['gb_memory'] = '4'
        _options.jsonconf['vms'] = [{"hostname": "scaqab10client01vm08.us.oracle.com", "gb_memory": "40"}, {"hostname": "scaqab10client02vm08.us.oracle.com", "gb_memory": "40"}]
        cluctrl = self.mGetClubox()
        _rc = cluctrl.mManageVMMemory("memset", "scaqab10client01vm08.us.oracle.com", aOptions=_options)
        #This should fail due to insufficient memory on dom0 !
        self.assertNotEqual(_rc, 0)

    @patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', return_value=0)
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog')
    @patch('exabox.ovm.cludbaas.ebCluDbaas.mWaitForJobComplete', return_value=0)
    @patch('exabox.ovm.cludbaas.ebCluDbaas.mBaseCopyFileToDomU', return_value=0)
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckDBIsUp', return_value=True)
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mStartVMAfterReshape')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mShutdownVMForReshape', return_value=(True,True))
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetSysCtlConfigValue', return_value=("", "7777"))
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mSetSysCtlConfigValue', return_value=True)
    def test_mem_mgr(self,mock_exitstatus,mock_executelog,mock_mwaitforjobtocomplete, mock_mcopyfiletodomu, mock_mcheckdbisup, mock_mstartvmafterreshape, mock_mShutdownVMForReshape, mock_mGetSysCtlConfigValue,  mock_mSetSysCtlConfigValue):
        _vmcfg = self.mGetResourcesTextFile("cmd_vmcfg.txt")

        _cmds = {
            self.mGetRegexVm(): [
		        [
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i /var/opt/oracle/log/grid/get_exatest.json.*", aRc=0),
                    exaMockCommand("/bin/cat /etc/oratab .*", aStdout="/u01/app/19.0.0.0/grid"),
                    exaMockCommand(".*crsctl check crs")
		        ],
                [
                    exaMockCommand("cat /var/opt/oracle/log/.*", aStdout=DB_INFO, aRc=0),
                    exaMockCommand("/bin/cat /etc/oratab .*", aStdout="/u01/app/19.0.0.0/grid"),
                    exaMockCommand(".*crsctl check crs"),
                    exaMockCommand(".*ls -la /var/opt/oracle/creg/grid | head -2 | grep ...x..x..."),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*sid.*", aStdout="ASM+"),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*oracle_home.*", aStdout="/u01/app/19.0.0.0/grid")
                ],
		        [
                    exaMockCommand("cat /var/opt/oracle/log/.*", aStdout=DB_INFO, aRc=0),
                    exaMockCommand(".*ls -la /var/opt/oracle/creg/grid | head -2 | grep ...x..x..."),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*sid.*", aStdout="ASM+"),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*oracle_home.*", aStdout="/u01/app/19.0.0.0/grid"),
	                exaMockCommand(re.escape("/u01/app/19.0.0.0/grid/bin/crsctl stat res -w 'TYPE = ora.database.type'"),aStdout=aHaveDBStdout, aRc=aHaveDBretCode),
                    exaMockCommand(re.escape("/u01/app/19.0.0.0/grid/bin/crsctl stat res -attr TYPE,TARGET,STATE -p -n `hostname -s` | grep -C2 ora.database.type"),aStdout=aDBStateStdout),
                    exaMockCommand(re.escape("/u01/app/19.0.0.0/grid/bin/crsctl stat res -attr TYPE,TARGET,STATE -p -n `hostname -s` | grep -A2 -B1 ora.database.type"),aStdout=aDBStateStdout)
		        ],
                [
                    exaMockCommand("/bin/cat /etc/oratab .*", aStdout="/u01/app/19.0.0.0/grid"),
                    exaMockCommand(".*crsctl check crs"),
                    exaMockCommand("sysctl -n.*", aStdout="1"),
                    exaMockCommand("cp /etc/sysctl.conf /etc/sysctl.conf.bkup"),
                    exaMockCommand("sed -i.*"),
                    exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"),aStdout="19.0.0.0"),
                    exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"),aStdout="/u01/app/grid")
                    
                ],
		[
                    exaMockCommand(".*Hugepagesize.*", aStdout="2"),
                    exaMockCommand("/var/opt/oracle/ocde/rops atp_enabled", aRc=0),
                    exaMockCommand("sysctl -n.*", aStdout="1"),
                    exaMockCommand("cp /etc/sysctl.conf /etc/sysctl.conf.bkup"),
                    exaMockCommand("sed -i.*"),
                    exaMockCommand("/u01/app/19.0.0.0/grid/bin/crsctl check crs"),  
		],
		[
                    exaMockCommand(".*Hugepagesize.*", aStdout="2"),
                    exaMockCommand("/var/opt/oracle/ocde/rops atp_enabled", aRc=0),
                    exaMockCommand("sysctl -n.*", aStdout="1"),
                    exaMockCommand("cp /etc/sysctl.conf /etc/sysctl.conf.bkup"),
                    exaMockCommand("sed -i.*")    
		],
                [
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*oracle_home.*", aStdout="/u01/app/19.0.0.0/grid"),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*sid.*", aStdout="ASM+"),
                    exaMockCommand("/bin/uname -r", aRc=0, aStdout="4.14.35-2047.517.3.1.el7uek.x86_64", aPersist=True),
                    exaMockCommand("/bin/test -e.*", aRc=0,  aPersist=True),
                    exaMockCommand("/bin/rm -rf /var/initramfs.*", aRc=0,  aPersist=True),
                    exaMockCommand("/usr/bin/cp .*", aRc=0,  aPersist=True),
                    exaMockCommand(".*dracut --omit-drivers 'oracleacfs oracleadvm oracleoks' -f"),
                    exaMockCommand(".*ls -la /var/opt/oracle/creg/grid | head -2 | grep ...x..x..."),
                    exaMockCommand("/bin/grep Hugepagesize /proc/meminfo | /usr/bin/awk '{print$2/1024}'",aStdout="2",aRc=0,  aPersist=True),
                    
                ],
                [
                    exaMockCommand(".*srvctl config database", aStdout="db1"),
                    exaMockCommand("cat /etc/oratab | grep %s.*", aStdout="oh1"),
                    exaMockCommand(".*srvctl status database.*", aStdout="""Instance db1 is running on node node1"""),
                    exaMockCommand("/bin/uname -r", aRc=0, aStdout="4.14.35-2047.517.3.1.el7uek.x86_64", aPersist=True),
                    exaMockCommand("/bin/test -e /boot/initramfs-4.14.35-2047.517.3.1.el7uek.x86_64.img", aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /var/initramfs-4.14.35-2047.517.3.1.el7uek.x86_64.img", aRc=0, aPersist=True),
                    exaMockCommand("/bin/rm -rf /var/initramfs-4.14.35-2047.517.3.1.el7uek.x86_64.img", aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/cp /boot/initramfs-4.14.35-2047.517.3.1.el7uek.x86_64.img  /var/initramfs-4.14.35-2047.517.3.1.el7uek.x86_64.img", aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /sbin/dracut", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/dracut --omit-drivers 'oracleacfs oracleadvm oracleoks' -f", aRc=0, aPersist=True),
		        ],
                [
                    exaMockCommand("/bin/cat /etc/oratab .*", aStdout="/u01/app/19.0.0.0/grid"),
                    exaMockCommand(".*ls -la /var/opt/oracle/creg/grid | head -2 | grep ...x..x..."),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*sid.*", aStdout="ASM+"),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*oracle_home.*", aStdout="/u01/app/19.0.0.0/grid"),
                    exaMockCommand(".*crsctl check crs")
		        ],
		        [
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*sid.*", aStdout="ASM+"),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*oracle_home.*", aStdout="/u01/app/19.0.0.0/grid"),
                    exaMockCommand(re.escape("/u01/app/19.0.0.0/grid/bin/crsctl stat res -w 'TYPE = ora.database.type'"),aStdout=aHaveDBStdout, aRc=aHaveDBretCode),
                    exaMockCommand(re.escape("/u01/app/19.0.0.0/grid/bin/crsctl stat res -attr TYPE,TARGET,STATE -p -n `hostname -s` | grep -C2 ora.database.type"),aStdout=aDBStateStdout),
                    exaMockCommand(re.escape("/u01/app/19.0.0.0/grid/bin/crsctl stat res -attr TYPE,TARGET,STATE -p -n `hostname -s` | grep -A2 -B1 ora.database.type"),aStdout=aDBStateStdout)
                ],
		        [
		            exaMockCommand("ip addr show | grep 'ib0\|ib1\|inet '")
		        ],
                [
                    exaMockCommand(".*ls -la /var/opt/oracle/creg/grid | head -2 | grep ...x..x..."),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*sid.*", aStdout="ASM+"),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*oracle_home.*", aStdout="/u01/app/19.0.0.0/grid"),
		        ],
		        [
                    exaMockCommand(re.escape("/u01/app/19.0.0.0/grid/bin/crsctl stat res -w 'TYPE = ora.database.type'"),aStdout=aHaveDBStdout, aRc=aHaveDBretCode),
                    exaMockCommand(re.escape("/u01/app/19.0.0.0/grid/bin/crsctl stat res -attr TYPE,TARGET,STATE -p -n `hostname -s` | grep -C2 ora.database.type"),aStdout=aDBStateStdout),
                    exaMockCommand(re.escape("/u01/app/19.0.0.0/grid/bin/crsctl stat res -attr TYPE,TARGET,STATE -p -n `hostname -s` | grep -A2 -B1 ora.database.type"),aStdout=aDBStateStdout)
                ],
                [
                    exaMockCommand(".*ls -la /var/opt/oracle/creg/grid | head -2 | grep ...x..x..."),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*sid.*", aStdout="ASM+"),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*oracle_home.*", aStdout="/u01/app/19.0.0.0/grid")
                ],
                [
                    exaMockCommand(".*srvctl config database", aStdout="db1"),
                    exaMockCommand("cat /etc/oratab | grep %s.*", aStdout="oh1"),
                    exaMockCommand(".*srvctl status database.*", aStdout="""Instance db1 is running on node node1""")
                ],

		],

            self.mGetRegexDom0(): [
                [   
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="DOM0 DOM0 DOM0"),
                    exaMockCommand("xm li .* | grep .* | awk '{ print $3 }'", aStdout="200")
                ],
                [
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="DOM0 DOM0 DOM0"),
                    exaMockCommand("xm li .* | grep .* | awk '{ print $3 }'", aStdout="200000"),
                    exaMockCommand("xm list", aStdout="scaqab10client01vm08.us.oracle.com              1513 65539     8     r-----  25154.2"),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout="scaqab10client01vm08.us.oracle.com scaqab10client02vm08.us.oracle.com"),
                    exaMockCommand("cat /EXAVMIMAGES/GuestImages/.*/vm.cfg", aStdout=_vmcfg)
                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="DOM0 DOM0 DOM0"),
                    exaMockCommand("xm li .* | grep .* | awk '{ print $3 }'", aStdout="200000")
                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="DOM0 DOM0 DOM0"),
                    exaMockCommand("xm info |grep 'free_memory'", aStdout="free_memory:50000")
                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="DOM0 DOM0 DOM0"),
                    exaMockCommand("xm info |grep 'free_memory'", aStdout="free_memory:50000"),
                    exaMockCommand("xm li .* | grep .* | awk '{ print $3 }'", aStdout="200000"),
                    exaMockCommand("xm li .* -l | grep '(maxmem' | tr -d ')' | awk '{ print $2 }'", aStdout="4000")
                ],
                [
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="DOM0 DOM0 DOM0"),
                    exaMockCommand("xm list", aStdout="scaqab10client01vm08.us.oracle.com              1513 65539     8     r-----  25154.2"),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout="scaqab10client01vm08.us.oracle.com scaqab10client02vm08.us.oracle.com"),
                    exaMockCommand("cat /EXAVMIMAGES/GuestImages/.*/vm.cfg", aStdout=_vmcfg)
                ],
                [
                    exaMockCommand("xm li .* | grep .* | awk '{ print $3 }'", aStdout="200"),
                    exaMockCommand("xm li .* -l | grep '(maxmem' | tr -d ')' | awk '{ print $2 }'", aStdout="4000"),
                    exaMockCommand("xm li scaqab10client01vm08.us.oracle.com | grep scaqab10client01vm08.us.oracle.com | awk '{ print $3 }'", aStdout="32768"),

                ],
		[
	            exaMockCommand("cp /EXAVMIMAGES/GuestImages/.*/vm.cfg /EXAVMIMAGES/GuestImages/.*/vm.cfg.*"),
                exaMockCommand("/bin/test -e .*", aRc=0,  aPersist=True),
                exaMockCommand("/bin/find /EXAVMIMAGES/GuestImages/.*/ -name 'vm.cfg.prev*' | /bin/xargs /bin/ls -t",aStdout=_vm_cfg_prev_list),
                exaMockCommand("/bin/test -e /bin/rm", aRc=0,  aPersist=True),
                exaMockCommand("/bin/rm -f /EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev11"),
                exaMockCommand("/bin/rm -f /EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev12"),
	            exaMockCommand("/bin/scp .*", aPersist=True)
		],
		[
                    exaMockCommand("/bin/cat /etc/oratab .*", aStdout="/u01/app/19.0.0.0/grid"),
                    exaMockCommand(".*crsctl check crs"),
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="DOM0 DOM0 DOM0")

		],
		[
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="DOM0 DOM0 DOM0"),
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                    exaMockCommand("xm list", aStdout=_xmList1),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout="scaqab10client01vm08.us.oracle.com"),
                    exaMockCommand("xm list", aStdout=_xmList1),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout="scaqab10client02vm08.us.oracle.com"),
                    exaMockCommand("/bin/test -e /etc/xen/auto", aRc=0, aPersist=True),
                    exaMockCommand("/bin/unlink /etc/xen/auto", aRc=0, aPersist=True),
		            exaMockCommand("xm shutdown"),
                    exaMockCommand("xm list", aStdout=_xmList2),
                    exaMockCommand("xm list", aStdout=_xmList2),
		],
		[
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="DOM0 DOM0 DOM0"),
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                    exaMockCommand("xm list", aStdout=_xmList1),
                    exaMockCommand("xm list", aStdout=_xmList2),

		],
		[
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                    exaMockCommand("xm list", aStdout=_xmList1),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout="scaqab10client01vm08.us.oracle.com"),
                    exaMockCommand("xm list", aStdout=_xmList2),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout="scaqab10client02vm08.us.oracle.com"),
                    exaMockCommand("xm create /EXAVMIMAGES/GuestImages.*", aRc=0, aPersist=True),
                    exaMockCommand("xm create /EXAVMIMAGES/GuestImages.*", aRc=0, aPersist=True),
                    exaMockCommand("xm list", aStdout=_xmList1),
                    exaMockCommand("xm list", aStdout=_xmList2),
                    exaMockCommand("/bin/test -e /etc/xen/auto", aRc=0, aPersist=True),
                    exaMockCommand("/bin/unlink /etc/xen/auto", aRc=0, aPersist=True),

		],
		[
                    exaMockCommand("xm list", aStdout=_xmList1),
                    exaMockCommand("xm list", aStdout=_xmList2),
                    exaMockCommand("xm create /EXAVMIMAGES/GuestImages.*", aRc=0, aPersist=True),
                    exaMockCommand("xm create /EXAVMIMAGES/GuestImages.*", aRc=0, aPersist=True),
		],
		[
                    exaMockCommand("xm li scaqab10client01vm08.us.oracle.com | grep scaqab10client01vm08.us.oracle.com | awk '{ print $3 }'", aStdout="32768"),
		]
                ],
            self.mGetRegexCell():                                                                                                                                                         
                [                                                                                                                                                               
                    [                                                                                                                                                          
                          exaMockCommand("cellcli -e", aRc=0,  aPersist=True)                                                                                            
                    ],                                                                                                                                              
                    [   exaMockCommand("cellcli -e", aRc=0,  aPersist=True)                                                                                       
                    ],                                                                                                                                          
                    [                                                                                                                                            
                         exaMockCommand("cellcli -e", aRc=0,  aPersist=True)                                                                                             
                    ]                                                                                                                                             
                ],                                                                                                                                              
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("rm.*", aRc=0,  aPersist=True),
                    exaMockCommand("ping .*", aRc=0,  aPersist=True),
		],
		[
                    exaMockCommand("/bin/echo EXIT | /usr/bin/nc.*", aRc=0)
                ]
            ]


        }

        self.mPrepareMockCommands(_cmds)
        _options = self.mGetPayload()
        #_options.jsonconf['gb_memory'] = '4'
        _options.jsonconf['vms'] = [{"hostname": "scaqab10client01vm08.us.oracle.com", "gb_memory": "40"}, {"hostname": "scaqab10client02vm08.us.oracle.com", "gb_memory": "40"}]
        cluctrl = self.mGetClubox()
        _options.vmid = 'scaqab10client01vm08.us.oracle.com'
        _options.vmcmd = 'memset'
        _options.debug = '1'
        cluctrl.mSetOptions(_options)
        _rc = cluctrl.mHandlerVmCmd()
        self.assertEqual(_rc, 0)

    def mExecuteCmd_mock(self):
        response_mock = Mock()
        response_mock.return_value = (0,None,None)
        return response_mock

if __name__ == '__main__':
    unittest.main()

