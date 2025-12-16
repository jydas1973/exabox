"""
$Header:

 Copyright (c) 2014, 2021, Oracle and/or its affiliates. 

NAME:
    test_DBKeys.py - Base Class for DBkeys testing

FUNCTION:
    Use this class when is necessary to test the DBKeys methods

NOTE:
    None

History:

    MODIFIED   (MM/DD/YY)
    ndesanto    12/04/20 - Added test case related to empty file issue
    ndesanto    05/25/20 - Creation of the file
"""

import datetime
import json
import os
import shutil
import unittest
import uuid
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogDB
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.DBKeys import DBKeys

class TestDBKeys(ebTestClucontrol):

    @classmethod
    def setUpClass(self):

        super().setUpClass()

        _test_data_path = self.mGetPath(self)

        self._keys_db_path = os.path.abspath(os.path.join(self.mGetUtil(self).mGetOutputDir(), "test_data.json"))
        self._sqlite_db_path = os.path.abspath(os.path.join(self.mGetUtil(self).mGetOutputDir(), "sqlite.db"))

        shutil.copy(os.path.join(_test_data_path, "sqlite.db"), self._sqlite_db_path)
        shutil.copy(os.path.join(_test_data_path, "test_data.json"), self._keys_db_path)

        self._dbkeys = DBKeys(os.path.abspath(os.path.join(self.mGetUtil(self).mGetOutputDir(), "keys.json")))
        with open(self._keys_db_path, "rb") as fd:
            _data = json.load(fd)

        self._clustername = _data["clustername"]
        self._sshkeys = _data["sshkeys"]


    @classmethod
    def tearDownClass(self):
        pass

    def test_mMigration(self):
        _rows = self._dbkeys.mMigrate(self._sqlite_db_path)
        self.assertEqual(8, _rows)
        self.assertEqual(8, self._dbkeys.mSize())
        self.assertEqual(8, len(self._dbkeys))
        self._dbkeys.mReset()
        self.assertEquals({}, self._dbkeys.mGetDict())

    def test_mCreateSshkeyTable(self):
        self.assertIsNotNone(self._dbkeys)

    def test_mUpsertSshkey(self):
        self.assertTupleEqual((0, ''), self._dbkeys.mUpsertSshkey(\
            self._clustername, self._sshkeys))

    def test_mGetSshkey(self):
        self.assertTupleEqual((0, self._sshkeys), \
            self._dbkeys.mGetSshkey(self._clustername))

    def test_raceCondition(self):
        """
           In a 'real' exacloud setup, each worker will have an instance of
           DBKeys, sharing the same physical JSON, reproduce that
        """
        _dbkeys2 = DBKeys(os.path.abspath(os.path.join(self.mGetUtil().mGetOutputDir(), "keys.json")))
        # Reproduce race condition and ensure it is fixed with bug 32546000
        # We will, 
        # A) call set for clustername to update sshkeys on self.db_keys
        # B) Verify JSON was updated
        # C) call set on another DBKey instance with another clustername
        # D) With current code, update done in A) would be deleted as write 
        #    on one clustername reset the others to the 'saved' state
        _newssh_keys=json.loads(self._sshkeys.replace('\n',''))
        # ADD A NEW KEY
        _newssh_keys['id_rsa.newkey.grid'] = 'DUMMYKEYCONTENT'
        self._dbkeys.mUpsertSshkey(self._clustername, _newssh_keys)
        self.assertEqual(self._dbkeys.mGetSshkey(self._clustername)[1]['id_rsa.newkey.grid'],'DUMMYKEYCONTENT')
        # Update another cluster on dbkeys2 (with same keys)
        _dbkeys2.mUpsertSshkey(self._clustername+'2', _newssh_keys)
        # Create a new instance of DBKEYs (to force rereading of JSON file)
        _dbkeys3 = DBKeys(os.path.abspath(os.path.join(self.mGetUtil().mGetOutputDir(), "keys.json")))

        # EXPECTATION IS THAT JSON file we just read have updated key 
        # for BOTH clusters. Thee assert BELOW will fail without 32546000 fix
        self.assertTupleEqual((0, _newssh_keys), \
            _dbkeys3.mGetSshkey(self._clustername)) #First cluter
        
        # Second cluster must be updated and should not revert 
        # first cluster to original value
        self.assertTupleEqual((0, _newssh_keys), \
            _dbkeys3.mGetSshkey(self._clustername+'2'))

    def test_mDeleteSshkeyTable(self):
        self._dbkeys.mDeleteSshkeyTable()
        self.assertEquals({}, self._dbkeys.mGetDict())

    def test_mEmptyFile(self):
        self._dbkeys = None
        _empty_keys_db_path = os.path.abspath(os.path.join(self.mGetUtil().mGetOutputDir(), "empty.db"))
        with open(_empty_keys_db_path, "w") as fp:
            pass  # Create empty file
        self._dbkeys = DBKeys(_empty_keys_db_path)
        self.assertEquals({}, self._dbkeys.mGetDict())


def suite():
    """
    This method ensures the execution in the intended order of the tests.
    """
    suite = unittest.TestSuite()
    suite.addTest(TestDBKeys('test_mMigration'))
    suite.addTest(TestDBKeys('test_mCreateSshkeyTable'))
    suite.addTest(TestDBKeys('test_mUpsertSshkey'))
    suite.addTest(TestDBKeys('test_mGetSshkey'))
    suite.addTest(TestDBKeys('test_mUpsertSshkey'))
    suite.addTest(TestDBKeys('test_raceCondition'))
    suite.addTest(TestDBKeys('test_mDeleteSshkeyTable'))
    suite.addTest(TestDBKeys('test_mEmptyFile'))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner(failfast=True)
    runner.run(suite())
