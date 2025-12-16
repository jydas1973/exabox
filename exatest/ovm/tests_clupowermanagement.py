#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_clupowermanagement.py /main/1 2025/11/21 16:11:42 abysebas Exp $
#
# tests_clupowermanagement.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_clupowermanagement.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    abysebas    11/13/25 - Enh 38299823 - PHASE 1: CPU CORE POWER SAVING -
#                           EXACLOUD CHANGES
#    abysebas    11/13/25 - Creation
#
import json
import unittest
import re
import copy
import os
import io
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo
from exabox.ovm.clumisc import ebCluPreChecks,ebCluSshSetup,OracleVersion,ebCluStorageReshapePrecheck,ebCluStartStopHostFromIlom, ebCluNodeSubsetPrecheck, ebCluRestartVmExacsService, ebCluFaultInjection, ebMigrateUsersUtil, mGetGridListSupportedByOeda, ebCluCellSanityTests
from exabox.ovm.monitor import ebClusterNode
import warnings
from unittest.mock import patch, Mock, mock_open
from exabox.core.Error import ExacloudRuntimeError
from exabox.utils.node import  connect_to_host
from exabox.ovm.adbs_elastic_service import mCreateADBSSiteGroupConfig
from exabox.ovm.clumisc import mWaitForSystemBoot, ebMiscFx, mGetAlertHistoryOptions, ebADBSUtil
from exabox.ovm.kvmvmmgr import ebKvmVmMgr
from exabox.agent.ebJobRequest import ebJobRequest

JSON_ILOM_START = {
    "operation": "start",
    "parallel_process": False,
    "host_ilom_pair": {
        "iad103716exdd013.iad103716exd.adminiad1.oraclevcn.com": "iad103716exdd013lo.iad103716exd.adminiad1.oraclevcn.com",
        "iad103712exdcl07.iad103712exd.adminiad1.oraclevcn.com": "iad103712exdcl07lo.iad103712exd.adminiad1.oraclevcn.com"
    }
}

JSON_ILOM_STOP = {
    "operation": "stop",
    "parallel_process": True,
    "host_ilom_pair": {
        "iad103716exdd013.iad103716exd.adminiad1.oraclevcn.com": "iad103716exdd013lo.iad103716exd.adminiad1.oraclevcn.com",
        "iad103712exdcl07.iad103712exd.adminiad1.oraclevcn.com": "iad103712exdcl07lo.iad103712exd.adminiad1.oraclevcn.com"
    }
}

JSON_ILOM_INVALID_OPERATION = {
    "operation": "wait",  # invalid operation
    "parallel_process": True,
    "host_ilom_pair": {
        "iad103716exdd013.iad103716exd.adminiad1.oraclevcn.com": "iad103716exdd013lo.iad103716exd.adminiad1.oraclevcn.com"
    }
}

JSON_ILOM_MISSING_OPERATION = {
    "parallel_process": True,
    "host_ilom_pair": {
        "iad103716exdd013.iad103716exd.adminiad1.oraclevcn.com": "iad103716exdd013lo.iad103716exd.adminiad1.oraclevcn.com"
    }
}

JSON_ILOM_MISSING_HOST_PAIR = {
    "operation": "start",
    "parallel_process": True
}

JSON_LOWPOWER_VALID = {
    "operation": "lowpowermode",
    "parallel_process": False,
    "host_ilom_pair": {
        "iad103716exdd013.iad103716exd.adminiad1.oraclevcn.com": "iad103716exdd013lo.iad103716exd.adminiad1.oraclevcn.com"
    },
    "lowpoweroperation": "schedule",
    "lowPowerModeSchedule": [
        {
            "startTimestamp": "2025-01-03T18:00:00-07:00",
            "durationMinutes": 720,
            "frequency": "daily"
        }
    ],
    "lowPowerModeUntil": "2025-01-10T23:30:00-07:00"
}

