#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_coredump.py /main/1 2022/01/18 16:59:09 alsepulv Exp $
#
# tests_coredump.py
#
# Copyright (c) 2021, Oracle and/or its affiliates.
#
#    NAME
#      tests_coredump.py - Unit test for coredump
#
#    DESCRIPTION
#      Run tests for coredump
#
#    NOTES
#      None
#
#    MODIFIED   (MM/DD/YY)
#    alsepulv    12/06/21 - Creation
#

import unittest

from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

from exabox.ovm.coredump import ebCoredumpUtil, setKvmOnCrash


class ebTestCoredump(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()

    def test_setKvmOnCrash(self):
        _doms = self.mGetClubox().mReturnDom0DomUPair()
        _domU = self.mGetRegexVm()

        # Test virt-xml command failure
        _value = "restart"
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f"/usr/bin/virt-xml {_domU} --edit --event on_crash={_value}",
                                    aRc=1, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        self.assertRaises(ExacloudRuntimeError, lambda: setKvmOnCrash(_doms, _value))

        # Test good command and good value / success
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f"/usr/bin/virt-xml {_domU} --edit --event on_crash={_value}",
                                   aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        setKvmOnCrash(_doms, _value)

        # Test bad value
        _value = "Null"
        self.assertRaises(ExacloudRuntimeError, lambda: setKvmOnCrash(_doms, _value))


    def test_mRunCoredumpUtil(self):
        _script_path = "/opt/exacloud/bin/domU_coredump_util.py"
        _action = "setup"
        _domU = self.mGetRegexVm()
        _mount_target = "/example/path"

        get_gcontext().mSetConfigOption("coredump", "True")
        _payload = self.mGetPayload()
        _payload["coredump"] = {}
        _payload["coredump"]["action"] = _action
        _payload["coredump"]["coredumppath"] = _mount_target
        _doms = self.mGetClubox().mReturnDom0DomUPair()




        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/mkdir -p /opt/exacloud/bin",
                                   aRc=0, aPersist=True),
                    exaMockCommand(f"/bin/scp scripts/domU_coredump_util.py {_script_path}",
                                   aRc=0, aPersist=True),
                    exaMockCommand((f"/usr/bin/python {_script_path} -a {_action} "
                                    f"-hn {_domU} -mt {_mount_target}"),
                                   aRc=0, aStdout=("INFO: Setting up domU core dump\n"
                                   "INFO: Mounting NFS\n"), aPersist=True)
                ]
            ],
            self.mGetRegexVm(): [
                [
                    exaMockCommand(("/bin/systemctl stop kdump.service; "
                                    "/bin/systemctl disable kdump.service"),
                                    aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        _coredumpUtil = ebCoredumpUtil(_doms, _payload)
        _coredumpUtil.mRunCoredumpUtil()


if __name__ == '__main__':
    unittest.main()
