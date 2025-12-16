#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/ovm/csstep/exascale/cs_createvm.py /main/5 2025/10/31 17:31:05 bhpati Exp $
#
# cs_createvm.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      cs_createvm.py - Create Service CREATE VM
# 
#   FUNCTION:
#      Implements the Create VM step for exascale create service execution 
#
#    NOTES
#      Invoked from cs_driver.py
#
#    EXTERNAL INTERFACES:
#      csCreateVM     ESTP_CREATE_VM
#
#    INTERNAL CLASSES:
#
#    MODIFIED   (MM/DD/YY)
#    bhpati      10/20/25 - Bug 38490905 - OCI: ExaDB-D on exascale
#                           provisioning fails if ICMP ingress is not open on
#                           client network
#    pbellary    06/21/24 - ENH 36690743 - EXACLOUD: IMPLEMENT OEDA STEPS FOR EXASCALE CREATE SERVICE
#    pbellary    06/14/24 - ENH 36721696 - IMPLEMENT DELETE SERVICE STEPS FOR EXASCALE SERVICE
#    pbellary    06/06/24 - ENH 36603820 - REFACTOR CREATE SERVICE FLOW FOR ASM/XS/EXADB-XS
#    pbellary    06/06/24 - Creation
#
import exabox.ovm.clubonding as clubonding
from exabox.ovm.csstep.cs_base import CSBase
from exabox.ovm.csstep.cs_util import csUtil
from exabox.ovm.clumisc import ebCluPreChecks
from exabox.log.LogMgr import ebLogInfo, ebLogTrace

# This class implements doExecute and undoExecute functions
# for the ESTP_CREATE_VM step of create service
# This class primarily invokes OEDA do/undo create VM step
class csCreateVM(CSBase):
    def __init__(self):
        self.step = 'ESTP_CREATE_VM'

    def doExecute(self, aCluCtrlObj, aOptions, aStepList):
        ebLogTrace('csCreateVM: Entering doExecute')
        _ebox = aCluCtrlObj
        _csu = csUtil()
        _pchecks = ebCluPreChecks(_ebox)

        self.mCreateVM(_ebox, aOptions, aStepList)

        #
        # Attach virtio serial device to KVM Guest.
        # Update the chasis information to GuestVM. 
        #
        if _ebox.mIsKVM():
            _ebox.mUpdateVmetrics('vmexacs_kvm')
            _ebox.mStartVMExacsService(aOptions, aCheckCrsAsm=False)

        # Run ntp and dns updation as oeda create vm will remove these entries
        ebLogInfo('csCreateVM: Entering mAddMissingNtpDnsIps')
        if _ebox.mIsKVM() and (_csu.mReturnCountofVm(_ebox) == 1):
            _dom0s, _, _cells, _ = _ebox.mReturnAllClusterHosts()
            _hostList = _dom0s + _cells
            _pchecks.mAddMissingNtpDnsIps(_hostList)

        ebLogTrace('csCreateVM: Completed doExecute Successfully')

    def undoExecute(self, aCluCtrlObj, aOptions, aStepList):
        ebLogTrace('csCreateVM: Entering undoExecute')
        _ebox = aCluCtrlObj

        self.mDeleteVM(_ebox, aOptions, aStepList)

        # Deconfigure bondmonitor.
        clubonding.cleanup_bonding_if_enabled(
            _ebox, payload=aOptions.jsonconf, cleanup_bridge=False,
            cleanup_monitor=True)

        ebLogTrace('csCreateVM: Completed undoExecute Successfully')
