"""
 Copyright (c) 2014, 2020, Oracle and/or its affiliates. All rights reserved.

NAME:
    HelpHandler - Basic functionality

FUNCTION:
    Help endpoint of the managment

NOTE:
    None    

History:
    jesandov    26/03/2019 - File Creation
"""



import os
import sys
import uuid
import socket

from exabox.BaseServer.BaseEndpoint import BaseEndpoint

class HelpEndpoint(BaseEndpoint):

    def __init__(self, aHttpUrlArgs, aHttpBody, aHttpResponse, aSharedData):
        BaseEndpoint.__init__(self, aHttpUrlArgs, aHttpBody, aHttpResponse, aSharedData)

    def mGetEndpoints(self):
        _endpoints = self.mGetConfig().mGetClientEndpoints()
        _endpoints['hostname'] = socket.gethostname()
        return _endpoints
        

    def mGet(self):
        self.mGetResponse()['text'] = self.mGetEndpoints()

    def mPost(self):
        self.mGetResponse()['text'] = self.mGetEndpoints()

    def mPut(self):
        self.mGetResponse()['text'] = self.mGetEndpoints()

    def mPatch(self):
        self.mGetResponse()['text'] = self.mGetEndpoints()

    def mDelete(self):
        self.mGetResponse()['text'] = self.mGetEndpoints()

