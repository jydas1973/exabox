import unittest

from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.cludiskgroups import ebCluManageDiskgroup
from exabox.ovm.clustorage import ebCluStorageConfig, ebCluManageStorage, ebCluQuorumManager
from exabox.ovm.cluelasticcompute import ebCluReshapeCompute
from unittest.mock import patch, MagicMock, PropertyMock, mock_open
import os
import re
import io
import warnings

dsget_out = """profile: /DATAC1/disk
parameter: /DATAC1/disk
"""

vdisk_out= """##  STATE    File Universal Id                File Name Disk group
--  -----    -----------------                --------- ---------
 1. ONLINE   b5d451b8d4f24f8dbf25655bd24bd917
(o/192.168.136.24;192.168.136.25/DATAC1_CD_05_sea201203exdcl12) [DATAC1]
 2. ONLINE   6f4b23dd40c04f48bf7dbfedcf829dfe
(o/192.168.136.20;192.168.136.21/DATAC1_CD_05_sea201203exdcl10) [DATAC1]
 3. ONLINE   7bce04af06fc4f1fbfbe90bd35d419bb
(o/192.168.136.22;192.168.136.23/DATAC1_CD_05_sea201203exdcl11) [DATAC1]
 4. ONLINE   9d72c23e27f54fc0bf232e28ead51ba4
(/dev/exadata_quorum/QD_DATAC1_C41203Y0F2Z1) [DATAC1]
Located 4 voting disk(s).
"""

host_out="""SCAQAB10CLIENT01VM08
SCAQAB10CLIENT01VM08
"""

host2_out="""NEWVMDOMU
NEWVMDOMU
"""

grid_out = """
{
"id":"1",
"logfile":"log data",
"status":"Success",
"RECOC8":{"dg_storage_props":{"total_mb":"92160", "used_mb":"100"}, "failgroups":{"SCAQAB10CELADM01":{"num_disks":"2", "celldisks":"cl1"}}},
"DATAC8":{"rebalance_status":{"status":"DONE"}, "dg_storage_props":{"total_mb":"276480", "used_mb":"100"}, "failgroups":{"SCAQAB10CELADM02":{"num_disks":"2", "celldisks":"cl1"}}},
"SPARSEC8":{"rebalance_status":{"status":"DONE"}, "dg_storage_props":{"total_mb":"92160", "used_mb":"100"}, "failgroups":{"SCAQAB10CELADM03":{"num_disks":"2", "celldisks":"cl1"}}},
"msg":"Done"
}
"""

rebalance_out = """
{
"id":"1",
"logfile":"log data",
"status":"Success",
"RECOC8":{"dg_storage_props":{"total_mb":"200", "used_mb":"100"}, "failgroups":{"SCAQAB10CELADM01":{"num_disks":"2", "celldisks":"cl1"}}},
"DATAC8":{"dg_storage_props":{"total_mb":"200", "used_mb":"100"}, "failgroups":{"SCAQAB10CELADM02":{"num_disks":"2", "celldisks":"cl1"}}},
"SPRC8":{"rebalance_status":{"status":"DONE"}, "dg_storage_props":{"total_mb":"200", "used_mb":"100"}, "failgroups":{"SCAQAB10CELADM03":{"num_disks":"2", "celldisks":"cl1"}}},
"msg":"Done",
"Status":"Pass",
"rebalance_time_estimate":{"error_code":0}
}
"""
validate_out = """
{
"id":"1",
"logfile":"log data",
"status":"Success",
"RECOC8":{"dg_storage_props":{"total_mb":"200", "used_mb":"100"}, "failgroups":{"SCAQAB10CELADM01":{"num_disks":"2", "celldisks":"cl1"}}},
"DATAC8":{"dg_storage_props":{"total_mb":"200", "used_mb":"100"}, "failgroups":{"SCAQAB10CELADM02":{"num_disks":"2", "celldisks":"cl1"}}},
"SPRC8":{"rebalance_status":{"status":"DONE"}, "dg_storage_props":{"total_mb":"200", "used_mb":"100"}, "failgroups":{"SCAQAB10CELADM03":{"num_disks":"2", "celldisks":"cl1"}}},
"msg":"Done"
}
"""

size_out = """
{
"id":"1",
"logfile":"log data",
"status":"Success",
"RECOC8":{"dg_storage_props":{"total_mb":"200", "used_mb":"100"}, "failgroups":{"SCAQAB10CELADM01":{"num_disks":"2", "celldisks":"cl1"}}},
"DATAC8":{"rebalance_status":{"status":"DONE"}, "dg_storage_props":{"total_mb":"511968", "used_mb":"511968"}, "failgroups":{"SCAQAB10CELADM02":{"num_disks":"2", "celldisks":"cl1"}}},
"SPARSEC8":{"rebalance_status":{"status":"DONE"}, "dg_storage_props":{"total_mb":"200", "used_mb":"100"}, "failgroups":{"SCAQAB10CELADM03":{"num_disks":"2", "celldisks":"cl1"}}},
"msg":"Done"
}
"""

