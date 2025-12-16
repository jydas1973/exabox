#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/globalcache/GlobalCacheWorker.py /main/15 2025/11/13 07:05:36 joysjose Exp $
#
# GlobalCacheWorker.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      GlobalCacheWorker.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    joysjose    11/04/25 - Bug 38599605 modify GI bits naming for n-3
#                           according to new OEDA changes
#    akkar       11/04/24 - Bug 37177099: Delete img and sha256 files for
#                           corrupted images as well
#    akkar       10/08/24 - Bug 37114329:Fix reflink logic for 23ai image
#    akkar       01/18/24 - Bug 36172169:Fix reflink creation check
#    ririgoye    12/03/23 - Bug 35951395 - Fix mCreateSymbolicLink to copy
#                           grik-klone images
#    akkar       10/17/23 - Enh 35569058 - Add workaround for multiple GI image provisioning.
#    naps        07/03/23 - Bug 35502615 - Fix image copy failure .
#    aararora    01/13/23 - The comparison for image to be correct should be
#                           only with hash.
#    aypaul      07/11/22 - Enh#34340951 Remove transfer of dbklone and dbnid
#                           bits from imagerepo to dom0 globalcache.
#    jesandov    01/14/22 - Add validation on Close Connections
#    jesandov    10/07/21 - Creation
#

import os
import re
import time
import json
import copy

