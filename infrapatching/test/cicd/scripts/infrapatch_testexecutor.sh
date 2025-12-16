#!/bin/sh
#
# $Header: ecs/exacloud/exabox/infrapatching/test/cicd/scripts/infrapatch_testexecutor.sh /main/23 2025/04/09 16:39:08 sdevasek Exp $
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
# INPUT        :  -i <ECRA_INSTALL_ROOT>
#                    This is a mandatory parameter. The parameter value is the name of the folder where ecra is installed.
#                    Suppose, if ECRA is installed in /scratch/$USER/ecra_installs/automation, then /scratch/$USER/ecra_installs/automation
#                    should be passed as parameter value.
#
#              :  -j <TEST_JOB_NAME>
#                    This is a mandatory parameter. The parameter value is the test job name. This determines which tests would be run as part
#                    this script execution.
#
#                    Possible values are
#                    rolling_patch_dom0_cell, rolling_rollback_dom0_cell, non_rolling_patch_dom0_cell, non_rolling_rollback_dom0_cell,
#                    rolling_domu, rolling_switch ,rolling_patch_dom0_cell_with_include_list, rolling_rollback_dom0_cell_with_include_list,
#                    rolling_domu_with_include_list and code_coverage_calculator
#
#                    For code_coverage_calculator job, code coverage related steps are run and
#                    for other jobs, based on job name, required pytest markers and test result file for pytest command are formed.
#                    Suppose, if rolling_domu is choosen, then the following format of pytest would get formed.
#                    python3 -m pytest -vv -ra -s -m 'domu_patch_prereq_check or domu_patch or domu_rollback' --junitxml=${TEST_RESULTS_LOCATION}/domu_test_results.xml
#
#              :  -r <TEST_RESULTS_LOCATION>
#                    This is an optional parameter. If no value is specified, test results file gets stored in directory
#                    where test files are present(Eg:/scratch/sdevasek/ecra_installs/automate/mw_home/user_projects/domains/exacloud/exabox/infrapatching/test).
#
# Note:-
# The following is the example for the usage of the script.
#
# infrapatch_testexecutor.sh -i /scratch/sdevasek/ecra_installs/cicd -j rolling_switch
#   Here the script is going to execute switch tests.
#
# This script does the following
#  1) Make the environment ready, before executing the pytest.
#     a) Update ecraurl in test_infrapatching.conf with corret value.
#     b) Add write permissions to test_infrapatching.conf and payload.json.
#     c) Restart ecra services, if they are not running.
#     d) Update PATH to be able to use pytest and dependent modules.
#     e) Convert python test files from .txt files to .py.
#  2) Form the correct pytest command with correct test markers and test results file.
#  3) Execute pytest command.
#
# The script exits with either success or failure code. i.e.,
#   exit 0 means, success, when script successfully completes all of the above mentioned steps.
#   exit 1 means, failure, when scipt fails in any of the above mentioned steps.
#-----------------------------------------------------------------------------
#    MODIFIED   (MM/DD/YY)
#    sdevasek    04/02/25 - Enh 37501751 -TEST ADDITION FOR THE VALIDATION OF
#                           JOB SCHEDULER TO CLEAN PATCHES ON THE LAUNCHNODE
#                           FOR SINGLE VM CASE TEST IN X9M ENV
#    araghave    11/22/24 - Enh 37241595 - TEST CHANGES TO REPLACE ALL IBSWITCH
#                           REFERENCE WITH GENERIC SWITCH REFERENCES IN INFRA
#                           PATCHING TEST CODE
#    araghave    08/03/23 - Enh 35661378 - ADD DOM0 PATCHING CRS TESTS : DOM0
#                           POSTCHECK SHOULD STARTUP CRS ON ALL VMS IF CRS IS
#                           DOWN
#    emekala     07/18/23 - ENH 35610691 - INFRAPATCHING TEST AUTOMATION - Run
#                           SMR (Exasplice) as part of code coverage test suite
#    araghave    06/30/23 - Enh 35552878 - EXACOMPUTE TEST ADDITION FOR
#                           EXASPLICE PATCH OPERATIONS
#    emekala     05/12/23 - ENH 35330659 - Infrapatching Test Automation -
#                           Tracking ticket to enable Exasplice test suite in
#                           Jenkins for periodical execution
#    emekala     04/20/23 - Enh 35000319 - TEST ADDITION TO VALIDATE EXASPLICE
#                           SCENARIO IN INFRAPATCHING AUTOMATION
#    sdevasek    04/19/23 - ENH 35293707 - TEST ADDITION TO VALIDATE SINGLENODE
#                           UPGRADENAME INCLUDENODELIST COMBINATIONS
#    emekala     04/14/23 - ENH 35204492 - HEARTBEAT FAILURE ERROR CODE IS
#                           GETTING OVERRIDDEN WITH GENERIC ERROR CODE
#                           0X03010007 FOR DOM0 POSTCHECK FAILURE
#    emekala     03/13/23 - Enh 35173839 - TEST DEPENDENCY ADDITION FOR 
#                           EXACOMPUTE_BACKUP TESTS WITH ROLLBACK TESTS
#    emekala     02/27/23 - Enh 35123619 - TEST DEPENDENCY ADDITION FOR BACKUP 
#                           TESTS WITH ROLLBACK TESTS
#    emekala     02/15/23 - Enh 35027349 - ENABLE POSTCHECK AND BACKUP_IMAGE
#                           TESTS IN INFRAPATCHING AUTOMATION
#    sdevasek    01/23/23 - ENH 35005477 - ENABLE DOMU TEST TO VALIDATE EXADATA
#                           ERROR FRAMEWORK AND UPDATE IMAGE REFRESHER SCRIPT
#                           TO USE NEW ECRA INSTALL FOLDER PARAM
#    araghave    01/15/23 - ENH 34513424 - TEST ADDITION TO INFRAPATCH
#                           AUTOMATION TO COVER EXACOMPUTE PATCHING FLOW
#    sdevasek    01/03/23 - ENH 34862465 - UPDATE INFRAPATCHING TEST CODE FOR
#                           ECRA UPGRADE TO WORK IN X9M R1 ENV
#    sdevasek    12/20/22 - ENH 33893463 - UPDATE INFRAPATCH TEST AUTOMATION TO
#                           PROVIDE DIFFS OF TIME PROFILE FOR MAJOR OPERATIONS
#                           ACROSS CURRENT AND PREVIOUS RUNS
#    sdevasek    04/26/22 - ENH 34088744 - ENABLE TESTS FOR KSPLICE AND ONEOFF
#                           OPERATIONS IN INFRAPTACHING AUTOMATION
#    sdevasek    03/14/22 - Enh-33321832 - GET CODE COVERAGE REPORT FOR
#                           INFRAPATCHING PYTHON CODE
#    sdevasek    17/02/22 - Enh-33737906 - TEST ADDITION TO THE INFRAPATCHING
#                           AUTOMATION FOR EXACLOUD PLUGINS
#    sdevasek    07/01/22 - Bug33722164 - RESTART ECRA SERVICES WHEN NOT RUNNING
#                           DURING TEST JOB EXECUTION IN AUTOMATION
#    sdevasek    12/14/21 - Enh33496885 - IMPLEMENT DRIVER SCRIPT TO EXECUTE
#                           TESTS IN INFRAPATCHING AUTOMATION
#