JSON_LOWPOWER_INVALID_OP = {
    "operation": "lowpowermode",
    "parallel_process": True,
    "host_ilom_pair": {
        "iad103716exdd013.iad103716exd.adminiad1.oraclevcn.com": "iad103716exdd013lo.iad103716exd.adminiad1.oraclevcn.com"
    },
    "lowpoweroperation": "pause"  # invalid
}

JSON_LOWPOWER_MISSING_SCHEDULE = {
    "operation": "lowpowermode",
    "parallel_process": False,
    "host_ilom_pair": {
        "iad103716exdd013.iad103716exd.adminiad1.oraclevcn.com": "iad103716exdd013lo.iad103716exd.adminiad1.oraclevcn.com"
    },
    "lowpoweroperation": "schedule"
}

JSON_LOWPOWER_INVALID_FREQ = {
    "operation": "lowpowermode",
    "parallel_process": False,
    "host_ilom_pair": {
        "iad103716exdd013.iad103716exd.adminiad1.oraclevcn.com": "iad103716exdd013lo.iad103716exd.adminiad1.oraclevcn.com"
    },
    "lowpoweroperation": "schedule_add",
    "lowPowerModeSchedule": [
        {
            "startTimestamp": "2025-01-03T18:00:00-07:00",
            "durationMinutes": 720,
            "frequency": "hourly"  # unsupported
        }
    ]
}

JSON_LOWPOWER_VALID = {
    "operation": "lowpowermode",
    "parallel_process": False,
    "host_ilom_pair": {
        "host1": "ilom1"
    },
    "lowpoweroperation": "schedule",
    "lowPowerModeSchedule": [
        {
            "startTimestamp": "2025-01-03T18:00:00-07:00",
            "durationMinutes": 720,
            "frequency": "daily"
        }
    ],
    "lowPowerModeUntil": "2025-01-10T23:30:00-07:00"
}

JSON_LOWPOWER_INVALID_OP = {
    "operation": "lowpowermode",
    "parallel_process": True,
    "host_ilom_pair": {
        "host1": "ilom1"
    },
    "lowpoweroperation": "pause"
}

JSON_LOWPOWER_MISSING_SCHEDULE = {
    "operation": "lowpowermode",
    "parallel_process": False,
    "host_ilom_pair": {
        "host1": "ilom1"
    },
    "lowpoweroperation": "schedule"
}

JSON_LOWPOWER_INVALID_FREQ = {
    "operation": "lowpowermode",
    "parallel_process": False,
    "host_ilom_pair": {
        "host1": "ilom1"
    },
    "lowpoweroperation": "schedule_add",
    "lowPowerModeSchedule": [
        {
            "startTimestamp": "2025-01-03T18:00:00-07:00",
            "durationMinutes": 720,
            "frequency": "hourly"
        }
    ]
}

JSON_LOWPOWER_UNTIL_NEVER_WITH_SCHEDULE = {
    "operation": "lowpowermode",
    "parallel_process": False,
    "host_ilom_pair": {
        "host1": "ilom1"
    },
    "lowpoweroperation": "schedule",
    "lowPowerModeSchedule": [
        {
            "startTimestamp": "2025-01-03T18:00:00-07:00",
            "durationMinutes": 720,
            "frequency": "daily"
        }
    ],
    "lowPowerModeUntil": "NEVER"
}

JSON_LOWPOWER_UNTIL_NULL = {
    "operation": "lowpowermode",
    "parallel_process": False,
    "host_ilom_pair": {
        "host1": "ilom1"
    },
    "lowpoweroperation": "schedule_clear",
    "lowPowerModeUntil": "NULL"
}

JSON_LOWPOWER_SCHEDULE_CLEAR_WITH_ENTRIES = {
    "operation": "lowpowermode",
    "parallel_process": False,
    "host_ilom_pair": {
        "host1": "ilom1"
    },
    "lowpoweroperation": "schedule_clear",
    "lowPowerModeSchedule": [
        {
            "startTimestamp": "2025-01-03T18:00:00-07:00",
            "durationMinutes": 720,
            "frequency": "daily"
        }
    ]
}

JSON_LOWPOWER_GET_ALL = {
    "operation": "lowpowermode",
    "parallel_process": False,
    "host_ilom_pair": {
        "host1": "ilom1"
    },
    "lowpoweroperation": "get_all"
}

