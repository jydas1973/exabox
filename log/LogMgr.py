"""
$Header:

 Copyright (c) 2015, 2025, Oracle and/or its affiliates.

NAME:
    LogMgr - Log Manager

FUNCTION:
    Helpers to output and manage logs

NOTE:
    None

LVL Info:
---------
DEBUG	 : Detailed information, of no interest when everything is working well but invaluable when diagnosing problems.
INFO	 : Affirmations that things are working as expected, e.g. "service has started" or "indexing run complete". Often ignored.
WARNING	 : There may be a problem in the near future, and this gives advance warning of it. But the application is able to proceed normally.
ERROR	 : The application has been unable to proceed as expected, due to the problem being logged.
CRITICAL : This is a serious error, and some kind of application meltdown might be imminent.

History:

    MODIFIED   (MM/DD/YY)
       jesandov 11/24/25 - 38677852: Change inspect by traceback in logging format
       jesandov 03/25/24 - 36442769: Improve mSimpleExecuteCmd and mConnect
       ririgoye 07/18/23 - Bug 35113955 - INCORRECT FILE NAME IN EXACLOUD LOGS
                           FOR HEALTHCHECK
       jesandov 11/04/22 - Add abstraction of formatter
       aararora 10/10/22 - Make the default log level accessible outside log
                           manager
       rkhemcha 09/24/22 - 34350709,34350729 - Add logger for bonding mode
                           change and validate
       jesandov 07/19/22 - 34381056 - Init StreamHandler to use stdout
       rkhemcha 05/17/22 - 33928340 - Adding logger for cluster nw
                           reconfiguration
       naps     07/24/21 - move diagnostic messages to trace file.
       alsepulv 02/16/21 - Restore colors in console
       jserran  02/16/21 - Bug 32433186: Fix empty Healcheck log files.
       jejegonz 10/26/20 - Add .trc file for separate verbose from more
                           significant logs
       devbabu  04/06/20 - rotating the logs daily bases and keep last few logs
       ndesanto 10/02/19 - Enh 30374491: EXACC PYTHON 3 MIGRATION BATCH 02
       seha     01/25/18 - Enh 27427661: Add diagnostic module log handler
       dekuckre 11/07/17 - Bug 27156714: Add timezone to Exacloud logs.
       dekuckre 07/03/17 - Bug 26003275: Add new log level - verbose and
                           ebLogVerbose. Also add pid to the entries in the logs.
       mirivier    01/05/2015 - Create file
"""

import logging
import logging.config
import os, sys, time
from six.moves import _thread
import threading
import inspect
import functools
from typing import NamedTuple, Sequence, Optional
from logging.handlers import RotatingFileHandler
from copy import copy
import configparser
import enum
import traceback
import re

gLogMgrInit = False
gLogMgrDirectory = '.'
gLogMainThreadId = None
gLogThreadLocalLog = None
gLogBackupCount = 30
gLogMaxBytes = 100 * 1024 * 1024 #100 mb

MAPPING = {
    'VERBOSE' : 95, # header
    'DEBUG'   : 95, # header
    'INFO'    : 94, # okBlue
    'WARNING' : 93, # yellow
    'ERROR'   : 91, # fail
    'DIAGNOSTIC': 96, # cyan
    'CRITICAL': 101, # white on red bg
}

class ebFormattersEnum(enum.Enum):
    CONSOLE = "console"
    DEFAULT = "default"
    DATABASE = "database"
    WORKER = "worker"


PREFIX = '\033['
SUFFIX = '\033[0m'

class ebDefaultFileFormatter(logging.Formatter):
    pass

