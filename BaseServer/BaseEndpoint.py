"""
 Copyright (c) 2014, 2021, Oracle and/or its affiliates. 

NAME:
    BaseEndpoint - Basic functionality

FUNCTION:
    Base endpoint of the BaseServer

NOTE:
    None    

History:
    jesandov    26/03/2019 - File Creation
"""



import os
import sys
import math
import uuid

class BaseEndpoint(object):

    def __init__(self, aHttpUrlArgs, aHttpBody, aHttpResponse, aSharedData):

        #Mandatory params
        self.__httpUrlArgs  = aHttpUrlArgs
        self.__httpBody     = aHttpBody
        self.__httpResponse = aHttpResponse
        self.__shared       = aSharedData

        self.__httpResponse['status'] = 200

    def mGetUrlArgs(self):
        return self.__httpUrlArgs

    def mGetBody(self):
        return self.__httpBody

    def mGetResponse(self):
        return self.__httpResponse

    def mGetShared(self):
        return self.__shared

    def mGetConfig(self):
        return self.__shared['config']

    def mGetLog(self):
        return self.__shared['log']

    def mGet(self):
        self.__httpResponse['status'] = 501
        self.__httpResponse['text']   = "Error: Not implemented"
        self.__httpResponse['error']  = "Error: Not implemented"

    def mPost(self):
        self.__httpResponse['status'] = 501
        self.__httpResponse['text']   = "Error: Not implemented"
        self.__httpResponse['error']  = "Error: Not implemented"

    def mPut(self):
        self.__httpResponse['status'] = 501
        self.__httpResponse['text']   = "Error: Not implemented"
        self.__httpResponse['error']  = "Error: Not implemented"

    def mDelete(self):
        self.__httpResponse['status'] = 501
        self.__httpResponse['text']   = "Error: Not implemented"
        self.__httpResponse['error']  = "Error: Not implemented"

    def mPatch(self):
        self.__httpResponse['status'] = 501
        self.__httpResponse['text']   = "Error: Not implemented"
        self.__httpResponse['error']  = "Error: Not implemented"


