"""
 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    Agent - Configuration File Managemenet

FUNCTION:
    Agent Core functionalities

NOTE:
    None

History:
    jesandov 09/29/2020 - 31949634 - Migrate the MySQL DB
    ndesanto 11/21/2019 - 30294648 - PYTHON 3 compatibility, fixing missing import
    sdeekshi 08/15/2017 - Implement Mock functionalty
    sdeekshi 08/15/2017 - Creation
"""

from time import strftime,sleep
from datetime import datetime
from datetime import timedelta
import fcntl
import os
import re, json

from exabox.agent.ebJobRequest import ebJobRequest
from exabox.ovm.clucontrol import exaBoxCluCtrl
from exabox.core.Context import get_gcontext
from exabox.log.LogMgr import ebLogInfo
from exabox.ovm.bmc import XMLProcessor
from exabox.log.LogMgr import ebLogError, ebLogDebug, ebLogInfo, ebLogWarn
from exabox.core.DBStore import ebGetDefaultDB


def MockStatus(self, aParams, aResponse):
    ebLogInfo("handling mock status {0}".format(aParams['uuid']))
    sleep(1)
    
    # Get the database mock object
    _db = ebGetDefaultDB()
    row = _db.mGetMockCallByUUID(aParams['uuid'])

    # Read the behavior commands
    custom = {}
    with open("config/custom_mock.json", "r") as customFile:
        fcntl.flock(customFile.fileno(), fcntl.LOCK_SH)
        custom = json.load(customFile)
        fcntl.flock(customFile.fileno(), fcntl.LOCK_UN)

    # Read the call from the database
    parse = {"body": ""}
    data = ebJobRequest("", aParams)
    commandBehavior = custom['default']

    if not row:
        data.mSetStatusInfo("500")
    else:
        data.mSetUUID(row[0])
        data.mSetStatusInfo(str(row[2]))
        data.mSetCmdType(row[3])
        data.mSetXml(row[4])
        data.mSetParams(json.loads(row[5]))

        #Update the behavior object
        if data.mGetCmdType() in custom.keys():
            commandBehavior.update(custom[data.mGetCmdType()])

        # Respect sequence file
        if os.path.exists("config/custom_mock_sequence.json"):

            sequence = {}
            with open("config/custom_mock_sequence.json", "r") as sequenceFile:
                fcntl.flock(sequenceFile.fileno(), fcntl.LOCK_SH)
                sequence = json.load(sequenceFile)
                fcntl.flock(sequenceFile.fileno(), fcntl.LOCK_UN)

            if sequence['current'] < len(sequence['sequence']):
                currentCmd = sequence['sequence'][sequence['current']]

                if currentCmd.pop("cmd") == data.mGetCmdType():
                    commandBehavior.update(currentCmd)

        # Apply time operations
        cur = datetime.now()
        dbt = datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')
        ebLogInfo("cur: {0}, dbt: {1}".format(cur, dbt))
        data.mSetTimeStampStart(dbt.strftime("%c"))
        delta = timedelta(seconds=15)
        try:
            delta = timedelta(seconds=commandBehavior["execution_seconds"])
        except Exception:
            ebLogInfo("Invalid execution format: {0}".format(commandBehavior["execution_seconds"]))
        if cur - dbt <= delta:
            data.mSetStatusInfo("202")
        else:
            data.mSetTimeStampEnd((dbt + delta).strftime("%c"))

        # Determine if XML is configured for multivm
        _shared = "false"
        try:
            _xmlo = XMLProcessor(data.mGetXml())
            _clusters = _xmlo.findall('software/clusters/cluster')
            if len(_clusters) > 1:
                parse['body'] = 'SHARED ENVIRONMENT CONFIG TRUE'
                parse['is_shared_env'] = "true"
            else:
                parse['is_shared_env'] = "false"
        except:
          ebLogInfo("*** MOCK error can not determine single/multi vm XML")

    # Load the Behavior
    ec_details = {}
    new_ec_details = {}
    if commandBehavior['behavior'] == "success":
        ec_details = commandBehavior['on_success_ec_details']
    else:
        if data.mGetStatusInfo() != "202":
            data.mSetStatusInfo("500")
            ec_details = commandBehavior['on_fail_ec_details']

    # ECRA params behavior
    if data.mGetParams() and "jsonconf" in data.mGetParams().keys():
        if data.mGetParams()['jsonconf'] and "custom_mock" in data.mGetParams()['jsonconf']:
            custom_ecra_mock = data.mGetParams()['jsonconf']['custom_mock']
            if 'behavior' in custom_ecra_mock.keys() and 'ec_details' in custom_ecra_mock.keys():
                ec_details = custom_ecra_mock['ec_details']
                commandBehavior['behavior'] = custom_ecra_mock['behavior']
                ebLogInfo("Loaded ECRA params jsonconf > custom_mock")

            else:
                commandBehavior['behavior'] = "fail"
                ec_details = {}
                data.mSetStatusInfo("501")

                data.mSetError("718")
                msg = "Missing 'behavior' or 'ec_details' into ECRA params jsonconf > custom_mock"
                data.mSetErrorStr(msg)
                ebLogInfo(msg)

    # Create the returning data if not pending status
    if data.mGetStatusInfo() != "202":
        for dictkey, dictvalue in ec_details.items():
            patt = re.match("\<(.*)\>", str(dictvalue))
            if patt is not None:
                parsekey = patt.group(1)
                if parsekey in parse.keys():
                    new_ec_details[dictkey] = parse[parsekey]
                else:
                    new_ec_details[dictkey] = ""
            else:
                new_ec_details[dictkey] = dictvalue
    data.mSetData(new_ec_details)

    # Update the request object
    if data.mGetStatusInfo() in ["202"]:
        data.mSetStatus("Pending")
        aResponse['success'] = "True"
    else:
        data.mSetStatus("Done")

        if data.mGetStatusInfo() == "500" or commandBehavior['behavior'] == "fail":
            if data.mGetError() in ["0", "", "Undef"]:
                data.mSetError("717")
                data.mSetErrorStr("Error on Mock Mode")
            aResponse['success'] = "False"
        else:
            data.mSetError("0")
            data.mSetErrorStr("No Errors")
            aResponse['success'] = "True"

    aResponse['body'] = data.mUnpopulate(aStringfy=True)
    aResponse['xml'] = data.mGetXml()
    aResponse['status'] = "Done"

