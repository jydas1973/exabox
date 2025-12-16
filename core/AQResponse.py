#!/bin/python
#
# $Header: ecs/exacloud/exabox/core/AQResponse.py /main/3 2025/11/26 09:02:40 kanmanic Exp $
#
# AQResponse.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      AQResponse.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    kanmanic    11/19/25 - 37764703 - Add AQ Correlation Id and Message Id
#    aypaul      08/11/25 - Enh#37732728 Update AQ response seding flow with
#                           latest APIs.
#    aararora    05/21/25 - ER 37732745: Send response to ecra using AQ
#    aararora    05/21/25 - Creation
#
from datetime import datetime
import json
import os
import time
import traceback
import uuid
from exabox.core.Context import get_gcontext
from exabox.agent.ebJobRequest import ebJobRequest
from exabox.core.Error import retryOnException
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace
from exabox.utils.common import connect_to_ecradb, get_ecradb_details

ERROR_RESPONSE = 'Error'

def is_valid_uuid(aUUID):
    try:
        uuid.UUID(str(aUUID))
        return True
    except ValueError:
        return False

def getRequestDetails(aRequest, aDBObject):
    """
    Get request details
    """
    _request = aRequest
    _ebExacloudDB_obj = aDBObject
    _uuid = None
    _request_obj = None
    try:
        if _request and isinstance(_request, ebJobRequest):
            _request_obj = _request
            _uuid = _request_obj.mGetUUID()
            # Validate if the given request object exists in the DB
            if not _ebExacloudDB_obj.mGetCompleteRequest(_uuid):
                ebLogWarn(f"Received uuid is not valid and is not present in exacloud DB. Not sending response to ecra.")
                return (None, None)
        elif _request and is_valid_uuid(_request):
            _uuid = _request
            _request_obj = ebJobRequest(None,{}, aDB=_ebExacloudDB_obj)
            _request_obj.mLoadRequestFromDB(_uuid)
            # Validate if the given request uuid exists in the DB
            if _uuid != _request_obj.mGetUUID():
                ebLogWarn(f"Received uuid is not valid and is not present in exacloud DB. Not sending response to ecra.")
                return (None, None)
        else:
            ebLogTrace(f"Request uuid for the given request could not be obtained. "\
                        "Not sending response to ecra.")
            return (None, None)
        ebLogTrace(f"UUID obtained is {_uuid}. UUID from request object is {_request_obj.mGetUUID()}.")
    except Exception as ex:
        ebLogWarn(f"Could not obtain request object details.")
        ebLogTrace(f"Exception in obtaining request object details: {traceback.format_exc()}.")
        return (None, None)
    return (_uuid, _request_obj)

def getEcraDBDetails(aUUID, aDBObject):
    """
    Get ecra db details dictionary
    """
    _uuid = aUUID
    _ebExacloudDB_obj = aDBObject
    try:
        _ecradb_details_dict = get_ecradb_details()
        if len(_ecradb_details_dict.keys()) == 0:
            _ebExacloudDB_obj.mUpdateResponseSent(_uuid, ERROR_RESPONSE)
            ebLogWarn("ECRA DB details could not be obtained.")
            return None
    except Exception as ex:
        _ebExacloudDB_obj.mUpdateResponseSent(_uuid, ERROR_RESPONSE)
        ebLogWarn(f"Could not obtain db details from registry.")
        ebLogTrace(f"Exception in obtaining db details from registry: {traceback.format_exc()}.")
        return None
    return _ecradb_details_dict

def mGetAQName(aUUID, aDBObject, aRequestObj):
    """
    Get the AQ name sent from ecra
    """
    _uuid = aUUID
    _ebExacloudDB_obj = aDBObject
    _request_obj = aRequestObj
    try:
        _aq_name = _request_obj.mGetAqName()
        if _aq_name == '':
            raise Exception('Advanced queue name is empty.')
    except Exception as ex:
        _ebExacloudDB_obj.mUpdateResponseSent(_uuid, ERROR_RESPONSE)
        ebLogWarn(f"Could not obtain Advanced queue name.")
        ebLogTrace(f"Exception in obtaining AQ name: {traceback.format_exc()}.")
        return None
    return _aq_name

