import unittest

from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.cludiskgroups import ebCluManageDiskgroup
import os
import re

grid_out = """
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

class TestDiskMgr(ebTestClucontrol):

    '''
    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateDatabase=True)
        super().setUpClass()
    '''

    def setUp(self):
        self.mGetClubox()._exaBoxCluCtrl__ociexacc = False
        self.mGetClubox()._exaBoxCluCtrl__kvm_enabled = True
        #get_gcontext().mSetConfigOption('kvm_var_size',None)
        #self.mGetClubox().mRegisterVgComponents()

    def test_disk_mgr_failure(self):
        _cmds = {
            self.mGetRegexVm(): [
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


                #31
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

                #35
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

                #38
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

                [
                    exaMockCommand("mkdir -p.*"),
                    exaMockCommand("chown -R oracle:oinstall.*"),
                    exaMockCommand("/bin/scp .*")
                ],
                [
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i.*", aStdout="OK"),
                ],
                [
                    exaMockCommand("cat /var/opt/oracle/log/grid.*", aStdout=""),
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
                    exaMockCommand("cat /var/opt/oracle/log/grid.*", aStdout=""),
                ],
                
                #48
                [
                    exaMockCommand("cat /var/opt/oracle/log/grid.*", aStdout=""),
                ],
            
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/rm -f.*", aRc=0, aPersist=True),
                    exaMockCommand(".*ping.*", aRc=0, aPersist=True),
                    #exaMockCommand("/bin/mkdir -p oeda/requests/exatest/log/dbaasapilog", aRc=0)
                ],
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/local/bin/imageinfo -version", aStdout="20.1.1.0.0.200808")
                ],
                [
                    exaMockCommand("rm -rf /EXAVMIMAGES/System.first.boot.20.1.1.0.0.200722.*img"),
                    exaMockCommand("rm -rf /EXAVMIMAGES/System.first.boot.20.1.1.0.0.200722.*bz2")
                ]
            ],
            self.mGetRegexCell(): [
                [
                    exaMockCommand("cellcli -e alter griddisk.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e list griddisk attributes name where asmmodestatus.*", aRc=0, aPersist=True),
                ],
                [
                    exaMockCommand("cellcli -e alter griddisk.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e list griddisk attributes name where asmmodestatus.*", aRc=0, aPersist=True),
                ],
                [
                    exaMockCommand("cellcli -e alter griddisk.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e list griddisk attributes name where asmmodestatus.*", aRc=0, aPersist=True),
                ],
            ]

        }

        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        _options.diskgroupOp = 'create'
        _options.jsonconf['diskgroup_type'] = 'sparse'
        _options.jsonconf['diskgroup'] = 'DATAC8'
        _options.jsonconf['disk_backup_enabled'] = 'False'
        _options.jsonconf['storage_distribution'] = '35:50:15'
        _options.jsonconf['total_storagegb'] = 1000

        #_options.jsonconf['vms'] = [{"hostname": "scaqab10client01vm08.us.oracle.com", "gb_memory": "40"}, {"hostname": "scaqab10client02vm08.us.oracle.com", "gb_memory": "40"}]
        cluctrl = self.mGetClubox()
        _diskgroupobj = ebCluManageDiskgroup(cluctrl, aOptions=_options)
        _rc = _diskgroupobj.mClusterManageDiskGroup(aOptions=_options)
        self.assertNotEqual(_rc, 0)

    def test_disk_mgr_success(self):
        _cmds = {
            self.mGetRegexVm(): [
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


                #31
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

                #35
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

                #38
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

                #48
                [
                    exaMockCommand("cat /var/opt/oracle/log/grid.*", aStdout=grid_out),
                ],


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

                #60
                [
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i.*", aStdout="OK"),
                ],
                [
                    exaMockCommand("cat /var/opt/oracle/log/grid.*", aStdout=grid_out),
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

                #69
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
                #rollback from here



            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/rm -f.*", aRc=0, aPersist=True),
                    exaMockCommand(".*ping.*", aRc=0, aPersist=True),
                    #exaMockCommand("/bin/mkdir -p oeda/requests/exatest/log/dbaasapilog", aRc=0)
                ],
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/local/bin/imageinfo -version", aStdout="20.1.1.0.0.200808")
                ],
                [
                    exaMockCommand("rm -rf /EXAVMIMAGES/System.first.boot.20.1.1.0.0.200722.*img"),
                    exaMockCommand("rm -rf /EXAVMIMAGES/System.first.boot.20.1.1.0.0.200722.*bz2")
                ]
            ],
            self.mGetRegexCell(): [
                [
                    exaMockCommand("cellcli -e alter griddisk.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e create griddisk all.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e drop griddisk all.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e list griddisk attributes name where asmmodestatus.*", aRc=0, aPersist=True),

                ],
                [   
                    exaMockCommand("cellcli -e alter griddisk.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e create griddisk all.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e drop griddisk all.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e list griddisk attributes name where asmmodestatus.*", aRc=0, aPersist=True),

                ],
                [
                    exaMockCommand("cellcli -e alter griddisk.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e create griddisk all.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e drop griddisk all.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e list griddisk attributes name where asmmodestatus.*", aRc=0, aPersist=True),
                ],
                [
                    exaMockCommand("cellcli -e alter griddisk.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e create griddisk all.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e drop griddisk all.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e list griddisk attributes name where asmmodestatus.*", aRc=0, aPersist=True),
                ],
                [
                    exaMockCommand("cellcli -e alter griddisk.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e create griddisk all.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e drop griddisk all.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e list griddisk attributes name where asmmodestatus.*", aRc=0, aPersist=True),
                ],
                [
                    exaMockCommand("cellcli -e alter griddisk.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e create griddisk all.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e drop griddisk all.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e list griddisk attributes name where asmmodestatus.*", aRc=0, aPersist=True),
                ],

            ]

        }
        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        _options.diskgroupOp = 'create'
        _options.jsonconf['diskgroup_type'] = 'sparse'
        _options.jsonconf['diskgroup'] = 'DATAC8'
        _options.jsonconf['disk_backup_enabled'] = 'False'
        _options.jsonconf['storage_distribution'] = '35:50:15'
        _options.jsonconf['total_storagegb'] = 1000

        #_options.jsonconf['vms'] = [{"hostname": "scaqab10client01vm08.us.oracle.com", "gb_memory": "40"}, {"hostname": "scaqab10client02vm08.us.oracle.com", "gb_memory": "40"}]
        cluctrl = self.mGetClubox()
        _diskgroupobj = ebCluManageDiskgroup(cluctrl, aOptions=_options)
        _rc = _diskgroupobj.mClusterManageDiskGroup(aOptions=_options)
        self.assertNotEqual(_rc, 0)

if __name__ == '__main__':
    unittest.main()


