"""

 $Header: 

 Copyright (c) 2018, 2021, Oracle and/or its affiliates. 

 NAME:
      ebTest_vmcontrol.py - Unitest for vmcontrol classes and methods

 DESCRIPTION:
      Run tests for vmcontrol

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
    ndesanto    07/19/19 - File creation
    ndesanto    10/07/19 - Fixing the test
"""

import unittest

from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.vmcontrol import ebVgLifeCycle


class ebTestNode(ebTestClucontrol):

    def test_mDispatchEvent_list(self):

        _xmList = """Name                                        ID   Mem VCPUs      State   Time(s)
Domain-0                                     0  8746     4     r----- 2145201.6
scaqab10adm01vm01.us.oracle.com              1 92163    10     -b---- 811282.1
scaqab10adm01vm03.us.oracle.com              2 92163    10     -b---- 495633.3
scaqab10adm01vm05.us.oracle.com              8 92163    10     -b----  51637.6
scaqab10adm01vm07.us.oracle.com             11 92163    10     -b----  42935.3
scaqab10client01vm02.us.oracle.com           5 92163    10     -b---- 446566.6
"""

        _guestImages = """scaqab10adm01vm01.us.oracle.com
scaqab10adm01vm07.us.oracle.com
scaqab10adm01vm03.us.oracle.com
scaqab10client01vm02.us.oracle.com
scaqab10adm01vm05.us.oracle.com"""

        _domUSet = set(["scaqab10adm01vm01.us.oracle.com", "scaqab10adm01vm03.us.oracle.com", \
                        "scaqab10adm01vm05.us.oracle.com", "scaqab10adm01vm07.us.oracle.com", \
                        "scaqab10client01vm02.us.oracle.com"])

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("imageinfo | grep 'Node type:'"),
                    exaMockCommand("cat /sys/hypervisor/type", aStdout="xen\n")
                ],
                [
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aStdout="xen\n00000000-0000-0000-0000-000000000000\n"), #Xen detected
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages), # vmcontrol standard load
                    exaMockCommand("xm list", aStdout=_xmList), #vmcontrol standard load
                    exaMockCommand("xm list", aStdout=_xmList)  # vm list operation
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        #Execute the clucontrol function
        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            _node = exaBoxNode(self.mGetContext())
            _node.mConnect(aHost=_dom0)

            _vmhandle = ebVgLifeCycle()
            _vmhandle.mSetOVMCtrl(aCtx=get_gcontext(), aNode=_node)
            _vmhandle.mDispatchEvent('list', aOptions=None)

            _node.mDisconnect()
            self.assertEqual(set(_vmhandle.mGetVmCtrl().mGetDomUs()), _domUSet)
            self.assertEqual(set(_vmhandle.mGetVmCtrl().mGetDomUsCfg()), _domUSet)


if __name__ == '__main__':
    unittest.main()
