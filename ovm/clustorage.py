"""
$Header:

 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    OVM - Basic Storage functionality

FUNCTION:
    Provide basic/core API for managing Storage

NOTE:
    None

History:

    MODIFIED   (MM/DD/YY)
      jfsaldan  10/28/25 - Bug 38550997 - THE SHRINK BACK TO ORIGINAL SIZE STEP
                           WILL FAIL WHILE NO MORE THAN 15% FREESPACE |
                           EXACLOUD TO SUPPORT NEW FLAG IN ASM RESHAPE TO
                           CALCULATE NEW TARGET SIZE IF ORIGINAL SIZE CANNOT BE
                           SATISFIED W/CURRENT USED SPACE
      rajsag    09/15/25 - Enh 38406726 - ASM RESHAPE: DO NOT SET SET THE NEW
                           SPARSE VALUE TO BE 2 TIMES OF THE USED SPACE INCASE
                           OF UPSIZE REQUEST
      gparada  08/15/25 - 38254024 Reshape - Dynamic Storage for data reco sparse 
      naps     08/14/25 - Bug 38151629 - Fix the multiprocessing logic in pmem
                        disk handling.
      gparada  08/11/25 - 38253988 Dynamic Storage for data reco sparse in CS flow
      rajsag    06/04/25 - ER 37542345 - SUPPORT ADDITIONAL RESPONSE FIELDS IN EXACLOUD STATUS RESPONSE FOR STORAGE(ASM) RESHAPE STEPS
      rajsag    03/20/25 - 37731481 - exacs:24.4.1:"n-3" grid support:regular
                           exacs provisioning failing at prevmchecks:exception
                           class:<class 'typeerror'>, value: can only
                           concatenate list (not "set") to list
      rajsag    03/12/25 - 37692551 - exacs-ecra: vmc provision failed at step:
                           prevmchecks with typeerror during pmem component
                           check
      prsshukl  02/20/25 - ER 36981808 - EXACS | ADBS | ELASTIC COMPUTE AND
                           CELL OPERATION ENHANCEMENTS -> IMPLEMENT PHASE 2
      rajsag    02/03/25 - Enh 37481917 - exacloud | prevmcehcks
                           mfixpmemcomponent() runs pmem cache and log checks
                           sequentially checks sequentially| improve large
                           cluster provisioning time
      ririgoye  08/29/24 - Bug 36537230 - SET CORRECT VALUE FOR MAX STORAGE
                           SIZE FOR ACFS01 DEPENDING ON STORAGE SHAPE
      dekuckre  07/17/24 - 35408982: Add quorum devices to SPRC diskgroup
      prsshukl  07/04/24 - Bug 31973867 - SPARSE VIRTUAL TO PHYSICAL RATIO IS
                           HARDCODED AT MULTIPLE PLACES
      pbellary  07/02/24 - ENH 36690772 - EXACLOUD: IMPLEMENT PRE-VM STEPS FOR EXASCALE SERVICE
      rajsag    06/26/24 - Enh 36603947 - exacloud : exascale storage pool
                           resize operation
      avimonda  06/24/24 - Bug 36554441 - EXACS: DELETESERVICE FAILED WITH
                           EXACLOUD ERROR CODE: 3802 EXACLOUD : OEDACLI ERROR
                           FOUND ON SCRIPT EXECUTION.
      jfsaldan  05/02/24 - Bug 36573967 - EXACS:R1 SRG: CLUSTER TERMINATION
                           STUCK IN PREVMINSTALL STEP
      jfsaldan  02/20/24 - Bug 36277822 - CELLINIT.ORA HAS STIB0/STIB1 SET
                           AFTER TERMINATION CAUSING CELLRSRV PROBLEMS IN
                           XEN/IB SVM
      aararora  12/04/23 - ER 35995499: Add a utility method to return total
                           and free space for celldisks
      naps      09/21/23 - Bug 35830760 - Zdlra deleteservice diskgroup
                           validation check.
      aararora  07/06/23 - Bug 35539930 : Add a getter method for
                           mGetDiskGroupType.
      naps      06/01/23 - Bug 35095608 - mvm support for zdlra.
      aararora  05/04/23 - Bug 35320487: Add checks for grid disks - if resized
                           on the cells.
      pbellary  04/20/23 - 35109538: DISKGROUP CREATION FAILED DUE TO MISSING GRID DISKS 
      rajsag    02/21/23 - 35098117 - exacc:22.3.1:bb:x10m:activate compute
                           failed at config_dns step with keyerror: critical
                           exception caught aborting request [21]
      ndesanto  01/24/23 - Bug 35001886 - Fixed system model compare code to 
                           work correctly with X10M systems
      jfsaldan  11/03/22 - Bug 33993510 - CELLDISKS RECREATED AFTER DBSYSTEM
                           TERMINATION
      dekuckre  03/02/22 - 33294041: update condition to enable asm scoped security
      naps      02/21/22 - code coverage txn.
      jfsaldan  01/31/22 - Bug 33797430 - Adding method to get list of
                           griddisks in multiple cells
      rajsag    08/26/21 - 31985002 - ensure asm reshape flows update point in
                           time status for every step in request table
      scoral    05/06/21 - Added mListPMEMDetails and mFixPMEMComponent on
                           ebCluStorageConfig.
      aypaul    02/08/21 - 32453568 Cap ACFS volume size to 5% of DATA DG size
                           with a minimum size fo 100G
      jesandov  01/26/21 - XbranchMerge jesandov_bug-32418029 from
      naps      01/12/21 - Enhance error handling.
      naps      12/11/20 - zdlra provisioning support.
      dekuckre  12/07/20 - 32290350: Update mCheckGridDisks, mDeleteGD
      naps      10/12/20 - zdlra provisioning support.
      talagusu  08/09/20 - Bug 31721011 - STORAGE RESIZE SKIPPED WHEN ONE OF
                           THE DISKGROUP IS IN DESIRED SIZE
      rajsag    07/20/20 - 31642068 - FAILED ASM RESHAPE SKEWS STORAGE
                           DISTRIBUTION PROPORTION
      devbabu   07/06/20 - 31445600: Error code fix
      pverma    04/05/20 - Remove division factor while evaluating new sparse
                           size
      sringran  03/16/20 - 30899728: EXACC: STORAGE RESIZE REFECTS IN UI 
                           BUT NOT IN ASM
      rajsag    03/13/20 - ENSURE NO NODE REBOOT FOR NO CHANGE IN NODE RESOURCE
                           DURING RESHAPE OPERATIONS
      rajsag    01/25/20 - DOWNSIZE SUPPORT WITH ASM STORAGE RESHAPE OPERATION
                           IN EXACLOUD
      vicgupta  12/24/19 - Correction in calculation of original size of disk
                           group
      ndesanto  10/02/19 - Enh 30374491: EXACC PYTHON 3 MIGRATION BATCH 02
      gurkasin  07/24/19 - Adding quorum failgroups for RECO diskgroup.
      dekuckre  06/04/19 - 29782829: Add mCheckGridDisks
      dekuckre  04/29/19 - 29702612: Address regression
      dekuckre  11/22/19 - Handle case on moving mGetOracleHome from 
                           clucontrol.py to cluelasticcompute.py
      pnkrishn  11/26/18 - 27568807: sparse griddisk virtual size ratio set to
                           10x
      gurkasin  10/10/18 - Adding a class for Quorum operations
      dekuckre  07/04/18 - 28285387: Accept usable storage to be passed as 
                           input parameter for storage resize operation.
      pbellary  07/04/18 - XbranchMerge pbellary_bug-28252945 from
                           st_ecs_18.2.5.2.0
      gsundara  06/20/18 - Fix for bug 28098428
      dekuckre  05/25/18 - XbranchMerge hnvenkat_bug-27400682 from
                           st_ecs_18.1.3.0.0
      gsundara  05/01/18 - fix for bug 27941250
      gsundara  04/20/18 - fix for bug 27870536
      aanverma  03/09/18 - Bug #27666598: DG related changes from
                           mPatchClusterDiskgroup() of clucontrol.py
      dekuckre  02/23/18 - 27588418: Enable storage resize if sparse is enabled.
      dekuckre  02/22/18 - 27568807: Set <sparseVirtualSize> to slice size in 
                           mPatchClusterDiskgroup().
      dekuckre  02/05/18 - 27455021: Add capability to resize storage
      gsundara  01/17/18 - fix for bug 27401504
      hnvenkat  11/23/17 - XbranchMerge hnvenkat_bug-27156577 from
                           st_ecs_pt-multivm
      gsundara  11/11/17 - Fix for bug 27098559
      gsundara  10/20/17 - Refactor from clucontrol
"""

from __future__ import print_function

import copy
import json
import re
import six
import time
import xml.etree.cElementTree as etree
import math

from time import sleep
from typing import List, Mapping, Sequence, Tuple

from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure,\
TimeoutBehavior, ExitCodeBehavior

from exabox.core.Context import get_gcontext
from exabox.core.DBStore import ebGetDefaultDB
from exabox.core.Error import gDiskgroupError, gReshapeError, \
ExacloudRuntimeError, ebError
from exabox.core.Node import exaBoxNode

from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogVerbose, \
ebLogJson, ebLogTrace, ebLogCritical

from exabox.ovm.cludiskgroups import ebDiskgroupOpConstants, \
ebCluManageDiskgroup
from exabox.ovm.clumisc import mWaitForSystemBoot
from exabox.ovm.csstep.exascale.escli_util import ebEscliUtils
from exabox.ovm.utils.clu_utils import ebCluUtils
from exabox.core.Error import gElasticError

from exabox.utils.common import mCompareModel
from exabox.utils.node import connect_to_host, node_exec_cmd, node_exec_cmd_check

def mParseStorageDistrib(aStorageDistrib: str) -> Tuple[float, float, float]:
    """
    Expected format for aStorageDistrib is 9.9:9.9:9.9 
    Which are the float values for DATA:RECO:SPARSE
    For example: 50:25:25, 50:50:0
    This function validates in case ECRA sends 50:50
    Values must sum to 100 and be non-negative.
    """
    if not aStorageDistrib:
        _msg = "Input string cannot be empty"
        ebLogError(_msg)
        raise ValueError(_msg)

    parts = aStorageDistrib.split(':')
    if len(parts) < 2 or len(parts) > 3:
        _msg = "Invalid format: must have exactly 2 or 3 parts separated by ':'"
        ebLogError(_msg)
        raise ValueError(_msg)

    # ensure 3 values are always returned
    if len(parts) == 2:
        parts.append('0')

    try:
        data = float(parts[0])
        reco = float(parts[1])
        sparse = float(parts[2])
    except ValueError:
        _msg = "All parts must be valid float numbers"
        ebLogError(_msg)
        raise ValueError(_msg)

    # Validate non negatives
    if data < 0 or reco < 0 or sparse < 0:
        _msg = "Distribution values must be non-negative"
        ebLogError(_msg)
        raise ValueError(_msg)

    # Validate sum is 100 (add tolerance)
    total = data + reco + sparse
    
    if abs(total - 100) > 1e-6:  # Small imprecisions for float
        # 1e-6 is used due to Floating-point numbers in Python 
        # which are not always precise
        _msg = f"Distribution values must sum to 100, but sum is {total}"
        ebLogError(_msg)
        raise ValueError(_msg)

    return data, reco, sparse

class ebCluDiskGroupConfig(object):

    def __init__(self, aDiskGroupXML):

        dg = aDiskGroupXML
        self.__dgId = dg.get('id')
        self.__version = dg.find('version')
        self.__dgName = dg.find('diskGroupName')
        self.__redundancy = dg.find('redundancy')
        self.__sliceSize = dg.find('sliceSize')
        machines = dg.findall('machines/machine')
        self.__mac_list=[]
        for mac in machines:
            self.__mac_list.append(mac.get('id'))
        self.__cellDisks = dg.find('cellDisks')
        self.__dgSize = dg.find('diskGroupSize')
        self.__ocrVote = dg.find('ocrVote')
        self.__quorumDisk = dg.find('quorumDisk')
        self.__acfsVolumeName = dg.find('acfsVolumeName')
        self.__acfsVolumeSize = dg.find('acfsVolumeSize')
        self.__acfsMountPath = dg.find('acfsMountPath')
        self.__sparsedg = dg.find('sparse')
        self.__sparseVirtualSize = dg.find('sparseVirtualSize')
        self.__diskGroupType = dg.find("diskGroupType")
        self.__gridDiskPrefix = dg.find("gridDiskPrefix")
        self.__config  = dg
        self._constantsObj = ebDiskgroupOpConstants()

    def mGetOCRVote(self):
        return self.__ocrVote.text

    def mGetQuorumDisk(self):
        return self.__quorumDisk

    def mSetOCRVote(self,aValue):
        self.__ocrVote.text = aValue

    def mSetQuorumDisk(self,aValue):
        if self.__quorumDisk is None:
            self.__quorumDisk = etree.Element('quorumDisk')
            self.__config.append(self.__quorumDisk)
        self.__quorumDisk.text = aValue

    def mSetAcfsVolumeName(self,aVolName):
        if self.__acfsVolumeName is None:
            self.__acfsVolumeName = etree.Element('acfsVolumeName')
            self.__config.append(self.__acfsVolumeName)
        self.__acfsVolumeName.text = aVolName

    def mSetAcfsVolumeSize(self,aSize):
        if self.__acfsVolumeSize is None:
            self.__acfsVolumeSize = etree.Element('acfsVolumeSize')
            self.__config.append(self.__acfsVolumeSize)
        if type(aSize) == int:
            aSize = str(aSize)
        self.__acfsVolumeSize.text = aSize

    def mSetAcfsMountPath(self,aMntPath):
        if self.__acfsMountPath is None:
            self.__acfsMountPath = etree.Element('acfsMountPath')
            self.__config.append(self.__acfsMountPath)
        self.__acfsMountPath.text = aMntPath

    def mGetAcfsVolumeName(self):
        return self.__acfsVolumeName.text

    def mGetAcfsVolumeSize(self):
        return self.__acfsVolumeSize.text

    def mGetAcfsMountPath(self):
        return self.__acfsMountPath.text

    def mGetXMLObject(self):
        return self.__config

    def mGetDgName(self):
        return self.__dgName.text

    def mGetDgId(self):
        return self.__dgId

    def mReplaceDgId(self, aDgId):
        self.__dgId = aDgId
        dg = self.__config
        dg.set('id', aDgId)

    def mSetSparseDg(self, aSparse):
        if self.__sparsedg is None:
            self.__sparsedg = etree.Element('sparse')
            self.__config.append(self.__sparsedg)
        self.__sparsedg.text = aSparse

    def mGetDiskGroupType(self):
        _dg_types = [self._constantsObj._data_dg_type_str,
                     self._constantsObj._reco_dg_type_str,
                     self._constantsObj._sparse_dg_type_str,
                     self._constantsObj._catalog_dg_type_str,
                     self._constantsObj._delta_dg_type_str,
                     self._constantsObj._dbfs_dg_type_str]
        if self._constantsObj._sparse_dg_prefix in self.mGetDgName():
            # Sparse diskgroup can have name starting with SPR
            ebLogTrace(f"_dg_type identified from xml is {self._constantsObj._sparse_dg_type_str}.")
            return self._constantsObj._sparse_dg_type_str
        for _dg_type in _dg_types:
            if _dg_type in self.mGetDgName().lower():
                ebLogTrace(f"_dg_type identified from xml is {_dg_type}.")
                return _dg_type
        ebLogTrace(f"_dg_type could not be identified from xml. __dgName is {self.mGetDgName()} and __dgId is {self.mGetDgId()}.")

    def mSetDiskGroupType(self, aType):
        if self.__diskGroupType is None:
            self.__diskGroupType = etree.Element("diskGroupType")
            self.__config.append(self.__diskGroupType)
        self.__diskGroupType.text = aType

    def mGetGridDiskPrefix(self):
        return self.__gridDiskPrefix.text

    def mSetGridDiskPrefix(self, aGdPrefix):
        if self.__gridDiskPrefix is None:
            self.__gridDiskPrefix = etree.Element("gridDiskPrefix")
            self.__config.append(self.__gridDiskPrefix)
        self.__gridDiskPrefix.text = aGdPrefix

    def mSetSparseVirtualSize(self, aSize):
        if self.__sparseVirtualSize is None:
            self.__sparseVirtualSize = etree.Element('sparseVirtualSize')
            self.__config.append(self.__sparseVirtualSize)
        if type(aSize) == int:
            aSize = str(aSize)+'G'
        self.__sparseVirtualSize.text = aSize

    def mReplaceDgName(self, aDgName):
        self.__dgName.text = aDgName

    def mGetSliceSize(self):
        return self.__sliceSize.text

    def mGetDiskGroupSize(self):
        return self.__dgSize.text

    def mGetDgRedundancy(self):
        return self.__redundancy.text

    def mSetSliceSize(self, aSize):

        if type(aSize) == int:
            aSize = str(aSize)+'G'
        self.__sliceSize.text = aSize

    def mSetDiskGroupSize(self, aSize):

        if type(aSize) == int:
            aSize = str(aSize)+'G'
        self.__dgSize.text = aSize

    def mSetDgRedundancy(self, aRedund):
        self.__redundancy.text = aRedund

    def mGetDiskGroupMachines(self):
        return self.__mac_list

    def DumpDiskGroupConfig(self):
        pass

class ebCluStoragePoolConfig(object):

    def __init__(self, aStoragePoolXML):

        sp = aStoragePoolXML
        self.__spId = sp.get('id')
        self.__version = sp.find('version')
        self.__spName = sp.find('storagePoolName')
        self.__spType = sp.find('storagePoolType')
        self.__spSize = sp.find('storagePoolSize')
        self.__uiSize = sp.find('uiSize')
        self.__uiSizeType = sp.find('uiSizeType')
        machines = sp.findall('machines/machine')
        self.__mac_list=[]
        for mac in machines:
            self.__mac_list.append(mac.get('id'))

    def mGetSpId(self):
        return self.__spId

    def mGetStoragePoolMachines(self):
        return self.__mac_list

    def mGetSPName(self):
        return self.__spName.text

    def mGetSPType(self):
        return self.__spType.text

    def mGetSPSize(self):
        return self.__spSize.text

    def mGetUiSize(self):
        return self.__uiSize.text

    def mGetUiSizeType(self):
        return self.__uiSizeType.text

class ebCluEDVVolumesConfig(object):

    def __init__(self, aEDVVolumesXML):

        edv = aEDVVolumesXML
        self.__edvId = edv.get('id')
        self.__name = edv.find('edvVolumeName')
        self.__size= edv.find('edvVolumeSize')
        self.__edvType = edv.find('edvVolumeType')
        self.__devicePath = edv.find('edvDevicePath')

    def mGetEdvId(self):
        return self.__edvId

    def mGetEDVName(self):
        return self.__name.text

    def mGetSPSize(self):
        return self.__size.text

    def mGetEDVType(self):
        return self.__edvType.text

    def mGetDevicePath(self):
        return self.__devicePath.text

