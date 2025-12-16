"""
 Copyright (c) 2015, 2023, Oracle and/or its affiliates.

NAME:
    Handle VM configuration files (including OEDA/Ocmd files)

FUNCTION:
    Provide basic/core API for managing Exadata VM configuration files

NOTE:
    None

History:
    aararora    11/06/2023 - Bug 35926574: Correction of fortify reported issues for xml.
    rajsag      07/29/2022 - Bug 33989470 cpu resize failing due to error in parsing of vm.cfg file 
    ndesanto    10/02/2019 - Enh 30374491: EXACC PYTHON 3 MIGRATION BATCH 02
    hnvenkat    04/04/2018 - Add support for CLOUDBASE type XML files
    mirivier    01/06/2014 - Create file
"""

from __future__ import print_function

from exabox.log.LogMgr import ebLogError, ebLogDebug, ebLogInfo, ebLogWarn
from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
import defusedxml.ElementTree as etree
from exabox.core.Context import get_gcontext
from exabox.core.DBStore import ebGetDefaultDB, get_db_version

import six
import re
import os
import sys
import re

#
# OVS VM Configuration object/file
#
class ebVMCfg(object):

    def __init__(self, aCtx, aVMName = None, aConfigData = None):

        self.__ctx    = aCtx
        self.__data   = aConfigData
        self.__vmname = aVMName
        self.__config   = None
        self.__dConfig  = None
        self.__configpath = None

        if self.__data:
            self.mParseConfig(self.__data)

    def mParseConfig(self, aConfigData=None):

        if self.__config:
            ebLogWarn('OVS VM Configuration for :' + self.__vmname + ' already available/parsed')
            return

        if not aConfigData and self.__data:
            aConfigData = self.__data
        if not aConfigData:
            ebLogWarn('OVS VM Configuration data not provided parsing failed')

        self.mParse()

    #
    # Helper function for mParse
    #
    def mPrune(self, buffer, idx):

        try:
            while buffer[ idx ] in ( ' ', '\t', '\r', '\n' ):
                idx = idx + 1
        except:
            pass
        return idx

    #
    # Parse OVS vm.cfg raw data and build __config and __dconfig
    #
    def mParse(self, aData=None, aConfig=None):

        if aData:
            buffer = aData
        else:
            buffer = self.__data

        if not aConfig:
            if self.__config:
                ebLogWarn('OVS VM config already present - current parsing will overwrite the existing one')
            self.__config = {}
            aConfig = self.__config

        if not buffer:
            ebLogWarn('No data or dict. provided to OVS OVM config parser')
            return

        idx  = 0
        curr = ''
        line = 0

        while len(buffer) >= idx:

            cmt = ''
            idx = self.mPrune( buffer, idx )

            # Parsed everything that had to be *break free*
            if idx == len(buffer):
                break

            while len(buffer) > idx and buffer[ idx ] == '#':
                cmt = ''
                while len(buffer) > idx and buffer[ idx ] not in ('\r', '\n'):
                    cmt = cmt + buffer[ idx ]
                    idx  = idx + 1
                # print line, 'cmt:', cmt
                aConfig[ line ] = [ 0, 0, cmt ]
                line = line + 1
                idx = self.mPrune( buffer, idx )

            key = ''
            while len(buffer) > idx and buffer[ idx ] != '=':
                key = key + buffer[ idx ]
                idx = idx + 1

            # Fix key
            key = key.rstrip()

            # Skip '='
            idx = idx + 1

            value = ''
            idx = self.mPrune( buffer, idx )
            countA = 0
            countB = 0
            cmt    = ''
            while len(buffer) > idx and buffer[ idx ] not in ( '\r', '\n') or countA != 0 or countB != 0:

                if buffer[ idx ] == '#' and not countA and not countB:
                    while len(buffer) > idx and buffer[ idx ] == '#':
                        cmt = ''
                        while len(buffer) > idx and buffer[ idx ] not in ('\r', '\n'):
                            cmt = cmt + buffer[ idx ]
                            idx  = idx + 1
                        # print 'cmt:', cmt
                        idx = self.mPrune( buffer, idx )
                    if not countA and not countB:
                        break

                if buffer[ idx ] == '[':
                    countA = countA + 1
                if buffer[ idx ] == '{':
                    countB = countB + 1
                if buffer[ idx ] == ']':
                    countA = countA - 1
                if buffer[ idx ] == '}':
                    countB = countB - 1
                value = value + buffer[ idx ]
                idx   = idx + 1
            aConfig[ line ] = [ key, value, cmt ]
            line = line + 1
            idx = self.mPrune( buffer, idx )

        # Build DictConfig
        self.__dConfig = self.mDictConfig()
        self.__lastline = line

    def mDumpConfig(self):

        aConfig = self.__config
        for e in aConfig:
            if aConfig[ e ][ 0 ] == 0:
                ebLogInfo(str(e) + ' | ' + aConfig[e][2])
            else:
                ebLogInfo(str(e) + ' : ' + aConfig[e][0] + ' = ' + aConfig[e][1] + ' ' + aConfig[e][2])

    def mRawConfig(self):

        data = ''
        aConfig = self.__config
        for e in aConfig:
            if aConfig[ e ][ 0 ] == 0:
                data = data + aConfig[ e ][ 2 ] + '\n'
            else:
                data = data + aConfig[ e ][ 0 ] +' = '+ aConfig[ e ][ 1 ] +' '+ aConfig[ e ][ 2 ] +'\n'
        return data

    def mDumpDictConfig(self):

        for e in list(self.__dConfig.keys()):
            ebLogInfo(e + ' ' + str(self.__dConfig[e]))

    def mDictConfig(self):

        aConfig = self.__config
        dConfig = {}
        for e in aConfig:
            if aConfig[ e ][ 0 ] == 0:
                    pass
            else:
                # dict[ key ] = [ line, value, comment ]
                dConfig[ aConfig[ e ][ 0 ] ] = [ e, aConfig[ e ][ 1 ], aConfig[ e ][ 2 ] ]
        return dConfig

    def mGetValue(self, aKey):

        if not self.__dConfig:
            ebLogWarn('OVS VM config not available to fetch value for key: ' + aKey)
            return
        return self.__dConfig[ aKey ][1]

    def mSetValue(self, aKey, aValue):

        if not self.__dConfig:
            ebLogWarn('OVS VM config not available to set value for key: ' + aKey)
            return
        if aKey not in list(self.__dConfig.keys()):
            ebLogInfo('Adding new key: ' + aKey)
            self.mAddKeyValue(aKey, aValue)
            return
        if type(aValue) not in [ type(""), type(u"") ]:
            ebLogWarn('OVS VM config incorrect value type:' + str(type(aValue)) + ' - enforcing string')
            aValue = str(aValue)

        # Patch/Set both config dict config
        self.__dConfig[ aKey ][1] = aValue
        self.__config[ self.__dConfig[ aKey ][ 0 ] ][1] = str(aValue)

    def mAddKeyValue(self, aKey, aValue, aComment=''):

        if not aKey or not aValue:
            ebLogWarn('OVS VM config key or value not provided to AddKeyValue method')
            return
        if type(aValue) not in [type(""), type(u"")]:
            ebLogWarn('OVS VM config incorrect value type:' + str(type(aValue)) + ' - enforcing string')
            aValue = str(aValue)
        self.__config[ self.__lastline ] = [ aKey, aValue, aComment ]
        self.__dConfig[ aKey ] = [ self.__lastline, aValue, aComment ]
        self.__lastline = self.__lastline + 1

    def mDelKey(self, aKey):

        # TBD
        pass

    def mSaveConfig(self, aConfigPath):

        """

        :param aConfigPath: Path and Filname used to the local vm.cfg
        """
        self.__configpath = aConfigPath

        aConfig = self.__config
        data = ''
        for e in aConfig:
            if aConfig[ e ][ 0 ] == 0:
                data = data + aConfig[ e ][ 2 ] +'\n'
            else:
                data = data + aConfig[ e ][ 0 ] +' = '+ aConfig[ e ][ 1 ] +' '+ aConfig[ e ][ 2 ] + '\n'
        # Write configuration file to disk
        f = open(aConfigPath, "w")
        f.write( data )
        f.close()

