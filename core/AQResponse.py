#!/bin/python
#
# $Header: ecs/exacloud/exabox/core/AQResponse.py /main/4 2026/01/28 05:39:43 kanmanic Exp $
#
# AQResponse.py
#
# Copyright (c) 2025, 2026, Oracle and/or its affiliates.
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
#    kanmanic    06/15/26 - 39560339 - Retry failed AQ response publishes
#    kanmanic    03/17/26 - 37764703 AQ Status Tracker Support
#    kanmanic    01/16/26 - 38854724 - Remove duplicate log printing of AQ
#                           status flag
#    kanmanic    11/19/25 - 37764703 - Add AQ Correlation Id and Message Id
#    aypaul      08/11/25 - Enh#37732728 Update AQ response seding flow with
#                           latest APIs.
#    aararora    05/21/25 - ER 37732745: Send response to ecra using AQ
#    aararora    05/21/25 - Creation
#
from collections import defaultdict
from datetime import datetime
import json
import os
import time
import traceback
import uuid
import threading
import oracledb
from exabox.core.Context import get_gcontext
from exabox.agent.ebJobRequest import ebJobRequest
from exabox.core.Error import retryOnException
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace
from exabox.utils.common import connect_to_ecradb, get_ecradb_details

ERROR_RESPONSE = 'Error'

DEFAULT_QUEUE_TABLE = 'ECRA_EXACLOUD_RAW_QUEUE_TABLE'
DEFAULT_SYNC_QUEUE_NAME = 'SYNCUP_RAW_QUEUE'
AQNAME_SYNCUP_CORRELATION_ID = "ECRA_QUEUE_NAME"
DEFAULT_SYNCUP_LIVELINESS_INTERVAL_SECONDS = 300
AQ_RESPONSE_RETRY_BATCH_SIZE = 50
SYNCUP_LIVELINESS_INTERVAL_SECONDS = DEFAULT_SYNCUP_LIVELINESS_INTERVAL_SECONDS
_LIVELINESS_STOP_EVENT = threading.Event()
_AQNAME_SYNC_STOP_EVENT = threading.Event()
_AQNAME_SYNC_STATE_LOCK = threading.Lock()
_LIVELINESS_THREAD = None
_AQNAME_SYNC_THREAD = None
_AQNAME_SYNC_CONNECTION = None

def _sleep_or_stop(seconds):
    return _LIVELINESS_STOP_EVENT.wait(seconds)

def _is_pushstatus_sync_enabled():
    _ctx = get_gcontext()
    return not _ctx.mCheckConfigOption('ociexacc', 'True') and \
        _ctx.mGetConfigOptions().get('enable_pushstatus_support') == 'True'

def _normalize_sync_action(action):
    if action is None:
        return None
    _action = str(action).upper()
    if _action in ["START", "STOP"]:
        return _action
    return ""

def _format_message_id(message_or_id):
    _msgid = getattr(message_or_id, 'msgid', message_or_id)
    if _msgid is None:
        _msgid = getattr(message_or_id, 'message_id', None)
    if _msgid is None:
        return 'unknown'
    if isinstance(_msgid, memoryview):
        _msgid = _msgid.tobytes()
    if isinstance(_msgid, bytes):
        return _msgid.hex().upper()
    if hasattr(_msgid, 'hex'):
        try:
            return _msgid.hex().upper()
        except TypeError:
            pass
    return str(_msgid)

