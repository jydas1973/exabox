"""
 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    OVM - DBaaS API related functionality

FUNCTION:
    Module to provide access to DBaaS APIs via Exacloud

NOTE:
    None

History:
    aararora    08/07/2025 - ER 37858683: Add tcps config if present in the payload
    abflores    06/18/2025 - Bug 37508725 - IMPROVE PORT SCAN
    nelango     05/15/2025 - Bug 37566779 - Get ora errors during storage resize
    pbellary    04/04/2025 - Bug 37671564 - DB INSTANCES ARE GETTING DELETED ONLY IF STATUS IS OPEN
    aararora    04/02/2025 - Bug 37726464 - Correct path for dbaas api log
    pbellary    10/09/2024 - Bug 37145972 - EXASCALE: CREATE-SERVICE DID NOT CATCH INCORRECT STATUS IN DBAASCLI ADMIN INITIALIZECLUSTER 
    sdevasek    09/23/2024 - ENH 36654974 - ADD CDB HEALTH CHECKS DURING DOM0
                             INFRA PATCHING
    pbellary    08/21/2024 - 36974106 - ENHANCE CS FLOW FOR EXASCALE CLUSTER TO ADD REQUIRED FIELDS THE GRID.INI FILE. 
    akkar       06/18/2024 - 36397179: class for dbaascli commands
    sdevasek    01/30/2024 - 35306246: Add db health checks during domu os 
                             patching
    rajsag      09/27/2021 - 33231316: dbaas logs not getting copied to exacloud 
    dekuckre    10/25/2021 - 33498594: Remove dependency on non-root user
    dekuckre    06/05/2021 - 32205492: Update mExecuteDBaaSAPIAction
    dekuckre    06/25/2020 - Add 31537710.
    dekuckre    05/06/2019 - XbranchMerge dekuckre_bug-29617988 from
                             st_ebm_19.1.1.1.0   
    dekuckre    12/03/2018 - 28429399: Add mExecuteDBaaSAPIAction
    pverma      04/07/2017 - Modifications to generalize a few
                             functions to make it usable for 
                             modules other than sparse
    hnvenkat    11/24/2016 - Create file

Changelog:

   11/24/2016 - v1 changes:

"""
from exabox.core.Node import exaBoxNode
from exabox.core.Error import gDbaasError
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace
from exabox.log.LogMgr import ebLogJson
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure
import time, os, re
from exabox.core.Context import get_gcontext
import json
import traceback
from exabox.core.DBStore import ebGetDefaultDB
from exabox.utils.node import connect_to_host, node_cmd_abs_path_check, node_exec_cmd_check, node_exec_cmd
from typing import Dict, Optional

STATUS_PASS = "Pass"
STATUS_FAIL = "Fail"
FAILURE_RC = -1
SUCCESS_RC = 0

