"""
 Copyright (c) 2014, 2024, Oracle and/or its affiliates.

NAME:
    AsyncProcessing - Basic functionality

FUNCTION:
    AsyncProcessing is a little framework to control different process
    
    This have two class
        ProcessStructure: Inherit from process with extra params like id and execution time metrics
        ProcessManager: Control all the ProcessStructure 

NOTE:
    None    

History:
    ririgoye    19/02/24  - 36305000: Added process killing enforcement and process start/end logging
    dekuckre    19/01/24  - 36203786: Correctly pick the process in waitlist to be processed
    ririgoye    01/22/24  - 36206720: Add checks to prevent failure when reaching
                            the process limit.
    dekuckre    29/11/23  - 35924029: Add limit to the number of processes spawned.
    jesandov    25/05/23  - 35371006: Enhance error message on Non-Zero exit
    dekuckre    04/12/23  - 35280961: Use ps -ef instead of pstree
    aypaul      12/04/22  - Issue#34607716 Handle multiprocessing issue by shutting
                             down base manager instance explicitly.
    hgaldame    05/06/2022 - 34146854 - oci/exacc: persists exacloud remote ec 
                             async request status
    dekuckre    11/19/2020 - 32138331: report issues if process exitcode != 0
    jesandov    15/04/2019 - File Creation
"""



import os
import time
import uuid
import signal
import ctypes
import errno
import enum
import traceback
import json
import subprocess as sp
from datetime import datetime
from multiprocessing import Process, Manager, Array, Value
from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.DBStore import ebGetDefaultDB
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogVerbose, ebLogDebug, ebLogJson, ebLogTrace
from exabox.core.CrashDump import CrashDump


def mExecuteLocal(aLogFx, aCmd, aCurrDir=None, aStdIn=sp.PIPE, aStdOut=sp.PIPE, aStdErr=sp.PIPE):

    aLogFx('mExecuteLocal: {0}'.format(aCmd))

    _current_dir = aCurrDir
    _stdin = aStdIn
    _stdout = aStdOut
    _stderr = aStdErr

    _proc = sp.Popen(aCmd, stdin=_stdin, stdout=_stdout, stderr=_stderr, cwd=_current_dir)
    _stdoutP, _stderrP = _proc.communicate()
    _rc = _proc.returncode

    if _stdoutP:
        _stdoutP = _stdoutP.decode("UTF-8").strip()
    else:
        _stdoutP = ""

    if _stderrP:
        _stderrP = _stderrP.decode("UTF-8").strip()
    else:
        _stderrP = ""

    aLogFx('mExecuteLocal: RC:{0}'.format(_rc))
    aLogFx('STDOUT: {0}'.format(_stdoutP))
    aLogFx('STDERR: {0}'.format(_stderrP))


