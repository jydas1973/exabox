"""
 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    Bm - Functionality of Bare Metal Commands

FUNCTION:
    Provide basic/core API for managing the Bare Metal Cloud

NOTE:
    None

History:
    MODIFIED   (MM/DD/YY)
    ririgoye    05/28/25   - Bug 38007283 - CHANGE PYTHON 3.11 ISSUES DURING
                             MAIN WORKFLOWS
    ririgoye    06/18/24   - Bug 36746656 - PYTHON 3.11 - EXACLOUD NEEDS TO
                             UPDATE DEPRECATED/OLDER IMPORTS DYNAMICALLY
    alsepulv    03/16/21   - Enh 32619413: remove any code related to Higgs
    alsepulv    03/05/21   - Bug 32592473: replace get_stack_trace() with
                             traceback.format_exc()
    vmallu      06/15/2020 - bug 31617026 COMPOSE CLUSTER GENERATING SAME
                             PKEY ON IB (KVM) QTR RACKS
    vmallu      01/14/2020 - ENH 30765027 - COMPOSE CLUSTER ROCE/X8M SUPPORT
    vmallu      07/2220/19 - Enh 30022609 - COMPOSE CLUSTER SUPPORT FOR X8-IB
    srtata      04/26/2018 - bug 27697345: debug stmts for sabre 
    mmsharif    03/01/2017 - First draft of the implementation
"""
import six
import os
import re
import json
import subprocess
import shlex
import pprint
import shutil
import traceback
from base64 import b64encode, b64decode

try:
    from collections import OrderedDict, Counter
except ImportError:
    from collections import OrderedDict, Counter

from defusedxml import ElementTree as ET
from xml.etree.ElementTree import Element, SubElement
from exabox.tools.AttributeWrapper import wrapStrBytesFunctions
from exabox.core.Error import gBMCError
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.core.DBStore import ebGetDefaultDB
from exabox.ovm.bmcutil import BmcConfig, BmcUtil, logWarn, logInfo, logError
from exabox.log.LogMgr import ebLogSetBMCLogHandler, ebLogInfo
from exabox.log.LogMgr import ebLogGetBMCLogger


