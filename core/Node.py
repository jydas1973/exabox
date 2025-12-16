"""
 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    Node - Basic functionality

FUNCTION:
    Provide basic/core API for managing Node (DB Node, Switches, Cells,...)

NOTE:
    None

History:
    avimonda    10/31/2025 - Bug 38427813: Introduced separate checksum methods
                             for local and remote files, reused them in
                             sysimagehandler.py and mCompareFiles
    avimonda    09/19/2025 - Bug 38324744 - EXACC GEN 2 | PATCHING | SSHD
                             TIMEOUT ERRORS MISINTERPRETED AS SSHD NOT RUNNING
    apotluri    08/05/2025 - 38176674 - EXACS:25.2.2.1: DOM0 APPLY PATCH 
                             OPERATION HUNGWHILE CHECKING IMAGEINFO AFTER 
                             PATCHMGR FAILURE
    ririgoye    06/02/2025 - 38014410: SOP: REMOTE EXECUTION FAILED DUE TO 
                             EXACLOUDRUNTIMEERROR
    ririgoye    05/05/2025 - 37588295: Exacloud sop local remote execution will
                             hang on large output
    gparada     02/10/2025 - 37569998 Add out and err to matched regex mockcmd
    dekuckre    29/01/2024 - 35656778: Update mSingleLineOutputCellcli
    mirivier    08/21/2014 - Create file
    hgaldame    10/12/2017 - Add Support for Fetch key in mConnect
    dekuckre    04/11/2019 - Add support to execute cmds as sudo/non-sudo
    ndesanto    06/02/2020 - Added mIsConnectable method
    jlombera    01/12/2021 - Bug 32295581: add method sshconn.mWriteFile()
    jesandov    03/31/2023 - 35141247 - Add SSH Connection Pool
    scoral      03/21/2023 - Enh 34734317: Implemented mGetFileInfo
    aararora    01/29/2024 - Bug 36182157: Added a default timeout of 180 seconds for connection to happen
    gparada     03/25/2025 - Bug 36409407 Add retry to mCopyFile for resiliency
"""

from exabox.tools.profiling.profiler import measure_exec_time
from exabox.tools.profiling.stepwise import steal_hostname, steal_hostname_cmd, steal_hostname_file_copied
from exabox.tools.AttributeWrapper import wrapStrBytesFunctions
from exabox.core.Context import get_gcontext
from exabox.network.Connection import exaBoxConnection
from exabox.network.Local import exaBoxLocal
from exabox.network.Network import exaBoxNetwork
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogTrace
from exabox.core.MockCommand import exaMockCommand
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.utils import common
from contextlib import closing
from paramiko import SFTPAttributes

import threading
import os, socket, shlex
import hashlib
import re
import copy
import subprocess
import errno
from io import StringIO
from subprocess import PIPE
import shutil
import tempfile

ebNodeStateInitialized  = 0
ebNodeStateConnected    = 1
ebNodeStateDisconnected = 1 << 1

try:
    from subprocess import DEVNULL # Python 3X
except ImportError:
    DEVNULL = open(os.devnull, 'wb')


class exaBoxNodePool:

    def __init__(self, aId):
        self.__id = aId
        self.__connections = {}

    def mCreateConnection(self, aExaBoxNode, aHost=None, aOptions=None, aTimeout=None, aKeyOnly=None):

        _host = aHost
        _user = aExaBoxNode.mGetUser()

        if aExaBoxNode.mIsLocal():
            _host = socket.gethostname().split('.')[0]

            try:
                _user = os.getlogin()
            except:
                _user = "local"

        else:
            if _host and get_gcontext().mCheckRegEntry('_natHN_' + _host):
                _host = get_gcontext().mGetRegEntry('_natHN_' + _host)

        if not _user:

            if get_gcontext().mCheckRegEntry("domU_set"):
                if _host in get_gcontext().mGetRegEntry("domU_set") or \
                   aHost in get_gcontext().mGetRegEntry("domU_set"):
                    _user = "default"
                else:
                    _user = "root"

        _key = f"{_user}@{_host}"

        if _key in self.__connections:
            _activeNode = self.__connections[_key]

            aExaBoxNode.mSetUser(_activeNode.mGetUser())
            aExaBoxNode.mSetHostname(_activeNode.mGetHostname())
            aExaBoxNode.mSetExaKmsEntry(_activeNode.mGetExaKmsEntry())

            if aExaBoxNode.mIsLocal():
                aExaBoxNode.mSetConnection(_activeNode.mGetConnection())
                aExaBoxNode.mSetConnectionState(_activeNode.mGetConnectionState())

            else:

                if _activeNode.mGetConnection() and _activeNode.mGetConnection().mIsConnectionActive():
                    aExaBoxNode.mSetConnection(_activeNode.mGetConnection())
                    aExaBoxNode.mSetConnectionState(_activeNode.mGetConnectionState())

                else:
                    aExaBoxNode.mDisconnect()
                    aExaBoxNode.mConnectTimed(aHost, aOptions, aTimeout, aKeyOnly)
                    self.__connections[_key] = aExaBoxNode

        else:

            aExaBoxNode.mConnectTimed(aHost, aOptions, aTimeout, aKeyOnly)
            self.__connections[_key] = aExaBoxNode

    def mCloseConnections(self, aHost=None):

        _host = aHost
        if _host and  get_gcontext().mCheckRegEntry('_natHN_' + _host):
            _host = get_gcontext().mGetRegEntry('_natHN_' + _host)

        _host_list = list(self.__connections.keys())
        for _key in _host_list:
            if not _host or _host in _key:

                ebLogTrace(f"Closing connection: {_key}")
                _node = self.__connections[_key]
                _node.mDisconnect(aForce=True)
                del self.__connections[_key]


