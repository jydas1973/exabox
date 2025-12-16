#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/ovm/reconfig/clubackup_kvm.py /main/3 2022/03/11 03:05:32 naps Exp $
#
# clubackup_kvm.py
#
# Copyright (c) 2020, 2022, Oracle and/or its affiliates. 
#
#    NAME
#      clubackup_kvm.py - clubackup_kvm
#
#    DESCRIPTION
#      KVM implementation of clubackup
#
#    NOTES
#      Backup process page: https://www.bacula.org/kvm-backup-vm/
#
#    MODIFIED   (MM/DD/YY)
#    naps        03/06/22 - remove virsh dependency layer.
#    jesandov    05/18/20 - Creation
#

import os

from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogError, ebLogInfo
from exabox.core.Context import get_gcontext
from exabox.ovm.vmcontrol import ebVgLifeCycle

from exabox.ovm.reconfig.clubackup import ebCluBackup

class ebCluBackupKvm(ebCluBackup):

    def __init__(self, aClubox):
        ebCluBackup.__init__(self, aClubox)

        self.mSetVmsFolder("/EXAVMIMAGES/GuestImages")
        self.mSetBackupFolder("/EXAVMIMAGES/RollbackBackup")

    def mCreateBackup(self, aDom0Name, aVmName):
        """
        Create a new backup
        if the backup not exists, shutdown the vm, create the backup, restore the backup and start the vm

        :param:aDom0Name: The name of the Dom0 where is executed
        :param:aVmName: The name of the VM
        """

        _location = self.mFetchBackup(aDom0Name, aVmName)

        if _location is not None:
            ebLogInfo("Backup already in: {0}".format(_location))

        else:

            _dom0Node = self.mGetConnection(aDom0Name)

            # Make the VM Backup
            ebLogInfo("Creating Backup of VM XML: {0}".format(aVmName))
            _cmd = "/usr/sbin/vm_maker --dumpxml {0} > /tmp/backup_{0}.xml".format(aVmName)
            _dom0Node.mExecuteCmd(_cmd)

            # Shutdown the VM
            ebLogInfo("Shutdown VM to create Backup: {0}".format(aVmName))
            _vmhandle = ebVgLifeCycle()
            _vmhandle.mSetOVMCtrl(aCtx=get_gcontext(), aNode=_dom0Node)
            _vmhandle.mSetDestroyOnStart(True)
            _vmhandle.mDispatchEvent('shutdown', aOptions=None, aVMId=aVmName)

            # Make the VM Backup
            ebLogInfo("Creating Backup of VM: {0}".format(aVmName))
            _dom0Node.mExecuteCmd("/bin/mkdir -p {0}".format(self.mGetBackupFolder()))
            _dom0Node.mExecuteCmd("/bin/mv {0}/{1} {2}".format(self.mGetVmsFolder(), aVmName, self.mGetBackupFolder()))
            _dom0Node.mExecuteCmd("/bin/mv /tmp/backup_{0}.xml {1}/{0}/backup.xml".format(aVmName, self.mGetBackupFolder()))
            self.mRestoreBackup(aDom0Name, aVmName)

            # Restore the new created backup to the vm
            ebLogInfo("Restore Backup of VM: {0}".format(aVmName))
            self.mGetClubox().mRestartVM(aVmName, aVMHandle=_vmhandle)


    def mRestoreBackup(self, aDom0Name, aVmName):

        _location = self.mFetchBackup(aDom0Name, aVmName)

        if _location is None:
            ebLogError("Failing to Verify Backup of VM '{0}'".format(aVmName))
            raise ValueError

        ebLogInfo("Start VM Restore on Dom0: {0}, DomU: {1}".format(aDom0Name, aVmName))

        _dom0Node = self.mGetConnection(aDom0Name)

        # Undefine the vm
        _dom0Node.mExecuteCmd("/usr/bin/virsh undefine {0}".format(aVmName))

        # Start the copy from the backup
        _dom0Node.mExecuteCmd("/bin/mkdir -p {0}/{1}".format(self.mGetVmsFolder(), aVmName))

        #Copy the files
        _, _o, _ = _dom0Node.mExecuteCmd("/bin/ls {0}/{1}/*".format(self.mGetBackupFolder(), aVmName))
        _files = list(map(lambda x: x.strip(), _o.readlines()))

        for _file in _files:
            _basename = os.path.basename(_file)

            #Copy files from backup
            _cmd = "/bin/cp "
            _cmd += "{backup}/{vm}/{base} {vmfolder}/{vm}/{base}".format(backup=self.mGetBackupFolder(),
                                                                         vm=aVmName,
                                                                         base=_basename,
                                                                         vmfolder=self.mGetVmsFolder())

            _dom0Node.mExecuteCmd(_cmd)

        # define the vm from backup
        _dom0Node.mExecuteCmd("/usr/bin/virsh define {0}/{1}/backup.xml".format(self.mGetVmsFolder(), aVmName))

        ebLogInfo("Restored on Dom0: {0}, DomU: {1}".format(aDom0Name, aVmName))


    def mDeleteBackup(self, aDom0Name, aVmName):

        _rc = 1
        _dom0Node = self.mGetConnection(aDom0Name)

        _location = self.mFetchBackup(aDom0Name, aVmName)
        if _location is not None:

            ebLogInfo("Delete the Backup of {0} located on {1}:{2}".format(aVmName, aDom0Name, _location))

            _dom0Node.mExecuteCmd("/bin/rm -rf {0}".format(_location))
            _rc = _dom0Node.mGetCmdExitStatus()

        return _rc


    def mFetchBackup(self, aDom0Name, aVmName):

        _dom0Node = self.mGetConnection(aDom0Name)

        _cmd = "/bin/find {0} | /bin/grep '{1}'".format(self.mGetBackupFolder(), aVmName)
        _dom0Node.mExecuteCmd(_cmd)

        if _dom0Node.mGetCmdExitStatus() == 0:

            _location = _dom0Node.mSingleLineOutput(_cmd)
            return _location

        return None

# end of file
