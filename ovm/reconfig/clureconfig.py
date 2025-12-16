#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/ovm/reconfig/clureconfig.py /main/16 2021/10/11 15:00:24 ffrrodri Exp $
#
# clureconfig.py
#
# Copyright (c) 2020, 2021, Oracle and/or its affiliates. 
#
#    NAME
#      clureconfig.py - Reconfig Wrapper
#
#    DESCRIPTION
#      clureconfig methods 
#
#    NOTES
#      NONE
#
#    MODIFIED   (MM/DD/YY)
#    ffrrodri    07/13/21 - Bug 33111535: Remove functionality to update agent
#                           certs
#    ffrrodri    06/11/21 - Enh 32988103: Added method to validate admin agent
#                           certinstallation module
#    ffrrodri    02/03/21 - Enh 32460437: Implement arping check to catch wrong
#                           VLAN/VNIC
#    jesandov    05/18/20 - Creation
#

import re
import time

from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure
from exabox.ovm.vmcontrol import exaBoxOVMCtrl, ebVgLifeCycle
from exabox.ovm.atp import AtpCreateAtpIni, AtpSetupNamespace
from exabox.ovm.clunetworkvalidations import NetworkValidations


class ebCluReconfig:

    ###############
    # Constructor #
    ###############

    def __init__(self, aClubox, aBackupTool):

        self.__clubox = aClubox
        self.__backupTool = aBackupTool

        self.__reconfigWorkdir = "/opt/exacloud/reconfig/{0}".format(self.mGetClubox().mGetKey())

        self.__stepRecord = {}

        self.__waitSteps = {

            self.mExecuteReconfigDom0: [
                self.mReconfigDom0ChangeVifVlan,
                self.mReconfigDom0UpdateNetwork
            ],
            self.mExecuteReconfigDomU: [
                self.mReconfigDomUChangeEtc,
                self.mReconfigDomUNetworkInfo,
                self.mReconfigDomUNetworkAtp,
                self.mReconfigDomURestartVM
            ],
            self.mExecuteReconfigGI: [
                self.mReconfigGiExecuteCommand
            ],
            self.mExecuteReconfigChecks: [
                self.mReconfigArpingCheck
            ],
            self.mExecuteReconfigCleanUp: [
                self.mReconfigCleanUp
            ]
        }

        self.__rollbackSteps = {
            self.mRollbackExecute: [
                self.mRollbackDomU
            ],
            self.mExecuteReconfigCleanUp: [
                self.mReconfigCleanUp
            ]
        }

        _dom0s, _, _, _ = self.mGetClubox().mReturnAllClusterHosts()
        self.mSetWatcherHostname(_dom0s[0])

    ###################
    # Getters/Setters #
    ###################

    def mGetClubox(self):
        return self.__clubox

    def mSetClubox(self, aClubox):
        self.__clubox = aClubox

    def mGetStepRecord(self):
        return self.__stepRecord

    def mSetStepRecord(self, aStepRecord):
        self.__stepRecord = aStepRecord

    def mGetBackupTool(self):
        return self.__backupTool

    def mSetBackupTool(self, aBackupTool):
        self.__backupTool = aBackupTool

    def mGetWaitSteps(self):
        return self.__waitSteps

    def mSetWaitSteps(self, aSteps):
        self.__waitSteps = aSteps

    def mGetRollbackSteps(self):
        return self.__rollbackSteps

    def mSetRollbackSteps(self, aSteps):
        self.__rollbackSteps = aSteps

    def mGetReconfigWorkdir(self):
        return self.__reconfigWorkdir

    def mSetReconfigWorkdir(self, aWorkdir):
        self.__reconfigWorkdir = aWorkdir

    def mGetWatcherHostname(self):
        return self.__watcherHostname

    def mSetWatcherHostname(self, aHostname):
        self.__watcherHostname = aHostname


    ####################
    # Reconfig Methods #
    ####################

    def mExecuteReconfig(self, aStepRegex=".*"):
        """
        Execute reconfig steps Dom0n DomU and GI

        :raises: ValueError
        """

        # Create folders of workdir
        _nodeWatcher = exaBoxNode(get_gcontext())
        _nodeWatcher.mConnect(self.mGetWatcherHostname())

        try:
            _nodeWatcher.mExecuteCmd("/bin/mkdir -p {0}".format(self.mGetReconfigWorkdir()))
        finally:
            _nodeWatcher.mDisconnect()

        # Execute the steps
        for _step in self.mGetWaitSteps():
            if re.search(aStepRegex, _step.__name__):
                self.mExecuteStep(_step.__name__, _step)


    def mExecuteStep(self, aStepName, aFx):
        """
        Register the time execute by one operation

        :param:aStepName: Name of the step to record the activity
        :param:aStepType: The type of operation, only valid "start" and "end"
        :param:aStepType: The type of operation, only valid "start" and "end"

        :raises: ValueError
        """

        # Start Step
        _dict = {
            "start_time": time.time(),
            "end_time": None,
            "substeps": {}
        }

        self.mGetStepRecord()[aStepName] = _dict
        ebLogInfo("*** Starting Step: {0}".format(aStepName))

        # Execute Step
        aFx()

        # Finish Step
        _start_time = self.mGetStepRecord()[aStepName]['start_time']
        _end_time = time.time()
        _total_time = _end_time - _start_time

        self.mGetStepRecord()[aStepName]['end_time'] = _end_time
        self.mGetStepRecord()[aStepName]['total_time'] = _total_time

        ebLogInfo("*** Step {0} finnish in {1}".format(aStepName, _total_time))

    def mExecuteSubStep(self, aSubStepName, aHost, aFx, aFxArgs, aStepRecord):
        """
        Register the time execute by one suboperation

        :param:aSubStepName: The name of the substep
        :param:aStepType: The type of operation, only valid "start" and "end"
        :param:aHost: Host where the substep will be executed
        """

        # Start Step
        _stepKey = "{0}-{1}".format(aSubStepName, aHost)
        _dict = {
            "start_time": time.time(),
            "end_time": None,
            "hostname": aHost
        }

        ebLogInfo("*** Starting SubStep: {0} on {1}".format(aSubStepName, aHost))

        # Check if the operation was not done before
        _opsFile = "{0}/{1}".format(self.mGetReconfigWorkdir(), _stepKey)

        _nodeWatcher = exaBoxNode(get_gcontext())
        _nodeWatcher.mConnect(self.mGetWatcherHostname())

        try:

            _nodeWatcher.mExecuteCmd("/bin/ls -la {0}".format(_opsFile))

            if _nodeWatcher.mGetCmdExitStatus() != 0:

                # Operation file not found, execute the function
                aFx(*aFxArgs)

                # Register step of execution
                _nodeWatcher.mExecuteCmd("/bin/touch {0}".format(_opsFile))

            else:
                ebLogInfo("Operation already executed, found file: {0}".format(_opsFile))

        finally:
            _nodeWatcher.mDisconnect()

        # Finish Step
        _start_time = _dict['start_time']
        _end_time = time.time()
        _total_time = _end_time - _start_time

        _dict['end_time'] = _end_time
        _dict['total_time'] = _total_time

        aStepRecord[_stepKey] = _dict

        ebLogInfo("*** Ending SubStep {0} on {1} finnish in {2}".format(aSubStepName, aHost, _total_time))


    def mParallelWrapper(self, aFx, aStepName=None):
        """
        Validate the XML and execute the aFx in every Node detected in Payload

        :raises: ExacloudRuntimeError
        """

        #Fetch the differents computes
        _jconf = self.mGetClubox().mGetArgsOptions().jsonconf

        if _jconf is None or not 'preprov_network' in _jconf.keys():
            ebLogError('*** Invalid reconfig payload. Payload or preprov network missing')
            raise ExacloudRuntimeError(0x8001, 0xA, 'Invalid reconfig payload. Payload or preprov network missing')

        #Execute the Subprocesses
        _processes = ProcessManager()
        _stepExecuted = _processes.mGetManager().dict()

        for i in range(0, len(_jconf['customer_network']['nodes'])):

            _custNode = _jconf['customer_network']['nodes'][i]
            _prepNode = _jconf['preprov_network']['nodes'][i]

            _p = ProcessStructure(aFx, [_prepNode, _custNode, _stepExecuted], "{0}-{1}".format(aFx, i))
            _p.mSetMaxExecutionTime(60*60) # 60 minutes timeout
            _p.mSetJoinTimeout(10)
            _p.mSetLogTimeoutFx(ebLogWarn)
            _processes.mStartAppend(_p)

        _processes.mJoinProcess()

        if _processes.mGetStatus() == "killed":
            ebLogError('Timeout while executing VM services in {0}'.format(aFx))
            raise ExacloudRuntimeError(0x8002, 0xA, 'Timeout while executing {0}'.format(aFx), aStackTrace=False)

        for _process in _processes.mGetProcessList():
            if _process.exitcode != 0:
                _msg = "The process {0} exit with code: {1} in function: {2}".format(_process, _process.exitcode, aFx)
                ebLogError(_msg)
                raise ExacloudRuntimeError(0x8001, 0xA, _msg)

        # Update parallel step list
        if aStepName:
            self.mGetStepRecord()[aStepName]['substeps'] = dict(_stepExecuted)

    def mParsePayload(self, aPreprovJson, aCustomerJson):
        """
        Fetch the information of the payload with the tag preprov and customer tags

        :param:aPreprovJson: Preprov information on the reconfig payload
        :param:aCustomerJson: Customer information on the reconfig payload

        :return: tuple of elements
        :return:_dom0: The name of the Dom0 where the operations will be executed
        :return:_oldName: Old name of the vm to change on the reconfig
        :return:_newName: New name of the vm after the change of the reconfig
        :return:_oldNodeN: aCustomerJson tag after the node format
        :return:_newNodeN: aPreprovJson tag after the node format
        """

        _newNodeN = aCustomerJson
        _oldNodeN = aPreprovJson

        _dom0 = ""

        #Find the Dom0
        for _dom0Name, _ in self.mGetClubox().mReturnDom0DomUPair():
            if _dom0Name.find(_oldNodeN['client']['dom0_oracle_name']) != -1:
                _dom0 = _dom0Name
                break

        if _dom0 == "":
            ebLogInfo("No Dom0 Found: {0}".format(_oldNodeN['client']['dom0_oracle_name']))
            return False

        _oldName = "%s.%s" % (_oldNodeN['client']['hostname'], _oldNodeN['client']['domainname'])
        _newName = "%s.%s" % (_newNodeN['client']['hostname'], _newNodeN['client']['domainname'])

        ebLogInfo("Update Network configuration on Dom0: {0} for VM {1}".format(_dom0, _oldName))

        return _dom0, _oldName, _newName, _oldNodeN, _newNodeN

    ################
    # Dom0 Methods #
    ################

    def mExecuteReconfigDom0(self):
        """
        Validate the XML and execute the mReconfigDom0StepsExecute in every Node

        :raises: ExacloudRuntimeError
        """
        self.mParallelWrapper(self.mReconfigDom0StepsExecute, self.mExecuteReconfigDom0.__name__)

    def mReconfigDom0StepsExecute(self, aPreprovJsonNode, aCustomerJsonNode, aStepRecord):
        """
        Execute the Dom0 Steps in the parallel wrapper

        :param:aPreprovJsonNode: preprov json node
        :param:aCustomerJsonNode: customer json node
        """

        _dom0, _oldName, _newName, _oldJson, _newJson = self.mParsePayload(aPreprovJsonNode, aCustomerJsonNode)

        _dom0Node = exaBoxNode(get_gcontext())
        _dom0Node.mConnect(aHost=_dom0)

        for _step in self.mGetWaitSteps()[self.mExecuteReconfigDom0]:

            _args = [_dom0Node, _oldName, _newName, _oldJson, _newJson]
            self.mExecuteSubStep(_step.__name__, _dom0, _step, _args, aStepRecord)

        _dom0Node.mDisconnect()

    def mReconfigDom0ChangeVifVlan(self, aDom0Node, aOldName, aNewName, aOldJson, aNewJson):
        """
        Change the VIF and VLAN configuration on Dom0 level

        :param:aDom0Node: A live Dom0 where to run commands
        :param:aOldName: The old name of the vm
        :param:aNewname: The new name of the vm
        :param:aOldJson: The old information of the vm in json format
        :param:aNewJson: The new information of the vm in json format

        :raises: ExacloudRuntimeError
        """
        raise NotImplementedError

    def mConfigureVLAN(self, aDom0Node, aInterface, aVlanId, aNetType):
        """
        Configure the Dom0 VLAN configuration

        :param:aDom0Node: A Live Dom0 where to run commands
        :param:aInterface: The name of the interface to apply the VLAN
        :param:aVlanId: the number of the VLAN
        :param:aNetType: type of network (client/backup)
        """
        raise NotImplementedError

    def mReconfigDom0UpdateNetwork(self, aDom0Node, aOldName, aNewName, aOldJson, aNewJson):
        """
        Change the Dom0 Network configuration

        :param:aDom0Node: A live Dom0 where to run commands
        :param:aOldName: The old name of the vm
        :param:aNewname: The new name of the vm
        :param:aOldJson: The old information of the vm in json format
        :param:aNewJson: The new information of the vm in json format

        :raises: ExacloudRuntimeError
        """
        raise NotImplementedError

    def mReconfigDom0UpdateVmFolder(self, aDom0Node, aOldVmName, aNewVmName):
        """
        Change the VIF and VLAN configuration on Dom0 level

        :param:aDom0Node: A live Dom0 where to run commands
        :param:aOldName: The old name of the vm
        :param:aNewname: The new name of the vm
        :param:aOldJson: The old information of the vm in json format
        :param:aNewJson: The new information of the vm in json format

        :raises: ExacloudRuntimeError
        """
        raise NotImplementedError

    ################
    # DomU Methods #
    ################

    def mExecuteReconfigDomU(self):
        """
        Validate the XML and execute the mReconfigDom0StepsExecute in every Node

        :raises: ExacloudRuntimeError
        """

        self.mParallelWrapper(self.mReconfigDomUStepsExecute, self.mExecuteReconfigDomU.__name__)

    def mReconfigDomUStepsExecute(self, aPreprovJsonNode, aCustomerJsonNode, aStepRecord):
        """
        Execute the Dom0 Steps in the parallel wrapper

        :param:aPreprovJsonNode: preprov json node
        :param:aCustomerJsonNode: customer json node
        """

        _dom0, _oldName, _newName, _oldJson, _newJson = self.mParsePayload(aPreprovJsonNode, aCustomerJsonNode)
        _natName = "%s.%s" % (_newJson['client']['domu_oracle_name'], _dom0.split('.',1)[1])

        _localNode = exaBoxNode(get_gcontext(), aLocal=True)
        _domUNode = exaBoxNode(get_gcontext())

        try:

            _localNode.mConnect()

            # Check DomU SSH Port is alive
            if _localNode.mCheckPortSSH(_natName):

                _domUNode.mConnect(aHost=_natName)

                # Execute the callbacks of DomUs
                for _step in self.mGetWaitSteps()[self.mExecuteReconfigDomU]:

                    if _step != self.mReconfigDomURestartVM:

                        _args = [_domUNode, _oldName, _newName, _oldJson, _newJson]
                        self.mExecuteSubStep(_step.__name__, _natName, _step, _args, aStepRecord)

            else:
                ebLogInfo("DomU '{0}' SSH Port is down, Skip DomU Steps".format(_natName))

        finally:

            _localNode.mDisconnect()
            _domUNode.mDisconnect()

        # Execute the Vm Restart
        for _step in self.mGetWaitSteps()[self.mExecuteReconfigDomU]:

            if _step == self.mReconfigDomURestartVM:

                _args = [_dom0, _oldName, _newName, _natName]
                self.mExecuteSubStep(_step.__name__, _natName, _step, _args, aStepRecord)

    def mReconfigDomURestartVM(self, aDom0Name, aOldDomU, aNewDomU, aNatDomU):
        """
        Change the name of the vms during restart

        :param:aDom0: The name of the Dom0 where the vm is running
        :param: aOldDomU: The old name of the vm before reconfig to apply shutdown
        :param: aNewDomU: The new name of the vm after reconfig to apply start
        :param: aNatName: The nat name of the vm

        :raises:ExacloudRuntimeError
        """

        _dom0Node = exaBoxNode(get_gcontext())
        _dom0Node.mConnect(aHost=aDom0Name)

        #Shutdown the VM
        ebLogInfo("Start Shutdown of {0} on {1}".format(aOldDomU, aDom0Name))
        _vmhandle = ebVgLifeCycle()
        _vmhandle.mSetOVMCtrl(aCtx=get_gcontext(), aNode=_dom0Node)
        _vmhandle.mSetDestroyOnStart(True)

        _domUs = _vmhandle.mGetVmCtrl().mGetDomUs()

        if aOldDomU in _domUs:

            _shutdownRc = _vmhandle.mDispatchEvent("shutdown", aOptions=None, aVMId=aOldDomU)

            if _shutdownRc != 0:
                ebLogError("Failing to Shutdown VM '{0}' in Preprovisioning: {1}".format(aOldDomU, _shutdownRc))
                raise ExacloudRuntimeError(0x8002, 0xA, 'Fail while execute the commands of DomU part')
            else:
                ebLogInfo("Shutdown Sucessfull of {0} on {1}".format(aOldDomU, aDom0Name))

        else:
            ebLogInfo("VM '{0}' already shutdown in '{1}'".format(aOldDomU, aDom0Name))

        # Refresh domU config
        _vmhandle.mGetVmCtrl().mRefreshDomUs()
        _domUs = _vmhandle.mGetVmCtrl().mGetDomUs()

        if aNewDomU not in _domUs:
        
            #Restore the new VM
            ebLogInfo("Start Rename of VM '{0}' to '{1}' in Preprovisioning: {2}".format(aOldDomU, aNewDomU, aDom0Name))
            self.mReconfigDom0UpdateVmFolder(_dom0Node, aOldDomU, aNewDomU)

            ebLogInfo("Start Re-start of VM '{0}' to '{1}' in Preprovisioning: {2}".format(aOldDomU, aNewDomU, aDom0Name))
            self.mGetClubox().mRestartVM(aNewDomU, aVMHandle=_vmhandle, aNatName=aNatDomU)

        else:
            ebLogInfo("VM '{0}' already started in '{1}'".format(aNewDomU, aDom0Name))

        _dom0Node.mDisconnect()

    def mCalculateNetwork(self, aJsonObject, aSubtag='client'):
        """
        Calculate the network information of one subtag

        :param:aJsonObject:a Json Object with ip, netmask and gateway tags
        :param:aSubtag:The name of the subtag of the json where to fetch
        :return: a dict with the network information
        :rtype: dict
        """

        _ip = aJsonObject[aSubtag]['ip']
        _mask = aJsonObject[aSubtag]['netmask']
        _gateway = aJsonObject[aSubtag]['gateway']

        _ipOctets = _ip.split('.')
        _maskOctets = _mask.split('.')

        _network = str( int( _ipOctets[0] ) & int(_maskOctets[0] ) ) + '.'
        _network += str( int( _ipOctets[1] ) & int(_maskOctets[1] ) ) + '.'
        _network += str( int( _ipOctets[2] ) & int(_maskOctets[2] ) ) + '.'
        _network += str( int( _ipOctets[3] ) & int(_maskOctets[3] ) )

        _broadcast = str( int( _ipOctets[0] ) | int(~(int(_maskOctets[0])) & 0xff) ) + '.'
        _broadcast += str( int( _ipOctets[1] ) | int(~(int(_maskOctets[1])) & 0xff) ) + '.'
        _broadcast += str( int( _ipOctets[2] ) | int(~(int(_maskOctets[2])) & 0xff) ) + '.'
        _broadcast += str( int( _ipOctets[3] ) | int(~(int(_maskOctets[3])) & 0xff) )

        _netInfo = {}
        _netInfo['ip'] = _ip
        _netInfo['netmask'] = _mask
        _netInfo['network'] = _network
        _netInfo['broadcast'] = _broadcast
        _netInfo['gateway'] = _gateway
        _netInfo['cidr'] = str(sum(bin(int(x)).count('1') for x in _mask.split('.')))

        return _netInfo

    def mReconfigDomUChangeEtc(self, aDomUNode, aOldVmName, aNewVmName, aOldJson, aNewJson):
        """
        Change the etc files of the DomU

        :param:aDomUNode: A live DomU where to run commands
        :param:aOldName: The old name of the vm
        :param:aNewname: The new name of the vm
        :param:aOldJson: The old information of the vm in json format
        :param:aNewJson: The new information of the vm in json format

        :raises: ExacloudRuntimeError
        """

        # update udev rules
        ebLogInfo('*** Updating udev rules')
        _udevfile = '/etc/udev/rules.d/70-persistent-net.rules'

        _cmd = "/bin/sed --follow-symlinks -i s/{0}/{1}/gi {2}".format(aOldJson["client"]["mac"], aNewJson['client']['mac'].lower(), _udevfile)
        aDomUNode.mExecuteCmdLog(_cmd)

        _cmd = "/bin/sed --follow-symlinks -i s/{0}/{1}/gi {2}".format(aOldJson["backup"]["mac"], aNewJson['backup']['mac'].lower(), _udevfile)
        aDomUNode.mExecuteCmdLog(_cmd)

        # Update /etc/hosts
        ebLogInfo('*** Updating /etc/hosts')
        _entry = "{0} {1}.{2} {1}".format(aNewJson['client']['ip'], aNewJson['client']['hostname'], aNewJson['client']['domainname'])

        _cmd = '/bin/sed --follow-symlinks -i "s/^{0}.*/{1}/g" {2}'.format(aOldJson['client']['ip'], _entry, '/etc/hosts')
        aDomUNode.mExecuteCmdLog(_cmd)

        # Update domain, resolve and hostname
        ebLogInfo('*** Updating domain in /etc/resolv.conf and /etc/hostname')

        _cmd = "/bin/sed --follow-symlinks -i s/{0}/{1}/g {2}".format(aOldJson['client']['domainname'], aNewJson['client']['domainname'], '/etc/resolv.conf')
        aDomUNode.mExecuteCmdLog(_cmd)
        
        _cmd = "/bin/sed --follow-symlinks -i s/{0}/{1}/g {2}".format(aOldJson['client']['hostname'], aNewJson['client']['hostname'], '/etc/hostname')
        aDomUNode.mExecuteCmdLog(_cmd)

        # Update sshd_config file
        ebLogInfo("Update sshd_config file")
        _sshdconf = '/etc/ssh/sshd_config'

        _cmd = "/bin/sed --follow-symlinks -i s/{0}/{1}/g {2}".format(aOldJson['client']['ip'], aNewJson['client']['ip'], _sshdconf)
        aDomUNode.mExecuteCmdLog(_cmd)

        _cmd = "/bin/sed --follow-symlinks -i s/{0}/{1}/g {2}".format(aOldJson['backup']['ip'], aNewJson['backup']['ip'], _sshdconf)
        aDomUNode.mExecuteCmdLog(_cmd)


    def mReconfigDomUNetworkInfo(self, aDomUNode, aOldVmName, aNewVmName, aOldJson, aNewJson):
        """
        Change the network files of the DomU

        :param:aDomUNode: A live DomU where to run commands
        :param:aOldName: The old name of the vm
        :param:aNewname: The new name of the vm
        :param:aOldJson: The old information of the vm in json format
        :param:aNewJson: The new information of the vm in json format

        :raises: ExacloudRuntimeError
        """

        # Fetch network information
        _oldNetInfo = self.mCalculateNetwork(aOldJson, 'client')
        _newNetInfo = self.mCalculateNetwork(aNewJson, 'client')

        # Change sysconfig network
        ebLogInfo('*** Updating /etc/sysconfig/network')
        _cmd = "/bin/sed --follow-symlinks -i s/{0}/{1}/g {2}".format(_oldNetInfo['gateway'], \
                                                                      _newNetInfo['gateway'], \
                                                                      '/etc/sysconfig/network')
        aDomUNode.mExecuteCmdLog(_cmd)

        # Change rule-bondeth0
        ebLogInfo('*** Updating rule-bondeth0')
        _cmd = "/bin/sed --follow-symlinks -i s@{0}/{1}@{2}/{3}@g {4}".format(_oldNetInfo['network'], \
                                                                              _oldNetInfo['cidr'], \
                                                                              _newNetInfo['network'], \
                                                                              _newNetInfo['cidr'], \
                                                                              '/etc/sysconfig/network-scripts/rule-bondeth0')
        aDomUNode.mExecuteCmdLog(_cmd)

        # Change route-bondeth0
        ebLogInfo('*** Updating route-bondeth0')
        _routeBondEth0 = "/etc/sysconfig/network-scripts/route-bondeth0"

        _cmd = "/bin/sed --follow-symlinks -i s@{0}/{1}@{2}/{3}@g {4}".format(_oldNetInfo['network'], \
                                                                              _oldNetInfo['cidr'], \
                                                                              _newNetInfo['network'], \
                                                                              _newNetInfo['cidr'], \
                                                                              _routeBondEth0)
        aDomUNode.mExecuteCmdLog(_cmd)

        _cmd = "/bin/sed --follow-symlinks -i s/{0}/{1}/g {2}".format(_oldNetInfo['gateway'], _newNetInfo['gateway'], _routeBondEth0)
        aDomUNode.mExecuteCmdLog(_cmd)

        # change ifcfg-bondeth0
        ebLogInfo('*** Updating ifcfg-bondeth0')
        _ifcfgBondEth0 = "/etc/sysconfig/network-scripts/ifcfg-bondeth0"

        _cmd = '/bin/sed --follow-symlinks -i "s/^IPADDR.*/IPADDR={0}/" {1}'.format(_newNetInfo['ip'], _ifcfgBondEth0)
        aDomUNode.mExecuteCmdLog(_cmd)

        _cmd = '/bin/sed --follow-symlinks -i "s/^NETMASK.*/NETMASK={0}/" {1}'.format(_newNetInfo['netmask'], _ifcfgBondEth0)
        aDomUNode.mExecuteCmdLog(_cmd)

        _cmd = '/bin/sed --follow-symlinks -i "s/^GATEWAY.*/GATEWAY={0}/" {1}'.format(_newNetInfo['gateway'], _ifcfgBondEth0)
        aDomUNode.mExecuteCmdLog(_cmd)

        _cmd = '/bin/sed --follow-symlinks -i "s/^NETWORK.*/NETWORK={0}/" {1}'.format(_newNetInfo['network'], _ifcfgBondEth0)
        aDomUNode.mExecuteCmdLog(_cmd)

        _cmd = '/bin/sed --follow-symlinks -i "s/^BROADCAST.*/BROADCAST={0}/" {1}'.format(_newNetInfo['broadcast'], _ifcfgBondEth0)
        aDomUNode.mExecuteCmdLog(_cmd)

    def mReconfigDomUNetworkAtp(self, aDomUNode, aOldVmName, aNewVmName, aOldJson, aNewJson):
        """
        Apply Network change of ATP

        :param:aDomUNode: A live DomU where to run commands
        :param:aOldName: The old name of the vm
        :param:aNewname: The new name of the vm
        :param:aOldJson: The old information of the vm in json format
        :param:aNewJson: The new information of the vm in json format

        :raises: ExacloudRuntimeError
        """

        if self.mGetClubox().isATP() and \
           self.mGetClubox().mIsExabm() and \
           self.mGetClubox().mCheckClusterNetworkType():

            # Executing the ATP reconfig
            ebLogInfo("Executing AtpCreateAtpIni")

            AtpCreateAtpIni(aDomUNode, \
                              self.mGetClubox().mGetATP(), \
                              self.mGetClubox().mGetOptions().jsonconf["customer_network"], \
                              aNewVmName
                            ).mExecute()

        else:
            ebLogInfo("Skip AtpCreateAtpIni")

        # Check namespaces
        _atpConfig = self.mGetClubox().mCheckConfigOption('atp')

        if self.mGetClubox().isATP() and \
           _atpConfig is not None and \
           'enable_namespace' in _atpConfig and \
           _atpConfig['enable_namespace'] == 'True':

                # Executing the ATP reconfig
                ebLogInfo("Executing mSetupNamespace")
                AtpSetupNamespace(aDomUNode, \
                                    self.mGetClubox().mGetATP(), \
                                    self.mGetClubox().mGetOptions().jsonconf["customer_network"], \
                                    aNewVmName
                                 ).mExecute()
        else:
            ebLogInfo("Skip mSetupNamespace")

    ##############
    # GI Methods #
    ##############

    def mExecuteReconfigGI(self):
        """
        Validate the XML and execute the reconfig gi callbacks

        :raises: ExacloudRuntimeError
        """

        #Fetch the differents computes
        _jconf = self.mGetClubox().mGetArgsOptions().jsonconf

        if _jconf is None or not 'preprov_network' in _jconf.keys():
            ebLogError('*** Invalid reconfig payload. Payload or preprov network missing')
            raise ExacloudRuntimeError(0x8001, 0xA, 'Invalid reconfig payload. Payload or preprov network missing')

        _stepDict = {}

        for _step in self.mGetWaitSteps()[self.mExecuteReconfigGI]:

            _args = [_jconf['customer_network'], _jconf['preprov_network']]
            self.mExecuteSubStep(_step.__name__, None, _step, _args, _stepDict)

        self.mGetStepRecord()[self.mExecuteReconfigGI.__name__]['steps'] = _stepDict


    def mInternalNodeExecute(self, aNode, aCmd, aSleep=0, aTimeout=0, aCount=3, aSoftFail=False):
        """
        Execute aCmd in the live aNode

        :param:aNode: A live node where to run the commands
        :param:aCmd: The cmd to execute
        :param:aSleep: The sleep time to sleep between retries of the command
        :param:aTimeout: The maximum time of the command execution
        :param:aCount: The count of permited retries of the commands
        :param:aSoftFail: if true, raise a exception if the command fails

        :raises: ExacloudRuntimeError

        :return: return code of the command
        :rtype: int
        """

        _count = aCount
        _startTime = time.time()
        _timeout   = aTimeout
        _currtime  = _startTime
        _internalTime = time.time()
        _run = True

        while _run:

            _internalTime = time.time()

            ebLogInfo("Executing the command: '{0}'".format(aCmd))
            aNode.mExecuteCmdLog(aCmd)
            _rc = aNode.mGetCmdExitStatus()

            if _rc != 0:
                ebLogError("Command execution fail, Return Code: '{0}'".format(_rc))
                _count -= 1
            else:
                _count = aCount
                ebLogInfo("Command execution success")
                ebLogInfo("Local Execution Time: {0}, Total Time: {1}, Counts: {2}".format(time.time() - _internalTime, 
                                                                                           time.time() - _startTime, 
                                                                                           abs(_count-aCount)))
                break

            if aSleep != 0:
                time.sleep(aSleep)

            #Update Conditions
            _currtime  = time.time()
            if aTimeout != 0:
                if _currtime - _startTime >= _timeout:
                    _run = False
            else:
                if _count < 0:
                    _run = False

        if _count <= 0:
            if aSoftFail:
                ebLogError("SoftFailure: GI command execution failed: {0}".format(aCmd))
            else:
                ebLogError("Local Execution Time: {0}, Total Time: {1}, Counts: {2}".format(time.time() - _internalTime, 
                                                                                            time.time() - _startTime, 
                                                                                            abs(_count-aCount)))

        return 0

    def mReconfigGiExecuteCommand(self, aCustomerJson, aPreprovJson):
        """
        Execute GI command to change Grid Infrastructure

        :param:aCustomerJson: The customer json information from the payload
        :param:aPreprovJson: The preprov json information from the payload

        :raises: ExacloudRuntimeError
        """

        _customerJsonNodes = aCustomerJson['nodes']
        _preprovJsonNodes = aPreprovJson['nodes']

        # Create the node only of the first node
        _domUList = [ _domu for _ , _domu in self.mGetClubox().mReturnDom0DomUPair()]
        _lenDomUs = len(_domUList)

        _newNetInfo = self.mCalculateNetwork(_customerJsonNodes[0], 'client')

        _preprovShortHosts = []
        for _preprovNode in _preprovJsonNodes:
            _preprovShortHosts.append(_preprovNode['client']['hostname'])

        _vipCustList = []
        for _custNode in _customerJsonNodes:
            _vipCustList.append(_custNode['vip']['hostname'])

        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_domUList[0])

        # Fetch ORATAB Entry
        _cmd = "/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'"
        _i, _o, _e = _node.mExecuteCmd(_cmd)
        _out = _o.readlines()
        if not _out or len(_out) == 0:
            ebLogWarn('*** ORATAB entry not found for grid')
            return

        # Calculate relative paths
        _gridPath = _out[0].strip()
        _crsCmdPfx = _gridPath + '/bin/crsctl '
        _srvCmdPfx = _gridPath + '/bin/srvctl '
        _oifCmdPfx = _gridPath + '/bin/oifcfg '

        # Scale the MAX timeout with cluster size
        _initialTimeout = self.mGetClubox().mCheckConfigOption('reconfig_gistart_timeout')
        if _initialTimeout is None:
            _initialTimeout = 600
        else:
            _initialTimeout = int(_initialTimeout)
            _initialTimeout = _initialTimeout * (_lenDomUs/2)

        # Execute the commands
        _cmd = _crsCmdPfx + 'check cluster -all | grep -c online | grep -w {0}'.format(3*_lenDomUs)
        self.mInternalNodeExecute(_node, _cmd, aSleep=10, aTimeout=_initialTimeout, aSoftFail=True)

        _cmd = _crsCmdPfx + 'stop res ora.net1.network -f -unsupported'
        self.mInternalNodeExecute(_node, _cmd, aSoftFail=True)

        _cmd = _srvCmdPfx + 'config nodeapps -a'
        self.mInternalNodeExecute(_node, _cmd, aSoftFail=True)

        _cmd = _srvCmdPfx + 'modify network -k 1 -S %s/%s/bondeth0 -pingtarget %s' %(_newNetInfo['network'], \
                                                                                     _newNetInfo['netmask'], \
                                                                                     _newNetInfo['gateway'])
        self.mInternalNodeExecute(_node, _cmd)

        #self.mInternalNodeExecute(_node, _oifCmdPfx + 'delif -global bondeth0')
        #self.mInternalNodeExecute(_node, _oifCmdPfx + 'setif -global bondeth0/%s:public' % (_cust_net))

        _cmd = _crsCmdPfx + 'stop cluster -all'
        self.mInternalNodeExecute(_node, _cmd, aSoftFail=True)

        _cmd = _crsCmdPfx + 'check cluster -all | grep -c online | grep -w "0"'
        self.mInternalNodeExecute(_node, _cmd, aSleep=10, aTimeout=300, aSoftFail=True)

        _cmd = _crsCmdPfx + 'start cluster -all'
        self.mInternalNodeExecute(_node, _cmd, aSoftFail=True)

        _cmd = _crsCmdPfx + 'check cluster -all | grep -c online | grep -w {0}'.format(3*_lenDomUs)
        self.mInternalNodeExecute(_node, _cmd, aSleep=10, aTimeout=_initialTimeout)

        _cmd = _srvCmdPfx + 'stop listener'
        self.mInternalNodeExecute(_node, _cmd, aSoftFail=True)

        # DomU preprov hostname is the VIP resource name
        for _vipResourceName in _preprovShortHosts:
            self.mInternalNodeExecute(_node, _srvCmdPfx + 'stop vip -i %s -v -force' %(_vipResourceName), aSoftFail=True)

        _cmd = _srvCmdPfx + "remove vip -vip '%s' -force" %(','.join(_preprovShortHosts))
        self.mInternalNodeExecute(_node, _cmd)

        for i in range(_lenDomUs):
            _netmask = _customerJsonNodes[0]['client']['netmask']
            _cmd = _srvCmdPfx + 'add vip -n %s -A %s/%s -k 1' %(_preprovShortHosts[i], _vipCustList[i], _netmask)
            self.mInternalNodeExecute(_node, _cmd)

            _cmd = _srvCmdPfx + 'start vip -i %s' %(_preprovShortHosts[i])
            self.mInternalNodeExecute(_node, _cmd)

        self.mInternalNodeExecute(_node, _srvCmdPfx + 'stop scan_listener', aSoftFail=True)
        self.mInternalNodeExecute(_node, _srvCmdPfx + 'stop scan', aSoftFail=True)
        self.mInternalNodeExecute(_node, _srvCmdPfx + 'modify scan -n %s' % (aCustomerJson['scan']['hostname']))
        self.mInternalNodeExecute(_node, _srvCmdPfx + 'modify scan_listener -u')
        self.mInternalNodeExecute(_node, _srvCmdPfx + 'config scan_listener')
        self.mInternalNodeExecute(_node, _srvCmdPfx + 'start scan')
        self.mInternalNodeExecute(_node, _srvCmdPfx + 'start scan_listener')
        self.mInternalNodeExecute(_node, _srvCmdPfx + 'status scan')
        self.mInternalNodeExecute(_node, _srvCmdPfx + 'config scan')
        self.mInternalNodeExecute(_node, _srvCmdPfx + 'status scan_listener')
        self.mInternalNodeExecute(_node, _srvCmdPfx + 'status listener')
        self.mInternalNodeExecute(_node, _srvCmdPfx + 'start listener', aSoftFail=True)

        _node.mDisconnect()

        # Execute additinal GI Command
        self.mGetClubox().mApplyExtraSrvctlConfig()


    ###################
    # Cleanup methods #
    ###################

    def mExecuteReconfigCleanUp(self):
        """
        Exacloud substep to clean the enviroment after the execution of the command
        """

        _stepDict = {}

        for _step in self.mGetWaitSteps()[self.mExecuteReconfigCleanUp]:

            _args = [self.mGetClubox().mGetKey()]
            self.mExecuteSubStep(_step.__name__, None, _step, _args, _stepDict)

        self.mGetStepRecord()[self.mExecuteReconfigCleanUp.__name__]['steps'] = _stepDict


    def mReconfigCleanUp(self, aExacloudKey):
        """
        Clean up the enviroment of the reconfig execution

        :param:aExacloudKey: Unique key of the name of the cluster given by Exacloud
        """

        ebLogInfo("Removing {0}".format(self.mGetReconfigWorkdir()))

        _nodeWatcher = exaBoxNode(get_gcontext())
        _nodeWatcher.mConnect(self.mGetWatcherHostname())

        try:
            _nodeWatcher.mExecuteCmd("/bin/rm -rf {0}".format(self.mGetReconfigWorkdir()))
        finally:
            _nodeWatcher.mDisconnect()

        self.mReconfigCleanUpEnv()


    def mReconfigCleanUpEnv(self):
        """
        Clean up the environment of the reconfig execution
        """
        raise NotImplementedError


    ####################
    # Rollback methods #
    ####################

    def mExecuteRollback(self):
        """
        Validate the XML and execute mRollbackStepsExecute in every Node

        :raises: ExacloudRuntimeError
        """

        # Execute the steps
        for _step in self.mGetRollbackSteps():
            self.mExecuteStep(_step.__name__, _step)

    def mRollbackExecute(self):
        """
        Main entry function to execute rollback steps in parallel wrapper

        :raises: ExacloudRuntimeError
        """

        self.mParallelWrapper(self.mRollbackStepsExecute, self.mRollbackExecute.__name__)

    def mRollbackStepsExecute(self, aPreprovJsonNode, aCustomerJsonNode, aStepRecord):
        """
        Execute the Rollback Steps in the parallel wrapper

        :param:aPreprovJsonNode: preprov json node
        :param:aCustomerJsonNode: customer json node
        """

        _dom0, _oldName, _newName, _oldJson, _newJson = self.mParsePayload(aPreprovJsonNode, aCustomerJsonNode)

        _dom0Node = exaBoxNode(get_gcontext())
        _dom0Node.mConnect(aHost=_dom0)

        for _step in self.mGetRollbackSteps()[self.mRollbackExecute]:

            _args = [_dom0Node, _oldName, _newName, _oldJson, _newJson]
            self.mExecuteSubStep(_step.__name__, _dom0, _step, _args, aStepRecord)

        _dom0Node.mDisconnect()

    def mRollbackDomU(self, aDom0Node, aOldName, aNewName, aOldJson, aNewJson):
        """
        Execute the rollback of the DomU

        :param:aDom0Node: A live Dom0 where to run commands
        :param:aOldName: The old name of the vm
        :param:aNewname: The new name of the vm
        :param:aOldJson: The old information of the vm in json format
        :param:aNewJson: The new information of the vm in json format

        :raises: ExacloudRuntimeError
        """

        _backupTool = self.mGetBackupTool()

        #Check the location
        if _backupTool.mFetchBackup(aDom0Node.mGetHostname(), aOldName) is None:
            ebLogInfo("Could not find a backup for: {0} in {1}".format(aOldName, aDom0Node.mGetHostname()))
            return

        #clean the new envorinment
        ebLogInfo("Shutdown VMs")

        _vmhandle = ebVgLifeCycle()
        _vmhandle.mSetOVMCtrl(aCtx=get_gcontext(), aNode=aDom0Node)

        if aOldName in _vmhandle.mGetVmCtrl().mGetDomUs() and \
           aOldName in _vmhandle.mGetVmCtrl().mGetDomUsCfg():
            _vmhandle.mDispatchEvent("shutdown", aOptions=None, aVMId=aOldName)

        if aNewName in _vmhandle.mGetVmCtrl().mGetDomUs() and \
           aNewName in _vmhandle.mGetVmCtrl().mGetDomUsCfg():
            _vmhandle.mDispatchEvent("shutdown", aOptions=None, aVMId=aNewName)

        #Execute the restore of the symbolic links
        self.mRollbackUpdateVmFolder(aDom0Node, aNewName, aOldName)

        #Clean the folder of the VM
        ebLogInfo("Clean the Enviroment of VMs")
        _cmd = "/bin/rm -rf {0}/{1}".format(_backupTool.mGetVmsFolder(), aNewName)
        aDom0Node.mExecuteCmd(_cmd)

        _cmd = "/bin/rm -rf {0}/{1}".format(_backupTool.mGetVmsFolder(), aOldName)
        aDom0Node.mExecuteCmd(_cmd)

        #Execute restore
        ebLogInfo("Execute VM Restore: {0}".format(aOldName))
        _backupTool.mRestoreBackup(aDom0Node.mGetHostname(), aOldName)

        #Restart the VM
        _natVm = aOldName
        _ctx = get_gcontext()
        if _ctx.mCheckRegEntry('_natHN_' + aOldName):
            _natVm = _ctx.mGetRegEntry('_natHN_' + aOldName)

        if _ctx.mCheckRegEntry('_natHN_' + aNewName):
            _natVm = _ctx.mGetRegEntry('_natHN_' + aNewName)

        ebLogInfo("Restart the VM: {0}".format(_natVm))
        self.mGetClubox().mRestartVM(aOldName, aVMHandle=_vmhandle, aNatName=_natVm)

    def mRollbackUpdateVmFolder(self, aDom0Node, aNewVmName, aOldVmName):
        """
        Function that will execute additional checks to be done in the subclass when rollback invoke

        :param:aDom0Node: A live Dom0 where to run commands
        :param:aNewVmName: The new name of the vm
        :param:aOldVmName: The old name of the vm
        :raises: ExacloudRuntimeError
        """

        raise NotImplementedError

    ########################
    # Arping Check methods #
    ########################

    def mExecuteReconfigChecks(self):
        """
        Executes Arping check method

        :raises: TypeError, ExacloudRuntimeError
        """

        self.mParallelWrapper(self.mReconfigCheckStepsExecute, self.mExecuteReconfigChecks.__name__)

    def mReconfigCheckStepsExecute(self, aPreprovJsonNode, aCustomerJsonNode, aStepRecord):
        """
            Execute the Arping check Steps in the parallel wrapper

            :param:aPreprovJsonNode: preprov json node
            :param:aCustomerJsonNode: customer json node

            :raises: TypeError, ExacloudRuntimeError
        """

        _dom0, _oldName, _newName, _oldJson, _newJson = self.mParsePayload(aPreprovJsonNode, aCustomerJsonNode)
        _natName = f"{_newJson['client']['domu_oracle_name']}.{_dom0.split('.', 1)[1]}"

        # Execute the callbacks of DomUs
        _domUNode = exaBoxNode(get_gcontext())

        try:
            _domUNode.mConnect(aHost=_natName)

            for _step in self.mGetWaitSteps()[self.mExecuteReconfigChecks]:
                _args = [_domUNode, _newJson]
                self.mExecuteSubStep(_step.__name__, _natName, _step, _args, aStepRecord)
        finally:
            _domUNode.mDisconnect()

    def mReconfigArpingCheck(self, aDomUNode, aNetworkJson):
        """
            Arping check of a Network from DomU

            :param:aDomUNode: A live DomU where to run commands
            :param:aNetworkJson: The new information of the vm in json format

            :raises: TypeError, ExacloudRuntimeError
        """

        _client_gateway = aNetworkJson["client"]["gateway"]
        _backup_gateway = aNetworkJson["backup"]["gateway"]

        _network_validation = NetworkValidations(aDomUNode)

        # Arping check for client net
        _network_validation.mArpingCheck('bondeth0', _client_gateway, None)

        # Verify if namespace RPM installed for backup net
        _nameSpace = None
        _cmd = '/bin/rpm --version'
        aDomUNode.mExecuteCmd(_cmd)
        if aDomUNode.mGetCmdExitStatus() == 0:
            _nameSpace = 'mgmt'

        # Arping check for backup net
        _network_validation.mArpingCheck('bondeth1', _backup_gateway, _nameSpace)


# end of file