from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace, ebLogDebug
from exabox.core.Error import ExacloudRuntimeError
from exabox.agent.ExaLock import ExaLock
_26AIREFERENCE = "232600251021"
_26AIMAJORMINORREF = "2326"
class GlobalCacheWorker:

    def __init__(self, aImageLocalPath, aImageHash, aDom0List):

        self.__globalCacheFolder = get_gcontext().mGetConfigOptions()['global_cache_dom0_folder']
        _remotePath = os.path.basename(aImageLocalPath)
        _remotePath = os.path.join(self.__globalCacheFolder, _remotePath)

        self.__imageLocalPath = aImageLocalPath
        self.__imageRemotePath = _remotePath
        self.__imageHash = aImageHash

        self.__dom0List = aDom0List
        self.__localCopyDom0s = []
        self.__connections = {}

        self.__imageName = os.path.basename(aImageLocalPath)
        #Lets have json file per image And acquire lock wrt this json file.
        #i.e, We will have a separate lock for every image copy across dom0s.
        #This will give us greater control and keep each image updation clean. 
        self.__imageInfoFile = os.path.join(self.__globalCacheFolder, f"ImagesInformation{self.__imageName}.json")
    #######################
    # Getters and Setters #
    #######################

    def mGetImageLocalPath(self):
        return self.__imageLocalPath

    def mSetImageLocalPath(self, aStr):
        self.__imageLocalPath = aStr

    def mGetImageRemotePath(self):
        return self.__imageRemotePath

    def mSetImageRemotePath(self, aStr):
        self.__imageRemotePath = aStr

    def mGetImageHash(self):
        return self.__imageHash

    def mSetImageHash(self, aStr):
        self.__imageHash = aStr

    def mGetDom0List(self):
        return self.__dom0List

    def mSetDom0List(self, aList):
        self.__dom0List = aList

    def mGetLocalCopyDom0s(self):
        return self.__localCopyDom0s

    def mSetLocalCopyDom0s(self, aStr):
        self.__localCopyDom0s = aStr

    def mGetConnections(self):
        return self.__connections

    def mSetConnections(self, aDict):
        self.__connections = aDict

    def mGetGlobalCacheFolder(self):
        return self.__globalCacheFolder

    def mGetImageInfoFile(self):
        return self.__imageInfoFile

    #################
    # CLASS METHODS #
    #################
    
    def mDoImageCopy(self):

        try:

            # Create connections
            self.mCreateConnections()
            self.mCalculateInitialHash()

            _maxRetries = 3
            _currentRetry = 0

            #Lets acquire lock here using json file corresponding to the image.
            #It will ensure atomocity for below 3 operations:
            #a. Read json file
            #b. Copy image local and remote
            #c. Update json with correct contents

            ebLogInfo(f'Waiting for lock dom0_global_cache_{self.__imageName}')
            with ExaLock(f"dom0_global_cache_{self.__imageName}"):
                ebLogInfo(f'Got   the   lock dom0_global_cache_{self.__imageName}')        
                while _currentRetry < _maxRetries:

                    _missingDom0s = self.mCalculateMissingDom0s()

                    # All images complete
                    if not _missingDom0s:
                        #Adding this fix to make sure 23.26 images 
                        # are copied to /EXAVMIMAGES wihtout fail when 
                        # original file is present in the dom0. 
                        # This will be removed once general fix is merged
                        if _26AIMAJORMINORREF in self.__imageName:
                            _dom0List = self.mGetDom0List()
                            for _dom0 in _dom0List:
                                self.mCreateSymbolicLink(_dom0)
                        ##End of fix for bug 38599605
                        ebLogInfo(f'image {self.__imageName} is consistent across all dom0s !')
                        return True

                    # Remove unncesary images and get space to copy
                    for _dom0 in _missingDom0s:
                        self.mFreeNecesarySpace(_dom0)

                    # Copy local to dom0
                    for _dom0 in _missingDom0s:
                        if _dom0 in self.mGetLocalCopyDom0s():
                            self.mCopyExacloudToDom0(_dom0)

                    # Copy dom0 to dom0
                    for _dom0 in _missingDom0s:

                        if _dom0 in self.mGetLocalCopyDom0s():
                            continue

                        self.mCopyDom0ToDom0(self.mGetLocalCopyDom0s()[0], _dom0)

                    _currentRetry += 1

                # Verify dom0s
                _missingDom0s = self.mCalculateMissingDom0s()
                if not _missingDom0s:
                     return True

                _msg = f"Could not copy {self.mGetImageRemotePath()} on {_missingDom0s}"
                ebLogError(_msg)
                raise ExacloudRuntimeError(0x0754, 0x0A, _msg)
        finally:
            self.mCloseConnections()

    def mCalculateInitialHash(self):

        if not self.mGetImageHash():
            _hash = self.mCalculateHash("local", self.mGetImageLocalPath())
            self.mSetImageHash(_hash)


    def mCalculateHash(self, aDom0, aImagePath):

        _node = self.mGetConnections()[aDom0]
        _hash = None

        _, _o, _e = _node.mExecuteCmd(f"/usr/bin/sha256sum {aImagePath}")
        if _node.mGetCmdExitStatus() == 0:

            _sha256sum = _o.read()
            _sha256sum = _sha256sum.split(" ")[0]
            _hash = _sha256sum

        return _hash


    def mCalculateImageInfoState(self, aDom0, aImagePath, aCalculateHash=False):

        _content = {}
        _node = self.mGetConnections()[aDom0]

        _content['path'] = aImagePath


        _maxRetries = 10                                                                                                                                                                                        
        _currentRetry = 0

        while _currentRetry < _maxRetries:

            _, _o, _ = _node.mExecuteCmd(f"/usr/bin/stat {aImagePath} -c %x,%z,%s")

            _content['access_time'] = ""
            _content['create_time'] = ""
            _content['size'] = ""

            if _node.mGetCmdExitStatus() == 0:

                _cmdOut = _o.read().strip()

                if _cmdOut:

                    _cmdSplit = _cmdOut.split(",")
                    _content['access_time'] = _cmdSplit[0]
                    _content['create_time'] = _cmdSplit[1]
                    _content['size'] = _cmdSplit[2]
                    break
            _currentRetry += 1
            #Sometimes file is not ready yet for 'stat' to work.. hence lets retry after 1 second!
            ebLogInfo(f'Iteration {_currentRetry} to stat file {aImagePath}')
            time.sleep(1)

        _content['hash'] = ""
        if aCalculateHash:
            _content['hash'] = self.mCalculateHash(aDom0, aImagePath)

        return _content

    def mGetRemoteImageState(self, aDom0):

        _content = {}

        #No need to acquire lock here
        #Since we already acquired json lock in mDoImageCopy
        _node = self.mGetConnections()[aDom0]

        _, _o, _ = _node.mExecuteCmd(f"/bin/cat {self.mGetImageInfoFile()}")

        if _node.mGetCmdExitStatus() == 0:
            _out = _o.read()
            ebLogTrace(f'mGetRemoteImageState: Read from {aDom0}  : {_out}')                                                                                           
            try:
                _content = json.loads(_out)

            except Exception as e:
                ebLogWarn(f'mGetRemoteImageState: {e}')
                pass

        return _content

    def mUpdateRemoteImageState(self, aDom0, aRemoteDict, aDelete=False):

        #No need to acquire lock here
        #Since we already acquired json lock in mDoImageCopy

        _node = self.mGetConnections()[aDom0]
        _imageName = os.path.basename(aRemoteDict['path'])

        _content = self.mGetRemoteImageState(aDom0)

        if aDelete:

            if _imageName in _content:
                del _content[_imageName]

        else:
            _content[_imageName] = aRemoteDict

        try:
            _content = json.dumps(_content, sort_keys=True, indent=4)
            ebLogTrace(f'mUpdateRemoteImageState: Writing for {aDom0}: {_imageName}')
            _node.mWriteFile(self.mGetImageInfoFile(), _content.encode('utf-8'), aAppend=False)

        except Exception as e:
            raise


    def mCalculateMissingDom0s(self):

        # Review status
        _dom0List = self.mGetDom0List()
        _missingDom0s = []

        for _dom0 in _dom0List:

            _status = self.mVerifyRemoteStatus(_dom0)

            if _status == "complete":
                continue

            elif _status == "missing":
                _missingDom0s.append(_dom0)

            elif _status == "corrupted":
                self.mRemoveImageMetaData(_dom0, self.mGetImageRemotePath())
                self.mRemoveImage(_dom0, self.mGetImageRemotePath())
                _missingDom0s.append(_dom0)

        return _missingDom0s

    def mGetEmptySpace(self, aDom0):

        _node = self.mGetConnections()[aDom0]
        _dirname = os.path.dirname(self.mGetImageRemotePath())
        _dirname = os.path.join(_dirname, "..")
        _dirname = os.path.abspath(_dirname)

        _cmd = f"/bin/df {_dirname} -m --total | /bin/grep total | /bin/awk '{{print $4}}'"
        _, _o, _e = _node.mExecuteCmd(_cmd)

        if _node.mGetCmdExitStatus() != 0:
            _errorStr = _e.read()
            ebLogError(_errorStr)
            raise ExacloudRuntimeError(0x0754, 0x0A, _errorStr)

        return int(_o.read())

    def mFreeNecesarySpace(self, aDom0):

        _node = self.mGetConnections()[aDom0]
        _dirname = os.path.dirname(self.mGetImageRemotePath())

        _minimumSpace = int(get_gcontext().mGetConfigOptions()['global_cache_minimum_mb_required'])
        _actualSpace = self.mGetEmptySpace(aDom0)

        while _minimumSpace > _actualSpace:

            # Remove oldest image

            _cmd = f"/bin/ls -t1 --time=atime {_dirname} | /usr/bin/tail -n 1"
            _, _o, _e = _node.mExecuteCmd(_cmd)

            if _node.mGetCmdExitStatus() != 0:
                _errorStr = _e.read()
                ebLogError(_errorStr)
                raise ExacloudRuntimeError(0x0754, 0x0A, _errorStr)

            _file = _o.read().strip()

            if not _file:
                ebLogInfo(f"Minimal:{_minimumSpace}, Actual:{_actualSpace}")
                _errorStr = "No remaining images to remove"
                ebLogError(_errorStr)
                raise ExacloudRuntimeError(0x0754, 0x0A, _errorStr)

            self.mRemoveImage(aDom0, os.path.join(_dirname, _file))

            _actualSpace = self.mGetEmptySpace(aDom0)


    def mCreateConnections(self):

        _bestDom0 = None
        _bestTime = 100000000

        for _dom0 in self.mGetDom0List():

            _startTime = time.time()

            _node = exaBoxNode(get_gcontext())
            _node.mConnect(_dom0)
            self.mGetConnections()[_dom0] = _node

            _totalTime = time.time() - _startTime

            if _totalTime < _bestTime:
                _bestDom0 = _dom0
                _bestTime = _totalTime

        if not self.mGetLocalCopyDom0s():
            self.mSetLocalCopyDom0s([_bestDom0])

        # create local node
        _node = exaBoxNode(get_gcontext(), aLocal=True)
        _node.mConnect()
        self.mGetConnections()['local'] = _node


    def mCloseConnections(self):

        _activeConns = list(self.mGetConnections().keys())
        for _dom0 in _activeConns:

            try:
                _node = self.mGetConnections()[_dom0]
                _node.mDisconnect()

                del self.mGetConnections()[_dom0]
            except Exception as e:
                ebLogWarn(f"Error while close connection of node {_dom0}")
                ebLogWarn(e)

    def mRemoveImage(self, aDom0, aImagePath):

        _node = self.mGetConnections()[aDom0]

        _node.mExecuteCmd(f"/bin/rm -f {aImagePath}")
        if _node.mGetCmdExitStatus() != 0:
            ebLogError("No more images to remove")
            raise ExacloudRuntimeError(0x0754, 0x0A, f"No more images in {aImagePath} to remove")

        ebLogWarn(f"Deleting {aImagePath} on {aDom0}")
        _imageDict = {'path': aImagePath}
        self.mUpdateRemoteImageState(aDom0, _imageDict, aDelete=True)
        
    def mRemoveImageMetaData(self, aDom0, aImagePath):
        """Delete .img and sha256sum files of corrupted images

        Arguments:
            aDom0 -- dom0 node 
            aImagePath -- globalcache path of corrupted image

        Raises:
            ExacloudRuntimeError: Error during removal
        """
        try:
            _node = self.mGetConnections()[aDom0]
            _grid_klone_image = aImagePath.split('/')[-1]
            ebLogTrace(f"Metadata removal for {_grid_klone_image}")
            _image_split = _grid_klone_image.split("-")
            _version_zip = _image_split[-1] # "23500240716.zip"
            _version = self.mReturnVersionName(_version_zip)
            _image_split[-1] = _version
            _major_version_image = "-".join(item for item in _image_split)
            ebLogTrace(f"Looking for metadata images with major version: {_major_version_image}")
            _50img_file_path = f"/EXAVMIMAGES/{_major_version_image.replace('.zip', '.50.img')}"
            _sha256_file_path = f"/EXAVMIMAGES/{_major_version_image.replace('.zip', '.sha256')}"
            _files_to_delete = [_50img_file_path, _sha256_file_path]
            for _file in _files_to_delete:
                if not _node.mFileExists(_file):
                    ebLogTrace(f" {_file} file does not exist, skipping deletion")
                    continue
                ebLogTrace(f"Deleting metadata for {_grid_klone_image} : {_file}")
                _node.mExecuteCmdLog(f"/bin/rm -f {_file}")
        except Exception as e:
            ebLogWarn(f'Removal of GI image metadata failed due to : {str(e)}')

    def mVerifyRemoteStatus(self, aDom0):

        _node = self.mGetConnections()[aDom0]

        if not _node.mFileExists(self.mGetImageRemotePath()):
            return "missing"

        _content = self.mGetRemoteImageState(aDom0)
        _imageName = os.path.basename(self.mGetImageRemotePath())

        if _imageName not in _content:
            return "corrupted"

        _imageInfo = _content[_imageName]

        if _imageInfo['hash'] == self.mGetImageHash():

            ebLogInfo(f"Image correct {self.mGetImageRemotePath()} in {aDom0}")
            return "complete"

        return "corrupted"
    
    def mReturnVersionName(self,aVersion):
        _version = aVersion
        _major_version = _version[:2] # "23"
        _ru_date_zip = _version[-10:] # "240716.zip"
        _version_number = _version[:-4] # "23500240716"
        #From this version onwards, there is change in OEDA naming for supported files
        _result = int(_version_number) >= int(_26AIREFERENCE)
        if _result:
            _version = _major_version + "000" + _version[2:-10] + "0" + ".zip" #232600251021 -> 2300026000.zip
        else:
            _version = _major_version + "000" + _ru_date_zip # "23000240716.zip"
        return _version
        

    def mCreateSymbolicLink(self, aDom0):

        _node = self.mGetConnections()[aDom0]

        if "grid-klone" in self.mGetImageRemotePath():

            _image = os.path.basename(self.mGetImageRemotePath())
            _link = f"/EXAVMIMAGES/{_image}"
            _remote = self.mGetImageRemotePath()

            _cmd = f"/bin/rm -f {_link}"
            _node.mExecuteCmd(_cmd)

            _cmd = f"/bin/cp --reflink {_remote} {_link}"
            _node.mExecuteCmd(_cmd)
            
            # workaround till oeda fix
            # Create reflink with major version only for oeda compatibility
            try:
                _image_split = _image.split("-")
                _version_zip = _image_split[-1] # "23500240716.zip"
                _version = self.mReturnVersionName(_version_zip)
                _image_split[-1] = _version
                _major_version_image = "-".join(item for item in _image_split)
                if _major_version_image != _image: #avoid creation of reflink for same image name
                    ebLogInfo(f'Image name with Major version only for oeda support: {_major_version_image}')
                    _major_version_link = f"/EXAVMIMAGES/{_major_version_image}"
                    _cmd = f"/bin/cp --reflink {_remote} {_major_version_link}"
                    _node.mExecuteCmd(_cmd)
            except Exception as e:
                ebLogError(f'Error during major version reflink creation : {e}')



    def mCopyExacloudToDom0(self, aDom0):

        _node = self.mGetConnections()[aDom0]

        _dirname = os.path.dirname(self.mGetImageRemotePath())
        _node.mExecuteCmdLog(f"/bin/mkdir -p {_dirname}")

        ebLogInfo(f"Copy image local#{self.mGetImageLocalPath()} to {aDom0}#{self.mGetImageRemotePath()}")
        _ok = _node.mCopyFile(self.mGetImageLocalPath(), self.mGetImageRemotePath())

        if _node.mFileExists(self.mGetImageRemotePath()):
            ebLogInfo(f"File exists in dom0:{aDom0}, creating reflink in /EXAVMIMAGES")
            self.mCreateSymbolicLink(aDom0)
            _ok = True

        # Update
        _info = self.mCalculateImageInfoState(aDom0, self.mGetImageRemotePath(), aCalculateHash=True)
        self.mUpdateRemoteImageState(aDom0, _info, aDelete=False)
        ebLogInfo(f"Local Copy {self.mGetImageRemotePath()} complete in {aDom0}")
        
        return _ok

    def mCopyDom0ToDom0(self, aFromDom0, aToDom0):

        _nodeTo = self.mGetConnections()[aToDom0]
        _nodeFrom = self.mGetConnections()[aFromDom0]

        _dirname = os.path.dirname(self.mGetImageRemotePath())
        _nodeTo.mExecuteCmdLog(f"/bin/mkdir -p {_dirname}")

        ebLogInfo(f"Copy image {aFromDom0}#{self.mGetImageRemotePath()} to {aToDom0}#{self.mGetImageRemotePath()}")

        _cmd = f"/usr/bin/scp"
        _cmd = f"{_cmd} -i /root/.ssh/global_cache_key"
        _cmd = f"{_cmd} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
        _cmd = f"{_cmd} {self.mGetImageRemotePath()}"
        _cmd = f"{_cmd} root@{aToDom0}:{self.mGetImageRemotePath()}"
        _nodeFrom.mExecuteCmdLog(_cmd)

        _ok = _nodeFrom.mGetCmdExitStatus() == 0

        if _ok:
            self.mCreateSymbolicLink(aToDom0)
        else:
            self.mGetLocalCopyDom0s().append(aToDom0)

        # Update
        _info = self.mCalculateImageInfoState(aToDom0, self.mGetImageRemotePath(), aCalculateHash=True)
        self.mUpdateRemoteImageState(aToDom0, _info, aDelete=False)
        ebLogInfo(f"Remote Copy {self.mGetImageRemotePath()} complete in {aToDom0}")

        return _ok


# end of file
