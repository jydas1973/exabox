"""
 Copyright (c) 2014, 2024, Oracle and/or its affiliates.

NAME:
    hcconstants.py - Refactored from cluhealth to contain all constant strings

FUNCTION:
    define HCConstants and enum for common usage.

NOTE:
    None

History:
    bhuvnkum    02/19/2018 - Creation

"""

# Return codes
SUCCESS_CODE = 0
FAIL_CODE    = 1

class LOG_TYPE(object):
    VERBOSE = 0
    DEBUG = 1
    INFO = 2
    RECOMMEND = 3
    WARNING = 4
    ERROR = 5
    CRITICAL = 6

    @classmethod
    def reverse_mapping(self, value):
        for member in list(vars(self).items()):
            if member[1] == value:
                return member[0]
        return None

class CHK_RESULT(object):
    PASS = 0
    FAIL = 1

    @classmethod
    def reverse_mapping(self, value):
        for member in list(vars(self).items()):
            if member[1] == value:
                return member[0]
        return None


class HcConstants(object):
    """
    Class contains will store all literals used in check parser, profile parser, checkexecutor and healthcheck operations
    """
    
    VERSION             =   "hcVersion"
    TARGET_LIST         =   "hcTargetList"
    TAG_LIST            =   "hcTagList"
    CHECK_LIST          =   "hcCheckList"
    REFERENCE           =   "hcReference"
    CHECK_PARAM         =   "hcCheckParam"
    COMMENTS            =   "hcComments"
    ALERT_LEVEL         =   "hcAlertLevel"
    HCCONF              =   "hcConf"
    
    CHK_NAME            =   "chkName"
    CHK_DESC            =   "chkDesc"
    CHK_TARGET          =   "chkTarget"
    CHK_TAGS            =   "chkTags"
    CHK_REF             =   "chkRef"
    CHK_ALERT_LEVEL     =   "chkAlertLevel"
    
    PROFILE_NAME        =   "hcProfileName"
    RESULT_LEVEL        =   "hcResultLevel"
    FUNCTION_LIST       =   "hcFunctionList"
    
    #profile strings
    PROFILE_TARGET      =   "target"
    PROFILE_TAGS        =   "tags"
    PROFILE_INCLUDE     =   "include"
    PROFILE_EXCLUDE     =   "exclude"
    PROFILE_CHK_NAMES   =   "names"
    PROFILE_CHK_IDS     =   "ids"
    PROFILE_ALERT_LEVEL =   "alertlevel"
    
    PROFILE_CUSTOM_CHK  =   "hcCustomCheck"
    # existing cluhealth strings

    CONNECTION          =   "connection"
    XML                 =   "xml"
    CONF                =   "conf"
    PREPROV             =   "PREPROV"
    EXACHK              =   "exachk"
    STRESS_TEST         =   "stresstest"

    #target type
    DOM0                =   "dom0"
    DOMU                =   "domu"
    CELL                =   "cell"
    SWITCH              =   "switch"
    CONTROLPLANE        =   "controlplane"
    COMPOSITE           =   "composite"
    CUSTOMCHECK         =   "customcheck"
    ALL                 =   "all"
    
    
    #check result
    RES_STARTTIME       =   "hcExecStartTimestamp"
    RES_ENDTIME         =   "hcExecEndTimestamp"
    RES_HCID            =   "hcID"
    RES_PROFILE         =   "hcProfile"             
    RES_CHKNAME         =   "hcName"
    RES_NODETYPE        =   "hcNodeType"            
    RES_NODENAME        =   "hcNodeName"            
    RES_ALERTTYPE       =   "hcAlertType"           
    RES_RESULT          =   "hcTestResult"          
    RES_LOG             =   "hcLogs"                
    RES_MSGDETAIL       =   "hcMsgDetail"           
    RES_CHECKPARAM      =   "hcCheckParam"         
    RES_DISPLAYSTRING   =   "hcDisplayString"
    RES_CUSTOMERTAG     =   "chkCustomerDisplayTag"
    RES_NODESUMMARY     =   "nodeSummary"

    # networks
    CLIENT              =   "client"
    BACKUP              =   "backup"
    DR                  =   "dr"
    
    
gHealthcheckError = {
    '0'  : ['No error'],
    '111': ['Missing input JSON object'],
    '902': ['Failed to ping domU'],
    '903': ['Failed to connect to domU'],
    '904': ['Error running dbaasapi on target domU'],
    '911': ['Invalid master check list json'],
    '912': ['Invalid check profile json']
}


