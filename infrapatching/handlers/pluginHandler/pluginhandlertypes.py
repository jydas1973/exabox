#
# $Header: ecs/exacloud/exabox/infrapatching/handlers/pluginHandler/pluginhandlertypes.py /main/11 2025/03/28 04:20:31 araghave Exp $
#
# pluginhandlertypes.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
#
#    NAME
#      pluginhandlertypes.py - This module contains main handler class for plugin management.
#
#    DESCRIPTION
#      This module contains main handler class for plugin management.
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    araghave    03/22/25 - Bug 37739736 - ENABLE METADATA BASED EXACLOUD CELL
#                           PLUGIN DURING CELL MONTHLY PATCHING
#    araghave    02/04/25 - Enh 34479463 - PROVIDE EXACLOUD REGISTRATION AND
#                           PLUGIN SUPPORT FOR CELLS
#    araghave    08/27/24 - Enh 36829406 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE CORE, PLUGIN AND TASKHANDLER
#                           FILES
#    araghave    07/15/24 - Enh 36830077 - CLEANUP KSPLICE CODE FROM
#                           INFRAPATCHING FILES
#    araghave    03/13/24 - Enh 36270822 - EXECUTION OF EXACLOUD PLUGINS USING
#                           INFRA PATCHING PLUGIN METADATA
#    araghave    02/28/24 - Enh 36295801 - IMPLEMENT ONEOFFV2 PLUGIN EXACLOUD
#                           CHANGES
#    jyotdas     02/05/24 - ER 36108549 - adbd dom0domu plugins should be
#                           enabled in case user specified dom0 plugin type
#    jyotdas     04/17/23 - ENH 35106082 - By default run dom0domu plugin on
#                           autonomous vms
#    sdevasek    09/30/21 - ENH 33400429 - CLEAN UP OF MODIFY AT PREREQ FROM
#                           ADDITIONAL OPTIONS
#    nmallego    08/28/20 - Refactor infra patching code
#    nmallego    08/28/20 - Creation
#

from exabox.infrapatching.handlers.pluginHandler.exacloudpluginhandler import ExacloudPluginHandler
from exabox.infrapatching.handlers.pluginHandler.oneoffpluginhandler import OneOffPluginHandler
from exabox.infrapatching.handlers.pluginHandler.oneoffv2pluginhandler import OneOffV2PluginHandler
from exabox.infrapatching.utils.constants import TASK_ONEOFF, PATCH_DOM0, PATCH_DOMU, TASK_ONEOFFV2, TASK_PATCH, TASK_ROLLBACK, PATCH_CELL
from exabox.log.LogMgr import ebLogInfo, ebLogError
from exabox.infrapatching.utils.utility import checkPluginEnabledFromInfraPatchMetadata

def mGetPluginHandlerType(*initial_data, **kwargs):
    _pluginHandler = None
    _oneoff_plugin_enabled = False
    _exacloud_plugin_enabled = False
    _dbnu_plugin_enabled = False
    _oneoffv2_plugin_enabled = False
    _plugin_types = None
    _additional_options = []
    _target_types = []
    #Plugin parameters: "EnablePlugins": "yes" and "PluginTypes": "dom0+dom0domu",
    _enable_plugin_param = None
    _plugin_type_param = None
    _operation_param = None
    _plugin_types = None
    _autonomous_db_flag = None

    for dictionary in initial_data:
        if 'EnablePlugins' in dictionary.keys():
            _enable_plugin_param = dictionary.get('EnablePlugins')
            if _enable_plugin_param and _enable_plugin_param.lower() == 'yes':
                _exacloud_plugin_enabled = True
        if 'PluginTypes' in dictionary.keys():
            _plugin_types = dictionary.get('PluginTypes')
        if 'TargetType' in dictionary.keys():
            _target_types = dictionary.get('TargetType')
        if 'Operation' in dictionary.keys():
            _operation_param = dictionary.get('Operation')
            _additional_option = dictionary.get('AdditionalOptions')
            _is_exasplice = False
            if _additional_option and 'exasplice' in _additional_option[0] and _additional_option[0]['exasplice']:
                if _additional_option[0]['exasplice'].lower() == 'yes':
                    _is_exasplice = True
            if _operation_param == TASK_ONEOFF:
                _oneoff_plugin_enabled = True
            elif _operation_param in [ TASK_ONEOFFV2 ]:
                _oneoffv2_plugin_enabled = True
            elif not _exacloud_plugin_enabled and _operation_param in [ TASK_PATCH ] and 'InfraPatchPluginMetaData' in dictionary.keys():
                _pluginsMetadata = []
                _exacloud_plugin_enabled, _dbnu_plugin_enabled = False, False
                '''
                 Exacloud plugin must be disabled only during Dom0 Exasplice
                 patching
                '''
                if _is_exasplice and _target_types[0] == PATCH_DOM0:
                    ebLogInfo("Plugin execution is not applicable for DOM0 targets during SMR patching.")
                else:
                    _pluginsMetadata = dictionary.get('InfraPatchPluginMetaData')
                    if len(_pluginsMetadata) > 0:
                        _exacloud_plugin_enabled, _ = checkPluginEnabledFromInfraPatchMetadata(_pluginsMetadata)
                    if _exacloud_plugin_enabled:
                        ebLogInfo("Plugin metadata was found in the input json and exacloud plugins will be run implicitly.")
                    if _dbnu_plugin_enabled:
                        ebLogInfo("Plugin metadata was found in the input json and dbnu plugins will be run implicitly.")

        if 'AdditionalOptions' in dictionary.keys():
            _additional_options = dictionary.get('AdditionalOptions')

    if _exacloud_plugin_enabled:
        if any(_ttype in _target_types for _ttype in (PATCH_DOM0, PATCH_DOMU, PATCH_CELL)):
            _pluginHandler = ExacloudPluginHandler(*initial_data, **kwargs)
            ebLogInfo("Initialized ExacloudPluginHandler")
            return _pluginHandler
        else:
            raise Exception(f'Exacloud Plugin is not applicable for the following targets {_target_types}')

    if _oneoff_plugin_enabled:
        _pluginHandler = OneOffPluginHandler(*initial_data, **kwargs)
        ebLogInfo("Initialized OneOffPluginHandler")
        return _pluginHandler

    if _oneoffv2_plugin_enabled:
        _pluginHandler = OneOffV2PluginHandler(*initial_data, **kwargs)
        ebLogInfo("Initialized OneOffV2PluginHandler")
        return _pluginHandler

    return _pluginHandler
