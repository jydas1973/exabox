#!/bin/bash
#
# $Header: ecs/exacloud/exabox/infrapatching/test/cicd/scripts/cleanup_space.sh /main/3 2024/11/14 16:04:15 apotluri Exp $
#
# cleanup_space.sh
#
# Copyright (c) 2023, 2024, Oracle and/or its affiliates. 
#
#    NAME
#      cleanup_space.sh - This is a shell script to cleanup space on dev environment dom0, domu, cell
#
#    DESCRIPTION
#      This is a shell script to cleanup space on dev environment dom0, domu, cell
#      ------------------------------------------------------------------------------------------------------------------
#       INPUT        :  -i <ECRA_INSTALL_FOLDER>
#                          This is a mandatory parameter.The parameter value is the complete path where ecra is installed.
#                          Suppose, if ECRA is installed in /scratch/$USER/ecra_installs/automation, then /scratch/$USER/ecra_installs/automation should #be passed as parameter value.
#
#    NOTES
#       The following are the examples for the usage of the script.
#
#       cleanup_space.sh -i /u02/ecra_preprov/oracle/ecra_installs/infrapatch0917
#         
#       This script does the following clean up in dom0 domu and cells
#             dom0: 
#               /opt/oracle.ExaWatcher/archive/*/*dat* 
#               /var/log/{messages.*,secure.*,boot.log.*,wtmp.*,cellos.*,audit/audit.log.*}
#
#             domu:
#               /opt/oracle.ExaWatcher/archive/*/*dat*
#               /var/log/{messages.*,secure.*,boot.log.*,wtmp.*,cellos.*,audit/audit.log.*}
#               /u02/dbserver.patch.zip_exadata_*.zip
#
#             cell:
#               /opt/oracle.ExaWatcher/archive/*/*dat*
#               /var/log/{messages.*,secure.*,boot.log.*,wtmp.*,cellos.*,audit/audit.log.*}
#               /var/log/journal/*/system@*.journal
#
#       The script exits with always success as we dont want to fail if the cleanup fails
#
#
#    MODIFIED   (MM/DD/YY)
#    apotluri    11/13/24 - Bug 37273645 - INFRAPATCH TEST AUTOMATION : REMOVE
#                           JOURNAL FILES UNDER /VAR/LOG/JOURNAL/*/SYSTEM@*
#    sdevasek    10/03/23 - ENH 35821751 - INFRAPATCHING TEST AUTOMATION- CLEAN
#                           UP SPACE IN CELL IN ORACLE.EXAWATCHER ARCHIVE DIR
#    apotluri    05/10/23 - Enh 35371736 - INFRAPATCHING TEST AUTOMATION : MOVE
#                           CLEAN UP SPACE TASK TO A GENERIC PLACE INSTEAD OF
#                           DOING FOR EVERY TEST
#    apotluri    05/10/23 - Creation
#

ECRA_INSTALL_FOLDER=""

function usage() {
    echo "Usage: $0 [ -i ECRA_INSTALL_FOLDER ]"
}

function exit_abnormal() {
    usage
    exit 1
}

while getopts ":i:" options; do

    case "${options}" in
        i)
            ECRA_INSTALL_FOLDER=${OPTARG}
            if [[ ${ECRA_INSTALL_FOLDER:0:1} == "-" ]]; then
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
fi

TEST_INFRAPATCHING_CONFIG_FILE_LOCATION="${ECRA_INSTALL_FOLDER}/mw_home/user_projects/domains/exacloud/exabox/infrapatching/test/config/test_infrapatching.conf"
DOM0S=$(cat $TEST_INFRAPATCHING_CONFIG_FILE_LOCATION | jq -r .dom0s[])
DOMUS=$(cat $TEST_INFRAPATCHING_CONFIG_FILE_LOCATION | jq -r .domus[] | head -2)
CELLS=$(cat $TEST_INFRAPATCHING_CONFIG_FILE_LOCATION | jq -r .cells[])
EXASSH_PATH="${ECRA_INSTALL_FOLDER}/mw_home/user_projects/domains/exacloud/bin/exassh"
RETRY_COUNT="2"

function exec_cmd_remote_nodes()
{
  local nodes="${1}"
  #shift
  local exec_cmd="${2}"
  local cleanup_dir="$(echo ${exec_cmd} | awk '{print $2}')"

  # Execute command on given node which is passed as an input to the function
  # If the execution fails it'll retry for the given RETRY_COUNT.
  for node in ${nodes}
  do
      echo "[ ${node} ]: Checking if directory '${cleanup_dir}' exists"
      ${EXASSH_PATH} ${node} -e "ls -1 ${cleanup_dir}" >/dev/null 2>&1
      if (( $? != 0 )); then
           echo "[ ${node} ]: Skipping as directory doesn't exist"
           echo
           continue
      else
         failed_cmd=0
         counter=0
         until [[ ${counter} == ${RETRY_COUNT} ]]; do
            ((counter++))
            echo "[ ${node} ]: (${counter}/${RETRY_COUNT}) Executing '${exec_cmd}'"
            ${EXASSH_PATH} ${node} -e "${exec_cmd}"
            ret_val=$?
            if (( "${ret_val}" != "0" ));then
              echo -e "[ ${node} ]: ERROR While executing '${exec_cmd}'"
              failed_cmd=1
              if [[ ${counter} == ${RETRY_COUNT} ]];then
                echo -e "[ ${node} ]: ERROR While executing '${exec_cmd}' even after ${RETRY_COUNT} retries"
                continue
              fi
              echo -e "[ ${node} ]: Retrying..."
            else
              failed_cmd=0
              break
            fi
         done
      fi
  done
}

function cleanup(){
  final_ret_val=0
  all_nodes="${DOMUS}
${DOM0S}
${CELLS}"
  
  exec_cmd_remote_nodes "${all_nodes}" "find /var/log -type f \( -name 'messages.*' -o -name 'secure.*' -o -name 'boot.log.*' -o -name 'wtmp.*' -o -name 'cellos.*' -o -name 'audit.log.*' \) -delete -print"
  final_ret_val=$(( ${failed_cmd} + ${final_ret_val} ))

  exec_cmd_remote_nodes "${all_nodes}" "find /opt/oracle.ExaWatcher/archive/ -type f -delete -print"
  final_ret_val=$(( ${failed_cmd} + ${final_ret_val} ))

  exec_cmd_remote_nodes "${DOMUS}" "find /u02 -type d -name dbserver.patch.zip_exadata_*.zip -print0 -exec rm -rf {} +"
  final_ret_val=$(( ${failed_cmd} + ${final_ret_val} ))

  exec_cmd_remote_nodes "${CELLS}" "find /var/log/journal/*/ -type f -name system@*.journal -print0 -exec rm -rf {} +"
  final_ret_val=$(( ${failed_cmd} + ${final_ret_val} ))
}

# Main function (cleanup). Actual execution starts from here.
cleanup
if (( ${final_ret_val} != 0 )); then
  echo -e "\nERROR: Problem while running cleanup."
  # NOTE: It is intentional that we dont want to fail if the cleanup fails
  #exit 1
else
  echo -e "\nCleanup completed successfully."
fi
