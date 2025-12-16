import unittest

from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.cludiskgroups import ebCluManageDiskgroup
from exabox.log.LogMgr import ebLogInfo
import os
import re
import json
from unittest.mock import patch, MagicMock, PropertyMock, mock_open

grid_out = """
{
"id":"1",
"logfile":"log data",
"status":"Success",
"RECOC8":{"dg_storage_props":{"total_mb":"200", "used_mb":"100"}, "failgroups":{"SCAQAB10CELADM01":{"num_disks":"2", "celldisks":"cl1"}}},
"DATAC8":{"rebalance_status":{"status":"DONE"}, "dg_storage_props":{"total_mb":"200", "used_mb":"100"}, "failgroups":{"SCAQAB10CELADM02":{"num_disks":"2", "celldisks":"cl1"}}},
"SPRC8":{"rebalance_status":{"status":"DONE"}, "dg_storage_props":{"total_mb":"200", "used_mb":"100"}, "failgroups":{"SCAQAB10CELADM03":{"num_disks":"2", "celldisks":"cl1"}}},
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
"SPRC8":{"rebalance_status":{"status":"DONE"}, "dg_storage_props":{"total_mb":"200", "used_mb":"100"}, "failgroups":{"SCAQAB10CELADM03":{"num_disks":"2", "celldisks":"cl1"}}},
"msg":"Done"
}
"""
class testOptions(object): pass

