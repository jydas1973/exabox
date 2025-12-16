"""
$Header:

 Copyright (c) 2017, 2023, Oracle and/or its affiliates.

NAME:
    DBService - Process that handles DBStore DB calls

FUNCTION:
    Prevents issues with forks and DB corruption

NOTE:
    None

History:

    MODIFIED   (MM/DD/YY)
    jesandov    11/06/23 - 35983285: Reduce 80 to 70 characters in socket
                           lenght validation
    alsepulv    03/04/22 - Enh 32852620: Add precheck code for MySQL
    ndesanto    01/13/22 - Moving function to other location.
    ndesanto    12/10/21 - Increase coverage on ndesanto files.
    ndesanto    10/29/21 - Removing debug message when MySQL is stopped using
                           exacloud command.
    ndesanto    12/04/20 - Make MySQL stop call deterministic
    ndesanto    09/23/20 - Added class to validate socket and pid files 
                           locations, /var/run, /var/lib, exacloud path
                           or, as a last resort, /home/oracle
    ndesanto    08/05/20 - Changes to only use sockets to connect to MySQL.
                           Added Typing.
    ndesanto    07/27/20 - Added code to auto clean up stale lock files
    ndesanto    07/16/20 - BUG 31632947 - mkstore & mysql shell fixes
    ndesanto    09/23/19 - Create file
"""

import configparser
import json
import os
import psutil
import shutil
import subprocess as sp
import tempfile
import time
import traceback
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Tuple

from exabox.agent.ExaLock import ExaLock
from exabox.core.Context import get_gcontext
from exabox.network.Local import exaBoxLocal
from exabox.core.Mask import umaskSensitiveData
from exabox.log.LogMgr import ebLogDebug, ebLogInfo, ebLogWarn, ebLogError, \
    ebLogDB
from exabox.tools.AttributeWrapper import wrapStrBytesFunctions
from exabox.config.Config import get_value_from_exabox_config


def _execute_mysql_command(aCmd: str, aIsLog: bool=True) -> bool:
    _process = sp.Popen(aCmd, stdout=sp.PIPE, stderr=sp.PIPE)
    _out: str; _err: str
    _out, _err = wrapStrBytesFunctions(_process).communicate()
    _rc: int = _process.returncode
    if aIsLog:  # pragma: no cover
        ebLogDebug('stdout:\n{}\n'.format(_out))
    if _rc != 0 and aIsLog:  # pragma: no cover
        ebLogError('stderr:\n{}\n'.format(_err))
    return _rc == 0


def is_mysql_running() -> bool:
    _basepath: str = os.path.abspath(os.path.dirname(__file__) + "/../..")
    _init_file_path: str = os.path.join(_basepath, "opt","mysql","init.cfg")
    _mysqladmin_fp : str = os.path.join(_basepath, "opt","mysql","latest",
                                                   "bin","mysqladmin")
    if not os.path.exists(_mysqladmin_fp):  # pragma: no cover
        return False # MySQL not yet installed

    _status_cmd: List[str] = [\
        _mysqladmin_fp,
        "--defaults-file={}".format(_init_file_path),
        "-u", "exacloud",
        "ping"]
    return _execute_mysql_command(_status_cmd, False)


def get_mysql_config(aConfigParam: str, aConfFile: str) -> Optional[dict]:
    _get_value: Optional[dict] = None
    with open(aConfFile, "r") as _f:
        _mysqlConfig: dict = json.load(_f)
        _get_value = dict(_mysqlConfig[aConfigParam])
    return _get_value


def get_mysql_id(aExaboxConf: dict=None) -> int:
    # if dictionary aExaboxConf is present get the id from there
    if aExaboxConf and "mysql_id" in aExaboxConf:
        return aExaboxConf["mysql_id"]

    # If no dictionary was passed then get the agent_port from the exabox.conf
    # retry logic for when exabox.conf is not available the first time
    for i in range(5):
        try:
            _port = get_value_from_exabox_config("agent_port", \
                "config/exabox.conf")
            if _port:
                return int(_port)
        except Exception as e:
            if i > 4:
                ebLogError(f"Exception:\n{e}\n")
                break
            time.sleep(5)

    # If we reach this point we log an error and raise an exception
    _comment = "Unable to obtain the \"agent_port\" from "
    "\"config/exabox.conf\", please verify the file is present and can be "
    "accessed."
    ebLogError(_comment)
    raise ValueError(_comment)


