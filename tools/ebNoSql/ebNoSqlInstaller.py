"""
$Header:

 Copyright (c) 2019, Oracle and/or its affiliates. All rights reserved.

NAME:
    ebNoSqlInstaller - installer for nosql

FUNCTION:
    Provide basic API for install Oracle nosql

NOTE:
    None

History:

    MODIFIED   (MM/DD/YY)
    agarrido    06/24/19 - Create file
"""
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogDebug, ebLogVerbose


class ebNoSqlInstaller(object):

    # Constants defined for this class
    # TODO: Change this call to dbaasapi installnosql
    NOSQL_INSTALLER = "/var/opt/oracle/nosql/dbaas_nosql_installer.pl"

    def __init__(self, aDomUs, aRackSize):
        self.__domUs     = aDomUs
        self.__rackSize  = aRackSize

    # mGetParticipantNodes:
    # This method chooses within the rack configuration in which nodes the
    # nosql service will be installed
    # quarter: all
    # half & full: 1st, 2nd and last one
    def mGetParticipantNodes(self):
        _domUlist = self.__domUs
        if len(_domUlist) < 4:
            return _domUlist
        else:
            return list(_domUlist[0], _domUlist[1], _domUlist[-1])

    # mInstallNoSql:
    # Install NoSql on participant nodes
    def mInstallNoSql(self, aDomUs):
        ebLogInfo("*** Installing Oracle NoSQL")
        for _domu in aDomUs:
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_domu)
            if not self.mCheckNoSqlInstalled(_node):
                _, _o, _e = _node.mExecuteCmd("perl {0}".format(
                    self.NOSQL_INSTALLER))
                if _node.mGetCmdExitStatus() == 0:
                    ebLogInfo('{0} '.format(str(_o.read())))
                    if self.mCheckNoSqlInstalled(_node):
                        ebLogInfo('Oracle NoSQL installed on: {0} '.format(_domu))
                    else:
                        _err = '' if _e is None else str(_e.read())
                        _error_str = '*** NoSQL install fail: {0}'.format(_err)
                        ebLogError(_error_str)
                else:
                    _error_str = '*** NoSQL install fail: {0}'.format(
                        str(_e.read()))
                    ebLogError(_error_str)
            _node.mDisconnect()

    # mCheckNoSqlInstalled:
    # Install NoSql on participant nodes
    def mCheckNoSqlInstalled(self, aNode, aVerbose=False):
        if aVerbose:
            _cmd_str = '/usr/bin/systemctl status ons.service'
            _, _o, _e = aNode.mExecuteCmd(_cmd_str)
            ebLogInfo('*** Service {0}'.format(str(_o.read())))
        else:
            _cmd_str = '/usr/bin/systemctl is-active --quiet ons.service'
            aNode.mExecuteCmd(_cmd_str)
        if aNode.mGetCmdExitStatus() == 0:
            return True
        return False

    # mRunInstall:
    # Run the insaller and check the service after
    def mRunInstall(self):

        _domUs = self.mGetParticipantNodes()
        self.mInstallNoSql(_domUs)
        for _domu in _domUs:
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_domu)
            if self.mCheckNoSqlInstalled(_node):
                ebLogInfo('*** NoSql service running on {0}'.format(_domu))
            else:
                _, _o, _e = _node.mExecuteCmd("/usr/bin/systemctl status ons.service")
                ebLogError('*** NoSql service not running:{0}'.format(str(_o.read().strip())))
