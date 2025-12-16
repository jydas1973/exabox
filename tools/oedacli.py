"""
$Header:

 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    oedacli - 

FUNCTION:
    oedacli module for handling elastic functions

NOTE:
    None

History:

    MODIFIED   (MM/DD/YY)
    prsshukl   11/20/25 - Bug 38675257 - EXADBXS PROVISIONING FAILING IN
                          FETCHUPDATEDXMLFROMEXACLOUD
    mpedapro   11/14/25 - Enh::38235082 xml patching changes for sriov
    pbellary   10/30/25 - Enh 38596691 - ASM/EXASCALE TO SUPPORT ADD NODE WITH EDV IMAGE 
    scoral     10/28/25 - Enh 38452359: Support separate "admin" network
                          section in payload.
    aararora   07/30/25 - ER 38132942: Single stack support for ipv6
    dekuckre   07/18/25 - Remove mCreateGuest
    dekuckre   06/17/25 - 38036039: Add mCreateGuest
    pbellary   05/26/25 - Bug 37982976 - EXACC:ELASTIC INFO:DELETE CELL SHOULD REMOVE CELL FROM STORAGEPOOL IF EXISTS
    pbellary   05/15/25 - Enh 37698277 - EXASCALE - CREATE SERVICE FLOW TO SUPPORT VM STORAGE ON EDV OF IMAGE VAULT 
    prsshukl   04/25/25 - Bug 37861890 - EXADB-XS: EXACLOUD: ADD COMPUTE IS
                          FAILING IN OEDA
    pbellary   04/16/25 - Bug 37778364: CONFIGURE EXASCALE IS FAILING IN X11 ENV FOR EXTREME FLASH STORAGE TYPES
    prsshukl   01/29/25 - ER 36981808 - EXACS | ADBS | ELASTIC COMPUTE AND CELL
                          OPERATION ENHANCEMENTS -> IMPLEMENT PHASE 2
    pbellary   01/23/25 - Bug 37506231 - EXACALE:CLUSTER PROVISIONING FAILING DUE TO EDV SERVICES STARTUP FAILURE
    aararora   12/18/24 - ER 37402747: Add NTP and DNS entries in xml
    aararora   10/18/24 - Bug 37186358: Ignore natvlan and natgateway if not
                          found in payload
    aararora   09/26/24 - Bug 37105761: Oedacli command is failing for
                          elastic_info call in ipv6
    prsshukl   09/02/24 - ER 36553793 - EXACS | ADBS | ELASTIC CELL AND COMPUTE
                          OPERATION ENHANCEMENTS -> IMPLEMENT PHASE 1
    pbellary   08/02/24 - Bug 36911874 - EXASCALE: CONFIGURE EXISTING INFRA TO USE EXASCALE - OEDA : OEDA STEP 3 FAILED
    aararora   04/29/24 - ER 36485120: Support IPv6 in exacloud
    jesandov   02/02/24 - 36257956: Add NATVLANID in Clone Guest
    dekuckre   09/29/23 - XbranchMerge dekuckre_bug-35825283 from
                          st_ecs_23.3.1.0.0
    dekuckre   09/22/23 - 35825283: Patch the xml with image version in case of KVM or Xen based OCIExaCC systems
    pbellary   06/06/23 - ENH 35445802: EXACS X9M - ADD SUPPORT FOR 2TB MEMORY IN X9M
    aararora   03/03/23 - Add DR network during elastic compute addition.
    aararora   01/04/23 - Update DR Network slaves to patched xml.
    pbellary   10/17/22 - Bug 34686909 - FOR HETERO ENV, PATCH THE XML WITH CORRECT INTERFACES
    dekuckre   09/29/22 - 34653200: Add RESET ACTIONS after deploy.
    dekuckre   06/10/22 - 34252376: Include more oedacli substeps
    akkar      05/06/22 - bandit fix 34004584
    dekuckre   05/17/21 - 34093987: Include sub step capability in add cell operation
    ajayasin   12/09/21 - Adding call back after create user
    dekuckre   05/04/21 - 32563027: Update APIs to account for add/delete multple compute 
    pverma     03/23/21 - Log oedacli script for debugging purposes
    pverma     03/11/21 - Add aWait param to mAlterCluster
    siyarlag   03/03/21 - 32214702: multiple image version support
    jlombera   02/26/21 - Bug 32536707: add client network's VLANTAG to patched
                          XML
    dekuckre   12/15/20 - 32253587: Update mDropCell
    dekuckre   10/23/20 - 31992073: Add mDelNode. Update mDelCell, mDropCell
    dekuckre   10/30/20 - 32076487: Add capability for multi-cell add-delete
    jesandov   08/27/20 - XbranchMerge jesandov_bug-31806249 from
                          st_ecs_20.2.1.0.0rel
    dekuckre   08/26/20 - XbranchMerge dekuckre_bug-31753841 from
                          st_ecs_20.2.1.0.0rel
    dekuckre   08/20/20 - Fix 31753841
    dekuckre   06/15/20 - 31486312: Update error handling of oedacli cmds.
    dekuckre   05/22/20 - 31389081: Make Add Dom0 KVM compatible
    dekuckre   05/19/20 - 31367445: enable alter cluster for patching xml
    dekuckre   05/08/20 - 31282887: Include delete cell capability
    File created.
"""

#!/usr/bin/python

import subprocess
import json
import re
import os
from exabox.tools.AttributeWrapper import wrapStrBytesFunctions
from exabox.core.Context import get_gcontext
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogVerbose
from exabox.core.Error import ExacloudRuntimeError
from exabox.ovm.cluacceleratednetwork import ebCluAcceleratedNetwork
import shlex

from exabox.network.NetworkUtils import NetworkUtils

ENABLED_OEDACLI_PATCH = True

