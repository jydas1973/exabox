#!/bin/sh +x
#
# $Header: ecs/exacloud/exabox/exatest/exatest.sh /main/39 2021/03/26 10:22:27 jesandov Exp $
#
# exatest.sh
#
# Copyright (c) 2018, 2021, Oracle and/or its affiliates. 
#
#    NAME
#      exatest.sh - command line tool to run exatest
#
#    DESCRIPTION
#      This script can run all the test in the folder exatest using the framework of unitest
#      In addition can install the python package
#
#    NOTES
#      Actual options are "-install [-use_ecs_oeda], -srg [-txn], -run [-all|<filename>] [-use_ecs_oeda], -pylint [-txn|<filename>]"
#
#    MODIFIED   (MM/DD/YY)
#    alsepulv    02/17/21 - Bug 32513420 : Correct return codes in runPylint()
#                           and runPylintOne()
#    jlombera    10/06/20 - Bug 31961132: don't repeat failed tests nor abort
#                           on first failed test by default
#    ndesanto    09/25/20 - Added code to create /var/run/ecmysql_<user_id> for
#                           Farm, QA and dev environments
#    ndesanto    04/13/20 - 31118633 - ADD OEDA label fall fallback
#    ndesanto    09/19/19 - 30374491 - EXACC PYTHON 3 MIGRATION BATCH 01
#    ndesanto    09/19/19 - 30294648 - IMPLEMENT PYTHON 3 MIGRATION WHITELIST ON EXATEST
#    ndesanto    05/06/19 - Removed a pipe to /dev/stdout that was not needed 
#    jesandov    12/10/18 - Add pylint test
#    jesandov    07/17/18 - Creation of the file for exacloud unit test
#


# Compute basepath
realpath_cmd="realpath --no-symlinks"
# shellcheck disable=SC2086
abspath="$(${realpath_cmd} $0)"
# shellcheck disable=SC2086
dname="$(dirname ${abspath})"
# shellcheck disable=SC2086
basepath="$(${realpath_cmd} ${dname}/../..)"

cleanup() {

    echo "Delete suc and dif file"
    rm -f "${basepath}/exabox/exatest/exatest*.suc"
    rm -f "${basepath}/exabox/exatest/exatest*.dif"

    echo "Delete log/exatest folder"
    rm -rf "${basepath}/log/exatest/"

    echo "Cleanup done"
}

write_succ_diff() {
    rc="$1"
    testname="$2"

    # Clean up old suc and dif
    rm -f "$basepath/exabox/exatest/exatest_${testname}.suc"
    rm -f "$basepath/exabox/exatest/exatest_${testname}.dif"

    # Create new suc and diff
    if [ "$rc" -eq 0 ]; then
        echo "Exatest success $rc" > "${basepath}/exabox/exatest/exatest_${testname}.suc" 2>&1
    else
        echo "Exatest failure $rc" > "${basepath}/exabox/exatest/exatest_${testname}.dif" 2>&1
    fi
}

my_exit() {
    if [ -n "$2" ]; then
        write_succ_diff "$1" "$2"
    fi

    # Exit the program
    if [ "$1" != 0 ]; then
        exit "$1"
    fi
}

get_config() {

    res=$(test -f "${basepath}/config/exatest_extra_config.conf" &&
          grep "$1" "${basepath}/config/exatest_extra_config.conf" | 
          awk '{print $2}' | 
          sed "s/[,\"']//g" 2>&1)

    if [ "${res}" = "" ]; then
        echo "$2"
    else
        echo "${res}"
    fi
}

usage() {
   echo "$0: "
   echo "  -h"
   echo "  -install"
   echo "  -srg [-txn] [-all]"
   echo "  -run [-all|<filename>]"
   echo "  -pylint [<filename>]"
   echo "  -cleanup"
}

# Configuration part on the config
test_retries=$(get_config "exatest_retries" "1")
exit_on_error=$(get_config "exatest_exit_on_error" "false")
use_oeda=$(get_config "use_oeda" "true")