gCheckNameFunctionMap = {
    "NetworkChecks"         :   "HealthCheck.mPreProvNetworkChecks",
    "NetIfsTest"            :   "HealthCheck.mCheckNetIfs",
    "SystemChecks"          :   "HealthCheck.mPreProvSystemChecks",
    "NodeSpace"             :   "HealthCheck.mCheckNodeSpace",
    "MemCheck"              :   "HealthCheck.mCheckMemory",
    "GridInfraCheck"        :   "HealthCheck.mCheckGridInfra",
    "ScanStatusCheck"       :   "HealthCheck.mCheckScanStatus",
    "SCANCluvfyCheck"       :   "HealthCheck.mCheckSCANCluvfy",
    "VipStatusCheck"        :   "HealthCheck.mCheckVipStatus",
    "CDBStatusCheck"        :   "HealthCheck.mCheckCDBStatus",
    "CellDeactivation"      :   "HealthCheck.mCheckCellDeactivation",
    "AsmOperation"          :   "HealthCheck.mCheckAsmOperation",
    "AsmMode"               :   "HealthCheck.mCheckAsmMode",
    "ImageVersion"          :   "HealthCheck.mCheckImageVersion",
    "RootPartitionSpace"    :   "HealthCheck.mCheckRootSpace",
    "ValidateXml"           :   "HealthCheck.mValidateXML",
    "AsmPowerLimit"         :   "HealthCheck.mCheckAsmPowerLimit",
    "ExaVmImagesSpace"      :   "HealthCheck.mCheckEXAVMIMAGESSpace",
    "DomUList"              :   "HealthCheck.mCheckDomUList",
    "DomUUptime"            :   "HealthCheck.mCheckDomUUptime",
    "XenInfo"               :   "HealthCheck.mCheckXenInfo",
    "XenLog"                :   "HealthCheck.mCheckXenLog",
    "Dom0MemInfo"           :   "HealthCheck.mCheckDom0MemInfo",
    "CellOSConf"            :   "HealthCheck.mCheckCellOSConf",
    "BrctlShow"             :   "HealthCheck.mCheckBrctlShow",
    "Ifconfig"              :   "HealthCheck.mCheckIfconfig",
    "Route"                 :   "HealthCheck.mCheckRoute",
    "CellFlashLog"          :   "HealthCheck.mCheckCellFlashLog",
    "CellFlashCache"        :   "HealthCheck.mCheckCellFlashCache",
    "CellGridDisk"          :   "HealthCheck.mCheckCellGridDisk",
    "CellPhysicalDisk"      :   "HealthCheck.mCheckCellPhysicalDisk",
    "CellAlertHistory"      :   "HealthCheck.mCheckCellAlertHistory",
    "CellDetail"            :   "HealthCheck.mCheckCellDetail",
    "CellDatabase"          :   "HealthCheck.mCheckCellDatabase",
    "IORMPlan"              :   "HealthCheck.mCheckIORMPlan",
    "CellosTgz"             :   "HealthCheck.mCheckCellosTgz",
    "Ipconfpl"              :   "HealthCheck.mCheckIpconfpl",
    "SundiagOsw"            :   "HealthCheck.mCheckSundiagOsw",
    "Ebtables"              :   "HealthCheck.mCheckEbtables",
    "Iptables"              :   "HealthCheck.mCheckIptables",
    "IpAddrShow"            :   "HealthCheck.mCheckIpAddrShow",
    "Ibstat"                :   "HealthCheck.mCheckIbstat",
    "Dom0XenLogs"           :   "HealthCheck.mCheckDom0XenLogs",
    "AllCellosLogs"         :   "HealthCheck.mCheckAllCellosLogs",
    "VarLogMessages"        :   "HealthCheck.mCheckVarLogMessages",
    "NetworkDom0PreChecks"  :   "ebCluPreChecks.mNetworkDom0PreChecks",
    "NetworkBasicChecks"    :   "ebCluPreChecks.mNetworkBasicChecks",
    "ConnectivityChecks"    :   "ebCluPreChecks.mConnectivityChecks",
    "VMPreChecks"           :   "ebCluPreChecks.mVMPreChecks",
    "CPSVersion"            :   "HealthCheck.mCPSVersion",
    "ListEXAVMIMAGESContents"     :   "HealthCheck.mCheckListEXAVMIMAGESContents"
    }

