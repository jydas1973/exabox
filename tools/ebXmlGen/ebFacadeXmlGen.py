#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/tools/ebXmlGen/ebFacadeXmlGen.py /main/1 2021/02/15 07:53:35 jesandov Exp $
#
# ebFacadeXmlGen.py
#
# Copyright (c) 2021, Oracle and/or its affiliates. 
#
#    NAME
#      ebFacadeXmlGen.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      Facade as entry point to Generate XML
#
#    NOTES
#      Confluence: https://confluence.oraclecorp.com/confluence/x/D_xSq
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    01/13/21 - Creation
#

from exabox.tools.ebXmlGen.ebJsonCallbackGenerator import ebJsonCallbackGenerator
from exabox.tools.ebXmlGen.ebExacloudVanillaGenerator import ebExacloudVanillaGenerator

class ebFacadeXmlGen:

    def __init__(self, aUUID, aPayload, aSaveDir):

        self.__uuid = aUUID
        self.__payload = aPayload
        self.__savedir = aSaveDir

    def mGetUUID(self):
        return self.__uuid

    def mSetUUID(self, aValue):
        self.__uuid = aValue

    def mGetPayload(self):
        return self.__payload

    def mSetPayload(self, aValue):
        self.__payload = aValue

    def mGetSaveDir(self):
        return self.__savedir

    def mSetSaveDir(self, aValue):
        self.__savedir = aValue


    def mGenerateXml(self):
        """
        XML Generation Entry point

        This method first takes the ECRA Payload and calls the ebJsonCallbackGenerator
        The ebJsonCallbackGenerator result is passed to the ebExacloudVanillaGenerator
        the ebExacloudVanillaGenerator generate one exacloud XML with the ebJsonCallbackGenerator
        """

        # Execute xml_generator framework
        _callbackInfoGen = ebJsonCallbackGenerator(self.mGetUUID(), \
                                                   self.mGetPayload(), \
                                                   aSaveDir=self.mGetSaveDir())
        _callbackInfoGen.mExecute()

        _xmlGen = ebExacloudVanillaGenerator(self.mGetUUID(), \
                                             _callbackInfoGen.mGetCallbackInfo(), \
                                             aSaveDir=self.mGetSaveDir())
        _xmlGen.mExecute()

        _finalXML = "{0}/result-{1}.xml".format(self.mGetSaveDir(), self.mGetUUID())
        _xmlGen.mGetVanillaXML().mExportXml(_finalXML)

        return _finalXML


# end of file
