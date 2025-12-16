#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_io_resource_manager.py /main/9 2025/02/20 06:36:55 aypaul Exp $
#
# test_io_resource_manager.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      test_io_resource_manager.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      02/19/25 - Update unit tests for pmemcachesize fetch.
#    joysjose    10/04/24 - Bug 37113297 Add pmemcache check
#    joysjose    08/01/24 - ER 36727567 Add support for IORM resetclusterplan
#    jfsaldan    12/20/21 - Creation

import unittest
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo
from exabox.core.MockCommand import exaMockCommand
from exabox.ovm.cluresmgr import ebCluResManager
from unittest.mock import patch, MagicMock, PropertyMock, mock_open


class ebTestIOResourceManager(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()

    def test_invalid_operation(self):
        """
        Test None operation
        """

        # Declare variables
        _ebox = self.mGetClubox()
        _options = self.mGetPayload()

        # 825 is return code for invalid operations
        _expected_return = self.get_error_code(825)

        # Prepare test variables, objects
        _options.resmanage = None #set invalid operation
        _iormobj = ebCluResManager(_ebox, _options)

        # Execute test
        s = _iormobj.mClusterIorm(_options)

        # Compare results
        self.assertEqual(s, _expected_return)

    def test_mClusterDbListFromDomU_no_errors(self):
        """
        Method to test mClusterDbListFromDomU execution
        """

        # Prepare cmds
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand(
                        "cat /var/opt/oracle/creg/grid/grid.ini |grep.*",
                        aStdout="/u01/app/19.0.0.0/grid",
                        aRc=0),
                ],
                [
                    exaMockCommand(
                        "/u01/app/19.0.0.0/grid/bin/srvctl config database",
                        aStdout="db190203_uniq\ndb190253_uniq\n"),
                ]
            ],
            self.mGetRegexLocal():[
                [
                    exaMockCommand("ping -c 1 scaqab10adm01nat08.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10adm02nat08.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10adm01nat08.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10adm02nat08.us.oracle.com",
                        aRc=0),
                ],
                [
                    exaMockCommand("ping -c 1 scaqab10adm01nat08.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10adm02nat08.us.oracle.com",
                        aRc=0),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Declare variables
        _ebox = self.mGetClubox()
        _options = self.mGetPayload()

        # Print output instead of storing in db
        _options.jsonmode = True

        # Prepare test variables, objects
        _options.resmanage = "dblist"
        _iormobj = ebCluResManager(_ebox, _options)

        # Execute test
        #import pdb;pdb.set_trace()
        s = _iormobj.mClusterIorm(_options)

        # Compare results
        self.assertEqual(s, 0)

    def test_mClusterDbListFromDomU_no_grid_home(self):
        """
        Method to test mClusterDbListFromDomU execution
        """

        # Prepare cmds
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand(
                        "cat /var/opt/oracle/creg/grid/grid.ini |grep.*",
                        aStdout="",
                        aRc=1),
                ],
            ],
            self.mGetRegexLocal():[
                [
                    exaMockCommand("ping -c 1 scaqab10adm01nat08.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10adm02nat08.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10adm01nat08.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10adm02nat08.us.oracle.com",
                        aRc=0),
                ],
                [
                    exaMockCommand("ping -c 1 scaqab10adm01nat08.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10adm02nat08.us.oracle.com",
                        aRc=0),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Declare variables
        _ebox = self.mGetClubox()
        _options = self.mGetPayload()

        # Print output instead of storing in db
        _options.jsonmode = True

        # Prepare test variables, objects
        _options.resmanage = "dblist"
        _iormobj = ebCluResManager(_ebox, _options)

        # Execute test
        s = _iormobj.mClusterIorm(_options)

        # Compare results
        self.assertEqual(s, 0)

    def test_mClusterFcSize_no_error(self):
        """
        Function to test mClusterFcSize
        """

        # Prepare cmds
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand(
                        "cellcli -e list flashcache detail | grep size",
                        aStdout="size:                   23.28692626953125T",
                        aRc=0),
                ],
            ],
            self.mGetRegexLocal():[
                [
                    exaMockCommand("ping -c 1 scaqab10celadm01.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10celadm02.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10celadm03.us.oracle.com",
                        aRc=0),
                ],
                [
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Declare variables
        _ebox = self.mGetClubox()
        _options = self.mGetPayload()

        # Print output instead of storing in db
        _options.jsonmode = True

        # Prepare test variables, objects
        _options.resmanage = "fcsize"
        _iormobj = ebCluResManager(_ebox, _options)

        # Execute test
        _result = _iormobj.mClusterIorm(_options)

        # Compare results
        self.assertEqual(_result, 0)

    def test_mClusterFcSize_error_no_size(self):
        """
        Function to test mClusterFcSize
        """

        # Prepare cmds
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand(
                        "cellcli -e list flashcache detail | grep size",
                        aStdout="",
                        aRc=1),
                ],
            ],
            self.mGetRegexLocal():[
                [
                    exaMockCommand("ping -c 1 scaqab10celadm01.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10celadm02.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10celadm03.us.oracle.com",
                        aRc=0),
                ],
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Declare variables
        _ebox = self.mGetClubox()
        _options = self.mGetPayload()

        # Print output instead of storing in db
        _options.jsonmode = True

        # Prepare test variables, objects
        _options.resmanage = "fcsize"
        _iormobj = ebCluResManager(_ebox, _options)

        # Execute test
        _result = _iormobj.mClusterIorm(_options)

        # 806 is return code for invalid operations
        _expected_return = self.get_error_code(807)

        # Compare results
        self.assertEqual(_result, _expected_return)

    def test_mClusterGetObjective_no_error(self):
        """
        Function to test mClusterGetObjective
        """

        # Prepare cmds
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand(
                        "cellcli -e list iormplan detail |grep objective",
                        aStdout="         objective:              auto\n",
                        aRc=0),
                ],
            ],
            self.mGetRegexLocal():[
                [
                    exaMockCommand("ping -c 1 scaqab10celadm01.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10celadm02.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10celadm03.us.oracle.com",
                        aRc=0),
                ],
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Declare variables
        _ebox = self.mGetClubox()
        _options = self.mGetPayload()

        # Print output instead of storing in db
        _options.jsonmode = True

        # Prepare test variables, objects
        _options.resmanage = "getobj"
        _iormobj = ebCluResManager(_ebox, _options)

        # Execute test
        _result = _iormobj.mClusterIorm(_options)

        # Compare results
        self.assertEqual(_result, 0)

    def test_mClusterGetObjective_no_objective(self):
        """
        Function to test mClusterGetObjective
        """

        # Prepare cmds
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand(
                        "cellcli -e list iormplan detail |grep objective",
                        aStdout="",
                        aRc=1),
                ],
            ],
            self.mGetRegexLocal():[
                [
                    exaMockCommand("ping -c 1 scaqab10celadm01.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10celadm02.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10celadm03.us.oracle.com",
                        aRc=0),
                ],
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Declare variables
        _ebox = self.mGetClubox()
        _options = self.mGetPayload()

        # Print output instead of storing in db
        _options.jsonmode = True

        # 812 is return code for invalid operations
        _expected_return = self.get_error_code(812)

        # Prepare test variables, objects
        _options.resmanage = "getobj"
        _iormobj = ebCluResManager(_ebox, _options)

        # Execute test
        _result = _iormobj.mClusterIorm(_options)

        # Compare results
        self.assertEqual(_result, _expected_return)


    def tests_mClusterGetDbPlan(self, aDBPlan="", aExaBM=False):
        """
        Function to test mClusterGetDbPlan
        """

        # Prepare cmds
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("cellcli -e list iormplan detail",
                        aStdout=(
                    "name:                   scaqab10celadm01_IORMPLAN\n"
                    "catPlan:                   \n"
                    f"dbPlan:                {aDBPlan}\n"
                    "clusterPlan:               \n"
                    "objective:              auto\n"
                    "status:                 active"),
                        aRc=0),
                ],
            ],
            self.mGetRegexLocal():[
                [
                    exaMockCommand("ping -c 1 scaqab10celadm01.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10celadm02.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10celadm03.us.oracle.com",
                        aRc=0),
                ],
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Declare variables
        _ebox = self.mGetClubox()
        _options = self.mGetPayload()

        # Print output instead of storing in db
        _options.jsonmode = True

        # Prepare test variables, objects
        _ebox.mSetExabm(aExaBM)
        _options.resmanage = "getdbplan"
        _iormobj = ebCluResManager(_ebox, _options)

        # Execute test
        _result = _iormobj.mClusterIorm(_options)

        # Compare results
        self.assertEqual(_result, 0)

    def test_mClusterGetDbPlan_no_dbplan(self):
        self.tests_mClusterGetDbPlan()

    def test_mClusterGetDbPlan_dbplan(self):
        self.tests_mClusterGetDbPlan(
            "name=scaqab10celadm01_DBPLAN,flashcachelimit=65420G",
            True
        )

    def test_mClusterGetDbPlan_dbplan_no_flashcahce(self):
        self.tests_mClusterGetDbPlan("name=scaqab10celadm01_DBPLAN", True)

    def get_error_code(self, aErrorCode: int) -> str:
        """
        This helper function receives an integer and returns the equivalent
        error code used by cluresmgr.py module

        The formula to calculate this error code is:"
        _rc = (-1<<16) | int("0x" + str(aErrorCode), 16)

        Currently cluresmgr.py module returns Error messages this way
        """

        return (-1<<16) | int("0x" + str(aErrorCode), 16)
    
    def tests_mClusterSetDbPlan_reset(self, aDBPlan="", aExaBM=False):
        """
        Function to test mClusterSetDbPlan
        """

        # Prepare cmds
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("cellcli -e 'alter iormplan dbPlan=\"\"'",
                        aStdout="",
                        aRc=0),
                    exaMockCommand("cellcli -e alter iormplan objective='auto'",
                        aStdout="",
                        aRc=0),
                    exaMockCommand("cellcli -e list iormplan detail", aStdout="",aRc=0)
                ],
            ],
            self.mGetRegexLocal():[
                [
                    exaMockCommand("ping -c 1 scaqab10celadm01.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10celadm02.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10celadm03.us.oracle.com",
                        aRc=0),
                ],
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Declare variables
        _ebox = self.mGetClubox()
        _options = self.mGetPayload()

        # Print output instead of storing in db
        _options.jsonmode = True

        # Prepare test variables, objects
        _ebox.mSetExabm(aExaBM)
        _options.resmanage = "resetdbplan"
        _iormobj = ebCluResManager(_ebox, _options)

        # Execute test
        _result = _iormobj.mClusterIorm(_options)

        # Compare results
        self.assertEqual(_result, 0)
    def tests_mClusterSetDbPlan_no_json(self, aDBPlan="", aExaBM=False):
        """
        Function to test mClusterSetDbPlan
        """

        # Prepare cmds
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("cellcli -e 'alter iormplan dbPlan=\"((name=db3, share=1, flashCacheLimit=10G),(name=db4, share=2, flashCacheLimit=20G)\"'",
                        aStdout="",
                        aRc=0),
                    exaMockCommand("cellcli -e alter iormplan objective='auto'",
                        aStdout="",
                        aRc=0),
                ],
            ],
            self.mGetRegexLocal():[
                [
                    exaMockCommand("ping -c 1 scaqab10celadm01.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10celadm02.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10celadm03.us.oracle.com",
                        aRc=0),
                ],
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Declare variables
        _ebox = self.mGetClubox()
        _options = self.mGetPayload()

        # Print output instead of storing in db
        _options.jsonmode = True

        # Prepare test variables, objects
        _ebox.mSetExabm(aExaBM)
        _options.resmanage = "setdbplan"
        _iormobj = ebCluResManager(_ebox, _options)

        # Execute test
        _result = _iormobj.mClusterIorm(_options)

        # Compare results
        
        # 808 is return code for no json file
        _expected_return = self.get_error_code(808)

        # Compare results
        self.assertEqual(_result, _expected_return)
    def tests_mClusterSetDbPlan_fclimit_issue(self, aDBPlan="", aExaBM=False):
        """
        Function to test mClusterSetDbPlan
        """

        # Prepare cmds
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("cellcli -e 'alter iormplan dbPlan=\"((name=db3, share=1, flashCacheLimit=10G),(name=db4, share=2, flashCacheLimit=20G))\"'",
                        aStdout="",
                        aRc=0),
                    exaMockCommand("cellcli -e alter iormplan objective='auto'",
                        aStdout="",
                        aRc=0),
                    exaMockCommand("cellcli -e list pmemcache detail",
                        aStdout="name: sea201732exdcl06_XRMEMCACHE",
                        aRc=0),
                    exaMockCommand("cellcli -e list iormplan detail",
                        aStdout="",
                        aRc=0),
                    exaMockCommand("cellcli -e list flashcache detail | grep size",
                        aStdout="",
                        aRc=1),
                ],
            ],
            self.mGetRegexLocal():[
                [
                    exaMockCommand("ping -c 1 scaqab10celadm01.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10celadm02.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10celadm03.us.oracle.com",
                        aRc=0),
                ],
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Declare variables
        _ebox = self.mGetClubox()
        _options = self.mGetPayload()
        _options.jsonconf ={"dbPlan" : [{ "dbname" : "db1", "share" : "2", "flashcachelimit":"25G"},{ "dbname" : "db3", "share" : "1", "flashcachelimit":"10G"}]}

        # Print output instead of storing in db
        _options.jsonmode = True

        # Prepare test variables, objects
        _ebox.mSetExabm(aExaBM)
        _options.resmanage = "setdbplan"
        _iormobj = ebCluResManager(_ebox, _options)
        _expected_return = self.get_error_code(807)
        # Execute test
        with patch('exabox.ovm.cluresmgr.ebCluResManager.mGetDBPlanList', return_value=([],None, False)):
            _result = _iormobj.mClusterIorm(_options)
            
        # Compare results
        self.assertEqual(_result, _expected_return)
    
    def tests_mGetClusterPlan(self, aDBPlan="", aExaBM=False):
        """
        Function to test mClusterSetDbPlan
        """

        # Prepare cmds
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("cellcli -e list iormplan detail",
                        aStdout="",
                        aRc=0),
                ],
            ],
            self.mGetRegexLocal():[
                [
                    exaMockCommand("ping -c 1 scaqab10celadm01.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10celadm02.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10celadm03.us.oracle.com",
                        aRc=0),
                ],
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Declare variables
        _ebox = self.mGetClubox()
        _options = self.mGetPayload()
        _options.jsonconf ={}

        # Print output instead of storing in db
        _options.jsonmode = True

        # Prepare test variables, objects
        _ebox.mSetExabm(aExaBM)
        _options.resmanage = "getclusterplan"
        _iormobj = ebCluResManager(_ebox, _options)
        # Execute test
        _result = _iormobj.mClusterIorm(_options)
            
        # Compare results
        self.assertEqual(_result, 0)
    def tests_mSetClusterPlan_exabm_false_payload_issue(self, aDBPlan="", aExaBM=False):
        """
        Function to test mClusterSetDbPlan
        """

        # Prepare cmds
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("cellcli -e 'alter iormplan clusterplan=((name=asmclu1, share=4), (name=asmclu2, share=2))'",
                        aStdout="",
                        aRc=0),
                ],
            ],
            self.mGetRegexLocal():[
                [
                    exaMockCommand("ping -c 1 scaqab10celadm01.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10celadm02.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10celadm03.us.oracle.com",
                        aRc=0),
                ],
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Declare variables
        _ebox = self.mGetClubox()
        _options = self.mGetPayload()
        _options.jsonconf ={"clusterPlan":[{"exaunitId":222,"share":"4"},{"exaunitId":222,"share":"2"}]}

        # Print output instead of storing in db
        _options.jsonmode = True

        # Prepare test variables, objects
        _ebox.mSetExabm(aExaBM)
        _options.resmanage = "setclusterplan"
        _iormobj = ebCluResManager(_ebox, _options)
        _expected_return = self.get_error_code(830)
        # Execute test
        _result = _iormobj.mClusterIorm(_options)
            
        # Compare results
        self.assertEqual(_result, _expected_return)
        
        
    def tests_mSetClusterPlan_exabm_false_payload_issue_name(self, aDBPlan="", aExaBM=False):
        """
        Function to test mClusterSetDbPlan
        """

        # Prepare cmds
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("cellcli -e 'alter iormplan clusterplan=((name=asmclu1, share=4), (name=asmclu2, share=2))'",
                        aStdout="",
                        aRc=0),
                    exaMockCommand("cellcli -e list iormplan detail",
                        aStdout="",
                        aRc=0),
                ],
            ],
            self.mGetRegexLocal():[
                [
                    exaMockCommand("ping -c 1 scaqab10celadm01.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10celadm02.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10celadm03.us.oracle.com",
                        aRc=0),
                ],
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Declare variables
        _ebox = self.mGetClubox()
        _options = self.mGetPayload()
        _options.jsonconf ={"ClusterPlan":[{"nam":"asmclu1","share":"4"},{"name":"asmclu2","share":"2"}]}

        # Print output instead of storing in db
        _options.jsonmode = True

        # Prepare test variables, objects
        _ebox.mSetExabm(aExaBM)
        _options.resmanage = "setclusterplan"
        _iormobj = ebCluResManager(_ebox, _options)
        _expected_return = self.get_error_code(831)
        # Execute test
        _result = _iormobj.mClusterIorm(_options)
            
        # Compare results
        self.assertEqual(_result, _expected_return)
        
        
    def tests_mSetClusterPlan_reset(self, aDBPlan="", aExaBM=False):
        """
        Function to test command resetclusterplan
        """

        # Prepare cmds
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("cellcli -e 'alter iormplan clusterplan=\"\"'",
                        aStdout="",
                        aRc=0)
                ],
            ],
            self.mGetRegexLocal():[
                [
                    exaMockCommand("ping -c 1 scaqab10celadm01.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10celadm02.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10celadm03.us.oracle.com",
                        aRc=0),
                ],
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Declare variables
        _ebox = self.mGetClubox()
        _options = self.mGetPayload()
        _options.jsonmode = True

        # Prepare test variables, objects
        _ebox.mSetExabm(aExaBM)
        _options.resmanage = "resetclusterplan"
        _iormobj = ebCluResManager(_ebox, _options)
        _iormobj.mClusterIorm(_options)
            
        
    def tests_mGetData_SetData(self):
        """
        Function to test mClusterSetDbPlan
        """

        # Prepare cmds
        _cmds = {
            self.mGetRegexCell(): [
                [
                    
                ],
            ],
            self.mGetRegexLocal():[
                [
                    exaMockCommand("ping -c 1 scaqab10celadm01.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10celadm02.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10celadm03.us.oracle.com",
                        aRc=0),
                ],
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Declare variables
        _ebox = self.mGetClubox()
        _options = self.mGetPayload()

        # Print output instead of storing in db
        _options.jsonmode = True

        # Prepare test variables, objects
        _iormobj = ebCluResManager(_ebox, _options)
        # Execute test
        aData = {'Status': 'Pass', 'Command': 'getdbplan', 'ErrorCode': '0', 'Log': 'Common IORM DB Plan found across cells', 'dbPlan': [{'limit': '2', 'share': '3', 'flashcachelimit': '25G', 'flashcachemin': '10G', 'asmcluster': 'myclu1', 'xrmemcachemin': '12G', 'xrmemcachesize': '20G', 'dbname': 'db3'}, {'limit': '2', 'share': '5', 'flashcachemin': '2G', 'flashcachesize': '10G', 'asmcluster': 'myclu1', 'xrmemcachelimit': '20G', 'xrmemcachemin': '10G', 'dbname': 'db1'}, {'limit': '10', 'share': '1', 'flashcachelimit': '30G', 'flashcachemin': '8G', 'asmcluster': 'myclu1', 'xrmemcachemin': '5G', 'xrmemcachesize': '25G', 'dbname': 'db2'}], 'cell': ['scaqab10celadm01.us.oracle.com', 'scaqab10celadm02.us.oracle.com', 'scaqab10celadm03.us.oracle.com']}
        _result = _iormobj.mSetData(aData)
        _result = _iormobj.mGetData()
        print(_result)
    
    def tests_mUnSupported(self, aDBPlan="", aExaBM=False):
        """
        Function to test mClusterSetDbPlan
        """

        # Prepare cmds
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("cellcli -e 'alter iormplan dbPlan=\"((name=db3, share=1, flashCacheLimit=10G),(name=db4, share=2, flashCacheLimit=20G))\"'",
                        aStdout="",
                        aRc=0),
                    exaMockCommand("cellcli -e alter iormplan objective='auto'",
                        aStdout="",
                        aRc=0),
                    exaMockCommand("cellcli -e list pmemcache detail",
                        aStdout="",
                        aRc=0),
                    exaMockCommand("cellcli -e list iormplan detail",
                        aStdout="",
                        aRc=0),
                    exaMockCommand("cellcli -e list flashcache detail | grep size",
                        aStdout="",
                        aRc=1),
                ],
            ],
            self.mGetRegexLocal():[
                [
                    exaMockCommand("ping -c 1 scaqab10celadm01.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10celadm02.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10celadm03.us.oracle.com",
                        aRc=0),
                ],
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Declare variables
        _ebox = self.mGetClubox()
        _options = self.mGetPayload()
        _options.jsonconf ={"dbPlan" : [{ "dbname" : "db1", "share" : "2", "flashcachelimit":"25G"},{ "dbname" : "db3", "share" : "1", "flashcachelimit":"10G"}]}

        # Print output instead of storing in db
        _options.jsonmode = True

        # Prepare test variables, objects
        _ebox.mSetExabm(aExaBM)
        _options.resmanage = "setdbpla"
        _iormobj = ebCluResManager(_ebox, _options)
        _expected_return = self.get_error_code(851)
        # Execute test
        _result = _iormobj.mClusterIorm(_options)
            
        # Compare results
        self.assertEqual(_result, _expected_return)
        
        
    def tests_mSetClusterPlan_exabm_false(self, aDBPlan="", aExaBM=False):
        """
        Function to test mClusterSetDbPlan
        """

        # Prepare cmds
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("cellcli -e list pmemcache detail | grep effectiveCacheSize",
                        aStdout="",
                        aRc=0),
                    exaMockCommand("cellcli -e list pmemcache detail",
                        aStdout="",
                        aRc=0),
                    exaMockCommand("cellcli -e list iormplan detail",
                        aStdout="",
                        aRc=0),
                ],
            ],
            self.mGetRegexLocal():[
                [
                    exaMockCommand("ping -c 1 scaqab10celadm01.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10celadm02.us.oracle.com",
                        aRc=0),
                    exaMockCommand("ping -c 1 scaqab10celadm03.us.oracle.com",
                        aRc=0),
                ],
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Declare variables
        _ebox = self.mGetClubox()
        _options = self.mGetPayload()
        _options.jsonconf ={"ClusterPlan":[{"name":"asmclu1","share":"4"},{"name":"asmclu2","share":"2"}]}

        # Print output instead of storing in db
        _options.jsonmode = True

        # Prepare test variables, objects
        _ebox.mSetExabm(aExaBM)
        _options.resmanage = "pmemcsize"
        _iormobj = ebCluResManager(_ebox, _options)
        # Execute test
        _result = _iormobj.mClusterIorm(_options)

if __name__ == '__main__':
    unittest.main()
