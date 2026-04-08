#
# $Header: ecs/exacloud/exabox/managment/src/CPSTunerEndpoint.py /main/7 2023/10/04 17:22:33 anhiguer Exp $
#
# CPSTunerEndpoint.py
#
# Copyright (c) 2020, 2026, Oracle and/or its affiliates.
#
#    NAME
#      CPSTunerEndpoint.py - Basic functionality
#
#    DESCRIPTION
#      Wrapper for cps tuner commands execution
#
#    NOTES
#      None
#
#    MODIFIED   (MM/DD/YY)
#    cagaray     03/02/26 - 32065633 - Improve CPS Tuner endpoint for filtering
#                           status of a specific patch
#    shapatna    02/09/26 - Bug: 38900266 - Fix for issues pointed by Codev 
#                           in exabox/management directory
#    anhiguer    09/07/23 - 35787795 Adding endpoint for getting execute status
#    anhiguer    05/18/23 - 34874427 - Adding endpoint to download specific
#                           bundle
#    harshpa     01/20/23 - Enh 34874477 - CPSTUNER V7: REMOTEEC ENDPOINT FOR
#                           CPSTUNER_FIXBUNDLE_STATUS.JSON
#    rbehl       07/20/20 - Creation
#

from exabox.managment.src.AsyncTrackEndpoint import AsyncTrackEndpoint
import base64
import os
import subprocess
import stat
import json
from datetime import datetime



CPSTUNER_CONF_PATH = "/opt/oci/exacc/cpstuner/config/cpstuner.conf"
CPSTUNER_CLI_PATH = "/opt/oci/exacc/cpstuner/cps_tuner_cli.py"

