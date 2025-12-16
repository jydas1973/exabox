#!/bin/bash
#
# $Header: ecs/exacloud/exabox/infrapatching/test/cicd/scripts/imagerefresher.sh /main/11 2024/12/10 09:03:44 araghave Exp $
# Copyright (c) 2020, 2024, Oracle and/or its affiliates.
#
#    NAME
#      imagerefresher.sh
#
#    DESCRIPTION
#      This shell script used in automation to download patch payloads in exacloud and register with ecra.
#---------------------------------------------------------------------------------------------------------------------------
# INPUT        :  -i <ECRA_INSTALL_ROOT>
#                    This is a mandatory parameter. The parameter value is the name of the folder where ecra is installed.
#                    Suppose, if ECRA is installed in /scratch/$USER/ecra_installs/automation, then /scratch/$USER/ecra_installs/automation
#                    should be passed as parameter value.
#              :  -v <ABSOLUTE_URL_OF_QUARTERLY_PATCH_BUNDLE>
#                    This is an optional parameter. The parameter value is the exadata bundle version's complete download url.
#                    Note that either of -v (Exadata bundle) or -e (Exasplice bundle) options are mandatory but not together
#              :  -d <DOWNLOAD_LATEST_DBSERVER.PATCH.ZIP>
#                    This is an optional parameter. The parameter value is used to decide whether to download latest dbserver.patch.zip into
#                    ${EXACLOUD_LOCATION}PatchPaylods/DBPatchFile.  When "Yes" is specified, latest dbserver.patch.zip gets downloaded 
#                    to ${EXACLOUD_LOCATION}/PatchPayloads/DBPatchFile and exits. When no value is specified or when "No" is specified, latest 
#                    dbserver.patch.zip is not downloaded.
#              :  -b <ADE_VIEW_NAME>
#                    This is an optional parameter. The parameter value is the ade view name from where latest PrepareExadataReleaseTarball.sh is 
#                    used to download latest dbserver.patch.zip.
#                    If this option is not specified, ecrainstall view name is used which is present in current automation machine.
#              :  -e <ABSOLUTE_URL_OF_MONTHLY_PATCH_BUNDLE>
#                    This is an optional parameter. The parameter value is the exasplice bundle version's complete download url.
#                    Note that either of -v (Exadata bundle) or -e (Exasplice bundle) options are mandatory but not together
#
# Note:-
# The following are the examples for the usage of the script.
#
# imagerefresher.sh -i /scratch/sdevasek/ecra_installs/cicd
#   Here the script is going to download and register the latest patch payload with ecra,
#    assuming ecra is installed in /scratch/$USER/ecra_installs/cicd directory.
#
# imagerefresher.sh -i /scratch/sdevasek/ecra_installs/cicd -v https://objectstorage.us-phoenix-1.oraclecloud.com/p/5B8SC46avbBy2vdHwBkQxxK9ixruuA7bXHSrf3Cf2Ffn_FCDKBNy36QM1RLvDGUA/n/exadata/b/ECRA-Software/o/exadata_common_22.1.11.0.0.230516_tar_xvf_in_exacloud_root_directory_atp_exacs.tar
#   Here the script is going to download and register 22.1.11.0.0.230516 exadata bundle with ecra,
#    assuming ecra is installed in /scratch/$USER/ecra_installs/cicd directory.
#
# imagerefresher.sh -i /scratch/sdevasek/ecra_installs/cicd -d yes
#   Here the script is going to download latest dbserver.patch.zip into ${EXACLOUD_LOCATION}/PatchPayloads/DBPatchFile directory
#
# imagerefresher.sh -i /scratch/sdevasek/ecra_installs/cicd -e https://objectstorage.us-phoenix-1.oraclecloud.com/p/5B8SC46avbBy2vdHwBkQxxK9ixruuA7bXHSrf3Cf2Ffn_FCDKBNy36QM1RLvDGUA/n/exadata/b/ECRA-Software/o/exadata_exasplice_230607_cell_22.1.11.0.0.230516_tar_xvf_in_exacloud_root_directory.tar
#   Here the script is going to download and register exasplice DOM0 version: 230607 and exasplice CELL version: 22.1.11.0.0.230516 with ecra
#    assuming ecra is installed in /scratch/$USER/ecra_installs/cicd directory.
#
# This script downloads latest dbserver.patch.zip into ${EXACLOUD_LOCATION}/PatchPayloads/DBPatchFile directory when option d is specified
# otherwise updates the exadata bundle with the below steps
#  1) Download the given exadata/exasplice bundle version from oss
#  2) In the case of exadata bundle, patch all targets to the currently registered version.
#  3) Untar the patch payload to exacloud location.
#  4) Do exaversion register for all the targets.
#  5) In the case of exadata bundle, purge exadata patch payload that was used earlier.
#
# The script exits with either success or failure code. i.e.,
#   exit 0 means, success, when script successfully completes all of the above mentioned steps.
#   exit 1 means, failure, when scipt fails in any of the above mentioned steps.
#-----------------------------------------------------------------------------
#    MODIFIED   (MM/DD/YY)
#    araghave    11/22/24 - Enh 37241595 - TEST CHANGES TO REPLACE ALL IBSWITCH
#                           REFERENCE WITH GENERIC SWITCH REFERENCES IN INFRA
#                           PATCHING TEST CODE
#    apotluri    02/13/24 - Bug 36270809 - INFRAPATCH TEST AUTOMATION : USE
#                           ABSOLUTE OSS URL FOR BUNDLE DOWNLOAD AND SKIP
#                           SWITCH PATCHING FOR R1 ENV IN IMAGEREFRESHER
#                           SCRIPT
#    apotluri    02/13/24 - Bug 36270809 - INFRAPATCH TEST AUTOMATION: ISSUES
#                           IN IMAGEREFRESHER SCRIPT
#    emekala     07/31/23 - ENH 35656608 - INFRAPATCHING TEST AUTOMATION -
#                           imagerefresher.sh requires changes to handle
#                           certain cases
#    emekala     07/06/23 - ENH 35573121 - INFRAPATCHING TEST AUTOMATION -
#                           Monthly patching download url keeps changing hence
#                           accept complete url instead of version number
#    emekala     04/26/23 - ENH 35328381 - INFRAPATCHING TEST AUTOMATION -
#                           UPDATE IMAGEREFRESHER SCRIPT TO UPTAKE AND REGISTER
#                           EXASPLICE BUNDLE
#    apotluri    03/30/23 - ENH 34862477 - UPDATE INFRAPATCHING TEST CODE TO
#			    DOWNLOAD SPECIFIC VERSION OF EXADATA PATCH PAYLOAD
#			    IN X9M R1 ENV 
#    sdevasek    01/23/23 - ENH 35005477 - ENABLE DOMU TEST TO VALIDATE EXADATA
#                           ERROR FRAMEWORK AND UPDATE IMAGE REFRESHER SCRIPT
#                           TO USE NEW ECRA INSTALL FOLDER PARAM
#    sdevasek    09/14/22 - ENH 34547838 - TEST ADDITION TO AUTOMATION
#                           FOR VALIDATION OF NEW ERROR CODES FROM PATCH_MGR
#    sdevasek    04/11/22 - Enh34036744 - PROVIDE OPTION TO USE SPECIFIC
#                           VERSION OF EXADATA BUNDLE IN AUTOMATION
#    sdevasek    01/07/22 - Bug33722164 - RESTART ECRA SERVICES WHEN NOT RUNNING
#                           DURING TEST JOB EXECUTION IN AUTOMATION
#    sdevasek    11/23/21 - Enh33504205 - IMAGE REFRESHING INCLUSION IN
#                           INFRAPATCHING AUTOMATION