class ebFileFormatter(logging.Formatter):

    def format(self, aRecord):

        _exacloudPath = os.path.abspath(__file__)
        _exacloudPath = _exacloudPath[0: _exacloudPath.rfind("exacloud")+8] + "/"

        _stack = traceback.extract_stack()
        _stack = list(filter(lambda x:
            "helper" not in str(x) and \
            "wrapper" not in str(x),
        _stack))

        _currentLogId = 0
        for i in range(0, len(_stack)):
            _frame = _stack[i]
            if "ebLog" in _frame.line:
                _currentLogId = i
                break
        if "mAppendLog" in _frame:
            _currentLogId += 1

        if "mPatchLog" in _frame:
            _currentLogId -= 1

        _frame = _stack[_currentLogId]
        _extra = ""

        if "mSimpleExecuteCmd" in _frame:
            _currentLogId = _currentLogId-8
            _frame = _stack[_currentLogId]
            _extra = "mSimpleExecuteCmd"

        if "mConnect" in _frame:
            _currentLogId = _currentLogId-8
            _frame = _stack[_currentLogId]
            _extra = "mConnect"

        _current = copy(aRecord)

        _current.filename = _frame.filename.replace(_exacloudPath, "")
        _current.pathname = _frame.filename.replace(_exacloudPath, "")
        _current.lineno = _frame.lineno

        _fxMatch = re.search("in (.*)>", str(_frame))
        if _fxMatch:
            _current.funcName = _fxMatch.group(1)
        if _extra:
            _current.funcName = f"{_extra}/{_current.funcName}"

        return super().format(_current)


class ebColorFormatter(ebFileFormatter):
    """
    ColoredFormatter extends class logging.Formatter, from which it inherits most of its behavior.

    It takes a pattern string, which represents the format in which to return
    the string representation of a record when the format() method is called.
    Methods:
        format(record): Returns a string representation of the record with the determined
                        format and console text color properties.
    """

    def format(self, aRecord: logging.LogRecord) -> str:
        colored_record = copy(aRecord)
        levelname = colored_record.levelname
        seq = MAPPING.get(levelname)

        if seq is not None:
            colored_record.levelname = f'{PREFIX}{seq}m{levelname}{SUFFIX}'

        return super().format(colored_record)

def check_is_log_initialized(func):
    def helper(*args, **kwargs):
        if ebLogInitialized():
            return func(*args, **kwargs)
    return helper

def verbose(logger, message, *args, **kws):
    if logger.isEnabledFor(logging.VERBOSE):
        logger._log(logging.VERBOSE, message, args, **kws)

logging.VERBOSE = 9
logging.addLevelName(logging.VERBOSE, "VERBOSE")
logging.Logger.verbose = verbose


def diagnostic(logger, message, *args, **kws):
    if logger.isEnabledFor(logging.DIAGNOSTIC):
        logger._log(logging.DIAGNOSTIC, message, args, **kws)

logging.DIAGNOSTIC = 19
logging.addLevelName(logging.DIAGNOSTIC, "DIAGNOSTIC")
logging.Logger.diagnostic = diagnostic

def ebGetDefaultLoggerName():
    return 'dfltlog'

def ebGetDefaultLogLevel():
    if ebLogInitialized():
        global default_log_level
        if str.isdigit(str(default_log_level)):
            return logging.getLevelName(default_log_level)
        else:
            return default_log_level
    else:
        return "DIAGNOSTIC"

def ebSetLogLvl(logger, lvl):
        
    if lvl == 'VERBOSE':
        logger.setLevel(logging.VERBOSE)
    elif lvl == 'DEBUG':
        logger.setLevel(logging.DEBUG)
    elif lvl == 'INFO':
        logger.setLevel(logging.INFO)
    elif lvl == 'WARNING':
        logger.setLevel(logging.WARNING)
    elif lvl == 'ERROR':
        logger.setLevel(logging.ERROR)
    elif lvl == 'CRITICAL':
        logger.setLevel(logging.CRITICAL)
    elif lvl == 'DIAGNOSTIC':
        logger.setLevel(logging.DIAGNOSTIC)

