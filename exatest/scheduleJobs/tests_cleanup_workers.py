#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/scheduleJobs/tests_cleanup_workers.py /main/2 2026/04/17 18:05:00 aypaul Exp $
#
# tests_cleanup_workers.py
#
# Unit tests for scheduleJobs.cleanup_workers
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      04/16/26 - Bug#38900303 Fix unit tests for codev identified issues
#

import importlib
import json
import subprocess
import sys
import unittest
from unittest.mock import MagicMock, call, mock_open, patch

import types
import _thread

try:
    import six  # type: ignore
except ImportError:  # pragma: no cover - fallback for minimal environments
    six = types.ModuleType("six")  # type: ignore
    sys.modules["six"] = six  # type: ignore
    moves_module = types.ModuleType("six.moves")
    moves_module._thread = _thread  # type: ignore[attr-defined]
    moves_module.getoutput = subprocess.getoutput  # type: ignore[attr-defined]
    six.moves = moves_module  # type: ignore
    sys.modules["six.moves"] = moves_module

if not hasattr(six, "ensure_binary"):
    def _ensure_binary(value, encoding='utf-8', errors='strict'):
        if isinstance(value, bytes):
            return value
        return str(value).encode(encoding, errors)

    def _ensure_text(value, encoding='utf-8', errors='strict'):
        if isinstance(value, bytes):
            return value.decode(encoding, errors)
        return str(value)

    six.ensure_binary = _ensure_binary
    six.ensure_text = _ensure_text
    six.ensure_str = _ensure_text

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

_MOCK_PROGRAM_ARGS = {
    "clusterctrl": {
        "choices": {
            "cleanup": []
        },
        "dest": "clusterctrl",
        "help": "cluster operations",
        "shortname": "c"
    },
    "uid": {
        "action": "store",
        "dest": "uid",
        "help": "uuid list",
        "shortname": "u"
    }
}


def _reload_cleanup_workers():
    module_name = "exabox.scheduleJobs.cleanup_workers"
    if module_name in sys.modules:
        del sys.modules[module_name]
    opener = mock_open(read_data=json.dumps(_MOCK_PROGRAM_ARGS))
    with patch("builtins.open", opener):
        module = importlib.import_module(module_name)
    return module


