#
# $Header: ecs/exacloud/exabox/infrapatching/core/ibclusterpatch.py /main/16 2025/02/27 06:37:17 sdevasek Exp $
#
# ibclusterpatch.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
#
#    NAME
#      ibclusterpatch.py - Class IBClusterPatch
#
#    DESCRIPTION
#      It is a wrapper that allows to manage the information located in ibfabricclusters.
#      It also allows to get the ibswitches information and sha512sum for each cluster xml we
#      receive as input.
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    sdevasek    02/14/25 - ENH 37496197 - INFRAPATCHING TEST AUTOMATION -
#                           REVIEW AND ADD METHODS INTO METHODS_TO_EXCLUDE_
#                           COVERAGE_REPORT
#    josedelg    09/22/24 - Bug 37071698 - Truncate file name to 225 characters
#    araghave    08/27/24 - Enh 36829406 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE CORE, PLUGIN AND TASKHANDLER
#                           FILES
#    araghave    06/13/24 - Enh 36522596 - REVIEW PRE-CHECK/PATCHING/ROLLBACK
#                           LOGS AND CLEAN-UP
#    araghave    05/24/23 - Bug 35424783 - CREATE SWITCH LIST FILE UNDER
#                           EXACLOUD CONF LOCATION
#    araghave    05/17/23 - Enh 35401978 - CALCULATE SHA256SUM FROM LIST OF
#                           SWITCH FETCHED FROM CLUSTER XML
#    araghave    11/25/22 - Bug 34828301 - EXACC:INFRA-PATCH:DOM0 PRECHECK
#                           EXPECT INCORRECT SPACE REQUIREMENT - SPACE IN / -
#                           NEEDED 5120 GB, GOT 2207 GB
#    araghave    10/07/22 - Enh 34623863 - PERFORM SPACE CHECK VALIDATIONS
#                           BEFORE PATCH OPERATIONS ON TARGET NODES
#    sdevasek    06/27/22 - Bug 33213137 - INTRODUCE A SPECIFIC ERROR IF ROCE 
#                           SWITCHES EMPTY FROM XML FILE 
#    araghave    12/08/21 - Enh 33598784 - MOVE ALL INFRA PATCHING ERROR CODES
#                           FROM ERROR.PY TO INFRAPATCHERROR.PY
#    araghave    07/08/21 - BUG 33081173 - Remove older error codes from Infra
#                           patching core files
#    vmallu      03/01/21 - Bug 32556005 clusterless patching is checking access
#                           to excluded node list
#    josedelg    01/20/21 - Bug 32387832
#                           Refactored bugs 31900436, 31945775, 
#                                           31970202, 32006820
#    nmallego    08/28/20 - Refactor infra patching code
#    nmallego    08/28/20 - Creation
#

from uuid import uuid4

from exabox.core.Context import get_gcontext
from exabox.infrapatching.utils.constants import *
from exabox.infrapatching.utils.utility import mFormatOut
from exabox.infrapatching.core.infrapatcherror import *
from exabox.core.Node import exaBoxNode
from exabox.infrapatching.handlers.loghandler import LogHandler
import re
import traceback

