"""
$Header:

 Copyright (c) 2014, 2021, Oracle and/or its affiliates. 

NAME:
    test_DBLocks.py : Class to test DB Lock impl

FUNCTION:

NOTE:
    None

History:

    MODIFIED   (MM/DD/YY)
    vgerard    06/08/20 - Creation of the file
"""

import six
import datetime
import unittest
import uuid
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogDB
from exabox.agent.ebJobRequest import ebJobRequest
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.DBStore import ebGetDefaultDB
from exabox.core.DBLockTableUtils import ebDBLockTypes, sDBLockCleanAllLeftoverLocks

class TestDBStore(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateDatabase=True)
        self._db = ebGetDefaultDB()

    @classmethod
    def tearDownClass(self):
        self._db.mDeleteAllLocks()

    def test_mPrepareDatabase(self):
        self.assertTrue(self._db.mCheckTableExist('requests'))
        self.assertTrue(self._db.mCheckTableExist('requests_archive'))
        self.assertTrue(self._db.mCheckTableExist('locks'))

    def test_locksTable(self):
        self._db.mInsertLock(uuid=str(uuid.uuid4()),lock_type=ebDBLockTypes.DOM0_LOCK,lock_hostname='scaqab10adm01')
        self._db.mInsertLock(uuid=str(uuid.uuid4()),lock_type=ebDBLockTypes.DOM0_LOCK,lock_hostname='scaqab10adm02')
        _locks = self._db.mGetAllLocks()
        self.assertEqual(2,len(_locks))
        for _lock in _locks:
            self.assertIn(_lock['lock_hostname'],('scaqab10adm01','scaqab10adm02'))
            # Delete row
            self._db.mDeleteLock(_lock['uuid'],ebDBLockTypes.DOM0_LOCK,_lock['lock_hostname'],)
        _locks = self._db.mGetAllLocks()
        self.assertEqual(0,len(_locks))

    def test_locksTable2(self):
        _u1 = str(uuid.uuid4())
        self._db.mInsertLock(uuid=_u1,lock_type=ebDBLockTypes.DOM0_LOCK,lock_hostname='scaqab10adm01')
        self._db.mInsertLock(uuid=str(uuid.uuid4()),lock_type=ebDBLockTypes.DOM0_LOCK,lock_hostname='scaqab10adm02')
        _locks  = self._db.mGetLocksByUUID(_u1)
        _locks2 = self._db.mGetLocksByUUIDAndType(_u1,ebDBLockTypes.DOM0_LOCK)
        self.assertListEqual(_locks,_locks2)
        self.assertEqual(1,len(_locks))
        self._db.mDeleteLockByHostname(ebDBLockTypes.DOM0_LOCK,_locks[0]['lock_hostname'])
        _locks = self._db.mGetLocksByType(ebDBLockTypes.DOM0_LOCK)
        self.assertEqual(1,len(_locks))
        self._db.mDeleteAllLocks()
        _locks = self._db.mGetAllLocks()
        self.assertEqual(0,len(_locks))

    def test_locksCleanup(self):
        self._db.mInsertLock(uuid='uuidA',lock_type=ebDBLockTypes.DOM0_LOCK,lock_hostname='scaqab10adm01')
        self._db.mInsertLock(uuid='uuidB',lock_type=ebDBLockTypes.DOM0_LOCK,lock_hostname='scaqab10adm02')
        self._db.mInsertLock(uuid='uuidC',lock_type=ebDBLockTypes.DOM0_LOCK_ACQUIRING,lock_hostname='scaqab10adm01')
        self._db.mInsertLock(uuid='uuidD',lock_type=ebDBLockTypes.DOM0_LOCK,lock_hostname='scaqab10adm03')
        self._db.mInsertLock(uuid='uuidE',lock_type=ebDBLockTypes.DOM0_LOCK_ACQUIRING,lock_hostname='scaqab10adm04')
        self._db.mInsertLock(uuid='uuidF',lock_type=ebDBLockTypes.DOM0_LOCK,lock_hostname='scaqab10adm06.us.oracle.com')
        self._db.mInsertLock(uuid='uuidG',lock_type=ebDBLockTypes.DOM0_LOCK,lock_hostname='scaqab10adm01')


        results = sDBLockCleanAllLeftoverLocks(aMock=True)
        _order = ['scaqab10adm01','scaqab10adm01','scaqab10adm01','scaqab10adm02','scaqab10adm03','scaqab10adm04','scaqab10adm06.us.oracle.com']

        killfmt = "pkill -9 -f 'tlock.sh acquire {}'"
        dom0rm  = 'rm -f /tmp/exacs_dom0_lock ; rm -f /tmp/exacs_dom0_lock_info'
        # count matches of commands for each dom0
        res = {k:[0,0] for k in set(_order)}

        for host, cmd in results:
            #Verify order is sorted
            self.assertEqual(host, _order.pop(0))
            if cmd == dom0rm:
                res[host][0] = res[host][0]+1
            if host == 'scaqab10adm01':
                if cmd == killfmt.format('uuidC'): # C is dom0 01
                    res[host][1] = res[host][1]+1
            elif host == 'scaqab10adm04':
                if cmd == killfmt.format('uuidE'):
                    res[host][1] = res[host][1]+1

        # Expected values, first is ACK locks, second is pending locks
        self.assertEqual(res,
            {'scaqab10adm03': [1, 0],
             'scaqab10adm02': [1, 0],
             'scaqab10adm01': [2, 1],
             'scaqab10adm06.us.oracle.com': [1, 0],
             'scaqab10adm04': [0, 1]})  #04 have 1 pending lock only


if __name__ == '__main__':
   unittest.main()
