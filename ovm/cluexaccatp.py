"""
 Copyright (c) 2020, 2023, Oracle and/or its affiliates.

NAME:
    cluexaccatp.py - ATP parts specific to ExaCC

FUNCTION:
    ATP specifics for OCI-ExaCC and to enable testing while ECRA gets ready

NOTE:

History:

    MODIFIED   (MM/DD/YY)
       diyanez  10/19/20 - 32042031 - OCIEXACC: ADB: MAIN: PYTHON 3
                           COMPATIBILITY ISSUE IN CLUEXACCATP.PY
       vgerard  03/10/20 - add full ATP support (NatVIPs, XML with admin Net)
       vgerard  01/06/20 - Creation 
"""

import json
import os
import copy
import subprocess
import tempfile
import re
import operator
import socket
import ipaddress
from exabox.ovm.bmc import V1OedaXMLRebuilder
from exabox.ovm.AtpUtils import ebAtpUtils
from exabox.core.Context import get_gcontext
from exabox.log.LogMgr import ebLogInfo, ebLogError, ebLogDebug, ebLogWarn
from exabox.core.Node import exaBoxNode

ATPEXACC_NATVIPFILE="/opt/exacloud/atpcc_natvips"

class ebExaCCAtpListener(object):
    
    @staticmethod
    def sExtractInfoFromDomU(aNode):
        """
            Method to extract info for the ATP listener creation

            :param aNode: Connected Node to any domU

            :return: False on error
                on success: dictionnary of 5 RESULTS to form the arguments of
                            sGenerateListenerCommands, see the next function
        """

        _cmd = "cat /etc/oratab | grep '^+ASM.*' | cut -f 2 -d ':'"
        _i, _o, _e = aNode.mExecuteCmd(_cmd)
        _out = _o.readlines()
        if not _out or len(_out) == 0:
            ebLogWarn('*** ORATAB entry not found for grid')
            return False
        # RESULT 1
        _grid_home = _out[0].strip()
        
        _cmd_cidr = "ip route show dev eth0 scope link | cut -d ' ' -f 1"
        _cidr = aNode.mSingleLineOutput(_cmd_cidr)
        try:
            _net_cidr = ipaddress.ip_network(_cidr)
            # RESULT 2 and 3
            _net_addr = str(_net_cidr.network_address)
            _net_mask = str(_net_cidr.netmask)
        except:
            ebLogWarn("Could not extract admin network information from ({}) output: {}".format(_cmd_cidr,_cidr))
            return False

        _cmd_natatpcc = "cat {}".format(ATPEXACC_NATVIPFILE)
        _natatpcc_str = aNode.mSingleLineOutput(_cmd_natatpcc)
        try:
            # RESULT 4
            _natatpcc = json.loads(_natatpcc_str)
        except:
            ebLogWarn("Could not decode NATATP info from ({}) output: {}".format(_cmd_natatpcc, _natatpcc_str))
            return False

        # RESULT 5
        _secListenerPort = ebAtpUtils.mGetExaboxATPOption("sec_listener_port")

        return {'aGridHome':_grid_home, 
                'aAdminNetwork':(_net_addr, _net_mask),
                'aNatVips':_natatpcc,
                'aListenerPort':_secListenerPort}

    @staticmethod
    def sGenerateListenerCommands(aGridHome, aAdminNetwork, aNatVips, aListenerPort=1522):
        """
            Generate commands to create the Admin ATP-CC Listener

            :param str aGridHome: Path to Grid Home ex: "/u01/app/19.0.0.0/grid"
            :param (str,str) aAdminNetwork: Tuple (admin net address, netmask)
                              ex: ("10.31.112.0","255.255.255.0")
            :param [dict] aNatVips: datastructure as returned by sGenerateEtcHostsData
            :param str aListenerPort: Port for AdminVIP listener (default 1522)
            
            :return ([str],[str],[str]): a tuple of list, first list are root commands
                                   second are grid commands, last are final root commands
        """
        _commands = []
        _srvctl = '{}/bin/srvctl'.format(aGridHome)
        _crsctl = '{}/bin/crsctl'.format(aGridHome)
        _adminNet, _adminMask = aAdminNetwork
        _commands += ["{} add network -netnum 2 -subnet {}/{}/eth0"\
                   .format(_srvctl,_adminNet,_adminMask),
                 "{} start res ora.net2.network -unsupported".format(_crsctl)]

        _addVIPs_cmds   = []
        _startVIPs_cmds = []
        for _natDict in aNatVips:
            _clienthn = _natDict['clienthn']
            _natviphn = _natDict['viphn']
            _addVIPs_cmds.append("{} add vip -node {} -netnum 2 -address {}/{}".format(
                                _srvctl, _clienthn, _natviphn, _adminMask ))
            _startVIPs_cmds.append("{} start vip -netnum 2 -node {}".format(
                                   _srvctl,_clienthn))
        # Append first All AddVips, then All Start VIPs
        _commands += _addVIPs_cmds
        _commands += _startVIPs_cmds
        # Name of listener was not changed
        _grid_commands = ["{} add listener -listener LISTENER_BKUP -netnum 2 -endpoints TCP:{} -oraclehome {}"\
                      .format(_srvctl, aListenerPort, aGridHome),
                      "{} start listener -listener LISTENER_BKUP".format(_srvctl)]

        # VGE, Listener Registration function MUST BE CALLED before final grid commands 
        # This has become a lot more complex than initially designed and need to be reviewed
        _final_grid_commands = ["echo \"ALTER SYSTEM REGISTER;\" | sqlplus -s / as sysasm"]
        _final_grid_commands.append("{} modify resourcegroup ora.asmgroup -attr \"START_DEPENDENCIES='weak(global:ora.gns,ora.LISTENER_BKUP.lsnr) dispersion:active(site:type:ora.asmgroup.gtype)'\" -unsupported".format(_crsctl))

        _final_root_commands = ["{} stop cluster -all".format(_crsctl),"{} start cluster -all".format(_crsctl)]

        return (_commands, _grid_commands, _final_grid_commands, _final_root_commands)

    @staticmethod
    # This function is to be called on every domU between grid commands and final_grid commands
    def sRegisterListenerOnBKUPOnly(aGridDomUNode, aListenerPort=1522):
        """
        To be called on every domU between the grid_commands and _final grid commands above
        Reproduce atp.py logic
            :params: aGridDomUNode: a DomU Node connected to grid user
                     aListenerPort: BKUP listener port
        """
        _sid = ebAtpUtils.mGetOracleSid(aGridDomUNode, 'ASM', True)
        # do not use mGetBackupVipFromAtpIni as atp.ini is the pre-namespace mappings
        #_backupVip = ebAtpUtils.mGetBackupVipFromAtpIni(_domU)
        _cmd_run_as_grid="lsnrctl status listener_bkup|grep \"HOST=\"|tr '(' '\n'|grep \"HOST=\"|tr -d ')'|cut -d= -f2"
        _backupVip = None
        _i, _o, _e = aGridDomUNode.mExecuteCmd(_cmd_run_as_grid)
        if _o:
            _out = _o.readlines()
            if _out:
                _backupVip = _out[0].strip()
        if not _backupVip:
            ebLogError("*** ATP ASM Unable To get Backup VIP, will not set local listener")
            return False
        ebLogInfo("*** ATP ASM Listener migration on sid %s " % _sid)
        ebLogInfo("*** ATP ASM Listener migration backupVip %s " % _backupVip)
        # Note:alter system register is done in next block to execute it just once
        # VGENOTE: Took the code as-is from atp.py, refactor should be done
        _cmd_run_as_grid="echo \"ALTER SYSTEM SET LOCAL_LISTENER='(ADDRESS=(PROTOCOL=TCP)(HOST="   +   _backupVip   +   ")(PORT="   +   aListenerPort   +    "))' SCOPE=BOTH SID='"  +     _sid   +    "';\" | sqlplus -s / as sysasm"
        ebLogInfo(" Running %s. " % _cmd_run_as_grid)
        #_expectedOutput =  "System altered."
        _i, _o, _e = aGridDomUNode.mExecuteCmd(_cmd_run_as_grid)
        return True