JSON_LOWPOWER_EMPTY_SCHEDULE = {
    "operation": "lowpowermode",
    "parallel_process": False,
    "host_ilom_pair": {
        "host1": "ilom1"
    },
    "lowpoweroperation": "schedule",
    "lowPowerModeSchedule": []
}

JSON_LOWPOWER_SCHEDULE_MISSING_KEYS = {
    "operation": "lowpowermode",
    "parallel_process": False,
    "host_ilom_pair": {
        "host1": "ilom1"
    },
    "lowpoweroperation": "schedule",
    "lowPowerModeSchedule": [
        {
            "startTimestamp": "2025-01-03T18:00:00-07:00"
        }
    ]
}

JSON_LOWPOWER_MISSING_HOST_PAIR = {
    "operation": "lowpowermode",
    "parallel_process": True,
    "lowpoweroperation": "schedule"
}

JSON_LOWPOWER_MISSING_OPERATION = {
    "operation": "lowpowermode",
    "parallel_process": True,
    "host_ilom_pair": {
        "host1": "ilom1"
    }
}

JSON_LOWPOWER_UNTIL_EMPTY = {
    "operation": "lowpowermode",
    "parallel_process": False,
    "host_ilom_pair": {
        "host1": "ilom1"
    },
    "lowpoweroperation": "schedule_clear",
    "lowPowerModeUntil": ""
}

def mRemoteExecute(aCmd):
    return "critical HW Alert"

class mMockPrecheck:
    def __init__(self, aCluCtrl):
        self.__cluctrl = aCluCtrl

    def mGetEbox(self):
        return self.__cluctrl

