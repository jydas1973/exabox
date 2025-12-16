#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/common/ebOedaInstaller.py /main/3 2021/12/14 00:11:20 aypaul Exp $
#
# ebOedaInstaller.py
#
# Copyright (c) 2021, Oracle and/or its affiliates.
#
#    NAME
#      ebOedaInstaller.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      12/02/21 - 33633132 Use oss/bin location to get the latest
#                           OEDA package even for ecs type.
#    jesandov    02/23/21 - Creation
#

import os
import glob

from exabox.exatest.common.ebGeneralInstaller import ebGeneralInstaller

class ebOedaInstaller(ebGeneralInstaller):

    def __init__(self, aExacloudPath, aExaboxConf, aVerbose=False):

        super().__init__(aExacloudPath, aExaboxConf, aVerbose)
        self.__oedaDir = None

    #######################
    # GETTERS AND SETTERS #
    #######################

    def mGetOedaDir(self):
        return self.__oedaDir

    def mSetOedaDir(self, aDir):
        self.__oedaDir = aDir

    #################
    # Class Methods #
    #################

    def mInstallOEDA(self, aInstallDir):

        # Detect OEDA Installed
        _oedaUnzipFolder = aInstallDir
        _oedaFolder = os.path.join(aInstallDir, "linux-x64")
        _oedaLabelFile = os.path.join(_oedaUnzipFolder, "label.txt")

        self.mSetOedaDir(_oedaFolder)

        if os.path.exists(_oedaLabelFile):

            _cmd = "cat {0}".format(_oedaLabelFile)
            _, _out, _ = self.mExecuteLocal(_cmd)
            _label = _out

            print("Already OEDA: {0}".format(_out), flush=True)

        else:

            # Remove current OEDA
            _cmd = "rm -rf {0}".format(_oedaUnzipFolder)
            self.mExecuteLocal(_cmd)

            _cmd = "mkdir -p {0}".format(_oedaFolder)
            self.mExecuteLocal(_cmd)

            _ade_view_root = os.getenv('ADE_VIEW_ROOT')
            if _ade_view_root is None:
                raise Exception("Please execute unit tests from inside a ADE view and make sure environment variable \
                ADE_VIEW_ROOT is set.")
            _ocmd_installer_package_searchexp = os.path.join(_ade_view_root, "oss/bin/Ocmd*OTN*linux*")
            _search_results = glob.glob(_ocmd_installer_package_searchexp)

            if _search_results is None or type(_search_results) is not list:
                raise Exception(f"OCMD package could not be found. Search expression: {_ocmd_installer_package_searchexp}")
            _filesToCopy = _search_results[0]

            # Copy the files
            _cmd = "cp -Lf {0} {1}".format(_filesToCopy, _oedaUnzipFolder)
            _rc, _, _err = self.mExecuteLocal(_cmd)

            if _rc != 0:
                raise ValueError(_err)

            # Untar the files
            _zipFile = "{0}/{1}".format(_oedaUnzipFolder, 'Ocmd*OTN*linux*')
            _cmd = "unzip {0} -d {1}".format(_zipFile, _oedaUnzipFolder)

            _rc, _, _err = self.mExecuteLocal(_cmd)

            if _rc != 0:
                raise ValueError(_err)

            # Save Cache of label
            _oeda_version_cmd = "{} -h".format(os.path.join(_oedaFolder, "install.sh"))
            _rc, _out, _err = self.mExecuteLocal(_oeda_version_cmd)
            _label = "DUMMY OEDA VERSION"
            if _out:
                _label = _out.split("\n")[-1].strip()
            with open(os.path.join(_oedaUnzipFolder, "label.txt"), "w") as f:
                f.write(_label)

            print("Install OEDA: {0}".format(_label), flush=True)

        self.mGetExaboxCfg()['oeda_dir'] = _oedaFolder

    def mInstall(self, aInstallDir):

        self.mInstallOEDA(aInstallDir)

# end of file
