"""
 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    OVM - Diskgroup/Griddisk Management
          1. Create
          2. Resize
          3. Rebalance
          4. Query Info
          5. Delete (TBD)

FUNCTION:
    Module to provide all the diskgroup management APIs

NOTE:
    None

History:
    nelango   11/20/25 - Bug 38483116 - Skip celldisk freespace check if freespace available in griddisks
    shapatna  09/29/25 - Bug 38449773 - FIX FOR ISSUES WITH REBALANCE PERCENTAGE PROGRESS UPDATE IN EXACLOUD DB
    gparada   08/15/25 - 38254024 Reshape - Dynamic Storage for data reco sparse 
    rajsag    06/04/25 - ER 37542345 - SUPPORT ADDITIONAL RESPONSE FIELDS IN EXACLOUD STATUS RESPONSE FOR STORAGE(ASM) RESHAPE STEPS
    bhpati    04/09/25 - Bug 37514334 GRIDDISK SIZE PRECHECK CALCULATION IS NOT ACCURATE
    gparada   05/08/24 - 37873380 Skip mEnsureDgsRebalanced for ADD_CELL
    pbellary  11/14/24 - 37284375 - DISABLE SPARSE ON ASM CLUSTER FAILS "'NONETYPE' OBJECT IS NOT SUBSCRIPTABLE"
    rajsag    10/29/24 - enh 37012632 - exacloud - allow cpu reshape wf during storage reshape
    aararora  10/10/24 - ER 36253480: Return ASM rebalance status during rebalance step
    prsshukl  10/15/24 - 37164970 - SCALE VM CLUSTER EXADATA STORAGE: INVALID LITERAL FOR INT() WITH BASE 10
    dekuckre  07/17/24 - 35408982 - Add quorum to SPRC diskgroup
    aararora  05/31/24 - 35715255 - Add precheck before doing the alter of the griddisk during reshape
    rajsag    03/05/24 - 36218516 - issues with remove sparse diskgroup workflow  
    rajsag    11/23/23 - 35779694 - exacc gen2 add in precheck size must be same for griddisk and asmdisksize  
    rajsag    11/20/23 - 35945468 - storage pre_check should allow reshape if there is 9% free space for 5 or more cells 
    rajsag    11/10/23 - 35926833 - exacc-gen2 - elastic cell addition operation failed to shrink the dg. 
    rajsag    09/12/23 - 35793715 - exacc: sparse feature integration testing bugs. 
    rajsag    08/29/23 - 35736916: parallel scaling up 2 cell failed at attachstorage stage in attach-elastic-storage-wfd 
    rajsag    07/24/23 - enh 35614624 - sparse dg addition precheck api for exacloud 
    rajsag    07/17/23 - 35604323 - exacc: sparse create and drop api will fail if first dgid is not sparse id 
    dekuckre  07/13/23 - 35555686: Add retry logic for resize diskgroup.
    rajsag    07/13/23 - enh 35521221 - exacc: sparse clone feature update the payload for sparse partition drop and create api in exacloud 
    aararora  05/04/23 - 35320487: Resize grid disks on cells if it was not successful in last resize.
    scoral    02/27/23 - 35125011: Type issue in mCheckIfDgResizable.
    ashisban  04/07/22 - 34036190: ADD SPARSE DG FLOW ADDING INCORRECT DISKGROUPTYPE ENTRY IN XML
    rajsag    07/22/21 - 32974396: ora-15313 handler needs to wait for rebalance to complete before relocating voting file back
    dekuckre  02/19/21 - 32509175: Report status from v$ASM_OPERATION
    dekuckre  01/28/21 - 32255834: Correct the cell naming for correction.
    dekuckre  07/05/18 - 28285387: Add support to get diskgroup used space
    dekuckre  02/23/18 - 27588418: Specify 'virtualSize' to alter SPARSE 
                         grid disks.
    pverma    04/07/17 - Create file

Changelog:

   04/07/2017 - v1 changes:

       1) APIs for create, resize, rebalance, info for a diskgroup
"""
import copy
import collections.abc
import json
import math
import xml.etree.ElementTree as ET
import re
import time
import secrets


from exabox.utils.node import connect_to_host

try:
    from collections import deque
except ImportError:
    from collections.abc import deque

from exabox.core.Context import get_gcontext
from exabox.core.Error import gDiskgroupError, ebError, gReshapeError, \
    gElasticError, ExacloudRuntimeError
from exabox.core.Node import exaBoxNode

from .cludbaas import ebCluDbaas
from .clumisc import ebCluStorageReshapePrecheck

from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogDebug, ebLogVerbose, ebLogJson, ebLogTrace, ebLogWarn

from exabox.ovm.utils.clu_utils import ebCluUtils

# Function used to dump object as json
def universal_converter(obj):
    import collections.abc

    # Handle primitives
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj

    # Handle dicts
    if isinstance(obj, dict):
        return {str(k): universal_converter(v) for k, v in obj.items()}

    # Handle lists/tuples/sets
    if isinstance(obj, (list, tuple, set)):
        return [universal_converter(v) for v in obj]

    # Handle XML Elements
    if isinstance(obj, ET.Element):
        return {
            "__class__": "Element",
            "tag": obj.tag,
            "attrib": obj.attrib,
            "text": obj.text.strip() if obj.text else None,
            "children": [universal_converter(child) for child in obj]
        }

    # Handle objects with __dict__
    if hasattr(obj, "__dict__"):
        def clean_key(o, k):
            cls_name = o.__class__.__name__
            prefix = f"_{cls_name}__"
            if k.startswith(prefix):
                return k[len(prefix):]
            return k

        return {
            "__class__": obj.__class__.__name__,
            **{
                clean_key(obj, k): universal_converter(v)
                for k, v in vars(obj).items()
                if not callable(v)
            }
        }

    # Fallback
    return str(obj)

"""
class ebDiskgroupOpConstants shall store literals for use by operations/actions
class ebCluManageDiskgroup
"""
# TODO Refactor this class to comply with python standards of implementing 
# constants 
class ebDiskgroupOpConstants(object):
    def __init__(self,aOptions = None):
        # Constants for handling DGs
        self._all_dg = "ALL"

        self._data_dg_prefix = "DATA"
        self._reco_dg_prefix = "RECO"
        self._sparse_dg_prefix = "SPR"
        self._data_dg_rawname = "datadg"
        self._reco_dg_rawname = "recodg"
        self._sparse_dg_rawname = "sparsedg"
        self._catalog_dg_rawname = "catalogdg"
        self._delta_dg_rawname = "deltadg"
        self._data_dg_type_str = "data"
        self._reco_dg_type_str = "reco"
        self._sparse_dg_type_str = "sparse"
        self._catalog_dg_type_str = "catalog"
        self._delta_dg_type_str = "delta"
        self._dbfs_dg_type_str = "dbfs"

        # Input parameters of DBAASAPI JSON payload
        self._dbaasapi_object_key = "object"
        self._dbaasapi_object_value = "db"
        self._operation_key = "operation"
        self._operation_value = "diskgroup"
        self._action_key = "action"
        self._failgroup_list = "failgroup_list"
        
        self._dbname_key = "dbname"
        self._dbname_value = "grid"
        
        self._params_key = "params"
        self._param_infofile_key = "infofile"
        
        self._outfile_key = "outputfile"
        self._flags_key = "FLAGS"
        self._props_key = "props"
        
        self._propkey_storage = "dg_storage_props"
        self._propkey_failgroup = "failgroups"
        self._propkey_rebstat = "rebalance_status"
        self._supported_dg_properties = [self._propkey_storage, self._propkey_failgroup,\
                                          self._propkey_rebstat]
        
        self._diskgroupname_key = "diskgroup"
        self._diskgrouptype_key = "diskgroup_type"
        self._newsizeMB_key = "new_size"
        self._newsizeGB_key = "new_sizeGB"
        self._rebalancepower_key = "rebalance_power"
        self._optype_key = "opType"

        self._diskgroup_ratios_key = "storage_distribution"
        self._disk_backup_key = "disk_backup_enabled"
        self._total_storagegb_key = "total_storagegb"
        self._force_drop_key = "force_drop"
        self._shrink_key = "shrink"
        self._redundancy_factor = "redundancy_factor"
        
        self._storprop_totalMb = "total_mb"
        self._storprop_usedMb = "used_mb"
        self._storprop_osMb =   "os_mb"
        
        self._fgrpprop_celldisks = "celldisks"
        self._fgrpprop_numdisks = "num_disks"
        
        self._rebstatprop_diskgroup = "diskgroup"
        self._rebstatprop_operation = "operation"
        self._rebstatprop_status = "status"
        
        self._celldisk_type = "cd_type"
        
        self._slice_suffix = "slice"
        if aOptions is not None and aOptions.jsonconf is not None and 'virtual_size_ratio' in list(aOptions.jsonconf.keys()):
            self._sparse_vsize_factor = int(aOptions.jsonconf["virtual_size_ratio"])
        else:
            self._sparse_vsize_factor = 10

        # Constant string for comparision
        self._alter_disk_failure_msg = "alter failed for reason"

    def mGetSparseVsizeFactor(self):
        return self._sparse_vsize_factor

# end of ebDiskgroupOpConstants            