class exaBoxNode(object):


    def __init__(self, aCtx, aLocal = False, Cluctrl = None ):

        if aLocal:
            self.__isLocal = True
        else:
            self.__isLocal = False

        self.__ctx     = aCtx
        self.__state   = ebNodeStateInitialized
        self.__network = None
        self.__options = aCtx.mGetArgsOptions()
        self.__connection = None
        self.__hostname = None
        self.__pwd      = None
        self.__exakmsEntry = None
        self.__user     = None
        self.__sudo     = None
        self.__cluctrl = Cluctrl

        self.__debug = False
        if self.__options is not None:
            self.__debug = self.__options.debug

        self.__mockMode = isinstance(self.__options, dict) and 'mock_cmds' in self.__options
        self.__mockModePatch = get_gcontext().mCheckConfigOption('mock_mode_patch')
        self.__mockExitCmd = 0
        self.__mockCmds = None
        self.__mockInstanceId = None

        self.__max_retries = get_gcontext().mCheckConfigOption('ssh_connect_max_retries')
        if self.__max_retries is None:
            self.__max_retries = 10
        else:
            self.__max_retries = int(self.__max_retries)

    def mSetMockMode(self, aMock=False):
        self.__mockMode = aMock

    def mGetMockMode(self):
        return self.__mockMode

    def mGetMaxRetries(self):
        return self.__max_retries

    def mSetMaxRetries(self, aValue):
        self.__max_retries = aValue

    def mGetSudo(self):
        return self.__sudo

    def mSetSudo(self, aFlag):
        self.__sudo = aFlag

    def mIsRemote(self):
        return not self.__isLocal

    def mIsLocal(self):
        return self.__isLocal

    def mIsConnected(self):
        if self.__state == ebNodeStateConnected:
            return True
        else:
            return False

    def mGetConnection(self):
        return self.__connection

    def mSetConnection(self, aValue):
        self.__connection = aValue

    def mGetConnectionState(self):
        return self.__state

    def mSetConnectionState(self, aValue):
        self.__state = aValue

    def mGetHostname(self):
        return self.__hostname

    def mSetHostname(self, aHostname):
        self.__hostname = aHostname

    def mGetConsoleRawOutput(self):
        if self.__connection:
            return self.__connection.mGetConsoleRawOutput()
        return ""

    # TODO: Push this to connection / OSDs SSH
    def mResetHostKey(self, aHost):

        if aHost:
            if not self.validateIpOrHostname(aHost):
                ebLogError('*** Invalid hostname provided. Aborting')
                return
            _cmd = '/bin/ssh-keygen -R ' +aHost
            self.mExecuteLocal(_cmd, aStdOut=DEVNULL, aStdErr=DEVNULL)
        if len(aHost.split('.')) == 1:
            # TODO: This does _NOT_ work with non us.oracle.com Domain (e.g. pre-prod)
            #       Make this a configuration option w/ default domain
            _cmd = '/bin/ssh-keygen -R '+aHost+'.us.oracle.com'
            self.mExecuteLocal(_cmd, aStdOut=DEVNULL, aStdErr=DEVNULL)

    def mExecuteLocal(self, aCmd, aCurrDir=None, aStdIn=PIPE, aStdOut=PIPE, aStdErr=PIPE):

        if self.__debug:
            ebLogDebug('*** mExecuteLocal: %s' % (aCmd))

        _args = shlex.split(aCmd)
        _current_dir = aCurrDir
        _stdin = aStdIn
        _std_out = aStdOut
        _stderr = aStdErr
        _proc = subprocess.Popen(_args, stdin=_stdin, stdout=_std_out, stderr=_stderr, cwd=_current_dir)
        _std_out, _std_err = wrapStrBytesFunctions(_proc).communicate()
        _rc = _proc.returncode
        return _rc, None, _std_out, _std_err

    #Check if given input is either in a valid hostname or ipv4/ipv6 address format.
    def validateIpOrHostname(self, aHostOrIP):
        try:
            socket.inet_pton(socket.AF_INET, aHostOrIP)
            return True
        except socket.error:
            try:
                socket.inet_pton(socket.AF_INET6, aHostOrIP)
                return True
            except socket.error:
                #doing simple checks for hostnames, instead of rigorous checking in terms of length and starting character restrictions.
                if not re.match("^[0-9A-Za-z\-\.]+$", aHostOrIP):
                    return False
                return True

    def mGetUser(self):
        return self.__user

    def mSetUser(self,aUser):
        self.__user = aUser

    def mSetPassword(self,aPassword):

        self.__pwd = aPassword

    def mGetExaKmsEntry(self):
        return self.__exakmsEntry

    def mSetExaKmsEntry(self,aEntry):

        self.__exakmsEntry = aEntry

    def mIsConnectable(self, aHost=None, aOptions=None, aTimeout=None, aKeyOnly=None):

        _isConnectable = False

        if not aOptions:
            aOptions = self.__options

        # note: socket.gethostname() can return the FQDN
        if self.mIsLocal():
            aHost = socket.gethostname().split('.')[0]

        self.__hostname = aHost

        if self.__mockMode:
            return True

        if self.mIsLocal():
            self.__connection = exaBoxLocal(aHost, aOptions)
            _isConnectable = self.__connection.mIsConnectable()
        else:
            self.__connection = exaBoxConnection(aHost, aOptions)
            if self.__pwd != None:
                self.__connection.mSetPassword(self.__pwd)
            if self.__exakmsEntry != None:
                self.__connection.mSetExaKmsEntry(self.__exakmsEntry)
            if self.__user != None:
                self.__connection.mSetUser(self.__user)
            if self.__sudo != None:
                self.__connection.mSetSudo(self.__sudo)

            # pylint: disable=E1121
            _isConnectable = self.__connection.mIsConnectable(aHost, aTimeout, aKeyOnly)
            # pylint: enable=E1121

        return _isConnectable

    def mConnect(self, aHost=None, aOptions=None, aTimeout=None, aKeyOnly=None):

        # Bug 36182157: Added a default timeout of 180 seconds (3 minutes) for connection to happen
        if not aTimeout:
            aTimeout = get_gcontext().mCheckConfigOption('ssh_connect_default_timeout_sec')

        _connkey = f"{threading.get_ident()}-{os.getpid()}"

        if get_gcontext().mCheckRegEntry(f'SSH-POOL-{_connkey}'):
            _connectionPool = get_gcontext().mGetRegEntry(f'SSH-POOL-{_connkey}')
            _connectionPool.mCreateConnection(self, aHost, aOptions, aTimeout, aKeyOnly)

        else:
            self.mConnectTimed(aHost, aOptions, aTimeout, aKeyOnly)

    def mConnectAuthInteractive(self, aHost=None, aOptions=None, aTimeout=None):

        if self.__state == ebNodeStateConnected:
            return

        # note: socket.gethostname() can return the FQDN
        if self.mIsLocal():
            aHost = socket.gethostname().split('.')[0]

        self.__hostname = aHost

        if self.__mockMode:
            return

        if self.mIsLocal():
            self.__connection = exaBoxLocal(aHost, aOptions)
            self.__connection.mConnect()
        else:
            self.__connection = exaBoxConnection(aHost, aOptions)
            if self.__pwd != None:
                self.__connection.mSetPassword(self.__pwd)
            if self.__exakmsEntry != None:
                self.__connection.mSetExaKmsEntry(self.__exakmsEntry)
            if self.__user != None:
                self.__connection.mSetUser(self.__user)
            if self.__sudo != None:
                self.__connection.mSetSudo(self.__sudo)

            self.__connection.mConnectAuthInteractive(aHost, aTimeout)
        self.__state = ebNodeStateConnected

    @measure_exec_time(steal_hostname)
    def mConnectTimed(self, aHost=None, aOptions=None, aTimeout=None, aKeyOnly=None):

        if self.__state == ebNodeStateConnected:
            return

        if not aOptions:
            aOptions = self.__options

        # note: socket.gethostname() can return the FQDN
        if self.mIsLocal():
            aHost = socket.gethostname().split('.')[0]

        self.__hostname = aHost

        if self.__mockMode:
            return

        if self.mIsLocal():
            self.__connection = exaBoxLocal(aHost, aOptions)
            self.__connection.mConnect()
        else:
            self.__connection = exaBoxConnection(aHost, aOptions)
            if self.__pwd != None:
                self.__connection.mSetPassword(self.__pwd)
            if self.__exakmsEntry != None:
                self.__connection.mSetExaKmsEntry(self.__exakmsEntry)
            if self.__user != None:
                self.__connection.mSetUser(self.__user)
            if self.__sudo != None:
                self.__connection.mSetSudo(self.__sudo)

            self.__connection.mSetMaxRetries(self.__max_retries)
            self.__connection.mConnectTimed(aHost, aTimeout, aKeyOnly)

        self.__state = ebNodeStateConnected


    def mGetSSHClient(self):
        if not self.mIsLocal() and self.__connection is not None:
            return self.__connection.mGetSSHClient()
        return None


    @measure_exec_time(steal_hostname)
    def mDisconnect(self, aForce=False):

        _connkey = f"{threading.get_ident()}-{os.getpid()}"
        if get_gcontext().mCheckRegEntry(f'SSH-POOL-{_connkey}'):
            if not aForce:
                return

        if self.__connection:
            self.__connection.mDisconnect()
            self.__connection = None

        self.__mockExitCmd = 0
        self.__mockCmds = None
        self.__mockInstanceId = None

        self.__state = ebNodeStateDisconnected

    def mExecuteCmdsAuthInteractive(self, aWaitExecList):
        if self.__connection and aWaitExecList:
            return self.__connection.mExecuteCmdsAuthInteractive(aWaitExecList)

    # Execute a cmd line tool/script
    def mExecuteScript(self, aCmd):
        if self.__connection and aCmd:
            return self.__connection.mExecuteScript(aCmd)

    def mParseCmdCellCli(self, aI, aO, aE):
        ebLogInfo('*** mExecuteCmdCLI ***')
        _i = aI
        _o = aO
        _e = aE

        _o2 = tempfile.NamedTemporaryFile(mode = "w+")
        _output = _o.readlines()
        if _output:
            for _line in _output:
                if "CELL-" in _line.strip():
                    self.__cluctrl.mSetProvErr("CELLCLI : " + _line.strip().split(":")[0])
                _o2.write(_line)

        _o.close()
        _o2.seek(0, 0)
        return _i,_o2,_e

    # Execute a cmd line tool/script
    @measure_exec_time(steal_hostname_cmd)
    def mExecuteCmdCellcli(self, aCmd, aCurrDir=None, aStdIn=PIPE, aStdOut=PIPE, aStdErr=PIPE, aTimeout=None):
        _curr_dir = aCurrDir
        _stdin = aStdIn
        _std_out = aStdOut
        _stderr = aStdErr
        _timeout = aTimeout

        if self.__mockMode:
            return self.mExecuteMock(aCmd)

        if self.__connection and aCmd:
            _i,_o,_e = self.__connection.mExecuteCmd(aCmd, aCurrDir=_curr_dir, aStdIn=_stdin, aStdOut=_std_out, aStdErr=_stderr, aTimeout=_timeout)
            if self.__cluctrl and self.__connection.mGetCmdExitStatus():
                return self.mParseCmdCellCli(_i,_o,_e)
            else:
                return _i,_o,_e

    # Execute a cmd line tool/script
    @measure_exec_time(steal_hostname_cmd)
    def mExecuteCmd(self, aCmd, aCurrDir=None, aStdIn=PIPE, aStdOut=PIPE, aStdErr=PIPE, aTimeout=None, aDecodeUtf8=False):
        _curr_dir = aCurrDir
        _stdin = aStdIn
        _std_out = aStdOut
        _stderr = aStdErr
        _timeout = aTimeout
        _decodeutf8 = aDecodeUtf8

        if self.__mockMode:
            return self.mExecuteMock(aCmd)

        if self.__connection and aCmd:
            return self.__connection.mExecuteCmd(aCmd, aCurrDir=_curr_dir, aStdIn=_stdin, aStdOut=_std_out, aStdErr=_stderr, aTimeout=_timeout, aDecodeUtf8=_decodeutf8)

    # Execute a cmd line tool/script and display the result in the Log/Console
    @measure_exec_time(steal_hostname_cmd)
    def mExecuteCmdLog(self, aCmd, aCurrDir=None, aStdIn=PIPE, aStdOut=PIPE, aStdErr=PIPE, aTimeout=None):
        _curr_dir = aCurrDir
        _stdin = aStdIn
        _std_out = aStdOut
        _stderr = aStdErr
        _timeout = aTimeout

        if self.__mockMode:
            return self.mExecuteMock(aCmd)

        if self.__connection and aCmd:
            return self.__connection.mExecuteCmdLog(aCmd, aCurrDir=_curr_dir, aStdIn=_stdin, aStdOut=_std_out, aStdErr=_stderr, aTimeout=_timeout)

    #Execute a cmd line tool/script asynchronously (e.g. non blocking). Callbacks set needs to be provided
    def mExecuteCmdAsync(self,aCmd,aCallBacks):

        if self.__connection and aCmd:
            return self.__connection.mExecuteCmdAsync(aCmd,aCallBacks)

    # Return when possible the exit status of the last Cmd that ran
    def mGetCmdExitStatus(self):
        if self.__mockMode:
            return self.__mockExitCmd

        if self.__connection:
            return self.__connection.mGetCmdExitStatus()

    # Check if a file exists (absolute path is required)
    def mFileExists(self, aFilename):

        if self.__mockMode:
            self.mExecuteCmd("/bin/test -e {0}".format(aFilename))
            return self.mGetCmdExitStatus() == 0

        if self.__connection and aFilename:
            return self.__connection.mFileExists(aFilename)

    def mGetFileInfo(self, aFilename):
        if self.__mockMode:
            _i, _o, _e = self.mExecuteCmd("/bin/stat {0}".format(aFilename))
            _out = _o.readlines()
            # Get file size
            _sizeLine, *_ = [ line for line in _out if 'Size:' in line ]
            _sizeLineSplit = _sizeLine.split()
            _sizeIx = _sizeLineSplit.index("Size:")
            _size = int(_sizeLineSplit[_sizeIx + 1])

            # Build result
            _result = SFTPAttributes()
            _result.st_size = _size
            return _result

        if self.__connection and aFilename:
            return self.__connection.mGetFileInfo(aFilename)

    # Copy file
    @measure_exec_time(steal_hostname_file_copied)
    def mCopyFile(self, aFilename, aRemotePath=None, aRetryCnt=0):        
        _rtn = False

        _attempts = 0
        # Do at least one time
        while _attempts <= aRetryCnt:
            if self.__mockMode:
                self.mExecuteCmd("/bin/scp {0} {1}".format(aFilename, aRemotePath))
                if not aRetryCnt:
                    ebLogTrace("Copy in mock mode. No retry. Exit with None.")
                    return

            if self.__connection and aFilename:
                _rtn = self.__connection.mCopyFile(aFilename, aRemotePath)
                if not aRetryCnt:
                    ebLogTrace(f"Copy with No retry. Exit code: {_rtn}")
                    return _rtn

            # If file copied OK, then exit (no need to retry)
            if not self.__mockMode:
                return _rtn
            _attempts += 1
        
        if not self.__mockMode and not _rtn:
            _msg = 'File was not copied OK <{0}> or checksum was not OK.'
            _msg = _msg.format(aFilename)
            raise ExacloudRuntimeError(0x0779, 0xA, _msg)
    
    # Read file
    def mReadFile(self, aFilename: str) -> bytes:
        if self.__mockMode:
            _i, _o, _e = self.mExecuteCmd(f"/bin/cat {aFilename}")
            return _o.read().encode('utf-8')
        if self.__connection and aFilename:
            return self.__connection.mReadFile(aFilename)

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
        if self.__connection:
            self.__connection.mWriteFile(aFilepath, aData, aAppend)

    # Copy to Local
    def mCopy2Local(self, aFilename, aLocalPath=None):
        if self.__connection and aFilename:
            return self.__connection.mCopy2Local(aFilename, aLocalPath)

    # Mkdir
    def mMakeDir(self, aRemotePath):
        if self.__connection and aRemotePath:
            return self.__connection.mMakeDir(aRemotePath)

    # Chown file
    def mChmodFile(self, aFilename, aPerm=None):
        if self.__connection and aFilename:
            return self.__connection.mChmodFile(aFilename, aPerm)

    # Execute one of support operation on the Node (e.g. reboot, shutdown,...)
    def mExecuteOp(self, aOperation ):
        pass

    def mUpdateHostInfo(self):
        pass

    def mUpdateNetworkInfo(self):

        self.__network = exaBoxNetwork(self)
        self.__network.mDiscover()

    def mSetupPwdLess(self, aUser=None, aPwd=None):

        if self.__connection:
            if not aUser:
                uname = self.__ctx.mGetArgsOptions().username
            if not aPwd:
                pwd   = self.__ctx.mGetArgsOptions().password
            return self.__connection.mSetupPwdLess(aUser=uname, aPwd=pwd)

    def mSetupSSHKey(self, aUser=None, aPwd=None):

        if self.__connection:
            if not aUser:
                uname = self.__options.username
            if not aPwd:
                pwd   = self.__options.password
            return self.__connection.mSetupSSHKey(aUser=uname, aPwd=pwd)

    def mDownloadRemoteFile(self, aLogFile, aDestDir):
        """This method is used to transfer the logs generated at remote node to a local destination directory.

        Args:
            self (Node object): Node object with connection to the remote node
            aLogFile (str): Path to the remote log file
            aDestDir (str): Path to the local directory to copy the remote log to

        Returns:
            bool: Returns True if the download was successful. Returns False if there was an issue.
        """
        if not os.path.isabs(aLogFile):
            ebLogError(f"The path {aLogFile} is not an absolute path.")
            return False
        if self.mFileExists(aLogFile):
            # Check the space occupied by the log file - in KB
            _i, _o, _e = self.mExecuteCmd(f"/usr/bin/du {aLogFile}")
            _space_log = _o.read()
            _space_log = _space_log.strip().split()[0].strip()
            ebLogInfo(f"The disk size occupied by log file {aLogFile} is : {_space_log}")
            _av_size = common.mGetFolderFreeSize(aDestDir)
            if not _av_size:
                ebLogError(f"The path {aDestDir} does not exist.")
            else:
                ebLogInfo(f"Available disk size for folder {aDestDir} is : {_av_size}")
            # Check if available size is less than 3 times the log size to keep some buffer
            if int(_av_size) < 3*int(_space_log):
                ebLogError(f"The free disk space in dir {aDestDir} is not sufficient (Available size should be atleast 3 times the log size). The available size is {_av_size} and log {aLogFile} size is {_space_log}.")
            else:
                _local_tar = os.path.join(aDestDir, os.path.basename(aLogFile))
                # Copy the logs to destination directory
                self.mCopy2Local(aLogFile, _local_tar)
                ebLogInfo(f"The file {aLogFile} is copied to {_local_tar}.")
                return True
        else:
            ebLogWarn(f"The file {aLogFile} does not exist.")
        return False

    # Calculate checksum of a remote file using sha256sum
    def mGetRemoteFileCksum(self, aRemoteFile):
        """
        Calculate the checksum of a remote file using the sha256sum command.

        Args:
            aRemoteFile (str): Path to the remote file.

        Returns:
            str or None: Checksum of the remote file if successful;
                         None if the file does not exist or checksum calculation fails.
        """
        #Get the Host
        aHost=self.mGetHostname()
        if not aHost:
            aHost = "localhost"

        try:
            if not self.mFileExists(aRemoteFile):
                ebLogError(f"Remote file {aRemoteFile} does not exist on host {aHost}.")
                return None

            _sha256sum = '/bin/sha256sum'
            _cmd = f'{_sha256sum} {aRemoteFile}'
            if not self.mFileExists(_sha256sum):
                _sha256sum_in_usr_bin = '/usr/bin/sha256sum'
                _cmd = f'{_sha256sum_in_usr_bin} {aRemoteFile}' 

            _fin, _fout, _ferr = self.mExecuteCmd(_cmd)
            _out = _fout.readlines()
            if _out:
                _remote_hash = _out[0].strip().split(' ')[0]
                ebLogInfo(f'*** Calculated sha256sum for file {aRemoteFile}: {_remote_hash}')
                return _remote_hash
            else:
                ebLogError(f"Failed to calculate sha256sum for remote file {aRemoteFile}: No output from sha256sum.")
                return None
        except Exception as e:
            ebLogError(f"Error calculating sha256sum for remote file {aRemoteFile}: {str(e)}")
            return None 

    # Calculate checksum of a local file using sha256sum
    def mGetLocalFileCksum(self, aLocalFile):
        """
        Calculate the checksum of a local file using the sha256sum command.
        
        Args:
            aLocalFile (str): Path to the local file.
        
        Returns:
            str or None: Checksum of the local file if successful;
                         None if the file does not exist or checksum calculation fails.
        """
        try:
            if not os.path.exists(aLocalFile):
                ebLogError(f"Local file {aLocalFile} does not exist.")
                return None

            _sha256sum = '/bin/sha256sum'
            _cmd = f'{_sha256sum} {aLocalFile}' 
            if os.path.isfile(_sha256sum) is False:
                _sha256sum_in_usr_bin = '/usr/bin/sha256sum'
                _cmd = f'{_sha256sum_in_usr_bin} {aLocalFile}'

            _rc, _fin, _fout, _ferr = self.mExecuteLocal(_cmd)
            if _rc == 0:
                if isinstance(_fout, bytes):
                    _out = _fout.decode('utf-8').splitlines()
                else:
                    _out = _fout.splitlines()

                if _out:
                    _local_hash = _out[0].strip().split(' ')[0]
                    ebLogInfo(f'*** Calculated sha256sum for local file {aLocalFile}: {_local_hash}')
                    return _local_hash
                else:
                    ebLogError(f"Failed to calculate sha256sum for local file {aLocalFile}: No output from sha256sum.")
                    return None
            else:
                if isinstance(_ferr, bytes):
                    _stderr_str = _ferr.decode('utf-8')
                else:
                    _stderr_str = _ferr
                ebLogError(f"Failed to calculate sha256sum for local file {aLocalFile}: Return code {_rc}, Error: {_stderr_str}")
                return None
        except Exception as e:
            ebLogError(f"Error calculating sha256sum for local file {aLocalFile}: {str(e)}")
            return None

    #Compare the Files using Hashes
    def mCompareFiles(self, aLocalFile, aRemoteFile, aHashDict):

        #Get the Host
        aHost=self.mGetHostname()
        if not aHost:
            aHost = "localhost"
        _RemoteFile=aHost+aRemoteFile
        ebLogInfo("mCompareFiles: aHost = %s, aLocalFile = %s, aRemoteFile = %s" % (aHost, aLocalFile, aRemoteFile))

        #Calculate Hash of Remote File
        if 'IS_MULTIPROCESS' in os.environ and 'IS_EXACLOUD_TEST' in os.environ:
            ebLogDebug("mCompareFiles in multiprocess, skipping sha256sum")
            return True 

        #Assign Hash dict
        _hash_dict = {}
        if aHashDict is not None:
            _hash_dict = aHashDict

        try:
            # Check For Existing Hash File for Remote
            if not _RemoteFile in _hash_dict:
                _remote_hash = self.mGetRemoteFileCksum(aRemoteFile)
                if _remote_hash is None:
                    return False
                _hash_dict[_RemoteFile] = _remote_hash

            # Calculate Hash of Localfile
            _LocalFile = aLocalFile
            if not _LocalFile in _hash_dict:
                _local_hash = self.mGetLocalFileCksum(aLocalFile)
                if _local_hash is None:
                    return False
                _hash_dict[_LocalFile] = _local_hash

            # Compare the Hashes
            return _hash_dict[_RemoteFile] == _hash_dict[_LocalFile]
        except Exception as e:
            ebLogError(f"Error in mCompareFiles: {str(e)}")
            return False

    def mSingleLineOutputCellcli(self, aCommand):

        _i, _o, _e = self.mExecuteCmd(aCommand, aTimeout=300)
        if self.__cluctrl and self.mGetCmdExitStatus():
            _, _o, _ = self.mParseCmdCellCli(_i,_o,_e)
        else:
            _i, _o, _e = self.mExecuteCmd(aCommand, aTimeout=300)
        _lines = _o.readlines()
        if len(_lines) != 0:
            return _lines[0].rstrip("\n")
        else:
            return ""

    def mSingleLineOutput(self, aCommand):
        _i, _o, _e = self.mExecuteCmd(aCommand)
        _lines = _o.readlines()
        if len(_lines) != 0:
            return _lines[0].rstrip("\n")
        else:
            return ""

    # Creates a dictionary key,value for console output with a specifiec separator
    def mMultipleLineOutputWithSeparator(self, aCommand, aSeparator, aResult = {}, aTimeout=None):
        _i, _o, _e = self.mExecuteCmd(aCommand, aTimeout=aTimeout)
        for _line in _o.readlines():
            _line = re.sub(r"\s+", " ", _line)
            _line = _line.rstrip("\n")
            tuple = _line.split(aSeparator,1)
            if (len(tuple) > 1):
                aResult[tuple[0].strip()] = tuple[1].strip()
        return aResult

    def mCheckPortSSH(self, aHost, aTimeout=None):
        _host = aHost

        if self.__ctx.mCheckRegEntry('_natHN_' + _host):
            _host = self.__ctx.mGetRegEntry('_natHN_' + _host)

        if not self.mGetHostname():
            self.mSetHostname("localhost")

        if isinstance(self.__options, dict) and 'exatest' in list(self.__options.keys()):

            _cmd = "/bin/echo EXIT | /usr/bin/nc {0} 22".format(_host)
            _, _, _e = self.mExecuteCmd(_cmd)

            if self.mGetCmdExitStatus() != 0:
                ebLogWarn(_e.read())

            return self.mGetCmdExitStatus() == 0

        else:

            _sock = socket.socket()
            _sock.settimeout(aTimeout)

            with closing(_sock):
                try:
                    _result = _sock.connect_ex((_host,22))
                    if _result == 0:
                        return True
                    else:
                        if _result == errno.ECONNREFUSED:
                            ebLogWarn(f"{_host} - CONNECTION REFUSED (errno={_result})")
                        elif _result == errno.ETIMEDOUT:
                            ebLogWarn(f"{_host} - TIMEOUT (errno={_result})")
                        elif _result == errno.EHOSTUNREACH:
                            ebLogWarn(f"{_host} - NO ROUTE TO HOST (errno={_result})")
                        elif _result == errno.ENETUNREACH:
                            ebLogWarn(f"{_host} - NETWORK UNREACHABLE (errno={_result})")
                        else:
                            ebLogWarn(f"{_host} - SOCKET ERROR: {os.strerror(_result)} (errno={_result})")
                        return False
                except Exception as e:
                    ebLogWarn(e)
                    return False


    def mExecuteMock(self, aCmd):

        #Copy the mock command on the first time
        _instanceNumber = None

        if self.__mockCmds is None:
            for _host in list(sorted(self.__options['mock_cmds'].keys(), reverse=True)):
                if re.match(_host, self.mGetHostname()) is not None:
                    # Check the number of instance that is this node
                    _threadId = threading.current_thread().ident
                    if "mock_cmds_instances" not in self.__options:
                        self.__options['mock_cmds_instances'] = {}

                    if _threadId not in self.__options['mock_cmds_instances']:
                        self.__options['mock_cmds_instances'][_threadId] = {}

                    if self.mGetHostname() not in self.__options['mock_cmds_instances'][_threadId]:
                        self.__options['mock_cmds_instances'][_threadId][self.mGetHostname()] = 0

                    _instanceNumber = self.__options['mock_cmds_instances'][_threadId][self.mGetHostname()]
                    self.__mockInstanceId = _instanceNumber

                    # Copy the mock command of that instance
                    try:
                        self.__mockCmds = list(self.__options['mock_cmds'][_host][_instanceNumber])
                    except IndexError:
                        _msg = "Invalid Instance Number\n"
                        _msg += "The amount of times called mConnect is greater than tne number of instances in the test "
                        _msg += "hostname: {0} ".format(self.mGetHostname())
                        _msg += 'InstaceExpected: {0}'.format(_instanceNumber)
                        raise IndexError(_msg)

                    # Increment the instance for the next iteration
                    self.__options['mock_cmds_instances'][_threadId][self.mGetHostname()] = _instanceNumber+1
                    break

        #Find the current mock command that match the cmd
        if self.__mockCmds is None:
            _msg = "Missing MockCmds; Hostname: {0} ".format(self.mGetHostname())
            _msg += 'InstaceExpected: {0}'.format(_instanceNumber)
            raise IndexError(_msg)


        for _current in self.__mockCmds:

            if re.search(_current.mGetCmdRegex(), aCmd) is not None:
                _stdin = ""
                _rc, _stdout, _stderr = _current.mExecuteMockCmd(aCmd, _stdin)
                self.__mockExitCmd = _rc

                if self.__debug:
                    ebLogInfo(f"Matched REGEX: `{_current.mGetCmdRegex()}` MockExecuted: << `{aCmd}` rc[{_rc}] out[{_stdout}] err[{_stderr}] >>")

                if not _current.mIsPersist():
                    self.__mockCmds.remove(_current)

                return (wrapStrBytesFunctions(StringIO(stream))
                        for stream in (_stdin, _stdout, _stderr))

        _msg = 'Node instance <{0}> of host <{1}> command not implemented: ` {2} `'
        _msg = _msg.format(self.__mockInstanceId, self.mGetHostname(), aCmd)
        raise ExacloudRuntimeError(0x0779, 0xA, _msg)

#end of file