class ebExaCCAtpEtcHostsNATVIPs(object):

    @staticmethod
    def sGenerateEtcHostsData(aNatHostnames):
        """
            Simple method to generate /etc/hosts dict of entries for all domU VIPs
            @TODO Unit testing this method would require python3 unittest.mock class

            :param iterable aNetHostnames: List of Tuples (ClientHN, Nat FQDN)

            :return: [] on error
                on success [{"ip":<natVIP_IP>,"vipfqdn":<FQDN>,"viphn":<HOSTNAME>},{...}]
        """
        _out = []
        for _client, _nat in aNatHostnames:
            _dotpos = _nat.find('.')
            if _dotpos == -1:
                _vip_name = _nat + '-vip'
            else:
                _vip_name = _nat[:_dotpos] + '-vip' + _nat[_dotpos:]
            try:
                _vipip = socket.gethostbyname(_vip_name)
                _adminip = socket.gethostbyname(_nat)
                _out.append({"ip":_vipip,
                             "vipfqdn":_vip_name,
                             "viphn":_vip_name.split('.')[0],
                             "adminip":_adminip,
                             "clienthn":_client.split('.')[0]})
            except:
                ebLogWarn("Some Nat-VIPs are not resolved ({}), ATP listener and Transparent SSH will NOT BE SETUP".format(_vip_name))
                return []                
        return _out

    @staticmethod
    def sWriteEtcHostsLines(aNode, aNatVips):
        """
            Write the array of lines to /etc/hosts on an existing connection
            AND the marker file:  /opt/exacloud/exaccatp_natvips_enabled

            :param object aNode: Connected domU exaBoxNode
            :param list aNatVips : Result of sExaCCAtpGenerateEtcHostsLines
        """
        # Convert dict to list of /etc/hosts strings lines
        _lines = ["{ip} {vipfqdn} {viphn}".format(**natvip) for natvip in aNatVips]
        # Using \\n, to have the \n string passed to echo -e and interpreted by it
        _single_echo = "echo -e '{}' >> /etc/hosts".format('\\n'.join(_lines))
        aNode.mExecuteCmd(_single_echo)
        aNode.mExecuteCmd("mkdir -p /opt/exacloud")
        aNode.mExecuteCmd("echo '{}' > {}"\
                          .format(json.dumps(aNatVips),ATPEXACC_NATVIPFILE))

