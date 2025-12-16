"""
 Copyright (c) 2014, 2022, Oracle and/or its affiliates.

NAME:
    EditorHandler - Basic functionality

FUNCTION:
    Editor endpoint of the managment

NOTE:
    None    

History:
    hgaldame    11/01/2022 - 33995798 - exacc remoteec enhancements 
                             exaccops-hot 
    hgaldame    09/30/2022 - 34627398 - exacc:bb:22.3.1:cps-sw upgrade: provide
                             proper error code for precheck failure instead of
                             returning generic error
    jesandov    06/04/2020 - Add validation against 'folder' hidden parameter
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
import json
import stat 
from exabox.BaseServer.BaseEndpoint import BaseEndpoint
from pathlib import Path
from datetime import datetime
class EditorEndpoint(BaseEndpoint):


    def __init__(self, aHttpUrlArgs, aHttpBody, aHttpResponse, aSharedData):

        #Initializate the class
        BaseEndpoint.__init__(self, aHttpUrlArgs, aHttpBody, aHttpResponse, aSharedData)

        self.__whitelist = self.mGetConfig().mGetConfigValue("editor_whitelist")
        self.__whitelist.insert(0, self.mGetConfig().mGetExacloudPath())
        if self.mGetConfig().mGetExacloudConfigValue("ociexacc"):
            _token = self.mGetConfig().mGetConfigValue("ecra_token")
            if _token and os.path.exists(_token):
                with open(_token, "r") as _file:
                    _token_json = json.load(_file)
                _cpswa_dir = os.path.join( _token_json["install_dir"], "dyntasks")
                if _cpswa_dir not in self.__whitelist:
                        self.__whitelist.append(_cpswa_dir)
        self.__exacloudLogsBlackList = self.mGetConfig().mGetConfigValue("exacloud_log_qry_blacklist")

    def mGetWhiteList(self):
        return self.__whitelist

    def mResetWhiteList(self, aFolder):
        _validFolder = self.mGetPath(aFolder)

        if _validFolder:
            self.__whitelist = [_validFolder]
            return True
        else:
            return False

    def mListFiles(self, aPath, aRegex=None, aLimit=None):
        _files = []
        _is_exacloud_log = False
        int_limit = aLimit if aLimit is not None else 20
        try:
            _local_path = Path(self.mGetConfig().mGetExacloudPath()).joinpath("log/threads/0000-0000-0000-0000")
            _param_path = Path(self.mGetConfig().mGetExacloudPath()).joinpath(aPath)
            _is_exacloud_log = _local_path == _param_path
            
            _exacloud_blacklist = self.__exacloudLogsBlackList 
            _expr_blacklist = [ re.escape(_pattern) for _pattern in _exacloud_blacklist]
            _regex_blacklist = re.compile("|".join(_expr_blacklist))
            for _file in set(os.listdir(aPath)):
                if aRegex is not None:
                    if re.search(aRegex, _file) is not None:
                        _files.append(_file)
                else:
                    if _is_exacloud_log:
                        # filter exacloud log files from blacklist when no regex
                        if re.search(_regex_blacklist, _file):
                            continue
                        _files.append(_file)                                    
                    else:
                        _files.append(_file)
            if _files:
                def mGetmtimeFromPath(_aFile):
                    try:
                        _filePath = os.path.join(aPath,_aFile)
                        if os.path.exists(_filePath):
                            return os.path.getmtime(_filePath)
                    except OSError:
                        pass
                    return None
                _sorted_list = sorted(_files, key=mGetmtimeFromPath, reverse=True)
                _sliced_files = _sorted_list[:int_limit]
                _files = [ self.mBuildDictFromFile(aPath, _path) for _path in _sliced_files]
        except Exception as e:
            self.mGetResponse()['text'] = "Could not list directory: {0}".format(e)
            self.mGetResponse()['error'] = "Could not list directory: {0}".format(e)
            self.mGetResponse()['status'] = 500

        return _files

    def mGetPath(self, aFile=None):

        if aFile is None:
            return self.mGetWhiteList()[0]

        else:

            if aFile.startswith("/"):
                _path = os.path.abspath(aFile)
                for _white in self.mGetWhiteList():
                    if _path.startswith(_white):
                        return _path

            else:
                _path = os.path.abspath("{0}/{1}".format(self.mGetConfig().mGetExacloudPath(), aFile))

                if _path.startswith(self.mGetConfig().mGetExacloudPath()):
                    return _path

            return None

    def mGetFileContent(self, aFile, aOffset=None, aLimit=None, aRegex=None):

        _filecontent = []
        _maxLines    = 0

        try:
            with open(aFile, "r") as _f:
                _lines = [x.rstrip("\n") for x in _f.readlines()]

                _filecontent = []
                _counter = 0
                for _line in _lines:
                    _filecontent.append([_counter, _line])
                    _counter += 1

            _maxLines = len(_filecontent)
        except Exception as e:
            self.mGetResponse()['text']  = "Could not get file content: {0}".format(e)
            self.mGetResponse()['error']  = "Could not get file content: {0}".format(e)
            self.mGetResponse()['status'] = 500
            return None

        if aLimit is not None and aOffset is None:
            _filecontent = _filecontent[0: aLimit]

        elif aLimit is None and aOffset is not None:
            _filecontent = _filecontent[aOffset: ]

        elif aLimit is not None and aOffset is not None:
            _filecontent = _filecontent[aOffset : aLimit+aOffset]

        _content = {}
        for _c in _filecontent:
            _maxFill = int(math.log10(_maxLines))+1
            _lineNum = str(_c[0]).zfill(_maxFill)
            _content[_lineNum] = _c[1]

        if aRegex is not None:
            for _c in copy.deepcopy(_content).keys():
                if re.search(aRegex, _content[_c]) is None:
                    _content.pop(_c)

        return _content

    def mReplaceFile(self, aFile, aWholeText):

        try:
            with open(aFile, "w") as _f:
                _f.write(aWholeText)
                _f.write("\n")
                return True
        except Exception as e:
            self.mGetResponse()['text']  = "Could not replace file: {0}".format(e)
            self.mGetResponse()['error']  = "Could not replace file: {0}".format(e)
            self.mGetResponse()['status'] = 500
            return False

    def mGet(self):
        if self.mGetUrlArgs() is None:
            self.mGetResponse()["text"] = {"files": self.mListFiles(self.mGetPath())}

        else:

            _offset = None
            _limit  = None
            _file   = None
            _regex  = None

            if "folder" in self.mGetUrlArgs().keys():
                _folder = self.mGetUrlArgs()['folder']

                if not self.mResetWhiteList(_folder):
                    self.mGetResponse()['text']  = "Invalid folder location: {0}".format(_folder)
                    self.mGetResponse()['error']  = "Invalid folder location: {0}".format(_folder)
                    self.mGetResponse()['status'] = 500
                    return False

            if "offset" in self.mGetUrlArgs().keys():
                try:
                    _offset = int(self.mGetUrlArgs()['offset'])
                except:
                    _offset = None

            if "limit" in self.mGetUrlArgs().keys():
                try:
                    _limit = int(self.mGetUrlArgs()['limit'])
                except:
                    _limit = None

            if "file" in self.mGetUrlArgs().keys():
                _file = self.mGetUrlArgs()['file']

                if "folder" in self.mGetUrlArgs().keys():
                    _file = "{0}/{1}".format(self.mGetWhiteList()[0], _file)
                    _file = os.path.abspath(_file)

                _file = self.mGetPath(_file)
            else:
                _file = self.mGetPath()

            if "regex" in self.mGetUrlArgs().keys():
                _regex = self.mGetUrlArgs()['regex']

            if _file is None:
                self.mGetResponse()['status'] = 404
                self.mGetResponse()['error'] = "File outside the whitelist folders"

            elif not os.path.exists(_file):
                self.mGetResponse()['status'] = 404
                self.mGetResponse()['error'] = "File does not exists"
            else:

                if os.path.isdir(_file):
                    self.mGetResponse()['text'] = {"files": self.mListFiles(_file, _regex, aLimit=_limit)}
                else:
                    self.mGetResponse()['text'] = {'filecontent': self.mGetFileContent(_file, _offset, _limit, _regex) }

    def mPost(self):

        _file = self.mGetPath(self.mGetBody()['file'])

        if "folder" in self.mGetBody().keys():
            _folder = self.mGetBody()['folder']

            if not self.mResetWhiteList(_folder):
                self.mGetResponse()['text']  = "Invalid folder location: {0}".format(_folder)
                self.mGetResponse()['error']  = "Invalid folder location: {0}".format(_folder)
                self.mGetResponse()['status'] = 500
                return False

            _file = "{0}/{1}".format(self.mGetWhiteList()[0], self.mGetBody()['file'])
            _file = os.path.abspath(_file)
            _file = self.mGetPath(_file)

        if _file is None:
            self.mGetResponse()['status'] = 404
            self.mGetResponse()['error'] = "File outside the exacloud folder"

        elif os.path.exists(_file):
            self.mGetResponse()['text'] = "Error, File already on the Filesystem"
            self.mGetResponse()['error'] = "Error, File already on the Filesystem"
            self.mGetResponse()['status'] = 500

        else:

            _type = self.mGetBody()['type']

            if _type == "folder":
                os.makedirs(_file)
                self.mGetResponse()['text'] = {"files": self.mListFiles(_file)}

            else:

                _text = ""
                if "text" in self.mGetBody().keys():
                    _text = self.mGetBody()['text']

                if self.mReplaceFile(_file, _text):
                    self.mGetResponse()['text'] = {'filecontent': self.mGetFileContent(_file) }


    def mPut(self):

        _file = self.mGetPath(self.mGetBody()['file'])

        if "folder" in self.mGetBody().keys():
            _folder = self.mGetBody()['folder']

            if not self.mResetWhiteList(_folder):
                self.mGetResponse()['text']  = "Invalid folder location: {0}".format(_folder)
                self.mGetResponse()['error']  = "Invalid folder location: {0}".format(_folder)
                self.mGetResponse()['status'] = 500
                return False

            _file = "{0}/{1}".format(self.mGetWhiteList()[0], self.mGetBody()['file'])
            _file = os.path.abspath(_file)
            _file = self.mGetPath(_file)

        if _file is None:
            self.mGetResponse()['status'] = 404
            self.mGetResponse()['error'] = "File outside the exacloud folder"
            self.mGetResponse()['text']   = "File outside the exacloud folder"

        elif not os.path.exists(_file):
            self.mGetResponse()['text'] = "Error, File not in the Filesystem"
            self.mGetResponse()['error'] = "Error, File not in the Filesystem"
            self.mGetResponse()['status'] = 500

        elif os.path.isdir(_file):
            self.mGetResponse()['text'] = "Error, File is a folder"
            self.mGetResponse()['error'] = "Error, File is a folder"
            self.mGetResponse()['status'] = 500

        else:

            _offset = None
            _limit  = 1

            if "offset" in self.mGetBody().keys():
                try:
                    _offset = int(self.mGetBody()['offset'])
                except:
                    _offset = None

            if "limit" in self.mGetBody().keys():
                try:
                    _limit = int(self.mGetBody()['limit'])
                except:
                    _limit = 1

            _text = self.mGetBody()['text']

            _newFileC   = []
            _wholeText  = self.mGetFileContent(_file)
            _toRemplace = self.mGetFileContent(_file, _offset, _limit)

            _putContent = False
            for _index in sorted(_wholeText.keys()):

                if _index in _toRemplace.keys():

                    if not _putContent:
                        _newFileC += _text.split("\n")
                        _putContent = True

                else:
                    _newFileC.append(_wholeText[_index])

            if self.mReplaceFile(_file, "\n".join(_newFileC)):

                if _limit is not None:
                    _limit  += 6

                if _offset is not None:
                    _offset -= 3
                    if _offset < 0:
                        _offset = 0

                self.mGetResponse()['text'] = {'filecontent': self.mGetFileContent(_file, _offset, _limit) }

    def mDelete(self):

        _file = self.mGetPath(self.mGetBody()['file'])

        if "folder" in self.mGetBody().keys():
            _folder = self.mGetBody()['folder']

            if not self.mResetWhiteList(_folder):
                self.mGetResponse()['text']  = "Invalid folder location: {0}".format(_folder)
                self.mGetResponse()['error']  = "Invalid folder location: {0}".format(_folder)
                self.mGetResponse()['status'] = 500
                return False

            _file = "{0}/{1}".format(self.mGetWhiteList()[0], self.mGetBody()['file'])
            _file = os.path.abspath(_file)
            _file = self.mGetPath(_file)

        if _file is None:
            self.mGetResponse()['status'] = 404
            self.mGetResponse()['error']  = "File outside the exacloud folder"
            self.mGetResponse()['text']   = "File outside the exacloud folder"

        elif not os.path.exists(_file):
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['text']   = "File not in Filesystem"
            self.mGetResponse()['error']  = "File not in Filesystem"

        else:
            if os.path.isdir(_file):
                try:
                    shutil.rmtree(_file)
                    self.mGetResponse()['text']   = "Folder deleted"
                except Exception as e:
                    self.mGetResponse()['status'] = 500
                    self.mGetResponse()['text']   = "Could not delete the folder: {0}".format(e)
                    self.mGetResponse()['error']  = "Could not delete the folder: {0}".format(e)

            else:
                try:
                    os.remove(_file)
                    self.mGetResponse()['text']   = "File deleted"
                except Exception as e:
                    self.mGetResponse()['status'] = 500
                    self.mGetResponse()['text']   = "Could not delete the file: {0}".format(e)
                    self.mGetResponse()['error']  = "Could not delete the file: {0}".format(e)

    def mPatch(self):

        _mode = self.mGetBody()['mode']

        if _mode == "upload":
            _remote = self.mGetPath(self.mGetBody()['remote'])

            if not _remote:
                self.mGetResponse()['status'] = 404
                self.mGetResponse()['error']  = "File outside the exacloud folder"
                self.mGetResponse()['text']   = "File outside the exacloud folder"

            else:
                try:
                    with open(_remote, "wb") as _f:
                        _fileC = base64.b64decode(self.mGetBody()['local'])
                        _f.write(_fileC)
                        self.mGetResponse()['text'] = "File was saved successful"
                except Exception as e:
                    self.mGetResponse()['status'] = 500
                    self.mGetResponse()['text']   = "Could not save file: {0}".format(e)
                    self.mGetResponse()['error']  = "Could not save file: {0}".format(e)

        elif _mode == "download":

            _remote = self.mGetPath(self.mGetBody()['remote'])

            if not _remote or not os.path.exists(_remote):
                self.mGetResponse()['status'] = 500
                self.mGetResponse()['text']   = "File not found in File System"
                self.mGetResponse()['error']  = "File not found in File System"
            else:

                _fileC = ""
                try:
                    with open(_remote, "rb") as _f:
                        _fileC = _f.read()
                        _fileC = base64.b64encode(_fileC).decode('utf8')

                        self.mGetResponse()['ctype'] = "application/octet-stream"
                        self.mGetResponse()['text']  = _fileC
                except Exception as e:
                    self.mGetResponse()['status'] = 500
                    self.mGetResponse()['text']   = "Could not download file: {0}".format(e)
                    self.mGetResponse()['error']  = "Could not download file: {0}".format(e)

    def mBuildDictFromFile(self, aPath, aFile):
        _pathObj = Path(aPath).joinpath(aFile)
        _file_time = datetime.fromtimestamp(_pathObj.stat().st_mtime)
        _ownership = "{0}:{1}".format(_pathObj.owner(),_pathObj.group()) 
        _type = "undef"
        if _pathObj.is_symlink():
            _type = "symlink"
        elif _pathObj.is_dir():
            _type = "dir"
        elif _pathObj.is_file():
            _type = "file"
        _ui_dict = {
            "name" : str(Path(aPath).joinpath(_pathObj)),
            "mode": stat.filemode(_pathObj.stat().st_mode),
            "mtime": _file_time.strftime('%Y-%m-%d %H:%M:%S+%f'),
            "owner": _ownership,
            "type" : _type, 
            "bytes" : _pathObj.stat().st_size

        }
        return _ui_dict

# enf of file
