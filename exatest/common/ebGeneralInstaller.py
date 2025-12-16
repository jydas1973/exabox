#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/common/ebGeneralInstaller.py /main/2 2021/04/16 12:46:06 jesandov Exp $
#
# ebGeneralInstaller.py
#
# Copyright (c) 2021, Oracle and/or its affiliates. 
#
#    NAME
#      ebGeneralInstaller.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    02/23/21 - Creation
#

import os
import sys
import shlex
import socket
import subprocess as sp

from exabox.core.Node import exaBoxNode
from exabox.core.Context import exaBoxContext, get_gcontext

class ebGeneralInstaller:

    def __init__(self, aExacloudPath, aExaboxCfg, aVerbose=False):

        self.__exacloudPath = aExacloudPath
        self.__exaboxCfg = aExaboxCfg
        self.__verbose = aVerbose

    #######################
    # Getters and Setters #
    #######################

    def mIsVerbose(self):
        return self.__verbose

    def mSetVerbose(self, aValue):
        self.__verbose = aValue

    def mGetExacloudPath(self):
        return self.__exacloudPath

    def mSetExacloudPath(self, aValue):
        self.__exacloudPath = aValue

    def mGetExaboxCfg(self):
        return self.__exaboxCfg

    def mSetExaboxCfg(self, aValue):
        self,__exaboxiCfg = aValue

    #################
    # Class Methods #
    #################

    def mNextPortEmpty(self, aPort):
        return self.mGetEmptyPort(int(aPort), 1)

    def mPreviousPortEmpty(self, aPort):
        return self.mGetEmptyPort(int(aPort) - 1, -1)

    def mGetEmptyPort(self, aPort, aStep):
        _port = aPort
        while self.mPortInUse(_port):
            _port += aStep
        return _port

    def mPortInUse(self, aPort):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("127.0.0.1", aPort))
        except socket.error:
            s.close()
            return True
        s.close()
        return False

    def mSocketInUse(self, aSocket):

        _out = False
        try:

            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.bind(aSocket)

            os.remove(aSocket)

        except FileNotFoundError:
            pass

        except socket.error:
            _out = True

        return _out

    def mExecuteLocal(self, aCmd, aCurrDir=None, aStdIn=sp.PIPE, aStdOut=sp.PIPE, aStdErr=sp.PIPE, aMock=False):

        _args = aCmd
        if isinstance(aCmd, str):
            _args = shlex.split(aCmd)

        if self.mIsVerbose():

            if self.mIsVerbose() == "list":
                print('@@@ mExecuteLocal: {0} @@@'.format(_args), flush=True)

            else:
                print('@@@ mExecuteLocal: `{0}` @@@'.format(aCmd), flush=True)

        _rc = 0
        _stdoutP = ""
        _stderrP = ""

        if aMock:

            _node = exaBoxNode(get_gcontext(), aLocal=True)

            try:
                _node.mConnect()
                _rc,  _stdout,  _stderr = _node.mExecuteCmd(aCmd)
                _stdoutP = _stdout.read()
                _stderrP = _stderr.read()

            finally:
                _node.mDisconnect()

        else:

            _current_dir = aCurrDir
            _stdin = aStdIn
            _stdout = aStdOut
            _stderr = aStdErr

            _proc = sp.Popen(_args, stdin=_stdin, stdout=_stdout, stderr=_stderr, cwd=_current_dir)
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

        return _rc, _stdoutP, _stderrP

    ######################
    # Interfaces Methods #
    ######################

    def mInstall(self):
        raise NotImplementedError

# end of file
