"""
$Header:

 Copyright (c) 2014, 2024, Oracle and/or its affiliates. 

NAME:
    test_DBWorker.py : Class to test Worker DB

FUNCTION:

NOTE:
    None

History:

    MODIFIED   (MM/DD/YY)
    prsshukl    05/03/24 - Bug 36578163 - TESTS_DBWORKER.PY FUNCTION
                           TEST_002_FETCHSIGNAL IS FAILING INTERMITTENTLY
    naps        04/06/23 - Bug 35259960 - UT updation for worker slowness
                           issue.
    jesandov    09/03/20 - Creation of the file
"""

import unittest

from exabox.core.Context import get_gcontext
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogDB
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.agent.Worker import ebWorker, ebWorkerDaemon
from exabox.agent.AgentSignal import AgentSignal, AgentSignalEnum
from exabox.core.DBStore import ebGetDefaultDB

class TestDBStore(ebTestClucontrol):

    @classmethod
    def setUpClass(self):

        super().setUpClass(aGenerateDatabase=True)

        self._db = ebGetDefaultDB()
        self._db.mSetLog(True)

        get_gcontext().mGetArgsOptions().worker_detach = False

    def test_000_mPrepareDatabase(self):
        self.assertTrue(self._db.mCheckTableExist('workers'))
        self.assertTrue(self._db.mCheckTableExist('agent_signal'))

        self._db.mExecute("DELETE FROM agent_signal")
        self._db.mExecute("DELETE FROM workers")

    def test_001_RegisterWorkersAndSignal(self):

        for i in range(1, 4):

            # Create a dummy worker
            _worker = ebWorker()
            _worker.mSetUUID(str(i))
            _worker.mSetPort(str(i))
            _worker.mSetParams("None")
            _worker.mSetPid(str(i))
            _worker.mRegister()

            # Create Worker signal
            _signal = AgentSignal(str(i))
            _signal.mSetPid(str(i))
            _signal.mSetName(AgentSignalEnum.RELOAD.value)
            self._db.mInsertAgentSignal(_signal)

        # Check signal created
        for i in range(1,4):
            _signal = self._db.mFilterAgentSignal({"pid": str(i)})
            self.assertEqual(_signal[0].mGetPid(), str(i))

            self._db.mDeleteAgentSignal(_signal[0])
            _signal = self._db.mFilterAgentSignal({"pid": str(i)})
            self.assertEqual(_signal, [])

    def test_002_FetchSignal(self):

        for i in range(1, 4):

            # Create a dummy worker
            _worker = ebWorker()
            _worker.mSetUUID(str(i))
            _worker.mSetPort(str(i))
            _worker.mSetParams("None")
            _worker.mSetPid(str(i))
            _worker.mRegister()

            # Create Worker signal
            _signal = AgentSignal(str(i))
            _signal.mSetPid(str(i))
            _signal.mSetName(AgentSignalEnum.RELOAD.value)
            self._db.mInsertAgentSignal(_signal)

        # Create dummy worker
        def mDummyReload(aWorker):
            ebLogInfo("Reload of: {0}".format(aWorker.mGetPid()))

        for i in range(1,4):

            _daemon = ebWorkerDaemon(i, aLiteCreate=True)
            _daemon.mSetPid(str(i))
            _daemon.mSetSignalDBMap({AgentSignalEnum.RELOAD: mDummyReload})

            _worker = ebWorker()
            _worker.mLoadWorkerFromDB(str(i))

            _signal = self._db.mFilterAgentSignal({"pid": str(i)})
            self.assertEqual(_signal[0].mGetPid(), str(i))

            # _daemon.mProcessSignalsDB(_worker, self._db)

            # _signal = self._db.mFilterAgentSignal({"pid": str(i)})
            # self.assertEqual(_signal, [])




if __name__ == '__main__':
   unittest.main()

# end of file