class ebOedacli(object):
    """ 
       PURE OEDACLI HANDLER
    """
    OEDACLI_PATH = None
    oeda_xml = None
    def __init__(self, oedaclipath=None, save_dir='/tmp'):
        if oedaclipath and os.path.isfile(oedaclipath):
            self.OEDACLI_PATH = oedaclipath
        elif os.path.isfile('/scratch/jopatino/tmp/linux-x64/oedacli'):
            self.OEDACLI_PATH = '/scratch/jopatino/tmp/linux-x64/oedacli'
        elif os.path.isfile(os.getcwd() + '/oeda/oedacli'):
            self.OEDACLI_PATH = os.getcwd() + '/oeda/oedacli'
        else:
            raise ExacloudRuntimeError(1,2,"Invalid oedacli path:{}".format(oedaclipath))
        self._oedacli_script = []
        self._no_actions = True
        self.save_dir = save_dir

    def oc_cmd(self, command, arguments=None, where=None):
        if not arguments:
            arguments = {}
        arguments = {k:v for k,v in arguments.items() if v is not None}
        if where is None:
            where = {}
        where = {k:v for k,v in where.items() if v is not None}
        arguments_str = self._paramfmt(arguments)
        where_str = self._paramfmt(where)
        action = '%s %s' % (command, arguments_str)
        if where_str:
            action += ' WHERE ' + where_str
        self._oedacli_script.append(action)
        return action

    def comment(self, comment):
        fmt_comment = '# ' + re.sub("\n","\n# ",comment)
        self._oedacli_script.append(fmt_comment)

    def getJsonData(self, xmlfile=None):
        self.xmlfile = os.path.abspath(xmlfile)
        structures = {}
        # initialize main structures
        structs = ['LOAD FILE NAME=%s' % (self.xmlfile),
                   'LIST MACHINES',
                   'LIST SCANS',
                   'LIST CLUSTERS',
                   'LIST VIPS',
                   'LIST NETWORKS',
                   'LIST SWITCHES',
                   'LIST DATABASEHOMES',
                   'LIST DATABASES',
                   'LIST DISKGROUPS',
                   'LIST RACKS']
        out = self._raw_oedacliscript(structs).split('oedacli>')
        structures['machine'] = json.loads(out[2][out[2].find('['):])
        structures['scan'] = json.loads(out[3][out[3].find('['):])
        structures['cluster'] = json.loads(out[4][out[4].find('['):])
        structures['vip'] = json.loads(out[5][out[5].find('['):])
        structures['network'] = json.loads(out[6][out[6].find('['):])
        structures['switch'] = json.loads(out[7][out[7].find('['):])
        structures['databaseHome'] = json.loads(out[8][out[8].find('['):])
        structures['database'] = json.loads(out[9][out[9].find('['):])
        structures['diskGroup'] = json.loads(out[10][out[10].find('['):])
        structures['racks'] = json.loads(out[11][out[11].find('['):])
        return structures

    def _paramfmt(self, params=None):
        param_lst = [key + '="' + params[key] + '"' for key in params]
        if len(param_lst) == 0:
            return ''
        return ' '.join(param_lst)
    
    def save_action(self):
        self._no_actions = False
        self._oedacli_script.append('SAVE ACTION')

    def merge_actions(self, aForce=False):
        self._no_actions = False
        if aForce:
            self._oedacli_script.append('MERGE ACTIONS FORCE')
        else:
            self._oedacli_script.append('MERGE ACTIONS')

    def run_oedacli(self, source=None, save_path=None, script_path=None, deploy=False, resetActions=True):
        self._oedacli_script.insert(0, 'LOAD FILE NAME=%s' % (os.path.abspath(source)))

        if self._no_actions:
            ebLogInfo("OEDAie No oedacli actions")
        else:
            if deploy:
                self._oedacli_script.append('MERGE ACTIONS')
                self._oedacli_script.append('DEPLOY ACTIONS')
                self._oedacli_script.append('RESET ACTIONS')
            else:
                self._oedacli_script.append('MERGE ACTIONS FORCE')
                if resetActions:
                    self._oedacli_script.append('RESET ACTIONS')
        if save_path is not None:
            self._oedacli_script.append('SAVE FILE NAME=%s' % os.path.abspath((save_path)))
        if script_path is not None:
            with open(script_path, 'w') as f:
                f.write('\n'.join(self._oedacli_script))

        ebLogInfo(f"oedacli script: {self._oedacli_script}")

        stdo = self._raw_oedacliscript(self._oedacli_script)
        # clean script buffer
        self._oedacli_script = []
        return stdo
    #
    # oedacli interaciton functions
    #
    def _raw_oedacliscript(self, occmds):
        cmd = self.OEDACLI_PATH + ' -j {0}'.format(get_gcontext().mGetConfigOptions()["oedacli_extra_args"])
        if get_gcontext().mGetExaKms().mGetDefaultKeyAlgorithm() == "RSA":
            cmd = f"{cmd} --enablersa"
        cmd = shlex.split(cmd)
        #occmds = [exp for exp in occmds if not exp.startswith('#')]
        script = '\n'.join(occmds) + '\n'
        out = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdo, stde = wrapStrBytesFunctions(out).communicate(input=script.encode('utf8'))
        # FIXME: oedacli does not report returncode if errors during merge
        if 'ERROR:' in stdo or 'ERROR :' in stdo or out.returncode !=0 :
            if not os.path.exists(self.save_dir):
                os.makedirs(self.save_dir)
            open(self.save_dir + '/out.err', 'w+').write(stdo)
            ebLogError("oedacli errors found:")
            ebLogError("\n".join([line.strip() for line in stdo.split('\n') if 'ERROR' in line]))
            raise ExacloudRuntimeError(1,1,'OEDAie Errors found in oedacli script execution')
        return stdo


