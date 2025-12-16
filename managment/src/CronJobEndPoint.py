#!/bin/python
"""
$Header: ecs/exacloud/exabox/managment/src/CronJobEndPoint.py /main/1 2022/12/13 15:57:01 anhiguer Exp $

CronJobEndPoint.py

 Copyright (c) 2022, Oracle and/or its affiliates.

   NAME
     CronJobEndPoint.py - <one-line expansion of the name>

   DESCRIPTION
     <short description of component this file declares/defines>

   NOTES
     <other useful comments, qualifications, etc.>

   MODIFIED   (MM/DD/YY)
   anhiguer    11/24/22 - 34728392 - Creation

"""
from exabox.BaseServer.BaseEndpoint import BaseEndpoint
import subprocess


class CronJobEndPoint(BaseEndpoint):

    def __init__(self, aHttpUrlArgs, aHttpBody, aHttpResponse, aSharedData):
        # Initialization of the base class
        BaseEndpoint.__init__(self, aHttpUrlArgs, aHttpBody, aHttpResponse, aSharedData)
    
    def mGet(self):
        # Set ecra user by default 
        _user = "ecra"
        _json = None
        if self.mGetUrlArgs() is not None:
            _url_args = list(self.mGetUrlArgs().keys())
            if "user" in _url_args:
                _user = self.mGetUrlArgs()["user"]
            if "json" in _url_args:
                _json = "--json"
        
        _cmd_to_exec = ["/usr/bin/sudo", "/opt/oci/exacc/cpscronjobs/bin/exacc_crontab.py", "-l", "-u", _user]
        if _json:
            _cmd_to_exec.append(_json)
        print(_cmd_to_exec)
        _p = subprocess.Popen(_cmd_to_exec, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, encoding="utf-8")
        _stdout, _stderr = _p.communicate()
        # Failure
        if _p.returncode != 0:
            self.mGetResponse()["status"] = 500
            self.mGetResponse()["error"] = "Error listing crons{0} {1}".format(_stdout, _stderr)
            return
        # Success
        self.mGetResponse()["text"] = _stdout
