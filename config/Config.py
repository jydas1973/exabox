"""
 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    Config - Configuration File Management

FUNCTION:
    Manage configuration file

NOTE:
    None

History:
    aypaul      04/23/2026 - Bug#37535214 Use consistent backup before copying file.
    ririgoye    06/18/2024 - Bug 36746656 - PYTHON 3.11 - EXACLOUD NEEDS TO UPDATE 
                             DEPRECATED/OLDER IMPORTS DYNAMICALLY
    jesandov    02/15/2023 - 36238139: Add options for subarguments in CS and VM_CMD
    ndesanto    02/18/2022 - Fixing issue with get_value_from_exabox_config
                             because an aOptions is expected.
    ndesanto    01/13/2022 - Adding function from DBService.
    ndesanto    08/05/2020 - Fixing open call outside of with block
    dekuckre    03/09/2020 - 30817349: Add capability to block operations
    araghave    20/02/2020 - Enh 30908782 - ksplice configuration on dom0
                             and cells
    dekuckre    11/29/2019 - 30590874: Add chk_vm_timedrift
    sringran    02/12/2020 - 30876901 - EXACLOUD GETS DOWN DUE TO 0BYTE "EXABOX.CONF" 
                             WHEN $EC_HOME MOUNT POINT USAGE BECOMES 100%
    dekuckre    01/02/2020 - 30697759: Add op_cleanup
    hgaldame    10/15/2019 - 30381699 - exacc gen2 sar lock
                             celladmin/cellmonitor accounts on cells
    ndesanto    10/02/2019 - 30374491 - EXACC PYTHON 3 MIGRATION BATCH 01 
    rajsag	    08/13/2019 - ER 30151146: New ECRA/EXACLOUD API to list CPU settings
    araghave    07/02/2019 - ENH 29911293 - POSTCHECK OPTION FOR ALL PATCH 
                             OPERATIONS.
    pbellary    04/04/2019 - bug 29472359: undo stepwise createservice
    srtata      03/22/2019 - bug 29472239: stepwise createservice
    gsundara    11/30/2018 - ER 28864094
    gsundara    10/15/2018 - Bug 28796559
    hgaldame    09/25/2018 - Bug 26353030: Add SSHKEY Fails
    nmallego    08/01/2018 - Bug28434953 - 18.1.7.0.0.180717
    dekuckre    05/25/2018 - 28060479: Add userconfig commands.
    bhuvnkum    04/04/2018 - 27775714: Adding fs option to read xml from filesystem
    dekuckre    02/05/2018 - 27455021: Add capability to resize storage
    hgaldame    10/12/2017 - Support for check oeda ssh keys
    aanverma    09/26/2017 - Bug #26819554: Add Jumbo supported commands
    dekuckre    09/06/17   - 26735879: Add 'clientkeys' as option for listing
                             client keys
    pverma      04/07/2017 - Support for sparse for existing customers
    srtata      10/17/2017 - bug 26984295: add cnssetup
    sdeekshi    08/25/2017 - Bug 26571290: restructure mock code to use existing dispatcher framework
    dekuckre    06/09/2017 - 26187395: Add 'stresstest' option for stress testing
    srtata      01/06/2017 - cns option for healthcheck
    aschital    01/06/2016 - new dataguard options
    hnvenkat	10/09/2015 - new checkcluster option
    mirivier    08/21/2014 - Create file
"""
import argparse
import os
import sys
import json

from exabox.log.LogMgr import ebLogError, ebLogDebug, ebLogInfo, ebLogWarn, ebLogInitialized
from exabox.core.Context import get_gcontext
from exabox.core.Mask import mask, umask, checkifsaltedandb64encoded
from exabox.tools.Utils import mBackupFile
try:
    from collections import OrderedDict
except ImportError:
    from collections.abc import OrderedDict
from typing import Any, Iterable, Optional, TypeVar


__all__ = ['exaBoxProcessArgs', 'exaBoxConfigFileReader', 'ebJsonConfigFileReader']

