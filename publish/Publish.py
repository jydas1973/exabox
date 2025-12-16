"""
 Copyright (c) 2015, 2019, Oracle and/or its affiliates. All rights reserved.

NAME:
    Publish Packages to Remote Host

FUNCTION:
    Provide basic/core API for managing Packages (locally and remote)

NOTE:
    None

History:
    ndesanto    10/02/2019 - Enh 30374491: EXACC PYTHON 3 MIGRATION BATCH 02
    mirivier    01/06/2014 - Create file
"""

from exabox.log.LogMgr import ebLogError, ebLogDebug, ebLogInfo, ebLogWarn, ebLogCmd
from exabox.core.Context import get_gcontext
import os
import sys

""" ----- exaBoxPackage ----

Name
    exaBoxPackage - Manage and Publish/Upload packages to remote host

PARAMETERS
    Package to Publish
    Node to Publish/Upload to

RETURNS
    NA

NOTE
    Packages need to be _localy_ stored under $(EXACLOUD_HOME)/package
    Packages extension are .pkg (support .sh is also available)
    Packages are uploaded in $(HOME)/exabox.pkgs)
    ...
"""
# TODO: Enhance publish features
# @ Support config parameter to specify remote directory
# @ Support config parameter to specify specific/ad-hoc setup scripts
#
class exaBoxPackage(object):

    def __init__(self, aCtx, aPackageName = None, aNode = None):

        # Add default .pkg extension if not provided (skip shell scripts).
        if aPackageName.rfind('.pkg') == -1 and aPackageName.rfind('.sh') == -1:
            aPackageName = aPackageName + '.pkg'

        self.__pkgname = aPackageName
        self.__node    = aNode
        self.__ctx     = aCtx
        self.__basepath = get_gcontext().mGetBasePath()

        self.__pkgpath     = self.__basepath + '/packages/' + aPackageName
        self.__setupscript =  'setup.sh'
        self.__setupscriptpath = self.__basepath + '/packages/' + self.__setupscript

        chkfile = os.path.isfile(self.__pkgpath)
        if not chkfile:
            ebLogError('Could not find requested package: ' + self.__pkgpath)
            sys.exit(-1)

    def mGetPackageName(self):
        return self.__pkgname

    def mPublish(self, aRemotePath=None):

        if not self.__node or not self.__node.mIsConnected():
            ebLogError('Node / Connection object required to publish package: ' + self.__pkgpath)
            sys.exit(-1)

        if aRemotePath:
            remote_dir = os.path.dirname(aRemotePath)
            aRemotePath = aRemotePath +'/' + self.__pkgname
        else:
            remote_dir = './exabox.pkgs'
            aRemotePath = './exabox.pkgs/'+self.__pkgname

        if self.__node.mMakeDir(remote_dir):
            self.__node.mCopyFile(self.__setupscriptpath, remote_dir+'/'+os.path.basename(self.__setupscriptpath))
            self.__node.mChmodFile(remote_dir+'/'+os.path.basename(self.__setupscriptpath), 0o774)
            ebLogInfo('Installing setup script')

        self.__node.mCopyFile(self.__pkgpath, aRemotePath)

    def mInstallPkg(self):

        if not self.__node or not self.__node.mIsConnected():
            ebLogError('Node / Connection object required to publish package: ' + self.__pkgpath)
            sys.exit(-1)

        ebLogCmd(self.__node.mExecuteCmd('./exabox.pkgs/' + self.__setupscript + ' ' + self.__pkgname))

    def mInstallSetup(self):

        if not self.__node or not self.__node.mIsConnected():
            ebLogError('Node / Connection object required to install setup script')
            sys.exit(-1)

        remote_dir = './exabox.pkgs'
        aRemotePath = './exabox.pkgs/'+self.__pkgname

        self.__node.mMakeDir(remote_dir)
        self.__node.mCopyFile(self.__setupscriptpath, remote_dir+'/'+os.path.basename(self.__setupscriptpath))
        self.__node.mChmodFile(remote_dir+'/'+os.path.basename(self.__setupscriptpath), 0o774)
        ebLogInfo('Installing setup script')

    def mExecuteSetup(self):

        ebLogError('*** Not Yet Implemented ***')
        pass


