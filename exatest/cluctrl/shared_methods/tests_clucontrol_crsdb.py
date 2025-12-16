"""

 $Header: 

 Copyright (c) 2020, 2025, Oracle and/or its affiliates.

 NAME:
      tests_clucontrol_crsdb.py - Unitest for CRS/DB related funcs in clucontrl

 DESCRIPTION:
      Run tests for the methods of kvmvmmgr.py

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
       avimonda 09/08/25 - Bug 38179586 - OCI: VMLOCALSTORAGE OPERATION FAILED
                           DUE TO RAC ONE DATABASE
       joysjose 03/25/24 - Bug 36430462: Make mCheckCrsUp and mCheckDBIsUp for
                           obtain the GI home path from
                           mGetOracleBaseDirectories instead of mGetGridHome

    vgerard    07/28/20 - Creation of the file
"""

import unittest
import io
import re
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import *
from unittest.mock import patch, MagicMock, PropertyMock, mock_open

_aDBAASCliOut = """DBAAS CLI version MAIN
Executing command grid getDetails
Job id: cffe369d-ba80-4eac-b675-4aaf8c1773b6
Session log: /var/opt/oracle/log/grid/getDetails/dbaastools_2024-03-24_11-33-05-PM_293026.log
{
  "createTime" : 1711130848000,
  "updateTime" : 1711130848000,
  "scanListenerTCPPorts" : [ 1521 ],
  "scanListenerTCPSPorts" : [ 2484 ],
  "diskGroupDetails" : [ {
    "name" : "DATA",
    "redundancy" : "HIGH",
    "totalSize" : "1944GB",
    "freeSpace" : "1941GB"
  }, {
    "name" : "RECO",
    "redundancy" : "HIGH",
    "totalSize" : "468GB",
    "freeSpace" : "466GB"
  }, {
    "name" : "SPR",
    "redundancy" : null,
    "totalSize" : null,
    "freeSpace" : null
  } ],
  "giNodeLevelDetails" : {
    "slcqab02adm04vm07" : {
      "nodeName" : "slcqab02adm04vm07",
      "homePath" : "/u01/app/19.0.0.0/grid",
      "version" : "19.20.0.0.0",
      "status" : null
    },
    "slcqab02adm03vm07" : {
      "nodeName" : "slcqab02adm03vm07",
      "homePath" : "/u01/app/19.0.0.0/grid",
      "version" : "19.20.0.0.0",
      "status" : null
    }
  },
  "messages" : [ ]
}
dbaascli execution completed
"""