class ebCluDbaas(object):

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
        self.__dbaasdata = {}

    
    def mGetEbox(self):
        return self.__ebox

    def mGetDbaasData(self):
        return self.__dbaasdata

    def mSetDbaasData(self, aDbaasData):
        self.__Dbaasdata = aDbaasData

    def mGetDomUs(self):
        return self.__domUs

    def mSetDomUs(self, aDomUs):
        self.__domUs = aDomUs

    def mGetJobId(self):
        return self.__jobid

    def mSetJobId(self, aJobId):
        self.__jobid = aJobId

    def mGetLogFile(self):
        return self.__logfile

    def mSetLogFile(self, aLogFile):
        self.__logfile = aLogFile
        
    
    # Dump the JSON object
    def _mUpdateRequestData(self, aOptions, aDataD, aEbox):
        _data_d = aDataD
        _eBox = aEbox
        _reqobj = _eBox.mGetRequestObj()
        if _reqobj is not None:
            _reqobj.mSetData(json.dumps(_data_d, sort_keys=True))
            _db = ebGetDefaultDB()
            _db.mUpdateRequest(_reqobj)
        elif aOptions.jsonmode:
            ebLogJson(json.dumps(_data_d, indent=4, sort_keys=True))

    def mClusterDbaas(self, aOptions, aCmd, aDbaasdata=None):

        _options = aOptions
        _acmd = aCmd
        _rc = SUCCESS_RC

        if aDbaasdata is None:
            _dbaasdata = self.mGetDbaasData()
        else:
            _dbaasdata = aDbaasdata
            self.mSetDbaasData(_dbaasdata)

        _dbaasdata['Status'] = STATUS_PASS
        _eBox = self.mGetEbox()

        if (_options.dbaas is None) and (_acmd not in ("db_info", "cprops_update")):
            ebLogInfo("Invalid invocation or unsupported DBaaS API option")
            _rc = FAILURE_RC
            _dbaasdata["Log"] = "Invalid invocation or unsupported DBaaS API option"
            _dbaasdata["Status"] = STATUS_FAIL
            self._mUpdateRequestData(_options, _dbaasdata, _eBox)
            return _rc

        # Invoke right worker method
        if (_options.dbaas == "dbinfo") or (_acmd == "db_info"):
            ebLogInfo("Running Step: Fetch DB Info")
            _dbaasdata["Command"] = "dbinfo"
            _rc = self.mClusterDbInfo(_options, _dbaasdata)
        elif _acmd == "cprops_update":
            ebLogInfo("Running Step: Update Cloud properties")
            _dbaasdata["Command"] = "cprops_update"
            # Update cloud props
            _rc = self.mUpdateCprops(_options, "update", _dbaasdata)
            if _rc == SUCCESS_RC:
                ebLogInfo("Running Step: Update TFA properties")
                _dbaasdata["Command"] = "tfa_props_update"

                # Update tfactl properties
                _rc = self.mUpdateCprops(_options, "update_tfactl", _dbaasdata)
        else:
            ebLogInfo("Running DBaaS API Step: Unsupported")
            _rc = FAILURE_RC
            _dbaasdata["Log"] = "DBaaS Step: Unsupported"
            _dbaasdata["Status"] = STATUS_FAIL

        self._mUpdateRequestData(_options, _dbaasdata, _eBox)

        return _rc
    # end mClusterDbaas

    # Generic method to fetch DB Info
    def mClusterDbInfo(self, aOptions, aDbaasData=None):

        _options = aOptions
        _sourcedb = None
        _eBox = self.mGetEbox()

        if aDbaasData is None:
            _dbaasdata = self.mGetDbaasData()
        else:
            _dbaasdata = aDbaasData

        _dbaasdata["Status"] = STATUS_PASS

        _dbaasdata["ErrorCode"] = "0"

        _inparams = {}
        _rc = self.mClusterParseDbInfoInput(_options, _inparams)
            
        if _rc == SUCCESS_RC:
            if _inparams["mode"] == "all":
                _sourcedb = None
            else:
                _sourcedb = _inparams["dbname"]
        else:
            ebLogInfo("Returning due to input args related error")
            return _rc

        step_list = ["InfoFetch", "Complete"]

        if _sourcedb is not None:
            _eBox.mUpdateStatusOEDA(True, "InfoFetch", step_list, 'DbInfo Fetch operation for ' + _sourcedb)
            ebLogInfo("*** Database: %s -- Step: InfoFetch" % (_sourcedb))
        else:
            _eBox.mUpdateStatusOEDA(True, "InfoFetch", step_list, 'DbInfo Fetch operation for ALL databases in the cluster')
            ebLogInfo("*** Database: [ALL DBs in the cluster] -- Step: InfoFetch")
            
        _rc = self.mExecuteDbInfo(_options, _dbaasdata, _sourcedb)
        if _sourcedb is None:
            _sourcedb = "ALL Cluster DBs"

        if _rc == SUCCESS_RC:
            ebLogInfo("*** DbInfo Fetch for %s succeeded!" % (_sourcedb))
            _dbaasdata["Status"] = STATUS_PASS
        else:
            ebLogInfo("*** DbInfo Fetch for %s failed!" % (_sourcedb))
            _dbaasdata["Status"] = STATUS_FAIL
            return self.mRecordError("911")

        _eBox.mUpdateStatusOEDA(True, "Complete", step_list, _sourcedb + ' DbInfo Fetch Completed')
        return _rc

    # end

    def mUpdateCprops(self, aOptions, aAction, aDbaasData=None):

        _options = aOptions
        _eBox = self.mGetEbox()

        if aDbaasData is None:
            _dbaasdata = self.mGetDbaasData()
        else:
            _dbaasdata = aDbaasData

        _dbaasdata["Status"] = STATUS_PASS
        _dbaasdata["ErrorCode"] = "0"

        _inparams = {}
        _rc = self.mClusterParseDbInfoInput(_options, _inparams)

        if _rc != SUCCESS_RC:
            ebLogInfo("DIAG Returning due to input args related error")
            return _rc
        _command = _dbaasdata["Command"]
        _steplist = [_command, "Complete"]

        _eBox.mUpdateStatusOEDA(True, _command, _steplist, 'Update Cloud properties ')
        ebLogInfo("*** DIAG -- Step: " + _command)

        if aAction == "update_tfactl":
            _inparams = self.mParseTfaInput(_inparams)

        _rc = self.mExecuteUpdateCprops(_options, _dbaasdata, _inparams, aAction)
        if _rc == SUCCESS_RC:
            ebLogInfo("*** DIAG Dbaas API operation " + _command + " succeeded!")
            _dbaasdata["Status"] = STATUS_PASS
        else:
            ebLogInfo("*** DIAG Dbaas API operation " + _command + " failed!")
            _dbaasdata["Status"] = STATUS_FAIL
            return self.mRecordError("904")

        _eBox.mUpdateStatusOEDA(True, "Complete", _steplist, _command + ' Completed')
        return _rc


    # Method to execute DB Info Fetch command of dbaasapi
    def mExecuteDbInfo(self, aOptions, aDbaasdata, aSourcedb=None):

        _options = aOptions
        _sourcedb = aSourcedb
        _ebox = self.mGetEbox()

        _dbaasdata = aDbaasdata
        _injson = {}
        _infoobj = {}
        _logmsg = ""

        _dbname = ""
        _dbname_for_status = ""
        if _sourcedb is None:
            _dbname_for_status = "grid"
        else:
            _dbname_for_status = _sourcedb

        _uuid = _ebox.mGetUUID()
        _outfile = "/var/opt/oracle/log/dbinfo" + _uuid + "_outfile.out"
        _infofile = "/var/opt/oracle/log/dbinfo" + _uuid + "_infofile.out"

        # Gather the parameters required for dbaasapi
        # 1. Source DB name
        _domulist = None

        _injson["object"] = "db"
        _injson["action"] = "get"
        _injson["operation"] = "info"

        _injson["params"] = {}

        if _sourcedb is None:
            _injson["params"]["mode"] = "all"
            _sourcedb = "ALL cluster DBs"
        else:
            _injson["params"]["dbname"] = _sourcedb
        _injson["params"]["infofile"] = _infofile

        _injson["outputfile"] = _outfile
        _injson["FLAGS"] = ""

        if self.__verbose:
            ebLogInfo("*** The input JSON for Info Fetch for DB %s is" % (_dbname))
            ebLogJson(json.dumps(_injson, indent=4, sort_keys=True))

        _domUs = self.mGetDomUs()

        _info_input_file = "/tmp/db_infofetch_input_" + _uuid + ".json"

        with open(_info_input_file, 'w') as infile:
            json.dump(_injson, infile, sort_keys=True, skipkeys=True, indent=4, ensure_ascii=False)
        # Initiate the step
        _cmd = "nohup /var/opt/oracle/dbaasapi/dbaasapi -i /var/opt/oracle/log/db_infofetch_input_" + _uuid + ".json < /dev/null > /dev/null 2>&1"
        for _domU in _domUs:

            _node = exaBoxNode(get_gcontext())
            if not _node.mIsConnectable(aHost=_domU):
                _logmsg += f"DomU {_domU} is not connectable; "
                continue

            # Copy the input json file to the domU
            self.mCopyFileToDomU(_domU, _dbname, None, _info_input_file)

            # Execute the step
            _i, _o, _e = self.mExecCommandOnDomU(_domU, _options, _cmd)
            if str(_e) == "0":
                _dbaasdata["Status"] = STATUS_PASS
            else:
                _logmsg = "*** Failed to execute command for " + _dbname + " Info Fetch"
                ebLogInfo("%s" % (_logmsg))
                _dbaasdata["Log"] = _logmsg
                _dbaasdata["Status"] = STATUS_FAIL

            # Read the job ID
            _idobj = self.mReadStatusFromDomU(_options, _domU, _outfile)
            if not _idobj or ("id" not in _idobj):
                _logmsg = "*** Failed to read Job ID from domU"
                ebLogInfo("%s" % (_logmsg))
                _dbaasdata["Log"] = _logmsg
                _dbaasdata["Status"] = STATUS_FAIL
                return FAILURE_RC

            _jobid = _idobj["id"]
            self.mSetJobId(_jobid)

            if "logfile" in _idobj:
                self.mSetLogFile(_idobj["logfile"])

            _infoobj = {}
            # Wait for step to complete
            _status_input_file = "db_info_status_input_" + _uuid + ".json" 
            _status = self.mWaitForJobComplete(_options, _dbname_for_status, _domU, _jobid, _dbaasdata, "info", _status_input_file, _outfile,  _infofile)
            if _status == SUCCESS_RC:
                _logmsg = "*** Info fetch operation for " + _sourcedb + " succeeded on Node " + _domU
                _dbaasdata["Log"] = _logmsg
                _dbaasdata["Status"] = STATUS_PASS
                _node_infoobj = self.mReadStatusFromDomU(_options, _domU, _infofile)
                if _node_infoobj:
                    if self.__verbose:
                        ebLogJson(json.dumps(_node_infoobj, indent=4, sort_keys=True))
                    _infoobj.update(_node_infoobj)
                else:
                    _logmsg = "DB Info not available in cloud metadata"
            else:
                _logmsg = "*** Info fetch operation for " + _sourcedb + " failed"
                _dbaasdata["Log"] = _logmsg
                _dbaasdata["Status"] = STATUS_FAIL
                self.mCopyDomuInfoLog(_options, _domU, self.mGetLogFile(), _infofile) 
                return FAILURE_RC

        _ebox.mExecuteLocal("/bin/rm -f " + _info_input_file)

        if not _infoobj:
            _logmsg = f"*** Could not get DB info: {_logmsg}"
            _dbaasdata["Log"] = _logmsg
            _dbaasdata["Status"] = STATUS_FAIL
            return FAILURE_RC

        if self.__verbose:
            ebLogJson(json.dumps(_infoobj, indent=4, sort_keys=True))
        _dbaasdata["DbInfo"] = {}
        _dbaasdata["DbInfo"] = _infoobj
        return SUCCESS_RC

    # end


    def mExecuteUpdateCprops(self, aOptions, aDbaasdata, aInParams, aAction):

        _options = aOptions
        _ebox = self.mGetEbox()

        _dbaasdata = aDbaasdata
        _injson = {}

        _uuid = _ebox.mGetUUID()
        _command = _dbaasdata["Command"]
        _outfile = "/var/opt/oracle/log/" + _command + "_" + _uuid + "_outfile.out"
        _infofile = "/var/opt/oracle/log/" + _command + "_" + _uuid + "_infofile.out"

        # Gather the parameters required for dbaasapi
        _domulist = None

        _injson["object"] = "os"
        _injson["action"] = aAction
        _injson["operation"] = "cloud_properties"
        _injson["params"] = aInParams
        _injson["outputfile"] = _outfile
        _injson["FLAGS"] = ""

        if self.__verbose:
            ebLogInfo("*** DIAG - The input JSON for DBAAS API " + _command + " operation")
            ebLogJson(json.dumps(_injson, indent=4, sort_keys=True))

        _domUs = self.mGetDomUs()

        _info_input_file = "/tmp/" + _command + "_input_" + _uuid + ".json"

        with open(_info_input_file, 'w') as infile:
            json.dump(_injson, infile, sort_keys=True, skipkeys=True, indent=4, ensure_ascii=False)
        # Initiate the step
        _cmd = "nohup /var/opt/oracle/dbaasapi/dbaasapi -i /var/opt/oracle/log/" + _command + "_input_" + _uuid + ".json < /dev/null > /dev/null 2>&1"
        for _domU in _domUs:
            # Copy the input json file to the domU
            self.mCopyFileToDomU(_domU, None, None, _info_input_file)

            # Execute the step
            _i, _o, _e = self.mExecCommandOnDomU(_domU, _options, _cmd)
            if str(_e) == "0":
                _dbaasdata["Status"] = STATUS_PASS
            else:
                _logmsg = "*** DIAG Failed to execute command " + _command
                ebLogInfo("%s" % (_logmsg))
                _dbaasdata["Log"] = _logmsg
                _dbaasdata["Status"] = STATUS_FAIL

            # Read the job ID
            _idobj = self.mReadStatusFromDomU(_options, _domU, _outfile)
            if not _idobj or ("id" not in _idobj):
                _logmsg = "*** DIAG Failed to read Job ID from domU"
                ebLogInfo("%s" % (_logmsg))
                _dbaasdata["Log"] = _logmsg
                _dbaasdata["Status"] = STATUS_FAIL
                return FAILURE_RC

            _jobid = _idobj["id"]
            self.mSetJobId(_jobid)

            if "logfile" in _idobj:
                self.mSetLogFile(_idobj["logfile"])

            _infoobj = {}
            # Wait for step to complete
            _status_input_file = _command + "_status_input_" + _uuid + ".json"
            _status = self.mWaitForJobComplete(_options, None, _domU, _jobid, _dbaasdata, "cloud_properties", _status_input_file, _outfile,  _infofile, aInParams)
            if _status == SUCCESS_RC:
                _logmsg = "*** " + _command + " operation succeeded on Node " + _domU
                _dbaasdata["Log"] = _logmsg
                _dbaasdata["Status"] = STATUS_PASS
            else:
                _logmsg = "*** " + _command + " failed"
                _dbaasdata["Log"] = _logmsg
                _dbaasdata["Status"] = STATUS_FAIL
                self.mCopyDomuInfoLog(_options, _domU, self.mGetLogFile(), _infofile)
                return FAILURE_RC

        _ebox.mExecuteLocal("/bin/rm -f " + _info_input_file)
        if self.__verbose:
            ebLogJson(json.dumps(_infoobj, indent=4, sort_keys=True))
        return SUCCESS_RC

    def mParseTfaInput(self, aParams):
        ''' 
        Method to parse input required in the format for updating TFA properties
        '''

        _diag_dict = aParams.get("diag", None)
        _valid_tfa_props = ("logstash.port", "logstash.host", "oss.type", "oss.url", "oss.user", "oss.password", "oss.proxy", "tfaweb.url" )
        _response = {}
        if _diag_dict:
            ebLogInfo("*** DIAG Get input for updating TFA properties")
            for server_name in list(_diag_dict.keys()):
                _server_dict = _diag_dict.get(server_name)
                for key in list(_server_dict.keys()):
                    _new_key = key.replace("_", ".")
                    if "passwd" in _new_key:
                        _new_key = _new_key.replace("passwd", "password")
                    if _new_key == "tfaweb.host":
                        _new_key = "tfaweb.url"
                    if _new_key in _valid_tfa_props:
                        _response[_new_key] = _server_dict.get(key)
        return _response

    # Method to parse input JSON for DB Info operation.
    # For now, reuse the delete related method
    def mClusterParseDbInfoInput(self, aOptions, aReqParams):

        # Initialize 
        _options = aOptions
        _reqparams = aReqParams
        _inputjson = None

        if _options.jsonconf:
            _inputjson = _options.jsonconf
        
        if not _inputjson:
            return self.mRecordError("901")
        
        for key in list(_inputjson.keys()):
            _reqparams[key] = _inputjson[key]
            
        if self.__verbose:
            ebLogJson(json.dumps(_inputjson, indent=4, sort_keys=True))

        return SUCCESS_RC

    # end

    def mExecuteDBaaSAPIAction(self, aAction, aOperation, aDbaasdata, aDomU, aParams, aOptions, aRaiseError=True,
                               aUser=None):
        """
        Note: aUser variable has been added to allow commands to be executed on the remote node using opc user with
        sudo privileges. Be default, None is chosen for compatibility with existing caller. This variable is introduced
        primarily for infrapatching callers (for precheck and postcheck sanity_check apis)
        """
        _options = aOptions
        _action = aAction
        _operation = aOperation
        _params = aParams
        _domU = aDomU
        _dbname = "ALL_CLUSTER_DBS"
        _sourcedb = "ALL cluster DBs"
        
        _ebox = self.mGetEbox()

        _dbaasdata = aDbaasdata
        _injson = {}

        _uuid = _ebox.mGetUUID()

        """
        For sanity_check operations, using uuid by parsing infofile of the caller.        
        {
            "dbname": "grid",
            "target_type": "domu",
            "operation_style": "rolling",
            "check_type": "infra",
            "scope": "VM",
            "infofile": "/var/opt/oracle/log/precheck_e716f0f0a05746cb80f068e826e31427_infofile.out",
            "error_checks": [
                "CRS_RESOURCE"
            ]
        }
         Note: When this method mExecuteDBaaSAPIAction is invoked in parallely, _ebox.mGetUUID() creates issues, as each
         thread was getting same value 
        """
        if _action in ["precheck", "postcheck"] and _operation == "sanity_check" and _params and "infofile" in _params :
            _info_file = _params["infofile"].split("/")[-1]
            _uuid = _info_file.split("_")[1]

        _outfile = "/var/opt/oracle/log/" + _action + "_" + _uuid + "_outfile.out"
        _infofile = "/var/opt/oracle/log/" + _action + "_" + _uuid + "_infofile.out"

        # Gather the parameters required for dbaasapi
        _domulist = None

        _injson["object"] = "db"
        _injson["action"] = _action
        _injson["operation"] = _operation
        _injson["params"] = {}

        if _params and _params["dbname"] is not None and _params["dbname"].strip() != "":
            _dbname = _params["dbname"]

        if _params:
            _injson["params"] = _params
        else:
            _injson["params"]["infofile"] = _infofile

        _injson["outputfile"] = _outfile
        _injson["FLAGS"] = ""

        if self.__verbose:
            ebLogInfo("*** The input JSON for %s for DB %s is" % (_action, _dbname))
            ebLogJson(json.dumps(_injson, indent=4, sort_keys=True))

        _filename = _action + "_" + _uuid + ".json"
        _input_file = "/tmp/" + _filename
        ebLogInfo("Input JSON : %s" % _injson)

        with open(_input_file, 'w') as infile:
            json.dump(_injson, infile, sort_keys=True, skipkeys=True, indent=4, ensure_ascii=False)
        # Initiate the step
        _cmd = "nohup /var/opt/oracle/dbaasapi/dbaasapi -i /var/opt/oracle/log/" + _dbname + "/" + _filename + " < /dev/null > /dev/null 2>&1"
        
        # Copy the input json file to the domU
        self.mCopyFileToDomU(_domU, _dbname, None, _input_file, aUser=aUser)

        # Execute the step
        _i, _o, _e = self.mExecCommandOnDomU(_domU, _options, _cmd, aUser=aUser) 
        if str(_e) == "0":
            _dbaasdata["Status"] = "Pass"
        else:
            _logmsg = "*** Failed to execute command to " + _action
            ebLogInfo("%s" % (_logmsg))
            _dbaasdata["Log"] = _logmsg
            _dbaasdata["Status"] = "Fail"

        # Read the job ID
        _idobj = self.mReadStatusFromDomU(_options, _domU, _outfile, aUser=aUser)
        if not _idobj or ("id" not in _idobj):
            _logmsg = "*** Failed to read Job ID from domU"
            ebLogInfo("%s" % (_logmsg))
            _dbaasdata["Log"] = _logmsg
            _dbaasdata["Status"] = "Fail"
            raise ExacloudRuntimeError(0x0774, 0xA, 'DBAASAPI: Failed to read Job ID from domU')

        _jobid = _idobj["id"]
        self.mSetJobId(_jobid)

        if "logfile" in _idobj:
            self.mSetLogFile(_idobj["logfile"])

        _infoobj = {}
        _status_outfile = "/var/opt/oracle/log/" + _action + "_status_" + _uuid + "_outfile.out"
        _status_infofile = "/var/opt/oracle/log/" + _action + "_status_" + _uuid + "_infofile.out"

        # Wait for step to complete
        _status_input_file = _action + "_status_" + _uuid + ".json"
        _status = self.mWaitForJobComplete(_options, "grid", _domU, _jobid, _dbaasdata, _operation, _status_input_file, _status_outfile,  _status_infofile, aUser=aUser) 
        if _status == 0:
            _logmsg = _action + " for " + _sourcedb + " succeeded on Node " + _domU
            _dbaasdata["Log"] = _logmsg
            _dbaasdata["Status"] = "Pass"
            
            if (_action == "dbhome_fetch" and _operation == "configure_node") or (_action == "get"  and _operation == "inst_status") or \
               (_action == "get"  and _operation == "precheck_memory_resize") or \
               (_action in ["validate","rebalance_time_estimate"] and _operation == "diskgroup") or \
                    (_action in ["precheck", "postcheck"] and _operation == "sanity_check"):
                _node_infoobj = self.mReadStatusFromDomU(_options, _domU, _injson["params"]["infofile"], aUser=aUser)
                if _node_infoobj:
                    if self.__verbose:
                        ebLogJson(json.dumps(_node_infoobj, indent=4, sort_keys=True))
                    _infoobj.update(_node_infoobj)
                else:
                    _logmsg = "Info for action: " + _action + " not available in cloud metadata"
        else:
            _logmsg = _action + " for " + _sourcedb + " failed on Node " + _domU
            _dbaasdata["Log"] = _logmsg
            _dbaasdata["Status"] = "Fail"
            self.mCopyDomuInfoLog(_options, _domU, self.mGetLogFile(), _status_infofile, aUser=aUser)

            # In case of error in _action get(inst_status)/addInstance, no need to 
            # error out and break "add node flow".
            # For extension of DB Homes, separate DBAASAPI can be called
            # to syncup spfile, redo, undo tablespace, add the DB instance.           
            if _action in ["get", "addInstance", "validate", "clone_relink"]:
                ebLogError(_logmsg)
            else:
                if aRaiseError:
                    raise ExacloudRuntimeError(0x0775, 0xA, _logmsg)
                else:
                    ebLogError(_logmsg)

        _ebox.mExecuteLocal("/bin/rm -f " + _input_file)

        if self.__verbose:
            ebLogJson(json.dumps(_infoobj, indent=4, sort_keys=True))
        _dbaasdata[_action] = _infoobj

        ebLogInfo("JSON returned as part of DBAAS API call for %s - %s : %s" % (_action, _operation, _dbaasdata))

        return 0

    # Common method to log error code and error message
    def mRecordError(self, aErrorCode, aString=None):

        _dbaasdata = self.mGetDbaasData()

        _dbaasdata["Status"] = STATUS_FAIL
        _dbaasdata["ErrorCode"] = aErrorCode
        if aString is None:
            _dbaasdata["Log"] = gDbaasError[_dbaasdata["ErrorCode"]][0]
        else:
            _dbaasdata["Log"] = gDbaasError[_dbaasdata["ErrorCode"]][0] + aString

        ebLogInfo("%s" % (_dbaasdata["Log"]))
        _errorCode = int(_dbaasdata["ErrorCode"], 16)
        if _errorCode != 0:
            return ebError(_errorCode)
        return SUCCESS_RC
    # end

    # Method to copy the input json file to domU
    def mCopyFileToDomU(self, aDomU, aSourcedb, aDestdb, aLocalFile, aUser=None):

        _remotefile = aLocalFile.split("/")[2]
        if aDestdb is not None:
            self.mBaseCopyFileToDomU(aDomU, aLocalFile, '/var/opt/oracle/log/' + aDestdb + '/' + _remotefile, aUser=aUser)
        elif aSourcedb is not None:
            self.mBaseCopyFileToDomU(aDomU, aLocalFile, '/var/opt/oracle/log/' + aSourcedb + '/' + _remotefile, aUser=aUser)

    # end

    # Base method to copy a file (local copy) to DomU (remote copy)
    def mBaseCopyFileToDomU(self, aDomU, aLocalFile, aRemoteFile, aUser=None):
        """
        Note: aUser variable has been added to allow commands to be executed on the remote node using opc user with
        sudo privileges. Be default, None is chosen for compatibility with existing caller. This variable is introduced
        primarily for infrapatching callers (for precheck and sanity_check sanity apis)
        """
        _node = exaBoxNode(get_gcontext())
        if aUser:
            _node.mSetUser(aUser)        
        if _node.mIsConnectable(aHost=aDomU):
            _node.mConnect(aHost=aDomU)
            _dir = os.path.dirname(aRemoteFile)
            _node.mExecuteCmd("/usr/bin/mkdir -p " + _dir)
            _node.mExecuteCmd("/usr/bin/chown -R oracle:oinstall " + _dir)
            _node.mCopyFile(aLocalFile, aRemoteFile)
            _node.mDisconnect()
        else:
            ebLogInfo("Failed to copy the file %s to domU %s" % (aLocalFile, aDomU))

    # end


    # Method to execute dbaas api steps on the domU
    def mExecCommandOnDomU(self, aDomU, aOptions, aCmd, aField=False, aUser=None):
        """
        Note: aUser variable has been added to allow commands to be executed on the remote node using opc user with
        sudo privileges. Be default, None is chosen for compatibility with existing caller. This variable is introduced
        primarily for infrapatching callers (for precheck and postcheck sanity_check apis)
        """
        _domU = aDomU
        _options = aOptions
        _cmd = aCmd
        _i = None
        _o = None
        _e = None
        _error = 0
        _eBox = self.mGetEbox()
        if not _eBox.mPingHost(_domU):
            ebLogInfo("Failed to ping %s" % (_domU))
            _o = "Failed to ping " + _domU
            _e = 902
            return _i, _o, _e

        # Connect to the cell
        _node = exaBoxNode(get_gcontext())
        if aUser:
            _node.mSetUser(aUser)
        try:
            _node.mConnect(aHost=_domU)
        except:
            ebLogWarn('*** Failed to connect to: %s' % (_domU))
            _o = "Failed to connect to " + _domU
            _e = 903
            return _i, _o, _e

        _i, _o, _e = _node.mExecuteCmd(_cmd)
        _out = _o.readlines()
        if not _out and aField:
            ebLogInfo("Error running command on %s" % (_domU))
            if self.__verbose:
                _err = _e.readlines()
                ebLogInfo("stderr returned from %s is" % (_domU))
                for _line in _err:
                    ebLogInfo("%s" % (_line))
            _o = "Error running command on " + _domU
            _e = 904
            _node.mDisconnect()
            return _i, _o, _e
        else:
            _e = 0
            _node.mDisconnect()
            return _i, _out, _e
    # end

    def mReadStatusFromDomU(self, aOptions, aDomU, aOutfile, aUser=None):

        _options = aOptions
        _domU = aDomU
        _outfile = aOutfile

        _jsondict = None
        _cmd = "cat " + _outfile
        _i, _out, _e = self.mExecCommandOnDomU(_domU, _options, _cmd, True, aUser=aUser)
        if str(_e) == "0":
            if _out:
                _jsonstring = ""
                for _line in _out:
                    _jsonstring += _line

                _jsondict = json.loads(_jsonstring)
            else:
                _logmsg = "*** File " + _outfile + " is empty"
                ebLogInfo("%s" % (_logmsg))
        else:
            _logmsg = "*** Failed to read " + _outfile + " from " + _domU
            ebLogInfo("%s" % (_logmsg))

        return _jsondict
    # end

    # Method to read status of dbaasapi from domU
    def mWaitForJobComplete(self, aOptions, aDbname, aDomU, aJobid, aDbaasdata, aOp, aPayloadFilename, aOutfile, aInfofile, aParams = None, aUser=None):

        _options = aOptions
        _domU = aDomU
        _jobid = aJobid
        _dbaasdata = aDbaasdata
        _op = aOp
        _ebox = self.mGetEbox()
        _outfile = None
        _infofile = aInfofile
        _payloadFilename = aPayloadFilename
        _rc = SUCCESS_RC

        # Prepare JSON for wait call
        _injson = {}
        if _op == "cloud_properties":
            _injson["object"] = "os"
        else:
            _injson["object"] = "db"
        _injson["action"] = "status"
        if _op == "info":
            _injson["operation"] = "info"
        else:
            _injson["operation"] = _op
        _injson["id"] = _jobid
        if aParams:
            _injson["params"] = aParams
        else:
            _injson["params"] = {}
            _injson["params"]["dbname"] = aDbname

        if _infofile is None:
            if _op == "cloud_properties":
                _infofile = "/var/opt/oracle/log/" + _op + "dbaas_info.json"
            else:
                _infofile = "/var/opt/oracle/log/" + aDbname + "/" + _op + "dbaas_info.json"
        _injson["params"]["infofile"] = _infofile

        _outfile = aOutfile
        _injson["outputfile"] = _outfile
        _injson["FLAGS"] = ""

        if self.__verbose:
            ebLogInfo("*** The input JSON for status call is")
            ebLogJson(json.dumps(_injson, indent=4, sort_keys=True))

        # Wait on the job ID till it completes
        _uuid = _ebox.mGetUUID()
        _input_file_lcopy = "/tmp/" + _payloadFilename
        _input_file_rcopy = "/var/opt/oracle/log/" + aDbname + "/" + _payloadFilename

        with open(_input_file_lcopy, 'w') as infile:
            json.dump(_injson, infile, sort_keys=True, skipkeys=True, indent=4, ensure_ascii=False)

        _cmd = "/var/opt/oracle/dbaasapi/dbaasapi -i " + _input_file_rcopy 

        while True:
            # Copy the input json file to the domU
            self.mBaseCopyFileToDomU(_domU, _input_file_lcopy, _input_file_rcopy, aUser=aUser)

            # Execute the status call
            _i, _o, _e = self.mExecCommandOnDomU(_domU, _options, _cmd, aUser=aUser)
            if str(_e) == "0":
                _dbaasdata["Status"] = STATUS_PASS
            else:
                _logmsg = "*** Failed to execute command to check status"
                ebLogInfo("%s" % (_logmsg))
                _dbaasdata["Log"] = _logmsg
                _dbaasdata["Status"] = STATUS_FAIL

            _statusobj = self.mReadStatusFromDomU(_options, _domU, _outfile, aUser=aUser)
            if not _statusobj or ("status" not in list(_statusobj.keys())):
                _logmsg = "*** Failed to read status field from domU"
                ebLogInfo("%s" % (_logmsg))
                _dbaasdata["Log"] = _logmsg
                _dbaasdata["Status"] = STATUS_FAIL
                return FAILURE_RC

            _status = _statusobj["status"]
            ebLogInfo("*** Status of operation is %s" % (_status))
            # Ugly hack for now
            if "errmsg" in list(_statusobj.keys()):
                _errmsg = _statusobj["errmsg"]

            # Sleep for a minute and try again
            _breakcodes = ['Success', 'Error', 'Failed']
            if _status not in _breakcodes:
                if self.__verbose:
                    ebLogInfo("*** Waiting for job %s to complete" % (_jobid))
                time.sleep(60)
            else:
                if _status != "Success":
                    _rc = 1
                break

        if self.__verbose:
            ebLogInfo("*** dbaasapi job %s completed" % (_jobid))
        return _rc

    # end

    # Method to copy the DomU Logs to the UUID logs folder
    def mCopyDomuLogs(self, aOptions, aDomU, aTargetdb, aDbaasdata, aOp, aStep, aLogFile=None):

        _options = aOptions
        _domU = aDomU
        _targetdb = aTargetdb
        _dbaasdata = aDbaasdata
        _op = aOp
        _step = aStep

        _jobid = self.mGetJobId()
        if aLogFile is not None:
            _logfile = aLogFile
        else:
            _logfile = self.mGetLogFile()
        _ebox = self.mGetEbox()
        _uuid = _ebox.mGetUUID()

        _amode = '600'
        _oeda_path = _ebox.mGetOedaPath()
        if _oeda_path:
            _localfile = os.path.join(_oeda_path, f'log/dbaasapi_{_op}_{_step}.out')
        else:
            _localfile = f'oeda/log/{_uuid}/dbaasapi_{_op}_{_step}.out'
        try:
            os.stat(os.path.dirname(_localfile))
        except:
            _ebox.mExecuteLocal(f"/bin/mkdir -p {os.path.dirname(_localfile)}")
        ebLogInfo('Copying remote file: ' + _logfile + ' to staging log folder')
        _node = exaBoxNode(get_gcontext())
        _node.mResetHostKey(aHost=_domU)
        _node.mConnect(aHost=_domU)
        try:
            _node.mCopy2Local(_logfile, _localfile)
            _node.mExecuteCmd('/usr/bin/chmod ' + _amode + ' ' + _localfile)
        except Exception as e:
            ebLogError('*** Error while copying dbaasapi log file: %s' % (str(e)))

        try:
            _oeda_path = _ebox.mGetOedaPath()
            if _oeda_path:
                _localfile2 = os.path.join(_oeda_path, f'log/edcsss_{_op}_{_step}.out')
            else:
                _localfile2 = f'oeda/log/{_uuid}/edcsss_{_op}_{_step}.out'
            _logfile2 = '/var/opt/oracle/log/' + _targetdb + '/edcsss/edcsss.log'
            ebLogInfo('Copying remote file: ' + _logfile2 + ' to staging log folder')
            _node.mCopy2Local(_logfile2, _localfile2)
            _node.mExecuteCmd('/usr/bin/chmod ' + _amode + ' ' + _localfile2)
        except Exception as e:
            ebLogError('*** Error while copying dbaasapi log file: %s' % (str(e)))

        _node.mDisconnect()

    # end

    # Method to copy the DomU Log(info and log file) to the UUID logs folder for a given input json
    def mCopyDomuInfoLog(self, aOptions, aDomU, aLogFile, aInfofile, aUser=None):

        _options = aOptions
        _domU = aDomU
        _ora_error_pattern = re.compile(r'ORA-\d{5}|\b[Ee]rror\b')
        if aLogFile is not None:
            _logfile = aLogFile
        else:
            _logfile = self.mGetLogFile()
        _ebox = self.mGetEbox()
        _uuid = _ebox.mGetUUID()
        _oeda_path = _ebox.mGetOedaPath()
        if _oeda_path:
            _path = os.path.join(_oeda_path, 'log/dbaasapilog')
        else:
            _path = f'oeda/log/dbaasapilog/{_uuid}'
        try:
            os.stat(_path)
        except:
            _ebox.mExecuteLocal("/bin/mkdir -p {0}".format(_path))
        _infofile = aInfofile
        _localLogFile = _path + '/' + _logfile.split('/')[-1]
        ebLogInfo('Copying remote file: ' + _logfile + ' to staging log folder')
        try:
            _cmd = "/usr/bin/cat " + _logfile
            _i, _out, _e = self.mExecCommandOnDomU(_domU, _options, _cmd, True, aUser=aUser)
            if str(_e) == "0":
                if _out:
                    _linecontent = ''
                    for _line in _out:
                        _linecontent += _line
                    f=open(_localLogFile,'w')
                    f.write(_linecontent)
                    f.close()
                    error_lines = set([textline for textline in _out if _ora_error_pattern.search(textline)])
                    if error_lines:
                        ebLogError("*** Error observed in dbaasapi logfile: %s" % (error_lines))

        except Exception as e:
            ebLogError('*** Error while copying dbaasapi log file: %s' % (str(e)))

        if _infofile is not None:
            try:
                _localInfoFile = _path + '/' + _infofile.split('/')[-1]
                ebLogInfo('Copying remote Infofile: ' + _infofile + ' to staging log folder')
                _cmd = "/usr/bin/cat " + _infofile
                _i, _out, _e = self.mExecCommandOnDomU(_domU, _options, _cmd, True, aUser=aUser)
                if str(_e) == "0":
                    if _out:
                        _linecontent = ''
                        for _line in _out:
                            _linecontent += _line
                        f=open(_localInfoFile,'w')
                        f.write(_linecontent)
                        f.close()
            except Exception as e:
                ebLogError('*** Error while copying dbaasapi Info file: %s' % (str(e)))
    # end

