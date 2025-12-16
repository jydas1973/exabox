#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/exatest.py /main/37 2025/12/03 06:22:50 aararora Exp $
#
# exatest.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      exatest.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aararora    12/02/25 - Bug 38715125: Fix coverage issue when running with
#                           --coverage option
#    ririgoye    11/13/25 - Bug 38606501 - Fix coverage issue
#    abflores    02/27/25 - Fix running duplcated files when using --txn and
#                           --r
#    gparada     06/22/23 - 37032724 When code is executed under multiprocess,
#                           the subprocess does NOT accept matching nor mockMode
#                           adding a particular environment variable will help.
#    gvalderr    08/21/24 - Enh 36958472 - Adding files from other folders to
#                           -pylynt -all option
#    prsshukl    07/15/24 - Bug 36840047 - Increase the timeout for
#                           mExecuteLocal
#    gparada     14/09/23 - 35715235 Add option -vj or --validate-json
#    ririgoye    09/05/23 - Enh 35778810 - EXATEST.PY UNIT TESTS FOR TXN FILES 
#                           NOT WORKING PROPERLY
#    ririgoye    07/31/23 - Bug 35646264 - EXACS:EXACLOUD:EXATEST: EXATEST -C
#                           OPTION MISSING SOME CLEANUPS
#    prsshukl    01/24/23 - Bug 34854512: Enable Pylint for all files except
#                           the unittest files
#    alsepulv    03/15/22 - Bug 33964575: Use FQDN for dbfort
#    aararora    03/14/22 - Add etf path to pylint transaction option
#    ndesanto    09/23/21 - Bug 33392220: Adding code to print output of the 
#                           python installation
#    araghave    09/01/21 - ENH 33182904 - MOVE ALL CONFIGURABLE PARAMETERS
#                           FROM CONSTANTS.PY TO INFRAPATCHING.CONF
#    jserran     08/12/21 - Bug 33216612: Include JSON check to pylint flag
#    jserran     07/01/21 - Enh 32833723: Enforce style for JSON files
#    alsepulv    04/19/21 - Fix double entries on mCalculateFiles()
#    jesandov    02/16/21 - Exatest Python Version
#    jesandov    02/16/21 - Creation
#

import os
import re
import sys
import uuid
import enum
import time
import tempfile
import json
import glob
import shlex
import shutil
import signal
import logging
import argparse
import subprocess as sp
import difflib
import six
import codecs

############
# CONSTATS #
############

class ebExatestRC(enum.Enum):
    GENERAL_ERROR = 1
    INVALID_OPTION = 2
    ENV_ERROR = 3
    PYLINT_ERROR = 4
    UNITTEST_ERROR = 5
    JSON_ERROR = 6

class ebExatestState(enum.Enum):
    PASS = 0
    FAIL = 1
    LOG = 2

class ColoredFormatter(logging.Formatter):

    def __init__(self, msg, use_color = True):
        logging.Formatter.__init__(self, msg)
        self.use_color = use_color

    def format(self, record):

        BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

        #These are the sequences need to get colored ouput
        RESET_SEQ = "\033[0m"
        COLOR_SEQ = "\033[1;%dm"
        BOLD_SEQ = "\033[1m"

        COLORS = {
            'WARNING': YELLOW,
            'INFO': BLUE,
            'DEBUG': MAGENTA,
            'CRITICAL': YELLOW,
            'ERROR': RED,
            "CMD": GREEN
        }

        levelname = record.levelname
        if self.use_color and levelname in COLORS:
            levelname_color = COLOR_SEQ % (30 + COLORS[levelname]) + levelname + RESET_SEQ
            record.levelname = levelname_color
        return logging.Formatter.format(self, record)

class ebExatestLogger():

    CMD_LEVEL = 5

    def __init__(self, aLogLocation):
        self.__logger = None
        self.__logLocation = aLogLocation

    def mGetLog(self):

        if not self.__logger:

            # Add Level for commands
            logging.addLevelName(ebExatestLogger.CMD_LEVEL, "CMD")

            # Create exatest logger
            _logger = logging.getLogger("exatest")

            try:
                os.makedirs(self.__logLocation)
            except OSError:
                pass

            # Add file handler
            _fileLog = os.path.join(self.__logLocation, "exatest.log")
            _fh = logging.FileHandler(_fileLog)
            _formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            _fh.setFormatter(_formatter)
            _logger.addHandler(_fh)

            # Add console handler
            _sh = logging.StreamHandler()
            _formatter = ColoredFormatter('%(levelname)s %(message)s')
            _sh.setFormatter(_formatter)
            _logger.addHandler(_sh)

            self.__logger = _logger

        return self.__logger

class ExatestRuntimeError(Exception):

    def __init__(self, aExatestRc):
        self.message = str(aExatestRc.name)
        self.rc = aExatestRc.value

    def __str__(self):
        return "{0} ({1})".format(self.message, self.rc)

