#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/ovm/cluzdlra.py /main/33 2025/09/11 04:18:16 naps Exp $
#
# cluzdlra.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      cluzdlra.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    naps        09/01/25 - Bug 38343791 - remove quorum disk dependency with
#                           asm scope security.
#    aararora    04/15/25 - Bug 37737222: Skip check for zdlra diskgroups for
#                           cpu scale up
#    naps        10/01/24 - Bug 37121709 - Change racktype for zdlra X11M.
#    naps        08/30/24 - Bug 36929267 - Detect zdlra env for cpu resize.
#    ririgoye    08/29/24 - Bug 36537230 - SET CORRECT VALUE FOR MAX STORAGE
#                           SIZE FOR ACFS01 DEPENDING ON STORAGE SHAPE
#    joysjose    08/09/24 - Bug 36922015 Correction of Undo timeout during
#                           zdlra wallet access
#    naps        08/09/24 - Bug 36908342 - X11M support.
#    prsshukl    04/23/24 - Bug 36539419 - Correctly logging the exit_status
#                           value of a command execution
#    asrigiri    02/23/24 - Bug 36235610 - PRECHECK WF FOR INFRAPATCHING IS
#                           STUCK FOR MORE THAN 10 HRS, NOT GETTING TIMED OUT
#    jesandov    01/25/24 - 36207260: Add function to read/write sysctl
#                           parameters
#    scoral      12/20/23 - Bug 36086915 - Make mGetGridHome polymorphic to
#                           accept the DomU FQDN or the connection object.
#    naps        09/19/23 - Bug 35742711 - X10M support for zdlra.
#    naps        08/23/23 - Bug 35689065 - Check for empty cell list before
#                           connecting to cell nodes.
#    aararora    07/06/23 - Bug 35539930: Remove dg id dependency for checking
#                           dg type.
#    naps        04/07/23 - Bug 35095608 - Support zdlra in mvm envs.
#    naps        02/13/23 - Bug 35074137 - Deduce rackDescription attr based on
#                           exacs version .
#    ndesanto    01/24/23 - Bug 35001886 - Fixed system model compare code to 
#                           work correctly with X10M systems
#    naps        01/06/23 - Bug 34884577 - Move HT for zdlra to prevmsetup
#                           step.
#    naps        10/10/22 - Bug 34631793 - Fortify fix.
#    naps        09/19/22 - Bug 34613739 - zdlra password should begin with
#                           alpha.
#    naps        09/13/22 - Bug 34538968 - Generate correct random password for
#                           zdlra to include both uppercase and lowercase
#                           chars.
#    naps        06/08/22 - Bug 34258477 - Hyperthreading logic for AMD
#                           systems.
#    naps        04/13/22 - Bug 34042937 - remove grid user login.
#    naps        04/22/22 - Bug 34082933 - asm instance password storage issue
#                           for zdlra.
#    dekuckre    22/06/21 - 33031729: Report None password if unable to get 
#                           wallet entry.
#    naps        07/02/21 - enable acfs volume for zdlra.
#    dekuckre    06/28/21 - XbranchMerge dekuckre_bug-33031729_new from
#                           st_ecs_20.4.1.2.0
#    dekuckre    16/06/21 - 32982101: Create - add wallet with root access. 
#    naps        06/16/21 - enable flag for zdlra type env.
#    naps        02/10/21 - Patch xml with zdlra attrs and enable
#                           hyperthreading during deleteservice.
#    naps        01/21/21 - zdlra support in exacloud.
#    naps        01/21/21 - Creation
#

import time
from exabox.log.LogMgr import ebLogDiag, ebLogWarn, ebLogInfo, ebLogDebug, ebLogError, ebLogVerbose, ebLogTrace
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.core.DBStore import ebGetDefaultDB
from exabox.ovm.hypervisorutils import getHVInstance, ebVgCompRegistry
from exabox.ovm.bmc import XMLProcessor
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure
from exabox.utils.common import mCompareModel
from exabox.config.Config import ebVmCmdCheckOptions
from exabox.core.Error import ExacloudRuntimeError
import random, string
import json

