#!/bin/sh
#
# infrapatch_testexecutor.sh
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates. 
#
#    NAME
#      infrapatch_testexecutor.sh
#
#    DESCRIPTION
#      This shell script used in automation to execute tests based on the job name passed to it.
#--------------------------------------------------------------------------------------------------------------------------
#              :  -i <ECRA_INSTALL_FOLDER>
#                    This is a mandatory parameter. The parameter value should point to ecra install folder location
#
#              :  -j <TEST_JOB_NAME>
#                    This is an optional parameter. The parameter value is the test job name. This determines which test
#                    would be run as part this script execution.
#
#                    Possible values are
#                    dom0_patch_prereq_check, dom0_patch, dom0_postcheck, dom0_rollback and etc.,
#                    for other exadata hw components
#
#                    For code_coverage_calculator job, code coverage related steps are run and
#                    for other jobs, based on job name, required pytest command are formed.
#
#              :  -r <TEST_REPORT_FILE>
#                    This is an optional parameter. If value is specified, test report file generated in the current dir
#
#              :  -m yes
#                    This is an optional parameter. If value is yes and -r option specified then,
#                    current test report merged with previous rest report file (which is backed up before new test run)
#
#              :  -d yes
#                    This is an optional parameter. If value is yes and -r option specified then, previous test report
#                    file deleted
#
#              :  -s yes
#                    This is an optional parameter. If value is yes then, ECRA services are checked and started
#
# Note:-
# The following is the example for the usage of the script.
#
# infrapatch_testexecutor.sh -i /scratch/sdevasek/ecra_installs/automate -j dom0_patch -r TEST_REPORT/xyz.xml -m yes
#   Here the script is going to execute dom0 patch test, record the test report in TEST_REPORT/xyz.xml under 
#   current dir and before to test execution if test report file already present then backup taken to merge report with new report.
#
# This script does the following
#  1) Make the environment ready, before executing the pytest.
#     a) Update ecraurl in test_infrapatching.conf with correct value.
#     b) Add write permissions to test_infrapatching.conf and payload.json.
#     c) Restart ecra services, if they are not running.
#     d) Update PATH to be able to use pytest and dependent modules.
#     e) Convert python test files from .txt files to .py.
#  2) Form the correct pytest command with given test name and test report file.
#  3) Execute pytest command.
#
# The script exits with either success or failure code. i.e.,
#   exit 0 means, success, when script successfully completes all of the above mentioned steps.
#   exit 1 means, failure, when script fails in any of the above mentioned steps.
#-----------------------------------------------------------------------------
#    MODIFIED   (MM/DD/YY)
#    apotluri    07/21/25 - Enhancement Request 37982406 - COMBINE COVERAGE
#                           REPORTS FROM CLUSTERLESS SETUP AND REGULAR COVERAGE
#                           RUN SETUP
#    emekala     12/06/23 - ENH 35706176 - Source control Pipeline based
#                           infrapatching test automation job xml
#

set -x
this_script=$(readlink -f $0)
script_dir=$(dirname $this_script)
export http_proxy=

ECRA_INSTALL_ROOT=
INFRAPATHING_TEST_LOCATION=
TEST_INFRAPATCHING_CONFIG_FILE_LOCATION=
TEST_PAYLOAD_CONFIG_JSON_FILE_LOCATION=
TEST_REPORT_FILE=""
TEST_RESULTS_FOLDER="/tmp/"
TEST_JOB_NAME=""
IS_R1_ENV="False"
PYTHON_CMD_TO_RUN_PYTESTS='python3 -m pytest -vv -ra -s -m'
BACKUP_OLD_FILE=""
MERGE_FILES=""
DELETE_OLD_FILES=""
START_ECRA_SERVICES=""
SKIP_TESTS_FILE_LOCATION="${script_dir}/skip_tests.conf"