class ebCluStorageConfig(object):

    def __init__(self, aExaBoxCluCtrl, aConfig):

        storage = aConfig.mGetConfigAllElement('storage/diskGroups/diskGroup')
        storage_pool = aConfig.mGetConfigAllElement('storage/storagePools/storagePool')
        edv_volume = aConfig.mGetConfigAllElement('storage/edvVolumes/edvVolume')

        self.__dgo_list = {}
        for dg in storage:
            dgo = ebCluDiskGroupConfig(dg)
            self.__dgo_list[dgo.mGetDgId()] = dgo

        self.__spo_list = {}
        for sp in storage_pool:
            spo = ebCluStoragePoolConfig(sp)
            self.__spo_list[spo.mGetSpId()] = spo

        self.__edvvol_list = {}
        for edv in edv_volume:
            edvo = ebCluEDVVolumesConfig(edv)
            self.__edvvol_list[edvo.mGetEdvId()] = edvo

        self.__ebox = aExaBoxCluCtrl
        self.__config = aConfig.mConfigRoot()

    def mGetDiskGroupConfigList(self):
        return list(self.__dgo_list.keys())

    def mGetDiskGroupConfig(self, aDgId):
        return self.__dgo_list[aDgId]

    def mGetStoragePoolConfigList(self):
        return list(self.__spo_list.keys())

    def mGetStoragePoolConfig(self, aSpId):
        return self.__spo_list[aSpId]

    def mGetEDVVolumesConfigList(self):
        return list(self.__edvvol_list.keys())

    def mGetEDVVolumesConfig(self, aEdvId):
        return self.__edvvol_list[aEdvId]

    def mGetEbox(self):
        return self.__ebox

    def mRemoveDiskGroupConfig(self,aDGId):

        if not aDGId in self.__dgo_list.keys():
            return

        _dgco = self.__dgo_list[aDGId]
        del self.__dgo_list[aDGId]
        self.__config.find('storage/diskGroups').remove(_dgco.mGetXMLObject())

    def mAddDiskGroupConfig(self, aDgConfig):

        if aDgConfig.mGetDgId() in self.__dgo_list.keys():
            return

        self.__dgo_list[aDgConfig.mGetDgId()] = aDgConfig
        self.__config.find('storage/diskGroups').append(aDgConfig.mGetXMLObject())

    def DumpStorageConfig(self):

        for dg in self.__dgo_list:
            print(dg)

    """
    ACFS GridDisk mgmt
    """
    def mCreateCellDG(self, aNode, aDiskNumber, aPrefix, aCellSrvName, aCellDisk, aSize):
        _eBox = self.mGetEbox()
        if len(str(aDiskNumber)) == 1:
            aDiskNumber = '0' + str(aDiskNumber)
        else:
            aDiskNumber = str(aDiskNumber)
        _cmdstr = "cellcli -e CREATE GRIDDISK  %sCD_%s_%s celldisk=%s, size=%s;" % (
                                            aPrefix, aDiskNumber, aCellSrvName, aCellDisk, aSize)
        aNode.mExecuteCmd(_cmdstr)
        if aNode.mGetCmdExitStatus():
            raise Exception('mExecuteCmd Failed', aNode.mGetHostname(), _cmdstr)
        if _eBox.mIsDebug():
            ebLogInfo('*** GridDisk : %sCD_%s_%s on celldisk=%s has been created' %
                        (aPrefix, aDiskNumber, aCellSrvName, aCellDisk))
        return _cmdstr

    def mDeleteCellDG(self, aNode, aDiskNumber, aPrefix, aCellSrvName):
        _eBox = self.mGetEbox()
        if len(str(aDiskNumber)) == 1:
            aDiskNumber = '0' + str(aDiskNumber)
        else:
            aDiskNumber = str(aDiskNumber)
        _cmdstr = "cellcli -e DROP GRIDDISK  %sCD_%s_%s;" % (aPrefix, aDiskNumber, aCellSrvName)
        aNode.mExecuteCmd(_cmdstr)
        if aNode.mGetCmdExitStatus():
            raise Exception('mExecuteCmd Failed', aNode.mGetHostname(), _cmdstr)
        if _eBox.mIsDebug():
            ebLogInfo('*** GridDisk : %sCD_%s_%s has been deleted' % (aPrefix, aDiskNumber, aCellSrvName))
        return _cmdstr

    def mListCellDG(self, aNode, aSuffix=None, aCellType="GRIDDISK"):
        _eBox = self.mGetEbox()

        if _eBox.IsZdlraProv():
            _cmdstr = f"cellcli -e list {aCellType} attributes NAME,SIZE where diskType like \\'.*Disk\\'"
        elif aSuffix:
            _cmdstr = f"cellcli -e list {aCellType} ATTRIBUTES NAME,SIZE where NAME like \\'.*{aSuffix}_.*\\' and diskType like \\'.*Disk\\';"
        else:
            _cmdstr = "cellcli -e LIST GRIDDISK ATTRIBUTES NAME;"
        aNode.mExecuteCmd(_cmdstr)
        _i,_o,_e = aNode.mExecuteCmd(_cmdstr)
        if aNode.mGetCmdExitStatus():
            ebLogError('*** CMD_OUT: '+str(_o)+' _ERR:'+str(_e))
            raise Exception('mExecuteCmd Failed', aNode.mGetHostname(), _cmdstr)

        if aSuffix:
            _griddisks = _o.read().split('\n')
        else:
            _griddisks = _o.read().split()

        _cluster_griddisks = []
        if _eBox.IsZdlraProv():
            for _griddisk in _griddisks:
                if "CATALOG" in _griddisk or "DELTA" in _griddisk:
                    _cluster_griddisks.append(_griddisk)
        elif aSuffix:
            for _griddisk in _griddisks:
                if aSuffix in _griddisk:
                    _cluster_griddisks.append(_griddisk)
        else:
            _cluster_griddisks = _griddisks
        return _cluster_griddisks

    def mListCellDisksAttributes(self, aNode: exaBoxNode, aAttributes: List[str]=['STATUS']) -> Mapping[str, Mapping[str, str]]:
        """
        Return a dictionary with all of the cell disks and their attributes
        for a given node.

        E.g.: {
            'CD_00_scaqab10celadm01': { 'STATUS': 'normal' },
            'CD_01_scaqab10celadm01': { 'STATUS': 'normal' }
        }
        """
        _cmdstr = 'cellcli -e LIST CELLDISK ATTRIBUTES NAME, {};'.format(', '.join(aAttributes))
        _, _o, _e = aNode.mExecuteCmdCellcli(_cmdstr)
        if aNode.mGetCmdExitStatus():
            ebLogError(f'*** CMD_OUT: {_o.read()}, _ERR: {_e.read()}')
            raise ExacloudRuntimeError(0x0825, 0xA, f'mExecuteCmd Failed on {aNode.mGetHostname()}, with cmd: {_cmdstr}', Cluctrl = self.__ebox)
        
        _celldisks = {}
        for _line in _o.readlines():
            _celldisk_name, *_celldisk_attrs = _line.split()
            _celldisks[_celldisk_name] = dict(zip(aAttributes, _celldisk_attrs))
        
        return _celldisks

    @staticmethod
    def mListPMEMDetails(aNode: exaBoxNode, aPMEMComponent: str) -> Mapping[str, str]:
        """
        Returns a dictionary with all of the PMEMLOG or PMEMCACHE attributes
        for the given node.

        E.g.: {
            'name': 'sea201109exdcl01_PMEMLOG',
            'cellDisk': 'PM_00_sea201109exdcl01,PM_01_sea201109exdcl01,...',
            'creationTime': '2021-05-05T23:48:01+00:00',
            'degradedCelldisks': '',
            'effectiveSize': '9.9375G',
            'efficiency': '100.0',
            'id': '7be25e9d-0f6b-4240-b186-c520e30d17c3',
            'size': '9.9375G',
            'status': 'normal'
        }
        """
        _cmd = f"cellcli -e list pmem{aPMEMComponent.lower()} detail"
        _, _o, _ = node_exec_cmd(aNode, _cmd, \
            log_error=True, log_stdout_on_error=True \
        )
        
        _details = {}
        for _line in _o.split('\n'):
            if not _line.strip():
                continue
            _attr_name, *_attr_value = _line.split()
            _details[_attr_name[:-1]] = ' '.join(_attr_value)
        
        return _details

    @staticmethod
    def mFixPMEMComponent(aFDQNs: Sequence[str], aPMEMComponent: str):
        """
        Checks the PMEMLOG or PMEMCACHE status for all specified cells and
        tries to redefine it in case its status is not normal or inconsisten
        with the other cells.
        """
        def mCheckPerCellPMEMStatus(aCell, aPMEMComponent: str, aCellDisks):
            _cell = aCell
            _cells_disks = aCellDisks

            with connect_to_host(_cell, get_gcontext()) as _node:
                _details = ebCluStorageConfig.mListPMEMDetails(
                    _node,
                    aPMEMComponent
                )

                ebLogTrace(f"Details of PMEM{aPMEMComponent.upper()} in cell {_cell}: {_details}")

                if "XRMEMCACHE" in str(_details.get("name")):
                    # X10M+ changed from PMEMCACHE to XRMEMCACHE and does not contains status field
                    # Since the name can be fetch, assumming status normal
                    _status = _details.get('status', 'normal')
                else:
                    _status = _details.get('status')

                if not _status or _status.lower() != "normal":
                    ebLogWarn(f'*** Cell {_cell} '
                        f'PMEM{aPMEMComponent.upper()} '
                        f'status is "{_status}", trying to redefine it...'
                    )
                    return
                _disks = _details.get('cellDisk')
                if not _disks:
                    ebLogWarn(f'*** Cell {_cell} '
                        f'PMEM{aPMEMComponent.upper()} '
                        f'cellDisk is empty, trying to redefine it...'
                    )
                    if "XRMEMCACHE" in str(_details.get("name")):
                        _cells_disks[_cell] = []
                    return
                
                _cell_disks = { 
                    _cell_disk[:5] for _cell_disk in _disks.split(',')
                }
                _cells_disks[_cell] = _cell_disks

        
        def mFixPerCellPMEMStatus(aCell):
            _cell = aCell
            with connect_to_host(_cell, get_gcontext()) as _node:
                _cmd = f"cellcli -e drop pmem{aPMEMComponent.lower()}"
                node_exec_cmd(_node, _cmd, \
                    log_error=True, log_stdout_on_error=True \
                )

                _cmd = f"cellcli -e create pmem{aPMEMComponent.lower()} all"
                node_exec_cmd(_node, _cmd, \
                    log_error=True, log_stdout_on_error=True \
                )


        _plist = ProcessManager()
        _cells_disks = _plist.mGetManager().dict()
        for _cell in aFDQNs:
            _p = ProcessStructure(mCheckPerCellPMEMStatus, [_cell, aPMEMComponent, _cells_disks], _cell)
            _p.mSetMaxExecutionTime(30*60) # 30 minutes
            _p.mSetJoinTimeout(5)
            _p.mSetLogTimeoutFx(ebLogWarn)
            _plist.mStartAppend(_p)
        
        _plist.mJoinProcess()
 
        # If we didn't add some cell to the _cell_disks dictionary, that
        # means something went wrong when checking its PMEM detail, so
        # it needs to be fixed, that is, we need to fix all of the cells
        # except for the ones we have in our cells_disks dict.
        #    set(aFDQNs) - set(_cells_disks.keys())
        # We also add the cells which cellDisk PMEM detail is inconsistent
        # with th ther cells.

        _cells_disks = dict(_cells_disks)
        _cell_disks_total = set()
        for _cell in aFDQNs:
            if _cell in _cells_disks.keys():
                _cdisks = _cells_disks[_cell]
                _cell_disks_total.update(_cdisks)

        _plist = ProcessManager()
        _cells_to_fix = (set(aFDQNs) - set(_cells_disks.keys())) | \
            { _cell for _cell, _cell_disks in _cells_disks.items() \
                if _cell_disks != _cell_disks_total }

        for _cell in _cells_to_fix:
            _p = ProcessStructure(mFixPerCellPMEMStatus, [_cell], _cell)
            _p.mSetMaxExecutionTime(30*60) # 30 minutes
            _p.mSetJoinTimeout(5)
            _p.mSetLogTimeoutFx(ebLogWarn)
            _plist.mStartAppend(_p)
        
        _plist.mJoinProcess()
            

    @staticmethod
    def mDropCellDisks(aCellList: Sequence[str]):
        """
        This function will use cellcli to attempt to drop all the celldisks
        present in each cell from aCellList.

        If an error occurs on a cell this method will retry once adding 'FORCE'
        to the command.
        If an error still persist this method will move on to the next cell.
        If any cell had errors, this method will raise an exception at the end

        :param aCellList: a sequence of cell FQDNs on where to (attempt to) drop
            it's celldisks
        :raises ExacloudRuntimeError: if an error happens even after retrying
            with FORCE on any cell, when attempting to drop the celldisks
        """

        _bin_cellcli = "/opt/oracle/cell/cellsrv/bin/cellcli"
        _drop_cmd = f"{_bin_cellcli} -e drop celldisk all"
        _cells_with_errors = set()

        for _cell in aCellList:
            ebLogInfo(f"Attempting to drop the celldisk of {_cell}")
            with connect_to_host(_cell, get_gcontext()) as _node:

                # Try without force
                _out_drop = node_exec_cmd(_node, _drop_cmd)

                if _out_drop.exit_code != 0:
                    ebLogWarn("An error happened when attempting to drop the "
                        f"celldisks for {_cell}. Cmd output is:\n {_out_drop}.\n "
                        "Retrying with FORCE")

                    # Try using FORCE
                    _out_drop_force = node_exec_cmd(_node,
                        f"{_drop_cmd} FORCE")

                    if _out_drop_force.exit_code != 0:
                        ebLogError("An error happened when attempt to drop the "
                            f"celldisks for {_cell} with FORCE. Cmd output is:\n "
                            f"{_out_drop_force}")
                        _cells_with_errors.add(_cell)

                    else:
                        ebLogInfo(f"Successfully dropped celldisks for {_cell} "
                            "using FORCE")
                        ebLogTrace(f"Drop with force output:\n{_out_drop_force}")

                else:
                    ebLogInfo(f"Successfully dropped celldisks for {_cell}")

        # Raise error if dropping the celldisks was not possible on any cell
        if _cells_with_errors:
            _err_msg = ("Exacloud was not able to delete the celldisks in the "
                f"following cells: {_cells_with_errors}. Please review the output "
                "of the drop command for each cell where it failed, address the "
                "issue and retry the operation")
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(0x0825, 0xA, _err_msg)

    #
    # Try first to locate CD celldisks and then fallback to FD celldisks
    #
    def mListACFSCellDisks(self, aNode):

        _cmdstr = 'cellcli -e LIST CELLDISK WHERE name LIKE \\"CD_.*\\" attributes NAME;'
        _i,_o,_e = aNode.mExecuteCmdCellcli(_cmdstr)
        _celldisks = _o.read().split()
        if len(_celldisks):
            return _celldisks
        ebLogInfo('*** No CD celldisk found on cell: '+aNode.mGetHostname())
        _cmdstr = 'cellcli -e LIST CELLDISK WHERE name LIKE \\"FD_.*\\" attributes NAME;'
        _i,_o,_e = aNode.mExecuteCmdCellcli(_cmdstr)
        _celldisks = _o.read().split()
        if len(_celldisks):
            ebLogInfo('*** All Flash configuration found switching to FD celldisk on cell: '+aNode.mGetHostname())
        return _celldisks
    #
    # if aCreate is False then delete GridDisk instead of creating them
    #
    def mCreateACFSGridDisks(self,aCreate=True):
        _eBox = self.mGetEbox()
        _exadata_cell_model = _eBox.mGetExadataCellModel()
        _cutOff_model = 'X7'
        if mCompareModel(_exadata_cell_model, _cutOff_model) >= 0:
            ebLogWarn('*** mCreateACFSGridDisks() IS DISABLED')
            return

        #
        # Fetch use same suffix as DATA/RECO (e.g. C1/C2/..) to suffix the Grid Disk
        #
        _cluster = _eBox.mGetClusters().mGetCluster()
        _cludgroups = _cluster.mGetCluDiskGroups()
        _suffix = 'XX'
        for _dgid in _cludgroups:
            if self.mGetDiskGroupConfig(_dgid).mGetDgName()[:4] in ['DATA','RECO']:
                _suffix = self.mGetDiskGroupConfig(_dgid).mGetDgName()[-2:]
                # If cluster number is >= 10, suffix is 3-char
                if 'C' not in _suffix:
                    _suffix = self.mGetDiskGroupConfig(_dgid).mGetDgName()[-3:]
                break

        ebLogInfo('*** Using Grid Disk cluster suffix: %s' % (_suffix))
        #
        # Proceed with Grid Disk Creation.
        #
        _key0 = "ADG1%s_" % (_suffix)
        _key1 = "ADG2%s_" % (_suffix)
        _prefixes = {_key0: "24G", _key1: "8G"}
        _cell_list = _eBox.mReturnCellNodes()
        for _cell_name in sorted(_cell_list.keys()):
            # Start on celldisk disk_num
            disk_num = 2
            _node = exaBoxNode(get_gcontext(), Cluctrl = self.__ebox)
            _node.mConnect(aHost=_cell_name)
            ebLogInfo('*** ACFS DG Check on: '+_cell_name)
            _cell_name = _cell_name.split('.')[0]
            # Fetch existing DG
            _dg_list = self.mListCellDG(_node)
            for celldisk in self.mListACFSCellDisks(_node):
                a = re.compile("^(CD|FD)_0[0-1].*")      # Skip first two celldisks in each cellserver
                if not a.match(celldisk):
                    for _dgprefix, _size in sorted(six.iteritems(_prefixes)):
                        if len(str(disk_num)) == 1:
                            _dn = '0'+str(disk_num)
                        else:
                            _dn=str(disk_num)
                        _dg_name = "%sCD_%s_%s" % (_dgprefix, _dn, _cell_name)
                        if aCreate:
                            if not _dg_name in _dg_list:
                                self.mCreateCellDG(_node,disk_num, _dgprefix, _cell_name, celldisk, _size)
                            else:
                                if _eBox.mIsDebug():
                                    ebLogInfo('*** ACFS GridDisk already created: '+_dg_name)
                        else:
                            if _dg_name in _dg_list:
                                self.mDeleteCellDG(_node,disk_num, _dgprefix, _cell_name)
                    disk_num = disk_num + 1
            _node.mDisconnect()

    def mListCellDisksSize(self, aCellList=[]):
        """
        Utility method to list total space and free space for all the celldisks
        in all the cells
        """
        _eBox = self.mGetEbox()
        _escli = ebEscliUtils(_eBox)
        _cell_list = aCellList
        if _cell_list== None or _cell_list == []:
            _cell_list = _eBox.mReturnCellNodes()
            _cell_list = sorted(_cell_list.keys())

        _total_space_output_GB = 0.0
        _free_space_output_GB = 0.0
        _exadata_model_gt_X8 = False
        for _cell_name in _cell_list:
            _exadata_model = _eBox.mGetNodeModel(aHostName=_cell_name)
            if _eBox.mCompareExadataModel(_exadata_model, 'X8') >= 0:
                _exadata_model_gt_X8 = True

            if _escli.mIsEFRack(_cell_name) and _exadata_model_gt_X8:
                _cmdstr = 'cellcli -e LIST CELLDISK WHERE name LIKE \\"CF_.*\\" attributes name,size,freespace;'
            else:
                _cmdstr = 'cellcli -e LIST CELLDISK WHERE name LIKE \\"CD_.*\\" attributes name,size,freespace;'
            ebLogInfo(f"*** Executing the command - {_cmdstr} on cell - {_cell_name}.")

            with connect_to_host(_cell_name, get_gcontext()) as _node:
                _out, _err, _output, _error = None, None, None, None
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
                        _slice_size = _slice_output_for_celldisk[1]
                        _free_space_slice_size = _slice_output_for_celldisk[2]
                        # Here, 0.0009765625 is 1/1024.
                        _unit_factor_mapping = {'M': '0.0009765625', 'G': '1', 'T': '1024'}
                        if _slice_size[-1] not in _unit_factor_mapping.keys() or _free_space_slice_size[-1] not in _unit_factor_mapping.keys():
                            ebLogInfo(f"Unit not found in the supported mapping for unit and associated factor. Slice size - {_slice_size}. Free space - {_free_space_slice_size}. Skipping.")
                            continue
                        _total_space_output_GB += (float(_slice_size[:-1]) * float(_unit_factor_mapping[_slice_size[-1]]))
                        _free_space_output_GB += (float(_free_space_slice_size[:-1]) * float(_unit_factor_mapping[_free_space_slice_size[-1]]))
                else:
                    ebLogError(f'Error while running cellcli command on cell - None output received. *** ERROR: {_error}.')
                    raise ExacloudRuntimeError(0x0825, 0xA, f'mExecuteCmd Failed on {_cell_name}, with cmd: {_cmdstr}')
        return (_total_space_output_GB, _free_space_output_GB)

    def mDeleteACFSGridDisks(self):
        self.mCreateACFSGridDisks(aCreate=False)
    """
    Grid Disks Mgmt.
    """
    def mClusterDiskGroupSuffix(self):
        _eBox = self.mGetEbox()
        #
        # Fetch ClusterID
        #
        _cluster = _eBox.mGetClusters().mGetCluster()
        _cluster_groups = _cluster.mGetCluDiskGroups()
        _suffix = None
        for _dgid in _cluster_groups:
            #CATALOG and DELTA will be used in only single-vm env for Zdlra provisioning.
            if self.mGetDiskGroupConfig(_dgid).mGetDgName()[:4] in ['DATA','RECO'] or self.mGetDiskGroupConfig(_dgid).mGetDgName() in ['CATALOG','DELTA']:
                _suffix = self.mGetDiskGroupConfig(_dgid).mGetDgName()[-2:]
                if 'C' not in _suffix:
                    _suffix = self.mGetDiskGroupConfig(_dgid).mGetDgName()[-3:]
                break

        return _suffix

    def mClusterDiskGroupList(self):
        pass

    def mDeleteForceGridDisks(self):

        _nogd = False
        _count = 3
        while _count:
            _erc = self.mDeleteGD()
            if _erc == 1:
                _nogd = True
                break
            _count -= 1
            if _count:
                time.sleep(5)
                ebLogWarn('*** DeleteForce GD re-try count: %d' % (3 - _count))
            else:
                ebLogError('*** DeleteForce GD FAILED : unable to delete following GDs')
                self.mDeleteGD(aListOnly=True)
        return _nogd

    # mCheckGridDisks returns 1 if there are any grid disks present, otherwise 0.
    def mCheckGridDisks(self, aCell=None):

        # mDeleteGD(aListOnly = True) will not delete the grid disks.
        # It returns 1 if there are no grid disks created
        # for the cluster, otherwise return 0.
        if self.mDeleteGD(True, aCell):
            return 0
        else:
            return 1

    def mGetCurrentClusterGridDisksFromCells(self, aNode: exaBoxNode)-> list:
        """
        This method will get the list of the griddisks of aNode that correspond
        to the current cluster. It uses the DiskGroups suffix to determine
        if the griddisk belongs to this cluster.

        :param aNode: an already connected exaBoxNode to the cell on which
            the method should fetch the griddisks from current cluster

        :returns: a list of the griddisk belonging to the current cluster
            based on the XML DiskGroups suffix
        """

        _list_cluster_griddisks = []

        # Fetch the DiskGroup suffix
        # e.g. suffix is C03 from RECOC03_CD_11_sea201602exdcl01
        # e.g. suffix is C1 from RECOC1_CD_00_sea201602exdcl01
        _diskgroup_suffix = self.mClusterDiskGroupSuffix()
        if _diskgroup_suffix is None:
            ebLogError("Fetching Cluster DG suffix failed !")
            return _list_cluster_griddisks

        # Fetch list of all griddisks from the cell of aNode
        _list_all_griddisk = self.mListCellDG(aNode)

        # Iterate over all griddisks of the cell on which aNode is connected to
        for _grid_disk in _list_all_griddisk:

            # Get first part of griddisk name, it contains the Diskgroup suffix
            # E.g. 'RECOC5' from 'RECOC5_CD_10_scaqae14celadm01'
            # E.g. 'RECOC03' from 'RECOC03_CD_11_sea201602exdcl01'
            _grid_name_suffix = _grid_disk.split('_')[0]

            # Check if griddisk name first part contains the DiskGroup suffix
            # E.g. 'C03' in 'RECOC03' -> True
            # E.g. 'C5' in 'RECOC03' -> False
            if _diskgroup_suffix in _grid_name_suffix:
                ebLogInfo(f"Grid Disk entry detected {_grid_disk} in "
                    f"{aNode.mGetHostname()}, suffix {_diskgroup_suffix}")
                _list_cluster_griddisks.append(_grid_disk)
            else:
                ebLogTrace(f"Grid Disk entry NOT part of cluster {_grid_disk} "
                    f"in {aNode.mGetHostname()}, suffix {_diskgroup_suffix}")

        return _list_cluster_griddisks

    def mDeleteGD(self, aListOnly=False, aCell=None):
        _eBox = self.mGetEbox()
        if _eBox.IsZdlraProv():
            return _eBox.mGetZDLRA().mDeleteGD(aListOnly, aCell)

        _rc = 0
        _cnb = 0

        _suffix = self.mClusterDiskGroupSuffix()
        if _suffix is None:
            ebLogError('*** CC:mDeleteForceGridDisks fetching Cluster DG suffix failed !')
            return _rc

        # Over here, last 2 chars of suffix are enough
        _suffix = _suffix[-2:]

        if aCell:
            _cell_list = [aCell]
        else:
            _cell_list = _eBox.mReturnCellNodes()
        #_dg_names   = ['ACFS', 'DBFS', 'DATA', 'RECO']
        for _cell in _cell_list:

            _node = exaBoxNode(get_gcontext(), Cluctrl = self.__ebox)
            _node.mConnect(aHost=_cell)
            #
            # Check/Compute Existing List of DG
            #
            _dg_list = []
            _cnb += 1
            _cmd = 'cellcli -e list griddisk'
            _i, _o, _e = _node.mExecuteCmdCellcli(_cmd)
            _output = _o.readlines()
            if _output:
                for _entry in _output:
                    _dg_name = _entry.strip().split(' ')[0].strip()
                    _dg_name_suffix = _dg_name.split('_')[0][-2:]
                    if _dg_name[:4] == 'DBFS' and _dg_name_suffix[0] == 'S':
                        _dg_name_suffix = 'C' + _dg_name_suffix[1:]
                    if _dg_name_suffix == _suffix:
                        if _eBox.mIsDebug():
                            ebLogInfo('*** GD_ENTRY: %s on CELL: %s' % (_dg_name, _cell))
                        _dg_list.append(_dg_name)
                    elif not _eBox.SharedEnv() and _eBox.mIsExabm() and not _eBox.mCheckConfigOption('skip_exabm_gdisk_cleanup', 'True'):
                        _dg_list.append(_dg_name)
                        ebLogWarn('*** GD_ENTRY/BM_MODE SINGLE VM  %s on CELL: %s' % (_dg_name, _cell))

                if not len(_dg_list):
                    ebLogInfo('*** NO GD_ENTRY FOR CLUSTER %s FOUND ON CELL: %s' % (_suffix, _cell))
                    _rc += 1

                for _dg_entry in _dg_list:
                    if not aListOnly:
                        _cmd = 'cellcli -e DROP GRIDDISK %s FORCE' % (_dg_entry)
                        _node.mExecuteCmdLog(_cmd)
                    else:
                        ebLogWarn('GD : %s' % (_dg_entry))
            else:
                ebLogInfo('*** No GD_ENTRY found on CELL: %s' % (_cell))
                _rc += 1

            _node.mDisconnect()

        return 1 if (_rc == _cnb) else 0

    # Patch the XML cluster configuration file with diskgroup
    # information.
    def mPatchClusterDiskgroup(self, 
        aCreateSparse:bool, 
        aBackupDisk:bool, 
        aDRSdistrib:str, 
        aOptions:object, 
        aTotalDGSize=None):

        def parseStorageDistrib(aStorageDistrib:str) -> Tuple[float,float,float]:
            """
            Expected format for aStorageDistrib is 9.9:9.9:9.9 
            Which are the float values for DATA:RECO:SPARSE
            For example: 50:25:25, 50:50:0
            This function validates in case ECRA sends 50:50
            """
            values = []
            if aStorageDistrib:
                values = aStorageDistrib.split(':')
            # ensure 3 values are always returned
            if len(values)==2:
                values.append('0')
            return float(values[0]),float(values[1]),float(values[2])

        _eBox = self.mGetEbox()
        _participant_node = None
        _options =  _eBox.mGetArgsOptions()
        if _options is not None and _options.jsonconf is not None and 'node_subset' in _options.jsonconf.keys():
            _participant_node = _options.jsonconf['node_subset']['num_participating_computes']
        _sparseConfig = None

        _create_sparse = aCreateSparse
        _backup_disk = aBackupDisk
        _storage_distrib = aDRSdistrib
        _dataPct:float
        _recoPct:float
        _sparsePct:float
        if _storage_distrib:
            _dataPct, _recoPct, _sparsePct = \
                parseStorageDistrib(_storage_distrib)

        _cluster = _eBox.mGetClusters().mGetCluster()
        _cludgroups = _cluster.mGetCluDiskGroups()

        #
        # Retrieve number of localDisk in cell
        #
        _cell_list = _eBox.mReturnCellNodes()
        _cell_name = list(_cell_list.keys())[0]  # Pick first cell
        _mac_cfg = _eBox.mGetMachines().mGetMachineConfig(_cell_name)
        _ldisk_cnt = _mac_cfg.mGetLocaldisksCount()
        
        # Get Data, Reco, Sparse, DBFS info (size, slice, dg_id) from
        # _eBox.mGetClusters().mGetCluster().mGetCluDiskGroups()

        _data_size = 0
        _reco_size = 0
        _sparse_size = 0
        _dbfs_size = 0
        _data_slice = 0
        _reco_slice = 0
        _sparse_slice = 0
        _slice = 0
        _data_dg_id = None
        _reco_dg_id = None
        _sparse_dg_id = None
        _dbfs_dg_id = None
        _sparse_virtual_physical_ratio = 10

        for _dgid in _cludgroups:
            _dgConfig = self.mGetDiskGroupConfig(_dgid)
            #_dgConfig = _eBox.mGetStorage().mGetDiskGroupConfig(_dgid)
        
            _slice_sz = _dgConfig.mGetSliceSize()
            _dgroup_sz = _dgConfig.mGetDiskGroupSize()
            _dgname = _dgConfig.mGetDgName().lower()
            _dgtype = _dgConfig.mGetDiskGroupType().lower()
        
            if _dgname.find('data') != -1:
                _data_size = int(_dgroup_sz[:-1])
                try:
                    _data_slice = int(_slice_sz[:-1])
                except:
                    _data_slice = 0
                _data_dg_id = _dgid
            elif _dgname.find('reco') != -1:
                _reco_size = int(_dgroup_sz[:-1])
                try:
                    _reco_slice = int(_slice_sz[:-1])
                except:
                    _reco_slice = 0
                _reco_dg_id = _dgid
            elif _dgtype.find('sparse') != -1:
                _sparse_size = int(_dgroup_sz[:-1])
                try:
                    _sparse_slice = int(_slice_sz[:-1])
                except:
                    _sparse_slice = 0
                _sparse_dg_id = _dgid
        
            else:
                if _eBox.mGetVerbose() and _dgname.find('dbfs') == -1:
                    ebLogWarn('*** Unsuported DG found in configuration (%s)' % (_dgid))
                if _dgname.find('dbfs') != -1 and not _eBox.mCheckConfigOption('keep_dbfs_dg', 'True'):
                    _dbfs_size = int(_dgroup_sz[:-1])
                    _dbfs_dg_id = _dgid
        
        #
        # TODO: Add DBFS DG back to the storage pool (e.g. _total_dg below).
        #
        
        if _dbfs_dg_id is not None:  # Quorum is no more gated by 12.2 enabled
            if _eBox.mGetEnableQuorum():
                ebLogInfo('*** QUORUM enabled (and keep_dbfs_dg is False) removing DBFS DG: %s' % (_dbfs_dg_id))
                _cluster.mRemoveDiskGroup(_dbfs_dg_id)
                self.mRemoveDiskGroupConfig(_dbfs_dg_id)
            else:
                ebLogInfo('*** QUORUM disabled. DBFS DG + OCR enabled')
                # Ensure redundancy of DBFS diskgroup is set as NORMAL
                _dbfsConfig = self.mGetDiskGroupConfig(_dbfs_dg_id)
                if _dbfsConfig.mGetDgRedundancy() != "NORMAL":
                    _dbfsConfig.mSetDgRedundancy("NORMAL")
                    ebLogInfo("Setting DBFS diskgroup (%s) redundancy as NORMAL" % _dbfs_dg_id)

                # Ensure 'ocrVote' tag associated with DBFS diskgroup is set
                # to 'true' when sparse diskgroup is enabled.
                if _create_sparse and _dbfsConfig.mGetOCRVote() != 'true':
                    _dbfsConfig.mSetOCRVote('true')
        else:
            ebLogWarn('*** keep_dbfs_dg is enabled (bypassing QUORUM)')
            # Add DBFS_DG if not present in XML and  if quorum is disabled
            if not _eBox.mGetEnableQuorum() and _eBox.mGetRackSize() in ['eighth', 'quarter'] and _participant_node == 1: 
                ebLogWarn('*** add DBFS DG,  QUORUM is disabled and single node rac')
                _dbfsConfig = copy.deepcopy(self.mGetDiskGroupConfig(_data_dg_id))
                if "data" in _data_dg_id:
                    _dbfs_dg_id = _data_dg_id.replace("data", "dbfs")
                else:
                    _dbfs_dg_id = _eBox.mGenerateUUID()
                _dbfsConfig.mReplaceDgId(_dbfs_dg_id)
                _dbfsConfig.mReplaceDgName(_dbfsConfig.mGetDgName().replace("DATA", "DBFS"))
                self.mAddDiskGroupConfig(_dbfsConfig)
                _eBox.mGetClusters().mGetCluster().mAddCluDiskGroupConfig(_dbfs_dg_id)

                if _eBox.mGetRackSize() == 'quarter':
                    _dbfs_slice = 12
                    _dbfs_size = 216 
                else:
                    _dbfs_slice = 6
                    _dbfs_size = 108 
                _dbfsConfig.mSetSliceSize(_dbfs_slice)
                _dbfsConfig.mSetDiskGroupSize(_dbfs_size)
                _dbfsConfig.mSetOCRVote("true")
                _dbfsConfig.mSetQuorumDisk("false")
                _dbfsConfig.mSetDgRedundancy("NORMAL")
                _dbfsConfig.mSetDiskGroupType("")

        
        # Enable ASM Scoped Security if conf option is on AND QUORUM disks are also enabled

        if _eBox.mGetEnableAsmss() and _eBox.mGetEnableAsmss().lower() == "true":
            ebLogInfo('*** ASM Scoped Security enabled')
            _eBox.mGetClusters().mGetCluster().mSetCluAsmScopedSecurity('true')
        else:
            ebLogInfo('*** ASM Scoped Security disabled')
            _eBox.mGetClusters().mGetCluster().mSetCluAsmScopedSecurity('false')
        
        # Ensure redundancy of DATA diskgroup is set as HIGH
        if _data_dg_id is not None:
            _dataConfig = self.mGetDiskGroupConfig(_data_dg_id)
            if _dataConfig.mGetDgRedundancy() != "HIGH":
                _dataConfig.mSetDgRedundancy("HIGH")
                ebLogInfo("Setting DATA diskgroup (%s) redundancy as HIGH" % _data_dg_id)
    
        # Ensure redundancy of RECO diskgroup is set as HIGH
        if _reco_dg_id is not None:
            _recoConfig = self.mGetDiskGroupConfig(_reco_dg_id)
            if _recoConfig.mGetDgRedundancy() != "HIGH":
                _recoConfig.mSetDgRedundancy("HIGH")
                ebLogInfo("Setting RECO diskgroup (%s) redundancy as HIGH" % _reco_dg_id)

        # ER 26520207
                
        _eBox.mCheckSharedEnvironment()
        _racksize = _eBox.mGetRackSize()
        _disksize = _eBox.mGetEsracks().mGetDiskSize()

        if aOptions is not None:
            _jconf = aOptions.jsonconf
            if _jconf is not None and 'rack' in _jconf.keys() and 'size' in _jconf['rack'].keys() and _jconf['rack']['size'] == "BASE-RACK":
                ebLogInfo("BaseSystem Configuration detected in clustorage")
                _disksize = 7

        _cell_list = _eBox.mReturnCellNodes()
        _cell_name = list(_cell_list.keys())[0]
        _mac_cfg   = _eBox.mGetMachines().mGetMachineConfig(_cell_name)
        _ldisk_cnt = _mac_cfg.mGetLocaldisksCount()
        _disknb = _ldisk_cnt * len(_cell_list)

        ebLogInfo('*** Racksize : ' + _racksize + ' rack, Disksize : ' + str(_disksize) + 'TB, Total Celldisks : ' + str(_disknb))

        if _eBox.mGetEnableQuorum():
                _dbfs_size = 0
        _total_dg = _data_size + _reco_size + _sparse_size + _dbfs_size

        if _data_size < 0 or _reco_size < 0 or _sparse_size < 0 or _dbfs_size < 0 or _total_dg < 0: 
            _action_msg = "A negative size has been detected in the disk group. Please fix the XML cluster configuration file according to the instructions in the runbook."
            if _data_size < 0 :
                _err_msg = f'*** Data Storage Size is {_data_size}'
                ebLogCritical(_err_msg, _action_msg)
            if _reco_size < 0 :
                _err_msg = f'*** Reco Storage Size is {_reco_size}'
                ebLogCritical(_err_msg, _action_msg) 
            if _sparse_size < 0:
                _err_msg = f'*** Sparse Storage Size is {_sparse_size}'
                ebLogCritical(_err_msg, _action_msg) 
            if _dbfs_size < 0:
                _err_msg = f'*** DBFS Storage Size is {_dbfs_size}'
                ebLogCritical(_err_msg, _action_msg) 
            if _total_dg < 0:
                _err_msg = f'*** Total DB Storage Size is {_total_dg}'
                ebLogCritical(_err_msg, _action_msg)
            raise ExacloudRuntimeError(0x0746, 0xA, 'Invalid Input')

        if _eBox.mGetDbStorage() is not None:
            if _eBox.mCheckConfigOption('min_db_storage') is not None:
                _min_dbstorage = int(_eBox.mCheckConfigOption('min_db_storage')[:-2])
            else:
                _min_dbstorage = 2048
        
            if int(_eBox.mGetDbStorage()[:-1]) < _min_dbstorage:
                _total_dg = _min_dbstorage
            else:
                _total_dg = int(_eBox.mGetDbStorage()[:-1])
       
        if aTotalDGSize:
            _total_dg = aTotalDGSize

        ebLogInfo('*** Total DB Storage Size is %s' % (_total_dg))

        if _eBox.mGetCmd() == 'info':
            _reqobj = _eBox.mGetRequestObj()
            effectiveStorage = {}
            effectiveStorage['gb_storage'] = _total_dg
            if _reqobj is not None:
                _reqobj.mSetData(json.dumps(effectiveStorage, sort_keys=True))
                _db = ebGetDefaultDB()
                _db.mUpdateRequest(_reqobj)
            else:
                ebLogInfo(json.dumps(effectiveStorage, sort_keys=True))

        #############################################
        # start of disksize & slicesize calculations
        #############################################
        if not _create_sparse:
        
            ebLogInfo('Current DG Setup: DATA: ' + str(_data_slice) + 'G TOTAL: ' + str(_data_size))
            ebLogInfo('                  RECO: ' + str(_reco_slice) + 'G TOTAL: ' + str(_reco_size))
        
            _dataConfig = self.mGetDiskGroupConfig(_data_dg_id)
            _recoConfig = self.mGetDiskGroupConfig(_reco_dg_id)
        
            if not _backup_disk:
                #############################################
                # 80/20
                #############################################

                # If dynamic distrib DATA:RECO:SPARSE is given
                # then overwrites 80-20, else keep 80-20
                if _storage_distrib:
                    Dsplit = _dataPct
                    Rsplit = _recoPct                    
                    if _sparsePct > 0:
                        ebLogWarn("Sparse percentage provided but " + \
                            "create_sparse is False. Ignoring sparse pct.")
                else:
                    Dsplit, Rsplit = 80, 20

                if not _eBox.SharedEnv():
                    ebLogInfo('Single VM not sparse and backup2disk is false')
                    (_data_size, _reco_size, _data_slice, _reco_slice) = \
                        self.mGetDgVolsize(_disknb, _disksize, _dbfs_size, 
                            Dsplit, Rsplit, _eBox.SharedEnv(), 0)
                else:
                    ebLogInfo('Multi VM not sparse and backup2disk is false')
                    (_data_size, _reco_size, _data_slice, _reco_slice) = \
                        self.mGetDgVolsize(_disknb, _disksize, _dbfs_size, 
                            Dsplit, Rsplit, _eBox.SharedEnv(), _total_dg)
                    
                ebLogInfo(f'{Dsplit}%-{Rsplit}% DG Setup:') 
                ebLogInfo('    DATA: ' + str(_data_slice) + 'G TOTAL: ' + str(_data_size))
                ebLogInfo('    RECO: ' + str(_reco_slice) + 'G TOTAL: ' + str(_reco_size))

                _dataConfig.mSetSliceSize(_data_slice)
                _dataConfig.mSetDiskGroupSize(_data_size)
                _dataConfig.mSetDiskGroupType("data")
                _recoConfig.mSetSliceSize(_reco_slice)
                _recoConfig.mSetDiskGroupSize(_reco_size)
                _recoConfig.mSetDiskGroupType("reco")
        
            else:
                #############################################
                # 40/60 - backup2disk TRUE
                #############################################

                # If dynamic distrib DATA:RECO:SPARSE is given
                # then overwrites 40-60, else keep 40-60
                if _storage_distrib:
                    Dsplit = _dataPct
                    Rsplit = _recoPct
                    if _sparsePct > 0:
                        ebLogWarn("Sparse percentage provided but " + \
                            "create_sparse is False. Ignoring sparse pct.")
                else:
                    Dsplit, Rsplit = 40, 60

                if not _eBox.SharedEnv():
                    ebLogInfo('Single VM not sparse and backup2disk is true')
                    (_data_size, _reco_size, _data_slice, _reco_slice) = \
                        self.mGetDgVolsize(_disknb, _disksize, _dbfs_size, 
                            Dsplit, Rsplit, _eBox.SharedEnv(), 0)
                else:
                    ebLogInfo('Multi VM not sparse and backup2disk is true')
                    (_data_size, _reco_size, _data_slice, _reco_slice) = \
                        self.mGetDgVolsize(_disknb, _disksize, _dbfs_size, 
                            Dsplit, Rsplit, _eBox.SharedEnv(), _total_dg)

                ebLogInfo(f'{Dsplit}%-{Rsplit}% DG Setup:') 
                ebLogInfo('    DATA: ' + str(_data_slice) + 'G TOTAL: ' + str(_data_size))
                ebLogInfo('    RECO: ' + str(_reco_slice) + 'G TOTAL: ' + str(_reco_size))

                _dataConfig.mSetSliceSize(_data_slice)
                _dataConfig.mSetDiskGroupSize(_data_size)
                _dataConfig.mSetDiskGroupType("data")
                _recoConfig.mSetSliceSize(_reco_slice)
                _recoConfig.mSetDiskGroupSize(_reco_size)
                _recoConfig.mSetDiskGroupType("reco")
        else:
        
            # If create_sparse is chosen and XML doesn't contain a DG entry, add one.
            if _sparse_size == 0:
                ebLogInfo("*** Adding a SPARSE diskgroup entry")
        
                _sparseConfig = copy.deepcopy(self.mGetDiskGroupConfig(_data_dg_id))
                if "data" in _data_dg_id:
                    _sparse_dg_id = _data_dg_id.replace("data", "sparse")
                else:
                    _sparse_dg_id = _eBox.mGenerateUUID()
                _sparseConfig.mReplaceDgId(_sparse_dg_id)
                _sparseConfig.mReplaceDgName(_sparseConfig.mGetDgName().replace("DATA", "SPR"))
                _sparseConfig.mSetSparseDg("true")
                _sparseConfig.mSetOCRVote("false")
                _sparseConfig.mSetQuorumDisk("false")
                self.mAddDiskGroupConfig(_sparseConfig)
                _eBox.mGetClusters().mGetCluster().mAddCluDiskGroupConfig(_sparse_dg_id)
        
            ebLogInfo('Current DG Setup:   DATA: ' + str(_data_slice) + 'G TOTAL: ' + str(_data_size))
            ebLogInfo('                    RECO: ' + str(_reco_slice) + 'G TOTAL: ' + str(_reco_size))
            ebLogInfo('                  SPARSE: ' + str(_sparse_slice) + 'G TOTAL: ' + str(_sparse_size))
            _dataConfig = self.mGetDiskGroupConfig(_data_dg_id)
            _recoConfig = self.mGetDiskGroupConfig(_reco_dg_id)
            _sparseConfig = self.mGetDiskGroupConfig(_sparse_dg_id)
        
            if not _backup_disk:
                #############################################
                # 60/20/20
                #############################################

                # If dynamic distrib DATA:RECO:SPARSE is given
                # then overwrites 60-20-20, else keep 60-20-20
                if _storage_distrib:
                    Dsplit = _dataPct
                    Rsplit = _recoPct
                    Ssplit = _sparsePct
                    if Ssplit <= 0:
                        ebLogWarn("create_sparse is True but sparse pct " + \
                            " is 0 or not provided. This may result in a " + \
                            " zero-size sparse DG.")
                else:
                    Dsplit, Rsplit, Ssplit = 60, 20, 20
                
                if not _eBox.SharedEnv():
                    ebLogInfo('Single VM sparse is true, backup2disk is false')
                    (_data_size, _reco_size, _sparse_size, 
                     _data_slice, _reco_slice, _sparse_slice) = \
                        self.mGetDgVolsize(_disknb, _disksize, _dbfs_size,
                            Dsplit, Rsplit, _eBox.SharedEnv(), 0, Ssplit)
                else:
                    ebLogInfo('Multi VM sparse is true, backup2disk is false')
                    (_data_size, _reco_size, _sparse_size, 
                     _data_slice, _reco_slice, _sparse_slice) = \
                        self.mGetDgVolsize(_disknb, _disksize, _dbfs_size, 
                            Dsplit, Rsplit, _eBox.SharedEnv(), _total_dg, Ssplit)
                    
                _sparse_virtual_slice = _sparse_slice * _sparse_virtual_physical_ratio
                _sparse_virtual_size = _sparse_size * _sparse_virtual_physical_ratio
                                
                ebLogInfo(f'{Dsplit}%-{Rsplit}%-{Ssplit}% DG Setup:')
                ebLogInfo('    DATA: ' + str(_data_slice) + 'G TOTAL: ' + str(_data_size))
                ebLogInfo('    RECO: ' + str(_reco_slice) + 'G TOTAL: ' + str(_reco_size))
                ebLogInfo('    SPARSE: ' + str(_sparse_slice) + 'G TOTAL: ' + str(_sparse_size))

                _dataConfig.mSetSliceSize(_data_slice)
                _dataConfig.mSetDiskGroupSize(_data_size)
                _dataConfig.mSetDiskGroupType("data")
                _recoConfig.mSetSliceSize(_reco_slice)
                _recoConfig.mSetDiskGroupSize(_reco_size)
                _recoConfig.mSetDiskGroupType("reco")
                _sparseConfig.mSetSliceSize(_sparse_slice)
                _sparseConfig.mSetDiskGroupSize(_sparse_size)
                _sparseConfig.mSetSparseVirtualSize(_sparse_virtual_slice)
                _sparseConfig.mSetDiskGroupType("sparse")
            else:
                #############################################
                # 35/50/15
                #############################################

                # If dynamic distrib DATA:RECO:SPARSE is given
                # then overwrites 35-50-15, else keep 35-50-15
                if _storage_distrib:
                    Dsplit = _dataPct
                    Rsplit = _recoPct
                    Ssplit = _sparsePct
                    if Ssplit <= 0:
                        ebLogWarn("create_sparse is True but sparse pct " + \
                            "is 0 or not provided. This may result in a " + \
                            "zero-size sparse DG.")
                else:
                    Dsplit, Rsplit, Ssplit = 35, 50, 15

                if not _eBox.SharedEnv():
                    ebLogInfo('Single VM sparse is true, backup2disk is true')
                    (_data_size, _reco_size, _sparse_size, 
                     _data_slice, _reco_slice, _sparse_slice) = \
                        self.mGetDgVolsize(_disknb, _disksize, _dbfs_size, 
                            Dsplit, Rsplit, _eBox.SharedEnv(), 0, Ssplit)
                else:
                    ebLogInfo('Multi VM sparse is true, backup2disk is true')
                    (_data_size, _reco_size, _sparse_size, 
                     _data_slice, _reco_slice, _sparse_slice) = \
                        self.mGetDgVolsize(_disknb, _disksize, _dbfs_size, 
                            Dsplit, Rsplit, _eBox.SharedEnv(), _total_dg, Ssplit)
                    
                _sparse_virtual_slice = _sparse_slice * _sparse_virtual_physical_ratio
                _sparse_virtual_size = _sparse_size * _sparse_virtual_physical_ratio
                
                # 35/50/15 - backup2disk TRUE
                ebLogInfo(f'{Dsplit}%-{Rsplit}%-{Ssplit}% DG Setup:')
                ebLogInfo('    DATA: ' + str(_data_slice) + 'G TOTAL: ' + str(_data_size))
                ebLogInfo('    RECO: ' + str(_reco_slice) + 'G TOTAL: ' + str(_reco_size))
                ebLogInfo('    SPARSE: ' + str(_sparse_slice) + 'G TOTAL: ' + str(_sparse_size))

                _dataConfig.mSetSliceSize(_data_slice)
                _dataConfig.mSetDiskGroupSize(_data_size)
                _dataConfig.mSetDiskGroupType("data")
                _recoConfig.mSetSliceSize(_reco_slice)
                _recoConfig.mSetDiskGroupSize(_reco_size)
                _recoConfig.mSetDiskGroupType("reco")
                _sparseConfig.mSetSliceSize(_sparse_slice)
                _sparseConfig.mSetDiskGroupSize(_sparse_size)
                _sparseConfig.mSetSparseVirtualSize(_sparse_virtual_slice)
                _sparseConfig.mSetDiskGroupType("sparse")
        
        #############################################
        # end of disksize & slicesize calculations
        #############################################
        
        if _eBox.mGetEnableQuorum():
            ebLogInfo('*** 12.X GI ENABLED setting OCR Voting and QuorumDisk for DATA & RECO DGs')
            _dataConfig.mSetOCRVote('true')
            _dataConfig.mSetQuorumDisk('true')
            _recoConfig.mSetQuorumDisk('true')
            if _sparseConfig:
                _sparseConfig.mSetQuorumDisk('true')
                ebLogInfo('*** Setting QuorumDisk for SPARSE DG')
        else:
            # Quorum is disabled - Make sure Data/Reco is set accordingly.
            if _dbfs_size == 0:
                ebLogInfo('*** Quorum disabled OCR setting to Data and Quorum unset from Data/Reco')
                _dataConfig.mSetOCRVote('true')
                _dataConfig.mSetQuorumDisk('false')
                _recoConfig.mSetQuorumDisk('false')
            else:
                if not _eBox.mGetEnableQuorum() and _eBox.mGetRackSize() in ['eighth', 'quarter'] and _participant_node == 1:
                    _dataConfig.mSetOCRVote('false')
                    _dataConfig.mSetQuorumDisk('false')
                    _recoConfig.mSetQuorumDisk('false')
                    ebLogWarn('*** Single node rac config detected: Quorum disabled/DBFS active')
                else:
                    ebLogError('*** Obsolete configuration detected: Quorum disabled/DBFS active')

        _exadata_cell_model = _eBox.mGetExadataCellModel()
        _cutOff_model = 'X7'
        if _eBox.mGetCmd() not in ['elastic_info'] \
            and mCompareModel(_exadata_cell_model, _cutOff_model) >= 0:
            # calculate the acfs vol size as a factor of disksize
            # for 4TB disk -> 320GB of ACFS size per cell
            _avsize = _disksize * 40

            if not _eBox.SharedEnv():
                _avsize = _disksize * 80

            _dataConfig = self.mGetDiskGroupConfig(_data_dg_id)
            _modified_data_dg_size = _dataConfig.mGetDiskGroupSize()
            ebLogInfo("Current DATA DG size is: {0}".format(_modified_data_dg_size))
            _modified_data_dg_size = self.mGetDiskSizeInInt(_modified_data_dg_size)
            if _modified_data_dg_size is not None:
                _modified_data_dg_size = int(_modified_data_dg_size)
                if _avsize > (0.05 * _modified_data_dg_size):#Capping the ACFS volume size to 5% of current DATA DG size.
                    _avsize = int(0.05 * _modified_data_dg_size)
                if _avsize < 100:#If resultant ACFS vol. size is less than 100G, set it to a minimum of 100G.
                    _avsize = 100

            _acfsvolname = 'acfsvol01'
            _acfsmountpath = '/acfs01'
            ebLogInfo("Setting ACFS volume details: Volume Name: {0}, Volume size: {1}G, Mount path: {2}".format(_acfsvolname,_avsize,_acfsmountpath))
            _dataConfig.mSetAcfsVolumeName(_acfsvolname)
            _dataConfig.mSetAcfsVolumeSize(_avsize)
            _dataConfig.mSetAcfsMountPath(_acfsmountpath)


    def mGetDiskSizeInInt(self, aDgsz):
        aDgsz = aDgsz.strip()
        _size = 0
        if aDgsz[-2:] in ['gb', 'GB']:
            _size = int(aDgsz[:-2])
        elif aDgsz[-2:] in ['tb', 'TB']:
            _size = int(aDgsz[:-2])
        elif aDgsz[-1:] in ['g', 'G']:
            _size = int(aDgsz[:-1])
        elif aDgsz[-1:] in ['t', 'T']:
            _size = int(aDgsz[:-1])

        return _size

    #
    # ER 26520207
    #
    def mGetDgVolsize(self, *args):
        # HC disksize (in TB) adjustment after accounting for shortfall (in GB)
        # Calculate with this example: index 18 = (9123/10)*18 = 16421.3

        # As per Bug 38253988, DATA:RECO:SPARSE splits may be float 

        asize = {2: 1823, 3: 2759, 4: 3646, 7: 6386, 8: 7290, 10: 9123, 14:12772, 18:16421, 22:20489} #Basesystem is 7
        
        _eBox = self.mGetEbox()
        # disk_count = Cell_count in rack * Disks per cell
        disk_count = int(args[0])
        disksize = float(args[1])
        dbfs_size = int(args[2])
        Dsplit = float(args[3])
        Rsplit = float(args[4])
        isMVM = args[5]
        total_dg = int(args[6])

        # t -> total diskgroup size of the cluster
        t=0
        if not _eBox.IsZdlraProv() and ( isMVM or _eBox.mGetCmd() == "elastic_cell_update"):
            t = ((total_dg - dbfs_size) * 3) # include redundancy factor
        else:
            t = (asize[disksize] * disk_count) - (dbfs_size * disk_count // 12)
            if _eBox.mGetExadataCellModel() == 'X6' and disksize == 7 :
                t = t - 2000  # this number can be as low as 1152

        # initialize matrices for solving the set of linear equations

        A = [[0 for x in range(3)] for y in range(3)]
        adjA = [[0 for x in range(3)] for y in range(3)]
        invA = [[0 for x in range(3)] for y in range(3)]
        vecT = [[0 for x in range(1)] for y in range(3)]

        # Data, Reco & Sparse
        if len(args) == 8:
            Ssplit = float(args[7])

            # Solve the set of linear eqns. Matrix A
            A[0][0] = 3
            A[0][1] = 3
            A[0][2] = 3
            A[1][0] = Rsplit
            A[1][1] = (-1 * Dsplit)
            A[1][2] = 0
            A[2][0] = 0
            A[2][1] = Ssplit
            A[2][2] = (-1 * Rsplit)

            # column vector T
            vecT[0][0] = t
            vecT[1][0] = 0
            vecT[2][0] = 0

            # determinant of matrix A
            detA = (A[0][0] * A[1][1] * A[2][2] + A[0][1] * A[1][2] * A[2][0] + A[0][2] * A[1][0] * A[2][1]) - \
                   (A[0][2] * A[1][1] * A[2][0] + A[0][1] * A[1][0] * A[2][2] + A[0][0] * A[1][2] * A[2][1])

            # adjoint (cofactor + transpose) of matrix A
            adjA[0][0] = (A[1][1] * A[2][2]) - (A[1][2] * A[2][1])
            adjA[0][1] = -1 * ((A[0][1] * A[2][2]) - (A[2][1] * A[0][2]))
            adjA[0][2] = (A[0][1] * A[1][2]) - (A[0][2] * A[1][1])
            adjA[1][0] = -1 * ((A[1][0] * A[2][2]) - (A[1][2] * A[2][0]))
            adjA[1][1] = (A[0][0] * A[2][2]) - (A[0][2] * A[2][0])
            adjA[1][2] = -1 * ((A[0][0] * A[1][2]) - (A[0][2] * A[1][0]))
            adjA[2][0] = (A[1][0] * A[2][1]) - (A[1][1] * A[2][0])
            adjA[2][1] = -1 * ((A[0][0] * A[2][1]) - (A[0][1] * A[2][0]))
            adjA[2][2] = (A[0][0] * A[1][1]) - (A[0][1] * A[1][0])

            # inverse of matrix A
            invA[0][0] = (1 / (1.0 * detA)) * adjA[0][0]
            invA[0][1] = (1 / (1.0 * detA)) * adjA[0][1]
            invA[0][2] = (1 / (1.0 * detA)) * adjA[0][2]
            invA[1][0] = (1 / (1.0 * detA)) * adjA[1][0]
            invA[1][1] = (1 / (1.0 * detA)) * adjA[1][1]
            invA[1][2] = (1 / (1.0 * detA)) * adjA[1][2]
            invA[2][0] = (1 / (1.0 * detA)) * adjA[2][0]
            invA[2][1] = (1 / (1.0 * detA)) * adjA[2][1]
            invA[2][2] = (1 / (1.0 * detA)) * adjA[2][2]

            # solution vector
            volszD = int(invA[0][0] * vecT[0][0])
            volszR = int(invA[1][0] * vecT[0][0])
            volszS = int(invA[2][0] * vecT[0][0])

            # calculate slice size
            sliceD = int(volszD * 3 / disk_count)
            sliceR = int(volszR * 3 / disk_count)
            sliceS = int(volszS * 3 / disk_count)

            return (volszD, volszR, volszS, sliceD, sliceR, sliceS)

        else:

            # Data & Reco

            # Solve the set of linear eqns. Matrix A
            A[0][0] = 3
            A[0][1] = 3
            A[1][0] = Rsplit
            A[1][1] = (-1 * Dsplit)

            # column vector T
            vecT[0][0] = t
            vecT[1][0] = 0

            # determinant of matrix A
            detA = (A[0][0] * A[1][1]) - (A[0][1] * A[1][0])

            # adjoint (cofactor + transpose) of matrix A
            # adjA[0][0] = (A[1][1] * A[2][2]) - (A[1][2] * A[2][1]) assig below
            adjA[0][0] = A[1][1]
            adjA[0][1] = -1 * A[0][1]
            adjA[1][0] = -1 * A[1][0]
            adjA[1][1] = A[0][0]

            # inverse of matrix A
            invA[0][0] = (1 / (1.0 * detA)) * adjA[0][0]
            invA[0][1] = (1 / (1.0 * detA)) * adjA[0][1]
            invA[1][0] = (1 / (1.0 * detA)) * adjA[1][0]
            invA[1][1] = (1 / (1.0 * detA)) * adjA[1][1]

            # solution vector
            volszD = int(invA[0][0] * vecT[0][0])
            volszR = int(invA[1][0] * vecT[0][0])

            # calculate slice size
            sliceD = int(volszD * 3 / disk_count)
            sliceR = int(volszR * 3 / disk_count)

            return (volszD, volszR, sliceD, sliceR)

#
# ebCluManageStorage manages all the diskgroups during storage resize
#
class ebCluManageStorage(object):
   
    # Constants defined for the class
    OLDSIZE_GB = "OLDSIZE_GB"
    NEWSIZE_GB = "NEWSIZE_GB"
    DATA = "DATA"
    RECO = "RECO" 
    SPARSE = "SPARSE"
    DG_NEWSIZE = "DG_NEWSIZE"
    DG_NAME = "DG_NAME"
    REBALANCE_POWER = "rebalance_power"

    def __init__(self, aExaBoxCluCtrl, aOptions):

        self.__config = get_gcontext().mGetConfigOptions()
        self.__xmlpath = aOptions.configpath
        self.__ebox = aExaBoxCluCtrl

        self.__verbose = self.__ebox.mGetVerbose()
        
        # Object to store results
        self.__storageData = {}

        # Initialize the constants object
        self._constantsObj = ebDiskgroupOpConstants() 
        self.__rebalancedata = False
        self.__rebalancereco = False
        self.__rebalancesprs = False
        self.__resizedata = True
        self.__resizereco = True
        self.__resizesprs = True
       
    def mGetEbox(self):
        return self.__ebox

    def mGetStorageOperationData(self):
        return self.__storageData

    def mSetStorageOperationData(self, aStorageData):
        self.__storageData = aStorageData

    def mGetConstantsObj(self):
        return self._constantsObj

    # mClusterStorageResize -
    # Resizes DATA and RECO diskgroups (and SPARSE diskgroup) maintaining the
    # original ratio of the diskgroups.
    #
    # Currently the ratio of the sizes of the diskgroups are as follows -
    # if SPARSE diskgroup is present,
    # sizes of DATA: RECO: SPARSE DG is retained in the following ratios -
    # 60:20:20 if disk backup is not enabled
    # 35:50:15 if disk backup is enabled
    # 
    # if SPARSE diskgroup is not present,
    # sizes of DATA: RECO DG is retained in the following ratios -
    # 80:20 if disk backup is not enabled
    # 40:60 if disk backup is enabled
    # 

    def mClusterStorageResize(self, aOptions, aJson=None):

        _options = aOptions
        _inparams = {}
        _storage_data = self.mGetStorageOperationData()
        _storage_data["Command"] = "storage_resize"
        _storage_data["Status"] = "Pass"
        _storage_data["ErrorCode"] = "0"
        _dgmap = {}
        
        _oldsizeGB = 0.0 
        _newsizeGB = 0.0
        _eBoxCluCtrl = self.mGetEbox()
        _clu_utils = ebCluUtils(_eBoxCluCtrl)
        if aJson:
            _json = aJson
        else:
            _json = aOptions.jsonconf

        ebLogTrace(f"mClusterStorageResize options: {aOptions}")
        _rc = self.mClusterParseInputJson(_json, _inparams)
        if _rc != 0:
            _err = "Returning due to input args related error"
            ebLogError(_err)
            _storage_data["Status"] = "Fail"
            _storage_data["ErrorCode"] = "-1"
            _storage_data["Log"] = _err
            self.mUpdateRequestData(_storage_data, _options)
            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['INVALID_INPUT_PARAMETER'],_err)
            return _rc
        else:
            _oldsizeGB = float(_inparams[self.OLDSIZE_GB])
            _newsizeGB = float(_inparams[self.NEWSIZE_GB])
            ebLogInfo("mClusterStorageResize: Old storage size = %f, New storage size = %f" %(_oldsizeGB, _newsizeGB))
            
        """        
        if _newsizeGB == _oldsizeGB:
            _msg = "As per payload, old size and new size of storage " + \
                    "are of same size. Thus resize is not attempted."
            ebLogInfo("mClusterStorageResize: " + _msg)
            _storage_data["Status"] = "Pass"
            _storage_data["ErrorCode"] = "0"
            _storage_data["Log"] = _msg
            self.mUpdateRequestData(_storage_data, _options)
            return _rc
        """

        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("reshapeDetails", 'ONGOING', "ASM reshape in progress parsing inputs", "","ASM")
        _clu_utils.mUpdateTaskProgressStatus([], 5, "ASM Reshape", "In Progress", _stepSpecificDetails)
        _dgObj = ebCluManageDiskgroup(_eBoxCluCtrl, _options)
        
        # populate the new sizes of DATA, RECO (and SPARSE) diskgroups in 
        # _dgmap.
        # Note: mGetDiskgroupsNewSizes() does not really need the old storage 
        # value. It just requires the new storage value to estimate the 
        # distribution among different diskgroups (maintaining existing ratios)
        _rc = self.mGetDiskgroupsNewSizes(_options, _dgObj, _newsizeGB, _dgmap)
        if _rc != 0:
            _err = "Failed to get new sizes of DATA, RECO (and SPARSE) diskgroups"
            ebLogError(_err)
            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_FETCHING_NEW_SIZES_DG'],_err)
            return _rc

        #
        # Check if the target size satisfies MAA minium FreeSpace recommendation:
        # 15% for 3-4 cells, or 9% for >= 5 cells
        if _options.jsonconf and str(
                _options.jsonconf.get(f"allow_flexible_shrink")).lower() == "true":
            ebLogInfo(f"Detected flag 'allow_flexible_shrink' to allow "
                "DiskGroup size increase during shrink if each "
                "diskgroup has enough Free space to perform the resize")

            _dgmap = self.mCheckMinFreeSpaceDGShrink(aOptions, _dgmap)

        #check if the disks are resizable 
        _stepSpecificDetails = _clu_utils.mStepSpecificDetails("reshapeDetails", 'ONGOING', "ASM reshape in progress performing DG resizable check", "","ASM")
        _clu_utils.mUpdateTaskProgressStatus([], 8, "ASM Reshape", "In Progress", _stepSpecificDetails)
        _rc = _dgObj.mCheckIfDgResizableAll(_options,_dgmap)
        if _rc != 0:
            _err = "Failed resizable check for diskgroups"
            ebLogError(_err)
            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_RESIZE_CHECK_FAILED'],_err)
            return _rc
        
        _eBoxCluCtrl.mUpdateStatus('ASM resize in progress', False)        
        if not _dgmap.get(self.SPARSE):
            _dgmap[self.SPARSE][self.DG_NAME] = None
            _dgmap[self.SPARSE][self.DG_NEWSIZE] = None
            ebLogTrace(f"SPARSE is not detected so deleting from input object")
        # Resize DATA, RECO (and SPARSE) diskgroups based on the new sizes 
        # present in _dgmap.
        _rc = self.mUtilStorageResize(_dgObj, _options, _dgmap, _rc)
        if _rc != 0:
            _err = "Storage resize failed"
            ebLogError("mClusterStorageResize: " + _err)
            _storage_data["Status"] = "Fail"
            _storage_data["ErrorCode"] = "-1"
            _storage_data["Log"] = _err
            self.mUpdateRequestData(_storage_data, _options)
            ebLogError(json.dumps(_storage_data, indent=4, sort_keys=True))
            _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_STORAGE_RESIZE_FAIL'],_err)
            return _rc

        _log = "Storage resize went successful. "
        ebLogInfo("mClusterStorageResize: " + _log)
        _storage_data["Status"] = "Pass"
        _storage_data["ErrorCode"] = "0"
        _storage_data["Log"] = _log

        self.mUpdateRequestData(_storage_data, _options)
        ebLogInfo(json.dumps(_storage_data, indent=4, sort_keys=True))
        return _rc 

    # mGetSize -
    # function to remove trailing G,GB,T,TB from sizes.
    def mGetDiskSizeInInt(self, aDgsz):
        aDgsz = aDgsz.strip()
        _size = 0
        if aDgsz[-2:] in ['gb', 'GB']:
            _size = int(aDgsz[:-2])
        elif aDgsz[-2:] in ['tb', 'TB']:
            _size = int(aDgsz[:-2])
        elif aDgsz[-1:] in ['g', 'G']:
            _size = int(aDgsz[:-1])
        elif aDgsz[-1:] in ['t', 'T']:
            _size = int(aDgsz[:-1])

        return _size

    # mGetDiskgroupsNewSizes -
    # function to populate the new sizes of DATA, RECO (and SPARSE) 
    # diskgroups in aDGMap
    def mGetDiskgroupsNewSizes(self, aOptions, aDGObj, aNewSizeGB, aDGMap):

        _options = aOptions
        _dgObj = aDGObj
        _storage_data = self.mGetStorageOperationData()
        # Get the cluctrl handle to fetch current details
        _eBoxCluCtrl = self.mGetEbox()
        # Get the constants object for use in the scope of this function
        _constantsObj = self.mGetConstantsObj()
        _dgMap = aDGMap

        _dg_data = {}
        _data_dg = None
        _reco_dg = None
        _sparse_dg = None
        _sparse_dgname = None
        _data_dgname = None
        _reco_dgname = None
        _new_sprsize = 0
        _new_datasize = 0
        _new_recosize = 0
        _data_usedspace = 0
        _reco_usedspace = 0
        _spr_usedspace = 0

        _cluster = _eBoxCluCtrl.mGetClusters().mGetCluster()

        _cludgroups = _cluster.mGetCluDiskGroups()

        _data = {}
        _sparse_enabled = False

        for _dgid in _cludgroups:
            if _data_dg is not None and \
                _reco_dg is not None and \
                _sparse_dg is not None:
                break
            _dg = _eBoxCluCtrl.mGetStorage().mGetDiskGroupConfig(_dgid)
            _dg_type = _dg.mGetDiskGroupType().lower()
            if _dg_type == _constantsObj._data_dg_type_str:
                _data_dg = _dg
                _data_dgname = _data_dg.mGetDgName()
                _data_dgsize = _data_dg.mGetDiskGroupSize()
                ebLogInfo("*** DATA DG size from xml is : %s" %(_data_dgsize))
                _data_dgsize = self.mGetDiskSizeInInt(_data_dgsize)

                if _data_dg.mGetDgRedundancy() == "HIGH":
                    _redundancy_factor = 3
                elif _data_dg.mGetDgRedundancy() == "NORMAL":
                    _redundancy_factor = 2
                else:
                    _redundancy_factor = 1

            if _dg_type == _constantsObj._reco_dg_type_str:
                _reco_dg = _dg
                _reco_dgname = _reco_dg.mGetDgName()
                _reco_dgsize = _reco_dg.mGetDiskGroupSize()
                ebLogInfo("*** RECO DG size from xml is : %s" %(_reco_dgsize))
                _reco_dgsize = self.mGetDiskSizeInInt(_reco_dgsize)

            if _dg_type == _constantsObj._sparse_dg_type_str:
                _sparse_dg = _dg
                _sparse_dgname = _sparse_dg.mGetDgName()
                _spr_dgsize = _sparse_dg.mGetDiskGroupSize()
                _sparse_enabled = True
                ebLogInfo("*** SPARSE DG size from xml is : %s" %(_spr_dgsize))
                _spr_dgsize = self.mGetDiskSizeInInt(_spr_dgsize)
            
        # Input passed as json is usable storage value.
        # Thus factor in redundancy to calculate the total storage value
        # to be used below.
        # Assumption: DATA, RECO (and SPARSE) all have same redundancy.
        # Thus no need to determine redundancy of individual diskgroups.
        _newsizeGB = aNewSizeGB * _redundancy_factor
 
        # Validate DATA dg (_data_dgname)

        _dgObj.mSetDiskGroupOperationData(_dg_data)
        _storage_data[_data_dgname] = {}
        _data_cursizeMB = _dgObj.mUtilGetDiskgroupSize(
            _options, _data_dgname, _constantsObj)

        if _data_cursizeMB == -1:
            _err = "*** Invalid size of diskgroup " + _data_dgname
            _storage_data[_data_dgname]["Log"] = _err
            return self.mRecordError(gDiskgroupError['InvalidPropValue'], _err)
        _data_cursize = _data_cursizeMB / float(1024)

        _dgObj.mSetDiskGroupOperationData(_dg_data)
        _data_usedspace = _dgObj.mUtilGetDiskgroupSize(
            _options, _data_dgname, _constantsObj, "usedMb") / float(1024)

        if _data_usedspace == -1:
            _err = "*** Invalid usedspace of diskgroup " + _data_dgname
            _storage_data[_data_dgname]["Log"] = _err
            return self.mRecordError(gDiskgroupError['InvalidPropValue'], _err)

        # Validate RECO dg (_reco_dgname)

        _dgObj.mSetDiskGroupOperationData(_dg_data)
        _storage_data[_reco_dgname] = {}
        _reco_cursizeMB = _dgObj.mUtilGetDiskgroupSize(
            _options, _reco_dgname, _constantsObj)

        if _reco_cursizeMB == -1:
            _err = "*** Invalid size of diskgroup " + _reco_dgname
            _storage_data[_reco_dgname]["Log"] = _err
            return self.mRecordError(gDiskgroupError['InvalidPropValue'], _err)
        _reco_cursize = _reco_cursizeMB / float(1024)

        _dgObj.mSetDiskGroupOperationData(_dg_data)
        _reco_usedspace = _dgObj.mUtilGetDiskgroupSize(
            _options, _reco_dgname, _constantsObj, "usedMb") / float(1024)

        if _reco_usedspace == -1:
            _err = "*** Invalid usedspace of diskgroup " + _reco_dgname
            _storage_data[_data_dgname]["Log"] = _err
            return self.mRecordError(gDiskgroupError['InvalidPropValue'], _err)
        
        # Read payload

        _jconf = aOptions.jsonconf

        _backup_flag_enabled = None
        _sparse_flag_enabled = None

        _storage_distrib = None
        if 'storage_distribution' in list(_jconf.keys()) :  
            # This is Reshape workflow
            _backup_flag_enabled = _jconf['backup_disk']
            _sparse_flag_enabled = _jconf['create_sparse']
            _storage_distrib     = _jconf['storage_distribution']

        elif 'rack' in list(_jconf.keys()) :  
            # This is Create Service workflow
            _backup_flag_enabled = _jconf['rack']['backup_disk']
            _sparse_flag_enabled = _jconf['rack']['create_sparse']
            if 'storage_distribution' in list(_jconf['rack'].keys()):
                _storage_distrib = _jconf['rack']['storage_distribution']
                ebLogInfo(f'DATA:RECO:SPARSE Distribution : {_storage_distrib}')

        if _storage_distrib:
            _dataPct, _recoPct, _sparsePct = \
                mParseStorageDistrib(_storage_distrib)

        ############################################################
        # start of disksize & slicesize calculations for reshape
        ############################################################
        ebLogInfo(f'_sparse dg exists in curr cluster: {_sparse_enabled}')

        ebLogInfo(f'_backup_flag_enabled (payload): {_backup_flag_enabled}')
        ebLogInfo(f'_sparse_flag_enabled (payload): {_sparse_flag_enabled}')

        if _sparse_enabled: # if sparse DOES exist in current diskgroups
        
            _dgObj.mSetDiskGroupOperationData(_dg_data)
            _storage_data[_sparse_dgname] = {}
            _spr_cursize = 0
            _spr_usedspace = 0 
            _sparse_usage_percentage, _spr_cursize, _spr_usedspace = \
                self.mDgUsagePercentage(_options, _dgObj, _sparse_dgname)

            ## This is virtual size of sparse and should be converted into real size
            if _spr_usedspace == -1:
                _err = "*** Invalid usedspace of diskgroup " + _sparse_dgname
                _storage_data[_data_dgname]["Log"] = _err
                return self.mRecordError(
                    gDiskgroupError['InvalidPropValue'], _err)

            # sparse used value received from dbaasapi call is virtual sparse.
            # Need to convert to physical sparse size
            _spr_usedspace = _spr_usedspace / \
                self._constantsObj.mGetSparseVsizeFactor()
            # sparse current size value received from dbaasapi call is virtual
            # sparse. Need to convert to physical sparse size
            _spr_cursize = _spr_cursize / \
                self._constantsObj.mGetSparseVsizeFactor()
                
            _current_total_sizeGB = _data_cursize + _reco_cursize + _spr_cursize
            _shrink = False
            if _current_total_sizeGB > _newsizeGB:
                _shrink = True
            #DATA : RECO: SPARSE ratio is:
            #35:50:15 if Local Backups option was selected in UI
            #60:20:20 if Local Backups option was NOT selected in UI
            # 35:50:15 if Local Backups option was selected in UI
            # 60:20:20 if Local Backups option was NOT selected in UI
            if _sparse_usage_percentage < 50 or _shrink == False:
                if _backup_flag_enabled == "true":
                    # If dynamic distrib DATA:RECO:SPARSE is given
                    # then overwrites 35-50-15, else keep them
                    if _storage_distrib:
                        Dsplit = _dataPct / 100
                        Rsplit = _recoPct / 100
                        Ssplit = _sparsePct / 100
                    else:
                        Dsplit = 0.35
                        Rsplit = 0.50
                        Ssplit = 0.15
                    ebLogInfo(f'DRS1: {Dsplit}%-{Rsplit}%-{Ssplit}% DG Setup')

                else:
                    # If dynamic distrib DATA:RECO:SPARSE is given
                    # then overwrites 60-20-20, else keep them
                    if _storage_distrib:
                        Dsplit = _dataPct / 100
                        Rsplit = _recoPct / 100
                        Ssplit = _sparsePct / 100
                    else:
                        Dsplit = 0.60
                        Rsplit = 0.20
                        Ssplit = 0.20
                    ebLogInfo(f'DRS2: {Dsplit}%-{Rsplit}%-{Ssplit}% DG Setup')
                    
                _new_datasize = Dsplit * float(_newsizeGB)
                _new_recosize = Rsplit * float(_newsizeGB)
                _new_sprsize  = Ssplit * float(_newsizeGB)

            else:
                # we need to make sure we have 50% empty space 
                # available for sparse
                _new_sprsize = 2 * _spr_usedspace 
                                
                if _backup_flag_enabled == "true":
                    # If dynamic distrib DATA:RECO:SPARSE is given
                    # then overwrites 35-50-X, else keep them
                    if _storage_distrib:
                        Dsplit = _dataPct
                        Rsplit = _recoPct
                    else:
                        Dsplit = 35.0
                        Rsplit = 50.0
                    ebLogInfo(f'DRS3: {Dsplit}%-{Rsplit}% DG Setup')
                    
                    DRsplitSum = Dsplit + Rsplit

                    #ratio of size between DATA and RECO should remain the same
                    _new_datasize = \
                        (Dsplit * float(_newsizeGB - _new_sprsize))/DRsplitSum
                    _new_recosize = \
                        (Rsplit * float(_newsizeGB - _new_sprsize))/DRsplitSum
                else:
                    # If dynamic distrib DATA:RECO:SPARSE is given
                    # then overwrites 60-20-X, else keep them
                    if _storage_distrib:
                        Dsplit = _dataPct
                        Rsplit = _recoPct
                    else:
                        Dsplit = 60.0
                        Rsplit = 20.0
                    ebLogInfo(f'DRS4: {Dsplit}%-{Rsplit}% DG Setup')

                    DRsplitSum = Dsplit + Rsplit

                    #ratio of size between DATA and RECO should remain the same
                    _new_datasize = \
                        (Dsplit * float(_newsizeGB - _new_sprsize))/DRsplitSum
                    _new_recosize = \
                        (Rsplit * float(_newsizeGB - _new_sprsize))/DRsplitSum

        else: # if sparse DOES NOT exist in current diskgroups

            # DATA : RECO ratio is :
            # 40:60 if Local Backups option was selected in UI
            # 80:20 if Local Backups option was NOT selected in UI
            if _backup_flag_enabled == "true":
                # If dynamic distrib DATA:RECO:SPARSE is given
                # then overwrites 40-60-X, else keep them
                if _storage_distrib:
                    Dsplit = _dataPct / 100
                    Rsplit = _recoPct / 100
                else:
                    Dsplit = 0.4
                    Rsplit = 0.6
                ebLogInfo(f'DRS5: {Dsplit}%-{Rsplit}% DG Setup')

                _new_datasize = Dsplit * float(_newsizeGB)
                _new_recosize = Rsplit * float(_newsizeGB)
            else:
                # If dynamic distrib DATA:RECO:SPARSE is given
                # then overwrites 80-20-X, else keep them
                if _storage_distrib:
                    Dsplit = _dataPct / 100
                    Rsplit = _recoPct / 100
                else:
                    Dsplit = 0.8
                    Rsplit = 0.2
                ebLogInfo(f'DRS6: {Dsplit}%-{Rsplit}% DG Setup')

                _new_datasize = Dsplit * float(_newsizeGB)
                _new_recosize = Rsplit * float(_newsizeGB)

        if _new_datasize < _data_usedspace or \
            _new_recosize < _reco_usedspace or \
           (_sparse_enabled and _new_sprsize < _spr_usedspace):
            # Ref 38550997
            # Allow Exaloud to calculate new TargetSize with
            # 15% or 9% FreeSpace in each ASM diskgroup
            if aOptions.jsonconf and str(aOptions.jsonconf.get(
                f"allow_flexible_shrink")).lower() == "true":
                ebLogInfo(f"Detected flag 'allow_flexible_shrink' to allow "
                    "extra free space requirement calculation")
            else:
                _err = "Resize will lead to loss of DATA/RECO (or SPARSE) " + \
                       "diskgroup with current configuration."
                ebLogInfo("mGetDiskgroupsNewSizes: " + _err)
                _storage_data["Status"] = "Fail"
                _storage_data["ErrorCode"] = "1"
                _storage_data["Log"] = _err
                return self.mRecordError(gDiskgroupError['InvalidResize'])

        ebLogInfo("mGetDiskgroupsNewSizes: %s: current total size(GB): %f, " \
                  "used space(GB): %f, new total size(GB): %f" %(_data_dgname,\
                  _data_cursize, _data_usedspace, _new_datasize))

        ebLogInfo("mGetDiskgroupsNewSizes: %s: current total size(GB): %f, " \
                  "used space(GB): %f, new total size(GB): %f" %(_reco_dgname,\
                  _reco_cursize, _reco_usedspace, _new_recosize))

        if _sparse_enabled:

            ebLogInfo("mGetDiskgroupsNewSizes: %s: current total size(GB): %f," \
                      " used space(GB): %f, new total size(GB): %f" %(_sparse_dgname,\
                      _spr_cursize, _spr_usedspace, _new_sprsize))

        _dgMap[self.DATA] = {}
        _dgMap[self.RECO] = {}
        _dgMap[self.SPARSE] = {}
        _dgMap[self.DATA][self.DG_NAME] = _data_dgname
        _dgMap[self.DATA][self.DG_NEWSIZE] = _new_datasize

        _dgMap[self.RECO][self.DG_NAME] = _reco_dgname
        _dgMap[self.RECO][self.DG_NEWSIZE] = _new_recosize
        
        _dgMap[self.SPARSE][self.DG_NAME] = _sparse_dgname
        _dgMap[self.SPARSE][self.DG_NEWSIZE] = _new_sprsize

        # actual disk size is usually little more than input size... 
        # keeping it to 1% for now.

        # previously failed during disk rebalance.
        if (abs(float((_data_cursize - _new_datasize) / _new_datasize)) < 0.01):
            ebLogInfo("*** Data size is same.. resize not required. "+
                      "Will attempt a rebalance. !")
            self.__rebalancedata = True
            self.__resizedata = False
            # Check if Data grid disks are resized on cells
            if not self.mCheckGridDisksResizedCells(
                    _data_dgname, _new_datasize, _dgObj):
                _dgObj.mSetResizeDataOnCells(True)

        # previously failed during reco rebalance.
        if (abs(float((_reco_cursize - _new_recosize) / _new_recosize)) < 0.01):
            ebLogInfo("*** Reco size is same.. resize not required. " +
                      "Will attempt a rebalance. !")
            self.__rebalancereco = True
            self.__resizereco = False
            # Check if Reco grid disks are resized on cells
            if not self.mCheckGridDisksResizedCells(
                    _reco_dgname, _new_recosize, _dgObj):
                _dgObj.mSetResizeRecoOnCells(True)

        # previously failed during sparse rebalance.
        if (_sparse_enabled and (abs(float((_spr_cursize - _new_sprsize) / _new_sprsize)) < 0.01)):
            ebLogInfo("*** Sparse size is same.. resize not required. "+
                      "Will attempt a rebalance. !")
            self.__rebalancesprs = True
            self.__resizesprs = False
            # Check if Sparse grid disks are resized on cells
            if not self.mCheckGridDisksResizedCells(
                    _sparse_dgname, _new_sprsize, _dgObj):
                _dgObj.mSetResizeSparseOnCells(True)

        ebLogTrace(f'Returning dgMap to ecra: {_dgMap}')
        req = _eBoxCluCtrl.mGetRequestObj()
        if req is not None:
            req.mSetData(_dgMap)
            db = ebGetDefaultDB()
            db.mUpdateRequest(req)
            ebLogInfo('mGetDiskgroupsNewSizes db.mUpdateRequest')

        return 0
    # end of mGetDiskgroupsNewSizes

    def mFetchAndSaveDGSizes(self, aCludgroupsElement, aDgSizesDict):
        
        ebLogInfo("*** ebCluElasticCellManager:mFetchAndSaveDGSizes >>>")
        
        _cludgroups = aCludgroupsElement
        _dg_sizes_dict = aDgSizesDict
        _eBoxCluCtrl = self.mGetEbox()
        _cluDgObj = ebCluManageDiskgroup(_eBoxCluCtrl, _eBoxCluCtrl.mGetArgsOptions())
        _dgConstantsObj = _cluDgObj.mGetConstantsObj()
        _rc = 0
        for _dgid in _cludgroups:
            _dg = _eBoxCluCtrl.mGetStorage().mGetDiskGroupConfig(_dgid)
            _dg_type = _dg.mGetDiskGroupType().lower()
            if _dg_type in [_dgConstantsObj._data_dg_type_str, _dgConstantsObj._reco_dg_type_str, _dgConstantsObj._sparse_dg_type_str]:
                _dg_name = _dg.mGetDgName()
                _dgrp_properties = []
                _dgrp_properties.append(_dgConstantsObj._propkey_storage)

                _size_dict = {}
                _rc = _cluDgObj.mUtilGetDiskgroupSize(_eBoxCluCtrl.mGetArgsOptions(), _dg_name, _dgConstantsObj)
                if _rc == -1:
                    _detail_error = "Could not fetch info for diskgroup " + _dg_name
                    _eBoxCluCtrl.mUpdateErrorObject(gElasticError['CELL_DG_INFO_FETCH_FAILED'], _detail_error) 
                    return self.mRecordError(gDiskgroupError['ErrorFetchingDetails'], "*** " + _detail_error)
    
                ## Save the totalgb size (GB) of diskgroups in the dictionary for restoration.
                if _dg_type == _dgConstantsObj._sparse_dg_type_str:
                    _size_dict['totalgb'] = int(_rc) / (1024 * _cluDgObj.mGetConstantsObj().mGetSparseVsizeFactor())  # Size is returned in MBs
                else:
                    _size_dict['totalgb'] = int(_rc) / 1024 # Size is returned in MBs
                _rc = 0 
    
                _rc = _cluDgObj.mUtilGetDiskgroupSize(_eBoxCluCtrl.mGetArgsOptions(), _dg_name, _dgConstantsObj, True)
                if _rc == -1: 
                    _detail_error = "Could not fetch info for diskgroup " + _dg_name
                    _eBoxCluCtrl.mUpdateErrorObject(gElasticError['CELL_DG_INFO_FETCH_FAILED'], _detail_error)
                    return self.mRecordError(gDiskgroupError['ErrorFetchingDetails'], "*** " + _detail_error)
    
                ## Save the usedgb size (GB) of diskgroups in the dictionary for restoration.
                _size_dict['usedgb'] = int(_rc) / 1024 # Size is returned in MBs
                _rc = 0 
                _dg_sizes_dict[_dg_name] = _size_dict
                # Sample Json for _dg_sizes_dict
                #    "DATAC7": {
                #        "totalgb": 24552,
                #        "usedgb": 637
                #    },
        ebLogInfo("The Current Space usage in ASM  is :")
        ebLogInfo(str(_dg_sizes_dict))
        ebLogInfo("*** ebCluElasticCellManager:mFetchAndSaveDGSizes <<<")
        return _rc
    #end mFetchAndSaveDGSizes

    def mCalculateDgResize(self, aCludgroupsElement, aDgSizesDict, aDgSizesDictAfterCellupdate):

        ebLogInfo("*** ebCluElasticCellManager:mCalculateDgResize >>>")
        _cludgroups = aCludgroupsElement
        _increment_storage = False
        _size_dict = aDgSizesDict
        _size_dict_afterupdate = aDgSizesDictAfterCellupdate
        _increment_percent=0
        _eBoxCluCtrl = self.mGetEbox()
        _cluDgObj = ebCluManageDiskgroup(_eBoxCluCtrl, _eBoxCluCtrl.mGetArgsOptions())
        _dgConstantsObj = _cluDgObj.mGetConstantsObj()
        ebLogInfo("Diskgroup sizes after cell update is : ")
        ebLogInfo(str(_size_dict_afterupdate))
        ebLogInfo("Diskgroup original sizes before cellupdate is : ")
        ebLogInfo(str(_size_dict))
        _sparse_enabled = False
        _sparse_adjust = False
        _rc = 0
 
        _num_cells = len(list(_eBoxCluCtrl.mReturnCellNodes().keys()))

        # depending on the number of cells, leave free space when shrinking DG's back
        # for 3-4 cells, 15%; for 5+ 9%
        if _num_cells <= 4:
            _max_used_percent = 85
            _check_percent = 85
        else:
            _max_used_percent = 91
            _check_percent = 91

        # check if there is a space issue in any DG calculate the max increment percentage required       
        for _dgid in _cludgroups:
            _dg = _eBoxCluCtrl.mGetStorage().mGetDiskGroupConfig(_dgid)
            _dg_type = _dg.mGetDiskGroupType().lower()
            if _dg_type in [_dgConstantsObj._data_dg_type_str, _dgConstantsObj._reco_dg_type_str, _dgConstantsObj._sparse_dg_type_str]:
                _dg_name = _dg.mGetDgName()
                # We should increment the storage by
                ebLogInfo("Working with diskgroup : " + _dg_name)
                ebLogInfo(json.dumps(_size_dict[_dg_name], indent=4, sort_keys=True)) 
                _temp_totalgb=_size_dict[_dg_name]['totalgb']
                # due to usage of the cell in backgroud during cell update, the used memory might have increased or decreased
                # make use of latest value incase it has increased else use the old one
                if _size_dict[_dg_name]['usedgb'] > _size_dict_afterupdate[_dg_name]['usedgb']:
                    _temp_usedgb=_size_dict[_dg_name]['usedgb']
                else:
                    _temp_usedgb=_size_dict_afterupdate[_dg_name]['usedgb']
                _temp_new_size=(_temp_usedgb * 100 /_max_used_percent)
                if 'SPRC' in _dg_name:
                    _sparse_enabled = True
                    _percent_usage_sparse =(_size_dict[_dg_name]['totalgb'] - _size_dict[_dg_name]['usedgb'])*100/_size_dict[_dg_name]['totalgb']
                    if _percent_usage_sparse > 50:
                        _sparse_adjust = True

                if _temp_usedgb > int(_temp_totalgb*_check_percent/100):
                    _increment_storage = True
                    ebLogInfo(_dg_name + " diskgroup needs more space: original totalgb -> "+str(_temp_totalgb)+" and current usedgb -> "+ str(_temp_usedgb))
              
                    _temp_percent = math.ceil((_temp_new_size - _temp_totalgb)*100/_temp_totalgb)
                    ebLogInfo("Estimated increment percent for "+_dg_name+"  is : "+str(_temp_percent)+" % ")     
                    if _temp_percent > _increment_percent:
                        _increment_percent = _temp_percent
                    ebLogInfo("Calculated increment percent for this cluster is : "+str(_increment_percent)+" % ")
        
        # Calculate the new sizes
        if _increment_storage:
            _abort_shrink = False
            for _dgid in _cludgroups:
                _dg = _eBoxCluCtrl.mGetStorage().mGetDiskGroupConfig(_dgid)
                _dg_type = _dg.mGetDiskGroupType().lower()
                if _dg_type in [_dgConstantsObj._data_dg_type_str, _dgConstantsObj._reco_dg_type_str, _dgConstantsObj._sparse_dg_type_str]:
                    _dg_name = _dg.mGetDgName()
                    # Check if the computed resize value is greater than existing size 
                    # due to usage of the cell in backgroud during cell update, the used memory might have increased or decreased
                    # make use of latest value incase it has increased else use the old one
                    _temp_totalgb=_size_dict[_dg_name]['totalgb']
                    if _size_dict[_dg_name]['usedgb'] > _size_dict_afterupdate[_dg_name]['usedgb']:
                        _temp_usedgb=_size_dict[_dg_name]['usedgb']
                    else:
                        _temp_usedgb=_size_dict_afterupdate[_dg_name]['usedgb']
                    _temp_new_size=(_temp_totalgb * _increment_percent/100)+_temp_totalgb
                    # if calculated new size is greater than _size_dict_afterupdate then no shrink is necessary

                    if int(_temp_new_size) > _size_dict_afterupdate[_dg_name]['totalgb']:
                        ebLogWarn(f"DG {_dg_name} - We detected that we will need to use a bigger size '{_temp_new_size}' "
                            f"than the original expected '{_size_dict_afterupdate[_dg_name]['totalgb']}")

            # Increment the resize values in _size_dict['totalgb']
            for _dgid in _cludgroups:
                _dg = _eBoxCluCtrl.mGetStorage().mGetDiskGroupConfig(_dgid)
                _dg_type = _dg.mGetDiskGroupType().lower()
                if _dg_type in [_dgConstantsObj._data_dg_type_str, _dgConstantsObj._reco_dg_type_str, _dgConstantsObj._sparse_dg_type_str]:
                    _dg_name = _dg.mGetDgName()
                    _temp_totalgb=_size_dict[_dg_name]['totalgb']
                    if _size_dict[_dg_name]['usedgb'] > _size_dict_afterupdate[_dg_name]['usedgb']:
                        _temp_usedgb=_size_dict[_dg_name]['usedgb']
                    else:
                        _temp_usedgb=_size_dict_afterupdate[_dg_name]['usedgb']
                    _temp_new_size=(_temp_totalgb * _increment_percent/100)+_temp_totalgb
                    ebLogInfo(f"Tmp new size {_temp_new_size}")
                    if _abort_shrink:
                        _size_dict.update(_size_dict_afterupdate)
                        ebLogWarn("Aborting resize as the calculated resize is greater than current size")
                        break
                    else:
                        # We should increment the storage to _increment_percent 
                        _temp_new_size = (_temp_new_size*1024)/1024
                        # when multiply and divide by 1024 we round off to gb
                        if _sparse_adjust and ('SPRC' in _dg_name) and (_temp_new_size < (2 * _temp_usedgb)):
                            ebLogInfo("*** setting new size to 2 times the sparse used size")
                            _temp_new_size = 2 * _temp_usedgb
                        _size_dict[_dg_name]['totalgb'] = _temp_new_size
                        ebLogInfo("Diskgroup "+_dg_name+" will incremented to  "+ str(_temp_new_size))
            ebLogInfo("Diskgroup sizes will be resized to ")
            ebLogInfo(str(_size_dict))
        ebLogInfo("*** ebCluElasticCellManager:mCalculateDgResize <<<")
    #end mCalculateDgResize

    def mCheckMinFreeSpaceDGShrink(self, aOptions, aDGTargeSizeMap):
        """
        Helper function that will read DGMap diskgroup
        sizes with target sizes, and will read the current
        ASM real diskgroup usage
        If the TargetTotalSize does not leave 15% (or 9%
        ) FreeSpace considering the current usage, then
        Exacloud will add enough space to TargetSize to
        make sure we leave 15% Free (or 9%)

        Note: 15% is for 3 or 4 cells, while 9% Free is for
        5 or more cells
        """

        _dgmap = aDGTargeSizeMap

        # Target sizes to shrink
        # Convert DG_map to
        _data_dgname = _dgmap[self.DATA][self.DG_NAME] 
        _new_datasize = _dgmap[self.DATA][self.DG_NEWSIZE] 

        _reco_dgname = _dgmap[self.RECO][self.DG_NAME] 
        _new_recosize = _dgmap[self.RECO][self.DG_NEWSIZE]

        _sparse_dgname = None
        _new_sprsize = None
        if _dgmap.get(self.SPARSE):
            ebLogTrace(f"SPARSE is detected")
            _sparse_dgname = _dgmap[self.SPARSE][self.DG_NAME] 
            _new_sprsize = _dgmap[self.SPARSE][self.DG_NEWSIZE] 

        _dg_target_sizes = {
            _data_dgname: {
                "totalgb": _new_datasize,
                "usedgb": 0,
            },
            _reco_dgname: {
                "totalgb": _new_recosize,
                "usedgb": 0,
            }
        }
        if _sparse_dgname:
            _dg_target_sizes[_sparse_dgname] = {
                "totalgb": _new_sprsize,
                "usedgb": 0,
            }

        # Get current real dg sizes
        _cluster = self.mGetEbox().mGetClusters().mGetCluster()
        cludgroups = _cluster.mGetCluDiskGroups()
        _dg_sizes_current_usage = {}

        self.mFetchAndSaveDGSizes(cludgroups, _dg_sizes_current_usage)

        # Compare the real ASM space usage and the target shrink size to satisfy
        # MAA recommendation
        self.mCalculateDgResize(cludgroups, _dg_target_sizes, _dg_sizes_current_usage)
        ebLogInfo(f"The size to use for the resize will be {_dg_target_sizes}")

        _dgmap = {}
        _dgmap[self.DATA] = {}
        _dgmap[self.RECO] = {}
        _dgmap[self.SPARSE] = {}

        # Convert dg_size_dict to _dgmap format
        for _dg_name in list(_dg_target_sizes.keys()):

            if self.DATA in _dg_name:
                _dgmap[self.DATA][self.DG_NAME] = _dg_name
                _dgmap[self.DATA][self.DG_NEWSIZE] = _dg_target_sizes[_dg_name]['totalgb']

            elif self.RECO in _dg_name:
                _dgmap[self.RECO][self.DG_NAME] = _dg_name
                _dgmap[self.RECO][self.DG_NEWSIZE] = _dg_target_sizes[_dg_name]['totalgb']

            # This needs to check SPRC instead of self.SPARSE because the logic is
            # borrowed from cluelasticcells.py which has different naming conventions
            elif ("SPRC" in _dg_name or self.SPARSE in _dg_name):
                _dgmap[self.SPARSE][self.DG_NAME] = _dg_name
                _dgmap[self.SPARSE][self.DG_NEWSIZE] = _dg_target_sizes[_dg_name]['totalgb']

        ebLogTrace(f"DG Map is {_dgmap}")
        return _dgmap

    def mDgUsagePercentage(self, aOptions, aDGObj, aDgName):
        """
        Utility function to check what is current usage percentage of a given dg.
        """
        ebLogInfo("*** mDgUsagePercentage >>>")
        # Get the constants object for use in the scope of this function
        _constantsObj = self.mGetConstantsObj()
        _options = aOptions
        _dgObj = aDGObj
        _dg_name = aDgName
        _dg_usedspaceGB = _dgObj.mUtilGetDiskgroupSize(_options, _dg_name, _constantsObj, "usedMb") / float(1024)
        _dg_totalspaceGB = _dgObj.mUtilGetDiskgroupSize(_options, _dg_name, _constantsObj) / float(1024)
        _percentage_usage = float(_dg_usedspaceGB/_dg_totalspaceGB) *  float(100)
        ebLogInfo("*** mDgUsagePercentage <<< Percentage usage is :%f"%(_percentage_usage))
        return round(_percentage_usage), _dg_totalspaceGB, _dg_usedspaceGB
    
    def mCheckGridDisksResizedCells(self, aDgName, aNewSize, aDgObj):
        """
        Utility function to check if grid disks are resized on cells
        This needs to be checked in case a previous resize operation failed during resize
        such that resize happened at the ASM level but it did not happen on the cells
        Refer Bug 35320487
        """
        _eBox = self.mGetEbox()
        _cell_list = _eBox.mReturnCellNodes()
        _grid_disk_count = 0
        _total_current_size_gb = 0.0
        for _cell in _cell_list:
            with connect_to_host(_cell, get_gcontext()) as _node:
                _cellcli_list_size = "cellcli -e list griddisk attributes size where name like \\'" + aDgName + ".*\\'"
                ebLogInfo("*** Executing the command - %s" % _cellcli_list_size)
                _out = None
                _err = None
                _output = None
                _error = None
                _in, _out, _err = _node.mExecuteCmd(_cellcli_list_size)
                if _out:
                    _output = _out.readlines()
                if _err:
                    _error = _err.read()
                if _output:
                    ebLogTrace("*** cellcli Output - %s" % _output)
                    _slice_size = 0.0
                    _dg_sliceGB = 0.0
                    for _grid_disk in _output:
                        _slice_size_from_cell = _grid_disk.strip()
                        if _slice_size_from_cell.endswith('M'):
                            _slice_size = _slice_size_from_cell[:-1]
                            _dg_sliceGB = (float(_slice_size) / 1024)
                        elif _slice_size_from_cell.endswith('G'):
                            _slice_size = _slice_size_from_cell[:-1]
                            _dg_sliceGB = (float)(_slice_size)
                        elif _slice_size_from_cell.endswith('T'):
                            _slice_size = _slice_size_from_cell[:-1]
                            _dg_sliceGB = (float(_slice_size) * 1024)
                        _total_current_size_gb += _dg_sliceGB
                        _grid_disk_count += 1
                else:
                    ebLogWarn(f"No output returned by the cell {_cell}. Stderr: {_error}.")
                    # Returning True to not process the cells further
                    return True
        # Set the count of grid disks and cells used for further calculation during resize in cludiskgroups
        aDgObj.mSetGridDiskCountRetryResize(_grid_disk_count, aDgName)
        if (abs(float((_total_current_size_gb - aNewSize) / aNewSize)) < 0.01):
            # Resize done at cells - No need for resize operation, only rebalance needed
            ebLogInfo(f"Resize not needed for {aDgName} grid disks on cells. Total current size is: {_total_current_size_gb} and new size is {aNewSize}.")
            return True
        else:
            # Resize needed on cells
            ebLogInfo(f"Resize needed for {aDgName} grid disks on cells. Total current size is: {_total_current_size_gb} and new size is {aNewSize}.")
            aDgObj.mSetCurrentRetrySizeTotalMB(_total_current_size_gb * 1024, aDgName)
            return False

    # mUtilStorageResize -
    # utility function to resize DATA, RECO (and SPARSE) diskgroups
    # using existing capability to resize a diskgroup (mClusterDgrpResize)
    def mUtilStorageResize(self, aDGObj, aOptions, aDGMap, aResizeSpecific):

        _dgMap = aDGMap
        _dgObj = aDGObj
        _dg_data = {}
        _data = {}
        _options = aOptions
        _storage_data = self.mGetStorageOperationData()

        if ((self.REBALANCE_POWER in _options.jsonconf.keys()) and (_options.jsonconf[self.REBALANCE_POWER] is not None)):
            _rebalance_power = _options.jsonconf[self.REBALANCE_POWER]
            ebLogInfo(" input json has rebalance_power value : %d " % (_rebalance_power))
            if _rebalance_power < 4 or _rebalance_power > 64:
                _rebalance_power = 16
        else:
            ebLogInfo("setting a default value of 16 for rebalance_power")
            _rebalance_power = 16

        _data_dgname = _dgMap[self.DATA][self.DG_NAME] 
        _new_datasize = _dgMap[self.DATA][self.DG_NEWSIZE] 

        _reco_dgname = _dgMap[self.RECO][self.DG_NAME] 
        _new_recosize = _dgMap[self.RECO][self.DG_NEWSIZE]

        _sparse_dgname = _dgMap[self.SPARSE][self.DG_NAME] 
        _new_sprsize = _dgMap[self.SPARSE][self.DG_NEWSIZE] 
        
        # populate json to issue resize of DATA diskgroup
        _data['diskgroup'] = _data_dgname 
        _data['new_sizeGB'] = int(_new_datasize)

        _rc = 0
        _options.jsonconf = _data
        if self.__rebalancedata:
            ebLogInfo("mUtilStorageResize: Only Rebalance DATA diskgroup\n")
            _dg_data["Command"] = "dg_rebalance"
            _dgObj.mSetDiskGroupOperationData(_dg_data)
            _options.jsonconf['rebalance_power'] = _rebalance_power
            _rc = _dgObj.mClusterDgrpRebalance(_options)
        elif self.__resizedata:
            ebLogInfo("mUtilStorageResize: Resize DATA diskgroup: %s to %d GB\n" % (_data_dgname, int(_new_datasize)))
            _dg_data["Command"] = "dg_resize"
            _dgObj.mSetDiskGroupOperationData(_dg_data)
            _rc = _dgObj.mClusterDgrpResize(_options)
        _storage_data[_data_dgname] = _dgObj.mGetDiskGroupOperationData()

        if _rc == 0: 
            # populate json to issue resize of RECO diskgroup
            _data['diskgroup'] = _reco_dgname
            _data['new_sizeGB'] = int(_new_recosize)

            _options.jsonconf = _data
            _dg_data = {}

            if self.__rebalancereco:
                ebLogInfo("mUtilStorageResize: Only Rebalance RECO diskgroup\n")
                _dg_data["Command"] = "dg_rebalance"
                _dgObj.mSetDiskGroupOperationData(_dg_data)
                _options.jsonconf['rebalance_power'] = _rebalance_power
                _rc = _dgObj.mClusterDgrpRebalance(_options)
            elif self.__resizereco:
                ebLogInfo("mUtilStorageResize: Resize RECO diskgroup: %s to %d GB\n" % (_reco_dgname, int(_new_recosize)))
                _dg_data["Command"] = "dg_resize"
                _dgObj.mSetDiskGroupOperationData(_dg_data)
                _rc = _dgObj.mClusterDgrpResize(_options)
            _storage_data[_reco_dgname] = _dgObj.mGetDiskGroupOperationData()

        if _rc == 0 and _sparse_dgname is not None and _new_sprsize is not None:
            # populate json to issue resize of SPARSE diskgroup
            _data['diskgroup'] = _sparse_dgname
            _data['new_sizeGB'] = int(_new_sprsize)
            _options.jsonconf = _data
            _dg_data = {}

            if self.__rebalancesprs:
                ebLogInfo("mUtilStorageResize: Only Rebalance SPARSE diskgroup\n")
                _dg_data["Command"] = "dg_rebalance"
                _dgObj.mSetDiskGroupOperationData(_dg_data)
                _options.jsonconf['rebalance_power'] = _rebalance_power
                _rc = _dgObj.mClusterDgrpRebalance(_options)
            elif self.__resizesprs:
                ebLogInfo("mUtilStorageResize: Resize SPARSE diskgroup: %s to %d GB\n" % (_sparse_dgname, int(_new_sprsize)))
                _dg_data["Command"] = "dg_resize"
                _dgObj.mSetDiskGroupOperationData(_dg_data)
                _rc = _dgObj.mClusterDgrpResize(_options)
            _storage_data[_sparse_dgname] = _dgObj.mGetDiskGroupOperationData()
      
        return _rc


    # Method to parse input JSON and validate the arguments
    def mClusterParseInputJson(self, aJson, aReqParams, aOpData=None):

        ebLogInfo("mClusterParseInputJson: Parse the input json to resize the storage.")
        _inputjson = aJson
        _reqparams = aReqParams
        
        if aOpData is None:
            _op_data = self.mGetStorageOperationData()
        else:
            _op_data = aOpData
            
        # Input JSON file is required
        if not _inputjson:
            return self.mRecordError(gDiskgroupError['MissingInputPayload'])

        # Old storage size is a MUST for resize operation.
        if (self.OLDSIZE_GB not in (key.upper() for key in _inputjson.keys()) or\
             not _inputjson[self.OLDSIZE_GB]):
            return self.mRecordError(gDiskgroupError['MissingStorageOldSize'])        
            
        # New storage Size is a MUST for resize operation
        if (self.NEWSIZE_GB not in (key.upper() for key in _inputjson.keys()) or\
             not _inputjson[self.NEWSIZE_GB]):
            return self.mRecordError(gDiskgroupError['MissingStorageNewSize'])        

        _reqparams[self.OLDSIZE_GB] = _inputjson[self.OLDSIZE_GB]
        _reqparams[self.NEWSIZE_GB] = _inputjson[self.NEWSIZE_GB]
        
        ebLogInfo("*** ebCluManageStorage:mClusterParseInputJson <<<")
        return 0
    # end

    def mUpdateRequestData(self, aDataD, aOptions):
        _data_d = aDataD
        _eBox = self.mGetEbox() 
        _reqobj = _eBox.mGetRequestObj()
        if _reqobj is not None:
            _reqobj.mSetData(json.dumps(_data_d, sort_keys = True))
            _db = ebGetDefaultDB()
            _db.mUpdateRequest(_reqobj)
        elif aOptions.jsonmode:
            ebLogJson(json.dumps(_data_d, indent = 4, sort_keys = True))

    # Common method to log error code and error message
    def mRecordError(self, aErrorObject, aString=None):

        _storageData = self.mGetStorageOperationData()

        _storageData["Status"] = "Fail"
        _storageData["ErrorCode"] = aErrorObject[0]
        if aString is None:
            _storageData["Log"] = aErrorObject[1]
        else:
            _storageData["Log"] = aErrorObject[1] + aString

        ebLogError("*** %s\n" % (_storageData["Log"]))
        _errorCode = int(_storageData["ErrorCode"], 16)
        if _errorCode != 0:
            return ebError(_errorCode)
        return 0
    # end

    @staticmethod
    def mEnsureEmptyXenCellsInterconnect(aCellList):
        """
        Method to validate and make sure the the interconnect1 and
        interconnect2 of the cells from aCellList, are properly set as
        ib0/ib1. If not, we will set them and restart the services, with
        the intention of having CELLSRV healthy in the cells

        This flow can be skipped with an exabox.conf flag

        :param aCellList: a list of cells where to make this check
        """

        if get_gcontext().mGetConfigOptions().get(
            "skip_empty_cell_interconnect_check", "false").lower() == "true":
            ebLogInfo(f"Skippig flow to validate Interconnect Interfaces in "
                "Cells")
            return 2


        # Hard link to cellcli bin
        _bin_cellcli = "/opt/oracle/cell/cellsrv/bin/cellcli"

        _map_interfaces = (
                ("interconnect1", "ib0"),
                ("interconnect2", "ib1"))

        _cmd_check_iface = "{0} -e list cell attributes {1}"
        _cmd_set_iface = "{0} -e alter cell {1}={2}"
        _cmd_restart_service = f"{_bin_cellcli} -e alter cell restart services all"


        ebLogInfo("Checking if interconnects are ok in XEN based cells: "
            f"[{aCellList}]")

        for _cell in aCellList:

            with connect_to_host(_cell, get_gcontext()) as _node:

                # Ensure cells user-space is completely booted
                # as this method is most likely run after a reboot
                mWaitForSystemBoot(_node)

                _changed = False
                for _interconnect, _interface in _map_interfaces:

                    # Get interconnect
                    _out = node_exec_cmd_check(_node, _cmd_check_iface.format(
                        _bin_cellcli, _interconnect))
                    _stdout = _out.stdout.strip()

                    # If different, change it
                    if _stdout != _interface:
                        _changed = True
                        ebLogInfo(f"Interconnect {_interconnect} set to "
                            f"{_stdout}, we will attempt to change it to "
                            f"{_interface} for {_cell}")
                        node_exec_cmd_check(_node, _cmd_set_iface.format(
                            _bin_cellcli, _interconnect, _interface))
                    else:
                        ebLogInfo(f"Interconnect {_interconnect} already set to "
                            f"{_interface} for {_cell}")

                # Restart services if needed
                if _changed is True:
                    ebLogInfo(f"A change was detected, restarting services in {_cell}")
                    node_exec_cmd_check(_node, _cmd_restart_service)
        return 0


