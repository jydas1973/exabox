"""
 Copyright (c) 2020, 2025, Oracle and/or its affiliates.

NAME:
    cluexaccmigration.py - Migrate ExaCC environments (dom0, domU, etc),
                           from Gen1 (OCC) to Gen2 (OCI)

FUNCTION:
    ExaCC Gen1 to Gen2 migration.

NOTE:
    ExaCC Gen1 to Gen2 migration.

History:

    MODIFIED   (MM/DD/YY)
    ririgoye   11/26/25 - Bug 38636333 - EXACLOUD PYTHON:ADD INSTANTCLIENT TO
                          LD_LIBRARY_PATH
    jesandov   10/16/23 - 35729701: Support of OL7 + OL8
    ririgoye   08/30/23 - Fix redundant/deprecated mConnect calls
    rajsag     01/15/23 - ol8 support
    abyayada   02/17/21 - Bug 33810140 - EXACC GEN1-GEN2 UPGRADE CREATE CLUSTER ISSUES 
    joseort    11/10/21 - Adding dbaasapi commands for update after rpms are
                          pushed.
    joseort    09/10/21 - Changed add wallet method locally to change flow for
                          migration
    joseort    07/29/21 - Adding jsonconf to path
    joseort    07/09/21 - Changing pkeys checker to avoid deletion.
    joseort    06/24/21 - Adding CPS IB configuration to migration task
    joseort    06/22/21 - Comment Reboot
    joseort    01/27/21 - Adding methods to change dns/ntp server
    joseort    01/11/21 - Changed reboot action to this operation as per BUG 32171459.
    oerincon   07/23/20 - Creation
"""
import os

from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.log.LogMgr import ebLogDebug, ebLogInfo, ebLogWarn, ebLogCrit, ebLogError
from exabox.core.Context import get_gcontext
from exabox.core.DBStore import ebInitDBLayer
from exabox.core.Node import exaBoxNode
from exabox.BaseServer.AsyncProcessing import ProcessManager
from exabox.ovm.cluexaccib import ExaCCIB_CPS
from exabox.network.dns.DNSConfig import ebDNSConfig
from exabox.utils.node import connect_to_host
from exabox.exakms.ExaKmsEntry import ExaKmsHostType

def migrateExaCCGen1ClusterToGen2(aCluCtrl):
    """
    Public utility method to migrate ExaCC Gen1 cluster to Gen2.

    Performs the following actions:
      - Configure firewall (iptables) rules as per Gen2 requirements
      - Update dbaas tools to latest version
      - Install DBCS agent in domU (along with required certificates)

    NOTE: This method should not be invoked for a context other than OCI ExaCC

    WARNING: As per v1: No error checking is done, since clucontrol methods this
    code uses, do not return special error codes for potential failures.
    Will revisit once better error handling is implemented on those external methods.
    """

    if not aCluCtrl.mIsOciEXACC():
        ebLogWarn('Migration should not be invoked for non OCI ExaCC environments')
        return

    # ebLogInfo("Reboot DomU's")
    # _mRebootDomUs(aCluCtrl)

    ebLogInfo('Configuring CPS IB')
    _mConfigureCpsIb(aCluCtrl)

    # TODO: Verify whether this won't interfere with customer pre-existing rules in dom0
    # TODO: This might be invoked multiple times in MVM environment, double check it is harmless
    # Configure iptables rules that are specific to ExaCC.
    isShared = aCluCtrl.mCheckSharedEnvironment()
    ebLogInfo('Configuring iptables according to Gen2 requirements isShared {0} aOptions[{1}]'.format(isShared, aCluCtrl.mGetArgsOptions()))
    aCluCtrl.mSetupNATIptablesOnDom0v2()

    # Prepare domUs for MTLS communication
    # Need to be executed *before* installing the dbcs agent
    ebLogInfo('Setting up certificates for secure communication to DBCS agent')
    aCluCtrl.mSetupDomUsForSecureDBCSCommunication()
    mAddAgentWallet(aCluCtrl)

    # Prepare domUs for MTLS communication, adding cprops.ini entries
    # Need to be executed *before* installing the dbcs agent
    ebLogInfo('Setting up cprops for secure communication to DBCS agent')
    aCluCtrl.mPrepareCloudPropertiesPayload()
    aCluCtrl.mPushCloudPropertiesPayload()
    aCluCtrl.mExecuteDbaaSApi()


    # Install/upgrade relevant RPMs
    ebLogInfo('Setting up Gen2 required RPMs')
    _mInstallRpmsInDomUs(aCluCtrl)
    _mExecuteDBaaSApiDomUs(aCluCtrl)

    # Reconfigure dns and ntp servers
    # configurator = ReconfigureDNSAndNtpServers(aCluCtrl)
    # configurator.doReconfigureDnsAndNtpServers()

