#
# $Header: ecs/exacloud/exabox/proxy/ExacloudInstancePool.py /main/1 2020/10/01 09:08:34 aypaul Exp $
#
# ExacloudInstancePool.py
#
# Copyright (c) 2020, Oracle and/or its affiliates. 
#
#    NAME
#      ExacloudInstancePool.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      06/15/20 - Creation
#
from abc import ABCMeta, abstractmethod

class ECInstancePool(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def insert(self, aObject):
        pass

    @abstractmethod
    def remove(self, aObject):
        pass

    @abstractmethod
    def getNextAvailableElement(self):
        pass

    @abstractmethod
    def getCurrentSizeOfPool(self):
        pass