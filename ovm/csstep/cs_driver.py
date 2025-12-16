"""
 Copyright (c) 2019, 2025, Oracle and/or its affiliates.

NAME:
    cs_driver.py - Create Service Step Wise Execution

FUNCTION:
    Implements driver for create service execution 
    using steplist as an input

NOTES:
    Invoked from exaBoxCluCtrl

EXTERNAL INTERFACES: 
    csDriver: handleRequest()

History:
    prsshukl  11/19/2025 - Bug 38037088 - Refactor Create Service Flow for BaseDB
    pbellary  06/14/2024 - ENH 36721696 - IMPLEMENT DELETE SERVICE STEPS FOR EXASCALE SERVICE
    pbellary  06/10/2024 - ENH 36690543 - EXACLOUD: PATCH XML WITH EXASCALE INFORMATION FOR INFO COMMAND
    pbellary  06/06/2024 - ENH 36603820 - REFACTOR CREATE SERVICE FLOW FOR ASM/XS/EXADB-XS
    aararora  03/11/2024 - Bug 36369329: Catch any exceptions when logging profiling data
    joserran  08/06/2021 - Bug 32614102 - Adding Remote Lock heartbeat mechanism
    dekuckre  05/18/2020 - 31326778: Update undo step 7 and 6.
    srtata    04/19/2019 - bug 29556301: rename dbinstall steps
    pbellary  04/17/2019 - bug 29472359: undo stepwise createservice
    srtata    03/05/2019 - Creation

"""
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogVerbose
from exabox.ovm.clumisc import ebCluPreChecks
from exabox.ovm.csstep.cs_stephandler import DriverStepFactory, csOedaTable, csEDVOedaTable, csX11ZOedaTable, csEighthOedaTable
from exabox.ovm.csstep.exascale.cs_stephandler import exascaleStepFactory, xsOedaTable, xsEighthOedaTable
from exabox.ovm.csstep.exabasedb.cs_stephandler import BaseDBStepFactory, csBaseDBOedaTable
from exabox.ovm.csstep.cs_util import csUtil
from exabox.tools.profiling.profiler import measure_exec_time, flush_profiled_data
from exabox.tools.profiling.stepwise import log_profiled_data, steal_steplist