class ProcessStructure(Process):

    def mNow(self):
        return datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S+%f')

    def mToDT(self, aStr):
        return datetime.strptime(aStr, '%Y-%m-%d %H:%M:%S+%f')

    def __init__(self, aCallback, aArgs=None, aId=None, aMaxExecutionTime=-1, aLogFile=None):

        self.__id = aId
        if self.__id is None:
            self.__id = str(uuid.uuid1())

        self.__args             = aArgs
        self.__callback         = aCallback
        self.__startTime        = Array(ctypes.c_char, self.mNow().encode('utf8'))
        self.__endTime          = Array(ctypes.c_char, (" " * len(self.mNow())).encode('utf8'))
        self.__maxExecutionTime = aMaxExecutionTime
        self.__logFile          = aLogFile
        self.__onFinish         = None
        self.__onFinishArgs     = []
        self.__joinTimeout      = 30
        self.__manager          = None
        self.__shared           = None
        self.__logTimeoutFx     = print
        self.__persistState     = False
        self.__error            = Value(ctypes.c_bool, False)
        self.__running          = Value(ctypes.c_bool, False)

        self.mDebugHang()
        Process.__init__(self, target=self.mRealCallback, name=self.__id, args=self.__args)

    def mDebugHang(self):

        def debug(sig, frame):

            d={'_frame':frame}
            d.update(frame.f_globals)
            d.update(frame.f_locals)

            message  = f"DEBUG SIGNAL RECEIVED IN PROCESS {os.getpid()}, \nTRACEBACK:\n"
            message += ''.join(traceback.format_stack(frame))
            self.__logTimeoutFx(message)

        signal.signal(signal.SIGUSR2, debug)

    def mInitShared(self):

        if self.__manager is not None:
            self.__shared = self.__manager.dict()

    def mRealCallback(self, *args, **kwargs):

        ebLogInfo(f"*** Invoking Callback for Process ID: {self.__id}. PID: {os.getpid()} | Callback Function: {self.__callback}")

        self.mDebugHang()
        self.mSetStartTime(self.mNow())
        self.mSetRunning(True)

        try:
            if self.mGetPersistState():
                self.mPersistsProcessState(aAlive=True)

            _rc = self.__callback(*args, **kwargs)

        except Exception as e:

            with CrashDump(logFx=self.__logTimeoutFx) as c:
                c.ProcessException()

            if self.__logTimeoutFx:
                _fx = self.__logTimeoutFx
                _fx("Failure on process: {0}".format(self.mStr()))
                _fx("".join(traceback.format_exc()))

            self.mSetError(True)
            if self.mGetPersistState():
                self.mPersistsProcessState()
            raise

        if self.__onFinish is not None:

            if self.__onFinishArgs is None:
                self.__onFinishArgs = []

            try:

                self.__onFinish(*self.__onFinishArgs)

            except:

                if self.__logTimeoutFx:
                    _fx = self.__logTimeoutFx
                    _fx("Failure on process: {0}".format(self.mStr()))
                    _fx("".join(traceback.format_exc()))
                self.mSetError(True)
                ebLogWarn(f"* Process  {os.getpid()} ended with error.")
                if self.mGetPersistState():
                    self.mPersistsProcessState()
                raise

        self.mSetReturn(_rc)
        self.mSetEndTime(self.mNow())
        self.mSetError(False)
        ebLogInfo(f"* Process {os.getpid()} ended sucessfully.")
        if self.mGetPersistState():
            self.mPersistsProcessState()

    def mKill(self):

        _exacloudPath = os.path.abspath(__file__)
        _exacloudPath = _exacloudPath[0: _exacloudPath.rfind("exacloud")+8]

        _fx = self.mGetLogTimeoutFx()
        if _fx:
            _fx("Send it SIGTERM to ({0})".format(self.mStr()))

        # Create crashdump
        try:

            # Get diagnostic information
            _cmd = ["/usr/bin/timeout", "3", "/usr/bin/strace", "-p", str(self.pid)]
            mExecuteLocal(_fx, _cmd)

            # reports the details of process (pid)
            _cmd = ["/bin/ps", "--pid", str(self.pid), "-o", "pid", "-o", "ppid", "-o", "cmd"]
            mExecuteLocal(_fx, _cmd)

            # reports details of child processes of the process (pid)
            _cmd = ["/bin/ps", "--ppid", str(self.pid), "-o", "pid", "-o", "ppid", "-o", "cmd"]
            mExecuteLocal(_fx, _cmd)

            # Get information about all exacloud process
            _cmd = ["/usr/bin/pgrep", "-a", "-fl", _exacloudPath]
            mExecuteLocal(_fx, _cmd)

            raise ValueError("Exception for CrashDump creation")

        except:
            with CrashDump(logFx=self.__logTimeoutFx) as c:
                c.ProcessException()

        # Get stacktrace
        os.kill(self.pid, signal.SIGUSR2)
        time.sleep(1)

        # Send SIGTERM of the process
        self.terminate()

    def mStr(self):
        _list = []
        _list.append("id: {0}".format(self.mGetId()))
        _list.append("start_time: {0}".format(self.mGetStartTime()))
        _list.append("end_time: {0}".format(self.mGetEndTime()))
        _list.append("max_time: {0}".format(self.mGetMaxExecutionTime()))
        _list.append("callback: {0}".format(self.mGetCallback()))
        _list.append("args: {0}".format(self.mGetArgs()))
        _list.append("pid: {0}".format(self.pid))
        _list.append("is_running: {0}".format(self.mIsRunning()))
        return ", ".join(_list)

    def mGetName(self):
        return self.name

    def mSetName(self, aName):
        self.name = aName

    def mIsRunning(self):
        return self.__running.value

    def mSetRunning(self, aBool):
        self.__running.value = aBool

    def mGetStartTime(self):
        return self.__startTime.value.decode('utf8')

    def mGetStartTimeDT(self):
        return self.mToDT(self.mGetStartTime())

    def mSetStartTime(self, aStr):
        self.__startTime.value = aStr.encode('utf8')

    def mGetEndTime(self):
        if self.__endTime.value.strip() == b"":
            return None
        else:
            return self.__endTime.value.strip().decode('utf8')

    def mGetEndTimeDT(self):
        if self.__endTime.value == b"":
            return None
        else:
            return self.mToDT(self.__endTime.value.decode('utf8'))

    def mSetEndTime(self, aStr):
        self.__endTime.value = aStr.encode('utf8')

    def mGetMaxExecutionTime(self):
        return self.__maxExecutionTime

    def mSetMaxExecutionTime(self, aFloat):
        self.__maxExecutionTime = aFloat

    def mGetId(self):
        return self.__id

    def mSetId(self, aUuid):
        self.__id = aUuid

    def mGetCallback(self):
        return self.__callback

    def mSetCallback(self, aFunction):
        self.__callback = aFunction

    def mGetError(self):
        return self.__error.value

    def mSetError(self, aBool):
        self.__error.value = aBool

    def mGetReturn(self):
        if self.__shared is not None and "return" in list(self.__shared.keys()):
            return self.__shared['return']
        return None

    def mSetReturn(self, aReturn):
        if aReturn is not None:
            if self.__shared is not None:
                self.__shared['return'] = aReturn

    def mGetArgs(self):
        return self.__args

    def mSetArgs(self, aMasterList):
        self.__args = aMasterList

    def mGetLogFile(self):
        return self.__logFile

    def mSetLogFile(self, aLogFile):
        self.__logFile = aLogFile

    def mGetOnFinish(self):
        return self.__onFinish

    def mSetOnFinish(self, aFn):
        self.__onFinish = aFn

    def mGetOnFinishArgs(self):
        return self.__onFinishArgs

    def mSetOnFinishArgs(self, aArgsList):
        self.__onFinishArgs = aArgsList

    def mGetJoinTimeout(self):
        return self.__joinTimeout

    def mSetJoinTimeout(self, aTimeout):
        self.__joinTimeout = aTimeout

    def mGetLogTimeoutFx(self):
        return self.__logTimeoutFx

    def mSetLogTimeoutFx(self, aFx):
        self.__logTimeoutFx = aFx

    def mGetManager(self):
        return self.__manager

    def mSetManager(self, aManager):
        self.__manager = aManager

    def mGetPersistState(self):
        return self.__persistState

    def mSetPersistState(self, aProcessSate):
        self.__persistState = aProcessSate

    def mPersistsProcessState(self, aAlive=False):
        _db = ebGetDefaultDB()
        _processDict = {}
        _processDict["id"]              = self.mGetId()
        _processDict["rc"]              = self.mGetReturn()
        _processDict["name"]            = self.mGetName()
        _processDict["alive"]           = aAlive
        _processDict["log_file"]        = self.mGetLogFile()
        _processDict["time_start"]      = self.mGetStartTime()
        _processDict["time_end"]        = self.mGetEndTime()
        _processDict["max_exec_time"]   = self.mGetMaxExecutionTime()
        _processDict["args"]            = self.mGetArgs()
        _db.mUpsertAsyncProcess(_processDict)
        return