function usage() {
    echo -e
    echo "Usage: $0 [-j TEST_JOB_NAME] [ -r TEST_REPORT_FILE ] [-m yes] [-d yes] [-s yes]"
    echo -e
    echo -e "Explanation of options:"
    echo -e
    echo -e "-i <ECRA_INSTALL_FOLDER>"
    echo -e "    This is a mandatory parameter. The parameter value should point to ecra install folder location"
    echo -e
    echo -e "-j <TEST_JOB_NAME>"
    echo -e "    This is an optional parameter. The parameter value is the test job name. This determines which test"
    echo -e "    would be run as part this script execution."
    echo -e
    echo -e "    Possible values are"
    echo -e "    dom0_patch_prereq_check, dom0_patch, dom0_postcheck, dom0_rollback and etc.,"
    echo -e "    for other exadata hw components"
    echo -e
    echo -e "    For code_coverage_calculator job, code coverage related steps are run and"
    echo -e "    for other jobs, based on job name, required pytest command are formed."
    echo -e
    echo -e " -r <TEST_REPORT_FILE>"
    echo -e "    This is an optional parameter. If no value is specified, test report file not generated"
    echo -e
    echo -e " -m yes"
    echo -e "    This is an optional parameter. If value is yes and -r option specified then,"
    echo -e "    current test report merged with previous rest report file (which is backed up before new test run)"
    echo -e
    echo -e " -d yes"
    echo -e "    This is an optional parameter. If value is yes and -r option specified then, previous test report"
    echo -e "    file deleted"
    echo -e
    echo -e " -s yes"
    echo -e "    This is an optional parameter. If value is yes then, ECRA services are checked and started"
    echo -e

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

while getopts ":i:j:r:m:d:s:" options; do

    case "${options}" in
        i)
            ECRA_INSTALL_ROOT=${OPTARG}
            if [[ $ECRA_INSTALL_ROOT:0:1} == "-" ]]; then
                exit_abnormal
            fi
            ;;
        j)
            TEST_JOB_NAME=${OPTARG}
            if [[ ${TEST_JOB_NAME:0:1} == "-" ]]; then
                exit_abnormal
            fi
            ;;
        r)
            TEST_REPORT_FILE=${OPTARG}
            if [[ ${TEST_REPORT_FILE:0:1} == "-" ]]; then
                exit_abnormal
            fi
            TEST_RESULTS_FOLDER=$(dirname ${TEST_REPORT_FILE})
	    mkdir -p ${TEST_RESULTS_FOLDER}
          ;;
        m)
            MERGE_FILES=${OPTARG}
            if [[ ${MERGE_FILES:0:1} == "-" ]]; then
                exit_abnormal
            fi
          ;;
        d)
            DELETE_OLD_FILES=${OPTARG}
            if [[ ${DELETE_OLD_FILES:0:1} == "-" ]]; then
                exit_abnormal
            fi
          ;;
        s)
            START_ECRA_SERVICES=${OPTARG}
            if [[ ${START_ECRA_SERVICES:0:1} == "-" ]]; then
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

# make sure no duplicate tests are added in case of reruns
function check_and_delete_failure_error_case(){
  cat << EOF > check_and_delete_failure_error_case.py
#!/usr/bin/python3
import xml.etree.ElementTree as ET

tree = ET.parse("${TEST_REPORT_FILE}.bkp")
root = tree.getroot()

for testsuite in root.findall(".//testsuite[@errors='1']"):
    root.remove(testsuite)

for testsuite in root.findall(".//testsuite[@failures='1']"):
    root.remove(testsuite)

tree.write("${TEST_REPORT_FILE}.bkp")

EOF

  chmod 755 check_and_delete_failure_error_case.py
  timeout 60 python3 check_and_delete_failure_error_case.py
}

function exec_cmd()
{
  cmd="$*"
  ${cmd}
  if (( $? == 0 )); then
    echo -e "\nSuccessfully executed '${cmd}'\n"
  else
    echo -e "\nERROR: While executing '${cmd}'\n"
    exit 1
  fi
}