set -x

JOB_ARRAY=("rolling_patch_dom0_cell" "rolling_rollback_dom0_cell" "non_rolling_patch_dom0_cell" "non_rolling_rollback_dom0_cell" "rolling_domu" "rolling_switch" "patch_exacompute" "patch_exacompute_exasplice")
JOB_ARRAY_FOR_SUBSET_NODE_PATCHING=("rolling_patch_dom0_cell_with_include_list" "rolling_rollback_dom0_cell_with_include_list" "rolling_domu_with_include_list")
JOB_ARRAY_FOR_CODE_COVERAGE=("code_coverage_calculator")
ECRA_INSTALL_ROOT=""
INFRAPATHING_TEST_LOCATION=""
TEST_INFRAPATCHING_CONFIG_FILE_LOCATION=""
TEST_PAYLOAD_CONFIG_JSON_FILE_LOCATION=""
TEST_RESULTS_FILE=""
TEST_MARKERS=""
TEST_JOB_NAME=""
TEST_RESULTS_LOCATION=""
IS_R1_ENV="False"

function usage() {
    echo "Usage: $0 [ -i ECRA_INSTALL_ROOT ] [-j TEST_JOB_NAME] [ -r TEST_RESULTS_LOCATION ]"
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

while getopts ":i:j:r:" options; do

    case "${options}" in
        i)
            ECRA_INSTALL_ROOT=${OPTARG}
            if [[ ${ECRA_INSTALL_ROOT:0:1} == "-" ]]; then
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
            TEST_RESULTS_LOCATION=${OPTARG}
            if [[ ${TEST_RESULTS_LOCATION:0:1} == "-" ]]; then
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
if [ -z "$ECRA_INSTALL_ROOT" ]; then
    echo "Error: -i is the mandatory parameter to be passed."
    exit_abnormal
