#
# $Header: ecs/exacloud/exabox/infrapatching/handlers/pluginHandler/dbnupluginhandler.py /main/12 2024/09/24 16:45:50 araghave Exp $
#
# dbnupluginhandler.py
#
# Copyright (c) 2020, 2024, Oracle and/or its affiliates.
#
#    NAME
#      dbnupluginhandler.py - This module contains methods to run dbnu plugin on selected targets.
#
#    DESCRIPTION
#      This module contains methods to run dbnu plugin on selected targets.
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    araghave    08/27/24 - Enh 36829406 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE CORE, PLUGIN AND TASKHANDLER
#                           FILES
#    araghave    06/13/24 - Enh 36522596 - REVIEW PRE-CHECK/PATCHING/ROLLBACK
#                           LOGS AND CLEAN-UP
#    vmallu      03/17/23 - Enh 32298104 - ENABLE DBNU PLUGIN SUPPORT FOR DOMU
#    pkandhas    08/17/22 - Bug 34245376 - Remove code related to dom0.txt
#    araghave    06/06/22 - Enh 34239188 - ADD ADDITIONAL, GRANULAR ERROR
#                           CODES FOR PLUG-IN FAILURES
#    araghave    01/18/22 - Enh 30646084 - Require ability to specify compute
#                           nodes to include as part of Patching process
#    araghave    12/08/21 - Enh 33598784 - MOVE ALL INFRA PATCHING ERROR CODES
#                           FROM ERROR.PY TO INFRAPATCHERROR.PY
#    jyotdas     11/19/21 - ENH 33577777 - Handle dbnu plugin script location
#                           in infrapatching to support exacc
#    araghave    12/08/20 - Enh 31984849 - RETURN ERROR CODES TO DBCP FROM DOMU
#                           AND PLUGINS
#    nmallego    08/28/20 - Refactor infra patching code
#    nmallego    08/28/20 - Creation
#

import os, sys
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.infrapatching.handlers.pluginHandler.pluginhandler import PluginHandler
from exabox.infrapatching.utils.utility import mRegisterInfraPatchingHandlers
from exabox.infrapatching.utils.constants import *
from exabox.infrapatching.core.infrapatcherror import *
from exabox.log.LogMgr import ebLogError, ebLogInfo

sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))