class ebExaCCAtpPatchXML(object):
    """
        Class to patch XML for ExaCC ATP:
        A) Set the subtype to EXACC ATP
        B) Clone the Nat network as a top level admin network
    """
    
    def __init__(self, aXML, aDomUList, aDebug):
        self.__oedaXML  = aXML
        # Store short hostname to match OEDA
        self.__domUList = list(map(lambda x: x.split('.')[0], aDomUList))
        self.__debug    = aDebug

    def mExecuteOEDACLI(self, aCMDs):
        """
            Execute OEDA commands
        """
        if True:
            ebLogInfo("***DBG ATPCC: oedaCLI commands: {}".format(aCMDs))

        # is ReadOnly if ALL commands start with LIST
        _read_only = all(map(lambda x: x.strip().split()[0].upper() == 'LIST',aCMDs))
        
        _tmpfile =  tempfile.NamedTemporaryFile(delete=False)
        _tmpfile.write('\n'.join(aCMDs).encode('utf8'))
        _tmpfile.close()

        # For XMLv1 Reinject vmSizes flags (only for WriteOps)
        _xmlV1Reinjector = None
        if not _read_only:
            _xmlV1Reinjector = V1OedaXMLRebuilder()
            _xmlV1Reinjector.SavePropertiesFromTemplate(self.__oedaXML)

        _oedacli_path = os.path.join(get_gcontext().mGetOEDAPath(),'oedacli')
        _cmd = [_oedacli_path,'-j','-c',os.path.abspath(self.__oedaXML),'-f', _tmpfile.name]

        _oedaArgs = get_gcontext().mGetConfigOptions()['oedacli_extra_args'].split(" ")
        if get_gcontext().mGetExaKms().mGetDefaultKeyAlgorithm() == "RSA":
            _oedaArgs.append("--enablersa")

        _cmd = _cmd + _oedaArgs

        if _read_only:
            _cmd.append('-q') # Quiet mode for LIST commands to get clean JSON
        try:
            _ocli_out = subprocess.check_output(_cmd).decode('utf8')
        except subprocess.CalledProcessError as cpe:
            ebLogError("Non Zero return code from oedacli: RETCODE: {}".format(cpe.returncode))
            ebLogError("Dump of faulty commands: {}", aCMDs)
            raise
        finally:
            os.unlink(_tmpfile.name)

        if not _read_only:
            _xmlV1Reinjector.ProcessOedaCliXML(self.__oedaXML)

        return _ocli_out

    def mConvertOEDAOutputToDict(self, aInput):
        """
           A succession of LIST command in OEDA will generate
           [ { ... first command object} ]
           [ { ... second command object}]
           Which is an invalid JSON format, this function add top level braces and colons
           [
               [{....}],
               [{....}]
           ]
        """

        # Strip eventual Warnings
        _first_pos = 0
        delayed_start = re.search(r'\[\s*\{', aInput)
        if delayed_start:
           _first_pos = delayed_start.start()

        # find all closing brackets, 
        # followed by any number of space THEN by [ or { (<opening)
        # And replace the ]<anyspaces><opening> by ],<opening(group 1)>
        
        _json_str = '[' + re.sub(r'\]\s*([\[\{])',r'],\g<1>', aInput[_first_pos:]) + ']'
        _out = {}
        
        try:
           _out = json.loads(_json_str)
        except:
            ebLogError('*** ATPCC, oedacli output JSON conversion error, check output: \n{}'.format(_json_str))
            raise

        return _out


    def mGetNatNetworksInfo(self):
        # Generate one list command for each domU Hostname
        _cmdsList = \
            list(map('list networks where hostname={} networktype=client'.format,
                self.__domUList))

        # OEDA will generate an invalid json output
        _oeda_out = self.mExecuteOEDACLI(_cmdsList)
        _dict_out = self.mConvertOEDAOutputToDict(_oeda_out)

        # Return list of all client network objects
        return _dict_out
    
    def mGenNewAdminNetworksCmds(self):

        _nat_nets = self.mGetNatNetworksInfo()
        # Template keys must match the OEDA LIST NETWORKS OUTPUT as we will
        # use directly the dict output to format this string (** operator)
        _template = "ADD NETWORK NETWORKTYPE=ADMIN HOSTNAME={nathostName} "\
                    "IP={natipAddress} NETMASK={natnetMask} "\
                    "DOMAINNAME={natdomainName} MASTER=eth0 "\
                    "WHERE hostname={hostName}"
        
        # Generate array of all add network commands
        _out = []
        for _net in _nat_nets:
            _out += [_template.format(**_net[0]),'save action']

        return _out

    def mPatchXML(self):
        
        _cmds = ['reset actions','alter es PAAS = True subtype = EXACCATP'] + \
                ['save action'] + self.mGenNewAdminNetworksCmds()   + \
                ['merge actions force','save file']
        self.mExecuteOEDACLI(_cmds)