def _mExecuteDBaaSApiDomUs(aCluCrtl):
    """
    Reboot
    :param aCluCrtl:
    :return:
    """
    _processes = ProcessManager()
    for _dom0, _domU in aCluCrtl.mReturnDom0DomUPair():
        _username = 'grid'

        # first connect as grid to get crsctl path
        ebLogInfo('*************************************************************************')
        with connect_to_host(_domU, get_gcontext(), username=_username) as _node:
            _cmd_Crs = 'which crsctl'
            _cmd_dbaascli = 'which dbaascli'
            _, _out, _err = _node.mExecuteCmd(_cmd_Crs)
            _crsCtlPath = str(_out.readline().replace('\n', ''))
            ebLogInfo('_mExecuteDBaaSApiDomUs: Found crsctl path [{0}]'.format(_crsCtlPath))
            
            _, _out, _err = _node.mExecuteCmd(_cmd_dbaascli)
            _dbaascliPath = str(_out.readline().replace('\n', ''))
            ebLogInfo('_mExecuteDBaaSApiDomUs: Found dbaascli path [{0}]'.format(_dbaascliPath))

        # crsctl getperm resource `crsctl stat res | grep acfs | awk -F= '{if ($1 == "NAME") print $2 }'`
        # crsctl setperm resource `crsctl stat res | grep acfs | awk -F= '{if ($1 == "NAME") print $2 }'` -u user:oracle:r-x -unsupported
        _cmd = _crsCtlPath + " getperm resource `" + _crsCtlPath + " stat res | grep acfs | awk -F= '{if ($1 == \"NAME\") print $2 }'`"
        _cmd_setPerm = _crsCtlPath + " setperm resource `" + _crsCtlPath + " stat res | grep acfs | awk -F= '{if ($1 == \"NAME\") print $2 }'` -u user:oracle:r-x -unsupported"
        _cmd_dbaascli = _dbaascliPath + " admin updateStack --version LATEST --force"
        _username = 'root'

        with connect_to_host(_domU, get_gcontext(), username=_username) as _node:
            # Update the interface
            ebLogInfo('_mExecuteDBaaSApiDomUs: Command for dbaasApi domU [{0}]'.format(str(_cmd)))
            _node.mExecuteCmdLog(_cmd)
            _node.mExecuteCmdLog(_cmd_setPerm)
            _node.mExecuteCmdLog(_cmd)
            ebLogInfo('_mExecuteDBaaSApiDomUs: Command [{0}]'.format(str(_cmd_dbaascli)))
            _node.mExecuteCmdLog(_cmd_dbaascli)
        
        ebLogInfo('_mExecuteDBaaSApiDomUs: Executed dbaasApi domU [{0}]'.format(str(_domU)))
        ebLogInfo('*************************************************************************')


def _mConfigureCpsIb(aCluCtrl) :
    _allGuids = aCluCtrl.mGetAllGUID()
    _pkeys = aCluCtrl.mCheckPkeysConfig(_allGuids, False)
    if aCluCtrl.mIsOciEXACC() and _pkeys is not None:
        #Add all IB entries to /etc/hosts.exacc_domuib
        ebDNSConfig(aCluCtrl.mGetArgsOptions(), aCluCtrl.mGetPatchConfig()).mConfigureDNS('guest')

        _exacc_ib_cps = ExaCCIB_CPS(_allGuids, _pkeys, aCluCtrl.mIsDebug(), True)
        _dom0s, _, _cells, _ = aCluCtrl.mReturnAllClusterHosts()
        # _exacc_ib_cps.mSetupIBSwitches(_dom0s, _cells)
        # Set up CPS IB
        _exacc_ib_cps.mSetupCPSIB()