else
    if [ ! -d "$ECRA_INSTALL_ROOT" ]; then
        echo "${ECRA_INSTALL_ROOT} does not exist. Please check the parameter value ${ECRA_INSTALL_ROOT} passed for ECRA install folder is correct."
        exit 1
    fi
    INFRAPATHING_TEST_LOCATION="${ECRA_INSTALL_ROOT}/mw_home/user_projects/domains/exacloud/exabox/infrapatching/test"

    if [ ! -d "$INFRAPATHING_TEST_LOCATION" ]; then
        echo "${INFRAPATHING_TEST_LOCATION} does not exist. Please check the parameter value ${ECRA_INSTALL_ROOT} passed for ECRA install folder is correct."
        exit 1
    fi
fi

# -j is the mandatory parameter
if [ -z "$TEST_JOB_NAME" ]; then
    echo "Error: -j is the mandatory parameter to be passed."
    exit_abnormal
else
    job_name_found_in_input=false
    # Merge JOB_ARRAY_FOR_SUBSET_NODE_PATCHING and JOB_ARRAY_FOR_CODE_COVERAGE into JOB_ARRAY
    JOB_ARRAY=( "${JOB_ARRAY[@]}" "${JOB_ARRAY_FOR_SUBSET_NODE_PATCHING[@]}" "${JOB_ARRAY_FOR_CODE_COVERAGE[@]}" )
    for job in ${JOB_ARRAY[@]}; do
        if [ "${job}" == "${TEST_JOB_NAME}" ] ; then
            job_name_found_in_input=true
        fi
    done

    if [[ "${job_name_found_in_input}" != "true" ]]; then
        echo "${TEST_JOB_NAME} is not a valid job name. Please provide a valid job name from the below."
        for job in ${JOB_ARRAY[@]}; do
            echo "  ${job}"
        done
        exit 1
    fi
fi

# -r is an optional parameter
if [ -z "$TEST_RESULTS_LOCATION" ]; then
    # When no location is specified to the script, test results get stored in test folder of infrapatching
    TEST_RESULTS_LOCATION="${INFRAPATHING_TEST_LOCATION}"
else
    if [ ! -d "$TEST_RESULTS_LOCATION" ]; then
        echo "${TEST_RESULTS_LOCATION} does not exist. Please check the parameter value ${TEST_RESULTS_LOCATION} passed for test results location is correct."
        exit 1
    fi
fi