# end of ebCluDbaas

# dbaascli commands 
def getDatabaseHomes(domain: str, username: Optional[str] = "root") -> Dict:
    """
    Retrieves database homes from the specified domain.

    Args:
        domain (str): Domain name of the domU.
        username (str, optional): The username to use for the connection. Defaults to "root".

    Returns:
        Dict: A dictionary containing information about the database homes.
    """
    command = "dbaascli system getDBHomes"
    try:
        with connect_to_host(domain, get_gcontext(), username=username) as node:
            _, output, _ = node.mExecuteCmd(command)
            output_lines = output.readlines()[4:-2]
            if any("There are no homes registered in the system" in item for item in output_lines):
                ebLogInfo(f"No databasehomes registered in the system for {domain}.")  
                return {} 
            json_string = ''.join(output_lines)
            return json.loads(json_string)
    except Exception as e:
        ebLogError(f'*** Error while getting dbhomes {str(e)}')
        return {}

def getDatabases(domain: str, username: Optional[str] = "root") -> Dict:
    """
    Retrieves information regarding databases in a cluster from the specified domain.

    Args:
        domain (str): Domain name of the domU.
        username (str, optional): The username to use for the connection. Defaults to "root".

    Returns:
        Dict: A dictionary containing information about the databases.
    """
    command = "dbaascli system getDatabases --reload"
    try:
        with connect_to_host(domain, get_gcontext(), username=username) as node:
            _, output, _ = node.mExecuteCmd(command)
            output_lines = output.readlines()[4:-2]
            # Check for specific warning message  
            if any("There are no databases registered in the system" in line for line in output_lines):  
                ebLogInfo(f"No databases registered in the system for {domain}.")  
                return {}  
            json_string = ''.join(output_lines)
            return json.loads(json_string)
    except Exception as e:
        ebLogError(f'*** Error while getting databases: {str(e)}.')
        return {}
        

