"""
 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    OVM - Resource Management Functionality

FUNCTION:
    Module to provide IORM, and other, resource management
    capabilities

NOTE:
    None

History:
    MODIFIED (MM/DD/YY)
    ririgoye  11/20/25 - Bug 38667586 - EXACS: MAIN: PYTHON3.11: SUPRASS ALL
                         PYTHON WARNINGS
    dekuckre  06/23/25 - 38098385: Allow varied flashcache size across the cells.
    ririgoye  04/10/25 - Bug 37754079 - Fixed SETIORMDBPLAN issue when
                         retrieving size of a clusters PMEM cache size when the
                         feature is disabled
    dekuckre  03/13/25 - 37697911: update 'get pmemcache size' flow
    aypaul    02/19/25 - Bug#37600624 Send zero as pmemcache size when
                         pmemcache is disabled.
    aypaul    02/11/25 - Bug#37578181 Compare db plan of cells in sorted
                         manner.
    joysjose  01/08/25 - Bug 37450728: Regression fix for ririgoye_bug-37185708
    dekuckre  12/24/24 - 37416248: update mGetDBPlanList 
    ririgoye  12/23/24 - Bug 37417201 - EXACS:24.4.2.1:IORM-SETDBPLANV2 FAILING
                         AT DBPLANUPDATEMETADATAWFTASK
    ririgoye  11/29/24 - Bug 37185708 - EXACC:BB:IORM:ECRA IS NOT ABLE TO
                         PERFORM SET DB PLAN
    dekuckre  11/12/24 - 37258867: update Log and cell section in setdbplan
    joysjose  10/01/24 - Bug 37113297 Add precheck in Exacloud to Proceed with
                         pmemcache value setting only is pmemcache is present
    dekuckre  09/10/24 - 37113212: update mGetDBPlanList
    joysjose  09/04/24 - Bug 37019943: Fix IORM DBplan updation issue with
                         default db
    joysjose  08/01/24 - ER 36727567 Add support for IORM resetclusterplan
    gparada   07/11/24 - Bug 36564670 Replace Queue by ProcessManager.List
    joysjose  04/18/2024 - 36376472: Solution to setdbplan overwriting existing dbplan on cells
    joysjose  03/28/2024 - 36406874: ER for enhanced support of get/set dbplan, get/set clusterplan and addition of pmemcache size endpoint. 
    dekuckre    04/27/2023 - 35330536: Ignore dbplan for reset dbplan 
    dekuckre    03/29/2023 - 35215851: Set dbplan ignoring case insensitivity
    dekuckre    08/05/2022 - 34462792: Allow default setting for dbplan in MVM
    dekuckre    11/19/2021 - 33294041: Add support for asmcluster for db plan
    dekuckre    12/15/2020 - 32249703: Update instance variable __data
    dekuckre    08/10/2020 - 31726368: Convert multithreading to multiprocessing 
                             for userconfig cmds
    dekuckre    07/18/2019 - 29932345:Convert multithreading to multiprocessing
    sakskuma    20/02/2019 - Bug 29373581 - set objective to basic after iorm resetdbplan
    dekuckre    09/17/2018 - 28645478: Send formatted 'Get objective' as per 
                             yaml specs.
    dekuckre    09/11/2018 - 28590068: Enhance error recording and reporting.
    dekuckre    06/27/2018 - 28222155: Move user-password correction code from
                             cluresmgr.py to clucontrol.py
    dekuckre    05/25/2018 - 28060479: Add userconfig commands
    dekuckre    09/06/2017 - 26735879: Add mClusterGetClientKeys
    hnvenkat    24/03/2016 - Create file

Changelog:

   24/03/2016 - v1 changes:

       1) DB List API implementation

   01/04/2016 - v2 changes:

       1) Flash cache size read API

   04/04/2016 - v3 changes:

       1) Set objective API
       2) Get objective API

   13/04/2016 - v4 changes:

       1) Create (set) DB Plan API
       2) Read (get) DB Plan API
       3) Reset DB Plan API

   23/06/2016 - new API to create flashcache

"""

from exabox.core.Node import exaBoxNode
from exabox.core.Error import gResError, ExacloudRuntimeError
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace, ebLogVerbose
from exabox.log.LogMgr import ebLogJson
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure
from exabox.core.Context import get_gcontext
from base64 import b64decode
import json
import decimal
from exabox.core.DBStore import ebGetDefaultDB
from threading import Lock

MULTIPROCESSING_MAXEXECUTION_TIMEOUT = 30*60

