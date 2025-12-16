"""
 Copyright (c) 2014, 2024, Oracle and/or its affiliates.

NAME:
    Racks - Basic functionality

FUNCTION:
    Provide basic/core API for managing Racks Cluster (List, Reserve/Release, Check,...)

NOTE:
    None

History:

    MODIFIED   (MM/DD/YY)
       prsshukl    06/13/24 - Bug 36731332 - Fix for rack getkeys in mInitrepo
       prsshukl    06/11/24 - Bug 36719808 - Add another ADE_SITE condition
       prsshukl    07/03/23 - Bug 35543852 - Fix for the getkeys feature to
                              work for every other region
       prsshukl    06/16/23 - Bug 35508310 - Updating the new location for
                              devracks keys for etf
       alsepulv    03/22/22 - Enh 33941264: Improve code coverage
       alsepulv    01/25/22 - Enh 33734668: Code coverage improvements
       alsepulv    12/13/21 - Bug 33642466: Remove dead code
       alsepulv    03/16/21 - Enh 32619413: remove any code related to Higgs
       jesandov    07/30/20 - XbranchMerge jesandov_bug-31653453_19.4.3.3.0
                              from st_ecs_19.4.3.0.0
       ndesanto    10/02/19 - Enh 30374491: EXACC PYTHON 3 MIGRATION BATCH 02
       indrabha    01/30/19 - XbranchMerge indrabha_bug-29170517_18.2.5.2exabm
                              from st_ebm_18.2.5.2.0
       gsundara    01/17/19 - ER 29217327
       gsundara    11/30/18 - ER 28864094 (KMS+CASPER)
       agarrido    02/02/18 - Improve rack getkeys funcionality for higgs
       mirivier    12/01/15 - Create file
"""

from __future__ import print_function

import six
import sqlite3
import os, sys, time
import threading
from multiprocessing import Process
import getpass
import socket
import tempfile
import paramiko
import select
import re
import time
import json
import ast
import shutil
from glob import glob
from base64 import b64decode
from zipfile import ZipFile

from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogDB
from exabox.core.Core import ebExit
from exabox.ovm.clucontrol import exaBoxCluCtrl
from exabox.ovm.clumisc import ebCluPreChecks
from exabox.config.Config import exaBoxConfigFileReader
from exabox.ovm.hypervisorutils import getHVInstance
from exabox.exakms.ExaKmsEntry import ExaKmsEntry, ExaKmsHostType

DEVNULL = open(os.devnull, 'wb')

gNodeCache={}
gThreadLock=threading.Lock()

