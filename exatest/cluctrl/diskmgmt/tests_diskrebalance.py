#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/diskmgmt/tests_diskrebalance.py 
#
# tests_diskrebalance.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates. 
#
#    NAME
#      tests_diskrebalance.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      Unittesting class to clustorage.py files
#
#    NOTES
#      NONE
#
#    MODIFIED MM/DD/YY
#    gparada  09/09/25 - 38254024 Reshape - Dynamic Storage for data reco sparse 
#    ?        ??/??/?? - Creation

import unittest

from unittest.mock import patch

from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.cludiskgroups import ebCluManageDiskgroup
from exabox.ovm.clustorage import ebCluStorageConfig, ebCluManageStorage
from exabox.core.Error import ExacloudRuntimeError
import os
import re

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
"SPRC8":{"rebalance_status":{"status":"DONE"}, "dg_storage_props":{"total_mb":"200", "used_mb":"98"}, "failgroups":{"SCAQAB10CELADM03":{"num_disks":"2", "celldisks":"cl1"}}},
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
"SPRC8":{"rebalance_status":{"status":"DONE"}, "dg_storage_props":{"total_mb":"200", "used_mb":"98"}, "failgroups":{"SCAQAB10CELADM03":{"num_disks":"2", "celldisks":"cl1"}}},
"msg":"Done"
}
"""

size_out = """
{
"id":"1",
"logfile":"log data",
"status":"Success",
"RECOC8":{"dg_storage_props":{"total_mb":"200", "used_mb":"100"}, "failgroups":{"SCAQAB10CELADM01":{"num_disks":"2", "celldisks":"cl1"}}},
"DATAC8":{"rebalance_status":{"status":"DONE"}, "dg_storage_props":{"total_mb":"511968", "used_mb":"51196"}, "failgroups":{"SCAQAB10CELADM02":{"num_disks":"2", "celldisks":"cl1"}}},
"SPARSEC8":{"rebalance_status":{"status":"DONE"}, "dg_storage_props":{"total_mb":"200", "used_mb":"98"}, "failgroups":{"SCAQAB10CELADM03":{"num_disks":"2", "celldisks":"cl1"}}},
"msg":"Done"
}
"""

grid_diskgroupOp_out= """
{
   "dbname" : "",
   "exceptionErrorCodes" : "",
   "start" : "",
   "pid" : "",
   "recovery" : "",
   "resourceId" : "",
   "id" : "9f5e790e-8c14-4f2c-84fa-231e6c4271e1",
   "creation" : "",
   "workflow_id" : "",
   "workflow_enabled" : "0",
   "action" : "info",
   "infofile_content" : "",
   "perl_proxy_pid" : "",
   "ts" : "20250908 21:47:30",
   "msg" : "For security please remove your input file.",
   "object" : "db",
   "infofile_loc" : "/var/opt/oracle/log/grid/diskgroupOp-5753321a-8cfd-11f0-9100-000017018d97-0.786276.info_5753321a-8cfd-11f0-9100-000017018d97.json",
   "status" : "Starting",
   "logfile" : "/var/opt/oracle/log/grid/dbaasapi/db/diskgroup/9f5e790e-8c14-4f2c-84fa-231e6c4271e1.log",
   "progress" : "0",
   "operation" : "diskgroup",
   "errmsg" : "",
   "dgObserverResponseDetails" : "",
   "outputfile" : "/var/opt/oracle/log/grid/diskgroupOp-5753321a-8cfd-11f0-9100-000017018d97-0.786276.info_5753321a-8cfd-11f0-9100-000017018d97.out",
   "jobSpecificDetailsJson" : "",
   "host" : ""
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

    def test_disk_mgr_(self):
        _cmds = \
        {        
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




                [
                    exaMockCommand("mkdir -p.*"),
                    exaMockCommand("chown -R oracle:oinstall.*"),
                    exaMockCommand("/bin/scp .*")
                ],

                #36
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
                    exaMockCommand("cat /var/opt/oracle/log/grid.*", aStdout=size_out),
                ],

                [
                    exaMockCommand("mkdir -p.*"),
                    exaMockCommand("chown -R oracle:oinstall.*"),
                    exaMockCommand("/bin/scp .*")
                ],


                #50
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
                    exaMockCommand("cat /var/opt/oracle/log/grid.*", aStdout=size_out),
                ],


                [
                    exaMockCommand("mkdir -p.*"),
                    exaMockCommand("chown -R oracle:oinstall.*"),
                    exaMockCommand("/bin/scp .*")
                ],


                #57
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
                    exaMockCommand("cat /var/opt/oracle/log/grid.*", aStdout=size_out),
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

                #67 
                [
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i.*", aStdout="OK"),
                ],

                [
                    exaMockCommand("cat /var/opt/oracle/log/grid.*", aStdout=grid_out),
                ],
                [
                    exaMockCommand("mkdir -p.*"),
                    exaMockCommand("cat /var/opt/oracle/log/grid.*", aStdout=grid_out),
                    exaMockCommand("chown -R oracle:oinstall.*"),
                    exaMockCommand("/bin/scp .*")
                ],
                [
                    exaMockCommand("mkdir -p.*"),
                    exaMockCommand("cat /var/opt/oracle/log/grid.*", aStdout=grid_out),
                    exaMockCommand("chown -R oracle:oinstall.*"),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i.*", aStdout="OK"),
                    exaMockCommand("/bin/scp .*")

                ],
                [
                    exaMockCommand("mkdir -p.*"),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i.*", aStdout="OK"),
                    exaMockCommand("cat /var/opt/oracle/log/grid.*", aStdout=grid_out),
                    exaMockCommand("chown -R oracle:oinstall.*"),
                    exaMockCommand("/bin/scp .*")
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

                #76
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
                    exaMockCommand("mkdir -p.*"),
                    exaMockCommand("chown -R oracle:oinstall.*"),
                    exaMockCommand("cat /var/opt/oracle/log/grid.*", aStdout=grid_out),
                    exaMockCommand("/bin/scp .*")
                ],
                [
                    exaMockCommand("mkdir -p.*"),
                    exaMockCommand("chown -R oracle:oinstall.*"),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i.*", aStdout="OK"),
                    exaMockCommand("/bin/scp .*")
                ],
                [
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i.*", aStdout="OK"),
                    exaMockCommand("cat /var/opt/oracle/log/grid.*", aStdout=grid_out),
                ],
                [
                    exaMockCommand("cat /var/opt/oracle/log/grid.*", aStdout=grid_out),
                    exaMockCommand("mkdir -p.*"),
                    exaMockCommand("chown -R oracle:oinstall.*"),
                    exaMockCommand("/bin/scp .*")
                ],
                [
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i.*", aStdout="OK"),
                    exaMockCommand("mkdir -p.*"),
                    exaMockCommand("chown -R oracle:oinstall.*"),
                    exaMockCommand("/bin/scp .*")
                ],

                [
                    exaMockCommand("cat /var/opt/oracle/log/grid.*", aStdout=grid_out),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i.*", aStdout="OK"),
                    exaMockCommand("mkdir -p.*"),
                    exaMockCommand("chown -R oracle:oinstall.*"),
                    exaMockCommand("/bin/scp .*")
                ],

                #88
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



                ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/rm -f.*", aRc=0, aPersist=True),
                    exaMockCommand(".*ping.*", aRc=0, aPersist=True),
                    #exaMockCommand("/bin/mkdir -p oeda/requests/exatest/log/dbaasapilog", aRc=0)
                ],
            ],
            self.mGetRegexCell(): [
                [
                    # exaMockCommand("cellcli -e alter griddisk.*", aRc=0, aPersist=True),
                    # exaMockCommand("cellcli -e list griddisk attributes name where asmmodestatus.*", aRc=0, aPersist=True),
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)

        cluctrl = self.mGetClubox()
        disks_xml = \
            'exabox/exatest/cluctrl/diskmgmt/resources/rack_disks.xml'
        #shutil.copy2('exabox/exatest/cluctrl/cluzdlra/resources/disks.xml', disks_xml)
        #os.chmod(disks_xml, 0o744)
        # load zdlra XML

        jsonconf = cluctrl.mGetArgsOptions().jsonconf

        cluctrl.mSetConfigPath(disks_xml)
        cluctrl.mSetPatchConfig(disks_xml)

        _options = self.mGetPayload()

        '''
        _options.diskgroupOp = 'resize'
        _options.jsonconf['diskgroup_type'] = 'sparse'
        _options.jsonconf['diskgroup'] = 'DATAC8'
        _options.jsonconf['disk_backup_enabled'] = 'False'
        _options.jsonconf['storage_distribution'] = '35.0:50.0:15.0'
        _options.jsonconf['total_storagegb'] = 1000
        '''

        _options.jsonconf['OLDSIZE_GB'] = '100'
        _options.jsonconf['NEWSIZE_GB'] = '150'
        _options.jsonconf['rack'] = {}
        _options.jsonconf['rack']['backup_disk'] = "false"
        _options.jsonconf['rack']['create_sparse'] = "true"

        cluctrl = self.mGetClubox()

        _storage = ebCluManageStorage(cluctrl, _options)
        with patch('exabox.ovm.clustorage.ebCluManageStorage.mCheckGridDisksResizedCells', return_value=True):
            _rc = _storage.mClusterStorageResize(_options)

        self.assertEqual(_rc, 0)

    @patch.object(ebCluManageStorage, 'mClusterStorageResize')
    def test_mHandlerResizeStorage(self, mock_mClusterStorageResize):
        """
        Tests method mHandlerResizeStorage in clucontrol
        """
        # Arrange
        instance = self.mGetClubox()
        _options = self.mGetPayload()
        _options.jsonconf['OLDSIZE_GB'] = '100'
        _options.jsonconf['NEWSIZE_GB'] = '150'
        _options.jsonconf['rack'] = {}
        _options.jsonconf['rack']['backup_disk'] = "false"
        mock_mClusterStorageResize.return_value = 1

        # Act and Assert
        with self.assertRaises(ExacloudRuntimeError),\
             patch.object(self.mGetClubox(), 'remote_lock'):
            instance.mHandlerResizeStorage(_options)

if __name__ == '__main__':
    unittest.main()