def cloneDbHome(domain: str, version: str, dbhome_path: str, new_node: str, username: Optional[str] = "root") -> None:
    """
    Clones the database home to a new node.

    Args:
        domain (str):Domain name of the domU.
        version (str): The version of the database home.
        dbhome_path (str): The path to the database home.
        new_node (str): The new node to clone the database home to.
        username (str, optional): The username to use for the connection. Defaults to "root".
    """
    clone_cmd = f"dbaascli dbhome create --version {version} --oraclehome {dbhome_path} --extendHome --newNodes {new_node}"
    with connect_to_host(domain, get_gcontext(), username=username) as node:
        node.mExecuteCmdLog(clone_cmd)

def addInstance(domain: str, dbname: str, new_node: str, username: Optional[str] = "root") -> None:
    """
    Adds a database instance to a new node.

    Args:
        domain (str): Domain name of the domU.
        dbname (str): The name of the database.
        new_node (str): The new node to add the database instance to.
        username (str, optional): The username to use for the connection. Defaults to "root".
    """
    add_instance_cmd = f"dbaascli database addInstance --dbname {dbname} --nodeListForInstanceMgmt {new_node}"
    with connect_to_host(domain, get_gcontext(), username=username) as node:
        node.mExecuteCmdLog(add_instance_cmd)
            