# xxx/MR: Redefined outside Core to avoid circular dependencies with Context & Core w/ Logging
# TODO: Fix this eventually - low priority
def ebExit(aExitCode, aMsg=None):

    if aMsg:
        print('* EXIT *', aMsg)
    sys.exit(aExitCode)

def ebThreadLocalLog():
    global gLogThreadLocalLog
    return gLogThreadLocalLog

def ebLogInitialized():
    global gLogMgrInit
    return gLogMgrInit

def ebLogDaemonize():
    pass

class DestinationHandler(NamedTuple):
    """ Opaque Class """
    trcHandler: logging.Handler
    logHandler: logging.Handler
    errHandler: logging.Handler

@check_is_log_initialized
def ebLogAddDestinationToLoggers(aLoggerNames : Sequence[str],
                     aPathToHandlerFileWithoutExtension : str,
                     aFormatter: enum) -> DestinationHandler:
    """ 
        Set 3 log files (err/log/trc) with different logging level for each 
        Logger passed. This will permit errors and critical messages  will 
        easily spotted in a separatted file.
        aLoggerNames: Sequence of the logger names in which the log files will be set.
        aPathToHandlerFileWithoutExtension: path of the destination of the log files.
                                            It contains the name of the file, but with 
                                            no extension.
        aFormatter: enum of the formatter to use defined in the config/logging.conf file
    """

    _log_file = os.path.abspath(f"{aPathToHandlerFileWithoutExtension}.log")
    _err_file = os.path.abspath(f"{aPathToHandlerFileWithoutExtension}.err")
    _trc_file = os.path.abspath(f"{aPathToHandlerFileWithoutExtension}.trc")
    os.makedirs(os.path.dirname(_log_file), exist_ok=True)

    _log_handler = RotatingFileHandler(_log_file,
        maxBytes=gLogMaxBytes, backupCount=gLogBackupCount)
    _err_handler = RotatingFileHandler(_err_file,
        maxBytes=gLogMaxBytes, backupCount=gLogBackupCount)
    _trc_handler = RotatingFileHandler(_trc_file,
        maxBytes=gLogMaxBytes, backupCount=gLogBackupCount)

    _formatter_inf = ebCreateFormatter(aFormatter.value)
    _formatter_trc = ebCreateFormatter(f"{aFormatter.value}_debug")

    _log_handler.setFormatter(_formatter_inf)
    _err_handler.setFormatter(_formatter_trc)
    _trc_handler.setFormatter(_formatter_trc)

    # Set Handler Level
    _log_handler.setLevel(logging.INFO)
    _err_handler.setLevel(logging.ERROR)
    _trc_handler.setLevel(logging.VERBOSE)        

    for _logger_name in aLoggerNames:
        _logger = logging.getLogger(_logger_name)
        # Add Handlers
        _logger.addHandler(_log_handler)
        _logger.addHandler(_err_handler)
        _logger.addHandler(_trc_handler)

    return DestinationHandler(_trc_handler, _log_handler, _err_handler)

@check_is_log_initialized
def ebLogDeleteLoggerDestination(aLogName: str, aDestinationHandler: DestinationHandler,
    aDeleteLogFiles: bool=False) -> None:
    """
    Deattach Destination logs to specified Logger.
    Arguments:
    aLogName:           Name of the logger which will the destination handler be deattached.
    aDestinationHandler:Destination handler to be removed from logger.
    aDeletionLogFiles:  Removes log files of the destination Handler. Warning: Other loggers/processes 
                        could be using this file for logging. Please avoid deleting log files.
    """
    
    if aDestinationHandler is not None:
        aDestinationHandler.trcHandler.close()
        aDestinationHandler.logHandler.close()
        aDestinationHandler.errHandler.close()
        logging.getLogger(aLogName).removeHandler(aDestinationHandler.trcHandler)
        logging.getLogger(aLogName).removeHandler(aDestinationHandler.logHandler)
        logging.getLogger(aLogName).removeHandler(aDestinationHandler.errHandler)

        if aDeleteLogFiles:
            os.remove(aDestinationHandler.trcHandler.baseFilename)
            os.remove(aDestinationHandler.logHandler.baseFilename)
            os.remove(aDestinationHandler.errHandler.baseFilename)