function run_test() {
  # this is only required on my local host to help ecra start its services.

  echo -e "\nPreparing run execution cmd..."
  cd ${INFRAPATHING_TEST_LOCATION}
  pip3 install --proxy=http://www-proxy-brmdc.us.oracle.com:80/ pytest > /dev/null 2>&1
  EXEC_CMD="${PYTHON_CMD_TO_RUN_PYTESTS} '${TEST_JOB_NAME}'"
  if [ ! -z ${TEST_REPORT_FILE} ]; then
      if [ -f "${TEST_REPORT_FILE}.bkp" ]; then
        check_and_delete_failure_error_case
      fi
      EXEC_CMD="${EXEC_CMD} --junitxml=${TEST_REPORT_FILE}"
      echo -e "\nTest report for ${TEST_JOB_NAME} job are stored in ${TEST_REPORT_FILE}\n"
  fi

  echo -e "Running cmd..."
  echo -e "\n${EXEC_CMD}\n"

  eval ${EXEC_CMD}
}

function merge_test_report_file() {
    echo -e
    if [[ ! -z "${TEST_REPORT_FILE}" && -f "${TEST_REPORT_FILE}.bkp" && -f "${TEST_REPORT_FILE}" ]]; then
        # required for merging test report
        pip3 install --proxy=http://www-proxy-brmdc.us.oracle.com:80/ junitparser > /dev/null 2>&1

        python3 -c "from junitparser import JUnitXml; full_report = JUnitXml.fromfile(\"${TEST_REPORT_FILE}.bkp\"); new_report = JUnitXml.fromfile(\"${TEST_REPORT_FILE}\"); full_report += new_report; full_report.write()"
        mv "${TEST_REPORT_FILE}.bkp" ${TEST_REPORT_FILE}
        echo -e "\nTest reports merged into: $TEST_REPORT_FILE"
    else
        echo -e "Test report files either missing or not sent. Hence not merging reports!"
    fi
    echo -e
}

function delete_test_report_file() {
    echo -e
    if [[ ! -z "${TEST_REPORT_FILE}" ]] && [[ -f "${TEST_REPORT_FILE}" || -f "${TEST_REPORT_FILE}.bkp" ]]; then
        rm -f ${TEST_REPORT_FILE}*
        echo -e "Deleted all matching files: ${TEST_REPORT_FILE}*"
    else
        echo -e "Test report file either missing or not sent. Hence not deleting!"
    fi
    echo -e
}

function backup_test_report_file() {
    echo -e
    if [[ ! -z "${TEST_REPORT_FILE}" && -f "${TEST_REPORT_FILE}" ]]; then
        if [[ -f "${TEST_REPORT_FILE}.bkp" ]]; then
            merge_test_report_file
        fi
        mv ${TEST_REPORT_FILE} ${TEST_REPORT_FILE}.bkp
        echo -e "Existing test report file backed up as: ${TEST_REPORT_FILE}.bkp"
    else
        echo -e "Test report file either missing or not sent. Hence not backing up!"
    fi
    echo -e
}

