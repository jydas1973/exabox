#!/bin/python
#
# $Header: ecs/exacloud/exabox/exakms/ExaKmsHistory.py /main/1 2022/06/16 21:47:28 aypaul Exp $
#
# ExaKmsHistory.py
#
# Copyright (c) 2022, Oracle and/or its affiliates.
#
#    NAME
#      ExaKmsHistory.py - Base class for exakms entry history 
#
#    DESCRIPTION
#      Interface functions for exakms entry history generation and tracking.
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      06/01/22 - Creation
#
from abc import ABCMeta, abstractmethod
from exabox.exakms.ExaKmsEntry import ExaKmsEntry

class ExaKmsHistory:
    __metaclass__ = ABCMeta

    @abstractmethod
    def mPutExaKmsHistory(self, aKmsEntry: ExaKmsEntry, aOperationType: str) -> None:
        pass

    @abstractmethod
    def mGetExaKmsHistory(self, aUser: str, aHostName: str, aNumEntries: int) -> list:
        pass