def deleteInstance(domain: str, dbname: str, new_node: str, username: Optional[str] = "root") -> None:
    """
    Delete a database instance to a new node.

    Args:
        domain (str): Domain name of the domU.
        dbname (str): The name of the database.
        new_node (str): The new node to add the database instance to.
        username (str, optional): The username to use for the connection. Defaults to "root".
    """
    _flag = "--force"
    _delete_instance_cmd = f"dbaascli database deleteInstance --dbname {dbname} --nodeListForInstanceMgmt {new_node} "
    with connect_to_host(domain, get_gcontext(), username=username) as node:
        node.mExecuteCmdLog(_delete_instance_cmd)
        if node.mGetCmdExitStatus() == 0:
            return 0
        else:
            node.mExecuteCmdLog(_delete_instance_cmd + _flag)
            if node.mGetCmdExitStatus() == 0:
                return 0
    return -1

def getDatabaseDetails(domain: str, dbname: str, username: Optional[str] = "root") -> Dict:
    """
    Retrieves details for a specific database from the specified domain.

    Args:
        domain (str): Domain name of the domU.
        dbname (str): The name of the database to retrieve details for.
        username (str, optional): The username to use for the connection. Defaults to "root".

    Returns:
        Dict: A dictionary containing information about the database.
    """
    try:
        command = f"dbaascli database getDetails --dbname {dbname} --reload"
        with connect_to_host(domain, get_gcontext(), username=username) as node:
            _, output, _ = node.mExecuteCmd(command)
            output_lines = output.readlines()[4:-2]
            json_string = ''.join(output_lines)
            return json.loads(json_string)
    except Exception as e:
        ebLogError('*** Error while getting database detail info: %s' % (str(e)))
        return {}