set -x

EXA_IMAGE_BINARY_FULL_PATH_URL=""
EXADATA_IMAGE_VERSION_TO_BE_DOWNLOADED=""
EXASPLICE_IMAGE_VERSION_TO_BE_DOWNLOADED=""
EXA_IMAGE_BINARY_VERSION=""
DOWNLOAD_LATEST_DBSERVER_PATCH=""
ADE_VIEW_NAME=""
PREPAREEXADATARELEASETARBALL_SCRIPT_PATH=""
ECRA_ENDPOINT=""
ECRA_USER=""
ECRA_PASSWD=""
SERVICE_TYPE=""
ECRA_INSTALL_ROOT=""
TEST_INFRAPATCHING_CONFIG_FILE_LOCATION=""
TEST_PAYLOAD_CONFIG_JSON_FILE_LOCATION=""
EXACLOUD_LOCATION=""
EXADATA_IMAGE_VERSION_TO_BE_PURGED=""
REGISTERED_EXA_IMAGE_VERSIONS=""
INFRAPATCHING_TEST_LOCATION=""
RM_CMD=$(whereis -b rm | awk  '{print $2}')
PATCH_TYPE=""
EXASPLICE_DOM0_IMAGE_BINARY_VERSION=""
EXASPLICE_CELL_IMAGE_BINARY_VERSION=""

