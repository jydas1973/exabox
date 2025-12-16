"""
 Copyright (c) 2014, 2024, Oracle and/or its affiliates.

NAME:
    Connection - Basic functionality for Node Connection

FUNCTION:
    Provide basic/core API for managing connection to local/remote Node

NOTE:
    None

History:
    mirivier    08/21/2014 - Create file
    mirivier    03/22/2017 - BM NAT Support
    hgaldame    10/12/2017 - Add Support for Fetch key in mConnect
    dekuckre    04/11/2019 - Add support to execute cmds as sudo/non-sudo
    ndesanto    06/02/2020 - Added mIsConnectable method
    jlombera    01/12/2021 - Bug 32295581: add method
                             exaBoxConnection.mWriteFile()
    jesandov    03/31/2023 - 35141247 - Add SSH Connection Pool
    scoral      03/21/2023 - Enh 34734317: Implemented mGetFileInfo

"""

from exabox.network.osds.sshgen import sshconn
from exabox.network.osds.sshgen import setup_remote_host
from exabox.core.Context import get_gcontext
from exabox.log.LogMgr import ebLogDebug

from subprocess import PIPE

ebConnInitialized  = 0
ebConnConnected    = 1
ebConnDisconnected = 1 << 1

class exaBoxConnection(object):

    def __init__(self, aHost = None, aOptions=None):

        self.__host     = aHost
        self.__ssh_conn = None
        self.__options  = aOptions
        self.__state    = ebConnInitialized
        self.__pwd      = None
        self.__user     = None
        self.__debug    = False
        self.__sudo     = None
        self.__exakmsEntry = None

        self.__max_retries = get_gcontext().mCheckConfigOption('ssh_connect_max_retries')
        if self.__max_retries is None:
            self.__max_retries = 10
        else:
            self.__max_retries = int(self.__max_retries)

    def mGetMaxRetries(self):
        return self.__max_retries

    def mSetMaxRetries(self, aValue):
        self.__max_retries = aValue

    def mGetSudo(self):
        return self.__sudo

    def mSetSudo(self, aFlag):
        self.__sudo = aFlag

    def mGetConsoleRawOutput(self):
        if self.__ssh_conn:
            return self.__ssh_conn.mGetConsoleRawOutput()
        return ""

    def mSetDebug(self,aDebugMode):
        self.__debug = aDebugMode

    def mSetUser(self,aUser):
        self.__user = aUser

    def mSetPassword(self,aPassword):

        self.__pwd = aPassword

    def mSetExaKmsEntry(self,aKey):

        self.__exakmsEntry = aKey

    def mIsConnectable(self, aHost, aTimeout = None, aKeyOnly=None):

        _isConnectable = False
        if self.__state != ebConnInitialized:
            raise Exception('ebConnection::mIsConnectable : Connection already connected')

        if self.__state == ebConnConnected:
            return

        if aHost != None:
            self.__host = aHost

        if not self.__host:
            raise Exception('ebConnection::mIsConnectable : Host undefined')

        _ctx = get_gcontext()
        if _ctx.mCheckRegEntry('_natHN_'+self.__host):
            self.__host = _ctx.mGetRegEntry('_natHN_'+self.__host)
            if self.__debug:
                ebLogDebug('*** CONN_CONNECT_USING_NATHN: %s/%s' % (aHost,self.__host))
        self.__ssh_conn = sshconn(self.__host, self.__options)
        if self.__pwd != None:
            self.__ssh_conn.mSetPassword(self.__pwd)
        if self.__exakmsEntry != None:
            self.__ssh_conn.mSetExaKmsEntry(self.__exakmsEntry)
        if self.__user != None:
            self.__ssh_conn.mSetUser(self.__user)
        if self.__sudo != None:
            self.__ssh_conn.mSetSudo(self.__sudo)

        _isConnectable = self.__ssh_conn.mIsConnectable(aTimeout, aKeyOnly)
        if _isConnectable:
            self.__state = ebConnConnected
        else:
            self.__state = ebConnDisconnected

        return _isConnectable

    def mIsConnectionActive(self):

        try:

            if self.__ssh_conn:
                _client = self.__ssh_conn.mGetClient()
                if _client and _client.get_transport():
                    return _client.get_transport().is_active()

        except:
            return False

        return False

    def mConnect(self, aHost = None, aKeyOnly=None):

        self.mConnectTimed(aHost, aKeyOnly)

    def mConnectAuthInteractive(self, aHost, aTimeout=None):

        if self.__state != ebConnInitialized:
            raise Exception('ebConnection::mConnect : Connection already connected')

        if self.__state == ebConnConnected:
            return

        if aHost != None:
            self.__host = aHost

        if not self.__host:
            raise Exception('ebConnection::mConnect : Host undefined')

        _ctx = get_gcontext()
        if _ctx.mCheckRegEntry('_natHN_'+self.__host):
            self.__host = _ctx.mGetRegEntry('_natHN_'+self.__host)
            if self.__debug:
                ebLogDebug('*** CONN_CONNECT_USING_NATHN: %s/%s' % (aHost,self.__host))
        self.__ssh_conn = sshconn(self.__host, self.__options)
        if self.__pwd != None:
            self.__ssh_conn.mSetPassword(self.__pwd)
        if self.__exakmsEntry != None:
            self.__ssh_conn.mSetExaKmsEntry(self.__exakmsEntry)
        if self.__user != None:
            self.__ssh_conn.mSetUser(self.__user)
        if self.__sudo != None:
            self.__ssh_conn.mSetSudo(self.__sudo)

        self.__ssh_conn.mConnectAuthInteractive(aTimeout)

        self.__state = ebConnConnected

    def mConnectTimed(self, aHost, aTimeout = None, aKeyOnly=None):

        if self.__state != ebConnInitialized:
            raise Exception('ebConnection::mConnect : Connection already connected')

        if self.__state == ebConnConnected:
            return

        if aHost != None:
            self.__host = aHost

        if not self.__host:
            raise Exception('ebConnection::mConnect : Host undefined')

        _ctx = get_gcontext()
        if _ctx.mCheckRegEntry('_natHN_'+self.__host):
            self.__host = _ctx.mGetRegEntry('_natHN_'+self.__host)
            if self.__debug:
                ebLogDebug('*** CONN_CONNECT_USING_NATHN: %s/%s' % (aHost,self.__host))
        self.__ssh_conn = sshconn(self.__host, self.__options)
        if self.__pwd != None:
            self.__ssh_conn.mSetPassword(self.__pwd)
        if self.__exakmsEntry != None:
            self.__ssh_conn.mSetExaKmsEntry(self.__exakmsEntry)
        if self.__user != None:
            self.__ssh_conn.mSetUser(self.__user)
        if self.__sudo != None:
            self.__ssh_conn.mSetSudo(self.__sudo)

        self.__ssh_conn.mSetMaxRetries(self.__max_retries)
        self.__ssh_conn.mConnect(aTimeout, aKeyOnly)

        self.__state = ebConnConnected

    def mReconnect(self, aHost = None):

        self.mDisconnect()
        self.mConnect(aHost)

    def mGetSSHClient(self):
        if self.__ssh_conn:
            return self.__ssh_conn.mGetSSHClient()
        return None

    def mExecuteCmdAsync(self,aCmd,aCallBacks):

        if self.__ssh_conn and aCmd:
            return self.__ssh_conn.mExecuteCmdAsync(aCmd,aCallBacks)

    def mExecuteCmdsAuthInteractive(self, aWaitExecList):
    
        if self.__ssh_conn and aWaitExecList:
            return self.__ssh_conn.mExecuteCmdsAuthInteractive(aWaitExecList)

    def mExecuteCmd(self, aCmd, aCurrDir=None, aStdIn=PIPE, aStdOut=PIPE, aStdErr=PIPE, aTimeout=None, aDecodeUtf8=False):
        _curr_dir = aCurrDir
        _stdin = aStdIn
        _std_out = aStdOut
        _stderr = aStdErr
        _timeout = aTimeout
        _decodeutf8 = aDecodeUtf8

        if self.__ssh_conn and aCmd:
            return self.__ssh_conn.mExecuteCmd(aCmd, aCurrDir=_curr_dir, aStdIn=_stdin, aStdOut=_std_out, aStdErr=_stderr, aTimeout=_timeout, aDecodeUtf8=_decodeutf8)

    def mExecuteCmdLog(self, aCmd, aCurrDir=None, aStdIn=PIPE, aStdOut=PIPE, aStdErr=PIPE, aTimeout=None):
        _curr_dir = aCurrDir
        _stdin = aStdIn
        _std_out = aStdOut
        _stderr = aStdErr
        _timeout = aTimeout

        if self.__ssh_conn and aCmd:
            return self.__ssh_conn.mExecuteCmdLog(aCmd, aCurrDir=_curr_dir, aStdIn=_stdin, aStdOut=_std_out, aStdErr=_stderr, aTimeout=_timeout)

    def mExecuteScript(self, aCmd):

        if self.__ssh_conn and aCmd:
            return self.__ssh_conn.mExecuteScript(aCmd)

    def mGetCmdExitStatus(self):

        if self.__ssh_conn:
            return self.__ssh_conn.mGetCmdExitStatus()

    def mFileExists(self, aFilename):
        if self.__ssh_conn and aFilename:
            return self.__ssh_conn.mFileExists(aFilename)

    def mGetFileInfo(self, aFilename):
        if self.__ssh_conn and aFilename:
            return self.__ssh_conn.mGetFileInfo(aFilename)

    def mReadFile(self, aFilename: str) -> bytes:
        if self.__ssh_conn and aFilename:
            return self.__ssh_conn.mReadFile(aFilename)

    def mWriteFile(self, aFilepath: str, aData: bytes,
                   aAppend: bool = False) -> None:
        """Write data to a remote file.

        aFilepath must not be start with '~'; this is not expanded to remote
        user's HOME.

        :param aFilename: remote filepath to write to.
        :param aData: data to write to file.
        :param aAppend: whether to append to file rather than
            overwrite/truncate it.
        """
        if self.__ssh_conn:
            self.__ssh_conn.mWriteFile(aFilepath, aData, aAppend)

    def mCopyFile(self, aFilename, aRemotePath=None):

        if self.__ssh_conn and aFilename:
            return self.__ssh_conn.mCopyFile(aFilename, aRemotePath)

    def mCopy2Local(self, aFilename, aLocalPath=None):

        if self.__ssh_conn and aFilename:
            return self.__ssh_conn.mCopy2Local(aFilename, aLocalPath)

    def mMakeDir(self, aRemotePath):

        if self.__ssh_conn and aRemotePath:
            return self.__ssh_conn.mMakeDir(aRemotePath)

    def mChmodFile(self, aFilename, aPerm=None):
        if self.__ssh_conn and aFilename:
            return self.__ssh_conn.mChmodFile(aFilename, aPerm)

    def mDisconnect(self):

        if self.__state == ebConnDisconnected:
            return

        if self.__ssh_conn:
            self.__ssh_conn.mDisconnect()
            self.__ssh_conn = None

        self.__state = ebConnDisconnected

    def mSetupPwdLess(self, aUser=None, aPwd=None):

        if self.__ssh_conn:
            self.__ssh_conn.mSetupPwdLess(aUser, aPwd)

    def mSetupSSHKey(self, aUser=None, aPwd=None):

        if self.__ssh_conn:
            self.__ssh_conn.mSetupSSHKey(aUser, aPwd)