class ebExaCCAtpSimulatePayload(object):
    """ Static class to manage ATP specific parts of ExaCCOCI """
    def __init__(self, aPayload, aCmd):
        """
            Temporary class until ECRA support is there 
            @TODO TO BE REMOVED 
 
            :param dict aPayload: Payload from ECRA with AutonomousDB:N 
            :param str aCmd: clucontrol Command (vmgi_xxxx,db_install...)
        """
        self.__payload = aPayload
        self.__cmd = aCmd
        self.__atp_force = ebAtpUtils.mCheckExaboxConfigOption('atp_force') == "True"
        self.__atp_dbaas_payload = ebAtpUtils.mCheckExaboxConfigOption('atp_force_dbaas_payload')

    def mIsATPSimulateEnabled(self):
        if not self.__atp_force:
            return False

        if self.__cmd in ('vmgi_install,db_install,createservice,info,env_info'):
            if 'jsonconf' in self.__payload:
                return True
        return False

    def mInjectATPfromAgentWorkaround(self):
        """
            :return Payload with AutonomousDb set to Y and ATP parts
            :rtype dict
        """
        
        _jconf = self.__payload['jsonconf']

        _atp_section = {"AutonomousDb":"Y",
            "dbSystemOCID": "ocid1.autonomousexainfrastructure.oc1.sea.abzwkljsc6uhzgjkpcuqu5rc65q7g7drvkmeyreljuinr3kmxwwuj7rnvbxa",
            "whitelist": {
              "client": {
                "protocol": {
                  "tcp": [
                    "@1521@in",
                    "@1521@out",
                    "@2484@in",
                    "@2484@out",
                    "@443@in",
                    "@443@out",
                    "@6200@in",
                    "@6200@out"
                  ]
               }
             }}}

        if not 'atp' in _jconf:
            _jconf['atp'] = _atp_section
        else:
            _jconf['atp']['AutonomousDb'] = "Y" #Always Y, but only override client
            if not 'whitelist' in _jconf['atp']:
                _jconf['atp']['whitelist'] = _atp_section['whitelist']

        #DBAAS Payload (either minimal or from file)
        if "dbaas_api" in _jconf and "params" in _jconf["dbaas_api"]:
            if self.__atp_dbaas_payload:
                if os.path.exists(self.__atp_dbaas_payload):
                    self.mInjectDBAASPayload(_jconf['dbaas_api'])
                else:
                    raise ValueError('File {} does not exists'.format(self.__atp_dbaas_payload))
            else:
                _jconf['dbaas_api']['params']['atp'] = {"enabled":"True"}
        
        #Force 19000 as DB version for now
        if self.__cmd == 'db_install' and "dbParams" in _jconf:
            _jconf["dbParams"]["version"] = "19000"
 
        return self.__payload

    def mInjectDBAASPayload(self, aDBAASPayload):
        with open(self.__atp_dbaas_payload) as _fd:
            _atp_dbaas_payload = json.load(_fd)
        aDBAASPayload['params'].update(_atp_dbaas_payload)
        