function usage() {
    echo "Usage: $0 [ -i ECRA_INSTALL_ROOT ] [ -v ABSOLUTE_URL_OF_QUARTERLY_PATCH_BUNDLE | -e ABSOLUTE_URL_OF_MONTHLY_PATCH_BUNDLE ] [ -d DOWNLOAD_LATEST_DBSERVER.PATCH.ZIP ] [ -b ADE_VIEW_NAME ] "
}

function exit_abnormal() {
    usage
    exit 1
}


#
# General parameter validation is done first, like no of parameters and parameter names etc.
#

# If no parameter is passed, display the usage.
if [ $# -eq 0 ]; then
    exit_abnormal
fi

while getopts ":i:v:d:b:e:" options; do

    case "${options}" in
        i)
            ECRA_INSTALL_ROOT=${OPTARG}
            if [[ ${ECRA_INSTALL_ROOT:0:1} == "-" ]]; then
                exit_abnormal
            fi
            ;;
        v)
            EXADATA_IMAGE_VERSION_TO_BE_DOWNLOADED=${OPTARG}
            if [[ ${EXADATA_IMAGE_VERSION_TO_BE_DOWNLOADED:0:1} == "-" ]]; then
                exit_abnormal
            fi
            PATCH_TYPE="exadata"
            EXA_IMAGE_BINARY_VERSION=${EXADATA_IMAGE_VERSION_TO_BE_DOWNLOADED}
            if [[ ${EXADATA_IMAGE_VERSION_TO_BE_DOWNLOADED} =~ ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+) ]]; then
                EXA_IMAGE_BINARY_VERSION="${BASH_REMATCH[1]}"
            else
                echo "Version number not found in ${EXADATA_IMAGE_VERSION_TO_BE_DOWNLOADED}"
                exit_abnormal
            fi

            EXA_IMAGE_BINARY_FULL_PATH_URL="${EXADATA_IMAGE_VERSION_TO_BE_DOWNLOADED}"
            ;;
        d)
            DOWNLOAD_LATEST_DBSERVER_PATCH=${OPTARG}
            if [[ ${DOWNLOAD_LATEST_DBSERVER_PATCH:0:1} == "-" ]]; then
                exit_abnormal
            fi
            ;;
        b)
            ADE_VIEW_NAME=${OPTARG}
            if [[ ${ADE_VIEW_NAME:0:1} == "-" ]]; then
                exit_abnormal
            fi
            ;;
        e)
            EXA_IMAGE_BINARY_FULL_PATH_URL=${OPTARG}
            if [[ ${EXA_IMAGE_BINARY_FULL_PATH_URL:0:1} == "-" ]]; then
                exit_abnormal
            fi
            PATCH_TYPE="exasplice"
            EXASPLICE_IMAGE_VERSION_TO_BE_DOWNLOADED=$(echo $EXA_IMAGE_BINARY_FULL_PATH_URL | awk -F 'exadata_exasplice_|_tar_xvf_' '{print $2}')
            EXA_IMAGE_BINARY_VERSION=${EXASPLICE_IMAGE_VERSION_TO_BE_DOWNLOADED}
            EXASPLICE_DOM0_IMAGE_BINARY_VERSION=$(eval echo "$EXA_IMAGE_BINARY_VERSION" | awk -F '_cell' '{print $1}')
            EXASPLICE_CELL_IMAGE_BINARY_VERSION=$(eval echo "$EXA_IMAGE_BINARY_VERSION" | awk -F '_cell_' '{print $2}')
            ;;

        *)
            exit_abnormal
            ;;
    esac

done

# Validate -i parameter
# -i is the mandatory parameter
if [ -z "$ECRA_INSTALL_ROOT" ]; then
    echo "Error: -i is the mandatory parameter to be passed."
    exit_abnormal
else
    if [ ! -d "$ECRA_INSTALL_ROOT" ]; then
        echo "${ECRA_INSTALL_ROOT} does not exist. Please check the parameter value ${ECRA_INSTALL_ROOT} passed for ECRA install folder is correct."
        exit 1
    fi
    EXACLOUD_LOCATION="${ECRA_INSTALL_ROOT}/mw_home/user_projects/domains/exacloud"

    if [ ! -d "${EXACLOUD_LOCATION}" ]; then
        echo "${EXACLOUD_LOCATION} does not exist. Please make sure ${ECRA_INSTALL_ROOT} passed for ECRA install folder is correct."
        return 1
    fi
fi