class CPSTunerEndpoint(AsyncTrackEndpoint):

    def __init__(self, aHttpUrlArgs, aHttpBody, aHttpResponse, aSharedData):
        # Initialization of the base class
        AsyncTrackEndpoint.__init__(self, aHttpUrlArgs, aHttpBody,
                                    aHttpResponse, aSharedData)
        self.__install_dir = self.mGetConfig().mGetConfigValue('install_dir')

    def mGet(self):
        if self.__install_dir is None or not os.path.isdir(self.__install_dir):
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = 'install_dir key is missing or ' \
                                           'pointing to an invalid directory. ' \
                                           'Please review ' \
                                           'exacloud/exabox/managment/config/basic.conf'
            return

        # Check whether this validation is really needed

        __op = None
        __rc = 1

        if self.mGetUrlArgs() is not None:
            _url_args = list(self.mGetUrlArgs().keys())
            if "op" in _url_args:
                __op = self.mGetUrlArgs()["op"]

        if __op is None:
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = 'op is a required parameter.'
            return

        if __op == "bundle_status":
            _bundle_status_json_path = os.path.realpath(os.path.join(
                self.__install_dir, "..", "script/cpstuner_fixBundle_status.json"))
            if not os.path.isfile(_bundle_status_json_path):
                self.mGetResponse()['status'] = 500
                self.mGetResponse()['error'] = '{0} is an invalid filepath. Please review ' \
                                               'exacloud/exabox/managment/config/basic.conf'.format(_bundle_status_json_path)
                return
            __cmd_to_exec = ['/usr/bin/cat', _bundle_status_json_path]
            __rc, __stdout, __stderr = self.mBashExecution(__cmd_to_exec, subprocess.PIPE)

        elif __op == "exec_status":
            _cpstuner_execute_status_path = os.path.realpath(os.path.join(
                self.__install_dir, "cpstuner/config/cpstuner_applyScript_execStatus.conf"))
            if not os.path.isfile(_cpstuner_execute_status_path):
                self.mGetResponse()['status'] = 500
                self.mGetResponse()['error'] = '{0} is an invalid filepath. Please review ' \
                                               'exacloud/exabox/managment/config/basic.conf'.format(_cpstuner_execute_status_path)
                return
            __cmd_to_exec = ['/usr/bin/cat', _cpstuner_execute_status_path]
            __rc, __stdout, __stderr = self.mBashExecution(__cmd_to_exec, subprocess.PIPE)

        elif __op == "filter_status":
            __result = self.__get_version_status()
            if __result is None:
                return
            __rc = 0

        # Failure
        if __rc != 0:
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = 'Error obtaining cps tuner status for op = {0} '.format(__op)
            return

        # Success
        if __op == "filter_status":
            self.mGetResponse()['text'] = __result
            return

        # Preprocess the output to remove well-known tags so return value is just JSON
        __result = self.__parse_json_payload(__stdout)

        self.mGetResponse()['text'] = __result

    def __get_version_status(self):
        _version_json_path = os.path.realpath(os.path.join(
            self.__install_dir, "..", "script/version.json"))
        if not os.path.isfile(_version_json_path):
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = '{0} is an invalid filepath. Please review ' \
                                           'exacloud/exabox/managment/config/basic.conf'.format(_version_json_path)
            return None

        __cmd_to_exec = ['cat', _version_json_path]
        __rc, __stdout, __stderr = self.mBashExecution(__cmd_to_exec, subprocess.PIPE)
        if __rc != 0:
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = 'Error obtaining cps tuner status {0} {1}'.format(__stdout, __stderr)
            return None

        __result = self.__parse_json_payload(__stdout)
        __bug_id = None
        __after_download_timestamp = None
        __patch_name = None
        __apply_script = None
        if self.mGetUrlArgs() is not None and "bug_id" in self.mGetUrlArgs():
            __bug_id = str(self.mGetUrlArgs()["bug_id"]).strip()
        if self.mGetUrlArgs() is not None and "after_download_timestamp" in self.mGetUrlArgs():
            __after_download_timestamp = str(
                self.mGetUrlArgs()["after_download_timestamp"]).strip()
        if self.mGetUrlArgs() is not None and "patch_name" in self.mGetUrlArgs():
            __patch_name = str(self.mGetUrlArgs()["patch_name"]).strip()
        if self.mGetUrlArgs() is not None and "apply_script" in self.mGetUrlArgs():
            __apply_script = str(self.mGetUrlArgs()["apply_script"]).strip()

        if (__bug_id or __after_download_timestamp or __patch_name or __apply_script) and isinstance(__result, list):
            __filtered = []
            for entry in __result:
                __match = self.__matches_filters(entry, __bug_id,
                                                 __after_download_timestamp,
                                                 __patch_name, __apply_script)
                if __match is None:
                    return None
                if __match:
                    __filtered.append(entry)
            __result = __filtered

        return __result

    def __matches_filters(self, entry, bug_id, after_download_timestamp,
                          patch_name, apply_script):
        if bug_id:
            bug_list = [bug.strip() for bug in str(
                entry.get("bug_id", "")).split(",") if bug.strip()]
            if bug_id not in bug_list:
                return False

        if after_download_timestamp:
            timestamp_value = str(entry.get("download_timestamp", "")).strip()
            if not timestamp_value:
                return False
            entry_time = self.__parse_timestamp(timestamp_value)
            filter_time = self.__parse_timestamp(after_download_timestamp)
            if entry_time is None or filter_time is None:
                self.mGetResponse()['status'] = 400
                self.mGetResponse()['error'] = 'Invalid after_download_timestamp format. Expected YYYY-MM-DD or YYYY-MM-DD_HH:MM:SS.'
                return None
            if entry_time <= filter_time:
                return False

        if patch_name:
            download_loc = str(entry.get("download_loc", "")).strip()
            if not download_loc:
                return False
            patch_value = self.__extract_patch_name(download_loc)
            if patch_value is None:
                return False
            if patch_name != patch_value:
                return False

        if apply_script:
            download_loc = str(entry.get("download_loc", "")).strip()
            if not download_loc:
                return False
            script_value = self.__extract_apply_script(download_loc)
            if script_value is None:
                return False
            if apply_script != script_value:
                return False

        return True

    def __extract_patch_name(self, download_loc):
        marker = "/script/"
        marker_index = download_loc.find(marker)
        if marker_index == -1:
            return None
        remainder = download_loc[marker_index + len(marker):]
        if not remainder:
            return None
        return remainder.split("/", 1)[0].strip() or None

    def __extract_apply_script(self, download_loc):
        if not download_loc:
            return None
        return download_loc.rsplit("/", 1)[-1].strip() or None

    def __parse_timestamp(self, timestamp_value):
        try:
            return datetime.strptime(timestamp_value, "%Y-%m-%d_%H:%M:%S")
        except ValueError:
            pass

        try:
            return datetime.strptime(timestamp_value, "%Y-%m-%d")
        except ValueError:
            return None

    def __parse_json_payload(self, payload):
        __result = payload
        __start_tag = '----START-JSON-DATA----'
        __start_tag_index = __result.find(__start_tag)
        if __start_tag_index >= 0:
            __result = __result[__start_tag_index + len(__start_tag):]

        __end_tag = '----END-JSON-DATA----'
        __end_tag_index = __result.find(__end_tag)
        if __end_tag_index >= 0:
            __result = __result[:__end_tag_index]

        try:
            __result = json.loads(__result)
        except ValueError:
            pass

        return __result

    def mPost(self):
        if self.__install_dir is None or not os.path.isdir(self.__install_dir):
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = 'install_dir key is missing or ' \
                                           'pointing to an invalid directory. ' \
                                           'Please review ' \
                                           'exacloud/exabox/managment/config/basic.conf'
            return

        _version_json_path = os.path.realpath(os.path.join(self.__install_dir, "..", "script/version.json"))
        if not os.path.isfile(_version_json_path):
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = '{0} is an invalid filepath. Please review ' \
                                           'exacloud/exabox/managment/config/basic.conf'.format(_version_json_path)
            return

        # Check whether this validation is really needed
        __op = None
        
        if 'op' in self.mGetBody():
            __op = self.mGetBody()['op']
        
        if __op is None:
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = 'op is a required parameter.'
            return

        if __op == "status":
            __cmd_to_exec = ['cat', _version_json_path]
            __rc, __stdout, __stderr = self.mBashExecution(__cmd_to_exec, subprocess.PIPE)
        elif __op == "exec_status":
            self.__add_status_to_execute_status_conf()
            return
        # Failure
        if __rc != 0:
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = 'Error obtaining cps tuner status {0} {1}'.format(__stdout, __stderr)
            return

        # Success
        __result = self.__parse_json_payload(__stdout)

        self.mGetResponse()['text'] = __result

    def __add_status_to_execute_status_conf(self):
        if "keys_to_add" not in self.mGetBody():
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = 'keys_to_add flag required'
            return
        try:
            string_json_to_add = self.mGetBody()["keys_to_add"]
            json_to_add = json.loads(string_json_to_add)
            __cpstuner_execute_status_path = os.path.realpath(os.path.join(
                self.__install_dir, "cpstuner/config/cpstuner_applyScript_execStatus.conf"))
            curr_json = self.__load_json(__cpstuner_execute_status_path)
            # merge dicts
            curr_json.update(json_to_add)

            with open(__cpstuner_execute_status_path, "w", encoding="utf-8") as _file:
                json.dump(curr_json, _file)

            self.mGetResponse()['text'] = "Key and value added succesfully"
        except Exception as err:
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = "Error adding new items. {}".format(err)

    def mPut(self):
        __op = None
        
        if 'op' in self.mGetBody():
            __op = self.mGetBody()['op']

        if __op is None:
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = "op is a required parameter."
            return

        if __op == "download":
            self.__download_specific_bundle()

        elif __op == "set":
            self.__set_download_latest_property()


    def __download_specific_bundle(self):
        if "bundle" not in self.mGetBody():
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = "Bundle not passed"
            return
        __bundle = self.mGetBody()['bundle']
        __cmd = [CPSTUNER_CLI_PATH, "--download", __bundle]
        subprocess.Popen(__cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.mGetResponse()['text'] = "CPSTuner CLI download in progress. Please check status json."

    def __set_download_latest_property(self):
        if "flag" not in self.mGetBody():
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = "Flag not passed"
            return

        __flag = self.mGetBody()['flag'].lower()

        if __flag not in ["true", "false"]:
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = "Incorrect flag value"
            return

        __flag = True if __flag == "true" else False

        try:
            self.__change_property("downloadLatest", __flag)
        except Exception as e:
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = "Error changing donwloadLatest property\n" + str(e)
            return
        self.mGetResponse()['text'] = "Property updated successfully"

    def __change_property(self, property, value):
        conf_file = self.__load_json(CPSTUNER_CONF_PATH)
        conf_file[property] = value
        os.chmod(CPSTUNER_CONF_PATH,  os.stat(CPSTUNER_CONF_PATH).st_mode | stat.S_IWRITE)
        with open(CPSTUNER_CONF_PATH, "w", encoding="utf-8") as _file:
            json.dump(conf_file, _file)

    def __load_json(self, json_path):
        with open(json_path, encoding="utf-8") as _file:
            conf_file = json.load(_file)
        return conf_file
# end of file
