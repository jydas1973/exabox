#!/usr/bin/env/python
#
# $Header: ecs/exacloud/exabox/managment/src/LogMonitorEndpoint.py /main/11 2023/05/19 05:57:15 chandapr Exp $
#
# LogMonitorEndpoint.py
#
# Copyright (c) 2023, Oracle and/or its affiliates.
#
#    NAME
#      LogMonitorEndpoint.py - Basic Functionality
#
#    DESCRIPTION
#    Function:
#      Remoteec endpoint for Log Monitoring
#    Usage/Commands:
#    (1). To register a new service -
#         cmd - remoteec log_monitoring register name=<service_name> payload=<json_file_location>  
#         Note - name and payload are mandatory params.
#         Example - remoteec log_monitoring register name="logmon_query_dummy" payload="/opt/oci/log/dummy.json"
#  
#    (2). To run log_monitoring for service(s) - 
#         cmd - remoteec log_monitoring execute name=<service_name>
#         Note - name is a optional parameter, if not given it will run all registered services.
#         Example -  remoteec log_monitoring execute name="logmon_query_dummy"
#    
#    (3). To execute  1-off query
#         (i). When data is passed as  json file.
#              cmd - remoteec log_monitoring execute_json_file name=<service_name> payload=<json_file_location>
#              Note - name is an optional param here.
#              Example - remoteec log_monitoring execute_json_file payload="/opt/oci/log/dummy.json"
#         
#         (ii). When data is in form of a json query.
#              cmd - remoteec log_monitoring execute_json_query name=<service_name> query=<valid_json_string>
#              Note - name is an optional param here.
#              Example - remoteec log_monitoring execute_json_query query='{ "logs":[ {  "filename":"/opt/oci/exacc/logmanager/log/log/imageManagement*.log.*",  "errorCodes" :["IMGMGMT_REVOKED_KEY", "IMGMGMT_SIGVERIFY_FAILED"] }] } '
#    (4). To update or add config params
#         Ex - Set "exec_duration" value in config to 3600
#         cmd - remoteec log_monitoring update_conf key="exec_duration" value="3600"
#    
#      NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    chandapr    05/02/23 - Bug#35230563: Add modify config params remoteec
#                           endpoints
#    chandapr    04/11/23 - Bug#35230549: Add off-query remoteec endpoints 
#    chandapr    03/01/23 - Bug#35085772: Add log_monitoring regular query remoteec
#    chandapr    02/13/23 - Bug#35117222: Update python exec and version info
#    chandapr    01/27/23 - Creation
#
from exabox.managment.src.AsyncTrackEndpoint import AsyncTrackEndpoint
import os
import tempfile
import subprocess
import base64
import json
from socket import getfqdn