function prepare_env() {
    #
    # Sets the values for all the global variables declared and returns success(0) or failure(1).
    #

    echo -e "\nPrepare environment step started..."

    INFRAPATHING_TEST_LOCATION="${ECRA_INSTALL_ROOT}/mw_home/user_projects/domains/exacloud/exabox/infrapatching/test"
    TEST_INFRAPATCHING_CONFIG_FILE_LOCATION="${INFRAPATHING_TEST_LOCATION}/config/test_infrapatching.conf"
    TEST_PAYLOAD_CONFIG_JSON_FILE_LOCATION="${INFRAPATHING_TEST_LOCATION}/config/payload.json"

    echo -e "\nInfrapatching test location is ${INFRAPATHING_TEST_LOCATION}"

    if [ ! -f "$TEST_INFRAPATCHING_CONFIG_FILE_LOCATION" ]; then
        echo -e "\n${TEST_INFRAPATCHING_CONFIG_FILE_LOCATION} does not exist. Please make sure ${TEST_INFRAPATCHING_CONFIG_FILE_LOCATION} exists."
        return 1
    fi

    if [ ! -f "$TEST_PAYLOAD_CONFIG_JSON_FILE_LOCATION" ]; then
        echo -e "\n${TEST_PAYLOAD_CONFIG_JSON_FILE_LOCATION} does not exist. Please make sure ${TEST_PAYLOAD_CONFIG_JSON_FILE_LOCATION} exists."
        return 1
    fi

    # Add write perms to test_infrapatching.conf

    chmod +w $TEST_INFRAPATCHING_CONFIG_FILE_LOCATION

    # Add write permissions to cleanup_infrapatching_logs.conf so that tests can update metadata for ecra scheduler
    chmod +w "${ECRA_INSTALL_ROOT}/mw_home/user_projects/domains/exacloud/exabox/infrapatching/config/cleanup_infrapatching_logs.conf"

    local ecra_url=""
    local cmd_to_update_ecra_url=""
    local host_name=$(hostname --fqdn)

    # In R1 env all the test_config details are updated prior to execution of these tests
    IS_R1_ENV=$(grep is_r1_env $TEST_INFRAPATCHING_CONFIG_FILE_LOCATION | sed  's/\"is_r1_env\"//g;s/[ \":,]//g')
    if [ "$IS_R1_ENV" != "True" ]; then
        ecra_url="\"http:\/\/${host_name}:9001\/ecra\/endpoint\","
        # In test_infrapatching.conf file "ecraurl" is updated with correct hostname details.
        cmd_to_update_ecra_url="sed -i 's/\"ecraurl\".*/\"ecraurl\":${ecra_url}/g' ${TEST_INFRAPATCHING_CONFIG_FILE_LOCATION}"

        echo -e "\nCommand used to update ecra url in test_infrapatching.conf is:\n${cmd_to_update_ecra_url}"

        # Execute command to update ecraurl in test_infrapatching.conf
        eval "$cmd_to_update_ecra_url"

        # Pytest dependencies are installed locally in the automation machine
        export PATH=$HOME/.local/bin:$PATH
    fi

    echo -e "\nConverting .txt test files into .py"

    cd ${INFRAPATHING_TEST_LOCATION}
    for file in *.txt; do
        if [ -e $file ]; then
            mv "$file" "${file%.txt}.py"
        fi
    done

    echo -e "\nPrepare environment step completed."

    return 0
}

function check_ecra_services_status() {
    #
    # Checks ecra servcies status by looking for "result": "fail" string in the output of ecractl.sh status.
    #
    local status_output="/tmp/statusoutput.txt"
    rm -f $status_output
    $ECRA_INSTALL_ROOT/ecractl.sh status 2>&1 | tee -a $status_output
    filesize=$(wc -c <"$status_output")
    if [[ -f $status_output  && $filesize -gt 0 ]]; then 
        grep "\"result\": \"fail\"" $status_output
        if [ $? -ne 0 ];  then
            echo -e "\nAll the ECRA services are up and running."
            return 0
        else
            echo -e "\nAll the ECRA services are not up and running."
            return 1
        fi
    fi
    return 1
}

function restart_ecra_services() {
    #
    # Restarts ECRA services and checks for servcies status at the end.
    #
    echo
    $ECRA_INSTALL_ROOT/ecractl.sh stop
    $ECRA_INSTALL_ROOT/ecractl.sh start
    return $?
}

function check_and_start_ecra_services() {
    echo -e "\nChecking whether ECRA services are up and running, if not, ECRA services would be started..."
    check_ecra_services_status
    if [ $? -ne 0 ]; then
        echo -e "\nECRA services are down. Trying to restart ecra services..."
        restart_ecra_services
        if [ $? -ne 0 ]; then
            echo -e "\nECRA services are down even after restarting them. Exiting.."
            return 1
        fi
    fi

    return 0
}

function enable_exacloud_agent_in_code_coverage_mode() {
    #
    # Enables exacloud agent to run in code coverage mode, run the testsuite and generate the code coverage report.
    #e

    # Prepare the environment required for code coverage calculation
    python3 $INFRAPATHING_TEST_LOCATION/infrapatching_coverage_executor.py --enable_exacloud_agent_in_code_coverage_mode
    if [ $? -ne 0 ];  then
        echo -e "\nFailure occured while enabling code coverage mode with exacloud."
        return 1
    fi

    return 0
}