def updateGridINI(aHost: str, aUser: Optional[str] = "root") -> None:
    """
    update GRID.INI for XS(Exacale) clusters.

    Args:
        host (str): host name of the domU.
        aUser (str, optional): The username to use for the connection. Defaults to "root".
    """
    _rc = 0
    _cmd_str = f"/usr/bin/dbaascli admin initializeCluster"
    with connect_to_host(aHost, get_gcontext(), username=aUser) as _node:
        _node.mExecuteCmdLog(_cmd_str)
        _rc = _node.mGetCmdExitStatus()
    return _rc

def executeOCDEInitOnDomUs(aDomUList: list, aParallel: bool, aTcpSslPort: str = None, aIsAtp: bool = False):
    """
    Connects to aDomU and executes the POSTGINID subtask: OCDE INIT

    Args:
        aDomU (str): host name of the domU.
        aParallel (bool): True to spawn subprocesses to handle multiple nodes
            in parallel. False to execute serially

    Returns:
        0 on success

    """

    def executeOCDEInit(aDomU, aResultsDict, aTcpSslPort, aIsAtp):
        """
        Callback helper
        """
        with connect_to_host(aDomU, get_gcontext()) as _node:

            # Run OCDE INIT
            ebLogInfo(f"Executing OCDE init in {aDomU}")
            if aIsAtp:
                # Refer bug 38391988
                _cmd = "/var/opt/oracle/ocde/ocde -exa -init;"
            else:
                _cmd = "/usr/bin/dbaascli admin initializeCluster"
            if aTcpSslPort and not aIsAtp:
                _out_ocde = node_exec_cmd(_node,
                        f"/usr/bin/dbaascli admin initializeCluster --listenerSSLPort {aTcpSslPort}")
            else:
                _out_ocde = node_exec_cmd(_node, _cmd)

            if _out_ocde.exit_code == 0:
                ebLogInfo(f"OCDE init finished with success in {aDomU}")

                # NOTE: Review with dbaas if this is still needed
                # 1- DB Backup requires group access for
                #    /u01/app/oracle
                #    Because the backup assistant will
                #    install java 8 in that path
                #    This is used also for integration with PSM in domU
                node_exec_cmd_check(_node,
                    f"/bin/chmod -R g+rwx /u01/app/oracle",
                    log_error=True, log_stdout_on_error=True)

                node_exec_cmd_check(_node,
                   '/bin/echo "NID" > /u01/app/oracle/nid;',
                    log_error=True, log_stdout_on_error=True)

            else:
                ebLogError(f"OCDE init finished with error in {aDomU}")

            ebLogTrace(f"OCDE init output from {aDomU}:\n{_out_ocde}")
            aResultsDict[aDomU] = _out_ocde.exit_code


    _rc_status = {}
    # Parallel execute
    if aParallel:
        _plist = ProcessManager()
        _rc_status = _plist.mGetManager().dict()

        for _domU in aDomUList:

            _p = ProcessStructure(executeOCDEInit, [_domU, _rc_status, aTcpSslPort, aIsAtp], _domU)
            _p.mSetMaxExecutionTime(30*60) # 30 minutes
            _p.mSetJoinTimeout(5)
            _p.mSetLogTimeoutFx(ebLogWarn)
            _plist.mStartAppend(_p)

        _plist.mJoinProcess()

    else:
        for _domU in aDomUList:
            executeOCDEInit(_domU, _rc_status, aTcpSslPort, aIsAtp)

    # Validate for errors
    _rc = 0
    for _host, _rcs in _rc_status.items():
        if _rcs != 0:
            ebLogError(f"Error detected in {_host}. {_rcs}")
            _rc = _rcs

    return _rc

