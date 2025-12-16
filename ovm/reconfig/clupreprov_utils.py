#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/ovm/reconfig/clupreprov_utils.py /main/5 2023/12/14 07:50:53 dekuckre Exp $
#
# clupreprovutils.py
#
# Copyright (c) 2020, 2023, Oracle and/or its affiliates. 
#
#    NAME
#      clupreprovutils.py - Preprovision Utilities
#
#    DESCRIPTION
#       Class with utilities used during the preprovision of exacloud
#
#    NOTES
#       NONE
#
#    MODIFIED   (MM/DD/YY)
#    dekuckre    12/08/23 - 36088226: select preprov VM based on customer node dom0.
#    naps        03/06/22 - remove virsh dependency layer.
#    jesandov    05/18/20 - Creation
#

from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogVerbose, ebLogJson

class ebPreprovUtils:
    """
    Class with utilities used during the preprovision of exacloud
    """

    ###############
    # Constructor #
    ###############

    def __init__(self, aClubox):
        self.__clubox = aClubox

    ###################
    # Getters/Setters #
    ###################

    def mGetClubox(self):
        """ getter """
        return self.__clubox

    def mSetClubox(self, aClubox):
        """ setter """
        self.__clubox = aClubox

    ###############################
    # Preprov detection functions #
    ###############################

    def mSetPreprovEnv(self):
        """
        Set one enviroment as preprov enviroment creating a file called
        /opt/exacloud/preprov on every DomU
        """
        for _, _domU in self.mGetClubox().mReturnDom0DomUPair():
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_domU)
            _node.mExecuteCmd('/bin/touch /opt/exacloud/preprov')
            _node.mDisconnect()

    def mCleanPreprovEnv(self):
        """
        Clean the enviroment as preprov enviroment deleting the file
        /opt/exacloud/preprov on every DomU
        """
        for _, _domU in self.mGetClubox().mReturnDom0DomUPair():
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_domU)
            _node.mExecuteCmd('/bin/rm /opt/exacloud/preprov')
            _node.mDisconnect()

    def mIsPreprovEnv(self):
        """
        Detect if one enviroment is a preprov enviroment cheching the file 
        /opt/exacloud/preprov on every DomU

        :return: enviroment state about reconfig
        :rtype: boolean
        """
        for _, _domU in self.mGetClubox().mReturnDom0DomUPair():
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_domU)
            if not _node.mFileExists('/opt/exacloud/preprov'):
                return False
            _node.mDisconnect()
        return True

    ################################
    # Clucontrol embebed functions #
    ################################

    def mUpdateVmNameReconfigDeleteService(self, aOptions):
        """
        Update the XML only in delete service to choose the correct name of the vm to delete
        """

        if self.mGetClubox().mGetCmd() not in ["vmgi_delete", "deleteservice"]:
            ebLogInfo("Skip mUpdateVmNameReconfigDeleteService since is not delete service")
            return

        if not self.mGetClubox().mIsExabm():
            ebLogInfo("Skip mUpdateVmNameReconfigDeleteService since is not exabm")
            return

        _jconf = aOptions.jsonconf

        if _jconf is not None and 'preprov_network' in _jconf:
            ebLogInfo('*** Patching VM Name on Reconfig Delete Service')

            for i in range(0, len(_jconf['customer_network']['nodes'])):

                #Get the variables of the name of the nodes
                _custNode = _jconf['customer_network']['nodes'][i]
                _prepNode = _jconf['preprov_network']['nodes'][i]
                _custNodeDom0 = _custNode['client']['dom0_oracle_name']

                for i in range(0, len(_jconf['preprov_network']['nodes'])):
                    if _jconf['preprov_network']['nodes'][i]['client']['dom0_oracle_name'] == _custNodeDom0:
                        _prepNode = _jconf['preprov_network']['nodes'][i]
                        break


                _custHost    = "{0}.{1}".format(_custNode['client']['hostname'], _custNode['client']['domainname'])
                _prepHost    = "{0}.{1}".format(_prepNode['client']['hostname'], _prepNode['client']['domainname'])
                _currentNode = None

                _dom0 = ""

                #Find the Dom0
                for _dom0Name, _ in self.mGetClubox().mReturnDom0DomUPair():
                    if _dom0Name.find(_prepNode['client']['dom0_oracle_name']) != -1:
                        _dom0 = _dom0Name
                        break

                if _dom0 == "":
                    ebLogInfo("No Dom0 Found: {0}".format(_prepNode['client']['dom0_oracle_name']))
                    return False

                _dom0node = exaBoxNode(get_gcontext())
                _dom0node.mConnect(aHost=_dom0)

                _rcCust = _dom0node.mSingleLineOutput("ls /EXAVMIMAGES/GuestImages | grep '{0}'".format(_custHost))
                _rcPrep = _dom0node.mSingleLineOutput("ls /EXAVMIMAGES/GuestImages | grep '{0}'".format(_prepHost))
                if self.mGetClubox().mIsKVM():
                    _rcCustXm = _dom0node.mSingleLineOutput("/usr/sbin/vm_maker --list | grep {0}".format(_custHost))
                    _rcPrepXm = _dom0node.mSingleLineOutput("/usr/sbin/vm_maker --list | grep {0}".format(_prepHost))
                else:
                    _rcCustXm = _dom0node.mSingleLineOutput("xm list | grep {0} | awk '{{print $1}}'".format(_custHost))
                    _rcPrepXm = _dom0node.mSingleLineOutput("xm list | grep {0} | awk '{{print $1}}'".format(_prepHost))
                _dom0node.mDisconnect()

                #Discover the real name of the vm on the Dom0
                if _rcCust != "":
                    _currentNode = _custNode

                elif _rcCustXm != "":
                    _currentNode = _custNode

                elif _rcPrep != "":
                    _currentNode = _prepNode

                elif _rcPrepXm != "":
                    _currentNode = _prepNode

                else:
                    ebLogInfo("Skip machine config on Delete Service, {0}/{1}".format(_custHost, _prepHost))
                    continue

                #Patch the XML
                if _currentNode is not None:

                    _mac_conf_list = self.mGetClubox().mGetMachines().mGetMachineConfigList()
                    for _machine in _mac_conf_list.keys():

                        _mac_conf = _mac_conf_list[_machine]

                        if _mac_conf.mGetMacHostName().find(_prepHost) == -1 and _mac_conf.mGetMacHostName().find(_custHost) == -1:
                            continue

                        _currHost   = _currentNode['client']['hostname']
                        _currDomain = _currentNode['client']['domainname']
                        _currFQDN   = "{0}.{1}".format(_currHost, _currDomain)

                        ebLogInfo("Update Machine: {0}/{1} to {2}".format(_machine, _mac_conf.mGetMacHostName(), _currFQDN))
                        _mac_conf.mSetMacHostName(_currFQDN)

                        #Update Network Information
                        _domu_conf_net = _mac_conf.mGetMacNetworks()

                        for _net_id in _domu_conf_net:
                            _net_conf = self.mGetClubox().mGetNetworks().mGetNetworkConfig(_net_id)
                            _net_id_prefix = _net_id.split('_')[-1]

                            if _net_id_prefix == 'client':
                                ebLogInfo("Update Network: {0}".format(_net_id))
                                _net_conf.mSetNetHostName(_currHost)
                                _net_conf.mSetNetDomainName(_currDomain)

        self.mGetClubox().mReturnDom0DomUPair(aForce=True)

# end of file
