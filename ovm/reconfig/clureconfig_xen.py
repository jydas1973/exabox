#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/ovm/reconfig/clureconfig_xen.py /main/6 2021/05/31 21:44:50 pbellary Exp $
#
# clureconfig_xen.py
#
# Copyright (c) 2020, 2021, Oracle and/or its affiliates. 
#
#    NAME
#      clureconfigxm.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      Xen Interface method for ebCluReconfig
#
#    NOTES
#      NONE
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    05/18/20 - Creation
#

import re
import ast
import time

from exabox.core.Error import ExacloudRuntimeError
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn
from exabox.core.Context import get_gcontext
from exabox.ovm.vmcontrol import exaBoxOVMCtrl, ebVgLifeCycle
from exabox.ovm.atp import AtpAddiptables2Dom0
from exabox.ovm.reconfig.clureconfig import ebCluReconfig

class ebCluReconfigXen(ebCluReconfig):

    def __init__(self, aClubox, aBackupTool):
        ebCluReconfig.__init__(self, aClubox, aBackupTool)

    ################
    # Dom0 Methods #
    ################

    def mReconfigDom0ChangeVifVlan(self, aDom0Node, aOldName, aNewName, aOldJson, aNewJson):

        #Get the information of the configuration file
        _vmhandle = exaBoxOVMCtrl(aCtx=get_gcontext(), aNode=aDom0Node)
        _vmhandle.mReadRemoteCfg(aOldName)
        _cfg = _vmhandle.mGetOVSVMConfig(aOldName)

        if not _cfg:
            ebLogError('Invalid name on VM, vm.cfg does not exists on {0}'.format(aOldName))
            raise ExacloudRuntimeError(0x8001, 0xA, 'Invalid name on VM, vm.cfg does not exists on {0}'.format(aOldName))

        # Remove information about the past vm vif
        _vif = ast.literal_eval(_cfg.mGetValue('vif'))
        _vif = list(filter(lambda x: x.upper().find(aOldJson['client']['mac'].upper()) == -1, _vif))
        _vif = list(filter(lambda x: x.upper().find(aOldJson['backup']['mac'].upper()) == -1, _vif))

        #Patch tne new macs and devices of Client
        _vifNode = "type=netfront,mac={0},bridge=vmbondeth0".format(aNewJson['client']['mac'])

        if "vlantag" in aNewJson['client'].keys() and aNewJson['client']['vlantag'] is not None:
            _vlanId = int(aNewJson['client']['vlantag'])
            _vifNode += ".{0}".format(_vlanId)
            self.mConfigureVLAN(aDom0Node, "bondeth0", _vlanId, "client")

        if _vifNode not in _vif:
            _vif.insert(0, _vifNode)

        # Patch the new macs and devices of Backup
        _vifNode = "type=netfront,mac={0},bridge=vmbondeth0".format(aNewJson['backup']['mac'])

        if "vlantag" in aNewJson['backup'].keys() and aNewJson['backup']['vlantag'] is not None:
            _vlanId = int(aNewJson['backup']['vlantag'])
            _vifNode += ".{0}".format(_vlanId)
            self.mConfigureVLAN(aDom0Node, "bondeth0", _vlanId, "backup")

        if _vifNode not in _vif:
            _vif.insert(1, _vifNode)

        #Restore Vif to file format
        _vif = list(map(lambda x: "'{0}'".format(x), _vif))
        _newVif = '['+",".join(_vif)+']'
        _cfg.mSetValue('vif', _newVif)

        # Save the configuration of the vm.cfg
        self.mGetClubox().mSaveVMCfg(aDom0Node, aOldName, _cfg.mRawConfig())

    def mConfigureVLAN(self, aDom0Node, aInterface, aVlanId, aNetType):

        _iface = "%s.%s" % (aInterface, aVlanId)

        ebLogInfo("Configuring VLAN {0}".format(_iface))

        _cmd = """ ! /usr/bin/test -e /etc/sysconfig/network-scripts/ifcfg-{0} &&
/bin/echo "DEVICE={0}
TYPE=Ethernet
BOOTPROTO=static
ONBOOT=yes
VLAN=yes
BRIDGE=vm{0}" > /etc/sysconfig/network-scripts/ifcfg-{0} """ .format(_iface)
        aDom0Node.mExecuteCmd(_cmd)

        #Up the new interface
        aDom0Node.mExecuteCmd("/sbin/ifup {0}".format(_iface))

        _cmd = """ ! /usr/bin/test -e /etc/sysconfig/network-scripts/ifcfg-vm{0} &&
/bin/echo "DEVICE=vm{0}
TYPE=Bridge
BOOTPROTO=static
ONBOOT=yes
DELAY=0" > /etc/sysconfig/network-scripts/ifcfg-vm{0} """ .format(_iface)
        aDom0Node.mExecuteCmd(_cmd)

        #Up the new interface
        aDom0Node.mExecuteCmd("/sbin/ifup vm{0}".format(_iface))

    def mReconfigDom0UpdateNetwork(self, aDom0Node, aOldName, aNewName, aOldJson, aNewJson):

        #Apply Rename if in payload
        ebLogInfo("Update VM Network from: {0} to {1}".format(aOldName, aNewName))

        #Rename the file with a proper name of the VM
        _base = "/bin/ls /opt/exacloud/network/vif-whitelist.*{0}* | /usr/bin/tr '/' '\\n' | /usr/bin/tail -1".format(aOldName)
        _cmd = "vifListNew=$({0} | /bin/sed 's/{1}/{2}/g');".format(_base, aOldName, aNewName)
        _cmd += "vifListOld=$({0});".format(_base)
        _cmd += "/bin/mv $vifListOld $vifListNew"
        aDom0Node.mExecuteCmd(_cmd)

        #Change the config file
        _fileConfig = '/EXAVMIMAGES/GuestImages/{0}/vm.cfg'.format(aOldName)
        _cmd = "/bin/sed --follow-symlinks -i s/{0}/{1}/g {2}".format(aOldName, aNewName, _fileConfig)
        aDom0Node.mExecuteCmd(_cmd)

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

    def mReconfigCleanUpEnv(self):
        return

    def mRollbackUpdateVmFolder(self, aDom0Node, aNewVmName, aOldVmName):

        self.mReconfigDom0UpdateVmFolder(aDom0Node, aNewVmName, aOldVmName)

    def mReconfigDom0UpdateVmFolder(self, aDom0Node, aOldVmName, aNewVmName):

        _vmhandle = exaBoxOVMCtrl(aCtx=get_gcontext(), aNode=aDom0Node)
        _vmhandle.mReadRemoteCfg(aOldVmName)
        _cfg = _vmhandle.mGetOVSVMConfig(aOldVmName)
        _uuid = re.sub("[\'\"\s]", "", _cfg.mGetValue('uuid'))

        if _cfg is not None:

            #Update disk information
            _diskspath = ast.literal_eval(_cfg.mGetValue('disk'))
            _diskspath = list(map(lambda x: x[x.find(":")+1: x.find("VirtualDisks/")+len("VirtualDisks/")], _diskspath))
            _diskspath = list(filter(lambda x: x.find("EXAV") == -1, _diskspath))
            _diskspath = _diskspath[0]

            _cmd = "/bin/ls %s*" % (_diskspath)
            _, _o, _ = aDom0Node.mExecuteCmd(_cmd)
            _o = _o.readlines()

            for _diskOutput in _o:
                _disk = _diskOutput.strip()
                if _disk.find(_diskspath) == -1:
                    _disk = _diskspath + _diskOutput.strip()

                _cmd =  "/bin/ls -la %s | " % (_disk)
                _cmd += "/bin/awk '{printf \"/bin/unlink %s; /bin/ln -sf %s %s\\n\", $9, $11, $9}' | "
                _cmd += '/bin/sed "s/{0}/{1}/g" | '.format(aOldVmName, aNewVmName)
                _cmd += "/bin/sh"
                aDom0Node.mExecuteCmd(_cmd)

            #Move the image folder
            _cmd = "/bin/mv /EXAVMIMAGES/GuestImages/{0} /EXAVMIMAGES/GuestImages/{1}".format(aOldVmName, aNewVmName)
            aDom0Node.mExecuteCmd(_cmd)

            #Upload the Symbolic Link /etc/xen/auto
            _vmlink = f"/OVS/Repositories/{_uuid}/vm.cfg"
            _cmd = "/bin/unlink /etc/xen/auto/{0}.cfg; ".format(aOldVmName)
            _cmd += "/bin/ln -sf {0} /etc/xen/auto/{1}.cfg; ".format(_vmlink, aNewVmName)
            _cmd += "/bin/unlink {0}; ".format(_vmlink)
            _cmd += "/bin/ln -sf /EXAVMIMAGES/GuestImages/{0}/vm.cfg {1}".format(aNewVmName, _vmlink)
            aDom0Node.mExecuteCmd(_cmd)


# end of file
