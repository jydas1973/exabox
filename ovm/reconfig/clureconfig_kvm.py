#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/ovm/reconfig/clureconfig_kvm.py /main/7 2022/03/11 03:05:32 naps Exp $
#
# clureconfig_kvm.py
#
# Copyright (c) 2020, 2022, Oracle and/or its affiliates. 
#
#    NAME
#      clureconfigkvm.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      KVM Interface method for ebCluReconfig
#
#    NOTES
#      NONE
#
#    MODIFIED   (MM/DD/YY)
#    naps        03/06/22 - remove virsh dependency layer.
#    ajayasin    03/07/21 - 32595640_fix
#    jesandov    05/18/20 - Creation
#

import copy
import xml.dom.minidom
import defusedxml.ElementTree as ET

from exabox.core.Error import ExacloudRuntimeError
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn
from exabox.core.Context import get_gcontext
from exabox.ovm.atp import AtpAddiptables2Dom0
from exabox.ovm.reconfig.clureconfig import ebCluReconfig
from tempfile import NamedTemporaryFile

class ebCluReconfigKvm(ebCluReconfig):

    def __init__(self, aClubox, aBackupTool):
        ebCluReconfig.__init__(self, aClubox, aBackupTool)

        self.__remotePrefix = "/tmp/reconfig"
        self.__xmlTree = None
        self.__initialVmName = None

    ######################
    # Getter and Setters #
    ######################

    def mGetRemotePrefix(self):
        return self.__remotePrefix

    def mSetRemotePrefix(self, aRemotePrefix):
        self.__remotePrefix = aRemotePrefix

    def mGetRemoteFile(self):
        return "{0}-{1}.xml".format(self.__remotePrefix, self.__initialVmName)

    def mGetXmlTree(self):
        return self.__xmlTree

    def mSetXmlTree(self, aTree):
        self.__xmlTree = aTree

    def mGetInitialVmName(self):
        return self.__initialVmName

    def mSetInitialVmName(self, aVmName):
        self.__initialVmName = aVmName

    ################
    # Dom0 Methods #
    ################

    def mInitStep(self, aDom0Node, aInitialVm):

        # If the tree exists, already init
        if self.mGetXmlTree():
            return

        self.mSetInitialVmName(aInitialVm)
        _xmlTree = None

        # If remote file exist, read the configuration
        if self.mGetRemoteFile() and \
           aDom0Node.mFileExists(self.mGetRemoteFile()):

            _, _o, _ = aDom0Node.mExecuteCmd("cat {0}".format(self.mGetRemoteFile()))
            _xmlTree = ET.fromstring(_o.read())

        # Anyother case, dump the xml
        else:

            _, _o, _ = aDom0Node.mExecuteCmd("/usr/sbin/vm_maker --dumpxml {0}".format(aInitialVm))
            _xmlTree = ET.fromstring(_o.read())

        # Save the XML Tree
        self.mSetXmlTree(_xmlTree)
        self.mRecordXml(aDom0Node, "Init")

    def mRecordXml(self, aDom0Node, aStepName):

        # Put the new configuration into the workdir
        _xmlOutFile = "{0}/{1}-{2}.xml".format(self.mGetReconfigWorkdir(), self.mGetInitialVmName(), aStepName)
        _xmlStr = xml.dom.minidom.parseString(ET.tostring(self.mGetXmlTree()).decode('utf8'))
        _pretty = _xmlStr.toprettyxml()

        with NamedTemporaryFile(mode='w+', delete=True) as _tmp:
            _tmp.write(_pretty)
            _tmp.flush()
            # Upload the extracted XML into the Dom0
            aDom0Node.mCopyFile(_tmp.name, self.mGetRemoteFile())

    def mReconfigDom0ChangeVifVlan(self, aDom0Node, aOldName, aNewName, aOldJson, aNewJson):

        # Read XML Info
        self.mInitStep(aDom0Node, aOldName)

        # Change the mac address
        _xpath = 'devices/interface/alias[@name="net0"]/../mac'
        _node = self.mGetXmlTree().find(_xpath)

        if _node is not None:
            _node.set("address", aNewJson['client']['mac'])
        else:
            ebLogWarn("Missing node on tree: '{0}'".format(_xpath))

        # Configure VLAN
        ebLogInfo("Configure VLANs")

        if "vlantag" in aNewJson['client'].keys() and aNewJson['client']['vlantag'] is not None:
            ebLogInfo("Configure VLAN of client")
            _vlanId = int(aNewJson['client']['vlantag'])
            self.mConfigureVLAN(aDom0Node, "bondeth0", _vlanId, "client")
        else:
            ebLogInfo("No VLAN change of client")

        if "vlantag" in aNewJson['backup'].keys() and aNewJson['backup']['vlantag'] is not None:
            ebLogInfo("Configure VLAN of backup")
            _vlanId = int(aNewJson['backup']['vlantag'])
            self.mConfigureVLAN(aDom0Node, "bondeth0", _vlanId, "backup")
        else:
            ebLogInfo("No VLAN change of backup")

        # Put the new configuration into the guest
        self.mRecordXml(aDom0Node, "mReconfigDom0ChangeVifVlan")


    def mConfigureVLAN(self, aDom0Node, aInterface, aVlanId, aNetType):

        _iface = "%s.%s" % (aInterface, aVlanId)

        ebLogInfo("Configuring VLAN {0}".format(_iface))

        _cmd = """ ! /usr/bin/test -e /etc/sysconfig/network-scripts/ifcfg-{0} &&
/bin/echo "DEVICE={0}
TYPE=Ethernet
BOOTPROTO=none
ONBOOT=yes
VLAN=yes
BRIDGE=vm{0}
NM_CONTROLLED=no" > /etc/sysconfig/network-scripts/ifcfg-{0} """ .format(_iface)
        aDom0Node.mExecuteCmd(_cmd)

        #Up the new interface
        aDom0Node.mExecuteCmd("/sbin/ifup {0}".format(_iface))

        _cmd = """ ! /usr/bin/test -e /etc/sysconfig/network-scripts/ifcfg-vm{0} &&
/bin/echo "DEVICE=vm{0}
TYPE=Bridge
BOOTPROTO=none
ONBOOT=yes
DELAY=0" > /etc/sysconfig/network-scripts/ifcfg-vm{0} """ .format(_iface)
        aDom0Node.mExecuteCmd(_cmd)

        #Up the new interface
        aDom0Node.mExecuteCmd("/sbin/ifup vm{0}".format(_iface))
        ebLogInfo("Created interface for VLAN: vm{0}".format(_iface))

        # Get tne net alias by network type
        _aliasInterface = "x"

        if aNetType == "client":
            _aliasInterface = "net0"

        elif aNetType == "backup":
            _aliasInterface = "net1"

        # Configure the vlan in the XML netX
        _xpath = 'devices/interface/alias[@name="{0}"]/../source'.format(_aliasInterface)
        _node = self.mGetXmlTree().find(_xpath)

        ebLogInfo("VLAN Modified bridge of {0} with vm{1}".format(_aliasInterface, _iface))

        if _node is not None:
            _node.set('bridge', "vm{0}".format(_iface))
        else:
            ebLogWarn("VLAN Missing node on tree: '{0}'".format(_xpath))

    def mReconfigDom0UpdateNetwork(self, aDom0Node, aOldName, aNewName, aOldJson, aNewJson):

        # Read XML Info
        self.mInitStep(aDom0Node, aOldName)

        # Apply Rename if in payload
        ebLogInfo("Update VM Network from: {0} to {1}".format(aOldName, aNewName))

        # Change the XML file
        _xmlstr = ET.tostring(self.mGetXmlTree()).decode('utf8')
        _xmlstr = _xmlstr.replace(aOldName, aNewName)
        _xmlTree = ET.fromstring(_xmlstr)

        self.mSetXmlTree(_xmlTree)

        # Update rules of ATP
        if self.mGetClubox().isATP() and \
           self.mGetClubox().mIsExabm() and \
           self.mGetClubox().mCheckClusterNetworkType():

            ebLogInfo("Executing AtpAddiptables2Dom0")

            AtpAddiptables2Dom0(aDom0Node, self.mGetClubox().mGetATP(), \
                                  self.mGetClubox().mReturnDom0DomUPair(), \
                                  self.mGetClubox().mGetMachines(), 
                                  self.mGetClubox().mGetNetworks()
                               ).mExecute()

        # Put the new configuration into the guest
        self.mRecordXml(aDom0Node, "mReconfigDom0UpdateNetwork")

    def mRollbackUpdateVmFolder(self, aDom0Node, aNewVmName, aOldVmName):

        # Undefine the old domain
        aDom0Node.mExecuteCmd('/usr/bin/virsh undefine {0}'.format(aOldVmName))

        # Undefine the old domain
        aDom0Node.mExecuteCmd('/usr/bin/virsh undefine {0}'.format(aNewVmName))

        # Rename network filters
        self.mMoveNetworksFilters(aDom0Node, aNewVmName, aOldVmName)

    def mReconfigCleanUpEnv(self):

        # Remove all .backup.xml
        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            ebLogInfo("Removing Backups in Dom0 {0}".format(_dom0))
            _dom0Node = exaBoxNode(get_gcontext())

            try:
                _dom0Node.mConnect(aHost=_dom0)
                _dom0Node.mExecuteCmdLog("/bin/rm /etc/libvirt/qemu*.backup.xml")

            finally:
                _dom0Node.mDisconnect()


    def mMoveNetworksFilters(self, aDom0Node, aTargetVmName, aReplaceVmName):

        # Rename the network filters
        _cmd = "/usr/bin/virsh nwfilter-list | awk '{{print $2}}' | grep {0}".format(aTargetVmName)
        _, _o, _ = aDom0Node.mExecuteCmd(_cmd)

        if _o:
            _filters = list(map(lambda x: x.strip(), _o.readlines()))
            for _filter in _filters:

                _cmd = "/usr/bin/virsh nwfilter-dumpxml {0} > /tmp/{0}".format(_filter)
                aDom0Node.mExecuteCmd(_cmd)

                _cmd = "/usr/bin/virsh nwfilter-undefine {0}".format(_filter)
                aDom0Node.mExecuteCmdLog(_cmd)

                _cmd = "sed -i 's/{0}/{1}/g' /tmp/{2}".format(aTargetVmName, aReplaceVmName, _filter)
                aDom0Node.mExecuteCmd(_cmd)

                _cmd = "/usr/bin/virsh nwfilter-define /tmp/{0}".format(_filter)
                aDom0Node.mExecuteCmdLog(_cmd)


    def mReconfigDom0UpdateVmFolder(self, aDom0Node, aOldVmName, aNewVmName):

        # Read XML Info
        self.mInitStep(aDom0Node, aOldVmName)

        # Change the name
        _xpath = "name"
        _node = self.mGetXmlTree().find(_xpath)

        if _node is not None:
            _node.text = aNewVmName
        else:
            ebLogWarn("Missing node on tree: '{0}'".format(_xpath))

        # Put the new configuration into the guest
        self.mRecordXml(aDom0Node, "mReconfigDom0UpdateVmFolder")

        # Undefine the old domain
        aDom0Node.mExecuteCmdLog('/usr/bin/virsh undefine {0}'.format(aOldVmName))

        # Move the folder
        _cmd = "/bin/mv {0}/{1} {0}/{2}".format("/EXAVMIMAGES/GuestImages", aOldVmName, aNewVmName)
        aDom0Node.mExecuteCmd(_cmd)

        # Define the new domain
        aDom0Node.mExecuteCmdLog('/usr/bin/virsh define {0}'.format(self.mGetRemoteFile()))
        aDom0Node.mExecuteCmdLog('/usr/bin/virsh autostart {0}'.format(aNewVmName))

        # Rename the network filters
        self.mMoveNetworksFilters(aDom0Node, aOldVmName, aNewVmName)

        # Save the new edited VM name on Exacloud qemu backups
        _path = "/opt/exacloud/qemu_backup/reconfig/"
        aDom0Node.mExecuteCmd("/bin/mkdir -p {0}".format(_path))
        aDom0Node.mExecuteCmd("/bin/mv {0} {1}/{2}".format(self.mGetRemoteFile(), _path, aNewVmName))


# end of file