SENSITIVE_PARAMS = 'oeda_pwd', 'default_pwd', 'root_spwd', 'db_connstr'

def _load_cfgfile(cfgpath, aOptions):
    '''This function load the config file and umask.

    Args:
        cfgpath (str): Path to config file
    '''
    dictConfig = None
    with open(cfgpath) as fd:
        dictConfig = json.load(fd, object_pairs_hook=OrderedDict)
    dictConfigCopyTemp = OrderedDict(dictConfig)
    isConfigToBeChanged = False

    # Enable EC Port only in proxy mode
    if 'proxy_port' in dictConfig and dictConfig['proxy_port']:
        dictConfig['agent_port'] = dictConfig['ec_agent_port']

    isSensitiveParamsSalted = {}
    for param in set(SENSITIVE_PARAMS) & set(dictConfig.keys()):
        isSensitiveParamsSalted[param] = checkifsaltedandb64encoded(dictConfig[param])
        dictConfig[param] = umask(dictConfig[param])

    # Ensure that new sensitive values updated by the user are masked back
    maskedConfig = OrderedDict(dictConfig)
    for param in set(SENSITIVE_PARAMS) & set(dictConfig.keys()):
        maskedValue=mask(maskedConfig[param])
        if (not isSensitiveParamsSalted.get(param, True) and dictConfigCopyTemp[param]!=maskedValue):
            maskedConfig[param] = maskedValue
            isConfigToBeChanged = True

    _options = {}
    if isinstance(aOptions, argparse.Namespace):
        _options = vars(aOptions)
    else:
        _options = aOptions

    aa = maskedConfig["default_pwd"] if "default_pwd" in maskedConfig else "Not present"
    if (isConfigToBeChanged and ('exatest' not in _options or not _options['exatest'])):
        mBackupFile(cfgpath, True)
        if os.access(cfgpath, os.W_OK):
            with open(cfgpath, 'w') as fd:
                json.dump(maskedConfig, fd, indent=4)

    return dictConfig


def get_value_from_exabox_config(aValueName: str, aConfPath: str) -> \
    Optional[Any]:
    try:
        return _load_cfgfile(aConfPath, {'exatest': True})[aValueName]
    except Exception as e:
        ebLogError(f"Exception happened while trying to read from {aConfPath}:"
        f"\n{e}\n")
        raise


def exaBoxConfigFileReader(aOptions):
    """ Read configuration file """

    # HACK: Context is not created at this stage and __basepath is not yet computed.
    bp  = os.path.abspath(sys.argv[0])
    idx = bp.rfind('/exabox')
    if idx == -1:
        # In some condition the logger may not have been initialized
        if not ebLogInitialized():
            print('*** ERROR *** Could not build base path : {0}'.format(bp))
        else:
            ebLogError('Could not build base path : {0}'.format(bp))
        sys.exit(-1)
    _basepath = bp[:idx]

    if aOptions.exaconf:
        if aOptions.exaconf[0] == '/':
            _configpath = aOptions.exaconf
        else:
            _configpath = os.path.join(_basepath, aOptions.exaconf)
    else:
        _configpath = os.path.join(_basepath, 'config', 'exabox.conf')

    if not os.path.exists(_configpath):
        if not ebLogInitialized():
            print('*** ERROR *** ExaBox Config file not found: ' + _configpath)
        else:
            ebLogWarn('ExaBox Config file not found: ' + _configpath)
        return None

    _dictConfig = _load_cfgfile(_configpath, aOptions)

    return _dictConfig


def ebJsonConfigFileReader(aJsonFile):
    _configpath = aJsonFile
    if os.path.exists(_configpath) is True:
        _dictConfig = json.load(open(_configpath))
        return _dictConfig
    else:
        _exa_config = get_gcontext().mGetConfigOptions()
        if _exa_config.get('db_version', '1') == '2':
            from exabox.core.DBStore import ebGetDefaultDB
            _db = ebGetDefaultDB()
            _db_file = _db.mReadFile(_configpath,'ecra_files')
            if _db_file and len(_db_file):
                _dictConfig = json.loads(_db_file)
                return _dictConfig

    if not ebLogInitialized():
        print('*** ERROR *** ExaBox Config file not found: ' + _configpath)
    else:
        ebLogWarn('ExaBox Config file not found: ' + _configpath)

    return None


