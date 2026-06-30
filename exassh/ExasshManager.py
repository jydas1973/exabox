"""
 Copyright (c) 2014, 2026, Oracle and/or its affiliates.

NAME:
    ExasshManager - Basic functionality

FUNCTION:
    Provide the Managment of the of the objects of type ExasshInfo

NOTE:
    Mock command details in: 
        https://confluence.oraclecorp.com/confluence/display/~jonathan.sandoval@oracle.com/Exacloud+Exatest+Framework

History:
    aararora    06/19/2026 - Bug#39568198 Support RoCE switch download without SFTP
    jesandov    06/10/2026 - Bug#39462050: Add secure client
    jesandov    04/27/2026 - Bug#39263025 Fix security issues found using IA
    aypaul      07/15/2025 - Bug#38126347 Update ssh channel implementation for reading data.
    abflores    03/14/2025 - Bug 37704409: Fix MINA FAILS IN R1 BECAUSE OEDA IS UNDEFINED
    jesandov    01/06/2024 - Add PKCS8 and TraditionalOpenSSL Format export
    ririgoye    09/09/2024 - 36348868 - EXASSH PASTE ONLY PUTS 1ST CHARACTER OF 
                             BUFFER UNTIL ANOTHER CHARACTER IS TYPED
    jesandov    09/02/2024 - 36883563: Add Paramiko Debug Mode
    ririgoye    08/02/2023 - Added function to remotely execute a file
    jesandov    26/01/2022 - Add two new options for invalid keys
    hcheon      04/07/2021 - 32737675 Resize terminal
    oespinos    11/21/2018 - 29043127 exassh table has invalid column "cluster"
    jesandov    26/09/2018 - File Creation
"""

from __future__ import print_function

import base64
import gzip
import math
import six
import sys
import pprint
import json
import os
import re
import time
import tempfile
import subprocess as sp
import shlex
import time
import paramiko
import termios
import select
import fcntl
import signal
import struct
import traceback
import logging
import uuid
from io import StringIO
from threading import Thread
from socket import *

from exabox.core.Error import ExacloudRuntimeError
from exabox.log.LogMgr import ebLogInit
from exabox.core.Context import exaBoxContext, set_gcontext, get_gcontext
from exabox.tools.AttributeWrapper import wrapStrBytesFunctions
from exabox.exatest.common.ebExacloudUtil import ebExacloudUtil
from exabox.exakms.ExaKmsSingleton import ExaKmsSingleton
from exabox.exakms.ExaKmsEntry import ExaKmsEntry, ExaKmsHostType, ExaKmsOperationType, ExaKmsKeyFormat
from exabox.network.osds.sshclient import SshClient, mExecuteLocal

_ROCE_DOWNLOAD_DEFAULT_MB = 4
_ROCE_DOWNLOAD_MAX_MB = 64
_ROCE_DOWNLOAD_READY_TIMEOUT = 60
_ROCE_DOWNLOAD_MIN_CHUNK_TIMEOUT = 180
_ROCE_DOWNLOAD_TIMEOUT_OVERHEAD_SECONDS = 30
_ROCE_DOWNLOAD_MIN_MB_PER_SECOND = 0.03

class MaxLevelFilter(logging.Filter):
    def __init__(self, level):
        self.level = level
    def filter(self, record):
        return record.levelno < self.level

class ebExasshLogger:

    def __init__(self, aLogLocation, aConsoleLog=True, aFileLog=False):
        self.__logger = None
        self.__logLocation = aLogLocation
        self.__consoleLog = aConsoleLog
        self.__fileLog = aFileLog
        self.__fileHandler = None

    def mGetLog(self, aConsoleLog=True, aFileLog=False):

        if not self.__logger:

            # Create exassh logger
            _logger = logging.getLogger("exassh")

            if len(_logger.handlers) == 0:

                _logger.propagate = False
                _logger.setLevel(logging.DEBUG)

                try:
                    os.makedirs(self.__logLocation)
                except OSError:
                    pass

                if self.__fileLog:

                    # Add file handler
                    _fileLog = os.path.join(self.__logLocation, "exassh.log")
                    _fh = logging.FileHandler(_fileLog)
                    _formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                    _fh.setFormatter(_formatter)
                    _logger.addHandler(_fh)
                    self.__fileHandler = _fh

                if self.__consoleLog:

                    _minLevel = logging.DEBUG
                    _lowerThanWarning = MaxLevelFilter(logging.WARNING)
                    _formatter = logging.Formatter('%(message)s')

                    # Add stdout handler
                    _sho = logging.StreamHandler(sys.stdout)
                    _sho.setFormatter(_formatter)
                    _sho.addFilter(_lowerThanWarning)
                    _sho.setLevel(_minLevel)
                    _logger.addHandler(_sho)

                    # Add stderr handler
                    _she = logging.StreamHandler(sys.stderr)
                    _she.setFormatter(_formatter)
                    _she.setLevel(max(_minLevel, logging.WARNING))
                    _logger.addHandler(_she)

            self.__logger = _logger

        return self.__logger

    def mAttachToParamiko(self):

        if not self.__fileHandler:
            self.mGetLog()

        if not self.__fileHandler:
            return

        _paramiko_logger = logging.getLogger("paramiko")

        if self.__fileHandler not in _paramiko_logger.handlers:
            _paramiko_logger.addHandler(self.__fileHandler)

        if _paramiko_logger.level > logging.DEBUG:
            _paramiko_logger.setLevel(logging.DEBUG)


