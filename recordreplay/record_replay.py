"""
$Header:

 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    Record and Replay - functionality

FUNCTION:
    Provide API to record and replay the provisioning

"""

import copy
from functools import wraps
from exabox.log.LogMgr import ebLogDebug
from exabox.tools.AttributeWrapper import wrapStrBytesFunctions
from io import StringIO
import traceback
import shutil
import time
import os
import hashlib
import re
from enum import Enum



class Mode(Enum):
    NORMAL = 0
    RECORD = 1
    REPLAY = 2


class ebRecordReplay:
  
    clusterName = None
    taskUuid = None
    operMode = Mode.NORMAL
    commandExitStatus = 0
    pingCmdExitStatus = 0
    repositoryRoot = ""
    basePath = ""
    recordFolder = "" 
    maxKeyLength = 580
    lastMExecuteCmd = None

    @staticmethod 
    def mInitRecordReplay(mode:str,uuid:str,clusterName:str,repoRoot:str,basePath:str):
        """
        This function initializes the global variables and creates a table which will 
        be used to record. In case of replay, recorded mysql file imported into this table  
        This function gets called at every command execution
        """

        if mode == "RECORD":
            ebRecordReplay.operMode = Mode.RECORD
        elif mode == "REPLAY":
            ebRecordReplay.operMode = Mode.REPLAY
        else:
            ebRecordReplay.operMode = Mode.NORMAL
            return 
        if clusterName is None:
            raise Exception("Record Replay Failed, cluster name None")
        ebRecordReplay.taskUuid = uuid
        ebRecordReplay.clusterName = clusterName
        ebRecordReplay.repositoryRoot = repoRoot
        ebRecordReplay.basePath = basePath
        ebRecordReplay.recordFolder = "{0}/Record_bundle_{1}/".format(ebRecordReplay.basePath,ebRecordReplay.clusterName)
        ebRecordReplay.tableName = "{0}_record_replay".format(ebRecordReplay.clusterName)
        try:
            ret = ebRecordReplay.mCreateClusterRecRepTable()
            ebRecordReplay.mRemoveReadCountColumn()
            if ebRecordReplay.operMode is Mode.REPLAY:
                ebRecordReplay.mImportRecordReplayTable()
                ebRecordReplay.mAddReadCountColumn()
        except Exception as e:
            ebLogDebug('*** Record Table Creation/Import failed failed for cluster {0} with exp {1}'.format(ebRecordReplay.clusterName,str(e)))
            raise


    @staticmethod 
    def mCreateClusterRecRepTable():
        """
        This function checks the record table exist or not. If not exist, it creates the record table 
        """ 
        from exabox.core.DBStore import ebGetDefaultDB
        db = ebGetDefaultDB()
        if not db.mCheckTableExist("record_replay"): 
            st = '''CREATE TABLE record_replay (cmd_name VARCHAR(650) PRIMARY KEY, 
                                                cmd_output TEXT, 
                                                occurrence TEXT,
                                                cluster_name TEXT,
                                                cmd_exit_status TEXT)'''
            db.mExecute(st)
            return True
        return False
        """
        record_replay fields:
            0. cmd_name
            1. cmd_output
            2. occurrence
            3. cluster_name 
            4. cmd_exit_status
        """

    @staticmethod 
    def mAddReadCountColumn():
        """
        This function checks the record table exist or not. If not exist, it creates the record table 
        """ 
        from exabox.core.DBStore import ebGetDefaultDB
        db = ebGetDefaultDB()
        if db.mCheckTableExist("record_replay"): 
            st = '''ALTER TABLE record_replay ADD COLUMN read_count INT DEFAULT 0 AFTER cmd_exit_status'''
            db.mExecute(st)
        """
        record_replay fields:
            0. cmd_name
            1. cmd_output
            2. occurrence
            3. cluster_name 
            4. cmd_exit_status
            5. read_count
        """

    @staticmethod 
    def mRemoveReadCountColumn():
        """
        This function checks the record table exist or not. If not exist, it creates the record table 
        """ 
        from exabox.core.DBStore import ebGetDefaultDB
        try:
            db = ebGetDefaultDB()
            if db.mCheckTableExist("record_replay"): 
                st = '''ALTER TABLE record_replay DROP COLUMN read_count'''
                db.mExecute(st)
        except Exception as e:
            ebLogDebug("*** Exception during remove read_column  {0}".format(str(e)))


    @staticmethod 
    def mInsertCmdRec(cmdName:str, cmdOutput:str, occurrence = str(1), cmdExitStatus = str(0)):
        """
        This function is used to insert cmd record into the table.
        """  
        from exabox.core.DBStore import ebGetDefaultDB
        db = ebGetDefaultDB()

        sqlQuery = "INSERT INTO record_replay VALUES (%(1)s, %(2)s, %(3)s, %(4)s, %(5)s)"
        data = [cmdName, cmdOutput, occurrence,ebRecordReplay.clusterName, cmdExitStatus]
        db.mExecute(sqlQuery, data)


    @staticmethod 
    def mUpdateCmdOccCount(cmdName:str,occurrence:str):
        """
        This function is used to update cmd record into the table.
        """ 

        from exabox.core.DBStore import ebGetDefaultDB
        db = ebGetDefaultDB()

        sql = "UPDATE record_replay SET occurrence=%(1)s WHERE cmd_name=%(2)s"
        data = [occurrence, cmdName]
        db.mExecuteLog(sql, data)

    @staticmethod 
    def mUpdateCmdReadCount(cmdName:str,read_count:int):
        """
        This function is used to update cmd record into the table.
        """ 

        from exabox.core.DBStore import ebGetDefaultDB
        db = ebGetDefaultDB()

        sql = "UPDATE record_replay SET read_count=%(1)s WHERE cmd_name=%(2)s"
        data = [read_count, cmdName]
        db.mExecuteLog(sql, data)


    @staticmethod 
    def mGetRecordByCmd(cmdName:str):
        """
        This function is used to get the record using the key command.
        """ 

        from exabox.core.DBStore import ebGetDefaultDB
        db = ebGetDefaultDB()
        sqlQuery = "SELECT * FROM record_replay WHERE cmd_name=%(1)s"
        data = [cmdName]
        rc = db.mFetchOne(sqlQuery,data)
        return rc

    @staticmethod 
    def mGetRecordByCmdLike(cmdName:str):
        """
        This function is used to get the record using "like"  keyword cmd from the table.
        """ 
        from exabox.core.DBStore import ebGetDefaultDB
        db = ebGetDefaultDB()
        sqlQuery = "SELECT * FROM record_replay WHERE cmd_name like %(1)s"
        data = [cmdName]
        rc = db.mFetchOne(sqlQuery,data)
        return rc


    @staticmethod 
    def mExportRecordReplayTable() -> str:
        """
        This function is used to export the recorded  table into a file format mysql dump,which will be used at replay.
        """ 
        from exabox.core.DBStore import ebGetDefaultDB
        db = ebGetDefaultDB()
        sql = "SELECT @@secure_file_priv"
        mySqlFileLoc = None
        fileName = ""
        fileList = db.mFetchOne(sql)
        if fileList is not None:
            mySqlFileLoc = str(fileList[0])
            fileName = os.path.join(mySqlFileLoc, ebRecordReplay.tableName)
            if os.path.isfile(fileName):
                os.remove(fileName)
            sql1 = "SELECT * FROM record_replay WHERE cluster_name=%(1)s INTO OUTFILE %(2)s FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n'"
            data = [ebRecordReplay.clusterName,fileName]
            db.mExecuteLog(sql1,data)
        return fileName

    @staticmethod 
    def mImportRecordReplayTable():
        """
        This function is used to import the mysql file dump into table and will be used at replay.
        """ 
        from exabox.core.DBStore import ebGetDefaultDB
        db = ebGetDefaultDB()
        sql = "SELECT @@secure_file_priv"
        importTableFromLoc = None
        fileList = db.mFetchOne(sql)
        srcDBTableLoc = ebRecordReplay.recordFolder
        if fileList is not None:
            importTableFromLoc = str(fileList[0])
            srcDBTableLoc = os.path.join(srcDBTableLoc,ebRecordReplay.tableName)
            destfile = os.path.join(importTableFromLoc, ebRecordReplay.tableName)
            shutil.copy(srcDBTableLoc, destfile)
            sql1 = "LOAD DATA INFILE %(1)s REPLACE INTO TABLE record_replay FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n'"
            data = [destfile]
            db.mExecuteLog(sql1,data)


    @staticmethod 
    def mExportRecordedTable():
        """
        This function is an util function for exporting the recorded table into mysql file. 
        This function gets called at every command execution 
        """

        from exabox.core.DBStore import ebGetDefaultDB
        try:
            db = ebGetDefaultDB()
            recordedDbFile = ebRecordReplay.mExportRecordReplayTable()
            if recordedDbFile:
                fileName = os.path.basename(recordedDbFile)
                recordDestPath = os.path.join(ebRecordReplay.recordFolder,fileName)
                if not os.path.exists(ebRecordReplay.recordFolder):
                    os.mkdir(ebRecordReplay.recordFolder)
                if os.path.exists(recordDestPath):
                    os.remove(recordDestPath)
                shutil.copy2(recordedDbFile, recordDestPath)
                ebLogDebug('*** Recorded Table Exported for cluster {0} at  {1}'.format(ebRecordReplay.clusterName, recordDestPath))
            else:
                ebLogDebug('*** Recorded Table Export failed for cluster {0}'.format(ebRecordReplay.clusterName))
        except Exception as e:
            ebLogDebug('*** Exception : Recorded Table Export failed for cluster {0} with error {1}'.format(ebRecordReplay.clusterName,str(e)))
        

    @staticmethod 
    def mCheckNoOutputCmd(cmdType:str) -> bool:
        """
        This function checks whether the command has output from the remote node or not. 
        """

        return cmdType in ["echo","rm","cp","/bin/echo","/bin/rm","/bin/cp"]

    @staticmethod 
    def mHandleBiggerCmd(cmd:str) -> str:
        """
        This function handles bigger command and reduces the size for specific commands.
        """
        cmd = cmd.split(" ")
        try:
            index = cmd.index("\"ssh-rsa")
            cmd = cmd[:index+1]
            cmd = " ".join(cmd)
            cmd = cmd + "\""
        except ValueError:
            cmd = " ".join(cmd)

        #Mysql table key size is fixed as 650.Due to some restrictions unable to increase.TBD 
        origCmd = cmd
        if len(cmd) > ebRecordReplay.maxKeyLength:
            ebLogDebug('RecRep: Key length is greater than MAX KEY LENGTH {0}. cmd {1}'.format(ebRecordReplay.maxKeyLength,cmd))
            hashcmd = hashlib.sha256(cmd.encode()) 
            cmd = hashcmd.hexdigest()
            ebLogDebug('mHandleBiggerCmd: command size reduced using sha256. command {0}. reduced command {1}'.format(origCmd,cmd))
        return cmd 

    @staticmethod 
    def mHandleSpecialReturnStatus(cmd:str):
        """
        This function is used to control the return status of commandExitStatus function.
        mCommandExitStatus function returns 0 by default in replay mode. As per the code flow
        if any other return values are expected, then that is controlled through this function. 
        """

        if cmd == "cat /etc/sysconfig/network | grep 'HOSTNAME' | grep '\.'":
            ebRecordReplay.commandExitStatus = -1


    @staticmethod 
    def mAppendCmdWithClustNameAndHostname(cmd:str,hostName:str) -> str:
        """
        This function appends the clustername and hostname with command and returns the command.
        Few operations are not guaranteed to happen on specific dom0, 
        because it is decided based on the load at the time of recording. So except 
        those all other commands are appended with hostname.
        """

        cmdListStartsWith = ("ssh-keygen -f","cat /tmp/","/bin/grep","cd /tmp/; chmod")
        if cmd.startswith(cmdListStartsWith) or cmd.find("mBeginParallelCopy") != -1:
            cmd = "{0}_{1}".format(ebRecordReplay.clusterName,cmd)
            return cmd
        else:
            cmd = "{0}_{1}_{2}".format(ebRecordReplay.clusterName,hostName.split('.')[0], cmd)
            return cmd

    @staticmethod 
    def mReturnCallStack(caller:str,cmd:str) -> str:
        """
        This function returns the full call stack. This will be used to append with command to make 
        the command unique 
        """

        _stack = traceback.format_stack()
        _call_stack = ""
        start = False
        for line in _stack:
            line = line.strip()
            func_name = line.split("in ")[1].split('\n')[0]
            full_line = "".join(line.split("in ")[1].split('\n'))
            if func_name == "main":
                start = True
            if start:
                _call_stack += func_name
                _call_stack += "_"
            if  full_line.find(caller) != -1:
                ebLogDebug('final call_stack  : {0}'.format(_call_stack))
                return _call_stack
        return _call_stack 

    @staticmethod 
    def mChecksumRepoUpdate(srcFile:str,targetFile:str,recordRepoRoot:str):
        """
        This function modifies the checksum.conf file according to replay repo path.
        This file gets generated at the time create service and it contais repo path 
        of the image and used in create service flow. This file copied into Record
        bundle while Recording and same file is changed with replay repo path and used 
        while replay create service.
        """

        ebLogDebug('mChecksumRepoUpdate called')
        newLines = []
        with open(srcFile,'r') as f:
            lines = f.readlines()
            newLines = [line.replace(recordRepoRoot,ebRecordReplay.repositoryRoot) for line in lines]
           
        with open(targetFile,'w+') as f: 
            f.writelines(newLines)

    @staticmethod 
    def mFindTimePattern(cmd:str) -> str:
        """
        This function finds any random time pattern present in the command
        and replaces withe generic pattern, so that record and replay matches
        """
        match = re.search(r'\d{10}\.\d{7}', cmd)
        if match is None:
            match = re.search(r'\d{10}\.\d{6}', cmd)
            if match is None:
                match = re.search(r'\d{10}\.\d{5}', cmd)
                if match is None:
                    match = re.search(r'\d{10}\.\d{4}', cmd)
        
        if match:
            timePattern = match.group()
            genTimePattern = "0000000000.0000000"
            cmd = cmd.replace(timePattern,genTimePattern)
            ebLogDebug("cmd after time pattern change {0}".format(cmd))
        return cmd

    @staticmethod 
    def mFindOEDARandomPattern(cmd:str) -> str:
        """
        This function finds any random generated uuid pattern present in the command
        If it finds the pattern, then it returns the uuid else returns empty string
        """
        matches = re.findall(r'\w{8}-\w{4}-\w{4}-\w{4}-\w{12}', cmd)
        uuidReplace = "00000000-0000-0000-0000-000000000000"
        for match in matches:
            cmd = cmd.replace(match,uuidReplace)

        xmlFileNameReplacePattern = "/0000000000000000000000000000000000000000000000000000000000000000_"
        pattern = '(/\w{64})_'
        match = re.search(pattern, cmd)
        if match:
            xmlFileNamePattern = match.group()
            cmd = cmd.replace(xmlFileNamePattern,xmlFileNameReplacePattern)
        return cmd


    @staticmethod 
    def mFindUuidPattern(cmd:str) -> str:
        """
        This function finds any random generated uuid pattern present in the command
        If it finds the pattern, then it returns the uuid else returns empty string
        """
        found = False
        match = re.search(r'\w{8}-\w{4}-\w{4}-\w{4}-\w{12}', cmd)
        if match:
            uuidPattern = match.group()
            return uuidPattern
        else:
            return ""

    @staticmethod 
    def mRecordExecuteLocal(callee, callerSelf, *args, **kwargs):
        """
        This function handles the recording of mExecuteLocal. It executes the command on the 
        real node and records the command, command output and occurrence count in the record table. 
        callee : Input : Function
        callerSelf : Input  : Callers Instance
        *args : Input : Input or callee
        **kargs : Input: Key value input for callee
        """

        from exabox.core.DBStore import ebGetDefaultDB
        cmd = args[0]
        ret, u, o, e = callee(callerSelf, *args, **kwargs)
        try:
            if cmd.startswith("/bin/ping -c") == False:
                return ret,u,o,e
            if ebRecordReplay.mCheckNoOutputCmd(cmd.split(" ")[0]):
                return ret,u,o,e
            outStr = copy.deepcopy(o)

            # Replace self uuid from command and command output 
            cmd = cmd.replace(ebRecordReplay.taskUuid,"uuid_str") 
            if outStr: 
                outStr = outStr.replace(ebRecordReplay.taskUuid,"uuid_str")
            #append call stack with command
            callStack = ebRecordReplay.mReturnCallStack(callee.__name__,cmd)
            cmd = callStack + cmd
 
            # replace any random uuid in comman and command output with fixed uuid pattern 
            uuidReplace = "00000000-0000-0000-0000-000000000000"
            uuidPattern = ebRecordReplay.mFindUuidPattern(cmd)
            if uuidPattern:
                cmd = cmd.replace(uuidPattern,uuidReplace)
            uuidPattern = None
            if outStr: 
                uuidPattern = ebRecordReplay.mFindUuidPattern(outStr)
            if uuidPattern:
                outStr = outStr.replace(uuidPattern,uuidReplace)
            cmd = ebRecordReplay.mFindTimePattern(cmd)
            ebLogDebug('mRecordExecuteLocal commmand {0} : OUTPUT from real Node : {1} return: {2}'.format(cmd,outStr,ret))
            #handle Bigger command
            cmd = ebRecordReplay.mHandleBiggerCmd(cmd)
            db = ebGetDefaultDB()
            rc = ebRecordReplay.mGetRecordByCmd(cmd)
            if rc is None :
                ebRecordReplay.mInsertCmdRec(cmd,str(outStr),occurrence = str(1), cmdExitStatus = str(ret))
            else:
                #update the occurrence count in master entry
                occ = int(rc[2]) + 1
                outStrDb = rc[1]
                ebRecordReplay.mUpdateCmdOccCount(cmd, str(occ))
                if outStrDb == str(outStr):
                    ebLogDebug('mExecuteCmdLocal: got same output for existing command, increased occurrence count')
                else:
                    ebLogDebug('mExecuteCmdLocal: got diff output for existing command, so new entry added with occurrence_number')
                    cmd = "{0}_{1}".format(cmd,str(occ))
                    ebRecordReplay.mInsertCmdRec(cmd, str(outStr), occurrence = str(1), cmdExitStatus = str(ret))
        except Exception as exp:
            ebLogDebug('Exception while DB recording {0} for cmd {1}'.format(str(exp),cmd))
        return ret,u,o,e

    @staticmethod
    def mReplayExecuteLocal(callee, callerSelf, *args, **kwargs):
        """
        This function handles the replay of mExecuteLocal. It fetches the record from table using 
        command as key and returns the command output if the entry exist. 
        callee : Input : Function
        callerSelf : Input  : Callers Instance
        *args : Input : Input or callee
        **kargs : Input: Key value input for callee
        """

        from exabox.core.DBStore import ebGetDefaultDB
        cmd = args[0]
        if cmd.startswith("/bin/ping -c") == False:
            return callee(callerSelf, *args, **kwargs)
          
        if ebRecordReplay.mCheckNoOutputCmd(cmd.split(" ")[0]):
            return 0,None,"",""
                    
        # replace self uuid in command
        cmd = cmd.replace(ebRecordReplay.taskUuid,"uuid_str")
        # Add Call stack with command
        ebLogDebug('mReplayExecuteLocal:callee name {0}'.format(callee.__name__)) 
        callStack = ebRecordReplay.mReturnCallStack(callee.__name__,cmd)
        ebLogDebug('mReplayExecuteLocal:call stack {0}'.format(callStack)) 
        cmd = callStack + cmd
        # find uuid pattern and replace with fixed pattern
        uuidPattern = ebRecordReplay.mFindUuidPattern(cmd)
        uuidReplace = "00000000-0000-0000-0000-000000000000"
        if uuidPattern:
            cmd = cmd.replace(uuidPattern,uuidReplace)
        cmd = ebRecordReplay.mFindTimePattern(cmd)
        # handle bigger command
        cmd = ebRecordReplay.mHandleBiggerCmd(cmd)
        try:
            db = ebGetDefaultDB()
            rc = ebRecordReplay.mGetRecordByCmd(cmd)
            if rc:
                # update command with occurrence count 
                read_count = int(rc[5]) + 1
                ebRecordReplay.mUpdateCmdReadCount(cmd,read_count)
                if read_count != 1:
                    cmdWithOcc = "{0}_{1}".format(cmd,str(read_count)) 
                    rcWithOcc = ebRecordReplay.mGetRecordByCmd(cmdWithOcc)
                    if rcWithOcc:
                        rc = rcWithOcc
            if rc is None :
                    raise Exception("mReplayExecuteLocal: DB entry missing for command {0}".format(cmd))
            if rc is not None:
                retVal = int(rc[4])
                output = rc[1]
                if output == "None":
                   output = None
                if uuidPattern and output:
                    output = output.replace(uuidReplace,uuidPattern)
                if output:
                    output = output.replace("uuid_str",ebRecordReplay.taskUuid)
                ebLogDebug('mReplayExecuteLocal OUTPUT from db: cmd {0} output {1} return {2}'.format(cmd,output,retVal))
                err = ""
                return retVal, None, output, err
        except Exception as e:
            ebLogDebug('Exception during fetch record : {0}'.format(str(e)))
            raise

    
    @staticmethod 
    def mRecordExecuteCmd(callee, callerSelf, *args, **kwargs):
        """
        This function handles the recording of mExecuteCmd. It executes the command on the 
        real node and records the command, command output and occurrence count in the record table. 
        callee : Input : Function
        callerSelf : Input  : Callers Instance
        *args : Input : Input or callee
        **kargs : Input: Key value input for callee
        """

        from exabox.core.DBStore import ebGetDefaultDB
        if type(callerSelf).__name__ == "exaBoxLocal":
            ebLogDebug('mExecuteCmd : exaBoxLocal: COMMAND: func:{0} - {1}'.format(callee.__name__,args[0]))
            return callee(callerSelf, *args, **kwargs)
        cmd = args[0]
        if callee.__name__ == "mExecuteCmd":
            u, o, e = callee(callerSelf, *args, **kwargs)
            outStr = o.read()
            oo = StringIO(outStr)
            if ebRecordReplay.mCheckNoOutputCmd(cmd.split(" ")[0]):
                return u,oo,e
        elif callee.__name__ == "mExecuteCmdLog":
            callee(callerSelf, *args, **kwargs)
            outStr = "None"
                
        try:
            # Replace self uuid from command and command output 
            cmd = cmd.replace(ebRecordReplay.taskUuid,"uuid_str") 
            outStr = outStr.replace(ebRecordReplay.taskUuid,"uuid_str")
        
            #append call stack with command
            callStack = ebRecordReplay.mReturnCallStack(callee.__name__,cmd)
            cmd = callStack + cmd
            #append hostname 
            cmd = ebRecordReplay.mAppendCmdWithClustNameAndHostname(cmd,callerSelf.mGetHost())
 
            # replace any random uuid in comman and command output with fixed uuid pattern 
            uuidReplace = "00000000-0000-0000-0000-000000000000"
            uuidPattern = ebRecordReplay.mFindUuidPattern(cmd)
            if uuidPattern:
                cmd = cmd.replace(uuidPattern,uuidReplace)
            uuidPattern = ebRecordReplay.mFindUuidPattern(outStr)
            if uuidPattern:
                outStr = outStr.replace(uuidPattern,uuidReplace)
            cmd = ebRecordReplay.mFindTimePattern(cmd)
            ebLogDebug('commmand {0} : OUTPUT from real Node : {1} exitstatus: {2}'.format(cmd,outStr,callerSelf.mGetCmdExitStatus()))
            #handle Bigger command
            cmd = ebRecordReplay.mHandleBiggerCmd(cmd)
            db = ebGetDefaultDB()
            rc = ebRecordReplay.mGetRecordByCmd(cmd)
            if rc is None :
                ebRecordReplay.mInsertCmdRec(cmd,outStr,occurrence = str(1), cmdExitStatus = str(callerSelf.mGetCmdExitStatus()))
            else:
                #update the occurrence count in master entry
                occ = int(rc[2]) + 1
                outStrDb = rc[1]
                cmdExitStatus = int(rc[4])
                ebRecordReplay.mUpdateCmdOccCount(cmd, str(occ))
                if outStrDb == outStr and cmdExitStatus == callerSelf.mGetCmdExitStatus():
                    ebLogDebug('mExecuteCmd: got same output for existing command, increased occurrence count')
                else:
                    ebLogDebug('mExecuteCmd: got diff output for existing command, so new entry added with occurrence_number')
                    cmd = "{0}_{1}".format(cmd,str(occ))
                    ebRecordReplay.mInsertCmdRec(cmd, outStr, occurrence = str(1), cmdExitStatus = str(callerSelf.mGetCmdExitStatus()))
        except Exception as exp:
            ebLogDebug('Exception while DB recording {0} for cmd {1}'.format(str(exp),cmd))
        if callee.__name__ == "mExecuteCmd":
            return u,oo,e

    @staticmethod 
    def mReplayExecuteCmd(callee, callerSelf, *args, **kwargs):
        """
        This function handles the replay of mExecuteCmd. It fetches the record from table using 
        command as key and returns the command output if the entry exist. 
        callee : Input : Function
        callerSelf : Input  : Callers Instance
        *args : Input : Input or callee
        **kargs : Input: Key value input for callee
        """

        from exabox.core.DBStore import ebGetDefaultDB
        cmd = args[0]
        if ("mExecuteCmd" == callee.__name__):
            if type(callerSelf).__name__ == "exaBoxLocal":
                cmd = args[0]
                if cmd.startswith("/bin/ping"):
                    ebRecordReplay.pingCmdExitStatus = 1
                    ebLogDebug('***** exaBoxLocal: PING COMMAND: func:{0} - {1}'.format(callee.__name__,args[0]))
                return callee(callerSelf, *args, **kwargs)
        #if no putout command return empty outputs
        if ebRecordReplay.mCheckNoOutputCmd(cmd.split(" ")[0]):
            i = StringIO("")
            e = StringIO("")
            oo = StringIO("")
            return i, oo, e
                    
        # replace self uuid in command
        cmd = cmd.replace(ebRecordReplay.taskUuid,"uuid_str")
        # Add Call stack with command 
        callStack = ebRecordReplay.mReturnCallStack(callee.__name__,cmd)
        cmd = callStack + cmd
        # Add hostname along with command
        cmd = ebRecordReplay.mAppendCmdWithClustNameAndHostname(cmd,callerSelf.mGetHost())
        # find uuid pattern and replace with fixed pattern
        uuidPattern = ebRecordReplay.mFindUuidPattern(cmd)
        uuidReplace = "00000000-0000-0000-0000-000000000000"
        if uuidPattern:
            cmd = cmd.replace(uuidPattern,uuidReplace)
        cmd = ebRecordReplay.mFindTimePattern(cmd)
        # handle bigger command
        cmd = ebRecordReplay.mHandleBiggerCmd(cmd)
        try:
            db = ebGetDefaultDB()
            rc = ebRecordReplay.mGetRecordByCmd(cmd)
            ebRecordReplay.lastMExecuteCmd = cmd
            if rc:
                # update command with occurrence count 
                read_count = int(rc[5]) + 1
                cmdExitStatus = int(rc[4])
                ebRecordReplay.mUpdateCmdReadCount(cmd,read_count)
                if read_count != 1:
                    cmdWithOcc = "{0}_{1}".format(cmd,str(read_count)) 
                    rcWithOcc = ebRecordReplay.mGetRecordByCmd(cmdWithOcc)
                    ebRecordReplay.lastMExecuteCmd = cmdWithOcc
                    cmdExitStatus = int(rc[4])
                    if rcWithOcc:
                        rc = rcWithOcc
            if rc is None :
                    raise Exception("mReplayExecuteCmd: DB entry missing for command {0}".format(cmd))
            if rc is not None:
                output = rc[1]
                if uuidPattern:
                    output = output.replace(uuidReplace,uuidPattern)
                output = output.replace("uuid_str",ebRecordReplay.taskUuid)
                ebLogDebug('OUTPUT from db: cmd {0} output {1} exitStatus {2}'.format(cmd,output,cmdExitStatus))
                if callee.__name__ == "mExecuteCmd":
                    oo = StringIO(output)
                    i = StringIO("")
                    e = StringIO("")
                    return i, oo, e
        except Exception as e:
            ebLogDebug('Exception during fetch record : {0}'.format(str(e)))
            raise


    @staticmethod 
    def mRecordFileExists(callee, callerSelf, *args, **kwargs):
        """
        This function handles the recording of record_mFileExists. It records the file name, 
        output from remote node and occurrence count in the record table. 
        callee : Input : Function
        callerSelf : Input  : Callers Instance
        *args : Input : Input or callee
        **kargs : Input: Key value input for callee
        """

        result = callee(callerSelf, *args, **kwargs)
        from exabox.core.DBStore import ebGetDefaultDB
        db = ebGetDefaultDB()
        cmd = args[0]
        try:
            # Replace self uuid from command and command output 
            cmd = cmd.replace(ebRecordReplay.taskUuid,"uuid_str")
            #append call stack with command
            callStack = ebRecordReplay.mReturnCallStack(callee.__name__,cmd)
            cmd = callStack + cmd
            #append hostname 
            cmd = ebRecordReplay.mAppendCmdWithClustNameAndHostname(cmd,callerSelf.mGetHost())
            #handle Bigger command
            cmd = ebRecordReplay.mFindTimePattern(cmd)
            cmd = ebRecordReplay.mHandleBiggerCmd(cmd)
            rc = ebRecordReplay.mGetRecordByCmd(cmd)
            if rc is None :
                ebRecordReplay.mInsertCmdRec(cmd,str(result))
                ebLogDebug('mFileExists called for filename {0} and returned {1}'.format(args[0],str(result)))
                return result
            else:
                #update the occurrence count in master entry
                occ = int(rc[2]) + 1
                ebRecordReplay.mUpdateCmdOccCount(cmd, str(occ))
                if str(result) == rc[1]:
                    ebLogDebug('mFileExists: got same output for existing command, increased occurrence count')
                else:
                    ebLogDebug('mFileExists: got diff output for existing command, so new entry added with occurrence_number')
                    cmd = "{0}_{1}".format(cmd,str(occ))
                    ebRecordReplay.mInsertCmdRec(cmd,str(result))
                return result
        except Exception as e:
            ebLogDebug(f"Exception during record : {cmd} exception:{str(e)}")
        return result


    @staticmethod 
    def mReplayFileExists(callee, callerSelf, *args, **kwargs):
        """
        This function handles the replaying of mFileExists. It fectches the record using 
        file name as key and returns the output 
        callee : Input : Function
        callerSelf : Input  : Callers Instance
        *args : Input : Input or callee
        **kargs : Input: Key value input for callee
        """

        from exabox.core.DBStore import ebGetDefaultDB
        cmd = args[0]
        # replace self uuid with fixed pattern
        cmd = cmd.replace(ebRecordReplay.taskUuid,"uuid_str")
        callStack = ebRecordReplay.mReturnCallStack(callee.__name__,cmd)
        cmd = callStack + cmd
        cmd = ebRecordReplay.mAppendCmdWithClustNameAndHostname(cmd,callerSelf.mGetHost())
        cmd = ebRecordReplay.mFindTimePattern(cmd)
        cmd = ebRecordReplay.mHandleBiggerCmd(cmd)
        try:
            db = ebGetDefaultDB()
            rc = ebRecordReplay.mGetRecordByCmd(cmd)
            if rc:
                #update read count
                read_count = rc[5] + 1
                ebRecordReplay.mUpdateCmdReadCount(cmd,read_count)
                if read_count != 1:
                    cmdWithOcc = "{0}_{1}".format(cmd,str(read_count)) 
                    rcWithOcc = ebRecordReplay.mGetRecordByCmd(cmdWithOcc)
                    if rcWithOcc:
                        rc = rcWithOcc
            if rc is None :
                raise Exception("mReplayFileExists: DB entry missing for command {0}".format(cmd))
            if rc is not None:
                ebLogDebug('OUTPUT from db: {0}'.format(rc[1]))
                if rc[1] == 'True':
                    ret = True
                elif rc[1] == 'False':
                    ret = False
                ebLogDebug('Replay mFileExists called for filename {0} and returned {1}'.format(args[0],ret))
                return ret
                 
        except Exception as e:
            ebLogDebug('Exception during fetch record for fileexist: {0}'.format(str(e)))
            raise
                            

    @staticmethod 
    def mRecordCommon(cmd:str, cmdOut, funcName:str, hostName:str) -> bool:
        """
        This function handles the record. It is a generic one,all 
        It executes the command in the real node and stores the command, command 
        output along with command occurrence count.
        """

        from exabox.core.DBStore import ebGetDefaultDB
        db = ebGetDefaultDB()
        if isinstance(cmdOut,bytes):
            cmdOut = cmdOut.decode("utf-8")
        cmd = cmd.replace(ebRecordReplay.taskUuid,"uuid_str")
        cmdOut = cmdOut.replace(ebRecordReplay.taskUuid,"uuid_str")
        callStack = ebRecordReplay.mReturnCallStack(funcName,cmd)
        cmd = callStack + cmd
        cmd = ebRecordReplay.mAppendCmdWithClustNameAndHostname(cmd,hostName)
        uuidPattern = ebRecordReplay.mFindUuidPattern(cmd)
        uuidReplace = "00000000-0000-0000-0000-000000000000"
        if uuidPattern:
            cmd = cmd.replace(uuidPattern,uuidReplace)
        uuidPattern = ebRecordReplay.mFindUuidPattern(cmdOut)
        if uuidPattern:
            cmdOut = cmdOut.replace(uuidPattern,uuidReplace)
        cmd = ebRecordReplay.mFindTimePattern(cmd)
        cmd = ebRecordReplay.mHandleBiggerCmd(cmd)

        rc = ebRecordReplay.mGetRecordByCmd(cmd)
        if rc is None :
            ebRecordReplay.mInsertCmdRec(cmd,cmdOut)
            ebLogDebug('{0} called for cmd {1} and returned {2}'.format(funcName, cmd,cmdOut))
            return True
        else:
            #update the occurrence count in master entry
            occ = int(rc[2]) + 1
            ebRecordReplay.mUpdateCmdOccCount(cmd, str(occ))
            if cmdOut == rc[1]:
                ebLogDebug('{0}: got same output for existing command, increased occurrence count'.format(funcName))
            else:
                ebLogDebug('{0}: got diff output for existing command, so new entry added with occurrence_number'.format(funcName))
                cmd = "{0}_{1}".format(cmd,str(occ))
                ebRecordReplay.mInsertCmdRec(cmd,cmdOut)
            return True


    @staticmethod 
    def mReplayCommon(cmd:str, funcName:str, hostName:str):
        """
        This function handles the replay of all other function. It is a generic one.
        It fetches the record from table using command as key and returns the command 
        output if the entry exist. 
        """

        from exabox.core.DBStore import ebGetDefaultDB
        cmd = cmd.replace(ebRecordReplay.taskUuid,"uuid_str")
        callStack = ebRecordReplay.mReturnCallStack(funcName,cmd)
        cmd = callStack +cmd
        cmd = ebRecordReplay.mAppendCmdWithClustNameAndHostname(cmd,hostName)
        uuidPattern = ebRecordReplay.mFindUuidPattern(cmd)
        uuidReplace = "00000000-0000-0000-0000-000000000000"
        if uuidPattern:
            cmd = cmd.replace(uuidPattern,uuidReplace)
        cmd = ebRecordReplay.mFindTimePattern(cmd)
        cmd = ebRecordReplay.mHandleBiggerCmd(cmd)
        try:
            db = ebGetDefaultDB()
            rc = ebRecordReplay.mGetRecordByCmd(cmd)
            if rc:
                #update read count
                read_count = rc[5] + 1
                ebRecordReplay.mUpdateCmdReadCount(cmd,read_count)
                if read_count != 1:
                    cmdWithOcc = "{0}_{1}".format(cmd,str(read_count)) 
                    rcWithOcc = ebRecordReplay.mGetRecordByCmd(cmdWithOcc)
                    if rcWithOcc:
                        ebLogDebug('Replay: {0} called for cmd {1} and returned {2}'.format(funcName,cmdWithOcc,rc[1]))
                        rc = rcWithOcc
                    else:
                        ebLogDebug('Replay: {0} called for cmd {1} and returned {2}'.format(funcName,cmd,rc[1]))
            if rc is None:
                raise Exception("mReplayCommon: DB entry missing for command {0}".format(cmd))
            ret = ""
            if rc is not None :
                ret = rc[1]
            ret = ret.replace(uuidReplace,uuidPattern)
            ret = ret.replace("uuid_str",ebRecordReplay.taskUuid)
            return ret
        except Exception as e:
            ebLogDebug('Exception during fetch record for {0}: {1}'.format(funcName,str(e)))
            raise

    @staticmethod
    def mHandleRecord(callee,callerSelf,*args, **kwargs):
        """
        callee : Input : Function
        callerSelf : Input  : Callers Instance
        *args : Input : Input or callee
        **kargs : Input: Key value input for callee
        """
        from exabox.core.DBStore import ebGetDefaultDB
        if("mExecuteCmdLog2" == callee.__name__):
            cmdOutput = callee(callerSelf, *args, **kwargs)
            try:
                ebLogDebug('mExecuteCmdLog2 called to execute : {0} '.format(args[0]))
                cmds = args[0]
                if type(cmds) is list:
                    cmd = "".join(cmds)
                else:
                    cmd = cmds
                cmd = ebRecordReplay.mFindOEDARandomPattern(cmd) 
                out, err= cmdOutput
                cmdOut = ""
                if out:
                    cmdOut = "".join(out)
                    db = ebGetDefaultDB()
                    rc = ebRecordReplay.mGetRecordByCmd(cmd)
                    if rc is None :
                        ebRecordReplay.mInsertCmdRec(cmd,cmdOut)
            except Exception as e:
                ebLogDebug('mExecuteCmdLog2 Exception during record for cmd {0} : exp {1}'.format(cmd,str(e)))
            return cmdOutput
        elif ("mExecuteLocal" == callee.__name__) and (type(callerSelf).__name__ == "exaBoxCluCtrl"):
            return ebRecordReplay.mRecordExecuteLocal(callee,callerSelf, *args, **kwargs)
        elif ("mExecuteCmd" == callee.__name__) or ("mExecuteCmdLog" == callee.__name__):
            return  ebRecordReplay.mRecordExecuteCmd(callee,callerSelf, *args, **kwargs)
        elif ("mFileExists" == callee.__name__):
            return ebRecordReplay.mRecordFileExists(callee,callerSelf, *args, **kwargs)
        elif ("mReadFile" == callee.__name__):
            ebLogDebug('mReadFile called')
            cmd = args[0]
            cmdOut = callee(callerSelf, *args, **kwargs)
            try:
                ebRecordReplay.mRecordCommon(cmd, cmdOut, callee.__name__,callerSelf.mGetHost())
            except Exception as e :
                ebLogDebug('Exception during record cmd:{0} Exception: {1}'.format(cmd,str(e)))
            return cmdOut
        elif ("mExecuteCmdsAuthInteractive" == callee.__name__):
            ebLogDebug('mExecuteCmdsAuthInteractive called')
            cmdlist = args[0]
            cmd = ""
            for cmds in cmdlist:
                if type(cmds) is list:
                    cmd = "".join(cmds)
                else:
                    cmd = cmds
            ret = callee(callerSelf, *args, **kwargs)
            cmdOut = str(ret)
            try:
                retRecord = ebRecordReplay.mRecordCommon(cmd,cmdOut,callee.__name__,callerSelf.mGetHost())
                if not retRecord:
                    ebLogDebug('Record insertion failed for command : {0}'.format(cmd))
            except Exception as e :
                ebLogDebug('Exception during record : {0}'.format(str(e)))
            return ret
        elif ("mCopy2Local" == callee.__name__):
            ebLogDebug('mCopy2Local called src: {0} :: dest: {1}'.format(args[0],args[1]))
            src = args[0]
            dest = args[1]
            ret = callee(callerSelf, *args, **kwargs)
            if os.path.basename(src) == "check_sum_file.conf":
                if os.path.exists(ebRecordReplay.recordFolder):
                    shutil.rmtree(ebRecordReplay.recordFolder)
                    os.mkdir(ebRecordReplay.recordFolder)
                else:
                    os.mkdir(ebRecordReplay.recordFolder)
                recordDest = "{0}/record_check_sum_file.conf".format(ebRecordReplay.recordFolder)
                shutil.copy2(dest,recordDest)
                db = ebGetDefaultDB()
                cmd = "record_repo_root"
                rc = ebRecordReplay.mGetRecordByCmd(cmd)
                if rc is None :
                    cmdOut = ebRecordReplay.repositoryRoot
                    ebRecordReplay.mInsertCmdRec(cmd,cmdOut)
            return
        else:
            ebLogDebug('RECORD DEBUG IMP:{0} called'.format(callee.__name__))
            return callee(callerSelf, *args, **kwargs)


    @staticmethod
    def mHandleReplay(callee,callerSelf,*args, **kwargs):
        """
        callee : Input : Function
        callerSelf : Input  : Callers Instance
        *args : Input : Input or callee
        **kargs : Input: Key value input for callee
        """
        from exabox.core.DBStore import ebGetDefaultDB
        #if (args.len() > 0): 
        #    cmd = args[0]
        #    ebLogDebug("***** callee name {0} : cmd {0}".format(callee.__name__,cmd))
        if ("mExecuteCmd" == callee.__name__) or ("mExecuteCmdLog" == callee.__name__):
            return  ebRecordReplay.mReplayExecuteCmd(callee,callerSelf, *args, **kwargs)
        elif ("mExecuteLocal" == callee.__name__) and (type(callerSelf).__name__ == "exaBoxCluCtrl"):
            ebLogDebug('***** mExecuteLocalLocal:{0}'.format(type(callerSelf).__name__))
            return ebRecordReplay.mReplayExecuteLocal(callee,callerSelf, *args, **kwargs)
        elif ("mGetCmdExitStatus" == callee.__name__):
            if type(callerSelf).__name__ == "exaBoxLocal":
                if ebRecordReplay.pingCmdExitStatus == 1:
                    ebLogDebug("exaBoxLocal :: ping mGetCmdExitStatus handled")
                    ebRecordReplay.pingCmdExitStatus = 0
                    return 0
                else:
                    return callee(callerSelf, *args, **kwargs)
            else:
                ebLogDebug("***** callee name {0} : cmd {1}".format(callee.__name__,ebRecordReplay.lastMExecuteCmd))
                mExecuteCmdExitStatus = 0
                db = ebGetDefaultDB()
                if ebRecordReplay.lastMExecuteCmd == None:
                    return mExecuteCmdExitStatus
                rc = ebRecordReplay.mGetRecordByCmd(ebRecordReplay.lastMExecuteCmd)
                ebRecordReplay.lastMExecuteCmd = None
                if rc is not None :
                    mExecuteCmdExitStatus = int(rc[4])
                    ebLogDebug('mExecuteCmdExitStatus {0}'.format(mExecuteCmdExitStatus))
                return mExecuteCmdExitStatus 
        elif ("mFileExists" == callee.__name__):
            return  ebRecordReplay.mReplayFileExists(callee,callerSelf, *args, **kwargs)
        elif ("mCopy2Local" == callee.__name__):
            ebLogDebug('mCopy2Local called src: {0} :: dest: {1}'.format(args[0],args[1]))
            src = args[0]
            dest = args[1]
            if os.path.basename(src) == "check_sum_file.conf":
                ebLogDebug('check_sum_file.conf update in progress.{0}'.format(ebRecordReplay.recordFolder))
                if os.path.exists(ebRecordReplay.recordFolder) and os.path.exists(ebRecordReplay.recordFolder +  "/record_check_sum_file.conf"):
                    db = ebGetDefaultDB()
                    cmd = "record_repo_root"
                    rc = ebRecordReplay.mGetRecordByCmd(cmd)
                    if rc is not None :
                        recordRepoRoot = rc[1]
                        ebLogDebug('check_sum_file.conf Repo root of Record {0}'.format(recordRepoRoot))
                    else:
                        raise Exception("record_repo_root not present in recorded mysql file dump {0}, Replay Failed".format(ebRecordReplay.tableName))
                    ebRecordReplay.mChecksumRepoUpdate(ebRecordReplay.recordFolder + "/record_check_sum_file.conf",ebRecordReplay.recordFolder + "/replay_check_sum_file.conf",recordRepoRoot) 
                    recSrc = os.path.join(ebRecordReplay.recordFolder,"replay_check_sum_file.conf")
                    shutil.copy2(recSrc,dest)
                else:
                    ebLogDebug('check_sum_file.conf file not present at ./{0}, Replay Failed'.format(ebRecordReplay.recordFolder))
                    raise Exception("check_sum_file.conf file not present at ./{0}, Replay Failed".format(ebRecordReplay.recordFolder))
            return
        elif("mExecuteCmdLog2" == callee.__name__):
            try:
                ebLogDebug('mExecuteCmdLog2 called to execute : {0} '.format(args[0]))
                out = []
                err = []
            
                cmds = args[0]
                if type(cmds) is list:
                    cmd = "".join(cmds)
                else:
                    cmd = cmds

                cmd = ebRecordReplay.mFindOEDARandomPattern(cmd) 
                db = ebGetDefaultDB()
                rc = ebRecordReplay.mGetRecordByCmd(cmd)
                if rc is not None :
                    out = list(rc[1])
                else:
                    ebLogDebug('mExecuteCmdLog2 - DB entry not found  for {0}'.format(cmd))
                return [out,err]
            except Exception as e:
                ebLogDebug('mExecuteCmdLog2: Exception during replay for cmd {0} : exp {1}'.format(cmd,str(e)))
                raise
        elif ("_mCheckSshd" == callee.__name__):
            return True
        elif ("mReadFile" == callee.__name__):
            ebLogDebug('mReadFile called')
            cmd = args[0]
            cmdOut = ebRecordReplay.mReplayCommon(cmd,callee.__name__,callerSelf.mGetHost())
            cmdOut = cmdOut.encode("utf-8")
            return cmdOut
        elif ("mExecuteCmdsAuthInteractive" == callee.__name__):
            ebLogDebug('mExecuteCmdsAuthInteractive called')
            cmdlist = args[0]
            for cmds in cmdlist:
                if type(cmds) is list:
                    cmd = "".join(cmds)
                else:
                    cmd = cmds
            try:
                cmdOut = ebRecordReplay.mReplayCommon(cmd,callee.__name__,callerSelf.mGetHost())
                if cmdOut == 'True':
                    ret = True
                elif cmdOut == 'False':
                    ret = False
                else:
                    ebLogDebug('Replay: Record not found for cmd : {0}'.format(cmd))
            except Exception as e :
                ebLogDebug('Exception during replay : {0}'.format(str(e)))
                raise
            return ret
        else:
            ebLogDebug('REPLAY DEBUG IMP:{0} called'.format(callee.__name__))
            return

    @staticmethod 
    def mRecordReplayWrapper(callee):
        """
        This is the entry point of record and replay. This is a wrapper gets called before the 
        actual function gets called. According to the caller, Recording and Replaying gets executed.
        callee : Input : Function
        """

        @wraps(callee)
        def wrapper(callerSelf, *args, **kwargs):
            from exabox.core.DBStore import ebGetDefaultDB
            if (ebRecordReplay.operMode is Mode.NORMAL) or (ebRecordReplay.clusterName is None):
                return callee(callerSelf, *args, **kwargs)
            if ebRecordReplay.operMode is Mode.RECORD:
                return ebRecordReplay.mHandleRecord(callee,callerSelf, *args, **kwargs)
            if ebRecordReplay.operMode is Mode.REPLAY:
                return ebRecordReplay.mHandleReplay(callee,callerSelf, *args, **kwargs)

        return wrapper
