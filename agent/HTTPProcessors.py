"""
 Copyright (c) 2014, 2025, Oracle and/or its affiliates. 

NAME:
    PostProtocol.py

FUNCTION:
    Agent Post Protocol functionalities

NOTE:
    None

History:
    pbellary   03/17/25   - Bug 37713924 - EXASCALE: ADD CELL OPERATION DELETING CLUSTERS DIRECTORY 
    vgerard    2019/09/05 - Relieve pressure on DB on converting XML to file path
    vgerard    2019/04/09 - Create file
    aypaul     04/24/2021 - Bug#32677651 Exacloud to update policies on provisioned clusters.
    
"""

import six
import uuid
import base64
import zlib
import os
from exabox.tools.AttributeWrapper import forceStrArgRet

class MethodWrapper(object):
    def __init__(self, aMethod, preprocess=[], postprocess=[]):
        self.__wrappedMethod  = aMethod
        self.__preProcessors  = preprocess
        self.__postProcessors = postprocess

    def getWrappedMethod(self):
        return self.__wrappedMethod

    def applyPreProcessors(self,aHttpReq):
        for _preprocessClass in self.__preProcessors:
            _preprocessClass.PreprocessRequest(aHttpReq)

    def applyPostProcessors(self,aResponseDict):
        for _postprocessClass in self.__postProcessors:
            _postprocessClass.PostProcessResponse(aResponseDict)

# HTTP PRE PROCESSORS, Work on HttpRequest Object

class HTTPPreProcessor(object):
    def PreprocessRequest(self,aRequest):
        raise NotImplementedError

#Usecase is to forward Authentication to subrequest
class ConvertHttpHeaderToParam(HTTPPreProcessor):
    def __init__(self, aHeader, aParam):
        self.__header = aHeader
        self.__param = aParam
    def PreprocessRequest(self, aHttpReq):
        _req_header = aHttpReq.getHeaders().get(self.__header)
        if _req_header:
            aHttpReq.setParam(self.__param,_req_header)

#Usecase is to convert /CluCtrl/vmgi_install
#to cmd=vmgi_install param for postpreprocess
class ConvertPathToParam(HTTPPreProcessor):
    def __init__(self,aParam):
        self.__param = aParam
    def PreprocessRequest(self,aHttpReq):
        _fullpath = aHttpReq.getFullPath() #/CluCtrl/<cmd>
        _split = _fullpath[1:].split('/')
        if len(_split) == 2:
            aHttpReq.setParam(self.__param,_split[1])
            aHttpReq.setParam('frompath_'+self.__param, True)

#usecase is for configfile param
class DecodeBase64(HTTPPreProcessor):
    def __init__(self,aParam,deflate=True):
        self.__param = aParam
        self.__deflate = deflate
    def PreprocessRequest(self,aHttpReq):
        _base64coded = aHttpReq.getParam(self.__param)
        if _base64coded:
            _data = base64.b64decode(_base64coded)
            if self.__deflate:
                _data = zlib.decompress(_data)
            # Use a new random UUID unrelated to request,
            # exacloud will log it anyway
            _path='./clusters/PodRepo/'
            if not os.path.exists(_path):
                os.makedirs(_path)
            _filename = os.path.abspath('./clusters/PodRepo/{}.xml'.format(uuid.uuid4()))
            with open(_filename,'w') as f:
                f.write(_data.decode('utf8'))
            aHttpReq.setParam(self.__param,_filename)

"""Use case to decode the base64 encoded policy file sent along with the JSON payload from ECRA.
This function decodes the json payload for se_linux if present along with policy file will insert new keys
in the se_linux dictionary in the format {component_type}_policy which can be used later on by exacloud.
"""
class DecodeBase64Policy(HTTPPreProcessor):

    def PreprocessRequest(self,aHttpReq):

        jsonConfigurationParameter = aHttpReq.getParam("jsonconf")
        if jsonConfigurationParameter is not None and jsonConfigurationParameter.get("se_linux", None) is not None:
            if type(jsonConfigurationParameter["se_linux"]) == str:
                return
            listOfInfrastructureComponents = jsonConfigurationParameter["se_linux"].get("infraComponent", [])
            for infrastructureComponent in listOfInfrastructureComponents:
                currentComponentType = infrastructureComponent.get("component", None)
                if currentComponentType is None:
                    continue
                currentInfraTypeAndPolicy = "{0}_policy".format(currentComponentType)
                base64CodedPolicy = infrastructureComponent.get("policy", None)
                if base64CodedPolicy:
                    if type(base64CodedPolicy) is str:
                        _data = base64.b64decode(base64CodedPolicy)
                        _path='./clusters/PolicyRepo/'
                        if not os.path.exists(_path):
                            os.makedirs(_path, exist_ok=True)
                        _filename = os.path.abspath('./clusters/PolicyRepo/{}.pp'.format(uuid.uuid4()))
                        with open(_filename,'wb') as f:
                            f.write(_data)
                        jsonConfigurationParameter["se_linux"][currentInfraTypeAndPolicy] = [_filename]
                    elif type(base64CodedPolicy) is list:
                        policyFileList = list()
                        for currentEncodedPolicy in base64CodedPolicy:
                            _data = base64.b64decode(currentEncodedPolicy)
                            _path='./clusters/PolicyRepo/'
                            if not os.path.exists(_path):
                                os.makedirs(_path, exist_ok=True)
                            _filename = os.path.abspath('./clusters/PolicyRepo/{}.pp'.format(uuid.uuid4()))
                            with open(_filename,'wb') as f:
                                f.write(_data)
                            policyFileList.append(_filename)
                        jsonConfigurationParameter["se_linux"][currentInfraTypeAndPolicy] = policyFileList


#usecase is getting appropriate path for UI index file
class GetPathForIndex(HTTPPreProcessor):
    def __init__(self, aParam):
        self.__param = aParam
    def PreprocessRequest(self, aHttpReq):
        if aHttpReq.getFullPath()=="" or aHttpReq.getFullPath()=="/":
            aHttpReq.setParam(self.__param, "/index.html")
        else:
            aHttpReq.setParam(self.__param, aHttpReq.getFullPath())

# HTTP POST PROCESSORS, Work on Response dictionary

class HTTPPostProcessor(object):
    def PostProcessResponse(self,aResponseDict):
        raise NotImplementedError

class EncodeBase64(HTTPPostProcessor):
    def __init__(self,aParam=None,deflate=True):
        self.__param = aParam
        self.__deflate = deflate
    def PostProcessResponse(self,aResponseDict):
        #Read File and encode to base64
        if self.__param and self.__param in aResponseDict:
            _data = aResponseDict[self.__param]
            if _data:
                if os.path.isfile(_data):
                    with open(_data,'rb') as _f:
                        _data = _f.read()
                if self.__deflate:
                    _data = zlib.compress(six.ensure_binary(_data))
                    aResponseDict[self.__param+'-encoding'] = 'base64+deflate'
                else:
                    aResponseDict[self.__param+'-encoding'] = 'base64'
                aResponseDict[self.__param] = forceStrArgRet(base64.b64encode)(_data)

#EOF
