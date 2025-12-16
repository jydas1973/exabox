#!/usr/bin/python3
#
# $Header: ecs/exacloud/exabox/infrapatching/utils/exadata_bundles_purge.py /main/24 2025/11/18 18:35:18 mirrodri Exp $
#
# exadata_bundles_purge.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#    Exadata cloud bundle purge script - Basic Functionality
#
#    DESCRIPTION
#    Provide basic purge management using a json configuration file
#    on OCI EXACC environments.
#       Usage:
#       ./exadata_bundles_purge.py --exadatafolder=/u01/downloads/exadata
#                                  --metadatafile=/u01/downloads/exadata_bundles_metadata.json
#
#       -e, --exadatafolder: Exadata folder where bundles are untarred and PatchPayloads and images folders are located.
#                            Optional. Default value is /u01/downloads/exadata
#       -m, --metadatafile:  exadata_bundles_metadata.json file absolute path.
#                            Optional. Default value is /u01/downloads/exadata_bundles_metadata.json.
#
#    NOTES
#      No
#
#    MODIFIED   (MM/DD/YY)
#    kdas        10/29/25 - Bug 38588871 - Bundle purging should fail if we are
#                           unable to download latest
#                           exadata_bundles_retention_policy.json every after
#                           retries
#    mirrodri    10/28/25 - Bug 37315658 - Add support for the local retention
#                           file for testing.
#    mirrodri    08/06/25 - Bug 37834488 - Fixed an issue where bundle was
#                           not being removed due to an unexpected bunlde
#                           name.
#    josedelg    05/16/25 - Bug 35848654 - Dont remove tar bundle
#                           while imagemgmt is untarring it
#    josedelg    05/14/25 - Bug 37797348 - Run only using ECRA user
#    josedelg    05/14/25 - Bug 37932443 - RTG image needs to be retain
#    avimonda    01/12/25 - Bug 37445844 - EXADATA FILESYSTEMCHECKS U01
#    araghave    08/27/24 - Enh 36829406 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE CORE, PLUGIN AND TASKHANDLER
#                           FILES
#    josedelg    08/15/24 - Bug 36932898 - Fix parsing metadata json file
#    josedelg    07/24/24 - Bug 36863591 - Change retention policy json file
#                           location
#    josedelg    07/19/24 - Bug 36750722 - Remove leftover bundles using a new
#                           bundle name convention.
#    josedelg    05/31/24 - Bug 36632719 - Use retention policy file for
#                           exadata computes bundles.
#    josedelg    09/05/23 - Bug 35760439 - Extracted exadata patches must be
#                           removed using sudo.
#    josedelg    08/10/23 - Enh 35638971 - Cleanup extrated exadata patches
#                           when CPS is selected as a launch node
#    josedelg    04/28/23 - Bug 35226800 - Clear exasplice bundles
#    josedelg    03/03/23 - Enh 34235673 - Compatibility with new patch stage
#                           location
#    josedelg    07/28/22 - Enh 34353378 - Download metadata file from private
#                           bucket
#    josedelg    09/28/22 - Bug 34604883 - Remove leftover bundles a system
#                           images not  used for virtualization type (xen/kvm)
#    josedelg    09/19/22 - Bug 34615935 - Add files details in metadata json
#    josedelg    09/02/22 - Bug 34551752 - Sync metadata file
#    josedelg    08/29/22 - Bug 34543749 - Validate active process
#    josedelg    05/19/22 - Enh 34116323 - Creation of exadata cloud bundle purge
#    josedelg    05/26/22 - Creation
#
from json.decoder import JSONDecodeError
from optparse import OptionParser
import os
import glob
import json
import subprocess
import shlex
import getpass
import re
import logging
from logging.handlers import RotatingFileHandler
import sys
import time

bundles_list_folder = "/u01/downloads"
retention_policy_folder = "/opt/oci/exacc/exacloud/exabox/infrapatching/utils"
exadata_version_folder = "exadata"
cpsos_version_folder = "cpsos"
compute_folder = "dbgipatch/exadata_compute_updates"
bundles_list_file = "exadata_bundles_retention_policy.json"
exadata_bundle_metadata = "exadata_bundles_metadata.json"
img_download_properties = "/opt/oci/exacc/imagemgmt/config/download.properties"
exadata_purge_name = os.path.basename(__file__)
managerepo_name= "managerepo"
virtualization_kvm = "kvm"
virtualization_xen = "xen"
img_download_utility = "/opt/oci/exacc/imagemgmt/bin/download_utility.py"
cps_infrapatch_base = "/opt/oci/exacc/exacloud/InfraPatchBase/"
qa_exadata_retention_policy = "/u01/downloads/qa_exadata_retention_policy.json"

class PurgeLog:
    __debug = False
    __log_file = "log/exadata_bundles_purge.log"
    __log_level = logging.INFO
    __logger = None

    def __init__(self, p_exadata_folder, p_log_name, _log_size, _backup_count):
        _log_folder = f"{p_exadata_folder}{'/log/'}"
        create_directory(_log_folder)

        #get the logger object from the logging module
        self.__logger = logging.getLogger(p_log_name)
        self.__logger.setLevel(self.__log_level)

        # logfile name.
        _filename = f"{_log_folder}{p_log_name}"

        # Create file handler
        fileHandler = RotatingFileHandler(_filename, mode='a', maxBytes=_log_size, backupCount=_backup_count,
                                          encoding=None, delay=0)

        # Get the formator object and set it to fileHandler
        fileFormator = logging.Formatter(
            '%(asctime)s: %(levelname)s: %(filename)s:%(lineno)s - %(funcName)s(): %(message)s')
        fileHandler.setFormatter(fileFormator)
        # set the level to the fileHanlder.
        fileHandler.setLevel(logging.DEBUG)
        # finally add handler to the logger object.
        self.__logger.addHandler(fileHandler)

        # adding log to console
        consoleHandler = logging.StreamHandler(sys.stdout)
        consoleHandler.setFormatter(fileFormator)
        self.__logger.addHandler(consoleHandler)

    def print_info(self, p_message):
        self.__logger.info(p_message)

    def print_error(self, p_message):
        self.__logger.error(p_message)

    def print_debug(self, p_message):
        self.__logger.debug(p_message)

    def print_warn(self, p_message):
        self.__logger.warning(p_message)