def is_mysql_present(aInitFilePath: Optional[str]=None) -> bool:
    if aInitFilePath == None:
        _basepath: ClassVar[str] = os.path.abspath(\
            os.path.dirname(__file__) + "/../..")
        aInitFilePath = os.path.join(_basepath, "opt/mysql/init.cfg")
    return os.path.isfile(aInitFilePath) and os.path.isfile(\
        "opt/mysql/latest/bin/mysqld")


def __get_value_from_mysql_init(aPropertyName: str, aSectionName: str, \
    aInitCfg: Optional[str]=None) -> Any:
    _out = None
    if aInitCfg == None:  # pragma: no cover
        aInitCfg = os.path.abspath(os.path.dirname(__file__) + \
            "../../opt/mysql/init.cfg")
    if not os.path.isfile(aInitCfg):  # pragma: no cover
        raise FileNotFoundError("Property file {} not found.".format(aInitCfg))
    cfg = configparser.ConfigParser()
    cfg.read(aInitCfg)
    try:
        _out = cfg.get(aSectionName, aPropertyName)
    except Exception as e:  # pragma: no cover
        raise ValueError(\
            "Error retriving value '{}' on section '{}' from config file '{}'".\
                format(aPropertyName, aSectionName, aInitCfg), e)

    return _out


def get_value_from_mysql_init(aPropertyName: str, \
    aSectionName: str, aInitCfg: Optional[str]=None) -> Any:
    return __get_value_from_mysql_init(aPropertyName, aSectionName, aInitCfg)


