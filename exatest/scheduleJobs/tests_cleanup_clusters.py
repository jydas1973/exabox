#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/scheduleJobs/tests_cleanup_clusters.py /main/1 2024/02/19 06:45:03 aararora Exp $
#
# tests_cleanup_clusters.py
#
# Copyright (c) 2024, Oracle and/or its affiliates.
#
#    NAME
#      tests_cleanup_clusters.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aararora    01/03/24 - Bug 35863722: Cleanup of cluster xml files under
#                           PodRepo directory
#    aararora    01/03/24 - Creation
#
import unittest
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.scheduleJobs.cleanup_clusters import CleanUpClustersFolder

class ebTestCleanupClusters(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestCleanupClusters, self).setUpClass(True,False)

    def test_mExecuteJob(self):
        clean = CleanUpClustersFolder()
        clean.mExecuteJob()

if __name__ == '__main__':
    unittest.main()