# Its mandatory to pass either of exadata bundle version or exasplice bundle version but not together
if ( [ -z "$EXADATA_IMAGE_VERSION_TO_BE_DOWNLOADED" ] && [ -z "$EXASPLICE_IMAGE_VERSION_TO_BE_DOWNLOADED" ] ) ||  ( [ ! -z "$EXADATA_IMAGE_VERSION_TO_BE_DOWNLOADED" ] && [ ! -z "$EXASPLICE_IMAGE_VERSION_TO_BE_DOWNLOADED" ] ); then
    echo -e '\nPlease provide either of -v or -e options. Both these options together not supported!\n'
    exit_abnormal
fi

echo "$PATCH_TYPE bundle version ${EXA_IMAGE_BINARY_VERSION} is chosen for downloading."

# -d is the optional parameter
if [ ! -z "$DOWNLOAD_LATEST_DBSERVER_PATCH" ]; then
   # Convert to lowercase
   DOWNLOAD_LATEST_DBSERVER_PATCH=`echo "$DOWNLOAD_LATEST_DBSERVER_PATCH" | awk '{ print tolower($1) }'`

   if [[ "${DOWNLOAD_LATEST_DBSERVER_PATCH}" == 'yes' || "${DOWNLOAD_LATEST_DBSERVER_PATCH}" == 'no' ]]; then
        echo "The value chosen for DOWNLOAD_LATEST_DBSERVER_PATCH is ${DOWNLOAD_LATEST_DBSERVER_PATCH}."
    else
         echo "-d option can have only Yes/No values. The value chosen for DOWNLOAD_LATEST_DBSERVER_PATCH is ${DOWNLOAD_LATEST_DBSERVER_PATCH}."
         exit_abnormal
   fi
fi


# When download dbserver.patch.zip is chosen then validate for ade view name
if [[ "$DOWNLOAD_LATEST_DBSERVER_PATCH" == "yes" ]] ; then
    # -b is the optional parameter
    if [ -z "$ADE_VIEW_NAME" ]; then
        ADE_VIEW_NAME="ecrainstall"
    fi

    # validate view name
    PREPAREEXADATARELEASETARBALL_SCRIPT_PATH="/scratch/${USER}/view_storage/${USER}_${ADE_VIEW_NAME}/ecs/ecra/exacm/tools/PrepareExadataReleaseTarball.sh"
    echo "Complete path for PrepareExadataReleaseTarball.sh is ${PREPAREEXADATARELEASETARBALL_SCRIPT_PATH}"
    if [ ! -f "${PREPAREEXADATARELEASETARBALL_SCRIPT_PATH}" ]; then
        echo "${PREPAREEXADATARELEASETARBALL_SCRIPT_PATH} does not exist. Please provide the correct ade view name to use PrepareExadataReleaseTarball.sh."
        exit 1
    fi
fi

