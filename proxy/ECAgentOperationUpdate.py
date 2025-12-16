#
# $Header: ecs/exacloud/exabox/proxy/ECAgentOperationUpdate.py /main/6 2021/11/30 22:23:16 aypaul Exp $
#
# ECAgentOperationUpdate.py
#
# Copyright (c) 2020, 2021, Oracle and/or its affiliates.
#
#    NAME
#      ECAgentOperationUpdate.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    dekuckre    10/07/20 - 31465951: Enhancements to proxy feature
#    aypaul      06/17/20 - Creation
#
import json
from exabox.core.DBStore import ebInitDBLayer, ebShutdownDBLayer, ebGetDefaultDB
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogDB
from exabox.agent.Agent import ebAgentDaemon
from exabox.core.Context import get_gcontext

def fetch_update_ecregistrationinfo(aOptions):
    _db = ebGetDefaultDB()
    if aOptions.eccontrol == 'list':
        _data = _db.mSelectAllFromExacloudInstance()
        if len(_data) == 0:
            ebLogWarn("There are no active exacloud instances registered with this exaproxy.")
        else:
            _jsonData = {}
            for _row in _data:
                _jsonRow = {}
                _key = _row[0]
                if not aOptions.short:
                    _jsonRow['ecinstanceid'] = _row[0]
                    _jsonRow['hostname'] = _row[1]
                    _jsonRow['port'] = _row[2]
                    _jsonRow['version'] = _row[3]
                    _jsonRow['request_type'] = _row[6]
                _jsonRow['status'] = _row[4]
                _jsonRow['authkey'] = _row[5]
                _jsonRow['oeda_version'] = _row[7]

                _jsonData[_key] = _jsonRow
            
            ebLogInfo("*** List of registered exacloud instances with exaproxy: *****\n" + json.dumps(_jsonData, indent = 4))

    elif aOptions.eccontrol == 'update':

        _config_opts = get_gcontext().mGetConfigOptions()
        if "agent_port" in list(_config_opts.keys()):
            _proxy_port = int(_config_opts["agent_port"])

        if "agent_host" in list(_config_opts.keys()):
            _proxy_host = str(_config_opts["agent_host"])

        if not aOptions.eccontrolkeyval:
            ebLogError("Please provide exacloud instance information to update using --eccontrolkeyval. Comma separated info of ecinstanceID and key-values. Example: inst1=key1-value1,inst2=key2-value2,inst3=key3-value3 .")
        else:
            _listOfECInstances = str(aOptions.eccontrolkeyval).split(",")
            for _ecinst_info in _listOfECInstances:
                if len(_ecinst_info.split("=")) != 2:
                    ebLogError("Invalid ecinstance information: {}".format(_ecinst_info))
                    continue
                
                _ecinstance_id = _ecinst_info.split("=")[0]
                _ecinst_key_value = _ecinst_info.split("=")[1]
                _data={}
                _data['host'] = _ecinstance_id.split(":")[0]
                _data['port'] = _ecinstance_id.split(":")[1] 
                _data['op'] = 'update'
                _data['key'] = _ecinst_key_value.split("-")[0]
                _data['value'] = _ecinst_key_value.split("-")[1]
                # Proxy updates exacloud instance info
                _proxy_request = 'http://' + _proxy_host + ':' + str(_proxy_port)+"/ecinstmaintenance"
                if hasattr(aOptions, 'unittest') and aOptions.unittest is True:
                    ebAgentDaemon.mPerformRequest(_proxy_request, _proxy_host, str(_proxy_port), json.dumps(_data).encode(), isMock=True, mockReturn="EC agent operation succeded.")
                else:
                    ebAgentDaemon.mPerformRequest(_proxy_request, _proxy_host, str(_proxy_port), json.dumps(_data).encode())

    else:
        ebLogError("Invalid ECControl operation type: " + aOptions.eccontrol)
