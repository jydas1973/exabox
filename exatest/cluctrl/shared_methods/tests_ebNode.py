"""

 $Header: 

 Copyright (c) 2018, 2024, Oracle and/or its affiliates.

 NAME:
      tests_ebNode.py - Unitest for ebNode on clucontrol

 DESCRIPTION:
      Run tests for the method of ebNode on clucontrol

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
       jfsaldan 03/21/24 - Bug 36004327 - EXACS: PROVISIONING FAILED WITH
                           EXACLOUD ERROR CODE: 276 EXACLOUD : TIMEOUT WHILE
                           WAITING FOR ASM TO BE RUNNING. ABORTING

        jesandov    07/27/18 - Creation of the file for xmlpatching
"""

import unittest
import re
import shlex
import subprocess

from random import shuffle
from unittest.mock import patch, Mock


from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import MockCommand, exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.sysimghandler import copyVMImageVersionToDom0IfMissing
from exabox.tools.AttributeWrapper import wrapStrBytesFunctions

GRID_PATH = "/u01/app/18.1.0.0/grid"
class ebTestNode(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(False, False)    
 
    def test_000_pair(self):

        _pair = self.mGetClubox().mReturnDom0DomUPair()
        _realpair = [['scaqab10adm01.us.oracle.com', 'scaqab10client01vm08.us.oracle.com'], \
                     ['scaqab10adm02.us.oracle.com', 'scaqab10client02vm08.us.oracle.com']]

        self.assertEqual(_pair, _realpair)

    def test_002_instance(self):
        #Create args structure
        _cmds = {
            self.mGetRegexVm(): [
                [
                    #CRS Check
                    exaMockCommand("tac /etc/oratab | grep -v ASM", aStdout="dborc19_unique:/u02/app/oracle/product/19.0.0.0/dbhome_2:Y"),
                    exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'"), aStdout=GRID_PATH, aPersist=True),
                    exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/18.1.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                    exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/18.1.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/grid" ,aPersist=True),
                    exaMockCommand("check cluster -all | grep -c online", aRc=0),
                    
                ],
                [
                    #ASM Check
                    exaMockCommand('/u01/app/18.1.0.0/grid/bin/crsctl query css votedisk | grep "Located 5 voting disk"', aRc=0, aStdout="", aPersist=True),
                    exaMockCommand(re.escape("cat /etc/oratab | grep '^+ASM.*' | cut -f 2 -d ':'"), aStdout=GRID_PATH),
                    exaMockCommand("/bin/srvctl status asm | grep 'ASM is running on'", aStdout="ASM is running on x,y"),
                    exaMockCommand("/bin/srvctl status filesystem | grep 'is mounted on nodes'", aStdout="is mounted on nodes on x,y"),
                    exaMockCommand("/bin/crsctl check cluster | grep -c online ", aRc=0, aStdout="", aPersist=True)
                ],
                [
                    #DB Check
                    exaMockCommand("tac /etc/oratab | grep -v ASM", aStdout="dborc19_unique:/u02/app/oracle/product/19.0.0.0/dbhome_2:Y"),
                    exaMockCommand(re.escape("cat /etc/oratab | grep '^+ASM.*' | cut -f 2 -d ':'"), aStdout=GRID_PATH, aPersist=True),
                    exaMockCommand("check cluster | grep -c online", aRc=0),
                    exaMockCommand("status database -d .*  | grep -c \"is running\"", aRc=0),
                ],
                [
                    exaMockCommand(re.escape("cat /etc/oratab | grep '^+ASM.*' | cut -f 2 -d ':'"), aStdout=GRID_PATH),
                    exaMockCommand(GRID_PATH+"/bin/srvctl  status asm", aRc=0, aStdout="ASM is running on scaqab10client01vm08,scaqab10client02vm08", aPersist=True),
                    exaMockCommand(GRID_PATH+"/bin/srvctl status asm | grep 'ASM is running on'", aRc=0, aStdout="ASM is running on scaqab10client01vm08,scaqab10client02vm08", aPersist=True),
                    exaMockCommand(GRID_PATH+"/bin/srvctl  status filesystem", aRc=0, aStdout="is mounted on nodes on scaqab10client01vm08,scaqab10client02vm08", aPersist=True),
                    exaMockCommand(GRID_PATH+"/bin/srvctl status filesystem | grep 'is mounted on nodes'", aRc=0, aStdout="is mounted on nodes on scaqab10client01vm08,scaqab10client02vm08", aPersist=True),
                ],
                [
                    exaMockCommand("tac /etc/oratab | grep -v ASM", aStdout="dborc19_unique:/u02/app/oracle/product/19.0.0.0/dbhome_2:Y"),
                    exaMockCommand(re.escape("cat /etc/oratab | grep '^dborc19_unique.*' | cut -f 2 -d ':'"), aRc=0, aStdout="/u02/app/oracle/product/19.0.0.0/dbhome_2", aPersist=True),
                    exaMockCommand('export ORACLE_HOME=/u02/app/oracle/product/19.0.0.0/dbhome_2; /u02/app/oracle/product/19.0.0.0/dbhome_2/bin/srvctl status database -d dborc19_unique | grep -c "is running" | grep -w 2', aRc=0, aStdout="2", aPersist=True)
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        #Execute the clucontrol function
        self.mGetClubox().mCheckDBInstanceIsUp(aOptions=None)

    def test_003_instance_2(self):
        #Create args structure
        _cmds = {
            self.mGetRegexVm(): [
                [
                    #CRS Check
                    exaMockCommand("tac /etc/oratab | grep -v ASM", aStdout="dborc19_unique:/u02/app/oracle/product/19.0.0.0/dbhome_2:Y"),
                    exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'"), aStdout=GRID_PATH, aPersist=True),
                    exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/18.1.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                    exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/18.1.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/grid" ,aPersist=True),
                    exaMockCommand("check cluster -all | grep -c online", aRc=0),
                ],
                [
                    #ASM Check
                    exaMockCommand('/u01/app/18.1.0.0/grid/bin/crsctl query css votedisk | grep "Located 5 voting disk"', aRc=0, aStdout="", aPersist=True),
                    exaMockCommand(re.escape("cat /etc/oratab | grep '^+ASM.*' | cut -f 2 -d ':'"), aStdout=GRID_PATH),
                    exaMockCommand("/bin/srvctl status asm | grep 'ASM is running on'", aStdout="ASM is running on x,y"),
                    exaMockCommand("/bin/srvctl status filesystem | grep 'is mounted on nodes'", aStdout="is mounted on nodes on x,y"),
                    exaMockCommand("crsctl check cluster | grep -c online ", aRc=0, aStdout="", aPersist=True)

                ],
                [
                    #DB Check
                    exaMockCommand("tac /etc/oratab | grep -v ASM", aStdout="dborc19_unique:/u02/app/oracle/product/19.0.0.0/dbhome_2:Y"),
                    exaMockCommand(re.escape("cat /etc/oratab | grep '^+ASM.*' | cut -f 2 -d ':'"), aStdout=GRID_PATH),
                    exaMockCommand("check cluster -all | grep -c online", aRc=1),
                    exaMockCommand("check cluster -all | grep -c online", aRc=0),
                    exaMockCommand(re.escape("cat /etc/oratab | grep '^+ASM.*' | cut -f 2 -d ':'"), aStdout="/u01/app/18.1.0.0/dbAnastasia"),
                    exaMockCommand("status database -d .*  | grep -c \"is running\"", aRc=0),
                    exaMockCommand(GRID_PATH+"/bin/srvctl  status asm", aRc=0, aStdout="ASM is running on scaqab10client01vm08,scaqab10client02vm08", aPersist=True),
                    exaMockCommand(GRID_PATH+"/bin/srvctl status asm | grep 'ASM is running on'", aRc=0, aStdout="ASM is running on scaqab10client01vm08,scaqab10client02vm08", aPersist=True),
                    exaMockCommand(GRID_PATH+"/bin/srvctl  status filesystem", aRc=0, aStdout="is mounted on nodes on scaqab10client01vm08,scaqab10client02vm08", aPersist=True),
                    exaMockCommand(GRID_PATH+"/bin/srvctl status filesystem | grep 'is mounted on nodes'", aRc=0, aStdout="is mounted on nodes on scaqab10client01vm08,scaqab10client02vm08", aPersist=True)

                ],
                [
                    exaMockCommand(re.escape("cat /etc/oratab | grep '^+ASM.*' | cut -f 2 -d ':'"), aStdout=GRID_PATH),
                    exaMockCommand(GRID_PATH+"/bin/srvctl  status asm", aRc=0, aStdout="ASM is running on scaqab10client01vm08,scaqab10client02vm08", aPersist=True),
                    exaMockCommand(GRID_PATH+"/bin/srvctl status asm | grep 'ASM is running on'", aRc=0, aStdout="ASM is running on scaqab10client01vm08,scaqab10client02vm08", aPersist=True),
                    exaMockCommand(GRID_PATH+"/bin/srvctl  status filesystem", aRc=0, aStdout="is mounted on nodes on scaqab10client01vm08,scaqab10client02vm08", aPersist=True),
                    exaMockCommand(GRID_PATH+"/bin/srvctl status filesystem | grep 'is mounted on nodes'", aRc=0, aStdout="is mounted on nodes on scaqab10client01vm08,scaqab10client02vm08", aPersist=True),

                ],
                [
                    exaMockCommand("tac /etc/oratab | grep -v ASM", aStdout="dborc19_unique:/u02/app/oracle/product/19.0.0.0/dbhome_2:Y"),
                    exaMockCommand(re.escape("cat /etc/oratab | grep '^dborc19_unique.*' | cut -f 2 -d ':'"), aRc=0, aStdout="/u02/app/oracle/product/19.0.0.0/dbhome_2", aPersist=True),
                    exaMockCommand('export ORACLE_HOME=/u02/app/oracle/product/19.0.0.0/dbhome_2; /u02/app/oracle/product/19.0.0.0/dbhome_2/bin/srvctl status database -d dborc19_unique | grep -c "is running" | grep -w 2', aRc=0, aStdout="2", aPersist=True)
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        #Execute the clucontrol function
        self.mGetClubox().mCheckDBInstanceIsUp(aOptions=None)

    def test_005_async(self):

        #Test results
        _cellG = ["0x0010e00001c565e1", "0x0010e00001c565e2"]
        _dom0G = ["0x0010e00001944191", "0x0010e00001944192"]

        #Create args structure
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("ibstat | grep 'Port GUID'", aStdout="Port GUID: {0}\nPort GUID: {1}".format(_cellG[0], _cellG[1]))
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("ibstat | grep 'Port GUID'", aStdout="Port GUID: {0}\nPort GUID: {1}".format(_dom0G[0], _dom0G[1]))
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        #Execute the clucontrol function
        _guids = self.mGetClubox().mGetAllGUID()

        #Asserts
        _dom0s, _, _cells, _ = self.mGetClubox().mReturnAllClusterHosts()
        for _host in _guids:

            if _host in _cells:
                for _cellGuid in _cellG:
                    self.assertTrue(_cellGuid in _guids[_host])

            elif _host in _dom0s:
                for _dom0Guid in _dom0G:
                    self.assertTrue(_dom0Guid in _guids[_host])


    def test_006_custome_fx(self):

        #Create args structure
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("cat myos", aStdout="cell")
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("cat myos", aStdout="dom0")
                ]
            ],
            self.mGetRegexVm(): [
                [
                    exaMockCommand("cat myos", aStdout="vm")
                ]
            ],
            self.mGetRegexSwitch(): [
                [
                    exaMockCommand("cat myos", aStdout="sw")
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        #Execute the clucontrol function
        _dom0s, _domUs, _cells, _switches = self.mGetClubox().mReturnAllClusterHosts()
        _hosts = _dom0s + _domUs + _cells + _switches
        shuffle(_hosts)

        for _host in _hosts:
            _node = exaBoxNode(self.mGetContext())
            _node.mConnect(aHost=_host)
            _os = _node.mSingleLineOutput("cat myos")
            _node.mDisconnect()

            if _host in _dom0s:
                self.assertEqual(_os, "dom0")

            elif _host in _domUs:
                self.assertEqual(_os, "vm")

            elif _host in _cells:
                self.assertEqual(_os, "cell")

            elif _host in _switches:
                self.assertEqual(_os, "sw")

    def test_008_multiple_connect(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("echo 0", aStdout="0")
                ],
                [
                    exaMockCommand("echo 1", aStdout="1")
                ],
                [
                    exaMockCommand("echo 2", aStdout="2")
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        #Execute the clucontrol function
        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            # Instance No. 0
            _node = exaBoxNode(self.mGetContext())
            _node.mConnect(aHost=_dom0)
            _out = _node.mSingleLineOutput("echo 0")
            self.assertEqual(_out, "0")
            _node.mDisconnect()

            # Instance No. 1
            _node = exaBoxNode(self.mGetContext())
            _node.mConnect(aHost=_dom0)
            _out = _node.mSingleLineOutput("echo 1")
            self.assertEqual(_out, "1")
            _node.mDisconnect()

            # Instance No. 2
            _node = exaBoxNode(self.mGetContext())
            _node.mConnect(aHost=_dom0)
            _out = _node.mSingleLineOutput("echo 2")
            self.assertEqual(_out, "2")
            _node.mDisconnect()

    def test_009_mCopyFile(self):

        def mRealExecute(aCmd, aStdIn):

            _cmd = aCmd
            if _cmd.startswith("/bin/scp"):
                _cmd = _cmd.replace("/bin/scp", "/bin/cp")

            _args = shlex.split(_cmd)

            _proc = subprocess.Popen(_args, \
                                     stdin=subprocess.PIPE, \
                                     stdout=subprocess.PIPE, \
                                     stderr=subprocess.PIPE,
                                     cwd=".")

            _stdout, _stderr = wrapStrBytesFunctions(_proc).communicate()
            _rc = _proc.returncode

            return _rc, _stdout, _stderr

        #Create args structure
        _cmds = {
            self.mGetRegexLocal(): [
                [
                    MockCommand(".*touch.*", mRealExecute),
                    MockCommand(".*ls.*", mRealExecute),
                    MockCommand(".*scp.*", mRealExecute),
                    MockCommand(".*bin/test.*", mRealExecute),
                    MockCommand(".*sha256sum.*", mRealExecute),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        # Execute the clucontrol function
        _node = exaBoxNode(self.mGetContext(),aLocal=True)
        _node.mConnect(aHost="locahost")
        _out = _node.mSingleLineOutput("touch /tmp/test.txt")

        _out = _node.mSingleLineOutput("ls /tmp/test*")

        _out = _node.mCopyFile(
            "/tmp/test.txt",
            "/tmp/test1.txt")

        _node.mDisconnect()

    def test_010_mCopyFile_Retry(self):

        def mRealExecute(aCmd, aStdIn):

            _cmd = aCmd
            if _cmd.startswith("/bin/scp"):
                _cmd = _cmd.replace("/bin/scp", "/bin/cp")

            _args = shlex.split(_cmd)

            _proc = subprocess.Popen(_args, \
                                     stdin=subprocess.PIPE, \
                                     stdout=subprocess.PIPE, \
                                     stderr=subprocess.PIPE,
                                     cwd=".")

            _stdout, _stderr = wrapStrBytesFunctions(_proc).communicate()
            _rc = _proc.returncode

            return _rc, _stdout, _stderr

        #Create args structure
        _cmds = {
            self.mGetRegexLocal(): [
                [
                    MockCommand(".*touch.*", mRealExecute),
                    MockCommand(".*ls.*", mRealExecute),
                    exaMockCommand("/bin/scp *", aRc=1), # Forced failure
                    MockCommand(".*bin/test.*", mRealExecute),
                    exaMockCommand("sha256sum *", aRc=1), # Forced failure
                    MockCommand(".*bin/scp.*", mRealExecute),
                    MockCommand(".*bin/test.*", mRealExecute),
                    MockCommand("sha256sum.*", mRealExecute),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        # Execute the clucontrol function
        _node = exaBoxNode(self.mGetContext(),aLocal=True)
        _node.mConnect(aHost="locahost")
        _out = _node.mSingleLineOutput("touch /tmp/test.txt")

        _out = _node.mSingleLineOutput("ls /tmp/test*")
        
        _out = _node.mCopyFile(
            "/tmp/test.txt",
            "/tmp/test1.txt",
            1)

        _node.mDisconnect()

if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end file
