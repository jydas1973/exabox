"""
$Header: 

 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    ebOedacli - Basic functionality

FUNCTION:
    This class takes a XML and apply oedacli commands

NOTE:
   Project Documentation: https://confluence.oraclecorp.com/confluence/pages/viewpage.action?pageId=1063643852

History:

    MODIFIED   (MM/DD/YY)
       jesandov 06/03/25 - Bug 38024144 - Add sanitize string to ignore errors
       prsshukl 09/17/24 - Bug 37068271 - Fix exacloud condition to ignore oeda
                           warning
       aararora 08/29/24 - Bug 36998256: IPv6 fixes
       pbellary 06/10/24 - 36690543 - EXACLOUD: PATCH XML WITH EXASCALE INFORMATION FOR INFO COMMAND
       jesandov 02/23/24 - 36326706: Add After and Before callbacks
       jesandov 07/21/23 - 35539443: Integration of VM MOVE with OEDA API
       jfsaldan 03/14/23 - Fixing ResourceWarning: subprocess still
                           running/unclosed file
       akkar    05/08/22 - bandit fixes 34004580
        jesandov    17/12/2018 - File Creation

"""

import json
import os
import re
import six
import subprocess
import shlex
import sys
import tempfile
from time import gmtime, strftime

from exabox.tools.AttributeWrapper import wrapStrBytesFunctions
from exabox.core.Context import get_gcontext
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogVerbose
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.Node import exaBoxNode

DEVNULL = open(os.devnull, 'wb')

