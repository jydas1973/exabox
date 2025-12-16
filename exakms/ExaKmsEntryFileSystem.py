#!/bin/python
#
# $Header: ecs/exacloud/exabox/exakms/ExaKmsEntryFileSystem.py /main/4 2023/05/23 13:12:59 jesandov Exp $
#
# ExaKmsEntryFileSystemRSA.py
#
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.
#
#    NAME
#      ExaKmsEntryFileSystemRSA.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    04/27/23 - 35141575: Add support of ECDSA key type
#    jesandov    07/06/22 - Creation
#
from exabox.exakms.ExaKmsEntry import ExaKmsEntry, ExaKmsHostType
from exabox.exakms.ExaKmsEntryRSA import ExaKmsEntryRSA
from exabox.exakms.ExaKmsEntryECDSA import ExaKmsEntryECDSA

class ExaKmsEntryFileSystem(ExaKmsEntry):

    def __init__(self, aFQDN, aUser, aPrivateKey, aHostType=ExaKmsHostType.UNKNOWN):

        self.__privateKey = None
        ExaKmsEntry.__init__(self, aFQDN, aUser, aPrivateKey, aHostType)

    def mGetVersion(self):
        return "ExaKmsEntryFileSystem"

    def mGetPrivateKey(self):
        return self.__privateKey

    def mSetPrivateKey(self, aStr):

        if isinstance(aStr, bytes):
            self.__privateKey = aStr.decode("utf-8")
        else:
            self.__privateKey = aStr

        if self.__privateKey:
            self.mSetPublicKey(self.mCalculatePublicKey())

        if self.__privateKey:
            self.mSetHash(self.mCalculateHash())


#####################
# DERIVATED CLASSES #
#####################

class ExaKmsEntryFileSystemECDSA(ExaKmsEntryECDSA, ExaKmsEntryFileSystem):

    def __init__(self, aFQDN, aUser, aPrivateKey, aHostType=ExaKmsHostType.UNKNOWN):

        self.__privateKey = None
        ExaKmsEntryFileSystem.__init__(self, aFQDN, aUser, aPrivateKey, aHostType)
        ExaKmsEntryECDSA.__init__(self, aFQDN, aUser, aPrivateKey, aHostType)

    def mGetVersion(self):
        return "ExaKmsEntryFileSystemECDSA"

class ExaKmsEntryFileSystemRSA(ExaKmsEntryRSA, ExaKmsEntryFileSystem):

    def __init__(self, aFQDN, aUser, aPrivateKey, aHostType=ExaKmsHostType.UNKNOWN):

        self.__privateKey = None
        ExaKmsEntryFileSystem.__init__(self, aFQDN, aUser, aPrivateKey, aHostType)
        ExaKmsEntryRSA.__init__(self, aFQDN, aUser, aPrivateKey, aHostType)

    def mGetVersion(self):
        return "ExaKmsEntryFileSystemRSA"



# end of file