class MockDispatcher():

    def __init__(self, aJob):
        self.__requestType     = aJob.mGetType()
        self.__commandName     = aJob.mGetCmd()
        self.__commandOptions  = aJob.mGetOptions()
        self.__cmdtype         = aJob.mGetCmdType()
        self.__params          = json.dumps(aJob.mGetParams())
        self.__requestUUID     = aJob.mGetUUID()
 
    def mDispatchMock(self):
        ebLogInfo('{0}: dispatched for cmd {1} with options: ({2}) and request type {3}\n'.format( \
                   datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self.__commandName, self.__commandOptions, self.__requestType))
        self.mMockOperation()
        sleep(1)

    def mMockOperation(self):
        ebLogInfo("handling mock operation " + self.__commandName)
        # by default all the operation status will be 200 success
        # if we want to mock a failed operation, we could modify this status for certain situation
        status = 200
        curt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        xml_path = self.__commandOptions.configpath or '/tmp/params.xml'

        # Respect sequence file
        if os.path.exists("config/custom_mock_sequence.json"):

            sequence = {}
            with open("config/custom_mock_sequence.json", "r") as sequenceFile:
                fcntl.flock(sequenceFile.fileno(), fcntl.LOCK_SH)
                sequence = json.load(sequenceFile)
                fcntl.flock(sequenceFile.fileno(), fcntl.LOCK_UN)

            if sequence['current']+1 < len(sequence['sequence']):
                currentCmd = sequence['sequence'][sequence['current']+1]

                if self.__cmdtype == currentCmd['cmd']:
                    sequence['current'] += 1
                    ebLogInfo("Update custom_mock_sequence.json: {0}".format(sequence))

                    with open("config/custom_mock_sequence.json", "w") as sequenceFile:
                        fcntl.flock(sequenceFile.fileno(), fcntl.LOCK_EX)
                        json.dump(sequence, sequenceFile, sort_keys=True, indent=4)
                        fcntl.flock(sequenceFile.fileno(), fcntl.LOCK_UN)

        # Create mock call
        _req = ebJobRequest(None, {})
        _req.mSetUUID(self.__requestUUID)
        _req.mSetCmdType(self.__cmdtype)
        _req.mSetTimeStampStart(curt)
        _req.mSetStatusInfo(status)
        _req.mSetXml(xml_path)
        _req.mSetParams(self.__params, aMock=True)

        ebLogInfo("Inserting values into calls table : ")
        ebLogInfo(_req.mToDictMock())

        _db = ebGetDefaultDB()
        _reqExist = _db.mGetMockCallByUUID(self.__requestUUID)

        if not _reqExist:
            _db.mInsertMockCall(_req)

# end of file