def _ensure_sync_queue_with_retry(sync_queue, worker_label, exit_label, stop_aware=False):
    ensure_attempts = 3
    ensure_delay_seconds = 3
    for attempt in range(1, ensure_attempts + 1):
        if stop_aware and _LIVELINESS_STOP_EVENT.is_set():
            ebLogInfo("SYNCUP_AQ_LIVELINESS worker stopped before start.")
            return False
        try:
            with connect_to_ecradb() as connection:
                if not connection:
                    ebLogWarn(f"SYNCUP_AQ {worker_label} cannot start: ECRA DB connection unavailable.")
                else:
                    ebLogInfo(f"SYNCUP_AQ {worker_label} ensuring queue {sync_queue} on table {DEFAULT_QUEUE_TABLE}.")
                    _ensure_sync_queue_exists(connection, sync_queue, DEFAULT_QUEUE_TABLE)
                    ebLogInfo(f"SYNCUP_AQ {worker_label} queue ensured: {sync_queue}.")
                    return True
        except Exception as ex:
            ebLogError(f"SYNCUP_AQ {worker_label} ensure attempt {attempt} failed: {ex}")
        if attempt < ensure_attempts:
            if stop_aware:
                if _sleep_or_stop(ensure_delay_seconds):
                    ebLogInfo("SYNCUP_AQ_LIVELINESS worker stopped during ensure.")
                    return False
            else:
                time.sleep(ensure_delay_seconds)
    ebLogInfo(f"SYNCUP_AQ {worker_label} cannot start after retries. Exiting {exit_label}.")
    return False

def _start_aqname_sync_worker(target=None, name="AQNameSyncQueueWorker"):
    global _AQNAME_SYNC_THREAD
    if _AQNAME_SYNC_THREAD and _AQNAME_SYNC_THREAD.is_alive():
        return _AQNAME_SYNC_THREAD
    _AQNAME_SYNC_STOP_EVENT.clear()
    worker_target = target or mSyncUpEcraQueueNameWithRequest
    _AQNAME_SYNC_THREAD = threading.Thread(
        target=worker_target,
        name=name,
        daemon=True
    )
    _AQNAME_SYNC_THREAD.start()
    ebLogInfo("SYNCUP_AQ_NAME worker started.")
    return _AQNAME_SYNC_THREAD

def _start_liveliness_worker():
    global _LIVELINESS_THREAD
    if _LIVELINESS_THREAD and _LIVELINESS_THREAD.is_alive():
        return
    _LIVELINESS_STOP_EVENT.clear()
    _LIVELINESS_THREAD = threading.Thread(
        target=mSyncUpRequestLivelinessWithEcra,
        name="AQ-SYNCUP-LIVELINESS",
        daemon=True
    )
    _LIVELINESS_THREAD.start()
    ebLogInfo("SYNCUP_AQ_LIVELINESS worker started.")

def _stop_liveliness_worker():
    if _LIVELINESS_THREAD and _LIVELINESS_THREAD.is_alive():
        _LIVELINESS_STOP_EVENT.set()
        ebLogInfo("SYNCUP_AQ_LIVELINESS worker stop requested.")

def _stop_aqname_sync_worker():
    global _AQNAME_SYNC_CONNECTION
    _thread = _AQNAME_SYNC_THREAD
    if not (_thread and _thread.is_alive()):
        return

    _AQNAME_SYNC_STOP_EVENT.set()
    ebLogInfo("SYNCUP_AQ_NAME worker stop requested.")
    with _AQNAME_SYNC_STATE_LOCK:
        _connection = _AQNAME_SYNC_CONNECTION
    if _connection is not None:
        try:
            _connection.cancel()
        except Exception as ex:
            ebLogWarn(f"SYNCUP_AQ_NAME worker cancel failed during shutdown: {ex}")
        try:
            _connection.close()
        except Exception as ex:
            ebLogWarn(f"SYNCUP_AQ_NAME worker close failed during shutdown: {ex}")
    _thread.join(timeout=5)
    if _thread.is_alive():
        ebLogWarn("SYNCUP_AQ_NAME worker is still alive after forced shutdown interrupt.")