function prepare_env() {
    #
    # Sets the values for all the global variables declared and validates the exadata bundle version chosen.
    # Returns success(0) or failure(1) upon completion.
    #
    INFRAPATCHING_TEST_LOCATION="${ECRA_INSTALL_ROOT}/mw_home/user_projects/domains/exacloud/exabox/infrapatching/test"
    TEST_INFRAPATCHING_CONFIG_FILE_LOCATION="${INFRAPATCHING_TEST_LOCATION}/config/test_infrapatching.conf"
    TEST_PAYLOAD_CONFIG_JSON_FILE_LOCATION="${INFRAPATCHING_TEST_LOCATION}/config/payload.json"


    if [ ! -f "$TEST_INFRAPATCHING_CONFIG_FILE_LOCATION" ]; then
        echo "${TEST_INFRAPATCHING_CONFIG_FILE_LOCATION} does not exist. Please make sure ${TEST_INFRAPATCHING_CONFIG_FILE_LOCATION} exists."
        return 1
    fi

    if [ ! -f "$TEST_PAYLOAD_CONFIG_JSON_FILE_LOCATION" ]; then
        echo "${TEST_PAYLOAD_CONFIG_JSON_FILE_LOCATION} does not exist. Please make sure ${TEST_PAYLOAD_CONFIG_JSON_FILE_LOCATION} exists."
        return 1
    fi


    # The config file has name value pair,value is extracted by removing unwanted characters.
    # Eg:
    # The name value pair "ecrausername": "b3Bz",
    #  Here value for username b3Bz is extracted by removing ",:,ecrausername, spaces and comma
    # Similar approach is followed for other attributes as well.

    ECRA_USER=`grep "ecrausername" $TEST_INFRAPATCHING_CONFIG_FILE_LOCATION | sed  's/ //g;s/\"ecrausername\"://g;s/\"//g;s/,//g' |base64 --decode`

    if [ -z "$ECRA_USER" ]; then
        echo "Please check the value of username in ${TEST_INFRAPATCHING_CONFIG_FILE_LOCATION}."
        return 1
    fi

    ECRA_PASSWD=`grep "ecrapassword" $TEST_INFRAPATCHING_CONFIG_FILE_LOCATION | sed  's/ //g;s/\"ecrapassword\"://g;s/\"//g;s/,//g' |base64 --decode`

    if [ -z "$ECRA_PASSWD" ]; then
        echo "Please check the value of password in ${TEST_INFRAPATCHING_CONFIG_FILE_LOCATION}."
        return 1
    fi

    ECRA_ENDPOINT=`grep "ecraurl" $TEST_INFRAPATCHING_CONFIG_FILE_LOCATION | sed  's/ //g;s/\"ecraurl\"://g;s/\"//g;s/,//g'`

    if [ -z "$ECRA_ENDPOINT" ]; then
        echo "Please check the value of url in ${TEST_INFRAPATCHING_CONFIG_FILE_LOCATION}."
        return 1
    fi

    SERVICE_TYPE=`grep "serviceType" $TEST_PAYLOAD_CONFIG_JSON_FILE_LOCATION | sed  's/ //g;s/\"serviceType\"://g;s/\"//g;s/,//g'`

    if [ -z "$SERVICE_TYPE" ]; then
        echo "Please check the value of serviceType in ${TEST_PAYLOAD_CONFIG_JSON_FILE_LOCATION}."
        return 1
    fi

    IS_R1_ENV=`grep "is_r1_env" ${TEST_INFRAPATCHING_CONFIG_FILE_LOCATION} | awk -F '"' '{print $(NF-1)}'`

    if [ -z "$IS_R1_ENV" ]; then
        echo "Please check the value of is_r1_env in ${TEST_PAYLOAD_CONFIG_JSON_FILE_LOCATION}."
        return 1
    fi

    # Get the currently registered bundle version(s). At the end, after successful registraion of latest bundle (or specific bundle),
    # respective old bundle(s) will be purged.
    # The following steps are done to get the currently registered exadata bundle version
    #  1. Get the registered payload json by sending curl command to ECRA
    REGISTERED_EXA_IMAGE_VERSIONS=`curl --silent -u ${ECRA_USER}:${ECRA_PASSWD}  -k -X GET --header 'Content-Type: application/json' --header 'Accept: application/json' -d ' {"serviceType": "${SERVICE_TYPE}"}' ${ECRA_ENDPOINT}/exaversion/registration`

    if [ -z "$REGISTERED_EXA_IMAGE_VERSIONS" ]; then
        echo "Could not fetch registered exa versions."
        return 1
    fi

    # check only exadata bundle here as exasplice bundle has both dom0 and cell hence can't skip when either one of then is already registered
    # more over exasplice bundles are lighweight when compared to exadata bundles hence can be quickly downloaded
    if [ "$PATCH_TYPE" = "exadata" ]; then
        EXADATA_IMAGE_VERSION_TO_BE_PURGED="$(echo "${REGISTERED_EXA_IMAGE_VERSIONS}" | jq -r ' .ExaVersions | map(select(.patchType == "QUARTERLY") | .imageVersion) | unique[]')"
        if [ "$EXADATA_IMAGE_VERSION_TO_BE_PURGED" = "$EXA_IMAGE_BINARY_VERSION" ]; then
            echo "Current registered $PATCH_TYPE bundle version: $EXADATA_IMAGE_VERSION_TO_BE_PURGED is same as $PATCH_TYPE bundle version: $EXA_IMAGE_BINARY_VERSION chosen to download"
            return 1
        fi
    fi


    # Set the path to run pytest
    export PATH=$HOME/.local/bin:$PATH

    return 0
}

