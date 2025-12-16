#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/cluinfradelete.py /main/8 2025/01/29 06:29:53 aararora Exp $
#
# cluinfradelete.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      cluinfradelete.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aararora    01/27/25 - Bug 37521880: Patch ntp and dns information during
#                           delete infra.
#    prsshukl    11/29/24 - Bug 37240032 - AFTER CELL PATCHING SYSTEM DATE IS
#                           SHOWING AS JAN 1ST 2019.
#    jfsaldan    08/22/23 - Bug 35719818 - PLEASE PROVIDE A WAY TO IDENTIFY
#                           FROM A XEN DOM0 IF THE GUESTVM HAS LUKS ENABLED OR
#                           NOT
#    aararora    07/03/23 - Bug 35156368: Add secure cell shredding during
#                           infra delete.
#    jfsaldan    11/03/22 - Bug 33993510 - CELLDISKS RECREATED AFTER DBSYSTEM
#                           TERMINATION
#    jfsaldan    06/08/22 - Bug 34242884 - Run vlanId change during prevm_setup
#                           only in singleVM, and run it on MVM during Delete
#                           Infra
#    jesandov    02/21/22 - Creation
#

from exabox.log.LogMgr import ebLogError, ebLogInfo
from exabox.ovm.cluencryption import deleteEncryptionMarkerFileForVM
from exabox.ovm.clumisc import ebCluPreChecks

class ebCluInfraDelete:

    def __init__(self, aClubox):
        self.__clubox = aClubox

    def mGetClubox(self):
        return self.__clubox

    def mExecute(self):

        if not self.mGetClubox().mIsOciEXACC():
            try:
                self.mGetClubox().mHandlerUpdateNtpDns()
            except Exception as ex:
                ebLogError(f"Ntp and Dns information could not be patched successfully. Exception: {ex}.")

        ebLogInfo("Running mCleanUpBackupsQemu")
        self.mGetClubox().mCleanUpBackupsQemu()

        _cluster_cells = self.mGetClubox().mReturnCellNodes()

        # This code block is under "iad_etf_enabled" parameter as this code block 
        # has to be skipped for IAD-ETF run
        if self.mGetClubox().mCheckConfigOption('iad_etf_enabled', 'False'):
            ebLogInfo(f"Running mRestoreStorageVlan in: '{_cluster_cells}'")
            self.mGetClubox().mRestoreStorageVlan(_cluster_cells)

            try:
                aOptions = self.mGetClubox().mGetArgsOptions()
                self.mGetClubox().mCellSecureShredding(aOptions, aInfraDelete=True, aForce=True)
            except Exception as ex:
                ebLogError("Secure cell shredding was not successful. Please perform it manually.")

            # IMPORTANT: Execute this after restoring the stre0/1 vlanID in the
            # cells. Reason: BUG 33993510
            if not self.mGetClubox().mIsExaScale():
                ebLogInfo("Drop all the celldisks in the Cells")
                self.mGetClubox().mGetStorage().mDropCellDisks(_cluster_cells)

                # adding the missing ntp and dns server value and restarting chrony
                # As OEDA is deleting the entry for cells Reason: BUG 37240032
                _pchecks = ebCluPreChecks(self.mGetClubox())
                _pchecks.mAddMissingNtpDnsIps(_cluster_cells)

        ebLogInfo("Running mSetSharedEnvironment")
        self.mGetClubox().mSetSharedEnvironment(aMode=False)

        # Delete the directory used to keep the marker files for fs encryption, it does
        # not matter if the directory exists or not, nor if this Infra ever had an
        # encrypted cluster, as it's not costly to rm this directory and will help
        # avoid future problems
        ebLogInfo("Running LUKS FS encryption marker removal")
        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
                deleteEncryptionMarkerFileForVM(_dom0)


# end of file
