#!/bin/python
#
# $Header: ecs/exacloud/exabox/jsondispatch/jsonhandler.py /main/3 2024/11/06 18:19:05 jfsaldan Exp $
#
# jsondispatch.py
#
# Copyright (c) 2022, 2026, Oracle and/or its affiliates.
#
#    NAME
#      jsondispatch.py - jsondispatch basic functionality
#
#    DESCRIPTION
#      Provide basic/core API for exacloud json-only endpoints
#
#    NOTES
#      None
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    03/13/26 - 38875952: Add mExecuteLocal function
#    jfsaldan    10/30/24 - Bug 37202899 - EXACS:24.4.1:VMBACKUP TO OSS :
#                           DOWNLOAD GOLD BACKUP RETURN COMPLETED/SUCCESS POST
#                           GOLD BACKUP FAILED TO OSS
#    alsepulv    02/11/22 - Creation
#

import json
import uuid
import time
import shlex
from jsonschema import validate

from exabox.agent.ebJobRequest import ebJobRequest
from exabox.core.Context import exaBoxContext
from exabox.core.DBStore import ebExacloudDB, ebGetDefaultDB
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.log.LogMgr import (ebLogDebug, ebLogError, ebLogInfo, ebLogTrace,
                               ebLogWarn)
import subprocess as sp


class JDHandler:

    def __init__(self, aOptions: object, aRequestObj: ebJobRequest = None,
                 aDB: ebExacloudDB = None) -> None:
        """Initializes the JDHandler object.

        :param aOptions: an object holding the exacloud options
        :param aRequestObj: the job request object (if any)
        :param aDb: the database object used to update ECRA request
        """

        self.__options = aOptions
        self.__requestobj = aRequestObj
        self.__db = aDB
        self.__schemaFile = None
        self.__emptyPayloadAllowed = False

    #######################
    # GETTERS AND SETTERS #
    #######################

    def mGetOptions(self):
        return self.__options

    def mGetRequestObj(self):
        return self.__requestobj

    def mGetDB(self):
        return self.__db

    def mGetPayload(self):
        return self.__options.jsonconf

    def mGetSchemaFile(self):
        return self.__schemaFile

    def mSetSchemaFile(self, aFilename):
        self.__schemaFile = aFilename

    def mGetEmtyPayloadAllowed(self):
        return self.__emptyPayloadAllowed

    def mSetEmptyPayloadAllowed(self, aBool):
        self.__emptyPayloadAllowed = aBool

    #################
    # CLASS METHODS #
    #################

    def mParseJsonConfig(self) -> bool:

        if not self.mGetEmtyPayloadAllowed():
            if not self.__options.jsonconf:
                _err_msg = "JSON configuration required; none provided"
                ebLogError(_err_msg)
                return False

        ebLogTrace(f"Input JSON Payload: {json.dumps(self.__options.jsonconf, indent=4, sort_keys=True)}")

        with open(self.__schemaFile, "r") as _f:
            _schema = json.load(_f)

        _endpointPayload = self.__options.jsonconf

        try:
            validate(_endpointPayload, _schema)
        except Exception as e:
            ebLogError(f"Unexpected payload: {self} will not be executed")
            ebLogError(f"{e}")
            return False

        return True

    def mHandleEndpoint(self) -> int:
        """Executes the jsondispatch endpoint and handles the response.

        :returns an integer corresponding to an error value,
                 with 0 representing no error.
        """

        if not self.mParseJsonConfig():
            raise ExacloudRuntimeError(0x00, 0x0, "Invalid json provided")

        _rc, _resp = self.mExecute()

        # Return reqobj to ECRA
        _reqobj = self.__requestobj
        if _reqobj:
            _reqobj.mSetData(json.dumps(_resp, sort_keys=True))
            if not self.__db:
                self.__db = ebGetDefaultDB()
            self.__db.mUpdateRequest(_reqobj)

        #Console output
        ebLogInfo(json.dumps(_resp, indent=4, sort_keys=True))

        return _rc

    def mExecute(self) -> tuple:
        """Executes the endpoint.

        :returns a tuple (int, dict) containing an error code, with 0
                 representing no error, and a dict, which is the response of
                 the endpoint
        """

        raise NotImplementedError


    def mExecuteLocal(self, aCmd, aCurrDir=None, aStdIn=sp.PIPE, aStdOut=sp.PIPE, aStdErr=sp.PIPE, aFailOnRc=True, aShell=False, aDebug=True):

        _starttime = time.time()

        _args = aCmd
        if isinstance(aCmd, str):
            _args = shlex.split(aCmd)

        # Add timeot hook of 20m
        #_args = ["/usr/bin/timeout", "1200"] + _args

        ebLogTrace(f'mExecuteLocal: {_args}')

        _current_dir = aCurrDir
        _stdin = aStdIn
        _stdout = aStdOut
        _stderr = aStdErr

        _proc = sp.Popen(_args, stdin=_stdin, stdout=_stdout, stderr=_stderr, cwd=_current_dir, shell=aShell)
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

        ebLogTrace(f'mExecuteLocal: RC:{_rc}')
        ebLogTrace(f"TIME: {time.time() - _starttime} secs")

        if aFailOnRc and _rc != 0:
            _msg = f'Command execution failed: {aCmd}\n'
            _msg = f"{_msg}RC: {_rc}\n"
            _msg = f"{_msg}STDOUT: {_stdoutP}\n"
            _msg = f"{_msg}STDERR: {_stderrP}\n"
            ebLogError(_msg)
            raise OSError(_msg)
        else:
            if aDebug:
                ebLogTrace(f'STDOUT: "{_stdoutP}"')
                ebLogTrace(f'STDERR: "{_stderrP}"')

        return _rc, _stdoutP, _stderrP

# end of file