gCreateServiceStepIncidentTestsMap = {
    "ESTP_PREVM_CHECKS"     : [[["PingTest","SshTest","ExaVmImagesSpace","Dom0MemInfo","CellOSConf","Ebtables","Iptables","BrctlShow","Ifconfig","Route","CellFlashLog","CellFlashCache","CellGridDisk","CellPhysicalDisk","CellAlertHistory","CellDetail","CellDatabase","IORMPlan","ListEXAVMIMAGESContents"],["dom0","cell"]],[["PingTest","SshTest","ExaVmImagesSpace","Dom0MemInfo","CellOSConf","Ebtables","Iptables","BrctlShow","Ifconfig","Route","CellFlashLog","CellFlashCache","CellGridDisk","CellPhysicalDisk","CellAlertHistory","CellDetail","CellDatabase","IORMPlan","ListEXAVMIMAGESContents"],["dom0","cell"]]],
    "ESTP_PREVM_SETUP"      : [[["PingTest","SshTest","ExaVmImagesSpace","Dom0MemInfo","CellOSConf","Ebtables","Iptables","BrctlShow","Ifconfig","Route","CellFlashLog","CellFlashCache","CellGridDisk","CellPhysicalDisk","CellAlertHistory","CellDetail","CellDatabase","IORMPlan","ListEXAVMIMAGESContents"],["dom0","cell"]],[["PingTest","SshTest","ExaVmImagesSpace","Dom0MemInfo","CellOSConf","Ebtables","Iptables","BrctlShow","Ifconfig","Route","CellFlashLog","CellFlashCache","CellGridDisk","CellPhysicalDisk","CellAlertHistory","CellDetail","CellDatabase","IORMPlan","ListEXAVMIMAGESContents"],["dom0","cell"]]],
    "ESTP_CREATE_VM"        : [[["PingTest","SshTest","ExaVmImagesSpace","Dom0MemInfo","CellOSConf","Ebtables","Iptables","BrctlShow","Ifconfig","Route","CellFlashLog","CellFlashCache","CellGridDisk","CellPhysicalDisk","CellAlertHistory","CellDetail","CellDatabase","IORMPlan","ListEXAVMIMAGESContents"],["dom0","cell"]],[["PingTest","SshTest","ExaVmImagesSpace","Dom0MemInfo","CellOSConf","Ebtables","Iptables","BrctlShow","Ifconfig","Route","CellFlashLog","CellFlashCache","CellGridDisk","CellPhysicalDisk","CellAlertHistory","CellDetail","CellDatabase","IORMPlan","ListEXAVMIMAGESContents"],["dom0","cell"]]],
    "ESTP_POSTVM_INSTALL"   : [[["PingTest","SshTest","ExaVmImagesSpace","Dom0MemInfo","CellOSConf","CellFlashLog","CellFlashCache","CellGridDisk","CellPhysicalDisk","CellAlertHistory","CellDetail","CellDatabase","IORMPlan","ListEXAVMIMAGESContents"],["dom0","cell","domu"]],[["PingTest","SshTest","ExaVmImagesSpace","Dom0MemInfo","CellOSConf","CellFlashLog","CellFlashCache","CellGridDisk","CellPhysicalDisk","CellAlertHistory","CellDetail","CellDatabase","IORMPlan","ListEXAVMIMAGESContents"],["dom0","cell","domu"]]],
    "ESTP_CREATE_USER"      : [[["PingTest","SshTest","ExaVmImagesSpace","Dom0MemInfo","CellOSConf","CellFlashLog","CellFlashCache","CellGridDisk","CellPhysicalDisk","CellAlertHistory","CellDetail","CellDatabase","IORMPlan","AsmOperation","AsmMode","AsmPowerLimit","ListEXAVMIMAGESContents"],["dom0","cell","domu"]],[["PingTest","SshTest","ExaVmImagesSpace","Dom0MemInfo","CellOSConf","CellFlashLog","CellFlashCache","CellGridDisk","CellPhysicalDisk","CellAlertHistory","CellDetail","CellDatabase","IORMPlan","AsmOperation","AsmMode","AsmPowerLimit","ListEXAVMIMAGESContents"],["dom0","cell","domu"]]],
    "ESTP_CREATE_STORAGE"   : [[["PingTest","SshTest","ExaVmImagesSpace","Dom0MemInfo","CellOSConf","CellFlashLog","CellFlashCache","CellGridDisk","CellPhysicalDisk","CellAlertHistory","CellDetail","CellDatabase","IORMPlan","AsmOperation","AsmMode","AsmPowerLimit","ListEXAVMIMAGESContents"],["dom0","cell","domu"]],[["PingTest","SshTest","ExaVmImagesSpace","Dom0MemInfo","CellOSConf","CellFlashLog","CellFlashCache","CellGridDisk","CellPhysicalDisk","CellAlertHistory","CellDetail","CellDatabase","IORMPlan","AsmOperation","AsmMode","AsmPowerLimit","ListEXAVMIMAGESContents"],["dom0","cell","domu"]]],
    "ESTP_INSTALL_CLUSTER"  : [[["PingTest","SshTest","ExaVmImagesSpace","Dom0MemInfo","CellOSConf","CellFlashLog","CellFlashCache","CellGridDisk","CellPhysicalDisk","CellAlertHistory","CellDetail","CellDatabase","IORMPlan","AsmOperation","AsmMode","AsmPowerLimit","ListEXAVMIMAGESContents"],["dom0","cell","domu"]],[["PingTest","SshTest","ExaVmImagesSpace","Dom0MemInfo","CellOSConf","CellFlashLog","CellFlashCache","CellGridDisk","CellPhysicalDisk","CellAlertHistory","CellDetail","CellDatabase","IORMPlan","AsmOperation","AsmMode","AsmPowerLimit","ListEXAVMIMAGESContents"],["dom0","cell","domu"]]],
    "ESTP_POSTGI_INSTALL"   : [[["PingTest","SshTest","ExaVmImagesSpace","Dom0MemInfo","CellOSConf","CellFlashLog","CellFlashCache","CellGridDisk","CellPhysicalDisk","CellAlertHistory","CellDetail","CellDatabase","IORMPlan","AsmOperation","AsmMode","AsmPowerLimit","ListEXAVMIMAGESContents"],["dom0","cell","domu"]],[["PingTest","SshTest","ExaVmImagesSpace","Dom0MemInfo","CellOSConf","CellFlashLog","CellFlashCache","CellGridDisk","CellPhysicalDisk","CellAlertHistory","CellDetail","CellDatabase","IORMPlan","AsmOperation","AsmMode","AsmPowerLimit","ListEXAVMIMAGESContents"],["dom0","cell","domu"]]],
    "ESTP_POSTGI_NID"       : [[["PingTest","SshTest","ExaVmImagesSpace","Dom0MemInfo","CellOSConf","CellFlashLog","CellFlashCache","CellGridDisk","CellPhysicalDisk","CellAlertHistory","CellDetail","CellDatabase","IORMPlan","AsmOperation","AsmMode","AsmPowerLimit","ListEXAVMIMAGESContents"],["dom0","cell","domu"]],[["PingTest","SshTest","ExaVmImagesSpace","Dom0MemInfo","CellOSConf","CellFlashLog","CellFlashCache","CellGridDisk","CellPhysicalDisk","CellAlertHistory","CellDetail","CellDatabase","IORMPlan","AsmOperation","AsmMode","AsmPowerLimit","ListEXAVMIMAGESContents"],["dom0","cell","domu"]]],
    "ESTP_DB_INSTALL"       : [[["PingTest","SshTest","ExaVmImagesSpace","Dom0MemInfo","CellOSConf","CellFlashLog","CellFlashCache","CellGridDisk","CellPhysicalDisk","CellAlertHistory","CellDetail","CellDatabase","IORMPlan","AsmOperation","AsmMode","AsmPowerLimit","VarLogMessages","ListEXAVMIMAGESContents"],["dom0","cell","domu"]],[["PingTest","SshTest","ExaVmImagesSpace","Dom0MemInfo","CellOSConf","CellFlashLog","CellFlashCache","CellGridDisk","CellPhysicalDisk","CellAlertHistory","CellDetail","CellDatabase","IORMPlan","AsmOperation","AsmMode","AsmPowerLimit","VarLogMessages","ListEXAVMIMAGESContents"],["dom0","cell","domu"]]],
    "ESTP_POSTDB_INSTALL"   : [[["PingTest","SshTest","ExaVmImagesSpace","Dom0MemInfo","CellOSConf","CellFlashLog","CellFlashCache","CellGridDisk","CellPhysicalDisk","CellAlertHistory","CellDetail","CellDatabase","IORMPlan","AsmOperation","AsmMode","AsmPowerLimit","VarLogMessages","ListEXAVMIMAGESContents"],["dom0","cell","domu"]],[["PingTest","SshTest","ExaVmImagesSpace","Dom0MemInfo","CellOSConf","CellFlashLog","CellFlashCache","CellGridDisk","CellPhysicalDisk","CellAlertHistory","CellDetail","CellDatabase","IORMPlan","AsmOperation","AsmMode","AsmPowerLimit","VarLogMessages","ListEXAVMIMAGESContents"],["dom0","cell","domu"]]]
}

gCreateServiceMapDO = 0
gCreateServiceMapUNDO = 1

gCheckList = []
