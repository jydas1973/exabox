"""
$Header:

 Copyright (c) 2020, 2024, Oracle and/or its affiliates.

NAME:
    ExaLock.py - Handles file locks to prevent race conditions within Python process

FUNCTION:
    Handles file locks to prevent race conditions within Python process

NOTE:
    This class can, and is recommended to, be used as part of a with block

History:

    MODIFIED   (MM/DD/YY)
       jesandov    08/21/24 - Bug 36971420: Create dedicated folder
       ndesanto    12/10/21 - Increase coverage on ndesanto files.
       ndesanto    09/29/20 - Modified lock removal logic
       ndesanto    08/10/20 - Added logic to automatically create nested 
                              folders if not already present. Fixed missing
                              file descriptor close call.
       ndesanto    06/20/20 - Creation

"""


import errno
import fcntl
import os
import six
from datetime import datetime

from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace

class ExaLock(object):

    def __init__(self, aPath, aDebug=False):
        self.__debug = aDebug
        self.__fp = None
        self.__start_time = None

        self.__exacloudPath = os.getcwd()
        self.__exacloudPath = self.__exacloudPath[0: self.__exacloudPath.rfind("exacloud")+8]
        self.__dir_path = os.path.join(self.__exacloudPath, "tmp", "exa_locks")
        self.__lock_file = os.path.join(self.__dir_path, os.path.basename(aPath))

    def __create_dir_path(self, aDirPath):  # pragma: no cover
        if six.PY2:
            try:
                os.makedirs(aDirPath)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
        else:
            os.makedirs(aDirPath, exist_ok=True)

    def mCreateLock(self):
        if not os.path.exists(self.__dir_path):  # pragma: no cover
            self.__create_dir_path(self.__dir_path)

        elif not os.path.isdir(self.__dir_path):  # pragma: no cover
            raise RuntimeError("Provided path is not a directory.")

        self.__fp = open(self.__lock_file, 'w')
        self.__fp.flush()
        fcntl.lockf(self.__fp, fcntl.LOCK_EX)
        self.__start_time = datetime.now()
        ebLogTrace("Created lock {} on {} for PID {}".format(\
            self.__lock_file, self.__start_time, os.getpid()))

    def mReleaseLock(self):
        fcntl.lockf(self.__fp, fcntl.LOCK_UN)
        self.__fp.close()

        _time_delta = datetime.now() - self.__start_time
        ebLogTrace("Released lock {} on {} (locked for {}) for PID {}".format(\
            self.__lock_file, datetime.now(), _time_delta, os.getpid()))

    def __enter__(self):
        self.mCreateLock()
        return self

    def __exit__(self, type, value, traceback):
        self.mReleaseLock()
        return False
