#
# $Header: ecs/exacloud/exabox/proxy/ecinstance.py /main/2 2020/10/20 09:14:47 dekuckre Exp $
#
# ecinstance.py
#
# Copyright (c) 2020, Oracle and/or its affiliates. 
#
#    NAME
#      ecinstance.py - Exacloud Instance
#
#    DESCRIPTION
#      Exacloud instance to be used to register/deregister with router.
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    dekuckre    10/07/20 - Creation
#


ALIVE='Alive'
SUSPECTED='Suspected'
DEAD = 'Dead'

class ExacloudInstance(object):

    def __init__(self, _host, _port, _version, _auth_key, _requestype, _oeda_version):
        self.__id = str(_host)+":"+str(_port)
        self.__host = _host
        self.__port = _port
        self.__version = _version
        self.__auth_key = _auth_key
        self.__status = ALIVE
        self.__reqtype = _requestype
        self.__oeda_version = _oeda_version

    def mGetVersion(self):
        return self.__version

    def mGetOedaVersion(self):
        return self.__oeda_version

    def mGetRequestType(self):
        return self.__reqtype

    def mSetRequestType(self, aReqType):
        self.__reqtype = aReqType

    def mGetExacloudHostURL(self):
        return str(self.__host)+":"+str(self.__port)

    def mGetHost(self):
        return self.__host

    def mGetPort(self):
        return self.__port

    def mGetID(self):
        return self.__id

    def toString(self):
        return "Exacloud Instance ID = "+str(self.__id)

    def mSetStatus(self, status):
        self.__status = status

    def mGetStatus(self):
        return self.__status

    def mGetAuthKey(self):
        return self.__auth_key

