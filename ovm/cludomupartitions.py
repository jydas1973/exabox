"""
 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    OVM - Local Disk Partition Management on cluster nodes
          1. Resize
          2. Query Info

FUNCTION:
    Module to provide all the local disk partition management APIs

NOTE:
    None

History:
    bhpati    06/10/25 - Bug 38018344 - UPDATECVMLOCALSTORAGE FAILED FOR 
                         COULD NOT UNMOUNT FILESYSTEM U02
    rajsag    06/04/25 - Enhancement Request 38022921 support additional
                         response fields in exacloud status response for
                         reshape steps
    bhpati    11/08/24 - Enh 37224232 - RESILIENCY FOR LOCALSTORAGE UPDATE
                         WORKFLOW
    bhpati    09/10/24 - Bug 36915832: REQUEST TO INCLUDE NFS MOUNT PRECHECK 
                         DURING UPDATECVMLOCALSTORAGE OPERATIONS
    scoral    04/10/24 - Bug 36452330: Fix mClusterPartitionInfo2 for FS with
                         no LV. Now it returns the disk size if the FS is not
                         part of any LV.
                         Make mClusterPartitionTargetDiff very strict. Now it
                         decides to resize as long as there is any size diff.
    scoral    03/13/24 - Bug 36343989: Have mClusterPartitionInfo2 return the
                         PV size for _totalsizeGB_key instead of the filesystem
                         size to avoid confusion.
    scoral    10/12/23 - Bug 35851243 - Add more resilience to
                         mExecuteDomUUmountPartition.
    dekuckre  05/30/23 - 34851263: Add support for resize in reconfig flow.
    nmallego  06/21/21 - Bug32991330 - Referring path for ebCluPatchHealthCheck
    pverma    06/22/18 - Create file

Changelog:

   06/22/2018 - v1 changes:

       1) APIs for resize, info for a local disk partition
"""
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogJson, ebLogDebug, ebLogTrace, ebLogVerbose, ebLogWarn
from exabox.core.Context import get_gcontext
import json, math, re, time, os
from exabox.core.Error import gPartitionError , ebError, gReshapeError
from exabox.core.DBStore import ebGetDefaultDB
from exabox.ovm.clucontrol import exaBoxNode
from exabox.ovm.cludomufilesystems import get_disk_for_part_dev
from exabox.ovm.kvmdiskmgr import exaBoxKvmDiskMgr
from exabox.utils.node import node_exec_cmd_check, node_cmd_abs_path_check, connect_to_host
from exabox.infrapatching.core.clupatchhealthcheck import ebCluPatchHealthCheck
from exabox.ovm.utils.clu_utils import ebCluUtils
"""
class ebDomUPartitionOpConstants shall store literals for use by operations/actions
class ebCluManageDomUPartition
"""
# TODO Refactor this class to comply with python standards of implementing 
# constants 
class ebDomUPartitionOpConstants(object):
    def __init__(self):
        
        self._params_key = "params"
        
        self._partitionname_key = "partitionName"
        self._newsizeMB_key = "new_size"
        self._newsizeGB_key = "new_sizeGB"
        
        self._filesystem_key = "Filesystem"
        self._totalsizeGB_key = "total_sizeGB"
        self._usedsizeGB_key = "used_sizeGB"
        self._freepercent_key = "free_percent"
        
# end of ebDomUPartitionOpConstants            

