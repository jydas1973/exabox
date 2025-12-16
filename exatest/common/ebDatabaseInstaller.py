#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/common/ebDatabaseInstaller.py /main/12 2023/10/06 08:38:40 jesandov Exp $
#
# ebDatabaseInstaller.py
#
# Copyright (c) 2021, 2023, Oracle and/or its affiliates.
#
#    NAME
#      ebDatabaseInstaller.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    sdevasek    05/22/22 - Enh 33859232 Call mCreatePatchingTimeStatsTable
#    hgaldame    05/06/22 - 34146854 - oci/exacc: persists exacloud remote ec
#                           async request status
#    ndesanto    04/13/22 - Adding new DB table creationg to exatest.
#    rajsag      02/21/22 - 33422731 - retry of vm memory workflow not checking
#                           status of previous node, could cause complete
#                           outage
#    nmallego    07/25/21 - Bug33153140 - Change position of
#                           clusterpatchoperations table creation
#    nmallego    07/13/21 - Bug32925372- Call mCreateClusterPatchOperationsTable
#    jesandov    02/23/21 - Creation
#

import os
import socket
import subprocess as sp

from exabox.tools.AttributeWrapper import wrapStrBytesFunctions

from exabox.exatest.common.ebGeneralInstaller import ebGeneralInstaller

from exabox.agent.DBService import ExaMySQL, CreateValidMysqlSocketDir, \
                                   is_mysql_present, get_mysql_id, \
                                   get_value_from_mysql_init

from exabox.core.DBStore import get_db_version, ebInitDBLayer, \
                                ebShutdownDBLayer, ebGetDefaultDB


class ebDatabaseInstaller(ebGeneralInstaller):

    def __init__(self, aExacloudPath, aExaboxCfg, aDeploy, \
                 aInstallPort, aVerbose=False):

        super().__init__(aExacloudPath, aExaboxCfg, aVerbose)
        self.__install_port = aInstallPort
        self.__deploy = aDeploy

    #######################
    # GETTERS AND SETTERS #
    #######################

    def mIsDeploy(self):
        return self.__deploy

    def mSetDeploy(self, aValue):
        self.__deploy = aValue

    def mGetInstallPort(self):
        return self.__install_port

    def mSetInstallPort(self, aValue):
        self.__install_port = aValue

    #################
    # CLASS METHODS #
    #################

    def mInitDB(self, aCtx, aOptions):

        ebInitDBLayer(aCtx, aOptions)

        if get_db_version() == 3:
            ExaMySQL(self.mGetExaboxCfg()).mInit()

        _db = ebGetDefaultDB()
        _db.mCreateAgentTable()
        _db.mCreateAgentSignalTable()
        _db.mCreateRequestsTable()
        _db.mCreateRequestsArchiveTable()
        _db.mCreateWorkersTable()
        _db.mCreateClusterStatusTable()
        _db.mCreatePatchListTable()
        _db.mCreateIBFabricLocksTable()
        _db.mCreateIBFabricClusterTable()
        _db.mCreateIBFabricIBSwitchesTable()
        _db.mCreateClusterPatchOperationsTable()
        _db.mCreateInfraPatchingTimeStatsTable()
        _db.mCreateMockCallTable()
        _db.mCreateFilesTable('ecra_files')
        _db.mCreateFilesTable('exacloud_files')
        _db.mCreateScheduleTable()
        _db.mCreateScheduleArchiveTable()
        _db.mCreateExawatcherTable()
        _db.mCreateCCATable()
        _db.mCreateLocksTable()
        _db.mCreateErrCodeTable()
        _db.mCreateRunningDBsList()
        _db.mCreateAsyncProcessTable()
        _db.mCreateDataCacheTable()
        _db.mCreateExaKmsHistoryTable()
        _db.mCreateProfilerTable()

    def mGetEmptyMySQLSocket(self, aSocketPath, aMySQLId, aStep):

        _counter = int(aMySQLId)

        while self.mSocketInUse("{}/mysql_{}.sock".format(aSocketPath, _counter)):
            _counter += aStep

        return _counter

    def mInstall(self, aInstallPath):

        # Create Database Config files
        _installPath = os.path.abspath(aInstallPath)
        _exacloudPath = os.path.abspath(self.mGetExacloudPath())

        if get_db_version() == 1:

            _dbDir = "{}/sqlitedb/".format(_installPath)
            os.makedirs(_dbDir, exist_ok=True)

            self.mGetExaboxCfg()['db_dir'] = _dbDir

        elif get_db_version() == 3:

            _mysqlID = get_mysql_id()

            # Ensure MySQL is installed
            _socketPath = CreateValidMysqlSocketDir().mGetValidPath()

            if not is_mysql_present(os.path.join(_exacloudPath, "opt/mysql/init.cfg")):

                _cmd = "{0}/bin/mysql_installer.sh".format(_exacloudPath)
                _cmd += " -install {0} {1}".format(_mysqlID, _socketPath)

                _rc, _, _ = self.mExecuteLocal(_cmd)

                if _rc != 0:
                    raise Exception("ERROR: Could not install MySQL")

            # Now we obtain the port for
            _idFile = os.path.join(_exacloudPath, "opt/mysql/exatest_id.dat")

            if os.path.exists(_idFile):

                with open(_idFile, "r") as _f:
                    _mysqlID = int(_f.read())

                print("Already MYSQL: {0}".format(_mysqlID), flush=True)

            else:

                _mysqlID = self.mGetEmptyMySQLSocket(_socketPath, self.mGetInstallPort(), aStep=-1)
                if not is_mysql_present(os.path.join(_installPath, "init.cfg")):

                    _cmd = "{0}/bin/mysql_installer.sh".format(_exacloudPath)
                    _cmd += " -exatest {0} {1} {2}".format(_mysqlID, _socketPath, _installPath)

                    _rc, _, _ = self.mExecuteLocal(_cmd)
    
                    if _rc != 0:
                        raise Exception("ERROR: Could not create exatest MySQL files")

                if not self.mIsDeploy():

                    with open(_idFile, "w") as _f:
                        _f.write(str(_mysqlID))

                    print("Install MYSQL: {0}".format(_mysqlID), flush=True)

            self.mGetExaboxCfg()["mysql_id"] = _mysqlID
            self.mGetExaboxCfg()["mysql_config"] = os.path.join(_installPath, "mysql_conn.cfg")
            self.mGetExaboxCfg()["mysql_init"] = os.path.join(_installPath, "init.cfg")

        else:
            raise Exception("ERROR: DB not supported")

# End of file
