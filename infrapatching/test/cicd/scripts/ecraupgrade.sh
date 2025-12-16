#!/bin/bash
#
# $Header: ecs/exacloud/exabox/infrapatching/test/cicd/scripts/ecraupgrade.sh /main/12 2025/04/23 04:52:14 apotluri Exp $
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
#
#    NAME
#      ecraupgrade.sh
#
#    DESCRIPTION
#      This is a shell script to upgrade existing ecra installation in the dev environment.
#--------------------------------------------------------------------------------------------------------------------------------------------
# INPUT        :  -i <ECRA_INSTALL_FOLDER>
#                    This is a mandatory parameter.The parameter value is the complete path where ecra is installed.
#                    Suppose, if ECRA is installed in /scratch/$USER/ecra_installs/automation, then /scratch/$USER/ecra_installs/automation should #                    be passed as parameter value.
#
#              :  -l <ECS_BRANCH_LABEL>
#                    This is mandatory parameter.
#                    The parameter value is the label name to which ECRA upgrade need to happen. Eg:210810.0901, 210810.0501 etc.
#
#              :  -b <ECS_BRANCH_NAME>
#                    This is an optional parameter.
#                    The parameter value is the base branch name from which label value is considered for upgrade. Eg:20.4.1.3.0, MAIN etc.
#                    If this parameter is not passed, MAIN branch is considered for upgrade.
#
#
# Note:-
# The following are the examples for the usage of the script.
#
# ecraupgrade.sh -i /scratch/sdevasek/ecra_installs/cicd -b MAIN -l 210810.0901
#   Here the script is going to upgrade ECRA installed in cicd folder to ECS_MAIN_LINUX.X64_210803.0901 label.
# ecraupgrade.sh -i /scratch/sdevasek/ecra_installs/cicd -b 20.4.1.3.0 -l 210810.0501
#   Here the script is going to upgrade ECRA installed in cicd folder to ECS_20.4.1.3.0_LINUX.X64_210810.0501 label.
# ecraupgrade.sh -i /scratch/sdevasek/ecra_installs/cicd -l 210810.0901
#   Here the script is going to upgrade ECRA installed in cicd folder to ECS_MAIN_LINUX.X64_210810.0901 label.
#
# This script does the following
#  1)Validate the parameters and their values passed(ecra install folder, ecs branch name and label value).
#  2)Pre-Cleanup(removing exacloud.bak* folders by keeping only the last backup folder,removing the oeda request logs and thread logs from
#    exacloud location and removing ecradpy backup folders).
#  3)Execute ECRA upgrade.
#  4)Upgrade DCS agent rpms.
#
# The script exits with either success or failure code. i.e.,
#   exit 0 means, success, when script successfully completes all of the above mentioned steps.
#   exit 1 means, failure, when scipt fails in any of the above mentioned steps.
#-----------------------------------------------------------------------------
#    MODIFIED   (MM/DD/YY)
#    apotluri    04/21/25 - Bug 37849224 - INFRAPATCHING TEST AUTOMATION : SKIP
#                           UPGRADING DCSAGENT RPMS DURING ECRAUPGRADE WHEN
#                           THERE ARE NO DOMUS PRESENT IN THE TEST CONFIG
#    apotluri    10/17/24 - Enhancement Request 37183984 - UPDATE DCS AGENT AND
#                           DBAASTOOL RPMS IN X9M INFRAPATCHING TEST
#                           ENVIRONMENT
#    apotluri    06/10/23 - Enhancement Request 35115050 - INFRAPATCHING TEST
#                           AUTOMATION IN EXACS R1 SETUP: UPGRADE DCS AGENT
#                           RPMS AS PART OF ECRA UPGRADE SCRIPT
#    emekala     08/04/23 - ENH 35676187 - INFRAPATCHING TEST AUTOMATION -
#                           Address gaps in ECRAUPGRADE.SH
#    emekala     07/10/23 - ENH 35579094 - INFRAPATCHING TEST AUTOMATION -
#                           ecraupgrade.sh must backup and restore rack
#                           specific test config and payload files to make the
#                           script generic
#    apotluri    05/08/23 - ENH 35348661 - TEST AUTOMATION: ECRAUPGRADE.SH
#                           SHOULD BE COMPATIBLE TO RUN ON X5 AND X9 RACKS
#    apotluri    03/14/23 - ENH 35164167 - INFRAPATCHING TEST AUTOMATION
#                           IMPROVEMENT: ECRA UPGRADE SCRIPT TO PURGE OLD
#                           EXACLOUD BACK UP DIRECTORIES AND USE CORRECT ADE
#                           NAS LOCATIONS
#    sdevasek    27/12/22 - ENH 34862465 - UPDATE INFRAPATCHING TEST CODE FOR
#                           ECRA UPGRADE TO WORK IN X9M R1 ENV
#    sdevasek    06/20/22 - Bug 34299214 - UPGRADE DBASSTOOL RPMS IN AUTOMATION
#                           SETUP ALONG WITH ECRA UPGRADE
#    sdevasek    05/30/22 - ENH 34057041 - UPGRADE DCSAGENT IN INFRAPATCHING
#                           AUTOMATION SETUP ALONG WITH ECRA UPGRADE
#    sdevasek    11/08/21 - Enh33519964 - Delete thread logs,oeda request logs
#                           and ecradpy upgrade backup folders.
#    sdevasek    08/11/21 - Enh33204096 - Develop ecra upgrade pipeline for cicd
#    sdevasek    08/11/21 - Creation
#