function prepare_env() {
    #
    # Sets the values for all the global variables declared and returns success(0) or failure(1).
    #

    local ecra_url=""
    local cmd_to_update_ecra_url=""
    local host_name=$(hostname --fqdn)

    TEST_INFRAPATCHING_CONFIG_FILE_LOCATION="${INFRAPATHING_TEST_LOCATION}/config/test_infrapatching.conf"
    TEST_PAYLOAD_CONFIG_JSON_FILE_LOCATION="${INFRAPATHING_TEST_LOCATION}/config/payload.json"

    if [ ! -f "$TEST_INFRAPATCHING_CONFIG_FILE_LOCATION" ]; then
        echo "${TEST_INFRAPATCHING_CONFIG_FILE_LOCATION} does not exist. Please make sure ${TEST_INFRAPATCHING_CONFIG_FILE_LOCATION} exists."
        return 1
    fi

    if [ ! -f "$TEST_PAYLOAD_CONFIG_JSON_FILE_LOCATION" ]; then
        echo "${TEST_PAYLOAD_CONFIG_JSON_FILE_LOCATION} does not exist. Please make sure ${TEST_PAYLOAD_CONFIG_JSON_FILE_LOCATION} exists."
        return 1
    fi

    echo "Infrapatching test location is ${INFRAPATHING_TEST_LOCATION}."

    # Add write perms to test_infrapatching.conf

    chmod +w $TEST_INFRAPATCHING_CONFIG_FILE_LOCATION

    # Add write permissions to cleanup_infrapatching_logs.conf so that tests can update metadata for ecra scheduler
    chmod +w "${ECRA_INSTALL_ROOT}/mw_home/user_projects/domains/exacloud/exabox/infrapatching/config/cleanup_infrapatching_logs.conf"
    
    # In R1 env all the test_config details are updated prior to execution of these tests
    IS_R1_ENV=$(grep is_r1_env $TEST_INFRAPATCHING_CONFIG_FILE_LOCATION | sed  's/\"is_r1_env\"//g;s/[ \":,]//g')
    if [ "$IS_R1_ENV" != "True" ]; then
        ecra_url="\"http:\/\/${host_name}:9001\/ecra\/endpoint\","
        # In test_infrapatching.conf file "ecraurl" is updated with correct hostname details.
        cmd_to_update_ecra_url="sed -i 's/\"ecraurl\".*/\"ecraurl\":${ecra_url}/g' ${TEST_INFRAPATCHING_CONFIG_FILE_LOCATION}"

        echo "Command used to update ecra url in test_infrapatching.conf is ${cmd_to_update_ecra_url}"

        # Execute command to update ecraurl in test_infrapatching.conf
        eval "$cmd_to_update_ecra_url"
    fi

    # Other than code_coverage_calculator job, for rest of the jobs, test markers and rest results files are required and are updated here.
    if [[ "${TEST_JOB_NAME}" != "code_coverage_calculator" ]]; then

        # Update test results file name and test markers based on test job name to be executed.
        case "$TEST_JOB_NAME" in
        'rolling_patch_dom0_cell')
            TEST_RESULTS_FILE="${TEST_RESULTS_LOCATION}/rolling_patch_dom0_cell_test_results.xml"
            TEST_MARKERS="'cell_patch_prereq_check or cell_patch or cell_postcheck or dom0_patch_prereq_check or dom0_patch or dom0_postcheck or dom0_postcheck_crs_validation'"
            ;;
        'rolling_rollback_dom0_cell')
            TEST_RESULTS_FILE="${TEST_RESULTS_LOCATION}/rolling_rollback_dom0_cell_test_results.xml"
            TEST_MARKERS="'cell_rollback or cell_rollback_prereq_check or dom0_rollback'"
            ;;
        'non_rolling_patch_dom0_cell')
            TEST_RESULTS_FILE="${TEST_RESULTS_LOCATION}/non_rolling_patch_dom0_cell_test_results.xml"
            TEST_MARKERS="'cell_patch_prereq_check or cell_patch_non_rolling or dom0_patch_prereq_check or dom0_patch_non_rolling'"
            ;;
        'non_rolling_rollback_dom0_cell')
            TEST_RESULTS_FILE="${TEST_RESULTS_LOCATION}/non_rolling_rollback_dom0_cell_test_results.xml"
            TEST_MARKERS="'cell_rollback_non_rolling  or cell_rollback_prereq_check or dom0_rollback_non_rolling'"
            ;;
        'rolling_domu')
            TEST_RESULTS_FILE="${TEST_RESULTS_LOCATION}/domu_test_results.xml"
            TEST_MARKERS="'domu_patch_prereq_check or domu_patch or domu_rollback or domu_postcheck or domu_patch_prereq_check_patch_mgr_failure'"
            ;;
        'rolling_switch')
            TEST_RESULTS_FILE="${TEST_RESULTS_LOCATION}/switch_test_results.xml"
            TEST_MARKERS="'switch_patch_prereq_check or switch_one_off or switch_patch or switch_rollback or switch_rollback_prereq_check or switch_postcheck'"
            ;;
        'rolling_patch_dom0_cell_with_include_list')
            TEST_RESULTS_FILE="${TEST_RESULTS_LOCATION}/rolling_patch_dom0_cell_with_include_list_test_results.xml"
            TEST_MARKERS="'cell_patch_prereq_check_with_include_list or dom0_ksplice_list or cell_ksplice_list or cell_patch_with_include_list or dom0_patch_prereq_check_with_include_list or dom0_patch_with_include_list'"
            ;;
        'rolling_rollback_dom0_cell_with_include_list')
            TEST_RESULTS_FILE="${TEST_RESULTS_LOCATION}/rolling_rollback_dom0_cell_with_include_list_test_results.xml"
            TEST_MARKERS="'cell_rollback_with_include_list or dom0_one_off or cell_one_off or cell_rollback_prereq_check_with_include_list or dom0_rollback_with_include_list'"
            ;;
        'rolling_domu_with_include_list')
            TEST_RESULTS_FILE="${TEST_RESULTS_LOCATION}/domu__with_include_list_test_results.xml"
            TEST_MARKERS="'domu_patch_prereq_check_with_include_list or domu_patch_prereq_check_with_single_node_name or domu_one_off or domu_patch_with_include_list or domu_rollback_with_include_list or domu_patch_prereq_check_patch_mgr_failure'"
            ;;
          'patch_exacompute')
            TEST_RESULTS_FILE="${TEST_RESULTS_LOCATION}/patch_exacompute_test_results.xml"
            TEST_MARKERS="'exacompute_precheck or exacompute_patch or exacompute_rollback or exacompute_postcheck'"
            ;;
          'patch_exacompute_exasplice')
            TEST_RESULTS_FILE="${TEST_RESULTS_LOCATION}/patch_exacompute_test_results.xml"
            TEST_MARKERS="'exacompute_exasplice_precheck or exacompute_exasplice_patch or exacompute_exasplice_rollback'"
            ;;
        esac

        echo "Test results for ${TEST_JOB_NAME} job are stored in ${TEST_RESULTS_FILE}."
        echo "Pytest markers used in ${TEST_JOB_NAME} job are ${TEST_MARKERS}."
    fi

    return 0
}

