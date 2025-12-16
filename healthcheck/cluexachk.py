"""
 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    cluexachk.py - Refactored from cluhealth to provide exachk functionality

FUNCTION:
    Implements Exachk invocation code from Healthcheck

NOTE:
    None

History:
    ririgoye  25/11/25 - Bug 38667586 - EXACS: MAIN: PYTHON3.11: SUPRASS ALL PYTHON WARNINGS
    jesandov  22/07/25 - Bug 38222270: Avoid locking on AHF DomU Install in ExaCS
    akkar     01/25/24 - Bug:37151441 - Remove Ahf_setup file from domU after installation 
    jesandov  04/05/25 - 36482990: Avoid locking on AHF DomU Install in ExaScale
    akkar     01/25/24 - Bug:36085104 - Add support for AHF installation on
                            EXASCALE
    pbellary    21/06/2023 - Bug 35516786: ERROR IN MULTIPROCESSING INTERMITTENTLY IN PRE_VM_CHECKS STEP
    akkar       12/05/2023 - Bug 35326504: Parallelize AHF installation
    ndesanto    12/05/2022 - Bug 34804581 - Fix for lock not releasing by using
                             a Context Managers to warranty locks are released.
                             Also added a timeout
    dekuckre    06/12/2020 - Add fix for 31476866
    jungnlee    01/01/2018 - fixed wrong hc filename, minor code defects
    bhuvnkum    06/29/2017 - Creation

"""

import os
import fcntl
import glob
import shutil
import zipfile

from contextlib import contextmanager
from datetime import datetime
from enum import Enum
from exabox.core.Mask import maskSensitiveData
from os import path
from pathlib import Path
from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError, gProvError
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, \
    ebLogSetHCLogDestination, ebLogRemoveHCLogDestination, ebLogHealth
from exabox.ovm.clumisc import ebCluSshSetup
from exabox.utils.node import connect_to_host
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure

CTRL_PLN_LOCK = "/exachk_lk"

class LockMode(Enum):
    SHARED = 1
    EXCLUSIVE = 2

class FileLockMgr():
    def __init__(self, lockfile):
        if not lockfile.startswith("/"):
            msg = "absolute path to be given"
            raise Exception(msg)
        self.lockfile = lockfile
        self.fd = 0
        self.check_and_create_file()

    def __del__(self):
        if self.fd:
            fcntl.flock(self.fd.fileno(), fcntl.LOCK_UN)
            self.fd.close()

    def check_and_create_file(self):
        if not os.path.exists(self.lockfile):
            Path(self.lockfile).touch()

    def file_lock(self, mode):
        '''
        This function locks the file in shared/exclusive based on the given mode. 
        Multiple shared operations are possible in parallel by taking shared lock. 
        If shared lock is taken then exclusive lock cannot be taken
        If exclusive lock is taken then no other lock can be taken
        If lock is taken by other process, this function blocks until the lock gets released
        '''
        lock = False
        try:
            if not isinstance(mode,LockMode):
                raise TypeError('mode should be LockMode')
            if mode == LockMode.SHARED:
                ebLogInfo(" Trying SHARED lock for file: %s" %(self.lockfile))
                self.fd = open(self.lockfile, "r")
                self.fd.flush()
                fcntl.flock(self.fd.fileno(), fcntl.LOCK_SH)
            elif mode == LockMode.EXCLUSIVE:
                ebLogInfo(" Trying EXCLUSIVE lock for file: %s" %(self.lockfile))
                self.fd = open(self.lockfile, "w")
                self.fd.flush()
                fcntl.flock(self.fd.fileno(), fcntl.LOCK_EX)
            ebLogInfo("Got %s lock  for file: %s" %(mode, self.lockfile))
            lock = True
        except Exception as e:
            ebLogError("Got Exception %s while trying to lock file: %s" %(str(e), self.lockfile))
            lock = False
        return lock


@contextmanager
def obtain_cp_lock(lockfile, mode):
    shared_lock = None
    try:    
        try:
            shared_lock = FileLockMgr(lockfile)
            yield shared_lock.file_lock(mode)
        except Exception as err:
            ebLogError(f"Error while creating lock {lockfile} "\
                f"with exception:\n{err}\n")
            yield False
    except StopIteration:
        return
    finally:
        if shared_lock and shared_lock.fd:
            fid = shared_lock.fd.fileno()
            ebLogInfo(f"Unlocking {mode} lock on File Descriptor: {fid}")
            fcntl.flock(fid, fcntl.LOCK_UN)
            shared_lock.fd.close()
            ebLogInfo(f"File Descriptor {fid} is closed for {mode} lock")


@contextmanager
def obtain_remote_lock(eBox):
    try:
        if eBox.SharedEnv():
            eBox.mAcquireRemoteLock()
        try:
            yield eBox
        except StopIteration:
            return
    finally:
        if eBox.SharedEnv():
            eBox.mReleaseRemoteLock()


