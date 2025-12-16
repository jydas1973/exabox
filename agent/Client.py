"""
 Copyright (c) 2015, 2025, Oracle and/or its affiliates.

NAME:
    Client - Client RESTFull API and CLI support

FUNCTION:
    Client Core functionalities

NOTE:
    None

History:
    abflores    06/30/2025 - Bug 38027811 - Add SOP testing
    avimonda    03/19/2024 - Bug 36405321 - Adding retry mechanism in
                             mPerformRequest in case of 503 HTTP response.
    avimonda    12/12/2023 - Bug 36062328 - Modified the retry mechanism
                             in mPerformRequest based on the data about free
                             workers and the current resource utilization.
    aypaul      12/07/2023 - Enh#36060629 Pending exacloud operations list.
    aypaul      11/29/2023 - Enh#35730776 Integration of OCI certificate service with exacloud agent.
    araghave    20/02/2020 - Enh 30908782 - ksplice configuration on dom0
                             and cells
    ndesanto    11/05/2019 - ENH 30480538: HTTPS and Certificate Rotation
    ndesanto    10/02/2019 - 30374491 - EXACC PYTHON 3 MIGRATION BATCH 01
    araghave    07/02/2019 - ENH 29911293 - POSTCHECK OPTION FOR
                             ALL PATCH OPERATIONS.
    pbellary    04/04/2019 - bug 29472359: undo stepwise createservice
    srtata      03/22/2019 - bug 29472239: add stepwise createservice
    pverma      04/07/2017 - Support for sparse for existing customers
    aschital    06/14/2016 - Added dataguard in allowed REST APIs
    mirivier    02/09/2015 - Create file
"""

from __future__ import print_function

from six.moves.urllib.parse import urlparse
import ast
import json
import socket
from six.moves import urllib
from six.moves.urllib.parse import quote_plus, unquote_plus, urlencode
import base64
from exabox.core.Context import get_gcontext
from exabox.agent.AuthenticationStorage import ebGetHTTPAuthStorage
from exabox.core.DBStore import ebGetDefaultDB
import time
import exabox.network.HTTPSHelper as HTTPSHelper
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogJson, ebGetDefaultLogLevel, ebLogTrace
from exabox.config.Config import PROGRAM_ARGUMENTS
from ast import literal_eval
import traceback
import zlib

DEFAULT_RETRY_COUNT = 5

def ebBuildAPIRouteMap():
    """
    Builds REST_API_MAP using the information of PROGRAM_ARGUMENTS from the
    config/Config.py file.
    """

    """
    The keys of this dictionary will be he same as in REST_API_MAP.
    The value consist of a tuple, where the first entry will be route of the
    endpoint and the second entry, a key from the PROGRAM_ARGUMENTS
    dictionary at config/Config.py from which to pick its choices parameters
    to fill in the cmd? argument queries of the endpoint.
    """
    _endpoints_config_map = {
        'vmctrl':       ('VMCtrl',      'vmctrl'),
        'bmcctrl':      ('BMCCtrl',     'bmcctrl'),
        'cluctrl':      ('CLUCtrl',     'clusterctrl'),
        'schedgenctrl': ('SCGENCtrl',   'schedgenctrl'),
        'agentcmd':     ('AgentCmd',    'agent'),
        'monitor':      ('Monitor',     'monitor'),
        'exakms':       ('exakms',      'exakms')
    }

    _result = {}
    for process, routes in _endpoints_config_map.items():
        _result[process] = {}
        for endpoint in PROGRAM_ARGUMENTS[routes[1]]['choices']:
            _result[process][endpoint] = '/%s?cmd=%s' % (routes[0], endpoint)

    # SPECIAL CASES

    # No status-like option in PROGRAM_ARGUMENTS and no cmd query commands.
    _result['status'] = {}
    _result['status']['request'] = '/Status'

    # Query command is not start, but status
    _result['agentcmd']['start'] = '/AgentCmd?cmd=status'

    # No patch-like option in PROGRAM_ARGUMENTS, added manually
    _result['patch'] = {}
    _result['patch']['patchclu_apply'] = '/Patch?cmd=patchclu_apply'

    # Missing 'echo' command in Config.py, added only here
    _result['cluctrl']['echo'] = '/CLUCtrl?cmd=echo'

    return _result


REST_API_MAP = ebBuildAPIRouteMap()