# this class implements the create service step wise execution
# driver which calls doExecute() and undoExecute() functions
# of the appropriate classes based on the steplist passed
class csDriver(object):

    def __init__(self, aExaBoxCluCtrlObj, aOptions):
        ebLogInfo('csDriver: Entering init')
        self.__eboxobj = aExaBoxCluCtrlObj
        self.__aOptions = aOptions
        self.__steplist = []
        if aOptions.steplist :
            ebLogInfo('csDriver: aOptions.steplist='+str(aOptions.steplist))
            optionStr= str(aOptions.steplist)
            self.__steplist = optionStr.split(",")

        self.__driver = CSDriverFactory()
        ebLogInfo('csDriver: Completed init Successfully')

    def mGetStorageType(self):
        _ebox = self.__eboxobj
        _storageType = None

        if _ebox.mIsXS() and not _ebox.mIsExaScale():
            #StorageType is XS for exascale service 
            _storageType = "XS"
        elif _ebox.isBaseDB() or _ebox.isExacomputeVM():
            #This is just a placeholder value to redirect flow to BaseDB steps
            _storageType = "BASEDB"
        else:
            #StorageType is None for ASM/exaDB-XS
            _storageType = None

        return _storageType

    def mGetOedaTable(self):
        _ebox = self.__eboxobj
        _options = self.__aOptions
        _utils = _ebox.mGetExascaleUtils()
        _oeda_step_table = None

        if _ebox.mIsXS():
            if _utils.mGetRackSize() == 'eighthrack':
                _oeda_step_table = xsEighthOedaTable
            else:
                _oeda_step_table = xsOedaTable
        elif _ebox.isBaseDB() or _ebox.isExacomputeVM():
            _oeda_step_table = csBaseDBOedaTable
        elif _options and _utils.mIsEDVImageSupported(_options):
            _oeda_step_table = csEDVOedaTable
        elif _utils.mGetRackSize() == 'eighthrack':
            _oeda_step_table = csEighthOedaTable
        elif _utils.mGetRackSize() == 'zrack':
            _oeda_step_table = csX11ZOedaTable
        else:
            _oeda_step_table = csOedaTable
        return _oeda_step_table

    def validateStepList(self, aStorageType):
        _storageType = aStorageType
        ebLogInfo('csDriver: Entering validateStepList')
        if _storageType == "XS":
            _stepFactory = exascaleStepFactory
        elif _storageType == "BASEDB":
            _stepFactory = BaseDBStepFactory
        else:
            _stepFactory = DriverStepFactory
        for step in self.__steplist:
           if step not in _stepFactory:
               ebLogError('*** Invalid Step Name {} **** '.format(step))
               raise ExacloudRuntimeError(0x0781, 0xA, 'createservice stepwise execution: Invalid step {}'.format(step), aStackTrace=False)
        ebLogInfo('csDriver: Completed validateStepList Successfully') 

    def handleRequest(self):
        #The step list is already printed in init function
        ebLogInfo('csDriver: Entering stepwise execution handleRequest')
        _ebox = self.__eboxobj
        _cmd = _ebox.mGetCmd()
        _options = self.__aOptions
        _step_list = []
        _rc = 0

        _storageType = self.mGetStorageType()
        self.validateStepList(_storageType)
        _csu = csUtil()
        _csu.mUpdateOEDAConfiguration(_ebox, _options)
        _undo = _options.undo if 'undo' in _options else False

        flush_profiled_data()
        for step in self.__steplist:
            _step_list.append(step)
        _rc = self.mHandleStep(_step_list, _undo)

        ebLogInfo('csDriver: Completed stepwise execution handleRequest Successfully')
        try:
            log_profiled_data(self.__steplist, _ebox.mFetchOedaString)
        except Exception as ex:
            # Issues in logging profiling data should not hamper the functionality.
            # So, just log a warning and continue.
            ebLogWarn(f"Could not log profiling data due to an error. Error: {ex}.")
        return 0
    
    @measure_exec_time(steal_steplist)
    def mHandleStep(self, aStepList, aUndo):
        _ebox = self.__eboxobj
        _options = self.__aOptions
        _undo = aUndo
        _step_list = aStepList
        _rc = 0

        _storageType = self.mGetStorageType()
        for _step in _step_list:

            ebLogInfo('csDriver: Executing step='+ _step)
            #lookup the dictionary to get appropriate class
            _stepHandle = self.__driver.getCSHandle(_step, _storageType)

            #__steplist is passed so that each step can call mUpdateStatusOEDA
            # in order to update request on what percentage is completed

            if not _stepHandle is None:
                if _undo == False or _undo == 'False':
                    _rc = _stepHandle.doExecute(_ebox, _options, _step_list)
                else:
                    _rc = _stepHandle.undoExecute(_ebox, _options, _step_list)

        return _rc

class CSDriverFactory(object):
    def getCSHandle(self, aStep, aStorageType):
        _step = aStep
        _storageType = aStorageType
        _stepHandler = None
        try:
            if _storageType and _storageType.upper() == "XS":
                ebLogInfo("Invoking exascale Step Factory.")
                _stepHandler = exascaleStepFactory[_step]()
            elif _storageType and _storageType.upper() == "BASEDB":
                ebLogInfo("Invoking BaseDB Step Factory.")
                _stepHandler = BaseDBStepFactory[_step]()
            else:
                ebLogInfo("Invoking ASM|exaDB-XS Step Factory.")
                _stepHandler = DriverStepFactory[_step]()
        except Exception as e:
            ebLogError(f"*** Failed to fetch step handler, ERROR: {e}")
        return _stepHandler