def ebLoadProgramArguments():
    """
    This function fills the PROGRAM_ARGUMENTS & the CLU_CMDS_OPTIONS
    dictionaries with the information on
    exacloud/config/program_arguments.conf
    """
    _program_args = {}
    with open('config/program_arguments.conf', 'r') as _file:
        _program_args = json.load(_file)

    # CLUCTRL
    _clu_cmds_options = { k: set(v) for k, v in _program_args['clusterctrl']['choices'].items() }
    _program_args['clusterctrl']['choices'] = list(_program_args['clusterctrl']['choices'].keys())

    # VM_CMD
    _vm_cmds_options = { k: set(v) for k, v in _program_args['vmcmd']['choices'].items() }
    _program_args['vmcmd']['choices'] = list(_program_args['vmcmd']['choices'].keys())

    # CS_SUBSTEPS_CMD
    _cs_substeps_cmds_options = { k: set(v) for k, v in _program_args['steplist']['tags'].items() }
    del _program_args["steplist"]["tags"]

    return _program_args, _clu_cmds_options, _vm_cmds_options, _cs_substeps_cmds_options


PROGRAM_ARGUMENTS, CLU_CMDS_OPTIONS, VM_CMDS_OPTIONS, CS_SUBSTEPS_CMDS_OPTIONS = ebLoadProgramArguments()

def ebCluCmdCheckOptions(aCmd, aOptions):
    if aCmd not in CLU_CMDS_OPTIONS:
        return False

    filter_options = CLU_CMDS_OPTIONS[aCmd]
    if get_gcontext().mCheckRegEntry("ENV_EXADBXS") and get_gcontext().mGetRegEntry('ENV_EXADBXS'):
        filter_options = [x.replace("exadbxs:", "").strip() for x in filter_options]
    else:
        filter_options = [x for x in filter_options if "exadbxs:" not in x]

    if get_gcontext().mCheckRegEntry("ENV_EXACC") and get_gcontext().mGetRegEntry('ENV_EXACC'):
        filter_options = [x.replace("exacc:", "").strip() for x in filter_options]
    else:
        filter_options = [x for x in filter_options if "exacc:" not in x]

    return set(aOptions).issubset(set(filter_options))

def ebVmCmdCheckOptions(aCmd, aOptions):
    if aCmd not in VM_CMDS_OPTIONS:
        return False
    return set(aOptions).issubset(VM_CMDS_OPTIONS[aCmd])

def ebCsSubCmdCheckOptions(aCmd, aOptions):
    if aCmd not in CS_SUBSTEPS_CMDS_OPTIONS:
        return False
    return set(aOptions).issubset(CS_SUBSTEPS_CMDS_OPTIONS[aCmd])


def exaBoxProcessArgs(aOptions, aArgs=None):
    """ Parse command line arguments """

    parser = argparse.ArgumentParser()

    for _prog_arg_name, _prog_arg_kw in PROGRAM_ARGUMENTS.items():

        args = ['-' + _prog_arg_kw['shortname']] if 'shortname' in _prog_arg_kw else []
        args.append('--' + _prog_arg_name)

        kwargs = { k: v for k, v in _prog_arg_kw.items() if k != 'shortname' }
        parser.add_argument(*args, **kwargs)

    if not aArgs:
        options = parser.parse_args()
    else:
        options = parser.parse_args(aArgs)

    if not options.agent and options.proxy != 'asproxy':
        options.agent = options.proxy
    if options.proxy == 'switchover':
        if not options.standbyloc:
            parser.error('Proxy switchover command requires --standbyloc arguement to be specified.')
        elif not os.path.exists(options.standbyloc):
            ebLogError("Standby proxy location invalid: "+options.standbyloc)

    return options
