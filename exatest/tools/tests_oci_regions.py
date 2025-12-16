#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/tools/tests_oci_regions.py /main/3 2023/04/03 15:33:47 gparada Exp $
#
# tests_oci_regions.py
#
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.
#
#    NAME
#      tests_oci_regions.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    gparada     02/24/23 - Add missing test case for region checking
#    ndesanto    04/13/22 - Retrieve region directly from cavium.
#    ndesanto    01/13/22 - Tests for oci regions file.
#    ndesanto    01/13/22 - Creation
#

import os
import shlex
import unittest

import exabox.utils.common 

from unittest import mock
from unittest.mock import patch, Mock

from exabox.core.DBStore import ebGetDefaultDB
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

from exabox.utils.oci_region import get_oci_config, update_oci_config, \
    load_oci_region_config, parse_region_info, load_config_bundle
from exabox.core.Error import ExacloudRuntimeError
 
class TestOciRegions(ebTestClucontrol):

    @classmethod
    def setUpClass(self):        
        super().setUpClass(aGenerateDatabase=True)
        self._db = ebGetDefaultDB()
        self._realmKey = "TestRealmKey"
        self._realmDomainComponent = "TestRealmDomain"
        self._regionKey ="TestRegionKey"
        self._regionIdentifier = "TestRegionIdentifier"

        self._r1_realmKey = "R1_ENVIRONMENT"
        self._r1_realmDomainComponent = "oracleiaas.com"
        self._r1_regionKey ="SEA"
        self._r1_regionIdentifier = "r1"


    def test_get_oci_config(self):
        _config = get_oci_config(self._realmKey, self._realmDomainComponent, \
            self._regionKey, self._regionIdentifier)

        self.assertEqual(self._realmKey, _config["realmKey"])
        self.assertEqual(self._realmDomainComponent, _config["realmDomainComponent"])
        self.assertEqual(self._regionKey, _config["regionKey"])
        self.assertEqual(self._regionIdentifier, _config["regionIdentifier"])

    def test_update_oci_config(self):
        _config = get_oci_config(self._realmKey, self._realmDomainComponent, \
            self._regionKey, self._regionIdentifier)

        update_oci_config(_config)

        _loaded = load_oci_region_config()
        self.assertDictEqual(_config, _loaded)

    def test_negative_update_oci_config(self):
        _config = get_oci_config(self._realmKey, self._realmDomainComponent, \
            self._regionKey, self._regionIdentifier)
        with patch('exabox.utils.oci_region._set_region_to_db_cache') as mock_cache:
            mock_cache.side_effect = Mock(side_effect=Exception('TestExc'))
            with self.assertRaises(ExacloudRuntimeError):
                update_oci_config(_config)

    def test_parse_region_info(self):
        _aBase64Msg = "eyJyZWFsbURvbWFpbkNvbXBvbmVudCI6ICJvcmFjbGVpYWFzLmNvbSIsICJyZWFsbUtleSI6ICJSMV9FTlZJUk9OTUVOVCIsICJyZWdpb25JZGVudGlmaWVyIjogInIxIiwgInJlZ2lvbktleSI6ICJTRUEifQ=="
        _region_info = parse_region_info(_aBase64Msg)

        self.assertEqual(self._r1_realmKey, _region_info["realmKey"])
        self.assertEqual(self._r1_realmDomainComponent, _region_info["realmDomainComponent"])
        self.assertEqual(self._r1_regionKey, _region_info["regionKey"])
        self.assertEqual(self._r1_regionIdentifier, _region_info["regionIdentifier"])

    @patch("exabox.utils.oci_region.read_json_into_string", return_value={"a":"b"}) 
    def test_load_config_bundle(self, read_json_into_string_mock):
        _config = load_config_bundle()
        self.assertIsNotNone(_config)

    def test_get_value(self):
        _my_dic: dict = {
            "a": 1, 
            "b": "some b val"
        }
        _val = exabox.utils.oci_region.get_value(_my_dic,"a")
        self.assertEqual(_val, 1)
        _val = exabox.utils.oci_region.get_value(_my_dic,"b","")
        self.assertEqual(_val, "some b val")

    @patch("exabox.utils.oci_region._get_region_from_db_cache", return_value=None)
    def test_load_oci_region_config(self, _get_region_from_db_cache_mock):
        _config = load_oci_region_config() 
        self.assertIsNotNone(_config)

if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end of file