#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/ovm/reconfig/clupreprov_reconfig_factory.py /main/1 2020/10/27 14:21:40 jesandov Exp $
#
# clureconfig_preprov_factory.py
#
# Copyright (c) 2020, Oracle and/or its affiliates. 
#
#    NAME
#      clureconfig_preprov_factory.py
#
#    DESCRIPTION
#      Factory class to generate the preprov, reconfig and rollback classes
#
#    NOTES
#      NONE
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    05/18/20 - Creation
#

from exabox.ovm.reconfig.clupreprov_utils import ebPreprovUtils

from exabox.ovm.reconfig.clureconfig_kvm import ebCluReconfigKvm
from exabox.ovm.reconfig.clureconfig_xen import ebCluReconfigXen

from exabox.ovm.reconfig.clubackup_kvm import ebCluBackupKvm
from exabox.ovm.reconfig.clubackup_xen import ebCluBackupXen

from exabox.ovm.hypervisorutils import getTargetHVIType, HVIT_XEN, HVIT_KVM

class ebCluPreprovReconfigFactory:

    ###############
    # Constructor #
    ###############

    def __init__(self, aClubox):
        self.__clubox = aClubox

    ###################
    # Getters/Setters #
    ###################

    def mGetClubox(self):
        """ getter """
        return self.__clubox

    def mSetClubox(self, aClubox):
        """ setter """
        self.__aClubox = aClubox

    ###################
    # Factory Methods #
    ###################

    def mGetTypeDom0(self):
        """
        Get the type of the enviroment checking by the Dom0

        :return: Flag of KVM, Xen or undefined
        :rtype: int
        """
        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            _type = getTargetHVIType(_dom0)
            return _type
        return None

    def mCreatePreprovUtil(self):
        """
        Get the preprov util object by the factory

        :return: a preprov util object
        :rtype: ebCluPreprovUtils
        """
        return ebPreprovUtils(self.mGetClubox())

    def mCreateReconfig(self):
        """
        Get the preprov util object by the factory

        :return: a reconfig object
        :rtype: ebCluReconfig
        """
        _type = self.mGetTypeDom0()

        if _type == HVIT_XEN:
            _backupTool = ebCluBackupXen(self.mGetClubox())
            return ebCluReconfigXen(self.mGetClubox(), aBackupTool=_backupTool)

        elif _type == HVIT_KVM:
            _backupTool = ebCluBackupKvm(self.mGetClubox())
            return ebCluReconfigKvm(self.mGetClubox(), aBackupTool=_backupTool)

        else:
            raise NotImplementedError("Undefined type of enviroment: {0}".format(_type))

    def mCreateBackupTool(self):
        """
        Get the preprov util object by the factory

        :return: a clubackup object
        :rtype: ebCluBackup
        """
        _type = self.mGetTypeDom0()

        if _type == HVIT_XEN:
            return ebCluBackupXen(self.mGetClubox())

        elif _type == HVIT_KVM:
            return ebCluBackupKvm(self.mGetClubox())

        else:
            raise NotImplementedError("Undefined type of enviroment: {0}".format(_type))

# end of file