function generate_code_coverage_report() {

    # Generate code coverage report
    python3 $INFRAPATHING_TEST_LOCATION/infrapatching_coverage_executor.py --generate_code_coverage_report=${TEST_RESULTS_FOLDER}/infrapatching_text_summary_of_coverage_data.txt
    if [ $? -ne 0 ];  then
        echo -e "\nFailure occurred while generating the code coverage report."
        return 1
    fi

    return 0
}

function generate_time_profile_diff_data() {
    #
    # This generates time profile data containing duration difference for all infrapatch operations of current and previous successful runs
    #
    # Generate time profile diff data
    python3 $INFRAPATHING_TEST_LOCATION/infrapatching_coverage_executor.py --prepare_time_profile_data_diff=${TEST_RESULTS_FOLDER}/time_profile_diff.txt
    if [ $? -ne 0 ];  then
        echo -e "\nFailure occurred while generating the time profile diff data."
        return 1
    fi
    return 0
}

function get_ecra_ecs_label()
{
  check_and_start_ecra_services
  if [ $? -ne 0 ];  then
      return 1
  fi
set +x
  test_infrapatching_conf="${ECRA_INSTALL_ROOT}/mw_home/user_projects/domains/exacloud/exabox/infrapatching/test/config/test_infrapatching.conf"
  ecra_user=$(jq -r .ecrausername ${test_infrapatching_conf} | base64 -d)
  ecra_pass=$(jq -r .ecrapassword ${test_infrapatching_conf} | base64 -d)
  ecra_url=$(jq -r .ecraurl ${test_infrapatching_conf})

  ecra_version=$(curl --silent -u ${ecra_user}:${ecra_pass} -k -X GET --header 'Content-Type: application/json' --header 'Accept: application/json'  ${ecra_url}/version)
  if (( $? != 0 )); then
     return 1
  fi

  ecra_version=$(echo "${ecra_version}" | jq -r .dborch_version)
 
  echo "$ecra_version"
  
set -x
}

function patch_and_restart_services() {
set +x
    local domains_dir="$1"
    local tar_file="$2"
    local tar_content="$(tar -tf ${tar_file})"

    echo
    get_ecra_ecs_label
    if [ $? -ne 0 ];  then
        echo -e "\nError while getting ecra version"
        return 1
    fi
    echo

    cd ${domains_dir}/
    tar -xvf ${tar_file}
    if (( $? != 0 )); then
       echo -e "\nERROR: While untarring ${tar_file}\n"
       return 1
    fi
    echo -e "\n'${tar_file}' Successfully extracted\n"
    
    echo -e "\nVerifying if services requires restart"
    echo -e "${tar_content}" | grep -q ".py"
    if (( $? == 0 )); then
      echo -e "\n${tar_file} contains python files. Restarting exacloud...\n"
      cd ${domains_dir}/exacloud 
      exec_cmd "./bin/exacloud --agent stop -fsd"
      exec_cmd "./bin/exacloud --agent start -da"
      exec_cmd "./bin/exacloud --agent status"
    else
      echo -e "\n${tar_file} contains no python files. Not restarting exacloud\n"
    fi
    
    echo -e "${tar_content}" | grep -qe ecra.war -e ecra-ng.jar
    if (( $? == 0 )); then
      cd ${ECRA_INSTALL_ROOT}
      echo -e "${tar_content}" | grep -qe ecra.war
      if (( $? == 0 )); then
        echo -e "\n${tar_file} contains ecra war file. Restarting ecra wls...\n"
        exec_cmd "./ecractl.sh stopwls"  
        exec_cmd "./ecractl.sh startwls"  
      else
        echo -e "\n${tar_file} contains ecra jar file. Restarting ecra...\n"
        exec_cmd "./ecractl.sh stop_ecra_server"
        exec_cmd "./ecractl.sh start_ecra_server"
      fi
    else
      echo -e "\n${tar_file} contains no ecra war|jar files.\n"
    fi
set -x
}