class ebRacksDB(object):

    def __init__(self):

        _config = get_gcontext().mGetConfigOptions()
        if 'racks_dir' in list(_config.keys()) and _config['racks_dir']:
            self.__db_path = _config['racks_dir']
        else: # pragma: no cover
            _ade_site= ""
            _o = os.environ.get('ADE_SITE')
            _ade_site = _o.strip()
            ebLogInfo(f'The value of ADE_SITE is {_ade_site}')
            if _ade_site == "slc" or _ade_site == "ade_slc" or _ade_site == "ade_farm_slc":
                self.__db_path = '/net/slcnas648.us.oracle.com/export/intg_largedos_metadata/large_dos/ECS/MAIN/LINUX.X64/ecs/ecra/racks/devracks'
            else:
                self.__db_path = '/net/dbdevfssifarm1.dev3farm1phx.databasede3phx.oraclevcn.com/farm_intg_metadata/large_dos/ECS/MAIN/LINUX.X64/ecs/ecra/racks/devracks'

        try:
            os.lstat(self.__db_path)
        except: # pragma: no cover
            ebLogError('*** RACK Global Repository not accessible using path: %s ' % (self.__db_path))
            ebLogDB('ERR','Invalid DB location: '+self.__db_path)
            ebExit(-1)

        self.__conn   = sqlite3.connect(self.__db_path+'/racks.db', check_same_thread=False, isolation_level=None)
        self.__cursor = self.__conn.cursor()

        self.__lock   = threading.Lock()
        self.__log = False

        self.mCreateRacksTable()
        self.mCreateLocationTable()
        self.mCreateKeysTable()

    def mShutdownDB(self):
        self.__cursor.close()
        self.__conn.close()
        self.__lock = None

    def mGetLog(self):
        return self.__log

    def mExecute(self, aSql, aDataList=None):

        self.__lock.acquire()
        try:
            if self.mGetLog():
                ebLogDB('NFO', aSql) # pragma: no cover

            if aDataList:
                if isinstance(aDataList, list) or isinstance(aDataList, tuple):
                    _dict = { str(i+1): str(aDataList[i]) for i in range(0, len(aDataList)) }
                else: # pragma: no cover
                    _dict = aDataList

                if self.mGetLog(): # pragma: no cover
                    _n = 40
                    _out = {k: v[:_n] for k, v in list(_dict.items())}
                    ebLogDB('NFO', _out)

                rc = self.__cursor.execute(aSql, _dict)
            else:
                rc = self.__cursor.execute(aSql)
        except Exception as ex: # pragma: no cover
            ebLogError(aSql)
            ebLogDB('ERR',aSql)
            raise ex
        finally:
            self.__lock.release()

        return rc

    def mCommit(self):
        self.__conn.commit()

    def mCheckTableExist(self, aTableName):
        _sql = """SELECT name FROM sqlite_master WHERE type='table' AND name=:1"""
        _data = [aTableName]
        self.mExecute(_sql, _data)
        _fdata = self.__cursor.fetchone()
        if _fdata and len(_fdata) and _fdata[0] == aTableName:
            return True
        else:
            return False

    def mCreateKeysTable(self):
        """
        Request fields:
            0. uuid
            1. hostname
            2. user
            3. keydata
            4. createtime
            5. updatetime
            6. misc
        """
        if not self.mCheckTableExist('keys'):
            self.mExecute('''CREATE TABLE keys (uuid text, hostname text, user text, keydata text, createtime text, updatetime text, misc text, keydatapub text)''')

    def mCreateRacksTable(self):
        """
        Request fields:
            0. uuid
            1. rackid
            2. status
            3. owner
            4. timestamp-start
            5. timestamp-stop
        """
        if not self.mCheckTableExist('registry'):
            self.mExecute('''CREATE TABLE registry (uuid text, rackid text, status text, owner text, starttime text, endtime text)''')

    def mCreateLocationTable(self):
        """
        Request fields:
            0. uuid
            1. rackid
            2. hostname
            3. path
        """
        if not self.mCheckTableExist('location'):
            self.mExecute('''CREATE TABLE location (uuid text, rackid text, hostname text, path text)''')

    def mDeleteRack(self,aRackId='0'):

        _sql = """DELETE from registry WHERE rackid=:1"""
        _data = [aRackId]
        self.mExecute(_sql, _data)
        self.mCommit()

    def mDeleteLocation(self,aRackId='0'):

        _sql = """DELETE from location WHERE rackid=:1"""
        _data = [aRackId]
        self.mExecute(_sql, _data)
        self.mCommit()

    def mInsertRack(self,aRackInfo):

        _ai = aRackInfo
        _uuid      = _ai.mGetUUID()
        _rackid    = _ai.mGetRackID()
        _status    = _ai.mGetStatus()
        _owner     = _ai.mGetOwner()
        _ttstart   = _ai.mGetStartTime()
        _ttstop    = _ai.mGetEndTime()

        _sql = """INSERT INTO registry VALUES (:1, :2, :3, :4, :5, :6)"""
        _data = [_uuid, _rackid, _status, _owner, _ttstart, _ttstop]
        self.mExecute(_sql, _data)
        self.mCommit()

    def mInsertLocation(self,aRackInfo):

        _ai = aRackInfo
        _uuid      = _ai.mGetUUID()
        _rackid    = _ai.mGetRackID()
        _host      = _ai.mGetHostname()
        _path      = _ai.mGetPath()

        _sql = """INSERT INTO location VALUES (:1, :2, :3, :4)"""
        _data = [_uuid, _rackid, _host, _path]
        self.mExecute(_sql, _data)
        self.mCommit()

    def mUpdateLocation(self,aRackInfo):

        _ai = aRackInfo
        _uuid      = _ai.mGetUUID()
        _rackid    = _ai.mGetRackID()
        _host      = _ai.mGetHostname()
        _path      = _ai.mGetPath()

        _sql = """UPDATE location SET uuid=:1, rackid=:2, hostname=:3, path=:4"""
        _data = [_uuid, _rackid, _host, _path]
        self.mExecute(_sql, _data)
        self.mCommit()

    def mUpdateRack(self,aRackInfo):

        _ai = aRackInfo
        _uuid      = _ai.mGetUUID()
        _rackid    = _ai.mGetRackID()
        _status    = _ai.mGetStatus()
        _owner     = _ai.mGetOwner()
        _ttstart   = _ai.mGetStartTime()
        _ttstop    = _ai.mGetEndTime()

        _sql = """UPDATE registry SET uuid=:1, rackid=:2, status=:3, owner=:4, starttime=:5, endtime=:6"""
        _data = [_uuid, _rackid, _status, _owner, _ttstart, _ttstop]
        self.mExecute(_sql, _data)
        self.mCommit()

    def mRackStatus(self,aRackId='0'):

        _sql = """SELECT * from registry WHERE rackid=:1"""
        _data = [aRackId]
        _handle = self.mExecute(_sql, _data)
        _rc = _handle.fetchone()
        return _rc