class ExaMySQL(object):

    def __init__(self, aExaboxConf: Optional[Dict[str, Any]]=None):

        self._basepath: ClassVar[str] = os.path.abspath(\
            os.path.dirname(__file__) + "/../..")
        self.__debug: ClassVar[bool] = False
        if "debug" in aExaboxConf:  # pragma: no cover
            self.__debug = aExaboxConf["debug"]

        # Exacloud agent_port is used to identify sock, lock and pid files 
        # for MySQL, since this value is managed to not conflict in multi-
        # exacloud install, like farm and QA environments
        self._mysql_id: ClassVar[int] = get_mysql_id(aExaboxConf)
        self._mysql_wait_time: ClassVar[int] = 5

        self._exacloud_tmp: ClassVar[str] = self._basepath
        self._dbservice_init_lock: ClassVar[str] = os.path.join(\
            self._exacloud_tmp, "dbservice_init_lock")
        self._dbservice_start_lock: ClassVar[str] = os.path.join(\
            self._exacloud_tmp, "dbservice_start_lock")
        self._mysql_install_lock: ClassVar[str] = os.path.join(\
            self._exacloud_tmp, "mysql_install_lock")
        self._mysql_stop_lock: ClassVar[str] = os.path.join(\
            self._exacloud_tmp, "mysql_stop_lock")
        self._default_init_path: ClassVar[str] = os.path.join(self._basepath, \
            "opt/mysql/init.cfg")
        self._init_file_path: ClassVar[str] = self._default_init_path
        if "mysql_init" in aExaboxConf:
            self._init_file_path = aExaboxConf["mysql_init"]

        self._backup_path: ClassVar[str] = \
            "{}/db/exacloud_mysql_backup.sql".format(self._basepath)
        self._socket_path: ClassVar[str] = \
            CreateValidMysqlSocketDir().mGetValidPath()
        self._mysqld_log: ClassVar[str] = os.path.join(self._basepath, \
            "log/mysql/mysql-error.log")
        self._mysql_installer: ClassVar[str] = os.path.join(self._basepath, \
            "bin/mysql_installer.sh")
        self._install_cmd: ClassVar[str] = [\
            self._mysql_installer, 
            "-install", 
            str(self._mysql_id),
            self._socket_path]
        self._mysqladmin_exec: ClassVar[str] = \
            "{}/opt/mysql/latest/bin/mysqladmin".format(self._basepath)
        self._status_cmd: ClassVar[List[str]] = [\
            self._mysqladmin_exec, 
            "--defaults-file={}".format(self._init_file_path), 
            "ping"]

        # Defaults for installation check
        self._mysqld_sock: ClassVar[str] = "{}/mysql_{}.sock".\
            format(self._socket_path, self._mysql_id)
        self._mysqld_lock: ClassVar[str] = self._mysqld_sock + ".lock"
        self._mysqld_pid: ClassVar[str] = "{}/mysqld_{}.pid".\
            format(self._socket_path, self._mysql_id)

    def __set_variables_from_mysql_init(self):
        self._mysqld_sock = get_value_from_mysql_init(\
            "socket", "mysqld", self._init_file_path)
        self._mysqld_lock = self._mysqld_sock + ".lock"
        self._mysqld_pid = get_value_from_mysql_init(\
            "pid-file", "mysqld", self._init_file_path)
        self._mysqld_log: ClassVar[str] = get_value_from_mysql_init(\
            "log-error", "mysqld", self._init_file_path)
        self._mysqld_user: ClassVar[str] = get_value_from_mysql_init(\
            "user", "mysqld", self._init_file_path)

        self._start_cmd: ClassVar[List[str]] = [\
            "{}/opt/mysql/latest/bin/mysqld".format(self._basepath), 
            "--defaults-file={}".format(self._init_file_path),
            "--daemonize"]
        self._stop_cmd: ClassVar[List[str]] = [\
            self._mysqladmin_exec, 
            "--defaults-file={}".format(self._init_file_path), 
            "-u", 
            self._mysqld_user, 
            "shutdown"]
        self._backup_cmd: ClassVar[List[str]] = [\
            "{}/bin/mysql".format(self._basepath), 
            "--backup", 
            self._backup_path]

    def __execute_command(self, cmd: str) -> Tuple[int, str, str]:
        _result = sp.run(cmd, stdout=sp.PIPE, stderr=sp.PIPE, encoding="utf-8")
        ebLogInfo("ExaMySQL - CMD: {}, RESULT: {}".format(cmd, _result))
        return _result.returncode, _result.stdout, _result.stderr

    def __removeFileIfPresent(self, aPath: str) -> None:
        if os.path.isfile(aPath):
            if self.__debug:  # pragma: no cover
                ebLogDebug('ExaMySQL - Removing {}'.format(aPath))
            os.remove(aPath)

    def __removeLockFiles(self) -> None:
        self.__removeFileIfPresent(self._dbservice_init_lock)
        self.__removeFileIfPresent(self._dbservice_start_lock)
        self.__removeFileIfPresent(self._mysql_install_lock)
        self.__removeFileIfPresent(self._mysql_stop_lock)

        self.__removeFileIfPresent(self._mysqld_sock)
        self.__removeFileIfPresent(self._mysqld_lock)
        self.__removeFileIfPresent(self._mysqld_pid)

    def mInit(self) -> None:
        if not os.path.isfile(self._mysqladmin_exec) or \
            not _execute_mysql_command(self._status_cmd, aIsLog=False):
            self.__removeLockFiles()
            self.mInstallMysql()
            self.__set_variables_from_mysql_init()
            self.mStart()

    def mStart(self) -> None:

        _rc = self.mPrechecks()
        if _rc != 0:
            ebLogError("MySQL failed to start: prechecks failed.")
            return

        with ExaLock(self._dbservice_start_lock):
            if not self.__isMySQLLock():
                self.__set_variables_from_mysql_init()
                ebLogInfo('ExaMySQL - Starting MySQL')
                _rc: int; _out: str; _err: str
                _rc, _out, _err = self.__execute_command(self._start_cmd)
                if _rc == 0 and self.__debug:  # pragma: no cover
                    ebLogDebug('stdout:\n{}\n'.format(_out))
                if _rc != 0:  # pragma: no cover
                    ebLogError('stdout:\n{}\n'.format(_out))
                    ebLogError('stderr:\n{}\n'.format(_err))
                    raise RuntimeError("MySQL failed to start. Please " + \
                        "look at {} for the failure reason.".format(\
                            self._mysqld_log))
                ebLogInfo('ExaMySQL - Thread started')
            else:
                ebLogInfo('ExaMySQL - MySQL is already UP and RUNNING')

    def mInstallMysql(self) -> None:
        if not os.path.isfile(self._mysql_installer):  # pragma: no cover
            ebLogError("ExaMySQL - Missing mysql_installer.sh script")
            raise RuntimeError("Missing mysql_installer.sh script")

        with ExaLock(self._mysql_install_lock):
            if not os.path.exists(self._default_init_path):
                ebLogInfo('ExaMySQL - Installing MySQL')
                _rc: int; _out: str; _err: str
                _rc, _out, _err = self.__execute_command(self._install_cmd)
                if _rc == 0 and self.__debug:  # pragma: no cover
                    ebLogDebug('stdout:\n{}\n'.format(_out))
                if _rc != 0:  # pragma: no cover
                    ebLogError('stdout:\n{}\n'.format(_out))
                    ebLogError('stderr:\n{}\n'.format(_err))
                    raise RuntimeError("Error Installing MySQL. Please " + \
                        "look at {} for the failure reason.".format(\
                            self._mysqld_log))

    # Not used at the moment
    def mMigrateFromSQliteToMySQL(self) -> None:  # pragma: no cover
        _db_requests: str = os.path.join(self._basepath, "db/requests.db")
        _db_requests_bkp: str = os.path.join(self._basepath, \
            "db/requests.db.bkp")
        if os.path.isfile(_db_requests):
            shutil.copyfile(_db_requests, _db_requests_bkp)

            _cmd: List[str] = ["{}/bin/python".format(self._basepath), \
                "{}/exabox/core/DBMigration.py".format(self._basepath)]
            _rc: int; _out: str; _err: str
            _rc, _out, _err = self.__execute_command(_cmd)
            if _rc == 0:
                if self.__debug:  # pragma: no cover
                    ebLogDebug('stdout:\n{}\n'.format(_out))
                # After migration remove requests.db file and leave the backup
                os.remove(_db_requests)
            else:
                ebLogError('stdout:\n{}\n'.format(_out))
                ebLogError('stderr:\n{}\n'.format(_err))

    def mStop(self) -> None:
        ebLogInfo("ExaMySQL - DBService Stop called")
        self.__mMySQLStop()

    def mIsRunning(self, aIsLog: bool = False) -> bool:
        return _execute_mysql_command(self._status_cmd, aIsLog)

    # Not used at the moment
    def mBackup(self) -> None:  # pragma: no cover
        ebLogInfo('ExaMySQL - Creating MySQL data backup')
        with ExaLock(self._mysql_stop_lock):
            self.__set_variables_from_mysql_init()
            _rc: int; _out: str; _err: str
            _rc, _out, _err = self.__execute_command(self._backup_cmd)
            if _rc == 0 and self.__debug:  # pragma: no cover
                ebLogDebug('stdout:\n{}\n'.format(_out))
            if _rc != 0:  # pragma: no cover
                ebLogError('stdout:\n{}\n'.format(_out))
                ebLogError('stderr:\n{}\n'.format(_err))
            else:
                ebLogInfo('ExaMySQL - MySQL backup completed')

    def mPrechecks(self) -> int:
        """ Perform MySQL prechecks. Returns 0 if successful. 1 otherwise """

        # Ensure Socket id is not being used by another instance of Exacloud
        if os.path.isfile(self._mysqld_sock):
            _err_msg = ("There is a MySQL socket already present: "
                       f"{self._mysqld_sock}. Make sure it is not being used "
                        "by another instance of Exacloud")
            ebLogError(_err_msg)
            return 1

        # Ensure Socket file can be created (permission and disk space)
        try:
            _tmpfile_dir = os.path.dirname(self._mysqld_sock)
            with tempfile.NamedTemporaryFile(dir=_tmpfile_dir):
                pass
        except Exception as e:
            _err_msg = (f"Unable to create socket file: {e} "
                        "Ensure this user has the permissions "
                        "necessary to do so")
            ebLogError(_err_msg)
            return 1

        # Expected size of pid, sock, and lock files (~2.5KB)
        _min_free_bytes = 2560
        # Get free disk space in socket path file system
        _fs = os.path.abspath(self._socket_path)
        while not os.path.ismount(_fs):
            _fs = os.path.dirname(_fs)
        _, _, _free_bytes = shutil.disk_usage(_fs)

        if _free_bytes < _min_free_bytes:
            _err_msg = ("There is not enough free disk space to start MySQL. "
                       f"Free up some disk space in {_fs} and retry. "
                       f"Minimum space required: {_min_free_bytes} bytes.")
            ebLogError(_err_msg)
            return 1


        # Ensure there's not a zombie MySQL instance running
        _procs = psutil.process_iter(["pid", "name", "cmdline"])
        _mysql_procs = [p for p in _procs if p.info["name"] == "mysqld"]

        for _process in _mysql_procs:
            _process_id = _process.info["pid"]
            _process_cmd = " ".join(_process.info["cmdline"])

            if "--defaults-file=" in _process_cmd:
                _file = _process_cmd.split("--defaults-file=")[-1].split()[0]

                if _file == self._init_file_path and not os.path.exists(_file):
                    _err_msg = ("There appears to be a MySQL instance "
                               f"(process #{_process_id}) running with an init "
                               f"file that does not exist: {_file}. Kill the "
                                "process and retry. Note: killing the process "
                                "with -9 will not remove the sock, pid, and "
                                "lock files")
                    ebLogError(_err_msg)
                    return 1

        # Ensure configuration files exist and are valid
        _conn_file = os.path.join(self._basepath, "opt", "mysql", "mysql_conn.cfg")
        _env_file = os.path.join(self._basepath, "opt", "mysql", "mysql.env")

        if not os.path.isfile(self._init_file_path):
            _err_msg = ("MySQL file init.cfg does not exist. "
                       f"Create it at {self._init_file_path}")
            ebLogError(_err_msg)
            return 1

        # Ensure init file is properly configured
        if not (get_value_from_mysql_init("pid-file", "mysqld",
                                          self._init_file_path)
                and get_value_from_mysql_init("socket", "client",
                                              self._init_file_path)
                and get_value_from_mysql_init("mysql-id", "exacloud",
                                              self._init_file_path)):
            _err_msg = "MySQL file init.cfg is not properly configured"
            ebLogError(_err_msg)
            return 1

        if not os.path.isfile(_conn_file):
            _err_msg = ("MySQL file mysql_conn.cfg does not exist."
                       f"Create it at {_conn_file}")
            ebLogError(_err_msg)
            return 1

        # Ensure conn config file is properly configured
        _conf_dict = get_mysql_config("exacloud", _conn_file)
        if not (_conf_dict.get("unix_socket") and _conf_dict.get("db")
                and _conf_dict.get("user")):
            _err_msg = "MySQL file mysql_conn.cfg is not properly configured"
            ebLogError(_err_msg)
            return 1

        if not os.path.isfile(_env_file):
            _err_msg = ("mySql file mysql.env does not exist."
                       f"Create it at {_env_file}")
            ebLogError(_err_msg)
            return 1

        ebLogInfo("ExaMySQL - prechecks finished successfully")
        return 0

    def mManualStop(self) -> bool:
        _result = False
        _retry = 0
        try:
            while self.mIsRunning(False):
                self.__mMySQLStop(True)
                # wait for MySQL to stop
                time.sleep(10)
                _retry += 1
                if _retry > 5:
                    break
            else:
                # We verified MySQL stopped, we only arrive here if 
                # self.mIsRunning() returns false
                _result = True
        except:  # pragma: no cover
            pass
        # on break or exception out of the while loop MySQL stop failed
        return _result

    def __mMySQLStop(self, aIsLog: bool = False) -> None:
        ebLogInfo('ExaMySQL - Stopping MySQL')
        with ExaLock(self._mysql_stop_lock):
            self.__set_variables_from_mysql_init()
            _rc: int; _out: str; _err: str
            _rc, _out, _err = self.__execute_command(self._stop_cmd)
            if _rc == 0 and self.__debug:  # pragma: no cover
                ebLogDebug('stdout:\n{}\n'.format(_out))
            if _rc != 0:  # pragma: no cover
                if aIsLog:
                    ebLogError('stdout:\n{}\n'.format(_out))
                    ebLogError('stderr:\n{}\n'.format(_err))
            else:
                ebLogInfo('ExaMySQL - MySQL stopped')

    def __isMySQLLock(self) -> bool:
        _out: bool = False
        if os.path.exists(self._mysqld_lock):
            _out = True
        return _out