function patch_user_changes() {
set +x
    tar_file="$(ls -1rt /tmp/patch_user_file/*.tar | head -1)"
    domains_dir="${ECRA_INSTALL_ROOT}/mw_home/user_projects/domains"
  
    if [[ ! -f "${tar_file}" ]]; then
      echo -e "\nERROR: Tar file is mandatory\n"
      return 1
    fi
    
    echo -e "\nChecking if tar file '${tar_file}' is valid...\n"
    tar -tvf ${tar_file}
    if (( $? == 0 )); then
      echo -e "\n${tar_file} is healthy\n"
    else
      echo -e "\nERROR: While checking tar file '${tar_file}'\n"
      return 1
    fi
    
    echo -e "\nBackup existing files that are matching with tar file contents\n"
    cd ${domains_dir}/
    tar_content="$(tar -tf ${tar_file})"
    backup_tar_file_name="before_user_changes.`date '+%Y%m%d%H%M%S'`.tar"
    matching_files_found_for_backup=1
    for _file in ${tar_content}
    do
      if [[ -f "${_file}" ]]; then
        matching_files_found_for_backup=0
        chmod 755 ${_file}
        tar -rvf ${backup_tar_file_name} ${_file}
        if (( $? != 0 )); then
          echo -e "ERROR: While tarring ${_file}"
          return 1
        fi
      fi
    done
    if [ $matching_files_found_for_backup -eq 0 ]; then
      echo -e "\nSuccessfuly backed up existing files and its located at : ${domains_dir}/${backup_tar_file_name}\n"
    else
      echo -e "\nNo matching files found for backup. Could be that all the files are newly added. Hence no backup tar file created\n"
    fi
    
    echo -e "\nPatching user changes from ${tar_file} under ${domains_dir}...\n"
    patch_and_restart_services ${domains_dir} ${tar_file}
    if [ $? -ne 0 ];  then
        echo -e "\nError while patching user changes"
        return 1
    fi
    echo -e "\nSuccessfully patched user changes from ${tar_file} under ${domains_dir}\n"
set -x
}

function restore_to_original_ecra_state() {
set +x
    domains_dir="${ECRA_INSTALL_ROOT}/mw_home/user_projects/domains"
  
    echo -e "\nGetting the initial version of backed up tar...\n"
    tar_file=$(ls -1rt ${domains_dir}/before_user_changes.*.tar 2>/dev/null | head -1)

    if [[ -z ${tar_file} ]]; then
     echo -e "\nUnable to get initial version of tar file. Seems like no user patches applied before.\n"
     return 0
    fi

    echo -e "\nReverting to original changes from ${tar_file} under ${domains_dir}...\n"
    patch_and_restart_services ${domains_dir} ${tar_file}
    if [ $? -ne 0 ];  then
        echo -e "\nError while reverting to original changes"
        return 1
    fi
    echo -e "\nSuccessfully reverted to original changes from ${tar_file} under ${domains_dir}\n"
set -x
}