class ebOedacli(object):

    def __init__(self, aOedacliPath=None, aSaveDir=None, aLogFile="oedacli.log", aDeploy=False):

        self.__oedacliPath      = aOedacliPath
        self.__oedacliScript    = []
        self.__logDir           = os.path.abspath(aSaveDir)
        self.__logFile          = aLogFile
        self.__oedaXml          = None
        self.__saveXml          = None
        self.__posibleCmds      = []
        self.__autoSaveActions  = True
        self.__autoMergeActions = True
        self.__isDeploy         = aDeploy
        self.__useJdb           = False
        self.__callbacks        = []

        if "use_oedacli_jdb" in get_gcontext().mGetConfigOptions() and \
           str(get_gcontext().mGetConfigOptions()["use_oedacli_jdb"]).upper() == "TRUE":
            self.__useJdb = True

        self.mLog("Info", "__init__")

        if aOedacliPath is not None and not self.mProbePath(): 
            _msg = "Invalid path to oedacli: {0}".format(aOedacliPath)
            self.mLog("Error", _msg)
            raise ExacloudRuntimeError(0x0EDA, 0x0EDA, _msg)

    def mGetCallbacks(self):
        return self.__callbacks

    def mAddCallback(self, aCallbackFx, aCallbackArgs, aCallbackMoment="BEFORE"):
        """
        CallbackFx needs to have the headers:
            def aCallbackFx(aCmd, aCallbackArgs)
        This callbacks will be executed before the real command will be executed
        """
        self.__callbacks.append({"fx":aCallbackFx, "args":aCallbackArgs,  "moment": aCallbackMoment.upper()})

    def mGetAutoSaveActions(self):
        return self.__autoSaveActions

    def mSetAutoSaveActions(self, aBool):
        self.__autoSaveActions = aBool

    def mIsDeploy(self):
        return self.__isDeploy

    def mSetDeploy(self, aBool):
        self.__isDeploy = aBool

    def mGetAutoMergeActions(self):
        return self.__autoMergeActions

    def mSetAutoMergeActions(self, aBool):
        self.__autoMergeActions = True

    def mGetOedacliPath(self):
        return self.__oedacliPath

    def mSetOedacliPath(self, aStr):
        self.__oedacliPath = aStr

    def mGetOedacliScript(self):
        return self.__oedacliScript

    def mSetOedacliScript(self, aList):
        self.__oedacliScript = aList

    def mGetLogDir(self):
        return self.__logDir

    def mSetLogDir(self, aStr):
        self.__logDir = aStr

    def mGetLogFile(self):
        return self.__logFile

    def mSetLogFile(self, aStr):
        self.__logFile = aStr

    def mGetOedaXml(self):
        return self.__oedaXml

    def mSetOedaXml(self, aXml):
        self.__oedaXml = os.path.abspath(aXml)

    def mGetSaveXml(self):
        return self.__saveXml

    def mSetSaveXml(self, aXml):
        self.__saveXml = os.path.abspath(aXml)

    def mGetPosibleCmds(self):
        return self.__posibleCmds

    def mSetPosibleCmds(self, aList):
        self.__posibleCmds = aList

    def mProbePath(self):
        _cmd = self.mGetOedacliPath()
        eboxNodeObject = exaBoxNode(get_gcontext())
        _rc, _, _, _ = eboxNodeObject.mExecuteLocal(_cmd, aStdOut=DEVNULL, aStdErr=DEVNULL)
        if _rc == 0:
            self.mCalculatePosibleCmds()
            return True
        else:
            return False

    def mAppendCommand(self, aCommand, aArgs=None, aWhere=None, aForce=False):
        _flag = aForce
        _args = {}
        if aArgs is not None:
            _args = {k:v for k,v in six.iteritems(aArgs) if v is not None}

        _where = {}
        if aWhere is not None:
            _where = {k:v for k,v in six.iteritems(aWhere) if v is not None}

        _argsStr   = self.mFormatParam(_args)
        _whereStr = self.mFormatParam(_where)

        _actions = '%s %s' % (aCommand, _argsStr)

        if _whereStr:
            _actions += ' WHERE ' + _whereStr

        self.mGetOedacliScript().append(_actions)

        if self.__autoSaveActions:
            self.mSaveAction(aForce=_flag)

        if self.mGetAutoMergeActions():
            self.mMergeActionsDeploy()

        self.mLog("Info", "Append cmd: '{0}'".format(_actions))

    def mComment(self, aComment):
        _formatComment = '# ' + re.sub("\n","\n# ", aComment)
        self.mGetOedacliScript().append(_formatComment)

    def mLog(self, aType, aMsg, aExacloud=False, aFilename="ebOedacli"):

        if aExacloud:
            _format = "{0} * {1}".format(aFilename, aMsg)

            if aType == "Error":
                ebLogError(_format)
            elif aType == "Warn":
                ebLogWarn(_format)
            elif aType == "Debug":
                ebLogDebug(_format)
            elif aType == "Info":
                ebLogDebug(_format)

        with open(os.path.join(self.mGetLogDir(), self.mGetLogFile()), "a+") as _f:
            _today = strftime("%Y-%m-%d %H:%M:%S", gmtime())
            _str = "{0} * {1} * {2} * {3}\n".format(_today, aFilename, aType, aMsg)
            _f.write(_str)


    def mGetJsonData(self, aXmlfile=None):

        if aXmlfile is not None:
            self.mSetOedaXml(aXmlfile)

        structures = {}

        # initialize main structures
        structs = ['LOAD FILE NAME=%s' % (self.mGetOedaXml()),
                   'LIST MACHINES',
                   'LIST SCANS',
                   'LIST CLUSTERS',
                   'LIST VIPS',
                   'LIST NETWORKS',
                   'LIST SWITCHES',
                   'LIST DATABASEHOMES',
                   'LIST DATABASES',
                   'LIST DISKGROUPS',
                   'LIST RACKS',
                   'LIST CLUSTERSCANS']

        self.mSetOedacliScript(structs)

        ebLogInfo("Info", self.mGetOedacliScript())
        out = re.split("oedacli>.*\n", self.mExecute())

        structures['machine'] = json.loads(out[2][out[2].find('['):])
        structures['scan'] = json.loads(out[3][out[3].find('['):])
        structures['cluster'] = json.loads(out[4][out[4].find('['):])
        structures['vip'] = json.loads(out[5][out[5].find('['):])
        structures['network'] = json.loads(out[6][out[6].find('['):])
        structures['switch'] = json.loads(out[7][out[7].find('['):])
        structures['databaseHome'] = json.loads(out[8][out[8].find('['):])
        structures['database'] = json.loads(out[9][out[9].find('['):])
        structures['diskGroup'] = json.loads(out[10][out[10].find('['):])
        structures['racks'] = json.loads(out[11][out[11].find('['):])

        return structures

    def mFormatParam(self, aParams=None):
        _list = [key + '="' + aParams[key] + '"' for key in aParams]
        if len(_list) == 0:
            return ''
        return ' '.join(_list)
    
    def mRun(self, aLoadPath=None, aSavePath=None):

        #Save the Load file path
        if aLoadPath is not None:
            self.mSetOedaXml(aLoadPath)

        self.mGetOedacliScript().insert(0, 'LOAD FILE NAME=%s' % (self.mGetOedaXml()))

        if not self.mGetAutoMergeActions():
            self.mMergeActionsDeploy()

        #Add the path to save the xml
        if aSavePath is not None:
            self.mSetSaveXml(aSavePath)

        if self.mGetSaveXml():
            self.mGetOedacliScript().append('SAVE FILE NAME=%s' % self.mGetSaveXml())

        #Execute the commands
        self.mLog("Info", "\n".join(self.mGetOedacliScript()))
        _stdout = self.mExecute()

        # clean script buffer
        self.mSetOedacliScript([])

        return _stdout

    def mCalculatePosibleCmds(self):
        _oedacli_path = f'{self.mGetOedacliPath()} -e "help"'
        cmd_list = shlex.split(_oedacli_path)
        shell_output = []
        filtered_output = []

        with subprocess.Popen(cmd_list, stdin=subprocess.PIPE, stdout=subprocess.PIPE) as _proc:
            shell_output = _proc.stdout.read().decode("utf-8").replace('\t', ' ').split('\n\r')

        for line in shell_output:
            if line.startswith("  ") and 'Available Objects' not in line:
                line = line.strip()
                filtered_output.append(line)
        filtered_output.sort()
        self.mSetPosibleCmds(filtered_output)

    def mMergeActionsDeploy(self):

        #Add the final commands of Oedacli
        if self.mIsDeploy():
            self.mGetOedacliScript().append('MERGE ACTIONS')
            self.mGetOedacliScript().append('DEPLOY ACTIONS')
        else:
            self.mGetOedacliScript().append('MERGE ACTIONS FORCE')

    def mMergeAction(self):
        if len(self.mGetOedacliScript()) != 0 and self.mGetOedacliScript()[-1].find("SAVE ACTION") == -1:
            self.mGetOedacliScript().append('MERGE ACTIONS')

    def mSaveAction(self, aForce=False):
        if len(self.mGetOedacliScript()) != 0 and self.mGetOedacliScript()[-1].find("SAVE ACTION") == -1:
            if aForce:
                self.mGetOedacliScript().append('SAVE ACTION FORCE')
            else:
                self.mGetOedacliScript().append('SAVE ACTION')

    def mGetOedacliLogLines(self):

        _oedaLog = os.path.abspath(self.mGetOedacliPath() + "/../log/oedacli.out")

        with open(_oedaLog, "r") as _oLog:
            _logLines = _oLog.readlines()

        return _logLines

    def mExecute(self):

        self.mLog("Warn", "*"*80)
        self.mLog("Warn", "*** START COMMAND EXECUTION ***")
        self.mLog("Warn", "*"*80)

        # Add Java Options for Debug
        _javaOptions = "-XX:-UseLargePages -Xss6m -Xmx4096m"

        if self.__useJdb:
            _javaOptions += " -Xdebug -Xrunjdwp:transport=dt_socket,address=8008,server=y,suspend=n"

        _cmd = """sed -i 's/JAVA_OPTIONS=.*/JAVA_OPTIONS="{0}"/g' {1}"""
        _cmd = _cmd.format(_javaOptions, self.mGetOedacliPath())
        _cmd = shlex.split(_cmd)
        out = subprocess.Popen(_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        #Execute the Oedacli script
        _oedacliArgs = get_gcontext().mGetConfigOptions()["oedacli_extra_args"].split(" ")
        if get_gcontext().mGetExaKms().mGetDefaultKeyAlgorithm() == "RSA":
            _oedacliArgs.append("--enablersa")

        _cmd = [self.mGetOedacliPath(), '-l', '-j'] + _oedacliArgs

        # Ensure we use a unique stdout filename to interact with oedacli so
        # that it's safe to use this utility concurrently.
        with tempfile.NamedTemporaryFile(
                prefix="oedacli_command_", suffix=".log",
                dir=self.mGetLogDir(), delete=False) as cmd_fd:
            _outfile = cmd_fd.name
            self.mLog("Info", f"Commands file: {_outfile}")

        _outfileFd1 = open(_outfile, "w")

        _subproc = subprocess.Popen(_cmd, stdin=subprocess.PIPE,  \
                                          stdout=_outfileFd1, \
                                          stderr=_outfileFd1, shell=False)

        _lastLineLogOedacliIdx = len(self.mGetOedacliLogLines())
        _lastOedacliOutput = "oedacli>"

        _errMsg = "Oedacli Error found on script execution."
        _errMsg += "Please review the log: {0}".format(os.path.join(self.mGetLogDir(), self.mGetLogFile()))

        try:

            _cmdIdx = 0
            _lastCmdIdx = 0
            _count = 1
            _affectedCmd = ""
            _startDebug = False

            # Fetch for errors
            while _cmdIdx < len(self.mGetOedacliScript()):

                _cmd = self.mGetOedacliScript()[_cmdIdx]

                # Wait to have the oedacli>
                _ready = False
                while not _ready:

                    with open(_outfile, "r") as _f:

                        _logContent = _f.read()

                        if _logContent.count("oedacli>") == _count:
                            _ready = True

                    # Check process is alive
                    if _subproc.poll() is not None:
                        self.mLog("Info", "OEDACLI Process suddenly stopped")
                        raise ExacloudRuntimeError(0x0EDA, 0x0EDA, _errMsg)

                # Send the cmd
                if _startDebug and _cmdIdx == _lastCmdIdx:

                    self.__useJdb = False

                    print("#"*50)
                    print("*** Lets start debuggin with JDB ***")
                    print("oedacli_commands file: {}".format(_outfile))
                    print("oedacli_path: {}".format(self.mGetOedacliPath()))
                    print("last_affected cmd : {}".format(_affectedCmd))
                    print("#"*50)

                    print("#"*50)
                    print(" *** Recommended instructions for JDB ***")
                    print("1.- Go to ECRA folder and use the JDB of ECRA `JDB=<ECRA_FOLDER>/jdk_home/bin/jdb`")
                    print("2.- Download OEDA source code and go to that folder `cd oeda/src/`")
                    print("3.- Start JDB in current folder `$JDB -attach localhost:8008 -sourcepath $PWD`")
                    print("4.- Do a breakpoint in the line that process oedacli `stop in oracle.onecommand.cli.oedacli.processLine`")
                    print("5.- Continue with the execution and wait of the breakpoint to hit`")
                    print("#"*50)

                # Execute callbacks before execute command
                for _callback in self.mGetCallbacks():
                    if _callback["moment"] == "BEFORE":
                        _callback["fx"](_cmd, _callback["args"])

                # Execute command
                self.mLog("Info", "Trying command: {0}".format(_cmd))

                _cmdAddLine = "{0}\n".format(_cmd)

                _outfileFd1.write(_cmdAddLine)
                _outfileFd1.flush()

                _subproc.stdin.write(_cmdAddLine.encode('utf-8'))
                _subproc.stdin.flush()

                _count += 1

                # Wait command to finnish and get output
                _cmdFinnish = False
                _out = ""

                while not _cmdFinnish:

                    with open(_outfile, "r") as _f:

                        _logContent = _f.read()
                        _logTrimmed = _logContent[len(_lastOedacliOutput):].strip()

                        if _logContent.count("oedacli>") == _count:
                            _cmdFinnish = True
                            _lastOedacliOutput = _logContent
                            _out = _logTrimmed.replace("oedacli>", "").strip()

                    # Check process is alive
                    if _subproc.poll() is not None:
                        self.mLog("Info", "OEDACLI Process suddenly stopped")
                        raise ExacloudRuntimeError(0x0EDA, 0x0EDA, _errMsg)

                self.mLog("Info", "Stdout: {0}".format(_out))

                # Save current state of the XML
                if self.__useJdb:

                    if "MERGE" in _cmd or "LOAD FILE" in _cmd:

                        _cmd = 'SAVE FILE NAME={0}/debug{1}.xml'.format(self.mGetLogDir(), _cmdIdx)
                        _cmdAddLine = "{0}\n".format(_cmd)

                        _outfileFd1.write(_cmdAddLine)
                        _outfileFd1.flush()

                        _subproc.stdin.write(_cmdAddLine.encode('utf-8'))
                        _subproc.stdin.flush()

                        _count += 1

                # Fetch for errors
                # There are library errors thrown sometimes by oedacli causing this to fail even though it
                # is not a real failure

                _toRemove = get_gcontext().mGetConfigOptions()["oedacli_ignorable_messages"]

                _sanitized = _out.lower().split("\n")
                for _regex in _toRemove:
                    _sanitized = [re.sub(_regex, "", x) for x in _sanitized]
                _sanitized = "\n".join(_sanitized)

                if "fail" in _sanitized or "error:" in _sanitized:

                    _oedacliLog = self.mGetOedacliLogLines()[_lastLineLogOedacliIdx:]

                    self.mLog("Warn", "*"*80)
                    self.mLog("Warn", "*** Dumping OEDACLI log ***")
                    self.mLog("Warn", "*"*80)
                    self.mLog("Warn", "".join(_oedacliLog))

                    if self.__useJdb:

                        self.mLog("Warn", _errMsg)

                        if not _startDebug:

                            # Save state on variables
                            _startDebug = True
                            _lastCmdIdx = _cmdIdx
                            _cmdIdx = _cmdIdx -3
                            _affectedCmd = self.mGetOedacliScript()[_cmdIdx+1]

                    else:

                        raise ExacloudRuntimeError(0x0EDA, 0x0EDA, _errMsg)

                _lastLineLogOedacliIdx = len(self.mGetOedacliLogLines())
                _cmdIdx += 1

                # Execute callbacks after execute command
                if "fail" not in _sanitized and "error:" not in _sanitized:
                    for _callback in self.mGetCallbacks():
                        if _callback["moment"] == "AFTER":
                            _callback["fx"](_cmd, _callback["args"])

        finally:

            _outfileFd1.close()
            _subproc.terminate()

        _scriptOut = ""
        with open(_outfile, "r") as _f:
            _scriptOut = _f.read().strip()

        return _scriptOut

# end of file