class LogMonitorEndpoint(AsyncTrackEndpoint):

    def __init__(self, aHttpUrlArgs, aHttpBody, aHttpResponse, aSharedData):

        # Initialization of the base class
        AsyncTrackEndpoint.__init__(self, aHttpUrlArgs, aHttpBody, aHttpResponse, aSharedData)

        self.__install_dir = self.mGetConfig().mGetConfigValue('install_dir')

    def mPost(self):

        if self.__install_dir is None or not os.path.isdir(self.__install_dir):
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = 'install_dir key is missing or pointing to an invalid directory. ' \
                                           'Please review exacloud/exabox/managment/config/basic.conf'
            return

        # File Path
        __file_path = os.path.join(self.__install_dir, 'logmanager', 'metadata_repos')
        if not os.path.isdir(__file_path):
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = '{0} is an invalid config path for Log Monitoring. Please review ' \
                                        'exacloud/exabox/managment/config/basic.conf'.format(__file_path)
            return 

        #Check If name(service name) is passed (or) not. If not return with error.
        if not 'name' in self.mGetBody() or self.mGetBody()['name'] is None:
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = 'Please pass name of the service to register.'
            return

        #Check If payload(file) is passed (or) not. If not return with error.
        if not 'payload' in self.mGetBody() or self.mGetBody()['payload'] is None:
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = 'Please pass json registeration file to register.'
            return

        #Decode the payload
        try:       
	        __payload = base64.b64decode(self.mGetBody()['payload'])
        except Exception as e:	
            self.mGetResponse()['status'] = 500	
            self.mGetResponse()['error'] = 'Error decoding payload: {0}'.format(e)
            return
        
        #Name the registeration file
        __service_name = str(self.mGetBody()['name'])

        try:
            with tempfile.NamedTemporaryFile() as __payload_file:
                __payload_file.write(__payload)
                __payload_file.flush()
                __registercmd = ["/usr/bin/python", "/opt/oci/exacc/logmanager/logMonitorRegister.py", "-name={}".format(__service_name), "-file={}".format(__payload_file.name)]
                self.mGetLog().mInfo("locally created payload file name :: {0}".format(__payload_file.name))
        
                __rc, __stdout, __stderr = self.mBashExecution(__registercmd, subprocess.PIPE)
                if __rc != 0:
                    self.mGetResponse()['status'] = 500
                    self.mGetResponse()['error'] = 'Error registering the service {0} {1}'.format(__stdout, __stderr)
                    return
        
                self.mGetLog().mInfo("registering the service in the current host is successful")

        except Exception as e:
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = 'Error registering the service in primary host {0} '.format(e)
            return

        #If we reach here which means success.
        self.mGetResponse()['text'] = "Registeration of new service is successful."

    def mGet(self):

        if self.__install_dir is None or not os.path.isdir(self.__install_dir):
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = 'install_dir key is missing or pointing to an invalid directory. ' \
                                           'Please review exacloud/exabox/managment/config/basic.conf'
            return

        # File Path
        __file_path = os.path.join(self.__install_dir, 'logmanager', 'metadata_repos')
        if not os.path.isdir(__file_path):
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = '{0} is an invalid config path for Log Monitoring. Please review ' \
                                        'exacloud/exabox/managment/config/basic.conf'.format(__file_path)
            return
        
        __registercmd = ["/usr/bin/python3", "/opt/oci/exacc/logmanager/logMonitorProcess.py"]
        __service_name = None
        
        if self.mGetUrlArgs() is not None:
            _url_args = list(self.mGetUrlArgs().keys())
            if "name" in _url_args:
                __service_name = str(self.mGetUrlArgs()["name"])
        try:
            if __service_name is None:
                self.mGetLog().mInfo("executing log monitoring for every registered service")
            else:
                #Name the registeration file
                self.mGetLog().mInfo("executing log monitoring for service: {}".format(__service_name))
                __registercmd.append("--ServiceName={}".format(__service_name))
            
            __rc, __stdout, __stderr = self.mBashExecution(__registercmd, subprocess.PIPE)
            if __rc != 0:
                self.mGetResponse()['status'] = 500
                self.mGetResponse()['error'] = 'Error executing the registered service. {0} {1}'.format(__stdout, __stderr)
                return
            self.mGetLog().mInfo("executing the service(s) in the current host is successful")

        except Exception as e:
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = 'Error executing the service in primary host {0} '.format(e)
            return

        #If we reach here which means success.
        self.mGetResponse()['text'] = "Execution of service: {} is successful.".format(__service_name)

    def validate_json_data(self, str_json_data):
        # Validate the input json data file
        try:
            json.loads(str_json_data)
        except ValueError as err:
            return False
        return True

    def mDelete(self):
        if self.__install_dir is None or not os.path.isdir(self.__install_dir):
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = 'install_dir key is missing or pointing to an invalid directory. ' \
                                           'Please review exacloud/exabox/managment/config/basic.conf'
            return

        # Config Directory Path
        __file_path = os.path.join(self.__install_dir, 'logmanager', 'config')
        if not os.path.isdir(__file_path):
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = '{0} is an invalid config path for Log Monitoring. Please review ' \
                                        'exacloud/exabox/managment/config/basic.conf'.format(__file_path)
            return

        # Config File Path
        __config_file_path = os.path.join(self.__install_dir, 'logmanager', 'config', 'logmanager.conf')
        if not os.path.isfile(__config_file_path):
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = '{0} is an invalid config file path for Log Monitoring. Please review ' \
                                        'exacloud/exabox/managment/config/basic.conf'.format(__file_path)
            return
        
        #Check If key is passed (or) not. If not return with error.
        if not 'key' in self.mGetBody() or self.mGetBody()['key'] is None:
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = 'Please pass a key for the config value.'
            return

        #Check If value is passed (or) not. If not return with error.
        if not 'value' in self.mGetBody() or self.mGetBody()['value'] is None:
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = 'Please pass a value for the config key.'
            return
        
        __key = self.mGetBody()['key']
        __value = self.mGetBody()['value']
        
        __cmd = ["/usr/bin/python3", "/opt/oci/exacc/logmanager/logMonitorConfigParams.py"]
        __cmd.append("--Key={}".format(__key))
        __cmd.append("--Value={}".format(__value))

        try:
            self.mGetLog().mInfo("updating config of log monitoring")
            __rc, __stdout, __stderr = self.mBashExecution(__cmd, subprocess.PIPE)
            if __rc != 0:
                self.mGetResponse()['status'] = 500
                self.mGetResponse()['error'] = 'Error updating the config for log monitoring service. {0} {1}'.format(__stdout, __stderr)
                return
            self.mGetLog().mInfo("updating the config in the current host is successful")

        except Exception as e:
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = 'Error updating the config in primary host {0} '.format(e)
            return
    
        #If we reach here which means success.
        self.mGetResponse()['text'] = "New config paramater added : {} is successful.".format(__key)

    def mPatch(self): 
    
        #Check If payload(file) is passed (or) not. If not return with error.
        if not 'payload' in self.mGetBody() or self.mGetBody()['payload'] is None:
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = 'Please pass json file to execute.'
            return
        
        #Decode the payload
        try:
            __payload = base64.b64decode(self.mGetBody()['payload'])
        except Exception as e:	
            self.mGetResponse()['status'] = 500	
            self.mGetResponse()['error'] = 'Error decoding payload: {0}'.format(self.mGetBody()['payload'])
            return

        #Name the registeration file
        __service_name = None
        if 'name' in self.mGetBody() and self.mGetBody()['name'] is not None:
            __service_name = str(self.mGetBody()['name'])
            self.mGetLog().mInfo("Found service name for special query:  {0}".format(__service_name))
        __temp_json_path = os.path.join(self.__install_dir, 'logmanager')
        if not os.path.isdir(__temp_json_path):
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = '{0} is an invalid config path for LogMonitor. Please review ' \
                                        'exacloud/exabox/managment/config/basic.conf'.format(__temp_json_path)
            return
        __file_name = "temp.json"
        if __service_name is not None:
            __file_name = "{}.json".format(__service_name)
        __temp_json_file = os.path.join(__temp_json_path, __file_name)
         
        
        try:
            with tempfile.NamedTemporaryFile(dir=os.path.dirname("temp.json")) as __payload_file:
                __payload_file.write(__payload)
                __payload_file.flush()
                __copycmd = ["sudo", "cp", "-p", __payload_file.name, __temp_json_file]
                __rc, __stdout, __stderr = self.mBashExecution(__copycmd, subprocess.PIPE)
                if __rc != 0:
                    self.mGetResponse()['status'] = 500
                    self.mGetResponse()['error'] = 'Error copying temporary json file {0} {1}'.format(__stdout, __stderr)
                    return
 
                __registercmd = ["/usr/bin/python3", "/opt/oci/exacc/logmanager/logMonitorSpecialQuery.py", "--File={}".format(__temp_json_file)]
            
                self.mGetLog().mInfo("executing log monitoring special query!")
                if __service_name is not None:
                    __registercmd.append("--ServiceName={}".format(__service_name))
                    
                __rc, __stdout, __stderr = self.mBashExecution(__registercmd, subprocess.PIPE)
                if __rc != 0:
                    self.mGetResponse()['status'] = 500
                    self.mGetResponse()['error'] = 'Error executing the special query: {0} {1}'.format(__stdout, __stderr)
                    return

            self.mGetLog().mInfo("Execution of special query is successful")

        except Exception as e:
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = 'Error execution of special query failed: {0} '.format(e)
            return
	
        #If we reach here which means success.
        self.mGetResponse()['text'] = "Execution of special query json_data is successful."

    def mPut(self):
        
        __service_name = None
        __payload_json_data = None
        
        if not 'query' in self.mGetBody() or self.mGetBody()['query'] is None:
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = 'JSON data as query is required, please pass json data'
            return

        __payload_json_data = str(self.mGetBody()["query"])
        if self.validate_json_data(__payload_json_data) is False:
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = 'Found invalid JSON data, please pass valid json'
            return
        
        if "name" in self.mGetBody():
            __service_name = str(self.mGetBody()["name"])
            self.mGetLog().mInfo("Found service name for special query:  {0}".format(__service_name))
        
        try:
            __registercmd = ["/usr/bin/python3", "/opt/oci/exacc/logmanager/logMonitorSpecialQuery.py", "--JSONData={}".format(__payload_json_data)]
            
            self.mGetLog().mInfo("executing log monitoring special query!")
            if __service_name is not None:
                __registercmd.append("--ServiceName={}".format(__service_name))
                    
            self.mGetLog().mInfo("execution of special query is successful")
            __rc, __stdout, __stderr = self.mBashExecution(__registercmd, subprocess.PIPE)
            if __rc != 0:
                self.mGetResponse()['status'] = 500
                self.mGetResponse()['error'] = 'Error executing the special query: {0} {1}'.format(__stdout, __stderr)
                return

            self.mGetLog().mInfo("Execution of special query is successful")


        except Exception as e:
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = 'Error execution of special query failed: {0} '.format(e)
            return

        #If we reach here which means success.
        self.mGetResponse()['text'] = "Execution of special query is successful."

