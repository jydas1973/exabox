"""
$Header:

 Copyright (c) 2014, 2019, Oracle and/or its affiliates. All rights reserved.

NAME:
    ArchivingOperation - Handle DB Archiving, saving select queries, DELETING all other
                       - In the future we will implement more DB operations

FUNCTION:
    Handle requests DB policies

NOTE:
    None

History:

    MODIFIED   (MM/DD/YY)
    vgerard    09/05/19 - Create file
"""


from exabox.core.dbpolicies.Base import ebDbOperation
from exabox.core.dbpolicies.TimeBasedTrigger import ebTimeBasedTrigger
from exabox.core.DBStore import ebGetDefaultDB

class ebDBArchivingOperation(ebDbOperation):

    # Archiving only supports time based trigger
    @staticmethod
    def mIsTriggerSupported(aEbDbTrigger):
        return isinstance(aEbDbTrigger, ebTimeBasedTrigger)

    # Archiving is implemented by a DBStore method
    @staticmethod
    def mExecute(aEbDbTrigger, aEbFilters=[]):
        #only one trigger supported, simple logic
        return ebGetDefaultDB().mBackupRequests(aEbDbTrigger.mGetFilterData(),
                                                aEbFilters)