class ExadataVersionConfig:
    __config_file = ""
    __config_dict = {}

    def __init__(self, p_config_file):
        self.__config_file = p_config_file
        _img_download_dict = load_properties(img_download_properties)
        self.__oos_bucket_url = _img_download_dict["oss.url"]
        _env_proxy = _img_download_dict["cp.proxy"]
        _proxy_host = None
        _proxy_port = None
        self.__proxy_param = None
        if _env_proxy == "null":
            log.print_warn("no proxy details available in property file")
        else:
            _proxy_host, _proxy_port = get_proxy_detail(_env_proxy)
        if _proxy_host is not None and _proxy_port is not None:
            self.__proxy_param = f'{"http://"}{_proxy_host}:{_proxy_port}'

    def download_utility(self):
        log.print_info(
            f"Downloading config file {bundles_list_file}/{bundles_list_file} using {img_download_utility}... ")
        _cmd_img_download_utility = img_download_utility

        if self.__proxy_param is not None:
            _cmd_img_download_utility = f'{_cmd_img_download_utility} {"-p"} {self.__proxy_param} '

        _cmd_img_download_utility = f" {_cmd_img_download_utility} {'-u'} {self.__oos_bucket_url} "
        _cmd_img_download_utility = f" {_cmd_img_download_utility} {'-o'} {bundles_list_file} "
        _cmd_img_download_utility = f" {_cmd_img_download_utility} {'-d'} {retention_policy_folder} "

        log.print_info(f"Cmd to use for downloading {bundles_list_file} is {_cmd_img_download_utility}")

        '''
        download_utility.py command example:
        /opt/oci/exacc/imagemgmt/bin/download_utility.py 
            -p 
            -u https://swiftobjectstorage.us-phoenix-1.oraclecloud.com/v1/intexadatateam/ImageManagement 
            -o exadata_bundles_retention_policy.json 
            -d /tmp
        '''
        _output, _status = safe_execute_local(shlex.split(_cmd_img_download_utility))
        if _status == 0:
            log.print_debug(f"Stdout for the download_utility.py command - {_output.strip()}")
        else:
            log.print_warn(f"Failed to download oss file {bundles_list_file} : {_output}")
            self.download()

    def download(self):
        log.print_info(f"Downloading config file {bundles_list_file}/{bundles_list_file} ... ")
        _cmd_curl = "/usr/bin/curl "
        _bundles_list_file_path = f"{retention_policy_folder}/{bundles_list_file}"
        _bundles_list_file_path_tmp = f"{retention_policy_folder}/{bundles_list_file}-tmp"

        _oss_file_url = f"{self.__oos_bucket_url}/{bundles_list_file}"

        if self.__proxy_param is not None:
            _cmd_curl = f'{_cmd_curl} {"-x"} {self.__proxy_param}'

        _params = "{0}{1}{2}{3}".format('-s -o ',_bundles_list_file_path_tmp , ' -w', '"%{http_code}"')
        _cmd_curl = f"{_cmd_curl} {_params}"

        _cmd_curl = f'{_cmd_curl} {_oss_file_url}'

        log.print_debug(f"Cmd to use for downloading {bundles_list_file} is {_cmd_curl}")
        log.print_info(f"Downloading oss file {bundles_list_file} from oss bucket ...")

        '''
        curl command example:
        curl  -x http://www-proxy-hqdc.us.oracle.com:80 
              -s -o /u01/downloads/exadata_bundles_retention_policy.json-tmp -w"%{http_code}" 
              https://swiftobjectstorage.us-phoenix-1.oraclecloud.com/v1/intexadatateam/ImageManagement/exadata_bundles_retention_policy.json
        '''
        _num_retries = 3
        _retry_delay = 30  # seconds, to allow for guarding against intermittent connectivity issues to oss
        for attempt in range(1, _num_retries + 1):
          _output, _status = safe_execute_local(shlex.split(_cmd_curl))
          if _status != 0:
            log.print_warn(f"Failed to download oss file {bundles_list_file} : {_output}. "
                           f"Will retry in {_retry_delay} seconds.")
          else:
            log.print_info(f"stdout for the curl command - {_output.strip()}")
            if _output and _output.strip() != "200":
              log.print_warn(f"Curl command returned status code :: {_output.strip()}. "
                             f"Will retry in {_retry_delay} seconds.")
            else:
              _cmd_cp = f"/usr/bin/cp {_bundles_list_file_path_tmp} {_bundles_list_file_path}"
              _output, _status = safe_execute_local(shlex.split(_cmd_cp))
              if _status != 0:
                log.print_error(f"cp {_bundles_list_file_path_tmp} {_bundles_list_file_path} failed. "
                                f"Error: {_output.strip() if _output else 'No error message'}. "
                                f"Exiting as the latest {bundles_list_file} could not be copied.")
                exit(1)
              else:
                break  # curl and cp both succeeded, exit the retry loop

          if attempt == _num_retries:
            log.print_error(f"Exceeded maximum retries for curl. "
                            f"Exiting due to failure in downloading file {bundles_list_file}")
            exit(1)
          time.sleep(_retry_delay)

        _cmd_rm_tmp = f"/usr/bin/rm {_bundles_list_file_path_tmp}"
        _output, _status = safe_execute_local(shlex.split(_cmd_rm_tmp))

    def validate_json_file(self, aJsonFile):
        log.print_info(f"Validating json file format {aJsonFile} ...")
        _valid_json_file = True
        log.print_debug(f"Input file: {str(aJsonFile)}")

        # Validate file exists and is readable
        if os.path.exists(aJsonFile):
            log.print_debug(f"File :: {aJsonFile} exists.")

            # Validate file is not a directory
            if os.path.isdir(aJsonFile):
                log.print_error(f"File {aJsonFile} is a directory.")
                _valid_json_file = False
            else:
                input_json = None
                try:
                    with open(aJsonFile) as input_file:
                        input_json = json.load(input_file)
                        log.print_debug(f"File :: {aJsonFile} is a well-formed json file.")
                        _valid_json_file = True

                except ValueError as error_found:
                    log.print_debug(error_found)
                    _valid_json_file = False
        else:
            log.print_debug(f"File :: {aJsonFile} does not exist.")
            _valid_json_file = False

        return _valid_json_file

    def load_file(self):
        if not os.path.exists(img_download_utility):
            self.download()
        else:
            self.download_utility()
        if not os.path.exists(self.__config_file):
            log.print_error("Exadata bundle list configuration file does not exist!")
            return False
        if not self.validate_json_file(self.__config_file):
            log.print_error("Exadata bundle list configuration file is not in proper format")
            return False
        with open(self.__config_file) as _config_json:
            self.__config_dict = json.load(_config_json)
            log.print_debug(f"Exadata bundle list -> {self.__config_dict}")

        # qa_exadata_retention_policy is added as some testing need retain some  additional images
        if os.path.exists(qa_exadata_retention_policy) and os.stat(qa_exadata_retention_policy).st_size > 0:
            if not self.validate_json_file(qa_exadata_retention_policy):
                log.print_error("Exadata bundle local list configuration file is not in proper format")
            else:
                with open(qa_exadata_retention_policy, 'r') as _local_json:
                    local_policy_dict = json.load(_local_json)
                    self.__config_dict.update(local_policy_dict)
                    log.print_debug(f"Exadata bundle list after qa exadata retention policy -> {self.__config_dict}")
        else:
            log.print_info(f"Path does not exist: {qa_exadata_retention_policy} or the file is empty.")
            
        return True

    def search_common_infra(self, aExadataVersion):
        log.print_info(f"Search {aExadataVersion} in common infra ...")
        _common_infra_details = None
        _config_dict = self.__config_dict
        if _config_dict:
            if aExadataVersion in _config_dict["CommonInfra"]:
                _common_infra_details = _config_dict["CommonInfra"][aExadataVersion]
        else:
            log.print_error(f"{_config_dict} config file is not loaded!")
            exit(1)
        return _common_infra_details

    def search_common_compute(self, aExadataVersion):
        log.print_info(f"Search {aExadataVersion} in common compute ...")
        _common_compute_details = None
        _config_dict = self.__config_dict
        if _config_dict:
            if aExadataVersion in _config_dict["CommonCompute"]:
                _common_compute_details = _config_dict["CommonCompute"][aExadataVersion]
        else:
            log.print_error(f"{self.__config_file} config file is not loaded!")
            exit(1)
        return _common_compute_details

    def search_exasplice(self, aExadataVersion):
        log.print_info(f"Search {aExadataVersion} in exasplice ...")
        _exasplice_details = None
        _config_dict = self.__config_dict
        if _config_dict:
            if aExadataVersion in self.__config_dict["ExaSplice"]:
                _exasplice_details = self.__config_dict["ExaSplice"][aExadataVersion]
        else:
            log.print_error(f"{self.__config_file} config file is not loaded!")
            exit(1)
        return _exasplice_details

    def search_cpsos(self, aCPSOSVersion):
        log.print_info(f"Search {aCPSOSVersion} in cpsos ...")
        _cpsos_details = None
        _config_dict = self.__config_dict
        if _config_dict:
            if aCPSOSVersion in self.__config_dict["CpsOs"]:
                _cpsos_details = self.__config_dict["CpsOs"][aCPSOSVersion]
        else:
            log.print_error(f"{self.__config_file} config file is not loaded!")
            exit(1)
        return _cpsos_details

    def search_system_image(self, aExadataVersion):
        _system_image_details = None
        _config_dict = self.__config_dict
        if _config_dict:
            if len([_version for _version in _config_dict["SystemImages"] if _version == aExadataVersion]) > 0:
                return True
            else:
                return False
        else:
            log.print_error(f"{self.__config_file} config file is not loaded!")
            exit(1)
        return _system_image_details

    def metadata_file_sync(self, aMetadataFile):
        _config_dict = self.__config_dict
        if _config_dict:
            log.print_info("Updating exadata bundle version json file ... ")
            if not os.path.exists(aMetadataFile):
                log.print_warn("Exadata bundle metadata file does not exist!")
            else:
                with open(aMetadataFile) as _metadata_json:
                    _metadata_dict = json.load(_metadata_json)
                    log.print_debug(f"Exadata bundle metadata file -> {_metadata_dict}")
                    _payloads = _metadata_dict["payloads"]
                    for _exadata_version_ret in _config_dict["CommonInfra"]:
                        _version_found = [_version for _version in _payloads if
                                          _version["imageVersion"] == _exadata_version_ret]
                        if len(_version_found) > 0:
                            if "display" in _config_dict["CommonInfra"][_exadata_version_ret]:
                                _version_found[0]["display"] = _config_dict["CommonInfra"][_exadata_version_ret][
                                    "display"]
                            else:
                                _version_found[0]["display"] = "no"

                _metadata_dict["payloads"] = _payloads
                with open(aMetadataFile, "w") as _output_file:
                    json.dump(_metadata_dict, _output_file, indent=4)
        else:
            log.print_error(f"{self.__config_file} config file is not loaded!")
            exit(1)

    def remove_exadata_tarballs(self, aExadataFolder):
        """
        Remove exadata common bundles
        Ex. exadata_common_21.2.8.0.0.220203.1_tar_xvf_in_exacloud_root_directory.tar
        """
        log.print_info("Removing leftover exadata common bundles")
        for _filename in os.listdir(aExadataFolder):
            _match = re.match("^exadata_common_([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\.[0-9]{6,6}(|\.[0-9]))(|_exacc)_tar_xvf_in_exacloud_root_directory(|_exacc).tar$", _filename)
            if _match:
                _status_json = ""
                _version = _match.group(1)
                _version_numbers = _version.split(".")
                _version = f"{_version_numbers[0]}.{_version_numbers[1]}.{_version_numbers[2]}.{_version_numbers[3]}.{_version_numbers[4]}_{_version_numbers[5]}"
                if len(_version_numbers) > 6:
                    _version = f"{_version}.{_version_numbers[6]}"
                _status_json_file = f"{bundles_list_folder}/{exadata_version_folder}/{_version}/status.json"
                if os.path.exists(_status_json_file):
                    try:
                        with open(_status_json_file, 'r', encoding="utf-8") as _f:
                            _status_json = json.load(_f)
                        _status = _status_json["status"]
                    except ValueError as error_found:
                        log.print_warn(f"Error parsing status json file {_status_json_file} :: {error_found}, status is unknown")
                        _status = "unknown"
                else:
                    log.print_warn(f"Status json file is not found {_status_json_file}, status is unknown")
                    _status = "unknown"
                log.print_info(f"Exadata version {_version}, download status {_status}")
                if _status == "success" or _status == "fail" or _status == "unknown":
                    log.print_info(f"Remove exadata common tar bundle {_filename}")
                    _cmd_remove_tar = f"/usr/bin/rm -rf '{aExadataFolder}/{_filename}'"
                    _output, _status = safe_execute_local(shlex.split(_cmd_remove_tar))
                    if _status != 0:
                        log.print_warn(f"Unable to purge '{aExadataFolder}/{_filename}' {_output}")
                else:
                    log.print_warn(f"Bundle {_filename} is not in success or fail state, skipping it")


    def remove_exasplice_tarballs(self, aExadataFolder):
        """
        Remove exasplice bundles
        Ex. exadata_exasplice_230209.1_cell_22.1.7.0.0.230113_tar_xvf_in_exacloud_root_directory.tar
        """
        log.print_info("Removing leftover exasplice bundles")
        for _filename in os.listdir(aExadataFolder):
            if re.match("^exadata_exasplice_[0-9]{6,6}(|\.[0-9])_cell_[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\.[0-9]{6,6}(|\.[0-9])_tar_xvf_in_exacloud_root_directory.tar$", _filename):
                log.print_info(f"Remove exasplice tar bundle {_filename}")
                _cmd_remove_tar = f"/usr/bin/rm -rf '{aExadataFolder}/{_filename}'"
                _output, _status = safe_execute_local(shlex.split(_cmd_remove_tar))
                if _status != 0:
                    log.print_warn(f"Unable to purge '{aExadataFolder}/{_filename}' {_output}")