set -x

USER_NAME=$(whoami)
ECRA_INSTALL_FOLDER=""
ECS_BRANCH=""
ECS_LABEL=""
COMPLETE_ECS_LABEL_NAME=""
ADE_ECRA_PATCH_ROOT_LOCATION="/ade_autofs/dd223_db/ECS"
ECRA_PATCH_LOCATION=""
EXACLOUD_BACKUP_LOCATION=""
EXACLOUD_THREADS_LOG_LOCATION=""
LOCATION_FOR_ECS_LABEL_INFO="/tmp/ecslabel.txt"
TEST_INFRAPATCHING_CONFIG_FILE_LOCATION=""
DCS_AGENT_NO_AUTH_SCRIPT="/opt/oracle/dcs/bin/agent-noauth.sh"
IS_R1_ENV="False"
declare -a DOMU_ARRAY

function usage() {
    echo "Usage: $0 [ -i ECRA_INSTALL_FOLDER ] [ -b ECS_BRANCH_NAME ] [ -l ECS_BRANCH_LABEL ]"
    echo "If branch(-b) option is not passed, ECS_MAIN branch is considered for upgrade."
}

function exit_abnormal() {
    usage
    exit 1
}

#
# General parameter validation is done first, like no of parameters and parameter names
#

# If no parameter is passed, display the usage.
if [ $# -eq 0 ]; then
    exit_abnormal
fi

while getopts ":i:b:l:" options; do

    case "${options}" in
        i)
            ECRA_INSTALL_FOLDER=${OPTARG}
            if [[ ${ECRA_INSTALL_FOLDER:0:1} == "-" ]]; then
                exit_abnormal
            fi
            ;;
        b)
            ECS_BRANCH=${OPTARG}
            if [[ ${ECS_BRANCH:0:1} == "-" ]]; then
                exit_abnormal
            fi
            ;;
        l)
            ECS_LABEL=${OPTARG}
            if [[ ${ECS_LABEL:0:1} == "-" ]]; then
                exit_abnormal
            fi
            ;;
        :)
            echo "Error: -${OPTARG} requires an argument."
            exit_abnormal
            ;;
        *)
            exit_abnormal
            ;;
    esac

done

# Validate -i parameter
# -i is the mandatory parameter
if [ -z "$ECRA_INSTALL_FOLDER" ]; then
    echo "Error: -i is the mandatory parameter to be passed."
    exit_abnormal
else
    if [ ! -d "$ECRA_INSTALL_FOLDER" ]; then
        echo "${ECRA_INSTALL_FOLDER} does not exist. Please check the parameter value ${ECRA_INSTALL_FOLDER} passed for ECRA install folder is correct."
        exit 1
    fi
    EXACLOUD_BACKUP_LOCATION="${ECRA_INSTALL_FOLDER}/mw_home/user_projects/domains"
    EXACLOUD_THREADS_LOG_LOCATION="${ECRA_INSTALL_FOLDER}/mw_home/user_projects/domains/exacloud/log/threads/0000-0000-0000-0000/*"
fi

TEST_INFRAPATCHING_LOCATION="${ECRA_INSTALL_FOLDER}/mw_home/user_projects/domains/exacloud/exabox/infrapatching/test"
TEST_INFRAPATCHING_CONFIG_LOCATION="${TEST_INFRAPATCHING_LOCATION}/config"
TEST_INFRAPATCHING_CONFIG_FILE_LOCATION="${TEST_INFRAPATCHING_CONFIG_LOCATION}/test_infrapatching.conf"
IS_R1_ENV=$(cat $TEST_INFRAPATCHING_CONFIG_FILE_LOCATION | jq -r .is_r1_env)
ECRA_INSTALL_BASE=$(cat $TEST_INFRAPATCHING_CONFIG_FILE_LOCATION | jq -r .ecra_install_base)
EXASSH_PATH="${ECRA_INSTALL_FOLDER}/mw_home/user_projects/domains/exacloud/bin/exassh"
RACK_SPECIFIC_TEST_CONFIG_BACKUP_LOCATION="/tmp/rack_specific_test_config_b4_ecra_upgrade"