def _mInstallRpmsInDomUs(aCluCtrl) :
    """ Traverse domUs and install/upgrade required RPMs for ExaCC. """

    # This will traverse the domUs and upgrade the RPMs
    ebLogInfo('Installing updated dbaastools rpm in the domUs.')
    aCluCtrl.mUpdateRpm('dbaastools_exa_main.rpm')

    ebLogInfo('Installing updated dbcs-agent rpm in the domUs.')

    _majorityVersion = aCluCtrl.mGetMajorityHostVersion(ExaKmsHostType.DOMU)

    if _majorityVersion in ["OL7", "OL8"]:
        aCluCtrl.mUpdateRpm('dbcs-agent-exacc.OL7.x86_64.rpm')
    else:
        aCluCtrl.mUpdateRpm('dbcs-agent-exacc.OL6.x86_64.rpm')

def _mRebootDomUs(aCluCrtl):
    """
    Reboot
    :param aCluCrtl:
    :return:
    """
    # In case of single vm, would be necessary to restart the Dom0s
    _processes = ProcessManager()
    for _dom0, _domU in aCluCrtl.mReturnDom0DomUPair():
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_dom0)

        _cmd = 'xm shutdown {0} -w; xm create /EXAVMIMAGES/GuestImages/{0}/vm.cfg'.format(_domU)
        # Update the interface
        ebLogInfo('*************************************************************************')
        ebLogInfo('mCreateDomUWithInterface: Command for rebooting and attaching interface is [{0}]'.format(str(_cmd)))
        _node.mExecuteCmdLog(_cmd)

        _node.mDisconnect()
        ebLogInfo('mCreateDomUWithInterface: Rebooted domU [{0}]'.format(str (_domU)))
        ebLogInfo('*************************************************************************')