class ExasshManager:

    def __init__(self, aClubox=None, aConsoleLog=True, aFileLog=False, aSilent=True, aDebug=False):

        self.__exacloudPath = os.getcwd()
        self.__exacloudPath = self.__exacloudPath[0: self.__exacloudPath.rfind("exacloud")+8]

        self.__clubox = None
        self.__mode = "default"
        self.__output = "default"
        self.__sshMicroseconds = 100
        self.__xmlPath = None
        self.__exakmsSingletion = None

        self.__exakmsType = "auto"
        self.__connParams = {}
        self.__requestedFqdn = None
        self.__sessionSsh = None
        self.__channel = None
        self.__silent = aSilent
        self.__connectedEntry = None
        self.__debug = aDebug
        self.__logger = ebExasshLogger(os.path.join(self.__exacloudPath, "log"), aConsoleLog, aFileLog)
        self.__sshclient = None
        self.mInitExacloud(aClubox)

        if not self.__silent and self.__debug:
            logging.getLogger("paramiko").setLevel(logging.DEBUG)

        if self.__debug and aFileLog:
            self.__logger.mAttachToParamiko()

    def mGetLog(self):
        return self.__logger.mGetLog()

    def mInitExacloud(self, aClubox=None):

        if aClubox is None:
            _util = ebExacloudUtil(aDeploy=True)
            self.mSetClubox(_util.mPrepareEnviroment())

        else:
            self.mSetClubox(aClubox)

            _exakmsSingletion = get_gcontext().mGetExaKmsSingleton()
            self.mSetExaKmsSingleton(_exakmsSingletion)

    def mGetExacloudPath(self):
        return self.__exacloudPath

    def mSetExacloudPath(self, aPath):
        self.__exacloudPath = aPath

    def mGetConnParams(self):
        return self.__connParams

    def mSetConnParams(self, aDict):
        self.__connParams = aDict
        self.__requestedFqdn = aDict.get("FQDN") if aDict else None

    def mGetRequestedFqdn(self):
        return self.__requestedFqdn

    def mGetExaKmsSingleton(self):

        if not self.__exakmsSingletion:
            self.__exakmsSingletion = ExaKmsSingleton()

        return self.__exakmsSingletion

    def mSetExaKmsSingleton(self, aValue):
        self.__exakmsSingletion = aValue

    def mGetXmlPath(self):
        return self.__xmlPath

    def mSetXmlPath(self, aXml):

        self.__xmlPath = os.path.abspath(aXml)
        _util = ebExacloudUtil(aDeploy=True)

        self.mGetClubox().mSetConfigPath(self.__xmlPath)
        self.mGetClubox().mParseXMLConfig(_util.mGetConfig())

    def mGetSshMicroseconds(self):
        return self.__sshMicroseconds

    def mSetSshMicroseconds(self, aMicroseconds):
        self.__sshMicroseconds = aMicroseconds

    def mGetMode(self):
        return self.__mode

    def mSetMode(self, aMode):
        self.__mode = aMode

    def mGetClubox(self):
        return self.__clubox

    def mSetClubox(self, aClubox):
        self.__clubox = aClubox

    def mGetSshClient(self):
        return self.__sshclient

    def mSetSshClient(self, aClient):
        self.__sshclient = aClient

    def mGetSessionSsh(self):
        return self.__sessionSsh

    def mSetSessionSsh(self, aSession):
        self.__sessionSsh = aSession

    def mGetChannel(self):
        return self.__channel

    def mSetChannel(self, aChannel):
        self.__channel = aChannel

    def mGetConnectedEntry(self):
        return self.__connectedEntry

    def mSetConnectedEntry(self, aEntry):
        self.__connectedEntry = aEntry

    def mGetOutput(self):
        return self.__output

    def mSetOutput(self, aOutputMode):
        self.__output = aOutputMode

    def mConnectMina(self, aCmd=None):

        _entries = self.mSearchExaKms()
        _entriesValid = []

        for _entry in _entries:

            _status = self.mGetHostStatus(_entry, aValidateEntry=True)
            if "invalid" not in _status:
                _entriesValid.append(_entry)

        if not _entriesValid:
            raise ValueError(f"Key not found for params {self.mGetConnParams()}")

        _entry = _entriesValid[0]

        # Prepare file for Mina testing
        _oedaPath = self.mGetClubox().mCheckConfigOption("oeda_dir")
        _uuid = str(uuid.uuid1())
        _tmpfile = f"/tmp/{_uuid}"
        _minafile = f"{_oedaPath}/debug_mina_{_uuid}.sh"

        with open(f"{self.__exacloudPath}/exabox/exatest/resources/debug_mina.sh", "r") as _f:
            _mina_content = _f.read()

        _java = shlex.quote(os.path.join(get_gcontext().mGetJavaHome(), "bin", "java"))

        _entry.mSaveToFile("/tmp", _tmpfile)

        if self.__debug:
            _mina_content = _mina_content.replace("{_debug}", "-vvv")
        else:
            _mina_content = _mina_content.replace("{_debug}", "")

        _mina_content = _mina_content.replace("{_java}", _java)
        _mina_content = _mina_content.replace("{_keyfile}", _tmpfile)
        _mina_content = _mina_content.replace("{_user}", _entry.mGetUser())
        _mina_content = _mina_content.replace("{_host}", _entry.mGetFQDN())

        if aCmd:
            _mina_content = _mina_content.replace("{_cmd}", aCmd)
        else:
            _mina_content = _mina_content.replace("{_cmd}", "")

        with open(_minafile, "w") as _f:
            _f.write(_mina_content)
            _f.write("\n")

        # Execute OEDA Mina
        os.chmod(_minafile, 0o700)
        _rc = sp.run(["/bin/bash", _minafile], cwd=_oedaPath, check=False).returncode

        if _rc == 0:
            self.mGetLog().info(f"Mina Connection to: {_entry.mGetFQDN()} closed.")
            os.remove(_minafile)
            os.remove(_tmpfile)

        else:
            self.mGetLog().error(f"Error on Mina to {_entry.mGetFQDN()} closed.")
            self.mGetLog().error(f"Please review file: {_minafile} and {_tmpfile}")

        return _rc

    def mConnect(self):

        _entries = self.mSearchExaKms()
        _entriesValid = []

        for _entry in _entries:

            _status = self.mGetHostStatus(_entry, aValidateEntry=True)
            if "invalid" not in _status:
                _entriesValid.append(_entry)

        if not _entriesValid:
            raise ValueError(f"Key not found for params {self.mGetConnParams()}")

        self.mPrepareChannel(_entriesValid[0])

    def mDisconnect(self):

        self.mCloseChannel()


    def mCalculatePingable(self, aExaKmsEntry):

        if self.mGetMode() == "default":
            return True

        else:

            _ping = True

            s = socket(AF_INET, SOCK_STREAM)
            s.settimeout(float(self.mGetSshMicroseconds())/1000)

            try:
                s.connect((aExaKmsEntry.mGetFQDN(), 22))
            except:
                _ping = False
            finally:
                s.close()

            return _ping

    def mInputInteractiveData(self, aStatus):

        fd = sys.stdin.fileno()

        oldterm = termios.tcgetattr(fd)
        newattr = termios.tcgetattr(fd)
        newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
        termios.tcsetattr(fd, termios.TCSANOW, newattr)

        oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

        while aStatus["run"]:

            try:
                rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
                if rlist:
                    c = sys.stdin.read(1024)

                    if self.mGetChannel().send_ready():
                        self.mGetChannel().sendall(c)
                    else:
                        aStatus['run'] = False

            except IOError:
                pass

        termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
        fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)

    def mOutputInteractiveData(self, aStatus):
        while aStatus["run"]:

            if not self.mGetChannel().get_transport().is_alive():
                aStatus['run'] = False

            else:
                select.select([self.mGetChannel()], [], [])
                if self.mGetChannel().recv_ready():
                    _consoleData = self.mGetChannel().recv(1024).decode('utf8', 'ignore')

                    if len(_consoleData) != 0:
                        try:
                            sys.stdout.write(_consoleData)
                        except:
                            sys.stderr.write(_consoleData)
                            sys.stderr.flush()

                        sys.stdout.flush()
                else:
                    aStatus['run'] = False

    def mInteractiveConsole(self, aOutputCallback, aInputCallback):

        def mTempSigint(x,y):
            _sent = False
            while not _sent:
                if self.mGetChannel().send_ready():
                    self.mGetChannel().sendall(chr(3))
                    _sent = True

        def mResizeWindow(x,y):
            _r = fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, b'0000')
            _h, _w = struct.unpack('HH', _r)
            self.mGetChannel().resize_pty(width=_w, height=_h)

        if self.mGetChannel() is not None:

            #Prepare the socket thread information
            _status = {"run": True}

            mResizeWindow(None, None)

            thread = Thread(target=aOutputCallback, args=[_status])
            thread2 = Thread(target=aInputCallback, args=[_status])

            thread.start()
            thread2.start()

            #Process Control+C signal to request dispatch to subshell
            originalSigintHandler = signal.getsignal(signal.SIGINT)
            signal.signal(signal.SIGINT, mTempSigint)
            originalSigWinChHandler = signal.getsignal(signal.SIGWINCH)
            signal.signal(signal.SIGWINCH, mResizeWindow)

            while _status['run']:
                time.sleep(0.03)

            signal.signal(signal.SIGINT, originalSigintHandler)
            signal.signal(signal.SIGWINCH, originalSigWinChHandler)

            #Join Threads
            thread.join()
            thread2.join()

            self.mGetLog().info("Connection to {0} closed.".format(self.__host))

    def mAddRSAToKeys(self, _data):

        if 'BEGIN PRIVATE KEY' in _data:
            _data = _data.replace('BEGIN PRIVATE KEY', 'BEGIN RSA PRIVATE KEY')
            _data = _data.replace('END PRIVATE KEY', 'END RSA PRIVATE KEY')

        return _data

    def mShellQuote(self, aValue):
        return shlex.quote(str(aValue))

    def mAddPreferredPubkeys(self, aExaKmsEntry):

        if aExaKmsEntry.mGetHostType() == ExaKmsHostType.SWITCH:

            paramiko.transport.Transport.preferred_pubkeys = (
                "ssh-ed25519",
                "ecdsa-sha2-nistp256",
                "ecdsa-sha2-nistp384",
                "ecdsa-sha2-nistp521",
                "ssh-rsa",
                "rsa-sha2-512",
                "rsa-sha2-256",
                "ssh-dss"
            )

        else:

            paramiko.transport.Transport.preferred_pubkeys = (
                "ssh-ed25519",
                "ecdsa-sha2-nistp256",
                "ecdsa-sha2-nistp384",
                "ecdsa-sha2-nistp521",
                "rsa-sha2-512",
                "rsa-sha2-256",
                "ssh-rsa",
                "ssh-dss"
            )


    def mHasRoceFqdn(self):
        _entry = self.mGetConnectedEntry()
        _candidateFqdns = [
            self.mGetRequestedFqdn(),
            self.mGetConnParams().get("FQDN"),
            getattr(self, "_ExasshManager__host", None)
        ]

        if _entry:
            try:
                _candidateFqdns.append(_entry.mGetFQDN())
            except Exception:
                pass

        for _fqdn in _candidateFqdns:
            if not _fqdn:
                continue

            # RoCE switch detection is used only as an SFTP failure fallback.
            # Keep it tied to the user-visible hostname instead of requiring
            # strict FQDN validation, since short names like scaqan17sw-rocea0
            # are valid exassh input and still identify RoCE switches.
            if "roce" in str(_fqdn).lower():
                return True

        return False

    def mGetRoceDownloadChunkBytes(self):
        _mb = _ROCE_DOWNLOAD_DEFAULT_MB
        try:
            _configured = get_gcontext().mCheckConfigOption(
                "exassh_roce_default_mbrate",
                str(_ROCE_DOWNLOAD_DEFAULT_MB)
            )
            _mb = int(str(_configured).strip())
        except Exception:
            _mb = _ROCE_DOWNLOAD_DEFAULT_MB

        if _mb <= 0:
            _mb = _ROCE_DOWNLOAD_DEFAULT_MB

        if _mb > _ROCE_DOWNLOAD_MAX_MB:
            self.mGetLog().info(
                f"Configured exassh_roce_default_mbrate={_mb} MB exceeds "
                f"maximum; using {_ROCE_DOWNLOAD_MAX_MB} MB"
            )
            _mb = _ROCE_DOWNLOAD_MAX_MB

        return _mb * 1024 * 1024

    def mGetRoceDownloadChunkTimeout(self):
        # Scale timeout with the configured chunk size while preserving the
        # 4 MB behavior as the minimum. The rate is intentionally
        # conservative because RoCE downloads run through an interactive shell.
        _chunkMb = float(self.mGetRoceDownloadChunkBytes()) / (1024 * 1024)
        _timeout = (
            _ROCE_DOWNLOAD_TIMEOUT_OVERHEAD_SECONDS +
            int(math.ceil(_chunkMb / _ROCE_DOWNLOAD_MIN_MB_PER_SECOND))
        )

        return max(_ROCE_DOWNLOAD_MIN_CHUNK_TIMEOUT, _timeout)

    def mPrepareChannel(self, aExaKmsEntry):

        self.__host = aExaKmsEntry.mGetFQDN()
        self.mSetConnectedEntry(aExaKmsEntry)

        if self.__debug:
            self.mGetLog().info(f"Using public key: {aExaKmsEntry.mGetPublicKey().strip()}")

        _keydat = aExaKmsEntry.mGetPrivateKey()
        self.mAddPreferredPubkeys(aExaKmsEntry)

        if "ECDSA" in aExaKmsEntry.mGetVersion():
            _key = paramiko.ECDSAKey.from_private_key(StringIO(_keydat))

        else:
            _keydat = self.mAddRSAToKeys(_keydat)
            _key = paramiko.RSAKey.from_private_key(StringIO(_keydat))

        _retries = 3
        while _retries > 0:
            try:
                self.mSetSshClient(SshClient(self.__host))
                self.mSetSessionSsh(self.mGetSshClient().mCreateSshClient())
                self.mGetSessionSsh().connect(self.__host, 22, aExaKmsEntry.mGetUser(), pkey=_key)
                break
            except paramiko.ssh_exception.SSHException as exp:
                if "not found in known_hosts" in str(exp):
                    SshClient(self.__host).mAddToKnownHost()
                else:
                    _retries -= 1
                    if _retries <= 0:
                        raise
            except Exception as e:
                _retries -= 1
                if _retries <= 0:
                    raise

        _banner = self.mGetSessionSsh()._transport.get_banner()
        if _banner is not None and not self.__silent:
                self.mGetLog().info(_banner)

        self.mGetSessionSsh()._transport.set_keepalive(1)

        _channel = self.mGetSessionSsh()._transport.open_session()
        _channel.get_pty()
        _channel.invoke_shell()
        _channel.settimeout(1)

        self.mSetChannel(_channel)


    def mCloseChannel(self):

        if self.mGetChannel() is not None:
            self.mGetChannel().close()
            self.mSetChannel(None)

        if self.mGetSessionSsh() is not None:
            self.mGetSessionSsh().close()
            self.mSetSessionSsh(None)

        if self.mGetSshClient() is not None:
            self.mGetSshClient().mCleanUp()
            self.mSetSshClient(None)

    def mExecuteSshCommand(self, aCommand):

        rc = -777
        out = ""
        err = ""

        try:

            channel = self.mGetChannel().get_transport().open_session()
            channel.exec_command(command=aCommand)

            #Although we are attempting to read both stdout and stderr streams from the same paramiko channel, there is a known limitation in
            #paramiko where it is unable to read/send any data if both streams are producing output. Using get_pty() for a pseudo terminal doesn't help.
            #Also combining stdout and stderr stream completely messes up the output data.
            outchannelfile = channel.makefile("r")
            errchannelfile = channel.makefile_stderr("r")
            while not channel.exit_status_ready():
                select.select([channel], [], [])
                if channel.recv_stderr_ready():
                    err += errchannelfile.read().decode("utf-8")
                if channel.recv_ready():
                    out += outchannelfile.read().decode("utf-8", errors='ignore')

            #Weird behavior of paramiko channel. The channel exit status is set even if the consumer has not read any data from the stdout/stderr streams.
            if channel.recv_stderr_ready():
                err += errchannelfile.read().decode("utf-8")
            if channel.recv_ready():
                out += outchannelfile.read().decode("utf-8", errors='ignore')
            if channel.exit_status_ready():
                rc = channel.recv_exit_status()

        except Exception as e:
            self.mGetLog().error(e)
            self.mGetLog().error(traceback.format_exc())

        return rc, out, err

    def mStartCli(self):

        try:
            self.mInteractiveConsole(self.mOutputInteractiveData, self.mInputInteractiveData)
            return 0

        except Exception as e:
            self.mGetLog().error(e)
            self.mGetLog().error(traceback.format_exc())
            return 1

    def mDrainInteractiveChannel(self):
        # Clear prompts, command echoes, and banners left on the interactive
        # channel before sending a marker-delimited command.
        try:
            while self.mGetChannel().recv_ready():
                self.mGetChannel().recv(4096)
                time.sleep(0.05)
        except Exception as e:
            self.mGetLog().error(f"Failed to drain interactive SSH channel: {e}")
            self.mGetLog().error(traceback.format_exc())
            raise

    def mReadInteractiveUntil(self, aEndMarker, aTimeout=60):
        _end = time.time() + aTimeout
        _data = ""

        while time.time() < _end:
            if self.mGetChannel().recv_ready():
                _data += self.mGetChannel().recv(4096).decode("utf-8", errors="ignore")
                if aEndMarker in _data:
                    return _data
            else:
                time.sleep(0.2)

        raise ExacloudRuntimeError(aErrorMsg=f"Timed out waiting for marker: {aEndMarker}")

    def mExecuteGuestShellMarkedCommand(self, aCommand, aTimeout):
        # Keep the interactive transfer protocol simple: write unique begin/end
        # markers around the command output and parse the bytes between them.
        _token = uuid.uuid4().hex
        _beginPrefix = "__EXASSH_ROCE_BEGIN_"
        _endPrefix = "__EXASSH_ROCE_END_"
        _markerSuffix = f"{_token}__"
        _begin = f"{_beginPrefix}{_markerSuffix}"
        _end = f"{_endPrefix}{_markerSuffix}"

        # Split the marker into shell variables so the echoed command does not
        # contain the complete marker.  Then simple substring parsing only sees
        # markers that were printed by command execution.
        _cmd = (
            f"_exassh_b={self.mShellQuote(_beginPrefix)}; "
            f"_exassh_e={self.mShellQuote(_endPrefix)}; "
            f"_exassh_s={self.mShellQuote(_markerSuffix)}; "
            f"printf '\n%s%s\n' \"$_exassh_b\" \"$_exassh_s\"; "
            f"{aCommand}; "
            f"_rc=$?; "
            f"printf '\n%s%s:%s\n' \"$_exassh_e\" \"$_exassh_s\" \"$_rc\""
        )

        self.mDrainInteractiveChannel()
        self.mGetChannel().sendall(_cmd + "\n")
        _output = self.mReadInteractiveUntil(_end, aTimeout)

        try:
            _payload = _output.split(_begin, 1)[1].split(_end, 1)[0]
            _rcText = _output.split(_end, 1)[1].splitlines()[0].lstrip(":").strip()
        except Exception:
            raise ExacloudRuntimeError(
                aErrorMsg=f"Unable to parse guestshell command output: {_output[-200:]}"
            )

        if _rcText != "0":
            raise ExacloudRuntimeError(
                aErrorMsg=f"Guestshell command failed with rc={_rcText}: {aCommand}"
            )

        return _payload

    def mEnterRoceGuestShell(self):
        # RoCE switches land in a restricted shell; guestshell is required
        # before Linux log paths and tools such as tail/head/gzip are available.
        self.mDrainInteractiveChannel()
        self.mGetLog().info("Entering guestshell")
        self.mGetChannel().sendall("run guestshell\n")
        time.sleep(5)
        self.mDrainInteractiveChannel()

    def mGetRoceGuestShellFileSize(self, aRemoteFile):
        # Snapshot the readable regular-file size once so downloads are bounded
        # even if a live log grows while the transfer is in progress.
        _remote = self.mShellQuote(aRemoteFile)
        _cmd = (
            f"if test -r {_remote} && test -f {_remote}; then "
            f"wc -c < {_remote}; "
            f"elif test -d {_remote}; then echo DIRECTORY; "
            f"else echo UNREADABLE; fi"
        )
        _output = self.mExecuteGuestShellMarkedCommand(_cmd, _ROCE_DOWNLOAD_READY_TIMEOUT)
        _value = ""

        # Restricted-shell prompts can arrive in the same PTY read as command
        # output.  Use the first meaningful status or numeric line and ignore
        # prompt-only noise such as ">" after the marker payload.
        for _line in _output.strip().splitlines():
            _line = _line.strip()
            if not _line or _line in [">", "$", "#"]:
                continue
            if _line in ["DIRECTORY", "UNREADABLE"] or _line.isdigit():
                _value = _line
                break

        if _value == "DIRECTORY":
            raise ExacloudRuntimeError(aErrorMsg="RoCE guestshell download supports files only")
        if _value == "UNREADABLE":
            raise ExacloudRuntimeError(aErrorMsg=f"Remote file is missing or unreadable: {aRemoteFile}")

        try:
            return int(_value)
        except ValueError:
            raise ExacloudRuntimeError(aErrorMsg=f"Unable to determine remote file size from guestshell output: {_output.strip()}")

    def mDownloadRoceGuestShellFile(self, aRemoteFile, aLocalFile):
        _rc = 0
        _tempLocal = None

        try:
            _baseLocal = os.path.abspath(os.path.expanduser(aLocalFile))
            _parentDir = os.path.dirname(_baseLocal)
            if _parentDir:
                os.makedirs(_parentDir, exist_ok=True)

            self.mEnterRoceGuestShell()

            _remoteSize = self.mGetRoceGuestShellFileSize(aRemoteFile)
            _chunkSize = self.mGetRoceDownloadChunkBytes()
            _chunkTimeout = self.mGetRoceDownloadChunkTimeout()
            _remote = self.mShellQuote(aRemoteFile)
            self.mGetLog().info(
                f"RoCE guestshell download size={_remoteSize} bytes, chunk_size={_chunkSize} bytes, chunk_timeout={_chunkTimeout} seconds"
            )
            _offset = 1

            self.mGetLog().info(
                f"Downloading RoCE switch file through guestshell in {_chunkSize} byte chunks\n"
            )

            # Write to a sibling temporary file first so a failed chunk does not
            # leave a truncated file at the user-requested destination.
            with tempfile.NamedTemporaryFile(
                "wb",
                dir=_parentDir if _parentDir else ".",
                prefix=os.path.basename(_baseLocal) + ".",
                suffix=".tmp",
                delete=False
            ) as _localFile:
                _tempLocal = _localFile.name
                while _offset <= _remoteSize:
                    _size = min(_chunkSize, _remoteSize - _offset + 1)
                    self.mGetLog().info(
                        f"Downloading RoCE chunk offset={_offset} size={_size}"
                    )
                    # Stream a precise byte range, compress it to keep terminal
                    # traffic smaller, and base64 encode it to survive the PTY.
                    _cmd = (
                        f"tail {_remote} -c +{_offset} | "
                        f"head -c {_size} | "
                        f"gzip - -cf | base64"
                    )
                    _payload = self.mExecuteGuestShellMarkedCommand(
                        _cmd,
                        _chunkTimeout
                    )
                    _payload = "".join(_payload.strip().splitlines())
                    _localFile.write(gzip.decompress(base64.b64decode(_payload, validate=True)))
                    _offset += _size

            os.replace(_tempLocal, _baseLocal)
            _tempLocal = None

            self.mGetLog().info(f"{aRemoteFile}  -> {_baseLocal}")
            self.mGetLog().info("")
            self.mGetLog().info("File Transfer complete")

        except Exception as e:
            if _tempLocal and os.path.exists(_tempLocal):
                try:
                    os.remove(_tempLocal)
                except Exception as cleanupError:
                    self.mGetLog().error(
                        f"Failed to remove temporary download file {_tempLocal}: {cleanupError}"
                    )
            self.mGetLog().error(e)
            self.mGetLog().error(traceback.format_exc())
            _rc = 1

        return _rc

    def mDownload(self, aRemoteFile, aLocalFolder):

        _rc = 0
        _sftp = None
        _roceFallback = False

        try:

            self.mGetLog().info("Downloading\n")
            _sftp = paramiko.SFTPClient.from_transport(self.mGetChannel().get_transport())

            _baseLocal = os.path.expanduser(aLocalFolder)
            _baseLocal = os.path.abspath(_baseLocal)
            _baseRemote = aRemoteFile

            _remoteList = [aRemoteFile]

            while _remoteList:

                _remoteFile = _remoteList.pop(0)

                _localFile = _remoteFile.replace(_baseRemote, "").strip("/")
                _localFile = os.path.join(_baseLocal, _localFile).rstrip("/")

                try:

                    # Check if is folder
                    _newFiles = _sftp.listdir(_remoteFile)

                    # Append new files for get them
                    for _newFile in _newFiles:
                        _remoteList.append(os.path.join(_remoteFile, _newFile))

                    # Create local folder
                    os.makedirs(_localFile, exist_ok=True)
                    self.mGetLog().info(f"{_remoteFile}  -> {_localFile}")

                except IOError:

                    _sftp.get(_remoteFile, _localFile)
                    self.mGetLog().info(f"{_remoteFile}  -> {_localFile}")

            self.mGetLog().info("")
            self.mGetLog().info("File Transfer complete")

        except Exception as e:
            if self.mHasRoceFqdn():
                self.mGetLog().info(
                    "SFTP download failed; assuming RoCE switch from FQDN "
                    "and retrying through guestshell"
                )
                self.mGetLog().info(f"SFTP failure before RoCE guestshell retry: {e}")
                _roceFallback = True

            else:
                self.mGetLog().error(e)
                self.mGetLog().error(traceback.format_exc())
                _rc = 1

        finally:
            if _sftp:
                try:
                    _sftp.close()
                except Exception as closeError:
                    self.mGetLog().error(f"Failed to close SFTP download session: {closeError}")

        if _roceFallback:
            return self.mDownloadRoceGuestShellFile(aRemoteFile, aLocalFolder)

        return _rc

    def mUpload(self, aLocalFile, aRemoteFolder):

        _rc = 0

        try:

            _local = os.path.expanduser(aLocalFile)
            _local = os.path.abspath(_local)

            self.mGetLog().info("Uploading\n")
            _sftp = paramiko.SFTPClient.from_transport(self.mGetChannel().get_transport())

            if os.path.isdir(_local):

                try:
                    _sftp.mkdir(aRemoteFolder)
                except IOError as e:
                    pass

                for (_root, _dirs, _files) in os.walk(_local, topdown=True):

                    _remoteroot = _root.replace(_local, "").strip("/")

                    for _dir in _dirs:

                        _localdir = os.path.join(_root, _dir)
                        _remotedir = os.path.join(aRemoteFolder, _remoteroot, _dir)

                        try:
                            _sftp.mkdir(_remotedir)
                            self.mGetLog().info(f"{_localdir} ----> {_remotedir}")
                        except IOError as e:
                            pass

                    for _file in _files:

                        _localfile = os.path.join(_root, _file)
                        _remoteFile = os.path.join(aRemoteFolder, _remoteroot, _file)

                        _sftp.put(_localfile, _remoteFile)
                        self.mGetLog().info(f"{_localfile} ----> {_remoteFile}")

            else:
                _sftp.put(_local, aRemoteFolder)
                self.mGetLog().info(f"{_local} ----> {aRemoteFolder}")

            self.mGetLog().info("")
            self.mGetLog().info("File Transfer complete")

            _sftp.close()

        except Exception as e:
            print(traceback.format_exc())
            self.mGetLog().error(e)
            self.mGetLog().error(traceback.format_exc())
            _rc = 2
        return _rc


    def mRemotelyExecute(self, aLocalFile, aScriptArgs):
        _rc, _stdout, _stderr = 1, "", ""

        try:
            # Set directories
            _, _localFileExtension = os.path.splitext(aLocalFile)
            _tmpFile = os.path.abspath(f"/tmp/{uuid.uuid4()}_tmp_remotefile{_localFileExtension}")
            # Upload file
            _rc = self.mUpload(aLocalFile, _tmpFile)
            # Set executable permissions
            _rc, _stdout, _stderr = self.mExecuteSshCommand(f"/bin/chmod u+x {_tmpFile}")
            # Run newly uploaded file
            _cmd = f"{_tmpFile}" + "".join([f" {arg}" for arg in aScriptArgs])
            self.mGetLog().info("Executing file")
            _rc, _stdout, _stderr = self.mExecuteSshCommand(_cmd)
            if _rc != 0:
                self.mGetLog().info(f"Execution failed with codes: {_rc}, {_stdout}, {_stderr}")
                return _rc
            # Delete tmp file
            self.mGetLog().info(f"Execution returned codes: {_rc}, {_stdout}, {_stderr}")
            self.mExecuteSshCommand(f"/bin/rm {_tmpFile}")
        except Exception as e:
            self.mGetLog().error(traceback.format_exc())

        self.mGetLog().info("Remote execution successful.")
        return _rc


    def mSearchExaKms(self):

        _ids = {}
        _idFiles = "config/exassh_ids.json"

        if os.path.exists(_idFiles):
            with open("config/exassh_ids.json", "r") as _f:
                _ids = json.loads(_f.read())

        if "FQDN" in self.mGetConnParams():

            _host = str(self.mGetConnParams()['FQDN'])
            for _name, _id in _ids.items():
                if _host == str(_id) or _host == _name.split(".")[0]:
                    _host = _name
                    break

            self.mGetConnParams()["FQDN"] = _host

        _exakms = self.mGetExaKmsSingleton().mGetExaKms()
        _entries = _exakms.mSearchExaKmsEntries(self.mGetConnParams())

        if "FQDN" in self.mGetConnParams():
            for _entry in _entries:
                if self.mGetConnParams()["FQDN"] not in _entry.mGetFQDN():
                    _entry.mSetFQDN(self.mGetConnParams()["FQDN"])

        return _entries

    def mGetHostStatus(self, aKmsEntry, aValidateEntry=False):

        if not aKmsEntry:
            self.mGetLog().info("KmsEntry not found")
            return 1

        _entry = aKmsEntry

        try:
            _dict = _entry.mToJson()

            _dict['pingable'] = self.mCalculatePingable(_entry)
            _dict['publicKey'] = _entry.mGetPublicKey()

        except:

            _dict = _entry.mToJsonMinimal()
            _dict['invalid'] = True

            if aValidateEntry:
                return _dict

        # Try ssh
        _sshable = True

        if self.mGetMode() == "hard":

            _sshable = False
            try:
                self.mPrepareChannel(_entry)
                _sshable = True

            except:
                _sshable = False

            finally:
                self.mCloseChannel()

        _dict['sshable'] = _sshable

        if "privateKey" in _dict:
            del _dict['privateKey']

        return _dict

    def mPrintAll(self):

        self.mGetLog().info('*** EXASSH HOSTS ***')

        _exakms = self.mGetExaKmsSingleton().mGetExaKms()
        _entries = _exakms.mSearchExaKmsEntries(self.mGetConnParams())

        _xmlEntries = []
        _xmlEntriesShort = []
        if self.mGetXmlPath():
            _xmlEntries = list(self.mGetClubox().mGetExaKmsHostMap().keys())
            _xmlEntriesShort = list(map(lambda x: x.split(".")[0], _xmlEntries))

        # Calculate entries
        _hostEntries = []
        for _entry in _entries:

            if _xmlEntries and _entry.mGetFQDN().split(".")[0] not in _xmlEntriesShort:
                continue

            _fqdn = _entry.mGetFQDN()

            if _xmlEntries:
                _idx = _xmlEntriesShort.index(_entry.mGetFQDN().split(".")[0])
                _fqdn = _xmlEntries[_idx]

            _minimal = {}
            _minimal['FQDN'] = _fqdn
            _minimal['user'] = _entry.mGetUser()
            _minimal['host_type'] = _entry.mGetHostType().name.lower()

            if self.mGetOutput() == "json":
                _minimal['public_key'] = _entry.mGetPublicKey()

            _hostEntries.append(_minimal)

        _hostEntries.sort(key=lambda x: f"{x['host_type']}/{x['FQDN']}/{x['user']}")

        # Calculate formated values
        _hostValues = {}
        _hostIds = {}
        _lastId = 0

        for _entry in _hostEntries:

            if _entry['FQDN'] in _hostIds:
                _id = _hostIds[_entry['FQDN']]
            else:
                _lastId += 1
                _hostIds[_entry['FQDN']] = _lastId
                _hostValues[_lastId] = []
                _id = _lastId

            _entry['id'] = _id
            _hostValues[_id].append(_entry)

        # Print formatter
        for _hostId, _entries in _hostValues.items():

            if self.mGetOutput() == "delimiter":

                _str = ""

                for _entry in _entries:

                    _str += str(_entry["id"])
                    _str += "|"

                    del _entry['id']

                    _str += '|'.join(list(map(lambda x: str(x), _entry.values())))
                    _str += "\n"

                self.mGetLog().info(_str)

            elif self.mGetOutput() == "json":

                for _entry in _entries:
                    self.mGetLog().info(json.dumps(_entry, sort_keys=True, indent=4))

            else:

                _users = list(set(list(map(lambda x: x['user'], _entries))))
                _first = _entries[0]
                self.mGetLog().info(f"{_hostId}) {_first['FQDN'].split('.')[0]} {_users}")

        # Save exassh ids
        with open("config/exassh_ids.json", "w") as _f:
            _f.write(json.dumps(_hostIds))


# end of file
