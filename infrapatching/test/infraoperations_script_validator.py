#!/bin/python
#
# $Header: ecs/exacloud/exabox/infrapatching/test/infraoperations_script_validator.py /main/2 2024/08/16 10:00:25 araghave Exp $
#
# infraoperations_script_validator.py
#
# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
#
#    NAME
#      infraoperations_script_validator.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    araghave    07/15/24 - Enh 36830077 - CLEANUP KSPLICE CODE FROM
#                           INFRAPATCHING FILES
#    abherrer    10/06/22 - ENH 33115324 - Integration test for shell script that checks current infra operations in CPS
#
import os
import subprocess
import time

NO_RESULTS_FROM_QUERY_MSG = "{results:[]}"
FILE_NOT_FOUND_MSG = "{results:[], error:Patch operation ongoing. Not able to extract information, uuid:testid, cmdtype:cluctrl.patch_prereq_check}"
RESULT_MSG = "{\"results\":[{\"Operation\":\"patch_prereq_check\",\"PayloadType\":\"exadata_release\",\"OperationStyle\":\"auto\",\"TargetType\":[\"dom0\"],\"TargetVersion\":\"22.1.2.0.0.220816\",\"BackupMode\":\"yes\",\"EnablePlugins\":\"no\",\"PluginTypes\":\"none\",\"Fedramp\":\"DISABLED\",\"Retry\":\"no\",\"RequestId\":\"b672ecab-2688-4b75-95b4-ece7398992b5\",\"AdditionalOptions\":[{\"AllowActiveNfsMounts\":\"yes\",\"ClusterLess\":\"no\",\"EnvType\":\"ecs\",\"ForceRemoveCustomRpms\":\"no\",\"IgnoreAlerts\":\"no\",\"IgnoreDateValidation\":\"yes\",\"IncludeNodeList\":\"none\",\"LaunchNode\":\"none\",\"OneoffCustomPluginFile\":\"none\",\"OneoffScriptArgs\":\"none\",\"PluginLocation\":\"none\",\"RackSwitchesOnly\":\"no\",\"SingleUpgradeNodeName\":\"none\",\"SkipDomuCheck\":\"no\",\"exasplice\":\"no\",\"isSingleNodeUpgrade\":\"no\",\"serviceType\":\"EXACC\",\"exaunitId\":21}],\"ComputeNodeList\":{},\"StorageNodeList\":{},\"Dom0domUDetails\":{},\"DBPatchFile\":\"/u01/downloads/exadata/PatchPayloads/22.1.2.0.0.220816/DBPatchFile/dbserver.patch.zip\",\"Dom0YumRepository\":\"/u01/downloads/exadata/PatchPayloads/22.1.2.0.0.220816/Dom0YumRepository/exadata_ovs_22.1.2.0.0.220816_Linux-x86-64.zip,/u01/downloads/exadata/PatchPayloads/22.1.2.0.0.220816/Dom0YumRepository/exadata_ol7_22.1.2.0.0.220816_Linux-x86-64.zip\",\"XmlOeda\":\"log/patch/bc1a81ba-4e3c-11ed-a829-52540094717e/exadata_patching_oedaxml_iad156921exd-atpmg-scaqan03XXX-clu01.xml\",\"TargetEnv\":\"production\",\"RackName\":\"iad156921exd-atpmg-scaqan03XXX-clu01\",\"ClusterID\":\"1\",\"rack\":{\"backup_disk\":\"false\"}}]}"
RESULT_LIST = RESULT_MSG.split()

# Check if mysql is up
command_exit_val = os.system("/opt/oci/exacc/exacloud/bin/mysql --status > /dev/null 2>&1")
assert command_exit_val == 0, "Mysql is down"

# Check if there are infra operations going on
result = subprocess.run(["/opt/oci/exacc/exacloud/bin/mysql", "--execute", "requests", "SELECT uuid FROM requests WHERE status='Pending' AND cmdtype IN ('cluctrl.patch_prereq_check', 'cluctrl.postcheck', 'cluctrl.patch', 'cluctrl.rollback', 'cluctrl.rollback_prereq_check')"], stdout=subprocess.PIPE)
cmd_output = result.stdout.decode('utf-8')
assert len(cmd_output) == 0, "Theres a patching operation executing. Cant test."

# Check empty results
result = subprocess.run(["./check_for_active_infraoperations.sh"], stdout=subprocess.PIPE)
cmd_output = result.stdout.decode('utf-8')
assert NO_RESULTS_FROM_QUERY_MSG in cmd_output, "Operation failed on empty execution"

try:
    # Insert test record into requests database and try scrip
    os.system("/opt/oci/exacc/exacloud/bin/mysql --execute requests \"INSERT INTO requests (uuid, cmdtype, status, starttime) VALUES ('testid', 'cluctrl.patch_prereq_check', 'Pending', DATE_FORMAT(NOW(), '%a %b %d %H:%i:%S %Y'))\"")
    result = subprocess.run(["./check_for_active_infraoperations.sh"], stdout=subprocess.PIPE)
    cmd_output = result.stdout.decode('utf-8')
    assert FILE_NOT_FOUND_MSG in cmd_output, "Operation failed on file not found execution: " + cmd_output 

    # Copy test file an try script again
    os.system("cp log_file_for_validator/testid_cluctrl.patch_prereq_check.log /opt/oci/exacc/exacloud/log/threads/0000-0000-0000-0000/")
    result = subprocess.run(["./check_for_active_infraoperations.sh"], stdout=subprocess.PIPE)
    cmd_output = result.stdout.decode('utf-8')
    cmd_output = "".join(cmd_output.split())
    cmd_list = cmd_output.split()
    assert RESULT_LIST == cmd_list, "Operation failed on normal execution: " + str(cmd_list)

except AssertionError as e:
    print(e)
finally:
    os.system("/opt/oci/exacc/exacloud/bin/mysql --execute requests \"DELETE FROM requests WHERE uuid='testid'\"")    
    os.system("rm /opt/oci/exacc/exacloud/log/threads/0000-0000-0000-0000/testid_cluctrl.patch_prereq_check.log")