class ebExatestManager:

    ###############
    # CONSTRUCTOR #
    ###############

    def __init__(self):

        self.__exacloudPath = os.path.abspath(__file__)
        self.__exacloudPath = self.__exacloudPath[0: self.__exacloudPath.rfind("exacloud")+8]
        self.__ecsPath = self.__exacloudPath[0: self.__exacloudPath.rfind("exacloud")-1]
        os.chdir(self.__exacloudPath)

        self.__uuid = str(uuid.uuid4())
        self.__workdir = os.path.join(self.mGetExacloudPath(), "log/exatest", self.__uuid)
        self.__resultDir = os.path.join(self.mGetExacloudPath(), "exabox/exatest/test_results")
        self.__exatestCodeDir = os.path.join(self.mGetExacloudPath(), "exabox/exatest")

        self.__configData = None
        self.__reportType = None
        self.__logger = ebExatestLogger(self.__workdir)
        self.__scriptArgs = None

        self.mReadConfig()

    #######################
    # GETTERS AND SETTERS #
    #######################

    def mGetLog(self):
        return self.__logger.mGetLog()

    def mSetLogLevel(self, aValue):
        self.mGetLog().setLevel(aValue)

    def mGetReportType(self):
        return self.__reportType

    def mSetReportType(self, aValue):
        self.__reportType = aValue

    def mGetUUID(self):
        return self.__uuid

    def mSetUUID(self, aValue):
        self.__uuid = aValue

    def mGetWorkdir(self):
        return self.__workdir

    def mSetWorkdir(self, aValue):
        self.__workdir = aValue

    def mGetExatestCodeDir(self):
        return self.__exatestCodeDir

    def mSetExatestCodeDir(self, aValue):
        self.__exatestCodeDir = aValue

    def mGetResultDir(self):
        return self.__resultDir

    def mSetResultDir(self, aValue):
        self.__resultDir = aValue

    def mGetExacloudPath(self):
        return self.__exacloudPath

    def mSetExacloudPath(self, aExacloudPath):
        self.__exacloudPath = aExacloudPath

    def mGetEcsPath(self):
        return self.__ecsPath

    def mSetEcsPath(self, aEcsPath):
        self.__ecsPath = aEcsPath

    def mGetConfigData(self):
        return self.__configData
    
    def mSetConfigData(self, aConfigData):
        self.__configData = aConfigData

    def mGetScriptArgs(self):
        return self.__scriptArgs

    def mSetScriptArgs(self, aValue):
        self.__scriptArgs = aValue

    ####################
    # HELPER FUNCTIONS #
    ####################

    def mExecuteLocal(self, aCmd, aCurrDir=None, aStdIn=sp.PIPE, aStdOut=sp.PIPE, aStdErr=sp.PIPE):

        _args = aCmd
        if isinstance(aCmd, str):
            _args = shlex.split(aCmd)

        # Add timeot hook of 20m
        _args = ["/usr/bin/timeout", "1200"] + _args

        self.mGetLog().log(ebExatestLogger.CMD_LEVEL, 'mExecuteLocal: {0}'.format(_args))

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

        self.mGetLog().log(ebExatestLogger.CMD_LEVEL, 'mExecuteLocal: RC:{0}'.format(_rc))

        return _rc, _stdoutP, _stderrP


    def mReadConfig(self):
        self.mSetConfigData(dict())
        _config_file = os.path.join(self.mGetExacloudPath(), "config/exatest_extra_config.conf")
        if os.path.exists(_config_file):
            with open(_config_file, "r") as _file:
                self.mSetConfigData(json.load(_file))

    def mGetConfig(self, aKey, aDefaultValue):
        _result = ""
        if aKey in self.mGetConfigData():
            _result = self.mGetConfigData()[aKey]
        if _result:
            self.mGetLog().debug("{0}: {1}".format(aKey, _result))
            return _result
        else:
            self.mGetLog().debug("{0}: {1}".format(aKey,aDefaultValue))
            return aDefaultValue


    ###################
    # CLASS FUNCTIONS #
    ###################

    def mGenerateTestResult(self, aType, aTestName, aMsg):

        _ext = "log"
        if aType == ebExatestState.PASS:

            _ext = "suc"
            if self.mGetReportType() not in ["suc", "all"]:
                return

        elif aType == ebExatestState.FAIL:

            _ext = "dif"
            if self.mGetReportType() not in ["dif", "all"]:
                return

        _testFile = "{0}/{1}.{2}".format(self.mGetResultDir(), aTestName, _ext)

        with codecs.open(_testFile, "w", encoding='utf-8') as _f:
            _f.write(aMsg)
            _f.write("\n")

    def mFindFiles(self, aFolder, aRegex):

        _cmd = 'find -wholename "{0}" -exec realpath {{}} \;'.format(aRegex)
        _, _out, _ = self.mExecuteLocal(_cmd, aFolder)

        _files = []
        if _out:
            _files = _out.split("\n")

        return _files

    def mFilterTestFiles(self, aFileList):
        return list(filter(lambda x: re.search("tests_", x), aFileList))

    def mFilterNotTestFiles(self, aFileList):
        return list(filter(lambda x: not re.search("tests_", x), aFileList))

    def mConvertToUT(self, aFileList):
        _unitTestFileList = []
        # Add "exatest" directory and test_prefix to the file path
        # NOTE: If your file is not being tested make sure its' name matches the
        # unit test file after the "tests_" prefix.
        for _file in aFileList:
            # Check if basename is already a unit test, in which case the file
            # should be added to the list without any further processing
            if os.path.basename(_file).startswith("tests_"):
                _unitTestFileList.append(_file)
                continue
            # Find "exabox" position in path and split before and after that dir
            _exaboxIndex = _file.rfind("exabox")
            _pathBeforeIndex = self.mGetExatestCodeDir()
            _pathAfterIndex = _file[_exaboxIndex + len("exabox"):]
            # Once split and once adding the exatest dir, modify filename
            _newPath = _pathBeforeIndex + _pathAfterIndex
            _unitTestFileName = os.path.join(os.path.split(_newPath)[0], "tests_" + os.path.basename(_newPath))
            if os.path.isfile(_unitTestFileName):
                _unitTestFileList.append(_unitTestFileName)
        return _unitTestFileList

    def mCalculateFiles(self, aMode):

        _files = []

        if aMode == "txn":

            # Chec ade state
            if not "ADE_VIEW_ROOT" in os.environ:
                _msg = "ADE_VIEW_ROOT is undefined"
                self.mGenerateTestResult(ebExatestState.FAIL, "fetch_files", _msg)
                raise ExatestRuntimeError(ebExatestRC.INVALID_OPTION)

            _viewRoot = os.environ["ADE_VIEW_ROOT"]

            # Fetch affected files from txn
            _cmd = "ade describetrans -short"
            _, _out, _ = self.mExecuteLocal(_cmd)

            _lines = _out.split("\n")

            for _line in _lines:

                _file = _line.strip()

                _filepath = re.search("ecs/exacloud/(.*py)", _file)
                if _filepath:

                    _file = os.path.join(self.mGetExacloudPath(), _filepath.group(1))

                    if "->" in _file:
                        _file = _file.split("->")[1]

                    if os.path.exists(_file):
                        _files.append(_file.strip())

                # Include etf test framework files for calculation of files involved in a transaction
                _filepath_etf = re.search("ecs/(test/ecs_test_framework)/(.*py)", _file)
                if _filepath_etf:

                    _file = os.path.join(self.mGetEcsPath(), _filepath_etf.group(1), _filepath_etf.group(2))

                    if "->" in _file:
                        _file = _file.split("->")[1]

                    if os.path.exists(_file):
                        _files.append(_file.strip())

        elif aMode == "owner":

            _user = os.getlogin()
            _cmd = """ owner "%') AND branch_name LIKE ('MAIN') AND owner LIKE upper('{0}" """.format(_user)
            _, _o, _ = self.mExecuteLocal(_cmd)

            _ownerStr = _o.replace("\n", "")
            _ownerStr = _ownerStr.replace("\r", "")

            _exp = "([-]+)([\w\d]+.py)(ecs/)([\w\d\/]+)(/ECS)"
            _match = re.search(_exp, _ownerStr)

            while _match:

                _file =  _match.group(4) + "/" + _match.group(2)
                _ownerStr = _ownerStr[0: _match.start()] + _ownerStr[_match.end():]
                _match = re.search(_exp, _ownerStr)

                if _file.startswith("exacloud"):
                    _files.append(_file[9:])

        elif aMode == "all":

            _exabox = os.path.join(self.mGetExacloudPath(), "exabox")
            _files = self.mFindFiles(_exabox, "*py")

            _vcncloud = os.path.join(self.mGetExacloudPath(), "vcncloud")
            _files += self.mFindFiles(_vcncloud, "*py")

            _reimage = os.path.join(self.mGetExacloudPath(), "misc/exadatareimage")
            _files += self.mFindFiles(_reimage, "*py")

        _files = list(set(_files))

        return _files

    def mValidateJSON(self, aFixStyleRequested):

        _files = []
        _files.append('config/dyndep.conf')
        _files.append('config/hc_master_checklist.conf')
        _files.append('config/healthcheck.conf')
        _files.append('config/hcname.conf')
        _files.append('config/exabox.conf')
        _files.append('config/exabox.conf.oradb.template')
        _files.append('config/exabox.conf.template')
        _files.append('config/exabox.conf.overrides')
        _files.append('config/exabox.conf.exclusions')
        _files.append('config/program_arguments.conf')
        _files.append('config/bom.conf')
        _files.append('exabox/managment/config/endpoints.conf')
        _files.append('exabox/managment/config/basic.conf')
        _files.append('exabox/tools/ebXmlGen/default_values.json')
        _files.append('exabox/infrapatching/config/infrapatching.conf')

        _skip_style_files = [
        ]

        _msg = ""
        _error = False

        self.mGetLog().info("*** Validating JSON Syntax and Style ***")

        for _file in _files:

            _abspath = os.path.join(self.mGetExacloudPath(), _file)

            try:
                # Verify file is a valid JSON document
                with open(_abspath) as _fd:
                    _json_obj = json.load(_fd)

                if _file in _skip_style_files:
                    _style_result = "PASS"
                else:
                    # Now check if it has propper style (e.g. sorted members etc)
                    _style_result = self.mValidateJSONStyle(_abspath,
                                                            aFixStyleRequested)

                _msg += "JSON Syntax PASS and Style {}: {}\n".format(_style_result,
                                                                     _abspath)

            except (ValueError, SyntaxWarning) as _e:

                # Syntax error: Raised by json.load()
                if isinstance(_e, ValueError):
                    _msg1 = "JSON Syntax FAIL: {}\n".format(_abspath)
                # Style error: Raised by mValidateJSONStyle()
                else:
                    _msg1 = "JSON Style FAIL: {}\n".format(_abspath)
                    _msg1 += ("Suggestion: Use '--fix-json-style' flag to "
                              "automatically apply style changes\n")

                _error = True
                _msg += _msg1
                _msg += str(_e) + "\n"

                self.mGetLog().error(_msg1.strip())
                self.mGetLog().error(str(_e).strip())

        if _error:
            self.mGenerateTestResult(ebExatestState.FAIL, "json_checks", _msg)
            raise ExatestRuntimeError(ebExatestRC.JSON_ERROR)
        else:
            self.mGenerateTestResult(ebExatestState.PASS, "json_checks", _msg)

    def mRemoveExacloudPycFiles(self):

        _exabox = os.path.join(self.mGetExacloudPath(), "exabox")
        _files = self.mFindFiles(_exabox, "*pyc")
        for _file in _files:
            os.remove(_file)

        _exabox = os.path.join(self.mGetExacloudPath(), "exabox")
        _folders = self.mFindFiles(_exabox, "*__pycache__")
        for _folder in _folders:
            shutil.rmtree(_folder)

    def mCreateWorkdir(self):

        # Exatest extra config
        _extraDestFile = os.path.join(self.mGetExacloudPath(), "config/exatest_extra_config.conf")
        _extraSrcFile = os.path.join(self.mGetExacloudPath(), "exabox/exatest/exatest_extra_config.conf")

        _extraCfg = {}

        if os.path.exists(_extraDestFile):
            with open(_extraDestFile, "r") as _f:
                _extraCfg = json.load(_f)
        else:
            with open(_extraSrcFile, "r") as _f:
                _extraCfg = json.load(_f)

        _extraCfg['exatest']['log_level'] = self.mGetLog().level
        _extraCfg['exatest']['r1'] = self.mGetScriptArgs().r1

        with open(_extraDestFile, "w") as _f:
            _f.write(json.dumps(_extraCfg, indent=4, sort_keys=True))

        # Create Workdir
        self.mExecuteLocal("mkdir -p {0}".format(self.mGetWorkdir()))
        self.mExecuteLocal("rm -rf {0}".format(self.mGetResultDir()))
        self.mExecuteLocal("mkdir -p {0}".format(self.mGetResultDir()))

        self.mGetLog().info("WorkDir: {0}".format(self.mGetWorkdir()))
        self.mGetLog().info("Results: {0}".format(self.mGetResultDir()))


    def mCleanServices(self):

        self.mGetLog().info("Clean Services")

        _cmd = "ps -ax"
        _, _out, _ = self.mExecuteLocal(_cmd)
        _processes = _out.split("\n")

        # Filter process of only in exacloud exatest path
        _processes = list(filter(lambda x: x.find(self.mGetExacloudPath()) != -1, _processes))
        _processes = list(filter(lambda x: x.find("exatest") != -1, _processes))

        # Get the process ID
        _processes = list(map(lambda x: re.split("\s+", x.strip())[0], _processes))
        _processes = list(map(int, _processes))

        # Destroy process
        _ownpid = os.getpid()
        for _process in _processes:
            if _process != _ownpid:
                os.kill(_process, signal.SIGKILL)

        # Remove Addons
        self.mExecuteLocal("rm -rf {0}/opt/".format(self.mGetExacloudPath()))
        self.mExecuteLocal("rm -rf {0}/ecmysql/".format(self.mGetExacloudPath()))
        self.mExecuteLocal("rm -rf {0}/db/mysql/".format(self.mGetExacloudPath()))
        self.mExecuteLocal("rm -rf {0}/config/wallet/".format(self.mGetExacloudPath()))


    def mCleanWorkdir(self):

        self.mGetLog().info("Clean Workdir")

        _folder = os.path.join(self.mGetExacloudPath(), "log/exatest")
        _cmd = "rm -rf {0}".format(_folder)
        self.mExecuteLocal(_cmd)

        _sqlfolder = os.path.join(self.mGetExacloudPath(), "log/mysql")
        _cmd = "rm -rf {0}".format(_sqlfolder)
        self.mExecuteLocal(_cmd)


    def mCheckPythonInstallation(self):

        _pyPath = os.path.join(self.mGetExacloudPath(), 'opt/py3_venv/bin/python')

        _cmd = "{0} --version".format(_pyPath)
        _rc, _out, _ = self.mExecuteLocal(_cmd)

        if _rc == 0:
            return _out
        else:
            return None

    def mInstallPython(self):

        _pyPath = os.path.join(self.mGetExacloudPath(), 'opt/py3_venv/bin/python')

        if not os.path.exists(_pyPath):

            _basecmd = os.path.join(self.mGetExacloudPath(), "bin/py3_venv.sh")

            _cmd = "{0} -addons".format(_basecmd)
            _rc, _out, _err = self.mExecuteLocal(_cmd)

            if _rc != 0:
                self.mGenerateTestResult(ebExatestState.FAIL, "install_python_addons", _err)
                raise ExatestRuntimeError(ebExatestRC.ENV_ERROR)
            else:
                self.mGenerateTestResult(ebExatestState.LOG, "install_python_addons", _out)
                self.mGenerateTestResult(ebExatestState.LOG, "install_python_addons_err", _err)

            _cmd = "{0} -dev_addons".format(_basecmd)
            _rc, _out, _err = self.mExecuteLocal(_cmd)

            if _rc != 0:
                self.mGenerateTestResult(ebExatestState.FAIL, "install_python_dev_addons", _err)
                raise ExatestRuntimeError(ebExatestRC.ENV_ERROR)
            else:
                self.mGenerateTestResult(ebExatestState.LOG, "install_python_dev_addons", _out)
                self.mGenerateTestResult(ebExatestState.LOG, "install_python_dev_addons_err", _err)

            _pythonVersion = self.mCheckPythonInstallation()
            self.mGetLog().debug("Python Version Installed: {0}".format(_pythonVersion))

        if not os.path.exists(_pyPath):
            self.mGenerateTestResult(ebExatestState.FAIL, "install_python", "Python not found")
            raise ExatestRuntimeError(ebExatestRC.ENV_ERROR)

        _pythonVersion = self.mCheckPythonInstallation()
        self.mGenerateTestResult(ebExatestState.PASS, "installed_python", _pythonVersion)

    def mRunMultiple(self, aFileList, aMethod, aTag, aRc, aArgs={}):

        _error = False
        _msg = ""

        for _file in aFileList:

            _suc = aMethod(_file, aArgs)

            if not _suc:
                _error = True
                _msg += "{0} FAIL {1}\n".format(aTag, _file)

            else:
                _msg += "{0} PASS {1}\n".format(aTag, _file)

        if _error:
            self.mGenerateTestResult(ebExatestState.FAIL, aTag, _msg)
            raise ExatestRuntimeError(aRc)

        else:
            self.mGenerateTestResult(ebExatestState.PASS, aTag, _msg)

    def mRunPylint(self, aFileList):

        self.mGetLog().info("*** Running Pylint ***")

        self.mRunMultiple(aFileList, self.mRunPylintOne, "Pylint", ebExatestRC.PYLINT_ERROR)

    def mRunPylintOne(self, aFile, aExtraArgs={}):

        _python = os.path.join(self.mGetExacloudPath(), 'bin/python')
        _pylint = os.path.join(self.mGetExacloudPath(), 'opt/py3_venv/bin/pylint')

        # Execute Pylint
        self.mGetLog().info("Check File {0}".format(aFile))
        _testfile = re.sub("[^A-Za-z0-9_-]", "_", aFile)
        _testfile = "pylint_{0}".format(_testfile)

        _cmd = "{0} {1} -j 0 -E {2}".format(_python, _pylint, aFile)
        _rc, _out, _err = self.mExecuteLocal(_cmd)

        if _rc == 0:

            self.mGenerateTestResult(ebExatestState.PASS, _testfile, _out)
            return True

        else:

            if _out:
                self.mGetLog().info(_out)

            if _err:
                self.mGetLog().error(_err)

            _total = _out + _err

            self.mGenerateTestResult(ebExatestState.FAIL, _testfile, _total)
            return False

    def mRunUnittest(self, aFileList):
        self.mRunMultiple(aFileList, self.mRunUnittestOne, "Unittest", ebExatestRC.UNITTEST_ERROR)

    def mRunUnittestOne(self, aFile, aExtraArgs={}):

        # Clean Environment
        self.mRemoveExacloudPycFiles()

        # Start testing
        _python = os.path.join(self.mGetExacloudPath(), "bin/python")

        _testfile = aFile
        _testfile = _testfile.replace(self.mGetExatestCodeDir(), "")
        _testfile = re.sub("[^A-Za-z0-9_-]", "_", _testfile)
        _testfile = _testfile.strip("_")
        _testfile = "unittest_{0}".format(_testfile)

        _retries = self.mGetConfig("exatest_retries" ,1)

        _successRun = False
        for _ in range(0, _retries):

            self.mGetLog().info("*"*50)
            self.mGetLog().info("Testing file: {0}".format(aFile))

            _base = _python
            if "base_cmd" in aExtraArgs:
                _base = aExtraArgs["base_cmd"]

            # Prepare command
            _outfile = os.path.join(self.mGetResultDir(), "unittest.log")
            _cmd = "{0} {1} 2>&1 | tee {2}".format(_base, aFile, _outfile)

            self.mGetLog().log(ebExatestLogger.CMD_LEVEL, "mExecuteCmd: {0}".format(_cmd))
            os.system(_cmd)

            # Read and remove temporal file
            _, _out, _ = self.mExecuteLocal("cat {0}".format(_outfile))
            self.mExecuteLocal("rm {0}".format(_outfile))

            _rc = 0
            if "FAILED" in _out:
                _rc = 1

            if _rc == 0:
                _successRun = True
                break

        if _successRun:
            self.mGenerateTestResult(ebExatestState.PASS, _testfile, _out)
            return True

        else:

            self.mGenerateTestResult(ebExatestState.FAIL, _testfile, _out)
            return False

    def mCreateCoverageRC(self, aProperties, aTargetFile):

        with open(aTargetFile, "w") as _f:

            for tag, subjson in aProperties.items():
                _f.write("[{0}]\n".format(tag))

                for subtag, subvalue in subjson.items():

                    if not subvalue:
                        continue

                    if isinstance(subvalue, str) or isinstance(subvalue, six.text_type):
                        _f.write("{0} = {1}\n".format(subtag, subvalue))

                    else:
                        _f.write("{0} = \n".format(subtag))
                        for value in subvalue:
                            _f.write("  {0}\n".format(value))
                        _f.write("\n")

                _f.write("\n")

    def mRunCoverage(self, aFileList):

        # Start testing
        _python = os.path.join(self.mGetExacloudPath(), "bin/python")
        _coverage = os.path.join(self.mGetExacloudPath(), "opt/py3_venv/bin/coverage")

        # Create coveragerc file
        _coveragetpl = os.path.join(self.mGetExacloudPath(), "exabox/exatest/.coveragerc")
        _coveragerc = os.path.join(self.mGetWorkdir(), "coveragerc")
        _coverageCmd = "{0} -m coverage".format(_python)

        # Patch coverage fields
        _coverageJson = {}
        with open(_coveragetpl, "r") as _f:
            _coverageJson = json.load(_f)

        _coverageJson['html']['directory'] = os.path.join(self.mGetResultDir(), "coverage_html")

        if self.mGetScriptArgs().coverage_include_files:
            _coverageJson['run']['include'] = self.mGetScriptArgs().coverage_include_files

        if self.mGetScriptArgs().coverage_omit_files:
            _coverageJson['run']['omit'] = self.mGetScriptArgs().coverage_omit_files

        if self.mGetScriptArgs().coverage_include_owner:

            _files = self.mCalculateFiles(aMode="owner")

            if _files:

                if "include" not in _coverageJson['run']:
                    _coverageJson['run']['include'] = []

                _coverageJson['run']['include'] += _files

        if self.mGetScriptArgs().coverage_include_txn:

            _files = self.mCalculateFiles(aMode="txn")

            if _files:

                if "include" not in _coverageJson['run']:
                    _coverageJson['run']['include'] = []

                _coverageJson['run']['include'] += _files

        # Create coverage rc
        self.mCreateCoverageRC(_coverageJson, _coveragerc)

        # Init coverage
        _cmd = "{0} erase".format(_coverageCmd)
        self.mExecuteLocal(_cmd)

        # Run multiple
        _extra = {}
        _extra["base_cmd"] = "{0} run --rcfile={1}".format(_coverageCmd, _coveragerc)

        self.mRunMultiple(aFileList, self.mRunUnittestOne, "Coverage", ebExatestRC.UNITTEST_ERROR, _extra)

        # Combine coverage
        _cmd = "{0} combine".format(_coverageCmd)
        self.mExecuteLocal(_cmd)

        self.mGetLog().info("*** Generating Coverage HTML Report ***")

        # Generate Report
        _cmd = "{0} report --rcfile={1} --include=*/exabox/*".format(_coverageCmd, _coveragerc)
        _, _out, _ = self.mExecuteLocal(_cmd)
        self.mGetLog().debug(_out)
        self.mGenerateTestResult(ebExatestState.PASS, "coverage_txt", _out)

        _cmd = "{0} html --rcfile={1} --include=*/exabox/*".format(_coverageCmd, _coveragerc)
        self.mExecuteLocal(_cmd)

        self.mGetLog().debug("*** To coverage result execute ***")
        self.mGetLog().debug("(cd {0}/coverage_html; python -m SimpleHTTPServer 8000)".format(self.mGetResultDir()))


    def mCalculateAdeCoverage(self, aAdeFiles):

        self.mGetLog().info("****** Running ADE Coverage ********")

        _execLines = 0
        _totalLines = 0

        for _file in aAdeFiles:

            if re.search("tests_.*", _file):
                continue

            self.mGetLog().info("* Analizing file: {0}".format(_file))
            self.mGetLog().debug("")

            _, _o, _ = self.mExecuteLocal("ade diff {0} -label".format(_file))

            _affectedLines = re.findall("\n[0-9,]{1,}[ac]{0,1}([0-9,]{1,})", _o)

            # New created files
            if os.path.exists(_file) and not _affectedLines:

                with open(_file, "r") as _f:
                    _linesInNewFile = _f.readlines()
                    _affectedLines = ["1," + str(len(_linesInNewFile))]

            # Expand lines
            _lineList = []
            for _lines in _affectedLines:

                if _lines:
                    if "," in _lines:
                        _lineS = _lines.split(",")
                        _lineList += range(int(_lineS[0]), int(_lineS[1])+1)
                    else:
                        _lineList.append(int(_lines))

            # Fetch if the affected lines was executed
            _fileS = os.path.basename(_file).replace(".", "_")
            _fileGlob = glob.glob("{0}/coverage_html/*{1}*".format(self.mGetResultDir(), _fileS))
            _coverageResult = ""

            if _fileGlob:

                with open(_fileGlob[0], "r") as _f:
                    _coverageResult = _f.read()

            # Fetch all the HTML tags
            _html = re.findall("\<p id=\"t([0-9]{1,})\" class=\"(.*?)\"\>(.*?)\</p\>", _coverageResult)

            if not _html:
                self.mGetLog().debug("Not HTML file")
                self.mGetLog().info("ADE Coverage in file: {0}/{1} = {2:.2f}%".format(0, 0, 0))
                continue

            _totalLinesLocal = 0
            _execLinesLocal = 0

            for _htmlTag in _html:

                if int(_htmlTag[0]) in _lineList:

                    _cleanLine = re.sub("<.*?>", "", _htmlTag[2])
                    _cleanLine = re.match("[0-9]{1,}(.*)(&.*){1,}", _cleanLine).group(1)

                    _lineType = "---"
                    if _htmlTag[1] in ["pln", "run"]:
                        _lineType = "RUN"
                        _execLinesLocal += 1

                    _totalLinesLocal += 1

                    self.mGetLog().debug("[{0}] {1} | {2}".format(_lineType, _htmlTag[0].ljust(5, " "), _cleanLine))

            self.mGetLog().debug("")

            _div = 0
            if _totalLinesLocal != 0:
                _div = (_execLinesLocal*100.0 / _totalLinesLocal)

            self.mGetLog().info("ADE Coverage in file: {0}/{1} = {2:.2f}%".format(_execLinesLocal, _totalLinesLocal, _div))

            _execLines += _execLinesLocal
            _totalLines += _totalLinesLocal

        _div = 0
        if _totalLines != 0:
            _div = (_execLines*100.0 / _totalLines)

        self.mGetLog().info("*"*10)
        self.mGetLog().info("ADE Coverage total: {0}/{1} = {2:.2f}%\n".format(_execLines, _totalLines, _div))


    def mRunFortify(self, aFileList):

        _files = " ".join(aFileList)

        # Install Fortify
        self.mGetLog().info("*** Installing fortify")
        _runAsRoot = "/usr/local/packages/aime/install/run_as_root"
        _installPath = os.path.join(self.mGetWorkdir(), "fortify")

        _cmd = "/bin/mkdir -p {0}".format(_installPath)
        self.mExecuteLocal(_cmd)

        _cmd = "{0} '/bin/mount dbfort.us.oracle.com:/scratch/fortify {1}'".format(_runAsRoot, _installPath)
        self.mExecuteLocal(_cmd)

        try:

            # Execute Fortify
            _ffbin = "{0}/sca18.20/bin/sourceanalyzer".format(_installPath)
            _scanFile = "/tmp/{0}.txt".format(self.mGetUUID())

            # Files
            self.mGetLog().info("*** Running fortify add files")
            _cmd = "{0} -b {1} python-path bin/python {2}"
            _cmd = _cmd.format(_ffbin, self.mGetUUID(), _files)
            self.mExecuteLocal(_cmd)

            # Scan
            self.mGetLog().info("*** Running fortify scan")
            _cmd = "{0} -b {1} -scan -f {2}"
            _cmd = _cmd.format(_ffbin, self.mGetUUID(), _scanFile)
            self.mExecuteLocal(_cmd)

            _cmd = "/bin/cat {0}".format(_scanFile)
            _, _out, _ = self.mExecuteLocal(_cmd)

            self.mGetLog().info("Fortify Result")
            self.mGetLog().info("*"*30)
            self.mGetLog().info(_out)
            self.mGetLog().info("*"*30)
            self.mGetLog().info("")

            # Clean
            self.mGetLog().info("*** Running fortify clean")

            _cmd = "{0} -b {1} -clean"
            _cmd = _cmd.format(_ffbin, self.mGetUUID())
            self.mExecuteLocal(_cmd)

            self.mGenerateTestResult(ebExatestState.PASS, "Fortify", _out)

        finally:

            _retries = 3

            while _retries > 0:

                _cmd = "{0} '/bin/umount {1}'".format(_runAsRoot, _installPath)
                _rc, _out, _err = self.mExecuteLocal(_cmd)

                if _rc == 0:
                    break

                _retries -= 1
                time.sleep(1)


    def mRunJSONValidator(self, aFileList, aFixStyleRequested):
        """ 
        For each file, runs mValidateJSONStyle.
        """
        _error = ""
        _msg = ""
        for _file in aFileList:
            try:
                # Verify file is a valid JSON document
                with open(_file) as _fd:
                    _json_obj = json.load(_fd)

                # Now check if it has propper style (e.g. sorted members etc)
                _style_result = self.mValidateJSONStyle(_file,
                                                        aFixStyleRequested)

                _msg += "JSON Syntax PASS and Style {}: {}\n".format(_style_result,
                                                                     _file)

            except (ValueError, SyntaxWarning) as _e:                
                if isinstance(_e, ValueError):
                    _msg1 = "JSON Syntax FAIL: {}\n".format(_file)                
                else:
                    _msg1 = "JSON Style FAIL: {}\n".format(_file)
                    _msg1 += ("Suggestion: Use '--fix-json-style' flag to "
                              "automatically apply style changes\n")

                _error = True
                _msg += _msg1
                _msg += str(_e) + "\n"

                self.mGetLog().error(_msg1.strip())
                self.mGetLog().error(str(_e).strip())    
    
            if _error:                
                self.mGetLog().warning("Error: {} in file: {}".format(_error,_file) )
            else:
                self.mGetLog().info("JSON file: {} is OK.".format(_file))                

    def mValidateJSONStyle(self, aAbsFilePath, aFixStyleRequested):
        """ Validates the style of a JSON file
        :param: aAbsFilePath full name of the json file to validate.
                File must exists and be a valid JSON document.
        :param: aFixStyleRequested Automatically fix the JSON style if True.
        :returns: "PASS" if aAbsFilePath has proper style, "FIXED" if automatic
                  fix was applied.
        SyntaxWarning() is raised if aAbsFilePath has invalid style and no fix
        was requested.
        """
        with open(aAbsFilePath) as _fd:
            _file_content = _fd.read()

        # Create expected JSON style
        _json_object = json.loads(_file_content)
        _expected_style_lines = json.dumps(_json_object,
                                           sort_keys=True,
                                           indent=4,
                                           separators=(',', ': ')).splitlines()

        _existing_file_lines = _file_content.splitlines()

        # Compare existing and expected JSON styles
        _diff_lines = difflib.unified_diff(_existing_file_lines,
                                           _expected_style_lines,
                                           fromfile='<existing style>{}'.format(aAbsFilePath),
                                           tofile='<expected style>{}'.format(aAbsFilePath),
                                           lineterm='')

        _diff_output = "\n".join(_diff_lines)
        if _diff_output:
            if not aFixStyleRequested:
                _file_name = os.path.basename(aAbsFilePath)
                with tempfile.NamedTemporaryFile(dir=self.mGetResultDir(),
                                                 prefix=_file_name+"_",
                                                 suffix=".dif",
                                                 delete=False) as fd:
                    fd.write(_diff_output)
                raise SyntaxWarning("JSON Style diff can be found at {}".format(fd.name))

            # Fix JSON style
            self.mFixJSONStyle(aAbsFilePath)
            self.mGetLog().info("JSON Style FIXED for {}".format(aAbsFilePath))
            return "FIXED"

        return "PASS"

    def mFixJSONStyle(self, aAbsFilePath):
        """ Applies recommended style to a JSON file
        :param: aAbsFilePath full name of the json file to fix.
        """
        with open(aAbsFilePath) as _fd:
            _json_obj = json.load(_fd)

        with open(aAbsFilePath, "w") as _fd:
            json.dump(_json_obj, fp=_fd,
                      sort_keys=True,
                      indent=4,
                      separators=(',', ': '))