"""
class ebCluManageDiskgroup implements diskgroup management functionalities:
(1) Create diskgroup:
    (a) SPARSE Diskgroup - Involves resizing of DATA/RECO DGs, resizing of
                           underlying griddiks, creation of griddisks for 
                           sparse DG and then creation of sparse DG
    (b) DATA Diskgroup   - NOT Supported yet
(2) Resize Diskgroup
(3) Fetch Info of a diskgroup
(4) Rebalance a diskgroup
                           
"""
class ebCluManageDiskgroup(object):

    def __init__(self, aExaBoxCluCtrl, aOptions):

        self.__config = get_gcontext().mGetConfigOptions()
        self.__basepath = get_gcontext().mGetBasePath()
        self.__clusterpath = None
        self.__xmlpath = aOptions.configpath
        self.__ebox = aExaBoxCluCtrl
        self.__domUs = []
        self.__jobid = None
        self.__logfile = None
        self.__rollback_flag = False
        self.__options = aOptions
        self.__shrink_existing_dgs = True

        self.__clusterpath = self.__ebox.mGetClusterPath()
        self.__ddpair = self.__ebox.mReturnDom0DomUPair()

        self.__verbose = self.__ebox.mGetVerbose()
        
        for _, _dU in self.__ddpair:
            self.__domUs.append(_dU)

        # Object to store results
        self.__diskgroupData = {}

        # Stack to store rollback commands
        self._rollback_stack = deque()

        # Object to store output JSON for intermediate dbaasapi diskgroup info calls
        self._curOutJson = {}
        # Reference to hold reference of DomU on which last command was dispatched
        self._lastDomUused = None
        
        # Initialize for DBaaS API calls
        self.__dbaasobj = ebCluDbaas(self.__ebox, aOptions)
        
        # Initialize the constants object
        self._constantsObj = ebDiskgroupOpConstants(aOptions)

        self.__resizedataoncells = False
        self.__resizerecooncells = False
        self.__resizesprsoncells = False
        self.__resizeretrygriddiskcount = {}
        self.__currentSizeRetryMB = {}
        self._dict_groups_percent_avg = {}
        self._max_overall_percent = 0

    def mGetEbox(self):
        return self.__ebox

    def mGetDomUs(self):
        return self.__domUs

    def mSetGridDiskCountRetryResize(self, aCount, aDgName):
        self.__resizeretrygriddiskcount[aDgName] = aCount

    def mSetResizeDataOnCells(self, aResize=False):
        self.__resizedataoncells = aResize

    def mSetResizeRecoOnCells(self, aResize=False):
        self.__resizerecooncells = aResize

    def mSetResizeSparseOnCells(self, aResize=False):
        self.__resizesprsoncells = aResize

    def mSetCurrentRetrySizeTotalMB(self, aSize, aDgName):
        self.__currentSizeRetryMB[aDgName] = aSize

    def mGetGridDiskCountRetryResize(self, aDgName):
        return self.__resizeretrygriddiskcount.get(aDgName)

    def mGetResizeDataOnCells(self):
        return self.__resizedataoncells

    def mGetResizeRecoOnCells(self):
        return self.__resizerecooncells

    def mGetResizeSparseOnCells(self):
        return self.__resizesprsoncells

    def mGetCurrentRetrySizeTotalMB(self, aDgName):
        return self.__currentSizeRetryMB.get(aDgName)

    def mSetDomUs(self, aDomUs):
        self.__domUs = aDomUs

    def mGetDiskGroupOperationData(self):
        return self.__diskgroupData

    def mSetDiskGroupOperationData(self, aDiskgroupData):
        self.__diskgroupData = aDiskgroupData

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
        
    def mGetOutJson(self):
        return self._outJson
    
    def mSetOutJson(self, aOutJson):
        self._outJson = aOutJson
        
    def mGetLastDomUused(self):
        return self._lastDomUused
    
    def mSetLastDomUused(self, aDomU):
        self._lastDomUused = aDomU
        
    def mGetConstantsObj(self):
        return self._constantsObj

    def mGetRollbackStack(self):
        return self._rollback_stack

    def mGetAoptions(self):
        return self.__options
    
    """
    Method mClusterManageDiskGroup is general entry point of any diskgroup
    related operation.
    
    Required Params: (1) Dictionary containing properties related to the
                         specific operation
    """
    def mClusterManageDiskGroup(self, aOptions):

        ebLogInfo("*** ebCluManageDiskgroup:mClusterManageDiskGroup >>>")
        _options = aOptions
        _rc = 0

        _diskgroupData = self.mGetDiskGroupOperationData()
        _diskgroupData['Status'] = "Pass"
        _eBoxCluCtrl = self.mGetEbox()
        _dbaasObj = self.mGetDbaasObj()

        if (_options.diskgroupOp is None):
            ebLogInfo("Invalid invocation or unsupported DiskGroup LCM option")
            _rc = self.mRecordError(gDiskgroupError['DiskGroupLCMInvocationError'], "***Invalid invocation or unsupported DiskGroup LCM option")
            _diskgroupData["Log"] = "Invalid invocation or unsupported DiskGroup LCM option"
            _diskgroupData["Status"] = "Fail"
            _dbaasObj._mUpdateRequestData(_options, _diskgroupData, _eBoxCluCtrl)
            return _rc

        # Invoke right worker method
        if (_options.diskgroupOp == "create"):
            ebLogInfo("Running DiskGroup LCM Step: Create Diskgroup")
            _diskgroupData["Command"] = "dg_create"
            _rc = self.mClusterDgrpCreate(_options)
            if _rc:
                ebLogError("*** Create of Sparse DG failed")
                _diskgroupData['Status'] = "Fail"
                return _rc
        elif (_options.diskgroupOp == "update_add_sparse"):
            ebLogInfo("Running DiskGroup LCM Step: Update Adding Sparse Diskgroup")
            _diskgroupData["Command"] = "dg_update_add_sparse"
            _rc = self.mClusterDgrpCreate(_options, False)
        elif (_options.diskgroupOp == "resize"):
            ebLogInfo("Running DiskGroup LCM Step: Resize Diskgroup")
            _diskgroupData["Command"] = "dg_resize"
            _rc = self.mClusterDgrpResize(_options)
        elif (_options.diskgroupOp == "rebalance"):
            ebLogInfo("Running DiskGroup LCM Step: Rebalance Diskgroup")
            _diskgroupData["Command"] = "dg_rebalance"
            _rc = self.mClusterDgrpRebalance(_options)
        elif (_options.diskgroupOp == "info"):
            ebLogInfo("Running DiskGroup LCM Step: Fetching info of Diskgroup")
            _diskgroupData["Command"] = "dg_info"
            _rc = self.mClusterDgrpInfo(_options)
        elif (_options.diskgroupOp == "drop"):
            ebLogInfo("Running DiskGroup LCM Step: Drop Diskgroup")
            _diskgroupData["Command"] = "dg_drop"
            _rc = self.mClusterDgrpDrop(_options)
            if _rc:
                ebLogError("*** Drop of Sparse DG  failed")
                _diskgroupData['Status'] = "Fail"
                return _rc
        elif (_options.diskgroupOp == "precheck"):
            ebLogInfo("Running DiskGroup LCM Step: Precheck Diskgroup")
            _diskgroupData["Command"] = "dg_precheck"
            _diskPrecheckOnly = True
            _rc = self.mClusterDgrpCreate(_options, True, _diskPrecheckOnly)
            if _rc:
                ebLogError("*** Validation of Sparse DG creation precheck failed")
                _diskgroupData["validatePrecheckSparseCreation"] = "Failed"
                _diskgroupData['Status'] = "Fail"
                return _rc
            else:
                ebLogInfo("*** Validation of Sparse DG creation success")
                _diskgroupData["validatePrecheckSparseCreation"] = "Success"
        else:
            ebLogInfo("Running DiskGroup LCM step: Unsupported")
            _rc = self.mRecordError(gDiskgroupError['InvalidOp'], "DiskGroup LCM Step:\
            %s is Unsupported" % (_options.diskgroupOp))

        _dbaasObj._mUpdateRequestData(_options, _diskgroupData, _eBoxCluCtrl)
        
        ebLogInfo("*** ebCluManageDiskgroup:mClusterManageDiskGroup <<<")

        return _rc
    # end mSparseclone

    # Method to get the diskgroup allocation percentages whether the ratios 
    # are provided or not
    def mCalculateNewDgSizes(self, 
        aOptions, 
        aDiskgroupData, 
        aCurrentDgSizesDict, 
        aSparseCreate=False):

        _thisFn = "ebCluManageDiskgroup:mCalculateNewDgSizes"

        ebLogInfo(f"*** {_thisFn} >>>")

        _options = aOptions
        _diskgroupData = aDiskgroupData
        _cur_dg_sizes = aCurrentDgSizesDict

        _constantsObj = self.mGetConstantsObj()
        # Decide the new ratios on the basis of sparse dg creation or not
        _sparsedg_create = aSparseCreate
        _shrink_existing_dgs = self.__shrink_existing_dgs
        _diskgroupData[_constantsObj._shrink_key] = _shrink_existing_dgs

        _inparams = {}

        ebLogInfo(f"** {_thisFn} - Fetching and validation input args")
        _rc = self.mClusterParseInput(_options, _inparams, _diskgroupData)
        if _rc:
            ebLogError(f"** {_thisFn} - Could not validate input args")
            return _rc

        _datadg_cur_size = _cur_dg_sizes[_constantsObj._data_dg_rawname]
        _recodg_cur_size = _cur_dg_sizes[_constantsObj._reco_dg_rawname]
        _redundancy_factor = _cur_dg_sizes[_constantsObj._redundancy_factor]    

        _disk_backup_enabled = None
        if (_constantsObj._disk_backup_key) in _inparams:
            _disk_backup_enabled = _inparams[_constantsObj._disk_backup_key]   
        elif not _constantsObj._disk_backup_key in _inparams:
            ebLogInfo(f"** {_thisFn} - Disk backup enabled value is not " +
                        "given. Determining the value from the current " + 
                        "diskgroup sizes")
            if _datadg_cur_size > _recodg_cur_size:
                _disk_backup_enabled = False
            else:
                _disk_backup_enabled = True
        ebLogInfo(f"** {_thisFn} - Disk backup enabled is {_disk_backup_enabled}")


        _ratio_distribution_string = "D:R"
        if _sparsedg_create:
            _ratio_distribution_string = "D:R:S"
        
        _new_dg_ratio = None
        
        # _diskgroup_ratios_key is "storage_distribution" in payload
        if (_constantsObj._diskgroup_ratios_key) in _inparams:
            _new_dg_ratio = _inparams[_constantsObj._diskgroup_ratios_key]
        # If we are creating sparse and storage distribution is not given
        # it should fail
        elif not _constantsObj._diskgroup_ratios_key in _inparams:
            ebLogInfo(f"** {_thisFn} - Storage distribution ratio is not " +
                "given. Calculating from disk_backup_enabled and " +
                "create_sparse values")
            if _sparsedg_create:
                if _disk_backup_enabled:
                    _new_dg_ratio = "35:50:15"
                else:
                    _new_dg_ratio = "60:20:20"

            else:
                if _disk_backup_enabled:
                    _new_dg_ratio = "40:60"
                else:
                    _new_dg_ratio = "80:20"
        
        ebLogInfo(f"** {_thisFn} - New Storage distribution " + 
            f"will be {_new_dg_ratio}")

        # Calculate the current D:R ratio if we are running update add sparse
        # This is needed because in a certain ECS label, a bug was introduced 
        # where sparse was not getting created, even though space was alloted
        # for it. Hence calculate the ratio to confirm that provided backup
        # disk enabled, sparse create and shrink dg values
        # provided are correct or not

        _curr_dg_ratio = _new_dg_ratio
        # We don't need to calculate existing dg ratio if we are given
        # total exadata storage
        if (not _shrink_existing_dgs) and \
            (not _constantsObj._total_storagegb_key in _inparams):
            _rc = self.mCalcCurrentDgRatio(
                    _diskgroupData, _datadg_cur_size, _recodg_cur_size)
            if _rc == 1:
                return _rc
            _curr_dg_ratio = _diskgroupData["curr_dg_ratio"]

        _total_dg_sizes = 0
        if (_constantsObj._total_storagegb_key) in _inparams:
            _total_dg_sizes = \
                _inparams[_constantsObj._total_storagegb_key] * _redundancy_factor
        # If we are creating sparse and storage distribution is not given, 
        # then it should fail
        elif (not _constantsObj._total_storagegb_key in _inparams):
            ebLogInfo(f"** {_thisFn} - Total storage gb value is not provided."+
                " Calculating from current dg sizes")
            _rc = self.mCalcTotalStorageForUpdate(
                    _diskgroupData, _cur_dg_sizes, _curr_dg_ratio)
            _total_dg_sizes = \
                _diskgroupData["_total_storage_size"] * _redundancy_factor

        # Given total size is in GB, convert it to MB
        _total_dg_sizes = (_total_dg_sizes * 1024)

        # Validate whether new ratio given is in correct format
        _rc = self.mValidateNewDgRatio(
                _diskgroupData, _new_dg_ratio, _sparsedg_create)
        if _rc == 1:
            return _rc

        _ratio_split = _diskgroupData["ratio_split"]
        #Calculate ratio sum to get percentages of each dg
        _ratio_sum = 0.0
        for dg_ratio in _ratio_split:
            # We'll get the ratio numbers as string. Convert them to float
            dg_ratio = float(dg_ratio)
            _ratio_sum = _ratio_sum + dg_ratio

        _datadg_new_pct = round( (float(_ratio_split[0])*100)/_ratio_sum )
        _recodg_new_pct = round( (float(_ratio_split[1])*100)/_ratio_sum )
        _sparsedg_new_pct = 0.0

        # Rounding off can make sum of both data and reco pcts more than 100
        if not _sparsedg_create:
            _recodg_new_pct = (100 - _datadg_new_pct)
        
        else:
            _sparsedg_new_pct = (100 - _datadg_new_pct - _recodg_new_pct)
            _diskgroupData["sparsedg_new_pct"] = _sparsedg_new_pct

        if _datadg_new_pct < 10:
            ebLogError("Please provide ratio which allots data diskgroup " +
                "more than 10% distribution")
            return 1

        ebLogInfo(f"{_thisFn} - The new Data, Reco and Sparse diskgroup " +
            "percentages are %s, %s and %s" 
            % (_datadg_new_pct, _recodg_new_pct, _sparsedg_new_pct))

        _diskgroupData["datadg_new_pct"] = _datadg_new_pct
        _diskgroupData["recodg_new_pct"] = _recodg_new_pct
        _datadg_new_size = (_datadg_new_pct*_total_dg_sizes)/100
        _recodg_new_size = (_recodg_new_pct*_total_dg_sizes)/100

        # If shrink is set to False, the new sizes for datadg and recodg 
        # are the same as current one
        if not _shrink_existing_dgs:
            _datadg_new_size = _datadg_cur_size
            _recodg_new_size = _recodg_cur_size
            
        _sparsedg_new_size = \
            _total_dg_sizes - (_datadg_new_size + _recodg_new_size)
        if _sparsedg_create:
            _diskgroupData["sparsedg_new_size"] = _sparsedg_new_size

        _diskgroupData["datadg_new_size"] = _datadg_new_size
        _diskgroupData["recodg_new_size"] = _recodg_new_size

        ebLogInfo(f"{_thisFn} - The new Data, Reco and Sparse diskgroup sizes "+
            "are %s MB, %s MB and %s MB" 
            % (_datadg_new_size, _recodg_new_size, _sparsedg_new_size))

        ebLogInfo(f"*** {_thisFn} <<<")

        return 0

    #end mCalculateNewDgSizes

    def mCalcCurrentDgRatio(self, aDiskgroupData, aDataDgCurSize, aRecoDgCurSize):
        _thisFn = "ebCluManageDiskgroup:mCalcCurrentDgRatio"
        ebLogInfo(f"*** {_thisFn} >>>")
        
        _datadg_cur_size = aDataDgCurSize
        _recodg_cur_size = aRecoDgCurSize
        _diskgroupData = aDiskgroupData

        _data_reco_ratio = _datadg_cur_size/_recodg_cur_size
        _disk_backup_enabled = _recodg_cur_size > _datadg_cur_size
        if _disk_backup_enabled:
            _data_reco_ratio = round(_data_reco_ratio, 4)
            if 39/60 <= _data_reco_ratio <= 41/60:
                _curr_dg_ratio = "40:60"
            elif 34.3/50 < _data_reco_ratio < 36/50:
                _curr_dg_ratio = "35:50:15"
            else:
                ebLogError(f"*** {_thisFn} - Current diskgroup ratios are not correctly configured. \
                            Please contact ops to provide additional paramters for sparse creation/deletion operations")
                return 1
        else:
            _data_reco_ratio = round(_data_reco_ratio)
            if _data_reco_ratio == 3:
                _curr_dg_ratio = "60:20:20"
            elif _data_reco_ratio == 4:
                _curr_dg_ratio = "80:20"
            else:
                ebLogError(f"*** {_thisFn} - Current diskgroup ratios are not correctly configured. \
                            Please contact ops to provide additional paramters for sparse creation/deletion operations")
                return 1

        _diskgroupData["curr_dg_ratio"] = _curr_dg_ratio
        
        ebLogInfo(f"** {_thisFn} - Current DG ratio %s" % (_curr_dg_ratio))
                
        ebLogInfo(f"*** {_thisFn} <<<")

        return 0

    def mCalcTotalStorageForUpdate(self, aDiskgroupData, aCurrentDgSizesDict, aDgRatio):
        _thisFn = "ebCluManageDiskgroup:mCalcTotalStorageForUpdate"
        ebLogInfo(f"*** {_thisFn} >>>")

        _diskgroupData = aDiskgroupData
        _cur_dg_sizes = aCurrentDgSizesDict
        _dg_ratio = aDgRatio

        _constantsObj = self.mGetConstantsObj()
        _datadg_cur_size = _cur_dg_sizes[_constantsObj._data_dg_rawname]
        _recodg_cur_size = _cur_dg_sizes[_constantsObj._reco_dg_rawname]

        _ratio_split = _dg_ratio.split(":")

        _sparsedg_cur_size = (_recodg_cur_size * int(_ratio_split[2])/int(_ratio_split[1]))
        _total_storage_size = _datadg_cur_size + _recodg_cur_size + _sparsedg_cur_size

        # Currently sizes are in MB, convert it to GB for later conversion
        _total_storage_size = round(_total_storage_size/1024)
        _diskgroupData["_total_storage_size"] = _total_storage_size

        ebLogInfo(f"** {_thisFn} - Current total storage size is %s GB" % (_total_storage_size))

        ebLogInfo(f"*** {_thisFn} <<<")

        return 0

    def mValidateNewDgRatio(self, aDiskgroupData, aNewDgRatio, aSparseCreate):
        from exabox.ovm.clustorage import mParseStorageDistrib
        _thisFn = "ebCluManageDiskgroup:mValidateNewDgRatio"
        ebLogInfo(f"*** {_thisFn} >>>")

        _diskgroupData = aDiskgroupData
        _new_dg_ratio = aNewDgRatio
        _sparsedg_create = aSparseCreate

        # Validate ratio for 3 disgroups is defined and have correct format
        # Throw ValueError on error
        if _new_dg_ratio:
            _dataPct, _recoPct, _sparsePct = mParseStorageDistrib(_new_dg_ratio)

        _ratio_split = _new_dg_ratio.split(":")

        _diskgroupData["ratio_split"] = _ratio_split

        ebLogInfo(f"*** {_thisFn} <<<")

        return 0

    # Method to parse input JSON and validate the arguments
    def mClusterParseInput(self, aOptions, aReqParams, aOpData=None):
        _thisFn = "ebCluManageDiskgroup:mClusterParseInput"
        ebLogInfo(f"*** {_thisFn} >>>")
        _options = aOptions
        _reqparams = aReqParams
        # Get the constants object for use in the scope of this function
        _constantsObj = self.mGetConstantsObj()

        # Get the cluctrl handle to fetch current details
        _eBoxCluCtrl = self.mGetEbox()

        if aOpData is None:
            _op_data = self.mGetDiskGroupOperationData()
        else:
            _op_data = aOpData
            
        _dg_type_key_upper = (_constantsObj._diskgrouptype_key).upper()
        _dg_name_key_upper = (_constantsObj._diskgroupname_key).upper()
        _rbpower_key_upper = (_constantsObj._rebalancepower_key).upper()
        _newsize_key_upper = (_constantsObj._newsizeGB_key).upper()
        # As the ratios are just numbers, no need to make them upper
        _diskgroup_ratios_key  = (_constantsObj._diskgroup_ratios_key)
        _disk_backup_key_upper = (_constantsObj._disk_backup_key).upper()
        _total_storagegb_key   = (_constantsObj._total_storagegb_key)

        # Input JSON file is required
        _inputjson = _options.jsonconf
        if not _inputjson:
            return self.mRecordError(gDiskgroupError['MissingInputPayload'])
        
        if _op_data["Command"] == "dg_create":
            # Diskgroup Type is a MUST for create operation
            if (_dg_type_key_upper not in (key.upper() for key in list(_inputjson.keys())) or\
                 not _inputjson[_constantsObj._diskgrouptype_key]):
                return self.mRecordError(gDiskgroupError['MissingDiskgroupType'])

        if _op_data["Command"] == "dg_update_add_sparse":
            # Diskgroup Type is a MUST for update add sparse
            if (_dg_type_key_upper not in (key.upper() for key in list(_inputjson.keys())) or\
                 not _inputjson[_constantsObj._diskgrouptype_key]):
                return self.mRecordError(gDiskgroupError['MissingDiskgroupType'])
            
        if _op_data["Command"] == "dg_resize":
            # Diskgroup Size is a MUST for resize operation
            if (_newsize_key_upper not in (key.upper() for key in list(_inputjson.keys())) or\
                 not _inputjson[_constantsObj._newsizeGB_key]):
                return self.mRecordError(gDiskgroupError['MissingDiskgroupSize'])
        
        if _op_data["Command"] == "dg_drop":
            if _inputjson[_constantsObj._diskgrouptype_key].upper() == 'SPARSE':
                #find the sparse disk group name to be deleted
                _cluster = _eBoxCluCtrl.mGetClusters().mGetCluster()
                _cludgroups = _cluster.mGetCluDiskGroups()
                _sparse_found = False
                _data_dgid = None
                for _dgid in _cludgroups:
                    if _dgid.find(_constantsObj._data_dg_rawname) > 0:
                        _data_dgid = _dgid
                        continue
                    if _dgid.find(_constantsObj._sparse_dg_rawname) > 0:
                        _dg = _eBoxCluCtrl.mGetStorage().mGetDiskGroupConfig(_dgid)
                        _dg_type = _dg.mGetDiskGroupType().lower()
                        if _dg_type == _constantsObj._sparse_dg_type_str:
                            _sparse_dg = _dg
                            _inputjson[_constantsObj._diskgroupname_key] = _sparse_dg.mGetDgName()
                            _sparse_found = True
                        break
                    else:
                        ebLogInfo("*** _sparse_dg_rawname not found")
                        _sparse_dg = copy.deepcopy(_eBoxCluCtrl.mGetStorage().mGetDiskGroupConfig(_data_dgid))
                        _sparse_dg_id =_data_dgid.replace(_constantsObj._data_dg_type_str, _constantsObj._sparse_dg_type_str)
                        _sparse_dg.mReplaceDgId(_sparse_dg_id)
                        _sparse_dg.mReplaceDgName(_sparse_dg.mGetDgName().replace(_constantsObj._data_dg_prefix, _constantsObj._sparse_dg_prefix))
                        _inputjson[_constantsObj._diskgroupname_key] = _sparse_dg.mGetDgName()
                        _sparse_found = True
                        break
                if not _sparse_found:
                    ebLogError("*** Not able to get the sparse diskgroup name")
                    return self.mRecordError(gDiskgroupError['DgDoesNotExist'])
            # Diskgroup Name is a MUST for drop operation
            elif (_dg_name_key_upper not in (key.upper() for key in list(_inputjson.keys())) or\
                 not _inputjson[_constantsObj._diskgroupname_key]):
                return self.mRecordError(gDiskgroupError['MissingDiskgroupName'])

        if _op_data["Command"] == "dg_precheck":
            # Diskgroup Type is a MUST for sparse creation precheck
            if (_constantsObj._optype_key in list(_inputjson.keys())) and \
                 (_inputjson[_constantsObj._optype_key] == "ENABLE_SPARSE"):
                _inputjson[_constantsObj._diskgrouptype_key] = 'sparse'
            else:
                return self.mRecordError(gDiskgroupError['MissingArgs'])
            
        # Diskgroup Name is a MUST if diskgroup type is NOT SPARSE
        if (((_dg_type_key_upper in (key.upper() for key in list(_inputjson.keys())) and\
               _inputjson[_constantsObj._diskgrouptype_key].upper() != 'SPARSE') \
              or _op_data["Command"] not in ["dg_create","dg_precheck"]) and
                (_dg_name_key_upper not in (key.upper() for key in list(_inputjson.keys())) or\
                  not _inputjson[_constantsObj._diskgroupname_key])):
            return self.mRecordError(gDiskgroupError['MissingDiskgroupName'])
        
        for key in list(_inputjson.keys()):
            if _dg_type_key_upper == key.upper():
                _reqparams[_constantsObj._diskgrouptype_key] = _inputjson[key]
            if _dg_name_key_upper == key.upper():
                _reqparams[_constantsObj._diskgroupname_key] = _inputjson[key]
            if _rbpower_key_upper == key.upper():
                _reqparams[_constantsObj._rebalancepower_key] = _inputjson[key]
            if _newsize_key_upper == key.upper():
                _reqparams[_constantsObj._newsizeGB_key] = _inputjson[key]
            if _diskgroup_ratios_key == key:
                _reqparams[_constantsObj._diskgroup_ratios_key] = _inputjson[key]
            if _disk_backup_key_upper == key.upper():
                _reqparams[_constantsObj._disk_backup_key] = _inputjson[key].upper() == "TRUE"
            if _total_storagegb_key == key:
                _reqparams[_constantsObj._total_storagegb_key] = _inputjson[key]
        
        ebLogInfo(f"*** {_thisFn} p:{_reqparams}")
        ebLogInfo(f"*** {_thisFn} <<<")
        return 0
    # end

    def mExecuteSetDGsRebalancePower(self, aDgsList, aRebalancePower):
        ebLogInfo("*** ebCluManageDiskgroup:mExecuteSetDGsRebalancePower >>>")
        _dg_list = aDgsList
        _rebalancePower = aRebalancePower
        _eBoxCluCtrl = self.mGetEbox()
        _rc = 0
        
        for _dg_name in _dg_list:
            ebLogInfo("*** Setting rebalance power for diskgroup %s" %(_dg_name))
            _dg_data = {}
            _dg_data["Command"] = "dg_rebalance"
            _dg_data['diskgroup'] = _dg_name
            _dg_data['rebalance_power'] = _rebalancePower
            
            dgrpOpOptions = self.mGetAoptions()
            dgrpOpOptions.jsonconf['diskgroup'] =_dg_data['diskgroup']
            dgrpOpOptions.jsonconf['rebalance_power'] = _rebalancePower
            dgrpOpOptions.configpath = self.__xmlpath
            
            self.mSetDiskGroupOperationData(_dg_data)
            _rc = self.mClusterDgrpRebalance(dgrpOpOptions)
            if _rc != 0:
                _detail_error = "Could not set new rebalance power for diskgroup " + _dg_name
                _eBoxCluCtrl.mUpdateErrorObject(gElasticError['CELL_DG_REBAL_POWER_SET_FAILED'], _detail_error)
                return self.mRecordError(gDiskgroupError['DgOperationError'], "*** " + _detail_error)
        ebLogInfo("*** ebCluManageDiskgroup:mExecuteSetDGsRebalancePower <<<")
        return _rc
    # end mExecuteSetDGsRebalancePower

    # Method to prepare dbaasapi calls
    def mHandleDbaasapiSynchronousCall(self, aOptions, aJsonPayload, aInfo=False, aMsg={}):
        ebLogInfo("*** ebCluManageDiskgroup:mHandleDbaasapiSynchronousCall >>>")
        _options = aOptions
        _injson = aJsonPayload
        _ebox = self.mGetEbox()
        # Get the constants object for use in the scope of this function
        _constantsObj = self.mGetConstantsObj()
        _diskgroupData = self.mGetDiskGroupOperationData()
        _dbaasobj = self.mGetDbaasObj()
        _uuid = _ebox.mGetUUID()
        _dbName = _constantsObj._dbname_value
        _info = aInfo
        random_int = secrets.randbelow(1_000_000)
        x = str(random_int / 1_000_000)
        _uniqStr = f"-{_uuid}-{x}"
        _opTarget = "diskgroupOp"
        
        _outfile = "/var/opt/oracle/log/" + _constantsObj._dbname_value + "/" + _opTarget + _uniqStr + "." +\
                   _injson[_constantsObj._action_key] + "_" + _uuid + ".out"
                   
        _injson[_constantsObj._outfile_key] = _outfile

        _domulist = None

        _domUs = self.mGetDomUs()

        _input_filename = _opTarget + _uniqStr + "_input_" + _uuid + ".json"
        _input_file_lcopy = "/tmp/" + _input_filename  # local copy on exacloud box
        _input_file_rcopy = "/var/opt/oracle/log/dbaasapi/" + _input_filename  # remote copy on DomU

        _outJson = None            
        if _info:  # Caller would expect an output JSON
            _outJson = "/var/opt/oracle/log/" + _constantsObj._dbname_value + "/" + _opTarget + _uniqStr +\
             "." + _injson[_constantsObj._action_key] + "_" + _uuid + ".json"
            _injson[_constantsObj._params_key][_constantsObj._param_infofile_key] = _outJson
            
        ebLogInfo("*** The input JSON for operation %s action %s is:" 
                       %(_injson[_constantsObj._operation_key], _injson[_constantsObj._action_key]))
        ebLogInfo(json.dumps(_injson, default=universal_converter, 
            indent=4, sort_keys=True))

        self.mSetOutJson(_outJson)
            
        with open(_input_file_lcopy, 'w') as infile:
            json.dump(_injson, infile, default=universal_converter, 
                sort_keys=True, skipkeys=True, indent=4, ensure_ascii=False)

        # Initiate the step
        _cmd = "nohup /var/opt/oracle/dbaasapi/dbaasapi -i " + _input_file_rcopy + " < /dev/null\
         > /dev/null 2>&1"
        for _domU in _domUs:
            self.mSetLastDomUused(_domU)
            # Copy the input json file to the domU
            ebLogInfo("*** ebCluManageDiskgroup:mHandleDbaasapiSynchronousCall - Copying dbaasapi " + \
                        "input JSON to DomU %s" %(_domU))
            _dbaasobj.mBaseCopyFileToDomU(_domU, _input_file_lcopy, _input_file_rcopy)

            # It's ok to clean this here because we only use this once
            _ebox.mExecuteLocal("/bin/rm -f " + _input_file_lcopy)

            # Execute the step
            ebLogInfo("*** ebCluManageDiskgroup:mHandleDbaasapiSynchronousCall - Executing command %s on \
                       DomU %s" %(_cmd, _domU))
            _i, _o, _e = _dbaasobj.mExecCommandOnDomU(_domU, _options, _cmd)
            if str(_e) == "0":
                _diskgroupData ["Status"] = "Pass"
            else:
                _logmsg = "*** Failed to execute dbaasapi command for action " +\
                 _injson[_constantsObj._action_key] + " under operation " + _injson[_constantsObj._operation_key] 
                ebLogInfo("%s" % (_logmsg))
                _diskgroupData["Log"] = _logmsg
                _diskgroupData["Status"] = "Fail"

            if str(_e) == "0":
                # Read the job ID 
                _idobj = _dbaasobj.mReadStatusFromDomU(_options, _domU, _outfile)
                if not _idobj or ("id" not in _idobj):
                    _logmsg = "*** Failed to read Job ID from domU"
                    ebLogInfo("%s" % (_logmsg))
                    _diskgroupData["Log"] = _logmsg
                    _diskgroupData["Status"] = "Fail"
                    return self.mRecordError(gDiskgroupError['DbaasObjJobIDReadFail'], "*** Dbaas Obj Failed to read Job ID from domU" )
    
                _jobid = _idobj["id"]
                self.mSetJobId(_jobid)
    
                if "logfile" in _idobj:
                    self.mSetLogFile(_idobj["logfile"])
    
                # Wait for step to complete
                _infileName = _opTarget + _uniqStr + "." + "status" + ".json"
                _outfile = "/var/opt/oracle/log/" + _constantsObj._dbname_value + "/" + _opTarget + _uniqStr + "." + "status" + ".out"
                
                _status = _dbaasobj.mWaitForJobComplete(_options, _dbName, _domU, _jobid, _diskgroupData,
                                                         _injson[_constantsObj._operation_key], _infileName,
                                                          _outfile, _outJson)
                if _injson[_constantsObj._action_key] == "resize":
                    _response = _dbaasobj.mReadStatusFromDomU(_options, _domU, _outfile)
                    aMsg["msg"] = _response["msg"]
                    if "errmsg" in _response.keys() and _response['errmsg']:
                        aMsg["errmsg"]  = _response['errmsg']
                # TODO : Copy DomU logs
                if _status == 0:
                    _logmsg = "*** " + _injson[_constantsObj._action_key] + " action succeeded for operation " + _opTarget
                    _diskgroupData["Log"] = _logmsg
                    _diskgroupData["Status"] = "Pass"
                    return 0
                else:
                    _dbaasobj.mCopyDomuInfoLog(_options, _domU, self.mGetLogFile(), _outfile)

            break  # We need to perform this on the first DomU only
        
        ebLogInfo("*** ebCluManageDiskgroup:mHandleDbaasapiSynchronousCall <<<")
    # end

    # Generic method to execute DATA/SPARSE diskgroup creation
    # param aResizablePrecheckOnly when set will result in only precheck for DG resize to be run and not the real DG creation
    def mClusterDgrpCreate(self, aOptions, aShrinkExistingDgs=True, aResizablePrecheckOnly=False, aDiskgroupData=None):

        if aResizablePrecheckOnly:
            ebLogInfo("*** ebCluManageDiskgroup:mClusterDgrpCreate ResizablePrecheckOnly >>>")
        else:
            ebLogInfo("*** ebCluManageDiskgroup:mClusterDgrpCreate >>>")
        _options = aOptions
        # Get the cluctrl handle to fetch current details
        _eBoxCluCtrl = self.mGetEbox()
        # Get the constants object for use in the scope of this function
        _constantsObj = self.mGetConstantsObj()

        if aDiskgroupData is None:
            _diskgroupData = self.mGetDiskGroupOperationData()
        else:
            _diskgroupData = aDiskgroupData

        _rollback_stack = self.mGetRollbackStack()
        _shrink_existing_dgs = aShrinkExistingDgs
        self.__shrink_existing_dgs = _shrink_existing_dgs

        _diskgroupData["Status"] = "Pass"
        _diskgroupData["ErrorCode"] = "0"
        
        _data_dg = None
        _reco_dg = None
        _cluster = _eBoxCluCtrl.mGetClusters().mGetCluster()
        _cludgroups = _cluster.mGetCluDiskGroups()
        _dgid = None
        _redundancy_factor = 1
        for _dgid in _cludgroups:
            if _data_dg is not None and _reco_dg is not None:
                break
            _dg = _eBoxCluCtrl.mGetStorage().mGetDiskGroupConfig(_dgid)
            _dg_type = _dg.mGetDiskGroupType().lower()
            if _dg_type == _constantsObj._data_dg_type_str:
                _data_dg = _dg
                if _data_dg.mGetDgRedundancy() == "HIGH":
                    _redundancy_factor = 3
                elif _data_dg.mGetDgRedundancy() == "NORMAL":
                    _redundancy_factor = 2
                else:
                    _redundancy_factor = 1
            if _dg_type == _constantsObj._reco_dg_type_str:
                _reco_dg = _dg

        _datadg_name = _data_dg.mGetDgName()
        _recodg_name = _reco_dg.mGetDgName()

        _inparams = {}
        ebLogInfo("** ebCluManageDiskgroup:mClusterDgrpCreate - Fetching and validating input args")
        _rc = self.mClusterParseInput(_options, _inparams, _diskgroupData)
        if _rc == 0:
            _diskgroupData[_constantsObj._diskgrouptype_key] = _inparams[_constantsObj._diskgrouptype_key]
            # The name will be ignored if the diskgroup type is 'sparse'
            if _inparams[_constantsObj._diskgrouptype_key] == _constantsObj._sparse_dg_type_str:
                _diskgroupData[_constantsObj._diskgroupname_key] = _datadg_name.replace\
                                (_constantsObj._data_dg_prefix, _constantsObj._sparse_dg_prefix, 1)
            else: 
                if (_constantsObj._diskgroupname_key in _inparams and _inparams[_constantsObj._diskgroupname_key]):
                    _diskgroupData[_constantsObj._diskgroupname_key] = _inparams[_constantsObj._diskgroupname_key]
            if (_constantsObj._rebalancepower_key in _inparams and _inparams[_constantsObj._rebalancepower_key]):
                _diskgroupData[_constantsObj._rebalancepower_key] = _inparams[_constantsObj._rebalancepower_key]
            
        else:
            ebLogInfo("Returning due to input args related error. The input arg(s) provided is/are not vaild")
            return _rc

        if aResizablePrecheckOnly:
            _diskgroupData[_constantsObj._diskgrouptype_key] = _constantsObj._sparse_dg_type_str
        _dg = _diskgroupData[_constantsObj._diskgroupname_key]
        if self.mCheckDgExist(_options, _dg):
            return self.mRecordError(gDiskgroupError['DgAlreadyExists'], "The diskgroup %s already exists" % (_inparams[_constantsObj._diskgrouptype_key]))

        # Save the list of all diskgroups in the cluster
        _cluster = _eBoxCluCtrl.mGetClusters().mGetCluster()
        _cludgroups = _cluster.mGetCluDiskGroups()
        ebLogInfo("*** mClusterDgrpCreate: DG List : %s" % ' '.join(_cludgroups))
        
        for _dgid in _cludgroups:            
            _curr_dg = _eBoxCluCtrl.mGetStorage().mGetDiskGroupConfig(_dgid)
            _dg_type = _curr_dg.mGetDiskGroupType().lower()
            if _shrink_existing_dgs and (_dg_type.find(_inparams[_constantsObj._diskgrouptype_key]) != -1):
                return self.mRecordError(gDiskgroupError['DgAlreadyExists'], "The diskgroup %s already exists" % (_inparams[_constantsObj._diskgrouptype_key]))
        
        _step_list = ["Check_Diskgroups_Resizable", "Update_DiskgroupData", "Resize_Diskgroup_and_Cell_Griddisks", "Create_Griddisks", "Create_Diskgroup", "Complete"]

        _eBoxCluCtrl.mUpdateStatusOEDA(True, _step_list[0], _step_list, "Checking diskgroup current and new sizes")
        ebLogInfo("*** Executing steps required for creation of diskgroup %s of type %s" %\
                   (_diskgroupData[_constantsObj._diskgroupname_key], _diskgroupData[_constantsObj._diskgrouptype_key]))
        
        _cur_dg_sizes = {}
        _cur_dg_sizes[_constantsObj._data_dg_rawname] = self.mUtilGetDiskgroupSize(_options, _datadg_name, _constantsObj)
        _cur_dg_sizes[_constantsObj._reco_dg_rawname] = self.mUtilGetDiskgroupSize(_options, _recodg_name, _constantsObj)
        _cur_dg_sizes[_constantsObj._redundancy_factor] = _redundancy_factor       

        ebLogInfo("*** ebCluManageDiskgroup:mClusterDgrpCreate - Current diskgroup sizes are %s" % (_cur_dg_sizes))

        ebLogInfo("** ebCluManageDiskgroup:mClusterDgrpCreate - Getting diskgroup distribution percentages")
        # Save the default ratios in diskgroup data if not specified by the user
        _rc = self.mCalculateNewDgSizes(_options, _diskgroupData, _cur_dg_sizes, True)
        if _rc:
            ebLogError("** ebCluManageDiskgroup:mClusterDgrpCreate - Could not get diskgroup distribution percentages for %s %s diskgroup operation"
                % (_options.diskgroupOp, _diskgroupData[_constantsObj._diskgroupname_key]))
            return _rc
        
        _new_dg_sizes = {}
        _new_dg_sizes[_constantsObj._data_dg_rawname] = 0
        _new_dg_sizes[_constantsObj._reco_dg_rawname] = 0

        if  _inparams[_constantsObj._diskgrouptype_key] == "sparse":
            ebLogInfo("*** Checking if applicable diskgroups are resizable")
            _rc = self.mCheckIfDgsResizable(_options, _cur_dg_sizes, _new_dg_sizes, _diskgroupData)
            if aResizablePrecheckOnly:
                ebLogInfo("*** ebCluManageDiskgroup:mClusterDgrpCreate ResizablePrecheckOnly<<<")
                return _rc
            if _rc:
                return _rc
            
            ebLogInfo("*** DGs Resizable; Getting cell count and griddisk count for resizing griddisks")
            _eBoxCluCtrl.mUpdateStatusOEDA(True, _step_list[1], _step_list, "Getting cell count and griddisk count")

             # Also update DiskgroupData with sparse related info, cell count and griddisk count in case of rollback
            ebLogInfo("*** ebCluManageDiskgroup:mClusterDgrpCreate - Updating DiskgroupData with sparse related info, cell count and griddisk count for rollback")
            _rc = self.mUpdateDgrpData(_options, _diskgroupData, _datadg_name, _cur_dg_sizes[_constantsObj._data_dg_rawname])
            if _rc:
                ebLogError("*** ebCluManageDiskgroup:mClusterDgrpCreate - Could not get cell count and griddisk count")

            ebLogInfo("*** ebCluManageDiskgroup:mClusterDgrpCreate - Updating Diskgroupdata complete. Attempting to resize DGs and Griddisks")

            if _shrink_existing_dgs:
                _eBoxCluCtrl.mUpdateStatusOEDA(True, _step_list[2], _step_list, "Attempting to resize DGs and Griddisks")
                # We need to compare current and new diskgroup sizes to determine whether to resize dgs first, or the diskgroups first
                _rc = self.mResizeDgAndGriddisks(_options, _datadg_name, _new_dg_sizes[_constantsObj._data_dg_rawname],
                    _cur_dg_sizes[_constantsObj._data_dg_rawname], _rollback_stack, _diskgroupData)
                if _rc == 0:
                    _rc = self.mResizeDgAndGriddisks(_options, _recodg_name, _new_dg_sizes[_constantsObj._reco_dg_rawname],
                        _cur_dg_sizes[_constantsObj._reco_dg_rawname], _rollback_stack, _diskgroupData)
                    if _rc:
                        return _rc

                else:
                    return _rc

            else:
                _eBoxCluCtrl.mUpdateStatusOEDA(True, _step_list[2], _step_list, "Shrink is set to false. Skipping dg and griddisk resize")
            
            ebLogInfo("*** Diskgroup and Griddisk resize completed; Attempting to create Griddisks sparse diskgroup")
            _eBoxCluCtrl.mUpdateStatusOEDA(True, _step_list[3], _step_list, "Creating sparse griddisks")

            _rollback_stack.append({self.mDropGridDisks:(_options, _dg)})
            _rc = self.mCreateSparseGriddisks(_options, _diskgroupData)
            if _rc:
                _tempResult = self.mRollback(_rollback_stack)
                return _rc
            
            ebLogInfo("*** Griddisks created for sparse diskgroup; Attempting to create the diskgroup")
            _eBoxCluCtrl.mUpdateStatusOEDA(True, _step_list[4], _step_list, "Creating sparse diskgroup")
            
            _rollback_stack.append({self.mDropDiskGroup:(_options, _dg, "yes")})
            _rc = self.mCreateSparseDg(_options, _new_dg_sizes, _diskgroupData)
            if _rc:
                _tempResult = self.mRollback(_rollback_stack)
                return _rc
            
            ebLogInfo("*** Diskgroup created; Ensuring re-balancing of the same")
            _rc = self.mEnsureDgsRebalanced(_options, _diskgroupData[_constantsObj._sparse_dg_rawname], _diskgroupData)
            if _rc:
                _tempResult = self.mRollback(_rollback_stack)
                return _rc
            _eBoxCluCtrl.mUpdateStatusOEDA(True, _step_list[5], _step_list, "Completed creating sparse diskgroup")
        
        else:
            if aResizablePrecheckOnly:
                ebLogError("*** Diskgroup type %s currently unsupported for Precheck" % (_inparams[_constantsObj._diskgrouptype_key]))
                ebLogInfo("*** ebCluManageDiskgroup:mClusterDgrpCreate ResizablePrecheckOnly<<<")
                return _rc
            ebLogError("*** Diskgroup type %s currently unsupported" % (_inparams[_constantsObj._diskgrouptype_key]))
                
        _eBoxCluCtrl.mUpdateStatusOEDA(True, "Complete", _step_list, "Diskgroup Create Completed")

        ebLogInfo("ebCluManageDiskgroup:mClusterDgrpCreate - DiskgroupData variable is %s" % (_diskgroupData))
        
        ebLogInfo("*** ebCluManageDiskgroup:mClusterDgrpCreate <<<")
        return _rc

    # end

    # Method to execute resizeDG and resizeGridDisk methods on the basis of current and new sizes
    def mResizeDgAndGriddisks(self, aOptions, aDgName, aNewDgSize, aCurrentDgSize, aRollbackStack, aDiskgroupData=None, aDeleteSparse=False):

        ebLogInfo("*** ebCluManageDiskgroup:mResizeDgAndGriddisks >>>")
        _options = aOptions

        if aDiskgroupData is None:
            _diskgroupData = self.mGetDiskGroupOperationData()
        else:
            _diskgroupData = aDiskgroupData

        _dg_name = aDgName
        _new_dg_size = aNewDgSize
        _rollback_stack = aRollbackStack
        _delete_sparse = aDeleteSparse

        _cur_dg_size = aCurrentDgSize
        _new_dg_size = aNewDgSize

        _rc = 0

        if _cur_dg_size > _new_dg_size:

            ebLogInfo("*** ebCluManageDiskgroup:mResizeDgAndGriddisks - Resizing Diskgroup %s" % (_dg_name))
            _rollback_stack.append({self.mResizeDg:(_options, _dg_name, _cur_dg_size, _diskgroupData, _delete_sparse)})
            _rc = self.mResizeDg(_options, _dg_name, _new_dg_size, _diskgroupData, _delete_sparse)
            if _rc:
                ebLogError("*** ebCluManageDiskgroup:mResizeDgAndGriddisks - Could not resize diskgroup %s" % (_dg_name))
                _tempResult = self.mRollback(_rollback_stack)
                return _rc

            ebLogInfo("*** ebCluManageDiskgroup:mResizeDgAndGriddisks - Resizing Griddisks of diskgroup %s" % (_dg_name))
            _rollback_stack.append({self.mResizeGriddisks:(_options, _dg_name, _cur_dg_size, _diskgroupData)})
            _rc = self.mResizeGriddisks(_options, _dg_name, _new_dg_size, _diskgroupData)
            if _rc:
                ebLogError("*** ebCluManageDiskgroup:mResizeDgAndGriddisks - Could not resize griddisks for diskgroup %s" % (_dg_name))
                _tempResult = self.mRollback(_rollback_stack)
                return _rc

        elif _cur_dg_size < _new_dg_size:
            ebLogInfo("*** ebCluManageDiskgroup:mResizeDgAndGriddisks - Resizing Griddisks of diskgroup %s" % (_dg_name))
            _rollback_stack.append({self.mResizeGriddisks:(_options, _dg_name, _cur_dg_size, _diskgroupData)})
            _rc = self.mResizeGriddisks(_options, _dg_name, _new_dg_size, _diskgroupData)
            if _rc:
                ebLogError("*** ebCluManageDiskgroup:mResizeDgAndGriddisks - Could not resize griddisks for diskgroup %s" % (_dg_name))
                _tempResult = self.mRollback(_rollback_stack)
                return _rc

            ebLogInfo("*** ebCluManageDiskgroup:mResizeDgAndGriddisks - Resizing Diskgroup %s" % (_dg_name))
            _rollback_stack.append({self.mResizeDg:(_options, _dg_name, _cur_dg_size, _diskgroupData, _delete_sparse)})
            _rc = self.mResizeDg(_options, _dg_name, _new_dg_size, _diskgroupData, _delete_sparse)
            if _rc:
                ebLogError("*** ebCluManageDiskgroup:mResizeDgAndGriddisks - Could not resize diskgroup %s" % (_dg_name))
                _tempResult = self.mRollback(_rollback_stack)
                return _rc

        else:
            ebLogInfo("*** ebCluManageDiskgroup:mResizeDgAndGriddisks - Current dg size is equal to new dg size. Skipping resize dg and griddisks")
            return _rc

        ebLogInfo("*** ebCluManageDiskgroup:mResizeDgAndGriddisks <<<")
        return _rc

    # Method to execute the commands in rollback stack
    def mRollback(self, aRollbackStack):
        ebLogInfo("*** ebCluManageDiskgroup:mRollback <<<")
        _rollback_stack = aRollbackStack
        _original_stack_size = len(_rollback_stack)

        _tempResult = 0
        while(_rollback_stack):
            # We have a list of dictionary in the stack. Get the di
            _stack_dict = _rollback_stack.pop()
            _dict_keys = _stack_dict.keys()

            # Check if more than one key
            if(len(_dict_keys) > 1):
                ebLogError("*** mRollback: Number of keys in any dictionary in rollback stack cannot be greater than 1")

            for _rollback_funtion in _dict_keys:

                ebLogInfo("*** ebCluManageDiskgroup:mRollback - Executing rollback function %s with parameters %s" % (_rollback_funtion, _stack_dict[_rollback_funtion]))
                # '*' will pass the dictionary value as all parameters in function

                _tempResult = _rollback_funtion(*_stack_dict[_rollback_funtion])

                if(_tempResult):
                    # Will skip the error for the first rollback function in stack as it can result it failure
                    if(_original_stack_size == len(_rollback_stack) - 1):
                        continue
                    else:
                        ebLogError("*** mRollback: Could not complete the function: %s" % (_rollback_funtion))
                        return _tempResult

        ebLogInfo("*** ebCluManageDiskgroup:mRollback - Rollback complete <<<")
        return _tempResult

    # end
    # modifying payload to match dbaas 35947615
    def mGetFailGroupList(self, aDiskGroupSuffix):
        ebLogInfo("*** ebCluManageDiskgroup:mGetFailGroupList>>>")
        # Get the cluctrl handle to fetch current details
        _eBoxCluCtrl = self.mGetEbox()
        _list_all_griddisk = []
        _failgroup_list = []
        _cell_list = _eBoxCluCtrl.mReturnCellNodes()
        for _cell_name in sorted(_cell_list.keys()):
            with connect_to_host(_cell_name, get_gcontext()) as _node:
                try:
                    _list_all_griddisk  += _eBoxCluCtrl.mGetStorage().mListCellDG(_node, aDiskGroupSuffix)
                except Exception as e:
                    ebLogError(f"*** Exception Message Detail on host {_cell_name} {e}")
        for _griddisk in _list_all_griddisk:
            _failgroup_list.append(_griddisk.strip().split()[0])
        ebLogInfo("*** ebCluManageDiskgroup:mGetFailGroupList list is: %s <<<"% (_failgroup_list))
        return _failgroup_list

    # Method to Resize a Diskgroup
    def mClusterDgrpResize(self, aOptions):
        """
        In RESIZE_DGS step, run only Resize processes:
        * mResizeGriddisks
        In WAIT_RESIZE_DGS step, run only WAIT processes:
        * mEnsureDgsRebalanced and 
        * mValidateDgsPostRebalance
        """

        _op = "ResizeDiskgroup"
        return self.mDiskgroupUpdate(aOptions, _op)
    # end

    # Method to update rebalance power of a diskgroup operation
    def mClusterDgrpRebalance(self, aOptions):
        
        _op = "RebalanceDiskgroup"
        return self.mDiskgroupUpdate(aOptions, _op)
    
    # end
        
    
    def mClusterDgrpInfo(self, aOptions, aPropList=None):
        _options = aOptions
        # Get the cluctrl handle to fetch current details
        _eBoxCluCtrl = self.mGetEbox()
        # Get the constants object for use in the scope of this function
        _constantsObj = self.mGetConstantsObj()
        # Get the dbaasobj handle for dbaasapi calls and handling DomU commands/output
        _dbaasObj = self.mGetDbaasObj()

        _diskgroupData = self.mGetDiskGroupOperationData()
        _diskgroupData["Status"] = "Pass"
        _diskgroupData["ErrorCode"] = "0"
        
        _dg_name_key = _constantsObj._diskgroupname_key 

        _inparams = {}
        _rc = self.mClusterParseInput(_options, _inparams)
        step_list = ["InfoFetch", "Complete"]
        if _rc == 0:
            _eBoxCluCtrl.mUpdateStatusOEDA(True, "InfoFetch", step_list, 
                'Diskgroup Info Fetch operation for ' + _inparams[_dg_name_key])
            _rc = self.mClusterDgrpInfo2(_options, _inparams[_dg_name_key], aPropList)
            if _rc != 0:
                return self.mRecordError(gDiskgroupError['ErrorFetchingDetails'], 
                        "*** Could not fetch info for diskgroup " + _inparams[_dg_name_key])
            
            # Read the INFO file containing the storage property value
            # It should be ready and populated as mClusterDgrpInfo2 above is a blocking call
            _infoobj = _dbaasObj.mReadStatusFromDomU(_options, self.mGetLastDomUused(),\
                                                      self.mGetOutJson())
            _diskgroupData["DiskgroupInfo"] = _infoobj
        else:
            ebLogError("Returning due to input args related error")
            return _rc
        
        _eBoxCluCtrl.mUpdateStatusOEDA(True, "Complete", step_list,
                                        'Diskgroup Info Fetch operation for '
                                         + _inparams[_dg_name_key])
        return _rc
    # end
    
    # Function to drop the respective disk group
    # Force Drop option is used in create rollback if drop fails, but dsset needs to be updated to drop grid disks further
    def mDropDiskGroup(self, aOptions, aDg, aForceDrop="no"):

        ebLogInfo("*** ebCluManageDiskgroup:mDropDiskGroup >>>")
        _options = aOptions
        # Get the cluctrl handle to fetch current details
        _eBoxCluCtrl = self.mGetEbox()
        # Get the constants object for use in the scope of this function
        _constantsObj = self.mGetConstantsObj()

        _dg = aDg
        _force_drop = aForceDrop

        _injson = {}
        _injson[_constantsObj._dbaasapi_object_key] = _constantsObj._dbaasapi_object_value
        _injson[_constantsObj._operation_key] = _constantsObj._operation_value
        _injson[_constantsObj._action_key] = "drop"
        _injson[_constantsObj._params_key] = {}
        _injson[_constantsObj._params_key][_constantsObj._dbname_key] = _constantsObj._dbname_value
        _injson[_constantsObj._params_key][_constantsObj._diskgroupname_key] = _dg
        _injson[_constantsObj._params_key][_constantsObj._force_drop_key] = _force_drop
        _injson[_constantsObj._flags_key] = ""
        
        # Append to stack only if we are not in rollback mode            
        _rc = self.mHandleDbaasapiSynchronousCall(_options, _injson, False)
        if _rc:
            return _rc
        
        # Start update xml file
        _cluster = _eBoxCluCtrl.mGetClusters().mGetCluster()
        _cludgroups = _cluster.mGetCluDiskGroups()
        for _dgid in _cludgroups:
            _dgConfig = _eBoxCluCtrl.mGetStorage().mGetDiskGroupConfig(_dgid)
            if _dgConfig.mGetDgName() == _dg:
                ebLogInfo("*** Working on Diskgroup ID %s" %(_dgid))
                # Remove the old config 
                _eBoxCluCtrl.mGetStorage().mRemoveDiskGroupConfig(_dgid)
                _eBoxCluCtrl.mGetClusters().mGetCluster().mRemoveCluDiskGroupConfig(_dgid)
                break

        # Patch XM Cluster Configuration (note: this also write/create the new __patchconfig file)
        _eBoxCluCtrl.mSaveXMLClusterConfiguration()
        # End update xml file

        return _rc
    # end

    # Generic method to validate if diskgroup Exists
    def mCheckDgExist(self, aOptions, aDgName):
        ebLogInfo("*** ebCluManageDiskgroup:mCheckDgExist >>>")
        # Get the constants object for use in the scope of this function
        _constantsObj = self.mGetConstantsObj()
        _dgrp_properties = []
        _dgrp_properties.append(_constantsObj._propkey_storage)
        # Get DATA Diskgroup properties
        _rc = self.mClusterDgrpInfo2(aOptions, aDgName, _dgrp_properties)
        if _rc == 0:
            ebLogInfo("*** ebCluManageDiskgroup:mCheckDgExist is True<<<")
            return True
        ebLogInfo("*** ebCluManageDiskgroup:mCheckDgExist is False<<<")
        return False 
    
    # It's just for Sparse diskgroup right now
    def mClusterDgrpDrop(self, aOptions, aDiskgroupData=None):
        
        ebLogInfo("*** ebCluManageDiskgroup:mClusterDgrpDrop >>>")
        _options = aOptions
        # Get the cluctrl handle to fetch current details
        _eBoxCluCtrl = self.mGetEbox()
        # Get the constants object for use in the scope of this function
        _constantsObj = self.mGetConstantsObj()
        # Get the dbaasobj handle for dbaasapi calls and handling DomU commands/output
        _dbaasObj = self.mGetDbaasObj()

        _rollback_stack = self.mGetRollbackStack()

        if aDiskgroupData is None:
            _diskgroupData = self.mGetDiskGroupOperationData()
        else:
            _diskgroupData = aDiskgroupData
            
        _diskgroupData["Status"] = "Pass"
        _diskgroupData["ErrorCode"] = "0"
        
        _dg_name_key = _constantsObj._diskgroupname_key

        _data_dg = None
        _reco_dg = None
        _sparse_dg = None
        _cluster = _eBoxCluCtrl.mGetClusters().mGetCluster()
        _cludgroups = _cluster.mGetCluDiskGroups()
        _data_dgid = None
        _redundancy_factor = 1
        for _dgid in _cludgroups:
            _dg = _eBoxCluCtrl.mGetStorage().mGetDiskGroupConfig(_dgid)
            _dg_type = _dg.mGetDiskGroupType().lower()
            if _dg_type == _constantsObj._data_dg_type_str:
                _data_dg = _dg
                _data_dgid = _dgid
                if _data_dg.mGetDgRedundancy() == "HIGH":
                    _redundancy_factor = 3
                elif _data_dg.mGetDgRedundancy() == "NORMAL":
                    _redundancy_factor = 2
                else:
                    _redundancy_factor = 1
            if _dg_type == _constantsObj._reco_dg_type_str:
                _reco_dg = _dg
            if _dg_type == _constantsObj._sparse_dg_type_str:
                ebLogInfo("*** _sparse_dg_rawname found")
                _sparse_dg = _dg
            elif _dg_type != _constantsObj._sparse_dg_type_str:
                ebLogInfo("*** _sparse_dg_rawname not found")
                _sparse_dg = copy.deepcopy(_eBoxCluCtrl.mGetStorage().mGetDiskGroupConfig(_data_dgid))
                _sparse_dg_id =_data_dgid.replace(_constantsObj._data_dg_type_str, _constantsObj._sparse_dg_type_str)
                _sparse_dg.mReplaceDgId(_sparse_dg_id)
                _sparse_dg.mReplaceDgName(_sparse_dg.mGetDgName().replace(_constantsObj._data_dg_prefix, _constantsObj._sparse_dg_prefix))

        _datadg_name = _data_dg.mGetDgName()
        _recodg_name = _reco_dg.mGetDgName()
        _sparsedg_name = _sparse_dg.mGetDgName()
        ebLogInfo("*** _sparsedg_name is %s"%(_sparsedg_name))
        if not self.mCheckDgExist(_options, _sparsedg_name):
            ebLogInfo("The diskgroup %s does not exists. Marking the DG drop call as Success." % (_constantsObj._sparse_dg_type_str))
            return 0
        ebLogInfo("*** ebCluManageDiskgroup:mClusterDgrpDrop - Getting current diskgroup sizes")

        _cur_dg_sizes = {}
        _cur_dg_sizes[_constantsObj._data_dg_rawname] = self.mUtilGetDiskgroupSize(_options, _datadg_name, _constantsObj)
        _cur_dg_sizes[_constantsObj._reco_dg_rawname] = self.mUtilGetDiskgroupSize(_options, _recodg_name, _constantsObj)
        _cur_dg_sizes[_constantsObj._sparse_dg_rawname] = self.mUtilGetDiskgroupSize(_options, _sparsedg_name, _constantsObj)
        _cur_dg_sizes[_constantsObj._redundancy_factor] = _redundancy_factor

        ebLogInfo("*** ebCluManageDiskgroup:mClusterDgrpDrop - Current diskgroup sizes are %s" % (_cur_dg_sizes))

        ebLogInfo("** ebCluManageDiskgroup:mClusterDgrpCreate - Getting diskgroup distribution percentages")
        # Save the default ratios in diskgroup data if not specified by the user
        _rc = self.mCalculateNewDgSizes(_options, _diskgroupData, _cur_dg_sizes)
        if _rc:
            ebLogError("** ebCluManageDiskgroup:mClusterDgrpCreate - Could not get diskgroup distribution percentages for %s diskgroup operation"
                % (_options.diskgroupOp))
            return _rc

        # Also update DiskgroupData with sparse related info, cell count and griddisk count in case of rollback
        ebLogInfo("*** ebCluManageDiskgroup:mClusterDgrpDrop - Updating DiskgroupData with sparse related info, cell count and griddisk count for rollback")
        _rc = self.mUpdateDgrpData(_options, _diskgroupData, _sparsedg_name, _cur_dg_sizes[_constantsObj._sparse_dg_rawname], True)
        if _rc:
            ebLogDebug("*** Could not get sparse related information for rollback. Might fail in rollback stage")

        _inparams = {}
        ebLogInfo("*** ebCluManageDiskgroup:mClusterDgrpDrop - Fetching and validating input args")
        _rc = self.mClusterParseInput(_options, _inparams, _diskgroupData)
        
        if _rc == 0:
            _diskgroupData[_constantsObj._diskgroupname_key] = _inparams[_constantsObj._diskgroupname_key]
            _diskgroupData[_constantsObj._diskgrouptype_key] = _inparams[_constantsObj._diskgrouptype_key]
        else:
            ebLogInfo("Returning due to input args related error")
            return _rc

        ebLogInfo("*** ebCluManageDiskgroup:mClusterDgrpDrop - Validating the diskgroup existence in cluster config")
        _cluster = _eBoxCluCtrl.mGetClusters().mGetCluster()
        _cludgroups = _cluster.mGetCluDiskGroups()
        ebLogInfo("*** mClusterDgrpDrop: DG List : %s" % ' '.join(_cludgroups))

        _dgConfig = None

        for _dgid in _cludgroups:
            _dg = _eBoxCluCtrl.mGetStorage().mGetDiskGroupConfig(_dgid)
            _dgName = _dg.mGetDgName()
            if (_dgName == _diskgroupData[_constantsObj._diskgroupname_key]):
                ebLogInfo("*** ebCluManageDiskgroup:mClusterDgrpDrop - Found matching diskgroup %s for dropping" %\
                          (_dgName))
                _dgConfig = _dg
                break


        _step_list = ["Drop_Diskgroup", "Drop_Griddisks", "Check_Diskgroups_Resizable", "Resize_Griddisks_and_Diskgroups", "Complete"]

        _eBoxCluCtrl.mUpdateStatusOEDA(True, _step_list[0], _step_list, "Diskgroup Drop Started")
        ebLogInfo("*** Executing steps required for dropping diskgroup %s" %\
                   (_diskgroupData[_constantsObj._diskgroupname_key]))
        
        _dg = _diskgroupData[_constantsObj._diskgroupname_key]
        ebLogInfo("*** Attempting to drop the diskgroup %s" % (_dg))

        _rollback_stack.append({self.mCreateSparseDg:(_options, _cur_dg_sizes, _diskgroupData)})
        _rc = self.mDropDiskGroup(_options, _dg)
        if _rc:    
            _tempResult = self.mRollback(_rollback_stack)
            return _rc

        _eBoxCluCtrl.mUpdateStatusOEDA(True, _step_list[1], _step_list, "Griddisk Drop Started")

        _rollback_stack.append({self.mCreateSparseGriddisks:(_options, _diskgroupData)})
        _rc = self.mDropGridDisks(_options, _dg, True) #issue force option
        if _rc:
            _tempResult = self.mRollback(_rollback_stack)
            return _rc

        _eBoxCluCtrl.mUpdateStatusOEDA(True, _step_list[2], _step_list, "Calculating new RECO and DATA diskgroup sizes and checking if they are resizable")
        ebLogInfo("*** Checking if the diskgroup are resizable")

        _new_dg_sizes = {}
        _new_dg_sizes[_constantsObj._data_dg_rawname] = 0
        _new_dg_sizes[_constantsObj._reco_dg_rawname] = 0

        _rc = self.mCheckIfDgsResizable(_options, _cur_dg_sizes, _new_dg_sizes, _diskgroupData, True)
        if _rc:
            ebLogError("Could not get the new diskgroup sizes")
            return _rc

        _eBoxCluCtrl.mUpdateStatusOEDA(True, _step_list[3], _step_list, "Resizing of RECO and DATA GridDisk and diskgroups")
        ebLogInfo("*** Resizing RECO and DATA griddisks and diskgroups")

        # We need to compare current and new diskgroup sizes to determine whether to resize dgs first, or the diskgroups first
        _rc = self.mResizeDgAndGriddisks(_options, _datadg_name, _new_dg_sizes[_constantsObj._data_dg_rawname],
            _cur_dg_sizes[_constantsObj._data_dg_rawname], _rollback_stack, _diskgroupData, True)
        if _rc == 0:
            _rc = self.mResizeDgAndGriddisks(_options, _recodg_name, _new_dg_sizes[_constantsObj._reco_dg_rawname],
                _cur_dg_sizes[_constantsObj._reco_dg_rawname], _rollback_stack, _diskgroupData, True)

        ebLogInfo("*** Resizing of DiskGroup and Griddisks completed; Checking rebalancing")
        _rollback_stack.append({self.mEnsureDgsRebalanced:(_options, None, _diskgroupData)})
        _rc = self.mEnsureDgsRebalanced(_options, None, _diskgroupData)
        if _rc:
            _tempResult = self.mRollback(_rollback_stack)
            return _rc
        
        ebLogInfo("*** DGs rebalanced; Checking if DGs are correctly resized")
        _rollback_stack.append({self.mValidateDgsPostRebalance:(_options, None, None, _cur_dg_sizes, _diskgroupData)})
        _rc = self.mValidateDgsPostRebalance(_options, None, None, _new_dg_sizes, _diskgroupData)
        if _rc:
            _tempResult = self.mRollback(_rollback_stack)
            return _rc

        _eBoxCluCtrl.mUpdateStatusOEDA(True, _step_list[4], _step_list, "Complete")

        ebLogInfo("ebCluManageDiskgroup:mClusterDgrpDrop - DiskgroupData variable is %s" % (_diskgroupData))

        ebLogInfo("*** ebCluManageDiskgroup:mClusterDgrpDrop for delete sparse <<<")
        return _rc

    # end

    # Method to update DiskgroupData with sparse related info, cell count and griddisk count for sparse creation or deletion
    def mUpdateDgrpData(self, aOptions, aDiskgroupData, aDgName, aCurDgSize, aDeleteSparse=False):

        ebLogInfo("*** ebCluManageDiskgroup:mUpdateDgrpData >>>")
        _options = aOptions
        if aDiskgroupData is None:
            _diskgroupData = self.mGetDiskGroupOperationData()
        else:
            _diskgroupData = aDiskgroupData
        # Get the cluctrl handle to fetch current details
        _eBoxCluCtrl = self.mGetEbox()
        # Get the constants object for use in the scope of this function
        _constantsObj = self.mGetConstantsObj()
        # Get the dbaasobj handle for dbaasapi calls and handling DomU commands/output
        _dbaasObj = self.mGetDbaasObj()
         
        _dgName = aDgName
        _curDgSize = aCurDgSize
        # To check whether we are dropping sparse or not
        _delete_sparse = aDeleteSparse
        
        if _dgName is None or _curDgSize is None:
            return self.mRecordError(gDiskgroupError['MissingArgs'], "*** aDgName and aCurDgSize combination mandatory. One or both params are missing")

        _fgrp_prop_dict = {} 
         
        _cell_vs_griddisks_map = {}
        _dgrp_properties = []
        _dgrp_properties.append(_constantsObj._propkey_failgroup)
        _rc = 0
        # Get failgroups and filter celldisks for it for a given diskgroup
        _rc = self.mClusterDgrpInfo2(_options, _dgName, _dgrp_properties)
        if _rc != 0:
            return self.mRecordError(gDiskgroupError['ErrorFetchingDetails'], "*** Could not\
              fetch info for diskgroup " + _dgName)
        # Read the INFO file containing the storage property value
        # It should be ready and populated as mClusterDgrpInfo2 above is a blocking call
        _infoobj = _dbaasObj.mReadStatusFromDomU(_options, self.mGetLastDomUused(), self.mGetOutJson())
        # Get failgroups for the given DG
        _rc = self.mValidateAndGetFailgroupDetails(_infoobj, _dgName, _constantsObj, _fgrp_prop_dict)
        
        if _fgrp_prop_dict is None:
            _rc = self.mRecordError(gDiskgroupError['MissingFgrpPropDict'], "*** Fail to fetch\
                                              diskgroup property " )
        if _rc == 0:
            _rc = self._extract_cell_vs_griddisks_map(_dgName, _fgrp_prop_dict, _cell_vs_griddisks_map)
            ## Save the celldisk type (harddisk or flashdisk)
            _one_of_the_griddisks = _cell_vs_griddisks_map[(list(_cell_vs_griddisks_map.keys())[0])][0]
            _pattern = re.compile("^(FD)_0[0-1].*")
            if _pattern.match(_one_of_the_griddisks):
                _diskgroupData[_constantsObj._celldisk_type] = "flashdisk"
            else:
                _diskgroupData[_constantsObj._celldisk_type] = "harddisk"

        if _rc != 0:    # Issue at some point above while parsing info
            return self.mRecordError(gDiskgroupError['ErrorReadingPayload'], "*** Could not read\
             info output payload for one or more diskgroups")
        _cell_list = []
        _dg_griddisks_count = 0
        for _cell_name in sorted (_cell_vs_griddisks_map.keys()):
            ebLogInfo("mResizeGriddisks: Cell Name : %s" % _cell_name)
            if len(_cell_vs_griddisks_map[_cell_name]) > 1:
                _dg_griddisks_count = len(_cell_vs_griddisks_map[_cell_name])
                ebLogInfo("mResizeGriddisks: Number of grid disks in a cell = %d" % _dg_griddisks_count)
                _cell_list.append(_cell_name.lower())

        _cell_count = len(_cell_list)
        if _dg_griddisks_count == 0:
            ebLogInfo("mResizeGriddisks: Failed to count number of grid disks.")
            return self.mRecordError(gDiskgroupError['ErrorFetchingDetails'], "*** Could not\
                                                        fetch info for diskgroup. Failed to count number of diskgroups")

        _diskgroupData["griddisk_count"] = _dg_griddisks_count
        _diskgroupData["cell_count"] = _cell_count

        

        # We will need this only for rollback while running rollback in drop sparse diskgroup
        if _delete_sparse:
            # Convert sparse virtual size to physical size
            _sparse_size = _curDgSize/(_constantsObj._sparse_vsize_factor)

            ebLogDebug("*** DG Size : %s, Cell Count : %s, Griddisk Count : %s" %(_sparse_size, _cell_count, _dg_griddisks_count))
            _sparse_slice_size =  _sparse_size/(_cell_count * _dg_griddisks_count)
            _diskgroupData["sparse_size"] = _sparse_size
            _diskgroupData["sparse_slice_size"] = _sparse_slice_size

        else:
            ## Save sparse slice size too while we have cell and griddisk count
            _sparse_dg = _diskgroupData[_constantsObj._sparse_dg_rawname]
            _sparse_size = _diskgroupData["sparse_size"]
            _sparse_slice_size = _sparse_size / (_cell_count * _dg_griddisks_count)
            _sparse_slice_size = int(_sparse_slice_size / 16) * 16
            _diskgroupData["sparse_slice_size"] = _sparse_slice_size
            
            ebLogInfo("New slice size for diskgroup %s with absolute size of %s, cell count %s and griddisk \
            count %s is %s" %(_sparse_dg, str(_sparse_size), str(_cell_count), str(_dg_griddisks_count), str(_sparse_slice_size)))

        ebLogInfo("*** ebCluManageDiskgroup:mUpdateDgrpData <<<")

        return _rc

    # end
        
    # Method to Drop Grid Disks
    def mDropGridDisks(self, aOptions, aGridDiskPrefix, aForce=False):
        
        ebLogInfo("*** ebCluManageDiskgroup:mDropGridDisks >>>")
        _force = ''
        if aForce:
            _force= 'force'
        _cellcli_base_dropcmd = f"cellcli -e drop griddisk all prefix={aGridDiskPrefix} {_force}"
        # Get the cluctrl handle to fetch current details
        _eBoxCluCtrl = self.mGetEbox()
        _cell_list = _eBoxCluCtrl.mReturnCellNodes()
        for _cell_name in sorted(_cell_list.keys()):
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_cell_name)
            ebLogVerbose("*** Executing the command - %s" % _cellcli_base_dropcmd)
            _node.mExecuteCmdLog(_cellcli_base_dropcmd)
            if _node.mGetCmdExitStatus():
                return self.mRecordError(gDiskgroupError['GDDropFailed'],\
                                         "*** mExecuteCmd Failed " + _node.mGetHostname() + \
                                         ":" + _cellcli_base_dropcmd)
            _node.mDisconnect()
        ebLogInfo("*** ebCluManageDiskgroup:mDropGridDisks <<<")
        return 0
            
    # end    

    def mCheckIfDgsResizable(self, aOptions, aCurrentDgSizes, aNewDgSizesDict, aDiskgroupData=None, aDeleteSparse=False):
        
        ebLogInfo("*** ebCluManageDiskgroup:mCheckIfDgsResizable >>>")
        _options = aOptions
        _new_dg_sizes_dict = aNewDgSizesDict
        
        if aDiskgroupData is None:
            _diskgroupData = self.mGetDiskGroupOperationData()
        else:
            _diskgroupData = aDiskgroupData
        
        _delete_sparse = aDeleteSparse
            
        # Get the cluctrl handle to fetch current details
        _eBoxCluCtrl = self.mGetEbox()
        # Get the dbaasobj handle for dbaasapi calls and handling DomU commands/output
        _dbaasObj = self.mGetDbaasObj()
        # Get the constants object for use in the scope of this function
        _constantsObj = self.mGetConstantsObj()
        
        # Save the list of all diskgroups in the cluster
        _cluster = _eBoxCluCtrl.mGetClusters().mGetCluster()
        _cludgroups = _cluster.mGetCluDiskGroups()
        
        _data_dg = None
        _reco_dg = None
        
        for _dgid in _cludgroups:
            if _data_dg is not None and _reco_dg is not None:
                    break
            _dg = _eBoxCluCtrl.mGetStorage().mGetDiskGroupConfig(_dgid)
            _dg_type = _dg.mGetDiskGroupType().lower()
            if _dg_type == _constantsObj._data_dg_type_str:
                _data_dg = _dg
            if _dg_type == _constantsObj._reco_dg_type_str:
                _reco_dg = _dg

        if _data_dg is None:
            return self.mRecordError(gDiskgroupError['DgDoesNotExist'], _constantsObj._data_dg_prefix)
        if _reco_dg is None:
            return self.mRecordError(gDiskgroupError['DgDoesNotExist'], _constantsObj._reco_dg_prefix)
            
        _currentDgSizes = aCurrentDgSizes
        _datadg_name = _data_dg.mGetDgName()
        _datadg_size = _currentDgSizes[_constantsObj._data_dg_rawname] / 1024 # Size in GB
        _datadg_sizeG = str(_datadg_size) + "G"
        
        _recodg_name = _reco_dg.mGetDgName()
        _recodg_size = _currentDgSizes[_constantsObj._reco_dg_rawname] / 1024 # Size in GB
        _recodg_sizeG = str(_recodg_size) + "G"

        ebLogInfo("Current sizes of %s and %s diskgroups are %s and %s, respectively"
                   %(_datadg_name, _recodg_name, _datadg_sizeG, _recodg_sizeG))
        
        _diskgroupData[_constantsObj._data_dg_rawname] = _datadg_name
        _diskgroupData[_constantsObj._reco_dg_rawname] = _recodg_name  
        
        _data_total_mb = _currentDgSizes[_constantsObj._data_dg_rawname]
        _reco_total_mb = _currentDgSizes[_constantsObj._reco_dg_rawname]

        _new_sparse_size = 0
        _datadg_new_size = _diskgroupData["datadg_new_size"]
        _recodg_new_size = _diskgroupData["recodg_new_size"]
        
        _stor_prop_dict = {}
        _rc = 0

        
        # Get both DATA and RECO Diskgroup properties to check if DGs are re-sizable
        _rc = self.mCheckIfDgResizable(_options, _datadg_name, _datadg_new_size, None, _new_dg_sizes_dict, _diskgroupData)
        if _rc != 0:
            return _rc
        
        _rc = self.mCheckIfDgResizable(_options, _recodg_name, _recodg_new_size, None, _new_dg_sizes_dict, _diskgroupData)
        if _rc != 0:
            return _rc
        
        if not _delete_sparse:
            _new_sparse_size = _diskgroupData["sparsedg_new_size"]

        # Let's ensure new sizes are at the closest 16 MB boundary since the cell will
        # round down to this:
        _new_dg_sizes_dict[_constantsObj._data_dg_rawname] = math.floor(_datadg_new_size / 16) * 16
        _new_dg_sizes_dict[_constantsObj._reco_dg_rawname] = math.floor(_recodg_new_size / 16) * 16

        if not _delete_sparse:
            _new_sparse_size = math.floor(_new_sparse_size / 16) * 16
            _new_dg_sizes_dict[_constantsObj._sparse_dg_rawname] = _new_sparse_size
            _diskgroupData["sparse_size"] = _new_sparse_size

        ebLogInfo("ebCluManageDiskgroup:mCheckIfDgsResizable - The new sizes are coming out to be %s" % (_new_dg_sizes_dict))

        ebLogInfo("*** ebCluManageDiskgroup:mCheckIfDgsResizable <<<")
        _diskgroupData[_constantsObj._sparse_dg_rawname] = _datadg_name.replace\
                            (_constantsObj._data_dg_prefix, _constantsObj._sparse_dg_prefix, 1)

        return _rc
        
    # end

    #Method to check if all diskgroups are resizable
    def mCheckIfDgResizableAll(self, aOptions, aDGMap):
    
        ebLogInfo("*** ebCluManageDiskgroup:mCheckIfDgResizableAll >>>")
        _options = aOptions
        _dgMap = aDGMap
        _rc = 0
        _precheck_dict = {"currentMB": 0, "osMB": 0, "newMB": 0}

        for key in _dgMap:
            value = _dgMap[key]
            if value.get("DG_NAME"):
                _rc = self.mCheckIfDgResizable(_options,value["DG_NAME"], int(value["DG_NEWSIZE"]) * 1024, aPrecheckDict=_precheck_dict)
                if _rc !=0 :
                    ebLogError("Diskgroup %s resizable test failed" %(value["DG_NAME"]))
                    return _rc

        _rc = self.mPrecheckDgSizeAvailableCells(_precheck_dict)
        ebLogInfo("*** ebCluManageDiskgroup:mCheckIfDgsResizableAll <<<")
        return _rc

    # end

    def mPrecheckDgSizeAvailableCells(self, aPrecheckDict):
        """
        Precheck for checking if the cells have available capacity for resize
        """
        _rc = 0
        _precheck_dict = aPrecheckDict
        _newMB = _precheck_dict["newMB"]
        _currentMB = _precheck_dict["currentMB"]
        _osMB = _precheck_dict["osMB"]
        _eBox = self.mGetEbox()
        if _eBox.mCheckConfigOption('precheck_cell_disk_free_space', "True") and _newMB > _currentMB:
            _free_space_output_MB = self.mCalculateFreeSpaceCelldisk()
            _cell_disk_list = self.mGetCelldisks()
            if _free_space_output_MB is not None and _cell_disk_list is not None:
                # The below sizes are in MB
                _cell_disk_count = len(_cell_disk_list)
                _cell_count = len(_eBox.mReturnCellNodes())
                _current_dg_slice =  _currentMB/(_cell_count * _cell_disk_count)
                if _osMB:
                    _current_dg_slice =  _osMB
                _current_dg_slice = math.floor(_current_dg_slice / 16) * 16
                _new_dg_slice =  _newMB/(_cell_count * _cell_disk_count)
                _new_dg_slice = math.floor(_new_dg_slice / 16) * 16
                if (_new_dg_slice - _current_dg_slice) > _free_space_output_MB:
                    _msg = f"The free storage - {_free_space_output_MB} MB on each cell disk is less than the requested storage. "\
                           f"The current slice size for each grid disk is {_current_dg_slice} and requested slice size for "\
                           f"each grid disk is {_new_dg_slice}. Please retry the resize operation within the free space available "\
                            "on cells."
                    ebLogError(_msg)
                    _rc = 1
                else:
                    ebLogInfo(f"Precheck passed for free space check on cell disk. Current DG slice size is {_current_dg_slice} MB."\
                              f" New DG slice size is {_new_dg_slice} MB. Free space on cell disk is {_free_space_output_MB} MB.")
        return _rc

    #Method to check if all diskgroups resize is permitted for the given value
    def mCheckIfSizeChangePermitted(self, aOptions, aDGMap):
        ebLogInfo("*** ebCluManageDiskgroup:mCheckIfSizeChangePermitted >>>")
        # Get the constants object for use in the scope of this function
        _constantsObj = self.mGetConstantsObj()
        _options = aOptions
        _dgMap = aDGMap
        _rc = 0
        _dg_newsize = 0
        _dg_currsize = 0
        for key in _dgMap:
            value = _dgMap[key]
            if value["DG_NAME"] is not None:
                 _dg_newsize += int(value["DG_NEWSIZE"]) * 1024
                 _dg_currsize += self.mUtilGetDiskgroupSize(_options, value["DG_NAME"], _constantsObj)
        _diff_inMB = abs(_dg_newsize - _dg_currsize)
        _percentage = 100 * float(_diff_inMB)/float(_dg_currsize)
        if int(_percentage) < 2:
            _rc = self.mRecordError(gDiskgroupError['DgSizeChangeNotPermitted'],
                               "Disk Groups Size Change Not Permitted")
        ebLogInfo("*** ebCluManageDiskgroup:mCheckIfSizeChangePermitted <<<")
        return _rc

    # end
    
    # Internal Method to resize the DATA and RECO DGs individually for creating SPARSE 
    def mResizeDg(self, aOptions, aDgName, aNewDgSize, aDiskgroupData=None, aDeleteSparse=False):
        
        ebLogInfo("*** ebCluManageDiskgroup:mResizeDg >>>")
        _options = aOptions

        if aDiskgroupData is None:
            _diskgroupData = self.mGetDiskGroupOperationData()
        else:
            _diskgroupData = aDiskgroupData
        # Get the constants object for use in the scope of this function
        _constantsObj = self.mGetConstantsObj()
        # Get the dbaasobj handle for dbaasapi calls and handling DomU commands/output
        _dbaasObj = self.mGetDbaasObj()

        # Which diskgroup to resize
        _dg_name = aDgName
        _delete_sparse = aDeleteSparse

        ebLogInfo("*** ebCluManageDiskgroup:mResizeDg - Resizing %s diskgroup" % (_dg_name))
        _new_dg_size = int(aNewDgSize)
                
        _data_dg = _diskgroupData[_constantsObj._data_dg_rawname]
        _reco_dg = _diskgroupData[_constantsObj._reco_dg_rawname]

        # Get the cluctrl handle to fetch current details
        _eBoxCluCtrl = self.mGetEbox()
        
        def _resizeDg(aOptions, aConstantsObj, aDiskgroupData, aDgName, aDgSliceSize, aDgSize):
            
            ebLogInfo("*** ebCluManageDiskgroup:mResizeDg:_resizeDG >>>")
            _options = aOptions
            _constantsObj = aConstantsObj
            _diskgroupData = aDiskgroupData
            
            _dg = aDgName
            _size = aDgSliceSize
            _total_size_in_GB = int(aDgSize/1024)
            _dg_slice_size_GB  = int(_size/1024)
            
            _injson = {}
            _injson[_constantsObj._dbaasapi_object_key] = _constantsObj._dbaasapi_object_value
            _injson[_constantsObj._operation_key] = _constantsObj._operation_value
            _injson[_constantsObj._params_key] = {}
            _injson[_constantsObj._params_key][_constantsObj._dbname_key] = _constantsObj._dbname_value
            _injson[_constantsObj._params_key][_constantsObj._diskgroupname_key] = _dg
            _injson[_constantsObj._flags_key] = ""
            if (_constantsObj._rebalancepower_key in _diskgroupData and _diskgroupData[_constantsObj._rebalancepower_key]):
                    _injson[_constantsObj._rebalancepower_key] = _diskgroupData[_constantsObj._rebalancepower_key]
            
            _injson[_constantsObj._action_key] = "resize"
            _injson[_constantsObj._params_key][_constantsObj._newsizeMB_key] = int(_size)

            _rc = self.mHandleDbaasapiSynchronousCall(_options, _injson, True)
            ebLogInfo("*** ebCluManageDiskgroup:mResizeDg:_resizeDG <<<")
            if _rc == 0:
                # Update xml file
                _cluster = _eBoxCluCtrl.mGetClusters().mGetCluster()
                _cludgroups = _cluster.mGetCluDiskGroups()
                for _dgid in _cludgroups:
                    ebLogInfo("*** Working on Diskgroup ID %s" %(_dgid))
                    _dgConfig = _eBoxCluCtrl.mGetStorage().mGetDiskGroupConfig(_dgid)
                    if _dgConfig.mGetDgName() == _dg:
                        if _dg.startswith(_constantsObj._sparse_dg_prefix):
                            _dgConfig.mSetSparseVirtualSize(_dg_slice_size_GB * _constantsObj._sparse_vsize_factor)
                        _dgConfig.mSetSliceSize(_dg_slice_size_GB)
                        _dgConfig.mSetDiskGroupSize(_total_size_in_GB)
                        # Remove the old config and add new one
                        _eBoxCluCtrl.mGetStorage().mRemoveDiskGroupConfig(_dgid)
                        _eBoxCluCtrl.mGetStorage().mAddDiskGroupConfig(_dgConfig)
                        break

                # Patch XM Cluster Configuration (note: this also write/create the new __patchconfig file)
                _eBoxCluCtrl.mSaveXMLClusterConfiguration()
                return _rc
            
            return self.mRecordError(gDiskgroupError['NonModifiable'], "*** Diskgroup %s could\
             not be resized to %s M" %(_dg, _size))
        
        # end resizeDg       
        
        _cell_count = _diskgroupData["cell_count"]
        _griddisk_count = _diskgroupData["griddisk_count"]

        
        _new_dg_slice = _new_dg_size / (_cell_count * _griddisk_count)
        _new_dg_slice = int(_new_dg_slice / 16) * 16  ## Round to multiple of 16
        _new_dg_size = int(_new_dg_size)
        
        ebLogInfo("*** New slice size for diskgroup %s with absolute size of %s, cell count %s and griddisk \
        count %s is %s" %(_dg_name, str(_new_dg_size), str(_cell_count), str(_griddisk_count), str(_new_dg_slice)))

        _rc = _resizeDg(_options, _constantsObj, _diskgroupData, _dg_name, _new_dg_slice, _new_dg_size)
        if _rc:
            ebLogError("*** ebCluManageDiskgroup:mResizeDg - Resizing of %s dg failed" % (_dg_name))
            return _rc

        else:
            ebLogInfo("*** ebCluManageDiskgroup:mResizeDg - Resizing of %s diskgroup not Supported" % (_dg_name))

        ebLogInfo("*** ebCluManageDiskgroup:mResizeDg <<<")
        return _rc
    # end
    
    # Internal method to check if the rebalance operation is finished for a Diskgroup
    def mEnsureDgsRebalanced(self, aOptions, aDg=None, aDiskgroupData=None):
        
        ebLogInfo("*** ebCluManageDiskgroup:mEnsureDgsRebalanced >>>")
        _options = aOptions
        _dg = aDg

        if aDiskgroupData is None:
            _diskgroupData = self.mGetDiskGroupOperationData()
        else:
            _diskgroupData = aDiskgroupData
        # Get the constants object for use in the scope of this function
        _constantsObj = self.mGetConstantsObj()
        
        if _dg is None:
            _data_dg = _diskgroupData[_constantsObj._data_dg_rawname]
            _reco_dg = _diskgroupData[_constantsObj._reco_dg_rawname]
        
        _rc = 0
        if _dg is None:
            _rc = self.mWaitUntilDgRebalanced(_options, _data_dg, _constantsObj)
            if _rc == 0:
                _rc = self.mWaitUntilDgRebalanced(_options, _reco_dg, _constantsObj)

        else:
            _rc = self.mWaitUntilDgRebalanced(_options, _dg, _constantsObj)
        
        ebLogInfo("*** ebCluManageDiskgroup:mEnsureDgsRebalanced <<<")
        return _rc            
    
    # end

    # Internal method to validate the size of a Diskgroup post resize
    def mValidateDgsPostRebalance(self, aOptions, aDg=None, aDgSize=None, aNewDgSizesDict=None, aDiskgroupData=None):
        
        ebLogInfo("*** ebCluManageDiskgroup:mValidateDgsPostRebalance >>>")
        _options = aOptions
        
        if aDiskgroupData is None:
            _diskgroupData = self.mGetDiskGroupOperationData()
        else:
            _diskgroupData = aDiskgroupData
            
        # Get the cluctrl handle to fetch current details
        _eBoxCluCtrl = self.mGetEbox()
        # Get the dbaasobj handle for dbaasapi calls and handling DomU commands/output
        _dbaasObj = self.mGetDbaasObj()
        # Get the constants object for use in the scope of this function
        _constantsObj = self.mGetConstantsObj()
        
        _dgName = aDg
        _dgSize = aDgSize
        _newDgSizesDict = aNewDgSizesDict
        
        if _dgName is None and _dgSize is None and _newDgSizesDict is None:
            return self.mRecordError(gDiskgroupError['MissingArgs'], "*** One of\
             'aDg/aDgSize combination' or 'aNewDgSizesDict' is mandatory")
        
        _dg_setsize = 0
        _new_dg_size = 0
        if _newDgSizesDict is not None:
            _new_data_size = _newDgSizesDict[_constantsObj._data_dg_rawname]
            _new_reco_size = _newDgSizesDict[_constantsObj._reco_dg_rawname]
            _new_dg_size = _new_data_size
        
            _data_dg = _diskgroupData[_constantsObj._data_dg_rawname]
            _reco_dg = _diskgroupData[_constantsObj._reco_dg_rawname]
            _dgName = _data_dg
        
            _data_dg_setsize = self.mUtilGetDiskgroupSize(_options, _data_dg, _constantsObj)
            _dg_setsize = _data_dg_setsize
        else:
            _new_dg_size = _dgSize
            _dg_setsize = self.mUtilGetDiskgroupSize(_options, _dgName, _constantsObj)
            
        if _dg_setsize == -1:
            return self.mRecordError(gDiskgroupError['InvalidPropValue'], "*** Invalid size of\
             diskgroup " + _dgName)
        else:
            if self.isDgResized(_dg_setsize, _new_dg_size):
                ebLogInfo("%s diskgroup has been successfully resized to %s M" %(_dgName, _dg_setsize))
                
                if _newDgSizesDict is not None and _new_reco_size != 0:
                    _reco_dg_setsize = self.mUtilGetDiskgroupSize(_options, _reco_dg, _constantsObj)
                    
                    if _reco_dg_setsize == -1:
                        return self.mRecordError(gDiskgroupError['InvalidPropValue'], "*** Invalid\
                         size of diskgroup " + _reco_dg)
                    else:
                        if self.isDgResized(_reco_dg_setsize, _new_reco_size):
                            ebLogInfo("%s diskgroup has been successfully resized to %s M" %\
                                      (_dgName, _reco_dg_setsize))
                        else:
                            ebLogInfo('ebCluManageDiskgroup:mValidateDgsPostRebalance: _reco_dg_setsize = %f, _new_reco_size = %f' % (_reco_dg_setsize, _new_reco_size))
                            return self.mRecordError(gDiskgroupError['InvalidPropValue'],\
                                                      "*** Invalid size of diskgroup " + _reco_dg)
            else:
                ebLogInfo('ebCluManageDiskgroup:mValidateDgsPostRebalance: _dg_setsize = %f, _new_dg_size = %f' % (_dg_setsize, _new_dg_size))
                return self.mRecordError(gDiskgroupError['InvalidPropValue'],\
                                          "*** Invalid size of diskgroup " + _dgName)
        
        ebLogInfo("*** ebCluManageDiskgroup:mValidateDgsPostRebalance <<<")
        return 0
        
    # end

    def mGetCelldisks(self):
        """
        Get list of cell disks from cells
        """
        try:
            _eBox = self.mGetEbox()
            _cell_list = _eBox.mReturnCellNodes()
            _cmdstr = 'cellcli -e LIST CELLDISK WHERE name LIKE \\"CD_.*\\" attributes name;'
            _cell_name_list = list(_cell_list.keys())
            _cell_disk_list = []
            if len(_cell_name_list) > 0:
                _cell_name = _cell_name_list[0]
            else:
                return None
            with connect_to_host(_cell_name, get_gcontext()) as _node:
                ebLogInfo(f"*** Executing the command - {_cmdstr} on cell - {_cell_name}.")
                _output, _error = None, None
                _in, _out, _err = _node.mExecuteCmd(_cmdstr)
                if _out:
                    _output = _out.readlines()
                if _err:
                    _error = _err.read()
                if _node.mGetCmdExitStatus() != 0:
                    ebLogError(f'Error while running cellcli command on cell. *** CMD_OUT: {_output}, ERROR: {_error}.')
                    raise ExacloudRuntimeError(0x0825, 0xA, f'mExecuteCmd Failed on {_cell_name}, with cmd: {_cmdstr}')
                if _output:
                    ebLogTrace("*** cellcli Output - %s" % _output)
                    for _cell_disk in _output:
                        _slice_output_for_celldisk = _cell_disk.strip().split()
                        _slice_name = _slice_output_for_celldisk[0]
                        _cell_disk_list.append(_slice_name)
                else:
                    ebLogError(f'Error while running cellcli command on cell - None output received. *** ERROR: {_error}.')
                    raise ExacloudRuntimeError(0x0825, 0xA, f'mExecuteCmd Failed on {_cell_name}, with cmd: {_cmdstr}')
        except Exception as ex:
            ebLogWarn(f"There was an error while checking for cell disks. Skipping precheck. Error: {ex}")
            return None
        return _cell_disk_list
    
    def mCheckGriddiskSize(self, aDg, aNewDgSize):
        """
        Get the size of Griddisks of specified Diskgroup and
        compare it with the expected new Griddisk slice to
        know if the griddisks are already resized and celldisk
        freespace check could be skipped.
        """
        _rc = 0
        _dgName = aDg
        _newMB = aNewDgSize

        try:
            _eBox = self.mGetEbox()
            _cell_list = _eBox.mReturnCellNodes()
            _cell_disk_list = self.mGetCelldisks()
            _cell_count = len(_cell_list)
            _cell_disk_count = len(_cell_disk_list)

            if _cell_count == 0:
                _rc = None
                return _rc
            
            _cell_name = list(_cell_list.keys())[0]
            _dg_slice = int(math.floor(_newMB / (_cell_count * _cell_disk_count)) / 16) * 16
            ebLogInfo(f"Expected dg_slice size for the new dg size is : {_dg_slice}") 
            _cmdstr = f'cellcli -e list griddisk attributes size where asmDiskGroupName = {_dgName};'
            with connect_to_host(_cell_name, get_gcontext()) as _node:
                ebLogInfo(f"*** Executing the command - {_cmdstr} on cell - {_cell_name}.")
                _output, _error = None, None
                _in, _out, _err = _node.mExecuteCmd(_cmdstr)
                if _out:
                    _output = _out.readlines()
                if _err:
                    _error = _err.read()
                if _node.mGetCmdExitStatus() != 0:
                    ebLogError(f'Error while running cellcli command on cell. *** CMD_OUT: {_output}, ERROR: {_error}.')
                    raise ExacloudRuntimeError(0x0825, 0xA, f'mExecuteCmd Failed on {_cell_name}, with cmd: {_cmdstr}')
                if _output:
                    _unit_factor_mapping = {'M': 1, 'G': 1024, 'T': 1048576}
                    for _o in _output:
                        _values = _o.strip().split()
                        if len(_values) < 1:
                            continue
                        curr_griddisk_size = float(_values[0][:-1]) * _unit_factor_mapping[_values[0][-1]]
                        ebLogInfo(f"Existing griddisk size is {curr_griddisk_size} for diskgroup {_dgName}")
                        if curr_griddisk_size >= _dg_slice:
                            _rc = curr_griddisk_size
                        break
        except Exception as ex:
            ebLogWarn(f"There was an error while checking for free space in griddisks. Skipping precheck. Error: {ex}")
            return None
        return _rc

    def mCalculateFreeSpaceCelldisk(self):
        """
        Get free space for a cell disk from cells
        """
        try:
            _eBox = self.mGetEbox()
            _cell_list = _eBox.mReturnCellNodes()
            _cmdstr = 'cellcli -e LIST CELLDISK WHERE name LIKE \\"CD_.*\\" attributes name,size,freespace;'
            _total_space_output_MB = 0.0
            _free_space_output_MB = 0.0
            _cell_name_list = list(_cell_list.keys())
            if len(_cell_name_list) > 0:
                _cell_name = _cell_name_list[0]
            else:
                return None
            with connect_to_host(_cell_name, get_gcontext()) as _node:
                ebLogInfo(f"*** Executing the command - {_cmdstr} on cell - {_cell_name}.")
                _output, _error = None, None
                _in, _out, _err = _node.mExecuteCmd(_cmdstr)
                if _out:
                    _output = _out.readlines()
                if _err:
                    _error = _err.read()
                if _node.mGetCmdExitStatus() != 0:
                    ebLogError(f'Error while running cellcli command on cell. *** CMD_OUT: {_output}, ERROR: {_error}.')
                    raise ExacloudRuntimeError(0x0825, 0xA, f'mExecuteCmd Failed on {_cell_name}, with cmd: {_cmdstr}')
                if _output:
                    ebLogTrace("*** cellcli Output - %s" % _output)
                    _slice_size = 0.0
                    _free_space_slice_size = 0.0
                    for _cell_disk in _output:
                        _slice_output_for_celldisk = _cell_disk.strip().split()
                        _slice_name = _slice_output_for_celldisk[0]
                        _slice_size = _slice_output_for_celldisk[1]
                        _free_space_slice_size = _slice_output_for_celldisk[2]
                        # 1024*1024 = 1048576
                        _unit_factor_mapping = {'M': '1', 'G': '1024', 'T': '1048576'}
                        _total_space_output_MB = (float(_slice_size[:-1]) * float(_unit_factor_mapping[_slice_size[-1]]))
                        _free_space_output_MB = (float(_free_space_slice_size[:-1]) * float(_unit_factor_mapping[_free_space_slice_size[-1]]))
                        ebLogInfo(f"*** Obtained free space as {_free_space_output_MB} MB and total space as {_total_space_output_MB} MB "\
                                  f"for cell disk {_slice_name} on cell {_cell_name}.")
                        # Need only single celldisk slice size
                        break
                else:
                    ebLogError(f'Error while running cellcli command on cell - None output received. *** ERROR: {_error}.')
                    raise ExacloudRuntimeError(0x0825, 0xA, f'mExecuteCmd Failed on {_cell_name}, with cmd: {_cmdstr}')
        except Exception as ex:
            ebLogWarn(f"There was an error while checking for free space on a cell disk. Skipping precheck. Error: {ex}")
            return None
        return _free_space_output_MB

    # Method to resize grid disks
    def mResizeGriddisks(self, aOptions, aDg=None, aNewDgSize=None, aDiskgroupData=None):
        ebLogInfo("*** ebCluManageDiskgroup:mResizeGriddisks >>>") 
        _options = aOptions
        if aDiskgroupData is None:
            _diskgroupData = self.mGetDiskGroupOperationData()
        else:
            _diskgroupData = aDiskgroupData
        # Get the cluctrl handle to fetch current details
        _eBoxCluCtrl = self.mGetEbox()
        # Get the constants object for use in the scope of this function
        _constantsObj = self.mGetConstantsObj()
        # Get the dbaasobj handle for dbaasapi calls and handling DomU commands/output
        _dbaasObj = self.mGetDbaasObj()
         
        _dgName = aDg
        _newDgSize = aNewDgSize
        
        if _dgName is None or _newDgSize is None:
            return self.mRecordError(gDiskgroupError['MissingArgs'], "*** aDg and aNewDgSize combination mandatory")

        _fgrp_prop_dict = {} 
         
        _cell_vs_griddisks_map = {}
        _dgrp_properties = []
        _dgrp_properties.append(_constantsObj._propkey_failgroup)
        _rc = 0
        # Get failgroups and filter celldisks for it for a given diskgroup
        _rc = self.mClusterDgrpInfo2(_options, _dgName, _dgrp_properties)
        if _rc != 0:
            return self.mRecordError(gDiskgroupError['ErrorFetchingDetails'], "*** Could not\
              fetch info for diskgroup " + _dgName)
        # Read the INFO file containing the storage property value
        # It should be ready and populated as mClusterDgrpInfo2 above is a blocking call
        _infoobj = _dbaasObj.mReadStatusFromDomU(_options, self.mGetLastDomUused(), self.mGetOutJson())
        # Get failgroups for the given DG
        _rc = self.mValidateAndGetFailgroupDetails(_infoobj, _dgName, _constantsObj, _fgrp_prop_dict)
        
        if _fgrp_prop_dict is None:
            _rc = self.mRecordError(gDiskgroupError['MissingFgrpPropDict'], "*** Fail to fetch\
                                              diskgroup property for dg " + _dgName)
        if _rc == 0:
            _rc = self._extract_cell_vs_griddisks_map(_dgName, _fgrp_prop_dict, _cell_vs_griddisks_map)
            ## Save the celldisk type (harddisk or flashdisk)
            _one_of_the_griddisks = _cell_vs_griddisks_map[(list(_cell_vs_griddisks_map.keys())[0])][0]
            _pattern = re.compile("^(FD)_0[0-1].*")
            if _pattern.match(_one_of_the_griddisks):
                _diskgroupData[_constantsObj._celldisk_type] = "flashdisk"
            else:
                _diskgroupData[_constantsObj._celldisk_type] = "harddisk"

        if _rc != 0:    # Issue at some point above while parsing info
            return self.mRecordError(gDiskgroupError['ErrorReadingPayload'], "*** Could not read\
             info output payload for one or more diskgroups")
        _cell_list = []
        _cells = _eBoxCluCtrl.mReturnCellNodes().keys()
        _dg_griddisks_count = 0
        for _cell_name in sorted (_cell_vs_griddisks_map.keys()):
            ebLogInfo("mResizeGriddisks: Cell Name : %s" % _cell_name)
            if len(_cell_vs_griddisks_map[_cell_name]) > 1:
                _dg_griddisks_count = len(_cell_vs_griddisks_map[_cell_name])
                ebLogInfo("mResizeGriddisks: Number of grid disks in a cell = %d" % _dg_griddisks_count)
                for _cell in _cells:
                    if _cell_name.lower() == _cell.split('.')[0]:
                        _cell_list.append(_cell)

        _cell_count = len(_cell_list)
        if _dg_griddisks_count == 0:
            ebLogInfo("mResizeGriddisks: Failed to count number of grid disks.")
            return self.mRecordError(gDiskgroupError['ErrorFetchingDetails'], "*** Could not\
                                                                           fetch info for diskgroup " + _dgName)

        ebLogInfo("*** DG name : %s, DG Size : %s, Cell Count : %s, Griddisk Count : %s" %(_dgName, _newDgSize, _cell_count, _dg_griddisks_count))
        _new_dg_slice =  _newDgSize/(_cell_count * _dg_griddisks_count)
        _new_dg_slice = math.floor(_new_dg_slice / 16) * 16
        _cellserver_num = 1
        _cellcli_base_altercmd = "cellcli -e alter griddisk"

        # Validate Grid disks are Online and not in Dropped state before issuing alter disk command
        cluPrecheckReshapeStorage = ebCluStorageReshapePrecheck(self.__ebox)
        cluPrecheckReshapeStorage.mStorageReshapePrecheck(_options, True)

        for _cell_name in sorted(_cell_list):
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_cell_name)
            ebLogInfo('*** Initiating resize of griddisks for diskgroup ' + _dgName+\
                       ' on: '+ _cell_name)

            _cell_shortname = (_cell_name.split('.')[0]).upper()

            ebLogInfo("*** Following griddisks will be altered (resized):")
            ebLogInfo('\n'.join(_cell_vs_griddisks_map[_cell_shortname]))
            for _griddisk in _cell_vs_griddisks_map[_cell_shortname]:
                _gd_resize_cmd = _cellcli_base_altercmd + " " + _dgName + "_" + _griddisk + " "
                _gd_resize_cmd += "size=" + str(_new_dg_slice) + "M"
                if _dgName.startswith(_constantsObj._sparse_dg_prefix):
                    _gd_resize_cmd += ",virtualSize=" + str(_new_dg_slice * _constantsObj._sparse_vsize_factor) + "M"

                ebLogInfo("*** Executing the command - %s" % _gd_resize_cmd)
                _, _o, _e = _node.mExecuteCmd(_gd_resize_cmd)
                _output = str(_o.readlines())
                ebLogInfo("*** GridDisk :Output of cmd:%s is :%s"%(_gd_resize_cmd, str(_output)))
                if _node.mGetCmdExitStatus() or _constantsObj._alter_disk_failure_msg in _output:
                    return self.mRecordError(gDiskgroupError['GDResizeFailed'],\
                                                  "*** mExecuteCmd Failed" + _node.mGetHostname() + \
                                                  ":" + _gd_resize_cmd)
                
            
                ebLogInfo('*** GridDisk : %s on cell %s has been resized to %sM'\
                                   %(_griddisk, _cell_name, _new_dg_slice))
        ebLogInfo("*** ebCluManageDiskgroup:mResizeGriddisks <<<")
        return 0
    # end

    # Internal method to create griddisks for sparse DG
    def mCreateSparseGriddisks(self, aOptions, aDiskgroupData=None):
        
        ebLogInfo("*** ebCluManageDiskgroup:mCreateSparseGriddisks >>>")
        _options = aOptions
        if aDiskgroupData is None:
            _diskgroupData = self.mGetDiskGroupOperationData()
        else:
            _diskgroupData = aDiskgroupData
            
        
        # Get the cluctrl handle to fetch current details
        _eBoxCluCtrl = self.mGetEbox()
        # Get the constants object for use in the scope of this function
        _constantsObj = self.mGetConstantsObj()
        
        _sparse_dg = _diskgroupData[_constantsObj._sparse_dg_rawname]
        _sparse_dg_slice_MB = int(_diskgroupData["sparse_slice_size"])
        _sparse_dg_slice_GB = int(_sparse_dg_slice_MB / 1024)
        _sparse_dg_vSlice_GB =_sparse_dg_slice_GB * _constantsObj._sparse_vsize_factor
        
        _cell_list = _eBoxCluCtrl.mReturnCellNodes()
        
        _cellserver_num = 1
        _cellcli_sparse_gdcreate_cmd = "cellcli -e create griddisk all " +\
                                         _diskgroupData[_constantsObj._celldisk_type] +\
                                          " prefix=" + _sparse_dg +\
                                           ",size= " + str(_sparse_dg_slice_GB) + "G,virtualsize=" +\
                                            str(_sparse_dg_vSlice_GB) + "G"
        
        # begin outer 'for'
        _rollback_flag = False
        _error_code = 0
        for _cell_name in sorted(_cell_list.keys()):
            _node = exaBoxNode(get_gcontext(), Cluctrl = _eBoxCluCtrl)
            _node.mConnect(aHost=_cell_name)
            ebLogInfo('*** Initiating create of griddisks for SPARSE diskgroup ' + _sparse_dg +\
                       ' on: '+ _cell_name)
            
            _node.mExecuteCmdCellcli(_cellcli_sparse_gdcreate_cmd)
            if _node.mGetCmdExitStatus():
                _rollback_flag = True
                _error_code =  self.mRecordError(gDiskgroupError['GDCreateFailed'],\
                                                 "*** mExecuteCmd Failed " + _node.mGetHostname() + \
                                                 ":" + _cellcli_sparse_gdcreate_cmd)
                _node.mDisconnect()
                break
                
            ebLogInfo('*** GridDisks of type %s on cell %s have been created using cmd %s'\
                               %(_diskgroupData[_constantsObj._celldisk_type], _cell_name,\
                                  _cellcli_sparse_gdcreate_cmd)) 
            
            _node.mDisconnect()
            _cellserver_num = _cellserver_num + 1
        
        # end 'for'
        
        # Delete all sparse grid disks if error occurs in creation  
        if _rollback_flag:
            for _cell_name in sorted(_cell_list.keys()):
                _node = exaBoxNode(get_gcontext())
                _node.mConnect(aHost=_cell_name)
                _cellcli_sparse_gddrop_cmd = "cellcli -e drop griddisk all prefix="+aDiskgroupData[_constantsObj._sparse_dg_rawname]
                ebLogInfo('*** Initiating rollback: mCreateSparseGriddisks ' + _sparse_dg +\
                       ' on: '+ _cell_name)
            
                _node.mExecuteCmd(_cellcli_sparse_gddrop_cmd)
                if _node.mGetCmdExitStatus():
                    return self.mRecordError(gDiskgroupError['GDCreateFailed'],\
                                      "*** mExecuteCmd Failed " + _node.mGetHostname() + \
                                      ":" + _cellcli_sparse_gdcreate_cmd)
            
                _node.mDisconnect()
            return _error_code
        
        ebLogInfo("*** ebCluManageDiskgroup:mCreateSparseGriddisks <<<")
        return 0
    
    # end
    
    # Internal method to create sparse DG 
    def mCreateSparseDg(self, aOptions, aNewDgSizesDict, aDiskgroupData=None):
        
        ebLogInfo("*** ebCluManageDiskgroup:mCreateSparseDg >>>")
        _options = aOptions
        
        if aDiskgroupData is None:
            _diskgroupData = self.mGetDiskGroupOperationData()
        else:
            _diskgroupData = aDiskgroupData
        
        # Get the cluctrl handle to fetch current details
        _eBoxCluCtrl = self.mGetEbox()
        # Get the constants object for use in the scope of this function
        _constantsObj = self.mGetConstantsObj()
        # Get the dbaasobj handle for dbaasapi calls and handling DomU commands/output
        _dbaasObj = self.mGetDbaasObj()
        
        _sparse_dg = _diskgroupData[_constantsObj._sparse_dg_rawname]
        _dg_type = _diskgroupData[_constantsObj._diskgrouptype_key]
        
        _injson = {}
        _injson[_constantsObj._dbaasapi_object_key] = _constantsObj._dbaasapi_object_value
        _injson[_constantsObj._operation_key] = _constantsObj._operation_value
        _injson[_constantsObj._action_key] = "create"
        _injson[_constantsObj._params_key] = {}
        _injson[_constantsObj._params_key][_constantsObj._dbname_key] = _constantsObj._dbname_value
        _injson[_constantsObj._params_key][_constantsObj._diskgroupname_key] = _sparse_dg
        _injson[_constantsObj._params_key][_constantsObj._diskgrouptype_key] = _dg_type
        _injson[_constantsObj._flags_key] = ""
                
        _rc = self.mHandleDbaasapiSynchronousCall(_options, _injson, False)
        ebLogTrace("*** ebCluManageDiskgroup:mCreateSparseDg " + \
            f" HandleDbaasAPISync. RC: {_rc}" )
        
        if _rc == 0:
            _sparse_dg_size_MB = int(_diskgroupData["sparse_size"])
            _sparse_dg_size_GB = _sparse_dg_size_MB / 1024
            
            _griddisks_count = int(_diskgroupData["griddisk_count"])
            _cell_count = int(_diskgroupData["cell_count"])
            _sparse_slice_GB = int(_sparse_dg_size_GB / (_griddisks_count *  _cell_count))
            _sparse_dg_size_GB = int(_sparse_dg_size_GB)
            
            _cluster = _eBoxCluCtrl.mGetClusters().mGetCluster()
            _cludgroups = _cluster.mGetCluDiskGroups()
                    
            _data_dg = _diskgroupData[_constantsObj._data_dg_rawname]
            _reco_dg = _diskgroupData[_constantsObj._reco_dg_rawname]
            
            _data_dg_size = int(aNewDgSizesDict[_constantsObj._data_dg_rawname])
            _reco_dg_size = int(aNewDgSizesDict[_constantsObj._reco_dg_rawname])
            
            _data_slice = int(_data_dg_size/(_cell_count * _griddisks_count))
            _reco_slice = int(_reco_dg_size/(_cell_count * _griddisks_count))
            
            for _dgid in _cludgroups:
                ebLogInfo("*** Working on Diskgroup ID %s" %(_dgid))
                _dg = _eBoxCluCtrl.mGetStorage().mGetDiskGroupConfig(_dgid)
                _dg_type = _dg.mGetDiskGroupType().lower()
                if _dg_type == _constantsObj._data_dg_type_str:

                    ## Save the sparse diskgroup config as well since we will modify DATA DG for sure
                    _sparseConfig = copy.deepcopy(_eBoxCluCtrl.mGetStorage().mGetDiskGroupConfig(_dgid))
                    if _constantsObj._data_dg_type_str in _dgid:
                        _sparse_dg_id = _dgid.replace(_constantsObj._data_dg_type_str, _constantsObj._sparse_dg_type_str)
                    else:
                        _sparse_dg_id = _eBoxCluCtrl.mGenerateUUID()
                    _sparseConfig.mReplaceDgId(_sparse_dg_id)
                    _sparseConfig.mReplaceDgName(_sparseConfig.mGetDgName().replace(_constantsObj._data_dg_prefix, _constantsObj._sparse_dg_prefix))
                    _sparseConfig.mSetDiskGroupType(_constantsObj._sparse_dg_type_str)
                    _sparseConfig.mSetSparseDg("true")
                    _sparseConfig.mSetSliceSize(_sparse_slice_GB)
                    _sparseConfig.mSetDiskGroupSize(_sparse_dg_size_GB)
                    _sparseConfig.mSetOCRVote("false")
                    if _eBoxCluCtrl.mGetEnableQuorum():
                        _sparseConfig.mSetQuorumDisk("true")
                    else:
                        _sparseConfig.mSetQuorumDisk("false")
                    _sparseConfig.mSetSparseVirtualSize(_sparse_slice_GB * _constantsObj._sparse_vsize_factor)
                    _eBoxCluCtrl.mGetStorage().mAddDiskGroupConfig(_sparseConfig)
                    _eBoxCluCtrl.mGetClusters().mGetCluster().mAddCluDiskGroupConfig(_sparse_dg_id)

            # Patch XM Cluster Configuration (note: this also write/create the new __patchconfig file)
            _eBoxCluCtrl.mSaveXMLClusterConfiguration()
            ebLogInfo('*** ebCluManageDiskgroup:mCreateSparseDg: Saved patched Cluster Config: ' + _eBoxCluCtrl.mGetPatchConfig())

        else:
            ebLogInfo("*** ebCluManageDiskgroup:mCreateSparseDg Failed.")    
            return 1
        
        ebLogInfo("*** ebCluManageDiskgroup:mCreateSparseDg <<<")    
        return _rc
    # end  
        
    def mGetGridDiskCount(self, _dg_name):
        _dg_griddisks_count = 0
        # Get the constants object for use in the scope of this function
        _constantsObj = self.mGetConstantsObj()
        # Get the dbaasobj handle for dbaasapi calls and handling DomU commands/output
        _dbaasObj = self.mGetDbaasObj()   
        _dg_name_key = _constantsObj._diskgroupname_key
        _inparams = {}

        _dgrp_properties = []
        _dgrp_properties.append(_constantsObj._propkey_failgroup)
        _rc = self.mClusterDgrpInfo2(self.mGetAoptions(), _dg_name, _dgrp_properties)
        if _rc != 0:
            return self.mRecordError(gDiskgroupError['ErrorFetchingDetails'], "*** Could not\
                             fetch info for diskgroup " + _dg_name)

        # Read the INFO file containing the storage property value
        # It should be ready and populated as mClusterDgrpInfo2 above is a blocking call
        _infoobj = _dbaasObj.mReadStatusFromDomU(self.mGetAoptions(), self.mGetLastDomUused(), self.mGetOutJson())
        _dg_fgrp_prop_dict = {}
        # Get failgroups for the given DG
        _rc = self.mValidateAndGetFailgroupDetails(_infoobj, _dg_name, _constantsObj, _dg_fgrp_prop_dict)
        _dg_griddisks_count = 0
        if _rc == 0:
            _cell_vs_griddisks_map = {}
            ebLogInfo(json.dumps(_dg_fgrp_prop_dict, indent=4, sort_keys=True))
            _rc = self._extract_cell_vs_griddisks_map(_dg_name, _dg_fgrp_prop_dict, _cell_vs_griddisks_map)
            if _rc == 0:              
                for _cell_name in sorted (_cell_vs_griddisks_map.keys()):
                    ebLogInfo("mGetGridDiskCount: Cell Name : %s" % _cell_name)
                    if len(_cell_vs_griddisks_map[_cell_name]) > 1:
                        if _dg_griddisks_count == 0:
                            _dg_griddisks_count = len(_cell_vs_griddisks_map[_cell_name])
                            ebLogInfo("*** mGetGridDiskCount: Number of grid disks in a cell = %d" % _dg_griddisks_count)
                            break

        return _dg_griddisks_count
   
 
    # Factory method to perform update actions on a Diskgroup 
    def mDiskgroupUpdate(self, aOptions, aOperation):
        """
        This method is called during Add Cell, Delete Cell, ASM Reshape.
        For Add Cell ExaCS ResizeDiskgroup: Historically this method handled
        all 3 -- resize diskgroup, wait for rebalance, resize griddisks
        As part of 37873380 we split this, and we will ONLY do now 
        resize diskgroup in here. Wait for rebalance and
        Resize griddisks are taken out to their own steps
        """

        _options = aOptions
        # Get the cluctrl handle to fetch current details
        _eBoxCluCtrl = self.mGetEbox()
        # Get the constants object for use in the scope of this function
        _constantsObj = self.mGetConstantsObj()
        # Get the dbaasobj handle for dbaasapi calls and handling DomU commands/output
        _dbaasObj = self.mGetDbaasObj()
        _detail_error = '' 
        _op = aOperation

        # Ref bug 37873380
        # We need to create a flag to detect when we're in ADD CELL
        # in step RESIZ_DGs (shrinkg diskgroups to original
        # sizes). We will only trigger the Resize Diskgroups
        # call and all post-operations like
        # waiting for rebalance, validation and voting disk
        # relocation will be done in subsequent step 
        # to resize/shrinkg the griddisks
        _options_top_level = self.__ebox.mGetArgsOptions()
        _is_add_cell = False
        _is_step_resize_dg = False

        if _options_top_level.jsonconf and 'reshaped_node_subset' in list(_options_top_level.jsonconf.keys()):
            _reshape_config = _options_top_level.jsonconf['reshaped_node_subset']
            if _reshape_config.get('added_cells'):
                _is_add_cell = True

            # Fow now only ADD CELL should modify the behavior
            # of skiping waitForRebalance and GridDisk resize
            if _options_top_level.steplist:
                _step_list = str(_options_top_level.steplist).split(",")
                if "RESIZE_DGS" in _step_list:
                    _is_step_resize_dg = True

        ebLogTrace(f"mDiskgroupUpdate: Detection as 'Add Cell' is: {_is_add_cell}")
        ebLogTrace(f"mDiskgroupUpdate: Detection as 'RESIZE_DGS' is: {_is_step_resize_dg}")

        _diskgroupData = self.mGetDiskGroupOperationData()
        _diskgroupData["Status"] = "Pass"
        _diskgroupData["ErrorCode"] = "0"
        
        _dg_name_key = _constantsObj._diskgroupname_key 

        _inparams = {}
        _rc = self.mClusterParseInput(_options, _inparams)
        
        _info = True
        _vote_disk_relocated = False 
        _newsizeMB = 0
        _dg_name = None
        _dg_fgrp_prop_dict = {}
        _dg_slice = 0
        _clu_utils = ebCluUtils(_eBoxCluCtrl)

        _step = 0

        ebLogInfo("*** mDiskgroupUpdate: Input JSON for diskgroup update operation: ")
        ebLogInfo(json.dumps(_inparams, indent=4, sort_keys=True))
        if _rc != 0:
            _detail_error = "Returning due to input arguments related error"
            ebLogError("*** " + _detail_error)
            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['INVALID_INPUT_PARAMETER'], _detail_error)
            return _rc
        else:
            _dg_name = _inparams[_dg_name_key]
            _dg_cursize = self.mUtilGetDiskgroupSize(_options, _dg_name, _constantsObj)
            step_list = []
            _injson = {}
            _injson[_constantsObj._dbaasapi_object_key] = _constantsObj._dbaasapi_object_value
            _injson[_constantsObj._operation_key] = _constantsObj._operation_value
            _injson[_constantsObj._params_key] = {}
            _injson[_constantsObj._params_key][_constantsObj._dbname_key] = _constantsObj._dbname_value
            _injson[_constantsObj._params_key][_constantsObj._diskgroupname_key] = _dg_name
            _injson[_constantsObj._flags_key] = ""

            if (_constantsObj._rebalancepower_key in _inparams and _inparams[_constantsObj._rebalancepower_key] >= 0):
                    _injson[_constantsObj._params_key][_constantsObj._rebalancepower_key] = _inparams[_constantsObj._rebalancepower_key]
            
            if _op == "ResizeDiskgroup":
                if _dg_cursize == -1:
                    _detail_error = "Invalid size of diskgroup: " + _dg_name
                    _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['INVALID_SIZE_PROVIDED_DG'], _detail_error)
                    return self.mRecordError(gDiskgroupError['InvalidPropValue'], "*** Invalid\
                     size of diskgroup " + _dg_name)
                ### Size returned from ASM is virtual one for sparse diskgroup.
                ### should be converted to physical size before processing
                if _dg_name.startswith(_constantsObj._sparse_dg_prefix):
                    _dg_cursize = int(_dg_cursize / _constantsObj._sparse_vsize_factor)
                
                _injson[_constantsObj._action_key] = "resize"
                _newsizeGB = _inparams[_constantsObj._newsizeGB_key]
                _newsizeMB = int(_newsizeGB) * 1024 
                
                _diskgroupData["SizeMB"] = _dg_cursize
                
                if _newsizeMB == _dg_cursize:
                    ebLogInfo("New size of " + str(_newsizeMB) + "M for " + _dg_name + "\
                     same as its current size. Nothing to do.")
                    return 0
                
                _dgrp_properties = []
                _dgrp_properties.append(_constantsObj._propkey_failgroup)
                _rc = self.mClusterDgrpInfo2(_options, _dg_name, _dgrp_properties)
                if _rc != 0:
                    _detail_error = "Could not fetch info for diskgroup: " + _dg_name
                    _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_FETCHING_DETAILS_DG'], _detail_error)
                    return self.mRecordError(gDiskgroupError['ErrorFetchingDetails'], "*** Could not\
                     fetch info for diskgroup " + _dg_name)
                
                # Read the INFO file containing the storage property value
                # It should be ready and populated as mClusterDgrpInfo2 above is a blocking call
                _infoobj = _dbaasObj.mReadStatusFromDomU(_options, self.mGetLastDomUused(), self.mGetOutJson())
                # Get failgroups for the DATA DG
                _rc = self.mValidateAndGetFailgroupDetails(_infoobj, _dg_name, _constantsObj, _dg_fgrp_prop_dict)
                
                if _rc == 0:
                    _cell_list = []
                    _cell_count = 0
                    _data_cell_vs_griddisks_map = {}
                    ebLogInfo(json.dumps(_dg_fgrp_prop_dict, indent=4, sort_keys=True))
                    _rc = self._extract_cell_vs_griddisks_map(_dg_name, _dg_fgrp_prop_dict, _data_cell_vs_griddisks_map)
                    
                    if _rc == 0:        
                        _dg_griddisks_count = 0
                        
                        for _cell_name in sorted (_data_cell_vs_griddisks_map.keys()): 
                            ebLogInfo("mDiskgroupUpdate: Cell Name : %s" % _cell_name)
                            if len(_data_cell_vs_griddisks_map[_cell_name]) > 1:
                                if _dg_griddisks_count == 0:
                                    _dg_griddisks_count = len(_data_cell_vs_griddisks_map[_cell_name])
                                    ebLogInfo("*** mDiskgroupUpdate: Number of grid disks in a cell = %d" % _dg_griddisks_count)
                                _cell_list.append(_cell_name)
                        
                        _cell_count = len(_cell_list)        
        
                        ebLogInfo("*** mDiskgroupUpdate: Cell List : %s" % ' '.join(_cell_list))
                        if _dg_griddisks_count == 0:
                            _detail_error = "mDiskgroupUpdate: Failed to count number of grid disks."
                            ebLogInfo("*** " + _detail_error) 
                            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_FETCHING_GRIDDISK_COUNT'], _detail_error)
                            return self.mRecordError(gDiskgroupError['ErrorFetchingDetails'], "*** Could not\
                                                               fetch info for diskgroup " + _dg_name)

                        _dg_slice =  _newsizeMB/(_cell_count * _dg_griddisks_count)
                        _dg_slice = int(_dg_slice / 16) * 16  ## Round to multiple of 16
                        _newsizeMB = _dg_slice * (_cell_count * _dg_griddisks_count)
                        if _dg_name.startswith(_constantsObj._sparse_dg_prefix):
                            _injson[_constantsObj._params_key][_constantsObj._newsizeMB_key] = _dg_slice * _constantsObj._sparse_vsize_factor
                        else:
                            _injson[_constantsObj._params_key][_constantsObj._newsizeMB_key] = _dg_slice
                        
            
                        ebLogInfo("*** DG Size : %s, Cell Count : %s, Slice size : %s, Griddisk Count : %s" %(_newsizeMB, _cell_count, _dg_slice, _dg_griddisks_count))
                        ebLogInfo('*** mDiskgroupUpdate: Diskgroup %s resize %s -> %s' % (_dg_name, _dg_cursize, _newsizeMB))
                        if _newsizeMB < _dg_cursize:
                            step_list = ["DgResize", "Rebalance", "SizeValidation", "GdResize", "Complete"]
                        else:
                            # In Add Cell we expect almost always to go down to
                            # original diskgroup size. So this condition
                            # below is unlikely to happen
                            if _is_add_cell  and _is_step_resize_dg and not _eBoxCluCtrl.mIsOciEXACC():
                                ebLogInfo(f'Skip mResizeGriddisks for RESIZE_DGS step in Add Cell for ExaCS')
                                step_list = ["DgResize", "Complete"]       
                            else:
                                step_list = ["GdResize", "DgResize", "Rebalance", "SizeValidation", "Complete"]       
                                _eBoxCluCtrl.mUpdateStatusOEDA(True, step_list[_step], step_list, 'Diskgroup '\
                                                            + _injson[_constantsObj._action_key] +\
                                                            ' operation for ' + _inparams[_dg_name_key])
                                ebLogInfo("*** Attempting to resize Griddisks for diskgroup %s" %(_dg_name))
                                _eBoxCluCtrl.mUpdateStatus('Griddisks resize for diskgroup %s in progress' %(_dg_name), False)
                                _rc = self.mResizeGriddisks(_options, _dg_name,  _newsizeMB, _diskgroupData)
                                if _rc:
                                    return _rc
                                _step = 1
                    
            elif _op == "RebalanceDiskgroup":
                step_list = ["DgRebalance", "Complete"]
                _injson[_constantsObj._action_key] = "rebalance"

                if _dg_name == _constantsObj._all_dg:
                    _dg_list = []
                    _cluster = _eBoxCluCtrl.mGetClusters().mGetCluster()
                    _cludgroups = _cluster.mGetCluDiskGroups()

                    for _dgid in _cludgroups:
                        _dg = _eBoxCluCtrl.mGetStorage().mGetDiskGroupConfig(_dgid)
                        _dg_type = _dg.mGetDiskGroupType().lower()
                        if _dg_type in [_constantsObj._data_dg_type_str, _constantsObj._reco_dg_type_str, _constantsObj._sparse_dg_type_str]:
                            _dg_list.append(_eBoxCluCtrl.mGetStorage().mGetDiskGroupConfig(_dgid).mGetDgName())

                    _injson[_constantsObj._params_key][_constantsObj._diskgroupname_key] = _dg_list

                _info = False
                
            _eBoxCluCtrl.mUpdateStatusOEDA(True, step_list[_step], step_list, 'Diskgroup '\
                                            + _injson[_constantsObj._action_key] +\
                                             ' operation for ' + _inparams[_dg_name_key])

            #calculating rebalance estimate for the given DG    
            if _injson[_constantsObj._action_key] == "resize":
                _injson[_constantsObj._params_key][_constantsObj._failgroup_list] = self.mGetFailGroupList(_dg_name)
                self.mLogRebalanceTimeEstimate(_injson, aOptions, _dg_name)
                _msg = {}
                ebLogInfo("*** Attempting to update diskgroup %s through ASM" %(_dg_name))
                _rc = self.mHandleDbaasapiSynchronousCall(_options, _injson, True,_msg)

                _count = 2
                # Retry diskgroup resize operation incase the Quorum disks are
                # not accessible intermittently resulting in ORA-15025. 
                while "errmsg" in list(_msg.keys()) and "ORA-15025" in _msg["errmsg"] and _count > 0:
                    time.sleep(5)
                    ebLogInfo("Retrying resize of diskgroup in ASM.")
                    _msg = {}
                    _rc = self.mHandleDbaasapiSynchronousCall(_options, _injson, True,_msg)
                    _count = _count - 1

                if "msg" in list(_msg.keys()) and "relocating" in _msg["msg"]:
                    _vote_disk_relocated = True
                    ebLogTrace(f"Detected voting disk relocation")
            else:
                ebLogInfo("*** Attempting to update diskgroup %s through ASM" %(_dg_name))
                _rc = self.mHandleDbaasapiSynchronousCall(_options, _injson, _info) 
            _eBoxCluCtrl.mUpdateStatus('Resize for diskgroup %s through ASM in progress' %(_dg_name), False)
            if _rc == 0:
                if _op == "ResizeDiskgroup":
                    # Ref 37873380:
                    # For ADD_CELL-RESIZE_DGS, this step is skipped as
                    # it is time consuming (up to several days)
                    # Waiting should be done in WAIT_RESIZE_DGS step
                    if _is_add_cell  and _is_step_resize_dg and not _eBoxCluCtrl.mIsOciEXACC():
                        ebLogInfo(f'Skip mEnsureDgsRebalanced and '
                            'mValidateDgsPostRebalance for step RESIZE_DGS in ExaCS')
                    else:
                        _step += 1
                        ebLogInfo("*** DG resize started; Dispatching watcher to ensure resized DG is rebalanced")
                        _eBoxCluCtrl.mUpdateStatusOEDA(True, step_list[_step], step_list, 'Diskgroup '\
                                                + _injson[_constantsObj._action_key] +\
                                                ' operation for ' + _inparams[_dg_name_key])
                        _eBoxCluCtrl.mUpdateStatus('Rebalance for diskgroup %s  in progress' %(_dg_name), False)

                        _rc = self.mEnsureDgsRebalanced(_options, _dg_name, _diskgroupData)
                        if _rc:
                            _detail_error = "Rebalance status not retrieved"
                            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_REBALANCE_FAILED'], _detail_error)
                            if _vote_disk_relocated:
                                self.mRelocateVotedisk(_options, _dg_name)
                            return _rc
                    
                        _step += 1
                        if _vote_disk_relocated:
                            self.mRelocateVotedisk(_options,_dg_name)
                        ebLogInfo("*** DG rebalanced; Checking if DG is correctly resized")
                        _eBoxCluCtrl.mUpdateStatus('Rebalance for diskgroup %s done, Resize value check in progress' %(_dg_name), False)
                        _eBoxCluCtrl.mUpdateStatusOEDA(True, step_list[_step], step_list, 'Diskgroup '\
                                                + _injson[_constantsObj._action_key] +\
                                                ' operation for ' + _inparams[_dg_name_key])

                        ### Size has to be validated against this number post rebalance of sparse DG
                        _newExpectedSizeMB = _newsizeMB
                        if _dg_name.startswith(_constantsObj._sparse_dg_prefix):
                            _newExpectedSizeMB = _newsizeMB * _constantsObj._sparse_vsize_factor
                        _rc = self.mValidateDgsPostRebalance(_options, _dg_name, _newExpectedSizeMB, None, _diskgroupData)
                        if _rc:
                            _detail_error = "Post ASM resize validation failed for: " + _dg_name
                            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_POST_ASM_RESIZE'], _detail_error)
                            return _rc
                    
                        if _newsizeMB < _dg_cursize:
                            _eBoxCluCtrl.mUpdateStatusOEDA(True, step_list[_step], step_list, 'Diskgroup '\
                                                    + _injson[_constantsObj._action_key] +\
                                                    ' operation for ' + _inparams[_dg_name_key])
                            ebLogInfo("*** Attempting to resize Griddisks for diskgroup %s" %(_dg_name))
                            _eBoxCluCtrl.mUpdateStatus('Griddisks resize for diskgroup %s in progress' %(_dg_name), False)
                            _rc = self.mResizeGriddisks(_options, _dg_name, _newsizeMB, _diskgroupData)
                            if _rc:
                                _detail_error = "Error resizing grid disks for diskgroup: " + _dg_name
                                _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_RESIZE_GRIDDISK'], _detail_error)
                                return _rc
                            
                        _log = _dg_name + " resized successfully to " + str(_newsizeMB) + " MB"
                        ebLogInfo(_log)
                        _diskgroupData["Log"] = _log
                        _diskgroupData["SizeMB"] = _newsizeMB
                        # Update xml file
                        _cluster = _eBoxCluCtrl.mGetClusters().mGetCluster()
                        _cludgroups = _cluster.mGetCluDiskGroups()
                        for _dgid in _cludgroups:
                            ebLogInfo("*** Working on Diskgroup ID %s" %(_dgid))
                            _dgConfig = _eBoxCluCtrl.mGetStorage().mGetDiskGroupConfig(_dgid)
                            if _dgConfig.mGetDgName() == _dg_name:
                                _dg_slice_size_GB = int(_dg_slice/1024)
                                ebLogInfo("*** Diskgroup Slice for %s Is %s" %(_dg_name, _dg_slice))
                                if _dg_name.startswith(_constantsObj._sparse_dg_prefix):
                                    _dgConfig.mSetSparseVirtualSize(_dg_slice_size_GB * _constantsObj._sparse_vsize_factor)
                                _total_size_in_GB = int(_newsizeMB/1024)
                                _dgConfig.mSetSliceSize(_dg_slice_size_GB)
                                _dgConfig.mSetDiskGroupSize(_total_size_in_GB)
                                # Remove the old config and add new one
                                _eBoxCluCtrl.mGetStorage().mRemoveDiskGroupConfig(_dgid)
                                _eBoxCluCtrl.mGetStorage().mAddDiskGroupConfig(_dgConfig)
                                _eBoxCluCtrl.mSaveXMLClusterConfiguration()
                                break
                elif self.mGetResizeDgonCells(_dg_name, _constantsObj):
                    # Refer Bug 35320487 - This section should only be reached in case of a retry of storage
                    # resize operation. If during previous storage resize operation, there was
                    # an error - say just after resizing DATA grid disk on ASM. When retry happens
                    # the flow should come here after rebalancing the disk group on asm to complete
                    # the resize of DATA grid disks on cells.
                    # Resize _dg_name on cells
                    _injson[_constantsObj._action_key] = "resize"
                    _newsizeGB = _inparams[_constantsObj._newsizeGB_key]
                    _newsizeMB = int(_newsizeGB) * 1024
                    # If there are 12 grid disks and 3 cells, this value = 36
                    _dg_griddisks_count_all_cells = self.mGetGridDiskCountRetryResize(_dg_name)
                    # The below calculations is based on the calculations done in
                    # case of _op == "ResizeDiskgroup" operation.
                    _dg_slice =  _newsizeMB/(_dg_griddisks_count_all_cells)
                    _dg_slice = int(_dg_slice / 16) * 16  ## Round to multiple of 16
                    _newsizeMB = _dg_slice * (_dg_griddisks_count_all_cells)
                    # This is the old size of diskgroup on cells currently,
                    # which couldn't be resized to correct size in previous resize attempt.
                    # It is set in clustorage when checking, if the grid disk size is different
                    # from grid disk size on asm in method mCheckGridDisksResizedCells.
                    _dg_cursize = self.mGetCurrentRetrySizeTotalMB(_dg_name)
                    _diskgroupData["SizeMB"] = _newsizeMB
                    # Below way of resizing grid disks on cells is based on how resize
                    # operation is done in case of _op == "ResizeDiskgroup" operation.
                    if _newsizeMB < _dg_cursize:
                        step_list = ["DgRebalance", "GdResize", "Complete"]
                        _eBoxCluCtrl.mUpdateStatusOEDA(True, "GdResize", step_list, 'Diskgroup '\
                                                + _injson[_constantsObj._action_key] +\
                                                 ' operation for ' + _inparams[_dg_name_key])
                        ebLogInfo("*** Attempting to resize Griddisks for diskgroup %s" %(_dg_name))
                        _eBoxCluCtrl.mUpdateStatus('Griddisks resize for diskgroup %s in progress' %(_dg_name), False)
                        _rc = self.mResizeGriddisks(_options, _dg_name, _newsizeMB, _diskgroupData)
                        if _rc:
                            _detail_error = "Error resizing grid disks for diskgroup: " + _dg_name
                            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_RESIZE_GRIDDISK'], _detail_error)
                            return _rc
                    
                _eBoxCluCtrl.mUpdateStatusOEDA(True, "Complete", step_list, 'Diskgroup '\
                                            + _injson[_constantsObj._action_key] +\
                                             ' operation for ' + _inparams[_dg_name_key])
            else:
                _detail_error = "Error updating diskgroup: " + _dg_name
                _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_UPDATING_DG'], _detail_error)
                _rc = self.mRecordError(gDiskgroupError['UpdateError'],\
                                   "*** Error updating diskgroup " + _dg_name)
            _stepSpecificDetails = _clu_utils.mStepSpecificDetails("reshapeDetails", 'DONE', "ASM reshape is completed", "","ASM")
            _clu_utils.mUpdateTaskProgressStatus([], 100, "ASM Reshape", "DONE", _stepSpecificDetails)
            return _rc
    # end


    def mGetResizeDgonCells(self, aDgName, aConstObj):
        """
        This method returns True if a resize of grid disks is needed on cells in case of
        retry of storage resize operation for any disk group. The boolean values for
        specific disk groups is determined from the method mCheckGridDisksResizedCells in
        clustorage.py.
        """
        # Sparse
        if aDgName.startswith(aConstObj._sparse_dg_prefix):
            return self.mGetResizeSparseOnCells()
        # Reco
        elif aDgName.startswith(aConstObj._reco_dg_prefix):
            return self.mGetResizeRecoOnCells()
        # Data
        elif aDgName.startswith(aConstObj._data_dg_prefix):
            return self.mGetResizeDataOnCells()
        else:
            return False

    def mValidateAndFilterStorPropDict(self, aOutJson, aStorPropContainer, aDgName, aConstantsObj=None):
        
        _payloadJson = aOutJson
        _storPropContainer = aStorPropContainer
        _dgName = aDgName
        _constantsObj = aConstantsObj
        
        if _constantsObj is None:
            _constantsObj = ebDiskgroupOpConstants()
        
        if _payloadJson:
            if _dgName in _payloadJson and _payloadJson[_dgName]:
                _dg_details_dict = _payloadJson[_dgName]
                if _constantsObj._propkey_storage in _dg_details_dict and _dg_details_dict[_constantsObj._propkey_storage]:
                    _storPropContainer.update(_dg_details_dict[_constantsObj._propkey_storage])
                    if not (_constantsObj._storprop_totalMb in _storPropContainer or _constantsObj._storprop_usedMb in _storPropContainer \
                             or _storPropContainer[_constantsObj._storprop_totalMb] or _storPropContainer[_constantsObj._storprop_usedMb]):
                        return self.mRecordError(gDiskgroupError['MissingStorProp'],\
                                                  "*** Required value for property total/used\
                                                   Mb not found for for diskgroup " + _dgName)
                else:
                    return self.mRecordError(gDiskgroupError['MissingStorPropDict'],\
                                              "*** No storage info for diskgroup " + _dgName)
            else:
                return self.mRecordError(gDiskgroupError['MissingPropDict'], "*** No info\
                 for diskgroup " + _dgName)
        else:
            return self.mRecordError(gDiskgroupError['NullOutputPayload'], "*** Null output\
             payload body; nothing to read")
        
        return 0
    # end

    def mLogRebalanceTimeEstimate(self, aInJson, aOptions, aDgName):
        _dbaasobj = self.mGetDbaasObj()
        # Get the cluctrl handle to fetch current details
        _eBoxCluCtrl = self.mGetEbox()
        _domUs = self.mGetDomUs()
        _domU = _domUs[0]
        _constantsObj = self.mGetConstantsObj()
        _injson= aInJson
        _dbaasData = {}
        _params = {}
        _params["dbname"] = "grid"
        _params["diskgroup"]= aDgName
        _uuid = _eBoxCluCtrl.mGetUUID()
        _params[_constantsObj._newsizeMB_key]=  _injson[_constantsObj._params_key][_constantsObj._newsizeMB_key]
        if (_constantsObj._rebalancepower_key in list(_injson[_constantsObj._params_key].keys()) and _injson[_constantsObj._params_key][_constantsObj._rebalancepower_key]):
            _params[_constantsObj._rebalancepower_key] = _injson[_constantsObj._params_key][_constantsObj._rebalancepower_key]
        _params["infofile"] = "/var/opt/oracle/log/validate" + "_" + _uuid + "_infofile.out"
        _dbaasobj.mExecuteDBaaSAPIAction("rebalance_time_estimate", "diskgroup", _dbaasData, _domU, _params, aOptions, False)
        ebLogInfo("*** The JSON for operation diskgroup action is rebalance_time_estimate")
        ebLogInfo(json.dumps(_dbaasData, indent=4, sort_keys=True))
        if ['Status','rebalance_time_estimate'] in list(_dbaasData.keys()) and _dbaasData['Status'] == 'Pass' and _dbaasData['rebalance_time_estimate']['error_code']==0:        
            ebLogInfo("*** The rebalance time estimate for %s is %s seconds"%(_dbaasData['rebalance_time_estimate']['diskgroup'],_dbaasData['rebalance_time_estimate']['rebalance_eta_sec']))    

    def mRelocateVotedisk(self, aOptions, aDgName):
        ebLogInfo("*** ebCluManageDiskgroup:mRelocateVotedisk >>>")
        _options = aOptions
        # Get the cluctrl handle to fetch current details
        _eBoxCluCtrl = self.mGetEbox()
        # Get the constants object for use in the scope of this function
        _constantsObj = self.mGetConstantsObj()
        _dg = aDgName
        _injson = {}
        _uuid = _eBoxCluCtrl.mGetUUID()
        _injson[_constantsObj._dbaasapi_object_key] = _constantsObj._dbaasapi_object_value
        _injson[_constantsObj._operation_key] = _constantsObj._operation_value
        _injson[_constantsObj._action_key] = "relocate_votedisk"
        _injson[_constantsObj._params_key] = {}
        _injson[_constantsObj._params_key][_constantsObj._dbname_key] = _constantsObj._dbname_value
        _injson[_constantsObj._params_key][_constantsObj._diskgroupname_key] = _dg
        _injson[_constantsObj._params_key][_constantsObj._param_infofile_key] = "/var/opt/oracle/log/validate" + "_" + _uuid + "_infofile.json"
        _injson[_constantsObj._flags_key] = ""

        # Append to stack only if we are not in rollback mode            
        _rc = self.mHandleDbaasapiSynchronousCall(_options, _injson, False)
        if _rc == 0:
            ebLogInfo("*** Successfully relocated votedisk back to %s"%(_dg))
        else:
            ebLogError("Relocation of votedisk back to %s failed"%(_dg))
        return _rc
        
    def mUtilCheckIfDgResizable(self, aUsedMb, aNewSize):
        _used_mb = aUsedMb
        _new_size = aNewSize
        # Get the cluctrl handle to fetch current details
        _eBoxCluCtrl = self.mGetEbox()
        _cellCount = len(list(_eBoxCluCtrl.mReturnCellNodes().keys()))   
        # As per MAA recommendation, minimum space after resize of a DG should be > 15%
        # depending on the number of cells, leave free space when shrinking DG's back
        # for 3-4 cells, 15%; for 5+ 9%
        # (new size - used) * 100 / (new size) should be greater than 15 incase of 3-4 cells else 9 incase of 5 and above cells
        _new_free_percentage = (_new_size - _used_mb) * 100 / _new_size
        ebLogInfo("*** Cell count is: %s and the minimum free space percentage after resize is: %s"%(str(_cellCount), str(_new_free_percentage)))
        if (_cellCount > 4 and _new_free_percentage <= 9) or (_cellCount < 5 and _new_free_percentage <= 15):
            return -1
        return 0
    # end
    
    def mASMRebalancePrecheck(self, aOptions, aNewCellList):
        ebLogInfo("*** Executing mASMRebalancePrecheck")
        rebalance_power = 4
        #Minumum space needed on each DG  is 64 X RebalancePower X total number of disks currently in a disk group
        _eBoxCluCtrl = self.mGetEbox()
        _cluster = _eBoxCluCtrl.mGetClusters().mGetCluster()
        _cludgroups = _cluster.mGetCluDiskGroups()
        _dg_Name_List = []
        for _dgid in _cludgroups:
            _dg_Name_List.append(_eBoxCluCtrl.mGetStorage().mGetDiskGroupConfig(_dgid).mGetDgName())

        _cellCount = len(list(_eBoxCluCtrl.mReturnCellNodes().keys()))
        _newCellCount = len(aNewCellList)
        _space_needed = 64 * _cellCount * 12 * rebalance_power
        _more_needed_space = 0
        if _newCellCount > 0:
            _disksize = _eBoxCluCtrl.mGetEsracks().mGetDiskSize()
            _more_needed_space = (_newCellCount * 12 * _disksize/1.73 + 2) * 3 * 4 
        for _dg_name in _dg_Name_List:
            _used_size_mb  = self.mUtilGetDiskgroupSize(aOptions, _dg_name, self.mGetConstantsObj(),"usedMb")
            _total_size_mb = self.mUtilGetDiskgroupSize(aOptions, _dg_name, self.mGetConstantsObj())
            _space_available = _total_size_mb - _used_size_mb
            if _space_available > (_space_needed + _more_needed_space ):
                _rc = 0
                ebLogInfo("*** No change needed for Rebalance Power")
            elif (_space_available > _space_needed) & (_space_available < (_space_needed + _more_needed_space )):
                ebLogInfo("*** Rebalance Power changed to 1")
                rebalance_power = 1
                self.mExecuteSetDGsRebalancePower(_dg_Name_List, rebalance_power)
                _rc = 0
            else:
                _rc = 1
                ebLogError("*** Rebalance precheck failed: free space needed: %d MB and available is:%d MB for DG %s "%((_space_needed + _more_needed_space), _space_available, _dg_name))
                return _rc
        return _rc


    
    def mCheckDgPropertyInDbaasOutJson(self, aInfoJson, aDgName, aPropertyName):
        
        _infoobj = aInfoJson
        _dg = aDgName
        _property = aPropertyName
        
        # Get the constants object for use in the scope of this function
        _constantsObj = self.mGetConstantsObj()
        
        _rc = 0
        if not _infoobj:
            _rc = self.mRecordError(gDiskgroupError['NullOutputPayload'], "*** No readable\
             properties in info output payload for diskgroup " + _dg)
        else:
            if _dg in _infoobj and _infoobj[_dg]:
                _dg_stat = _infoobj[_dg]
                if _property in _dg_stat and _dg_stat[_property]:
                    _rc = 0
                else:
                    _err_key = ""
                    
                    if _property == _constantsObj._propkey_rebstat:
                        _err_key = "MissingReblPropDict"
                    
                    if _property == _constantsObj._propkey_failgroup:
                        _err_key = "MissingFgrpPropDict"
                    
                    if _property == _constantsObj._propkey_storage:
                        _err_key = "MissingStorPropDict"
                    
                    _rc = self.mRecordError(gDiskgroupError[_err_key], "*** Could not find "\
                                             + _property + " for diskgroup " + _dg)
            else:
                _rc = self.mRecordError(gDiskgroupError['MissingPropDict'], "*** Could not find\
                 properties for diskgroup " + _dg)
            
        return _rc
            
    # end
    
    
    def mUtilGetDiskgroupSize(self, aOptions, aDg, aConstantsObj, aUsedMB=None):
        _options = aOptions
        _dg = aDg
        _constantsObj = aConstantsObj
        
        _dg_properties = []
        _dg_properties.append(_constantsObj._propkey_storage)

        if aUsedMB is None:
            _storprop = _constantsObj._storprop_totalMb
        else:
            _storprop = _constantsObj._storprop_usedMb

        ebLogInfo("*** ebCluManageDiskgroup:mUtilGetDiskgroupSize - Getting diskgroup size for %s diskgroup" % (_dg))
       
        # Get the dbaasobj handle for dbaasapi calls and handling DomU commands/output
        _dbaasObj = self.mGetDbaasObj()
        _rc = self.mClusterDgrpInfo2(_options, _dg, _dg_properties)
        if _rc != 0:
            _rc = self.mRecordError(gDiskgroupError['ErrorFetchingDetails'], "*** Could not fetch\
             info for diskgroup " + _dg)

        else:    
            _infoobj = _dbaasObj.mReadStatusFromDomU(_options, self.mGetLastDomUused(), self.mGetOutJson())
            _rc = self.mCheckDgPropertyInDbaasOutJson(_infoobj, _dg, _constantsObj._propkey_storage)
            
            if _rc == 0:
                _dg_stat = _infoobj[_dg]
                _stor_stats = _dg_stat[_constantsObj._propkey_storage]
                if _storprop in _stor_stats and _stor_stats[_storprop]:
                    # have put float here to handle if dbaascli gives output in scientific notation like -> "2.3857E+10"
                    _rc = int(float(_stor_stats[_storprop]))
                else:
                    _rc = self.mRecordError(gDiskgroupError['MissingReblProp'], "*** Could not find\
                     'status' property for rebalancing operation of diskgroup " + _dg)

            else:
                _rc = self.mRecordError(gDiskgroupError['DbaasApiFail'], "*** Dbaas API failed with internal error. Operation failed" )
        
        return _rc
    
    # end

        
    def isDgResized(self, aDgSetSize, aDgRequestedSize):
        
        _round_factor = 1024  # Round the sizes to nearest GB before comparison
        
        _dgSetSize = int(aDgSetSize)
        _dgRequestedSize = int(aDgRequestedSize)
        
        _dgSetSize /= _round_factor
        _dgRequestedSize /= _round_factor
   
        _diff = int(_dgSetSize - _dgRequestedSize)
        # presence of quorum disks can add a mismatch of at max 1 GB 
        # in diskgroup resize. Thus allow tolerance of 1 GB during resize 
        # of diskgroup.
        if (_diff == -1 or _diff == 0 or _diff == 1):
            return 1
        else:
            return 0
    
    #end
    
    
    def mValidateAndGetFailgroupDetails(self, aInfoJson, aDg, aConstantsObj, aFgrpPropDict):
        
        _infoobj = aInfoJson
        _dg = aDg
        _constantsObj = aConstantsObj
        _fgrp_prop_dict = aFgrpPropDict
        
        if _infoobj:
            if _dg in _infoobj and _infoobj[_dg]:
                _dg_prop_dict = _infoobj[_dg]
                if _constantsObj._propkey_failgroup in _dg_prop_dict and _dg_prop_dict[_constantsObj._propkey_failgroup]:
                    _fgrp_prop_dict.update(_dg_prop_dict[_constantsObj._propkey_failgroup])
                else:
                    return self.mRecordError(gDiskgroupError['MissingFgrpPropDict'], "*** No\
                     failgroups info for diskgroup " + _dg)
            else:
                return self.mRecordError(gDiskgroupError['MissingPropDict'], "*** No info for\
                 diskgroup " + _dg)
        else:
            return self.mRecordError(gDiskgroupError['NullOutputPayload'], "*** Null output\
             payload body; nothing to read")
        
        return 0
        
    # end
    
    
    # Method to fetch diskgroup info for combination of parameters "dg_storage_props", "failgroups", "rebalance_status" 
    def mClusterDgrpInfo2(self, aOptions, aDGName, aPropList=None):

        _options = aOptions
        _propList = aPropList
        _dgName = aDGName
        # Get the constants object for use in the scope of this function
        _constantsObj = self.mGetConstantsObj()

        if _propList is None:
            _propList = _constantsObj._supported_dg_properties
            
        if type(_options) is dict and "password" in list(_options.keys()):
            _copy_options = copy.deepcopy(_options)
            _copy_options["password"] = "*****************"
            ebLogInfo(json.dumps(_copy_options, indent=4))
        
        _injson = {}
        _injson[_constantsObj._dbaasapi_object_key] = _constantsObj._dbaasapi_object_value
        _injson[_constantsObj._operation_key] = _constantsObj._operation_value
        _injson[_constantsObj._action_key] = "info"
        _injson[_constantsObj._params_key] = {}
        _injson[_constantsObj._params_key][_constantsObj._dbname_key] = _constantsObj._dbname_value
        _injson[_constantsObj._params_key][_constantsObj._diskgroupname_key] = _dgName
        _injson[_constantsObj._params_key][_constantsObj._props_key] = _propList
        _injson[_constantsObj._flags_key] = ""
        
        return self.mHandleDbaasapiSynchronousCall(_options, _injson, True)

    # end


    def mCheckIfDgResizable(self, aOptions, aDgName, aNewDgSizeMb=None, aNewDgRelativeSize=None, aNewSizesDict=None, aDiskgroupData=None, aPrecheckDict=None):
        
        _options = aOptions
        _dgName = aDgName
        _newSize = aNewDgSizeMb
        _newSizeRelative = aNewDgRelativeSize
        _new_dg_sizes_dict = aNewSizesDict
        _precheck_dict = aPrecheckDict
        if aDiskgroupData is None:
            _diskgroupData = self.mGetDiskGroupOperationData()
        else:
            _diskgroupData = aDiskgroupData
        
        # Get the cluctrl handle to fetch current details
        _eBoxCluCtrl = self.mGetEbox()
        # Get the dbaasobj handle for dbaasapi calls and handling DomU commands/output
        _dbaasObj = self.mGetDbaasObj()
        # Get the constants object for use in the scope of this function
        _constantsObj = self.mGetConstantsObj()
            
        if (_newSize is None and _newSizeRelative is None):
            return self.mRecordError(gDiskgroupError['InvalidArgs'], "*** At least one of absolute \
             or relative size is needed")
            
        if (_newSize is not None):
            ebLogInfo("** ebCluManageDiskgroup:mCheckIfDgResizable - Absolute size provided, \
            ignoring relative size")
            _newSizeRelative = None
        
        _dgrp_properties = []
        _dgrp_properties.append(_constantsObj._propkey_storage)
        _stor_prop_dict = {}

        # Get DATA Diskgroup properties to check if DGs are re-sizable
        _rc = self.mClusterDgrpInfo2(_options, _dgName, _dgrp_properties)
        if _rc != 0:
            return self.mRecordError(gDiskgroupError['ErrorFetchingDetails'], "*** Could not\
             fetch info for diskgroup " + _dgName)
          
        # Read the INFO file containing the storage property value
        # It should be ready and populated as mClusterDgrpInfo2 above is a blocking call
        _infoobj = _dbaasObj.mReadStatusFromDomU(_options, self.mGetLastDomUused(), self.mGetOutJson())
        ebLogInfo("** ebCluManageDiskgroup:mCheckIfDgResizable - Filtering storage properties")
        _rc = self.mValidateAndFilterStorPropDict(_infoobj, _stor_prop_dict, _dgName, _constantsObj)
                
        if _rc == 0:
            _dg_total_mb = int(_stor_prop_dict[_constantsObj._storprop_totalMb])
            _dg_used_mb = int(_stor_prop_dict[_constantsObj._storprop_usedMb])
            _dg_os_mb   =  int(_stor_prop_dict.get(_constantsObj._storprop_osMb, 0))
            if _dgName.startswith(_constantsObj._sparse_dg_prefix):
                _dg_used_mb = int(_dg_used_mb / _constantsObj._sparse_vsize_factor)
                _dg_total_mb = int(_dg_total_mb / _constantsObj._sparse_vsize_factor)
                _dg_os_mb = int(_dg_os_mb / _constantsObj._sparse_vsize_factor) 
                ebLogInfo("*** %s DG: (Actual Size, Actual Used Space) : (%s, %s)"%(_dgName, _dg_total_mb, _dg_used_mb))

            if _newSize is None:
                _newSize = _dg_total_mb * float(_newSizeRelative)
            
            if (_new_dg_sizes_dict is not None):
                for key in _new_dg_sizes_dict:
                    if _diskgroupData[key] == _dgName:
                        _new_dg_sizes_dict[key] = _newSize
                        break

            ebLogInfo("*** %s DG: (Current Size, Used Space, New Size) : (%s, %s, %s)" %\
                       (_dgName, _dg_total_mb, _dg_used_mb, _newSize))
            if  int(_newSize) < _dg_total_mb:
                _rc = self.mUtilCheckIfDgResizable(_dg_used_mb, _newSize)
                if _rc == 0:
                    ebLogInfo("*** %s DG qualifies for resizing" %(_dgName))
                else:
                    return self.mRecordError(gDiskgroupError['NonModifiable'],
                        f"***DG does not qualify for resizing: {_dgName} as it does not fulfill the free space percentage criteria")
            else:
                _rc = 0
                if _precheck_dict:
                    #Bug 38483116: If freespcce is available in gridisks, skip addition of 
                    #space details to _precheck_dict thereby freespace for this dg is not checked
                    #in celldisks level later in mCalculateFreeSpaceCelldisk
                    ebLogInfo(f"*** Checking if Griddisks are already resized")
                    _rc = self.mCheckGriddiskSize(_dgName,_newSize)
                    if _rc == 0:
                        if "currentMB" in list(_precheck_dict.keys()):
                            _precheck_dict["currentMB"] += _dg_total_mb
                        if "newMB" in list(_precheck_dict.keys()):
                            _precheck_dict["newMB"] += int(_newSize)
                        if "osMB"  in list(_precheck_dict.keys()):
                            _precheck_dict["osMB"]  += _dg_os_mb
                        ebLogInfo(f"*** {_dgName} DG qualifies for resizing as it is upsize operation. "\
                                   "Precheck will be done now for checking free space on cells.")
                    else:
                        ebLogInfo(f"*** Griddisks of dg: {_dgName} are already resized to accomodate new dg size. "
                                   "Freespace check at celldisk level is skipped for this diskgroup.")
                        _rc = 0
        return _rc
    # end
    
    
    def mWaitUntilDgRebalanced (self, aOptions, aDgName, aConstantsObj):
            
        ebLogInfo("*** ebCluManageDiskgroup:mEnsureDgsRebalanced:mWaitUntilDgRebalanced >>>")
        _options = aOptions
        _dg = aDgName
        _constantsObj = aConstantsObj
        _ebox = self.mGetEbox()
        _node = exaBoxNode(get_gcontext())

        # Get the dbaasobj handle for dbaasapi calls and handling DomU commands/output
        _dbaasObj = self.mGetDbaasObj()
        
        _dgrp_properties = []
        _dgrp_properties.append(_constantsObj._propkey_rebstat)
        
        _rc = 0
        _time_start = time.time()
        _cmd_timeout = 300
        while True:
            _rc = self.mClusterDgrpInfo2(_options, _dg, _dgrp_properties)
            if _rc != 0:
                _rc = self.mRecordError(gDiskgroupError['ErrorFetchingDetails'], "*** Could\
                    not fetch info for diskgroup " + _dg)
                break
                
            _infoobj = _dbaasObj.mReadStatusFromDomU(_options, self.mGetLastDomUused(), self.mGetOutJson())
            _rc = self.mCheckDgPropertyInDbaasOutJson(_infoobj, _dg, _constantsObj._propkey_rebstat)
                
            if _rc:
                break
                
            _dg_stat = _infoobj[_dg]
            _rebalance_stats = _dg_stat[_constantsObj._propkey_rebstat]
            if _constantsObj._rebstatprop_status in _rebalance_stats and _rebalance_stats[_constantsObj._rebstatprop_status]:
                if (_rebalance_stats[_constantsObj._rebstatprop_status]).upper() == "DONE":
                    break

                if (_rebalance_stats[_constantsObj._rebstatprop_status]).upper() == "INCOMPLETE" and _ebox.mCheckConfigOption('extra_traces', "True"):
                    ebLogInfo("Rebalance is in progress.")
                    ebLogInfo("Output of query from v$ASM_OPERATION:")
                    _domU = _ebox.mReturnDom0DomUPair()[0][1]
                    _path, _sid = _ebox.mGetGridHome(_domU)
                    _cmd_pfx = 'ORACLE_HOME=%s;export ORACLE_HOME;ORACLE_SID=%s; export ORACLE_SID;PATH=$PATH:$ORACLE_HOME/bin;export PATH;'%(_path,_sid)
                    _cmd = _cmd_pfx + "echo \"select GROUP_NUMBER, OPERATION, PASS, STATE, SOFAR, EST_WORK, EST_MINUTES, POWER from GV\$ASM_OPERATION ;\" | sqlplus -s / as sysasm"
                    _cmd_pfx_state = "ORACLE_HOME=%s;export ORACLE_HOME;ORACLE_SID=%s; export ORACLE_SID;PATH=\$PATH:\$ORACLE_HOME/bin;export PATH;"%(_path,_sid)
                    _cmd_state_run = _cmd_pfx_state + 'echo \\"select GROUP_NUMBER, STATE, POWER, EST_MINUTES, SOFAR, EST_WORK from GV\\\\\$ASM_OPERATION where STATE=\'RUN\';\\" | sqlplus -s / as sysasm'
                    _cmd_get_diskgroup_name = _cmd_pfx_state + 'echo \\"select GROUP_NUMBER, NAME from GV\\\\\$ASM_DISKGROUP where GROUP_NUMBER=\'{0}\';\\" | sqlplus -s / as sysasm'
                    _node.mConnect(aHost=_domU)
                    _i, _o, _e = _node.mExecuteCmd(f'su - grid -c \'{_cmd}\'', aTimeout=_cmd_timeout)
                    _node.mDisconnect()
                    _out = _o.readlines()
                    if "no rows selected\n" in _out:
                        ebLogInfo("No rebalance in progress")
                        break
                    else:
                        ebLogInfo("Rebalance is in progress")
                        ebLogInfo(' '.join(_out))
                        _time_start = self.mUpdateRebalanceStatus(_domU, _cmd_state_run,
                                                               _cmd_get_diskgroup_name,
                                                               _time_start, _cmd_timeout,
                                                               self.mGetConstantsObj())
            else:
                _rc = self.mRecordError(gDiskgroupError['MissingReblProp'], "*** Could not\
                    find 'status' property for rebalancing operation of diskgroup " + _dg)
                break
            time.sleep(30)
                
        # done while
        if _rc == 0:
            ebLogInfo("*** Diskgroup %s detected to be re-balanced successfully" %(_dg))
                
        ebLogInfo("*** ebCluManageDiskgroup:mEnsureDgsRebalanced:mWaitUntilDgRebalanced <<<")
        return _rc
        
        # end waitUntilDgRebalanced
        
    def _extract_cell_vs_griddisks_map(self, aDg, aFgrpPropDict, aCellVsGriddisksMap):
        
        _dg = aDg
        _fgrp_prop_dict = aFgrpPropDict
        _cell_vs_griddisks_map = aCellVsGriddisksMap
        
        # Get the constants object for use in the scope of this function
        _constantsObj = self.mGetConstantsObj()
        
        if _fgrp_prop_dict:
            _cell_count = len(list(_fgrp_prop_dict.keys()))
            if _cell_count == 0:
                return self.mRecordError(gDiskgroupError['MissingFgrpProp'], "*** No cells listed by failgroups for diskgroup " + _dg)
                
            for _cell_short_name in sorted(_fgrp_prop_dict.keys()):
                if _constantsObj._fgrpprop_numdisks in _fgrp_prop_dict[_cell_short_name.upper()] and\
                        int(_fgrp_prop_dict[_cell_short_name.upper()][_constantsObj._fgrpprop_numdisks]) > 1:
                    _cell_vs_griddisks_map[_cell_short_name.upper()] = _fgrp_prop_dict[_cell_short_name.upper()][_constantsObj._fgrpprop_celldisks]
                
                if len(_cell_vs_griddisks_map[_cell_short_name]) == 0:
                    return self.mRecordError(gDiskgroupError['NullPropertyValue'], "*** No \
                     griddisks listed diskgroup:cell " + _dg + ":" + _cell_short_name)
        else:
            return self.mRecordError(gDiskgroupError['MissingFgrpPropDict'], "*** No failgroups\
             info for diskgroup " + _dg)
        
        return 0

    def mCalcOverallRebalPercent(self, aDgConstantsObj):
        """
        This method is to calculate overall percentage progress for rebalance
        1. Get the sizes from xml and calculate percentage distribution of different DGs
        2. Based on self._dict_groups_percent_avg for each diskgroup - calculate weighted average percentage
        with the weights calculated in point 1 and the rebalance percentage per diskgroup
        """
        try:
            _ebox = self.mGetEbox()
            _cluster = _ebox.mGetClusters().mGetCluster()
            _cludgroups = _cluster.mGetCluDiskGroups()
            _dgConstantsObj = aDgConstantsObj
            _dg_names = []
            _dg_sizes = {}
            _total_size = 0
            # Get diskgroup names and diskgroup size for each diskgroup
            # Note: Since, we are only concerned about weightage of each diskgroup - it doesn't matter if
            # the size is current size in the xml or the size before resize since percentage weightage should
            # remain same
            for _dgid in _cludgroups:
                _dg = _ebox.mGetStorage().mGetDiskGroupConfig(_dgid)
                _dg_type = _dg.mGetDiskGroupType().lower()
                if _dg_type in [_dgConstantsObj._data_dg_type_str, _dgConstantsObj._reco_dg_type_str, _dgConstantsObj._sparse_dg_type_str]:
                    _dg_name = _dg.mGetDgName()
                    _dg_size = _dg.mGetDiskGroupSize()
                    if _dg_size is not None:
                        _dg_sizes[_dg_name] = _ebox.mGetStorage().mGetDiskSizeInInt(_dg_size)
                        _total_size += _dg_sizes[_dg_name]
                        _dg_names.append(_dg_name)

            # Use weighted averages and calculate overall percentage
            _overall_percentage = 0
            for _dg_name in _dg_names:
                if _dg_name in self._dict_groups_percent_avg:
                    _dg_weighted_progress = (self._dict_groups_percent_avg[_dg_name]) * (_dg_sizes[_dg_name] / _total_size)
                else:
                    _dg_weighted_progress = 0
                _overall_percentage += _dg_weighted_progress
            return int(_overall_percentage)
        except Exception as ex:
            ebLogWarn(f"Overall percentage could not be calculated due to an exception: {ex}. Returning 0 instead.")
            return 0

    def mUpdateRebalanceStatus(self, aDOMU, aCmdStateRun, aCmdDiskgrpName, aTimeStart, aCmdTimeout,
                               aDgConstantsObj):
        """
        This method prepares a rebalance status structure and updates it in the "data" column
        of exacloud mysql DB from where ecra can query the same.
        The rebalance status is updated in 'time_check_rebalance_seconds' time. Current
        default is 10 minutes.
        """
        try:
            _domU = aDOMU
            _cmd_state_run = aCmdStateRun
            _time_start = aTimeStart
            _cmd_timeout = aCmdTimeout
            _eBoxCluCtrl = self.mGetEbox()
            _clu_utils = ebCluUtils(_eBoxCluCtrl)
            _dg_constants_obj = aDgConstantsObj
            # Prepare basic dict structure to get rebalance status
            _rebalance_status = {"stepProgressDetails": {}}
            _rebalance_status["stepProgressDetails"] = {"message": "Rebalance is in progress",
                                                        "completedNodes": [],
                                                        "stepSpecificDetails": {},
                                                        "percent_complete": 0,
                                                        "status": "InProgress"}
            if time.time() - _time_start >= int(_eBoxCluCtrl.mCheckConfigOption('time_check_rebalance_seconds')):
                # Move the start time ahead by "time_check_rebalance_seconds" for next iteration
                _time_start = _time_start + int(_eBoxCluCtrl.mCheckConfigOption('time_check_rebalance_seconds'))
                with connect_to_host(_domU, get_gcontext()) as _node:
                    _i, _o, _e = _node.mExecuteCmd(f'su - grid -c "{_cmd_state_run}"', aTimeout=_cmd_timeout)
                _out = _o.readlines()
                _group_number = None
                _rebalance_power = None
                _work_done = None
                _estimated_work = None
                _group_details_dict = {}
                # Get the parameters such as group number, rebalance power and eta in minutes
                # Also, calculate max eta if there are 2 or more RUN states.
                ebLogTrace(f"Output obtained is {_out}.")
                for _line in _out:
                    if "RUN" in _line:
                        _columns = _line.strip().split()
                        _group_number = _columns[0].strip()
                        _rebalance_power = _columns[2].strip()
                        _eta_mins = _columns[3].strip()
                        _work_done = _columns[4].strip()
                        _estimated_work = _columns[5].strip()
                        _work_done_float = 0.0
                        _estimated_work_float = 0.0
                        _percent_completed_dg = 0.0
                        if _work_done and _clu_utils.mIsNumber(_work_done):
                            _work_done_float = float(_work_done)
                        if _estimated_work and _clu_utils.mIsNumber(_estimated_work):
                            _estimated_work_float = float(_estimated_work)
                        if _work_done_float != 0.0 and _estimated_work_float != 0.0:
                            _percent_completed_dg = (_work_done_float/_estimated_work_float) * 100
                        if _group_number not in _group_details_dict:
                            _group_details_dict.update({_group_number : {}})
                        _group_details_dict[_group_number]["rebalance_power"] = _rebalance_power
                        _group_details_dict[_group_number]["eta_mins"] = _eta_mins
                        _group_details_dict[_group_number]["percent_work_done_dg"] = _percent_completed_dg
                        # if there are 2 or more states with RUN state - and are of same Diskgroup, only for the
                        # same group number max eta will be updated
                        if "max_eta_mins" not in _group_details_dict[_group_number]:
                            _group_details_dict[_group_number]["max_eta_mins"] = float(_group_details_dict[_group_number]["eta_mins"])
                        if float(_group_details_dict[_group_number]["eta_mins"]) > _group_details_dict[_group_number]["max_eta_mins"]:
                            _group_details_dict[_group_number]["max_eta_mins"] = float(_group_details_dict[_group_number]["eta_mins"])
                        if "cumulative_percent_dg" not in _group_details_dict[_group_number]:
                            _group_details_dict[_group_number]["cumulative_percent_dg"] = _group_details_dict[_group_number]["percent_work_done_dg"]
                        else:
                            _group_details_dict[_group_number]["cumulative_percent_dg"] += _group_details_dict[_group_number]["percent_work_done_dg"]
                        if "number_of_operations_dg" not in _group_details_dict[_group_number]:
                            _group_details_dict[_group_number]["number_of_operations_dg"] = 1
                        else:
                            _group_details_dict[_group_number]["number_of_operations_dg"] += 1
                        # Calculate average percentage of parallel operations done for a DG
                        _group_details_dict[_group_number]["percent_work_done_avg"] =  _group_details_dict[_group_number]["cumulative_percent_dg"]/_group_details_dict[_group_number]["number_of_operations_dg"]
                _diskgroup_rebalance_details = []
                _diskgroup_names = [
                    _dg_constants_obj._data_dg_prefix,
                    _dg_constants_obj._reco_dg_prefix,
                    _dg_constants_obj._sparse_dg_prefix
                ]
                _diskgroup_names_number_dict = {}
                for _group_number, _group_details in _group_details_dict.items():
                    _cmd_get_diskgroup_name = aCmdDiskgrpName
                    _cmd_get_diskgroup_name = _cmd_get_diskgroup_name.format(_group_number)
                    # Get diskgroup name with the group number
                    with connect_to_host(_domU, get_gcontext()) as _node:
                        _i, _o, _e = _node.mExecuteCmd(f'su - grid -c "{_cmd_get_diskgroup_name}"', aTimeout=_cmd_timeout)
                    _out = _o.readlines()
                    _diskgroup_name = None
                    for _dg in _diskgroup_names:
                        for _line in _out:
                            if _dg in _line:
                                _diskgroup_name = _line.strip().split()[1].strip()
                                _diskgroup_names_number_dict[_diskgroup_name] = _group_number
                                break
                        # Optimization of loop - since _diskgroup_name is obtained - no need to loop again for
                        # diskgroup names
                        if _diskgroup_name:
                            break
                    # Create a structure for the status of diskgroup rebalance operation
                    # Since we queried for rebalance status in "RUN" state - the status will be "ONGOING"
                    _status = { "name": _diskgroup_name,
                                "status": "ONGOING",
                                "est_time_remaining": str(int(_group_details["max_eta_mins"]) * 60),
                                "Rebalance_power": _group_details["rebalance_power"],
                                "percentage_task_completed": int(_group_details["percent_work_done_avg"])}
                    # This class level variable will ensure:
                    # 1. If parallel rebalance operation is ongoing, the diskgroup associated average percentage is available
                    # for each diskgroup in this dictionary. This will be applicable for cell addition.
                    # 2. If sequentual rebalance operation is ongoing, the ebCluManageDiskgroup object will still be the same
                    # - so, each diskgroup associated percentage will be available in this dictionary at any point of time.
                    # This will help to calculate overall rebalance percentage.
                    self._dict_groups_percent_avg[_diskgroup_name] = _group_details["percent_work_done_avg"]
                    _diskgroup_rebalance_details.append(_status)
                # Below logic is to take care of status update for a diskgroup if it is completed just
                # after the previous status update such that it is not marked 100 percent done.
                # This is because the entry for the asm_operations table can be removed during this
                # time and the completed percentage may not yet be updated.
                for _diskgroup_name in self._dict_groups_percent_avg:
                    if _diskgroup_name not in _diskgroup_names_number_dict:
                        self._dict_groups_percent_avg[_diskgroup_name] = 100
                _overall_percent = self.mCalcOverallRebalPercent(_dg_constants_obj)
                # Overall percentage gets reset if during next status call, there is no 'RUN' entry in asm operations
                # table. To fix it, get the max of overall percentage and update that in DB.
                self._max_overall_percent = max(self._max_overall_percent, _overall_percent)
                _rebalance_status["stepProgressDetails"]["percent_complete"] = self._max_overall_percent
                # Final rebalance status dictionary formation
                _rebalance_status["stepProgressDetails"]["stepSpecificDetails"] = {"diskgroup_rbal_details": _diskgroup_rebalance_details}
                # Update the DB with rebalance status
                # Note that if there is no rebalance in progress, the waitforrebalancing step
                # will proceed and the "data" will be overwritten by - {"Status": "Pass"}
                _dbaasObj = self.mGetDbaasObj()
                _dbaasObj._mUpdateRequestData(self.mGetAoptions(), _rebalance_status, _eBoxCluCtrl)
                return _time_start
            else:
                return _time_start
        except Exception as ex:
            ebLogWarn(f"Could not update rebalance status in DB due to an exception - {ex}.")
            return _time_start

    # Common method to log error code and error message
    def mRecordError(self, aErrorObject, aString=None):

        _diskgroupData = self.mGetDiskGroupOperationData()

        _diskgroupData["Status"] = "Fail"
        _diskgroupData["ErrorCode"] = aErrorObject[0]
        if aString is None:
            _diskgroupData["Log"] = aErrorObject[1]
        else:
            _diskgroupData["Log"] = aErrorObject[1] + aString

        ebLogError("*** %s\n" % (_diskgroupData["Log"]))

        _errorCode = int(_diskgroupData["ErrorCode"], 16)
        if _errorCode != 0:
            return ebError(_errorCode)
        return 0
    # end

# end of ebCluSparseClone
