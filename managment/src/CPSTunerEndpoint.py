#
# $Header: ecs/exacloud/exabox/managment/src/CPSTunerEndpoint.py /main/7 2023/10/04 17:22:33 anhiguer Exp $
#
# CPSTunerEndpoint.py
#
# Copyright (c) 2020, 2023, Oracle and/or its affiliates.
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
            _bundle_status_json_path = os.path.realpath(os.path.join(self.__install_dir, "..", "script/cpstuner_fixBundle_status.json"))
            if not os.path.isfile(_bundle_status_json_path):
                self.mGetResponse()['status'] = 500
                self.mGetResponse()['error'] = '{0} is an invalid filepath. Please review ' \
                                            'exacloud/exabox/managment/config/basic.conf'.format(_bundle_status_json_path)
                return
            __cmd_to_exec = ['/usr/bin/cat', _bundle_status_json_path]
            __rc, __stdout, __stderr = self.mBashExecution(__cmd_to_exec, subprocess.PIPE)

        elif __op == "exec_status":
            _cpstuner_execute_status_path  = os.path.realpath(os.path.join(self.__install_dir, "cpstuner/config/cpstuner_applyScript_execStatus.conf"))
            if not os.path.isfile(_cpstuner_execute_status_path):
                self.mGetResponse()['status'] = 500
                self.mGetResponse()['error'] = '{0} is an invalid filepath. Please review ' \
                                            'exacloud/exabox/managment/config/basic.conf'.format(_cpstuner_execute_status_path)
                return
            __cmd_to_exec = ['/usr/bin/cat', _cpstuner_execute_status_path]
            __rc, __stdout, __stderr = self.mBashExecution(__cmd_to_exec, subprocess.PIPE)

        # Failure
        if __rc != 0:
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = 'Error obtaining cps tuner status for op = {0} '.format(__op)
            return

        # Success
        # Preprocess the output to remove well-known tags so return value is just JSON
        __result = __stdout
        __start_tag = '----START-JSON-DATA----'
        __start_tag_index = __result.find(__start_tag)
        if __start_tag_index >= 0:
            __result = __result[__start_tag_index + len(__start_tag):]

        __end_tag = '----END-JSON-DATA----'
        __end_tag_index = __result.find(__end_tag)
        if __end_tag_index >= 0:
            __result = __result[:__end_tag_index]

        # Convert to JSON on a best-effort basis
        try:
            __result = json.loads(__result)
        except ValueError as e:
            # This is not JSON, return value as-is
            pass

        self.mGetResponse()['text'] = __result

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
        # Preprocess the output to remove well-known tags so return value is just JSON
        __result = __stdout
        __start_tag = '----START-JSON-DATA----'
        __start_tag_index = __result.find(__start_tag)
        if __start_tag_index >= 0:
            __result = __result[__start_tag_index + len(__start_tag):]

        __end_tag = '----END-JSON-DATA----'
        __end_tag_index = __result.find(__end_tag)
        if __end_tag_index >= 0:
            __result = __result[:__end_tag_index]

        # Convert to JSON on a best-effort basis
        try:
            __result = json.loads(__result)
        except ValueError as e:
            # This is not JSON, return value as-is
            pass

        self.mGetResponse()['text'] = __result

    def __add_status_to_execute_status_conf(self):
        if "keys_to_add" not in self.mGetBody():
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = 'keys_to_add flag required'
            return
        try:
            string_json_to_add = self.mGetBody()["keys_to_add"]
            json_to_add = json.loads(string_json_to_add)
            __cpstuner_execute_status_path  = os.path.realpath(os.path.join(self.__install_dir, "cpstuner/config/cpstuner_applyScript_execStatus.conf"))
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