def create_directory(aFolder):
    if not os.path.exists(aFolder):
        os.makedirs(aFolder)


def load_properties(aFilePath, aDelim='=', aCommentChar='#'):
    """
    Read the file passed as parameter as a properties file.
    """
    props = {}
    with open(aFilePath, "rt") as f:
        for line in f:
            l = line.strip()
            if l and not l.startswith(aCommentChar):
                key_value = l.split(aDelim)
                key = key_value[0].strip()
                value = aDelim.join(key_value[1:]).strip().strip('"')
                props[key] = value
    return props


def get_proxy_detail(proxy = None):
    '''
    Returns the proxy hostname and it's port if it is http proxy.
    '''
    proxyHost = None
    proxyPort = None
    log.print_info(f"User given proxy details :: {proxy}")
    if proxy is not None and proxy.strip():
        if re.match("https://", proxy):
            log.print_warn(f"https proxy {proxy} is not supported for oci communication.")
        elif re.match("^http://", proxy):
            proxy = re.split("http://", proxy)
            proxyHost, proxyPort = re.split(":", proxy[1])
            if proxyPort is None:
                proxyPort = 80
                log.print_info(f"proxyhost :: {proxyHost} and proxyport :: {proxyPort}")
        else:
            #If not starting with http assuming it is http
            if re.match(":", proxy):
                proxyHost, proxyPort = re.split(":", proxy)
            else:
                proxyHost = proxy
            #If user did not give port assuming 80, since it is http proxy.
            if proxyPort is None:
                proxyPort = 80
        log.print_info(f"proxyhost :: {proxyHost} and proxyport :: {proxyPort}")

    return proxyHost, proxyPort