def _enqueue_pending_liveliness_once(db_obj, sync_queue, aq_name_filter=None):
    query = """
        SELECT uuid, aq_name
        FROM requests
        WHERE status='Pending'
          AND aq_name IS NOT NULL AND aq_name != ''
    """
    query_args = []
    if aq_name_filter:
        query += " AND aq_name = %(1)s"
        query_args = [aq_name_filter]

    grouped_pending = defaultdict(set)
    rows = db_obj.mFetchAll(query, query_args)
    for row in rows:
        if not row or len(row) < 2:
            continue
        _uuid = row[0]
        _aq_name = row[1]
        if not _uuid or not _aq_name:
            continue
        grouped_pending[_aq_name].add(_uuid)

    if not grouped_pending:
        return 0, 0

    with connect_to_ecradb() as connection:
        if not connection:
            ebLogWarn("SYNCUP_AQ_LIVELINESS pending enqueue skipped: ECRA DB connection unavailable.")
            return None, None

        queue = connection.queue(sync_queue)
        enqueued = 0
        for aq_name, pending_uuid_set in grouped_pending.items():
            pending_uuids = list(pending_uuid_set)
            if not pending_uuids:
                continue
            payload = json.dumps({
                "aq_name": aq_name,
                "pending": pending_uuids
            }).encode('utf-8')
            msgprop = connection.msgproperties(payload=payload, correlation=aq_name, expiration=30)
            queue.enqone(msgprop)
            ebLogInfo(
                f"SYNCUP_AQ_LIVELINESS pending enqueue aq_name={aq_name} count={len(pending_uuids)} msgid={_format_message_id(msgprop)}")
            enqueued += len(pending_uuids)

        connection.commit()
        ebLogInfo(
            f"SYNCUP_AQ_LIVELINESS pending enqueue processed for {enqueued} request(s) across {len(grouped_pending)} queue(s)")
        return enqueued, len(grouped_pending)

def _retry_failed_responses_once(db_obj, batch_size=AQ_RESPONSE_RETRY_BATCH_SIZE):
    _publish_once = mUpdateResponseToEcra(lambda _db_obj, _req: None)
    rows = db_obj.mGetFailedAQResponses(batch_size) or []
    retry_count = 0
    for row in rows:
        if not row:
            continue
        _uuid = row[0]
        if not _uuid:
            continue
        _publish_once(db_obj, _uuid)
        retry_count += 1
    if retry_count:
        ebLogInfo(f"RESPONSE_AQ retry processed for {retry_count} request(s).")
    return retry_count

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
                ebLogWarn(f"Received uuid {_uuid} is not valid and is not present in exacloud DB. Not sending response to ecra.")
                return (None, None)
        elif _request and is_valid_uuid(_request):
            _uuid = _request
            _request_obj = ebJobRequest(None,{}, aDB=_ebExacloudDB_obj)
            _request_obj.mLoadRequestFromDB(_uuid)
            # Validate if the given request uuid exists in the DB
            if _uuid != _request_obj.mGetUUID():
                ebLogWarn(f"Received uuid {_uuid} is not valid and is not present in exacloud DB. Not sending response to ecra.")
                return (None, None)
        else:
            ebLogTrace(f"Request uuid for the given request could not be obtained. "\
                        "Not sending response to ecra.")
            return (None, None)
        ebLogTrace(f"UUID obtained is {_uuid}. UUID from request object is {_request_obj.mGetUUID()}.")
    except Exception as ex:
        ebLogWarn(f"Could not obtain request object details for request {_request}.")
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
            ebLogWarn(f"ECRA DB details could not be obtained for request id {_uuid}.")
            return None
    except Exception as ex:
        _ebExacloudDB_obj.mUpdateResponseSent(_uuid, ERROR_RESPONSE)
        ebLogWarn(f"Could not obtain db details from registry for request id {_uuid}.")
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
        if not _aq_name:
            raise Exception('Advanced queue name is unavailable.')
    except Exception as ex:
        _ebExacloudDB_obj.mUpdateResponseSent(_uuid, ERROR_RESPONSE)
        ebLogWarn(f"Could not obtain Advanced queue name for request id {_uuid}.")
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
        # Step 2 - Combined guard: skip for ExaCC or when pushstatus support disabled (no logs)
        if not _is_pushstatus_sync_enabled():
            return
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
            ebLogTrace(f"RESPONSE_AQ publish skipped because request details are unavailable for request {_request}.")
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
            ebLogWarn(f"Response data could not be prepared for request id {_uuid}.")
            ebLogTrace(f"Exception in preparing response data: {traceback.format_exc()}.")
            return
        try:
            # Step 8 - Initialize connection to Oracle DB (ECRA DB)
            with connect_to_ecradb() as connection:
                if not connection:
                    raise Exception('ECRA DB connection unavailable.')
                # Step 9 - Send the response data to ECRA
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
                ebLogInfo(f"Response message sent for request id {_uuid} to queue {_aq_name}:{_msg_prp.msgid.hex().upper()} at time {_current_timestamp} size: {_payload_size}.")
        except Exception as ex:
            _ebExacloudDB_obj.mUpdateResponseSent(_uuid, ERROR_RESPONSE)
            ebLogWarn(f"Could not send the response to ecra for request id {_uuid} queue {_aq_name}: {ex}.")
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