class ebCluExachk(object):

    EXACHK_PATH = '/opt/oracle.ahf/exachk'

    def __init__(self, aCluHealthCheck, aOptions):
        self.__hc= aCluHealthCheck
        # Bug27556005 - Get ssh setup class object and use the same for both 
        # ssh key generate and cleanup 
        self.__ssh_env_setup = None
        self.__debug = False
        self.ahf_copy_path = None

    def mGetCluHealthCheck(self):
        return self.__hc

    def mSetupExachkEnv(self, aDom0, aNodesList):
        """
        setup passwordless access to other dom0, cells & switches to run exachk.
        """
        self.__ssh_env_setup = ebCluSshSetup(self.mGetCluHealthCheck().mGetEbox())
        # Set passwordless connection between dom0 and cells/ibswitches
        if self.__ssh_env_setup:
            _key = self.__ssh_env_setup.mSetSSHPasswordless(aDom0, aNodesList)        


    def mCleanupExachkEnv(self, aDom0, aNodesList):
        """
        cleanup passwordless access to other dom0, cells & switches.
        """
        # Clean passwordless connection between dom0 and cells/ibswitches
        if self.__ssh_env_setup:
            self.__ssh_env_setup.mCleanSSHPasswordless(aDom0, aNodesList) 
        
 
    def mRunExachk(self, aOptions=None):
        _hc = self.mGetCluHealthCheck()
        _ebox = _hc.mGetEbox()
        os.environ["RAT_ECRA"] = "1"
        os.environ["RAT_ROOT_COLLECTIONS_IN_SERIAL"] = "1"
        os.environ["RAT_NOCLEAN_DIR"] = "1"
        
        if _ebox.mIsOciEXACC():
            ebLogInfo('AHF/Exack operations skipped for exacc')
            return

        try:
            #install ahf on all dom0s
            self.mInstallAhf("dom0",aOptions)
            # check if only ahf installtion request
            if aOptions.jsonconf.get('other'):
                if aOptions.jsonconf['other'] == 'ahf_install_dom0':
                    ebLogInfo(f'Request only for AHF installation on dom0 , skipping other flows of exachk!')
                    return
        except Exception as _detail_error:
            ebLogError('*** ' + _detail_error)
            _ebox.mUpdateErrorObject(gProvError['ERROR_AHF_INSTALL_FAIL'],_detail_error)
            raise ExacloudRuntimeError(0x0129, 0x0A, "Failure during AHF installation setup")
        try:
            #install ahf on all standby cps - only for exacc
            self.mInstallAhfOnRemoteCps(aOptions) 
        except Exception as _detail_error:
            ebLogError('*** ' + _detail_error)
            _ebox.mUpdateErrorObject(gProvError['ERROR_AHF_INSTALL_FAIL'],_detail_error)
            raise ExacloudRuntimeError(0x0129, 0x0A, "Failure during AHF installation setup")
        ebLogInfo('*** Exachk execution on control plane in progress')
        self.mRemoteRunExachk(aOptions)
        
     #
     # Run Exachk utility v4
     #
     #prerequisites to run exachk healthcheck:
     #1. exachk must be installed at location '/opt/oracle.SupportTools/exachk'
     #2. exachk executable must be added in PATH so that it can be executed remotely from ssh command  (using /etc/profile.d/exachk_env.sh)
     #3. root has passwordless ssh access to all of the other respective dbnodes
     #4. exachk should be integrated with exacloud command line options
     #

    def mRemoteRunExachk(self, aOptions=None):
        _hc    = self.mGetCluHealthCheck()
        _ebox = _hc.mGetEbox()
        _cluster_path = _ebox.mGetClusterPath()
        _recommend = _hc.mGetRecommend()
        _jsonMap = _hc.mGetJsonMap()
        
        _testResult = "Fail"
        _jsonMap['Exachk'] = {}
        _jsonMap['Exachk']['hostCheck'] = {}
        _dom0Checked = False
        _domuChecked = False
        _ecmode = 0
        _jconf = {}
        
        DOM0_MODE       = 1    
        DOMU_MODE       = 2
        DOM0_DOMU_MODE  = 3
        DEFAULT_MODE    = 5 # Default mode dom0,cells and switches
        ALL_MODE        = 7
        #compute exachk path
        _exachk_path_ctx = get_gcontext().mGetBasePath()
        if _exachk_path_ctx[-1] !=  '/':
            _exachk_path_ctx = _exachk_path_ctx + '/'

        #ahf remote install path - same for dom0 & domU   
        if aOptions is not None and aOptions.jsonconf is not None and 'ahf_install_path' in aOptions.jsonconf.keys():
            _ahf_ctrl_install_path = aOptions.jsonconfi.get('ahf_ctrl_install_path')
        elif _ebox.mCheckConfigOption('ahf_ctrl_install_path'):
            _ahf_ctrl_install_path = _ebox.mCheckConfigOption('ahf_ctrl_install_path')
        else:
            _ahf_ctrl_install_path  = _exachk_path_ctx + 'ahf_install'

        _ahf_bin_path = _exachk_path_ctx + 'ahf_setup'
        _tmp_local_path = "/tmp"
        if aOptions is not None and aOptions.jsonconf is not None:
            _jconf = aOptions.jsonconf
            if 'other' in list(aOptions.jsonconf.keys()):
                if _jconf["other"].lstrip().rstrip().startswith('-tmpdir'):
                    _tmp_local_path = _jconf["other"].lstrip().rstrip().split("-tmpdir")[1].strip()
        try:
            #check ahf_installation exist on control plane and install if does not exist
            _iret = self.mSetupAhfonCtrlPlane(_ahf_bin_path,_ahf_ctrl_install_path,_tmp_local_path)
        except Exception as e:
                _ebox.mUpdateErrorObject(gProvError['ERROR_AHF_INSTALL_FAIL'],e)
                raise ExacloudRuntimeError(0x0129, 0x0A, "Failure during AHF installation setup")
        finally:
            del os.environ["RAT_ECRA"]
        
        if _iret == False:
            ebLogError('ERROR: ahf install failed in path %s' % (_ahf_ctrl_install_path))
            _recommend.append('ERROR: ahf_install failed on path : %s' % (_ahf_ctrl_install_path))
            _jsonMap['Exachk']['hostCheck']['logs'] = _recommend[-1]
            _jsonMap['Exachk']['hostCheck']['TestResult'] = "Fail"
            return
            
        if aOptions is not None and aOptions.jsonconf is not None:
            _jconf = aOptions.jsonconf
            _jconf_masked = maskSensitiveData(_jconf)  
            if self.__debug:
                ebLogInfo('INFO: *** json payload for exachk healthcheck:\n %s' % (_jconf_masked))
        else:
            _jconf = {}
            _ecmode = DEFAULT_MODE
            ebLogInfo('INFO: *** json payload for exachk healthcheck not provided, Running Default Mode.')    
            ebLogHealth('NFO', '*** json payload for exachk healthcheck not provided, Running Default Mode.')    
            _recommend.append('INFO: *** json payload for exachk healthcheck not provided, Running Default Mode.')

        if _jconf.get("dom0_verify") == "True":
            _ecmode = DOM0_MODE
               
        if _jconf.get("domu_verify") == "True" and not _ebox.isATP():
                _ecmode = _ecmode | DOMU_MODE
                
        if not _ecmode & ALL_MODE:
            _ecmode = DEFAULT_MODE
        
        #read exachk path on remote host from config/healthcheck.conf
        _exachk_bin_path = _ahf_ctrl_install_path + '/oracle.ahf/bin/exachk'
        if not os.path.isfile(_exachk_bin_path):
            ebLogError('ERROR: exachk path not found: %s' % (_exachk_bin_path))
            _recommend.append('ERROR: exachk path not found: %s' % (_exachk_bin_path))
            _jsonMap['Exachk']['hostCheck']['logs'] = _recommend[-1]
            _jsonMap['Exachk']['hostCheck']['TestResult'] = "Fail"
            return
        
        _tmp_log_destination = ebLogSetHCLogDestination(_hc.mGetLogHandler(), True)
        _cluster_host_d = _hc.mGetClusterHostD()
            
        _dom0s, _domUs, _cells, _switches = _ebox.mReturnAllClusterHosts()
        if _ebox.mIsExabm() or _ebox.mIsOciEXACC():
            _ddp = _ebox.mReturnDom0DomUNATPair()
            _dUs = []
            for _, _du in _ddp:
                _dUs.append(_du)
            _domUs = _dUs

        _hostList = []
            
        if (_ecmode & DOM0_MODE):
            _hostList = _dom0s
        elif (_ecmode & DOMU_MODE):
            _hostList = _domUs
        else:
            pass
        #
        # Check if host is pingable
        #
        if _hostList[0]:
            _host = _hostList[0]
            _clunode = _cluster_host_d[_host]
            #_cluhealth = _cluster_health_d[_host]
            _cmd_param = []

            ebLogInfo('*** *** Execute Exachk for %s' % (_host))
            ebLogHealth('NFO', '*** *** Execute Exachk for %s' % (_host))
            #initialize jsonMap
            _jsonMap['Exachk']['hostCheck'][_host] = {}
            _jsonMap['Exachk']['hostCheck'][_host]['logs'] = {}
            _jsonMap['Exachk']['hostCheck'][_host]['NodeType'] = _clunode.mGetNodeType()
            _jsonMap['Exachk']['hostCheck'][_host]['TestResult'] = _testResult
            _loglist = []
            
            #
            # Check if node is pingable
            #
            if _clunode.mGetPingable():
                #function to parse command line params to build exachk cmd
                def _build_exachk_cmd_param(_host, _cluster_host_d):
                    _param_list = []
                    #silentforce is always required to run exachk in background w/o any user interruption
                    _param_list = ['-silentforce', '-ecra', '-keep_output_dir']
                    if _clunode.mGetNodeType() == 'dom0':

                        if (_ecmode & DOMU_MODE):
                            _param = ['-clusternodes' , ",".join(_dom0s+_domUs)]
                        else:
                            _param = ['-clusternodes' , ",".join(_dom0s)]
                        _param_list = _param_list + _param

                        if (_jconf.get("cell_verify") == "True") or (_ecmode == DEFAULT_MODE):
                            _param = ['-cells' , ",".join(_cells)]
                            _param_list = _param_list + _param

                        if not _ebox.mIsKVM() and ((_jconf.get("switch_verify") == "True") or (_ecmode == DEFAULT_MODE)):
                            _param = ['-ibswitches' , ",".join(_switches)]
                            _param_list = _param_list + _param
                    
                    elif _clunode.mGetNodeType() == 'domu':
                        _param = ['-clusternodes' , ",".join(_domUs)]
                        _param_list = _param_list + _param
                                
                    #add other params
                    if "db_check" in list(_jconf.keys()):
                        _param = [_jconf["db_check"].strip()]
                    else:
                        _param = ['-dball'] #for default case
                    _param_list = _param_list + _param

                    if "other" in list(_jconf.keys()):
                        _param = _jconf["other"].lstrip().rstrip().split(" ")
                        _param_list = _param_list + _param

                    #by default, it will run exachk using root user
                    if _jconf.get("remoteuser") and (_ecmode & DOMU_MODE):
                        _param = ['-remoteuser' , _jconf["remoteuser"]]
                        _param_list = _param_list + _param

                    if _jconf.get("identitydir") and os.path.isfile(_jconf["identitydir"]) :
                        _param = [' -identitydir' ,  _jconf["identitydir"]]
                    else:
                        _oeda_keys_dir = os.path.join(self.__hc.mGetEbox().mGetOedaPath(), "WorkDir")
                        _param = ['-identitydir' , _oeda_keys_dir ]
                    _param_list = _param_list + _param

                    return _param_list


                #build exachk command with given command line params
                _cmd_param = _build_exachk_cmd_param(_host, _cluster_host_d)
                #output dir for exachk zip file
                _exachk_output_dir = _cluster_path + '/exachk/' + _ebox.mGetUUID() + '_' + str(datetime.now().strftime('%m%d%y_%H%M%S'))
                try:
                    os.stat(_exachk_output_dir)
                except:
                    os.makedirs(_exachk_output_dir)
                

                #execute exachk with command line params
                # -dbnone : to skip all db's
                # -dball  :  to select all db's 
                # either of above 2 options are required to avoid exachk waiting to select db

                # -output : provide option to define exachk result dir
                # -b      : Runs only the best practice checks.
                # -silentforce  : hidden options provide run exachk in silent mode
                #above check is reqrd to run healthchk on dom0, otherwise it will ask for root pwd
                #for storage nodes and InfiniBand switches 
                
                ebLogInfo('*** Start Running Exachk Healthcheck***') 
                ebLogHealth('NFO', 'Start Running Exachk Healthcheck')
                ctrl_lock_filename = get_gcontext().mGetBasePath() + CTRL_PLN_LOCK
                with obtain_cp_lock(ctrl_lock_filename, LockMode.SHARED) as lock_state:
                    try:
                        # Try to take shared control plane lock, because parallel exachk execution is allowed
                        if lock_state == False:
                            ebLogError('*** Exachk Failed - could not get ctrl pln lock ***')
                            _jsonMap['Exachk']['hostCheck'][_host]['logs'][0] = "could not get ctrl pln lock"
                            _jsonMap['Exachk']['hostCheck'][_host]['TestResult'] = "Fail"
                            return

                        PYTHONPATH = os.environ["PYTHONPATH"]
                        if PYTHONPATH:
                            os.environ["PYTHONPATH"] = ""
                        with obtain_remote_lock(_ebox):
                            _cmdlist = [_exachk_bin_path,'-output',_exachk_output_dir+"/" ]
                            _cmdlist = _cmdlist + _cmd_param
                            ebLogInfo('*** *** Execute Exachk on Control Plane. Command %s \n please wait, this will take a few minutes..'\
                            % (_cmdlist))
                            ebLogHealth('NFO','*** *** Execute Exachk on control plane. command: %s \n please wait, this will take a few minutes..'\
                            % (_cmdlist))
                            _out,_err = _ebox.mExecuteCmdLog2(_cmdlist)
                            if _err:
                                #exachk command failed due to invalid arguement passed
                                ebLogInfo('ERROR: on host %s: mExecuteCmd Failed: %s output: %s error: %s' % (_host, _cmdlist, \
                                    _out, _err))
                                ebLogHealth('ERR', 'on host %s: mExecuteCmd Failed: %s ' % (_host, _cmdlist))
                                _recommend.append('ERROR: on host %s: mExecuteCmd Failed: %s ' % (_host, _cmdlist))
                                _jsonMap['Exachk']['hostCheck'][_host]['logs'][0] = _recommend[-1]
                                _jsonMap['Exachk']['hostCheck'][_host]['TestResult'] = "Fail"
                                #disconnect current node and try to run exachk on other
                                if _ebox.SharedEnv():
                                    _ebox.mReleaseRemoteLock()
                                #Releasing lock after exachk execution
                                # del shared_lock
                                return

                        def _get_exachk_result():
                            #below command will give us only last modified json report 
                            _file_list = glob.glob('{0}/exachk*.zip'.format(_exachk_output_dir))
                            _file_str = ' '.join([str(_file) for _file in _file_list])
                            return _file_str

                        #fetch exack generated zip file
                        os.environ["PYTHONPATH"] = PYTHONPATH
                        _exachk_zip_path = _get_exachk_result()
                        if _exachk_zip_path is not None:
                            #Copy .json result files to diagnostic result path
                            if "diag_root" in _hc.mGetHcConfig():
                                exachk_zip = zipfile.ZipFile(_exachk_zip_path)
                                _diag_result_path = _hc.mGetHcConfig()["diag_root"] + '/diagnostic/results/exachk/'
                                try:
                                    os.stat(_diag_result_path)
                                except:
                                    os.makedirs(_diag_result_path)
                        
                                [exachk_zip.extract(file, _diag_result_path) \
                                for file in exachk_zip.namelist() if file.endswith('.json')]
                                exachk_zip.close()

                            if _clunode.mGetNodeType() == 'dom0':
                                _dom0Checked  = True
                                _domuChecked  = True
                            elif _clunode.mGetNodeType() == 'domu':
                                _domuChecked  = True
                            else:
                                pass

                            if "exachk_zip_dir" in _hc.mGetHcConfig():
                                exachk_zip_dir = _hc.mGetHcConfig()["exachk_zip_dir"]
                                try:
                                    os.stat(exachk_zip_dir)
                                except:
                                    os.makedirs(exachk_zip_dir)
                                clustername = None
                                _node = exaBoxNode(get_gcontext())
                                try:
                                    _node.mConnectTimed(aHost=_host, aTimeout="10")
                                    _cmd = '/usr/bin/ipmitool sunoem cli \"show /SYSTEM serial_number\" | grep \"serial_number =\" | awk \'{print $NF}\''
                                    _i, _o, _e = _node.mExecuteCmd(_cmd)
                                    if _node.mGetCmdExitStatus():
                                        ebLogError('*** Dom0 Serial number fetch failed on host %s with error %s ' % (_host,str(_e.readlines())))
                                        ebLogError('*** cluster name used in exachk zip instead of Dom0 Serial number')
                                        clustername = _ebox.mGetClusterName()
                                    else:
                                        _out = _o.readlines()
                                        clustername = _out[0].lstrip().rstrip()
                                        ebLogInfo('*** clustername {0}: '.format(clustername))
                                except Exception as e:
                                    ebLogError('*** Exception while fetching serial number : {0}: '.format(str(e)))
                                    ebLogError('*** cluster name used in exachk zip instead of Dom0 Serial number')
                                    clustername = _ebox.mGetClusterName()
                                    if _ebox.mGetCmd() == 'checkcluster':
                                        raise Exception('Exception while fetching serial number : {0}: '.format(str(e)))

                                try:
                                    if clustername:
                                        zip_file_name = _exachk_zip_path.split('/')[-1]
                                        # remove .zip to get the directory name
                                        src_exachk_folder_name = _exachk_zip_path[:-4]
                                        _args = '_'
                                        #Add profile name if profile used in args
                                        if "other" in list(_jconf.keys()):
                                            if _jconf["other"].lstrip().rstrip().startswith('-profile'):
                                                _args += _jconf["other"].lstrip().rstrip().split("-profile")[1].strip() + '_'
                                        zip_file_name = zip_file_name.split("_")
                                        if len(zip_file_name) < 4:
                                            raise Exception("The file name does not have the required fields. List Index Out of Range error.")
                                        date = zip_file_name[2] + zip_file_name[3]
                                        zip_file_name = zip_file_name[0] + "_" + zip_file_name[1] + "_" + clustername + _args + date.split('.')[0]
                                        ebLogInfo('*** *** zip name %s: ' % (zip_file_name))
                                        exachk_zip_dir = exachk_zip_dir + '/' + zip_file_name
                                        #replacing the directory name with the computed cluster name
                                        dst_exachk_folder_name  = src_exachk_folder_name.replace(src_exachk_folder_name.split('/')[-1],"") + "tmp"
                                        ebLogInfo('*** *** source result at %s: ' % (src_exachk_folder_name))
                                        ebLogInfo('*** *** destination result at %s: ' % (dst_exachk_folder_name))
                                        shutil.move(src_exachk_folder_name,dst_exachk_folder_name + "/" + zip_file_name)
                                        shutil.make_archive(exachk_zip_dir,'zip',dst_exachk_folder_name)
                                        shutil.rmtree(_exachk_output_dir)
                                        ebLogInfo('*** *** result copied at %s.zip: ' % (exachk_zip_dir))
                                        _testResult = "Pass"
                                except Exception as e:
                                    ebLogError('*** Exception while computing  exachk zip name : {0}: '.format(str(e)))
                                    if _ebox.mGetCmd() == 'checkcluster':
                                        raise Exception(f"*** result copy to {exachk_zip_dir}.zip failed with error:{e}")
                            else:    
                                ebLogInfo('*** *** result copied at %s: ' % (_exachk_zip_path))
                                for _root, _dirs, _files in os.walk(_exachk_output_dir,  topdown=False):
                                    for _dir in [os.path.join(_root, _d) for _d in _dirs]:
                                        os.chmod(_dir, 0o755)
                                    for _file in [os.path.join(_root, _f) for _f in _files]:
                                        os.chmod(_file, 0o644)
                                _testResult = "Pass"

                        else:
                            ebLogInfo('WARNING: Exachk failed to generate report for %s' %(_host))
                            ebLogHealth('WRN', 'Exachk failed to generate report for %s' %(_host))
                            _recommend.append('WARNING: Exachk failed to generate report for %s' %(_host))
                            _loglist.append(_recommend[-1])
                            _testResult = "Fail"

                    except Exception as e:
                        ebLogInfo('WARNING: Error on host %s: while executing exachk %s' % (_host, str(e)))
                        ebLogHealth('WRN', 'Error on host %s: while executing exachk %s' % (_host, str(e)))
                        _recommend.append('WARNING: Error on host %s: while executing exachk %s' % (_host, str(e)))
                        _loglist.append(_recommend[-1])
                        if _ebox.mGetCmd() == 'checkcluster':
                            raise Exception('Error on host %s: while executing exachk %s' % (_host, str(e)))
                
                for i in range(len(_loglist)):
                    _jsonMap['Exachk']['hostCheck'][_host]['logs'][i] = _loglist[i]

                if len(_jsonMap['Exachk']['hostCheck'][_host]['logs']) == 0:
                    _jsonMap['Exachk']['hostCheck'][_host].pop("logs", None)

                _jsonMap['Exachk']['hostCheck'][_host]['TestResult'] = _testResult
                
            else:
                ebLogInfo('WARNING: host: %s is not pingable' % (_host))
                ebLogHealth('WRN','CheckInfo failed to connect to: %s (pingable though)' % (_host))
                _recommend.append('WARNING: host: %s is not pingable' % (_host))
                _jsonMap['Exachk']['hostCheck'][_host]['logs'][0] = _recommend[-1] 
            
        ebLogInfo('\n')
        ebLogInfo('*** Completed Running exachk\n')
        ebLogHealth('NFO', '*** Completed Running exachk \n')

        ebLogRemoveHCLogDestination(_tmp_log_destination)
        ebLogSetHCLogDestination(_hc.mGetDefaultLogHandler())
    #end mRemoteRunExachk

    def mCopyAhfImage(self, aNode, _ahf_bin_path, _remote_ahf_bin_path):
        '''
        This is an utility method used in AHF installation. It copies the ahf_setup from control plane to remote machine
        @aNode: DomU Node on which AHF will be installed
        @_ahf_bin_path: Local path where ahf_setup file present
        @_remote_ahf_bin_path : path where the ahf_setup to be stored on DomU
        '''
        _ret = False
        try:
            ebLogInfo('*** Install Ahf for host: %s' % (aNode.mGetHostname()))
            #check if dom0/domu root partition has atleast 150MB to setup exachk
            # exachk.zip: 12M + unzip exachk: 70M  + store result
            _cmdstr = 'df -PBM / | tail -1| awk \'0+$4 <= 150  {print}\''
            _, _o, _ = aNode.mExecuteCmd(_cmdstr)
            _out = _o.readlines()
            if len(_out):
                ebLogError('*** Not enough space to setup exachk(<150MB), skippig exachk run for host - %s' % (aNode.mGetHostname()))
                return _ret
            #
            # Copy ahf Image if available
            # 
            if os.path.isfile(_ahf_bin_path):
                ebLogInfo('*** Copying ahf Image to %s in progress...' %(aNode.mGetHostname()))
                if aNode.mFileExists(_remote_ahf_bin_path):
                    if aNode.mFileExists(_remote_ahf_bin_path + '/ahf_setup'):
                        ebLogInfo('*** ahf Image exist on host:%s , overriding with new one' %(aNode.mGetHostname()))
                else:
                    aNode.mMakeDir(_remote_ahf_bin_path)
                self.ahf_copy_path = f'{_remote_ahf_bin_path}/ahf_setup'
                aNode.mCopyFile(_ahf_bin_path, self.ahf_copy_path)
                _cmdstr =  'chmod 700 '  + _remote_ahf_bin_path + '/ahf_setup'
                _, _e, _ = aNode.mExecuteCmd(_cmdstr)
                if aNode.mGetCmdExitStatus():
                    ebLogError('*** could not change ahf_setup permissions for host - %s' % (aNode.mGetHostname()))
                    return _ret
                else:
                    ebLogInfo('*** AHF Image permissions changed to 700 on host %s' %(aNode.mGetHostname()))
                ebLogInfo('*** AHF Image copied  on host %s' %(aNode.mGetHostname()))
                _ret = True
            else:
                ebLogError('*** Local Ahf Image : %s not found !' % (_ahf_bin_path))

        except Exception as e:
                ebLogError('*** AHF image copy failed for host: %s with error %s' % (aNode.mGetHostname(),str(e)))
        return _ret

    def mDeleteAhfImage(self, aNode):
        """Utility method to delete ahf_setup from domU after installation.
        """
        try:
            # check ahf_setup present in the location
            if not aNode.mFileExists(self.ahf_copy_path):
                ebLogInfo(f'ahf_setup file not present in path:{self.ahf_copy_path}, skipping removal')
                return
            ebLogInfo(f'Deleting ahf_setup path at {self.ahf_copy_path}')
            _cmdstr =  f'rm {self.ahf_copy_path}'
            _, _e, _ = aNode.mExecuteCmd(_cmdstr)
            if aNode.mGetCmdExitStatus():
                ebLogError(f'*** Could not delete ahf_setup for host - {aNode.mGetHostname()}')
                return
            ebLogInfo(f'ahf_setup deleted from host :{aNode.mGetHostname()}')
        except Exception as e:
            ebLogError(f'*** ahf_setup file removal failed for host: {aNode.mGetHostname()} with error {str(e)}')

    def mChgFolderOwnShip(self,aNode,path,owner, group):
        '''
        This is an utility method to change the ownership of the folder in remote machines(DOMU/DOM0)
        @aNode: Remote machine on which folder ownership to be changed
        @path: path contains the folder name of which ownership to be changed
        @owner: The  folder ownership will be chaged to the given owner
        @group: The  folder group will be chaged to this group
        '''
        _ret = False
        try:
            base_dir = path.split('/')
            base_dir = '/' + base_dir[1]
            #Base dirctory owner ship changed to given owner 
            _cmdstr = 'chown ' + owner + ':' + group + ' ' + base_dir 
            _, _o, _e = aNode.mExecuteCmd(_cmdstr)
            if aNode.mGetCmdExitStatus():
                ebLogError(f'*** change folder ownership failed for host {aNode.mGetHostname()} with error: {_e.readlines()}')
            else: 
                ebLogInfo(f'*** Base directory {base_dir} ownership changed to {owner}:{group} for host: {aNode.mGetHostname()}')
                _ret = True
        except Exception as e:
                ebLogError('*** Got exception while changing folder ownership to %s:%s  for host: %s with error %s' % (owner,group, aNode.mGetHostname(),str(e)))
        return _ret

    def mAhfUninstall(self,aNode,_remote_ahf_install_path):
        '''
        This is method uninstalls ahf in the given path and deletes the oracle.ahf directory
        @aNode: DomU Node on which AHF will be installed 
        @_remote_ahf_install_path : path where the ahf_setup present
        '''
        _ret = True
        try:
            #check already ahf_exist for dom0. dom0 does not support upgrade, so need to uninstall the old version
            ahf_install_dir = _remote_ahf_install_path + "/oracle.ahf"
            if aNode.mFileExists(ahf_install_dir):
                ahf_uninstall_bin = ahf_install_dir + '/ahf/bin/uninstallahf.sh'
                if aNode.mFileExists(ahf_uninstall_bin):
                    _cmdstr =  ahf_uninstall_bin + ' -silent' + ' -local'
                    _, _e, _ = aNode.mExecuteCmd(_cmdstr)
                    if aNode.mGetCmdExitStatus():
                        ebLogHealth('WRN','*** AHF : Uninstallation Failed. command output for host : %s' % (aNode.mGetHostname()))
                        ebLogHealth('WRN','*** AHF : Uninstall log: %s: ' % (_e.readlines()))
                        _ret = False
                    else:
                        ebLogHealth('NFO','*** AHF : Uninstallation Success. command output for host : %s' % (aNode.mGetHostname()))
                        ebLogHealth('NFO','*** AHF : Uninstall log: %s: ' % (_e.readlines()))
                else:
                    ebLogWarn('*** AHF: Unable to uninstall Ahf, binary not found for host: %s' % (aNode.mGetHostname()))
                _cmdstr =  'rm -rf ' + ahf_install_dir
                _, _e, _ = aNode.mExecuteCmd(_cmdstr)
                if aNode.mGetCmdExitStatus():
                    ebLogError('*** AHF: Unable to delete ahf install directory %s for host: %s' % (ahf_install_dir, aNode.mGetHostname()))
                    _ret = False
                else:
                    ebLogInfo('*** AHF: ahf install directory %s deleted for host: %s' % (ahf_install_dir, aNode.mGetHostname()))
        except Exception as e:
                ebLogError('*** AHF: Got exception while uninstalling ahf for host: %s with error %s' % (aNode.mGetHostname(),str(e)))
                _ret = False
        return _ret

    def mDeleteDataDir(self, aNode):
        '''
        This method removed oracle.ahf directory if it
        is present in path other than provided data path.
        In case of zdlra, /u02 should not contain oracle.ahf
        @aNode: DomU Node on which AHF will be installed 
        '''
        _hc    = self.mGetCluHealthCheck()
        _ebox = _hc.mGetEbox()
        # oracle.ahf should not be present at /u01 in case of non-zdlra 
        _non_install_path = _ebox.mCheckSubConfigOption('ahf_paths','remote_ahf_data_path_zdlra_domu')
        if _ebox.IsZdlraProv():
            _non_install_path = _ebox.mCheckSubConfigOption('ahf_paths','remote_ahf_data_path_domu')
        _remote_old_data_dir = os.path.join(_non_install_path, "oracle.ahf")
        if aNode.mFileExists(_remote_old_data_dir):
            ebLogInfo(f'*** AHF: Data dir {_remote_old_data_dir} still exists on {_non_install_path} !')
            _cmdstr =  '/bin/rm -rf ' + _remote_old_data_dir
            _, _e, _ = aNode.mExecuteCmd(_cmdstr)
            if aNode.mGetCmdExitStatus():
                ebLogError(f'*** AHF: Unable to delete Data directory {_remote_old_data_dir} for host: {aNode.mGetHostname()}')
            else:
                ebLogInfo(f'*** AHF: Data directory {_remote_old_data_dir} deleted for host: {aNode.mGetHostname()}')
        else:
            ebLogInfo(f'*** AHF: Data directory on {_remote_old_data_dir} doesnt exist for host: {aNode.mGetHostname()}, skipping deletion')

    def mGetAhfBinVerFromCtrlPlane(self,_ctrlplane_ahf_bin_path,aNode=None):
        '''
        This method compares the local ahf_setup and  remote installed version and decides whether upgradation required or not.
        @_ctrlplane_ahf_bin_path : control plane bin path
        '''
        _ahf_bin_version = 0
        _hc    = self.mGetCluHealthCheck()
        _ebox = _hc.mGetEbox()
        _node = aNode
        
        try:
            if _node:
                if not _node.mFileExists(_ctrlplane_ahf_bin_path):
                   return _ahf_bin_version
                _cmdstr =  f"{_ctrlplane_ahf_bin_path} -v"
                _, _o, _e = _node.mExecuteCmd(_cmdstr)
                if aNode.mGetCmdExitStatus():
                   return _ahf_bin_version
                if _o:
                   _out = _o.readlines()   
            else:
                if os.path.isfile(_ctrlplane_ahf_bin_path) == False:
                   return _ahf_bin_version
                _cmdstr =  f"{_ctrlplane_ahf_bin_path} -v"
                _out,_err = _ebox.mExecuteCmdLog2(_cmdstr)
                if _err:
                   return _ahf_bin_version
            _ahf_bin_version = _out[0]
            _ahf_bin_version = _ahf_bin_version.lstrip().rstrip().split(':')
            #remove two digits to match with the pattern in remote version
            _ahf_bin_version = _ahf_bin_version[1][:-2]
            _ahf_bin_version = int(_ahf_bin_version)
        except Exception as e:
                ebLogWarn('*** AHF: Got exception while fetching ahf binary version from control plane path %s.Exception %s ' % (_ctrlplane_ahf_bin_path,str(e)))
                _ahf_bin_version = 0
                raise Exception(e)
        return _ahf_bin_version
     
    def mAhfCtrlPlaneVersionCheck(self,_ctrlplane_ahf_bin_path, _ctrlplane_ahf_install_path):
        '''
        This method compares the ctrlplane ahf_setup and  ctrlplane installed version and decides whether upgradation required or not.
        @_ctrlplane_ahf_install_path : Node path where the ahf_setup installed
        @_ctrlplane_ahf_bin_path : bin path to be verified against installed path
        '''
        _upgrade = True
        _hc    = self.mGetCluHealthCheck()
        _ebox = _hc.mGetEbox()
        try:
            ahf_install_properties = _ctrlplane_ahf_install_path + "/oracle.ahf/install.properties"
            if os.path.isfile(ahf_install_properties):
                _ahf_build_version = None
                _ahf_build_date = None

                _cmdstr = "cat " + ahf_install_properties
                _in, _out, _err = _ebox.mExecuteCmd(_cmdstr)

                _cmdstr = "grep 'BUILD_VERSION'"
                _o, _e = _ebox.mExecuteCmdLog2(_cmdstr, aStdIn=_out)
                if _o:
                    for _line in _o:
                        _ahf_build_version = _line.lstrip().rstrip()
                        break

                _cmdstr = "cat " + ahf_install_properties
                _in, _out, _err = _ebox.mExecuteCmd(_cmdstr)
                _cmdstr = "grep 'BUILD_DATE'"
                _o, _e = _ebox.mExecuteCmdLog2(_cmdstr,aStdIn=_out)
                if _o:
                    for _line in _o:
                        _ahf_build_date = _line.lstrip().rstrip()
                        break
                #compute ctrlplane install ahf version based on theoutput
                if _ahf_build_version and _ahf_build_date:
                    _ahf_build_version  = _ahf_build_version.split('=')
                    _ahf_build_version = _ahf_build_version[1]
                    _ahf_build_date = _ahf_build_date.split('=')
                    _ahf_build_date = _ahf_build_date[1]
                    _remote_version = int(_ahf_build_version + _ahf_build_date)
                    #get local ahf version
                    _ahf_bin_version = self.mGetAhfBinVerFromCtrlPlane(_ctrlplane_ahf_bin_path)
                    if _ahf_bin_version > _remote_version:
                        ebLogInfo('*** AHF : Ctrl Bin version %d is greater than Ctrl install version %d on control plane - upgrade required' % (_ahf_bin_version,_remote_version))
                    else:
                        _upgrade = False
                        ebLogInfo('*** AHF : Local version %d is smaller/equal than ctrl install version %d on control plane - upgrade not required' % (_ahf_bin_version, _remote_version))
                else:
                    ebLogInfo('*** AHF : Unable to fetch ahf ctrlplane install version on path %s for control plane:' % (ahf_install_properties))
            else:
                ebLogInfo('*** AHF : ahf installation not found on path %s for host control plane ' % (ahf_install_properties))
        except Exception as e:
                ebLogWarn('*** AHF: Got exception while retrieving ctrlplane  exachk version for control plane with error %s' % (str(e)))
                raise Exception(e)
        return _upgrade
        
    def mGetHigherAHFPath(self,aNode, aCtrlPlaneAhfBinPath):
        # TODO: Move this to init
        _hc = self.mGetCluHealthCheck()
        _ebox = _hc.mGetEbox()
        # set exacloud ahf_setup as default
        _path = _ebox.mCheckSubConfigOption('ahf_paths','remote_ahf_bin_path')
        _dbaas_ahfsetup_path = _ebox.mCheckSubConfigOption('ahf_paths','remote_ahf_dbaas_path') + "/ahf_setup"
        try:
            _ahf_exacloud_version = self.mGetAhfBinVerFromCtrlPlane(aCtrlPlaneAhfBinPath)
            _ahf_dbaas_version = self.mGetAhfBinVerFromCtrlPlane(_dbaas_ahfsetup_path, aNode)
            if _ahf_exacloud_version >= _ahf_dbaas_version:
                ebLogInfo(f'*** AHF : Exacloud version {_ahf_exacloud_version} is greater than or equal to dbaas version {_ahf_dbaas_version} on host {aNode.mGetHostname()} - use Exacloud setup ')
            else:
                ebLogInfo(f'*** AHF : Exacloud version {_ahf_exacloud_version} is smaller than dbaas version {_ahf_dbaas_version} on host {aNode.mGetHostname()} - use dbaas setup)')
                _path = _ebox.mCheckSubConfigOption('ahf_paths','remote_ahf_dbaas_path')
        except Exception as e:
                ebLogWarn('*** AHF: Got exception while comparing AHF version for host: %s with error %s' % (aNode.mGetHostname(),str(e)))
                return _path
        return _path
        
    def mRetriveAhfInstallDataPath(self,aNode, _remote_ahf_install_path):
        '''
        This method fetches the remote(dom0,domU) AHF data path.
        @aNode: DomU/Dom0 Node on which AHF will be installed 
        @_remote_ahf_install_path : Node path where the ahf_setup installed
        '''
        _data_path = ""
        try:
            ahf_exachk_bin_path = os.path.join(_remote_ahf_install_path , "oracle.ahf/install.properties")
            if aNode.mFileExists(ahf_exachk_bin_path):
                _ahf_build_version = None
                _ahf_build_date = None
                _cmdstr = f"/bin/grep 'DATA_DIR' {ahf_exachk_bin_path}"
                _, _o, _e = aNode.mExecuteCmd(_cmdstr)
                if _o:
                    _out = _o.readlines()   
                    for _line in _out:
                        if _line.startswith("DATA_DIR"):
                            _data_path = _line.split("=")[1]
                            return _data_path
        except Exception as e:
                ebLogWarn(f'*** AHF: Got exception while retrieving remote AHF installation datapath with error: {str(e)}')
        return _data_path
 
    def mGetTFACTLStatus(self, aRemoteAhfInstallPath, aNode):
        _remote_ahf_install_path = aRemoteAhfInstallPath
        # access the install properties file
        try:
            _tfa_home_location = None
            _ahf_install_properties_path = os.path.join(_remote_ahf_install_path , "oracle.ahf/install.properties")
            if aNode.mFileExists(_ahf_install_properties_path):
                _cmdstr = f'/bin/cat {_ahf_install_properties_path}'
                _, _o, _e = aNode.mExecuteCmd(_cmdstr)
                if _o:
                    _out = _o.readlines()   
                    for _line in _out:
                        _key = _line.split("=")[0]
                        if _key == 'TFA_HOME':
                            _tfa_home_location = _line.split("=")[1]
            if not _tfa_home_location:
                return False
            _tfactl_path = os.path.join(_tfa_home_location, "bin" , "tfactl")
            _tfactl_status_cmd = f'{_tfactl_path} print status'
            _, _o, _e = aNode.mExecuteCmd(_tfactl_status_cmd)
            ebLogInfo(f' *** Post AHF Install TFACTL status:')
            for _line in _o.readlines():
                _line = _line.replace("\n", "")
                if _line:
                    ebLogInfo(f'{_line}')
        except Exception as e:
                ebLogWarn(f'*** AHF: Got exception while accessing remote AHF installation with error: {str(e)}')
                return False
        return True
        
    def mAhfRemoteVersionCheck(self,aNode,_ctrlplane_ahf_bin_path, _remote_ahf_install_path,_device_type=None):
        '''
        This method compares the local ahf_setup and  remote installed version and decides whether upgradation required or not.
        @aNode: DomU Node on which AHF will be installed 
        @_remote_ahf_install_path : Node path where the ahf_setup installed
        @_ctrlplane_ahf_bin_path : bin path to be verified against installed path
        '''
        _upgrade = True
        _fresh = False
        try:
            ahf_exachk_bin_path = _remote_ahf_install_path + "/oracle.ahf/install.properties"
            if aNode.mFileExists(ahf_exachk_bin_path):
                _ahf_build_version = None
                _ahf_build_date = None
                _cmdstr = "(cat " + ahf_exachk_bin_path + " | grep 'BUILD_VERSION' )"
                _, _o, _e = aNode.mExecuteCmd(_cmdstr)
                if _o:
                    _out = _o.readlines()   
                    for _line in _out:
                        _ahf_build_version = _line.lstrip().rstrip()
                        break
                _cmdstr = "(cat " + ahf_exachk_bin_path + " | grep 'BUILD_DATE' )"
                _, _o, _e = aNode.mExecuteCmd(_cmdstr)
                if _o:
                    _out = _o.readlines()   
                    for _line in _out:
                        _ahf_build_date = _line.lstrip().rstrip()
                        break
                #compute remote ahf version based on theoutput
                if _ahf_build_version and _ahf_build_date:
                    _ahf_build_version  = _ahf_build_version.split('=')
                    _ahf_build_version = _ahf_build_version[1]
                    _ahf_build_date = _ahf_build_date.split('=')
                    _ahf_build_date = _ahf_build_date[1]
                    _remote_version = int(_ahf_build_version + _ahf_build_date)
                    #get local ahf version
                    if _device_type == "standby_cps":
                        _ahf_bin_version = self.mGetAhfBinVerFromCtrlPlane(_ctrlplane_ahf_bin_path,aNode)
                    else:
                        _ahf_bin_version = self.mGetAhfBinVerFromCtrlPlane(_ctrlplane_ahf_bin_path)
                    if _ahf_bin_version > _remote_version:
                        ebLogInfo('*** AHF : Local version %d is greater than remote version %d on host %s - upgrade required' % (_ahf_bin_version,_remote_version, aNode.mGetHostname()))
                    else:
                        _upgrade = False
                        ebLogInfo('*** AHF : Local version %d is smaller/equal than remote version %d on host %s - upgrade not required' % (_ahf_bin_version, _remote_version, aNode.mGetHostname()))
                else:
                    ebLogInfo('*** AHF : Unable to fetch ahf remote version on path for host %s: %s' % (ahf_exachk_bin_path,aNode.mGetHostname()))
            else:
                ebLogInfo('*** AHF : ahf installation not found on path %s for host : %s' % (ahf_exachk_bin_path,aNode.mGetHostname()))
                _fresh = True
        except Exception as e:
                ebLogWarn('*** AHF: Got exception while retrieving remote exachk version for host: %s with error %s' % (aNode.mGetHostname(),str(e)))
                raise Exception(e)
        return _upgrade , _fresh
       

    def mRemoveOldExachk(self,aNode):
        _old_exachk_installation = '/opt/oracle.SupportTools/exachk' 
        try:
            if aNode.mFileExists(_old_exachk_installation):
                _cmdstr =  'rm -rf ' + _old_exachk_installation
                _, _e, _ = aNode.mExecuteCmd(_cmdstr)
                if aNode.mGetCmdExitStatus():
                    ebLogError('*** AHF: old exachk version found but, could not delete on path %s for host: %s' % (_old_exachk_installation, aNode.mGetHostname()))
                else:
                    ebLogInfo('*** AHF: old exachk version found and deleted on path %s for host: %s' % (_old_exachk_installation, aNode.mGetHostname()))
        except Exception as e:
            ebLogError('*** AHF: old exachk version detection on path %s for host failed : %s' % (_old_exachk_installation, aNode.mGetHostname()))


    def mSetupAhfonCtrlPlane(self,_ahf_bin_path, _ctrl_ahf_install_path,_tmp_local_path = "/tmp"):
        '''
        This is an utility method used in Dom0/DomU AHF installation. It checks and created the required install directories
        @_ahf_bin_path: Local path where ahf_setup file present
        @_ctrl_ahf_install_path : path where the ahf_setup to be installed
        '''
        _ret = False
        _hc    = self.mGetCluHealthCheck()
        _ebox = _hc.mGetEbox()
        try:
            #check the version binary and remote, if upgrade not required then skip ahf install
            _upgrade = self.mAhfCtrlPlaneVersionCheck(_ahf_bin_path, _ctrl_ahf_install_path)
            if _upgrade == False:
                _ret = True
                return _ret
            #check the ahf executable present or not 
            if not os.path.isfile(_ahf_bin_path):
                ebLogError('*** AHF: ahf binary not preset in ctrl plane at path %s ' % (_ahf_bin_path))
                return _ret
            # Try to take exclusive control plane lock, because no operation allowed during ahf installtion
            ctrl_lock_filename = get_gcontext().mGetBasePath() + CTRL_PLN_LOCK
            with obtain_cp_lock(ctrl_lock_filename, LockMode.EXCLUSIVE) as lock_state:
                if lock_state == False:
                    ebLogError('*** Exachk Failed - could not get ctrl pln lock ***')
                    return False
                try:
                    os.stat(_ctrl_ahf_install_path)
                except:
                    os.mkdir(_ctrl_ahf_install_path)
                ebLogInfo('*** installing AHF Image on path %s of control plane in progress...' %(_ctrl_ahf_install_path))
                _cmdstr = _ahf_bin_path + ' -silent -local -ahf_loc ' + _ctrl_ahf_install_path + ' -data_dir ' + _ctrl_ahf_install_path +  ' -tmp_loc ' + _tmp_local_path
                ebLogInfo('*** installing AHF command to execute:  %s ' %(_cmdstr))
                _o, _e = _ebox.mExecuteCmdLog2(_cmdstr)
                ebLogInfo(_o)
                if _e:
                    ebLogHealth('WRN','*** AHF : Install failed on control plane. Error log : %s: ' % (str(_e)))
                    _ret = False
                else:
                    ebLogHealth('NFO','*** AHF : Install success on control plane : %s: ' % (str(_o)))
                    _ret = True
        except Exception as e:
            _ret = False
            ebLogError('*** AHF install failed on control plane with exception : %s' % (str(e)))
            raise Exception(e)
        return _ret

 
    def mSetupAhfonRemote(self,aNode, _deviceType, _ahf_bin_path, _remote_ahf_bin_path, _remote_ahf_install_path,_remote_ahf_data_path):
        '''
        This is an utility method used in Dom0/DomU AHF installation. It checks and created the required install directories
        @aNode: DomU Node on which AHF will be installed 
        @_ahf_bin_path: Local path where ahf_setup file present
        @_remote_ahf_bin_path : path where the ahf_setup to be stored
        @_remote_ahf_install_path : path where the ahf_setup to be installed
        @_remote_ahf_data_path: data path to be used while installing ahf
        '''
        _hc    = self.mGetCluHealthCheck()
        _ebox = _hc.mGetEbox()
        _ret = False
        _env_type = 'exacc' if _ebox.mIsOciEXACC() else 'exacs'
        try:
            #check install path & data path exist in remote system
            if (aNode.mFileExists(_remote_ahf_install_path) and aNode.mFileExists(_remote_ahf_data_path)):
                ebLogInfo('*** remote ahf install path, data path exist')
            else:
                ebLogError('*** remote ahf install and data path does not exist.install path: %s, data path %s'%(_remote_ahf_install_path,_remote_ahf_data_path))
                return _ret
            #check the version of local and remote, if upgrade not required then skip ahf install
            _upgrade, _fresh = self.mAhfRemoteVersionCheck(aNode,_ahf_bin_path, _remote_ahf_install_path,_deviceType)
            if _upgrade == False and _deviceType != "domU":
                _ret = True
                return _ret
        
            if _deviceType != "standby_cps":
                #remove if any very old exachk version present  
                self.mRemoveOldExachk(aNode)
                _ret = self.mCopyAhfImage(aNode,_ahf_bin_path,_remote_ahf_bin_path)
                if _ret == False:
                    ebLogError('*** AHF image copy failed for host : %s  ' % (aNode.mGetHostname()))
                    return _ret
            if _deviceType == "domU":
                _data_path_domu = _ebox.mCheckSubConfigOption('ahf_paths','remote_ahf_data_path_domu')
                if _ebox.IsZdlraProv():
                    _data_path_domu = _ebox.mCheckSubConfigOption('ahf_paths','remote_ahf_data_path_zdlra_domu')
                #get data_path location and if data location is not u02 then uninstall AHF on do fresh install
                _data_path = self.mRetriveAhfInstallDataPath(aNode,_remote_ahf_install_path)
                ebLogInfo(f"*** AHF _data_path on host {aNode.mGetHostname()} : {_data_path}")
                # skip installation if path is correct and version not new
                if _data_path.startswith(_data_path_domu) and _upgrade == False:
                    ebLogInfo(f"*** Skipping AHF installation on host:{aNode.mGetHostname()}")
                    _ret = True
                    return _ret
                ebLogInfo('*** Uninstall and install AHF for domU. host: %s' % (aNode.mGetHostname()))
                _ret = self.mAhfUninstall(aNode, _remote_ahf_install_path)
                if _ret == False:
                    ebLogError('*** AHF Uninstall failed for host : %s  ' % (aNode.mGetHostname()))
                #verify if data directory is removed from non install path
                self.mDeleteDataDir(aNode)
                #change data folder ownership to root
                _ret = self.mChgFolderOwnShip(aNode,_remote_ahf_data_path,"root","root")
                if _ret == False:
                    ebLogError('*** AHF: change folder owner ship failed for host : %s  ' % (aNode.mGetHostname()))
                    return _ret
                ebLogInfo('Compare and pick higher AHF version between Exacloud and Dbaas')
                _remote_ahf_bin_path = self.mGetHigherAHFPath(aNode, _ahf_bin_path)
            elif _deviceType == "dom0":
                _ret = self.mChgFolderOwnShip(aNode,"/opt","root","root")
                if _ret == False:
                    ebLogError('*** AHF: change folder ownership for /opt failed for host : %s  ' % (aNode.mGetHostname()))
                    return _ret
            ebLogInfo('*** installing AHF Image on %s , device type %s in progress...' %(aNode.mGetHostname(),_deviceType))
            _cmdstr = '(' + _remote_ahf_bin_path + '/ahf_setup' + ' -silent -local -ahf_loc ' + _remote_ahf_install_path + ' -data_dir ' + _remote_ahf_data_path +  ' -tmp_loc /tmp' + ' -env_type ' + _env_type + ' )'
            ebLogInfo('*** AHF installation command:  %s ' %(_cmdstr))
            _, _e, _ = aNode.mExecuteCmd(_cmdstr)
            ebLogInfo('*** AHF installation log ***')
            for _line in _e.readlines():
                _line = _line.replace("\n", "")
                if _line:
                    ebLogInfo(f'{_line}')
            if aNode.mGetCmdExitStatus():
                ebLogHealth('WRN','*** AHF : Installation Failed. Installtion command output for host : %s' % (aNode.mGetHostname()))
                ebLogHealth('WRN','*** AHF : Install log: %s: ' % (_e.readlines()))
                #try with uninstall and install only for dom0
                _ret = False
                if _deviceType == "dom0":
                    if _fresh == True:
                        _ret = False
                    else:
                        ebLogInfo('*** Uninstall and install AHF for dom0 as upgrade fails, host: %s' % (aNode.mGetHostname()))
                        _ret = self.mAhfUninstall(aNode, _remote_ahf_install_path)
                        if _ret == False:
                            ebLogError('*** AHF Uninstall failed for host : %s  ' % (aNode.mGetHostname()))
                        else:
                            ebLogInfo('*** installing AHF Image on %s , device type %s in progress...' %(aNode.mGetHostname(),_deviceType))
                            _cmdstr = '(' + _remote_ahf_bin_path + '/ahf_setup' + ' -silent -local -ahf_loc ' + _remote_ahf_install_path + ' -data_dir ' + _remote_ahf_data_path +  ' -tmp_loc /tmp' + ' -env_type ' + _env_type + ' )'
                            ebLogInfo('*** installing AHF command to execute:  %s ' %(_cmdstr))
                            _, _e, _ = aNode.mExecuteCmd(_cmdstr)
                            if aNode.mGetCmdExitStatus():
                                ebLogHealth('WRN','*** AHF : Retry Installation Failed. Installtion command output for host : %s' % (aNode.mGetHostname()))
                                ebLogHealth('WRN','*** AHF : Retry Install log: %s: ' % (_e.readlines()))
                                _ret = False
                            else:
                                ebLogHealth('NFO','*** AHF : Retry Installation Success. Installtion command output for host : %s' % (aNode.mGetHostname()))
                                ebLogHealth('NFO','*** AHF : Retry Install log: %s: ' % (_e.readlines()))
                                _ret = True
            else:
                
                ebLogInfo(f'*** AHF installation succeeded on {aNode.mGetHostname()} , {_deviceType}')
                ebLogHealth('NFO','*** AHF : Installation Success. Installtion command output for host : %s' % (aNode.mGetHostname()))
                ebLogHealth('NFO','*** AHF : Install log: %s: ' % (_e.readlines()))
                _ret = True
            if _deviceType == "domU":
                if not self.mGetTFACTLStatus(_remote_ahf_install_path, aNode):
                    ebLogWarn(f'*** AHF : Issues with installation, please check again for {aNode.mGetHostname()}')
                _ret = self.mChgFolderOwnShip(aNode,_remote_ahf_data_path,"oracle","oinstall")
                if _ret == False:
                    ebLogError(f'*** AHF: change folder owner to oracle:oinstall failed for host : {aNode.mGetHostname()}')
                    return _ret
                # below TFA setting are only applicable for ATP Systems
                if _ebox.isATP():
                    _cmdstr = '(' + _remote_ahf_install_path + '/oracle.ahf/bin/tfactl set redact=SANITIZE' + ' )'
                    ebLogInfo('*** Setting TFA settings on DOMU %s'%(_cmdstr))
                    _, _e, _ = aNode.mExecuteCmd(_cmdstr)
                    if aNode.mGetCmdExitStatus():
                        ebLogInfo('*** Setting TFA settings on DOMU Failed ')
                        _ret = False
                    else:
                        _cmdstr = '(' + _remote_ahf_install_path + '/oracle.ahf/bin/tfactl set manageLogsAutoPurge=ON' + ' )'
                        ebLogInfo('*** Setting TFA settings on DOMU %s'%(_cmdstr))
                        _, _e, _ = aNode.mExecuteCmd(_cmdstr)
                        if aNode.mGetCmdExitStatus():
                            ebLogInfo('*** Setting TFA settings on DOMU Failed ')
                            _ret = False
                        else:
                            ebLogInfo('*** Setting TFA settings on DOMU Completed')
        except Exception as e:
            if _deviceType == "domU":
                self.mChgFolderOwnShip(aNode,_remote_ahf_data_path,"oracle","oinstall")
            _ret = False
            ebLogError('*** AHF install failed for host: %s with error %s' % (aNode.mGetHostname(),str(e)))
            raise Exception(e)
        self.mDeleteAhfImage(aNode)
        return _ret

    def mInstallAhfOnRemoteCps(self,aOptions=None):
        '''
        This method installs the AHF packageon remote cps (standby ECRA/exacloud) 
        @aOptions: Configurable Options passed. If the option is not available, AHF will be insalled on default path
        '''
        _hc    = self.mGetCluHealthCheck()
        _ebox = _hc.mGetEbox()
        try:
            if not _ebox.mGetOciExacc():
                return 
            _host_name = _ebox.mCheckConfigOption('remote_cps_host')
            if not _host_name:
                ebLogWarn('*** Remote CPS not configured, AHF installation on remote cps is skipped')
                return
            _ahf_bin_path = os.path.join(get_gcontext().mGetBasePath() , 'ahf_setup')
            _device_type = "standby_cps"
            _remote_ahf_bin_path = get_gcontext().mGetBasePath()
            _remote_ahf_install_path =  os.path.join(get_gcontext().mGetBasePath() , 'ahf_install')
            _remote_ahf_data_path =  os.path.join(get_gcontext().mGetBasePath() , 'ahf_install')
            with connect_to_host(_host_name,get_gcontext()) as _node:
                _ahf_installed = self.mSetupAhfonRemote(_node, _device_type, _ahf_bin_path, _remote_ahf_bin_path, _remote_ahf_install_path,_remote_ahf_data_path )
        except Exception as e:
            _err_str = '*** AHF install failed on remote cps with exception : %s' % (str(e))
            ebLogError(_err_str)
            raise Exception(e)
 
    def mInstallAhf(self,deviceType, aOptions=None,_selected_host = None):
        '''
        This method installs the AHF package in all the 
        @aOptions: Configurable Options passed. If the option is not available, AHF will be insalled on default path
        '''
        # TODO: Move the common paths to init 
        _hc    = self.mGetCluHealthCheck()
        _ebox = _hc.mGetEbox()

        _ahf_bin_path = get_gcontext().mGetBasePath() + 'ahf_setup'
        _remote_ahf_bin_path = _ebox.mCheckSubConfigOption('ahf_paths','remote_ahf_bin_path')
        _remote_ahf_install_path  = None
        if deviceType == "domU":
            #domU ahf data path 
            _remote_ahf_data_path = _ebox.mCheckSubConfigOption('ahf_paths','remote_ahf_data_path_domu')
            if _ebox.IsZdlraProv():
                _remote_ahf_data_path = _ebox.mCheckSubConfigOption('ahf_paths','remote_ahf_data_path_zdlra_domu')
        elif deviceType == "dom0":
            #dom0 data path 
            _remote_ahf_data_path = _ebox.mCheckSubConfigOption('ahf_paths','remote_ahf_data_path_dom0')
        else:
            ebLogError('*** AHF: Wrong device type given. It should be dom0 or domU')
            return
   
        #ahf remote install path - same for dom0 & domU   
        if aOptions is not None and aOptions.jsonconf is not None and 'ahf_install_path' in aOptions.jsonconf.keys():
            _remote_ahf_install_path = aOptions.jsonconf.get('ahf_install_path')
        elif _ebox.mCheckConfigOption('ahf_install_path'):
            _remote_ahf_install_path = _ebox.mCheckSubConfigOption('ahf_paths', 'remote_ahf_install_path')
        else:
            _remote_ahf_install_path  = '/opt'

        # Return error if absolute path is not given 
        if _remote_ahf_data_path.startswith('/') != True or _remote_ahf_install_path.startswith('/') != True:
            ebLogError('*** AHF: Absolute install path / data path not given for AHF installation')
            return
            
        _tmp_log_destination = ebLogSetHCLogDestination(_hc.mGetLogHandler(), True)
        ebLogDebug('*** AHF Install on %s : ahf local bin path : %s ' %(deviceType, _ahf_bin_path))
        ebLogDebug('*** AHF Install on %s : ahf remote bin path : %s ' %(deviceType, _remote_ahf_bin_path))
        ebLogDebug('*** AHF Install on %s : ahf remote install path : %s ' %(deviceType, _remote_ahf_install_path))
        ebLogDebug('*** AHF Install on %s : ahf remote data path : %s ' %(deviceType, _remote_ahf_data_path))

        _dom0s, _domUs, _cells, _switches = _ebox.mReturnAllClusterHosts()
        _hostList = []
        _install_result = {}
        if deviceType == "domU":
            _hostList += _domUs
        elif deviceType == "dom0":
            _hostList += _dom0s
        else:
            return
        
        def _mInstallAhf(aHost, aDeviceType, aAhf_bin_path, aRemote_ahf_bin_path, aRemote_ahf_install_path, aRemote_ahf_data_path):
            _host = aHost
            _node = exaBoxNode(get_gcontext())
            try:
                _node.mSetUser("root")
                _node.mConnectTimed(aHost=_host, aTimeout="10")
            except:
                ebLogInfo('WARNING: CheckInfo failed to connect to: %s ' % (_host))
                return

            try:
                if _ebox.mIsExaScale() and deviceType == "domU":
                    # install for domU only
                    ebLogInfo(f'AHF to be installed on Exascale Environment ')
                    _ahf_installed = self.mSetupAhfonExascale(_node,aDeviceType, aAhf_bin_path, aRemote_ahf_bin_path, aRemote_ahf_install_path, aRemote_ahf_data_path)
                else:
                    _ahf_installed = self.mSetupAhfonRemote(_node, aDeviceType, aAhf_bin_path, aRemote_ahf_bin_path, aRemote_ahf_install_path, aRemote_ahf_data_path)

            except Exception as e:
                raise Exception(e)

            if _ahf_installed == False:
                ebLogError('*** AHF installation failed for %s: %s ' % (deviceType, _host))
                _install_result[_host] = False
            else:
                ebLogInfo('*** AHF installation succeeded  for %s: %s ' % (deviceType, _host))
                _install_result[_host] = True

        # Parallelize AHF installation
        _lockRequired = True
        if deviceType == "domU":
            _lockRequired = False

        try:

            if _lockRequired:
                _ebox.mAcquireRemoteLock()

            _plist = ProcessManager()
            for _host in _hostList:
                if _selected_host and _host != _selected_host:
                    continue
                _p = ProcessStructure(_mInstallAhf, [_host, deviceType, _ahf_bin_path, _remote_ahf_bin_path, _remote_ahf_install_path, _remote_ahf_data_path])
                _p.mSetMaxExecutionTime(30*60) # 30 minutes
                _p.mSetJoinTimeout(5)
                _p.mSetLogTimeoutFx(ebLogWarn)
                _plist.mStartAppend(_p)
            _plist.mJoinProcess()

        finally:
            if _lockRequired:
                _ebox.mReleaseRemoteLock()

        ebLogRemoveHCLogDestination(_tmp_log_destination)
        ebLogSetHCLogDestination(_hc.mGetDefaultLogHandler())
        return _install_result
    
    def mSetupAhfonExascale(self,aNode, _deviceType, _ahf_bin_path, _remote_ahf_bin_path, _remote_ahf_install_path, _remote_ahf_data_path):
        """ Install AHF on EXASCALE enviornment 

        Args:
            aNode (object): domU node connection instance
            _deviceType (string): domU
            _ahf_bin_path (string): path where ahf_setup is present
            _remote_ahf_bin_path (string): path to copy ahf_setup in domU
            _remote_ahf_install_path (string): installation path in domU
            _remote_ahf_data_path (string): data directory path in domU

        Returns:
            bool: True if installation successful else False
        """
        try:
            _hc    = self.mGetCluHealthCheck()
            _ebox = _hc.mGetEbox()
            _ret = False
            _ret = self.mChgFolderOwnShip(aNode, _remote_ahf_data_path, "root", "root")
            if _ret == False:
                ebLogError('*** AHF cannot be installed for host due to permission issue : %s  ' % (aNode.mGetHostname()))
                return _ret
            _ret = self.mCopyAhfImage(aNode,_ahf_bin_path,_remote_ahf_bin_path)
            if _ret == False:
                ebLogError('*** AHF image copy failed for host : %s  ' % (aNode.mGetHostname()))
                return _ret
            
            ebLogInfo(f'*** installing AHF Image on Exascale host {aNode.mGetHostname()} , device type domU in progress...')
            _cmdstr = '(' + _remote_ahf_bin_path + '/ahf_setup' + ' -silent -local -ahf_loc ' + _remote_ahf_install_path + ' -data_dir ' + _remote_ahf_data_path +  ' -tmp_loc /tmp' + ' )'
            ebLogInfo('*** AHF installation command:  %s ' %(_cmdstr))
            _, _e, _ = aNode.mExecuteCmd(_cmdstr)
            ebLogInfo('*** AHF installation log ***')
            for _line in _e.readlines():
                _line = _line.replace("\n", "")
                if _line:
                    ebLogInfo(f'{_line}')
            if aNode.mGetCmdExitStatus():
                ebLogHealth('WRN','*** AHF : Installation Failed. Installtion command output for host : %s' % (aNode.mGetHostname()))
                ebLogHealth('WRN','*** AHF : Install log: %s: ' % (_e.readlines()))
                #try with uninstall and install only for dom0
                _ret = False
            
            if not self.mGetTFACTLStatus(_remote_ahf_install_path, aNode):
                ebLogWarn(f'*** AHF : Issues with installation, please check again for {aNode.mGetHostname()}')
            _ret = self.mChgFolderOwnShip(aNode,_remote_ahf_data_path,"oracle","oinstall")
            if _ret == False:
                ebLogError(f'*** AHF: change folder owner to oracle:oinstall failed for host : {aNode.mGetHostname()}')
                return _ret
            # below TFA setting are only applicable for ATP Systems
            if _ebox.isATP():
                _cmdstr = '(' + _remote_ahf_install_path + '/oracle.ahf/bin/tfactl set redact=SANITIZE' + ' )'
                ebLogInfo('*** Setting TFA settings on DOMU %s'%(_cmdstr))
                _, _e, _ = aNode.mExecuteCmd(_cmdstr)
                if aNode.mGetCmdExitStatus():
                    ebLogInfo('*** Setting TFA settings on DOMU Failed ')
                    _ret = False
                else:
                    _cmdstr = '(' + _remote_ahf_install_path + '/oracle.ahf/bin/tfactl set manageLogsAutoPurge=ON' + ' )'
                    ebLogInfo('*** Setting TFA settings on DOMU %s'%(_cmdstr))
                    _, _e, _ = aNode.mExecuteCmd(_cmdstr)
                    if aNode.mGetCmdExitStatus():
                        ebLogInfo('*** Setting TFA settings on DOMU Failed ')
                        _ret = False
                    else:
                        ebLogInfo('*** Setting TFA settings on DOMU Completed')
        except Exception as e:
            self.mChgFolderOwnShip(aNode,_remote_ahf_data_path,"oracle","oinstall")
            _ret = False
            ebLogError('*** AHF install failed for host: %s with error %s' % (aNode.mGetHostname(),str(e)))
            raise Exception(e)
        self.mDeleteAhfImage(aNode)
        return _ret
