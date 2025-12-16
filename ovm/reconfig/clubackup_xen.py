#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/ovm/reconfig/clubackup_xen.py /main/2 2020/12/09 11:01:46 jesandov Exp $
#
# clubackup_xen.py
#
# Copyright (c) 2020, Oracle and/or its affiliates. 
#
#    NAME
#      clubackup_xen.py - clubackup_xen
#
#    DESCRIPTION
#      XEN implentation of clubackup
#      <short description of component this file declares/defines>
#
#    NOTES
#      NONE
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    05/18/20 - Creation
#

import os

from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogError, ebLogInfo
from exabox.core.Context import get_gcontext
from exabox.ovm.vmcontrol import ebVgLifeCycle

from exabox.ovm.reconfig.clubackup import ebCluBackup

class ebCluBackupXen(ebCluBackup):

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

            #Shutdown the vm
            ebLogInfo("Shutdown VM to create Backup: {0}".format(aVmName))
            _vmhandle = ebVgLifeCycle()
            _vmhandle.mSetOVMCtrl(aCtx=get_gcontext(), aNode=_dom0Node)
            _vmhandle.mSetDestroyOnStart(True)
            _vmhandle.mDispatchEvent('shutdown', aOptions=None, aVMId=aVmName)

            #Make the vm backup
            ebLogInfo("Creating Backup of VM: {0}".format(aVmName))
            _dom0Node.mExecuteCmd("/bin/mkdir -p {0}".format(self.mGetBackupFolder()))
            _dom0Node.mExecuteCmd("/bin/mv {0}/{1} {2}".format(self.mGetVmsFolder(), aVmName, self.mGetBackupFolder()))
            self.mRestoreBackup(aDom0Name, aVmName)

            #Restore the new created backup to the vm
            ebLogInfo("Restore Backup of VM: {0}".format(aVmName))
            self.mGetClubox().mRestartVM(aVmName, aVMHandle=_vmhandle)


    def mRestoreBackup(self, aDom0Name, aVmName):
        """
        Restore a backup from the backup folder to the vms folder

        :param:aDom0Name: The name of the Dom0 where is executed
        :param:aVmName: The name of the VM
        """

        _location = self.mFetchBackup(aDom0Name, aVmName)

        if _location is None:
            ebLogError("Failing to Verify Backup of VM '{0}'".format(aVmName))
            raise ValueError

        ebLogInfo("Start VM Restore on Dom0: {0}, DomU: {1}".format(aDom0Name, aVmName))

        _dom0Node = self.mGetConnection(aDom0Name)

        #Create the folder with the name of the vm
        _dom0Node.mExecuteCmd("/bin/mkdir -p {0}/{1}".format(self.mGetVmsFolder(), aVmName))

        #Copy the files
        _, _o, _ = _dom0Node.mExecuteCmd("/bin/ls {0}/{1}/*".format(self.mGetBackupFolder(), aVmName))
        _files = list(map(lambda x: x.strip(), _o.readlines()))

        for _file in _files:
            _basename = os.path.basename(_file)

            #Symbolic link the .img and .tar.gz
            if _basename.endswith(".img") or _basename.endswith(".tar.gz"):
                _cmd = "/usr/bin/reflink "
            else:
                _cmd = "/bin/cp "

            _cmd += "{backup}/{vm}/{base} {vmfolder}/{vm}/{base}".format(backup=self.mGetBackupFolder(),
                                                                        vm=aVmName,
                                                                        base=_basename,
                                                                        vmfolder=self.mGetVmsFolder())
            _dom0Node.mExecuteCmd(_cmd)

        ebLogInfo("Restored on Dom0: {0}, DomU: {1}".format(aDom0Name, aVmName))

    def mDeleteBackup(self, aDom0Name, aVmName):
        """
        Delete a backup from the backup folder

        :param:aDom0Name: The name of the Dom0 where is executed
        :param:aVmName: The name of the VM

        :return: return code of remove command
        :rtype: int
        """
        _rc = 0
        _dom0Node = self.mGetConnection(aDom0Name)

        _location = self.mFetchBackup(aDom0Name, aVmName)
        if _location is not None:

            ebLogInfo("Delete the Backup of {0} located on {1}:{2}".format(aVmName, aDom0Name, _location))

            _dom0Node.mExecuteCmd("/bin/rm -rf {0}".format(_location))
            _rc = _dom0Node.mGetCmdExitStatus()

        else:
            _rc = 1

        return _rc

    def mFetchBackup(self, aDom0Name, aVmName):
        """
        Find a backup in the backup folder

        :param:aDom0Name: The name of the Dom0 where is executed
        :param:aVmName: The name of the VM
        """

        _dom0Node = self.mGetConnection(aDom0Name)

        _cmd = "/bin/find {0} | /bin/grep '{1}'".format(self.mGetBackupFolder(), aVmName)
        _dom0Node.mExecuteCmd(_cmd)

        if _dom0Node.mGetCmdExitStatus() == 0:

            _location = _dom0Node.mSingleLineOutput(_cmd)
            return _location

        return None

# end of file
