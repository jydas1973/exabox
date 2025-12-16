#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/shared_methods/tests_scan_ips.py /main/1 2021/06/14 12:47:49 jlombera Exp $
#
# tests_scan_ips.py
#
# Copyright (c) 2021, Oracle and/or its affiliates.
#
#    NAME
#      tests_scan_ips.py - Scan IPs tests
#
#    DESCRIPTION
#      Tests for exaBoxCluCtrl methods related to Scan IPs.
#
#    NOTES
#      - If you change this file, please make sure lines are no longer than 80
#        characters (including newline) and it passes pylint, mypy and flake8
#        with all the default checks enabled.
#
#    MODIFIED   (MM/DD/YY)
#    jlombera    06/11/21 - Bug 32992276: test exaBoxCluCtrl.mGetScanIps()
#    jlombera    06/11/21 - Creation
#
"""
Tests exaBoxCluCtrl metods related to Scan IPs.
"""
import unittest

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol


class TestScanIPs(ebTestClucontrol):
    """Tests related Scan IPs."""

    def test_scan_ips(self):
        """Test exaBoxCluCtrl.mGetScanIps()."""
        cluctrl = self.mGetClubox()

        # we should get at least one Scan IP
        ips = cluctrl.mGetScanIps()
        self.assertTrue(len(ips) > 0)

        clusterless_xml = \
            'exabox/exatest/cluctrl/shared_methods/clusterless.xml'

        # load clusterless XML
        jsonconf = cluctrl.mGetArgsOptions().jsonconf
        cluctrl.mSetConfigPath(clusterless_xml)
        cluctrl.mParseXMLConfig(jsonconf)

        # we should get 0 Scan IPs for clusterless XML (and shouldn't crash)
        ips = cluctrl.mGetScanIps()
        self.assertEqual(len(ips), 0)


if __name__ == "__main__":
    unittest.main()
