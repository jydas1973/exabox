"""
 Copyright (c) 2015, 2023, Oracle and/or its affiliates.

NAME:
    Execute Scripts

FUNCTION:
    Provide basic/core API for managing scripts (locally and remote)

NOTE:
    None

History:
    aararora    06/11/2023 - Bug 35926574: Correction of fortify reported issues for xml.
    jesandov    18/01/2022 - Remove exabox/os folder
    ndesanto    10/02/2019 - Enh 30374491: EXACC PYTHON 3 MIGRATION BATCH 02
    mirivier    02/03/2014 - Create file
"""

from __future__ import print_function

from exabox.log.LogMgr import ebLogError, ebLogDebug, ebLogInfo, ebLogWarn, ebLogCmd
import defusedxml.ElementTree as etree
from exabox.core.Context import get_gcontext
import sys, os, errno

gScriptsList=[]
gMajorFatal_FS_Error = [ errno.ENOSPC, errno.EROFS ]


class ebAction(object):

    def __init__(self,aScript):
        _se=aScript
        self.__prio   = _se.get('prio')
        self.__where  = _se.get('where')
        self.__shell  = _se.get('shell')
        self.__script = _se.get('script')
        self.__mode   = _se.get('mode')
        self.__cmd    = _se.text.strip()
        self.__singleNode = _se.get('singlenode')

    def mGetScript(self):
        return self.__script

    def mGetPrio(self):
        return self.__prio

    def mGetWhere(self):
        return self.__where

    def mGetMode(self):
        return self.__mode

    def mDumps(self):
        print('Action:',self.__prio, self.__where, self.__shell, self.__mode, self.__singleNode, '{'+self.__script+'}')

    def mGetCmd(self):
        return self.__cmd

    def mGetSingleNode(self):
        if self.__singleNode is None:
            return False
        _singleNode = self.__singleNode.lower()
        return True if _singleNode == 'true' else False

class ebScript(object):

    def __init__(self,aScript,aPath=None):
        _se=aScript
        self.__type  = _se.get('type')
        self.__when  = _se.get('when')
        self.__name  = _se.get('name')
        self.__where = _se.get('where')
        self.__desc  = _se.find('desc')
        if not self.__desc is None:
            self.__desc = self.__desc.text
        self.__action_list = []
        self.__scriptpath = aPath

    def mGetScriptPath(self):
        return self.__scriptpath

    def mAddAction(self,aAction):

        self.__action_list.append(aAction)

    def mFetchActions(self):

        _ad = {}
        for _a in self.__action_list:
            _ad[_a.mGetPrio()] = _a
        return _ad

    def mGetType(self):
        return self.__type

    def mGetWhen(self):
        return self.__when

    def mGetName(self):
        return self.__name

    def mDumps(self):

        print('Script:',self.__type, self.__when, self.__where, self.__name)
        print('Desc:', self.__desc)
        for _action in self.__action_list:
                _action.mDumps()

class ebScripts(object):

    def __init__(self, aScriptName=None):

        self.__script_name = aScriptName
        self.__ctx         = get_gcontext()
        self.__basepath    = self.__ctx.mGetBasePath()
        self.__root        = None
        self.__scripts = []

        _config = get_gcontext().mGetConfigOptions()
        if 'script_paths' in list(_config.keys()):
            self.__paths = _config['script_paths']
        else:
            self.__path = ['.']

        self.__fileio = ebIOFile(self.__script_name, self.__paths)
        self.__fileio.mOpenFile()
        self.__script_path = self.__fileio.mGetFilePath()
        _data = self.__fileio.mReadFile()
        if not _data:
            ebLogError('ebScripts: Fatal Error could not open XM config file: ' + self.__script_name)
            return

        # Below is changed to use defusedxml library instead of xml library to avoid XML security
        # vulnerability according to https://codeql.github.com/codeql-query-help/python/py-xxe/
        self.__root = etree.fromstring(_data)
        self.__fileio.mCloseFile()

        self.mParseScript()

    def mFetchScript(self,aType=None,aWhen=None):

        _script_list = []
        for _script in self.__scripts:

            if (_script.mGetType() == aType or aType=='*') and (_script.mGetWhen() == aWhen or aWhen=='*'):
                _script_list.append(_script)

        return _script_list

    def mParseScript(self):

        for _script in self.mGetConfigAllElement('script'):
            _so = ebScript(_script,self.mGetScriptsPath())
            for _action in _script.findall('action'):
                _sa = ebAction(_action)
                _so.mAddAction(_sa)
            self.__scripts.append(_so)

    def mDumps(self):

        for _script in self.__scripts:
            _script.mDumps()

    def mGetScriptsName(self):
        return self.__script_name

    def mGetScriptsPath(self):
        return self.__script_path

    def mDumpConfig(self):
        print(etree.tostring(self.__root).decode('utf8'))

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

    def mWriteScripts(self, aConfigPath):

        conf = etree.tostring(self.__root, method="xml").decode('utf8')
        conf = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +'\n'+conf
        fd = open(aConfigPath,"w")
        fd.write(conf)
        fd.close()

    def mSetConfigElementText(self, aPath, aValue):
        self.__root.find(aPath).text=aValue

