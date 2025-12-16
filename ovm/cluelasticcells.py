"""
$Header:

 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    cluelasticstorage - 

FUNCTION:
    Storage module for handling elastic functions

NOTE:
    PLEASE LET'S DOCUMENT WITH DIAGRAMS IN: 
    https://confluence.oraclecorp.com/confluence
      /display/EDCS/Elastic+Cell+-+Diagrams

History:

    MODIFIED   (MM/DD/YY)
    oespinos 11/25/25 - Bug 38688728: Try to read rack_num from actual rack_num 
    pbellary   11/24/25 - Enh 38685113 - EXASCALE: POST CONFIGURE EXASCALE EXACLOUD SHOULD FETCH STRE0/STE1 FROM DOM0
    prsshukl 09/24/25 - Bug 38466258 - ADBS: ADD CELL Phase 1: support multiple
                        cell addition
    prsshukl   09/24/25 - Bug 38466258 - ADBS: ADD CELL Phase 1: support multiple cell addition
    nelango  09/09/25 - Bug 38399834: Update original size dict with
                        post-cellupdate dict instead of reassigning it
    nelango    09/09/25 - Bug 38399834: Update original size dict with
                          post-cellupdate dict instead of reassigning it
    jfsaldan 09/08/25 - Bug 38402930 - EXACS PROD: DBAAS.ADDSTORAGEEXACSINFRA
                        IS FAILING AT WAITFORRESIZEDGS - SEEMS TO BE CAUSED BY
                        THE ENHANCEMENT - 37873380
    jfsaldan   09/08/25 - Bug 38402930 - EXACS PROD: DBAAS.ADDSTORAGEEXACSINFRA
                          IS FAILING AT WAITFORRESIZEDGS - SEEMS TO BE CAUSED BY
                          THE ENHANCEMENT - 37873380
    gparada  08/11/25 - 38253988 Dynamic Storage for data reco sparse - CS flow
    gparada    08/11/25 - 38253988 Dynamic Storage for data reco sparse - CS flow
    jfsaldan   07/17/25 - Bug 38205808 - SPARSE GRIDDISKS DOES NOT HAVE THE
                          CORRECT SIZE AFTER ATTACH STORAGE | REGRESSION 2 FROM
                          RESIZE_DGS SPLIT
    gparada    06/11/25 - 37895129 If DomU is down, try with others. 
    jfsaldan   06/09/25 - Bug 37967738 - CELL REMAINED IN WRITETHROUGH
                          FLASHCACHE MODE AFTER SCALE UP WHICH RESULTED IN
                          PERFORMANCE ISSUES | ECRA DIDN'T CALL EXACLOUD FOR
                          STEP PRECHECKS DURING ADD CELL FOR BOTH CLUSTERS
    rajsag     05/30/25 - Enh 37542341 - support additional response fields in exacloud status response for add compute steps
    jfsaldan   06/05/25 - Bug 38039075 - EXACLOUD ADD CELL WAIT_RESIZE_DGS
                          FAILS | REGRESSION 1 FROM RESIZE_DGS SPLIT
    gparada &  05/08/24 - 37873380 Split RESIZE_DGS and WAIT_RESIZE_DGS
    jfsaldan
    naps       04/25/25 - Bug 37800783 - Skip resize and savesize steps for
                          zdlra.
    dekuckre   10/02/25 - 37571364: Use wait(for rebalance) as False when
                          dropping the griddisks from diskgroup
    aararora   02/05/25 - ER 37541321: Update percentage progress of rebalance
                          operation
    dekuckre   01/24/25 - 37514465: Fix Resize DG step in delete cell flow.
    dekuckre   01/07/25 - 37441359: Resize DG in delete cell flow.
    aararora   01/03/25 - ER 37402747: Add NTP and DNS entries in xml
    prsshukl   12/10/24 - Bug 37308092 - ADBS: Skip mASMRebalancePrecheck for ADBS 
                          env. as dbaastools and dbcs agent rpms are removed in 
                          ADBS env. as part of customisation
    rajsag     12/06/24 - Enh 37363259 - exacs:exascale: update storage vlan in
                          new cell during add cell operation
    gojoseph   11/26/24 - Bug 37289206 - Check if grid home path and sid are
                          empty
    rajsag     11/14/24 - bug 37279005 - exacc:bb:exascale:attach cell failed
                          with error-exacloud : cannot proceed with patching of
                          xml..failed to retrieve clustername from domu
                          iad114582exdvm01clu01.oraclecloud.internal
    jfsaldan   11/04/24 - Enh 37238540 - EXACS EXACLOUD - EXACLOUD SHOULD RESET
    aararora   10/10/24 - ER 36253480: Return ASM rebalance status during
                          rebalance step
    prsshukl   10/04/24 - ER 36981808 - EXACS | ADBS | ELASTIC COMPUTE AND CELL
                          OPERATION ENHANCEMENTS -> IMPLEMENT PHASE 2
    prsshukl   09/26/24 - Bug 37103101 - ADBS: Taking care of the case if
                          get_cs_data.py is not present
    prsshukl   09/20/24 - Bug 37082702 - EXACS: ADBS: ELASTIC STORAGE SUPPORT
                          ISSUES
    rajsag     09/17/24 - 37028667 - exacs exacloud - asm power limit parameter
                          not consumed in add/delete storage flows
    naps       09/10/24 - Bug 37038319 - Check for mandatory arguments in
                          correct way.
    prsshukl   09/05/24 - ER 36553793 - EXACS | ADBS | ELASTIC CELL AND COMPUTE
                          OPERATION ENHANCEMENTS -> IMPLEMENT PHASE 1
    rajsag     09/05/24 - 37029420 - EXASCALE: ADD CELL FOR EXASCALE FAILURE
                          HANDLING AS PART OF 37015865 AND 37022058
    aararora   08/13/24 - ER 36904128: Secure erase API
    prsshukl   07/19/24 - Bug 36860623 - mWhitelistCidr() method needs to be
                          called for Fedramp enabled Exacc env
    rajsag     07/04/24 - Enh 36637281 - exacloud : exascale support for
                          elastic operations on cells
    dekuckre   04/24/24 - 36535455: Acquire locks around mResizeDGs
    rajsag     04/09/24 - enh 36264070 - exacs exacloud - shrink during add
                          storage to auto calculate and use the asm disk size
                          that works
    jfsaldan   04/02/24 - Bug 36472454 - EXACLOUD: PARALLEL ADD CELL PRECHECKS
                          FAIL IF SSH_CONNECTION POOL IS ENABLED AND CELLDISKS
                          ARE MISSING
    rajsag     01/31/24 - 36201584 - elastic storage add: set rebalance power
                          to 1 instead of default 4 if utilisation > 99% for
                          any diskgroup
    dekuckre   01/23/24 - 36193406: Add timeout while getting output of v$asm_operation.
    pbellary   11/03/23 - Bug 35448716 - EXACC:22.3.1:X8:ADD CELL FAILED AFTER RENAMING CLUSTER NAME ON DOMUS
    aypaul     09/01/23 - Bug#35759743 Updating call to process selinux update
                          to postvm_install step.
    dekuckre   07/27/23 - 35645215: Get dbplan from existing cell in add cell flow.
    naps       07/26/23 - Bug 35598840 - Ensure flashcachemode is properly set
                          for zdlra.
    prsshukl   07/12/23 - Bug 35593754 - Create celldisk in precheck step
    aararora   07/06/23 - Bug 35539930: Remove dg id dependency for checking dg
                          type.
    naps       06/01/23 - Bug 35095608 - mvm support for zdlra.
    diguma     04/09/23 - 35199588: Free space when shrinking DG's back
    akkar      04/06/23 - Bug-35254647:Add cell status precheck
    dekuckre   03/24/23 - 35215851: Handle errors during scyncup of cells.
    dekuckre   02/07/23 - 35058452: init dg_size_dict if stepwise disabled.
    dekuckre   01/02/23 - 34922244: bubble up the error recorded.
    akkar      11/10/22 - Bug 34749826: Make call to mSecureCellsSSH as part of
                          elastic flow
    dekuckre   11/10/22 - 34726603: send updated xml in RESIZE_DGS step
    jfsaldan   11/08/22 - Bug 33993510 - CELLDISKS RECREATED AFTER DBSYSTEM
                          TERMINATION
    aypaul     11/03/22 - ENH#34250801 Connectivity check to existing VMs prior
                          to elastic add operations.
    dekuckre   10/06/22 - 34667086: Invoke delete cell stepwise
    dekuckre   10/03/22 - 34627247: Update mEnsureDgRebalanced
    naps       09/20/22 - Bug 34618415 - Check dgid for zdlra.
    dekuckre   09/13/22 - 34556048: Add timeout of 1 day (max 7 days) for rebalance check
    aypaul     08/25/22 - Enh#34472994 A precheck for presentce of celldisks at
                          the start of elastic storage.
    alsepulv   06/15/22 - Bug 34236957: Run hostnames' length precheck before
                          add cell
    dekuckre   04/21/22 - 34093987: Break oedacli clone/delete cell steps to substeps 
    jfsaldan   06/08/22 - Bug 34242884 - Run vlanId change during prevm_setup
                          only in singleVM, and run it on MVM during Delete
                          Infra
    dekuckre   04/21/22 - 34081412: Skip rebalance check for ExaCS singleVM
    dekuckre   04/04/22 - 34022578: Update InMemory config objects
    siyarlag   01/31/22 - 31540575: call mCreateAdbsUser
    jfsaldan   01/28/22 - Bug 33797430 - Reset KVM Vlan Using Diskgroup as
                          condition instead of cluster count
    scoral     12/16/21 - Bug 33677411: Call mRecordError if the Disk groups
                          are not rebalanced at the end of mExecuteResizeDGs.
    dekuckre   11/09/21 - XbranchMerge alsepulv_bug-33513659 from
                          st_ecs_21.4.1.0.0
    rajsag     10/19/21 - Enh 33477686: adding error code handling for the
                          elastic cell in exacloud
    dekuckre   10/25/21 - 33498594: Remove dependency on non root user for
                          elastic flow
    rajsag     09/12/21 - 33333194 - exacc:bb:cpu offline: scaling failed -
                          critical exception caught aborting request [invalid
                          literal for int() with base 10: ] after ecra/cps
                          upgrade
    alsepulv   08/30/21 - Enh 33260899: MVM - Reset vlan id when last VM is
                          deleted
    rajsag     07/20/21 - 33133679 cell add: add a check for kfod to see if
                          griddisks can be listed on the new cell after init
                          clone
    dekuckre   06/28/21 - XbranchMerge dekuckre_bug-33031729_new from
                          st_ecs_20.4.1.2.0
    dekuckre   09/05/21 - 32982101: Add support for ZDLRA systems
    rajsag     06/14/21 - need to update clusters/clustersjson during elastic
                          storage expansion flow
    pverma     06/02/21 - Fetch sparse vSize from cell
    pverma     05/18/21 - Fix for using dictionary element count
    pverma     05/13/21 - Patch XML based on values from cluster before calling
                          OEDACLI
    pverma     04/30/21 - read Workflow_data as JSON
    jfsaldan   04/30/21 - 32805288 - ADB-S EXADATA GRID DISK PROVISIONING -
                          CACHEPOLICY
    pverma     04/29/21 - return usable storageGB
    pverma     04/28/21 - Save physical size for SPARSE in place of virtual
    pverma     03/23/21 - Don't override power for OciExaCC to 0
    pverma     03/10/21 - add string check for str value (was boolean check)
    dekuckre   02/23/21 - 32531434: Send back accumulated storageGB as part
                          of add cell.
    pverma     02/23/21 - set rbal power to 0 for CC env
    jfsaldan   02/05/21 - Bug 31801447: KVM ROCE EXACLOUD NEEDS TO RESET THE
                          STORAGE VLAN AS PART OF DELETE SERVICE
    dekuckre   12/24/20 - 32255834: Convert to workflow based.
    dekuckre   01/25/21 - 32417464: Update mSyncupCells 
    dekuckre   12/15/20 - 32253587: Send patched xml
                          32290095: Add prechecks
    dekuckre   12/09/20 - 32249703: Set iorm obj and dbplan on new cell.
    dekuckre   11/19/20 - 32103689: Update cloud_user password
    dekuckre   10/30/20 - 32076487: Add capability for multi-cell add-delete
    dekuckre   09/25/20 - 31890181: Correct error handling in elastic cell.
    dekuckre   09/08/20 - 31850420: Validate cell was added successfully.
    dekuckre   09/07/20 - 31852479: Call mPostVMCellPatching as part of Add Cell 
    jesandov   08/27/20 - XbranchMerge jesandov_bug-31806249 from
                          st_ecs_20.2.1.0.0rel
    talagusu   08/01/20 - Enh 31699307 - EXACC ELASTIC CELL ADD TO INCREASE
                          RESIZE BY 15%
    dekuckre   07/16/20 - 31627599: Fix 31627599
    gurkasin   06/18/20 - Added mPostReshapeValidation
    dekuckre   05/29/20 - 31404467: Update add and delete cell.
    dekuckre   05/08/20 - 31282887: Include delete cell capability
    dekuckre   05/07/20 - 30858268: Make elastic cell KVM compatible. 
    oespinos   03/05/19 - 29443843 - EXCEPTIONS.KEYERROR 'ACTION'
    pverma     12/13/18 - 29035542 : ELASTIC STORAGE: SUPPORT FOR STORAGE ADDITION FROM EXACLOUD
    

"""
# Ordered python imports
import ast
import copy
import json
import time
import math
from typing import Optional

# Ordered exabox imports
from exabox.core.DBStore import ebGetDefaultDB
from exabox.core.Context import get_gcontext
from exabox.core.Error import ebError, gCellUpdateError, gDiskgroupError, ExacloudRuntimeError, gElasticError, gReshapeError
from exabox.core.Node import exaBoxNode

from exabox.config.Config import ebCluCmdCheckOptions

from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogJson, ebLogDebug, ebLogWarn, ebLogTrace

from exabox.ovm.adbs_elastic_service import (mCreateGriddiskADBS,mDeleteGriddiskADBS,mAssignKeyToCell,
                                             mCheckASMScopeSecurity,mSetAvailableToOnGriddisk,mAppendCellipOraForDomU,
                                             mRemoveCellipOraForDomU,mRemoveKeyFromCell)
from exabox.ovm.cludbaas import ebCluDbaas
from exabox.ovm.cludiskgroups import ebDiskgroupOpConstants, ebCluManageDiskgroup
from exabox.ovm.cluelastic import getGridHome, getDiskGroupNames
from exabox.ovm.clumisc import ebCluPreChecks
from exabox.ovm.cluresmgr import ebCluResManager
from exabox.ovm.csstep.cs_util import csUtil
from exabox.ovm.csstep.exascale.exascaleutils import ebExascaleUtils
from exabox.ovm.utils.clu_utils import ebCluUtils
from exabox.ovm.vmconfig import exaBoxClusterConfig
from exabox.ovm.adbs_elastic_service import (mCreateGriddiskADBS,mDeleteGriddiskADBS,mAssignKeyToCell,
                                             mCheckASMScopeSecurity,mSetAvailableToOnGriddisk,mAppendCellipOraForDomU,
                                             mRemoveCellipOraForDomU,mRemoveKeyFromCell,mGetorCreateDomUObj)

from exabox.tools.oedacli import OedacliCmdMgr

from exabox.utils.node import connect_to_host

SELINUX_UPDATE_SUCCESS = 0
MAX_RETRY = 3
RETRY_WAIT_TIME = 10


