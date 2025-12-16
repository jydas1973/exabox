"""
 Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.

NAME:
    cleanup_exawatcher_log - cleanup old exawatcher log files

FUNCTION:
    Invoke cleanup routine for exawatcher

NOTE:
    None

"""

import sys

from exabox.core.Context import get_gcontext
from exabox.core.Core import exaBoxCoreInit
from exabox.log.LogMgr import ebLogInit
from exabox.ovm.exawatcher import cleanupExaWatcherLogs

def main(argv=None):
    exaBoxCoreInit({})
    ebContext = get_gcontext()
    options = ebContext.mGetArgsOptions()
    ebLogInit(ebContext, options)
    cleanupExaWatcherLogs()
    sys.exit(0)

if __name__ == '__main__':
    main()