class IBClusterPatch(LogHandler):
    """
    Wrapper that allows to manage the information located in ibfabricclusters.
    It also allows to get the ibswitches information and sha512sum for each
    cluster xml that is received as input.
    Note : Please make sure to call mInitializeCluster method after constructor invocation.
    """

    def __init__(self, aOptions, aCall=None, aCluCtrl=None,aCluDispatcher=None):
        super(IBClusterPatch, self).__init__()
        self.__fabricID = -1
        self.__fabricSha512 = None
        self._clusterID = -1
        self.__ibSwitchList = []
        self.__node = None
        self.__cluctrl = None
        self.__excludeNodeList = []

        self.__options = aOptions

        # Cludispatcher object
        self.__cludispatcher = aCluDispatcher
        if aCall:
            # Dictionay obtained from parsing JSON input file
            self.__call = aCall

            _hostname = 'hostname'

            # Clean options
            for _key in self.__options.__dict__:
                if _key != _hostname:
                    setattr(self.__options, _key, None)

            # Set cluster XML file
            self.__options.configpath = aCall['XmlOeda']
            if 'AdditionalOptions' in self.__call and 'ExcludedNodeList' in \
               self.__call['AdditionalOptions'][0]:
               self.__excludeNodeList = self.__call['AdditionalOptions'][0]['ExcludedNodeList']

        elif aCluCtrl:
            self.__cluctrl = aCluCtrl

    def mInitializeCluster(self):
        """
         Note : Please make sure to call mInitializeCluster method after constructor invocation.
        """
        _rc = PATCH_SUCCESS_EXIT_CODE
        if self.__call:
            # Init cluster
            _rc = self.__initClusterHandler(self.__excludeNodeList)
            if _rc == PATCH_SUCCESS_EXIT_CODE:
                # Build clustername (cluster key)
                self.mBuildClusterName()
        return _rc

    def __initClusterHandler(self, aExcludeNodeList=None):
        """
        Initializes a exaBoxCluCtrl object in order to parse the xml file we received.
        """
        _rc = PATCH_SUCCESS_EXIT_CODE
        from exabox.ovm.clucontrol import exaBoxCluCtrl

        # Get context
        _ebContext = get_gcontext()
        #Create node
        self.__node = exaBoxNode(_ebContext, aLocal=True)
        self.__node.mConnect(aHost="localhost")
        # Create exaBoxCluCtrl object
        self.__cluctrl = exaBoxCluCtrl(aCtx=_ebContext, aNode= self.__node)
        # Parse xml file
        self.__cluctrl.mParseXMLConfig(self.__options)
        # KMS ImportKey requires an UUID to be set, it can be any one
        self.__cluctrl.mSetUUID(str(uuid4()))

        # KMS Mode
        # Fetch ssh keys in case of KMS env. Same keys would be deleted at
        # class exaBoxCluCtrl()-> mDispatchCluster()-> mDeleteOndiskKeys()

        self.__ociexacc = self.__cluctrl.mCheckConfigOption('ociexacc', 'True')

        # Get one dom0 that belongs to this cluster
        # TODO: EXCLUDED LIST IS NOT PROCESSED IN IB/ROCE PATCHING CLASS
        self.__dom0 = None
        for _dom0, _ in self.__cluctrl.mReturnDom0DomUPair(aIsClusterLessXML=self.__cluctrl.mIsClusterLessXML(), aExcludeNodeList=aExcludeNodeList):
            self.__dom0 = _dom0
            break

        # In case of upgrading cells from storage/clusterless xml, then we 
        # need to set dom0 with user provided launch node 
        if self.__cluctrl.mIsClusterLessXML() and self.__call['TargetType'] and \
           'cell' in self.__call['TargetType'] and  'AdditionalOptions' in self.__call:
            _addtitional_list = self.__call['AdditionalOptions'][0]
            if 'LaunchNode' in _addtitional_list: 
                self.__dom0 = _addtitional_list['LaunchNode']
                self.__cluctrl.mAppendToHostList(self.__dom0)
            else: 
                self.mPatchLogWarn("Unable to get launch node for cell upgrade")

        if not self.__dom0:
            _suggestion_msg = "Unable to fetch dom0 details."
            _rc = DOM0_DETAILS_NOT_AVAILABLE
            self.__cludispatcher.mAddDispatcherError(_rc, _suggestion_msg)
            return _rc

        # Get the ibfabric information
        _rc = self.mfetchSwitchFabric()

        return _rc

    def mfetchSwitchFabric(self):
        """
        Update switch list and checksum on switch list
        """
        _rc = PATCH_SUCCESS_EXIT_CODE
        _fabric_sha512 = None
        _switch_list = []

        if self.__cluctrl.mIsKVM():
            _switch = self.__cluctrl.mReturnSwitches(False, True)
        else:
            _switch = self.__cluctrl.mReturnSwitches(True)

        self.mPatchLogInfo(f"Switch list from XML : {_switch}")
        if len(_switch) == 0 :
            _suggestion_msg = "Switch list from cluster XML is empty."
            if self.__cluctrl.mIsKVM():
                _rc = ROCESWITCH_LIST_FROM_CLUSTER_XML_IS_EMPTY
            else:
                _rc = INVALID_DATA_FROM_IBSWITCHES_COMMAND
            self.__cludispatcher.mAddDispatcherError(_rc, _suggestion_msg)
            return _rc

        '''
         Stage switch_list file under exacloud conf location
         Switch_list file need to contain cluster name as 
         suffix to avoid multiple patch requests from different
         clusters to write into the same file.
        '''
        _exacloud_conf_location =  os.path.join(self.__cluctrl.mGetBasePath(), "config/")
        if not os.path.exists(_exacloud_conf_location):
            self.mPatchLogError(
                f"Exacloud config {_exacloud_conf_location} location does not exist and hence unable to create switch list file.")
            _rc = EXACLOUD_CONFIG_PATH_MISSING
            _suggestion_msg = f"Unable to create switch list file under exacloud config file as exacloud config location : {str(_exacloud_conf_location)} does not exist. Lock cannot be acquired and patch operation will be terminated."
            self.__cludispatcher.mAddDispatcherError(_rc, _suggestion_msg)
            return _rc

        self.mBuildClusterName()
        _switch_list_file = "switch_list_" + self.__cluname
        if len(_switch_list_file) >= 255:
            # if _switch_list_file name lenght is more than 255 character, we have to truncate to 255
            _switch_list_file = _switch_list_file[:255]
        _switch_list_conf_file = os.path.join(_exacloud_conf_location, _switch_list_file)
        self.mPatchLogInfo(f"Switch list file : {str(_switch_list_conf_file)} will contain checksum details of {str(_switch)}.")
        for _switch_name in _switch:
            with open(_switch_list_conf_file, 'a') as f:
                f.write(_switch_name)


        if os.stat(_switch_list_conf_file).st_size == 0:
            _suggestion_msg = f"Switch list file : {_switch_list_conf_file} is empty. Cannot proceed with patch operations."
            _rc = SWITCH_LIST_FILE_EMPTY
            self.__cludispatcher.mAddDispatcherError(_rc, _suggestion_msg)
            return _rc

        for _sw in _switch:
            _sw = _sw.strip()
            _switch_list.append({'hostname': _sw.split('.')[0], 'ip': ''})

        _cmd_sha512sum = f"/bin/sha512sum {_switch_list_conf_file}"
        _in, _out, _err = self.__node.mExecuteCmd(_cmd_sha512sum)

        _cmd = "awk '{print $1}'"
        _in, _out, _err = self.__node.mExecuteCmd(_cmd, aStdIn=_out)

        # Check if the command generated any error
        _err_lines = _err.readlines()
        if _err_lines:
            # Log the error. Do not bail out though, as it might be a warning.
            _err_msg = f"Command generated error. Command, error: sha512sum, {_err_lines}"
            self.mPatchLogWarn(_err_msg)
            _suggestion_msg = "Command : sha512sum returned invalid data on exacloud host."
            _rc = INVALID_DATA_FROM_SHA512SUM_COMMAND
            self.__cludispatcher.mAddDispatcherError(_rc, _suggestion_msg)
            return _rc

        # Parse output to get checksum
        _output = _out.readlines()
        if _output:
            _fabric_sha512 = _output[0].strip()

        self.mPatchLogInfo(f"CheckSum {_fabric_sha512}")

        if os.path.exists(_switch_list_conf_file):
            self.__node.mExecuteCmd(f"rm -rf {_switch_list_conf_file}")
        # Save information
        self.mSetIBSwitchList(_switch_list)
        self.mSetIBFabricSha512(_fabric_sha512)

        return _rc

    def mBuildClusterName(self):
        """
        Builds clustername or key: Dom0Name0vmNames0...
        """
        self.__cluname = ""
        _excluded_node_list = []
        # For clusterless, take clucontrol logic which will generate smaller IDs
        if self.__cluctrl.mIsClusterLessXML():
            _dom0s, _, _cells, _ = self.__cluctrl.mReturnAllClusterHosts()
            _host_list=''
            if 'AdditionalOptions' in self.__call:
                _addtitional_list = self.__call['AdditionalOptions'][0]
                if 'ExcludedNodeList' in _addtitional_list:
                    _excluded_node_list = _addtitional_list['ExcludedNodeList']
                else:
                     self.mPatchLogDebug("ExcludedNodeList is empty")
            if _dom0s:
                if _excluded_node_list:
                    _dom0s = [_node for _node in _dom0s if _node not in \
                        _excluded_node_list]
                _host_list = _dom0s[0].split('.')[0] + _dom0s[-1].split('.')[0]
            elif _cells:
                if _excluded_node_list:
                    _cells = [_node for _node in _cells if _node not in \
                        _excluded_node_list]
                _host_list = _cells[0].split('.')[0] + _cells[-1].split('.')[0]
            self.__cluname = ''.join(_host_list)
        else:
            self.__cluname = self.__cluctrl.mBuildClusterId()

    def mGetCall(self):
        return self.__call

    def mGetOptions(self):
        return self.__options

    def mSetIBFabricID(self, aIBFabricID):
        self.__fabricID = int(aIBFabricID)

    def mGetIBFabricID(self):
        return self.__fabricID

    def mSetIBFabricSha512(self, aSha512):
        self.__fabricSha512 = aSha512

    def mGetIBFabricSha512(self):
        return self.__fabricSha512

    def mSetIBSwitchList(self, aList):
        self.__ibSwitchList = aList

    def mGetIBSwitchList(self):
        return self.__ibSwitchList

    def mSetIBClusterID(self, aClusterID):
        self.__clusterID = int(aClusterID)

    def mGetIBClusterID(self):
        return self.__clusterID

    def mGetClusterName(self):
        return self.__cluname

    def mGetXMLIBSwitchList(self):
        if self.__cluctrl.mIsKVM():
            return self.__cluctrl.mReturnSwitches(False, True)
        else:
            return self.__cluctrl.mReturnSwitches(True)