function register_patch_payload()
{
    #
    # Registers the patch payloads using ECRA REST API and returns success(0) or failure(1).
    #
    local is_exasplice="no"
    local register_exa_image_binary_version=${EXA_IMAGE_BINARY_VERSION}
    declare -A target_servicetype_mapping
    if [ "$PATCH_TYPE" = "exasplice" ]; then
      is_exasplice="yes"
      target_servicetype_mapping=(["dom0"]="${SERVICE_TYPE}" ["cell"]="${SERVICE_TYPE}")
    else
      if [[ "${IS_R1_ENV,,}" == "true" ]]; then
        target_servicetype_mapping=(["dom0"]="EXACOMPUTE" ["dom0\",\"cell"]="${SERVICE_TYPE}" ["domu"]="${SERVICE_TYPE}")
      else 
        target_servicetype_mapping=(["dom0"]="EXACOMPUTE" ["dom0\",\"cell"]="${SERVICE_TYPE}" ["domu"]="${SERVICE_TYPE}" ["switch"]="${SERVICE_TYPE}")
      fi
    fi
    declare -i result=0
    local service_type=""
    for TARGET in ${!target_servicetype_mapping[@]}
    do
        service_type="${target_servicetype_mapping[$TARGET]}"
        # exasplice has two separate versions one each for DOM0 and CELL.
        if [ "$PATCH_TYPE" = "exasplice" ]; then
          if [ "${TARGET}" == "dom0" ]; then
            register_exa_image_binary_version=$EXASPLICE_DOM0_IMAGE_BINARY_VERSION
          else
            register_exa_image_binary_version=$EXASPLICE_CELL_IMAGE_BINARY_VERSION
          fi
        fi
        exaversion_register_cmd="curl --silent  -u ${ECRA_USER}:${ECRA_PASSWD} -i -k -X POST --header 'Content-Type: application/json' --header 'Accept: application/json' -d ' {\"serviceType\": \"${service_type}\", \"exasplice\": \"${is_exasplice}\", \"targetTypes\": [\"${TARGET}\"], \"imageVersion\": \"${register_exa_image_binary_version}\"}' '${ECRA_ENDPOINT}/exaversion/registration'"

        cmd_output=$(eval "$exaversion_register_cmd")

        #Check for HTTP status 200
        if [[ "${cmd_output}" != *"HTTP/1.1 200"* ]] ;then
            echo "Patch payload registration failed for the image version ${register_exa_image_binary_version} when the target type is ${TARGET}."
            result=1
        fi
    done
    return $result
}

function check_ecra_services_status() {
    #
    # Checks ecra servcies status by looking for "result": "fail" string in the output of ecractl.sh status.
    #
    local status_output="/tmp/statusoutput.txt"
    ${RM_CMD} -f $status_output
    $ECRA_INSTALL_ROOT/ecractl.sh status | tee $status_output
    grep "\"result\": \"fail\"" $status_output
    if [ $? -ne 0 ];  then
        echo "All the ECRA services are up and running."
        return 0
    else
        echo "All the ECRA services are not up and running."
        return 1
    fi
}

function restart_ecra_services() {
    #
    # Restarts ECRA services.
    #
    $ECRA_INSTALL_ROOT/ecractl.sh stop
    if [ $? -ne 0 ]; then
        echo "Could not stop ECRA services."
        return 1
    else
        $ECRA_INSTALL_ROOT/ecractl.sh start
    fi
    return $?
}

function execute_patch_on_all_targets() {
    #
    # Upgrades all the targets to the current availble exadata version.
    # This is done before downloading the latest exadata bundle and registering with system.
    #

    chmod +w $TEST_PAYLOAD_CONFIG_JSON_FILE_LOCATION
    chmod +w $TEST_INFRAPATCHING_CONFIG_FILE_LOCATION
    cd $INFRAPATCHING_TEST_LOCATION
    if [[ "${IS_R1_ENV,,}" == "true" ]]; then
       test_executor_cmd="python3 -m pytest -vv -ra -s -m 'cell_patch_prereq_check or cell_patch or dom0_patch_prereq_check or dom0_patch or domu_patch_prereq_check or domu_patch' "
    else
       test_executor_cmd="python3 -m pytest -vv -ra -s -m 'cell_patch_prereq_check or cell_patch or dom0_patch_prereq_check or dom0_patch or switch_patch_prereq_check or switch_patch or domu_patch_prereq_check or domu_patch' "
    fi
    echo "Command used to execute to patch all targets is : ${test_executor_cmd}."
    eval "$test_executor_cmd"
    if [ $? -ne 0 ];  then
        echo "Failure occured while patching the targets."
        return 1
    fi
    return 0
}

