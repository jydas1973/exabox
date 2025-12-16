"""
 Copyright (c) 2017, 2022, Oracle and/or its affiliates.

NAME:
    Exawatcher - Integration with exawatcher logging mechanism.

FUNCTION:
    Methods to retreive and list exawatcher logs.

NOTE:
    None
"""

import time
import tarfile
import glob
import re
import os
import json
import datetime
import subprocess
import calendar
import shutil

from exabox.tools.AttributeWrapper import wrapStrBytesFunctions
from exabox.log.LogMgr import ebLogDiag, ebLogWarn, ebLogInfo, ebLogError
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.core.DBStore import ebGetDefaultDB

class exaBoxExaWatcher(object):

    def __init__(self, aCluCtrlObject):
        self.__ecc = aCluCtrlObject

    def mCollectExaWatcherLogs(self, aOptions):
        _supported_target_types = ['dom0', 'domU', 'cell']
        _log_file_list = list()
        _list_str = None
        _fromtime = None
        _totime = None
        _filter = None
        _target_types = None
        _targets = None
        _tar_file = None
        _file_expiry_time = 0
        _etime = None
        _final_target_types = ['dom0', 'domU', 'cell'] # collect from all targets by default.
        _result = {}

        if aOptions is not None and aOptions.jsonconf is not None:
            _jconf = aOptions.jsonconf
            _jconf_keys = list(_jconf.keys())
            if _jconf_keys is not None:
                if 'fromtime' in _jconf_keys:
                    _fromtime = _jconf['fromtime']
                if 'totime' in _jconf_keys:
                    _totime = _jconf['totime']
                if 'filter' in _jconf_keys:
                    _filter = _jconf['filter']
                if 'targettypes' in _jconf_keys:
                    _target_types = _jconf['targettypes']
                if 'targets' in _jconf_keys:
                    _targets = _jconf['targets']

        if _target_types is not None:
            _final_target_types = _target_types.split(',')
            for _target in _final_target_types:
                if _target not in _supported_target_types:
                    ebLogWarn('Unknown log type %s' % _target)
                    _final_target_types.remove(_target)

        #If all input types in json are wrong, retreive all nodes !
        if not _final_target_types:
            _final_target_types = ['dom0', 'domU', 'cell']

        ebLogInfo('_final_target_types is : %s ' % _final_target_types)
        _all_dom0s = set()
        _all_domUs = set()
        _all_cells = set()
        self.mGetNodeList(_all_dom0s, _all_domUs, _all_cells)

        _target_nodes = []
        if 'dom0' in _final_target_types:
            _target_nodes.extend(_all_dom0s)
        if 'domU' in _final_target_types:
            _target_nodes.extend(_all_domUs)
        if 'cell' in _final_target_types:
            _target_nodes.extend(_all_cells)

        # If there any any hosts explicitly mentioned, add them too to the list
        if _targets is not None:
            _target_nodes.extend((_targets.split(',')))
        _target_nodes = list(set(_target_nodes))

        _db = ebGetDefaultDB()
        _sqldata = (self.__ecc.mGetUUID(), None, _filter, _fromtime, _totime, _target_types, _targets, None, "PENDING")
        _db.mSetWatcherRequest(_sqldata)

        _max_exalog_age = self.__ecc.mCheckConfigOption('max_exawatcher_log_age_in_hours')
        if (not _max_exalog_age) or _max_exalog_age == '' or (int(_max_exalog_age) == 0):
            ebLogInfo('Setting a default value of 24 hours for _max_exalog_age')
            _max_exalog_age = 24*60*60
        else:
            _max_exalog_age = int(_max_exalog_age)*60*60
        ebLogInfo('_max_exalog_age is : %s' % (_max_exalog_age))

        for _node in _target_nodes:
            if not self.__ecc.mPingHost(_node):
                ebLogWarn('getExaWatcherLog: host %s not reachable. skipping log collection' % (_node))
                continue
            ebLogInfo('getExaWatcherLog collecting exaWatcher logs from host: %s' % (_node))
            self.mCollectLog(_node, _log_file_list, _fromtime, _totime, _filter, _max_exalog_age)

        if _log_file_list:
            _tar_file = ArchiveLogs(_log_file_list)
            _create_time = os.stat(_tar_file).st_mtime
            _file_expiry_time = _create_time + _max_exalog_age
            _etime = time.strftime('%H:%M:%S %Y-%m-%d', time.localtime(_file_expiry_time))
            ebLogInfo('exawatcher log expiry time is : %s' % (_etime))

        _result.update({'exawatcher log location' : _tar_file})
        _reqobj = self.__ecc.mGetRequestObj()
        if _reqobj is not None:
            _reqobj.mSetData(json.dumps(_result, sort_keys=True))
            _db.mUpdateRequest(_reqobj)

        _db.mUpdateWatcher(self.__ecc.mGetUUID(), _tar_file, "DONE", float(_file_expiry_time))
        ebLogInfo('exawatcher log files are in : %s' % (_tar_file))


    def mListExaWatcherLogs(self, aOptions):
        _result = {}
        _rcount = None
        if aOptions is not None and aOptions.jsonconf is not None:
            _jconf = aOptions.jsonconf
            _jconf_keys = list(_jconf.keys())
            if _jconf_keys is not None:
                if 'retrieval-history' in _jconf_keys:
                    _rcount = _jconf['retrieval-history']
        if _rcount is None:
            #By default, lets retreive last 10 log details.
            _rcount = 10

        _db = ebGetDefaultDB()
        _rc, _rowdata = _db.mGetWatcherLog(_rcount)

        if not _rc:
            _resp = []
            for i in range(len(_rowdata)):
                _logdata = {}
                _logdata['log-location'] = _rowdata[i][0]
                _logdata['filter'] = _rowdata[i][1]
                _logdata['from-time'] = _rowdata[i][2]
                if _rowdata[i][3]:
                    _strtime = time.strftime('%H:%M:%S %Y-%m-%d', time.localtime(float(_rowdata[i][3])))
                    _logdata['expiry-time'] = _strtime
                else:
                    _logdata['expiry-time'] = None
                _logdata['status'] = _rowdata[i][4]
                _resp.append(_logdata)
            ebLogInfo('listExaWatcherLog response : %s' % _resp)
            _result.update({'exawatcher logs list' : _resp})
        _reqobj = self.__ecc.mGetRequestObj()
        if _reqobj is not None:
            _reqobj.mSetData(json.dumps(_result, sort_keys=True))
            ebLogInfo("mCollectExaWatcherLogs: Updating request id : %s" % self.__ecc.mGetUUID())
            _db.mUpdateRequest(_reqobj)


    def mCollectLog(self, aHost, _log_file_list, _fromtime, _totime, _filter, _max_exalog_age):
        _max_logdir_size = self.__ecc.mCheckConfigOption('max_exawatcher_folder_size_in_gb')
        if (not _max_logdir_size) or _max_logdir_size == '' or (int(_max_logdir_size) == 0):
            ebLogInfo('Setting a default value of 10GB for _max_logdir_size')
            _max_logdir_size = 10*1024*1024
        else:
           _max_logdir_size = int(_max_logdir_size)*1024*1024 

        ebLogInfo('_max_logdir_size is : %s kb' % _max_logdir_size)
        _node = exaBoxNode(get_gcontext())
        os.system('mkdir -p log/exawatcher')

        try:
            _node.mConnect(aHost, aTimeout=20)
            _collect_time = time.ctime()
            _collect_time = _collect_time.replace(" ", "_")
            _collect_time = _collect_time.replace(":", "_")
            _resultdir = "/opt/oracle.ExaWatcher/ExaWatcherResults_%s" % (_collect_time)
            _cmd = "/opt/oracle.ExaWatcher/GetExaWatcherResults.sh"
            if _fromtime is None:
                # If fromtime is not specified, lets retreive logs for the last 10 hours.
                # But this time should be relative of remote node, since timezone can be different
                # Hence lets compute time on the node itself !
                _cmd += " --from " + "`date -d \"10 hour ago\" \"+%m/%d/%Y_%H:%M:%S\"`"
            else:
                _cmd += " --from " + _fromtime
            if _totime is not None:
                _cmd += " --to " + _totime
            if _filter is not None:
                _cmd += " --filter " + _filter
            _cmd += " --resultdir " + _resultdir
            ebLogInfo('Running exawatcher command : %s' % (_cmd)) 
            _node.mExecuteCmd(_cmd)
            _i, _o, _e = _node.mExecuteCmd ("du -s %s/ExtractedResults/ | awk '{print $1}'" % (_resultdir))
            _out = _o.readlines()
            if _out:
                _required_size = _out[0].strip()
                ebLogInfo('Total size required is : %s' % (_required_size))

            _local_size = GetFolderSize("log/exawatcher/")
            _av_size = GetFolderFreeSize("log/exawatcher/")
            _quota_left =  int(_max_logdir_size) - int(_local_size)
            ebLogInfo('Quota disk size left is : %s' % (_quota_left))

            if (int(_av_size) < int(_required_size)) or (_quota_left < int(_required_size)):
                # We dont have enough space to copy the log. So lets try to get rid of old log files.
                deleteOldLogs("log/exawatcher/", _max_exalog_age)

                # Calculate the spaces again.
                _local_size = GetFolderSize("log/exawatcher/")
                _av_size = GetFolderFreeSize("log/exawatcher/")
                _quota_left =  int(_max_logdir_size) - int(_local_size)
                ebLogInfo('Revised quota disk size left is : %s' % (_quota_left))

                if (int(_av_size) < int(_required_size)) or (_quota_left < int(_required_size)):
                    ebLogError('Error: No space left to copy exawatcher logs.') 
                    return
                else:
                    ebLogInfo('Able to recover space. Continuing to copy file to exacloud!.')

  
            _i, _o, _e = _node.mExecuteCmd ("ls %s/ExtractedResults/" %(_resultdir))
            _out = _o.readlines()
            if _out:
                for o in _out :
                    o = o.strip()
                    rfile = ("%s/ExtractedResults/%s" % (_resultdir, o))
                    lfile = ("log/exawatcher/%s" % (o))
                    ebLogInfo('copying file: %s to %s' %(rfile, lfile))
                    try:
                        _node.mCopy2Local(rfile, lfile)
                    except Exception as e:
                        ebLogError('Error copying file : %s' % (str(e)))
                    _log_file_list.append(lfile)
            _node.mExecuteCmd ("/bin/rm -rf %s" %(_resultdir))
            _node.mDisconnect()
        except Exception as e:
            ebLogError('Unable to collect log. Error: %s ' % (e))

    def mGetNodeList(self, aDom0s, aDomUs, aCells):
        for cluster in self.__ecc.mGetClusters().mGetClusters():
            _dom0s, _domUs, _cells, _switches = \
                    self.__ecc.mReturnAllClusterHosts(cluster)
            aDom0s.update(_dom0s)
            aDomUs.update(_domUs)
            aCells.update(_cells)
            ebLogInfo('%d nodes in cluster %s :' % (len(_dom0s) + len(_domUs) + len(_cells), cluster))