def mAddAgentWallet(aCluCrtl, aWalletBundlePath: str = ""):
        """
        This function orchestrates the copy of both DBCS and CPS wallets.
        To do so it extracts both wallets from aWalletBundlePath (which
        should be the path where both wallets are located)
        param aWalletBundlePath: String representing the path where both
              wallets should exist encoded in base64.
              This path is fixed to "/opt/oci/exacc/config_bundle", however
              I left this as optional for unittest purposes.
        raises ExacloudRuntimeError
        """

        def executeOrRaise(aNode: exaBoxNode, aDomU: str, aCmd: str) -> None:
            """
            Helper function
            This function will execute aCmd on an already connected aNode
            If cmd returns non-zero code, it will raise ExacloudRuntimeError
            and will close aNode connection
            """
            _, _o, _e = _node.mExecuteCmd(aCmd)
            _rc = _node.mGetCmdExitStatus()
            if _rc:
                _messages = '\n'.join(_o.readlines()) + '\n'.join(_e.readlines())
                _err_msg = (f"Failed to create wallet in {aDomU}. "
                            f"Command '{aCmd}' failed with exit code {_rc}, "
                            f"stdout and sterr: {_messages}")
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(0x098, 0xA, _err_msg)

        def copyWallet(aNode: exaBoxNode, aEncodedWallet: str,
                       aRemoteDir: str, aUserPermission: str,
                       aGroupPermission: str) -> None:
            """
            This function copies aEncodedWallet to domU in aRemoteDir as
            cwallet.sso and sets proper permissions/ownership in addition
            to decode (base64) aEncodedWallet.
            param aNode: an already connected node to a domU host
            param aEncodedWallet: Filepath of desired wallet to copy on domU
            param aRemoteDir: Path in DomU where well copy wallet
            raises ExacloudRuntimeError:
            returns: None
            """
            _agent_wallet = aEncodedWallet
            _node = aNode
            _domU = None
            if not os.path.isfile(_agent_wallet):
                _err_msg = (f"Wallet {os.path.basename(_agent_wallet)} "
                            "does not exists")
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(0x098, 0xA, _err_msg)

            _remote_file_path = os.path.join(aRemoteDir, "cwallet.sso")
            _remote_file_base64 = _remote_file_path + ".b64"

            # Make sure remote dir exists
            _cmd = f"/usr/bin/mkdir -p {aRemoteDir}"
            executeOrRaise(_node, _domU, _cmd)

            # Assign proper permissions to remote dir
            _cmd = f"/usr/bin/chmod -R 700 {aRemoteDir}"
            executeOrRaise(_node, _domU, _cmd)

            # Assign proper ownership to remote dir
            _cmd = ("/usr/bin/chown -R "
                    f"{aUserPermission}:{aGroupPermission} "
                    f"{aRemoteDir}")
            executeOrRaise(_node, _domU, _cmd)

            # Copy base64 wallet to domU
            _node.mCopyFile(_agent_wallet, _remote_file_base64)

            # Decode base64 to final wallet
            _cmd = (f"sudo su {aUserPermission} --command '/usr/bin/base64 -d {_remote_file_base64} > "
                    f"{_remote_file_path}'")
            executeOrRaise(_node, _domU, _cmd)

            # Shred encoded wallet (no longer needed)
            _pass = aCluCrtl.mCheckConfigOption('vmerase_pass')
            if _pass is None:
                _pass = 3
            else:
                try:
                    _pass = int(_pass[:_pass.lower().find('pass')])
                except:
                    _pass = 3
            _cmd = (f"/usr/bin/shred {_remote_file_base64} "
                    f"-vun {_pass}")
            executeOrRaise(_node, _domU, _cmd)

            # Assign proper permissions to remote wallet file
            _cmd = f"/usr/bin/chmod 700 {_remote_file_path}"
            executeOrRaise(_node, _domU, _cmd)

            # Assign proper ownership to remote wallet file
            _cmd = ("/usr/bin/chown "
                    f"{aUserPermission}:{aGroupPermission} "
                    f"{_remote_file_path}")
            executeOrRaise(_node, _domU, _cmd)

            ebLogInfo("Succesfully added wallet "
                      f"{os.path.basename(aEncodedWallet)} on '{_domU}'")

        _bundle_wallets_path = aWalletBundlePath
        if not _bundle_wallets_path:
            _bundle_wallets_path = "/opt/oci/config_bundle"
        _dbcs_wallet = "DBCSAgentWallet.b64"
        _cps_wallet = "CPSAgentWallet.b64"
        # _dbcs_target_dir = "/tmp/dcs/auth"
        # _cps_target_dir = "/tmp/dbagent/dbagent_wallet"
        _dbcs_target_dir = "/opt/oracle/dcs/auth"
        _cps_target_dir = "/var/opt/oracle/dbaas_acfs/dbagent/dbagent_wallet"
        _dbcs_local_dir = os.path.join(_bundle_wallets_path, _dbcs_wallet)
        _cps_local_dir = os.path.join(_bundle_wallets_path, _cps_wallet)
        _dbcs_user_owner = "opc"
        _dbcs_group_owner = "opc"
        _cps_user_owner = "oracle"
        _cps_group_owner = "oinstall"

        if os.path.isfile(_dbcs_local_dir) and os.path.isfile(_cps_local_dir):
            for _, _domU in aCluCrtl.mReturnDom0DomUPair():
                _node = exaBoxNode(get_gcontext())
                try:
                    _node.mConnect(aHost=_domU)
                    copyWallet(_node, _dbcs_local_dir, _dbcs_target_dir,
                               _dbcs_user_owner, _dbcs_group_owner)
                    copyWallet(_node, _cps_local_dir, _cps_target_dir,
                               _cps_user_owner, _cps_group_owner)
                finally:
                    _node.mDisconnect()
        else:
            ebLogInfo("DBCS and/or CPS agent wallets don't "
                      f"exist in '{_bundle_wallets_path}'. This is no-op")

