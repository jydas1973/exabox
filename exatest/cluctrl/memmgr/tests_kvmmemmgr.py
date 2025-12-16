import unittest
import io
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from unittest.mock import patch, MagicMock, PropertyMock, mock_open
import os
import re

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

cmdOutput1="""xen
00000000-0000-0000-0000-000000000000
"""

aHaveDBretCode = 0
cmdOutput2 = """CRS-4638: Oracle High Availability Services is online
         CRS-4537: Cluster Ready Services is online
         CRS-4529: Cluster Synchronization Services is online
         CRS-4533: Event Manager is online"""
DB_INFO = """{"id": "123","status":"Pass","min_reqd_hugepages_memory":"4 GB","is_new_mem_sz_allowed":1,"logfile":"/tmp/file.log","Log":"get for ALL clusterDBs succeeded on Node scaqan03dv0101.us.oracle.com","get":{"current_total_sga":"12 GB","min_req_mem":"30GB","consolidated_info":"Demo","error":[],"nodes":[{"node_name":"scaqan03dv0101","vm_mem_info":{"info":"scaqan03dv0101 Used Memory: 15 GB.Available Memory: 13 GB","total_memory":"28 GB","free_memory":"5 GB","buffer":"0 GB","cache":"4 GB","free_hugepages_memory":"8 GB"}},{"node_name":"scaqan03dv0201","vm_mem_info":{"info":"scaqan03dv0201 UsedMemory: 14 GB. Available Memory: 14 GB","buffer":"0 GB","free_hugepages_memory":"8 GB","total_memory":"28 GB","free_memory":"6 GB","cache":"3 GB"}}],"current_total_pga":"0 GB"}}"""


