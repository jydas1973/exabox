#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/remoteec/tests_cps_oel8migr.py /main/4 2025/05/07 17:03:26 hgaldame Exp $
#
# tests_cps_oel8migr.py
#
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_cps_oel8migr.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    hgaldame    05/06/25 - 37911448 - oci/exacc: oel 7 to oel 8 cps os
#                           migration ecra wf task
#                           runcpsosstandbyadditionalconfigs failure due to
#                           iptables missing
#    hgaldame    03/10/25 - 37687625 - oci/exacc: remote manager returns false
#                           positive on oel 7 to oel 8 migration exadata image
#                           24
#    hgaldame    02/12/25 - 37587401 - oci/exacc: oel 8 migration fails on cps
#                           remote manager endpoint
#    hgaldame    10/25/24 - enh 37236624 - oci/exacc: remote manager endpoint
#                           for execute cps software oel 7 to oel 8 migration
#    hgaldame    10/25/24 - Creation
#

import unittest
import tempfile
import uuid
import os
import io
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from unittest.mock import patch, Mock, ANY, call
import exabox.managment.src.CpsEndpoint as moduleInstance
from exabox.managment.src.CpsEndpoint import CpsEndpoint

class ebTestRemoteManagmentOel8Migr(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateRemoteEC=True)

    def test_000_call_endpoint(self):
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _body = {
            "type": "cpsoel8migr", 
            "bundle": "LATEST",
            "args" : "--reset_history"
        }
        _response = {}
        _endpoint = CpsEndpoint(None, _body, _response, _shared)
        with patch.object(_endpoint, "mCreatePythonProcess") as _spy_method:
            _endpoint.mPost()
            _spy_method.assert_called_once_with(
                _endpoint._CpsEndpoint__mCpsOel8Migration,
                "--reset_history",
                aId=ANY, # uuid
                aOnFinish=_endpoint.mProcessCpsLogOnFinish,
                aOnFinishArgs=ANY, # custom log name
                aName="CPSS oel 8 migration: [--reset_history]",
                aLogFile=ANY
                )

    def test_001_mIsOelMigrRequired(self):
        """
        Scenario: Check if oel8 migration is required
        Given: Image history output
        When: The check for oel8 migration is executed
        Then: Last entry of image history should be 23
              second last of image history should be 22
        """
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _body = {
            "type": "cpsoel8migr", 
            "bundle": "LATEST"        
        }
        single_item="""
Version                              : 23.1.13.0.0.240510
Image activation date                : 2024-10-05 19:17:33 +0000
Imaging mode                         : fresh
Imaging status                       : success
"""
        only_22_series="""
Version                              : 21.2.11.0.0.220414.1
Image activation date                : 2022-05-25 13:39:31 +0000
Imaging mode                         : fresh
Imaging status                       : success

Version                              : 22.1.6.0.0.221207
Image activation date                : 2023-01-27 00:15:53 +0000
Imaging mode                         : patch
Imaging status                       : success

Version                              : 22.1.9.0.0.230302
Image activation date                : 2023-04-20 17:11:31 +0000
Imaging mode                         : patch
Imaging status                       : success
"""
        only_23_series="""
Version                              : 23.1.13.0.0.240410.1
Image activation date                : 2024-06-10 19:55:58 +0000
Imaging mode                         : fresh
Imaging status                       : success

Version                              : 23.1.15.0.0.240605
Image activation date                : 2024-07-16 05:04:57 +0000
Imaging mode                         : patch
Imaging status                       : success
        """
        not_valid_item= """
Imaging status                       : success
Exasplice update version             : 240407.1
Exasplice update activation date     : 2024-05-06 00:32:35 +0000
        """
        last_item_not_success="""
Version                              : 22.1.16.0.0.231012
Image activation date                : 2023-11-03 06:49:48 +0000
Imaging mode                         : patch
Imaging status                       : success
Exasplice update version             : 240407.1
Exasplice update activation date     : 2024-05-06 00:32:35 +0000

Version                              : 23.1.13.0.0.240510
Image activation date                : 2024-10-05 19:17:33 +0000
Imaging mode                         : patch
Imaging status                       : failure
"""

        oel8_migration_required="""
Version                              : 22.1.13.0.0.230712
Image activation date                : 2023-08-08 09:37:35 +0000
Imaging mode                         : patch
Imaging status                       : success

Version                              : 22.1.24.0.0.240601
Image activation date                : 2024-07-23 14:24:06 +0000
Imaging mode                         : patch
Imaging status                       : success

Version                              : 23.1.15.0.0.240605
Image activation date                : 2024-07-16 05:04:57 +0000
Imaging mode                         : patch
Imaging status                       : success
"""
        oel8_migration_required_boundaries="""
Version                              : 21.1.13.0.0.230712
Image activation date                : 2023-08-08 09:37:35 +0000
Imaging mode                         : patch
Imaging status                       : success

Version                              : 21.1.24.0.0.240601
Image activation date                : 2024-07-23 14:24:06 +0000
Imaging mode                         : patch
Imaging status                       : success

Version                              : 25.1.15.0.0.240605
Image activation date                : 2024-07-16 05:04:57 +0000
Imaging mode                         : patch
Imaging status                       : success
"""
        oel8_post_migration="""
Version                              : 22.1.13.0.0.230712
Image activation date                : 2023-08-08 09:37:35 +0000
Imaging mode                         : patch
Imaging status                       : success

Version                              : 22.1.24.0.0.240601
Image activation date                : 2024-07-23 14:24:06 +0000
Imaging mode                         : patch
Imaging status                       : success

Version                              : 23.1.15.0.0.240605
Image activation date                : 2024-07-16 05:04:57 +0000
Imaging mode                         : patch
Imaging status                       : success

Version                              : 23.1.16.0.0.240705
Image activation date                : 2024-08-16 05:04:57 +0000
Imaging mode                         : patch
Imaging status                       : success
"""

        exadata_24_oel8_migration_required_22_to_24="""
Version                              : 22.1.32.0.0.250205
Exadata Live Update Version          : n/a
Image activation date                : 2025-02-20 11:32:12 -0800
Imaging mode                         : fresh
Imaging status                       : success

Version                              : 24.1.8.0.0.250208
Exadata Live Update Version          : n/a
Image activation date                : 2025-03-07 18:09:53 -0800
Imaging mode                         : patch
Imaging status                       : success
"""

        exadata_24_oel8_migration_not_required_23_to_24="""
Version                              : 23.1.15.0.0.240605
Exadata Live Update Version          : n/a
Image activation date                : 2025-02-20 11:32:12 -0800
Imaging mode                         : fresh
Imaging status                       : success

Version                              : 24.1.8.0.0.250208
Exadata Live Update Version          : n/a
Image activation date                : 2025-03-07 18:09:53 -0800
Imaging mode                         : patch
Imaging status                       : success
"""
        exadata_24_oel8_migration_not_required_24_to_24="""
Version                              : 24.1.8.0.0.250208
Exadata Live Update Version          : n/a
Image activation date                : 2025-02-20 11:32:12 -0800
Imaging mode                         : fresh
Imaging status                       : success

Version                              : 24.1.9.0.0.250209
Exadata Live Update Version          : n/a
Image activation date                : 2025-03-07 18:09:53 -0800
Imaging mode                         : patch
Imaging status                       : success
"""
        exadata_24_oel8_post_migration="""
Version                              : 22.1.13.0.0.230712
Exadata Live Update Version          : n/a
Image activation date                : 2023-08-08 09:37:35 +0000
Imaging mode                         : patch
Imaging status                       : success

Version                              : 22.1.24.0.0.240601
Exadata Live Update Version          : n/a
Image activation date                : 2024-07-23 14:24:06 +0000
Imaging mode                         : patch
Imaging status                       : success

Version                              : 23.1.15.0.0.240605
Exadata Live Update Version          : n/a
Image activation date                : 2024-07-16 05:04:57 +0000
Imaging mode                         : patch
Imaging status                       : success

Version                              : 23.1.16.0.0.240705
Image activation date                : 2024-08-16 05:04:57 +0000
Imaging mode                         : patch
Imaging status                       : success

Version                              : 24.1.8.0.0.250208
Exadata Live Update Version          : n/a
Image activation date                : 2025-03-07 18:09:53 -0800
Imaging mode                         : patch
Imaging status                       : success
"""
        img_hist_content={
            "empty_history":("", False),
            "not_valid_item":(not_valid_item,False),
            "single_item":(single_item, False),
            "only_22_series":(only_22_series, False),
            "only_23_series":(only_23_series,False),
            "last_item_not_success":(last_item_not_success,False),
            "oel8_migration_required":(oel8_migration_required,True),
            "oel8_migration_required_boundaries":(oel8_migration_required_boundaries, True),
            "oel8_post_migration":(oel8_post_migration, False),
            "exadata_24_oel8_migration_required_22_to_24":(exadata_24_oel8_migration_required_22_to_24, True),
            "exadata_24_oel8_migration_not_required_23_to_24":(exadata_24_oel8_migration_not_required_23_to_24, False),
            "exadata_24_oel8_migration_not_required_24_to_24":(exadata_24_oel8_migration_not_required_24_to_24, False),
            "exadata_24_oel8_post_migration":(exadata_24_oel8_post_migration, False)
            }
        _response = {}
        _endpoint = CpsEndpoint(None, _body, _response, _shared)
        for name_test, content_tuple in img_hist_content.items():
            content, expected_result = content_tuple
            with self.subTest(" Retrieving code error for : {0}".format(name_test), 
            content=content,
            expected_result=expected_result):
                _rc = _endpoint.mIsOelMigrRequired(content)
                assert _rc.is_migr_req == expected_result , f" Failed test: {name_test}, expected: {expected_result}"

    def test_002_CpsOel8Migration_NotMaster(self):
        """
        Scenario: Run oel 8 migration on not master cps
        Given: Request for run oel 8 migration
        When: Send the request to not a master node
        Then: Migration should fail
        """
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _body = {
            "type": "cpsoel8migr", 
            "bundle": "LATEST"       
            }
        _response = {}
        _endpoint = CpsEndpoint(None, _body, _response, _shared)
        _log_fd, _log_path = tempfile.mkstemp()
        _process_id = str(uuid.uuid1(clock_seq=1))
        _mockAttrs = { "mGetExacloudConfigValue.return_value":"remotecps02"}
        _mockConfig = Mock(**_mockAttrs)

        with patch('exabox.managment.src.CpsEndpoint.CpsEndpoint.mGetConfig', return_value=_mockConfig),\
            patch('os.path.exists', return_value=False):
            _rc = _endpoint._CpsEndpoint__mCpsOel8Migration(_log_path, _process_id, aCustomArgs=None)
            assert  _rc.get("return_code",0) == 1
            assert  _rc.get("error_code","") == "0x07020010"

    def test_003_CpsOel8Migration_SingleCps(self):
        """
        Scenario: Run oel 8 migration on single cps
        Given: Request for run oel 8 migration
        When: There is a single cps
        Then: Migration should fail
        """
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _body = {
            "type": "cpsoel8migr", 
            "bundle": "LATEST"       
            }
        _response = {}
        _endpoint = CpsEndpoint(None, _body, _response, _shared)
        _log_fd, _log_path = tempfile.mkstemp()
        _process_id = str(uuid.uuid1(clock_seq=1))
        _mockAttrs = { "mGetExacloudConfigValue.return_value":None}
        _mockConfig = Mock(**_mockAttrs)

        with patch('exabox.managment.src.CpsEndpoint.CpsEndpoint.mGetConfig', return_value=_mockConfig),\
            patch('os.path.exists', return_value=True):
            _rc = _endpoint._CpsEndpoint__mCpsOel8Migration(_log_path, _process_id, aCustomArgs=None)
            assert  _rc.get("return_code",0) == 1
            assert  _rc.get("error_code","") == "0x07020013"
    
    def test_004_CpsOel8Migration_NotMigrationRequired(self):
        """
        Scenario: Run oel 8 migration on non major OS upgrade on cps
        Given: Request for run oel 8 migration
        When: The image history on cps-standby does not meet the migration
              conditions
        Then: Migration should success
        """
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _body = {
            "type": "cpsoel8migr", 
            "bundle": "LATEST"       
            }
        _response = {}
        _endpoint = CpsEndpoint(None, _body, _response, _shared)
        _log_fd, _log_path = tempfile.mkstemp()
        _process_id = str(uuid.uuid1(clock_seq=1))
        _mockAttrs = { "mGetExacloudConfigValue.return_value":"remotecps02"}
        _mockConfig = Mock(**_mockAttrs)
        img_hist_content="""
Version                              : 23.1.13.0.0.240410.1
Image activation date                : 2024-06-10 19:55:58 +0000
Imaging mode                         : fresh
Imaging status                       : success

Version                              : 23.1.15.0.0.240605
Image activation date                : 2024-07-16 05:04:57 +0000
Imaging mode                         : patch
Imaging status                       : success
"""
        _mock_exabox_node = Mock(**{
            "mGetCmdExitStatus.return_value":0, 
            "mExecuteCmd.return_value": (0,
                                         io.StringIO(img_hist_content),
                                         io.StringIO()), 
                                         "mConnect.return_value": None, 
                                         "mDisconnect.return_value": None}
                                         )
        with patch.object(moduleInstance,"connect_to_host") as spy_method:
            with patch('exabox.managment.src.CpsEndpoint.CpsEndpoint.mGetConfig', return_value=_mockConfig),\
                patch('os.path.exists', return_value=True):
                spy_method.return_value.__enter__.return_value = _mock_exabox_node
                _rc = _endpoint._CpsEndpoint__mCpsOel8Migration(_log_path, _process_id, aCustomArgs=None)
                assert  _rc == 0
                spy_method.return_value.__enter__.return_value.mExecuteCmd.assert_called_once_with("/usr/bin/sudo -n /bin/timeout --signal=SIGKILL 20s /usr/local/bin/imagehistory")

    def test_005_CpsOel8Migration_ImageHistoryFails(self):
        """
        Scenario: Failed imagehistory command on cps standby
        Given: Request for run oel 8 migration
        When: The image history on cps-standby fails 
        Then: Migration should fail
        """
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _body = {
            "type": "cpsoel8migr", 
            "bundle": "LATEST"       
            }
        _response = {}
        _endpoint = CpsEndpoint(None, _body, _response, _shared)
        _log_fd, _log_path = tempfile.mkstemp()
        _process_id = str(uuid.uuid1(clock_seq=1))
        _mockAttrs = { "mGetExacloudConfigValue.return_value":"remotecps02"}
        _mockConfig = Mock(**_mockAttrs)
        img_hist_content=""" """
        _mock_exabox_node = Mock(**{
            "mGetCmdExitStatus.return_value":1, 
            "mExecuteCmd.return_value": (1,
                                         io.StringIO(img_hist_content),
                                         io.StringIO("Image history fails")), 
                                         "mConnect.return_value": None, 
                                         "mDisconnect.return_value": None}
                                         )
        with patch.object(moduleInstance,"connect_to_host") as spy_method:
            with patch('exabox.managment.src.CpsEndpoint.CpsEndpoint.mGetConfig', return_value=_mockConfig),\
                patch('os.path.exists', return_value=True):
                spy_method.return_value.__enter__.return_value = _mock_exabox_node
                _rc = _endpoint._CpsEndpoint__mCpsOel8Migration(_log_path, _process_id, aCustomArgs=None)
                assert  _rc.get("return_code",0) == 1
                assert  _rc.get("error_code","") == "0x07020014"
                spy_method.return_value.__enter__.return_value.mExecuteCmd.assert_called_once_with("/usr/bin/sudo -n /bin/timeout --signal=SIGKILL 20s /usr/local/bin/imagehistory")


    def test_006_CpsOel8Migration_RunMigration_Fails(self):
        """
        Scenario: Failed cps deployer action after major OS upgrade
        Given: Request for run oel 8 migration
        When: cps deployer migration action fails 
        Then: Migration should fail
        """
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _body = {
            "type": "cpsoel8migr", 
            "bundle": "LATEST"       
            }
        _response = {}
        _endpoint = CpsEndpoint(None, _body, _response, _shared)
        _log_fd, _log_path = tempfile.mkstemp()
        _process_id = str(uuid.uuid1(clock_seq=1))
        _mockAttrs = { "mGetExacloudConfigValue.return_value":"remotecps02",
                      "mGetConfigValue.side_effect":[
                          "/opt/oci/exacc/exacloud",
                          "/opt/oci/config_bundle/rack.ocpsSetup.json"]}
        _mockConfig = Mock(**_mockAttrs)
        img_hist_content="""
Version                              : 22.1.13.0.0.230712
Image activation date                : 2023-08-08 09:37:35 +0000
Imaging mode                         : patch
Imaging status                       : success

Version                              : 22.1.24.0.0.240601
Image activation date                : 2024-07-23 14:24:06 +0000
Imaging mode                         : patch
Imaging status                       : success

Version                              : 23.1.15.0.0.240605
Image activation date                : 2024-07-16 05:04:57 +0000
Imaging mode                         : patch
Imaging status                       : success
"""
        _mock_exabox_node = Mock(**{
            "mGetCmdExitStatus.return_value":0, 
            "mExecuteCmd.return_value": (0,
                                         io.StringIO(img_hist_content),
                                         io.StringIO()), 
                                         "mConnect.return_value": None, 
                                         "mDisconnect.return_value": None}
                                         )
        with patch.object(moduleInstance,"connect_to_host") as spy_method:
            with patch('exabox.managment.src.CpsEndpoint.CpsEndpoint.mGetConfig', return_value=_mockConfig),\
                patch('exabox.managment.src.CpsEndpoint.CpsEndpoint.mGetCpsUser', return_value="ecra"),\
                patch('os.path.exists', return_value=True),\
                 patch('exabox.managment.src.CpsEndpoint.CpsEndpoint.mBashExecution', return_value=(1,"","cps deployer fails")) as spy_bash_exec:
                spy_method.return_value.__enter__.return_value = _mock_exabox_node
                _rc = _endpoint._CpsEndpoint__mCpsOel8Migration(_log_path, _process_id, aCustomArgs=None)
                assert  _rc.get("return_code",0) == 1
                assert  _rc.get("error_code","") == "0x07020014"
                spy_method.return_value.__enter__.return_value.mExecuteCmd.assert_called_once_with("/usr/bin/sudo -n /bin/timeout --signal=SIGKILL 20s /usr/local/bin/imagehistory")
                spy_bash_exec.assert_called_once_with(['/usr/bin/sudo', '-n', 
                                                       '/opt/oci/exacc/exacloud/deployer/ocps-full/cps-exacc-dpy', 
                                                       '--action', 'oel8migr','--reset_history',
                                                       '-t', '/opt/oci/config_bundle/rack.ocpsSetup.json'], 
                                                       aRedirect=ANY)
        if _log_fd:
            os.close(_log_fd)

    def test_007_CpsOel8Migration_RunMigration_Sanity_Fails(self):
        """
        Scenario: Failed cps sanity postcheck after cps sw oel migration
        Given: Request for run oel 8 migration
        When: cps sw oel 8 migrations succeeded
        and cps sanity post check migration fails
        Then: Migration should fail
        """
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _body = {
            "type": "cpsoel8migr", 
            "bundle": "LATEST"       
            }
        _response = {}
        _endpoint = CpsEndpoint(None, _body, _response, _shared)
        _log_fd, _log_path = tempfile.mkstemp()
        _process_id = str(uuid.uuid1(clock_seq=1))
        remote_cps="remotecps02"
        _mockAttrs = { "mGetExacloudConfigValue.return_value":remote_cps,
                      "mGetConfigValue.side_effect":[
                          "/opt/oci/exacc/exacloud",
                          "/opt/oci/config_bundle/rack.ocpsSetup.json"]}
        _mockConfig = Mock(**_mockAttrs)
        img_hist_content="""
Version                              : 22.1.13.0.0.230712
Image activation date                : 2023-08-08 09:37:35 +0000
Imaging mode                         : patch
Imaging status                       : success

Version                              : 22.1.24.0.0.240601
Image activation date                : 2024-07-23 14:24:06 +0000
Imaging mode                         : patch
Imaging status                       : success

Version                              : 23.1.15.0.0.240605
Image activation date                : 2024-07-16 05:04:57 +0000
Imaging mode                         : patch
Imaging status                       : success
"""
        _mock_exabox_node = Mock(**{
            "mGetCmdExitStatus.return_value":1, 
            "mExecuteCmd.return_value": (1,
                                         io.StringIO("Sanity error"),
                                         io.StringIO("Sanit error")), 
                                         "mConnect.return_value": None, 
                                         "mDisconnect.return_value": None}
                                         )
        with patch.object(moduleInstance,"connect_to_host") as spy_method:
            with patch('exabox.managment.src.CpsEndpoint.CpsEndpoint.mGetConfig', return_value=_mockConfig),\
                patch('exabox.managment.src.CpsEndpoint.CpsEndpoint.mGetCpsUser', return_value="ecra"),\
                patch('exabox.managment.src.CpsEndpoint.CpsEndpoint.extract_image_history_from_cps', return_value=(0, img_hist_content)) as spy_method2,\
                patch('os.path.exists', return_value=True),\
                patch('exabox.managment.src.CpsEndpoint.CpsEndpoint.mBashExecution', side_effect=[(0,"",""),(1,"oel 8 migration sanity fails","oel 8 migration sanity fails")]) as spy_bash_exec:
                spy_method.return_value.__enter__.return_value = _mock_exabox_node
                _rc = _endpoint._CpsEndpoint__mCpsOel8Migration(_log_path, _process_id, aCustomArgs=None)
                assert  _rc.get("return_code",0) == 1
                assert  _rc.get("error_code","") == "0x07020015"
                spy_method.return_value.__enter__.return_value.mExecuteCmd.assert_called_once_with(self.get_sanity_cmd())
                spy_method2.assert_called_once_with(remote_cps)
                calls = [
                    call(['/usr/bin/sudo', '-n', '/opt/oci/exacc/exacloud/deployer/ocps-full/cps-exacc-dpy', 
                          '--action', 'oel8migr','--reset_history',
                          '-t', '/opt/oci/config_bundle/rack.ocpsSetup.json'], 
                          aRedirect=ANY)
                ]
                spy_bash_exec.assert_has_calls(calls)
        if _log_fd:
            os.close(_log_fd)
    

    def test_008_CpsOel8Migration_RunMigration_Sanity(self):
        """
        Scenario: Run oel 8 migration on non OS upgraded cps
        Given: Request for run oel 8 migration
        When: The image history on cps-standby meet the migration
              conditions
            and cps sw migration succeeded
            and cps sanity migration post-check succeeded
        Then: Migration should success
        """
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _body = {
            "type": "cpsoel8migr", 
            "bundle": "LATEST"       
            }
        _response = {}
        _endpoint = CpsEndpoint(None, _body, _response, _shared)
        _log_fd, _log_path = tempfile.mkstemp()
        _process_id = str(uuid.uuid1(clock_seq=1))
        remote_cps="remotecps02"
        _mockAttrs = { "mGetExacloudConfigValue.return_value":remote_cps,
                      "mGetConfigValue.side_effect":[
                          "/opt/oci/exacc/exacloud",
                          "/opt/oci/config_bundle/rack.ocpsSetup.json"]}
        _mockConfig = Mock(**_mockAttrs)
        img_hist_content="""
Version                              : 22.1.13.0.0.230712
Image activation date                : 2023-08-08 09:37:35 +0000
Imaging mode                         : patch
Imaging status                       : success

Version                              : 22.1.24.0.0.240601
Image activation date                : 2024-07-23 14:24:06 +0000
Imaging mode                         : patch
Imaging status                       : success

Version                              : 23.1.15.0.0.240605
Image activation date                : 2024-07-16 05:04:57 +0000
Imaging mode                         : patch
Imaging status                       : success
"""
        _mock_exabox_node = Mock(**{
            "mGetCmdExitStatus.return_value":0, 
            "mExecuteCmd.return_value": (0,
                                         io.StringIO(img_hist_content),
                                         io.StringIO()), 
                                         "mConnect.return_value": None, 
                                         "mDisconnect.return_value": None}
                                         )
        with patch.object(moduleInstance,"connect_to_host") as spy_method:
            with patch('exabox.managment.src.CpsEndpoint.CpsEndpoint.mGetConfig', return_value=_mockConfig),\
                patch('exabox.managment.src.CpsEndpoint.CpsEndpoint.mGetCpsUser', return_value="ecra"),\
                patch('os.path.exists', return_value=True),\
                patch('exabox.managment.src.CpsEndpoint.CpsEndpoint.extract_image_history_from_cps', return_value=(0, img_hist_content)) as spy_method2,\
                patch('exabox.managment.src.CpsEndpoint.CpsEndpoint.mBashExecution', return_value=(0,"","")) as spy_bash_exec:
                spy_method.return_value.__enter__.return_value = _mock_exabox_node
                _rc = _endpoint._CpsEndpoint__mCpsOel8Migration(_log_path, _process_id, aCustomArgs=None)
                assert  _rc == 0
                spy_method.return_value.__enter__.return_value.mExecuteCmd.assert_called_once_with(self.get_sanity_cmd())
                spy_method2.assert_called_once_with(remote_cps)
                calls = [
                    call(['/usr/bin/sudo', '-n', '/opt/oci/exacc/exacloud/deployer/ocps-full/cps-exacc-dpy', 
                          '--action', 'oel8migr','--reset_history',
                          '-t', '/opt/oci/config_bundle/rack.ocpsSetup.json'], 
                          aRedirect=ANY)
                ]
                spy_bash_exec.assert_has_calls(calls)
        if _log_fd:
            os.close(_log_fd)

    def test_009_CpsOel8Migration_RunMigration_Sanity_exadata_24(self):
        """
        Scenario: Run oel 8 migration on non OS upgraded cps and cps is exadata 24 based
        Given: Request for run oel 8 migration
        When: The image history on cps-standby meet the migration
              conditions
            and cps sw migration succeeded
            and cps sanity migration post-check succeeded
        Then: Migration should success
        """
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _body = {
            "type": "cpsoel8migr", 
            "bundle": "LATEST"       
            }
        _response = {}
        _endpoint = CpsEndpoint(None, _body, _response, _shared)
        _log_fd, _log_path = tempfile.mkstemp()
        _process_id = str(uuid.uuid1(clock_seq=1))
        remote_cps="remotecps02"
        _mockAttrs = { "mGetExacloudConfigValue.return_value":remote_cps,
                      "mGetConfigValue.side_effect":[
                          "/opt/oci/exacc/exacloud",
                          "/opt/oci/config_bundle/rack.ocpsSetup.json"]}
        _mockConfig = Mock(**_mockAttrs)
        img_hist_content="""
Version                              : 22.1.13.0.0.230712
Image activation date                : 2023-08-08 09:37:35 +0000
Imaging mode                         : patch
Imaging status                       : success

Version                              : 22.1.24.0.0.240601
Image activation date                : 2024-07-23 14:24:06 +0000
Imaging mode                         : patch
Imaging status                       : success

Version                              : 24.1.8.0.0.250208
Exadata Live Update Version          : n/a
Image activation date                : 2025-03-07 18:09:53 -0800
Imaging mode                         : patch
Imaging status                       : success
"""
        _mock_exabox_node = Mock(**{
            "mGetCmdExitStatus.return_value":0, 
            "mExecuteCmd.return_value": (0,
                                         io.StringIO(img_hist_content),
                                         io.StringIO()), 
                                         "mConnect.return_value": None, 
                                         "mDisconnect.return_value": None}
                                         )
        with patch.object(moduleInstance,"connect_to_host") as spy_method:
            with patch('exabox.managment.src.CpsEndpoint.CpsEndpoint.mGetConfig', return_value=_mockConfig),\
                patch('exabox.managment.src.CpsEndpoint.CpsEndpoint.mGetCpsUser', return_value="ecra"),\
                patch('os.path.exists', return_value=True),\
                patch('exabox.managment.src.CpsEndpoint.CpsEndpoint.extract_image_history_from_cps', return_value=(0, img_hist_content)) as spy_method2,\
                patch('exabox.managment.src.CpsEndpoint.CpsEndpoint.mBashExecution', return_value=(0,"","")) as spy_bash_exec:
                spy_method.return_value.__enter__.return_value = _mock_exabox_node
                _rc = _endpoint._CpsEndpoint__mCpsOel8Migration(_log_path, _process_id, aCustomArgs=None)
                assert  _rc == 0
                spy_method.return_value.__enter__.return_value.mExecuteCmd.assert_called_once_with(self.get_sanity_cmd())
                spy_method2.assert_called_once_with(remote_cps)
                calls = [
                    call(['/usr/bin/sudo', '-n', '/opt/oci/exacc/exacloud/deployer/ocps-full/cps-exacc-dpy', 
                          '--action', 'oel8migr','--reset_history',
                          '-t', '/opt/oci/config_bundle/rack.ocpsSetup.json'], 
                          aRedirect=ANY)
                ]
                spy_bash_exec.assert_has_calls(calls)
        if _log_fd:
            os.close(_log_fd)
    

    def test_010_extract_image_history_from_cps(self): 
        """
        Scenario: Extract image history from cps
        When: Run migration
            and check image history
        Then: return image history from cps and 
         and return code should succeed
        """
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _body = {
            "type": "cpsoel8migr", 
            "bundle": "LATEST"       
            }
        _response = {}
        _endpoint = CpsEndpoint(None, _body, _response, _shared)
        remote_cps="remotecps02"
        img_hist_content="""
Version                              : 22.1.13.0.0.230712
Image activation date                : 2023-08-08 09:37:35 +0000
Imaging mode                         : patch
Imaging status                       : success

Version                              : 22.1.24.0.0.240601
Image activation date                : 2024-07-23 14:24:06 +0000
Imaging mode                         : patch
Imaging status                       : success

Version                              : 24.1.8.0.0.250208
Exadata Live Update Version          : n/a
Image activation date                : 2025-03-07 18:09:53 -0800
Imaging mode                         : patch
Imaging status                       : success
"""
        _mock_exabox_node = Mock(**{
            "mGetCmdExitStatus.return_value":0, 
            "mExecuteCmd.return_value": (0,
                                         io.StringIO(img_hist_content),
                                         io.StringIO()), 
                                         "mConnect.return_value": None, 
                                         "mDisconnect.return_value": None}
                                         )
        with patch.object(moduleInstance,"connect_to_host") as spy_method:
            spy_method.return_value.__enter__.return_value = _mock_exabox_node
            _rc, sysresult = _endpoint.extract_image_history_from_cps(remote_cps)
            self.assertEqual(_rc, 0)
            self.assertIsNotNone(sysresult)
            spy_method.return_value.__enter__.return_value.mExecuteCmd.assert_called_once_with("/usr/bin/sudo -n /bin/timeout --signal=SIGKILL 20s /usr/local/bin/imagehistory")



    def test_011_extract_image_history_from_cps_fail(self): 
        """
        Scenario: Extract image history from cps
        When: Run migration
            and  image history fails
        Then:  return code should fail 
        """
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _body = {
            "type": "cpsoel8migr", 
            "bundle": "LATEST"       
            }
        _response = {}
        _endpoint = CpsEndpoint(None, _body, _response, _shared)
        remote_cps="remotecps02"
        img_hist_content=""" Image history failure"""
        _mock_exabox_node = Mock(**{
            "mGetCmdExitStatus.return_value":1, 
            "mExecuteCmd.return_value": (1,
                                         io.StringIO(img_hist_content),
                                         io.StringIO(img_hist_content)), 
                                         "mConnect.return_value": None, 
                                         "mDisconnect.return_value": None}
                                         )
        with patch.object(moduleInstance,"connect_to_host") as spy_method:
            spy_method.return_value.__enter__.return_value = _mock_exabox_node
            _rc, sysresult = _endpoint.extract_image_history_from_cps(remote_cps)
            self.assertNotEqual(_rc, 0)
            self.assertIsNotNone(sysresult)
            spy_method.return_value.__enter__.return_value.mExecuteCmd.assert_called_once_with("/usr/bin/sudo -n /bin/timeout --signal=SIGKILL 20s /usr/local/bin/imagehistory")



    
    @staticmethod
    def get_sanity_cmd():
        return "/usr/bin/sudo -n /opt/oci/exacc/sanity/python3/bin/python /opt/oci/exacc/sanity/sanity_tests/sanity_driver.py -c /opt/oci/exacc/sanity/config/sanityconfig.conf -d 4 -p  --cpssw_oel8migr_postcheck"

if __name__ == '__main__':
    unittest.main(warnings='ignore')
