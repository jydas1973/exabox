"""
 Copyright (c) 2019, 2025, Oracle and/or its affiliates.

NAME:
    cs_util.py - step wise Create Service UTILities

FUNCTION:
    Implements utilities used during create service execution 

NOTES:
    Invoked from create service  stepwise execution classes

EXTERNAL INTERFACES: 
    csUtil

INTERNAL CLASSES:

History:
    MODIFIED (MM/DD/YY)
    pbellary  11/03/25   - Bug 38605016: INSTALL CLUSTER STEP FAILING TIMEOUT WHILE EXECUTING OEDA STEP: 9 
    pbellary  10/30/25   - Enh 38596691 - ASM/EXASCALE TO SUPPORT ADD NODE WITH EDV IMAGE
    akkar     08/30/25   - Bug 38025087: dbaastool rpm for multi cloud
    akkar     06/30/25   - Bug 38025087: dbaastool rpm for multi cloud
    pbellary  08/15/25   - Enh 38318848 - CREATE ASM CLUSTERS TO SUPPORT VM STORAGE ON EDV OF IMAGE VAULT 
    avimonda  07/17/25   - Bug 38019086 - EXACS: PROVISIONING FAILED WITH
                           EXACLOUD ERROR CODE: 0 EXACLOUD : NETWORK TIME
                           PROTOCOL (NTP) TEST FAILED BEFORE INSTALL CLUSTER
    rajsag    07/01/25   - 37812009 - 24.3.2 exacc exascale : xsconfig fails on
                           base 1/8th rack due to different steplist
    scoral    05/29/25   - Bug : Skip deletion of stale bonding interfaces
                           config files under network-scripts because it is not
                           using Exadata commands.
    abflores  03/12/25   - Bug 37473868: Fix marker files logging
    jfsaldan  02/26/25   - Bug 37570873 - EXADB-D|XS -- EXACLOUD | PROVISIONING
                           | REVIEW AND ORGANIZE PREVM_CHECKS AND PREVM_SETUP
                           STEPS
    prsshukl  11/28/24   - Bug 37240032 - Add ntp and dns value pre and post
                           OEDA create vm
    anudatta  11/22/24   - Enh 36553996 - clufy report before add node and install cluster
    rajsag    08/06/24   - ER 36907966 - exacloud: exacloud to support undo
                           operation for exascale config
    jesandov  08/08/23   - Bug 36899593 - Add support of remove bridges and create vm in parallel
    prsshukl  07/24/24   - Bug 34014317 - Remove Storage Pool from libvirt
                           definition on dom0s
    prsshukl  07/21/24   - Bug 36860623 - Re-Implement mWhitelistCidr
    prsshukl  06/17/24   - Bug 36260053 - 23C GRID IMAGES TO BE MADE AVAILABLE
                           FOR EXASCLE ENVIRONMENT
    pbellary  06/14/24   - ENH 36721696 - IMPLEMENT DELETE SERVICE STEPS FOR EXASCALE SERVICE
    dekuckre  05/27/24   - XbranchMerge dekuckre_bug-36663068 from
                           st_ecs_23.4.1.2.5
    dekuckre  05/27/24   - 36663068: update mDeleteStaleDummyBridge 
    aararora  05/06/24   - Bug 36557878: Remove double quotes along with single
                           quotes for used bridges.
    prsshukl  02/19/24   - Bug 36260050 - SUPPORT CREATING TEST OVERRIDE URL
                           FOR EXASCALE CLUSTER
    scoral    08/03/23   - 35646209: Call unmount_stale_gcv_edv during
                           mDeleteStaleDummyBridge
    scoral    07/14/23   - 35605560: Enhanced mDeleteBridges to show stdout &
                           stderr of brctl show
    naps      01/16/23   - Bug 34983589 Dont remove stale ifcfg files for
                           bonded env.
    naps      01/06/23   - Bug 34884579 - remove stale ifcfg file.
    jfsaldan  12/02/22   - Bug 34833579 - EXACS-MVM:CREATE VM CLUSTER FAILED IN
                           CREATEVM DUE TO UNABLE TO REMOVE STALE DUMMY BRIDGE
    dekuckre  07/21/22   - 34406947: Add timeout for OSTP_APPLY_FIX
    joysjose  07/08/22   - Add fix for 34319760
    scoral    06/08/22   - 34261110: Modified mFetchBridges to use a specific
                           list of nodes to work with Elastic Node deletion.
    ajayasin  03/22/22   - 33983538 : minor code issue
    ajayasin  02/16/22   - stale bridge removal
    ajayasin  01/08/22   - stale bridge removal
    ajayasin  12/09/21   - ahf install function
    naps      08/23/21   - Handle error during undo step.
    dekuckre  21/05/21   - 32899744: Acquire-release locks around calls to vm_maker
    llmartin  03/26/21   - 32418827: Increase OEADA step 2 execution timeout.
    alsepulv  03/16/21   - Enh 32619413: remove any code related to Higgs
    dekuckre  11/20/2020 - 32177169: raise Exception if OEDA failed to delete vm
    dekuckre  07/29/2020 - 31683600: Update timeout of different steps.
    dekuckre  03/18/2020 - 31046996: Add timeout for OSTP_CREATE_CELL
    dekuckre  11/29/2019 - 30571907: Gate OEDA execution with timeout 
                           and retry option
    dekuckre  06/19/2019 - 29928603: Avoid breaking flow during 
                           vmgi-gi-vm_delete
    srtata    04/01/2019 - Creation

"""
from exabox.core.Error import ebError, ExacloudRuntimeError, gProvError
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogVerbose, ebLogTrace
from exabox.ovm.csstep.cs_constants import csConstants, csXSConstants, csXSEighthConstants, csBaseDBXSConstants, csAsmEDVConstants, csEighthConstants, csX11ZConstants
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.ovm.clumisc import ebCluPreChecks
from exabox.ovm.hypervisorutils import getHVInstance
from exabox.ovm.cluhealth import ebCluHealthCheck
from exabox.healthcheck.cluexachk import ebCluExachk
from exabox.utils.node import connect_to_host, node_exec_cmd, node_exec_cmd_check, node_cmd_abs_path_check, node_write_text_file, node_read_text_file
from exabox.ovm.clubonding import dom0_supports_static_bridge
from exabox.exadbxs.edv import unmount_stale_gcv_edv
import exabox.ovm.clubonding as clubonding
from base64 import b64decode
import hashlib
import time, json
import re
import os
import subprocess
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure, TimeoutBehavior, ExitCodeBehavior

