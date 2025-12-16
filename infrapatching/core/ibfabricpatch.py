#
# $Header: ecs/exacloud/exabox/infrapatching/core/ibfabricpatch.py /main/7 2024/09/24 16:45:50 araghave Exp $
#
# ibfabricpatch.py
#
# Copyright (c) 2020, 2024, Oracle and/or its affiliates.
#
#    NAME
#      ibfabricpatch.py - Class IBFabricPatch has fabric and synchronization on
#      Exadata cluster operation.
#
#    DESCRIPTION
#      This module manages locking on cluster patching operation.
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    araghave    08/27/24 - Enh 36829406 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE CORE, PLUGIN AND TASKHANDLER
#                           FILES
#    araghave    06/13/24 - Enh 36522596 - REVIEW PRE-CHECK/PATCHING/ROLLBACK
#                           LOGS AND CLEAN-UP
#    araghave    10/19/23 - Bug 35747726 - PATCHING FAILING WITH | ERROR -
#                           ERROR MESSAGE IN A SHARED IBFABRIC ENVIRONMENT,
#                           COMBINATION OF AN IBSWITCH/NON-IBSWITCH TARGET
#                           PATCH CANNOT BE RUN IN PARALLEL
#    araghave    01/19/21 - Bug 32395969 - MONTHLY PATCHING: FOUND FEW ISSUES
#                           WHILE TESTING AND NEED TO FIX
#    araghave    01/05/21 - Bug 32343803 - INFRAPATCHING: INVALID REQUEST ADDED
#                           WHEN PATCHING ATTEMPTED VIA CURL
#    nmallego    08/28/20 - Refactor infra patching code
#    nmallego    08/28/20 - Creation
#

from exabox.core.DBStore import ebGetDefaultDB
from exabox.infrapatching.handlers.loghandler import LogHandler

