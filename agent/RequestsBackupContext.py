"""
$Header:

 Copyright (c) 2014, 2021, Oracle and/or its affiliates.

NAME:
    RequestsBackupContext - Stores date information and presents easy to use methods for handling the request backup

FUNCTION:
    Used to habdle the request to request archive backup capability on the supervisor

NOTE:
    None

History:

    MODIFIED   (MM/DD/YY)
    ndesanto    12/10/21 - Increase coverage on ndesanto files.
    vgerard     09/05/19 - Pruning/Archiving
    ndesanto    02/05/19 - Create file
"""

import datetime
import json
from exabox.core.dbpolicies.Base import ebDBPolicy,ebDBFilter
from exabox.core.dbpolicies.TimeBasedTrigger import ebTimeBasedTrigger
from exabox.core.dbpolicies.ArchivingOperation import ebDBArchivingOperation
from exabox.core.dbpolicies.PruningOperation import ebDBPruningOperation
from exabox.log.LogMgr import ebLogInfo,ebLogWarn,ebLogError


class RequestsBackupContext(object):
    def __init__(self):
        self.__policies = []
        with open('./config/exabox.conf') as _conf:
            __ebconfig = json.load(_conf)

        _config_keys = ('db_pruning_interval','db_pruning_commands','db_archiving_interval','db_archiving_commands') 

        # Check if all specified in configuration, if not, use DEFAULT values
        if not set(_config_keys).issubset(__ebconfig.keys()):
            ebLogWarn('*** Db pruning/archiving parameters missing, using default values') 
            _config_vals = ( '2h',
                             ['cluctrl.rack_info','cluctrl.fetchkeys','cluctrl.em_cluster_details','cluctrl.em_db_details'],
                             '96h',
                             ['cluctrl.vmgi_install','cluctrl.db_install','cluctrl.vmgi_preprov','cluctrl.vmgi_reconfig','cluctrl.vmgi_delete','cluctrl.db_delete',
                              'patch.patchclu_apply','cluctrl.patch_prereq_check','cluctrl.postcheck','cluctrl.backup_image','cluctrl.patch','cluctrl.rollback_prereq_check','cluctrl.rollback'])
        else:
            _config_vals = map(__ebconfig.get,_config_keys) 

        # Generate config dictonary {'db_pruning_interval':<either default or conf>}
        self.__config = dict(zip(_config_keys,_config_vals))
        
        # Validate intervals
        for itv in ('db_pruning_interval','db_archiving_interval'):
           _conf_value = self.__config[itv].lower()
           if not (_conf_value and (_conf_value[-1] == 'h' or _conf_value[-1] == 'm') and _conf_value[:-1].isdigit()):
               _msg = 'Parameter {} must be of form "<digits>[h|m]"'.format(itv)
               ebLogError(_msg)
               raise ValueError(_msg)
           else:
               if _conf_value[-1] == 'h':
                   self.__config[itv] = datetime.timedelta(hours=int(_conf_value[:-1]))
               else: # minutes as h or m is verified above
                   self.__config[itv] = datetime.timedelta(minutes=int(_conf_value[:-1]))

        _TriggerArchive = ebTimeBasedTrigger(wait_time=self.__config['db_archiving_interval'])
        _StatusDone = ebDBFilter('status',['Done'],True)
        _ArchiveWhitelist = ebDBFilter('cmdtype',self.__config['db_archiving_commands'],True)
        _ArchivePolicy = ebDBPolicy(ebDBArchivingOperation,_TriggerArchive,[_StatusDone,_ArchiveWhitelist])
        self.__policies.append(_ArchivePolicy)

        #Pruning Policy
        _TriggerPruning = ebTimeBasedTrigger(self.__config['db_pruning_interval'])
        _PruningList    = ebDBFilter('cmdtype', self.__config['db_pruning_commands'],True)
        _PruningPolicy = ebDBPolicy(ebDBPruningOperation, _TriggerPruning, [_StatusDone, _PruningList])

        self.__policies.append(_PruningPolicy)

        ebLogInfo('*** Setup of db policies done with following configuration:\n{}'.format(self.__config))

    def mEvaluate(self):
        for _policy in self.__policies:
            _policy.mEvaluate()