function purge_exadata_payload()
{
    #
    # Purge the respective exadata/exasplice bundle that was downloaded and registered before refreshing to latest (or specific version).
    #
 
    if [ "$PATCH_TYPE" = "exadata" ]; then
       EXADATA_IMAGE_VERSION_TO_BE_PURGED="$(echo "${REGISTERED_EXA_IMAGE_VERSIONS}" | jq -r ' .ExaVersions | map(select(.patchType == "QUARTERLY") | .imageVersion) | unique[]')"
       EXCLUDE_VERSIONS_FROM_PURGE="$(echo "${REGISTERED_EXA_IMAGE_VERSIONS}" | jq -r ' .ExaVersions | map(select(.patchType == "MONTHLY") | .imageVersion) | unique[]')"
    elif [ "$PATCH_TYPE" = "exasplice" ]; then
       EXADATA_IMAGE_VERSION_TO_BE_PURGED="$(echo "${REGISTERED_EXA_IMAGE_VERSIONS}" | jq -r ' .ExaVersions | map(select(.patchType == "MONTHLY") | .imageVersion) | unique[]')"
       EXCLUDE_VERSIONS_FROM_PURGE="$(echo "${REGISTERED_EXA_IMAGE_VERSIONS}" | jq -r ' .ExaVersions | map(select(.patchType == "QUARTERLY") | .imageVersion) | unique[]')"
    fi

    # exasplice has image versions for DOM and CELL and its observed that one of the version remain same for couple of months
    EXCLUDED_VERSIONS_LIST="${EXCLUDE_VERSIONS_FROM_PURGE} ${EXA_IMAGE_BINARY_VERSION} ${EXASPLICE_DOM0_IMAGE_BINARY_VERSION} ${EXASPLICE_CELL_IMAGE_BINARY_VERSION}"
    skip_purge=1
    # iterate to see all versions in EXADATA_IMAGE_VERSION_TO_BE_PURGED are not part of exclude list
    # this is to avoid a case where dom0/cell binary of monthly bundle is purged leaving just cell/dom0 binary 
    # chances of cell version matching with quarterly cell version is high and sometimes just dom0/cell version changes 
    # between monthly patch bundles
    for version in ${EXADATA_IMAGE_VERSION_TO_BE_PURGED}
    do
        for excluded_version in ${EXCLUDED_VERSIONS_LIST}
        do
            if [ "$version" = "$excluded_version" ]; then
                echo "Registered $PATCH_TYPE bundle version: $version is one of the excluded version (shared version with other component): $EXCLUDED_VERSIONS_LIST hence purge skipped!"
                skip_purge=0
                break
            fi
        done
        if [ "$skip_purge" -ne 0 ]; then
           exaversion_purge_cmd="curl -i -k -u ${ECRA_USER}:${ECRA_PASSWD} -X PUT -i ${ECRA_ENDPOINT}/exaversion/purge  -d '{\"patchVersion\":\"${version}\"}'"

           cmd_output=$(eval "$exaversion_purge_cmd")

           #Check for HTTP status 200
           if [[ "${cmd_output}" != *"HTTP/1.1 200"* ]] ;then
               echo "Warning!! Failed to purge payload version ${version}."
               return 1
           else
               echo "Successfully purged payload version ${version}."
           fi
        fi
        # reset for next iteration
        skip_purge=1
    done
}

function download_latest_dbserver_patch_file() {
    #
    # Downloads latest dbserver.patch.zip to ${EXACLOUD_LOCATION}/PatchPayloads/DBPatchFile/ .
    #
    
    # temp location to store the tar file having latest dbserver.patch.zip
    local dbserver_patch_tar_download_location="/tmp/dbserver_patch"
    refresh_ade_view
    mkdir -p "${dbserver_patch_tar_download_location}"

    local dbserver_patch_zip_tar_gen_cmd="${PREPAREEXADATARELEASETARBALL_SCRIPT_PATH}  -b -l ${dbserver_patch_tar_download_location}"
    $dbserver_patch_zip_tar_gen_cmd
    if [ $? -ne 0 ];  then
        echo "Preparing tar file having latest dbserver.patch.zip failed."
        return 1
    fi
    
    local dbserver_patch_zip_tar=`ls ${dbserver_patch_tar_download_location} | grep 'exadata_dbserverpatch'`
    local local untar_cmd="tar -pxvf ${dbserver_patch_tar_download_location}/${dbserver_patch_zip_tar} -C ${EXACLOUD_LOCATION}"
    ${RM_CMD} -f ${EXACLOUD_LOCATION}/PatchPayloads/DBPatchFile/dbserver.patch.zip ${EXACLOUD_LOCATION}/Steps_dbserver_patch.txt ${EXACLOUD_LOCATION}/managerepo.py

    echo "$untar_cmd"
    $untar_cmd

    if [ $? -ne 0 ];  then
        echo "Extracting dbserver.patch.zip failed."
        return 1
    fi
    echo "Extraction of latest dbserver.patch.zip completed."
    return 0
}