def ebCreateLogger(aLoggerName: str,
                   aPathToHandlerFileWithoutExtension: str,
                   aFormatter: enum = ebFormattersEnum.DEFAULT,
                   aLogLevel: Optional[int] = None,
                   aEnableConsole: bool = False,
                   aRemovePreviousHandlers: bool = False
                   ) -> DestinationHandler:
    """
        Sets initial config and handlers for the given aLoggerName logger.
        Params:
            aLoggerName: Name of the logger to use.
            aPathToHandlerFileWithoutExtension: Path + name without extension where log files will be located.
            aFormatter: enum with the name of the formatter to use defined in config/logging.conf
            aLogLevel: Minimum log level permited into logger. 
                       If not specified, log level will not be changed.
                (Permitted values:  logging.NOTSET, logging.VERBOSE,
                                    logging.INFO, logging.WARNING,
                                    logging.ERROR, logging.CRITICAL)
            aEnableConsole: Flag to enable the console output of the logger. 
            aRemovePreviousHandlers: Flag to delete previous existent Handlers in Logger.
    """

    _logger = logging.getLogger(aLoggerName)
    _logger.propagate = False

    if aRemovePreviousHandlers:
        while _logger.handlers:
            _logger.handlers[0].close()
            _logger.removeHandler(_logger.handlers[0])

    # If console is enabled, set a handler for it. 
    if aEnableConsole:
        _console_handler = logging.StreamHandler(sys.stdout)
        _formatter = ebCreateFormatter(ebFormattersEnum.CONSOLE.value)

        if aLogLevel == logging.DEBUG or aLogLevel == logging.VERBOSE:
            _formatter = ebCreateFormatter(f"{ebFormattersEnum.CONSOLE.value}_debug")

        _console_handler.setFormatter(_formatter)
        _console_handler.setLevel(logging.VERBOSE)
        _logger.addHandler(_console_handler)

    # Change Logger Level if requested
    if aLogLevel is None:
        aLogLevel = _logger.getEffectiveLevel()
    _logger.setLevel(aLogLevel)

    return ebLogAddDestinationToLoggers([aLoggerName],
                                        aPathToHandlerFileWithoutExtension,
                                        aFormatter)


def ebCreateFormatter(aFormatterName):

    _exacloudPath = os.path.abspath(__file__)
    _exacloudPath = _exacloudPath[0: _exacloudPath.rfind("exacloud")+8] + "/"
    _basepath = _exacloudPath

    _confpath = os.path.join(_basepath, 'config', 'logging.conf')
    if not os.path.isfile(_confpath):
        raise ValueError(f"Missing configuration file for logging, {_confpath}")

    _config = configparser.RawConfigParser()
    _config.read(_confpath)

    _loggername = f"formatter_{aFormatterName}"
    if _loggername not in _config.sections():
        raise ValueError(f"Invalid logger name {_loggername}, missing in configuration file")

    _formatter_class = None

    if "class" in _config[_loggername]:
        _formatter_class = getattr(sys.modules[__name__], _config[_loggername]["class"])
    else:
        _formatter_class = logging.Formatter

    if "format" not in _config[_loggername]:
        raise ValueError(f"Missing format field in {_loggername} configuration")

    if "datefmt" not in _config[_loggername]:
        raise ValueError(f"Missing datefmt field in {_loggername} configuration")

    _formatter = _formatter_class(_config[_loggername]["format"], _config[_loggername]["datefmt"])
    return _formatter


