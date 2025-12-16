#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/tests_exabox.py /main/4 2024/02/23 09:15:51 jesandov Exp $
#
# tests_exabox.py
#
# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
#
#    NAME
#      tests_exabox.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    gparada     14/09/23 - 35715235 Add UT: duplicated property in JSON
#    hgaldame    11/08/22 - 34778659 - ociexacc: exacloud cli command for 
#                           health metrics network configuration on cps host 
#    alsepulv    03/25/22 - Creation
#

import argparse
import json
import os
import unittest
from unittest.mock import patch

from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.config.Config import ebLoadProgramArguments

from exabox.bin.exabox import (clean_environment, ebExaboxState,
                               execute_from_commandline, main)

class ebTestExaBox(ebTestClucontrol):
    def setUp(self):
        super().setUp()

    @classmethod
    def setUpClass(self):
        super().setUpClass(False,False)
        self.mGetParser(self)

    def mGetParser(self):
        self.__parser = argparse.ArgumentParser()

        _program_arguments, _, _, _ = ebLoadProgramArguments()

        for _prog_arg_name, _prog_arg_kw in _program_arguments.items():

            args = ['-' + _prog_arg_kw['shortname']] if 'shortname' in _prog_arg_kw else []
            args.append('--' + _prog_arg_name)

            kwargs = { k: v for k, v in _prog_arg_kw.items()
                                                          if k != 'shortname' }
            self.__parser.add_argument(*args, **kwargs)

    def test_clean_env(self):
        os.environ["TMPDIR"] = os.path.abspath(os.path.dirname(__file__))
        clean_environment()
        os.environ["TMPDIR"] = "/this/does/not/exist"
        # cleans environment variable "TMPDIR"
        clean_environment()

    @patch("exabox.core.CrashDump.CrashDump.WriteCrashDump")
    @patch("exabox.bin.exabox.clean_environment")
    def test_exceptions(self, mock_clean_environment, mock_crash_dump):
        mock_clean_environment.side_effect = [ExacloudRuntimeError, TypeError,
                                              KeyboardInterrupt, SystemExit]

        with self.assertRaises(SystemExit):
            main()

        with self.assertRaises(SystemExit):
            main()

        with self.assertRaises(KeyboardInterrupt):
            main()

        with self.assertRaises(SystemExit):
            main()

    @patch("exabox.core.Core.exaBoxCoreInit")
    @patch("exabox.core.Context.exaBoxContext.mGetArgsOptions")
    @patch("exabox.bin.exabox.ebLogInit")
    def test_misc(self, mock_logInit, mock_options, mock_ebCoreInit):
        _state = ebExaboxState()
        _args = []
        _args.append(self.__parser.parse_args(["--version"]))
        _args.append(self.__parser.parse_args(["--short-version"]))
        _args.append(self.__parser.parse_args(["-id", "exatest"]))

        for _options in _args:
            mock_options.return_value = _options
            execute_from_commandline(_options, _state)

    @patch("exabox.bin.exabox.ExaMySQL")
    @patch("exabox.core.Core.exaBoxCoreInit")
    @patch("exabox.core.Context.exaBoxContext.mGetArgsOptions")
    @patch("exabox.bin.exabox.ebLogInit")
    def test_mysql(self, mock_logInit, mock_options, mock_ebCoreInit,
                   mock_mysql):
        _state = ebExaboxState()
        _args = []
        _args.append(self.__parser.parse_args(["--mysql-db", "start"]))
        _args.append(self.__parser.parse_args(["--mysql-db", "stop"]))
        _args.append(self.__parser.parse_args(["--mysql-db", "status"]))
        _args.append(self.__parser.parse_args(["--mysql-db", "prechecks"]))

        for _options in _args:
            mock_options.return_value = _options
            execute_from_commandline(_options, _state)

    @patch("exabox.bin.exabox.ProxyHeartbeat")
    @patch("exabox.core.DBStore3.ebExacloudDB")
    @patch("exabox.core.Core.exaBoxCoreInit")
    @patch("exabox.core.Context.exaBoxContext.mGetArgsOptions")
    @patch("exabox.bin.exabox.ebLogInit")
    def test_proxy(self, mock_logInit, mock_options, mock_ebCoreInit,
                   mock_exacloudDB, mock_heartbeat):
        _state = ebExaboxState()
        _options = self.__parser.parse_args(["--proxy", "start",
                                        "--migrateproxydb", "on"])

        mock_exacloudDB.mMigrateProxyDb.return_value = False
        mock_options.return_value = _options
        execute_from_commandline(_options, _state)

        _options = self.__parser.parse_args(["--proxy", "start", "-hb"])
        mock_options.return_value = _options
        execute_from_commandline(_options, _state)

    @patch("exabox.bin.exabox.ebRackControl")
    @patch("exabox.bin.exabox.ebInitDBLayer")
    @patch("exabox.core.Core.exaBoxCoreInit")
    @patch("exabox.core.Context.exaBoxContext.mGetArgsOptions")
    @patch("exabox.bin.exabox.ebLogInit")
    def test_rack(self, mock_logInit, mock_options, mock_ebCoreInit,
                   mock_initDB, mock_rackControl):
        _state = ebExaboxState()
        _options = self.__parser.parse_args(["--rack", "list"])

        mock_options.return_value = _options
        execute_from_commandline(_options, _state)

    @patch("exabox.bin.exabox.fetch_update_ecregistrationinfo")
    @patch("exabox.bin.exabox.ebInitDBLayer")
    @patch("exabox.core.Core.exaBoxCoreInit")
    @patch("exabox.core.Context.exaBoxContext.mGetArgsOptions")
    @patch("exabox.bin.exabox.ebLogInit")
    def test_eccontrol(self, mock_logInit, mock_options, mock_ebCoreInit,
                   mock_initDB, mock_eccontrol):
        _state = ebExaboxState()
        _options = self.__parser.parse_args(["--eccontrol", "list"])

        mock_options.return_value = _options
        execute_from_commandline(_options, _state)

    @patch("exabox.bin.exabox.ebExaClient")
    @patch("exabox.bin.exabox.ebThreadStartHangMonitoring")
    @patch("exabox.core.Core.exaBoxCoreInit")
    @patch("exabox.core.Context.exaBoxContext.mGetArgsOptions")
    @patch("exabox.bin.exabox.ebLogInit")
    def test_agentloc(self, mock_logInit, mock_options, mock_ebCoreInit,
                   mock_threadMonitor, mock_exaclient):
        _state = ebExaboxState()

        # agentloc
        _options = self.__parser.parse_args(["--thread-monitor", "1",
                        "--status", "exatest", "--agentloc", "exatest"])
        mock_options.return_value = _options
        execute_from_commandline(_options, _state)

        # status
        _options = self.__parser.parse_args(["--status", "exatest"])
        mock_options.return_value = _options
        execute_from_commandline(_options, _state)

    @patch("exabox.bin.exabox.ebGetDefaultDB")
    @patch("exabox.bin.exabox.ebInitDBLayer")
    @patch("exabox.bin.exabox.ebWorkerDaemon")
    @patch("exabox.bin.exabox.ebWorkerCmd")
    @patch("exabox.core.Core.exaBoxCoreInit")
    @patch("exabox.core.Context.exaBoxContext.mGetArgsOptions")
    @patch("exabox.bin.exabox.ebLogInit")
    def test_worker(self, mock_logInit, mock_options, mock_ebCoreInit,
                   mock_ebWorkerCmd, mock_workerDaemon, mock_initDB,
                   mock_defaultDB):
        _state = ebExaboxState()

        # workercmd
        _options = self.__parser.parse_args(["--workercmd", "exatest",
                        "--workerport", "9100"])
        mock_options.return_value = _options
        execute_from_commandline(_options, _state)

        # worker
        _options = self.__parser.parse_args(["--worker",
                        "--workerport", "9100"])
        mock_options.return_value = _options
        execute_from_commandline(_options, _state)

    @patch("exabox.bin.exabox.exaBoxPackage")
    @patch("exabox.bin.exabox.exaBoxNode")
    @patch("exabox.core.Core.exaBoxCoreInit")
    @patch("exabox.core.Context.exaBoxContext.mGetArgsOptions")
    @patch("exabox.bin.exabox.ebLogInit")
    def test_installpkg(self, mock_logInit, mock_options, mock_ebCoreInit,
                        mock_ebNode, mock_ebPackage):
        _state = ebExaboxState()

        mock_ebPackage.return_value.mGetPackageName.return_value = "exatest"

        _options = self.__parser.parse_args(["--installpkg", "exatest"])
        mock_options.return_value = _options
        execute_from_commandline(_options, _state)

    @patch("exabox.bin.exabox.ebVgLifeCycle")
    @patch("exabox.bin.exabox.exaBoxNode")
    @patch("exabox.bin.exabox.ebInitDBLayer")
    @patch("exabox.core.Core.exaBoxCoreInit")
    @patch("exabox.core.Context.exaBoxContext.mGetArgsOptions")
    @patch("exabox.bin.exabox.ebLogInit")
    def test_vmctrl(self, mock_logInit, mock_options, mock_ebCoreInit,
                    mock_initDB, mock_ebNode, mock_lifeCycle):
        _state = ebExaboxState()

        _options = self.__parser.parse_args(["--vmctrl", "ping"])
        mock_options.return_value = _options
        execute_from_commandline(_options, _state)

    @patch("exabox.bin.exabox.exaBoxNode")
    @patch("exabox.core.Core.exaBoxCoreInit")
    @patch("exabox.core.Context.exaBoxContext.mGetArgsOptions")
    @patch("exabox.bin.exabox.ebLogInit")
    def test_pwdless(self, mock_logInit, mock_options, mock_ebCoreInit,
                    mock_ebNode):
        _state = ebExaboxState()

        _options = self.__parser.parse_args(["--pwdless"])
        mock_options.return_value = _options
        execute_from_commandline(_options, _state)

    @patch("exabox.bin.exabox.exaBoxNode")
    @patch("exabox.core.Core.exaBoxCoreInit")
    @patch("exabox.core.Context.exaBoxContext.mGetArgsOptions")
    @patch("exabox.bin.exabox.ebLogInit")
    def test_setupssh(self, mock_logInit, mock_options, mock_ebCoreInit,
                    mock_ebNode):
        _state = ebExaboxState()

        _options = self.__parser.parse_args(["--setupsshkey"])
        mock_options.return_value = _options
        execute_from_commandline(_options, _state)

    @patch("exabox.bin.exabox.ebDNSConfig")
    @patch("exabox.core.Core.exaBoxCoreInit")
    @patch("exabox.core.Context.exaBoxContext.mGetArgsOptions")
    @patch("exabox.bin.exabox.ebLogInit")
    def test_setupdns(self, mock_logInit, mock_options, mock_ebCoreInit,
                    mock_ebDNS):
        _state = ebExaboxState()

        _options = self.__parser.parse_args(["--setupdns", "all"])
        mock_options.return_value = _options
        execute_from_commandline(_options, _state)

    @patch("exabox.bin.exabox.ebCluPatchDispatcher")
    @patch("exabox.core.Core.exaBoxCoreInit")
    @patch("exabox.core.Context.exaBoxContext.mGetArgsOptions")
    @patch("exabox.bin.exabox.ebLogInit")
    def test_patchclu(self, mock_logInit, mock_options, mock_ebCoreInit,
                    mock_ebCluPatch):
        _state = ebExaboxState()

        _options = self.__parser.parse_args(["--patch-cluster", "apply"])
        mock_options.return_value = _options
        execute_from_commandline(_options, _state)

        _options = self.__parser.parse_args(["--patch-cluster", "apply", "-jc",
                                             "/path/to/payload.json"])
        mock_options.return_value = _options
        execute_from_commandline(_options, _state)

    @patch("exabox.bin.exabox.ExaKmsEndpoint")
    @patch("exabox.core.Core.exaBoxCoreInit")
    @patch("exabox.core.Context.exaBoxContext.mGetArgsOptions")
    @patch("exabox.bin.exabox.ebLogInit")
    def test_exakms(self, mock_logInit, mock_options, mock_ebCoreInit,
                    mock_exakms):
        _state = ebExaboxState()

        _options = self.__parser.parse_args(["--exakms", "backup", "-jc",
                                             "/path/to/payload.json"])
        mock_options.return_value = _options
        execute_from_commandline(_options, _state)

    @patch("exabox.bin.exabox.ebJsonDispatcher")
    @patch("exabox.core.Core.exaBoxCoreInit")
    @patch("exabox.core.Context.exaBoxContext.mGetArgsOptions")
    @patch("exabox.bin.exabox.ebLogInit")
    def test_jsondispatch(self, mock_logInit, mock_options, mock_ebCoreInit,
                    mock_jsondispatch):
        _state = ebExaboxState()

        _options = self.__parser.parse_args(["--json-dispatch", "sla"])
        mock_options.return_value = _options
        execute_from_commandline(_options, _state)

        _options = self.__parser.parse_args(["--json-dispatch", "sla", "-jc",
                                             "/path/to/payload.json"])
        mock_options.return_value = _options
        execute_from_commandline(_options, _state)

    @patch("exabox.bin.exabox.os.makedirs")
    @patch("exabox.bin.exabox.ebFacadeXmlGen")
    @patch("exabox.core.Core.exaBoxCoreInit")
    @patch("exabox.core.Context.exaBoxContext.mGetArgsOptions")
    @patch("exabox.bin.exabox.ebLogInit")
    def test_elastic(self, mock_logInit, mock_options, mock_ebCoreInit,
                    mock_xmlgen, mock_makedirs):
        _state = ebExaboxState()

        _options = self.__parser.parse_args(["--elastic_shapes", "xmlgen"])
        mock_options.return_value = _options
        execute_from_commandline(_options, _state)

        _options = self.__parser.parse_args(["--elastic_shapes", "xmlgen",
                                             "-jc",
                                             "/path/to/payload.json"])
        mock_options.return_value = _options
        execute_from_commandline(_options, _state)

    @patch("exabox.bin.exabox.os.makedirs")
    @patch("exabox.bin.exabox.ebFacadeXmlGen")
    @patch("exabox.core.Core.exaBoxCoreInit")
    @patch("exabox.core.Context.exaBoxContext.mGetArgsOptions")
    @patch("exabox.bin.exabox.ebLogInit")
    def test_duplicated_property(self, mock_logInit, mock_options, mock_ebCoreInit,
                    mock_xmlgen, mock_makedirs):
        """
        In this scenario, exabox loads a JSON containing duplicated entries 
        for the same property (meaning property is duplicated).
        There's NO need to handle exception since python libraries automatically
        handle this scenario. When a property is repeated, the parser always
        takes the value from the "last occurrence" of such property. 
        See ref below.
        
        https://www.rfc-editor.org/rfc/rfc4627#section-2.2
        "The names within an object SHOULD be unique."

        https://www.ecma-international.org/ecma-262/#sec-json.parse
        "In the case where there are duplicate name Strings within an object, 
        lexically preceding values for the same key shall be overwritten."

        So, if a JSON needs to be validated we can use:
        exabox/exatest/exatest.py -vj -f /path/your_desired_file.json

        exabox/exatest/exatest.py -vj -f 
          exabox/exatest/resources/payload_duplicated_prop.json                 
        """
        _state = ebExaboxState()

        _json_path = "exabox/exatest/resources/payload_duplicated_prop.json"
        _json_path = os.path.join(get_gcontext().mGetBasePath(),_json_path)

        _options = self.__parser.parse_args(["--elastic_shapes", "xmlgen",
                                             "-jc",
                                             _json_path])     
        mock_options.return_value = _options        
        execute_from_commandline(_options, _state)
        print(_options)

    @patch("exabox.bin.exabox.ebBasicAuthStorage")
    @patch("exabox.bin.exabox.ebConvertToWalletStorage")
    @patch("exabox.core.Core.exaBoxCoreInit")
    @patch("exabox.core.Context.exaBoxContext.mGetArgsOptions")
    @patch("exabox.bin.exabox.ebLogInit")
    def test_createwallet(self, mock_logInit, mock_options, mock_ebCoreInit,
                        mock_converter, mock_auth):
        _state = ebExaboxState()

        mock_converter.return_value.mCheckPrereq.return_value = True

        _options = self.__parser.parse_args(["--createwallet"])
        mock_options.return_value = _options
        execute_from_commandline(_options, _state)

        mock_auth.side_effect = TypeError
        _options = self.__parser.parse_args(["--createwallet"])
        mock_options.return_value = _options
        with self.assertRaises(TypeError):
            execute_from_commandline(_options, _state)

    @patch("exabox.bin.exabox.ProxyClient")
    @patch("exabox.bin.exabox.ebInitDBLayer")
    @patch("exabox.bin.exabox.ebGetDefaultDB")
    @patch("exabox.core.Core.exaBoxCoreInit")
    @patch("exabox.core.Context.exaBoxContext.mGetArgsOptions")
    @patch("exabox.bin.exabox.ebLogInit")
    def test_agent_misc(self, mock_logInit, mock_options, mock_ebCoreInit,
                        mock_defaultDB, mock_initDB, mock_proxy):
        _state = ebExaboxState()

        _options = self.__parser.parse_args(["--agent", "suspend"])
        mock_options.return_value = _options
        execute_from_commandline(_options, _state)

        _options = self.__parser.parse_args(["--agent", "activate"])
        mock_options.return_value = _options
        execute_from_commandline(_options, _state)

        _options = self.__parser.parse_args(["--agent", "register"])
        mock_options.return_value = _options
        execute_from_commandline(_options, _state)

        _options = self.__parser.parse_args(["--agent", "deregister"])
        mock_options.return_value = _options
        execute_from_commandline(_options, _state)

    @patch("exabox.bin.exabox.AgentSignal")
    @patch("exabox.bin.exabox.AgentWorkerPIDListing")
    @patch("exabox.bin.exabox.ebInitDBLayer")
    @patch("exabox.bin.exabox.ebGetDefaultDB")
    @patch("exabox.core.Core.exaBoxCoreInit")
    @patch("exabox.core.Context.exaBoxContext.mGetArgsOptions")
    @patch("exabox.bin.exabox.ebLogInit")
    def test_agent_reload(self, mock_logInit, mock_options, mock_ebCoreInit,
                        mock_defaultDB, mock_initDB, mock_listing, mock_signal):
        _state = ebExaboxState()

        mock_listing.getWorkerPIDs.return_code = [1]

        _options = self.__parser.parse_args(["--agent", "reload"])
        mock_options.return_value = _options
        execute_from_commandline(_options, _state)

    @patch("exabox.bin.exabox.ebGetClientConfig")
    @patch("exabox.bin.exabox.ebWorkerFactory")
    @patch("exabox.bin.exabox.ebExaClient")
    @patch("exabox.bin.exabox.ebInitDBLayer")
    @patch("exabox.bin.exabox.ebGetDefaultDB")
    @patch("exabox.core.Core.exaBoxCoreInit")
    @patch("exabox.core.Context.exaBoxContext.mGetArgsOptions")
    @patch("exabox.bin.exabox.ebLogInit")
    def test_agent_status(self, mock_logInit, mock_options, mock_ebCoreInit,
                        mock_defaultDB, mock_initDB, mock_client, mock_factory,
                        mock_client_config):
        _state = ebExaboxState()

        mock_client_config.return_value = ["localhost", 9100]

        _options = self.__parser.parse_args(["--agent", "status", "--debug"])
        mock_options.return_value = _options

        mock_client.return_value.mGetJsonResponse.return_value = {"success":
                                                                   True}
        execute_from_commandline(_options, _state)

        mock_client.return_value.mGetJsonResponse.return_value = {"success":
                                                                   False}
        execute_from_commandline(_options, _state)

    @patch("exabox.bin.exabox.ebGetClientConfig")
    @patch("exabox.bin.exabox.os.popen")
    @patch("exabox.bin.exabox.ebAgentDaemon")
    @patch("exabox.bin.exabox.AgentWorkerPIDListing")
    @patch("exabox.bin.exabox.ebExaClient")
    @patch("exabox.bin.exabox.is_mysql_running")
    @patch("exabox.bin.exabox.ebInitDBLayer")
    @patch("exabox.bin.exabox.ebGetDefaultDB")
    @patch("exabox.core.Core.exaBoxCoreInit")
    @patch("exabox.core.Context.exaBoxContext.mGetArgsOptions")
    @patch("exabox.bin.exabox.ebLogInit")
    def test_agent_stop(self, mock_logInit, mock_options, mock_ebCoreInit,
                        mock_defaultDB, mock_initDB, mock_mysql_running,
                        mock_client, mock_listing, mock_agentDaemon,
                        mock_popen, mock_clientConfig):
        _state = ebExaboxState()

        mock_mysql_running.return_value = True
        mock_client.return_value.mGetJsonResponse.return_value = {"success":
                                                                   True}
        mock_listing.getWorkerPIDs.side_effect = [["33000"], ["33000", "33001"],
                                                  ["33000"], ["33000", "33001"]]
        mock_popen.return_value.read.return_value = ""
        mock_clientConfig.return_value = ["localhost", 9100]

        _options = self.__parser.parse_args(["--agent", "stop"])
        mock_options.return_value = _options
        execute_from_commandline(_options, _state)

        _options = self.__parser.parse_args(["--agent", "stop",
                                             "--forceshutdown"])
        mock_options.return_value = _options
        execute_from_commandline(_options, _state)

    @patch("exabox.bin.exabox.ebDNSConfig")
    @patch("exabox.core.Core.exaBoxCoreInit")
    @patch("exabox.core.Context.exaBoxContext.mGetArgsOptions")
    @patch("exabox.bin.exabox.ebLogInit")
    def test_configure_health_check_metrics(self, mock_logInit, mock_options, mock_ebCoreInit,
                    mock_ebDNS):
        _state = ebExaboxState()

        _options = self.__parser.parse_args(["--healthcheckmetrics", "all"])
        mock_options.return_value = _options
        execute_from_commandline(_options, _state)

if __name__ == "__main__":    
    unittest.main(buffer=False)