#
# ebCluQuorumManager manages add/remove quorum disks
#
class ebCluQuorumManager(object):
    
    def __init__(self, aCluCtrlObj):
        self.__cluctrl = aCluCtrlObj

    def checkOutput(self, aOutput, aExpectedOutput, aCompareOutput=True):
        _output = [x.strip() for x in aOutput]
        _success = True
        if(aCompareOutput and aExpectedOutput in str(_output)):
            _success = True
        else: _success = False
        if not _success:
            ebLogInfo("Returning failure because expected output = " + aExpectedOutput + " actual output = " + str(_output))
        return _success

    def runCommand(self, aCmd, aNodeU, aCompareOutput=False, aRequestOutput=False, aRaiseError=True, aExpectedOutput="", aErrorCode=None, aErrorStr=None, aSuccessCmdExitStatus=[0]):
        # aCompareOutput = True: compares the output with aExpectedOutput
        # aRequestOutput = True: returns the output of the command
        # aRaiseError = False: executes the command and does not raise any exception
        # aSuccessCmdExitStatus : List of acceptable command exit codes

        _success = False
        _fin, _fout, _ferr = aNodeU.mExecuteCmd(aCmd)
        _out = _fout.readlines()
        _commandExitStatus = aNodeU.mGetCmdExitStatus()
        if _commandExitStatus not in aSuccessCmdExitStatus:
            ebLogError("Command exited with Status " + str(_commandExitStatus))
            raise ExacloudRuntimeError(aErrorCode, 0xA, aErrorStr, Cluctrl = self.__cluctrl)

        if _out and len(_out):
            _success = True
            if aCompareOutput:
                _success =  self.checkOutput(_out, aExpectedOutput, aCompareOutput)

        if aRaiseError and  not _success and aErrorCode is not None and aErrorStr is not None:
            raise ExacloudRuntimeError(aErrorCode, 0xA, aErrorStr, Cluctrl = self.__cluctrl)
        if aRequestOutput : return _success, _out, _commandExitStatus
        return _success

    def getVotingDisk(self, aDiskList, aErrorCode):
        _DiskList = [x.split() for x in aDiskList]
        _Voting_files = -1
        _Name = -1
        _State = -1
        _Type = -1
        for itr in range(0, len(_DiskList[0])):
            if _Voting_files == -1 and "Voting_files" in _DiskList[0][itr]:
                _Voting_files = itr
            if _Name == -1 and "Name" in _DiskList[0][itr]:
                _Name = itr
            if _State == -1 and "State" in _DiskList[0][itr]:
                _State = itr
            if _Type == -1 and "Type" in _DiskList[0][itr]:
                _Type = itr
        _votingDisk = -1
        # Getting the voting disk
        for itr in range(1, len(_DiskList)):
            if(_votingDisk == -1 and _DiskList[itr][_Voting_files] == 'Y'):
                _votingDisk = _DiskList[itr][_Name][:-1]
                _votingDiskType = _DiskList[itr][_Type]
                break
        if _votingDisk == -1 :
            _error_str = "ebCluQuorumManager: No Voting Disk Exists."
            ebLogError(_error_str)
            raise ExacloudRuntimeError(aErrorCode, 0xA, _error_str, Cluctrl = self.__cluctrl)
        else :
            return _votingDisk, _votingDiskType

    def getDATADisk(self, aDiskList, aErrorCode):
        _DiskList = [x.split() for x in aDiskList]
        _Name = -1
        _State = -1
        _Disk = None
        for itr in range(0, len(aDiskList[0])):
            if _Name == -1 and "Name" in _DiskList[0][itr]:
                _Name = itr
            if _State == -1 and "State" in _DiskList[0][itr]:
                _State = itr
        _foundDisk = False
        # Getting the DATA disk
        for itr in range(1, len(aDiskList)):
            if(not _foundDisk and _DiskList[itr][_Name].startswith("DATA")):
                _Disk = _DiskList[itr][_Name][:-1]
                _foundDisk = True
                break
        if not _foundDisk :
            _error_str = "ebCluQuorumManager: Cannot find a disk with high redudancy."
            ebLogError(_error_str)
            raise ExacloudRuntimeError(aErrorCode, 0xA, _error_str, Cluctrl = self.__cluctrl)
        else :
            return _Disk

    def mCountVotingDisks(self, aNodeU, aErrorCode):
        _nodeU = aNodeU
        _numberOfVoteDisks = 0
        _cmd = " crsctl query css votedisk "
        _expectedOutput = "Located"
        _errorStr = "Error Quorum: Cannot get the number of votedisks."
        _status, _output, _commandExitStatus = self.runCommand(_cmd, _nodeU, False, True, False, _expectedOutput, aErrorCode, _errorStr)
        for itr in range(0,len(_output)):
            if "Located" in _output[itr]:
                _temp = _output[itr]
                _temp = _temp.split()
                for itr2 in range(0,len(_temp)):
                    if _temp[itr2].isnumeric():
                        _numberOfVoteDisks = int(_temp[itr2])
                        return _numberOfVoteDisks
        return _numberOfVoteDisks

    def mRemoveQuorumDisk(self, aDomU, aOptions, aElasticObj):
        ebLogInfo("Deleting quorum disk for " + aDomU)
        _elasticobj = aElasticObj
        _options = aOptions
        _errorCode = 773

        _nodeU = exaBoxNode(get_gcontext(), Cluctrl = self.__cluctrl)
        _nodeUGrid = exaBoxNode(get_gcontext(), Cluctrl = self.__cluctrl) #For Grid user
        _nodeU.mConnect(aHost=aDomU)
        _oracleHome, _ = self.__cluctrl.mGetGridHome(aDomU)
        _cmd = _oracleHome + "/bin/asmcmd lsdg"
        _fin, _fout, _ferr = _nodeU.mExecuteCmd(_cmd)
        _votingDisk, _votingDiskType = self.getVotingDisk(_fout.readlines(), _errorCode)
        _hostName = aDomU.split(".")[0].upper()

        # Getting quorumDisk
        _cmd = "/opt/oracle.SupportTools/quorumdiskmgr --device --list"
        _expectedOutput =  "Host name: " + _hostName
        _errorStr = "Remove quorum disk: Quorum Device does not exist for _DomU " + _hostName
        _status, _output, _commandExitStatus = self.runCommand(_cmd, _nodeU, True, True, True, _expectedOutput, _errorCode, _errorStr)
        for itr in range(0, len(_output)):
            if(_hostName in str(_output[itr])) and ("Host name" in str(_output[itr])):
                itr = itr - 1  # Fetching from previous line
                if(itr >= 0):
                    _quorumDisk = _output[itr].split("/")[-1].strip()
                else:
                    _error_str = "Remove quorum disk: Error in getting the quorum device for _DomU " + _hostName
                    raise ExacloudRuntimeError(_errorCode, 0xA, _error_str, Cluctrl = self.__cluctrl)

        # Deleting Quorum Disk
        ebLogInfo("Deleting Quorum Disk")
        _nodeUGrid.mSetUser('grid')
        _nodeUGrid.mConnect(aHost=aDomU)
        
        _cmd = "echo \"select name from V\$ASM_DISK where name='" + _quorumDisk + "' ;\" | sqlplus -s / as sysasm"
        _expectedOutput =  _quorumDisk
        _errorStr = "Remove Quorum Disk : Could not find quorum Disk " + _quorumDisk
        self.runCommand(_cmd, _nodeUGrid, True, False, True, _expectedOutput, _errorCode, _errorStr)

        _cmd = "echo \"alter diskgroup " + _votingDisk + " drop quorum disk '" + _quorumDisk + "' force;\" | sqlplus -s / as sysasm"
        _expectedOutput =  "Diskgroup altered."
        _errorStr = "Remove Quorum Disk : Could not drop quorum disk " + _votingDisk
        self.runCommand(_cmd, _nodeUGrid, True, False, True, _expectedOutput, _errorCode, _errorStr)
        
        ebLogInfo("Dropped quorum disk " + _votingDisk + " from database.")
        _nodeUGrid.mDisconnect()
        # Wait for Rebalance Operation
        _diskgroupobj = ebCluManageDiskgroup(self.__cluctrl, _options)
        _rc = _diskgroupobj.mEnsureDgsRebalanced(_options, _votingDisk)

        _retryCount = 5
        _waitTime = 30 #in seconds
        _success = False
        while _retryCount > 0 and not _success:
            # Delete Quorum Devices
            _cmd = "/opt/oracle.SupportTools/quorumdiskmgr --delete --device --asm-disk-group " + _votingDisk + " --host-name " + _hostName
            _expectedOutput =  "Successfully deleted device"
            _errorStr = "Remove Quorum Disk : Error deleting Quorum Device"
            _success = self.runCommand(_cmd, _nodeU, True, False, False, _expectedOutput, _errorCode, _errorStr)
            _retryCount = _retryCount - 1
            time.sleep(_waitTime)
        if not _success :
            _error_str = "Remove Quorum Disk : Error deleting Quorum Device"
            raise ExacloudRuntimeError(_errorCode, 0xA, _error_str, Cluctrl = self.__cluctrl)
        ebLogInfo("Deleted quorum device " + _votingDisk)

        _cmd = "/opt/oracle.SupportTools/quorumdiskmgr --delete --target --asm-disk-group " + _votingDisk + " --force"
        _expectedOutput =  "Successfully deleted target"
        _errorStr = "Remove Quorum Disk : Error deleting target"
        self.runCommand(_cmd, _nodeU, True, False, True, _expectedOutput, _errorCode, _errorStr)

        ebLogInfo("Deleted target asm-disk-group")
        _nodeU.mDisconnect()
        ebLogInfo("Quorum disk deleted")

    def mAddQuorumDisk(self, aDomU1, aDomU2, aIPList, aElasticObj):

        ebLogInfo("Adding quorum disk for " + aDomU1 + " and " + aDomU2)
        _errorCode = 776

        _nodeU1Grid = exaBoxNode(get_gcontext(), Cluctrl = self.__cluctrl)
        _nodeU1Grid.mSetUser('grid')
        _nodeU1Grid.mConnect(aHost=aDomU1)

        if self.mCountVotingDisks(_nodeU1Grid, _errorCode)==5:
            _nodeU1Grid.mDisconnect()
            ebLogInfo("Quorum disks already exist.")
            return

        _nodeU1 = exaBoxNode(get_gcontext(), Cluctrl = self.__cluctrl)
        _nodeU1.mConnect(aHost=aDomU1)

        _elasticobj = aElasticObj
        _oracleHome, _ = self.__cluctrl.mGetGridHome(aDomU1)
        _cmd = _oracleHome + "/bin/asmcmd lsdg"
        _fin, _fout, _ferr = _nodeU1.mExecuteCmd(_cmd)
        _out = _fout.readlines()
        _DATADisk = self.getDATADisk(_out,_errorCode)
        _votingDisk, _votingDiskType = self.getVotingDisk(_out, _errorCode)

        _nodeU2 = exaBoxNode(get_gcontext(), Cluctrl = self.__cluctrl)
        _nodeU2.mConnect(aHost=aDomU2)

        _nodeU2Grid = exaBoxNode(get_gcontext(), Cluctrl = self.__cluctrl)
        _nodeU2Grid.mSetUser('grid')
        _nodeU2Grid.mConnect(aHost=aDomU2)

        _retryCount = 3
        _hostName1 = aDomU1.split(".")[0].upper()
        _nodePair1 = {"node" : _nodeU1, "host" : _hostName1}
        _nodeGridPair1 = {"node" : _nodeU1Grid, "host" : _hostName1}
        _hostName2 = aDomU2.split(".")[0].upper()
        _nodePair2 = {"node" : _nodeU2, "host" : _hostName2}
        _nodeGridPair2 = {"node" : _nodeU2Grid, "host" : _hostName2}

        for _nodePairX in [_nodeGridPair1, _nodeGridPair2]:
            _pathToDisk = None
            _cmd = "echo \"select path from GV\$ASM_DISK where path like '%" + _DATADisk + "%" + _nodePairX["host"] +"%' and ROWNUM<=1;\" | sqlplus -s / as sysasm"
            _fin, _fout, _ferr = _nodePairX["node"].mExecuteCmd(_cmd)
            _out = _fout.readlines()
            _out = [x.strip() for x in _out]
            for itr in range(len(_out) - 1, 0, -1):
                if _nodePairX["host"] in _out[itr] :
                    _pathToDisk = _out[itr]
                    break
            if _pathToDisk is None:
                continue
            ebLogInfo("Cleaning up stale entries")
            _quorumDisk = _pathToDisk.split("/")[-1]
            _cmd = "echo \"alter diskgroup " + _DATADisk + " drop quorum disk '" + _quorumDisk + "' force ;\" | sqlplus -s / as sysasm"
            _expectedOutput =  "Diskgroup altered."
            _errorStr = "Error Adding Quorum: Cannot clean stale redudancy entries on host " + _nodePairX["host"]
            self.runCommand(_cmd, _nodePairX["node"], False, False, False, _expectedOutput, _errorCode, _errorStr)

        while(_retryCount>0):
            _retryCount -= 1

            # Deleting quorum devices, targets and configurations
            for _nodeUX in [_nodeU1, _nodeU2]:
                for _hostNameX in [_hostName1, _hostName2]:
                    _cmd = "/opt/oracle.SupportTools/quorumdiskmgr --delete --device --asm-disk-group " + _DATADisk + " --host-name " + _hostNameX
                    _expectedOutput =  "[Success] Successfully deleted"
                    _errorStr = "Could not delete quorum device " + _hostNameX
                    _status, _output, _commandExitStatus = self.runCommand(_cmd, _nodeUX, False, True, True, _expectedOutput, _errorCode, _errorStr)
                    if not ( (_commandExitStatus==0 and _expectedOutput in str(_output)) or (_commandExitStatus==0 and "[Info] There are no devices for the specified ASM disk group name and host name combination to delete." in str(_output)) ):
                        raise ExacloudRuntimeError(_errorCode, 0xA, _errorStr, Cluctrl = self.__cluctrl)

            for _nodePairX in [_nodePair1, _nodePair2]:
                _cmd = "/opt/oracle.SupportTools/quorumdiskmgr --delete --target --asm-disk-group " + _DATADisk + " --force"
                _expectedOutput =  "[Success] Successfully deleted target"
                _errorStr = "Could not delete quorum target at " + _nodePairX["host"]
                self.runCommand(_cmd, _nodePairX["node"], False, False, True, _expectedOutput, _errorCode, _errorStr)

            for _nodePairX in [_nodePair1, _nodePair2]:
                _cmd = "/opt/oracle.SupportTools/quorumdiskmgr --delete --config"
                _expectedOutput =  "[Success] Successfully deleted quorum disk configuration"
                _errorStr = "Could not delete quorum config at " + _nodePairX["host"]
                self.runCommand(_cmd, _nodePairX["node"], False, False, True, _expectedOutput, _errorCode, _errorStr)

            # Create quorum configuration, targets and devices
            for _nodePairX in [_nodePair1, _nodePair2]:
                _cmd = "/opt/oracle.SupportTools/quorumdiskmgr --create --config --owner=grid --group=asmadmin  --network-iface-list=\"stib0, stib1, clib1, clib0\""
                _expectedOutput =  "[Success] Successfully created quorum disk configurations"
                _errorStr = "Could not create quorum config at " + _nodePairX["host"]
                self.runCommand(_cmd, _nodePairX["node"], True, False, True, _expectedOutput, _errorCode, _errorStr)

            # Create Target for Node 1 and Node 2
            for _nodePairX in [_nodePair1, _nodePair2]:
                _cmd = "/opt/oracle.SupportTools/quorumdiskmgr --create --target --asm-disk-group=" + _DATADisk +" --visible-to=\"" + ",".join(aIPList) + "\""
                _expectedOutput =  "[Success] Successfully created target"
                _errorStr = "Could not create quorum target at " + _nodePairX["host"]
                self.runCommand(_cmd, _nodePairX["node"], True, False, True, _expectedOutput, _errorCode, _errorStr)

            # Create Device for Node 1 and Node 2
            for _nodePairX in [_nodePair1, _nodePair2]:
                _cmd = "/opt/oracle.SupportTools/quorumdiskmgr --create --device --target-ip-list=\"" + ",".join(aIPList) + "\""
                _expectedOutput =  "[Success] Successfully created all device(s) from target(s) on machine"
                _errorStr = "Could not create quorum device at " + _nodePairX["host"]
                self.runCommand(_cmd, _nodePairX["node"], True, False, True, _expectedOutput, _errorCode, _errorStr)

            # Checking for success. Both DomUs should have two devices each.
            _numberOfDevicesSuccess = True
            for _nodePairX in [_nodePair1, _nodePair2]:
                _countDevices = 0
                _cmd = "/opt/oracle.SupportTools/quorumdiskmgr --list --device"
                _fin, _fout, _ferr = _nodePairX["node"].mExecuteCmd(_cmd)
                _out = _fout.readlines()
                if _out and len(_out) and _nodePairX["node"].mGetCmdExitStatus()==0:
                    _out = [x.strip() for x in _out]
                    for itr in range(len(_out) - 1, 0, -1):
                        if "Host name" in _out[itr]:
                            _countDevices += 1
                if not _countDevices==2:
                    ebLogInfo("Add Quorum Disk: Could not discover the required number of quorum devices on " + _hostName1 + ".")
                    _numberOfDevicesSuccess = False
                    break
            if _numberOfDevicesSuccess == False:
                continue
            ebLogInfo("Successfully created quorum devices on " + _hostName1 + " and " + _hostName2)
            break

        if _retryCount <= 0:
            raise ExacloudRuntimeError(_errorCode, 0xA, "Failed to create quorum devices on "+ _hostName1 + " and " + _hostName2, Cluctrl = self.__cluctrl)

        #Find Discovery Path
        _cmd = _oracleHome + "/bin/asmcmd dsget"
        _expectedOutput =  "CRS-4266: Voting file(s) successfully replaced"
        _errorStr = "Error Adding Quorum: Cannot replace voting disk"
        _fin, _fout, _ferr = _nodeU1Grid.mExecuteCmd(_cmd)
        _out = _fout.readlines()
        _foundParameter = False
        _ASM_DiskString = ""
        if _out and len(_out) and _nodeU1Grid.mGetCmdExitStatus()==0:
            _out = [x.strip() for x in _out]
            for itr in range(len(_out) - 1, 0, -1):
                _currentOutput = _out[itr].split(":")
                if "RECO" in _currentOutput[-1] or "DATA" in _currentOutput[-1]:
                    _foundParameter = True
                    _ASM_DiskString = _currentOutput[-1]
                    if not "exadata" in _ASM_DiskString:
                        _ASM_DiskString = _ASM_DiskString + ", /dev/exadata_quorum/*"
                    break
        if not _foundParameter:
            raise ExacloudRuntimeError(_errorCode, 0xA, "Could not find the ASM Diskstring", Cluctrl = self.__cluctrl)
        
        _ASM_DiskString = "'" + _ASM_DiskString.replace(",","','") + "'"
        
        # Add Discovery path
        _cmd = "echo \" alter system set asm_diskstring=" + _ASM_DiskString +" ;\" | sqlplus -s / as sysasm"
        _expectedOutput =  "System altered."
        _errorStr = "Error Adding Quorum: Cannot alter diskstring "
        self.runCommand(_cmd, _nodeU1Grid, True, False, True, _expectedOutput, _errorCode, _errorStr)

        # add quorum disk failgroup
        for _nodePairX in [_nodeGridPair1, _nodeGridPair2]:
            _pathToDisk = None
            _cmd = "echo \"select path from GV\$ASM_DISK where path like '%" + _DATADisk + "%" + _nodePairX["host"] +"%' and ROWNUM<=1;\" | sqlplus -s / as sysasm"
            _fin, _fout, _ferr = _nodePairX["node"].mExecuteCmd(_cmd)
            _out = _fout.readlines()
            _out = [x.strip() for x in _out]
            for itr in range(len(_out) - 1, 0, -1):
                if _nodePairX["host"] in _out[itr] :
                    _pathToDisk = _out[itr]
                    break
            if _pathToDisk is None:
                raise ExacloudRuntimeError(_errorCode, 0xA, "Add quorum disk: Cannot fetch the path to disk", Cluctrl = self.__cluctrl)

            _cmd = "echo \"alter diskgroup " + _DATADisk + " add quorum failgroup "+ _nodePairX["host"] + " disk '" + _pathToDisk + "' ;\" | sqlplus -s / as sysasm"
            _expectedOutput =  "Diskgroup altered."
            _errorStr = "Error Adding Quorum: Cannot add quorum failgroup to host " + _nodePairX["host"]
            self.runCommand(_cmd, _nodePairX["node"], True, False, True, _expectedOutput, _errorCode, _errorStr)

        ebLogInfo("Add Quorum: Altered quorum diskgroup")

        #Validate success
        if self.mCountVotingDisks(_nodeU1Grid, _errorCode)==5:
            ebLogInfo("Add Quorum:Quorum disks added successfully.")
        else:
            ebLogInfo("Add Quorum: Could not validate success")

        _nodeU1.mDisconnect()
        _nodeU2.mDisconnect()
        _nodeU1Grid.mDisconnect()
        _nodeU2Grid.mDisconnect()