def mSyncUpEcraQueueNameWithRequest():
    """
    Dequeue AQ SYNCUP messages from ECRA and update aq_name in exabox requests.
    Expected payload:
      {"aq_name": "<queue>", "status_uuids": [...], "action": "START|STOP",
       "liveliness_interval_seconds": <seconds>}
    """
    # Skip for ExaCC or when pushstatus support disabled
    if not _is_pushstatus_sync_enabled():
        return

    try:
        from exabox.core.DBStore3 import ebExacloudDB
    except Exception as ex:
        ebLogWarn(f"Could not initialize exabox DB handler for SYNCUP_AQ: {ex}")
        return

    global _AQNAME_SYNC_CONNECTION
    _db = ebExacloudDB()
    _sync_queue = DEFAULT_SYNC_QUEUE_NAME
    _publish_once = mUpdateResponseToEcra(lambda _db_obj, _req: None)

    if not _ensure_sync_queue_with_retry(_sync_queue, "dequeue", "sync worker"):
        return

    backoff_seconds = 3
    backoff_max_seconds = 30
    dequeue_backoff_seconds = 3
    dequeue_backoff_max_seconds = 30
    global SYNCUP_LIVELINESS_INTERVAL_SECONDS
    while not _AQNAME_SYNC_STOP_EVENT.is_set():
        try:
            with connect_to_ecradb() as connection:
                with _AQNAME_SYNC_STATE_LOCK:
                    _AQNAME_SYNC_CONNECTION = connection
                if not connection:
                    ebLogWarn("SYNCUP_AQ_NAME dequeue skipped: ECRA DB connection unavailable.")
                    if _AQNAME_SYNC_STOP_EVENT.wait(backoff_seconds):
                        break
                    backoff_seconds = min(backoff_seconds * 2, backoff_max_seconds)
                    continue
                backoff_seconds = 3

                queue = connection.queue(_sync_queue)
                ebLogInfo(f"SYNCUP_AQ_NAME dequeue started on queue {_sync_queue}.")
                queue.deqoptions.wait = oracledb.DEQ_WAIT_FOREVER
                
                while not _AQNAME_SYNC_STOP_EVENT.is_set():
                    try:
                        queue.deqoptions.correlation = AQNAME_SYNCUP_CORRELATION_ID
                        msg = queue.deqone()
                    except Exception as ex:
                        if _AQNAME_SYNC_STOP_EVENT.is_set():
                            ebLogInfo("SYNCUP_AQ_NAME dequeue interrupted during shutdown.")
                            break
                        # ORA-25228: timeout or end-of-fetch during dequeue
                        if "ORA-25228" in str(ex):
                            continue
                        ebLogWarn(f"SYNCUP_AQ_NAME  dequeue failed: {ex}")
                        time.sleep(dequeue_backoff_seconds)
                        dequeue_backoff_seconds = min(dequeue_backoff_seconds * 2, dequeue_backoff_max_seconds)
                        break
                    if not msg:
                        continue
                    dequeue_backoff_seconds = 3
                    payload = msg.payload
                    if payload is None:
                        ebLogWarn(
                            f"SYNCUP_AQ_NAME message {_format_message_id(msg)} has no payload, committing and skipping.")
                        connection.commit()
                        continue
                    if isinstance(payload, memoryview):
                        payload = payload.tobytes()
                    if isinstance(payload, bytes):
                        payload = payload.decode('utf-8')
                    try:
                        data = json.loads(payload)
                    except Exception:
                        _payload_size = len(payload) if hasattr(payload, "__len__") else "unknown"
                        ebLogWarn(
                            f"SYNCUP_AQ_NAME  payload is not valid JSON, skipping. msgid={_format_message_id(msg)} payload_size={_payload_size}")
                        connection.commit()
                        continue

                    _aq_name = data.get('aq_name')
                    _liveliness_interval_seconds = data.get('liveliness_interval_seconds')
                    _action = data.get('action')
                    _normalized_action = _normalize_sync_action(_action)
                    status_uuids = data.get('status_uuids', [])
                    if not isinstance(status_uuids, list):
                        ebLogWarn(f"SYNCUP_AQ_NAME  status_uuids is not a list for action {_action} queue {_aq_name}: {status_uuids}")
                        status_uuids = []

                    if _liveliness_interval_seconds is not None:
                        try:
                            _interval_seconds = int(_liveliness_interval_seconds)
                            if _interval_seconds > 0:
                                SYNCUP_LIVELINESS_INTERVAL_SECONDS = _interval_seconds
                                ebLogInfo(f"SYNCUP_AQ_NAME  liveliness_interval_seconds set to {_interval_seconds} seconds.")
                        except Exception:
                            ebLogWarn(
                                f"SYNCUP_AQ_NAME  invalid liveliness_interval_seconds={_liveliness_interval_seconds}, ignoring.")

                    if _action is not None and not _normalized_action:
                        ebLogWarn(f"SYNCUP_AQ_NAME  invalid action '{_action}' for queue {_aq_name}, skipping.")
                        connection.commit()
                        continue

                    if not _aq_name:
                        ebLogWarn(f"SYNCUP_AQ_NAME  no aq_name present in the payload '{data}'")
                        connection.commit()
                        continue

                    _status_uuids = status_uuids
                    if len(_status_uuids) == 0:
                        ebLogInfo(f"SYNCUP_AQ_NAME  no status_uuids present for action {_normalized_action} queue {_aq_name}, skipping.")
                        connection.commit()
                        continue

                    if _normalized_action == "STOP":
                        for _uuid in _status_uuids:
                            _db.mUpdateAqName(_uuid, None)
                        ebLogInfo(f"SYNCUP_AQ_NAME STOP cleared aq_name for {len(_status_uuids)} status uuid(s) from queue {_aq_name}.")
                    elif _normalized_action == "START":
                        for _uuid in _status_uuids:
                            _existing_aq_name = None
                            try:
                                _row = _db.mGetCompleteRequest(_uuid)
                                if _row and len(_row) >= 17:
                                    _existing_aq_name = _row[16]
                            except Exception as ex:
                                ebLogWarn(f"SYNCUP_AQ_NAME  unable to fetch existing aq_name for uuid {_uuid}: {ex}")
                            if not _existing_aq_name or _existing_aq_name != _aq_name:
                                _db.mUpdateAqName(_uuid, _aq_name)
                                ebLogInfo(f"SYNCUP_AQ_NAME RELOAD {_uuid} aq_name is set to {_aq_name}. It was {_existing_aq_name}.")
                            else:
                                ebLogInfo(f"SYNCUP_AQ_NAME RELOAD {_uuid} aq_name already set to {_aq_name}.")
                            ebLogInfo(f"SYNCUP_AQ_NAME RELOAD {_uuid} current status is published to the AQ queue.")
                            _publish_once(_db, _uuid)
                    connection.commit()
                    ebLogInfo(
                        f"SYNCUP_AQ_NAME  processed total={len(_status_uuids)} for queue {_aq_name}.")

        except Exception as ex:
            if _AQNAME_SYNC_STOP_EVENT.is_set():
                ebLogInfo("SYNCUP_AQ_NAME worker stopped during shutdown.")
                break
            ebLogWarn(f"SYNCUP_AQ_NAME processing failed: {ex}")
            ebLogTrace(f"Exception in SYNCUP_AQ_NAME processing: {traceback.format_exc()}.")
        finally:
            with _AQNAME_SYNC_STATE_LOCK:
                _AQNAME_SYNC_CONNECTION = None
    ebLogInfo("SYNCUP_AQ_NAME worker stopped.")