class OedacliCmdMgr(object):

    def __init__(self, aOedaCli, aSaveDir): 
        self.oxm = ebOedacli(aOedaCli, aSaveDir)

    def mDeleteDBHomes(self, aDomUList, aSrcXml, aDestXml):
        """
        Remove DB Homes present on node
        :param aDomUList: domu list
        :param aSrcXml
        :param aDestXml
        :return:
        """
        _list = ','.join(aDomUList)

        self.oxm.oc_cmd(command='DELETE GUEST',
                        where={'SRCNAMES':str(_list), 'STEPNAME':'EXTEND_DBHOME'})
        self.oxm.save_action()
        self.oxm.run_oedacli(aSrcXml, aDestXml, None, True)
    
    def mDeleteClusterNode(self, aDomUList, aSrcXml, aDestXml, aStepName):
        """
        Remove node from clusterware
        :param aDomUList: domu list
        :param aSrcXml
        :param aDestXml
        :param aStepName
        :return:
        """
        _stepname = aStepName
        _list = ','.join(aDomUList)

        self.oxm.oc_cmd(command='DELETE GUEST',
                        where={'SRCNAMES':str(_list), 'STEPNAME':_stepname})
        self.oxm.save_action()
        self.oxm.run_oedacli(aSrcXml, aDestXml, None, True)

    def mUpdateDnsNtpServers(self, aHostName, aSrcXml, aDestXml, aDnsServers=[], aNtpServers=[], aDeploy=False):
        _dnsServers = aDnsServers
        _ntpServers = aNtpServers
        _host = aHostName
        _srcXML = aSrcXml
        _destXML = aDestXml
        if _dnsServers:
            _dns_servers = ','.join(_dnsServers)
        if _ntpServers:
            _ntp_servers = ','.join(_ntpServers)
        if _dnsServers and _ntpServers:
            self.oxm.oc_cmd(command=f"ALTER machine ntpservers='{_ntp_servers}' dnsservers='{_dns_servers}'",
                            where={'hostname':str(_host)})
        elif _dnsServers:
            self.oxm.oc_cmd(command=f"ALTER machine dnsservers='{_dns_servers}'",
                            where={'hostname':str(_host)})
        elif _ntpServers:
            self.oxm.oc_cmd(command=f"ALTER machine ntpservers='{_ntp_servers}'",
                            where={'hostname':str(_host)})
        self.oxm.save_action()
        self.oxm.run_oedacli(aSrcXml, aDestXml, None, aDeploy)

    def mUpdateNetworkSlaves(self, aSlaves, aID, aHostname, aNetworkType, aSrcXml, aDestXml, aBridge=None):
        _slaves = ','.join(aSlaves)
        _id = aID
        _host = aHostname
        _type = aNetworkType

        if aBridge:
            self.oxm.oc_cmd(command=f'ALTER NETWORK NETWORKBRIDGE={aBridge} SLAVE="{str(_slaves)}"',
                            where={'ID':str(_id), 'HOSTNAME':str(_host), 'NETWORKTYPE':str(_type)})
        else:
            self.oxm.oc_cmd(command=f'ALTER NETWORK SLAVE="{str(_slaves)}"',
                            where={'ID':str(_id), 'HOSTNAME':str(_host), 'NETWORKTYPE':str(_type)})
        self.oxm.save_action()
        self.oxm.run_oedacli(aSrcXml, aDestXml, None, False)

    def mUpdatePhysicalMemory(self, aPhysicalMem, aClusterID, aHostType, aSrcXml, aDestXml):
        _physical_mem = aPhysicalMem
        _id = aClusterID
        _type = aHostType

        self.oxm.oc_cmd(command=f'ALTER MACHINES PHYSICALMEMORYSIZE={_physical_mem}',
                            where={'CLUSTERID':str(_id), 'TYPE':str(_type)})

        self.oxm.save_action()
        self.oxm.run_oedacli(aSrcXml, aDestXml, None, False)

    def mUpdateVirtualMemory(self, aVMem, aClusterID, aSrcXml, aDestXml):
        _vmem = aVMem
        _id = aClusterID

        self.oxm.oc_cmd(command=f'ALTER CLUSTER VMEM={_vmem}', where={'CLUSTERID':str(_id)})

        self.oxm.save_action()
        self.oxm.run_oedacli(aSrcXml, aDestXml, None, False)

    def mUpdateGIHome(self, aCluName, aGIVersion, aGIHOME, aSrcXml, aDestXml):
        _clustername = aCluName
        _gi_version = aGIVersion
        _gi_home = aGIHOME

        self.oxm.oc_cmd(command=f"ALTER CLUSTER GIHOMELOC={_gi_home}  WHERE CLUSTERNAME='{_clustername}' ")

        self.oxm.save_action()
        self.oxm.run_oedacli(aSrcXml, aDestXml, None, False)

    def mUpdateClusterName(self, aCluName, aClusterID, aSrcXml, aDestXml):
        _clustername = aCluName
        _id = aClusterID

        self.oxm.oc_cmd(command=f"ALTER CLUSTER CLUSTERNAME={_clustername}", where={'CLUSTERID':str(_id)})

        self.oxm.save_action()
        self.oxm.run_oedacli(aSrcXml, aDestXml, None, False)

    def mUpdateDiskGroupName(self, aNewDiskGroupName, aDiskGroupId, aSrcXml, aDestXml):
        _newdiskgroupName = aNewDiskGroupName
        _id = aDiskGroupId

        self.oxm.oc_cmd(command=f"ALTER DISKGROUP DISKGROUPNAME={_newdiskgroupName}", where={'ID':str(_id)})

        self.oxm.save_action()
        self.oxm.run_oedacli(aSrcXml, aDestXml, None, False)

    def mUpdateDiskGroupGriddiskPrefix(self, aNewDiskGroupName, aGriddiskPrefix, aDiskGroupId, aSrcXml, aDestXml):
        _newdiskgroupName = aNewDiskGroupName
        _griddiskPrefix = aGriddiskPrefix
        _id = aDiskGroupId

        self.oxm.oc_cmd(command=f"ALTER DISKGROUP DISKGROUPNAME={_newdiskgroupName} GRIDDISKPREFIX={_griddiskPrefix}", where={'ID':str(_id)})

        self.oxm.save_action()
        self.oxm.run_oedacli(aSrcXml, aDestXml, None, False)

    def mVMOperation(self, aDomu, aSrcXml, aDestXml, aAction):
        """
        DomU VM Operations : Start, Stop, Restart, Delete
        :param aDomu: domu 
        :param aAction: start|stop|restart|delete 
        :return:
        """
        if aAction.lower() == 'delete':
            _command = self.oxm.oc_cmd(command='DELETE GUEST',
                                       where={'SRCNAME':str(aDomu), 'STEPNAME':'CREATE_GUEST'})
        else:
            _command = self.oxm.oc_cmd(command='ALTER MACHINE ACTION=%s' % (aAction.upper()), where={'HOSTNAME':str(aDomu)})
        ebLogInfo("Running oedacli command : %s" % (_command))
        self.oxm.save_action()
        self.oxm.run_oedacli(aSrcXml, aDestXml, None, True)

    def mDelNode(self, aDomU, aDom0, aSrcXml, aDestXml, aDeploy=True):

        if aDomU:
            self.oxm.oc_cmd(command='DELETE GUEST', where={'SRCNAME':str(aDomU)})
            self.oxm.save_action()

        if aDom0:
            self.oxm.oc_cmd(command='DELETE COMPUTE', where={'SRCNAME':str(aDom0)})
            self.oxm.save_action()

        self.oxm.run_oedacli(aSrcXml, aDestXml, None, aDeploy)

    def mBuildCloneCompute(self, aSrcDom0, aSrcXml, aDestXml, aJson, aKVM=False):
        """
        Add Dom0 TO XML
        :param aSrcDom0: dom0
        :return:
        """
        _srcdom0 = aSrcDom0
        _json = aJson

        #COMPUTE COMMANDS
        self.oxm.oc_cmd(command='CLONE COMPUTE SRCNAME=%s TGTNAME=%s' % (_srcdom0, _json['dom0']['admin']['fqdn']))

        if aKVM:
            self.oxm.oc_cmd(command='SET ADMINNET NAME=%s, IP=%s GATEWAY=\'%s\' NETMASK=\'%s\'' % (_json['dom0']['admin']['fqdn'], _json['dom0']['admin']['ipaddr'], _json['dom0']['admin']['gateway'], _json['dom0']['admin']['netmask']))
        else:
            self.oxm.oc_cmd(command='SET ADMINNET NAME=%s, IP=%s' % (_json['dom0']['admin']['fqdn'], _json['dom0']['admin']['ipaddr']))

        self.oxm.oc_cmd(command='SET PRIVNET NAME1=%s, IP1=%s' % (_json['dom0']['priv1']['fqdn'], _json['dom0']['priv1']['ipaddr']))
        self.oxm.oc_cmd(command='SET PRIVNET NAME2=%s, IP2=%s' % (_json['dom0']['priv2']['fqdn'], _json['dom0']['priv2']['ipaddr']))

        if aKVM:
            self.oxm.oc_cmd(command='SET ILOMNET NAME=%s, IP=%s GATEWAY=\'%s\' NETMASK=\'%s\'' % (_json['dom0']['ilom']['fqdn'], _json['dom0']['ilom']['ipaddr'], _json['dom0']['ilom']['gateway'], _json['dom0']['ilom']['netmask']))
        else:
            self.oxm.oc_cmd(command='SET ILOMNET NAME=%s, IP=%s' % (_json['dom0']['ilom']['fqdn'], _json['dom0']['ilom']['ipaddr']))

        self.oxm.oc_cmd(command='SET RACK NUM=%s, ULOC=%s' % (_json['dom0']['rack_num'], _json['dom0']['uloc']))

    def mSetNetwork(self, aJson, aNetType='client'):
        _net_type_mapping = {"client": "CLIENTNET", "backup": "BACKUPNET", "vip": "VIPNET"}
        _json = aJson
        _ip_net = None
        if 'ipaddr' in _json['domU'][aNetType] and _json['domU'][aNetType]['ipaddr'] != "0.0.0.0":
            _ip_net = _json['domU'][aNetType]['ipaddr']
        if _ip_net:
            self.oxm.oc_cmd(command=f'SET {_net_type_mapping[aNetType]} NAME=%s, IP=%s' % (_json['domU'][aNetType]['fqdn'], _ip_net))

    def mBuildCloneGuest(self, aSrcDomU, aNewDomU, aSrcXml, aDestXml, aJson):
        """
        Add DomU TO XML
        :param aSrcDomU: domU
        :return:
        """
        _srcdomU = aSrcDomU
        _newdomU = aNewDomU
        _json = aJson

        #GUEST COMMANDS
        self.oxm.oc_cmd(command=f"CLONE GUEST SRCNAME='{_srcdomU}' TGTNAME='{_newdomU}'")
        self.oxm.oc_cmd(command='SET PARENT NAME=%s' % _json['dom0']['hostname'])

        if _json['domU']['admin']:
            if 'ipaddr' in _json['domU']['admin']:
                self.oxm.oc_cmd(command='SET ADMINNET NAME=%s, IP=%s' % (_json['domU']['admin']['fqdn'], _json['domU']['admin']['ipaddr']))
            else:
                self.oxm.oc_cmd(command='SET ADMINNET NAME=%s'% (_json['domU']['admin']['fqdn']))

        if "natip" in _json['domU']['client']:

            _optionalArgs = ""

            if "natvlantag" in _json['domU']['client']:
                _optionalArgs += f", NATVLANID=%s" % _json['domU']['client']['natvlantag']

            if "natgateway" in _json['domU']['client']:
                _optionalArgs += f", NATGATEWAY=%s" % _json['domU']['client']['natgateway']

            _domU_natip = (_json['domU'].get('admin') or {}).get('ipaddr')
            _domU_nathostname = (_json['domU'].get('admin') or {}).get('hostname')
            _domU_natdomainname = (_json['domU'].get('admin') or {}).get('domainname')
            _domU_natnetmask = (_json['domU'].get('admin') or {}).get('netmask')
            self.oxm.oc_cmd(command='SET CLIENTNET NAME=%s, IP=%s, NATIP=%s, NATHOSTNAME=%s, NATNETMASK=%s, NATDOMAINNAME=%s %s' % (\
                _json['domU']['client']['fqdn'], \
                _json['domU']['client']['ipaddr'], \
                _json['domU']['client']['natip'] if _domU_natip is None else _domU_natip, \
                _json['domU']['client']['nathostname'] if _domU_nathostname is None else _domU_nathostname, \
                _json['domU']['client']['natnetmask'] if _domU_natnetmask is None else _domU_natnetmask, \
                _json['domU']['client']['natdomain'] if _domU_natdomainname is None else _domU_natdomainname, \
                _optionalArgs))
        else:
            self.mSetNetwork(_json)

        if ('priv1' in _json['domU'].keys()) and ('priv2' in _json['domU'].keys()) and _json['domU']['priv1'] and _json['domU']['priv2']:
            self.oxm.oc_cmd(command='SET PRIVNET NAME1=%s, IP1=%s' % (_json['domU']['priv1']['fqdn'], _json['domU']['priv1']['ipaddr']))
            self.oxm.oc_cmd(command='SET PRIVNET NAME2=%s, IP2=%s' % (_json['domU']['priv2']['fqdn'], _json['domU']['priv2']['ipaddr']))
        self.mSetNetwork(_json, aNetType='backup')
        if ('interconnect1' in _json['domU'].keys()) and ('interconnect2' in _json['domU'].keys()) and _json['domU']['interconnect1'] and _json['domU']['interconnect2']:
            self.oxm.oc_cmd(command='SET INTERCONNECT NAME1=%s, IP1=%s' % (_json['domU']['interconnect1']['fqdn'], _json['domU']['interconnect1']['ipaddr']))
            self.oxm.oc_cmd(command='SET INTERCONNECT NAME2=%s, IP2=%s' % (_json['domU']['interconnect2']['fqdn'], _json['domU']['interconnect2']['ipaddr']))
        self.mSetNetwork(_json, aNetType='vip')

    def mBuildCloneCell(self, aSrcCell, aJson, aKVM=False):
        """
        Add CELL TO XML
        :param aSrcCell: cell
        :return:
        """
        _srccell = aSrcCell
        _json = aJson

        #CELL COMMANDS
        if aKVM:
            # User clone newcell cmd in KVM env.
            self.oxm.oc_cmd(command=f"CLONE NEWCELL SRCNAME='{_srccell}' TGTNAME='{_json['admin']['fqdn']}'")
            # Set gateway and netmask for Admin network in KVM env.
            self.oxm.oc_cmd(command=f"SET ADMINNET NAME='{_json['admin']['fqdn']}', IP='{_json['admin']['ipaddr']}' gateway='{_json['admin']['gateway']}' netmask='{_json['admin']['netmask']}'")
        else:
            # User clone cell cmd in non kvm (XEN env).
            self.oxm.oc_cmd(command=f"CLONE CELL SRCNAME='{_srccell}' TGTNAME='{_json['admin']['fqdn']}'")
            self.oxm.oc_cmd(command=f"SET ADMINNET NAME='{_json['admin']['fqdn']}', IP='{_json['admin']['ipaddr']}'")
        self.oxm.oc_cmd(command=f"SET PRIVNET NAME1='{_json['priv1']['fqdn']}', IP1='{_json['priv1']['ipaddr']}'")
        self.oxm.oc_cmd(command=f"SET PRIVNET NAME2='{_json['priv2']['fqdn']}', IP2='{_json['priv2']['ipaddr']}'")
        if aKVM:
            # Set gateway and netmask for ILOM in KVM env.
            self.oxm.oc_cmd(command=f"SET ILOMNET NAME='{_json['ilom']['fqdn']}', IP='{_json['ilom']['ipaddr']}' gateway='{_json['admin']['gateway']}' netmask='{_json['admin']['netmask']}'")
        else:
            self.oxm.oc_cmd(command=f"SET ILOMNET NAME='{_json['ilom']['fqdn']}', IP='{_json['ilom']['ipaddr']}'")
        self.oxm.oc_cmd(command=f"SET RACK NUM={_json['rack_num']} ULOC={_json['uloc']}")

    def mBuildMultipleGuests(self, aDomUList, aSrcXml, aDestXml, aStepName):
        """                                                                                                                                    
        Add DomUs to existing cluster
        :param aDomUList
        :param aSrcXml
        :param aDestXml                                                                                                                  
        :param aStepName
        :return:                                                                                                                               
        """   

        _guestlist = ','.join(aDomUList)
        _stepname = aStepName

        #COMPUTE COMMANDS
        self.oxm.oc_cmd(command=f"CLONE GUEST TGTNAMES='{_guestlist}' WHERE STEPNAME='{_stepname}'")
        self.oxm.save_action()
        self.oxm.run_oedacli(aSrcXml, aDestXml, None, True)

    def mAlterCluster(self, aCellList, aCluName, aOperation, aPower, aWait, aStep=None):

        """
        mAlterCluster: Alter cluster where we can add cells / drop cells
        aCellList: cell list
        aCluName: clustername
        aOperation: operation (ADDCELLS/DROPCELLS) 
        aPower: rebalance power to be used in the operation.
        """

        _celllist = ' '.join(aCellList)
        _clustername = aCluName
        _operation = aOperation
        _power = aPower
        _wait = aWait
        if aStep:
            _step_clause = f"STEPNAME={aStep}"
        else:
            _step_clause = ""

        if _wait == 'false':
            self.oxm.oc_cmd(command=f"ALTER CLUSTER {_operation}='{_celllist}' POWER={_power}, WAIT='{_wait}' WHERE CLUSTERNAME='{_clustername}' {_step_clause}")
        else:
            self.oxm.oc_cmd(command=f"ALTER CLUSTER {_operation}='{_celllist}' POWER={_power} WHERE CLUSTERNAME='{_clustername}' {_step_clause}")

    def mAlterStoragePool(self, aCellList, aOperation, aPoolName="hcpool"):
        """
        mAlterStoragePool: Alter cluster where we can add cells / drop cells
        aCellList: cell list
        aCluName: clustername
        aOperation: operation (ADDCELLS/DROPCELLS)
        """
        _celllist = ' '.join(aCellList)
        _operation = aOperation
        _pool_name = aPoolName

        self.oxm.oc_cmd(command=f"ALTER STORAGEPOOL {_operation}='{_celllist}' WHERE NAME='{_pool_name}' ")

    def mAddDom0(self, aSrcDom0, aSrcXml, aDestXml, aJson, aKVM=False, aResetActions=True):
        """
        Add Dom0
        :param aSrcDom0: dom0
        :return:
        """
        _srcdom0 = aSrcDom0
        _json = aJson
        _kvm = aKVM

        self.mBuildCloneCompute(_srcdom0, aSrcXml, aDestXml, _json, _kvm)
        self.oxm.save_action()
        self.oxm.run_oedacli(aSrcXml, aDestXml, None, False, aResetActions)

    def mAddNetwork(self, aNetworkDict, aSlaves, aBridge, aMaster, aNetworkType, aDomuHostname):
        """
        Add Network in the DOMU
        :param aNetworkDict: Payload dict with network information
        :param aSlaves: Comma separated slave interfaces
        :param aBridge: Bridge name
        :param aMaster: Master interface name
        :param aNetworkType: Network type information
        :param aDomuHostname: DOMU hostname information for which the network is added
        """
        _json = aNetworkDict
        _net_slaves = aSlaves
        _bridge = aBridge
        _master = aMaster
        _network_type = aNetworkType
        _domu_hostname = aDomuHostname
        _net_hostname = _json['fqdn'].split('.')[0]
        _net_domainname = ".".join(_json['fqdn'].split('.')[1:])
        self.oxm.oc_cmd(command="ADD NETWORK",
                        arguments={
                            "DOMAINNAME": _net_domainname,
                            "HOSTNAME": _net_hostname,
                            "IP": _json['ipaddr'],
                            "NETMASK": _json['netmask'],
                            "GATEWAY": _json['gateway'],
                            "VLANID": _json.get('vlantag', ''),
                            "NETWORKTYPE": _network_type,
                            "NETWORKBRIDGE": _bridge,
                            "MASTER": _master,
                            "SLAVE": _net_slaves
                        },
                        where={
                            "HOSTNAME": _domu_hostname
                        }
        )

    def mAddDomU(self, aSrcDomU, aNewDomU, aSrcXml, aDestXml, aJson, aCluCtrl, aKVM=True, aSrcVer=None, aResetActions=True, aIsOciExacc=False, aNetInfo=None, aImgFile=None):
        """
        Add DomU
        :param aSrcDomU: domU
        :return:
        """
        _srcdomU = aSrcDomU
        _newdomU = aNewDomU
        _json = aJson
        _kvm = aKVM
        _ociexacc = aIsOciExacc
        _ebox = aCluCtrl
        _options = _ebox.mGetArgsOptions()

        self.mBuildCloneGuest(_srcdomU, _newdomU, aSrcXml, aDestXml, _json)

        if 'dr' in _json['domU'] and _ociexacc:
            # We need the DOMU information present, so merge the DOMU information
            self.oxm.save_action()
            self.oxm.merge_actions(True)
            _net_info = aNetInfo
            # _net_info is having space separated slaves - they should be comma separated when passed to ADD NETWORK
            _bond_slaves = ",".join(_net_info['dr']['bond_slaves'].split())
            self.mAddNetwork(_json['domU']['dr'], _bond_slaves, _net_info['dr']['bridge'], "bondeth2", "OTHER", _json['domU']['client']['fqdn'])

        # Patch the xml with image version in case of KVM or Xen based OCIExaCC systems
        if (not _kvm and _ociexacc) or _kvm:
            self.oxm.save_action()
            self.oxm.merge_actions(True)

            if aSrcVer is not None:
                _extraParam = ""
                if aImgFile:
                    _extraParam = f"IMAGEFILE=\'{aImgFile}\'"

                self.oxm.oc_cmd(command='ALTER MACHINES IMAGEVERSION=\'%s\' %s where TYPE=GUEST' % (aSrcVer, _extraParam))

        _client_gatewayv6 = None
        _client_netmaskv6 = None
        _backup_gatewayv6 = None
        _backup_netmaskv6 = None
        if _kvm:
            self.oxm.save_action()
            self.oxm.merge_actions(True)

            _client = _json['domU']['client']

            # Ensure net VLANIDs in new DomU are honored, rather than inherited
            # from source DomU.  If not specified or null/None, set VLANID to
            # empty value (""), which means don't use a VLAN.
            _vlan = _client.get('vlantag')
            _vlan = '' if _vlan is None else _vlan

            _nw_utils = NetworkUtils()
            _client_gateway_single_stack, _client_gatewayv6 = _nw_utils.mGetIPv4IPv6Payload(
                _client, key_single_stack='gateway', key_dual_stack='v6gateway')
            _client_netmask_single_stack, _client_netmaskv6 = _nw_utils.mGetIPv4IPv6Payload(
                _client, key_single_stack='netmask', key_dual_stack='v6netmask')
            if _ociexacc:
                self.oxm.oc_cmd(
                    command='ALTER NETWORK',
                    arguments={
                        'gateway': _client['gateway'],
                        'netmask': _client['netmask'],
                        'vlanid': _vlan
                    },
                    where={
                        'networktype': 'client',
                        'hostname': _client['fqdn'].split('.')[0]
                    }
                )
            else:
                _arguments = {'mac': _client['mac'], 'vlanid': _vlan}
                _set_accelerated_network = ebCluAcceleratedNetwork.checkInputAndValidateEnvForAcceleratedNetwork(aCluCtrl, _json['dom0'][
                    'hostname'], _client.get('fqdn'), _client.get('network_virtualization'))
                if _set_accelerated_network:
                    ebLogInfo('Enabling accelerated network for client-net of domu ' + _client.get('fqdn'))
                    _arguments['ACCELERATEDNETWORK'] = 'ENABLED'
                    #OEDA is yet to support below bonding_opts argument. Once it supports will uncomment and test this code.
                    # _arguments['BONDING_OPTS'] = ebCluAcceleratedNetwork.getBondingOptions(_ebox, _client_gateway_single_stack, _client.get('slaves'), _client['fqdn'].split('.')[0])
                _set_accelerated_network = False 
                if _client_gateway_single_stack and _client_netmask_single_stack:
                    _arguments["gateway"] = _client_gateway_single_stack
                    _arguments["netmask"] = _client_netmask_single_stack
                    self.oxm.oc_cmd(
                        command='ALTER NETWORK',
                        arguments=_arguments,
                        where={
                            'networktype': 'client',
                            'hostname': _client['fqdn'].split('.')[0]
                        }
                    )
            self.oxm.save_action()
            self.oxm.merge_actions(True)

            _backup = _json['domU']['backup']
            _vlan = _backup.get('vlantag')
            _vlan = '' if _vlan is None else _vlan
            _backup_gateway_single_stack, _backup_gatewayv6 = _nw_utils.mGetIPv4IPv6Payload(
                _backup, key_single_stack='gateway', key_dual_stack='v6gateway')
            _backup_netmask_single_stack, _backup_netmaskv6 = _nw_utils.mGetIPv4IPv6Payload(
                _backup, key_single_stack='netmask', key_dual_stack='v6netmask')
            if _ociexacc:
                self.oxm.oc_cmd(
                    command='ALTER NETWORK',
                    arguments={
                        'gateway': _backup['gateway'],
                        'netmask': _backup['netmask'],
                        'vlanid': _vlan
                    },
                    where={
                        'networktype': 'backup',
                        'networkhostname': _backup['fqdn'].split('.')[0]
                    }
                )
            else:
                _arguments = {'mac': _backup['mac'], 'vlanid': _vlan}
                _set_accelerated_network = ebCluAcceleratedNetwork.checkInputAndValidateEnvForAcceleratedNetwork(aCluCtrl, _json['dom0'][
                    'hostname'], _backup.get('fqdn'), _backup.get('network_virtualization'))
                if _set_accelerated_network:
                    ebLogInfo('Enabling accelerated network for backup network of domu ' + _backup.get('fqdn'))
                    _arguments['ACCELERATEDNETWORK'] = 'ENABLED'
                    #OEDA is yet to support below bonding_opts argument. Once it supports will uncomment and test this code.
                    # _arguments['BONDING_OPTS'] = ebCluAcceleratedNetwork.getBondingOptions(_ebox, _backup_gateway_single_stack, _backup.get('slaves'), _backup['fqdn'].split('.')[0])
                _set_accelerated_network = False
                if _backup_gateway_single_stack and _backup_netmask_single_stack:
                    _arguments['gateway'] = _backup_gateway_single_stack
                    _arguments['netmask'] = _backup_netmask_single_stack
                    self.oxm.oc_cmd(
                        command='ALTER NETWORK',
                        arguments=_arguments,
                        where={
                            'networktype': 'backup',
                            'networkhostname': _backup['fqdn'].split('.')[0]
                        }
                    )
            if (_client_gatewayv6 and _client_netmaskv6) or (_backup_gatewayv6 and _backup_netmaskv6):
                _ebox.mSetIPv6DualStackPresent(True)
                _domU_networks = _ebox.mGetMachines().mGetMachineConfig(_srcdomU).mGetMacNetworks()
                _domu_net_backup_v4 = None
                _domu_net_client_v4 = None
                _client_mac = None
                _client_mtu_set = None
                _client_nat_hostname = None
                _egressArgs = None
                _nat_vlan = None
                _nat_gateway = None
                _egressIps = _ebox.mFetchEgressIpsFromPayload(_options.jsonconf)
                for _net_id in _domU_networks:
                    _net_conf = _ebox.mGetNetworks().mGetNetworkConfig(_net_id)
                    if _net_conf.mGetNetType() == 'backup' and _net_conf.mGetNetIpAddr() and ':' not in _net_conf.mGetNetIpAddr():
                        _domu_net_backup_v4 = _net_conf
                    elif _net_conf.mGetNetType() == 'client' and _net_conf.mGetNetIpAddr() and ':' not in _net_conf.mGetNetIpAddr():
                        _domu_net_client_v4 = _net_conf
                if _client_gatewayv6 and _client_netmaskv6:
                    self.oxm.save_action()
                    self.oxm.merge_actions(True)
                    _client_payload = _json['domU']['client']
                    _admin_payload = _json['domU'].get('admin') or {}
                    _net_hostname = _client_payload['fqdn'].split('.')[0]
                    _net_domainname = ".".join(_client_payload['fqdn'].split('.')[1:])
                    _master = _domu_net_client_v4.mGetNetMaster()
                    if "slaves" in _client_payload:
                        _net_slaves = _client_payload["slaves"]
                    else:
                        _net_slaves = _domu_net_client_v4.mGetNetSlave()
                    if not _ociexacc and 'mac' in _client_payload:
                        _client_mac = _client_payload['mac'].lower()
                    if 'mtu' in _client_payload:
                        _client_mtu_set = _client_payload['mtu']
                    else:
                        _client_mtu_set = _domu_net_client_v4.mGetNetMtu()
                    if 'hostname' in _admin_payload:
                        _client_nat_hostname = _admin_payload['hostname']
                    elif 'nathostname' in _client_payload:
                        _client_nat_hostname = _client_payload['nathostname']
                    else:
                        raise ExacloudRuntimeError(f"nathostname is missing in payload for domu {_net_hostname}")
                    if 'domainname' in _admin_payload:
                        _nat_domainname = _admin_payload['domainname']
                    elif 'natdomain' in _client_payload:
                        _nat_domainname = _client_payload['natdomain']
                    else:
                        raise ExacloudRuntimeError(f"natdomain is missing in payload for domu {_net_hostname}")
                    if 'netmask' in _admin_payload:
                        _nat_mask = _admin_payload['netmask']
                    elif "natnetmask" in _client_payload:
                        _nat_mask = _client_payload['natnetmask']
                    else:
                        raise ExacloudRuntimeError(f"natnetmask is missing in payload for domu {_net_hostname}")
                    if 'ipaddr' in _admin_payload:
                        _nat_ip = _admin_payload['ipaddr']
                    elif "natip" in _client_payload:
                        _nat_ip = _client_payload['natip']
                    else:
                        raise ExacloudRuntimeError(f"natip is missing in payload for domu {_net_hostname}")
                    if 'gateway' in _admin_payload:
                        _nat_gateway = _admin_payload['gateway']
                    elif "natgateway" in _client_payload:
                        _nat_gateway = _client_payload['natgateway']
                    if 'vlantag' in _admin_payload:
                        _nat_vlan = _admin_payload['vlantag']
                    elif "natvlantag" in _client_payload:
                        _nat_vlan = _client_payload['natvlantag']

                    if _egressIps:
                        _egressArgs = ",".join(_egressIps)
                    _dict_client_args = {
                                    "DOMAINNAME": _net_domainname,
                                    "HOSTNAME": _net_hostname,
                                    "IP": _client_payload['ipv6addr'],
                                    "NETMASK": _client_payload['v6netmask'],
                                    "GATEWAY": _client_payload['v6gateway'],
                                    "VLANID": _client_payload.get('vlantag', ''),
                                    "NETWORKTYPE": "client",
                                    "MASTER": _master,
                                    "SLAVE": _net_slaves
                                }
                    if _client_mac:
                        _dict_client_args["MAC"] = _client_mac
                    if _client_mtu_set:
                        _dict_client_args["MTU"] = str(_client_mtu_set)
                    _dict_client_args["NATHOSTNAME"] = _client_nat_hostname
                    _dict_client_args["NATDOMAINNAME"] = _nat_domainname
                    _dict_client_args["NATNETMASK"] = _nat_mask
                    _dict_client_args["NATIP"] = _nat_ip
                    if _nat_gateway:
                        _dict_client_args["NATGATEWAY"] = _nat_gateway
                    if _nat_vlan:
                        _dict_client_args["NATVLANID"] = _nat_vlan
                    if _egressArgs:
                        _dict_client_args["nategressipaddresses"] = _egressArgs
                    self.oxm.oc_cmd(command="ADD NETWORK",
                                    arguments=_dict_client_args,
                                    where={
                                        "HOSTNAME": _client_payload['fqdn']
                                    })
                if _backup_gatewayv6 and _backup_netmaskv6:
                    self.oxm.save_action()
                    self.oxm.merge_actions(True)
                    _backup_mac = None
                    _backup_payload = _json['domU']['backup']
                    _net_hostname = _backup_payload['fqdn'].split('.')[0]
                    _net_domainname = ".".join(_backup_payload['fqdn'].split('.')[1:])
                    _master = _domu_net_backup_v4.mGetNetMaster()
                    if "slaves" in _backup_payload:
                        _net_slaves = _backup_payload["slaves"]
                    else:
                        _net_slaves = _domu_net_backup_v4.mGetNetSlave()
                    if not _ociexacc and 'mac' in _backup_payload:
                        _backup_mac = _backup_payload['mac'].lower()
                    if 'mtu' in _backup_payload:
                        _backup_mtu_set = _backup_payload['mtu']
                    else:
                        _backup_mtu_set = _domu_net_backup_v4.mGetNetMtu()

                    if _egressIps:
                        _egressArgs = ",".join(_egressIps)
                    _dict_backup_args = {
                                    "DOMAINNAME": _net_domainname,
                                    "HOSTNAME": _net_hostname,
                                    "IP": _backup_payload['ipv6addr'],
                                    "NETMASK": _backup_payload['v6netmask'],
                                    "GATEWAY": _backup_payload['v6gateway'],
                                    "VLANID": _backup_payload.get('vlantag', ''),
                                    "NETWORKTYPE": "backup",
                                    "MASTER": _master,
                                    "SLAVE": _net_slaves
                                }
                    if _backup_mac:
                        _dict_backup_args["MAC"] = _backup_mac
                    if _backup_mtu_set:
                        _dict_backup_args["MTU"] = str(_backup_mtu_set)
                    if _egressArgs:
                        _dict_backup_args["nategressipaddresses"] = _egressArgs
                    self.oxm.oc_cmd(command="ADD NETWORK",
                                    arguments=_dict_backup_args,
                                    where={
                                        "HOSTNAME":  _json['domU']['client']['fqdn']
                                    })
                _vip_ip_single_stack, _vip_ipv6 = _nw_utils.mGetIPv4IPv6Payload(_json['domU']['vip'], key_single_stack='ipaddr', key_dual_stack='ipv6addr')
                if _vip_ipv6:
                    self.oxm.save_action()
                    self.oxm.merge_actions(True)
                    # Add ipv6 vip info using oedacli command
                    _ebox.mSetIPv6DualStackPresent(True)
                    _vip_net = _json['domU']['vip']
                    _dict_oeda_args = {}
                    _net_hostname = _vip_net['fqdn'].split('.')[0]
                    _net_domainname = ".".join(_vip_net['fqdn'].split('.')[1:])
                    _dict_oeda_args["NAME"] = _net_hostname
                    _dict_oeda_args["DOMAINNAME"] = _net_domainname
                    _dict_oeda_args["IP"] = _vip_net['ipv6addr']
                    _dict_oeda_args["IPADDR_TYPE"] = "IPV6"
                    _dict_oeda_args["NETMASK"] = _client_payload['v6netmask']
                    self.oxm.oc_cmd(command="ADD VIP",
                                    arguments=_dict_oeda_args,
                                    where={
                                        "HOSTNAME":  _json['domU']['client']['fqdn']
                                    })

        self.oxm.save_action()
        self.oxm.run_oedacli(aSrcXml, aDestXml, None, False, aResetActions)
    
    def mAddCell(self, aSrcCell, aSrcXml, aDestXml, aJson, aDeploy=False, aPower=4, aKVM=False, aCluName=None, aWait='true', aStep=None,
                 aCluUtils=None):
        """
        Add Cell
        :param aSrcCell: cell
        :return:
        """
        _srccell = aSrcCell
        _json = aJson
        _deploy = aDeploy
        _kvm = aKVM
        _clustername = aCluName
        _power = aPower
        _wait = aWait
        _step = aStep
        _clu_utils = aCluUtils

        _celllist = []
        for _cellinfo in _json['cells']:
            _celllist.append(_cellinfo['hostname'])
               
            if _step == "CONFIG_CELL":
                self.mBuildCloneCell(_srccell, _cellinfo, _kvm)
                self.oxm.save_action()
                self.oxm.run_oedacli(aSrcXml, aDestXml, None, deploy=False)
                aSrcXml = aDestXml
                if _clu_utils:
                    _dns_servers, _ntp_servers = _clu_utils.mExtractNtpDnsPayload(_cellinfo)
                    if _dns_servers or _ntp_servers:
                        self.mUpdateDnsNtpServers(_cellinfo['hostname'], aSrcXml, aDestXml,
                                                  _dns_servers, _ntp_servers, aDeploy=False)

        if _kvm and _clustername and _celllist:
            self.mAlterCluster(_celllist, _clustername, 'ADDCELLS', _power, _wait, _step)
            self.oxm.save_action()
        
        self.oxm.run_oedacli(aSrcXml, aDestXml, None, _deploy)

    def mDelCell(self, aCell, aKVM):
        """
        Delete cell/newcell
        :param aCell
        :return:
        """

        _cell = aCell
        _kvm = aKVM

        if _kvm:
            self.oxm.oc_cmd(command='DELETE NEWCELL where SRCNAME=%s' % _cell)
        else:
            self.oxm.oc_cmd(command='DELETE CELL where SRCNAME=%s' % _cell)


    def mDropCell(self, aSrcXml, aDestXml, aCellList, aDeploy=False, aPower=4, aKVM=False, 
                  aCluName=None, aXmlOnly=False, aWait = 'true', aStep=None, aUserData=None):
        """
        Drop Cell
        :param aCell
        :return:
        """
        _celllist = aCellList
        _deploy = aDeploy
        _clustername = aCluName
        _kvm = aKVM
        _power = aPower
        _wait = aWait
        _step = aStep
        _user_data = aUserData

        if _kvm and not aXmlOnly:
            if _user_data and "exascale" in list(_user_data.keys()):
                _pool_name = ""
                _exascale_attr = _user_data['exascale']
                if "pool_name" in _exascale_attr.keys():
                   _pool_name = _exascale_attr['pool_name']
                if _celllist and _pool_name:
                    self.mAlterStoragePool(_celllist, 'DROPCELLS', aPoolName=_pool_name)
                    self.oxm.save_action()
                    self.oxm.run_oedacli(aSrcXml, aDestXml, None, _deploy)

            self.mAlterCluster(_celllist, _clustername, 'DROPCELLS', _power, _wait, _step)
            self.oxm.save_action()
            self.oxm.run_oedacli(aSrcXml, aDestXml, None, _deploy)

        if _step == "CONFIG_CELL":
            for _cell in _celllist:
                self.mDelCell(_cell, _kvm)
                self.oxm.save_action()

            self.oxm.run_oedacli(aSrcXml, aDestXml, None, False)

    def mUpdateEGSClusterName(self, aSrcXml, aDestXml, aName, aESClusterName):
        _name = aName
        _egs_cluster_name = aESClusterName

        self.oxm.oc_cmd(command=f"ALTER EXASCALECLUSTER NAME={_egs_cluster_name} WHERE NAME={_name}")
        self.oxm.save_action()
        self.oxm.run_oedacli(aSrcXml, aDestXml, None, False)

    def mUpdateEFRack(self, aSrcXml, aDestXml, aHostName, aCellType):
        _hostname = aHostName
        _cell_type = aCellType

        self.oxm.oc_cmd(command=f"ALTER MACHINE TYPE={_cell_type} WHERE HOSTNAME={_hostname}")
        self.oxm.save_action()
        self.oxm.run_oedacli(aSrcXml, aDestXml, None, False)

    def mUpdateEDVVolumes(self, aSrcXml, aDestXml, aStorageType, aProtocol, aName, aType):
        _storage_type = aStorageType
        _protocol = aProtocol
        _vault_name = aName
        _vault_type = aType

        self.oxm.oc_cmd(command=f"ALTER MACHINES STORAGETYPE={_storage_type} VOLUMEPROTOCOL={_protocol} VAULT={_vault_name}  WHERE TYPE={_vault_type}")
        self.oxm.save_action()
        self.oxm.run_oedacli(aSrcXml, aDestXml, None, False)

    def mUpdateEDVGuestVolumes(self, aSrcXml, aDestXml, aStorageType, aProtocol, aVault, aType, aHostName):
        _storage_type = aStorageType
        _protocol = aProtocol
        _vault = aVault
        _type = aType
        _hostname = aHostName

        self.oxm.oc_cmd(command=f"ALTER MACHINES STORAGETYPE={_storage_type} VOLUMEPROTOCOL={_protocol} VAULT={_vault} WHERE TYPE={_type} HOSTNAMES={_hostname}")
        self.oxm.save_action()
        self.oxm.run_oedacli(aSrcXml, aDestXml, None, False)