class ebTestCleanupWorkers(ebTestClucontrol):

    @classmethod
    def setUpClass(cls):
        super(ebTestCleanupWorkers, cls).setUpClass(True, False)

    def setUp(self):
        self.module = _reload_cleanup_workers()

    def _create_job(self, ctx=None, db=None):
        ctx = ctx or MagicMock()
        ctx.mGetArgsOptions.return_value = {}
        if db is None:
            db = MagicMock()
        with patch("exabox.scheduleJobs.cleanup_workers.exaBoxCoreInit"), \
             patch("exabox.scheduleJobs.cleanup_workers.ebLogInit"), \
             patch("exabox.scheduleJobs.cleanup_workers.get_gcontext", return_value=ctx), \
             patch("exabox.scheduleJobs.cleanup_workers.ebGetDefaultDB", return_value=db), \
             patch("exabox.scheduleJobs.cleanup_workers.os.getcwd", return_value="/opt/app/exacloud/bin"):
            job = self.module.CleanUpWorkers()
        return job, ctx, db

    def test_getWorkerPIDs_handles_empty_and_active_workers(self):
        job, _, _ = self._create_job()
        self.assertEqual(job.getWorkerPIDs("()"), [])

        worker_str = "[('uuid_a', 'Running', '', '', '', '', '', '', 4321), ('uuid_b', 'Running', '', '', '', '', '', '', 5432)]"
        proc1 = MagicMock()
        proc1.cmdline.return_value = ["python", "-w"]
        with patch("exabox.scheduleJobs.cleanup_workers.psutil.pid_exists", side_effect=[True, False]), \
             patch("exabox.scheduleJobs.cleanup_workers.psutil.Process", return_value=proc1):
            self.assertEqual(job.getWorkerPIDs(worker_str), [4321])

    def test_getWorkerPIDs_skips_non_worker_processes(self):
        job, _, _ = self._create_job()
        worker_str = "[('uuid_a', 'Running', '', '', '', '', '', '', 1234)]"
        proc = MagicMock()
        proc.cmdline.return_value = ["python", "cleanup.py"]
        with patch("exabox.scheduleJobs.cleanup_workers.psutil.pid_exists", return_value=True), \
             patch("exabox.scheduleJobs.cleanup_workers.psutil.Process", return_value=proc):
            self.assertEqual(job.getWorkerPIDs(worker_str), [])
            proc.cmdline.assert_called_once()

    @patch("exabox.scheduleJobs.cleanup_workers.psutil.pid_exists")
    @patch("exabox.scheduleJobs.cleanup_workers.psutil.Process")
    def test_getWorkerPIDs_skips_exited_and_zero_pid(self, mock_process, mock_pid_exists):
        job, _, _ = self._create_job()
        worker_str = "[('uuid_a', 'Exited', '', '', '', '', '', '', 9999), ('uuid_b', 'Running', '', '', '', '', '', '', 0)]"

        result = job.getWorkerPIDs(worker_str)

        self.assertEqual(result, [])
        mock_pid_exists.assert_not_called()
        mock_process.assert_not_called()

    def test_mCleanUp_kills_workers_and_handles_lock_errors(self):
        db = MagicMock()
        db.mDumpActiveWorkers.return_value = "[('uuid', 'Running', '', '', '', '', '', '', 9876)]"
        db.mGetLocksByUUID.return_value = [
            {"lock_hostname": "dom0a"},
            {"lock_hostname": "dom0b"},
        ]
        db.mDeleteLock.side_effect = [None, Exception("failed")]
        job, _, _ = self._create_job(db=db)
        job.getWorkerPIDs = MagicMock(return_value=[9876])

        req_obj = MagicMock()
        with patch("exabox.scheduleJobs.cleanup_workers.ebGetRequestObj", return_value=req_obj), \
             patch("exabox.scheduleJobs.cleanup_workers.mExecuteLocal") as mock_exec, \
             patch("exabox.scheduleJobs.cleanup_workers.ebLogWarn") as mock_warn:
            job.mCleanUp("uuid")

        mock_exec.assert_called_once_with("/bin/kill -9 9876")
        req_obj.mSetStatus.assert_called_once_with('Done')
        req_obj.mSetError.assert_called_once_with('709')
        db.mUpdateRequest.assert_called_once_with(req_obj)
        self.assertEqual(db.mDeleteLock.call_count, 2)
        mock_warn.assert_called_once()
        db.mClearWorkers.assert_called_once_with(aUUID="uuid")
        db.mDelRegByUUID.assert_called_once_with("uuid")

    def test_mCleanUp_skips_kill_when_no_workers(self):
        db = MagicMock()
        db.mDumpActiveWorkers.return_value = "[]"
        job, _, _ = self._create_job(db=db)
        job.getWorkerPIDs = MagicMock(return_value=[])

        with patch("exabox.scheduleJobs.cleanup_workers.ebGetRequestObj", return_value=MagicMock()), \
             patch("exabox.scheduleJobs.cleanup_workers.mExecuteLocal") as mock_exec:
            job.mCleanUp("uuid")

        mock_exec.assert_not_called()

    def test_mExecuteJob_with_uuid_list(self):
        job, _, _ = self._create_job()
        job.mCleanUp = MagicMock()
        job.mExecuteJob(aCmd="cluctrl.cleanup", aUuidList=["u1", "u2"])
        job.mCleanUp.assert_has_calls([call(aUUID="u1"), call(aUUID="u2")])

    def test_mExecuteJob_fetches_active_requests_when_missing_uuid_list(self):
        db = MagicMock()
        db.mGetActiveRequestsUUID.return_value = [("a",), ("b",)]
        job, _, _ = self._create_job(db=db)
        job.mCleanUp = MagicMock()
        job.mExecuteJob(aCmd="cluctrl.cleanup", aUuidList=None)
        job.mCleanUp.assert_has_calls([call(aUUID="a"), call(aUUID="b")])

    def test_ebLoadProgramArguments_converts_choices(self):
        data = {
            "clusterctrl": {
                "choices": {"task": ["flag1", "flag2"]},
                "dest": "clusterctrl",
            }
        }
        opener = mock_open(read_data=json.dumps(data))
        with patch("builtins.open", opener):
            program_args, clu_opts = self.module.ebLoadProgramArguments()

        self.assertEqual(program_args["clusterctrl"]["choices"], ["task"])
        self.assertEqual(clu_opts, {"task": {"flag1", "flag2"}})

    def test_main_without_arguments_logs_and_exits(self):
        with patch.object(self.module, "ebLogInfo") as mock_info, \
             patch.object(self.module, "CleanUpWorkers") as mock_clean, \
             patch.object(sys, "argv", ["cleanup_workers.py"]):
            self.module.main()

        mock_clean.assert_not_called()
        mock_info.assert_called_with('No Arguments specified...')

    def test_main_with_arguments_invokes_execute_job(self):
        cleaner = MagicMock()
        with patch.object(self.module, "CleanUpWorkers", return_value=cleaner) as mock_cls, \
             patch.object(sys, "argv", ["cleanup_workers.py", "--clusterctrl", "cleanup", "--uid", "id1,id2"]):
            self.module.main()

        mock_cls.assert_called_once()
        cleaner.mExecuteJob.assert_called_once_with('cluctrl.cleanup', ['id1', 'id2'])


if __name__ == '__main__':
    unittest.main()
