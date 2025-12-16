"""
 Copyright (c) 2014, 2022, Oracle and/or its affiliates. 

NAME:
    BaseServer - Basic functionality

FUNCTION:
    Create HTTPServer

NOTE:
    None    

History:
    ndesanto    11/05/2019 - ENH 30480538: HTTPS and Certificate Rotation
    ndesanto    09/19/2019 - 30294648 - IMPLEMENT PYTHON 3 MIGRATION WHITELIST ON EXATEST
    jesandov    26/03/2019 - File Creation
"""



import argparse
import socket
import time
import sys
import os

from exabox.BaseServer.BaseHandler import BaseHandler
from exabox.BaseServer.BaseLogMgnt import BaseLogMgnt
from exabox.BaseServer.BaseConfig  import BaseConfig
from exabox.network.ExaHTTPSServer import ExaHTTPSServer

class BaseServer(ExaHTTPSServer):

    def __init__(self, aConfig, *args):

        self.__config = aConfig
        self.__log    = BaseLogMgnt(self.__config)

        self.__sharedData = {"log": self.__log, "config": self.__config}

        super().__init__(*args)

    def mGetSharedData(self):
        return self.__sharedData

    def mGetLog(self):
        return self.__log

    def mGetConfig(self):
        return self.__config


class BaseServerAdministrator(object):

    def __init__(self, aServerName, aServerClass=None, aHandlerClass=None):

        self.__serverClass =  aServerClass
        if aServerClass is None:
            self.__serverClass = BaseServer

        self.__handlerClass =  aHandlerClass
        if aHandlerClass is None:
            self.__handlerClass = BaseHandler

        self.__config   = BaseConfig(aServerName)
        self.__listenAddress = self.__config.mGetConfigValue("listen")
        self.__port     = int(self.__config.mGetConfigValue("port"))

    def mGetHttpServer(self):
        return self.__httpd

    def mGetConfig(self):
        return self.__config

    def mDaemonize(self):

        try:
            pid = os.fork()
        except OSError as e:
            raise Exception("%s [%d]" % (e.strerror, e.errno))

        if (pid == 0):
            os.setsid()

            try:
                pid = os.fork()
            except OSError as e:
                raise Exception("%s [%d]" % (e.strerror, e.errno))

            if pid:
                os._exit(0)

        else:
            os._exit(0)

    def mRedirectDescriptors(self):

        if not os.path.exists(self.__config.mGetPath() + "/log"):
            os.makedirs(self.__config.mGetPath() + "/log")

        _rin_file = '/dev/null'
        _rout_file = self.__config.mGetPath() + '/log/daemon.out'
        _rerr_file = self.__config.mGetPath() + '/log/daemon.err'

        sys.stdout.flush()
        sys.stderr.flush()

        _sin  = open(_rin_file,'r')
        _sout = open(_rout_file, 'a+')
        _serr = open(_rerr_file, 'a+')

        os.dup2(_sin.fileno(),  sys.stdin.fileno())
        os.dup2(_sout.fileno(), sys.stdout.fileno())
        os.dup2(_serr.fileno(), sys.stderr.fileno())

    def mConnect(self):

        self.__httpd = self.__serverClass(self.__config, (self.__listenAddress, self.__port), self.__handlerClass)

        self.__httpd.mGetLog().mInit()

        self.__httpd.mGetLog().mInfo("Server Started - {0}:{1}".format(self.__listenAddress, self.__port))

        try:
            self.__httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        except Exception as e:
            self.__httpd.mGetLog().mError(e)

    def mDisconnect(self):

        self.__httpd.shutdown()
        self.__httpd.server_close()
        self.__httpd.mGetLog().mInfo("Server Stopped - {0}:{1}".format(self.__listenAddress, self.__port))
        self.__httpd.mGetLog().mClose()

