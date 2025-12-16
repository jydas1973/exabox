"""
 Copyright (c) 2014, 2021, Oracle and/or its affiliates. 

NAME:
    DBStore - Basic DB functionality

FUNCTION:
    Provide basic/core APIs

NOTE:
    None

History:
    mirivier    02/5/2015 - Create file
"""

import os
import json

with open('config/exabox.conf') as fd:
    cfg = json.load(fd)

#
# config/exatest_extra_config.conf file only exists on exatest enviroment
# the utility of this file is to load additional configuration without change exabox.conf in the txn
#
if os.path.isfile('config/exatest_extra_config.conf'):
    with open('config/exatest_extra_config.conf') as fd:
        _extra = json.load(fd)
        if "exacloud" in _extra:
            cfg.update(_extra['exacloud'])

if 'db_version' not in cfg:
    cfg['db_version'] = 3

if cfg['db_version'] == 3:
    from .DBStore3 import *
    def get_db_version():
        return 3
else:
    # Using default DB Version (3)
    from .DBStore3 import *
    def get_db_version():
        return 3

