#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/csstep/exabasedb/cs_prevmchecks.py /main/1 2025/11/25 05:03:58 prsshukl Exp $
#
# cs_prevmchecks.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      cs_prevmchecks.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    prsshukl    11/19/25 - Creation
#

import time

from exabox.core.Context import get_gcontext
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogTrace
import exabox.ovm.clubonding as clubonding
from exabox.ovm.clumisc import ebCluPreChecks
from exabox.ovm.csstep.cs_constants import csConstants
from exabox.ovm.csstep.cs_base import CSBase
from exabox.ovm.csstep.cs_util import csUtil
from exabox.ovm.cluhealth import ebCluHealthCheck
from exabox.ovm.clustorage import ebCluStorageConfig
from exabox.healthcheck.cluexachk import ebCluExachk
from exabox.utils.node import connect_to_host, node_exec_cmd_check
from exabox.ovm.bom_manager import ImageBOM
from exabox.ovm.clunetworkvalidations import ebNetworkValidations
from exabox.ovm.utils.clu_utils import ebCluUtils
from exabox.ovm.cluexascale import ebCluExaScale

# This class implements doExecute and undoExecute functions
# for the ESTP_PREVM_CHECKS step of create service
class csPreVMChecks(CSBase):
    def __init__(self):
        self.step = 'ESTP_PREVM_CHECKS'

    def doExecute(self, aExaBoxCluCtrlObj, aOptions, aStepList):

        ebLogInfo('csPreVMChecks: Entering doExecute')
        ebox = aExaBoxCluCtrlObj
        steplist = aStepList
        imageBom = ImageBOM(ebox)

        _csu = csUtil()
        _pchecks = ebCluPreChecks(ebox)
        ebox.mUpdateStatus('createservice step ESTP_PREVM_CHECKS')

        # Note: Ref Bug 37406059: run vm exists check before
        # mFetchHardwareAlerts()
        # Check if VM already exists -- skip precheck / semantic
        ebLogTrace('csPreVMChecks: Entering mVMPreChecks')
        if _pchecks.mVMPreChecks():
            _error_str = '*** Fatal ERROR - VMs already existing can not continue VM install'
            ebLogError(_error_str)
            raise ExacloudRuntimeError(0x0410, 0xA, _error_str,aStackTrace=False,
                   aStep=self.step, aDo=True)

        #
        # PRE-VM Hardware Alert check
        #
        if not imageBom.mIsSubStepExecuted(self.step, "HW_PRECHECKS"):
            _max_retries = 3
            _retry_count = 0
            _step_time = time.time()
            ebox.mUpdateStatusCS(True, self.step, steplist, aComment='HW Prechecks')
            while _retry_count < _max_retries:
                if _pchecks.mFetchHardwareAlerts(aOptions, aStep=self.step):
                    break
                else:
                    _retry_count += 1
                    if _retry_count < _max_retries:
                        time.sleep(5)  # wait 5 seconds before retrying
            if _retry_count == _max_retries:
                _error_str = '*** Fatal ERROR - Hardware alerts fetching failed after {} retries'.format(_max_retries)
                ebLogError(_error_str)
                raise ExacloudRuntimeError(0x0390, 0xA, _error_str, aStackTrace=False,
                   aStep=self.step, aDo=True)
            ebox.mLogStepElapsedTime(_step_time, 'HW Prechecks')

        _isclone = aOptions.jsonconf.get("isClone", None)
        if _isclone and str(_isclone).lower() == "true":
            _exascale = ebCluExaScale(self)
            _exascale.mClonePreCheck(aOptions)

    def undoExecute(self, aExaBoxCluCtrlObj, aOptions, aStepList):
        ebLogInfo('csPreVMChecks: Entering undoExecute')