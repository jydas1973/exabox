"""
 Copyright (c) 2014, 2022, Oracle and/or its affiliates. 

NAME:
    OVM - Sparse Cloning related functionality

FUNCTION:
    Module to provide all the sparse cloning APIs

NOTE:
    None

History:
    pverma      04/07/2017 - Factoring in changes due to 
                             updates to cludbaas module
    hnvenkat    04/07/2016 - Create file

Changelog:

   29/07/2016 - v1 changes:

       1) API for creating testmaster DB
"""
from exabox.core.Node import exaBoxNode
from exabox.core.Error import gSparseError,ebError
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug
from exabox.log.LogMgr import ebLogJson
from exabox.ovm.vmconfig import exaBoxClusterConfig
from exabox.ovm.cluresmgr import ebCluResManager
import os, sys, subprocess, uuid, time, os.path
from subprocess import Popen, PIPE
import xml.etree.cElementTree as etree
from exabox.core.Context import get_gcontext
from exabox.core.Core import exaBoxCoreInit
from exabox.ovm.vmcontrol import exaBoxOVMCtrl
from time import sleep
from datetime import datetime
from base64 import b64decode
import hashlib
import re
import json, copy, socket
import decimal
from exabox.core.DBStore import ebGetDefaultDB
from .cludbaas import ebCluDbaas
from multiprocessing import Process
from .monitor import ebClusterNode