def ebScriptsEngineInit(aScriptPaths):

    global gScriptsList

    _scripts_list=[]
    for scripts in os.listdir(aScriptPaths):
        if scripts[-4:] == '.xml':
            _scripts_list.append(ebScripts(scripts))

    gScriptsList=_scripts_list

    ebScriptsEngineFetch(aType='internal',aWhen='post.db_install')
    ebScriptsEngineFetch(aType='internal',aWhen='pre.db_install')
    ebScriptsEngineFetch(aType='internal',aWhen='post.gi_install')
    ebScriptsEngineFetch(aType='internal',aWhen='pre.gi_install')
    ebScriptsEngineFetch(aType='internal',aWhen='pre.vm_install')

def ebScriptsEngineFetch(aType=None,aWhen=None):

    global gScriptsList
    _sl=[]
    for _scripts in gScriptsList:
        _sl.append(_scripts.mFetchScript(aType,aWhen))

    return _sl

class ebIOFile(object):

    def __init__(self, aFile=None, aPaths=None):

        self.__filename = aFile
        self.__fd = None
        self.__paths = aPaths
        if self.__paths == None or self.__paths == []:
            self.paths = ['.']
        self.__filepath = None

    def mOpenFile(self, aFile=None, aMode=None):


        if aMode:
            raise 'TODO'

        if not aFile and not self.__filename:
            ebLogError('ebFileIO: Filename not provided/available')
            return None

        # Check if filename is absolute or relative filename
        # TODO: Support remote file

        if aFile:
            self.__filename = aFile

        _filename = None
        if not self.__filename[0] == '/':
            for _path in self.__paths:

                _filename = _path + '/' + self.__filename
                _found = False
                try:
                    os.lstat(_filename)
                    _found = True
                except (IOError, OSError) as e:
                    if e.errno in gMajorFatal_FS_Error:
                        ebLogError('ebFileIO: Exception catched during OpenFile (LStat)')
                except:
                    # TODO: Raise Exception
                    pass
                if _found:
                    break
            if not _found:
                ebLogError('ebFileIO: File: ' + self.__filename + ' not found in : ' + str(self.__paths))
                return None
        else:
            _filename = self.__filename

        try:
            self.__fd = open(_filename)
        except (IOError, OSError) as e:
            if e.errno in gMajorFatal_FS_Error:
                ebLogError('ebFileIO: Exception catched during OpenFile (Open): ' + self.__filename)
            else:
                ebLogWarn('ebFileIO: Failed to OpenFile (Open): ' + _filename)
        except:
            # TODO: Raise Exception
            pass

        self.__filepath = _filename

        return self.__fd

    def mGetFilePath(self):
        if not self.__fd:
            ebLogWarn('ebFileIO: FilePath has not been computed yet (e.g. None)!')
        return self.__filepath

    def mReadFile(self):

        if self.__fd:
            try:
                return self.__fd.read()
            except (IOError, OSError) as e:
                if e.errno in gMajorFatal_FS_Error:
                    ebLogError('ebFileIO: Exception catched during ReadFile: ' + self.__filepath)
            except:
                # TODO: Raise Exception
                pass

    def mWriteFile(self, aData):

        if self.__fd:
            try:
                self.__fd.write(aData)
            except (IOError, OSError) as e:
                if e.errno in gMajorFatal_FS_Error:
                    ebLogError('ebFileIO: Exception catched during WriteFile: ' + self.__filepath)
            except:
                # TODO: Raise Exception
                pass

    def mCloseFile(self):

        if self.__fd:
            self.__fd.close()
            self.__fd = None

