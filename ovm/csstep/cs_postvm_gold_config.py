"""
 Copyright (c) 2019, 2025, Oracle and/or its affiliates.

NAME:
    cs_postvm_gold_config.py - Complete step on Gold Image Provisioning

FUNCTION:
    Complete step on Gold Image Provisioning

NOTES:
    Invoked from cs_driver.py

EXTERNAL INTERFACES:
    csPostVmGoldConfig ESTP_POSTVM_GOLD_CONFIG

INTERNAL CLASSES:

History:
       MODIFIED (MM/DD/YY)
       jesandov  09/23/25 - 38437673: Add Bom file with minimal information
       jesandov  05/26/25 - 37265202: Add Bom file to DomU
       jesandov  03/14/25 - Bug 37675172 - File Creation
"""

import time
import os
import operator
import tempfile
import json
import copy

from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogVerbose, ebLogTrace, gLogMgrDirectory
from exabox.ovm.csstep.cs_constants import csConstants
from exabox.ovm.csstep.cs_util import csUtil
from exabox.ovm.csstep.cs_base import CSBase
from exabox.utils.node import node_cmd_abs_path_check, node_exec_cmd
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure
from exabox.utils.node import connect_to_host
from exabox.ovm.bom_manager import ImageBOM

from exabox.ovm.csstep.cs_exascale_complete import csExaScaleComplete
from exabox.ovm.csstep.cs_postvminstall import csPostVMInstall

# This class implements doExecute and undoExecute functions
# for the ESTP_GOLD_COMPLETE step of create service
class csPostVmGoldConfig(CSBase):
    def __init__(self):
        self.step = 'ESTP_POSTVM_GOLD_CONFIG'

    def mSaveBomFileDomU(self, aExaBoxCluCtrlObj, aOptions):

        _exagipFolder = "/opt/exacloud/exagip"
        _remoteBom = os.path.join(_exagipFolder, 'bom.conf')

        if "image_base_bom" in aOptions.jsonconf:

            _bom = copy.deepcopy(aOptions.jsonconf["image_base_bom"])

            _newbom = {
                "BOM_file_version": "",
                "BuildID": "",
                "artifacts": ""
            }

            for _key in list(_newbom.keys()):
                if _key in _bom:
                    _newbom[_key] = _bom[_key]

            fp = tempfile.NamedTemporaryFile(delete=False)
            fp.write( json.dumps(_newbom, indent=4).encode("utf-8") )
            fp.close()

            for _, _domU in aExaBoxCluCtrlObj.mReturnDom0DomUPair():
                with connect_to_host(_domU, get_gcontext()) as _node:
                    _node.mExecuteCmd(f"/bin/mkdir -p {_exagipFolder}")
                    _node.mCopyFile(fp.name, _remoteBom)
                    _node.mExecuteCmd(f"/bin/chmod 444 {_remoteBom}")

            os.unlink(fp.name)


    def doExecute(self, aExaBoxCluCtrlObj, aOptions, steplist):
        ebLogInfo('csGoldComplete: Entering doExecute')
        _ebox = aExaBoxCluCtrlObj
        _ebox.mUpdateStatus('createservice step '+self.step)
        _imageBom = ImageBOM(_ebox)
        _newStepList = steplist

        if not _imageBom.mIsSubStepExecuted(self.step, "USER_CONFIG"):
            if _imageBom.mIsGoldImageProvisioning() or _imageBom.mIsBaseDbProvisioning():
                _ebox.mConfigurePasswordLessDomU("opc")
                if _imageBom.mIsGoldImageProvisioning():
                    _ebox.mConfigurePasswordLessDomU("grid")
                    _ebox.mConfigurePasswordLessDomU("oracle")

        if not _imageBom.mIsSubStepExecuted(self.step, "BASEDB_OPT_PATITION"):
            if _imageBom.mIsBaseDbProvisioning():
                for _, _domU in _ebox.mReturnDom0DomUPair():
                    with connect_to_host(_domU, get_gcontext()) as _node:
                        node_exec_cmd(_node, f"/bin/sed -i 's@VGExaDbDomU-LVDbOpt@VGExaDb-LVDbOpt@g' /etc/fstab")

        if not _imageBom.mIsSubStepExecuted(self.step, "POSTVM_INSTALL"):
            _postVmInstall = csPostVMInstall()
            _newStepList = [_postVmInstall.step] + _newStepList
            _postVmInstall.doExecute(aExaBoxCluCtrlObj, aOptions, _newStepList)

        self.mSaveBomFileDomU(_ebox, aOptions)

        if not _imageBom.mIsSubStepExecuted(self.step, "EXASCALE_COMPLETE"):
            _exascaleComplete = csExaScaleComplete()
            _newStepList = [_exascaleComplete.step] + _newStepList
            _exascaleComplete.doExecute(aExaBoxCluCtrlObj, aOptions, _newStepList)

        ebLogInfo('*** csGoldComplete: Completed doExecute Successfully')


    def undoExecute(self, aExaBoxCluCtrlObj, aOptions, _steplist):
        ebLogInfo('*** csGoldComplete: Entering undoExecute')
        _ebox = aExaBoxCluCtrlObj
        _csu = csUtil()
        _newStepList = _steplist

        _exascaleComplete = csExaScaleComplete()
        _newStepList = [_exascaleComplete.step] + _newStepList
        _exascaleComplete.undoExecute(aExaBoxCluCtrlObj, aOptions, _newStepList)

        _postVmInstall = csPostVMInstall()
        _newStepList = [_postVmInstall.step] + _newStepList
        _postVmInstall.undoExecute(aExaBoxCluCtrlObj, aOptions, _newStepList)

        ebLogInfo('*** csGoldComplete: Completed undoExecute Successfully')


# end of file
