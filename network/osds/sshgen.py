"""
 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    SshGen - Basic functionality for Ssh Connection management

FUNCTION:
    Provide basic/core API for managing ssh connection to remote Node

NOTE:
    None

History:
    jesandov    11/03/2025 - Bug#38606181: Fix UT
    jesandov    10/27/2025 - Bug#37073667: Force key only on domus
    jesandov    08/19/2025 - Bug#38195112: Add a fallback mechanism in switches connection between ssh-rsa and rsa-sha2-512
    aypaul      07/18/2025 - Bug#38126347 Fetch paramiko channel exit status only when available.
    hgaldame    06/05/2025 - 38036553 - exacc gen 2| cps-sw patching | cpssw upgrade failed 
                             at runcpsremoteecrestart 
    abflores    03/14/2025 - Bug 37693925: ADD SSH COMMAND EXECUTION TIME IN TRC FILES
    aararora    11/27/2024 - Bug 37067118: Use cellcli drop command for performing secure erase.
    gparada     11/26/2026 - 37260301 mConnect to use provided user (not ecra)
    emekala     10/29/2024 - ER 37226701 - Exacloud mExecute api with aTimeout arg should 
                             return exit code other than 1 when timeout reached
    hgaldame    08/11/2024 - 37149105 - oci/exacc fedramp: exacloud to use ecdsa ssh key for 
                             connect cps on oci/exacc/fedramp/fips environment 
    joysjose    16/07/2024 - ER 36618415 Avoid looping in mExecuteCmdsAuthInteractive function.
    aypaul      23/04/2024 - ER#36511790 Support for non english language code in ssh commands.
    aararora    24/11/2023 - Bug 36042360 - Do not send 'y\n' for a sshkey addition request on ROCE switch
    aypaul      16/11/2023 - Enh#35783067 interactive ilom host login support.
    ririgoye    25/09/2023 - Bug 35752629 - BUG SEEN IN EXACSDBOPS-5276 WHERE 
                             THE KEYS FOR ROOT USER WEREN'T CACHED.
    akkar       23/06/2023 - Bug 35395223: Add check in iptables for context
    aypaul      03/07/2023 - Enh#35128164, Support for ilom shell SSH execution.
    pkandhas    12/06/2022 - Trace of command before executing
    mirivier    08/21/2014 - Create file
    mirivier    10/01/2015 - RC5a_100115 + BadHostKey FIX
    hcheon      07/03/2017 - Improve speed and stability of mExecuteCmdAsync
    hgaldame    10/12/2017 - Add Support for Fetch key in mConnect
    gsundara    11/30/2018 - ER 28864094 (KMS+CASPER)
    oespinos    02/14/2019 - ER 29181096 Dump more info on Authentication errors
    araghave    03/26/2019 - 28584487 modified from ebLogVerbose to ebLogDebug 
                             to avoid frequent logging of sshgen-init message.
    dekuckre    04/11/2019 - Add support to execute cmds as sudo/non-sudo
    dekuckre    08/29/2019 - 30085688: Allow cmds to be executed as sudo when
                             opc is enabled (root disabled).
    hcheon      09/09/2019 - 30281185 ignore known_hosts file
    dekuckre    03/09/2020 - 30769480: Ensure sshkey connection before attempting
                             user-password based connection.
    ndesanto    06/02/2020 - Added mIsConnectable method
    gsundara    05/26/2020 - ER 31242318 
    jlombera    01/12/2021 - Bug 32295581: add method exaBoxNode.mWritFile()
    jesandov    12/05/2021 - Bug 32746913: Integrate ExaKms
    joserran    22/07/2021 - Enh 33146520: Reducing logging level for conn and cp
    jfsaldan    28/04/2022 - Bug 34088059 - Don't check for iptables in non domU nodes
    jesandov    03/31/2023 - 35141247 - Add SSH Connection Pool
    scoral      03/21/2023 - Enh 34734317: Implemented mGetFileInfo
"""

from six.moves import getoutput
import paramiko
import socket
import sys
import os
import subprocess
from   subprocess import PIPE
import logging
import uuid
import errno
import threading
import time
import base64
import json
import io
import select
import re
import math
import tempfile
import functools
import glob

from exabox.tools.AttributeWrapper import wrapStrBytesFunctions
from exabox.core.Context import get_gcontext
from exabox.exakms.ExaKmsEntry import ExaKmsHostType

from exabox.log.LogMgr import (ebLogError, ebLogDebug, ebLogInfo,
                                ebLogWarn, ebLogVerbose, ebLogTrace,
                                ebLogDeleteLoggerDestination,
                                ebLogAddDestinationToLoggers,
                                ebGetDefaultLoggerName, ebFormattersEnum)
from exabox.core.Error import ExacloudRuntimeError
from exabox.recordreplay.record_replay import ebRecordReplay 

try:
    from subprocess import DEVNULL # Python 3X
except ImportError:
    DEVNULL = open(os.devnull, 'wb')


sc_initialized  = 0
sc_influx       = 1
sc_connected    = 1 << 1
sc_disconnected = 1 << 2

def retry_decorator(func):
    """
    This decorator receive one function inside sshconn class as first argument
    After the function is passing, the wrapper is going to execute the mGenericRetry.
    mGenericRetry inside implements a loop if the connection of ssh fails and automatically retry
    """
    @functools.wraps(func)
    def wrapper(*func_args, **func_kwargs):
        return func_args[0].mGenericRetry(func, func_args, func_kwargs)
    return wrapper

def diag_decorator(func):
    """
    This decorator receive one function inside sshconn class as first argument
    After the function is passing, the wrapper is going to execute the mGenerateSshDiag.
    mGenerateSshDiag inside implements the creation of debug file
    """
    @functools.wraps(func)
    def wrapper(*func_args, **func_kwargs):
        return func_args[0].mGenerateSshDiag(func, func_args, func_kwargs)
    return wrapper

def mDecorateConnectforHaltSRGFile(func):
    def wrapper_mDecorateConnectforHaltSRGFile(self, *args, **kwargs):
        try:
            func(self, *args, **kwargs)
        except ExacloudRuntimeError as ere:
            self.mCreateHaltSRGTestsFile()
            raise
        except paramiko.AuthenticationException as ae:
            self.mCreateHaltSRGTestsFile()
            raise
        except paramiko.BadHostKeyException as bhke:
            self.mCreateHaltSRGTestsFile()
            raise
        except paramiko.ssh_exception.SSHException as sshe:
            self.mCreateHaltSRGTestsFile()
            raise
        except Exception as e:
            self.mCreateHaltSRGTestsFile()
            raise
    return wrapper_mDecorateConnectforHaltSRGFile

