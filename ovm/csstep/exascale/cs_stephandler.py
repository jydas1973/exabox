#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/ovm/csstep/exascale/cs_stephandler.py /main/5 2025/08/05 11:43:03 rajsag Exp $
#
# cs_stephandler.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      cs_stephandler - Step Handler File for exascale
#
#    DESCRIPTION
#      Step Handler File for exascale
#
#    NOTES
#      NONE
#
#    MODIFIED   (MM/DD/YY)
#    rajsag      06/30/25 - 37812009 - 24.3.2 exacc exascale : xsconfig fails
#                           on base 1/8th rack due to different steplist
#    jfsaldan    05/12/25 - Bug 37940059 - ECS 24.4.3.1.0 ONE-OFF#3:
#                           EXASCALE:VMBACKUP GOLD BACK FAILED :INVALID STEP
#                           NAME ESTP_BACKUPVM_GOLDIMAGE
#    pbellary    06/21/24 - ENH 36690846 - IMPLEMENT POST-VM STEPS FOR EXASCALE SERVICE
#    pbellary    06/14/24 - ENH 36721696 - IMPLEMENT DELETE SERVICE STEPS FOR EXASCALE SERVICE
#    pbellary    06/06/24 - ENH 36603820 - REFACTOR CREATE SERVICE FLOW FOR ASM/XS/EXADB-XS
#    pbellary    06/06/24 - Creation
#
from exabox.ovm.csstep.cs_prevmchecks import csPreVMChecks
from exabox.ovm.csstep.cs_prevmsetup import csPreVMSetup
from exabox.ovm.csstep.exascale.cs_createvm import csCreateVM
from exabox.ovm.csstep.exascale.cs_postvminstall import csPostVMInstall
from exabox.ovm.csstep.exascale.cs_createuser import csCreateUser
from exabox.ovm.csstep.exascale.cs_createstorage import csCreateStorage
from exabox.ovm.csstep.exascale.cs_configcompute import csConfigCompute
from exabox.ovm.csstep.exascale.cs_installcluster import csInstallCluster
from exabox.ovm.csstep.exascale.cs_postgiinstall import csPostGIInstall
from exabox.ovm.csstep.exascale.cs_exascale_complete import csExaScaleComplete
from exabox.ovm.csstep.cs_golden_backup import csGoldenBackup

exascaleStepFactory = {
    "ESTP_PREVM_CHECKS"      : csPreVMChecks,
    "ESTP_PREVM_SETUP"       : csPreVMSetup,
    "ESTP_CREATE_VM"         : csCreateVM,
    "ESTP_POSTVM_INSTALL"    : csPostVMInstall,
    "ESTP_CREATE_USER"       : csCreateUser,
    "ESTP_CREATE_STORAGE"    : csCreateStorage,
    "ESTP_CONFIG_COMPUTE"    : csConfigCompute,
    "ESTP_INSTALL_CLUSTER"   : csInstallCluster,
    "ESTP_POSTGI_INSTALL"    : csPostGIInstall,
    "ESTP_EXASCALE_COMPLETE" : csExaScaleComplete,
    "ESTP_BACKUPVM_GOLDIMAGE" : csGoldenBackup
}

xsOedaTable  = { '1':['1','Validate Configuration File','udf'],
                '2':['2','Create Cell Disks','udf'],
                '3':['3','Configure Exascale Storage on Cell Servers','udf'],
                '4':['4','Configure Exascale on KVM Hosts','udf'],
                '5':['5','Create Virtual Machine','udf'],
                '6':['6','Create Users','udf'],
                '7':['7','Setup Cell Connectivity','udf'],
                '8':['8','Verify RDMA Network Fabric Connectivity','udf'],
                '9':['9','Calibrate Cells','udf'],
                '10':['10','Configure Exascale on Computes','udf'],
                '11':['11','Install Cluster Software','udf'],
                '12':['12','Initialize Cluster Software','udf'],
                '13':['13','Apply Security Fixes', 'udf'],
                '14':['14','Install Autonomous Health Framework','udf'],
                '15':['15','Create Installation Summary','udf'],
                '16':['16','Resecure Machine','udf']}
                
xsEighthOedaTable  = { '1':['1','Validate Configuration File','udf'],
                '2':['2','Update Nodes for Eighth Rack','udf'],
                '3':['3','Create Cell Disks','udf'],
                '4':['4','Configure Exascale Storage on Cell Servers','udf'],
                '5':['5','Configure Exascale on KVM Hosts','udf'],
                '6':['6','Create Virtual Machine','udf'],
                '7':['7','Create Users','udf'],
                '8':['8','Setup Cell Connectivity','udf'],
                '9':['9','Verify RDMA Network Fabric Connectivity','udf'],
                '10':['10','Calibrate Cells','udf'],
                '11':['11','Configure Exascale on Computes','udf'],
                '12':['12','Install Cluster Software','udf'],
                '13':['13','Initialize Cluster Software','udf'],
                '14':['14','Apply Security Fixes', 'udf'],
                '15':['15','Install Autonomous Health Framework','udf'],
                '16':['16','Create Installation Summary','udf'],
                '17':['17','Resecure Machine','udf']}