cmd1 = "/usr/bin/cat /etc/oratab | /usr/bin/grep '^+ASM.*'"
op1 = "+ASM1:/u01/app/19.0.0.0/grid:N"
cmd2 = "/u01/app/19.0.0.0/grid/bin/crsctl check crs"
op2 = "CRS-4638: Oracle High Availability Services is online"
cmd3 = "/u01/app/19.0.0.0/grid/bin/olsnodes -s -n|grep Active"
op3 = "scaqab10client01vm08\nscaqab10client02vm08"
cmd4 = "/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'"
op4 = "path1"

lsdg_out = """State   Type Rebal Sector Logical_Sector Block      AU Total_MB Free_MB Req_mir_free_MB Usable_file_MB Offline_disks Voting_files Name
MOUNTED HIGH N        512            512  4096 4194304  3686400 2417516 	  51200         788772             0            Y DATAC1/
MOUNTED HIGH N        512            512  4096 4194304  1179648  784932  	  16384         256182             0            Y RECOC1/
"""

list_out = """Device path: /dev/exadata_quorum/QD_DATAC1_DB01
Host name: SCAQAB10CLIENT01VM08
ASM disk group name: DATAC1
Size: 128 MB
"""

list_out1 = """Device path: /dev/exadata_quorum/QD_DATAC1_DB01
Host name: SCAQAB10CLIENT01VM08
Host name: NEWVMDOMU
ASM disk group name: DATAC1
Size: 128 MB
"""

vdisk2_out= """##  STATE    File Universal Id                File Name Disk group
--  -----    -----------------                --------- ---------
 1. ONLINE   b5d451b8d4f24f8dbf25655bd24bd917
(o/192.168.136.24;192.168.136.25/DATAC1_CD_05_sea201203exdcl12) [DATAC1]
 2. ONLINE   6f4b23dd40c04f48bf7dbfedcf829dfe
(o/192.168.136.20;192.168.136.21/DATAC1_CD_05_sea201203exdcl10) [DATAC1]
 3. ONLINE   7bce04af06fc4f1fbfbe90bd35d419bb
(o/192.168.136.22;192.168.136.23/DATAC1_CD_05_sea201203exdcl11) [DATAC1]
 4. ONLINE   9d72c23e27f54fc0bf232e28ead51ba4
(/dev/exadata_quorum/QD_DATAC1_C41203Y0F2Z1) [DATAC1]
Located 5 voting disk(s).
"""

ELASTIC_PAYLOAD = {
    "reshaped_node_subset": {
        "added_computes": [
				{
					"compute_node_hostname":"scaqab10adm01.us.oracle.com",
					"network_info": {
						"computenetworks":{}
						},
					"rack_info": {
						"uheight": "rack1",
						"uloc": "loc1"
						},
					"virtual_compute_info": {
						"compute_node_hostname": "scaqab10client01vm07.us.oracle.com",
						"network_info": {
							"virtualcomputenetworks": {}
							}
						}
				},
	                        {
        	                        "compute_node_hostname":"scaqab10adm02.us.oracle.com", 
                                        "network_info": {
                                                "computenetworks":{}
                                                },
                                        "rack_info": {
                                                "uheight": "rack1",
                                                "uloc": "loc1"
                                                },
                                        "virtual_compute_info": {
                                                "compute_node_hostname": "scaqab10client02vm07.us.oracle.com",
                                                "network_info": {
                                                        "virtualcomputenetworks": {}
                                                        }
                                                }
                	        }, 
			],
        "removed_computes": [],
        "num_participating_computes":2,
        "participating_computes":[{"compute_node_alias":"node-2","compute_node_hostname":"scaqan02adm02.us.oracle.com"}, {"compute_node_alias":"node-1","compute_node_hostname":"scaqan02adm01.us.oracle.com"}],


        "added_cells": [],
        "removed_cells": [ { 
            "cell_node_hostname": "iad103712exdcl09.iad103712exd.adminiad1.oraclevcn.com" 
        } ],
        "full_compute_to_virtualcompute_list": [
            {
              "compute_node_hostname": "iad103716exdd015.iad103716exd.adminiad1.oraclevcn.com",
              "compute_node_virtual_hostname": "iad103716x8mcompexpn15c.clientsubnet.devx8melastic.oraclevcn.com"
            },
            {
              "compute_node_hostname": "iad103716exdd016.iad103716exd.adminiad1.oraclevcn.com",
              "compute_node_virtual_hostname": "iad103716x8mcompexpn16c.clientsubnet.devx8melastic.oraclevcn.com"
            }
        ]
    }
}

