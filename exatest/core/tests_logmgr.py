#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/core/tests_logmgr.py /main/3 2022/11/09 12:51:49 jesandov Exp $
#
# tests_logmgr.py
#
# Copyright (c) 2020, 2022, Oracle and/or its affiliates.
#
#    NAME
#      tests_logmgr.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jejegonz    10/28/20 - Creation of Tests for exabox/log/LogMgr.py
#    jejegonz    10/28/20 - Creation
#

import unittest
from os import path, environ, makedirs
import subprocess
import pdb
import re
 
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import (ebLogInfo, ebLogError, ebLogVerbose,
                                ebLogWarn, ebLogHealth, ebLogCrit,
                                ebSetLogLvl, ebLogDB, ebLogAgent,
                                ebLogDiag, ebLogAddDestinationToLoggers,
                                ebGetDefaultLoggerName, ebLogDeleteLoggerDestination, ebFormattersEnum)
import logging
 
class ebTestLogMgr(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()

        self._log_dir = self.mGetUtil(self).mGetOutputDir()
        self._hostname_test = "host_test"
        self.test_uuid = "0"

        logging.getLogger('dfltlog').setLevel(logging.VERBOSE)
        logging.getLogger('database').setLevel(logging.VERBOSE)
        logging.getLogger('agent').setLevel(logging.VERBOSE)
        logging.getLogger('healthcheck').setLevel(logging.VERBOSE)
        logging.getLogger('diagnostic').setLevel(logging.VERBOSE)

    def _find_match(self,aLogMsg, aExpectedLines, file_name):
            # Adding -c flag, only getting how many lines match
        # Expected at least 1 match line.
        self.assertTrue(path.exists(file_name))
        grep = subprocess.Popen(['grep','-c', aLogMsg, file_name],
            shell=False, stdout=subprocess.PIPE)
        grep_output, _ = grep.communicate()
        number_match_lines = int(grep_output.decode('ascii').strip())
        self.assertEqual(number_match_lines, aExpectedLines) 

    def test_log_verbose(self):
        level = "VERBOSE"
        log_msg = "TEST TEST TEST " + level
        ebLogVerbose(log_msg)
        self._find_match(log_msg, 1, path.join(self._log_dir,  'exacloud.trc'))
        self._find_match(log_msg, 0, path.join(self._log_dir,  'exacloud.log'))
        self._find_match(log_msg, 0, path.join(self._log_dir,  'exacloud.err'))
        ebLogVerbose(log_msg)
        self._find_match(log_msg, 2, path.join(self._log_dir,  'exacloud.trc'))
        self._find_match(log_msg, 0, path.join(self._log_dir,  'exacloud.log'))
        self._find_match(log_msg, 0, path.join(self._log_dir,  'exacloud.err'))

    def test_log_info(self):
        level = "INFO"
        log_msg = "TEST TEST TEST " + level
        ebLogInfo(log_msg)
        self._find_match(log_msg, 1, path.join(self._log_dir, 'exacloud.trc'))
        self._find_match(log_msg, 1, path.join(self._log_dir, 'exacloud.log'))
        self._find_match(log_msg, 0, path.join(self._log_dir, 'exacloud.err'))
        ebLogInfo(log_msg)
        self._find_match(log_msg, 2, path.join(self._log_dir, 'exacloud.trc'))
        self._find_match(log_msg, 2, path.join(self._log_dir, 'exacloud.log'))
        self._find_match(log_msg, 0, path.join(self._log_dir, 'exacloud.err'))

    def test_log_warn(self):
        level = "WARNING"
        log_msg = "TEST TEST TEST " + level
        ebLogWarn(log_msg)
        self._find_match(log_msg, 1, path.join(self._log_dir, 'exacloud.trc'))
        self._find_match(log_msg, 1, path.join(self._log_dir, 'exacloud.log'))
        self._find_match(log_msg, 0, path.join(self._log_dir, 'exacloud.err'))
        ebLogWarn(log_msg)
        self._find_match(log_msg, 2, path.join(self._log_dir, 'exacloud.trc'))
        self._find_match(log_msg, 2, path.join(self._log_dir, 'exacloud.log'))
        self._find_match(log_msg, 0, path.join(self._log_dir, 'exacloud.err'))

    def test_log_error(self):
        level = "ERROR"
        log_msg = "TEST TEST TEST "+ level
        ebLogError(log_msg)
        self._find_match(log_msg, 1, path.join(self._log_dir, 'exacloud.trc'))
        self._find_match(log_msg, 1, path.join(self._log_dir, 'exacloud.log'))
        self._find_match(log_msg, 1, path.join(self._log_dir, 'exacloud.err'))
        ebLogError(log_msg)
        self._find_match(log_msg, 2, path.join(self._log_dir, 'exacloud.trc'))
        self._find_match(log_msg, 2, path.join(self._log_dir, 'exacloud.log'))
        self._find_match(log_msg, 2, path.join(self._log_dir, 'exacloud.err'))

    def test_log_crit(self):
        level = "CRITICAL"
        log_msg = "TEST TEST TEST " + level
        ebLogCrit(log_msg)
        self._find_match(log_msg, 1, path.join(self._log_dir, 'exacloud.trc'))
        self._find_match(log_msg, 1, path.join(self._log_dir, 'exacloud.log'))
        self._find_match(log_msg, 1, path.join(self._log_dir, 'exacloud.err'))
        ebLogCrit(log_msg)
        self._find_match(log_msg, 2, path.join(self._log_dir, 'exacloud.trc'))
        self._find_match(log_msg, 2, path.join(self._log_dir, 'exacloud.log'))
        self._find_match(log_msg, 2, path.join(self._log_dir, 'exacloud.err'))

    def test_log_database_debug(self):
        lvl = 'DBG'
        level = 'DEBUG'
        log_msg = "TEST TEST TEST " + level
        ebLogDB(lvl,log_msg)
        self._find_match(log_msg, 1, path.join(self._log_dir, 'database.trc'))
        self._find_match(log_msg, 0, path.join(self._log_dir, 'database.log'))
        self._find_match(log_msg, 0, path.join(self._log_dir, 'database.err'))
        ebLogDB(lvl,log_msg)
        self._find_match(log_msg, 2, path.join(self._log_dir, 'database.trc'))
        self._find_match(log_msg, 0, path.join(self._log_dir, 'database.log'))
        self._find_match(log_msg, 0, path.join(self._log_dir, 'database.err'))

    def test_log_database_info(self):
        lvl = 'NFO'
        level = 'INFO'
        log_msg = "TEST TEST TEST " + level
        ebLogDB(lvl,log_msg)
        self._find_match(log_msg, 1, path.join(self._log_dir, 'database.trc'))
        self._find_match(log_msg, 1, path.join(self._log_dir, 'database.log'))
        self._find_match(log_msg, 0, path.join(self._log_dir, 'database.err'))
        ebLogDB(lvl,log_msg)
        self._find_match(log_msg, 2, path.join(self._log_dir, 'database.trc'))
        self._find_match(log_msg, 2, path.join(self._log_dir, 'database.log'))
        self._find_match(log_msg, 0, path.join(self._log_dir, 'database.err'))
        
    def test_log_database_warn(self):
        lvl = 'WRN'
        level = 'WARNING'
        log_msg = "TEST TEST TEST " + level
        ebLogDB(lvl,log_msg)
        self._find_match(log_msg, 1, path.join(self._log_dir, 'database.trc'))
        self._find_match(log_msg, 1, path.join(self._log_dir, 'database.log'))
        self._find_match(log_msg, 0, path.join(self._log_dir, 'database.err'))
        ebLogDB(lvl,log_msg)
        self._find_match(log_msg, 2, path.join(self._log_dir, 'database.trc'))
        self._find_match(log_msg, 2, path.join(self._log_dir, 'database.log'))
        self._find_match(log_msg, 0, path.join(self._log_dir, 'database.err'))
    
    def test_log_database_error(self):
        lvl = 'ERR'
        level = 'ERROR'
        log_msg = "TEST TEST TEST " + level
        ebLogDB(lvl,log_msg)
        self._find_match(log_msg, 1, path.join(self._log_dir, 'database.trc'))
        self._find_match(log_msg, 1, path.join(self._log_dir, 'database.log'))
        self._find_match(log_msg, 1, path.join(self._log_dir, 'database.err'))
        ebLogDB(lvl,log_msg)
        self._find_match(log_msg, 2, path.join(self._log_dir, 'database.trc'))
        self._find_match(log_msg, 2, path.join(self._log_dir, 'database.log'))
        self._find_match(log_msg, 2, path.join(self._log_dir, 'database.err'))

    def test_log_database_critical(self):
        lvl = 'CRT'
        level = 'CRITICAL'
        log_msg = "TEST TEST TEST " + level
        ebLogDB(lvl,log_msg)
        self._find_match(log_msg, 1, path.join(self._log_dir, 'database.trc'))
        self._find_match(log_msg, 1, path.join(self._log_dir, 'database.log'))
        self._find_match(log_msg, 1, path.join(self._log_dir, 'database.err'))
        ebLogDB(lvl,log_msg)
        self._find_match(log_msg, 2, path.join(self._log_dir, 'database.trc'))
        self._find_match(log_msg, 2, path.join(self._log_dir, 'database.log'))
        self._find_match(log_msg, 2, path.join(self._log_dir, 'database.err'))
   
    def test_log_agent_debug(self):
        lvl = 'DBG'
        level = 'DEBUG'
        log_msg = "TEST TEST TEST " + level
        ebLogAgent(lvl,log_msg)
        self._find_match(log_msg, 1, path.join(self._log_dir, 'agent.trc'))
        self._find_match(log_msg, 0, path.join(self._log_dir, 'agent.log'))
        self._find_match(log_msg, 0, path.join(self._log_dir, 'agent.err'))
        ebLogAgent(lvl,log_msg)
        self._find_match(log_msg, 2, path.join(self._log_dir, 'agent.trc'))
        self._find_match(log_msg, 0, path.join(self._log_dir, 'agent.log'))
        self._find_match(log_msg, 0, path.join(self._log_dir, 'agent.err'))

    def test_log_agent_info(self):
        lvl = 'NFO'
        level = 'INFO'
        log_msg = "TEST TEST TEST " + level
        ebLogAgent(lvl,log_msg)
        self._find_match(log_msg, 1, path.join(self._log_dir, 'agent.trc'))
        self._find_match(log_msg, 1, path.join(self._log_dir, 'agent.log'))
        self._find_match(log_msg, 0, path.join(self._log_dir, 'agent.err'))
        ebLogAgent(lvl,log_msg)
        self._find_match(log_msg, 2, path.join(self._log_dir, 'agent.trc'))
        self._find_match(log_msg, 2, path.join(self._log_dir, 'agent.log'))
        self._find_match(log_msg, 0, path.join(self._log_dir, 'agent.err'))

    def test_log_agent_warn(self):
        lvl = 'WRN'
        level = 'WARNING'
        log_msg = "TEST TEST TEST " + level
        ebLogAgent(lvl,log_msg)
        self._find_match(log_msg, 1, path.join(self._log_dir, 'agent.trc'))
        self._find_match(log_msg, 1, path.join(self._log_dir, 'agent.log'))
        self._find_match(log_msg, 0, path.join(self._log_dir, 'agent.err'))
        ebLogAgent(lvl,log_msg)
        self._find_match(log_msg, 2, path.join(self._log_dir, 'agent.trc'))
        self._find_match(log_msg, 2, path.join(self._log_dir, 'agent.log'))
        self._find_match(log_msg, 0, path.join(self._log_dir, 'agent.err'))
    
    def test_log_agent_error(self):
        lvl = 'ERR'
        level = 'ERROR'
        log_msg = "TEST TEST TEST " + level
        ebLogAgent(lvl,log_msg)
        self._find_match(log_msg, 1, path.join(self._log_dir, 'agent.trc'))
        self._find_match(log_msg, 1, path.join(self._log_dir, 'agent.log'))
        self._find_match(log_msg, 1, path.join(self._log_dir, 'agent.err'))
        ebLogAgent(lvl,log_msg)
        self._find_match(log_msg, 2, path.join(self._log_dir, 'agent.trc'))
        self._find_match(log_msg, 2, path.join(self._log_dir, 'agent.log'))
        self._find_match(log_msg, 2, path.join(self._log_dir, 'agent.err'))

    def test_log_agent_critical(self):
        lvl = 'CRT'
        level = 'CRITICAL'
        log_msg = "TEST TEST TEST " + level
        ebLogAgent(lvl,log_msg)
        self._find_match(log_msg, 1, path.join(self._log_dir, 'agent.trc'))
        self._find_match(log_msg, 1, path.join(self._log_dir, 'agent.log'))
        self._find_match(log_msg, 1, path.join(self._log_dir, 'agent.err'))
        ebLogAgent(lvl,log_msg)
        self._find_match(log_msg, 2, path.join(self._log_dir, 'agent.trc'))
        self._find_match(log_msg, 2, path.join(self._log_dir, 'agent.log'))
        self._find_match(log_msg, 2, path.join(self._log_dir, 'agent.err'))

    def test_log_healthcheck_debug(self):
        lvl = 'DBG'
        level = 'DEBUG'
        log_msg = "TEST TEST TEST " + level
        ebLogHealth(lvl,log_msg)
        self._find_match(log_msg, 1, path.join(self._log_dir,
            'checkcluster', 'healthcheck.trc'))
        self._find_match(log_msg, 0, path.join(self._log_dir,
            'checkcluster', 'healthcheck.log'))
        self._find_match(log_msg, 0, path.join(self._log_dir,
            'checkcluster', 'healthcheck.err'))
        ebLogHealth(lvl,log_msg)
        self._find_match(log_msg, 2, path.join(self._log_dir,
            'checkcluster', 'healthcheck.trc'))
        self._find_match(log_msg, 0, path.join(self._log_dir,
            'checkcluster', 'healthcheck.log'))
        self._find_match(log_msg, 0, path.join(self._log_dir,
            'checkcluster', 'healthcheck.err'))

    def test_log_healthcheck_info(self):
        lvl = 'NFO'
        level = 'INFO'
        log_msg = "TEST TEST TEST " + level
        ebLogHealth(lvl,log_msg)
        self._find_match(log_msg, 1, path.join(self._log_dir,
            'checkcluster', 'healthcheck.trc'))
        self._find_match(log_msg, 1, path.join(self._log_dir,
            'checkcluster', 'healthcheck.log'))
        self._find_match(log_msg, 0, path.join(self._log_dir,
            'checkcluster', 'healthcheck.err'))
        ebLogHealth(lvl,log_msg)
        self._find_match(log_msg, 2, path.join(self._log_dir,
            'checkcluster', 'healthcheck.trc'))
        self._find_match(log_msg, 2, path.join(self._log_dir,
            'checkcluster', 'healthcheck.log'))
        self._find_match(log_msg, 0, path.join(self._log_dir,
            'checkcluster', 'healthcheck.err'))
        
    def test_log_healthcheck_warn(self):
        lvl = 'WRN'
        level = 'WARNING'
        log_msg = "TEST TEST TEST " + level
        ebLogHealth(lvl,log_msg)
        self._find_match(log_msg, 1, path.join(self._log_dir,
            'checkcluster', 'healthcheck.trc'))
        self._find_match(log_msg, 1, path.join(self._log_dir,
            'checkcluster', 'healthcheck.log'))
        self._find_match(log_msg, 0, path.join(self._log_dir,
            'checkcluster', 'healthcheck.err'))
        ebLogHealth(lvl,log_msg)
        self._find_match(log_msg, 2, path.join(self._log_dir,
            'checkcluster', 'healthcheck.trc'))
        self._find_match(log_msg, 2, path.join(self._log_dir,
            'checkcluster', 'healthcheck.log'))
        self._find_match(log_msg, 0, path.join(self._log_dir,
            'checkcluster', 'healthcheck.err'))
    
    def test_log_healthcheck_error(self):
        lvl = 'ERR'
        level = 'ERROR'
        log_msg = "TEST TEST TEST " + level
        ebLogHealth(lvl,log_msg)
        self._find_match(log_msg, 1, path.join(self._log_dir,
            'checkcluster', 'healthcheck.trc'))
        self._find_match(log_msg, 1, path.join(self._log_dir,
            'checkcluster', 'healthcheck.log'))
        self._find_match(log_msg, 1, path.join(self._log_dir,
            'checkcluster', 'healthcheck.err'))
        ebLogHealth(lvl,log_msg)
        self._find_match(log_msg, 2, path.join(self._log_dir,
            'checkcluster', 'healthcheck.trc'))
        self._find_match(log_msg, 2, path.join(self._log_dir,
            'checkcluster', 'healthcheck.log'))
        self._find_match(log_msg, 2, path.join(self._log_dir,
            'checkcluster', 'healthcheck.err'))

    def test_log_healthcheck_critical(self):
        lvl = 'CRT'
        level = 'CRITICAL'
        log_msg = "TEST TEST TEST " + level
        ebLogHealth(lvl,log_msg)
        self._find_match(log_msg, 1, path.join(self._log_dir,
            'checkcluster', 'healthcheck.trc'))
        self._find_match(log_msg, 1, path.join(self._log_dir,
            'checkcluster', 'healthcheck.log'))
        self._find_match(log_msg, 1, path.join(self._log_dir,
            'checkcluster', 'healthcheck.err'))
        ebLogHealth(lvl,log_msg)
        self._find_match(log_msg, 2, path.join(self._log_dir,
            'checkcluster', 'healthcheck.trc'))
        self._find_match(log_msg, 2, path.join(self._log_dir,
            'checkcluster', 'healthcheck.log'))
        self._find_match(log_msg, 2, path.join(self._log_dir,
            'checkcluster', 'healthcheck.err'))

    def test_log_diagnostic_debug(self):
        lvl = 'DBG'
        level = 'DEBUG'
        log_msg = "TEST TEST TEST " + level
        ebLogDiag(lvl,log_msg)
        self._find_match(log_msg, 1, path.join(self._log_dir,
              'diagnostic', 'diagnostic.trc'))
        self._find_match(log_msg, 0, path.join(self._log_dir,
              'diagnostic', 'diagnostic.log'))
        self._find_match(log_msg, 0, path.join(self._log_dir,
              'diagnostic', 'diagnostic.err'))
        ebLogDiag(lvl,log_msg)
        self._find_match(log_msg, 2, path.join(self._log_dir,
              'diagnostic', 'diagnostic.trc'))
        self._find_match(log_msg, 0, path.join(self._log_dir,
              'diagnostic', 'diagnostic.log'))
        self._find_match(log_msg, 0, path.join(self._log_dir,
              'diagnostic', 'diagnostic.err'))

    def test_log_diagnostic_info(self):
        lvl = 'NFO'
        level = 'INFO'
        log_msg = "TEST TEST TEST " + level
        ebLogDiag(lvl,log_msg)
        self._find_match(log_msg, 1, path.join(self._log_dir,
              'diagnostic', 'diagnostic.trc'))
        self._find_match(log_msg, 1, path.join(self._log_dir,
              'diagnostic', 'diagnostic.log'))
        self._find_match(log_msg, 0, path.join(self._log_dir,
              'diagnostic', 'diagnostic.err'))
        ebLogDiag(lvl,log_msg)
        self._find_match(log_msg, 2, path.join(self._log_dir,
              'diagnostic', 'diagnostic.trc'))
        self._find_match(log_msg, 2, path.join(self._log_dir,
              'diagnostic', 'diagnostic.log'))
        self._find_match(log_msg, 0, path.join(self._log_dir,
              'diagnostic', 'diagnostic.err'))

    def test_log_diagnostic_warn(self):
        lvl = 'WRN'
        level = 'WARNING'
        log_msg = "TEST TEST TEST " + level
        ebLogDiag(lvl,log_msg)
        self._find_match(log_msg, 1, path.join(self._log_dir,
              'diagnostic', 'diagnostic.trc'))
        self._find_match(log_msg, 1, path.join(self._log_dir,
              'diagnostic', 'diagnostic.log'))
        self._find_match(log_msg, 0, path.join(self._log_dir,
              'diagnostic', 'diagnostic.err'))
        ebLogDiag(lvl,log_msg)
        self._find_match(log_msg, 2, path.join(self._log_dir,
              'diagnostic', 'diagnostic.trc'))
        self._find_match(log_msg, 2, path.join(self._log_dir,
              'diagnostic', 'diagnostic.log'))
        self._find_match(log_msg, 0, path.join(self._log_dir,
              'diagnostic', 'diagnostic.err'))

    def test_log_diagnostic_error(self):
        lvl = 'ERR'
        level = 'ERROR'
        log_msg = "TEST TEST TEST " + level
        ebLogDiag(lvl,log_msg)
        self._find_match(log_msg, 1, path.join(self._log_dir,
              'diagnostic', 'diagnostic.trc'))
        self._find_match(log_msg, 1, path.join(self._log_dir,
              'diagnostic', 'diagnostic.log'))
        self._find_match(log_msg, 1, path.join(self._log_dir,
              'diagnostic', 'diagnostic.err'))
        ebLogDiag(lvl,log_msg)
        self._find_match(log_msg, 2, path.join(self._log_dir,
              'diagnostic', 'diagnostic.trc'))
        self._find_match(log_msg, 2, path.join(self._log_dir,
              'diagnostic', 'diagnostic.log'))
        self._find_match(log_msg, 2, path.join(self._log_dir,
              'diagnostic', 'diagnostic.err'))

    def test_log_diagnostic_critical(self):
        lvl = 'CRT'
        level = 'CRITICAL'
        log_msg = "TEST TEST TEST " + level
        ebLogDiag(lvl,log_msg)
        self._find_match(log_msg, 1, path.join(self._log_dir,
              'diagnostic', 'diagnostic.trc'))
        self._find_match(log_msg, 1, path.join(self._log_dir,
              'diagnostic', 'diagnostic.log'))
        self._find_match(log_msg, 1, path.join(self._log_dir,
              'diagnostic', 'diagnostic.err'))
        ebLogDiag(lvl,log_msg)
        self._find_match(log_msg, 2, path.join(self._log_dir,
              'diagnostic', 'diagnostic.trc'))
        self._find_match(log_msg, 2, path.join(self._log_dir,
              'diagnostic', 'diagnostic.log'))
        self._find_match(log_msg, 2, path.join(self._log_dir,
              'diagnostic', 'diagnostic.err'))

    def test_add_delete_handler_files(self):
        _filepath_no_extension = self._log_dir + 'logFileToDelete'
        _destination_handler = ebLogAddDestinationToLoggers([ebGetDefaultLoggerName()],
            _filepath_no_extension, ebFormattersEnum.DEFAULT)
        ebLogVerbose("TEST DELETE FILE HANDLER")
        self.assertTrue(path.exists("{0}.trc".format(_filepath_no_extension)))
        self.assertTrue(path.exists("{0}.err".format(_filepath_no_extension)))
        self.assertTrue(path.exists("{0}.log".format(_filepath_no_extension)))
        ebLogDeleteLoggerDestination(ebGetDefaultLoggerName(), _destination_handler, True)
        self.assertFalse(path.exists("{0}.trc".format(_filepath_no_extension)))
        self.assertFalse(path.exists("{0}.err".format(_filepath_no_extension)))
        self.assertFalse(path.exists("{0}.log".format(_filepath_no_extension)))
        

if __name__ == '__main__':
    unittest.main()