class exaBoxZdlra(object):

    def __init__(self, aCluCtrlObject):
        self.__ecc = aCluCtrlObject

    def ZdlraProvVal(self, aOptions=None):
        if aOptions:
            _jconf = aOptions.jsonconf
            if _jconf and 'zdlra' in _jconf and 'enabled' in _jconf['zdlra']:
                if _jconf['zdlra']['enabled'] == True:
                    ebLogInfo('*** ZdlraProvVal: Enabling ZDLRA from input json!')
                    return True
                else:
                    ebLogInfo('*** ZdlraProvVal: Disabling ZDLRA from input json!')
                    return False

        if  self.__ecc.mCheckConfigOption('zdlra_provisioning', 'True'):
            ebLogInfo('*** ZdlraProvVal: Enabling ZDLRA from exabox.conf!')
            return True

        return False

    def ZdlraHThreadVal(self, aOptions=None):
        if aOptions:
            _jconf = aOptions.jsonconf
            if _jconf and 'zdlra' in _jconf and 'hyperthreading' in _jconf['zdlra']:
                if _jconf['zdlra']['hyperthreading'] == True:
                    ebLogInfo('*** ZdlraHThreadVal: Enabling ZDLRA Hyper-Threading from input json!')
                    return True
                else:
                    ebLogInfo('*** ZdlraHThreadVal: Disabling ZDLRA Hyper-Threading from input json!')
                    return False

        if  self.__ecc.mCheckConfigOption('zdlra_hyperthreading', 'True'):
            ebLogInfo('*** ZdlraHThreadVal: Enabling ZDLRA Hyper-Threading from exabox.conf!')
            return True
        elif  self.__ecc.mCheckConfigOption('zdlra_hyperthreading', 'False'):
            ebLogInfo('*** ZdlraHThreadVal: Disabling ZDLRA Hyper-Threading from exabox.conf!')
            return False

        return True

    def mDeleteGD(self, aListOnly=False, aCell=None):
        _eBox = self.__ecc
        _rc = 0
        _cnb = 0
        ebLogInfo('*** zdlra mDeleteGD, aListOnly: {0}'.format(aListOnly))

        _cell_list = _eBox.mReturnCellNodes()
        for _cell in _cell_list:

            if not aCell or _cell == aCell:
                _node = exaBoxNode(get_gcontext())
                _node.mConnect(aHost=_cell)

                _found_dg = False
                _cnb += 1
                _cmd = "cellcli -e list griddisk | grep 'CATALOG\|DELTA'"
                _i, _o, _e = _node.mExecuteCmd(_cmd)
                _output = _o.readlines()
                if _output:
                    for _entry in _output:
                        _found_dg = True
                        if aListOnly:
                            ebLogWarn('GD: %s' % (_entry.strip()))

                    if not _found_dg:
                        ebLogInfo('*** NO GD_ENTRY FOR CELL: %s' % (_cell))
                        _rc += 1

                    if not aListOnly and _found_dg:
                        _cmd = "cellcli -e DROP GRIDDISK ALL PREFIX='CATALOG' FORCE"
                        _node.mExecuteCmdLog(_cmd)
                        _cmd = "cellcli -e DROP GRIDDISK ALL PREFIX='DELTA' FORCE"
                        _node.mExecuteCmdLog(_cmd)
                else:
                    ebLogInfo('*** No GD_ENTRY found on CELL: %s' % (_cell))
                    _rc += 1

                _node.mDisconnect()

        return 1 if (_rc == _cnb) else 0

    def mEnableDisableHT(self, aStatus, aOptions):
        _eBox = self.__ecc
        _status = aStatus
        _reboot_set = set()
        for _dom0, _ in _eBox.mReturnDom0DomUPair():
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_dom0)
            if self.mModifyHyperThreading(aOptions, aHost=_dom0, aStatus=_status):
                _reboot_set.add(_dom0)
            _node.mDisconnect()
        if _reboot_set:
            _eBox.mRebootNodesIfNoVMExists(_reboot_set, "dom0")

    def mModifyHyperThreading(self, aOptions, aHost=None, aStatus=None):

       _host = aHost
       _reboot = False
       _eBox = self.__ecc
       _isAmd = True
       _uuid = _eBox.mGetUUID()
       _tmp_file = f"/tmp/bios-{_uuid}.xml"
       if aStatus:
           _nstatus = aStatus
       else:
           _val = _eBox.IsZdlraHThread()
           if _val == True:
               _nstatus = "Enabled"
           else:
               _nstatus = "Disabled"

       _node = exaBoxNode(get_gcontext())
       _node.mConnect(aHost=_host)

       _in, _o, _err = _node.mExecuteCmd("/usr/bin/lscpu | grep 'Model name' | grep -i 'Intel'")
       _rc = _node.mGetCmdExitStatus()
       if _rc == 0:
           ebLogInfo('***mModifyHyperThreading: Intel based cpu ')
           _isAmd = False
       else:
           ebLogInfo('***mModifyHyperThreading: AMD based cpu ')

       if _isAmd:
           if _nstatus == "Disabled":
               _nstatus = "Disable"
           else:
               _nstatus = "Auto"
           _in, _out, _err = _node.mExecuteCmd("/usr/sbin/ubiosconfig export all -x " +_tmp_file + " --expert_mode -y")
           _rc = _node.mGetCmdExitStatus()
           if _rc != 0:
               ebLogError('***mModifyHyperThreading: Unable to export bios params using ubiosconfig !')
               _node.mDisconnect()
               return _reboot

           _, _o, _ = _node.mExecuteCmd("/bin/grep -oP '(?<=<SMT_Control>).*?(?=<\/SMT_Control)' " +_tmp_file)
           _rc = _node.mGetCmdExitStatus()
           if _rc == 0 and _o:
               _out = _o.readlines()
               if _out and _out[0].strip() == _nstatus:
                   ebLogInfo('***mModifyHyperThreading: Hyper-threading already: ' + _nstatus)
               else:
                   ebLogInfo('***mModifyHyperThreading: Changing Hyper-threading to: ' + _nstatus + ' state')
                   if _nstatus == "Auto":
                       _node.mExecuteCmd("/bin/sed -i 's/<SMT_Control>Disable/<SMT_Control>Auto/' " +_tmp_file)
                   elif _nstatus == "Disable":
                       _node.mExecuteCmd("/bin/sed -i 's/<SMT_Control>Auto/<SMT_Control>Disable/' " +_tmp_file)
                   _reboot = True

       else:
           _in, _out, _err = _node.mExecuteCmd("/usr/sbin/ubiosconfig export all -x " +_tmp_file + " --expert_mode -y")
           _, _o, _ = _node.mExecuteCmd("/bin/grep -oP '(?<=<Hyper-threading>).*?(?=<\/Hyper-threading)' " +_tmp_file)
           _rc = _node.mGetCmdExitStatus()
           if _rc == 0 and _o:
               _out = _o.readlines()
               if _out and _out[0].strip() == _nstatus:
                   ebLogInfo('***mModifyHyperThreading: Hyper-threading already ' + _nstatus)
               else:
                   ebLogInfo('***mModifyHyperThreading: Changing Hyper-threading to ' + _nstatus + ' state')
                   if _nstatus == "Enabled":
                       _node.mExecuteCmd("/bin/sed -i 's/<Hyper-threading>Disabled/<Hyper-threading>Enabled/' "+_tmp_file)
                   elif _nstatus == "Disabled":
                       _node.mExecuteCmd("/bin/sed -i 's/<Hyper-threading>Enabled/<Hyper-threading>Disabled/' "+_tmp_file)
                   _reboot = True

           _, _o, _ = _node.mExecuteCmd("/bin/grep -oP '(?<=<Hyper-Threading_ALL>).*?(?=<\/Hyper-Threading_ALL)' "+_tmp_file)
           _rc = _node.mGetCmdExitStatus()
           if _rc == 0 and _o:
               _out = _o.readlines()
               if _out and _out[0].strip() == _nstatus:
                   ebLogInfo('***mModifyHyperThreading: Hyper-Threading_ALL already ' + _nstatus)
               else:
                   ebLogInfo('***mModifyHyperThreading: Changing Hyper-Threading_ALL to ' + _nstatus + ' state')
                   if _nstatus == "Enabled":
                       _node.mExecuteCmd("/bin/sed -i 's/<Hyper-Threading_ALL>Disabled/<Hyper-Threading_ALL>Enabled/' "+_tmp_file)
                   elif _nstatus == "Disabled":
                       _node.mExecuteCmd("/bin/sed -i 's/<Hyper-Threading_ALL>Enabled/<Hyper-Threading_ALL>Disabled/' "+_tmp_file)
                   _reboot = True

       if _reboot:
           _node.mExecuteCmd("/usr/sbin/ubiosconfig import all -x " +_tmp_file + " --expert_mode -y")
       _node.mExecuteCmd("/bin/rm -f " +_tmp_file)      
       _node.mDisconnect()

       return _reboot

    def mPatchXmlZdlra(self):
        _eBox = self.__ecc
        _patchconfig = _eBox.mGetPatchConfig()
        _config = XMLProcessor(_patchconfig)
        _tags = _config.find('./esRacks/esRack/rackDescription')
        ebLogInfo('*** mPatchXmlZdlra: Old rackDescription is ' + _tags.text)
        if 'zdlra' in _tags.text.lower():
            ebLogInfo('*** mPatchXmlZdlra: xml already patched with zdlra attrs !')
            return
        else:
            _rack_descr = _eBox.mCheckConfigOption('zdlra_rack_descr')
            if not _rack_descr:
                _rack_descr = _tags.text.split()
                _rack_descr = list(_rack_descr)
                #Lets insert 'ZDLRA' in the string.
                #Final rackDescription eg : "X8M-2 ZDLRA Elastic Rack HC 14TB"
                if 'X11M' in _rack_descr:
                    _rack_descr.remove("X11M")
                    _rack_descr.insert(0, "ZDLRA")
                    _rack_descr.insert(1, "RA23")
                else:
                    _rack_descr.insert(1, "ZDLRA")
                _rack_descr = ' '.join(_rack_descr)
                ebLogInfo(f'*** mPatchXmlZdlra: New rackDescription is {_rack_descr}')
            _tags.text = _rack_descr

        _tags = _config.find('./esRacks/esRack/rackType')
        ebLogInfo('*** mPatchXmlZdlra: Old rackType is ' + _tags.text)
        _rack_type = '1037'
        if "X8M" in _rack_descr:
            _rack_type = _eBox.mCheckConfigOption('zdlra_rack_type_x8m')
            if not _rack_type:
                _rack_type = '1037'
        elif "X9M" in _rack_descr:
            _rack_type = _eBox.mCheckConfigOption('zdlra_rack_type_x9m')
            if not _rack_type:
                _rack_type = '1147'
        elif "X10M" in _rack_descr:
            _rack_type = _eBox.mCheckConfigOption('zdlra_rack_type_x10m')
            if not _rack_type:
                _rack_type = '1210'
        elif "RA23" in _rack_descr:
            _rack_type = _eBox.mCheckConfigOption('zdlra_rack_type_x11m')
            if not _rack_type:
                _rack_type = '1216'

        _tags.text = _rack_type

        _tags = _config.findall('./storage/diskGroups/diskGroup')
        for x in _tags:
            for _ret in x.iter('diskGroupName'):
                ebLogInfo('*** mPatchXmlZdlra: Old diskGroupName is ' + _ret.text)
                if 'DATA' in _ret.text:
                    _ret.text = 'CATALOG'
                elif 'RECO' in _ret.text:
                    _ret.text = 'DELTA'
        for x in _tags:
            for _ret in x.iter('diskGroupType'):
                ebLogInfo('*** mPatchXmlZdlra: Old diskGroupType is ' + _ret.text)
                if 'DATA' in _ret.text:
                    _ret.text = 'CATALOG'
                elif 'RECO' in _ret.text:
                    _ret.text = 'DELTA'

        _config.writeXml(_patchconfig)
        ebLogInfo('*** mPatchXmlZdlra: Updated file ' + _patchconfig)


    def mPatchClusterZdlraDisks(self, aStorageObj, aOptions):
        _eBox = self.__ecc
        _storage = aStorageObj
        _options =  _eBox.mGetArgsOptions()

        _cluster = _eBox.mGetClusters().mGetCluster()
        _cludgroups = _cluster.mGetCluDiskGroups()
        _cludgroup_types = []
        for _cludg_id in _cludgroups:
            _dg = _eBox.mGetStorage().mGetDiskGroupConfig(_cludg_id)
            _cludgroup_types.append(_dg.mGetDiskGroupType().lower())
        if 'catalog' in _cludgroup_types:
            _catalog_id = 'catalog'
            _delta_id = 'delta'
        else:
            '''
            lets use this hack, untill oedacli supports zdlra types disks!
            we will use data section for catalog, and reco section for delta, to calculate disk size distribution, redundancy, ocrVote.. etc.
            But the actual names of CATALOG and DELTA will be replaced finally via mPatchXmlZdlra()
            '''
            _catalog_id = 'data'
            _delta_id = 'reco'

        #
        # Retrieve number of localDisk in cell
        #
        _cell_list = _eBox.mReturnCellNodes()
        _cell_name = list(_cell_list.keys())[0]  # Pick first cell
        _mac_cfg = _eBox.mGetMachines().mGetMachineConfig(_cell_name)
        _ldisk_cnt = _mac_cfg.mGetLocaldisksCount()

        _catalog_size = 0
        _delta_size = 0
        _catalog_slice = 0
        _delta_slice = 0
        _slice = 0
        _catalog_dg_id = None
        _delta_dg_id = None
        for _dgid in _cludgroups:
            ebLogInfo('*** _dgid : ' + _dgid)
            _dgConfig = _storage.mGetDiskGroupConfig(_dgid)
            _dg_type = _dgConfig.mGetDiskGroupType().lower()

            _slice_sz = _dgConfig.mGetSliceSize()
            _dgroup_sz = _dgConfig.mGetDiskGroupSize()

            if _dg_type.find(_catalog_id) != -1:
                _catalog_size = int(_dgroup_sz[:-1])
                try:
                    _catalog_slice = int(_slice_sz[:-1])
                except:
                    _catalog_slice = 0
                _catalog_dg_id = _dgid
            elif _dg_type.find(_delta_id) != -1:
                _delta_size = int(_dgroup_sz[:-1])
                try:
                    _delta_slice = int(_slice_sz[:-1])
                except:
                    _delta_slice = 0
                _delta_dg_id = _dgid

        # Enable ASM Scoped Security if conf option is on.
        if _eBox.mGetEnableAsmss() and _eBox.mGetEnableAsmss().lower() == "true":
            ebLogInfo('*** ASM Scoped Security enabled')
            _eBox.mGetClusters().mGetCluster().mSetCluAsmScopedSecurity('true')
        else:
            ebLogInfo('*** ASM Scoped Security disabled')
            _eBox.mGetClusters().mGetCluster().mSetCluAsmScopedSecurity('false')

        #Override redundancy as appropriate

        if _catalog_dg_id is not None:
            _catalogConfig = _storage.mGetDiskGroupConfig(_catalog_dg_id)
            if _catalogConfig.mGetDgRedundancy() != "HIGH":
                _catalogConfig.mSetDgRedundancy("HIGH")
                ebLogInfo("Setting CATALOG diskgroup (%s) redundancy as HIGH" % _catalog_dg_id)

        if _delta_dg_id is not None:
            _deltaConfig = _storage.mGetDiskGroupConfig(_delta_dg_id)
            if _deltaConfig.mGetDgRedundancy() != "NORMAL":
                _deltaConfig.mSetDgRedundancy("NORMAL")
                ebLogInfo("Setting DELTA diskgroup (%s) redundancy as NORMAL" % _delta_dg_id)


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

        _total_dg = _catalog_size + _delta_size

        if _eBox.mGetDbStorage() is not None:
            if _eBox.mCheckConfigOption('min_db_storage') is not None:
                _min_dbstorage = int(_eBox.mCheckConfigOption('min_db_storage')[:-2])
            else:
                _min_dbstorage = 2048

            if int(_eBox.mGetDbStorage()[:-1]) < _min_dbstorage:
                _total_dg = _min_dbstorage
            else:
                _total_dg = int(_eBox.mGetDbStorage()[:-1])

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


        # start of disksize & slicesize calculations
        ebLogInfo('Current DG Setup: CATALOG: ' + str(_catalog_slice) + 'G TOTAL: ' + str(_catalog_size))
        ebLogInfo('                  DELTA: ' + str(_delta_slice) + 'G TOTAL: ' + str(_delta_size))

        _catalogConfig = _storage.mGetDiskGroupConfig(_catalog_dg_id)
        _deltaConfig = _storage.mGetDiskGroupConfig(_delta_dg_id)

        if _disksize >= 22:
            #catalog and delta ratio for RA23 family
            _delta_share = _eBox.mCheckConfigOption('zdlra_delta_ratio_22TB')
            if not _delta_share:
                _delta_share = 98
            _catalog_share = _eBox.mCheckConfigOption('zdlra_catalog_ratio_22TB')
            if not _catalog_share:
                _catalog_share = 2
        else:
            _delta_share = _eBox.mCheckConfigOption('zdlra_delta_ratio_below22TB')
            if not _delta_share:
                _delta_share = 97
            _catalog_share = _eBox.mCheckConfigOption('zdlra_catalog_ratio_below22TB')
            if not _catalog_share:
                _catalog_share = 3

        if not _eBox.SharedEnv() or _eBox.mCheckConfigOption('zdlra_use_svm_config', 'True'):
            ebLogInfo('Single VM config')
            (_catalog_disk_size, _delta_disk_size, _catalog_disk_slice, _delta_disk_slice) = _storage.mGetDgVolsize(_disknb, _disksize, 0, _catalog_share,
                                                                                                    _delta_share, False, 0)
        else:
            ebLogInfo('Multi VM config')
            (_catalog_disk_size, _delta_disk_size, _catalog_disk_slice, _delta_disk_slice) = _storage.mGetDgVolsize(_disknb, _disksize, 0, _catalog_share,
                                                                                                    _delta_share, _eBox.SharedEnv(), _total_dg)

        ebLogInfo(f'{_catalog_share}%-{_delta_share}% DG Setup: CATALOG:  {_catalog_disk_slice} G TOTAL: {_catalog_disk_size}')
        ebLogInfo('                   DELTA: ' + str(_delta_disk_slice) + 'G TOTAL: ' + str(_delta_disk_size))
        #In oedacli, we can only set either slicesize or diskgroupsize. We cannot set both.
        #In mDiskGroupCallback in ebCommandGenerator.py, if both are set, it will pop slicesize !
        #i.e, if we pass both slicesize and diskgroupsize, diskgroupsize will get precedence.
        #But, there is a bug in oedacli, where it does not set a proper slicesize, when diskgroupsize it set!
        #i.e, slicesize is calculated to be smaller, and we underutilize celldisk space!. There is a difference of ~4TB per disk !
        #otoh, if slicesize it set, full disksize is getting used.
        #Hence, as a w/a let us set only slicesize for now, untill we figure out rootcause in oedacli.
        #It is sufficient to set only slicesize, oeda will calculate the diskgroupsize on its own !
        _catalogConfig.mSetSliceSize(_catalog_disk_slice)
        _catalogConfig.mSetDiskGroupType("catalog")
        _deltaConfig.mSetSliceSize(_delta_disk_slice)
        _deltaConfig.mSetDiskGroupType("delta")

        if _eBox.mGetEnableQuorum():
            ebLogInfo('*** ENABLING setting OCR Voting and QuorumDisk for CATALOG & DELTA DGs')
            _catalogConfig.mSetOCRVote('true')
            if _catalogConfig.mGetDgRedundancy() == "NORMAL":
                _catalogConfig.mSetQuorumDisk('false')
            else:
                _catalogConfig.mSetQuorumDisk('true')

            if _deltaConfig.mGetDgRedundancy() == "NORMAL":
                _deltaConfig.mSetQuorumDisk('false')
            else:
                _deltaConfig.mSetQuorumDisk('true')

        else:
            ebLogInfo('*** Quorum disabled OCR setting to Data and Quorum unset from Catalog/Delta')
            _catalogConfig.mSetOCRVote('true')
            _catalogConfig.mSetQuorumDisk('false')
            _deltaConfig.mSetQuorumDisk('false')

        _exadata_cell_model = _eBox.mGetExadataCellModel()
        _cutOff_model = 'X7'
        if _eBox.mGetCmd() not in ['elastic_info'] \
            and mCompareModel(_exadata_cell_model, _cutOff_model) >= 0:

            _avsize = _eBox.mCheckConfigOption('zdlra_acfs_size')
            if _avsize:
                _avsize = int(_avsize)
                ebLogInfo("acfs size set in config: %d" %_avsize)
            else:
                # calculate the acfs vol size as a factor of disksize
                # for 4TB disk -> 320GB of ACFS size per cell
                _avsize = _disksize * 40

                if not _eBox.SharedEnv() or _eBox.mCheckConfigOption('zdlra_use_svm_config', 'True'):
                    _avsize = _disksize * 80

                _modified_data_dg_size = _catalogConfig.mGetDiskGroupSize()
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
            _catalogConfig.mSetAcfsVolumeName(_acfsvolname)
            _catalogConfig.mSetAcfsVolumeSize(_avsize)
            _catalogConfig.mSetAcfsMountPath(_acfsmountpath)

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

    def mGetGridHome(self,aDomU):
        _node = aDomU
        _disconnect = False
        if isinstance(_node, str):
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=aDomU)
            _disconnect = True

        _cmd = "/bin/cat /etc/oratab | grep '^+ASM.*' | cut -f 2 -d ':'"
        _i, _o, _e = _node.mExecuteCmd(f'/bin/su - grid -c \'{_cmd}\'')
        _out = _o.readlines()
        if not _out or len(_out) == 0:
            ebLogWarn('*** Gridhome entry not found for grid')
            return "", ""
        _path = _out[0].strip()

        _cmd = "/bin/cat /etc/oratab | grep '^+ASM.*' | cut -f 1 -d ':'"
        _i, _o, _e = _node.mExecuteCmd(f'/bin/su - grid -c \'{_cmd}\'')
        _out = _o.readlines()
        if not _out or len(_out) == 0:
            ebLogWarn('*** ASM entry not found for grid')
            return "", ""
        _sid = _out[0].strip()

        ebLogTrace('mGetGridHome:: path:' + _path + ' sid:' + _sid)
        if _disconnect:
            _node.mDisconnect()
        return _path, _sid

    def mGetWalletInfo(self):
        _eBox = self.__ecc

        _oracle_home = _eBox.mGetClusters().mGetCluster().mGetCluHome()
        _key_store = _oracle_home + "/bin/mkstore"
        _wallet_loc = _oracle_home + "/exa_zdlra_wallet"
        return _key_store, _wallet_loc


    def mCreateWallet(self):
        _eBox = self.__ecc
        _key_store, _wallet_loc = self.mGetWalletInfo()

        _domu_list = [ _domu for _ , _domu in _eBox.mReturnDom0DomUPair()]
        _node = exaBoxNode(get_gcontext())

        for _domu in _domu_list:
            _node.mConnect(aHost=_domu)
            if _node.mFileExists(_wallet_loc):
                ebLogInfo('***Wallet already exists for zdlra !')
            else:
                ebLogInfo('*** Creating an auto-login wallet in %s for zdlra' %_wallet_loc)
                _node.mExecuteCmd(_key_store + ' -wrl ' + _wallet_loc + ' -createALO')
                _node.mExecuteCmdLog("chown -R grid:oinstall " + _wallet_loc + "*")
            _node.mDisconnect()

    def mDelWalletEntry(self, aWalletKey):
        _eBox = self.__ecc
        _wallet_key = aWalletKey
        _key_store, _wallet_loc = self.mGetWalletInfo()

        _domu_list = [ _domu for _ , _domu in _eBox.mReturnDom0DomUPair()]
        _node = exaBoxNode(get_gcontext())

        for _domu in _domu_list:
            _node.mConnect(aHost=_domu)
            ebLogInfo('***Deleting old entry in zdlra wallet !')
            _node.mExecuteCmd('{0} -wrl {1} -deleteEntry {2}'.format(_key_store, _wallet_loc, _wallet_key))
            _node.mDisconnect()

    def mAddWalletEntry(self, aWalletKey, aPasswd):
        _eBox = self.__ecc
        _key_store, _wallet_loc = self.mGetWalletInfo()
        _passwd = aPasswd
        _wallet_key = aWalletKey

        _domu_list = [ _domu for _ , _domu in _eBox.mReturnDom0DomUPair()]
        _node = exaBoxNode(get_gcontext())

        for _domu in _domu_list:
            _node.mConnect(aHost=_domu)

            _cmd = f'{_key_store} -wrl {_wallet_loc} -createEntry "{_wallet_key}" "{_passwd}"'
            _node.mExecuteCmdLog(_cmd)
            _ret = _node.mGetCmdExitStatus()
            ebLogInfo("*** zdlra mAddWalletEntry ret: {0} ***".format(_ret))

            _node.mDisconnect()

        return _wallet_key


    def mGetWalletViewEntry(self, aWalletKey, aDomU=None):
        _eBox = self.__ecc
        _wallet_key = aWalletKey
        _passwd = None
        _key_store, _wallet_loc = self.mGetWalletInfo()

        if aDomU:
            _domu = aDomU
        else:
            _domu_list = [ _domu for _ , _domu in _eBox.mReturnDom0DomUPair()]
            _domu = _domu_list[0]

        try:
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_domu)
            _cmd_timeout = 300
            _cmd  = '{0} -wrl {1} -viewEntry {2} | grep {2}'.format(_key_store, _wallet_loc, _wallet_key)
            _, _o, _e = _node.mExecuteCmd(_cmd, aTimeout=_cmd_timeout)
            _ret = _node.mGetCmdExitStatus()
            if _ret == 0 and _o:
                _out = _o.readlines()
                if _out and len(_out):
                    _out = _out[0].strip()
                    if '=' in _out:
                        _passwd = _out.split('=')[1].strip()

            _node.mDisconnect()

        except:
            ebLogError("Failed to get password from ZDLRA wallet")

        return _passwd

    def mUpdateHugePages(self, aOptions=None):
        _eBox = self.__ecc
        _hugepage = None
        if aOptions and aOptions.jsonconf:
            if 'hugepage_size' in list(aOptions.jsonconf.keys()):
                _hugepage = aOptions.jsonconf['hugepage_size']
        if not _hugepage:
            _hugepage = self.__ecc.mCheckConfigOption('hugepage_size')
        if not _hugepage:
            _hugepage = '34500'

        _hugepage = int(_hugepage)

        for _dom0, _domu in _eBox.mReturnDom0DomUPair():

            _hv = getHVInstance(_dom0)
            _currmaxvmem = _hv.mGetVMMemory(_domu, 'MAX_MEM')

            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_domu)

            _hugepagesize = None
            _cmd = "/bin/grep Hugepagesize /proc/meminfo | awk '{print$2/1024}'"
            _in, _out, _err = _node.mExecuteCmd(_cmd)
            if _out:
                _out = _out.readlines()
                _hugepagesize = _out[0].strip()
                ebLogInfo("Hugepagesize from meminfo: {0}".format(_hugepagesize))
            if not _hugepagesize:
                #Default of 2MB Hugepagesize
                _hugepagesize = "2"
            ebLogInfo("System mem is : {0}".format(_currmaxvmem))
            _hugepagesize = int(_hugepagesize)
            if (_hugepagesize*_hugepage > _currmaxvmem*0.4):
                ebLogWarn("Hugepage memory {0} greater than 40% of system memory of {1}".format(_hugepagesize*_hugepage, _currmaxvmem))
                _hugepage = int((_currmaxvmem*0.4)/_hugepagesize)
                ebLogInfo("Setting hugepage to 40% memory : {0}".format(_hugepage))

            _eBox.mSetSysCtlConfigValue(_node, "vm.nr_hugepages", _hugepage, aRaiseException=False)

            _node.mDisconnect()

    def mGenerate_random_password(self):
        #This password will be used for zdlra to update nonroot and cellcli cloud user password.
        #password should have at least one digit, one lowercase letter,one uppercase letter and a special character !

        #string.ascii_letters will include both uppercase and lowercase chars
        random_chars = string.ascii_letters + string.digits
        #Lets begin and end with a char
        _pwd_begin = ''.join(random.sample(string.ascii_letters, 1))
        _pwd_end = ''.join(random.sample(string.ascii_letters, 1))

        #This is midsection of the password
        #atleast 1 lowercase
        _mid = ''.join(random.sample(string.ascii_lowercase, 1))
        #atleast 1 uppercase
        _mid += ''.join(random.sample(string.ascii_uppercase, 1))
        #atleast 1 digit
        _mid += ''.join(random.sample(string.digits, 1))
        #There could be a case where some special characters are disallowed. Hence let us use just '_', which is also same previous logic !
        _mid += '_'
        #Fill in other characters randomly
        _mid += ''.join(random.sample(random_chars, 3))
        _mid_list = list(_mid)
        #Shuffle them again
        random.SystemRandom().shuffle(_mid_list)
        _pwd_mid = ''.join(_mid_list)

        #Now build full password using begining, midsection and ending !
        _pwd = _pwd_begin + _pwd_mid + _pwd_end
        return _pwd

    def mCheckZdlraInEnv(self):
        _eBox = self.__ecc
        _zdlra_flag = False
        _options = _eBox.mGetArgsOptions()

        racks = _eBox.mGetEsracks()
        if racks:
            ebLogInfo('*** mCheckZdlraInEnv: rackDescription is {}'.format(racks.mDumpEsRackDesc()))
            if 'zdlra' in racks.mDumpEsRackDesc().lower():
                ebLogInfo('*** mCheckZdlraInEnv: xml patched for zdlra. Enabling zdlra config !')
                return True

        # If it is a zdlra environment - we would know it is a zdlra environment from xml check above
        # For ExaCS - we can skip the below check on cells for zdlra
        if _options and _eBox.mGetCmd() == "vm_cmd" and _options.vmcmd and \
            ebVmCmdCheckOptions(_options.vmcmd, ['skip_zdlra_cell_check']):
            return False

        _cell_list = _eBox.mReturnCellNodes()
        if _cell_list is None or _cell_list == {}:
            ebLogWarn('mCheckZdlraInEnv: Cell list is empty!')
            return False

        _cell_name = list(_cell_list.keys())[0]
        _node = exaBoxNode(get_gcontext())
        # Below condition is to reduce the number of retries to connect to the cell node
        # and fail early
        if not _node.mIsConnectable(aHost=_cell_name):
            raise ExacloudRuntimeError(aErrorMsg=f"The cell node {_cell_name} is not connectable. Please correct "\
                " connectivity to the cell and try again.")
        _node.mConnect(aHost=_cell_name)
        _cmd_timeout = int(_eBox.mCheckConfigOption('zdlra_cellcli_list_griddisk_timeout_in_seconds'))

        _cmdstr = "/opt/oracle/cell/cellsrv/bin/cellcli -e list griddisk | /bin/grep 'CATALOG'"
        _i, _o, _e = _node.mExecuteCmd(_cmdstr, aTimeout=_cmd_timeout)
        _exit_status = _node.mGetCmdExitStatus()
        if _exit_status == 0:
            ebLogInfo('*** mCheckZdlraInEnv: Found CATALOG disk in cell!')
        else:
            ebLogInfo(f'*** mCheckZdlraInEnv: Non-Zdlra env detected!')
            return False

        _cmdstr = "/opt/oracle/cell/cellsrv/bin/cellcli -e list griddisk | /bin/grep 'DELTA'"
        _i, _o, _e = _node.mExecuteCmd(_cmdstr, aTimeout=_cmd_timeout)
        if _node.mGetCmdExitStatus() == 0:
            ebLogInfo('*** mCheckZdlraInEnv: Found DELTA disk in cell!')
            _zdlra_flag = True

        _node.mDisconnect()
        return _zdlra_flag

