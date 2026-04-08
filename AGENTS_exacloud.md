# Exabox Code Generation Guide

## 1. Core Principles
- **No hardcoded values** — use constants from `infrapatching/utils/constants.py` or config
- **F-strings only** — all string interpolation MUST use f-strings (no `.format()` or `%`)
- **Method prefix `m`** — every class method must start with `m` (e.g., `mPreCheck`, `mPatch`)
- **Global function prefix `eb`** — standalone utility/log functions use `eb` prefix
- **Mock external calls in tests** — DB, HTTP, SSH, subprocess must always be mocked
- **Log before raising** — always log with context before raising any exception
- **Never log sensitive data** — no passwords, keys, tokens in logs

## 2. Tech Stack
- **Language**: Python 3 | **Test framework**: `unittest` (NOT pytest)
- **Database**: MySQL via `core/DBStore3.py` | **HTTP server**: Custom `BaseServer/`
- **OCI**: `exaoci/` | **KMS**: `exakms/` | **No external package manager**

## 3. Architecture
```
exabox/
├── agent/           # Worker, Dispatcher, Scheduler, Client, DBService
├── BaseServer/      # HTTP/HTTPS server, AsyncProcessing, BaseHandler
├── core/            # Context, Error, DBStore, Threads, Node
├── infrapatching/
│   ├── core/        # cludispatcher.py, infrapatcherror.py
│   ├── handlers/targetHandler/   # dom0handler.py, cellhandler.py
│   ├── handlers/taskHandler/     # task-specific handlers
│   ├── helpers/     # crshelper.py
│   └── utils/       # constants.py, utility.py
└── exatest/         # Tests mirroring source structure
```
Handler hierarchy: `LogHandler → GenericHandler → TargetHandler / TaskHandler`

## 4. File Header (required on every file)
```python
# $Header: ecs/exacloud/exabox/<path>/<file>.py /main/1 YYYY/MM/DD HH:MM:SS author Exp $
# <file>.py
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
#    NAME      <file>.py - Brief description
#    MODIFIED  (MM/DD/YY)
#    jyotdas   03/03/26 - Brief description of change
```

## 5. Naming Conventions
| Element | Convention | Example |
|---------|-----------|---------|
| Class methods | `m` prefix | `mPreCheck`, `mPatch`, `mGetLogPath` |
| Global functions | `eb` prefix | `ebLogInfo`, `ebGetDefaultDB` |
| Private attributes | double underscore | `self.__config`, `self.__log` |
| Constants | UPPER_CASE | `PATCH_DOM0`, `TASK_PREREQ_CHECK` |
| Test classes | `ebTest` prefix | `ebTestCluPatchDispatcher` |

## 6. Imports & String Style
**F-strings only:** `self.mPatchLogInfo(f"Patching {_dom0} with {_version}")`

**Import order:** stdlib → third-party → local (wildcard ok for constants):
```python
from exabox.infrapatching.utils.constants import *
from exabox.infrapatching.core.infrapatcherror import *
```

## 7. Logging
- **In handlers:** `self.mPatchLogInfo/Error/Warn/Debug(f"...")` — do NOT use `ebLogInfo` directly
- **Outside handlers:** `from exabox.log.LogMgr import ebLogInfo, ebLogError, ebLogDebug, ebLogWarn`
- Log: operation start/end, return codes, `str(e)` before re-raise, state transitions

## 8. Error Handling
```python
# Infrapatching — use hex codes from infrapatcherror.py
if _ret != PATCH_SUCCESS_EXIT_CODE:
    self.mAddError(PATCH_OPERATION_FAILED, f"Patch failed rc={_ret}")

# Core agent — use core/Error.py
raise ebError(ebErrorCodes.GENERAL_ERROR, str(e))
```
**Common codes:** `PATCH_SUCCESS_EXIT_CODE="0x00000000"`, `PATCH_OPERATION_FAILED="0x03010000"`,
`MISSING_PATCH_FILES="0x03010001"`, `INCORRECT_INPUT_JSON="0x03010004"`, `PATCH_REQUEST_TIMEOUT="0x03010005"`