install() {
    if [ ! -f "${basepath}/opt/py3_venv/bin/python" ];
    then
        "${basepath}/bin/py3_venv.sh" -addons > /dev/null 2>&1
        if [ "$1" = "-debug" ];
        then
            python_version=$( "${basepath}/opt/py3_venv/bin/python" --version 2>&1 )
            echo "Complete Installation ${python_version}"
        fi
    else
        if [ "$1" = "-debug" ];
        then
            python_version=$( "${basepath}/opt/py3_venv/bin/python" --version 2>&1 )
            echo "Already Installed ${python_version}" 
        fi
    fi
    
    #Install the WorkDir
    if [ "$1" != "-debug" ];
    then
        folder_name=$(uuidgen)
        mkdir -p "${basepath}/log/exatest/"
        mkdir -p "${basepath}/log/exatest/${folder_name}"
        echo "WorkDir: ${basepath}/log/exatest/${folder_name}" 
    fi

    if [ "$1" = "-srg" ] || [ "$1" = "-pylint" ];
    then
        mkdir -p "${basepath}/log/exatest/oeda"
        mkdir -p "${basepath}/log/exatest/oeda/linux-x64"
        echo "NO OEDA" > "${basepath}/log/exatest/oeda/label.txt"
        echo "Skip OEDA Install" 
        return
    fi

    #Create ecmysql dictionary on Farm, QA and dev environments
    RUN_AS_ROOT="/usr/local/packages/aime/install/run_as_root"
    if [ -f "${RUN_AS_ROOT}" ]; then
        ECMYSQL_PATH="/var/run/ecmysql_$(id -u)"
        if [ ! -d "${ECMYSQL_PATH}" ]; then
            "${RUN_AS_ROOT}" "mkdir ${ECMYSQL_PATH}"
            "${RUN_AS_ROOT}" "chmod 755 ${ECMYSQL_PATH}"
            "${RUN_AS_ROOT}" "chown $(id -un):$(id -gn) ${ECMYSQL_PATH}"
            echo "This directory and the files contained in it are required by Exacloud, do not delete it." > "${ECMYSQL_PATH}/DO_NOT_DELETE.txt"
        fi
    fi

    #Install OEDA
    if [ "$use_oeda" == "false" ]; then
        return
    fi

    use_oss=1
    # Iterate over args to find -use_ecs_oeda
    for var in "$@"
    do
        if [ "$var" = "-use_ecs_oeda" ]; then
            use_oss=0
            echo "Taking OEDA from ECS label" 
        fi
    done

    label_OSS=$( ade showlabels -series OSS_MAIN_LINUX.X64 -latest -public | tail -1 )
    label_ECS=$( ade showlabels -series ECS_MAIN_LINUX.X64 -latest -public | tail -1 )
    if [ $use_oss -eq 1 ]; then
        label="${label_OSS}"
        label_fallback="${label_ECS}"
    else
        label="${label_ECS}"
        label_fallback="${label_OSS}"
    fi
    if [ ! -f "${basepath}/log/exatest/oeda" ]; then
        oeda "${label}" "${label_fallback}"
    else
        if [ ! -f "${basepath}/log/exatest/oeda/label.txt" ]; then
            oeda "${label}" "${label_fallback}"
        else
            echo "${label}" > "${basepath}/log/exatest/oeda/label2.txt"
            if ! diff "${basepath}/log/exatest/oeda/label2.txt" "${basepath}/log/exatest/oeda/label.txt" ; then
                oeda "${label}" "${label_fallback}"
            else
                echo "Already Installed OEDA ${label}"
            fi
        fi
    fi
}

oeda() {
    if ! oeda_internal "$1" ; then
        oeda_internal "$2"
    fi
}

oeda_internal() {
    oedapath=$( ade describe -label "$1" -labelserver )
    rm -rf "${basepath}/log/exatest/oeda"
    mkdir -p "${basepath}/log/exatest/oeda"
    if [ -d "${oedapath}/ecs/oeda/oss" ]; then
        #ECS VIEW
        cp "${oedapath}"/ecs/oeda/oss/Ocmd*OTN*linux* "${basepath}/log/exatest/oeda"
        retval=$?
    else
        #OSS VIEW
        cp "${oedapath}"/oss/bin/Ocmd*OTN*linux* "${basepath}/log/exatest/oeda"
        retval=$?
    fi
    if [ $retval -ne 0 ]; then
        return 1
    fi
    (cd "${basepath}/log/exatest/oeda" || exit; unzip Ocmd*OTN*linux*) > /dev/null
    echo "$1" > "${basepath}/log/exatest/oeda/label.txt"
    echo "Install OEDA $1" 
    return 0
}

runPylint() {
    echo "*** Running Pylint on Exacloud Code ***" 
    testfail="false"

    #Calculate the files
    fileExp=$( find "${basepath}/exabox" | grep "\.py$" | grep -v "\.ade\|\_\_" | sort )
    if [ "$1" = "-txn" ]; then
        echo "Running Pylint only on transaction files" 
        fileExp=$( ade describetrans -short | grep "exacloud" | grep "\.py" | awk '{print $2}' | sed "s@ecs/exacloud/@@g" | uniq )
    fi

    if [ "${fileExp}" = "" ]; then
        echo "No files to check with Pylint"
        my_exit 0 "pylint"
        return
    fi

    for file in ${fileExp}; do
        filex="$(echo "${file}" | sed "s@${basepath}@@g")"
        ( runPylintOne "${basepath}/${filex}" ) || testfail="true"
    done

    if [ "${testfail}" = "true" ]; then
        echo "### Exatest Pylint check code and found issues" 
        my_exit 4 "pylint"
    else
        my_exit 0 "pylint"
    fi
}

