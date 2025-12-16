"""
 Copyright (c) 2014, 2023, Oracle and/or its affiliates. 

NAME:
    DBLockTableUtils.py

FUNCTION:
    Functions to manage DBLock table easily and factorize code

NOTE:
    None

History:
    alsepulv   2021/02/23 - Bug 32513420: Fix pylint error '__str__ does not
                            represent str'
    vgerard    2019/10/04
    
"""

from exabox.core.Context import get_gcontext
from exabox.log.LogMgr import ebLogError,ebLogInfo,ebLogWarn
from exabox.utils.node import connect_to_host
from enum import Enum
from itertools import groupby
from operator import itemgetter


class ebDBLockTypes(Enum):
    ''' List of possible values for lock_type column '''
    DOM0_LOCK = 'dom0_lock'
    DOM0_LOCK_ACQUIRING = 'dom0_lock_acquiring'

    def __str__(self):
        return str(self.value)


#Please update this function to match columns, enable managing values
# by name across code instead of db position
def sLockDBRowToDict(aRow):
    # Be sure only values in ebDBLockType Enum are written in lock_type row
    return {'uuid':aRow[0],
            'lock_type':ebDBLockTypes(aRow[1]),
            'lock_hostname':aRow[2],
            'start_time':aRow[3], 
            'exp_time_sec':aRow[4],
            'json_metadata':aRow[5]}


def sDBLockCleanLockOnHost(aNode, aLockDict, aMock=False):
    ''' Will call the cleanup function depending on lock type '''
    if aLockDict['lock_type'] not in ebDBLockTypes:
        raise ValueError('lock_type column in DB is: {}, must be one of: {}'
                        .format(aLockDict['lock_type'], tuple(ebDBLockTypes)))
    
    return ebDBLockCleanup(aLockDict['lock_type'],aMock).mCleanup(aNode, aLockDict)


# Function, to cleanup ALL  Leftover locks
def sDBLockCleanAllLeftoverLocks(aMock=False):
    # Defered import to avoid Circular dependencies
    from exabox.core.Node import exaBoxNode
    from exabox.core.DBStore import ebGetDefaultDB

    _db = ebGetDefaultDB()
    try:
        _allLocks = _db.mGetAllLocks()
    except Exception as e:
        ebLogWarn('Unable to get locks:{}, aborting cleanup'.format(e))
        return
    
    # Group locks per hostnames so connections are efficient
    _sort_key = itemgetter('lock_hostname')

    _node = None
    _results = []

    # groupby output is ((dom0A,[LockA1,LockA2]), (dom0B,[LockB]),...)
    # Cleanup all locks, dom0 by dom0 in sorted order
    for _host,_lock_list in groupby(sorted(_allLocks, key=_sort_key),key=_sort_key):
        if not aMock:
            try:
                with connect_to_host(_host, get_gcontext()) as _node:
                    # Here we are connected to host (in non Mock), cleanup all locks
                    for _lock in _lock_list:
                        _results.append(sDBLockCleanLockOnHost(_node, _lock, aMock))
            except Exception as e:
                ebLogWarn('Cannot connect to host: {} for lock cleanup:({})'
                          .format(_host, e))
                continue
        else:
            # Here we are connected to host (in Mock), cleanup all locks
            for _lock in _lock_list:
                _results.append(sDBLockCleanLockOnHost(_node, _lock, aMock))

    _db.mDeleteAllLocks()
    return _results
           

# END OF EXTERNAL API ==== INTERNALS FUNCTION BELOW ====

class ebDBLockCleanup(object):

    def __init__(self, aLockType, aMock=False):
        self.__lock_type = aLockType
        self.__mock = aMock

    def mCleanup(self, aNode, aLockDict):
        # Dispatching method
        _methodMap = {
            ebDBLockTypes.DOM0_LOCK           : self.mCleanDom0Lock,
            ebDBLockTypes.DOM0_LOCK_ACQUIRING : self.mCleanDom0PendingLock
        }
        return _methodMap[self.__lock_type](aNode, aLockDict)


    def mCleanDom0Lock(self, aNode, aLockDict):
        ''' If lock is still in DB, it means that lock is still aquired'''
        _cmd = 'rm -f /tmp/exacs_dom0_lock ; rm -f /tmp/exacs_dom0_lock_info'
        if self.__mock:
            return (aLockDict['lock_hostname'],_cmd)
        ebLogInfo('Cleaning up Acquired lock on {}'.format(aLockDict['lock_hostname']))
        aNode.mExecuteCmdLog(_cmd)
        return aNode.mGetCmdExitStatus()
        
    def mCleanDom0PendingLock(self, aNode, aLockDict):
        ''' For pending locks, there is a queue, only kill same UUID'''
        _cmd = "pkill -9 -f 'tlock.sh acquire {}'".format(aLockDict['uuid'])
        if self.__mock:
            return (aLockDict['lock_hostname'],_cmd)
        ebLogInfo('Cleaning up Pending Lock on {}'.format(aLockDict['lock_hostname']))
        aNode.mExecuteCmdLog(_cmd)
        return aNode.mGetCmdExitStatus()