_aHaveDBStdout = """NAME=ora.db112265.db
TYPE=ora.database.type
TARGET=ONLINE                  , ONLINE
STATE=ONLINE on scaqak02dv0501, ONLINE on scaqak02dv0601
ROLE=PRIMARY
USR_ORA_OPEN_MODE=open
"""
_aDBStateStdout = """STATE=ONLINE
NAME=ora.db112265.db 2 1
TYPE=ora.database.type
TARGET=ONLINE
STATE=ONLINE
ROLE=PRIMARY
USR_ORA_OPEN_MODE=open
"""
class ebTestCluControlCrsDB(ebTestClucontrol):
    @classmethod
    def setUpClass(self):
        # Surcharge ebTestClucontrol, to specify noDB/noOEDA
        super(ebTestCluControlCrsDB, self).setUpClass()

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetActiveDbInstances', return_value=["DB1"])
    def _checkDBIsUp(self, aMockmGetActiveDbInstances, aHaveDBretCode=0, aHaveDBStdout="",aDBStateStdout=""):

        #Create args structure
        _cmds = {
            self.mGetRegexVm(): [[
                exaMockCommand(re.escape("""cat /var/opt/oracle/creg/grid/grid.ini | grep "^sid" | cut -d '=' -f 2"""),aStdout="BBB"),
                exaMockCommand(re.escape("""cat /var/opt/oracle/creg/grid/grid.ini | grep "^oracle_home" | cut -d '=' -f 2"""),aStdout="/u01/app/19.0.0.0/grid"),
                exaMockCommand(re.escape("""/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':' """),aStdout="/u01/app/19.0.0.0/grid"),
            ], [
                exaMockCommand(re.escape("/u01/app/19.0.0.0/grid/bin/crsctl stat res -w 'TYPE = ora.database.type'"),aStdout=aHaveDBStdout, aRc=aHaveDBretCode),
                exaMockCommand(re.escape("/u01/app/19.0.0.0/grid/bin/crsctl stat res -attr TYPE.*"),aStdout=aDBStateStdout),
                
            ]]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _domU = self.mGetClubox().mReturnDom0DomUPair()[0][1]
        return self.mGetClubox().mCheckDBIsUp(_domU)
      
      
    def _checkgetOracleBaseDir(self):

        #Create args structure
        _cmds = {
            self.mGetRegexVm(): [[
                exaMockCommand(re.escape("""cat /var/opt/oracle/creg/grid/grid.ini | grep "^oracle_home" | cut -d '=' -f 2"""),aStdout="/u01/app/19.0.0.0/grid"),
                exaMockCommand(re.escape("""/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':' """),aStdout="/u01/app/19.0.0.0/grid"),
                exaMockCommand(re.escape("""export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"""),aStdout="19.0.0.0"),
                exaMockCommand(re.escape("""export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"""),aStdout="/u01/app/grid")
            ]]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)
        _domU = self.mGetClubox().mReturnDom0DomUPair()[0][1]
        return self.mGetClubox().mGetOracleBaseDirectories(_domU)
      
    @patch('exabox.ovm.clucontrol.node_exec_cmd', return_value = [0,_aDBAASCliOut,None])
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmd', side_effect = iter([(0,io.StringIO("/u01/app/19.0.0.0/grid"),None),(0,io.StringIO("19.0.0.0.0"),None),(0,io.StringIO("/u01/app/grid"),None)]))
    def test_getOracleHome(self,mock_node_exec,mock_execute):
        self.assertTrue(self._checkgetOracleBaseDir())

    @patch('exabox.ovm.clucontrol.node_exec_cmd', return_value = [0,_aDBAASCliOut,None])
    @patch('exabox.ovm.clucontrol.node_cmd_abs_path_check')
    @patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', return_value=0)
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog')
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmd', side_effect = iter([(0,io.StringIO(""),None),(0,io.StringIO("BBB"),None),(0,io.StringIO(""),None),(0,io.StringIO("/u01/app/19.0.0.0/grid"),None),(0,io.StringIO(""),None),(0,io.StringIO(""),None)]))
    def test_noDBCRSup(self,mock_node_exec,mock_pathcheck1,mock_exitstatus,mock_executelog,mock_execute):
        self.assertTrue(self._checkDBIsUp())

    @patch('exabox.ovm.clucontrol.node_exec_cmd', return_value = [0,_aDBAASCliOut,None])
    @patch('exabox.ovm.clucontrol.node_cmd_abs_path_check')
    @patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', return_value=0)
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog')
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmd', side_effect = iter([(1,io.StringIO(""),None),(1,io.StringIO("BBB"),None),(1,io.StringIO(""),None),(1,io.StringIO("/u01/app/19.0.0.0/grid"),None),(1,io.StringIO("dummy"),io.StringIO("error")),(1,io.StringIO("dummy"),io.StringIO("error"))]))
    def test_noDBCRSdown(self,mock_node_exec,mock_pathcheck1,mock_exitstatus,mock_executelog,mock_execute):
        self.assertFalse(self._checkDBIsUp(1))

    _aDBStateStdout = """NAME=ora.db112265.db
TYPE=ora.database.type
TARGET=ONLINE                  , ONLINE
STATE=ONLINE on scaqak02dv0501, ONLINE on scaqak02dv0601
ROLE=PRIMARY
USR_ORA_OPEN_MODE=open
"""
    _aHaveDBStdout = """STATE=ONLINE
NAME=ora.db112265.db 2 1
TYPE=ora.database.type
TARGET=ONLINE
STATE=ONLINE
ROLE=PRIMARY
USR_ORA_OPEN_MODE=open
"""
    @patch('exabox.ovm.clucontrol.node_exec_cmd', return_value = [0,_aDBAASCliOut,None])
    @patch('exabox.ovm.clucontrol.node_cmd_abs_path_check')
    @patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', return_value=0)
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog')
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmd', side_effect = iter([(0,io.StringIO(""),None),(0,io.StringIO(""),None),(0,io.StringIO("BBB"),None),(0,io.StringIO("/u01/app/19.0.0.0/grid"),None),(0,io.StringIO(_aDBStateStdout),None),(0,io.StringIO(_aHaveDBStdout),None)]))
    def test_oneDBup(self,mock_node_exec,mock_pathcheck1,mock_exitstatus,mock_executelog,mock_execute):
        self.assertTrue(self._checkDBIsUp(0,_aDBStateStdout,_aHaveDBStdout))
        

    _aDBStateStdout = """NAME=ora.db112265.db
TYPE=ora.database.type
TARGET=ONLINE                  , ONLINE
STATE=OFFLINE on scaqak02dv0501, OFFLINE on scaqak02dv0601
ROLE=PRIMARY
USR_ORA_OPEN_MODE=open
"""
    _aHaveDBStdout = """STATE=ONLINE
NAME=ora.db112265.db 2 1
TYPE=ora.database.type
TARGET=ONLINE
STATE=OFFLINE
ROLE=PRIMARY
USR_ORA_OPEN_MODE=open
"""
    @patch('exabox.ovm.clucontrol.node_exec_cmd', return_value = [0,_aDBAASCliOut,None])
    @patch('exabox.ovm.clucontrol.node_cmd_abs_path_check')
    @patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', return_value=0)
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog')
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmd', side_effect = iter([(0,io.StringIO(""),None),(0,io.StringIO("BBB"),None),(0,io.StringIO(""),None),(0,io.StringIO("/u01/app/19.0.0.0/grid"),None),(0,io.StringIO(_aDBStateStdout),None),(0,io.StringIO(_aHaveDBStdout),None)]))
    def test_oneDBdown(self,mock_node_exec,mock_pathcheck1,mock_exitstatus,mock_executelog,mock_execute):
        self.assertFalse(self._checkDBIsUp(0,_aDBStateStdout,_aHaveDBStdout))

    _aDBStateStdout = """NAME=ora.db112265.db
TYPE=ora.database.type
TARGET=OFFLINE                  , OFFLINE
STATE=OFFLINE on scaqak02dv0501, OFFLINE on scaqak02dv0601
ROLE=PRIMARY
USR_ORA_OPEN_MODE=open
"""
    _aHaveDBStdout = """STATE=OFFLINE
NAME=ora.db112265.db 2 1
TYPE=ora.database.type
TARGET=OFFLINE
STATE=OFFLINE
ROLE=PRIMARY
USR_ORA_OPEN_MODE=open
"""
    @patch('exabox.ovm.clucontrol.node_exec_cmd', return_value = [0,_aDBAASCliOut,None])
    @patch('exabox.ovm.clucontrol.node_cmd_abs_path_check')
    @patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', return_value=0)
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog')
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmd', side_effect = iter([(0,io.StringIO(""),None),(0,io.StringIO("BBB"),None),(0,io.StringIO(""),None),(0,io.StringIO("/u01/app/19.0.0.0/grid"),None),(0,io.StringIO(_aDBStateStdout),None),(0,io.StringIO(_aHaveDBStdout),None)]))
    def test_oneDBExpectedDown(self,mock_node_exec,mock_pathcheck1,mock_exitstatus,mock_executelog,mock_execute):
        self.assertTrue(self._checkDBIsUp(0,_aDBStateStdout,_aHaveDBStdout))


    _aDBStateStdout = """NAME=ora.db121244.db
TYPE=ora.database.type
TARGET=ONLINE                  , ONLINE
STATE=ONLINE on scaqak02dv0503, ONLINE on scaqak02dv0603
ROLE=PRIMARY
USR_ORA_OPEN_MODE=open

NAME=ora.db121960.db
TYPE=ora.database.type
TARGET=ONLINE                  , ONLINE
STATE=ONLINE on scaqak02dv0503, ONLINE on scaqak02dv0603
ROLE=PRIMARY
USR_ORA_OPEN_MODE=open

NAME=ora.db18342.db
TYPE=ora.database.type
TARGET=ONLINE                  , ONLINE
STATE=ONLINE on scaqak02dv0503, ONLINE on scaqak02dv0603
ROLE=PRIMARY
USR_ORA_OPEN_MODE=open
"""
    _aHaveDBStdout = """STATE=ONLINE
NAME=ora.db121244.db 1 1
TYPE=ora.database.type
TARGET=ONLINE
STATE=ONLINE
ROLE=PRIMARY
USR_ORA_OPEN_MODE=open
--
STATE=ONLINE
NAME=ora.db121960.db 1 1
TYPE=ora.database.type
TARGET=ONLINE
STATE=ONLINE
ROLE=PRIMARY
USR_ORA_OPEN_MODE=open
--
STATE=ONLINE
NAME=ora.db18342.db 1 1
TYPE=ora.database.type
TARGET=ONLINE
STATE=ONLINE
ROLE=PRIMARY
USR_ORA_OPEN_MODE=open
"""
    @patch('exabox.ovm.clucontrol.node_exec_cmd', return_value = [0,_aDBAASCliOut,None])
    @patch('exabox.ovm.clucontrol.node_cmd_abs_path_check')
    @patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', return_value=0)
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog')
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmd', side_effect = iter([(0,io.StringIO(""),None),(0,io.StringIO("BBB"),None),(0,io.StringIO(""),None),(0,io.StringIO("/u01/app/19.0.0.0/grid"),None),(0,io.StringIO(_aDBStateStdout),None),(0,io.StringIO(_aHaveDBStdout),None)]))
    def test_multiDBup(self,mock_node_exec,mock_pathcheck1,mock_exitstatus,mock_executelog,mock_execute):
        self.assertTrue(self._checkDBIsUp(0,_aDBStateStdout,_aHaveDBStdout))

    _aDBStateStdout = """NAME=ora.db121244.db
TYPE=ora.database.type
TARGET=ONLINE                  , ONLINE
STATE=ONLINE on scaqak02dv0503, ONLINE on scaqak02dv0603
ROLE=PRIMARY
USR_ORA_OPEN_MODE=open

NAME=ora.db121960.db
TYPE=ora.database.type
TARGET=ONLINE                  , ONLINE
STATE=ONLINE on scaqak02dv0503, ONLINE on scaqak02dv0603
ROLE=PRIMARY
USR_ORA_OPEN_MODE=open

NAME=ora.db18342.db
TYPE=ora.database.type
TARGET=ONLINE                  , ONLINE
STATE=OFFLINE on scaqak02dv0503, OFFLINE on scaqak02dv0603
ROLE=PRIMARY
USR_ORA_OPEN_MODE=open
"""
    _aHaveDBStdout = """STATE=ONLINE
NAME=ora.db121244.db 1 1
TYPE=ora.database.type
TARGET=ONLINE
STATE=ONLINE
ROLE=PRIMARY
USR_ORA_OPEN_MODE=open
--
STATE=ONLINE
NAME=ora.db121960.db 1 1
TYPE=ora.database.type
TARGET=ONLINE
STATE=ONLINE
ROLE=PRIMARY
USR_ORA_OPEN_MODE=open
--
STATE=ONLINE
NAME=ora.db18342.db 1 1
TYPE=ora.database.type
TARGET=ONLINE
STATE=OFFLINE
ROLE=PRIMARY
USR_ORA_OPEN_MODE=open
"""
    @patch('exabox.ovm.clucontrol.node_exec_cmd', return_value = [0,_aDBAASCliOut,None])
    @patch('exabox.ovm.clucontrol.node_cmd_abs_path_check')
    @patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', return_value=0)
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog')
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmd', side_effect = iter([(0,io.StringIO(""),None),(0,io.StringIO("BBB"),None),(0,io.StringIO(""),None),(0,io.StringIO("/u01/app/19.0.0.0/grid"),None),(0,io.StringIO(_aDBStateStdout),None),(0,io.StringIO(_aHaveDBStdout),None)]))
    def test_multiDBoneDown(self,mock_node_exec,mock_pathcheck1,mock_exitstatus,mock_executelog,mock_execute):
        self.assertFalse(self._checkDBIsUp(0,_aDBStateStdout,_aHaveDBStdout))

    
if __name__ == '__main__':
    unittest.main()