class DbnuPluginHandler(PluginHandler):

    def __init__(self, *initial_data, **kwargs):
        super(DbnuPluginHandler, self).__init__(*initial_data, **kwargs)
        self.mPatchLogInfo("DbnuPluginHandler")
        mRegisterInfraPatchingHandlers(INFRA_PATCHING_HANDLERS, [PLUGIN_DBNU], self)
        # Currently dbnu plugins are for compute nodes , dom0 and domU
        # Initialize all variables required for plugins to run
        self.initializePluginMetadata()

    @staticmethod
    def mIsRunDbnuPlugin(aTargetTypes, aTaskType, aDbnuPluginBaseDirPrefix):
        """
          This function is called right whenever any targethandler like dom0 , domu is initialized .
          Based on True/False , the DbnuPluginHandler is initialized else it will not be initialized at all
        """
        try:
            _plugin_script = None

            if aDbnuPluginBaseDirPrefix is None:
                ebLogError("Dbnu Plugin Base Dir not specified")
                return False

            if aTaskType not in [ TASK_PATCH, TASK_ROLLBACK ]:
                return False

            #Applicable only for Dom0 and Domu
            if PATCH_DOM0 not in aTargetTypes and PATCH_DOMU not in aTargetTypes:
                return False

            #For EXACC /u01/downloads/exadata/exadataPrePostPlugins/dbnu_plugins/
            #for EXACS <EXACLOUD_HOME>/exadata/exadataPrePostPlugins/dbnu_plugins/
            _plugins_base_dir = os.path.join(aDbnuPluginBaseDirPrefix, "exadataPrePostPlugins")

            _plugins_dbnu_dir = os.path.join(_plugins_base_dir, "dbnu_plugins")
            #To make it compatible with older bundles, we check for the existence of both the scripts dom0.sh or infra_dbnu_plugin.sh
            #Any of them exists, dbnu plugin will run
            #Skip this check for domu

            if PATCH_DOMU not in aTargetTypes:
                return True

            _plugin_scripts = [os.path.join(_plugins_dbnu_dir, "dom0.sh"), os.path.join(_plugins_dbnu_dir, "infra_dbnu_plugin.sh")]
            for _plugin_script in _plugin_scripts:
                if os.path.exists(_plugin_script):
                    ebLogInfo("Dbnu plugin script exists.")
                    return True

            return False

        except Exception as e:
            ebLogError(f"Exception: Validating presence of dbnu plugins: {str(e)}")

        return False

    def mApply(self, aNode, aNodeType):
        """
          -> Returns PATCH_SUCCESS_EXIT_CODE if all checks pass.
          -> Return non PATCH_SUCCESS_EXIT_CODE if any of the checks failed.

          This method helps to:
          1) Do nothing if there are no plugins to run
          2) Copy dbnu plugins to target nodes and helps to run during dbnu/patchmgr session.
          3) Copy exacloud pre-post scripts to dom0/domU and can be used before and after patchmgr run.
             Args passed:
             aNode => Node on which plugins needs to run
             aNodeType => type of node (dom0/domU)
        """

        # Set dbnu plugin locations only
        _plugins_base_dir = os.path.join(self.mGetDbnuPluginBaseDirPrefix(), "exadataPrePostPlugins")
        _plugins_dbnu_dir = os.path.join(_plugins_base_dir, "dbnu_plugins")

        ret = PATCH_SUCCESS_EXIT_CODE

        # Location of dbnu plugins on target node
        _plugins_to_run = {"dbnu_plugins": {'plugin_loc_dir': _plugins_dbnu_dir,
                                            'plugin_remote_dir': '/opt/exacloud/customs/plugins/dbnu_plugins/'}
                           }
        self.mPatchLogInfo(f"\nRunning DBNU plugins on '{aNodeType}' : '{aNode}'")

        try:
            # 1. Copy dbnu plugins. These plugins will be run by patchmgr->dbnodeupdate.sh
            # during patchmgr/patching

            ebLogInfo(f"Copying plugins to {aNode} '{aNodeType}':")
            _dom0U = exaBoxNode(get_gcontext())
            _dom0U.mConnect(aHost=aNode)

            # Copy all plugins to target node
            for _plugin_type, _plugin_list in _plugins_to_run.items():
                ebLogInfo(f"Copy {_plugin_type.upper()} to {aNodeType} '{aNode}':")
                _plugin_loc_dir = _plugin_list['plugin_loc_dir']
                _plugin_remote_dir = _plugin_list['plugin_remote_dir']
                if os.path.isdir(_plugin_loc_dir) and os.listdir(_plugin_loc_dir):
                    # as a root user for dom0
                    _dom0U.mExecuteCmdLog(f'mkdir -p {_plugin_remote_dir}')

                    for _entry_file in os.listdir(_plugin_loc_dir):
                        ebLogInfo(
                            f"Copy plugins: Source = {os.path.join(_plugin_loc_dir, _entry_file)}, Destination file = {os.path.join(_plugin_remote_dir, _entry_file)}")
                        # if listed entry is diretory, then we skip it, since we expect
                        # all files in plugin directory itself.
                        if os.path.isdir(os.path.join(_plugin_loc_dir, _entry_file)):
                            ebLogInfo(
                                f"The '{os.path.join(_plugin_loc_dir, _entry_file)}' is a directory, we skip to copy directory.")
                            continue
                        else:
                            if os.path.exists(os.path.join(_plugin_loc_dir, _entry_file)):
                                _dom0U.mCopyFile(os.path.join(_plugin_loc_dir, _entry_file),
                                                 os.path.join(_plugin_remote_dir, _entry_file))
                    _dom0U.mExecuteCmdLog(f"chmod +x -R {_plugin_remote_dir}")
                    if os.path.join(_plugin_remote_dir, "install.sh"):
                        ebLogInfo(
                            f"Move install.sh from Source = {os.path.join(_plugin_remote_dir, 'install.sh')}, Destination = {os.path.dirname(os.path.dirname(_plugin_remote_dir))}")
                        _dom0U.mExecuteCmdLog(
                            f"mv {os.path.join(_plugin_remote_dir, 'install.sh')} {os.path.dirname(os.path.dirname(_plugin_remote_dir))}")

                else:
                    ebLogInfo(f"No {_plugin_type.upper()} scripts to copy from '{_plugin_loc_dir}'")

            if _dom0U.mIsConnected():
                _dom0U.mDisconnect()

        except Exception as e:
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()
            if _child_request_error_already_exists_in_db:
                ret = _rc
            else:
                _suggestion_msg = f"Exception: Copying Plugins: {str(e)}"
                ret = DBNUPLUGIN_COPY_ERROR
                self.mAddError(ret, _suggestion_msg)
        finally:
            return ret

    def mCleanupDbnuPluginsFromNode(self, aNode, aNodeType):

        self.mPatchLogInfo(f"\nCleaning up DBNU plugins on '{aNodeType}' : '{aNode}'")
        # Set dbnu plugin locations only
        _plugins_base_dir = os.path.join(self.mGetDbnuPluginBaseDirPrefix(), "exadataPrePostPlugins")
        _plugins_dbnu_dir = os.path.join(_plugins_base_dir, "dbnu_plugins")
        # Location of dbnu plugins on target node
        _plugins_to_run = {"dbnu_plugins": {'plugin_loc_dir': _plugins_dbnu_dir,
                                            'plugin_remote_dir': '/opt/exacloud/customs/plugins/dbnu_plugins/'}
                           }
        self.mCleanupPluginsfromTargetNode(aNode, aNodeType, _plugins_to_run, POST_PATCH)
