#!/bin/python
#
# $Header: ecs/exacloud/exabox/managment/src/LogManagementEndpoint.py /main/1 2023/03/16 12:32:45 chandapr Exp $
#
# LogManagementEndpoint.py
#
# Copyright (c) 2023, Oracle and/or its affiliates.
#
#    NAME
#      LogManagementEndpoint.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#    USAGE
#      remoteec log_management register name="hellochp" payload="/home/opc/hello.json" 
#    MODIFIED   (MM/DD/YY)
#    chandapr    03/13/23 - Creation
#
from exabox.managment.src.AsyncTrackEndpoint import AsyncTrackEndpoint
import os
import tempfile
import subprocess
import base64
import json
from socket import getfqdn

class LogManagementEndpoint(AsyncTrackEndpoint):

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
            self.mGetResponse()['error'] = '{0} is an invalid config path for Log Management. Please review ' \
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
                __registercmd = ["/usr/bin/python", "/opt/oci/exacc/logmanager/logManagerRegister.py", "-name={}".format(__service_name), "-file={}".format(__payload_file.name)]
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


