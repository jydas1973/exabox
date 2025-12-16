#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/ovm/csstep/cs_stephandler.py /main/8 2025/11/25 05:03:58 prsshukl Exp $
#
# cs_stephandler.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      cs_stephandler - Step Handler File for ASM/exaDB-XS
#
#    DESCRIPTION
#      Step Handler File for  ASM/exaDB-XS
#
#    NOTES
#      NONE
#
#    MODIFIED   (MM/DD/YY)
#    prsshukl    11/19/25 - Bug 38037088 - Refactor Create Service Flow for
#                           BaseDB
#    pbellary    06/14/24 - ENH 36721696 - IMPLEMENT DELETE SERVICE STEPS FOR EXASCALE SERVICE
#    pbellary    06/06/24 - ENH 36603820 - REFACTOR CREATE SERVICE FLOW FOR ASM/XS/EXADB-XS
#    pbellary    06/06/24 - Creation
#
from exabox.ovm.csstep.cs_prevmchecks import csPreVMChecks
from exabox.ovm.csstep.cs_prevmsetup import csPreVMSetup
from exabox.ovm.csstep.cs_createvm import csCreateVM
from exabox.ovm.csstep.cs_postvminstall import csPostVMInstall
from exabox.ovm.csstep.cs_createuser import csCreateUser
from exabox.ovm.csstep.cs_createstorage import csCreateStorage
from exabox.ovm.csstep.cs_installcluster import csInstallCluster
from exabox.ovm.csstep.cs_postgiinstall import csPostGIInstall
from exabox.ovm.csstep.cs_postginid import csPostGINID
from exabox.ovm.csstep.cs_dbinstall import csDBInstall
from exabox.ovm.csstep.cs_postdbinstall import csPostDBInstall
from exabox.ovm.csstep.cs_exascale_complete import csExaScaleComplete
from exabox.ovm.csstep.cs_postvm_gold_config import csPostVmGoldConfig
from exabox.ovm.csstep.cs_golden_backup import csGoldenBackup

DriverStepFactory = {
    "ESTP_PREVM_CHECKS"       : csPreVMChecks,
    "ESTP_PREVM_SETUP"        : csPreVMSetup,
    "ESTP_CREATE_VM"          : csCreateVM,
    "ESTP_POSTVM_INSTALL"     : csPostVMInstall,
    "ESTP_CREATE_USER"        : csCreateUser,
    "ESTP_CREATE_STORAGE"     : csCreateStorage,
    "ESTP_INSTALL_CLUSTER"    : csInstallCluster,
    "ESTP_POSTGI_INSTALL"     : csPostGIInstall,
    "ESTP_POSTGI_NID"         : csPostGINID,
    "ESTP_DB_INSTALL"         : csDBInstall,
    "ESTP_POSTDB_INSTALL"     : csPostDBInstall,
    "ESTP_EXASCALE_COMPLETE"  : csExaScaleComplete,
    "ESTP_POSTVM_GOLD_CONFIG" : csPostVmGoldConfig,
    "ESTP_BACKUPVM_GOLDIMAGE" : csGoldenBackup
}

csOedaTable = { '1':['1','Validate Configuration File','udf'],
                '2':['2','Create Virtual Machine','udf'],
                '3':['3','Create Users','udf'],
                '4':['4','Setup Cell Connectivity','udf'],
                '5':['5','Create Cell Disks','udf'],
                '6':['6','Create Grid Disks','udf'],
                '7':['7','Install Cluster Software','udf'],
                '8':['8','Initialize Cluster Software','udf'],
                '9':['9','Install Database Software','udf'],
                '10':['10','Relink Database with RDS','udf'],
                '11':['11','Create ASM Diskgroups','udf'],
                '12':['12','Create Databases','udf'],
                '13':['13','Create Pluggable Databases', 'udf'],
                '14':['14','Apply Security Fixes','udf'],
                '15':['15','Install Exachk','udf'],
                '16':['16','Create Installation Summary','udf'],
                '17':['17','Resecure Machine','udf']}

csEDVOedaTable = { '1':['1','Validate Configuration File','udf'],
                   '2':['2','Create Cell Disks','udf'],
                   '3':['3','Configure Exascale Storage on Cell Servers','udf'],
                   '4':['4','Configure Exascale on KVM Hosts','udf'],
                   '5':['5','Create Virtual Machine','udf'],
                   '6':['6','Create Users','udf'],
                   '7':['7','Setup Cell Connectivity','udf'],
                   '8':['8','Verify RDMA Network Fabric Connectivity','udf'],
                   '9':['9','Calibrate Cells','udf'],
                   '10':['10','Create Grid Disks','udf'],
                   '11':['11','Install Cluster Software','udf'],
                   '12':['12','Initialize Cluster Software','udf'],
                   '13':['13','Create ASM Diskgroups','udf'],
                   '14':['14','Apply Security Fixes','udf'],
                   '15':['15','Install Autonomous Health Framework','udf'],
                   '16':['16','Create Installation Summary','udf'],
                   '17':['17','Resecure Machine','udf']}

csEighthOedaTable = { '1':['1','Validate Configuration File','udf'],
                '2':['2','Update Nodes for Eighth Rack','udf'],
                '3':['3','Create Virtual Machine','udf'],
                '4':['4','Create Users','udf'],
                '5':['5','Setup Cell Connectivity','udf'],
                '6':['6','Verify RDMA Network Fabric Connectivity','udf'],
                '7':['7','Calibrate Cells','udf'],
                '8':['8','Create Cell Disks','udf'],
                '9':['9','Create Grid Disks','udf'],
                '10':['10','Install Cluster Software','udf'],
                '11':['11','Initialize Cluster Software','udf'],
                '12':['12','Create ASM Diskgroups','udf'],
                '13':['13','Apply Security Fixes','udf'],
                '14':['14','Install Autonomous Health Framework','udf'],
                '15':['15','Create Installation Summary','udf'],
                '16':['16','Resecure Machine','udf']}

csX11ZOedaTable = { '1':['1','Validate Configuration File','udf'],
                '2':['2','Create Virtual Machine','udf'],
                '3':['3','Create Users','udf'],
                '4':['4','Setup Cell Connectivity','udf'],
                '5':['5','Verify RDMA Network Fabric Connectivity','udf'],
                '6':['6','Calibrate Cells','udf'],
                '7':['7','Create Cell Disks','udf'],
                '8':['8','Create Grid Disks','udf'],
                '9':['9','Install Cluster Software','udf'],
                '10':['10','Initialize Cluster Software','udf'],
                '11':['11','Install Database Software','udf'],
                '12':['12','Relink Database with RDS','udf'],
                '13':['13','Create ASM Diskgroups','udf'],
                '14':['14','Create Databases','udf'],
                '15':['15','Create Pluggable Databases', 'udf'],
                '16':['16','Apply Security Fixes','udf'],
                '17':['17','Install Autonomous Health Framework','udf'],
                '18':['18','Create Installation Summary','udf'],
                '19':['19','Resecure Machine','udf']}