function refresh_ade_view() {
    #
    # Refresh the ade view to get latest PrepareExadataReleaseTarball.sh
    #
    
    local ade_view_name="${USER}_${ADE_VIEW_NAME}"
    ade useview $ade_view_name<<EOF
    ade refreshview -latest
    exit
EOF
}


function new_exadata_bundle_refresher() {
    #
    #  This does the following and returns success(0) or failure(1).
    #   1.Set all the global variables declared
    #   2.Patch all targets to the current registered version
    #   3.Untar the patch payload to exacloud location
    #   4.Register the patch payloads
    #

    echo "Checking whether ECRA services are up and running, if not, ECRA services would be started."
    check_ecra_services_status
    if [ $? -ne 0 ]; then
        echo "ECRA services are down. Trying to restart ecra services.."
        restart_ecra_services
        if [ $? -ne 0 ]; then
            echo "ECRA services are down even after restarting them. Exiting.."
            return 1
        fi
        echo "All the ECRA services are up and running."
    fi

    echo "Prepare environment step started."
    prepare_env
    if [ $? -ne 0 ];  then
        echo "Preparation of the environment failed."
        return 1
    fi
    echo "Prepare environment step completed."

    # single exadata bundle version can be used for all hw components and given that as of now we are purging only
    # previous exadata bundles lets limit the upgrade to previous version only for exadata hw components
    if [ "$PATCH_TYPE" = "exadata" ]; then
        echo "Upgrading all the targets to the currently registered exadata version ${EXADATA_IMAGE_VERSION_TO_BE_PURGED}."
        execute_patch_on_all_targets
        if [ $? -ne 0 ]; then
            return 1
        fi
        echo "All the targets are patched to currently registered exadata version ${EXADATA_IMAGE_VERSION_TO_BE_PURGED}."
    fi

    echo "Downloading '${EXA_IMAGE_BINARY_FULL_PATH_URL}'"
    getFromOss ${EXA_IMAGE_BINARY_FULL_PATH_URL}  
    if [ $? -ne 0 ]; then
      echo "Download from ${EXA_IMAGE_BINARY_FULL_PATH_URL} failed"
      return 1
    fi

    echo "Extracting ${EXA_IMAGE_BINARY_FULL_PATH_URL##*/} to ${EXACLOUD_LOCATION}."
    #Untar the payload
    local untar_cmd="tar -pxvf ${ECRA_INSTALL_ROOT}/${EXA_IMAGE_BINARY_FULL_PATH_URL##*/} -C ${EXACLOUD_LOCATION}"
    $untar_cmd

    if [ $? -ne 0 ];  then
        echo "Extracting the patch payload failed."
        return 1
    fi
    echo "Extracting the patch payload completed."

    echo "Purge '${ECRA_INSTALL_ROOT}/${EXA_IMAGE_BINARY_FULL_PATH_URL##*/}' which is downloaded from oss"
    ${RM_CMD} -f ${ECRA_INSTALL_ROOT}/${EXA_IMAGE_BINARY_FULL_PATH_URL##*/}

    echo "Registering exadata image version ${EXA_IMAGE_BINARY_VERSION} with ECRA."
    register_patch_payload
    if [ $? -eq 0 ];  then
        echo "Patch payloads registered successfully."
        return 0
    else
        echo "Patch payloads registration failed."
        return 1
    fi
}

function getFromOss()
{
  local url="${1}"

  curl -f -v --connect-timeout 120 -X GET -o ${ECRA_INSTALL_ROOT}/${url##*/} -O ${url}
  if (( $? != 0 )); then
    echo "ERROR: Unable to download '${url}'"
    return 1
  fi
}

function main() {

if [[ "$DOWNLOAD_LATEST_DBSERVER_PATCH" == "yes" ]] ; then
    download_latest_dbserver_patch_file
    if [ $? -ne 0 ];  then
        echo "download_latest_dbserver_patch_file failed."
        exit 1
    fi
    exit 0
else
    new_exadata_bundle_refresher    
    if [ $? -eq 0 ];  then
        echo "$PATCH_TYPE image version ${EXA_IMAGE_BINARY_VERSION} is downloaded and registered successfully."
    else
        echo "Exiting..The steps to download and registraion of $PATCH_TYPE image version ${EXA_IMAGE_BINARY_VERSION} are failed."
    exit 1
    fi

    # Post activities after downloading and registering exadata software bits 
    purge_exadata_payload
    if [ $? -ne 0 ];  then
        # failed to purge the payload
        exit 1
    fi
fi

}
##MAIN
main
