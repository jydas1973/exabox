"""
 Copyright (c) 2019, 2025, Oracle and/or its affiliates.

NAME:
    cs_constants.py - Create Service stepwise execution constants
FUNCTION:

NOTES:

EXTERNAL INTERFACES: 

History:
    pbellary  08/15/2025 - Enh 38318848 - CREATE ASM CLUSTERS TO SUPPORT VM STORAGE ON EDV OF IMAGE VAULT 
    pbellary  06/14/2024 - ENH 36721696 - IMPLEMENT DELETE SERVICE STEPS FOR EXASCALE SERVICE
    srtata    04/05/2019 - more constants to complete all cs steps
    dekuckre  04/05/2019 - Included DB related steps.
    srtata    03/27/2019 - Creation

"""

# STEPLIST FOR ASM CLUSTERS WITHOUT EDV SUPPORT
class csConstants(object):

        OSTP_VALIDATE_CNF = 1
        OSTP_CREATE_VM    = 2
        OSTP_CREATE_USER  = 3
        OSTP_SETUP_CELL   = 4
        OSTP_CREATE_CELL  = 5
        OSTP_CREATE_GDISK = 6
        OSTP_INSTALL_CLUSTER = 7
        OSTP_INIT_CLUSTER = 8
        OSTP_INSTALL_DB   = 9
        OSTP_RELINK_DB    = 10
        OSTP_CREATE_ASM   = 11
        OSTP_CREATE_DB    = 12
        OSTP_CREATE_PDB   = 13
        OSTP_APPLY_FIX    = 14
        OSTP_INSTALL_EXCHK = 15
        OSTP_CREATE_SUMMARY = 16

        OSTP_PREDB_INSTALL  = 133
        OSTP_POSTDB_INSTALL = 134

        OSTP_DBNID_INSTALL  = 142
        OSTP_APPLY_FIX_NID  = 143
        OSTP_DG_CONFIG      = 144

        OSTP_END_INSTALL    = 255

        VMGI_MODE = 3

# STEPLIST FOR ASM CLUSTERS WITH EDV SUPPORT
class csAsmEDVConstants(object):

        OSTP_VALIDATE_CNF      = 1
        OSTP_CREATE_CELL       = 2
        OSTP_CONFIG_STORAGE    = 3
        OSTP_CONFIG_KVM_HOSTS  = 4
        OSTP_CREATE_VM         = 5
        OSTP_CREATE_USER       = 6
        OSTP_SETUP_CELL        = 7
        OSTP_VERIFY_FABRIC     = 8
        OSTP_CALIBRATE_CELLS   = 9
        OSTP_CREATE_GDISK      = 10
        OSTP_INSTALL_CLUSTER   = 11
        OSTP_INIT_CLUSTER      = 12
        OSTP_CREATE_ASM        = 13
        OSTP_APPLY_FIX         = 14
        OSTP_ATP_HEALTH_FWK    = 15
        OSTP_CREATE_SUMMARY    = 16
        OSTP_RESECURE_MACHINE  = 17

        OSTP_END_INSTALL       = 255

        VMGI_MODE = 3

# STEPLIST FOR EXASCALE CLUSTERS WITH & WITHOUT EDV SUPPORT
class csXSConstants(object):
      OSTP_VALIDATE_CNF      = 1
      OSTP_CREATE_CELL       = 2
      OSTP_CONFIG_STORAGE    = 3
      OSTP_CONFIG_KVM_HOSTS  = 4
      OSTP_CREATE_VM         = 5
      OSTP_CREATE_USER       = 6
      OSTP_SETUP_CELL        = 7
      OSTP_VERIFY_FABRIC     = 8
      OSTP_CALIBRATE_CELLS   = 9
      OSTP_CONFIG_COMPUTE    = 10
      OSTP_INSTALL_CLUSTER   = 11
      OSTP_INIT_CLUSTER      = 12
      OSTP_APPLY_FIX         = 13
      OSTP_ATP_HEALTH_FWK    = 14
      OSTP_CREATE_SUMMARY    = 15
      OSTP_RESECURE_MACHINE  = 16

      OSTP_END_INSTALL       = 255

# STEPLIST FOR EXASCALE Eighth Rack CLUSTERS
class csXSEighthConstants(object):
      OSTP_VALIDATE_CNF      = 1
      OSTP_UPDATE_EIGHTH     = 2
      OSTP_CREATE_CELL       = 3
      OSTP_CONFIG_STORAGE    = 4
      OSTP_CONFIG_KVM_HOSTS  = 5
      OSTP_CREATE_VM         = 6
      OSTP_CREATE_USER       = 7
      OSTP_SETUP_CELL        = 8
      OSTP_VERIFY_FABRIC     = 9
      OSTP_CALIBRATE_CELLS   = 10
      OSTP_CONFIG_COMPUTE    = 11
      OSTP_INSTALL_CLUSTER   = 12
      OSTP_INIT_CLUSTER      = 13
      OSTP_APPLY_FIX         = 14
      OSTP_ATP_HEALTH_FWK    = 15
      OSTP_CREATE_SUMMARY    = 16
      OSTP_RESECURE_MACHINE  = 17

      OSTP_END_INSTALL       = 255

class csBaseDBXSConstants(object):
    OSTP_CREATE_VM    = 3

# STEPLIST FOR ASM Eighth Rack CLUSTERS
class csEighthConstants(object):

    OSTP_VALIDATE_CNF      = 1
    OSTP_UPDATE_EIGHTH     = 2
    OSTP_CREATE_VM         = 3
    OSTP_CREATE_USER       = 4
    OSTP_SETUP_CELL        = 5
    OSTP_VERIFY_FABRIC     = 6
    OSTP_CALIBRATE_CELLS   = 7
    OSTP_CREATE_CELL       = 8
    OSTP_CREATE_GDISK      = 9
    OSTP_INSTALL_CLUSTER   = 10
    OSTP_INIT_CLUSTER      = 11
    OSTP_CREATE_ASM        = 12
    OSTP_APPLY_FIX         = 13
    OSTP_ATP_HEALTH_FWK    = 14
    OSTP_CREATE_SUMMARY    = 15
    OSTP_RESECURE_MACHINE  = 16

    OSTP_END_INSTALL       = 255

# STEPLIST FOR ASM X11M-Z CLUSTERS
class csX11ZConstants(object):

    OSTP_VALIDATE_CNF      = 1
    OSTP_CREATE_VM         = 2
    OSTP_CREATE_USER       = 3
    OSTP_SETUP_CELL        = 4
    OSTP_VERIFY_FABRIC     = 5
    OSTP_CALIBRATE_CELLS   = 6
    OSTP_CREATE_CELL       = 7
    OSTP_CREATE_GDISK      = 8
    OSTP_INSTALL_CLUSTER   = 9
    OSTP_INIT_CLUSTER      = 10
    OSTP_INSTALL_DB        = 11
    OSTP_RELINK_DB         = 12
    OSTP_CREATE_ASM        = 13
    OSTP_CREATE_DB         = 14
    OSTP_CREATE_PDB        = 15
    OSTP_APPLY_FIX         = 16
    OSTP_ATP_HEALTH_FWK    = 17
    OSTP_CREATE_SUMMARY    = 18
    OSTP_RESECURE_MACHINE  = 19

    OSTP_END_INSTALL       = 255