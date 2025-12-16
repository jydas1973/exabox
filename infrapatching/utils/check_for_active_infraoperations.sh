#!/bin/sh
#
# $Header: ecs/exacloud/exabox/infrapatching/utils/check_for_active_infraoperations.sh /main/1 2022/10/20 07:48:08 abherrer Exp $
#
# check_for_active_infraoperations.sh
#
# Copyright (c) 2022, Oracle and/or its affiliates. 
#
#    NAME
#      check_for_active_infraoperations.sh - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    abherrer    10/06/22 - ENH 33115324 - Script to check if there is an infapatching operation running on the CPS
#
/opt/oci/exacc/exacloud/bin/mysql --status > /dev/null 2>&1
if [ $? -eq 0 ]; then
  query_result=`timeout 60 /opt/oci/exacc/exacloud/bin/mysql --execute requests "select uuid, cmdtype from requests where (UNIX_TIMESTAMP(STR_TO_DATE(starttime, '%a %b %d %H:%i:%S %Y')) >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 1 DAY))) and cmdtype like '%patch%' AND cmdtype in ('cluctrl.patch_prereq_check', 'cluctrl.postcheck', 'cluctrl.patch', 'cluctrl.rollback', 'cluctrl.rollback_prereq_check') AND status='Pending'" | grep -v uuid`
  if [ $? -eq 124 ]; then
    echo {"results":[], "error":"MySQL query timed out"}
    exit 1
  fi
else
  echo {"results":[], "error":"MySQL database is down"}
  exit 1
fi

if [ -z "$query_result" ]; then
  echo {"results":[]}
  exit 0
fi

query_array=($query_result)
uuid_arr=()
cmdtype_arr=()

for ((i=0; i<${#query_array[@]}; i++)); do
  if !((i % 2)); then
    uuid_arr+=(${query_array[$i]})
  else
    cmdtype_arr+=(${query_array[$i]})
  fi
done

if [ ${#uuid_arr[@]} -eq 0 ]; then
  echo {"results":[], "error":"uuid array is empty"}
  exit 1
fi

if [ ${#cmdtype_arr[@]} -eq 0 ]; then
  echo {"results":[], "error":"cmdtype array is empty"}
  exit 1
fi

if [ ${#uuid_arr[@]} -ne ${#cmdtype_arr[@]} ]; then
  echo {"results":[], "error":"uuid array and cmdtype array should be same lenght"}
  exit 1
fi

json_array=()

json_array+="["
for ((i=0; i<${#uuid_arr[@]}; i++)); do
  sed -n '/^\s*"Operation":/,/^\s*"backup_disk":/p' /opt/oci/exacc/exacloud/log/threads/0000-0000-0000-0000/"${uuid_arr[$i]}"_"${cmdtype_arr[$i]}"*.log > /dev/null 2>&1 
  if [ $? -eq 0  ]; then
    sed_result=`sed -n '/^\s*"Operation":/,/^\s*"backup_disk":/p' /opt/oci/exacc/exacloud/log/threads/0000-0000-0000-0000/"${uuid_arr[$i]}"_"${cmdtype_arr[$i]}"*.log` > /dev/null 2>&1
    if [ -z "$sed_result" ]; then
      echo {"results":[], "error":"Patch operation ongoing. Not able to extract information", "uuid":"${uuid_arr[$i]}", "cmdtype":"${cmdtype_arr[$i]}"}
      exit 1
    fi
  else
    echo {"results":[], "error":"Patch operation ongoing. Not able to extract information", "uuid":"${uuid_arr[$i]}", "cmdtype":"${cmdtype_arr[$i]}"}
    exit 1
  fi
  json_array+="{"$sed_result"}},"
done
json_array+="]"

json_array=`echo "$json_array" | sed 's/}},]/}}]/g'`
echo {\"results\":"$json_array"}
exit 0