# Validate -b parameter
# -b is an optional paramter. If not passed ECS_MAIN is considered for upgrade.
if [ -z "$ECS_BRANCH" ]; then
    ECS_BRANCH="MAIN"
else
    patch_tar_base_folder="${ADE_ECRA_PATCH_ROOT_LOCATION}/${ECS_BRANCH}/LINUX.X64"
fi

# Validate -l parameter
if [ -z "$ECS_LABEL" ]; then
    echo "Please pass the parameter value for -l to select the correct label for upgrade."
        exit 1
else
    COMPLETE_ECS_LABEL_NAME="ECS_${ECS_BRANCH}_LINUX.X64_${ECS_LABEL}"
fi

echo "Complete label name considered for upgrade is ${COMPLETE_ECS_LABEL_NAME}."

if [[ "$IS_R1_ENV" == "True" ]]; then
  # Download ecra-patch.tar to current location in R1 env
    if [[ -d ${ECRA_INSTALL_BASE} ]];then
      cd ${ECRA_INSTALL_BASE}
      rm -f *_ecra-patch.tar
    fi
    /home/oracle/bin/getFromOss ${COMPLETE_ECS_LABEL_NAME}_ecra-patch.tar
    if [ $? -ne 0 ];  then
        echo "Could not download ${COMPLETE_ECS_LABEL_NAME}_ecra-patch.tar."
        exit 1
    fi
    ECRA_INSTALL_BASE=`pwd`
    ECRA_PATCH_LOCATION=${ECRA_INSTALL_BASE}/${COMPLETE_ECS_LABEL_NAME}_ecra-patch.tar
else
    ECRA_PATCH_LOCATION="${ADE_ECRA_PATCH_ROOT_LOCATION}/${ECS_BRANCH}/LINUX.X64/${ECS_LABEL}/ecs/ecra/ship/ecra-patch.tar"
fi

if [ ! -f "$ECRA_PATCH_LOCATION" ]; then
    echo "${ECRA_PATCH_LOCATION} does not exist. Please check the parameter value ${ECS_LABEL} passed for label is correct."
    exit 1
fi

# ECRA Label info is pushed into /tmp/ecslabel.txt which will be used to propagate as Jenkins job parameter.
echo "COMPLETE_ECS_LABEL_NAME=${COMPLETE_ECS_LABEL_NAME}" > $LOCATION_FOR_ECS_LABEL_INFO

# Actual utility functions start from here
function pre_cleanup(){
    #
    # This does the following
    # 1.It keeps exacloud.bak folders as per retention count(currently 1) and delete rest of all exacloud.bak folders from
    # /scratch/$USER/ecra_installs/${ECRA_INSTALL_FOLDER}/mw_home/user_projects/domains folder.
    # 2.It deletes logs from exacloud threads location with retention as x days.
    # 3.It deletes oeda request folder from exacloud location with retention as x days.
    # 4.It deletes ecradpy upgrade backups from ecra location.
    #

    declare -i deletable_count=0
    declare -i retention_count=1
    local ecradpy_backup_clean_cmd=""

    # Delete exacloud.bak folders
    deletable_count=$(ls -t $EXACLOUD_BACKUP_LOCATION |grep exacloud.bak|wc -l)

    if [ $deletable_count -gt $retention_count  ]; then
        deletable_count=$(($deletable_count-$retention_count))
        echo "Deleting $deletable_count exacloud.bak* folder/s from ${EXACLOUD_BACKUP_LOCATION}."
        find $EXACLOUD_BACKUP_LOCATION  -type d -name 'exacloud.bak*' -print |sort |head -$deletable_count |xargs rm -rf
    fi

    # Delete log files from exacloud threads location and delete oeda requests folder
    log_cleanup

    # Delete ecradpy backup folders from ECRA location which are older than retention days

    if [ -d  "${ECRA_INSTALL_FOLDER}/backup/dpy_upgrade" ]; then
       ecradpy_backup_clean_cmd="find ${ECRA_INSTALL_FOLDER}/backup/dpy_upgrade  -maxdepth 1  -mindepth 1  -type d -mtime +$retention_count -exec rm -rf {} +"
       echo "deleting ecradpy backup folders from ECRA location which are older than ${retention_count} day/s."
       $ecradpy_backup_clean_cmd
    fi
}

