"""

 $Header: 

 Copyright (c) 2018, 2023, Oracle and/or its affiliates.

 NAME:
      tests_atpAddRoutes.py - Unitest for add routes ATP

 DESCRIPTION:
      Run tests for the class ebSubnetIp using Unitest

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)

        vgerard    09/06/18 - Creation of the file for exacloud unit test
"""

import unittest
import glob
import os
import platform
import io
import time
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.CrashDump import CrashDump 
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogWarn
import resource
import subprocess as sp


class ebTestCrashDump(ebTestClucontrol):


    def test_ValidBasicCase(self):
       try:
           array = [1,2]
           array[3] = 4
       except:
           with CrashDump() as c:
               c.ProcessException()


    def test_ExceptionInCrashdump(self):
        try:
           array = [1,2]
           array[3] = 4
        except:
           try:
               with CrashDump() as c:
                   array[5] = 5
                   c.ProcessException()
           except:
               pass

    def test_NoWith(self):
        try:
           array = [1,2]
           array[3] = 4
        except:
           c = CrashDump()
           c.ProcessException()
           c.WriteCrashDump()

    def test_Multiprocess(self):

        crashOutputIO = io.StringIO()
        try:

            def sample_function(number):
                time.sleep(number)

            _plist = ProcessManager()
            _to_review = [20000000, 10000000]
            for _i in _to_review:
                _p = ProcessStructure(sample_function, [_i])
                _p.mSetMaxExecutionTime(1/60) # 10 secs timeout
                _p.mSetJoinTimeout(1)
                _p.mSetLogTimeoutFx(ebLogWarn)
                _plist.mStartAppend(_p)

            _plist.mJoinProcess()

        except:
            c = CrashDump()
            c.ProcessException()
            c.crashDumpOutput(crashOutputIO)

        crashOutput = crashOutputIO.getvalue()
        crashOutputIO.close()
        self.assertIn('tests_CrashDump.py',crashOutput)


    def test_multiProcessException(self):

        def sample_function(number):
            raise ValueError("Totally expected exception")

        _plist = ProcessManager()
        _to_review = [20000000, 10000000]

        for _i in _to_review:
            _p = ProcessStructure(sample_function, [_i])
            _p.mSetMaxExecutionTime(1/60) # 10 secs timeout
            _p.mSetJoinTimeout(1)
            _p.mSetLogTimeoutFx(ebLogWarn)
            _plist.mStartAppend(_p)

        with self.assertRaises(ExacloudRuntimeError):
            _plist.mJoinProcess()

    def test_multiProcessIdle(self):

        crashOutputIO = io.StringIO()
        try:

            def sample_function(number):
                time.sleep(number)

            _plist = ProcessManager()
            _to_review = [20000000, 10000000]

            for _i in _to_review:
                _p = ProcessStructure(sample_function, [_i])
                _p.mSetMaxExecutionTime(1/60) # 10 secs timeout
                _p.mSetJoinTimeout(1)
                _p.mSetLogTimeoutFx(ebLogWarn)
                _plist.mStartAppend(_p)

            # Wait process to be marked as running
            time.sleep(2)
            self.assertTrue(_p.mIsRunning())

            # Set one as IDLE and not running
            _p.mSetRunning(False)

            # Join the process
            _plist.mJoinProcess()

        except:
            c = CrashDump()
            c.ProcessException()
            c.crashDumpOutput(crashOutputIO)

        crashOutput = crashOutputIO.getvalue()
        crashOutputIO.close()



    def test_Output(self):
        crashOutputIO = io.StringIO()
        try:
           array = [1,2]
           array[3] = 4
        except:
           c = CrashDump()
           c.ProcessException()
           c.crashDumpOutput(crashOutputIO)

        crashOutput = crashOutputIO.getvalue()
        crashOutputIO.close()
        self.assertIn(str(os.getpid()),crashOutput)
        #ACTUAL error should be clearly in dump
        self.assertIn('array[3] = 4',crashOutput)
        self.assertIn('IndexError',crashOutput)
        self.assertIn('index out of range',crashOutput)
        self.assertIn('tests_CrashDump.py',crashOutput)
        self.assertIn(platform.release(),crashOutput)
        self.assertIn(str(platform.uname()),crashOutput)




if __name__ == '__main__':
    unittest.main()