# This class contains utility functions used by create service 
# step wise execution classes
class csUtil(object):

    def __init__(self):
        self.__ahfProcessManager = None

     #estep is the exacloud create service step name given by ECRA
     #aOedaStep are the OEDA step constants
     #undo if set to TRUE will run the OEDA step with -u flag
    def mExecuteOEDAStep(self, aExaBoxCluCtrlObj, estep, steplist, aOedaStep, undo=False, dom0Lock=True, aSkipFail=False, aOverride=False):
        ebox = aExaBoxCluCtrlObj
        aOptions = ebox.mGetArgsOptions()
        _utils = ebox.mGetExascaleUtils()
        _csConstants = self.mGetConstants(ebox, False)
        _timeout = None
        _rc = True

        if ebox.mIsXS() or ebox.isBaseDB() or ebox.isExacomputeVM() or _utils.mIsEDVImageSupported(aOptions):
            _cnt = 0
            for _, _domU in ebox.mReturnDom0DomUPair():
                _cnt += 1
            _timeout = _cnt*30*60
        else:
            _timeout = self.mFetchDefaultCSTimeout(ebox, aOedaStep, _csConstants)

        ebLogInfo('csUtil mExecuteOEDAStep: Entering mExecuteOEDAStep aOedaStep='+ebox.mFetchOedaString(aOedaStep))
        #
        # OEDA Step 
        #
        # Acquire Remote Lock in shared mode-environment only if "dom0Lock " flag is True
        # Create service: lock required in the following steps OSTP_SETUP_CELL , OSTP_CREATE_CELL, OSTP_CREATE_GDISK
        # Delete service: None  of the steps required lock while executing
        if dom0Lock:
            ebox.mAcquireRemoteLock()
            ebLogInfo('csUtil mExecuteOEDAStep: Lock acquired for aOedaStep='+ebox.mFetchOedaString(aOedaStep))
        _step_time = time.time()
        ebox.mUpdateStatusCS(True, estep, steplist, oedaStep=aOedaStep)

        if undo:
           stepstr = "-u"
        else:
           stepstr = "-s"

        lCmd = "/bin/bash install.sh -cf {0} {1} {2} {3}".format(ebox.mGetRemoteConfig(), stepstr, \
                                                                            ebox.mFetchOedaStep(aOedaStep), \
                                                                            ebox.mGetOEDAExtraArgs())

        # Command for OEDA is contructed. mFetchOedaStep looks up a table to get OEDA step number
        if undo:
            _override_str = self.mGetOverrideStr(ebox, aOedaStep, aOverride)
            lCmd = lCmd + _override_str

        ebLogInfo('csUtil mExecuteOEDAStep: Running: ' + lCmd)

        try:
            _out = ebox.mExecuteCmdLog2(lCmd, aTimeOut=_timeout, aCurrDir=ebox.mGetOedaPath() )

            #Timeout, if OEDA step is still running, raise an ExacloudRuntimeError
            _rc  = ebox.mParseOEDALog(_out, estep, undo)
            _skip_exception = False
            if not _rc:
                _rc, _skip_exception  = ebox.mParseOEDAErrorJson(_out, estep, undo)
                if not _rc:
                    ebLogError("Exception detected both in OEDA logs & OEDAErrors.json...")
                    _rc = False
                else:
                    ebLogError("Exceptions detected only in OEDA logs. No OEDAErrors.json found...")
                    _rc = False
            else:
                _rc, _skip_exception  = ebox.mParseOEDAErrorJson(_out, estep, undo)
                if not _rc:
                    ebLogWarn("Exception detected only in OEDAErrors.json. No errors detected in OEDA logs...")
                    _rc = False
                else:
                    ebLogInfo("Parsing OEDA logs & OEDAErrors.json are successful. No errors reported...")
                    _rc = True
            if _skip_exception:
                _rc = True

        except ExacloudRuntimeError as ere:

            ebLogError("Timeout while executing OEDA Step: %s" % str(aOedaStep))
            _rc = False

    
        if str(estep) == "ESTP_CREATE_VM" and _utils.mIsEDVImageSupported(aOptions):
            #copy updated oeda file to patch config file
            ebox.mCopyFile(ebox.mGetRemoteConfig(), ebox.mGetPatchConfig())

        ebox.mLogStepElapsedTime(_step_time, f"Finished OEDA step: {ebox.mFetchOedaString(aOedaStep)}")

        if not _rc:
            try:
                if str(estep) in ["ESTP_CREATE_VM", "ESTP_POSTVM_INSTALL", "ESTP_CREATE_USER", "ESTP_CREATE_STORAGE", "ESTP_INSTALL_CLUSTER", "ESTP_POSTGI_INSTALL", "ESTP_POSTGI_NID"]:
                    ebox.mRunVMDiagnosticOnOEDAFailure()
            except Exception as e:
                ebLogError("Exception occured while running VM diagnostics. Exception: %s"%(str(e)))

        if dom0Lock:
            ebox.mReleaseRemoteLock()
        if not _rc:
            ebLogError('*** Fatal Error *** : Aborting current job - please review errors log and try again.')
            _error_str = "OEDA : OEDA step " +str(aOedaStep) + " failed."
        
            # Avoid breaking flow during vmgi-gi-vm_delete
            if ebox.mGetCmd() in ['vmgi_delete', 'vm_delete', 'gi_delete', 'deleteservice'] and str(estep) != "ESTP_CREATE_VM":
                ebLogError(_error_str)
            else:
                if aSkipFail:
                    ebLogError(_error_str)
                else:
                    raise ExacloudRuntimeError(0x0411, 0xA, _error_str, aStackTrace=False)


        ebLogInfo('csUtil mExecuteOEDAStep: Completed Successfully')

    def mIsRestartChronyDSuccessful(self, aDomU):

        with connect_to_host(aDomU, get_gcontext(), username="root") as _node:
            _systemctl = node_cmd_abs_path_check(_node, "systemctl", sbin=True)
            _cmd = f"{_systemctl} is-active --quiet chronyd"
            _ret, _out, _err = node_exec_cmd(_node, _cmd, log_warning=True, log_stdout_on_error=True)
            if _ret:
                ebLogWarn("The chronyd service is not active. Attempting restart.")
                _cmd = f"{_systemctl} restart chronyd"
                _ret, _out, _err = node_exec_cmd(_node, _cmd, log_warning=True, log_stdout_on_error=True)
                if _ret:
                    ebLogError(f"Failed to restart chronyd. Stdout is: {_out}, Stderr is: {_err}")
                    return False
                else:
                    ebLogInfo("The chronyd restarted successfuly")
                    return True

            return True

    def mHealthCheckClufy(self, ebox):#add
        for _dom0, _domU in ebox.mReturnDom0DomUPair():
            with connect_to_host(_domU, get_gcontext(), username="grid") as _node:
                _gihome, _, _ = ebox.mGetOracleBaseDirectories(aDomU=_domU)
                if not _gihome:
                    _gihc = ebox.mGetClusters().mGetCluster()
                    _gihome = _gihc.mGetCluHome()
                _cmd_timeout = 300
                match = None
                _hostname = _domU.split(".")[0]
                _cmd = _gihome + '/runcluvfy.sh stage -pre crsinst -n ' + _hostname + ' -verbose'
                _i, _o, _e = _node.mExecuteCmd(_cmd, aTimeout=_cmd_timeout)
                _ret = _node.mGetCmdExitStatus()
                if _e:
                    ebLogInfo(_e)
                if _o:
                    _output = _o.readlines()
                    # Join all lines in _output into a single string
                    output_text = ''.join(_output)
                    ebLogTrace(output_text)
                    pattern = r"Network Time Protocol \(NTP\).*PASSED"
                    match = self.match_pattern(output_text, match, pattern)
                    if match:
                        ebLogInfo("Pattern found in output : Network Time Protocol (NTP) PASSED")
                    else:
                        msg="Network Time Protocol (NTP) test Failed before install cluster"
                        pattern = r".*PRVG-1017.*"
                        match = self.match_pattern(output_text, match, pattern)
                        if match:
                            # Add a brief pause to ensure the network interfaces are fully up and running before continuing.
                            time.sleep(5)
                            ebLogWarn(f"{msg}, attempting restart chronyd")
                            if not self.mIsRestartChronyDSuccessful(_domU):
                                raise ExacloudRuntimeError(aErrorMsg=msg)
                        else:
                            raise ExacloudRuntimeError(aErrorMsg=msg)

                    pattern = r"DNS/NIS name service.*PASSED"
                    match = self.match_pattern(output_text, match, pattern)
                    if match:
                        ebLogInfo("Pattern found in output : DNS/NIS name service.*PASSED")
                    else:
                        raise ExacloudRuntimeError(aErrorMsg=" DNS/NIS name service test Failed before install cluster")

                    pattern = r"Node Connectivity.*PASSED"
                    match = self.match_pattern(output_text, match, pattern)
                    if match:
                        ebLogInfo("Pattern found in output : Node Connectivity.*PASSED")
                    else:
                        ebLogWarn(" Node Connectivity test Failed before install cluster")

                    # clufy report generation in the output
                    clufyReportfile = ebox.mGetOedaPath() + f"/WorkDir/clufyReport_install_cluster-{_domU}.txt"
                    try:
                        # Open the file in write mode and write the lines
                        with open(clufyReportfile, "w") as report_file:
                            report_file.writelines(_output)  # Attempt to write to the file                                                                             
                        ebLogInfo(f"Report saved as {clufyReportfile}")
                    except FileNotFoundError as e:
                        ebLogInfo(f"Error: The file or directory was not found. Details: {e}")
                    except PermissionError as e:
                        ebLogInfo(f"Error: Permission denied. Details: {e}")
                    except OSError as e:
                        ebLogInfo(f"Error: OS error occurred. Details: {e}")
                    except Exception as e:
                        ebLogInfo(f"An unexpected error occurred. Details: {e}")

    def match_pattern(self, _output, match, pattern):#add
         # Join all lines in _output into a single string
         output_text = ''.join(_output)
         # Search for the pattern in output_text with re.IGNORECASE for case-insensitivity
         match = re.search(pattern, output_text, re.IGNORECASE)
         return match

    def mFetchDefaultCSTimeout(self, aExaBoxCluCtrlObj, aOedaStep, aCSConstant=None):
        ebox = aExaBoxCluCtrlObj
        _csConstant = aCSConstant
        _oedastep_table = {}
        _timeout = 0

        try:
            # if present, use the timeouts defined in config/cs_step_timeout.json :
            #
            #    {
            #        "OSTP_CREATE_VM":"10",
            #        "OSTP_CREATE_USER":"20",
            #        .
            #        .
            #    }
            with open('config/cs_step_timeout.json', 'r') as _f:
                _data = json.load(_f)

                _oedastep_table[_csConstant.OSTP_CREATE_VM] = int(_data['OSTP_CREATE_VM'])
                _oedastep_table[_csConstant.OSTP_CREATE_USER] = int(_data['OSTP_CREATE_USER'])
                _oedastep_table[_csConstant.OSTP_SETUP_CELL] = int(_data['OSTP_SETUP_CELL'])
                _oedastep_table[_csConstant.OSTP_CREATE_CELL] = int(_data['OSTP_CREATE_CELL'])
                _oedastep_table[_csConstant.OSTP_CREATE_GDISK] = int(_data['OSTP_CREATE_GDISK'])
                _oedastep_table[_csConstant.OSTP_INSTALL_CLUSTER] = int(_data['OSTP_INSTALL_CLUSTER'])
                _oedastep_table[_csConstant.OSTP_INIT_CLUSTER] = int(_data['OSTP_INIT_CLUSTER'])
                _oedastep_table[_csConstant.OSTP_CREATE_ASM] = int(_data['OSTP_CREATE_ASM'])
                _oedastep_table[_csConstant.OSTP_APPLY_FIX] = int(_data['OSTP_APPLY_FIX'])
        except:
            _cnt = 0
            for _, _domU in ebox.mReturnDom0DomUPair():
                _cnt += 1

            # following timeout limits are decided based on time taken
            # by the steps in the provisioning flow (using Quarter rack).
            # In case of more nodes in the cluster (_cnt), the timeouts
            # have been extrpolated accondingly (as a factor of _cnt).
            _oedastep_table[_csConstant.OSTP_CREATE_VM] = _cnt*45*60
            _oedastep_table[_csConstant.OSTP_CREATE_USER] = _cnt*15*60
            _oedastep_table[_csConstant.OSTP_SETUP_CELL] = _cnt*30*60
            _oedastep_table[_csConstant.OSTP_CREATE_CELL] = _cnt*30*60
            _oedastep_table[_csConstant.OSTP_CREATE_GDISK] = _cnt*20*60
            _oedastep_table[_csConstant.OSTP_INSTALL_CLUSTER] = _cnt*15*60
            _oedastep_table[_csConstant.OSTP_INIT_CLUSTER] = _cnt*45*60
            _oedastep_table[_csConstant.OSTP_CREATE_ASM] = _cnt*15*60
            _oedastep_table[_csConstant.OSTP_APPLY_FIX] = _cnt*15*60

        if aOedaStep in _oedastep_table.keys():
            _timeout = _oedastep_table[aOedaStep]

        return _timeout

    def mPreVMDeleteCreatePatching(self, aExaBoxCluCtrlObj, aOptions):
        _ebox = aExaBoxCluCtrlObj
        _dbpair = _ebox.mReturnDom0DomUPair()
        _ssh_comment = ''
        _path_sshdir = '/root/.ssh/authorized_keys'
        _jconf = aOptions.jsonconf
        _ssh_key = _ebox.mGetToolsKey()
        for _pair in _dbpair:
            _domu = _pair[1]
            ebLogInfo('*** Tools Keys VM Patching for: '+_domu)

            if not _ebox.mPingHost(_domu):
                ebLogWarn('*** Host (%s) is not pingable aborting VM Patching for this host.' % (_domu))
                continue

            _node = exaBoxNode(get_gcontext())
            _node.mResetHostKey(aHost=_domu)
            _node.mConnect(aHost=_domu)
            if _ebox.mGetToolsKey():
                #_cmd = 'test -f ' + _path_sshdir
                _cmd = 'grep -F "'+str(_ssh_key)+'" '+_path_sshdir+' 2> /dev/null'
                _node.mExecuteCmd(_cmd)
                _rc = _node.mGetCmdExitStatus()
                if not _rc:
                    _esckey = _ssh_key.replace('/','\\/')
                    _cmd = 'sed \'/'+_esckey+'/d\' -i '+_path_sshdir+' 2> /dev/null'
                    _node.mExecuteCmd(_cmd)
                    _cmt = _ssh_key.split(' ')[-1]
                    ebLogInfo('*** SSH Key (%s) removed from authorized_keys' % (_cmt))

    def mPreVMDeleteCellPatching(self, aExaBoxCluCtrlObj, aOptions):
        """
        Step 1. Drop the FlashCache on that Cell
        # cellcli -e drop flashcache

        Step 2. Check the status of ASM if the grid disks go OFFLINE. The following command should return 'Yes' for the grid disks being listed:
        # cellcli -e list griddisk attributes name,asmmodestatus,asmdeactivationoutcome

        Step 3. Inactivate the griddisk on the cell
        # cellcli -e alter griddisk all inactive

        Step 4. Shut down cellsrv service
        # cellcli -e alter cell shutdown services cellsrv

        Step 5. Restart the cellsrv service
        # cellcli -e alter cell startup services cellsrv
        """
        _ebox = aExaBoxCluCtrlObj

        _cmds_list = [ 'cellcli -e drop flashcache',  'cellcli -e list griddisk attributes name,asmmodestatus,asmdeactivationoutcome',
                       'cellcli -e alter griddisk all inactive', 'cellcli -e alter cell shutdown services cellsrv',
                       'cellcli -e alter cell startup services cellsrv'
            ]

        for _cell in sorted(_ebox.mReturnCellNodes().keys()):
            ebLogInfo('*** Cell : '+str(_cell))
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_cell)
            for _cmd in _cmds_list:
                _node.mExecuteCmdLog(_cmd)
            _node.mDisconnect()

    def mUndoSecureDOMUPwd(self, aExaBoxCluCtrlObj, aOptions):
        _ebox = aExaBoxCluCtrlObj
        _dpairs = _ebox.mReturnDom0DomUPair()

        _spwd = _ebox.mCheckConfigOption('root_spwd')
        if _spwd is None:
            _pchecks = ebCluPreChecks(self)
            _spwd = _pchecks.mGeneratePassword(_ebox.mGetClusters().mGetCluster().mGetCluId(), _ebox.mGetClusters().mGetCluster().mGetCluName(), _dpairs[0][1])

        _pwd = b64decode(_spwd).decode('utf8')    # Current default : V2UhY29tJDJ8czhldHRlUg==
        for _dom0, _domU in _dpairs:
            if not _ebox.mPingHost(_domU):
                ebLogWarn('*** Host (%s) is not pingable aborting SecureDOMUPwd for this host.' % (_domU))
                continue

            try:
                _nodeU = exaBoxNode(get_gcontext())
                #_nodeU.mSetPassword(_pwd)
                _nodeU.mConnect(aHost=_domU)

                _cmdstr = """echo 'root:%s' | chpasswd >& /dev/null""" % (_pwd)
                _nodeU.mExecuteCmdLog("sh -c \"" + _cmdstr + "\"")

                _cmdstr = """echo 'oracle:%s' | chpasswd >& /dev/null""" % (_pwd)
                _nodeU.mExecuteCmdLog("sh -c \"" + _cmdstr + "\"")

                _cmdstr = """echo 'grid:%s' | chpasswd >& /dev/null""" % (_pwd)
                _nodeU.mExecuteCmdLog("sh -c \"" + _cmdstr + "\"")

                #_cmd_restart_sshd = "service sshd restart"
                #_nodeU.mExecuteCmdLog(_cmd_restart_sshd)

                _nodeU.mDisconnect()
            except:
                ebLogWarn('*** Unable to update default password to Host (%s).' % (_domU))

    def mUndoSecureDOMUSsh(self, aExaBoxCluCtrlObj, aOptions):
        _ebox = aExaBoxCluCtrlObj
        _dom0s, _domUs, _cells, _switches = _ebox.mReturnAllClusterHosts()
        _cluhosts = _domUs
        for _host in _cluhosts:
            if not _ebox.mPingHost(_host):
                ebLogInfo('*** (SECURE_DOMU_SSH) Host: %s is not responding' % (_host))
                continue
            _node = exaBoxNode(get_gcontext())

            ebLogInfo('*** (SECURE_DOMU_SSH) Connecting to: %s' % (_host))
            try:
                _node.mConnect(aHost=_host)
            except:
                ebLogInfo('*** (SECURE_DOMU_SSH) Unable to connect to host: %s' % (_host))
                continue
            _node.mExecuteCmdLog('grep "^PasswordAuthentication" /etc/ssh/sshd_config')
            _node.mExecuteCmdLog('grep "^PermitRootLogin" /etc/ssh/sshd_config')
            _node.mExecuteCmdLog('grep "^PubkeyAuthentication" /etc/ssh/sshd_config')
            _node.mExecuteCmdLog('grep "OEDA_PUB" .ssh/authorized_keys')
            #
            # ON == (enable password authentication) && (Allow root login with passwd)
            #
            _cmd1_str_on  = "sed 's/^PasswordAuthentication.*/PasswordAuthentication yes/' -i /etc/ssh/sshd_config"
            _cmd2_str_on = "sed 's/^PermitRootLogin without-password/#PermitRootLogin without-password/' -i /etc/ssh/sshd_config"

            _cmd_restart_sshd = "service sshd restart"
            _node.mExecuteCmdLog(_cmd1_str_on + " ; " + _cmd2_str_on +  " ; " + _cmd_restart_sshd)
            _node.mDisconnect()

    def mUndoCopyFileToClusterConfiguration(self, aExaBoxCluCtrlObj, aRemoteFilename):
        _ebox = aExaBoxCluCtrlObj
        _signature = _ebox.mBuildClusterId()
        _config_name = hashlib.sha224(_signature.encode('utf8')).hexdigest()
        _dom0U_list = _ebox.mReturnDom0DomUPair()
        _dom0_d = {}
        for _dom0, _domU in  _dom0U_list:
            _dom0_d[_dom0] = _dom0

        for _dom0 in list(_dom0_d.keys()):
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_dom0)
            _cmd = "rm -r /opt/exacloud/clusters/config/{0}/{1}".format(_config_name, aRemoteFilename)
            _node.mExecuteCmdLog(_cmd)

    def mUpdateOEDAConfiguration(self, aExaBoxCluCtrlObj, aOptions):
        _ebox = aExaBoxCluCtrlObj
        _options = aOptions
        _use_xml_patching = False

        _ebox.mUpdateOEDAProperties(_options)
        #EXACC: PATCH THE XML WITH CLIENT/BACKUP/DR NETWORK EHTERNET SLAVES & ENABLE SKIPPASSPROPERTY FLAG
        _enable_skip_paasproperty = _ebox.mCheckConfigOption('enable_skip_passproperty')
        _use_xml_patching = True if _enable_skip_paasproperty.lower() == "true" else False
        _ebox.mOEDASkipPassProperty(aOptions, aUseXMLPatching=_use_xml_patching)

    def mDeleteVM(self, aExaBoxCluCtrlObj, aStep, aSteplist):
        _ebox = aExaBoxCluCtrlObj
        _step = aStep
        _step_list = aSteplist

        _step_time = time.time()
        _ebox.mUpdateStatusCS(True, _step, _step_list, aComment='Destroy VM before undoing Cells Setup')
        _ebox.mAcquireRemoteLock()
        for _dom0, _domu in _ebox.mReturnDom0DomUPair():
            _hv = getHVInstance(_dom0)
            _hv.mDestroyVM(_domu)

        _ebox.mReleaseRemoteLock()

        _ebox.mLogStepElapsedTime(_step_time, 'Destroy VM before undoing Cells Setup')

    def mGetBridgeInfo(self, aNode, aCmd):
        _bridge_list = []
        _node = aNode
        _,_out,_ = _node.mExecuteCmd(aCmd)
        _rc = _node.mGetCmdExitStatus()
        if not _rc:
            _bridge_list = _out.readlines() 
        return _bridge_list

    def mDeleteBridgeUtil(self, aNode, aStaleBridgeList, aExaBoxCluCtrlObj, aRaiseException=False):
        #find the stale dummy bridge list by comparing existing list and used list 
        _ebox = aExaBoxCluCtrlObj
        _stale_dummy_bridges = []
        _node = aNode

        _stale_dummy_bridges = aStaleBridgeList

        ebLogInfo(f"Stale Dummy Brigde List: {_stale_dummy_bridges}")

        _ignorableErrors = [
            "Bridge is not found in Exadata configuration files"
        ]

        # According to bug 34242510, currently we cannot remove a static bridge
        # with the --force option.
        _force = "--force" if not dom0_supports_static_bridge(_node) else ""

        for _stale_bridge in _stale_dummy_bridges:
           ebLogWarn(f"Found Stale Bridge {_stale_bridge} on {_node.mGetHostname()}. Removing using cmd: vm_maker --remove-bridge {_stale_bridge} {_force}")
           _cmd = f"/opt/exadata_ovm/vm_maker --remove-bridge {_stale_bridge} {_force}"
           ebLogInfo('*** Running command: ' + _cmd)
           _, _o, _e = _node.mExecuteCmd(_cmd)
           _out = _o.read().strip()
           _err = _e.read().strip()
           if _node.mGetCmdExitStatus():
               _error_str = (f"Unable to remove stale Dummy Bridge {_stale_bridge} on {_node.mGetHostname()}. "
                   f"Manual cleanup required.\nStdout is:\n{_out}\nStderr is:\n{_err}\n"
                   "Make sure the path '/EXAVMIMAGES/GuestImages' doesn't contain stale invalid files\n"
                   "If needed you can review the vm_maker trace file for more information: '/var/log/cellos/vm_maker.trc'")

               _toIgnore = False
               for _igErr in _ignorableErrors:
                   if _igErr in _error_str:
                       _toIgnore = True

               ebLogError(_error_str)
               if aRaiseException:
                   if not _toIgnore:
                       raise ExacloudRuntimeError(0x0453, 0xA, _error_str, aStackTrace=True)
           else:
               ebLogInfo(f"Stale Dummy Bridge {_stale_bridge} on {_node.mGetHostname()} got removed successfully!")
               ebLogTrace(f"Stdout is {_out}, and Stderr is {_err}")
               
        """
        _no_vms_present = False
        _cmd = f"/usr/sbin/vm_maker --list-domains"
        _, _o, _ = _node.mExecuteCmd(_cmd)
        _out = _o.readlines()
        if _node.mGetCmdExitStatus() == 0 and (not _out or not len(_out)):
            # Ensure dom0 does not have any more vms.
            _no_vms_present = True

        _cmd = f"/bin/ls /etc/sysconfig/network-scripts/ifcfg-*bondeth*"
        _node.mExecuteCmdLog(_cmd)

        if not clubonding.is_bonding_supported(_ebox) and _no_vms_present and _node.mGetCmdExitStatus() == 0:
            # When we remove the stale bridges above, vm_maker is recreating the file ifcfg-bondeth0 as part of the same '--remove-bridge'
            # As a consequence, *if* a dom0 reboot happens after this. then during bootup sequence, an empty /sys/class/net/bondeth0/bonding/slaves is getting created.
            # This empty slaves file will fail any subsequent provisioning on this dom0, at exacloud level and also at oeda layer.
            # This issue will happen more frequently in zdlra cases, because dom0 reboot happens as part of DeleteService for Zdlra.
            # For exacs, this may not happen in regular scenarios, since there is a no dom0 reboot during DeleteService. 
            # But for exacs, issue will occur if there was a manual reboot or imageupgrade triggerred reboot happens.
            _cmd = f"/usr/bin/rm -f /etc/sysconfig/network-scripts/ifcfg-*bondeth*"
            ebLogInfo(f"Removing stale file /etc/sysconfig/network-scripts/ifcfg-*bondeth*")
            _node.mExecuteCmd(_cmd)
        """

    def mDeleteStaleDummyBridge(self, aExaBoxCluCtrlObj, aList=None):
        _ebox = aExaBoxCluCtrlObj
        if aList:
            # Incase the operation (function) is called without cluster xml,
            # mReturnDom0DomUPair and functions which use mReturnDom0DomUPair
            # (like mIsKVM) cannot be used. NEed to use the list from payload.
            _list = aList
        else:
            _list = _ebox.mReturnDom0DomUPair()
            if not _ebox.mIsKVM():
                return 

        _staleBridgesBeforeWait = {}

        for _dom0, _domU in _list:
            with connect_to_host(_dom0, get_gcontext()) as _node:
                # 35646209: For Exacompute, there is a possibility that the
                # there are stale CGV EDVs that will make this dummy bridge
                # deletion fail, so we will try to clean those first.
                RMDIR: str = node_cmd_abs_path_check(_node, 'rmdir')
                for fs in unmount_stale_gcv_edv(_node):
                    node_exec_cmd_check(_node, f"{RMDIR} {fs.mountpoint}")

                # Get existing bridge list on dom0
                _bridges_full_list_d1 = self.mGetDummyBridgesBrctl(_node)
                _bridges_in_use_d1 = self.mGetInUseBridges(_node)
                _stale_dummy_bridges = [x for x in _bridges_full_list_d1 if x not in _bridges_in_use_d1]
                _stale_dummy_bridges.sort(reverse=True)

                _staleBridgesBeforeWait[_dom0] = _stale_dummy_bridges

        # Wait 60
        ebLogInfo("Waiting for bridges to be attached to vms")
        if not _ebox.mIsUt():
            _node.mExecuteCmd("/bin/ps -C vm_maker -o args | /bin/grep start-domain")
            if _node.mGetCmdExitStatus() == 0:
                time.sleep(60)

        for _dom0, _domU in _list:
            with connect_to_host(_dom0, get_gcontext()) as _node:

                # Get a second round of stale bridges
                _bridges_full_list_d2 = self.mGetDummyBridgesBrctl(_node)
                _bridges_in_use_d2 = self.mGetInUseBridges(_node)
                _stale_dummy_bridges_d2 = [x for x in _bridges_full_list_d2 if x not in _bridges_in_use_d2]
                _stale_dummy_bridges_d2.sort(reverse=True)

                # Delete stale briges between the two times
                _stale_dummy_bridges = [x for x in _staleBridgesBeforeWait[_dom0] if x in _stale_dummy_bridges_d2]
                _stale_dummy_bridges.sort(reverse=True)

                ebLogInfo(f"Final stale bridges list: {_stale_dummy_bridges}")

                #Raise exception required here as it is in create service flow and stalte bridge can cause CS fail
                if _stale_dummy_bridges:
                    self.mDeleteBridgeUtil(_node, _stale_dummy_bridges, _ebox, aRaiseException=True)


    def mFetchBridges(self, aExaBoxCluCtrlObj, aDom0DomUPairs=None):
        _ebox = aExaBoxCluCtrlObj
        _nodes = _ebox.mReturnDom0DomUPair() if aDom0DomUPairs is None else aDom0DomUPairs
        _bridges = {}
        if not _ebox.mIsKVM():
            return _bridges
       
        for _dom0, _domU in _nodes:
            _bridges[_dom0] = []
            _node = exaBoxNode(get_gcontext())
            _cmd = "/usr/bin/virsh dumpxml {0} | /bin/grep \"source bridge=\" | /bin/sed \'s/.*<source bridge=\(.*\)\/>.*/\\1/\' | /bin/tr -d \"'\"".format(_domU)
            _node.mConnect(aHost=_dom0)
            _, _out, _err = _node.mExecuteCmd(_cmd)
            if _err and " ".join(_err.readlines()).find("error: failed to get domain") != -1:
                ebLogWarn(f"virsh dumpxml {_domU} failed for {_domU}. Trying with GuestImages xml file")
                _cmd = f"/bin/grep -r \"source bridge\" /EXAVMIMAGES/GuestImages/{_domU}/*.xml |  /bin/sed \'s/.*<source bridge=\(.*\)\/>.*/\\1/\' | /bin/tr -d \"\\\"\""
                _, _out, _err = _node.mExecuteCmd(_cmd)
            if _out:
                _o = _out.readlines()
                for _line in _o:
                    _bridges[_dom0].append(_line.strip())

            _node.mDisconnect()

        return _bridges


    def mGetDummyBridgesBrctl(self, aDom0Node):
        """
        Parsing output from:

        # /sbin/brctl show
        bridge name bridge id       STP enabled interfaces
        vmbondeth0      8000.b8cef6a28d90   no      bondeth0
        vmbondeth0.1645     8000.b8cef6a28d90   no      bondeth0.1645
                                    vnet132
        vmbondeth0.1646     8000.b8cef6a28d90   no      bondeth0.1646
                            vnet133

        """

        _bridge_full_list = []

        # Get existing bridge list on dom0
        _cmd = f'/sbin/brctl show'
        _out = self.mGetBridgeInfo(aDom0Node, _cmd)
        for _o in _out:
            if _o.startswith("vmeth"):
                _bridge = _o.split("\t")[0]
                if re.search(r'vmeth\d\d\d', _bridge):
                    _bridge_full_list.append(_bridge)

        ebLogInfo(f"Bridges existing on {aDom0Node.mGetHostname()}: {_bridge_full_list}")
        return _bridge_full_list

    def mGetInUseBridges(self, aDom0Node):
        """
        Example of the qemu xml

        # /bin/grep -r "source bridge=" /etc/libvirt/qemu/*.xml 
        /etc/libvirt/qemu/ntg112-infvr.exadbxs.exadbxsdevvcn.oraclevcn.com.xml:      <source bridge='vmeth206'/>
        /etc/libvirt/qemu/rtgb032-ekrvn.exadbxs.exadbxsdevvcn.oraclevcn.com.xml:      <source bridge='vmbondeth0.1654'/>
        /etc/libvirt/qemu/rtgb032-ekrvn.exadbxs.exadbxsdevvcn.oraclevcn.com.xml:      <source bridge='vmeth201'/>
        """

        _bridges_in_use = []

        # Need tr command to remove single quotes as well as double quotes if present in source bridges output
        _cmd = f"/bin/grep -r \"source bridge=\" /etc/libvirt/qemu/*.xml |  /bin/sed \'s/.*<source bridge=\(.*\)\/>.*/\\1/\' | /bin/tr -d \"\\\'\" | /bin/tr -d \"\\\"\""
        _out = self.mGetBridgeInfo(aDom0Node, _cmd)
        for _line in _out:
            _line = _line.strip()
            if re.search(r'vmeth\d\d\d', _line):
                _bridges_in_use.append(_line)

        ebLogInfo(f"Bridges in use on {aDom0Node.mGetHostname()}: {_bridges_in_use}")
        return _bridges_in_use


    def mDeleteBridges(self, aExaBoxCluCtrlObj, aBridges):
        '''
           This will remove bridges that were not removed by oeda during vm deletion.
           For eg: vmbondeth0.127, vmbondeth1.135, vmeth206
           This should work for both single and multivm setups.
        '''
        _ebox = aExaBoxCluCtrlObj
        _bridges = aBridges
        if not _ebox.mIsKVM():
            #TODO: need to do this for xen if issue occurs in xen !
            return

        for _dom0 in _bridges:
            with connect_to_host(_dom0, get_gcontext()) as _node:
                _stale_bridges = []
                for _bridge in _bridges[_dom0]:
                    _cmd = f'/sbin/brctl show {_bridge}'
                    _ret = node_exec_cmd(_node, _cmd, log_warning=True, log_stdout_on_error=True)
                    if not _ret.exit_code:
                        _o = " ".join(_ret.stdout.splitlines())
                        if _o.find("can't get info No such device") == -1:
                            ebLogWarn(f'*** Bridge  {_bridge} is still present on dom0: {_dom0} - cmd out: {_o}')
                            _stale_bridges.append(_bridge)
                        else:
                            ebLogInfo('*** Bridge ' + _bridge + ' is already removed on dom0 ' + _dom0)
                if _stale_bridges:
                    _cmd = "/bin/grep -r \"source bridge\" /etc/libvirt/qemu/* |  /bin/sed \'s/.*<source bridge=\(.*\)\/>.*/\\1/\' | /bin/tr -d \"'\""
                    _, _out, _ = _node.mExecuteCmd(_cmd)
                    _rc = _node.mGetCmdExitStatus()
                    _all_bridge_list = []
                    if not _rc:
                         _o = _out.readlines()
                         for _line in _o:
                            _all_bridge_list.append(_line.strip())
                    #Get all used bridges and compare any stale bridge used by any other VM.If so, remove the same from stale entry
                    _to_delete_bridges = [x for x in _stale_bridges if x not in _all_bridge_list]
                    _to_delete_bridges.sort(reverse=True)

                    self.mDeleteBridgeUtil(_node, _to_delete_bridges, _ebox, aRaiseException=False)


    def mInstallAhfonDomU(self,aExaBoxCluCtrlObj,aStep=None,aStepList=None, aInit=True, aWait=True):

        def mInstallAhfonDomUInternal(aExaBoxCluCtrlObj,aStep=None,aStepList=None):

            _step_time = time.time()
            if aStep and aStepList:
                aExaBoxCluCtrlObj.mUpdateStatusCS(True, aStep, aStepList, aComment='AHF install on DomU')
            _options = aExaBoxCluCtrlObj.mGetArgsOptions()
            _hcObj = ebCluHealthCheck(aExaBoxCluCtrlObj, _options)
            _hcObjExachk = ebCluExachk(_hcObj, _options)
            try:
                _hcObjExachk.mInstallAhf("domU",_options)
            except Exception as e:
                ebLogError('*** AHF install failed for domU with error %s' % (str(e)))
                aExaBoxCluCtrlObj.mUpdateErrorObject(gProvError['ERROR_AHF_INSTALL_FAIL'],e)
                raise ExacloudRuntimeError(0x0129, 0x0A, "Failure during AHF installation setup")

            aExaBoxCluCtrlObj.mLogStepElapsedTime(_step_time, 'AHF install on DomU')

        if aInit:
            self.__ahfProcessManager = ProcessManager()

            _p = ProcessStructure(mInstallAhfonDomUInternal, [aExaBoxCluCtrlObj,aStep,aStepList], "AHF")
            _p.mSetMaxExecutionTime(20*60) # 20 minutes
            _p.mSetJoinTimeout(5)
            _p.mSetLogTimeoutFx(ebLogWarn)

            self.__ahfProcessManager.mStartAppend(_p)

        if aWait:
            self.__ahfProcessManager.mJoinProcess()

    def mSetEnvVariableInDomU(self, aExaBoxCluCtrlObj):
        _ebox = aExaBoxCluCtrlObj
        _cswlib_oss_url = _ebox.mCheckConfigOption('cswlib_oss_url')
        if _cswlib_oss_url:
            for _, _domU in _ebox.mReturnDom0DomUPair():
                with connect_to_host(_domU, get_gcontext(), 'root') as _node:
                    CSWLIB_OSS_URL = "CSWLIB_OSS_URL" 
                    try:
                        _tmp_path = "/etc/environment"
                        _cswlib_append = f"{CSWLIB_OSS_URL}={_cswlib_oss_url}\n"
                        node_write_text_file(_node, _tmp_path, _cswlib_append, append=True)
                        ebLogInfo(f"*** {CSWLIB_OSS_URL}={_cswlib_oss_url} appended in /etc/environment for DomU:{_domU}")
                    except Exception as e:
                        ebLogError(f"*** Error in appending {CSWLIB_OSS_URL}={_cswlib_oss_url} in {_domU}: {str(e)}")

    def mRemoveStoragePool(self, aExaBoxCluCtrlObj):
        """
        Remove Storage Pool from libvirt definition on the dom0s
        
        :param ebox: A clucontrol object.
        """

        ebox = aExaBoxCluCtrlObj
        for _dom0, _domU in ebox.mReturnDom0DomUPair():
            with connect_to_host(_dom0, get_gcontext()) as _node:
                try:
                    _virsh_cmd = node_cmd_abs_path_check(node=_node, cmd="virsh")
                    _cmd_str = f"{_virsh_cmd} pool-list --name"
                    _, _o, _e = _node.mExecuteCmd(_cmd_str)
                    _out = _o.read().strip()
                    _err = _e.read().strip()
                    if _node.mGetCmdExitStatus():
                        _msg = f'csPreVMSetup: {_cmd_str} command failed on dom0: {_dom0}.\nStdout is:\n{_out}\nStderr is:\n{_err}\n'
                        ebLogWarn(_msg)
                        continue
                    
                    # Stopping the pool if it is active in libvirt
                    _active_storage_pool_list = _out.split('\n')
                    ebLogInfo(f'The active storage pool list on {_dom0} is: {_active_storage_pool_list}')
                    if _domU in _active_storage_pool_list:
                        _cmd_str = f"{_virsh_cmd} pool-destroy {_domU}"
                        _, _o, _e = _node.mExecuteCmd(_cmd_str)
                        _out = _o.read().strip()
                        _err = _e.read().strip()
                        if _node.mGetCmdExitStatus():
                            _msg = f'csPreVMSetup: {_cmd_str} command failed on dom0: {_dom0} for domU: {_domU}.\nStdout is:\n{_out}\nStderr is:\n{_err}\n'
                            ebLogWarn(_msg)
                            continue
                        ebLogInfo(f'Output of {_cmd_str}: {_out}')
                    
                    _cmd_str = f"{_virsh_cmd} pool-undefine {_domU}"
                    _, _o, _e = _node.mExecuteCmd(_cmd_str)
                    _out = _o.read().strip()
                    _err = _e.read().strip()
                    if _node.mGetCmdExitStatus():
                        _msg = f'csPreVMSetup: {_cmd_str} command failed on dom0: {_dom0} for domU: {_domU}.\nStdout is:\n{_out}\nStderr is:\n{_err}\n'
                        ebLogWarn(_msg)
                        continue
                    ebLogInfo(f'Output of {_cmd_str}: {_out}')
                except Exception as e:
                    _msg = f"*** Warning in deleting the storage pool {_domU} in {_dom0}: {str(e)}"
                    ebLogWarn(_msg)

    def mGet23cMultiGiPath(self, aExaBoxCluCtrlObj, aVersion):
        # Fetch latest and if the whole version is present then that gi image path from inventory is used, else latest 23 gi image
        _ebox = aExaBoxCluCtrlObj
        aMajorVersion = '23'
        ebLogInfo("Getting the multgipath for gi image in local")
        _path = None
        if aVersion == aMajorVersion:
            for _klone in _ebox.mGetRepoInventory()['grid-klones']:
                if ('service' in _klone.keys()) and (_ebox.mGetServiceType() == "EXACS") and (_ebox.mGetServiceType() in _klone['service']) and _klone['xmeta']['latest'] and _klone['version'].split('.')[0] == aMajorVersion:
                    _path = _klone['files'][0]['path']

        else:
            for _klone in _ebox.mGetRepoInventory()['grid-klones']:
                if ('service' in _klone.keys()) and (_ebox.mGetServiceType() == "EXACS") and (_ebox.mGetServiceType() in _klone['service']) and _klone['version'].split('.')[0] == aMajorVersion:
                    if _klone['version'] == aVersion:
                        ebLogInfo(f"{aVersion} present in inventory.json. Calculating its path")
                        _path = _klone['files'][0]['path']
                        break

        return _path

    def mGet23cGiPathLatest(self, aExaBoxCluCtrlObj):
        _ebox = aExaBoxCluCtrlObj
        aMajorVersion = '23'
        ebLogInfo("Getting the latest 23 version path for gi image in local")
        _path = None
        for _klone in _ebox.mGetRepoInventory()['grid-klones']:
            if ('service' in _klone.keys()) and (_ebox.mGetServiceType() == "EXACS") and (_ebox.mGetServiceType() in _klone['service']) and _klone['xmeta']['latest'] and _klone['version'].split('.')[0] == aMajorVersion:
                _path = _klone['files'][0]['path']

        return _path

    def mInstall23cGridImageInDomU(self, aExaBoxCluCtrlObj, aDomUGridPath, aOptions):
        
        """
        For multigi,
        Copy the latest 23c grid-klone image to domU at aDomUGridPath path if grid_version is 23
        or copy the image whose version is passed in grid_version payload

        For singlegi,
        grid_version is 19 -> Nothing needs to be done
        grid_version is 23 -> Copy the latest 23 grid image to aDomUGridPath
        """

        _ebox = aExaBoxCluCtrlObj
        _gi_payload = None
        _gi_path = None
        _local_gi_path = None
        _repository_root = _ebox.mCheckConfigOption('repository_root')
        if not _repository_root:
            ebLogWarn('*** repository_root key not found in exabox.conf. Inventory not loaded.')
            return
        # Get GI from Payload
        if aOptions and aOptions.jsonconf and "grid_version" in aOptions.jsonconf:
            _gi_payload = aOptions.jsonconf['grid_version']
            if _gi_payload and _gi_payload[:2] == "23":
                if _ebox.mGetGiMultiImageSupport():
                    _gi_path = self.mGet23cMultiGiPath(_ebox, _gi_payload)
                    if not _gi_path:
                        ebLogInfo(f"No path for {_gi_payload} calculated. No copy done")
                        return
                    _local_gi_path = os.path.join(_repository_root, _gi_path)
                else:
                    _gi_path = self.mGet23cGiPathLatest(_ebox)
                    if not _gi_path:
                        ebLogInfo(f"No path for {_gi_payload} calculated. No copy done")
                        return
                    _local_grid_klones_path = os.path.join(_repository_root, 'grid-klones')
                    #Get the path of the image from where download has to happen
                    _local_gi_path = os.path.join(_local_grid_klones_path, _gi_path)

                ebLogInfo(f"Copying {_local_gi_path} to {aDomUGridPath}")
                for _, _domU in _ebox.mReturnDom0DomUPair():
                    with connect_to_host(_domU, get_gcontext()) as _nodeU:
                        MKDIR: str = node_cmd_abs_path_check(_nodeU, 'mkdir')
                        _cmd = f"{MKDIR} -p {aDomUGridPath}"
                        ebLogInfo(f"Creating {aDomUGridPath} grid path if not present")
                        _nodeU.mExecuteCmdLog(_cmd)
                        _nodeU.mCopyFile(_local_gi_path, aDomUGridPath)
            else:
                ebLogInfo("The gi version is not 23. No need for copying the gi image to domU")

    def mHostControlAccessStatus(self, aNode):
        
        if not aNode.mIsConnected():
            raise ExacloudRuntimeError(aErrorMsg=f"{aNode} is not connected")

        _cmdstr = """/opt/oracle.cellos/host_access_control access --status"""
        aNode.mExecuteCmdLog(_cmdstr)
        if aNode.mGetCmdExitStatus():
            raise ExacloudRuntimeError(aErrorMsg=f"mExecuteCmd Failed to execute {_cmdstr} on {aNode.mGetHostname()}")

    def mAddRulesAccessControl(self, aNode, aUser, aIp):
        
        if not aNode.mIsConnected():
            raise ExacloudRuntimeError(aErrorMsg=f"{aNode} is not connected")

        _cmdstr = f"/opt/oracle.cellos/host_access_control access -a --user {aUser} --origins {aIp}"
        aNode.mExecuteCmdLog(_cmdstr)
        if aNode.mGetCmdExitStatus():
            raise ExacloudRuntimeError(aErrorMsg=f"mExecuteCmd Failed to execute {_cmdstr} on {aNode.mGetHostname()}")
    
    def mWhitelistCidr(self, aExaBoxCluCtrlObj, _node):
        """
        Whitelist admin Network Cidr for Exacc-Fedramp env. 
        Appends the new ip at the end of the already present root user rules
        """

        if not _node.mIsConnected():
            raise ExacloudRuntimeError(aErrorMsg=f"{_node} is not connected")

        _ebox = aExaBoxCluCtrlObj
        _ocps_jsonpath = _ebox.mCheckConfigOption('ocps_jsonpath')
        if _ocps_jsonpath and os.path.exists(_ocps_jsonpath):
            with open(_ocps_jsonpath, 'r') as fd:
                _ocps_json = json.load(fd)
            if 'adminNetworkCidr' in _ocps_json and _ocps_json['adminNetworkCidr']:
                #Export the configuration file
                _timestamp = str(time.time()).replace(".", "")
                _exportFile = "/tmp/access_rule_fedramp_export{0}.txt".format(_timestamp)
                _cmdstr = f"/opt/oracle.cellos/host_access_control access-export --file={_exportFile}"
                _node.mExecuteCmdLog(_cmdstr)
                if _node.mGetCmdExitStatus():
                    raise ExacloudRuntimeError(aErrorMsg=f"mExecuteCmd Failed to execute {_cmdstr} on {_node.mGetHostname()}")
                
                lines = node_read_text_file(_node, _exportFile).splitlines()
                _root_user_rule_present = False

                # Find the root access line and append the whitelist Cidr
                for i,line in enumerate(lines):
                    if line.startswith("+ : root :"):
                        _root_user_rule_present = True
                        # Append the whitelist Cidr
                        if _ocps_json['adminNetworkCidr'] not in lines[i]:
                            lines[i] = line.strip() + " " + _ocps_json['adminNetworkCidr']
                        break

                if _root_user_rule_present is False:
                    self.mAddRulesAccessControl(_node, "root", _ocps_json['adminNetworkCidr'])
                    self.mHostControlAccessStatus(_node)
                    return

                # Remove all the lines started with "#"" . So that only rules are present
                filtered_lines = [line for line in lines if not line.strip().startswith("#")] 

                _importFile = "/tmp/access_rule_fedramp_import{0}.txt".format(_timestamp)
                _importFileOnHost = "/tmp/access_rule_fedramp_import_host_{0}.txt".format(_node.mGetHostname())

                with open(_importFileOnHost, "w") as _file:
                    for line in filtered_lines:
                        _file.write(line + "\n")

                _node.mCopyFile(_importFileOnHost, _importFile)

                _cmdstr = f"/opt/oracle.cellos/host_access_control access-import --file={_importFile} <<< yes"
                _node.mExecuteCmdLog(_cmdstr)
                if _node.mGetCmdExitStatus():
                    raise ExacloudRuntimeError(aErrorMsg=f"mExecuteCmd Failed to execute {_cmdstr} on {_node.mGetHostname()}")
                
                #Delete the rule files
                _rm_cmd = node_cmd_abs_path_check(_node, 'rm')
                _cmdstr = f"{_rm_cmd} {_exportFile} {_importFile}"
                _node.mExecuteCmdLog(_cmdstr)

                _ebox.mExecuteLocal(f"/bin/rm {_importFileOnHost}")

                self.mHostControlAccessStatus(_node)

            else:
                _err_str = '*** Fatal Error *** adminNetworkCidr is not present in OCPS token file ***'
                ebLogError(_err_str)
                raise ExacloudRuntimeError(aErrorMsg=_err_str)
        else:
            _err_str = '*** OCPS token file is missing ***'
            ebLogError(_err_str)
            raise ExacloudRuntimeError(aErrorMsg=_err_str)

    def mReturnCountofVm(self, aExaBoxCluCtrlObj):
        """
        DEPRECATED: Use plain aExaBoxCluCtrlObj.mCheckNumVM
        No need to grab lock, we know vm_maker will create
        a dir under /EXAVMIMAGES/GuestImages/<vm> so that
        is enough to return a VM is present

        return the count of vm in the dom0 also taking
        lock** (no longer used)
        so that any new vms that is getting created is created post that.
        """

        _numVms = aExaBoxCluCtrlObj.mCheckNumVM()
        return _numVms
    
    def mGetDbaastoolRpmName(self, aOptions, aLocalPath='images/'):
        """
        Determine the Dbaastools rpm name and return based on localpath
        """
        ebLogTrace(f'Selecting DBAAS RPM ...')
        _dbaastools_rpm_default = 'dbaastools_exa_main.rpm'
        # verify the payload contains entry or not
        if aOptions and aOptions.jsonconf and "location" in aOptions.jsonconf and \
        aOptions.jsonconf['location'].get("dbaastoolsrpm") and \
        aOptions.jsonconf['location'].get("dbaastoolsrpm_checksum"):
            _dbaastools_rpm_payload = aOptions.jsonconf['location']["dbaastoolsrpm"]
            _dbaastools_rpm_checksum = aOptions.jsonconf['location']["dbaastoolsrpm_checksum"]
            ebLogTrace(f'Payload contains DBAAS RPM info, RPM: {_dbaastools_rpm_payload}, checksum: {_dbaastools_rpm_checksum}')
            # if local path as None , then no need to verify checksum
            if not aLocalPath:
                ebLogTrace(f'Local path not provided, skipping sha256sum check')
                return _dbaastools_rpm_payload
            
            # check if the rpm is present in the images folder and verify checksum
            _localfile = os.path.join(aLocalPath,_dbaastools_rpm_payload)
            ebLogTrace(f'DBAAS tools RPM path : {_localfile}')
            if not os.path.exists(_localfile):
                _err_str = '*** RPM doest not exist in images folder {_localfile} ***'
                ebLogError(_err_str)
                raise ExacloudRuntimeError(aErrorMsg=_err_str)
            
            ebLogTrace(f'DBAAS tools RPM exists at{_localfile}')
            _out = subprocess.check_output(['sha256sum', _localfile]).decode('utf8')
            _local_hash = _out.strip().split(' ')[0]
            ebLogTrace(f'DBAAS tools RPM computed checksum {_local_hash}')
            if _local_hash != _dbaastools_rpm_checksum: #matches
                _err_str = '*** RPM checksum does not match with payload ***'
                ebLogError(_err_str)
                raise ExacloudRuntimeError(aErrorMsg=_err_str)
                
            ebLogTrace(f'DBAAS tools RPM checksum verified')
            return _dbaastools_rpm_payload
        
        #if rpm details provided in payload does not exist/match checksum use default rpm
        ebLogTrace(f'Exacloud to use default DBAAS tools RPM : {_dbaastools_rpm_default}')
        return _dbaastools_rpm_default
    
    def mGetConstants(self, aExaBoxCluCtrlObj, aOptions=None, aCheckBaseDb=True):
        _csConstants = None
        _ebox = aExaBoxCluCtrlObj
        _utils = _ebox.mGetExascaleUtils()
        if _ebox.mIsXS():
            if _utils.mGetRackSize() == 'eighthrack':
                _csConstants = csXSEighthConstants
            else:
                _csConstants = csXSConstants
        elif (aCheckBaseDb and _ebox.isBaseDB()) or _ebox.isExacomputeVM():
            _ebox.mGetBaseDB().mUpdateOedaPropertiesInterface()
            _csConstants = csBaseDBXSConstants
        elif aOptions and _utils.mIsEDVImageSupported(aOptions):
            _csConstants = csAsmEDVConstants
        elif _utils.mGetRackSize() == 'eighthrack':
            _csConstants = csEighthConstants
        elif _utils.mGetRackSize() == 'zrack':
            _csConstants = csX11ZConstants
        else:
            _csConstants = csConstants
        return _csConstants

    def mGetOverrideStr(self, aExaBoxCluCtrlObj, aOedaStep, aOverride=False):
        _ebox = aExaBoxCluCtrlObj
        _csConstants = self.mGetConstants(_ebox, False)
        _override_str = ""

        if not _ebox.mIsExaScale() and not _ebox.mIsXS() and not _ebox.isBaseDB() and not _ebox.isExacomputeVM():
            if aOedaStep in [_csConstants.OSTP_CREATE_CELL, _csConstants.OSTP_CREATE_GDISK] or aOverride:
                _override_str = " -override"
        elif aOverride:
            _override_str = " -override"

        return _override_str