class TestDiskMgr(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateDatabase=True)

    def setUp(self):
        self.mGetClubox()._exaBoxCluCtrl__ociexacc = False
        self.mGetClubox()._exaBoxCluCtrl__kvm_enabled = True

    def test_disk_mgr_resize_failure_insufficient_params(self):
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("mkdir -p.*"),
                ],
                ]
        }
        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        _options.diskgroupOp = 'resize'
        _options.jsonconf['diskgroup_type'] = 'sparse'
        _options.jsonconf['diskgroup'] = 'DATAC8'
        _options.jsonconf['disk_backup_enabled'] = 'False'
        _options.jsonconf['storage_distribution'] = '35:50:15'
        _options.jsonconf['total_storagegb'] = 1000

        cluctrl = self.mGetClubox()
        _diskgroupobj = ebCluManageDiskgroup(cluctrl, aOptions=_options)
        _rc = _diskgroupobj.mClusterManageDiskGroup(aOptions=_options)
        self.assertNotEqual(_rc, 0)

    def test_disk_mgr_resize_success(self):
        _dg_suffix = 'C8'
        _cellcli_path = "/opt/oracle/cell/cellsrv/bin/cellcli"
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

                #20
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
                    exaMockCommand("cat /var/opt/oracle/log/rebalance.*", aStdout=rebalance_out),
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
                    exaMockCommand("cat /var/opt/oracle/log/rebalance.*", aStdout=rebalance_out),
                ],
                [
                    exaMockCommand("cat /var/opt/oracle/log/validate.*", aStdout=validate_out),
                ],
                [
                    exaMockCommand("mkdir -p.*"),
                    exaMockCommand("chown -R oracle:oinstall.*"),
                    exaMockCommand("/bin/scp .*")
                ],
                [
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i.*", aStdout="OK"),
                ],
                #30
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
                #40
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
                #40
                [
                    exaMockCommand("cat /var/opt/oracle/log/grid.*", aStdout=grid_out),
                ],
                [
                    exaMockCommand("cat /var/opt/oracle/log/grid.*", aStdout=size_out),
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
                    exaMockCommand(f"{_cellcli_path} -e \"list griddisk attributes name where asmmodestatus=\'DROPPED\' and name like \'.*{_dg_suffix}.*\'\"", aRc=0, aPersist=True),
                    exaMockCommand(f"{_cellcli_path} -e \"list griddisk attributes name where asmmodestatus=\'OFFLINE\' and name like \'.*{_dg_suffix}.*\'\"", aRc=0, aPersist=True),
                    exaMockCommand(f"{_cellcli_path} -e \"list griddisk attributes name where asmmodestatus=\'UNKNOWN\' and name like \'.*{_dg_suffix}.*\'\"", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e alter griddisk.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e create griddisk all.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e drop griddisk all.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e list griddisk attributes name where asmmodestatus.*", aRc=0, aPersist=True),
                    exaMockCommand("/opt/oracle/cell/cellsrv/bin/cellcli -e \"list griddisk attributes name,asmmodestatus where name like*", aRc=0, aPersist=True),

                ],
                [   
                    exaMockCommand(f"{_cellcli_path} -e \"list griddisk attributes name where asmmodestatus=\'DROPPED\' and name like \'.*{_dg_suffix}.*\'\"", aRc=0, aPersist=True),
                    exaMockCommand(f"{_cellcli_path} -e \"list griddisk attributes name where asmmodestatus=\'OFFLINE\' and name like \'.*{_dg_suffix}.*\'\"", aRc=0, aPersist=True),
                    exaMockCommand(f"{_cellcli_path} -e \"list griddisk attributes name where asmmodestatus=\'UNKNOWN\' and name like \'.*{_dg_suffix}.*\'\"", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e alter griddisk.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e create griddisk all.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e drop griddisk all.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e list griddisk attributes name where asmmodestatus.*", aRc=0, aPersist=True),

                ],
                [
                    exaMockCommand(f"{_cellcli_path} -e \"list griddisk attributes name where asmmodestatus=\'DROPPED\' and name like \'.*{_dg_suffix}.*\'\"", aRc=0, aPersist=True),
                    exaMockCommand(f"{_cellcli_path} -e \"list griddisk attributes name where asmmodestatus=\'OFFLINE\' and name like \'.*{_dg_suffix}.*\'\"", aRc=0, aPersist=True),
                    exaMockCommand(f"{_cellcli_path} -e \"list griddisk attributes name where asmmodestatus=\'UNKNOWN\' and name like \'.*{_dg_suffix}.*\'\"", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e alter griddisk.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e create griddisk all.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e drop griddisk all.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e list griddisk attributes name where asmmodestatus.*", aRc=0, aPersist=True),
                ],
                [
                    exaMockCommand(f"{_cellcli_path} -e \"list griddisk attributes name where asmmodestatus=\'DROPPED\' and name like \'.*{_dg_suffix}.*\'\"", aRc=0, aPersist=True),
                    exaMockCommand(f"{_cellcli_path} -e \"list griddisk attributes name where asmmodestatus=\'OFFLINE\' and name like \'.*{_dg_suffix}.*\'\"", aRc=0, aPersist=True),
                    exaMockCommand(f"{_cellcli_path} -e \"list griddisk attributes name where asmmodestatus=\'UNKNOWN\' and name like \'.*{_dg_suffix}.*\'\"", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e alter griddisk.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e create griddisk all.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e drop griddisk all.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e list griddisk attributes name where asmmodestatus.*", aRc=0, aPersist=True),
                ],
                [
                    exaMockCommand(f"{_cellcli_path} -e \"list griddisk attributes name where asmmodestatus=\'DROPPED\' and name like \'.*{_dg_suffix}.*\'\"", aRc=0, aPersist=True),
                    exaMockCommand(f"{_cellcli_path} -e \"list griddisk attributes name where asmmodestatus=\'OFFLINE\' and name like \'.*{_dg_suffix}.*\'\"", aRc=0, aPersist=True),
                    exaMockCommand(f"{_cellcli_path} -e \"list griddisk attributes name where asmmodestatus=\'UNKNOWN\' and name like \'.*{_dg_suffix}.*\'\"", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e alter griddisk.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e create griddisk all.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e drop griddisk all.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e list griddisk attributes name where asmmodestatus.*", aRc=0, aPersist=True),
                ],
                [
                    exaMockCommand(f"{_cellcli_path} -e \"list griddisk attributes name where asmmodestatus=\'DROPPED\' and name like \'.*{_dg_suffix}.*\'\"", aRc=0, aPersist=True),
                    exaMockCommand(f"{_cellcli_path} -e \"list griddisk attributes name where asmmodestatus=\'OFFLINE\' and name like \'.*{_dg_suffix}.*\'\"", aRc=0, aPersist=True),
                    exaMockCommand(f"{_cellcli_path} -e \"list griddisk attributes name where asmmodestatus=\'UNKNOWN\' and name like \'.*{_dg_suffix}.*\'\"", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e alter griddisk.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e create griddisk all.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e drop griddisk all.*", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e list griddisk attributes name where asmmodestatus.*", aRc=0, aPersist=True),
                ],

            ]

        }
        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        _options.diskgroupOp = 'resize'
        _options.jsonconf['new_sizeGB'] = '500'

        _options.jsonconf['diskgroup_type'] = 'sparse'
        _options.jsonconf['diskgroup'] = 'DATAC8'
        _options.jsonconf['disk_backup_enabled'] = 'False'
        _options.jsonconf['storage_distribution'] = '35:50:15'
        _options.jsonconf['total_storagegb'] = 1000

        cluctrl = self.mGetClubox()
        _diskgroupobj = ebCluManageDiskgroup(cluctrl, aOptions=_options)
        _rc = _diskgroupobj.mClusterManageDiskGroup(aOptions=_options)
        self.assertEqual(_rc, 0)

    def test_mClusterDgrpInfo2(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluManageDiskgroup.mClusterDgrpInfo2")

        _exaBoxObj = self.mGetClubox()
        _options = self.mGetPayload()
        _diskgroupobj = ebCluManageDiskgroup(_exaBoxObj, aOptions=_options)
        _mock_constant_obj = testOptions()
        _mock_constant_obj._dbaasapi_object_key = "mock_dbaas_key"
        _mock_constant_obj._dbaasapi_object_value = "mock_dbaas_value"
        _mock_constant_obj._operation_key = "mock_operation_key"
        _mock_constant_obj._operation_value = "mock_operation_value"
        _mock_constant_obj._action_key = "mock_action_key"
        _mock_constant_obj._params_key = "mock_params_key"
        _mock_constant_obj._dbname_key = "mock_dbname_key"
        _mock_constant_obj._dbname_value = "mock_dbname_value"
        _mock_constant_obj._diskgroupname_key = "mock_diskgroupname_key"
        _mock_constant_obj._props_key = "mock_props_key"
        _mock_constant_obj._flags_key = "mock_flags_key"
        _mock_constant_obj._supported_dg_properties = ["mock_property1", "mock_property2"]

        _curr_test_options_dict = {"mock_key": "mock_value", "password": "mock password"}
        _curr_test_options_str = json.dumps(_curr_test_options_dict)


        with patch('exabox.ovm.cludiskgroups.ebCluManageDiskgroup.mGetConstantsObj', return_value=_mock_constant_obj),\
             patch('exabox.ovm.cludiskgroups.ebCluManageDiskgroup.mHandleDbaasapiSynchronousCall', return_value=0):
            _rc = _diskgroupobj.mClusterDgrpInfo2(_curr_test_options_dict, "mock_dgname")

        with patch('exabox.ovm.cludiskgroups.ebCluManageDiskgroup.mGetConstantsObj', return_value=_mock_constant_obj),\
             patch('exabox.ovm.cludiskgroups.ebCluManageDiskgroup.mHandleDbaasapiSynchronousCall', return_value=0):
            _rc = _diskgroupobj.mClusterDgrpInfo2(_curr_test_options_str, "mock_dgname")

        ebLogInfo("Unit test on ebCluManageDiskgroup.mClusterDgrpInfo2 succeeded.")


if __name__ == '__main__':
    unittest.main()


