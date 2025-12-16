#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/agent/tests_supervisor.py /main/1 2025/07/29 09:03:22 aararora Exp $
#
# tests_supervisor.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_supervisor.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aararora    07/08/25 - Unit tests for supervisor class
#    aararora    07/08/25 - Creation
#
import datetime
import signal
import threading
import unittest
from unittest.mock import patch, MagicMock
from exabox.core.DBStore import ebGetDefaultDB
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.agent.Supervisor import ebSupervisor, stop, supervisor_running

class ebTestSupervisor(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestSupervisor, self).setUpClass(aGenerateDatabase=True,aUseOeda=False)

    @patch('exabox.core.DBStore.ebGetDefaultDB')
    @patch('exabox.agent.Supervisor.get_gcontext')
    def test_mSetupCrontab(self, mock_get_gcontext, mock_ebGetDefaultDB):
        with patch('exabox.agent.Worker.gWorkerFactory', None):
            supervisor = ebSupervisor()
        mock_gcontext = MagicMock()
        mock_get_gcontext.return_value = mock_gcontext
        mock_gcontext.mGetConfigOptions.return_value = {
            'exacloud_base_path': '/path/to/exacloud'
        }
        mock_gcontext.mGetBasePath.return_value = '/path/to/exacloud'
        mock_db = MagicMock()
        mock_ebGetDefaultDB.return_value = mock_db
        # No agent port - no cron job setup
        supervisor.mSetupCrontab()
        mock_gcontext.mGetConfigOptions.return_value = {
            'agent_port': 1234,
            'exacloud_base_path': '/path/to/exacloud'
        }
        mock_gcontext.mGetBasePath.return_value = '/path/to/exacloud'
        mock_db = MagicMock()
        mock_ebGetDefaultDB.return_value = mock_db
        supervisor.mSetupCrontab()

    @patch('exabox.agent.Supervisor.get_gcontext')
    @patch('exabox.agent.Supervisor.CronTab')
    def test_mDeleteCrontab(self, mock_CronTab, mock_get_gcontext):
        mock_gcontext = MagicMock()
        with patch('exabox.agent.Worker.gWorkerFactory', None):
            supervisor = ebSupervisor()
        mock_get_gcontext.return_value = mock_gcontext
        mock_gcontext.mSetConfigOption('ociexacc',"True")
        mock_crontab = MagicMock()
        mock_CronTab.return_value = mock_crontab
        # it is exacc env
        supervisor.mDeleteCrontab()
        mock_gcontext.mSetConfigOption('ociexacc',"False")
        mock_gcontext.mCheckConfigOption.side_effect = [False, True]
        mock_crontab = MagicMock()
        mock_CronTab.return_value = mock_crontab
        # agent port is not None
        supervisor.mDeleteCrontab()

    @patch('psutil.pid_exists')
    @patch('exabox.agent.Supervisor.ebLogWarn')
    def test_mCheckAgentStatus_supervisor_stopped(self, mock_ebLogWarn, mock_psutil_pid_exists):
        with patch('exabox.agent.Worker.gWorkerFactory', None):
            instance = ebSupervisor()
        instance._running = False
        instance.mCheckAgentStatus()
        mock_ebLogWarn.assert_called_once_with("Supervisor has been asked to gracefully shutdown. skipping restart of exacloud agent.")

    @patch('exabox.agent.Supervisor.ebExaClient')
    @patch('exabox.agent.Supervisor.ebGetClientConfig')
    def test_mCheckAgentStatusSuccess(self, mock_ClientConfig, mock_ebExaClient):
        with patch('exabox.agent.Worker.gWorkerFactory', None):
            supervisor = ebSupervisor()
        supervisor._running = True
        mock_client = MagicMock()
        supervisor._healthcheckstart = datetime.datetime.now()
        mock_ebExaClient.return_value = mock_client
        mock_client.mGetJsonResponse.return_value = {'success': 'True'}
        supervisor.mCheckAgentStatus()
        supervisor._healthcheckstart = datetime.datetime.now().replace(microsecond=0) + datetime.timedelta(minutes = 3)
        supervisor.mCheckAgentStatus()

    @patch('exabox.agent.Supervisor.ebExaClient')
    @patch('exabox.agent.Supervisor.ebGetClientConfig')
    @patch.object(ebSupervisor, 'mTriggerCommand')
    @patch('psutil.Process')
    def test_mCheckAgentStatusNotSuccess(self, mock_psutil_process, mock_mTriggerCommand, mock_ClientConfig, mock_ebExaClient):
        with patch('exabox.agent.Worker.gWorkerFactory', None):
            supervisor = ebSupervisor()
        supervisor._running = True
        mock_client = MagicMock()
        supervisor._healthcheckstart = datetime.datetime.now()
        supervisor._db = MagicMock()
        mock_psutil_process.return_value = MagicMock()
        supervisor._db.mGetAgentsPID.return_value = [["10000"]]
        mock_ebExaClient.return_value = mock_client
        mock_client.mGetJsonResponse.return_value = {'success': 'False'}
        supervisor.mCheckAgentStatus()

    @patch('exabox.core.DBStore.ebGetDefaultDB')
    @patch('exabox.agent.Supervisor.psutil.pid_exists')
    def test_mCheckScheduler(self, mock_pid_exists, mock_ebGetDefaultDB):
        mock_db = MagicMock()
        mock_ebGetDefaultDB.return_value = mock_db
        with patch('exabox.agent.Worker.gWorkerFactory', None):
            supervisor = ebSupervisor()
        supervisor._running = True
        mock_db.mGetWorkerByType.return_value = [(1, 'scheduler', '', '', '', '', '', '', 1234, '', '', '', '')]
        mock_pid_exists.return_value = True
        supervisor.mCheckScheduler()

    @patch('subprocess.Popen')
    def test_mTriggerCommand(self, mock_Popen):
        with patch('exabox.agent.Worker.gWorkerFactory', None):
            supervisor = ebSupervisor()
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b'', b'')
        mock_Popen.returncode = 0
        mock_Popen.return_value = mock_process
        supervisor.mTriggerCommand('test command')
        mock_Popen.returncode = 1
        supervisor.mTriggerCommand('test command')

    @patch('signal.signal')
    def test_mSigHandler(self, mock_signal):
        with patch('exabox.agent.Worker.gWorkerFactory', None):
            supervisor = ebSupervisor()
        supervisor._db = MagicMock()
        supervisor._mSigHandler(signal.SIGTERM, None)
        self.assertFalse(supervisor._running)

    @patch('psutil.pid_exists')
    @patch('exabox.agent.Supervisor.ebLogWarn')
    def test_mCheckDispatcher_supervisor_stopped(self, mock_ebLogWarn, mock_psutil_pid_exists):
        with patch('exabox.agent.Worker.gWorkerFactory', None):
            instance = ebSupervisor()
        instance._running = False
        instance.mCheckDispatcher()
        mock_ebLogWarn.assert_called_once_with("Supervisor has been signaled to stop, skipping restart of dispatcher.")

    @patch('psutil.pid_exists')
    @patch('exabox.agent.Supervisor.ebLogError')
    @patch('exabox.agent.Supervisor.get_gcontext')
    @patch.object(ebSupervisor, 'mTriggerCommand')
    def test_mCheckDispatcher_dispatcher_not_running(self, mock_mTriggerCommand, mock_get_gcontext, mock_ebLogError, mock_psutil_pid_exists):
        with patch('exabox.agent.Worker.gWorkerFactory', None):
            instance = ebSupervisor()
        instance._running = True
        instance._db = MagicMock()
        instance._db.mGetWorkerByType.return_value = None
        mock_psutil_pid_exists.return_value = False
        mock_get_gcontext.return_value.mGetBasePath.return_value = '/path/to/base'
        instance.mCheckDispatcher()
        mock_ebLogError.assert_called_once_with("dispatcher process does not exist. Will attempt to restart the same.")
        mock_mTriggerCommand.assert_called_once()

    @patch('psutil.pid_exists')
    @patch('exabox.agent.Supervisor.ebLogError')
    @patch('exabox.agent.Supervisor.get_gcontext')
    @patch.object(ebSupervisor, 'mTriggerCommand')
    @patch('exabox.agent.Worker.ebWorker.mPopulate')  # Mock out mPopulate method
    @patch('exabox.agent.Supervisor.ebWorker', return_value=MagicMock())
    def test_mCheckDispatcher_dispatcher_running(self, mock_ebWorker, mock_mPopulate, mock_mTriggerCommand, mock_get_gcontext, mock_ebLogError, mock_psutil_pid_exists):
        with patch('exabox.agent.Worker.gWorkerFactory', None):
            instance = ebSupervisor()
        instance._running = True
        instance._db = MagicMock()
        instance._db.mGetWorkerByType.return_value = {'pid': 123}
        mock_mPopulate.return_value = None  # Return None from mPopulate
        mock_psutil_pid_exists.return_value = True
        instance.mCheckDispatcher()
        mock_ebLogError.assert_not_called()
        mock_mTriggerCommand.assert_not_called()

    @patch('psutil.pid_exists')
    @patch('exabox.agent.Supervisor.ebLogWarn')
    def test_mCheckWrkManager_supervisor_stopped(self, mock_ebLogWarn, mock_psutil_pid_exists):
        with patch('exabox.agent.Worker.gWorkerFactory', None):
            instance = ebSupervisor()
        instance._running = False
        instance.mCheckWrkManager()
        mock_ebLogWarn.assert_called_once_with("Supervisor has been signaled to stop, skipping restart of workermanager.")

    @patch('psutil.pid_exists')
    @patch('exabox.agent.Supervisor.ebLogError')
    @patch('exabox.agent.Supervisor.get_gcontext')
    @patch.object(ebSupervisor, 'mTriggerCommand')
    def test_mCheckWrkManager_workermanager_not_running(self, mock_mTriggerCommand, mock_get_gcontext, mock_ebLogError, mock_psutil_pid_exists):
        with patch('exabox.agent.Worker.gWorkerFactory', None):
            instance = ebSupervisor()
        instance._running = True
        instance._db = MagicMock()
        instance._db.mGetWorkerByType.return_value = None
        mock_psutil_pid_exists.return_value = False
        mock_get_gcontext.return_value.mGetBasePath.return_value = '/path/to/base'
        instance.mCheckWrkManager()
        mock_ebLogError.assert_called_once_with("workermanager process does not exist. Will attempt to restart the same.")
        mock_mTriggerCommand.assert_called_once()

    @patch('psutil.pid_exists')
    @patch('exabox.agent.Supervisor.ebLogError')
    @patch('exabox.agent.Supervisor.get_gcontext')
    @patch.object(ebSupervisor, 'mTriggerCommand')
    @patch('exabox.agent.Worker.ebWorker.mPopulate')  # Mock out mPopulate method
    @patch('exabox.agent.Supervisor.ebWorker', return_value=MagicMock())
    def test_mCheckWrkManager_workermanager_running(self, mock_worker, mock_mPopulate, mock_mTriggerCommand, mock_get_gcontext, mock_ebLogError, mock_psutil_pid_exists):
        with patch('exabox.agent.Worker.gWorkerFactory', None):
            instance = ebSupervisor()
        instance._running = True
        instance._db = MagicMock()
        instance._db.mGetWorkerByType.return_value = {'pid': 123}
        mock_mPopulate.return_value = None  # Return None from mPopulate
        mock_psutil_pid_exists.return_value = True
        instance.mCheckWrkManager()
        mock_ebLogError.assert_not_called()
        mock_mTriggerCommand.assert_not_called()

    @patch('ast.literal_eval')
    @patch('exabox.agent.Supervisor.daemonize_process')
    @patch.object(threading.Event, 'wait')
    @patch('exabox.agent.Supervisor.ebWorker', return_value=MagicMock())
    @patch('exabox.agent.Supervisor.ebGetDefaultDB')
    @patch.object(ebSupervisor, 'mUpdateResourceUtilisationInfo')
    @patch.object(ebSupervisor, 'mManageWorkers')
    def test_mStart_daemonizeProcess_called(self, mock_mManageWorkers, 
                                            mock_mUpdateResourceUtilisationInfo, 
                                            mock_db, mock_worker, mock_wait, mock_daemonize_process,
                                            mock_literal_eval):
        def mTestOrphanRequests():
            mock_values = [("123e4567-e89b-12d3-a456-426655440000",
                            "Pending",
                            "Sat Jan 1 00:00:00 2022",
                            "Sat Jan 2 00:00:00 2022",
                            "test",
                            '{"param1": "value1"}',
                            "",
                            "",
                            "",
                            "path/xml",
                            "",
                            "cluster1",
                            "",
                            '{"data": "example_data}"'
            )]
            return mock_values
        # Return None on first call, raise exception on second call
        # Since there is an infinite loop running with self._running set to True
        # below is a hack to unit test the method by raising the exception in 
        # notify.wait
        mock_wait.side_effect = [None, Exception('Break out of loop')]
        with patch('exabox.agent.Supervisor.redirect_std_descriptors') as mock_redirect_std_descriptors:
            with patch('exabox.agent.Supervisor.supervisor_running', return_value=False) as mock_supervisor_running:
                with patch('exabox.agent.Worker.gWorkerFactory', None):
                    instance = ebSupervisor()
                    with self.assertRaises(Exception):
                        mock_db.return_value.mOrphanRequests.return_value = mTestOrphanRequests()
                        instance.mStart()
                mock_daemonize_process.assert_called_once_with()
                mock_supervisor_running.assert_called_once()

    @patch('psutil.pid_exists')
    @patch('exabox.agent.Supervisor.ebLogError')
    @patch('exabox.agent.Supervisor.get_gcontext')
    @patch.object(ebSupervisor, 'mTriggerCommand')
    def test_mCheckScheduler_not_running(self, mock_mTriggerCommand, mock_get_gcontext, mock_ebLogError, mock_psutil_pid_exists):
        with patch('exabox.agent.Worker.gWorkerFactory', None):
            instance = ebSupervisor()
        instance._running = True
        instance._healthcheckstart = datetime.datetime.now()
        instance._db = MagicMock()
        instance._db.mGetWorkerByType.return_value = None
        mock_psutil_pid_exists.return_value = False
        mock_get_gcontext.return_value.mGetBasePath.return_value = '/path/to/base'
        instance.mCheckScheduler()

    @patch('psutil.pid_exists')
    @patch('exabox.agent.Supervisor.ebLogWarn')
    def test_mCheckScheduler_supervisor_stopped(self, mock_ebLogWarn, mock_psutil_pid_exists):
        with patch('exabox.agent.Worker.gWorkerFactory', None):
            instance = ebSupervisor()
        instance._running = False
        instance.mCheckScheduler()
        mock_ebLogWarn.assert_called_once_with("Supervisor has been signaled to stop, skipping restart of scheduler.")

    @patch('psutil.pid_exists')
    @patch('exabox.agent.Supervisor.ebLogError')
    @patch('exabox.agent.Supervisor.get_gcontext')
    @patch.object(ebSupervisor, 'mTriggerCommand')
    @patch('exabox.agent.Worker.ebWorker.mPopulate')  # Mock out mPopulate method
    @patch('exabox.agent.Supervisor.ebWorker', return_value=MagicMock())
    def test_mCheckScheduler_running(self, mock_worker, mock_mPopulate, mock_mTriggerCommand, mock_get_gcontext, mock_ebLogError, mock_psutil_pid_exists):
        with patch('exabox.agent.Worker.gWorkerFactory', None):
            instance = ebSupervisor()
        instance._running = True
        instance._healthcheckstart = datetime.datetime.now()
        instance._db = MagicMock()
        instance._db.mGetWorkerByType.return_value = {'pid': 123}
        mock_mPopulate.return_value = None  # Return None from mPopulate
        mock_psutil_pid_exists.return_value = True
        instance.mCheckScheduler()
        mock_ebLogError.assert_not_called()
        mock_mTriggerCommand.assert_not_called()

    def test_mLogTopStatsSorted(self):
        with patch('exabox.agent.Worker.gWorkerFactory', None):
            instance = ebSupervisor()
        instance.mLogTopStatsSorted()

    def test_mUpdateResourceUtilisationInfo(self):
        def mSelectEnvironmentDetails():
            _last_update_time = datetime.datetime.now().replace(microsecond=0) - datetime.timedelta(minutes = 3)
            return 70, 60, str(_last_update_time)
        with patch('exabox.agent.Worker.gWorkerFactory', None):
            instance = ebSupervisor()
        instance._db = MagicMock()
        instance._cpu_threshold = 0
        instance._db.mSelectAllFromEnvironmentResourceDetails = mSelectEnvironmentDetails
        instance.mUpdateResourceUtilisationInfo()

    @patch.object(ebSupervisor, 'mGetIdleWorkersForTermination', return_value=['10000'])
    @patch.object(ebSupervisor, 'mGetCorruptedWorkersForTermination', return_value=['10001'])
    @patch('exabox.agent.Supervisor.ebWorker', return_value=MagicMock())
    @patch('exabox.agent.Supervisor.ebWorkerCmd', return_value=MagicMock())
    def test_mManageWorkers(self, mock_worker_command, mock_worker, mock_mGetCorruptedWorkersForTermination,
                            mock_mGetIdleWorkersForTermination):
        with patch('exabox.agent.Worker.gWorkerFactory', None):
            instance = ebSupervisor()
        instance._db = MagicMock()
        instance.mManageWorkers()

    @patch.object(ebSupervisor, 'mGetIdleWorkersForTermination', return_value=['10000'])
    @patch.object(ebSupervisor, 'mGetCorruptedWorkersForTermination', return_value=['10001'])
    @patch('exabox.agent.Supervisor.ebWorker', return_value=MagicMock())
    @patch('exabox.agent.Supervisor.ebWorkerCmd', return_value=MagicMock())
    def test_mManageWorkersIdleWorkers(self, mock_worker_command, mock_worker, mock_mGetCorruptedWorkersForTermination,
                            mock_mGetIdleWorkersForTermination):
        def get_idle_worker():
            return "00000000-0000-0000-0000-000000000000"
        with patch('exabox.agent.Worker.gWorkerFactory', None):
            instance = ebSupervisor()
        instance._db = MagicMock()
        mock_worker.return_value.mGetUUID.return_value = get_idle_worker()
        instance.mManageWorkers()

    @patch('ast.literal_eval')
    def test_mGetCorruptedWorkersForTermination(self, mock_eval):
        with patch('exabox.agent.Worker.gWorkerFactory', None):
            instance = ebSupervisor()
        mock_eval.return_value = [((1, 'worker', '', '', '', '', '', '', '', 1234, '', '', '', 'CORRUPTED'))]
        instance._db = MagicMock()
        instance.mGetCorruptedWorkersForTermination()

    def test_mGetIdleWorkerCount(self):
        with patch('exabox.agent.Worker.gWorkerFactory', None):
            instance = ebSupervisor()
        instance._db = MagicMock()
        gContext = self.mGetContext()
        gConfigOptions = gContext.mGetConfigOptions()
        instance.mGetIdleWorkerCount(gConfigOptions)

    @patch('ast.literal_eval')
    def test_mGetIdleWorkersForTermination(self, mock_eval):
        with patch('exabox.agent.Worker.gWorkerFactory', None):
            instance = ebSupervisor()
        instance._db = MagicMock()
        mock_eval.return_value = [(1, 'Idle', '', '', '', '', '', '', '', 1234, '', '', str(datetime.datetime.now()), ''),
                                  (2, 'Idle', '', '', '', '', '', '', '', 12345, '', '', str(datetime.datetime.now()), ''),
                                  (3, 'Idle', '', '', '', '', '', '', '', 12346, '', '', str(datetime.datetime.now()), ''),
                                  (4, 'Idle', '', '', '', '', '', '', '', 12347, '', '', str(datetime.datetime.now()), ''),
                                  (5, 'Idle', '', '', '', '', '', '', '', 12348, '', '', str(datetime.datetime.now()), '')]
        instance.mGetIdleWorkersForTermination()

    def test_mIsRunning(self):
        with patch('exabox.agent.Worker.gWorkerFactory', None):
            instance = ebSupervisor()
        instance.mIsRunning()

    @patch('exabox.agent.Supervisor.ebGetDefaultDB')
    @patch('exabox.agent.Supervisor.psutil.pid_exists')
    def test_mCheckSupervisorRunning(self, mock_pid_exists, mock_ebGetDefaultDB):
        mock_db = MagicMock()
        mock_ebGetDefaultDB.return_value = mock_db
        mock_db.mGetWorkerByType.return_value = (1, 'supervisor', '', '', '', '', '', '', 1234, '', '', '', '')
        mock_pid_exists.return_value = True
        supervisor_running()
        mock_db.mGetWorkerByType.return_value = ()
        # Supervisor returned db value is None
        supervisor_running()

    @patch('exabox.agent.Supervisor.supervisor_running', return_value='')
    def test_mSupervisorStop(self, mock_supervisor_running):
        stop()

if __name__ == '__main__':
    unittest.main()