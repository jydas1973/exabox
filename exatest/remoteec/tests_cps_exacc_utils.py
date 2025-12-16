#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/remoteec/tests_cps_exacc_utils.py /main/7 2025/09/15 20:32:51 hgaldame Exp $
#
# test_cps_exacc_utils.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      test_cps_exacc_utils.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    hgaldame    09/11/25 - enh 38036854 - exacc gen 2| infra patching |
#                           enhance ecra remoteec command
#    hgaldame    07/20/23 - 35626691 - oci/exacc: remoteec enhancement for
#                           allow to create custom log name
#    hgaldame    06/16/23 - 35509904 - oci/exacc: fix error codes on remote
#                           manager for match with ecra error catalog
#    hgaldame    09/30/22 - 34627398 - exacc:bb:22.3.1:cps-sw upgrade: provide
#                           proper error code for precheck failure instead of
#                           returning generic error
#    hgaldame    08/14/22 - 34494690 - ociexacc: cps exacc utils unit test dif
#                           in ECS_MAIN_LINUX.x64_220813.0901
#    hgaldame    08/05/22 - 34457946 - oci/exacc: add new parameter for send
#                           tgz file on dynamic tasks remote manager endpoint
#    hgaldame    07/27/22 - 34352482 - cps sw v2 - make sure that all logs
#                           during sw upgrade goes to the same path at cps
#    hgaldame    07/26/22 - Creation
#
import os
import unittest
import uuid
import json
import socket
import io
import re
import  exabox.managment.src.utils.CpsExaccUtils as utils
import  exabox.managment.src.utils.CpsExaccError as error_fwk

import traceback

from datetime import datetime
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from unittest.mock import patch, Mock, call
from urllib.error import HTTPError
from exabox.network.HTTPSHelper import ebResponse
from time import strftime, localtime, sleep
from pathlib import Path

