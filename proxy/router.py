#
# $Header: ecs/exacloud/exabox/proxy/router.py /main/5 2020/12/28 23:58:38 dekuckre Exp $
#
# router.py
#
# Copyright (c) 2020, Oracle and/or its affiliates. 
#
#    NAME
#      router.py - Exacloud router.
#
#    DESCRIPTION
#      Exacloud router to be used by proxy agents to route request to Exacloud instances.
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    dekuckre    12/08/20 - 32239952: Update mRegisterECInstance to set Inactive status
#    dekuckre    12/03/20 - 32178865: Add mExportDBData, mImportDBData
#    dekuckre    10/27/20 - 32072322: Fix DB connections
#    dekuckre    06/09/20 - Creation
#
import time
import cgi
import os
import socket
import json
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug
from exabox.core.DBStore import ebGetDefaultDB
from exabox.core.Context import get_gcontext
from exabox.proxy.CustomCircularQueue import CustomCircularQueue
from exabox.proxy.ecinstance import ExacloudInstance
from multiprocessing import Lock

GENERIC = 'Generic'
SPECIFIC = 'Specific'
PATCHING = 'Patching'

ALIVE = 'Alive'
SUSPENDED = 'Suspended'
INACTIVE = 'Inactive'
DEAD = 'Dead'

format_str = '%Y-%m-%d %H:%M:%S%z'