def mSyncUpRequestLivelinessWithEcra():
    """
    Periodically enqueue pending request UUIDs to AQ SYNCUP queue so ECRA can
    verify tracked requests are still pending in exabox.
    Payload: {"aq_name": "<queue>", "pending": [...]}
    """
    # Skip for ExaCC or when pushstatus support disabled
    if not _is_pushstatus_sync_enabled():
        return

    try:
        from exabox.core.DBStore3 import ebExacloudDB
    except Exception as ex:
        ebLogWarn(f"Could not initialize exabox DB handler for SYNCUP_AQ_LIVELINESS enqueue: {ex}")
        return

    _db = ebExacloudDB()
    _sync_queue = DEFAULT_SYNC_QUEUE_NAME

    if not _ensure_sync_queue_with_retry(_sync_queue, "pending enqueue", "enqueue worker", stop_aware=True):
        return

    while True:
        if _LIVELINESS_STOP_EVENT.is_set():
            ebLogInfo("SYNCUP_AQ_LIVELINESS worker stopped.")
            break
        try:
            _retry_failed_responses_once(_db)
        except Exception as ex:
            ebLogWarn(f"RESPONSE_AQ retry processing failed: {ex}")
            ebLogTrace(f"Exception in RESPONSE_AQ retry processing: {traceback.format_exc()}.")

        try:
            enqueued, _queue_count = _enqueue_pending_liveliness_once(_db, _sync_queue)
            if enqueued is None:
                if _sleep_or_stop(SYNCUP_LIVELINESS_INTERVAL_SECONDS):
                    ebLogInfo("SYNCUP_AQ_LIVELINESS worker stopped during backoff.")
                    break
                continue

            if enqueued == 0:
                if _sleep_or_stop(SYNCUP_LIVELINESS_INTERVAL_SECONDS):
                    ebLogInfo("SYNCUP_AQ_LIVELINESS worker stopped during idle wait.")
                    break
                continue
        except Exception as ex:
            ebLogWarn(f"SYNCUP_AQ_LIVELINESS enqueue processing failed: {ex}")
            ebLogTrace(f"Exception in SYNCUP_AQ_LIVELINESS enqueue processing: {traceback.format_exc()}.")

        if _sleep_or_stop(SYNCUP_LIVELINESS_INTERVAL_SECONDS):
            ebLogInfo("SYNCUP_AQ_LIVELINESS worker stopped during sleep.")
            break