"""
JSON Response format and fields:
--------------------------------
uuid    : Request Unique Identifier
status  : Done | Pending | Cancelled
statusinfo : True|False:%complete: step - stepinfo
success : True | False
error   : int Code | 0 No Error
error_str : str Explanation string about the error | None No Error
body  : Body containing information about the excution of the request.
start_time: TimeStamp referring to the beginning of the request processing
end_time : TimeStamp referring to the end of the request processing
params : request parameters (if any)
"""

class ebJobResponse(object):

    def __init__(self):
        self.__uuid    = '00000000-0000-0000-0000-000000000000'
        self.__status  = 'Undefined'
        self.__statusinfo = 'Undefined'
        self.__starttime = None
        self.__endtime = None
        self.__cmdtype = None
        self.__params  = None
        self.__error   = None
        self.__error_str = None
        self.__body    = None
        self.__data    = None
        self.__success = 'Undefined'
        self.__xml     = None
        self.__patch_list = None

        self.__response= {}

        self.__callback = {
            'uuid' : self.mSetUUID,
            'status' : self.mSetStatus,
            'statusinfo' : self.mSetStatusInfo,
            'success' : self.mSetSuccess,
            'start_time' : self.mSetTimeStampStart,
            'end_time' : self.mSetTimeStampEnd,
            'cmd' : self.mSetCmdType,
            'error' : self.mSetError,
            'error_str' : self.mSetErrorStr,
            'body' : self.mSetBody,
            'data' : self.mSetData,
            'patch_list' : self.mSetPatchList
        }

    def mPopulate(self, aKey, aValue):

        if aKey in list(self.__callback.keys()):
            self.__callback[aKey](aValue)

    def mToJson(self):

        _response = self.__response

        _response['uuid'] = self.mGetUUID()
        _response['status'] = self.mGetStatus()
        _response['statusinfo'] = self.mGetStatusInfo()
        _response['success'] = self.mGetSuccess()
        if self.__starttime is not None:
            _response['start_time'] = self.mGetTimeStampStart()
        if self.__endtime is not None:
            _response['end_time'] = self.mGetTimeStampEnd()
        if self.__error is not None:
            _response['error'] = self.mGetError()
        if self.__error_str is not None:
            _response['error_str'] = self.mGetErrorStr()
        _response['cmd'] = self.mGetCmdType()
        if self.__params is not None:
            _response['params'] = self.mGetParams()
        if self.__body is not None:
            _response['body'] = self.mGetBody()
        if self.__xml is not None:
            _response['xml'] = self.mGetXml()
        if self.__data is not None:
            _response['data'] = self.mGetData()
        if self.__patch_list is not None:
            if self.mGetPatchList():
                _response['patch_list'] = self.mGetPatchList()
            else:
                _response['patch_list'] = 'Undef'

        return json.dumps(_response, indent=4, separators=(',',': '))

    def mGetXml(self):
        return self.__xml

    def mSetXml(self, aValue):
        self.__xml = aValue

    def mGetSuccess(self):
        return self.__success

    def mSetSuccess(self, aSuccess):
        self.__success = aSuccess

    def mGetStatus(self):
        return self.__status

    def mSetStatus(self, aStatus):
        self.__status = aStatus

    def mGetStatusInfo(self):
        return self.__statusinfo

    def mSetStatusInfo(self, aStatusInfo):
        self.__statusinfo = aStatusInfo

    def mGetUUID(self):
        return self.__uuid

    def mSetUUID(self, aUUID):
        self.__uuid = aUUID

    def mSetTimeStampStart(self,aValue):
        self.__starttime = aValue

    def mGetTimeStampStart(self):
        return self.__starttime

    def mGetTimeStampEnd(self):
        return self.__endtime

    def mSetTimeStampEnd(self,aValue):
        self.__endtime = aValue

    def mGetCmdType(self):
        return self.__cmdtype

    def mSetCmdType(self, aCmdType):
        self.__cmdtype = aCmdType

    def mGetParams(self):
        return self.__params

    def mSetParams(self, aParams):
        self.__params = aParams

    def mGetError(self):
        return self.__error

    def mSetError(self, aError):
        self.__error = aError

    def mGetErrorStr(self):
        return self.__error_str

    def mSetErrorStr(self, aErrorStr):
        self.__error_str = aErrorStr

    def mGetBody(self):
        return self.__body

    def mSetBody(self, aBody):
        self.__body = aBody

    def mGetData(self):
        return self.__data

    def mSetData(self, aData):
        self.__data = aData

    def mGetPatchList(self):
        return self.__patch_list

    def mSetPatchList(self, aPatchList):
        self.__patch_list = aPatchList

