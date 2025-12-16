#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/vmgi_install/cs_prevmchecks/tests_check_sys_img_consistency.py /main/1 2021/06/03 19:31:07 jlombera Exp $
#
# tests_check_sys_img_consistency.py
#
# Copyright (c) 2021, Oracle and/or its affiliates.
#
#    NAME
#      tests_check_sys_img_consistency.py - Test Sys. Img. consistency check
#
#    DESCRIPTION
#      Test System Image consistency check.
#
#    NOTES
#      - If you change this file, please make sure lines are no longer than 80
#        characters (including newline) and it passes pylint, mypy and flake8
#        with all the default checks enabled.
#
#    MODIFIED   (MM/DD/YY)
#    jlombera    06/01/21 - Bug 32920094: test System Image consistency check
#    jlombera    06/01/21 - Creation
#
"""
Tests for System Image consistency check.
"""
import unittest

from exabox.core.Error import ExacloudRuntimeError
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.csstep.cs_prevmchecks import check_sys_img_version_consistency

VERSIONS = ('1.2.3.4', '1.2.3.5', '2.0.0.5')
HOSTS = ('host1', 'host2', 'host3')
IMG_VER_CMD = '/usr/local/bin/imageinfo -version'


class TestSysImgConsistencyCheck(ebTestClucontrol):
    """Test System Image consistency check"""
    def test_success(self):
        """Test successful check"""
        # all hosts have same system image version
        cmds = {
            HOSTS[0]: [[exaMockCommand(IMG_VER_CMD, aStdout=VERSIONS[0])]],
            HOSTS[1]: [[exaMockCommand(IMG_VER_CMD, aStdout=VERSIONS[0])]],
            HOSTS[2]: [[exaMockCommand(IMG_VER_CMD, aStdout=VERSIONS[0])]]
        }

        self.mPrepareMockCommands(cmds)

        # should finish without raising any exception (return None)
        self.assertIsNone(check_sys_img_version_consistency(
            HOSTS, self.mGetContext()))

    def test_failure(self):
        """Test unsuccessful check"""
        # all hosts have different versions
        cmds = {
            HOSTS[0]: [[exaMockCommand(IMG_VER_CMD, aStdout=VERSIONS[0])]],
            HOSTS[1]: [[exaMockCommand(IMG_VER_CMD, aStdout=VERSIONS[1])]],
            HOSTS[2]: [[exaMockCommand(IMG_VER_CMD, aStdout=VERSIONS[2])]]
        }

        self.mPrepareMockCommands(cmds)

        # should raise exception
        with self.assertRaises(ExacloudRuntimeError):
            check_sys_img_version_consistency(HOSTS, self.mGetContext())

        # one hosts have different version
        cmds = {
            HOSTS[0]: [[exaMockCommand(IMG_VER_CMD, aStdout=VERSIONS[1])]],
            HOSTS[1]: [[exaMockCommand(IMG_VER_CMD, aStdout=VERSIONS[1])]],
            HOSTS[2]: [[exaMockCommand(IMG_VER_CMD, aStdout=VERSIONS[2])]]
        }

        self.mPrepareMockCommands(cmds)

        # should raise exception
        with self.assertRaises(ExacloudRuntimeError):
            check_sys_img_version_consistency(HOSTS, self.mGetContext())

    def test_error(self):
        """Test error during check"""
        # All hosts have same version but an error occurred while retrieving
        # the version in one of them.
        cmds = {
            HOSTS[0]: [[exaMockCommand(IMG_VER_CMD, aStdout=VERSIONS[2])]],
            HOSTS[1]: [
                [exaMockCommand(IMG_VER_CMD, aStdout=VERSIONS[2], aRc=1)]
            ],
            HOSTS[2]: [[exaMockCommand(IMG_VER_CMD, aStdout=VERSIONS[2])]],
        }

        self.mPrepareMockCommands(cmds)

        # should raise exception
        with self.assertRaises(ExacloudRuntimeError):
            check_sys_img_version_consistency(HOSTS, self.mGetContext())


if __name__ == "__main__":
    unittest.main()
