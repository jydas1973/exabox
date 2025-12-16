#
# $Header: ecs/exacloud/exabox/infrapatching/handlers/loghandler.py /main/4 2024/09/24 06:06:59 araghave Exp $
#
# loghandler.py
#
# Copyright (c) 2020, 2024, Oracle and/or its affiliates.
#
#    NAME
#      loghandler.py - This module contains all the log handling methods used to write information into thread logs.
#
#    DESCRIPTION
#      This module contains all the log handling methods used to write information into thread logs.
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    araghave    09/18/24 - Enh 36971721 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE TARGET HANDLER FILES
#    araghave    06/12/24 - Enh 36522596 - REVIEW PRE-CHECK/PATCHING/ROLLBACK
#                           LOGS AND CLEAN-UP
#    araghave    07/09/21 - BUG 33081173 - Remove older error codes from Infra
#                           patching core files
#    nmallego    08/28/20 - Refactor infra patching code
#    nmallego    08/28/20 - Creation
#

import os, sys
from exabox.log.LogMgr import ebLogWarn, ebLogInfo, ebLogDebug, ebLogError, ebLogTrace

sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))
# logging.getLogger().setLevel(logging.NOTSET)
#
# # Add stdout handler, with level INFO
# console = logging.StreamHandler(sys.stdout)
# console.setLevel(logging.INFO)
# formater = logging.Formatter('%(name)-13s: %(levelname)-8s %(message)s')
# console.setFormatter(formater)
# logging.getLogger().addHandler(console)
# log = logging.getLogger(__name__)

class LogHandler(object):

    def __init__(self):
        super(LogHandler, self).__init__()
        # self.mPatchLogInfo("Infra Patching Log Framework Initialized")

    def mPatchLogInfo(self, msg):
        ebLogInfo(f"{self.__class__.__name__} - {msg}")

    def mPatchLogError(self, msg):
        ebLogError(f"{self.__class__.__name__} - {msg}")

    def mPatchLogWarn(self, msg):
        ebLogWarn(f"{self.__class__.__name__} - {msg}")

    def mPatchLogDebug(self, msg):
        ebLogDebug(f"{self.__class__.__name__} - {msg}")

    def mPatchmgrLogInfo(self, msg):
        ebLogInfo(f"{'ExadataLogHandler'} - {msg}")

    def mPatchLogTrace(self, msg):
        ebLogTrace(f"{self.__class__.__name__} - {msg}\n")
