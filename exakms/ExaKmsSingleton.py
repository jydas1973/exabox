#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exakms/ExaKmsSingleton.py /main/7 2023/05/23 13:12:59 jesandov Exp $
#
# ExaKmsSingleton.py
#
# Copyright (c) 2021, 2023, Oracle and/or its affiliates.
#
#    NAME
#      ExaKmsSingleton.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    05/05/23 - 35364881 - Update ExaKmsSingleton by the process
#                           and thread id
#    alsepulv    06/08/22 - Bug 34256357: Remove previous fix for bug 33852308
#    alsepulv    04/21/22 - Enh 31861263: Add ExaKmsSIV
#    alsepulv    02/28/22 - Bug 33852308: Create new exakms object every time
#                           to avoid SSL errors with multiprocessing
#    jesandov    04/27/21 - Creation
#

import os
import threading

from exabox.core.Context import get_gcontext
from exabox.log.LogMgr import ebLogError, ebLogDebug, ebLogInfo, ebLogWarn

from exabox.exakms.ExaKms import ExaKms

class ExaKmsSingleton:

    def __init__(self):

        self.__exakms = {}

    def mGetExaKms(self):

        _connkey = f"{threading.get_ident()}-{os.getpid()}"

        if not _connkey in list(self.__exakms.keys()):
            _exakms = self.mCreateExaKms()
            self.__exakms[_connkey] = _exakms

        return self.__exakms[_connkey]

    def mInitExaKmsSIV(self):
        from exabox.exakms.ExaKmsSIV import ExaKmsSIV

        ebLogInfo("Create ExaKms of type: ExaKmsSIV")
        return ExaKmsSIV()

    def mInitExaKmsOCI(self):

        from exabox.exakms.ExaKmsOCI import ExaKmsOCI

        ebLogInfo("Create ExaKms of type: ExaKmsOCI")
        return ExaKmsOCI()

    def mInitExaKmsKeysDB(self):

        from exabox.exakms.ExaKmsKeysDB import ExaKmsKeysDB

        ebLogInfo("Create ExaKms of type: ExaKmsKeysDB")
        return ExaKmsKeysDB()

    def mInitExaKmsFileSystem(self):

        from exabox.exakms.ExaKmsFileSystem import ExaKmsFileSystem

        ebLogInfo("Create ExaKms of type: ExaKmsFileSystem")
        return ExaKmsFileSystem()

    def mCreateExaKms(self):

        _exakmsType = get_gcontext().mCheckConfigOption("exakms_type")

        if _exakmsType == "ExaKmsSIV":
            return self.mInitExaKmsSIV()

        elif _exakmsType == "ExaKmsOCI":
            return self.mInitExaKmsOCI()

        elif _exakmsType == "ExaKmsKeysDB":
            return self.mInitExaKmsKeysDB()

        elif _exakmsType == "ExaKmsFileSystem":
            return self.mInitExaKmsFileSystem()

        else: # auto

            _enableSIV = get_gcontext().mCheckConfigOption('enable_siv', 'True')
            _ociKeyID = get_gcontext().mCheckConfigOption('kms_key_id')
            _ociDpEnd = get_gcontext().mCheckConfigOption('kms_dp_endpoint')
            _ociExacc = get_gcontext().mCheckConfigOption('ociexacc', "True")

            if _enableSIV:
                return self.mInitExaKmsSIV()

            elif (_ociKeyID and _ociDpEnd):
                return self.mInitExaKmsOCI()

            elif _ociExacc:
                return self.mInitExaKmsKeysDB()

            else:
                return self.mInitExaKmsFileSystem()

# end of file
