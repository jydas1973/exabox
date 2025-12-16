#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/remoteec/tests_cps_exacc_error.py /main/2 2023/06/22 18:50:15 hgaldame Exp $
#
# tests_cps_exacc_error.py
#
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.
#
#    NAME
#      tests_cps_exacc_error.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    hgaldame    06/16/23 - 35509904 - oci/exacc: fix error codes on remote
#                           manager for match with ecra error catalog
#    hgaldame    10/03/22 - 34627398 - exacc:bb:22.3.1:cps-sw upgrade: provide
#                           proper error code for precheck failure instead of
#                           returning generic error
#    hgaldame    10/03/22 - Creation
#
import os
import unittest
import uuid
import json
import socket
import io
import re
import  exabox.managment.src.utils.CpsExaccError as error_fwk
import traceback
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from datetime import datetime
from unittest.mock import patch, Mock, call
from time import strftime, localtime, sleep
from pathlib import Path
from collections import ChainMap

class ebTestRemoteManagmentCpsExaccError(ebTestClucontrol):

    def setUp(self):
        _abs_path = os.path.abspath(self.mGetPath())
        self.exacloud_path = self.mGetUtil().mGetExacloudPath()

    def test_001_build_default_success_message(self):
        """
            Scenario: Retrieve a default success message
            Given a request which ends successfully
            When a default success message is required
            Then response should a default success message
        """
        _result = error_fwk.mBuildDefaultSuccessMessage()
        self.assertIsNotNone(_result)
        self.assertTrue(isinstance(_result, dict))
        self.assertIn("error_code", _result)
        self.assertIn("error_message", _result)
        self.assertIn("error_detail", _result)
        self.assertEqual(_result.get("error_code",""), "0x00000000")
        self.assertEqual(_result.get("error_message", ""), "Operation executed successfully.")
        self.assertEqual(_result.get("error_detail", ""), "no further action required.")

    def test_002_build_default_failure_message(self):
        """
            Scenario: Retrieve a default failure message
            Given a request which ends with error
            When a default failure message is required
            Then response should a default failure message
        """
        _result = error_fwk.mBuildDefaultFailureMessage()
        self.assertIsNotNone(_result)
        self.assertTrue(isinstance(_result, dict))
        self.assertIn("error_code", _result)
        self.assertIn("error_message", _result)
        self.assertIn("error_detail", _result)
        self.assertEqual(_result.get("error_code",""), "0x07020005")
        self.assertEqual(_result.get("error_message", ""), "CPS SW Upgrade operation failed.")
        self.assertEqual(_result.get("error_detail", ""), "no error code reported, returning generic error.")

    def test_003_get_error_code_by_precheck_action(self):
        """
            Scenario: Retrieve a code error message for cps sw check
            Given a cps sw check action
            When there is a failure of cps sw check action
            Then response should include a failure message for cps sw check.
        """
        _precheck_list = [ "--action {0}".format(_action) for _action in ["checkcpsversion", "checkfsavailable", "checkcpsartifact" ]]
        for _precheck in _precheck_list:
            with self.subTest(" Retrieving code error for : {0}".format(_precheck), _precheck=_precheck):
                _result = error_fwk.mGetErrorByPrecheckAction(_precheck)
                self.assertIsNotNone(_result)
                self.assertIn("0702",_result)
                self.assertNotEqual("0x07020009",_result)

    def test_004_get_default_error_code_precheck_action(self):
        """
            Scenario: Retrieve a default code error message for cps sw check
            Given a cps sw check action
            When there is a failure of cps sw check action
            and action is not defined on error catalogue
            Then response should include a default failure message for cps sw check.
        """
        _result = error_fwk.mGetErrorByPrecheckAction("--notregisteredaction")
        self.assertIsNotNone(_result)
        self.assertEqual("0x07020009",_result)

    def test_005_get_error_message_by_range(self):
        """
            Scenario: Retrieve error message by range.
            Given an error range
            When there is a failure on remote manager request and is required
            to provide an error message.
            Then response should include an error message
        """
        _error_range_list = [ error_range.value for error_range in  error_fwk.CpsMessageRangeEnum]
        for _error_range in _error_range_list:
            with self.subTest(" Retrieving error message for range : {0}".format(_error_range), _error_range=_error_range):
                _message = error_fwk.mGetErrorMessageByRange(_error_range)
                self.assertIsNotNone(_message)
                self.assertTrue(len(_message)>0)

    def test_006_get_catalogue_message_by_range(self):
        """
            Scenario: Retrieve catalogue of error details message by range.
            Given an error range
            When there is a failure on remote manager request and is required
            to provide an error detail
            Then response should include an error detail
        """
        _error_range_list = [ error_range.value for error_range in  error_fwk.CpsMessageRangeEnum]
        for _error_range in _error_range_list:
            with self.subTest(" Retrieving catalogue for range : {0}".format(_error_range), _error_range=_error_range):
                _catalogue = error_fwk.mGetDetailCatalogueByRange(_error_range)
                self.assertIsNotNone(_catalogue)
                self.assertTrue(isinstance(_catalogue, dict))

    def test_007_get_catalogue_message_by_range(self):
        """

        Returns:

        """
        _catalogue_error_list = [ error_fwk.CpsCpsSwUpgradeErrorEnum, error_fwk.CpsGenericMesgEnum]
        _catalogue_pair_list = []
        for _catalogue in _catalogue_error_list:
            _catalogue_pair_list.append( (_catalogue, [ _error.value for _error in  _catalogue]))
        _general_detail_msg = ChainMap(error_fwk.CPS_GENERIC_MESSAGE, error_fwk.CPS_SW_UPGRADE_DETAIL)
        for _catalogue, _error_code_list in _catalogue_pair_list:
            for _error_code in _error_code_list:
                with self.subTest(" Retrieving message for code error : {0}".format(_error_code), _error_range=_error_code):
                    _error_message = error_fwk.mCpsFormatBuildError(_error_code)
                    self.assertIsNotNone(_error_message)
                    self.assertTrue(isinstance(_error_message, dict))
                    self.assertIn("error_code", _error_message)
                    self.assertIn("error_message", _error_message)
                    self.assertIn("error_detail", _error_message)
                    self.assertEqual(_error_message.get("error_code", ""), _error_code)
                    self.assertIn(_error_code, _general_detail_msg)
                    self.assertEqual(_error_message.get("error_detail", ""), _general_detail_msg[_error_code])

if __name__ == '__main__':
    unittest.main(warnings='ignore')
