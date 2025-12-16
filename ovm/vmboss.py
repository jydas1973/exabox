"""
$Header: ecs/exacloud/exabox/ovm/vmboss.py /main/2 2021/08/24 13:48:37 gsundara Exp $

 Copyright (c) 2021, Oracle and/or its affiliates. 

NAME:
    vmboss.py - vmbackup to oss - Basic Vmbackup to Objectstore functionality

FUNCTION:
    Provide Backup, restore, list & delete API for managing VMBackup to Objectstore

NOTES:


History:

    MODIFIED   (MM/DD/YY)
    gsundara    08/19/21 - fix bug 33245647
    gsundara    06/12/21 - Creation (ER 32994768)
"""
from six.moves import urllib

urlopen = urllib.request.urlopen
URLError = urllib.error.URLError
HTTPError = urllib.error.HTTPError

import os, datetime, subprocess, sys
from exabox.core.Node import exaBoxNode
from exabox.kms.vmbkms import ebKmsVmbObjectStore
from exabox.core.Context import get_gcontext
from exabox.log.LogMgr import ebLogInfo, ebLogWarn, ebLogError
from exabox.core.Core import ebExit


class ebCluVmbackupObjectStore(object):

    # Constants defined for this class

    # vmbackup configuration file stored in dom0s

    def __init__(self, aExaBoxCluCtrl, aConfig):

        self.__config = get_gcontext().mGetConfigOptions()
        self.__ebox = aExaBoxCluCtrl
        self.__ociexacc = self.__ebox.mCheckConfigOption('ociexacc', 'True')
        self.__exabm = self.__ebox.mCheckConfigOption('exabm', 'True')
        self.__vmname = None
        self.__exastage = get_gcontext().mGetBasePath() + '/vmbstage/'
        self.__exastage_res = get_gcontext().mGetBasePath() + '/vmbstage/restore/'
        self.__backup = '/EXAVMIMAGES/Backup/Local/'
        self.__vmpath = '/EXAVMIMAGES/GuestImages/'
        self.__seqnum = 0
        self.__maxbackups = 3  # get from exabox.conf
        self.mSetVmbKms(ebKmsVmbObjectStore(self.__ebox, self.__config))
        if self.__ebox.mCheckConfigOption('max_oss_vmbackups') is not None:
            self.__maxbackups = int(self.__ebox.mCheckConfigOption('max_oss_vmbackups'))
        self.__skip_img = self.__ebox.mCheckConfigOption('vmbackup2oss_skip_image', 'True')

    def mGetVm(self):
        return self.__vmname

    def mSetVm(self, aVmname):
        self.__vmname = aVmname

    def mGetVmbKms(self):
        return self.__vmbkms

    def mSetVmbKms(self, aVmbKms):
        self.__vmbkms = aVmbKms

    def mGetEbox(self):
        return self.__ebox

    def mGetBkupPath(self):
        return self.__backup

    def mSetBkupPath(self, aDom0):
        self.__backup = self.__backup + aDom0

    def mGetVmPath(self):
        return self.__vmpath

    def mSetVmPath(self, aDomU):
        self.__vmpath = '/EXAVMIMAGES/GuestImages/' + aDomU

    def mGetSeqNum(self):
        return self.__seqnum

    def mSetSeqNum(self, aSeq):
        self.__seqnum = aSeq


    def mGetDomainName(self):
        _eBox = self.mGetEbox()
        _machines = _eBox.mGetMachines()
        _networks = _eBox.mGetNetworks()
        _dom0_list = [_dom0 for _dom0, _ in _eBox.mReturnDom0DomUPair()]
        if self.__exabm or self.__ociexacc:
            _dom0_list = [_dom0 for _dom0, _ in _eBox.mReturnDom0DomUNATPair()]
        _dom0_mac = _machines.mGetMachineConfig(_dom0_list[0])
        _dom0_net_list = _dom0_mac.mGetMacNetworks()
        return '.' + _networks.mGetNetworkConfig(_dom0_net_list[0]).mGetNetNatDomainName()


    def mCheckCount(self):
        # if self.__vmbcount file exists, count the number of lines & it >4 return False , else True
        pass


    # Common for Backup & Restore operations
    def mPrecheckValidVM(self, aOptions, aOperation):
        _dom0 = None
        _domU = None
        _domain_name = None
        _eBox = self.mGetEbox()
        _jconf = aOptions.jsonconf
        if _jconf and 'vmname' in _jconf.keys():
            self.mSetVm(_jconf['vmname'])

        _vmname = self.mGetVm().split('.')[0]

        if _vmname is None:
            ebLogError('no vmname provided')
            ebExit(-1)

        _dpairs = _eBox.mReturnDom0DomUPair()
        if self.__exabm or self.__ociexacc:
            _dpairs = _eBox.mReturnDom0DomUNATPair(True)

        for _d0, _dU in _dpairs:
            if _vmname in _dU:
                _dom0 = _d0
                _domU = _dU
                _domain_name = '.'.join(_domU.split('.')[1:])
                if not (_domain_name):
                    _domain_name = '.'.join(_dom0.split('.')[1:])
                    if not (_domain_name):
                        ebLogError('cannot determine nat domain name')
                        ebExit(-1)
                _domain_name = '.' + _domain_name
                break

        if _dom0 is None:
            ebLogError('{} not part of this rack'.format(_vmname))
            ebExit(-1)

        try:
            os.stat(self.__exastage)
        except:
            os.mkdir(self.__exastage)

        if _domain_name not in _d0:
            _dom0 = _d0 + _domain_name
        if _domain_name not in _dU:
            _domU = _dU + _domain_name

        return _dom0, _domU

    def mExecute(self, aOptions, aCmd=None):
        _jconf = aOptions.jsonconf
        if _jconf and 'operation' in _jconf.keys():
            if _jconf['operation'] == 'backup':
                self.mBackup(aOptions)
            elif _jconf['operation'] == 'restore':
                self.mRestore(aOptions)
            elif _jconf['operation'] == 'list':
                # self.mList(aOptions)
                pass
            elif _jconf['operation'] == 'delete':
                self.mDelete(aOptions, aCmd)
            else:
                ebLogWarn('*** Invalid operation specified for vmbackup to objectstore')
        else:
            self.mList(aOptions)


    def mBackup(self, aOptions):
        ebLogInfo("{}: backup to objectstore".format(datetime.datetime.now()))
        _eBox = self.mGetEbox()
        _dom0, _domU = self.mPrecheckValidVM(aOptions, 'backup')
        ebLogInfo('dom0 fqdn : {0}, domU NAT name : {1}'.format(_dom0, _domU))

        self.mSetBkupPath(_dom0)
        self.mSetVmPath(_domU)
        if self.__exabm or self.__ociexacc:
            _dpairs = _eBox.mReturnDom0DomUPair()
            for _d0, _dU in _dpairs:
                if _d0 == _dom0:
                    self.mSetVmPath(_dU)
                    ebLogInfo('domU client nat fqdn : {}'.format(_domU))
        ebLogInfo(self.mGetBkupPath())
        ebLogInfo(self.mGetVmPath())

        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_dom0)

        if _node.mFileExists(self.mGetBkupPath()):
            _cmd = '/bin/ls -d {}/*/'.format(self.mGetBkupPath())
            _, _o, _ = _node.mExecuteCmd(_cmd)
            _o = _o.readlines()
            _dirs = []
            for _d in _o:
                _bsj = str(_d.strip('\n')) + '.backup_summary.json'
                if _node.mFileExists(_bsj):
                    _dirs.append(str(_d.strip('\n')))
            _dirs.sort()

            if not _dirs:
                ebLogInfo('*** No Complete Local Backup is present (missing .backup_summary.json)')
                return

            # Find the last backup, which is the sequence num
            self.mSetSeqNum(int(os.path.basename(_dirs[-1].rstrip('/'))))
            _oss_obj = _domU + '.' + str(self.mGetSeqNum())

            # Check if this backup seq number is already in ObjectStore
            _rc, _resp = self.mGetVmbKms().mGetObject(_oss_obj + '.details')
            if not _rc:
                ebLogInfo('*** Latest Backup Sequence number {} is already present in objectstore'.format(
                    str(self.mGetSeqNum())))
                return

            _cmd = '/bin/ls {}'.format(_dirs[-1])
            _, _o, _ = _node.mExecuteCmd(_cmd)
            _o = _o.readlines()

            # There will be only one dir under _seq, named by timestamp
            if not _o:
                ebLogError('*** no backups found under {}'.format(_dirs[-1]))
                ebExit(-1)

            _subdir = _o[0].strip('\n')
            _vmpath = _dirs[-1] + _subdir + self.mGetVmPath()

            if not _node.mFileExists(_vmpath):
                ebLogError('*** Backup dirpath {} not found'.format(_vmpath))
                ebExit(-1)

            _cmd = "/bin/ls {0} | /bin/grep -v ^db".format(_vmpath)
            if self.__skip_img:
                _cmd = _cmd + '| /bin/grep -v \.img$'
            _, _o, _ = _node.mExecuteCmd(_cmd)
            _o = _o.readlines()
            _diskspath = []
            for _d in _o:
                _diskspath.append(str(_d.strip('\n')))

            _filestr = ''
            for _f in _diskspath:
                _filestr += os.path.basename(_f) + ' '

            _src = _vmpath + '.tgz'
            _dst = self.__exastage + '/' + _domU + '.tgz'
            _enc = _dst + '.enc'
            try:
                _cmd = '/bin/tar cvzf {0} -C {1} {2} &> /dev/null'.format(_src, _vmpath, _filestr)
                ebLogInfo('compressed tar backup command: ' + _cmd)
                _node.mExecuteCmd("/bin/sh -c \'" + _cmd + "\'")
                _cmd_toprint = "echo \"compressed tar backup size on {0} is `du -hc {1}`\"".format(_dom0, _src)
                _node.mExecuteCmdLog(_cmd_toprint)
                ebLogInfo('{}: compressed tar backup command completed'.format(datetime.datetime.now()))
                _node.mCopy2Local(_src, _dst)
                ebLogInfo('copied tar backup to ecra host')
            except Exception as e:
                ebLogError('*** Error while copying compressed tar file {}'.format(_src))
                raise

            _, _o, _ = _node.mExecuteCmd('/usr/bin/md5sum ' + _src)
            _remote_hash = _o.readlines()[0].strip().split(' ')[0]
            ebLogInfo('Remote hash :' + str(_remote_hash))

            _o = subprocess.check_output(['/usr/bin/md5sum', _dst]).decode()
            _local_hash = _o.strip().split(' ')[0]
            ebLogInfo('Local hash :' + str(_local_hash))

            _node.mExecuteCmd('/bin/rm  ' + _src)

            if _remote_hash != _local_hash:
                ebLogError('*** Failed to copy {0} from {1}'.format(_src, _dom0))
            else:
                ebLogInfo('*** {0}: Copied {1} from {2} to {3}'.format(datetime.datetime.now(), _src, _dom0, _dst))
                try:
                    self.mGetVmbKms().mPutKms(_oss_obj, _dst, _local_hash)
                except Exception as e:
                    subprocess.check_output(['/bin/rm', '-f', _enc], stderr=subprocess.STDOUT)
                    subprocess.check_output(['/bin/rm', '-f', _dst], stderr=subprocess.STDOUT)
                    ebLogError('*** Error while encrypting compressed tar file {}'.format(_src))
                    raise
                ebLogInfo('{}: Backup Uploaded to OSS'.format(datetime.datetime.now()))
                subprocess.check_output(['/bin/rm', '-f', _enc], stderr=subprocess.STDOUT)

            subprocess.check_output(['/bin/rm', '-f', _dst], stderr=subprocess.STDOUT)

            # Retain only last N backups in objectstore
            _lastN_oss_obj = _domU + '.' + str(self.mGetSeqNum() - self.__maxbackups)
            _rc, _resp = self.mGetVmbKms().mGetObject(_lastN_oss_obj + '.details')
            if not _rc:
                ebLogInfo('*** Deleting {0} backup to retain only the last {1} backups'.format(_lastN_oss_obj,
                                                                                               self.__maxbackups))
                self.mGetVmbKms().mDeleteObject(_lastN_oss_obj)
                self.mGetVmbKms().mDeleteObject(_lastN_oss_obj + '.details')
        else:
            ebLogInfo('{} does not exist and no backup-to-oss operation will be performed.'.format(self.mGetBkupPath()))

        _node.mDisconnect()
        return


    def mRestore(self, aOptions):
        ebLogInfo("{}: Restore from objectstore".format(datetime.datetime.now()))
        _eBox = self.mGetEbox()
        _dom0, _domU = self.mPrecheckValidVM(aOptions, 'restore')

        ebLogInfo('dom0 fqdn : {0}, domU NAT name : {1}'.format(_dom0, _domU))

        self.mSetVmPath(_domU)
        if self.__exabm or self.__ociexacc:
            _dpairs = _eBox.mReturnDom0DomUPair()
            for _d0, _dU in _dpairs:
                if _d0 == _dom0:
                    self.mSetVmPath(_dU)
                    ebLogInfo('domU client fqdn : {}'.format(_dU))
        ebLogInfo(self.mGetVmPath())

        _src = self.__exastage_res + '/' + _domU + '.tgz'

        _vmpath = self.mGetVmPath()
        _vmlist = self.mList(aOptions)

        if not _vmlist:
            ebLogInfo('*** Backup for {} is not available in Objectstore'.format(_domU))
            ebExit(0)

        _vmver = _vmlist.pop()
        _vmname = _vmver.rsplit('.', 1)[0]

        if _domU != _vmname:
            ebLogError('*** Backup for {} is not available in Objectstore'.format(_domU))
            ebExit(0)
        else:
            if not os.path.exists(self.__exastage_res):
                os.makedirs(self.__exastage_res)
            _local_hash = ''
            try:
                _local_hash = self.mGetVmbKms().mGetKms(_vmver, _src)
                ebLogInfo('{}: Downloaded and decrypted the backup'.format(datetime.datetime.now()))
            except Exception as e:
                subprocess.check_output(['rm', '-f', _src], stderr=subprocess.STDOUT)
                ebLogError('*** Error while decrypting compressed tar file {}'.format(_src))
                raise

            _dst = _vmpath + '.tgz'

            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_dom0)
            _node.mCopyFile(_src, _dst)

            _, _o, _ = _node.mExecuteCmd('/usr/bin/md5sum ' + _dst)
            _remote_hash = _o.readlines()[0].strip().split(' ')[0]

            if _remote_hash != _local_hash:
                ebLogError('*** Failed to copy {0} to {1}'.format(_src, _dom0))
            else:
                ebLogInfo('***{0}: Copied the backup to {1}'.format(datetime.datetime.now(), _dom0))
                try:
                    _cmd = '/bin/mkdir -p {0}; /bin/tar xvzf {1} -C {2} &> /dev/null'.format(_vmpath, _dst, _vmpath)
                    ebLogInfo('uncompress tar backup command: ' + _cmd)
                    _node.mExecuteCmd("/bin/sh -c \'" + _cmd + "\'")
                except Exception as e:
                    ebLogError('*** Error while uncompressing/unarchiving  file {}'.format(_dst))
                    raise

                _node.mExecuteCmd('/bin/chmod 740 {0}'.format(_vmpath))

                ebLogInfo('***{0}: Restore of backup of {1} is complete'.format(datetime.datetime.now(), _domU))
                ebLogInfo('\n*** NEXT Fetch the necessary db img files & copy to {0} and start vm {1}\n'.format(_vmpath,
                                                                                                                _domU))

            subprocess.check_output(['/bin/rm', '-f', _src], stderr=subprocess.STDOUT)
            _node.mExecuteCmd('/bin/rm  ' + _dst)
            _node.mDisconnect()


    def mList(self, aOptions):
        ebLogInfo("Fetch list of all versions of vmbackups for this cluster xml from objectstore")
        _eBox = self.mGetEbox()
        _rc, _resp = self.mGetVmbKms().mListObjects()
        _vmlist = []
        if not _rc:
            for _d in _resp:
                if 'details' not in _d['name']:
                    _dpairs = _eBox.mReturnDom0DomUPair()
                    if self.__exabm or self.__ociexacc:
                        _dpairs = _eBox.mReturnDom0DomUNATPair(True)
                    for _d0, _dU in _dpairs:
                        if _dU in _d['name']:
                            _vmlist.append(_d['name'])
        # ebLogInfo(_vmlist)
        # List the ones with the .details file present. Otherwise the backup cannot be used due to missing DEK
        _updated_vmlist = []
        for _vmver in _vmlist:
            _rc, _resp = self.mGetVmbKms().mGetObject(_vmver + '.details')
            if not _rc:
                _updated_vmlist.append(_vmver)
        ebLogInfo(_updated_vmlist)
        return (sorted(_updated_vmlist))


    # TODO: To be called during delete service too
    def mDelete(self, aOptions, aCmd=None):
        def _delete(_domU):
            for _vmver in self.mList(aOptions):
                _vmname = _vmver.rsplit('.', 1)[0]
                if _vmname == _domU:
                    ebLogInfo('Deleting ' + _vmver)
                    ebLogInfo('Deleting ' + _vmver + '.details')
                    self.mGetVmbKms().mDeleteObject(_vmver)
                    self.mGetVmbKms().mDeleteObject(_vmver + '.details')

        _eBox = self.mGetEbox()
        if aCmd is not None:
            _dom0, _domU = self.mPrecheckValidVM(aOptions, 'delete')
            ebLogInfo("Delete all versions of {} vmbackups from objectstore".format(_domU))
            _delete(_domU)
        else:
            # being called as a part of delete service
            ebLogInfo('Delete all versions of all vms in this cluster from objectstore as a part of Delete Service')
            _dpairs = _eBox.mReturnDom0DomUPair()
            if self.__exabm or self.__ociexacc:
                _dpairs = _eBox.mReturnDom0DomUNATPair(True)
            for _dom0, _domU in _dpairs:
                _delete(_domU)