function check_ecra_services_status() {
    #
    # Checks ecra servcies status by looking for "result": "fail" string in the output of ecractl.sh status.
    #
    local status_output="/tmp/statusoutput.txt"
    rm -f $status_output
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
    # Restarts ECRA services and checks for servcies status at the end.
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

function execute_steps_required_to_get_code_coverage() {
    #
    # Enables exacloud agent to run in code coverage mode, run the testsuite and generate the code coverage report.
    #

    # Prepare the environment required for code coverage calculation
    python3 $INFRAPATHING_TEST_LOCATION/infrapatching_coverage_executor.py --enable_exacloud_agent_in_code_coverage_mode
    if [ $? -ne 0 ];  then
        echo "Failure occured while enabling code coverage mode with exacloud."
        return 1
    fi

    # Run the tests to capture the coverage data
    python3 $INFRAPATHING_TEST_LOCATION/infrapatching_coverage_executor.py --collect_coverage_data=$TEST_RESULTS_LOCATION
    if [ $? -ne 0 ];  then
        echo "Failure occured when executing the tests to capture the code coverage."
        return 1
    fi

    # Generate code coverage report
    python3 $INFRAPATHING_TEST_LOCATION/infrapatching_coverage_executor.py --generate_code_coverage_report=$TEST_RESULTS_LOCATION/infrapatching_text_summary_of_coverage_data.txt
    if [ $? -ne 0 ];  then
        echo "Failure occurred while generating the code coverage report."
        return 1
    fi

    return 0
}

function generate_time_profile_diff_data() {
    #
    # This generates time profile data containing duration difference for all infrapatch operations of current and previous successful runs
    #
    # Generate time profile diff data
    python3 $INFRAPATHING_TEST_LOCATION/infrapatching_coverage_executor.py --prepare_time_profile_data_diff=$TEST_RESULTS_LOCATION/time_profile_diff.txt
    if [ $? -ne 0 ];  then
        echo "Failure occurred while generating the time profile diff data."
        return 1
    fi
    return 0
}

function main() {
    #
    #  This does the following and returns success(0) or failure(1).
    #   1. Set all the global variables declared
    #   2. Check ecra services are running or not
    #   3. For code_coverage_calculator job, execute the required steps to get the code coverage report and
    #      for rest of the jobs, form the pytest command and execute it
    #

    echo "Prepare environment step started."
    prepare_env
    if [ $? -ne 0 ];  then
        echo "Preparation of the environment failed."
        return 1
    fi
    echo "Prepare environment step completed."

    # Remove the old test result file
    rm -f ${TEST_RESULTS_FILE}


    echo "Checking whether ECRA services are up and running, if not, ECRA services would be started."
    check_ecra_services_status
    if [ $? -ne 0 ]; then
        echo "ECRA services are down. Trying to restart ecra services.."
        restart_ecra_services
        if [ $? -ne 0 ]; then
            echo "ECRA services are down even after restarting them. Exiting.."
            return 1
        fi
    fi

    if [ "$IS_R1_ENV" != "True" ]; then
        # Pytest dependencies are installed locally in the automation machine
        export PATH=$HOME/.local/bin:$PATH
    fi

    echo "Converting .txt test files into .py"
    # Convert all .txt test files into .py
    cd ${INFRAPATHING_TEST_LOCATION}
    for file in *.txt; do
      if [ -e $file ]; then
        mv "$file" "${file%.txt}.py"
      fi
    done

    # payload.json is updated when running the tests so need to correct permissions
    chmod +w $TEST_PAYLOAD_CONFIG_JSON_FILE_LOCATION

    # Execute code coverage steps
    if [[ "${TEST_JOB_NAME}" == "code_coverage_calculator" ]]; then
        execute_steps_required_to_get_code_coverage
        if [ $? -ne 0 ];  then
            echo "Executing the steps to get code coverage report failed."
            return 1
        fi
        generate_time_profile_diff_data
        if [ $? -ne 0 ];  then
          echo "Generating time profile diff data failed."
          return 1
        fi
    # Execute tests
    else
        test_executor_cmd="python3 -m pytest -vv -ra -s -m ${TEST_MARKERS}  --junitxml=${TEST_RESULTS_FILE}"
        echo "Command used to execute tests is : ${test_executor_cmd}"
        eval "$test_executor_cmd"
        if [ $? -ne 0 ];  then
            # Remove the write permission after test execution for payload.json
            chmod -w $TEST_PAYLOAD_CONFIG_JSON_FILE_LOCATION
            echo "Failure occured when executing tests."
            return 1
        fi
        echo "All tests got executed successfully."
    fi

    # Revert write permissions to payload.json and test_infrapatching.conf
    chmod -w $TEST_PAYLOAD_CONFIG_JSON_FILE_LOCATION
    chmod -w $TEST_INFRAPATCHING_CONFIG_FILE_LOCATION

    return 0
}

main
if [ $? -eq 0 ]; then
    echo "Jenkins job - ${TEST_JOB_NAME} got succeeded."
    exit 0
else
    echo "Jenkins job - ${TEST_JOB_NAME} failed."
    exit 1
fi