class CreateValidMysqlSocketDir(object):
    def __init__(self, aDirectoryName:str="ecmysql"):
        """
        Class used to determines the correct directory to store MySQL lock and 
        pid files.

        The correct directory is determined by the parent directory and access 
        rights, if not present it would be created.

        Arguments
            aDirectoryName(optional):str="ecmysql"
                This value is the name (or the first half) of the directory 
                that will store the lock and pid files.
        """
        self._ecmysql: ClassVar[str] = aDirectoryName
        self._var_run: ClassVar[str] = "/var/run/"
        self._current_path: ClassVar[str] = os.path.abspath(os.path.dirname(\
            __file__) + "/../..")
        self._home: ClassVar[str] = os.path.expanduser("~")

    def mSetSubdirectory(self, aPath) -> None:
        self._ecmysql = aPath

    def mSetVarRun(self, aPath) -> None:
        self._var_run = aPath

    def mSetCurrentPath(self, aPath) -> None:
        self._current_path = aPath

    def mSetHome(self, aPath) -> None:
        self._home = aPath

    def __create_do_not_delete_file(self, aPath:str) -> None:
        if not os.path.exists(aPath):
            with open(aPath, "w") as fd:
                fd.write("This directory and the files contained in it are " + \
                    "required by Exacloud, do not delete it.")

    def __create_valid_mysql_socket_dir(self, aPath:str) -> Tuple[str, int]:
        _out: str = ""
        _found: bool = False
        if os.path.exists(aPath) and os.path.isdir(aPath) \
            and os.access(aPath, os.R_OK | os.W_OK | os.X_OK):
            _out = aPath
            _found = True
        else:
            try:
                os.mkdir(aPath)
                _out = aPath
                _found = True
            except:  # pragma: no cover
                pass
        
        return _out, _found

    def mGetValidPath(self, aSocketPathLimit:int=70) -> None:
        """
        Determines the correct directory to store MySQL lock and pid files.

        The correct directory is determined by the parent directory and access 
        rights, if not present it would be created.

        Arguments
            aSocketPathLimit(optional):int=70
                This numeric value is used to determine if the exacloud path
                can be used to store the lock and pid files.
                The validation will be done at domain folder level
                And there is at least 32 extra characters for the socket
                Current maximum mysql socket size is 107 characters
        """
        _out: str = ""
        _tmp: str = ""
        _path: Path = Path(_out)
        _found = False

        # /var/run/ecmysql_<user id>
        if not _found and os.path.exists(self._var_run) and os.path.isdir(\
            self._var_run) and os.access(self._var_run, \
                os.R_OK | os.W_OK | os.X_OK):
            _tmp = os.path.abspath(os.path.join(self._var_run, "{}_{}".format(\
                self._ecmysql, os.getuid())))
            _out, _found = self.__create_valid_mysql_socket_dir(_tmp)
        
        # /../exacloud/ecmysql
        _tmp = os.path.abspath(os.path.join(self._current_path, self._ecmysql))
        if not _found and len(_tmp) < aSocketPathLimit:  # pragma: no cover
            _out, _found = self.__create_valid_mysql_socket_dir(_tmp)

        # /home/<user name>/ecmysql
        if not _found:  # pragma: no cover
            _tmp = os.path.join(self._home, self._ecmysql)
            _dnd = os.path.join(self._home, self._ecmysql, "DO_NOT_DELETE.txt")
            _out, _found = self.__create_valid_mysql_socket_dir(_tmp)
            if _found:
                self.__create_do_not_delete_file(_dnd)

        if not _found:  # pragma: no cover
            _msg = "Cannot find/create a location to store MySQL " + \
                "socket and pid files. Tried '{}', '{}' and '{}' locations."\
                    .format(self._var_run, self._current_path, self._home)
            ebLogError(_msg)
            raise RuntimeError(_msg)

        return _out
