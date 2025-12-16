"""
 Copyright (c) 2024, Oracle and/or its affiliates.

NAME:
    metrics_collector - This is responsible for the creation of a scheduler that periodically inserts the data to MySQL Db

FUNCTION:
    Provide functions for creation of the scheduler

NOTE:
    None

History:
    MODIFIED   (MM/DD/YY)
    shapatna    06/21/24 - Adding in methods for adding 'metrics_collector' scheduler job
    shapatna    06/14/24 - Bug 36732867: Create File
"""

from exabox.ovm.exametrics import ebExacloudSysMetrics
from exabox.core.Context import get_gcontext
from exabox.core.Core import exaBoxCoreInit
from exabox.log.LogMgr import ebLogInfo, ebLogInit
from exabox.core.DBStore import ebGetDefaultDB
import os
import json


class MetricsCollector():
    def __init__(self):
        '''
            This method initialises the context and fetches in the path of the exacloud directory
        '''
        exaBoxCoreInit({})
        self.__ctx = get_gcontext()
        self.__options = self.__ctx.mGetArgsOptions()
        ebLogInit(self.__ctx, self.__options)
        
        self.__exacloudPath = os.getcwd()
        self.__exacloudPath = self.__exacloudPath[0: self.__exacloudPath.rfind("exacloud")+8]
        self.__configPath = f"{self.__exacloudPath}/config/metrics_categories.conf"

    def mParseConfig(self):
        '''
            This method parses the metrics_categories.conf file and gets a list of mwthod names which need to be executed
        '''
        _file_path = self.__configPath
        # Open the file as a JSON Object
        with open(_file_path, 'r') as _file:
            _config = json.load(_file)
        _response = {}
        
        # Check for which of the values the corresponding values are true
        for _category, _metrics in _config.items():
            _true_metrics = [_metric for _metric, _value in _metrics.items() if _value]
            if _true_metrics:
                _response[_category] = _true_metrics
        
        return _response

    def mExecuteJob(self):
        '''
            This method first fetches in the selected metrics, calculates their values and then pushes the respective values to the database
        '''
        _functionNames = self.mParseConfig()
        ebLogInfo("*** Entering the execution of metrics_collector job ***")
        aMetric = ebExacloudSysMetrics()
        ebLogInfo(aMetric.mInsertUpdatedDataIntoDb(_functionNames))
        ebLogInfo("*** Exiting metrics_collector job ***")


if __name__ == '__main__':
    job = MetricsCollector()
    job.mExecuteJob()