class ebRackInfo(object):

    def __init__(self,aUUID=0, aDB=None):

        self.__uuid     = aUUID
        self.__rackid   = None
        self.__status   = 'released'
        self.__owner    = 'None'
        self.__ttstart  = None  # time.strftime("%c")
        self.__ttstop   = None
        self.__db       = aDB
        self.__host     = None
        self.__path     = None

    def mGetPath(self):
        return self.__path

    def mGetHostname(self):
        return self.__host

    def mSetPath(self, aPath=None):
        self.__path = aPath

    def mSetHostname(self, aHost=None):
        self.__host = aHost

    def mGetStatus(self):
        return self.__status

    def mGetUUID(self):
        return self.__uuid

    def mGetRackID(self):
        return self.__rackid

    def mGetOwner(self):
        return self.__owner

    def mGetStartTime(self):
        return self.__ttstart

    def mGetEndTime(self):
        return self.__ttstop

    def mSetStatus(self,aStatus):
        self.__status =  aStatus

    def mSetUUID(self,aUUID=0):
        self.__uuid = aUUID

    def mSetRackID(self,aRackID=0):
        self.__rackid = aRackID

    def mSetOwner(self,aOwner):
        self.__owner = aOwner

    def mSetStartTime(self,aStartTime=None):
        if aStartTime is None:
            self.__ttstart = time.strftime("%c")
        else:
            self.__ttstart = aStartTime

    def mSetEndTime(self,aEndTime=None):
        if aEndTime is None:
            self.__ttstop = time.strftime("%c") # pragma: no cover
        else:
            self.__ttstop = aEndTime

    def mLoadRackFromDB(self, aRackID=0):

        _req = self.__db.mRackStatus(aRackID)
        self.mPopulateRack(_req)

    def mPopulateRack(self, aReq):

        _req = aReq
        if _req:
            self.mSetUUID(_req[0])
            self.mSetRackID(_req[1])
            self.mSetStatus(_req[2])
            self.mSetOwner(_req[3])
            self.mSetStartTime(_req[4])
            self.mSetEndTime(_req[5])