function main() {
    #
    #  This does the following and returns success(0) or failure(1).
    #   1. Set all the global variables declared
    #   2. Check ecra services are running or not
    #   3. For code_coverage_calculator job, execute the required steps to get the code coverage report and
    #      for rest of the jobs, form the pytest command and execute it
    #

    if [[ ! -z "${DELETE_OLD_FILES}" && "${DELETE_OLD_FILES}" == "yes" ]]; then
        delete_test_report_file
        return 0
    fi


    prepare_env
    if [ $? -ne 0 ];  then
        echo -e "\nPreparation of the environment failed."
        return 1
    fi


    if [[ ! -z "${START_ECRA_SERVICES}" && "${START_ECRA_SERVICES}" == "yes" ]]; then
        check_and_start_ecra_services
        if [ $? -ne 0 ];  then
            return 1
        fi
    fi


    if [[ ! -z "${TEST_JOB_NAME}" ]] ; then
        # payload.json is updated when running the tests so need to correct permissions
        chmod +w $TEST_PAYLOAD_CONFIG_JSON_FILE_LOCATION

        # Execute tests
        if [[ "${TEST_JOB_NAME}" == "enable_exacloud_agent_in_code_coverage_mode" ]]; then
	    echo -e "\nEnabling code coverage mode with exacloud..."
            enable_exacloud_agent_in_code_coverage_mode
            if [ $? -ne 0 ];  then
	        echo -e "\nEnabling code coverage mode with exacloud failed."
                return 1
            fi
	elif [[ "${TEST_JOB_NAME}" == "generate_code_coverage_report" ]]; then
            echo -e "\nGenerating the code coverage report..."
            generate_code_coverage_report
            if [ $? -ne 0 ];  then
                echo -e "\nGenerating the code coverage report failed."
                return 1
            fi
	elif [[ "${TEST_JOB_NAME}" == "generate_time_profile_diff_data" ]]; then
	    echo -e "\nGenerating time profile diff data..."
            generate_time_profile_diff_data
            if [ $? -ne 0 ];  then
                echo -e "\nGenerating time profile diff data failed."
                return 1
            fi
	elif [[ "${TEST_JOB_NAME}" == "patch_user_changes" ]]; then
            patch_user_changes
            if [ $? -ne 0 ];  then
                echo -e "\nError while patching user changes"
                return 1
            fi
	elif [[ "${TEST_JOB_NAME}" == "restore_to_original_ecra_state" ]]; then
            restore_to_original_ecra_state
            if [ $? -ne 0 ];  then
                echo -e "\nError while reverting patching user changes"
                return 1
            fi
	elif [[ "${TEST_JOB_NAME}" == "get_ecra_ecs_label" ]]; then
            get_ecra_ecs_label
            if [ $? -ne 0 ];  then
                echo -e "\nError while getting ecra version"
                return 1
            fi
        # Execute tests
        else
            chmod +x $SKIP_TESTS_FILE_LOCATION
            skip_test_names=`cat ${SKIP_TESTS_FILE_LOCATION} | jq .SKIP_TESTS_FROM_EXECUTION | tr -d '"'`
            is_skip_test="no"
            if [[ ! -z "${skip_test_names}" ]]; then
                for skip_test_name in ${skip_test_names//,/ }
                do
                    if [[ ! -z "${skip_test_name}" && "${skip_test_name}" == "${TEST_JOB_NAME}" ]]; then
                        is_skip_test="yes"
                        echo -e "\nTest name: '${TEST_JOB_NAME}' specified against: SKIP_TESTS_FROM_EXECUTION in the file: $SKIP_TESTS_FILE_LOCATION\n"
                        cat $SKIP_TESTS_FILE_LOCATION
                        break
                    fi
                done
            fi

            if [ "${is_skip_test}" == "no" ]; then
                if [[ ! -z "${MERGE_FILES}" && "${MERGE_FILES}" == "yes" ]]; then
                    backup_test_report_file
                fi

                # now run the test
                run_test
                ret_code=$?

                if [[ ! -z "${MERGE_FILES}" && "${MERGE_FILES}" == "yes" ]]; then
                    merge_test_report_file
                fi

                if [ $ret_code -ne 0 ];  then
                    # Remove the write permission after test execution for payload.json
                    chmod -w $TEST_PAYLOAD_CONFIG_JSON_FILE_LOCATION
                    echo -e "\nFailure occured when executing tests."
                    return 1
                fi
            else
                echo -e "\nAs per user request, skipping the test: '${TEST_JOB_NAME}' from runtime execution!\n"
            fi
        fi

        # Revert write permissions to payload.json and test_infrapatching.conf
        chmod -w $TEST_PAYLOAD_CONFIG_JSON_FILE_LOCATION
        chmod -w $TEST_INFRAPATCHING_CONFIG_FILE_LOCATION
    fi

    return 0
}

main
if [ $? -eq 0 ]; then
    exit 0
else
    exit 1
fi
