"""
 Copyright (c) 2020, Oracle and/or its affiliates. 

NAME:
    cluexaccroce.py - Exacloud RoCE logic, specific to ExaCC OCI

FUNCTION:
    Setup CPS RoCE interface.

NOTE:
    Initial implementation set the interfaces in active passive mode

History:

    MODIFIED   (MM/DD/YY)
       rajsag   12/01/20 - create service prevmsetup error in script
                           ociexacc-cps-setupib.sh
       oerincon 04/07/20 - 31124650: Validate QinQ proper setup for RoCE enabled
                           environments during Create Service
       oerincon 03/11/20 - Creation
"""

import json
import os
import socket
import subprocess

import ipaddress

from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogInfo, ebLogError, ebLogDebug
from exabox.ovm.AtpUtils import ebAtpUtils
# Shell secure quoting is implemented in a different module in p2 and p3
from six.moves import shlex_quote

# Main Class
class ExaCCRoCE_CPS(object):

    def __init__(self, aDebug=False, aMode=False):
        self.__aMode = aMode
        self.__debug = aDebug
        # Use ATPUtils method to read configuration, need to have a common UTIL class without ATP in name
        self.__remote_cps = ebAtpUtils.mCheckExaboxConfigOption('remote_cps_host')
        _ocps_jsonpath = ebAtpUtils.mCheckExaboxConfigOption('ocps_jsonpath')
        if not _ocps_jsonpath or not os.path.exists(_ocps_jsonpath):
            _msg = 'OCI-ExaCC requires ocps_jsonpath setting in exabox configuration for RoCE Setup'
            raise ExacloudRuntimeError(0x0120, 0xA, _msg)
        with open(_ocps_jsonpath, 'r') as fd:
            self.__ocps_json = json.load(fd)

    def mSetupCPSRoCE(self):
        # FIXME: Will this still be named after infiniband?
        _roce_net = ipaddress.ip_network(self.__ocps_json['ibNetworkCidr'])
        _netmask = shlex_quote(str(_roce_net.netmask))
        _localhostname = socket.gethostname().split('.')[0]
        _localIP = None
        _remoteIP = None

        for cps in self.__ocps_json['servers']:
            if _localhostname == cps['hostname']:
                # FIXME: Will this still be named after infiniband?
                _localIP = shlex_quote(cps['ibAdmin'][0])
            else:
                # FIXME: Will this still be named after infiniband?
                _remoteIP = shlex_quote(cps['ibAdmin'][0])
        # if _localIP not found, fallback on first of list
        if not _localIP:
            # FIXME: Will this still be named after infiniband?
            _localIP = shlex_quote(self.__ocps_json['servers'][0]['ibAdmin'][0])

        ebLogInfo('*** Setting up CPS infiniband with localIP:{} netmask:{} otherCPSIP:{}'
                  .format(_localIP, _netmask, _remoteIP))

        _path = os.path.abspath('scripts/network/ociexacc-cps-setup-roce.sh')
        # Test mode
        if not self.__aMode:
            return _localIP, _netmask, _remoteIP, _path

        try:
            # No need to log, output is kept in exception if error
            subprocess.check_output(['sudo', '/bin/sh', _path, _localIP, _netmask],
                                    stderr=subprocess.STDOUT)
            if self.__remote_cps and _remoteIP:
                _remote_cps = exaBoxNode(get_gcontext())
                _remote_cps.mSetUser('ecra')
                _remote_cps.mConnect(aHost=self.__remote_cps)
                _remote_cmd = 'sudo {} {} {}'.format(_path, _remoteIP, _netmask)
                _remote_cps.mExecuteCmdLog(_remote_cmd)
                _rc = _remote_cps.mGetCmdExitStatus()
                _remote_cps.mDisconnect()
                if int(_rc) != 0:
                    raise subprocess.CalledProcessError(cmd=_remote_cmd, returncode=int(_rc), output=_remote_cmd)
 
        except subprocess.CalledProcessError as e:
            ebLogError('***ERROR RoCE setup script return code({}) with output {}'
                       .format(e.returncode, e.output))
            raise ExacloudRuntimeError(0x0120, 0xA, 'Error while executing {}'.format(_path))

    def mVerifyCPSRoCEQinQSetup (self, cells_roce_ips):
        ebLogInfo('*** Verifying CPS RoCE QinQ setup.')

        # Test mode
        if not self.__aMode:
            return [cells_roce_ips]

        _path = os.path.abspath('scripts/network/ociexacc-cps-validate-qinq-roce.sh')
        _validate_cmd = '/bin/sh {} {}'.format(_path, ' '.join(cells_roce_ips))

        # Execute validation script in all CPS in a row, so if something goes wrong, Field Engineer can take a look at
        # all possible failures at once.
        _failed_cps = []

        _localhostname = socket.gethostname().split('.')[0]
        ebLogInfo('Verifying CPS RoCE QinQ setup at host {}'.format(_localhostname))

        # Perform local execution of the validation script
        _local_cps = exaBoxNode(get_gcontext(), True)
        _local_cps.mConnect()

        # In order to capture command exit status, we need to use mExecuteCmd instead mExecuteCmdLog
        # Also, mExecuteCmd does not log the script output/error so we need to print it ourselves
        fin, fout, ferr = _local_cps.mExecuteCmd(_validate_cmd)
        out = fout.readlines()
        if out:
            for e in out:
                ebLogInfo(e[:-1])
        err = ferr.readlines()
        if err:
            for e in err:
                ebLogError(e[:-1].encode('utf-8'))
        _rc = _local_cps.mGetCmdExitStatus()
        _local_cps.mDisconnect()
        if _rc:
            _failed_cps.append(_localhostname)
            if self.__debug:
                ebLogDebug('***RoCE QinQ validation script {} returned an error on CPS host {}. '
                           'Check logs for further details.'.format(_path, _localhostname))

        # Perform remote (other CPS) execution of the validation script
        if self.__remote_cps:
            ebLogInfo('Verifying CPS RoCE QinQ setup at host {}'.format(self.__remote_cps))
            _remote_cps = exaBoxNode(get_gcontext())
            _remote_cps.mSetUser('ecra')
            _remote_cps.mConnect(aHost=self.__remote_cps)
            _remote_cps.mExecuteCmdLog(_validate_cmd)
            _rc = _remote_cps.mGetCmdExitStatus()
            _remote_cps.mDisconnect()
            if _rc:
                _failed_cps.append(self.__remote_cps)
                if self.__debug:
                    ebLogDebug('***RoCE QinQ validation script {} returned an error on CPS host {}. '
                               'Check logs for further details.'.format(_path, self.__remote_cps))

        # In case our list of failed CPS is not empty, something went wrong, throw a runtime exception
        if _failed_cps:
            raise ExacloudRuntimeError(0x0120, 0xA, 'RoCE QinQ is incorrectly configured at hosts {}'.
                                       format(', '.join(_failed_cps)))
