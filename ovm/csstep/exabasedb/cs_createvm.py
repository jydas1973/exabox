#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/csstep/exabasedb/cs_createvm.py /main/5 2026/01/07 22:19:36 zpallare Exp $
#
# cs_createvm.py
#
# Copyright (c) 2025, 2026, Oracle and/or its affiliates.
#
#    NAME
#      cs_createvm.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    scoral      12/22/25 - Re-added cleanup_bonding_if_enabled for cleaning
#                           monitor_admin.json entry in non-eth0 envs.
#    prsshukl    11/19/25 - Creation
#

import exabox.ovm.clubonding as clubonding
from exabox.ovm.csstep.cs_base import CSBase
from exabox.ovm.csstep.cs_util import csUtil
from exabox.ovm.clumisc import ebCluPreChecks
from exabox.log.LogMgr import ebLogInfo, ebLogTrace, ebLogError
from exabox.ovm.bom_manager import ImageBOM
from exabox.ovm.cluexascale import ebCluExaScale
from exabox.ovm.utils.clu_utils import ebCluUtils
from exabox.utils.node import connect_to_host
from exabox.core.Context import get_gcontext                                                                                                                                                                                                  

# This class implements doExecute and undoExecute functions
# for the ESTP_CREATE_VM step of create service
# This class primarily invokes OEDA do/undo create VM step
class csCreateVM(CSBase):
    def __init__(self):
        self.step = 'ESTP_CREATE_VM'

    def doExecute(self, aExaBoxCluCtrlObj, aOptions, aStepList):
        ebLogTrace('csCreateVM: Entering doExecute')
        _ebox = aExaBoxCluCtrlObj
        _csu = csUtil()
        imageBom = ImageBOM(_ebox)
        _pchecks = ebCluPreChecks(_ebox)
        _exascale = ebCluExaScale(_ebox)

        if not imageBom.mIsSubStepExecuted(self.step, "CONFIGURE_DOMU_PASSWORD_OEDA"):
            if _ebox.IsZdlraProv():
                # Update non root password (es.properties) in ZDLRA env from wallet  
                _password = _ebox.mGetZDLRA().mGenerate_random_password()
                _ebox.mUpdateOedaUserPswd(_ebox.mGetOedaPath(), "non-root", _password) 

        self.mCreateVM(_ebox, aOptions, aStepList)

        # 38368497: Add remote fs target to multi-user-target.wants to ensure
        # u01, u02 is mounted as part of reboot of VM.
        for _, _domU in _ebox.mReturnDom0DomUPair():
            with connect_to_host(_domU, get_gcontext(), "root") as _node:
                _node.mExecuteCmd('/usr/bin/systemctl enable remote-fs.target')

        ebLogTrace('csCreateVM: Completed doExecute Successfully')


    def undoExecute(self, aExaBoxCluCtrlObj, aOptions, aStepList):

        ebLogInfo('csCreateVM: Entering undoExecute')
        _ebox = aExaBoxCluCtrlObj 

        if _ebox.mGetCmd() == 'deleteservice':
            _exascale = ebCluExaScale(_ebox)                                                                                                                                                                         
            _json = {}
            for _dom0, _domU in _ebox.mReturnDom0DomUPair():        
                for _dev in ['u01', 'u02']:
                    ebLogInfo(f"Checking if any snapshots need to be unmounted as part of delete service")
                    _lvm, _snap_dev = _exascale.mGetLVDev(_dom0, _domU, _dev)
                    if not _snap_dev or not _lvm:
                        ebLogInfo(f"No {_dev} snapshot mounted for the VM {_domU}. Nothing to unmount")
                        continue
                    _json['snapshot_device_name'] = _snap_dev 
                    _json['lvm'] = _lvm
                    _json['dom0'] = _dom0
                    _json['vm'] = _domU
                    ebLogInfo(f"Performing unmount of snapshot for {_json}")
                    _exascale.mUnmountVolume(aOptions, _json) 

        self.mDeleteVM(_ebox, aOptions, aStepList)

        # Deconfigure bondmonitor.
        clubonding.cleanup_bonding_if_enabled(
            _ebox, payload=aOptions.jsonconf, cleanup_bridge=False,
            cleanup_monitor=True)

        ebLogInfo('csCreateVM: Completed undoExecute Successfully')