class ebExatestScript:

    def __init__(self):

        self.__start = time.time()
        self.__manager = ebExatestManager()
        self.__scriptArgs = None
        self.__parser = None

    def mGetLog(self):
        return self.mGetManager().mGetLog()

    def mGetManager(self):
        return self.__manager

    def mSetManager(self, aValue):
        self.__manager = aValue

    def mGetScriptArgs(self):
        return self.__args
    
    def mSetScriptArgs(self, aArgs):
        self.__args = aArgs

    def mGetParser(self):
        return self.__parser

    def mSetParser(self, aValue):
        self.__parser = aValue
    
    def mArgsParse(self):

        _parser = argparse.ArgumentParser(description="Exatest: Exacloud Test Framework")

        _g1 = _parser.add_argument_group("Environment Opetions")
        _g1.add_argument(
            "-c", "--clean", dest="clean",
            action="store_true", help="Clean the test results and workdir"
        )

        _g2 = _parser.add_argument_group("Test Options")
        _g2.add_argument(
            '-r', '--run', dest='run',
            action="store_true", help='Run exacloud tests.'
        )
        _g2.add_argument(
            '-p', '-s', '--pylint', '--srg', dest='srg',
            action="store_true", help='Pylint + JSON Syntax'
        )
        _g2.add_argument(
            '-y', '--fortify', dest='fortify',
            action="store_true", help='Run Fortify test.'
        )
        _g2.add_argument(
            '-cv', '--coverage', dest='coverage',
            action="store_true", help='Run exacloud coverage.'
        )
        _g2.add_argument(
            '-acv', '--ade-coverage', dest='ade_coverage',
            action="store_true", help='Compare coverage with ade diff'
        )
        _g2.add_argument(
            '-vj', '--validate-json', dest='validate_json',
            action="store_true", help='Validate a particular given json. '
                                      'Must be used with --files'
        )
        _g2.add_argument(
            '--fix-json-style', dest='fix_json_style',
            action="store_true", help=('Automatically apply style suggestions to JSON files. '
                                       'Must be used along with --srg flag')
        )

        _g3 = _parser.add_argument_group("Affected Files Options")
        _g3.add_argument(
            '-ow', '--owner', dest='owner',
            action='store_true', help='Run test on current user ownership files.'
        )
        _g3.add_argument(
            '-t', '--txn', dest='txn',
            action='store_true', help='Run test on transaction files.'
        )
        _g3.add_argument(
            '-a', '--all', dest='all_py', action='store_true',
            help='-r: excecute all exacloud test. -p, -s, -y: Run on all exacloud files.'
        )
        _g3.add_argument(
            '-f', '--files', dest='files',
            nargs='+', help='-r: Unittest files. -p, -s, -y: Files to be tested.'
        )

        _g5 = _parser.add_argument_group("Coverage RC Options")
        _g5.add_argument(
            "-cvof", "--coverage-omit-files", dest="coverage_omit_files",
            nargs="+",
            help="Coverage omit entries"
        )
        _g5.add_argument(
            "-cvif", "--coverage-include", dest="coverage_include_files",
            nargs="+",
            help="Coverage include entries"
        )
        _g5.add_argument(
            "-cvit", "--coverage-include-txn", dest="coverage_include_txn",
            action="store_true", help="Include only txn files"
        )
        _g5.add_argument(
            "-cvio", "--coverage-include-owner", dest="coverage_include_owner",
            action="store_true", help="Include current user exacloud owner files"
        )

        _g4 = _parser.add_argument_group("Misc Operations")
        _g4.add_argument(
            "-r1", "--r1", dest="r1", action="store_true", help="Run on R1 environments"
        )
        _g4.add_argument(
            "-v", "--log-level", dest="log_level",
            choices=["CRITICAL","ERROR","WARNING","INFO","DEBUG","CMD"],
            default="INFO",
            help="Log level for the logger, see: https://docs.python.org/3/library/logging.html#levels"
        )
        _g4.add_argument(
            "-rp", "--report", dest="report",
            choices=["suc", "dif", "all"], default="all",
            help="Report type after running test"
        )

        _args = _parser.parse_args()
        self.mSetScriptArgs(_args)
        self.mSetParser(_parser)
        self.mGetManager().mSetScriptArgs(_args)

    def mValidateR1(self):

        if self.mGetScriptArgs().r1:

            self.mGetLog().warning("This option will affect Exacloud DB and Exacloud Agent")
            opt = six.moves.input("Do you want to continue? [y/n] ")

            if opt == "y":
                self.mGetLog().info("R1 user validation OK")
                return

            else:
                self.mGetLog().info("R1 user validation FAIL")
                sys.exit(0)

    def mValidateAdeView(self):

        if self.mGetScriptArgs().r1:
            return

        if not "ADE_VIEW_ROOT" in os.environ:

            def mPrintBanner(aMsg, aSize):

                if len(aMsg) > 0:

                    _diffence = ((aSize - len(aMsg))/2)-1

                    self.mGetLog().warning("*", end="")
                    self.mGetLog().warning(" "*_diffence, end="")
                    self.mGetLog().warning(aMsg, end="")
                    self.mGetLog().warning(" "*_diffence, end="")
                    self.mGetLog().warning("*")

                else:
                    self.mGetLog().warning("*"*aSize)

            mPrintBanner("", 60)
            mPrintBanner("ADE_VIEW_ROOT is undefined", 60)
            mPrintBanner("Script exatest.py only works on dev environments", 60)
            mPrintBanner("", 60)

            sys.exit(0)


    def mExecute(self):
        # Set an environment variable to indicate test
        os.environ['IS_EXACLOUD_TEST'] = '1'

        _rc = 0

        try:

            _optionSelected = False

            if self.mGetScriptArgs().log_level:
                self.mGetManager().mSetLogLevel(self.mGetScriptArgs().log_level)

            # Report type
            if self.mGetScriptArgs().report:
                self.mGetManager().mSetReportType(self.mGetScriptArgs().report)

            # Clean Workdir
            if self.mGetScriptArgs().clean:
                self.mValidateR1()
                self.mValidateAdeView()
                self.mGetManager().mCleanWorkdir()
                self.mGetManager().mCleanServices()
                return

            # Do Installations
            self.mGetManager().mCreateWorkdir()
            self.mGetManager().mInstallPython()

            # Calculate files
            _files = []

            if self.mGetScriptArgs().files:

                _absfiles = []

                for _file in self.mGetScriptArgs().files:

                    _exabox = os.path.join(self.mGetManager().mGetExacloudPath(), "exabox")
                    _regex = "*{0}*".format(_file)
                    _regex = _regex.replace("**", "*")

                    _fetched = self.mGetManager().mFindFiles(_exabox, _regex)

                    if _fetched:
                        for _f in _fetched:
                            _absfiles.append(_f)

                    else:
                        _absfiles.append(_file)

                _files += _absfiles

            if self.mGetScriptArgs().owner:
                _files += self.mGetManager().mCalculateFiles(aMode="owner")

            if self.mGetScriptArgs().txn:
                _files += self.mGetManager().mCalculateFiles(aMode="txn")

            if self.mGetScriptArgs().all_py:
                _files += self.mGetManager().mCalculateFiles(aMode="all")

            _files = list(filter(lambda x: re.match("^.*\.(py|json)$", x), _files))
            _files = list(set(_files))

            if not _files and not _optionSelected:
                self.mGetLog().warning("Not files found to process")
                raise ExatestRuntimeError(ebExatestRC.INVALID_OPTION)

            # Calculate mode

            if self.mGetScriptArgs().srg:
                _optionSelected = True
                self.mValidateAdeView()
                _filesNotTest = self.mGetManager().mFilterNotTestFiles(_files)
                self.mGetManager().mRunPylint(_filesNotTest)
                self.mGetManager().mValidateJSON(self.mGetScriptArgs().fix_json_style)

            if self.mGetScriptArgs().fortify:
                _optionSelected = True
                self.mValidateAdeView()
                self.mGetManager().mRunFortify(_files)

            if self.mGetScriptArgs().run:
                _optionSelected = True
                _filesTest = []
                if self.mGetScriptArgs().txn:
                    _filesTest = self.mGetManager().mConvertToUT(_files)

                if not self.mGetScriptArgs().coverage:
                    _filesTest = self.mGetManager().mFilterTestFiles(_files)
                    
                _filesTest = list(set(_filesTest))
                self.mGetManager().mRunUnittest(_filesTest)

            if self.mGetScriptArgs().coverage:
                _optionSelected = True
                _filesTest = self.mGetManager().mFilterTestFiles(_files)
                self.mGetManager().mRunCoverage(_filesTest)

                if self.mGetScriptArgs().ade_coverage:

                    if not self.mGetScriptArgs().txn:
                        self.mGetLog().warning("ade_coverage only works with --txn option")

                    else:
                        _adeFiles = self.mGetManager().mCalculateFiles(aMode="txn")
                        self.mGetManager().mCalculateAdeCoverage(_adeFiles)

            if self.mGetScriptArgs().validate_json:
                _optionSelected = True
                self.mGetManager().mRunJSONValidator(_files, 
                    self.mGetScriptArgs().fix_json_style)
                

            # In case of not option
            if not _optionSelected:
                raise ExatestRuntimeError(ebExatestRC.INVALID_OPTION)

        except ExatestRuntimeError as ere:

            if ere.rc == ebExatestRC.INVALID_OPTION.value:
                self.mGetParser().print_help()

            else:

                self.mGetLog().error("")
                self.mGetLog().error("#"*50)
                self.mGetLog().error("exception ",exc_info=1)
                self.mGetLog().error("#"*50)

                self.mGetLog().error("")
                self.mGetLog().error("*** Please review the dif inside the Result folder ***")
                self.mGetLog().error(self.mGetManager().mGetResultDir())
                self.mGetLog().error("")

            _rc = ere.rc

        except Exception:
            self.mGetLog().error("exception ",exc_info=1)
            _rc = ebExatestRC.GENERAL_ERROR.value

        finally:
            # Remove the environment variable for exatest
            del os.environ['IS_EXACLOUD_TEST']
            self.mGetLog().info("\n*** Exatest Execution time: {0}\n".format(time.time() - self.__start))

        sys.exit(_rc)

if __name__ == '__main__':
    _obj = ebExatestScript()
    _obj.mArgsParse()
    _obj.mExecute()

# end of file