class ebCluElasticCellManager(object):

    def __init__(self, aExaBoxCluCtrlObj, aOptions, aSkipConf=False):

        ebLogInfo("*** ebCluElasticCellManager:__init__ <CTOR>")
        
        self.__oedacli_mgr = None
        self.__options = aOptions
        self.__xmlpath = aOptions.configpath
        self.__eboxobj = aExaBoxCluCtrlObj
        self.__dbaasobj = ebCluDbaas(aExaBoxCluCtrlObj, aOptions)
        self._dgConstantsObj = ebDiskgroupOpConstants()
        self.__origVMs = copy.deepcopy([domU for _, domU in self.__eboxobj.mReturnDom0DomUPair()])
        self.__zdlra_noop_steps = ["SAVE_DG_SIZES", "RESIZE_DGS", "WAIT_RESIZE_DGS", "RESIZE_GRIDDISKS"]
        
        self.__update_conf = {}
        
        # Object to store results
        self.__cellOperationData = {}
        
        _oeda_path  = self.__eboxobj.mGetOedaPath()

        _oedacli_bin = _oeda_path + '/oedacli'
        self.__savexmlpath = _oeda_path + '/exacloud.conf/'
        self.__oedacli_mgr = OedacliCmdMgr( _oedacli_bin, self.__savexmlpath )

        if aSkipConf == False:
            # initialize the json to be used for elastic_cell_manage.
            self.initElasticCellConf(aOptions)
        else:
            self.__update_conf['operation'] = 'CELL_INFO'
        
        self.__clu_utils = ebCluUtils(aExaBoxCluCtrlObj)

        ebLogInfo("init completed")    
    
    def mGetCluUtils(self):
        return self.__clu_utils

    def mUpdateNetworkConfig(self, aNetworks):
        _networks = aNetworks

        #private
        _dict = [_dict for _index, _dict in enumerate(_networks) if 'private' in list(_dict.keys())]
        if _dict:
            _dict = _dict[0]
            self.__update_conf['cell']['priv1'] = _dict['private'][0]
            self.__update_conf['cell']['priv2'] = _dict['private'][1]

        #admin
        _dict = [_dict for _index, _dict in enumerate(_networks) if 'admin' in list(_dict.keys())]
        if _dict:
            _dict = _dict[0]
            if _dict['admin']:
                self.__update_conf['cell']['admin'] = _dict['admin'][0]
            else:
                self.__update_conf['cell']['admin'] = ""
        else:
            self.__update_conf['cell']['admin'] = ""

        #ilom
        _dict = [_dict for _index, _dict in enumerate(_networks) if 'ilom' in list(_dict.keys())]
        if _dict:
            _dict = _dict[0]
            self.__update_conf['cell']['ilom'] = _dict['ilom'][0]

        #ntp
        _dict = [_dict for _index, _dict in enumerate(_networks) if 'ntp' in list(_dict.keys())]
        if _dict:
            _dict = _dict[0]
            self.__update_conf['cell']['ntp'] = _dict['ntp']

        #dns
        _dict = [_dict for _index, _dict in enumerate(_networks) if 'dns' in list(_dict.keys())]
        if _dict:
            _dict = _dict[0]
            self.__update_conf['cell']['dns'] = _dict['dns']

    def initElasticCellConf(self, aOptions):
        ebLogInfo("*** ebCluElasticCellManager:initElasticCellConf >>>")
        _ebox = self.mGetEbox()
        _rc  = self.mValidateReshapePayload(aOptions)
        if _rc != 0:
            raise ExacloudRuntimeError(0x07004, 0xA, "Input Error ")

        if 'reshaped_node_subset' in list(aOptions.jsonconf.keys()):
            _reshape_config = aOptions.jsonconf['reshaped_node_subset']
        
            self.__update_conf['cells']=[]
            for _cell in _reshape_config['added_cells']:
                self.__update_conf['operation'] = 'ADD_CELL'
                self.__update_conf['cell'] = {}
                self.__update_conf['cell']['hostname'] = _cell['cell_hostname']
                _networks = _cell['network_info']['cellnetworks']
                self.mUpdateNetworkConfig(_networks)
                if 'rack_num' in _cell['rack_info'].keys():
                    self.__update_conf['cell']['rack_num'] = _cell['rack_info']['rack_num']
                else:
                    self.__update_conf['cell']['rack_num'] = _cell['rack_info']['uheight']
                self.__update_conf['cell']['uloc'] = _cell['rack_info']['uloc']

                self.__update_conf['cells'].append(self.__update_conf['cell'])
                del self.__update_conf['cell']

            if not _ebox.mIsXS(): 
                for _cell in _reshape_config['removed_cells']:

                    self.__update_conf['operation'] = 'DELETE_CELL'
                    self.__update_conf['cell'] = {}
                    self.__update_conf['cell']['hostname'] = _cell['cell_node_hostname']
                    self.__update_conf['cells'].append(self.__update_conf['cell'])
                    del self.__update_conf['cell']

            if self.__update_conf['operation'] == 'ADD_CELL' and not _ebox.mIsXS():
                self.__update_conf['full_compute_to_virtualcompute_list'] = _reshape_config['full_compute_to_virtualcompute_list']

        elif 'rebalance_power' in list(aOptions.jsonconf.keys()):
            self.__update_conf['operation'] = 'UPDATE_RBALPOWER'
            self.__update_conf['rebalance_power'] = int(aOptions.jsonconf['rebalance_power'])
        
        ebLogInfo("self.__update_conf = %s" % self.__update_conf)
        ebLogInfo("*** ebCluElasticCellManager:initElasticCellConf <<<")

    def mGetCellOperationData(self):
        return self.__cellOperationData

    def mSetCellOperationData(self, aCellOperationData):
        self.__cellOperationData = aCellOperationData
        
    def mGetEbox(self):
        return self.__eboxobj
    
    def mGetAoptions(self):
        return self.__options
    
    def mGetUpdateConf(self):
        return self.__update_conf
    
    def mGetDgConstantsObj(self):
        return self._dgConstantsObj
    
    def mGetOedaCliMgr(self):
        return self.__oedacli_mgr
    
    def mGetOedaXmlPath(self):
        return self.__savexmlpath
        
    def mValidateReshapePayload(self, aOptions):
        _eBoxCluCtrl = self.mGetEbox()
        if aOptions is not None and aOptions.jsonconf is not None and 'reshaped_node_subset' in list(aOptions.jsonconf.keys()):
            cellParams = aOptions.jsonconf['reshaped_node_subset']
                
            if ('added_cells' in cellParams and len(cellParams['added_cells']) > 0) and ('removed_cells' in cellParams and len(cellParams['removed_cells']) > 0):
                _detail_error = "Reshape service json payload: Add and Remove cell not allowed in single operation "
                _eBoxCluCtrl.mUpdateErrorObject(gElasticError['INVALID_INPUT_PARAMETER'], _detail_error)
                return self.mRecordError(gCellUpdateError['BadInputCombination'], _detail_error)

            if 'added_cells' in cellParams and len(cellParams['added_cells']) > 0:
                for _cell in cellParams['added_cells']:
                    if not _cell['cell_hostname']:
                        _detail_error = "cell_hostname is mandatory"
                        _eBoxCluCtrl.mUpdateErrorObject(gElasticError['INVALID_INPUT_PARAMETER'], _detail_error)
                        return self.mRecordError(gCellUpdateError['MissingArgs'], "*** " + _detail_error)

                if not _cell['network_info']:
                    _detail_error = "network_info is mandatory"
                    _eBoxCluCtrl.mUpdateErrorObject(gElasticError['INVALID_INPUT_PARAMETER'], _detail_error)
                    return self.mRecordError(gCellUpdateError['MissingArgs'], "*** " + _detail_error)
                
                if len(_cell['network_info']['cellnetworks']) < 3 or not _cell['network_info']['cellnetworks'][0]['admin'] \
                        or not _cell['network_info']['cellnetworks'][1]['private'] or not _cell['network_info']['cellnetworks'][2]['ilom']:
                    ebLogDebug(json.dumps(_cell['network_info'], indent=4, sort_keys=True))
                    ebLogDebug("*** Elements count %s" %(str(len(_cell['network_info']['cellnetworks']))))
                    ebLogDebug(json.dumps(_cell['network_info']['cellnetworks'][0]['admin'], indent=4, sort_keys=True))
                    ebLogDebug(json.dumps(_cell['network_info']['cellnetworks'][1]['private'], indent=4, sort_keys=True))
                    ebLogDebug(json.dumps(_cell['network_info']['cellnetworks'][2]['ilom'], indent=4, sort_keys=True))
                    _detail_error = "'admin', 'private' and 'ilom' entries are mandatory as part of network_info"
                    _eBoxCluCtrl.mUpdateErrorObject(gElasticError['INVALID_INPUT_PARAMETER'], _detail_error)
                    return self.mRecordError(gCellUpdateError['MissingArgs'], "*** " + _detail_error)
                
                if not _cell['network_info']['cellnetworks'][0]['admin'][0]['fqdn'] or not _cell['network_info']['cellnetworks'][0]['admin'][0]['ipaddr']:
                    _detail_error = "Both ip and name expected for admin networks"
                    _eBoxCluCtrl.mUpdateErrorObject(gElasticError['INVALID_INPUT_PARAMETER'], _detail_error)
                    return self.mRecordError(gCellUpdateError['MissingArgs'], "*** " + _detail_error)
                
                if len(_cell['network_info']['cellnetworks'][1]['private']) < 2:
                    _detail_error = "Both ip and name expected for admin networks"
                    _eBoxCluCtrl.mUpdateErrorObject(gElasticError['INVALID_INPUT_PARAMETER'], _detail_error)
                    return self.mRecordError(gCellUpdateError['InsufficientArgs'], "*** " + _detail_error)
                else:
                    for _net in _cell['network_info']['cellnetworks'][1]['private']:
                        if not _net['ipaddr'] or not _net['fqdn']:
                            _detail_error = "Both ip and name expected for private networks"
                            _eBoxCluCtrl.mUpdateErrorObject(gElasticError['INVALID_INPUT_PARAMETER'], _detail_error)
                            return self.mRecordError(gCellUpdateError['MissingArgs'], "*** " + _detail_error)
                
                if not _cell['network_info']['cellnetworks'][2]['ilom'][0]['fqdn'] or not _cell['network_info']['cellnetworks'][2]['ilom'][0]['ipaddr']:
                    _detail_error = "Both ip and name expected for ILOM networks"
                    _eBoxCluCtrl.mUpdateErrorObject(gElasticError['INVALID_INPUT_PARAMETER'], _detail_error)
                    return self.mRecordError(gCellUpdateError['MissingArgs'], "*** " + _detail_error)
                
                if 'rack_info' not in _cell.keys() or 'uloc' not in _cell['rack_info'].keys() or 'uheight' not in _cell['rack_info'].keys():
                    _detail_error = "Missing value(s) for rack_num(uheight)/uloc as part of rack_info"
                    _eBoxCluCtrl.mUpdateErrorObject(gElasticError['INVALID_INPUT_PARAMETER'], _detail_error)
                    return self.mRecordError(gCellUpdateError['MissingArgs'], "*** " + _detail_error)
               
                if not _eBoxCluCtrl.mIsXS() and 'full_compute_to_virtualcompute_list' not in list(cellParams.keys()):
                    _detail_error = "Missing value(s) for full_compute_to_virtualcompute_list"
                    _eBoxCluCtrl.mUpdateErrorObject(gElasticError['INVALID_INPUT_PARAMETER'], _detail_error)
                    return self.mRecordError(gCellUpdateError['MissingArgs'], "*** " + _detail_error)
            
            if 'removed_cells' in cellParams and len(cellParams['removed_cells']) > 0:

                for _cell in cellParams['removed_cells']:
                    if not _cell['cell_node_hostname']:
                        _detail_error = "cell_hostname is mandatory"
                        _eBoxCluCtrl.mUpdateErrorObject(gElasticError['INVALID_INPUT_PARAMETER'], _detail_error)
                        return self.mRecordError(gCellUpdateError['MissingArgs'], "*** " + _detail_error)

        elif aOptions is not None and aOptions.jsonconf is not None and 'rebalance_power' in list(aOptions.jsonconf.keys()):
            if str.isdigit(str(aOptions.jsonconf['rebalance_power'])):
                rebalance_power = int(aOptions.jsonconf['rebalance_power'])
                if rebalance_power < 4 or rebalance_power > 64:
                    _detail_error = "rebalance power can only fall in range (4-64)"
                    _eBoxCluCtrl.mUpdateErrorObject(gElasticError['INVALID_INPUT_PARAMETER'], _detail_error)
                    return self.mRecordError(gCellUpdateError['InvalidInput'], "*** " + _detail_error)
            else:
                _detail_error = "rebalance power can only be an integer in range (4-64)"
                _eBoxCluCtrl.mUpdateErrorObject(gElasticError['INVALID_INPUT_PARAMETER'], _detail_error)
                return self.mRecordError(gCellUpdateError['InvalidInput'], "*** " + _detail_error) 
        else:
            _detail_error = "JSON payload missing for the cell udpate call"
            _eBoxCluCtrl.mUpdateErrorObject(gElasticError['INVALID_INPUT_PARAMETER'], _detail_error)
            return self.mRecordError(gCellUpdateError['MissingArgs'], "*** " + _detail_error)
        
        return 0
    # end mValidateReshapePayload

    #
    # UPDATE SERVICE
    #
    # Supported operations : [ADD_CELL, UPDATE_RBALPOWER, DELETE_CELL]
    #
    # ADD_CELL operation : Add a specific cell to an existing cluster;
    #                      Expectation is to have the cell available and
    #                      reachable over network for the existing Dom-0's.
    #                      It is also expected for the keys to the cell
    #                      available inside the cluster's keys location.
    #
    #                      Sample Payload:
    #                      {  
    #                         "reshaped_node_subset":{  
    #                            "added_cells":[  
    #                               {  
    #                                  "cell_hostname":"scaqae08celadm04.us.oracle.com",
    #                                  "network_info":{  
    #                                     "cellnetworks":[  
    #                                        {  
    #                                           "admin":[  
    #                                              {  
    #                                                 "fqdn":"scaqae08celadm04.us.oracle.com",
    #                                                 "ipaddr":"10.31.17.160"
    #                                              }
    #                                           ]
    #                                        },
    #                                        {  
    #                                           "private":[  
    #                                              {  
    #                                                 "fqdn":"scaqae08cel04-priv1.us.oracle.com",
    #                                                 "ipaddr":"192.168.12.126"
    #                                              },
    #                                              {  
    #                                                 "fqdn":"scaqae08cel04-priv2.us.oracle.com",
    #                                                 "ipaddr":"192.168.12.127"
    #                                              }
    #                                           ]
    #                                        },
    #                                        {  
    #                                           "ilom":[  
    #                                              {  
    #                                                 "fqdn":"scaqae08celadm06-ilom.us.oracle.com",
    #                                                 "ipaddr":"10.31.17.184"
    #                                              }
    #                                           ]
    #                                        }
    #                                     ]
    #                                  },
    #                                  "rack_info":{  
    #                                     "uloc":"8",
    #                                     "uheight":"1"
    #                                  }
    #                               }
    #                            ]
    #                         }
    #                      }
    #
    # DELETE_CELL operation: Delete specified cell.
    #
    #      Payload:
    #
    #        {
    #          "reshaped_node_subset": {
    #            "added_cells": [
    #            ],
    #            "removed_cells": [ {
    #                 "cell_node_hostname": "scaqab10cel09.us.oracle.com"
    #             }
    #            ],
    #            "full_compute_to_virtualcompute_list": [
    #              {
    #                "compute_node_hostname": "scaqab10adm08.us.oracle.com",
    #                "compute_node_virtual_hostname": "scaqab10adm08vm07.us.oracle.com"
    #              },
    #              {
    #                "compute_node_hostname": "scaqab10adm09.us.oracle.com",
    #                "compute_node_virtual_hostname": "scaqab10adm09vm07.us.oracle.com"
    #              }
    #            ]
    #          }
    #        }
    #
    #
    # UPDATE_RBALPOWER operation : Set specified rebalance power for all the ASM diskgroups
    #                              of the cluster
    #
    #                      Sample Payload:
    #                      {
    #                          "rebalance_power" : <Integer (4-64)>
    #                      }
    #
    def mClusterCellUpdate(self, aOptions=None):
        """
        Automata driving Update Service,
        :param: aOptions: Options context
        :return: integer return code
        """
        ebLogInfo("*** ebCluElasticCellManager:mClusterCellUpdate >>>")
        _options = aOptions
        _rc = 0
        _rc_secure_cell_shredding = False
        
        _eBoxCluCtrl = self.mGetEbox()
        
        _cellOperationData = self.mGetCellOperationData()
        _cellOperationData['Status'] = "Pass"
        
        _updateConf = self.mGetUpdateConf()
        _operation = _updateConf['operation']

        if _operation == 'ADD_CELL':
            ebLogInfo("Running DiskGroup LCM Step: Clone Cell")

            _rc = self.mCloneCell(_options)

        if _operation == 'DELETE_CELL':
            ebLogInfo('Deleting cells')
            _rc = self.mDeleteCell(_options)
            try:
                _cell_nodes = []
                for _cellinfo in _updateConf['cells']:
                    _cell_nodes.append(_cellinfo['hostname'])
                _rc_secure_cell_shredding = _eBoxCluCtrl.mCellSecureShredding(_options, aInfraDelete=True, aCellList=_cell_nodes, aCellData=_cellOperationData)
            except Exception as ex:
                ebLogError(f"Secure cell shredding was not successful. Error raised: {ex}. "\
                            "Secure cell shredding API can be used instead.")
                _rc_secure_cell_shredding = False

        if _operation == 'UPDATE_RBALPOWER':
            ebLogInfo("Running DiskGroup LCM Step: Update Rebalance Power for all diskgroups")
            _rc = self.mUpdateRebalancePower(_options)

        # For delete cell, data will be updated as part of secure erase call
        # If the mCellSecureShredding did not return True, the request data would not be updated in mysql
        if _operation != 'DELETE_CELL' or not _rc_secure_cell_shredding :
            self._mUpdateRequestData(_options, _cellOperationData, _eBoxCluCtrl)

        ebLogInfo("*** ebCluElasticCellManager:mClusterCellUpdate <<<")
        return _rc
    # end mClusterCellUpdate

    def mClusterExascaleCellUpdate(self, aOptions=None):
        """
        Automata driving Update Service,
        :param: aOptions: Options context
        :return: integer return code
        """
        ebLogInfo("*** ebCluElasticCellManager:mClusterExascaleCellUpdate >>>")
        _options = aOptions
        _rc = 0
        
        _eBoxCluCtrl = self.mGetEbox()
        
        _cellOperationData = self.mGetCellOperationData()
        _cellOperationData['Status'] = "Pass"
        
        _updateConf = self.mGetUpdateConf()
        _operation = _updateConf['operation']

        #Patch XML with storage Interconnect Ips from compute nodes
        if _eBoxCluCtrl.mIsKVM() and not _eBoxCluCtrl.mIsExaScale():
            _existing_dom0_domu_pairs = _eBoxCluCtrl.mReturnDom0DomUPair()
            _utils = _eBoxCluCtrl.mGetExascaleUtils()
            _utils.mPatchStorageInterconnctIps(aOptions, aDom0DomUList=_existing_dom0_domu_pairs)

        if _operation == 'ADD_CELL':
            ebLogInfo("Running DiskGroup LCM Step: Clone Cell")

            _rc = self.mCloneExascaleCell(_options)

        if _operation == 'DELETE_CELL':
            ebLogInfo('Deleting cells')
            _rc = self.mDeleteExascaleCell(_options)

            
        self._mUpdateRequestData(_options, _cellOperationData, _eBoxCluCtrl)
        ebLogInfo("*** ebCluElasticCellManager:mClusterExascaleCellUpdate <<<")
        return _rc
    # end mClusterExascaleCellUpdate

    def mCloneExascaleCell(self, aOptions):
        ebLogInfo("*** ebCluElasticCellManager:mCloneExascaleCell >>>")
        _options = aOptions
        _eBoxCluCtrl = self.mGetEbox()
        _cluster = _eBoxCluCtrl.mGetClusters().mGetCluster()
        _cellConf = self.mGetUpdateConf()
        _cell_list = list(_eBoxCluCtrl.mReturnCellNodes().keys())
        _cellOperationData = self.mGetCellOperationData()
        _ociexacc = _eBoxCluCtrl.mCheckConfigOption('ociexacc', 'True')
        _stepwise = False
        # Keys need to be pushed to OEDA WorkDir
        if not ebCluCmdCheckOptions(_eBoxCluCtrl.mGetCmd(), ['nooeda']):
            ebLogInfo(f"Restore Keys to OEDA WorkDir")
            _eBoxCluCtrl.mRestoreOEDASSHKeys(aOptions)
        _exascale = ebExascaleUtils(_eBoxCluCtrl)
        _exascale.mRemoveVmMachines(aOptions)
        if _eBoxCluCtrl.mIsExabm():
            _exascale.mUpdateVLanId(aOptions)
        _rc = 0

        _step_list = ["PRE_CHECKS", "CONFIG_CELL", "CREATE_GRIDDISKS", "POST_ADDCELL_CHECK"]

        if aOptions.steplist:
            _step_list = str(aOptions.steplist).split(",")
            _stepwise = True

        if 'undo' not in aOptions:
            _undo = False
        elif str(aOptions.undo).lower() == "true":
            _undo = True
        else:
            _undo = False

        _do = not _undo

        for _step in _step_list:

            if _step == "PRE_CHECKS" and _do:

                _message = "Prechecks before Add Cell"
                ebLogInfo("*** " + _message)
                _eBoxCluCtrl.mUpdateStatusOEDA(True, "PRE_CHECKS", _step_list, _message)

                # Check cell status
                _cells = []
                for _cellinfo in _cellConf['cells']:
                    _cells.append(_cellinfo['hostname'])
                
                self.mElasticAddNtpCellStatus()

                self.mPreAddCellSetup(_cells)

                if not _eBoxCluCtrl.mCheckCellDisks(_cells,'celldisk'):
                    _detail_error = "*** Exacloud Operation Failed : Cell disks do not have normal status."
                    _eBoxCluCtrl.mUpdateErrorObject(gElasticError['CELL_STATUS_NOT_NORMAL'], _detail_error)
                    return self.mRecordError(gCellUpdateError['PrecheckFailed'], "*** " + _detail_error)

            elif _step in [ "CONFIG_CELL", "CREATE_GRIDDISKS"] and _do:

                _message = f"Initiating clone operation sub step {_step} on the cell through OEDACLI"
                ebLogInfo("*** " + _message)
                _eBoxCluCtrl.mUpdateStatusOEDA(True, _step, _step_list, _message)
                _rc = self.mExecuteCellCloneAndSaveXml(_step)
                if _rc:
                    _detail_error = "Cloning operation on the cell failed"
                    _eBoxCluCtrl.mUpdateErrorObject(gElasticError['CELL_CLONING_FAILED'], _detail_error)
                    return self.mRecordError(gCellUpdateError['CellOperationFailed'], "*** " + _detail_error)

                if _step == "CONFIG_CELL":

                    self.mElasticAddNtpCellStatus()

                    # Fix 37967738
                    _cells = []
                    for _cellinfo in _cellConf['cells']:
                        _cells.append(_cellinfo['hostname'])
                    _eBoxCluCtrl.mPostVMCellPatching(aOptions , _cells)
            
            elif _step == "POST_ADDCELL_CHECK" and _do:
                 
                _message = "Post Add Cell Checks."
                ebLogInfo("*** " + _message)
                _eBoxCluCtrl.mUpdateStatusOEDA(True, "POST_ADDCELL_CHECK", _step_list, _message)
                #post validation step to be added

                # Whitelisted the admin network cidr on the Added cell for EXACC fedramp enabled env. for Exascale
                _csu = csUtil()
                if _eBoxCluCtrl.mIsFedramp() and _eBoxCluCtrl.mCheckConfigOption ('whitelist_admin_network_cidr', 'True'):
                    _new_cell_list = []
                    for _cellinfo in _cellConf['cells']:
                        _new_cell_list.append(_cellinfo['hostname'])
                    _remote_lock = _eBoxCluCtrl.mGetRemoteLock()
                    with _remote_lock():
                        for _newcell in _new_cell_list:
                            with connect_to_host(_newcell, get_gcontext()) as _node:
                                _csu.mWhitelistCidr(_eBoxCluCtrl, _node)

            elif _step == "CREATE_GRIDDISKS" and _undo:

                _message = "Initiating delete cell through OEDACLI"
                ebLogInfo("*** " + _message)
                _eBoxCluCtrl.mUpdateStatusOEDA(True, _step, _step_list, _message)
                _rc = self.mDelCell(aOptions, _step)

        ebLogInfo("*** ebCluElasticCellManager:mCloneExascaleCell <<<")
        return _rc
    

    def mDeleteExascaleCell(self, aOptions):
        ebLogInfo("*** ebCluElasticCellManager:mDeleteExascaleCell >>>")
        _ebox = self.mGetEbox()
        _cellConf = self.mGetUpdateConf()
        _cluster = _ebox.mGetClusters().mGetCluster()

        _rc = 0
        _step_list = ["CREATE_GRIDDISKS", "DELETE_CELL_CHECK"]

        if aOptions.steplist:
            _step_list = str(aOptions.steplist).split(",")
            _stepwise = True

        if 'undo' not in aOptions:
            _undo = False
        elif aOptions.undo == "true":
            _undo = True
        else:
            _undo = False

        _do = not _undo

        for _step in _step_list:
            if _step in ["CREATE_GRIDDISKS"] and _do:

                _message = "Initiating delete cell through OEDACLI"
                ebLogInfo("*** " + _message)
                _ebox.mUpdateStatusOEDA(True, _step, _step_list, _message)
                _rc = self.mDelCell(aOptions, _step)

            elif _step == "DELETE_CELL_CHECK" and _do:

                _message = "Post Cell Deletion Checks."
                ebLogInfo("*** " + _message)
                _ebox.mUpdateStatusOEDA(True, "DELETE_CELL_CHECK", _step_list, _message)
                #post validation step to be added

            else:
                ebLogInfo("No-OP: Nothing to be performed as part of this operation.")
            
        ebLogInfo("*** ebCluElasticCellManager:mDeleteExascaleCell <<<")
        return _rc


    def mClusterCellInfo(self, aOptions=None):
        ebLogInfo("*** ebCluElasticCellManager:mClusterCellInfo >>>")
        _options = aOptions
        _rc = 0
        SUPPORTED_PARAMS = ['cell_rbal_status']
        _eBoxCluCtrl = self.mGetEbox()
        
        _cellOperationData = self.mGetCellOperationData()
        _cellOperationData['Status'] = "Pass"
        
        _updateConf = self.mGetUpdateConf()
        _operation = _updateConf['operation']

        if _operation == 'CELL_INFO':
            if _options is not None and _options.jsonconf is not None and 'cell_info_param' in list(aOptions.jsonconf.keys()):
                if _options.jsonconf['cell_info_param'] not in SUPPORTED_PARAMS:
                    _detail_error = f"cell_info_param can only take values from {SUPPORTED_PARAMS}"
                    _eBoxCluCtrl.mUpdateErrorObject(gElasticError['INVALID_INPUT_PARAMETER'], _detail_error)
                    return self.mRecordError(gCellUpdateError['InvalidInput'], "*** " + _detail_error)
                _rc = self.mFetchCellInfo(_options.jsonconf['cell_info_param'])
            else:
                _detail_error = "cell_info command needs cell_info_param"
                _eBoxCluCtrl.mUpdateErrorObject(gElasticError['INVALID_INPUT_PARAMETER'], _detail_error)
                return self.mRecordError(gCellUpdateError['InvalidInput'], "*** " + _detail_error)

        self._mUpdateRequestData(_options, _cellOperationData, _eBoxCluCtrl)
        ebLogInfo("*** ebCluElasticCellManager:mClusterCellInfo <<<")
        return _rc
    # end mClusterCellInfo

    def mCloneCell(self, aOptions):
        ebLogInfo("*** ebCluElasticCellManager:mCloneCell >>>")
        _options = aOptions
        _eBoxCluCtrl = self.mGetEbox()
        _cluster = _eBoxCluCtrl.mGetClusters().mGetCluster()
        cludgroups = _cluster.mGetCluDiskGroups()
        _cellConf = self.mGetUpdateConf()
        _cell_list = list(_eBoxCluCtrl.mReturnCellNodes().keys())
        _cellOperationData = self.mGetCellOperationData()
        _ociexacc = _eBoxCluCtrl.mCheckConfigOption('ociexacc', 'True')
        _stepwise = False
        _power = None

        if 'rebalance_power' in list(_options.jsonconf.keys()):
            _power = int(_options.jsonconf['rebalance_power'])
        _rc = 0

        _step_list = ["PRE_CHECKS", "WAIT_IF_REBALANCING", "SAVE_DG_SIZES", "CONFIG_CELL", "CREATE_GRIDDISKS", "ADD_DISKS_TO_ASM", "WAIT_FOR_REBALANCING", "SYNCUP_CELLS", "RESIZE_DGS", "POST_ADDCELL_CHECK"]
        if _eBoxCluCtrl.mIsAdbs():
            _step_list = ["PRE_CHECKS", "UPDATE_ADBS_VM", "WAIT_IF_REBALANCING", "SAVE_DG_SIZES", "CONFIG_CELL", "CREATE_GRIDDISKS", "ADD_DISKS_TO_ASM", "WAIT_FOR_REBALANCING", "SYNCUP_CELLS", "POST_ADDCELL_CHECK", "REVERT_ADBS_CONFIG"]

            # remove the steps which have hard depenedency on DATA-RECO DGs in zdlra env.

        if not _eBoxCluCtrl.SharedEnv():
            # In single VM env, no need to resize the DGs to originial sizes
            if "RESIZE_DGS" in _step_list:
                _step_list.remove("RESIZE_DGS")
            if "WAIT_RESIZE_DGS" in _step_list:
                _step_list.remove("WAIT_RESIZE_DGS")
            if "RESIZE_GRIDDISKS" in _step_list:   
                _step_list.remove("RESIZE_GRIDDISKS")
            ebLogTrace(f"Step list modified after SVM check {_step_list}")
       
        if aOptions.steplist:
            _step_list = str(aOptions.steplist).split(",")
            _stepwise = True
        if _eBoxCluCtrl.IsZdlraProv():
            for _step in self.__zdlra_noop_steps:
                if _step in _step_list:
                    _step_list.remove(_step)
                    ebLogTrace(f"Removing step {_step} for ZDLRA")

        if 'undo' not in aOptions:
            _undo = False
        elif str(aOptions.undo).lower() == "true":
            _undo = True
        else:
            _undo = False

        _do = not _undo
        dg_size_dict = {}
        _domUDict = {}

        # Patch clusterName in XML before Add Cell
        _domU = self.getConnectableDomU()
        _eBoxCluCtrl.mUpdateClusterName(_domU)

        if "INIT_CLONE_CELL" in _step_list:
            if _do:
                _step_list = ["CONFIG_CELL", "CREATE_GRIDDISKS", "ADD_DISKS_TO_ASM"]
            else:
                _step_list = ["ADD_DISKS_TO_ASM", "CREATE_GRIDDISKS", "CONFIG_CELL"]

        for _step in _step_list:

            if _step == "PRE_CHECKS" and _do:

                _message = "Prechecks before Add Cell"
                ebLogInfo("*** " + _message)
                _eBoxCluCtrl.mUpdateStatusOEDA(True, "PRE_CHECKS", _step_list, _message)
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'ONGOING', "Elastic Cell Pre Check in progress", _step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, _step, "In Progress", _stepSpecificDetails)

                # Check cell status
                _cells = []
                for _cellinfo in _cellConf['cells']:
                    _cells.append(_cellinfo['hostname'])

                self.mElasticAddNtpCellStatus()
                
                self.mPreAddCellSetup(_cells)
                _cluDgObj = ebCluManageDiskgroup(_eBoxCluCtrl, _options)
                _dgConstantsObj = _cluDgObj.mGetConstantsObj()
                if (not _eBoxCluCtrl.mIsAdbs()) and _cluDgObj.mASMRebalancePrecheck(_options, _cells):
                    _detail_error = "*** Exacloud Precheck Operation Failed : Cell disks do not have enough space for the rebalance to complete with given rebalance power value"
                    _eBoxCluCtrl.mUpdateErrorObject(gElasticError['CELL_DG_REBAL_POWER_SET_FAILED'], _detail_error)
                    return self.mRecordError(gCellUpdateError['PrecheckFailed'], "*** " + _detail_error)

                if not _eBoxCluCtrl.mCheckCellDisks(_cells,'celldisk'):
                    _detail_error = "*** Exacloud Operation Failed : Cell disks do not have normal status."
                    _eBoxCluCtrl.mUpdateErrorObject(gElasticError['CELL_STATUS_NOT_NORMAL'], _detail_error)
                    return self.mRecordError(gCellUpdateError['PrecheckFailed'], "*** " + _detail_error)

                # Check hostnames' length
                _pchecks = ebCluPreChecks(_eBoxCluCtrl)
                if _do:
                    _are_existing_vms_connectable = _pchecks.mConnectivityChecks(aHostList=self.__origVMs)
                    if not _are_existing_vms_connectable:
                        _detail_error = "Connectivity checks to existing VMs in the cluster has failed. \
                        Make sure that temporal key for all existing VMs are added and are ssh enabled prior to elastic add operation."
                        _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_VM_NOT_CONNECTABLE'], _detail_error)
                        return self.mRecordError(gCellUpdateError['PrecheckFailed'], "*** " + _detail_error)
                _pchecks.mHostnamesLengthChecks()
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'DONE', "Elastic Cell Pre Check Completed", _step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, _step, "Done", _stepSpecificDetails)


                # Iterate over new cells and check if grid disks
                # are already created in them.
                for _cellinfo in _cellConf['cells']:
                    if _eBoxCluCtrl.mGetStorage().mCheckGridDisks(_cellinfo['hostname']):
                        _detail_error = "Grid disks already created before cloning cell"
                        _eBoxCluCtrl.mUpdateErrorObject(gElasticError['CELL_PRECHECK_FAILED'], _detail_error)
                        return self.mRecordError(gCellUpdateError['PrecheckFailed'], "*** " + _detail_error)

            elif _step == "UPDATE_ADBS_VM" and _do:
                for _, _domU in _eBoxCluCtrl.mReturnDom0DomUPair():
                    _domU_obj = mGetorCreateDomUObj(_domU, _domUDict)
                    _domU_obj.mUpdateGridHomePath()

            elif _step == "WAIT_IF_REBALANCING" and _do:

                _message = "Ensuring all the DGs are rebalanced before proceeding"
                ebLogInfo("*** " + _message)
                _eBoxCluCtrl.mUpdateStatusOEDA(True, "WAIT_IF_REBALANCING", _step_list, _message)
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'ONGOING', "Elastic Cell check and wait if rebalance in progress", _step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, _step, "In Progress", _stepSpecificDetails)
                _rc = self.mEnsureDgRebalanced(aTimeout=1440)
                if _rc:
                    _detail_error = "Fetching rebalance status of diskgroup(s) failed"
                    _eBoxCluCtrl.mUpdateErrorObject(gElasticError['CELL_DG_REBALANCE_INFO_FAILED'], _detail_error)
                    return self.mRecordError(gCellUpdateError['DiskgroupInfoFailed'], "*** " + _detail_error)
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'DONE', "Elastic Cell rebalance check completed", _step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, _step, "Done", _stepSpecificDetails)

            elif _step == "SAVE_DG_SIZES" and _do:

                _message = "Saving current DG sizes for restoration post cell cloning"
                ebLogInfo("*** " + _message)
                _eBoxCluCtrl.mUpdateStatusOEDA(True, "SAVE_DG_SIZES", _step_list, _message)
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'ONGOING', "Saving current DG sizes for restoration post cell cloning in progress", _step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, _step, "In Progress", _stepSpecificDetails)
                _rc = self.mFetchAndSaveDGSizes(cludgroups, dg_size_dict)
                if _rc:
                    _detail_error = "Diskgroup metadata fetch and save failed"
                    _eBoxCluCtrl.mUpdateErrorObject(gElasticError['CELL_DG_METADATA_FETCH_FAILED'], _detail_error)
                    return self.mRecordError(gCellUpdateError['DiskgroupInfoFailed'], "*** " + _detail_error)

                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'DONE', "Saving current DG sizes for restoration post cell cloning completed", _step)

                if _stepwise:
                    dg_size_dict["workflow_step"] = "RESIZE_DGS"
                    _cellOperationData['Workflow_data'] = dg_size_dict
                    self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, _step, "Done", _stepSpecificDetails, _cellOperationData)     

            elif _step in ["CONFIG_CELL", "CREATE_GRIDDISKS", "ADD_DISKS_TO_ASM"] and _do:

                if _stepwise and _step == "CONFIG_CELL" and 'Workflow_data' in aOptions.jsonconf:
                    dg_size_dict = copy.deepcopy(aOptions.jsonconf['Workflow_data'])
                    del dg_size_dict['workflow_step']
                
                if not _eBoxCluCtrl.IsZdlraProv() and _step == "CONFIG_CELL" and not _eBoxCluCtrl.mIsAdbs():
                    self.mPatchXml(dg_size_dict, cludgroups)

                if _step == "CREATE_GRIDDISKS" and _eBoxCluCtrl.mIsAdbs():
                    _message = f"Initiating clone operation sub step {_step} on the cell through CELLCLI"
                    ebLogInfo("*** " + _message)
                    _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'ONGOING', f"Initiating clone operation sub step {_step} on the cell through CELLCLI", _step)
                    self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, _step , "In Progress", _stepSpecificDetails)

                    try:
                        _new_cell_list = []
                        for _cellinfo in _cellConf['cells']:
                            _new_cell_list.append(_cellinfo['hostname'])
                        _remote_lock = _eBoxCluCtrl.mGetRemoteLock()
                        with _remote_lock():
                            for _newcell in _new_cell_list:
                                mCreateGriddiskADBS(_eBoxCluCtrl, _newcell)
                                mAppendCellipOraForDomU(_eBoxCluCtrl, _newcell)
                                if mCheckASMScopeSecurity(_eBoxCluCtrl):
                                    mAssignKeyToCell(_eBoxCluCtrl, _newcell)
                                    mSetAvailableToOnGriddisk(_eBoxCluCtrl, _newcell)
                            _rc = self.validateKfodCmd()
                            if _rc:
                                _detail_error = "kfod utility did not find Griddisks from new cell. Cloning operation failed."
                                _eBoxCluCtrl.mUpdateErrorObject(gElasticError['CELL_CLONING_FAILED'], _detail_error)
                                return self.mRecordError(gCellUpdateError['CellOperationFailed'], "*** " + _detail_error)
                        continue
                    except Exception as e:
                        ebLogError(f"Failure in Create_Griddisk step for Adbs env. Exception: {str(e)}")
                    _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'DONE', f"clone operation sub step {_step} on the cell through CELLCLI completed", _step)
                    self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, _step, "Done", _stepSpecificDetails)

                _message = f"Initiating clone operation sub step {_step} on the cell through OEDACLI"
                ebLogInfo("*** " + _message)
                _eBoxCluCtrl.mUpdateStatusOEDA(True, _step, _step_list, _message)
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'ONGOING', f"Initiating clone operation sub step {_step} on the cell through OEDACLI", _step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, _step , "In Progress", _stepSpecificDetails)
                _rc = self.mExecuteCellCloneAndSaveXml(_step, _power, cludgroups)
                if _rc:
                    _detail_error = "Cloning operation on the cell failed"
                    _eBoxCluCtrl.mUpdateErrorObject(gElasticError['CELL_CLONING_FAILED'], _detail_error)
                    return self.mRecordError(gCellUpdateError['CellOperationFailed'], "*** " + _detail_error)
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'DONE', f"clone operation sub step {_step} on the cell through OEDACLI completed", _step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, _step, "Done", _stepSpecificDetails)

                if _step == "CONFIG_CELL":
                    _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'ONGOING', "Elastic cell config cell in progress", _step)
                    self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, _step , "In Progress", _stepSpecificDetails)
                    self.mElasticAddNtpCellStatus()
                    _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'DONE', "Elastic cell config cell completed", _step)
                    self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, _step , "Done", _stepSpecificDetails)

                    # Fix 37967738
                    _cells = []
                    for _cellinfo in _cellConf['cells']:
                        _cells.append(_cellinfo['hostname'])
                    _eBoxCluCtrl.mPostVMCellPatching(aOptions , _cells)

            elif _step in ["CONFIG_CELL", "CREATE_GRIDDISKS", "ADD_DISKS_TO_ASM"] and _undo:

                if _step == "CREATE_GRIDDISKS" and _eBoxCluCtrl.mIsAdbs():
                    _message = "Initiating delete griddisk through CELLCLI"
                    ebLogInfo("*** " + _message)
                    _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'ONGOING', f"Initiating delete griddisk through CELLCLI", _step)
                    self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, _step , "In Progress", _stepSpecificDetails)
                    _new_cell_list = []
                    for _cellinfo in _cellConf['cells']:
                        _new_cell_list.append(_cellinfo['hostname'])
                    _remote_lock = _eBoxCluCtrl.mGetRemoteLock()
                    with _remote_lock():
                        for _newcell in _new_cell_list:
                            mDeleteGriddiskADBS(_eBoxCluCtrl, _newcell)
                            if mCheckASMScopeSecurity(_eBoxCluCtrl):
                                mRemoveKeyFromCell(_eBoxCluCtrl, _newcell)
                            mRemoveCellipOraForDomU(_eBoxCluCtrl, _newcell)
                    continue
                    _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'ONGOING', f"Initiating delete griddisk through CELLCLI", _step)
                    self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, _step , "Done", _stepSpecificDetails)

                _message = "Initiating delete cell through OEDACLI"
                ebLogInfo("*** " + _message)
                _eBoxCluCtrl.mUpdateStatusOEDA(True, _step, _step_list, _message)
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'ONGOING', f"Initiating Elastic delete cell step {_step} through OEDACLI in progress", _step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, _step , "In Progress", _stepSpecificDetails)
                _rc = self.mDelCell(aOptions, _step)
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'DONE', f"Elastic delete cell step {_step} through OEDACLI completed", _step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, _step , "Done", _stepSpecificDetails)

            elif _step == "WAIT_FOR_REBALANCING" and _do:

                _message = "Ensuring all the DGs are rebalanced"
                ebLogInfo("*** " + _message)
                _eBoxCluCtrl.mUpdateStatusOEDA(True, "WAIT_FOR_REBALANCING", _step_list, _message)
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'ONGOING', "Elastic Cell rebalance in progress", _step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, _step, "In Progress", _stepSpecificDetails)
                _rc = self.mEnsureDgRebalanced()
                if _rc:
                    _detail_error = "Fetching rebalance status of diskgroup(s) failed"
                    _eBoxCluCtrl.mUpdateErrorObject(gElasticError['CELL_DG_REBALANCE_INFO_FAILED'], _detail_error)
                    return self.mRecordError(gCellUpdateError['DiskgroupInfoFailed'], "*** " + _detail_error)
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'DONE', "Elastic Cell rebalance check completed", _step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, _step, "Done", _stepSpecificDetails)
      
            elif _step == "SYNCUP_CELLS" and _do:

                _message = "Ensuring all the cells are synced-up"
                ebLogInfo("*** " + _message)
                _eBoxCluCtrl.mUpdateStatusOEDA(True, "SYNCUP_CELLS", _step_list, _message)
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'ONGOING', "Elastic Cell sync up in progress", _step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, _step, "In Progress", _stepSpecificDetails)

                for _cellinfo in _cellConf['cells']:
                    if _cellinfo['hostname'] in _cell_list:
                        _cell_list.remove(_cellinfo['hostname'])
                self.mSyncupCells(_cell_list)
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'DONE', "Elastic Cell sync up completed", _step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, _step, "Done", _stepSpecificDetails)

            elif _step == "RESIZE_DGS" and _do:

                if not _eBoxCluCtrl.SharedEnv():
                    ebLogInfo(f"Skipping {_step} in SingleVM")
                    continue

                try:
                    _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'ONGOING', "Elastic Cell resize DGs in progress", _step)
                    self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, _step, "In Progress", _stepSpecificDetails)
                    _eBoxCluCtrl.mAcquireRemoteLock()
                    # In RESIZE_DGS step, run only Resize diskgroups
                    # without waiting for rebalance in ExaCS
                    # * mResizeDiskgroups
                    _rc = self.mResizeDGs(aOptions, _step_list, dg_size_dict)

                finally:
                    _eBoxCluCtrl.mReleaseRemoteLock() 
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'DONE', "Elastic Cell resize DGs completed", _step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, _step, "Done", _stepSpecificDetails)

            elif _step == "WAIT_RESIZE_DGS" and _do:

                if not _eBoxCluCtrl.SharedEnv():
                    ebLogInfo(f"Skipping DG size validation in SVM")
                    continue

                # Wait for all rebalance operations
                _message = "Ensuring all the DGs are rebalanced"
                ebLogInfo("*** " + _message)
                _eBoxCluCtrl.mUpdateStatusOEDA(True, "WAIT_RESIZE_DGS", _step_list, _message)
                _rc = self.mEnsureDgRebalanced()
                if _rc:
                    _detail_error = "Fetching rebalance status of diskgroup(s) failed"
                    _eBoxCluCtrl.mUpdateErrorObject(gElasticError['CELL_DG_REBALANCE_INFO_FAILED'], _detail_error)
                    return self.mRecordError(gCellUpdateError['DiskgroupInfoFailed'], "*** " + _detail_error)
      
                # Once all rebalance are done, we must ensure all the diskgroups
                # have the correct size
                # Bug 38402930. Skip Validate Sizes since we dont know if
                # space usage increased during RESIZE_DGS leading to
                # original sizes not being used during shrink
                #_message = "Ensuring all the DGs have correct size post rebalance"
                #ebLogInfo("*** " + _message)
                #_eBoxCluCtrl.mUpdateStatusOEDA(True, "WAIT_RESIZE_DGS", _step_list, _message)
                #_rc = self.mValidateAllDiskGroupsSizes(_step)
                #if _rc:
                #    _detail_error = "Validation of DGs post rebalance failed"
                #    _eBoxCluCtrl.mUpdateErrorObject(gElasticError['CELL_DG_REBALANCE_INFO_FAILED'], _detail_error)
                #    return self.mRecordError(gCellUpdateError['DiskgroupInfoFailed'], "*** " + _detail_error)
                #_message = "Ensuring all the DGs have correct size post rebalance finishe with sucess"
                #ebLogInfo("*** " + _message)

            elif _step == "RESIZE_GRIDDISKS" and _do:

                if not _eBoxCluCtrl.SharedEnv():
                    ebLogInfo(f"Skipping {_step} in SingleVM")
                    continue

                try:
                    _eBoxCluCtrl.mAcquireRemoteLock()

                    # May need this below in the future
                    # If votedisk relocated, run below
                    # self.mRelocateVotedisk(_options,_dg_name)

                    # RUN LOGIC TO RESIZE_GRIDDISKS IF NEEDED
                    _message = "Resizing griddisks"
                    ebLogInfo("*** " + _message)
                    _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'ONGOING', f"Elastic Add Cell {_step} in progress", _step)
                    self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, _step, "In Progress", _stepSpecificDetails)
                    _eBoxCluCtrl.mUpdateStatusOEDA(True, "RESIZE_GRIDDISKS", _step_list, _message)
                    _rc = self.mExecuteResizeGridDisks(dg_size_dict, _step_list)
                    if _rc:
                        _detail_error = "GridDisk resize failed"
                        _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_RESIZE_GRIDDISK'], _detail_error)
                        return self.mRecordError(gCellUpdateError['DiskgroupInfoFailed'], "*** " + _detail_error)
                    _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'DONE', f"Elastic Add Cell step {_step} completed", _step)
                    self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, _step, "DONE", _stepSpecificDetails)

                finally:
                    _eBoxCluCtrl.mReleaseRemoteLock()                     


            elif _step == "POST_ADDCELL_CHECK" and _do:

                # Check if Cell addition was Succesful
                _message = "Post Cell Addition Check."
                ebLogInfo("*** " + _message)
                _eBoxCluCtrl.mUpdateStatusOEDA(True, "POST_ADDCELL_CHECK", _step_list, _message)
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'ONGOING', "Elastic Cell Post Cell Addition Check in progress", _step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, _step, "In Progress", _stepSpecificDetails)

                for _cellinfo in _cellConf['cells']:
                    self.mCellOperationCheck(_cellinfo['hostname'], "ADD_CELL")
                
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'ONGOING', "Elastic Cell Post Cell Addition Check Reshape Validation in progress", _step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 25, _step, "In Progress", _stepSpecificDetails)
                self.mPostReshapeValidation(_options)

                if not _eBoxCluCtrl.IsZdlraProv():
                    # Set CAHINGPOLICY to DEFAULT on ADB-S RECO GridDisk
                    _cells = []
                    for _cellinfo in _cellConf['cells']:
                        _cells.append(_cellinfo['hostname'])

                    # for now not setting the CACHINGPOLICY TO DEFAULT on ADB-S RECO Griddisk as Bug 37542413 for ADD CELL
                    if not _eBoxCluCtrl.mIsAdbs():
                        _eBoxCluCtrl.mSetCachingPolicyRecoGD(_cells, _options)

                    # Save Diskgroup sizes
                    dg_size_dict = {}
                    _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'ONGOING', "Elastic Cell Post Cell Addition Fetch and save DG sizes in progress", _step)
                    self.mGetCluUtils().mUpdateTaskProgressStatus([], 50, _step, "In Progress", _stepSpecificDetails)
                    _rc = self.mFetchAndSaveDGSizes(cludgroups, dg_size_dict)
                    if _rc:
                        _detail_error = "Diskgroup metadata fetch and save failed"
                        _eBoxCluCtrl.mUpdateErrorObject(gElasticError['CELL_DG_METADATA_FETCH_FAILED'], _detail_error)
                        return self.mRecordError(gCellUpdateError['DiskgroupInfoFailed'], "*** " + _detail_error)
                    _sum = 0
                    for k, v in dg_size_dict.items():
                        _sum = _sum + v['totalgb']

                    _cellOperationData['storageGB'] = (_sum / 3) #factor out HIGH REDUNDANCY
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 75, _step, "In Progress", _stepSpecificDetails,_cellOperationData)

                _cell_list = []
                for _cellinfo in _cellConf['cells']:
                    _cell_list.append(_cellinfo['hostname'])

                #Drop pmemlogs for adbs env
                _eBoxCluCtrl.mDropPmemlogs(aOptions, _cell_list)

                # secure host access control
                _new_cells = {}
                for _cellinfo in _cellConf['cells']:
                    # creating dictionary with empty list as mSecureCellsSSH needs keys only
                    _new_cells[_cellinfo['hostname']] = []
                _eBoxCluCtrl.mSecureCellsSSH(_new_cells)

                # Whitelisted the admin network cidr on the Added cell for EXACC fedramp enabled env. for ASM
                _csu = csUtil()
                if _eBoxCluCtrl.mIsFedramp() and _eBoxCluCtrl.mCheckConfigOption ('whitelist_admin_network_cidr', 'True'):
                    _new_cell_list = []
                    for _cellinfo in _cellConf['cells']:
                        _new_cell_list.append(_cellinfo['hostname'])
                    _remote_lock = _eBoxCluCtrl.mGetRemoteLock()
                    with _remote_lock():
                        for _newcell in _new_cell_list:
                            with connect_to_host(_newcell, get_gcontext()) as _node:
                                _csu.mWhitelistCidr(_eBoxCluCtrl, _node)


                _selinux_status = _eBoxCluCtrl.mGetSELinuxMode("cell")
                if _selinux_status:
                    try:
                        _return_code = _eBoxCluCtrl.mProcessSELinuxUpdate(aOptions)
                        if _return_code == SELINUX_UPDATE_SUCCESS:
                            ebLogInfo("SE Linux mode/policy update succeeded for elastic cell update.")
                    except ExacloudRuntimeError as ere:
                        _exception_message = "{0}".format(ere.mGetErrorMsg())
                        ebLogError("SE Linux mode/policy update failed for elastic cell update. Error details: {0}".format(_exception_message))

                ebLogInfo('*** Exacloud Operation Succesful : Add Cell Completed')
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'DONE', "Elastic Cell Post Cell Addition Check completed", _step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, _step, "Done", _stepSpecificDetails)

            elif _step == "REVERT_ADBS_CONFIG" and _do:
                # the updated value of oracle_home remains to make sync with customisation
                ebLogInfo("No-OP: Nothing to be performed as part of this operation for ADBS")

                if _eBoxCluCtrl.mIsAdbs():
                    # Remove access to the domUs for root, grid, opc, oracle
                    _eBoxCluCtrl.mRemoveSshKeys()

            else:
                ebLogInfo("No-OP: Nothing to be performed as part of this operation.")

        ebLogInfo("*** ebCluElasticCellManager:mCloneCell <<<")
        return _rc
    # end mCloneCell
   
    def mDeleteCell(self, aOptions):

        _ebox = self.mGetEbox()
        _cellConf = self.mGetUpdateConf()
        _cell_list = list(_ebox.mReturnCellNodes().keys())
        _cluster = _ebox.mGetClusters().mGetCluster()
        cludgroups = _cluster.mGetCluDiskGroups()
        _cellOperationData = self.mGetCellOperationData()
        dg_size_dict = {}
        _power = None
        if 'rebalance_power' in list(aOptions.jsonconf.keys()):
            _power = int(aOptions.jsonconf['rebalance_power'])

        _rc = 0
        _step_list = ["WAIT_IF_REBALANCING", "SAVE_DG_SIZES", "RESIZE_DGS", "ADD_DISKS_TO_ASM", "WAIT_FOR_REBALANCING", "CREATE_GRIDDISKS", "CONFIG_CELL", "DELETE_CELL_CHECK"]

        if aOptions.steplist:
            _step_list = str(aOptions.steplist).split(",")
            _stepwise = True
        if _ebox.IsZdlraProv():
            for _step in self.__zdlra_noop_steps:
                if _step in _step_list:
                    _step_list.remove(_step)

        if 'undo' not in aOptions:
            _undo = False
        elif aOptions.undo == "true":
            _undo = True
        else:
            _undo = False

        _do = not _undo

        if "INIT_CLONE_CELL" in _step_list and _do: 
            _step_list = ["ADD_DISKS_TO_ASM", "CREATE_GRIDDISKS", "CONFIG_CELL"]                                                                                         

        for _step in _step_list:

            if _step == "WAIT_IF_REBALANCING" and _do:

                _message = "Ensuring all the DGs are rebalanced before proceeding"
                ebLogInfo("*** " + _message)
                _ebox.mUpdateStatusOEDA(True, "WAIT_IF_REBALANCING", _step_list, _message)
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticDeleteDetails", 'ONGOING', "Elastic Cell check for rebalance in progress", _step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, _step, "In Progress", _stepSpecificDetails)
                _rc = self.mEnsureDgRebalanced()
                if _rc:
                    _detail_error = "Fetching rebalance status of diskgroup(s) failed"
                    _ebox.mUpdateErrorObject(gElasticError['CELL_DG_REBALANCE_INFO_FAILED'], _detail_error)
                    return self.mRecordError(gCellUpdateError['DiskgroupInfoFailed'], "*** " + _detail_error)
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticDeleteDetails", 'DONE', "Elastic Cell rebalance check completed", _step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, _step, "Done", _stepSpecificDetails)
                

            elif _step == "SAVE_DG_SIZES" and _do:

                _message = "Saving current DG sizes for restoration."
                ebLogInfo("*** " + _message)
                _ebox.mUpdateStatusOEDA(True, "SAVE_DG_SIZES", _step_list, _message)
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticDeleteDetails", 'ONGOING', "Saving current DG sizes for restoration in progress", _step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, _step, "In Progress", _stepSpecificDetails)
                _rc = self.mFetchAndSaveDGSizes(cludgroups, dg_size_dict)
                if _rc:
                    _detail_error = "Diskgroup metadata fetch and save failed"
                    _ebox.mUpdateErrorObject(gElasticError['CELL_DG_METADATA_FETCH_FAILED'], _detail_error)
                    return self.mRecordError(gCellUpdateError['DiskgroupInfoFailed'], "*** " + _detail_error)
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticDeleteDetails", 'DONE', "Saving current DG sizes for restoration completed", _step)
               

                if _stepwise:
                    dg_size_dict["workflow_step"] = "RESIZE_DGS"
                    _cellOperationData['Workflow_data'] = dg_size_dict
                    self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, _step, "Done", _stepSpecificDetails, _cellOperationData)

            elif _step == "RESIZE_DGS" and _do:

                if not _ebox.SharedEnv():
                    continue

                try:
                    _ebox.mAcquireRemoteLock()
                    _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticDeleteDetails", 'ONGOING', "Resize DGs in progress", _step)
                    self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, _step, "In Progress", _stepSpecificDetails)
                    
                    if aOptions.steplist and "Workflow_data" in aOptions.jsonconf:
                        dg_size_dict = aOptions.jsonconf['Workflow_data']
                        del dg_size_dict['workflow_step']

                    ebLogInfo(f"Old diskgroup size = {dg_size_dict}")

                    _current_cell_count = len(_cell_list) 
                    _post_del_cell_count = _current_cell_count - len(_cellConf['cells'])
                    for k,v in dg_size_dict.items():
                        dg_size_dict[k]["totalgb"] = (dg_size_dict[k]["totalgb"] * _current_cell_count) / _post_del_cell_count

                    ebLogInfo(f"New diskgroup size = {dg_size_dict}")
                    _rc = self.mResizeDGs(aOptions, _step_list, dg_size_dict)

                finally:
                    _ebox.mReleaseRemoteLock() 
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticDeleteDetails", 'DONE', "Resize DGs completed", _step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, _step, "Done", _stepSpecificDetails)

            elif _step in ["ADD_DISKS_TO_ASM", "CREATE_GRIDDISKS", "CONFIG_CELL"] and _do:

                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticDeleteDetails", 'ONGOING', f"Elastic Delete Cell step {_step} in progress", _step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, _step, "In Progress", _stepSpecificDetails) 
                if _step == "CREATE_GRIDDISKS" and _ebox.mIsAdbs():
                    _message = "Initiating delete griddisk through CELLCLI"
                    ebLogInfo("*** " + _message)
                    _new_cell_list = []
                    for _cellinfo in _cellConf['cells']:
                        _new_cell_list.append(_cellinfo['hostname'])
                    _remote_lock = _ebox.mGetRemoteLock()
                    with _remote_lock():
                        for _newcell in _new_cell_list:
                            mDeleteGriddiskADBS(_ebox, _newcell)
                            if mCheckASMScopeSecurity(_ebox):
                                mRemoveKeyFromCell(_ebox, _newcell)
                            mRemoveCellipOraForDomU(_ebox, _newcell)
                    continue

                _message = "Initiating delete cell through OEDACLI"
                ebLogInfo("*** " + _message)
                _ebox.mUpdateStatusOEDA(True, _step, _step_list, _message)
                _rc = self.mDelCell(aOptions, _step)
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticDeleteDetails", 'DONE', f"Elastic Delete cell step {_step} completed", _step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, _step, "DONE", _stepSpecificDetails)
           
            elif _step in ["ADD_DISKS_TO_ASM", "CREATE_GRIDDISKS", "CONFIG_CELL"] and _undo:

                _message = f"Initiating clone operation sub step {_step} on the cell through OEDACLI"
                ebLogInfo("*** " + _message)
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticDeleteDetails", 'ONGOING', f"Elastic Delete Cell step {_step} in progress", _step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, _step, "In Progress", _stepSpecificDetails) 
                _ebox.mUpdateStatusOEDA(True, _step, _step_list, _message)
                _rc = self.mExecuteCellCloneAndSaveXml(_step, _power)
                if _rc:
                    _detail_error = "Cloning operation on the cell failed"
                    _ebox.mUpdateErrorObject(gElasticError['CELL_CLONING_FAILED'], _detail_error)
                    return self.mRecordError(gCellUpdateError['CellOperationFailed'], "*** " + _detail_error)
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticDeleteDetails", 'DONE', f"Elastic Delete cell step {_step} completed", _step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, _step, "DONE", _stepSpecificDetails)

            elif _step == "WAIT_FOR_REBALANCING" and _do:

                _message = "Ensuring all the DGs are rebalanced"
                ebLogInfo("*** " + _message)
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticDeleteDetails", 'ONGOING', f"Elastic Delete Cell step {_step} in progress", _step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, _step, "In Progress", _stepSpecificDetails)
                _ebox.mUpdateStatusOEDA(True, "WAIT_FOR_REBALANCING", _step_list, _message)
                _rc = self.mEnsureDgRebalanced()
                if _rc:
                    _detail_error = "Fetching rebalance status of diskgroup(s) failed"
                    _ebox.mUpdateErrorObject(gElasticError['CELL_DG_REBALANCE_INFO_FAILED'], _detail_error)
                    return self.mRecordError(gCellUpdateError['DiskgroupInfoFailed'], "*** " + _detail_error)
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticDeleteDetails", 'DONE', f"Elastic Delete cell step {_step} completed", _step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, _step, "DONE", _stepSpecificDetails)


            elif _step == "DELETE_CELL_CHECK" and _do:

                _message = "Post Cell Deletion Checks."
                ebLogInfo("*** " + _message)
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticDeleteDetails", 'ONGOING', f"Elastic Delete Cell step {_step} in progress", _step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, _step, "In Progress", _stepSpecificDetails)
                _ebox.mUpdateStatusOEDA(True, "DELETE_CELL_CHECK", _step_list, _message)
                _celllist = []
                for _cellinfo in _cellConf['cells']:
                    self.mCellOperationCheck(_cellinfo['hostname'], 'DELETE_CELL')

                self.mPostReshapeValidation(aOptions)
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticDeleteDetails", 'DONE', f"Elastic Delete cell step {_step} completed", _step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, _step, "DONE", _stepSpecificDetails)

            else:
                ebLogInfo("No-OP: Nothing to be performed as part of this operation.")

        ebLogInfo("*** ebCluElasticCellManager:mDeleteCell <<<")
        return _rc

    def mResizeDGs(self, aOptions, aStepList, aDGSizeDict=None):
        # PLEASE FIND DIAGRAM IN: 
        # https://confluence.oraclecorp.com/confluence
        #   /display/EDCS/Elastic+Cell+-+Diagrams

        _options = aOptions
        _step_list = aStepList 
        _eBoxCluCtrl = self.mGetEbox()
        _cluster = _eBoxCluCtrl.mGetClusters().mGetCluster()
        cludgroups = _cluster.mGetCluDiskGroups()

        # This step is to ensure 15% freespace to avoid issues during shrink
        if _options.steplist and "Workflow_data" in aOptions.jsonconf and not aDGSizeDict:
            dg_size_dict = aOptions.jsonconf['Workflow_data']
            del dg_size_dict['workflow_step']
        else:
            dg_size_dict = aDGSizeDict
        
        dg_size_dict_after_update_cell = {}
        _message = "Calculating the resize values for diskgroup(s)"
        ebLogInfo("*** " + _message)
        _eBoxCluCtrl.mUpdateStatusOEDA(True, "RESIZE_DGS", _step_list, _message)
        _rc = self.mFetchAndSaveDGSizes(cludgroups, dg_size_dict_after_update_cell)

        self.mCalculateDgResize(cludgroups, dg_size_dict, dg_size_dict_after_update_cell)
        if _rc:
            _detail_error = "Calculating the resize values for diskgroup(s) failed"
            _eBoxCluCtrl.mUpdateErrorObject(gElasticError['CELL_DG_RESIZE_CALC_FAILED'], _detail_error)
            return self.mRecordError(gCellUpdateError['OperationFailed'], "*** " + _detail_error)

        _message = "Resize diskgroups back to original size(s)"
        ebLogInfo("*** " + _message)
        _rc = self.mExecuteResizeDGs(dg_size_dict)
        if _rc:
            _detail_error = "Resize of diskgroup(s) failed"
            _eBoxCluCtrl.mUpdateErrorObject(gElasticError['CELL_DG_RESIZE_CALC_FAILED'], _detail_error)
            return self.mRecordError(gCellUpdateError['OperationFailed'], "*** " + _detail_error)

        if not _eBoxCluCtrl.mIsOciEXACC():
            ebLogInfo("*** Wait for Rebalance is NO longer part of RESIZE_DG, " \
                  "waiting should be run as its own single (next) step in WF in ExaCS.")

        if _options.steplist:
            if 'workflow_step' in dg_size_dict:
                del dg_size_dict['workflow_step'] 
       
            if not _eBoxCluCtrl.IsZdlraProv():
                #We dont (re)-patch xml for zdlra here.
                #This usecase is specific to exacs.        
                _total_dg_size = 0
                _sparse_enabled = False
                for _dgname, _size in dg_size_dict.items():
                    _total_dg_size = _total_dg_size + int(_size['totalgb'])
                    if 'DATA' in _dgname:
                        _data_size = int(_size['totalgb'])
                    if 'RECO' in _dgname:
                        _reco_size = int(_size['totalgb'])
                    if 'SPRC' in _dgname:
                        _sparse_enabled = True

                if _data_size > _reco_size:                     
                   _backup_disk = False                          
                else:        
                   _backup_disk = True                                   

                _eBoxCluCtrl.mGetStorage().mPatchClusterDiskgroup(
                    aCreateSparse = _sparse_enabled, 
                    aBackupDisk = _backup_disk, 
                    aDRSdistrib = None, 
                    aOptions = self.mGetAoptions(), 
                    aTotalDGSize = int(_total_dg_size/3))

        _eBoxCluCtrl.mUpdateInMemoryXmlConfig(_eBoxCluCtrl.mGetPatchConfig(), self.mGetAoptions())
        ebLogInfo('ebCluCtrl: Saved patched Cluster Config: ' + _eBoxCluCtrl.mGetPatchConfig())
        _db = ebGetDefaultDB()
        _db.import_file(_eBoxCluCtrl.mGetPatchConfig())

    def mSyncupCells(self, aOrigCells):

        _ioptions = self.mGetAoptions()
        _eBoxCluCtrl = self.mGetEbox()
        _cellConf = self.mGetUpdateConf()
        _cells = []
        for _cellinfo in _cellConf['cells']:
            _cells.append(_cellinfo['hostname'])

        # Update cloud_user password (in the new cells) obtained from store in domUs
        _domU = self.getConnectableDomU()
        try:
            with connect_to_host(_domU, get_gcontext()) as _node:
                _, _o, _ = _node.mExecuteCmd('/opt/exacloud/get_cs_data.py --dataonly')
                _passwd = _o.read().strip()
                if _passwd:
                    if _eBoxCluCtrl.mIsAdbs() is False:  
                        _eBoxCluCtrl.mUpdateCloudUser(self.mGetAoptions(), _cells, _passwd)
                    _eBoxCluCtrl.mCreateAdbsUser(self.mGetAoptions(), _cells, _passwd)
                    _eBoxCluCtrl.mEnableRemotePwdChange(self.mGetAoptions(), _cells)
        except Exception as e:
            if _eBoxCluCtrl.mIsAdbs():
                ebLogWarn(f"Failure in Creating Adbs user with exception {str(e)}")
            else:
                raise ExacloudRuntimeError(aErrorMsg=f"Exception during Creation of Cloud user with ex:{str(e)}")

        _iormobj = ebCluResManager(_eBoxCluCtrl, _ioptions)
        _iormobj.mSetCells([aOrigCells[0]])

        # Get current objective value set in existing cells
        _ioptions.resmanage = "getobj"
        _iormobj.mClusterIorm(_ioptions)
        _jsonobj = _iormobj.mGetData()
        if _jsonobj["Status"] != "Pass":
            ebLogError("Failed to get Objective from the cells.")
            raise ExacloudRuntimeError(0x0802, 0xA, "Add Cell Operation Failed")

        # Get current dbplan value set in existing cells
        _ioptions.resmanage = "getdbplan"
        _iormobj.mSetData({})
        _iormobj.mClusterIorm(_ioptions)
        _jsondbplan = _iormobj.mGetData()
        if _jsondbplan["Status"] != "Pass":
            ebLogError("Failed to get DB Plan from the cells.")
            raise ExacloudRuntimeError(0x0802, 0xA, "Add Cell Operation Failed")

        _iormobj.mSetCells(_cells)

        # Set objective (_jsonobj) in the new cells
        _ioptions.resmanage = "setobj"
        if _eBoxCluCtrl.mIsExabm():
            _key = "objective"
        else:
            _key = "Objective"
        _ioptions.jsonconf['objective'] = _jsonobj[_key]
        _iormobj.mSetData({})
        if _jsonobj["Status"] == "Pass" and  _jsonobj[_key] != "None":
            _iormobj.mClusterIorm(_ioptions)

        # Set dbplan (_jsondbplan) in the new cells
        _ioptions.resmanage = "setdbplan"
        if _eBoxCluCtrl.mIsExabm():
            _key = "dbPlan"
        else:
            _key = "DbPlan"

        if _key not in _jsondbplan or not _jsondbplan[_key] or _jsondbplan[_key][0] == "None":
            ebLogInfo("No DB plan set on the cells")
            return

        if not _eBoxCluCtrl.mIsExabm():

            for _entry in _jsondbplan[_key]:
                _entry['dbname'] = _entry.pop('name')
        
        _ioptions.jsonconf[_key] = _jsondbplan[_key]
        _iormobj.mSetData({})
        _iormobj.mClusterIorm(_ioptions)

    def mDelCell(self, aOptions, aStep=None):

        _ebox = self.mGetEbox()
        _oedaCliMgr = self.mGetOedaCliMgr()
        _cellConf = self.mGetUpdateConf()
        _cellParams = aOptions.jsonconf['reshaped_node_subset']
        _power = None
        if 'rebalance_power' in list(aOptions.jsonconf.keys()):
            _power = int(aOptions.jsonconf['rebalance_power'])
        else:
            _power = _ebox.mCheckConfigOption('rebal_power')
        _uuid = _ebox.mGetUUID()
        _oedaXmlPath = self.mGetOedaXmlPath() + "/" + "delCell_" + _uuid + ".xml"
        
        _step = aStep

        try:
            _ebox.mAcquireRemoteLock()
            _configxml = _ebox.mGetOedaPath() + '/exacloud.conf/elastic_cell_' + _uuid + '.xml'
            _ebox.mExecuteLocal("/bin/cp {} {}".format(_ebox.mGetPatchConfig(), _configxml))            
            _ebox.mExecuteLocal("/bin/cp {} {}".format(_ebox.mGetPatchConfig(), _oedaXmlPath))
            _config = exaBoxClusterConfig(_ebox.mGetCtx(), _configxml)
            _ebox.mSetConfig(_config)

            ebLogDebug("*** Using source XML : %s and savexml : %s" %(_configxml, _oedaXmlPath))

            _celllist = []
            for _cellinfo in _cellConf['cells']:
                _celllist.append(_cellinfo['hostname'])

            _oedaCliMgr.mDropCell(_configxml, _oedaXmlPath, _celllist, True, _power, _ebox.mIsKVM(), _ebox.mGetClusters().mGetCluster().mGetCluName(), False, 'false', _step)

        except ExacloudRuntimeError as e:
            ebLogDebug("*** Exception Stack Trace: %s" %(str(e)))
            _detail_error = "Could not delete cell through Oedacli"
            _ebox.mUpdateErrorObject(gElasticError['CELL_OEDA_DEL_CMD_FAILED'], _detail_error)
            return self.mRecordError(gCellUpdateError['OedaError'], "*** " + _detail_error)

        finally:
            _ebox.mReleaseRemoteLock() 

        if _ebox.mIsKVM() and _ebox.mIsExabm() and not _ebox.mIsXS() and _step == "CONFIG_CELL":

            # ER 37238540: Restore Storage VlanId if payload includes
            # 'keepcellreserved' as false
            _keep_reserved = aOptions.jsonconf.get("keepcellreserved", "true")
            ebLogTrace(f"Keep Cell Reserved in payload is {_keep_reserved}")
            if not _ebox.SharedEnv() or str(_keep_reserved).lower() == "false":

                _all_cells_empty = True
                for _cell in _celllist:
                    ebLogInfo(f"Fetching GridDisks info from: {_cell}")
                    with connect_to_host(_cell, get_gcontext()) as _node:

                        # If any GridDisks is still there we skip the
                        # vlanID restore
                        _gd_list = _ebox.mGetStorage().mListCellDG(_node)
                        if _gd_list:
                            ebLogInfo(f"Found GridDisks in cell {_cell}, so "
                                "we'll skip the RoCE VlanID restore. List:\n{_gd_list}")
                            _all_cells_empty = False
                if _all_cells_empty:
                    _ebox.mRestoreStorageVlan(_celllist)

                    _ebox.mGetStorage().mDropCellDisks(_celllist)

        _config = exaBoxClusterConfig(_ebox.mGetCtx(), _oedaXmlPath)
        _ebox.mSetConfig(_config)

        _ebox.mSaveXMLClusterConfiguration()
        ebLogInfo('ebCluCtrl: Saved patched Cluster Config: ' + _ebox.mGetPatchConfig())
        _ebox.mDeleteClusterDomUList()
        _ebox.mSaveClusterDomUList()
        _db = ebGetDefaultDB()
        _db.import_file(_ebox.mGetPatchConfig())

    def mUpdateRebalancePower(self, aOptions):
        ebLogInfo("*** ebCluElasticCellManager:mUpdateRebalancePower >>>")
        _options = aOptions
        _eBoxCluCtrl = self.mGetEbox()
        _cluster = _eBoxCluCtrl.mGetClusters().mGetCluster()
        _cludgroups = _cluster.mGetCluDiskGroups()
        _dgConstantsObj = ebDiskgroupOpConstants()
        _cluDgObj = ebCluManageDiskgroup(_eBoxCluCtrl, _options)
        _rc = 0
        _step_list = ["SAVE_DG_NAMES", "SET_RBAL_POWER"]
        _step = 0
        dg_list = []
        
        _message = "Fetching DG Names for applying new rebalance power"
        ebLogInfo("*** " + _message)
        _eBoxCluCtrl.mUpdateStatusOEDA(True, _step_list[_step], _step_list, _message)
        for _dgid in _cludgroups:
            _dg = _eBoxCluCtrl.mGetStorage().mGetDiskGroupConfig(_dgid)
            _dg_type = _dg.mGetDiskGroupType().lower()
            if _dg_type in [_dgConstantsObj._data_dg_type_str, _dgConstantsObj._reco_dg_type_str, _dgConstantsObj._sparse_dg_type_str]:
                _dg_name = _dg.mGetDgName()
                dg_list.append(_dg_name)
        
        _step += 1
        _message = "Applying new rebalance power to all the diskgroups"
        ebLogInfo("*** " + _message)
        _eBoxCluCtrl.mUpdateStatusOEDA(True, _step_list[_step], _step_list, _message)
        _rc = _cluDgObj.mExecuteSetDGsRebalancePower(dg_list, _options.jsonconf['rebalance_power'])
        if _rc:
            _detail_error = "Applying new rebalance power to all the diskgroups failed"
            _eBoxCluCtrl.mUpdateErrorObject(gElasticError['CELL_DG_REBAL_POWER_SET_FAILED'], _detail_error)
            ebLogError("*** " + _detail_error)
            return _rc
        
        ebLogInfo("*** ebCluElasticCellManager:mUpdateRebalancePower <<<")
    # end mUpdateRebalancePower

    def mElasticAddNtpCellStatus(self):
        """
        1) Add the ntp/dns/chrony values if not present
        2) restart chronyd
        3) check cellsrv are up, if not, check MAX_RETRY(3) times, then go ahead
        """

        _cellConf = self.mGetUpdateConf()
        _eBoxCluCtrl = self.mGetEbox()
        _pchecks = ebCluPreChecks(_eBoxCluCtrl)
        _cells = []
        for _cellinfo in _cellConf['cells']:
            _cells.append(_cellinfo['hostname'])
        if _eBoxCluCtrl.mIsKVM():
            _pchecks.mAddMissingNtpDnsIps(_cells)

        _remote_lock = _eBoxCluCtrl.mGetRemoteLock()
        with _remote_lock():
            if _eBoxCluCtrl.mIsKVM() and self.mCheckCellsServicesStatus(_cells):
                ebLogInfo(f"The cell services are up on all the new cells to be added")
            else:
                ebLogWarn(f"The cell service are down in one of newly added cells")


    def mCheckCellsServicesStatus(self, aCells=[]):
        """
        Bug 37316970 - Checking if cell services are up after time sync through chrony restart
        """
        _eBoxCluCtrl = self.mGetEbox()
        _cell_list = aCells
        _retry_count = 1
        while _retry_count <= MAX_RETRY:
            if _eBoxCluCtrl.mCheckCellsServicesUp(aRestart=False, aCellList=_cell_list):
                return True
            else:
                _retry_count += 1
                time.sleep(RETRY_WAIT_TIME)
        return False

    # Create celldisks if not already present.
    def mPreAddCellSetup(self, aCells):

        _cell_list = aCells

        for _cell in _cell_list:

            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_cell)
            _, _o, _ = _node.mExecuteCmd('cellcli -e list celldisk attributes name,size where disktype=HardDisk')
            _out = _o.readlines()
            ebLogTrace("*** The value of _out is %s" % _out)
            if not _out:
                _node.mExecuteCmd('cellcli -e drop celldisk all')
                _node.mExecuteCmd('cellcli -e create celldisk all')

            _node.mDisconnect()

    def mFetchAndSaveDGSizes(self, aCludgroupsElement, aDgSizesDict):
        
        ebLogInfo("*** ebCluElasticCellManager:mFetchAndSaveDGSizes >>>")
        
        _cludgroups = aCludgroupsElement
        _dg_sizes_dict = aDgSizesDict
        _eBoxCluCtrl = self.mGetEbox()
        _cluDgObj = ebCluManageDiskgroup(_eBoxCluCtrl, self.mGetAoptions())
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
                _rc = _cluDgObj.mUtilGetDiskgroupSize(self.mGetAoptions(), _dg_name, _dgConstantsObj)
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
    
                _rc = _cluDgObj.mUtilGetDiskgroupSize(self.mGetAoptions(), _dg_name, _dgConstantsObj, True)
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
    
    def mPatchXml(self, aDgSizesDict, aCludgroupsElement):
        ebLogInfo("*** ebCluElasticCellManager:mPatchXml >>>")
        _cludgroups = aCludgroupsElement
        _size_dict = aDgSizesDict
        _eBoxCluCtrl = self.mGetEbox()
        _cell_count = len(_eBoxCluCtrl.mReturnCellNodes())
        _cluDgObj = ebCluManageDiskgroup(_eBoxCluCtrl, self.mGetAoptions())
        _dgConstantsObj = _cluDgObj.mGetConstantsObj()
        _griddisk_count = 0

        ebLogInfo("*** Using Cell Count %s" % (_cell_count))

        for _dgid in _cludgroups:
            ebLogInfo("*** Working on Diskgroup ID %s" %(_dgid))
            _dgConfig = _eBoxCluCtrl.mGetStorage().mGetDiskGroupConfig(_dgid)
            _dg_name = _dgConfig.mGetDgName()
            _dg_sizeGB=_size_dict[_dg_name]['totalgb']

            if _griddisk_count == 0:
                _griddisk_count = _cluDgObj.mGetGridDiskCount(_dg_name)
                if _griddisk_count == 0:
                    ebLogWarn("*** ebCluElasticCellManager: Failed to count number of grid disks. Failed to Patch XML")
                    return

            _dg_sliceGB = _dg_sizeGB / (int(_cell_count) * _griddisk_count)
            _dg_sliceGB = int(16 * (_dg_sliceGB / 16))  ## Round to multiple of 16

            ebLogInfo("*** Persisting slice size to %s" % (_dg_sliceGB))
            _dgConfig.mSetSliceSize(_dg_sliceGB)

            if _dg_name.startswith(_dgConstantsObj._sparse_dg_prefix):
                _sparse_vsliceGB = int(_dg_sliceGB * _dgConstantsObj._sparse_vsize_factor)
                _cell_list = _eBoxCluCtrl.mReturnCellNodes()
                for _cell_name in sorted(_cell_list.keys()):
                    _node = exaBoxNode(get_gcontext())
                    _node.mConnect(aHost=_cell_name)
                    _cellcli_list_virtsize = "cellcli -e list griddisk attributes virtualSize where name like \\'" + _dg_name + ".*\\'"
                    ebLogInfo("*** Executing the command - %s" % _cellcli_list_virtsize)
                    _in, _out, _err = _node.mExecuteCmd(_cellcli_list_virtsize)
                    _output = _out.readlines()
                    if _output:
                        ebLogInfo("*** Output - %s" % _output)
                        _slice_size = 0.0
                        _line = _output[0]
                        _slice_size_from_cell = _line.strip()
                        if _slice_size_from_cell.endswith('M'):
                            _slice_size = _slice_size_from_cell[:-1]
                            _dg_sliceGB = (float(_slice_size) / 1024)
                        if _slice_size_from_cell.endswith('G'):
                            _slice_size = _slice_size_from_cell[:-1]
                            _dg_sliceGB = (float)(_slice_size)
                        if _slice_size_from_cell.endswith('T'):
                            _slice_size = _slice_size_from_cell[:-1]
                            _dg_sliceGB = (float(_slice_size) * 1024)
                        if _slice_size != 0.0:
                            _sparse_vsliceGB = _dg_sliceGB
                            break # We read slice size from this cell; no need to check next cell


                ebLogInfo("*** Sparse found : Persisting virtual size to %s" % (_sparse_vsliceGB))
                _dgConfig.mSetSparseVirtualSize(str(_sparse_vsliceGB) + 'G')

            ebLogInfo("*** Persisting total size to %s" % (_dg_sizeGB))
            _dgConfig.mSetDiskGroupSize(int(_dg_sizeGB))

            # Remove the old config and add new on
            _eBoxCluCtrl.mGetStorage().mRemoveDiskGroupConfig(_dgid)
            _eBoxCluCtrl.mGetStorage().mAddDiskGroupConfig(_dgConfig)

        _eBoxCluCtrl.mSaveXMLClusterConfiguration()

        ebLogInfo("*** ebCluElasticCellManager:mPatchXml <<<")
        
    def mCalculateDgResize(self, aCludgroupsElement, aDgSizesDict, aDgSizesDictAfterCellupdate):

        ebLogInfo("*** ebCluElasticCellManager:mCalculateDgResize >>>")
        _cludgroups = aCludgroupsElement
        _increment_storage = False
        _size_dict = aDgSizesDict
        _size_dict_afterupdate = aDgSizesDictAfterCellupdate
        _increment_percent=0
        _eBoxCluCtrl = self.mGetEbox()
        _cluDgObj = ebCluManageDiskgroup(_eBoxCluCtrl, self.mGetAoptions())
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
              
                    _temp_percent = (_temp_new_size - _temp_totalgb)*100/_temp_totalgb
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
                        _abort_shrink=True
                        break
        
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
                    if _abort_shrink:
                        _size_dict.update(_size_dict_afterupdate)
                        ebLogDebug("Aborting resize as the calculated resize is greater than current size")
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
    
    def mExecuteCellCloneAndSaveXml(self, aStep=None, aRebalancePower=None, aCludgroupsElement=None):
        
        ebLogInfo("*** ebCluElasticCellManager:mExecuteCellCloneAndSaveXml >>>")
        
        _rc = 0
        _options = self.mGetAoptions()
        _eBoxCluCtrl = self.mGetEbox()
        _oedaCliMgr = self.mGetOedaCliMgr()
        _cellConf = self.mGetUpdateConf()
        _uuid = _eBoxCluCtrl.mGetUUID()
        _oedaXmlPath = self.mGetOedaXmlPath() + "/" + "addCell_" + _uuid + ".xml" 
        _power = aRebalancePower
        if not aRebalancePower:
            _power = _eBoxCluCtrl.mCheckConfigOption('rebal_power')

        _srccell = None

        _cell_list = _eBoxCluCtrl.mReturnCellNodes()
        for _cell_name in sorted(_cell_list.keys()):
            _srccell = _cell_name
            break

        try:
            _eBoxCluCtrl.mAcquireRemoteLock()
            _configxml = _eBoxCluCtrl.mGetOedaPath() + '/exacloud.conf/elastic_cell_' + _uuid + '.xml'
            _eBoxCluCtrl.mExecuteLocal("/bin/cp {} {}".format(_eBoxCluCtrl.mGetPatchConfig(), _configxml))

            ebLogInfo("*** Using source XML : %s and savexml : %s" %(_configxml, _oedaXmlPath))
            _clu_utils = ebCluUtils(_eBoxCluCtrl)
            if _eBoxCluCtrl.mIsAdbs() and aStep == "CONFIG_CELL":
                _domU = _eBoxCluCtrl.mReturnDom0DomUPair()[0][1]
                _newdiskgroupNames = getDiskGroupNames(_domU)
                _diskGroupIds = aCludgroupsElement
                _id_diskgroup_mapping = dict(zip(_diskGroupIds, _newdiskgroupNames))

                for _diskGroupId,_newdiskgroupName in _id_diskgroup_mapping.items():
                    _dgConfig = _eBoxCluCtrl.mGetStorage().mGetDiskGroupConfig(_diskGroupId)
                    if _dgConfig.mGetGridDiskPrefix() is None:
                        # This will be the case in the 1st ADD CELL
                        #  <diskGroupName>DATAC1</diskGroupName>
                        #  No Griddisk prefix
                        _griddiskPrefix = _dgConfig.mGetDgName()
                    else:
                        # in any other ADD CELL
                        #  <diskGroupName>DATA</diskGroupName>
                        #  <gridDiskPrefix>DATAC1</gridDiskPrefix>
                        _griddiskPrefix = _dgConfig.mGetGridDiskPrefix()
                    ebLogInfo(f"The diskGroup id from the object = {_diskGroupId}")
                    ebLogInfo(f"The diskGroup id={_diskGroupId} and Customized diskGroupName={_newdiskgroupName} and griddisk Prefix = {_griddiskPrefix}")
                    _oedaCliMgr.mUpdateDiskGroupGriddiskPrefix(_newdiskgroupName,_griddiskPrefix,_diskGroupId,_configxml, _configxml)
                    
                ebLogInfo(f"*** Updated and using the patched XML for ADBS : {_configxml}")

            _oedaCliMgr.mAddCell(_srccell, _configxml, _oedaXmlPath, _cellConf, True, _power,
                                 _eBoxCluCtrl.mIsKVM(), 
                                 _eBoxCluCtrl.mGetClusters().mGetCluster().mGetCluName(), 'false', aStep,
                                 aCluUtils=self.mGetCluUtils())

        except ExacloudRuntimeError as e:
            ebLogDebug("*** Exception Stack Trace: %s" %(str(e)))
            _detail_error = "Could not add cell through Oedacli"
            _eBoxCluCtrl.mUpdateErrorObject(gElasticError['CELL_OEDA_ADD_CMD_FAILED'], _detail_error)
            return self.mRecordError(gCellUpdateError['OedaError'], "*** " + _detail_error)

        finally:
            _eBoxCluCtrl.mReleaseRemoteLock() 
      
        if _options.steplist and not _eBoxCluCtrl.mIsXS() and not _eBoxCluCtrl.mIsAdbs():                                                                                                           
            if 'Workflow_data' in _options.jsonconf:
                dg_size_dict = _options.jsonconf['Workflow_data']
                if 'workflow_step' in dg_size_dict:
                    del dg_size_dict['workflow_step'] 
       
            if not _eBoxCluCtrl.IsZdlraProv():
                #We dont (re)-patch xml for zdlra here.
                #This usecase is specific to exacs.        
                _total_dg_size = 0
                _sparse_enabled = False
                for _dgname, _size in dg_size_dict.items():
                    _total_dg_size = _total_dg_size + int(_size['totalgb'])
                    if 'DATA' in _dgname:
                        _data_size = int(_size['totalgb'])
                    if 'RECO' in _dgname:
                        _reco_size = int(_size['totalgb'])
                    if 'SPRC' in _dgname:
                        _sparse_enabled = True

                if _data_size > _reco_size:                     
                   _backup_disk = False                          
                else:        
                   _backup_disk = True                                   

                _eBoxCluCtrl.mGetStorage().mPatchClusterDiskgroup(
                    aCreateSparse = _sparse_enabled, 
                    aBackupDisk = _backup_disk, 
                    aDRSdistrib = None, 
                    aOptions = self.mGetAoptions(), 
                    aTotalDGSize = int(_total_dg_size/3))

        _eBoxCluCtrl.mUpdateInMemoryXmlConfig(_oedaXmlPath, self.mGetAoptions())
        ebLogInfo('ebCluCtrl: Saved patched Cluster Config: ' + _eBoxCluCtrl.mGetPatchConfig())
        _eBoxCluCtrl.mDeleteClusterDomUList()
        _eBoxCluCtrl.mSaveClusterDomUList()
        _db = ebGetDefaultDB()
        _db.import_file(_eBoxCluCtrl.mGetPatchConfig())

        if aStep in ["CONFIG_CELL", "CREATE_GRIDDISKS"]:
            return _rc

        _rc = self.validateKfodCmd()
        if _rc:
            _detail_error = "kfod utility did not find Griddisks from new cell. Cloning operation failed."
            _eBoxCluCtrl.mUpdateErrorObject(gElasticError['CELL_CLONING_FAILED'], _detail_error)
            return self.mRecordError(gCellUpdateError['CellOperationFailed'], "*** " + _detail_error)

        #Copy the keys from OEDA staging area (WorkDir) to cluster directory & cluster/oeda
        _eBoxCluCtrl.mSaveOEDASSHKeys()

        ebLogInfo("*** ebCluElasticCellManager:mExecuteCellCloneAndSaveXml <<<")
        return _rc
    #end mExecuteCellClone

    def mEnsureDgRebalanced(self, aTimeout=None):
        ebLogInfo("*** ebCluElasticCellManager:mEnsureDgRebalanced >>>")
        
        _eBoxCluCtrl = self.mGetEbox()
        _cluster = _eBoxCluCtrl.mGetClusters().mGetCluster()   
        _cludgroups = _cluster.mGetCluDiskGroups()
        _count = 0
        if aTimeout:
            _timeout = aTimeout
        else:
            _timeout = int(_eBoxCluCtrl.mCheckConfigOption('rebal_timeout')) # 10000 = approx 7 days

        _cluDgObj = ebCluManageDiskgroup(_eBoxCluCtrl, self.mGetAoptions())
        _dgConstantsObj = _cluDgObj.mGetConstantsObj()
        _rc = 0
      
        ebLogInfo("*** Ensuring diskgroups rebalanced")
        _domU = self.getConnectableDomU()
        _path, _sid = _eBoxCluCtrl.mGetGridHome(_domU)
        if not _path or not _sid:
            ebLogError("Failed to fetch Grid home path and SID")
            return 1
        _cmd_pfx = 'ORACLE_HOME=%s;export ORACLE_HOME;ORACLE_SID=%s; export ORACLE_SID;PATH=$PATH:$ORACLE_HOME/bin;export PATH;'%(_path,_sid)
        _cmd = _cmd_pfx + "echo \"select GROUP_NUMBER, OPERATION, PASS, STATE, SOFAR, EST_WORK, EST_MINUTES, POWER from GV\$ASM_OPERATION ;\" | sqlplus -s / as sysasm"
        _cmd_timeout = 300
        _cmd_pfx_state = "ORACLE_HOME=%s;export ORACLE_HOME;ORACLE_SID=%s; export ORACLE_SID;PATH=\$PATH:\$ORACLE_HOME/bin;export PATH;"%(_path,_sid)
        _cmd_state_run = _cmd_pfx_state + 'echo \\"select GROUP_NUMBER, STATE, POWER, EST_MINUTES, SOFAR, EST_WORK from GV\\\\\$ASM_OPERATION where STATE=\'RUN\';\\" | sqlplus -s / as sysasm'
        _cmd_get_diskgroup_name = _cmd_pfx_state + 'echo \\"select GROUP_NUMBER, NAME from GV\\\\\$ASM_DISKGROUP where GROUP_NUMBER=\'{0}\';\\" | sqlplus -s / as sysasm'
        _time_start = time.time()
        _node = exaBoxNode(get_gcontext())
        while True:
            _node.mConnect(_domU)
            _i, _o, _e = _node.mExecuteCmd(f'su - grid -c \'{_cmd}\'', aTimeout=_cmd_timeout)
            _node.mDisconnect()
            _out = _o.readlines()
            if "no rows selected\n" in _out:
                ebLogInfo("No rebalance in progress")
                break
            else:
                _count = _count + 1

                if _count > _timeout:
                    _time = _timeout
                    _err = f"Rebalance Operation is stuck for {_time} mins."
                    ebLogError(_err)
                    return 1

                ebLogInfo("Rebalance is in progress")
                _rebalance_output = ' '.join(_out)
                if _eBoxCluCtrl.mCheckConfigOption('extra_traces', "True"):
                    ebLogInfo(_rebalance_output)
                _time_start = _cluDgObj.mUpdateRebalanceStatus(_domU, _cmd_state_run,
                                                               _cmd_get_diskgroup_name,
                                                               _time_start, _cmd_timeout,
                                                               self.mGetDgConstantsObj())

            time.sleep(60)

        ebLogInfo("*** ebCluElasticCellManager:mEnsureDgRebalanced <<<")
        return _rc
    # end mEnsureDgRebalanced
    
    def mExecuteResizeDGs(self,aDgSizesDict):
        """
        Logic to resize diskgroups, it uses
        cludiskgroup.py
        Only called by mResizeDGs
        """

        ebLogInfo("*** ebCluElasticCellManager:mExecuteResizeDGs >>>")
        
        _dg_sizes_dict = aDgSizesDict
        _eBoxCluCtrl = self.mGetEbox()
        _cluDgObj = ebCluManageDiskgroup(_eBoxCluCtrl, self.mGetAoptions())
        _dgConstantsObj = _cluDgObj.mGetConstantsObj()
        
        _rc = 0
        ebLogInfo(json.dumps(_dg_sizes_dict, indent=4, sort_keys=True))
        
        ebLogInfo("*** Restoring diskgroups to their original sizes")
        for _dg_name in list(_dg_sizes_dict.keys()):
            _dg_data = {}
            _dg_data['Command'] = "dg_resize"
            _dg_data['diskgroup'] = _dg_name
            _dg_data['new_sizeGB'] = _dg_sizes_dict[_dg_name]['totalgb']
            
            dgrpOpOptions = dgAOptions(self)
            dgrpOpOptions.jsonconf['diskgroup'] =_dg_data['diskgroup']
            dgrpOpOptions.jsonconf['new_sizeGB'] =_dg_data['new_sizeGB']
            dgrpOpOptions.configpath = self.__xmlpath
            
            _cluDgObj = ebCluManageDiskgroup(_eBoxCluCtrl, dgrpOpOptions)
            _cluDgObj.mSetDiskGroupOperationData(_dg_data)
            _rc = _cluDgObj.mClusterDgrpResize(dgrpOpOptions)
            if _rc != 0:
                _detail_error = "Could not complete resize operation for diskgroup " + _dg_name
                _eBoxCluCtrl.mUpdateErrorObject(gElasticError['CELL_DG_RESIZE_OPS_FAILED'], _detail_error)
                return self.mRecordError(gDiskgroupError['DgOperationError'], "*** " + _detail_error)

        if _eBoxCluCtrl.mIsOciEXACC():
            ebLogInfo("*** ExaCC Ensuring diskgroups rebalanced after resize")
            _rc1 = self.mEnsureDgRebalanced()
            if _rc1:
                return self.mRecordError(gCellUpdateError['DiskgroupInfoFailed'],
                    "*** Fetching rebalance status of diskgroup(s) FAILED")
        else:
            ebLogInfo("*** ebCluElasticCellManager:mExecuteResizeDGs <<<")
            ebLogTrace("*** Skipping mEnsureDgRebalanced")
        return _rc
    #end mExecuteResizeDGs

    def mValidateAllDiskGroupsSizes(self, aStepList):
        """
        Method that calls cludiskgroup.py logic
        to validate all diskgroup sizes against the
        payload aOptions values provided

        PLEASE FIND DIAGRAM IN: 
        https://confluence.oraclecorp.com/confluence
          /display/EDCS/Elastic+Cell+-+Diagrams
        """

        _options = self.mGetAoptions()
        _step_list = aStepList 
        _eBoxCluCtrl = self.mGetEbox()
        _cluster = _eBoxCluCtrl.mGetClusters().mGetCluster()
        cludgroups = _cluster.mGetCluDiskGroups()

        _message = "Validate diskgroups size(s)"
        ebLogInfo("*** " + _message)
        # This step is to ensure 15% freespace to avoid issues during shrink
        if _options.steplist and "Workflow_data" in _options.jsonconf:
            dg_size_dict = _options.jsonconf['Workflow_data']
            del dg_size_dict['workflow_step']
        else:
            _detail_error = "Missing diskgroup info in payload"
            _eBoxCluCtrl.mUpdateErrorObject(gElasticError['CELL_DG_SHRINK_FAILED'], _detail_error)
            return self.mRecordError(gCellUpdateError['OperationFailed'], "*** " + _detail_error)

        dg_size_dict_after_update_cell = {}
        _eBoxCluCtrl.mUpdateStatusOEDA(True, "WAIT_RESIZE_DGS", _step_list, _message)
        _rc = self.mFetchAndSaveDGSizes(cludgroups, dg_size_dict_after_update_cell)

        self.mCalculateDgResize(cludgroups, dg_size_dict, dg_size_dict_after_update_cell)
        if _rc:
            _detail_error = "Calculating the resize values for diskgroup(s) failed"
            _eBoxCluCtrl.mUpdateErrorObject(gElasticError['CELL_DG_SHRINK_FAILED'], _detail_error)
            return self.mRecordError(gCellUpdateError['OperationFailed'], "*** " + _detail_error)

        def mValidateHandler(aDgSizesDict):
            """
            """
            _dg_sizes_dict = aDgSizesDict
            _eBoxCluCtrl = self.mGetEbox()
            _cluDgObj = ebCluManageDiskgroup(_eBoxCluCtrl, self.mGetAoptions())
            _dgConstantsObj = _cluDgObj.mGetConstantsObj()
            _flow = self.mGetUpdateConf()['operation']

            _rc = 0
            ebLogInfo(json.dumps(_dg_sizes_dict, indent=4, sort_keys=True))

            ebLogInfo("*** Validating diskgroups sizes")
            for _dg_name in list(_dg_sizes_dict.keys()):
                _dg_data = {}
                _dg_data['Command'] = "dg_resize"
                _dg_data['diskgroup'] = _dg_name
                _dg_data['new_sizeGB'] = _dg_sizes_dict[_dg_name]['totalgb']

                dgrpOpOptions = dgAOptions(self)
                dgrpOpOptions.jsonconf['diskgroup'] =_dg_data['diskgroup']
                dgrpOpOptions.jsonconf['new_sizeGB'] =_dg_data['new_sizeGB']
                dgrpOpOptions.configpath = self.__xmlpath

                _cluDgObj = ebCluManageDiskgroup(_eBoxCluCtrl, dgrpOpOptions)
                _cluDgObj.mSetDiskGroupOperationData(_dg_data)

                # Declare variables to use
                _dg_fgrp_prop_dict = {}

                # change gb to MB
                _newsizeMB = int(_dg_data['new_sizeGB']) * 1024
                ebLogInfo(f"New Size for {_dg_name} in MB is {_newsizeMB}")

                # Calculate fail groups
                _dgrp_properties = []
                _dgrp_properties.append(_dgConstantsObj._propkey_failgroup)
                _rc = _cluDgObj.mClusterDgrpInfo2(_options, _dg_name, _dgrp_properties)
                if _rc != 0:
                    _detail_error = "Could not fetch info for diskgroup: " + _dg_name
                    _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_FETCHING_DETAILS_DG'], _detail_error)
                    return self.mRecordError(gDiskgroupError['ErrorFetchingDetails'], "*** Could not\
                        fetch info for diskgroup " + _dg_name)

                # Read the INFO file containing the storage property value
                # It should be ready and populated as mClusterDgrpInfo2 above is a blocking call
                _dbaasObj = _cluDgObj.mGetDbaasObj()
                _infoobj = _dbaasObj.mReadStatusFromDomU(_options, _cluDgObj.mGetLastDomUused(), _cluDgObj.mGetOutJson())
                # Get failgroups for the DATA DG
                _rc = _cluDgObj.mValidateAndGetFailgroupDetails(_infoobj, _dg_name, _dgConstantsObj, _dg_fgrp_prop_dict)

                if _rc == 0:
                    _cell_list = []
                    _cell_count = 0
                    _data_cell_vs_griddisks_map = {}
                    ebLogInfo(json.dumps(_dg_fgrp_prop_dict, indent=4, sort_keys=True))
                    _rc = _cluDgObj._extract_cell_vs_griddisks_map(_dg_name, _dg_fgrp_prop_dict, _data_cell_vs_griddisks_map)

                    # Get list of griddisks
                    if _rc == 0:
                        _dg_griddisks_count = 0

                        for _cell_name in sorted (_data_cell_vs_griddisks_map.keys()): 
                            ebLogInfo("mDiskgroupUpdate: Cell Name : %s" % _cell_name)
                            if len(_data_cell_vs_griddisks_map[_cell_name]) > 1:
                                if _dg_griddisks_count == 0:
                                    _dg_griddisks_count = len(_data_cell_vs_griddisks_map[_cell_name])
                                    ebLogInfo("*** mDiskgroupUpdate: Number of grid disks in a cell = %d" % _dg_griddisks_count)
                                _cell_list.append(_cell_name)

                    # Calculate cell list
                    _cell_count = len(_cell_list)
                    ebLogInfo("*** mDiskgroupUpdate: Cell List : %s" % ' '.join(_cell_list))
                    if _dg_griddisks_count == 0:
                        _detail_error = "mDiskgroupUpdate: Failed to count number of grid disks."
                        ebLogInfo("*** " + _detail_error) 
                        _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_FETCHING_GRIDDISK_COUNT'], _detail_error)
                        return self.mRecordError(gDiskgroupError['ErrorFetchingDetails'], "*** Could not\
                                                           fetch info for diskgroup " + _dg_name)

                    # Not needed in reshape...?
                    _dg_slice =  _newsizeMB/(_cell_count * _dg_griddisks_count)
                    _dg_slice = int(_dg_slice / 16) * 16  ## Round to multiple of 16
                    _newsizeMB = _dg_slice * (_cell_count * _dg_griddisks_count)
                    ebLogInfo("*** DG Size : %s, Cell Count : %s, Slice size : %s, Griddisk Count : %s" %(_newsizeMB, _cell_count, _dg_slice, _dg_griddisks_count))

                ### Size has to be validated against this number post rebalance of sparse DG
                _newExpectedSizeMB = _newsizeMB
                if _dg_name.startswith(_dgConstantsObj._sparse_dg_prefix):
                    ebLogInfo(f"Applying SPARSE multiplier {_dgConstantsObj._sparse_vsize_factor}")
                    _newExpectedSizeMB = _newsizeMB * _dgConstantsObj._sparse_vsize_factor


                # Call to validate dg sizes
                _dg_cursize = _cluDgObj.mUtilGetDiskgroupSize(_options, _dg_name, _dgConstantsObj)
                _diskgroupData = _cluDgObj.mGetDiskGroupOperationData()
                _diskgroupData["Status"] = "Pass"
                _diskgroupData["ErrorCode"] = "0"
                _diskgroupData["SizeMB"] = _dg_cursize
                _rc = _cluDgObj.mValidateDgsPostRebalance(dgrpOpOptions, _dg_name, _newExpectedSizeMB, None, _diskgroupData)
                if _rc != 0:
                    _detail_error = f"Could not validate diskgroup size for {_dg_name}"
                    _eBoxCluCtrl.mUpdateErrorObject(gElasticError['CELL_DG_RESIZE_OPS_FAILED'], _detail_error)
                    return self.mRecordError(gDiskgroupError['DgOperationError'], "*** " + _detail_error)

                # Update XML
                _log = _dg_name + " resized successfully to " + str(_newsizeMB) + " MB"
                ebLogInfo(_log)
                _diskgroupData["Log"] = _log
                _diskgroupData["SizeMB"] = _newsizeMB
                # Update xml file
                _cluster = _eBoxCluCtrl.mGetClusters().mGetCluster()
                _cludgroups = _cluster.mGetCluDiskGroups()
                for _dgid in _cludgroups:
                    _dgConfig = _eBoxCluCtrl.mGetStorage().mGetDiskGroupConfig(_dgid)
                    if _dgConfig.mGetDgName() == _dg_name:
                        ebLogInfo("*** Working on Diskgroup ID %s" %(_dgid))
                        _dg_slice_size_GB = int(_dg_slice/1024)
                        ebLogInfo("*** Diskgroup Slice for %s Is %s" %(_dg_name, _dg_slice))
                        if _dg_name.startswith(_dgConstantsObj._sparse_dg_prefix):
                            _dgConfig.mSetSparseVirtualSize(_dg_slice_size_GB * _dgConstantsObj._sparse_vsize_factor)
                        _total_size_in_GB = int(_newsizeMB/1024)
                        _dgConfig.mSetSliceSize(_dg_slice_size_GB)
                        _dgConfig.mSetDiskGroupSize(_total_size_in_GB)
                        # Remove the old config and add new one
                        _eBoxCluCtrl.mGetStorage().mRemoveDiskGroupConfig(_dgid)
                        _eBoxCluCtrl.mGetStorage().mAddDiskGroupConfig(_dgConfig)
                        _eBoxCluCtrl.mSaveXMLClusterConfiguration()
                        break

        _rc = mValidateHandler(dg_size_dict)
        if _rc:
            _detail_error = "Validation of diskgroups sizes failed"
            _eBoxCluCtrl.mUpdateErrorObject(gElasticError['CELL_DG_SHRINK_FAILED'], _detail_error)
            return self.mRecordError(gCellUpdateError['OperationFailed'], "*** " + _detail_error)
        return _rc

    def mExecuteResizeGridDisks(self, aDgSizesDict, aStepList):
        """
        Driver to resize the griddisks back to their original sizes
        during the ADD CELL operation
        """
        # PLEASE FIND DIAGRAM IN: 
        # https://confluence.oraclecorp.com/confluence
        #   /display/EDCS/Elastic+Cell+-+Diagrams

        _message = "Resizing GridDisks sizes"
        ebLogInfo("*** " + _message)
        _options = self.mGetAoptions()
        _step_list = aStepList
        _eBoxCluCtrl = self.mGetEbox()
        _cluster = _eBoxCluCtrl.mGetClusters().mGetCluster()
        cludgroups = _cluster.mGetCluDiskGroups()

        # This step is to ensure 15% freespace to avoid issues during shrink
        if _options.steplist and "Workflow_data" in _options.jsonconf:
            dg_size_dict = _options.jsonconf['Workflow_data']
            del dg_size_dict['workflow_step']
        else:
            _detail_error = "Missing diskgroup info in payload"
            _eBoxCluCtrl.mUpdateErrorObject(gElasticError['CELL_GD_SHRINK_FAILED'], _detail_error)
            return self.mRecordError(gCellUpdateError['OperationFailed'], "*** " + _detail_error)

        dg_size_dict_after_update_cell = {}
        _eBoxCluCtrl.mUpdateStatusOEDA(True, "RESIZE_GRIDDISKS", _step_list, _message)
        _rc = self.mFetchAndSaveDGSizes(cludgroups, dg_size_dict_after_update_cell)

        if _rc:
            _detail_error = "Calculating the resize values for diskgroup(s) failed"
            _eBoxCluCtrl.mUpdateErrorObject(gElasticError['CELL_GD_SHRINK_FAILED'], _detail_error)
            return self.mRecordError(gCellUpdateError['OperationFailed'], "*** " + _detail_error)

        def mResizeGridDisk(aDgSizesDict):
            """
            """

            _dg_sizes_dict = aDgSizesDict
            _eBoxCluCtrl = self.mGetEbox()
            _cluDgObj = ebCluManageDiskgroup(_eBoxCluCtrl, self.mGetAoptions())
            _dgConstantsObj = _cluDgObj.mGetConstantsObj()
            _flow = self.mGetUpdateConf()['operation']

            _rc = 0
            ebLogInfo(json.dumps(_dg_sizes_dict, indent=4, sort_keys=True))

            ebLogInfo("*** Resizing Griddisks")
            for _dg_name in list(_dg_sizes_dict.keys()):
                _dg_data = {}
                _dg_data['Command'] = "dg_resize"
                _dg_data['diskgroup'] = _dg_name
                _dg_data['new_sizeGB'] = _dg_sizes_dict[_dg_name]['totalgb']

                dgrpOpOptions = dgAOptions(self)
                dgrpOpOptions.jsonconf['diskgroup'] =_dg_data['diskgroup']
                dgrpOpOptions.jsonconf['new_sizeGB'] =_dg_data['new_sizeGB']
                dgrpOpOptions.configpath = self.__xmlpath

                _cluDgObj = ebCluManageDiskgroup(_eBoxCluCtrl, dgrpOpOptions)
                _cluDgObj.mSetDiskGroupOperationData(_dg_data)

                # Declare variables to use
                _dg_fgrp_prop_dict = {}

                # change gb to MB
                _newsizeMB = math.ceil(_dg_data['new_sizeGB'] * 1024)
                ebLogInfo(f"New Size for {_dg_name} in MB is {_newsizeMB}")

                # Calculate fail groups
                _dgrp_properties = []
                _dgrp_properties.append(_dgConstantsObj._propkey_failgroup)
                _rc = _cluDgObj.mClusterDgrpInfo2(_options, _dg_name, _dgrp_properties)
                if _rc != 0:
                    _detail_error = "Could not fetch info for diskgroup: " + _dg_name
                    _eBoxCluCtrl.mUpdateErrorObject(gReshapeError['ERROR_FETCHING_DETAILS_DG'], _detail_error)
                    return self.mRecordError(gDiskgroupError['ErrorFetchingDetails'], "*** Could not\
                        fetch info for diskgroup " + _dg_name)

                # Read the INFO file containing the storage property value
                # It should be ready and populated as mClusterDgrpInfo2 above is a blocking call
                _dbaasObj = _cluDgObj.mGetDbaasObj()
                _infoobj = _dbaasObj.mReadStatusFromDomU(_options, _cluDgObj.mGetLastDomUused(), _cluDgObj.mGetOutJson())
                # Get failgroups for the DATA DG
                _rc = _cluDgObj.mValidateAndGetFailgroupDetails(_infoobj, _dg_name, _dgConstantsObj, _dg_fgrp_prop_dict)

                if _rc == 0:
                    _cell_list = []
                    _cell_count = 0
                    _data_cell_vs_griddisks_map = {}
                    ebLogInfo(json.dumps(_dg_fgrp_prop_dict, indent=4, sort_keys=True))
                    _rc = _cluDgObj._extract_cell_vs_griddisks_map(_dg_name, _dg_fgrp_prop_dict, _data_cell_vs_griddisks_map)

                    # Get list of griddisks
                    if _rc == 0:
                        _dg_griddisks_count = 0

                        for _cell_name in sorted (_data_cell_vs_griddisks_map.keys()): 
                            ebLogInfo("mDiskgroupUpdate: Cell Name : %s" % _cell_name)
                            if len(_data_cell_vs_griddisks_map[_cell_name]) > 1:
                                if _dg_griddisks_count == 0:
                                    _dg_griddisks_count = len(_data_cell_vs_griddisks_map[_cell_name])
                                    ebLogInfo("*** mDiskgroupUpdate: Number of grid disks in a cell = %d" % _dg_griddisks_count)
                                _cell_list.append(_cell_name)

                    # Calculate cell list
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

                    ebLogInfo("*** DG Size : %s, Cell Count : %s, Slice size : %s, Griddisk Count : %s" %(_newsizeMB, _cell_count, _dg_slice, _dg_griddisks_count))

                _newExpectedSizeMB = _newsizeMB

                # Call to validate dg sizes
                _dg_cursize = _cluDgObj.mUtilGetDiskgroupSize(_options, _dg_name, _dgConstantsObj)
                _diskgroupData = _cluDgObj.mGetDiskGroupOperationData()
                _diskgroupData["Status"] = "Pass"
                _diskgroupData["ErrorCode"] = "0"
                _diskgroupData["SizeMB"] = _dg_cursize
                _rc = _cluDgObj.mResizeGriddisks(dgrpOpOptions, _dg_name, _newExpectedSizeMB, _diskgroupData)
                if _rc != 0:
                    _detail_error = f"Could not validate diskgroup size for {_dg_name}"
                    _eBoxCluCtrl.mUpdateErrorObject(gElasticError['CELL_DG_RESIZE_OPS_FAILED'], _detail_error)
                    return self.mRecordError(gDiskgroupError['DgOperationError'], "*** " + _detail_error)

        # Call helper to use cludiskgroup logic
        _rc = mResizeGridDisk(dg_size_dict_after_update_cell)
        if _rc:
            _detail_error = "Resize of griddisks failed"
            _eBoxCluCtrl.mUpdateErrorObject(gElasticError['CELL_GD_SHRINK_FAILED'], _detail_error)
            return self.mRecordError(gCellUpdateError['OperationFailed'], "*** " + _detail_error)
        return _rc
    #end mExecuteResizeGridDisks


    # Add Cell Operation should ensure the following checks are True 
    # 1) asmcmd lsdsk should report disks from the cell
    # 2) cell ip should be stored in cellip.ora
    # and 
    # Delete Cell Operation should ensure the above (2 checks) are False.
    def mCellOperationCheck(self, aCell, aOperation):

        _ebox = self.mGetEbox()
        _op = aOperation
        _cluster = _ebox.mGetClusters().mGetCluster()
        _cludgroups = _cluster.mGetCluDiskGroups()
        _cludgroup_types = []
        for _cludg_id in _cludgroups:
            _dg = _ebox.mGetStorage().mGetDiskGroupConfig(_cludg_id)
            _cludgroup_types.append(_dg.mGetDiskGroupType().lower())
        _dgConstantsObj = ebDiskgroupOpConstants()
        _dg_name = None
        if _ebox.IsZdlraProv():
            #For Zdlra, the diskgroupid can be either 'catalogdg'+'deltadg' or 'datadg'+recodg', depending on the xml patching.
            #diskgroupid is just a reference to get the disk groups.
            #But the actual diskgroup names will remain to be CATALOG and DELTA.
            #See mPatchClusterZdlraDisks in cluzdlra.py for details on how this dgid is used.
            if _dgConstantsObj._catalog_dg_type_str in _cludgroup_types:
                _constdgname = _dgConstantsObj._catalog_dg_type_str
            else:
                _constdgname = _dgConstantsObj._data_dg_type_str
        else:
            _constdgname = _dgConstantsObj._data_dg_type_str

        for _dgid in _cludgroups:
            _dg = _ebox.mGetStorage().mGetDiskGroupConfig(_dgid)
            _dg_type = _dg.mGetDiskGroupType().lower()
            if _dg_type == _constdgname:
                _dg_name = _dg.mGetDgName()
                break

        _domU = _ebox.mReturnDom0DomUPair()[0][1]                                                                                       
        _path, _sid = _ebox.mGetGridHome(_domU)
        _node = exaBoxNode(get_gcontext())
        _cmd = "{0}/bin/asmcmd lsdsk -G {1} | grep {2}".format(_path, _dg_name, aCell.split('.')[0])

        _node.mConnect(aHost=_domU)
        _node.mExecuteCmdLog('{0}/bin/srvctl status asm -node {1}'.format(_path, _domU))
        if not _node.mGetCmdExitStatus():

            # If ASM is running check asmcmd lsdsk output to contain cellname
            ebLogInfo("Information from asmcmd ldsk:")
            _node.mExecuteCmdLog(_cmd)
            if _node.mGetCmdExitStatus() and _op == 'ADD_CELL':
                _node.mDisconnect()
                raise ExacloudRuntimeError(0x0802, 0xA, "Add Cell Operation Failed")
            elif not _node.mGetCmdExitStatus() and _op == 'DELETE_CELL':
                _node.mDisconnect()
                raise ExacloudRuntimeError(0x0802, 0xA, "Delete Cell Operation Failed")
            else:
                ebLogInfo("{0} check ran successfully for cell {1}".format(_op, aCell))

        _node.mDisconnect()
    
    def mFetchCellInfo(self, aCellInfoParam):
        ebLogInfo("*** ebCluElasticCellManager:mFetchCellInfo >>>")
        _cellInfoParam = aCellInfoParam
        _eBoxCluCtrl = self.mGetEbox()
        _cluster = _eBoxCluCtrl.mGetClusters().mGetCluster()
        _cludgroups = _cluster.mGetCluDiskGroups()
        _dgConstantsObj = ebDiskgroupOpConstants()
        _rc = 0
        
        _cellOperationData = self.mGetCellOperationData()
        if _cellInfoParam == 'cell_rbal_status':
            dg_list = []
            for _dgid in _cludgroups:
                _dg = _eBoxCluCtrl.mGetStorage().mGetDiskGroupConfig(_dgid)
                _dg_type = _dg.mGetDiskGroupType().lower()
                if _dg_type in [_dgConstantsObj._data_dg_type_str, _dgConstantsObj._reco_dg_type_str, _dgConstantsObj._sparse_dg_type_str]:
                    _dg_name = _dg.mGetDgName()
                    dg_list.append(_dg_name)
            _cellOperationData['rebalance_status'] = {}
            for _dg_name in dg_list:
                ebLogInfo("*** Getting rebalance status for diskgroup %s" %(_dg_name))
                _dg_data = {}
                _dg_data["Command"] = "dg_info"
                _dg_data['diskgroup'] = _dg_name
                dgrpOpOptions = dgAOptions(self)
                dgrpOpOptions.jsonconf['diskgroup'] =_dg_data['diskgroup']
            
                _cluDgObj = ebCluManageDiskgroup(_eBoxCluCtrl, dgrpOpOptions)
                _cluDgObj.mSetDiskGroupOperationData(_dg_data)
                propList = ['rebalance_status']
                _rc = _cluDgObj.mClusterDgrpInfo(dgrpOpOptions, propList)
                if _rc != 0:
                    _detail_error = "Could not set new rebalance power for diskgroup " + _dg_name
                    _eBoxCluCtrl.mUpdateErrorObject(gElasticError['CELL_DG_REBAL_POWER_SET_FAILED'], _detail_error)
                    return self.mRecordError(gDiskgroupError['DgOperationError'], "*** " + _detail_error)
                    
                _dgData = _cluDgObj.mGetDiskGroupOperationData()
                _cellOperationData['rebalance_status'][_dg_name] = _dgData['DiskgroupInfo'][_dg_name]['rebalance_status']['status']
                
        ebLogDebug(json.dumps(_cellOperationData['rebalance_status'], indent=4, sort_keys=True))
        ebLogInfo("*** ebCluElasticCellManager:mFetchCellInfo <<<")
        return _rc
    # end mFetchCellInfo

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
    # end _mUpdateRequestData
    
    # Common method to log error code and error message
    def mRecordError(self, aErrorObject, aString=None):

        _cellOperationData = self.mGetCellOperationData()

        _cellOperationData["Status"] = "Fail"
        _cellOperationData["ErrorCode"] = aErrorObject[0]
        if aString is None:
            _cellOperationData["Log"] = aErrorObject[1]
        else:
            _cellOperationData["Log"] = aErrorObject[1] + aString

        ebLogError("*** %s\n" % (_cellOperationData["Log"]))

        _errorCode = int(_cellOperationData["ErrorCode"], 16)
        if _errorCode != 0:
            return ebError(_errorCode)
        return 0
    # end mRecordError

    def mPostReshapeValidation(self, aOptions):
        #
        # validate cluster integrity after reshape operation
        #
        ebLogInfo("Running Post Reshape Validation")
        _ebox = self.__eboxobj
        _pchecks = ebCluPreChecks(_ebox)
        _report_fatal_err = _ebox.mCheckConfigOption('report_fatal_err', 'True') 
        _pchecks.mCheckClusterIntegrity(True, _report_fatal_err)
    
    def validateKfodCmd(self):
        # 
        # validate kfod to see if griddisks can be listed
        #
        ebLogInfo("*** Running Kfod command validation")
        _eBoxCluCtrl = self.mGetEbox()
        _domU = self.getConnectableDomU()
        _cellConf = self.mGetUpdateConf()
        _cells = []
        for _cellinfo in _cellConf['cells']:
            _cells.append(_cellinfo['hostname'].split('.')[0])

        _path, _sid = _eBoxCluCtrl.mGetGridHome(_domU)
        _cmd = f"sh -c 'ORACLE_HOME={_path};export ORACLE_HOME;$ORACLE_HOME/bin/kfod.bin disks=all op=disks'"
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(_domU)
        _i, _o, _e = _node.mExecuteCmd(_cmd)
        if _node.mGetCmdExitStatus():
            _node.mDisconnect()
            return _e
        else:
            _out = _o.readlines()

        _node.mDisconnect()
        ebLogInfo("Following disks reported as part of kfod disks=all op=disks:")
        for _entry in _out:
            ebLogInfo(f"{_entry}")
        for cell in _cells:   
            if not any(cell in word for word in _out):
                return 1
        ebLogInfo("*** Completed Kfod command validation succesfully")
        return 0

    def getConnectableDomU(self) -> Optional[str]:
        """
        For some operations, exacloud needs to connect to a DomU in order to
        run some commands.
        But if one DomU is down, exacloud should try with another one and 
        verify if is connectable. If so, return it. Return None if all are down.
        """
        _ebox = self.mGetEbox()
        ebLogTrace("Detect first DomU available.")
        for _, _domU in _ebox.mReturnDom0DomUPair():
            _node = exaBoxNode(get_gcontext())
            if not _node.mIsConnectable(_domU):
                ebLogWarn(f"DomU {_domU} is not connectable. Trying others.")
                continue
            return _domU

        _errMsg = "Zero domUs connectable!"
        ebLogError(_errMsg)
        raise ExacloudRuntimeError(0x0802, 0xA, _errMsg)

class dgAOptions(object):
    def __init__(self, aEbCluElasticCellManager):
        self.jsonconf = {}
        self.configpath = aEbCluElasticCellManager.mGetOedaXmlPath()
            
# end of ebCluReshapeCell

