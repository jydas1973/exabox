#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/tools/tests_exa_regions.py /main/4 2025/04/23 04:55:22 aypaul Exp $
#
# tests_exa_regions.py
#
# Copyright (c) 2023, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_exa_regions.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ririgoye    10/25/23 - Bug 35919782 - Unit tests for instance principals
#                           retried
#    gparada     03/14/23 - Creation (test_exa_regions)
#    gparada     03/14/23 - Creation
#

import os
import shlex
import unittest
import urllib
import exabox.utils.common 

from unittest import mock
from unittest.mock import patch, mock_open
from urllib.request import urlopen 

from exabox.core.DBStore import ebGetDefaultDB
from exabox.core.Node import exaBoxNode
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Context import get_gcontext

from exabox.utils.ExaRegion import (get_region_info, get_region,
    is_r1_region, get_canonical_region_name, _handle_url_req,
    get_instance_root_compartment)

URLError = urllib.error.URLError
HTTPError = urllib.error.HTTPError

class TestExaRegions(ebTestClucontrol):

    @classmethod
    def setUpClass(self):        
        super().setUpClass(aGenerateDatabase=True)
        self._db = ebGetDefaultDB()
        self._realmKey = "oc1"
        self._realmDomainComponent = "oraclecloud.com"
        self._regionKey ="PHX"
        self._regionIdentifier = "us-phoenix-1"


    def test_get_region_info_URLError(self):    
        get_gcontext().mSetRegEntry("exaregion_information", {})    
        _str_URLError = "http://badurl.com/opc/v1/instance"        
        _region_info = get_region_info(_str_URLError)
        self.assertIsNone(_region_info)

    def test_get_region_info_HttpError(self):
        get_gcontext().mSetRegEntry("exaregion_information", {})
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.HTTPError('url', 404, 'Not Found', {}, None)
            _region_info = get_region_info()
        self.assertIsNone(_region_info)


    def test_get_region_info(self):
        _region_info = get_region_info(None)
        self.assertIsNotNone(_region_info)
        self.assertEqual(self._realmKey, _region_info["realmKey"])
        self.assertEqual(self._realmDomainComponent, _region_info["realmDomainComponent"])
        self.assertEqual(self._regionKey, _region_info["regionKey"])
        self.assertEqual(self._regionIdentifier, _region_info["regionIdentifier"])
        # curl --noproxy '*' http://169.254.169.254/opc/v1/instance


    @patch("exabox.utils.ExaRegion.json.loads", return_value={
            "realmDomainComponent": "oraclecloud.com",
            "realmKey": "region1",
            "regionIdentifier": "us-phoenix-1",
            "regionKey": "PHX"
        })
    def test_get_region_info_alt(self,json_loads_mock):
        _region_info = get_region_info(None)
        self.assertIsNotNone(_region_info)
        self.assertEqual(_region_info["realmKey"],"R1_ENVIRONMENT")

    def test_get_region(self):
        _region_info = get_region_info(None)
        self.assertIsNotNone(_region_info)

    def test_negative_is_r1_region(self):
        _is_r1 = is_r1_region()
        self.assertFalse(_is_r1)


    def test_positive_is_r1_region(self):
        mock_get_region = mock.Mock(return_value="sea")
        original_function = exabox.utils.ExaRegion.get_region
        exabox.utils.ExaRegion.get_region = mock_get_region
        _is_r1 = is_r1_region()
        mock_get_region.assert_called_once()
        self.assertTrue(_is_r1)
        exabox.utils.oci_region.get_region = original_function

    def test_get_canonical_region_name(self):
        _canonical_region_name = get_canonical_region_name(None)
        self.assertIsNotNone(_canonical_region_name)

    @patch('urllib.request.urlopen')
    def test_one_retry_and_success(self, mock_urlopen):
        # Simulate a single retry before success
        get_gcontext().mSetRegEntry("exaregion_information", {})
        http_err = urllib.error.HTTPError('url', 404, 'Not Found', {}, None)
        mock_urlopen.side_effect = [http_err, http_err, mock.Mock()]
        _region_info = get_region_info()
        self.assertEqual(mock_urlopen.call_count, 3)

    @patch('urllib.request.urlopen')
    def test_get_instance_compartment_retry(self, mock_urlopen):

        _ocid = "ocid1.tenancy.oc1..aaaaaaaakqhkiuvchkoxuxgpax4zcieeizobkzmszhegyaaqx3fkiyjzwkrq'"
        mock_response = mock_open(read_data=_ocid.encode()).return_value
        mock_urlopen.return_value = mock_response
        self.assertEqual(_ocid, get_instance_root_compartment())


    def test_get_region_info_fromcache(self):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.HTTPError('url', 404, 'Not Found', {}, None)
            _region_info = get_region_info()
        self.assertIsNotNone(_region_info)

if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end of file