def ebLogInit(aContext, aOptions):

    global gLogMgrInit
    global gLogMgrDirectory
    global gLogMainThreadId
    global gLogThreadLocalLog
    global default_log_level

    gLogMgrInit = True
    #Unique ID, even in multiprocess
    gLogMainThreadId = os.getpid() + _thread.get_ident()
    gLogThreadLocalLog = threading.local()

    _coptions = aContext.mGetConfigOptions()
    _basepath = aContext.mGetBasePath()

    '''
    Lets have DIAGNOSTIC as default level. This is just 1 level below INFO. This will not include debug/verbose.
    All diagnostic logs will go only into .trc file.
    This will make .log file less nosiy.
    Especially during provisioning error scenarios, .log file will look clean and last bits in the file will only have messages about actual failure.
    '''
    default_log_level = logging.DIAGNOSTIC
    if _coptions:
        if 'log_dir' in list(_coptions.keys()):
            if os.path.isabs(_coptions['log_dir']):
                gLogMgrDirectory = _coptions['log_dir']
            else:
                gLogMgrDirectory = os.path.join(_basepath, _coptions['log_dir'])
        if 'log_level' in list(_coptions.keys()):
            default_log_level = _coptions['log_level']

    if aOptions.log_level:
        default_log_level = aOptions.log_level
    if aOptions.debug:
        default_log_level = logging.DEBUG

    # By Default the log is sent to the console (may be changed in the future)
    # Use the option -dc to disable this default behavior
    enable_console = not aOptions.dis_console

    # Load Logging configuration file if presents
    _confpath = os.path.join(_basepath, 'config', 'logging.conf')
    chkfile = os.path.isfile(_confpath)
    if chkfile:
        logging.config.fileConfig(_confpath)

    # This unfortunately triggers also the logging from other python module using logging
    # logging.basicConfig(level=logging.INFO)

    # File Handler Log
    if aOptions.proxy:
        dflt_log_file = 'exaproxy'
    else:
        dflt_log_file = 'exacloud'
    
    ebCreateLogger(ebGetDefaultLoggerName(), os.path.join(gLogMgrDirectory, dflt_log_file),
                   ebFormattersEnum.DEFAULT, default_log_level, aEnableConsole=enable_console)
    
    ebCreateLogger('agent', os.path.join(gLogMgrDirectory, 'agent'),
                   ebFormattersEnum.DEFAULT, default_log_level, aEnableConsole=enable_console)

    ebCreateLogger('healthcheck', os.path.join(gLogMgrDirectory, 'checkcluster', 'healthcheck'),
                   ebFormattersEnum.DEFAULT, logging.VERBOSE, aEnableConsole=enable_console)
    
    ebCreateLogger('diagnostic', os.path.join(gLogMgrDirectory, 'diagnostic', 'diagnostic'),
                   ebFormattersEnum.DEFAULT, default_log_level, aEnableConsole=enable_console)

    ebCreateLogger('nw_reconfig', os.path.join(gLogMgrDirectory, 'nw_reconfig', 'nw_reconfig'),
                   ebFormattersEnum.DEFAULT, logging.VERBOSE, aEnableConsole=enable_console)

    ebCreateLogger('nw_bonding', os.path.join(gLogMgrDirectory, 'nw_bonding', 'nw_bonding'),
                   ebFormattersEnum.DEFAULT, logging.VERBOSE, aEnableConsole=enable_console)

    ebCreateLogger('database', os.path.join(gLogMgrDirectory, 'database'),
                   ebFormattersEnum.DATABASE, default_log_level, aEnableConsole=enable_console)

@check_is_log_initialized
def ebLogSetBMCLogHandler(aLogName, aLogLevel):
    log_name_no_extension, _ = os.path.splitext(aLogName)
    ebCreateLogger('bmcctrl', os.path.join(gLogMgrDirectory, log_name_no_extension),
        ebFormattersEnum.DEFAULT, aLogLevel, aRemovePreviousHandlers=True)

@check_is_log_initialized
def ebLogGetBMCLogger():
    return logging.getLogger('bmcctrl')