class interactiveSSHconnection(object):

    def __init__(self, aSSHClient, aDefaultPrompt):
        self.__interactive_shell = aSSHClient.invoke_shell()
        self.__default_prompt = aDefaultPrompt
        self.__current_prompt = aDefaultPrompt
        self.__data = ""
        self.__current_command_offset = 0
        self.__stop_reading = threading.Event()
        _thread = threading.Thread(target=self.mReadData, args=(self.__stop_reading,))
        _thread.daemon = True
        _thread.start()
        self.mGetData(self.__default_prompt)

    def __del__(self):
        self.mCloseInteractiveShell()

    def mGetCurrentPrompt(self):
        return self.__current_prompt

    def mCloseInteractiveShell(self):
        self.__stop_reading.set()
        if self.__interactive_shell:
            self.__interactive_shell.close()
            self.__interactive_shell = None

    def mGetData(self, aPromptToLookFor, aTimeout=50):
        _prompt_found = False
        _output = ""
        _timeout = aTimeout
        if _timeout is None:
            _timeout = 50
            ebLogTrace("Using a default timeout for 50 seconds.")
        _prompt_to_search_for = aPromptToLookFor
        _length_offset = len(_prompt_to_search_for) + 3 #incoming data ends as \r\n\n over the network.
        _length_offset = (_length_offset * -1)
        ebLogTrace(f"Prompt to check for: {_prompt_to_search_for}")
        while not _prompt_found:
            _prompt_check = self.__data[_length_offset:].strip()
            ebLogTrace(f"Prompt check buffer: {_prompt_check}")
            if _prompt_to_search_for in _prompt_check:
                _prompt_found = True
            time.sleep(1)
            if not _prompt_found:
                pass
            _timeout = _timeout - 1
            if not _timeout:
                ebLogInfo(f"Timeout while waiting for prompt/command execution: Current prompt: {_prompt_to_search_for}")
                break

        ebLogTrace(f"Complete data: {self.__data}")
        self.__data = self.__data[self.__current_command_offset:]
        if _prompt_to_search_for in self.__data[_length_offset:].strip():
            self.__data = self.__data[:len(self.__data)+_length_offset+1]
            self.__current_prompt = _prompt_to_search_for
        _output = self.__data
        self.__data = ''
        self.__current_command_offset = 0
        return _output

    def mExecuteCommand(self, aCommand, aPrompt, aTimeout):
        _command_to_execute = aCommand
        if self.__interactive_shell:
            self.__interactive_shell.send(_command_to_execute + "\n")
            self.__current_command_offset = len(_command_to_execute)
            return self.mGetData(aPrompt, aTimeout)
        else:
            raise ExacloudRuntimeError(0x0801, 0xA, "Interactive SSH shell is not yet initialised.")

    def mReadData(self, aStopEvent):
        _stop_event = aStopEvent
        while not _stop_event.is_set():
            if self.__interactive_shell is not None and self.__interactive_shell.recv_ready():
                _current_data = self.__interactive_shell.recv(1024)
                while self.__interactive_shell.recv_ready():
                    _current_data += self.__interactive_shell.recv(1024)
                self.__data += _current_data.decode("utf-8")

