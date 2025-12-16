"""

 $Header: 

 Copyright (c) 2018, 2025, Oracle and/or its affiliates.

 NAME:
      ebTestClucontrol.py - Base class for unittesting

 DESCRIPTION:
      Base class for unittesting

 NOTES:
      None

 History:

       MODIFIED (MM/DD/YY)
       gparada  02/10/25 - 37569998 New param in mGetRegexCell for better test
       gparada  06/22/23 - 35213979 Override workers, adding typing
       gparada  05/23/23 - 35098923 New param to mGetRegexDom0 for better handling
       jfsaldan 11/14/22 - Bug 33993510 - CELLDISKS RECREATED AFTER DBSYSTEM
                           TERMINATION (FIXING UNITTEST REGEX)
       aypaul   01/11/22 - Bug#33738885 Fixing population of mock status for
                           local node object.
       aypaul   12/05/21 - Enh33638849 Support elastic cases with Unit testing.

        jesandov    10/14/19 - Creation of the file for xmlpatching
        aypaul      07/22/21 - Bug#33057521 Adding unit tests for healthcheck.py
"""

import unittest
import os
import sys
import copy
import shlex
import socket
import subprocess
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom

from random import shuffle

from exabox.exatest.common.ebExacloudUtil import ebExacloudUtil, ebJsonObject
from exabox.core.MockCommand import exaMockCommand
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogInfo
from exabox.tools.AttributeWrapper import wrapStrBytesFunctions

##############
# MAIN CLASS #
##############

class ebTestClucontrol(unittest.TestCase):

    def setUp(self):
        super().setUp()
        _method = getattr(self, self._testMethodName)
        ebLogInfo("{0} {1} {0}".format("@"*25, _method.__name__))

    @classmethod
    def setUpClass(self, aGenerateDatabase=False, \
                         aUseOeda=False, \
                         aUseAgent=False, \
                         aGenerateRemoteEC=False,
                         aResourceFolder=None,
                         isElasticOperation=None,
                         aEnableUTFlag=True):

        self.__is_elastic = False if isElasticOperation is None else True
        self.__path = aResourceFolder

        if not self.__path:

            _pathSelf = "{0}/{1}/".format(os.path.dirname(__file__), "resources")
            _pathChild = "{0}/{1}/".format(os.path.dirname(sys.argv[0]), "resources")

            if os.path.exists(_pathChild):
                self.__path = _pathChild

            else:
                self.__path = _pathSelf

        self.__util = ebExacloudUtil(self.__path,
                                     aGenerateDatabase=aGenerateDatabase,
                                     aExatestAgent=aUseAgent,
                                     aUseOeda=aUseOeda,
                                     aGenerateRemoteEC=aGenerateRemoteEC,
                                     isElasticOperation=isElasticOperation)

        self.__clubox = self.__util.mPrepareEnviroment()
        if aUseOeda:
            self.__clubox.mSetOedaPath(self.__util.mGetOedaDir())

        if isElasticOperation is not None:
            _payload_required_path = os.path.join(self.__path,"{}_payload.json".format(isElasticOperation))
            if os.path.exists(_payload_required_path):
                _payload = self.__util.mReadJson(_payload_required_path)
            else:
                raise Exception("Elastic operation {} payload not available.".format(isElasticOperation))
        else:
            _payload = self.__util.mReadJson(self.__path + 'payload.json')

        self.__clubox.mSetUt(aEnableUTFlag)

        #Parse of the XML and init of enviroment variables
        self.__clubox.mParseXMLConfig(_payload)
        self.__clubox.mGetArgsOptions().jsonconf = _payload
        self.__clubox.mSetUUID("exatest")

    def mSetIsElatic(self, aBool):
        self.__is_elastic = aBool

    def mGetPath(self):
        return self.__path

    def mSetPath(self, aValue):
        self.__path = aValue

    def mGetRegexCell(self, aSeqNo:str=None):
        if self.__is_elastic:
            return ".*exdcl.*"
        if aSeqNo:
            return ".*[0-9]{1}celadm" + aSeqNo +"{1}.*"
        return ".*cel*"

    def mGetRegexDom0(self, aSeqNo:str=None) -> str:
        if self.__is_elastic:
            return ".*exdd0.*"
        if aSeqNo:
            return ".*[0-9]{1}adm" + aSeqNo +"{1}.*"
        return ".*[0-9]{1}adm[0-9]{1}.*"

    def mGetRegexDomU(self):
        if self.__is_elastic:
            return ".*exddu.*"
        return ".*[0-9]{1}vm[0-9]{1}.*"

    def mGetRegexVm(self):
        if self.__is_elastic:
            return ".*compexpn*."
        return ".*vm.*"

    def mGetRegexNatVm(self):
        return ".*nat.*"

    def mGetRegexSwitch(self):
        return ".*sw.*"

    def mGetRegexLocal(self):
        return "(.*{0}.*)|({1}.*)".format(socket.gethostname(), "local")

    def mGetUtil(self) -> ebExacloudUtil:
        return self.__util

    def mGetClubox(self):
        return self.__clubox

    def mGetPayload(self):
        return self.mGetResourcesJsonFile("payload.json")

    def mGetConfig(self):
        return self.mGetResourcesJsonFile("config.json")

    def mGetResourcesJsonFile(self, aFilename):
        _content = self.__util.mReadJson(self.__path + aFilename)
        return _content

    def mGetResourcesTextFile(self, aFilename):
        _content = None
        with open(self.__path + aFilename, "r") as _f:
            _content = _f.read()
        return _content

    def mGetContext(self):
        return self.__util.mGetLastContext()

    def mPrepareMockCommands(self, aMock):

        # Reconnect local node
        self.mGetClubox().mGetLocalNode().mDisconnect()
        self.mGetClubox().mGetLocalNode().mConnect()
        self.mGetClubox().mGetLocalNode().mSetMockMode(True)

        self.mGetContext().mGetArgsOptions()['mock_cmds'] = aMock
        self.mGetContext().mGetArgsOptions()['mock_cmds_instances'] = {}

    @staticmethod
    def mRealExecute(aCmd, aStdIn):

        _cmd = aCmd
        if _cmd.startswith("/bin/scp"):
            _cmd = _cmd.replace("/bin/scp", "/bin/cp")

        _args = shlex.split(_cmd)

        _proc = subprocess.Popen(
            _args, \
            stdin=subprocess.PIPE, \
            stdout=subprocess.PIPE, \
            stderr=subprocess.PIPE \
        )

        _stdout, _stderr = wrapStrBytesFunctions(_proc).communicate()
        _rc = _proc.returncode

        return _rc, _stdout, _stderr



# end file