def ArchiveLogs(_log_list):
    _tar_file = "log/exawatcher/exawatcher-" + time.strftime('%Y_%m_%d-%H_%M_%S') + ".tar"
    _out_tar = tarfile.open(_tar_file, mode='w')
    _log_file_list = list()

    for _log_file in _log_list:
        for _file in glob.glob(_log_file):
            _log_file_list.append(_file)

    for _file in _log_file_list:
        _out_tar.add(_file)
        os.remove(_file)

    _out_tar.close()
    return _tar_file

def GetFolderSize(_folder):
    _local_size = 0
    if os.path.islink(_folder):
        _local_size = 0
        ebLogInfo('Current Log size is : %s' % (_local_size))
        return _local_size
    if os.path.isfile(_folder):
        _local_size = os.path.getsize(_folder)
        _local_size = str(_local_size//1024)
        ebLogInfo('Current Log size is : %s' % (_local_size))
        return _local_size
    for dirpath, dirnames, filenames in os.walk(_folder):
        _local_size += os.path.getsize(dirpath)
        for _file in filenames:
            _file_path = os.path.join(dirpath, _file)
            if os.path.islink(_file_path):
                continue
            _local_size += os.path.getsize(_file_path)
    # Convert Bytes to KBs
    _local_size = str(_local_size//1024)
    ebLogInfo('Current Log size is : %s' % (_local_size))
    return _local_size

def GetFolderFreeSize(_folder):
    _av_size = None
    total, used, free = shutil.disk_usage(_folder)
    # Available size in KBs
    _av_size = str(free//1024)
    ebLogInfo('Available disk size is : %s' % (_av_size))
    return _av_size

def deleteOldLogs(location, stime):
    if location is None or not os.path.isdir(location):
        ebLogWarn('log location does not exist')
        return
    _time_ago = time.time() - stime
    for _file in os.listdir(location):
        _file_path = os.path.join(location, _file)
        #st_birthtime is not supported in all file systems.
        #But, mtime is same as birthtime for new files. This serves the purpose for us.
        _last_modified = os.stat(_file_path).st_mtime
        if _last_modified < _time_ago:
            ebLogInfo('Deleting old log file %s' % _file_path)
            _db = ebGetDefaultDB()
            _db.mRemoveWatcherLog(_file_path)
            try:
                if os.path.isfile(_file_path) or os.path.islink(_file_path):
                    os.remove(_file_path)
                else:
                    ebLogWarn('Failed to delete log file %s. %s is not a file.' % (_file_path, _file_path))
            except Exception as e:
                ebLogWarn('Failed to delete log file %s. Reason: %s.' % (_file_path, str(e)))

def cleanupExaWatcherLogs():
    _max_exalog_age = get_gcontext().mGetConfigOptions().get("max_exawatcher_log_age_in_hours", "")
    if (not _max_exalog_age) or _max_exalog_age == '' or (int(_max_exalog_age) == 0):
        ebLogInfo('CleanupExaWatcherLogs: Using a default value of 24 hours for _max_exalog_age')
        _max_exalog_age = 24*60*60
    else:
        _max_exalog_age = int(_max_exalog_age)*60*60
    ebLogInfo('CleanupExaWatcherLogs: _max_exalog_age is  %s seconds' % (_max_exalog_age))
    deleteOldLogs("log/exawatcher/", _max_exalog_age)
    _db = ebGetDefaultDB()
    _cur_time = float(calendar.timegm(time.gmtime()))
    #Delete entries which are older than current time. This will also clean up entries for 
    #files which were manually deleted.
    _db.mDeleteWatcher(_cur_time)