class sshconn(object):

    def __init__(self, aHost, aOptions):
        
        self.__client  = None
        self.__options = aOptions
        self.__user = None
        self.__pwd  = None
        self.__exakmsEntry  = None
        self.__exakmsEntriesList = []
        self.__port    = 22
        self.__state   = sc_initialized
        self.__chan    = None
        self.__sftp    = None
        self.xferdone  = False
        self.__exit_status = 0
        self.__transport = None
        self.__compress_mode = False
        self.__channel = None
        self.__debug   = False
        self.__sudo    = None
        self.__console_raw_output = ""

        if aOptions is not None:
            self.__debug   = aOptions.debug

        if get_gcontext().mCheckConfigOption('enable_kvm') == 'True':
            self.__kvm_enabled = True
        else:
            self.__kvm_enabled = False

        self.__max_retries = get_gcontext().mCheckConfigOption('ssh_connect_max_retries')
        if self.__max_retries is None:
            self.__max_retries = 10
        else:
            self.__max_retries = int(self.__max_retries)

        if aHost:
            self.__host = socket.getfqdn(aHost)
            if len(self.__host.split('.')) == 1 and len(aHost.split('.')) > 1:
                if self.__debug:
                    ebLogWarn('*** FQDN check for %s failed using provided FQDN: %s' % (self.__host, aHost))
                self.__host = aHost
        else:
            self.__host = None

        _config = get_gcontext().mGetConfigOptions()
        _oeda_workdir = ''
        if 'info_oeda_req_path' in _config.keys():
            _oeda_workdir = _config['info_oeda_req_path'] + '/WorkDir/'

        #
        # Only lookup for login credential if user/pwd is not provided
        #
        if 'login_credentials' in list(_config.keys()) and \
           (self.__options is not None and self.__options.username is None and self.__options.password is None):
            _login = _config['login_credentials']
            if self.__host in list(_login.keys()):
                self.__user = _login[self.__host][0]
                self.__pwd  = _login[self.__host][1]
        if self.__user and self.__pwd and self.__debug:
            ebLogTrace('Credential lookup succesfull for host: '+self.__host)

        # Default
        if self.__user is None:

            if self.__options is not None and self.__options.username:
                self.__user = self.__options.username

            else:

                # review if exists opc user entry
                _exakms = get_gcontext().mGetExaKms()
                _cparam = {"FQDN": self.__host}
                _opcEntries = _exakms.mSearchExaKmsEntries(_cparam)
                _found = False

                for _entry in _opcEntries:
                    if _entry.mGetUser() == "opc":
                        if get_gcontext().mCheckRegEntry('opc_enabled') and \
                        get_gcontext().mGetRegEntry('opc_enabled') == "True" and \
                        _opcEntries:
                            ebLogVerbose("sshgen init: Using opc user")
                            self.__user = 'opc'
                            self.__sudo = True
                            _found = True

                if not _found:
                    ebLogVerbose("sshgen init: Using root user")
                    self.__user = 'root'

        # Handle special case for OEDA access based on config
        if 'oeda_host' in list(_config.keys()) and socket.getfqdn(_config['oeda_host']) == self.__host and 'oeda_user' in list(_config.keys()):
            self.__user = _config['oeda_user']

        # Default pwd
        if self.__pwd is None:
            if self.__options is not None and self.__options.password:
                self.__pwd = self.__options.password
            else:
                self.__pwd = base64.b64decode('d2VsY29tZTE=').decode('utf8')

    def __del__(self):

        if self.__transport:
            self.__transport.close()
            self.__transport = None
        if self.__client:
            self.__client.close()
            self.__client = None

    def mGetMaxRetries(self):
        return self.__max_retries

    def mSetMaxRetries(self, aValue):
        self.__max_retries = aValue

    def mGetClient(self):
        return self.__client

    #
    # RC5/User us set by default to root or via credential lookup (one per hostname) or oeda_user
    #
    def mSetUser(self,aUser):

        self.__user = aUser

        # By default, for opc user, execute cmds as sudo.
        if self.__user == 'opc':
            self.__sudo = True

    def mGetUser(self):

        return self.__user

    def mGetHost(self):
        return self.__host

    def mGetSudo(self):
        return self.__sudo

    def mSetSudo(self, aFlag):
        self.__sudo = aFlag

    def mGetConsoleRawOutput(self):

        return self.__console_raw_output

    def mSetPassword(self,aPassword):

        self.__pwd = aPassword

    def mGetExaKmsEntry(self):
        return self.__exakmsEntry

    def mSetExaKmsEntry(self, aEntry):
        self.__exakmsEntry = aEntry

    def mGetExaKmsEntriesList(self):
        return self.__exakmsEntriesList

    def mSetExaKmsEntriesList(self, aValue):
        self.__exakmsEntriesList = aValue

    def mGetSSHClient(self):
        return self.__client

    def mAddPreferredPubkeys(self, aExaKmsEntry, aCount):

        if aExaKmsEntry.mGetHostType() == ExaKmsHostType.SWITCH and (aCount%2 == 0):

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


    @ebRecordReplay.mRecordReplayWrapper
    def mConnectAuthInteractive(self, aTimeout=None):

        def mInterHandler(aTitle, aInstructions, aPromptList):
            _resp = []
            for _prompt in aPromptList:

                if str(_prompt[0]).lower().find("username") != -1:
                    _resp.append(self.__user)
                elif str(_prompt[0]).lower().find("password") != -1:
                    _resp.append(self.__pwd)

            return tuple(_resp)

        #Create the socket
        _sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _sock.connect((self.__host, self.__port))

        #Make the Authentication Interactive
        _timeout = 10
        if aTimeout is not None:
            _timeout = aTimeout

        self.__transport = paramiko.Transport(_sock)
        self.__transport.start_client(timeout=aTimeout)
        self.__transport.auth_interactive(self.__user, mInterHandler)
        ebLogTrace("Interactive Authentication OK")

    @ebRecordReplay.mRecordReplayWrapper
    def mExecuteCmdsAuthInteractive(self, aWaitExecList):

        self.__console_raw_output = ""

        #Init the channel
        self.__channel = self.__transport.open_session()
        self.__channel.get_pty()
        self.__channel.invoke_shell()
        self.__channel.settimeout(1)

        _waitList   = list(aWaitExecList)
        _actualWait = None
        _lastWaitData = ""

        while True:

            if not self.__transport.is_alive():
                return False

            #Wait to File descriptors
            _r, _w, _e = select.select([self.__channel], [], [])

            #Read the information of the socket
            if self.__channel.recv_ready():

                _consoleData = self.__channel.recv(1024).decode('utf8')

                if len(_consoleData) != 0:
                    self.__console_raw_output += _consoleData
                    _lastWaitData += _consoleData

            #Send the commands
            if self.__channel.send_ready():

                # Bug 36042360 - If the public key consists of y/n character, this code is causing exacloud to hang
                # So, do not sent 'y\n' in case it is a request to add sshkey.
                if "sshkey" not in _lastWaitData and re.search("y/n", _lastWaitData):
                    self.__channel.send("y\n")
                    _lastWaitData = ""
                    continue

                if _actualWait is None:
                    if len(_waitList) != 0:
                        _actualWait = _waitList.pop(0)
                    else:
                        break

                if _actualWait is not None:
                    if _actualWait[0] == "" or re.search(_actualWait[0], _lastWaitData):

                        ebLogDebug("Send it: {0}".format(_actualWait[1]))
                        self.__channel.sendall("{0}\n".format(_actualWait[1]))

                        _actualWait = None
                        _lastWaitData = ""

        return True

    def mCreateHaltSRGTestsFile(self):
        _ctx = get_gcontext()
        _coptions = get_gcontext().mGetConfigOptions()
        _localOption = 'env_type'
        if _localOption not in list(_coptions.keys()):
            ebLogVerbose("option env_type not found in configurations. will not write to SRG configuration file.")
        elif "DEV" != _coptions[_localOption]:
            return

        _localOption = 'info_oeda_req_path'
        if _localOption not in list(_coptions.keys()):
            ebLogError("OEDA request path not found for the current step. Will not create halt SRG file.")
            return

        _localOption = 'domU_set'
        if not _ctx.mCheckRegEntry(_localOption):
            ebLogError("DomU environment details not available. Will not create halt SRG file.")
            return
        
        _oeda_req_path = _coptions['info_oeda_req_path']
        if not os.path.isdir(_oeda_req_path):
            ebLogError("OEDA request path doesnt exist.")
            return
        
        if self.__host not in _ctx.mGetRegEntry('domU_set'):
            ebLogVerbose("Machine type is not DomU. Will skip halting SRG tests.")
            return

        _halt_srg_file = os.path.join(_oeda_req_path, 'halt-srg-tests')
        
        _fd_file = open(_halt_srg_file, 'w')
        _fd_file.close()

    def mAddRSAToKeys(self, _data):

        _rsa_mod = True
        if get_gcontext().mCheckConfigOption('disable_key_rsa_patch') == 'True':
            _rsa_mod = False

        if _rsa_mod and 'BEGIN PRIVATE KEY' in _data:
            _data = _data.replace('BEGIN PRIVATE KEY', 'BEGIN RSA PRIVATE KEY')
            _data = _data.replace('END PRIVATE KEY', 'END RSA PRIVATE KEY')

        return _data

    @diag_decorator
    @mDecorateConnectforHaltSRGFile
    @ebRecordReplay.mRecordReplayWrapper
    def mConnect(self, aTimeout=None, aKeyOnly=None, aRetryStrategy=True):

        ebLogVerbose("Enter in mConnect")
        _envArgs = dict(vars(self)).items()
        ebLogVerbose(_envArgs)

        _retry = True
        self.__state = sc_influx
        _timeout = None
        _count = 0
        _ctx = get_gcontext()
        _oeda_workdir = ''

        domus = []
        if _ctx.mCheckRegEntry('domU_set'):
            domus = _ctx.mGetRegEntry('domU_set')

        if 'info_oeda_req_path' in _ctx.mGetConfigOptions().keys():
            _oeda_workdir = _ctx.mGetConfigOptions()['info_oeda_req_path'] + '/WorkDir/'

        if _ctx.mCheckRegEntry('ssh_post_fix') and \
           _ctx.mGetRegEntry('ssh_post_fix') == "True" and \
           _ctx.mCheckRegEntry('domU_set'):

            if domus:

                # Add NAT Hostnames
                for domu in list(domus):
                    if _ctx.mCheckRegEntry('_natHN_' + domu):
                        domus.append(_ctx.mGetRegEntry('_natHN_' + domu))

                if self.__host in domus:
                    ebLogError("ssh_post_fix operations does not require DomU access")
                    raise ExacloudRuntimeError(0x0705, 0xA, "ssh_post_fix operations does not require DomU access")

        if get_gcontext().mCheckRegEntry("ROCE_SWITCHES"):
            if self.__user == "root" and self.__host in get_gcontext().mGetRegEntry("ROCE_SWITCHES"):
                ebLogDebug("ROCE_SWITCH with root detected, change to admin: {0}".format(self.__host))
                self.__user = "admin"

        if not aRetryStrategy:
            _count = self.__max_retries - 1

        if aTimeout is not None:
            _timeout = int(aTimeout)

        # Fetch KMS key
        if not self.mGetExaKmsEntry():

            _exakms = get_gcontext().mGetExaKms()

            _cparam = {"FQDN": self.__host, "user": self.__user, "strict": True}
            _entries = _exakms.mSearchExaKmsEntries(_cparam)

            if _entries:
                self.mSetExaKmsEntry(_entries.pop(0))
                self.mSetExaKmsEntriesList(_entries)

        # 37073667: Force key only on domus
        _keyOnly = False
        if ( aKeyOnly is not None and aKeyOnly is True ) or \
           ( domus and self.__host in domus ):
            _keyOnly = True

        if _keyOnly:
            if not self.mGetExaKmsEntry():
                raise ExacloudRuntimeError(0x0701, 0xA, "SSH Key is required but not provided")

        #condition added for only CPS backup node connect
        _remote_cps = get_gcontext().mCheckConfigOption('remote_cps_host')
        _ociexacc = get_gcontext().mCheckConfigOption('ociexacc','True')

        # check if its an exacc env and remote cps host name is not NONE before proceeding
        if _ociexacc and _remote_cps:
            __host = self.__host.split(".")[0]
            __remote_cps = _remote_cps.split(".")[0]
            if __remote_cps == __host:

                _keyfile = "/home/ecra/.ssh/id_rsa"
                if get_gcontext().mCheckConfigOption("exakms_default_keygen_algorithm", "ECDSA"):
                    _keyfile = "/home/ecra/.ssh/id_ecdsa"

                if os.path.exists(_keyfile):

                    ebLogTrace("Change credentials to CPS Login, using key {0}".format(_keyfile))

                    _privKey = ""
                    with open(_keyfile) as _f:
                        _privKey = _f.read()
                    self.__user = "ecra"
                    _exakms = get_gcontext().mGetExaKms()
                    _kmsEntry = _exakms.mBuildExaKmsEntry(self.__host, self.__user, _privKey)
                    self.mSetExaKmsEntry(_kmsEntry)

        ebLogTrace('*** SSH Connection to: {}@{}'.format(self.__user, self.__host))

        def start_iptables_service(aHost) -> bool:
            """
            This function will try to enable the iptables service in the dom0
            where connectivity is failing for the domU aHost.
            If aHost is not a domU, this function will just return False

            :returns: True if aHost is a domU, False if it's a dom0/cell/switch
                This check is done using '_dom0_domU_relation' entry in the
                context so we rely on this field to determine if aHost
                is a domU or not
            """

            # This field in the context is a dictionary with domu  names as keys
            # and dom0 names as values
            # Adding check as context is not set sometimes
            if not get_gcontext().mCheckRegEntry("_dom0_domU_relation"):
                ebLogError("*** Dom0-DomU registry mapping missing in context.Iptables service could not be started ***.")
                return False
            _dom0Us = get_gcontext().mGetRegEntry("_dom0_domU_relation")

            # Only run this flow when aHost is a domU, and return True
            # Use _dom0_domU_relation in the context for this check
            if aHost in _dom0Us.keys():
                _dom0 = _dom0Us[aHost]
                try:
                    _dom0_node = sshconn(_dom0, None)
                    _dom0_node.mConnect()

                    # Script path variables
                    _local_iptables_script = "scripts/network/dom0_iptables_setup.sh"
                    _remote_iptables_script = "/opt/exacloud/network/dom0_iptables_setup.sh"

                    # Check if iptables script is present, copy it otherwise
                    if not _dom0_node.mFileExists(_remote_iptables_script):

                        ebLogInfo(f"Copying dom0_iptables_setup.sh to Dom0: {_dom0} ***")

                        # Maker sure directory /opt/exacloud/network/ exists
                        _dom0_node.mExecuteCmd(f"/bin/mkdir -p {os.path.dirname(_remote_iptables_script)}")
                        _dom0_node.mCopyFile(_local_iptables_script, _remote_iptables_script)

                    # Execute script to start iptables service and restore dynamic rules
                    ebLogInfo(f"Running 'dom0_iptables_setup' script in {_dom0}")
                    _dom0_node.mExecuteCmdLog(f"/bin/sh {_remote_iptables_script}")

                finally:
                    _dom0_node.mDisconnect()
                    return True

            # Do nothing if aHost is a Dom0/cell/switch, i.e. if aHost is not a DomU
            else:
                ebLogInfo(f'*** No corresponding Dom0 found for {aHost}. Iptables service could not be started ***')
                return False

        _iptables_sv_host_bounce = []
        while _retry:

            ebLogVerbose("Enter in Retry of mConnect: {0}".format(_count))
            _envArgs = dict(vars(self)).items()
            ebLogVerbose(_envArgs)

            _timewait = int(math.exp(float(_count)/2))

            try:
                
                self.__client = paramiko.SSHClient()
                self.__client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                if self.mGetExaKmsEntry():

                    self.mAddPreferredPubkeys(self.mGetExaKmsEntry(), _count)

                    ebLogTrace(f'*** SSH Connection using SSH Private Key: {self.mGetExaKmsEntry()}')
                    _keydat = self.mGetExaKmsEntry().mGetPrivateKey()

                    if "ECDSA" in self.mGetExaKmsEntry().mGetVersion().upper():
                        _key = paramiko.ECDSAKey.from_private_key(io.StringIO(_keydat))

                    else:
                        _keydat = self.mAddRSAToKeys(_keydat)
                        _key = paramiko.RSAKey.from_private_key(io.StringIO(_keydat))

                    self.__client.connect(self.__host, self.__port, self.__user, pkey=_key, allow_agent=False, timeout=_timeout)

                else:

                    if _keyOnly:
                        raise ExacloudRuntimeError(0x0701, 0xA, 'SSH Key is required and user/password login disabled')

                    ebLogTrace('*** SSH Connection Using user/password for: {}@{}'.format(self.__user, self.__host))
                    self.__client.connect(self.__host, self.__port, self.__user, self.__pwd, allow_agent=False, timeout=_timeout)

                self.__transport = self.__client.get_transport()
                self.__transport.use_compression(self.__compress_mode)
                self.__transport.set_keepalive(30)
                self.__state = sc_connected

                _retry = False

                ebLogDebug("Connection Success")

            except (ConnectionRefusedError, paramiko.ssh_exception.NoValidConnectionsError) as e:

                # These Exceptions can happen for iptables issues but also for other reasons, such as
                # a node booting up when an mConnect attempts to establish a connection.
                # We should only raise an error here when ALL below conditions are met:
                #   1 - We are trying to connect to a domU (not a cell or dom0)
                #   2 - We tried already once (at least) to reenable rules/service by running start_iptables_service
                #       function, i.e. we ran start_iptables_service but that didn't fix the problem
                # For other cases, we should only log an error message to debug, and continue to allow
                # our retry mechanism to work

                # If host  was already marked to have run start_iptables_servics, fail
                # this implies host is a domU
                if self.__host  in _iptables_sv_host_bounce:
                    raise ExacloudRuntimeError(0x0801, 0xA, f"Failed to connect to {self.__host}") from e

                # If host is domU, and if iptalbes rules/service has been just enabled,
                # add the host to _iptables_sv_host_bounce
                # list so that is not retried again
                # start_iptables_service does not apply for ExaCC environments
                if not _ociexacc and start_iptables_service(self.__host):
                    ebLogTrace(f"Retrying connection in {self.__host}")
                    _iptables_sv_host_bounce.append(self.__host)

                # If self.__host is not a domU or if it is a domU but is an ExaCC environment, just retry connection following our retry mechanism
                else:
                    ebLogTrace('mConnect: ConnectionRefusedError for {}@{}'.format(self.__user, self.__host))

                # Raise and exception if _max_retries was reached, otherwise  increase counter and sleep
                # for _timewait seconds
                if _count >= self.__max_retries:
                    raise ExacloudRuntimeError(0x0801, 0xA, f"Failed to connect to {self.__host}") from e

                else:
                    ebLogTrace("Retrying connection in {0}s".format(_timewait))
                    _count += 1
                    time.sleep(_timewait)

            except paramiko.AuthenticationException as e:

                ebLogDebug(f"paramiko.AuthenticationException ocurred \n{e}")

                # Try with the next key
                if self.mGetExaKmsEntriesList():
                    _nextEntry = self.mGetExaKmsEntriesList().pop(0)
                    self.mSetExaKmsEntry(_nextEntry)
                    ebLogDebug("mConnect: Change to next exakms entry")

                else:
                    # Refresh new keys from cache
                    _exakms = get_gcontext().mGetExaKms()

                    _cparam = {"FQDN": self.__host, "user": self.__user}
                    _entries = _exakms.mSearchExaKmsEntries(_cparam, aRefreshKey=True)

                    if _entries:
                        self.mSetExaKmsEntry(_entries.pop(0))
                        self.mSetExaKmsEntriesList(_entries)

                if _retry and _count < self.__max_retries:
                    ebLogTrace('mConnect: Authentication failure for {}@{}'.format(self.__user, self.__host))
                    _count += 1

                elif _retry and _count == self.__max_retries:

                    # Attempt user-password based connection in next pass.
                    if self.mGetExaKmsEntry():

                        _json = self.mGetExaKmsEntry().mToJson()
                        _json['publicKey'] = self.mGetExaKmsEntry().mGetPublicKey()
                        del _json['privateKey']

                        ebLogTrace(_json)

                    self.mSetExaKmsEntry(None)
                    ebLogDebug("mConnect: Change to user/password login")
                    _count += 1

                else:

                    ebLogTrace('mConnect: Authentication failure for {}@{}'.format(self.__user, self.__host))
                    raise

            except paramiko.BadHostKeyException as e:

                ebLogDebug(f"paramiko.BadHostKeyException ocurred\n{e}")

                if _retry and _count < self.__max_retries:

                    _valid_host = validate_hostname(self.__host)
                    if not _valid_host:
                        raise

                    _ret = ping_host(self.__host)
                    if not _ret:
                        raise
                    ebLogTrace("Validation of hostname {} is successful".format(self.__host))

                    _cmd_list = ["/bin/ssh-keygen", "-R"]
                    _cmd_list.append(self.__host)
                    execute_local(_cmd_list, aStdOut=DEVNULL, aStdErr=DEVNULL)

                    ebLogTrace('mConnect: BadHostKeyException catched - clearing hostkey and retry in progress')
                    ebLogTrace("Retrying connection")
                    _count += 1
                else:
                    ebLogTrace('mConnect: Could not proceed after clearing hostkey please check manually')
                    raise
            except paramiko.ssh_exception.SSHException as e:

                ebLogDebug(f"paramiko.ssh_exception.SSHException ocurred\n{e}")

                if _retry and str(e) == 'Error reading SSH protocol banner' and _count < self.__max_retries:
                    ebLogTrace('mConnect: Error reading SSH protocol banner and retry in progress')
                    ebLogTrace("Retrying connection in {0}s".format(_timewait))
                    _count += 1
                    time.sleep(_timewait)
                else:
                    ebLogTrace('mConnect: Error reading SSH protocol banner')
                    if _count >= self.__max_retries:
                        raise
                    else:
                        ebLogTrace("Retrying connection in {0}s".format(_timewait))
                        _count += 1
                        time.sleep(_timewait)

            except ExacloudRuntimeError:
                raise

            except Exception as e:

                ebLogTrace('mConnect: Exception:: {} : {}'.format(e.__class__, e))
                ebLogTrace('mConnect: Can not connect (SSH) to host: {} ({})'.format(self.__host, self.__user))
                if _count >= self.__max_retries:
                    raise

                else:
                    ebLogTrace("Retrying connection in {0}s".format(_timewait))
                    _count += 1
                    time.sleep(_timewait)
            finally:

                if self.__state == sc_connected:
                    return True

                # In case of unsuccessful connections, close sshclient and transport 
                # before retrying and recreating them..
                ebLogTrace("Close SSH Client and its underlying transport")
                if self.__transport:
                    self.__transport.close()
                    self.__transport = None
                if self.__client:
                    self.__client.close()
                    self.__client = None

    def mIsConnectable(self, aTimeout=None, aKeyOnly=None):

        _oldmax = self.__max_retries

        try:
            self.__max_retries = 2
            self.mConnect(aTimeout, aKeyOnly, aRetryStrategy=False)
            self.mDisconnect()
            return True
        except:
            return False
        finally:
            self.__max_retries = _oldmax

    def mExecuteCmdAsync(self,aCmd,aCallBacks):

        if not self.__client and not self.__transport:
            # TODO: Use appropriate callback
            return -1

        if self.mGetUser() == "opc" and self.mGetSudo():
            aCmd = "sudo " + aCmd

        # Fetch callbacks
        _cb_read   = aCallBacks[0]
        _cb_write  = aCallBacks[1]
        _cb_error  = aCallBacks[2]
        _cb_status = aCallBacks[3]

        # Initialize channel
        self.__channel = self.__transport.open_session()
        if not _cb_error:
            self.__channel.set_combine_stderr(True)
        if get_gcontext().mCheckConfigOption('enable_multilanguage_support') == 'True':
            self.__channel.exec_command(f"export LANG=en_US.UTF-8;{aCmd}")
        else:
            self.__channel.exec_command(aCmd)

        # Handle Read/Error - TBD: Write
        _data    = ''
        _bufsize = 8192 * 8
        self.__channel.setblocking(0)
        while True:
            _waittime = 0.200
            if self.__channel.recv_ready():
                try:
                    _data = ''
                    _data = self.__channel.recv(_bufsize)
                except socket.timeout:
                    pass
                if len(_data) == 0:
                    # Channel stream has closed
                    break
                else:
                    if _cb_read: _cb_read(_data)
                _waittime = 0.030

            if self.__channel.recv_stderr_ready():
                try:
                    _data = ''
                    _data = self.__channel.recv_stderr(_bufsize)
                except socket.timeout:
                    pass
                if len(_data) == 0:
                    # Channel stream has closed
                    break
                else:
                    if _cb_error: _cb_error(_data)
                _waittime = 0.030

            # Check if we're done
            if self.__channel.exit_status_ready():
                # Wait to receive pending data, if any
                time.sleep(0.030)
                break

            # Handle timeout
            time.sleep(_waittime)

        # Check if anything is pending to read
        while self.__channel.recv_ready():
            try:
                _data = ''
                _data = self.__channel.recv(_bufsize)
            except socket.timeout:
                pass
            if len(_data) and _cb_read: _cb_read(_data)
            time.sleep(0.030)

        while self.__channel.recv_stderr_ready():
            try:
                _data = ''
                _data = self.__channel.recv_stderr(_bufsize)
            except socket.timeout:
                pass
            if len(_data) == 0 and _cb_error: _cb_error(_data)
            time.sleep(0.030)

        self.__exit_status = self.__channel.recv_exit_status()
        if _cb_status: _cb_status(self.__exit_status)

    def mGenerateSshDiag(self, aInsideLoopFx=None, aInsideLoopArgs=[], aInsideLoopKwargs={}):

        _ctx = get_gcontext()
        if "ssh_diagnostic" in _ctx.mGetConfigOptions() and \
           _ctx.mGetConfigOptions()["ssh_diagnostic"] == "True":
                ebLogTrace("Generate Ssh Diag")
        else:
            ebLogVerbose("Skip Generate Ssh Diag")
            return aInsideLoopFx(*aInsideLoopArgs, **aInsideLoopKwargs)

        # Set paramiko destination handlers
        _filename_without_extension = os.path.join('log','ssh_diag_{0}_{1}'.format(self.__host, uuid.uuid1()))
        _destination_handler = ebLogAddDestinationToLoggers(ebGetDefaultLoggerName(),
            _filename_without_extension, ebFormattersEnum.DEFAULT)

        # File headers
        ebLogDebug("*"*30)
        ebLogDebug("Paramiko Debug Information")

        try:
            _ret = aInsideLoopFx(*aInsideLoopArgs, **aInsideLoopKwargs)

            # Clean up file handler
            # Delete Log Files if everything ok.
            ebLogDeleteLoggerDestination(ebGetDefaultLoggerName(), _destination_handler,
                aDeleteLogFiles=True)

            return _ret

        except Exception as _ex:

            ebLogDebug("User: {0}".format(self.__user))

            ebLogDebug("*"*10)
            ebLogTrace(_ex)
            ebLogDebug("*"*10)

            if self.mGetExaKmsEntry():
                ebLogDebug(self.mGetExaKmsEntry().mToJson())
            else:
                ebLogDebug("Exakms Entry not found")

            ebLogDebug("*"*30)

            ebLogDeleteLoggerDestination(ebGetDefaultLoggerName(), _destination_handler)

            raise


    def mGenericRetry(self, aInsideLoopFx=None, aInsideLoopArgs=[], aInsideLoopKwargs={}):

        _count = 0
        _retry = True

        while _retry:
            _timewait = int(math.exp(float(_count)/2))
            try:
                if _count >= self.__max_retries/2:
                    ebLogTrace("Retry connection ...")
                    self.mDisconnect()
                    self.mConnect(aRetryStrategy=False)
                    self.__sftp = None

                return aInsideLoopFx(*aInsideLoopArgs, **aInsideLoopKwargs)

            except Exception as e:
                ebLogTrace('%s(%s%s): Exception:: %s : %s' % (aInsideLoopFx, aInsideLoopArgs, aInsideLoopKwargs, e.__class__, e))
                if _count >= self.__max_retries:
                    raise
                else:
                    ebLogTrace("Retrying {0} in {1}s".format(aInsideLoopFx, _timewait))
                    _count += 1
                    time.sleep(_timewait)

        return None

    @retry_decorator
    def mSimpleExecuteCmd(self, aCmd, aTimeout=None, aDecodeUtf8=False):
        """
        WARNING: This implementation works only for output of 2MB or less which is the default transport window size for linux systems.
        If your command generates an output of size 2MB or greater consider using a different ssh mechanism or implementation.
        For output of size equal to or more than 2MB, this method will hang if the timeout is not set. For calls where timeout is set, the output buffer will be incomplete.
        """

        _maskedCmd = aCmd
        if ("pass" in aCmd and not self.__debug and not "7pass" in aCmd) or \
           "BEGIN RSA" in aCmd or \
           "BEGIN EC" in aCmd or \
           "BEGIN KEY" in aCmd or \
           "BEGIN PRIVATE KEY" in aCmd:
            _maskedCmd = "*"*10

        ebLogTrace("mSimpleExecuteCmd :: Executing on {0}: command <+< {1} >+>".format(self.__host, _maskedCmd))

        if aDecodeUtf8 == True:
            _in = ""
            _out = ""
            _err = ""

            _command_exec_time = time.time()                                                                                                                                                                                                   
            try:

                if get_gcontext().mCheckConfigOption('enable_multilanguage_support') == 'True':
                    fin, fout, ferr = self.__client.exec_command(command=f"export LANG=en_US.UTF-8;{aCmd}")
                else:
                    fin, fout, ferr = self.__client.exec_command(command=aCmd)

                _err = ferr.read().decode("utf-8")
                _out = fout.read().decode("utf-8", errors='ignore')
                self.__exit_status = fout.channel.recv_exit_status()

            except Exception as e:
                ebLogError(f"mSimpleExecuteCmd Error : {e}")
                
            _command_exec_time = time.time() - _command_exec_time
            ebLogTrace("mSimpleExecuteCmd :: Executed on {0} [RC:{1}] [TIME:{2:.4}] the command <+< {3} >+>".format(self.__host, self.__exit_status, _command_exec_time, _maskedCmd))

            return io.StringIO(_in), io.StringIO(_out), io.StringIO(_err)

        _timeout = aTimeout
        _channel = self.__client.get_transport().open_session()
        if _timeout:
            _channel.settimeout(_timeout)

        _command_exec_time = time.time()

        if get_gcontext().mCheckConfigOption('enable_multilanguage_support') == 'True':
            _channel.exec_command(f"export LANG=en_US.UTF-8;{aCmd}")
        else:
            _channel.exec_command(aCmd)

        _i = _channel.makefile_stdin("wb")
        _o = _channel.makefile("r")
        _e = _channel.makefile_stderr("r")

        if _timeout:
            _initial_time = time.time()
            while True:
                _elapsed_time = time.time() - _initial_time

                if _channel.exit_status_ready():
                    self.__exit_status = _channel.recv_exit_status()
                    break

                if _timeout < _elapsed_time:
                    self.__exit_status = 124
                    break

                time.sleep(0.05)
        else:
            while not _channel.exit_status_ready():
                time.sleep(0.05)

        if _channel.exit_status_ready():
            self.__exit_status = _channel.recv_exit_status()

        _command_exec_time = time.time() - _command_exec_time

        ebLogTrace("mSimpleExecuteCmd :: Executed on {0} [RC:{1}] [TIME:{2:.4}] the command <+< {3} >+>".format(self.__host, self.__exit_status, _command_exec_time, _maskedCmd))
        if self.__exit_status != os.EX_OK:
            ebLogTrace(f"mSimpleExecuteCmd failed for command: {_maskedCmd}")

        return (wrapStrBytesFunctions(stream) for stream in (_i, _o, _e))

    @ebRecordReplay.mRecordReplayWrapper
    def mExecuteCmd(self, aCmd, aCurrDir=None, aStdIn=PIPE, aStdOut=PIPE, aStdErr=PIPE, aTimeout=None, aDecodeUtf8=False):
        """
        :param aCmd: string containing the command line to execute in the remote shell
        :return: a triple (in,out,err) of filedescriptor
        """

        _decodeutf8 = aDecodeUtf8
        if self.mGetUser() == "opc" and self.mGetSudo():
            aCmd = "sudo " + aCmd

        if self.__client and aCmd:
            return self.mSimpleExecuteCmd(aCmd, aTimeout, aDecodeUtf8=_decodeutf8)
        else:
            return None, None, None

    @retry_decorator
    def mExecuteScript(self, aScript):
        _channel = self.__client.invoke_shell()
        _stdin = wrapStrBytesFunctions(_channel.makefile('wb'))
        _stdout = wrapStrBytesFunctions(_channel.makefile('rb'))
        if self.__debug:
            ebLogDebug("Running this script:\n" + aScript)
        _stdin.write(aScript + "\nexit\n") ## prevent shell to hang
        _o = _stdout.read()
        _stdout.close()
        _stdin.close()
        _channel.close()
        return _o

    @ebRecordReplay.mRecordReplayWrapper
    def mExecuteCmdLog(self, aCmd, aCurrDir=None, aStdIn=PIPE, aStdOut=PIPE, aStdErr=PIPE, aTimeout=None):

        if self.__debug:
            ebLogTrace('@@@ CMD: %s' % (aCmd)) 

        if self.mGetUser() == "opc" and self.mGetSudo():
            aCmd = "sudo " + aCmd

        if self.__client and aCmd:
            fin, fout, ferr = self.mSimpleExecuteCmd(aCmd, aTimeout)
            out = fout.readlines()
            if out:
                for e in out:
                    ebLogTrace(e[:-1])
            err = ferr.readlines()
            if err:
                for e in err:
                    ebLogTrace(e[:-1].encode('utf-8'))

    @ebRecordReplay.mRecordReplayWrapper
    def mGetCmdExitStatus(self):

        if self.__client:
            return self.__exit_status

    @retry_decorator
    def mCallbackSFTP(self, aByteDone, aByteRemaining):

        if self.xferdone:
            return
        aByteDone = aByteDone * 1.0 / 1024
        aByteRemaining = aByteRemaining * 1.0 / 1024
        if int(aByteRemaining) == 0:
            self.xferdone = True
            return
        # TODO: To be enable via option
        if False:
            ebLogInfo('Transfer: ' + str(int(aByteDone)) + ' ' + str(int(aByteRemaining)) + ' ' + \
                  str(int(aByteDone / aByteRemaining * 100)) + ' %', True)
        sys.stdout.flush()
        if aByteDone == aByteRemaining:
            self.xferdone = True
            # TODO: To be enabled via option
            if False:
                ebLogInfo('* XFER Done *')

    @retry_decorator
    @ebRecordReplay.mRecordReplayWrapper
    def mFileExists(self, aFilename):
        return self.mGetFileInfo(aFilename) is not None


    @retry_decorator
    @ebRecordReplay.mRecordReplayWrapper
    def mGetFileInfo(self, aFilename):

        if '~' in aFilename:
            raise ValueError("~ is not Expanded by mFileExistsFunction/Paramiko SFTP (it look for a directory named ~)")

        if not self.__sftp:
           self.__sftp = self.__client.open_sftp()

        try:
            return self.__sftp.stat(aFilename)
        except IOError as io:
            if io.errno == errno.ENOENT:
                pass
            
        return None


    @retry_decorator
    @ebRecordReplay.mRecordReplayWrapper
    def mReadFile(self, aFilename: str) -> bytes:

        if not self.__client or not aFilename:
            return None

        if '~' in aFilename:
            raise ValueError("~ is not Expanded by mReadFile/Paramiko SFTP (it look for a directory named ~)")

        if not self.__sftp:
           self.__sftp = self.__client.open_sftp()

        with self.__sftp.open(aFilename, 'rb') as fd:
            return fd.read()  # pylint: disable=no-member

    @retry_decorator
    def mWriteFile(self, aFilepath: str, aData: bytes,
                   aAppend: bool = False) -> None:
        """Write data to a remote file.

        aFilepath must not be start with '~'; this is not expanded to remote
        user's HOME.

        :param aFilepath: remote filepath to write to.
        :param aData: data to write to file.
        :param aAppend: whether to append to file rather than
            overwrite/truncate it.
        """
        if self.__client and aFilepath:
            if aFilepath.startswith('~'):
                raise ValueError('"~" as HOME is not expanded')

            if not self.__sftp:
                self.__sftp = self.__client.open_sftp()

            mode = 'ab' if aAppend else 'wb'

            with self.__sftp.open(aFilepath, mode) as fd:
                fd.write(aData)  # pylint: disable=no-member
                #Sometimes a write followed by a quick read does not get any data !
                #Especially, during continous reads/writes of image json file during globalcache update.
                #Hence Lets flush it.
                fd.flush()
              
    # aRemotePath is the remote directory _and_ the remote filename to use
    @retry_decorator
    @ebRecordReplay.mRecordReplayWrapper
    def mCopyFile(self, aFilename, aRemotePath=None):

        if not self.__client or not aFilename:
            return False

        basename = os.path.basename(aFilename)
        if not aRemotePath:
            aRemotePath = './' + basename
 
        _path = aRemotePath

        if self.mGetUser() == "opc":
           # 'opc' user has access to /tmp, thus we can safely copy 
           # to /tmp (without permission denied error). This is to avoid 
           # permission denied error if aRemotePath (passed as parameter)
           # is owned by non-opc user.
           aRemotePath = "/tmp/" + basename

        if not self.mGetExaKmsEntry() or get_gcontext().mCheckConfigOption('disable_scpx') == 'True':
            if not self.__sftp:
                self.__sftp = self.__client.open_sftp()
            self.xferdone = False
            rc = self.__sftp.put(aFilename, aRemotePath, self.mCallbackSFTP)
        else:
            # SCPX
            if not os.path.isdir('.ssh'):
                os.mkdir('.ssh')
                os.chmod('.ssh', 0o700)

            _valid_host = validate_hostname(self.__host)
            if _valid_host:
                _ret = ping_host(self.__host)
                if not _ret:
                    raise ExacloudRuntimeError(0x0766, 0xA, "Ping failed for the hostname")
            else:
                raise ExacloudRuntimeError(0x0766, 0xA, "Failed in validating the hostname")
            ebLogTrace("Validation of hostname {} is successful".format(self.__host))

            _valid_user = validate_user(self.__user)
            if not _valid_user:
                raise ExacloudRuntimeError(0x0793, 0xA, "Failed in validating the user")
            ebLogTrace("Validation of user {} is successful".format(self.__user))

            with tempfile.NamedTemporaryFile(dir=".ssh", delete=True) as _keyfile:

                #Create the keyfile
                os.chmod(_keyfile.name, 0o600)
                _keyfile.write(self.mGetExaKmsEntry().mGetPrivateKey().encode('utf8'))
                _keyfile.flush()

                # Build local scp cmd line to execute
                cmdList = ["/bin/scp", "-o", "StrictHostKeyChecking=no"]
                cmdList.append('-i')
                cmdList.append(_keyfile.name)
                cmdList.append(aFilename)
                cmdList.append(self.__user+'@'+self.__host+':'+aRemotePath)

                _logstr = '>>> '+aFilename+' --> '+self.__user+'@'+self.__host+':'+aRemotePath
                ebLogTrace('*** SCPX FTL TRANSFER IN PROGRESS : %s' % (_logstr))

                # Call the process
                _proc = subprocess.Popen(cmdList, shell=False, stdout=PIPE, stderr=PIPE)
                _std_out, _std_err = wrapStrBytesFunctions(_proc).communicate()
                _rc = _proc.returncode

            if _rc:
                ebLogError(f"User, host, file: {self.__user}, {self.__host}, {aFilename}")
                ebLogError(f"_std_out: {_std_out}, _std_err: {_std_err}, _rc: {_rc}")
                raise ExacloudRuntimeError(0x0701, 0xA, "Something wrong happened while in FTL")

        if self.mGetUser() == "opc":
            # Move the file from /tmp to the desired location.
            _tempfile = "/tmp/" + basename
            if _tempfile != _path:
                ebLogWarn("*** Moving {0} to {1}".format(_tempfile, _path))
                self.mExecuteCmdLog("mv " + _tempfile  + " " + _path)

    @retry_decorator
    @ebRecordReplay.mRecordReplayWrapper
    def mCopy2Local(self, aRemotePath, aLocalPath=None):

        if not self.__client or not aRemotePath:
            return False

        _user = self.mGetUser()

        if _user == "opc":

            # Extract the owner of 'aRemotePath' and connect 
            # to the node as that user. Thereby, avoid getting permissions
            # denied error when fetching(self.__sftp.get) the file.
            _i, _o, _e = self.mExecuteCmd('stat -c "%U" ' + aRemotePath)
            _owner = _o.readlines()[0].strip()

            self.mSetUser(_owner)

            self.mConnect()

        if not aLocalPath:
            basename    = os.path.basename(aRemotePath)
            aLocalPath = './' + basename
        if not self.__sftp:
           self.__sftp = self.__client.open_sftp()
        self.xferdone = False
        rc = self.__sftp.get(aRemotePath, aLocalPath, self.mCallbackSFTP)

        if _user == "opc":
            # Disconnect ssh connection as owner and
            # restore the user for which the original connection was 
            # established.
            self.mDisconnect()

            self.mSetUser(_user)
    
    
    @retry_decorator
    @ebRecordReplay.mRecordReplayWrapper
    def mMakeDir(self, aRemotePath):

        if not self.__client or not aRemotePath:
            return False

        if not self.__sftp:
            self.__sftp = self.__client.open_sftp()

        try:
            self.__sftp.stat(aRemotePath)
        except IOError:
            self.__sftp.mkdir(aRemotePath)
            ebLogTrace('Remote mkdir: ' + aRemotePath)
            rc = True
        else:
            rc = False
        return rc

    @retry_decorator
    @ebRecordReplay.mRecordReplayWrapper
    def mChmodFile(self, aFilename, aPerm=None):

        if not self.__client or not aFilename:
            return False

        if not self.__sftp:
            self.__sftp = self.__client.open_sftp()

        try:
            self.__sftp.chmod(aFilename, aPerm)
        except:
            ebLogError('Chmod: ' + aFilename + ' : ' + str(aPerm))
            rc = False
        else:
            rc = True
        return rc

    @retry_decorator
    @ebRecordReplay.mRecordReplayWrapper
    def mShell(self):
        self.__chan = self.__client.invoke_shell()

    @ebRecordReplay.mRecordReplayWrapper
    def mDisconnect(self):

        self.__state = sc_influx

        if self.__channel:
            self.__channel.close()
            self.__channel = None

        if self.__chan:
            self.__chan.close()
            self.__chan = None

        if self.__client:
            self.__client.close()
            self.__client = None

        if self.__transport:
            self.__transport.close()
            self.__transport = None

        if self.__sftp:
            self.__sftp.close()
            self.__sftp = None

        self.__state = sc_disconnected

    @retry_decorator
    @ebRecordReplay.mRecordReplayWrapper
    def mSetupPwdLess(self, aUser=None, aPwd=None):

        if not aUser:
            aUser = self.__user
        if not aPwd:
            aPwd = self.__pwd

        lSSHKey = None
        if self.__options.sshkey:
            lSSHKey = self.__options.sshkey
        else:
            # Default to current user HOME/.ssh (RSA PUB KEY)
            # Exception gKey missing cause hang
            lSSHKey=os.environ['HOME']+'/.ssh/id_rsa.pub'

        ebLogTrace('Using SSH Key file: ' + lSSHKey)

        if not aUser or not aPwd:
            ebLogError('SetupPwdLess connection requires user/pwd information')
            return

        setup_remote_host(self.__host, aUser, aPwd, lSSHKey)

    @retry_decorator
    @ebRecordReplay.mRecordReplayWrapper
    def mSetupSSHKey(self, aUser=None, aPwd=None):

        if not aUser:
            aUser = self.__user
        if not aPwd:
            aPwd = self.__pwd

        lSSHKey = None
        if self.__options.sshkey:
            lSSHKey = self.__options.sshkey
        else:
            # Default to current user HOME/.ssh (RSA PUB KEY)
            # Exception gKey missing cause hang
            lSSHKey=os.environ['HOME']+'/.ssh/id_rsa.pub'

        if self.__options.clearhostkeys:
            lClearHost = True
        else:
            lClearHost = False

        ebLogTrace('Using SSH Key file: ' + lSSHKey)

        if not aUser or not aPwd:
            ebLogError('SetupSSHKey connection requires user/pwd information')
            return

        setup_ssh_key(self.__host, aUser, aPwd, lSSHKey, lClearHost)