class TestQuorumDiskMgr(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateDatabase = True)
        warnings.filterwarnings("ignore")

    def setUp(self):
        self.mGetClubox()._exaBoxCluCtrl__ociexacc = False
        self.mGetClubox()._exaBoxCluCtrl__kvm_enabled = True

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, "/u01/app/grid"))
    @patch('exabox.ovm.clucontrol.node_cmd_abs_path_check')
    @patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', return_value=0)
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog')
    def test_quorumdisk_add_(self,mock_pathcheck1,mock_exitstatus,mock_executelog, mock_mGetOracleBaseDirectories):
        _cmds = {
            self.mGetRegexVm(): [
		[
                    exaMockCommand(re.escape(cmd1), aRc=0, aStdout=op1), 
                    exaMockCommand(re.escape(cmd2), aRc=0, aStdout=op2),
                    exaMockCommand(re.escape(cmd3), aRc=0, aStdout=op3),
                    exaMockCommand(".*select path from GV.*"),
                    exaMockCommand("/opt/oracle.SupportTools/quorumdiskmgr --delete --device.*", aStdout="[Success] Successfully deleted"),

                    exaMockCommand(".*select path from GV.*", aStdout=host2_out),
                    exaMockCommand(".*alter diskgroup.*", aStdout="Diskgroup altered."),

		],
                [
                    exaMockCommand("/opt/oracle.SupportTools/quorumdiskmgr --delete --device.*", aStdout="[Success] Successfully deleted"),
                    exaMockCommand("/opt/oracle.SupportTools/quorumdiskmgr --delete --target.*", aStdout="[Success] Successfully deleted target"),
                    exaMockCommand("/opt/oracle.SupportTools/quorumdiskmgr --delete --config.*", aStdout="[Success] Successfully deleted quorum disk configuration"),
                    exaMockCommand("/opt/oracle.SupportTools/quorumdiskmgr --create --config --owner=grid.*", aStdout="[Success] Successfully created quorum disk configurations"),
                    exaMockCommand("/opt/oracle.SupportTools/quorumdiskmgr --create --target.*", aStdout="[Success] Successfully created target"),
                    exaMockCommand("/opt/oracle.SupportTools/quorumdiskmgr --create --device.*", aStdout="[Success] Successfully created all device(s) from target(s) on machine"),
                    exaMockCommand("/opt/oracle.SupportTools/quorumdiskmgr --list --device", aStdout=list_out1),
                    exaMockCommand(".*/bin/asmcmd dsget.*", aRc=0, aStdout=dsget_out),
                    exaMockCommand(".*alter system set asm_diskstring.*", aStdout="System altered."),
                    exaMockCommand(".*select path from GV.*", aStdout=host_out),
                    exaMockCommand(".*alter diskgroup.*", aStdout="Diskgroup altered."),

                    exaMockCommand(".*crsctl query css votedisk.*", aStdout=vdisk_out),

                    exaMockCommand(".*crsctl query css votedisk.*", aStdout=vdisk2_out),
                    exaMockCommand(".*select path from GV.*", aStdout=host_out),
                    exaMockCommand(".*alter diskgroup.*", aStdout="Diskgroup altered."),
                    exaMockCommand("/opt/oracle.SupportTools/quorumdiskmgr --delete --device.*", aStdout="[Success] Successfully deleted"),
                    exaMockCommand(".*select path from GV.*"),
                ],
                [
                    exaMockCommand(".*ls -la /var/opt/oracle/creg/grid | head -2 | grep ...x..x..."),
                    exaMockCommand("cat /var/opt/oracle/creg/grid/grid.ini | grep \"^sid\"", aRc=0, aStdout= "ASM1", aPersist=True),
                    exaMockCommand("cat /var/opt/oracle/creg/grid/grid.ini | grep \"^oracle_home\"", aRc=0, aStdout= "/u01/app/19.0.0.0/grid", aPersist=True),
                    #exaMockCommand(".*select path from GV.*"),
                ],
                [
                    exaMockCommand("/opt/oracle.SupportTools/quorumdiskmgr --delete --device.*", aStdout="[Success] Successfully deleted"),
                    exaMockCommand(".*ls -la /var/opt/oracle/creg/grid | head -2 | grep ...x..x..."),
                    exaMockCommand("cat /var/opt/oracle/creg/grid/grid.ini | grep \"^sid\"", aRc=0, aStdout= "ASM1", aPersist=True),
                    exaMockCommand("cat /var/opt/oracle/creg/grid/grid.ini | grep \"^oracle_home\"", aRc=0, aStdout= "/u01/app/19.0.0.0/grid", aPersist=True),
                    exaMockCommand(".*/bin/asmcmd lsdg.*", aStdout=lsdg_out),
                    exaMockCommand("/opt/oracle.SupportTools/quorumdiskmgr --delete --device.*", aStdout="[Success] Successfully deleted"),
                    exaMockCommand("/opt/oracle.SupportTools/quorumdiskmgr --delete --target.*", aStdout="[Success] Successfully deleted target"),
                    exaMockCommand("/opt/oracle.SupportTools/quorumdiskmgr --delete --config.*", aStdout="[Success] Successfully deleted quorum disk configuration"),
                    exaMockCommand("/opt/oracle.SupportTools/quorumdiskmgr --create --config --owner=grid.*", aStdout="[Success] Successfully created quorum disk configurations"),
                    exaMockCommand("/opt/oracle.SupportTools/quorumdiskmgr --create --target.*", aStdout="[Success] Successfully created target"),
                    exaMockCommand("/opt/oracle.SupportTools/quorumdiskmgr --create --device.*", aStdout="[Success] Successfully created all device(s) from target(s) on machine"),
                    exaMockCommand("/opt/oracle.SupportTools/quorumdiskmgr --list --device", aStdout=list_out1),

                ],

                ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/rm -f.*", aRc=0, aPersist=True),
                    exaMockCommand(".*ping.*", aRc=0, aPersist=True),
                ],
            ],

        }
        self.mPrepareMockCommands(_cmds)

        cluctrl = self.mGetClubox()

        _options = self.mGetPayload()
        _options.jsonconf = ELASTIC_PAYLOAD 

        _quorum = ebCluQuorumManager(cluctrl)
        _reshape = ebCluReshapeCompute(cluctrl, _options)

        _ip_list = ["10.1.1.3", "10.1.1.4"]

        _domu_list = [ _domu for _ , _domu in cluctrl.mReturnDom0DomUPair()]
        _quorum.mAddQuorumDisk(_domu_list[0], "newvmdomu.oracle.com", _ip_list, _reshape)

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetGridHome', return_value=("/u01/app/19.0.0.0/grid", None))
    @patch("exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mSetSrcDom0DomU")
    @patch('exabox.ovm.clucontrol.node_cmd_abs_path_check')
    @patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', return_value=0)
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog')
    def test_quorumdisk_remove_(self, mock_mGetGridHome, mock_mSetSrcDom0DomU, mock_pathcheck1,mock_exitstatus,mock_executelog):
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/u01/app/19.0.0.0/grid/bin/asmcmd lsdg", aStdout=lsdg_out),
                    exaMockCommand("/opt/oracle.SupportTools/quorumdiskmgr --device --list", aStdout=list_out),
                    exaMockCommand("/opt/oracle.SupportTools/quorumdiskmgr --delete --device --asm-disk-group", aStdout="Successfully deleted device"),
                    exaMockCommand("/opt/oracle.SupportTools/quorumdiskmgr --delete --target --asm-disk-group", aStdout="Successfully deleted target"),
                ],
                [
                    exaMockCommand(".*select name from V.*", aStdout="QD_DATAC1_DB01"),
                    exaMockCommand(".*alter diskgroup DATAC1 drop quorum disk.*", aStdout="Diskgroup altered."),
                ],
                #6
                [
                    exaMockCommand("mkdir -p.*"),
                    exaMockCommand("chown -R oracle:oinstall.*"),
                    exaMockCommand("/bin/scp .*")
                ],
                [
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i.*", aStdout="OK"),
                ],
                [
                    exaMockCommand("cat /var/opt/oracle/log/grid.*", aStdout=grid_out),
                ],
                [
                    exaMockCommand("mkdir -p.*"),
                    exaMockCommand("chown -R oracle:oinstall.*"),
                    exaMockCommand("/bin/scp .*")
                ],
                [
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i.*", aStdout="OK"),
                ],
                [
                    exaMockCommand("cat /var/opt/oracle/log/grid.*", aStdout=grid_out),
                ],
                [
                    exaMockCommand("cat /var/opt/oracle/log/grid.*", aStdout=grid_out),
                ],


                ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/rm -f.*", aRc=0, aPersist=True),
                    exaMockCommand(".*ping.*", aRc=0, aPersist=True),
                ],
            ],

        }
        self.mPrepareMockCommands(_cmds)

        cluctrl = self.mGetClubox()

        _options = self.mGetPayload()
        _options.jsonconf = ELASTIC_PAYLOAD

        _quorum = ebCluQuorumManager(cluctrl)
        _reshape = ebCluReshapeCompute(cluctrl, _options)
        _domu_list = [ _domu for _ , _domu in cluctrl.mReturnDom0DomUPair()]
        _quorum.mRemoveQuorumDisk(_domu_list[0], _options, _reshape)


if __name__ == '__main__':
    unittest.main()


