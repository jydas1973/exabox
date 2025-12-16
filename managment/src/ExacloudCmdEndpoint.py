"""
 Copyright (c) 2014, 2023, Oracle and/or its affiliates.

NAME:
    ExacloudCmdHandler - Basic functionality

FUNCTION:
    Exacloud Cmd endpoint of the managment

NOTE:
    None    

History:
    hgaldame    11/29/2023 - 36055367 - oci/exacc: unrecognized arguments error
                             executing exacloud commands through remote manager
    jesandov    06/04/2020 - Change function name affected by AsyncTrackEndpoint
    jesandov    26/03/2019 - File Creation
"""



import os
import re
import sys
import uuid
import json
import time
import subprocess
import shlex
from pathlib import Path

from exabox.BaseServer.BaseEndpoint import BaseEndpoint
from exabox.BaseServer.AsyncProcessing import ProcessStructure
from exabox.managment.src.AsyncTrackEndpoint import AsyncTrackEndpoint

class ExacloudCmdEndpoint(AsyncTrackEndpoint):

    def __init__(self, aHttpUrlArgs, aHttpBody, aHttpResponse, aSharedData):

        #Initialization of the base class
        AsyncTrackEndpoint.__init__(self, aHttpUrlArgs, aHttpBody, aHttpResponse, aSharedData)


    def mPost(self):

        _args = self.mGetBody()["args"].split(";")[0]

        #Compute Exacloud Path
        _exapath = self.mGetConfig().mGetPath()
        _exapath = _exapath[0: _exapath.find("exabox")] 

        _cmd = []
        _cmd.append(os.path.join(_exapath, "bin/exacloud"))
        if _args:
            _cmd.extend(shlex.split(_args))

        _cmdlist = [_cmd]

        self.mGetResponse()['text'] = self.mCreateBashProcess(_cmdlist, aName="execute [{0}]".format(_args))


    def mPatch(self):

        #Compute Exacloud Path
        _exapath = self.mGetConfig().mGetPath()
        _exapath = _exapath[0: _exapath.find("exabox")] 

        _parentPath = os.path.abspath("{0}/../".format(_exapath))
        _upgradePath = "{0}/upgrade".format(_parentPath)
        _mode = self.mGetBody()["mode"]

        if os.path.exists(_upgradePath) and _mode != "clean":
            self.mGetResponse()['text']   = "Error, already an upgrade operation begin executed"
            self.mGetResponse()['error']  = "Error, already an upgrade operation begin executed"
            self.mGetResponse()['status'] = 500

        else:

            if _mode == "only_upgrade":
                self.mOnlyUpgrade(_exapath, _upgradePath, _parentPath)

            elif _mode == "clean":
                self.mClean(_exapath, _upgradePath, _parentPath)

            elif _mode == "list_bk":
                self.mListBk(_exapath, _upgradePath, _parentPath)

            elif _mode == "rollback":
                self.mRollback(_exapath, _upgradePath, _parentPath)


    def mGetExacloudBackups(self):

        #Compute Exacloud Path
        aExapath = self.mGetConfig().mGetPath()
        aExapath = aExapath[0: aExapath.find("exabox")] 

        aParentPath = os.path.abspath("{0}/../".format(aExapath))
        return [x for x in os.listdir(aParentPath) if x.find(".bak") != -1]

    def mHasOngoingOperations(self):

        _filter = {"status": "Pending"}
        _database = self.mGetShared()['db']
        _requests = _database.mFilterRequests(_filter)

        return _requests is None or len(_requests) > 0

    def mFindLite(self, aCpsBundleFolder):

        _lite = ""
        for (_dirpath, _, _filenames) in os.walk(aCpsBundleFolder):

            for _filename in _filenames:
                if re.search("exacloud_lite.*tgz", _filename) is not None:
                    _lite = "{0}/{1}".format(_dirpath, _filename)
                    _lite = _lite.strip("/")
                    break

            if _lite != "":
                break

        return _lite

    def mOnlyUpgrade(self, aExapath, aUpgradePath, aParentPath):

        if self.mHasOngoingOperations():
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error']  = "There are ongoing operations on exacloud"
            self.mGetResponse()['text']   = "There are ongoing operations on exacloud"

        else:

            #Fetch the repository_root
            _lite = ""
            if "lite_location" in list(self.mGetBody().keys()):
                _lite = self.mGetBody()['lite_location']

            else:
                _repoRoot = self.mGetConfig().mGetExacloudConfigValue("repository_root")
                _repoFile = os.path.join(_repoRoot, "activeVersion.json")

                if not os.path.exists(_repoFile):
                    self.mGetResponse()['text']   = "Error, activeVersion.json not found on repo_root: {0}".format(_repoRoot)
                    self.mGetResponse()['error']  = "Error, activeVersion.json not found on repo_root: {0}".format(_repoRoot)
                    self.mGetResponse()['status'] = 500

                else:

                    try:
                        with open(_repoFile, "r") as _file:
                            _repoJson = json.load(_file)
                            _dwLite = _repoJson["active"]["cpssw"]["download_location"]
                            _lite = self.mFindLite(_dwLite)

                    except Exception as e:
                        self.mGetResponse()['text']   = "Error, {0}".format(e)
                        self.mGetResponse()['error']  = "Error, {0}".format(e)
                        self.mGetResponse()['status'] = 500

            if _lite == "":
                self.mGetResponse()['text']   = "Error, exacloud_lite location not found"
                self.mGetResponse()['error']  = "Error, exacloud_lite location not found"
                self.mGetResponse()['status'] = 500

            else:

                _id = str(uuid.uuid1())
                _cmdList = []
                _logFile = "{0}/mgnt-{1}.log".format(aUpgradePath, _id)
                os.makedirs(aUpgradePath)
                Path(_logFile).touch()

                #Prepare the folder
                _cmd = ["cp"]
                _cmd.append("{0}/scripts/xpatch.py".format(aExapath))
                _cmd.append(aUpgradePath)
                _cmdList.append(_cmd)

                #Symlink the lite package
                _cmd = ["ln"]
                _cmd.append("-sf")
                _cmd.append(_lite)
                _cmd.append("{0}/exacloud_lite.tgz".format(aUpgradePath))
                _cmdList.append(_cmd)

                #Create the main command of xpatch
                _cmd = ["{0}/bin/python".format(aExapath)]
                _cmd.append("{0}/xpatch.py".format(aUpgradePath))
                _cmd.append("upgrade")
                _cmd.append("-ni")
                _cmd.append("-e {0}".format(aParentPath))
                _cmdList.append(_cmd)

                #Clean up command
                _cmdList.append(["echo", "Running Clean up"])

                _cmd = ["cp", _logFile, "{0}/{1}".format(aExapath, "/log/threads/")]
                _cmdList.append(_cmd)

                _cmd = ["rm", "-rf", aUpgradePath]
                _cmdList.append(_cmd)

                #Run the command and return the response
                self.mGetResponse()['text'] = self.mCreateBashProcess(_cmdList, aId=_id, aLogFile=_logFile, aName="upgrade", aOnFinish=self.mFinish)


    def mFinish(self):
        aExapath = self.mGetConfig().mGetPath()
        aExapath = aExapath[0: aExapath.find("exabox")] 
        os.chdir(aExapath)

    def mListBk(self, aExapath, aUpgradePath, aParentPath):
        _backups = [x for x in os.listdir(aParentPath) if x.find(".bak") != -1]
        self.mGetResponse()['text'] = self.mGetExacloudBackups()


    def mClean(self, aExapath, aUpgradePath, aParentPath):
        _backups = [x for x in os.listdir(aParentPath) if x.find(".bak") != -1]

        _cmdList = []
        _cmdList.append(["echo", 'Running cleanup of backup'])

        for _backup in _backups:
            _cmdList.append(["rm", "-rf", "{0}/{1}".format(aParentPath, _backup)])

        _cmdList.append(["rm", "-rf", "{0}/upgrade".format(aParentPath)])
        _cmdList.append(["echo", 'Cleanup done'])

        #Run the command and return the response
        self.mGetResponse()['text'] = self.mCreateBashProcess(_cmdList, aName="upgrade [clean]")


    def mRollback(self, aExapath, aUpgradePath, aParentPath):

        if "backup_name" not in list(self.mGetBody().keys()):
            self.mGetResponse()['text']   = "Error, missing 'backup_name' param"
            self.mGetResponse()['error']  = "Error, missing 'backup_name' param"
            self.mGetResponse()['status'] = 500

        elif self.mHasOngoingOperations():
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error']  = "There are ongoing operations on exacloud"
            self.mGetResponse()['text']   = "There are ongoing operations on exacloud"

        else:

            _backupName = self.mGetBody()['backup_name']

            if _backupName not in self.mGetExacloudBackups():
                self.mGetResponse()['text']   = "Error, backup: '{0}' does not exists".format(_backupName)
                self.mGetResponse()['error']  = "Error, backup: '{0}' does not exists".format(_backupName)
                self.mGetResponse()['status'] = 500

            else:

                _id = str(uuid.uuid1())
                _logFile = "/tmp/mgnt-{0}.log".format(_id)
                _cmdList = []

                #Stop exacloud
                _cmdList.append(["echo", 'Stopping Exacloud...'])
                _cmdList.append(["{0}/bin/exacloud".format(aExapath), "--agent stop"])

                #Restore exacloud
                _cmdList.append(["echo", 'Restore backup exacloud...'])
                _cmdList.append(["rm", "-rf", "{0}/exacloud".format(aParentPath)])

                _cmd = ["mv", "-v"]
                _cmd.append("{0}/{1}".format(aParentPath, _backupName))
                _cmd.append("{0}/exacloud".format(aParentPath))
                _cmdList.append(_cmd)
                _cmdList.append(["cd"])
                _cmdList.append(["cd", "-"])

                #Start exacloud
                _cmdList.append(["echo", 'Start Exacloud...'])
                _cmdList.append(["{0}/bin/exacloud".format(aExapath), "--agent start -da"])
                _cmdList.append(["echo", 'Rollback Done'])

                #Restore the log
                _cmdList.append(["mv", _logFile, "{0}/{1}".format(aExapath, "/log/threads/")])

                #Run the command and return the response
                self.mGetResponse()['text'] = self.mCreateBashProcess(_cmdList, aId=_id, aLogFile=_logFile, aName="upgrade [rollback]", aOnFinish=self.mFinish)



