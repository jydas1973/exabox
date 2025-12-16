#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/proxy/tests_ECAgentOperationUpdate.py /main/4 2024/04/04 14:33:50 prsshukl Exp $
#
# tests_ECAgentOperationUpdate.py
#
# Copyright (c) 2021, 2024, Oracle and/or its affiliates.
#
#    NAME
#      tests_ECAgentOperationUpdate.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    prsshukl    04/04/24 - Bug 36480365 - Commenting the unittest
#    ndesanto    11/24/21 - Fixing setup to call agent setup
#    aypaul      08/19/21 - Creation
#
import json
import unittest
from exabox.log.LogMgr import ebLogInfo
import warnings
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.proxy.ECAgentOperationUpdate import fetch_update_ecregistrationinfo
from exabox.core.DBStore import ebGetDefaultDB
from ast import literal_eval
import uuid

class testOptions(object): pass

class ebTestECAgentOperationUpdate(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestECAgentOperationUpdate, self).setUpClass(aGenerateDatabase=True, aUseAgent=True)
        warnings.filterwarnings("ignore")

    def test_listECAgentDetails(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on class fetch_update_ecregistrationinfo.list.")
        myOptions = testOptions()
        myOptions.eccontrol = 'list'
        myOptions.short = False

        mysqlDB = ebGetDefaultDB()
        mysqlDB.mCreateExacloudInstanceTable()
        #No data in Table test
        fetch_update_ecregistrationinfo(myOptions)

        #Data in table test
        mysqlDB.mInsertExacloudInstanceInfo("slc18qpm.us.oracle.com", "7080", "21.220", "YWxhZGRpbjpvcGVuc2VzYW1l", "GENERIC", "210511")
        fetch_update_ecregistrationinfo(myOptions)

    def test_updateECAgentDetails(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on class fetch_update_ecregistrationinfo.update.")
        myOptions = testOptions()
        myOptions.eccontrol = 'update'
        myOptions.short = False
        myOptions.unittest = True
        mysqlDB = ebGetDefaultDB()
        mysqlDB.mCreateExacloudInstanceTable()
        mysqlDB.mInsertExacloudInstanceInfo("slc18qpm.us.oracle.com", "7080", "21.220", "YWxhZGRpbjpvcGVuc2VzYW1l", "GENERIC", "210511")

        #Missing option information test
        myOptions.eccontrolkeyval = False
        fetch_update_ecregistrationinfo(myOptions)

        #Invalid ecccontrol value: slc18qpm.us.oracle.com:7080
        myOptions.eccontrolkeyval = "slc18qpm.us.oracle.com:7080"
        fetch_update_ecregistrationinfo(myOptions)

        #ecccontrol value: slc18qpm.us.oracle.com:7080=thisKey-thisValue
        myOptions.eccontrolkeyval = "slc18qpm.us.oracle.com:7080=thisKey-thisValue"
        fetch_update_ecregistrationinfo(myOptions)

    def test_InvalidECAgentDetails(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on class fetch_update_ecregistrationinfo.invalid.")
        myOptions = testOptions()
        myOptions.eccontrol = 'invalid'

        fetch_update_ecregistrationinfo(myOptions)

if __name__ == "__main__":
    pass
    # unittest.main()