class ebTestRemoteManagmentCpsExaccUtils(ebTestClucontrol):

    @classmethod
    def setUpClass(cls):
        super().setUpClass(aGenerateRemoteEC=True)

    @staticmethod
    def create_dummy_log_files(root_dir, name_log_generator, num_files=3, delay_sec=1):
        _file_list = []
        for _ in range(num_files):
            _log_name = name_log_generator()
            _log_path = os.path.join(os.path.abspath(root_dir), _log_name)
            if os.path.exists(_log_path):
                os.unlink(_log_path)
            Path(_log_path).touch()
            _file_list.append(_log_path)
            sleep(delay_sec)
        return _file_list

    @staticmethod
    def cleanup_dummy_log_files(_file_list):
        for _file in _file_list:
            if os.path.exists(_file):
                os.unlink(_file)
        return

    @staticmethod
    def log_file_generator_for_cps_deployer():
        _localtime = strftime('%Y%m%d_%H%M%S', localtime())
        _log_path = 'oci_exacc_dpy_rollingupgrade_{0}.log'.format(_localtime)
        return _log_path

    @staticmethod
    def log_file_generator_for_Sanity():
        _localtime = strftime('%Y%m%d_%H%M%S', localtime())
        _log_path = 'SANITY_{0}.log'.format(_localtime)
        return _log_path

    @staticmethod
    def log_file_generator_for_cps_sw_check():
        return "cps_sw_check.log"

    def setUp(self):
        _abs_path = os.path.abspath(self.mGetPath())
        self.exacloud_path = self.mGetUtil().mGetExacloudPath()
        self.log_dir = os.path.join(self.exacloud_path, "log", "threads")
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, mode=0o777, exist_ok=True)

    def test_001_get_log_info_by_type(self):
        """
            Scenario: Get log information by log type
            Given a log type
            When the log information is required
            Then response should return the log information
        """
        for _log_type in (utils.CpsLogType.SANITY_TOOL, utils.CpsLogType.CPS_DEPLOYER, utils.CpsLogType.CPS_CHECK_TOOL):
            with self.subTest(" Retrieve log info from {0}".format(_log_type), _log_type=_log_type):
                _root_dir, _regex = utils.mGetInfoByLogType("/opt/oci/exacc", _log_type)
                self.assertIsNotNone(_root_dir)
                self.assertIsNotNone(_regex)

    def test_002_get_log_info_by_type_optional_dir(self):
        """
            Scenario: Get log information by log type
            Given a log type and optional root dir location
            When the log information is required
            Then response should return the log information
        """

        _optional_dict = {
            utils.CpsLogType.SANITY_TOOL: os.path.join(self.log_dir, "Sanity"),
            utils.CpsLogType.CPS_DEPLOYER: os.path.join(self.log_dir, "ocps-full", "deployer"),
            utils.CpsLogType.CPS_CHECK_TOOL: os.path.join(self.log_dir, "cps-sw-check"),
        }
        for _log_type in (utils.CpsLogType.SANITY_TOOL, utils.CpsLogType.CPS_DEPLOYER, utils.CpsLogType.CPS_CHECK_TOOL):
            with self.subTest(" Retrieve log info from {0}".format(_log_type), _log_type=_log_type):
                _root_dir, _regex = utils.mGetInfoByLogType("", _log_type, aOptionalDirDict=_optional_dict)
                self.assertIsNotNone(_root_dir)
                self.assertTrue(_root_dir.startswith(self.log_dir))
                self.assertIsNotNone(_regex)

    def test_003_get_invalid_log_info_by_type(self):
        """
            Scenario: Get log information by log type
            Given a log type not in catalogue
            When the log information is required
            Then response should return None
        """
        _root_dir, _regex = utils.mGetInfoByLogType("/opt/oci/exacc", "invalidlog")
        self.assertIsNone(_root_dir)
        self.assertIsNone(_regex)

    def test_004_get_last_file_create_from_dir(self):
        """
            Scenario: Search location of the last log created
            Given root directory for search and
                  a regex expression
            When the location of the last log created is required
            Then response should be the location of the log
        """
        _regex = re.compile(r'oci_exacc_dpy_(upgrade|rollingupgrade)_\d{8}_\d{6}.log')
        _file_list = self.create_dummy_log_files(self.log_dir, self.log_file_generator_for_cps_deployer)
        log_path = utils.mGetLastFileCreateFromDir(self.log_dir, _regex)
        self.assertIsNotNone(log_path)
        self.assertEqual(log_path, _file_list[-1])
        self.cleanup_dummy_log_files(_file_list)

    def test_005_process_cps_log(self):
        """
            Scenario: Create a symling of remote manager log on a specific
                      directory location.
            Given an remote manager request uuid
            When the remote manager requests is completed.
            Then a symlink of remote manager log should be created on target
            directory
        """
        _exabox_path = os.path.join(self.exacloud_path, "exabox")
        _mockConfig = Mock(**{"mGetConfigValue.return_value": "/opt/oci/exacc",
                              "mGetPath.return_value": _exabox_path})
        _mockEndpoint = Mock(**{
            "mGetConfig.return_value":_mockConfig,
            "mBashExecution.return_value": (0, io.StringIO("sysout"), io.StringIO("syserr")),
            "mAsyncLog.return_value": None
        })
        _uuid = str(uuid.uuid1(clock_seq=1))

        _log_file = os.path.abspath("{0}/mgnt-{1}.log".format(self.log_dir, _uuid))
        if os.path.exists(_log_file):
            os.unlink(_log_file)

        Path(_log_file).touch()

        try:
            utils.mProcessCpsLog(_mockEndpoint, _uuid, utils.CpsLogType.CPS_DEPLOYER)
        except Exception:

            self.fail("mProcessCpsLog() should not raise exception {0}".format(traceback.format_exc()))
        _chainsaw_loc = "/opt/oci/exacc/chainsaw/logs/cpssw"
        calls = [
            call.mBashExecution(['/usr/bin/sudo', '/usr/bin/mkdir', '-p',_chainsaw_loc]),
            call.mBashExecution(['/usr/bin/sudo', '/usr/bin/ln', '-sf', _log_file,
                                 '{0}/mgmt-log-latest'.format(_chainsaw_loc)])
        ]
        _mockEndpoint.assert_has_calls(calls)
        if os.path.exists(_log_file):
            os.unlink(_log_file)

    def test_006_process_cps_log_external_log(self):
        """
            Scenario: Create a symlink for log files on a specific
                      directory location.
            Given an remote manager request uuid and external log information
            When the remote manager requests is completed
            Then a symlink of remote manager log should be created on target directory
            directory and a symlink of external log should be created on same target directory
        """
        _list_logs_cps = [
            (utils.CpsLogType.SANITY_TOOL,self.log_file_generator_for_Sanity),
            (utils.CpsLogType.CPS_DEPLOYER, self.log_file_generator_for_cps_deployer),
            (utils.CpsLogType.CPS_CHECK_TOOL, self.log_file_generator_for_cps_sw_check)
        ]
        for _log_type, _file_gen in _list_logs_cps:
            with self.subTest("process log from {0}".format(_log_type.value), _log_type=_log_type):
                _exabox_path = os.path.join(self.exacloud_path, "exabox")
                _mockConfig = Mock(**{"mGetConfigValue.return_value": "/opt/oci/exacc",
                                      "mGetPath.return_value": _exabox_path})
                _mockEndpoint = Mock(**{
                    "mGetConfig.return_value": _mockConfig,
                    "mBashExecution.return_value": (0, io.StringIO("sysout"), io.StringIO("syserr")),
                    "mAsyncLog.return_value": None
                })
                _uuid = str(uuid.uuid1(clock_seq=1))
                _file_list = self.create_dummy_log_files(self.log_dir, _file_gen)
                _log_file = os.path.abspath("{0}/mgnt-{1}.log".format(self.log_dir, _uuid))
                if os.path.exists(_log_file):
                    os.unlink(_log_file)
                Path(_log_file).touch()

                _optional_dict = {
                    _log_type: self.log_dir
                }
                try:
                    utils.mProcessCpsLog(_mockEndpoint, _uuid, _log_type,
                                         aOptionalDirDict=_optional_dict)
                except Exception:
                    self.fail("mProcessCpsLog() should not raise exception {0}".format(traceback.format_exc()))
                _chainsaw_loc = "/opt/oci/exacc/chainsaw/logs/cpssw"
                calls = [
                    call.mBashExecution(['/usr/bin/sudo', '/usr/bin/mkdir', '-p', _chainsaw_loc]),
                    call.mBashExecution(['/usr/bin/sudo', '/usr/bin/ln', '-sf', _log_file,
                                         '{0}/mgmt-log-latest'.format(_chainsaw_loc)]),
                    call.mBashExecution(['/usr/bin/sudo', '/usr/bin/ln', '-sf', _file_list[-1],
                                         "{0}/{1}".format(_chainsaw_loc, _log_type.value)])
                ]
                _mockEndpoint.assert_has_calls(calls)
                _file_list.append(_log_file)
                self.cleanup_dummy_log_files(_file_list)

    def test_007_build_process_result_success(self):
        """
        Scenario: Build a result output message for a successfully request
        Given : A request for remote manager
        When : The request is successfully completed.
        Then : The response should include the default success message.
        """
        _result = utils.mBuildProccessResult(0, aErrorCode=error_fwk.CpsGenericMesgEnum.GENERIC_UPGRADE_SUCCESS_EXIT_CODE.value)
        self.assertIsNotNone(_result)
        self.assertTrue(isinstance(_result, dict))
        self.assertIn(utils.CpsResultProcessKeys.ERROR_CODE.value, _result)
        self.assertIn(utils.CpsResultProcessKeys.ERROR_MESSAGE.value, _result)
        self.assertIn(utils.CpsResultProcessKeys.ERROR_DETAIL.value, _result)
        self.assertIn(utils.CpsResultProcessKeys.TYPE_RESULT.value, _result)
        self.assertEqual(_result.get(utils.CpsResultProcessKeys.TYPE_RESULT.value, ""),
                         utils.CpsTypeReturnCode.CPS_SW_RETURN_CODE.value)
        self.assertEqual(_result.get(utils.CpsResultProcessKeys.ERROR_CODE.value, ""),
                         error_fwk.CpsGenericMesgEnum.GENERIC_UPGRADE_SUCCESS_EXIT_CODE.value)
        self.assertEqual(_result.get(utils.CpsResultProcessKeys.ERROR_MESSAGE.value, ""),
                         error_fwk.CPS_MESSAGE_BY_RANGE.get(error_fwk.CpsMessageRangeEnum.G_SUCCESS_PATCH_GENERIC.value))
        self.assertEqual(_result.get(utils.CpsResultProcessKeys.ERROR_DETAIL.value, ""),
                         error_fwk.CPS_GENERIC_MESSAGE.get(error_fwk.CpsGenericMesgEnum.GENERIC_UPGRADE_SUCCESS_EXIT_CODE.value))

    def test_008_build_process_result_no_error_code(self):
        """
        Scenario: Build a result output message for a failed  request
        Given : A request for remote manager
        When : The request fails
            And the error code is not registered
        Then : The response should include the default failed message.
        """
        unknown_error_code = "0x09999999"
        _default_message = error_fwk.CPS_MESSAGE_BY_RANGE.get(error_fwk.CpsMessageRangeEnum.G_ERROR_RANGE_CPS_SW_UPGRADE.value)
        _default_error_code = error_fwk.CpsCpsSwUpgradeErrorEnum.CPS_SW_UPGRADE_NO_ERROR_CODE.value
        _result = utils.mBuildProccessResult(0, aErrorCode=unknown_error_code)
        self.assertIsNotNone(_result)
        self.assertTrue(isinstance(_result, dict))
        self.assertIn(utils.CpsResultProcessKeys.ERROR_CODE.value, _result)
        self.assertIn(utils.CpsResultProcessKeys.ERROR_MESSAGE.value, _result)
        self.assertIn(utils.CpsResultProcessKeys.ERROR_DETAIL.value, _result)
        self.assertEqual(_result.get(utils.CpsResultProcessKeys.ERROR_CODE.value, ""), unknown_error_code)
        self.assertEqual(_result.get(utils.CpsResultProcessKeys.ERROR_MESSAGE.value, ""), _default_message)
        self.assertEqual(_result.get(utils.CpsResultProcessKeys.ERROR_DETAIL.value, ""),
                         error_fwk.CPS_SW_UPGRADE_DETAIL.get(_default_error_code))

    def test_009_get_cps_return_code_success(self):
        """
        Scenario: Retrieve error code from return value of remote manager endpoint method.
        Given: A return code from remote manager endpoint
        When : Return code is an int and return code is zero
        Then : Return value should include the default success message.
        """
        _test_dict = dict()
        _rc = 0
        utils.get_cps_return_code(_rc, _test_dict)
        self.assertTrue(_test_dict)
        self.assertIn(utils.CpsResultProcessKeys.ASYNC_ERROR.value, _test_dict)
        _async_error = _test_dict.get(utils.CpsResultProcessKeys.ASYNC_ERROR.value)
        self.assertEqual(_async_error.get(utils.CpsResultProcessKeys.ERROR_CODE.value, None),
                        error_fwk.CpsGenericMesgEnum.GENERIC_UPGRADE_SUCCESS_EXIT_CODE.value)
        self.assertEqual(_async_error.get(utils.CpsResultProcessKeys.ERROR_MESSAGE.value, None),
                         error_fwk.CPS_MESSAGE_BY_RANGE.get(
                             error_fwk.CpsMessageRangeEnum.G_SUCCESS_PATCH_GENERIC.value))
        self.assertEqual(_async_error.get(utils.CpsResultProcessKeys.ERROR_DETAIL.value, None),
                         error_fwk.CPS_GENERIC_MESSAGE.get(
                             error_fwk.CpsGenericMesgEnum.GENERIC_UPGRADE_SUCCESS_EXIT_CODE.value))

    def test_010_get_cps_return_code_failure(self):
        """
        Scenario: Retrieve error code from return value of remote manager endpoint method.
        Given: A return code from remote manager endpoint
        When : Return code is an int and return code is different than zero
        Then : Return value should include the default failure message.
        """
        _test_dict = dict()
        _rc = 1
        utils.get_cps_return_code(_rc, _test_dict)
        self.assertTrue(_test_dict)
        self.assertIn(utils.CpsResultProcessKeys.ASYNC_ERROR.value, _test_dict)
        _async_error = _test_dict.get(utils.CpsResultProcessKeys.ASYNC_ERROR.value)
        self.assertEqual(_async_error.get(utils.CpsResultProcessKeys.ERROR_CODE.value, None),
                        error_fwk.CpsCpsSwUpgradeErrorEnum.CPS_SW_UPGRADE_OPERATION_FAILED.value)
        self.assertEqual(_async_error.get(utils.CpsResultProcessKeys.ERROR_MESSAGE.value, None),
                         error_fwk.CPS_MESSAGE_BY_RANGE.get(
                             error_fwk.CpsMessageRangeEnum.G_ERROR_RANGE_CPS_SW_UPGRADE.value))
        self.assertEqual(_async_error.get(utils.CpsResultProcessKeys.ERROR_DETAIL.value, None),
                         error_fwk.CPS_SW_UPGRADE_DETAIL.get(
                             error_fwk.CpsCpsSwUpgradeErrorEnum.CPS_SW_UPGRADE_NO_ERROR_CODE.value))

    def test_011_get_cps_return_code_success_format_error_message(self):
        """
        Scenario: Retrieve error code from return value of remote manager endpoint method.
        Given: A return code from remote manager endpoint
        When : Return code is instance dict and "type_result" = "CPS_SW_RETURN_CODE" and
               "rc" is zero
        Then : Return value should include the default success message.
        """
        _test_dict = dict()
        _return_code = {
            utils.CpsResultProcessKeys.TYPE_RESULT.value: utils.CpsTypeReturnCode.CPS_SW_RETURN_CODE.value,
            utils.CpsResultProcessKeys.RETURN_CODE.value: 0,
            utils.CpsResultProcessKeys.ERROR_CODE.value: error_fwk.CpsGenericMesgEnum.GENERIC_UPGRADE_SUCCESS_EXIT_CODE.value
        }
        utils.get_cps_return_code(_return_code, _test_dict)
        self.assertTrue(_test_dict)
        self.assertIn(utils.CpsResultProcessKeys.ASYNC_ERROR.value, _test_dict)
        _async_error = _test_dict.get(utils.CpsResultProcessKeys.ASYNC_ERROR.value)
        self.assertEqual(_async_error.get(utils.CpsResultProcessKeys.ERROR_CODE.value, None),
                        error_fwk.CpsGenericMesgEnum.GENERIC_UPGRADE_SUCCESS_EXIT_CODE.value)
        self.assertEqual(_async_error.get(utils.CpsResultProcessKeys.ERROR_MESSAGE.value, None),
                         error_fwk.CPS_MESSAGE_BY_RANGE.get(
                             error_fwk.CpsMessageRangeEnum.G_SUCCESS_PATCH_GENERIC.value))
        self.assertEqual(_async_error.get(utils.CpsResultProcessKeys.ERROR_DETAIL.value, None),
                         error_fwk.CPS_GENERIC_MESSAGE.get(
                             error_fwk.CpsGenericMesgEnum.GENERIC_UPGRADE_SUCCESS_EXIT_CODE.value))

    def test_012_get_cps_return_code_failure_format_error_message(self):
        """
        Scenario: Retrieve error code from return value of remote manager endpoint method.
        Given: A return code from remote manager endpoint
        When : Return code is instance dict and "type_result" = "CPS_SW_RETURN_CODE" and
               "return_code" is not zero
        Then : Return value should include the default failure message.
        """
        _test_dict = dict()
        _return_code = {
            utils.CpsResultProcessKeys.TYPE_RESULT.value: utils.CpsTypeReturnCode.CPS_SW_RETURN_CODE.value,
            utils.CpsResultProcessKeys.RETURN_CODE.value : 1,
            utils.CpsResultProcessKeys.ERROR_CODE.value: error_fwk.CpsCpsSwUpgradeErrorEnum.CPS_SW_UPGRADE_OPERATION_FAILED.value
        }
        utils.get_cps_return_code(_return_code, _test_dict)
        self.assertTrue(_test_dict)
        self.assertIn(utils.CpsResultProcessKeys.ASYNC_ERROR.value, _test_dict)
        _async_error = _test_dict.get(utils.CpsResultProcessKeys.ASYNC_ERROR.value)
        self.assertEqual(_async_error.get(utils.CpsResultProcessKeys.ERROR_CODE.value, None),
                         error_fwk.CpsCpsSwUpgradeErrorEnum.CPS_SW_UPGRADE_OPERATION_FAILED.value)
        self.assertEqual(_async_error.get(utils.CpsResultProcessKeys.ERROR_MESSAGE.value, None),
                         error_fwk.CPS_MESSAGE_BY_RANGE.get(
                             error_fwk.CpsMessageRangeEnum.G_ERROR_RANGE_CPS_SW_UPGRADE.value))
        self.assertEqual(_async_error.get(utils.CpsResultProcessKeys.ERROR_DETAIL.value, None),
                         error_fwk.CPS_SW_UPGRADE_DETAIL.get(
                             error_fwk.CpsCpsSwUpgradeErrorEnum.CPS_SW_UPGRADE_OPERATION_FAILED.value))
    
    def test_013_get_cps_return_code_alive_process(self):
        """
        Scenario: Retrieve error code from return value of remote manager endpoint method.
        Given: A return code from remote manager endpoint
        When : the request still in progress
        Then : Return value should not include the error code  message.
        """
        _test_dict = dict()
        _rc = None
        utils.get_cps_return_code(_rc, _test_dict, aProcessIsAlive=True)
        _async_error = _test_dict.get(utils.CpsResultProcessKeys.ASYNC_ERROR.value)
        self.assertIn(utils.CpsResultProcessKeys.ASYNC_ERROR.value, _test_dict.keys())
        self.assertFalse(_test_dict[utils.CpsResultProcessKeys.ASYNC_ERROR.value])

    def test_014_process_cps_log_external_log_custom_name(self):
        """
            Scenario: Create a symlink for log files on a specific
                      directory location.
            Given an remote manager request uuid and external log information
            When the remote manager requests is completed
            Then a symlink of remote manager log should be created on target directory
            directory and a symlink of external log should be created on same target directory
        """
        _list_logs_cps = [
            (utils.CpsLogType.SANITY_TOOL,self.log_file_generator_for_Sanity, "cpssw-cpscheck-sanity"),
            (utils.CpsLogType.CPS_DEPLOYER, self.log_file_generator_for_cps_deployer, "cpssw-upgrade"),
            (utils.CpsLogType.CPS_CHECK_TOOL, self.log_file_generator_for_cps_sw_check, "cpssw-cpscheck-version")
        ]
        for _log_type, _file_gen, _custom_name in _list_logs_cps:
            with self.subTest("process log from {0}".format(_log_type.value), _log_type=_log_type):
                _exabox_path = os.path.join(self.exacloud_path, "exabox")
                _mockConfig = Mock(**{"mGetConfigValue.return_value": "/opt/oci/exacc",
                                      "mGetPath.return_value": _exabox_path})
                _mockEndpoint = Mock(**{
                    "mGetConfig.return_value": _mockConfig,
                    "mBashExecution.return_value": (0, io.StringIO("sysout"), io.StringIO("syserr")),
                    "mAsyncLog.return_value": None
                })
                _uuid = str(uuid.uuid1(clock_seq=1))
                _file_list = self.create_dummy_log_files(self.log_dir, _file_gen)
                _log_file = os.path.abspath("{0}/mgnt-{1}-{2}.log".format(self.log_dir, _uuid, _custom_name))
                if os.path.exists(_log_file):
                    os.unlink(_log_file)
                Path(_log_file).touch()
                _optional_dict = {
                    _log_type: self.log_dir
                }
                try:
                    utils.mProcessCpsLog(_mockEndpoint, _uuid, _log_type,
                                         aOptionalDirDict=_optional_dict, aCustomLogName=_log_file)
                except Exception:
                    self.fail("mProcessCpsLog() should not raise exception {0}".format(traceback.format_exc()))
                _chainsaw_loc = "/opt/oci/exacc/chainsaw/logs/cpssw"
                calls = [
                    call.mBashExecution(['/usr/bin/sudo', '/usr/bin/mkdir', '-p', _chainsaw_loc]),
                    call.mBashExecution(['/usr/bin/sudo', '/usr/bin/ln', '-sf', _log_file,
                                         '{0}/mgmt-log-latest'.format(_chainsaw_loc)]),
                    call.mBashExecution(['/usr/bin/sudo', '/usr/bin/ln', '-sf', _file_list[-1],
                                         "{0}/{1}".format(_chainsaw_loc, _log_type.value)])
                ]
                _mockEndpoint.assert_has_calls(calls)
                _file_list.append(_log_file)
                self.cleanup_dummy_log_files(_file_list)


    def test_015_generate_custom_log_path_uuid(self):
        """
        Scenario: Generate a custom log path.
        Given: A uuid
               and exacloud config
        When : the log name should be customized.
        Then : Return value should have the path of the custom log name in format
               mgnt-{uuid}.log
        """
        _uuid = str(uuid.uuid1(clock_seq=1))
        _exabox_path = os.path.join(self.exacloud_path, "exabox")
        _mockConfig = Mock(**{"mGetPath.return_value": _exabox_path})
        _custom_log_path = utils.generate_custom_log_path(_mockConfig, _uuid)
        self.assertIsNotNone(_custom_log_path)
        result_log_path = Path(_custom_log_path)
        self.assertEquals(result_log_path.name,f"mgnt-{_uuid}.log")

    def test_016_generate_custom_log_path(self):
        """
        Scenario: Generate a custom log path.
        Given: An uuid
               and exacloud config
               and dict with custom name
        When : the log name should be customized.
        Then : Return value should have the path of the custom log name
        """
        _uuid = str(uuid.uuid1(clock_seq=1))
        _exabox_path = os.path.join(self.exacloud_path, "exabox")
        _mockConfig = Mock(**{"mGetPath.return_value": _exabox_path})
        _custom_log_path = utils.generate_custom_log_path(_mockConfig, _uuid, aSuffixName="cpssw-cpscheck-sanity")
        self.assertIsNotNone(_custom_log_path)
        result_log_path = Path(_custom_log_path)
        self.assertEquals(result_log_path.name,f"mgnt-{_uuid}-cpssw-cpscheck-sanity.log")
           
    def test_017_get_local_hostname(self):
        """
        Scenario: Get local hostname
        When : local hostname is required
        Then : Return value is short form of the current host
        """
        cps_localhost  = "cps01localhost"
        cps_fqdn = f'{cps_localhost}.us.oracle.com'
        with patch("exabox.managment.src.utils.CpsExaccUtils.socket.gethostname", side_effect = [socket.error("mock socket error"), cps_fqdn]):
            cps_localhostname = utils.mGetLocalHostname()
            self.assertIsNotNone(cps_localhostname)
            self.assertEquals(cps_localhost, cps_localhostname)

    def test_018_sanitize_path(self):
        """
            Scenario: sanitize file path on cps
            Given: A file path
            When: the file path is required to be sanitized
            Then: return file path if the path is under allowed directories, empty string otherwise
        """
        _list_file_cps = [
            ("/opt/oci/exacc/config_bundle/ocpsSetup.json",  "/opt/oci/exacc/config_bundle/ocpsSetup.json"),
            ("/u01/downloads/activeVersion.json", "/u01/downloads/activeVersion.json"),
            ("/etc/noallowed","")
        ]
        for _file_path, expected_file_path in _list_file_cps:
            with self.subTest("process log from {0}".format(_file_path), _file_path=_file_path):
                _result_file_path = utils.mSanitizePath(_file_path)
                self.assertIsNotNone(_result_file_path)
                self.assertEquals(_result_file_path, expected_file_path)
    
    def test_019_execute_cmd_by_host_locahost(self):
        """
        Scenario: Execute cmd on host
        Given: 
              A cmd and host is localhost
        Then: 
             Cmd should be executed on localhost
        """
        cps_localhost  = "cps01localhost"
        cps_fqdn = f'{cps_localhost}.us.oracle.com'
        _mockEndpoint = Mock(**{
            "mBashExecution.return_value": (0,"sysout\nsysout", "syserr")
        })
        with patch("exabox.managment.src.utils.CpsExaccUtils.mGetLocalHostname", return_value=cps_localhost):
            _rc, _sysout, _ = utils.mExecuteCmdByHost(_mockEndpoint, "ls -la", None, cps_fqdn)
            self.assertEquals(_rc , 0)
            self.assertEquals(["sysout", "sysout"], _sysout)
            _mockEndpoint.mBashExecution.assert_called_with(["ls", "-la"], aRedirect=-1)

    def test_20_execute_cmd_by_host_remotecps(self):
        """
        Scenario: Execute cmd on remote host
        Given: 
              A cmd and host is not localhost
        Then: 
             Cmd should be executed on remote hosts
        """
        _mockEndpoint = Mock(**{})
        cps_localhost  = "cps01localhost"
        cps_fqdn = "cps02remotehost.us.oracle.com"
        mock_exabox_node = Mock(**{
            "mGetCmdExitStatus.return_value":0, 
            "mExecuteCmd.return_value": (0, io.StringIO("sysout sysout"),io.StringIO("")), 
            "mConnect.return_value": None, 
            "mDisconnect.return_value": None})
        with patch("exabox.managment.src.utils.CpsExaccUtils.exaBoxNode", return_value=mock_exabox_node):
            _rc, _sysout, _ = utils.mExecuteCmdByHost(_mockEndpoint, "ls -la", None, cps_fqdn)
            self.assertEquals(_rc , 0)
            self.assertEquals(["sysout sysout"], _sysout)
            mock_exabox_node.mSetUser.assert_called_with("ecra")
            mock_exabox_node.mConnect.assert_called_with(aHost='cps02remotehost.us.oracle.com')
            mock_exabox_node.mExecuteCmd.assert_called_with("ls -la", aTimeout=3600)

if __name__ == '__main__':
    unittest.main(warnings='ignore')