function log_cleanup(){
    #
    # Deletes all thread logs from exacloud location which are older than retention days
    # and deletes oeda requests logs from exacloud location which are older than retention days.
    #

    declare -i log_retention_days=10
    local cmd=""

    #delete all thread logs from exacloud location which are older than retention days
    if [ -d  "${EXACLOUD_THREADS_LOG_LOCATION:0:-1}" ]; then
        #delete all thread logs from exacloud location which are older than retention days
        cmd="find ${EXACLOUD_THREADS_LOG_LOCATION:0:-1} -maxdepth 1 -type f -mtime +$log_retention_days -delete"
        echo "deleting thread logs from exacloud location which are older than ${log_retention_days} days."
        $cmd
    fi

    #delete oeda requests logs folder from exacloud location which are older than retention days
    if [ -d  "${ECRA_INSTALL_FOLDER}/mw_home/user_projects/domains/exacloud/oeda/requests/" ]; then
       cmd="find ${ECRA_INSTALL_FOLDER}/mw_home/user_projects/domains/exacloud/oeda/requests/ -maxdepth 1  -mindepth 1  -type d -mtime +$log_retention_days  -exec rm -rf {} +"
       echo "deleting oeda requests folder from exacloud location which are older than ${log_retention_days} days."
       $cmd
    fi
}

function execute_ecradpy_action() {
    #
    # Executes ecradpy_cmd and return success(0) or failure(1).
    #
    local ecradpy_cmd=""
    if [[ "$1" == "upgrade" ]]; then
        local ecradpy_cmd="${ECRA_INSTALL_FOLDER}/ecradpy/ecradpy --action upgrade --patchtar ${ECRA_PATCH_LOCATION} --patchhost all --noimagechanges"
        # For R1 EXACS ecra upgrades, need to use  --env bm in the ecradpy command
        if [[ "$IS_R1_ENV" == "True" ]]; then
            ecradpy_cmd="${ecradpy_cmd}  --env bm"
        fi
    elif [[ "$1" == "dpy_upgrade" ]]; then
        local ecradpy_cmd="${ECRA_INSTALL_FOLDER}/ecradpy/ecradpy --action dpy_upgrade  --patchtar ${ECRA_PATCH_LOCATION}"
    else
        echo "Unsupported option provided to be used with ecradpy"
        return 1
    fi

    $ecradpy_cmd
    if [ $? -eq 0 ];  then
        echo "ECRADPY action $1 completed successfully."
        return 0
    else
        echo "ECRADPY action $1 failed."
        return 1
    fi
}

function execute_ecra_upgrade() {
    #
    # Executes the ecra upgrade command and return success(0) or failure(1).
    # First deployer is upgraded and then ecra
    #

    # Execute ecra deployer upgrade
    execute_ecradpy_action  "dpy_upgrade"

    if [ $? -eq 0 ];  then
        echo "ECRA Deployer is upgraded successfully."
        sleep 1m

        #Execute ecra upgrade
        execute_ecradpy_action "upgrade"
        if [ $? -eq 0 ];  then
            echo "ECRA Upgrade done successfully."
            return 0
        else
            echo "ECRA Upgrade failed."
            return 1
        fi
    else
        echo "ECRA Deployer upgrade failed."
        return 1
    fi
}

function check_ecra_services_status() {
    #
    # Checks ecra servcies status by looking for "result": "fail" string in the output of ecractl.sh status.
    #
    local status_output="/tmp/statusoutput.txt"
    rm -f $status_output
    $ECRA_INSTALL_FOLDER/ecractl.sh status | tee $status_output
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
    # Restarts ECRA services and checks for servcies status at the end.
    #
    $ECRA_INSTALL_FOLDER/ecractl.sh stop
    if [ $? -ne 0 ]; then
        echo "Could not stop ECRA services."
        return 1
    else
        $ECRA_INSTALL_FOLDER/ecractl.sh start
    fi
    return $?
}

function check_ecracli_info(){
    #
    # Checks for "status : 200" in the ecracli info command output.
    #
    local ecra_cli_output="/tmp/del.txt"
    rm -f ${ecra_cli_output}
    echo welcome1>> /tmp/password.txt;
    ${ECRA_INSTALL_FOLDER}/ecracli/ecracli info --username ops --password=/tmp/password.txt|tee ${ecra_cli_output}
    grep "status : 200" ${ecra_cli_output}
    if [ $? -ne 0 ];  then
        echo "ECRACLI info command failed."
        return 1
    else
        echo "ECRACLI info command succeeded."
        return 0
    fi
}

function check_start_ecra_service() {
   check_ecra_services_status
   if [ $? -ne 0 ];  then
       echo "ECRA services are down so restarting ECRA services."
       restart_ecra_services
       if [ $? -ne 0 ];  then
            echo "ECRA services could not start."
            return 1
       fi
   fi
}