class ebCluSparseClone(object):

        def __init__(self, aExaBoxCluCtrl, aOptions):

            self.__config = get_gcontext().mGetConfigOptions()
            self.__basepath = get_gcontext().mGetBasePath()
            self.__clusterpath = None
            self.__xmlpath = aOptions.configpath
            self.__ebox = aExaBoxCluCtrl
            self.__domUs = []
            self.__jobid = None
            self.__logfile = None

            self.__clusterpath = self.__ebox.mGetClusterPath()
            self.__ddpair = self.__ebox.mReturnDom0DomUPair()

            self.__verbose = self.__ebox.mGetVerbose()
            
            for _, _dU in self.__ddpair:
                self.__domUs.append(_dU)

            # Object to store results
            self.__sparsedata = {}

            # Initialize for DBaaS API calls
            self.__dbaasobj = ebCluDbaas(self.__ebox, aOptions)

        # Dump the JSON object
        def _mUpdateRequestData(self, aOptions, aDataD, aEbox):
            _data_d = aDataD
            _eBox = aEbox
            _reqobj = _eBox.mGetRequestObj()
            if _reqobj is not None:
                _reqobj.mSetData(json.dumps(_data_d, sort_keys = True))
                _db = ebGetDefaultDB()
                _db.mUpdateRequest(_reqobj)
            elif aOptions.jsonmode:
                ebLogJson(json.dumps(_data_d, indent = 4, sort_keys = True))

        def mClusterSparseclone(self, aOptions):

            _options = aOptions
            _rc = 0

            _sparsedata = self.mGetSparseData()
            _sparsedata['Status'] = "Pass"
            _eBox = self.mGetEbox()

            if (_options.sparseclone is None):
                ebLogInfo("Invalid invocation or unsupported Sparse Clone option")
                _sparsedata["Log"] = "Invalid invocation or unsupported Sparse Clone option"
                _sparsedata["Status"] = "Fail"
                self._mUpdateRequestData(_options, _sparsedata, _eBox)
                return self.mRecordError("872")

            # Invoke right worker method
            if (_options.sparseclone == "tm_create"):
                ebLogInfo("Running Sparse Clone Step: Create Testmaster DB")
                _sparsedata["Command"] = "tm_create"
                _rc = self.mClusterTmCreate(_options)
            elif (_options.sparseclone == "snap_create"):
                ebLogInfo("Running Sparse Clone Step: Create Snapclone")
                _sparsedata["Command"] = "tm_create"
                _rc = self.mClusterSnapCreate(_options)
            elif (_options.sparseclone == "status"):
                ebLogInfo("Running Sparse Clone Step: Fetching status")
                _sparsedata["Command"] = "status"
                _rc = self.mClusterSparseStatus(_options)
            elif (_options.sparseclone == "tm_delete"):
                ebLogInfo("Running Sparse Clone Step: Deleting Testmaster DB")
                _sparsedata["Command"] = "tm_delete"
                _rc = self.mClusterTmDelete(_options)
            elif (_options.sparseclone == "snap_delete"):
                ebLogInfo("Running Sparse Clone Step: Deleting Snapclone")
                _sparsedata["Command"] = "snap_delete"
                _rc = self.mClusterSnapDelete(_options)
            else:
                ebLogInfo("Running Sparse Clone Step: Unsupported")
                _rc = self.mRecordError("872")
                _sparsedata["Log"] = "Sparse Clone Step: Unsupported"
                _sparsedata["Status"] = "Fail"

            self._mUpdateRequestData(_options, _sparsedata, _eBox)

            return _rc
        # end mSparseclone

        # Method to create a Testmaster DB
        def mClusterTmCreate(self, aOptions, aSparseData=None):

            _op = "Testmaster"
            return self.mClusterCreate(aOptions, _op)

        # end

        # Method to create a snapclone
        def mClusterSnapCreate(self, aOptions, aSparseData=None):

            _op = "Snapclone"
            return self.mClusterCreate(aOptions, _op)

        # end

        # Method to delete a Testmaster DB
        def mClusterTmDelete(self, aOptions, aSparseData=None):

            _op = "Testmaster"
            return self.mClusterDelete(aOptions, _op)

        # end

        # Method to delete a Snapclone
        def mClusterSnapDelete(self, aOptions, aSparseData=None):

            _op = "Snapclone"
            return self.mClusterDelete(aOptions, _op)

        # end

        # Generic method to execute testmaster and snapclone creation
        def mClusterCreate(self, aOptions, aOp, aSparseData=None):

            _options = aOptions
            _op = aOp
            _sourcedb = None
            _tmdb = None
            _clonedb = None
            _sourcepwd = None
            _async = False
            _eBox = self.mGetEbox()

            if aSparseData is None:
                _sparsedata = self.mGetSparseData()
            else:
                _sparsedata = aSparseData

            _sparsedata["Status"] = "Pass"
            _sparsedata["ErrorCode"] = "0"

            _inparams = {}
            _flag = True
            if _op == "Snapclone":
               _flag = False
            _rc = self.mClusterParseInput(_options, _inparams, _flag)
            if _rc == 0:
                if _op == "Testmaster":
                    _sourcedb = _inparams["sourcedb"]
                else:
                    _clonedb = _inparams["clonedb"]
                _tmdb = _inparams["tmdb"]
                if _inparams["passwd"]:
                    _sourcepwd = _inparams["passwd"]
                if "async" in list(_inparams.keys()):
                    _async = _inparams["async"]
            else:
                ebLogInfo("Returning due to input args related error")
                return _rc

            if _op == "Testmaster":
                _destdb = _tmdb
            else:
                _sourcedb = _tmdb
                _destdb = _clonedb

            step_list = ["Prepare", "Create", "Finalize", "Complete"]

            # If async request, do the operation in a single step
            if _async:
                ebLogInfo("*** Executing %s creation in asynchronous mode" %(_op))
                _rc = self.mExecuteFull(_options, _sourcedb, _destdb, _sourcepwd, _sparsedata, _op)
                if _sparsedata["Status"] == "Pass":
                    ebLogInfo("*** %s creation successfully initiated!" %(_op))
                    ebLogInfo("*** %s creation jobid is %s" %(_op, str(_rc)))
                    _sparsedata["jobid"] = str(_rc)
                    return 0
                else:
                    ebLogInfo("*** %s creation job could not be launched!" %(_op))
                    _sparsedata["jobid"] = "0"
                    return self.mRecordError("861")

            # Step1: Prepare domUs for Testmaster/Snapclone creation
            _eBox.mUpdateStatusOEDA(True, "Prepare", step_list, 'Preparing cluster for ' + _op + ' creation')
            ebLogInfo("*** Request: %s -- Step: Prepare" %(_op))
            _rc = self.mExecutePrepare(_options, _sourcedb, _destdb, _sourcepwd, _sparsedata, _op)
            if _rc == 0:
                ebLogInfo("*** Prepare step for %s succeeded!" %(_op))
                _sparsedata["Status"] = "Pass"
            else:
                ebLogInfo("*** Prepare step for %s failed!" %(_op))
                _sparsedata["Status"] = "Fail"
                return self.mRecordError("864")

            # Step2: Create the Testmaster/Snapclone
            _eBox.mUpdateStatusOEDA(True, "Create", step_list, 'Creating ' +_op + ' on cluster')
            ebLogInfo("*** Request: %s -- Step: Create" %(_op))
            _rc = self.mExecuteCreate(_options, _sourcedb, _destdb, _sourcepwd, _sparsedata, _op)
            if _rc == 0:
                ebLogInfo("*** Create step for %s succeeded!" %(_op))
                _sparsedata["Status"] = "Pass"
            else:
                ebLogInfo("*** Create step for %s failed!" %(_op))
                _sparsedata["Status"] = "Fail"
                return self.mRecordError("865")

            # Stepr3: Execute post-processing steps, if any
            _eBox.mUpdateStatusOEDA(True, "Finalize", step_list, 'Post creation setup for ' + _op)
            ebLogInfo("*** Request: %s -- Step: Finalize" %(_op))
            _rc = self.mExecuteFinalize(_options, _sourcedb, _destdb, _sourcepwd, _sparsedata, _op)
            if _rc == 0:
                ebLogInfo("*** Finalize step for %s succeeded!" %(_op))
                _sparsedata["Status"] = "Pass"
            else:
                ebLogInfo("*** Finalize step for %s failed!" %(_op))
                _sparsedata["Status"] = "Fail"
                return self.mRecordError("866")

            _eBox.mUpdateStatusOEDA(True, "Complete", step_list, _op + ' Create Completed')
            return _rc

        # end

        # Generic method to execute testmaster and snapclone deletion
        def mClusterDelete(self, aOptions, aOp, aSparseData=None):

            _options = aOptions
            _op = aOp
            _sourcedb = None
            _tmdb = None
            _clonedb = None
            _sourcepwd = None
            _async = False
            _eBox = self.mGetEbox()

            if aSparseData is None:
                _sparsedata = self.mGetSparseData()
            else:
                _sparsedata = aSparseData

            _sparsedata["Status"] = "Pass"
            _sparsedata["ErrorCode"] = "0"

            _inparams = {}
            _rc = self.mClusterParseDbInput(_options, _inparams)
            if _rc == 0:
                _sourcedb = _inparams["dbname"]
            else:
                ebLogInfo("Returning due to input args related error")
                return _rc

            step_list = ["Delete", "Complete"]

            _eBox.mUpdateStatusOEDA(True, "Delete", step_list, 'Delete operation for ' + _op)
            ebLogInfo("*** Request: %s -- Step: Delete" %(_op))
            _rc = self.mExecuteDelete(_options, _sourcedb, _sparsedata, _op)
            if _rc == 0:
                ebLogInfo("*** Delete step for %s succeeded!" %(_op))
                _sparsedata["Status"] = "Pass"
            else:
                ebLogInfo("*** Delete step for %s failed!" %(_op))
                _sparsedata["Status"] = "Fail"
                return self.mRecordError("870")

            _eBox.mUpdateStatusOEDA(True, "Complete", step_list, _op + ' Delete Completed')
            return _rc

        # end

        # Method to prepare domU for Testmaster creation
        # Can be done via caller - but better to have a separate method per-step
        # so any custom code can be added in future
        def mExecutePrepare(self, aOptions, aSourcedb, aDestdb, aSourcepwd, aSparsedata, aOp):

            _step = "prepare"
            return self.mExecuteStep(aOptions, aSourcedb, aDestdb, aSourcepwd, aSparsedata, aOp, _step)

        # end

        def mExecuteCreate(self, aOptions, aSourcedb, aDestdb, aSourcepwd, aSparsedata, aOp):

            _step = "create"
            return self.mExecuteStep(aOptions, aSourcedb, aDestdb, aSourcepwd, aSparsedata, aOp, _step)

        # end

        def mExecuteFinalize(self, aOptions, aSourcedb, aDestdb, aSourcepwd, aSparsedata, aOp):

            _step = "finalize"
            return self.mExecuteStep(aOptions, aSourcedb, aDestdb, aSourcepwd, aSparsedata, aOp, _step)

        # end

        def mExecuteFull(self, aOptions, aSourcedb, aDestdb, aSourcepwd, aSparsedata, aOp):

            _step = "async"
            return self.mExecuteStep(aOptions, aSourcedb, aDestdb, aSourcepwd, aSparsedata, aOp, _step)

        # end

        def mExecuteDelete(self, aOptions, aSourcedb, aSparsedata, aOp):

            _step = "delete"
            return self.mExecuteDeleteStep(aOptions, aSourcedb, aSparsedata, aOp, _step)

        # end

        # Method to parse input JSON and validate the arguments
        def mClusterParseInput(self, aOptions, aReqParams, aTmCreate):

            _options = aOptions
            _reqparams = aReqParams

            # Input JSON file is required
            _inputjson = _options.jsonconf
            if not _inputjson:
                return self.mRecordError("851")
            elif ('SOURCEDB' not in (key.upper() for key in list(_inputjson.keys()))) and aTmCreate:
                return self.mRecordError("852")
            elif 'TMDB' not in (key.upper() for key in list(_inputjson.keys())):
                return self.mRecordError("853")
            elif ('PASSWD' not in (key.upper() for key in list(_inputjson.keys()))) and aTmCreate:
                return self.mRecordError("860")
            elif ('CLONEDB' not in (key.upper() for key in list(_inputjson.keys()))) and not aTmCreate:
                return self.mRecordError("867")

            for key in list(_inputjson.keys()):
                if 'SOURCEDB' == key.upper():
                    _reqparams["sourcedb"] = _inputjson[key]
                if 'TMDB' == key.upper():
                    _reqparams["tmdb"] = _inputjson[key]
                if 'CLONEDB' == key.upper():
                    _reqparams["clonedb"] = _inputjson[key]
                if 'PASSWD' == key.upper():
                    _reqparams["passwd"] = _inputjson[key]
                if ('ASYNC' == key.upper()) and (_inputjson[key].upper() == 'TRUE'):
                    _reqparams["async"] = True

            """
            _dblistdata = {}
            _iormobj = ebCluResManager(self.__ebox, _options)
            _iormobj.mClusterDbList(_options, _dblistdata)
            if _dblistdata["Status"] == "Fail":
                return self.mRecordError("854")

            _dbstring = _dblistdata["DbSet"]
            _dblist = _dbstring.split(",")

            # Make sure sourceDB exists
            if ("sourcedb" in _reqparams.keys()) and (_reqparams["sourcedb"].upper() not in _dblist):
                return self.mRecordError("855", " : " + _reqparams["sourcedb"])

            # In case of Testmaster creation, Testmaster DB name should be available
            if aTmCreate and (_reqparams["tmdb"].upper() in _dblist):
                return self.mRecordError("856", " : " + _reqparams["tmdb"])
            elif not aTmCreate and (_reqparams["tmdb"].upper() not in _dblist):
                return self.mRecordError("868", " : " + _reqparams["tmdb"])

            # Snapclone DB name should be available
            if ("clonedb" in _reqparams.keys()) and (_reqparams["clonedb"].upper() in _dblist):
                return self.mRecordError("869", " : " + _reqparams["clonedb"])
            """

            return 0

        # end

        # Method to parse input JSON and validate the arguments for delete operations
        def mClusterParseDbInput(self, aOptions, aReqParams):

            _options = aOptions
            _reqparams = aReqParams

            # Input JSON file is required
            _inputjson = _options.jsonconf
            if not _inputjson or not _inputjson['dbParams']:
                return self.mRecordError("851")
            _dbparams = _inputjson['dbParams']
            if ('DBNAME' not in (key.upper() for key in list(_dbparams.keys()))):
                return self.mRecordError("852")

            for key in list(_dbparams.keys()):
                if 'DBNAME' == key.upper():
                    _reqparams["dbname"] = _dbparams[key]

            return 0

        # end    

        # Method to fetch status of a Job
        def mClusterSparseStatus(self, aOptions, aSparseData=None):

            _options = aOptions
            _jobid = None
            _sourcedb = None
            _dbaasobj = self.mGetDbaasObj()

            if aSparseData is None:
                _sparsedata = self.mGetSparseData()
            else:
                _sparsedata = aSparseData

            _sparsedata["Status"] = "Pass"
            _sparsedata["ErrorCode"] = "0"

            # Job ID is mandatory
            _jobid = _options.id

            if not _jobid or (_jobid.isdigit() == False):
                return self.mRecordError("862")

            # Get the operation name for which status is queried
            _jsonPload = _options.jsonconf
            _op = _jsonPload["operation"]
            
            # Source DB SID is required
            _sourcedb = _options.dbsid

            if not _sourcedb:
                return self.mRecordError("852")            

            if self.__verbose:
                ebLogInfo("*** Fetching status for job ID %s" %(_jobid))

            _outfile = "/var/opt/oracle/log/" + _sourcedb + "/dbaas_status.out"
            
            _ebox = self.mGetEbox()
            _uuid = _ebox.mGetUUID()
            _inputJsonFilename = None
            _inputJsonFilename = "/dbaas_input_" + _uuid + ".json"

            _domUs = self.mGetDomUs()

            for _domU in _domUs:

                _destdb = ""

                # Invoke status call
                _status = _dbaasobj.mWaitForJobComplete(_options, _sourcedb, _domU, _jobid, _sparsedata, _op, _inputJsonFilename, _outfile, None)
                if _status == 0:
                    ebLogInfo("*** Status of jobid %s is %s" %(_jobid, _sparsedata["Status"]))
                    return 0
                else:
                    return self.mRecordError("863")

                break # One domU will suffice

        # end

        # Method to prepare domU for Testmaster creation
        def mExecuteStep(self, aOptions, aSourcedb, aDestdb, aSourcepwd, aSparsedata, aOp, aStep):

            _options = aOptions
            _sourcedb = aSourcedb
            _destdb = aDestdb
            _sourcepwd = aSourcepwd
            _ebox = self.mGetEbox()
            _dbaasobj = self.mGetDbaasObj()
            
            _sparsedata = aSparsedata
            _op = aOp

            _step = aStep
            _injson = {}

            _validSteps = ["prepare", "create", "finalize", "async"]
            if _step not in _validSteps:
                ebLogInfo("*** Invalid step specificed for %s creation" %(_op))
                return -1

            _outfile = "/var/opt/oracle/log/" + _sourcedb +"/sparse_create.out"

            # Gather the parameters required for dbaasapi
            # 1. Source DB name in case of Testmaster
            # 2. Testmaster DB name
            # 3. Clone DB name in case of Snapclone
            # 4. Password of Source DB in case of Testmaster
            # 5. DomU-list
            # 6. Scan IP list
            _domulist = None

            _injson["object"] = "db"
            _injson["action"] = "begin"
            if _op == "Testmaster":
                _dbOp = "snapshot"
            else:
                _dbOp = "clone"

            _injson["operation"] = _dbOp
            _injson["params"] = {}
            _injson["params"]["dbname"] = _sourcedb
            _injson["params"]["dest_dbname"] = _destdb
            # In case of Testmaster, passwd is mandatory
            if _sourcepwd is not None:
                _injson["params"]["passwd"] = _sourcepwd
            if _step != "async":
                _injson["params"]["step"] = _step
            _injson["params"]["scope"] = "local"

            if (_op == "Testmaster") and ((_step == "prepare") or (_step == "async")):
                _injson["params"]["vm_map"] = {}
                _dom0U_list = _ebox.mReturnDom0DomUPair()
                for _, _domU in _dom0U_list:
                    _domU = _domU.split(".")[0]
                    _injson["params"]["vm_map"][_domU] = _domU

                _cluster = _ebox.mGetClusters().mGetCluster()
                _clu_scans = _cluster.mGetCluScans()

                _scan_ips = []
                for _scann in _clu_scans:
                    _scano = _ebox.mGetScans().mGetScan(_scann)
                    _scan_ips += _scano.mGetScanIps()

                _injson["params"]["scan_ip_map"] = {}
                for _scan_ip in _scan_ips:
                    _injson["params"]["scan_ip_map"][_scan_ip] = _scan_ip

            _injson["outputfile"] = _outfile
            _injson["FLAGS"] = ""

            if self.__verbose:
                ebLogInfo("*** The input JSON for %s %s is" %(_op, _step))
                ebLogJson(json.dumps(_injson, indent = 4, sort_keys = True))

            _domUs = self.mGetDomUs()

            _uuid = _ebox.mGetUUID()
            _input_file = "/tmp/sparse_input_" + _uuid + ".json"

            with open(_input_file, 'w') as infile:
                json.dump(_injson, infile, sort_keys = True, skipkeys = True, indent = 4, ensure_ascii=False)

            # Initiate the step
            _cmd = "nohup /var/opt/oracle/dbaasapi/dbaasapi -i /var/opt/oracle/log/" + _sourcedb + "/sparse_input_" + _uuid + ".json < /dev/null > /dev/null 2>&1"
            for _domU in _domUs:
                # Copy the input json file to the domU
                _dbaasobj.mCopyFileToDomU(_domU, _sourcedb, _destdb, _input_file)

                # It's ok to clean this here because we only use this once
                _ebox.mExecuteLocal("/bin/rm -f "+_input_file)

                # Execute the step
                _i, _o, _e = _dbaasobj.mExecCommandOnDomU(_domU, _options, _cmd)
                if str(_e) == "0":
                    _sparsedata["Status"] = "Pass"
                else:
                    _logmsg = "*** Failed to execute command to " + _step + " " + _op + " creation" 
                    ebLogInfo("%s" %(_logmsg))
                    _sparsedata["Log"] = _logmsg
                    _sparsedata["Status"] = "Fail"

                # Read the job ID 
                _idobj = _dbaasobj.mReadStatusFromDomU(_options, _domU, _outfile)
                if not _idobj or ("id" not in _idobj):
                    _logmsg = "*** Failed to read Job ID from domU"
                    ebLogInfo("%s" %(_logmsg))
                    _sparsedata["Log"] = _logmsg
                    _sparsedata["Status"] = "Fail"
                    return -1

                _jobid = _idobj["id"]
                self.mSetJobId(_jobid)

                if "logfile" in _idobj:
                    self.mSetLogFile(_idobj["logfile"])

                # Return here if we are in async mode
                if _step == "async":
                    _sparsedata["Log"] = "*** " + _op + " creation successfully initiated"
                    _sparsedata["Status"] = "Pass"
                    return int(_jobid)
                
                # Wait for step to complete
                _outfile = "/var/opt/oracle/log/" + _sourcedb + "/dbaas_status.out"
                _inputJsonFilename = _sourcedb + "/dbaas_input_" + _uuid + ".json"
                _status = _dbaasobj.mWaitForJobComplete(_options, _sourcedb, _domU, _jobid, _sparsedata, _op, _inputJsonFilename, _outfile, None)
                _dbaasobj.mCopyDomuLogs(_options, _domU, _destdb, _sparsedata, _op, _step, self.mGetLogFile())
                if _status == 0:
                    _logmsg = "*** " + _step + " operation for " + _op + " succeeded"
                    _sparsedata["Log"] = _logmsg
                    _sparsedata["Status"] = "Pass"
                    return 0

                # Undo the step
                if self.__verbose:
                    _logmsg = "*** " + _step + " " + _op +" failed. Undoing..."
                    ebLogInfo("%s" %(_logmsg))

                if _op == "Testmaster":
                    _stepundo = _step+"-undo"
                else:
                    _stepundo = "undo-"+_step
                _injson["params"]["step"] = _stepundo

                if _step == "prepare":
                    _injson["params"].pop("vm_map", None)
                    _injson["params"].pop("scan_ip_map", None)

                if self.__verbose:
                    ebLogInfo("*** The input JSON for %s %s is" %(_op, _stepundo) )
                    ebLogJson(json.dumps(_injson, indent = 4, sort_keys = True))

                _i, _o, _e = _dbaasobj.mExecCommandOnDomU(_domU, _options, _cmd) #_cmd remains same
                if str(_e) == "0":
                    _sparsedata["Status"] = "Pass"
                else:
                    _logmsg = "*** Failed to execute command to " + _stepundo + " " + _op + " operation"
                    ebLogInfo("%s" %(_logmsg))
                    _sparsedata["Log"] = _logmsg
                    _sparsedata["Status"] = "Fail"

                # Read the job ID 
                _idobj = _dbaasobj.mReadStatusFromDomU(_options, _domU, _outfile)
                if not _idobj or ("id" not in _idobj):
                    _logmsg = "*** Failed to read Job ID from domU"
                    ebLogInfo("%s" %(_logmsg))
                    _sparsedata["Log"] = _logmsg
                    _sparsedata["Status"] = "Fail"
                    return -1

                _jobid = _idobj["id"]
                self.mSetJobId(_jobid)

                if "logfile" in _idobj:
                    self.mSetLogFile(_idobj["logfile"])

                ebLogInfo("Job ID is %s" %(_jobid))

                # Wait for undo step to complete
                _outfile = "/var/opt/oracle/log/" + _sourcedb + "/dbaas_status.out"
                _inputJsonFilename = _sourcedb + "/dbaas_input_" + _uuid + ".json"
                _status = _dbaasobj.mWaitForJobComplete(_options, _sourcedb, _domU, _jobid, _sparsedata, _op, _inputJsonFilename, _outfile, None)
                _dbaasobj.mCopyDomuLogs(_options, _domU, _destdb, _sparsedata, _op, _stepundo, self.mGetLogFile())
                if _status == 0:
                    _logmsg = "*** " + _stepundo + " operation for " + _op + " succeeded"
                    _sparsedata["Log"] = _logmsg
                    _sparsedata["Status"] = "Pass"
                    return 0
                else:
                    _logmsg = "*** " + _stepundo + " operation for " + _op + " failed"
                    _sparsedata["Log"] = _logmsg
                    _sparsedata["Status"] = "Fail"
                    return -1

                break # Only on 1 domU is enough
           
        # end

        # Method to execute undo operation for any step (used only for delete tm/snap as of now)
        def mExecuteDeleteStep(self, aOptions, aSourcedb, aSparsedata, aOp, aStep):

            _options = aOptions
            _sourcedb = aSourcedb
            _ebox = self.mGetEbox()
            _dbaasobj = self.mGetDbaasObj()
            
            _sparsedata = aSparsedata
            _op = aOp
            _step = aStep
            _injson = {}

            if _step != "delete":
                ebLogInfo("*** Invalid step specified for %s deletion" %(_op))
                return -1

            _outfile = "/var/opt/oracle/log/" + _sourcedb +"/sparse_delete.out"

            # Gather the parameters required for dbaasapi
            # 1. Source DB name
            _domulist = None

            _injson["object"] = "db"
            _injson["action"] = "delete"
            if _op == "Testmaster":
                _injson["operation"] = "snapshot"
            else:
                _injson["operation"] = "clone"

            _injson["params"] = {}
            _injson["params"]["dbname"] = _sourcedb
            _injson["params"]["scope"] = "local"

            _injson["outputfile"] = _outfile
            _injson["FLAGS"] = ""

            if self.__verbose:
                ebLogInfo("*** The input JSON for %s delete is" %(_op))
                ebLogJson(json.dumps(_injson, indent = 4, sort_keys = True))

            _domUs = self.mGetDomUs()

            _uuid = _ebox.mGetUUID()
            _input_file = "/tmp/sparse_delete_input_" + _uuid + ".json"

            with open(_input_file, 'w') as infile:
                json.dump(_injson, infile, sort_keys = True, skipkeys = True, indent = 4, ensure_ascii=False)

            # Initiate the step
            _cmd = "nohup /var/opt/oracle/dbaasapi/dbaasapi -i /var/opt/oracle/log/sparse_delete_input_" + _uuid + ".json < /dev/null > /dev/null 2>&1"
            for _domU in _domUs:
                # Copy the input json file to the domU
                _dbaasobj.mCopyFileToDomU(_domU, _sourcedb, None, _input_file)

                # It's ok to clean this here because we only use this once
                _ebox.mExecuteLocal("/bin/rm -f "+_input_file)

                # Execute the step
                _i, _o, _e = _dbaasobj.mExecCommandOnDomU(_domU, _options, _cmd)
                if str(_e) == "0":
                    _sparsedata["Status"] = "Pass"
                else:
                    _logmsg = "*** Failed to execute command for " + _op + " deletion" 
                    ebLogInfo("%s" %(_logmsg))
                    _sparsedata["Log"] = _logmsg
                    _sparsedata["Status"] = "Fail"

                # Read the job ID 
                _idobj = _dbaasobj.mReadStatusFromDomU(_options, _domU, _outfile)
                if not _idobj or ("id" not in _idobj):
                    _logmsg = "*** Failed to read Job ID from domU"
                    ebLogInfo("%s" %(_logmsg))
                    _sparsedata["Log"] = _logmsg
                    _sparsedata["Status"] = "Fail"
                    return -1

                _jobid = _idobj["id"]
                self.mSetJobId(_jobid)

                if "logfile" in _idobj:
                    self.mSetLogFile(_idobj["logfile"])

                # Wait for step to complete
                _outfile = "/var/opt/oracle/log/" + _sourcedb + "/dbaas_status.out"
                _inputJsonFilename = "/dbaas_input_" + _uuid + ".json"
                _status = _dbaasobj.mWaitForJobComplete(_options, _sourcedb, _domU, _jobid, _sparsedata, _op, _inputJsonFilename, _outfile, None)
                _dbaasobj.mCopyDomuLogs(_options, _domU, _sourcedb, _sparsedata, _op, _step, self.mGetLogFile())
                if _status == 0:
                    _logmsg = "*** Delete operation for " + _op + " succeeded"
                    _sparsedata["Log"] = _logmsg
                    _sparsedata["Status"] = "Pass"
                    return 0
                else:
                    _logmsg = "*** Delete operation for " + _op + " failed"
                    _sparsedata["Log"] = _logmsg
                    _sparsedata["Status"] = "Fail"
                    return -1

                break # Only on 1 domU is enough
           
        # end

        # Common method to log error code and error message
        def mRecordError(self, aErrorCode, aString=None):

            _sparsedata = self.mGetSparseData()

            _sparsedata["Status"] = "Fail"
            _sparsedata["ErrorCode"] = aErrorCode
            _errorCode = int(_sparsedata["ErrorCode"], 16)
            if aString is None:
                _sparsedata["Log"] = gSparseError[_sparsedata["ErrorCode"]][0]
            else:
                _sparsedata["Log"] = gSparseError[_sparsedata["ErrorCode"]][0] + aString

            ebLogInfo("%s" %(_sparsedata["Log"]))

            if _errorCode != 0:
                return ebError(_errorCode)
            return 0
        # end

        def mGetEbox(self):
            return self.__ebox

        def mGetDomUs(self):
            return self.__domUs

        def mSetDomUs(self, aDomUs):
            self.__domUs = aDomUs

        def mGetSparseData(self):
            return self.__sparsedata

        def mSetSparseData(self, aSparseData):
            self.__sparsedata = aSparseData

        def mGetJobId(self):
            return self.__jobid

        def mSetJobId(self, aJobId):
            self.__jobid = aJobId

        def mGetLogFile(self):
            return self.__logfile

        def mSetLogFile(self, aLogFile):
            self.__logfile = aLogFile

        def mGetDbaasObj(self):
            return self.__dbaasobj

        def mSetDbaasObj(self, aDbaasObj):
            self.__dbaasobj = aDbaasObj

# end of ebCluSparseClone