def remove_folder(aFolder, asRoot = False):
    log.print_info(f"Removing {aFolder}")
    _cmd_remove_tar = f"/usr/bin/rm -rf '{aFolder}'"
    if asRoot:
        _cmd_remove_tar = f"sudo /usr/bin/rm -rf '{aFolder}'"
    _output, _status = safe_execute_local(shlex.split(_cmd_remove_tar))
    if _status != 0:
        log.print_warn(f"Unable to purge  '{aFolder}' {_output}")


def remove_folder_wild(aFolder):
    log.print_info(f"Removing {aFolder}")
    _cmd_remove_tar = f"/usr/bin/rm -rf {aFolder}"
    _output, _status = safe_execute_local(_cmd_remove_tar, shell=True)
    if _status != 0:
        log.print_warn(f"Unable to purge  '{aFolder}' {_output}")


def remove_complete_common_infra(aPatchPayloadsFolder, aExadataVersion):
    log.print_info(f"{aExadataVersion} exadata common infra version will be purged!")
    remove_folder(f"{aPatchPayloadsFolder}/{aExadataVersion}")

def remove_compute_version(aComputeFolder, aComputeVersion):
    log.print_info(f"{aComputeVersion} compute version will be purged!")
    remove_folder(f"{aComputeFolder}/{aComputeVersion}")

def remove_exasplice_version(aPatchPayloadsFolder, aExadataVersion):
    log.print_info(f"{aExadataVersion} exasplice version will be purged!")
    remove_folder(f"{aPatchPayloadsFolder}/{aExadataVersion}")
    remove_folder(f"{aPatchPayloadsFolder}/../../cpsos/exasplice_{aExadataVersion}")


def remove_common_infra(aPatchPayloadsFolder, aExadataVersion, aComputeDetails, aExaspliceDetails):
    log.print_info(f"{aExadataVersion} exadata version will be purged!")
    remove_folder(f"{aPatchPayloadsFolder}/{aExadataVersion}/{'SwitchPatchFile'}")
    remove_folder(f"{aPatchPayloadsFolder}/{aExadataVersion}/{'Dom0YumRepository'}")
    if not aComputeDetails:
        log.print_info(f"{aExadataVersion} exadata common compute will be purged!")
        remove_folder(f"{aPatchPayloadsFolder}/{aExadataVersion}/{'DomuYumRepository'}")
        remove_folder(f"{aPatchPayloadsFolder}/{aExadataVersion}/{'DBPatchFile'}")
    if not aExaspliceDetails:
        log.print_info(f"{aExadataVersion} exadata exasplice (cell) will be purged!")
        remove_folder(f"{aPatchPayloadsFolder}/{aExadataVersion}/{'CellPatchFile'}")