function upgrade_dcsagent_update_rpm()
{
    # get list of all domus 
    # Example: 
    # [oracle@ecra-exacsdev7 ~]$ domu_list=$(jq -r '.vm_map[] | .vms[] | .clusterName' ${TEST_INFRAPATCHING_CONFIG_FILE_LOCATION} | sort -u | while read clu; do  jq -r --arg cluster "$clu" '.vm_map[] | .vms[] | select(.clusterName == $cluster) | .domuNatHostname' ${TEST_INFRAPATCHING_CONFIG_FILE_LOCATION}; done)
    # [oracle@ecra-exacsdev7 ~]$ echo "$domu_list" 
    # sea201323exddu0601.sea2xx2xx0061qf.adminsea2.oraclevcn.com
    # sea201323exddu0701.sea2xx2xx0061qf.adminsea2.oraclevcn.com
    # sea201323exddu0801.sea2xx2xx0061qf.adminsea2.oraclevcn.com
    # sea201323exddu1101.sea2xx2xx0061qf.adminsea2.oraclevcn.com
    # sea201323exddu0702.sea2mvm01roce.adminsea2.oraclevcn.com
    # sea201323exddu0802.sea2mvm01roce.adminsea2.oraclevcn.com
    # sea201323exddu0603.sea2mvm01roce.adminsea2.oraclevcn.com
    # sea201323exddu0703.sea2mvm01roce.adminsea2.oraclevcn.com
    # sea201323exddu0803.sea2mvm01roce.adminsea2.oraclevcn.com
    # sea201323exddu0604.sea2mvm01roce.adminsea2.oraclevcn.com
    # sea201323exddu1104.sea2mvm01roce.adminsea2.oraclevcn.com
    # sea201323exddu1105.sea2mvm01roce.adminsea2.oraclevcn.com
    # [oracle@ecra-exacsdev7 ~]$ 

    domu_list=$(jq -r '.vm_map[] | .vms[] | .clusterName' ${TEST_INFRAPATCHING_CONFIG_FILE_LOCATION} | sort -u | while read clu; do  jq -r --arg cluster "$clu" '.vm_map[] | .vms[] | select(.clusterName == $cluster) | .domuNatHostname' ${TEST_INFRAPATCHING_CONFIG_FILE_LOCATION}; done)
    
    if [[ -z ${domu_list} ]]; then
      echo "Error in getting list of domus from ${TEST_INFRAPATCHING_CONFIG_FILE_LOCATION}"
      return 1
    fi

    # Upgrade dbaastool rpm and dcs agent rpms in each domu
    for domu in ${domu_list}
    do
        # Upgarde one by one rpm
        for rpm_name in ${!dbaas_rpm_name_path_map[@]}
        do
            local rpm_name_to_be_installed="$rpm_name"
            local rpm_path_to_be_installed="${dbaas_rpm_name_path_map[$rpm_name]}"
            local rpm_upload_cmd="${EXASSH_PATH} ${domu} -up ${rpm_path_to_be_installed}  /root/${rpm_name_to_be_installed}"
            local rpm_install_cmd="${EXASSH_PATH} ${domu} -e 'rpm -Uvh /root/${rpm_name_to_be_installed} --force'"
            local rpm_delete_file_cmd="${EXASSH_PATH} ${domu} -e 'rm -f /root/${rpm_name_to_be_installed}'"
            local dbcs_agent_noauth_cmd="${EXASSH_PATH} ${domu} -e '${DCS_AGENT_NO_AUTH_SCRIPT}'"


            # Copy the rpm to remote node location
            eval $rpm_upload_cmd
            if [ $? -ne 0 ];  then
                result=1
                echo "Copying the rpm ${rpm_name_to_be_installed} to ${domu} failed."
                break
            else
                echo "Copied the rpm ${rpm_name_to_be_installed} to ${domu}."
                # Install the rpm in the remote node
                eval "$rpm_install_cmd"
                if [ $? -ne 0 ];  then
                    result=1
                    echo "Installing the rpm ${rpm_name_to_be_installed} failed in ${domu}."
                    break
                else
                    echo "Installation of the rpm ${rpm_name_to_be_installed} in ${domu} completed."
                    # Remove the rpm from remote node location
                    eval $rpm_delete_file_cmd
                    if [ $? -ne 0 ];  then
                        result=1
                        echo "Deleting the rpm ${rpm_name_to_be_installed} from ${domu} failed."
                        break
                    else
                        echo "Removed the rpm ${rpm_name_to_be_installed} from ${domu}."
                    fi
                fi
            fi
        done # end of looping of rpms

        if [ "$IS_R1_ENV" != "True" ]; then
          # Execute /opt/oracle/dcs/bin/agent-noauth.sh on the remote node
          eval $dbcs_agent_noauth_cmd
          if [ $? -ne 0 ];  then
              echo "Executing ${DCS_AGENT_NO_AUTH_SCRIPT} failed in ${domu}."
              result=1
          fi

          # When any of the step fails, exit the method
          if [ $result -ne 0 ];  then
              break
          fi
        fi
    done

    return $result
}