class TimeoutBehavior(enum.Enum):
    IGNORE = 1
    ERROR = 2

class ExitCodeBehavior(enum.Enum):
    IGNORE = 1
    ERROR = 2

class ProcessManager(object):

    def __init__(self, aTimeoutBehavior=TimeoutBehavior.ERROR, aExitCodeBehavior=ExitCodeBehavior.ERROR):
        self.__processList = []
        self.__wait_processlist = []
        self.__status = "idle" #idle, working, done, killed
        self.__timeoutBehavior = aTimeoutBehavior
        self.__exitcodeBehavior = aExitCodeBehavior
        self.__managerStarted = False
        self.__maxNewDispatched = 5

        _retries = 5

        while True:
            try:
                self.__manager = Manager()
                self.__managerStarted = True
                break
            except EOFError:
                _retries -= 1
                if _retries <= 0:
                    self.mMarkCurrentWorkerAsCorrupted()
                    raise
                time.sleep(1)

        self.__killedList = []

    def __del__(self):
        if self.__managerStarted:
            self.__manager.shutdown()

    def mMarkCurrentWorkerAsCorrupted(self):
        _worker_pid = os.getpid()
        _db_instance = ebGetDefaultDB()
        _input_reg_key = f"{_worker_pid}_WORKER_CORRUPTED"
        _db_instance.mSetRegEntry(_input_reg_key)

    def mGetManager(self):
        return self.__manager

    def mGetStatus(self):
        return self.__status

    def mGetProcessList(self):
        return self.__processList

    def mSetProcessList(self, aList):
        self.__processList = aList

    def mGetKilledList(self):
        return self.__killedList

    def mSetKilledList(self, aKilledList):
        self.__killedList = aKilledList

    def mGetAliveProceses(self):

        _plist = []
        for _p in self.__processList:

            if _p.mGetId() in self.__killedList:
                continue

            if _p.is_alive():
                _plist.append(_p)

        return _plist

    def mGetAliveCount(self):
        return len(self.mGetAliveProceses())

    def mAppend(self, aProcess):
        self.__processList.append(aProcess)
        aProcess.mSetManager(self.__manager)
        aProcess.mInitShared()

    def mGetProcessLimit(self):
        _coptions = get_gcontext().mGetConfigOptions()
        if "multiple_process_limit" in _coptions.keys():
            _pl = int(_coptions["multiple_process_limit"])
        else:
            _pl = 50
        return _pl


    def mStartAppend(self, aProcess):
        _pl = self.mGetProcessLimit()
        if self.mGetAliveCount() >= _pl:
            self.__wait_processlist.append(aProcess)
        else:
            ebLogTrace(f"mStartAppend: {aProcess.mStr()}")
            self.mAppend(aProcess)
            aProcess.start()

    def mGetProcess(self, aId):
        for _p in self.__processList:
            if _p.mGetId() == aId:
                return _p
        return None

    def mGetReturnKeyValues(self):
        _rcs = {}
        for _process in self.__processList:
            if not _process.is_alive():
                _rcs[_process.mGetName()] = _process.mGetReturn()
        return _rcs

    def mGetReturnValues(self):
        _rcs = []
        for _process in self.__processList:
            if not _process.is_alive():
                _rcs.append(_process.mGetReturn())
        return _rcs

    def mGetTimeoutProcesses(self):
        _timeoutP = []
        for _process in self.__processList:
            if _process.mGetError():
                _timeoutP.append(_process)
        return _timeoutP

    def mKillProcess(self, aProcess):
        try:
            # Do kill (SIGTERM)
            ebLogInfo(f"Killing process {aProcess.pid}")
            aProcess.mKill()

            # In case child ignore the terminate process
            aProcess.join(aProcess.mGetJoinTimeout())
            if aProcess.is_alive():
                os.kill(aProcess.pid, signal.SIGKILL)
                os.waitpid(aProcess.pid, 0)

        except EnvironmentError as ex:
              if ex.errno != errno.ESRCH:
                  raise

        finally:
            if aProcess.mGetId() not in self.__killedList:
                self.__killedList.append(aProcess.mGetId())

    def mJoinProcess(self):

        self.__status = "working"
        _one_failure = False
        _maxDispachedLocal = 0
        _pl = self.mGetProcessLimit()

        while self.mGetAliveCount() > 0:

            for _process in self.__processList:

                if _process.mGetId() in self.__killedList:
                    continue

                # Process in IDLE state
                _execution = datetime.now() - _process.mGetStartTimeDT()

                while self.mGetAliveCount() < _pl and len(self.__wait_processlist) != 0:
                    _toSpawn = self.__wait_processlist.pop(0)
                    self.mStartAppend(_toSpawn)

                if not _process.mIsRunning() and _execution.seconds > max(_process.mGetMaxExecutionTime(), 600)/10:

                    _maxDispachedLocal += 1
                    if _maxDispachedLocal > self.__maxNewDispatched:
                        raise ExacloudRuntimeError(0x0756, 0xA,f"Error: Max number of process created in AsyncProcessing")

                    # Remove process from process list
                    _process.mKill()
                    self.__processList.remove(_process)

                    ebLogWarn(f"Destroyed process: {_process.mGetId()}")
                    ebLogWarn(f"Creating new process: {_process.mGetId()}-{_maxDispachedLocal}")

                    # Clone process
                    _newProcess = ProcessStructure(
                        _process.mGetCallback(),
                        _process.mGetArgs(),
                        f"{_process.mGetId()}-{_maxDispachedLocal}",
                        _process.mGetMaxExecutionTime(),
                        _process.mGetLogFile()
                    )

                    _newProcess.mSetJoinTimeout(_process.mGetJoinTimeout())
                    _newProcess.mSetLogTimeoutFx(_process.mGetLogTimeoutFx())

                    self.mStartAppend(_newProcess)
                    time.sleep(_maxDispachedLocal * 2)
                    continue


                if _process.is_alive():
                    _execution = datetime.now() - _process.mGetStartTimeDT()

                    if _execution.seconds > _process.mGetMaxExecutionTime() and \
                       _process.mGetMaxExecutionTime() != -1:

                        self.mKillProcess(_process)

                        if _process.mGetEndTime() is None:
                            _process.mSetEndTime(_process.mNow())

                        _process.mSetError(True)
                        self.__status = "killed"

                        if _process.mGetLogTimeoutFx() is not None:
                            _fx = _process.mGetLogTimeoutFx()
                            _fx("Timeout while async execute ({0})".format(_process.mStr()))

                        if self.__timeoutBehavior == TimeoutBehavior.ERROR:
                            _one_failure = True


                    else:
                        _process.join(_process.mGetJoinTimeout())
                else:
                    if _process.mGetEndTime() is None:
                        _process.mSetEndTime(_process.mNow())

        if _one_failure:
            raise ExacloudRuntimeError(0x0756, 0xA,f"Error: {_process.mStr()}. Error while multiprocessing(Process timeout)")

        # Check process finnish and return codes
        for _process in self.__processList:

            if _process.mGetEndTime() is None:
                _process.mSetEndTime(_process.mNow())

            if _process.exitcode != 0 and self.__exitcodeBehavior == ExitCodeBehavior.ERROR:
                _msg = f"Error in multiprocessing(Non-zero exitcode({_process.exitcode}) returned {_process}, {_process.mStr()})"
                raise ExacloudRuntimeError(0x0755, 0xA, _msg)

        if self.__status == "working":
            self.__status = "done"


    def mKillAll(self):
        for _process in self.__processList:
            if _process.is_alive():

                self.mKillProcess(_process)

                if _process.mGetEndTime is None:
                    _process.mSetEndTime(_process.mNow())

                _process.mSetError(True)

        self.__status = "killed"


# end of file
