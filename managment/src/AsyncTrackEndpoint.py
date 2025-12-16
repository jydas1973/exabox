"""
 Copyright (c) 2014, 2023, Oracle and/or its affiliates.

NAME:
    AsyncTrackingEndpoint - Basic functionality

FUNCTION:
    Async Tracking endpoint of the managment

NOTE:
    None    

History:
    hgaldame    06/05/2022 - 34146854 - oci/exacc: persists exacloud remote ec 
                             async request status
    hgaldame    04/06/2022 - 33643036 - remote ec to return text as json object
                             in case of success & failure
    jesandov    06/04/2020 - Add docstring in functions and add Python subprocess support
    jesandov    15/04/2019 - File Creation
"""



import os
import sys
import json
import time
import uuid
import subprocess
import exabox.managment.src.utils.CpsExaccUtils as utils

from datetime import datetime
from exabox.tools.AttributeWrapper import wrapStrBytesFunctions
from exabox.BaseServer.BaseEndpoint import BaseEndpoint
from exabox.BaseServer.AsyncProcessing import ProcessStructure
from exabox.managment.src.EditorEndpoint import EditorEndpoint


class AsyncTrackEndpoint(EditorEndpoint):

    def __init__(self, aHttpUrlArgs, aHttpBody, aHttpResponse, aSharedData):

        #Initialization of the base class
        EditorEndpoint.__init__(self, aHttpUrlArgs, aHttpBody, aHttpResponse, aSharedData)

        #Extra parameters
        self.__async = aSharedData['async']
        self.__asyncLogTag = "Async"

    def mGetAsyncLogTag(self):
        return self.__asyncLogTag

    def mSetAsyncLogTag(self, aTag):
        self.__asyncLogTag = aTag

    def mBashExecution(self, aCmd, aRedirect=subprocess.PIPE):
        """
        Execute a single bash command

        :param aCmd: desired command to execute in bash
        :param aRedirect: location where to reditrec the command

        :return: returncode, stdout and stderr as three arguments
        """

        if "exatest_mock" in self.mGetShared():

            _cmd = " ".join(aCmd)
            _util = self.mGetShared()['util']
            _remoteec = _util.mGetRemoteEC()
            _rc,  _stdout, _stderr = _remoteec.mExecuteLocal(_cmd, aMock=self.mGetShared()['exatest_mock'])

        else:

            _sp = subprocess.Popen(aCmd, stdout=aRedirect, stderr=aRedirect, close_fds=True, shell=False)
            _stdout, _stderr = wrapStrBytesFunctions(_sp).communicate()
            _rc = _sp.returncode

        return _rc, _stdout, _stderr

    def mAsyncLog(self, aFd, aProcessId, aMsg, aDebug=True):
        """
        Log used during async operations

        :param aFd: file descriptor of the log file
        :param aProcessId: process id to identified
        :param aMsg: desired message to put on the log
        """
        self.mGetLog().mInfo("{0} - {1} - {2}".format(self.__asyncLogTag, aProcessId, aMsg))
        _msg = aMsg

        # If debug append the line 'RemoteManagment Debug - ' to all the output
        if aDebug:
            _msg = "\n".join(list(map(lambda x: "RemoteManagment Debug - {0}".format(x), _msg.split("\n"))))

        aFd.write("{0}\n".format(_msg))
        aFd.flush()


    def mAsyncBashExecution(self, aLogFilename, aProcessId, aCustomArgs):
        """
        Wrapper used to execute asyn bash command from mCreateBashProcess

        :param aLogFilename: log file designed for the async operation
        :param aProcessId: unique id designed for the async operation
        :param aCustomArgs: function relate arguments

        :return: if a command fail, return that return code, otherwise return 0
        """

        _rc = 0
        with open(aLogFilename, "w") as _log:

            for _cmd in aCustomArgs["cmd_list"]:

                self.mAsyncLog(_log, aProcessId, "Execute: '{0}'".format(_cmd), aDebug=True)

                _newrc, _stdout, _stderr = self.mBashExecution(_cmd, _log)
                _log.flush()

                self.mAsyncLog(_log, aProcessId, "Rc: '{0}'".format(_newrc), aDebug=True)

                if _newrc != 0:
                    _rc = _newrc

        return _rc
 
    def mAsyncBashExecutionStdOut(self, aLogFilename, aProcessId, aCustomArgs):
        """
        Wrapper used to execute asyn bash command and read the standard output

        :param aLogFilename: log file designed for the async operation
        :param aProcessId: unique id designed for the async operation
        :param aCustomArgs: function relate arguments

        :return: if a command fail, return the returrn code and the standard output for the given process id
        """

        _output = []
        with open(aLogFilename, "w") as _log:

            for _cmd in aCustomArgs["cmd_list"]:

                self.mAsyncLog(_log, aProcessId, "Execute: '{0}'".format(_cmd), aDebug=True)

                _newrc, _stdout, _stderr = self.mBashExecution(_cmd)
                self.mAsyncLog(_log, aProcessId, "rc: '{0}'".format(_newrc), aDebug=True)
                self.mAsyncLog(_log, aProcessId, "stdout: '{0}'".format(_stdout), aDebug=True)
                self.mAsyncLog(_log, aProcessId, "errout: '{0}'".format(_stderr), aDebug=True)
                _log.flush()

                self.mAsyncLog(_log, aProcessId, "Rc: '{0}'".format(_newrc), aDebug=True)
                _cmdListOutput = { "rc": _newrc, "stdout": _stdout, "stderr" : _stderr, "command": _cmd}  
                _output.append(_cmdListOutput)

        return _output


    def mCreatePythonProcess(self, aCallback, aCustomArgs, aId=None, aLogFile=None, aName=None, aOnFinish=None, aOnFinishArgs=None, \
        aPersistState=False):
        """
        Create a new subprocess controlled by the Remote Managment

        :param aCallback: function that will be running as subprocess
                          the function must to be of the form:
                          aCallback(aLogFilename, aId, aCustomArgs)
        :param aCustomArgs: arguments fo the aCallback function in aCustomArgs
        :param aId: custom id of the new process or a new uuid will be calculated
        :param aName: custome name of the new process
        :param aOnFinish: custom function to execute when the process finish
        :param aOnFinishArgs: argument for aOnFinish functions
        :param aPersistState: Boolean. True if the process state should be persisted

        :return: async response with the tracking uuid
        """

        #Get the id
        _id = aId
        if _id is None:
            _id   = str(uuid.uuid1())

        #Compute Exacloud Path
        _exapath = self.mGetConfig().mGetPath()
        _exapath = _exapath[0: _exapath.find("exabox")] 

        #Compute Log File
        _logFile = aLogFile
        if _logFile is None:
            _logFile = "{0}/log/threads/mgnt-{1}.log".format(_exapath, _id)

        #Create the argument list
        _args = []
        _args.append(_logFile)
        _args.append(_id)
        _args.append(aCustomArgs)

        # Call the subprocess
        _process = ProcessStructure(aCallback, aArgs=_args, aId=_id)
        _process.mSetLogTimeoutFx(self.mGetLog().mWarn)

        _process.mSetLogFile(_logFile)

        if aName is not None:
            _process.mSetName(aName)

        if aOnFinish is not None:
            _process.mSetOnFinish(aOnFinish)
            _process.mSetOnFinishArgs(aOnFinishArgs)
        if aPersistState:
            _process.mSetPersistState(True)

        self.__async.mStartAppend(_process)

        #Return the response
        _response = {}
        _response['id'] = _id
        _response['reqtype'] = "async call"

        return _response

    def mCreateBashProcess(self, aCmdList, aId=None, aLogFile=None, aName=None, aOnFinish=None, aOnFinishArgs=None, aPersistState=False):
        """
        Create a new subprocess that execute bash commands

        :param aCmdList: Bash command to execute
        :param aId: custom id of the new process or a new uuid will be calculated
        :param aName: custome name of the new process
        :param aOnFinish: custom function to execute when the process finish
        :param aOnFinishArgs: argument for aOnFinish functions
        :param aPersistState: Boolean. True if the process state should be persisted
        :return: async response with the tracking uuid
        """

        #Create the args
        _customArgs = {"cmd_list": aCmdList}
        return self.mCreatePythonProcess(self.mAsyncBashExecution, _customArgs, aId, aLogFile, aName, aOnFinish, aOnFinishArgs, aPersistState=aPersistState)

    def mGet(self):

        _pruid = None
        if self.mGetUrlArgs() is not None:
            if "id" in list(self.mGetUrlArgs().keys()):
                _pruid = self.mGetUrlArgs()['id']

        self.mGetResponse()['text'] = []

        for _process in self.__async.mGetProcessList():
            _processDict = {}

            _processDict["id"]         = _process.mGetId()
            _processDict["name"]       = _process.mGetName()
            _processDict["alive"]      = _process.is_alive()
            _processDict["log_file"]   = _process.mGetLogFile()
            _processDict["time_start"] = _process.mGetStartTime()
            _processDict["rc"]         = _process.mGetReturn()

            if _processDict['alive']:
                _processDict["time_end"] = None
            else:
                _processDict["time_end"] = _process.mGetEndTime()

            if _pruid is None:
                self.mGetResponse()['text'].append(_processDict)

            else:
                if _processDict['id'] == _pruid:
                    utils.get_cps_return_code(_process.mGetReturn(), _processDict, _process.is_alive())
                    self.mGetResponse()['text'] = _processDict
                    break

    def mDelete(self):

        _id = self.mGetBody()["id"]

        _process = self.__async.mGetProcess(_id)

        if _process is None:
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error']  = "Process id does not exists"
            self.mGetResponse()['text']   = "Process id does not exists"
        else:
            self.__async.mKillProcess(_process)
            self.mGetResponse()['text'] = "Process has stopped"


    def mPut(self):

        _offset = None
        _limit  = None
        _file   = None

        if "id" not in list(self.mGetBody().keys()):
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = "missing argument id"

        else:
            _id = self.mGetBody()['id']

            if "offset" in list(self.mGetBody().keys()):
                try:
                    _offset = int(self.mGetBody()['offset'])
                except:
                    _offset = None

            if "limit" in list(self.mGetBody().keys()):
                try:
                    _limit = int(self.mGetBody()['limit'])
                except:
                    _limit = None

            _alive = False
            _process = self.__async.mGetProcess(_id)

            if _process is None:
                self.mGetResponse()['status'] = 500
                self.mGetResponse()['error'] = "Process id does not exists"

            else:

                _file = _process.mGetLogFile()

                if _file is not None:
                    
                    if _file.startswith("/"):

                        if not os.path.exists(_file):
                            #Compute Exacloud Path
                            _exapath = self.mGetConfig().mGetPath()
                            _exapath = _exapath[0: _exapath.find("exabox")] 

                            #Compute Log File
                            _file = "{0}/log/threads/mgnt-{1}.log".format(_exapath, _id)
                            _process.mSetLogFile(_file)

                    else:
                        _file = self.mGetPath(self.mGetBody()['file'])

                if _file is None:
                    self.mGetResponse()['status'] = 404
                    self.mGetResponse()['error'] = "File outside the exacloud folder"

                elif not os.path.exists(_file):
                    self.mGetResponse()['status'] = 404
                    self.mGetResponse()['error'] = "Tracking file not longer avaliable: {0}".format(_file)

                else:

                    if os.path.isdir(_file):
                        self.mGetResponse()['status'] = 404
                        self.mGetResponse()['error'] = "Tracking file is a folder"

                    else:
                        _alive = _process.is_alive()
                        _content = self.mGetFileContent(_file, _offset, _limit, "^(?!RemoteManagment Debug)")

                        self.mGetResponse()['text'] = {"content": _content, "alive": _alive, "reqtype": "async call", "id": _id}

                        if len(list(_content.keys())) != 0:
                            _offset = max([int(x) for x in list(_content.keys())])
                            self.mGetResponse()['text']['offset'] = _offset

    def mGetSharedData(self):
        return self.__async
 
# end of file