class ReconfigureDNSAndNtpServers(object):
    SUDO_COMMAND = '/usr/bin/sudo'
    IPCONF_TOOL_TMP_PATH = '/tmp/exacc_migration'
    IPCONF_TOOL_TAR_NAME = 'ipconf_migration.tar'
    IPCONF_TOOL_CMD= 'ipconf'
    IPCONF_TOOL_URL = 'http://exaboard.maa.oraclecorp.com/static/stage/ipconf.ntp.dns.online.changes.tar'

    def __init__(self, aCluCtrl):
        ebLogInfo('Starting Reconfigure DNS amd NTP object for cluster [{0}]'.format(aCluCtrl))

        _argsOptions = aCluCtrl.mGetArgsOptions()
        self._aCluCtrl = aCluCtrl

        ebLogInfo('Options for this execution [{0}]'.format(str(_argsOptions)))

        # Get Server options to obtain new server configuration
        self._cpsIpConfig, self._custDnsIpConfig, self._custNtpIpConfig = self._getNewDnsNtpIp(_argsOptions.jsonconf)
        self._dom0s, self._domUs, self._cells, self._switches = self._mGetHostList(aCluCtrl)

    def doReconfigureDnsAndNtpServers(self):
        """
        Public utility method to reconfigure ntp servers and dns servers into all components of this cluster.
        :param aCluCtrl: Cluster to be updated
        :return:  None
        """
        _eb_context = get_gcontext()
        _options = _eb_context.mGetArgsOptions()
        _config_file = get_gcontext().mGetConfigOptions()

        ebLogInfo('getting keys and values per options cpsIpConfig[{0}] - custDnsIpConfig[{1}] - custNtpIpConfig[{2}]'.format(str(self._cpsIpConfig), str(self._custDnsIpConfig), str(self._custNtpIpConfig)))
        ebLogInfo('Retrieved HostList dom0s[{0}] - domUs[{1}] - cells[{2}] - switches[{3}]'.format(str(self._dom0s), str(self._domUs), str(self._cells), str(self._switches)))

        ebInitDBLayer(_eb_context, _options)


        ebLogInfo('Reconfiguring dom0s in this run...')
        self._reconfigureNodeList(_eb_context, self._dom0s + self._cells, self._cpsIpConfig, None, True)
        ebLogInfo('Reconfiguring domUs in this run...')
        self._reconfigureNodeList(_eb_context, self._domUs, self._custDnsIpConfig, self._custNtpIpConfig, False)

    def _reconfigureNodeList(self, _eb_context, _aNodeList, _ipConfig, _ntpConfig, _updateIlom):
        ebLogInfo('Trying to reconfigure by nodelist[{0}]'.format(str(_aNodeList)))
        for _hostname in _aNodeList:
            ebLogInfo('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
            ebLogInfo('Trying to connect to host [{0}]'.format(str(_hostname)))
            _aNode = exaBoxNode(_eb_context, aLocal=False)
            try:
                _aNode.mConnect(aHost = _hostname)
                ebLogInfo('Connected to host [{0}]'.format(str(_hostname)))

                _isSunOs = self._checkIfSunOs(_aNode, _hostname)
                ebLogInfo('Result for checking if this is a Sun Os which is no t currently supported - isSunOs[{0}]...'.format(_isSunOs))
                if _isSunOs:
                    ebLogInfo('This is an unsupported OS will not update ntp/dns servers...')
                    continue

                _exaVersion = self._getExadataVersion(_aNode, _hostname)
                ebLogInfo('Exadata version [{0}], checking if version is valid...'.format(str(_exaVersion)))

                _isValidExaVersion = self._validateExaVersion(_aNode, _hostname, _exaVersion)
                if not _isValidExaVersion:
                    ebLogInfo('We should download the correct version for ipconf')
                    self._downloadIpConfTool(_aNode, _hostname)
                else:
                    _ipConfigTool = self._checkIpConfigTool(_aNode, _hostname)
                    ebLogInfo('Check if ipconfig tool exists [{0}]'.format(str(_ipConfigTool)))

                ebLogInfo('Executing ipconfig tool for hostname[{0}]'.format(str(_hostname)))
                self._executeIpConfTool(_aNode, _hostname, _ipConfig, _ntpConfig, _updateIlom)

                _aNode.mDisconnect()
            except Exception as e:
                ebLogCrit('Connection failure aborting NAT setup.')
                ebLogCrit(str(e))
            ebLogInfo('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')

    def _checkIpConfigTool(self, _aNode, _hostname):
        """
            Check if we can use ipconfig tool to change dns/ntp
            :param _aNode: Node in which we are connected
            :param _hostname: Name of the host we are checking
            :return: True if ipconfig tool was found, False otherwise.
        """
        result = True
        _o, _e, _rc = self._executeCommandInNode(_aNode, _hostname, self.SUDO_COMMAND + ' su --command "/usr/local/bin/ipconf -help"')

        for line in _o.readlines():
            ebLogInfo('Result for line [{0}]'.format(str(line)))

        return result

    def _checkIfSunOs(self, _aNode, _hostname):
        """
            Checks if this '_aNode' OS is supported, only Linux is supported right now.

            :param _aNode: Node in which we are connected
            :param _hostname: Name of the host we are checking
            :return: String containing exadata version
        """
        result = None
        _isSunOs = False

        _o, _e, _rc = self._executeCommandInNode(_aNode, _hostname, 'uname -sp')

        if _rc is not None and _rc != 0:
            ebLogWarn('Could NOT check if OS system is valid in node [{0}], return_code[{1}], error_output[{2}], output[{3}]'.format(_hostname, str(_rc), str(_e.readlines()), str(_o.readlines())))
        else:
            for line in _o.readlines():
                result = line.replace('\n','')
            ebLogInfo('Retrieved current exadata OS: [{0}]'.format(str(result)))
            if 'Linux x86_64' not in result and 'Linux sparc64' not in result and 'Linux' not in result:
                _isSunOs = True

        ebLogInfo('Checked OS System in node[{0}] with OS [{1}] isSunOs[{2}]'.format(str(_hostname), str(result), str(_isSunOs)))
        return _isSunOs

    def _getExadataVersion(self, _aNode, _hostname):
        """
            Check exadata version for compatibility using command:
            'exadata_version=$(imageinfo 2>/dev/null | grep -i '^active image version' | awk -F': ' {'print $2'})'

            :param _aNode: Node in which we are connected
            :param _hostname: Name of the host we are checking
            :return: String containing exadata version
        """
        ebLogInfo('Retrieving Exadata Version for Node[{0}]'.format(_hostname))
        version = self._getImageinfoVersionFromCommand(_aNode, _hostname, self.SUDO_COMMAND + ' su - root -c "imageinfo 2>/dev/null | grep -i \'^active image version\' | awk -F\': \' {\'print $2\'}"')

        ebLogInfo('Retrieved version with first command, result [{0}]'.format(version))
        if version is None:
            version = self._getImageinfoVersionFromCommand(_aNode, _hostname, self.SUDO_COMMAND + ' su - root -c "imageinfo 2>/dev/null | grep -i \'^Image version\' | awk -F\': \' {\'print $2\'}"')
            ebLogInfo('Retrieved version with second command, result [{0}]'.format(version))

        ebLogInfo('Overall retrieved version is [{0}]'.format(version))
        return version

    def _getImageinfoVersionFromCommand(self, _aNode, _hostname, _command):
        ebLogInfo('Retrieving Exadata Version for Node[{0}], command[{1}]'.format(_hostname, _command))
        result = None

        # if not self._imageinfoExists(_aNode, _hostname):
        #    ebLogInfo('Imageinfo tool does not exist, could not verify exadata version')
        #    return result

        _o, _e, _rc = self._executeCommandInNode(_aNode, _hostname, _command)

        if _rc is not None and _rc != 0:
            ebLogCrit('Could NOT retrieve exadata version for hostname[{3}] with RC[{0}], and error[{1}] out[{2}] and command[{4}], please check and retry...'.format(str(_rc), str(_e.readlines()), str(_o.readlines()), _hostname, _command))
            return result

        for line in _o.readlines():
            result = line.replace('\n','')
        ebLogInfo('Retrieved current exadata version: [{0}]'.format(str(result)))

        return result

    def _imageinfoExists(self, _aNode, _hostname):
        """
            Check if image info tool exists.
            :param _aNode: Node in which we are connected
            :param _hostname: Name of the host we are checking
            :return: True if tool exists, False otherwise
        """
        exists = False
        result = None
        ebLogInfo('Check if imageinfo tool exists in node[{0}]'.format(_hostname))
        _o, _e, _rc = self._executeCommandInNode(_aNode, _hostname, 'which imageinfo')

        if _rc is not None and _rc != 0:
            ebLogCrit('Could NOT retrieve imageinfo tool for hostname[{3}] with RC[{0}], and error[{1}] out[{2}], please check and retry...'.format(str(_rc), str(_e.readlines()), str(_o.readlines()), _hostname))
            exists = False
        else:
            for line in _o.readlines():
                result = line.replace('\n', '')
            exists = True

        ebLogInfo('Retrieved which imageinfo: [{0}]'.format(str(result)))
        return exists

    def _mGetHostList(self, aCluCtrl):
        _domUs_filtered = []
        if not aCluCtrl.mIsKVM():
            _dom0s, _domUs, _cells, _switches = aCluCtrl.mReturnAllClusterHosts()
        else:
            _dom0s, _domUs, _cells, _ = aCluCtrl.mReturnAllClusterHosts()
            _switches = []

        for _host in _domUs:
            _ctx = get_gcontext()
            if _ctx.mCheckRegEntry('_natHN_' + _host):
                _host = _ctx.mGetRegEntry('_natHN_' + _host)
            _domUs_filtered.append(_host)

        return _dom0s, _domUs_filtered, _cells, _switches

    def _executeCommandInNode(self, _aNode, _hostname, _aCommand):
        ebLogDebug('Trying to execute command[{2}] in node[{0}] - isConnected[{1}]'.format(_hostname, str(_aNode.mIsConnected()), _aCommand))
        if _aNode.mIsConnected():
            _, _o, _e = _aNode.mExecuteCmd(_aCommand)
            _rc = _aNode.mGetCmdExitStatus()

            return _o, _e, _rc

    def _validateExaVersion(self, _aNode, _hostname, _exaVersion):
        ebLogInfo('Validating Exadata Version [{0}]'.format(str(_exaVersion)))
        _isValid = True;

        if not _exaVersion.startswith('20'):
            ebLogInfo('Exadata Version is not valid, should be prior 20.x')
            _isValid = False

        return _isValid

    def _downloadIpConfTool(self, _aNode, _hostname):
        ebLogInfo('Downloading ipconf tool into node [{0}]'.format(_hostname))
        _o, _e, _rc = self._executeCommandInNode(_aNode, _hostname, self.SUDO_COMMAND + ' su - root -c "mkdir -p {0}; wget --output-document={0}/{1} {2}; cd {0}; tar -xf {1}"'.format(self.IPCONF_TOOL_TMP_PATH,self.IPCONF_TOOL_TAR_NAME, self.IPCONF_TOOL_URL))

        if _rc is not None and _rc != 0:
            ebLogCrit('Could NOT download an udpated version of "IPCONF" tool into node [{0}], aborting configuration for this node'.format(_hostname))
            return False
        else:
            ebLogInfo('Downloaded file with ipconf tool with output[{0}]'.format(str(_o.readlines())))

        return True

    def _getNewDnsNtpIp(self, _newIpsConfiguration):
        ebLogInfo('Trying to split ips Configuration from argument [{0}]'.format(str(_newIpsConfiguration)))

        _cpsIpConfig = ''
        _custDnsIpConfig = ''
        _custNtpIpConfig = ''
        if _newIpsConfiguration is not None:
            if 'customer' in _newIpsConfiguration:
                customerData = _newIpsConfiguration['customer']
                _custDnsIpConfig = customerData['customerDnsIp']
                _custNtpIpConfig = customerData['customerNtpIp']
            if 'cps' in _newIpsConfiguration:
                cpsData = _newIpsConfiguration['customer']
                _custIpConfig = cpsData['cpsOneIp'] + ',' +  cpsData['cpsTwoIp']

        ebLogInfo('Retrieved ip for reconfiguration custDnsIpConfig[{0}] - custNtpIpConfig[{1}] - _cpsIpConfig[{2}]'.format(str(_custDnsIpConfig), str(_custNtpIpConfig), str(_cpsIpConfig)))
        return _cpsIpConfig, _custDnsIpConfig, _custNtpIpConfig

    def _executeIpConfTool(self, _aNode, _hostname, _ipConfig, _ntpConfig, _updateIlom):
        ebLogInfo('Executing ipconfig tool for hostname [{0}]'.format(str(_hostname)))
        _dnsConf = _ipConfig
        _ntpConf = _ntpConfig

        if _ntpConfig is None:
            _ntpConf = _ipConfig

        if _updateIlom:
            command = self.SUDO_COMMAND + ' su - root -c "{0}/{1} -update -dns {2} -ntp {3} -ilom-dns {2} -ilom-ntp {3} -nocodes -dry; "'.format(self.IPCONF_TOOL_TMP_PATH, self.IPCONF_TOOL_CMD, _dnsConf, _ntpConf)
        else:
            command = self.SUDO_COMMAND + ' su - root -c "{0}/{1} -update -dns {2} -ntp {3} -nocodes -dry; "'.format(self.IPCONF_TOOL_TMP_PATH, self.IPCONF_TOOL_CMD, _dnsConf, _ntpConf)

        _o, _e, _rc = self._executeCommandInNode(_aNode, _hostname, command)
        if _rc is not None and _rc != 0:
            ebLogCrit('Could NOT execute ipconf tool for node [{0}], the return code is [{1}] output is [{2}] and error [{3}]'.format(_hostname, str(_rc), str(_o.readlines()), str(_e.readlines())))
            return False

        else:
            return True