class IBFabricPatch(LogHandler):
    """
    Wrapper that allows to manage the information located in ibfabriclocks table.
    """

    def __init__(self, aFabricID, aSha512, aDoSwitch, aBusyClusters, aCluPatchObjects, aLockedFor, aFabricLock):
        super(IBFabricPatch, self).__init__()
        self.__id = int(aFabricID)
        self.__sha512 = str(aSha512)
        self.__do_switch = str(aDoSwitch)
        self.__clusters = str(aBusyClusters)
        self.__cluobjs = aCluPatchObjects
        self.__lockedfor = str(aLockedFor)
        self.__fabriclock = int(aFabricLock)
        self.__ibswitches = []

    def mCheckCluster(self, aClusterName):
        """
        Checks if cluster is already in the local list of clusters.
        """

        _list = self.mGetCluObjects()
        if _list:
            for _index,_clu in enumerate(_list):
                if _clu.mGetClusterName() == aClusterName:
                    return _index
        return -1

    def mAddCluster(self, aClusterObj):
        """
        Adds a new cluster to the local list of clusters.
        """

        if self.__cluobjs:
            self.__cluobjs.append(aClusterObj)
        else:
            self.__cluobjs = [aClusterObj]

        return (len(self.__cluobjs) - 1)

    def mGetCluster(self, aClusterIndex):
        """
        Gets the IBClusterPatch object from the clusters list located in aClusterIndex
        """

        if self.__cluobjs and aClusterIndex < len(self.__cluobjs):
            return self.__cluobjs[aClusterIndex]
        return None

    def mDeleteCluster(self, aClusterIndex):
        """
        Deletes cluster from clusters list.
        """

        if self.__cluobjs and aClusterIndex < len(self.__cluobjs):
            self.__cluobjs.pop(aClusterIndex)

    def mSetIBFabricID(self, aFabricID):
        self.__id = int(aFabricID)

    def mGetIBFabricID(self):
        return self.__id

    def mSetSha512(self, aSha512):
        self.__sha512 = aSha512

    def mGetSha512(self):
        return self.__sha512

    def mSetDoSwitch(self, aDoSwitch):
        self.__do_switch = aDoSwitch

    def mGetDoSwitch(self):
        return self.__do_switch

    def mSetBusyClustersList(self, aClusters):
        self.__clusters = aClusters

    def mGetBusyClustersList(self):
        return self.__clusters

    def mSetCluObjects(self,aCluPatchObjects):
        self.__cluobjs = aCluPatchObjects

    def mGetCluObjects(self):
        return self.__cluobjs

    def mSetLockedFor(self, aLockedFor):
        self.__lockedfor = aLockedFor

    def mGetLockedFor(self):
        return self.__lockedfor

    def mSetFabricLock(self, aFabricLock):
        self.__fabriclock = int(aFabricLock)

    def mGetFabricLock(self):
        return self.__fabriclock

    def mSetIBSwitches(self, aIBSwitches):
        self.__ibswitches = aIBSwitches

    def mAddIBSwitch(self, aIBSwitch):
        self.__ibswitches.append(aIBSwitch)

    def mGetIBSwitches(self):
        return self.__ibswitches

    def mDumpIBFabric(self):
        """
        Prints the IBFabric information.
        """

        self.mPatchLogInfo("---------------------------------")
        self.mPatchLogInfo(f"IBFabric ID: {self.mGetIBFabricID():d}")
        self.mPatchLogInfo(f"Sha512: {self.mGetSha512()}")
        self.mPatchLogInfo(f"Clusters: {self.mGetBusyClustersList()} ")
        self.mPatchLogInfo(f"Lockedfor: {self.mGetLockedFor()}")
        self.mPatchLogInfo(f"FabricLock: {self.mGetFabricLock():d}")
        self.mPatchLogInfo(f"IBSwitchList: {str(self.mGetIBSwitches())}")
        for _c in self.__cluobjs:
            self.mPatchLogInfo(f"\t\tCluster {_c.mGetClusterName()} ID: {_c.mGetIBClusterID():d} ")
        self.mPatchLogInfo("---------------------------------")

    def mLock(self, aClusterID, non_ibswitch):
        """
        Locks a specified cluster and ibfabric if non_ibswitch is set to False.
        """

        self.mDumpIBFabric()
        _db = ebGetDefaultDB()

        if non_ibswitch:
            return _db.mManageIBFabricLock(self.mGetIBFabricID(), aClusterID, True, 'non_ibswitch')

        self.mPatchLogInfo("Acquiring lock using switch fabric details.")
        return _db.mManageIBFabricLock(self.mGetIBFabricID(), aClusterID, True, 'ibswitch')

    def mRelease(self, aClusterID):
        """
        Releases the lock for a specified cluster and ibfabric if necessary.
        """
        self.mDumpIBFabric()
        _db = ebGetDefaultDB()
        self.mPatchLogInfo("Release Switch fabric based lock previously acquired.")
        return _db.mManageIBFabricLock(self.mGetIBFabricID(), aClusterID, False)

    def mUpdateDoSwitchDB(self):
        """
        Updates do_switch column in db.
        """

        _db = ebGetDefaultDB()
        return _db.mSetDoSwitchIBFabic(self.mGetIBFabricID(), self.mGetDoSwitch())

    def mResetSwitchFabricdata(self):
        """
         Resets all the data in this object by reading the values from the db.
         In case of switch fabric locking mechanism disabled, we should reset
         all the entries in ibfabriclocks table as the lock is not acquired
         currently and stale sessions must not exist in the next patch cycle,
         when the switch fabric based locking mechanism is enabled.

         - As per current logic, stale entries are required to be cleaned up
           manually if there is a patch failure encountered and entries were
           not cleaned up.
        """
        _db = ebGetDefaultDB()
        _row = _db.mCheckIBFabricEntry(aFabricID=self.mGetIBFabricID())
        if _row:
            self.mPatchLogInfo("Ibfabriclocks table entries on the exacloud db before reset.")
            self.mDumpIBFabric()

            self.mSetDoSwitch('no')
            self.mSetSha512(_row[1])
            self.mSetBusyClustersList('')
            self.mSetLockedFor('none')
            self.mSetFabricLock(0)

            self.mPatchLogInfo("Ibfabriclocks table entries are reset in this case to ensure no stale entries are present before running the next patch iteration.")
            self.mPatchLogInfo("Current values on the ibfabriclocks table on the exacloud DB after reset are as follows :")
            self.mDumpIBFabric()
        else:
            self.mPatchLogInfo("No switch fabric entries present in exacloud DB IBfabriclocks table and no action to cleanup stale entries required for now.")

    def mRefreshData(self):
        """
        Refreshes all the data in this object by reading the values from the db.
        """

        _db = ebGetDefaultDB()

        _row = _db.mCheckIBFabricEntry(aFabricID=self.mGetIBFabricID())

        if _row:
            '''
             Case 1 : Reset do_switch to 'no' in case request is left with stale data. Basically, we need to look
                      for list_clusters_in_process to '' (empty) and lockedcount is '0'.

               sqlite> select * from ibfabriclocks;
               id|ibswitches_output_sha512|do_switch|list_clusters_in_process|lockedfor|lockcount
               1|c99d4253ec79f9008696ec7c5d5017bcaa74b02f8ee6722e6c6cf8c3a85e1edfd841a903b0366da74ba4f9a399158a002f77d856d784f5df1815ce511846267e|yes||none|0
               sqlite> .exit
            '''
            if _row[2] == 'yes' and _row[3] in [ None, '' ] and _row[5] > 0:
                self.mPatchLogInfo("A stale session was found in the DB, cleaning the same and proceeding with patch operations.")
                self.mSetDoSwitch('no')
                self.mUpdateDoSwitchDB()
            else:
                self.mSetDoSwitch(_row[2])

            self.mSetSha512(_row[1])
            self.mSetBusyClustersList(_row[3])
            self.mSetLockedFor(_row[4])
            self.mSetFabricLock(_row[5])
