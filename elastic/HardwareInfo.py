"""
 Copyright (c) 2014, 2018, Oracle and/or its affiliates. All rights reserved.

NAME:
    ElasticInfo - Information about hardware

FUNCTION:
    Provide Command usage for Hardware details

NOTE:
    None

History:
    jloubet    21/11/2018 - File Creation
"""

from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogVerbose
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
import re

class ebHardwareInfo(object):

    def __init__(self, aHwType, aHostname):
        self.__hw_type = aHwType
        self.__hostname = aHostname

    def mGetHwType(self):
        return self.__hw_type

    def mGetHostname(self):
        return self.__hostname

    def mGetInfo(self):
        if self.mGetHwType() == 'cell':
            return self.mCellInfo()
        if self.mGetHwType() == 'compute':
            return self.mComputeInfo()
        return 'Invalid hw_type'

    def mCellInfo(self):
        _node = exaBoxNode(get_gcontext())
        _result = {}

        try:
            _node.mConnect(aHost=self.mGetHostname())
            _result['ipaddress'] = _node.mSingleLineOutput("hostname -i")
            _result['fullhostname'] = _node.mSingleLineOutput("hostname")
            _node.mMultipleLineOutputWithSeparator("cellcli -e list cell detail", ":", _result)
            _i, _o, _e = _node.mExecuteCmd("cellcli -e list physicaldisk attributes physicalSize")
            _storage_in_tb = 0
            for _line in _o.readlines():
                _line = re.sub(r"\s+", " ", _line)
                _line = _line.rstrip("\n")
                tuple = _line.split('.')
                #Changing to 2 decimals precision
                _storage_in_tb += float(tuple[0] + '.' + tuple[1][:2])
            _result['local_storage_gb'] = str("%.2f" % (_storage_in_tb*1024))
        except Exception as e:
            _result = e
        _node.mDisconnect()
        return _result

    def mComputeInfo(self):
        _node = exaBoxNode(get_gcontext())
        _result = {}
        try:
            _node.mConnect(aHost=self.mGetHostname())
            _result['model'] = _node.mSingleLineOutput("exadata.img.hw --get model")
            _result['ipaddress'] = _node.mSingleLineOutput("hostname -i")
            _result['fullhostname'] = _node.mSingleLineOutput("hostname")
            _node.mMultipleLineOutputWithSeparator("xm info", ":",_result)
            _result['total_cores'] = int(_result['cores_per_socket']) * int(_result['nr_nodes'])
        except Exception as e:
            _result = e
        _node.mDisconnect()
        return _result