def copy_ssh_key_on_remote_host(aSSHConn, aKey):

    ssh = aSSHConn
    lRemoteName = 'key.pub.'+str(uuid.uuid1())

    # Clean up any previous Pub Key
    lHostSig = lRemoteName.split('-')[-1]
    stdin,stdout,stderr=ssh.exec_command("rm -f key.pub.*-"+lHostSig)
    stdin.flush()
    data=stdout.readlines()

    # Copy local SSH Key (eg. rsa.pub or dsa.pub to remote host)
    ftp=ssh.open_sftp()
    ftp.put(aKey, lRemoteName)
    ftp.close()

    return lRemoteName

def setup_ssh_key(aHost, aUser, aPwd, aKey, aClearHost=False):

    ebLogTrace('Setup SSH Key on remote Host: ' + aHost)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy())
    ssh.connect(aHost, username=aUser, password=aPwd, allow_agent=False)

    lRemoteName = copy_ssh_key_on_remote_host(ssh, aKey)

    # create the .ssh directory
    stdin,stdout,stderr=ssh.exec_command("mkdir .ssh")
    stdin.flush()
    data=stdout.readlines()

    # Read pub Key and extract UserName@Hostname
    f = open(aKey)
    data = f.read()
    f.close()

    if aClearHost:
        ebLogTrace('Remove public SSH Keys from remote host authorized_file')
        # Note: we only clean the entries filtered using _USER_@_HOSTNAME not only _HOSTNAME_
        # lHostName = data.split(' ')[-1].split('@')[-1]
        lHostName = data.split(' ')[-1][:-1] # remove \n
        ebLogTrace('Removing entries: ' + lHostName)
        exec_str = "\cp -f .ssh/authorized_keys .ssh/.old_ak"
        stdin,stdout,stderr=ssh.exec_command(exec_str)
        exec_str = "sed '/"+lHostName+"/d' -i .ssh/authorized_keys"
        stdin,stdout,stderr=ssh.exec_command(exec_str)
        stdin.flush()

    # Append SSH Key file to authorized_host
    stdin,stdout,stderr=ssh.exec_command("cat "+lRemoteName+" >> .ssh/authorized_keys")
    stdin.flush()

    ebLogTrace('* Done *')