class ebTestClupowermanagement(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestClupowermanagement, self).setUpClass(True, True)
        warnings.filterwarnings("ignore")

            
    def test_mHandlerStopStartHostViaIlom_start(self):
        _cmds = {
            self.mGetRegexLocal(): [
                [exaMockCommand("/bin/ping *", aRc=1, aStdout="", aPersist=True)]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_ILOM_START
        ebLogInfo("Running unit test on exaBoxCluCtrl.mHandlerStopStartHostViaIlom with valid start payload")
        with patch('exabox.ovm.clucontrol.exaBoxNode.mConnectAuthInteractive'), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mExecuteCmdsAuthInteractive"):
            self.assertEqual(_ebox_local.mHandlerStopStartHostViaIlom(), None)

    def test_mHandlerStopStartHostViaIlom_stop(self):
        _cmds = {
            self.mGetRegexLocal(): [
                [exaMockCommand("/bin/ping *", aRc=1, aStdout="", aPersist=True)]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_ILOM_STOP
        ebLogInfo("Running unit test on exaBoxCluCtrl.mHandlerStopStartHostViaIlom with valid stop payload")
        with patch('exabox.ovm.clucontrol.exaBoxNode.mConnectAuthInteractive'), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mExecuteCmdsAuthInteractive"):
            self.assertEqual(_ebox_local.mHandlerStopStartHostViaIlom(), None)

    def test_mHandlerStopStartHostViaIlom_invalid_operation(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_ILOM_INVALID_OPERATION
        ebLogInfo("Running unit test on exaBoxCluCtrl.mHandlerStopStartHostViaIlom with invalid operation")
        with patch('exabox.ovm.clucontrol.exaBoxNode.mConnectAuthInteractive'), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mExecuteCmdsAuthInteractive"):
            self.assertRaises(ExacloudRuntimeError, _ebox_local.mHandlerStopStartHostViaIlom)

    def test_mHandlerStopStartHostViaIlom_missing_operation(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_ILOM_MISSING_OPERATION
        ebLogInfo("Running unit test on exaBoxCluCtrl.mHandlerStopStartHostViaIlom with missing operation")
        with patch('exabox.ovm.clucontrol.exaBoxNode.mConnectAuthInteractive'), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mExecuteCmdsAuthInteractive"):
            self.assertRaises(ExacloudRuntimeError, _ebox_local.mHandlerStopStartHostViaIlom)

    def test_mHandlerStopStartHostViaIlom_missing_host_ilom_pair(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_ILOM_MISSING_HOST_PAIR
        ebLogInfo("Running unit test on exaBoxCluCtrl.mHandlerStopStartHostViaIlom with missing host_ilom_pair")
        with patch('exabox.ovm.clucontrol.exaBoxNode.mConnectAuthInteractive'), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mExecuteCmdsAuthInteractive"):
            self.assertRaises(ExacloudRuntimeError, _ebox_local.mHandlerStopStartHostViaIlom)

    def test_mHandlerStopStartHostViaIlom_lowpowermode_valid(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_LOWPOWER_VALID
        ebLogInfo("Running unit test on mHandlerStopStartHostViaIlom with valid lowpowermode payload")
        with patch('exabox.ovm.clucontrol.exaBoxNode.mConnectAuthInteractive'), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mExecuteCmdsAuthInteractive"):
            self.assertEqual(_ebox_local.mHandlerStopStartHostViaIlom(), None)

    def test_mHandlerStopStartHostViaIlom_lowpowermode_invalid_operation(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_LOWPOWER_INVALID_OP
        ebLogInfo("Running unit test on mHandlerStopStartHostViaIlom with invalid lowpoweroperation")
        with patch('exabox.ovm.clucontrol.exaBoxNode.mConnectAuthInteractive'), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mExecuteCmdsAuthInteractive"):
            self.assertRaises(ExacloudRuntimeError, _ebox_local.mHandlerStopStartHostViaIlom)

    def test_mHandlerStopStartHostViaIlom_lowpowermode_missing_schedule(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_LOWPOWER_MISSING_SCHEDULE
        ebLogInfo("Running unit test on mHandlerStopStartHostViaIlom with missing schedule for schedule operation")
        with patch('exabox.ovm.clucontrol.exaBoxNode.mConnectAuthInteractive'), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mExecuteCmdsAuthInteractive"):
            self.assertRaises(ExacloudRuntimeError, _ebox_local.mHandlerStopStartHostViaIlom)

    def test_mHandlerStopStartHostViaIlom_lowpowermode_invalid_frequency(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_LOWPOWER_INVALID_FREQ
        ebLogInfo("Running unit test on mHandlerStopStartHostViaIlom with invalid frequency in schedule")
        with patch('exabox.ovm.clucontrol.exaBoxNode.mConnectAuthInteractive'), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mExecuteCmdsAuthInteractive"):
            self.assertRaises(ExacloudRuntimeError, _ebox_local.mHandlerStopStartHostViaIlom)

    def test_mHandlerStopStartHostViaIlom_lowpowermode_valid(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_LOWPOWER_VALID
        with patch('exabox.ovm.clucontrol.exaBoxNode.mConnect'), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mExecuteCmd", return_value=(None, ["OK"], None)), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mGetCmdExitStatus", return_value=0), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mDisconnect"):
            self.assertEqual(_ebox_local.mHandlerStopStartHostViaIlom(), None)

    def test_mHandlerStopStartHostViaIlom_lowpowermode_invalid_operation(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_LOWPOWER_INVALID_OP
        with self.assertRaises(ExacloudRuntimeError):
            _ebox_local.mHandlerStopStartHostViaIlom()

    def test_mHandlerStopStartHostViaIlom_lowpowermode_missing_schedule(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_LOWPOWER_MISSING_SCHEDULE
        with self.assertRaises(ExacloudRuntimeError):
            _ebox_local.mHandlerStopStartHostViaIlom()

    def test_mHandlerStopStartHostViaIlom_lowpowermode_invalid_frequency(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_LOWPOWER_INVALID_FREQ
        with self.assertRaises(ExacloudRuntimeError):
            _ebox_local.mHandlerStopStartHostViaIlom()

    def test_mHandlerStopStartHostViaIlom_lowpowermode_until_never_with_schedule(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_LOWPOWER_UNTIL_NEVER_WITH_SCHEDULE
        with self.assertRaises(ExacloudRuntimeError):
            _ebox_local.mHandlerStopStartHostViaIlom()

    def test_mHandlerStopStartHostViaIlom_lowpowermode_until_null(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_LOWPOWER_UNTIL_NULL
        with patch('exabox.ovm.clucontrol.exaBoxNode.mConnect'), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mExecuteCmd", return_value=(None, ["Until cleared"], None)), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mGetCmdExitStatus", return_value=0), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mDisconnect"):
            self.assertEqual(_ebox_local.mHandlerStopStartHostViaIlom(), None)

    def test_mHandlerStopStartHostViaIlom_lowpowermode_schedule_clear_with_schedule(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_LOWPOWER_SCHEDULE_CLEAR_WITH_ENTRIES
        with patch('exabox.ovm.clucontrol.exaBoxNode.mConnect'), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mExecuteCmd", return_value=(None, ["Schedule cleared"], None)), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mGetCmdExitStatus", return_value=0), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mDisconnect"):
            self.assertEqual(_ebox_local.mHandlerStopStartHostViaIlom(), None)

    def test_mHandlerStopStartHostViaIlom_lowpowermode_get_all(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_LOWPOWER_GET_ALL
        with patch('exabox.ovm.clucontrol.exaBoxNode.mConnect'), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mExecuteCmd", return_value=(None, ["Schedule: OK"], None)), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mGetCmdExitStatus", return_value=0), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mDisconnect"):
            self.assertEqual(_ebox_local.mHandlerStopStartHostViaIlom(), None)

    def test_mHandlerStopStartHostViaIlom_lowpowermode_empty_schedule(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_LOWPOWER_EMPTY_SCHEDULE
        with self.assertRaises(ExacloudRuntimeError):
            _ebox_local.mHandlerStopStartHostViaIlom()

    def test_mHandlerStopStartHostViaIlom_lowpowermode_schedule_missing_keys(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_LOWPOWER_SCHEDULE_MISSING_KEYS
        with self.assertRaises(ExacloudRuntimeError):
            _ebox_local.mHandlerStopStartHostViaIlom()

    def test_mHandleLowPowerMode_missing_host_ilom_pair(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_LOWPOWER_MISSING_HOST_PAIR
        with self.assertRaises(ExacloudRuntimeError):
            _ebox_local.mHandlerStopStartHostViaIlom()

    def test_mHandleLowPowerMode_missing_lowpoweroperation(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_LOWPOWER_MISSING_OPERATION
        with patch('exabox.ovm.clucontrol.exaBoxNode.mConnect'), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mExecuteCmd", return_value=(None, ["OK"], None)), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mGetCmdExitStatus", return_value=0), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mDisconnect"):
            self.assertEqual(_ebox_local.mHandlerStopStartHostViaIlom(), None)

    def test_mHandleLowPowerMode_until_empty_string(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_LOWPOWER_UNTIL_EMPTY
        with patch('exabox.ovm.clucontrol.exaBoxNode.mConnect'), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mExecuteCmd", return_value=(None, ["Until cleared"], None)), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mGetCmdExitStatus", return_value=0), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mDisconnect"):
            self.assertEqual(_ebox_local.mHandlerStopStartHostViaIlom(), None)

    def test_mProcessLowPowerMode_command_failure(self):
        payload = copy.deepcopy(JSON_LOWPOWER_VALID)
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = payload
        with patch('exabox.ovm.clucontrol.exaBoxNode.mConnect'), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mExecuteCmd", return_value=(None, [], ["Error occurred"])), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mGetCmdExitStatus", return_value=1), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mDisconnect"):
            self.assertEqual(_ebox_local.mHandlerStopStartHostViaIlom(), None)

    def test_mProcessLowPowerMode_exception(self):
        payload = copy.deepcopy(JSON_LOWPOWER_VALID)
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = payload
        with patch('exabox.ovm.clucontrol.exaBoxNode.mConnect', side_effect=Exception("Simulated failure")):
            self.assertEqual(_ebox_local.mHandlerStopStartHostViaIlom(), None)

if __name__ == "__main__":
    unittest.main()