function upgrade_dbaastool_rpm()
{
    # get the list of clusters available 
    for cluster in $(jq -r '.vm_map[] | .vms[] | .clusterName' ${TEST_INFRAPATCHING_CONFIG_FILE_LOCATION} | sort -u)
    do
      # for each cluster get the first domu
      # sample o/p for cluster
      # [oracle@ecra-exacsdev7 config]$ jq -r --arg clusterName "sea2-d3-cl4-c1981188-b4db-4a28-9900-62d6a99d797a-clu03" '.vm_map[] | .vms[] | select(.clusterName == $clusterName) | .domuNatHostname' test_infrapatching.conf | sort | head -1
      # sea201323exddu0603.sea2mvm01roce.adminsea2.oraclevcn.com
      first_domu=$(jq -r --arg clusterName "$cluster" '.vm_map[] | .vms[] | select(.clusterName == $clusterName) | .domuNatHostname' ${TEST_INFRAPATCHING_CONFIG_FILE_LOCATION} | sort | head -1)

      dbaascli_cmd="dbaascli admin updateStack --location /root/${DBAASTOOLS_EXA_RPM_PATH##*/}"
      ${EXASSH_PATH} ${first_domu} -up ${DBAASTOOLS_EXA_RPM_PATH}  /root/${DBAASTOOLS_EXA_RPM_PATH##*/}
      if (( $? != 0 )); then
         echo "ERROR: Uploading rpm to ${first_domu} failed"
         result=1
         return ${result}
      fi

      ${EXASSH_PATH} ${first_domu} -e "${dbaascli_cmd}"
      if (( $? != 0 )); then
         echo "ERROR: While running '${dbaascli_cmd}' on '${first_domu}'"
         result=1
         return ${result}
      fi

      ${EXASSH_PATH} ${first_domu} -e "rm -f /root/${DBAASTOOLS_EXA_RPM_PATH##*/}"
      if (( $? != 0 )); then
         echo "ERROR: While removing '/root/${DBAASTOOLS_EXA_RPM_PATH##*/}' on '${first_domu}'"
         result=1
         return ${result}
      fi
    done

    return ${result}
}

function upgrade_dcs_agent() {
    #
    # Upgrades the dcs agent.
    # The following steps are followed
    # 1) Fetch the latest rpms from DBAAS ade location
    # 2) Fetch domus from test_infrapatching.conf
    # 3) Execute required steps to upgrade the dcs agent( upgrade the rpms, execute no_auth script and remove the rpms to clear up the space)
    #
    # Here two rpms
    #   1. dbcs-agent-update-exacc.rpm -    /ade_autofs/dd223_db/DBAAS/MAIN/LINUX.X64/220617.1413/dbaas/opc/rpms/exa/dbcs-agent/update/dbcs-agent-update-exacc-2.24.0.0.0_220617.1413.x86_64.rpm
    #   2. dbaastools_exa.rpm - /ade_autofs/dd223_db/DBAAS/MAIN/LINUX.X64/220617.1413/dbaas/opc/rpms/exa/dbaastools_exa-1.0-1+MAIN_220617.1413.x86_64.rpm
    #   are copied to remote nodes and are upgraded.
    #
    #

    declare -i result=0
    declare -A dbaas_rpm_name_path_map
    if [ "$IS_R1_ENV" != "True" ]; then
       local COMPLETE_DBAAS_LABEL_NAME=$(ade showlabels -series DBAAS_MAIN_LINUX.X64 |tail -1)
       local DBAAS_DATED_LABEL=$(echo $COMPLETE_DBAAS_LABEL_NAME |cut -d'_' -f 4)
       local DBAAS_RPMS_LOC="${ADE_ECRA_PATCH_ROOT_LOCATION%/*}/DBAAS/MAIN/LINUX.X64/${DBAAS_DATED_LABEL}/dbaas/opc/rpms/exa"
       local DBCS_AGENT_UPDATE_EXACC_RPM=$(ls ${DBAAS_RPMS_LOC}/dbcs-agent/update/ |grep dbcs-agent-update-exacc)
       local DBAASTOOLS_EXA_RPM=$(ls ${DBAAS_RPMS_LOC} |grep dbaastools_exa)

       # Eg: dcs_agent_update rpm path is like below    #/ade_autofs/dd223_db/DBAAS/MAIN/LINUX.X64/220529.0657/dbaas/opc/rpms/exa/dbcs-agent/update/dbcs-agent-update-exacc-2.24.0.0.0_220529.0657.x86_64.rpm
       local DBCS_AGENT_UPDATE_EXACC_RPM_PATH="${DBAAS_RPMS_LOC}/dbcs-agent/update/${DBCS_AGENT_UPDATE_EXACC_RPM}"
       local DBAASTOOLS_EXA_RPM_PATH="${DBAAS_RPMS_LOC}/${DBAASTOOLS_EXA_RPM}"
       # map contains rpm name and its path
       dbaas_rpm_name_path_map[$DBCS_AGENT_UPDATE_EXACC_RPM]=$DBCS_AGENT_UPDATE_EXACC_RPM_PATH
    else
       local DCSAGENT_RPMS_DIR="/tmp/dcsagent_rpms"
       local DBCS_AGENT_UPDATE_RPM=$(ls ${DCSAGENT_RPMS_DIR}/ |grep dbcs-agent-update-[0-9])
       local DBAASTOOLS_EXA_RPM=$(ls ${DCSAGENT_RPMS_DIR} |grep dbaastools_exa)
       local DBCS_AGENT_UPDATE_RPM_PATH="${DCSAGENT_RPMS_DIR}/$(ls ${DCSAGENT_RPMS_DIR}/ | grep dbcs-agent-update-[0-9])"
       local DBAASTOOLS_EXA_RPM_PATH="${DCSAGENT_RPMS_DIR}/$(ls ${DCSAGENT_RPMS_DIR}/ |grep dbaastools_exa)"
       # map contains rpm name and its path
       dbaas_rpm_name_path_map[$DBCS_AGENT_UPDATE_RPM]=$DBCS_AGENT_UPDATE_RPM_PATH
    fi

    upgrade_dbaastool_rpm
    ret_val="$?"
    if (( ${ret_val} != 0 )); then
      return ${ret_val}
    fi
    
    upgrade_dcsagent_update_rpm
    ret_val="$?"
    if (( ${ret_val} != 0 )); then
      return ${ret_val}
    fi

    return ${result}
}

function update_dcs_agent_conf() {

    declare -i result=0

    local dcs_agent_conf_dir="/opt/oracle/dcs/conf"
    local dcs_agent_json="${dcs_agent_conf_dir}/dcs-agent.json"

    exassh_path="${ECRA_INSTALL_FOLDER}/mw_home/user_projects/domains/exacloud/bin/exassh"

    # Ex: [oracle@ecra-exacsdev7 config]$ jq -r '.. | .domuNatHostname? // empty' test_infrapatching.conf
    # sea201323exddu0603.sea2mvm01roce.adminsea2.oraclevcn.com
    # sea201323exddu0601.sea2xx2xx0061qf.adminsea2.oraclevcn.com
    # sea201323exddu0604.sea2mvm01roce.adminsea2.oraclevcn.com
    # sea201323exddu0702.sea2mvm01roce.adminsea2.oraclevcn.com
    # sea201323exddu0701.sea2xx2xx0061qf.adminsea2.oraclevcn.com
    # sea201323exddu0703.sea2mvm01roce.adminsea2.oraclevcn.com
    # sea201323exddu0803.sea2mvm01roce.adminsea2.oraclevcn.com
    # sea201323exddu0802.sea2mvm01roce.adminsea2.oraclevcn.com
    # sea201323exddu0801.sea2xx2xx0061qf.adminsea2.oraclevcn.com
    # sea201323exddu1101.sea2xx2xx0061qf.adminsea2.oraclevcn.com
    # sea201323exddu1104.sea2mvm01roce.adminsea2.oraclevcn.com
    # sea201323exddu1105.sea2mvm01roce.adminsea2.oraclevcn.com
    domu_list=$(jq -r '.. | .domuNatHostname? // empty' ${TEST_INFRAPATCHING_CONFIG_FILE_LOCATION})
    # Update dcs_agent_json in each domu
    for domu in ${domu_list}
    do
        local backup_dcs_agent_json="${exassh_path} ${domu} -e 'cp ${dcs_agent_json} ${dcs_agent_json}.bkp'"
        local update_dcs_agent_json="${exassh_path} ${domu} -e 'sed -i "s/\\\"ssl\\\"/\\\"ssl2\\\"/" ${dcs_agent_json}'"
        local restart_dbcsagent="${exassh_path} ${domu} -e 'systemctl restart dbcsagent'"

        # backup dcs_agent_json
        echo "Backing up ${dcs_agent_json} on ${domu}"
        eval "$backup_dcs_agent_json"
        if [ $? -ne 0 ];  then
            result=1
            echo "Back up of ${dcs_agent_json} failed on ${domu}."
            break
        else
            echo "Backup of ${dcs_agent_json} is successful on ${domu}."
            # Update dcs_agent_json file with ssl2
            echo "Updating ${dcs_agent_json} with ssl2 on ${domu}."
            eval "$update_dcs_agent_json"
            if [ $? -ne 0 ];  then
                result=1
                echo "Update of $dcs_agent_json failed on ${domu}."
                break
            else
                echo "Update of ${dcs_agent_json} with ssl2 completed on ${domu}."
                # restart dbcs agent
                echo "Restarting dbcsagent on ${domu}"
                eval "$restart_dbcsagent"
                if [ $? -ne 0 ];  then
                  result=1
                  echo "Restart of dbcsagent failed on ${domu}."
                else
                  echo "Restart of dbcsagent is successful on ${domu}"
                fi
            fi
        fi

        # When any of the step fails, exit the method
        if [ $result -ne 0 ];  then
            break
        fi

    done
    return $result
}

## Actual functionality logic starts from here
##MAIN

check_start_ecra_service
if [[ $? != "0" ]]; then
  echo "ECRA service failed to start. Exiting.."
  exit 1
fi

echo "pre_cleanup step started."
pre_cleanup
echo "pre_cleanup step completed."

# ecra upgrade copies source from ecs label which causes rack specific test config getting overwritten with automation rack config
# to avoid this, lets backup rack specific test config before ecra upgrade starts and restore the same after ecra upgrade completes or fails
echo -e "\nBackup rack specific test config folder from $TEST_INFRAPATCHING_LOCATION to $RACK_SPECIFIC_TEST_CONFIG_BACKUP_LOCATION before starting with ecra upgrade..."
rm -rf $RACK_SPECIFIC_TEST_CONFIG_BACKUP_LOCATION
mkdir -p $RACK_SPECIFIC_TEST_CONFIG_BACKUP_LOCATION
cp -a $TEST_INFRAPATCHING_CONFIG_LOCATION ${RACK_SPECIFIC_TEST_CONFIG_BACKUP_LOCATION}/
ls -lR $RACK_SPECIFIC_TEST_CONFIG_BACKUP_LOCATION

echo -e "\nECRA upgrade step started."
execute_ecra_upgrade
ret_code=$?

echo -e "\nNow lets restore backed up rack specific test config folder from $RACK_SPECIFIC_TEST_CONFIG_BACKUP_LOCATION to $TEST_INFRAPATCHING_LOCATION"
mv  $TEST_INFRAPATCHING_CONFIG_LOCATION ${TEST_INFRAPATCHING_LOCATION}/config_from_ecs_label
cp -a ${RACK_SPECIFIC_TEST_CONFIG_BACKUP_LOCATION}/config ${TEST_INFRAPATCHING_LOCATION}/ 
ls -l $TEST_INFRAPATCHING_CONFIG_LOCATION

if [ "$ret_code" -ne 0 ];  then
    echo "ECRA upgrade step failed.Exiting.."
    exit 1
fi

echo -e "\nRunning add_test_params_to_config.py to add new config params, if any added to run test automation... "
cd ${TEST_INFRAPATCHING_LOCATION}
for file in utils.txt constants.txt add_test_params_to_config.txt; do
  if [ -e $file ]; then
    mv "$file" "${file%.txt}.py"
  fi
done
chmod +w $TEST_INFRAPATCHING_CONFIG_FILE_LOCATION

python3 add_test_params_to_config.py
if [ $? -ne 0 ];  then
    echo -e "\nFailed to add test config parameters for automation run. Exiting.\n"
    exit 1
fi

if [[ ! -z "$(cat $TEST_INFRAPATCHING_CONFIG_FILE_LOCATION | jq -r .domus[])" ]]; then
  echo "Upgrading dcs agent started."
  upgrade_dcs_agent
  if [ $? -ne 0 ];  then
      echo "DCS agent upgrade failed.Exiting.."
      exit 1
  fi
  
  if [ "$IS_R1_ENV" == "True" ]; then
    update_dcs_agent_conf
    if [ $? -ne 0 ];  then
        echo "DCS agent upgrade failed.Exiting.."
        exit 1
    fi
  fi
else
  echo "Skipping Upgrading dcs agent as there are no domus present in the config"
fi

# check and start ecra service if they are not up post upgrade
check_start_ecra_service
if [[ $? != "0" ]]; then
  echo "ECRA service failed to start post upgrade. Exiting.."
  exit 1
fi

echo "All the steps are completed successfully.ECRA is upgraded to ${COMPLETE_ECS_LABEL_NAME}."
exit 0
