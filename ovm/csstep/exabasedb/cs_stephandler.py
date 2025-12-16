#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/csstep/exabasedb/cs_stephandler.py /main/1 2025/11/25 05:03:58 prsshukl Exp $
#
# cs_stephandler.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      cs_stephandler.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    prsshukl    11/19/25 - Creation
#

from exabox.ovm.csstep.exabasedb.cs_prevmchecks import csPreVMChecks
from exabox.ovm.csstep.exabasedb.cs_prevmsetup import csPreVMSetup
from exabox.ovm.csstep.exabasedb.cs_createvm import csCreateVM
from exabox.ovm.csstep.exabasedb.cs_postvminstall import csPostVMInstall
from exabox.ovm.csstep.exabasedb.cs_createuser import csCreateUser
from exabox.ovm.csstep.exabasedb.cs_exascale_complete import csExaScaleComplete

BaseDBStepFactory = {
    "ESTP_PREVM_CHECKS"       : csPreVMChecks,
    "ESTP_PREVM_SETUP"        : csPreVMSetup,
    "ESTP_CREATE_VM"          : csCreateVM,
    "ESTP_POSTVM_INSTALL"     : csPostVMInstall,
    "ESTP_CREATE_USER"        : csCreateUser,
    "ESTP_EXASCALE_COMPLETE"  : csExaScaleComplete
}

csBaseDBOedaTable = { '1':['1','Create Cell Disks','udf'],
                '2':['2','Configure Exascale Storage on Cell Servers','udf'],
                '3':['3','Create BaseDB Virtual Machines','udf'],
                '4':['4','Configure Exascale on Computes','udf'],
                '5':['5','Install Database Software','udf'],
                '6':['6','Create Databases','udf'],
                '7':['7','Create Pluggable Databases','udf'],
                '8':['8','Create Installation Summary','udf']}
