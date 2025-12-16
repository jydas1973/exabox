"""
 Copyright (c) 2017, 2025, Oracle and/or its affiliates.

NAME:
    Diagnosis - Basic functionality

FUNCTION:
    Provide API for Cluster Diagnosis

NOTE:
    None

History:
    hcheon      10/12/2025 - 38491623 Fixed defunct tail command
    gojoseph    02/10/2025 - Bug 37521984 Add directories to exclude in aide.conf
    seha        10/19/2024 - Bug 37153945 Configure Clamav and AIDE for SELinux
    seha        10/10/2024 - Bug 36720493 AIDE failed due to report_url order
    seha        29/03/2024 - Bug 36292289 Add a comment for command injection
    seha        10/20/2023 - Enh 35901819 Update clamav cmd to quarantine file
    seha        09/22/2023 - Enh 35524459 OCI-ExaCC Fedramp automated inventry
    seha        04/10/2023 - Bug 35225606 Clamav support for OL8
    seha        09/22/2022 - Bug 34579030 Fix fortify command injection
    seha        08/25/2022 - Bug 34522569 Run log download cmd as sudo in cps
    seha        05/06/2022 - Bug 34115848 copy cps inventory logs
    aararora    04/28/2022 - Bug 34004530 Bandit issue fix
    seha        12/12/2021 - Bug 33634669 delta collection for cps logs
    pvachhan    11/26/2021 - Bug 33588528 HIDS: IMPLEMENT EXACD FLOW FOR LOG COLLECTION
    seha        08/12/2021 - Bug 33212098 create log repo cps_sw with ecra user
    seha        06/20/2021 - Bug 31442550 Make AIDE conf using exadata AIDE conf
    seha        04/09/2021 - Bug 32664822 install clamav on standby cps
    seha        12/23/2020 - Bug 31285649 change AIDE log path to avoid rotation
    seha        11/18/2020 - Bug 31970738 OCI-ExaCC ADB-D AV/FIM
    hcheon      10/13/2020 - Bug 31985795 Change os.system() to library calls
    hcheon      08/28/2020 - Bug 31814290 command injection in mCopyCPSLog()
    seha        07/17/2020 - Bug 31629542 do not cleanup config files in PodRepo 
    hcheon      07/06/2020 - Bug 31580084 gunzip files without os.system()
    seha        05/11/2020 - Bug 31325614 run OCI-ExaCC AV/FIM on CPS
    scoral      04/23/2020 - Bug 31145240 - Python 3 migration code adaption
    seha        04/22/2020 - Bug 31197624 split log transmitted from cps to ecra
    seha        04/09/2020 - Bug 31127549 OCI-ExaCC AV/FIM management
    seha        04/03/2020 - Bug 31105354 use config lock file
    seha        03/14/2020 - Bug 31030162 cleanup only existing files
    seha        01/23/2020 - Bug 30774505 copy domU logs to CPS chainsaw repo
    itcherna    11/06/2019 - Bug 30464944 - HUGE TAR FILES CREATED IN EXACLOULD/LOG 
                                            TAKING UP A LOT OF SPACE
    seha        10/10/2019 - Bug 30355756 collect CPS logs
    seha        06/25/2019 - bug 29947189 provide exaccocid to fetch log request
    seha        06/15/2019 - Bug 29892700 delete exacloud diagnostic logs
    seha        05/27/2019 - Bug 29679165 log collection for OCI-ExaCC
    jungnlee    21/03/2018 - Enh 27742648 - DUP LOGS FOR CHAINSAW, DISABLE DOMU IN OCIC
    jungnlee    18/02/2018 - Enh 27563832 - LOG COLLECTION SUPPORT FOR OCI CHAINSAW 
    hcheon      13/02/2018 - Bug 27533367: Fix undefined variable error
    jungnlee    31/01/2018 - Bug 27468792: HANDLE SSH CONNECTION TIMEOUT
    hcheon      26/01/2018 - Bug 27440121: ignore old logs at the first time
    seha        25/01/2018 - Enh 27427661: store logs in log/diagnostic
    seha        24/01/2018 - raise exception if failed to get rackinfo.conf
    jungnlee    15/01/2018 - Bug 27397702: log time error between remote hosts
    jungnlee    14/11/2017 - Bug 27106091: SHOULD HANDLE TIMESTAMP W/O TIMEZONE
    seha        21/09/2017 - modify log classification method to aware multi-vm
    hcheon      18/09/2017 - Bug 26799195: Collect logs by lines
    seha        31/08/2017 - modify mCollectLog to collect cell/switch log
    hcheon      04/06/2017 - File Creation
"""
import fcntl
import fnmatch
import glob
import gzip
import json
import os
import re
import shlex
import shutil
import socket
import subprocess
import tarfile
import traceback
import time

from exabox.core.DBStore import ebGetDefaultDB
from exabox.core.Error import ebError
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.log.LogMgr import ebLogDiag, ebSetLogDiagLvl, ebLogWarn, ebLogError
from exabox.tools.AttributeWrapper import wrapStrBytesFunctions

class file_lock_manager(object):
    def __init__(self, lock_file_path):
        self.lock_file_path = lock_file_path
        self.lock_file = None

    def __enter__(self):
        self.lock_file = open(self.lock_file_path)
        fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX)

    def __exit__(self, type, value, traceback):
        fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
        self.lock_file.close()

class packageInfo:
    def __init__(self, aRpmFile, aPkgName, aPkgVersion,
                    aPkgRelease, aPkgLinuxVer, aPkgBuildTime):
        self.rpm_file = aRpmFile
        self.pkg_name = aPkgName
        self.pkg_version = aPkgVersion
        self.pkg_release = aPkgRelease
        self.pkg_linux_ver = aPkgLinuxVer
        self.pkg_build_time = aPkgBuildTime