class ebCluResManager(object):

        def __init__(self, aExaBoxCluCtrl, aOptions):

            self.__config = get_gcontext().mGetConfigOptions()
            self.__basepath = get_gcontext().mGetBasePath()
            self.__clusterpath = None
            self.__xmlpath = aOptions.configpath
            self.__ebox = aExaBoxCluCtrl
            self.__eboxnetworks = None

            self.__cells = {}
            self.__domUs = []
            self.__cluster_host_d = {}
            self.__cluster_resmgr_d = {}

            self.__clusterpath = self.__ebox.mGetClusterPath()
            self.__ddpair = self.__ebox.mReturnDom0DomUPair()

            self.__cells = list(self.__ebox.mReturnCellNodes().keys())

            for _, _dU in self.__ddpair:
                self.__domUs.append(_dU)

            self.__data = {}

        # Main worker method for IORM
        def mClusterIorm(self, aOptions):

            _options = aOptions
            _rc = 0

            _iormdata = self.mGetData()
            _iormdata["Status"] = "Pass"
            _eBox = self.mGetEbox()

            _iormcmd = self.mGetIormCommands()
            _dblist = _iormcmd["dblist"]
            _fcsize = _iormcmd["fcsize"]
            _clientkeys = _iormcmd["clientkeys"]

            # Dump the JSON object
            def _mUpdateRequestData(aDataD):
                _data_d = aDataD
                _reqobj = _eBox.mGetRequestObj()
                if _reqobj is not None:
                    _reqobj.mSetData(json.dumps(_data_d, sort_keys = True))
                    _db = ebGetDefaultDB()
                    _db.mUpdateRequest(_reqobj)
                elif aOptions.jsonmode:
                    ebLogJson(json.dumps(_data_d, indent = 4, sort_keys = True))

            if (_options.resmanage is None):
                ebLogInfo("Invalid invocation or unsupported IORM option")
                _iormdata["Log"] = "Invalid invocation or unsupported IORM option"
                _iormdata["Status"] = "Fail"
                _mUpdateRequestData(_iormdata)
                return self.mRecordError("825")

            # Invoke right worker method
            if (_options.resmanage == "dblist"):
                ebLogInfo("Running IORM Step: Read DB List")
                _iormdata["Command"] = "dblist"
                _rc = self.mClusterDbListFromDomU(_options)

            elif (_options.resmanage == "fcsize"):
                ebLogInfo("Running IORM Step: Read flash cache size")
                _iormdata["Command"] = "fcsize"
                _rc = self.mClusterFcSize(_options)
                
            elif (_options.resmanage == "pmemcsize"):
                ebLogInfo("Running IORM Step: Read pmemcache size")
                _iormdata["Command"] = "getpmemcsize"
                _rc = self.mClusterGetPMemcSize(_options)

            elif (_options.resmanage == "setobj"):
                ebLogInfo("Running IORM Step: Set objective")
                _iormdata["Command"] = "setobj"
                _rc = self.mClusterSetObjective(_options)

            elif (_options.resmanage == "getobj"):
                ebLogInfo("Running IORM Step: Get objective")
                _iormdata["Command"] = "getobj"
                _rc = self.mClusterGetObjective(_options)

            elif (_options.resmanage == "setdbplan"):
                ebLogInfo("Running IORM Step: Create a DB Plan")
                _iormdata["Command"] = "setdbplan"
                _rc = self.mClusterSetDbPlan(_options)

            elif (_options.resmanage == "getdbplan"):
                ebLogInfo("Running IORM Step: Read DB Plan")
                _iormdata["Command"] = "getdbplan"
                _rc = self.mClusterGetDbPlan(_options)
                
            elif (_options.resmanage == "setclusterplan"):
                ebLogInfo("Running IORM Step: Set Cluster Plan")
                _iormdata["Command"] = "setclusterplan"
                _rc = self.mSetClusterPlan(_options)
                
            elif (_options.resmanage == "getclusterplan"):
                ebLogInfo("Running IORM Step: Get Cluster Plan")
                _iormdata["Command"] = "getclusterplan"
                _rc = self.mGetClusterPlan(_options)
                
            elif (_options.resmanage == "resetclusterplan"):
                ebLogInfo("Running IORM Step: Reset Cluster Plan")
                _iormdata["Command"] = "resetclusterplan"
                _rc = self.mSetClusterPlan(_options)
                
            elif (_options.resmanage == "resetdbplan"):
                ebLogInfo("Running IORM Step: Deleting DB Plan")
                _iormdata["Command"] = "resetdbplan"
                _rc = self.mClusterSetDbPlan(_options)
                ebLogInfo("Running IORM Step: Set objective to Auto after Deleting DB Plan")
                _iormdata["Command"] = "setobj"
                _rc = self.mClusterSetObjective(_options,aObjective='auto')

            elif (_options.resmanage == "createflash"):
                ebLogInfo("Running IORM Step: Creating flashcache")
                _iormdata["Command"] = "createflash"
                _rc = self.mClusterCreateFlash(_options)

            elif (_options.resmanage == "dropflash"):
                ebLogInfo("Running IORM Step: Deleting flashcache")
                _iormdata["Command"] = "dropflash"
                _rc = self.mClusterCreateFlash(_options, False)

            elif (_options.resmanage == "clientkeys"):
                ebLogInfo("Running IORM Step: Get Client Keys")
                _iormdata["Command"] = "clientkeys"
                _rc = self.mClusterGetClientKeys(_options)

            else:
                ebLogInfo("Running IORM Step: Unsupported")
                _iormdata["Log"] = "IORM Step: Unsupported"
                _iormdata["Status"] = "Fail"
                _rc = self.mRecordError("851")

            self.mSetData(_iormdata)
            _mUpdateRequestData(_iormdata)

            ebLogInfo(f"_iormdata: {_iormdata}")
            return _rc
        # end

        def mGetIormCommands(self):
            _iormcmd = {}
            if self.__ebox.mIsExabm():
                _iormcmd["dblist"] = "dbList"
                _iormcmd["dbset"] = "dbSet"
                _iormcmd["fcsize"] = "fcSize" 
                _iormcmd["pmemcsize"] = "pmemcSize"
                _iormcmd["pmemcexist"] = "pmemcExist"
                _iormcmd["objective"] = "objective"
                _iormcmd["dbplan"] = "dbPlan"
                _iormcmd["clientkeys"] = "clientKeys"
                _iormcmd["clusterplan"] = "clusterPlan"
            else:
                _iormcmd["dblist"] = "dblist"
                _iormcmd["dbset"] = "DbSet"
                _iormcmd["fcsize"] = "FcSize"
                _iormcmd["pmemcsize"] = "PmemcSize"
                _iormcmd["pmemcexist"] = "PmemcExist"
                _iormcmd["objective"] = "Objective"
                _iormcmd["dbplan"] = "DbPlan"
                _iormcmd["clientkeys"] = "ClientKeys"
                _iormcmd["clusterplan"] = "ClusterPlan"
                
            return _iormcmd

        # Method to read DB List from cluster cells
        def mClusterDbList(self, aOptions, aIormdata=None):

            _options = aOptions

            if aIormdata is None:
                _iormdata = self.mGetData()
            else:
                _iormdata = aIormdata

            _iormdata["Status"] = "Pass"
            _iormdata["cell"] = {}
            _iormdata["ErrorCode"] = "0"

            _cells    = self.mGetCells()

            _iormcmd = self.mGetIormCommands()
            _key = _iormcmd["dbset"]

            # Execute commands on each cell
            _cmd = "cellcli -e list database"
            for _cell in _cells:

                _iormdata["cell"][_cell] = {}
                _i, _o, _e = self.mExecCommandOnCell(_cell, _options, _cmd)
                if str(_e) == "0":
                    _dbl, _dbe = self.mParseDbListOutput(_o)
                    _iormdata["cell"][_cell]["dbList"] = _dbl
                    _iormdata["cell"][_cell]["errorCode"] = str(_dbe)
                    _iormdata["cell"][_cell]["log"] = gResError[str(_dbe)]
                else:
                    _iormdata["cell"][_cell]["dbList"] = None
                    _iormdata["cell"][_cell]["errorCode"] = str(_e)
                    _iormdata["cell"][_cell]["log"] = gResError[str(_e)]

                if _iormdata["cell"][_cell]["dbList"] == None:
                    ebLogInfo(f"Fetching DB List from {_cell} failed")
                    _iormdata["Status"] = "Fail"

            # Format, store results

            _uniqdblist = []
            for _cell in _cells:
                _uniqdblist.append(_iormdata["cell"][_cell]["dbList"])

            _uniqdl = set(_uniqdblist)
            if len(_uniqdl) != 1:
                _iormdata[_key] = "None"
                _iormdata["Status"] = "Fail"
                _iormdata["ErrorCode"] = "803"
                _iormdata["Log"] = gResError[_iormdata["ErrorCode"]][0]
                ebLogInfo("%s" %(str(_iormdata["Log"])))
            elif (list(_uniqdl)[0] is not None):
                ebLogInfo(f"Common DB List found across all cells - {list(_uniqdl)[0]}")
                _iormdata["Log"] = "Common DB List found across all cells"
                _iormdata[_key] = list(_uniqdl)[0]
            else:
                _iormdata[_key] = "None"
                _iormdata["ErrorCode"] = "804"
                _iormdata["Log"] = gResError[_iormdata["ErrorCode"]][0]
                ebLogInfo("%s" %(str(_iormdata["Log"])))

            if not _options.jsonmode:
                if len(_uniqdl) != 1:
                    for _cell in _cells:
                        ebLogInfo("DB List for %s is %s" %(_cell, _iormdata["cell"][_cell]["dbList"]))

        # end

        # Method to read DB List from cluster cells
        def mClusterDbListFromDomU(self, aOptions, aIormdata=None):

            _options = aOptions
            _gridhome = None

            if aIormdata is None:
                _iormdata = self.mGetData()
            else:
                _iormdata = aIormdata

            _iormcmd = self.mGetIormCommands()
            _key = _iormcmd["dbset"]

            _iormdata["Status"] = "Pass"
            _iormdata["ErrorCode"] = "0"
            _iormdata["cell"] = {} #ECRA will complain if absent
            _iormdata[_key] = "None"

            _domUs = self.mGetDomUs()

            # First get the GRID_HOME path
            _cmd = "cat /var/opt/oracle/creg/grid/grid.ini |grep \"^oracle_home\" | cut -d \"=\" -f 2"
            def _mExecute(aDomU, aList):
                _domU = aDomU
                _list = aList
                _iormdata[_domU] = {}

                # Rese mExecCommandOnCell
                _i, _o, _e = self.mExecCommandOnCell(_domU, _options, _cmd)
                if str(_e) == "0":

                    if (_o is None) or (len(_o)) > 1:
                        ebLogInfo("Unexpected output from oratab parsing of %s" %(_domU))
                        return 1

                    for _line in _o:
                        _gridhome = str(_line).strip()
                        ebLogInfo("GRID_HOME from %s is %s" %(_domU, _gridhome))
                        break
                else:
                    _iormdata[_domU][_key] = "None"
                    _iormdata[_domU]["ErrorCode"] = "804"
                    _iormdata[_domU]["Log"] = gResError[_iormdata[_domU]["ErrorCode"]][0]
                    ebLogInfo("%s" %(str(_iormdata[_domU]["Log"])))
                    _list.append([_domU, _iormdata[_domU]])
                    return 1

                _srvctlcmd = _gridhome + "/bin/srvctl config database" 
                _i, _o, _e = self.mExecCommandOnCell(_domU, _options, _srvctlcmd)
                if str(_e) == "0":
                    _dbl, _dbe = self.mParseDbListOutput(_o)
                    _iormdata[_domU][_key] = _dbl
                    _iormdata[_domU]["ErrorCode"] = str(_dbe)
                    _iormdata[_domU]["Log"] = gResError[str(_dbe)]
                    _list.append([_domU, _iormdata[_domU]])
                    if _dbl is None:
                        ebLogInfo("%s" %(str(_iormdata[_domU]["Log"])))
                        return 1
                    else:
                        ebLogInfo("DB List is %s in %s" %(_dbl, _domU))
                        return 0

            _plist = ProcessManager()
            _list = _plist.mGetManager().list()

            # Parallelize execution on cells
            for _domU in _domUs:
                _p = ProcessStructure(_mExecute, [_domU, _list], _domU)
                _p.mSetMaxExecutionTime(MULTIPROCESSING_MAXEXECUTION_TIMEOUT)
                _p.mSetJoinTimeout(60)
                _p.mSetLogTimeoutFx(ebLogWarn)
                _plist.mStartAppend(_p)
                ebLogTrace('%s : _mExecute started for %s ' %(_p.name, _domU))
            
            _plist.mJoinProcess()
            ebLogTrace('All processes completed their call to _mExecute.')

            for _entry in _list:                
                _iormdata[_entry[0]] = _entry[1]

            for _domU in _domUs:

                if _iormdata[_domU][_key] == "None":
                    _iormdata[_key] = "None"
                    _iormdata["Log"] = _iormdata[_domU]["Log"]
                    #Lets not fail the overall op.
                    return 0

                else:
                    _iormdata[_key] = _iormdata[_domU][_key] 
                    _iormdata["Log"] = _iormdata[_domU]["Log"]
                    if _iormdata[_key] is None:
                        ebLogInfo("%s" %(str(_iormdata[_domU]["Log"])))
                        #Lets not fail the overall op.
                        return 0
                    else:
                        ebLogInfo("DB List is %s" %(_iormdata[_key]))
                        return 0

        # end
        
        # Method to read the size of the flash cache from the cells
        def mClusterFcSize(self, aOptions, aIormdata=None):

            _options = aOptions

            if aIormdata is None:
                _iormdata = self.mGetData()
            else:
                _iormdata = aIormdata

            _iormdata["Status"] = "Pass"
            _iormdata["cell"] = {}
            _iormdata["ErrorCode"] = "0"

            _cells    = self.mGetCells()

            _iormcmd = self.mGetIormCommands()
            _key = _iormcmd["fcsize"]

            # Execute commands on each cell
            _cmd = "cellcli -e list flashcache detail | grep size"

            def _mExecute(aCell, aList):
                _cell = aCell
                _list = aList

                _iormdata["cell"][_cell] = {}
                _i, _o, _e = self.mExecCommandOnCell(_cell, _options, _cmd)
                if str(_e) == "0":
                    _fcs, _fcse = self.mParseCacheOutput(_o, "flashcache")
                    _iormdata["cell"][_cell]["fcSize"] = _fcs
                    _iormdata["cell"][_cell]["errorCode"] = str(_fcse)
                    _iormdata["cell"][_cell]["log"] = gResError[str(_fcse)]
                else:
                    _iormdata["cell"][_cell]["fcSize"] = None
                    _iormdata["cell"][_cell]["errorCode"] = str(_e)
                    _iormdata["cell"][_cell]["log"] = gResError[str(_e)]

                _list.append([_cell, _iormdata["cell"][_cell]])

            _plist = ProcessManager()
            _list = _plist.mGetManager().list()

            # Parallelize execution on cells
            for _cell in _cells:
                _p = ProcessStructure(_mExecute, [_cell, _list], _cell)
                _p.mSetMaxExecutionTime(MULTIPROCESSING_MAXEXECUTION_TIMEOUT)
                _p.mSetJoinTimeout(60)
                _p.mSetLogTimeoutFx(ebLogWarn)
                _plist.mStartAppend(_p)
                ebLogTrace('%s : _mExecute started for %s ' %(_p.name, _cell))

            _plist.mJoinProcess()
            ebLogTrace('All processes completed their call to _mExecute.')

            for _entry in _list:
                _iormdata["cell"][_entry[0]] = _entry[1]

            for _cell in _cells:
                if _iormdata["cell"][_cell]["fcSize"] == None:
                    ebLogInfo("Fetching flash cache size from %s failed" %(_cell))
                    _iormdata["Status"] = "Fail"

            # Format, store results

            _uniqfclist = []
            for _cell in _cells:
                _uniqfclist.append(_iormdata["cell"][_cell]["fcSize"])

            def to_terabytes(val):
                if val.endswith('T'):
                    return float(val[:-1])
                elif val.endswith('G'):
                    return float(val[:-1]) / 1024
                elif val.endswith('M'):
                    return float(val[:-1]) / 1024 / 1024
                else:
                    return float(val[:-1])

            _uniqfc = set(_uniqfclist)
            if len(_uniqfc) != 1:
                _iormdata[_key] = min(list(_uniqfc), key=lambda x: to_terabytes(x))
                _iormdata["Log"] = f"Varied flash cache size found across all cells. Min flashcache size across cells: {_iormdata[_key]}"
                ebLogInfo("%s" %(str(_iormdata["Log"])))
            elif (list(_uniqfc)[0] is not None):
                ebLogInfo("Common flash cache size found across all cells - %s" %(list(_uniqfc)[0]))
                _iormdata["Log"] = "Common flash cache size found across all cells"
                _iormdata[_key] = list(_uniqfc)[0]
            else:
                _iormdata[_key] = "None"
                _iormdata["ErrorCode"] = "807"
                _iormdata["Log"] = gResError[_iormdata["ErrorCode"]][0]
                ebLogInfo("%s" %(str(_iormdata["Log"])))

            if not _options.jsonmode:
                if len(_uniqfc) != 1:
                    for _cell in _cells:
                        ebLogInfo("flash cache size for %s is %s" %(_cell, _iormdata["cell"][_cell]["fcSize"]))

            if (_iormdata["ErrorCode"] != "0"):
                return self.mRecordError(_iormdata["ErrorCode"])
            else:
                return 0

        # end
        
        # Method to validate the size values and typing of the pmemcache from the cells
        def mValidatePmemcSizes(self, aCells, aIormData):
            _cells, _iormdata = aCells, aIormData

            # Format, store results
            _uniqpmlist = []
            _valsuffix = ""

            for _cell in _cells:
                # Skip None values
                _val = _iormdata["cell"][_cell]["pmemcSize"]
                if _val is None:
                    raise TypeError(f"pmemcache size is None for cell {_cell}")

                # Check if value is string
                _strval = _val
                if not isinstance(_strval, str):
                    raise TypeError(f"Invalid pmemcache type in cell: {_cell}. Not a string.")

                # Split number and measure unit (will throw exception if no measure unit is found)
                _valsuffix = ""
                try:
                    _valsuffixIndex = _strval.find(next(filter(str.isalpha, _strval)))
                    _valsuffix = _strval[_valsuffixIndex:]
                    _strval = _strval[:_valsuffixIndex]
                except StopIteration:
                    _msg = f"No suffix found in {_strval}. Unit of measurement is required."
                    ebLogError(_msg)
                    raise ExacloudRuntimeError(0x0114, 0xA, _msg)
                except Exception as e:
                    raise ExacloudRuntimeError(0x0114, 0xA, str(e))

                # Convert to float and add to list of pmem sizes
                try:
                    _uniqpmlist.append(float(_strval))
                except ValueError as e:
                    raise ValueError(f"Invalid pmemcache size: {_strval}. Got error: {str(e)}")

            # Check pmem size values are not very different
            _exceedsthreshold = False
            _config = get_gcontext().mGetConfigOptions()
            _pmsizethreshold = float(_config.get("pmemcsize_dif_threshold", 0.01))

            if len(_uniqpmlist) > 1:
                _minval, _maxval = min(_uniqpmlist), max(_uniqpmlist)
                _exceedsthreshold = abs(_maxval - _minval) > _pmsizethreshold

            if _exceedsthreshold:
                #raise ValueError(f"PMEM cache sizes between cells differ too much.")
                return str(min(_uniqpmlist)) + _valsuffix, _uniqpmlist

            # Return values according to the result
            _avgpmemsize = 0.0 if len(_uniqpmlist) == 0 else sum(_uniqpmlist) / len(_uniqpmlist)
            _avgpmemsize = round(_avgpmemsize, 3)
            _formattedpmemsize = str(_avgpmemsize) + _valsuffix
            return _formattedpmemsize, _uniqpmlist
        
        # end

        # Method to read the size of the pmemcache from the cells
        def mClusterGetPMemcSize(self, aOptions, aIormdata=None):

            _options = aOptions

            if aIormdata is None:
                _iormdata = self.mGetData()
            else:
                _iormdata = aIormdata

            _iormdata["Status"] = "Pass"
            _iormdata["cell"] = {}
            _iormdata["ErrorCode"] = "0"

            _cells    = self.mGetCells()

            _iormcmd = self.mGetIormCommands()
            _key = _iormcmd["pmemcsize"]

            _cmd_tocheck_pmemcacheexists = "cellcli -e list pmemcache detail"
            _cmd_tofetch_pmemcachesize = "cellcli -e list pmemcache detail | grep effectiveCacheSize"

            def _mExecute(aCell, aList):
                _cell = aCell
                _list = aList

                _iormdata["cell"][_cell] = {}
                _i, _o, _e = self.mExecCommandOnCell(_cell, _options, _cmd_tocheck_pmemcacheexists)
                
                if not _o:
                    ebLogWarn(f"PMEMCache is disabled for {_cell}")
                    _iormdata["cell"][_cell]["pmemcSize"] = "0"
                    _iormdata["cell"][_cell]["errorCode"] = "0"
                    _iormdata["cell"][_cell]["log"] = "pmemcache is disabled for this cluster."
                else:
                    ebLogTrace(f"PMEMCache is enabled for {_cell}")
            
                    _i, _o, _e = self.mExecCommandOnCell(_cell, _options, _cmd_tofetch_pmemcachesize)
                    if str(_e) == "0":
                        _fcs, _fcse = self.mParseCacheOutput(_o, "pmemcache")
                        _iormdata["cell"][_cell]["pmemcSize"] = _fcs
                        _iormdata["cell"][_cell]["errorCode"] = str(_fcse)
                        _iormdata["cell"][_cell]["log"] = gResError[str(_fcse)]
                    else:
                        _iormdata["cell"][_cell]["pmemcSize"] = None
                        _iormdata["cell"][_cell]["errorCode"] = str(_e)
                        _iormdata["cell"][_cell]["log"] = gResError[str(_e)]

                _list.append([_cell, _iormdata["cell"][_cell]])

            _plist = ProcessManager()
            _list = _plist.mGetManager().list()

            # Parallelize execution on cells
            for _cell in _cells:
                _p = ProcessStructure(_mExecute, [_cell, _list], _cell)
                _p.mSetMaxExecutionTime(MULTIPROCESSING_MAXEXECUTION_TIMEOUT)
                _p.mSetJoinTimeout(60)
                _p.mSetLogTimeoutFx(ebLogWarn)
                _plist.mStartAppend(_p)
                ebLogTrace('%s : _mExecute started for %s ' %(_p.name, _cell))

            _plist.mJoinProcess()
            ebLogTrace('All processes completed their call to _mExecute.')

            for _entry in _list:
                _iormdata["cell"][_entry[0]] = _entry[1]

            _pmemcacheenabled = True

            for _cell in _cells:
                if _iormdata["cell"][_cell]["pmemcSize"] == None:
                    ebLogInfo("Fetching pmemcache size from %s failed" %(_cell))
                    _iormdata["Status"] = "Fail"
                if "disabled" in _iormdata["cell"][_cell]["log"]:
                    ebLogTrace("Marking PMEM cache state as disabled.")
                    _pmemcacheenabled = False

            # If PMEM cache is disabled, skip the checks below
            if not _pmemcacheenabled:
                ebLogInfo("PMEM cache is disabled. Will skip size difference check.")
                _iormdata["Log"] = "PMEM cache is disabled for this cluster."
                _iormdata[_key] = "0.0T"
                return 0

            # Validate the cell values and return the average size
            _uniqpmlist = []

            try:
                _formattedpmemsize, _uniqpmlist = self.mValidatePmemcSizes(_cells, _iormdata)
                ebLogInfo("pmemcache size - %s" %(_formattedpmemsize))
                _iormdata["Log"] = "pmemcache size found across all cells"
                _iormdata[_key] = _formattedpmemsize
            except TypeError as te:
                _iormdata[_key] = "None"
                _iormdata["Status"] = "Fail"
                _iormdata["ErrorCode"] = "835"
                _iormdata["Log"] = gResError[_iormdata["ErrorCode"]][0]
                ebLogInfo("%s" %(str(_iormdata["Log"])))
            except ValueError as ve:
                _iormdata[_key] = "None"
                _iormdata["ErrorCode"] = "836"
                _iormdata["Log"] = gResError[_iormdata["ErrorCode"]][0]
                ebLogInfo("%s" %(str(_iormdata["Log"])))

            if not _options.jsonmode:
                if len(_uniqpmlist) != 1:
                    for _cell in _cells:
                        ebLogInfo("pmemcache size for %s is %s" %(_cell, _iormdata["cell"][_cell]["pmemcSize"]))

            if (_iormdata["ErrorCode"] != "0"):
                return self.mRecordError(_iormdata["ErrorCode"])
            else:
                return 0

        # end

        # Method to set the IORM objective on each of the cells
        def mClusterSetObjective(self, aOptions, aObjective=None):

            _options = aOptions
            _objective = None

            _iormdata = self.mGetData()
            _iormdata["Status"] = "Pass"
            _iormdata["ErrorCode"] = "0"

            _objvalues = [ "basic", "auto", "balanced", "low_latency", "high_throughput" ]              
            _cells    = self.mGetCells()

            # Parse the input JSON and read the objective
            _inputjson = _options.jsonconf 
            if not aObjective:
                if not _inputjson:
                    return self.mRecordError("808")
                elif 'objective' not in list(_inputjson.keys()):
                    return self.mRecordError("809")
                elif _inputjson['objective'].lower() not in _objvalues:
                    return self.mRecordError("810")
                else:
                    _objective = _inputjson['objective'].lower()
            else:
                _objective = aObjective.lower()

            _iormdata["cell"] = {}

            # Execute commands on each cell
            _cmd = "cellcli -e alter iormplan objective=\'" + _objective + "\'"
            
            def _mExecute(aCell, aList):
                _cell = aCell
                _list = aList

                _iormdata["cell"][_cell] = {}
                _i, _o, _e = self.mExecCommandOnCell(_cell, _options, _cmd)
                _iormdata["cell"][_cell]["errorCode"] = str(_e)
                _iormdata["cell"][_cell]["log"] = gResError[str(_e)]


                _list.append([_cell, _iormdata["cell"][_cell]])

            _plist = ProcessManager()
            _list = _plist.mGetManager().list()

            # Parallelize execution on cells
            for _cell in _cells:
                _p = ProcessStructure(_mExecute, [_cell, _list], _cell)
                _p.mSetMaxExecutionTime(MULTIPROCESSING_MAXEXECUTION_TIMEOUT)
                _p.mSetJoinTimeout(60)
                _p.mSetLogTimeoutFx(ebLogWarn)
                _plist.mStartAppend(_p)
                ebLogTrace('%s : _mExecute started for %s ' %(_p.name, _cell))

            _plist.mJoinProcess()
            ebLogTrace('All processes completed their call to _mExecute.')

            for _entry in _list:
                _iormdata["cell"][_entry[0]] = _entry[1]

            for _cell in _cells:
                if _iormdata["cell"][_cell]["errorCode"] != "0":
                    ebLogInfo("Setting IORM objective on %s failed" %(_cell))
                    _iormdata["Status"] = "Fail"
                    _iormdata["ErrorCode"] = _iormdata["cell"][_cell]["errorCode"] 

            if _iormdata["Status"] == "Fail":
                ebLogInfo("Setting IORM objective on the cluster failed")
                _iormdata["Log"] = "Setting IORM objective on the cluster failed"
            else:
                ebLogInfo("Setting IORM objective on the cluster succeeded")
                _iormdata["Log"] = "Setting IORM objective on the cluster succeeded"

            if _iormdata["ErrorCode"] != "0":
                return self.mRecordError(_iormdata["ErrorCode"])
            else:
                return 0

        # end

        # Method to read the IORM objective from the cells
        def mClusterGetObjective(self, aOptions):

            _options = aOptions

            _iormdata = self.mGetData()
            _iormdata["Status"] = "Pass"
            _iormdata["cell"] = {}
            _iormdata["ErrorCode"] = "0"
            _objdict = {'auto':'Auto', 'low_latency':'Low_Latency', 'high_throughput':'High_Throughput', 'balanced':'Balanced', 'basic':'Basic'}

            _cells    = self.mGetCells()

            _iormcmd = self.mGetIormCommands()
            _key = _iormcmd["objective"]

            # Execute commands on each cell
            _cmd = "cellcli -e list iormplan detail |grep objective"
            
            def _mExecute(aCell, aList):
                _cell = aCell
                _list = aList
                

                _iormdata["cell"][_cell] = {}
                _iormdata["cell"][_cell]["objective"] = ""
                _iormdata["cell"][_cell]["errorCode"] = ""
                _iormdata["cell"][_cell]["log"]= ""
                _i, _o, _e = self.mExecCommandOnCell(_cell, _options, _cmd)
                if str(_e) == "0":
                    _gob, _gobe = self.mParseGetObjOutput(_o)
                    _iormdata["cell"][_cell]["objective"] = _objdict[_gob]
                    _iormdata["cell"][_cell]["errorCode"] = str(_gobe)
                    _iormdata["cell"][_cell]["log"] = gResError[str(_gobe)]
                else:
                    _iormdata["cell"][_cell]["objective"] = None
                    _iormdata["cell"][_cell]["errorCode"] = str(_e)
                    _iormdata["cell"][_cell]["log"] = gResError[str(_e)]
                
                _list.append([_cell, _iormdata["cell"][_cell]])

            _plist = ProcessManager()
            _list = _plist.mGetManager().list()

            # Parallelize execution on cells
            for _cell in _cells:
                _p = ProcessStructure(_mExecute, [_cell, _list], _cell)
                _p.mSetMaxExecutionTime(MULTIPROCESSING_MAXEXECUTION_TIMEOUT)
                _p.mSetJoinTimeout(60)
                _p.mSetLogTimeoutFx(ebLogWarn)
                _plist.mStartAppend(_p)
                ebLogTrace('%s : _mExecute started for %s ' %(_p.name, _cell))
            
            _plist.mJoinProcess()
            ebLogTrace('All processes completed their call to _mExecute.')

            for _entry in _list:
                _iormdata["cell"][_entry[0]] = _entry[1]

            for _cell in _cells:
                if _iormdata["cell"][_cell]["objective"] == None:
                    ebLogInfo("Fetching IORM objective from %s failed" %(_cell))
                    _iormdata["Status"] = "Fail"

            # Format, store results

            _uniqgoblist = []
            for _cell in _cells:
                _uniqgoblist.append(_iormdata["cell"][_cell]["objective"])

            _uniqgob = set(_uniqgoblist)
            if len(_uniqgob) != 1:
                _iormdata[_key] = "None"
                _iormdata["Status"] = "Fail"
                _iormdata["ErrorCode"] = "811"
                _iormdata["Log"] = gResError[_iormdata["ErrorCode"]][0]
                ebLogInfo("%s" %(str(_iormdata["Log"])))
            elif (list(_uniqgob)[0] is not None):
                ebLogInfo("Common IORM objective found across all cells - %s" %(list(_uniqgob)[0]))
                _iormdata["Log"] = "Common IORM objective found across all cells"
                _iormdata[_key] = list(_uniqgob)[0]
            else:
                _iormdata[_key] = "None"
                _iormdata["ErrorCode"] = "812"
                _iormdata["Log"] = gResError[_iormdata["ErrorCode"]][0]
                ebLogInfo("%s" %(str(_iormdata["Log"])))

            if not _options.jsonmode:
                if len(_uniqgob) != 1:
                    for _cell in _cells:
                        ebLogInfo("IORM objective for %s is %s" %(_cell, _iormdata["cell"][_cell]["objective"]))
            
            if _iormdata["ErrorCode"] != "0":
                return self.mRecordError(_iormdata["ErrorCode"])
            else:
                return 0

        # end
        
        #the function returns the dbplanlist 
        def mGetDBPlanList(self, _existing_db_plan, _inputdbplist):
            #to take care of the asmcluster attribute inclusion. 
            if self.mGetEbox().mGetEnableAsmss() == "true":
                for _dbp in _inputdbplist:
                    if _dbp['dbname'].lower() != "default" and 'asmcluster' not in _dbp.keys():
                        _dbp['asmcluster'] = self.mGetEbox().mGetClusters().mGetCluster().mGetCluName()
                ebLogTrace(f"Input dbplan list after asmcluster inclusion: {_inputdbplist}")
            else:
                ebLogTrace(f"Input dbplan list: {_inputdbplist}")
                
                        
            #this part takes care of the default entry in existing dbplan.
            _existing_default = None
            _defExists = False #flag to check if default entry is specified by user
            _input_dbplan_dict = {_dbp['dbname']:_dbp for _dbp in _inputdbplist}
            _existing_dbplan_dict = {_dbp['dbname']:_dbp for _dbp in _existing_db_plan}
            _dbplist = []
            #if there is new default entry from customer, then we overwrite the existing default entry. 
            #Deletion of default entry from both input dictionary and existing dictionary helps to handle the rest of the entries
            #by creating a composite key in the next section
            if "default" in _input_dbplan_dict:
                #if customer specified default entry, then directly append it to dbplan and delete the default entry from _existing_db_plan
                _dbplist.append(_input_dbplan_dict['default'])
                _defExists = True
                ebLogTrace(f"_input_dbplan_dict: {_input_dbplan_dict}")
                ebLogTrace(f"_existing_dbplan_dict: {_existing_dbplan_dict}")
                _existing_dbplan_dict.pop('default', None)
                _existing_db_plan = [_dbp for _dbp in _existing_db_plan if _dbp['dbname'] != 'default']
                _inputdbplist = [_dbp for _dbp in _inputdbplist if _dbp['dbname'] != 'default']
                ebLogTrace(f"New dbplan after appending default entry: {_dbplist}")
                ebLogTrace(f"Inputdblist after removing default entry: {_inputdbplist}")
                
            elif "default" in _existing_dbplan_dict:
                #need to recalculate default share after all dbplans are checked in next step.
                _existing_default = _existing_dbplan_dict['default']
                ebLogInfo(f"Existing default entry in dbplan: {_existing_default}")
                _defExists = False
                del _existing_dbplan_dict['default']
                _existing_db_plan = [_dbp for _dbp in _existing_db_plan if _dbp['dbname'] != 'default']
                ebLogInfo(f"New existing dblist after removing default entry: {_existing_db_plan}")
            elif self.mGetEbox().mGetEnableAsmss() != "true":
                ebLogInfo("There is no default entry in both existing dbplan and input dbplan. Default entry will be added to the dbplan")
                _defExists = False
            
            #this part takes care of appending the new dbplan from payload to the existing dbplan
            #replace the old dbplan with new dbplan if the new dbplan contains the same dbname and asmcluster  as in old dbplan (if self.mGetEbox().mGetEnableAsmss() == "true")
            #replace the old dbplan with new dbplan if the new dbplan contains the same dbname as in old dbplan (if self.mGetEbox().mGetEnableAsmss() == "false")
            #when code reach this part, the _inputdbplist will not contain the default entry and so it will not error out in formation of composite key
            _existing_dbplan_dict = {}
            for _dbp in _existing_db_plan:
                if 'asmcluster' in _dbp.keys():
                    _existing_dbplan_dict[(_dbp['dbname'],_dbp['asmcluster'])]=_dbp
                else:
                    _existing_dbplan_dict[_dbp['dbname']]=_dbp
                
            for _dbplan in _inputdbplist:
                if 'asmcluster' in _dbplan.keys():
                    _key = (_dbplan['dbname'],_dbplan['asmcluster'])
                else:
                    _key = _dbplan['dbname']
                if "flashcachesize" in list(_dbplan.keys()) and _dbplan['flashcachesize']:
                    _dbplan['is_fc_size'] = "True"
                else:
                    _dbplan['is_fc_size'] = "False"
                #either flashcachelimit or flashcachesize value can be present in the cellcli plan. Else cellcli will raise error. So this flag checks if flashcachesize is in input from customer. 
                # If yes, then flashcachelimit will not be appended for it. Else, it will append.
                ebLogTrace(f"flashCacheSize value in payload: {_dbplan['is_fc_size']}")
                if _key in _existing_dbplan_dict:
                    _existing_dbplan_dict[_key] = _dbplan
                else:
                    _dbplist.append(_dbplan)
            
            _dbplist.extend(_existing_dbplan_dict.values()) 
            ebLogTrace(f"New dbplan after appending all entries: {_dbplist}")
            
            return _dbplist, _defExists, _existing_default
        
        def mCreateDBPlanString(self, _dbplist, _dbflashlimit):                                                                                                                                                  
            # Create the dbplan string
            _dbpstring = "dbPlan=("
            for _dbp in _dbplist:

                _dbpstring = _dbpstring + "(name=" + _dbp['dbname'] 
                _dbpstring = _dbpstring + ", share=" + _dbp['share'] 
                if 'limit' in list(_dbp.keys()) and _dbp['limit']:
                    _dbpstring = _dbpstring + ", limit=" + _dbp['limit'] 
                if 'flashcachemin' in list(_dbp.keys()) and _dbp['flashcachemin']:
                    _dbpstring = _dbpstring + ", flashCacheMin=" + _dbp['flashcachemin']
                if 'is_fc_size' in list(_dbp.keys()) and _dbp['is_fc_size'] == "True": 
                    if 'flashcachesize' in list(_dbp.keys()) and _dbp['flashcachesize']:
                        _dbpstring = _dbpstring + ", flashCacheSize=" + _dbp['flashcachesize']
                if 'pmemcachemin' in list(_dbp.keys()) and _dbp['pmemcachemin']:
                    _dbpstring = _dbpstring + ", pmemCacheMin=" + _dbp['pmemcachemin']
                elif 'xrmemcachemin' in list(_dbp.keys()) and _dbp['xrmemcachemin']:
                    _dbpstring = _dbpstring + ", pmemCacheMin=" + _dbp['xrmemcachemin']
                if 'pmemcachelimit' in list(_dbp.keys()) and _dbp['pmemcachelimit']:
                    _dbpstring = _dbpstring + ", pmemCacheLimit=" + _dbp['pmemcachelimit']
                elif 'xrmemcachelimit' in list(_dbp.keys()) and _dbp['xrmemcachelimit']:
                    _dbpstring = _dbpstring + ", pmemCacheLimit=" + _dbp['xrmemcachelimit']
                if 'pmemcachesize' in list(_dbp.keys()) and _dbp['pmemcachesize']:
                    _dbpstring = _dbpstring + ", pmemCacheSize=" + _dbp['pmemcachesize']
                elif 'xrmemcachesize' in list(_dbp.keys()) and _dbp['xrmemcachesize']:
                    _dbpstring = _dbpstring + ", pmemCacheSize=" + _dbp['xrmemcachesize']
                
                if self.mGetEbox().mGetEnableAsmss() == "true" and _dbp['dbname'].lower() != "default" and 'asmcluster' in _dbp.keys():
                    _dbpstring = _dbpstring + ", asmcluster=" + _dbp['asmcluster'] 
                    
                if 'is_fc_size' in list(_dbp.keys()) and _dbp['is_fc_size'] == "True":
                    _dbpstring = _dbpstring + "),"
                else:
                    if _dbflashlimit[_dbp['dbname']]:
                        _dbpstring = _dbpstring + ", flashCacheLimit=" + _dbflashlimit[_dbp['dbname']] + "),"
                    else:
                        _dbpstring = _dbpstring + "),"
                    
                

            # Remove trailing comma and complete command string
            _dbpstring = _dbpstring[:-1]
            _dbpstring = _dbpstring + ")"
            
            # if-else end
            return _dbpstring
        
        # Method to check if pmemcache is configured/enabled on the cells
        def mCheckPmemCachePresent(self, aOptions, aIormdata=None):

            _options = aOptions
            if aIormdata is None:
                _iormdata = self.mGetData()
            else:
                _iormdata = aIormdata

            _iormdata["Status"] = "Pass"
            _iormdata["cell"] = {}
            _iormdata["ErrorCode"] = "0"

            _cells    = self.mGetCells()
            _iormcmd = self.mGetIormCommands()
            _key = _iormcmd["pmemcexist"]

            # Execute commands on each cell
            _cmd = "cellcli -e list pmemcache detail"

            def _mExecute(aCell, aList):
                _cell = aCell
                _list = aList

                _iormdata["cell"][_cell] = {}
                _i, _o, _e = self.mExecCommandOnCell(_cell, _options, _cmd)
                if str(_e) == "0":
                    if not _o:
                        _iormdata["cell"][_cell]["pmemcexist"] = False
                    else:
                        _iormdata["cell"][_cell]["pmemcexist"] = True     
                else:
                    _iormdata["cell"][_cell]["pmemcexist"] = None
                    _iormdata["cell"][_cell]["errorCode"] = str(_e)
                    _iormdata["cell"][_cell]["log"] = gResError[str(_e)]

                _list.append([_cell, _iormdata["cell"][_cell]])

            _plist = ProcessManager()
            _list = _plist.mGetManager().list()

            # Parallelize execution on cells
            for _cell in _cells:
                _p = ProcessStructure(_mExecute, [_cell, _list], _cell)
                _p.mSetMaxExecutionTime(MULTIPROCESSING_MAXEXECUTION_TIMEOUT)
                _p.mSetJoinTimeout(60)
                _p.mSetLogTimeoutFx(ebLogWarn)
                _plist.mStartAppend(_p)
                ebLogTrace('%s : _mExecute started for %s ' %(_p.name, _cell))

            _plist.mJoinProcess()
            ebLogTrace('All processes completed their call to _mExecute.')

            for _entry in _list:
                _iormdata["cell"][_entry[0]] = _entry[1]

            for _cell in _cells:
                if _iormdata["cell"][_cell]["pmemcexist"] == None:
                    ebLogError("Fetching pmem status from %s failed" %(_cell))
                    _iormdata["Status"] = "Fail"
                    _iormdata["ErrorCode"] = "836"
                    _iormdata["Log"] = gResError[_iormdata["ErrorCode"]][0]
                    ebLogInfo("%s" %(str(_iormdata["Log"])))
                    return None

            _pmlist = []
            for _cell in _cells:
                _pmlist.append(_iormdata["cell"][_cell]["pmemcexist"])

            if all(_pmlist) == False:
                _iormdata[_key] = "None"
                _iormdata["Status"] = "Fail"
                _iormdata["ErrorCode"] = "839"
                _iormdata["Log"] = gResError[_iormdata["ErrorCode"]][0]
                ebLogInfo("%s" %(str(_iormdata["Log"])))
                return False
            else:
                ebLogInfo(f"Pmemcache exist across all cells")
                _iormdata["Log"] = "Pmemcache found across all cells: {_cells}"
                return True
        # end
        
        def mClusterSetDbPlan(self, aOptions):
            _options = aOptions
            _objective = None
            _dbplist = []
            _dbpstring = None

            _iormdata = self.mGetData()
            _iormdata["Status"] = "Pass"
            _iormdata["ErrorCode"] = "0"
            _iormdata["cell"] = {}

            TBFACTOR = 1<<40
            GBFACTOR = 1<<30
            MBFACTOR = 1<<20

            _cells    = self.mGetCells()
            _iormcmd = self.mGetIormCommands()
            _dbplan = _iormcmd["dbplan"]
            _flashsize = _iormcmd["fcsize"]
            _inputjson = _options.jsonconf 
            
            if (_options.resmanage == "resetdbplan"):
                _dbpstring = "dbPlan=\"\""
            else:
                #check if _inputjson is present. Else return Error
                if not _inputjson:
                    return self.mRecordError("808")
                _key = 'dbPlan'
                for k in _inputjson.keys():
                    if k.lower() == _dbplan.lower():
                        _key = k
                        break
                if _key not in list(_inputjson.keys()):
                    return self.mRecordError("814")
                
                #check if pmemcache is present for the cells.
                _pmem_present = False
                _pmem_present = self.mCheckPmemCachePresent(_options)

                # Copy the DB plan entries into a list
                _inputdbplist = _inputjson[_key]
                _pmem_attributes = ['pmemcachemin','pmemcachesize','pmemcachelimit']
                for _dbp in _inputdbplist:
                    if 'dbname' not in list(_dbp.keys()) or not _dbp['dbname']:
                        return self.mRecordError("815")
                    elif 'share' not in list(_dbp.keys()) or not _dbp['share']:
                        return self.mRecordError("816")
                    if any(_dbp.get(pmem_attr) is not None for pmem_attr in _pmem_attributes) and not _pmem_present:
                        return self.mRecordError("839")

                #retrieve the existing dbplan from cells. Only if the dbplan across all cells are same, proceed with the setdbplan.
                #else raise error.    
                _rc = self.mClusterGetDbPlan(_options)
                _hasPreviousEntries = True

                if "No IORM DB Plan has been set" in _iormdata["Log"]:
                    ebLogInfo(f"No DbPlan is set. Continuing with setdbplan")
                    _hasPreviousEntries = False
                elif _rc:
                    ebLogError(f"Cannot proceed with set dbplan. Because dbplan varies across cells")
                    _iormdata["ErrorCode"]= "827"
                    ebLogTrace(f"iormdata: {_iormdata}")
                    return self.mRecordError(_iormdata["ErrorCode"])
                elif _rc == 0:
                    ebLogInfo(f"DbPlan is same across the cells. Proceeding with the appending of new DB plan.")
                    ebLogTrace(f"iormdata: {_iormdata}")
                
                _existing_db_plan = _iormdata[_dbplan] if _hasPreviousEntries else []

                # Modify _existing_db_plan to normalize keys
                ebLogTrace(f"Existing DB plan before key normalization: {_existing_db_plan}")
                for _index, _entry in enumerate(_existing_db_plan):
                    for _key, _val in _entry.items():
                        if _key == 'name':
                            _temp = str(_val)
                            del _entry[_key]
                            _entry['dbname'] = _temp
                            _existing_db_plan[_index] = _entry

                ebLogTrace(f"Existing DB plan after key normalization: {_existing_db_plan}")

                # Typecast each entry's set of values to string
                for _index, _entry in enumerate(_inputdbplist):
                    for _key, _val in _entry.items():
                        if _val is None:
                            continue
                        if isinstance(_val, str):
                            continue
                        _entry[_key] = str(_val)
                        _inputdbplist[_index] = _entry

                for _index, _entry in enumerate(_existing_db_plan):
                    for _key, _val in _entry.items():
                        if _val is None:
                            continue
                        if isinstance(_val, str):
                            continue
                        _entry[_key] = str(_val)
                        _existing_db_plan[_index] = _entry

                ebLogTrace(f"Input DB plan list after typecast: {_inputdbplist}")
                ebLogTrace(f"Existing DB plan after typecast: {_existing_db_plan}")

                # Retrieve DB plan list
                _dbplist, _defExists, _existing_default = self.mGetDBPlanList(_existing_db_plan, _inputdbplist)
                
                _iormdata["Status"] = "Pass"
                _iormdata["ErrorCode"] = "0"
                _iormdata["cell"] = {}
                    
                # Add a 'default' entry if not already specified by the user
                if not _defExists:
                    _sharedefault = "0"
                    for _dbp in _dbplist:
                        if (int(_sharedefault) == 0) or (int(_sharedefault) > int(_dbp['share'])):
                            _sharedefault = _dbp['share']

                    _dbptemp = {}
                    _dbptemp['dbname'] = "default"
                    _dbptemp['share'] = _sharedefault
                    ebLogTrace(f"share default value: {_sharedefault}")
                    if _existing_default:
                        for _attribute in _existing_default:
                            if _attribute != 'share' and _attribute != 'dbname':
                                _dbptemp[_attribute] = _existing_default[_attribute]
                    _dbplist.append(_dbptemp)
                    
                # Read the flash cache size
                _fcsizedata = {}
                self.mClusterFcSize(_options, _fcsizedata)
                if _fcsizedata["Status"] == "Fail":
                    return self.mRecordError("807")
                else:
    
                    _fcsstr = _fcsizedata[_flashsize]
                    _fcsize = _fcsstr[:-1]
                    _fcstype = _fcsstr[-1:]

                    _fcsnum = float(_fcsize)
                    _fcsint = None

                    if _fcstype == "T":
                        _fcsint = _fcsnum * TBFACTOR
                    elif _fcstype == "G":
                        _fcsint = _fcsnum * GBFACTOR
                    elif _fcstype == "M":
                        _fcsint = _fcsnum * MBFACTOR

                # Determine total share
                _totalshare = 0
                for _dbp in _dbplist:
                    if not (_dbp['share'].isdecimal()):
                        return self.mRecordError("818", " : " + _dbp['share'])

                    # Share must be within 1 to 32
                    _shareval = int(_dbp['share'])
                    if (_shareval == 0) or (_shareval > 32):
                        return self.mRecordError("819", " : " + _dbp['share'])

                    _totalshare = _totalshare + int(_shareval)

                ebLogInfo("Total share of all DB instances: %d" %(_totalshare))

                # Calculate flashcacheLimit for each DB
                # Overprovisioning rule is 2X
                _dbflashlimit = {}
                for _dbp in _dbplist:
                    if 'flashcachelimit' in list(_dbp.keys()) and _dbp['flashcachelimit']:
                        ebLogInfo(f"Flashcachelimit is present in the dbplan. So appending")
                        _dbflashlimit[_dbp['dbname']] = _dbp['flashcachelimit']
                    else:
                        _fclratio = (float(_dbp['share'])/float(_totalshare)) * 2
                        _fclimit = _fclratio * float(_fcsint)
                        if _fcstype == "T":
                            _fclimit = _fclimit / GBFACTOR
                            _fcsg = float(_fcsint / GBFACTOR)
                            if _fclimit > _fcsg:
                                _fclimit = _fcsg
                            _dbflashlimit[_dbp['dbname']] = str(decimal.Decimal(_fclimit).quantize(decimal.Decimal(10) ** -11)) + "G"
                        elif _fcstype == "G":
                            _fclimit = _fclimit / MBFACTOR
                            _fcsm = float(_fcsint / MBFACTOR)
                            if _fclimit > _fcsm:
                                _fclimit = _fcsm
                            _dbflashlimit[_dbp['dbname']] = str(decimal.Decimal(_fclimit).quantize(decimal.Decimal(10) ** -8)) + "M"
                        elif _fcstype == "M":
                            _fclimit = _fclimit / MBFACTOR
                            _fcsm = float(_fcsint / MBFACTOR)
                            if _fclimit > _fcsm:
                                _fclimit = _fcsm
                            _dbflashlimit[_dbp['dbname']] = str(decimal.Decimal(_fclimit).quantize(decimal.Decimal(10) ** -8)) + "M"
                
                # Create the dbplan string
                _dbpstring = self.mCreateDBPlanString(_dbplist, _dbflashlimit)
                ebLogTrace(f"DBPLAN string: {_dbpstring}")

            # Execute commands on each cell
            _cmd = "cellcli -e \'alter iormplan " + _dbpstring + "\'"
            
            def _mExecute(aCell, aList):
                _cell = aCell
                _list = aList

                _iormdata["cell"][_cell] = {}
                _i, _o, _e = self.mExecCommandOnCell(_cell, _options, _cmd)
                _iormdata["cell"][_cell]["errorCode"] = str(_e)
                _iormdata["cell"][_cell]["log"] = gResError[str(_e)]

                _list.append([_cell, _iormdata["cell"][_cell]])

            _plist = ProcessManager()
            _list = _plist.mGetManager().list()

            # Parallelize execution on cells
            for _cell in _cells:
                _p = ProcessStructure(_mExecute, [_cell, _list], _cell)
                _p.mSetMaxExecutionTime(MULTIPROCESSING_MAXEXECUTION_TIMEOUT)
                _p.mSetJoinTimeout(60)
                _p.mSetLogTimeoutFx(ebLogWarn)
                _plist.mStartAppend(_p)
                ebLogTrace('%s : _mExecute started for %s ' %(_p.name, _cell))
            
            _plist.mJoinProcess()
            ebLogTrace('All processes completed their call to _mExecute.')

            for _entry in _list:
                _iormdata["cell"][_entry[0]] = _entry[1]

            for _cell in _cells:
                if _iormdata["cell"][_cell]["errorCode"] != "0":
                    ebLogInfo("Creating IORM DB Plan on %s failed" %(_cell))
                    _iormdata["Status"] = "Fail"
                    _iormdata["ErrorCode"] = _iormdata["cell"][_cell]["errorCode"]

            if _iormdata["Status"] == "Fail":
                ebLogInfo("Creating IORM DB Plan on the cluster failed")
                _iormdata["Log"] = "Creating IORM DB Plan on the cluster failed"
            else:
                ebLogInfo("Creating IORM DB Plan on the cluster succeeded")
                _cell = _iormdata["cell"]
                _rc = self.mClusterGetDbPlan(_options)
                _iormdata["Log"] = "Creating IORM DB Plan on the cluster succeeded"
                _iormdata["cell"] = _cell

            if _iormdata["ErrorCode"] != "0":
                return self.mRecordError(_iormdata["ErrorCode"])

            # This reads the objective (if it exists) from dbplan.json and sets the objective to the input value
            if _inputjson is not None and 'objective' in list(_inputjson.keys()) and _inputjson['objective']:
                self.mClusterSetObjective(_options,aObjective = _inputjson["objective"])

        # end

        # Method to read the IORM DB Plan from the cells
        def mClusterGetDbPlan(self, aOptions):

            _options = aOptions

            _iormdata = self.mGetData()
            _iormdata["Status"] = "Pass"
            _iormdata["cell"] = {}
            _iormdata["ErrorCode"] = "0"

            _cells    = self.mGetCells()

            _iormcmd = self.mGetIormCommands()
            _key = _iormcmd["dbplan"]

            # Execute commands on each cell
            _cmd = "cellcli -e list iormplan detail"

            for _cell in _cells:
                _iormdata["cell"][_cell] = {}

            def _mExecute(aCell, aList):
                _cell = aCell
                _list = aList

                _i, _o, _e = self.mExecCommandOnCell(_cell, _options, _cmd)
                if str(_e) == "0":
                    _gdbpe = self.mParseGetIORMPlan(_cell, _iormdata, _o, "dbPlan")
                    _iormdata["cell"][_cell]["errorCode"] = str(_gdbpe)
                    _iormdata["cell"][_cell]["log"] = gResError[str(_gdbpe)]
                else:
                    _iormdata["cell"][_cell]["errorCode"] = str(_e)
                    _iormdata["cell"][_cell]["log"] = gResError[str(_e)]

                _list.append([_cell, _iormdata["cell"][_cell]])

            _plist = ProcessManager()
            _list = _plist.mGetManager().list()
            
            # Parallelize execution on cells
            for _cell in _cells:
                _p = ProcessStructure(_mExecute, [_cell, _list], _cell)
                _p.mSetMaxExecutionTime(MULTIPROCESSING_MAXEXECUTION_TIMEOUT)
                _p.mSetJoinTimeout(60)
                _p.mSetLogTimeoutFx(ebLogWarn)
                _plist.mStartAppend(_p)
                ebLogTrace('%s : _mExecute started for %s ' %(_p.name, _cell))
            
            _plist.mJoinProcess()
            ebLogTrace('All processes completed their call to _mExecute.')

            for _entry in _list:
                
                _iormdata["cell"][_entry[0]] = _entry[1]
            for _cell in _cells:

                if _iormdata["cell"][_cell]["errorCode"] != "0":
                    _iormdata["Status"] = "Fail"
                    _iormdata["ErrorCode"] = _iormdata["cell"][_cell]["errorCode"]

                if "dbPlan" not in _iormdata["cell"][_cell]: 
                    ebLogInfo("Fetching IORM DB Plan from %s failed" %(_cell))
                    _iormdata["Status"] = "Fail"

            # Format, store results
            if _iormdata["Status"] == "Pass":
                _iormdata["Log"] = "Common IORM DB Plan found across cells"
                _idata = []
                for _cell in _cells:
                    if not _idata:
                        _idata = _iormdata["cell"][_cell]["dbPlan"]
                    else:
                        _new_idata = _iormdata["cell"][_cell]["dbPlan"]
                        _is_dbplan_same = sorted(_idata, key = lambda ele: sorted(ele.items())) == sorted(_new_idata, key = lambda ele: sorted(ele.items()))
                        if not _is_dbplan_same:
                            _iormdata["Status"] = "Fail"
                            _iormdata["Log"] = "IORM DB Plan varies across cells"
                            _iormdata["ErrorCode"]= "827"
                            break

                _eBox = self.mGetEbox()
                if not _idata:
                    _idata = []
                    if not _eBox.mIsExabm():
                        _idata.append("None")
                    _iormdata["Log"] = "No IORM DB Plan has been set on the cells"
                else:
                    if _eBox.mIsExabm():
                        for _data in _idata:
                            _data["dbname"] = _data.pop("name")
                            
                if _iormdata["Status"] == "Pass":
                    _iormdata[_key] = _idata
                    _iormdata.pop("cell", None)
                    
                    _iormdata["cell"] = []
                    for _cell in _cells:
                        _iormdata["cell"].append(_cell)

            if not _options.jsonmode:
                if _iormdata["Status"] == "Pass":
                    ebLogInfo("%s" %(_iormdata["Log"]))
                    if (len(_iormdata[_key]) != 1):
                        ebLogInfo("DBPLAN:")
                        for _dbPlan in _iormdata[_key]:
                            for _attribute, _value in list(_dbPlan.items()):
                                ebLogInfo("\t DB Name: %s" %(_value)) if _attribute == 'name' else ebLogInfo("\t %s : %s" %(_attribute, _value))
                else:
                    for _cell in _cells:
                        ebLogInfo("IORM Db Plan for %s" %(_cell))
                        for _line in _iormdata["cell"][_cell]["dbPlan"]:
                            ebLogInfo("%s" %(_line))

            if _iormdata["ErrorCode"] != "0":
                return self.mRecordError(_iormdata["ErrorCode"])
            else:
                return 0

        # end
                
        # Method to set the IORM Cluster Plan on all the cells
        def mSetClusterPlan(self, aOptions):
            _options = aOptions
            _clusterpstring = None
            _iormdata = self.mGetData()
            _iormdata["Status"] = "Pass"
            _iormdata["ErrorCode"] = "0"
            _iormdata["cell"] = {}

            if _options.resmanage == "resetclusterplan":
                _clusterpstring = "clusterplan=\"\""
            else:
                _clusterplist = []
                _iormcmd = self.mGetIormCommands()
                _clusterplan = _iormcmd["clusterplan"]
                # Parse the input JSON and read the objective
                _inputjson = _options.jsonconf 
                if not _inputjson:
                    return self.mRecordError("808")
                elif _clusterplan not in list(_inputjson.keys()) or not _inputjson[_clusterplan]:
                    return self.mRecordError("830")
                
                #check if mGetClusterPlan returns success - meaning clusterplan is same across all cells.
                #If same, then mSetClusterPlan will append the new clusterplan to existing plan and avoid duplicate entries for the same db.
                #Else, Exacloud will error out saying clusterplan varies across the cells. 
                #What to do when clusterplan differ across cells? This is to be discussed in future. 
                #Currently we safely assume that clusterplan will be the same across all cells. That is the way it is supposed to be.
                _rc = self.mGetClusterPlan(_options)
                if _rc:
                    ebLogError(f"Cannot proceed with set cluster. Because clusterplan varies across cells")
                    _iormdata["ErrorCode"]= "828"
                    ebLogInfo(f"iormdata populated: {_iormdata}")
                    return self.mRecordError(_iormdata["ErrorCode"])
                else:
                    ebLogInfo(f"Clusterplan is same across the cells. Proceeding with the appending of new cluster plan.")
                    ebLogInfo(f"iormdata populated: {_iormdata}")
                _existing_cluster_plan = []
                _existing_cluster_plan = _iormdata[_clusterplan]
                ebLogInfo(f"_existing cluster plan: {_existing_cluster_plan}")
                    
                _iormdata["Status"] = "Pass"
                _iormdata["ErrorCode"] = "0"
                _iormdata["cell"] = {}
                
                # Copy the Cluster plan entries into a list and check if required attributes are present.
                #name and share are the mandatory attributes for all clusterplans.
                _clusterplist = _inputjson[_clusterplan]
                ebLogInfo(f"clusterlist from input payload: {_clusterplist}")
                for _clusterp in _clusterplist:
                    if 'name' not in list(_clusterp.keys()) or not _clusterp['dbname']:
                        return self.mRecordError("831")
                    elif 'share' not in list(_clusterp.keys()) or not _clusterp['share']:
                        return self.mRecordError("832")
                    
                # Validate share values in payload. It should be digit.
                for _clusterp in _clusterplist:
                    if (_clusterp['share'].isdigit() == False):
                        return self.mRecordError("833", " : " + _clusterp['share'])
                    # Share must be within 1 to 32
                    _shareval = int(_clusterp['share'])
                    if (_shareval == 0) or (_shareval > 32):
                        return self.mRecordError("834", " : " + _clusterp['share'])

                #this part takes care of appending the new clusterplan from payload to the existing clusterplan
                #while replacing the old clusterplan with new clusterplan if the new clusterplan contains the same name as in old clusterplan
                _existing_clusterplan_dict = {_clup['dbname']:_clup for _clup in _existing_cluster_plan}
                _new_cluster_plan = []
                for _cluplan in _clusterplist:
                    name = _cluplan['dbname']
                    if name in _existing_clusterplan_dict:
                        _existing_clusterplan_dict[name] = _cluplan
                    else:
                        _new_cluster_plan.append(_cluplan)
                
                _new_cluster_plan.extend(_existing_clusterplan_dict.values()) 
                ebLogInfo(f"New cluster plan after appending: {_new_cluster_plan}")
                
                #default entry is not valid for clusterplan. Cellcli command itself produces the error: CELL-00004: The ALTER IORMPLAN command contains an invalid name DEFAULT.
                #so there would not be default entry appended to clusterplan.
                
                # Create the clusterplan string for cellcli command formation
                _clusterpstring = "clusterplan=("
                for _clusterp in _new_cluster_plan:

                    _clusterpstring = _clusterpstring + "(name=" + _clusterp['dbname'] + ","
                    _clusterpstring = _clusterpstring + " share=" + _clusterp['share'] + "),"
                        
                # Remove trailing comma and complete command string
                _clusterpstring = _clusterpstring[:-1]
                _clusterpstring = _clusterpstring + ")"
                
                # if-else end

            # Execute commands on each cell
            _cmd = "cellcli -e \'alter iormplan " + _clusterpstring + "\'"
            
            def _mExecute(aCell, aList):
                _cell = aCell
                _list = aList

                _iormdata["cell"][_cell] = {}
                _i, _o, _e = self.mExecCommandOnCell(_cell, _options, _cmd)
                _iormdata["cell"][_cell]["errorCode"] = str(_e)
                _iormdata["cell"][_cell]["log"] = gResError[str(_e)]

                _list.append([_cell, _iormdata["cell"][_cell]])

            _plist = ProcessManager()
            _list = _plist.mGetManager().list()
            _cells    = self.mGetCells()
            # Parallelize execution on cells
            for _cell in _cells:
                _p = ProcessStructure(_mExecute, [_cell, _list], _cell)
                _p.mSetMaxExecutionTime(MULTIPROCESSING_MAXEXECUTION_TIMEOUT)
                _p.mSetJoinTimeout(60)
                _p.mSetLogTimeoutFx(ebLogWarn)
                _plist.mStartAppend(_p)
                ebLogTrace(f"{_p.name} : _mExecute started for {_cell} ")
            
            _plist.mJoinProcess()
            ebLogTrace('All processes completed their call to _mExecute.')

            for _entry in _list:
                _iormdata["cell"][_entry[0]] = _entry[1]

            for _cell in _cells:
                if _iormdata["cell"][_cell]["errorCode"] != "0":
                    ebLogInfo(f"Creating IORM Cluster Plan on {_cell} failed")
                    _iormdata["Status"] = "Fail"
                    _iormdata["ErrorCode"] = _iormdata["cell"][_cell]["errorCode"]

            if _iormdata["Status"] == "Fail":
                ebLogInfo("Creating IORM Cluster Plan failed")
                _iormdata["Log"] = "Creating IORM Cluster Plan failed"
            else:
                ebLogInfo("Creating IORM Cluster Plan succeeded")
                _iormdata["Log"] = "Creating IORM Cluster Plan succeeded"

            if _iormdata["ErrorCode"] != "0":
                return self.mRecordError(_iormdata["ErrorCode"])

        # end
        
        # Method to read the IORM Cluster Plan from the cells
        def mGetClusterPlan(self, aOptions):

            _options = aOptions

            _iormdata = self.mGetData()
            _iormdata["Status"] = "Pass"
            _iormdata["cell"] = {}
            _iormdata["ErrorCode"] = "0"

            _cells    = self.mGetCells()

            _iormcmd = self.mGetIormCommands()
            _key = _iormcmd["clusterplan"]

            # Execute commands on each cell
            _cmd = "cellcli -e list iormplan detail"

            for _cell in _cells:
                _iormdata["cell"][_cell] = {}

            def _mExecute(aCell, aList):
                _cell = aCell
                _list = aList

                _i, _o, _e = self.mExecCommandOnCell(_cell, _options, _cmd)
                if str(_e) == "0":
                    _gclupe = self.mParseGetIORMPlan(_cell, _iormdata, _o, "clusterPlan")
                    _iormdata["cell"][_cell]["errorCode"] = str(_gclupe)
                    _iormdata["cell"][_cell]["log"] = gResError[str(_gclupe)]
                else:
                    _iormdata["cell"][_cell]["errorCode"] = str(_e)
                    _iormdata["cell"][_cell]["log"] = gResError[str(_e)]

                _list.append([_cell, _iormdata["cell"][_cell]])

            _plist = ProcessManager()
            _list = _plist.mGetManager().list()
            
            # Parallelize execution on cells
            for _cell in _cells:
                _p = ProcessStructure(_mExecute, [_cell, _list], _cell)
                _p.mSetMaxExecutionTime(MULTIPROCESSING_MAXEXECUTION_TIMEOUT)
                _p.mSetJoinTimeout(60)
                _p.mSetLogTimeoutFx(ebLogWarn)
                _plist.mStartAppend(_p)
                ebLogTrace('%s : _mExecute started for %s ' %(_p.name, _cell))
            
            _plist.mJoinProcess()
            ebLogTrace('All processes completed their call to _mExecute.')

            for _entry in _list:
                _iormdata["cell"][_entry[0]] = _entry[1]

            for _cell in _cells:

                if _iormdata["cell"][_cell]["errorCode"] != "0":
                    _iormdata["Status"] = "Fail"
                    _iormdata["ErrorCode"] = _iormdata["cell"][_cell]["errorCode"]

                if "clusterPlan" not in _iormdata["cell"][_cell]: 
                    ebLogInfo("Fetching IORM Cluster Plan from %s failed" %(_cell))
                    _iormdata["Status"] = "Fail"

            # Format, store results
            if _iormdata["Status"] == "Pass":
                _iormdata["Log"] = "Common IORM Cluster Plan found across cells"
                _idata = []
                for _cell in _cells:
                    if not _idata:
                        _idata = _iormdata["cell"][_cell]["clusterPlan"]
                    else:
                        if (_idata != _iormdata["cell"][_cell]["clusterPlan"]):
                            _iormdata["Status"] = "Fail"
                            _iormdata["Log"] = "IORM Cluster Plan varies across cells"
                            _iormdata["ErrorCode"]= "828"
                            break

                _eBox = self.mGetEbox()
                if not _idata:
                    _idata = []
                    if not _eBox.mIsExabm():
                        _idata.append("None")
                    _iormdata["Log"] = "No IORM Cluster Plan has been set on the cells"

                if _iormdata["Status"] == "Pass":
                    _iormdata[_key] = _idata
                    _iormdata.pop("cell", None)
                    
                    _iormdata["cells"] = []
                    for _cell in _cells:
                        _iormdata["cells"].append(_cell)

            if not _options.jsonmode:
                if _iormdata["Status"] == "Pass":
                    ebLogInfo("%s" %(_iormdata["Log"]))
                    if (len(_iormdata[_key]) != 1):
                        ebLogInfo("CLUSTER PLAN:")
                        for _clusterPlan in _iormdata[_key]:
                            for _attribute, _value in list(_clusterPlan.items()):
                                ebLogInfo("\t Cluster Name: %s" %(_value)) if _attribute == 'name' else ebLogInfo("\t %s : %s" %(_attribute, _value))
                else:
                    for _cell in _cells:
                        ebLogInfo("IORM Cluster Plan for %s" %(_cell))
                        for _line in _iormdata["cell"][_cell]["clusterPlan"]:
                            ebLogInfo("%s" %(_line))

            if _iormdata["ErrorCode"] != "0":
                return self.mRecordError(_iormdata["ErrorCode"])
            else:
                return 0

        # end

        # Method to (re)create a flash cache on each cell. Uses all flash cache disks
        # Also drops the flashcache if aCreate=False
        def mClusterCreateFlash(self, aOptions, aCreate=True):

            _options = aOptions
            _objective = None

            _iormdata = self.mGetData()
            _iormdata["Status"] = "Pass"
            _iormdata["ErrorCode"] = "0"

            _cells    = self.mGetCells()

            _iormdata["cell"] = {}

            #
            # Check if flashCache already exists on the cell
            #
            def check_flashExists(_cell):
                _cmd = 'cellcli -e list flashcache detail | grep status'
                _node=exaBoxNode(get_gcontext())
                _node.mConnect(aHost=_cell)
                _i, _o, _e = _node.mExecuteCmd(_cmd)
                _output = _o.readlines()
                _status_dict = {}
                if _output:
                    for _status in _output:
                        k,v = _status.split(':')
                        k = k.strip()
                        v = v.strip()
                        _status_dict[k] = v
                _node.mDisconnect()
                # flashCache status
                if 'status' in list(_status_dict.keys()) and _status_dict['status'].upper() == 'NORMAL':
                    ebLogInfo("Cell %s already has a flashcache setup" %(_cell))
                    return True
                else:
                    ebLogInfo("Cell %s does not have a flashcache" %(_cell))
                    return False

            # Execute commands on each cell
            if aCreate:
                ebLogInfo("Creating flashcache on all cells")
                _cmds_list = ['cellcli -e "alter cell flashCacheMode=writeback"', 'cellcli -e create flashcache all'
                    ]
            else:
                ebLogInfo("Dropping flashcache on all cells")
                _cmds_list = ['cellcli -e alter flashcache all flush', 'cellcli -e drop flashcache'
                    ]

            def _mExecute(aCell, aList):
                _cell = aCell
                _list = aList

                _iormdata["cell"][_cell] = {}
                _iormdata["cell"][_cell]["errorCode"] = ""
                _iormdata["cell"][_cell]["log"] = ""

                if aCreate:
                    if check_flashExists(_cell): return

                for _cmd in _cmds_list:
                    ebLogInfo("Executing %s on %s" %(_cmd, _cell))
                    _i, _o, _e = self.mExecCommandOnCell(_cell, _options, _cmd)
                    _iormdata["cell"][_cell]["errorCode"] = str(_e)
                    _iormdata["cell"][_cell]["log"] = gResError[str(_e)]

                _list.append([_cell, _iormdata["cell"][_cell]])

            _plist = ProcessManager()
            _list = _plist.mGetManager().list()
            
            # Parallelize execution on cells
            for _cell in _cells:
                _p = ProcessStructure(_mExecute, [_cell, _list], _cell)
                _p.mSetMaxExecutionTime(MULTIPROCESSING_MAXEXECUTION_TIMEOUT)
                _p.mSetJoinTimeout(60)
                _p.mSetLogTimeoutFx(ebLogWarn)
                _plist.mStartAppend(_p)
                ebLogTrace('%s : _mExecute started for %s ' %(_p.name, _cell))
            
            _plist.mJoinProcess()
            ebLogTrace('All processes completed their call to _mExecute.')

            for _entry in _list:
                _iormdata["cell"][_entry[0]] = _entry[1]

            for _cell in _cells:
                if _iormdata["cell"][_cell]["errorCode"] != "0":
                    ebLogInfo("Creating flashcache on %s failed" %(_cell))
                    _iormdata["Status"] = "Fail"
                    _iormdata["ErrorCode"] = _iormdata["cell"][_cell]["errorCode"]
                    break            
 
            if aCreate:
                _op = "Creating"
            else:
                _op = "Dropping"

            if _iormdata["Status"] == "Fail":
                ebLogInfo("%s flashcache on the cluster failed" %(_op))
                _iormdata["Log"] = _op + " flashcache on the cluster failed"
            else:
                ebLogInfo("%s flashcache on the cluster succeeded" %(_op))
                _iormdata["Log"] = _op + " flashcache on the cluster succeeded"

            if _iormdata["ErrorCode"] != "0":
                return self.mRecordError(_iormdata["ErrorCode"])
            else:
                return 0

        # end

        # Common method to execute a cellcli command
        #
        # On success, a list containing lines from the output
        # will be returned along with 0 as error code. If any
        # failure occurs, a log message and the appropriate 
        # error code is returned
        #
        # We now use this method to execute on domU as well
        def mExecCommandOnCell(self, aCell, aOptions, aCmd):

            _cell = aCell
            _options = aOptions
            _cmd = aCmd
            _i = None
            _o = None
            _e = None
            _error = 0
            _eBox = self.mGetEbox()

            if not _eBox.mPingHost(_cell):
                ebLogInfo("Failed to ping %s" %(_cell))
                _o = "Failed to ping " + _cell
                _e = 800
                return _i, _o, _e

            # Connect to the cell
            _node = exaBoxNode(get_gcontext())
            try:
                _node.mConnect(aHost=_cell)
            except:
                ebLogWarn('*** Failed to connect to: %s' %(_cell))
                _o = "Failed to connect to " + _cell
                _e = 801
                return _i, _o, _e
         
            _i, _o, _e = _node.mExecuteCmd(_cmd)
            _out = _o.readlines()
            if _node.mGetCmdExitStatus():
                ebLogInfo("Error running cellcli/command on %s" %(_cell))
                ebLogInfo("Output returned from cell/domU %s is" %(_cell))
                for _line in _out:
                    ebLogInfo("%s" %(_line))
                _o = "Error running cellcli/command on " + _cell
                _e = 802
                _node.mDisconnect()
                return _i, _o, _e
            else:
                _e = 0
                _node.mDisconnect()
                return _i, _out, _e

        # end

        # Parse the output received from cell and return flashcach/pmemcache size
        def mParseCacheOutput(self, aO, CacheType):

            _out = aO
            _csize = None
            _error = None
            _cache_type = CacheType
            if _cache_type == "flashcache":
                _error = 805
            elif _cache_type == "pmemcache":
                _error = 829

            for _line in _out:
                _csize = _line.split(":")[1].rstrip().lstrip()
                _error = 0

            return _csize, _error

        # end

        # Parse the output received from cell and return list of DBs
        def mParseDbListOutput(self, aO):

            _out = sorted(aO)
            _dblist = None
            _error = 804

            for _line in _out:
                if "ASM" in _line: # Ignore the ASM instance
                    continue
                if _dblist == None:
                    _dblist = _line.lstrip().rstrip()
                else:
                    _dblist = _dblist + "," + _line.lstrip().rstrip()

            if _dblist is not None:
                _error = 0

            return _dblist, _error

        # end

        # Parse the output received from cell and return IORM objective
        def mParseGetObjOutput(self, aO):

            _out = aO
            _fcsize = None
            _error = 813

            for _line in _out:
                _fcsize = _line.split(":")[1].rstrip().lstrip()
                _error = 0

            return _fcsize, _error

        # end

        # Parse the output received from cell and return IORM DB/Cluster Plan according to the type specified
        def mParseGetIORMPlan(self, aCell, aIormdata, aO, aDataType):

            _cell = aCell
            _iormdata = aIormdata
            _out = aO
            _iorm_data_type = aDataType
            _index = -1
            _iormdata["cell"][_cell][_iorm_data_type] = []

            for _line in _out:
                if _line.strip().startswith(_iorm_data_type):
                    _index = _out.index(_line)
                    break 
            if _index !=-1:
                for _line in _out[_index:]:
                    if _iorm_data_type in _line:
                        _line = _line.split(":")[1].rstrip().lstrip()
                    elif ":" in _line and _iorm_data_type not in _line:
                        break
                    else:
                        _line = _line.rstrip().lstrip()
                    if "name" in _line:
                        _kvpairs = _line.split(",")
                        _iormplan = {}

                    # Store the attribute name and value
                        for _kvp in _kvpairs:
                            _iormplan[_kvp.split("=")[0]] = _kvp.split("=")[1]
                        ebLogTrace(f"_iormplan to append to _iormdata: {_iormplan}")
                        _iormdata["cell"][_cell][_iorm_data_type].append(_iormplan)
                    
            return 0

        # end
        
        
        # Common method to log error code and error message
        def mRecordError(self, aErrorCode, aString=None):

            _data = self.mGetData()

            _data["Status"] = "Fail"
            _data["ErrorCode"] = aErrorCode
            if aString is None:
                _data["Log"] = gResError[_data["ErrorCode"]][0]
            else:
                _data["Log"] = gResError[_data["ErrorCode"]][0] + aString
            ebLogWarn("%s" %(_data["Log"]))

            # Use the error code as a hexadecimal value to return a value 
            # which can be used in Agent.py:thread_ctrl_cmd() to obtain the
            # error.
            _rc = (-1<<16) | int("0x" + aErrorCode, 16)

            return _rc

        # end

        def mGetEbox(self):
            return self.__ebox

        def mGetCells(self):
            return self.__cells

        def mSetCells(self, aCells):
            self.__cells = aCells

        def mGetDomUs(self):
            return self.__domUs

        def mSetDomUs(self, aDomUs):
            self.__domUs = aDomUs

        def mGetData(self):
            return self.__data

        def mSetData(self, aData):
            self.__data = aData

        # 
        # Populates aIormdata with the list of client keys 
        # (client name, client key, client type)
        # 
        def mClusterGetClientKeys(self, aOptions, aIormdata=None):

            _options = aOptions

            if aIormdata is None:
                _iormdata = self.mGetData()
            else:
                _iormdata = aIormdata

            _iormcmd = self.mGetIormCommands()
            _key = _iormcmd["clientkeys"]

            _iormdata["cell"] = {}
            _iormdata[_key] = []
            _iormdata["ErrorCode"] = "0"
            _iormdata["Status"] = "Pass"
            _cluname = self.mGetEbox().mGetClusters().mGetCluster().mGetCluName()

            _cells = self.mGetCells()

            # Execute commands on each cell
            _cmd1 = f"cellcli -e list key ATTRIBUTES NAME, KEY, TYPE | grep {_cluname}"

            def _mExecute(aCell, aList):
                _cell = aCell
                _list = aList

                _iormdata["cell"][_cell] = {}
                _i1, _o1, _e1 = self.mExecCommandOnCell(_cell, _options, _cmd1)
                if str(_e1) == "0":
                    self.mParseClientKeysOutput(_cell, _iormdata, _o1)
                    _iormdata["cell"][_cell]["List Key Status"] = "Pass"
                    _iormdata["cell"][_cell]["List Key ErrorCode"] = str(_e1)
                    _iormdata["cell"][_cell]["log"] = gResError[str(_e1)]
                    _iormdata["cell"][_cell][_key] = _iormdata[_key]
                else:
                    _iormdata["cell"][_cell]["List Key Status"] = "Fail"
                    _iormdata["cell"][_cell]["List Key ErrorCode"] = str(_e1)
                    _iormdata["cell"][_cell]["log"] = gResError[str(_e1)]

                _list.append([_cell, _iormdata["cell"][_cell]])

            _plist = ProcessManager()
            _list = _plist.mGetManager().list()
            
            # Parallelize execution on cells
            for _cell in _cells:
                _p = ProcessStructure(_mExecute, [_cell, _list], _cell)
                _p.mSetMaxExecutionTime(MULTIPROCESSING_MAXEXECUTION_TIMEOUT)
                _p.mSetJoinTimeout(60)
                _p.mSetLogTimeoutFx(ebLogWarn)
                _plist.mStartAppend(_p)
                ebLogTrace('%s : _mExecute started for %s ' %(_p.name, _cell))
            
            _plist.mJoinProcess()
            ebLogTrace('All processes completed their call to _mExecute.')

            for _entry in _list:
                _iormdata["cell"][_entry[0]] = _entry[1]
                if _entry[1][_key] not in _iormdata[_key]:
                    _iormdata[_key].append(_entry[1][_key])

            for _cell in _cells:
                if _iormdata["cell"][_cell]["List Key Status"] == "Fail":
                    _iormdata["Status"]= "Fail"
                    _iormdata["ErrorCode"] = _iormdata["cell"][_cell]["List Key ErrorCode"]

            if _iormdata["ErrorCode"] != "0":
                return self.mRecordError(_iormdata["ErrorCode"])
            else:
                return 0


        # 
        # Parses the output of the following command, and stores it in
        # aIormdata JSON.
        # 
        # cellcli -e list key ATTRIBUTES NAME, KEY, TYPE
        #
        def mParseClientKeysOutput(self, aCell, aIormdata, aOutput):
            _cell = aCell
            _iormdata = aIormdata
            _output = aOutput
            _l = Lock()

            _iormcmd = self.mGetIormCommands()
            _key = _iormcmd["clientkeys"]

            for entry in _output:

                arr = entry.replace("\n", "").split("\t")

                key_details = {}
                key_details["client name"] = arr[1].strip()
                key_details["client key"] = arr[2].strip()
                key_details["client type"] = arr[3].strip()

                # Acquire a lock before accessing '_iormdata["ClientKeys"]'
                # shared accross multi-processes
                _l.acquire()

                if key_details not in _iormdata[_key]:
                    # Form a consolidated list of unique key entries.
                    _iormdata[_key].append(key_details)

                # Release the lock on completion.
                _l.release()

        # Main worker method for User config.
        def mUserConfig(self, aOptions):

            _options = aOptions
            _rc = 0

            _usrdata = self.mGetData()
            _usrdata["Status"] = "Pass"
            _eBox = self.mGetEbox()

            # Dump the JSON object
            def _mUpdateRequestData(aDataD):
                _data_d = aDataD
                _reqobj = _eBox.mGetRequestObj()
                if _reqobj is not None:
                    _reqobj.mSetData(json.dumps(_data_d, sort_keys = True))
                    _db = ebGetDefaultDB()
                    _db.mUpdateRequest(_reqobj)
                elif aOptions.jsonmode:
                    ebLogJson(json.dumps(_data_d, indent = 4, sort_keys = True))

            if (_options.user_operation is None):
                ebLogInfo("Invalid invocation or unsupported userconfig option")
                _usrdata["Log"] = "Invalid invocation or unsupported userconfig option"
                _usrdata["Status"] = "Fail"
                _mUpdateRequestData(_usrdata)
                return self.mRecordError("826")

            # Invoke right worker method
            if (_options.user_operation == "create_user"):
                ebLogInfo("Running userconfig step: Create user")
                _usrdata["Command"] = "create user"
                _rc = self.mCreateUser(_options)

            elif (_options.user_operation == "alter_user"):
                ebLogInfo("Running userconfig step: Alter user")
                _usrdata["Command"] = "alter user"
                _rc = self.mAlterUser(_options)

            elif (_options.user_operation == "grant_role"):
                ebLogInfo("Running userconfig step: Grant role")
                _usrdata["Command"] = "grant role"
                _rc = self.mGrantRole(_options)

            elif (_options.user_operation == "list_user"):
                ebLogInfo("Running userconfig step: list user")
                _usrdata["Command"] = "list user"
                _rc = self.mListUser(_options)           
 
            elif (_options.user_operation == "delete_user"):
                ebLogInfo("Running userconfig step: delete user")
                _usrdata["Command"] = "drop user"
                _rc = self.mDeleteUser(_options)           

            elif (_options.user_operation == "delete_role"):
                ebLogInfo("Running userconfig step: delete role")
                _usrdata["Command"] = "drop role"
                _rc = self.mDeleteRole(_options) 
          
            elif (_options.user_operation == "create_role"):
                ebLogInfo("Running userconfig step: Create role")
                _usrdata["Command"] = "create role"
                _rc = self.mCreateRole(_options)
          
            elif (_options.user_operation == "grant_privilege"):
                ebLogInfo("Running userconfig step: Grant privilege")
                _usrdata["Command"] = "grant privilege"
                _rc = self.mGrantPrivilege(_options)

          
            elif (_options.user_operation == "setup_user"):
                ebLogInfo("Running userconfig step: Setup user")
                _usrdata["Command"] = "setup user"
                self.mSetupUser(_options)

            else:
                ebLogInfo("Running userconfig step: Unsupported")
                _rc = self.mRecordError("826")
                _usrdata["Log"] = "userconfig Step: Unsupported"
                _usrdata["Status"] = "Fail"

            ebLogTrace("User config data: %s" % _usrdata)
            _mUpdateRequestData(_usrdata)
            return _rc
        
        # Method to create user-password for a user.
        def mCreateUser(self, aOptions):

            _options = aOptions
            _objective = None

            _usrdata = self.mGetData()
            _usrdata["Status"] = "Pass"
            _usrdata["ErrorCode"] = "0"

            _cells    = self.mGetCells()

            # Parse the input JSON and read the objective
            _inputjson = _options.jsonconf 
            if not _inputjson:
                return self.mRecordError("808")
            elif 'user' not in list(_inputjson.keys()):
                return self.mRecordError("822")
            elif 'password' not in list(_inputjson.keys()):
                return self.mRecordError("823")

            _uname = _inputjson['user']
            _pswd = b64decode(_inputjson['password']).decode('utf8')

            _usrdata["cell"] = {}

            # Execute commands on each cell
            _cmd = "cellcli -e \'create user \"" + _uname + "\" password=\"" + _pswd + "\"\'"
            _cmdForLog = "cellcli -e \'create user \"" + _uname + "\" password=\"****\"\'"
            
            def _mExecute(aCell, aList):
                _cell = aCell
                _list = aList

                _usrdata["cell"][_cell] = {}
                _i, _o, _e = self.mExecCommandOnCell(_cell, _options, _cmd)
                _usrdata["cell"][_cell]["errorCode"] = str(_e)
                _usrdata["cell"][_cell]["log"] = str(_o)

                _list.append([_cell, _usrdata["cell"][_cell]])

            _plist = ProcessManager()
            _list = _plist.mGetManager().list()
            
            # Parallelize execution on cells
            for _cell in _cells:
                _p = ProcessStructure(_mExecute, [_cell, _list], _cell)
                _p.mSetMaxExecutionTime(MULTIPROCESSING_MAXEXECUTION_TIMEOUT)
                _p.mSetJoinTimeout(60)
                _p.mSetLogTimeoutFx(ebLogWarn)
                _plist.mStartAppend(_p)
                ebLogTrace('%s : _mExecute started for %s ' %(_p.name, _cell))
            
            _plist.mJoinProcess()
            ebLogTrace('All processes completed their call to _mExecute.')

            for _entry in _list:
                _usrdata["cell"][_entry[0]] = _entry[1]

            for _cell in _cells:
                if "CELL-" in _usrdata["cell"][_cell]["log"]:
                    ebLogWarn("Create user failed on %s" %(_cell))
                    _usrdata["Status"] = "Fail"
                    _usrdata["ErrorCode"] = "802"

            if _usrdata["Status"] == "Fail":
                ebLogWarn("Create user command failed")
                _usrdata["Log"] = "Create user command failed"
            else:
                ebLogInfo("Create user command succeeded")
                _usrdata["Log"] = "Create user command succeeded"

            if _usrdata["ErrorCode"] != "0":
                return self.mRecordError(_usrdata["ErrorCode"])
            else:
                return 0

        # end

        # Method to create role for a user.
        def mCreateRole(self, aOptions):

            _options = aOptions
            _objective = None

            _usrdata = self.mGetData()
            _usrdata["Status"] = "Pass"
            _usrdata["ErrorCode"] = "0"

            _cells    = self.mGetCells()

            # Parse the input JSON and read the objective
            _inputjson = _options.jsonconf 
            if not _inputjson:
                return self.mRecordError("808")
            elif 'role' not in list(_inputjson.keys()):
                return self.mRecordError("824")

            _uname = _inputjson['role']

            _usrdata["cell"] = {}

            # Execute commands on each cell
            _cmd = "cellcli -e create role " + _uname
            _cmdForLog = "cellcli -e create role " + _uname 
            
            def _mExecute(aCell, aList):
                _cell = aCell
                _list = aList

                _usrdata["cell"][_cell] = {}
                _i, _o, _e = self.mExecCommandOnCell(_cell, _options, _cmd)
                _usrdata["cell"][_cell]["errorCode"] = str(_e)
                _usrdata["cell"][_cell]["log"] = str(_o)

                _list.append([_cell, _usrdata["cell"][_cell]])

            _plist = ProcessManager()
            _list = _plist.mGetManager().list()
            
            # Parallelize execution on cells
            for _cell in _cells:
                _p = ProcessStructure(_mExecute, [_cell, _list], _cell)
                _p.mSetMaxExecutionTime(MULTIPROCESSING_MAXEXECUTION_TIMEOUT)
                _p.mSetJoinTimeout(60)
                _p.mSetLogTimeoutFx(ebLogWarn)
                _plist.mStartAppend(_p)
                ebLogTrace('%s : _mExecute started for %s ' %(_p.name, _cell))
            
            _plist.mJoinProcess()
            ebLogTrace('All processes completed their call to _mExecute.')

            for _entry in _list:
                _usrdata["cell"][_entry[0]] = _entry[1]

            for _cell in _cells:
                if "CELL-" in _usrdata["cell"][_cell]["log"]:
                    ebLogWarn("Create role failed on %s" %(_cell))
                    _usrdata["Status"] = "Fail"
                    _usrdata["ErrorCode"] = "802"

            if _usrdata["Status"] == "Fail":
                ebLogWarn("Create role command failed")
                _usrdata["Log"] = "Create role command failed"
            else:
                ebLogInfo("Create role command succeeded")
                _usrdata["Log"] = "Create role command succeeded"

            if _usrdata["ErrorCode"] != "0":
                return self.mRecordError(_usrdata["ErrorCode"])
            else:
                return 0

            # end

        # Method to grant role to a user
        def mGrantPrivilege(self, aOptions):

            _options = aOptions
            _objective = None

            _usrdata = self.mGetData()
            _usrdata["Status"] = "Pass"
            _usrdata["ErrorCode"] = "0"

            _cells    = self.mGetCells()

            # Parse the input JSON and read the objective
            _inputjson = _options.jsonconf 
            if not _inputjson:
                return self.mRecordError("808")
            elif 'role' not in list(_inputjson.keys()):
                return self.mRecordError("824")

            _role = _inputjson['role']
            _object = 'ALL OBJECTS'
            _attributes = ''

            if 'attributes' in list(_inputjson.keys()) and _inputjson['attributes'].strip():
                _attributes = " ATTRIBUTES " + _inputjson['attributes']

            if 'object' in list(_inputjson.keys()) and _inputjson['object'].strip():
                _object = _inputjson['object']

            _usrdata["cell"] = {}

            # Execute commands on each cell
            _cmd = "cellcli -e grant privilege list ON " + _object + " " + _attributes + " TO ROLE " + _role

            def _mExecute(aCell, aList):
                _cell = aCell
                _list = aList

                _usrdata["cell"][_cell] = {}
                _i, _o, _e = self.mExecCommandOnCell(_cell, _options, _cmd)
                _usrdata["cell"][_cell]["errorCode"] = str(_e)
                _usrdata["cell"][_cell]["log"] = str(_o)

                _list.append([_cell, _usrdata["cell"][_cell]])

            _plist = ProcessManager()
            _list = _plist.mGetManager().list()
            
            # Parallelize execution on cells
            for _cell in _cells:
                _p = ProcessStructure(_mExecute, [_cell, _list], _cell)
                _p.mSetMaxExecutionTime(MULTIPROCESSING_MAXEXECUTION_TIMEOUT)
                _p.mSetJoinTimeout(60)
                _p.mSetLogTimeoutFx(ebLogWarn)
                _plist.mStartAppend(_p)
                ebLogTrace('%s : _mExecute started for %s ' %(_p.name, _cell))
            
            _plist.mJoinProcess()
            ebLogTrace('All processes completed their call to _mExecute.')

            for _entry in _list:
                _usrdata["cell"][_entry[0]] = _entry[1]

            for _cell in _cells:
                if "CELL-" in _usrdata["cell"][_cell]["log"]:
                    ebLogWarn("Grant privilege command failed on %s" %(_cell))
                    _usrdata["Status"] = "Fail"

            if _usrdata["Status"] == "Fail":
                ebLogWarn("Grant privilege command failed")
                _usrdata["Log"] = "Grant privilege command failed"
            else:
                ebLogInfo("Grant privilege succeeded")
                _usrdata["Log"] = "Grant privilege command succeeded"

        # end
        
        # Method to Setup user name, password, role name and role attributes.
        def mSetupUser(self, aOptions):    

            _options = aOptions
            _objective = None

            _usrdata = self.mGetData()
            _usrdata["Status"] = "Pass"
            _usrdata["ErrorCode"] = "0"

            _cells    = self.mGetCells()

            # Parse the input JSON and read the objective
            _inputjson = _options.jsonconf 
            if not _inputjson:
                return self.mRecordError("808")
            elif 'user' not in list(_inputjson.keys()):
                return self.mRecordError("822")
            elif 'password' not in list(_inputjson.keys()):
                return self.mRecordError("823")
            elif 'role' not in list(_inputjson.keys()):
                return self.mRecordError("824")
            
            ebLogInfo("Running userconfig step: Create user")
            self.mCreateUser(_options)
            ebLogInfo("Running userconfig step: Create role")
            self.mCreateRole(_options)
            ebLogInfo("Running userconfig step: Grant Privilege")
            self.mGrantPrivilege(_options)
            ebLogInfo("Running userconfig step: Grant Role")
            self.mGrantRole(_options)

            
        # end

        # Method to alter user-password.
        def mAlterUser(self, aOptions):    

            _options = aOptions
            _objective = None

            _usrdata = self.mGetData()
            _usrdata["Status"] = "Pass"
            _usrdata["ErrorCode"] = "0"

            _cells    = self.mGetCells()

            # Parse the input JSON and read the objective
            _inputjson = _options.jsonconf 
            if not _inputjson:
                return self.mRecordError("808")
            elif 'user' not in list(_inputjson.keys()):
                return self.mRecordError("822")
            elif 'password' not in list(_inputjson.keys()):
                return self.mRecordError("823")

            _uname = _inputjson['user']
            _pswd = b64decode(_inputjson['password']).decode('utf8')

            _usrdata["cell"] = {}

            # Execute commands on each cell
            _cmd = "cellcli -e \'alter user \"" + _uname + "\" password=\"" + _pswd + "\"\'"
            _cmdForLog = "cellcli -e \'alter user \"" + _uname + "\" password=\"****\"\'"
            
            def _mExecute(aCell, aList):
                _cell = aCell
                _list = aList

                _usrdata["cell"][_cell] = {}
                _i, _o, _e = self.mExecCommandOnCell(_cell, _options, _cmd)
                _usrdata["cell"][_cell]["errorCode"] = str(_e)
                _usrdata["cell"][_cell]["log"] = str(_o)
 
                _list.append([_cell, _usrdata["cell"][_cell]])

            _plist = ProcessManager()
            _list = _plist.mGetManager().list()
            
            # Parallelize execution on cells
            for _cell in _cells:
                _p = ProcessStructure(_mExecute, [_cell, _list], _cell)
                _p.mSetMaxExecutionTime(MULTIPROCESSING_MAXEXECUTION_TIMEOUT)
                _p.mSetJoinTimeout(60)
                _p.mSetLogTimeoutFx(ebLogWarn)
                _plist.mStartAppend(_p)
                ebLogTrace('%s : _mExecute started for %s ' %(_p.name, _cell))
            
            _plist.mJoinProcess()
            ebLogTrace('All processes completed their call to _mExecute.')

            for _entry in _list:
                _usrdata["cell"][_entry[0]] = _entry[1]

            for _cell in _cells:
                if "CELL-" in _usrdata["cell"][_cell]["log"]:
                    ebLogWarn("Alter user command failed on %s" %(_cell))
                    _usrdata["Status"] = "Fail"

            if _usrdata["Status"] == "Fail":
                ebLogWarn("Alter user command failed")
                _usrdata["Log"] = "Alter user command failed"
            else:
                ebLogInfo("Alter user command succeeded")
                _usrdata["Log"] = "Alter user command succeeded"

            # end

        # Method to grant role to a user
        def mGrantRole(self, aOptions):

            _options = aOptions
            _objective = None

            _usrdata = self.mGetData()
            _usrdata["Status"] = "Pass"
            _usrdata["ErrorCode"] = "0"

            _cells    = self.mGetCells()

            # Parse the input JSON and read the objective
            _inputjson = _options.jsonconf 
            if not _inputjson:
                return self.mRecordError("808")
            elif 'user' not in list(_inputjson.keys()):
                return self.mRecordError("822")
            elif 'role' not in list(_inputjson.keys()):
                return self.mRecordError("824")

            _uname = _inputjson['user']
            _role = _inputjson['role']

            _usrdata["cell"] = {}

            # Execute commands on each cell
            _cmd = "cellcli -e \'grant role " + _role + " to user \"" + _uname + "\"\'"
            
            def _mExecute(aCell, aList):
                _cell = aCell
                _list = aList

                _usrdata["cell"][_cell] = {}
                _i, _o, _e = self.mExecCommandOnCell(_cell, _options, _cmd)
                _usrdata["cell"][_cell]["errorCode"] = str(_e)
                _usrdata["cell"][_cell]["log"] = str(_o)

                _list.append([_cell, _usrdata["cell"][_cell]])

            _plist = ProcessManager()
            _list = _plist.mGetManager().list()
            
            # Parallelize execution on cells
            for _cell in _cells:
                _p = ProcessStructure(_mExecute, [_cell, _list], _cell)
                _p.mSetMaxExecutionTime(MULTIPROCESSING_MAXEXECUTION_TIMEOUT)
                _p.mSetJoinTimeout(60)
                _p.mSetLogTimeoutFx(ebLogWarn)
                _plist.mStartAppend(_p)
                ebLogTrace('%s : _mExecute started for %s ' %(_p.name, _cell))
            
            _plist.mJoinProcess()
            ebLogTrace('All processes completed their call to _mExecute.')

            for _entry in _list:
                _usrdata["cell"][_entry[0]] = _entry[1]

            for _cell in _cells:
                if "CELL-" in _usrdata["cell"][_cell]["log"]:
                    ebLogWarn("Grant role command failed on %s" %(_cell))
                    _usrdata["Status"] = "Fail"
                    _usrdata["ErrorCode"] = "802"

            if _usrdata["Status"] == "Fail":
                ebLogWarn("Grant role command failed")
                _usrdata["Log"] = "Grant role command failed"
            else:
                ebLogInfo("Grant role succeeded")
                _usrdata["Log"] = "Grant role command succeeded"

            if _usrdata["ErrorCode"] != "0":
                return self.mRecordError(_usrdata["ErrorCode"])
            else:
                return 0

            # end

        # Method to list users
        def mListUser(self, aOptions):

            _options = aOptions
            _objective = None

            _usrdata = self.mGetData()
            _usrdata["Status"] = "Pass"
            _usrdata["ErrorCode"] = "0"
            _usrdata["Users"] = []

            _cells    = self.mGetCells()

            _usrdata["cell"] = {}

            # Execute commands on each cell
            _cmd = "cellcli -e list user"

            def _mExecute(aCell, aList):
                _cell = aCell
                _list = aList

                _usrdata["cell"][_cell] = {}
                _i, _o, _e = self.mExecCommandOnCell(_cell, _options, _cmd)
                _usrdata["cell"][_cell]["errorCode"] = str(_e)
                _usrdata["cell"][_cell]["log"] = gResError[str(_e)]
                _usrdata["cell"][_cell]["Users"] = self.mParseUsrOutput(_o)

                _list.append([_cell, _usrdata["cell"][_cell]])
        
            _plist = ProcessManager()
            _list = _plist.mGetManager().list()
            
            # Parallelize execution on cells
            for _cell in _cells:
                _p = ProcessStructure(_mExecute, [_cell, _list], _cell)
                _p.mSetMaxExecutionTime(MULTIPROCESSING_MAXEXECUTION_TIMEOUT)
                _p.mSetJoinTimeout(60)
                _p.mSetLogTimeoutFx(ebLogWarn)
                _plist.mStartAppend(_p)
                ebLogTrace('%s : _mExecute started for %s ' %(_p.name, _cell))
            
            _plist.mJoinProcess()
            ebLogTrace('All processes completed their call to _mExecute.')

            for _entry in _list:
                _usrdata["cell"][_entry[0]] = _entry[1]

            for _cell in _cells:
                if _usrdata["cell"][_cell]["errorCode"] != "0":
                    ebLogWarn("List user command failed on %s" %(_cell))
                    _usrdata["ErrorCode"] = "802"
                    _usrdata["Status"] = "Fail"
                else:
                    for _user in _usrdata["cell"][_cell]["Users"]:
                        if _user not in _usrdata["Users"]:
                            _usrdata["Users"].append(_user)

            if _usrdata["Status"] == "Fail":
                ebLogWarn("List user command failed")
                _usrdata["Log"] = "List user command failed"
            else:
                ebLogInfo("List user succeeded")
                _usrdata["Log"] = "List user command succeeded"

            if _usrdata["ErrorCode"] != "0":
                return self.mRecordError(_usrdata["ErrorCode"])
            else:
                return 0

        # end   

        # Method to delete a particular user from cell
        def mDeleteUser(self, aOptions):

            _options = aOptions
            _objective = None

            _usrdata = self.mGetData()
            _usrdata["Status"] = "Pass"
            _usrdata["ErrorCode"] = "0"

            _cells    = self.mGetCells()

            # Parse the input JSON and read the user name
            _inputjson = _options.jsonconf 
            if not _inputjson:
                return self.mRecordError("808")
            elif 'user' not in list(_inputjson.keys()):
                return self.mRecordError("822")

            _uname = _inputjson['user']

            _usrdata["cell"] = {}

            # Execute commands on each cell
            _cmd = "cellcli -e \'drop user \"" + _uname + "\"\'"
            
            def _mExecute(aCell, aList):
                _cell = aCell
                _list = aList

                _usrdata["cell"][_cell] = {}
                _i, _o, _e = self.mExecCommandOnCell(_cell, _options, _cmd)
                _usrdata["cell"][_cell]["errorCode"] = str(_e)
                _usrdata["cell"][_cell]["log"] = str(_o)
                
                _list.append([_cell, _usrdata["cell"][_cell]])

            _plist = ProcessManager()
            _list = _plist.mGetManager().list()
            
            # Parallelize execution on cells
            for _cell in _cells:
                _p = ProcessStructure(_mExecute, [_cell, _list], _cell)
                _p.mSetMaxExecutionTime(MULTIPROCESSING_MAXEXECUTION_TIMEOUT)
                _p.mSetJoinTimeout(60)
                _p.mSetLogTimeoutFx(ebLogWarn)
                _plist.mStartAppend(_p)
                ebLogTrace('%s : _mExecute started for %s ' %(_p.name, _cell))
            
            _plist.mJoinProcess()
            ebLogTrace('All processes completed their call to _mExecute.')

            for _entry in _list:
                _usrdata["cell"][_entry[0]] = _entry[1]

            for _cell in _cells:
                if "CELL-" in _usrdata["cell"][_cell]["log"]:
                    ebLogWarn("Delete user command failed on %s" %(_cell))
                    _usrdata["Status"] = "Fail"
                    _usrdata["ErrorCode"] = "802"

            if _usrdata["Status"] == "Fail":
                ebLogWarn("Delete user command failed")
                _usrdata["Log"] = "Delete user command failed"
            else:
                ebLogInfo("Delete user command succeeded")
                _usrdata["Log"] = "Delete user command succeeded"

            if _usrdata["ErrorCode"] != "0":
                return self.mRecordError(_usrdata["ErrorCode"])
            else:
                return 0

            # end

        # Method to delete a particular role from cell
        def mDeleteRole(self, aOptions):

            _options = aOptions
            _objective = None

            _usrdata = self.mGetData()
            _usrdata["Status"] = "Pass"
            _usrdata["ErrorCode"] = "0"

            _cells    = self.mGetCells()

            # Parse the input JSON and read the user name
            _inputjson = _options.jsonconf 
            if not _inputjson:
                return self.mRecordError("808")
            elif 'role' not in list(_inputjson.keys()):
                return self.mRecordError("824")

            _force = ''
            if 'force' in list(_inputjson.keys()) and _inputjson['force'] == "True":
                _force = "force"

            _rname = _inputjson['role']

            _usrdata["cell"] = {}

            # Execute commands on each cell
            _cmd = "cellcli -e \'drop role \"" + _rname + "\" " + _force + "\'"
            
            def _mExecute(aCell, aList):
                _cell = aCell
                _list = aList

                _usrdata["cell"][_cell] = {}
                _i, _o, _e = self.mExecCommandOnCell(_cell, _options, _cmd)
                _usrdata["cell"][_cell]["errorCode"] = str(_e)
                _usrdata["cell"][_cell]["log"] = str(_o)

                _list.append([_cell, _usrdata["cell"][_cell]])

            _plist = ProcessManager()
            _list = _plist.mGetManager().list()
            
            # Parallelize execution on cells
            for _cell in _cells:
                _p = ProcessStructure(_mExecute, [_cell, _list], _cell)
                _p.mSetMaxExecutionTime(MULTIPROCESSING_MAXEXECUTION_TIMEOUT)
                _p.mSetJoinTimeout(60)
                _p.mSetLogTimeoutFx(ebLogWarn)
                _plist.mStartAppend(_p)
                ebLogTrace('%s : _mExecute started for %s ' %(_p.name, _cell))
            
            _plist.mJoinProcess()
            ebLogTrace('All processes completed their call to _mExecute.')

            for _entry in _list:
                _usrdata["cell"][_entry[0]] = _entry[1]

            for _cell in _cells:
                if "CELL-" in _usrdata["cell"][_cell]["log"]:
                    ebLogWarn("Delete role command failed on %s" %(_cell))
                    _usrdata["Status"] = "Fail"
                    _usrdata["ErrorCode"] = "802"

            if _usrdata["Status"] == "Fail":
                ebLogWarn("Delete role command failed")
                _usrdata["Log"] = "Delete role command failed"
            else:
                ebLogInfo("Delete role command succeeded")
                _usrdata["Log"] = "Delete role command succeeded"

            if _usrdata["ErrorCode"] != "0":
                return self.mRecordError(_usrdata["ErrorCode"])
            else:
                return 0

            # end

        def mParseUsrOutput(self, aOut):

            _out = aOut
            _result = []

            _internal_users = self.__ebox.mCheckConfigOption("internal_cell_users")

            ebLogTrace("Internal cell users: %s" % _internal_users)
            for _line in _out:
                _line = _line.replace("\t", "")
                _line = _line.replace("\n", "")
                _line = _line.replace(' ', '')

                # Now that alter user-password command is supported from ecracli,
                # exposing internal cell users can become a security concern.
                # Thus internal cell users are not reported as part of the list.
                if _line not in _internal_users:
                    _result.append(_line) 

            ebLogTrace("List of cell users: %s" % _result)

            return _result


# End of file