def remove_system_image(aExadataFolder, aSystemImageFile):
    log.print_info(f"{aSystemImageFile} system image will be purged!")
    remove_folder(f"{aExadataFolder}/images/{aSystemImageFile}")


def remove_system_images(aExadataFolder, aExadataVersion, aCommonComputeDetails):
    if not aCommonComputeDetails:
        log.print_info(f"{aExadataVersion} system image will be purged!")
        remove_folder_wild(f"{aExadataFolder}/images/System.first.boot.{aExadataVersion}*.img.*")
    else:
        log.print_warn(f"{aExadataVersion} system image won't be purged, It's required for common compute!")


def remove_cpsos_version(aCPSOSFolder, aCPSOSVersion):
    log.print_info(f"{aCPSOSVersion} cpsos version will be purged!")
    remove_folder(f"{aCPSOSFolder}/{aCPSOSVersion}")


def safe_execute_local(aListCmd, shell=False):
    _status = 1
    log.print_debug(f"Command to execute : {' '.join(map(str, aListCmd))}")
    proc = subprocess.Popen(aListCmd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _output, _err = proc.communicate()
    try:
        _status = proc.returncode
    except:
        proc.kill()
        proc.wait()
        raise
    if _status is None:
        _status = 0
    if _status != 0:
        if _err:
            _output = _err
    if _output:
        _output = _output.decode("utf-8")
    return _output, _status


def active_process(aProcessName):
    log.print_info(f"Validating script process {aProcessName}...")
    _active_process = False
    _pid = os.getpid()
    _cmd_ps = "/usr/bin/ps -ef"
    _output, _status = safe_execute_local(shlex.split(_cmd_ps))
    if _status == 0:
        if _output:
            _process_list = _output.split("\n")
            log.print_info(f"Current script name {aProcessName}")
            _processes = [_process for _process in _process_list if aProcessName in _process
                          and "python" in _process and _process.split()[1] != str(_pid)]
            if len(_processes) > 0:
                _active_process = True
    else:
        log.print_warn("Failed validating process exadata_bundles_purge")
    return _active_process


def virtualization_type():
    '''
        XEN switch interfaces
            [root@scaqak01dv0804m ~]# ip addr show | grep stib
            24: stib1@ib1: <BROADCAST,MULTICAST,SLAVE,UP,LOWER_UP> mtu 65520 qdisc pfifo_fast master stbondib00 state UP group default qlen 256
            25: stib0@ib0: <BROADCAST,MULTICAST,SLAVE,UP,LOWER_UP> mtu 65520 qdisc pfifo_fast master stbondib00 state UP group default qlen 256
            [root@scaqak01dv0804m ~]# echo $?
            0

        KVM swith interfaces
            [root@scaqan03dv0811m ~]# ip addr show | grep stre
            4: stre0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 2300 qdisc mq state UP group default qlen 1000
                inet 192.168.35.241/23 brd 192.168.35.255 scope global stre0
            5: stre1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 2300 qdisc mq state UP group default qlen 1000
                inet 192.168.35.242/23 brd 192.168.35.255 scope global stre1
    '''
    log.print_info("Checking virtualization type (kvm/xen)...")
    _v_type = None
    _cmd_ibswitch = "/usr/sbin/ip addr show"
    log.print_info(f"Getting virtualization type : {_cmd_ibswitch}")
    _output, _status = safe_execute_local(shlex.split(_cmd_ibswitch))
    if _output:
        _switches_output = _output.strip().lower()
        _ib_switch = re.search("st.*ib.*", _switches_output)
        _roce_switch = re.search("st.*re.*", _switches_output)
        if _ib_switch:
            _v_type = virtualization_xen
        elif _roce_switch:
            _v_type = virtualization_kvm
    return _v_type


class MetadataFileSync:

    def __init__(self, aPatchDownload, aInputJsonName):
        self.__patch_download = aPatchDownload
        self.__input_json_name = aInputJsonName


    def mGetFileDetails(self, aFolderLocation, aFileName):
        """
          This method returns file details like size and checksum.

          dict returned example
          {
              file_name : "/u01/downloads//exadata//PatchPayloads/20.1.17.0.0.211221//DomuYumRepository/exadata_ol7_20.1.17.0.0.211221_Linux-x86-64.zip",
              file_size : "1.3G",
              sha256sum : "f1ebb4744bac543f2917a42030489da43d71f0336594c84d7b4f3e195581ccd6"
          }
        """
        _exadata_bundle_name = f"{aFolderLocation}/{aFileName}"
        log.print_info(f"Generating file details for {_exadata_bundle_name}")
        _exadata_bundle_size = "-1"
        _exadata_bundle_checksum = ""
        if os.path.exists(_exadata_bundle_name):
            log.print_info(f"Generating checksum for the patch file : {_exadata_bundle_name} ***")
            _cmd = f'/bin/sha256sum {_exadata_bundle_name} | /bin/cut -d" " -f1'
            _exadata_bundle_checksum, _status = safe_execute_local([_cmd], shell=True)
            _cmd = f"/bin/du -shL {_exadata_bundle_name} | /bin/awk '{{print $1}}'"
            _exadata_bundle_size, _status_size = safe_execute_local([_cmd], shell=True)
        _file_details = {
            "file_name": _exadata_bundle_name,
            "file_size": _exadata_bundle_size.strip(),
            "sha256sum": _exadata_bundle_checksum.strip()
        }
        return _file_details

    def mGetFileDetailsFromFolder(self, aExadataPayloadsLocation, aFolderName):
        _patch_folder = f"{aExadataPayloadsLocation}/{aFolderName}"
        log.print_info(f"Getting files details in folder {_patch_folder}")
        _file_detail_list = []
        if os.path.exists(_patch_folder):
            _exadata_patchpayloads_location = os.path.join(aExadataPayloadsLocation, aFolderName)
            _patch_files = os.listdir(_exadata_patchpayloads_location)
            for _file in _patch_files:
                _file_detail = self.mGetFileDetails(_patch_folder, _file)
                _file_detail_list.append(_file_detail)
        return _file_detail_list


    def mGetImageFile(self, aImageFolder, aPatchVersion):
        """
          This method gets image file, in older versions bundle unzips 2 files
          Ex.
          System.first.boot.21.2.10.0.0.220317.img.bz2
          System.first.boot.21.2.10.0.0.220317.kvm.img.bz2
        """
        _image_file = None
        _images_files = glob.glob(f"{aImageFolder}/System.first.boot.{aPatchVersion}*.img.*")
        if _images_files and len(_images_files) > 0:
            _image_file = os.path.basename(_images_files[0])
        return _image_file


    def mGetQuarterlyBundleDetails(self, aPatchDownload, aPatchVersion):
        """
          This method generates the quarterly entries for payloads metadata file
        """
        log.print_info("Quarterly exadata common bundle detail")
        # patch version example : 20.1.10.0.0.210506
        _patchpayload_image_location = f"{aPatchDownload}/PatchPayloads/{aPatchVersion}/"
        _image_file = self.mGetImageFile(f"{aPatchDownload}/images/", aPatchVersion)
        _image_data = {}
        if _image_file:
            _image_data = self.mGetFileDetails(f"{aPatchDownload}/images/", _image_file)
        _dom0_data = self.mGetFileDetailsFromFolder(_patchpayload_image_location, "Dom0YumRepository")
        _cell_data = self.mGetFileDetailsFromFolder(_patchpayload_image_location, "CellPatchFile")
        _domu_data = self.mGetFileDetailsFromFolder(_patchpayload_image_location, "DomuYumRepository")
        _switch_data = self.mGetFileDetailsFromFolder(_patchpayload_image_location, "SwitchPatchFile")
        if len(_switch_data) == 0 and len(_cell_data) > 0:
            # Return monthly bundle details
            # if switch data entry is not present and cell data entry is there
            return self.mGetExaspliceBundleDetails(aPatchDownload, aPatchVersion, _cell_data)
        else:
            _bp_date = re.search('((\d{6}\.\d+)$)|(\d{6}$)', aPatchVersion).group()
            _bp_name = re.search('\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{1,2}', aPatchVersion).group()
            # Return quarterly bundle details
            _quarterly_exadata_common_entry = {
                "imageVersion": aPatchVersion,
                "patchType":  "quarterly",
                "targetTypes":[
                    "dom0, domu, cell, switch"
                ],
                "serviceType":"EXACC",
                "bp_date": _bp_date,
                "bp_name": _bp_name,
                "imageData": _image_data,
                "dom0data": _dom0_data,
                "celldata": _cell_data,
                "domudata": _domu_data,
                "switchdata": _switch_data
            }
        log.print_info(f"Quarterly exadata common entry: {_quarterly_exadata_common_entry['imageVersion']}")
        return _quarterly_exadata_common_entry

    def mGetExaspliceBundleDetails(self, aPatchDownload, aPatchVersion, aCellData=None):
        """
          This method generates the monthly entries for payloads metadata file
        """
        log.print_info(f"INFO - Monthly exadata bundle detail {aPatchVersion}")
        _monthly_exadata_entry = {
            "imageVersion": aPatchVersion,
            "patchType": "monthly",
            "serviceType": "EXACC"
        }
        if aCellData:
            _bp_date = re.search('((\d{6}\.\d+)$)|(\d{6}$)', aPatchVersion).group()
            _bp_name = re.search('\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{1,2}', aPatchVersion).group()
            _monthly_exadata_entry["celldata"] = aCellData
            _monthly_exadata_entry["targetTypes"] = ["cell"]
            _monthly_exadata_entry["bp_date"] = _bp_date
            _monthly_exadata_entry["bp_name"] = _bp_name
        else:
            _patchpayload_image_location = f"{aPatchDownload}/PatchPayloads/{aPatchVersion}/"
            _dom0_data = self.mGetFileDetailsFromFolder(_patchpayload_image_location, "ExaspliceRepository")
            _monthly_exadata_entry["dom0data"] = _dom0_data
            _monthly_exadata_entry["targetTypes"] = ["dom0"]
            _monthly_exadata_entry["bp_date"] = aPatchVersion
            _monthly_exadata_entry["bp_name"] = aPatchVersion

        return _monthly_exadata_entry


    def mSyncPatchCommonJson(self):
        """
          This method regenerate payloads metadata file adding missing entries syncing with PatchPayloads
        """
        log.print_info(f"Generating {self.__input_json_name} metadata file")

        _json_file = os.path.join(bundles_list_folder, self.__input_json_name)
        _dict_content = {}
        if os.path.exists(_json_file):
            with open(_json_file) as json_read:
                try:
                    _dict_content = json.load(json_read)
                except JSONDecodeError as e:
                    log.print_warn(f"JSONDecodeError occurred: {e}")
                    log.print_warn(f"Bad format - Metadata file {self.__input_json_name}. will be regenerated!")
                    _dict_content = {"payloads":[]}
        else:
            _dict_content = {"payloads":[]}

        _payloads = _dict_content["payloads"]

        _exadata_patchpayloads_location = os.path.join(self.__patch_download, exadata_version_folder, "PatchPayloads")
        _patch_versions = os.listdir(_exadata_patchpayloads_location)
        for _patch_version in _patch_versions:
            # Format of the folder is 20.1.10.0.0.210506
            _patch_type = "common"
            # Exasplice entries for dom0 E.g. 210506 or 210506.1
            is_exasplice = re.search('^(((\d{6}\.\d+)$)|(\d{6}$))', _patch_version)
            if is_exasplice:
                _patch_type = "exasplice"
            if len([_version for _version in _payloads if _version["imageVersion"] == _patch_version]) == 0:
                _re_out = re.match('\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{1,2}', _patch_version)
                """
                  Exadada common versions to be checked
                    [ecra@scaqan17cps02 PatchPayloads]$ ll
                    total 0
                    drwxr-xr-x 7 ecra dba 143 Jun  9  2022 21.2.12.0.0.220513
                    drwxr-xr-x 7 ecra dba 143 Jul 26  2022 21.2.13.0.0.220602
                    drwxr-xr-x 6 ecra dba 120 Mar  7 02:02 21.2.15.0.0.220816
                """
                if _re_out:
                    if _patch_type == "common":
                        _patch_version_details = self.mGetQuarterlyBundleDetails(
                            f"{self.__patch_download}/{exadata_version_folder}", _patch_version)
                    else:
                        _patch_version_details = self.mGetExaspliceBundleDetails(
                            f"{self.__patch_download}/{exadata_version_folder}", _patch_version)
                    _payloads.append(_patch_version_details)

        _dict_content["payloads"] = sorted(_payloads, key=lambda _version: _version["bp_date"])

        with open(_json_file, 'w') as outfile:
            json.dump(_dict_content, outfile, indent=4)
        return 0

    def mRemovePurgedCommmonJson(self):
        """
          This method removes entries in the metadata file that have been purged
        """
        log.print_info(f"Removing purged versions from {self.__input_json_name}")
        _json_file = os.path.join(bundles_list_folder, self.__input_json_name)
        _dict_content = {}
        if os.path.exists(_json_file):
            with open(_json_file) as json_read:
                _dict_content = json.load(json_read)
        else:
            return

        _payloads = _dict_content["payloads"]
        _new_payloads = []

        for _patch_version in _payloads:
            _exadata_version_location = os.path.join(self.__patch_download, exadata_version_folder, "PatchPayloads",
                                                     _patch_version["imageVersion"])
            if not os.path.exists(_exadata_version_location):
                log.print_info(f"Removing {_patch_version['imageVersion']} entry from metadata json file")
            else:
                _new_payloads.append(_patch_version)

        _dict_content["payloads"] = sorted(_new_payloads, key=lambda _version: _version["bp_date"])

        with open(_json_file, 'w') as outfile:
            json.dump(_dict_content, outfile, indent=4)


'''
Format of folder to purge
/opt/oci/exacc/exacloud/InfraPatchBase/dbserver.patch.zip_exadata_ovs_23.1.3.0.0.230613_Linux-x86-64.zip/
                                       dbserver.patch.zip_exadata_ol7_23.1.3.0.0.230613_Linux-x86-64.zip/
                                       dbserver.patch.zip_exadata_ol8_23.1.3.0.0.230613_Linux-x86-64.zip/
                                       dbserver.patch.zip_exadata_ol9_23.1.3.0.0.230613_Linux-x86-64.zip/
'''
def mPurgeExtractedExadataVersion(_exadata_version_config):
    log.print_info(f"Removing extracted exadata common version from {cps_infrapatch_base}")
    if not (os.path.exists(cps_infrapatch_base) and os.path.isdir(cps_infrapatch_base)):
        log.print_warn(f"Extracted exadata common version folder does not exist {cps_infrapatch_base}")
        return
    _extracted_exadata_version_folders = os.listdir(f"{cps_infrapatch_base}")
    if len(_extracted_exadata_version_folders) > 0:
        for _extracted_exadata_version in _extracted_exadata_version_folders:
            _exadata_version = None
            _re_result = re.search('\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{1,2}.((\d{6}\.\d+)|\d{6})',_extracted_exadata_version)
            if _re_result:
                log.print_info(f"Exadata version folder {_extracted_exadata_version}")
                _exadata_version = _re_result.group()
                log.print_info(f"Extracted exadata version {_exadata_version}")
            else:
                log.print_warn(f"Exadata version not found {_extracted_exadata_version}, folder will be skipped")

            if _exadata_version:
                if not _exadata_version_config.search_common_infra(_exadata_version):
                    _ls_progress_file_command = f"sudo /usr/bin/ls {cps_infrapatch_base}/{_extracted_exadata_version}/*_progress.txt"
                    _output, _status = safe_execute_local(_ls_progress_file_command, shell=True)
                    if _status == 0:
                        log.print_warn(f"Patch in progress for {_extracted_exadata_version}")
                    else:
                        log.print_info(f"{_extracted_exadata_version} extracted version folder will be purged!")
                        remove_folder(f"{cps_infrapatch_base}/{_extracted_exadata_version}", True)


def main():
    global log, statLog
    parse = OptionParser()
    parse.add_option("-m", "--metadatafile", dest="metadatafile", help="Input for exadata bundle json file.")
    (options, args) = parse.parse_args()
    _metadatafile = options.metadatafile

    _username = getpass.getuser().upper()
    if _username != "ECRA":
        print(f"ERROR - The user ({_username}) executing exadata_bundle_purge must be ECRA.\n")
        exit(1)

    _exadata_folder = f"{bundles_list_folder}/{exadata_version_folder}"

    if not _metadatafile:
        _metadatafile = f"{bundles_list_folder}/{exadata_bundle_metadata}"

    log = PurgeLog(_exadata_folder, "exadata_bundles_purge.log", 5000000, 1)
    statLog = PurgeLog(_exadata_folder, "status.log", 2000000, 1)

    if active_process(exadata_purge_name):
        log.print_error("There is another active process of exadata_bundles_purge.py!")
        exit(0)

    log.print_info("Start exadata bundle purge process ...")

    log.print_debug(f"PatchPayload folder {_exadata_folder}")

    _exadata_version_config = ExadataVersionConfig(f"{retention_policy_folder}/{bundles_list_file}")
    _config_file_loaded = _exadata_version_config.load_file()
    if not _config_file_loaded:
        exit(1)

    # Exadata common, compute common, exasplice purge
    _patch_payloads = f"{_exadata_folder}/PatchPayloads"
    if os.path.exists(_patch_payloads) and os.path.isdir(_patch_payloads):
        _exadata_version_folders = os.listdir(f"{_patch_payloads}")
        if len(_exadata_version_folders) > 0:
            for _exadata_version in _exadata_version_folders:
                '''
                [ecra@scaqan17cps01 PatchPayloads]$ ll
                total 0
                drwxr-xr-x 3 ecra dba  35 May 16 09:57 21.2.9.0.0.220216    <<<< Exadata version
                drwxr-xr-x 3 ecra dba  37 Mar 24 01:19 21.3.0.0.0.211115    <<<< Exadata version
                drwxr-xr-x 4 ecra dba  64 Apr  8 08:32 220404               <<<< Exasplice version
                drwxr-xr-x 4 ecra dba  64 May 13 16:00 220504               <<<< Exasplice version
                '''
                is_exasplice = re.search('^(((\d{6}\.\d+)$)|(\d{6}$))', _exadata_version)
                if is_exasplice:
                    log.print_info(f"Exasplice version {_exadata_version}")
                    if not _exadata_version_config.search_exasplice(_exadata_version):
                        remove_exasplice_version(_patch_payloads, _exadata_version)
                else:
                    _re_out = re.match('\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{1,2}', _exadata_version)
                    if _re_out:
                        log.print_debug(f"Exadata version {_exadata_version}")
                        if not _exadata_version_config.search_common_infra(_exadata_version):
                            _common_compute_details = _exadata_version_config.search_common_compute(_exadata_version)
                            _exasplice_details = _exadata_version_config.search_exasplice(_exadata_version)
                            if not _common_compute_details and not _exasplice_details:
                                remove_complete_common_infra(_patch_payloads, _exadata_version)
                            else:
                                remove_common_infra(_patch_payloads, _exadata_version, _common_compute_details,
                                                    _exasplice_details)
                            _system_image_details = _exadata_version_config.search_system_image(_exadata_version)
                            if not _system_image_details:
                                remove_system_images(_exadata_folder, _exadata_version, _common_compute_details)
            statLog.print_info("Common Infra purge executed successful!")
        else:
            log.print_warn("There isn't any version in the PatchPayloads folder!")
    else:
        log.print_warn("PatchPayloads folder does not exist!")

    # Purge system images
    _system_image_folder = f"{_exadata_folder}/images"
    if os.path.exists(_system_image_folder) and os.path.isdir(_system_image_folder):
        log.print_info(f"Start listing system images folder {_system_image_folder}")
        _system_images_files = os.listdir(f"{_system_image_folder}")
        if len(_system_images_files) > 0:
            for _system_images_file in _system_images_files:
                _system_image_version_re = re.search('(\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{6})(.\d{1,2})*', _system_images_file)
                if _system_image_version_re:
                    log.print_info(f"System image {_system_images_file} found")
                    _system_image_version = _system_image_version_re.group()
                    log.print_info(f"Image version {_system_image_version}")
                    # Validate purge policy json file
                    _system_image_details = _exadata_version_config.search_system_image(_system_image_version)
                    _common_infra_details = _exadata_version_config.search_common_infra(_system_image_version)
                    _common_compute_details = _exadata_version_config.search_common_compute(_system_image_version)
                    if not _system_image_details and not _common_infra_details and not _common_compute_details:
                        remove_system_images(_exadata_folder, _system_image_version, None)
        # Remove unused system images by virtualization type
        _system_images_files = os.listdir(f"{_system_image_folder}")
        if len(_system_images_files) > 0:
            _vir_type = virtualization_type()
            if not _vir_type:
                log.print_warn("Virtualization type is not found!")
            else:
                log.print_info(f"Virtualization type {_vir_type}!")
                for _system_images_file in _system_images_files:
                    _system_image_version_re = re.search('(\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{6})(.\d{1,2})*', _system_images_file)
                    if _system_image_version_re:
                        # kvm and rtg images are not required in xen environments
                        if _vir_type == virtualization_xen and (_system_images_file.find("kvm") > -1 or _system_images_file.find("rtg") > -1):
                            remove_system_image(_exadata_folder, _system_images_file)
                        # kvm and rtg images are required in kvm environments
                        if _vir_type == virtualization_kvm and not (_system_images_file.find("kvm") > -1) and not _system_images_file.find("rtg") > -1:
                            remove_system_image(_exadata_folder, _system_images_file)

    # CPSOS version purge
    _cpsos_folder = f"{bundles_list_folder}/{cpsos_version_folder}"
    if os.path.exists(_cpsos_folder) and os.path.isdir(_cpsos_folder):
        log.print_info(f"CPSOS folder - {_cpsos_folder}")
        _cpsos_version_folders = os.listdir(_cpsos_folder)
        if len(_cpsos_version_folders) > 0:
            for _cpsos_version in _cpsos_version_folders:
                if os.path.isdir(f"{_cpsos_folder}/{_cpsos_version}"):
                    _re_out_exasplice = re.match('exasplice_[0-9]{6}', _cpsos_version)
                    _re_out = re.match('\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{1,2}', _cpsos_version)
                    if _re_out or _re_out_exasplice:
                        log.print_info(f"CpsOS version {_cpsos_version}")
                        _cpsos_version_details = _exadata_version_config.search_cpsos(_cpsos_version)
                        if not _cpsos_version_details:
                            remove_cpsos_version(_cpsos_folder, _cpsos_version)
            statLog.print_info("CPSOS purge executed successful!")
        else:
            log.print_warn("There isn't any version in the CPSOS folder!")
    else:
        log.print_warn("CPSOS folder does not exist!")

    # Compute folder purge
    _compute_folder = f"{bundles_list_folder}/{compute_folder}"
    if os.path.exists(_compute_folder) and os.path.isdir(_compute_folder):
        _compute_folders = os.listdir(f"{_compute_folder}")
        if len(_compute_folders) > 0:
            log.print_info(f"Compute folder - {_compute_folder}")
            for _compute_version in _compute_folders:
                _re_out = re.match('\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{1,2}', _compute_version)
                if _re_out:
                    log.print_debug(f"Compute version {_compute_version}")
                    if not _exadata_version_config.search_common_compute(_compute_version):
                        remove_compute_version(_compute_folder, _compute_version)
            statLog.print_info("Compute purge executed successful!")
        else:
            log.print_warn("There isn't any version in the compute folder!")
    else:
        log.print_warn("Compute folder does not exist!")

    # Remove old exadata tar balls
    # Validate no managerepo script is running
    if not active_process(f"{managerepo_name}.{'py'}"):
        _exadata_version_config.remove_exadata_tarballs(_exadata_folder)
        _exadata_version_config.remove_exasplice_tarballs(_exadata_folder)
    else:
        log.print_info("Managerepo is running, skip leftover exadata common bundles!")

    # Purge extracted exadata common vesion
    # when cps is used as a launch node
    mPurgeExtractedExadataVersion(_exadata_version_config)

    _metadata_file_sync = MetadataFileSync(bundles_list_folder, exadata_bundle_metadata)
    _metadata_file_sync.mSyncPatchCommonJson()
    _metadata_file_sync.mRemovePurgedCommmonJson()

    _exadata_version_config.metadata_file_sync(_metadatafile)
    statLog.print_info(f"Metadata file {_metadatafile} updated!")


if __name__ == '__main__':
    main()