def add_pwdless_to_host(aHost, aUser, aPwd, aKey):

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy())
    ssh.connect(aHost, username=aUser, password=aPwd, allow_agent=False)

    lRemoteName = copy_ssh_key_on_remote_host(ssh, aKey)

    # create the .ssh directory
    stdin,stdout,stderr=ssh.exec_command("mkdir .ssh")
    stdin.flush()

    # Remove public key from authorized_keys if already present
    stdin,stdout,stderr=ssh.exec_command("\cp -f .ssh/authorized_keys .ssh/.old_ak")
    localHost = socket.gethostname()
    exec_str = "sed '/"+localHost+"/d' -i .ssh/authorized_keys"
    stdin,stdout,stderr=ssh.exec_command(exec_str)
    stdin.flush()

    stdin,stdout,stderr=ssh.exec_command("cat "+lRemoteName+" >> .ssh/authorized_keys")
    stdin.flush()
    data=stdout.readlines()

    stdin,stdout,stderr=ssh.exec_command("chmod 600 .ssh/authorized_keys")
    stdin.flush()
    data=stdout.readlines()

    ebLogTrace('* Done *')

def setup_remote_host(aHost, aUser, aPwd, aKey):

    o=getoutput('host '+aHost)
    host_ip=o.split(' ')[-1]
    ebLogTrace(aHost + ' ip: ' + host_ip)

    _cmd_list_1 = ["/bin/ssh-keygen", "-R"]
    _cmd_list_1.append(host_ip)
    execute_local(_cmd_list_1)

    _cmd_list_2 = ["/bin/ssh-keygen", "-R"]
    _cmd_list_2.append(aHost)
    execute_local(_cmd_list_2)

    # Default user is current user (e.g. the one running the script)
    # Gather Keys from the host
    home_dir = os.environ['HOME']
    if not os.path.isdir(home_dir):
        ebLogWarn('Home directory env invalid or does not exist !')
        return

    _valid_host = validate_hostname(aHost)
    if _valid_host:
        _ret = ping_host(aHost)
        if not _ret:
            return
    else:
        ebLogWarn('Failed in validating the hostname !')
        return
    ebLogTrace("Validation of hostname {} is successful".format(aHost))

    _out_file = "{0}/.ssh/known_hosts".format(home_dir)
    _fd = open(_out_file, 'a')
    _cmd_list = ["/bin/ssh-keyscan", "-t", "rsa,dsa"]
    _cmd_list.append(aHost)    
    execute_local(_cmd_list, aStdOut=_fd)

    add_pwdless_to_host(aHost, aUser, aPwd, aKey)