class ebRackControl:

    def __init__(self, aOptions):

        self.__options = aOptions
        self.__rackInfo = None
        self.__clubox = None
        self.__repoPath = None
        self.__endpointInfo = None
        self.__rackDB = ebRacksDB()

        self.mInitRepoPath()
        self.mReadEndpointConfig()

    def mGetOptions(self):
        return self.__options

    def mSetOptions(self, aValue):
        self.__options = aValue

    def mGetRackInfo(self):
        return self.__rackInfo

    def mSetRackInfo(self, aValue):
        self.__rackInfo = aValue

    def mGetClubox(self):
        return self.__clubox

    def mSetClubox(self, aValue):
        self.__clubox = aValue

    def mGetRepoPath(self):
        return self.__repoPath

    def mSetRepoPath(self, aValue):
        self.__repoPath = aValue

    def mGetEndpointInfo(self):
        return self.__endpointInfo

    def mSetEndpointInfo(self, aValue):
        self.__endpointInfo = aValue

    def mGetRackDB(self):
        return self.__rackDB

    def mSetRackDB(self, aValue):
        self.__rackDB = aValue

    def mReadEndpointConfig(self):

        _endpoints = {}
        with open("config/program_arguments.conf", "r") as _f:
            _endpoints = json.loads(_f.read())

        self.mSetEndpointInfo(_endpoints['rack']['choices'])

    def mInitRepoPath(self):

        _config = get_gcontext().mGetConfigOptions()
        if 'racks_dir' in list(_config.keys()) and _config['racks_dir']:
            _path = _config['racks_dir']
        else: # pragma: no cover
            _ade_site= ""
            _o = os.environ.get('ADE_SITE')
            _ade_site = _o.strip()
            ebLogInfo(f'The value of ADE_SITE is {_ade_site}')
            if _ade_site == "slc" or _ade_site == "ade_slc" or _ade_site == "ade_farm_slc":
                _path = '/net/slcnas648.us.oracle.com/export/intg_largedos_metadata/large_dos/ECS/MAIN/LINUX.X64/ecs/ecra/racks/devracks'
            else:
                _path = '/net/dbdevfssifarm1.dev3farm1phx.databasede3phx.oraclevcn.com/farm_intg_metadata/large_dos/ECS/MAIN/LINUX.X64/ecs/ecra/racks/devracks'

        try:
            os.lstat(_path)
        except: # pragma: no cover
            raise ValueError(f'*** Invalid Racks patch location: {_path}')

        self.mSetRepoPath(_path)

    def mCreateClubox(self, aRackInfo):

        # Create clucontrol object
        _ecc = exaBoxCluCtrl(get_gcontext())
        _ecc.mSetConfigPath(aRackInfo['xml_path'])
        _ecc.mParseXMLConfig(self.mGetOptions())

        _key = _ecc.mBuildClusterId()
        _rackId = aRackInfo['id']

        # Create cluster directory
        _dir = f'clusters/{_key}'
        _link = f'clusters/cluster-{_rackId}'

        if not os.path.exists(_dir):
            os.mkdir(_dir)
            os.mkdir(f"{_dir}/config")

        if not os.path.exists(_link):
            os.symlink(_dir.split('/')[-1],_link)

        # Save XML
        shutil.copy(aRackInfo['xml_path'], f"{_dir}/config/")

        return _ecc


    def mInitConfig(self, aOptions, aRackId=None):

        _rackInfo = {}
        _cmd  = aOptions.rackcmd
        _user = aOptions.uid
        _id   = aOptions.id

        if aRackId: # pragma: no cover
            _id = aRackId

        # Validate CMD
        _rackInfo['cmd'] = _cmd

        # Validate User
        if "require_user" in self.mGetEndpointInfo()[_cmd]:

            if not _user: # pragma: no cover
                raise ValueError("Parameter -uid is requiered")

            _rackInfo['user'] = _user

        # Validate ID
        if "require_id" in self.mGetEndpointInfo()[_cmd]:

            if not _id: # pragma: no cover
                raise ValueError("Parameter -id is requiered")

            _rackInfo['id'] = _id

        if _rackInfo['id']:

            # XML and Keys
            _xml, _keys = self.mCheckClusterConfig(_rackInfo['id'])

            _rackInfo['xml_path'] = _xml
            _rackInfo['keys_path'] = _keys

        return _rackInfo

    def mGetAvaliableRackIds(self):

        _rackFolders = sorted(os.listdir(self.mGetRepoPath()))
        _rackIds = []

        for _rackBase in _rackFolders:

            _rackFolder = os.path.join(self.mGetRepoPath(), _rackBase)

            if os.path.isdir(_rackFolder):

                _rackXmls = os.listdir(_rackFolder)
                _rackXmls = list(filter(lambda x: x.endswith("xml"), _rackXmls))
                _rackXmls = list(map(lambda x: x.replace(".xml", ""), _rackXmls))

            _rackIds += _rackXmls

        return _rackIds

    def mCheckClusterConfig(self, aId):

        _rack = aId
        _id = aId

        if "clu" in aId: # pragma: no cover
            _rack = aId.split("clu")[0]

        _rackFolder = os.path.join(self.mGetRepoPath(), _rack)
        _rackXmlFile = os.path.join(self.mGetRepoPath(), _rack, f"{_id}.xml")

        # XML Validation
        if not os.path.exists(_rackXmlFile): # pragma: no cover
            _rackXmlFile = None
            ebLogWarn(f'*** No rack XML file found for rack: {_rack}')

        # Keys Validation
        _keysList  = glob(f"{_rackFolder}/keys*.zip")
        _keys = None

        if not len(_keysList):
            _keys = None
            ebLogWarn(f'*** No SSH key files found for rack: {_rack}')
            return
        else:
            _keys = _keysList[0]

        return _rackXmlFile, _keys


    def mExecute(self):

        _cmd = self.mGetOptions().rackcmd

        try:

            if "require_id" in self.mGetEndpointInfo()[_cmd]:

                _rackInfo = self.mInitConfig(self.mGetOptions())

                if not _rackInfo['xml_path']: # pragma: no cover
                    ebLogError(f"Invalid rack id: {_rackInfo['id']}, XML not found")
                    return

                if not _rackInfo['keys_path']: # pragma: no cover
                    ebLogError(f"Invalid rack id: {_rackInfo['id']}, Keys not found")
                    return

                _clubox = self.mCreateClubox(_rackInfo)

                self.mSetRackInfo(_rackInfo)
                self.mSetClubox(_clubox)

            if _cmd == "list":
                self.mListRacks()

            elif _cmd == "listowner":
                self.mListOwner()

            elif _cmd == "reserve":
                self.mReserverRack()

            elif _cmd == "release":
                self.mReleaseRack()

            elif _cmd == "getkeys":
                self.mGetKeysRack()

        finally:

            self.mGetRackDB().mShutdownDB()
            ebLogInfo('*** Rack operation completed')

    def mListRacks(self):

        _rackIds = self.mGetAvaliableRackIds()

        for _rackId in _rackIds:
            ebLogInfo("Found rack id: {0}".format(_rackId))

    def mListOwner(self):

        _rackId = self.mGetRackInfo()['id']
        _rackEntry = ebRackInfo(aDB=self.mGetRackDB())
        _rackEntry.mLoadRackFromDB(_rackId)

        if _rackEntry.mGetRackID() and _rackEntry.mGetStatus() != 'released':
            ebLogInfo(f'*** rackid {_rackId} is reserved by {_rackEntry.mGetOwner()}')
        elif _rackEntry.mGetStatus() == 'released':
            ebLogInfo(f'*** rackid {_rackId} is unreserved')
        else: # pragma: no cover
            ebLogWarn(f'*** rackid {_rackId} owner information unavailable')

    def mReserverRack(self):

        _rackId = self.mGetRackInfo()['id']
        _owner = self.mGetRackInfo()['user']

        _rackEntry = ebRackInfo(aDB=self.mGetRackDB())
        _rackEntry.mLoadRackFromDB(_rackId)

        if _rackEntry.mGetRackID() and _rackEntry.mGetStatus() != 'released': # pragma: no cover
            ebLogInfo(f'*** rackid {_rackId} is reserved by {_rackEntry.mGetOwner()}')
            return

        # Do reservation
        _rackinfo = ebRackInfo()
        _rackinfo.mSetRackID(_rackId)
        _rackinfo.mSetOwner(_owner)
        _rackinfo.mSetStatus('reserved')
        _rackinfo.mSetStartTime()
        _rackinfo.mSetHostname(socket.getfqdn())
        _path=os.getcwd()
        _path=_path[:_path.rfind('exacloud')]+'exacloud'
        _rackinfo.mSetPath(_path)

        if self.mGetRackDB().mRackStatus(_rackId) is None:
            self.mGetRackDB().mInsertRack(_rackinfo)
            self.mGetRackDB().mInsertLocation(_rackinfo)
        else: # pragma: no cover
            self.mGetRackDB().mUpdateRack(_rackinfo)
            self.mGetRackDB().mUpdateLocation(_rackinfo)

        ebLogInfo("*** Rack reserver complete")

    def mReleaseRack(self):

        _rackId = self.mGetRackInfo()['id']
        _owner = self.mGetRackInfo()['user']

        _rackEntry = ebRackInfo(aDB=self.mGetRackDB())
        _rackEntry.mLoadRackFromDB(_rackId)

        if not _rackEntry.mGetRackID() or _rackEntry.mGetOwner() != _owner: # pragma: no cover
            ebLogInfo(f'*** Invalid rackid {_rackId} and user {_owner} combination fore release')
            return

        self.mGetRackDB().mDeleteRack(_rackEntry)
        self.mGetRackDB().mDeleteLocation(_rackEntry)

        ebLogInfo("*** Rack release complete")

    def mGetKeysRack(self):

        # Read Keys Zip
        _inputZip = ZipFile(self.mGetRackInfo()['keys_path'])
        _keysContent = {name: _inputZip.read(name) for name in _inputZip.namelist()}

        # Dump keys on folder
        _rackId = self.mGetRackInfo()['id']
        _saveFolder = f'clusters/cluster-{_rackId}/keys/'

        if not os.path.exists(_saveFolder):
            os.makedirs(_saveFolder)

        for _filename, _sshkey in _keysContent.items():


            try:
                _internalFile = os.path.join(_saveFolder, os.path.basename(_filename))
                with open(_internalFile, "w") as _f:
                    _f.write(_sshkey.decode("utf-8"))
                os.chmod(_internalFile, 0o600)

            except: # pragma: no cover
                ebLogWarn(f"Invalid file: {_filename}")

        _hostDict = self.mGetClubox().mGetExaKmsHostMap()

        _exakms = get_gcontext().mGetExaKms()
        _exakms.mRestoreEntriesFromFolder(_saveFolder, _hostDict)

# end of file
