"""
 Copyright (c) 2014, 2022, Oracle and/or its affiliates.

NAME:
    Oss Endpoint - Basic functionality

FUNCTION:
    Oss endpoint of the managment

NOTE:
    None    

History:
    jesandov    26/03/2019 - File Creation
"""

from __future__ import print_function

import os
import oci
import sys
import json
import uuid
import socket
import base64

from datetime import datetime, timedelta

from exabox.BaseServer.BaseEndpoint import BaseEndpoint
from exabox.managment.src.AsyncTrackEndpoint import AsyncTrackEndpoint
from exabox.utils.oci_region import load_oci_region_config, get_value
from exabox.config.Config import get_value_from_exabox_config


class OssEndpoint(AsyncTrackEndpoint):

    def __init__(self, aHttpUrlArgs, aHttpBody, aHttpResponse, aSharedData):
        AsyncTrackEndpoint.__init__(self, aHttpUrlArgs, aHttpBody, aHttpResponse, aSharedData)

        self.mSetAsyncLogTag("OSS")
        self.__bucket = "RemoteManagementObj"
        self.__ossClient = None
        self.__ossConfig = None
        self.__ociRegionConfig = {}


    def mGetOssClient(self):
        return self.__ossClient

    def mSetOssClient(self, aClient):
        self.__ossClient = aClient

    def mGetOssConfig(self):
        return self.__ossConfig

    def mSetOssConfig(self, aConfig):
        self.__ossConfig = aConfig

    def mGetOssRegionConfig(self):
        return self.__ociRegionConfig

    def mSetOssRegionConfig(self, aRegionConfig):
        self.__ociRegionConfig = aRegionConfig

    def mOssCreateClient(self, aConfigArgs):

        _exapath = self.mGetConfig().mGetExacloudPath()
        _alias = aConfigArgs["cfg_alias"]
        _cfgPath = "{0}/exabox/managment/config/oss/{1}/oci.conf".format(_exapath, _alias)
        

        if not os.path.exists(_cfgPath):
            self.mGetResponse()['text']  = "Configuration file not exist {0}\nplease run register_config".format(_alias)
            self.mGetResponse()['error']  = "Configuration file not exist {0}\nplease run register_config".format(_alias)
            self.mGetResponse()['status'] = 500
            return False

        if self.mGetOssClient() is None:

            self.mGetLog().mInfo("Start Creation of object store client'")

            _ociRegionConfig = load_oci_region_config()
            _oci_region = get_value(_ociRegionConfig, "regionIdentifier")
            self.mSetOssRegionConfig(_ociRegionConfig)

            # Get the config of the object store
            _config = oci.config.from_file(file_location=_cfgPath)
            if len(_ociRegionConfig) > 0:
                _config["region"] = _oci_region

            oci.config.validate_config(_config)
            self.mSetOssConfig(_config)
            self.mGetLog().mInfo("Read Config: '{0}'".format(_config))

            # Create the client
            _client = oci.object_storage.ObjectStorageClient(_config)
            self.mSetOssClient(_client)
            self.mGetLog().mInfo("New client created: {0}".format(_client))

        return True

    def mOssRegisterConfig(self, aConfigArgs):

        _exapath = self.mGetConfig().mGetExacloudPath()
        _alias = aConfigArgs["cfg_alias"]
        _aliasPath = "{0}/exabox/managment/config/oss/{1}".format(_exapath, _alias)

        if os.path.exists(_aliasPath):
            self.mGetResponse()["text"] = "Oss config already created, please use other alias"
            return False

        self.mBashExecution(["mkdir", "-p", "{0}/exabox/managment/config/oss".format(_exapath)])
        self.mBashExecution(["mkdir", "-p", _aliasPath])

        with open("{0}/key_file".format(_aliasPath), "w") as _keyFile:
            _keyFile.write(base64.b64decode(aConfigArgs["oss_key_file"]).decode('utf8'))

        with open("{0}/oci.conf".format(_aliasPath), "w") as _cfgFile:
            _cfgFile.write("[DEFAULT]\n")
            _cfgFile.write("user={0}\n".format(aConfigArgs["oss_user"]))
            _cfgFile.write("fingerprint={0}\n".format(aConfigArgs["oss_fingerprint"]))
            _cfgFile.write("key_file={0}/key_file\n".format(_aliasPath))
            _cfgFile.write("tenancy={0}\n".format(aConfigArgs["oss_tenancy"]))
            _cfgFile.write("region={0}\n".format(aConfigArgs["oss_region"]))

        return True


    def mOssCreateBucket(self, aCustomArgs):

        self.mGetLog().mInfo("Start Create Bucket: '{0}'".format(self.__bucket))

        _client = self.mGetOssClient()
        _namespace = _client.get_namespace().data
        _compartmentId = self.mGetOssConfig()["tenancy"]

        # Create the bucket details
        _details = oci.object_storage.models.CreateBucketDetails()
        _details.compartment_id = _compartmentId
        _details.name = self.__bucket
        self.mGetLog().mInfo("Create bucket details: {0}".format(_details))

        # Create the bucket
        try:
            _client.create_bucket(_namespace, _details)

        except oci.exceptions.ServiceError as serviceError:
            self.mGetLog().mWarn(serviceError)
            if str(serviceError.status) != "409":
                # Raise only in case there i snot a duplicate bucket error
                raise

        self.mGetLog().mInfo("Create bucket complete")

    def mOssUploadObject(self, aLogFilename, aProcessId, aCustomArgs):

        # Validate the object is on the reacheble path
        _ossObjPath = self.mGetPath(aCustomArgs["path"])

        if _ossObjPath:
            _ossObjPath = _ossObjPath.rstrip("/")
            _ossObjName = os.path.basename(_ossObjPath)
            _ossObjNewName = "{0}-{1}".format(aProcessId, _ossObjName)

            # Create client and bucket
            _client = self.mGetOssClient()
            _namespace = _client.get_namespace().data
            _compartmentId = self.mGetOssConfig()["tenancy"]

        with open(aLogFilename, "w+") as _log:

            if not _ossObjPath:
                self.mAsyncLog(_log, aProcessId, "Invalid Path: {0}'".format(aCustomArgs["path"]), aDebug=False)
                return 4

            self.mAsyncLog(_log, aProcessId, "Start Upload Object: {0}'".format(_ossObjPath), aDebug=False)

            # If is dir the path, will create a new zip file
            _isCreated = False
            if os.path.isdir(_ossObjPath):
                _isCreated = True
            
                self.mAsyncLog(_log, aProcessId, "Create Zip file since is folder'", aDebug=False)
                _cmd = ["zip"]
                _cmd.append("-r")
                _cmd.append("{0}.zip".format(_ossObjName))
                _cmd.append(_ossObjPath)
                self.mBashExecution(_cmd)

                _ossObjPath = "{0}.zip".format(_ossObjPath)
                _ossObjName = "{0}.zip".format(_ossObjName)
                _ossObjNewName = "{0}.zip".format(_ossObjNewName)

            # Get the filecontent of the file to upload
            self.mAsyncLog(_log, aProcessId, "Read file content", aDebug=False)
            _filecontent = None
            with open(_ossObjPath, "r") as _ossRawFile:
                _filecontent = _ossRawFile.read()

            self.mAsyncLog(_log, aProcessId, "Upload Object in progress ...", aDebug=False)
            _ossObj = _client.put_object(_namespace, self.__bucket, _ossObjNewName, _filecontent)

            if _isCreated:
                _cmd = "rm -rf {0}".format(_ossObjNewName)

            self.mAsyncLog(_log, aProcessId, "Upload object done: {0}".format(_ossObjNewName), aDebug=False)
            self.mAsyncLog(_log, aProcessId, "Response: {0}'".format(vars(_ossObj)), aDebug=True)

            return 0


    def mOssCreateParUrl(self, aLogFilename, aProcessId, aCustomArgs):

        # Create client and bucket
        _client = self.mGetOssClient()
        _namespace = _client.get_namespace().data
        _ossName = aCustomArgs["obj_name"]
        _expirationDays = int(aCustomArgs["expiration_days"])

        with open(aLogFilename, "w+") as _log:

            _details = oci.object_storage.models.CreatePreauthenticatedRequestDetails()
            _details.name = _ossName
            _details.object_name = _ossName
            _details.access_type = "ObjectRead"
            _details.time_expires = datetime.now() + timedelta(days=_expirationDays)

            self.mAsyncLog(_log, aProcessId, "Details of Par: {0}".format(_details), aDebug=True)
            _response = _client.create_preauthenticated_request(_namespace, self.__bucket, _details)

            if str(_response.status) == "200":

                _singlePar = json.loads(str(_response.data))
                _singleUrl = "https://objectstorage.{0}.{1}{2}"
                _singleUrl = _singleUrl.format(\
                    get_value(self.mGetOssRegionConfig(), "regionIdentifier"), 
                    get_value(self.mGetOssRegionConfig(), "realmDomainComponent"), 
                    _singlePar["access_uri"])
                _singlePar["acess_uri_full"] = _singleUrl

                self.mAsyncLog(_log, aProcessId, "Par info created", aDebug=True)
                self.mAsyncLog(_log, aProcessId, json.dumps(_singlePar, indent=4), aDebug=False)

            else:
                self.mAsyncLog(_log, aProcessId, "Error while par obj: {0}".format(vars(_response)), aDebug=False)
                return 1

        return 0

    def mOssListObjects(self, aCustomArgs):

        # Create client and bucket
        _client = self.mGetOssClient()
        _namespace = _client.get_namespace().data
        _objects = []

        _prefix = ""
        if aCustomArgs and "uuid" in aCustomArgs.keys():
            _prefix = aCustomArgs["uuid"]

        _since = None
        if aCustomArgs and "since_in_days" in aCustomArgs.keys():
            try:
                _since = int(aCustomArgs["since_in_days"])
            except ValueError:
                pass

        _fields = "md5,name,size,timeCreated"
        _response = _client.list_objects(_namespace, self.__bucket, fields=_fields)

        if str(_response.status) == "200":
            _objects = json.loads(str(_response.data.objects))
            self.mGetLog().mInfo("Fetch object list: {0}".format(_objects))
        else:
            self.mGetLog().mError("Error while fetch obj: Respone({0})".format(vars(_response)))

        # Apply filter of prefix
        _newObjects = []
        for _ossObj in _objects:
            _add = True

            if _prefix:
                if not _ossObj['name'].startswith(_prefix):
                    _add = False

            if _since:

                _add = False

                if _ossObj['time_created']:
                    _objtime = datetime.strptime(_ossObj['time_created'], "%Y-%m-%dT%H:%M:%S.%f+00:00")
                    _maxtime = datetime.now() - timedelta(days=_since)

                    if _objtime > _maxtime:
                        _add = True

            if _add:
                _newObjects.append(_ossObj)

        return _newObjects


    def mGet(self):
        _args = self.mGetUrlArgs()
        if self.mOssCreateClient(_args):
            _errorMsg = None

            try:
                _pars = self.mOssListObjects(_args)
                self.mGetResponse()["text"] = _pars

            except oci.exceptions.ServiceError as _err:
                _errorMsg = "ServiceErrorException: {0}".format(_err)

            except Exception as _err:
                raise

            if _errorMsg:
                self.mGetLog().mError(_errorMsg)
                self.mGetResponse()['text'] = _errorMsg
                self.mGetResponse()['error'] = _errorMsg
                self.mGetResponse()['status'] = 500

    def mPost(self):
        _args = self.mGetBody()
        _name = "OSS_Create PAR [{0}]".format(_args)

        if self.mOssCreateClient(_args):
            _response = self.mCreatePythonProcess(self.mOssCreateParUrl, _args, aName=_name)
            self.mGetResponse()["text"] = _response

    def mPut(self):
        _args = self.mGetBody()
        _name = "OSS_Upload [{0}]".format(_args)

        if self.mOssCreateClient(_args):
            _response = self.mCreatePythonProcess(self.mOssUploadObject, _args, aName=_name)
            self.mGetResponse()["text"] = _response

    def mPatch(self):
        _args = self.mGetBody()

        if self.mOssRegisterConfig(_args):
            if self.mOssCreateClient(_args):
                self.mOssCreateBucket(_args)
                self.mGetResponse()["text"] = "Registration of {0} and bucket is done".format(_args["cfg_alias"])

# end file