def execute_local(aCmdList, aStdOut=PIPE, aStdErr=PIPE):

    _cmd_list = aCmdList
    _stdout = aStdOut
    _stderr = aStdErr

    # Call the process
    _proc = subprocess.Popen(_cmd_list, shell=False, stdout=_stdout, stderr=_stderr)
    _std_out, _std_err = wrapStrBytesFunctions(_proc).communicate()
    _rc = _proc.returncode

    return _rc, _std_out, _std_err

def validate_hostname(aHost):
    _host = aHost

    if len(_host) > 255:
        return False

    #Can begin and end with a number or letter only
    #Can contain hyphens, a-z, A-Z, 0-9
    #1 - 63 chars allowed
    _allowed = re.compile(r'^[a-z0-9]([a-z-0-9-]{0,61}[a-z0-9])?$', re.IGNORECASE)
    _result = all(_allowed.match(x) for x in _host.split("."))

    return _result

def ping_host(aHost, aCount=4):
    _host = aHost
    _count = aCount

    _cmd_list = ["/bin/ping", "-c", "1"]
    _cmd_list.append(_host)

    while _count:

        _rc, _, _std_err = execute_local(_cmd_list, aStdOut=DEVNULL)
        if _rc == 0:
            return True
        _count -= 1
        if _count:
            ebLogTrace('*** Ping Failed retrying for host: %s' % (_host))

    return False

def validate_user(aUser): 

    _user = aUser
    _valid_users = ['opc', 'oracle', 'grid', 'root']
    return _user in _valid_users