def mUpdateResponseToEcra(func):
    """
    Decorator method to send response to ECRA from exacloud using AQ.
    To maintain consistency - the DBStore method calling this decorator
    should have 1st argument as ebExacloudDB object, 2nd argument as request
    object or request uuid.
    This decorator also reads aInternal argument - if found to be True,
    it will not send response to ecra for that request update.
    """
    @retryOnException(max_times=3)
    def commit_transaction(connection):
        connection.commit()
    def wrapper(*args, **kwargs):
        # Step 1 - Call the function which is wrapped first
        func(*args, **kwargs)
        # Step 2 - Check for pushstatus support from exabox.conf
        if get_gcontext().mCheckConfigOption('ociexacc', 'True'):
            ebLogWarn("AQ support is disabled for ExaCC deployments.")
            return
        if not (get_gcontext().mGetConfigOptions()['enable_pushstatus_support'] == 'True'):
            ebLogWarn("AQ support for pushing status from exacloud to ecra is disabled")
            return
        ebLogTrace("AQ support for pushing status from exacloud to ecra is enabled")
        _ebExacloudDB_obj = args[0]
        # The argument at position 1 is either a request object OR the request uuid
        _request = args[1]
        # Step 3 - Check if the call needs to be propagated to ecra
        if kwargs and 'aInternal' in kwargs:
            aInternal = kwargs['aInternal']
            if aInternal is True:
                ebLogTrace("This is an internal call to update exacloud DB and is not required to be propagated to ecra.")
                return
        # Step 4 - Get the request details - uuid and the request object
        _uuid, _request_obj = getRequestDetails(_request, _ebExacloudDB_obj)
        if not _uuid or not _request_obj:
            return
        # Step 5 - Get the ecra db details dictionary
        _ecradb_details_dict = getEcraDBDetails(_uuid, _ebExacloudDB_obj)
        if not _ecradb_details_dict:
            return
        # Step 6 - Get the AQ Name stored in request object - obtained from payload
        _aq_name = mGetAQName(_uuid, _ebExacloudDB_obj, _request_obj)
        if not _aq_name:
            return
        # Step 7 - Get the response data to be sent to ecra
        try:
            _response_data = mGetResponseData(_uuid)
            if not _response_data:
                raise Exception('Response data is None.')
        except Exception as ex:
            _ebExacloudDB_obj.mUpdateResponseSent(_uuid, ERROR_RESPONSE)
            ebLogWarn(f"Response data could not be prepared.")
            ebLogTrace(f"Exception in preparing response data: {traceback.format_exc()}.")
            return
        # Step 8 - Initialize connection to Oracle DB (ECRA DB)
        with connect_to_ecradb() as connection:
            if not connection:
                return
            # Step 9 - Send the response data to ECRA
            try:
                _payload_data = [_response_data]
                _msg_prp = None
                _payload_size = 0
                ebLogTrace(f"Enqueuing messages for sending status response to ECRA for request id {_uuid}.")
                with connection.cursor() as cursor:
                    queue = connection.queue(_aq_name)
                    for data in _payload_data:
                        _payload = json.dumps(data).encode('utf-8')
                        _payload_size = len(_payload)
                        _msg_prp = connection.msgproperties(payload=_payload, correlation=_uuid)
                        queue.enqone(_msg_prp)
                commit_transaction(connection)
                _current_timestamp = datetime.now()
                _ebExacloudDB_obj.mUpdateResponseSent(_uuid, _current_timestamp)
                ebLogInfo(f"Response message sent for request id {_uuid}:{_msg_prp.msgid.hex().upper()} at time {_current_timestamp} size: {_payload_size}.")
            except Exception as ex:
                _ebExacloudDB_obj.mUpdateResponseSent(_uuid, ERROR_RESPONSE)
                ebLogWarn(f"Could not send the response to ecra.")
                ebLogTrace(f"Exception in sending response to ecra: {traceback.format_exc()}.")
                return
    return wrapper

def mGetResponseData(aUUID):
    """
    Method to prepare response data from /Status call to be sent to ECRA
    using AQ.
    """
    # Imports moved inside this method to avoid circular import exception
    from exabox.agent.HTTPRequest import HttpRequest
    from exabox.agent.Agent import ebRestHttpListener

    # aConfig=None in ebRestHttpListener ensures the base class for http
    # listener is not initialized.
    _server_class = ebRestHttpListener(aConfig=None)
    _endpoint = '/Status'
    _fullpath = f'{_endpoint}/{aUUID}'
    _method = 'GET'
    # Here, we are trying to mimic Status call to agent but not actually calling
    # the agent to process anything.
    # Example of parameters below:
    # _fullpath: /Status/bb8325f4-30b6-11f0-9a2a-020017135d89
    # _method: GET
    _httpreq = HttpRequest(_fullpath, _method, None, None)
    _httpreq.extractParams(_server_class, None)
    # Since this is an internal call and not an actual http call, 
    # unauthenticated request is ok
    _status_callback = _server_class.mGetStatusCallback(aAuthenticated=False)
    _response = _status_callback.executeRequest(_httpreq)
    ebLogTrace(f"Response obtained is {_response}.")
    return _response