class TestKvmMemMgr(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateDatabase=True)
        super().setUpClass()

    def setUp(self):
        self.mGetClubox()._exaBoxCluCtrl__ociexacc = False
        self.mGetClubox()._exaBoxCluCtrl__kvm_enabled = True
        get_gcontext().mSetConfigOption('kvm_var_size',None)
        self.mGetClubox().mRegisterVgComponents()

    @patch('exabox.ovm.clucontrol.node_cmd_abs_path_check')
    @patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', return_value=0)
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog')
    @patch('exabox.ovm.cludbaas.ebCluDbaas.mWaitForJobComplete', return_value=0)
    @patch('exabox.ovm.cludbaas.ebCluDbaas.mBaseCopyFileToDomU', return_value=0)
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckDBIsUp', return_value=True)
    def test_kmvmem_insufficient_domo_mem(self,mock_pathcheck1,mock_exitstatus,mock_executelog, mock_mwaitforjobtocomplete, mock_mcopyfiletodomu, mock_mcheckdbisup):

        _vmcfg = self.mGetResourcesTextFile("cmd_vmcfg.txt")

        _cmds = {
            self.mGetRegexVm(): [
		[
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i /var/opt/oracle/log/grid/get_exatest.json.*", aRc=0),
                    exaMockCommand(".*bin/mkdir -p.*"),
                    exaMockCommand("/usr/bin/chown -R oracle:oinstall.*"),
                    exaMockCommand("/bin/scp /tmp/get_exatest.json /var/opt/oracle/log/grid/get_exatest.json", aRc=0),
                    exaMockCommand("/bin/cat /etc/oratab .*", aStdout="/u01/app/19.0.0.0/grid"),
                    exaMockCommand(".*crsctl check crs")
		],
                [
                    exaMockCommand("cat /var/opt/oracle/log/.*", aStdout=DB_INFO, aRc=0),
                    exaMockCommand("/bin/cat /etc/oratab .*", aStdout="/u01/app/19.0.0.0/grid"),
                    exaMockCommand(".*crsctl check crs"),
                    exaMockCommand(".*ls -la /var/opt/oracle/creg/grid | head -2 | grep ...x..x..."),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*sid.*", aStdout="ASM+"),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i /var/opt/oracle/log/grid/get_exatest.json.*", aRc=0),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*oracle_home.*", aStdout="/u01/app/19.0.0.0/grid")
                ],
                [
                    exaMockCommand("cat /var/opt/oracle/log/.*", aStdout=DB_INFO, aRc=0),
                    exaMockCommand(".*ls -la /var/opt/oracle/creg/grid | head -2 | grep ...x..x..."),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*sid.*", aStdout="ASM+"),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*oracle_home.*", aStdout="/u01/app/19.0.0.0/grid"),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i /var/opt/oracle/log/grid/get_exatest.json.*", aRc=0),
                    exaMockCommand("cat /var/opt/oracle/log/get_exatest_outfile.out", aStdout=DB_INFO, aRc=0),
                    exaMockCommand(re.escape("/u01/app/19.0.0.0/grid/bin/crsctl stat res -w 'TYPE = ora.database.type'"),aStdout=aHaveDBStdout, aRc=aHaveDBretCode),
                    exaMockCommand(re.escape("/u01/app/19.0.0.0/grid/bin/crsctl stat res -attr TYPE,TARGET,STATE -p -n `hostname -s` | grep -C2 ora.database.type"),aStdout=aDBStateStdout),
                    exaMockCommand(re.escape("/u01/app/19.0.0.0/grid/bin/crsctl stat res -attr TYPE,TARGET,STATE -p -n `hostname -s` | grep -A2 -B1 ora.database.type"),aStdout=aDBStateStdout)
                ],
                [
                    exaMockCommand(".*crsctl check crs"),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*sid.*", aStdout="ASM+"),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*oracle_home.*", aStdout="/u01/app/19.0.0.0/grid"),
                    exaMockCommand("/bin/cat /etc/oratab .*", aStdout="/u01/app/19.0.0.0/grid"),
                    exaMockCommand("/usr/bin/mkdir -p.*"),
                    exaMockCommand("/usr/bin/chown -R oracle:oinstall.*"),
                    exaMockCommand("/bin/scp .*"),
                    exaMockCommand(".*Hugepagesize.*", aStdout="2"),
                    exaMockCommand("sysctl -n.*", aStdout="1000"),
                    exaMockCommand("cp /etc/sysctl.conf /etc/sysctl.conf.bkup"),
                    exaMockCommand("sed -i.*"),
                    exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"),aStdout="19.0.0.0"),
                    exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"),aStdout="/u01/app/grid")
                    
                ],
                [
                    exaMockCommand("/u01/app/19.0.0.0/grid/bin/crsctl check crs"),
                ]

		],

            self.mGetRegexDom0(): [
                [   
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="Node type: KVMHOST"),
                ],
                [
                    exaMockCommand("/usr/sbin/vm_maker --list --memory --domain.*", aStdout="scaqab10client01vm08.us.oracle.com               1281            1281")
                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="Node type: KVMHOST"),
                ],
		[
		    exaMockCommand("vm_maker --list --memory | grep .*", aStdout="   all 'autostart enabled domains' restart)           : 271 M")
		],
                [
                    exaMockCommand("/usr/sbin/vm_maker --list --memory --domain.*", aStdout="scaqab10client01vm08.us.oracle.com               1281            1281"),
		    exaMockCommand("virsh dominfo scaqab10client01vm08.us.oracle.com | grep 'Max memory' | awk '{ print $3/1024 }'", aStdout="6000")
                ],
		
                ],

            self.mGetRegexLocal(): [
                [
                    exaMockCommand("rm.*", aRc=0,  aPersist=True),
                    exaMockCommand("ping .*", aRc=0,  aPersist=True),
                    exaMockCommand("/bin/mkdir -p oeda/requests/exatest/log/dbaasapilog", aRc=0),
		],
		[
                    exaMockCommand("/bin/echo EXIT | /usr/bin/nc.*", aRc=0)
                ]
            ]


        }

        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        _options.jsonconf['vms'] = [{"hostname": "scaqab10client01vm08.us.oracle.com", "gb_memory": "40"}]
        cluctrl = self.mGetClubox()
        _rc = cluctrl.mManageVMMemory("memset", "scaqab10client01vm08.us.oracle.com", aOptions=_options)
        #This should fail due to insufficient memory on dom0 !!
        self.assertNotEqual(_rc, 0)


    @patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', return_value=0)
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog')
    @patch('exabox.ovm.cludbaas.ebCluDbaas.mWaitForJobComplete', return_value=0)
    @patch('exabox.ovm.cludbaas.ebCluDbaas.mBaseCopyFileToDomU', return_value=0)
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckDBIsUp', return_value=True)
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mStartVMAfterReshape')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mShutdownVMForReshape', return_value=(True,True))
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetSysCtlConfigValue', return_value=("/etc/sysctl.conf", "77777"))
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mSetSysCtlConfigValue', return_value=True)
    def test_kmvmemmgr(self,mock_exitstatus,mock_executelog, mock_mwaitforjobtocomplete, mock_mcopyfiletodomu, mock_mcheckdbisup, mock_mstartvmafterreshape, mock_mShutdownVMForReshape, mock_mGetSysCtl, mock_mSetSysCtl):
        _vmcfg = self.mGetResourcesTextFile("cmd_vmcfg.txt")

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i /var/opt/oracle/log/grid/get_exatest.json.*", aRc=0),
                    exaMockCommand("/usr/bin/mkdir -p.*"),
                    exaMockCommand("/usr/bin/chown -R oracle:oinstall.*"),
                    exaMockCommand("/bin/scp .*"),
                    exaMockCommand("/bin/cat /etc/oratab .*", aStdout="/u01/app/19.0.0.0/grid"),
                    exaMockCommand(".*crsctl check crs")
                ],
                [
                    exaMockCommand("cat /var/opt/oracle/log/.*", aStdout=DB_INFO, aRc=0),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i /var/opt/oracle/log/grid/get_exatest.json.*", aRc=0),
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
                    exaMockCommand("cat /var/opt/oracle/log/get_exatest_outfile.out", aStdout=DB_INFO, aRc=0),
                    exaMockCommand(re.escape("/u01/app/19.0.0.0/grid/bin/crsctl stat res -w 'TYPE = ora.database.type'"),aStdout=aHaveDBStdout, aRc=aHaveDBretCode),
                    exaMockCommand(re.escape("/u01/app/19.0.0.0/grid/bin/crsctl stat res -attr TYPE,TARGET,STATE -p -n `hostname -s` | grep -C2 ora.database.type"),aStdout=aDBStateStdout),
                    exaMockCommand(re.escape("/u01/app/19.0.0.0/grid/bin/crsctl stat res -attr TYPE,TARGET,STATE -p -n `hostname -s` | grep -A2 -B1 ora.database.type"),aStdout=aDBStateStdout)
                ],
                [
                    exaMockCommand(".*crsctl check crs"),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*sid.*", aStdout="ASM+"),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*oracle_home.*", aStdout="/u01/app/19.0.0.0/grid"),
                    exaMockCommand("/bin/cat /etc/oratab .*", aStdout="/u01/app/19.0.0.0/grid"),
                    exaMockCommand("/usr/bin/mkdir -p.*"),
                    exaMockCommand("/usr/bin/chown -R oracle:oinstall.*"),
                    exaMockCommand("/bin/scp .*"),
                    exaMockCommand(".*Hugepagesize.*", aStdout="2"),
                    exaMockCommand("sysctl -n.*", aStdout="1000"),
                    exaMockCommand("cp /etc/sysctl.conf /etc/sysctl.conf.bkup"),
                    exaMockCommand("sed -i.*"),
                    exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"),aStdout="19.0.0.0"),
                    exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"),aStdout="/u01/app/grid")
                    
                    
                ],
                [
                    exaMockCommand("/u01/app/19.0.0.0/grid/bin/crsctl check crs"),
                    exaMockCommand(".*Hugepagesize.*", aStdout="2"),
                    exaMockCommand("sysctl -n.*", aStdout="1000"),
                    exaMockCommand("cp /etc/sysctl.conf /etc/sysctl.conf.bkup"),
                    exaMockCommand("sed -i.*"),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i /var/opt/oracle/log/grid/get_status_exatest.json", aRc=0),
                    exaMockCommand("/var/opt/oracle/ocde/rops atp_enabled", aRc=0),
                    exaMockCommand(".*ls -la /var/opt/oracle/creg/grid | head -2 | grep ...x..x..."),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*sid.*", aStdout="ASM+"),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*oracle_home.*", aStdout="/u01/app/19.0.0.0/grid")
                ],
                [
                    exaMockCommand(".*Hugepagesize.*", aStdout="2"),
                    exaMockCommand("sysctl -n.*", aStdout="1000"),
                    exaMockCommand("cp /etc/sysctl.conf /etc/sysctl.conf.bkup"),
                    exaMockCommand("sed -i.*"),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i /var/opt/oracle/log/grid/get_status_exatest.json", aRc=0),
                    exaMockCommand("/var/opt/oracle/ocde/rops atp_enabled", aRc=0),
                    exaMockCommand(".*ls -la /var/opt/oracle/creg/grid | head -2 | grep ...x..x..."),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*sid.*", aStdout="ASM+"),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*oracle_home.*", aStdout="/u01/app/19.0.0.0/grid")
                ],
                [
                    exaMockCommand("cat /var/opt/oracle/log/get_status_exatest_outfile.out", aStdout=DB_INFO, aRc=0),
                    exaMockCommand(".*srvctl config database", aStdout="db1"),
                    exaMockCommand(".*Hugepagesize.*", aStdout="2"),
                    exaMockCommand("cat /etc/oratab | grep %s.*", aStdout="oh1"),
                    exaMockCommand(".*ls -la /var/opt/oracle/creg/grid | head -2 | grep ...x..x..."),
                    exaMockCommand("sysctl -n.*", aStdout="1000"),
                    exaMockCommand("cp /etc/sysctl.conf /etc/sysctl.conf.bkup"),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*sid.*", aStdout="ASM+"),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*oracle_home.*", aStdout="/u01/app/19.0.0.0/grid"),
                    exaMockCommand(".*srvctl status database.*", aStdout="""Instance db1 is running on node node1"""),
                    exaMockCommand("/bin/uname -r", aRc=0, aStdout="4.14.35-2047.517.3.1.el7uek.x86_64", aPersist=True),
                    exaMockCommand("/bin/test -e.*", aRc=0,  aPersist=True),
                    exaMockCommand("/bin/rm -rf /var/initramfs.*", aRc=0,  aPersist=True),
                    exaMockCommand("/usr/bin/cp .*", aRc=0,  aPersist=True),
                    exaMockCommand(".*dracut --omit-drivers 'oracleacfs oracleadvm oracleoks' -f"),
                    exaMockCommand(".*srvctl config database", aStdout="db1"),
                    exaMockCommand("cat /etc/oratab | grep %s.*", aStdout="oh1"),
                    exaMockCommand(re.escape("/u01/app/19.0.0.0/grid/bin/crsctl stat res -w 'TYPE = ora.database.type'"),aStdout=aHaveDBStdout, aRc=aHaveDBretCode),
                    exaMockCommand(re.escape("/u01/app/19.0.0.0/grid/bin/crsctl stat res -attr TYPE,TARGET,STATE -p -n `hostname -s` | grep -C2 ora.database.type"),aStdout=aDBStateStdout),
                    exaMockCommand(re.escape("/u01/app/19.0.0.0/grid/bin/crsctl stat res -attr TYPE,TARGET,STATE -p -n `hostname -s` | grep -A2 -B1 ora.database.type"),aStdout=aDBStateStdout)
                ],
                [

                    exaMockCommand(".*srvctl status database.*", aStdout="""Instance db1 is running on node node1"""),
                    exaMockCommand(".*srvctl config database", aStdout="db1"),
                    exaMockCommand("cat /etc/oratab | grep %s.*", aStdout="oh1"),
                    exaMockCommand(".*Hugepagesize.*", aStdout="2"),
                    exaMockCommand("sysctl -n.*", aStdout="1000"),
                    exaMockCommand("cp /etc/sysctl.conf /etc/sysctl.conf.bkup"),
                    exaMockCommand("sed -i.*"),
                    exaMockCommand("/usr/bin/mkdir -p.*"),
                    exaMockCommand("/usr/bin/chown -R oracle:oinstall.*"),
                    exaMockCommand("/bin/scp .*"),
                    exaMockCommand("/bin/cat /etc/oratab .*", aStdout="/u01/app/19.0.0.0/grid"),
                    exaMockCommand(".*crsctl check crs"),
                    exaMockCommand("/bin/uname -r", aRc=0, aStdout="4.14.35-2047.517.3.1.el7uek.x86_64", aPersist=True),
                    exaMockCommand("/bin/test -e /boot/initramfs-4.14.35-2047.517.3.1.el7uek.x86_64.img", aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /var/initramfs-4.14.35-2047.517.3.1.el7uek.x86_64.img", aRc=0, aPersist=True),
                    exaMockCommand("/bin/rm -rf /var/initramfs-4.14.35-2047.517.3.1.el7uek.x86_64.img", aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/cp /boot/initramfs-4.14.35-2047.517.3.1.el7uek.x86_64.img  /var/initramfs-4.14.35-2047.517.3.1.el7uek.x86_64.img", aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /sbin/dracut", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/dracut --omit-drivers 'oracleacfs oracleadvm oracleoks' -f", aRc=0, aPersist=True),
                    
                ],
                [
                    exaMockCommand("cat /etc/oratab | grep %s.*", aStdout="oh1"),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i /var/opt/oracle/log/grid/get_status_exatest.json", aRc=0),
                    exaMockCommand(".*ls -la /var/opt/oracle/creg/grid | head -2 | grep ...x..x..."),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*sid.*", aStdout="ASM+"),
                    exaMockCommand(".*crsctl check crs"),
                    exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*oracle_home.*", aStdout="/u01/app/19.0.0.0/grid")
                ],

                ],


            self.mGetRegexDom0(): [
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="Node type: KVMHOST"),
                ],
                [
                    exaMockCommand("/usr/sbin/vm_maker --list --memory --domain.*", aStdout="scaqab10client01vm08.us.oracle.com               1281            1281")
                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="Node type: KVMHOST"),
                ],
                [
                    exaMockCommand("vm_maker --list --memory | grep .*", aStdout="   all 'autostart enabled domains' restart)           : 200000 M")
                ],
                [
                    exaMockCommand("/usr/sbin/vm_maker --list --memory --domain.*", aStdout="scaqab10client01vm08.us.oracle.com               1281            1281"),
                    exaMockCommand("virsh dominfo scaqab10client01vm08.us.oracle.com | grep 'Max memory' | awk '{ print $3/1024 }'", aStdout="6000"),
                    exaMockCommand("/opt/exadata_ovm/vm_maker --set --memory.* --domain scaqab10client01vm08.us.oracle.com", aStdout=""),
                    exaMockCommand("virsh dominfo scaqab10client01vm08.us.oracle.com | grep 'Max memory' | awk '{ print $3/1024 }'", aStdout="40960"),
                    exaMockCommand("/usr/sbin/vm_maker --list --memory --domain.*", aStdout="scaqab10client01vm08.us.oracle.com               1281            1281"),

                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="Node type: KVMHOST"),
                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="Node type: KVMHOST"),
                    exaMockCommand("/usr/sbin/vm_maker --list-domains | /bin/grep 'running'.*", aStdout="scaqab10client01vm08.us.oracle.com(16)       : running"),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout="scaqab10client01vm08.us.oracle.com"),
                    exaMockCommand("/usr/sbin/vm_maker --list-domains | /bin/grep 'running'.*", aStdout="scaqab10client01vm08.us.oracle.com(16)       : running"),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout="scaqab10client01vm08.us.oracle.com"),
                    exaMockCommand("/opt/exadata_ovm/vm_maker --autostart.*", aRc=0),
                    exaMockCommand("/opt/exadata_ovm/vm_maker --stop-domain.*", aRc=0),
                    exaMockCommand("/usr/sbin/vm_maker --list-domains | /bin/grep 'running'.*", aStdout="scaqab10client01vm06.us.oracle.com(16)       : running"),
                    exaMockCommand("/usr/sbin/vm_maker --list-domains | /bin/grep 'running'.*", aStdout="scaqab10client01vm06.us.oracle.com(16)       : running"),

		        ],
		        [
                    exaMockCommand("/usr/sbin/vm_maker --list-domains.*", aStdout="scaqab10client01vm06.us.oracle.com(16)       :   running"),
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="Node type: KVMHOST"),
		        ],
		        [
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="Node type: KVMHOST"),
                    exaMockCommand("/usr/sbin/vm_maker --list-domains | /bin/grep 'running'.*", aStdout="scaqab10client01vm08.us.oracle.com(16)       : running"),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout="scaqab10client01vm08.us.oracle.com"),
                    exaMockCommand("/usr/sbin/vm_maker --list-domains | /bin/grep 'running'.*", aStdout="scaqab10client01vm08.us.oracle.com(16)       : running"),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout="scaqab10client01vm08.us.oracle.com"),
                    exaMockCommand("/bin/rm -rf *", aRc=0, aStdout="", aPersist=True),

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
                    exaMockCommand("/bin/mkdir -p oeda/requests/exatest/log/dbaasapilog", aRc=0),

                ],
                [
                    exaMockCommand("/bin/echo EXIT | /usr/bin/nc.*", aRc=0)
                ]
            ]

        }
        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        _options.jsonconf['vms'] = [{"hostname": "scaqab10client01vm08.us.oracle.com", "gb_memory": "40"}]
        cluctrl = self.mGetClubox()
        _rc = cluctrl.mManageVMMemory("memset", "scaqab10client01vm08.us.oracle.com", aOptions=_options)
        self.assertEqual(_rc, 0)



if __name__ == '__main__':
    unittest.main()