#
# XML Config Object
#
class exaBoxXMLConfig(object):

    def __init__(self, aCtx, aConfigName = None, aInlineData = None):

        # Add default .pkg extension if not provided (skip shell scripts).
        if aConfigName.rfind('.xml') == -1:
            aPackageName = aConfigName + '.pkg'

        self.__cfgname = aConfigName
        self.__ctx     = aCtx
        self.__basepath = get_gcontext().mGetBasePath()
        self.__root = None

        _config = get_gcontext().mGetConfigOptions()
        if 'exadata_config' in list(_config.keys()):
            self.__paths =  _config['exadata_config']
        else:
            self.__paths = ['.']

        self.__cfgpath = self.__cfgname

        data = None
        if aInlineData:
            data = aInlineData
        elif get_db_version() == 2:
            #Isolate this to Oracle as only Oracle have an implementation
            #of mReadFile which is not a simple fileSystem read
            _db = ebGetDefaultDB()            
            data = _db.mReadFile(self.__cfgname, 'ecra_files')
        else:
            with open(self.__cfgname) as _xmlfile:
                data = _xmlfile.read()
        if not data:
            ebLogError('ebXMLConfig: Fatal Error could not open XM config file: ' + self.__cfgname)
            return
        # Below is changed to use defusedxml library instead of xml library to avoid XML security
        # vulnerability according to https://codeql.github.com/codeql-query-help/python/py-xxe/
        self.__root = etree.fromstring(re.sub('xmlns="\w*"', '', data))

        # Check xml filetype to be PAAS or Vswitch
        if self.__root.attrib.get('filetype') is not None and not self.__root.attrib['filetype'] in ['PAAS', 'Vswitch', 'CLOUDBASE']:
            msg = 'Cluster XML {0} has not been generated in PAAS or Vswitch mode and can not be processed.'.format(self.__cfgname)
            raise ExacloudRuntimeError(0x0106, 0xA, msg, aStackTrace=False)

    def mGetConfigName(self):
        return self.__cfgname

    def mGetConfigPath(self):
        return self.__cfgpath

    def mDumpConfig(self):
        print(six.ensure_text(etree.tostring(self.__root)))

    def mConfigRoot(self):
        return self.__root

    def mGetConfigElement(self, aPath):

        elt = self.__root.find(aPath)
        if elt == None:
            return None
        else:
            return elt

    def mGetConfigAllElement(self, aPath):

        elt = self.__root.findall(aPath)
        if elt == None:
            return None
        else:
            return elt

    def mGetConfigElementText(self, aPath):

        elt = self.__root.find(aPath)
        if elt == None:
            return None
        else:
            return elt.text

    def mGetConfigXMLData(self):

        _conf = six.ensure_text(etree.tostring(self.__root, method="xml"))
        _conf = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +'\n'+_conf
        return _conf

    def mWriteConfig(self, aConfigPath):

        conf = six.ensure_text(etree.tostring(self.__root, method="xml"))
        conf = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +'\n'+conf
        fd = open(aConfigPath,"w+")
        fd.write(conf)
        fd.close()

    def mSetConfigElementText(self, aPath, aValue):
        self.__root.find(aPath).text=aValue

#
# OEDA VM Configuration object/file
#
class exaBoxVMConfig(exaBoxXMLConfig):

    def __init__(self, aCtx, aConfigName = None, aInlineData=None):
        super(exaBoxVMConfig,self).__init__(aCtx, aConfigName, aInlineData)

    def mInstallVMs(self):
        pass
#
# OEDA Cluster Configuration object/file
#
class exaBoxClusterConfig(exaBoxXMLConfig):

    def __init__(self, aCtx, aConfigName = None, aInlineData=None):
        super(exaBoxClusterConfig,self).__init__(aCtx, aConfigName, aInlineData)

    def mInstallCluster(self):
        pass
