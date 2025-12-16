#
# $Header: ecs/exacloud/exabox/proxy/CustomCircularQueue.py /main/2 2020/11/05 22:21:54 dekuckre Exp $
#
# CircularQueue.py
#
# Copyright (c) 2020, Oracle and/or its affiliates. 
#
#    NAME
#      CircularQueue.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      06/14/20 - Creation
#
from exabox.proxy.ExacloudInstancePool import ECInstancePool

class CustomCircularQueue(ECInstancePool):

    #All entries in the DS will be stored in the tpye string like "hostname:port"
    def __init__(self, maxSize=100):
        self.queue = list()
        self.maxSize = maxSize
        self.nextavailableelement = 0
        self.tail = 0

    def getCurrentSizeOfPool(self):
        return self.tail

    def getList(self):
        return self.queue

    def insert(self, aObject):

        if self.tail == self.maxSize:
            return False
        else:
            self.queue.append(str(aObject))
            self.tail = self.tail + 1
            return True

    def remove(self, aObject):

        if self.tail == 0:
            return False
        else:
            _str_data = str(aObject)
            if _str_data not in self.queue:
                return False
            else:
                _index = self.queue.index(_str_data)
                self.queue.remove(_str_data)
                if (self.tail - 1) == _index:
                    self.nextavailableelement = 0
                self.tail = self.tail - 1
                return True

    def getNextAvailableElement(self):

        if self.tail == 0:
            return None
        else:
            _str_data = str(self.queue[self.nextavailableelement])
            if self.nextavailableelement == (self.tail - 1):
                self.nextavailableelement = 0
            else:
                self.nextavailableelement = self.nextavailableelement + 1
            return _str_data