def mUpdateListenerPort(eBox, aDomUList):
    try:
        _eBox = eBox
        _cluster   = _eBox.mGetClusters().mGetCluster()
        _clu_scans = _cluster.mGetCluScans()
        if not _clu_scans:
            ebLogError("ClusterScans object not found in XML.")
            return
        _scan_name = _clu_scans[0]
        if not _scan_name:
            ebLogError("Scan Name not found in XML.")
            return
        _scan_conf = _eBox.mGetScans().mGetScan(_scan_name)
        _scan_port = _scan_conf.mGetScanPort()
        if not _scan_port:
            ebLogError("Scan Port not found in XML.")
            return
        ebLogInfo(f"Setting Scan Port {_scan_port} in grid.ini")

        _processes = ProcessManager()
        for _domU in aDomUList:

            _p = ProcessStructure(mSetScanPort, (_domU, _scan_port))
            _p.mSetMaxExecutionTime(60*60) # 60 min timeout
            _p.mSetLogTimeoutFx(ebLogWarn)
            _processes.mStartAppend(_p)

        _processes.mJoinProcess()
        
        ebLogInfo("Scan port was successfully set on all domU")

    except Exception as e:
        _err_msg = "Failed to update scan port in grid.ini."
        raise ExacloudRuntimeError(0x0775, 0xA, _err_msg)
        