## 9. Testing
**Structure:** `exatest/infrapatching/core/tests_cludispatcher.py` mirrors `infrapatching/core/cludispatcher.py`

**Template:**
```python
import unittest
from unittest.mock import patch, MagicMock
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo

class ebTest<ClassName>(ebTestClucontrol):
    SUCCESS_ERROR_CODE = "0x00000000"

    @classmethod
    def setUpClass(cls):
        super(ebTest<ClassName>, cls).setUpClass(aGenerateDatabase=True)

    @patch('exabox.<module>.<ClassName>.<mMethod>', return_value="0x00000000")
    def test_mOperation_success(self, mock_call):
        _instance = <ClassName>(aJob=self._job)
        self.assertEqual(_instance.mOperation(), self.SUCCESS_ERROR_CODE)

if __name__ == '__main__':
    unittest.main()
```
**Coverage required per method:** success path, edge cases (None/empty), error/exception case.
**Run:** `cd exatest && python exatest.py -run -all`

## 10. Infrapatching Handler Pattern
```python
from exabox.infrapatching.handlers.targetHandler.targethandler import TargetHandler
from exabox.infrapatching.utils.constants import *
from exabox.infrapatching.core.infrapatcherror import *

class Dom0Handler(TargetHandler):
    def mPreCheck(self):
        self.mPatchLogInfo(f"\n----> Starting {TASK_PREREQ_CHECK} on {PATCH_DOM0}s <----\n")
        _ret = PATCH_SUCCESS_EXIT_CODE
        try:
            pass  # logic here
        except Exception as e:
            self.mPatchLogError(f"Exception in mPreCheck: {str(e)}")
            self.mAddError(PATCH_OPERATION_FAILED, str(e))
            _ret = PATCH_OPERATION_FAILED
        self.mPatchLogInfo(f"Final return code from {self.mGetTask()}: {_ret}")
        return _ret
    # also implement: mPatch, mRollBack, mPostCheck
```

## 11. Common Patterns
```python
# Config
from exabox.core.Context import get_gcontext
context.mGetConfig().mGetConfigValue("key")

# Database
from exabox.core.DBStore import ebGetDefaultDB
db.mExecuteQuery(query, params)

# Locking
from exabox.core.DBStore import ExaLock
with ExaLock(lock_name): ...

# Factory
_handler = getTaskHandlerInstance(operation, params_dict)
_ret = _handler.mPreCheck()
```

## 12. AI Coding Assistant Instructions
- **Read before editing** — always read target file(s) before making changes
- **F-string rule** — never use `.format()` or `%` for string interpolation in new code
- **`m`/`eb` prefix** — all new class methods use `m`; global functions use `eb`
- **File header** — every new file needs RCS-style header with MODIFIED log
- **Mirror test structure** — test path must mirror source path under `exatest/`
- **Inherit correctly** — handlers must inherit from correct base (`TargetHandler`, `TaskHandler`)
- **Constants from constants.py** — never hardcode operation names, target types, or error codes
- **Mock all external calls** — no real DB/SSH/HTTP in tests; use `unittest.mock.patch`
- **Use `mPatchLog*` in handlers** — do NOT call `ebLogInfo` directly inside handler classes
- **Run tests before committing** — `cd exatest && python exatest.py -run -all` must pass

## 13. Pre-Commit Checklist
- [ ] File header with RCS `$Header` and MODIFIED log entry
- [ ] All string interpolation uses f-strings
- [ ] Method names prefixed with `m`, global functions with `eb`
- [ ] No hardcoded constants — all in `constants.py` or `infrapatcherror.py`
- [ ] Error codes from `infrapatcherror.py` (infrapatching) or `core/Error.py` (agent/core)
- [ ] Unit tests in `exatest/` with matching path; cover success, edge, and error cases
- [ ] All external dependencies mocked in tests
- [ ] `cd exatest && python exatest.py -run -all` passes
- [ ] No sensitive data (passwords, keys, tokens) in logs or code