runPylintOne() {
    #Create work folder
    rc=1
    work="${basepath}/log/exatest/${folder_name}/pylint"
    mkdir -p "${work}"

    #Check Pylint exists
    if [ ! -e "${basepath}/opt/py3_venv/bin/pylint" ]; then
        echo "### Exatest: No Pylint package installed" 
        echo "Trying auto install" 
        "${basepath}/bin/py3_venv.sh" -addons
        if [ ! -e "${basepath}/opt/py3_venv/bin/pylint" ]; then
            echo "### Exatest: Still no Pylint package installed" 
            my_exit 3 "pylint_install"
        fi
    fi

    if [ "$2" = "multi" ]; then
        file=$1
        outfile="pylint_report.log"		
    else
        # shellcheck disable=SC2086
        file="$(${realpath_cmd} $1)"
        outfile=$( echo "${file}" | awk -F "/" '{print $NF}' | sed "s/.py/.log/g" )
    fi

    # Getting the CPU cores for the parallel processing of the files	
    cpucores=$(grep -c processor /proc/cpuinfo)
    
    echo "Check File: ${file}" 
    "${basepath}/bin/python" -m pylint -j "${cpucores}" -E "${file}" 2>&1 | grep -v "No config file found" | tee "${work}/${outfile}"

    #Check if something fails
    grep -q -E "E[0-9]+:" "${work}/${outfile}" || rc=0
    return "${rc}"
}

runall() {
    for f in "${basepath}"/exabox/exatest/*.py ; do
        runone "${f}"
    done
}

runone() {
    ( rm -f "${basepath}/exabox/exatest/*.pyc" > /dev/null 2>&1 )
    i=${test_retries}
    rc=1
    while [ "${i}" -gt "0" ] && [ "${rc}" -ne "0" ]; do
        i=$((i-1))
        name=$( echo "$1" | awk -F/ '{print $NF}' )
        echo '' 
        echo '**********************************************************************' 
        echo "Testing file: '${name}'" 
        "${basepath}/bin/python" "$1" 2>&1 
        rc=$?
    done

    write_succ_diff "$rc" "$(echo "${name}" | sed 's/.py//g' | sed 's/tests_//g')"

    if [ $rc -ne 0 ]; then
        echo "### Exatest ${name} fails"

        if $exit_on_error; then
            exit "$rc"
        fi
    fi
}


# Carry over parameter to install function
oeda="-use_oss_oeda"
for var in "$@"
do
    if [ "$var" = "-use_ecs_oeda" ]; then
        oeda="-use_ecs_oeda"
    fi
done

echo ""
echo "######################################################"
echo "######################################################"
echo "####                                             #####"
echo "####             !!!  NOTICE   !!!               #####"
echo "####                                             #####"
echo "####         EXATEST.SH IS DEPRECATED            #####"
echo "####           PLEASE USE EXATEST.PY             #####"
echo "####                                             #####"
echo "######################################################"
echo "######################################################"
echo ""


case "$1" in 

    "-h")
        usage
        ;;

    "-cleanup")
        cleanup
        ;;

    "-install")
        install -debug $oeda
        ;;

    "-run")
        install $oeda
        ( cd "${basepath}" || exit ) 
        ( find "${basepath}/exabox/" | grep "tests_.*\.pyc" | xargs rm -f > /dev/null 2>&1 )

        if [ "$2" = "-all" ];
        then
            runall
        else
            if [ -z "$2" ];
            then
                echo "Error in '-run': No File" 
            else
                if [ -f "${basepath}/exabox/exatest/$2" ];
                then
                    runone "${basepath}/exabox/exatest/$2"
                else
                    # shellcheck disable=SC2086
                    FILE_PATH="$($realpath_cmd $2)"
                    runone "${FILE_PATH}"
                fi
            fi
        fi
        ( pgrep "${basepath}" | xargs kill  > /dev/null 2>&1 )
        ;;

    "-pylint")

        install -srg
        testfail="false"
        if [ "$2" = "-all" ] || [ "$2" = "-txn" ];
        then
            runPylint "$2"
        else
            if [ ! -f "$2" ]; then
                echo "### Exatest: The file does not exist" 
                my_exit 3 "pylint"
            fi
            for file in "$@"; do
                if [ "$file" != "-pylint" ];
                then
                    ( runPylintOne "$file" ) || testfail="true"
                fi
            done
        fi

        if [ "$testfail" = "true" ]; then
            echo "### Exatest Pylint check code and found issues" 
            my_exit 4 "pylint"
        else
            my_exit 0 "pylint"
        fi

        ;;

    "-srg")

        install -srg
        runPylint "$2"
        if [ "$2" = "-all" ] || [ "$3" = "-all" ];
        then
            runall
        else
            runone "${basepath}/exabox/exatest/tests_json_syntax.py"
        fi
        ;;

    *)
        echo "Error in cmd: Invalid Option '$1'." 
        usage
        my_exit 1

esac
exit 0

# end script
