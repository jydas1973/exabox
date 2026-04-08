"""
 Copyright (c) 2014, 2026, Oracle and/or its affiliates.

NAME:
    DiagEndpoint - Basic functionality

FUNCTION:
    Diag endpoint of the managment

NOTE:
    None    

History:
    shapatna    02/09/2026 - Bug: 38900266 - Fix for issues pointed by Codev
                             in exabox/management directory
    jesandov    06/04/2020 - Change function name affected by AsyncTrackEndpoint
    jesandov    26/03/2019 - File Creation
"""



import re
import os
import sys
import copy
import math
import uuid
import shutil
import base64

from exabox.managment.src.AsyncTrackEndpoint import AsyncTrackEndpoint

class DiagEndpoint(AsyncTrackEndpoint):

    def __init__(self, aHttpUrlArgs, aHttpBody, aHttpResponse, aSharedData):

        #Initializate the class
        AsyncTrackEndpoint.__init__(self, aHttpUrlArgs, aHttpBody, aHttpResponse, aSharedData)

    def mListDiags(self):

        _diags = []

        _diagPath = os.path.abspath("{0}/../../oeda/requests/".format(self.mGetConfig().mGetPath())) + "/"
        for (_dirpath, _, _filenames) in os.walk(_diagPath):

            for _filename in _filenames:
                if re.search("Incident_.*zip", _filename) is not None:
                    _diagLoc = "{0}/{1}".format(_dirpath.replace(_diagPath, ""), _filename)
                    _diagLoc = _diagLoc.strip("/")
                    _diags.append(_diagLoc)

        return _diags

    def mDownloadDiag(self, aZip):

        _diagPath = os.path.abspath("{0}/../../oeda/requests/".format(self.mGetConfig().mGetPath()))
        _zip = "{0}/{1}".format(_diagPath, aZip)

        if not os.path.exists(_zip):
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['text']   = "File not found in File System {0}".format(_zip)
            self.mGetResponse()['error']  = "File not found in File System {0}".format(_zip)
        else:

            _fileC = ""
            _file_bytes = ""
            with open(_zip, "rb") as _f:
                _file_bytes = _f.read()
                _fileC = base64.b64encode(_file_bytes).decode('utf-8')

            self.mGetResponse()['ctype'] = "application/octet-stream"
            self.mGetResponse()['text']  = _fileC

    def mCreateDiag(self):

        #Compute Exacloud Path
        _exapath = self.mGetConfig().mGetPath()
        _exapath = _exapath[0: _exapath.find("exabox")] 

        _args = "-clu create_diag -cf {0}".format(self.mGetBody()['remote_xml_path'])
        if "remote_payload_path" in list(self.mGetBody().keys()):
            _args = "{0} -jc {1}".format(_args, self.mGetBody()['remote_payload_path'])

        _cmd = []
        _cmd.append(os.path.join(_exapath, "bin/exacloud"))
        _cmd.append(_args)

        _cmdList = [_cmd]

        #Run the command and return the response
        self.mGetResponse()['text'] = self.mCreateBashProcess(_cmdList, aName="diag create")


    def mGet(self):
        self.mGetResponse()['text'] = self.mListDiags()

    def mPost(self):
        self.mDownloadDiag(self.mGetBody()['zip'])

    def mPut(self):
        self.mCreateDiag()