class exaBoxDiagCtrl(object):

    def __init__(self, aCluCtrlObject):
        self.__ecc = aCluCtrlObject
        self.__job = aCluCtrlObject.mGetRequestObj()
        self.__uuid = aCluCtrlObject.mGetRequestObj().mGetUUID()
        self.__finished = False
        self.__debug = False
        self.__sincedb = '/var/cache/exacloud/ebdiagcol'
        self.__sincedb_ls_target_splitter = '====== ls targets ======='
        self.__tz_dict = {}
        self.__td_dict = {}
        self.__day_ago = time.time() - 86400
        self.mReadConfig()

    def mReadConfig(self):
        self.__base_path = get_gcontext().mGetBasePath()
        _hcconfigpath = self.__base_path + '/config/healthcheck.conf'
        _hcconfig = {}

        try:
            with open(_hcconfigpath) as f:
                _hcconfig = json.load(f)
        except Exception as e: # pragma: no cover
            ebLogDiag('WRN', 'Failed to read healthcheck.conf : %s' % e)

        def _get_config_value(aKey, default=None):
            if aKey in _hcconfig and _hcconfig[aKey]:
                return _hcconfig[aKey]
            else: # pragma: no cover
                ebLogDiag('WRN','Could not get %s from healthcheck.conf' % aKey)
                return default

        self.__root_dir = _get_config_value('diag_root', self.__base_path)
        ebLogDiag('NFO','Collect logs to %s' % self.__root_dir)
        self.__domu_chainsaw_repo = _get_config_value('domu_chainsaw_repo',
                    self.__base_path + '/chainsaw_logs/dp_logs')
        ebLogDiag('NFO','Filter chainsaw log to %s' % self.__domu_chainsaw_repo)
        self.__domu_chainsaw_logs = _get_config_value('domu_chainsaw_logs',
                ["rack_alertxml", "rack_dcs-admin", "rack_dcs-agent"])
        self.__avfim_repo = _get_config_value('avfim_repo',
                '/u01/downloads/avfim_rpms')
        self.__tar_chunk_size = _get_config_value('tar_chunk_size_byte',4194304)

        self.__rackconfig = {}
        self.__log_repo_base = '%s/diagnostic/results' % self.__root_dir
        self.__log_repo = '%s/%s' % (self.__log_repo_base, self.__uuid)
        self.__tz_cfg = '%s/diagnostic/config/timezone.json' % self.__root_dir
        self.__td_cfg = '%s/diagnostic/config/timediff.json' % self.__root_dir
        self.__cps_marker='%s/diagnostic/config/cps_marker.json'%self.__root_dir
        self.__cps_marker_avfim='%s/diagnostic/config/cps_marker_avfim.json' % \
                                   self.__root_dir
        self.__cps_logs_to_copy = [
            '/opt/oci/exacc/inventory/json/ecs_applied_tuner_patches.json',
            '/opt/oci/exacc/inventory/json/ecs_images_info.json',
            '/opt/oci/exacc/inventory/json/ecs_inventory_imgversions.json',
            '/opt/oci/exacc/inventory/json/ecs_cpssw_versions.json',
            '/opt/oci/exacc/inventory/json/ecs_inventory_misc.json',
            '/opt/oci/exacc/inventory/json/ecs_exa_k_spliceinfo.json']

        if self.__debug:
            ebLogDiag('NFO', 'Logs will be collected to %s' % self.__log_repo)

    def mRunDiagnosis(self, aCmd, aOptions):
        _rc = 0
        self.__finished = False
        if aOptions.debug:
            self.__debug = True
            ebSetLogDiagLvl('DEBUG')
        try:
            if aCmd == 'collect_log':
                ebLogDiag('NFO',
                        'Collecting diag logs job uuid: %s' % self.__uuid)
                _rc = self.mCollectLog(aOptions)
                if _rc: # pragma: no cover
                    ebLogError('Failed to run cluster diagnosis log collection')
                    return ebError(0x0950)
            elif aCmd == 'run_compliance_tool':
                ebLogDiag('NFO',
                        'Running compliance tool job uuid: %s' % self.__uuid)
                _rc = self.mRunAvFim(aOptions)
                if _rc: # pragma: no cover
                    ebLogError('Failed to run cluster compliance tool management')
                    return ebError(0x0950)
            self.__finished = True
            return _rc
        except Exception as e: # pragma: no cover
            ebLogDiag('ERR', 'Exception during diagnosis run: %s' % e)
            return ebError(0x0950)


    def mCollectLog(self, aOptions):
        _support_node_types = ['dom0', 'domU', 'cell', 'switch', 'cps']
        _db = ebGetDefaultDB()

        # validate parameters
        if aOptions.diagtype == 'all':
            _target_node_types = _support_node_types
        else:
            _target_node_types = aOptions.diagtype.split(',')
            for _target in _target_node_types:
                if _target not in _support_node_types: # pragma: no cover
                    ebLogDiag('ERR', 'Ignore unknown node type %s' % _target)
                    _target_node_types.remove(_target)

            if len(_target_node_types) == 0: # pragma: no cover
                raise Exception('Invalid node type for %s' % aOptions.diagtype)

            # Add CPS to collection target
            _target_node_types.append('cps')

        # make config lock file
        self.__job_params = aOptions.params
        if self.__job_params:
            self.__cps_marker = '%s/diagnostic/config/cps_marker_%s.json' % (
                    self.__root_dir, self.__job_params)
        self.mMakeConfigLockFile(
                [self.__tz_cfg, self.__td_cfg, self.__cps_marker])

        # get node list (dom0, domU, cell, switch)
        _all_dom0s = set()
        _all_domUs = set()
        _all_cells = set()
        _all_switches = set()
        self.mGetNodeList(_all_dom0s, _all_domUs, _all_cells, _all_switches)
        if (self.__ecc.mEnvTarget() and
                not (self.__ecc.mIsExabm() or self.__ecc.mIsOciEXACC())):
            # access domU only if env is ExaCS or OCI-ExaCC ATP
            _all_domUs = set()

        # get rack info (cabinet, hwrack, cluster) from the metadata json
        _cluster_name = self.__ecc.mGetClusterName()
        _node_list = [_all_dom0s, _all_domUs, _all_cells, _all_switches]
        _rack_info = self.mGetRackInfo(aOptions, _cluster_name, _node_list)

        # eval the number of target nodes
        _total_target_cnt = 0
        _target_nodes = []
        if 'dom0' in _target_node_types:
            _total_target_cnt += len(_all_dom0s)
            _target_nodes.extend(_all_dom0s)
        if 'domU' in _target_node_types:
            _total_target_cnt += len(_all_domUs)
            _target_nodes.extend(_all_domUs)
        if 'cell' in _target_node_types:
            _total_target_cnt += len(_all_cells)
            _target_nodes.extend(_all_cells)
        if 'switch' in _target_node_types:
            _total_target_cnt += len(_all_switches)
            _target_nodes.extend(_all_switches)
        if 'cps' in _target_node_types:
            _total_target_cnt += 1

        def _update_cfg_with_locking(aDict, aPath):
            try:
                if not os.access(os.path.dirname(aPath), os.F_OK):
                    os.makedirs(os.path.dirname(aPath))
                if not (os.path.exists(aPath) and os.path.getsize(aPath) > 0):
                    with open(aPath, 'w') as _fp:
                        _fp.write(json.dumps(dict()))
                with open(aPath, 'r+') as _fp:
                    _cfg_dict = json.load(_fp)
                    _is_updated = False
                    for _key in aDict.keys():
                        if _key not in _cfg_dict:
                            _is_updated = True
                        else:
                            if _cfg_dict[_key] != aDict[_key]:
                                _is_updated = True
                        _cfg_dict[_key] = aDict[_key]
                    if _is_updated:
                        _fp.seek(0)
                        _fp.truncate()
                        _fp.write(json.dumps(_cfg_dict, indent=4))
                        _fp.flush()
            except Exception as e: # pragma: no cover
                ebLogDiag('WRN', 'Failed to update %s: %s' % (aPath, e))

        # get node timezone and timediff, and update dict
        try:
            _local_tz = subprocess.check_output(["/bin/date", "+%:z"]).decode('utf8').strip()
            self.__tz_dict[socket.getfqdn()] = _local_tz
            self.__tz_dict[socket.gethostname()] = _local_tz
        except:
            ebLogDiag('ERR', 'Failed to query local time offset')

        for _node in _target_nodes:
            self.mCollectSystemInfo(_node)
        # update cfg with dicts
        with file_lock_manager(self.__tz_cfg + '.lock'):
            _update_cfg_with_locking(self.__tz_dict, self.__tz_cfg)
        with file_lock_manager(self.__td_cfg + '.lock'):
            _update_cfg_with_locking(self.__td_dict, self.__td_cfg)

        # collect non-TFA logs from dom0s, domUs, cells and switches
        def _call_collect_system_log(aNodeType, aNodeList, aCompleteTargetCnt):
            ebLogDiag('NFO', 'Starting %s log collection from %s' 
                    % (aNodeType, _cluster_name))
            try:
                _targets = self.__rackconfig['log_collection_targets'][aNodeType]
            except KeyError: # pragma: no cover
                ebLogDiag('ERR', 'No %s log type specified in rackinfo.conf' 
                        % aNodeType)
                _targets = None
                aCompleteTargetCnt += len(aNodeList)
            if _targets:
                for node in aNodeList:
                    _progress_pct = (100 * aCompleteTargetCnt/_total_target_cnt)
                    self.__job.mSetStatusInfo(
                            'True:%d:Collecting system logs from %s' %
                            (_progress_pct, node))
                    _db.mUpdateRequest(self.__job)
                    self.mCollectSystemLog(node, _targets,
                            aNodeType, _rack_info)
                    aCompleteTargetCnt += 1
            return aCompleteTargetCnt

        _complete_target_cnt = 0
        if 'dom0' in _target_node_types:
            _complete_target_cnt = _call_collect_system_log('dom0',
                    _all_dom0s, _complete_target_cnt)
        if 'domU' in _target_node_types:
            _complete_target_cnt = _call_collect_system_log('domU',
                    _all_domUs, _complete_target_cnt)
        if 'cell' in _target_node_types:
            _complete_target_cnt = _call_collect_system_log('cell',
                    _all_cells, _complete_target_cnt)
        if 'switch' in _target_node_types:
            _complete_target_cnt = _call_collect_system_log('switch',
                    _all_switches, _complete_target_cnt)
        if 'cps' in _target_node_types:
            _complete_target_cnt = _call_collect_system_log('cps',
                    [self.mGetHostname(None, 'cps')], _complete_target_cnt)

        # make splitted tar files collected by each job
        _num_chunks = self.mCompressLog()

        # clean old config and log files
        self.mCleanFiles()

        self.__job.mSetStatusInfo('True:100:Done with %s chunks' % _num_chunks)
        # TODO: what should be returned on partial failure??
        return 0

    def mMakeConfigLockFile(self, aCfgPaths):
        for _cfg_path in aCfgPaths:
            _cfg_lock = _cfg_path + '.lock'
            if not os.access(os.path.dirname(_cfg_lock), os.F_OK):
                os.makedirs(os.path.dirname(_cfg_lock))
            if not os.path.exists(_cfg_lock):
                open(_cfg_lock, 'a').close()

    def mCollectSystemInfo(self, aHost):
        # connect
        _node = exaBoxNode(get_gcontext())
        try:
            _node.mConnect(aHost, aTimeout=20)
            # query timezone and update tz dict
            _, _o, _ = _node.mExecuteCmd('/bin/date +%:z')
            self.__tz_dict[aHost] = _o.read().strip()
        except Exception as e: # pragma: no cover
            ebLogDiag('NFO', 'Skip querying timezone on %s ' \
                      '(Failed to connect: %s)' % (aHost, e))

        # query timestamp and update td dict if diff >= 10
        try:
            _local_out = subprocess.check_output(["/bin/date", "+%s"]).decode('utf8')
            _, _o, _ = _node.mExecuteCmd('/bin/date +%s')
            _diff = int(_local_out.strip()) - int(_o.read().strip())
            if _diff >= 10 or _diff <= -10:
                self.__td_dict[aHost] = _diff
        except Exception as e: # pragma: no cover
            ebLogDiag('NFO', 'Exception during getting time diff on ' \
                      '%s: %s' % (aHost, e))
        _node.mDisconnect()
        return True


    def mCollectSystemLog(self, aHost, aTargets, aNodeType, aRackInfo):
        ebLogDiag('NFO','Start to collect %s logs from %s' % (aNodeType, aHost))

        # set last scan time to CPS marker to avoid duplicated log collection
        # collect CPS log if more than 20 min have passed since last scan time
        if aNodeType == 'cps':
            if self.__job_params == 'fedramp':
                _interval_sec = 60
            else:
                _interval_sec = 1200
            with file_lock_manager(self.__cps_marker + '.lock'):
                _rc = self.mUpdateCpsMarkerWithLocking(
                        self.__cps_marker, _interval_sec)
            if not _rc:
                return

            # copy CPS logs to log repo
            self.mCopyCPSLog()

        # prepare path and clear previous downloads
        _target_logs = {}   # {source file : (download path, config_dict)}
        self.mSetTargetLogInfo(_target_logs, aHost, aTargets,
                aNodeType, aRackInfo)
        _target_filenames = list(_target_logs.keys())

        _node = None
        if aNodeType != 'cps':
            # connect
            _node = exaBoxNode(get_gcontext())
            try:
                _node.mConnect(aHost, aTimeout=20)
            except Exception as e: # pragma: no cover
                ebLogDiag('WRN', 'Skip system log collection on %s ' \
                          '(Failed to connect: %s)' % (aHost, e))
                return False

        # run specific command if "command" is defined in diagnostic.conf
        self.mRunCommand(_target_logs, aHost, _node, aNodeType)

        # create sincedb path
        if self.__job_params:
            self.__sincedb = '/var/cache/exacloud/ebdiagcol_%s' % (
                    self.__job_params)
        self.mMakeDir(os.path.dirname(self.__sincedb), _node, aNodeType)

        # get last file info
        _last_fileinfo, _last_inodes, _last_target = self.mGetFileList(_node,
                                                             True, aNodeType)
        _file_list = ['%s*' % target for target in _target_logs]
        _cmd = '/bin/ls -AiLgG --time-style=+%%s %s > %s' % (
                ' '.join(_file_list), self.__sincedb)
        self.mExecuteCmd("/bin/sh -c \"" + _cmd + "\"", _node, aNodeType)
        _current_fileinfo, _, _ = self.mGetFileList(_node, False, aNodeType)
        _cmd = '/bin/echo "%s\n%s" >> %s' % (self.__sincedb_ls_target_splitter,
                '\n'.join(_target_logs), self.__sincedb)
        self.mExecuteCmd("/bin/sh -c \'" + _cmd + "\'", _node, aNodeType)

        # replace wildcards of _target_logs with the actual file names
        self.mUpdateTargetLogInfo(
                _target_logs, _current_fileinfo, _last_fileinfo, _last_target)

        # download deltas
        _filecount = 0
        _logsize = 0
        _download_info = self.mCompareFileList(
                        _last_fileinfo, _last_inodes, _current_fileinfo,
                        _target_filenames)
        for i, _download_entry in enumerate(_download_info):
            _src_filename, _dst_filename, _offset, _size = _download_entry
            if _dst_filename not in _target_logs:
                ebLogDiag('DBG', 'Ignore %s(%s)' % 
                        (_src_filename, _dst_filename))
                continue
            _download_path, _log_info = _target_logs[_dst_filename]
            self.mDownloadLogFile(_node, _src_filename, _download_path,
                                  _offset, _size, aNodeType)
            _filecount += 1

            _new_size = self.mTruncateIncompleteLog(_download_path, _log_info)
            if _new_size != _size:
                ebLogDiag('NFO', 'Ignore %d bytes of incomplete log of %s' %
                           (_size - _new_size, _src_filename))
                self.mManipulateSincedb(_node, _src_filename,
                                        _current_fileinfo, _new_size-_size,
                                        aNodeType)
            _logsize += _new_size

        if aNodeType != 'cps':
            _node.mDisconnect()
        ebLogDiag('NFO', 'Finished to collect %s logs from %s : '
                  '%d files, %d byte' % (aNodeType, aHost,
                      _filecount, _logsize))
        return True

    def mGetNodeList(self, aAllDom0s, aAllDomUs, aAllCells, aAllSwitches):
        """
        Get node list from the cluster xml and store them in the sets
        The nodes are classified by the type like dom0, domU, cell,
        and switch
        """
        for cluster in self.__ecc.mGetClusters().mGetClusters():
            _dom0s, _domUs, _cells, _switches = \
                    self.__ecc.mReturnAllClusterHosts(cluster)
            aAllDom0s.update(_dom0s)
            aAllDomUs.update(_domUs)
            aAllCells.update(_cells)
            aAllSwitches.update(_switches)
            ebLogDiag('DBG', '%d nodes in cluster %s :' %
                      (len(_dom0s) + len(_domUs) + len(_cells) +
                       len(_switches), cluster))
            ebLogDiag('DBG',' %d dom0s %s' % (len(_dom0s),','.join(_dom0s)))
            ebLogDiag('DBG',' %d domUs %s' % (len(_domUs),','.join(_domUs)))
            ebLogDiag('DBG',' %d cells %s' % (len(_cells),','.join(_cells)))
            ebLogDiag('DBG',' %d switches %s' %
                      (len(_switches), ','.join(_switches)))

    def mGetRackInfo(self, aOptions, aClusterName, aNodeList):
        """
        Load contents of jsonconf conveying rackinfo.conf from ECRA
        Get the rack info of current cluster from the jsonconf
        and store it in the dictionary by node
        _rack_info {node: (cabinet, hwrack, cluster)}
        """
        if 'jsonconf' in aOptions and aOptions.jsonconf:
            try:
                self.__rackconfig = aOptions.jsonconf
            except Exception as e: # pragma: no cover
                ebLogDiag('ERR',
                    'Could not load jsonconf conveying rackinfo.conf from ECRA')
                raise e
        else: # pragma: no cover
            raise Exception(
                    'Please make sure jsonconf is provided in the request URL')

        # get the rackinfo
        try:
            _clusters = self.__rackconfig['clusters']
            _cabinet = _clusters[aClusterName]['cabinet']
            _hwrack  = _clusters[aClusterName]['hwrack']
        except Exception as e: # pragma: no cover
            #can happen in BM env
            _cabinet = 'trunk'
            _hwrack = 'trunk'

        _rack_info = {}
        for _nodes in aNodeList:
            for _node in _nodes:
                _rack_info[_node] = (_cabinet, _hwrack, aClusterName)
        return _rack_info

    def mGetFileList(self, aNode, aBuildInodeMap, aNodeType):
        '''
        Download and parse remote file list (ls command output)
        Returns two dicts of file information and a list of ls targets
        {filename : (inode, size, modification time)}
        {inode : filename}  (or an empty dict if aBuildInodeMap == False)
        '''
        _ls_output_path = '/tmp/lsoutput_%s.tmp' % self.mGetHostname(aNode,
                aNodeType)

        try:
            if self.mFileExists(self.__sincedb, aNode, aNodeType):
                fileContent = self.mReadFile(self.__sincedb, aNode, aNodeType)
                with open(_ls_output_path, "w") as _localFile:
                    _localFile.write(fileContent)
                _ls_output = open(_ls_output_path)
            else:
                ebLogDiag('WRN', "Empty remote file.")
                return {}, {}, []
        except Exception as e: # pragma: no cover
            ebLogDiag('ERR', 'Failed to get file list: %s' % e)
            return {}, {}, []

        _dir = ''
        _files = {}
        _inodes = {}
        _ls_targets = []

        _ls_output_lines = _ls_output.read().splitlines()
        for _linenum, _line in enumerate(_ls_output_lines):
            _sp = _line.split(None, 5)
            if len(_sp) == 6:
                _inode, _mode, _, _size, _timestamp, _filename = _sp
                if _mode.startswith('d'):   # directory
                    continue
                if _inode == '?':   # broken link
                    continue
                _filename = os.path.join(_dir, _filename.strip())
                _files[_filename] = (int(_inode), int(_size), int(_timestamp))
                if aBuildInodeMap:
                    _inodes[int(_inode)] = _filename
            elif len(_sp) == 1 and _sp[0].endswith(':'):
                _dir = _sp[0][:-1]
            elif _line == self.__sincedb_ls_target_splitter:
                _ls_targets = _ls_output_lines[_linenum+1:]
                break

        _ls_output.close()
        os.remove(_ls_output_path)
        return _files, _inodes, _ls_targets

    def mSetTargetLogInfo(self,aTargetLogs,aHost,aTargets,aNodeType,aRackInfo):
        """
        Set the download path and other config of target logs
        by using given aTargets from diagnostics.conf.
        - aTargetLogs : configuration info, {filename : (download path, cfg)}
        Download path depends on the type of node
        - dom0/cell: log_repo_base/category/cabinet/hwrack/host/filename
        - domU     : log_repo_base/category/cabinet/hwrack/cluster/host/filename
        - switch   : log_repo_base/category/cabinet/host/filename
        """
        _shost = aHost.split('.')[0]
        for _src_file, _info in aTargets.items():
            if _src_file in self.__cps_logs_to_copy:
                # do not collect delta
                continue
            _category = _info['category']
            _filename = _info['filename']
            # replace cell log path .../cell/<hostname>/alert to real hostname
            _filename = _filename.replace('<hostname>', _shost)
            _src_file = _src_file.replace('<hostname>', _shost)
            ebLogDiag('DBG', ' target log: %s' % _src_file)

            # extract _cabinet, _hwrack, _cluster info from aRackInfo[aHost]
            if aNodeType != 'cps':
                _cabinet, _hwrack, _cluster = aRackInfo[aHost]
            if aNodeType in ['dom0', 'cell']:
                # log_repo_base/category/hwrack/rack/host/filename
                _download_path = '%s/%s/%s/%s/%s/%s' % \
                                 (self.__log_repo, _category,
                                  _cabinet, _hwrack, aHost, _filename)
                ebLogDiag('DBG', ' set dom0/cell download path: %s' % \
                            _download_path)
            elif aNodeType in ['domU']:
                if _category in self.__domu_chainsaw_logs:
                    # chainsaw_repo/chainsaw_filename
                    _download_path = '%s/%s' % \
                                 (self.__domu_chainsaw_repo,
                                  self.mGenChainsawFilename(aHost, _filename))
                else:
                    # log_repo_base/category/hwrack/rack/cluster/host/filename
                    _download_path = '%s/%s/%s/%s/%s/%s/%s' % \
                                 (self.__log_repo, _category,
                                  _cabinet, _hwrack, _cluster, aHost, _filename)
                ebLogDiag('DBG', ' set domU download path: %s' %
                            _download_path)
            elif aNodeType in ['switch']:
                # log_repo_base/category/hwrack/host/filename
                _download_path = '%s/%s/%s/%s/%s' % \
                                 (self.__log_repo, _category,
                                  _cabinet, aHost, _filename)
                ebLogDiag('DBG', ' set switch download path: %s' %
                            _download_path)
            elif aNodeType in ['cps']:
                _download_path = '%s/%s/%s/%s' % \
                                 (self.__log_repo, _category,
                                  aHost, _filename)
                ebLogDiag('DBG', ' set cps download path: %s' %
                            _download_path)

            _download_dir = os.path.dirname(_download_path)
            if not os.access(_download_dir, os.F_OK):
                try:
                    os.makedirs(_download_dir)
                except Exception as e: # pragma: no cover
                    ebLogDiag('WRN',
                        'Failed to make %s. Will try again with sudo: %s' % (
                            _download_dir, e))
                    _user = os.getuid()
                    _group = os.getgid()
                    _rc, _, _stderr = self.mExecuteCmd(
                            '/usr/bin/install -d -o %s -g %s %s' % (
                            _user, _group, _download_dir), None, 'cps')
                    if _rc or _stderr:
                        ebLogDiag('ERR', 'Failed to make %s with sudo. ' \
                                'Please manually make a directory: %s' % (
                                    _download_dir, _stderr))
                        continue
            aTargetLogs[_src_file] = (_download_path, _info)

    def mUpdateTargetLogInfo(self,
            aTargetLogs, aCurFiles, aLastFiles, aLastTargetLogs):
        """
        Find and replace the wildcard path in aTargetLogs to real dir name
        aTargetLogs : configuration info, {filename : (download path, cfg)}
            e.g. {'/rdbms/*/alert/log.xml' : ('rdbms:<id1>:log.xml', {})}
        aCurFiles : 'ls' command output, {filename : (inode, size, time)}
            e.g. {'rdbms/db95ad8d/alert/log.xml' : (..)}
        This function will compare file names and store 'db95ad8d' to _diff,
        and replace <id1> in download path to 'db95ad8d'
        With the sample input above, following info will be added to aTargetLogs
            {'/rdbms/db95ad8d/alert/log.xml' : ('rdbms:db95ad8d:log.xml', {})}
        """

        # do not collect existing old data of newly added target files
        for _new_target_file in set(aTargetLogs) - set(aLastTargetLogs):
            _matched_files = fnmatch.filter(aCurFiles, _new_target_file)
            for _file in _matched_files:
                ebLogDiag('NFO', 'Ignore existing data of %s' % _file)
                del aCurFiles[_file]

        # remove unchanged files from sincedb
        for _file in list(aCurFiles):
            _inode, _size, _ = aCurFiles[_file]
            if _file in aLastFiles: 
                _last_inode, _last_size, _ = aLastFiles[_file]
                if _inode == _last_inode and _size == _last_size:
                    del aCurFiles[_file]

        for _src_filename in list(aTargetLogs):
            if '*' not in _src_filename and '?' not in _src_filename:
                continue
            _matched_files = fnmatch.filter(aCurFiles, _src_filename)
            for _dst_filename in _matched_files:
                _parsed_src_filename = _src_filename.split('/')
                _parsed_dst_filename = _dst_filename.split('/')
                if len(_parsed_src_filename) == len(_parsed_dst_filename):
                    _diff = [_dst_filename_w for _src_filename_w,_dst_filename_w
                        in zip(_parsed_src_filename, _parsed_dst_filename)
                        if _src_filename_w != _dst_filename_w]
                    _download_path, _cfg = aTargetLogs[_src_filename]
                    for i, path in enumerate(_diff):
                        # replace <id1>,<id2>,... in download path to real path
                        _download_path = _download_path.replace(
                                '<id%s>' % str(i+1), path)
                    aTargetLogs[_dst_filename] = (_download_path, _cfg)
                else:
                     ebLogDiag('NFO', 'Ignore %s(%s)' % 
                             (_src_filename, _dst_filename))

    def mGenChainsawFilename(self, aHost, aFilename):
        # generate chainsaw format filename
        # e.g. dcs-agent.log -> dcs-agent-scas07adm03vm01-2020-01-21-091731.log
        _exteinsion = ''
        _last_dot_pos = aFilename.rfind('.')
        if _last_dot_pos > 0:
            _extension = aFilename[_last_dot_pos:]
            aFilename = aFilename[:_last_dot_pos]
        _short_hostname = aHost.split('.', 2)[0]
        _report_time = time.strftime('%Y-%m-%d-%H%M%S', time.localtime())
        _chainsaw_filename = aFilename + '-' + _short_hostname + '-' \
                + _report_time + _extension
        return _chainsaw_filename

    def mRunCommand(self, aTargetLogs, aHost, aNode, aNodeType):
        """
        Run the command if "command" is defined in diagnostic.conf as follows
        "/tmp/ibdiagnet.log" : {
            "category" : "rack_ibdiagnet",
            "filename" : "ibdiagnet.log",
            "command"  : "ibdiagnet -lw 4x -ls 10 -pm -pc"
        }
        The command is executed first, and the generated log is collected next
        """
        for _, _cfg in aTargetLogs.values():
            if 'command' in _cfg:
                _cmd = _cfg['command']
                ebLogDiag('NFO', ' Running command(%s) on %s' % (_cmd, aHost))
                _rc, _, _ = self.mExecuteCmd(_cmd, aNode, aNodeType)
                if _rc: # pragma: no cover
                    ebLogDiag('ERR', ' Failed to run command(%s) on %s' % 
                            (_cmd, aHost))
                    ebLogDiag('ERR', ' Exit status: %s' % _rc)

    def mCompareFileList(self,
        aLastFiles, aLastInodes, aCurFiles, aTargetFilenames):
        _entries = [] # [(_src_filename, _dst_filename, _offset, _size)]
        _asso_files = self.mAssociateFilesToTarget(aCurFiles, aTargetFilenames)
        for _filename_ptrn in _asso_files:
            _oldest_file = True
            for _filename in _asso_files[_filename_ptrn]:
                _entry = self.mMakeDownloadEntry(_filename, _filename_ptrn,
                            aLastFiles, aLastInodes, aCurFiles, _oldest_file)
                if _entry:
                    _entries.append(_entry)
                    _oldest_file = False
        return _entries

    def mAssociateFilesToTarget(self, aCurFiles, aTargetFilenames):
        _ret = {}
        for _filename_ptrn in aTargetFilenames:
            _matched_files = fnmatch.filter(aCurFiles, _filename_ptrn + '*')
            if len(_matched_files) > 1:
                _ret[_filename_ptrn] = self.mSortRotatedFiles(
                        _matched_files, _filename_ptrn)
            else:
                _ret[_filename_ptrn] = _matched_files
        return _ret

    def mSortRotatedFiles(self, aMatchedFiles, aFilenamePtrn):
        # sort filename list to check renamed old files first
        #   e.g. check /var/log/messages.20170630 prior to /var/log/messages
        # sort oldest file first
        for _matched_file in aMatchedFiles:
            _sfx = _matched_file[self.mGetSuffixPosition(
                    _matched_file, aFilenamePtrn):]
            if _sfx and any(_sfx_char.isdigit() for _sfx_char in _sfx):
                # suffix contains number
                if int(re.findall(r'\d+', _sfx)[-1]) > 20000000:
                    # suffixed by date, older file contains less number
                    # send a file that does not have date suffix to last
                    _sorted = sorted(aMatchedFiles)
                    return _sorted[1:] + [_sorted[0]]
                else:
                    # suffixed by 1, 2, .., older file contains greater number
                    return sorted(aMatchedFiles, reverse=True)
        # for log_*.xml and ms-odl-*.log
        return sorted(aMatchedFiles)

    def mMakeDownloadEntry(self, aFilename, aFilenamePtrn,
            aLastFiles, aLastInodes, aCurFiles, aOldestFile):
        _inode, _size, _timestamp = aCurFiles[aFilename]
        if _size == 0:
            return None
        if self.mMatchesExactly(aFilename, aFilenamePtrn):
            _last_filename = aLastInodes.get(_inode)
            if (_last_filename and
                    self.mMatchesExactly(_last_filename, aFilenamePtrn)):
                _, _last_size, _ = aLastFiles[_last_filename]
                if _size > _last_size:
                    # file size increased, no log rotation
                    return (aFilename, _last_filename, _last_size,
                                 _size - _last_size)
                elif _size < _last_size:
                    # rotated by copy-truncate
                    return (aFilename, aFilename, 0, _size)
                else:
                    # no new log data
                    return None
            else:
                # new file, or rotated by move-create
                return (aFilename, aFilename, 0, _size)
        else:
            # file has some additional suffix, may be a rotated file
            _last_filename = aLastInodes.get(_inode)
            if _last_filename:
                _, _last_size, _ = aLastFiles[_last_filename]
                if self.mMatchesExactly(_last_filename, aFilenamePtrn):
                    # renamed by log rotation
                    if _size > _last_size:
                        return (aFilename, _last_filename, _last_size,
                                     _size - _last_size)
                    elif _size < _last_size:
                        ebLogDiag('WRN', "%s -> %s (size %s -> %s)" % (
                                _last_filename, aFilename, _last_size, _size))
                    return None
                elif aFilename == _last_filename:
                    # rotated file should not be changed,
                    # and it should be filtered by mFilterUnchangedLogs
                    ebLogDiag('WRN', "%s size: %s -> %s" % (
                                aFilename, _size, _last_size))
                    return None
                elif self.mMatchesByPrefix(_last_filename, aFilenamePtrn):
                    # rotated again (for example, log.1.gz -> log.2.gz)
                    # rotated again (for example, log.1.gz -> log.2.gz)
                    if _size != _last_size:
                        ebLogDiag('WRN', "%s -> %s (size %s -> %s)" % (
                                _last_filename, aFilename, _last_size, _size))
                    return None
                # else the last file was associated with another target
            # this file (with some suffix in filename) is a new file
            _original_filename = aFilename[:self.mGetSuffixPosition(
                    aFilename, aFilenamePtrn)]
            if _original_filename not in aCurFiles:
                ebLogDiag('WRN', 'Found %s, but %s does not exist' % (
                            aFilename, _original_filename))
                return None
            elif _original_filename not in aLastFiles:
                # assume the log file has been created and rotated very quickly
                return (aFilename, aFilename, 0, 0)
            _inode, _size, _ = aCurFiles[_original_filename]
            _last_inode, _last_size, _ = aLastFiles[_original_filename]
            if _inode == _last_inode:
                if _size < _last_size:
                    # rotated by copy-truncate
                    if aOldestFile:
                        # assume this was the lastOrigFile. download delta
                        return (aFilename, aFilename, _last_size, 0)
                    else:
                        # assume the file has been rotated multiple times
                        return (aFilename, aFilename, 0, 0)
                else:
                    ebLogDiag('WRN', 'Found %s, but %s seems to be not rotated'
                            % (aFilename, _original_filename))
                    return None
            else:
                _renamed_last_origfile = None
                for _curfile in aCurFiles:
                    _cur_inode, _cur_size, _ = aCurFiles[_curfile]
                    if _cur_inode == _last_inode:
                        _renamed_last_origfile = _curfile
                if (_renamed_last_origfile and
                    self.mMatchesByPrefix(
                        _renamed_last_origfile, aFilenamePtrn)):
                    # the original file has been renamed by adding suffix
                    if self.mGetDecompressCommand(aFilename):
                        # assume this is a previously rotated file
                        # log -> log-20181019, log-20181012 -> log-20181012.gz
                        ebLogDiag('WRN', 'Ignore %s' % aFilename)
                        return None
                    else:
                        # assume the file has been rotated multiple times
                        # this is not the rotated file by the conditions above
                        return (aFilename, aFilename, 0, 0)
                else:
                    # the original file seems to be compressed
                    if not self.mGetDecompressCommand(aFilename):
                        ebLogDiag('WRN', 'Ignore %s' % aFilename)
                        return None
                    else:
                        if aOldestFile:
                            # assume this was the lastOrigFile.. download delta
                            return (aFilename, aFilename, _last_size, 0)
                        else:
                            # assume the file has been rotated multiple times
                            return (aFilename, aFilename, 0, 0)

    def mMatchesExactly(self, aFilename, aSrcFilename):
        _is_matched = False
        if '*' in aSrcFilename or '?' in aSrcFilename:
            if fnmatch.filter([aFilename], aSrcFilename):
                _is_matched = True
        else:
            if aFilename == aSrcFilename:
                _is_matched = True
        return _is_matched

    def mMatchesByPrefix(self, aFilename, aSrcFilename):
        _is_matched = False
        if '*' in aSrcFilename or '?' in aSrcFilename:
            if fnmatch.filter([aFilename], aSrcFilename + '*'):
                _is_matched = True
        else:
            if aFilename.startswith(aSrcFilename):
                _is_matched = True
        return _is_matched

    def mGetSuffixPosition(self, aFilename, aSrcFilename):
        if '*' not in aSrcFilename or '?' not in aSrcFilename:
            # no wildcard, filename starts with the source file path
            return len(aSrcFilename)
        _last_wildcard = max(
                aSrcFilename.rfind('*'), aSrcFilename.rfind('?'))
        _last_subpath = aSrcFilename[_last_wildcard + 1:]
        return aFilename.rfind(_last_subpath) + len(_last_subpath)

    def mGetDecompressCommand(self, aFilename):
        if aFilename.endswith('.gz'):
            return '/bin/gunzip -c'
        return None

    def mDownloadLogFile(self, aNode, aSrcFile, aDstFile, aOffset, aSize,
            aNodeType):
        ebLogDiag('DBG', ' Download %s : %d bytes from %d' % 
                (aSrcFile, aSize, aOffset))
        _dst_dir = os.path.dirname(aDstFile)
        if not os.access(_dst_dir, os.F_OK):
            os.makedirs(_dst_dir)

        # use compression for large data transfer over ssh
        _compress = (aSize > 65535) and aNodeType != 'cps'

        # use decompression command for compressed file
        _decompress = self.mGetDecompressCommand(aSrcFile)

        try:
            if _compress:
                _outfile = open('%s.gz'%aDstFile, 'wb')
            else:
                # Use append mode to collect
                # renamed old logs and newly created logs into the same file
                _outfile = open(aDstFile, 'ab')
        except IOError as e: # pragma: no cover
            ebLogDiag('ERR', 'Error while downloading %s : %s' % (aSrcFile, e))
            return

        def _read_cb(data):
            _outfile.write(data)
        def _err_cb(data):
            ebLogDiag('ERR', 'Error while downloading %s : %s' % (aSrcFile, data))

        if _decompress:
            _cmd = '%s %s' % (_decompress, aSrcFile)
            if aOffset:
                _cmd += ' | /usr/bin/tail -c +%d' % (aOffset + 1)
            if aSize:
                _cmd += ' | /usr/bin/head -c %d' % (aSize)
            if _compress:
                _cmd += ' | /bin/gzip - -c'
        else:
            _cmd = '/usr/bin/tail %s -c +%d' % (aSrcFile, aOffset + 1)
            if aSize:
                _cmd += ' | /usr/bin/head -c %d' % (aSize)
            if _compress:
                _cmd += ' | /bin/gzip - -c'

        if aNodeType == 'cps':
            try:
                # cps exacloud run as user 'ecra'
                _cmd = '/usr/bin/sudo %s' % _cmd
                _cmds = _cmd.split('|')
                _procs = []
                for i, _command in enumerate(_cmds):
                    _procs.append(subprocess.Popen(
                        shlex.split(_command),
                        stdin=_procs[-1].stdout if i else None,
                        stdout=subprocess.PIPE if i < len(_cmds) - 1 else _outfile))
                for _proc in _procs:
                    _proc.wait()
            except Exception as ex:
                ebLogDiag('ERR', 'Error while downloading %s : %s' % (aSrcFile, ex))
                _outfile.close()
                return
        else:
            aNode.mExecuteCmdAsync(_cmd, (_read_cb, None, _err_cb, None))

        _outfile.close()
        if _compress:
            # append
            #os.system('gunzip %s.gz -c >> %s' % (aDstFile, aDstFile))
            try:
                with gzip.open('%s.gz' % aDstFile, 'rb') as _infile:
                    with open(aDstFile, 'ab') as _outfile:
                        shutil.copyfileobj(_infile, _outfile)
            except IOError as e: # pragma: no cover
                ebLogDiag('ERR', 'Error while downloading %s : %s' % (aSrcFile, e))
            finally:
                os.remove('%s.gz'%aDstFile)

    def mTruncateIncompleteLog(self, aFilename, aLogInfo):
        _start_pattern = aLogInfo.get('start_of_msg', '')
        _end_pattern = aLogInfo.get('end_of_msg', '\n')
        _file = open(aFilename, 'r+')
        _file.seek(0, os.SEEK_END)
        _file_size = _file.tell()

        # check normal case first
        _file.seek(_file_size - len(_end_pattern))
        if _file.read() == _end_pattern:
            _file.close()
            return _file_size

        def _find_last_pos(aFile, aPattern):
            _offset = _file_size
            _read_size = 512
            while _offset > 0:
                _offset -= _read_size
                if _offset < 0:
                    _offset = 0
                aFile.seek(_offset)
                _buf = aFile.read(_read_size + len(aPattern))
                _pos = _buf.rfind(aPattern)
                if _pos != -1:
                    return _pos
            return -1

        _new_size = 0
        if _start_pattern:
            # don't need to search start pattern without \n : it is pos 0 case
            _pos = _find_last_pos(_file, '\n' + _start_pattern)
            if _pos != -1:
                _new_size = _pos + 1    # for \n
        else:
            _pos = _find_last_pos(_file, _end_pattern)
            if _pos != -1:
                _new_size = _pos + len(_end_pattern)

        if self.__debug:
            _file.seek(_new_size)
        ebLogDiag('DBG', 'truncated incomplete line: %s' % _file.read())

        _file.truncate(_new_size)
        _file.close()
        return _new_size

    def mManipulateSincedb(self, aNode, aFileName, aFileInfoMap, aSizeChange,
            aNodeType):
        _inode, _size, _timestamp = aFileInfoMap[aFileName]
        _new_size = _size + aSizeChange
        _sed_pattern = r's/^(%d\s+\S+\s+\S+\s+)%d(\s+%d\s.*)$/\1%d\2/' % \
                (_inode, _size, _timestamp, _new_size)
        _cmd = '/bin/sed -i -r "%s" %s' % (_sed_pattern, self.__sincedb)
        self.mExecuteCmd(_cmd, aNode, aNodeType)

    def mUpdateCpsMarkerWithLocking(self, aPath, aIntervalSec):
        try:
            if not os.access(os.path.dirname(aPath), os.F_OK):
                os.makedirs(os.path.dirname(aPath))
            if not (os.access(aPath, os.F_OK) and os.path.getsize(aPath)>0):
                ebLogDiag('NFO', 'Create cps marker %s' % aPath)
                _cps_dict = {}
                _cps_dict['last_scan_time'] = -1
                with open(aPath, 'w') as _fp:
                    _fp.write(json.dumps(_cps_dict))
            with open(aPath, 'r+') as _fp:
                _cps_dict = json.load(_fp)
                _cur_time = time.time()
                _last_scan_time = _cps_dict['last_scan_time']
                if _last_scan_time < _cur_time - aIntervalSec:
                    ebLogDiag('NFO',
                        'Update cps marker and continue running job on CPS')
                    _cps_dict['last_scan_time'] = _cur_time
                    _fp.seek(0)
                    _fp.truncate()
                    _fp.write(json.dumps(_cps_dict, indent=4))
                    _fp.flush()
                    return True
                else:
                    ebLogDiag('NFO',
                        'Skip updating cps marker and stop running job on CPS')
                    return False
        except Exception as e: # pragma: no cover
            ebLogDiag('WRN', 'Failed to update %s: %s' % (aPath, e))
            return False

    def mCopyCPSLog(self):
        # logs that do not require delta collection will be copied everytime
        ebLogDiag('NFO', 'Copy CPS logs to log repo %s' % self.__log_repo)
        # get CPS log targets from rackinfo.conf
        if 'cps' not in self.__rackconfig['log_collection_targets']:
            ebLogDiag('ERR', 'Failed to get cps log target from rackinfo.conf')
            return
        _targets = self.__rackconfig['log_collection_targets']['cps']
        if not _targets:
            ebLogDiag('ERR', 'cps log target is empty in rackinfo.conf')
            return

        # copy CPS logs
        for _target in _targets:
            if _target not in self.__cps_logs_to_copy:
                continue
            ebLogDiag('NFO', 'Copy CPS log %s' % _target)
            _list_index = self.__cps_logs_to_copy.index(_target)
            _target = self.__cps_logs_to_copy[_list_index]
            _category = _targets[_target]['category']
            _filename = _targets[_target]['filename']

            # change file permission/owner and copy to log repo
            # copy to predefined path and rename later, to avoid cmd injection
            _tmp_file = '%s/_tmp_cps_log' % self.__log_repo
            _user = os.getuid()
            _group = os.getgid()
            if not os.access(self.__log_repo, os.F_OK):
                os.makedirs(self.__log_repo)
            _rc, _, _stderr = self.mExecuteCmd(
                    '/usr/bin/install -m 644 -o %s -g %s %s %s' % (
                        _user, _group, _target, _tmp_file), None, 'cps')
            if _rc or _stderr:
                ebLogDiag('ERR', 'Failed to copy CPS log %s: %s' % (
                            _target, _stderr))
                continue

            # make a log repo
            _cps_log_repo = '%s/%s/%s' % (
                        self.__log_repo, _category, socket.gethostname())
            if not os.access(_cps_log_repo, os.F_OK):
                os.makedirs(_cps_log_repo)

            _dst_path = '%s/%s' % (_cps_log_repo, _filename)

            try:
                os.rename(_tmp_file, _dst_path)
            except OSError as e:
                ebLogDiag('ERR', 'Failed to rename CPS log: %s' % e)

    def mCompressLog(self):
        ebLogDiag('NFO', 'Compress logs collected by job %s' % self.__uuid)
        _tar_path = '%s/%s.tar.gz' % (self.__log_repo_base, self.__uuid)
        _num_chunks = 0
        _chunk_size = int(self.__tar_chunk_size)

        # skip compressing logs when nothing was collected
        if not os.access(self.__log_repo, os.F_OK):
            return

        # make compressed log files with configured size of chunks
        # file name will be like <uuid>.tar.gz.00, <uuid>.tar.gz.01, ...
        try:
            # compress
            with tarfile.open(_tar_path, mode='w:gz') as _out_tar:
                _out_tar.add(self.__log_repo, self.__uuid)
            shutil.rmtree(self.__log_repo)
            # split
            with open(_tar_path, 'rb') as _tar_file:
                for _chunk in iter(lambda: _tar_file.read(_chunk_size), b''):
                    _split_file_path = '%s.%02d' % (_tar_path, _num_chunks)
                    _num_chunks += 1
                    with open(_split_file_path, 'wb') as _split_file:
                        _split_file.write(_chunk)
            os.remove(_tar_path)
        except (tarfile.TarError, OSError): # pragma: no cover
            ebLogDiag('ERR', 'Failed to compress and delete %s' % self.__uuid)
            ebLogDiag('ERR', traceback.format_exc())

        return str(_num_chunks)

    def mCleanFiles(self):
        _log_repos = []
        _log_repos.append(self.__log_repo_base)
        _log_repos.append(self.__domu_chainsaw_repo)
        _log_repos.append('%s/log/diagnostic/' % self.__base_path)
        for _log_repo in _log_repos:
            if not os.path.exists(_log_repo):
                continue
            for _file in os.listdir(_log_repo):
                _file_path = os.path.join(_log_repo, _file)
                try:
                    _last_modified = os.stat(_file_path).st_mtime
                except Exception as e: # pragma: no cover
                    ebLogDiag('WRN',
                        'Failed to get file info during cleanup: %s' % e)
                    continue
                if _last_modified < self.__day_ago:
                    ebLogDiag('NFO', 'Delete %s' % _file_path)
                    try:
                        if os.path.isdir(_file_path):
                            shutil.rmtree(_file_path)
                        else:
                            os.remove(_file_path)
                    except OSError as e: # pragma: no cover
                        ebLogDiag('ERR',
                                  'Failed to delete %s (%s)' % (_file_path, e))

    def mValidateHostname(self, aHostname):
        # getaddrinfo() is being used for hostname validation
        # gaierror is raised for invalid hostname
        try:
            socket.getaddrinfo(aHostname, 22)
        except socket.gaierror:
            raise Exception('Invalid hostname: %s' % aHostname)

    def mGetHostname(self, aNode, aNodeType):
        if aNodeType == 'cps':
            try:
                # get FQDN if possible
                _hostname = subprocess.check_output(
                        ['hostname', '-f']).decode('utf8').rstrip()
            except:
                _hostname = os.environ.get('HOSTNAME', 'cpshost')
        else:
            _hostname = aNode.mGetHostname()
        self.mValidateHostname(_hostname)
        return _hostname

    def mExecuteLocal(self, aCmd, aCurrDir=None, aShell=False):
        if aShell == False:
            _args = shlex.split(aCmd)
        else:
            _args = aCmd
        _current_dir = aCurrDir
        _stdin = subprocess.PIPE
        _stdout = subprocess.PIPE
        _stderr = subprocess.PIPE
        # Security Bug 36292289
        # Discussion with Varsha Mohan at 2024-03-29
        #  - Varsha requested validation for command input
        #  - _hostname from mGetHostname() is the only arg from external source
        #  - Varsha agreed that _hostname is being validated by mValidateHostname()
        _proc = subprocess.Popen(_args, stdin=_stdin, stdout=_stdout,
                stderr=_stderr, cwd=_current_dir, shell=aShell)
        if aShell == False:
            _out, _err = wrapStrBytesFunctions(_proc).communicate()
        else:
            _out, _err = _proc.communicate()
        _rc = _proc.returncode
        return _rc, _out, _err
    
    def mExecuteCmd(self, aCmd, aNode, aNodeType, aShell=False):
        if aNodeType == 'cps':
            # cps exacloud run as user 'ecra'
            _rc, _out, _err = self.mExecuteLocal(
                    '/usr/bin/sudo %s' % aCmd, None, aShell)
        else:
            # dom0, domU or cell
            _, _o, _e = aNode.mExecuteCmd(aCmd)
            _out = _o.read() 
            _err = _e.read() 
            _rc = aNode.mGetCmdExitStatus()
        return _rc, _out, _err

    def mMakeDir(self, aPath, aNode, aNodeType):
        if aNodeType == 'cps':
            # cps exacloud run as user 'ecra'
            _rc, _, _ = self.mExecuteLocal(
                    '/usr/bin/sudo /bin/mkdir -p %s' % aPath)
        elif aNodeType == 'domU':
            # domU run as user 'opc'
            _rc, _, _ = self.mExecuteCmd(
                    '/bin/mkdir -p %s' % aPath, aNode, aNodeType)
        else:
            # dom0, cell
            _rc = aNode.mMakeDir(aPath)
        return _rc

    def mFileExists(self, aFile, aNode, aNodeType):
        if aNodeType == 'cps':
            _rc = os.path.exists(aFile)
        else:
            _rc = aNode.mFileExists(aFile)
        return _rc

    def mReadFile(self, aFile, aNode, aNodeType):
        if aNodeType == 'cps':
            with open(aFile) as f:
                _out = f.read()
        else:
            _out = aNode.mReadFile(aFile).decode('utf-8')
        return _out

    # aRegex    text to be replaced
    # aNewRegex text to replace
    # aTextToAppend    text to append aNewRegex if aRegex does not exist
    # aAppendBelowText append aNewRegex to the line below aTextToAppend if true
    #                  append aNewRegex to the line above aTextToAppend if false
    def mReplaceInFile(self, aPath, aNode, aNodeType,
            aRegex, aNewRegex, aTextToAppend, aAppendBelowText=True):
        _is_updated = False;
        # check if new regex exactly exists in the file
        _rc, _, _ = self.mExecuteCmd(
                "/bin/grep -x '%s' %s" % (aNewRegex, aPath), aNode, aNodeType)
        if _rc:
            # if regex exists in the file, remove whole line
            self.mExecuteCmd(
                    "/bin/sed -i '/%s/d' %s" % (aRegex, aPath),
                    aNode, aNodeType)
            if not aTextToAppend:
                # append new regex to end of the file
                self.mExecuteCmd(
                        "/bin/sed -i '$a %s' %s" % (aNewRegex, aPath),
                        aNode, aNodeType)
            else:
                if aAppendBelowText:
                    # append new regex to the line below aTextToAppend
                    self.mExecuteCmd(
                            "/bin/sed -i '/%s/a %s' %s" %
                                    (aTextToAppend, aNewRegex, aPath),
                            aNode, aNodeType)
                else:
                    # append new regex to the line above aTextToAppend
                    self.mExecuteCmd(
                            "/bin/sed -i '/%s/i %s' %s" %
                                    (aTextToAppend, aNewRegex, aPath),
                            aNode, aNodeType)
            _is_updated = True
        return _is_updated

    # aPatterns list of patterns in order that needs to be appended
    # aTextToAppend pattern of text below which the new list of patterns are appended
    #               if none, the patterns will be appended from last lin of the filee
    def mAddInFile(self, aPath, aPatterns, aNode, aNodeType, aTextToAppend=None):
        _rc = True
        for pattern in aPatterns:
            _rc &= self.mReplaceInFile(aPath, aNode, aNodeType,
                    pattern, pattern, aTextToAppend)
            aTextToAppend = pattern
        return _rc

    # aPatterns list of patterns in order that needs to be verified for its presence
    def mCheckInFile(self, aPath, aPatterns, aNode, aNodeType):
        for pattern in aPatterns:
            _rc, _, _ = self.mExecuteCmd(
                    "/bin/grep -x '%s' %s" % (pattern, aPath), aNode, aNodeType)
            if _rc:
                return False
        return True
        
    def mVerifyAideConf(self, aPath, aNode, aNodeType, aPatterns):
        # check if there is any mistake in the file
        _rc, _, _ = self.mExecuteCmd(
                "/usr/sbin/aide --config-check --config=%s" % aPath,
                aNode, aNodeType)
        if _rc: # pragma: no cover
            return False
        # check if pattern exactly exists in the file
        for _pattern in aPatterns:
            _rc, _, _ = self.mExecuteCmd(
                    "/bin/grep -x '%s' %s" % (_pattern,aPath), aNode, aNodeType)
            if _rc: # pragma: no cover
                return False
        return True
    
    def mConfigureSelinux(self, aComponent, aLogDir, aNode, aNodeType, aHost):
        _rc, _out, _ = self.mExecuteCmd(
                    "/sbin/sestatus | /bin/grep 'SELinux status:'",
                    aNode, aNodeType)
        if _rc:
            ebLogDiag('ERR', 'Failed to get SELinux status of %s' % aHost)
            return
        else:
            if _out.strip().split(':')[1] == 'disabled':
                # skip configuration
                return
        ebLogDiag('NFO', 'Update SELinux configuration on %s' % aHost)
        if aComponent == 'av':
            _rc, _, _ = self.mExecuteCmd(
                    "/usr/sbin/setsebool -P antivirus_can_scan_system 1",
                    aNode, aNodeType)
            if _rc:
                ebLogDiag('ERR', 'Failed to enable antivirus_can_scan_system ' \
                        'on %s' % aHost)
            else:
                ebLogDiag('NFO', 'Enabled antivirus_can_scan_system on %s' \
                        % aHost)
        if aNodeType == 'cps':
            _rc, _, _ = self.mExecuteCmd(
                    "/usr/bin/chcon -t var_log_t %s" % ' '.join(aLogDir),
                    aNode, aNodeType)
            if _rc:
                ebLogDiag('ERR', 'Failed to change %s type to var_log_t on %s' \
                        % (aLogDir, aHost))
            else:
                ebLogDiag('NFO', 'Changed %s type to var_log_t on %s' \
                        % (aLogDir, aHost))
        return
 
    def mRunAvFim(self, aOptions):
        _support_node_types = ['dom0', 'domU', 'cell', 'cps']
        _db = ebGetDefaultDB()

        # validate parameters
        if aOptions.diagtype == 'all':
            _target_node_types = _support_node_types
        else:
            _target_node_types = aOptions.diagtype.split(',')
            for _target in _target_node_types:
                if _target not in _support_node_types: # pragma: no cover
                    ebLogDiag('ERR', 'Ignore unknown node type %s' % _target)
                    _target_node_types.remove(_target)
            if len(_target_node_types) == 0: # pragma: no cover
                raise Exception('Invalid node type for %s' % aOptions.diagtype)

        # make config lock file
        self.mMakeConfigLockFile([self.__cps_marker_avfim])

        # get node list (dom0, domU, cell)
        _all_dom0s = set()
        _all_domUs = set()
        _all_cells = set()
        self.mGetNodeList(_all_dom0s, _all_domUs, _all_cells, set())

        # get rack info (cabinet, hwrack, cluster) from the metadata json
        _cluster_name = self.__ecc.mGetClusterName()
        _node_list = [_all_dom0s, _all_domUs, _all_cells]
        _rack_info = self.mGetRackInfo(aOptions, _cluster_name, _node_list)

        # eval the number of target nodes
        _total_target_cnt = 0
        if 'dom0' in _target_node_types:
            _total_target_cnt += len(_all_dom0s)
        if 'domU' in _target_node_types:
            _total_target_cnt += len(_all_domUs)
        if 'cell' in _target_node_types:
            _total_target_cnt += len(_all_cells)

        # read avfim repo which contains rpms
        if not (os.path.exists(self.__avfim_repo) and
                os.access(self.__avfim_repo, os.F_OK)): # pragma: no cover
            ebLogDiag('ERR',
                    'Failed to access directory: %s' % self.__avfim_repo)
            return 1

        # make a list of rpms in avfim repo
        _rpm_files = glob.glob('%s/*.rpm' % self.__avfim_repo)
        if not len(_rpm_files) > 0: # pragma: no cover
            ebLogDiag('ERR',
                    'No rpm found in the directory: %s' % self.__avfim_repo)
            return 1

        # _rpm_info stores packageInfo of latest rpms
        # _rpm_info = {_pkg_linux_ver(None/6/7) : {_pkg_name : _pkg_info}}
        _rpm_info = {}
        for _rpm_file in _rpm_files:
            # ignore zero size rpm file
            if not (os.access(_rpm_file, os.F_OK) and
                os.path.getsize(_rpm_file) > 0): # pragma: no cover
                ebLogDiag('ERR', 'Invalid rpm: %s' % _rpm_file)
                continue

            try:
                # query rpm info
                _, _out, _ = self.mExecuteCmd('/bin/rpm -qp --qf ' \
                        '%%{NAME}/%%{VERSION}/%%{RELEASE}/%%{BUILDTIME} %s'
                        % _rpm_file, None, 'cps')
                _output = _out.strip().split('/')
                _pkg_name = _output[0]
                _pkg_version = _output[1]
                _pkg_release = _output[2]
                _linux_ver = 'None'
                if '.el' in _pkg_release:
                    match = re.search(r'\.el(\d+)', _rpm_file)
                    # find a number follwing linux distribution 'el'
                    if match:
                        _linux_ver = match.group(1)
                _pkg_linux_ver = _linux_ver
                _pkg_build_time = int(_output[3])
                _pkg_info = packageInfo(_rpm_file, _pkg_name, _pkg_version,
                                        _pkg_release, _pkg_linux_ver,
                                        _pkg_build_time)
                # find latest rpms in a directory
                _latest_build_time = -1
                if _linux_ver in _rpm_info:
                    if _pkg_name in _rpm_info[_linux_ver]:
                        _latest_build_time = \
                            _rpm_info[_linux_ver][_pkg_name].pkg_build_time
                if _pkg_build_time > _latest_build_time:
                    if _linux_ver not in _rpm_info:
                        _rpm_info[_linux_ver] = {}
                    _rpm_info[_linux_ver][_pkg_name] = _pkg_info
            except Exception as e: # pragma: no cover
                ebLogDiag('ERR',
                        'Failed to query and parse rpm info of %s: %s' %
                        (_rpm_file, e))
                continue

        # run AV/FIM management from dom0s, domUs(ADB-D only), and cells
        def _call_avfim_install_run(aNodeType, aNodeList, aCompleteTargetCnt):
            ebLogDiag('NFO', 'Starting %s AV/FIM management from %s' 
                    % (aNodeType, _cluster_name))
            for _node in aNodeList:
                _progress_pct = (100 * aCompleteTargetCnt/_total_target_cnt)
                self.__job.mSetStatusInfo(
                        'True:%d:Running AV/FIM management from %s' %
                        (_progress_pct, _node))
                _db.mUpdateRequest(self.__job)
                self.mAvFimInstallAndRun(_node, aNodeType, _rpm_info)
                aCompleteTargetCnt += 1
            return aCompleteTargetCnt

        _complete_target_cnt = 0
        if 'dom0' in _target_node_types:
            _complete_target_cnt = _call_avfim_install_run('dom0',
                    _all_dom0s, _complete_target_cnt)
        if 'domU' in _target_node_types:
            _complete_target_cnt = _call_avfim_install_run('domU',
                    _all_domUs, _complete_target_cnt)
        if 'cell' in _target_node_types:
            _complete_target_cnt = _call_avfim_install_run('cell',
                    _all_cells, _complete_target_cnt)

        # run AVFIM on CPS
        if 'cps' in _target_node_types:
            self.mAvFimInstallAndRunOnCPS(_rpm_info)

        self.__job.mSetStatusInfo('True:100:Done')
        return 0

    def mAvFimInstallAndRunOnCPS(self, aRpmInfo):
        # set last run time to CPS marker to avoid duplicated AV/FIM run
        # run on CPS if more than 30 min have passed since last run time
        with file_lock_manager(self.__cps_marker_avfim + '.lock'):
            _rc = self.mUpdateCpsMarkerWithLocking(self.__cps_marker_avfim,1800)
        if _rc:
            self.mAvFimInstallAndRun(self.mGetHostname(None, 'cps'), 'cps', aRpmInfo)

    def mAvFimInstallAndRun(self, aHost, aNodeType, aRpmInfo):
        ebLogDiag('NFO',
                'Start to install and run AV/FIM from %s' % aHost)
        _node = None
        _host_tmpdir = '/tmp/avfim'
        if aNodeType != 'cps':
            # connect
            _node = exaBoxNode(get_gcontext())
            try:
                _node.mConnect(aHost, aTimeout=20)
            except Exception as e: # pragma: no cover
                ebLogDiag('WRN', 'Skip AV/FIM management on %s ' \
                          '(Failed to connect: %s)' % (aHost, e))
                return False

            # create a temp directory on each host
            _rc = self.mMakeDir(_host_tmpdir, _node, aNodeType)
            if not _rc: # pragma: no cover
                ebLogDiag('ERR','Failed to create temp directory on %s' % aHost)

        # check linux OS version
        _linux_version = ''
        _rc, _out, _ = self.mExecuteCmd('/bin/uname -r', _node, aNodeType)
        _uname = _out.strip().lower()
        if _rc:
            ebLogDiag('ERR', 'Failed to get Linux OS version info')
        match = re.search(r'el(\d+)uek', _uname)
        # find a number follwing linux distribution 'el'
        if match:
            _linux_version = match.group(1)
            ebLogDiag('DBG', 'Linux OS version: %s' % _linux_version)
        else:
            ebLogDiag('ERR', 'Failed to detect Linux OS version: %s' % _uname)

        # check installed version and upload rpm
        _rpm_need_install = ''
        for _pkg_linux_ver in [_linux_version, 'None']:
            if _pkg_linux_ver not in aRpmInfo:
                continue
            for _pkg_name in aRpmInfo[_pkg_linux_ver]:
                _need_install = False
                _pkg_info = aRpmInfo[_pkg_linux_ver][_pkg_name]
                _rpm_file = _pkg_info.rpm_file
                _pkg_version = _pkg_info.pkg_version
                _pkg_release = _pkg_info.pkg_release
                _pkg_build_time = _pkg_info.pkg_build_time
                _rc, _out, _ = self.mExecuteCmd(
                        '/bin/rpm -q --qf %%{VERSION}-%%{RELEASE} %s' % \
                        _pkg_name, _node, aNodeType)
                if _rc:
                    _need_install = True
                    ebLogDiag('DBG', '%s is not found in %s' \
                            '\nThe package will be installed' %
                            (_pkg_name, aHost))
                else:
                    _installed_version = _out.strip()
                    _, _out, _ = self.mExecuteCmd(
                            '/bin/rpm -q --qf %%{BUILDTIME} %s' % _pkg_name,
                            _node, aNodeType)
                    _installed_build_time = int(_out.strip())
                    # compare buildtime of rpm and installed package
                    if _pkg_build_time > _installed_build_time:
                        _need_install = True
                        ebLogDiag('DBG', 'Different version of ' + _pkg_name
                                + ' is installed in ' + aHost
                                + '\nInstalled: '+ _installed_version
                                + '\nUpgrading: '+ _pkg_version+'-'+_pkg_release
                                + '\nThe package will be upgraded')
                    else:
                        ebLogDiag('DBG', '%s is found in %s' \
                                '\nSkipping package installation' %
                                (_pkg_name, aHost))
                if _need_install:
                    if aNodeType != 'cps':
                        _target_path = _host_tmpdir+'/'+_rpm_file.split('/')[-1]
                    else:
                        _target_path = _rpm_file
                    _rpm_need_install += _target_path + ' '
                    # upload rpm
                    if aNodeType != 'cps':
                        ebLogDiag('NFO',
                                'Upload %s to host: %s' % (_rpm_file, aHost))
                        _node.mCopyFile(_rpm_file, _target_path)

        # install rpm
        if _rpm_need_install:
            if aNodeType == 'dom0':
                _cmd = '/usr/bin/yum install -y --disablerepo=* --nogpgcheck %s' % \
                        _rpm_need_install
                _rc, _out, _err = self.mExecuteCmd(_cmd, _node, aNodeType)
                if _rc: # pragma: no cover
                    ebLogDiag('WRN', 'Failed to install rpms to %s. ' \
                            'Will try again with rpm cmd:\n%s' % (aHost, _err))
                    _cmd = '/bin/rpm --nosignature --nodeps --force -iUvh %s' %\
                           _rpm_need_install
                    _rc, _out, _err = self.mExecuteCmd(_cmd, _node, aNodeType)
            else:
                # cell and cps where yum is disabled
                _cmd = '/bin/rpm --nosignature --nodeps --force -iUvh %s' % \
                       _rpm_need_install
                _rc, _out, _err = self.mExecuteCmd(_cmd, _node, aNodeType)
            if _rc: # pragma: no cover
                ebLogDiag('ERR', 'Failed to install rpms to %s:\n%s' %
                    (aHost, _err))
            else:
                ebLogDiag('NFO', 'Installed rpms to %s:\n%s' % (aHost, _out))

        # set ClamAV config value
        _av_db_path = '/opt/clamav/data'
        _av_log_path = '/var/log/clamav/clamav.log'
        _av_log_dir = '/var/log/clamav'
        _av_qtn_dir = '/var/log/clamav/quarantine'

        # run ClamAV
        # We run cmd in the bg and use nice/ionice to reduce system load.
        # 1) create a log directory
        # 2) run clamav with following options
        #    e.g. clamscan --database /opt/clamav/data
        #                  --copy /var/log/clamav/quarantine
        #                  --max-filesize 64M --max-scansize 64M
        #                  --log /var/log/clamav/clamav.tmp.log
        #                  --recursive --infected
        #                  --exclude-dir <dirs>
        # 3) change log name clamav.tmp.log to clamav.log
        _rc,_,_ = self.mExecuteCmd(
                '/bin/ps aux|/bin/grep /usr/bin/clamscan|/bin/grep -v grep',
                _node, aNodeType)
        if _rc:
            self.mMakeDir(_av_log_dir, _node, aNodeType)
            self.mMakeDir(_av_qtn_dir, _node, aNodeType)
            _rc, _, _ = self.mExecuteCmd('/usr/bin/test -f %s' % _av_qtn_dir,
                    _node, aNodeType)
            self.mConfigureSelinux('av', [_av_log_dir, _av_qtn_dir],
                    _node, aNodeType, aHost)
            if _rc:
                # command from OCI VM systemd clamscan.service
                ebLogDiag('NFO', 'Run ClamAV on %s' % aHost)
                self.mExecuteCmd("/usr/bin/nohup /bin/sh -c '"
                            + " /bin/nice -19 /usr/bin/ionice -c2 -n7"
                            + " /usr/bin/clamscan --database=" + _av_db_path
                            + " --copy=" + _av_qtn_dir
                            + " --max-filesize=64M --max-scansize=64M"
                            + " --log " + _av_log_dir + "/clamav.tmp.log"
                            + " --recursive --infected"
                            + " --exclude-dir=^/etc/selinux/"
                            + " --exclude-dir=^/tmp/access_data"
                            + " /etc /bin /sbin /lib /lib64"
                            + " /usr/bin /usr/sbin /usr/lib /usr/lib64"
                            + " /boot /root /tmp /home /run/user /var/tmp;"
                            + " /bin/mv -f " + _av_log_dir + "/clamav.tmp.log"
                            + " " + _av_log_path + ";' 1>/dev/null 2>&1 &",
                            _node, aNodeType)
            else:
                ebLogDiag('ERR', 'Failed to run ClamAV. ' \
                        '%s does not exist in %s' % (_av_qtn_dir, aHost))
        else:
            ebLogDiag('NFO', 'Skip running ClamAV on %s' % aHost)

        # set AIDE config value
        _fim_db_path = '/var/lib/aide/aide.exacd.db.gz'
        _fim_db_dir = '/var/lib/aide'
        _fim_log_path = '/var/log/aide_exacd/aide.exacd.log'
        _fim_log_dir = '/var/log/aide_exacd'
        _fim_cfg_path = '/etc/aide.exacd.conf'

        # aide exclusion list
        _aide_exclusion_patterns = [
            "# ECS AIDE SCAN EXCLUSION LIST",
            "!\/opt\/clamav",
            "!\/bin\/clam.*",
            "!\/usr\/bin\/clam.*",
            "!\/etc\/nftables\/exadata.nft.*",
            "!\/opt\/python-vmbackup"]

        # create a new aide.exacd.conf based on Exadata AIDE conf
        _exadata_aide_conf = '/etc/exadata/config/exadata_aide.conf'
        _run_aide = True
        ebLogDiag('NFO', 'Copy and update Exadata AIDE conf file on %s' % aHost)
        _rc, _, _ = self.mExecuteCmd('/usr/bin/test -f %s' % _exadata_aide_conf,
                _node, aNodeType)
        if _rc: # pragma: no cover
            ebLogDiag('ERR', 'Failed to get Exadata AIDE conf on %s' % aHost)
            _run_aide = False
        else:
            # build pattern list
            _patterns = [
                "@@define LOGDIR %s" % _fim_log_dir,
                "database=file:@@{DBDIR}/aide.exacd.db.gz",
                "database_out=file:@@{DBDIR}/aide.exacd.db.new.gz",
                "report_url=file:@@{LOGDIR}/aide.exacd.tmp.log",
                "syslog_format=yes",
                "#!/etc/exadata/config/exadata_aide.conf\$"]

            # copy conf
            _fim_temp_cfg_path = _fim_cfg_path + ".temp"
            self.mExecuteCmd('/bin/cp -f %s %s' %
                    (_exadata_aide_conf, _fim_temp_cfg_path), _node, aNodeType)
            
            # update conf
            _rc = list()
            _rc.append(self.mReplaceInFile(_fim_temp_cfg_path, _node, aNodeType,
                    "@@define LOGDIR",
                    _patterns[0],
                    "@@define DBDIR"))
            _rc.append(self.mReplaceInFile(_fim_temp_cfg_path, _node, aNodeType,
                    "database=file:@@{DBDIR}",
                    _patterns[1],
                    "# The location of the database to be read."))
            _rc.append(self.mReplaceInFile(_fim_temp_cfg_path, _node, aNodeType,
                    "database_out=file:@@{DBDIR}",
                    _patterns[2],
                    "# The location of the database to be written."))
            _rc.append(self.mReplaceInFile(_fim_temp_cfg_path, _node, aNodeType,
                    "report_url=file:@@{LOGDIR}",
                    _patterns[3],
                    "report_url=stdout", False))
            _rc.append(self.mReplaceInFile(_fim_temp_cfg_path, _node, aNodeType,
                    "syslog_format=",
                    _patterns[4],
                    "# Default."))
            _rc.append(self.mReplaceInFile(_fim_temp_cfg_path, _node, aNodeType,
                    "!\/etc\/exadata\/config\/exadata_aide.conf\$",
                    _patterns[5],
                    "# Ignore file: \/etc\/exadata\/config\/"
                    + "exadata_aide.conf content changes"))
            
            # append new line before adding exclusion list
            self.mExecuteCmd("[[ $(/usr/bin/tail -n 1 %s) != $'' ]] && /bin/sed -i '$a\\\\' %s" %
                        (_fim_temp_cfg_path, _fim_temp_cfg_path), _node, aNodeType)
            self.mAddInFile(_fim_temp_cfg_path, _aide_exclusion_patterns, _node, aNodeType)      
            # verify conf
            _isVerified = self.mVerifyAideConf(_fim_temp_cfg_path,
                    _node, aNodeType, _patterns + _aide_exclusion_patterns)
            if _isVerified:
                self.mExecuteCmd('/bin/mv -f %s %s' % 
                        (_fim_temp_cfg_path, _fim_cfg_path), _node, aNodeType)
            else: # pragma: no cover
                ebLogDiag('ERR','Failed to update aide.exacd.conf on %s'% aHost)
                _run_aide = False

        # run AIDE
        # We run cmd in the bg and use nice/ionice to reduce system load.
        # 1) create log and db directories
        # 2) if aide DB does not exist,
        #    2-1) initialize DB
        #         e.g. aide --init --config /etc/aide.exacd.conf
        #    2-2) change db name aide.exacd.db.new.gz to aide.exacd.db.gz
        #    2-3) run aide
        #         e.g. aide --check --config /etc/aide.exacd.conf
        # 3) if aide DB exists,
        #    3-1) run aide and update DB
        #         e.g. aide --update --config /etc/aide.exacd.conf
        #    3-2) change db name aide.exacd.db.new.gz to aide.exacd.db.gz
        # 4) change log name aide.exacd.tmp.log to aide.exacd.log
        _rc, _, _ = self.mExecuteCmd(
                '/bin/ps aux|/bin/grep config=%s|/bin/grep -v grep' % \
                _fim_cfg_path, _node, aNodeType)
        if (_run_aide and _rc):
            self.mMakeDir(_fim_log_dir, _node, aNodeType)
            self.mMakeDir(_fim_db_dir, _node, aNodeType)
            _rc, _, _ = self.mExecuteCmd('/usr/bin/test -f %s' % _fim_db_path,
                    _node, aNodeType)
            self.mConfigureSelinux('fim', [_fim_log_dir],
                    _node, aNodeType, aHost)
            if _rc:
                # command from OCI VM systemd aideinit.service
                ebLogDiag('NFO', 'Initialize AIDE DB on %s' % aHost)
                self.mExecuteCmd("/usr/bin/nohup /bin/sh -c '"
                        + " /bin/nice -19 /usr/bin/ionice -c2 -n7"
                        + " /usr/sbin/aide --init"
                        + " --config=" + _fim_cfg_path
                        + " && /bin/mv -f " + _fim_db_dir
                        + "/aide.exacd.db.new.gz"
                        + " " + _fim_db_path + ";"
                        + " /bin/nice -19 /usr/bin/ionice -c2 -n7"
                        + " /usr/sbin/aide --check"
                        + " --config=" + _fim_cfg_path + ";"
                        + " /bin/mv -f " + _fim_log_dir + "/aide.exacd.tmp.log"
                        + " " + _fim_log_path + "' 1>/dev/null 2>&1 &",
                        _node, aNodeType)
            else:
                # command from OCI VM systemd aidescan.service
                ebLogDiag('NFO', 'Run AIDE on ' + aHost)
                self.mExecuteCmd("/usr/bin/nohup /bin/sh -c '"
                        + " /bin/nice -19 /usr/bin/ionice -c2 -n7"
                        + " /usr/sbin/aide --update"
                        + " --config=" + _fim_cfg_path + ";"
                        + " /bin/mv -f " + _fim_db_dir + "/aide.exacd.db.new.gz"
                        + " " + _fim_db_path + ";"
                        + " /bin/mv -f " + _fim_log_dir + "/aide.exacd.tmp.log"
                        + " " + _fim_log_path + "' 1>/dev/null 2>&1 &",
                        _node, aNodeType)
        else:
            ebLogDiag('NFO', 'Skip running AIDE on %s' % aHost)

        # Bug 37521984 update /etc/aide.conf if there are any new config to be added
        _dflt_cfg_path = '/etc/aide.conf'
        _dflt_tmp_cfg_path = _dflt_cfg_path+"ecs.tmp"
        _rc, _, _ = self.mExecuteCmd('/usr/bin/test -f %s' % _dflt_cfg_path, _node, aNodeType)
        _isPatternPresent = self.mCheckInFile(_dflt_cfg_path, _aide_exclusion_patterns, _node, aNodeType)

        if _rc == 0 and not _isPatternPresent:
            ebLogDiag('NFO', 'Updating /etc/aide.conf on %s' % aHost)
            self.mExecuteCmd('/bin/cp -f %s %s' %
                    (_dflt_cfg_path, _dflt_tmp_cfg_path), _node, aNodeType) 
            # append new line before adding exclusion list
            self.mExecuteCmd("[[ $(/usr/bin/tail -n 1 %s) != $'' ]] && /bin/sed -i '$a\\\\' %s" %
                    (_dflt_tmp_cfg_path, _dflt_tmp_cfg_path), _node, aNodeType)
            self.mAddInFile(_dflt_tmp_cfg_path, _aide_exclusion_patterns, _node, aNodeType)
            # verify conf
            _isVerified = self.mVerifyAideConf(_dflt_tmp_cfg_path,
                    _node, aNodeType, _aide_exclusion_patterns)
            if _isVerified:
                self.mExecuteCmd('/bin/mv -f %s %s' %
                        (_dflt_tmp_cfg_path, _dflt_cfg_path), _node, aNodeType)
                ebLogDiag('NFO', 'Run AIDE using /etc/aide.conf on ' + aHost)
                self.mExecuteCmd("/usr/bin/nohup /bin/sh -c '"
                        + "/opt/oracle.SupportTools/exadataAIDE -update"
                        + "' 1>/dev/null 2>&1 &",
                        _node, aNodeType)
            else:
                ebLogDiag('ERR','Failed to update /etc/aide.conf on %s'% aHost)
        else:
            ebLogDiag('NFO','Skipping AIDE update using /etc/aide.conf on %s'% aHost)

        # clean up
        self.mExecuteCmd('/bin/rm -rf %s' % _host_tmpdir, _node, aNodeType)
        ebLogDiag('NFO', 'Removed temp directory on %s' % aHost)

