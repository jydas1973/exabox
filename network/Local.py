"""
 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    Local - Basic functionality for Local Node Connection

FUNCTION:
    Provide basic/core API for accessing local Node
    API provided similar to Network class

    If need be in the future - a base class in osds could be created
    to handle differences between OSs (e.g. localunix, localosx, localwin,...)

NOTE:
    None

History:
    ririgoye    06/02/2025 - Bug 38014410 - SOP: REMOTE EXECUTION FAILED DUE TO 
                             EXACLOUDRUNTIMEERROR
    ririgoye    05/05/2025 - Bug 37588295 - Exacloud sop local remote execution 
                             will hang on large output
    scoral      03/21/2023 - Enh 34734317 - Implemented mGetFileInfo
    pbellary    08/10/2020 - Bug 31364037 - FORTIFY: COMMAND INJECTION IN LOCAL.PY
    ndesanto    06/02/2020 - Added mIsConnectable method
    ndesanto    04/15/2020 - Added argument to add environment variables to the popen
    mirivier    08/21/2014 - Create file
"""

ebLocalInitialized  = 0
ebLocalConnected    = 1
ebLocalDisconnected = 1 << 1

import subprocess, shlex, socket, shutil
import os
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug
from exabox.tools.AttributeWrapper import wrapStrBytesFunctions
from exabox.recordreplay.record_replay import ebRecordReplay 

class exaBoxLocal(object):

    def __init__(self, aHost = None, aOptions=None, env=None):

        self.__host     = aHost.split('.')[0]
        self.__options  = aOptions
        self.__env      = env
        self.__state    = ebLocalInitialized
        self.__rc       = None
        self.__proc     = None
        self.__debug    = False
        self.__timeout  = None

    def mIsConnectable(self, aHost = None):

        _isConnectable = True
        if self.__state != ebLocalInitialized:
            _isConnectable = False

        if aHost is not None and type(aHost) == type(""):
            self.__host = aHost.split('.')[0]

        if self.__host is None:
            _isConnectable = False

        if self.__host not in ('local', 'localhost', socket.gethostname().split('.')[0]):
            _isConnectable = False

        return _isConnectable

    def mConnect(self, aHost = None):

        if self.__state != ebLocalInitialized:
            raise Exception('ebLocal::mConnect : Local object already connected')

        if aHost is not None and type(aHost) == type(""):
            self.__host = aHost.split('.')[0]

        if self.__host is None:
            raise Exception('ebLocl::mConnect : Local hostname provided is incorrect: %s' % (str(self.__host)))

        if self.__host not in ('local', 'localhost', socket.gethostname().split('.')[0]):
            raise Exception('ebLocal::mConnect : Local object host invalid:', self.__host)

        self.__state = ebLocalConnected

    def mReconnect(self, aHost=None):
        pass

    # TODO: Switch to communicate() method to interact with the child process
    @ebRecordReplay.mRecordReplayWrapper
    def mExecuteCmd(self, aCmd, aCurrDir=None, aStdIn=subprocess.PIPE, aStdOut=subprocess.PIPE, aStdErr=subprocess.PIPE, aTimeout=None, aDecodeUtf8=False):

        self.__proc = None
        if aCmd:
            if self.__debug:
                ebLogDebug('*** ebLocal::mExecuteCmd: %s' % (aCmd))
            # xxx/MR: Switch to _args
            _args = shlex.split(aCmd)
            _current_dir = aCurrDir
            _stdin = aStdIn
            _std_out = aStdOut
            _stderr = aStdErr
            _timeout = aTimeout
            if _timeout:
                self.__timeout = _timeout
            _proc = subprocess.Popen(_args, stdin=_stdin, stdout=_std_out, stderr=_stderr, cwd=_current_dir, env=self.__env)
            self.__proc = wrapStrBytesFunctions(_proc)
            return wrapStrBytesFunctions(_proc.stdin), wrapStrBytesFunctions(_proc.stdout), wrapStrBytesFunctions(_proc.stderr)

        self.__rc = None

        return None, None, None

    def mExecuteCmdLog(self, aCmd, aCurrDir=None, aStdIn=subprocess.PIPE, aStdOut=subprocess.PIPE, aStdErr=subprocess.PIPE, aTimeout=None):

        # xxx/MR: Removed stdin PIPE
        if aCmd:
            _args = shlex.split(aCmd)
            _current_dir = aCurrDir
            _stdin = aStdIn
            _std_out = aStdOut
            _stderr = aStdErr
            _timeout = aTimeout
            if _timeout:
                self.__timeout = _timeout
            cmd = subprocess.Popen(_args, stdin=_stdin, stdout=_std_out, stderr=_stderr, cwd=_current_dir)
            return (wrapStrBytesFunctions(stream) for stream in (cmd.stdin, cmd.stdout, cmd.stderr))

    @ebRecordReplay.mRecordReplayWrapper
    def mGetCmdExitStatus(self):

        if self.__proc is None:
            raise Exception('ebLocal::mGetCmdExitStatus : PROC object is invalid')

        self.__proc.wait(timeout=self.__timeout)
        return self.__proc.returncode

    def mFileExists(self, aFilename):

        return os.path.isfile(aFilename)

    def mGetFileInfo(self, aFileName):
        return os.stat(aFileName)

    def mReadFile(self, aFilename):
        _out = ''
        with open(aFilename, 'r') as _file:
            _out =  _file.read()
        return _out

    def mCopyFile(self, aFilename, aRemotePath=None):

        if self.__debug:
            ebLogDebug('*** ebLocal::mCopyFile: %s -> %s' % (aFilename, aRemotePath))
        shutil.copyfile(aFilename,aRemotePath)

    def mMakeDir(self, aRemotePath):

        assert(False)

    def mChmodFile(self, aFilename, aPerm=None):

        assert(False)

    def mDisconnect(self):

        if self.__state == ebLocalDisconnected:
            return
        self.__state = ebLocalDisconnected

    def mSetupPwdLess(self, aUser=None, aPwd=None):

        pass

    def mSetupSSHKey(self, aUser=None, aPwd=None):

        pass