def _ensure_sync_queue_exists(connection, queue_name, queue_table):
    if not queue_name or not queue_table:
        ebLogWarn(f"SYNCUP_AQ queue ensure skipped because queue_name={queue_name} queue_table={queue_table}.")
        return
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(1) FROM user_queue_tables WHERE queue_table = :1",
                           [queue_table.upper()])
            table_exists = cursor.fetchone()[0] > 0
            if not table_exists:
                ebLogInfo(f"SYNCUP_AQ queue table {queue_table} does not exist, creating.")
                cursor.execute(
                    "BEGIN DBMS_AQADM.CREATE_QUEUE_TABLE(queue_table => :1, queue_payload_type => 'RAW'); END;",
                    [queue_table])
            cursor.execute("SELECT COUNT(1) FROM user_queues WHERE name = :1",
                           [queue_name.upper()])
            queue_exists = cursor.fetchone()[0] > 0
            if not queue_exists:
                ebLogInfo(f"SYNCUP_AQ queue {queue_name} does not exist, creating on {queue_table}.")
                cursor.execute(
                    "BEGIN DBMS_AQADM.CREATE_QUEUE(queue_name => :1, queue_table => :2); END;",
                    [queue_name, queue_table])
            cursor.execute(
                "BEGIN DBMS_AQADM.START_QUEUE(queue_name => :1, enqueue => TRUE, dequeue => TRUE); END;",
                [queue_name])
            connection.commit()
        ebLogInfo(f"SYNCUP_AQ queue ensured: {queue_name} on {queue_table}.")
    except Exception as ex:
        try:
            connection.rollback()
        except Exception as rollback_ex:
            ebLogWarn(f"Failed to rollback SYNCUP_AQ queue ensure for {queue_name}: {rollback_ex}")
        ebLogWarn(f"Failed to ensure SYNCUP_AQ queue {queue_name} on table {queue_table}: {ex}")
        raise