gClientConfig = None

def ebGetClientConfig():
    global gClientConfig
    return gClientConfig

class ebExaClient(object):

    def __init__(self):

        self.__options = get_gcontext().mGetArgsOptions()
        self.__config_opts = get_gcontext().mGetConfigOptions()

        self.__authkey = ebGetHTTPAuthStorage().mGetAdminCredentialForRequest()

        if self.__options.agent_port:
            self.__agent_port = int(self.__options.agent_port)
        elif "agent_port" in list(self.__config_opts.keys()):
            self.__agent_port = int(self.__config_opts["agent_port"])
        else:
            self.__agent_port = 7080

        self.__hostname = self.__options.agenthostname
        if not self.__hostname:
            self.__hostname = self.__config_opts["agent_host"]

        if "use_ocicerts_https" in list(self.__config_opts.keys()):
            if isinstance(self.__config_opts["use_ocicerts_https"], str):
                _mode = self.__config_opts["use_ocicerts_https"].lower() == "true"
                if _mode:
                    self.__hostname = socket.getfqdn()

        self.__request  = None
        self.__response = ebJobResponse()
        self.__jsonresponse = None
        self.__uuid     = None
        self.__cmdtype  = None
        self.__quiet    = False
        #
        # Populate gClientConfig (if not done)
        #
        global gClientConfig
        if not gClientConfig:
            gClientConfig = [ self.__hostname, self.__agent_port, self.__authkey]

    def mSetQuietMode(self,aMode=True):
        self.__quiet=aMode

    def mBuildErrorResponse(self, aErrorCode, aErrorStr, aBody, aData=None):
        self.__response.mSetTimeStampStart(time.strftime("%c"))
        self.__response.mSetTimeStampEnd(time.strftime("%c"))
        self.__response.mSetCmdType(self.__cmdtype)
        self.__response.mSetStatus('Done')
        self.__response.mSetStatusInfo('False:100:0 - statusinfo not available')
        self.__response.mSetSuccess('False')
        self.__response.mSetError(aErrorCode)
        self.__response.mSetErrorStr(aErrorStr)
        self.__response.mSetBody(aBody)
        if aData is not None:
            self.__response.mSetData(aData)
        self.__response.mSetXml(None)

    def mBuildResponse(self, aJson):

        _json = aJson
        for k in list(_json.keys()):
            self.__response.mPopulate(k, _json[k])
        _body = self.__response.mGetBody()

        if self.__cmdtype == 'request_status':
            _l = _body
            if _l:
                self.__response.mSetStatus(_l[1])
                self.__response.mSetStatusInfo(_l[10])
                self.__response.mSetTimeStampStart(_l[2])
                self.__response.mSetTimeStampEnd(_l[3])
                self.__response.mSetCmdType(_l[4])
                self.__response.mSetParams(_l[5])
                self.__response.mSetError(_l[6])
                self.__response.mSetErrorStr(_l[7])
                self.__response.mSetBody(_l[8])
                self.__response.mSetData(_l[13])
                self.__response.mSetXml(_l[9])
                self.__response.mSetPatchList(_l[14])
            else:
                # __reponse should have been populated with Error and ErrorString during the mPopulate stage
                pass

    def mSetHostname(self, aValue):
        self.__hostname = aValue

    def mSetPort(self, aValue):
        self.__port = aValue

    def mBuildRequest(self, aPath):
        # Note: No trailing / required before path
        if HTTPSHelper.is_https_enabled():
            self.__request = 'https://'+self.__hostname+':'+str(self.__agent_port)+aPath
        else:
            self.__request = 'http://'+self.__hostname+':'+str(self.__agent_port)+aPath

    def mGetSystemMetricsFromDB(self):

        _free_worker = 0
        _cpu_percent = 0.0
        _mem_percent = 0.0

        _db = ebGetDefaultDB()

        _cpu_percent, _mem_percent, _last_update_time = _db.mSelectAllFromEnvironmentResourceDetails()
        if _cpu_percent is None:
            _cpu_percent = 0.0
        if _mem_percent is None:
            _mem_percent = 0.0

        _free_worker = _db.mGetNumberOfIdleWorkers()

        ebLogTrace(f"Environment resource statistics, CPU Usage: {_cpu_percent}, Memory Usage : {_mem_percent}, Free Workers: {_free_worker}.")

        return _cpu_percent, _mem_percent, _free_worker

    def mCheckSystemResourceAvailability(self, aTimeout):

        _free_worker = 0
        _cpu_percent = 0.0
        _mem_percent = 0.0
        _cpu_threshold = 80.0
        _mem_threshold = 80.0
        _retry = 0
        _retry_count = 11
        _timeout = aTimeout

        _config_options = get_gcontext().mGetConfigOptions()
        if 'cpu_threshold' in list(_config_options.keys()):
            _cpu_threshold = float(_config_options['cpu_threshold'])

        if 'mem_threshold' in list(_config_options.keys()):
            _mem_threshold = float(_config_options['mem_threshold'])

        while (_retry < _retry_count):

            _retry += 1
            if _retry == _retry_count:
                break

            _cpu_percent, _mem_percent, _free_worker = self.mGetSystemMetricsFromDB()
            if (_free_worker == 0 and (float(_cpu_percent) > _cpu_threshold or float(_mem_percent) > _mem_threshold)):
                time.sleep(_timeout)
            else:
                break

    def mPerformTimeout(self, retry_count):

        return 60 + retry_count * 60

    def mPerformRequest(self, form_data=None, aRetryCount=DEFAULT_RETRY_COUNT):

        _data = None
        _error = None
        _error_str = None
        _retry = 0
        _retry_count = aRetryCount
        _timeout = self.mPerformTimeout(_retry)

        if self.__options.debug:
            ebLogDebug('*** PerformRequest: %s' % (self.__request))
        # Issue Request
        while _retry < _retry_count:
            try:
                headers = {}
                headers["authorization"] = "Basic {}".format(self.__authkey)
                if form_data:
                    data = urlencode(form_data).encode("utf-8")
                    _response = HTTPSHelper.build_opener(\
                        self.__hostname, self.__agent_port,
                        self.__request, aData=data,
                        aHeaders=headers, aTimeout=_timeout)
                else:
                    _response = HTTPSHelper.build_opener(\
                        self.__hostname, self.__agent_port,
                        self.__request, aHeaders=headers, aTimeout=60)
                _data = _response.read()
                break
            except urllib.error.HTTPError as e:
                ebLogWarn(str(e))
                if e.code == 503:
                    _retry += 1
                    if _retry == 2:
                        _error = '503'
                        _error_str = 'Exacloud is unable to process the request due to system resources overload. Please retry after sometime.'
                        break
                    self.mCheckSystemResourceAvailability(_timeout)
                else:
                    _error = '120'
                    _error_str = str(e)
                    break
            except urllib.error.URLError as e:
                ebLogWarn(str(e))
                _error = '121'
                _error_str = str(e)
                break
            except socket.error as e:
                ebLogWarn(str(e))
                _retry += 1
                if _retry == _retry_count:
                    raise e
                _timeout = self.mPerformTimeout(_retry)
            except Exception as e:
                if self.__quiet:
                    ebLogError('*** urlopen error:{0} {1} {2}'.format(str(e), self.__request, _data))
                break

        # Process Reply
        if not _error:
            try:
                _json = json.loads(_data)
                self.mBuildResponse(_json)
                self.__jsonresponse = self.__response.mToJson()
            except Exception as e:
                _error = '122'
                _error_str = str(e)
                self.mBuildErrorResponse(_error, _error_str, 'None')
                self.__jsonresponse = self.__response.mToJson()
                ebLogError(self.__jsonresponse)
        else:
            self.mBuildErrorResponse(_error, _error_str, 'None')
            self.__jsonresponse = self.__response.mToJson()
            # ebLogError(self.__jsonresponse)

    def mIssueRequest(self,aCmd=None,aOptions=None,aRetryCount=DEFAULT_RETRY_COUNT):

        if aOptions is not None:
            options = aOptions
        else:
            options = get_gcontext().mGetArgsOptions()

        #Sample execution: bin/exacloud -jd requests -jc sample.json -al localhost -as
        if options.jsondispatch:
            _form = dict()
            _jc = dict()

            if options.jsonconf:
                _jc = options.jsonconf

            if options.exaunitid:
                _form['exaunitid'] = options.exaunitid
                _form["ignore_uuid_check"] = True

            if options.workflowid:
                _form['wf_uuid'] = options.workflowid
                _form["ignore_uuid_check"] = True

            _form['jsonconf'] = _jc
            _form['cmd'] = options.jsondispatch
            self.__cmdtype = 'jsondispatch'

            _path = f"/jsondispatch/{options.jsondispatch}"
            self.mBuildRequest(_path)
            ebLogInfo(f"Sending POST request for jsondispatch: {_path}")
            self.mPerformRequest(_form)

        if options.sop:
            _form = dict()
            if options.jsonconf:
                if isinstance(options.jsonconf, str):
                    _jc = json.loads(options.jsonconf)
                else:
                    _jc = options.jsonconf
            else:
                _jc = json.loads('{}')

            _form['jsonconf'] = _jc

            _path = "/sop"
            self.mBuildRequest(_path)
            self.__cmdtype = _jc.get("cmd", None)

            ebLogInfo(f"Sending POST request for path: {_path}")
            self.mPerformRequest(_form)

        if options.agent:
            if options.agent in REST_API_MAP['agentcmd']:
                self.__cmdtype = 'agentcmd'
                _path = REST_API_MAP['agentcmd'][options.agent]
                self.mBuildRequest(_path)
                self.mPerformRequest(aRetryCount=aRetryCount)
            else:
                self.mBuildErrorResponse('100', 'Invalid or unsupported AGENTCMD command: '+options.agent, 'None')
                self.__jsonresponse = self.__response.mToJson()
                ebLogError(self.__jsonresponse)
                return

        if options.exakms:
            if options.exakms in REST_API_MAP['exakms']:

                self.__cmdtype = 'exakms'
                _form = dict()
                if options.jsonconf:
                    _form.update(options.jsonconf)
                _form['cmd'] = options.exakms

                _path = REST_API_MAP['exakms'][options.exakms]
                self.mBuildRequest(_path)
                self.mPerformRequest(_form)

            else:

                self.mBuildErrorResponse('100', 'Invalid or unsupported EXAKMS command: '+options.exakms, 'None')
                self.__jsonresponse = self.__response.mToJson()
                ebLogError(self.__jsonresponse)
                return

        if options.vmctrl:

            self.__cmdtype = options.vmctrl
            self.__response.mSetCmdType(self.__cmdtype)

            # Check Agent location (local or remote)
            if not options.vmctrl in REST_API_MAP['vmctrl']:
                self.mBuildErrorResponse('100', 'Invalid or unsupported VMCTRL command: '+options.vmctrl, 'None')
                self.__jsonresponse = self.__response.mToJson()
                ebLogError(self.__jsonresponse)
                return

            _path = REST_API_MAP['vmctrl'][self.__cmdtype]
            if options.hostname:
                _path = _path + '?hostname=' + options.hostname
            if options.vmid:
                _path = _path + '?vmid=' + options.vmid
            self.mBuildRequest(_path)
            self.mPerformRequest()

        if options.bmcctrl:
            self.__cmdtype = options.bmcctrl
            self.__response.mSetCmdType(self.__cmdtype)

            if not self.__cmdtype in REST_API_MAP['bmcctrl']:
                self.mBuildErrorResponse('100',
                            'Invalid or unsupported BMCCTRL command: ' +
                            self.__cmdtype, 'None')
                self.__jsonresponse = self.__response.mToJson()
                ebLogError(self.__jsonresponse)
                return
            #_path = REST_API_MAP['bmcctrl'][self.__cmdtype]
            _path = '/BMCCtrl'
            ebLogInfo('_path : %s' % (_path,))

            _form = {}
            _form['cmd'] = self.__cmdtype
            _jc = None
            if options.hostname:
                #_path = _path + '?hostname=' + options.hostname
                _form['hostname'] = options.hostname
            if options.jsonconf:
                _jc = options.jsonconf

            if not _jc:
                self.mBuildErrorResponse('100', 'Invalid BMCCTRL command %s, missing json config' % (self.__cmdtype,), None)
                self.__jsonresponse = self.__response.mToJson()
                ebLogError(self.__jsonresponse)
                return

            _form['jsonconf'] = _jc

            if self.__cmdtype == 'add_customer_info':
                if options.configpath:
                    try:
                        with open(options.configpath) as f:
                            _xml_content = f.read()
                    except Exception as e:
                        ebLogError('Could not read input xml file %s[%s]' % (
                                   options.configpath, e))
                        _xml_content = ''
                else:
                    _xml_content = ''
                if not _xml_content:
                    self.mBuildErrorResponse('100', 'Invalid BMCCTRL command %s, missing xml config' % (self.__cmdtype,), None)
                    self.__jsonresponse = self.__response.mToJson()
                    ebLogError(self.__jsonresponse)
                    return

                _configfile = base64.b64encode(_xml_content.encode('utf8')).decode('utf8')
                _form['xmlconfig'] = _configfile

            self.mBuildRequest(_path)
            ebLogInfo('sending POST request for bmcctrl: path: %s' % (_path,))
            self.mPerformRequest(_form)

        if options.clusterctrl:
            self.__cmdtype = options.clusterctrl
            self.__response.mSetCmdType(self.__cmdtype)

            if not self.__cmdtype in REST_API_MAP['cluctrl']:
                self.mBuildErrorResponse('100', 'Invalid or unsupported CLUCTRL command: '+self.__cmdtype, 'None')
                self.__jsonresponse = self.__response.mToJson()
                ebLogError(self.__jsonresponse)
                return

            # _path = REST_API_MAP['cluctrl'][self.__cmdtype]
            _path = '/CLUCtrl/' + self.__cmdtype

            # _form = {'cmd': self.__cmdtype}
            _form = {}
            if options.steplist:
                # _path = _path + '?steplist=' + options.steplist
                _form['steplist'] = options.steplist
            else:
                # _path = _path + '?steplist=None'
                _form['steplist'] = 'None'
            if options.undo:
                # _path = _path + '?undo=' + options.undo
                _form['undo'] = options.undo
            if options.verbose:
                # _path = _path + '?log_level=VERBOSE'
                _form['log_level'] = 'VERBOSE'
            else:
                # _path = _path + '?log_level=INFO'
                _form['log_level'] = ebGetDefaultLogLevel()
            #bug 29798928: log_level can not be None

            if options.vmid:
                # _path = _path + '?vmid=' + options.vmid
                _form['vmid'] = options.vmid
            else:
                # _path = _path + '?vmid=None'
                _form['vmid'] = 'None'
            if options.scriptname:
                # _path  = _path + '?scriptname='+options.scriptname
                _form['scriptname'] = options.scriptname
            else:
                # _path  = _path + '?scriptname=None'
                _form['scriptname'] = 'None'
            if options.vmcmd:
                # _path = _path + '?vmcmd=' + options.vmcmd
                _form['vmcmd'] = options.vmcmd
            else:
                # _path = _path + '?vmcmd=None'
                _form['vmcmd'] = 'None'
            if options.hostname:
                # _path = _path + '?hostname=' + options.hostname
                _form['hostname'] = options.hostname
            if options.configpath:
                # _path = _path + '?configpath=' + options.configpath
                try:
                    with open(options.configpath) as f:
                        _xml_content = f.read()
                except Exception as e:
                    ebLogError('Could not read input xml file %s[%s]' % (
                        options.configpath, e))
                    _xml_content = ''
            else:
                _xml_content = ''

            if options.exaunitid:
                _form['exaunitid'] = options.exaunitid
                _form["ignore_uuid_check"] = True

            if options.workflowid:
                _form['wf_uuid'] = options.workflowid
                _form["ignore_uuid_check"] = True

            if self.__cmdtype not in ['validate_elastic_shapes','xsvault','infra_vm_states', 'xsput', 'xsget']:
                if not _xml_content:
                    self.mBuildErrorResponse('100', 'Invalid CLUCTRL command %s, missing xml config' % (self.__cmdtype,),
                                         None)
                    self.__jsonresponse = self.__response.mToJson()
                    ebLogError(self.__jsonresponse)
                    return

                _configfile = zlib.compress(_xml_content.encode('utf8'))
                _configfile = base64.b64encode(_configfile).decode('utf8')
                _form['configpath'] = _configfile

            if options.oeda_step:
                # _path = oeda_step + '?oeda_step=' + options.oeda_step
                _form['oeda_step'] = options.oeda_step
            if options.pkeyconf:
                # _path = _path + '?pkeyconf=True'
                _form['pkeyconf'] = options.pkeyconf
            else:
                # _path = _path + '?pkeyconf=False'
                _form['pkeyconf'] = 'False'
            if options.disablepkey:
                # _path = _path + '?disablepkey=True'
                _form['disablepkey'] = 'True'
            else:
                # _path = _path + '?disablepkey=False'
                _form['disablepkey'] = 'False'
            if options.jsonconf:
                # _jc = urllib2.quote(str(options.jsonconf))
                _jc = options.jsonconf
                # _path = _path + '?jsonconf='+_jc
            else:
                # _jc = urllib2.quote('{}')
                _jc = '{}'
                # _path = _path + '?jsonconf='+_jc
            _form['jsonconf'] = _jc
            if options.debug:
                # _path = _path + '?debug=True'
                _form['debug'] = 'True'
            else:
                # _path = _path + '?debug=False'
                _form['debug'] = 'False'
            if options.sshkey:
                # _path = _path + '?sshkey='+options.sshkey
                _form['sshkey'] = options.sshkey
            else:
                # _path = _path + '?sshkey=None'
                _form['sshkey'] = 'None'
            if options.pnode_type:
                # _path = _path +'?pnode_type='+options.pnode_type
                _form['pnode_type'] = options.pnode_type
            if options.patch_file_cells:
                # _path = _path +'?patch_file_cells='+options.patch_file_cells
                _form['patch_file_cells'] = options.patch_file_cells
            if options.patch_files_dom0s:
                # _path = _path +'?patch_files_dom0s='+options.patch_files_dom0s
                _form['patch_files_dom0s'] = options.patch_files_dom0s
            if options.patch_version_dom0s:
                # _path = _path +'?patch_version_dom0s='+options.patch_version_dom0s
                _form['patch_version_dom0s'] = options.patch_version_dom0s
            if options.dgcmd:
                # _path = _path + '?dgcmd=' + options.dgcmd
                _form['dgcmd'] = options.dgcmd
            if options.username:
                # _path = _path + '?username=' + options.username
                _form['username'] = options.username
            if options.enablegilatest:
                # _path = _path + '?enablegilatest=True'
                _form['enablegilatest'] = 'True'
            else:
                # _path = _path + '?enablegilatest=False'
                _form['enablegilatest'] = 'False'
            # _path = _path + '?patchcluinterface=False'
            _form['patchcluinterface'] = 'False'

            if self.__cmdtype == 'diskgroup':
                if options.diskgroupOp:
                    _supported_operations = ['create', 'resize', 'info', 'rebalance', 'drop', 'precheck']
                    _operation = options.diskgroupOp

                    if not _operation or _operation not in _supported_operations:

                        self.mBuildErrorResponse('100', 'Invalid or unsupported DISKGROUP operation: '+_operation, 'None')
                        self.__jsonresponse = self.__response.mToJson()
                        ebLogError(self.__jsonresponse)
                        return

                    if not options.jsonconf:
                        self.mBuildErrorResponse('4051', 'Missing input JSON', 'None')
                        self.__jsonresponse = self.__response.mToJson()
                        ebLogError(self.__jsonresponse)
                        return

                    if not options.hostname:
                        self.mBuildErrorResponse('4053', 'Missing target hostname', 'None')
                        self.__jsonresponse = self.__response.mToJson()
                        ebLogError(self.__jsonresponse)
                        return

            self.mBuildRequest(_path)
            ebLogInfo('sending POST request for cluctrl: path: %s' % (_path,))
            self.mPerformRequest(_form)

        if options.schedgenctrl:
            self.__cmdtype = options.schedgenctrl
            self.__response.mSetCmdType(self.__cmdtype)

            if not self.__cmdtype in REST_API_MAP['schedgenctrl']:
                self.mBuildErrorResponse('100', 'Invalid or unsupported SCGENCTRL command: '+self.__cmdtype, 'None')
                self.__jsonresponse = self.__response.mToJson()
                ebLogError(self.__jsonresponse)
                return

            _path = '/SCGENCtrl/' + self.__cmdtype

            _form = {}

            if options.verbose:
                # _path = _path + '?log_level=VERBOSE'
                _form['log_level'] = 'VERBOSE'
            else:
                # _path = _path + '?log_level=INFO'
                _form['log_level'] = ebGetDefaultLogLevel()

            if options.jsonconf:
                # _jc = urllib2.quote(str(options.jsonconf))
                _jc = options.jsonconf
                # _path = _path + '?jsonconf='+_jc
            else:
                # _jc = urllib2.quote('{}')
                _jc = '{}'
                # _path = _path + '?jsonconf='+_jc
            _form['jsonconf'] = _jc
            if options.debug:
                # _path = _path + '?debug=True'
                _form['debug'] = 'True'
            else:
                # _path = _path + '?debug=False'
                _form['debug'] = 'False'

            self.mBuildRequest(_path)
            ebLogInfo('sending POST request for schedgenctrl: path: %s' % (_path,))
            self.mPerformRequest(_form)

        if options.status:

            self.__cmdtype = 'request_status'
            self.__uuid = options.status
            self.__response.mSetCmdType('request_status')
            _path = REST_API_MAP['status']['request']
            _path = _path + '?uuid=' + options.status
            self.mBuildRequest(_path)
            self.mPerformRequest()

        if options.monitor:

            self.__cmdtype = options.monitor
            self.__response.mSetCmdType(self.__cmdtype)

            if not options.monitor in REST_API_MAP['monitor']:
                self.mBuildErrorResponse('100', 'Invalid or unsupported MONITOR command: '+options.monitor, 'None')
                self.__jsonresponse = self.__response.mToJson()
                ebLogError(self.__jsonresponse)
                return

            _path = REST_API_MAP['monitor'][self.__cmdtype]
            self.mBuildRequest(_path)
            self.mPerformRequest()

        if options.patchclu:
            self.__cmdtype = 'patchclu_' + str(options.patchclu).strip()
            self.__response.mSetCmdType(self.__cmdtype)
            if not self.__cmdtype in REST_API_MAP['patch']:
                self.mBuildErrorResponse('100', 'Invalid or unsupported PATCH command: ' + options.patchclu, 'None')
                self.__jsonresponse = self.__response.mToJson()
                ebLogError(self.__jsonresponse)
                return

            # _path = REST_API_MAP['patch'][self.__cmdtype]
            _path = '/Patch'
            ebLogInfo('_path : %s' % (_path,))

            _form = {'cmd': self.__cmdtype}
            if options.hostname:
                # _path = _path + '?hostname=' + options.hostname
                _form['hostname'] = options.hostname
            if options.jsonconf:
                # _jc = urllib2.quote(str(options.jsonconf))
                # _path = _path + '?jsonconf='+_jc
                _jc = options.jsonconf
                _form['jsonconf'] = _jc

            self.mBuildRequest(_path)
            ebLogInfo('sending POST request for patchclu: path: %s' % (_path,))
            self.mPerformRequest()

        if self.__jsonresponse and getattr(options, 'async'):
            self.mDumpJson()

    def mDumpJson(self):

        options = get_gcontext().mGetArgsOptions()
        self.__jsonresponse = self.__response.mToJson()

        if options.jsonmode:
            ebLogJson(self.__jsonresponse)
        else:
            ebLogInfo(self.__jsonresponse)

        if options.debug:
            try:
                for _line in json.loads(self.__jsonresponse)['body'].split('\n'):
                    if _line: print(_line)
            except:
                pass

    def mGetJsonResponse(self):

        return json.loads(self.__jsonresponse) if self.__jsonresponse else {}

    def mWaitForCompletion(self):
        if self.__cmdtype == None:
            ebLogError('Invalid CMD Type found in ::mWaitForCompletion')
            return

        # If request type is 'request_status' then we have nothing to do.
        if self.__cmdtype == 'request_status':
            return

        if self.__cmdtype == 'agentcmd':
            return

        # Check if Request has been done and if we have received a valid response
        if not self.__response:
            ebLogError('Response not found in ::mWaitForCompletion')
            return
        if self.__response.mGetSuccess() != 'True':
            ebLogError('Request was NOT successful ::mWaitForCompletion')
            ebLogError(self.__response.mToJson())
            ebLogJson(self.__response.mToJson())
            return
        if self.__response.mGetStatus() != 'Pending':
            ebLogInfo('non Async request detected or request is completed ::mWaitForCompletion')
            ebLogJson(self.__response.mToJson())
            return

        # Create a Check Status request and wait for completion
        # TODO: Eventually find a better way than clearing
        _options = get_gcontext().mGetArgsOptions()
        _options.clusterctrl = None
        _options.vmctrl = None
        _options.jsondispatch = None
        _options.patchclu = None
        _options.sop = None
        _options.status = self.__response.mGetUUID()
        while True:
            _client = ebExaClient()
            if self.__hostname != None:
                _client.mSetHostname(self.__hostname)
            _client.mIssueRequest()
            if _client.__response.mGetSuccess() != 'True':
                ebLogError(f'Error detected during get status ::mWaitForCompletion: {_client.__response.mToJson()}')
                break
            if _client.__response.mGetStatus() != 'Pending':
                ebLogInfo('::mWaitForCompletion done for request: '+_options.status)
                break
            # TODO: Get sleep time from config
            time.sleep(10)
            if get_gcontext().mGetArgsOptions().debug:
                ebLogInfo('Timeout reached in ::mWaitForCompletion')

        if _options.debug:
            ebLogJson(_client.__jsonresponse)

        if _options.debug:
            try:
                for _line in json.loads(_client.__jsonresponse)['body'].split('\n'):
                    if _line: print(_line)
            except:
                pass

    def mProcessRequest(self):
        pass

    def mBuidlLocalResponse(self):
        pass

    def mWaitForResponse(self):
        pass

# end of file