@check_is_log_initialized
def ebLogBMCDebug(aString):
    logging.getLogger('bmcctrl').debug(aString)

@check_is_log_initialized
def ebLogBMCWarn(aString):
    logging.getLogger('bmcctrl').warning(aString)

@check_is_log_initialized
def ebLogBMCError(aString):
    logging.getLogger('bmcctrl').error(aString)

@check_is_log_initialized
def ebLogBMCInfo(aString):
    logging.getLogger('bmcctrl').info(aString)

@check_is_log_initialized
def ebLogBMCCritical(aString):
    logging.getLogger('bmcctrl').critical(aString)


@check_is_log_initialized
def ebLogSetHCLogDestination(aLogName: str, aRemoveAllHandlers=False) -> DestinationHandler:
    """ Set Healthcheck log destination path """
    log_name_no_extension, _ = os.path.splitext(aLogName)
    abs_log_name_no_extension = os.path.join(gLogMgrDirectory,'checkcluster', log_name_no_extension)
    abs_log_name_no_extension = os.path.abspath(abs_log_name_no_extension)
    return ebCreateLogger('healthcheck', abs_log_name_no_extension,
                          ebFormattersEnum.DEFAULT, aRemovePreviousHandlers=aRemoveAllHandlers)

@check_is_log_initialized
def ebLogRemoveHCLogDestination(aDestinationHandler: DestinationHandler) -> None:
    ebLogDeleteLoggerDestination('healthcheck',  aDestinationHandler)

@check_is_log_initialized
def ebSetLogDiagLvl(lvl):
    logger = logging.getLogger('diagnostic')
    ebSetLogLvl(logger, lvl)

def ebLogFinalize(aOptions, *aString):
    global gLogMgrInit
    if gLogMgrInit:
        gLogMgrInit = False

@check_is_log_initialized
def ebLogJson(aString):
    print(aString)

@check_is_log_initialized
def ebThreadLogging(aString,aPfx=None):
    if aPfx is None:
        aPfx = ''
    else:
        aPfx = aPfx + ':'
    # Thread Logging is done via ThreadLocal storage
    assert(gLogMainThreadId is not None)
    if gLogMainThreadId != os.getpid() + _thread.get_ident():
        _ebt_local = ebThreadLocalLog()
        # Activated By will contains process type ('agent') if activated
        _processtype = getattr(_ebt_local,'activated_by',None)
        if _processtype is None:
            return False
        _outbuf = getattr(_ebt_local,'output_buffer',None)
        if _outbuf is None:
            # Only done once per thread/process
            _logdir = 'log/workers'
            if not os.path.exists(_logdir):
                try:
                    #except pass as I have seen load 2 threads
                    os.makedirs(_logdir, exist_ok=True)
                except OSError:
                    pass
            _filename = '{}_{}_{}.log'.format(_processtype, os.getpid(), _thread.get_ident())

            _outbuf = open(os.path.join(_logdir,_filename),'a',1)
            _ebt_local.output_buffer = _outbuf
        _format_str = '%Y-%m-%d %H:%M:%S%z'
        _time_str = time.strftime(_format_str, time.localtime())
        aPfx = _time_str + ':' + aPfx
        _outbuf.write(aPfx + str(aString) + '\n')
        return True
    return False

@check_is_log_initialized
def ebLogDB(aType,aString):
    if not aType in ['NFO', 'ERR', 'WRN', 'DBG', 'CRT']:
        ebLogError('Invalid Agent log type: '+aType)
        return

    logger = logging.getLogger('database')
    if aType == 'NFO':
        logger.info(aString)
    if aType == 'ERR':
        logger.error(aString)
    if aType == 'WRN':
        logger.warning(aString)
    if aType == 'DBG':
        logger.debug(aString)
    if aType == 'CRT':
        logger.critical(aString)