def mSetScanPort(aDomU, _scan_port):
    with connect_to_host(aDomU, get_gcontext()) as _node:
        try:
            _cmd = f"/var/opt/oracle/ocde/rops set_creg_key grid lsnr_port {_scan_port}"
            _, _o, _e = _node.mExecuteCmd(_cmd)
            _rc = _node.mGetCmdExitStatus()
            if _rc != 0:
                ebLogInfo(f"The cmd {_cmd} returned with the output:{_o.readlines()} error:{_e.readlines()}" )
                return

            _rc = 1
            _cmd = "/var/opt/oracle/ocde/rops get_creg_key grid lsnr_port"
            _, _o, _e = _node.mExecuteCmd(_cmd)
            if _o:
                _out = _o.readlines()
                if _out and len(_out):
                    _out = _out[0].strip()
                    if _out == _scan_port:
                        _rc = 0
                    else:
                        _rc = 1
                else:
                        _rc = 1
            else:
                _rc = 1

            if _rc == 1:
                    ebLogInfo(f"Failed to update scan port {_scan_port} in grid.ini.")
            else:
                ebLogInfo(f"Setting Scan Port {_scan_port} to grid.ini is successful.")
        except Exception as e:
            ebLogInfo("Error while trying to set scan port on a domU")
            raise