#TBD : Add diagnostic logs also    
def ebDownloadLog(aParams, aResponse, aDestDir='/tmp'):
    
    _uuid_s  = aParams['uuid']
    #file list
    if not os.path.isdir(aDestDir):
        os.makedirs(aDestDir)
    _tar_file       = aDestDir + '/' + _uuid_s + '.tar.gz'
    _oeda_log_dir   = 'oeda/requests/' + _uuid_s + '/log/'
    _log_file       = 'log/threads/' + _uuid_s + '*.log'
    _diagnostic_file= 'log/diagnostic/' + _uuid_s + '*.log'
    _exacloud_log   = 'log/exacloud.log'
    _database_log   = 'log/database.log'
    _agent_log      = 'log/agent.log'
    _exabox_conf    = 'config/exabox.conf'
    _cluster_xml    = 'oeda/requests/' + _uuid_s + '/exacloud.conf/*.xml'
    
    _log_list = [_oeda_log_dir, _log_file, _diagnostic_file, _exacloud_log, _database_log, 
                _agent_log, _exabox_conf, _cluster_xml]
    
    #generate new tar everytime
    #30464944 - Add compressing option (gz) to tar creation
    if os.path.isfile(_tar_file):
        os.remove(_tar_file)
    _out_tar = tarfile.open(_tar_file, mode='w:gz')

    #check logs' size before adding them to the tarball
    _sizesum = 0 #accumulator for file sizes
    _log_file_list = list() #new list for file paths

    for _log_file in _log_list:
        for _file in glob.glob(_log_file):

            _sizesum += os.path.getsize(_file) #weigh each file and add filesize to accumulator
            _log_file_list.append(_file) #add file to new list

    #calculate available space in destination directory
    _fs_size = os.statvfs(aDestDir)
    avail_space = _fs_size.f_frsize * _fs_size.f_bavail

    #if log files fit in destination directory then tar them up, else keep tarball empty.
    if _sizesum<avail_space:
        for _file in _log_file_list:
            _out_tar.add(_file)

    else: # pragma: no cover
        ebLogWarn("Log file is too big for staging directory "+aDestDir+".\nPlease specify alternate default directory as 'default_logdir' in exabox.conf.")

    _out_tar.close()
    _response = aResponse
    _response['file'] = _tar_file
    _response['delete_temp'] = True #flag file for deletion after download

    return