"""
class ebCluManageDomUPartition implements local disk partition management functionalities:
(1) Resize Partition
(2) Fetch Info of a DomU local partition
                           
"""
class ebCluManageDomUPartition(object):

    def __init__(self, aExaBoxCluCtrl):

        self.__config = get_gcontext().mGetConfigOptions()
        self.__ebox = aExaBoxCluCtrl
        self.__domUs = []
        self.__jobid = None
        self.__logfile = None

        self.__ddpair = self.__ebox.mReturnDom0DomUPair()

        self.__verbose = self.__ebox.mGetVerbose()
        self.__debug = self.__ebox.mIsDebug()
        
        for _, _dU in self.__ddpair:
            self.__domUs.append(_dU)

        # Object to store results
        self.__partitionData = {}

        # Reference to hold reference of DomU on which last command was dispatched
        self._lastDomUused = None
        
        # Initialize the constants object
        self._constantsObj = ebDomUPartitionOpConstants() 

        self.__clu_utils = ebCluUtils(aExaBoxCluCtrl)
        
    def mGetEbox(self):
        return self.__ebox

    def mGetDomUs(self):
        return self.__domUs
    
    def mGetDom0DomUpairs(self):
        return self.__ddpair

    def mGetPartitionOperationData(self):
        return self.__partitionData

    def mSetPartitionOperationData(self, aPartitionData):
        self.__partitionData = aPartitionData

    def mGetLastDomUused(self):
        return self._lastDomUused
    
    def mSetLastDomUused(self, aDomU):
        self._lastDomUused = aDomU
        
    def mGetConstantsObj(self):
        return self._constantsObj   
    
    def mGetCluUtils(self):
        return self.__clu_utils  


    
    """
    Method mClusterManageDomUPartition is general entry point of any partition
    related operation.
    
    Params: (1) Dictionary containing properties related to the specific operation
    """
    def mClusterManageDomUPartition(self, aPartitionOp, aOptions):

        ebLogInfo("*** ebCluManageDomUPartition:mClusterManageDomUPartition >>>")
        _partitionOp = aPartitionOp
        _options = aOptions
        _rc = 0

        _partitionData = self.mGetPartitionOperationData()
        _partitionData['Status'] = "Pass"
        _eBoxCluCtrl = self.mGetEbox()

        if (not _partitionOp and _options.partitionOp is None):
            ebLogInfo("Invalid invocation or unsupported Partition LCM option")
            _partitionData["Log"] = "Invalid invocation or unsupported Partition LCM option"
            _partitionData["Status"] = "Fail"
            self._mUpdateRequestData(_options, _partitionData, _eBoxCluCtrl)
            return self.mRecordError(gPartitionError['InvalidOp'], "Partition LCM Step:\
             Unsupported")
        # Invoke right worker method
        if (_partitionOp == "resize"):
            ebLogInfo("Running Partition LCM Step: Resize Partition")
            _partitionData["Command"] = "partition_resize"
            _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("reshapeDetails", 'ONGOING', "OH reshape in progress", "","OH")
            self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, "OH Reshape", "In Progress", _stepSpecificDetails)
            self.mSetPartitionOperationData(_partitionData)
            if self.__ebox.mIsKVM():
                _exadiskobj = exaBoxKvmDiskMgr(self)
                _rc = _exadiskobj.mClusterPartitionResize(_options)
            else:
                _rc = self.mClusterPartitionResize(_options)
        elif (_partitionOp == "info"):
            ebLogInfo("Running Partition LCM Step: Fetching info of DomU local disk partition")
            _partitionData["Command"] = "partition_info"
            self.mSetPartitionOperationData(_partitionData)
            _rc = self.mClusterPartitionInfo(_options)
        else:
            ebLogInfo("Running Partition LCM step: Unsupported")
            _rc = self.mRecordError(gPartitionError['InvalidOp'], "Partition LCM Step:\
             Unsupported")

        self._mUpdateRequestData(_options, _partitionData, _eBoxCluCtrl)
        
        ebLogInfo("*** ebCluManageDomUPartition:mClusterManageDomUPartition <<<")

        return _rc
    # end mClusterManageDomUPartition


    """
     Method to parse input JSON and validate the arguments
     
     It also populates the JSON parameters into the 'aReqParams'
     based on module requirements. 
    """
    def mClusterParseInput(self, aOptions, aReqParams, aOpData=None):

        ebLogInfo("*** ebCluManageDomUPartition:mClusterParseInput >>>")
        _options = aOptions
        _reqparams = aReqParams
        # Get the constants object for use in the scope of this function
        _constantsObj = self.mGetConstantsObj()
        
        if aOpData is None:
            _op_data = self.mGetPartitionOperationData()
        else:
            _op_data = aOpData
            
        _partition_name_key_upper = (_constantsObj._partitionname_key).upper()
        _newsize_key_upper = (_constantsObj._newsizeGB_key).upper()

        # Input JSON file is required
        _inputjson = _options.jsonconf
        if not _inputjson:
            return self.mRecordError(gPartitionError['MissingInputPayload'])
        
        if _op_data["Command"] == "partition_resize":
            if "exaunitAllocations" in list(_inputjson.keys()) and "ohomeSizeGb" in _inputjson["exaunitAllocations"]:
                ebLogInfo("Parameters passed for resize as per reconfig flow")

            # Partition Size is a MUST for resize operation
            elif (_newsize_key_upper not in (key.upper() for key in list(_inputjson.keys())) or\
                 not _inputjson[_constantsObj._newsizeGB_key]):
                return self.mRecordError(gPartitionError['MissingPartitionSize'])
        
        for key in list(_inputjson.keys()):
            if _partition_name_key_upper == key.upper():
                _reqparams[_constantsObj._partitionname_key] = _inputjson[key]
            if _newsize_key_upper == key.upper():
                _reqparams[_constantsObj._newsizeGB_key] = _inputjson[key]
        if "exaunitAllocations" in list(_inputjson.keys()) and "ohomeSizeGb" in _inputjson["exaunitAllocations"]:
            _reqparams[_constantsObj._newsizeGB_key] = _inputjson["exaunitAllocations"]["ohomeSizeGb"]
            _reqparams[_constantsObj._partitionname_key] = "u02"
        
        ebLogInfo(f"*** ebCluManageDomUPartition:mClusterParseInput {_reqparams}<<<")
        return 0
    # end

    
    """
    Method to Resize a Partition
    """
    def mClusterPartitionResize(self, aOptions):

        ebLogInfo("*** ebCluManageDomUPartition:mClusterPartitionResize >>>")
        _options = aOptions
        # Get the cluctrl handle to fetch current details
        _eBoxCluCtrl = self.mGetEbox()
        # Get the constants object for use in the scope of this function
        _constantsObj = self.mGetConstantsObj()

        _partitionData = self.mGetPartitionOperationData()
        _partitionData["Status"] = "Pass"
        _partitionData["ErrorCode"] = "0"
        
        _partition_name_key = _constantsObj._partitionname_key 

        _inparams = {}
        _rc = self.mClusterParseInput(_options, _inparams)
        current_step = 0
        _percentage_increase = 0.0
        step_list = ["EvaluateResources", "PartitionResize", "Complete"]
        _lastNode = []
        if _rc == 0:
            _eBoxCluCtrl.mUpdateStatusOEDA(True, step_list[current_step], step_list, 
                                       ' Partition resize operation for ' + _inparams[_partition_name_key])
            _eBoxCluCtrl.mUpdateStatus('Partition resize operation for ' + _inparams[_partition_name_key] + ' performing step ' + step_list[current_step], False)    
            _dpairs = self.mGetDom0DomUpairs()
            shrink = 1
            _node_toUpdate_list = []  # list of node which will require resize
            max_used_space = 0
            existing_partition_info = {}
            image_names = {}    
            _percentageStepSize= 20.0/len(_dpairs)
            for _dom0, _domU in _dpairs: 
                ## 1. We fetch the size information of the mount-point to be resized from each node on the cluster
                ##    and perform checks if the same can be resized.
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("reshapeDetails", 'ONGOING', "OH reshape in progress", "","OH")
                self.mGetCluUtils().mUpdateTaskProgressStatus(_lastNode, _percentage_increase, "OH Reshape", "In Progress", _stepSpecificDetails)
                _percentage_increase = _percentage_increase + _percentageStepSize
                _lastNode.append(_domU) 
                _rc, _this_node_infoobj = self.mClusterPartitionInfo2(_options, _inparams[_partition_name_key], _domU)
                if _rc != 0:
                    _detail_error = 'Could not fetch information for partition ' + _inparams[_partition_name_key] + ' on ' + _domU
                    _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_FETCHING_PARTITION_INFO'], _detail_error)
                    return self.mRecordError(gPartitionError['ErrorFetchingDetails'], "*** " + _detail_error)
                if max_used_space < int(_this_node_infoobj[_constantsObj._usedsizeGB_key]): 
                    max_used_space = int(_this_node_infoobj[_constantsObj._usedsizeGB_key])
                
                existing_partition_info[_domU] = _this_node_infoobj
                _filesystem = _this_node_infoobj[_constantsObj._filesystem_key]
                _node = exaBoxNode(get_gcontext())
                _node.mConnect(aHost=_domU)
                
                ebLogInfo('*** Fetching raw device size of %s on Node %s' %(_filesystem, _domU))
                _cmdstr = '/sbin/fdisk -l \'' + _filesystem + '\' | /usr/bin/grep Disk'
                ## Sample output for "/sbin/fdisk -l /dev/xvdg | grep Disk"
                ##   [root@scas07adm03vm04 ~]#  /sbin/fdisk -l /dev/xvdg | grep Disk
                ##   Disk /dev/xvdg: 64.4 GB, 64424509440 bytes
                ##   Disk identifier: 0x00000000
                if self.__debug:
                    ebLogDebug("Executing cmd : %s"%(_cmdstr))
                _i, _o, _e = _node.mExecuteCmd(_cmdstr)
                _out = _o.readlines()
                _node.mDisconnect()
                if not _out:
                    self.logDebugInfo(_out, _e)
                    _detail_error = 'Could not fetch fdisk info for partition ' + _inparams[_partition_name_key] + ' on ' + _domU
                    _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_FETCHING_PARTITION_INFO'], _detail_error)
                    return self.mRecordError(gPartitionError['ErrorFetchingDetails'], "*** " + _detail_error)
                
                if self.__verbose and len(_out):
                    ebLogVerbose("Command output : " + '\n'.join(_out))
               
                # Sample output of cmd: /sbin/fdisk -l /dev/xvdh | grep Disk
                # Disk /dev/xvdh: 48.3 GB, 48318382080 bytes, 94371840 sectors
                _partitionAttrs = _out[0].strip().replace(","," ").split()  ## Take 1st line, remove "," by spaces, create list of output
                _index=_partitionAttrs.index("bytes") ## get the index of the "bytes" in the list
                # From above, size: 48318382080 bytes
                if _index > 0:
                    _partitionsize_bytes_domU = _partitionAttrs[_index - 1].strip() ## look for the value just before the string bytes
                else:
                    _detail_error = 'Could not read the disk size in bytes for partition ' + _inparams[_partition_name_key] + ' on ' + _domU
                    _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_READING_DISKSIZE'], _detail_error)
                    return self.mRecordError(gPartitionError['ErrorFetchingDetails'], "*** " + _detail_error)

                ebLogDebug("Fdisk info for FS %s on host %s : %s"%(_filesystem, _domU, _partitionAttrs))
        
                ## Save size for Dom U to cross-verify against size on Dom 0
                ## From above, size: 48318382080 bytes 
                _devname = _filesystem.split('/')[-1]
                _node = exaBoxNode(get_gcontext())
                _node.mConnect(aHost=_dom0)
                _vmPath = '/EXAVMIMAGES/GuestImages/' + _domU + '/vm.cfg'
                _cmdstr = '/usr/bin/grep ' + _devname + ' ' + _vmPath
                ebLogInfo('*** Fetching image size of %s used for device %s on Node %s' %(_vmPath, _devname, _dom0))
                if self.__debug:
                    ebLogDebug("Executing cmd : %s"%(_cmdstr))
                _i, _o, _e = _node.mExecuteCmd(_cmdstr)
                _out = _o.readlines()
                if not _out:
                    self.logDebugInfo(_out, _e)
                    _detail_error = 'Could not read device info for partition ' + _inparams[_partition_name_key] + ' in VM config on ' + _dom0
                    _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_READING_DEVICE_INFO'], _detail_error)
                    return self.mRecordError(gPartitionError['ErrorFetchingDetails'], "*** " + _detail_error)
                    
                if self.__verbose and len(_out):
                    ebLogVerbose("Command output : " + '\n'.join(_out))
                
                _attached_disks = _out[0].strip()
                _attached_disks = " ".join(_attached_disks.split())
                _attached_disks = _attached_disks.split('[')[1]
                _attached_disks = _attached_disks.split('\'')
                
                for _disk in _attached_disks:
                    _elements = _disk.split(',')
                    if _devname in _elements:
                        _image_name = _elements[0].split(':')[1]
                        _image_name = _image_name.replace('///','/')
                        break
                
                image_names[_domU] = _image_name
                _cmdstr = "/usr/bin/ls -l " + _image_name
                if self.__debug:
                    ebLogDebug("Executing cmd : %s"%(_cmdstr))
                _i, _o, _e = _node.mExecuteCmd(_cmdstr)
                _out = _o.readlines()
                if not _out:
                    self.logDebugInfo(_out, _e)
                    _detail_error = 'Could not retrieve device size for partition ' + _inparams[_partition_name_key] + ' from filesystem on ' + _dom0
                    _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_FETCHING_DEVICE_SIZE'], _detail_error)
                    return self.mRecordError(gPartitionError['ErrorFetchingDetails'], "*** " + _detail_error)
                
                if self.__verbose and len(_out):
                    ebLogVerbose("Command output : " + '\n'.join(_out))
                _partitionsize_bytes_dom0 = _out[0].strip()
                _partitionsize_bytes_dom0 = " ".join(_partitionsize_bytes_dom0.split())
                _partitionsize_bytes_dom0 = _partitionsize_bytes_dom0.split()[4]
                
                if _partitionsize_bytes_domU != _partitionsize_bytes_dom0:
                    _detail_error = 'Partition ' + _inparams[_partition_name_key] + ' has inconsistent size Dom 0 [' + _partitionsize_bytes_dom0 +'] and DomU [' + _partitionsize_bytes_domU + ']' 
                    _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_FETCHING_DEVICE_SIZE'], _detail_error)
                    return self.mRecordError(gPartitionError['InvalidState'], "*** " + _detail_error) 

                if self.mClusterPartitionTargetDiff(_this_node_infoobj[_constantsObj._totalsizeGB_key], _inparams[_constantsObj._newsizeGB_key]):
                    _node_toUpdate_list.append(_domU)
                    
                _node.mDisconnect()
                
            
            ebLogInfo("partition size from %s -> %s" %(_this_node_infoobj[_constantsObj._totalsizeGB_key], _inparams[_constantsObj._newsizeGB_key]))

            if int(_inparams[_constantsObj._newsizeGB_key]) > int(_this_node_infoobj[_constantsObj._totalsizeGB_key]):
                shrink = 0
                

            ## Shrink/Expand only if change in value is by at least 2% in any of the  node
            if  not _node_toUpdate_list:
                ebLogInfo("*** New partition size very close to original size. No resize done. Task completed")
                return 0

            if shrink == 1:
                ## Shrink only if it will leave >= 10% of free space after resize
                expected_fspace_on_resize = int(_inparams[_constantsObj._newsizeGB_key]) - int(max_used_space)
                if expected_fspace_on_resize < 0:
                    _detail_error = 'Partition ' + _inparams[_partition_name_key] + ' cannot be modified as it is smaller than current utilization'
                    _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_USAGE_SIZE_MORE'], _detail_error)
                    return self.mRecordError(gPartitionError['NonModifiable'], "*** " + _detail_error) 
                percent_fspace_on_resize = float(expected_fspace_on_resize * 100) / int(_inparams[_constantsObj._newsizeGB_key])
                if percent_fspace_on_resize < 10.0:
                    _detail_error = 'Partition ' + _inparams[_partition_name_key] + ' cannot be modified as it will leave less than 10% of free space after resize'
                    _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_LESS_FREE_SPACE'], _detail_error)
                    return self.mRecordError(gPartitionError['NonModifiable'], "*** " + _detail_error) 
                
            current_step += 1
            
            _eBoxCluCtrl.mUpdateStatusOEDA(True, step_list[current_step], step_list, 
                                       ' Partition resize operation for ' + _inparams[_partition_name_key]) 
            _eBoxCluCtrl.mUpdateStatus('Partition resize operation for ' + _inparams[_partition_name_key] + ' performing step ' + step_list[current_step], False)
            _percentage_increase = 20
            _percentageStepSize= 79.0/len(_dpairs)
            _lastNode = []
            for _dom0, _domU in _dpairs:
                ebLogInfo("*** Working on resize operation for (Dom-0, Dom-U) : (%s, %s)"%(_dom0, _domU))
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("reshapeDetails", 'ONGOING', "OH reshape in progress", "","OH")
                self.mGetCluUtils().mUpdateTaskProgressStatus(_lastNode, _percentage_increase, "OH Reshape", "In Progress", _stepSpecificDetails)
                _percentage_increase = _percentage_increase + _percentageStepSize
                _lastNode.append(_domU)
                if _domU not in _node_toUpdate_list:
                    if _eBoxCluCtrl.mCheckIfCrsDbsUp(_domU):
                        ebLogInfo("*** node already at the resize Value. Continuing with next node")
                        continue

                _this_node_infoobj = existing_partition_info[_domU]
                _filesystem = _this_node_infoobj[_constantsObj._filesystem_key]
                
                # perform shutdown
                _node = exaBoxNode(get_gcontext())
                _node.mConnect(aHost=_dom0)
                _crs_status, _db_status = _eBoxCluCtrl.mShutdownVMForReshape(_dom0,_domU,aOptions,_node)

                ebLogInfo("*** Resize partition : " + _inparams[_partition_name_key])
                _rc = self.mExecuteDomUResizeStepsOnDom0(_dom0, \
                                                       image_names[_domU], \
                                                       _inparams[_constantsObj._newsizeGB_key])
                if _rc != 0:
                    return _rc

                ebLogInfo('*** Starting VM %s after resize' %(_domU))
                _eBoxCluCtrl.mUpdateStatus('Starting VM %s after resize' %(_domU), False)
                _eBoxCluCtrl.mStartVMAfterReshape(_dom0,_domU, aOptions, _crs_status, _db_status, _node)
                _node.mDisconnect()
                _node = exaBoxNode(get_gcontext())
                _node.mConnect(aHost=_domU)                
                ebLogInfo('*** Fetching raw device size of %s on Node %s after resize' %(_filesystem, _domU))
                _cmdstr = '/sbin/fdisk -l \'' + _filesystem + '\' | /usr/bin/grep Disk'
                if self.__debug:
                    ebLogDebug("Executing cmd : %s"%(_cmdstr))
                _i, _o, _e = _node.mExecuteCmd(_cmdstr)
                _out = _o.readlines()
                if not _out:
                    self.logDebugInfo(_out, _e)
                    _detail_error = 'Could not fetch fdisk info for partition ' + _inparams[_partition_name_key] + ' on ' + _domU
                    _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_IMG_FILE_CHECK_FAILED'], _detail_error)
                    return self.mRecordError(gPartitionError['ErrorFetchingDetails'], "*** " + _detail_error)
                
                if self.__verbose and len(_out):
                    ebLogVerbose("Command output : " + '\n'.join(_out))
                    
                # Sample output of cmd: /sbin/fdisk -l /dev/xvdh | grep Disk
                # Disk /dev/xvdh: 48.3 GB, 48318382080 bytes, 94371840 sectors
                _partitionAttrs = _out[0].strip().replace(","," ").split()  ## Take 1st line, remove "," by spaces, create list of output
                _index=_partitionAttrs.index("bytes") ## get the index of the "bytes" in the list
                # From above, size: 48318382080 bytes
                if _index > 0:
                    _partitionsize_bytes_domU = _partitionAttrs[_index - 1].strip() ## look for the value just before the string bytes
                else:
                    _detail_error = 'Could not read the disk size in bytes for partition ' + _inparams[_partition_name_key] + ' on ' + _domU
                    _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_IMG_FILE_CHECK_FAILED'], _detail_error)
                    return self.mRecordError(gPartitionError['ErrorFetchingDetails'], "*** " + _detail_error)
                    
                _new_size_bytes = int(_inparams[_constantsObj._newsizeGB_key]) * 1024 * 1024 * 1024
        
                ## There should not be offset of more than 2% after resize
                if abs(int(_new_size_bytes) - int(_partitionsize_bytes_domU)) * 100.0 / float(_partitionsize_bytes_domU) > 2.0: 
                    _detail_error = 'Image not properly resized on ' + _domU
                    _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_RESIZE_NOT_PROPER'], _detail_error)
                    return self.mRecordError(gPartitionError['ImageResizeFailed'], "*** " + _detail_error)
                
                _eBoxCluCtrl.mUpdateStatus('Performing filesystem check of ' + _filesystem + ' on ' + _domU + ' after resize', False)
                ebLogInfo("*** Performing filesystem check of " + _filesystem + " on " + _domU + " after resize")
                _cmdstr = "/usr/sbin/e2fsck -f " + _filesystem
                if self.__debug:
                    ebLogDebug("Executing cmd : %s"%(_cmdstr))
                _i, _o, _e = _node.mExecuteCmd(_cmdstr)
                _out = _o.readlines()
                if not _out:
                    self.logDebugInfo(_out, _e)
                    _detail_error = 'Could not perform filesystem check on ' + _domU + ' for filesystem ' + _filesystem
                    _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_FILE_SYS_CHECK_FAILED'], _detail_error)
                    return self.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)
                
                if self.__verbose and len(_out):
                    ebLogVerbose("Command output : " + '\n'.join(_out))
                    
                for outentry in _out:
                    if re.search("errors", outentry):
                        _detail_error = 'Errors found in filesystem check on ' + _domU + ' for filesystem ' + _filesystem
                        _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_FILE_SYS_CHECK_FAILED'], _detail_error)
                        return self.mRecordError(gPartitionError['InvalidState'], "*** " + _detail_error)
                _eBoxCluCtrl.mUpdateStatus('Mounting filesystem ' + _filesystem + ' on ' + _domU + ' after resize', False)
                ebLogInfo("*** Mounting filesystem " + _filesystem + " on " + _domU + " after resize")
                _cmdstr = "/usr/bin/mount " + _this_node_infoobj[_constantsObj._filesystem_key] + " /" + _inparams[_partition_name_key]
                if self.__debug:
                    ebLogDebug("Executing cmd : %s"%(_cmdstr))
                _i, _o, _e = _node.mExecuteCmd(_cmdstr)
                _out = _o.readlines()
                _exitstatus = _node.mGetCmdExitStatus()
                # Escape error out if the cmd executed with success or if the file system was 
                # already mounted (exit status: 32).
                if _exitstatus != 0 and _exitstatus != 32:
                    self.logDebugInfo(_out, _e)
                    _detail_error = 'Could not mount filesystem ' + _inparams[_partition_name_key] + ' on ' + _domU 
                    _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_MOUNTING_FILE_SYS'], _detail_error)
                    return self.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)
                    
                if _inparams[_partition_name_key] == 'u02' :
                    ebLogInfo("*** Resize was done for u02")
                    
                _node.mDisconnect()
                ebLogInfo("*** DONE with resize operation for (Dom-0, Dom-U) : (%s, %s)"%(_dom0, _domU))
                    
            # end for    
                              
        else:
            _detail_error = 'Returning due to input args related error' 
            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['INVALID_INPUT_PARAMETER'], _detail_error)
            ebLogError(_detail_error)
            return _rc
        
        current_step += 1
        _eBoxCluCtrl.mUpdateStatusOEDA(True, step_list[current_step], step_list, 
                                       ' Partition resize operation for ' + _inparams[_partition_name_key])
        _eBoxCluCtrl.mUpdateStatus('Partition resize operation for ' + _inparams[_partition_name_key] + ' performing step ' + step_list[current_step], False)    
        ebLogInfo("*** ebCluManageDomUPartition:mClusterPartitionResize <<<")
        _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("reshapeDetails", 'DONE', "OH reshape completed", "","OH")
        self.mGetCluUtils().mUpdateTaskProgressStatus(_lastNode, 100, "OH Reshape", "DONE", _stepSpecificDetails)
        return 0

    # end

    """
    Return true if the difference between current size value and target size value is greater than 0%
    """
    def mClusterPartitionTargetDiff(self, currentSize, newSize):

        ebLogInfo("*** ebCluManageDomUPartition:mClusterPartitionTargetDiff >>>")
        # Get the cluctrl handle to fetch current details
        _eBoxCluCtrl = self.mGetEbox()
        ebLogInfo("*** Current Size = %s and New Size= %s"%(currentSize, newSize))
        ret = False
        if _eBoxCluCtrl.mCheckConfigOption('disable_lvm_snapshot_space','True'):
            size_diff = abs(int(currentSize) - int(newSize))
        else:
            size_diff = abs(int(currentSize) + 2 - int(newSize))
        percentageChange = float(size_diff * 100) / int(currentSize)
        if percentageChange > 0:
            ebLogInfo("*** ebCluManageDomUPartition:mClusterPartitionTargetDiff:Resize needed on this")
            ret = True
        else:
            ebLogInfo("*** ebCluManageDomUPartition:mClusterPartitionTargetDiff:Resize not needed on this node")
            ret = False

        ebLogInfo("*** ebCluManageDomUPartition:mClusterPartitionTargetDiff <<<")
        return ret


    
    """
    Fetches the partition information from all nodes of a cluster
    """
    def mClusterPartitionInfo(self, aOptions):
        
        ebLogInfo("*** ebCluManageDomUPartition:mClusterPartitionInfo >>>")
        _options = aOptions
        # Get the cluctrl handle to fetch current details
        _eBoxCluCtrl = self.mGetEbox()
        # Get the constants object for use in the scope of this function
        _constantsObj = self.mGetConstantsObj()

        _partitionData = self.mGetPartitionOperationData()
        _partitionData["Status"] = "Pass"
        _partitionData["ErrorCode"] = "0"
        
        _partition_name_key = _constantsObj._partitionname_key 

        _inparams = {}
        _rc = self.mClusterParseInput(_options, _inparams)
        step_list = ["InfoFetch", "Complete"]
        if _rc == 0:
            _eBoxCluCtrl.mUpdateStatusOEDA(True, "InfoFetch", step_list, 
                'Partition Info Fetch operation for ' + _inparams[_partition_name_key])
            _eBoxCluCtrl.mUpdateStatus('Partition Info Fetch operation for ' + _inparams[_partition_name_key], False) 
            _domUs = self.mGetDomUs()
            _infoobj = {}
            _infoobj[_partition_name_key] = _inparams[_partition_name_key]
            for _domU in _domUs:
                _rc, _this_node_infoobj = self.mClusterPartitionInfo2(_options, _inparams[_partition_name_key], _domU)
                if _rc != 0:
                    return _rc
                _infoobj[_domU] = _this_node_infoobj
            
            _partitionData["PartitionInfo"] = _infoobj
        else:
            ebLogError("Returning due to input args related error")
            return _rc
        
        ebLogInfo(json.dumps(_infoobj, indent=4, sort_keys=True))
        
        _eBoxCluCtrl.mUpdateStatusOEDA(True, "Complete", step_list,
                                        'Partition Info Fetch operation for '
                                         + _inparams[_partition_name_key])
        _eBoxCluCtrl.mUpdateStatus('Partition Info Fetch operation for ' + _inparams[_partition_name_key] + 'completed', False)
        ebLogInfo("*** ebCluManageDomUPartition:mClusterPartitionInfo <<<")
        
        return _rc
    # end


    """
    Does following in that order on a given DomU:
    (1) Check if there are any child mounts from  the mount-point to be resized.
    (2) Check if there are processes accessing any file from the mount-point to be resized; kill if there are any
    (3) Unmount it
    """
    def mExecuteDomUUmountPartition(self, aDomU, aPartitionName):
        _domU = aDomU
        _partitionName = aPartitionName
        _eBoxCluCtrl = self.mGetEbox()
        with connect_to_host(_domU, _eBoxCluCtrl.mGetCtx()) as _node:
            _child_mounts = self.mCheckChildMounts(_node,_partitionName)
            if _child_mounts:
                _detail_error = f"Child Mounts {', '.join(_child_mounts)} exists on /{_partitionName}. Could not unmount filesystem /{_partitionName} on {_domU}"
                _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_MOUNTING_FILE_SYS'], _detail_error)
                return self.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)
            
            self.mCheckTerminateProcess(_node, _partitionName, 15)
            self.mCheckTerminateProcess(_node, _partitionName, 9) 
            ebLogInfo("*** Unmounting partition " + _partitionName + " on " + _domU)
            _timeStart = time.time()
            _timeoutSeconds = 60
            while True:
                # Terminate all processes again and unmount the filesystem
                self.mCheckTerminateProcess(_node, _partitionName, 9)
                _cmdstr = "/usr/bin/umount /" + _partitionName
                if self.__debug:
                    ebLogDebug("Executing cmd : %s"%(_cmdstr))
                _i, _o, _e = _node.mExecuteCmd(_cmdstr)
                _out = _o.readlines()

                # Check if still mounted
                _findmnt = node_cmd_abs_path_check(_node, "findmnt", sbin=True)
                _cmdstr = f"{_findmnt} /{_partitionName}"
                _i, _o, _e =_node.mExecuteCmd(_cmdstr)
                _out = _o.readlines()
                ebLogTrace(f"*** Command '{_cmdstr}' output: {_out} Error: {str(_e)}")
                if _node.mGetCmdExitStatus() != 0:
                    ebLogInfo("*** Unmounted partition " + _partitionName + " on " + _domU)
                    break

                # Timeout failure
                _now = time.time()
                if _now - _timeStart > _timeoutSeconds:
                    _lsof = "/usr/sbin/lsof"
                    _checklsof = "/usr/bin/ls -l " + _lsof
                    ebLogDebug("Executing cmd : %s"%(_checklsof))
                    _i, _o, _e = _node.mExecuteCmd(_checklsof)
                    if _node.mGetCmdExitStatus() != 0:
                        _lsof = "/usr/bin/lsof"
                    _cmd1 = "/usr/bin/df -kHP"
                    _cmd2 = _lsof + " -t /" + _partitionName
                    _cmd3 = "/usr/bin/ls -l /" + _partitionName
                    _i, _o1, _e = _node.mExecuteCmd(_cmd1)
                    _out1 = _o1.readlines()
                    ebLogInfo("*** Output of the %s is :%s"%(_cmd1,_out1))
                    _i, _o1, _e = _node.mExecuteCmd(_cmd2)
                    _out1 = _o1.readlines()
                    ebLogInfo("*** Output of the %s is :%s"%(_cmd2,_out1))
                    _i, _o1, _e = _node.mExecuteCmd(_cmd3)
                    _out1 = _o1.readlines()
                    ebLogInfo("*** Output of the %s is :%s"%(_cmd3,_out1))
                    self.logDebugInfo(_out, _e)
                    _detail_error = 'Could not unmount filesystem ' + _partitionName + ' on ' + _domU
                    _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_MOUNTING_FILE_SYS'], _detail_error)
                    return self.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)

            if self.__verbose and _out is not None and len(_out):
                ebLogVerbose("Command output : " + '\n'.join(_out))
            ebLogInfo("*** Waiting for 45 second after umount")
            time.sleep(45) # delay after umount
            return 0
    # end

    """
    check if there are child mounts on PartitionName
    """
    def mCheckChildMounts(self, aNode, aPartitionName):
        _node = aNode
        _partitionName = aPartitionName
        _findmnt = node_cmd_abs_path_check(aNode, "findmnt", sbin=True)
        ebLogInfo("*** Checking if there are child mounts out of the partition /" + _partitionName)
        # Command to find child mounts
        _cmdstr = f"{_findmnt} --output TARGET --noheadings -R -r /{_partitionName}"
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        _child_mounts = []
        if _node.mGetCmdExitStatus() == 0:
            _out = _o.readlines()
            _child_mounts = [line.split(' ')[0].strip() for line in _out if line]
            if _child_mounts:
                _child_mounts.pop(0)
        else:
             ebLogWarn(f"*** findmnt command: {_cmdstr} failed with message: {str(_e.readlines())}")

        # Return the list of child paths
        return _child_mounts

    """
    check and kill running processes with provide kill code
    """
    def mCheckTerminateProcess(self, aNode, aPartitionName, aSignal):
        _node = aNode
        _partitionName = aPartitionName
        _lsof = "/usr/sbin/lsof"
        _checklsof = "/usr/bin/ls -l " + _lsof
        ebLogDebug("Executing cmd : %s"%(_checklsof))
        _i, _o, _e = _node.mExecuteCmd(_checklsof)
        if _node.mGetCmdExitStatus() != 0:
            _lsof = "/usr/bin/lsof"
        ebLogInfo("*** Checking if processes running out of the partition " + _partitionName)
        _cmdstr = _lsof + " -t /" + _partitionName
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)

        _out = _o.readlines()
        if _out:
            ## issue command to kill running process
            _cmdstr = "{0} -t /{1} | /usr/bin/xargs /bin/sudo kill -{2} ".format(_lsof,_partitionName, aSignal)
            ebLogInfo("*** Kill PIDs " + str(_out))
            _i, _o, _e = _node.mExecuteCmd(_cmdstr)
            _out = _o.readlines()
            if _node.mGetCmdExitStatus() != 0:
                ebLogInfo("*** Output of the kill command %s is : %s : the message is :%s"%(_cmdstr, str(_out), str(_e.readlines())))

    """
    Does following in that order on a given DomU via Dom0:
    (1) Perform file system check on the device file which was used for the mount-point
    (2) Resize filesystem on the device file
    """
    def mExecuteDomUResizeStepsOnDom0(self, aDom0, aImageName, aNewSizeGB):
        _dom0 = aDom0
        _image_name = aImageName
        _new_sizeGB = aNewSizeGB
        _eBoxCluCtrl = self.mGetEbox() 
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_dom0)
        
        ebLogInfo("*** Performing ImageFile check of " + _image_name + " on " + _dom0)
        _cmdstr = "/sbin/e2fsck -fy " + _image_name
        if self.__debug:
            ebLogDebug("Executing cmd : %s"%(_cmdstr))
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        _out = _o.readlines()
        if not _out:
            self.logDebugInfo(_out, _e)
            _detail_error = 'Could not perform ImageFile check on ' + _dom0 + ' for ImageFile ' + _image_name
            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_IMG_FILE_CHECK_FAILED'], _detail_error)
            return self.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)
            
        if self.__verbose and len(_out):
            ebLogVerbose("Command output : " + '\n'.join(_out))
        
        for outentry in _out:
            if re.search("errors", outentry):
                _detail_error = 'Errors found in ImageFile check on ' + _dom0 + ' for ImageFile ' + _image_name
                _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_IMG_FILE_CHECK_FAILED'], _detail_error)
                return self.mRecordError(gPartitionError['InvalidState'], "*** " + _detail_error)
        
        ebLogInfo("*** Performing ImageFile resize of " + _image_name + " on " + _dom0)
        _cmdstr = "/sbin/e2fsck -fy " + _image_name + ";" + "/sbin/resize2fs -f " + _image_name + " " + str(_new_sizeGB) + "G"
        ebLogDebug("Executing cmd : %s"%(_cmdstr))
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        _out = _o.readlines()
        if _node.mGetCmdExitStatus() != 0:
            self.logDebugInfo(_out, _e)
            _detail_error = 'Could not perform ImageFile check on ' + _dom0 + ' for ImageFile ' + _image_name
            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_IMG_FILE_CHECK_FAILED'], _detail_error)
            return self.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], "*** " + _detail_error)
        
        return 0
    # end
    
    
    """
    Does following in that order on a given Dom0:
    (1) Establish relation between image-file (attached to DomU as disk), loop device and xen device ID 
    (2) Detach the xen block device
    (3) Delete the corresponding loop device
    (4) Resize the image file
    (5) Re-attach the block device
    """
    def mExecuteDom0ResizeSteps(self, aDom0, aDomU, aFilesystem, aNewSizeGB, aImageName):
        _dom0 = aDom0
        _domU = aDomU
        _filesystem = aFilesystem
        _new_sizeGB = aNewSizeGB
        _image_name = aImageName
        
        _devname = _filesystem.split('/')[-1]
        
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_dom0)
        
        ebLogInfo("*** Getting block device IDs for " + _domU + " on " + _dom0)
        _cmdstr = "xm block-list " + _domU
        if self.__debug:
            ebLogDebug("Executing cmd : %s"%(_cmdstr))
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        _out = _o.readlines()
        if not _out:
            self.logDebugInfo(_out, _e)
            return self.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], 
                "*** Could not fetch block devices list for " + _domU + " on " + _dom0)
        
        if self.__verbose and len(_out):
            ebLogVerbose("Command output : " + '\n'.join(_out))
        
        _blockdevices =  _out
        ebLogInfo("*** Getting xenstore dump from " + _dom0)
        _cmdstr = "xenstore ls"
        if self.__debug:
            ebLogDebug("Executing cmd : %s"%(_cmdstr))
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        _out = _o.readlines()
        if not _out:
            self.logDebugInfo(_out, _e)
            return self.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], 
                "*** Could not get xenstore dump on " + _dom0)
        
        if self.__verbose and len(_out):
            ebLogVerbose("Command output : " + '\n'.join(_out))
        
        _xenstore_dump = _out
        
        _vdev = None
        _loopdevice = None
        
        ## For each xen device id (of the attached block devices in the VM)
        ##  (1)   Identify the details block in the xenstore
        ##  (2)   Check if the block is for the VM (domain) in question
        ##  (3)   If (2) is true, check if the block is for virtual device (xvd*) as 
        ##        which the image is virtually presented inside the guest (VM) 
        ##  (4)   If (2) and (3) are true, save the loop device (parameter 'node' in xenstore)
        for _dev in _blockdevices[1:]: ## Skip first line (header)
            if _loopdevice is not None:
                break
            
            _vdev = _dev.strip()
            _vdev = " ".join(_vdev.split())
            _vdev = _vdev.split(' ')[0]
            _check_domain = 0
            _save_loopdevice = 0
            _check_devname = 0
            for _raw_entry in _xenstore_dump:
                _expected_entry = None
                _raw_entry = _raw_entry.strip()
                if _save_loopdevice == 1:
                    if re.search("node = ", _raw_entry):
                        _loopdevice = _raw_entry.split('"')[1].lstrip().rstrip()
                        break
                    else:
                        continue
                
                if _check_devname == 1:
                    if re.search("dev = ", _raw_entry):
                        if _raw_entry.split('"')[1].lstrip().rstrip() == _devname:
                            _save_loopdevice = 1
                            continue
                        else:
                            break
                    else:
                        continue
                        
                if _check_domain == 1:
                    _expected_entry = "domain = \"" + _domU + "\""
                else:
                    _expected_entry = str(_vdev) + " = \"\""
                
                                    
                if _check_domain == 0 and _raw_entry == _expected_entry:
                    _check_domain = 1
                    continue
                
                if _check_domain == 1:
                    if _raw_entry == _expected_entry:
                        _check_devname = 1
                        continue
                    else:
                        _check_domain = 0 ## Multiple hosts may have same IDs
            # end inner for
        # end outer for
        
        ebLogInfo("*** Detaching block device ID " + str(_vdev)  + " from  " + _domU + " on " + _dom0)
        _cmdstr = "xm block-detach " + _domU + " " + str(_vdev)
        if self.__debug:
            ebLogDebug("Executing cmd : %s"%(_cmdstr))
        for _index in range(0,3):
             _i, _o, _e = _node.mExecuteCmd(_cmdstr)
             _out = _o.readlines()
             _msg = str(_e.readlines())
             if _node.mGetCmdExitStatus() != 0:
                 self.logDebugInfo(_out, _e)
                 if 'Device busy' in _msg: 
                       if _index < 2:
                           ebLogInfo("*** Retry Detach block device again")
                           time.sleep(120) # retry after 2 mins incase of device busy
                           continue
                       else:
                           return self.mRecordError(gPartitionError['ErrorRunningRemoteCmd'],
                                        "*** Could not detach block device from " + _domU + " on " + _dom0)
                 elif 'not connected' in _e:
                       break
                 else:
                       return self.mRecordError(gPartitionError['ErrorRunningRemoteCmd'],
                                        "*** Could not detach block device from " + _domU + " on " + _dom0)
             else:
                  self.logDebugInfo(_out, _e)
                  break       
            
        if self.__verbose and _out is not None and len(_out):
            ebLogVerbose("Command output : " + '\n'.join(_out))
        
        ## Check if loop device is available
        ## If available, we detach it in next step
        _detach_loopdevice = 1
        ebLogInfo("*** Verifying loop device before attempting to detach on " + _dom0)
        _cmdstr = "/sbin/losetup " + _loopdevice
        if self.__debug:
            ebLogDebug("Executing cmd : %s"%(_cmdstr))
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        _out = _o.readlines()
        if _node.mGetCmdExitStatus() != 0:
            for _entry in _e.readlines():
                if (re.search("No such device or address", _entry)):
                    _detach_loopdevice = 0
                    break

        if self.__verbose and len(_out):
            ebLogVerbose("Command output : " + '\n'.join(_out))
        
        if _detach_loopdevice == 1: 
            ebLogInfo("*** Detaching loop device " + _loopdevice + " on " + _dom0)
            _cmdstr = "/sbin/losetup -d " + _loopdevice
            if self.__debug:
                ebLogDebug("Executing cmd : %s" % (_cmdstr))
            _i, _o, _e = _node.mExecuteCmd(_cmdstr)
            _out = _o.readlines()
            if _node.mGetCmdExitStatus() != 0:
                _ignore = 0
                for _line in _e.readlines():
                    if (re.search("No such device or address", _line)):
                        _ignore = 1
                if _ignore == 0:
                    return self.mRecordError(gPartitionError['ErrorRunningRemoteCmd'],
                        "*** Could not detach loop device on " + _dom0)
            if self.__verbose and _out is not None and len(_out):
                ebLogVerbose("Command output : " + '\n'.join(_out))
            
        ebLogInfo("*** Verifying loop device change for " + _loopdevice + " on " + _dom0)
        _cmdstr = "/sbin/losetup -a"
        if self.__debug:
            ebLogDebug("Executing cmd : %s"%(_cmdstr))
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        _out = _o.readlines()
        if not _out:
            self.logDebugInfo(_out, _e)
            return self.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], 
                "*** Could not run loop device info  command on " + _dom0)
        for _entry in _out:
            if re.search(_loopdevice, _entry):
                return self.mRecordError(gPartitionError['InvalidState'], 
                "*** Loop device " + _loopdevice + " still present on " + _dom0)
        
        if self.__verbose and len(_out):
            ebLogVerbose("Command output : " + '\n'.join(_out))
        
        ebLogInfo("*** Resizing image " + _image_name + " on " + _dom0)
        _cmdstr = "qemu-img resize " + _image_name +  " " + str(_new_sizeGB) + "G"
        if self.__debug:
            ebLogDebug("Executing cmd : %s"%(_cmdstr))
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        _out = _o.readlines()
        if _node.mGetCmdExitStatus() != 0:
            self.logDebugInfo(_out, _e)
            return self.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], 
                "*** Could not resize image on " + _dom0)
        
        ebLogInfo("*** Validating Resized image " + _image_name + " on " + _dom0)
        _cmdstr = "/usr/bin/ls -l " + _image_name
        if self.__debug:
            ebLogDebug("Executing cmd : %s"%(_cmdstr))
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        _out = _o.readlines()
        if not _out:
            self.logDebugInfo(_out, _e)
            return self.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], 
                "*** Could not get details of image from " + _dom0)
            
        if self.__verbose and len(_out):
            ebLogVerbose("Command output : " + '\n'.join(_out))
        
        _image_size = _out[0].strip()
        _image_size = " ".join(_image_size.split())
        _image_size = _image_size.split()[4].lstrip().rstrip()
        _new_size_bytes = int(_new_sizeGB) * 1024 * 1024 * 1024
        
        if abs(int(_new_size_bytes) - int(_image_size)) * 100.0 / float(_image_size) > 2.0: ## There should not offset of more than 2% after resize
            return self.mRecordError(gPartitionError['ImageResizeFailed'], 
                "*** Image not properly resized on " + _dom0)
        
        ebLogInfo("*** Attaching block device " + _loopdevice  + " to  " + _domU + " on " + _dom0)
        _cmdstr = "xm block-attach " + _domU + " " + "file:" + _image_name + " " + _devname + " w"
        if self.__debug:
            ebLogDebug("Executing cmd : %s"%(_cmdstr))
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        _out = _o.readlines()
        if _node.mGetCmdExitStatus() != 0:
            self.logDebugInfo(_out, _e)
            return self.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], 
                "*** Could not attach block device to " + _domU + " on " + _dom0)
        
        ## Loop device should automatically be added as part of xm block-attach
        ebLogInfo("*** Verifying loop device change for " + _loopdevice + " on " + _dom0)
        _cmdstr = "/sbin/losetup " + _loopdevice
        if self.__debug:
            ebLogDebug("Executing cmd : %s"%(_cmdstr))
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        _out = _o.readlines()
        if not _out:
            self.logDebugInfo(_out, _e)
            return self.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], 
                "*** Could not run loop device management command on " + _dom0)
        
        if self.__verbose and _out is not None and len(_out):
            ebLogVerbose("Command output : " + '\n'.join(_out))
        
        for _entry in _out:
            if not re.search(_loopdevice, _entry):
                return self.mRecordError(gPartitionError['LoopDeviceErr'], 
                    "*** Could not add loop device on " + _dom0)
        
        if self.__verbose and _out is not None and len(_out):
            ebLogVerbose("Command output : " + '\n'.join(_out))
                
        return 0
    # end
    
    
    """
    Fetches the follwoing details for a given partition on the specified host
    (1) Filesystem
    (2) Total Size
    (3) Used Size
    (4) Percentage Free
    """
    def mClusterPartitionInfo2(self, aOptions, aPartition, aHost):
        
        ebLogInfo("*** ebCluManageDomUPartition:mClusterPartitionInfo2 >>>")
        _options = aOptions
        # Get the cluctrl handle to fetch current details
        _eBoxCluCtrl = self.mGetEbox()
        # Get the constants object for use in the scope of this function
        _constantsObj = self.mGetConstantsObj()
        
        _partitionName = aPartition
        _host = aHost
        
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_host)
            
        ebLogInfo('*** Checking details for local partition %s on Node %s' %(_partitionName, _host))
        _cmdstr = '/usr/bin/df -h -B G -P ' + '/' + _partitionName + ' | /usr/bin/grep ' + _partitionName
        ## Sample output for "df -hB G -P /scratch"
        ##   Filesystem     1G-blocks  Used Available Use% Mounted on
        ##   /dev/vdb            178G   12G      157G   8% /scratch
        if self.__debug:
            ebLogDebug("Executing cmd : %s"%(_cmdstr))
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        _out = _o.readlines()
        if len(_out) == 0:
            self.logDebugInfo(_out, _e)
            _mntcmdstr =  '/usr/bin/mount ' + '/' + _partitionName
            ebLogInfo(f"Filesystem /{_partitionName} to be resized is not mounted on {_host}. Trying to mount /{_partitionName}")
            _i, _o, _e = _node.mExecuteCmd(_mntcmdstr)
            _exitstatus = _node.mGetCmdExitStatus()
            _out = _o.readlines()
            if _exitstatus != 0 and _exitstatus != 32:
                self.logDebugInfo(_out, _e)
                ebLogWarn(f"Could not mount filesystem /{_partitionName} on {_host}")
            else:
                ebLogInfo(f"Filesystem /{_partitionName} to be resized is mounted on {_host}")
            _i, _o, _e = _node.mExecuteCmd(_cmdstr)
            _out = _o.readlines()
            if len(_out) == 0:
                self.logDebugInfo(_out, _e)
                _detail_error = 'Could not fetch info for partition ' + _partitionName + ' on ' + _host + './' + _partitionName + ' is not mounted'
                _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_FETCHING_PARTITION_INFO'], _detail_error)
                return 1, self.mRecordError(gPartitionError['ErrorFetchingDetails'], "*** " + _detail_error)
        
        if self.__verbose and len(_out):
            ebLogVerbose("Command output : " + '\n'.join(_out))
        
        _partitionAttrs = _out[0].strip()  ## Take the only line
        
        ebLogDebug("Extracting partition properties from line %s"%(_partitionAttrs))
        _partitionAttrs = " ".join(_partitionAttrs.split())
        
        _filesystem = _partitionAttrs.split()[0].strip()
        _tspace = _partitionAttrs.split()[-5].strip()[:-1]
        _uspace = _partitionAttrs.split()[-4].strip()[:-1]
        _percent_fspace = 100 - int(_partitionAttrs.split()[-2].strip()[:-1])

        # For filesystems within a logical volume, we will obtain the size of
        # its corresponding phisical volume, which is the same value that the
        # customer sees in the UI.
        if '-' in _filesystem:
            _vg = _filesystem.split('/')[-1].split('-')[0]
            _cmd = f"/sbin/pvs --noheadings --units B -o size -S vg_name={_vg}"
            _out = node_exec_cmd_check(_node, _cmd).stdout
            _disk_gib = math.ceil(int(_out.strip()[:-1]) / 2**30)
        # For filesystems withing a phisical disk partition, we will obtain the
        # disk size, which is the same value that the customer sees in the UI.
        else:
            _disk_dev = get_disk_for_part_dev(_node, _filesystem)
            _cmd = f"/sbin/fdisk -l | /bin/grep 'Disk {_disk_dev}'"
            _out = node_exec_cmd_check(_node, _cmd).stdout
            _disk_gib = math.ceil(int(_out.split(',')[1].split()[0]) / 2**30)
        _node.mDisconnect()

        _partition_info = {}
        _partition_info[_constantsObj._filesystem_key] = _filesystem
        _partition_info[_constantsObj._totalsizeGB_key] = _disk_gib
        _partition_info[_constantsObj._usedsizeGB_key] = _uspace
        _partition_info[_constantsObj._freepercent_key] = _percent_fspace
        
        ebLogDebug(json.dumps(_partition_info, indent=4, sort_keys=True))
        
        ebLogInfo("*** ebCluManageDomUPartition:mClusterPartitionInfo <<<")
        return 0, _partition_info
    # end
    
    
    """
    Creates a mirror of the specified imagefile on given Dom-0 using 'reflink'
    for backup purposes
    """
    def mExecuteMirrorDom0imageFileForBackup(self, aDom0, aImageName):
        _dom0 = aDom0
        _image_name = aImageName
        
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_dom0)
        
        ts = time.time()
        _mirror_file = _image_name + ".mirror." + str(ts)
        ebLogInfo("*** Creating reflink mirror of image file " + _mirror_file + " on " + _dom0)
        if self.__ebox.mIsKVM():
            _cmdstr = "/usr/bin/cp --reflink " + _image_name + " " + _mirror_file
        else:
            _cmdstr = "reflink " + _image_name + " " + _mirror_file
        if self.__debug:
            ebLogDebug("Executing cmd : %s"%(_cmdstr))
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)

        if _node.mGetCmdExitStatus() != 0:
            self.logDebugInfo(None, _e)
            return self.mRecordError(gPartitionError['ErrorRunningRemoteCmd'], 
                "*** Could not create reflink mirror of image file " + _image_name + " on " + _dom0)
            
        return 0
        
    # end
    
    
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
    # end
    
    
    # Common method to log error code and error message
    def mRecordError(self, aErrorObject, aString=None):

        _partitionData = self.mGetPartitionOperationData()

        _partitionData["Status"] = "Fail"
        _partitionData["ErrorCode"] = aErrorObject[0]
        _errorCode = int(_partitionData["ErrorCode"], 16)
        if aString is None:
            _partitionData["Log"] = aErrorObject[1]
        else:
            _partitionData["Log"] = aErrorObject[1] + "\n" + aString

        ebLogError("*** %s\n" % (_partitionData["Log"]))

        if int(_partitionData["ErrorCode"]) != 0:
            return ebError(_errorCode)
        return 0
    # end
    
    
    #
    def logDebugInfo(self, aOutLines=None, aErrorStream=None):
        _outLines = aOutLines
        _errorStream = aErrorStream
        
        ebLogDebug("Command Output : ")
        if _outLines and len(_outLines):
            for _line in _outLines:
                ebLogDebug(_line)
        
        if _errorStream is not None:
            ebLogDebug("Command Error : ")
            _err = _errorStream.readlines()
            for _line in _err:
                ebLogDebug(_line)
        
    # end
    
# end of ebCluManageDomUPartition