class OedaProcessor(object):
    """
    Runs alter commands to change a template xml file. The class can be used as
    mentoned below:
        oeda = OedaProcessor(template_xml_path, output_folder_path, path to
                             oedacli, logger object)
        oeda.loadElements()
        oeda.alter... --> alter commands
        oeda.alter... --> more alter commands
        oeda.saveXmlFile(output_xml_file_name)
        oeda.processCmds()
    """
    def __init__(self, templateXml, outdir, oedaCli, logger):
        """
        templateXml: Base XML file on which alter commands are executed,
        outdir: Path to output folder,
        oedaCli: Path to oedacli executable,
        logger: Instance of a python logger
        """
        self.__templateXml = os.path.realpath(templateXml)
        self.__outdir = outdir
        self.__cmds = []
        self.__cmdFile = ''
        self.__outXmlFile = ''
        self.__errFile = ''
        self.__oedaCli = os.path.realpath(oedaCli)
        self.logger = logger
        self.logger.info('oedacli path: %s' % (self.__oedaCli,))
        self.util = BmcUtil(logger)
        self.__clusters = None
        self.__dbHomes = None
        self.__databases = None
        self._machines = None
        self._networks = None
        self._iloms = None
        self._switches = None
        self._sw_type = None
        self._clusters = None
        self._dom0s = None
        self._domus = None
        self._cells = None
        self._ibswitches = None
        self._roceswitches = None
        self._spineswitches = None
        self._pdus = None
        self._dom0domuMap = {}
        self._dgs = []
        self._dbfsdg_name = ''
        self._datadg_name = ''
        self._recodg_name = ''
        self.__xmlv1reinjector = V1OedaXMLRebuilder()
        self.__xmlv1reinjector.SavePropertiesFromTemplate(self.__templateXml)
        self.__parseXML()

    def getNodes(self, type_):
        """
        Returns all nodes specific of type type_.
        """
        _node_type_map = {
            'compute': self._dom0s,
            'dom0': self._dom0s,
            'domu': self._domus,
            'cell': self._cells,
            'ibsw': self._ibswitches,
            'rocesw': self._roceswitches,
            'spinesw': self._spineswitches,
            'pdu': self._pdus
        }
        return _node_type_map.get(type_.lower())

    def extractJson(self, s):
        """
        Tries to extract a json from the input string s.
        OEDACLI output has a header part in the response, this function
        strips header lines one by one and tries
        to make sense of the rest.
        """
        # TODO:
        # Once the OEDA bug is fixed, this hack will not be required.
        # Should be pretty straight-forward extraction after the fix
        # (bug# 26837646).

        lines = s.split('\n')
        outJson = {}
        for linenum in range(len(lines)):
            probableJson = '\n'.join(lines[linenum:])
            try:
                outJson = json.loads(probableJson)
            except Exception:
                pass
            else:
                break
        if not outJson:
            self.logger.warn('Could not parse a json from %s' % (s,))
        else:
            self.logger.info('oedacli cmd json output: %s' %
                             (pprint.pformat(str(outJson), indent=4)))
        return outJson if outJson else lines

    def runCmd(self, cmd):
        """
        Runs a raw oedacli cmd and returns the output in JSON format.
        """
        cmdArgs = self.__oedaCli + " -c " +  self.__templateXml + " -j -e "  \
                  + cmd
        cmdStr = ' '.join(cmdArgs)
        self.logger.info('oedacli cmd: %s' % cmdStr)
        try:
            p = subprocess.Popen(
                shlex.split(cmdArgs),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False
            )
            (outStr) = wrapStrBytesFunctions(p).communicate()[0]
            self.logger.info('oedacli output: %s' % (outStr,))
        except Exception as e:
            self.logger.error('Could not run oedacli cmd: %s [%s]' %
                              (cmdStr, e))
            raise
        return self.extractJson(outStr)

    def addCmd(self, cmdStr):
        """
        Adds an OEDA cmd (cmdStr) to the list of commands to execute.
        """
        self.__cmds.append(cmdStr)

    def alter(self, alterItem, setDict, whereDict):
        """
        Alters the alterItem (example: network, machine) to values mentioned
        in setDict (example:
        {'ip' : '192.168.1.2', 'netmask' : '255.255.255.0'}). To find the
        target host, values in whereDict is used such as
        {'hostname' : 'phx200815exdcl01', 'networktype' : 'client'}.
        This above exaple will add the following command for execution:
        "ALTER network ip = '192.168.1.2' netmask = 255.255.255.0 WHERE
         hostname = 'phx2exdcl01' networktype = 'client'"
        """
        setDict = {key: val for key, val in six.iteritems(setDict)
                   if val is not None}
        if not setDict:
            self.logger.warning('nothing to set for %s' % (alterItem,))
            return

        cmd = 'ALTER %s ' % alterItem
        for k, v in six.iteritems(setDict):
            cmd += ' %s = "%s" ' % (k, v)
        if whereDict:
            cmd += ' WHERE '
        for k, v in six.iteritems(whereDict):
            cmd += ' %s = "%s" ' % (k, v)
        self.__cmds.append(cmd)

    def alterDnsNtp(self, dnsStr, ntpStr, whHost, hostType):
        """
        Alters hostType (network, machine, ilom) dns and ntp
        where host name is whHost.
        """
        sd = {'dnsservers': dnsStr, 'ntpservers': ntpStr}
        wd = {'hostname': whHost}
        self.alter(hostType, sd, wd)

    def alterDns(self, dnsStr, whHost, hostType):
        """
        Alters hostType (network, machine, ilom) dns servers
        where host name is whHost.
        """
        self.alter(hostType, dict(dnsservers=dnsStr), dict(hostname=whHost))

    def alterNtp(self, ntpStr, whHost, hostType):
        """
        Alters hostType (network, machine, ilom) ntp servers
        where host name is whHost.
        """
        self.alter(hostType, dict(ntpservers=ntpStr), dict(hostname=whHost))

    def editCaviumPorts(self, etherfaceList, caviumList, macList, whHost):
        """
        Deletes any existing caviumport where hostname is whHost and
        adds caviumport with aligned etherfacelist, caviumList and macList.
        """
        self.addCmd('DELETE caviumport WHERE hostname = ' + whHost)

        tuples = list(zip(etherfaceList, caviumList, macList))
        # Add each caviumport
        for eachSet in tuples:
            eface, cavium, mac = eachSet
            efaceNum = re.match(r'\D+(\d+)', eface).groups()[0]
            cmdf = "ADD caviumport ethid='%s' caviumport='%s' mac='%s' "
            cmdf += "WHERE hostname='%s'"
            cmd = cmdf % (efaceNum, cavium, mac, whHost)
            self.addCmd(cmd)

    def alterCustomerName(self, custName):
        """
        Aleters the customer name to custName
        """
        if not custName:
            self.logger.error('alterCustomerName: empty customer name')
            return
        sd = {'customername': custName}
        self.alter('es', sd, {})

    def alterScans(self, hostname, port, ips):
        """
        Alters scans hostname, port and ip list
        """
        ipStr = ','.join(ips)
        clusterName = self.getClusterName()
        sd = {'scanname': hostname, 'scanport': port, 'scanips': ipStr}
        wd = {'clustername': clusterName}
        self.alter('scan', sd, wd)

    def listDiskgroups(self):
        """
        List diskgroups and saves the diskgroupnames.
        """
        if self._dgs:
            return
        self._dgs = self.runCmd('list diskgroups')
        # These values come from Template XML file where we have the diskgroup
        # names reflecting the diskgroup types.
        for dg in self._dgs:
            dgname = dg['diskGroupName']
            if dgname.find('DBFS') != -1:
                self._dbfsdg_name = dgname
            elif dgname.find('DATA') != -1:
                self._datadg_name = dgname
            elif dgname.find('RECO') != -1:
                self._recodg_name = dgname

    def alterDiskgroups(self, diskgroups):
        """
        Alters diskgroups based on the input diskgroups list. Each diskgroup in
        the diskgroups list is a dictionary with possible keys
        ['diskgroupsize', 'diskgroupname', 'redundancy']
        """
        if not diskgroups:
            return
        # List the diskgroups first
        self.listDiskgroups()
        # Get cluster name
        whereDict = OrderedDict()
        # Clustername needs to be the first parameter in where clause.
        whereDict['clustername'] = self.getClusterName()
        possible_keys = ['diskgroupsize', 'diskgroupname', 'redundancy']
        for dg in diskgroups:
            dgtype = dg['diskgrouptype'].upper()
            if dgtype == 'DATA':
                whereDict['diskgroupname'] = self._datadg_name
            elif dgtype == 'RECO':
                whereDict['diskgroupname'] = self._recodg_name
            elif dgtype == 'DBFS':
                whereDict['diskgroupname'] = self._dbfsdg_name
            else:
                raise ValueError("Unsupported diskgrouptype: %s" % (dgtype,))

            setdict = {}
            for key in possible_keys:
                if key in dg and dg.get(key):
                    setdict[key] = dg[key]

            self.alter('diskgroup', setdict, whereDict)

    def alterPkey(self, newKey, whHost, pkeyType):
        """
        Alters pkeyType(storage or compute) pkey with newKey where
        hostname is whHost
        """
        privateIds = [1, 2] if pkeyType == 'storage' else [3, 4]
        for privateId in privateIds:
            self.alter('network',
                       dict(pkey=newKey),
                       dict(hostname=whHost,
                            networktype='private',
                            privateid=str(privateId)))

    def getClusterName(self):
        """
        Returns the cluster name
        """
        return self._clusters[0]['clusterName']

    def getDbHomeLoc(self):
        """
        Returns the DB Home Location
        """
        if not self.__dbHomes:
            self.__dbHomes = self.runCmd('list databasehomes')
        return self.__dbHomes[0]['databaseHomeLoc']

    def getDbName(self, dbType):
        """
        Returns the name of the database sid from given dbType
        """
        if not self.__databases:
            self.__databases = self.runCmd('list databases')
        for db in self.__databases:
            if db['databaseType'].lower() == dbType.lower():
                return db['databaseSid']

    def alterClusterName(self, newCluster):
        """
        Alters the cluster name to newCluster
        """
        if not newCluster:
            self.logger.error('alterClusterName: empty clustername')
            return
        clusterName = self.getClusterName()
        # Now alter clustername
        self.alter('cluster',
                   {'clustername': newCluster},
                   {'clustername': clusterName})

    def __makeSetDict(self, allkeys, d):
        out = {}
        if not d:
            return out
        for k in allkeys:
            if d.get(k) is not None:
                if isinstance(d[k], list):
                    out[k] = ','.join([str(x) for x in d[k]])
                else:
                    out[k] = d[k]
        return out

    def alterNetwork(self, netdict, hostname, networktype, privateid=None):
        """
        Alters network as given in 'netdict' where the keys must be among
        ['hostname', 'ip', 'netmask', 'domainname', 'master','gateway',
        'sshenabled', 'mac', 'slave', 'pkey', 'pkeyname', 'status', 'lacp',
        'vlanid', 'nathostname','natip', 'natdomainname', 'natnetmask'].
        The network is changed for the given 'hostname' and of 'networktype'
        which can be 'admin', 'private', 'client', 'backup'. For private
        network 'privateid' is required.
        """
        # oedacli> help alter network
        # Usage:
        # ALTER NETWORK
        #   HOSTNAME = <hostname> |
        #   IP = <ipaddresss> |
        #   NETMASK = <netmask> |
        #   DOMAINNAME = <domainname> |
        #   MASTER = <master> |
        #   GATEWAY = <gateway> |
        #   SSHENABLED = <sshenabled> |
        #   MAC = <mac> |
        #   SLAVE = '<slave>' |
        #   PKEY = <pkey> |
        #   PKEYNAME = <pkeyname> |
        #   STATUS = <status> |
        #   LACP = <lacp> |
        #   VLANID = <vlanid> |
        #   NATHOSTNAME = <nathostname> |
        #   NATIP = <natipaddresss> |
        #   NATDOMAINNAME = <natdomainname> |
        #   NATNETMASK = <natnetmask>
        # WHERE
        #  ID = <networkid> |
        #  NETWORKHOSTNAME = <networkhostname> |
        #  NATHOSTNAME = <nathostname> |
        #  HOSTNAME = <hostname> NETWORKTYPE=<networktype>\
        #        [PRIVATEID=<PRIVATEID>] |
        #  CLUSTERNAME=<clustername> [ COMPUTENUMBER=<computenumber> |\
        #        STORAGENUMBER=<storagenumber> ] NETWORKTYPE=<networktype>i\
        #        [PRIVATEID=<PRIVATEID>] |
        #  CLUSTERNUMBER=<clusternumber> [ COMPUTENUMBER=<computenumber> |\
        #        STORAGENUMBER=<storagenumber> ] NETWORKTYPE=<networktype>\
        #        [PRIVATEID=<PRIVATEID>]|
        if not netdict:
            return
        if networktype == 'private':
            if not privateid:
                self.logger.error('unexpected private id[%s]' % (privateid,))
                return

        allkeys = ['hostname', 'ip', 'netmask', 'domainname', 'master',
                   'gateway', 'sshenabled', 'mac', 'slave', 'pkey',
                   'pkeyname', 'status', 'lacp', 'vlanid', 'nathostname',
                   'natip', 'natdomainname', 'natnetmask']

        setdict = self.__makeSetDict(allkeys, netdict)
        # We've a special handling here for slave. OEDA accepts space separated
        # items in the slave string, elsewhere it accepts ',' separated string.
        if 'slave' in setdict:
            slaves = setdict.get('slave')
            setdict['slave'] = ' '.join(slaves.split(','))

        wheredict = dict(hostname=hostname, networktype=networktype)
        if privateid:
            wheredict['privateid'] = str(privateid)
            self.logger.info('alterNetwork:\nsetdict:\n%s, wheredict:\n%s' %
                             (pprint.pformat(setdict, indent=4),
                              pprint.pformat(wheredict, indent=4)))
        self.alter('network', setdict, wheredict)

    def alterCluster(self, cluster):
        """
        Alters cluster information as passed in 'cluster' dictionary where the
        keys must be one from ['clustername', 'giversion', 'gihomeloc',
        'invloc','basedir', 'patchlist']
        """
        # oedacli> help alter cluster
        # Usage:
        # ALTER CLUSTER
        #  CLUSTERNAME = <clustername> |
        #  GIVERSION = <giversion> |
        #  GIHOMELOC = <gridhomelocation> |
        #  INVLOC = <inventorylocation> |
        #  BASEDIR = <basedir> |
        #  PATCHLIST = <patchlist>
        # WHERE
        #  CLUSTERNUMBER = <clusternumber> |
        #  CLUSTERNAME = <clustername> |
        #  CLUSTERID = <clusterid>
        allkeys = ['clustername', 'giversion', 'gihomeloc', 'invloc',
                   'basedir', 'patchlist']
        setdict = self.__makeSetDict(allkeys, cluster)
        wheredict = dict(clustername=self.getClusterName())
        self.alter('cluster', setdict, wheredict)

    def alterDatabase(self, db):
        """
        Alters database based on the given 'db' dictionary which can have keys
        from ['blocksize', 'charset', 'datadg', 'dblang', 'dbname',
        'dbtemplate', 'dbtype', 'recodg']
        """
        # oedacli> help alter database
        # Usage:
        # ALTER DATABASE
        #  BLOCKSIZE = <blocksize> |
        #  CHARSET = <characterset> |
        #  DATADG = <datadg> |
        #  DBLANG = <dblang> |
        #  DBNAME = <dbname> |
        #  DBTEMPLATE = <dbtemplate> |
        #  DBTYPE = <dbtype> |
        #  HOSTNAMES = <hostnames> |
        #  RECODG = <recodg>
        # WHERE
        #  ID = <databaseid> |
        #  CLUSTERNUMBER = <clusternumber> DATABASENAME = <databasename> |
        #  CLUSTERNAME = <clustername> DATABASENAME = <databasename> |
        #  CLUSTERID = <clusterid> DATABASENAME = <databasename>
        if not db:
            self.logger.warn('database section missing')
            return
        dbtype = db.get('dbtype')
        if not dbtype:
            self.logger.warn('dbtype missing, cannot alter db')
            return
        allkeys = ['blocksize', 'charset', 'datadg', 'dblang', 'dbname',
                   'dbtemplate', 'dbtype', 'recodg']
        setdict = self.__makeSetDict(allkeys, db)
        wheredict = dict(clustername=self.getClusterName(),
                         databasename=self.getDbName(dbtype))
        self.alter('database', setdict, wheredict)

    def alterDatabaseHomes(self, databasehomes):
        """
        Alters databasehomes based on the given 'databasehomes' list. Each of
        the item in the list is a dictionary having keys which must be among
        the following ['owner', 'dbversion', 'dbhomeloc', 'dbhomename',
        'invloc', 'dblang', 'patchlist', 'basedir']
        """
        if not databasehomes:
            self.logger.warn('databasehomes section missing')
            return
        for dbhome in databasehomes:
            # OEDA Supports following databasehome alterations
            # OWNER = <owner> |
            # DBVERSION = <version> |
            # DBHOMELOC = <homepath> |
            # DBHOMENAME = <dbhomename> |
            # INVLOC = <inventorylocation> |
            # DBLANG = <language> |
            # MACHINELIST = <machinelist> |
            # PATCHLIST = <patchlist>
            # BASEDIR = <basedir>
            allkeys = ['owner', 'dbversion', 'dbhomeloc', 'dbhomename',
                       'invloc', 'dblang', 'patchlist', 'basedir']
            setdict = self.__makeSetDict(allkeys, dbhome)
            wheredict = dict(clustername=self.getClusterName(),
                             dbhomeloc=self.getDbHomeLoc())
            self.alter('databasehome', setdict, wheredict)
            for db in dbhome.get('databases'):
                self.alterDatabase(db)

    def saveXmlFile(self, fileName='oedaOut.xml'):
        """
        Sets the altered XML path denoted by fileName.
        """
        self.__outXmlFile = os.path.join(self.__outdir, fileName)
        # Make sure we have full path
        self.__outXmlFile = os.path.realpath(self.__outXmlFile)

    def saveCmdFile(self, fn='oedaCmds.txt'):
        """
        Saves the commands file with filename fn.
        """
        self.__cmds.append('')
        content = '\nSAVE ACTION FORCE\n'.join(self.__cmds)
        if not self.__outXmlFile:
            self.saveXmlFile()
        content += '\nSAVE FILE NAME = ' + self.__outXmlFile
        fpath = os.path.join(self.__outdir, fn)
        self.util.writeFile(content, fpath)
        self.__cmdFile = fpath
        self.util.logFileContent('oedaCmd file content', fpath)

    def lookForError(self, logfilename):
        """
        Searches for "Error:" string in OEDA log file. If found returns a list
        of such lines. If not found returns a blank list.
        """
        error_lines = []
        with open(logfilename) as _f:
            for line in _f:
                line = line.strip()
                if line and re.search('.*error:.*', line, re.IGNORECASE):
                    error_lines.append(line)
        return error_lines

    def processCmds(self):
        """
        Executes the commands through OEDACLI and saves the output xml.
        Returns success_status, command_stdout  where
        success_status: True for no errors, False for errors
        command_stdout: Stdout generated by OEDACLI.
        "success" only indicates that the oedacli could be executed without
        errors, however oedacli itself can print error messages if it is
        not able to execute certain commands, these errors can be found at
        command_stdout file.
        """
        if not self.__cmdFile:
            self.saveCmdFile()

        runCmdf = '%s -c %s -f %s'
        # Make sure we have the full path
        self.__templateXml = os.path.realpath(self.__templateXml)
        self.__cmdFile = os.path.realpath(self.__cmdFile)
        self.__errFile = os.path.join(os.path.dirname(self.__cmdFile),
                                      'oedaOut.txt')

        runCmd = runCmdf % (self.__oedaCli, self.__templateXml,
                            self.__cmdFile)
        self.logger.info('Executing: %s' % (runCmd,))
        success = False
        try:
            p = subprocess.Popen(runCmd.split(), stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            outStr, errStr = wrapStrBytesFunctions(p).communicate()
            if errStr:
                self.logger.error('running oedacli encountered error: "%s"' %
                                  (errStr,))
            returnCode = p.returncode
            self.logger.info('oedacli returned %s' % (returnCode,))
        except Exception as e:
            self.logger.error('could not run oedacli: "%s"' % (e,))
        else:
            # Store the stdout of the cmd in a file
            self.util.writeFile(outStr, self.__errFile)
            # Check for errors in log file
            err_list = self.lookForError(self.__errFile)
            if err_list:
                self.logger.error('OEDACLI logfile %s contains errors' % (
                                self.__errFile))
                self.logger.error('Errors found are:\n%s' % (
                                '\n'.join(err_list),))
            else:
                success = True

        self.__xmlv1reinjector.ProcessOedaCliXML(self.__outXmlFile)

        return success and (returnCode == 0), self.__errFile

    def getOutXmlPath(self):
        """
        Returns the full path where the output XML is generated.
        """
        if not os.path.exists(self.__outXmlFile):
            self.logger.error('No oeda output xml found at %s' % (
                self.__outXmlFile,))
            self.logger.error('Please check oeda command output file at %s' % (
                self.__errFile,))
        return self.__outXmlFile

    def getCmdList(self):
        """
        Prints and returns the command list for execution
        """
        for index, cmd in enumerate(self.__cmds):
            self.logger.info('%s   : %s' % (index, cmd))
        return self.__cmds

    def deleteCmd(self, index):
        """
        Deletes a command with the index from command list
        """
        try:
            self.__cmds.pop(index)
        except Exception as e:
            self.logger.error('could not delete cmd with index %s [%s]' % (
                               index, e))

    def cmdFileContent(self):
        """
        Returns the content of the command file
        """
        return self.util.readFile(self.__cmdFile)

    def oedaLogContent(self):
        """
        Returns the content of the oeda log file
        """
        return self.util.readFile(self.__errFile)

    def outputXmlContent(self):
        """
        Returns the content of the output XML file
        """
        return self.util.readFile(self.__outXmlFile)

    def __parseXML(self):
        self._machines = self.runCmd('list machines')
        self._switches = self.runCmd('list switches')
        self._clusters = self.runCmd('list clusters')
        self._networks = self.runCmd('list networks')
        self._iloms = self.runCmd('list iloms')

    def loadElements(self):
        """
        Loads the passed XML elements
        """
        self.loadDom0s()
        self.loadDomus()
        self.loadCells()
        self.loadIBSwitches()
        self.loadRoceSwitches()
        self.loadSpineSwitches()
        self.loadPDUs()
        self.loadClusters()
        self.loadDom0DomUMap()

    def __loadNodes(self, type_):
        _nodes = []
        if type_.lower() == 'dom0' or type_.lower() == 'compute':
            for _machine in self._machines:
                if _machine.get('machineType') == 'compute' and\
                   (_machine.get('osType') == 'LinuxDom0' or\
                   _machine.get('osType') == 'LinuxKVM'):
                    _nodes.append(_machine)
        elif type_.lower() == 'domu':
            for _machine in self._machines:
                if _machine.get('machineType') == 'compute' and\
                   (_machine.get('osType') == 'LinuxGuest' or\
                   _machine.get('osType') == 'LinuxKVMGuest'):
                    _nodes.append(_machine)
        elif type_.lower() == 'cell':
            for _machine in self._machines:
                if _machine.get('machineType') == 'storage':
                    _nodes.append(_machine)
        elif type_.lower() == 'ibsw':
            for _switch in self._switches:
                if _switch.get('switchDescription') == 'Exadata Leaf Switch':
                    _nodes.append(_switch)
        elif type_.lower() == 'rocesw':
            for _switch in self._switches:
                if _switch.get('switchDescription') == 'Exadata Leaf Switch':
                    _nodes.append(_switch)
        elif type_.lower() == 'pdu':
            for _switch in self._switches:
                if _switch.get('switchDescription') == 'Exadata PDU Switch':
                    _nodes.append(_switch)
        elif type_.lower() == 'spinesw':
            for _switch in self._switches:
                if _switch.get('switchDescription') == 'Exadata Spine Switch':
                    _nodes.append(_switch)

        return _nodes

    def getNetworkDetail(self, id_):
        """
        Returns a dictionary of the network having id 'id_'
        """
        for _network in self._networks:
            if _network['id'] == id_:
                return _network
        logError('network id [%s]  not found in XML' % (id_,))
        return {}

    def getIlomDetail(self, id_):
        """
        Returns a dictionary of the ILOM with id 'id_'
        """
        _found = None
        if self._iloms is None:
            self._iloms = self.runCmd('list iloms')
        for _ilom in self._iloms:
            if _ilom['id'] == id_:
                _found = _ilom
                break
        if _found is None:
            return {}

        _networks = _found['networks']['network']
        for _dict in _networks:
            _network_detail = self.getNetworkDetail(_dict['id'])
            _dict.update(_network_detail)

        return _found

    def loadDom0s(self):
        """
        Loads dom0 information from the XML.
        """
        self._dom0s = self.__loadNodes('dom0')
        for _dom0 in self._dom0s:
            _networks = _dom0['networks']['network']
            for _dict in _networks:
                _network_detail = self.getNetworkDetail(_dict['id'])
                _dict.update(_network_detail)
            _iloms = _dom0['iloms']['ilom']
            for _dict in _iloms:
                _ilom_detail = self.getIlomDetail(_dict['id'])
                _dict.update(_ilom_detail)

        logInfo('Loaded DOM0s\n%s' % (pprint.pformat(self._dom0s, indent=4),))

    def loadDomus(self):
        """
        Loads domu information from the XML.
        """
        self._domus = self.__loadNodes('domu')
        for _domu in self._domus:
            _networks = _domu['networks']['network']
            for _dict in _networks:
                _network_detail = self.getNetworkDetail(_dict['id'])
                _dict.update(_network_detail)

        logInfo('Loaded DOMUs\n%s' % (pprint.pformat(self._domus, indent=4),))

    def loadDom0DomUMap(self):
        for _dom0 in self._dom0s:
            _dom0_admin_hostname = self.__getAdminHostName('dom0', _dom0['id'])
            _domu_machine_id = _dom0['machine'][0]['id']
            self._dom0domuMap[_dom0_admin_hostname] =\
              self.__getMachineHostName('domu', _domu_machine_id)

        logInfo('Loaded Dom0DomUMap\n%s' % (pprint.pformat(self._dom0domuMap,
                                                           indent=4)))
    def lookupDomuMachineHostName(self, dom0hostname):
        domu_machine_hostname = self._dom0domuMap.get(dom0hostname)
        if not domu_machine_hostname:
            raise Exception('DomU machine hostname not found for Dom0: %s' % (
                            dom0hostname,))
        return domu_machine_hostname

    def loadCells(self):
        """
        Loads cell information from the XML.
        """
        self._cells = self.__loadNodes('cell')
        for _cell in self._cells:
            _networks = _cell['networks']['network']
            for _dict in _networks:
                _network_detail = self.getNetworkDetail(_dict['id'])
                _dict.update(_network_detail)
            _iloms = _cell['iloms']['ilom']
            for _dict in _iloms:
                _ilom_detail = self.getIlomDetail(_dict['id'])
                _dict.update(_ilom_detail)

        logInfo('Loaded CELLs\n%s' % (pprint.pformat(self._cells, indent=4),))

    def loadIBSwitches(self):
        """
        Loads ibswitch information from the XML.
        """
        self._ibswitches = self.__loadNodes('ibsw')
        for _sw in self._ibswitches:
            _networks = _sw['networks']['network']
            for _dict in _networks:
                _network_detail = self.getNetworkDetail(_dict['id'])
                _dict.update(_network_detail)
        logInfo('Loaded IBSwitches\n%s' % (pprint.pformat(self._ibswitches,
                                                          indent=4),))
    def loadRoceSwitches(self):
        """
        Loads roceswitches information from the XML.
        """
        self._roceswitches = self.__loadNodes('rocesw')
        for _sw in self._roceswitches:
            _networks = _sw['networks']['network']
            for _dict in _networks:
                _network_detail = self.getNetworkDetail(_dict['id'])
                _dict.update(_network_detail)
        logInfo('Loaded RoceSwitches\n%s' % (pprint.pformat(self._roceswitches,
                                                          indent=4),))
    def loadSpineSwitches(self):
        """
        Loads spine switch information from the XML.
        """
        self._spineswitches = self.__loadNodes('spinesw')
        for _sw in self._spineswitches:
            _networks = _sw['networks']['network']
            for _dict in _networks:
                _network_detail = self.getNetworkDetail(_dict['id'])
                _dict.update(_network_detail)
        logInfo('Loaded Spine Switches\n%s' % (pprint.pformat(
                                    self._spineswitches, indent=4),))

    def loadPDUs(self):
        """
        Loads pdu information from the XML.
        """
        self._pdus = self.__loadNodes('pdu')
        for _sw in self._pdus:
            try:
                _networks = _sw['networks']['network']
            except Exception as e:
                logWarn('PDU does not have network info in XML [%s]' % (e,))
                _networks = []

            for _dict in _networks:
                _network_detail = self.getNetworkDetail(_dict['id'])
                _dict.update(_network_detail)
        logInfo('Loaded PDUs\n%s' % (pprint.pformat(self._pdus, indent=4),))

    def loadClusters(self):
        """
        Loads cluster information from the XML.
        """
        # Cluster is already loaded as part of parseXML, right now we don't
        # need to anything extra apart from printing the information.
        logInfo('Loaded Clusters\n%s' % (pprint.pformat(self._clusters,
                                                        indent=4),))

    def __getMachineHostName(self, machine_type, machine_id):
        _nodes = self.getNodes(machine_type)
        for _node in _nodes:
            if _node['id'] == machine_id:
                return _node['hostName']

    def __getAdminHostName(self, machine_type, machine_id):
        _nodes = self.getNodes(machine_type)
        for _node in _nodes:
            if _node['id'] == machine_id:
                for _network in _node['networks']['network']:
                    _network_type = _network['id'].split('_')[-1]
                    if _network_type == 'admin':
                        return _network['hostName']

    def __getAdminHostNames(self, machine_type):
        _nodes = self.getNodes(machine_type)
        _hostnames = []
        for _node in _nodes:
            for _network in _node['networks']['network']:
                _network_type = _network['id'].split('_')[-1]
                if _network_type == 'admin':
                    _hostnames.append(_network['hostName'])
                    break
        return _hostnames

    def getSwitchType(self):
        """
        Gets Switch Type.
        """
        _network_switches = self.getSwitches()
        logInfo('****VMDEBUG getSwitches : %s' % _network_switches)
        for _sw in _network_switches:
            _networks = _sw['networks']['network']
            logInfo('Switch type : %s' % self._sw_type)
            if self._sw_type is not None:
               break
            for _dict in _networks:
                _network_detail = self.getNetworkDetail(_dict['id'])
                if (re.search(".*ib[01]|.*sw-ib[a-zA-Z][01]$", 
                    _network_detail['hostName']) or 
                    re.search(".*sw-ib[a-zA-Z][01]", 
                    _network_detail['networkName'])):
                   self._sw_type = 'ibsw' 
                   break
                elif (re.search(".*sw-roce[a-zA-Z][01]$", 
                    _network_detail['hostName']) or 
                    re.search(".*sw-roce[a-zA-Z][01]", 
                    _network_detail['networkName'])):
                   self._sw_type = 'rocesw' 
                   break
        logInfo('Switch type : %s' % self._sw_type)
        return self._sw_type

    def getDom0HostNames(self):
        """
        Returns a list of dom0 host names.
        """
        return self.__getAdminHostNames('dom0')

    def getCellHostNames(self):
        """
        Returns a list of cell host names.
        """
        return self.__getAdminHostNames('cell')

    def getDomuHostNames(self):
        """
        Returns a list of domu host names.
        """
        return self.__getAdminHostNames('domu')

    def getDom0s(self):
        """
        Returns a list of dom0s.
        """
        return self._dom0s

    def getDomus(self):
        """
        Returns a list of domus.
        """
        return self._domus

    def getCells(self):
        """
        Returns a list of cells.
        """
        return self._cells

    def getClusters(self):
        """
        Returns cluster information.
        """
        return self._clusters

    def getSwitches(self):
        """
        Returns a list of switches.
        """
        return self._switches


class Actions(object):
    def __init__(self, obj, actions):
        self.__obj = obj
        self.__actions = actions

    def do(self):
        for action in self.__actions:
            getattr(self.__obj, 'process' + action)()


class NameSpace(object):
    def __init__(self, aDict):
        self.__dict__.update(aDict)

    def __getattr__(self, k):
        # This is called when the attribute is not found
        return None

    def __setattr__(self, k, v):
        self.__dict__.__setitem__(k, v)


class XMLProcessor(object):
    # TODO: This class will not be required, when OEDA supports manipulating
    # all the entities we want to alter from OEDACLI. This class is used only
    # for those entities that are not configurable from OEDACLI.
    # To be revisited once the fix is made (bug# 26823258)

    def __init__(self, xmlfn):
        self.__xmlfn = xmlfn
        self.__root = None
        self.loadXml()

    def loadXml(self):
        try:
            with open(self.__xmlfn) as f:
                self.__xml_file_content = f.read()
        except Exception as e:
            logError('Cannot open %s [%s]' % (self.__xmlfn, e))
            logError('Cannot process XML')
            return
        self.__xmlstring = re.sub(' xmlns="[^"]+"', '',
                                  self.__xml_file_content, count=1)
        self.__root = ET.fromstring(self.__xmlstring)

    def get_root_element(self):
        return self.__root

    def find_index_of_element(self, tag, root_el=None):
        if root_el is None:
            root_el = self.__root

        _children = []
        try:
            _children = root_el.getchildren()
        except AttributeError as e:
            _children = root_el.findall("./")

        for idx, child_el in enumerate(_children):
            if child_el.tag == tag:
                return idx

    def make_element(self, tag, value=None):
        el = Element(tag)
        if value is not None:
            el.text = value
        return el

    def make_sub_element(self, root_el, tag, value=None, attrib=None):
        if attrib:
            sub_el = SubElement(root_el, tag, attrib)
        else:
            sub_el = SubElement(root_el, tag)
        if value is not None:
            sub_el.text = value
        return sub_el

    def add_attribute(self, el, attr, val):
        if el is not None:
            el.set(attr, val)
        return el

    def insert_after_element(self, tag, insert_el, root_el=None):
        if root_el is None:
            root_el = self.__root
        idx = self.find_index_of_element(tag, root_el)
        if idx:
            root_el.insert(idx+1, insert_el)
        else:
            logError('Could not find index of %s' % (tag,))

    def remove_element(self, xp, root_el=None):
        if root_el is None:
            root_el = self.__root
        element_to_remove = root_el.find(xp)
        if element_to_remove is not None:
            logInfo('Removing %s from %s' % (xp, root_el))
            root_el.remove(element_to_remove)

    def findall(self, xpath, root_el=None):
        if root_el is None:
            root_el = self.__root
        return root_el.findall(xpath)

    def find(self, xpath, root_el=None):
        if root_el is None:
            root_el = self.__root
        return root_el.find(xpath)

    def writeXml(self, fn):
        xmldecl = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        xmlcontent = ET.tostring(self.__root).decode('utf8')
        try:
            with open(fn, 'w') as f:
                f.write(xmldecl + '\n' + xmlcontent)
        except Exception as e:
            logError('Could not save XML file %s [%s]' % (fn, e))


class ebCluConfigCreator(object):
    """
    Replaces the template values to correct values in config xml.
    """
    OUTPUT_ADMIN_XML_FILE_NAME = 'output_admin.xml'
    OUTPUT_CLIENT_XML_FILE_NAME = 'output_client.xml'

    def __init__(self, in_json, template_json=None, template_xml=None):
        """
        in_json: actual json with good values to be used in template_xml.
                 This is already a parsed json.
        template_json: Optional input which specifies what keys
                needs to be replaced with values from "in_json".
                If not specified it looks at a particular folder in disk.
        template_xml: OPtional input which specifies the xml with template
                values that will be replaced with values from good json.
                If not specified it looks at a particular folder in disk.

        """
        self.__in_json_parsed = in_json
        self.__template_json = str(template_json)
        self.__template_xml = str(template_xml)
        self.__template_json_parsed = None
        self.__outDir = '.'
        self.logger = ebLogGetBMCLogger()
        self.util = BmcUtil(self.logger)
        self.bmcConfig = BmcConfig(self.logger)
        self.getTemplateBasePath()
        self.__lastError = gBMCError['NO_ERROR']
        self.__version = None
        self.__ignore_nodes = []
        # self.__ignore_nodes = ['pdu']
        self.__domu_hostnames = []

    def validate(self):
        self.validateJsonContent(self.__in_json_parsed)

    def getTemplateBasePath(self):
        self.__templateDir = self.bmcConfig.getValue(
                                        ['alter_template', 'templates_dir'],
                                        './vcncloud/templates')
        logInfo('Template base directory: %s' % (self.__templateDir,))

    def setOutputDir(self, outDir):
        self.__outDir = outDir

    def getLastError(self):
        return self.__lastError

    def setLastError(self, err):
        self.__lastError = gBMCError.get(err, 'UNKNOWN_ERROR')

    def validateJsonContent(self, var, trackstr=''):
        # Check if we've any NULL values in input var
        if not var:
            logError('Input JSON value @%s is either blank or None' %
                     (trackstr,))
            self.setLastError("INVALID_JSON_CONTENT")
            raise Exception("INVALID_JSON_CONTENT")
        elif isinstance(var, dict):
            for key in var:
                self.validateJsonContent(var[key], trackstr+'{'+str(key)+'}')
        elif isinstance(var, list):
            for idx in range(len(var)):
                self.validateJsonContent(var[idx], trackstr+'['+str(idx)+']')

    def __get_template_json_path(self, cluster_dict):
        return os.path.join(
            self.__templateDir,
            cluster_dict.get('cluster_size') + '.template.json')

    def __get_template_xml_path(self, cluster_dict):
        """
        Figures out the template XML file path from the "xml_type" field in
        cluster_dict.
        """
        valid_types = ['public_vcn_x6', 'public_classic_x6', 'public_vcn_x7',
                       'public_classic_x7', 'public_vcn_x8', 
                       'public_classic_x8', 'public_vcn_x8m']
        xml_type = cluster_dict.get('xml_type')
        if xml_type is not None:
            if xml_type not in valid_types:
                raise Exception("Unsupported xml_type [%s]. Supported are %s" %
                                (xml_type, valid_types))
        else:
            xml_type = 'public_vcn_x6'
            logWarn('xml_type not specified, defaulting to "public_vcn_x6"')

        # Template file for Gen1/nbm_x6:
        # 3cell2comp2ibsw2pdu1ethsw.template.nbm_x6.xml
        # Template file for BMC:
        # 3cell2comp2ibsw2pdu1ethsw.template.bm_x6.xml
        # likewise
        begin = os.path.join(self.__templateDir,
                             cluster_dict.get('cluster_size'))
        parts = [begin, 'template']
        parts.append(xml_type)
        parts.append('xml')
        return '.'.join(parts)

    def __generic_iter(self, template, coming, outdict, traversal=[]):
        """
        Based on type of template variable, it iterates further untill
        it is presented with a string. When string is found, it assigns
        the template as a key to outdict and "coming" as a value to outdict.
        Formats of template and "coming" must exactly match so that all keys
        present in template is present in "coming" and length of any list are
        same in both. This function can handle any level of nestedness of
        dictionaries or lists within each other.
        """
        # There is no point in allowing integer as a templatekey, check for it
        try:
            int(template)
        except:
            pass
        else:
            return outdict

        if isinstance(template, dict):
            # If it is a dictionary, check each key value
            for k, v in six.iteritems(template):
                # Call itself again
                try:
                    traversal.append('Key:' + str(k))
                    self.__generic_iter(template[k], coming[k],
                                        outdict, traversal)
                except KeyError as e:
                    # The key might be a _pick_ key, try with it
                    pick_key = k + '_pick_'
                    if pick_key in coming:
                        self.__generic_iter(template[k], coming[pick_key],
                                            outdict, traversal)
                    else:
                        logError("%s key is missing in input.json [%s]" %
                                 (k, str(e)))
                        logError("traversal path = %s" %
                                 (','.join(traversal),))
                        self.setLastError("MISMATCHED_JSONS")
                        raise
        elif isinstance(template, list):
            # If it is a list, check for each item
            for index, item in enumerate(template):
                # Call itself again
                try:
                    traversal.append('idx:' + str(index))
                    self.__generic_iter(template[index], coming[index],
                                        outdict, traversal)
                except IndexError as e:
                    logError("%s index is missing for list:%s "
                             "in input.json [%s]" % (index, str(list), str(e)))
                    logError("traversal path = %s" % (','.join(traversal),))
                    self.setLastError("MISMATCHED_JSONS")
                    raise
        else:
            # A string, add template as key and "coming" as value
            # Make sure the value is in string
            outdict[template] = str(coming)
        return outdict

    def __prepare_kv(self, in_dict, tmplt_dict):
        """
        Returns a dictionary of tokens and values to replace those.
        """
        out_dict = {}
        return self.__generic_iter(tmplt_dict, in_dict, out_dict)

    def __substitute_values_in_xml(self, template_xml_path, kv_pairs):
        """
        Reads content of template_xml_path file and returns the
        modified xml after substituted tokens from the kv_pairs dictionary.
        """
        lines = self.util.readFile(template_xml_path)
        # We must have some content and a valid dictionary of kv_pairs
        if lines and kv_pairs:
            for k, v in six.iteritems(kv_pairs):
                lines = lines.replace(k, v)
        return lines

    def __get_special_fields(self, in_dict, lookfor='_pick_'):
        """
        Some fields in input_dict are special, we need to pick up
        those key value pairs for putting in response json.
        The special fields are tagged with "_pick_" at the end of the key.
        Example: "temporary_ecs_rack_name_pick_" : "temp_cluster"
        This function expects to have "nodes" key inside it whose value is
        a list of dictionaries.
        """
        _out_dict = {"nodes": []}
        # For the outermost keys
        for k, v in six.iteritems(in_dict):
            if k.endswith(lookfor):
                _out_dict[k[:-len(lookfor)]] = v
        if not in_dict.get('customer_network'):
            return _out_dict
        # For the items inside "nodes"
        for each_node in in_dict['customer_network'].get("nodes", {}):
            node_dict = {}
            for k, v in six.iteritems(each_node):
                if k.endswith(lookfor):
                    node_dict[k[:-len(lookfor)]] = v
            if len(node_dict) > 1:
                # We don't want to put oracle_hostname_pick
                # as the single entry there. Only if there are more
                # entries, append it in _our_dict
                _out_dict['nodes'].append(node_dict)

        logInfo("Special fields found:\n%s" %
                (pprint.pformat(_out_dict, indent=4),))
        return _out_dict

    def get_kv_host_pairs(self, inDict, tokenDict):
        """
        It prepares a dictionary of key value pairs of token and value.
        """
        hostnameKey = 'oracle_hostname_pick_'
        domainKey = 'oracle_domain'
        ilomHostKey = 'ilom_hostname'
        ilomDomainKey = 'ilom_domain'
        nathostKey = 'nat_hostname_pick_'
        outNodes = []

        for idx, node in enumerate(tokenDict.get('nodes')):
            out = {}
            inDictNode = inDict['nodes'][idx]
            # Create a tuple (findby, actualval)
            ht = (node[hostnameKey], inDictNode[hostnameKey])
            out[hostnameKey] = ht
            # Create a tuple of domain
            dt = (node[domainKey], inDictNode[domainKey])
            out[domainKey] = dt
            # If the node is not IBSW, then it will have ILOM
            if inDictNode['node_type'].upper() != 'IBSW':
                it = (node[ilomHostKey], inDictNode[ilomHostKey])
                out[ilomHostKey] = it
                # Create a tuple of domain
                dt = (node[ilomDomainKey], inDictNode[ilomDomainKey])
                out[ilomDomainKey] = dt
            if inDictNode['node_type'].upper() == 'COMPUTE':
                if inDictNode.get(nathostKey):
                    # BMC Specific
                    logInfo('token node: %s' % (node,))
                    logInfo('input node: %s' % (inDictNode,))

                    it = (node[nathostKey], inDictNode[nathostKey])
                    out[nathostKey] = it

            outNodes.append(out)
        logInfo("Hostname mapping: \n%s" % (
                               pprint.pformat(outNodes, indent=4),))
        return outNodes

    def getOedaCliPath(self):
        return self.bmcConfig.getValue(
                               ['alter_template', 'oedacli_path'],
                               'oedacli/oedacli')

    def getAdminHostName(self, idx=None):
        _nodes = self.__oeda.getNodes(self.__cur_node_type)
        if idx is None:
            idx = self.getIndex()
        try:
            _networks = _nodes[idx]['networks']['network']
        except Exception as e:
            logWarn("couldn't get admin hostname [%s]" % (e,))
            return None
        for _network in _networks:
            if _network['networkType'] == 'admin':
                return _network['hostName']
        logError('cannot find admin hostname for %s (index: %s), '
                 'nodes: %s, networks: %s' %
                 (self.__cur_node_type, idx, _nodes,
                  _networks))
        return None

    def getMachineHostName(self, idx=None):
        _nodes = self.__oeda.getNodes(self.__cur_node_type)
        logInfo('__cur_node_type: %s, _nodes=%s' % (self.__cur_node_type,
                                                    pprint.pformat(_nodes,
                                                                   indent=4)))
        if idx is None:
            idx = self.getIndex()
        return _nodes[idx]['hostName']

    def getDomuMachineHostName(self, idx=None):
        _domus = self.__oeda.getDomus()
        if idx is None:
            idx = self.getIndex()
        return _domus[idx]['hostName']

    def processIlom(self):
        machineHostName = self.getMachineHostName()
        # Ilom Network
        self.__oeda.alter(
            'network',
            dict(ip=self.ns.ilom_ip, netmask=self.ns.ilom_netmask,
                 gateway=self.ns.ilom_gateway),
            dict(hostname=machineHostName, networktype='ilom'))
        # Ilom DNS & NTP
        self.__oeda.alterDnsNtp(','.join(self.ns.ilom_dns),
                                ','.join(self.ns.ilom_ntp),
                                machineHostName, 'ilom')
        # Ilom Timezone
        if self.__timezone:
            self.__oeda.alter('ilom', dict(timezone=self.__timezone),
                              dict(hostname=machineHostName))

        # Ilom Hostname & Domainname
        self.__oeda.alter('network',
                          dict(hostname=self.ns.ilom_hostname,
                               domainname=self.ns.ilom_domain),
                          dict(hostname=machineHostName, networktype='ilom'))

    def processCommon(self):
        dnsStr = ','.join(self.ns.oracle_dns)
        ntpStr = ','.join(self.ns.oracle_ntp)

        machineHostName = self.getMachineHostName()
        logInfo('VM machineHostName : %s' % (machineHostName))
        self.__oeda.alterNetwork(self.ns.priv1, machineHostName, 'private', 1)
        self.__oeda.alterNetwork(self.ns.priv2, machineHostName, 'private', 2)

        logInfo('VM NS priv1: %s' % (self.ns.priv1))
        logInfo('VM NS priv2: %s' % (self.ns.priv2))
        # Timezone
        if self.__timezone:
            self.__oeda.alter('machine',
                              dict(timezone=self.__timezone),
                              dict(hostname=machineHostName))
        # DNS & NTP
        self.__oeda.alterDnsNtp(dnsStr, ntpStr, machineHostName, 'machine')
        # Admin Network
        self.__oeda.alter(
            'network',
            dict(ip=self.ns.oracle_ip,
                 netmask=self.ns.oracle_netmask,
                 gateway=self.ns.oracle_gateway),
            dict(hostname=self.getAdminHostName(),
                 networktype='admin'))

        if self.__cur_node_type == 'cell':
           logInfo('VM cell machineHostName : %s' % (machineHostName))
           # Storage PKEY
           if (self.__oeda.getSwitchType() == 'ibsw'):
               self.__oeda.alterPkey(self.ns.storage_pkey,
                                     self.getMachineHostName(), 'storage')

    def alterNat(self):
        clientMac = None
        bkupMac = None
        if self.ns.etherface_types:
            clientMacIndex = self.ns.etherface_types.index('DB_CLIENT')
            bkupMacIndex = self.ns.etherface_types.index('DB_BACKUP')
            if self.ns.macs_pick_:
                clientMac = self.ns.macs_pick_[clientMacIndex]
                bkupMac = self.ns.macs_pick_[bkupMacIndex]
        if self.ns.caviums:
            logInfo('Altering Caviums')
            self.__oeda.editCaviumPorts(self.ns.etherfaces, self.ns.caviums,
                                        self.ns.macs_pick_,
                                        self.ns.oracle_hostname_pick_)
        if self.ns.nat_ip_pick_:
            logInfo('Altering NAT')
            self.__oeda.alter(
                'network',
                dict(natip=self.ns.nat_ip_pick_,
                     nathostname=self.ns.nat_hostname_pick_,
                     natnetmask=self.ns.nat_netmask,
                     natdomainname=self.ns.nat_domainname,
                     mac=clientMac),
                dict(hostname=self.ns.hostname,
                     networktype='client'))

        if bkupMac:
            logInfo('Altering Backup MAC')
            self.__oeda.alter(
                'network',
                dict(mac=bkupMac),
                dict(hostname=self.ns.hostname,
                     networktype='backup'))

    def processAdminHostName(self):
        self.__oeda.alter(
            'network',
            dict(hostname=self.ns.oracle_hostname_pick_,
                 domainname=self.ns.oracle_domain),
            dict(hostname=self.getMachineHostName(),
                 networktype='admin'))

    def processSwitchNetwork(self):
        logInfo('Alter Switch network for %s' %
                (self.ns.oracle_hostname_pick_,))
        self.__oeda.alter(
            'network',
            dict(ip=self.ns.oracle_ip,
                 netmask=self.ns.oracle_netmask,
                 gateway=self.ns.oracle_gateway,
                 hostname=self.ns.oracle_hostname_pick_,
                 domainname=self.ns.oracle_domain),
            dict(networkhostname=self.getAdminHostName()))

    def getActionsObj(self):
        actionsMap = {
              'compute': ['Common', 'Ilom', 'AdminHostName'],
              'cell': ['Common', 'Ilom', 'AdminHostName'],
              'ibsw': ['SwitchNetwork'],
              'spinesw': ['SwitchNetwork'],
              'pdu': ['SwitchNetwork']
              }
        actionsObj = Actions(self, actionsMap[self.__cur_node_type])
        return actionsObj

    def incIndex(self):
        self.__counter[self.__cur_node_type] += 1

    def getIndex(self):
        return self.__counter[self.__cur_node_type]

    def processNode(self):
        actions = self.getActionsObj()
        actions.do()
        self.incIndex()

    def alterScans(self, scans):
        if scans:
            for scan in scans:
                self.__oeda.alterScans(scan['hostname'], scan['port'],
                                       scan['ips'])

    def alterClusterPatchList(self, patchlist):
        if patchlist:
            self.__oeda.alter(
                    'cluster',
                    dict(patchlist=','.join(patchlist)),
                    dict(clustername=self.__oeda.getClusterName()))

    def alterDnsNtp(self, dnsStr, ntpStr):
        if dnsStr:
            self.__oeda.alterDns(dnsStr, self.ns.hostname, 'machine')
        if ntpStr:
            self.__oeda.alterNtp(ntpStr, self.ns.hostname, 'machine')

    def alterMachineTimeZone(self, tz):
        if tz:
            self.__oeda.alter(
                    'machine',
                    dict(timezone=tz),
                    dict(hostname=self.ns.hostname))

    def alterVip(self):
        if self.ns.vip is None:
            return
        self.__oeda.alter(
                'vip',
                dict(name=self.ns.vip['name'],
                     domainname=self.ns.vip['domainname'],
                     ip=self.ns.vip['ip']),
                dict(hostname=self.ns.hostname))

    def alterPkey(self):
        if (self.__oeda.getSwitchType() == 'ibsw'):
            self.__oeda.alterPkey(self.ns.compute_pkey, self.ns.hostname,
                                  'compute')
            self.__oeda.alterPkey(self.ns.storage_pkey, self.ns.hostname,
                                  'storage')

    def alterDomuAdminNetwork(self):
        if self.ns.admin is not None:
            self.__oeda.alterNetwork(self.ns.admin, self.ns.hostname, 'admin')
            if 'hostname' in self.ns.admin:
                self.ns.hostname = self.ns.admin['hostname']

    def alterDomuClientNetwork(self):
        if self.ns.client is not None:
            self.__oeda.alterNetwork(self.ns.client, self.ns.hostname,
                                     'client')
            if 'hostname' in self.ns.client:
                self.ns.hostname = self.ns.client['hostname']

    def alterMachineAdapter(self, adapter_type, admin_or_client, hostname):
        if admin_or_client is None:
            return
        setdict = {}
        if adapter_type == 'gateway':
            setdict['gatewayadapter'] = admin_or_client
        else:
            setdict['hostnameadapter'] = admin_or_client
        self.__oeda.alter('machine', setdict, dict(hostname=hostname))

    def alterDomuPrivateNetwork(self):
        self.__oeda.alterNetwork(self.ns.priv1, self.ns.hostname, 'private', 1)
        self.__oeda.alterNetwork(self.ns.priv2, self.ns.hostname, 'private', 2)
        self.__oeda.alterNetwork(self.ns.clusterpriv1, self.ns.hostname,
                                 'private', 3)
        self.__oeda.alterNetwork(self.ns.clusterpriv2, self.ns.hostname,
                                 'private', 4)

    def alterDomuBackupNetwork(self):
        self.__oeda.alterNetwork(self.ns.backup, self.ns.hostname, 'backup')

    def alterXmlVmSizes(self, rxp, inDict):
        # TODO: This way of manipulating raw XML will not be required once
        # OEDACLI supports alterations of the VMSizes. We'll revisit once the
        # fix is made in OEDACLI (bug# 26823258)
        try:
            nodes = inDict['customer_network']['nodes']
        except Exception as e:
            logError('Cannot alter XML VM Sizes [%s]' % (e,))
            return

        for node in nodes:
            try:
                vmsizename = node['vmsizename']
                hostname_adapter = node['hostnameadapter']
                network = node[hostname_adapter]
                hostname = network['hostname'] + '.' + network['domainname']
            except Exception as e:
                logWarn('Cannot alter XML VM Sizes [%s]' % (e,))
                continue
            # Find the machine
            xpath = './machines/machine/[hostName="%s"]' % (hostname,)
            machine_el = rxp.find(xpath)
            # Remove the VmSizeName part in XML for this machine
            rxp.remove_element('./vmSizeName', machine_el)
            # Add the VmSizeName part in XML for this machine
            vmsize_el = rxp.make_element('vmSizeName')
            rxp.add_attribute(vmsize_el, 'id', vmsizename)
            rxp.insert_after_element('osType', vmsize_el, machine_el)
            logInfo('Altered VM Size to %s for %s' % (vmsizename, hostname))

        # Alter VmSize Definition
        vmsizes_def = inDict['customer_network'].get('vmsizes_def')
        if not vmsizes_def:
            logWarn('vmsizes_def missing in JSON')
            return
        vmsizes_el = rxp.find('./vmSizes')
        if vmsizes_el is None:
            logError('vmSizes element missing in XML, cannot alter VM Sizes.')
            return

        for sizeid, dictval in six.iteritems(vmsizes_def):
            # Check if it is present
            vmsize_el = rxp.find('./vmSizeName[@id="%s"]' % (sizeid,),
                                 vmsizes_el)
            if vmsize_el is None:
                vmsize_el = rxp.make_sub_element(vmsizes_el, 'vmSizeName')
                rxp.add_attribute(vmsize_el, 'id', sizeid)
            for attr, value in six.iteritems(dictval):
                vmattr_el = rxp.find('./vmAttribute[@id="%s"]' % (attr,),
                                     vmsize_el)
                if vmattr_el is None:
                    vmattr_el = rxp.make_sub_element(vmsize_el, 'vmAttribute')
                    rxp.add_attribute(vmattr_el, 'id', attr)
                vmattr_el.text = value

    def processByOedaNoToken(self, inDict, templateXml):
        templateXmlFullPath = os.path.realpath(templateXml)
        oedaCliPath = self.getOedaCliPath()
        try:
            self.__oeda = OedaProcessor(
                templateXmlFullPath, self.__outDir,
                oedaCliPath, ebLogGetBMCLogger())
            self.__oeda.loadElements()
        except Exception as e:
            logError('Encountered exception while loading XML [%s]' % (e,))
            self.setLastError('XML_LOADING_ERROR')
            return ''

        # Init the Counter
        self.__counter = Counter()

        # Change the customer name section
        self.__oeda.alterCustomerName(inDict['customer_name'])

        self.__timezone = inDict.get('time_zone')
        # Traverse through each input json node and process it
        for node in inDict['nodes']:
            if node['node_type'].lower() in self.__ignore_nodes:
                logWarn('Ignoring alteration for %s' % (node['node_type'],))
                continue
            self.__curNode = node
            self.ns = NameSpace(self.__curNode)
            self.__cur_node_type = self.ns.node_type.lower()
            try:
                self.processNode()
            except Exception as e:
                logError('Caught exception while altering XML [%s]' % (e,))
                self.setLastError('XML_PROCESSING_ERROR')
                raise

        self.__oeda.saveXmlFile(ebCluConfigCreator.OUTPUT_ADMIN_XML_FILE_NAME)
        success, outfile = self.__oeda.processCmds()
        self.util.logFileContent('oeda command output', outfile)
        if not success:
            # Go ahead with generating the files but treat it as failure
            self.setLastError('OEDACLI_LOG_CONTAINS_ERRORS')
        return self.__oeda.getOutXmlPath()

    def getTemplatePaths(self, inputClusterJson):
        """
        Returns the tokenJsonPath, templateXmlPath
        """
        tokenJson = self.__get_template_json_path(inputClusterJson)
        templateXml = self.__get_template_xml_path(inputClusterJson)
        return tokenJson, templateXml

    def doOedaProcessingNoToken(self, inputClusterJson, templateXml):
        logInfo('Processing input json through oeda cli')
        # Run the template Xml through OEDA
        return self.processByOedaNoToken(inputClusterJson, templateXml)

    def doTextSubstitution(self, inputClusterJson, tokenJsonParsed,
                           templateXml):
        logInfo('Processing input json through text substitution')
        # Run the template xml through text substitution.
        kv_pairs = self.__prepare_kv(inputClusterJson, tokenJsonParsed)
        logInfo("Calculated Substitution pairs:\n%s" % (
                                    pprint.pformat(kv_pairs, indent=4),))
        _out_xml = self.__substitute_values_in_xml(templateXml, kv_pairs)
        return _out_xml

    def generateClusterName(self, inDict):
        """
        Traverse through each node and find the node Numbers to generate
        clusterName using the format given below:
        phx300816exd-d0-01-04-cl-01-07-clu01
        Formula: <4 char AD - phx3><5 char cabinet id - 00816>
        <product id - exd>-<dom0 - d0 >-<first dom0 - 01>-<last dom0 - 04>-
        <cell - cl>-<first cell - 01>-<last cell - 07>-<cluster on this set of
        hardware - clu01>
        """
        cellNumbers = []
        computeNumbers = []
        clusterNumber = None
        ad = None
        for node in inDict['nodes']:
            nodeType = node['node_type'].upper()
            if nodeType == 'CELL' or nodeType == 'COMPUTE':
                try:
                    hn = node['oracle_hostname_pick_']

                    # Hostname example: phx300814exdd007
                    if not ad:
                        ad, cabinet, prod = hn[:4], hn[4:][:5], hn[9:][:3]
                    nodeNumber = hn[14:][:2]
                    if nodeType == 'CELL':
                        cellNumbers.append(nodeNumber)
                    else:
                        if not clusterNumber:
                            clusterNumber = node['nat_hostname_pick_'][-2:]
                        computeNumbers.append(nodeNumber)
                except Exception as e:
                    logError('Exception retrieving node details ' +
                             'from hostname: [%s]' % (e))
                    return ''

        computeNumbers.sort()
        firstCompute, lastCompute = computeNumbers[0], computeNumbers[-1]
        cellNumbers.sort()
        firstCell, lastCell = cellNumbers[0], cellNumbers[-1]

        # Now generate the clustername
        clusterName = ad + cabinet + prod
        clusterName += '-d0-' + firstCompute + '-' + lastCompute
        clusterName += '-cl-' + firstCell + '-' + lastCell
        clusterName += '-clu' + clusterNumber
        return clusterName

    def __sortNodes(self, inJson, tokenJson):
        """
        Sorts the nodes based on node sequences
        """
        _sorted_in_nodes = sorted(inJson['nodes'],
                                  key=lambda k: k['node_sequence'])
        inJson['nodes'] = _sorted_in_nodes
        _sorted_token_nodes = sorted(tokenJson['nodes'],
                                     key=lambda k: int(k['node_sequence']))
        tokenJson['nodes'] = _sorted_token_nodes
        inNs = [a['node_sequence'] for a in inJson['nodes']]
        tokenNs = [a['node_sequence'] for a in tokenJson['nodes']]
        tokenNs = tokenNs[:len(inNs)]
        for i, j in zip(tokenNs, inNs):
            logInfo("Matching Node Sequences: token [%s] --> in [%s]" % (i, j))

    def __process_files(self):
        """
        Iterates over template json, compares with the input json and
        creates a dictionary of token strings with values to replace with.
        Finally it creates xml file for for each cluster with replaced values.
        """
        outXml = None
        _pick_dict = {}
        # The input json is already parsed, print the content
        logInfo('Input json content:\n%s' %
                (json.dumps(self.__in_json_parsed, indent=4),))
        # Get the config values
        alterMethod = self.bmcConfig.getValue(['alter_template', 'method'],
                                              'oeda')
        logInfo("BmcConfig 'alter method' is: %s" % alterMethod)
        # Iterate over each cluster
        for cluster in self.__in_json_parsed['clusters']:
            # For now we are supporting a single cluster #TBD
            tokenJson, templateXml = self.getTemplatePaths(cluster)
            if self.__version is not None:
                # This is non-BMC - alterMethod must be only 'oeda'
                alterMethod = 'oeda'
            # Make sure that the token JSON exists
            if not os.path.isfile(tokenJson) and\
               alterMethod.find('text') != -1:
                logError('Missing token JSON: %s' % (tokenJson,))
                self.setLastError('MISSING_TOKEN_JSON')
                break
            # Make sure that the template XML exists
            if not os.path.isfile(templateXml):
                logError('Missing template XML: %s' % (templateXml,))
                self.setLastError('MISSING_TEMPLATE_XML')
                break

            self.util.logFileContent('Template Xml', templateXml)

            # If the clustername is being supplied by the input json, use that.
            # Otherwise generate one.
            if not cluster.get('customer_name'):
                logInfo('Customer name not present in input json: '
                        'trying to generate')
                cluster['customer_name'] = self.generateClusterName(cluster)
            # Following will ensure that for Older type of input JSONs, we
            # correctly put the customer name
            cluster['temporary_ecs_rack_name_pick_'] = cluster['customer_name']

            _pick_dict = self.__get_special_fields(cluster)
            outXml = None
            outXmlContent = ''
            # Generate the XML
            if alterMethod.find('oeda') != -1:
                # Generate by OEDA
                self.readOedaVersion()
                outXml = self.doOedaProcessingNoToken(cluster, templateXml)
                self.util.logFileContent('Oeda generated Xml', outXml)

            elif alterMethod.find('text') != -1:
                # Verify that this method is being used only for BM
                if self.__version is not None:
                    logError(
                        'Text substitution is only valid for BM type of '
                        'input JSON. Please change bmcconfig.json entry of '
                        '"alter_template:method"')
                    self.setLastError('UNSUPPORTED_ALTER_METHOD')
                else:
                    # Generate by Token Substitution
                    self.util.logFileContent('Token Json', tokenJson)
                    tokenJsonParsed = self.util.getParsedJson(tokenJson)
                    # Sort the nodes based on node sequence first
                    self.__sortNodes(cluster, tokenJsonParsed)
                    outXmlContent = self.doTextSubstitution(
                        cluster, tokenJsonParsed, templateXml)
                    outXml = os.path.join(
                        self.__outDir,
                        ebCluConfigCreator.OUTPUT_ADMIN_XML_FILE_NAME)
                    self.util.writeFile(outXmlContent, outXml)
                    self.util.logFileContent(
                        'Token substitution generated Xml', outXml)
            else:
                logError('Unsupported Alter Method [%s]' % (alterMethod,))
                self.setLastError('UNSUPPORTED_ALTER_METHOD')

            # Process raw XML
            _xp = self.getXmlProcessor(outXml)

            # Process the alerts section, this section is added for all type
            # of XMLs (BMC + non-BMC)
            self.processAlerts(_xp, cluster.get('alerts'))
            _xp.writeXml(outXml)
            # For now we are supporting a single cluster #TBDBM
            break
        return outXml, _pick_dict

    def getXmlProcessor(self, xml_filename):
        return XMLProcessor(xml_filename)

    def processAlerts(self, xmlprocessor, alertsJson):
        # TODO:
        # This way of manipulating raw XML will not be required when OEDA
        # supports the alteration of alerts from OEDACLI. This will be replaced
        # when the feature is available in OEDACLI (bug# 26823258).
        if alertsJson is None:
            return
        valid_tags = ['alertType', 'clusterSNMPServer', 'clusterSNMPPort',
                      'clusterSNMPCommunity', 'clusterSMTPAddress',
                      'clusterSMTPFrom', 'clusterSMTPTxtFrom',
                      'clusterSMTPServer', 'clusterSMTPPort',
                      'clusterSMTPUseSsl']
        valid_protocols = ['smtp', 'snmp']
        valid_alert_types = ['cell']
        found_protocols = []
        xmlprocessor.remove_element('./alerts')
        _alerts_el = xmlprocessor.make_element('alerts')
        xmlprocessor.insert_after_element('storage', _alerts_el)
        for _alert_in_json in alertsJson:
            protocol = _alert_in_json.get('protocol')
            alert_type = _alert_in_json.get('alertType')
            if alert_type not in valid_alert_types:
                logError('alertType %s is not supported, supported: %s' %
                         (alert_type, valid_alert_types))
                return

            if protocol not in valid_protocols:
                logError('protocol "%s" is not supported, supported: %s' %
                         (protocol, valid_protocols))
                return
            found_protocols.append(protocol)
            _alert_el = xmlprocessor.make_sub_element(_alerts_el, 'alert')
            xmlprocessor.add_attribute(_alert_el, 'id', protocol+'_alert')
            for key in valid_tags:
                if _alert_in_json.get(key):
                    if key == 'clusterSMTPAddress':
                        val = '#'.join(_alert_in_json[key])
                    else:
                        val = str(_alert_in_json[key])
                    xmlprocessor.make_sub_element(_alert_el, key, val)
        # proceed if there are valid items
        if not found_protocols:
            return
        # For every cell, we need to add an 'alerts' section in the xml
        cells_xpath = "./machines/machine/[machineType='storage']"
        storage_machine_els = xmlprocessor.findall(cells_xpath)
        for el in storage_machine_els:
            xmlprocessor.remove_element('./alerts', el)
            alerts_el = xmlprocessor.make_element('alerts')
            for protocol in valid_protocols:
                if protocol in found_protocols:
                    alert_el = xmlprocessor.make_sub_element(alerts_el,
                                                             'alert')
                    xmlprocessor.add_attribute(alert_el, 'id',
                                               protocol+'_alert')
            xmlprocessor.insert_after_element('virtual', alerts_el, el)

        # Save the XML
        logInfo('Added alerts section')
        return

    def process_files(self):
        """
        Generates the configuration XML by substituting the tokens.
        """
        return self.__process_files()

    def readOedaVersion(self):
        version = None
        # oedacli path
        path = self.bmcConfig.getValue(['alter_template', 'oedacli_path'],
                                       './')
        # Get the parent directory of oedacli binary
        parent_dir = os.path.dirname(path)
        # Path of the properties file
        properties_file_path = os.path.join(parent_dir,
                                            'properties/es.properties')
        # Make sure the file is there
        if not os.path.isfile(properties_file_path):
            logError('Could not find the properties file at %s' %
                     (properties_file_path,))
            return version
        # Get the version info from the file
        try:
            with open(properties_file_path) as f:
                for line in f.readlines():
                    try:
                        key, value = line.split('=')
                        if key.strip().upper() == 'OCVERSION':
                            version = value.strip()
                            break
                    except Exception:
                        pass
        except Exception as e:
            logError('Could not find OEDACLI version in %s [%s]' %
                     (properties_file_path, e))
        else:
            logInfo('Found OEDACLI Version: %s' % (version,))
        return version

    def generateOutputFileName(self):
        dom0s = self.__oeda.getDom0HostNames()
        cells = self.__oeda.getCellHostNames()
        fn = 'gen-' + dom0s[0] + '-' + dom0s[-1] + '_'\
             + cells[0] + '-' + cells[-1]
        if self.__domu_hostnames:
            fn += '_' + self.__domu_hostnames[0] + '-' +\
                  self.__domu_hostnames[-1]
        fn += '.xml'
        return fn

    def addClientInfo(self, inXml, clientDict):
        """
        Adds the client information in the inXml and saves the altered XML.
        Returns the path to altered XML.
        """
        self.readOedaVersion()
        oedaCliPath = self.getOedaCliPath()
        # inXml is a XML string, but oeda takes a file name, write this
        # into a file and send the path info to oeda
        templateXmlName = 'client_network_template.xml'
        xmlPath = os.path.join(self.__outDir, templateXmlName)
        with open(xmlPath, 'wb') as f:
            f.write(inXml.encode('utf8'))
        self.util.logFileContent(templateXmlName, xmlPath)
        logInfo('client_input_json Content: \n%s\n' % (str(clientDict),))
        self.__oeda = OedaProcessor(
            xmlPath, self.__outDir,
            oedaCliPath, ebLogGetBMCLogger())
        self.__oeda.loadElements()

        # Start alterations
        dnsStr = None
        ntpStr = None
        tz = None
        customerNetwork = clientDict.get('customer_network')
        if customerNetwork:
            self.alterScans(customerNetwork.get('scans'))
            networkServices = customerNetwork.get('network_services')
            if networkServices:
                dnsStr = ''
                ntpStr = ''
                dnslist = networkServices.get('dns')
                if dnslist:
                    dnsStr = ','.join(dnslist)
                else:
                    logWarn('dns entry not found in network services')
                ntplist = networkServices.get('ntp')
                if ntplist:
                    ntpStr = ','.join(ntplist)
                else:
                    logWarn('ntp entry not found in network services')
            tz = customerNetwork.get('timezone')

        for idx, node in enumerate(customerNetwork.get('nodes')):
            self.ns = NameSpace(node)
            try:
                self.ns.hostname =\
                    self.__oeda.lookupDomuMachineHostName(
                                   self.ns.oracle_hostname_pick_)
            except Exception as e:
                logError(str(e))
                self.setLastError("DOMU_LOOKUP_FAILED")
                raise
            self.alterDnsNtp(dnsStr, ntpStr)
            self.alterMachineTimeZone(tz)
            self.alterVip()
            if self.ns.admin is not None and\
               self.ns.admin.get('hostname') is not None:
                self.__domu_hostnames.append(self.ns.admin['hostname'])
            elif self.ns.client is not None and\
               self.ns.client.get('hostname') is not None:
                self.__domu_hostnames.append(self.ns.client['hostname'])
            self.alterNat()
            self.alterDomuAdminNetwork()
            self.alterDomuClientNetwork()
            self.alterMachineAdapter('gateway', self.ns.gatewayadapter,
                                     self.ns.hostname)
            self.alterMachineAdapter('hostname', self.ns.hostnameadapter,
                                     self.ns.hostname)
            self.alterDomuPrivateNetwork()
            self.alterDomuBackupNetwork()
            self.alterPkey()

        self.__oeda.alterDatabaseHomes(clientDict.get('databasehomes'))
        self.__oeda.alterDiskgroups(customerNetwork.get('diskgroups'))
        self.__oeda.alterCustomerName(clientDict.get('customer_name'))
        # Make sure to alter the cluster at the end, otherwise clustername
        # identifier will be lost
        self.__oeda.alterCluster(clientDict.get('cluster'))
        if self.bmcConfig.getValue(['alter_template', 'gen_xml_fn'], False):
            output_file_name = self.generateOutputFileName()
        else:
            output_file_name = ebCluConfigCreator.OUTPUT_CLIENT_XML_FILE_NAME
        logInfo('Saving output XML file: %s' % (output_file_name,))
        self.__oeda.saveXmlFile(output_file_name)
        self.__oeda.saveCmdFile('oeda_client_cmds.txt')
        # Run the commands in OEDA
        success, outfile = self.__oeda.processCmds()
        if not success:
            # Go ahead with generating the files but treat it as failure
            self.setLastError('OEDACLI_LOG_CONTAINS_ERRORS')
        self.util.logFileContent('oeda command output', outfile)
        outXmlPath = self.__oeda.getOutXmlPath()
        self.util.logFileContent('oeda generated client XML', outXmlPath)
        # Alter VM Sizes by manipulating raw XML. OEDA doesn't support altering
        # this yet.
        rxp = self.getXmlProcessor(outXmlPath)
        self.alterXmlVmSizes(rxp, clientDict)
        rxp.writeXml(outXmlPath)
        self.util.logFileContent('Raw XML Processor generated Client XML',
                                 outXmlPath)

        return outXmlPath, self.__get_special_fields(clientDict)


class ebBMCControl(object):
    """
    Processor of the Bare Metal commands
    Processes operations ['compose_cluster'], more TBD
    """
    LOG_DIRECTORY = 'log/bmcctrl/'

    def __init__(self, aCtx, aJob):
        self.__ctx = aCtx
        self.__job = aJob
        self.__options = self.__job.mGetOptions()
        self.__node = None
        if 'hostname' in self.__options:
            self.__hostname = self.__options.hostname
            self.__node = exaBoxNode(get_gcontext(), aLocal=True)
            self.__node.mConnect(aHost=self.__options.hostname)
        self.__req_log_dir = os.path.join('bmcctrl', self.__job.mGetUUID())
        self.__req_log = os.path.join(self.__req_log_dir, 'bmcctrl.log')
        self.__outDir = os.path.join(self.LOG_DIRECTORY,
                                     self.__job.mGetUUID())
        # Set the bmcctrl.log handler
        ebLogSetBMCLogHandler(self.__req_log, 'DEBUG')
        self.logger = ebLogGetBMCLogger()
        self.util = BmcUtil(self.logger)

    def mGetRequestObj(self):
        return self.__job

    def setJobOutput(self, xmlfn, data):
        # Update the req with xml
        if xmlfn:
            with open(xmlfn) as f:
                self.__job.mSetXml(b64encode(f.read().encode('utf8')).decode('utf8'))
        # Update the req data field
        if data:
            self.__job.mSetData(json.dumps(data))


    def composeCluster(self, aOption):
        try:
            input_json = aOption.jsonconf
            configCreator = ebCluConfigCreator(input_json)
            configCreator.validate()
            configCreator.setOutputDir(self.__outDir)
            _xml, _pick_dict = configCreator.process_files()
            self.setJobOutput(_xml, _pick_dict)
        except Exception as e:
            logError("%s failed [%s]" % ('composeCluster', str(e),))
            logError(f'Traceback: {traceback.format_exc()}')
            ebLogInfo("Check log at: %s" % ('log/' + self.__req_log))
            _rc, _ = configCreator.getLastError()
            if int(_rc) == 0:
                # configCreator has no clue of the issue, most likely coding
                # error
                configCreator.setLastError('EXCEPTION')
        _rc, _ = configCreator.getLastError()
        return int(_rc)

    def addCustomerInfo(self, aOption):
        try:
            _input_json = aOption.jsonconf
            _input_xml = b64decode(aOption.xmlconfig).decode('utf8')
            configCreator = ebCluConfigCreator(_input_json)
            configCreator.validate()
            configCreator.setOutputDir(self.__outDir)
            _xml, _pick_dict = configCreator.addClientInfo(_input_xml, _input_json)
            logInfo('_pick_dict: %s' % (pprint.pformat(_pick_dict, indent=4)))
            self.setJobOutput(_xml, _pick_dict)
        except Exception as e:
            logError("%s failed [%s]" % ('addCustomerInfo', str(e),))
            logError(f'Traceback: {traceback.format_exc()}')
            ebLogInfo("Check log at: %s" % ('log/'+self.__req_log))
            _rc, _ = configCreator.getLastError()
            if int(_rc) == 0:
                # configCreator has no clue of the issue, most likely coding
                # error
                configCreator.setLastError('EXCEPTION')
        _rc, _ = configCreator.getLastError()
        return int(_rc)

    def executeCmd(self, cmd, aOption):
        """ Executes the requested operation
        """
        _rc = (-1 << 16) | 0x0000
        ebLogInfo("Writing BMC log at log/%s" % (self.__req_log,))

        if cmd == 'compose_cluster':
            retVal = self.composeCluster(aOption)
        elif cmd == 'add_customer_info':
            retVal = self.addCustomerInfo(aOption)
        else:
            retVal = int(gBMCError['INVALID_CMD'][0])

        # Update db
        _db = ebGetDefaultDB()
        _db.mUpdateRequest(self.__job)
        _success = retVal == 0
        ebLogInfo("%s %s" % (cmd, 'succeeded' if _success else 'failed'))
        return retVal and _rc | retVal



#Bug 29268921, recents OEDACLI does not generate a valid v1 XML
# If template contains vmSizeName in Machine section of domU, it is a v1
class V1OedaXMLRebuilder(object):
    def __init__(self):
        self.__v1_domUwithVmSizesTags = None

    def SavePropertiesFromTemplate(self,templateXmlFullPath):
        _etxml = XMLProcessor(templateXmlFullPath)
        # Find machines of type DomU with tag vmSizeName and save tags into class
        self.__v1_domUwithVmSizesTags = _etxml.findall("./machines/machine/[osType='LinuxGuest']/[vmSizeName]")

    def ProcessOedaCliXML(self, outputXMLPath):
        _post_modified = False
        # If template is V1, check output for VmSizesTag and reinject them
        if self.__v1_domUwithVmSizesTags:

            _outxml_filename = outputXMLPath
            _outxml = XMLProcessor(_outxml_filename) 
            _num_domu_with_vmsize = len(_outxml.findall("./machines/machine/[osType='LinuxGuest']/[vmSizeName]"))
            # If any vmSizeName tags were removed from machines section, add them back
            if not _num_domu_with_vmsize == len(self.__v1_domUwithVmSizesTags):

                #Get All IDs of previous VMs with vmSizeTags
                _v1_domu_ids = {x.attrib['id']:x for x in self.__v1_domUwithVmSizesTags}
                #Add template vmNameSize to output XML on matching vm ids
                for _domu_id in _v1_domu_ids.keys():
                    _outdomu = _outxml.find('./machines/machine/[@id="{}"]/[osType="LinuxGuest"]'.format(_domu_id))
                    if (_outdomu is not None) and (_outdomu.find('./vmSizeName') is None):
                        if not _post_modified:
                            logWarn('Going to modify OEDACLI output XML to switch it back from v2 to v1 as template provided was v1')
                            logWarn('Writing a copy of original one with name: {}.oeda'.format(_outxml_filename))
                            shutil.copy(_outxml_filename,_outxml_filename+'.oeda')
                            _post_modified = True
                        #Add SAME tag that was in the template with same ID
                        _outxml.insert_after_element('osType', _v1_domu_ids[_domu_id].find('./vmSizeName'),_outdomu)
                        #Template machine was v1, output was switched to v2, remove v2 artifacts
                        _outxml.remove_element('guestCores',_outdomu)
                        _outxml.remove_element('guestMemory',_outdomu)
                        _outxml.remove_element('guestLocalDiskSize',_outdomu)
            if _post_modified:  
                _outxml.writeXml(_outxml_filename)