class Router(object):

    def __init__(self):

        self.__pool = {}
        _routing_algo = get_gcontext().mGetConfigOptions()['proxy_routingalgo']
        _agent_list = get_gcontext().mGetConfigOptions()['proxy_reqtype_list']
        if _routing_algo == 'round-robin':
            for _type in _agent_list.split(','):
                self.__pool[_type] = CustomCircularQueue()

        #dictionary of id to exacloudinstance object.
        self.__ECInstances={}
        self.__uuidToECInstance={}
        self.__db = ebGetDefaultDB()
        self.__lock = Lock()

        self.mLoadInstancesFromDB()


    def mLoadInstancesFromDB(self):

        self.__lock.acquire()

        _entries = self.__db.mSelectAllFromExacloudInstance()

        if len(_entries) != 0 and len(self.__ECInstances) == 0:
            for _row in _entries:  
                _inst = ExacloudInstance(_row[1], _row[2], _row[3], _row[5], _row[6], _row[7])
                _inst.mSetStatus(str(_row[4]))
                _id = _inst.mGetID()
                self.__ECInstances[_id] = _inst
                if str(_row[6]) in self.__pool.keys():
                    self.__pool[_row[6]].insert(_id)
                else:
                    self.__pool[GENERIC].insert(_id)

        _entries = self.__db.mSelectAllFromRequestuuidtoExacloud()

        if len(_entries) != 0 and len(self.__uuidToECInstance) == 0:
            for _row in _entries:
                self.__uuidToECInstance[_row[0]] = _row[1]

        self.__lock.release()

        self.mReportECInstances()
        if len(self.__pool.keys()) != 0:
            for _key in self.__pool.keys():
                ebLogInfo("Current size of {0} pool is {1}".format(_key, self.__pool[_key].getCurrentSizeOfPool()))


    def mGetECInstList(self):

        return self.__ECInstances

    def mReportECInstances(self):
        ebLogInfo('Router instance being used: {}'.format(self))
        for _key in self.__pool.keys():
            _list = self.__pool[_key].getList()
            if _list:
                ebLogInfo("Content of {0} pool is {1}".format(_key, _list))
        for _id in self.__ECInstances:
            _inst = self.__ECInstances[_id]
            ebLogInfo('Exacloud Instance: %s Status: %s' % (_inst.toString(), _inst.mGetStatus()))

    def mRegisterECInstance(self, aHost, aPort, aVers, aAuth_key, aReqtype, aOedaVersion):

        self.__lock.acquire()

        ebLogInfo('Router instance being used: {}'.format(self))
        _inst = self.mGetECInstObj(aHost, aPort)
        if not _inst:
            _inst = ExacloudInstance(aHost, aPort, aVers, aAuth_key, aReqtype, aOedaVersion) 
            _id = _inst.mGetID()
            _inst.mSetStatus(INACTIVE)
            ebLogInfo("Registering new exacloud instance: %s" % _inst.toString())

            # update DB
            self.__db.mInsertExacloudInstanceInfo(_inst.mGetHost(), _inst.mGetPort(), _inst.mGetVersion(), _inst.mGetAuthKey(), _inst.mGetRequestType(), _inst.mGetOedaVersion())

            self.__ECInstances[_id] = _inst
            # Add entry to the pool
            if str(aReqtype) in self.__pool.keys():
                self.__pool[aReqtype].insert(_id)
            else:
                self.__pool[GENERIC].insert(_id)

        else:
            #In case instance object is present in menory have to update the instance information based on what is sent.
            ebLogInfo("Updating already registered exacloud instance: %s" % _inst.toString())
            _id = _inst.mGetID()
            _inst.mSetStatus(ALIVE)
            self.__ECInstances[_id] = _inst
            _reqtype = GENERIC
            if str(aReqtype) in self.__pool.keys():
                _reqtype = aReqtype

            for _key in self.__pool.keys():
                if _key != _reqtype:
                    self.__pool[_key].remove(_id)

            self.__pool[_reqtype].insert(_id)
            self.__db.mUpdateExacloudInstanceInfo(_inst.mGetID(), 'status', ALIVE)
            self.__db.mUpdateExacloudInstanceInfo(_inst.mGetID(), 'reqtype', _reqtype)

        self.__lock.release()
        ebLogInfo('Number of exacloud instances: %d'% len(self.__ECInstances))
        self.mReportECInstances()


    def mDeregisterECInstance(self, aHost, aPort, aReqtype):

        self.__lock.acquire()
        ebLogInfo('Router instance being used: {}'.format(self))
        _inst = self.mGetECInstObj(aHost, aPort)
        if _inst is not None :
            _id = _inst.mGetID()
            ebLogInfo("Deregistering exacloud instance: %s" % _inst.toString())
            _inst.mSetStatus(DEAD)
            self.__ECInstances[_id] = _inst
            # Remove the entry from the pool
            self.__pool[aReqtype].remove(_id)
        else:
            ebLogWarn("No exacloud with instance information %s is registered with the proxy." % (str(aHost)+":"+str(aPort)))
            self.__lock.release()
            return

        # Update DB
        self.__db.mUpdateExacloudInstanceInfo(str(aHost)+":"+str(aPort), 'status', DEAD)

        self.__lock.release()

        ebLogInfo('Number of exacloud instances: %d'% len(self.__ECInstances))
        self.mReportECInstances()

    def mGetECInstVersionInfo(self, aID):
        _inst = self.__ECInstances[aID]
        return _inst.mGetVersion(), _inst.mGetOedaVersion()


    def mUpdateECInstance(self, aHost, aPort, aKey, aValue):
        
        self.__lock.acquire()
        _key = aKey
        _value = aValue

        _inst = self.mGetECInstObj(aHost, aPort)
        if _inst is not None:
            _id = _inst.mGetID()

            if _key == 'status':
                _inst.mSetStatus(_value)
            if _key == 'reqtype':
                _inst.mSetRequestType(_value)
                _reqtype = _value

                for _k in self.__pool.keys():
                    if _k != _reqtype:
                        self.__pool[_k].remove(_id)

                self.__pool[_reqtype].insert(_id)

            self.__ECInstances[_id] = _inst
            ebLogInfo("Updating exacloud instance: %s key: %s value: %s " % (_inst.toString(), _key, _value))

            # update DB
            self.__db.mUpdateExacloudInstanceInfo(_inst.mGetID(), _key, _value)
        else:
            ebLogWarn("No exacloud with instance information %s is registered with the proxy." % (str(aHost)+":"+str(aPort)))
            self.__lock.release()
            return

        ebLogInfo('Number of exacloud instances: %d'% len(self.__ECInstances))
        self.mReportECInstances()
        self.__lock.release()

    def mUpdateUUIDToECInstance(self, _uuid, _ecinstid=None, aDeleteEntry=False):
        self.__lock.acquire()
        if aDeleteEntry is False:
            self.__uuidToECInstance[_uuid] = _ecinstid

            self.__db.mInsertUUIDtoECInstanceInfo(_uuid, _ecinstid, time.strftime("%c"))

        else:
            if _uuid in self.__uuidToECInstance.keys():
                del self.__uuidToECInstance[_uuid]
                #self.__db.mUpdateStatusForReqUUID(_uuid, 'Done')
        self.__lock.release()
        
    def mGetExacloudHostURL(self, _ecInstanceID):
        if _ecInstanceID in self.__ECInstances.keys():
            return self.__ECInstances[_ecInstanceID].mGetExacloudHostURL()

    def mGetECInstObj(self, _strhost, _strport):

        for _inst in self.__ECInstances.values():
            if str(_inst.mGetHost()) == str(_strhost) and str(_inst.mGetPort()) == str(_strport):
                return _inst

        return None

    # Used by proxy to obtain - 
    # the next available exacloud instance details (host, port, auth_key)
    # or 
    # the exacloud instance details corresponding to the uuid passed
    def mGetECInstance(self, aRequestType=GENERIC, uuid=None):
        self.__lock.acquire()
        ebLogInfo('Router instance being used: {}'.format(self))
        _inst = None
        _reqtype = GENERIC
        if str(aRequestType) in self.__pool.keys():
            _reqtype = aRequestType

        if uuid:
            _id = self.__uuidToECInstance[uuid]
            _inst = self.__ECInstances[_id]
        else:
            _id = self.__pool[_reqtype].getNextAvailableElement()
            if _id == None:
                _reqtype = GENERIC
                _id = self.__pool[_reqtype].getNextAvailableElement()
                if _id == None:
                    self.__lock.release()
                    return None, None, None
            _inst = self.__ECInstances[_id]
            while(_inst.mGetStatus() != ALIVE):

                _idn = self.__pool[_reqtype].getNextAvailableElement()
                if _idn == None or _id == _idn:
                    self.__lock.release()
                    return None, None, None
                _inst = self.__ECInstances[_idn]

        if _inst:
            ebLogInfo("Routing request to host: {0}, port: {1}, authkey: {2}".format(_inst.mGetHost(), _inst.mGetPort(), _inst.mGetAuthKey()))
            self.__lock.release()
            return _inst.mGetHost(), _inst.mGetPort(), _inst.mGetAuthKey()
        else:
            ebLogInfo("returning None data.")
            self.__lock.release()
            return None, None, None

    def mExportDBData(self):

        return self.__db.mExportProxyMigrationTables()

    def mImportDBData(self, aFile):

        self.__db. mMigrateProxyDB(aFile)