@check_is_log_initialized
def ebLogAgent(aType,aString):
    if not aType in ['NFO', 'ERR', 'WRN', 'DBG', 'CRT']:
        ebLogError('Invalid Agent log type: '+aType)
        return

    logger = logging.getLogger('agent')
    if aType == 'NFO':
        logger.info(aString)
    if aType == 'ERR':
        logger.error(aString)
    if aType == 'WRN':
        logger.warning(aString)
    if aType == 'DBG':
        logger.debug(aString)
    if aType == 'CRT':
        logger.critical(aString)

@check_is_log_initialized
def ebLogHealth(aType,aString):
    #if not aType in  ['VERBOSE', 'DEBUG', 'INFO','RECOMMEND', 'WARNING', 'ERROR', 'CRITICAL']:
    #    ebLogError('Invalid Agent log type: '+aType)
    #    return
    logger = logging.getLogger('healthcheck')
    if aType == 'VERBOSE':
        logger.verbose(aString)
    elif aType == 'RECOMMEND' or aType == 'INFO' or aType == 'NFO':
        logger.info(aString)
    elif aType == 'ERROR' or aType == 'ERR':
        logger.error(aString)
    elif aType == 'WARNING' or aType == 'WRN':
        logger.warning(aString)
    elif aType == 'DEBUG' or aType == 'DBG':
        logger.debug(aString)
    elif aType == 'CRITICAL' or aType == 'CRT':
        logger.critical(aString)
    else:
        ebLogError('Invalid log type: '+aType)
        logger.verbose(aString)

@check_is_log_initialized
def ebLog(aModule, aType, aString):
    logger = logging.getLogger(aModule)
    if aType == 'VERBOSE':
        logger.verbose(aString)
    elif aType == 'RECOMMEND' or aType == 'INFO' or aType == 'NFO':
        logger.info(aString)
    elif aType == 'ERROR' or aType == 'ERR':
        logger.error(aString)
    elif aType == 'WARNING' or aType == 'WRN':
        logger.warning(aString)
    elif aType == 'DEBUG' or aType == 'DBG':
        logger.debug(aString)
    elif aType == 'CRITICAL' or aType == 'CRT':
        logger.critical(aString)
    else:
        ebLogError('Invalid log type: '+aType)
        logger.verbose(aString)

@check_is_log_initialized
def ebLogDiag(aType,aString):
    if not aType in ['NFO', 'ERR', 'WRN', 'DBG', 'CRT']:
        ebLogError('Invalid Agent log type: '+aType)
        return

    logger = logging.getLogger('diagnostic')
    if aType == 'NFO':
        logger.info(aString)
    if aType == 'ERR':
        logger.error(aString)
    if aType == 'WRN':
        logger.warning(aString)
    if aType == 'DBG':
        logger.debug(aString)
    if aType == 'CRT':
        logger.critical(aString)

@check_is_log_initialized
def ebLogDebug(aString, aNoNL = None):
    if not ebThreadLogging(aString,'DBG'):
        logger = logging.getLogger(ebGetDefaultLoggerName())
        logger.debug(aString)

@check_is_log_initialized
def ebLogError(aString, aNoNL = None):
    if not ebThreadLogging(aString,'ERR'):
        logger = logging.getLogger(ebGetDefaultLoggerName())
        logger.error(aString)

@check_is_log_initialized
def ebLogInfo(aString, aNoNL = None):
    if not ebThreadLogging(aString,'LOG'):
        logger = logging.getLogger(ebGetDefaultLoggerName())
        logger.info(aString)

@check_is_log_initialized
def ebLogWarn(aString):
    if not ebThreadLogging(aString,'WARN'):
        logger = logging.getLogger(ebGetDefaultLoggerName())
        logger.warning(aString)

@check_is_log_initialized
def ebLogCritical(aString, aAction):
    _banner = ("*"*70+'\n')*3
    if not ebThreadLogging(aString, 'CRIT'):
        logger = logging.getLogger(ebGetDefaultLoggerName())
        _criticalMessage = "\n{0}ERROR: {1}\nACTION: {2}\n{0}".format(_banner, aString, aAction)
        logger.critical(_criticalMessage)

@check_is_log_initialized
def ebLogCrit(aString):
    if not ebThreadLogging(aString, 'CRIT'):
        logger = logging.getLogger(ebGetDefaultLoggerName())
        logger.critical(aString)

@check_is_log_initialized
def ebLogVerbose(aString):
    if not ebThreadLogging(aString, 'VERBOSE'):
        logger = logging.getLogger(ebGetDefaultLoggerName())
        logger.verbose(aString)

@check_is_log_initialized
def ebLogTrace(aString):
    if not ebThreadLogging(aString, 'DIAGNOSTIC'):
        logger = logging.getLogger(ebGetDefaultLoggerName())
        logger.diagnostic(aString)

# Simple helper function to print the results of a Cmd (stdout/stderr)
@check_is_log_initialized
def ebLogCmd(aDesc):
    out = aDesc[1]
    err = aDesc[2]
    out = out.readlines()
    if out:
        for e in out:
            ebLogInfo(e[:-1])
    err = err.readlines()
    if err:
        for e in err:
            ebLogError(e[:-1])

#######################################################################
#
# @stacktrace
#
# 	This decorator is used to print the callstack before calling the
# 	function before which this has been invoked. This is to be used strictly
# 	for debugging purposes only.
#
#	This is helpful if one needs to figure out the code flow above a certain
#	module.
#
# Invocation:
#	@stacktrace
#	def abc (...):
#
#	Here, the stacktrace would print the callstack before making a call to
#	module abc.
#
# History:
#	Sept, 2018	nkattige	Written
#
# Sample Output:
#	Usage -
#	@stacktrace
#	def mExecuteDbInfo()
#
#	For the above usage the output is as shown below:
#
# 2018-09-24 23:47:06+0000 - dfltlog - INFO - 94451 - *** Printing Stacktrace using @stacktrace ***
# File "/scratch/nkattige/ecra_installs/instance1/mw_home/user_projects/domains/exacloud/exabox/log/LogMgr.py", Line 493, in wrapper_stacktrace
# '\t\tstackarr = inspect.stack()\n'
# File "/scratch/nkattige/ecra_installs/instance1/mw_home/user_projects/domains/exacloud/exabox/ovm/cludbaas.py", Line 174, in mClusterDbInfo
# '        _rc = self.mExecuteDbInfo(_options, _dbaasdata, _sourcedb)\n'
# File "/scratch/nkattige/ecra_installs/instance1/mw_home/user_projects/domains/exacloud/exabox/ovm/cludbaas.py", Line 126, in mClusterDbaas
# '            _rc = self.mClusterDbInfo(_options, _dbaasdata)\n'
#
#	[...]
#
# File "/scratch/nkattige/ecra_installs/instance1/mw_home/user_projects/domains/exacloud/opt/lib64/python2.7/runpy.py", Line 174, in _run_module_as_main
# '                     "__main__", fname, loader, pkg_name)\n'
# *** End of Stacktrace ***
#
def stacktrace(func):
    @functools.wraps(func)
    def wrapper_stacktrace(*args, **kwargs):
        stackarr = inspect.stack()
        s = "*** Printing Stacktrace using @stacktrace ***\n"

        for i in range(len(stackarr)):
            line_details = str(stackarr[i][4])
            line_details = line_details.replace("[", "")
            line_details = line_details.replace("]", "")
            s += "File \"" + stackarr[i][1] + "\", Line " + str(stackarr[i][2]) + ", in " + stackarr[i][3] + "\n"
            s +=  line_details + "\n"
        s += "*** End of Stacktrace ***"

        # Print the stacktrace
        ebLogInfo(s)
        return func(*args, **kwargs)
    return wrapper_stacktrace
